---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-13
wave: dev-wave-t2557-balanced-stock-inline
seq: 2
---

## 再発

### F622

- **再発: 2026-09-13** — T-1998 の対 consumer が実 producer 成果物へ通されないまま着地し、
  合成 fixture だけで検証された述語 2 系統が、実成果物では原理的に成立しないことが
  正式測定で初めて露見した。(1) run_cmd の numactl 前置を `linux-baremetal` 契約の値の
  literal で固定しており、事前登録が pin する `pegasus` 契約 (`numactl=()`) では満たせない。
  (2) `toolchain_record_sha256` を WAL の縮約 `toolchain` から再導出できる前提だが、producer は
  full version を含む別 manifest から digest を取っており、`version` は成果物に存在しない。
  **恒真の向きが F622 本体と逆である。** F622 は決して赤にならない gate、本件は決して緑に
  ならない gate であり、後者は実データが揃うまで露見せず、露見時には計測を 1 本消費し終えている。
  検知は「新設 gate を親が実データで 1 度通すまで完成としない」で共通し、着地前の live dogfood が
  唯一の防壁である。是正の裁定は未了 (numactl 側の方向だけ D924 が既裁定)。
  経緯と一次資料は `output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`。
