# 段 4 裁定・plan v2・変異事前登録 — [T-2610] fig10 (2026-09-20 07:20 JST)

軽量版 (DW-C00) のため段 2・3 は省略した。裁定 inbox の再走査: local main は着手時 `b7f970dfa` から不変、`docs/spool/` に未 fold fragment 無し、
本主題の最新裁定は D2162 (2026-09-20) と D2044 項 3。brief の前提を覆す新事実は無い。

## 裁定

- (P1) 採用 — 5 標本は durable raw から読む。根拠: 稿 §2.5 が「生値: 30 標本 (権威は durable の raw cell JSON)」と材料を固定し、FIGURE_CONVENTIONS §2 が反復の不確かさ描画を要求する。
  certification.json は median のみを持つ。fig6 が同じ束縛 (tracked raw-manifest の SHA-256 → 外部 raw) で着地済み。
- (P2) 採用 — 判定は稿 §2.1 の転記を定数に持ち、述語 `effect < −cv` との一致を fail-closed で検査する。生成器は判定を新しく作らない (D2162「床値判定はコードに入れず稿で計算」の趣旨を、
  図では「稿の判定を写し、述語との整合だけ検査」で守る。fig9 の classification と同型)。
- (P3) 採用 — 2 段構成 (上段 3 panel の標本、下段 1 panel の effect と −floor)。上段は fig6 の描画契約を踏襲し、下段だけが本図の純増。
- scope 外 (実装しない): 既存材料 (2026-09-16 稿の 10 / 5 / 2 µs) の併記 panel (D1993 項 6、規律 7)、有意差・区間の effect への付与、B-7 充足の表示、certification 昇格の語、
  plot_a2_certification.py の一般化・再利用、床値 √2 補正、新 gate・check_docs 規則・台帳。
- raw の correctness は anomaly 件数を持たない → caption は「certified・verdict serializable の記録 (legacy 1 + performance 5)」までを書き、anomaly 0 は書かない (稿の anomaly 0 は WAL 由来、図の主張にしない)。

## plan v2 (親起草、file 粒度)

### 1. `tools/plotting/plot_b7_fixed5_regression.py` (新規、自己完結、matplotlib/numpy のみ、既存生成器を import しない)

定数:
- `SCHEMA = "izanagi-b7-fixed5-regression-figure-provenance/v1"`, `GENERATOR_PATH`, `REPO_ROOT = parents[2]`
- `STUDY = "paper-story-b7-fixed5-regression"`, `ATTEMPT_ID = "b7f5-20260919a"`
- `CERT_SCHEMA = "paper-story-a2-certification-result/v4"`, `MANIFEST_SCHEMA = "paper-story-a2-full-raw-manifest/v4"`, `RAW_SCHEMA = "paper-story-a2-cell-result/v3"`,
  `FLOOR_SCHEMA = "between-run-noise-floor/v1"`, `POLICY_SCHEMA = "paper-story-a2-certification-policy/v2"`
- `LEAF_DIR = "output/insights/2026-09-19_t1998-b7-fixed5-three-workload"`, `CERT_JSON = LEAF_DIR + "/certification.json"`, `MANIFEST_JSON = LEAF_DIR + "/raw-manifest.json"`
- `FLOOR_JSON = {w: f"output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{w}_rmw0.json"}` (w ∈ rr5 / rr50 / rr95)
- `POLICY_PATH = "orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json"`
- `PINNED_SHA256` = {CERT_JSON: b6493e4eed17e23cbe10682af72e7c06b805ced1e13a329ffd13df896f4d5431, MANIFEST_JSON: be8163da33416020de3bfdca136ceaff5430e0878c46abe90681e6b0d954f6ac,
  floor rr5: 25b4d2a070ad6e5ebf44973e134d7149a9fa0ec9996b3d6ef0f37a5b7b5a34b8, rr50: a94dc83ed21c8f9e390b1af642487c10e551f8f6e75ee977e9bad948fd745b26,
  rr95: 23c024e467559b238b58ef9c32c144f78d23cb48ad7aafd6bbc02cd108842ce7, POLICY_PATH: c6b24050d17c4bc552d254ce65e328b3a6edca919387b5720b4e025ea78b0df1}
  (`INPUT_KINDS` = certification / raw_manifest / floor_rr5 / floor_rr50 / floor_rr95 / policy。pin は CLI から渡せず、test は `expected_hashes` 注入 seam を使う)
