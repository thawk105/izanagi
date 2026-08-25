---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1135-prereg-blockers
seq: 1
---

## 再発

### F474

- **再発: 2026-08-26** — 向きが逆の同型。親は「`EVIDENCE_UNDEFINED` を区別する production
  consumer は存在しない」を、その literal を全 production file へ grep して 0 件と測り、
  段 2 の plan もこの前提の上に版 bump 不要を組み立てた。実際には gate レポートが
  `PredicateStatus` の enum を総なめして status count を出しており、literal を 1 度も書かない
  ため grep に掛からなかった。段 3 のレンズ B が参照関係から発見した。F474 が「値を複製する
  consumer」を探せと定めたのに対し、本件は「値を一度も綴らず enum ごと畳み込む consumer」で
  あり、単一の綴りによる grep はどちら向きにも閉包にならない。不在を主張するときは、
  値を綴る箇所と綴らない箇所 (enum 反復・総なめ・動的解決) の両方を型から引く。
