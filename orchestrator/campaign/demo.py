# -*- coding: utf-8 -*-
"""探索ループの end-to-end 配線テスト (Phase 1 タスク6)。

silo の小さな genome 部分集合を campaign ループに通し、
  build(trace+perf) → verify(正しさゲート) → bench(排他+静定) → commit(WAL)
が回ることと、**2 回目の起動でリカバリが評価済みをスキップする**ことを実機で確認する。

これは「Linux が届いた時点で実機で回すだけ」の状態 (タスク6 完了条件) の実証。小さい
perf config で速く回す配線テストであり、ここの fitness 数値は baseline ではない
(trial='wiring' の独立 campaign に隔離)。本番の fitness は確定 calibration を使う。

  python orchestrator/campaign/demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.loop import run_campaign                          # noqa: E402
from campaign import env_contract                              # noqa: E402
from campaign.build_admission import (GeneratorId, build_run_context)  # noqa: E402
from campaign.model import CampaignConfig, Genome               # noqa: E402
from campaign.pipeline import PerfConfig                        # noqa: E402

# 歴史的 pin を意図的に保持 (IDENT-1/IDENT-3、pin.py docstring 参照)。
# 再走には submodule を dff0f1e へ checkout する。
CCBENCH_COMMIT = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

# 配線確認用の 2 genome (BACK_OFF だけ違う、共に正しい silo)。
_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
GENOMES = [
    Genome("silo", {**_BASE, "BACK_OFF": 1}),
    Genome("silo", {**_BASE, "BACK_OFF": 0}),
]


def main() -> int:
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = CampaignConfig(
        spec_slug="wiring-silo", search_tag="enumerate",
        spec_content="demo: silo BACK_OFF ablation", ccbench_commit=CCBENCH_COMMIT,
        search_config={"scale": "silo", "tier": "0-1"}, trial="wiring")
    perf = PerfConfig(records=100_000, threads=4,
                      workload={"ycsb_rratio": "50", "ycsb_zipf_skew": "0.9",
                                "ycsb_rmw": "false"}, extime=1, reps=2)

    print("=== run 1 (cold: build → verify → bench → commit) ===")
    s1 = run_campaign(cfg, GENOMES, perf, ENV_TAG, CLK, numactl=NUMA,
                      authorization_contract=env_contract.lookup(ENV_TAG),
                      build_context=build_context)
    print(f"  committed={s1.committed} aborted={s1.aborted} skipped={s1.skipped}")
    for r in s1.results:
        print(f"    {r.genome.canonical()}: certified={r.certified} "
              f"fitness={r.fitness_tps}")

    print("\n=== run 2 (recovery: 評価済みは WAL から skip) ===")
    s2 = run_campaign(cfg, GENOMES, perf, ENV_TAG, CLK, numactl=NUMA,
                      authorization_contract=env_contract.lookup(ENV_TAG),
                      build_context=build_context)
    print(f"  evaluated={s2.evaluated} skipped={s2.skipped}")

    ok = (s1.committed == 2 and s1.aborted == 0
          and s2.skipped == 2 and s2.evaluated == 0
          and s1.campaign_id == s2.campaign_id)
    print(f"\n配線テスト: {'PASS' if ok else 'FAIL'} "
          f"(campaign-id 安定={s1.campaign_id == s2.campaign_id}, "
          f"run1 commit 2={s1.committed == 2}, run2 全 skip={s2.skipped == 2})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
