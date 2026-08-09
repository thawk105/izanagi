---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t684-lease-fifo
seq: 1
---

## 新規

### {{F:acceptance-lease-no-fairness}}. 受入 lease に待ち行列が無く、待ち周期が短い側が有利だった [手順漏れ] [コンテキスト浪費]

- 事象: 並行 dev-wave が受入 lease を待つとき、待ち周期が短い側が release 直後の競争に勝つ。
  同日 2026-08-09 に独立 2 例 — [T-648] wave が 2 時間 15 分 (holder 5 回交替、60 秒周期が
  90 分空振り)、[T-671] wave が約 4 時間 (holder 5 回交替、120 秒周期の待ち手が 2 度空振りし、
  45 秒周期へ詰めて取得)。待つ側は local main を都度取り込み直すため、待ち時間ぶん検査と
  base digest の再基準化が増える。
- 根本原因: D239 の lease は `O_CREAT|O_EXCL` の 1 発勝負だけで、**待機者が状態としてどこにも
  残らない**。本 wave が既存 CLI だけで再現した — A が取得、B が `held`、A が release、
  直後に来た C が `acquired` を取り、lease directory には `acceptance.lease` 以外に
  1 byte も残っていなかった。
- 恒久対応: {{D:acceptance-lease-fifo-queue}} の待ち札方式待ち行列
  (`tools/wave_land_window.py` の `_queue_head` / `_ensure_ticket` / `_drop_ticket_best_effort`)。
  運用契約は `docs/pegasus-runbook.md` §7.3 に「30〜120 秒周期の loop」「待ち札は 300 秒で失効」
  として明記した。
- 再発検知: `orchestrator/tests/test_wave_land_window.py` の
  `test_fifo_oldest_waiter_acquires_before_fast_newcomer` ほか。変異 matrix 10 件で
  SURVIVED 0 を実測済み (`output/insights/2026-08-09_t684-lease-fifo/mutation-ledger.json`)。

### {{F:fifo-queue-self-sustaining-deadlock}}. 待ち行列の初版は先頭が自分で全 wave を止められた [恒真ゲート] [手順漏れ]

- 事象: 段 2 プランと段 5 実装は、先頭の待ち札を持つ wave が lease を作れないまま heartbeat を
  続けられる形になっていた。この wave は毎回先頭のまま、後続は永久に `queued` を返され、
  待ち札 TTL でも回復しない。**不公平を直すはずの機構が、より重い停止を作っていた。**
  段 5 実装では別経路も成立した — 自分の待ち札を登録できない wave が `queued` を返し続け、
  一度も従来の競争へ落ちない。
- 根本原因: 「異常時は縮退する」という原則を段 2 プランが**待ち札 1 枚の異常にだけ**適用し、
  自分が列に並べない場合と、先頭が取得に失敗し続ける場合に適用していなかった。
  段 5 実装の `_drop_ticket_best_effort` は flock 取得に依存し、失敗を
  `except Exception: pass` で握り潰していたため、生きた先頭札を残したまま `unavailable` を返せた。
- 恒久対応: {{D:acceptance-lease-fifo-queue}} の不変条件「非 `acquired` を返す `claim` は
  自分が先頭のまま生きた待ち札を残さない」と、縮退の発火条件を 3 つに明文化したこと。
  待ち札の削除は flock 非依存にし、成否を返す形にした。
- 再発検知: `test_head_that_cannot_create_lease_drops_own_ticket` と、変異 M4
  (V1 の cleanup を外す) が KILLED であること。段 3・段 6 とも敵対レビュー 2 本を独立レンズで
  回し、いずれも NO-GO を返してこの経路を見つけた — **レビューを 1 本に減らしていたら
  land していた**。
