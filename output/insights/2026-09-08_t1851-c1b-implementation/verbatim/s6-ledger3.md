## 総括

- tool 出力:

```text
excluded_failure_or_error=0
mode=add-only
added=242
skipped_existing=165
excluded_frozen_removed=0
excluded_writer_base_key=0
excluded_frozen_suite=0
excluded_total=0
```

- `nodeid_count`: 19,761 → 20,003
- 追加 nodeid 内訳:
  - `test_attempt_registry_core_s8b_profile.py`: 33
  - `test_s8b_attempt_registry.py`: 88
  - `test_s8b_floor_attempt_launcher.py`: 49
  - `test_s8b_terminal_evidence.py`: 72
- 指定外 file からの追加: 0
- 削除: 0
- main 側既存 duration value の変更: 0
- `schema_version=1`、`unit=seconds`: 不変
- `git diff --stat`:

```text
orchestrator/tests/acceptance_duration_ledger.json | 4048 +++++++++++---------
1 file changed, 2144 insertions(+), 1904 deletions(-)
```

変更対象は台帳 1 本だけです。`git add`、`git commit`、`git merge` は実行していません。

実走範囲は `orchestrator/tests/test_update_acceptance_duration_ledger.py` の全 nodeid 24 件です。

```text
24 passed in 2.35s
```

`orchestrator/tests/test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact` を含め、全件緑です。