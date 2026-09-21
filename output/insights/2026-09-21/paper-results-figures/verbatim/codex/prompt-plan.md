単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、その旨だけを `## 総括` に書いて終わる (射影 file 限定の停止規則で、自分が推測して探した path の不在は停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md` — 親の段 1 brief (研究前進・確定済み裁定・provisional 裁定 P1〜P8・不変条件・描かないもの・scope 外・成果物・分割方針)。**plan はこれに従う**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-pin-closure.md` — 親が調べた pin 閉包 (変更 file を照合する test・台帳、新規 test の登録要否)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/origin.md` — 依頼文の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/D2194-item6.md`、`D1752-D1753.md`、`fig9b-wave-RESOLVED.md` — 裁定の逐語と、先行 wave (2 attempt 並記図、作らないと再裁定) の終端記録
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/attempt2-doc-head-s0.md`、`attempt2-doc-s2.1.md`、`attempt2-doc-s2.6-2.7.md`、`attempt2-doc-s3.md`、`attempt2-doc-s5.1.md` — 図 (1) の caption_source (attempt-0002 稿) の該当節
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/witlight-doc-head-s0-s1.md`、`witlight-doc-s2.md`、`witlight-doc-s3-s4.md`、`witlight-doc-s5.md` — 図 (2) の caption_source (mocc witlight 稿) の該当節。§2.2 / §2.3 / §2.6 の表が「逐語で使う値」
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/figures-README-head.md`、`figures-README-fig9.md`、`figures-README-fig13.md`、`plotting-README-a1.md`、`plotting-README-fig13.md` — README 2 本の現行節 (fig9 = 図 (1) の兄弟、fig13 = repo 外証拠を束縛する先例)
- repo 内 (worktree の path、read-only):
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/tools/plotting/plot_a1_sized_paired.py` — **拡張対象の生成器** (全 472 行、全文を読む)
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/orchestrator/tests/test_plot_a1_sized_paired.py` — **拡張対象の test** (全 554 行、全文を読む)
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/tools/plotting/plot_b10_waiting_grid_forest.py` と `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` — repo 外証拠 (`--evidence-root`、`EXTERNAL_SHA256`、`external_inputs`、`validate_external_sources`、`test_real_evidence_loads_when_root_present`) の先例。`grep -n` で位置を出し 200 行以内ずつ読む
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/tools/plotting/plot_b10_static_tail_formal.py` — 1 生成器で cohort を CLI (`--reproduction-cohort`) で選ぶ先例。該当箇所だけ部分読み
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/tools/plotting/FIGURE_CONVENTIONS.md` — 作図規約 (全 131 行)
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json` — 着地済み fig9 の provenance (構造だけ。`workloads[].pairs` と `artist_series` の中身は読まなくてよい)
  - `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` の `result.json` (270 KB。**全文 cat しない**。`python3 -c` / `jq` で `workloads[].statistics` と `source_binding` を見る)・`receipt.json`・`.complete.json`
- repo 外 (read-only、図 (2) の権威入力): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json` と `W1/result.json`〜`W4/result.json`
  (各 100〜400 KB 程度。**全文 cat しない**。`python3 -c` / `jq` で key 構造、`runs[]` の 1 件、`bindings` の key、`summary.arms.<arm>`、`inputs` を見る)。
  `smoke/` と `parent-accounting.json` は入力にしない (brief P5)

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures`。上記以外も repo 内を読んでよい。**大きい file を全文 `cat` しない。**

## 前置き — この依頼の性質

対象は研究用 repo の**論文図の生成器 (matplotlib) の拡張・新設と、その図・provenance・test**である。セキュリティでも攻撃でもない。
入力は SHA-256 で束縛した JSON だけである。図 (1) は既存の fig9 (attempt-0001 の記述図、凍結物) と同形の attempt-0002 の単独記述図 fig14、
図 (2) は stock mocc の軽量 witness 4 arm × 60 走 (4 block W1〜W4) の G2 signal 検出率・Clopper–Pearson 区間・曝露量 (commit 数) の図 fig15 である。
fig9 の bytes と着地閉包 test、results 稿・版の bytes は変えない。**2 attempt のプール・差・比・再現判定、mocc の非有意の同等性化、TRACE=1 の曝露量の性能化、
G2 signal の根因化は描かない・書かない。**

## この段の仕事 — file:line 粒度の実装 plan を起草する (実装はしない)

sandbox は read-only で、書込可能 tmp は無い。pytest の実走は要求しない (静的検査でよい。実測は親が行う)。予算が尽きそうなら途中結論を下の出力形式で書いて終わる (無出力が最悪)。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。

plan は brief の不変条件と provisional 裁定 P1〜P8 を前提にし、次を **現物の file:line** で書く。P を覆すべき根拠を見つけたら、plan の中で覆さず `## P の反証` 節に根拠 (file:line・実測値) とともに書く。

1. **図 (1): `tools/plotting/plot_a1_sized_paired.py` の変更点** — 関数ごとに「現行の行範囲 → 変更後の形 (signature・定数・主な文)」。少なくとも次を決める:
   - attempt ごとの repo 所有 exact pin 表 (attempt-0001 = 現行 `LEAF_DIR` / `PINNED_SHA256` 4 件 / `CAPTION_SOURCE` を**名前・値・dict の挿入順ごと保持**、attempt-0002 = 稿 §5.1 の SHA-256 を写す)。`expected_hashes` seam の key 集合が attempt ごとに決まること
   - `_load_leaf` の `variance_plan_breach` 検査を attempt 別にする形 (attempt-0001 は現行の `is False` 拒否を維持、attempt-0002 は述語一致で受理)
   - `load_leaf` が返す dict の key 集合: **attempt-0001 の返り値は現行と key・値が完全一致**でなければならない (着地 fig9 の `validate_repo_closure` が `provenance[key] == value` を全 key で要求するため)。attempt-0002 側に key を足す場合も、attempt-0001 の返り値に key を足さない形を示す
   - caption: attempt-0001 の `_caption` の出力文字列は 1 文字も変えない。attempt-0002 用の caption は、workload ごとの `variance_plan_breach` (true/false) と sd・planned sigma の併記、単一 attempt・非認証 lane・headline でない・workload 横断なし・C1 の再現でない・**attempt-0001 とプールも比較もしない (差・比・再現判定なし)**・breach の原因を帰属しない、を固定文で含む。図番号は prefix から (D1753)
   - `make_figure`: attempt-0002 の panel に `variance_plan_breach` を出す形 (panel 題の 2 行目か axes 内の text か。layout 検査 `check_figure_layout` を通ること。attempt-0001 の描画 (fig9) は変えない)
   - CLI: `--attempt` (P2) の追加位置、`main` の展開済み argv (attempt-0001 の場合の argv 形を現行と同じに保つか)、`validate_repo_closure` / `build_provenance` の attempt の扱い
2. **図 (1) の test `orchestrator/tests/test_plot_a1_sized_paired.py`** — 既存 test をどれも弱めずに足す test の一覧 (名前・何を検査するか・fixture の形)。少なくとも: attempt-0002 の pin と稿 §5.1 の一致、real leaf と稿 §2.1 の一致 (breach 列を含む)、attempt-0002 の breach true 受理と attempt-0001 の breach true 拒否の維持、attempt-0002 caption の固定文と禁止語、fig14 の着地閉包 (fig9 の着地 test と同型、README の fig14 節の hash 行と caption 収録)、fixture は FIGURE_CONVENTIONS §10 の実寸 (3 workload × 30 対 × 2 arm)
3. **図 (2): 新規 `tools/plotting/plot_mocc_witlight_four_arm.py`** — fig13 の生成器を雛形にした関数構成 (load / make_figure / check_figure_layout / build_provenance / validate_repo_closure / validate_external_sources / _publish_outputs / main)、定数 (5 file の SHA-256 = 稿 §5.1、`EVIDENCE_ROOT` 既定、arm 名 4 つと順序、BACK_OFF / witness の対応、block 4 つ、rounds 15、planned 60)、
   `runs[]` から再計算する量 (arm 別 N / m / k / failure / indeterminate / decisive_m、CP 両側 95%、片側 Fisher p、走あたり commit 数の平均、on/off 比) と `summary.json` との照合、`summary.json.inputs` が W1〜W4 の 4 件と exact 一致することの検査、
   書式化 (稿 §2.2 の `0/60`・`1.667%`・`[0%, 5.963%]`・`[0.042%, 8.940%]`、§2.3 の `0.500`、§2.6 の `613,741.5`・`0.8636` などと同じ文字列)、
   図の形 (P7: 2 panel)、caption の固定文 (非有意 ≠ 同等性、設計仮定下の検出力 0.105 は計算値、TRACE=1 の曝露量 ≠ 性能、G2 signal ≠ 根因、非 certifying、smoke を分母に入れない、4 block × 15 round × 4 arm) と禁止語、provenance の field (`external_inputs` と `tracked_inputs` を分ける)。
   CP・Fisher の計算を scipy 無しで行う方法 (FIGURE_CONVENTIONS §8 は matplotlib / numpy のみ。Beta 分位を二分法で解く等) と、その精度で稿の丸め表記に一致すること
4. **図 (2) の test 新規 `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`** — 実寸 fixture (4 block × 60 走 = 15 round × 4 arm、回転、G2 signal 2 走を含む、smoke を含めない)、本物の Figure を layout 検査へ通す test、hash drift 拒否、summary 不一致拒否、smoke 混入拒否、caption の固定文・禁止語、稿 §2 の表との逐語一致 (実証拠が在るときだけ)、着地閉包 (repo 内の検査と repo 外の検査を分ける、fig13 の `test_external_sources_and_repo_closure_have_separate_roots` 型)
5. **新規 test の登録** — `s1-pin-closure.md` の結論に従い、登録が要る台帳・設定があれば file:line と追加行の形を書く。要らないなら「要らない」と根拠を書く
6. **親が書く docs の骨子** — `docs/paper-story/figures/README.md` の一覧 2 行と fig14 / fig15 節の見出し構成 (fig9 / fig13 節と同じ小見出し順)、`tools/plotting/README.md` の 2 節の骨子。本文は親が書くので骨子だけでよい
7. **変異候補** — 段 4 で事前登録する候補を 8〜12 件。各候補に「変える file:line・変え方・kill するはずの test 名・単一理由である根拠」。
   少なくとも: attempt-0001 の breach 拒否の除去、attempt-0002 の pin の 1 文字変更、attempt-0001 caption の 1 語変更 (fig9 着地 test が kill)、attempt-0002 caption の固定文除去、mocc の SHA-256 定数 1 文字変更、`summary.json.inputs` の exact 照合除去 (smoke 混入)、CP 上限の計算の破壊、Fisher の片側/両側の取り違え、commit 数平均の分母の誤り、layout 検査の無効化、等価対照 (コメント追加で SURVIVED 予測)
8. **想定される落とし穴** — 実寸 fixture の生成で遅くならないか (test 全体の所要の見積もり)、matplotlib の layout で panel 題が長くなる件、`fig14_` / `fig15_` の prefix、login node での font 解決

## 出力形式

次の見出しで書く。各節は file:line を含む箇条書きか表。推測は「未確認」と明記する。

```
## 1. 図 (1) 生成器
## 2. 図 (1) test
## 3. 図 (2) 生成器
## 4. 図 (2) test
## 5. 新規 test の登録
## 6. docs の骨子
## 7. 変異候補
## 8. 落とし穴
## P の反証
## 総括
```

`## 総括` は 5〜10 行で、plan の要点と、brief の P のうち採用・反証したもの、未確認のまま残ったものを書く。
