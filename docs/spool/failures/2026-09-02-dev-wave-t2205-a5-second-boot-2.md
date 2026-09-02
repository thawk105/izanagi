---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2205-a5-second-boot
seq: 2
---

## 再発

### F660

- **再発: 2026-09-02** — A-5 (D1100) の実測 wave が同じ形で当たった。
  新設した `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh` を走らせようとして
  `未登録 Pegasus 実行体` で拒否された。登録簿は wave の worktree で更新済みで、
  在庫テストも受入全走も緑だった。**迂回はしていない。**
  段 1 の brief で本 F の再発検知 (実測が新規 Pegasus 実行体を要するかを
  main 側の登録簿に対して確認する) を行わず、段 6 の実測直前まで進んでから当たった。
  恒久対応は F660 のものが正しく、変更しない — 機構を着地させる wave と実測を行う wave に分ける。
  本 wave は機構の着地までを成果とし、実測を次の一手へ起票した。
  **再発検知の実施点が段 1 の必読節 `DW-S01` に無いことが、2 回とも遅れた理由である。**
