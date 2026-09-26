# -*- coding: utf-8 -*-
"""偵察 sweep 専用の bench-first screening 組み立てと候補評価。

autonomous `loop.py` へ screening を配線せず、opt-in driver だけがこの層を使う。
"""
from __future__ import annotations

import glob
import json
import os
import tempfile
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Sequence

from ..calibrator import perf_preflight as _perf_preflight
from . import (
    buildcache, condition_meaning_gate, env_attestation,
    env_contract as _env_contract, execution_guard, ident, patchharness,
    source_digest, wal,
)
from .build_admission import BuildRunContext
from .env_contract import AuthorizedContract, ExecutionEnvironmentContract
from .genome import protocol_from_floor_genome
from .layout import CampaignLayout, campaign_layout, env_scope_dir
from .model import (STAGE_ABORT, STAGE_BENCH_DONE, STAGE_COMMIT,
                    CampaignConfig, Genome, cmake_cache_variable_for_axis)
from .pipeline import (AdmissionCapabilityResolver, EvalResult, PerfConfig, S2_TAG,
                       SEARCH_CONFIG_VERIFY_KEY,
                       ScreeningConfig, VERIFY_LEGACY_PLUS_S2, evaluate,
                       s2_correctness_workload, variant_id)


@dataclass(frozen=True)
class PreparedScreening:
    cfg: CampaignConfig
    layout: CampaignLayout
    screening: ScreeningConfig
    execution_receipt: Optional[dict] = None
    verified_calibration: Optional[env_attestation.VerifiedCalibration] = None


@dataclass(frozen=True, slots=True)
class _ScreeningConditionGateRun:
    supply_records: tuple[condition_meaning_gate.ConditionArmRecord, ...]
    meaning_records: tuple[condition_meaning_gate.ConditionArmRecord, ...]
    admission: condition_meaning_gate.ConditionFamilyAdmission


_CONDITION_DEFAULTS = {
    "BACKOFF_FIXED": -1,
    "BACKOFF_INCR_MILLI": 100000,
    "BACKOFF_MAX_US": 1000,
    "BACKOFF_COUNT_WINDOW": 0,
    "BACKOFF_COUNT_CAP_US": 0,
    "BACKOFF_STEP_ADAPT": 0,
    "BACKOFF_STEP_MIN_MILLI": 100000,
    "BACKOFF_STEP_MAX_MILLI": 100000,
    "BACKOFF_DYN_CEILING": 0,
    "BACKOFF_TRACE": 0,
    "BACKOFF_TRACE_TERMINAL_US": 0,
    "BACKOFF_STEP_POLICY": 0,
    "BACKOFF_STEP_POLICY_SEED": 11400714819323198485,
    "BACKOFF_NOINLINE": 0,
    "BACKOFF_REQUESTED_US": 0,
    "BACKOFF_TRIGGER_GATING": 0,
    "BACKOFF_UPDATE_US": 10,
    "MOCC_TEMP_PREDICATE": 0,
    "SORT_VARIANT": 0,
    "SILO_POLICY_VARIANT": 0,
    "IZANAGI_SILO_POLICY_PROBE": 0,
    "IZANAGI_BREAK_SILO_POLICY": 0,
    "SS2PL_LOCK_IMPL": 0,
    "SS2PL_LOCK_KIND": 1,
    "SS2PL_DLR": 1,
    "SS2PL_WFG_DIAG": 0,
    "IZANAGI_BREAK_PERMUTATION": 0,
    "IZANAGI_BREAK_PERMUTATION_SWAP": 0,
    "IZANAGI_BREAK_LOCK_COVERAGE": 0,
    "IZANAGI_BREAK_EARLY_UNLOCK": 0,
    "IZANAGI_BREAK_MOCC_LOCK_COVERAGE": 0,
    "IZANAGI_BREAK_MOCC_PERMUTATION": 0,
    "IZANAGI_BREAK_MOCC_EARLY_UNLOCK": 0,
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": 0,
    "IZANAGI_BREAK_NOREAD_VALIDATION": 0,
    "IZANAGI_BREAK_HIGHKEY_VALIDATION": 0,
    "IZANAGI_BREAK_WRITE_INTENT_ERASE": 0,
    "IZANAGI_BREAK_WRITE_INTENT_FORGE": 0,
    "IZANAGI_BREAK_WRITE_INTENT_OPSWAP": 0,
    "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP": 0,
    "IZANAGI_BREAK_TRIGGER_MISATTR": 0,
    "IZANAGI_BREAK_READ_LOCK_CHECK": 0,
    "IZANAGI_BREAK_NO_WRITE_TID_MAX": 0,
    "IZANAGI_BREAK_FIXED_COMMIT_VERSION": 0,
    "IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH": 0,
    "IZANAGI_BREAK_TAIL_COMMIT_OMISSION": 0,
    "IZANAGI_BREAK_NO_READ_TID_MAX": 0,
    "IZANAGI_BREAK_STALE_READ_PAYLOAD": 0,
    "IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD": 0,
    "IZANAGI_BREAK_SKIP_NODE_VALIDATION": 0,
    "IZANAGI_BREAK_STALE_READ_OWN_WRITE": 0,
    "IZANAGI_BREAK_REPEAT_UPDATE_BUFFER": 0,
    "IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF": 0,
    "IZANAGI_BREAK_REVERSE_WRITE_ORDER": 0,
    "IZANAGI_BREAK_CONSERVATIVE_ABORT": 0,
    "IZANAGI_SILO_LADDER_RUNG1": 0,
    "IZANAGI_SILO_LADDER_RUNG1_REPORT": 0,
}


