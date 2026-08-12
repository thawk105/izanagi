---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 7
---

## 新規

### {{F:pegasus-compute-perf-missing}}. 計算ノードに現行 kernel 用 perf が無く、測定が全滅する [ドリフト]

- 事象: 床値 campaign が `status: "completed"` / `driver_rc: 0` で返るのに、
  **120 回の測定試行が全て `launch_failure` (1 回 0.17 秒)、床値は全 null** になった。
  実際の理由は `ccbench produced no metrics. rc=2
  stderr=WARNING: perf not found for kernel 5.15.0-173`。
  計測は `perf stat` の下で行う契約なので、perf が起動しなければ 1 点も測れない。
- 根本原因: 計算ノードの kernel は `5.15.0-173-generic` だが、`/usr/lib/linux-tools/` には
  `5.15.0-100-generic` と `5.15.0-135-generic` しか無い。**kernel 更新に linux-tools が
  追随していない。** 実 campaign 2 ノード (bnode049 / bnode130) と probe 6 ノード
  (bnode013 / 021 / 023 / 027 / 031 / 032) の **8/8 で `perf stat` が rc=2**。
  login ノードは kernel `5.15.0-186-generic` で tools は 101/136/173 — 自ノード用が無い。
  第 1 世代 calibration は 2026-07 に bnode011 (同じ kernel 5.15.0-173) で perf 込みで
  取得できているため、**その後の環境更新で欠けた**。
- 恒久対応: 環境側 (管理者手番) に linux-tools を入れてもらう以外に道はない。
  **perf を外す回避を採ってはならない** — production command が測定契約に焼き込まれており
  (`s8b_floor_contract` が perf event 集合ごと記録する)、登録済み calibration も
  perf 込みで取得されている。外せば公正が崩れ、過去の値と比較できなくなる。
- 再発検知: 測定を始める前に perf の可用性を確かめる preflight を置くこと
  (現状 attestation は CPU・cache・クロックを照合するが「測定器が動くか」を見ないため、
  12 セル分の build を終えてから 120 回続けて失敗する)。
  **`driver_rc` と `status` だけを見て成功と判定しない** — 成果物の `floors` が
  実数を持つことまで確かめる。本件は rc=0 で 2 回返っている。
