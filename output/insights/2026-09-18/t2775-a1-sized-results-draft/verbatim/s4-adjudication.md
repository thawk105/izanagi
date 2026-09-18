# 段 4 裁定 — A-1 sized attempt-0001 の単独 results 稿と fig9 (親、2026-09-18)

段 2・3 は省略 (brief (P5))。裁定 inbox の再走査 (14:5x JST): 本題に関わる新しい裁定なし (`2026-09-18-t2724-…` の「A-1」は設計案ラベルで別物、
`2026-09-18-acceptance-gate-no-canonical-source-manager-thread.md` は受入投入の門番契約 → 段 9 で適用)。
brief の (P1)〜(P5) は provisional のまま採用し、段 6 のレビュー 2 本の攻撃対象にする。プラン v2 = brief の「成果物の形」。

## 1. 親が書く docs

- 稿 `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`。
- `docs/paper-story/README.md`: results 表 1 行 + stale 注記 A-1 項の末尾へ 1 行。
- `docs/paper-story/figures/README.md`: 一覧 1 行 + fig9 節 (何を示す図か / 既存図との関係 / 入力 / 再現 / 作図規約への適合 / キャプション正文 / proof chain)。
- `tools/plotting/README.md`: fig9 の command example 節。
- insight `output/insights/2026-09-18/t2775-a1-sized-results-draft/` (README.md + verbatim/)、spool fragment (worklog 1、failures 1)。

## 2. 生成器 `tools/plotting/plot_a1_sized_paired.py` (Codex author)

### 2.1 定数

- `SCHEMA = "izanagi-a1-sized-paired-figure-provenance/v1"`、`GENERATOR_PATH = "tools/plotting/plot_a1_sized_paired.py"`。
- `STUDY_ID = "paper-story-a1-20260901-balanced5-sized-v1"`、`RESULT_SCHEMA = "paper-story-a1-paired-result/v3"`、
  `RECEIPT_SCHEMA = "paper-story-a1-paired-receipt/v3"`、`COMPLETE_SCHEMA = "paper-story-a1-paired-materialization-complete/v1"`、
  `PAIRING_DESIGN = "balanced-a5b5-b5a5-v1"`、`CONTRAST = "variant-minus-baseline"`。
- `LEAF_DIR = "output/insights/2026-09-13/paper-story-a1-balanced5-sized"` (repo 相対、tracked)、file 3 本 `result.json` / `receipt.json` / `.complete.json`。
- `POLICY_PATH = "orchestrator/campaign/paper_story_a1_paired.v3-sized.json"` (repo 相対、tracked)。
- `PINNED_SHA256` = {result.json: `372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0`, receipt.json: `a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930`,
  .complete.json: `0b1f177944f6cab5c5eed5aa94a34beda11a06fcd8e94c1018d35c4e5e212a1e`, policy: `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`}。**CLI から渡せない。** test は `expected_hashes` 注入 seam を使う。
- `WORKLOADS = ("write-heavy", "balanced", "read-heavy")`、`RRATIOS = {"write-heavy": 5, "balanced": 50, "read-heavy": 95}`、
  `VARIANT_ARMS = {"write-heavy": "fixed10", "balanced": "fixed5", "read-heavy": "fixed2"}`、`BASELINE_ARM = "no-backoff"`、`REPS = 30`、`DF = 29`、`FLOOR_FRACTION = 0.03`。
- `CAPTION_SOURCE = "docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md"` (provenance `tracked_inputs` に `kind: "caption_source"`、path + sha256、
  `authority_scope: "wording of limitations and conditions only; not measurement values or classification"`)。file 不在なら生成を拒否する。
- `COMPARISON_WARNING = "Panel y scales are workload-local and must not be compared across panels."`
- 固定の限定句 (逐語で caption に入れる、test が literal を検査): `FIXED_LANE = "formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only"`、
  `FIXED_SCOPE = "This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts."`

### 2.2 読み込みと検査 (`load_leaf(repo_root, *, expected_hashes=None)`) — 拒否は例外 (`FigureDataError`) で rc 非 0

1. 3 file + policy の sha256 を pin 表 (または注入) と照合。`.complete.json` の `files` map の 3 値 (README.md / receipt.json / result.json) を現物と照合、`schema_version` 一致。
2. result.json: `schema_version` / `study_id` / `pairing_design` / `complete=true` / `all_workloads_terminal=true` / `formal=false` / `promotion_prohibited=true` /
   `measurement_error=None` / `policy_sha256 == policy file sha256` / `workload_reps` が 3 workload とも 30 / `workloads` が定数順の 3 件。
