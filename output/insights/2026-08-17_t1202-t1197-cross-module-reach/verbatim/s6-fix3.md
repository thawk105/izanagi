fixture の no-op を修正しました。production コード・docs・期待値は変更せず、commit も作成していません。

### 修正内容

- `multiple-assignment`
  - 修正前: 一致しない複合文字列の置換で、代入は 1 回のまま。
  - 修正後: `drive = trigger.drive_iteration` 自体を 2 行へ置換し、関数内の代入が 2 回。
  - 変更箇所: [test_s8c_preregistration_predicates.py:865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:865)
  - 変異適用 assert: [test_s8c_preregistration_predicates.py:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:936)
  - 代入数 2 の assert: [test_s8c_preregistration_predicates.py:938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:938)

### no-op 全件検査

- `.replace()` call site: 60
- 静的評価可能: 49、置換対象非一意 0、修正後 no-op 0
- 動的 parameter 展開を含む負例 param: 70
- 修正前 no-op: 1 (`multiple-assignment`)
- 修正後 no-op: 0
- 70 件すべての exact status/reason assert を一時 repo 上の直接診断で確認済み。
- `multiple-assignment`: `UNSATISFIED / environment-contract-consumer-absent`

`dev-wave` の `DW-M04` に従い、置換実在と一意性も確認しています。

### 実 tree 12 条件

| 条件 | status / reason |
|---|---|
| C01 | `UNSATISFIED / workload-projection-mismatch` |
| C02 | `EVIDENCE_UNDEFINED / arm-binding-declared-only` |
| C03 | `EVIDENCE_UNDEFINED / manifest-registry-proof-undefined` |
| C04 | `UNSATISFIED / crash-policy-cell-partial` |
| C05 | `EVIDENCE_UNDEFINED / schedule-schema-absent` |
| C06 | `EVIDENCE_UNDEFINED / budget-consumer-contract-undefined` |
| C07 | `EVIDENCE_UNDEFINED / floor-judge-contract-undefined` |
| C08 | `EVIDENCE_UNDEFINED / prereg-binding-proof-undefined` |
| C09 | `UNSATISFIED / formal-acceptance-layer3-consumer-absent` |
| C10 | `UNSATISFIED / cross-binding-verifier-incomplete` |
| C11 | `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` |
| C12 | `UNSATISFIED / allocation-enforcement-consumer-absent` |

`reachability-limit-exceeded` は 0 件です。`git diff --check`、`check_codex_agents.py`、`check_docs.py` も成功しました。

公式 runner は単一 nodeid と対象ファイル全体の両方で、pytest 開始前に `qstat -Q preflight rc=1`、child `rc=16` となりました。このため pytest 全緑とは報告しません。

## 総括

- 直した件数: 1 param (`multiple-assignment`)
- no-op 全件検査の結果: 70 param 中、修正前 1 件、修正後 0 件
- 実走した nodeid: なし。直接診断では 70 件の exact assert が全通過
- 未実走のもの: `test_callable_value_flow_failures_stay_environment_absent[multiple-assignment]` および対象テストファイル全 nodeid。Pegasus dispatch infrastructure failure のため pytest 未開始