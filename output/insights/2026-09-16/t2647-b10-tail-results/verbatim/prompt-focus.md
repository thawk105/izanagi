単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results

## 必読事項の射影

これは自分たちの論文材料 (統制稿) の、fix 後の焦点再レビューである。次の絶対パスだけを読む。**この射影に
挙げた file が読めなければ即停止し、その旨を出力に書く。** 停止規則の射程はこの射影 file に限る — 自分で探した
path が不在でも、それは停止理由にしない。差分は commit 前の作業ツリーであり、親が 2 本のレビュー所見
(下記) を反映した後の版である。

**レビュー対象 (fix 後の版)**

1. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`
2. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/paper-story/README.md` の
   「results 系列（`results/` サブディレクトリ）」節の表の `2026-09-16-b10-static-tail-not-observed` の行

**fix 前のレビュー出力 (所見の原文)**

3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-results/review-a-out.md` (数値・逐語検算。nit 1 件)
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-results/review-b-out.md` (主張範囲。must-fix 1、should-fix 3)

**照合に使う正本**

5. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/docs/b10-backoff-static-tail-preregistration.md`
   (§0、§3、§4.4、§7、§9)
6. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-results/output/insights/2026-09-16/b10-tail-formal-submit/README.md`
   (§3.1、§3.2)
7. `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.json`
   (限定 15 の「意味 witness の field は無い」の検算用。`meaning_witness` の語が 0 件か)

## 親が反映した fix (5 件)

| # | 所見 (出所) | 親の対応 |
|---|---|---|
| F1 | review-b 所見 4 (must-fix): D2050 への明示的言及が「触れない」に反する | §0.3 と限定 9 から D2050 と「再現・置換・併記」の語を除き、「本稿は 09-15 の 1 本の cohort だけを扱う」だけを残した |
| F2 | review-b 所見 1 (should-fix): 事前登録 §0 の更新契約違反の引継ぎ漏れ | §1.1 に、追補が §0 の更新契約を満たしていないこと、ただしそれを §7 の失敗条件 12 や `invalid` へ読み替えないことの両面を追記した (insight 6 の §3.2 を出所に) |
| F3 | review-b 所見 2 (should-fix): 物理量の意味 witness の限定が無い | 限定 15 を新設。§1.2 の対応表が独立の pointwise meaning witness を確立するものではない (事前登録 §3)、成果物に意味 witness の field は無い (実測)、既存 sweep 系列と同じ境界で弱めも強めもしない、と書いた |
| F4 | review-b 所見 3 (should-fix): 探索後に選んだ事項の開示が一部欠落 | 限定 12 に、格子の位置と刻み幅、域内非飽和を正当な結末に含める選択も探索後だったこと (事前登録 §0) を加えた |
| F5 | review-a nit: §2.2 の引用が非逐語 (`U ≤ 0.05`) | 原文表記 `U_i <= 0.05` へ戻した |

付随: 限定が 14 件から 15 件になったので README 行の「限定 14 件」を「限定 15 件」へ更新した。

## やること

1. **所見ごとに closed / partial / regressed を判定する対応表**を作る。表なしで閉じたと言わない。
   各行に、稿の該当箇所を逐語 (1 文以内) で引く。
2. F2・F3・F4 の追記文が**出所 (事前登録 §0・§3、insight 6 の §3.2) を超えていないか**を照合する。
   特に F3 で「現在も一律に未確立」と断定していないか (追補は §9 の「未確立」を追補前の記述として保持する)。
   F2 で「§7-12 に当たらない」の根拠が insight 6 §3.2 の逐語と整合するか。
3. F1 の除去後、稿に D2050・「再現」・「置換」・「併記」の語が残っていないか、また除去によって
   §0.3 と限定 9 の文が意味を失っていないか。
4. F5 の引用が事前登録 §4.4 の原文と 1 文字ずつ一致するか。
5. fix が**新しい主張・新しい数値・新しい限定の過剰**を持ち込んでいないか (regressed の検査)。
   限定 15 の「集団報告と campaign lock に意味 witness の状態を記録する field は無い」は、file 7 で
   `meaning_witness` の語を数えて確かめる。
6. README 行の「限定 15 件」が稿の連番と一致するか数える。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定・図・gate・検査を提案しない。fix 前のレビューが出していない新規所見は、regressed の検査で
  見つかった fix 由来のものに限る。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 所見ごとの対応表
## fix の出所整合
## regressed の検査
## 総括
