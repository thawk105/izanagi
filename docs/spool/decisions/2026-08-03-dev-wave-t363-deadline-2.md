---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-03
wave: dev-wave-t363-deadline
seq: 2
---

## {{D:run-observation-deadline}}. dispatch の実行監視予算は「rc=0 の RUN 初観測」から数える

**決定:** `tools/pegasus/dispatch_compute.py` の監視 deadline を二段階にする。

1. **pre-RUN**: 従来どおり `submitted_at` 起点で、実効上界は
   `min(submitted + queue_wait_timeout_s, submitted + walltime_s + overall_grace_s)`。
2. **post-RUN**: `qstat` が rc=0 で当該 request を含み、パーサが最初に `RUN` と判定した観測時刻から
   `walltime_s + overall_grace_s` へ**一度だけ**張り直す。

張り直しの latch は `run_seen` とは別に持つ。`run_seen` / `queue_wait_s` /
`queue_wait_observed` / `state_history` / receipt schema の意味は変えない。

**射程 (この決定が保証しないこと):**

- 起点は scheduler 上の実 RUN 開始ではなく**親の初観測**である。両者の差 (poll 粒度、qstat 所要、
  `pre-running` を RUN と分類すること) は残る。
- rc≠0 の stdout に `RUN` が含まれるだけでは張り直さない。後続の rc=0 の RUN で回復する。
- RUN を観測できないまま実際は走行中のジョブ (UNKNOWN、未認識状態、poll での見逃し) は保護しない。
- **infra error 時に走行中ジョブへ qdel を打つ経路そのものは変えていない。**
  したがって本決定は D131 の共通前提 6 (「`total_deadline` の修正**と** active job に対する
  qdel の禁止」) の前半だけを満たす。

**理由:**

- 順番待ちには `queue_wait_timeout_s` という独立した上界が既にある。同じ待ち時間を実行監視予算からも
  差し引くのは二重計上であり、超過時に `_best_effort_qdel` が走行中ジョブを殺していた。
- 早期 qdel の成立条件は概ね `Q < W+G < Q+D` (Q=順番待ち、W=walltime、G=grace、D=実行時間)。
  既定 (W=30 分、G=300 秒、queue 上限 900 秒) の受入全走はこの条件を満たしうる実経路である。
- 張り直しを rc=0 に束縛するのは、信頼できない観測で予算を延ばさない fail-closed 側の選択である。
  ただし latch を `run_seen` と共有すると偽 RUN が回復経路を潰すため、latch を分離する。

**却下した選択肢:**

- **pre-RUN 段を `queue_wait_timeout_s` 単独へ委ねる** — 未知状態のまま滞留するジョブの上界が
  queue 上限だけになり、既存の受理集合 (未知状態の overall 上界) を変える。
- **任意の `RUN` 文字列で張り直す** — rc≠0 の malformed 出力や schema drift でも予算が延び、
  監視が実質無制限へ倒れうる。
- **UNKNOWN を RUN 扱いして保護する** — scheduler の schema drift と malformed 出力を長時間受理する
  ことになり、正しさ防壁を緩める方向である。別途、権威ある証拠での RUN 確認として設計する。