- `CAPTION_SOURCE = "docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md"`、`CAPTION_SCOPE = "wording of limitations and conditions only; not measurement values, effects, or the floor judgment"`
  (pin しない。生成時に SHA-256 を取り provenance `tracked_inputs` に `kind: "caption_source"` で記録。不在は拒否)
- `WORKLOADS = ("rr5", "rr50", "rr95")`, `LABELS = {"rr5": "write-heavy", "rr50": "balanced", "rr95": "read-heavy"}`, `RRATIOS = {rr5: 5, rr50: 50, rr95: 95}`
- `STOCK_GENOME = {"BACK_OFF": 0, "BACKOFF_FIXED": -1}`, `ADOPTED_GENOME = {"BACK_OFF": 1, "BACKOFF_FIXED": 5}`, `ADOPTED_US = 5`
- `FLOOR_GENOME = "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"`
- `REPS = 5`, `DF = 4`, `T975_DF4 = 2.7764451051977987`
- `RECORDED_JUDGMENT = {"rr5": "no-regression", "rr50": "no-regression", "rr95": "regression"}` (稿 §2.1 の転記)
- `DEFAULT_MEASUREMENT_ROOT = "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a"`
- `RAW_REL = {f"{w}-{role}": f"jobs/{w}/raw/{w}-{role}.json"}` (role ∈ stock / fixed5)

`load_evidence(repo_root, measurement_root, *, expected_hashes=None)` → data dict。fail-closed (`FigureDataError`) の検査:
- tracked 6 file の SHA-256 が pin と一致。caption_source が実在。
- certification: schema、`study`、`attempt_id`、`status` は非空 str (写すだけ)、`a4_noise_floor_status` は非空 str (写すだけ)、`effects` の key 集合 == WORKLOADS、
  `request_ids` の key 集合 == WORKLOADS、`policy_sha256` == pin の policy SHA、`protocol_sha256` == manifest の `protocol_sha256`、`current_pin` == manifest `current_pin`、
  `source_commit` 非空。`cells` は 6 件で `cell_id` 順 = rr5-stock, rr5-fixed5, rr50-stock, rr50-fixed5, rr95-stock, rr95-fixed5、`workload`/`role` (stock / adopted)/`genome` 一致、
  `source_binding_status == "bound"`、stock の `src_token == "stock"`、adopted の `src_token` は `"stock"` でなく 3 workload で同一、`correctness.status == "certified"`・
  `disposition == "pass"`・`legacy == "pass"`・`performance == "pass"`・`legacy_repetitions_observed == 1`・`performance_repetitions_observed == 5`、
  `performance.status == "complete"`、`performance.median_tps` 正の有限数、`perf_bin_sha256` / `trace_bin_sha256` は 64 hex。
- manifest: schema、`study`、`attempt_id`、`protocol_sha256`、`files` に 6 raw path が全部ある (他 entry は無視)。
- raw 6 file: `measurement_root / RAW_REL[cell]` が実在し SHA-256 == manifest `files[path]`。JSON: schema、`cell_id`、`attempt_id`、`src_token` == certification cell、`genome` 一致、
  `performance.samples_tps` は長さ 5 の正の有限数、`performance.unstable is False`、`performance.trace_enabled is False`、`performance.status == "complete"`、
  `performance.perf_bin_sha256` == certification cell `perf_bin_sha256`、`build_evidence.performance_trace_disabled_build is True`、`build_evidence.trace_bin_sha256` == certification cell、
  `performance.workload` == {threads 48, records 1000000, reps 5, extime 3, workload {rratio 文字列 == str(RRATIOS[w]), rmw "0", max_ope "10", zipf "0.9"}} (policy と照合)、
  `correctness.legacy` 長さ 1・`correctness.performance` 長さ 5、各記録 `verdict == "serializable"`・`certified is True`・`status == "pass"`・`integrity == "ok"`・`trace_enabled is True`・
  `trace_binary_sha256` == certification cell `trace_bin_sha256`。
- 再計算: `median = statistics.median(samples)` が certification `median_tps` と `==`。`mean`、`stdev` (n−1)、`ci95_half = T975_DF4 * stdev / sqrt(5)`。
  `effect_computed = adopted_median / stock_median − 1` が `effects[w]` と `math.isclose(rel_tol=0, abs_tol=1e-12)`。
