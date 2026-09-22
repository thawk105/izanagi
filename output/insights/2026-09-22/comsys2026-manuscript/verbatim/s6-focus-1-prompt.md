単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-comsys2026-manuscript

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 前段のレビュー出力 (所見の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/codex/s6-review-A.md (版) と同 dir の s6-review-B.md (原稿)
- 依頼文の逐語と親 brief: 同 job dir の `verbatim-request.md`、`s1-brief.md`
- 親の fix: 投入先 worktree の commit `2aa318ba7a233fdb5225dee07a4640f84922d5d8` (親 = レビュー対象だった `d18b073abe2d8957c26827cd062d2e4a5e6cbcec`)。差分は
  `git diff d18b073ab 2aa318ba7 -- docs/paper-story/2026-09-22.md output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex` で読める。
  版の fix の置換案は job dir の `story/edits-S6A.json`・`story/edits-S6A2.json`、原稿の fix は job dir `build/` の断片と `fix_s6b_should.py`・`fit_pages.py`・`add_post_origin_notes.py`。
- 親の再検査: job dir の `numcheck-2.log` (最終 tex の数値 136 token、未検出は参考文献の頁 1 件)。組版は 14 頁・エラー 0 (親の実測)。
- 一次資料 (前段と同じ): `docs/decisions.md` (D2211 項 1・項 5、D2212)、`docs/b8-final-candidate-longrun-verify-preregistration.md` §6.1、
  `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md`、`docs/paper-story/figures/README.md` (fig2b・fig4・fig9・fig13・fig14・fig15 節)、
  `output/insights/2026-09-20/t2797-b5-contrast/README.md`、`output/insights/2026-09-21/paper-results-figures/README.md`、archive の entry 1803・1808・1809。

## 前置き

研究用 repo (トランザクションの並行性制御を LLM で合成する研究) の論文ストーリー文書と、国内シンポジウムの日本語原稿について、前段の敵対レビューの所見を親が直した。
その fix が所見を閉じたか、新しい誤りを入れていないかを点検してほしい。セキュリティ製品でも攻撃ツールでもない。あなたは read-only で、書込可能な tmp は無いので静的読解と grep でよい。
閉じていない所見は正直に partial / regressed と書け。

## 点検すること

1. **対応表 (必須):** レビュー A の M1・M2・M3・S1・N1・N2 とレビュー B の M1・M2・M3・S1〜S7・P1 の各所見について、`closed` / `partial` / `regressed` / `不採用 (親の判断が妥当 / 不当)` を 1 行ずつ、
   根拠 (fix 後の行番号と一次資料) つきで書く。親は A の N2 (重複) と B の P1 (頁数) と S6 (書誌の取得未確認フィールド) と S7 (再組版 README) を本 commit では直していない — S6・S7 は段 7 で原稿 dir の README に書く予定である。
   その扱いの妥当性も判定せよ。
2. **親が足した派生値・量化の検算:** 原稿の「36 セル中 32 が内側 (うち 18 は参照セルで区間 [0, 0])，4 が境界を跨ぎ，完全に外側のセルは 0」、B-8 の失格条件の書き換え、
   版の「運用側の診断の計測 (entry 1803・1808・1809)」の件と計算ノード / login の区別、fig15 の「4 block × 15 round × 4 arm = 240 走」を一次資料から再計算・再照合するまで closed としない。
3. **新しい誤り:** fix の文が新しい過大主張・状態語の取り違え・時点の取り違えを入れていないか。特に、原稿の今後の課題 (c)・(d) と 4.7 節の書き換え、内部語の定義文 (protocol・campaign・attempt・arm・cohort・witness)、
   版 §10 の段 6 の記録 (レビュー A の結果を正しく要約しているか)。
4. **採用時点より後の着地:** 原稿の 2 か所に置いた LaTeX 注釈 (entry 1823: K2 の同一 job pair 再投入が成立) が本文の主張を変えていないこと (注釈は PDF に出ない)、版と原稿の採用時点 (`8fd2a2f5c`) の扱いが一貫しているか。

## 出力形式

- 見出しは `#` 1 段だけを使い、`##` は最後の `## 総括` のみ。`### 総括` と書いてはならない。
- 実行できない検査は「未実走・静的読解」と明記する。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- **出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 末尾に `## 総括`: GO / NO-GO、対応表の集計 (closed / partial / regressed / 不採用)、新規の must-fix / should / nit の一覧 (各 1 行、根拠つき)、各 must-fix の最小修正案 (置き換え後の文面)。
