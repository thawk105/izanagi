---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t1170-run-start-schema-version
seq: 3
---

## supersede 追記

- F332 **supersede: 2026-09-18** — 副次的所見 (run-start の schema_version を上げずに field を足していた件) は {{D:run-start-consumer-owned-schema-generation}} で閉じた: 版は 4c6f03048 の v4 を既存の境界として利用し、完全性 consumer が読める run-start 世代を独立定数で所有して producer の現行版と照合しない。版 gate に到達した非対応版は、v3 を `legacy`、それ以外 (欠落を含む) を `unknown` として拒否し、対応版 v4 は従来の field 検査へ進む。検出は `orchestrator/tests/test_autonomous_trial_completeness.py` の v4・binding 無し正例、v3 旧形・未知版の負例、producer 定数を別値にしても判定が変わらない独立性正例。