- floor 3 file: schema、`workload.ycsb_rratio == str(RRATIOS[w])`、`ycsb_zipf_skew == "0.9"`、`ycsb_rmw == "0"`、`genome == FLOOR_GENOME`、`threads == 48`、`records == 1000000`、
  `between_run.cv` 正の有限数、`between_run.sessions == 8`、`between_run.reps_per_session == 5`、`between_run.high_variance is False`。
- 判定: `computed = "regression" if effects[w] < -cv else "no-regression"` が `RECORDED_JUDGMENT[w]` と一致。不一致は拒否。
- policy: schema、`study`、`performance_common` (records / threads / skew / rmw / max_ope / extime / reps / ccbench_protocol) を `measurement_conditions` に写す。
  `workloads[].adopted_backoff_us == 5` ×3、`cells` の (cell_id, role, genome) が上の順序と一致。
- 戻り値: `repo_root`、`tracked_inputs` (kind/path/sha256、caption_source は authority_scope 付き)、`external_inputs` (kind "raw_cell"、root 相対 path、sha256、cell_id)、
  `study`、`attempt_id`、`source_commit`、`ccbench_pin`、`request_ids`、`outer_status`、`a4_noise_floor_status`、`measurement_conditions`、
  `cells` (6: cell_id, workload, label, role, genome, src_token, samples_tps, median_tps, mean_tps, stdev_tps, ci95_half_tps, perf_bin_sha256, trace_bin_sha256, correctness 要約 {status, legacy_records 1, performance_records 5, verdicts_all_serializable True})、
  `effects` (写し)、`effect_crosschecks` ({computed, authority_matches: True})、`floors` ({w: {cv, sessions, reps_per_session, path}})、
  `judgments` ({w: {recorded, predicate: "effect < -floor (strict)", effect, neg_floor, computed_matches_recorded: True}})。

`make_figure(data)`: `plt.rcParams` を script 内で設定 (DejaVu Sans、font 8、top/right spine off)。`fig = plt.figure(figsize=(12, 6.4))`、`GridSpec(2, 3, height_ratios=[1.0, 0.85])`。
上段 3 axes (workload 順): x = 0 (stock) / 1 (fixed 5 us)、5 標本を決定的 jitter (`[-.12, -.06, 0, .06, .12]`) の散布 (M tps)、median を x±.20 の短い横棒、mean を菱形 + ci95 誤差棒、
stock median を灰破線 (`--`, `#777777`)、adopted median の上に effect % の直接 label (`gid="direct-label"`)、title `"{label} (rr{ratio})"`、xticks `["stock", "fixed 5 us"]`、
ylabel は左端だけ `"throughput (M tps)"`、y は 0 〜 max(samples)×1.28 (workload 別尺度)。
下段 1 axes (3 列を跨ぐ): x = 0/1/2 (workload)、y = effect (%)、effect を marker (退行は塗り、退行なしは白抜き、同一色)、0 線 (`#555555`, lw .6)、各 x に −floor (%) を
短い破線 (x±.3、`#b35806`) と label `"-floor {:.4f}%"`、effect の直接 label `"{:+.4f}%"`、判定 label `"no regression"` / `"regression (below -floor)"` (`gid="direct-label"`)、
xticks = label (rr)、ylabel `"median effect vs stock (%)"`、y 範囲は全 effect と −floor と 0 を含み上下 12% margin。
`fig.legend` (上段: samples / median / mean ± t95 CI / stock median、下段: effect / −floor) を `loc="upper center"`、`frameon=False`。
`fig.text(.5, .015, "Top-row y axes are workload-local; do not compare panel heights. Mean t95 CI describes samples, not effects.")`。
`fig._b7_artist_series = _artist_series(data)` を保持。

`_artist_series(data)`: 上段 6 cell の {cell_id, kind sample-points/median/mean-ci95, x, values}, stock median baseline, effect-label; 下段 {workload, effect_pct, neg_floor_pct, judgment, zero}。

`check_figure_layout(fig, axes)`: fig9 の関数を踏襲 (renderer-backed、text 逸脱・隣 panel 侵入・bbox 重なり・axis decoration 逸脱で `FigureLayoutError`)。axes 数は 4 固定。

