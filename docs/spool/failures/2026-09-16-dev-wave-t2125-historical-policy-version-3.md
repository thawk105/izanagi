---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2125-historical-policy-version
seq: 3
---

## 再発

### F358

- **再発: 2026-09-16** — [T-2125] wave の親が、閉包 member (`artifact_admission.py` / `build_admission.py` / `wal.py`) を変異させた本走の結果を、核を差し引く前に「8/8 KILLED・期待 node 完全一致」と記録した。`DW-M08` に従って probe の観測 node 集合をそのまま期待 node に再登録していたため、**完全一致は核を含んだ集合どうしの一致であり、核の有無を何も否定しない。** 段 8 で F358 を読み直して交差を取ったところ、核は 5 node (`test_layer3_report.py` の certifying 系、原因 `contract-loader-drift`)、delta が空の変異は 0 本で、KILLED 判定自体は正しかった (M3・M4・M7 は delta = 1 で狙った node ちょうど)。land 前に捕捉した near miss である。**再登録で期待 node を観測集合に合わせる手順は、F358 の差し引きを代替しない。**
