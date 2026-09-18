単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2775-a1-sized-results-draft/s4-adjudication.md` — **親の段 4 裁定 (確定指示)。§2 が生成器の実装仕様、§3 が test の仕様、§4 が変異 matrix の事前登録、§5 が受理集合、§6 が順序。** brief と食い違うときは裁定が勝つ
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2775-a1-sized-results-draft/s1-brief.md` — 親の段 1 brief (背景・実測済み事実)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/tools/plotting/FIGURE_CONVENTIONS.md` — 作図規約 (§1・§2・§3・§6・§8・§9・§10 と「新しい図種を足すとき」)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/tools/plotting/plot_b10_static_tail_formal.py` — 521 行。**雛形 (読むだけ、編集しない)**: 定数 25〜58、`_require`/`_sha256`/`_number`/`_close` 69〜97、`load_measurements`/`_load_measurements` 156〜257 (pin 表と注入 seam、fail-closed 照合)、`_figure_number` 258、`_caption` 264〜288、`_artist_series` 297、`make_figure` 312〜369、`check_figure_layout` 378〜409、`build_provenance` 414〜428、`validate_external_sources`/`validate_repo_closure` 429〜461、`_publish_outputs` 462〜495 (tmp → os.replace、失敗時に何も出さない)、`main` 496〜末尾
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/orchestrator/tests/test_plot_b10_static_tail_formal.py` — 453 行。**test の雛形 (読むだけ、編集しない)**: `_load_module` 23、`_fixture` 49〜107 (実寸 fixture + seal)、`_reject` 121、`test_real_figure_passes_layout_check` 198、`test_bbox_overlap_is_a_failure` 207、`test_pinned_input_hashes_match_results_document` 326〜333 (稿の表を grep する型)、`test_cli_writes_three_outputs_and_provenance_closure` 335、`test_layout_failure_publishes_nothing` 368、`test_landed_fig8_repo_closure_and_caption_when_present` 414〜424、`_run` 426〜末尾 (自走 harness)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/tools/plotting/plot_a2_certification.py` — 795〜828 だけ読む (`build_provenance` の `caption_source` 行の型: `tracked_inputs` に `{"kind": "caption_source", "path", "sha256", "authority_scope"}`)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/orchestrator/tests/test_official_perf_closure.py` — 501〜523 だけ読む (`_python_has_perf_predicate`: tools/ 配下の .py で `perf` 名の変数を `if` 条件に使うと「未レビュー perf file」として赤になる。生成器はこれに掛からない書き方にする)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` — 親が書いた results 稿 (v1、親所有。編集しない)。§1.1〜§1.3 (条件)、§2.1 (statistics の表。`test_real_leaf_loads_and_matches_results_document` が照合する値)、§2.6 (図の仕様と test への委任)、§5.1 (pin 表と一致させる sha256 の表。`test_pinned_input_hashes_match_results_document` は「### 5.1」〜「### 5.2」の間を grep する) を読む
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json` — 実データ (270 KB、読むだけ。**全文 cat しない**。`python3 -c` で構造を見る: 最上位 key、`workloads[].statistics` (`pairs` 30 件)、`workloads[].arms.<name>` (`raw_tps` 30 本、`correctness_evidence`、`genome`、`expected_reps`、`observed_reps`、`actual_rounds`、`attempt_count`、`unstable`、`valid`、`errors`)、`source_binding.measurement_source_commit`、`policy_sha256`、`formal`、`promotion_prohibited`、`limitations`)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/output/insights/2026-09-13/paper-story-a1-balanced5-sized/receipt.json` — 実データ (`job_executions[]` の `workload` / `request_id` / `reservation_binding.host`、`formal`、`promotion_prohibited`、`policy.sha256`、`schema_version`、`study_id`)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/output/insights/2026-09-13/paper-story-a1-balanced5-sized/.complete.json` — 実データ (`files` map、`schema_version`)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/orchestrator/campaign/paper_story_a1_paired.v3-sized.json` — policy (`authority`、`workloads[]` の `name` / `reps` / `df` / `k` (文字列) / `planned_sigma_tps` (文字列) / `arms[]` の `name` / `role` / `contrast` / `flags`、`ccbench_acceptance.canonical_pin`、`scale`、`pairing.design` / `pairing.contrast` / `pairing.physical_orders`)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl` とする。上記以外も repo 内を読んでよい。

**大きい file を全文 `cat` しないこと。** `grep -n <語> <file>` で位置を出し、`sed -n '<開始>,<終了>p' <file>` で 200 行以内ずつ読む。

## この段の仕事

裁定 §2・§3 を実装する。新規 file 2 本だけを書く:

1. `tools/plotting/plot_a1_sized_paired.py` — A-1 balanced5 sized 本走 attempt-0001 (study `paper-story-a1-20260901-balanced5-sized-v1`) の 3 workload の対差平均 ± 登録済み区間を床 ±B と並べる新図種の生成器。裁定 §2.1〜§2.6 のとおり。
2. `orchestrator/tests/test_plot_a1_sized_paired.py` — 裁定 §3 の test。`_run()` 自走 harness 付き。

必ず守る点:

1. **触らない file**: 上記 2 本以外はすべて。特に `tools/plotting/plot_b10_static_tail_formal.py`、`plot_a2_certification.py`、`plot_backoff.py`、`FIGURE_CONVENTIONS.md`、`tools/plotting/README.md`、`docs/**` (results 稿を含む)、`output/**`、`orchestrator/campaign/**`、`orchestrator/tests/README.md`、`orchestrator/tests/conftest.py`、`.claude/**`、`hooks/**`。docs 編集・commit・`git add`・図の実データ生成 (成果物の `docs/paper-story/figures/` への配置)・`figures/README.md` の fig9 節は親が行う。
2. 生成器は既存生成器を import しない (自己完結。標準 lib + numpy + matplotlib `Agg` だけ)。
3. **統計は再計算して fail-closed 照合、分類は記録値をコピーして述語で検算** (裁定 §2.2 の 6)。`mean = statistics.fmean(diff)`、`variance = Σ(d−mean)²/(n−1)`、`sd = sqrt(variance)`、`h = k·sd/√n`、`B = 0.03·fmean(baseline raw_tps)`。producer と同じ式である (`orchestrator/campaign/paper_story_a1_paired.py` の `_statistics_from_signed_differences` 4708〜4776 を読んで揃える)。照合は相対 1e-9 または絶対 1e-6 tps。`classification` は result.json の値をコピーし、述語 (`abs(mean) − h > B` → resolved-above-floor / `abs(mean) + h ≤ B` → bounded-below-floor / else unresolved) と一致しなければ拒否。`variance_plan_breach` は `sd > planned_sigma_tps` で検算し、true なら拒否。
4. **規律 2**: `formal` が `False` 以外、`promotion_prohibited` が `True` 以外なら拒否。両 arm の `correctness_evidence.certified == [True]` かつ `verify_configs == ["legacy"]` でなければ拒否。caption に `not a performance certification` の literal を残す。図は性能の認証ではない。
5. **言い方**: 裁定 §2.4 の項 1〜10 の順序で caption を組み立て、`FIXED_LANE` と `FIXED_SCOPE` を逐語で入れ、禁止語 (裁定 §2.4 末尾の一覧) を生成器の文字列にも caption にも書かない。`improvement` / `regression` の単語も caption に書かない (向きは `sign positive / negative`)。生成器の中に「自分の caption に禁止句が無いか」を検査する gate は置かない (恒真なので)。検査は test 側だけ。
6. pin 表 (`PINNED_SHA256`: result.json / receipt.json / .complete.json / policy の 4 本。値は裁定 §2.1 と稿 §5.1) は生成器の定数とし、CLI から渡せない。test は `load_leaf(repo_root, expected_hashes=...)` / `main(argv, expected_hashes=...)` / `validate_repo_closure(..., expected_hashes=...)` の注入 seam で合成 fixture の実 SHA-256 を渡す (monkeypatch で定数を書き換えない)。
7. `CAPTION_SOURCE` (稿の repo 相対 path) は生成器の定数。生成時に現物の sha256 を計算して provenance `tracked_inputs` へ `kind: "caption_source"` で入れ、file 不在なら拒否。**着地 closure (`validate_repo_closure`) では caption_source の記録 sha256 と現 file の sha256 の一致も検査する** (稿が変われば図を作り直す契約)。
8. fixture は実寸 (3 workload × 30 対 × 2 arm、`raw_tps` 30 本ずつ、`statistics` は fixture の値から同じ式で計算、`pairs[i].<arm>_tps == raw_tps[i]`、receipt / .complete.json / policy / 稿 placeholder を tmp の repo 形に置く)。§10 のとおり、生成器が定数で持つ形 (WORKLOADS / REPS / arm 名) から組み立てる。少なくとも 1 本の test で**本物の matplotlib Figure** を `check_figure_layout` へ通す。policy fixture は実 policy を tmp へ複製してよい (sha256 は fixture から計算して注入)。
9. fixture に現行 hash を差し込むなど、テストを甘くして緑にしない (fixture の実 sha256 を注入するのは可)。期待値へ揮発 payload (生成時刻・working tree hash) を焼き込まない。
10. 新規 test の parametrize id は ASCII だけ (`pytest.param(..., id="ascii-id")`)。test 名は裁定 §3 の一覧を**そのまま**使う (変異 matrix の kill 相手として親が名指しする)。
11. `_run()` は pytest 無しで全 test を拾って走らせる (雛形: `test_plot_b10_static_tail_formal.py` 末尾)。`tmp_path` を要する test には tempfile の一時 dir を注入する。`Skip` は SKIP として数える。
12. 図: 1 行 × 3 列、x = pair index (0..29、5 刻みの整数目盛)、y = paired difference (M tps、`/1e6`)。30 対の open marker (線で結ばない)、mean の水平実線と mean ± h の帯 (半透明)、0 の細い実線、±B の破線 2 本。y 範囲は 0・±B・全点を含めて余白 8%。panel 題は `write-heavy (rr5): fixed10 - no-backoff` の形。凡例は 1 箇所 (または直接ラベル)。内部識別子 (campaign id・variant hash) を図に出さない。layout check は保存前に必ず走らせ、赤なら 3 成果物を 1 つも出さない (tmp → `os.replace` の順、失敗時に tmp を消す)。出力 prefix は `fig<N>_` 必須。
13. `test_official_perf_closure.py` に掛からないこと: 生成器の `if` / `while` / 三項の条件式に `perf` を含む名前 (`use_perf`、`perf_*` 等) を使わず、`performance_trace0_evidence` を読まない。source 全体に `perf` という語を書かないのが最も安全 (caption の "no perf" は data から書式化せず literal で持ってよいが、`if` 条件には絶対に出さない)。
14. provenance には裁定 §2.5 の field を全部入れる (`workloads[]` cells に 30 対の生値も入れる、`artist_series` に実際に描いた y 値、`limitations` は result.json の 5 項の逐語コピー、`reproduction` の argv)。

## test の実走

- `tools/run_tests.py` と `python -m pytest` は sandbox から走らない (rc=16 / guard 拒否)。**`PYTHONPATH=. python3 orchestrator/tests/test_plot_a1_sized_paired.py`** (末尾の `_run` 自走 harness) を走らせ、緑には実走 nodeid・件数・範囲を併記する。走らなければ「実装済み・未実走」と書き、`closed` と書かない。親が統合後に `tools/run_tests.py` で実走する。
- 生成器の実データ実走 (`python3 tools/plotting/plot_a1_sized_paired.py /tmp/<任意>/fig9_a1_balanced5_sized_attempt1`) は sandbox 内の書込み可能な場所 (`/tmp`) へ試してよいが、その成果物は repo に残さない (`docs/paper-story/figures/` には書かない)。実走できたら rc と 3 成果物の有無、provenance の `workloads[]` の mean / h / B が稿 §2.1 と一致するかを報告に書く。
- `test_landed_fig9_repo_closure_and_caption_when_present` は着地物が無いので skip になる (そう書く)。`test_real_leaf_loads_and_matches_results_document` は tracked leaf を読むので走る。

## 完了報告に必ず含める

- 変更 file と関数の一覧 (file:line)。
- 実走した nodeid と結果 (passed / failed / skipped 件数)。未実走があればそう書く。
- 実データ実走の rc と 3 成果物の有無、provenance の mean / h / B / classification と稿 §2.1 の一致 (試した場合)。
- caption の全文 (親が figures/README.md に収録するので逐語で)。
- 所有外 caller・共有 fixture・consumer test への波及可能性の静的列挙 (`test_plain_runner_coverage` の allowlist 検査、`orchestrator/tests/README.md` の制約 meta-test、`test_official_perf_closure.py`、`tools/check_docs.py` に関係する path があるか)。
- 受理集合が裁定 §5 の列挙に収まることの自己申告 (収まらない点があれば名指しで書く)。
- 変異 matrix (裁定 §4) の M0〜M12 について、実装後の対象 file:line と anchor になる逐語 (1〜3 行)、その変異を単独で殺すと予想する test node。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。`### 総括` と書いてはならない。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 変更一覧
## 実走結果
## caption 全文
## 波及の静的列挙
## 受理集合の自己申告
## 変異 matrix の anchor
## 総括