`_caption(data, prefix)`: 英文、`Figure {N}.` は prefix `fig<N>_` から。固定 literal (test が逐語検査):
- `"B-7 material, not a B-7 satisfaction decision (D2044 item 3)"`
- `"the rule fixed before the results were seen classifies a workload as regression when effect < -floor (strict)"`
- `"no regression is neither superiority nor proof of no difference"`
- `"the floor is the between-run coefficient of variation of the stock genome measured earlier under the same settings (D1639), not the standard error of the effect, and no significance decision is made"`
- `"a single attempt of five samples per cell; it does not promote the certification and does not speak to repeated attempts"`
- `"Correctness comes from separate trace-enabled verify runs"` … `"this is not a performance certification"`
- `"Top-row y axes are workload-local and must not be compared across panels."`
- `"Existing materials with other adopted values are neither pooled nor compared."`
値 (effects %、−floor %、判定、median、request id、pin、source commit、条件) は data から書式化。outer status と `a4_noise_floor_status` は「protocol output; conjunction over the three workloads; follows from the negative read-heavy effect; not a research verdict」と併記。
禁止語 (test): `significant`, `superior`, `satisfies B-7`, `B-7 is met`, `performance certified`, `promot` の肯定形 (`does not promote` は可)。

`build_provenance(data, outputs, argv, *, hash_paths=None, generated_utc=None, artist_series=None)`: fig9 型 + `external_inputs`。`generator.sha256` は生成時記録。
`validate_repo_closure(provenance, repo_root)`: schema / generator path、`tracked_inputs` と `outputs` の path が実在し SHA-256 一致 (caption_source 含む)、`external_inputs` が manifest `files` と一致、
`artist_series` と `caption` を provenance の data から再計算して一致 (外部 root を読まない)。`validate_external_sources(provenance, measurement_root)`: raw 6 の SHA-256 一致。
`_publish_outputs`: fig9 と同じ (layout check → tmp へ描画 → provenance → `os.replace`、失敗時は 1 つも残さない)。
`main(argv=None, *, expected_hashes=None)`: `--repo-root` (既定 REPO_ROOT)、`--measurement-root` (既定 DEFAULT_MEASUREMENT_ROOT)、`out_prefix`。展開 argv を `reproduction` に記録。例外は rc=2 で stderr。

### 2. `orchestrator/tests/test_plot_b7_fixed5_regression.py` (新規)

fig9 test (`test_plot_a1_sized_paired.py`) の構成を踏襲: `importlib` で生成器を読み込み、`skiputil` の `Skip`/`skip`、末尾に `_run()` self-run harness (`python3 <file>` で pytest 無しに走る)。
実寸 fixture (`_fixture(tmp_path)`): repo 相当 root と durable 相当 root を tmp に作り、6 tracked file (certification / manifest / floor×3 / policy) と caption_source、6 raw file を
production と同じ形 (3 workload × 2 cell × 5 標本、correctness legacy 1 + performance 5、floor の between_run) で合成し、SHA-256 を manifest / `expected_hashes` に埋める。
値は実測値でなくてよいが、判定が RECORDED_JUDGMENT と一致する形にする (rr95 だけ負)。
テスト (最低限、全て本物の Figure / 本物の関数を通す):
- fixture が production 形 (6 cell × 5、4 axes) で、median / effect / judgment を再計算して一致
- `artist_series` == provenance と cells の整合
- 実 Figure が layout check を通る / bbox 重なりを注入すると `FigureLayoutError` / layout 失敗時に 3 成果物を 1 つも出さない
- caption が固定 literal・lane 文・図番号 (prefix 由来) を含み、禁止語を含まない
- 拒否 (各 1 test、`_reject_changed` 型): certification SHA drift、manifest SHA drift、floor SHA drift、policy SHA と `policy_sha256` 不一致、raw SHA と manifest 不一致、
  raw 欠落、標本数 ≠ 5、median 不一致、effect 不一致、判定不一致 (floor cv を大きくして rr95 を no-regression にする / effect 符号反転)、
  `correctness.status` ≠ certified、raw verdict ≠ serializable、raw `performance.trace_enabled` True、`unstable` True、adopted `src_token == "stock"`、
  `source_binding_status` ≠ bound、caption_source 不在、cell 順序入替
- provenance が caption_source を kind / path / sha256 / authority_scope 付きで束縛
- `expected_hashes` 無指定で pin が使われる
- 生成器の comment 変更で closure が壊れない (generator.sha256 は pin でない)
- 着地 path: 同 basename の別 dir を拒否
- pin と稿の照合: `PINNED_SHA256` の certification / manifest が稿 §5.1 表の SHA-256 と一致、floor 3 値が稿 §1.4 規則 3 の全桁 literal と一致、
  `RECORDED_JUDGMENT` と effects が稿 §2.1 主表の行 (判定列・`effect_w` 列) と一致
