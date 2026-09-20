# 段 4 裁定 — fig13 (軽量版: 段 2・3 省略。親の brief を plan v2 として確定し、変異を事前登録する)

裁定 inbox の再走査 (19:20 JST): `docs/spool/{worklog,decisions,failures}` の未 fold fragment は T-2304 の 1 組だけで本 wave と無関係。repo 外 inbox は 2026-08-25 の 1 dir で古い。
最新 D は D2183。fig13 に関する更新なし。

## 採否

- 採用: brief §scope の 6 行、(P1) 図の形、成果物の形、不変条件 1〜8。段 6 review 2 本を残す理由 = 新図種の caption / 限定文は新しい受理集合 (README 収録と provenance の逐語一致を着地 test が守る) で、
  fig11 先例 (受理集合が広がる wave で review 2 本を残した) と同型。
- 不採用 (scope 外・要求外): 対差 54 個の別 panel (依頼は 36 cell と 3 族)、全 135 cell の throughput 図、参照点 `none` / `adaptive` / `zero-loop` の描画 (判定の族に入らない、稿 §1.2)、
  paper-story/README.md の results 表の更新 (ユーザー指示)、新しい gate / 検査 / 台帳 (ユーザー指示)、既存生成器の一般化 (自己完結の新 file の方が既存 fig の bytes を守りやすい、fig10 型)。

## plan v2 (author の正本)

### §1 生成器 `tools/plotting/plot_b10_waiting_grid_forest.py` (新設、自己完結、matplotlib + numpy のみ、`plot_b7_fixed5_regression.py` を雛形にする)

定数 (全部 module 定数として持ち、CLI からは変えられない):
- `SCHEMA = "izanagi-b10-waiting-grid-forest-figure-provenance/v1"`, `GENERATOR_PATH`, `REPO_ROOT = Path(__file__).resolve().parents[2]`
- `PROVENANCE_JSON = "output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json"`, `REPORT_MD = ".../b10_backoff_shape_report_978195.nqsv-23409962b76b.md"`
- `PINNED_SHA256 = {PROVENANCE_JSON: "a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca", REPORT_MD: "e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768"}`, `INPUT_KINDS = ("report_provenance", "report_markdown")`
- `CAPTION_SOURCE = "docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md"`, `CAPTION_SCOPE` (稿は限定・条件の言い方の出所であって、測定値・判定の一次権威ではない)
- `EVIDENCE_ROOT = "/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape"`, `REPORT_NONCE = "23409962b76be959bb523a0cd5a31bc1"`, `REPORT_REQUEST = "978195.nqsv"`
- `EXTERNAL_REL = {"report_receipt": f"submissions/{REPORT_NONCE}/submit-receipt.json", "report_job_result": f"submissions/{REPORT_NONCE}/job-attempts/{REPORT_REQUEST}/job-result.json"}`
- `EXTERNAL_SHA256 = {"report_receipt": "93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4", "report_job_result": "d5d4a0ee4c503c1b4b6a811f998949f7a76434a575c4ed8d0bfad849eafd082b"}`
- `PROVENANCE_SCHEMA = "b10-backoff-shape-provenance/v2"`, `JUDGEMENT_SCHEMA = "b10-backoff-shape-judgement/v1"`, `RECEIPT_SCHEMA = "pegasus-b10-submit-receipt/v2"`, `JOB_RESULT_SCHEMA = "pegasus-b10-job-result/v1"`
- `PREREG_COMMIT = "77b33e37d2d63b1f83d10652792c3c93eba9fe8f"`, `SOURCE_COMMIT = "2a338449bb2798b729c5bc2f9bfe76463a7fe347"`, `CCBENCH_PIN = "511c953"`, `SPEC_SHA256 = "9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2"`
- `WORKLOADS = ("write-heavy", "balanced", "read-heavy")`, `BLOCKS = ("block-1", "block-2", "block-3")`, `MEANS_US = (2, 5, 10, 25, 50, 100)`, `SHAPES = ("constant", "symmetric-modulo")`, `REFERENCE_SHAPE = "constant"`, `CONTRAST_SHAPE = "symmetric-modulo"`
- `PAIRS_PER_FAMILY = 18`, `ENUMERATION = 2 ** 18`, `ALPHA = 0.05`, `EQUIVALENCE_MARGIN_PCT = 3.0`, `T975_DF2 = 4.302652729911275`, `DF = 2`, `REPS = 5`, `POINTS_PER_BLOCK = 15`, `RECORDS = 135`, `CELLS = 36`, `FAMILIES = 3`
- `RELATIONS = ("inside-equivalence-range", "overlaps-equivalence-boundary", "outside-equivalence-range")` — 3 番目の名前は spec / report にその値の実例が無い (36 cell に 0 件)。生成器は `outside` を「区間全体が帯の外」として再分類の結果に使うだけで、
  report にこの値が現れたら (現行 bytes には無い) 名称一致を要求する。実例が無い名前を受理集合に足すのではなく、再分類で `outside` になった cell が report の `equivalence_relation` と一致しなければ拒否する。

