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

import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .genome import SILO_SPACE                          # noqa: E402
from . import env_contract                              # noqa: E402
from .build_admission import GeneratorId, build_run_context  # noqa: E402
from .layout import repo_output_root                    # noqa: E402
from .loop import run_campaign                          # noqa: E402
from .model import CampaignConfig                       # noqa: E402
from .pipeline import PerfConfig                        # noqa: E402


# 歴史的 pin を意図的に保持 (IDENT-1/IDENT-3、pin.py docstring 参照)。
# 再走には submodule を dff0f1e へ checkout する。
CCBENCH_COMMIT = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

# 確定 calibration (worklog 2026-06-18, output/env/linux-baremetal/calibration)。
RECORDS = 1_000_000
THREADS = 48
EXTIME = 3
REPS = 5

# A2: noise floor は用途で 2 種 (roadmap §3.6(3'))。混同すると偽 faster を出す。
#   within-run = その 1 測定の品質 (= remeasure 品質ゲート)。calibration noise_floor.cv = 2.28%。
#   between-run = **差が信用できるかの下限** (= compare の丸め閾値)。variant/baseline は別 run で
#     測るので採否 floor はこちら。
# between_run_floor.py で B0-L-W0 baseline を確定動作点で 8 独立セッション実測した結果、fresh な
# same-window between は write: 0.67% (within 2.19% より低) / balanced: 1.07% (within 1.07% と同値)
# = back-to-back では下がりこそすれ within を上回らない楽観的下限と判明 (median 集約 + 熱/周波数/
# cache 共有で真の run 間ドリフトを捉えない)。よって floor は fresh 値でなく **時間分離された
# cross-campaign の genuine データ** に錨を打つ:
#   no-backoff CV(n=2, sweep vs repro) = 2.09% (write) / 1.53% (balanced)、high-abort within ≤2.91%。
# 観測された最悪の run 間分散 (~2.91%) をカバーする保守値 = 0.030。
WITHIN_RUN_CV = 0.0228       # 旧 NOISE_CV_SKEW09。compare には使わない (within の参考/表示用)
BETWEEN_RUN_CV = 0.030       # 採否 floor。cross-campaign genuine + high-abort within の保守側 (~3%)

# 代表 workload。skew=0.9 固定で rratio を振る (rmw=0 は calibration と同じ)。
WORKLOADS = [
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
]


def _competing_bench_pids() -> list:
    """競合ベンチ検知 (canonical は calibrator.runner)。driver の pre-flight 用に再公開。

    pipeline も同じ runner.competing_bench_pids を bench 直前に呼ぶ (admission fails-closed)。
    driver は campaign 冒頭、pipeline は genome ごと = 二段の単一テナント保証 (絶対規律4)。"""
    from ..calibrator.runner import competing_bench_pids
    return competing_bench_pids()


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


def _assert_matches_calibration() -> None:
    """RECORDS/THREADS の手書き値が確定 calibration (D15) と一致するか実行時照合する。

    値は calibrator が決めた動作点の手書きコピーなので、再 calibration 後に sync を
    漏らすと黙って古い動作点で測る (規律4 が人手同期に退化する)。commit/digest と同じ
    honest-by-construction: JSON 不在・キー欠落・不一致は fails-closed で停止。"""
    path = os.path.join(repo_output_root(), "env", ENV_TAG, "calibration",
                        "calibration_t48_skew0p9_rr50_rmw0.json")
    if not os.path.exists(path):
        raise RuntimeError(f"確定 calibration が無い: {path} (規律4: 動作点を照合できない"
                           "まま計測しない。calibrator を先に回すこと)")
    with open(path, encoding="utf-8") as f:
        cal = json.load(f)
    cal_records = (cal.get("saturation") or {}).get("records")
    cal_threads = cal.get("threads")
    if cal_records != RECORDS or cal_threads != THREADS:
        raise RuntimeError(
            f"RECORDS/THREADS が確定 calibration とずれている: 手書き "
            f"({RECORDS}, {THREADS}) != calibration ({cal_records}, {cal_threads})。"
            "再 calibration 後の sync 漏れ (規律4)。p2_2.py の定数を更新すること")


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
    _assert_matches_calibration()
    genomes = SILO_SPACE.enumerate()
    cfg = config_for(tag, workload)
    perf = PerfConfig(records=RECORDS, threads=THREADS, workload=workload,
                      extime=EXTIME, reps=REPS)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)

    log(f"\n=== P2-2 workload={tag}  ({workload})  {len(genomes)} genome ===")
    s = run_campaign(cfg, genomes, perf, ENV_TAG, CLK, numactl=NUMA, log=log,
                     authorization_contract=env_contract.authorize(ENV_TAG),
                     build_context=build_context,
                     declared_use_class="official")

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
