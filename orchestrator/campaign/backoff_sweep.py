# -*- coding: utf-8 -*-
"""P2 ケーススタディ: silo の backoff 量を単一軸として sweep (Phase 2→3 の橋渡し)。

critic が leading indicators から「BACK_OFF=1 は abort を減らせているのに ipc 崩壊で
遅い (over-throttling)」と帰属し、新軸「中間/適応 backoff」を提案した。ソースを見ると
CCBench の backoff は**既に Cicada 適応 backoff** で、その適応 hill-climbing 自体が
48thread 高競合で throughput を殺す値に収束しているのが BACK_OFF=1 の正体だった
(insight 2026-06-22_p2-3-critic-leading-indicator-attribution.md)。

そこで定義済みフラグ空間 (binary BACK_OFF) の**外**へ出て、backoff の*量*を静的に
固定する新フラグ `CCBENCH_BACKOFF_FIXED` (patches/silo-backoff-fixed.patch, default -1=
stock 適応で inert) を導入し、量を sweep して「適応 backoff が逃した sweet spot が
あるか」を測る。各 genome は pipeline で build→**verify (正しさゲート, 規律2)**→bench。
backoff は timing のみ変える (CC 論理は不変) ので serializable のはずだが**必ず検証**する。

  python orchestrator/campaign/backoff_sweep.py            # 全 workload
  python orchestrator/campaign/backoff_sweep.py write-heavy
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from typing import Optional
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .loop import run_campaign                          # noqa: E402
from .build_admission import (BuildRunContext, GeneratorId,  # noqa: E402
                                      attest_generator_output, build_run_context)
from .layout import CampaignLayout                      # noqa: E402
from .model import CampaignConfig, Genome               # noqa: E402
from .p2_2 import (CLK, ENV_TAG, EXTIME, NUMA, RECORDS,  # noqa: E402
                           REPS, THREADS, _assert_single_tenant)
from .pipeline import PerfConfig                        # noqa: E402
from . import (env_contract, ident, pin, screening_driver,
                      source_digest, wal)  # noqa: E402
from .loop import CampaignSummary                       # noqa: E402
from .pipeline import SCREEN_REJECTION_REASON, variant_id  # noqa: E402


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


def genomes():
    """L-W0 を base に: 無 backoff 参照 / stock 適応 / 静的 sweep。"""
    gs = [Genome("silo", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}),   # 無 backoff
          Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})]   # stock 適応
    for n in SWEEP_US:
        gs.append(Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": n}))  # 静的 N
    return gs


def config_for(tag: str, workload: dict, *,
               screening_fixed_us: Optional[int] = None) -> CampaignConfig:
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
    return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))


def _run_screened_workload(cfg, gs, perf, workload, calibration_dir, log, *,
                           build_context: BuildRunContext,
                           capability_resolver,
                           confirm_each_candidate=False):
    baseline = gs[0]
    baseline_ref = variant_id(
        baseline, source_digest.resolve(baseline, cfg.ccbench_commit))
    measured = []

    def measure_baseline(screen_cfg, layout):
        measured.append(screening_driver.evaluate_candidate(
            screen_cfg, layout, baseline, perf, ENV_TAG, CLK,
            authorization_contract=env_contract.authorize(ENV_TAG),
            build_context=build_context,
            capability_resolver=capability_resolver,
            screening=None, numactl=NUMA, force=True, do_settle=True, log=log))

    prepared = screening_driver.prepare_screening_campaign(
        cfg, workload, baseline_ref, measure_baseline,
        authorization_contract=env_contract.authorize(ENV_TAG),
        env_tag=ENV_TAG, clocks_per_us=CLK, numactl=NUMA,
        calibration_dir=calibration_dir, build_context=build_context)
    s = CampaignSummary(campaign_id=str(ident.campaign_id(prepared.cfg)),
                        layout_root=prepared.layout.root, total=len(gs))
    results = [measured[0]]
    for genome in gs[1:]:
        if confirm_each_candidate:
            input("screened candidate 直前の単一テナント/高CPU確認後に Enter: ")
        _assert_single_tenant()
        results.append(screening_driver.evaluate_candidate(
            prepared.cfg, prepared.layout, genome, perf, ENV_TAG, CLK,
            authorization_contract=env_contract.authorize(ENV_TAG),
            build_context=build_context,
            capability_resolver=capability_resolver,
            screening=prepared.screening, numactl=NUMA, log=log))
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
    cfg = config_for(tag, workload, screening_fixed_us=screening_fixed_us)
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
    if screening_enabled:
        s = _run_screened_workload(
            cfg, gs, perf, workload, calibration_dir, log,
            build_context=build_context,
            capability_resolver=capability_resolver,
            confirm_each_candidate=confirm_each_candidate)
    else:
        s = run_campaign(cfg, gs, perf, ENV_TAG, CLK, numactl=NUMA, log=log,
                         authorization_contract=env_contract.authorize(ENV_TAG),
                         build_context=build_context,
                         capability_resolver=capability_resolver)

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
                    help="between_run_noise_*.jsonの置き場 (省略時はlinux-baremetal正本)")
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
