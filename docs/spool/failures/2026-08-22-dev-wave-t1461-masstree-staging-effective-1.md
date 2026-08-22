---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1461-masstree-staging-effective
seq: 1
---

## 再発

### F95

- **再発: 2026-08-22** — floor masstree staging 実効化 wave の変異本走で 4 回目の再発
  (初出 2026-08-04、再発 08-16/08-17/08-18 に続く)。今回は台帳を検索する前に
  「素の node id を expected_nodes から除外するが runner argv には `--deselect` を
  足さない」という不完全な回避を最初に試したため、除外してもテストは実行され続け
  failed_nodes に残り、MISMATCH (expected 側に無い extra 1 件) を再現した。台帳を検索して
  正しい回避策 (`--deselect=<素の node id>` を runner argv へ追加) を発見し、
  baseline PASSED・161/161 KILLED で収束した。[T-417] の恒久対応は依然未実施であり、
  4 回目の再発によって「散文の再発記録だけでは検知にならない」ことが追加で示された。
