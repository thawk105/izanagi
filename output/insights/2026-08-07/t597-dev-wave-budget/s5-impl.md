[orchestrator/tests/test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:290) のみに3件追加しました。production・docs は変更せず、commit もしていません。

追加 nodeid:

- `orchestrator/tests/test_mutation_harness.py::test_missing_rf_is_rejected_before_runner_or_ledger`
- `orchestrator/tests/test_mutation_harness.py::test_mutation_nonzero_normal_rc_without_failed_nodes_is_parse_error`
- `orchestrator/tests/test_mutation_harness.py::test_baseline_nonzero_normal_rc_without_failed_nodes_is_parse_error`

実走状況は「実装済み・未実走」です。上記3 nodeidだけを `tools/run_tests.py` で2回試しましたが、いずれもテスト開始前に `qstat -Q preflight rc=1`、終了コード16で停止しました。直接 pytest には迂回しておらず、緑は主張しません。AST 構文確認と `git diff --check` は成功しています。該当テストを制約する meta-test は検索範囲内に見つからず、実走対象はありませんでした。

分岐削除時の検出力:

- `-rf` 必須分岐を削除すると runner 禁止スタブへ到達し、`pytest.raises(HarnessError, match="DW-M08.*-rf")` が壊れます。
- mutation 分岐を削除すると結果が `MISMATCH` になり、`assert status == "PARSE_ERROR"` が壊れます。
- baseline 分岐を削除すると結果が `FAILED` になり、`assert baseline["status"] == "PARSE_ERROR"` が壊れます。`rc == 1` と `failed_nodes == []` は実測 evidence として別途固定しています。

静的な波及可能性:

- `tools/mutation_worktree.py::_harness_argv` などの caller は runner argv を透過するため、`-rf` 欠落時は runner・ledger より前で拒否されます。
- `_observed_status` は mutation 実行と resume ledger 再検証から共有されています。
- baseline の producer `_baseline` と consumer `_validate_baseline_record` は同じ判定条件を持ちます。
- 共有の `repo` fixture、`_argv`、`_paths`、`_single_spec` は利用のみで変更していません。monkeypatch はテスト単位で復元され、他テストへの状態波及は想定していません。

## 総括

追加 nodeid は3件。3件とも対象分岐の単独削除を検出可能と自己判定しています。Pegasus dispatch infrastructure failure のため未実走です。想定波及は argv caller、mutation/resume の共有 status 判定、baseline producer/validator に限定されます。