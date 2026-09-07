---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2356-s4-prebuild-seam
seq: 1
---

## 新規

### {{F:enterworktree-shell-cwd-lockout}}. EnterWorktree 直後に永続 shell の cwd が共有 checkout に残り、全 Bash 呼び出しが拒否される [セッション死・救出] [手順漏れ]

- 事象: 背景 job で `EnterWorktree` を呼ぶと session は worktree に入るが、**Bash tool の永続 shell の
  cwd は共有 checkout のまま残ることがある。** その状態では `pwd` や `mkdir` を含む**あらゆる**
  Bash 呼び出しが `working directory resolved to the shared checkout` で拒否される。
  拒否文言は「その worktree から実行し直せ」と言うが、`cd <worktree>` も
  `cd <worktree>; pwd` も同じ理由で拒否されるため、bash 側に脱出手段が無い。2026-09-07 の本 wave で
  4 ターン空転した (実害は時間のみ)。
- 根本原因: guard は**コマンド開始時点の永続 shell の cwd** を見て判定する。`EnterWorktree` は
  session の作業ディレクトリを移すが、既に起動している永続 shell の cwd は動かさない。
  `cd` を含む複合コマンドも開始時点の cwd で判定されるので、自力で直せない。
  同型の危険として、隔離 session で `cd <別 worktree> && <cmd>` を Bash tool へ直接書くと
  永続 shell がそこへ移り、以後すべて拒否される。
- 恒久対応: memory `worktree-discipline` の節
  `enterworktree-leaves-shell-cwd-behind` と `never-cd-persistent-shell-to-another-worktree`
  (`/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/worktree-discipline.md`)。
  **復旧は同じ path で `EnterWorktree({path: <いま入っている worktree の絶対 path>})` を呼び直す。**
  予防は「Bash tool の command 先頭に裸の `cd` を書かない。別 path で走らせるものは
  `bash -c 'cd <path> && <cmd>'` の部分シェル形か、path を本文に固定した runner script にする」。
  `docs/dev-wave/operations.md` の `DW-O20` へ復旧経路を足す案は、同 file 群の byte 予算が
  満杯のため採らない (安全義務を削って捻出しない)。
- 再発検知: 隔離 session の最初の Bash が上記の拒否文言を返したかどうか。返したら
  `cd` を試さず即座に `EnterWorktree({path})` を呼ぶ。