def _condition_requests_for_genome(
        genome: Genome,
) -> tuple[condition_meaning_gate.DefineRequest, ...]:
    """Derive exact gate requests from the Genome passed to the build sink."""
    if type(genome) is not Genome:
        raise TypeError("condition gate genome は exact Genome が必要")
    macros = sorted(set(genome.flags) & set(condition_meaning_gate.DEFINE_SPECS))
    missing_defaults = set(macros).difference(_CONDITION_DEFAULTS)
    if missing_defaults:
        raise RuntimeError(
            "screening condition default が未宣言: "
            f"{sorted(missing_defaults)!r}"
        )
    requests = []
    for macro in macros:
        value = genome.flags[macro]
        if type(value) is not int:
            raise TypeError(
                f"screening Genome の domain macro は exact int が必要: {macro}"
            )
        default = _CONDITION_DEFAULTS[macro]
        spec = condition_meaning_gate.DEFINE_SPECS[macro]
        stock_comparison = value == default or str(value) in spec.inert_values
        requests.append(condition_meaning_gate.make_define_request(
            driver_id="orchestrator/campaign/screening_driver.py:evaluate_candidate",
            macro=macro,
            requested_value=value,
            default_value=default,
            stock_comparison=stock_comparison,
        ))
    return tuple(requests)


def _require_requests_match_genome_build_arguments(
        genome: Genome,
        requests: tuple[condition_meaning_gate.DefineRequest, ...],
) -> None:
    """Reject a gate route/value that the generic Genome build will not use."""
    configure_args = tuple(genome.cmake_defines())
    cxx_flag_values = tuple(
        argument.removeprefix("-DCMAKE_CXX_FLAGS=")
        for argument in configure_args
        if argument.startswith("-DCMAKE_CXX_FLAGS=")
    )
    for request in requests:
        required = ((request.macro, str(request.requested_value)), *(
            (macro, str(value)) for macro, value in request.companion_defines
        ))
        for macro, value in required:
            if request.route == condition_meaning_gate.ROUTE_CMAKE_CACHE:
                cache_variable = cmake_cache_variable_for_axis(
                    genome.protocol, macro,
                )
                present = f"-D{cache_variable}={value}" in configure_args
            elif request.route == condition_meaning_gate.ROUTE_CMAKE_CXX_FLAGS:
                define = f"-D{macro}={value}"
                present = any(
                    define in flags.split() for flags in cxx_flag_values
                )
            else:
                present = False
            if not present:
                raise condition_meaning_gate.ConditionMeaningGateError(
                    "screening-build-route-mismatch",
                    f"runtime Genome build arguments do not supply {macro}={value} "
                    f"through {request.route}",
                )


