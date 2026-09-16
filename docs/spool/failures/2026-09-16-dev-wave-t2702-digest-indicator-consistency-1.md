---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2702-digest-indicator-consistency
seq: 1
---

## 再発

### F273

- **再発: 2026-09-16** — [T-2702] wave で、統合 commit 直後の full-history provenance 監査 (計算ノードへ
  dispatch) が Bash tool の 120 秒上限で背景へ回った直後に、親が同一 worktree から焦点走を投入し、監査側の
  pending orphan hold (`phase: pending-qsub`) を run_tests が検知して rc=16 (`child_started=false`,
  `reason=orphan-hold`) になった (`DW-O26` の直列化義務違反、親の操作ミス)。監査は request 1944.nqsv で
  走り切り rc=0、hold は監査終端で自然に解除、焦点走は再投入で 6135 passed。qdel も hold の手動削除もしていない。
  既存恒久対応に修正すべき新事実はない — 背景へ回った dispatch は「完了通知まで同一 worktree から次の
  dispatch を投げない」対象に含める、の適用漏れである。