`_authority_data(root, expected_hashes)`:
1. tracked 2 file の SHA-256 を pin と照合 (override は test 専用の `expected_hashes`、key 集合一致を要求)。稿の存在と SHA-256 を `caption_source` として記録。
2. provenance JSON: `schema_version` / `official_certification is False` / `pin` / `submission` (request_id, nonce, phase == "report", receipt_sha256 == EXTERNAL_SHA256["report_receipt"], source_commit, prereg_commit, job_script_sha256 は 64 hex) / `judgement.schema_version` / `judgement.alpha == ALPHA` / `judgement.spec_sha256 == SPEC_SHA256` /
   `preregistration.spec.analysis` (alpha, equivalence_margin_pct, confidence_interval.{critical_value, degrees_of_freedom, method}, permutation.{enumeration "all-2^18", pairs_per_family 18, sided "two-sided"}, holm_families が WORKLOADS × CONTRAST_SHAPE の 3 件) / `preregistration.spec.grid.means_us == list(MEANS_US)` と `shapes` の name 2 件。
3. records: ちょうど 135、(workload, block_id, point) が一意、3 workload × 3 block × 15 点、全件 `correctness_certified is True` / `missing is False` / `unstable is False` / `official_certification is False` / `median_tps > 0` / `len(throughputs) == 5` かつ `median(throughputs) == median_tps`。
   登録 cell (shape ∈ SHAPES かつ mean_us ∈ MEANS_US) は 108 件、`backoff_call_count >= spec.analysis.exposure.minimum_calls_per_cell`。`zero-loop` (shape constant, mean_us 0) と `none` / `adaptive` は登録 cell に数えず描かない。
4. 族 3 件の再計算: 各 workload について `differences` を block-major / μ-minor の順に `median(sm) / median(const) − 1` で組み立て、report の `differences` と abs 1e-12 で全一致。`pairs == 18`、`status == "testable"`、`reasons == []`、`outcome == "different"` (これは現行 report の値の照合。`different` 以外の値は現行 bytes に無いので拒否 = 図はこの report 専用)、
   `raw_p * 2**18` が整数 (abs 1e-9) でその整数を `raw_p_numerator_2pow18` に記録、Holm を再計算 (昇順 i=1..3 で `max_{j≤i} min(1, (3−j+1)·p_j)`) して `holm_p` と abs 1e-15 で一致、`holm_p <= alpha`。`sum_of_differences` と `direction` (`"symmetric-modulo higher"` iff sum > 0) を記録。
   **raw p 自体は再計算しない** (全 2^18 列挙は report の仕事。生成器は分母 2^18 の整数性と Holm だけを照合する)。