def _condition_gate_base_configure_args(genome: Genome) -> tuple[str, ...]:
    """Keep real non-domain build inputs; each request supplies its own domain arm."""
    domain_arguments = {
        f"-D{cmake_cache_variable_for_axis(genome.protocol, macro)}="
        f"{genome.flags[macro]}"
        for macro in set(genome.flags) & set(condition_meaning_gate.DEFINE_SPECS)
    }
    return tuple(
        argument for argument in genome.cmake_defines()
        if argument not in domain_arguments
    )


def _run_condition_gate_for_genome(
        source_root: str, genome: Genome, *, stock_root: Optional[str],
        cxx: str, cmake: str,
        backoff_fixed_declaration: Optional[
            condition_meaning_gate.MeaningWitnessDeclaration
        ] = None,
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
) -> Optional[_ScreeningConditionGateRun]:
    """Evaluate both arms for every domain macro supplied by this Genome.

    A non-None manifest is a proxy for the backoff screening route in the
    current call graph, not authority to supply dependencies.  On that route a
    prepared shared base lets calls that previously stopped before judgment
    solely because the base was unsupplied reach the unchanged gate judgment.
    Passing ``site=None`` makes each gate re-observe ``current_site()``.
    """
    requests = _condition_requests_for_genome(genome)
    if not requests:
        return None
    _require_requests_match_genome_build_arguments(genome, requests)
    with ExitStack() as stack:
        configure_args = _condition_gate_base_configure_args(genome)
        if expected_toolchain_manifest is not None:
            fetchcontent_base_dir = str(Path(stack.enter_context(
                tempfile.TemporaryDirectory(
                    prefix="izanagi-screening-condition-gate-",
                )
            )).resolve())
            buildcache.prepare_masstree_fetchcontent(
                ccbench_dir=source_root,
                fetchcontent_base_dir=fetchcontent_base_dir,
                expected_toolchain_manifest=expected_toolchain_manifest,
                configure_timeout_s=900,
                target_timeout_s=900,
                site=None,
            )
            configure_args = (
                *configure_args,
                f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base_dir}",
            )
        captured = condition_meaning_gate.capture_define_inputs(
            source_root,
            stock_root=stock_root,
            configure_args=configure_args,
        )
        supply_records = tuple(
            condition_meaning_gate.evaluate_define_supply_effectuation(
                captured, request=request, cxx=cxx, cmake=cmake,
            )
            for request in requests
        )
        meaning_records = tuple(
            condition_meaning_gate.evaluate_define_runtime_meaning(
                captured, request=request,
                declaration=(
                    backoff_fixed_declaration
                    if request.macro == "BACKOFF_FIXED" else None
                ),
                cxx=cxx,
            )
            for request in requests
        )
        admission = condition_meaning_gate.require_condition_gate_family(
            supply_records, meaning_records, use_class="raw",
        )
        if not admission.admitted:
            reasons = ", ".join(
                f"{record.macro}:{record.arm}="
                f"{record.terminal_status}/{record.reason_code}"
                for record in (*supply_records, *meaning_records)
                if record.terminal_status == "red"
            )
            raise condition_meaning_gate.ConditionMeaningGateError(
                "condition-family-rejected",
                "screening Genome condition gate rejected before evaluation: " + reasons,
            )
        return _ScreeningConditionGateRun(
            supply_records, meaning_records, admission,
        )


def _require_condition_gate_before_evaluation(
        source_root: str, ccbench_commit: str, genome: Genome, *,
        cxx: str, cmake: str,
        backoff_fixed_declaration: Optional[
            condition_meaning_gate.MeaningWitnessDeclaration
        ] = None,
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
) -> Optional[_ScreeningConditionGateRun]:
    """Provide stock identity when needed, then close the pre-build gate."""
    requests = _condition_requests_for_genome(genome)
    if not requests:
        return None
    _require_requests_match_genome_build_arguments(genome, requests)
    if not any(request.stock_comparison for request in requests):
        return _run_condition_gate_for_genome(
            source_root, genome, stock_root=None, cxx=cxx, cmake=cmake,
            expected_toolchain_manifest=expected_toolchain_manifest,
            backoff_fixed_declaration=backoff_fixed_declaration,
        )
    with patchharness.checkout(
            ccbench_commit, base_dir=source_root,
    ) as stock_root:
        return _run_condition_gate_for_genome(
            source_root, genome, stock_root=stock_root, cxx=cxx, cmake=cmake,
            expected_toolchain_manifest=expected_toolchain_manifest,
            backoff_fixed_declaration=backoff_fixed_declaration,
        )


