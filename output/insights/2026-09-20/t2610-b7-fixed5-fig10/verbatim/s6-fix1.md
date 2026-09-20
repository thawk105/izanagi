## 実装した物

- **A-1 / B-2:** `CAPTION_SCOPE` と `test_provenance_binds_caption_source` を指定の逐語へ更新。
- **A-2:** `_caption` の固定文2・6と `test_caption_contains_fixed_literals` を更新。他の7文は維持。
- **A 削除候補:** `_caption` の自由度表示を `(df {DF})` に変更。
- **B-1:** `test_landed_fig10_repo_closure_and_caption_when_present` に、cell_id ごとの標本・median と稿 §2.2 の一致検査を追加。
- **B-3:** 等号境界と correctness trace-disabled の2 test を追加。fixture の hash は再封印。

## 実走した検査

`orchestrator/tests/test_plot_b7_fixed5_regression.py` の自走 harness：**41 passed / 0 failed / 0 skipped / 1 error**（rc=1）。

主要な実走 nodeid（接頭辞 `test_plot_b7_fixed5_regression.py::`）：

- `test_effect_equal_to_negative_floor_is_no_regression` — PASS
- `test_correctness_trace_disabled_record_is_rejected` — PASS
- `test_caption_contains_fixed_literals` — PASS
- `test_provenance_binds_caption_source` — PASS
- `test_pins_floors_effects_and_judgments_match_results_document` — PASS
- `test_cli_writes_three_outputs_and_provenance_closure` — PASS
- `test_cli_rejects_prefix_without_fig_number` — PASS
- `test_landed_fig10_rejects_all_missing_outputs` — PASS
- `test_landed_fig10_rejects_partial_missing_outputs` — PASS（6集合）
- `test_landed_fig10_repo_closure_and_caption_when_present` — **親の再生成待ち**。旧 `authority_scope` による `tracked_inputs closure mismatch`。

`test_plain_runner_coverage.py::` の以下3件：**3 passed / 0 failed / 0 skipped**（rc=0）。

- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_this_metatest_is_itself_self_runnable`

実データ生成は **rc=0**。`probe-t2610/` にPNG・PDF・provenanceを生成し、Pythonで固定文2・6の逐語包含、新 `authority_scope`、`df 4` を確認しました。`git diff --check` も通過。

## 受理・拒否の含意

測定入力の受理集合は**変わらない**。pin・schema・検査条件・描画・provenance の key 集合は維持しています。provenance の文言契約は更新され、着地 test は稿と異なる標本・median を追加で拒否します。

等号境界 test は、標本・median・effect が整合し `effect == -cv` となる rr50 を退行なしとして受理し、`<=` への変更を検出します。

correctness test は、正常 fixture が受理される条件から記録1件だけを `trace_enabled=False` にし、`raw correctness mismatch` で拒否します。

## 変異 m13 / m14 への対応

- **m13:** `test_plot_b7_fixed5_regression.py::test_effect_equal_to_negative_floor_is_no_regression`
- **m14:** `test_plot_b7_fixed5_regression.py::test_correctness_trace_disabled_record_is_rejected`

上記が各変異を検出する構造です。変異そのものの実走は未実施です。

## 総括

実装済み：指定2ファイルのみ変更、scratch は untracked。
指定検査はすべて実走済み。変異実走は未実施。
期待赤：着地 test 1件のみ、親の再生成待ち。
親への依頼：図・provenance の再生成、docs 更新、着地 test 再確認、変異実走・commit。