5. cell 36 件の再計算: (workload, shape, mean_us) が 36 通り一意。constant 18 cell は `effect == 0 and ci95_low == 0 and ci95_high == 0 and equivalence_relation == inside`。symmetric-modulo 18 cell は block 3 値の平均 = `effect`、`平均 ∓ T975_DF2 × stdev / √3` = `ci95_low` / `ci95_high` (abs 1e-12)、
   `equivalence_margin_pct == 3.0`、`status == "estimable"`、再分類 (両端が ±0.03 の内側 → inside、区間全体が外 → outside、他 → overlaps) が `equivalence_relation` と一致。summary (inside / overlaps / outside / indeterminate / estimable) を数える。
6. report .md: `## Paired sign-flip permutation + Holm` 節の 3 行を parse し、各 workload の `outcome=` / `pairs=` が JSON と一致、`raw_p=` / `holm_p=` は report .md の丸め (8 桁有効) と `float` 比較で rel 1e-6 以内。`## Cell effects and 95% paired-block intervals` 節が 36 行。
7. 受領証 / job 結果 (`load_evidence` だけが読む。`validate_repo_closure` は読まない): SHA-256 を EXTERNAL_SHA256 と照合、schema、`dry_run is False`、`phase == "report"`、`request_id` / `nonce` / `source_commit` / `prereg_commit` / `job_script_sha256` が provenance JSON `submission` と一致、job 結果の `driver_rc == 0`、`completed_epoch > submitted_epoch`。

`make_figure(data)`: brief (P1) どおり。figsize は layout check が通る幅 (目安 13 × 5.2)。3 axes だけ (凡例は fig 全体または axes 内)。x 範囲は 36 cell の区間と ±3% 帯を含む共通対称範囲。y は μ 6 行、`invert_yaxis`。
`check_figure_layout(fig, axes)`: b7 と同型 (axes ちょうど 3、text の重なり・図外逸脱・隣 panel 侵入・軸装飾逸脱で `FigureLayoutError`)。
`_caption(data, prefix)`: 英文、決定的。固定文 (test で逐語検査):
1. `Each family's outcome is the preregistered procedure's classification and is not a research verdict.`
2. `Intervals lying inside the +/-3.0% margin are reported as the position of the interval and are not a finding of equivalence; no equivalence test was performed.`
3. `Per-cell intervals are descriptive and no per-cell significance decision is made; the only tests are the three family-level permutation tests with Holm adjustment.`
4. `The static right-tail cohorts (separate preregistration, grid and driver) are neither pooled nor compared with this grid.`
5. `official_certification is false; these performance values are not a basis for adopting a variant.`
6. `Direction and effect sizes are stated for this one contrast only; nothing is claimed about waiting-shape effects in general, about binary, about a dose response of dispersion, or about a general separation of waiting shape from waiting amount.`
7. `Correctness is recorded from separate trace-enabled runs (135 of 135 cells certified) and is not a performance certification.`
8. `The three workloads ran as separate jobs on different days and driver versions; absolute throughput is not compared across workloads, and no mechanism is claimed for the direction.`
禁句 (caption に現れてはならない、test で検査): `equivalent`, `superior`, `desynchroniz`, `performance certified`, `significantly`, `no difference`, `mechanism explains`, `reproduc`.
値は data から書式化: 3 族の outcome / raw p (分数と小数) / Holm p / 対 18 / 和の符号、36 cell の集計 (inside 32 / overlaps 4 / outside 0 / indeterminate 0)、点推定が負の cell 数、区間下限が正の cell 数、条件 (Pegasus compute nodes, 48 threads, silo, YCSB 3 workload, μ grid, 5 reps × 3 blocks, CCBench pin, report request, prereg commit 短縮 9 桁, source commit 短縮 9 桁)。
`Figure {N}.` の N は prefix の `fig<N>_` から。
`build_provenance` / `validate_repo_closure` / `validate_external_sources` / `_publish_outputs` / `main` は b7 と同型 (tmp → atomic replace、失敗時は 1 つも残さない)。`main` の引数は `--repo-root`, `--evidence-root`, `out_prefix`。
**perf closure 規則**: `if` / `while` / 三項の条件式に `perf` を含む名前を置かない。