def _default_calibration_dir(env_tag: Optional[str] = None) -> str:
    if env_tag is None:
        legacy_tags = tuple(
            contract.env_tag
            for contract in _env_contract.REGISTRY.values()
            if contract.attestation_mode == "none"
        )
        if len(legacy_tags) != 1:
            raise ValueError(
                "legacy screening calibration env_tag を一意に解決できない: "
                f"candidates={len(legacy_tags)}"
            )
        env_tag = legacy_tags[0]
    return os.path.join(env_scope_dir(env_tag), "calibration")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _attest_required_contract(
        contract: ExecutionEnvironmentContract, *,
        execution_receipt: Optional[dict] = None,
        verified_calibration: Optional[env_attestation.VerifiedCalibration] = None,
) -> tuple[
        Optional[dict], Optional[env_attestation.VerifiedCalibration],
]:
    """required contract の v2 receipt を発行または再検証する。

    screening は ``loop.run_campaign`` の認可入口を通らないため、この driver 自身が
    required calibration の hash-bound verification と strict attestation を build/eval
    より前に完了させる。既に同一 campaign で発行した値を渡された場合も、consumer 側の
    ``receipt_matches_contract`` で再検証してから返す。
    """
    if type(contract) is not ExecutionEnvironmentContract:
        raise TypeError("screening runtime contract は exact value が必要")
    if contract.attestation_mode == "none":
        if execution_receipt is not None or verified_calibration is not None:
            raise execution_guard.ExecutionGuardError(
                "mode=none screening に required attestation state が渡された"
            )
        return None, None
    if contract.attestation_mode != "required":
        raise execution_guard.ExecutionGuardError(
            f"未対応 attestation_mode: {contract.attestation_mode!r}"
        )
    if verified_calibration is None:
        verified_calibration = env_attestation.load_verified_calibration(
            contract, _repo_root(),
        )
    if execution_receipt is None:
        execution_receipt = execution_guard.attest_and_build_receipt(
            contract, verified_calibration,
        )
    if not execution_guard.receipt_matches_contract(
            execution_receipt,
            env_tag=contract.env_tag,
            contract_sha256=contract.contract_sha256,
            attestation_mode=contract.attestation_mode,
            verified_calibration=verified_calibration,
    ):
        raise execution_guard.ExecutionGuardError(
            "screening execution receipt の契約再検算に失敗"
        )
    return execution_receipt, verified_calibration


def attest_runtime_contract(
        contract: ExecutionEnvironmentContract, *,
        execution_receipt: Optional[dict] = None,
        verified_calibration: Optional[env_attestation.VerifiedCalibration] = None,
) -> tuple[
        Optional[dict], Optional[env_attestation.VerifiedCalibration],
]:
    """screening の build/eval 前に runtime attestation を確定する公開 seam。"""
    return _attest_required_contract(
        contract,
        execution_receipt=execution_receipt,
        verified_calibration=verified_calibration,
    )


# Mirrors orchestrator/campaign/between_run_floor.py; importing it adds a heavy dependency chain.
BETWEEN_RUN_FLOOR_SCHEMA_VERSION = "between-run-noise-floor/v1"


