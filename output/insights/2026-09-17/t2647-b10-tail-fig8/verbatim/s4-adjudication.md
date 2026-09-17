# 段 4 裁定 — [T-2647] fig8 (B-10 右 tail 09-15 cohort の記述図)

段 2/3 は省いた (設計は正本 `docs/paper-story/2026-09-17.md` §4 の予定仕様と brief で file 粒度まで確定、1563 wave と同型)。
独立の敵対検証は段 6 のレビュー 2 本 (レンズ A: caption・claim 範囲・規律 2/7・事前登録 §4.5 の固定表現、レンズ B: 数値・pin・fixture 実寸・fail-closed) で行う。
brief の (P1)〜(P6) はそのまま採用し、以下で実装仕様に落とす。

## §1 scope の確定

- 実装面 (Codex author が書く): `tools/plotting/plot_b10_static_tail_formal.py` (新規)、`orchestrator/tests/test_plot_b10_static_tail_formal.py` (新規)。他の file は触らない。
- 親が行う: 実データでの生成 (login node)、3 成果物の `docs/paper-story/figures/` への配置、`docs/paper-story/figures/README.md` (一覧 1 行 + fig8 節)、`tools/plotting/README.md` (command 例)、commit。
- 触らない: 既存 7 図の bytes・provenance、`plot_a2_certification.py` / `plot_b10_extended_backoff.py` / `plot_backoff.py` / `FIGURE_CONVENTIONS.md`、`docs/paper-story/README.md`、版 (`2026-09-17.md`)、`docs/paper-story-backoff/**`、`docs/b10-backoff-static-tail-preregistration.md`、results 稿。gate・台帳・一般化の新設なし。

## §2 plan v2 — 生成器 `tools/plotting/plot_b10_static_tail_formal.py`

依存: 標準 lib + numpy + matplotlib (`Agg`)。`tools/plotting/plot_backoff.py` 等の既存生成器を import しない (自己完結、F812 系の pin 連鎖を作らない)。雛形は `plot_a2_certification.py` (external_inputs・`fig<N>_` 導出・`_publish_outputs` の tmp→rename・`check_figure_layout`・`validate_repo_closure`・`main(expected_hashes=)` seam) と `plot_b10_extended_backoff.py` (`_validate_text_bboxes`・claim boundary・workload-local y)。

### 2.1 定数 (repo 所有 pin 表。CLI から渡せない)

- `SCHEMA = "izanagi-b10-static-tail-formal-figure-provenance/v1"`
- `GROUP_ID = "b10-backoff-grid-20260915T061814Z-545445"`
- `REPORT_SCHEMA = "t2500-backoff-static-tail-formal-report/v1"`、`RUN_KIND = "t2500-tail-formal"`
- `EXPECTED_VERDICT = "not-observed-in-any-workload"` (JSON と一致しなければ拒否。verdict は再計算しない)
- `DEFAULT_ROOT = Path("/work/1/SFC/tanab/b10-backoff-grid-t2500-formal")`、root 相対 path 3 本は `group-report-20260915/t2500-backoff-static-tail-formal.json` / `.dat` / `-complete.json`
- `PINNED_SHA256 = {json: "5f426ecbc16132048cf0c73eaf6960a395ec821a9f48cc04a83a787dceec8b28", dat: "758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44", complete: "7192d1da0b4a032251a0e270ec60910a118a5f75844dc9276a6fba00a682d08c"}`
- `WORKLOADS = ("write-heavy", "balanced", "read-heavy")`、`RRATIOS = {5, 50, 95}`、`TAIL_GRID_US = (1250, 1768, 2500, 3535, 5000, 7070, 9999)`、`BOUNDARY_REFERENCE_US = 1000`、`GRID_US = (1000,) + TAIL_GRID_US`
- `REPS_PER_CELL = 5`、`T95_DF4 = 2.7764451051977987`
- `CLAIM_BOUNDARY = {"claim_scope": "descriptive_backoff_tail_cost_only", "performance_certified": False, "source_measurement": "trace_disabled", "mechanism_claim": False, "adoption_decision": False, "saturation_wording": "not-observed-within-representable-range"}`
- `COMPARISON_WARNING` (fig2c と同文: "Panel heights and slopes use workload-local y scales and must not be compared across panels.")
- `FIXED_WORDING = "Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding."` (事前登録 §4.5 の固定表現の英訳。これ以外の言い方 — "does not saturate" / "no saturation point" / "saturation-free" / "never saturates" — は生成器にも caption にも書かない)

