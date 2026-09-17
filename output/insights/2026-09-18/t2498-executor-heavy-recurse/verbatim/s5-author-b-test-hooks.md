## 追加したテスト (node id 一覧)

- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_module_denied`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_coverage_denied`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_script_denied`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_nonexecuting_and_light_allowed`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_nonrefusing_sites_unchanged`
- `orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_existing_denials_preserved`

## 実測 (直接呼び出し、現行 main での挙動)

以下の関数名は共通prefix `test_bash_login_executor_recursion_` を省略しています。

| 関数 | 直接呼び出し結果 |
|---|---|
| `module_denied` | AssertionError。全14コマンドを個別確認し、現行ALLOW |
| `coverage_denied` | AssertionError。全3コマンドが現行ALLOW |
| `script_denied` | AssertionError。1コマンドが現行ALLOW |
| `nonexecuting_and_light_allowed` | PASS（8形） |
| `nonrefusing_sites_unchanged` | PASS（3形 × 2サイト） |
| `existing_denials_preserved` | PASS（3形） |

`python3 -qmcProfile -m pytest` は現行でも拒否されるため、負例から外して既存拒否の再掲へ移しました。

構文検査はファイルを生成しない `compile()` で成功。`git diff --check` も成功しました。pytestは実行していません。

## 変異との対応

| 変異 | 検出関数・専属killer候補 |
|---|---|
| M1 | 負例3関数で再帰欠落を検出 |
| M2 | `module_denied`: `python3 -m cProfile -m pytest -q` |
| M3 | `coverage_denied`: `python3 -m coverage run -m pytest -q` |
| M4 | 正例関数: `python3 -m cProfile -m pytest --collect-only` |
| M5 | `script_denied`: `python3 -m cProfile pytest -q` |
| M6 | 正例関数: `python3 -m runpy tools/pegasus/exec_calibrate.py` |

変異実測は未実施です。M2・M3・M5はそれぞれ対応する負例関数に分離しています。

## 総括

指定位置に6関数・76行を追加しました。変更は `test_hooks.py` のみで、既存本文が変更されていないことも機械確認済みです。`git add`・`git commit` は実行していません。