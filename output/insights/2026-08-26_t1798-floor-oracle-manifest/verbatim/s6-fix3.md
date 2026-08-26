### 直したもの (file:line)

- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1798-floor-oracle-manifest/orchestrator/tests/test_ccbench_spawn_sites.py:150)
  - `_run_git` を 1 エントリ登録。
  - 分類根拠のコメントを追加。

### `_run_git` をどの集合へ分類したか、およびその根拠

`_EXPLICIT_NON_CCBENCH_PROCESS_SITES` へ分類しました。

実行対象は sanitize 済み環境での読み取り専用 Git 照会だけです。argv は CCBench を名指しせず、実行もしないため、明示的な非 CCBench process site に該当します。

### 実走した検査 (nodeid を併記)

実走完了なし。

`python3 tools/run_tests.py orchestrator/tests/test_ccbench_spawn_sites.py` を試みましたが、`qstat -Q` の dispatch 前検査が `rc=1` となり、子プロセス未起動のまま `rc=16` で終了しました。

`git diff --check` は成功しています。

### 実装済み・未実走のもの

以下は実装済み・未実走です。

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites`

## 総括

inventory の 1 エントリだけを追加しました。検査規則、production 実装、別件の赤には触れていません。`git add`、commit、docs、remote 操作は行っていません。作業ツリーの変更は対象テストファイル 1 件だけです。