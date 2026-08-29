## 総括

赤 27 件は全て、受領証つき COMMIT より前に置かれた lock が JSON でなかった同一原因です。  
対象 fixture を decode 可能な JSON lock に修正し、同型の S8B 潜在不具合も閉じました。  
production、docs、期待値、既存 8 node は変更していません。commit も作成していません。  
pytest は dispatch 基盤障害で child が起動せず、未実走です。

## 赤 27 件の原因内訳

全件が単一根本原因です。別原因は確認されませんでした。

- S1 共通 fixture、16 件:
  `test_missing_develop_s2_certification_is_structured_indeterminate`、
  `test_over_budget_refusal_is_symmetric_for_unfinished_comparisons`、
  `test_unframed_wal_tail_fails_but_keeps_completed_prefix_evidence`、
  `test_complete_samples_over_budget_invalidates_all_comparisons`、
  `test_gate1_failure_sets_p_star_one_and_not_established`、
  `test_preflight_refusal_always_has_global_schedule_failure`、
  `test_receipt_exists_but_report_freeze_gate_stays_legacy_strict`、
  `test_non_e1_campaign_is_structured_and_wal_is_not_read`、
  `test_line_issue_and_unframed_tail_are_both_reported_with_prefix_kept`、
  `test_floor_cell_with_seven_sessions_makes_comparison_indeterminate`、
  `test_schedule_order_mutation_invalidates_campaign_comparisons`、
  `test_complete_separation_passes_gates_with_one_over_4900`、
  `test_bench_value_without_commit_is_rejected_as_sample`、
  `test_budget_public_validation_failure_invalidates_all_comparisons`、
  `test_persisted_certification_invalidates_sample[s1]`、
  `test_lock_replacement_during_wal_read_invalidates_persisted_samples`。

- backoff 共通 fixture、8 件:
  `test_plot_backoff_rejects_blank_line_between_records`、
  `test_plot_backoff_rejects_unframed_tail_without_returning_partial_data[complete-json]`、
  `test_plot_backoff_rejects_unframed_tail_without_returning_partial_data[multibyte-partial]`、
  `test_backoff_repro_requires_persisted_certification[backoff-repro]`、
  `test_plot_backoff_loads_nan_ipc_as_missing`、
  `test_plot_backoff_excludes_and_reports_uncertified_bench_done`、
  `test_backoff_repro_bench_tps_requires_commit`、
  `test_plot_backoff_rejects_duplicate_tps_before_it_reaches_plot_data`。

- 個別 fixture、3 件:
  `test_reference_records_requires_persisted_certification[backoff-requested-us]`、
  `test_replay_outcome_requires_persisted_certification[s6]`、
  `test_replay_outcome_requires_persisted_certification[s8a]`。

## 所見ごとの closed / partial / regressed 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| S1 16 件の invalid lock | closed | 共通 `_fixture()` と単独 `_write_session()` が COMMIT 前に有効 JSON lock を配置 |
| backoff 8 件の invalid lock | closed | `_fixture_layout()` が COMMIT 前に有効 JSON lock を配置 |
| S6、S8A、requested-us の3件 | closed | 各 node が受領証つき COMMIT 前に有効 JSON lock を配置 |
| S8B の同型潜在不具合 | closed | `_campaign_start()` の plain text lock を有効 JSON に修正 |
| production の受理条件 | closed | 本 fix の編集は test file 6 件のみ |
| pytest による動的確認 | partial | runner rc=16、`child_started=false` で node 未実行 |
| 回帰または期待値緩和 | regressed なし | skip、xfail、期待値変更、node 削除・改名なし |

## 実装した修正 (file:line)

- [test_s1_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s1_report.py:101): 単独 session 用 lock。
- [test_s1_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s1_report.py:162): role 別共通 fixture lock。
- [test_s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s6_sort_sweep.py:580): S6 replay lock。
- [test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8a_trigger_sweep.py:776): S8A replay lock。
- [test_backoff_consumers.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_backoff_consumers.py:69): backoff 共通 lock。
- [test_backoff_requested_us.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_backoff_requested_us.py:51): requested-us lock。
- [test_s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_s8b_oracle_report.py:528): S8B 共通 lock。

全 lock 形を `decode_campaign_lock()` に通す smoke 検査、対象 6 file の `py_compile`、`git diff --check` は成功しました。

## production を変えていないことの確認

本 fix の編集先は上記 test file 6 件だけです。作業開始時から存在した単位 2 の production 未 commit 差分は触れていません。禁止された production、docs、receipt helper、期待値、8 新規 nodeにも変更はありません。

## 実走した pytest の nodeid と結果

次の5 file、親実走時の全137 nodeを runner 経由で起動しました。

```text
python3 tools/run_tests.py -q \
  orchestrator/tests/test_s1_report.py \
  orchestrator/tests/test_s6_sort_sweep.py \
  orchestrator/tests/test_s8a_trigger_sweep.py \
  orchestrator/tests/test_backoff_consumers.py \
  orchestrator/tests/test_backoff_requested_us.py
```

結果は `rc=16`、`qstat -Q preflight rc=1`、`child_started=false` でした。実行済み nodeid は0件で、緑とは報告しません。

## 未実走・未完の範囲

- 上記5 fileの全137 nodeは未実走です。
- S8B 潜在 fixture 修正の動的確認も未実走です。
- source 上の根本原因修正は完了しています。残る確認は親 sandbox での pytest 再実走です。