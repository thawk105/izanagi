実装のみ完了しました。docs・PBS wrapper・commit には触れていません。

現行の「正の非自消費はすべて拒否」「不可読診断も拒否」から、裁定どおり次へ変更しました。

- CPU ごとの非自消費合計が 1–5 tick：`ATTRIBUTION_UNRESOLVED`、arm は VALID、後続継続
- 6 tick 以上：`COMPETITOR`、INVALID、後続停止
- uid・comm・cgroup は記録のみ。判定には不使用
- 診断は `value / absent / unreadable / error`。`error` のみ incomplete
- 安定 field は `incidental_nonself_cpus`、`incidental_nonself_ticks_by_cpu`、`status_counts`、`status_counts_by_field`

静的な波及先は `IsolationTracker.finish()`、arm 実行・後続抑止、`evaluate()`、result.json の isolation/diagnostics consumer です。所有外に同関数のコード caller はなく、既存 output と README が新 field の利用候補です。

pytest は Pegasus ログインノード禁止のため実行 0 node、緑の主張はしません。既存テストの期待値は変更せず、旧 competitor fixture の入力だけを新境界の 6 tick に合わせました。

## 総括

- (a) [probe](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:39) +177/-19、[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:753) +148/-2。
- (b) `INCIDENTAL_NONSELF_TICKS_MAX = 5` と、A0 の 4 tick・CPU 22 が 30/30 帯内だった根拠を直後の docstring に記載。
- (c) 追加 node: `test_incidental_nonself_five_ticks_is_valid_and_recorded`、`test_nonself_six_ticks_is_competitor_invalid_and_stops_later_arms`、`test_root_system_slice_nonself_six_ticks_is_competitor`。
- (c) 追加 node: `test_unreadable_diagnostic_fields_are_complete_and_valid`、`test_diagnostic_error_is_incomplete_and_invalid`、`test_diagnostic_status_counts_cover_all_four_values`。
- (d) `python3.10 -m py_compile` rc=0、純計算 `--self-test` 全17 fixture rc=0、`git diff --check` rc=0、pytest 0 node。
- (e) 親は計算ノードで全 test file、A0 の incidental CPU/量、48 policy の unreadable 集計、A1 以降の完走、6 tick 以上の停止を確認すること。
- 未変更: 0.95/0.05/46、canonical band、`INVALID ⇒ NOT_EVALUATED`、445 読み、arm 順序、anchor/cooldown/critical window、投入時 hash 束縛。