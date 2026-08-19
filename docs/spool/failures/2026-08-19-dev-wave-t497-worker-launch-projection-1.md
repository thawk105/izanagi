---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t497-worker-launch-projection
seq: 1
---

## 再発

### F225

- **再発: 2026-08-19** — [T-497] merge 文脈ではなく、親が `docs/dev-wave/operations.md` を
  直接編集した (docs-only、D95 により親が編集可) working tree のまま段5 author・段6 review・
  段6 変異spec作成の Codex 子を dispatch しようとし、いずれも同じ
  「working tree が authority commit と異なる」で rc=2 拒否された (計4回)。F225 の根本原因
  (`docs/dev-wave/{operations,workers}.md` が authority commit と 1 byte でも異なると
  `--stage` を問わず全 dispatch が即死する) は merge 固有ではなく、親による通常の docs 直接編集
  でも同じ形で発火することを確認した。恒久対応 (F225 の「順序を入れ替える」) は merge 固有の
  手順で今回には適用できず、都度「`git diff` で対象ファイルだけ退避 → `git checkout --` で
  authority commit へ戻す → dispatch (prompt bytes を変えて新 job-id) → 完了後 `git apply` で
  復元」を実装子・レビュー子ごとに繰り返す運用で回避した。恒久対応の一般化 (退避手順を
  `docs/dev-wave/operations.md` のどこかへ明文化するか) は次 wave 課題として見送る
  (この wave 自体が dev-wave docs の L1.5 byte 予算を使い切っており追記の余地がない)。
