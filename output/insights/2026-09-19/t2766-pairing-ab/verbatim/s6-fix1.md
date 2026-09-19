## 所見対応表

nodeid の共通 prefix は `orchestrator/tests/test_acceptance_schedule_order.py::` です。

| 赤の nodeid（末尾） | 状態 | 根拠（変更行） |
|---|---|---|
| `test_g12_holds_shard_selection_and_real_repo_suffix_survive[A]` | partial | 1969 行で config に file path の `args` を追加。実走未確認。 |
| `test_g12_holds_shard_selection_and_real_repo_suffix_survive[B]` | partial | 同上。実走未確認。 |
| `test_g12_pairing_queue_and_all_item_witness` | partial | 1807〜1819 行で B arm 限定の config factory に変更。インスタンスに `workerinput`・`args` を設定し、class 属性の変更を除去。実走未確認。 |

## 総括

**実装済み・未実走**です。変更は [test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/orchestrator/tests/test_acceptance_schedule_order.py:1802) の上記 2 関数（G12）のみです。production、共有 harness、既存の期待値・assert は変更していません。

指定コマンドを実行しましたが、`qstat -Q preflight rc=1` により runner が **rc=16、child_started=false** で終了しました。

実走 nodeid はありません。**passed 0 / failed 0（テスト未起動）**であり、赤 3 件を含む指定ファイル全体の再検証が未完了です。