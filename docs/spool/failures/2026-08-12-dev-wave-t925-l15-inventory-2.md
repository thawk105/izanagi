---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t925-l15-inventory
seq: 2
---

## 新規

### {{F:git-segv-false-red-in-acceptance}}. 受入全走中に `git checkout` が SIGSEGV し fixture setup が偽の赤になる [計測汚染]

- 事象: [T-925] の受入全走 2 走目で `test_codex_reasoning_ab.py` の 3 node が
  **setup 段階**で error になった。逐語は
  `ValidationError: command failed rc=-11: git checkout -B codex/dev-wave-t153e-t15423 <sha>`。
  `rc=-11` は SIGSEGV。同じ木の 1 走目は `10,085 passed / 65 skipped` で緑、
  2 走目との差分は**文書 2 ファイル** (worklog fragment と insights README) のみで、
  テスト fixture の `git checkout` へは到達しえない。当該 3 node の単独再走は
  `--force-dispatch` で `3 passed` (rc=0)。**再現せず、実装差分へ帰属しない。**
- 根本原因: 未確定。並行 wave 4 本が同一 repo の object store を共有した状態で、
  commit 時に git 自身が
  `There are too many unreachable loose objects; run 'git prune'` と
  `The last gc run reported the following` を警告しており、
  `.git/worktrees/<wave>/gc.log` が残留して自動 gc が止まっていた。
  object store 圧下での git の異常終了が疑われるが、SIGSEGV の直接原因は未特定。
- 恒久対応: memory `no-concurrent-dispatch-during-acceptance` の対象を
  「単独再走で消える偽の赤」の既知型として本エントリへ拡張する。
  受入で `rc=-11` / SIGSEGV を見たら、実装差分へ帰属する前に
  `DW-O18` の単独再走 (`--force-dispatch` 付き) で再現性を実測する。
- 再発検知: 受入 log 中の `rc=-11` と `unreachable loose objects` 警告の同時出現。
  機械検査は未実装 (本エントリ 1 例目のため `DW-G03` の独立 2 例を満たさない)。
