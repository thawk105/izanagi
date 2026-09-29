## 総括

Stop hook と配線を実装し、focus ログで失敗した既存テスト 3 本を compare-and-delete の呼出し形へ追随させました。**pytest は未実走**です。commit・push はしていません。

## 変更一覧

- [tools/dev_wave_cleanup_stop_hook.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup_stop_hook.py:30): linked worktree の land 判定、5 秒以内の Git 判定、fail-open の `decide()` と `main()` を追加。
- [.claude/settings.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/.claude/settings.json:47): Stop を配線。既存 PreToolUse 4 本は変更なし。
- [orchestrator/tests/test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_hooks.py:5249): 配線と Stop の正負例、timeout、stdin/stdout のテストを追加。
- [orchestrator/tests/test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_dev_wave_cleanup.py:271): 指定の 3 テストで観測する argv を `update-ref -d` に変更。wave 本体の `branch -d` 期待は維持。

## テスト実走

- `test_hooks.py` の `cleanup_stop` 群と `test_settings_json_wires_all_hooks`、`test_dev_wave_cleanup.py` の指定 3 nodeid、制約 meta-test `test_pytest_collection_config.py`：**未実走**。`tools/run_tests.py` は各範囲で queue 事前確認に失敗し rc=16。指定どおり試した直接 pytest は `guard_bash` に拒否されました。
- 実 Git の手動 smoke では、commit 0 件・未 land は通過、fast-forward land 後は block、`stop_hook_active=true` は通過。Python 構文、settings JSON、`git diff --check` は通過しました。これらを pytest の緑とは扱いません。

## 変異 M9〜M12 の対応 test

| 変異 | 対応 test |
|---|---|
| M9 | `test_cleanup_stop_active_allows_landed_wave` |
| M10 | `test_cleanup_stop_allows_wave_with_zero_commits` |
| M11 | `test_cleanup_stop_allows_unlanded_wave` |
| M12 | `test_settings_json_wires_all_hooks` |

変異実走による単一理由性は未確認です。

## 波及の静的列挙

所有外の直接 caller は `tools/check_docs.py`、consumer test は `test_check_docs.py` と `test_branch_rescue_ledger.py` です。設定を読む test は `test_codex_hooks.py`、`test_dev_waves_cli.py`、`test_dev_waves_integration.py` などにあります。共有 fixture は `orchestrator/tests/conftest.py`、test file の収集制約は `test_pytest_collection_config.py` にあります。これら所有外ファイルは変更していません。

## 未了・リスク

pytest と制約 meta-test の結果は、計算ノードへの投入が復旧するまで確認できません。今回の hook は 91 行、追加テストは 300 行以内です。