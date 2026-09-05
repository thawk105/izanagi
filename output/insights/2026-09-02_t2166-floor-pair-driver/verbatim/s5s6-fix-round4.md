## 総括

在庫登録を追加しました。変更は literal 台帳への追加のみで、走査述語・判定・指定された禁止対象は変更していません。他に必要だった登録は process-launch 在庫の三件です。

## 変更内容

- [test_official_perf_closure.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_official_perf_closure.py:53)
  - `orchestrator/campaign/floor_pair_driver.py`
- [test_ccbench_spawn_sites.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_ccbench_spawn_sites.py:112)
  - `campaign/floor_pair_driver.py:<module>._git_head`
- [test_ccbench_spawn_sites.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_ccbench_spawn_sites.py:113)
  - `campaign/floor_pair_driver.py:<module>._git_show_head`
- [test_ccbench_spawn_sites.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_ccbench_spawn_sites.py:114)
  - `campaign/floor_pair_driver.py:<module>._run_probe`

後三件は production 全体を走査する [test_ccbench_spawn_sites.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_ccbench_spawn_sites.py:332) と literal 台帳を完全一致させる検査です。二つの read-only Git 問い合わせと固定 pgrep probe であり、non-CCBench 台帳へ登録しました。

## 他の在庫検査

- [test_plain_runner_coverage.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_plain_runner_coverage.py:60): 登録不要。新 test は [test_floor_pair_driver.py:1898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:1898) に pytest harness があり、allowlist 対象ではありません。
- [test_pytest_collection_config.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_pytest_collection_config.py:423): 登録不要。`verifier` または `oracle` 名の test だけが対象です。
- [test_campaign.py:4771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_campaign.py:4771): 登録不要。certified `evaluate` caller ではありません。
- [test_p3_exploration_namespace.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_p3_exploration_namespace.py:502): 登録不要。exploration campaign-root creator の述語を満たしません。
- [test_p3_build_authority_cli.py:1212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_p3_build_authority_cli.py:1212): 登録不要。`--build` を持つ manual materializer ではありません。
- [test_s8b_floor_campaign.py:1624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_s8b_floor_campaign.py:1624): 登録不要。検査対象は直接名による `measure_point(...)` などで、新 driver は qualified call `runner.measure_point(...)` です。
- [test_s8b_floor_stats.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_s8b_floor_stats.py:875)、oracle consumer、B4 analysis、ratified-freeze constructor などの symbol-filtered 在庫も確認しましたが、対象 symbol の呼出しはありません。

したがって、上記 process-launch 三件以外は該当なしです。

## 検証

実装済み・未実走です。次の nodeid を一括実行しようとしましたが、`tools/run_tests.py` が `qstat -Q preflight rc=1`、child 未起動、`rc=16` で終了しました。

- `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`
- `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `test_s8b_floor_campaign.py::test_production_use_perf_keyword_call_sites_are_a_closed_set`
- `test_p3_exploration_namespace.py::test_driver_contract_registry_is_exact`
- `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`

`git diff --check` と変更二ファイルの AST parse は成功しました。runner が一時生成した dispatch ファイルは今回の生成分だけ削除し、`output/` に残していません。