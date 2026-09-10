# 段 1 brief — next-tasks command の repo 移設 + main 系統 blocker (c12e25078) の前進修正

wave: dev-wave-next-tasks-command-20260908 / branch worktree-dev-wave-next-tasks-command-20260908
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908
base: main c12e25078 (HEAD == main)

## scope
1. `/home/SFC/tanab/.claude/commands/next-tasks.md` (27054 bytes, sha256 10c6c0b4…9ee15) を
   `.claude/commands/next-tasks.md` へ bytes 同一で置き、git 管理を始める (親が docs として配置)。
2. `tools/check_docs.py` の `COMMAND_LIMITS` / `COMMAND_INTERFACES` へ登録する (Codex author)。
   登録しないと `_check_command_docs_guard` が「command byte予算が未登録」で赤。
3. `orchestrator/tests/test_check_docs.py` の合成 fixture (`_build_min_repo`) に同名 command を足し、
   予算 literal の test を 1 本足す (Codex author)。
4. 系統 blocker: main 先頭 c12e25078 が `.codex/worktrees/*` 110 本を gitlink として誤 commit。
   全 land が provenance 全史監査 rc=1 (DW-O25 → rc=29)、全新規 worktree が submodule 初期化失敗。
   前進修正 = (a) 親が `git rm --cached -r .codex/worktrees` (機械的 git 操作、記録しない)、
   (b) Codex author が `tools/known_violations/c12e25078…--missing-codex-author--<sha256>.json` を書く。
   原因 session ([T-2412] wave [2e7075]) は 07:5x JST に「こちらの前進修正で進めてよい、reset はしない」と回答。
5. land 後に `~/.claude/commands/next-tasks.md` を撤去する (移動の完了)。

## 確定済みユーザー裁定
- 依頼文 (2026-09-08): 所在確認 → izanagi/.claude/commands/ 配下へ移動 → git 管理を始める。
- 予算増加は独立審査 (check_docs.py コメント、2026-08-02 ユーザー裁定)。今回は新規登録であり既存予算の増枠ではない。

## 不変条件
- next-tasks.md は bytes 同一で移す。本文は変えない (「repo 外」と書かれた自己改善節の文言も今回は変えず、報告で裁定へ返す)。
- 実装面 (tools/, orchestrator/tests/) は Codex role=author が書く。親は docs (.md) だけ。
- 規律 2 を緩めない。gate・台帳・一般化の追加は scope 外 (interface 登録は既存 gate への member 追加であって新 gate ではない)。
- known-violation 登録は c12e25078 の 1 finding 1 file。他 finding を相殺しない。

## (P1) 親の provisional 裁定・攻撃対象
- (P1-a) 予算値 `TextLimit(27_100, 100)`: 既存 3 command は現物 +3〜16 bytes の詰め方。27_054 → 27_100 (余裕 46)、最長行 91 → 100。
- (P1-b) interface 契約: frontmatter_keys={description, argument-hint}、arguments_count=0 (`$ARGUMENTS` 不使用、`$1` 使用)、skill-self-improvement.md への到達性あり。
- (P1-c) 段 2・3 を省略 (plan は file:line で確定済み)、段 6 は敵対レビュー 2 本を維持 (受理集合が変わるため)。

## 成果物の形
- commit A: gitlink 除去 + known-violation JSON (trailer: claude manager + codex author)。
- commit B: next-tasks.md + check_docs 登録 + test (trailer: claude manager (docs) + codex author)。
- 変異事前登録 (DW-M01): M1 = COMMAND_LIMITS から next-tasks 行を除く → `test_next_tasks_command_budget_literal_is_exact` が赤 (単一理由)。
  M2 = 予算を 27_101 へ変える → 同 test の plus-one 拒否が赤。M3 = COMMAND_INTERFACES の next-tasks 行を除く → interface の負例 test が赤 (子が足す場合)。
  known-violation 登録の正例/負例 = 全史監査の rc (登録前 rc=1 実測済み / 登録後 rc=0 を land 前に実測)。

## 分割方針
- 実装子 1 本 (author、workspace-write、repo-root = wave worktree)。所有 = tools/check_docs.py、orchestrator/tests/test_check_docs.py、tools/known_violations/ の新規 1 file。
- 親: next-tasks.md 配置、git rm --cached、commit、受入、記録、land、~ 側の撤去。