def load_between_run_floor(
    workload: Dict[str, str], *, protocol: str, calibration_dir: str = "",
) -> float:
    """protocol/workload が完全一致する between-run JSON を一意に選ぶ。"""
    root = calibration_dir or _default_calibration_dir()
    matches = []
    for path in sorted(glob.glob(os.path.join(root, "between_run_noise_*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"floor JSONを読めない: {path}: {exc}") from exc
        if not isinstance(doc, dict):
            raise ValueError(f"floor JSONのrootがobjectでない: {path}: {doc!r}")
        if ("schema_version" in doc
                and doc["schema_version"] != BETWEEN_RUN_FLOOR_SCHEMA_VERSION):
            raise ValueError(
                f"floor JSONのschema_versionが不一致: {path}: "
                f"{doc['schema_version']!r}")
        stored_workload = doc.get("workload")
        if isinstance(stored_workload, dict) and {
                str(k): str(v) for k, v in stored_workload.items()} == {
                str(k): str(v) for k, v in workload.items()}:
            try:
                stored_protocol = protocol_from_floor_genome(doc.get("genome"))
            except ValueError as exc:
                raise ValueError(
                    f"floor JSONのgenomeがcanonicalでない: {path}: "
                    f"{doc.get('genome')!r}"
                ) from exc
            if stored_protocol == protocol:
                matches.append((path, doc))
    if len(matches) != 1:
        raise ValueError(
            "protocol/workload対応のbetween-run floor JSONは一意に必要: "
            f"protocol={protocol!r}, workload={workload!r}, "
            f"matches={[p for p, _ in matches]!r}")
    path, doc = matches[0]
    between_run = doc.get("between_run")
    if not isinstance(between_run, dict):
        raise ValueError(f"between_run がobjectでない: {path}: {between_run!r}")
    floor = between_run.get("cv")
    if not isinstance(floor, (int, float)) or not 0 < floor < 1:
        raise ValueError(f"between_run.cv が欠落または範囲外: {path}: {floor!r}")
    return float(floor)


def _surface_repair(result: wal.WalTailRepairResult, log) -> None:
    if result.status == "repaired":
        log("[screening] WAL tail repair: " + json.dumps({
            "status": result.status,
            "original_size": result.original_size,
            "final_size": result.final_size,
            "removed_bytes": result.removed_bytes,
            "removed_sha256": result.removed_sha256,
            "preview": result.preview,
            "receipt_path": result.receipt_path,
        }, ensure_ascii=False, sort_keys=True))


def prepare_screening_campaign(
        base_cfg: CampaignConfig, workload: Dict[str, str], baseline_ref: str,
        measure_baseline: Callable[[CampaignConfig, CampaignLayout], None], *,
        authorization_contract: AuthorizedContract,
        env_tag: str, clocks_per_us: int, numactl: Sequence[str],
        protocol: str,
        calibration_dir: str = "", output_root: str = "", k: float = 1.5,
        high_abort_factor: float = 2.0,
        reanchor_threshold_s: float = 1800.0, log=print,
        build_context: BuildRunContext,
        env_contract: Optional[ExecutionEnvironmentContract] = None,
        execution_receipt: Optional[dict] = None,
        verified_calibration: Optional[env_attestation.VerifiedCalibration] = None,
        ) -> PreparedScreening:
    """identity焼き込み→同一campaign baseline実測→runtime config生成を一括実行する。"""
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if not baseline_ref:
        raise ValueError("baseline_ref が欠落")
    if "screening" in base_cfg.search_config:
        raise ValueError("base campaign config に既存 screening key がある")
    if k < 1.5:
        raise ValueError("k は 1.5 以上でなければならない")
    if high_abort_factor < 1.0:
        raise ValueError("high_abort_factor は 1.0 以上でなければならない")
    if reanchor_threshold_s <= 0:
        raise ValueError("reanchor_threshold_s は正でなければならない")
    authorization_kwargs = {
        "env_tag": env_tag,
        "clocks_per_us": clocks_per_us,
        "numactl": numactl,
    }
    if env_contract is not None:
        authorization_kwargs["env_contract"] = env_contract
    authorized_contract = execution_guard.require_certified_writer_authorization(
        authorization_contract, **authorization_kwargs,
    )
    execution_receipt, verified_calibration = _attest_required_contract(
        authorized_contract,
        execution_receipt=execution_receipt,
        verified_calibration=verified_calibration,
    )
    floor_root = calibration_dir or _default_calibration_dir(
        authorized_contract.env_tag,
    )
    floor = load_between_run_floor(
        workload, protocol=protocol, calibration_dir=floor_root,
    )
    policy = ident.screening_policy_search_config(
        baseline_ref, floor, k, high_abort_factor)
    cfg = replace(base_cfg, search_config={**base_cfg.search_config, **policy})
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, authorized_contract)
    layout = campaign_layout(str(ident.campaign_id(cfg)), output_root).ensure()
    _surface_repair(ident.ensure_resumable_wal(
        cfg, layout, admission_policy=build_context.policy,
    ), log)

    before = sum(1 for rec in wal.read_records(layout)
                 if rec.variant == baseline_ref and rec.stage == STAGE_BENCH_DONE)
    measure_baseline(cfg, layout)
    records = [rec for rec in wal.read_records(layout) if rec.variant == baseline_ref]
    benches = [rec for rec in records if rec.stage == STAGE_BENCH_DONE]
    commits = [rec for rec in records if rec.stage == STAGE_COMMIT]
    if len(benches) <= before:
        raise ValueError("baseline を同一campaign内で新規実測できなかった")
    if not commits or commits[-1].ts <= benches[-1].ts:
        raise ValueError("baseline の最新実測がCOMMITされていない")
    bench = benches[-1]
    median = bench.payload.get("median_tps")
    abort_rate = (bench.payload.get("leading_indicators") or {}).get("abort_rate")
    measured_at = bench.ts
    if not isinstance(median, (int, float)) or median <= 0:
        raise ValueError("baseline median_tps が欠落または非正")
    if not isinstance(abort_rate, (int, float)) or abort_rate < 0:
        raise ValueError("baseline abort_rate が欠落または負")
    if not isinstance(measured_at, (int, float)) or measured_at <= 0:
        raise ValueError("baseline 測定時刻が欠落または非正")
    screening = ScreeningConfig(
        baseline_tps=float(median), baseline_ref=baseline_ref,
        baseline_measured_at=float(measured_at), floor=floor, k=k,
        baseline_abort_rate=float(abort_rate), high_abort_factor=high_abort_factor,
        reanchor_threshold_s=reanchor_threshold_s)
    ident.verify_screening_preimage(screening, wal.read_lock(layout))
    return PreparedScreening(
        cfg=cfg,
        layout=layout,
        screening=screening,
        execution_receipt=execution_receipt,
        verified_calibration=verified_calibration,
    )


def evaluate_candidate(
        cfg: CampaignConfig, layout: CampaignLayout, genome: Genome,
        perf: PerfConfig, env_tag: str, clocks_per_us: int, *,
        authorization_contract: AuthorizedContract,
        build_context: BuildRunContext,
        screening: Optional[ScreeningConfig],
        capability_resolver: Optional[AdmissionCapabilityResolver] = None,
        env_contract=None,
        backoff_fixed_declaration: Optional[
            condition_meaning_gate.MeaningWitnessDeclaration
        ] = None,
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
        declared_use_class: Optional[str] = None,
        numactl: Optional[Sequence[str]] = None, src_token: Optional[str] = None,
        do_settle: bool = False, force: bool = False, log=print,
        ccbench_dir: str = "", cache_root: str = "",
        execution_receipt: Optional[dict] = None,
        verified_calibration: Optional[env_attestation.VerifiedCalibration] = None,
        ) -> Optional[EvalResult]:
    """sweep候補を1点評価する。forceはbaseline再アンカー専用。"""
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if expected_toolchain_manifest is not None and env_contract is None:
        raise ValueError(
            "expected_toolchain_manifest は env_contract 付き v2 screening に限る"
        )
    authorization_kwargs = {
        "env_tag": env_tag,
        "clocks_per_us": clocks_per_us,
        "numactl": numactl,
    }
    if env_contract is not None:
        authorization_kwargs["env_contract"] = env_contract
    authorized_contract = execution_guard.require_certified_writer_authorization(
        authorization_contract, **authorization_kwargs,
    )
    _attest_required_contract(
        authorized_contract,
        execution_receipt=execution_receipt,
        verified_calibration=verified_calibration,
    )
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, authorized_contract)
    _surface_repair(ident.ensure_resumable_wal(
        cfg, layout, admission_policy=build_context.policy,
    ), log)
    if expected_toolchain_manifest is None:
        _, resolved_cxx = buildcache.compilers_for_current_site()
        resolved_cmake = "cmake"
    else:
        _, resolved_cxx = buildcache.toolchain_compilers_from_manifest(
            expected_toolchain_manifest,
        )
        resolved_cmake = expected_toolchain_manifest["cmake"]["requested"]
    evidence_cxx = (
        buildcache.DEFAULT_CXX
        if resolved_cxx == buildcache.DEFAULT_CXX else resolved_cxx
    )
    evidence = source_digest.resolve_evidence(
        genome,
        cfg.ccbench_commit,
        ccbench_dir=ccbench_dir,
        cxx=evidence_cxx,
    )
    if src_token is not None and src_token != evidence.src_token:
        raise ValueError("src_token が current SourceEvidence と不一致")
    src_tok = evidence.src_token
    vid = variant_id(genome, src_tok)
    state = wal.replay(layout, admission_policy=build_context.policy).get(vid)
    # transient な環境故障 abort (identity/probe-error) は permanent skip にせず再評価する
    # (loop.py と同じ retryable 契約, D25/B-3)。
    if (not force and state is not None and state.terminal
            and not state.retryable_abort):
        return None
    perf_preflight_receipt = _perf_preflight.probe_perf_availability()
    use_perf = _perf_preflight.use_perf_from_receipt(perf_preflight_receipt)
    perf_evaluate_kwargs = {}
    if not use_perf:
        perf_evaluate_kwargs = {
            "use_perf": False,
            "perf_preflight_receipt": perf_preflight_receipt,
        }
    extra_correctness = None
    if cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2:
        extra_correctness = [(S2_TAG, s2_correctness_workload())]
    _require_condition_gate_before_evaluation(
        evidence.source_root,
        cfg.ccbench_commit,
        genome,
        cxx=resolved_cxx,
        cmake=resolved_cmake,
        expected_toolchain_manifest=expected_toolchain_manifest,
        backoff_fixed_declaration=backoff_fixed_declaration,
    )
    try:
        evaluate_kwargs = {
            "numactl": numactl,
            "do_settle": do_settle,
            "src_token": src_tok,
            "extra_correctness": extra_correctness,
            "screening": screening,
            "log": log,
            "ccbench_dir": ccbench_dir,
            "cache_root": cache_root,
            "build_context": build_context,
            "capability_resolver": capability_resolver,
            "source_evidence": evidence,
        }
        if env_contract is not None:
            evaluate_kwargs["env_contract"] = authorized_contract
            evaluate_kwargs["declared_use_class"] = declared_use_class
            if expected_toolchain_manifest is not None:
                evaluate_kwargs["expected_toolchain_manifest"] = (
                    expected_toolchain_manifest
                )
        return evaluate(
            genome, layout, env_tag, cfg.ccbench_commit, perf, clocks_per_us,
            authorization_contract=authorization_contract,
            **evaluate_kwargs, **perf_evaluate_kwargs)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:  # candidate固有失敗をWALへ隔離。loop.pyと同じ境界。
        if isinstance(exc, (wal.WalAppendError, wal.WalFramingError)):
            raise
        payload = {"reason": f"eval-exception: {type(exc).__name__}: {exc}"}
        replayed = wal.replay(layout, admission_policy=build_context.policy).get(vid)
        if replayed is not None:
            active = [
                attempt for attempt in replayed.attempts.values()
                if not attempt.committed and not attempt.aborted
            ]
            if len(active) == 1:
                payload["build_attempt_id"] = active[0].attempt_id
                if active[0].receipt_sha256 is not None:
                    payload["build_admission_receipt_sha256"] = active[0].receipt_sha256
        wal.log(layout, vid, STAGE_ABORT, env_tag, payload)
        return EvalResult(genome=genome, variant=vid, certified=False, aborted=True,
                          notes=[f"評価中の例外 → reject ({exc})"])
