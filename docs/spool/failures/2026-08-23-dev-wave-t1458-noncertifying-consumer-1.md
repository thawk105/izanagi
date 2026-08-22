---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1458-noncertifying-consumer
seq: 1
---

## 新規

### {{F:acceptance-lease-serialization-does-not-scale}}. 受入lease直列化が並行wave数の増加に耐えられず全体停止した [手順漏れ]

- 事象: 15件以上の並行 dev-wave が単一の `acceptance.lease` ファイルによる FIFO 直列化で
  同時に長時間 (実測で最長63分超、複数セッション報告の合算では7時間近く) ブロックされ、
  受入・main land が全体的に停止した (2026-08-22〜2026-08-23)。うち1件は holder
  プロセスが計算ジョブ完了後に異常終了し、TTL (2400秒=40分) 満了まで他の全 wave を
  待たせ続けた。D662 (2026-08-22 ユーザー裁定、「lease claim 待ちは不要」) は既に
  存在していたが、それを実行可能にする `tools/dev_wave_wait.py` 側のコード変更が
  裁定から半日以上経っても誰も着手していなかった。
- 根本原因: 直列化機構 (1 holder が同時に1つ) は並行 wave 数が少ない前提で設計されており、
  ユーザー裁定 (D662) という戦術層の変更が、対応するコード変更を伴わないまま「運用上は
  もう不要」という状態で放置されていた。運用裁定とコード実装のギャップが並行 wave 数の
  増加とともに致命的な停止を招いた。
- 恒久対応: `tools/dev_wave_wait.py acceptance` へ `--lease-optional` フラグを実装し
  (commit 0c89ec77)、claim が held/queued でも待たずに受入を継続できるようにした。
  `docs/dev-wave/operations.md` の DW-O27・`.claude/commands/dev-wave.md` 条件18へ
  「acceptance 投入は `--lease-optional` を既定で使う」ことを明記し (commit 25614f86)、
  今後の全 wave が起動手順に従うだけで自動的にこの経路を使うようにした。
- 再発検知: holder プロセスの死活監視強化 (TTL 満了を待たずに異常終了を検出する仕組み) と
  `_LEASE_TTL_SECONDS` の値自体の見直しは、本 wave のスコープ外として別セッションへ
  引き継いだ (未着手)。`--lease-optional` が浸透すれば直列化待ち自体の発生頻度は
  大幅に下がるはずだが、フラグを付け忘れた wave は引き続き同型の問題に当たりうる。
