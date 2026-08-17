修正を行わず停止しました。焦点テストの fixture に裁定前提との不整合があります。

`multiple-assignment` の `replace` は元文字列に一致しておらず、生成された source は正例 `VALUE_FLOW_C12` と完全同一です。

- source equality: `True`
- `drive = trigger.drive_iteration` の出現回数: `1`
- 該当箇所: [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:870)

一方、実際に代入を 2 回含む source を直接構成した診断では、現実装が既に期待どおり拒否しました。

```text
assignment_count: 2
status: UNSATISFIED
reason: environment-contract-consumer-absent
```

現実装にも `len(rows) != 1` の厳格化があります: [s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1077)。

この状態で実装だけを変更して焦点テストを緑にするには、同一 source を commit 名などで区別する不正な特例が必要になり、受理集合と F2 契約を壊します。テスト編集は禁止されているため、段 6 の停止規律に従いました。

焦点 nodeid は `tools/run_tests.py` で起動を試みましたが、dispatch 前に `rc=16` となり未実走です。

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_callable_value_flow_failures_stay_environment_absent[multiple-assignment]
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

## 総括

- 変更した箇所: なし。第 1 巡差分を一切変更していません。
- 厳格化の内容: 現実装は実際の 2 回代入を既に `UNSATISFIED / environment-contract-consumer-absent` へ倒します。
- 実 tree 12 条件の再確認結果: 停止条件成立後の再実走はしていません。第 1 巡報告と現行 golden は指定された 12 条件に一致し、`reachability-limit-exceeded` は 0 件です。
- 第 1 巡の他性質を壊していない根拠: 今回の変更は 0 件であり、F1〜F11、F2 の支配関係、production chain を含む第 1 巡差分はそのままです。