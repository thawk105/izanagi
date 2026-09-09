---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2503-pbs-binding
seq: 2
---

## 再発

### F273

- **再発: 2026-09-10** — 親が同一 worktree へ `check_ai_provenance.py` の full 監査と
  変異走行を続けて投入し、監査側の pending orphan hold を変異 harness が検知して停止した
  (`DW-O26` の直列化義務違反、親の操作ミス)。監査自身も QUE 10 本 / RUN 0 本の窓で
  `queue-wait-timeout` になった。直列化の義務は `DW-O26` に書かれているが、同節の題は
  「焦点走の consumer test 拡張」であり、条件 dispatch 表でも受入・テスト前の条件からしか
  引かれない。変異走行の直前に読む節 (`DW-M05`) からは到達しない。

### F932

- **再発: 2026-09-10** — D612 の opt-in 上書きを queue-wait 3600 秒 / grace 600 秒で当てた結果、
  事前登録済み spec の `timeout_seconds=1800` を上回り、変異走行が 1 走も始まらなかった。
  `qstat` の request ID が実際には進んでいる (988638〜642 が既に完了) ことを実測して、
  上書きを 1200 秒 / 300 秒へ下げ、spec を書き換えずに走らせた。
