---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t1941-backoff-requested-us
seq: 1
---

## 新規

### {{F:nested-patch-flock-self-wait}}. 同一treeのnested patch contextが自分のflockを待ち続けた [手順漏れ] [資源競合]

- 事象: T-1941診断attempt 2でfixed patch適用後にCPU timeが約6秒のまま10分以上停止し、shared submoduleがdirtyになった。
- 根本原因: 同一treeへ`patchharness.applied()`を入れ子にし、別fdで同じexclusive flockを再取得した。
- 恒久対応: `orchestrator/campaign/backoff_requested_us.py`は`patchharness.checkout()`の一意tree内でfixedとdiagnosticを逐次適用し、finallyでtouch path unionを復元する。
- 再発検知: `test_measure_uses_real_isolated_checkout_for_fixed_then_diagnostic`とMU-13がshared baseへの逃げを検出する。

### {{F:fixture-executor-patch-divergence}}. fixtureのGNU patch緑がproduction git apply失敗を隠した [テスト代表性]

- 事象: T-1941診断attempt 3でGNU `patch --fuzz=0`済みのdiagnostic patchがproduction `git apply`に拒否された。
- 根本原因: patch形式testがfixture executorだけを使い、production executorと3行context要件を実走しなかった。
- 恒久対応: `test_fixed_then_diagnostic_uses_production_git_apply_and_reverts_clean`がproduction `patchharness.apply_patch`でfixed→diagnostic→revertを実走する。
- 再発検知: 関連testとMU-01/MU-02をproduction同型patchへ照準する。
