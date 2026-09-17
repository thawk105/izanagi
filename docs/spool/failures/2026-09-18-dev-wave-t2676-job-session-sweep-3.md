---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2676-job-session-sweep
seq: 3
---

## 再発

### F1012

- **再発: 2026-09-18** — [T-2676] の新規 fixture (別 session の leader 配下で production の session 回収を走らせる実 process テスト) の `term` mode が孤児の SIGTERM 既定動作を継承状態に依存していた。login の再現は緑 (0.5 ms で `after=term`) だが、計算ノードへ dispatch した焦点走 (request 5015) では孤児が TERM を無視して KILL 経路へ進み赤。request 5043 の probe で job 内の全 process (nqs_shpd → bash → dispatcher → 子) が SIGTERM を `SIG_IGN` で継承していることを実測。対処は fixture の子と孫に `signal.signal(SIGTERM, SIG_DFL)` + `pthread_sigmask(SIG_UNBLOCK, {SIGTERM})` を明示 (同 file の既存テストと同じ形)、期待値は緩めていない。production 側への含意 (handler を持たない残存子は TERM で死なず 5 秒後の KILL で死ぬ) は {{D:job-session-sweep}} に記録し、計算ノード実測の期待を投入前に改訂した。一次資料 `output/insights/2026-09-18/t2676-job-session-sweep/README.md` §2 / §5。
