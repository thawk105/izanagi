---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t338-rf-validator
seq: 1
---

## 再発

### F157

- **再発: 2026-08-16** — [T-338] Q11 validator wave の段 1 で、親は発火条件 (i) を
  「事前登録が実走より後だから不成立」とユーザーへ中間報告した。実際に見ていたのは本走用の
  別文書 (`output/insights/2026-08-07_t139-mainrun-design/preregistration.md`) で、
  当該計測 (`892042.nqsv`) の事前登録は `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md`
  であり実走前に凍結されていた。前回は条件 (ii) の 4 項を印象で成立と判断し、今回は条件 (i) を
  **別 study の artifact で**不成立と判断した。型は同じ — **条件の各項を、その項を証拠立てる
  正しい artifact の field で照合していない**。段 2 の起草子が `preregistration-witness.tsv` の
  `preregistration_sha256` 束縛を示して倒し、親が一次資料で確認して撤回した。
  恒久対応は F157 のまま変えない (`DW-G03` — 単発ではなくなったが、既存の `DW-S03`
  「親自身の実測値とその一般化もレンズへ入れる」が 2 度とも投入前に止めており、機構は足りている)。
