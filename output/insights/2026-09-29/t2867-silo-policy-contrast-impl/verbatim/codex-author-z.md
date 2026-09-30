## 総括

Z 所有の 7 ファイルに、round tool、1 原提案ごとの新規 Claude session を起動する親、台帳からの report と各テストを実装しました。構文確認は通りました。**テストの実走と Y の台帳 API との結合確認は未完了**です。

## 変更 file と行数

| File | 行数 |
|---|---:|
| [silo_policy_contrast_round.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/silo_policy_contrast_round.py) | 189 |
| [silo_policy_contrast_parent.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.py) | 84 |
| [silo_policy_contrast_parent.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.md) | 12 |
| [silo_policy_contrast_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/campaign/silo_policy_contrast_report.py) | 242 |
| [test_silo_policy_contrast_round.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_round.py) | 60 |
| [test_silo_policy_contrast_parent.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_parent.py) | 48 |
| [test_silo_policy_contrast_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/tests/test_silo_policy_contrast_report.py) | 69 |

## 実装した interface

- Round CLI: `prepare --ledger --a --out [--critic-output]`、`check --ledger --a --coder --out`、`finalize --ledger --a --coder --auditor --out`。`opportunity-start`、`critic-result`、`opportunity-end` を追記します。driver は `--contrast-ledger` 付き CLI だけで呼びます。
- 親: `run_opportunity(ledger_root, a, out, *, settings, model, checkout, spawn, sleep)`。`spawn` を Claude 起動のテスト seam にしました。
- Report: `build_report(roots, *, n=None)`。台帳数から 10 または 12 を判定し、族 A・B ごとに Holm 補正します。探索点を持つ系列数と certified endpoint 数を別 key に出します。

## テスト

6 nodeid のファイルは `py_compile` 成功。`python3 tools/run_tests.py` による実走は **未実施扱い**です。Pegasus の `qstat -Q` preflight が失敗し、child は起動されませんでした（rc=16）。対象は `test_prepare_preserves_driver_stdout_and_critic_shape`、`test_preview_reject_records_without_auditor`、`test_fresh_sessions_and_429_retry_same_a`、`test_three_failures_end_series_without_consuming_a`、`test_seed_only_does_not_count_as_generation`、`test_holm_is_adjusted_within_each_two_comparison_family` です。

## 所有外への波及

driver CLI と Y の `ContrastLedger`・`LEDGER_SCHEMA` を消費します。指定された既存 meta test 6 ファイルに新名称の直接参照は見つかりませんでした。所有外ファイルは編集していません。

## 変異の位置

- M12: [report.py:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/campaign/silo_policy_contrast_report.py:115) — `test_seed_only_does_not_count_as_generation`
- M13: [report.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/orchestrator/campaign/silo_policy_contrast_report.py:191) — `test_holm_is_adjusted_within_each_two_comparison_family`
- M14: [parent.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/tools/pegasus/silo_policy_contrast_parent.py:42) — `test_fresh_sessions_and_429_retry_same_a`

## 未解決・報告して止めたこと

Y の `orchestrator/campaign/silo_policy_contrast.py` はこの tree で未着地です。上記 3 テストファイルはその import に依存するため、着地後の結合テストが必要です。