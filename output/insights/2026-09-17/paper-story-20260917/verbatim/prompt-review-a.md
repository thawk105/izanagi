単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/2026-09-17.md (**レビュー対象の新版**、289,737 bytes / 2,659 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### \|^#### "` で節の位置を出し `sed -n` で 200 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/README.md (**レビュー対象。版の履歴表・訂正一覧・stale 注記の 3 節が更新された**)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/ruling-s4.md (段 4 裁定。新版が従うべき裁定)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/codex/consult-a-out.md (段 3 レンズ A の所見)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md (37,670 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/output/insights/2026-09-16/t2698-official-floor-resubmit/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/output/insights/2026-09-16/t2630-scan-boundary-reach/README.md

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,248,926 bytes / 64,167 行、`docs/failures.md` は 2,661,806 bytes、
`docs/worklog.md` は約 130 KB、前版 `docs/paper-story/2026-09-14.md` は 229,235 bytes。**全文 `cat` してはならない。**
`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。`wc -c` / `wc -l` は許す。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新版の本文と README の 3 節を書いた。段 2 plan と段 3 の 2 レンズは骨格を検査し、
その所見は段 4 裁定 (`ruling-s4.md`) に反映済みである。**お前は本文に対する敵対レビューである。**
親が実走した検査: `tools/check_docs.py` rc=0、三軸語走査 (`s8b_holdout_freeze search`) rc=0 (holdout hit 0)、
`git diff --check` rc=0、本文が引く `output/` 55 path と `docs/` 18 path の実在確認 (不在は予定仕様の fig8 と
template 記法だけ)、§7 の件数 (前半 58 / 後半 9)、§0 の 14 点、§2 (g) の 11 点、冒頭の訂正 3 件の検算。

## お前のレンズ — 一次資料との照合、母集合、射程、件数

1. **数値・日付・判定を一次資料と照合せよ。** 新版が書く数値のうち、少なくとも次を権威 bytes / record / D 本文で
   検算せよ: official 床値の floor 案 (rr20 / rr80 の値、scale_ref、u_noise の範囲、配線下限 0.03、12 cell、CV 範囲、
   registry 481 行、admit +12 / consume +96、Elapse、request ID、初投入日 09-09 22:09 JST、`ce2769c32` の祖先性)、
   右 tail (group id、verdict、18 区間、8 点の格子、throughput と abort 率の表、SHA-256、`performance_certified`、
   120 記録、legacy 条件)、較正 record (8 件の内訳、rr5 の records / LLC miss / CV、非 silo 4 対の値)、
   T-2630 (5 変異の名前と種別、M4 / M4b / M6 の性質、F1016、[T-2731]、entry 1580)、K2 (job、tps、CV、proposal-2)、
   B-4 (binary bytes、record path、配置規則)、8c §5 (9 欄中 8 欄未記入)、D2044 の項番号と内容 (項3・8・9・11・12・
   13・14・25・36)、A-2 / A-6 / T-1998 の値 (前版と同じはず)。
2. **母集合と射程。** 新版が「certified」「accepted」「completed」「そろった」と書く箇所で、母集合が広すぎないか
   (例: T-2630 の 5 変異を実行差と読ませていないか、tail の correctness を性能条件の認証と読ませていないか、
   較正の `accepted` を correctness と混ぜていないか、B-7 を充足と読ませていないか)。
3. **件数・量化。** 「すべて」「だけ」「例外なく」「N 件」「N 稿」「N record」を原データから数え直せ。
   特に §5 の「results 系列は 7 稿」、§0 の「14 点」、§2 (e) の「5 度」「5 つ」、§9 の「7 種」。
4. **path と参照。** 本文が引く一次資料の path・D 番号・T 番号・F 番号・entry 番号が実在し、内容が本文の記述と
   合うか (特に D2016 / D2026 / D2027 / D2049 / D2050 / D2053 / D2069 / D2072 / D2077 / D2083 / D2044 の各項)。
   行番号参照が無いことも確かめよ (basename / 節名参照が規則)。
5. **凍結物の不変。** `git status` / `git diff --stat` で、変更が `docs/paper-story/README.md` (更新) と
   `docs/paper-story/2026-09-17.md` (新規) の 2 file だけであること、旧版・`results/`・`figures/`・
   `claim-evidence/`・`docs/paper-story-backoff/` に差分が無いことを確かめよ。
6. **README の 3 節。** 版の履歴表の新行、訂正一覧 (3 件)、stale 注記 (0 件へ) が新版の本文と食い違わないか。
   results 系列の表 (7 行) と恒久 erratum 節が壊れていないか。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 は充足と書かない。3 走行を pool しない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs の訂正・図の実装も scope 外。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当節 (§番号と小見出し)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新版をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
