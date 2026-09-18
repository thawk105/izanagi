## 変更 file と関数 (file:line)

所有6ファイルに実装・テストを追加しました。

- `tools/dev_waves/git_state.py:232`：`commit_worker_worktree`。指定5操作だけをallowlistに追加。残差commit、拒否・延期、provenance正規化、一時message削除を実装。
- `tools/dev_wave_codex.py:227,342`：`_launcher_argv`、`main`。receipt/job-id保持、launcher復帰後の保存、rc合成。
- `tools/dev_wave_wait.py:1591,1632,1964,4450`：parser、`wait_for_producer`、`main`。絶対pathのopt-in、死亡確定後の保存、失敗時のreceipt公開抑止。
- `orchestrator/tests/test_dev_waves_git_state.py:1341`：helperの5テスト追加。
- `orchestrator/tests/test_dev_wave_codex.py:680`：起動器の4テスト追加。
- `orchestrator/tests/test_dev_wave_wait.py:5120`：待ち手の4テスト追加、許可されたoption集合更新。

## 受理・拒否挙動

従来の「残差を保存せず終了」から、workspace-writeのauthor/fixはlauncher復帰後に残差をcommitする動作へ変更しました。

- 主checkout・detached・main/master・root不一致：`refused`。
- 操作進行中：`deferred`。
- launcher非0：元のrcを維持。launcher成功＋保存拒否/失敗：rc=3。
- 待ち手：opt-in時だけ死亡確定後に保存。既存成功＋保存拒否/失敗は`producer-commit`でfail-closed。
- flag無し・read-only・dry-run・check-onlyは既存経路を維持。bytes不変の実Git比較テストは追加済みですが未実走です。

## 実走・直接呼び出しの結果

**pytest未実走。実装済み・実Git検証未実走であり、closedではありません。**

`git add/commit/checkout`等の全面禁止と実Git検証の指定が重なるため、一時repo内操作の確認を出しましたが、回答は未受領です。禁止コマンドは実行していません。

直接呼び出しで以下の17ケースが`DIRECT_CALL_PASS`：

```text
test_dev_waves_git_state.py::
  test_git_command_table_has_no_forbidden_mutating_verb
  test_commit_diff_disables_move_detection_by_contract
  test_landed_diff_commands_pin_merge_and_root_contract
  test_commit_parent_command_is_one_ordered_batch

test_dev_wave_codex.py::
  test_dry_run_stage_and_lane_matrix
  test_paths_and_job_id_are_deterministic
  test_resource_defaults_and_overrides

test_dev_wave_wait.py::
  test_producer_commit_worktree_requires_absolute_path
  test_producer_cli_surface_has_no_pattern_input
  test_producer_waits_while_pid_alive_then_completes_after_death
  test_producer_check_only_requires_receipt_file
  test_producer_check_only_success_is_single_pass_and_publishes_receipt
  test_producer_start_time_change_is_original_process_death
  test_producer_zombie_is_dead_even_when_kill_zero_succeeds
  test_producer_file_visibility_grace_is_bounded
  test_producer_dead_without_required_file_fails_closed[done]
  test_producer_dead_without_required_file_fails_closed[artifact]
```

相対path拒否を一時的に無効化すると、`test_producer_commit_worktree_requires_absolute_path`が`COUNTERFACTUAL_KILLED`。実装は復元済みです。登録済みM0〜M14は未実走です。

6ファイルのAST検査、`git diff --check`は通過。既存288テスト本文は指定例外以外不変、`_run`・`_git_env`もASTで不変を確認しました。

## 所有外 caller・共有 fixture・consumer test の波及可能性 (静的列挙)

- plain runner：helper側5件、起動器側4件とも引数なしで収集可能。rc・拒否条件の組合せはテスト内ループで実装しています。
- `_Effects`、`_FakeEffects`、共有`conftest.py`は変更なし。
- `git_state`既存caller：`checker`、`daemon`、`cli`、`dev_wave_land`、`dev_wave_submodule_init`、`spool_fold`。既存関数契約は変更なし。
- `GIT_COMMANDS`の既存禁止verb検査は直接呼び出し通過。
- `_check_dev_wave_waiter_consumer_pins`はdocs consumer文面とtarget実在を検査。今回のCLI追加を直接pinしていません。
- `test_dev_waves_isolation_contract.py`はintegrationテストの隔離を対象とし、今回の追加テストは対象外です。

## 期待赤

親docs未landに起因するfinding集合は未確定です。consumer pin実走とdocs全検査を完了していないため、「期待赤なし」とは判定していません。

## 総括

所有6ファイルだけを変更し、docs・commit・破棄操作は行っていません。残る受入作業は、一時repoを使う追加テストの実走、M0〜M14の変異検証、親docs統合後の検査です。

consumer pinの読み取り検査は、保護パスとheredocの組合せを分類不能とする`guard_bash`の自動承認レビューに拒否され、実行できませんでした。