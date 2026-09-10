修正対象は [test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:73) のみです。

- 73–109行: 偽 submission に producer と同形の `request.json` を作成。`environment.PYTHONDONTWRITEBYTECODE` は実際の実行環境から取得します。missing / malformed fixture も追加しました。
- 121–128行: 上記 fixture を timeout 経路へ通す mode を追加。
- 980–988行: matched 時の期待値 `runner-mode-violation` と束縛状態を厳密に維持。
- 1083–1142行: `request.json` が無い場合と壊れている場合を別パラメータで固定し、`runner-mode-evidence-unavailable`、`indeterminate`、詳細エラーまで検査。

親が走らせるべき nodeid は6件です。

- `orchestrator/tests/test_mutation_harness.py::test_hang_risk_uses_short_timeout_records_evidence_and_restores`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_after_dispatch_submission_stops_without_terminal_record`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_ignores_conclusively_unrelated_submission`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_inventory_failure_stops_without_terminal_record`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[missing]`
- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[malformed]`

assertion は緩めていません。matched 経路は引き続き `runner-mode-violation` を必須とし、判定不能は独立した破損 fixture だけで検証します。

pytest は実走していません。実施した確認は AST 構文解析と `git diff --check` のみで、いずれも成功しました。docs 編集・commit も行っていません。

## 総括
変更内容: producer 忠実な request fixture と missing / malformed 回帰テストを追加。  
親が走らせるべき nodeid 数: 6件。  
残るリスク: pytest 未実走のため、実行時挙動は親の焦点走で確認が必要。