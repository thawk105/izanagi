---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1202-t1197-cross-module-reach
seq: 2
---

## 再発

### F320

- **再発: 2026-08-17** — wave 開始時の worktree 初期化で再現。`DW-O20` が指示する素の
  `git submodule update --init` は `fatal: transport 'file' not allowed` で必ず落ちる。
  さらに pipe 越しに実行すると shell の `$?` が pipe 側の 0 を拾うため、失敗が
  「rc=0」に見えて気づきにくい。`git -c protocol.file.allow=always submodule update --init` で
  通した。本件は受入ではなく wave 起動段での発現であり、既存の受入 preflight 検査は
  この時点では発火しない。`DW-O20` 本文の是正は同節が 997 / 1000 bytes で余白 3 bytes しか
  なく実測に裏付けられた 1 行も入らないため実施しない (恒久対応は [T-1139] が所有)。

### F104

- **再発: 2026-08-17** — 五つ目の方向。既往 4 方向はいずれも「生きている pid の選び違い」
  または「別 process への誤一致」だったが、本件は**生産者がそもそも起動していない**形である。
  段 5 で 2 単位の子を 1 回の Bash 呼び出しでまとめて detach したところ 2 本目が起動せず
  (pid file も log も未生成)、その状態で張った待ち手が `stage=pid-file rc=2` で即座に落ちた。
  待ち手の異常終了は harness からは「completed」として通知されるため、出力本文を読むまで
  正常完了と区別できなかった。判別 = detach 直後に pid file の実在を確認してから待ち手を張る。
  復旧 = 子を 1 本ずつ detach し直し、pid file 実在を確認してから待ち手を張り直した。
  本 wave では以後この順序で全子を投入し、同型の再発は起きていない。
