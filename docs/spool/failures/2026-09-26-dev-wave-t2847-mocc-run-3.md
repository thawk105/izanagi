---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: dev-wave-t2847-mocc-run
seq: 3
---

## 再発

### F889

- **再発: 2026-09-26 (near miss、[T-2847] dev-wave-t2847-mocc-run)** — 段 7 の記録 commit の直後に、段 8 を閉じないまま受入全走の門番 script を投入した。handoff の「dev-wave 改善候補」節に未裁定の候補 (下の F1031 の再発) が残っていた。門番が 1 周目の待機中 (受入の子は未起動) に、land が wave HEAD と tested tip の一致を要求することを記憶で確かめて気づき、門番を止めて段 8 の fragment を足してから受入を投入し直した。計算の浪費は無い。既存の再発検知 (投入直前に handoff の改善候補節を見る) を投入の手順に入れていなかった。

### F1031

- **再発: 2026-09-26 (near miss、[T-2847] dev-wave-t2847-mocc-run)** — 段 5 の unit worktree を作る script の起点に、`git rev-parse` の出力を写さず短縮 SHA の後ろを推測で埋めた値を渡した。`git worktree add` が `Not a valid object name` (rc=255) で止まり、branch も worktree も作られなかった。`rev-parse` の 40 hex を写して作り直した。既存の再発検知 (object 名の失敗で推測 SHA を疑う) が効いた。
