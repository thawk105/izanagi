実装完了です。docs、commit、指定外ファイルには触れていません。

### 変更箇所

- [tools/mutation_harness.py:1574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1574)
  - `matched` を nonce 一致だけで判定。
  - nonce 不一致を常に `unrelated` と判定。
  - repo、task、argv の一致結果を `corroboration` に記録。
  - 読取不能、JSON/schema 破損のみを `errors` として `indeterminate` に残した。
- [tools/mutation_harness.py:1840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1840)
  - inventory/request 調査不能時にも空の `corroboration` を記録。
- [orchestrator/tests/test_mutation_harness.py:989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:989)
  - argv 不一致でも nonce 一致により `matched` となり、corroboration が sidecar に残ることを厳密 assertion で固定。

### 親が走らせる nodeid

1. `orchestrator/tests/test_mutation_harness.py::test_hang_risk_uses_short_timeout_records_evidence_and_restores`
2. `orchestrator/tests/test_mutation_harness.py::test_local_timeout_after_dispatch_submission_stops_without_terminal_record`
3. `orchestrator/tests/test_mutation_harness.py::test_local_timeout_ignores_conclusively_unrelated_submission`
4. `orchestrator/tests/test_mutation_harness.py::test_local_timeout_inventory_failure_stops_without_terminal_record`
5. `orchestrator/tests/test_mutation_harness.py::test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[missing]`
6. `orchestrator/tests/test_mutation_harness.py::test_local_timeout_with_unreadable_dispatch_request_stops_as_evidence_unavailable[malformed]`
7. `orchestrator/tests/test_mutation_harness.py::test_preexisting_dispatch_hold_blocks_local_runner_start`
8. `orchestrator/tests/test_mutation_harness.py::test_dispatch_timeout_latches_hold_preserves_bytes_stops_next_and_writes_stop`

判定不能経路は引き続き成立します。before/after inventory の取得失敗は直接 `indeterminate` となり、欠落・不正 JSON・schema 不正の `request.json` は nonce を評価せず `errors` に入ります。正しく読めた request だけが nonce により `matched` または `unrelated` に二分されます。

pytest は実走していません。静的確認として Python AST parse、`git diff --check`、結合文字不在を確認しました。

## 総括
- 変更内容: nonce 単独束縛と corroboration 記録を実装。
- 影響する nodeid 数: 8。
- 残るリスク: 親による上記 nodeid の実走確認が未了。