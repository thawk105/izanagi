## 変更 file と要点

指定 5 file の実装・編集を完了しました。commit・git add はしていません。

| file | 全行数 | 変更 |
|---|---:|---|
| `tools/cleanup_remove_dirs.py` | 262 | 固定 rm 起動、PGID 検査、signal 転送、有界取消、最終 lstat・JSONL 集約 |
| `orchestrator/tests/test_cleanup_remove_dirs.py` | 296 | S2 の全ケース、自走 harness。追加で NUL・表記拒否を検査 |
| `.claude/commands/cleanup-branches.md` | 87 | exact 文案 v2 |
| `tools/check_docs.py` | 6879 | SHA 定数のみ |
| `orchestrator/tests/test_check_docs.py` | 12759 | 指定 SHA・synthetic 本文・予算 fixture のみ |

文書の実測値：

```text
6201 bytes
a6380f90dcaf8e5e5ac21cc9af0619e000697816257f3e3e8a8844595dad1f26
```

synthetic 本文との byte 一致も確認済みです。

## 実走結果

**pytest は未起動です。緑とは報告できません。**

pegasus02 の規律に従い、以下を `python3 tools/run_tests.py` 経由で実行しました。共通追加引数は `-n 0 -p no:cacheprovider`、環境は `PYTHONDONTWRITEBYTECODE=1` です。

| 引数 | 結果 | 起動試行時間 |
|---|---|---:|
| `orchestrator/tests/test_cleanup_remove_dirs.py -rf -q` | rc 16、子未起動 | 0.23 秒 |
| `orchestrator/tests/test_check_docs.py -rf -q -k cleanup` | 同上 | 0.24 秒 |
| `orchestrator/tests/test_branch_rescue_ledger.py orchestrator/tests/test_plain_runner_coverage.py -rf -q` | 同上 | 0.18 秒 |
| 下記 meta-test 群 `-rf -q` | 同上 | 0.42 秒 |
| 新規 test の `--collect-only -q` | 同上 | 0.65 秒 |

全試行の原因は `qstat -Q preflight rc=1`、`child_started=false`。実走 nodeid はなし、passed／failed／skipped は未集計です。

実行できた検査：

- `python3 tools/check_docs.py`：rc 0、違反なし。
- `python3 tools/check_codex_agents.py`：rc 0。
- `git diff --check`：rc 0。
- 新規 2 file の AST parse：成功。

上記 checker の総所要秒数は未計測です。

新規テストの予定 nodeid は、`orchestrator/tests/test_cleanup_remove_dirs.py::` を接頭辞として以下の 36 件です（角括弧内は各 parameter）：

```text
test_two_dirs_removed_without_wrapper
test_children_share_parent_pgid_then_remove
test_launcher_signal_is_forwarded_before_removal[TERM, INT, HUP]
test_timeout_is_interrupted
test_failed_path_does_not_hide_other_removal
test_usage_rejects_paths_without_removal[
  nested, duplicate, relative, missing, symlink, mid-symlink,
  file, root, trailing-slash, dotdot, empty, double-slash, dot]
test_usage_rejects_cwd_inside_target[exact, descendant]
test_usage_rejects_invalid_options[
  no-separator, no-paths, unknown, missing-value, nonnumeric,
  nan, infinity, zero, negative, duplicate]
test_nul_path_is_rejected_before_spawn
test_zero_returncode_with_existing_path_is_failed
test_nonzero_returncode_with_absent_path_is_failed
test_summary_never_succeeds_for_incomplete_results
```

## 制約 meta-test の洗い出し

以下を確認しました。pytest 結果はいずれも未取得です。

- `test_plain_runner_coverage.py`：新規 file に既存と同形の harness を実装。
- `test_pytest_collection_config.py`：全 file を指定して起動試行。
- `orchestrator/test_selection_contract.py`：test file ではなく共有契約 module。検査は上記 collection test に含まれます。
- `test_login_headroom.py::test_local_budget_constants_are_defined_only_in_login_headroom_leaf`：新規 tool/test も走査対象。起動試行済み。
- `test_pegasus_dispatch_compute.py::test_best_effort_qdel_production_caller_is_only_fresh_gate`：同上。
- `test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`：新規 tool が走査対象。起動試行済み。
- 共有 `conftest.py` と `test_real_repo_serialization.py`：一時領域・収集時の契約を確認。後者は未実走。

allowlist・除外表・資源分類 registry は変更していません。

## 現行の受理・拒否挙動と本変更の関係

§1〜§3 の削除述語は不変です。launcher は所有・取込・占有検査を代替しません。

入力表記は、実在する正規形の絶対 directory path、途中を含め symlink なし、相互非包含、cwd が対象外、に限定します。違反は全子起動前に rc 64。取消・不明は rc 2、通常失敗は rc 1、全件撤去確認時だけ rc 0 です。

親の dogfood 用 CLI 例（未実走）：

```bash
# 正例：所有確認済みの使い捨て directory を対象外 cwd から指定
python3 tools/cleanup_remove_dirs.py -- /tmp/t2665-dogfood-target

# usage 負例：rc 64、stdout 空
python3 tools/cleanup_remove_dirs.py --timeout-seconds 0 -- /tmp/t2665-dogfood-target
```

## 波及の静的列挙

- caller：cleanup command §3。`tools/dev_wave_cleanup.py` は不変。
- consumer：文書 SHA checker、synthetic command、予算 test、branch rescue ledger test。
- 共有 fixture：`tmp_path` と既存 conftest。共有 fixture の編集なし。
- overlay skill、docs、tools README、資源分類は不変。
- runner が失敗 receipt を `output/pegasus-dispatch/` 以下へ自動生成しました。手動編集・削除はしていません。git status の変更対象は指定 5 path だけでした。

## 未実走・未完了

pytest 全件の実走・受入確認が未完了です。dispatch 障害解消後の再実行が必要です。変異検査、親 dogfood、commit は未実施です。

## 総括

S1〜S3 のコード・テスト・exact 文案を実装しました。
文書は 6201 bytes、指定 SHA と一致しています。
docs・Codex checker は rc 0 です。
pytest は基盤障害で未起動のため、受入完了とはしていません。
commit・push・git add は行っていません。
