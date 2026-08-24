---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1636-dangling-argv-batch
seq: 2
---

## 再発

### F24

- **再発: 2026-08-25** — `tools/dev_wave_wait.py producer` を背景 job で張った段 6 fix の待ち手が、producer 生存中に **exit 0 かつ出力ゼロ**で偽完了した。`.done` は不在、launcher pid は経過 1 分 24 秒で生存しており、実際の完了は約 8 分後だった。既存の恒久対応 (待ち手の rc を信じず `.done` の exit code と producer 生死で判定する) がそのまま効き、`git diff` が未変化であることと `ps -p` の生存で誤完了を弾いて待ち手を張り直した。本 wave の追加事実は無く、2026-08-17 / 2026-08-23 と同型の 3 度目である。

## supersede 追記

- F526 **supersede: 2026-08-25** — 恒久対応の「分割実行への是正は本 wave の編集面の外」は解消した。`_landed_reference_matches()` は {{D:git-grep-batch-dual-limit}} の二重上限で分割実行し、再発検知は変異 15 件 (全件 KILLED) と `SC_ARG_MAX` 由来の母集合で pin した。argv 上限の手前で `SIGKILL` される領域があることも同時に判明したため、上限は byte だけでなく本数にも掛けている。
