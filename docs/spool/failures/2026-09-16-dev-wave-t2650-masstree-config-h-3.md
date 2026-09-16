---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2650-masstree-config-h
seq: 3
---

## 再発

### F39

- **再発: 2026-09-16** — 床値 campaign の condition gate へ依存供給を配線する wave で、
  production へ 12 行足した結果 `orchestrator/tests/test_ccbench_spawn_sites.py` の
  deferred-gate 登録簿が pin する `s8b_floor_campaign.py` の 2 sink が
  4708 → 4720 / 8661 → 8673 へずれ、4 node が赤になった。**この型の 4 度目である。**
  今回が足す事実は「`DW-O09` へ収容した後も、検索鍵が合っていなければ守られない」ことである。
  現行の `DW-O09` は行番号 pin の存在に触れているが、示している検索鍵は
  `git grep -n "<成果物パス>"` = **凍結成果物の path** であり、親はそれに従って
  `FROZEN_MANIFEST` と output 配下の成果物 path を引いた。**これから行を挿入する
  production source file 自身の path を鍵にする手順が無い。** 実際、同じ grep を
  `orchestrator/campaign/s8b_floor_campaign.py` を鍵に打てば段 1 で当該 test が 1 発で出る
  (段 6 の `DW-O26` 焦点走ではそれで出た)。検出は着地前で実害ゼロ、拾ったのは
  `DW-O26` の consumer 拡張焦点走。恒久対応は F39 から変更しない。
  運用として、**pin 閉包の検索鍵に「変更予定の production file の path」を明示的に足す**。
