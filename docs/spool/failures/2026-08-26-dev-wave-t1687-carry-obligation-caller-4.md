---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1687-carry-obligation-caller
seq: 4
---

## 再発

### F95

- **再発: 2026-08-26** — 段 6 の fix で `REAL_REPO_SERIAL_NODES` へ登録した
  `test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs` が kill 集合に入り、
  2 通りとも fail-closed に倒れた。素の node id では実測側が `@real-repo` 接尾辞付きで
  `MISMATCH`、接尾辞付きでは preflight が「期待 node が pytest collection に実在しない」で停止。
  **再照準せずに済む迂回を実測した** — runner argv へ `-n 0` を足して並列を切ると、
  実測側の node id にも接尾辞が付かず preflight と突き合わせの表記が一致する。
  1 変異だけの probe で確認してから本走し、台帳の記載だけを書き換える抜け道を塞ぐ変異を
  落とさずに済んだ。逐語は
  `output/insights/2026-08-26_t1687-carry-obligation-caller-mutation.md` の erratum。
  恒久対応 (`_normalize_node` への接尾辞正規化) は依然として未着手である。
