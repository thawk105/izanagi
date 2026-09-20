# 段 2 plan (親起草、file:line 粒度) — [T-2793] fig8b (2026-09-20 07:25 JST)

行番号は worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2793-fig8b-cohort2` (= local main `b7f970dfa`) の現物。
`G` = `tools/plotting/plot_b10_static_tail_formal.py`、`T` = `orchestrator/tests/test_plot_b10_static_tail_formal.py`。

## 1. 生成器 `G` の変更

### 1.1 定数 (G:25-36)

- `SCHEMA` (:25) は v1 の値のまま残し、`SCHEMA_V2 = "izanagi-b10-static-tail-formal-figure-provenance/v2"` を足す。
- cohort 表を足す (順序が役割を固定する。CLI からは cohort 番号しか渡せず、役割・group id・path・pin は表の定数):
  ```python
  COHORTS = {
      1: {"role": "primary", "group_id": "b10-backoff-grid-20260915T061814Z-545445", "completed_jst": "2026-09-15",
          "report_dir": "group-report-20260915",
          "pinned_sha256": {json: "5f426ecb…", dat: "758b3121…", complete: "7192d1da…"},
          "results_document": "docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md"},
      2: {"role": "reproduction", "group_id": "b10-backoff-grid-20260919T131526Z-2235286", "completed_jst": "2026-09-19",
          "report_dir": "group-report-20260919-cohort2",
          "pinned_sha256": {json: "932f6ccc…", dat: "15b99944…", complete: "93421187…"},
          "results_document": "docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md"},
  }
  PRIMARY_COHORT = 1
  ```
  file 名は 3 file とも両 cohort で同じ (`t2500-backoff-static-tail-formal.{json,dat}` / `-complete.json`) なので
  `report_dir` + 固定 basename で組む。既存の `GROUP_ID` / `REPORT_JSON` / `REPORT_DAT` / `COMPLETE_JSON` / `PINNED_SHA256` は
  **cohort 1 の別名として残す** (T の `_fixture` / `_seal` / `test_pinned_hashes_are_used_when_no_override` が参照する。既存 test の期待値を
  変えない、DW-S05-B)。
- `CLAIM_BOUNDARY` (:47) は v1 のまま。v2 用に `CLAIM_BOUNDARY_V2 = {**CLAIM_BOUNDARY, "cohorts_pooled": False, "cohort_roles_fixed_in_generator": True,
  "primary_cohort_group_id": COHORTS[1]["group_id"], "reproduction_cohort_group_id": COHORTS[2]["group_id"]}`。
- `FIXED_WORDING` (:50) と `COMPARISON_WARNING` (:49) は不変。新規に
  `NOT_POOLED_WORDING = "The two cohorts are not pooled: no combined estimate, no combined verdict and no cross-cohort significance level are formed, and the closeness of the two cohorts' values is not evaluated as reproduction accuracy or agreement."`
  と `NO_REREAD_WORDING = "The second cohort returning the same aggregate verdict is reported as such and is not read as anything beyond the fixed wording above."` を定数にする。

### 1.2 loader (G:143-233)

- `_load_measurements(root, expected_hashes)` を `_load_measurements(root, expected_hashes, cohort)` にし、`GROUP_ID` / 3 path / `PINNED_SHA256` の
  参照 (:157-158, :167-168, :176, :193, :226-227) を `spec = COHORTS[cohort]` 由来に置き換える。`load_measurements(root, *, expected_hashes=None, cohort=1)`。
  返り値 dict に `"cohort": cohort`, `"role": spec["role"]`, `"completed_jst"`, `"results_document"` を足す (v1 の fig8 provenance には無い key だが、
  v1 の closure 検査 (:423-441) は artist / caption の射影しか見ないので影響なし)。
- `_validate_dat` (:126-141) は path を引数で受けているので不変。

### 1.3 図番号 (G:236-239)

- `re.match(r"fig([0-9]+[a-z]?)_", …)`。`fig8b_` → "8b"、`fig8_` → "8"、`figX_` は不変で拒否。

### 1.4 caption (G:242-267)

- 既存 `_caption(data, prefix)` は **byte 同一の出力を保つ** (fig8 v1 の再射影に使われる、:437)。
- 新設 `_caption_v2(prov_like, prefix)`: `prov_like["cohorts"]` (順序 primary, reproduction) から組む。文の順序:
  1. `Figure {n}. B-10 static-backoff right tail: primary result, formal cohort 1 of 2026-09-15 (group …; aggregate verdict …; preregistration commit cad6f46d8), and independent reproduction, cohort 2 of 2026-09-19 (group …; aggregate verdict …; preregistration commit 8737cacb4, same spec SHA-256); performance_certified: false for both cohorts.`
  2. `The upper block (two rows) draws cohort 1 and the lower block draws cohort 2; the blocks share nothing but the grid.` + fig8 と同じ列の説明と job id (cohort 別: `job IDs cohort 1: …; cohort 2: …`)。
  3. x 軸・上段・下段の説明 (fig8 の文をそのまま)。
  4. 区間分類: cohort 別に `{declining}/{n} intervals … L from … to …` を 2 文。
  5. `FIXED_WORDING` + "9999 us is not a physical limit." + `NO_REREAD_WORDING`。
  6. throughput 比: cohort 別 2 文。
  7. `NOT_POOLED_WORDING`。
  8. "This figure is a descriptive accounting …" (fig8 と同じ)。
  9. Conditions (fig8 と同じ)。
  10. Correctness: `all 120 records in each cohort (240 in total) were certified with 0 anomalies` — **合算件数は統計ではないが、プールと誤読されうるので
      "in each cohort" を主にし総数は書かない** (planner 判断: 書かない)。
  11. `COMPARISON_WARNING` + "Blocks use cohort-local y scales as well." の 1 文。
  12. fig2c / 探索走の除外 (fig8 と同じ 2 文)。
  13. `Cohort 1 is the primary result and cohort 2 is its independent reproduction; the primary result is not replaced by the reproduction (preregistration addendum of 2026-09-19).`
- 禁止語 (T:206 の list: "does not saturate", "no saturation point", "never saturates", "saturation-free", "saturates") を source にも caption にも入れない。
  "not pooled" の "pool" は禁止語でない。

### 1.5 artist / figure (G:270-345)

- `_artist_series(data)` は v1 のまま (fig8 再射影)。v2 用 `_artist_series_v2(prov_like)` = cohort ごとに `_artist_series(cohort_data)` を呼び、各 row に
  `"cohort": n, "role": role` を足して連結。
- `make_figure(data)` (:295) を内部関数 `_draw_block(fig, axes_rows, cohort_data, col_titles)` に分け、`make_figure(data)` は 1 block を描く現行と同じ出力
  (fig8 v1 の再生成用)。新設 `make_figure_v2(cohorts_data, prefix)`: `plt.subplots(4, 3, figsize=(7.2, 10.6))`、block ごとに `_draw_block`。block 見出しは
  `fig.text` で "Primary result — cohort 1 (2026-09-15, group …)" / "Independent reproduction — cohort 2 (2026-09-19, group …)" を各 block の上に置く
  (gid `block-title`)。凡例は上部 1 つ。`COMPARISON_WARNING` の脚注 + "cohort-local y scales" を下部に置く。
  `fig._b10_tail_caption = _caption_v2(…, prefix)`、`fig._b10_tail_artist_series = _artist_series_v2(…)`。
- `make_figure` (:342) の `_caption(data, "fig8_b10_static_tail_not_observed")` は現行どおり (v1 経路の副作用なし)。

### 1.6 layout check (G:356-388)

- `check_figure_layout(fig, axes)`: `len(plot_axes) != 6` (:362) を `len(plot_axes) not in (6, 12)` にし、`set(plot_axes) == set(fig.axes)` は維持。
  block-title の text は `text.axes is None` なので既存の重なり検査 (:376-381) に乗る。

### 1.7 provenance / closure (G:395-441)

- `build_provenance(data, outputs, argv, *, hash_paths=None, generated_utc=None)` は v1 のまま。新設 `build_provenance_v2(cohorts_data, outputs, argv, …)`:
  `{"schema": SCHEMA_V2, "cohorts": [{"role", "cohort", "completed_jst", "results_document", "external_root", "external_inputs", "group_id", "report",
  "preregistration", "campaigns", "measurement_conditions", "workloads", "correctness"} × 2], "claim_boundary": CLAIM_BOUNDARY_V2, "generated_utc",
  "generator", "outputs", "external_source_locator", "artist_series": _artist_series_v2, "caption": _caption_v2, "reproduction"}`。
- `validate_external_sources(provenance, root)` (:414-421): v2 では各 cohort の `external_inputs` を検査 (schema で分岐)。
- `validate_repo_closure(provenance, repo_root, *, expected_hashes=None)` (:423-441): 先頭で `schema` を見て v1 は現行本文そのまま、v2 は
  `_validate_repo_closure_v2` へ。v2 検査: generator path、`cohorts` が長さ 2 で `[c["cohort"] for c] == [1, 2]`、`[c["role"]] == ["primary", "reproduction"]`、
  各 cohort の `group_id` / `external_inputs` の path・kind・sha256 が `COHORTS[n]` と一致 (`expected_hashes` は `{1: {...}, 2: {...}}` の形で fixture 用)、
  `report["verdict"] == EXPECTED_VERDICT`、`report["performance_certified"] is False`、outputs 2 件の sha256、`artist_series == _artist_series_v2(prov)`、
  `caption == _caption_v2(prov, prefix)`、`claim_boundary == CLAIM_BOUNDARY_V2`、**`cohorts` の外に `workloads` / `statistics` / `mean` などの
  統計 key が無い** (top-level key 集合を固定集合と一致検査 → プール項の混入を構造で拒否)。

### 1.8 publish / CLI (G:444-500)

- `_publish_outputs(fig, axes, prefix, data, argv)` は provenance builder を引数化 (`build=build_provenance` 既定) して v2 でも使う。
- `main`: `parser.add_argument("--cohort", type=int, choices=(1, 2), default=1)`。`--cohort 1` → 現行経路 (`load_measurements(root, cohort=1)` →
  `make_figure` → v1 provenance)。`--cohort 2` → `[load_measurements(root, cohort=1), load_measurements(root, cohort=2)]` → `make_figure_v2` → v2 provenance。
  `expected_hashes` は v2 では `{1: …, 2: …}`。展開 argv (:496) に `--cohort <n>` を必ず含める (`--cohort 1` でも明示)。
  **`--cohort 1` の展開 argv が fig8 の provenance の `reproduction.argv` と変わる**が、それは新規生成時だけの話で、着地済み fig8 の provenance は不変
  (closure 検査は argv を見ない :423-441)。

## 2. test `T` の変更

### 2.1 fixture (T:33-107)

- `_seal(root, cohort=1)` / `_fixture(tmp_path, cohort=1, **overrides)`: `p.COHORTS[cohort]` の `report_dir` / `group_id` で path と campaign_path を組む。
  `_fixture_pair(tmp_path)` = 同じ root 直下に cohort 1 と 2 の dir を作り `{1: hashes1, 2: hashes2}` を返す。cohort 2 の fixture 値は cohort 1 と
  **意図的に少しずらす** (例: tps に +12345、aborts に +7) — 同一値だと「取り違え」を検出できない (F649 の型)。`preregistration_commit` も cohort 別
  ("c"*40 と "e"*40)。
- 既存 test 群 (:110-360) は `_fixture` の既定 cohort=1 で不変。

### 2.2 新 test (名前は案)

1. `test_two_cohort_figure_has_twelve_axes_two_blocks_and_passes_layout` — `make_figure_v2` で 12 axes、block-title 2 つ、`check_figure_layout` 通過、
   上 block の tail line の y が cohort 1 の値・下 block が cohort 2 の値 (取り違え検出)。
2. `test_cohort_roles_and_order_are_fixed_by_generator` — `COHORTS[1]["role"] == "primary"`, `COHORTS[2]["role"] == "reproduction"`; v2 provenance の
   `cohorts` 順序 [1, 2]; `validate_repo_closure` は順序を入れ替えた provenance を拒否 (phrase "cohort order")。
3. `test_v2_provenance_has_no_pooled_statistics` — top-level key 集合が固定集合と一致; `json.dumps(prov)` に `"pooled": true` 等が無い; 各 cohort の
   `workloads[].cells[]` が cohort 別の値。
4. `test_v2_caption_contains_both_cohorts_fixed_wording_and_not_pooled` — 両 group id、両 verdict、両 prereg commit の短縮、`FIXED_WORDING`、
   `NOT_POOLED_WORDING`、"performance_certified: false"、`COMPARISON_WARNING`、cohort 別 job id、"Figure 8b." で始まる (prefix `fig8b_test`)。
5. `test_caption_avoids_forbidden_saturation_claims` (既存 :203-208) を v2 caption にも当てる (既存 test を拡張するか新 test)。
6. `test_figure_number_accepts_letter_suffix` — `fig8b_x` → "8b"、`fig10_x` → "10"、`figX_x` 拒否、`fig8bb_x` 拒否。
7. `test_cohort2_pinned_hashes_match_cohort2_results_document` — `COHORTS[2]["pinned_sha256"]` と cohort2 稿 §4.1 の表の一致 (既存 :311-317 と同型、
   稿 path は `COHORTS[2]["results_document"]`)。既存 `test_pinned_input_hashes_match_results_document` は cohort 1 のまま。
8. `test_cli_cohort2_writes_three_outputs_and_v2_closure` — `main(["--measurement-root", root, "--cohort", "2", prefix], expected_hashes={1:…, 2:…})` == 0、
   3 成果物、`validate_repo_closure` 緑、artist / caption drift で拒否、`reproduction.argv` に `--cohort 2`。
9. `test_cli_rejects_unknown_cohort` — `--cohort 3` は argparse で rc≠0 (SystemExit 2)、成果物ゼロ。
10. `test_v1_closure_unchanged_for_landed_fig8` — 既存 `test_landed_fig8_repo_closure_and_caption_when_present` (:369-378) はそのまま。
11. `test_landed_fig8b_repo_closure_and_caption_when_present` — fig8b の着地 bundle (prefix `docs/paper-story/figures/fig8b_b10_static_tail_cohort2`)、
    `validate_repo_closure` (v2) 緑、caption が README に収録、**fig8 の caption も README に残っている**。
12. `test_real_root_loads_cohort2_and_matches_results_document_when_present` — 実 root で cohort 2 を読み、verdict / 24 cell / 992686.2 / 比 0.445 0.484 0.398 と
    稿 §2.3 の文字列一致 (既存 :354-366 と同型)。
13. 負例: v2 の `validate_repo_closure` が `claim_boundary["cohorts_pooled"] = True` を拒否; cohort 2 の group id を cohort 1 の値にした provenance を拒否;
    `_load_measurements(cohort=2)` で verdict 不一致・pin 不一致を拒否 (既存 fixture 経路の再利用)。

### 2.3 自走 harness (T:381-404)

- 不変 (新 test は `test_` prefix で自動収集)。

## 3. 親の作業 (実装面でない)

1. fig8b 生成 (login node、worktree の統合後):
   `python3 tools/plotting/plot_b10_static_tail_formal.py --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal --cohort 2 docs/paper-story/figures/fig8b_b10_static_tail_cohort2`
   → 3 成果物。`--cohort 1` を一時 prefix (job dir) にも走らせ、値・caption が fig8 provenance と一致することを実測 (bytes は一致しない: 規律 7)。
   PNG を目視 (Read tool) し、block 見出し・凡例・脚注の可読性を確認。
2. `docs/paper-story/figures/README.md`: 一覧 (:12-27) に fig8b 行 (fig8 行の直後)、fig8 節末尾 (:819 の前) に「後継図 fig8b」の 1 段落、
   fig8b 節 (fig9 見出し :821 の前に挿入)。fig8b 節の caption 正文は provenance の `caption` を貼る。
3. `tools/plotting/README.md` (:137-146): `--cohort 2` の例と契約 1〜2 行。
4. 変異 matrix (段 4 で事前登録、段 6 で probe → final)、焦点走、受入、fragment、insight。

## 4. 未決 (段 3 で攻撃してほしい点)

- (Q1) 4 行 × 3 列 (7.2 × 10.6 in) は論文の 1 ページに収まるか。重ね描き案の方が読みやすいか (FIGURE_CONVENTIONS §4 と「一致度を評価しない」との整合)。
- (Q2) 直接ラベル "6/6 intervals declining / min L = …" を両 block に置くと 12 panel 中 6 panel に text が入る。layout check の重なりリスク。
- (Q3) caption の長さ (fig8 の約 1.6 倍) は許容か。README に収録する正文と同一文字列である必要があるので、長さの上限は無いが可読性。
- (Q4) v1 の `_caption` / `_artist_series` / `validate_repo_closure` の byte 同一性をどの test が守るか (既存 :369-378 の着地 test が守る。加えて
  「fig8 provenance を読んで `_caption` を再投影すると `caption` と一致」は同 test に含まれる)。
- (Q5) `COHORTS[2]["results_document"]` の稿 path を生成器が持つのは自己参照か (稿は生成器の hash を持たないので循環しない、F36)。
- (Q6) cohort 2 の完走日 "2026-09-19" と cohort 1 の "2026-09-15" を定数で持つ根拠は各稿 §1 / 集団報告の `completion.started_epoch` のどちらか
  (fig8 の caption は "formal cohort of 2026-09-15" を定数で持つ :250)。
