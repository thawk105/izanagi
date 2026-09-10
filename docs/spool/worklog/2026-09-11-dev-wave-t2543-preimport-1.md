---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2543-preimport
seq: 1
title: [T-2543] t316の条件関門をprobe import前の既存検査へ加える
---

## 本文

- D1936項30の指定どおり、shell配列1件追加に限定。独立レビュー2本は新規must-fix/nit 0件。
  下流のPython検査で最終拒否されてもimport前の拒否証拠にならない、という相談所見を採用し、
  実PBSのdirty検査断片を実Gitで動かす既存module内の契約で確認した。
- 修正前129 passed、修正後144 passed。関連5fileは856 passed/1 skipped。
  M1は条件関門entry1行の除去でKILLED、期待したstaged/unstagedの2node完全一致。
  記録は `output/insights/2026-09-11/t2543-preimport/README.md`。
- 工数: 隔離Codex worker6本（plan1/consult2/author1/review2）、全てaccepted。
  子ではqstat失敗で未実走。親焦点走はlocal cap到達後にrunnerが自動dispatchして成功した。
  親の途中追加投入は既存holdが拒否したため、元走行の収集を待ち追加childは起動しなかった。
- 起動時にt316関連waveの同対象所有なし。一般化・新防護機構・性能測定・pushを行わない。

## 次の一手差分

### 完了

- [T-2543] D1936項30のshell BOUND_PATHS追加と既存契約の正負例・順序確認を実装した。
  remaining: none
  base: 8777fcf67a486e25e2af19354408230a32af4cfc0be3c8862dbd51cf4466b7b4
