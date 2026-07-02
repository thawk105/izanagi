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

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.loop import run_campaign                          # noqa: E402
from campaign.model import CampaignConfig, Genome               # noqa: E402
from campaign.p2_2 import (CLK, ENV_TAG, EXTIME, NUMA, RECORDS,  # noqa: E402
                           REPS, THREADS, _assert_single_tenant)
from campaign.pipeline import PerfConfig                        # noqa: E402

CCBENCH_COMMIT = "dff0f1e"

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


def config_for(tag: str, workload: dict) -> CampaignConfig:
    return CampaignConfig(
        spec_slug=f"backoff-sweep-silo-{tag}", search_tag="sweep",
        spec_content=f"P2 case study: silo static-backoff sweep — workload={tag}",
        ccbench_commit=CCBENCH_COMMIT,
        search_config={"scale": "silo-backoff", "base": "L-W0",
                       "sweep_us": SWEEP_US, "workload": tag,
                       "records": RECORDS, "threads": THREADS, "ycsb": workload},
        trial="p2-backoff")


def run_workload(tag: str, workload: dict, log=print):
    _assert_single_tenant()
    gs = genomes()
    cfg = config_for(tag, workload)
    perf = PerfConfig(records=RECORDS, threads=THREADS, workload=workload,
                      extime=EXTIME, reps=REPS)
    log(f"\n=== backoff sweep  workload={tag}  ({workload})  {len(gs)} genome ===")
    s = run_campaign(cfg, gs, perf, ENV_TAG, CLK, numactl=NUMA, log=log)

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
    sel = argv[1] if len(argv) > 1 else None
    wls = [w for w in WORKLOADS if sel is None or w[0] == sel]
    if not wls:
        print(f"unknown workload: {sel} (選択肢: {[w[0] for w in WORKLOADS]})")
        return 2
    summaries = [(tag, run_workload(tag, wl)) for tag, wl in wls]
    print("\n=== backoff sweep 完了 ===")
    for tag, s in summaries:
        print(f"  {tag}: {s.campaign_id}  committed={s.committed} aborted={s.aborted}")
    ok = all(s.aborted == 0 for _, s in summaries)
    print(f"backoff sweep: {'全 genome 計測成功' if ok else 'abort あり (要確認)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
