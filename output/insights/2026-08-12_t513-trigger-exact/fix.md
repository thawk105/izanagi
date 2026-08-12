## 総括

テスト追加は完了しましたが、**実装済み・未実走**です。Pegasus の dispatch 前検査が `qstat -Q rc=1`、runner rc=16 で停止し、nodeid 本体には到達していません。

[test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5441) に以下の4 nodeidを追加しました。

- `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_leading_vertical_tab`
- `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_leading_form_feed`
- `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_leading_non_breaking_space`
- `orchestrator/tests/test_campaign.py::test_trigger_binding_rejects_materialized_predicate_with_leading_ideographic_space`

それぞれ `\v`、`\f`、`\u00a0`、`\u3000` を hole 先頭に置き、既存 helper で拒否を検査します。parametrization は追加していません。

- 既存テストの変更: なし
- production・docs・8c所有ファイルの変更: なし
- commit・index操作: なし
- `git diff --check`: rc=0
- AST解析・node名一意性: 確認済み
- meta-test: 静的確認済み、実走は同じdispatch障害により未実施
- 機能波及: 0件
- 静的波及確認対象: 4件（既存共有helper 2件、plain-runner/real-repo収集面 2件）。いずれも変更・登録追加不要です。