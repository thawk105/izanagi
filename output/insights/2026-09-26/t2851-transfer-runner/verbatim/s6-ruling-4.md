# 段 6 裁定 (受入赤への対応) — 2026-09-26 11:30 JST、受入 attempt 1 (tested tip dc41d40ce、main 856cdbcda を取り込み済み)

受入全走で赤 3 件 (F945 型ではない)。本文 (junit `<failure message=`):
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites` と
  `::test_reviewed_process_launch_inventory_is_recursive_and_exact`: 観測した launch site の Counter に
  `('campaign/t2851_transfer_runner.py', '<module>._probe')` と `('campaign/t2851_transfer_runner.py', '<module>.run_job.once.capture')` が余分。
- `orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`: 同じ 2 site が未登録。

判定: **本 wave に帰属する real 赤**。新 module が process launch site を 2 つ足したのに、review 済み inventory へ分類していない (段 5 実装子が制約 meta-test を洗い出していなかった)。

裁定 (採用): inventory の設計 (`test_ccbench_spawn_sites.py` の「a new launch must be classified in review before this test can pass」) に従い、
2 site を理由 comment 付きで分類登録する。これは受理集合を変えない登録であり、検査の弱体化ではない。
- `_probe` の TPC-C 用 `pgrep -af 'tpcc_.*\.exe'`: 固定 argv・shell なし・timeout 10 秒で競合 process を観測するだけで、CCBench を起動しない → 非 CCBench の process site
  (`_EXPLICIT_NON_CCBENCH_PROCESS_SITES` と materializer 側の `explicit_non_materializer_process_sites`)。
- `run_job.once.capture`: `calibrator.runner.run_once` の `subprocess_runner` seam へ渡す中継で、同じ process の stdout を TPC-C の取引別件数のために保持するだけ。
  起動 argv は gateway (`run_once`) が組む。分類は inventory の既存の区分のうち実態に合うものを選び、その理由を comment に書く
  (gateway の client として扱う区分があればそれ、無ければ既存の同型の登録例に合わせる)。
- `run_job` 内の `run_once` の直接呼び出し (`run_job.once`) が `_BOUNDED_RUN_ONCE_CLIENTS` に要るなら同時に登録する。
- 既存の他の entry・検査の論理は一切変えない。新 module のコードは変えない (必要が判明したら報告して止まる)。
