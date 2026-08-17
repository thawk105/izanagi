---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1302-r2-nonattrib
seq: 3
---

## supersede 追記

- F366 **supersede: 2026-08-17** — 恒久対応が保留していた機械化 (受領証 schema と消費側述語の相互 pin) を実施した。実 checker が書いた 3 分類の receipt bytes を実 consumer 述語へ通す pin を `orchestrator/tests/test_check_acceptance_reds.py` に置き、混在 (非帰属 1 件 + flake 1 件) の相互 pin も追加した。受理集合の裁定は {{D:r2-flake-observation}}。
