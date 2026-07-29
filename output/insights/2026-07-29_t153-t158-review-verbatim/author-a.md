## 変更ファイル・主要箇所

- [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:178)
  - `_normalize_args()`：位置 target と閉集合の path option を呼出元 cwd 基準で正規化
  - `_is_acceptance_run()`：[line 359](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:359)
  - `_preflight_unstaged_deletions()`：[line 394](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:394)
  - `_preflight_submodule()`：[line 459](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:459)
  - `_call_and_record()` の cwd 強制：[line 584](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:584)
  - `main()` の正規化・preflight 配線・非記録 cwd 強制：[line 644](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:644)
- [test_run_tests_preflight.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_preflight.py:1)：新規 41 node。tmp git repo、配線変異、GIT_* 消毒、self-runnable footer。
- [test_run_tests_task_run.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_task_run.py:50)：記録・非記録 subprocess の cwd call-shape 追随。
- [test_run_tests_nproc.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_nproc.py:161)：main call-shape の cwd 追随。

## 現行挙動 → 新挙動

| 対象 | 変更前 | 変更後 |
|---|---|---|
| 相対 target | 呼出元 cwd のまま pytest を起動し、repo 外からの正当な相対 target が不安定 | 実在する位置 target を呼出元 cwd 基準で絶対化し、pytest は repo cwd で実行 |
| path option | 相対値を無加工 | `--rootdir`、`--confcutdir`、`--basetemp`、`--junitxml`、`--log-file` の両形式を絶対化 |
| 非 path option | 無加工 | 引き続き無加工。`-k` 等の値を path と誤認しない |
| suite identity | 相対・絶対表記が分裂し得る | 正規化後 argv を利用。full-suite identity の意味は不変 |
| 未 stage 削除 | acceptance run でも受理 | 検出時 rc=3。`git add -A` を案内 |
| 削除 bypass | なし | `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS=1` の exact 値のみ。警告付き。`final` では拒否 |
| 削除検査の git 異常 | 検査なし | 警告して続行 |
| submodule 欠落 | 無検査で pytest へ進む | acceptance run は自動 init 後に marker 再確認、欠落継続なら rc=4 |
| targeted run の欠落 | 無検査 | init せず警告継続 |
| no-execution shape | 無検査 | submodule preflight を skip |
| git 環境 | 継承 | 両 preflight とも全 `GIT_*` を除去 |

既存の正当な緑を維持しつつ、相対 target 修復による受理拡大と、削除・submodule 欠落の fail-closed による拒否追加を行っています。

## 実行テスト

必須範囲：

- `orchestrator/tests/test_run_tests_preflight.py`
- `orchestrator/tests/test_run_tests_task_run.py`
- `orchestrator/tests/test_run_tests_nproc.py`
  - 最終結果：`98 passed`
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_dev_waves_isolation_contract.py::test_every_node_that_touches_process_external_resources_stays_serialised`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - 最終結果：`3 passed`

追加確認：

- `python3 orchestrator/tests/test_run_tests_preflight.py`：`41 passed`
- `orchestrator/tests/test_dev_waves_checker.py`：`12 passed`
- `python3 tools/check_codex_agents.py`：OK
- `python3 tools/check_docs.py`：違反なし
- `git diff --check`：違反なし

変更前 baseline は既存 2 ファイルで `57 passed`。作業途中に call-shape assertion 追随ミスで以下が一時的に赤になりましたが修正済みです。

- `test_opt_in_keeps_pytest_argv_and_records_monotonic_result`
- `test_sidecar_setup_and_record_failures_preserve_rc_and_output`
- `test_lazy_import_failure_preserves_child_rc_and_output`

最終赤はありません。受入全走は親の統合走に委ね、本実走では実施していません。

## 所有外への波及可能性

- `tools/dev_waves/cli.py`：`orchestrator/tests` 指定が acceptance run となり、新 preflight と repo cwd 強制を受ける。
- `tools/dev_waves/git_state.py` / `tools/dev_waves/checker.py`：`tools/run_tests.py` を trust-root として扱う。関連 checker テストは緑。
- `orchestrator/tests/conftest.py`：task-run sidecar hook の子プロセス cwd が repo 固定になる。task-run テストで記録・非記録両経路を確認済み。
- `tools/task_runs`：正規化後 argv から suite identity を得るため、相対・絶対表記が統一される。full-suite identity は不変。
- README・runbook 等からの repo-root 呼出し：通常のコマンド形は維持されるが、acceptance preflight が追加される。
- 共有 fixture、conftest、README allowlist は未編集。hash・時刻などの揮発 payload を期待値へ固定していない。

## 変異対応

| 変異 | kill test |
|---|---|
| V1 削除 gate の main 配線除去 | `test_main_deletion_preflight_failure_is_wired_before_xdist` |
| V2 submodule gate の main 配線除去 | `test_main_submodule_preflight_failure_is_wired_before_xdist` |
| V3 記録経路の cwd 除去 | `test_opt_in_keeps_pytest_argv_and_records_monotonic_result`、`test_lazy_import_failure_preserves_child_rc_and_output` |
| V4 非記録経路の cwd 除去 | `test_opt_out_preserves_exact_command_and_call_shape`、`test_sidecar_setup_and_record_failures_preserve_rc_and_output` |
| V5 位置 target 絶対化除去 | `test_main_assembles_absolute_relative_target_from_other_cwd` |
| P1 acceptance 判定恒真化 | `test_targeted_run_does_not_invoke_deletion_gate` |
| P2 非 acceptance まで submodule fail-closed | `test_targeted_missing_submodule_warns_without_init` |

## 総括

完了。author A の項目 1〜7 を所有 4 ファイル内で実装し、最終赤はありません。git commit・git 状態変更・docs 編集は行っていません。残る懸念は親環境での受入全走と、実 submodule auto-init の独立確認です。sandbox 由来の index lock エラーは今回発生していません。