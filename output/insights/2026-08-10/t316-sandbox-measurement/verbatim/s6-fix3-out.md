実装は完了しましたが、規定テストが pytest 起動前に停止したため、G1〜G6 はすべて「実装済み・未実走」の `partial` とします。commit、docs 編集、PBS 操作は行っていません。

## 総括

| 所見 | 状態 | 対応 |
|---|---|---|
| G1 | partial | sentinel に加え `timed_out is False`、厳密な整数 rc、正常 rc 閉集合 `{0}` を必須化。timeout・signal・非0終了は `inconclusive`。 |
| G2 | partial | カテゴリ別 errno 表を1箇所へ集約。`ECONNREFUSED` は `no-go`、`ETIMEDOUT` は `inconclusive`。DNS・write・credential の集合を分離。`std::system` は shell 不在、command failure、marker 副作用を区別。 |
| G3 | partial | host PID 不明時、一意 token と起動前 PID 集合で所有を限定した fallback 清掃を追加。清掃不能・残存検出時は S7 を `inconclusive`。 |
| G4 | partial | final receipt に `state: complete` と機械可読 completion predicate を追加。`COMPLETED` も temp→fsync→hard-link publish→dir fsync。完成前に `PARTIAL.json` を削除。 |
| G5 | partial | command/escape runner seam で実 observer を通すテストを追加。指定6変異を検出する独立 literal・正負テストを追加。 |
| G6 | partial | `discharged_by_this_probe` を実 stage verdict から導出。S1〜S5またはS7が非 `go` なら対応項目を discharge しない。 |

集計: `closed=0 / partial=6 / regressed=0`。未実走のため closed は主張しません。

編集ファイル:

- [t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py)
- [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py)

`test_hooks.py`、policy JSON、PBS の既存 dirty 差分は前巡からの継承物で、今回は編集していません。docs 差分はありません。

検査結果:

- `python3 tools/run_tests.py orchestrator/tests/test_t316_sandbox_probe.py -q`
  - nodeid: 0件
  - pytest collection 前に停止
  - `run_tests.py rc=16`
  - 出力:

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

したがって対象テストは「実装済み・未実走」で、pass は主張しません。

- production verdict 補助 smoke: `rc=0`
  - 正例: S1〜S7 `7/7 go`
  - 負例: S3 `11/11 no-go`
  - 負例: S5 runtime/build `8/8 no-go`
- receipt publish runtime smoke: `rc=0`
- Python AST/import、JSON parse、`bash -n`、`git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: `違反なし`

正例・負例の両立は、全正常観測が `aggregate_verdicts()` の `go` に到達する一方、S3各カテゴリおよびS5各profile/categoryの単独破壊が当該stageとoverallを `no-go` にすることで補助確認しました。これは pytest 実走の代替ではありません。

F1〜F15 / R1・R2 の静的回帰監査では回帰を認めませんでした。R1のhard-link create-only publishとpreflightは維持され、`COMPLETED` にも適用しています。R2の正例経路は要求を外さず `7/7 go`、負例は引き続き非 `go` です。

残る既知の限界は、規定pytest、C++ fixture compile、計算ノード実測が未実施であることです。また、子孫が一意 token をargvから消去してPID identityも解決不能な場合は清掃完了を証明できず、意図どおりS7を `inconclusive` にします。final receiptだけ存在して`COMPLETED`がないcrash windowは、completion predicateにより未完成として拒否されます。