---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-land-knowhow-ops-docs
seq: 2
---

## 再発

### F225

- **再発: 2026-09-29** — docs-only の land 調整の知見の反映 wave で、親が `docs/dev-wave/operations.md` を編集した未 commit 状態のまま段 6 の read-only review 子を投げ、`NG: docs/dev-wave/operations.md: working tree が authority commit と異なる` の rc=2 で起動前に終わった (起動から約 3 秒)。2026-08-27・2026-09-18 の再発と同型で、「実装子がいない docs-only wave でも、review 子の前に docs/dev-wave の編集を commit する」が追加の確認点。commit してから新しい job-id・新しい `.done` で投げ直して通った。失ったのは数分で、計算資源の浪費は無い。
