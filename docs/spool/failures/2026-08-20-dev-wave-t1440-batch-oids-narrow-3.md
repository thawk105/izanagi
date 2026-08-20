---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1440-batch-oids-narrow
seq: 3
---

## supersede 追記

- F417 **supersede: 2026-08-20** — 再発時の仮説(`_batch_oids` を通る他経路が履歴比例のまま残っている疑いが強い)は実測で否定された。真因は branch が D551 land (2026-08-19 12:51) より前の main (11:08) から分岐していたことであり、D551 親コミット時点のコードと失敗 tip での再現実験 (50061 requests) で確定した。`_batch_oids` の呼び出しは repo 全体で2経路のみ (1571行目 `_assert_rulings_exist`、1609行目 `validate_condition_freeze_at`) でどちらも履歴長非依存と確認済み。恒久対応として `_assert_rulings_exist` 経路の専用回帰テストを既存テスト拡張で追加した ({{D:batch-oids-narrow-verification}}、commit 8014d6778f1ca853b719b9d95a333d069ce17456)。
