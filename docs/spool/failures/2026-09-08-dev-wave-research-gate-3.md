---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-research-gate
seq: 3
---

## 新規

### {{F:codex-worktrees-gitlinks-in-main}}. codex 子 worktree 110 個が gitlink として main に混入し、全 wave の受入が走行前 fingerprint で rc=128 になった [手順漏れ] [ドリフト]

- 事象: main `c12e25078` (別 wave の docs 記録 commit) が repo 直下 `.codex/worktrees/*` を mode 160000 の
  gitlink 110 個として tree に入れた。`.gitmodules` に対応が無いため `git submodule status --recursive` が
  `fatal: no submodule mapping found` (rc=128) となり、受入待ち手の走行前 fingerprint が
  `stage=prerun-fingerprint rc=70 source_rc=128` で止まる。main 自動 merge 後に発生するため、
  main を取り込むすべての wave の受入が同じ理由で落ちる (本 wave の attempt 1 で実測、lease は claim 前で free)。
  同 commit は provenance 監査でも「実装面に Codex role=author がない (110 paths)」で赤になり、land の全史監査も止まる。
- 根本原因: 混入元 session の申告では、Bash の cwd が主 checkout に残ったまま `git add -A; git commit` を
  実行した。`.codex/worktrees/` は `tools/mutation_worktree.py` の共有木観測 (F599) のため意図的に
  untracked のまま見えており、`git add -A` が丸ごと stage する。`check_docs`・land の fold gate は
  gitlink の混入を検査しない。
- 恒久対応: memory `codex-worktrees-gitlinks-leak-into-main` と memory `git-state-changes-need-explicit-C`
  (記録 commit は path を名指しで stage し、`git add -A` を使わない。状態を変える git は `git -C <木>` で
  木を明示する)。`.gitignore` / `info/exclude` へ足す案は F599 により採れない。main 側の是正 (index からの
  除去と known-violation 登録) は別 wave の commit `48837186c` / `c9c97525e` が担う。
- 再発検知: 受入待ち手の `prerun-fingerprint rc=70 source_rc=128`、および
  `git ls-files -s | grep ^160000` に `external/ccbench` 以外が出ること。