### §2 test `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (新設、`test_plot_b7_fixed5_regression.py` を雛形にする)

fixture `_fixture(tmp_path)`: tmp repo に provenance JSON (実寸: 135 record = 3 workload × 3 block × 15 点、各 5 throughputs で median 一致、登録 cell の backoff_call_count ≥ 10000、参照点 3 種を含む、judgement.families 3 件 = fixture 自身が同じ式で differences / raw_p (2^18 分母の整数から作る) / Holm を計算、cell_effects 36 件 = 同じ式で effect / CI / relation を計算、
spec.analysis / grid / submission / top-level を実物と同じ key で)、report .md (Holm 3 行 + Cell effects 36 行、実物と同じ書式)、稿 (caption_source、内容は短い placeholder 文で可 — ただし `test_document_values_match_report_json` は実 repo の稿を読む)、tmp evidence root に受領証 + job 結果 (実物と同じ key)、`expected_hashes` override。
fixture の値は「境界を跨ぐ」「点推定が負」「区間下限が正」を少なくとも 1 cell ずつ含む形にする (実寸の注記密度)。
test 一覧 (名前は変異表の「期待 node」と一致させる):
- 形: `test_fixture_has_production_shape_and_recomputes_statistics`, `test_artist_series_equal_provenance_cells_and_rendered_artists`, `test_real_figure_passes_layout_check`, `test_bbox_overlap_is_a_failure`, `test_layout_failure_publishes_nothing`, `test_layout_rejects_wrong_axes_count`
- caption: `test_caption_contains_fixed_literals`, `test_caption_avoids_forbidden_claims`, `test_caption_figure_number_comes_from_prefix`
- 拒否: `test_provenance_json_hash_drift_is_rejected`, `test_report_markdown_hash_drift_is_rejected`, `test_receipt_hash_drift_is_rejected`, `test_job_result_hash_drift_is_rejected`, `test_receipt_sha_not_matching_submission_is_rejected`, `test_receipt_identity_mismatch_is_rejected`, `test_job_result_driver_rc_nonzero_is_rejected`,
  `test_family_count_mismatch_is_rejected`, `test_family_outcome_or_pairs_mismatch_is_rejected`, `test_differences_order_mismatch_is_rejected`, `test_differences_value_mismatch_is_rejected`, `test_raw_p_not_dyadic_is_rejected`, `test_holm_p_mismatch_is_rejected`, `test_holm_p_above_alpha_is_rejected`,
  `test_cell_count_mismatch_is_rejected`, `test_cell_effect_mismatch_is_rejected`, `test_cell_interval_mismatch_is_rejected`, `test_equivalence_relation_mismatch_is_rejected`, `test_constant_cell_nonzero_is_rejected`, `test_uncertified_or_missing_or_unstable_record_is_rejected`, `test_official_certification_true_is_rejected`,
  `test_record_count_mismatch_is_rejected`, `test_median_not_matching_throughputs_is_rejected`, `test_underexposed_registered_cell_is_rejected`, `test_report_markdown_holm_line_mismatch_is_rejected`, `test_caption_source_missing_is_rejected`, `test_spec_constants_mismatch_is_rejected`
- 閉包: `test_provenance_binds_caption_source`, `test_pinned_hashes_are_used_when_no_override`, `test_generator_comment_change_preserves_provenance_closure`, `test_external_sources_and_repo_closure_have_separate_roots`, `test_landed_output_paths_reject_same_basename_in_other_directory`
- 実データ: `test_pins_match_results_document` (稿 §4.1 の表に pin 2 値が逐語で現れ、現物 SHA と一致、`REPO/PROVENANCE_JSON` の実 SHA が pin と一致), `test_document_values_match_report_json` (稿 §2.2 表の Holm p / raw p 3 組、§2.4 生値表の 18 行 effect / ci95_low / ci95_high / relation を parse して実 JSON と一致),
  `test_real_evidence_loads_when_root_present` (evidence root 不在なら skip、部分欠は失敗。summary が inside 32 / overlaps 4 / outside 0)
