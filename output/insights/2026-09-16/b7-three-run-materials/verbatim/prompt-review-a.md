単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

**レビュー対象 (これが本題)**

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md`
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/README.md` の
   「results 系列（`results/` サブディレクトリ）」節の表 (2026-09-16 の行が今回の追加)

**照合に使う一次資料**

3. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`
4. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json`
5. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json`
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md`
7. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08/t2430-a6-readheavy-mechanism/README.md`
8. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json`
9. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/reservation.json`
10. `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl`
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/t1998-balanced-stock-inline-preregistration.md`
12. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`
13. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`
14. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-15/t1998-landed-main-recheck/README.md`
15. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/phase3-main-experiment.md` の「失敗条件」節

## レンズ

**逐語と数値の検算。** 稿に書いてある値・field 名・引用・SHA-256 が、一次資料の現物と
**1 つずつ一致するか**だけを攻める。主張の過大さや限定の欠落は別のレビュー子が担当する。

## やること

1. **稿の §1〜§4 に現れるすべての数値**を一次資料で検算する。median、生標本 (8 arm × 5 = 40 値)、
   効果量、abort 率、標本標準偏差、CI 半幅、CV、事前登録の版と sha、identity の各 digest、
   host、request、時刻、schema。**一致しないものを名指しする。**
2. **field 名と JSON path が実在するか**を確かめる。稿が「〜という field が記録している」と
   書いている箇所は、その field が現物にあるか。無い field を根拠にしている箇所があれば名指しする。
3. **SHA-256 を自分で再計算**して、稿の §4.1 と §4.3 の値と突き合わせる。
4. **引用が逐語か**を確かめる。稿が資料の文言を鉤括弧で引いている箇所は、現物と 1 文字ずつ一致するか。
   言い換えているのに引用の形にしている箇所があれば名指しする。
5. **「資料がこう書いている」という帰属が正しいか。** 稿は出所を細かく分けている
   (例: A-6 の abort 率は attempt 記録ではなく事後解析にある、[T-1998] の正しさは `result.json` では
   なく campaign WAL にある)。**この帰属が逆になっている箇所、混ざっている箇所を探す。**
6. **入口 README の 1 行**の数値・稿名・列の内容が稿の本文と整合するか。
   特に「限定 19 件」「3 走行・4 対比較・8 arm」が本文の実数と合うか**数えて**確かめる。
7. **桁区切り・丸め・符号**の誤りを探す。百分率の丸めが 4 桁か、全桁転記すべき箇所が丸められていないか。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- 数値を版 (`docs/paper-story/2026-09-14.md`) や既存稿から取らない。**出所は一次資料だけとする。**
- 所見が無いなら「無い」と根拠つきで書く。検算したことを書かずに「問題なし」とだけ返さない。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物 (統制稿・入口の表・下流の執筆) の値・受理集合・参照がどう変わるか**を 1 行で書く。

## 数値の検算
## field 名と JSON path
## SHA-256 の再計算
## 引用の逐語性
## 出所の帰属
## 入口 README の 1 行
## 総括
