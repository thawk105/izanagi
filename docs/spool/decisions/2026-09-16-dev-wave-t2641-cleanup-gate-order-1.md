---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2641-cleanup-gate-order
seq: 1
---

## {{D:cleanup-cheap-gate-first}}. 掃除の判定順は変えるが、削除の述語の連言は変えない

**決定:** `/cleanup-branches` の §1 / §2 を「安い条件を先に判定し、高い判定は通過対象だけに掛ける」
順序へ直す。**変えてよいのは評価順だけ**とし、削除が成立する述語の連言と閾値は 1 つも変えない。
高い判定とは worktree ごとの `git status` と §3 の占有検査を指す。
安い条件とは local main / primary / foreign / locked / 所有不明の除外、HEAD の古さ (目安 1h)、
HEAD の main 取り込み、branch の `ahead=0` を指す。

全 worktree の `git status` は**省略しない**。§4 の事後検査が surviving worktree 全体の
事前 status を要求するためで、これは削除判定の gate とは別の義務である。短縮は
(i) その取得を並列化すること、(ii) 占有検査と削除直前の再確認を安い条件の通過対象だけに
絞ること、の 2 つから来る。**安い条件で落ちた対象の status を省く短縮ではない。**

**理由:**
- 2026-09-15 の実測で worktree 68 件の直列 `git status` が 14.4 分、branch 92 本の判定が約 10 分。
  2026-09-16 の実測では `git status` が 1 worktree 22.0〜37.7 秒、
  `git rev-list --count --left-right` が 0.099 秒、`git cherry` が 0.080 秒。高いのは status だけで、
  branch 側の 10 分は git の費用ではなく 1 対象 1 tool call の呼び出し費用という仮説が立つ
  (1 本の測定からは断定できない)。
- 順序だけを変えれば、削除される対象の集合は変わらない。安い条件で落ちた対象は後続の判定結果に
  関わらず保持されるので、その対象へ高い判定を掛けないことは安全性を落とさない。
- D1231 に従い、到達不能 commit の可視化道具 (`audit_dangling_commits.py` と
  `check_branch_rescue.py --ledger-check`) は §1 と §5 に置いたままとし、§2 へ移さない。
  §2 は `ahead=0` の候補集合に述語が含意されて恒真になるためである。

**却下した選択肢:**
- 安い条件で落ちた対象の `git status` を省く — §4 の事後検査が成立しなくなる。
- §4 の検査範囲を cleanup が触りうる面へ絞る — 掃除の全経路が surviving 面へ到達しないことを
  道具の実装まで読んでも示せなかった。示せない縮小は採らない。
- 撤去の detach・branch 削除・prune まで並列化する — 共有 git metadata を触るため F26 の再発になる。
  並列にしてよいのは path が相互に非包含な directory 撤去だけで、prune は全撤去 process の
  終了・成功を確認した後に限る。

## {{D:cleanup-command-budget-raise}}. 掃除 command の byte 予算は 6204 へ上げ、詳細を failures へ退避しない

**決定:** `tools/check_docs.py` の `COMMAND_LIMITS[".claude/commands/cleanup-branches.md"]` を
`TextLimit(5_900, 110)` から `TextLimit(6_204, 110)` へ上げる (確定本文 6203 bytes + 1 の最小増分)。
§3 手順 3 の撤去手順を `docs/failures.md` F26 へ移して入口を短くする案は採らない。

**理由:**
- D730 / D782 の手順を順に適用した。(1) 既存記述の削減 — §1 / §2 / §3 を縮約し、
  敵対レビューが示した 76 bytes 相当の圧縮を取り込んだ。(2) 実測由来の独立事例は 3 件ある
  (掃除 1 回あたり 25 分超の所要、占有 checker が読み取り argv を占有と数える欠陥、
  裸の `git status` が index を書く欠陥)。(3) 収容先 — cleanup-branches には reference 文書が
  存在せず、自己改善契約が「入口は命令と dispatch、reference は実行手順、failures は
  事象・原因・恒久対応」と定める分担上、`docs/failures.md` は実行手順の収容先ではない。
- §3 手順 3 は**破壊操作の gate** である。常に読まれる入口から pointer の先へ移すと、
  pointer を辿らなかったときに gate が効かない。自己改善契約の
  「予算のために安全義務を削除・弱化してはならない」を、入口の短さより優先する。
- 敵対レビューは F26 への退避で本文 5810 bytes に収まると具体的に示した。この案は
  bytes の点では成立する。採らない理由は bytes ではなく、gate の到達性である。

**却下した選択肢:**
- §3 手順 3 を F26 へ移して既存上限 5900 を維持する — 破壊操作の gate を pointer の先へ移す。
- 縮約だけで 5899 以下に収める — 新しい義務 3 件を削らない限り到達できない。
- 上限を余裕込みで大きく上げる — 一括増枠は自己改善契約が禁じている。
