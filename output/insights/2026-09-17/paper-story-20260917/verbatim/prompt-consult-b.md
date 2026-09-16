単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/brief.md (親の段 1 brief。**攻撃対象**)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/codex/plan-out.md (段 2 の plan。**攻撃対象**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/README.md (33,959 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/2026-09-14.md (229,235 bytes / 2,310 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### "` で節の位置を出し `sed -n` で 200 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/output/insights/2026-09-16/t2647-b10-tail-downstream.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/tools/plotting/FIGURE_CONVENTIONS.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260917/docs/paper-story/figures/README.md

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,248,926 bytes / 64,167 行、`docs/failures.md` は 2,661,806 bytes、
`docs/worklog.md` は 98,430 bytes。**全文 `cat` してはならない。** `grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。
D2044 (全 39 項、2026-09-16) は `sed -n '62083,62507p' docs/decisions.md` で読める (本 wave の HEAD での行番号)。
archive worklog は `docs/archive/worklog-phase3-09*.md` を entry 番号で選んで読め。`wc -c` / `wc -l` は許す。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない。静的な読解と照合だけでよい。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## お前のレンズ — 主張の強さ、非対称性、裁定の先取り、scope

親は `docs/paper-story/2026-09-17.md` (最新版 2026-09-14 の全面再導出) を書こうとしている。
プランを守らせるな。**プランと親 brief の両方を攻撃せよ。** お前のレンズは次の 4 つである。

1. **主張の強さ。** 新版の headline (brief の (P2): 「肯定的 headline 主張は増えていない。増えたのは official 床値の初の実値・
   B-10 右 tail の集団判定・B-7 材料・非 silo 較正・B-4 の材料・層 3 の訂正」) が、正典に照らして過大か過小かを判定せよ。
   特に **official 床値の実値 (rr20 = 35,817.945 / rr80 = 46,065.78、両 holdout とも配線下限 0.03 × stock 中央値)** を
   §9 の 7 種の表のどこへ置くべきか — 「限定付きで取れた観測」か「運用上の証拠」か — を一次資料
   (`output/insights/2026-09-16/t2698-official-floor-resubmit/README.md`、D488、D811、D2077) で判定せよ。
   「床は配線下限で決まっている」という事実が、床値という量の意味 (D1639 / D1641) にどう効くかを書け。
2. **非対称性と二重計上。** §9 の 7 種の表で、同じ観測が 2 種へ置かれる危険、性能と correctness が混ざる危険を挙げよ。
   B-10 tail の `not-observed-in-any-workload` は「正式走の判定」か「非正式」か (事前登録に束縛された cohort だが
   `performance_certified: false`、`official_certification` は?)。B-7 の 3 走行材料は表に載せる新しい観測ではない
   (既存 3 走行の併記) ことを確認せよ。
3. **裁定の先取り。** 親 brief と plan が、ユーザー裁定に属する判断を版の中で先取りしていないか。
   特に (P1) 図の置き場所を「本版が定める」ことは、`figures/README.md` の契約と D1637 (2 本目の論文との境界) の
   範囲内か。(P4) T-2630 を exact claim の限定へ足すことは、裁定待ち ({{T:scan-boundary-directive-leak-fix}}) を
   先取りしないか。(P5) README の「最新スナップショット以後に確定したこと」を 0 件へ戻すことは README 契約と
   D1858 に沿うか。B-7 について D2044 項3 (要件充足へ昇格させない) を版がどう書くべきか。
4. **scope。** 依頼は「本題の版だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
   plan と brief が scope を超える提案 (隣接 docs の訂正、新しい検査、図の実装) をしていないか。
   逆に、依頼が求めた「§8 の A/B 群の状態欄を現物で埋める」と「README の stale 注記 3 件を本文へ取り込む」が
   欠けていないか。

## 親の暫定裁定 (brief.md の (P1)〜(P5)) と plan の結論

それぞれについて real / refuted を判定し、real なら一次資料を指した対案を書け。
plan が親に同意している箇所ほど疑え。

## 守らせる不変条件 (これを緩める提案は refuted として扱う)

- 凍結物 (旧版・`results/`・`figures/`・`claim-evidence/`・backoff 系列) は 1 byte も変えない。
- 旧 attempt の判定を取り消さない (絶対規律 7)。前後比較として読ませない。
- protocol status は研究の成否宣告ではない (D12)。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。`performance_certified: false`。
- B-7 は充足と書かない (D2044 項3)。3 走行を pool しない (D1993 項 6)。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。提案してはならない。

## 出力形式 (この見出しをそのまま使う)

## 所見 (主張の強さ・非対称性)

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、一次資料の path または D 番号、対案を書け。

## 所見 (裁定の先取り・scope)

同上。

## 親の暫定裁定への評価

(P1)〜(P5) と plan の総括に対して 同意 / 不同意 (一次資料つき)。

## GO / NO-GO

新版の骨格 (plan + brief) で執筆に入ってよいか。NO-GO なら最小の修正を書け。

## 総括

10 行以内。
