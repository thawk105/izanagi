## 変更した物

- `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`：例外文2箇所を先頭行の完全一致へ変更。同階層の`skiputil` importへ統一。実証拠テストに、曝露比2行を独立literalで可視Textと照合する検査を追加。
- `tools/plotting/plot_mocc_witlight_four_arm.py`：指定の隣接panel検査4行だけ削除。

## 実走した検査

`pegasus02`で実施。

| 検査 | 結果 |
|---|---|
| PYTHONPATHなしの直接実行 | 27 passed、0 failed、0 skipped、4.076秒 |
| `PYTHONPATH=.`付き直接実行 | 27 passed、0 failed、0 skipped、3.843秒 |
| 修正2関数の例外文確認 | 6ケース通過。説明付きは受理、別文言・先頭行末尾の相違は拒否 |
| M14描画2行削除→復元 | 緑→曝露比literalで赤→緑 |
| 指定CLIで作図 | rc=0 |
| 着地provenance比較 | 指定4キー以外の全11キー・captionが完全一致 |
| layout比較 | 削除前後とも通過 |
| probeのrepo／外部閉包 | ともに通過 |
| `git diff --check` | 通過 |

M14前後の生成器SHA-256は一致：

```text
5e46ef9ab403ddc17a05579a68ab0af417dd2f2cf87ee324185e83a7db9db942
```

両直接実行で通過した27 nodeid。共通接頭辞は`orchestrator/tests/test_plot_mocc_witlight_four_arm.py::`：

```text
test_arm_bindings_and_rotation_are_checked
test_caption_fixed_literals_and_forbidden_claims
test_caption_number_comes_from_prefix
test_cli_outputs_and_provenance_closure
test_commit_mean_uses_all_runs_of_each_arm
test_cp95_matches_reference_values_and_boundaries
test_external_hash_drift_is_rejected
test_external_sources_and_repo_closure_have_separate_roots
test_failure_or_indeterminate_is_rejected
test_fisher_is_one_sided_on_lower
test_fixture_has_production_shape_and_rotation
test_landed_fig15_external_closure_when_root_present
test_landed_fig15_rejects_missing_or_partial_bundle
test_landed_fig15_repo_closure_and_caption_when_present
test_layout_failure_publishes_nothing
test_layout_rejects_overlap_wrong_axes_and_escape
test_production_pins_match_results_document
test_real_evidence_matches_results_document_when_root_present
test_real_figure_passes_layout_check
test_relocated_evidence_keeps_original_input_paths
test_rendered_artists_equal_provenance
test_required_disclosures_are_rendered
test_smoke_or_duplicate_run_in_main_block_is_rejected
test_statistics_recomputed_from_runs
test_summary_disagreement_is_rejected
test_summary_inputs_are_exact
test_summary_inputs_reject_smoke_extra_entry
```

## 変異 M11〜M14 の kill 先

同じnodeid接頭辞を使用します。

| 変異 | kill先 | 今回の変異実走 |
|---|---|---|
| M11 | `test_required_disclosures_are_rendered` | 未実走 |
| M12 | `test_caption_fixed_literals_and_forbidden_claims` | 未実走 |
| M13 | `test_layout_failure_publishes_nothing` | 未実走 |
| M14 | `test_real_evidence_matches_results_document_when_root_present` | **KILLED** |

## 総括

4項目を修正し、指定検査はすべて通過しました。pytest自体は未実行です。変更は所有2ファイルのみ。`probe-fig15-fix/`の3成果物はuntrackedで残しました。禁止されたGit変更操作は実行していません。