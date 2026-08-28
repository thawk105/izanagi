---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t2000-legacy-build-probe
seq: 2
---

## 新規

### {{F:t2000-runner-env-representativeness}}. pure probe testがrunnerのselector表現とcompute環境を代表しなかった [テスト代表性]

- 事象: T-2000のexact-node gateとcompute scratch gateはpure testを通ったが、実tests dispatcherはnodeidをabsolute pathへ正規化し、ambient TMPDIRを供給しないため、real request 2回が3 arm前で停止した。
- 根本原因: pure fixtureが親promptのrepo-relative argvとambient TMPDIR前提をそのまま再現し、`tools/run_tests.py` とcompute job scriptが作る実consumer入力を通していなかった。
- 恒久対応: `orchestrator/manual_probes/test_t2000_legacy_build_probe.py` の `test_t2000_real_invocation_gate_*` でrelative/absolute正例と誤root負例を固定し、`test_t2000_compute_scratch_binding_is_exact` でrunbookの `/scr/$PBS_JOBID` 導出と負例を固定した。
- 再発検知: pure 14 exact nodeと通常suite境界meta-testを `tools/run_tests.py --force-dispatch` 経由で実走する。