3. receipt.json: `schema_version` / `study_id` / `formal=false` / `promotion_prohibited=true` / `policy.sha256 == policy_sha256` / `job_executions` 3 件 (workload・request_id・host を cells に写す)。
4. policy: `authority` が {formal false, promotion_prohibited true, result_authority sized-preregistered-descriptive-only}、`workloads[]` の `name` 順・`reps` 30・`df` 29・`k` (文字列) を float 化して result の `statistics.k` と一致、`planned_sigma_tps` 一致、arm 名と role 一致。
5. 各 workload: `valid=true`、`errors=[]`、`terminal_result.status == "valid"`、`statistics.n == 30`、`df == 29`、`contrast`・`pairing_design`・`floor_fraction == 0.03`、`pairs` が 30 件で `pair_index` 0..29 の順、
   各 pair で `signed_difference_tps == <variant>_tps − no-backoff_tps` (完全一致)、`pairs[i].<arm>_tps == arms.<arm>.raw_tps[i]`、両 arm `expected_reps == observed_reps == 30`、`actual_rounds == 1`、`attempt_count == 1`、
   `unstable=false`、`valid=true`、`errors=[]`、genome 文字列が定数 flag と一致 (`BACKOFF_FIXED=<N>,BACK_OFF=1` / `BACKOFF_FIXED=-1,BACK_OFF=0`)。
6. **統計は再計算して fail-closed 照合、分類は記録値をコピーして述語で検算:** `mean = fmean(diff)`、`variance = Σ(d−mean)²/(n−1)`、`sd = sqrt(variance)`、`h = k·sd/√n`、`baseline_mean = fmean(baseline raw_tps)`、
   `B = 0.03·baseline_mean`、区間 `[mean−h, mean+h]` を `statistics` の各 field と照合 (相対 1e-9 または絶対 1e-6 tps)。分類は `classification` をコピーし、述語 (`abs(mean) − h > B` → resolved-above-floor / `abs(mean) + h ≤ B` → bounded-below-floor / else unresolved) と一致しなければ拒否。
   `variance_plan_breach == (sd > planned_sigma_tps)` を検算し、true なら拒否 (本 attempt は 3 本とも false。true の図は本生成器の射程外)。
7. **規律 2:** 両 arm `correctness_evidence.certified == [True]`、`verify_configs == ["legacy"]`、`verify_done_frames` 1 件。1 つでも違えば拒否。caption に "not a performance certification" を残す。
8. perf 名 (`use_perf`、`perf_*`) の変数で分岐しない (`orchestrator/tests/test_official_perf_closure.py` が tools/ の .py を走査する)。`performance_trace0_evidence` は読まない。

### 2.3 図 (`make_figure(data)`)

- 1 行 × 3 列 (write-heavy / balanced / read-heavy)、workload-local の y。x = pair index 0..29 (整数目盛、5 刻み)、y = paired difference (variant − baseline) in M tps (`/1e6`)。
- 各 panel: 30 対の差 (open marker、線で結ばない)、対差平均の水平実線とその上下 ±h の帯 (半透明)、0 の水平実線 (細)、±B の水平破線 2 本。y 範囲は 0・±B・全点を含めて余白 8%。
- panel 題は `write-heavy (rr5): fixed10 - no-backoff` の形 (workload 名と対比を書く)、直接ラベルまたは 1 箇所の凡例 (mean ± h / ±B floor / zero / pairs)。内部識別子 (campaign id・variant hash) は図中に出さない。
- 図の sup-title は無し。subtitle 相当の測定条件 (48 threads, 1,000,000 records, Zipf 0.9, 3 s × 30 pairs, silo, pin 511c953) は caption に置く (§6)。
- 保存前に renderer-backed layout check (`check_figure_layout`: text bbox の重なり・figure 外への逸脱で `FigureLayoutError`)。赤なら 3 成果物を 1 つも出さない (tmp → `os.replace`、失敗時 tmp 削除)。
- 出力 prefix は `fig<N>_` 必須 (`_figure_number`)、PNG + PDF + `.provenance.json`。

### 2.4 caption (英文、決定的に組み立て、値は data から書式化。項の順序固定)

