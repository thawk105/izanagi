## 総括

R9・R10 を指定の 2 ファイルで修正しました。焦点テストは未実走です。

## 変更内容 (file:line)

- [p3_s4_loop_policy.py:659](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix2/orchestrator/campaign/p3_s4_loop_policy.py:659): pair 分岐の計測 layout を既存の `_campaign_layout(measurement_cfg)` で作るよう変更しました。
- [test_p3_s4_loop_policy.py:793](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix2/orchestrator/tests/test_p3_s4_loop_policy.py:793): 子 process の `PYTHONPATH` に repo root と `orchestrator/tests` を入れ、既存値を後ろに残しました。

## 実走した検査と結果 (未実走はそう書く)

2 ファイルの `py_compile` は成功しました。pytest と `tools/run_tests.py` は未実走です。

## 所有外への波及 (静的列挙)

`test_p3_exploration_namespace.py` が数える layout 呼出し箇所は、追加された 1 箇所を helper 呼出しに戻したため、期待値の 2 箇所になります。子 process では `test_campaign.py` からの `skiputil` import が解決可能になります。所有外ファイルは編集していません。

## 未解決・判断が要る点

焦点走による T1〜T3 と namespace inventory の結果は未確認です。