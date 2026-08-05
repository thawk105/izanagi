## 総括

`pytest` の既存非実行判定を baseline 残余走査にも限定適用しました。docs・registry・テスト期待値は変更せず、commit もしていません。

変更箇所:

- [`_baseline_first_token_violation()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1111): pytest 引数を受け取り、既存 `_pytest_nonexecuting()` が真の場合だけ重量対象拒否を除外。
- [`_interpreter_residual_violation()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:1135): 実際に解析できた pytest module 呼び出しの引数だけを上記走査へ渡す。
- `orchestrator/tests/test_hooks.py` は今回編集していません。

| 判定 | 綴り |
|---|---|
| ALLOW | `python3 -m pytest --collect-only` |
| ALLOW | `python3 -qm pytest --help` |
| ALLOW | `python3 -m pytest --version` |
| ALLOW | `python3 -mpytest tools/check_ai_provenance.py --collect-only` |
| DENY | `python3 -c 'print(1)' -m pytest` |
| DENY | `python3 -m pytest orchestrator/tests/test_hooks.py` |
| DENY | `python3 -mpytest tools/run_tests.py` |
| DENY | `pytest -q` |
| DENY | `python3 --help tools/pegasus/collect_receipt.py` |
| DENY | `python3 -W tools/pegasus/exec_calibrate.py /tmp/safe.py` |
| DENY | `python3 -BmcProfile -o tools/pegasus/exec_calibrate.py /tmp/safe.py` |
| DENY | `python3 -BmcProfile -- tools/pegasus/exec_calibrate.py --help` |
| ALLOW | `python3 -c 'print(1)' tools/pegasus/exec_calibrate.py` |
| ALLOW | `bash -c 'true' tools/pegasus/certify_calibration.sh` |
| ALLOW | `bash --rcfile tools/pegasus/certify_calibration.sh -c 'true'` |
| ALLOW | `python3 -Bmpydoc -n localhost tools/pegasus/exec_calibrate.py` |

実施した検査:

- 判定核 `decide()` による上記16綴りの直接検査: 全件期待どおり
- 過剰許可防止 control 3件: 全件 DENY 維持
- `python3 -m py_compile hooks/guard_bash.py`: 成功
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: 成功
- pytest: 未実走。現在地が Pegasus ログインノード `pegasus02` のため、規律上実行不可

指定された pytest 非実行集合以外に動かした受理集合はありません。追加 control の `python3 --help pytest --help`、`bash --help pytest --help`、`python3 -m py.test --help` はいずれも DENY のままです。