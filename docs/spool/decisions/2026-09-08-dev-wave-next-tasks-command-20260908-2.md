---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-next-tasks-command-20260908
seq: 2
---

## {{D:next-tasks-command-budget}}. next-tasks command は bytes 同一で repo へ移し、既存 3 command と同じ形で予算表と interface 表へ登録する

**決定:** `.claude/commands/next-tasks.md` は `~/.claude/commands/next-tasks.md` と bytes 同一で置く。
`tools/check_docs.py` の `COMMAND_LIMITS` に `TextLimit(27_100, 100)` (現物 27054 bytes / 最長行 91 chars)、
`COMMAND_INTERFACES` に frontmatter `{description, argument-hint}`・`$ARGUMENTS` 0 件を登録し、
`orchestrator/tests/test_check_docs.py` の合成 fixture と予算 literal test (現物 bytes・plus-one 拒否) を
既存 command と同型で足す。本文の文言 (「本ファイル (repo 外)」、絶対 path) と共通自己改善契約への編入は
変えず、編集境界としてユーザー裁定へ返す。

**理由:**
- checker は command directory と `COMMAND_LIMITS` の完全一致を要求する。登録なしでは新規 command が
  「予算未登録」で赤になり、登録は実装面なので Codex author が書く。
- 予算は既存 3 件 (現物 +3〜16 bytes) と同じ詰め方にした。増枠は独立審査 (2026-08-02 ユーザー裁定) であり、
  新規登録で緩い予算を置くと anti-bloat の意図が command ごとに割れる。
- 依頼は「移動して git 管理を始める」であり、本文の改稿は依頼に含まれない。移設で意味が変わる文言
  (repo 外・その場で直す) は裁定境界に関わるので既成事実にしない。

**却下した選択肢:**
- 予算を緩く (例 32_000) 置く — 既存 3 command との非対称を作り、増枠審査の意味が薄れる。
- 移設と同時に「repo 外」の文言と絶対 path を直す — bytes 同一の不変条件と scope を破る。
- interface 表へ登録しない — 既存 gate の member 追加であって新 gate ではなく、欠くと frontmatter・到達性の検査が
  この command だけ蒸発する。

## {{D:c12e25078-forward-fix}}. main へ誤って入った gitlink は index 除去 + 既知違反登録の前進 commit で直し、履歴の書き換えと除外設定の追加はしない

**決定:** main 先頭 c12e25078 が `.codex/worktrees/*` 110 本を gitlink として commit した系統 blocker は、
別 wave の branch 上で (a) `git rm --cached -r .codex/worktrees` (作業 file は触らない) と
(b) `tools/known_violations/` への c12e25078 の既知違反登録 (Codex author) を 1 commit にして ff-only で land する。
`git reset` による main の書き換えは行わない。`.gitignore` への `.codex/worktrees/` 追記も行わない。

**理由:**
- 全史 provenance 監査が rc=1 のままだと DW-O25 により全 session の land が rc=29 で止まり、原因 session 自身の
  land も同じ関門で止まる。登録は台帳の既存機構 (1 finding 1 file) で、他の finding を相殺しない。
- reset は c12e25078 を祖先に持つ全 branch (少なくとも 2 wave) の作り直しを要し、ff-only の land で再流入する。
  原因 session も reset の権限を持たず、前進修正を委ねた。
- 除外設定で `.codex/worktrees/` を隠すと、変異 harness が走行前後で bytes 一致を要求する共有 checkout の
  `?? .codex/worktrees/` 行が消える (F599 と既存の D)。再発防壁の要否はその観測面と同時にユーザーが裁定する。

**却下した選択肢:**
- `git reset --mixed` で main を戻す — 共有 main の履歴書き換え。index.lock も取れなかった。
- gitlink 除去だけを commit し登録しない — 除去 commit 自体は緑でも c12e25078 の finding が履歴に残り land が止まる。
- `.gitignore` 追記を同じ closure に含める — F599 の既裁定と衝突する。
