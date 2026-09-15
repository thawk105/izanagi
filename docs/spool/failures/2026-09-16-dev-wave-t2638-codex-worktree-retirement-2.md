---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2638-codex-worktree-retirement
seq: 2
---

## 再発

### F119

- **再発: 2026-09-16** — 向きが逆の同型 ([T-2638])。F119 は `git diff-tree -m` が merge で
  **過大計上**する側だったが、今回は `git log --find-object` が merge で**過少計上**した。
  `git log` は既定で merge commit の差分を作らないため、`merge(main):` 経由で main へ入った blob が
  「どの commit にも無い」と判定される。実証: 同じ blob が `-m` / `--diff-merges=first-parent` を
  付けると merge commit `9f2f8d3a3` に見つかり、`git rev-parse refs/heads/main:<path>` は
  **その blob が main の現行内容そのもの**だと返した。この誤判定のまま「子 worktree に着地して
  いない内容が 6 件ある」と報告する直前だった。**根本原因は F119 と同じで、merge commit に対する
  git の差分生成の既定を確かめずに判定器へ据えたこと。** 恒久対応 = 内容の着地判定は
  `git rev-parse <ref>:<path>` と `git hash-object` の直接比較を一次とし (O(1)・履歴を歩かない・
  merge の影響を受けない)、履歴検索は `-m` 付きの補助に限り、**`--find-object` の無 hit を単独の
  否定根拠にしない**。再発検知 = memory `git-find-object-misses-merge-commits`。
  なお `--find-object` の hit も「その commit の tree にその blob がある」ことを意味しない
  (削除された側でも hit する) ため、証拠 commit として記録するなら `ls-tree` で tree を直接照合する。
