## 変更前の挙動

既定入力は repo 外の原保存先 `EVIDENCE_ROOT` でした。平坦 layout を `--evidence-root` に渡すと、`W1/result.json` などの階層ファイルが見つからず拒否されました。

## 変更

- [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:29): 追跡下の写しの位置と論理名から平坦ファイル名への固定対応を追加し、ファイルごとに階層を優先して平坦名へ fallback するよう変更。`load_evidence` と CLI の既定入力を repo root 配下の写しに変更しました。**505行／上限530行**。
- [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/orchestrator/tests/test_plot_mocc_witlight_four_arm.py:390): 平坦 layout の既定 CLI test を1本追加し、既存2本の原本 root による skip を除去しました。**535行／上限580行**。

## 裁定との対応

| 裁定・不変条件 | 実装箇所 |
|---|---|
| P1: 固定対応、階層優先、平坦名 fallback、双方の SHA-256 照合 | [生成器:29](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:29)、[生成器:126](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:126) |
| P1: `load_evidence` と CLI の既定 root、provenance の絶対 path | [生成器:248](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:248)、[生成器:479](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:479) |
| P1: 原保存先の `EVIDENCE_ROOT`、summary exact 照合、`source_inputs`、論理名の `external_inputs` を維持 | [生成器:28](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:28)、[生成器:118](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:118)、[生成器:122](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:122)、[生成器:137](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:137) |
| P1: pin と key 集合、CLI の pin 引数、統計・書式・描画、argv 形を維持 | [生成器:37](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:37)、[生成器:406](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/tools/plotting/plot_mocc_witlight_four_arm.py:406)。これらに差分なし |
| P2: 既存2 test を追跡下の写しで常時実行 | [test:467](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/orchestrator/tests/test_plot_mocc_witlight_four_arm.py:467)、[test:499](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/orchestrator/tests/test_plot_mocc_witlight_four_arm.py:499) |
| P2: 平坦 fixture の既定 CLI 実行と3成果物・provenance・外部閉包 | [test:390](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/orchestrator/tests/test_plot_mocc_witlight_four_arm.py:390) |
| P2: 既存の階層 fixture を維持 | [test:369](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-fig15-unit-a/orchestrator/tests/test_plot_mocc_witlight_four_arm.py:369) |

裁定と違えた箇所: **なし**。

## 変異の位置

各アンカーは現在の対象ファイル内で1回だけ現れます。変異自体は適用していません。

| ID | 置換アンカー → 置換後 | 赤になる想定の test・assert |
|---|---|---|
| M1 | `'W1/result.json': 'W1-result.json',` → `'W1/result.json': 'W2-result.json',` | `test_cli_default_reads_flat_verbatim_fixture` の `main(...) == 0`、実データ2 test の読み出し／外部閉包。W1 の SHA-256 不一致という単一理由 |
| M2 | `parser.add_argument("--evidence-root", type=Path)` → `parser.add_argument("--evidence-root", type=Path, default=Path(EVIDENCE_ROOT))` | `test_cli_default_reads_flat_verbatim_fixture` の `main(...) == 0`。tmp repo の既定入力を読まない単一理由 |
| M3 | `path = Path(evidence_root)/VERBATIM_FILES[rel]` → `path = Path(evidence_root)/rel` | `test_cli_default_reads_flat_verbatim_fixture` の `main(...) == 0`、実データ2 test の読み出し／外部閉包。平坦ファイル不在という単一理由 |

## 波及

所有外の Python caller に該当参照は見つかりませんでした。共有 fixture `_fixture` と既存の階層 fixture test は変更していません。`test_plain_runner_coverage.py` はファイル単位で自走 harness を確認し、test 名の固定一覧は持たないため、変更不要です。`tools/plotting/README.md` などの入力説明には既定 root 変更の記述波及がありますが、本単位では編集していません。

## 実走

`py_compile` は両ファイルで成功。自走 harness は **28 PASS、0 FAIL、0 SKIP、0 ERROR** でした。

```text
PASS test_arm_bindings_and_rotation_are_checked
PASS test_caption_fixed_literals_and_forbidden_claims
PASS test_caption_number_comes_from_prefix
PASS test_cli_default_reads_flat_verbatim_fixture
PASS test_cli_outputs_and_provenance_closure
PASS test_commit_mean_uses_all_runs_of_each_arm
PASS test_cp95_matches_reference_values_and_boundaries
PASS test_external_hash_drift_is_rejected
PASS test_external_sources_and_repo_closure_have_separate_roots
PASS test_failure_or_indeterminate_is_rejected
PASS test_fisher_is_one_sided_on_lower
PASS test_fixture_has_production_shape_and_rotation
PASS test_landed_fig15_external_closure_when_root_present
PASS test_landed_fig15_rejects_missing_or_partial_bundle
PASS test_landed_fig15_repo_closure_and_caption_when_present
PASS test_layout_failure_publishes_nothing
PASS test_layout_rejects_overlap_wrong_axes_and_escape
PASS test_production_pins_match_results_document
PASS test_real_evidence_matches_results_document_when_root_present
PASS test_real_figure_passes_layout_check
PASS test_relocated_evidence_keeps_original_input_paths
PASS test_rendered_artists_equal_provenance
PASS test_required_disclosures_are_rendered
PASS test_smoke_or_duplicate_run_in_main_block_is_rejected
PASS test_statistics_recomputed_from_runs
PASS test_summary_disagreement_is_rejected
PASS test_summary_inputs_are_exact
PASS test_summary_inputs_reject_smoke_extra_entry
```

生成器の既定入力での実走は **rc=0**。`fig15_test.png`、`fig15_test.pdf`、`fig15_test.provenance.json` の3ファイルを確認し、一時ディレクトリは削除しました。`git diff --check` は成功。変異 M1〜M3 の実行、計算ノードでの test は未実走です。

## 総括

追跡下の平坦な写しから、既定設定で fig15 を生成できるようになりました。変更は指定の2ファイルのみで、commit は作成していません。