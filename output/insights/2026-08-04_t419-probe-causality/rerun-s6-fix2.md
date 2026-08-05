実装を完了しました。編集は指定された [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:39) と [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:183) のみです。docs・PBS・commit は変更していません。

- COMPETITOR 判定を `unexplained >= 3 && unexplained/duration_s > 6.7` のみに統一。
- arm 合計絶対 tick 判定と no-subwindow fallback を削除。空 subwindow は専用理由で INVALID。
- snapshot は PID/starttime、uid、comm、cgroup、消費量の証拠専用。
- self は安定した単一 CPU affinity が確認できる場合のみ per-CPU 帰属。それ以外は全量控除。
- 実 duration、unexplained 率、per-CPU residual 最大値を記録。
- `method_table.alpha` を巡回 α に変更し、旧方式は `alpha_without_rotation` のみに限定。

### 対応表

| 項目 | 判定 | 対応 |
|---|---|---|
| L-1 | closed | duration 正規化、旧絶対閾値・fallback 削除、空 subwindow INVALID、snapshot 判定除外 |
| L-2 | closed | affinity が安定した singleton の場合だけ帰属。非 pin self は `self_unattributable_total` へ控除 |
| L-3 | closed | `alpha` は巡回 9 群、旧方式は `alpha_without_rotation` のみ |
| S6R2-01 | closed | A4 の 1.5 秒窓も同じ率判定。A4 の読み方は未変更 |
| S6R2-02 | closed | endpoint CPU による推定を廃止し、同一 endpoint・multi-affinity fixture を追加 |
| S6R2-03 | closed | 旧 α の compatibility alias を削除 |
| S6R2-04 | partial | subwindow 0 件は INVALID。厳密な arm 別個数・ID・read 対応検証は backlog のまま |
| S6R2-05 | partial | duration・最大 residual・最大率を保存。4032 判定機会の実機偽陽性率は未測定 |
| S6R2-06 | closed | `SNAPSHOT_NONSELF_TICKS_MAX` 系と no-subwindow fallback を完全削除 |
| regressed | 0 | 禁止された受理集合・因果条件・読み数への変更なし |

### 今回追加・変更した test node

共通 prefix は `orchestrator/tests/test_t419_probe_causality.py::` です。

新規:

- `test_subwindow_rate_equal_to_limit_is_unresolved`
- `test_missing_all_isolation_subwindows_has_single_structural_reason`
- `test_unpinned_self_large_consumption_is_not_competitor`
- `test_stably_single_cpu_affinity_self_is_attributed_to_that_cpu`

段6初回 fixture の変更・改名:

- `test_nonself_snapshot_is_identity_evidence_only_and_valid`
- `test_rate_qualified_nonself_is_competitor_invalid_and_stops_later_arms`
- `test_root_system_slice_nonself_snapshot_is_identity_evidence_only`
- `test_subwindow_global_unexplained_rate_below_threshold_is_unresolved`
- `test_subwindow_two_tick_boundary_is_incidental_and_records_maximum`
- `test_subwindow_three_ticks_is_competitor_with_one_validity_reason`
- `test_same_endpoint_unpinned_self_is_unattributable_and_unresolved`
- `test_subwindow_boundary_sampling_reads_only_self_tree_and_proc_stat`
- `test_alpha_with_rotation_uses_nine_groups_and_records_three_discards`

既存 node の fixture/key 更新:

- `test_child_threshold_literals_are_pinned`
- `test_method_table_includes_a2_sham_in_should_pass_population`
- `test_should_reject_rows_are_not_replaced_by_constant_reject`
- `test_short_lived_competitor_is_detected_from_unattributed_ticks`
- `test_released_child_pid_reuse_is_not_allowlisted`
- `test_irq_and_softirq_only_ticks_are_clean`
- `test_unpinned_reader_migration_is_unresolved_but_valid`
- `test_residual_above_self_unattributable_invalidates_and_stops_later_arms`
- `test_positive_nonself_pid_delta_is_competitor_snapshot_evidence`
- `test_completed_child_fork_to_reap_ticks_are_all_attributed`
- `test_isolation_residual_is_never_cancelled_across_cpus`

既存期待値の変更は、親が承認した `alpha` key の意味変更に伴う2 nodeだけです。それ以外の既存 assertion 期待値変更は **0件**です。競合系の既存 node は fixture に rate-qualified subwindow を追加しただけです。

検査結果:

- `python3.10 -m py_compile ...`: rc=0
- 純計算 `--self-test`: rc=0、17 fixture PASS
- `git diff --check`: rc=0
- pytest: **0件**（`pegasus02` では禁止のため未実行）

静的確認では primary read は引き続き **445**（30+240+30+50+80+15）。arm 順、A4 の1窓、anchor/cooldown/critical window、0.95/0.05/46、canonical band、hash 束縛、`INVALID ⇒ NOT_EVALUATED` は不変です。所有外の能動 consumer は PBS wrapper の CLI 呼出しだけで、変更不要でした。親の README/表作成側は新しい duration・snapshot 証拠 field と `method_table.alpha` を読む必要があります。

## 総括

- closed=7、partial=2、regressed=0（L-1〜L-3 と S6R2-01〜06 の集計）。
- worktree 全差分は probe +757/-102、test +543/-6、指定2ファイルのみ。
- 新定数は `COMPETITOR_MIN_TICKS=3` / `COMPETITOR_MAX_TICKS_PER_SECOND=6.7`、直後に実測根拠を記載。
- 445、因果3条件、band、arm順、A4、hash、INVALID含意は不変。
- py_compile rc=0、self-test rc=0、diff-check rc=0、pytest 0件。
- 残リスクは S6R2-04 の厳密配置 gate と、4032 判定機会の実機分布。
- 親は84 subwindow（6/48/1/10/16/3）の duration・最大 residual・最大率・self控除を確認すること。
- A1交差、A2/A3 child tick、巡回α9群/余り3、診断819/48/0、全445読みも確認すること。
- submission/final hash、parser 3/3、affinity復元、900秒以内完走を実機で確認すること。