- CLI: `test_cli_writes_three_outputs_and_provenance_closure`, `test_cli_rejects_prefix_without_fig_number`
- 着地: `test_landed_fig13_repo_closure_and_caption_when_present` (fig10 / fig11 型: bundle 3 file 実在 → `validate_repo_closure(prov, REPO)` → caption が figures/README.md に逐語 → README の fig13 節「## 着地 bytes の SHA-256」3 行と現物一致 → provenance の caption_source の SHA が稿の現 SHA と一致。未着地は失敗、skip 化しない)、
  `test_landed_fig13_rejects_all_missing_outputs`, `test_landed_fig13_rejects_partial_missing_outputs`
- 末尾に `_run()` + `if __name__ == "__main__": sys.exit(_run())` (b7 と同型、`skiputil` 使用)。

### §3 親の docs (段 7 前に親が書く)
- `docs/paper-story/figures/README.md`: 一覧表 fig13 行、末尾節 (fig11 節の見出し構成を踏襲)。日本語キャプション正文 + 英文 caption (provenance と同一文字列)。
- `tools/plotting/README.md`: fig13 生成器の節。

## 変異事前登録 (DW-M01、実装後に単一理由性を確認して final)

対象 = `tools/plotting/plot_b10_waiting_grid_forest.py` のみ。runner = 新 test file (計算ノード dispatch)。probe で観測した赤 node の完全集合を期待 node にする。

| id | 位置 (生成器) | 変異 | 期待 |
|---|---|---|---|
| m0 | module docstring | 1 語追加 (等価対照) | SURVIVED (全 test 緑、provenance closure 不変) |
| m1 | `PINNED_SHA256[PROVENANCE_JSON]` | 末尾 1 hex 変更 | KILLED — `test_pinned_hashes_are_used_when_no_override`, `test_pins_match_results_document`, 実データ系 |
| m2 | receipt_sha256 照合 | `submission.receipt_sha256 == EXTERNAL_SHA256[...]` の `_require` を削除 | KILLED — `test_receipt_sha_not_matching_submission_is_rejected` |
| m3 | differences 照合 | list 比較を sorted 比較に変える (順序不問) | KILLED — `test_differences_order_mismatch_is_rejected` |
| m4 | CI 再計算 | `T975_DF2` を 1.96 に | KILLED — `test_cell_interval_mismatch_is_rejected`, 形 test |
| m5 | 等価域再分類 | 再分類の一致検査を削除 (report の値を信用) | KILLED — `test_equivalence_relation_mismatch_is_rejected` |
| m6 | Holm 再計算 | 一致検査を削除 | KILLED — `test_holm_p_mismatch_is_rejected` |
| m7 | caption 固定文 2 | 文を削除 | KILLED — `test_caption_contains_fixed_literals` (+ closure) |
| m8 | `check_figure_layout` | 重なり検査を `pass` に | KILLED — `test_bbox_overlap_is_a_failure`, `test_layout_failure_publishes_nothing` |
| m9 | constant cell の 0 検査 | 削除 | KILLED — `test_constant_cell_nonzero_is_rejected` |
| m10 | `official_certification is False` | 削除 | KILLED — `test_official_certification_true_is_rejected` |
| m11 | 族数 | `== 3` を `>= 3` に | KILLED — `test_family_count_mismatch_is_rejected` |
| m12 | raw_p 分母 2^18 整数性 | 削除 | KILLED — `test_raw_p_not_dyadic_is_rejected` |
| m13 | 登録 cell の曝露 | `>=` を `>` に (境界) または検査削除 | KILLED — `test_underexposed_registered_cell_is_rejected` |
| m14 | `_figure_number` | 正規表現を `fig?([0-9]*)_` に緩める | KILLED — `test_cli_rejects_prefix_without_fig_number` |

単一理由性の確認は author の報告 (§変異事前登録への対応) と probe の観測 node で行い、前後に同じ入力を拒否する層がある変異は分割または再照準する。
