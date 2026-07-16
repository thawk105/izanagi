# -*- coding: utf-8 -*-
"""[P1] over-throttling 直接実測 — backoff スピン時間占有率を量の関数として測る。

backoff ケーススタディの最致命の穴は「stock 適応が sweet spot を桁で行き過ぎ低 ipc 域に
駐車」を ipc/latency からの**外挿**でしか示せていなかったこと。ccbench の ODR バグ
(ADD_ANALYSIS+BACK_OFF segfault, PR #118 で修正) を直して `backoff_latency_rate`
(= total_backoff_latency / 全スレッドサイクル = machine の何割を backoff スピンに費やしたか)
が使えるようになったので、**スピン時間を量の関数として直接実測**する。

各 genome (L-W0 base, **ADD_ANALYSIS=1**) を確定 calibration (1m/48thread/skew0.9) で回し:
  - none (BACK_OFF=0): スピン 0
  - 静的 {2..100}us: スピン占有率が量とともに増える曲線
  - stock 適応: その占有率が静的のどこに駐車するか (sweet spot 10us 相当を超えていれば over-throttling を実測)
を測る。`backoff_latency_rate` は比なので ADD_ANALYSIS の計装オーバーヘッドに頑健
(throughput は ADD_ANALYSIS で歪むので絶対比較しない。**正しさは ADD_ANALYSIS=0 build で検証済み**、
これは backoff 内部の診断専用)。

  python orchestrator/campaign/backoff_overthrottle.py [workload]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibrator.benchparse import abort_rate                     # noqa: E402
from calibrator.runner import run_once                            # noqa: E402
from campaign import buildcache                                   # noqa: E402
from campaign.backoff_sweep import SWEEP_US, _BASE                # noqa: E402
from campaign.model import Genome                                 # noqa: E402
from campaign.p2_2 import (CCBENCH_COMMIT, CLK, NUMA, RECORDS,     # noqa: E402
                           THREADS, _assert_single_tenant)

EXTIME = 3
REPS = 3

WORKLOADS = {
    "write-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
    "read-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
}


def _points():
    """(label, flags) — none / adaptive / 静的 sweep。全て ADD_ANALYSIS=1。"""
    aa = {"ADD_ANALYSIS": 1}
    pts = [("none", {**_BASE, **aa, "BACK_OFF": 0, "BACKOFF_FIXED": -1}),
           ("adaptive", {**_BASE, **aa, "BACK_OFF": 1, "BACKOFF_FIXED": -1})]
    for n in SWEEP_US:
        pts.append((f"fixed-{n}us", {**_BASE, **aa, "BACK_OFF": 1, "BACKOFF_FIXED": n}))
    return pts


def _flags(workload: dict):
    base = [f"-thread_num={THREADS}", f"-ycsb_tuple_num={RECORDS}",
            f"-extime={EXTIME}", f"-clocks_per_us={CLK}"]
    return base + [f"-{k}={v}" for k, v in workload.items()]


def measure(tag: str, workload: dict, log=print):
    _assert_single_tenant()
    log(f"\n=== over-throttling 実測  workload={tag}  (1m/{THREADS}thread, ADD_ANALYSIS=1) ===")
    log(f"{'label':>12} | {'backoff_spin%':>13} | {'abort%':>7} | {'tps(AA計装込)':>14} | "
        f"{'eff_tps=tps/(1-spin)':>20}")
    rows = []
    for label, flags in _points():
        g = Genome("silo", flags)
        b = buildcache.build(g, CCBENCH_COMMIT, trace=False)
        spins, tpss, aborts = [], [], []
        for _ in range(REPS):
            m, _c, _w = run_once(b.binary, _flags(workload), numactl=NUMA)
            spins.append(float(m.get("backoff_latency_rate", "0") or 0))
            tv = m.get("throughput[tps]")
            tpss.append(float(tv) if tv else 0.0)
            av = abort_rate(m)
            aborts.append(av if av is not None else 0.0)
        spin = sorted(spins)[len(spins) // 2]
        tps = sorted(tpss)[len(tpss) // 2]
        ab = sorted(aborts)[len(aborts) // 2]
        eff = tps / (1 - spin) if spin < 1 else 0.0
        log(f"{label:>12} | {spin * 100:>12.2f}% | {ab * 100:>6.1f}% | {tps:>14,.0f} | "
            f"{eff:>20,.0f}")
        rows.append({"label": label, "backoff_us": flags["BACKOFF_FIXED"],
                     "back_off": flags["BACK_OFF"], "spin_rate": spin,
                     "abort_rate": ab, "tps_aa": tps, "eff_tps": eff})
    return rows


def main(argv) -> int:
    sel = argv[1] if len(argv) > 1 else None
    tags = [sel] if sel in WORKLOADS else list(WORKLOADS)
    for tag in tags:
        rows = measure(tag, WORKLOADS[tag])
        statics = [r for r in rows if r["back_off"] == 1 and r["backoff_us"] >= 0]
        adaptive = next((r for r in rows if r["back_off"] == 1 and r["backoff_us"] < 0), None)
        if statics and adaptive:
            # 適応のスピン占有率を超えない最大の静的点 = 適応が「どの量に駐車しているか」の下限
            over = [r for r in statics if r["spin_rate"] <= adaptive["spin_rate"]]
            parked = max((r["backoff_us"] for r in over), default=None)
            # over-throttling 判定 = 「sweet spot 上限 (fitness 実測 5-10us) を超えて駐車」。
            # 閾値はハードコード 25 でなく sweet spot 上限から導出 (grid 変更で暗黙にずれない)
            sweet_spot_max_us = 10
            print(f"\n[{tag}] 適応の backoff スピン占有率 = {adaptive['spin_rate']*100:.1f}% "
                  f"→ 静的 {parked}us 以上に相当 (sweet spot は別途 fitness で 5-{sweet_spot_max_us}us)。"
                  f"{'適応は sweet spot を超えて駐車 = over-throttling を実測' if (parked or 0) > sweet_spot_max_us else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
