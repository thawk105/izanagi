---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t755-q2-mocc-trace
seq: 3
---

## 新規

### {{F:submodule-clone-missing-git-identity}}. 新規 worktree の submodule クローンに git identity が無く、config 変更が auto mode classifier に block される [手順漏れ] [環境固有]

- 事象: `EnterWorktree` で新規作成した worktree の `external/ccbench` (submodule) は
  `git submodule update --init --recursive` で fresh clone されるが、この clone には
  `user.name`/`user.email` が一切設定されておらず (outer repo 側は local config 済みだが
  submodule は継承しない)、`git -C external/ccbench commit` が
  `fatal: unable to auto-detect email address` で失敗する。`git config` での補完も
  `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_*` 環境変数での代替も、
  auto mode classifier に block された (CLAUDE.md の「NEVER update the git config」
  規律に沿ったものと見られる)。
- 根本原因: submodule の fresh clone は outer repo の local git config を継承しない。
  CLAUDE.md の git config 変更禁止規律は正しく機能しているが、submodule 内で正当な
  commit を行うための identity 供給経路が用意されていない。
- 恒久対応: 未着手。回避策として、submodule 側の commit を作らず
  `git -C external/ccbench diff --cached` の出力を `.patch` として repo 外へ保全し、
  submodule 側の実 commit は人間が identity を設定したうえで行う運用にした
  (本 wave、`docs/worklog.md` 該当エントリ参照)。恒久対応の選択肢
  (例: submodule 専用の safe な identity 設定手段を用意する、または
  「submodule 内 commit は人間手番」を dev-wave の正式な契約として明記する) は
  ユーザー裁定へ送る。
- 再発検知: 次に submodule (`external/ccbench`) 内で AI が commit を試みる wave で
  同じ `fatal: unable to auto-detect email address` が出れば再発。
