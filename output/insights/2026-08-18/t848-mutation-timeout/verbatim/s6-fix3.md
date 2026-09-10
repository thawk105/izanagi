回帰原因を除去しました。変更はテスト fixture の 1 行だけです。

### 根本原因

[orchestrator/tests/test_mutation_harness.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:86) は、三重引用文字列の内側で生成する `tests/test_gate.py` に malformed JSON を書かせています。

2 巡目では `"{\n"` と一段しか escape されておらず、生成先では文字列途中に実改行が入り SyntaxError になりました。function-scoped `repo` fixture を使う全 harness テストで collection が `rc=2, collected=0` になったため、既存テストを含む 26 件が一斉に回帰しました。

`.git/info/exclude` は各テスト固有の一時 repo にだけ `/output/` を設定しています。fixture は function scope なので別テストへ伝播せず、根本原因ではありません。

### 変更

[orchestrator/tests/test_mutation_harness.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:86) を `"{\\n"` に修正しました。これにより、生成される Python は構文的に正しく、実行時には意図どおり不正 JSON の `"{\n"` を書きます。

同 fixture の producer 模倣は lines 93–109 で実 producer と同じ `schema_version/repo_root/task/args/environment` を持ち、走行 token も `PYTHONDONTWRITEBYTECODE` 経由で一致します。したがって matched 経路は `runner-mode-violation`、missing/malformed と inventory 失敗は引き続き `runner-mode-evidence-unavailable` です。

### 親が走らせるべき nodeid

```text
orchestrator/tests/test_mutation_harness.py::test_hang_risk_uses_short_timeout_records_evidence_and_restores
orchestrator/tests/test_mutation_harness.py::test_local_timeout_after_dispatch_submission_stops_without_terminal_record
orchestrator/tests/test_mutation_harness.py::test_local_timeout_ignores_conclusively_unrelated_submission
orchestrator/tests/test_mutation_harness.py::test_local_timeout_inventory_failure_stops_without_terminal_record
orchestrator/tests/test_mutation_harness.py::test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[missing]
orchestrator/tests/test_mutation_harness.py::test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[malformed]
orchestrator/tests/test_mutation_harness.py::test_preexisting_dispatch_hold_blocks_local_runner_start
orchestrator/tests/test_mutation_harness.py::test_dispatch_timeout_latches_hold_preserves_bytes_stops_next_and_writes_stop
orchestrator/tests/test_mutation_harness.py::test_dispatch_non_timeout_parse_error_is_not_an_orphan_condition
orchestrator/tests/test_mutation_harness.py::test_preexisting_hold_blocks_collection_and_baseline_runner_start[collection]
orchestrator/tests/test_mutation_harness.py::test_preexisting_hold_blocks_collection_and_baseline_runner_start[baseline]
orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[False-local]
orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[False-dispatch]
orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[True-local]
orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[True-dispatch]
orchestrator/tests/test_mutation_harness.py::test_timeout_request_recovery_uses_partial_receipt_as_correspondence_source
```

193 件の回帰閉包確認には、親の既存 six-file focus 走もそのまま再実行してください。

pytest は実走していません。生成される `test_gate.py` の AST 構文確認、`git diff --check`、結合文字不在検査は成功しました。docs・commit・禁止ファイルは変更していません。

## 総括
回帰の根本原因: 共有生成 fixture の二重文字列 escape 不足による全 test repo の SyntaxError。  
直した内容: line 86 を二重 escape にし、producer 忠実な request と判定不能テストを維持。  
未解決: 既知の実装課題なし。ただし pytest 未実走のため、緑確認は親の焦点走待ち。