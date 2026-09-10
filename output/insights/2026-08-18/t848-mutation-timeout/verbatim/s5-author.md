実装済み・未実走です。dev-wave 段 5 契約どおり、コードと既存テストだけを変更し、docs 編集と commit は行っていません。

### 変更内容

- [tools/mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:132)
  - `OrphanHoldStop` に停止理由コードを追加。
  - local timeout と新規 dispatch submission の組合せを検出し、`runner-mode-violation` として既存 orphan-stop 経路へ送るよう変更。
  - `_run_tests` は runner mode、attempt recorder の有無にかかわらず開始前 inventory を取得。
  - timeout 後の差分を `new_dispatch_submission` として result に保存。
  - local timeout では receipt recovery を呼ばない。
  - sidecar とエラー表示へ理由コードを反映。
  - `LEDGER_SCHEMA`、status 集合、summary、record shape は未変更。

- [orchestrator/tests/test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:64)
  - 実 subprocess が submission directory を作ってから hang する fixture mode を追加。
  - local timeout、新規 submission ありで rc=2、terminal 0 件、`runner-mode-violation` sidecar、変異保全を固定。
  - local timeout、新規 submission なしの既存 `TIMEOUT` 期待を維持し、sidecar 不在を追加確認。
  - dispatch timeout の既存テストへ terminal 0 件の D454 pin を追加。
  - before snapshot が runner mode と attempt recorder に依存しないことを4組合せで固定。

### 受理・拒否挙動の差

- 従来: local timeout は実際に dispatch されていても terminal `TIMEOUT`。
- 変更後: local timeout かつ新規 submission ありだけ、terminal record を書かず rc=2 で停止。
- local timeout かつ新規 submission なしは従来どおり terminal `TIMEOUT`。
- local の非 timeout は、実際に dispatch されていても従来どおり結果を受理。
- dispatch timeout は従来どおり orphan-stop、rc=2、terminal 0 件。
- D289 の `TIMEOUT` 拒否、v4 schema、status、summary、fan-out の受理集合は未変更。

### 親が実走すべき nodeid

- `orchestrator/tests/test_mutation_harness.py::test_local_timeout_after_dispatch_submission_stops_without_terminal_record`
- `orchestrator/tests/test_mutation_harness.py::test_hang_risk_uses_short_timeout_records_evidence_and_restores`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_timeout_latches_hold_preserves_bytes_stops_next_and_writes_stop`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode`
- `orchestrator/tests/test_mutation_harness.py::test_timeout_request_recovery_uses_partial_receipt_as_correspondence_source`
- `orchestrator/tests/test_mutation_worktree.py::test_real_harness_local_e2e_uses_disposable_tree_between_observation_points`
- `orchestrator/tests/test_mutation_worktree.py::test_orphan_stop_sidecar_preserves_container_and_receipt_without_hold`
- `orchestrator/tests/test_mutation_fanout_contract.py::test_merge_rejects_receipt_body_mismatch_and_orphan_evidence`

pytest は一切起動していません。静的には Python AST 解析と `git diff --check` が成功しています。意図的に赤へ残したテストはありませんが、全テスト結果は未確認です。

### 波及可能性

- `_collect_expected_nodes`、`_baseline`、`_apply_mutation` は共通の停止判定を通るため、collection、baseline、mutation の全段へ適用されます。
- `AttemptRecorder` の exact schema と `_recover_dispatch_request` の exact dict は変更していません。
- shared repo fixture は新しい専用 mode だけを追加し、既存 mode の意味は維持しています。
- `mutation_worktree` は local の child rc=2 により teardown せず container を保全します。ただし理由分類の `orphan_hold` 判定は dispatch mode 限定なので、wrapper receipt 上は新理由を `orphan-hold` と分類しません。編集禁止面のため未変更です。
- fan-out は rc=2を引き続き terminal shard として拒否します。
- 新規 test file は作っていないため test file 集合の meta-test への追加は不要です。禁止された `test_check_docs.py` は読んでいません。

## 総括
- 変更した file: `tools/mutation_harness.py`、`orchestrator/tests/test_mutation_harness.py`
- 親が走らせるべき nodeid: 上記 harness 5件と consumer 3件
- 残るリスク: pytest 未実走、local wrapper receipt は新停止理由を個別分類しない