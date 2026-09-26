---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: dev-wave-t2854-unit11-combined
seq: 3
---

## 再発

### F109

- **再発: 2026-09-26** — [T-2854] 単位 11 の計算 probe (job dir、repo 外) で、変異 H-line の判定器が TPC-C consumer を target 名 (`tpcc_` で始まる) で選んでいた。実際の 21 compile entry では該当が 12 件 (`tpcc_<p>.cc` 9 件 + silo・si・mocc の `transaction.cc` の tpcc target 3 件) で、正しく検出しても必ず「理由違い」になる形だった。selftest の合成 row が実構成 (source と target の組) を写しておらず、自己試験は緑、段 6 の敵対レビュー 2 本も見逃した。計算投入の前に親が前例の実測 JSON (単位 3 の `C1-preprocess.json`) と照合して見つけ、fix で TPC-C consumer を source で選び、selftest の row を実測の 21 組にし、旧 filter が正例を拒否する陰性 case を足した。near miss (計算前に是正、成果物の値は不変)。対応は実測の 21 組を selftest へ転記して代表性を改めたもので、実 artifact を直接入力する対策 (本エントリの恒久対応の形) は未実施 (probe は job dir の使い捨てで repo の gate ではないため)。記録は `output/insights/2026-09-26/t2854-unit11-combined/README.md` §6。
