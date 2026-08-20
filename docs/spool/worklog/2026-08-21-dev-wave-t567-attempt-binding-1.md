---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t567-attempt-binding
seq: 1
title: '[T-567] verify_done/bench_done を実行 attempt ID に束縛し、consumer は committed attempt record だけを投影するよう実装した (コード+テスト、branch worktree-dev-wave-t567-attempt-binding、変異matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- commit: `6130a1b9` [T-567] verify_done/bench_done を実行 attempt ID へ束縛 (Core: wal.py
  attempt topology 検証拡張・replay_admitted_records 新設、pipeline.py の build_attempt_id
  伝播、digest.py の committed projection 移行)。`40aded54` は統合後の4ファイル全体走で
  発覚した test_critic.py 既存 fixture の回帰 fix (新設検証ロジック自体は無傷)。
- 段3敵対相談・段6レビューA/Bが共に独立発見した real 所見2件 (`load_verify_abort_signals()`
  の旧 attempt フォールバック抜け穴、`load_workload()` の legacy WAL 破壊) は fix1巡目で解消。
- 変異matrix確定走行は Pegasus queue 混雑 (`qstat -Q gen_S` 実測 RUN=118/QUE=23) で2回目が
  pytest collection dispatch の queue-wait-timeout (rc=16) により未完。spec の timeout margin
  拡大 (1800→3000s、`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=1800`) の上で3回目を確定
  (baseline PASSED、5/5 KILLED、MISMATCH 0)。harness のバグではなく `bcd9c3e6` の fail-safe
  が正しく働いた結果。
- 設計判断は {{D:attempt-bound-verify-bench-signals}} (D193 の実質補完、recovery-abort/
  noncertifying semantics 自体は不変)。元起票 [T-459] 段6 レビュー
  (一次資料: docs/archive/worklog-phase3-0806-254.md:1-46, 390-393)。

## 次の一手差分

### 完了

- [T-567] verify_done/bench_done を実行 attempt ID に束縛し、consumer が committed attempt
  record だけを投影するよう検証・実装した。crash→retry・遅延 receipt・同一 variant 別
  attempt の negative fixtures を追加し、変異matrix (5/5 KILLED) で裏取りした。
  remaining: none
  base: 7bb9d8f706e6ae1fbeaa2b65c3ddcda2557573d32867a4d16c5c45f42a6df054

### 新規

- {{T:p3-s4-loop-resolve-duplicate-stale-verdict}} **P2**: `orchestrator/campaign/p3_s4_loop.py`
  の `_resolve_duplicate()` (882行目) が stale verdict を返しうる懸念を精査する
  (本 wave の scope 外、段3敵対相談で指摘のみ)。
- {{T:p3-s4-loop-records-report-inconsistency}} **P2**: `p3_s4_loop.py:993-1001` の
  records report が `_resolve_duplicate()` 呼び出し後に不整合を起こしうる懸念を精査する
  (本 wave の scope 外)。
- {{T:s8b-oracle-report-verify-state-correctness}} **P2**: `s8b_oracle_report.py::_verify_state`
  (1114行目、verify_done 複数一致で missing 扱いにする既存 fail-closed 挙動) が本 wave の
  committed attempt projection と整合するか、公式 report の正しさを精査する
  (consumer 移行の優先度: digest.py > p3_s4_loop 系 > s8b_oracle_report.py、本 wave の scope 外)。