1. `Figure <N>. A-1 balanced five-rep paired comparison, sized run attempt-0001 (study <STUDY_ID>; <FIXED_LANE>).`
2. Columns: write-heavy (rr5, fixed10 minus no-backoff), balanced (rr50, fixed5 minus no-backoff), read-heavy (rr95, fixed2 minus no-backoff), each an independent campaign in its own job (job IDs, respectively: 4939.nqsv, 4940.nqsv, 4941.nqsv; hosts bnode107, bnode108, bnode109) — 値は receipt の `job_executions` から。
3. What is drawn: 30 paired differences (variant minus baseline, one per pair index under the balanced five-rep schedule, ten-pair groups in the order A^5 B^5 B^5 A^5 or B^5 A^5 A^5 B^5) as open markers; the arithmetic mean as a solid line with the registered interval mean ± h, h = k·s/√n, k = <k> (t quantile at 1 − (1/120)/2 with df 29), s the sample standard deviation of the 30 differences; the zero line; and the registered floor boundary ±B, B = 3 % of the baseline-arm mean, as dashed lines. M tps means million transactions per second.
4. Values: per workload `mean <+/-x.xxx> M tps (h <x.xxx> M, B <x.xxx> M, baseline mean <x.xxx> M)`; then `The registered classification is resolved-above-floor in all three workloads (sign positive, positive and negative, respectively); variance_plan_breach is false in all three.` — 分類語と符号は data から。
5. `The interval and the classification are the descriptive outputs of the preregistered rule; they are not a hypothesis test and are not a performance certification.`
6. `<FIXED_SCOPE>`
7. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s per repetition, 30 pairs per workload, silo, CCBench pin 511c953, measurement source commit d2ebef7a4, no perf, trace-disabled performance. (pin と commit は result.json / policy から取る: `ccbench_acceptance.canonical_pin` の先頭 7 桁、`source_binding.measurement_source_commit` の先頭 9 桁)
8. `Correctness comes from separate trace-enabled verify runs under the recorded legacy check configuration, not the performance configuration: all 6 arms are recorded as certified (result.json correctness_evidence, verify_done frames bound by SHA-256); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification.` (anomaly 数は WAL にあり result.json には無いので caption には書かない。稿が WAL から書く)
9. `<COMPARISON_WARNING>`
10. `Pilot observations did not enter the estimate; the estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state effect.` (result.json `limitations` の 1・2 項の言い換え。逐語は稿が持つ)

禁止語 (test が検査、生成器の文字列にも入れない): `headline result`, `reproduces C1`, `reproduction of C1 confirmed`, `statistically significant`, `significant improvement`, `significant regression`, `certified performance`, `performance certified`, `A-1 is satisfied`, `formal result`。
("improvement" / "regression" の単語は caption に書かない。向きは "sign positive / negative" で言う。)

### 2.5 provenance (`build_provenance`)

`schema`、`generated_utc`、`generator {path, sha256}`、`outputs[] {path, sha256}`、`tracked_inputs[]` (leaf 3 file + policy + caption_source、各 path と sha256、kind)、
`study_id`、`measurement_source_commit`、`ccbench_pin`、`measurement_conditions` (threads / records / skew / rmw / max_ope / extime / reps / pairing_design / contrast / site)、
`workloads[]` = cells: workload / rratio / variant_arm / baseline_arm / request_id / host / n / k / df / mean / sd / h / interval / baseline_mean / B / classification / variance_plan_breach / planned_sigma / pairs (30 件の pair_index・variant_tps・baseline_tps・signed_difference) / correctness (certified list、verify_configs)、
`artist_series` (panel ごとに実際に描いた mean 線の y・帯の上下・±B・0・30 点の (x, y))、`limitations` (result.json の 5 項の逐語コピー)、`caption`、`reproduction {cwd, argv, command}`、`authority_note` (lane の 3 値)。

### 2.6 CLI

`python3 tools/plotting/plot_a1_sized_paired.py [--repo-root <abs>] <out_prefix>`。`--repo-root` 既定は生成器の `parents[2]`。leaf は repo 相対で固定 (CLI から別 path を渡せない)。
`main(argv, *, expected_hashes=None)` の注入 seam。`validate_repo_closure(provenance, repo_root, *, expected_hashes=None)` (着地 PNG/PDF の sha256、pin 表、caption_source の現 sha256、cells と現 leaf の statistics 一致)。

## 3. test `orchestrator/tests/test_plot_a1_sized_paired.py` (Codex author)

