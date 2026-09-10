## 総括

裁定 v2 を実装しました。許可された 4 ファイルだけを変更し、docs・commit・push は行っていません。

指定 harness では、`test_run_tests_shards.py` の全 189 node が通過しました。

## 実装した内容

- `report.json` に必須 top-level key `session_timeline` を追加。
- `pytest_collection_finish(trylast=True)` で collection 終了時刻を取得。
- worker ごとの最小 `start`、最大 `stop` を安全に集計。
- serial と xdist の collection 時刻、lock interval を既存 worker payload 経路で集約。
- 観測不能値は `null`、空 map、空 list として扱い、観測だけを理由に例外を出さない構成にした。
- `pytest_runtest_protocol` で real-repo lock の正常取得後と正常解放後だけ時刻を記録。
- lock 取得失敗、解放失敗、内側 protocol 例外では interval を記録しない。
- `config` 不在、shard spec 不在、`access is None` は従来の lock 経路へ直行。
- `_reports()` を新 schema に更新し、正例・負例・hook 順序・xdist 集約・欠測を既存 test file へ追加。
- `SCHEMA` は v1 のまま。
- AST 比較により、以下の本体が HEAD から不変であることを確認。
  - `validate_report_evidence`
  - `merge_reports`
  - `pytest_collection_modifyitems`

## 現行の受理・拒否挙動と、変えた点

変更前は、既存 14 key と完全一致し、既存 evidence 検査と 6 gate を満たす report を受理していました。`session_timeline` を持つ report は未知 key として拒否されていました。

変更後は次の挙動です。

- `session_timeline` を含む 15 key の完全一致を要求。
- `session_timeline` 欠落は `report-invalid`。
- timeline の型不正、NaN、key 欨落、空 dict などは、既存 field と 6 gate が正常なら `(0, "ok")`。
- timeline の内容を `validate_report_evidence`、scheduler、rc、receipt の判定に使用しない。
- report の key 形は変わりますが、同一走行内の producer と consumer が同期しているため、受理される走行集合は変更していません。

## 実走した nodeid と結果

実走コマンド:

```text
PYTHONPATH=. python3 orchestrator/tests/test_run_tests_shards.py
```

実走範囲は `orchestrator/tests/test_run_tests_shards.py` の collection 全 189 nodeです。先頭は
`orchestrator/tests/test_run_tests_shards.py::test_acceptance_shards_imports_in_isolated_mode_without_user_site`、
末尾は
`orchestrator/tests/test_run_tests_shards.py::test_junit_merge_recomputes_counts_and_has_malformed_control`
です。

結果:

```text
189 passed in 15.40s
```

collect-only も指定コマンドで実行し、189 node、rc 0 を確認しました。

## 受入台帳へ足した node id

以下の実 collection node 16 件を `0.0` で登録し、`nodeid_count` を `19541` から `19557` へ更新しました。

- `orchestrator/tests/test_run_tests_shards.py::test_acceptance_shard_hooks_keep_pytest_hookimpl_attributes[pytest_collection_finish-trylast]`
- `orchestrator/tests/test_run_tests_shards.py::test_collection_finish_clock_runs_after_synthetic_modifyitems_wrapper`
- `orchestrator/tests/test_run_tests_shards.py::test_controller_state_serial_uses_config_local_timeline`
- `orchestrator/tests/test_run_tests_shards.py::test_controller_state_xdist_uses_latest_collection_and_worker_lock_map`
- `orchestrator/tests/test_run_tests_shards.py::test_lock_interval_recorder_is_noop_without_shard_state`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_logreport_ignores_zero_nonfinite_missing_and_huge_bounds`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_logreport_tracks_reordered_bounds_per_worker_and_serial`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_access_none_reads_no_clock_and_records_nothing`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_configless_item_keeps_existing_lock_contract`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_lock_acquire_and_release_failures_record_nothing`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_preserves_inner_exception_without_recording`
- `orchestrator/tests/test_run_tests_shards.py::test_runtest_protocol_records_only_after_lock_release`
- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_contents_do_not_change_merge_verdict`
- `orchestrator/tests/test_run_tests_shards.py::test_session_timeline_is_required_and_valid_fixture_merges`
- `orchestrator/tests/test_run_tests_shards.py::test_sessionfinish_writes_serial_session_timeline`
- `orchestrator/tests/test_run_tests_shards.py::test_worker_payload_carries_observations_and_defaults_without_state`

台帳の `nodeid_count` と実 map 長はともに 19557、対象 test file の未登録 collection node は 0 件です。90% 閾値は変更していません。

## 所有外への波及可能性 (静的列挙)

- [tools/run_tests.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/run_tests.py): acceptance plugin の起動 caller。
- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/test_real_repo_serialization.py:2081): `pytest_runtest_protocol` と `_real_repo_locks` の共有契約 consumer。
- [test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/test_acceptance_schedule_order.py:832): duration ledger と 90% coverage の consumer。
- [tools/update_acceptance_duration_ledger.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/tools/update_acceptance_duration_ledger.py:483): ledger 更新 producer。
- [test_update_acceptance_duration_ledger.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/orchestrator/tests/test_update_acceptance_duration_ledger.py:307): canonical ledger の consumer test。
- `output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py`: 旧 exact-key report を読む歴史的 consumer。現行 tool/test caller からの参照はありません。

## 実装できなかったこと

scope 内の未実装はありません。

受入全走、`test_real_repo_serialization.py` 全体、`test_acceptance_schedule_order.py` 全体は実装済み・未実走です。そのため、それらを緑または certified とは申告しません。