---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2201-b10-denominator
seq: 2
---

## 再発

### F26

- **再発: 2026-09-02** — 削除側でなく**作成側**で、しかも一括ループでなく **1 件の
  `git worktree add` 単独**が 2 分の command timeout に掛かって kill された。残った中途状態は
  「branch は作成済み・checkout も進行済みだが `.git/worktrees/<name>` の admin dir が無い」形で、
  **`git worktree list` に現れない**。既載の運用則 (1 件ずつ・timeout を延ばす) は作成側にも要る。
  `git worktree prune` だけでは checkout 済み dir が残るので、`rm -rf` と併せて畳んでから
  既存 branch を再利用して作り直す。

### F615

- **再発: 2026-09-02** — 2 本目の書き手が自分の `git status` ではなく、**背景で走らせていた
  自分の `git worktree add`** および他 wave の活動だった。根本原因は「並行 `git status`」より広く、
  対象 worktree の index を refresh または書き換える**任意の並行 git 操作**で成立する。
  **新しいのは症状の形である。** pathspec を付けて走査したため、出力が「全 tracked file が編集中」
  ではなく**問い合わせた特定 path だけが `D` (staged delete) + `??` (untracked)** という形になり、
  狙い撃ちの編集面重複 hit と見分けが付かなかった。安価な判別子は再走査で、
  **本物の重複は同じ worktree に留まり、F615 は走査ごとに別の worktree へ移る** (今回は 5 件 → 1 件 →
  0 件と移動し、直接測り直すといずれも clean だった)。既載の恒久対応 (単独で測り直す) は有効だった。
