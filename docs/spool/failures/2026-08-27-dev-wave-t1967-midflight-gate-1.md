---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1967-midflight-gate
seq: 1
---

## 再発

### F225

- **再発: 2026-08-27** — 親が `docs/dev-wave/workers.md` と `docs/dev-wave/operations.md` を
  編集した未 commit 状態で段 6 の敵対レビュー子 2 本を同時に投げ、両方が
  `NG: docs/dev-wave/operations.md: working tree が authority commit と異なる` の rc=2 で
  即死した。2026-08-24 の再発と同型で、merge 由来でなく親自身の docs 編集が原因である点も同じ。
  追加事実は 2 つある。(1) **子が rc=2 で即死しても待ち手は producer-files rc=70 を返す** —
  待ち手の失敗理由 (`/proc/<pid>/stat` を読めない) だけを見ると子の起動失敗と区別できず、
  log 本文を読むまで原因に到達しない。(2) 再投入では `.done` と `-o` を新 path にする必要が
  あるため、同じ prompt でも成果物 path を作り直す手間が掛かる。回避は変わらず、docs 編集を
  統合 commit にしてから子を投げること。
