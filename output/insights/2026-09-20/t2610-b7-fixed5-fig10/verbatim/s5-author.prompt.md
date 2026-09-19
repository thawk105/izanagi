単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (設計の正本。plan v2 と変異事前登録を含む): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s4-adjudication.md
- 親 brief (背景・不変条件): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s1-brief.md
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/tools/plotting/FIGURE_CONVENTIONS.md
- 雛形 1 (pin 表・caption_source・layout check・publish・closure・CLI の形をそのまま踏襲する): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/tools/plotting/plot_a1_sized_paired.py
- 雛形 1 の test (fixture・拒否 test・着地 test・self-run harness の形を踏襲する): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/orchestrator/tests/test_plot_a1_sized_paired.py
- 雛形 2 (上段の描画契約と external_inputs・validate_repo_closure の形だけ参照。この file は編集禁止): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/tools/plotting/plot_a2_certification.py (`_summarize_samples` 247〜、`_artist_series` 690〜、`make_figure` 710〜760、`validate_external_sources` / `validate_repo_closure` 859〜890)
- caption_source の稿 (値・判定・限定の言い方の出所。§1.4 判定規則、§2.1 主表、§2.2 標本、§2.4 正しさ、§2.5 図の材料、§4 限定、§5.1 SHA-256): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md
- 権威 bytes: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json
- raw manifest: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/raw-manifest.json
- 床値 JSON (3 本のうち 1 本。他 2 本は同形): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json
- policy: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json
- durable raw cell JSON (repo 外、読むだけ。2 本): /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/jobs/rr95/raw/rr95-fixed5.json、/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/jobs/rr95/raw/rr95-stock.json
- test の skip helper: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/orchestrator/tests/skiputil.py
- self-run harness の要件を課す meta-test: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/orchestrator/tests/test_plain_runner_coverage.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の**論文図の生成器 (matplotlib) と、その単体 test を新規に書く**依頼である。セキュリティでも攻撃でもなく、外部入力は repo 内の tracked JSON と、SHA-256 で束縛された repo 外の測定記録 JSON だけである。「凍結済みの測定結果 (certification.json と raw cell JSON) と床値 JSON から、稿 (Markdown) が既に確定した床値判定を図にする。生成器は判定を作らず、記録された判定と述語の整合だけを fail-closed で検査する」依頼だと理解して読むこと。

# 依頼 — [T-2610] fig10 (B-7 fixed 5 µs 三 workload 退行の図) の生成器と test を実装する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_b7_fixed5_regression.py` (新規)
2. `orchestrator/tests/test_plot_b7_fixed5_regression.py` (新規)
3. `probe-t2610/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場。親が job dir へ退避し repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` を一度も実行しない。commit は親が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない (最終図は親が生成する)。`output/` 配下へ書かない。
- `tools/plotting/plot_a2_certification.py`、`tools/plotting/plot_a1_sized_paired.py`、既存の全 test file、`orchestrator/tests/conftest.py`、`orchestrator/tests/README.md` を編集しない。
- 入力 JSON (certification / raw-manifest / 床値 / policy / durable raw) と稿を編集しない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。
- 既存 test の期待値を変えない。fixture へ現行 hash を差し込む等でテストを甘くしない (F27)。機構の正例・負例は実体の関数を通し、依存先を stub しない (F649)。
- 生成器へ判定の新規計算経路 (稿に無い閾値・補正・有意差) を足さない。`RECORDED_JUDGMENT` との整合検査だけにする。

## 作る物 1 — `tools/plotting/plot_b7_fixed5_regression.py`

段 4 裁定の「plan v2 §1」を正本とし、そこに書かれた定数・検査・戻り値・図の形・provenance・closure・CLI を全部実装する。自己完結 (matplotlib / numpy / 標準 library のみ、既存生成器を import しない)。雛形 1 の構造 (`FigureDataError` / `FigureLayoutError`、`_require`、`load_*`、`_figure_number`、`_caption`、`_artist_series`、`make_figure`、`check_figure_layout`、`build_provenance`、`validate_repo_closure`、`_publish_outputs`、`main`) を踏襲し、plan v2 に書かれた差分 (外部 raw、床値、判定、2 段構成、`validate_external_sources`) を足す。