### 2.2 load (`load_measurements(root, *, expected_hashes=None) -> dict`)

fail-closed (`FigureDataError` 系の例外、CLI は rc=2 で 3 成果物を出さない)。順序:

1. 3 file の実在と SHA-256 が `expected_hashes` (None なら `PINNED_SHA256`) と一致。`-complete.json.artifacts` の json/dat の値も同じ値であること。
2. JSON top-level: `schema_version == REPORT_SCHEMA`、`run_kind == RUN_KIND`、`verdict == EXPECTED_VERDICT`、`performance_certified is False` (True・欠落・非 bool は拒否)、`failures == []`、`spec_sha256` が `-complete.json.spec_sha256` と一致。
3. `campaigns[]` は 3 件で `workload` が `WORKLOADS` 順。各 campaign: `admission.admission_status` が `admitted` または `admitted-new-schema`、`campaign_path` に `/{GROUP_ID}-{workload}/campaigns/` を含む (group id の data 束縛)、`identity.threads == 48`、`records == 1000000`、`extime_s == 3`、`workload_coordinates.ycsb_rratio` が workload の rratio、`ycsb_zipf_skew == "0.9"`、`ycsb_rmw == "0"`、`ycsb_max_ope == "10"`、`identity.grid` の `backoff_us` 集合 == `GRID_US` 集合、`performance_reps_per_cell == 5`、`build_admission.repo_stock_pin == "511c953"`。`completion.status == "complete"`、`completion.campaign_lock_sha256 == campaign_lock_digest`、`completion.wal_sha256`・`scheduler.job_id` を記録用に取る。
4. `points[]` は 8 件で `backoff_us` 集合 == `GRID_US` (順は測定順なので集合比較。重複は拒否)。各 point: `use_perf is False`、`reps[]` 5 件 (rep_index 0..4 が揃う)、各 rep の `abort_counts_` / `commit_counts_` は正整数、`throughput_tps` は正の有限数、`abort_rate_recomputed == aborts/(aborts+commits)` (相対 1e-12)、`tps[]` と `reps[].throughput_tps` が順序込みで一致、`correctness[]` 5 件すべて `payload.certified is True` かつ `payload.anomalies == 0` (規律 2: 未認証の記録を含む cohort は描かない)。
5. `.dat`: 1 行ヘッダ `# workload backoff_us rep aborts commits abort_rate throughput_tps` + 120 行。(workload, backoff_us, rep) が JSON の reps と 1:1 で、aborts / commits / throughput_tps が一致し、`abort_rate` 列が `aborts/(aborts+commits)` と一致 (相対 1e-12)。行数 120 でなければ拒否。
6. `workloads[]` は 3 件 `WORKLOADS` 順。各: `state`、`saturation_location`、`local_flat_intervals`、`intervals[]` 6 件で `(left_us, right_us)` が `TAIL_GRID_US` の隣接対を順に覆う (1000 を含む区間があれば拒否)、各 interval の `state` ∈ {declining, saturated, indeterminate}、`qhat`/`qL`/`qU`/`L`/`U`/`U_flat` が有限数。**state・qhat・L・U は JSON からコピーし再計算しない。** 一致検査だけ: `L == 1 − 2**qU`、`U == 1 − 2**qL` (絶対 1e-9)。`statistics[<backoff>]` の `throughput_tps_mean`・`mean` (abort 率) と再計算値が相対 1e-9 で一致、`gate_passed is True`。
7. 再計算 (図の値の出所): 各 cell で `tps_mean`、`tps_sd` (ddof=1)、`tps_ci95_half = T95_DF4 * sd / sqrt(5)`、`abort_rates[]` (整数カウンタから全精度)、`abort_mean`、`abort_ci95_half`、`tps_cv`、`abort_cv`。tail 端の比 `tps_mean[9999] / tps_mean[1250]` を workload ごとに (caption 用)。

