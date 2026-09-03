---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2183-knowledge-provenance
seq: 3
---

## 再発

### F357

- **再発: 2026-09-03** — 同じ機序が**変異帰属**という別の活動で現れた。probe 1 で
  `orchestrator/campaign/wal.py` へ打った 2 件の変異が 109 node / 111 node を赤にし、理由は
  すべて `contract-loader-drift` だった。同 file は campaign lock の
  `contract_loader_blob_sha256s` の member であり、bytes を変えると campaign 作成が先に落ちる。
  変異が狙った関門へ到達する前に前段が全赤になるため、**この閉包の member へ打つ変異は
  `DW-M01` の単一理由性を満たせない**。commit 済みかどうかとは無関係で、変異注入そのものが
  drift を作る。恒久対応は {{D:knowledge-provenance-rides-policy-hint-path}} ではなく手順側にあり、
  変異を事前登録する段で対象 file が閉包の member かを確認し、member なら閉包外の consumer へ
  再照準する。本 wave は 2 件を `orchestrator/campaign/layer3_report.py` (閉包外) へ再照準し、
  probe 2 で単一 node を確認してから本走した。
