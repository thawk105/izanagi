---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2621-land-budget-closure
seq: 1
title: [T-2621] land の lock 待ち予算は D1996 のとおり 2026-09-14 に着地済みで、carry と F975 の恒久対応欄だけが stale だった (docs のみ、branch worktree-dev-wave-t2621-land-budget-closure)
---

## 本文

- ユーザー依頼は「[T-2621] land の共通 lock 待ち窓を lock 外の provenance 監査が食い潰す構造
  (F975) を D1996 のとおり直す」で、`tools/dev_wave_land.py` の定数 (65 行)、
  `_run_outside_land_lock` (4059 行)、窓を計算する 3 箇所 (4980 / 5016 / 5302 行) を名指し、
  裁定の逐語を現物で確かめること、rc=21/22/29 の意味が変わっていないことを既存テストで示すこと、
  本題の 1 定数の意味変更と配線だけに留めることを求めていた。
- **段 1 の前提実測で依頼の前提が覆った。D1996 は 2026-09-14 に実装済みで、依頼が名指した行は
  すべて是正後の姿だった。** 追加実装は無く、実装面の差分はゼロである。照合は D1996 の 3 条項で
  行った。(a) 累積予算化 — `_run_outside_land_lock` の docstring は「guard 完了後、残りの
  累積競合待機予算で再取得する」で、5016 / 5302 行が `max(0.0, _LAND_LOCK_WAIT_SECONDS -
  waited_s)` を渡す (= 監査後と fold gate 後の両方)。4980 行だけが窓開始 + 180 で、これは純粋な
  lock 待ちである初回取得なので裁定どおり。定数は 180.0 据え置き。(b) reason 文の分離 —
  `budget_exhausted_before_attempt` が `wait budget already exhausted; tried once without
  waiting` と `wait budget exhausted after waiting` を出し分ける。(c) 窓の内訳 — `waited_s` /
  `window_elapsed_s` を結果 JSON へ出し、窓に入る前に終わった経路では両 key を省く。
- 着地 commit は `0ec8d0faf`「fix(land): lock 待ち予算を lock 外の作業時間に食わせない」
  (2026-09-14 12:29:13 +0900)。`git merge-base --is-ancestor 0ec8d0faf HEAD` が真。記録は
  `docs/archive/worklog-phase3-0914-1487.md` で、**T-758 の docs 訂正と同じ branch
  (`worktree-dev-wave-t758-docs-corrections`) に別の変更単位として載っていた。**
- **carry が自走した経路も確定した。** entry (1487) は本文で D1996 の実装を記録した一方、
  次の一手 delta の `完了` 節へ `T-2621` を書いていない (同 file を grep して 0 件)。その後
  2026-09-16 の /rulings 第 18/19 回が状態語を継承し、D2044 項 6 は「entry (1527) が本項を
  D1996 により実装手番へ更新済みなので、状態語は重ねない」と明記した。依頼引数もその状態語を
  写した。F35 の 4 件目の再発として記録した。
- **docs 側には実作業が 1 件あった。** F975 の恒久対応欄が「未実施」のままで、台帳の運用規則
  「恒久対応は実体へのポインタ必須」に反していた。canonical の既存 bytes は不変なので
  `supersede 追記` の 1 行挿入で現況へ改めた。D432 の旧条項 (取得点ごとに同じ絶対 deadline を
  渡す) は D1996 側が supersede を記録済みで、decisions canonical は追記のみのため D432 への
  後注は作れず、作業も不要と裁定した。
- 実測 (親): 焦点走 `orchestrator/tests/test_dev_wave_land.py` は **320 passed / 1 skipped
  (18.97s、Pegasus request 582.nqsv、Elapse 24S)**。skip は main に既登録の flaky hold
  (`test_exploration_external_root_keeps_wave_clean`) で本 wave に帰属しない。rc=21
  (`RC_CONTROL_PLANE`) を 15 箇所、rc=22 (`RC_IDENTITY`) を 5 箇所、rc=29 (`RC_PROVENANCE`) を
  14 箇所で assert するテストが含まれ、いずれも緑である。`test_cumulative_wait_budget_*` 8 本は
  再取得へ渡る値が残予算であること (`(180.0, True, 20.0), (160.0, False, 160.0)`) を assert し、
  満額補充と絶対期限の復活の両方を殺す。430 秒監査の後でも実競合を待って着地する正例も併置。
- 子エージェントは 0 本 (実装面の差分ゼロ・docs のみ)。`DW-S04` により変異 matrix は免除し、
  受入全走は免除せず実施した。land のコードは 1 byte も変えていない。

## 次の一手差分

### 完了

- [T-2621] D1996 の 3 条項がいずれも現行 main に実装済みであることを一次資料 (決定逐語・
  docstring・pickaxe・8 本の境界テスト) で確定し、F975 の恒久対応欄を現況へ改めた。
  追加実装は無い。
  remaining: none
  base: c9d9799f5dda2e5c3def37fa11277f6be09040fe07b02c6d14385e19599c5653
