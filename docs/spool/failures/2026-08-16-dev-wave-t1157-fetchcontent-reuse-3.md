---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1157-fetchcontent-reuse
seq: 3
---

## 再発

### F306

- **再発: 2026-08-16** — [T-1157] wave の受入 2 走目が
  `test_dev_wave_wait.py::test_public_main_failure_restores_handler_without_release` 1 件で
  `attributable-red` (rc=70 / `source_rc=1`) になった。**同一 node での 3 度目の再発**であり、
  2026-08-15 の再発とも同じ node である。全走の内訳は 11,539 passed / 1 failed / 65 skipped /
  145.64 秒。**本 wave の差分は docs と output/insights のみで、Python を 1 file も変えていない**
  (`git diff main...HEAD -- ':(exclude)docs' ':(exclude)output'` が空)。
  単独再走を計算ノードで行い `1 passed in 2.50s` / rc=0 を実測した
  (`Request 912956.nqsv`、Elapse 7 秒)。
  待ち手の非帰属 checker は今回も `attributable` と分類しており、
  **「docs-only の差分でも `attributable` になる経路」は 2026-08-15 の記録から塞がれていない。**
  本 wave は受入を再走して緑の receipt を取る経路で処理した (checker 自体は直していない —
  非帰属 checker は tested_main 側で走るため、本 wave では効かない)。
