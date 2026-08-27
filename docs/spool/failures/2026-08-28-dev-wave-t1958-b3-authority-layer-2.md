---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: dev-wave-t1958-b3-authority-layer
seq: 2
---

## 再発

### F273

- **再発: 2026-08-28** — T-1958 の受入 attempt 1 で
  `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[False]` が唯一の赤になった。
  failure signature は `subprocess 出力が空による JSONDecodeError` で、同一 tip の exact node 単独走は
  `1 passed in 5.60s`、次の全走は `18499 passed / 62 skipped` で緑。赤時の login node load average は
  `133.54 / 92.32 / 60.27`、並行 `codex_worker_launch.py run` は 4 本だった。原因は未確定のまま、
  ユーザー指示により exact-node hold を先行し、後続で原因分析・修理・再導入する。registry validator は
  evidence section に exact function 名を要求するため、D95 author は本再発の fold 前には正しく停止した。
