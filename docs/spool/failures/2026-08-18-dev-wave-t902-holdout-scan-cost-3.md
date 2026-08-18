---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t902-holdout-scan-cost
seq: 3
---

## 再発

### F172

- **再発: 2026-08-18** — 段 3 の敵対相談 2 本を並列投入した最中に
  `401 Unauthorized ... auth error code: token_revoked` が出た。今回の形は F172 初出と 2 点違う。
  (1) 死んだ子は即死ではなく、**371 秒・34 model call・出力 13,874 token を消費してから**
  websocket 再接続で 401 を踏み、rc=1・出力 0 bytes で終わった。receipt の
  `actuals` を見ずに wall-clock と rc だけで判断すると「重い相談が失敗した」と誤読する。
  (2) 同じ worktree の兄弟子は同じ 401 を 3 分間隔で 3 回受けながら**既存 session で耐え**、
  認証回復後に rc=0 で完走した。**同一 wave 内で生死が割れる。**
  並行 wave からは「利用枠切れ (数秒・token ゼロの即死)」として周知されたが、
  本 wave の stderr 実本文は枠切れではなく認証失効であり、**peer の分類をそのまま自分の
  失敗へ当てはめると真因を取り違える**。復旧の可否は親自身の最小実行で実測して確かめた。
  再投入は別 artifact-root で行った (同一 prompt は job-id が同じになり receipt 上書き拒否で
  rc=2)。F172 の恒久対応 (fail-closed 停止・成果の commit 保全・新 artifact 名での再投入) は
  そのまま有効で、追加の恒久対応は要らない。
