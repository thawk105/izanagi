[test_hooks.py:2624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:2624) に `root.mkdir()` を追加しました。helper・production・assertion・fallback 集合由来の 5 綴り生成は変更していません。

テスト nodeid:
`orchestrator/tests/test_hooks.py::test_bash_main_internal_error_conservatively_rejects_non_pegasus_admission_mentions`

`tools/run_tests.py` で実行を試みましたが、Pegasus の `qstat -Q` preflight が失敗し rc=16 で停止しました。実装済み・未実走です。`git diff --check` は成功しました。

静的な波及可能性:

- 各綴り用の一意な `mention-{index}` 一時ディレクトリのみ追加生成します。
- `_prepare_guard_fixture()` のシグネチャ・挙動と他の呼び出し元には影響しません。
- production 挙動には影響せず、テストが exact rc=2 の検査まで到達するようになるだけです。

## 総括

指定された赤の原因を呼び出し側の 1 行で修正しました。  
期待値変更・assertion 弱体化・所有外編集・commit/stage は行っていません。