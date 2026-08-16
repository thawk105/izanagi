---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1179-publish-seam
seq: 3
---

## 再発

### F95

- **再発: 2026-08-16** — [T-1179] の変異本走でも 2 通りとも fail-closed に倒れた。
  素の node id で登録した `test_real_seal_protocol_to_floor_official_core_e2e` は
  観測側が `@real-repo` 接尾辞付きで `MISMATCH` になり、接尾辞を付けて再登録すると
  preflight が「期待 node が pytest collection に実在しない」で停止した。
  [T-417] の恒久対応は未実施のままである。
  今回の回避は runner argv へ `--deselect <素の node id>` を足して当該 node を
  runner 範囲から外し、期待集合からも同じ node を除いた再導出である
  (観測されえない node なので、外した期待集合は完全集合のまま保たれる)。
  この回避は該当 node の検出力を 1 件失うので、`DW-M01` の再照準と同様に
  残る期待 node だけで単一理由の kill が成立することを確認してから使う。
