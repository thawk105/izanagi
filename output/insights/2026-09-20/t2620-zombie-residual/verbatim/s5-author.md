## 変更点

変更は [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2620-unit-tests/orchestrator/tests/test_codex_worker_launch.py) のみです。

- 1564〜1585行：`orphan_running`／`orphan_zombie`／`orphan_mixed` を追加。
- 1619〜1654行：`_write_subreaper_harness` を追加。`waitid(WNOWAIT)` で回収対象を特定し、state を読んでから `waitpid` で回収。
- 4545〜4650行：共通観測・単一 dict 比較・`finally` の後始末を追加。
- 1131、1147〜1148行：起動 helper に省略可能な `on_completed` callback を追加。rc 検査前に観測と stderr を確保。

追加テスト：

| 名前 | 行範囲 |
|---|---|
| `test_t2620_orphan_running_is_rejected` | 4653〜4656 |
| `test_t2620_orphan_zombie_is_rejected` | 4659〜4662 |
| `test_t2620_sigterm_ignore_subreaper_is_rejected` | 4665〜4668 |
| `test_t2620_orphan_mixed_is_rejected` | 4671〜4674 |
| `test_t2620_check_receipt_rejects_residual_only_changes` | 4677〜4695 |

## 実走

指定された `PYTHONPATH=. python3 -c "...pytest.main(...)"` 形式で実走しました。

- 追加5本：**5 passed / 0 failed**、19.04秒。
- 関連既存12本：**12 passed / 0 failed**、9.34秒。
- `git diff --check`：正常。失敗 assertion はありません。

nodeid はすべて `orchestrator/tests/test_codex_worker_launch.py::` を接頭辞とします。追加分は上表の5本、既存分は以下です。

```text
test_positive_p1_normal_job_is_accepted
test_sigterm_ignoring_child_is_killed
test_sigterm_child_pid_registration_regression_detector
test_setsid_escape_is_not_claimed_as_contained
test_group_member_count_reports_identity_missing_source
test_group_member_count_reports_scandir_failure_source
test_group_member_count_reports_stat_read_failure_source
test_group_member_count_reports_stat_parse_failure_source
test_group_member_count_records_malformed_without_changing_count
test_unknown_residual_source_propagates_without_verifying_normal_reap
test_unknown_residual_source_propagates_through_terminate
test_check_receipt_rejects_impossible_truth_table
```

全走・変異走は実施していません。

## 波及

- fake の追加分岐は新しい3 mode 名だけに一致します。既存 mode の分岐・期待値は変更していません。
- 起動 helper の既存 caller は callback 省略時の従来処理を継続します。`orchestrator/tests` 内に対象ファイル外からの参照はありません。
- `_base_command`、`_run_case`、共有 fixture、既存 consumer test は変更していません。
- production の consumer は正常回収、強制停止、receipt 封印、sidecar、writer truth、checker。強制停止が依存する `worker.py` の群走査も変更していません。
- production 差分ゼロ。`git add`／`commit`／`stash`／`checkout` は実行していません。

## 現行の受理・拒否挙動

N1・N2a・N2b・N4 共通の期待値：

```python
termination_verified = False
accepted = False
outcome = "not_accepted"
launcher_rc = 1
```

| 負例 | `process_group_residual` | `stop_reason` | `limit_trigger` | `codex_exit_code` | 外部真値 |
|---|---:|---|---|---:|---|
| N1 生存子 | 1 | `max_attempts` | `None` | 0 | 子 state が S または R |
| N2a ゾンビ | 1 | `max_attempts` | `None` | 0 | 対象 pid を Z で回収 |
| N2b 強制停止 | 1 | `wall_clock_admission_bound_s` | 同左 | -9 | 対象 pid を Z で回収 |
| N4 混在 | 2 | `max_attempts` | `None` | 0 | 生存子 S/R ＋対象 pid を Z で回収 |

各 sidecar の期待値は以下です。`final_count` は上表の残存数です。

```python
{
    "final_count": residual,
    "final_unknown_source": None,
    "unknown_sources_seen": [],
    "proc_stat_malformed": False,
}
```

harness 使用3例は `harness="subreaper"`、`harness_launcher_rc=1`、`zombie_reaped_as_Z=True`。N2b の `termination_signals_sent` は `["SIGTERM", "SIGKILL"]` です。

N3 は元 receipt の checker が rc 0。残存数だけを `None`／`1` に変えた双方で rc 2、`attempt.accepted semantic binding` による拒否を確認しました。

根拠は `tools/codex_worker_launch.py` の以下の行です。

- 1727〜1728：state を除外せず PGID 一致を加算。
- 1845〜1868：強制停止・正常回収の残存数と検証結果。
- 1984〜1993：attempt の受理条件。
- 701〜708、2430〜2433：sidecar の残存観測。
- 2493〜2506：outcome・stop reason・rc の決定。
- 3942〜3954：checker の accepted 束縛。

## 総括

実装済み：3 mode、subreaper harness、負例5本。関連を含む17本 passed。  
未実走：全走・変異走・異常経路への意図的な故障注入。  
未着手：なし（本 author 依頼の実装範囲）。