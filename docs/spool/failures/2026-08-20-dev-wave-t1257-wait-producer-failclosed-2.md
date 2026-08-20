---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1257-wait-producer-failclosed
seq: 2
---

## supersede 追記

- F355 **supersede: 2026-08-20** — [T-1257] で再発検知条件 (2 例目成立時に機序を特定し待ち手側の fails-closed 検査として実装する) を満たした。`tools/dev_wave_wait.py producer` へ `--check-only`/`--receipt-file` を追加し、producer 死亡+`.done`+artifact の 3 点が揃った場合だけ atomic に durable receipt を publish する一発検査を実装、完了通知・stdout・待ち手自身の rc は完了の証拠として扱わない設計にした ({{D:producer-receipt-fails-closed}})。実 subprocess へ SIGKILL/SIGTERM を送る統合テストで F355 の症状 (producer 生存・出力ゼロで待ち手が消える) を再現し、receipt が正しく publish されないことを確認した。変異事前登録 (producer 死亡判定の除去、3 条件 gate のバイパス) は baseline 緑・2/2 KILLED。運用契約 (`DW-C00`/`DW-O01`) への結線は `docs/dev-wave/**` の L1/L1.5 byte 予算と `.claude/commands/dev-wave.md` 自体の 9500 byte 予算がいずれも実質スラック 0 だったため本 wave では実施できず、次の一手 (`{{T:dev-wave-docs-budget-check-only-wiring}}`) へ回した。