戻り値 (`data`) は provenance にそのまま入る dict 群: `external_root`、`external_inputs` (3 行: kind ∈ {group-report-json, group-report-dat, completion-record}、root 相対 path、sha256)、`group_id`、`report` (schema_version, run_kind, verdict, performance_certified, spec_sha256, failures)、`preregistration` (commit, document_blob_sha256 — `-complete.json.preregistrations[]` が 3 件同値であること)、`campaigns[]` (workload, campaign_id, campaign_lock_digest, wal_sha256, job_id, admission_status, host は無ければ省く)、`measurement_conditions`、`workloads[]` (state, saturation_location, local_flat_intervals, intervals[] コピー, cells[] 再計算値 + 生値)、`correctness` (records=120, certified=120, anomalies=0)、`claim_boundary`。

### 2.3 図 (`make_figure(data) -> (fig, axes)`)

- 2 行 × 3 列、列 = workload (`WORKLOADS` 順)、`figsize` は横 7.2 in 前後 (2 段組 1 行幅の論文図)、`constrained_layout` か `tight_layout`。
- x: log scale、tick は 8 点の値 (`1000, 1250, 1768, 2500, 3535, 5000, 7070, 9999`、表示は整数。重なるなら 45° 回転)。minor tick は消す。x label は下段だけ "fixed static backoff (us)"。
- 上段: `tps_mean / 1e6` を線 + 塗り marker で tail 7 点、境界参照 1000 は中抜き marker (同色、線で結ばない。gid `boundary-reference`)。誤差棒 = `tps_ci95_half / 1e6`。y label (左端だけ) "throughput (M tps)"。
- 下段: `abort_mean` (fraction、y label "abort rate")、誤差棒 `abort_ci95_half`。tail の隣接点を結ぶ線分は interval の `state` で描き分ける (declining = 実線・系列色、saturated = 太線・別色、indeterminate = 点線・灰色。凡例は図中に 1 度、実際に現れる state だけ)。1000→1250 は結ばない (interval 集合外)。panel 内に direct label (gid `direct-label`) "6/6 intervals declining\nL >= <min L, 小数 3 桁>" (state 件数と min L は JSON コピー値から)。すべて declining でなければ "<n>/6 declining, <m> saturated, <k> indeterminate" と件数を出す。
- 列見出し: "write-heavy (rr5)" 等。y 軸は workload-local (共有しない)。
- `fig._b10_tail_caption` と `fig._b10_tail_artist_series` を属性に持たせる (test が読む)。
- 保存前に `check_figure_layout(fig, axes)` (a2 型: renderer-backed、text の figure 逸脱・隣 panel 侵入・bbox 重なり・axis decoration 逸脱で `FigureLayoutError`。plot axes 6 本以外の axes (colorbar 等) が無いことも検査)。

### 2.4 caption (`_caption(data, prefix) -> str`、英文、決定的)

図番号は prefix `fig<N>_` から導く。必ず含める (順序も固定):
1. "Figure <N>. B-10 static-backoff right tail, formal cohort of 2026-09-15 (group <GROUP_ID>; aggregate verdict <verdict>; performance_certified: false)."
2. 3 列の説明 (workload と rr)、各 workload が独立 campaign であること、job id 3 つ (`0:998865.nqsv` 等は JSON から)。
3. x 軸: tail 7 点 (塗り) と境界参照 1000 (中抜き、同一 job 内で測るが interval 集合に入らない)。
4. 上段: 5 反復 trace-disabled の平均と t 分布 95% CI (誤差棒)。"M tps means million transactions per second."
5. 下段: abort 率は rep ごとに整数カウンタから `aborts / (aborts + commits)` で再計算し、5 反復の平均と同じ CI。
6. 区間: "Segments between adjacent tail points are colored by the interval state copied from the group report: <18>/18 intervals (6 per workload) are declining; simultaneous lower bounds L on the per-doubling decrease range from <min L> to <max L> (Bonferroni over 36 one-sided limits, familywise 0.05)." 件数と L は JSON コピー値から書式化 (小数 4 桁)。
7. `FIXED_WORDING` を逐語で。続けて "9999 us is not a physical limit."
8. 費用: "From 1250 to 9999 us the mean throughput falls to <r_wh>, <r_bal> and <r_rh> of its 1250 us value (write-heavy, balanced, read-heavy) while the abort rate keeps decreasing." (比は再計算、小数 3 桁)。"This figure is a descriptive accounting of that cost; it makes no mechanism claim and no adoption decision."
9. 条件: "Conditions: 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, 5 repetitions, silo, CCBench pin 511c953, no perf, trace-disabled performance." 正しさ: "Correctness comes from separate trace-enabled runs under the recorded legacy check configuration, not the performance configuration: all 120 records were certified with 0 anomalies, and this is not a performance certification."
10. `COMPARISON_WARNING` を逐語で。
11. "This cohort is a different grid and a different cohort from fig2c and is not a continuation of it."

