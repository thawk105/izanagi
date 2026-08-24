---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1431-floor-pilot-submit
seq: 4
title: [T-1431] 床値 pilot が初めて完走し、床値の実測値が得られた (計測、request 945229.nqsv、12 セル 96 attempt すべて valid・除外 0・retry 0)
---

## 本文

- 到達不能述語の修正を local main へ land した直後に床値 pilot を再投入し、
  **12 セル全部が計測へ到達して完走した (`driver_rc=0`)。** 過去 3 回
  (`926261` / `940170` / `944884`) はいずれも計測到達セル 0 だったので、床値の実測値が
  得られたのは今回が初めてである。逐語は
  `output/insights/2026-08-25_t1431-floor-pilot-values/README.md`。
- 床値案は `rr20` が `scalar_alt=3.555e+04` (scale_ref=1.185e+06)、
  `rr80` が `scalar_alt=4.551e+04` (scale_ref=1.517e+06)。
  floor_pair は両 holdout とも全 5 pair で scalar_alt と同値である。
  **これは floor の「案」であって何も発効していない。** `eligible_for_refreeze=false` は
  `mode=pilot` によるもので、freeze への書込みは別の判断による。
- 走行は健全だった。96 attempt すべて `valid=True`、除外 session 0 件、retry 0 件
  (台帳の 96 行はすべて `kind=planned`)。`retry_slots_per_cell=2` は 1 枠も使っていない。
  各 attempt の所要は 26.79〜26.93 秒に収まり、外乱の兆候はない。
  `machine_anomaly` セルも両 holdout とも無し。
- **一回性 key は今回初めて消費した。** 計測に到達した以上は設計どおりである。
  過去 3 回は計測前に停止したため消費 0 枚だった。
- 投入元 commit は `e540eca316ef4086847c797fb97fa312f02168c1`、
  submission nonce は `5dfef3f7f1981b5694889f7a0f9f270b`。
  所要は job の Elapse で約 48 分。
- perf は `mode=disabled, reason=nonzero-rc`。本機で perf を要求しない既定方針どおり
  blocker としない。

## 次の一手差分

### 完了

- [T-1431] 床値 pilot を実投入し、床値の実測値を得た。停止していた到達不能述語も同 wave で
  直して land 済みである。得られた床値は pilot の「案」であり、freeze への発効は別項へ送った。
  remaining: none
  base: f5efce18f134098c40b68a8a2b429a0c387d6aa1930ce8e928b35795221048b8

### 新規

- {{T:floor-proposal-to-freeze-ruling}} **P1・新規**: pilot が出した床値案
  (`rr20`=3.555e+04 / `rr80`=4.551e+04) を freeze へ発効させるかを裁定する。
  pilot の `eligible_for_refreeze` は false であり、official 走行を要するのか、
  pilot の案をもって `s8b_oracle_driver.py gate-check` の `floor-null` refusal を
  解いてよいのかを決める。逐語は
  `output/insights/2026-08-25_t1431-floor-pilot-values/README.md`。
