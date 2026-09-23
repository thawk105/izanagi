T2 は期待値そのものが誤っているため、共通指示「期待値そのものが誤りだと判断したら、実装を変えず報告して止める」に従い停止しました。変更・commit はありません。

`test_harness_machine_slot_accepted[False]` は全 `build_run_context` 呼出しに coder authority を要求しています。しかし実際には、

- `default_cfg()`（`p3_s4_loop.py:1791`）が policy 束縛用に authority なしの context を作成する。
- `main()`（同 :3769）が K0 の評価用 context を CLI の coder authority 付きで作成する。

焦点走の `[None, CoderBuildAuthority(...)]` はこの既存経路と一致します。全呼出しへの要求ではなく、評価へ渡す context を検査する期待値への裁定変更が必要です。

## 総括

| 所見 | 状態 | 理由 |
|---|---|---|
| T1 | not-closed | T2 の停止条件により未修正 |
| T2 | not-closed | 期待値の誤りを確認。再裁定が必要 |
| T3 | not-closed | T2 の停止条件により未修正 |

受理・拒否挙動の変更なし。追加行数 production / test とも 0。所有外 caller・fixture・consumer への変更波及、所有外の必要変更はありません。テスト・変異は未実走です。

| 変異 | 登録関数・境界 | 登録された検出先（未実走） |
|---|---|---|
| M1 | `main` | `test_t2849_loop_entry.py::test_harness_machine_slot_accepted` |
| M2 | `_run_stock_control_resolved` | 同 `::test_read_heavy_reference_exact_flags` |
| M3 | `main` | 同 `::test_reference_rejected_outside_harness` |
| M4 | pipeline 保全・cleanup 境界 | `test_t2853_trace_preservation.py::test_archive_before_cleanup` |
| M5 | 同上 | 同 `::test_failure_retains_original` |
| M6 | 同上 | 同 `::test_preservation_error_does_not_replace_result` |
| M7 | 同上 | 同 `::test_unset_env_unchanged` |