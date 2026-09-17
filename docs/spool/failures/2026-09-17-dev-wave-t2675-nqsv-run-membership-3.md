---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2675-nqsv-run-membership
seq: 3
---

## 再発

### F553

- **再発: 2026-09-17** — 計算ノード実験 wave で、親が段 4 に凍結した進行規則「終端記録不足で追加投入を停止」を、
  同じ走の `E − J` の分類が成立していると読んで無視し、`child-exit` 欠落を確認した後に 3 条件を投入した。
  段 6 レビュー 2 本が「事前登録の適格性を結果後に緩めた事後変更」と指摘し、主解析から当該 2 走を外して
  寿命短縮版の実験 2 を投入前に事前登録し直した ({{D:nqsv-run-hold-is-current-session}})。凍結は自分が直前に書いたものでも拘束する。
