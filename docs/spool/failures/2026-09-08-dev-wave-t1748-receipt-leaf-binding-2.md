---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1748-receipt-leaf-binding
seq: 2
---

## 新規

### {{F:mutation-probe-file-scoping}}. 対象 file を絞った login 自走 probe は「正当な入力を全部拒否する」型の変異の期待 node を確定できない [手順漏れ] [テスト代表性]

- 事象: 変異本走 attempt 2 で、照合の向きを反転する変異 (正当な受領証を拒否する向き) だけが
  `MISMATCH` になった。login 自走 probe が観測した赤 node は 13 件、本走の実測は 15 件で、
  差の 2 件は probe が走らせなかった側の test file にあった。他の 7 変異は完全一致だった。
- 根本原因: probe を「変異ごとに必要な 1 file だけ」に絞ったこと。絞り込みは
  計算ノード混雑下で 1 変異 12 分 × 2 file × 8 変異 = 2.5 時間を避けるための判断だったが、
  **検査を弱める向きの変異 (負例側) は影響が局所に留まる一方、検査を強すぎる向きへ倒す変異
  (正例側 = 過剰拒否) は、その検査を通る全ての正例を赤にするため影響が file を跨ぐ。**
  絞り込みの可否は変異の向きで決まるのに、向きを見ずに一律へ絞った。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M08` が要求する「期待 node は完全集合」を
  満たすため、**`category: positive` の変異 (過剰拒否の正例) は probe でも本走と同じ file 集合を
  走らせる**。負例側だけを絞ってよい。判定は spec の `category` field で機械的に決まる。
- 再発検知: 本走が `MISMATCH` を返したとき、実測 node が probe の未走行 file に属するかを
  最初に見る。属していれば本項の型であり、変異の設計ではなく probe の絞り方を直す。

### {{F:mutation-timeout-vs-queue-override}}. D612 の queue-wait 上書きを付けたまま変異 harness を起動すると spec の timeout を超えて起動前に rc=2 で拒否される [手順漏れ]

- 事象: 変異本走 attempt 1 が走行ゼロで `rc=2` になった。本文は
  `mutation collection の外側 timeout が明示された dispatch 待機契約より短い:
  timeout_seconds=2400.0, queue_wait_timeout_s=3600.0, overall_grace_s=600.0`。
- 根本原因: 計算ノード混雑時に D612 の opt-in 上書き
  (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` /
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`) を runner script へ入れたまま
  変異 harness を起動したこと。harness は spec の `timeout_seconds` が
  `queue_wait_timeout_s + overall_grace_s` 以上であることを要求する。既定 (900+300=1200) なら
  2400 に収まるが、上書き後は 4200 になり収まらない。
  **上書きは焦点走・受入では有効だが、変異 harness には spec 側の制約として跳ね返る。**
- 恒久対応: 変異 harness の runner script に D612 上書きを入れない。混雑で queue 待ちが必要なら
  spec の `timeout_seconds` を上書き後の和より大きく取り、`hang_timeout_seconds` が
  job walltime 未満である `DW-M06` の制約と両立するかを起動前に確かめる。
- 再発検知: `mutation harness aborted:` で始まり 3 つの秒数を並べる本文が出たら本項である。
  再試行の前に runner script の `export IZANAGI_DISPATCH_*` を読む。
