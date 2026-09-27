## 変更 file と要点 (file:line)

- [test_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/tests/test_campaign.py:5439): 方策 driver の登録件数と raw-AST 期待値を 1→2 に更新し、各合計も追随させました。
- [test_p3_exploration_namespace.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/tests/test_p3_exploration_namespace.py:463): AST 呼出し件数を 2 に更新しました。実行経路の呼出し回数は 1 のままです。

## 実走 (または未実走)

login 上で test 関数を直接実行し、次の両 nodeid が通過しました。

- `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- `orchestrator/tests/test_p3_exploration_namespace.py::test_driver_ast_supplements_runtime_namespace_gate[p3_s4_loop_policy]`

`check_codex_agents.py`、`check_docs.py`、`git diff --check` も通過しました。

## 総括

登録件数を実物の 2 箇所に合わせました。検査は緩めていません。commit は作成していません。