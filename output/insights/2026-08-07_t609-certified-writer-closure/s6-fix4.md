変更は指定どおり 1 ファイル・2 箇所のみです。

- [test_campaign.py:4495](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix4-a/orchestrator/tests/test_campaign.py:4495)
- [test_campaign.py:4537](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix4-a/orchestrator/tests/test_campaign.py:4537)

変更前:

```python
*, build_context,
```

変更後:

```python
*, authorization_contract,
build_context,
```

`authorization_contract` はデフォルト値なしの必須 keyword-only 引数です。

検証状況:

- `git diff --check`: 成功
- 差分は `orchestrator/tests/test_campaign.py` の当該 signature 2 箇所のみ
- assert、期待値、関数本体、production コード、docs は変更なし
- 対象 2 nodeid は `tools/run_tests.py` 経由で起動したものの、Pegasus の `qstat -Q preflight rc=1`、runner rc=16 によりテスト本体は未実走
- add、commit、push は未実施

## 総括

指定された最小修正は実装済みです。変更範囲外への波及はなく、テストは dispatch infrastructure failure のため未実走です。