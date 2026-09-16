## 変更

[test_check_docs.py:2541](/work/1/SFC/tanab/izanagi/.codex/worktrees/nt-authority-pin/orchestrator/tests/test_check_docs.py:2541) の期待値のみ変更。現物を読み、26,903 bytes と確認しました。

変更前:
```python
    assert len(_read(_REPO, rel).encode("utf-8")) == 27_054
```

変更後:
```python
    assert len(_read(_REPO, rel).encode("utf-8")) == 26_903
```

## 実走

nodeid: `orchestrator/tests/test_check_docs.py::test_next_tasks_command_budget_literal_is_exact`

rc: 未取得（起動前に拒否）。指定コマンドは PreToolUse hook により、Pegasus ログインノードでの pytest 実行としてブロックされました。テスト出力はありません。

## 受理集合と波及

受理集合: pin が現物へ追随するだけで、上限 27,100 bytes と plus-one 拒否の境界は変わりません。

共有 fixture: 911–930 行は合成文字列を書き込み、実ファイルを参照しないため影響ありません。

所有外 caller・consumer test: 関数名・共有処理・fixture の変更はなく、今回の期待値変更による波及はありません。

## 総括

実装済み・未実走。`closed` ではありません。
差分は期待値 1 つのみです。commit・git add・push は行っていません。
単独 test の緑確認は親側に残ります。