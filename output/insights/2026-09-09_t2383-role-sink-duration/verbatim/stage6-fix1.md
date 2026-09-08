## 実装した変更

- [test_p3_autonomous_workload_trial.py:1885](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1885): `do_build` assert に `wire` を追加。
- [同:1917](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1917): role 件数 assert に `(wire, role)` を追加。
- [同:1927](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1927)、[同:1928](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1928): variant 2 種の assert に `wire` を追加。
- [同:1937](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1937)、[同:1939](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1939): build 関連 2 種の assert に `wire` を追加。

## 実走した nodeid と結果

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications` を含む同ファイル全266 nodeid: `266 passed in 155.43s`
- `orchestrator/tests/test_p3_build_authority_cli.py` の自走 harness 全19 test関数: `19/19 PASS`
- `orchestrator/tests/test_reflux_originless_compatibility.py` 全2 nodeid: `2 passed in 59.14s`
- すべて `PYTHONPATH=.` 付きの自走 harnessで実行。`git diff --check` も成功。

## 変えていないことの確認

- HEAD版と作業版の全1052 assertをAST比較し、条件式が完全一致。
- `try` / `except` は追加していない。
- [集約処理:1962](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1962) と [32件検査:1970](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:1970) は無変更。
- [_ROLE_SINK_TRIAL_MAX_WORKERS:56](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py:56) は `4` のまま。
- `git diff --name-only` は指定テスト1本だけ。production、他テスト、fixtureは無変更。

## 波及

worker内の対象assertが失敗すると、`AssertionError` の messageから該当wireを判定できます。role件数失敗ではroleも併記されます。成功経路、集約結果、受理集合には影響しません。commit、push、branch操作は行っていません。

## 総括

指定された6種のper-iteration assertに診断messageだけを追加しました。  
条件式、集約、件数検査、並行度、productionはすべて維持しています。  
焦点集合3ファイルは全件実走し、287件すべて緑です。  
作業ツリーの変更は指定テスト1本だけです。