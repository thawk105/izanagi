---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t1942-between-run-floor-wl
seq: 1
title: [T-1942] 走行間ばらつきの下限を write-heavy と balanced について Pegasus 計算ノードで測り read-heavy と揃えた — between CV は 0.95% / 0.73% (docs + 成果物、branch worktree-dev-wave-t1942-between-run-floor-wl、実装面の差分 0)
---

## 本文

- **D1638 / D1639 の委任に従い、既存 driver `orchestrator/campaign/between_run_floor.py` (無変更) で
  write-heavy (rr5) と balanced (rr50) の between-run noise floor を Pegasus 計算ノードで測った。**
  成果物は `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.{json,md}` と
  同 `_rr50_rmw0.{json,md}` (driver の create-only 出力の複写)。一次資料と読み方は
  `output/insights/2026-09-05_t1942-between-run-floor-write-balanced/README.md`。
- 素材: Pegasus (Xeon Platinum 8468、48 thread、records 1,000,000、extime 3 s、stock silo、trace-disabled) の
  走行間ばらつきの下限は write-heavy 0.95% (within 2.70%、abort 79%、median 2,280,352 tps)、
  balanced 0.73% (within 1.18%、abort 68%、median 3,796,356 tps)、read-heavy 0.22% (既測、within 1.00%、abort 15%)。
  3 点とも between < within で、abort 率が高いほど between CV が大きい。旧環境 (linux-baremetal) は
  0.67% / 1.07% / 0.11%。B-4 §5 の floor には流用しない (D1639)。
- **投入経路は read-heavy 既測 (2026-08-22、job 934445) と同じ型を段 1 で実測して写した。** 使い捨て PBS body と
  login submitter (repo 外 job dir `scripts/`) を Codex `role=author` が先例から計測段だけ残して書き、
  2 workload を別 checkout (detached submit-tree) から別ノード (bnode073 / bnode100) へ同時投入した
  (同じ checkout からの同時 build は buildcache の publish 衝突で片方が落ちうる)。request 978588 / 978589、
  Elapse 232 s / 245 s、queue 待ちは 1 分未満 (gen_S QUE 140 / RUN 33 の混雑下)。
- **段 1 で判明した事実:** committed の read-heavy JSON (commit e5a0dba4c) は worklog 864 が引く job 934086 の
  出力ではなく、同日の job 934445 (bnode040) の出力である。値の差 (between 0.2174% と 0.2228%) は別走行の差で、
  誤記ではない。insight §3 に一次資料を記した。
- **検査 (軽量版、review 子なし):** repo tracked の実装面差分は 0。job body の JSON 契約検査と create-only
  preflight を親が逐語切り出しで正例 1 / 負例 2 ずつ実測し (M1 / M2)、実 job 2 本を正例とした。
  受入全走の結果は段 9 の追記 commit に書く。
- エージェント工数: Codex author 1 本 (受理)、計測 job 2 本 (計算ノード約 4 分ずつ)。段 2・3・6 の子は省略。

## 次の一手差分

### 完了

- [T-1942] write-heavy / balanced の between-run noise floor を Pegasus で測り、read-heavy の既測と揃えた
  (between CV 0.95% / 0.73%、成果物は `output/env/pegasus/calibration/`、insight
  `output/insights/2026-09-05_t1942-between-run-floor-write-balanced/README.md`)。B-4 §5 の floor は
  [T-2140] の計画で別に測る。official 実測は [T-2324] 側が持つ。
  remaining: none
  base: f2b6553ba60d1d5be806d14e9a4d6fee12a87a14d5353f18625aeb90bcb0ed6b
