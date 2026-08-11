---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t139-manifest-land2-s2
seq: 1
---

## 再発

### F126

- **再発: 2026-08-11** — 負例が gate を分離していない事象が、fixture 側ではなく
  **assertion 側**で再発した。`extensions.partialClone` の拒否 gate は
  `pytest.raises(..., match="partial clone")` で照合していたが、production は同じ関数内で
  隣接する 2 つの `raise` を持ち、片方は「partial clone repository は受理しない」、
  もう片方は「partial clone 設定を検査できない」である。**部分一致の `match` は両方に当たる。**
  そのため 1 つ目の分岐を殺す変異を入れても、2 つ目が発火して同じ test が緑のまま通り、
  変異は SURVIVED した。F126 は「狙った検査以外でも**拒否される**入力」(false KILL) だったが、
  本件は「狙った検査以外の**拒否も受理する**照合」(gate が一度も検査されていない) である。
  レンズ 2 本の静的レビューは検出できず、変異検査だけが見つけた。
  対応は照合を拒否理由の完全一致 (`^...$`) へ厳格化することで、production は無変更。
  同型の緩い照合を点検し、隣接する「検査できない / 解決できない」例外まで拾いうる
  6 nodeid を同時に厳格化した。