禁止: "does not saturate" / "no saturation point" / "never saturates" / "saturation-free" / "saturates" を含まない (test が負例で検査。生成器側に自分の caption を検査する恒真 gate は置かない)。

### 2.5 provenance と閉包

- `build_provenance(data, outputs, argv, *, hash_paths=None, generated_utc=None)`: `schema`、`generated_utc`、`generator {path, sha256}` (生成時記録、live pin ではない)、`outputs[{path, sha256}]` (png, pdf)、`external_source_locator {root_at_generation, validation_key: "root-relative-path-plus-sha256"}`、`external_inputs`、`group_id`、`report`、`preregistration`、`campaigns`、`measurement_conditions`、`workloads`、`correctness`、`claim_boundary`、`artist_series` (`_artist_series(data)` から決定的に)、`caption`、`reproduction {cwd: "repository-root", argv, command}`。argv は repo 相対 (prefix) と絶対 (root)。
- `validate_external_sources(provenance, root)`: external_inputs の各 path を root 相対で読み SHA-256 一致。
- `validate_repo_closure(provenance, repo_root)`: schema・generator path・outputs の SHA-256 が着地 file と一致・`external_inputs` の path/sha が `PINNED_SHA256` と一致・`artist_series == _artist_series(provenance)`・`caption == _caption(provenance, prefix)`。
- `_publish_outputs`: a2 型 (layout check → tmp に png/pdf → provenance → tmp → `os.replace`)。失敗時は tmp を消し成果物を出さない。
- CLI: `main(argv=None, *, expected_hashes=None) -> int`。引数 `--measurement-root PATH` (既定 `IZANAGI_B10_TAIL_MEASUREMENT_ROOT` → `DEFAULT_ROOT`) と `out_prefix`。prefix が `fig<N>_` で始まらなければ rc=2。成功時 "wrote <prefix>.png / .pdf / .provenance.json"。

## §3 test `orchestrator/tests/test_plot_b10_static_tail_formal.py`

`_run()` 自走 harness (末尾 `if __name__ == "__main__": sys.exit(_run())`、pytest fixture は `tmp_path` だけ、`_run` が tempfile で注入)。allowlist に載せない。parametrize id は ASCII。

- 実寸 fixture builder `_fixture(tmp_path, **overrides)`: 3 workload × 8 点 × 5 反復の合成 JSON (schema・verdict・campaigns・identity・points・reps・correctness・workloads.intervals 6 件・statistics) + `.dat` 120 行 + `-complete.json` を書き、`expected_hashes` を実 SHA-256 で返す。値は実測値でなくてよいが、`statistics` は fixture の reps から同じ式で計算して入れる (孫引きしない)。既定はすべて `declining`。
- 正例: `test_fixture_has_production_shape_and_recomputes_statistics` (24 cell、CI = T95 * sd/√5、比の値)。
- 図: `test_artist_series_have_exact_x_and_boundary_reference_is_separate` (tail 7 点の x と 1000 の中抜き marker が別 artist)、`test_interval_states_are_copied_not_recomputed` (fixture の 1 区間を `indeterminate` にし L > 0.05 のままでも direct label と provenance が `indeterminate` を写す)、`test_real_figure_passes_layout_check` (実寸 fixture から本物の Figure を `check_figure_layout` へ通す)、`test_bbox_overlap_is_a_failure` (本物の Figure に text を足して重ねると `FigureLayoutError`)。
- caption: `test_caption_contains_fixed_expression_and_certification_literal` (`FIXED_WORDING` と "performance_certified: false" と group id と `COMPARISON_WARNING` を含む)、`test_caption_avoids_forbidden_saturation_claims` (禁止句 5 種を含まない)、`test_caption_figure_number_comes_from_prefix` (`fig8_`→"Figure 8."、`fig9_`→"Figure 9."、`figX_`→拒否)。
- 負例 (すべて `FigureDataError` 系を期待): `test_external_input_hash_drift_is_rejected`、`test_pinned_hashes_are_used_when_no_override` (expected_hashes 省略で fixture は pin 不一致により拒否)、`test_performance_certified_true_is_rejected`、`test_verdict_mismatch_is_rejected`、`test_dat_with_missing_row_is_rejected`、`test_dat_abort_rate_disagreeing_with_counters_is_rejected`、`test_boundary_reference_inside_interval_set_is_rejected` (interval に `left_us=1000` を入れる)、`test_uncertified_correctness_record_is_rejected` (1 記録の `certified=false`)、`test_group_id_absent_from_campaign_path_is_rejected`、`test_statistics_mismatch_is_rejected`。
- pin: `test_pinned_input_hashes_match_results_document` (生成器の `PINNED_SHA256` 3 値が `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` §4.1 の表の該当行の値と一致。md を path で grep して取る)。
- CLI: `test_cli_writes_three_outputs_and_provenance_closure` (fixture で `main()` rc=0、3 成果物、`validate_external_sources` と `validate_repo_closure` が通る、`reproduction.argv` が展開済み)、`test_cli_rejects_prefix_without_fig_number`。
- 実データ: `test_real_root_loads_and_matches_results_document_when_present` (`DEFAULT_ROOT` 不在なら skip、あれば verdict・24 cell・write-heavy 1000 の tps_mean == 993106.4・比 0.444/0.481/0.400 (小数 3 桁))。
- 着地: `test_landed_fig8_repo_closure_and_caption_when_present` (3 file と README の `fig8_b10_static_tail_not_observed` がともに無ければ skip、あれば `validate_repo_closure` + caption ⊂ README)。

