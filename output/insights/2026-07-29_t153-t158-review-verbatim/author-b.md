実装範囲 author B の全項目を完了しました。編集は指定された新規 4 ファイルのみで、commit・stage・docs 編集は行っていません。

## 変更ファイルと主要関数

- [tools/check_wave_startup.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_wave_startup.py:34)
  - `_git`: GIT_* 除去、read-only command 閉集合、`--no-optional-locks`
  - `check_repository`: fresh/resume の全検査集約（139行）
  - `main`: CLI と rc 変換（187行）
- [tools/check_codex_output.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/tools/check_codex_output.py:37)
  - `_without_fenced_code`: backtick fence 除去
  - `check_file`: file種別・10MB・raw bytes・見出し検査（55行）
  - `main`: CLI、regex 検証、rc 変換（112行）
- [test_check_wave_startup.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_wave_startup.py:36)
  - tmp git repo fixture、fresh/resume 全 gate、V6/V7/P4、passive Git 契約
- [test_check_codex_output.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-b/orchestrator/tests/test_check_codex_output.py:25)
  - regular/symlink/FIFO、10MB、raw bytes、fence、V8/V9/P3

## 受理・拒否仕様

| Checker | rc | 条件 |
|---|---:|---|
| wave startup `fresh` | 0 | HEAD=local main、main以外のbranch、rebase/mergeなし、clean、markerあり、指定時はhandoff残置なし |
| wave startup `resume` | 0 | rebase/mergeなし、markerあり、指定時はhandoff残置なし。HEAD前進・dirty tree・branch状態は拒否しない |
| wave startup | 1 | 適用 gate が1件以上失敗。全件を是正案付きで stderr に列挙 |
| wave startup | 2 | argparse の不正引数 |
| Codex output | 0 | regular file、10MB以下、raw bytesが閾値以上、fence外本文が見出しregexに一致 |
| Codex output | 1 | 不在・symlink・FIFO・directory、10MB超、byte不足、見出し不足、read失敗。検査可能な理由を全列挙 |
| Codex output | 2 | `--min-bytes < 1` または不正regexなどの引数エラー |

qsub 有効性および総括と本文の意味整合が scope 外であることは各 `--help` に明記しました。

## 実行テスト

必須 checker 範囲:

- `orchestrator/tests/test_check_wave_startup.py` 全15 node: **15 passed**
  - `test_fresh_normal_worktree_is_accepted`
  - `test_default_repo_is_current_working_directory`
  - `test_fresh_rejects_head_ahead_of_local_main`
  - `test_fresh_requires_non_main_branch[main|detached]`
  - `test_resume_rejects_rebase_or_merge_state[rebase-merge|rebase-apply|MERGE_HEAD]`
  - `test_fresh_rejects_dirty_tree`
  - `test_resume_rejects_missing_submodule_marker`
  - `test_external_handoff_gate_is_opt_in`
  - `test_resume_accepts_head_advance_and_dirty_tree`
  - `test_git_wrapper_is_sanitized_and_read_only`
  - `test_git_execution_error_becomes_aggregated_failure`
  - `test_help_discloses_qsub_is_out_of_scope`
- `orchestrator/tests/test_check_codex_output.py` 全14 node: **14 passed**
  - 正常、multibyte、small、fenced、missing heading、複数違反
  - non-regular `[directory|symlink|fifo]`
  - 10MB上限、custom regex
  - invalid arguments `[args0|args1]`
  - help scope
- 合計: **29 passed in 0.44s**

必須 meta node:

- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_dev_waves_isolation_contract.py::test_every_node_that_touches_process_external_resources_stays_serialised`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- 結果: **3 passed in 1.53s**

追加確認:

- self-runnable 直接実行: **15 passed / 14 passed**
- `python3 tools/check_codex_agents.py`: **OK**
- `python3 tools/check_docs.py`: **違反なし**
- 赤・xfail・skip: **なし**

## 所有外への波及可能性

- 親所有の DW-O20 / DW-O01 caller から両CLIを呼ぶ配線が必要です。現時点のコード内には既存 caller はありません。
- `tools/dev_waves/git_state.py` は `tools/check_*.py` と `orchestrator/tests/` を trust-root digestへ自動編入するため、統合commit後は trust-root digestが変化します。
- `tools/dev_waves/checker.py` の `CheckSpec` は両新規CLIを固定checkとして受理できる既存パターンです。
- shared fixture は `tmp_path`、`monkeypatch`、`capsys` のみ。`conftest.py` は未編集で、git変更は各tmp repo内に隔離しています。
- collection consumer は plain-runner、dev-wave isolation、real-repo serialization。新規nodeにreal-repo markerや共有外部資源はなく、指定meta-testは緑です。
- 親による全受入走・docs配線・統合commitは本実走の代替外です。

## 変異対応表

| 変異 | kill test |
|---|---|
| V6 submodule検査恒真化 | `test_resume_rejects_missing_submodule_marker` |
| V7 clean-tree検査恒真化 | `test_fresh_rejects_dirty_tree` |
| V8 min-bytes検査恒真化 | `test_small_fragment_is_rejected_even_with_heading` |
| V9 fence除去を外す | `test_fenced_heading_does_not_satisfy_requirement` |
| P3 heading regex不能化 | `test_normal_output_is_accepted` |
| P4 fresh HEAD検査恒偽化 | `test_fresh_normal_worktree_is_accepted` |

## 総括

author B の実装・単体検証は完了。赤はありません。懸念は所有外である親のdocs caller配線、trust-root digestを含む統合commit後検証、受入全走が未実施である点のみです。