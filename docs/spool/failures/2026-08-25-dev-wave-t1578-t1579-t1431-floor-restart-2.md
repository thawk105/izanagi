---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1578-t1579-t1431-floor-restart
seq: 2
---

## 再発

### F136

- **再発: 2026-08-25 ([T-1578]/[T-1579] wave)** — 並行 dispatch を作ったのが操作者ではなく
  **受入ツール自身**だった点が新しい。受入全走を 1 本だけ投入し、その最中に repo へ何も書いて
  いないのに、`test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系が 11 件赤になった
  (11 failed / 15217 passed / 60 skipped)。差分の実体は junit の
  `first extra item: ('dir', 'task-runs/reports')`、すなわち `output/task-runs/` の増加である。
  受入 shard 分割 (D710) は同じ作業木から 2 本の PBS request を**同時に**投入する
  (実測: 944371 と 944372 が重なり、shard-1 が 00:21:56、shard-0 が 00:24:13 に終了)。
  一方の shard の task-run 記録がもう一方の shard の snapshot 区間へ入る。
  shard の dispatch receipt 自体は repo 外の shard session root へ逃がされているため、
  汚染源は receipt ではなく task-run report である。
  既存の恒久対応は「同じ作業木から dispatch を伴う走行を 2 本以上同時に投入しない」であり、
  操作者が 1 本しか投入していない本件へは届かない。**射程の外側で同型が再生産されている。**
  帰属は 3 点で否定した。(1) wave の差分は `launch_cert` / `certificate` を 1 箇所も参照しない、
  (2) 同 file の焦点走は 817 passed で緑、(3) official / pilot 50 件の単独走は 43 秒で全緑。
  再投入 (attempt 2) は 15228 passed / 60 skipped / 0 failed で receipt が出た。
  恒久対応は本 wave の scope 外として追加していない。task-run 記録の書き出し先を
  shard session root へ逃がす seam (`dispatch_compute.dispatch()` の `output_root` と同型) を
  受入 shard 経路へ通すのが筋だが、受入基盤の所有 wave の判断に委ねる。
- **再発検知の補強**: 赤が `_real_output_snapshot` 系だけで、junit の diff が
  `task-runs` または `pegasus-dispatch` の dir 増加を指すなら、操作者が並行投入していなくても
  本件型である。単独再走と受入再投入の両方で消えることを確かめる。
