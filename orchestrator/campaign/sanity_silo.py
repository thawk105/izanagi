# -*- coding: utf-8 -*-
"""P2-0: silo 全 genome の verifier 大規模 sanity (Phase 2)。

パラメータ variant は CCBench 由来のフラグ組み合わせなので理屈上全部正しい。silo の有効
genome 全 8 を build(trace+perf)→verify→no-bench commit で回し、**全て certified** を確認
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
from campaign import env_contract                              # noqa: E402
from campaign.build_admission import GeneratorId, build_run_context  # noqa: E402
from campaign.loop import run_campaign                          # noqa: E402
from campaign.model import CampaignConfig                       # noqa: E402
from campaign.pipeline import PerfConfig                        # noqa: E402

# 歴史的 pin を意図的に保持 (IDENT-1/IDENT-3、pin.py docstring 参照)。
# 再走には submodule を dff0f1e へ checkout する。
CCBENCH_COMMIT = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800


def main() -> int:
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    # 両 no-wait=0 (wait validation) は livelock で計測不能と P2-2 で確定したため、
    # SILO_SPACE.enumerate() が no-wait XOR 制約で最初から除外する (= 8 genome)。
    # P2-0 当時の手動除外 (_trace_evaluable) は genome.py の制約に昇格して不要になった。
    # insight 2026-06-22_silo-both-no-wait-zero-livelock.md
    genomes = SILO_SPACE.enumerate()
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
    authorization = env_contract.authorize(ENV_TAG)
    contract = authorization.contract
    s = run_campaign(
        cfg, genomes, perf, ENV_TAG, CLK, numactl=list(contract.numactl),
        do_bench=False, authorization_contract=authorization,
        build_context=build_context,
    )

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
