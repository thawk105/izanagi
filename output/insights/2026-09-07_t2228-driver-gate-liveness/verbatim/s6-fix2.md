## 追記した内容

[orchestrator/tests/test_hooks.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2228-fix2/orchestrator/tests/test_hooks.py) の 2 つの literal golden に、指定された 2 path を辞書順で追記しました。

- `.pbs`: class=`dispatch-required`、PBS job body の4 field
- `.py`: class=`dispatch-required`、compute-side driver の4 field

## registry 現物との一致確認

AST と JSON による全体比較を実施しました。

- `_PEGASUS_EXPECTED_ENTRIES == registry["entries"]`: 一致
- `_PEGASUS_EXPECTED_CLASSES`: 全 path・class が一致
- 両 golden の辞書順: 正常
- 比較 rc=0

## 走らせた検査 (nodeid と rc)

- `orchestrator/tests/test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`
  - runner rc=16
  - `qstat -Q` preflight の infrastructure failure
  - `child_started=false` のためテスト本体は未実走
- `git diff --check -- orchestrator/tests/test_hooks.py`: rc=0

## 未実走・未確認

指定 nodeid の pytest 本体は dispatch infrastructure failure により未実走です。

## 総括

実装済みです。registry 現物との完全一致は独立比較で確認済みです。runner が生成した一時 dispatch ファイルは除去し、現在の変更対象は `orchestrator/tests/test_hooks.py` だけです。commit・push・docs 編集は行っていません。