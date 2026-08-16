---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1066-wait-signal-flake
seq: 2
---

## 新規

### {{F:scope-cap-page-alignment}}. bounded local の予算が page 境界に乗らない走行が全部 rc=16 で止まる [計測汚染] [恒真ゲート]

- 事象: `tools/run_tests.py` のローカル焦点走が `bounded scope の memory.max /
  memory.oom.group を走行中に attest できない` で `rc=16` になり、テストが 1 件も走らない。
  2026-08-16 に本 wave で 6 走中 4 走が該当した。rc=16 はテスト結果ですらないため、
  赤としても緑としても扱えない。
- 根本原因: `_scope_properties_are_enforced` が cgroup の `memory.max` を予算値と
  **文字列で厳密比較**する。一方 kernel は `memory.max` を page 境界へ丸めて保持する。
  予算は「前回ピーク × 1.25」で算出されるため 4096 の倍数にならず、端数が出た走行は
  **決定的に**失敗する。実測: 予算 4294967296 (`% 4096 == 0`) の 2 走は成功、
  2913920000 / 1417630720 / 1545958400 (いずれも `% 4096 == 1024`) の 4 走は全滅。
  保存ピーク 2331136000 × 1.25 = 2913920000 が失敗した予算値と byte 一致した。
- なぜ気づきにくいか: 予算は**同じ target set の 2 走目以降**にだけ前回ピークから導出される。
  初回は既定 4 GiB (page 境界) なので通り、「たまに落ちる」ように見える。
  `docs/dev-wave/mutation.md` の `DW-M07` が既に「local は同一 target set の 2 巡目以降で
  予算 attest が落ち収集段が rc=16 になる」と書いていたが、**原因は page 境界と特定されていなかった。**
- 恒久対応: {{T:run-tests-scope-cap-alignment}} として起票。本 wave は共有ツールを変更せず、
  **予算キャッシュの無いファイル組み合わせで走らせる**回避で進めた
  (キャッシュは `/run/user/<uid>/izanagi-admission/peak-tests-partial-<key>.peak`)。
- 再発検知: `rc=16` の走行で報告された「算出予算」が `% 4096 != 0` であること。

## 再発

### F306

- **再発: 2026-08-16 — ただし本エントリの根本原因記述が誤りであることが判明した。**
  本 wave が真因を特定した。詳細は supersede 行を参照。

## supersede 追記

- F306 **supersede: 2026-08-16** — 本エントリの根本原因「実 signal を扱う subprocess テストが 48 worker の並列下で timing 競合する」は誤りである。真因は `orchestrator/tests/test_dev_wave_wait.py` の `test_signal_after_receipt_publish_does_not_reverse_success` 1 件による決定的な worker signal mask 汚染で、同 test の `delayed_signal` が `SIG_BLOCK` では real `pthread_sigmask` を呼んで実際に mask を変えるのに復元側の `SIG_SETMASK` では real syscall を呼ばず例外を送出し、`monkeypatch` が Python 属性しか戻さないため、当該 worker は寿命の終わりまで `_HANDLED_SIGNALS` が blocked のまま残る。負荷は配送遅延の原因ではなく汚染 node の後ろに誰が配られるかを変える媒介にすぎず、赤 node が族内を移動する観測もこれで説明される。恒久対応「変異検査では族を含む file を runner 範囲から外す」も退役し、本 wave の変異走行は `orchestrator/tests/test_dev_wave_wait.py` を runner 範囲へ戻して行った。
