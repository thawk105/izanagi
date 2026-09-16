## 総括

**E3-1・E3-2 を実装し、指定の3テストは全走で赤0でした。commit はしていません。**

- **E3-1:** fixture の `output/env` を repo 外の `outside` へ移し、元の位置から symlink を張りました。staging の gflags／glog は引き続き `output/env` の symlink 成分を通って到達します。rc=2・既存診断文の assert を維持し、出力が増えないことも検査しています。
- **E3-2:** probe の1呼出しを `prepare_toolchain(policy, repo_root=repo_root)` に変更しました。既存の checkout root を使用しています。
- **F2 保護対象:** `submission.py`・M9 の2 node は変更前と同一。共有 fixture も未変更です。
- **削除した test 関数：0件。**

すべて指定の自走 harness で実行しました。

| 全走対象 | 結果 | rc |
|---|---:|---:|
| `orchestrator/tests/test_t126_pegasus_tools.py` | 278 passed | 0 |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | 47 passed | 0 |
| `orchestrator/tests/test_plain_runner_coverage.py` | 3 passed | 0 |
| `git diff --check` | 成功 | 0 |

T-126 全走には以下の nodeid を含み、いずれも成功しています。

- `test_t126_pegasus_tools.py::test_submit_rejects_symlink_component_hidden_drift_and_skip_worktree`
- `test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[hydrated]`
- `test_t126_pegasus_tools.py::test_archived_submission_uses_checkout_dependency_staging[missing-gflags]`

[全走ログ](/tmp/t548-f4-t126-full.log)