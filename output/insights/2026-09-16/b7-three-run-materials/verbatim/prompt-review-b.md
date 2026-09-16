単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

**レビュー対象 (これが本題)**

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md`
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/README.md` の
   「results 系列（`results/` サブディレクトリ）」節 (2026-09-16 の行が今回の追加)

**判断の基準になる資料**

3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1631.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1993.md`
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1986-1to5.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1874.md`
7. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-b7-item.md` (版 §8 の B-7 項の逐語)
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/figures/README.md`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/phase3-main-experiment.md` の「失敗条件」節
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/t1998-balanced-stock-inline-preregistration.md`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/CLAUDE.md` の「絶対規律」節

必要なら次も読んでよい (任意、読めなくても停止しない)。

- 同 worktree の `docs/decisions.md` (`D1631` / `D1993` / `D1986` / `D1874` / `D12` / `D1645` を見出しで検索)

## レンズ

**主張の過大さ・限定の欠落・規律への抵触・凍結境界。** 「この稿が、資料が言っていないことを
言っていないか」「言うべき限定を落としていないか」だけを攻める。
数値そのものの検算は別のレビュー子が担当するので、そちらへは踏み込まなくてよい。

## やること

1. **集計に読める箇所を探す。** D1993 項 6 は「A-2 / A-6 / balanced stock-inline 対の 3 走行を
   1 つの横断実験として集計しない」と定める。**主表の列の取り方、行の並べ方、脚注の位置、
   前文の言い回しのどこかで、3 走行が 1 つの実験に見える箇所が無いか。**
   A-2 の outer status が 2 workload の論理積であることが表で潰れていないか。
2. **B-7 の充足を先取りしていないか。** 稿は充足を宣告しないと書くが、**「3 走行そろった」
   「材料がそろった」という言い回しが事実上の充足宣言になっていないか。** B-7 の要件充足の扱いは
   未裁定である。
3. **絶対規律への抵触。** 規律 1 (観測者効果の分離)、規律 2 (正しさゲートを緩めない)、
   規律 7 (測定時点の事実と現行コードへの適合を分ける) に照らして、稿が踏み越えている箇所が無いか。
   **特に、正の効果と `accepted` / `observed-positive` の併記が variant 採用の許可に読める経路。**
4. **限定の過不足。** 稿の §3 は 19 件ある。**資料が言っていないことを言っている限定 (過剰)** と、
   **資料が言っているのに落ちている限定 (不足)** を探す。特に [T-1998] 固有の限定
   (consumer 是正で受理集合が広がったこと、toolchain の穴、compiler 同一性、事前登録前の生値) が
   資料の書きぶりに収まっているか。
5. **凍結境界。** 稿と入口の行が、既存の凍結物 (2026-09-14 稿、版、figures、事前登録) の
   bytes・意味・用途制限を変えてしまう経路が無いか。**旧 fig5 の用途制限 (期限なし) を緩めないか。**
   既存稿を「誤りを直した」と読ませる書き方になっていないか。
6. **裁定の帰属。** 稿が D1986 項 5 / D1993 各項 / D1874 / D1631 を引いている箇所で、
   **その裁定が実際に定めている範囲を超えて使っていないか。** 逐語と突き合わせる。
7. **稿が自分で立てた約束を守っているか。** 冒頭で「書かないもの」と宣言した項目を、
   本文のどこかで書いてしまっていないか。**§0.3 の一覧と本文を突き合わせる。**
8. **入口 README の 1 行**が、既存 5 行の書式・列の意味と整合するか。読者が
   「新稿が旧稿を置き換えた」と誤読しないか。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- B-7 の充足・不充足を宣告する案を出さない。
- 所見が無いなら「無い」と根拠つきで書く。検査したことを書かずに「問題なし」とだけ返さない。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物 (統制稿・入口の表・下流の執筆) の値・受理集合・参照がどう変わるか**を 1 行で書く。

## 集計に読める箇所
## 充足の先取り
## 絶対規律への抵触
## 限定の過不足
## 凍結境界
## 裁定の帰属
## 自己約束との整合
## 入口 README の 1 行
## 総括
