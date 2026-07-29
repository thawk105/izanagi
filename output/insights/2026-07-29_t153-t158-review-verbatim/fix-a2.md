## 所見対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| New-1 | closed | `PYTEST_ADDOPTS` を `.strip()` 判定し、空白のみでも deletion gate が発火 |
| New-2 | closed | argv を closed set で逐次消費する default-deny 判定へ変更。未知 long/short option を拒否 |
| R2-2 | closed | 親裁定残余の auto-init に `--no-fetch` を追加し、call shape を固定 |

## 変更箇所

- [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/tools/run_tests.py:366)
  - acceptance default-deny: 366–421
  - `--no-fetch`: 580–585
  - mode: `100755`
- [test_run_tests_preflight.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t153-author-a/orchestrator/tests/test_run_tests_preflight.py:136)
  - 正例・未知 option 負例: 136–182
  - V14: 191–197
  - V15: 388–414

`test_run_tests_task_run.py`、`test_run_tests_nproc.py` には第2巡で追加変更なし。docs 編集・commit ともに実施していない。

## 実行結果

- Nodeid 選択:
  - `orchestrator/tests/test_run_tests_preflight.py`
  - `orchestrator/tests/test_run_tests_task_run.py`
  - `orchestrator/tests/test_run_tests_nproc.py`
  - 結果: `133 passed in 1.89s`
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
  - 結果: `1 passed in 0.05s`
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff HEAD --check`: rc=0
- 失敗・期待赤: 0件

## V14/V15 kill 対応

- V14: `test_v14_whitespace_only_addopts_keeps_default_deletion_gate`
  - `.strip()` 除去時は空白 ADDOPTS が acceptance を外れ、期待 rc=13 に対して rc=0となり赤。
- V15: `test_v15_acceptance_missing_submodule_initializes_no_fetch_with_scrubbed_env`
  - `--no-fetch` 除去時は git argv の完全一致 assertion が赤。

## 総括

New-1 / New-2 / R2-2 はすべて closed。指定検証と完了検査は全件通過し、実行 mode も `755` へ変更済み。