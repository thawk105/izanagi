# -*- coding: utf-8 -*-
"""P2-2: silo 全探索 (最初の実探索) — 実 fitness 計測 (直列, env=linux-baremetal)。

silo の有効 8 genome (genome.SILO_SPACE, no-wait XOR) を確定 calibration
(records=1m / 48thread / skew0.9, clocks_per_us=1800) で実機計測し、代表 workload
ごとに最速構成を分布比較で特定する (compare は p2_2_report.py が WAL から行う)。

**計測する** ので絶対規律4: 単一テナント直列。bench は pipeline が bench_lock + settle
で排他・静定する。workload ごとに独立 campaign (search_config に workload を刻む) →
WAL も別 → リカバリ独立 (途中で落ちても再実行で続きから)。

代表 workload は contention 域 (skew=0.9) を固定し read/write 比を振る:
  - read-heavy   : ycsb_rratio=95
  - balanced     : ycsb_rratio=50  (= 確定 calibration の点 = high-contention)
  - write-heavy  : ycsb_rratio=5
records は working set (tuple 数) 駆動なので rratio 不変 → 1m を全 workload で共有
(calibration §下限基準, D15)。rmw=0 は calibration と同じ (read set と write set を分離)。

  python orchestrator/campaign/p2_2.py            # 全 workload
  python orchestrator/campaign/p2_2.py read-heavy # 1 workload だけ
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.genome import SILO_SPACE                          # noqa: E402
from campaign.loop import run_campaign                          # noqa: E402
from campaign.model import CampaignConfig                       # noqa: E402
from campaign.pipeline import PerfConfig                        # noqa: E402

CCBENCH_COMMIT = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

# 確定 calibration (worklog 2026-06-18, output/env/linux-baremetal/calibration)。
RECORDS = 1_000_000
THREADS = 48
EXTIME = 3
REPS = 5

# 代表 workload。skew=0.9 固定で rratio を振る (rmw=0 は calibration と同じ)。
WORKLOADS = [
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
]


def _competing_bench_pids() -> list:
    """他に走っている ccbench ベンチ (build-variants 下の ycsb_*.exe) の PID 一覧。

    settle() の load average は 1 分 EMA で laggy (汚染が始まった直後は検知できず、
    自分の直前 run の残像では誤検知する)。競合プロセスの直接確認はラグなしの確定信号
    なので、計測を始める前にこれで machine が単一テナントかを確かめる (絶対規律4)。
    pre-flight 時点で自分のベンチはまだ走っていない → 拾えるのは他者/孤児だけ。"""
    try:
        r = subprocess.run(["pgrep", "-af", r"build-variants/.*ycsb_.*\.exe"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return []
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def _assert_single_tenant() -> None:
    """競合ベンチが走っていたら計測を拒否する (規律4: 汚染した数値は無価値)。

    孤児/他者のプロセスを勝手に kill しない (規律6: 素性不明な実行物は人間が判断)。
    検出したら PID を表に出して停止する。"""
    comp = _competing_bench_pids()
    if comp:
        msg = ("競合する ccbench ベンチが稼働中 → 計測は規律4 違反になるので拒否する。\n"
               "  該当プロセス (孤児なら kill、他者の作業なら待つ — 自動で殺さない):\n"
               + "\n".join(f"    {ln}" for ln in comp))
        raise RuntimeError(msg)


def config_for(tag: str, workload: dict) -> CampaignConfig:
    """workload タグ → CampaignConfig。レポート生成器が同じ campaign-id を再計算して
    WAL を引けるよう、campaign 同一性を決める入力をここに集約する (D13)。"""
    return CampaignConfig(
        spec_slug=f"p2-2-silo-{tag}", search_tag="enumerate",
        spec_content=f"P2-2: silo 全探索 (実 fitness) — workload={tag}",
        ccbench_commit=CCBENCH_COMMIT,
        search_config={"scale": "silo", "space": "xor-8", "workload": tag,
                       "records": RECORDS, "threads": THREADS,
                       "ycsb": workload},
        trial="p2-2")


def run_workload(tag: str, workload: dict, log=print):
    _assert_single_tenant()
    genomes = SILO_SPACE.enumerate()
    cfg = config_for(tag, workload)
    perf = PerfConfig(records=RECORDS, threads=THREADS, workload=workload,
                      extime=EXTIME, reps=REPS)

    log(f"\n=== P2-2 workload={tag}  ({workload})  {len(genomes)} genome ===")
    s = run_campaign(cfg, genomes, perf, ENV_TAG, CLK, numactl=NUMA, log=log)

    rows = [(r.fitness_tps, r) for r in s.results if r.fitness_tps is not None]
    rows.sort(key=lambda t: t[0], reverse=True)
    log(f"\n  --- {tag}: fitness ランキング (committed={s.committed} "
        f"aborted={s.aborted} skipped={s.skipped}) ---")
    for tps, r in rows:
        log(f"    {tps:>12,.0f} tps  CV {r.cv * 100:4.2f}%"
            f"{'  ⚠UNSTABLE' if r.unstable else ''}  {r.genome.canonical()}")
    for r in (r for r in s.results if r.aborted):
        log(f"    ✗ ABORT {r.genome.canonical()}: {r.verdict} / {r.notes}")
    return s


def main(argv) -> int:
    sel = argv[1] if len(argv) > 1 else None
    wls = [w for w in WORKLOADS if sel is None or w[0] == sel]
    if not wls:
        print(f"unknown workload: {sel} (選択肢: {[w[0] for w in WORKLOADS]})")
        return 2
    summaries = []
    for tag, workload in wls:
        summaries.append((tag, run_workload(tag, workload)))
    print("\n=== P2-2 完了 ===")
    for tag, s in summaries:
        print(f"  {tag}: {s.campaign_id}  committed={s.committed} "
              f"aborted={s.aborted}")
    ok = all(s.aborted == 0 for _, s in summaries)
    print(f"P2-2: {'全 genome 計測成功' if ok else 'abort あり (要確認)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
