# -*- coding: utf-8 -*-
"""P2-0: silo 全 genome の verifier 大規模 sanity (Phase 2)。

パラメータ variant は CCBench 由来のフラグ組み合わせなので理屈上全部正しい。silo の有効
genome 全 12 を build(trace+perf)→verify→no-bench commit で回し、**全て certified** を確認
する = verifier が大量の正しい variant を緑と判定できる実証 (Phase 1 タスク3「赤を出せる」と
対になる「緑を取りこぼさない」の大規模版)。

**計測しない** (do_bench=False) ので絶対規律4 とは無関係。build と trace 検証のみ。

  python orchestrator/campaign/sanity_silo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.genome import SILO_SPACE                          # noqa: E402
from campaign.loop import run_campaign                          # noqa: E402
from campaign.model import CampaignConfig                       # noqa: E402
from campaign.pipeline import PerfConfig                        # noqa: E402

CCBENCH_COMMIT = "6656e93"
ENV_TAG = "linux-baremetal"
CLK = 1800


def _trace_evaluable(g) -> bool:
    """両 no-wait=0 (wait validation) は全 workload で trace 取得が timeout (評価不能、
    insight 2026-06-19_ccbench-silo-wal-ftruncate-xor-bug.md 副次発見)。trace sanity から
    外す。構成病理か trace I/O 特有かは perf build で P2-2 確認 (動けば genome 空間に残す)。"""
    return not (g.flags["NO_WAIT_LOCKING_IN_VALIDATION"] == 0
                and g.flags["NO_WAIT_OF_TICTOC"] == 0)


def main() -> int:
    genomes = [g for g in SILO_SPACE.enumerate() if _trace_evaluable(g)]
    cfg = CampaignConfig(
        spec_slug="sanity-silo", search_tag="enumerate",
        spec_content="P2-0: silo 全 genome の verifier 大規模 sanity",
        ccbench_commit=CCBENCH_COMMIT,
        search_config={"scale": "silo", "space": "full-2^4-constrained"},
        trial="p2-0-sanity")
    # 計測しないので perf は使わないが API 上必要 (do_bench=False で無視される)。
    perf = PerfConfig(records=1000, threads=4)

    print(f"=== P2-0: silo {len(genomes)} genome verifier sanity (do_bench=False) ===")
    for g in genomes:
        print(f"  - {g.canonical()}")
    s = run_campaign(cfg, genomes, perf, ENV_TAG, CLK, do_bench=False)

    print(f"\n committed(certified)={s.committed} aborted={s.aborted} "
          f"skipped={s.skipped} (of {s.total})")
    for r in (r for r in s.results if r.aborted):
        print(f"  ✗ {r.genome.canonical()}: {r.verdict} / {r.notes}")
    ok = (s.committed == len(genomes) and s.aborted == 0)
    print(f"\nP2-0 verifier 大規模 sanity: {'PASS' if ok else 'FAIL'} "
          f"(全 {len(genomes)} genome certified={ok})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
