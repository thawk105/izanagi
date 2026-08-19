---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1409-orphan-hold-probe
seq: 1
---

## 再発

### F383

- **再発: 2026-08-19** — [T-1409] で根本原因を切り分けた。`tools/check_acceptance_reds.py` は
  grep で qstat 参照 0 件と確認し、独自の qstat 判定ロジックを持たない
  (`tools/run_tests.py --force-dispatch` 経由で `tools/pegasus/dispatch_compute.py` の共有機構を
  呼ぶだけ)。トリガー経路は `dispatch_compute.py:1948` の
  `DispatchError("result/log/accounting-grace-expired")` (scheduler `END` 後
  `accounting_grace_s` 既定 60 秒以内に result/ログ/NQSV 会計サマリ/compute marker が揃わない) →
  `finally` の `_fresh_qstat_gated_qdel` が既に scheduler から消えたジョブを
  `success-request-absent` と分類し `gate.reason=request-absent` で保守的に latch、の 1 経路のみ。
  T-1362 land 時の実 receipt (`waiter.stdout.log`/`acceptance-receipt-1.json.acceptance-red-check.json`)
  では、同一コード・同一 nodeid・同一 probe worktree パターンへの反復投入のうち先行する複数回が
  この経路で orphan-hold に到達し、直後の試行が同一コードのまま正常完了 (`status=attributable-red`)
  していた — 決定論的なコード欠陥でなく非決定的な timing 事象と判断する根拠である。
  `check_acceptance_reds.py` の probe は短時間 dispatch を複数バースト投入する利用パターンであり、
  固定 60 秒窓が相対的に厳しくなる仮説を持つが未実測。恒久対応 (grace 窓拡張・投入間隔調整・
  `request-absent` latch 条件の見直し) はユーザー裁定へ返し、本 wave では実施しない。