- CLI: 3 成果物 + closure、`fig<N>_` でない prefix は rc=2 で何も出さない
- 実 evidence: durable root が無ければ skip、部分欠落は失敗、有れば `load_evidence(REPO, root)` の median 6 値が稿 §2.2 と一致
- 着地 fig10: bundle 3 file 実在 + closure + caption が README に逐語 + README fig10 節の「着地 bytes の SHA-256」3 行と現物一致。全欠落・部分欠落 (6 集合) は skip でなく失敗

### 3. docs (親が書く、docs-only)

- `docs/paper-story/figures/README.md`: 一覧表に fig10 行、末尾に fig10 節 (何を示す図か / 既存図との関係 / 入力 / 再現 / 再現できるのは値 / 作図規約への適合 / キャプション正文 / proof chain / 着地 bytes の SHA-256)。
- `tools/plotting/README.md`: 「B-7 fixed 5 µs 三 workload 退行 figure」節 (command 例・入力・拒否条件・出力)。
- `docs/paper-story/README.md`: results 表 2026-09-19 行の「図は無い」→「図 10 (本稿を `caption_source` として束縛、F36)」。
- insight `output/insights/2026-09-20/t2610-b7-fixed5-fig10/README.md` + verbatim、worklog fragment、phase3.md は該当チェック行が無ければ触らない。

## 変異事前登録 (DW-M01、位置は関数・述語で指定、`old`/`new` は実装後に spec へ写す)

| id | category | 位置 | 期待 |
|---|---|---|---|
| m0-equivalent-docstring | positive | 生成器 module docstring に 1 行追加 | SURVIVED (expected_nodes 空) |
| m1-drop-cert-hash-check | negative | tracked SHA-256 一致検査を恒真化 | KILLED: certification/manifest/floor hash drift test |
| m2-drop-raw-manifest-check | negative | raw の SHA-256 == manifest 検査を恒真化 | KILLED: raw sha mismatch test |
| m3-drop-median-crosscheck | negative | `median == median_tps` を恒真化 | KILLED: median mismatch test |
| m4-drop-effect-crosscheck | negative | `isclose(effect_computed, effects[w])` を恒真化 | KILLED: effect mismatch test |
| m5-drop-judgment-check | negative | `computed == RECORDED_JUDGMENT[w]` を恒真化 | KILLED: judgment mismatch test |
| m6-drop-certified-check | negative | `correctness.status == "certified"` を恒真化 | KILLED: uncertified cell test |
| m7-drop-trace-disabled-check | negative | `performance.trace_enabled is False` を恒真化 | KILLED: trace-enabled samples test |
| m8-drop-adopted-token-check | negative | adopted `src_token != "stock"` を恒真化 | KILLED: adopted stock token test |
| m9-bypass-layout-overlap | negative | bbox overlap で raise しない | KILLED: bbox overlap test |
| m10-landed-skip-on-missing | negative (test file) | 着地 test で全欠落時に skip する旧挙動を復活 | KILLED: landed rejects all-missing test |
| m11-drop-caption-literal | negative | caption の「not a performance certification」文を削除 | KILLED: caption fixed literal test |
| m12-drop-floor-genome-check | negative | floor `genome == FLOOR_GENOME` を恒真化 | KILLED: floor genome mismatch test |

単一理由性 (F820) は実装後に probe で確認し、前後に同じ入力を拒否する層があれば再照準する。runner は `tools/mutation_worktree.py --runner-mode dispatch` (計算ノード)、
spec / out は checkout 外 (job dir)。baseline 緑必須。

## 追記 (2026-09-20 07:35 JST、実行前の経路確定)

変異走行の経路は `tools/mutation_worktree.py` (独立 clone) でなく、DW-M05 の正本経路 = 主 repo に `git worktree add -b mut-t2610-fig10 .codex/worktrees/mut-t2610-fig10 <固定 commit>` で作り `dev_wave_submodule_init.py` で初期化した登録 worktree へ `tools/mutation_harness.py --repo <その worktree> --runner-mode dispatch --detached` を直接当てる形にする (2026-09-20 の test-inventory-prune wave の実測に従う。独立 clone は submodule 供給 URL が非 local で初期化に拒否される)。spec / out / attempt-out は job dir (checkout 外)。走行中は親も子も両 worktree へ 1 byte も書かない。
