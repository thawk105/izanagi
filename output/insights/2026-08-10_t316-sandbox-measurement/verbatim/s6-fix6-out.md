指定の正方向テストを [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:1011) に追加しました。既存の負方向テストは変更していません。

指定検査の出力:

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

dispatch preflight で停止したため、**実装済み・未実走**です。

## 総括

追加した nodeid:

- `orchestrator/tests/test_t316_sandbox_probe.py::test_containment_discharge_when_all_containment_stages_go`
- `orchestrator/tests/test_t316_sandbox_probe.py::test_performance_discharge_when_s7_go`

M7 では S7 が `go` でも perf 項目の append が行われなくなるため、後者の独立 literal による包含 assertion が必ず失敗します。production を実際に変異させてはいません。

検査結果は pytest 未開始のため **0 passed / 0 failed**。production および `docs/` の差分がないことを確認済みで、production は 1 byte も変更していません。commit も作成していません。