M-1〜M-3 を実装し、指定2ファイルだけを変更しました。commit・docs 編集・pytest 実行はしていません。

| 項目 | 判定 | 対応 |
|---|---|---|
| M-1 / S6R3-01 | closed | reader migration を判定前に self identity へ反映。equal-singleton 往復移動でも CPU 帰属を撤回し、全量を `self_unattributable_total` へ移して `ATTRIBUTION_UNRESOLVED` にする |
| M-2 / S6R3-02 | closed | `affinity_not_singleton` と `migration_observed` を subwindow・arm 集約・A4 出力で分離。`migration_detected` は実移動だけを示す |
| M-3 / erratum-4 | closed | `COMPETITOR_MAX_TICKS_PER_SECOND = 25.0` と指定根拠へ更新。絶対下限3 tickとのAND条件は不変 |
| regressed | なし | 因果3条件、canonical band、INVALID implication、445、arm順序、α、hash束縛は変更なし |

変更量:

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py): +109 / -36
- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py): +68 / -12

追加・変更したテスト node の完全列挙:

- 追加: `test_equal_singleton_return_migration_revokes_self_cpu_attribution`
- M-2 強化: `test_same_endpoint_unpinned_self_is_unattributable_and_unresolved`, `test_subwindow_boundary_sampling_reads_only_self_tree_and_proc_stat`
- M-3 更新: `test_child_threshold_literals_are_pinned`, `test_short_lived_competitor_is_detected_from_unattributed_ticks`, `test_released_child_pid_reuse_is_not_allowlisted`, `test_residual_above_self_unattributable_invalidates_and_stops_later_arms`, `test_positive_nonself_pid_delta_is_competitor_snapshot_evidence`, `test_rate_qualified_nonself_is_competitor_invalid_and_stops_later_arms`, `test_subwindow_two_tick_boundary_is_incidental_and_records_maximum`, `test_subwindow_three_ticks_is_competitor_with_one_validity_reason`, `test_subwindow_rate_equal_to_limit_is_unresolved`, `test_isolation_residual_is_never_cancelled_across_cpus`

既存 node の verdict・VALID/INVALID・停止期待値変更は0件です。数値・fixture 更新はM-3再較正に限り、25.0、率超過を維持する窓長、閾値同値25.0へ更新しました。M-1/M-2による既存期待値の置換は0件です。

検査結果:

- `python3.10 -m py_compile`（両ファイル）: rc=0
- 純計算 `--self-test`: rc=0、17 fixture
- `git diff --check`: rc=0
- pytest: 0件
- `EXPECTED_PRIMARY_READS` 合計と `PREREGISTERED_PRIMARY_READS`: ともに445、不変
- 因果条件: 0.95 / 0.05 / 46、不変

所有外への波及候補は、結果JSONのA4 consumerとinsight生成側です。A4は今後 `migration_observed` と `affinity_not_singleton` を別々に読む必要があります。リポジトリ内に旧 migration field の実 consumer は見つかりませんでした。

## 総括

- (a) M-1 closed、M-2 closed、M-3 closed、partial/regressedなし。
- 変更は指定2ファイルのみ。新定数25.0の実測根拠は定数直下docstringへ記録。
- 445 primary read、因果3条件、band、INVALID implication、arm順序、α、hash束縛は不変。
- 残リスクは、primary read間で完結して観測点に現れない migration は検出不能なこと。
- 親は計算ノードで全pytestと、equal-singleton fixture、2/3 tick境界を確認すること。
- 実機ではA4の2 field、A2約100 tick/s検出、全445読み、最終hash束縛を確認すること。