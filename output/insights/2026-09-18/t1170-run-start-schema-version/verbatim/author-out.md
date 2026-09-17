## 変更 hunk

- [autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1170-run-start-schema-version/orchestrator/campaign/autonomous_trial_completeness.py:428)
  - 428–429行：説明コメントと独立リテラル `_RUN_START_SCHEMA_VERSION` を追加。
  - 2242–2254行：run-start 版検査を置換。
- [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1170-run-start-schema-version/orchestrator/tests/test_autonomous_trial_completeness.py:2898)
  - 2898–2938行：指定2テストの run-start 拒否期待を全文一致へ変更。report 側の期待は維持。
  - 2941–3001行：指定4テストを追加。

変更後の版検査全文：

```python
    recorded_version = start.get("schema_version")
    if recorded_version != _RUN_START_SCHEMA_VERSION:
        generation = (
            "legacy"
            if recorded_version == "p3-autonomous-workload-trial/v3"
            else "unknown"
        )
        _fail(
            "run-envelope",
            "run-start.schema_version unsupported: "
            f"recorded={recorded_version!r}; generation={generation}; "
            f"consumer_supported={_RUN_START_SCHEMA_VERSION!r}",
        )
```

## 受理・拒否挙動 (新旧)

受理する版は新旧とも v4 のみで、変更後は consumer の独立定数で固定し、その他の形検査は従来どおりです。
v4 以外・欠落は引き続き拒否し、版 gate 到達時の理由を旧 `[run-envelope] run-start.schema_version does not match producer version` から `[run-envelope] run-start.schema_version unsupported: recorded=…; generation=…; consumer_supported='p3-autonomous-workload-trial/v4'` に変更しました（v3 だけ `legacy`、それ以外は `unknown`）。

## 実走結果

**合計295 passed、0 failed。**

以下のファイル名はすべて `orchestrator/tests/` 配下です。

| 実走対象 | 結果 |
|---|---|
| `test_autonomous_trial_completeness.py` 全287 node | 287 passed（200.42秒） |
| `test_p3_autonomous_workload_trial.py` 指定2 node | 2 passed、288 deselected |
| `test_plain_runner_coverage.py` 全3 node | 3 passed |
| `test_s8c_preregistration_invariant.py` 制約3 node | 3 passed、17 deselected |

本体全走には次の変更・追加 node を含みます：

```text
test_autonomous_trial_completeness.py::test_report_and_run_start_schema_versions_are_required[report]
test_autonomous_trial_completeness.py::test_report_and_run_start_schema_versions_are_required[start]
test_autonomous_trial_completeness.py::test_role_schema_v4_and_report_schema_v3_are_required
test_autonomous_trial_completeness.py::test_run_start_v4_without_binding_is_accepted
test_autonomous_trial_completeness.py::test_run_start_v3_legacy_shape_is_rejected
test_autonomous_trial_completeness.py::test_run_start_unknown_schema_version_is_rejected
test_autonomous_trial_completeness.py::test_run_start_schema_version_is_independent_of_producer
```

統合正例・meta-test の nodeid：

```text
test_p3_autonomous_workload_trial.py::test_transport_admission_error_persists_verified_partial_report
test_p3_autonomous_workload_trial.py::test_fixture_trial_runs_ycsb_abc_and_binds_descriptor
test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted
test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries
test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable
test_s8c_preregistration_invariant.py::test_machine_contract_function_names_exist_and_checked_set_is_exact
test_s8c_preregistration_invariant.py::test_machine_contract_exclusion_pin_cannot_be_omitted
test_s8c_preregistration_invariant.py::test_machine_contract_rejects_prewave_accept_trial_name
```

`git diff --check` も成功。AST比較で、他の既存テスト・共有 fixture の変更と関数削除がないことを確認しました。

## 波及の静的列挙

- 所有外 caller：`p3_autonomous_workload_trial.py`、`trial_registry.py`、`s8c_acceptance_receipt.py`。完全性検査経由で今回の診断変更が届き得ます。
- 直接 import するテスト：`test_layer3_admission_diagnosis`、`test_p3_autonomous_workload_trial`、`test_s8c_acceptance_receipt_v2`、`test_role_session_isolation`、`test_layer3_report`、`test_trial_registry`。
- 共有 fixture：`test_role_session_isolation` が本体テストを import して `_complete_trial` を使用。fixture は無変更です。
- 間接参照・静的制約：`test_s8c_preregistration_invariant`、`test_s8c_arm_inputs`、`test_s8c_preregistration_predicates`、`test_reflux_formal_consumer`、`test_official_perf_closure`。
- Python ソース全体を検索し、旧 run-start 拒否文言を固定する他ファイルは検出しませんでした。旧文言の残存は report 側のみです。

上記 consumer 群の全面実走・変異検査・受入全走は今回未実施で、親の統合検証対象です。

## 総括

指定2ファイルの実装と要求された実走を完了しました。docs・producer・共有 fixture は無変更、状態を変える git 操作は実行せず、未コミット差分を残しています。