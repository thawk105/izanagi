単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/brief.md (親の段 1 brief。**攻撃対象**)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/codex/plan-out.md (段 2 の plan。**攻撃対象**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/README.md (33,959 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/2026-09-14.md (229,235 bytes / 2,310 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### "` で節の位置を出し `sed -n` で 200 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md (37,670 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/spool/worklog/2026-09-16-dev-wave-t2630-scan-boundary-reach-1.md

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,248,926 bytes / 64,167 行、`docs/failures.md` は 2,661,806 bytes、
`docs/worklog.md` は 98,430 bytes。**全文 `cat` してはならない。** `grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。
archive worklog は `docs/archive/worklog-phase3-09*.md` を entry 番号で選んで読め。`wc -c` / `wc -l` は許す。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない。静的な読解と照合だけでよい。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## お前のレンズ — 正しさ境界と、古い記述の引き写し

親は `docs/paper-story/2026-09-17.md` (最新版 2026-09-14 の全面再導出) を書こうとしている。
プランを守らせるな。**プランと親 brief の両方を攻撃せよ。** お前のレンズは次の 2 つである。

1. **正しさ境界。** 新版が「certified」「certified の限定」「性能値」「protocol status」を書くとき、
   正しさの緑が性能へ染み出す文、限定が落ちる文、判定を取り消す文、旧値と新値を pool する文が
   入りうる箇所を、一次資料 (権威 bytes・decisions 本文・事前登録) で指して挙げよ。
   **特に (P4) — [T-2630] の走査境界の穴 (`#define`/`#undef` が identity に乗らず 5 変異で identity 同一のまま
   別 TU) を §8 exact claim の (正しさ) に限定 (v) として足す親の案 — が、A-2/A-6 の `src_token` 束縛の主張を
   どこまで弱めるべきかを一次資料で判定せよ** (insight `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md`)。
   到達したのは template patch を carrier にした経路で、A-2/A-6 は無変異の template で走っている。
   限定 (v) が過大か過小かを書け。
2. **古い記述の引き写し。** 最新版 (09-14) の記述で、2026-09-17 の正典に照らして**誤り** (当時から偽) と
   **stale** (当時は真・今は古い) を、親と plan が挙げた以外に探せ。親が把握しているのは
   「層 3 screening の 6 箇所 (当時から偽)」「B-10 tail の 5 箇所 (stale)」「official 床値 A-4 (stale)」だけである。
   §5 の「見落とされがちな素材」と §7 の 58 項は特に引き写しが起きやすい。
   D 番号・T 番号・日付・件数 (例: 完了証明層 1/12、較正 record の件数、限定の件数) を現物で数え直せ。

## 親の暫定裁定 (brief.md の (P1)〜(P5)) と plan の結論

それぞれについて real / refuted を判定し、real なら一次資料を指した対案を書け。
plan が親に同意している箇所ほど疑え — 3 者が同じ誤りを共有していることが前 wave (entry 1485・1544) で起きている。

## 守らせる不変条件 (これを緩める提案は refuted として扱う)

- 凍結物 (旧版・`results/`・`figures/`・`claim-evidence/`・backoff 系列) は 1 byte も変えない。
- 旧 attempt の判定を取り消さない (絶対規律 7)。前後比較として読ませない。
- protocol status (`observed-positive` / `reject` / `accepted` / `not-observed`) は研究の成否宣告ではない (D12)。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。`performance_certified: false`。
- B-7 は充足と書かない (D2044 項3)。3 走行を pool しない (D1993 項 6)。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。提案してはならない。

## 出力形式 (この見出しをそのまま使う)

## 所見 (正しさ境界)

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、一次資料の path または D 番号、対案を書け。

## 所見 (引き写し・誤り・stale)

同上。誤り (当時から偽) と stale (当時は真) を分けよ。

## 親の暫定裁定への評価

(P1)〜(P5) と plan の総括に対して 同意 / 不同意 (一次資料つき)。

## GO / NO-GO

新版の骨格 (plan + brief) で執筆に入ってよいか。NO-GO なら最小の修正を書け。

## 総括

10 行以内。