## §4 変異 matrix の事前登録 (位置は実装後に anchor を確定、DW-M07)

| id | 位置 (生成器) | 変異 | 期待 | 単独で殺す test (予想) |
|---|---|---|---|---|
| M0 | module docstring | comment だけ変更 (等価対照) | SURVIVED | — |
| M1 | `PINNED_SHA256` の dat 値 | 1 文字変更 | KILLED | `test_pinned_input_hashes_match_results_document` |
| M2 | load 手順 2 | `performance_certified is False` 検査を除去 | KILLED | `test_performance_certified_true_is_rejected` |
| M3 | load 手順 5 | dat `abort_rate` 列と整数カウンタの一致検査を除去 | KILLED | `test_dat_abort_rate_disagreeing_with_counters_is_rejected` |
| M4 | `_artist_series` / 上段描画 | 境界参照 1000 を tail 系列に含める | KILLED | `test_artist_series_have_exact_x_and_boundary_reference_is_separate` |
| M5 | `_caption` 項 1 | "performance_certified: false" を落とす | KILLED | `test_caption_contains_fixed_expression_and_certification_literal` |
| M6 | `FIXED_WORDING` | "saturation was not observed" → "the abort rate does not saturate" | KILLED | `test_caption_avoids_forbidden_saturation_claims` (+ 上の test) |
| M7 | load 手順 6 | interval `state` を `L > 0.05` から再計算して上書き | KILLED | `test_interval_states_are_copied_not_recomputed` |
| M8 | `T95_DF4` | 1.96 に変更 | KILLED | `test_fixture_has_production_shape_and_recomputes_statistics` |
| M9 | `check_figure_layout` | 先頭で `return` | KILLED | `test_bbox_overlap_is_a_failure` |
| M10 | load 手順 5 | 行数 120 の検査を除去 | KILLED | `test_dat_with_missing_row_is_rejected` |
| M11 | load 手順 1 | SHA-256 比較を除去 (実在検査だけ残す) | KILLED | `test_external_input_hash_drift_is_rejected`, `test_pinned_hashes_are_used_when_no_override` |
| M12 | load 手順 4 | `certified is True` 検査を除去 | KILLED | `test_uncertified_correctness_record_is_rejected` |

各変異の赤理由が一つに絞れることは実装後に anchor と一緒に確認する (F820)。dat 行数 (M10) と dat/JSON 対応 (M3) は別の検査に分けて書き、過剰決定を避ける。

## §5 受理集合 (契約)

受理: §2.2 の 1〜7 をすべて満たす 3 file。拒否: いずれかの不一致・欠落・型違い・非有限数・`performance_certified` が False 以外・未認証記録・interval 集合に 1000・dat 行数 ≠ 120・prefix が `fig<N>_` でない。正例は実データ 3 file (親が実走)。
