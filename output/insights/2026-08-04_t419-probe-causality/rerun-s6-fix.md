指定 2 ファイルだけを変更し、K-1〜K-5 を実装しました。docs・PBS・commit・pytest には触れていません。

実装前は、非自活動を arm 全体の per-CPU 5/6 tick で判定し、移動 process の全 delta を endpoint CPU に帰属していました。修正後は、実走経路では subwindow ごとの 2/3 tick 判定が主判定となり、arm 合計は判定に使いません。

| 項目 | 状態 | 対応 |
|---|---|---|
| K-1 / S6-01 / S6-02 | closed | anchor 前・最終 primary read 後に `/proc/stat` と自 tree PID の stat のみ取得。per-subwindow/per-CPU residual 2/3 判定と最大値を保存 |
| K-2 / S6-03 | closed | self stat endpoint または既存 read の reader CPU に移動があれば `ATTRIBUTION_UNRESOLVED`。residual による競合化を抑止 |
| K-3 / S6-04 | closed | A1 の incidental/OOB 交差件数・率を CPU ごと、pinned/control 別に追加 |
| K-4 / S6-05 | closed | A1 pin 順を5 targetずつ9群化。各 target の先頭 primary read、位置、flat index、余り3 targetを記録 |
| K-5 / S6-06 | closed | global-total、subwindow境界、migration、交差、α巡回、errno、理由完全一致 fixtureを追加 |
| regressed | 0 | 既存 assert の削除・反転・期待値変更なし |

`alpha_without_rotation` は報告対象から外し、`reported_method_columns` は `alpha_with_rotation / beta / gamma` です。既存 consumer 用の `alpha` alias は残していますが、`reported_as_alpha=False` として明示しています。巡回済み should-reject arm は既存445読みに存在しないため、そのセルは `evaluated=0` です。

変更ファイル:

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:39): +724 / -101
- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:802): +411 / -2

追加 test node（共通 prefix `orchestrator/tests/test_t419_probe_causality.py::`）:

- `test_incidental_nonself_five_ticks_is_valid_and_recorded`
- `test_nonself_six_ticks_is_competitor_invalid_and_stops_later_arms`
- `test_root_system_slice_nonself_six_ticks_is_competitor`
- `test_unreadable_diagnostic_fields_are_complete_and_valid`
- `test_diagnostic_error_is_incomplete_and_invalid`
- `test_diagnostic_status_counts_cover_all_four_values`
- `test_diagnostic_errno_classification_is_exact[eacces]`
- `test_diagnostic_errno_classification_is_exact[eperm]`
- `test_diagnostic_errno_classification_is_exact[enoent]`
- `test_diagnostic_errno_classification_is_exact[eio]`
- `test_nonself_three_ticks_on_each_of_two_cpus_is_not_globally_summed`
- `test_subwindow_two_tick_boundary_is_incidental_and_records_maximum`
- `test_subwindow_three_ticks_is_competitor_with_one_validity_reason`
- `test_migrated_subwindow_does_not_fabricate_per_cpu_competitor`
- `test_subwindow_boundary_sampling_reads_only_self_tree_and_proc_stat`
- `test_a1_incidental_out_of_band_intersection_is_split_by_population`
- `test_alpha_with_rotation_uses_nine_groups_and_records_three_discards`

変更した既存 node:

- `test_child_threshold_literals_are_pinned`: 新しい 5 / 2 定数を追加固定
- `test_released_child_pid_reuse_is_not_allowlisted`: stage 5 の fixture delta のみ変更
- `test_positive_nonself_pid_delta_is_competitor_snapshot_evidence`: stage 5 の fixture delta のみ変更

既存期待値の変更は0件、既存 assert の削除も0件です。

検査結果:

- `python3.10 -m py_compile ...`: rc=0
- 純計算 `--self-test`: rc=0、17 fixture PASS
- `git diff --check`: rc=0
- pytest: 0件（Pegasusログインノードのため未実行）

事前登録 primary read は引き続き `445`、arm順序・anchor/cooldown・critical window・0.95/0.05/46・canonical band・hash束縛・`INVALID ⇒ NOT_EVALUATED` は不変です。静的な所有外 caller は PBS wrapperによるCLI起動だけで、変更不要でした。

## 総括

- closed=11（K-1〜K-5、S6-01〜S6-06）、partial=0、regressed=0。
- 変更は指定2ファイルのみ、計 +1135/-103行。docs・PBS・commitなし。
- 新定数は snapshot=5、subwindow=2。実測根拠は subwindow 定数直後のdocstringへ記載。
- 445 primary read、arm順序、因果3条件、band、hash、INVALID含意は不変。
- py_compile rc=0、pure self-test rc=0、diff-check rc=0、pytest実行0件。
- 残リスクは巡回済み should-reject armが445読みに無く、αの同セルが未評価なこと。
- 親は計算ノードで追加17 nodeを含む対象pytestを実行すること。
- 実機では subwindow数 6/48/1/10/16/3、最大residual、migration量、A1交差を確認すること。
- αは9群・捨て3・各群のread index、診断は value=819/unreadable=48/error=0 を確認すること。
- 最後に全445読み、hash再照合、affinity復元、900秒以内完走を確認すること。