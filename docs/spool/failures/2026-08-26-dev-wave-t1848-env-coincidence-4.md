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

### F57

- **再発: 2026-08-26** — 本 wave の受入全走 2 回で、いずれも
  `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` 1 件だけが落ちた
  (17,390 passed / 1 failed / 64 skipped)。assertion 本文は
  `child.pid was not registered before deadline; stderr=''` で既往と逐語一致する。
  同一 tree の単独走は 1 passed / 6.58 秒で再現しない。
  wave の差分はこの file の import 1 行と別 test 1 つだけで、落ちた test も共有 helper も
  触れていないため非帰属である。
  **本再発は hold へ送らず是正した。** この検査は本 wave が是正対象としている族の実例
  (子 process の応答を小さい絶対期限で待つ型) であり、対象 file が本 wave の所有だからである。
  2 秒の poll を除去し、判定を launcher 終了後へ移した。証拠となる `child.pid` は終了後も残り、
  同じテストが後段で実際に読んでいる。診断文言と後続 assertion は 1 つも削っていない。
  `orchestrator/tests/flaky_test_holds.py` への登録は、同 file を稼働 wave が所有し、
  かつ同 wave が受入済みの tip で凍結していたため採れなかった。
  書けば相手に受入全走の再走を強いる。**所有の衝突が hold 経路を塞ぐ形は、
  非帰属赤の着地手順が想定していない状態である。**
