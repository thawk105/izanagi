## 総括

指定の F1、F2、F7、F9、F11、F12 を所有 path 内で修正しました。各 F にテストを追加しました。commit は作成していません。

## 変更 file と行数

| file | 追加 / 削除 |
|---|---:|
| [silo_policy_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/campaign/silo_policy_contrast.py) | 59 / 0 |
| [silo_policy_contrast_generators.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/campaign/silo_policy_contrast_generators.py) | 4 / 5 |
| [silo_policy_contrast_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/tools/pegasus/silo_policy_contrast_launch.py) | 32 / 15 |
| [test_silo_policy_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/tests/test_silo_policy_contrast.py) | 57 / 2 |
| [test_silo_policy_contrast_generators.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/tests/test_silo_policy_contrast_generators.py) | 20 / 0 |
| [test_silo_policy_contrast_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/tests/test_silo_policy_contrast_launch.py) | 43 / 0 |

## 実装した interface

- 台帳に `close_series_if_done(ledger) -> str | None`、`open_opportunity(ledger) -> int | None`、`next_opportunity(ledger) -> int` を追加しました。
- launcher の `submit`・`status` は終了判定を呼びます。実投入時の `endpoint-fixed` は `logical_slot`・`variant`・`source_digest`・`fitness_tps` を直下に記録し、dry-run の score 表示では記録しません。
- `generate` は台帳の機会番号を使い、却下時の `opportunity-end` に `reject_subtype`・`reject_rule_id` を記録します。grow 法は比較を一つの演算子として選んだ後に operand 型を選びます。

## テスト

追加した nodeid は `test_close_series_after_score_and_reference_once`（F2）、`test_stock_unestablished_closes_after_job1`（F7）、`test_open_and_next_opportunity_after_outage`（F9）、`test_submit_score_fixes_flat_endpoint_only_on_submit`（F1）、`test_generate_reject_preserves_preview_subtype`（F11）、`test_bool_grow_selects_operator_before_compare_operand`（F12）です。

対象の 3 テスト file は `tools/run_tests.py` で起動を試みましたが、すべて `qstat -Q` preflight の rc=16 で停止し、**テスト本体は未実走**です。6 file の構文解析と `git diff --check` は通過しました。

## 所有外への波及

driver、round、parent、report とその consumer test は未編集です。指定された inventory 系テストを静的検索し、対象 file 名への参照は見つかりませんでした。所有外の結合テストは未実走です。

## 変異の位置

| 変異 | 壊す位置 | 検出する nodeid |
|---|---|---|
| M7 | `silo_policy_contrast_generators.py:49` | `test_zero_mixture_and_retry` |
| M8 | `silo_policy_contrast_generators.py:228` | `test_evolution_tie_parent_and_field_extension` |
| M9 | `silo_policy_contrast.py:105` | `test_a_b_outage_and_retry` |
| M10 | `silo_policy_contrast.py:102` | `test_a_b_outage_and_retry` |
| M11 | `silo_policy_contrast.py:103` | `test_a_b_outage_and_retry` |

## 未解決・報告して止めたこと

`qstat -Q` の dispatch preflight 障害により、追加テストと所有外 consumer との結合結果は確認できていません。