caption は英文で決定的に組み立て、次の固定文を**逐語**で含めること (test でも逐語検査する):

1. `This is B-7 material, not a B-7 satisfaction decision (D2044 item 3).`
2. `The rule fixed before the results were seen classifies a workload as regression when effect < -floor (strict), floor being the D1639 between-run noise floor (coefficient of variation of the stock genome across 8 sessions of 5 repetitions, measured earlier under the same settings).`
3. `No regression is neither superiority nor proof of no difference; the floor is not the standard error of the effect, and no significance decision is made.`
4. `The outer status is the protocol's conjunction over the three workloads and follows from the negative read-heavy effect; it is not a research verdict.`
5. `This figure reports a single attempt of five samples per cell; it does not promote the certification and does not speak to repeated attempts.`
6. `Correctness comes from separate trace-enabled verify runs under the recorded check configuration, not the performance configuration: all 6 cells are recorded as certified with serializable verdicts (1 legacy and 5 performance records each); certified means serializability of the observed traces under that check configuration and nothing beyond, and this is not a performance certification.`
7. `Mean confidence intervals describe samples; they are not confidence intervals for effects, medians, or the floor judgment.`
8. `Top-row y axes are workload-local and must not be compared across panels.`
9. `Existing materials with other adopted values are neither pooled nor compared.`

caption の骨格 (値は data から書式化。`Figure N.` の N は出力 prefix の `fig<N>_` から):
`Figure N. B-7 material: static backoff fixed 5 us versus stock (no backoff) in three workloads, attempt <attempt_id> (study <study>; outer status <status>; a4_noise_floor_status <a4>). Columns: write-heavy (rr5, request <id>), balanced (rr50, request <id>), read-heavy (rr95, request <id>), each an independent campaign in its own request, with the stock control measured in the same campaign immediately before the adopted cell. Top row: all five trace-disabled performance samples per cell; short bars are medians; diamonds with error bars are sample means with t-distribution 95% confidence intervals (df 4); the gray dashed line is the workload's stock median and the effect denominator. Bottom row: median effects copied from certification (adopted median / stock median - 1): write-heavy <+x.xxxx>%, balanced <+x.xxxx>%, read-heavy <-x.xxxx>%; dashed ticks mark -floor per workload: write-heavy <-x.xxxx>%, balanced <-x.xxxx>%, read-heavy <-x.xxxx>%. [固定文 2] Result of that rule: write-heavy no regression, balanced no regression, read-heavy regression (below -floor). [固定文 3] [固定文 4] [固定文 1] [固定文 5] [固定文 6] Conditions: Pegasus compute nodes, <threads> threads, <records> records, Zipf <skew>, read-modify-write disabled, max operations <max_ope>, <extime> s per repetition, <reps> repetitions, silo, CCBench pin <pin>, source commit <9 桁>, no perf, trace-disabled performance; the adopted cells share one source bytes digest across workloads but each workload is a separate build (binaries differ). M tps means million transactions per second. [固定文 7] [固定文 8] [固定文 9]`
「Result of that rule:」の 3 語 (no regression / regression (below -floor)) は `judgments[w].recorded` から書式化する (固定文字列を直書きしない)。百分率は `f"{100*value:+.4f}%"` (床は `f"{-100*cv:.4f}%"`)。
caption に次を書かない: `significant`、`superior`、`satisfies B-7`、`B-7 is met`、`performance certified`、`improvement`、`anomaly` (raw は anomaly 件数を持たないため)。

## 作る物 2 — `orchestrator/tests/test_plot_b7_fixed5_regression.py`

