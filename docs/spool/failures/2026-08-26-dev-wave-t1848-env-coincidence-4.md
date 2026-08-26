---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1848-env-coincidence
seq: 4
---

## 再発

### F24

- **再発 (near-miss): 2026-08-26** — 背景 job の完了通知そのものが偽完了を出す形で、
  同型を 1 wave 中に 3 回実測した。待ち条件は `.done` の実在で正しく書いていた
  (`until [ -f <done> ]; do sleep N; done`) が、**待ち手 process が条件成立前に exit 0 で
  完了通知を返した。** 生産者は生存しており `.done` は存在しなかった。
  焦点走の待ち手で 1 回、変異本走の待ち手で 2 回。
  `DW-O01` の「通知は先行しうるので通知を判定にしない」がそのまま効き、
  通知のたびに `.done` の実在を再確認したため実害はゼロだった。
  本追記は、恒久対応の射程が子 process の log や `-o` ファイルだけでなく、
  **待ち手自身の完了通知**にも及ぶことを明示するためのものである。
