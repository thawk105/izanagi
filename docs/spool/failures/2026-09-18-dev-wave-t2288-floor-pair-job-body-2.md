---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2288-floor-pair-job-body
seq: 2
---

## 再発

### F100

- **再発: 2026-09-18** (同日 2 回目、near miss、実害なし) — 隔離 worktree の session が変異 harness の `--plan-only` を打つ前に Bash で `cd <変異 container worktree> && pwd` (読み取りだけ) を実行し、harness の追跡 cwd がその worktree へ移った。`EnterWorktree --path <自分の wave worktree>` で即復帰し、以後は container への操作をすべて `.sh` (内部で `cd`) 経由にした。書き込みは発生していない。同型: 他 worktree での command 実行は launcher script に閉じ込め、対話 shell で `cd` しない。

### F1012

- **再発: 2026-09-18** ([T-2288] job body wave) — 新規契約 test `test_child_rc_collection` の TERM 経路 (job body の `run_driver` が TERM を trap して記録し、child の rc を回収する) が login では緑、計算ノードへ dispatch した焦点走 (request 5523.nqsv) では `reason=completed` の赤 (期待 `signal_observed`)。原因は同じ SIG_IGN の継承 — bash は入口で ignore された signal を trap できず、`kill -TERM "$PPID"` が無視された。対処は test の `_bash()` が bash を exec する前の子で `SIGTERM/SIGHUP/SIGINT` を `SIG_DFL` に戻し `pthread_sigmask(SIG_UNBLOCK)` する (T-2676 の既存例と同じ形)。期待値は緩めていない。production 側 (job body の TERM trap) も計算ノードでは発火しない可能性があり、`docs/pegasus-runbook.md` §7.8 に「trap の存在を終了記録の保証と読まない」と明記した。一次資料 `output/insights/2026-09-18/t2288-floor-pair-job-body/README.md`。