段 4 裁定の「plan v2 §2」を正本とし、列挙された test を全部書く。雛形 1 の test と同じく `importlib` で生成器を読み込み、`skiputil` の `Skip` / `skip` を使い、末尾に `_run()` の self-run harness (`python3 <file>` で pytest 無しに全 test を走らせ、passed / failed / skipped を出し失敗で非 0) を付ける。`test_plain_runner_coverage.py` が要求する形に合わせること。
fixture は実寸 (3 workload × 2 cell × 5 標本、correctness legacy 1 + performance 5、床値 3 本、manifest に raw 6 entry) で、tmp に repo 相当 root と durable 相当 root の両方を作り、本物の `load_evidence` / `make_figure` / `check_figure_layout` / `build_provenance` / `validate_repo_closure` / `main` を通す。判定は `RECORDED_JUDGMENT` と一致する形 (rr95 だけ負の effect、他は正) にする。
変異事前登録の表 (裁定末尾) の各 negative 変異を殺す test を、表の「期待」欄の名前が分かる形で置くこと (例: `test_certification_hash_drift_is_rejected`、`test_raw_sha_mismatch_is_rejected`、`test_median_mismatch_is_rejected`、`test_effect_mismatch_is_rejected`、`test_judgment_mismatch_is_rejected`、`test_uncertified_cell_is_rejected`、`test_trace_enabled_samples_are_rejected`、`test_adopted_stock_token_is_rejected`、`test_bbox_overlap_is_a_failure`、`test_landed_fig10_rejects_all_missing_outputs`、`test_caption_contains_fixed_literals`、`test_floor_genome_mismatch_is_rejected`)。
稿との照合 test では、稿 §5.1 の表 (certification.json / raw-manifest.json の SHA-256)、§1.4 規則 3 の床値 3 値 (backtick 内の全桁 literal)、§2.1 主表の `effect_w` 列 (backtick 内 literal) と判定列 (「退行なし」= no-regression、「退行 (床値超)」= regression) を text から読んで生成器の定数・実 evidence と突き合わせる。
着地 test (`test_landed_fig10_repo_closure_and_caption_when_present`) は fig9 の同名 test と同型: bundle 3 file 実在 → `validate_repo_closure(prov, REPO)` → caption が `docs/paper-story/figures/README.md` に逐語で含まれる → README の fig10 節「## 着地 bytes の SHA-256」の 3 行 (`- \`<basename>\` SHA-256: \`<64 hex>\``) と現物一致。bundle 未着地は skip でなく失敗 (全欠落 1 ケース・部分欠落 6 集合)。**親が着地させるまでこの test は赤になる。それは期待赤であり、報告に「未着地のため赤」と書けばよい (xfail 化・skip 化しない)。**

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_b7_fixed5_regression.py` (self-run harness)。着地 test 以外が全部 passed であること。
2. 実データの全モード実走 (FIGURE_CONVENTIONS §10): `python3 tools/plotting/plot_b7_fixed5_regression.py --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a probe-t2610/fig10_b7_fixed5_three_workload_regression` が rc=0 で png / pdf / provenance.json の 3 成果物を出すこと。provenance の `effects`・`judgments`・`floors`・`cells[].median_tps` が稿 §2.1 / §2.2 と一致することを目視でなく `python3` で照合し、その結果を報告に写す。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` と、test file の列挙・命名に制約を課す他の meta-test を自分で洗い出して走らせる (F42。親の名指しを網羅と見なさない)。
4. `python3 -m py_compile` 相当の構文確認と、`PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_plot_b7_fixed5_regression.py','-q','-rf']))"` は guard で拒否されうる。拒否されたらその旨を書き、1 の自走結果を正とする。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない)

## 実装した物
file ごとの要点 (定数・検査・図の形・provenance の key)。
## 実走した検査
nodeid と passed / failed / skipped 件数。実データ実走の rc と 3 成果物の path、provenance と稿の照合結果 (median 6 値・effects 3 値・floors 3 値・judgments 3 値)。
## 未実走・期待赤
走らせられなかったもの、着地前に赤の test 名。
## 受理・拒否の含意
生成器が受理する入力の形と拒否する入力 (各 1 文)、通る正例 1 つ。
## 所有外への波及
所有外の caller・共有 fixture・consumer test・列挙型 meta-test への影響の静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
裁定の表の各 id について、どの test (nodeid) が殺すか。前後に同じ入力を拒否する層があって単一理由にならない変異があれば指摘。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
