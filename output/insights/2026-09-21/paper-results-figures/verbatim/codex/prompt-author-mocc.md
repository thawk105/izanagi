単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (設計の正本。所見の採否・plan v2 の差分・変異事前登録の表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s4-ruling.md
- 段 2 plan (§3 生成器・§4 test が本単位の詳細。段 4 裁定と食い違う箇所は段 4 裁定が優先。特に図の形は段 4 裁定の 1 axes forest + 数値列): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/plan.md
- 親 brief (不変条件・描かないもの・過去の型 F872 / F623 / F812 / F653、P5〜P8): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md
- caption_source の稿 (凍結物。§0 の書かないもの、§1.3 検出力、§1.5 条件、§2.1〜§2.6 の表、§3 限定、§5.1 SHA-256 表): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md
- 作図規約: /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/tools/plotting/FIGURE_CONVENTIONS.md
- 雛形 1 (repo 外証拠を束縛する生成器の型: `EVIDENCE_ROOT`・`EXTERNAL_REL`・`load_evidence`・`check_figure_layout`・`build_provenance`・`validate_repo_closure`・`validate_external_sources`・`_publish_outputs`・`main`。`grep -n` で位置を出して部分読み): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/tools/plotting/plot_b10_waiting_grid_forest.py
- 雛形 2 (test の型: fixture・`_reject`・外部 / repo 閉包の分離・実データ test・着地 test・`_run` harness。部分読み): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/test_plot_b10_waiting_grid_forest.py
- 権威入力 (repo 外、読むだけ。各 100〜400 KB、全文を読まず `json.load` して key を見る): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json と同 dir の `W1/result.json`〜`W4/result.json`
- test の skip helper: /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/skiputil.py
- self-run harness の要件を課す meta-test: /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/test_plain_runner_coverage.py
- perf 名の条件式を禁じる走査 test (`_python_has_perf_predicate` の規則だけ読む): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-mocc/orchestrator/tests/test_official_perf_closure.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の**論文図の生成器 (matplotlib) と、その単体 test の新設**である。セキュリティでも攻撃でもなく、入力は SHA-256 で束縛した repo 外の JSON 5 本と、repo 内 tracked の Markdown (稿) だけである。
「stock mocc の軽量 witness 4 arm × 60 走 (本走 4 block W1〜W4 × 15 round × 4 arm、smoke は含めない) の G2 signal 検出率・Clopper–Pearson 両側 95% 区間・曝露量 (走あたり commit 数の平均) を、
W1〜W4 の `runs[]` から再計算して `summary.json` と照合し、稿 §2 と同じ書式の文字列で 1 axes の forest 図 (fig15) に描く自己完結の新 file を作る」依頼だと理解して読むこと。
測定は TRACE=1 の観測専用 build で**非 certifying**である。

# 依頼 — fig15 (mocc witlight 4 arm) の生成器と test を新設する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_mocc_witlight_four_arm.py` (新規)
2. `orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (新規)
3. `probe-fig15/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場。親が job dir へ退避し repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` / `git rm` を一度も実行しない。commit は親 (と起動器) が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、`docs/paper-story/results/*`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない (最終の fig15 は親が生成する)。`output/` 配下へ書かない。repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/`) へ書かない。
- 他の生成器・他の test file・`orchestrator/tests/conftest.py`・`orchestrator/tests/acceptance_duration_ledger.json` (台帳は登録しない = 段 4 裁定 P9)・`orchestrator/campaign/*`・verifier・discriminator を編集しない。他の生成器を import しない (自己完結、matplotlib + numpy + 標準 library のみ。scipy を使わない)。
- 権威入力 5 本と稿を編集しない。`smoke/`・`parent-accounting.json`・走ごとの `runs/<ordinal>-<arm>/` 配下を入力として開かない (入力は 5 本だけ)。
- `tools/run_tests.py` と `python -m pytest` は sandbox では使わない (test は下の self-run で走らせる)。
- fixture へ現行 hash を差し込む等でテストを甘くしない (F27)。機構の正例・負例は実体の関数を通し、依存先 (`load_evidence`・`make_figure`・`check_figure_layout`・`_publish_outputs`) を stub しない (F649)。
- **描かない・書かないもの:** 非有意を同等性・「効果なし」・「witness on では G2 が出ない」として、TRACE=1 の commit 数を性能 (throughput・速い・遅い) として、G2 signal を根因の同定・実 anomaly / torn read の確認として。
  [T-1892] / [T-2774] / [T-2779] の値との合算・比較。smoke を第 5 block として数えること。稿に無い推論 (曝露平均の区間・検定、軽量化の改善量)。
- `if` / `while` / 三項の条件式に `perf` を含む名前を置かない (`test_official_perf_closure.py` の走査に掛かる)。

## 作る物 1 — `tools/plotting/plot_mocc_witlight_four_arm.py`

段 4 裁定「plan v2 / fig15」と plan §3 を正本とする (図の形・集計・provenance は段 4 裁定が優先)。要点:
- 定数: `EVIDENCE_ROOT = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W"`、`EXTERNAL_SHA256` = root 相対 5 件 (`summary.json` `b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698`、
  `W1/result.json` `ca8ab3ff579e3fb55b97447ebb7b647d34806a6fd452ad410051aca9e5bd4b50`、`W2/result.json` `473063aa741cc4c349931d987c902facbc5dcf6499b3692ea2cad3a27ac1e584`、
  `W3/result.json` `f68876600f1cd5b7300b030fb3cfa75509cc7a687858d6f12985051ce46e3642`、`W4/result.json` `197a2798de5ef53a7f6a32460f7ecfa5adbba8e853778b315d3b6e1839c36a6c`)。pin は CLI から渡せない (test は `expected_hashes` seam)。
  `CAPTION_SOURCE = "docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md"`。arm 4 つと順序、BACK_OFF / witness の対応、block 4 つ、rounds 15、planned 60。
- `summary.json.inputs` は W1〜W4 の 4 件 (原保存先の絶対 path と sha256) と exact 一致 (余剰・重複・欠落・順序・path・digest)。`--evidence-root` は読み出し場所で、summary 内の原保存先 path は書き換えない。
- 集計 (段 4 裁定 B-4 の早期拒否型): 全 240 走が benchmark `rc == 0` かつ verifier `(rc, status)` ∈ {(0, `no-g2`), (1, `g2`)}。それ以外は拒否。k = `verifier.status == "g2"` の数、N = m = decisive_m = 60 を再計算し、summary の N / m / k / failure / indeterminate / decisive_m / k_over_m / cp95 / discriminator_counts / identification と照合。
  block 検査 (block ID・completed・rounds 15・planned 60・not_started 0・runs 60・ordinal・round・各 round の 4 arm・回転・run と bindings の arm / witness / BACK_OFF・`workload_argv` が 4 block で一致)。
- CP 両側 95% と片側 Fisher (on が低い方向) は標準 library で (plan §3)。commit 平均 = その arm の 60 走の `commit_count` 総和 / 60。on/off 比は丸め前の平均どうし。
- 書式は稿 §2.2 / §2.3 / §2.6 と同じ文字列: `0/60`、`0%`、`1.667%`、`[0%, 5.963%]`、`[0.042%, 8.940%]`、`613,741.5`、`710,659.4`、`788,885.6`、`933,621.8`、`0.500`、`0.8636`、`0.8450`。
- 図 (段 4 裁定の形、必ず守る): axes はちょうど 1。縦に 4 arm (上から `on / BACK_OFF=0`、`off / BACK_OFF=0`、`on / BACK_OFF=1`、`off / BACK_OFF=1`)、横軸 `G2 signal detection rate (%)`、点 = k/m、横線 = CP 区間。
  右側の予約領域に arm ごとの数値列 (`k/m`、率、CP 区間、`mean commits per run`)、BACK_OFF ごとの `on/off exposure ratio`。
  図中の短い注記 (実描画必須): (i) non-certifying と TRACE=1 build、(ii) commits は `exposure, not performance`、(iii) 片側 Fisher (on lower、unadjusted) `p = 0.500` (BACK_OFF=0 / 1)、`not equivalence`、`power 0.105` は設計仮定下の計算値、
  (iv) `G2 signal` は verifier の検出で root cause を同定しない。文言は layout に合わせて短くしてよいが、4 要素とも可視 text に含める。
- caption (英文、決定的、`Figure {N}.` 始まり、図番号は prefix の `fig<N>_` から): plan §3 の固定文 7 文 (`Non-significance does not establish equivalence, and zero detections do not establish absence.` など) を逐語で含み、
  主比較 BACK_OFF=0 / 副比較 BACK_OFF=1・on が低い方向・未調整 p、discriminator が未到達 (on arm に G2 signal が無く 0 件発火)、固定時間 3 s の走あたり率で同じ commit 数への曝露比較ではないこと、旧 wave の値と合算しないこと、
  G2 signal 2 走の所在 (W1 の off / BACK_OFF=0、W3 の off / BACK_OFF=1)、**`Conditions:` 文** (W1〜W4 の `bindings.workload_argv` から: 48 threads、10,000 records、Zipf 0.9、read ratio 50、rmw 0、max operations 10、3 s、TRACE=1 build、pin e9e477ca + X/P + witlight patches、Pegasus compute nodes、4 blocks W1–W4 × 15 rounds × 4 arms、smoke excluded) を含む。
- provenance: 段 4 裁定の key (`tracked_inputs` = caption_source 1 件、`external_inputs` = 5 件、`source_inputs`、`measurement_conditions`、`arms`、`blocks`、`comparisons`、`exposure_ratios`、`artist_series` = 実際に描画へ渡した値と文字列 (F623)、`caption`、`outputs`、`reproduction`、schema `izanagi-mocc-witlight-four-arm-figure-provenance/v1`)。240 走の records は持たない。
- `validate_repo_closure(provenance, repo_root)` は repo 外を読まずに、schema・caption_source の現 SHA-256・出力 png / pdf の SHA-256・provenance の統計から作り直した caption / artist_series の一致を検査する。
  `validate_external_sources(provenance, evidence_root)` は 5 file の SHA-256 と、原本から再導出した統計・書式・条件が provenance と一致することを検査する。
- layout 検査は雛形 1 の `check_figure_layout` を自己完結で移植 (axes 数 1)。保存前に実行し、違反なら 3 成果物を 1 つも出さない。

## 作る物 2 — `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`

段 4 裁定と plan §4 の一覧を**全部**その名前で書く (段 4 裁定の変更: failure / indeterminate は拒否、実証拠 test を 2 本に分割、禁止句 test (caption と可視 Text、肯定形の列挙、否定の固定文は許す、題へ違反句を足した負例)、不完全 bundle は全欠落 + 単独欠落 3 例)。
- fixture は実寸 (4 block × 60 走 = 15 round × 4 arm、回転、G2 signal 2 走 = W1 ordinal 18 の off / BACK_OFF=0 と W3 ordinal 5 の off / BACK_OFF=1、commit 数は非一様、smoke なし)。W1〜W4 を書いて hash 化してから summary の `inputs` を組み、最後に summary を hash 化する。
- CP / Fisher の期待値は生成器の関数から作らず独立 literal (plan §3 の 0/60 上限 `0.059629492286166874`、1/60 `[0.0004218744523420083, 0.08939905005748705]`、`[[0,60],[1,59]] -> 0.5`)。
- 実データ test: `test_production_pins_match_results_document` (稿 §5.1、外部 root が無くても走る)、`test_real_evidence_matches_results_document_when_root_present` (外部 root 不在だけ skip。稿 §2.2 / §2.3 / §2.6 の表セルとの逐語一致、実 Figure の layout)。
- 着地 test `test_landed_fig15_repo_closure_and_caption_when_present` (fig13 版と同型、`LANDED = "docs/paper-story/figures/fig15_mocc_witlight_four_arm"`、bundle 未着地は skip でなく失敗、外部 root の有無で skip しない) と
  `test_landed_fig15_external_closure_when_root_present` (外部 root 不在だけ skip)。**親が着地させるまで fig15 の着地 test 2 本は赤になる。それは期待赤であり、報告に「未着地のため赤」と書けばよい (xfail 化・skip 化しない)。**
- matplotlib の実描画は 4〜5 回以内 (layout 正例・artist 照合・可視開示・CLI・禁止句負例)。数値 test では Figure を作らない。
- 末尾に `_run()` harness と `if __name__ == "__main__": sys.exit(_run())` (既存 `orchestrator/tests/test_plot_a1_sized_paired.py` の末尾と同型、`skiputil.Skip` / `skip` を使う)。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

matplotlib の cache dir が書けない場合は `MPLCONFIGDIR=probe-fig15/.mplconfig` を付けて走らせる。

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (self-run harness)。着地 test 2 本以外が全部 passed (外部 root は読めるはずなので skip 0 を目標) であること。所要 (wall 秒) も報告する。
2. 実データ実走 (FIGURE_CONVENTIONS §10): `python3 tools/plotting/plot_mocc_witlight_four_arm.py probe-fig15/fig15_mocc_witlight_four_arm` が rc=0 で png / pdf / provenance.json を出すこと。
   provenance の arm 別 k/m・率・CP・commit 平均・比・Fisher p を稿 §2.2 / §2.3 / §2.6 と照合し、caption 全文と図中の可視 text の一覧を報告に写す。
   生成した provenance を `validate_repo_closure(prov, <worktree root>)` と `validate_external_sources(prov, EVIDENCE_ROOT)` に通し例外が出ないこと。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` と、test file の列挙・命名に制約を課す他の meta-test (`orchestrator/tests/` を自分で `grep -l` して洗い出す) を走らせる (F42)。
4. 構文確認 (`python3 -m py_compile`)。`_python_has_perf_predicate` を新生成器の source に当てて False を確かめる。guard で拒否された command はその旨を書く。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個)

## 実装した物
file ごとの要点 (定数・入力検査・集計・書式・図の形・注記・caption の構成・provenance の key・2 つの closure)。
## 実走した検査
nodeid と passed / failed / skipped 件数、所要。実データ実走の rc と 3 成果物の path、稿との照合結果、caption 全文、可視 text 一覧、closure 2 関数の結果、meta-test・perf 走査の結果。
## 未実走・期待赤
走らせられなかったもの、着地前に赤の test 名。
## 受理・拒否の含意
受理する入力 (この 5 本の bytes、または同じ schema・同じ格子で再計算が summary と一致する fixture) と拒否する入力 (各 1 文)、通る正例 1 つ。
## 所有外への波及
所有外の caller・共有 fixture・consumer test・列挙型 meta-test への影響の静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
段 4 裁定の表の M6〜M13 (本単位の分) について、どの test (nodeid) が殺すか。前後に同じ入力を拒否する層があって単一理由にならない変異があれば指摘 (分割案を添える)。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