- 実寸 fixture: 3 workload × 30 対 × 2 arm (`raw_tps` 30 本ずつ)、`statistics` は fixture の値から生成器と同じ式で計算、receipt / .complete.json / policy (実 policy を tmp へ複製、sha256 は fixture から計算) を tmp の repo 形 (`output/insights/…/`、`orchestrator/campaign/…`、`docs/paper-story/results/<稿>` の placeholder file) に置き、`expected_hashes` で注入。
- 必須 test (名は固定。変異 matrix の kill 相手):
  `test_fixture_has_production_shape_and_recomputes_statistics`、`test_artist_series_equal_provenance_cells_and_leaf_statistics` (入力→表示値の対応)、
  `test_real_figure_passes_layout_check`、`test_bbox_overlap_is_a_failure`、`test_layout_failure_publishes_nothing`、
  `test_caption_contains_fixed_literals_and_lane`、`test_caption_avoids_forbidden_claims`、`test_caption_figure_number_comes_from_prefix`、
  `test_formal_true_is_rejected`、`test_promotion_prohibited_false_is_rejected`、`test_statistics_mismatch_is_rejected`、`test_classification_mismatch_is_rejected`、
  `test_pair_difference_mismatch_is_rejected`、`test_leaf_hash_drift_is_rejected`、`test_policy_hash_mismatch_is_rejected`、`test_uncertified_arm_is_rejected`、
  `test_variance_plan_breach_true_is_rejected`、`test_provenance_binds_caption_source`、`test_pinned_hashes_are_used_when_no_override`、
  `test_pinned_input_hashes_match_results_document` (稿 §5.1 の表を grep して pin 表と一致)、`test_cli_writes_three_outputs_and_provenance_closure`、`test_cli_rejects_prefix_without_fig_number`、
  `test_real_leaf_loads_and_matches_results_document` (tracked leaf を実際に読み、稿 §2.1 の表の mean / h / B と一致)、`test_landed_fig9_repo_closure_and_caption_when_present`。
- `_run()` 自走 harness (pytest 無しで全 test を拾う、雛形 `test_plot_b10_static_tail_formal.py` 末尾)。parametrize id は ASCII。fixture に現行 hash を差し込まない (fixture の実 sha256 を注入するのは可)。

## 4. 変異 matrix (事前登録、DW-M01。対象 = 生成器の検査 1 箇所ずつ。kill = 名指しの test node が赤)

| # | 変異 (生成器) | 殺す test |
|---|---|---|
| M0 | 無変異 (baseline) | 全緑 (SURVIVED が期待) |
| M1 | `formal` の検査を外す | `test_formal_true_is_rejected` |
| M2 | `promotion_prohibited` の検査を外す | `test_promotion_prohibited_false_is_rejected` |
| M3 | 再計算 mean/sd/h と `statistics` の照合を外す | `test_statistics_mismatch_is_rejected` |
| M4 | 分類の述語検算を外す | `test_classification_mismatch_is_rejected` |
| M5 | `signed_difference == variant − baseline` の検査を外す | `test_pair_difference_mismatch_is_rejected` |
| M6 | pin 表 / 注入 hash との照合を外す | `test_leaf_hash_drift_is_rejected` |
| M7 | layout check を no-op にする | `test_bbox_overlap_is_a_failure` |
| M8 | caption から `FIXED_LANE` を落とす | `test_caption_contains_fixed_literals_and_lane` |
| M9 | `correctness_evidence.certified` の検査を外す | `test_uncertified_arm_is_rejected` |
| M10 | policy sha256 と `policy_sha256` の照合を外す | `test_policy_hash_mismatch_is_rejected` |
| M11 | artist series の mean 線を `median` に変える (表示値 ≠ cells) | `test_artist_series_equal_provenance_cells_and_leaf_statistics` |
| M12 | provenance から `caption_source` を落とす | `test_provenance_binds_caption_source` |

各変異は単一理由性 (前後・内側に同じ入力を拒否する層が無い) を実装後に親が確認し、成立しないものは登録から外して理由を記録する。

## 5. 受理集合

- 生成器が受理するのは「study `paper-story-a1-20260901-balanced5-sized-v1` の公開 leaf (pin 表の bytes) で、3 workload とも valid・n=30・formal=false・promotion_prohibited=true・両 arm certified・variance_plan_breach=false・統計が pairs から再計算で一致・分類が述語と一致」だけ。
  正例 = 現行 leaf (1 件)。それ以外は拒否 (別 attempt・別 study・pilot・formal=true の図はこの生成器では描けない。描くなら別図種)。
- 既存 test の期待値は変えない。既存 file は触らない。

## 6. 順序 (F36 の自己参照回避)

稿 v1 → author (生成器 + test) → 親が稿 v1 で図を試し生成 (review 用、成果物は job dir) → 段 6 レビュー 2 本 → fix → 焦点再レビュー → **稿を確定** → 親が最終 bytes で図を生成して
`docs/paper-story/figures/` へ置く → figures/README fig9 節 (provenance sha256 を含む) → 焦点 test → 変異 matrix → 記録 → 受入 → land。
稿は provenance の sha256 を持たない (figures/README.md が持つ)。稿の数値の出所は leaf の result.json (sha256 を稿に書く) であり、図の値と表の値の同一性は test に委ねる。
