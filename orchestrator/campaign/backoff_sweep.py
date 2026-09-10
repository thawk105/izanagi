# -*- coding: utf-8 -*-
"""P2 ケーススタディ: silo の backoff 量を単一軸として sweep (Phase 2→3 の橋渡し)。

critic が leading indicators から「BACK_OFF=1 は abort を減らせているのに ipc 崩壊で
遅い (over-throttling)」と帰属し、新軸「中間/適応 backoff」を提案した。ソースを見ると
CCBench の BACK_OFF=1 は既定 3 定数 (刻み 100 µs / 上限 1000 µs / 更新間隔
10 µs) の adaptive backoff である。この値は上流を素のまま使ったときの文脈点であり、
調整済み adaptive を含まない本 campaign から adaptive 機構の verdict は出さない (D1506)。

そこで定義済みフラグ空間 (binary BACK_OFF) の**外**へ出て、backoff の*量*を静的に
固定する新フラグ `CCBENCH_BACKOFF_FIXED` (patches/silo-backoff-fixed.patch, default -1=
CCBench 既定 3 定数の adaptive で inert) を導入し、量を sweep して静的最良と無 backoff
の記述的な差を測る。各 genome は pipeline で build→**verify (正しさゲート, 規律2)**→bench。
backoff は timing のみ変える (CC 論理は不変) ので serializable のはずだが**必ず検証**する。

  python orchestrator/campaign/backoff_sweep.py            # 全 workload
  python orchestrator/campaign/backoff_sweep.py write-heavy
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .loop import run_campaign                          # noqa: E402
from . import buildcache, condition_meaning_gate, patchharness  # noqa: E402
from .build_admission import (BuildRunContext, GeneratorId,  # noqa: E402
                                      attest_generator_output, build_run_context)
from .layout import (CampaignLayout, _OFFICIAL_OUTPUT_ROOT_ENV)  # noqa: E402
from .durable_root import DurableRootPolicy             # noqa: E402
from .model import CampaignConfig, Genome               # noqa: E402
from . import p2_2                                       # noqa: E402
from .p2_2 import (EXTIME, RECORDS, REPS, THREADS,        # noqa: E402
                           _assert_single_tenant)
from .pipeline import PerfConfig                        # noqa: E402
from . import (ident, pin, screening_driver,
                      source_digest, wal)  # noqa: E402
from .loop import CampaignSummary                       # noqa: E402
from .pipeline import SCREEN_REJECTION_REASON, variant_id  # noqa: E402


_DEFAULT_CXX = buildcache.DEFAULT_CXX
_compilers_for_current_site = buildcache.compilers_for_current_site


CCBENCH_COMMIT = pin.CURRENT_PIN      # 511c953 — literal 保持をやめ pin 正本へ (between_run_floor と同型)

# 全 genome 共通の base = 高 abort 域の勝者構成 L-W0 (no-wait-locking / WAL 無)。
_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
# backoff 量の静的 sweep (us)。低域に密 (critic の「短い backoff」仮説の検証帯)。
SWEEP_US = [2, 5, 10, 25, 50, 100]

# backoff が効きうる高 abort workload (write-heavy/balanced) + 対照として read-heavy。
# read-heavy は abort が低いので「sweet spot が 0 (=無 backoff) に潰れ backoff は純損」を
# 確認する負け確の対照点 = 「backoff は abort が高い時だけ効く」の完全性 (ケーススタディの締め)。
WORKLOADS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
]


@dataclass(frozen=True, slots=True)
class _BackoffConditionGateRun:
    """The two independent arm records and their reference-only admission."""

    supply_records: tuple[condition_meaning_gate.ConditionArmRecord, ...]
    meaning_records: tuple[condition_meaning_gate.ConditionArmRecord, ...]
    admission: condition_meaning_gate.ConditionFamilyAdmission


_CONDITION_GATE_DEFAULTS = {
    "BACKOFF_FIXED": -1,
    "BACKOFF_NOINLINE": 0,
    "BACKOFF_REQUESTED_US": 0,
}


def _backoff_fixed_declarations(
        requested_values: Sequence[int],
        backoff_fixed_physical_us: Mapping[int, int],
) -> dict[int, condition_meaning_gate.MeaningWitnessDeclaration]:
    """Declare the driver physical intent independently of the backoff codec."""
    if not isinstance(backoff_fixed_physical_us, Mapping):
        raise RuntimeError("BACKOFF_FIXED physical intent must be a mapping")
    physical_rows = tuple(backoff_fixed_physical_us.items())
    if any(type(raw) is not int for raw, _physical in physical_rows):
        raise RuntimeError("BACKOFF_FIXED physical intent keys must be exact integers")
    requested_nonnegative = {
        value
        for value in requested_values
        if value >= 0
    }
    supplied_nonnegative = {raw for raw, _physical in physical_rows}
    if supplied_nonnegative != requested_nonnegative:
        raise RuntimeError(
            "BACKOFF_FIXED physical intent key mismatch: "
            f"missing={sorted(requested_nonnegative - supplied_nonnegative)!r}, "
            f"extra={sorted(supplied_nonnegative - requested_nonnegative)!r}"
        )
    if any(
            type(physical) is not int or physical < 0
            for _raw, physical in physical_rows
    ):
        raise RuntimeError(
            "BACKOFF_FIXED physical intent values must be non-negative exact integers"
        )

    fixed_declarations = {}
    for raw, physical in physical_rows:
        try:
            bits = condition_meaning_gate.canonical_float64_bits(float(physical))
        except (OverflowError, ValueError) as exc:
            raise RuntimeError(
                "BACKOFF_FIXED physical intent is not finite binary64"
            ) from exc
        fixed_declarations[raw] = condition_meaning_gate.MeaningWitnessDeclaration(
            "BACKOFF_FIXED",
            (condition_meaning_gate.MeaningCase(raw, (bits, bits)),),
        )

    return fixed_declarations


def _require_backoff_condition_gate(
        source_root: str, *, stock_root: Optional[str], driver_id: str,
        macro_values: Mapping[str, Sequence[int]],
        backoff_fixed_physical_us: Mapping[int, int], cxx: str,
        cmake: str = "cmake", use_class: str = "raw-measurement",
        configure_args: Sequence[str] = (),
) -> _BackoffConditionGateRun:
    """Run both condition-gate arms for every concrete driver request."""
    unsupported = set(macro_values).difference(condition_meaning_gate.DEFINE_SPECS)
    if unsupported:
        raise RuntimeError(
            "driver supplied macros outside DEFINE_SPECS: "
            f"{sorted(unsupported)!r}"
        )
    unknown_defaults = set(macro_values).difference(_CONDITION_GATE_DEFAULTS)
    if unknown_defaults:
        raise RuntimeError(
            "backoff driver has no reviewed default for macros: "
            f"{sorted(unknown_defaults)!r}"
        )
    reviewed_values: dict[str, tuple[int, ...]] = {}
    for macro, values in macro_values.items():
        if type(values) not in {tuple, list} or not values:
            raise RuntimeError(f"condition gate values are missing for {macro}")
        if any(type(value) is not int for value in values):
            raise RuntimeError(
                f"condition gate values must be exact integers for {macro}"
            )
        reviewed_values[macro] = tuple(dict.fromkeys(values))

    fixed_declarations = _backoff_fixed_declarations(
        reviewed_values.get("BACKOFF_FIXED", ()), backoff_fixed_physical_us,
    )

    captured = condition_meaning_gate.capture_define_inputs(
        source_root, stock_root=stock_root, configure_args=configure_args,
    )
    requests = []
    for macro, values in reviewed_values.items():
        for value in values:
            stock_comparison = macro == "BACKOFF_FIXED" and value == -1
            requests.append(condition_meaning_gate.make_define_request(
                driver_id=driver_id,
                macro=macro,
                requested_value=value,
                default_value=(
                    None if stock_comparison else _CONDITION_GATE_DEFAULTS[macro]
                ),
                stock_comparison=stock_comparison,
            ))
    supply_records = tuple(
        condition_meaning_gate.evaluate_define_supply_effectuation(
            captured, request=request, cxx=cxx, cmake=cmake,
        )
        for request in requests
    )
    meaning_records = tuple(
        condition_meaning_gate.evaluate_define_runtime_meaning(
            captured,
            request=request,
            declaration=(
                condition_meaning_gate.MeaningWitnessDeclaration(
                    "BACKOFF_FIXED",
                    (
                        condition_meaning_gate.MeaningCase(
                            -1,
                            None,
                            condition_meaning_gate.STOCK_ADAPTIVE_BRANCH,
                        ),
                    ),
                )
                if request.macro == "BACKOFF_FIXED"
                and request.requested_value == -1
                else fixed_declarations.get(request.requested_value)
                if request.macro == "BACKOFF_FIXED"
                else None
            ),
            cxx=cxx,
        )
        for request in requests
    )
    admission = condition_meaning_gate.require_condition_gate_family(
        supply_records, meaning_records, use_class=use_class,
    )
    if not admission.admitted:
        terminal = [
            f"{record.macro}={record.terminal_status}/{record.reason_code}"
            for record in (*supply_records, *meaning_records)
            if record.terminal_status == "red"
        ]
        raise RuntimeError(
            "condition gate rejected the driver before build/measurement: "
            + ", ".join(terminal)
        )
    return _BackoffConditionGateRun(supply_records, meaning_records, admission)


def _official_durable_root_policy(
        output_root: Optional[Path] = None,
) -> Optional[DurableRootPolicy]:
    """Build the injected durable policy for an official output root."""
    raw = (
        os.fspath(output_root)
        if output_root is not None
        else os.environ.get(_OFFICIAL_OUTPUT_ROOT_ENV)
    )
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = candidate.absolute()
    try:
        resolved = candidate.resolve(strict=False)
    except OSError:
        return None
    return DurableRootPolicy(approved_roots=(resolved,), forbidden_roots=())


def genomes():
    """L-W0 を base に: 無 backoff / 既定 3 定数 adaptive の文脈点 / 静的 sweep。

    調整済み adaptive は含まず、adaptive 機構の verdict には使わない (D1506)。
    """
    gs = [Genome("silo", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}),   # 無 backoff
          Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})]   # 既定 3 定数 adaptive
    for n in SWEEP_US:
        gs.append(Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": n}))  # 静的 N
    return gs


def config_for(tag: str, workload: dict, *,
               screening_fixed_us: Optional[int] = None,
               contract=None) -> CampaignConfig:
    search_config = {"scale": "silo-backoff", "base": "L-W0",
                     "sweep_us": SWEEP_US, "workload": tag,
                     "records": RECORDS, "threads": THREADS, "ycsb": workload}
    # positive control 等の最小 screening campaign 専用。省略時はキー自体を
    # 足さず、既存 campaign-id と全点 sweep の既定挙動を不変に保つ。
    if screening_fixed_us is not None:
        search_config["screening_fixed_us"] = screening_fixed_us
    cfg = CampaignConfig(
        spec_slug=f"backoff-sweep-silo-{tag}", search_tag="sweep",
        spec_content=f"P2 case study: silo static-backoff sweep — workload={tag}",
        ccbench_commit=CCBENCH_COMMIT,
        search_config=search_config,
        trial="p2-backoff")
    if contract is None:
        # Preserve the historical non-measurement config-builder contract. The
        # actual run path always supplies the resolved runtime contract below.
        contract = p2_2._legacy_linux_contract()
    return ident.bind_environment_contract(cfg, contract)


def _run_screened_workload(cfg, gs, perf, workload, calibration_dir, log, *,
                           backoff_fixed_physical_us: Mapping[int, int],
                           build_context: BuildRunContext,
                           capability_resolver,
                           runtime_contract,
                           authorization_contract,
                           expected_toolchain_manifest=None,
                           confirm_each_candidate=False,
                           verified_calibration=None):
    fixed_declarations = _backoff_fixed_declarations(
        tuple(genome.flags["BACKOFF_FIXED"] for genome in gs),
        backoff_fixed_physical_us,
    )
    baseline = gs[0]
    if expected_toolchain_manifest is None:
        _, resolved_cxx = _compilers_for_current_site()
    else:
        _, resolved_cxx = buildcache.toolchain_compilers_from_manifest(
            expected_toolchain_manifest,
        )
    evidence_cxx = _DEFAULT_CXX if resolved_cxx == _DEFAULT_CXX else resolved_cxx
    baseline_ref = variant_id(
        baseline,
        source_digest.resolve(
            baseline, cfg.ccbench_commit, cxx=evidence_cxx,
        ),
    )
    measured = []
    execution_contract = runtime_contract
    runtime_numactl = list(runtime_contract.numactl)
    execution_receipt, verified_calibration = screening_driver.attest_runtime_contract(
        runtime_contract, verified_calibration=verified_calibration,
    )

    def measure_baseline(screen_cfg, layout):
        measured.append(screening_driver.evaluate_candidate(
            screen_cfg, layout, baseline, perf,
            runtime_contract.env_tag, runtime_contract.clocks_per_us,
            backoff_fixed_declaration=fixed_declarations.get(
                baseline.flags["BACKOFF_FIXED"],
            ),
            authorization_contract=authorization_contract,
            env_contract=execution_contract,
            expected_toolchain_manifest=expected_toolchain_manifest,
            declared_use_class="official",
            build_context=build_context,
            capability_resolver=capability_resolver,
            screening=None, numactl=runtime_numactl, force=True,
            do_settle=True, log=log,
            execution_receipt=execution_receipt,
            verified_calibration=verified_calibration))

    prepared = screening_driver.prepare_screening_campaign(
        cfg, workload, baseline_ref, measure_baseline,
        protocol=baseline.protocol,
        authorization_contract=authorization_contract,
        env_tag=runtime_contract.env_tag,
        clocks_per_us=runtime_contract.clocks_per_us,
        numactl=runtime_numactl,
        calibration_dir=calibration_dir, build_context=build_context,
        env_contract=execution_contract,
        execution_receipt=execution_receipt,
        verified_calibration=verified_calibration)
    prepared_execution_receipt = getattr(
        prepared, "execution_receipt", execution_receipt,
    )
    prepared_verified_calibration = getattr(
        prepared, "verified_calibration", verified_calibration,
    )
    s = CampaignSummary(campaign_id=str(ident.campaign_id(prepared.cfg)),
                        layout_root=prepared.layout.root, total=len(gs),
                        execution_receipt=prepared_execution_receipt)
    results = [measured[0]]
    for genome in gs[1:]:
        if confirm_each_candidate:
            input("screened candidate 直前の単一テナント/高CPU確認後に Enter: ")
        _assert_single_tenant()
        results.append(screening_driver.evaluate_candidate(
            prepared.cfg, prepared.layout, genome, perf,
            runtime_contract.env_tag, runtime_contract.clocks_per_us,
            backoff_fixed_declaration=fixed_declarations.get(
                genome.flags["BACKOFF_FIXED"],
            ),
            authorization_contract=authorization_contract,
            env_contract=execution_contract,
            expected_toolchain_manifest=expected_toolchain_manifest,
            declared_use_class="official",
            build_context=build_context,
            capability_resolver=capability_resolver,
            screening=prepared.screening, numactl=runtime_numactl, log=log,
            execution_receipt=prepared_execution_receipt,
            verified_calibration=prepared_verified_calibration))
    for result in results:
        if result is None:
            s.skipped += 1
            continue
        s.results.append(result)
        s.evaluated += 1
        if result.aborted:
            s.aborted += 1
        elif result.certified:
            s.committed += 1
    return s


def run_workload(tag: str, workload: dict, log=print, *,
                 screening_enabled: bool = False, calibration_dir: str = "",
                 screening_fixed_us: Optional[int] = None,
                 confirm_each_candidate: bool = False):
    _assert_single_tenant()
    site, contract, authorization = p2_2.resolve_site_runtime()
    loaded_calibration = p2_2._assert_matches_calibration(contract)
    gs = genomes()
    if screening_fixed_us is not None:
        if not screening_enabled:
            raise ValueError("screening_fixed_us は screening opt-in 時だけ指定できる")
        selected = [g for g in gs
                    if g.flags.get("BACK_OFF") == 1
                    and g.flags.get("BACKOFF_FIXED") == screening_fixed_us]
        if len(selected) != 1:
            raise ValueError(
                f"screening_fixed_us は既存 sweep 点から一意に選ぶ: {screening_fixed_us}")
        gs = [gs[0], selected[0]]
    cfg = config_for(
        tag, workload, screening_fixed_us=screening_fixed_us, contract=contract,
    )
    cfg = p2_2._campaign_cfg_for_site(cfg, site, contract)
    resolved_cc, resolved_cxx = _compilers_for_current_site()
    expected_toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx,
    )
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    capability_resolver = lambda evidence: attest_generator_output(
        build_context, evidence,
        generator_input_sha256=hashlib.sha256(
            f"backoff-sweep/v1|{evidence.genome_sha256}".encode("utf-8")
        ).hexdigest(),
    )
    perf = PerfConfig(records=RECORDS, threads=THREADS, workload=workload,
                      extime=EXTIME, reps=REPS)
    log(f"\n=== backoff sweep  workload={tag}  ({workload})  {len(gs)} genome ===")
    backoff_fixed_physical_us = {
        amount: amount for amount in SWEEP_US
        if any(genome.flags["BACKOFF_FIXED"] == amount for genome in gs)
    }
    ccbench_dir = buildcache._ccbench_dir()
    patch_path = os.fspath(
        Path(__file__).resolve().parents[2] / "patches/silo-backoff-fixed.patch"
    )
    with patchharness.checkout(CCBENCH_COMMIT, base_dir=ccbench_dir) as stock_root:
        with patchharness.applied(patch_path, CCBENCH_COMMIT, ccbench_dir):
            canonical_ccbench_dir = os.fspath(Path(ccbench_dir).resolve())
            with tempfile.TemporaryDirectory(
                    prefix="izanagi-backoff-condition-gate-",
            ) as fetchcontent_base:
                canonical_base = os.fspath(Path(fetchcontent_base).resolve())
                buildcache.prepare_masstree_fetchcontent(
                    ccbench_dir=canonical_ccbench_dir,
                    fetchcontent_base_dir=canonical_base,
                    expected_toolchain_manifest=expected_toolchain_manifest,
                    configure_timeout_s=900,
                    target_timeout_s=900,
                    site=site,
                )
                _require_backoff_condition_gate(
                    canonical_ccbench_dir,
                    stock_root=stock_root,
                    driver_id="orchestrator/campaign/backoff_sweep.py",
                    macro_values={
                        "BACKOFF_FIXED": tuple(
                            genome.flags["BACKOFF_FIXED"] for genome in gs
                        ),
                    },
                    backoff_fixed_physical_us=backoff_fixed_physical_us,
                    cxx=resolved_cxx,
                    use_class="raw-measurement",
                    configure_args=(
                        f"-DFETCHCONTENT_BASE_DIR={canonical_base}",
                    ),
                )
            if screening_enabled:
                s = _run_screened_workload(
                    cfg, gs, perf, workload, calibration_dir, log,
                    backoff_fixed_physical_us=backoff_fixed_physical_us,
                    build_context=build_context,
                    capability_resolver=capability_resolver,
                    runtime_contract=contract,
                    authorization_contract=authorization,
                    expected_toolchain_manifest=expected_toolchain_manifest,
                    confirm_each_candidate=confirm_each_candidate,
                    verified_calibration=(
                        getattr(loaded_calibration, "verified", None)
                        if contract.attestation_mode == "required"
                        else None
                    ))
            else:
                s = run_campaign(
                    cfg, gs, perf, contract.env_tag, contract.clocks_per_us,
                    numactl=list(contract.numactl), log=log,
                    authorization_contract=authorization,
                    env_contract=contract,
                    expected_toolchain_manifest=expected_toolchain_manifest,
                    build_context=build_context,
                    declared_use_class="official",
                    capability_resolver=capability_resolver,
                    durable_root_policy=_official_durable_root_policy(),
                )

    rows = [(r.fitness_tps, r) for r in s.results if r.fitness_tps is not None]
    rows.sort(key=lambda t: t[0], reverse=True)
    log(f"\n  --- {tag}: backoff sweep ランキング (committed={s.committed} "
        f"aborted={s.aborted}) ---")
    for tps, r in rows:
        bf = r.genome.flags.get("BACKOFF_FIXED")
        tag_bf = "adaptive" if (r.genome.flags["BACK_OFF"] == 1 and bf == -1) else \
                 ("none" if r.genome.flags["BACK_OFF"] == 0 else f"fixed={bf}us")
        log(f"    {tps:>12,.0f} tps  CV {r.cv * 100:4.2f}%"
            f"{'  ⚠UNSTABLE' if r.unstable else ''}  backoff={tag_bf}")
    for r in (r for r in s.results if r.aborted):
        log(f"    ✗ ABORT {r.genome.canonical()}: {r.verdict} / {r.notes}")
    return s


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="silo static-backoff sweep")
    ap.add_argument("workload", nargs="?", choices=[w[0] for w in WORKLOADS])
    ap.add_argument("--screening", action="store_true",
                    help="bench-first screeningをopt-in (既定off)")
    ap.add_argument("--calibration-dir", default="",
                    help="between_run_noise_*.jsonの置き場 (省略時はresolved env scope)")
    ap.add_argument("--screening-fixed-us", type=int,
                    help="screening時に baseline + 指定fixed-usの最小2点だけ実走")
    ap.add_argument("--confirm-each-candidate", action="store_true",
                    help="screened candidate直前に外部競合確認のためEnter待ち")
    a = ap.parse_args(argv[1:])
    if (a.screening_fixed_us is not None or a.confirm_each_candidate) and not a.screening:
        ap.error("--screening-fixed-us/--confirm-each-candidate は --screening と併用する")
    sel = a.workload
    wls = [w for w in WORKLOADS if sel is None or w[0] == sel]
    summaries = [(tag, run_workload(
        tag, wl, screening_enabled=a.screening,
        calibration_dir=a.calibration_dir,
        screening_fixed_us=a.screening_fixed_us,
        confirm_each_candidate=a.confirm_each_candidate)) for tag, wl in wls]
    print("\n=== backoff sweep 完了 ===")
    for tag, s in summaries:
        print(f"  {tag}: {s.campaign_id}  committed={s.committed} aborted={s.aborted}")
    replay_policy = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP).policy
    def unexpected_abort(summary):
        layout = CampaignLayout(summary.layout_root)
        return any(
            st.last_terminal is not None
            and st.last_terminal.payload.get("reason") != SCREEN_REJECTION_REASON
            for st in wal.replay(layout, admission_policy=replay_policy).values()
            if st.aborted and not st.committed)

    ok = all(not unexpected_abort(s) for _, s in summaries) if a.screening else \
        all(s.aborted == 0 for _, s in summaries)
    print(f"backoff sweep: {'全 genome 計測成功' if ok else 'abort あり (要確認)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
