## 総括

**B2修正とM9テスト追加は実装済みです。ただし全走に1件の赤と所有外callerの追従が残り、完了条件は未達です。** 編集は2ファイルのみ。commitはしていません。

- [submission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-f2-t126/orchestrator/qualification/submission.py:112)の112・164・215行で、CLIの`repo_root`を依存解決へ渡しました。**hydrate済みcheckoutでも一時展開先を読んで拒否 → checkout stagingから解決して受理**。gflags欠落はrc=2で拒否します。env上書き、`_dependency()`、build argv、code identity集合は維持しています。
- **同型の誤りは他3ファイルにはありません。** `identity.py:228`は`git_repo_root`を使用。`t126_driver.py:1332,1377`と`collector.py:1464–1467,1516`はattemptの所属checkoutを導出して渡しています。3ファイルとも未編集です。

**M9期待node（新設）**

`orchestrator/tests/test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[hydrated]`

負例も新設しました：

`orchestrator/tests/test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[missing-gflags]`

実Git fixtureをarchive展開し、本物の`submission.py`を`-I -B`で実行します。依存解決のstubはありません。

**実走結果**

すべて指定の自走harnessを使用しました。

| 対象 | 結果 |
|---|---|
| 新設2nodeの選択実走 | 2 passed、rc=0 |
| 下記既存3node＋新設2node | 5 passed、rc=0 |
| `test_t126_pegasus_tools.py`全走 | **277 passed／1 failed、rc=1** |
| `test_plain_runner_coverage.py`全node | 3 passed、rc=0 |
| `test_ccbench_spawn_sites.py`全node | 47 passed、rc=0 |
| `test_official_perf_closure.py`全node | 7 passed、rc=0 |
| `git diff --check` | rc=0 |

選択実走した既存nodeは、同じ`test_t126_pegasus_tools.py::`配下の以下です。

- `test_fake_qsub_qstat_exact_visibility_and_durable_receipt`
- `test_identity_consumer_rejects_protocol_policy_dependency_and_build_argv_tamper`
- `test_submit_unsupported_policy_perf_uses_canonical_degraded_toolchain`

**残件・波及**

- 赤：`test_t126_pegasus_tools.py::test_submit_rejects_symlink_component_hidden_drift_and_skip_worktree`。単独でもrc=1。共有`_submit_fixture()`がstaging用に作った`output/env`へsymlinkを作ろうとして、submit実行前に`FileExistsError`になります。期待赤にはせず、回帰として報告します。裁定範囲を広げるfixture修正は行っていません。
- 所有外caller：`tools/pegasus/probes/t293_perf_site_probe.py:783`の`prepare_toolchain(policy)`は必須`repo_root`引数への追従が必要です。所有外のため未変更です。
- consumerへの波及：submit shellのCLIは変更不要。driver／collectorの依存再検証と`official_perf_closure`の構造検査は上記結果のとおりです。共有fixtureは未変更です。
- **削除したtest関数：0件。** 既存122関数のAST不変を確認しました。
- 実job投入・計算ノード走行は**実装済み・未実走**。M9変異本走も未実施です。

全走ログ：[t548-f2-t126-full.log](/tmp/t548-f2-t126-full.log)