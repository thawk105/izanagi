追加した node id は次の 2 件です。

```text
test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static
test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore
```

両方を次の 3 集合へ追加しました（計 6 行）。

- `conftest.py`: `_REAL_REPO_NODE_INVENTORY`
- `conftest.py`: `_REAL_REPO_BOTH_READER_NODES`
- `test_real_repo_serialization.py`: `_REAL_REPO_CLASSIFIED_NODES_GOLDEN`

access は **parent/read・ccbench/read** です。`benchmark_snapshots` → `_build_snapshot_base` → `_init_submodules_from_local_source` を追跡し、親 repo の履歴・Git objects と共有 submodule を読むことを確認しました。既存の `test_parent_numstat_controls_remain_pinned` などと同じ区分です。AST 静的照合では、同 fixture の直接 consumer 全 23 関数がこの区分に登録済みでした。

実行結果：

| command | 結果 |
|---|---|
| `PYTHONPATH=. python3 orchestrator/tests/test_real_repo_serialization.py` | rc=1、`GrowthTestHoldBypassRefused` により実走前に拒否 |
| `PYTHONPATH=. python3 orchestrator/tests/test_acceptance_schedule_order.py` | rc=0、79 passed・1 warning |
| `python3 - <<'PY' … PY` による AST 静的照合 | rc=0、inventory/golden 一致・新設 node の分類と consumer 網羅を確認 |
| `git diff --check` | rc=0 |

hold は解除していません。AST 照合を代替に用いましたが、拒否された検査の実走成功とは扱いません。

所有外への波及を `orchestrator/`・`tools/` の Python ファイルで静的確認しました。

- `test_acceptance_schedule_order.py`、`test_run_tests_shards.py`、`test_dev_waves_isolation_contract.py` は正本から導出するため、追加登録は不要です。
- `patchharness.py` は分類済み access を参照します。
- `growth_test_holds.py` と `test_hold_inventory.py` は個別 hold の登録・golden であり、新設 2 件を要求する集合ではありません。
- 確認範囲に、ほかの追加必須登録簿はありません。

## 総括

指定 2 ファイルの登録漏れを修正しました。既存 node・検査ロジックは変更していません。
`test_codex_reasoning_ab.py` と `tools/codex_reasoning_ab.py` は **1 byte も変更していません**（作業前後の SHA-256 一致）。
docs 編集・`git add`・commit は行っていません。
acceptance harness は成功。対象 serialization 検査は hold のため **実装済み・未実走**です。