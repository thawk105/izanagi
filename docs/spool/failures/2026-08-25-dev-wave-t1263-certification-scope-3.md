---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1263-certification-scope
seq: 3
---

## 新規

### {{F:mutation-worktree-skips-submodule-init}}. 使い捨て変異 worktree が submodule を初期化せず baseline を赤にした [手順漏れ]

- 事象: (2026-08-25、変異 probe の起動時) `tools/mutation_worktree.py` が作った使い捨て
  worktree で baseline が `PARSE_ERROR` になり、production write の前で停止した。
  失敗本文は `submodule is not initialized: external/ccbench/third_party/shirakami` で、
  real repo を読む 3 node が error になっていた。`--resume` は baseline を再走せず
  前回の赤を引き継ぐため、初期化しないまま再試行しても同じ場所で止まる。
- 根本原因: wrapper は固定 commit の worktree を作るだけで、submodule の再帰初期化を行わない。
  `DW-C01` が要求する `tools/dev_wave_submodule_init.py` は wave worktree の作成時にだけ
  適用されており、変異 wrapper が作る worktree はその導線の外にある。実 repo を読む
  テストを変異対象に含む wave でだけ発火するため、合成 fixture だけの wave では表面化しない。
- 恒久対応: 未実施。回避策は、保持された container
  (`<scratch-root>/.izanagi-mutation-worktree/repo`) に対して
  `python3 tools/dev_wave_submodule_init.py --worktree <container>` を実行し、
  以後はその container へ `tools/mutation_harness.py --repo <container>` を直接当てること。
  `--resume` 経由では baseline の赤が更新されないため、`--out` を新しくして harness を
  直接起動する。本 wave はこの手順で baseline PASSED を得た。
- 再発検知: 変異対象の runner command が `REAL_REPO_SERIAL_NODES` の node を含むなら、
  wrapper 起動前に container の submodule 初期化が要る。baseline が
  `submodule is not initialized` を含む `PARSE_ERROR` で止まったらこの型である。

## 再発

### F494

- **再発: 2026-08-25** — 期待 node に real-repo 直列 node を含む変異本走が
  `期待 node が pytest collection に実在しない` で rc=2 停止した。先行 wave の回避策
  (`--deselect` で該当 node を外す) は、本 wave の kill 集合が当該 node に依存するため使えなかった。
  **runner argv へ `-n 0` を渡して分散を切ると、collection 側と `FAILED` 行側の node 表記が
  揃い、real-repo node を期待 node として登録できる。** 実測で baseline PASSED、
  8 変異中 7 KILLED を得た (うち 3 変異は real-repo node だけが kill する)。
  受入形では `--dist loadgroup` 以外が拒否されるが、変異の runner command は受入形ではない。
  恒久対応の代替ではなく、`--deselect` より射程の広い回避策として記録する。
