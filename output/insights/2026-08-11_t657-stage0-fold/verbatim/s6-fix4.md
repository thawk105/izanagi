指定の陰性 node を [test_calibration_freeze_authority_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:1118) に追加しました。変更はこのファイルのみで、`git add` / `git commit` は未実施です。

境界 marker 後方の `pending` 完了条件だけを反転しています。抽出後に predicates と control が canonical、execution boundary が replacement と一致することを明示的に assert しています。後段の fixture assignment gate 照合は別の段集合宣言から導出されるため、この変更を拒否するのは第 3 選言だけです。

テスト投入は `qstat -Q` preflight の infrastructure failure（rc=16）で拒否され、実走されませんでした。`git diff --check` は成功しています。

## 総括

追加した nodeid: `orchestrator/tests/test_calibration_freeze_authority_contract.py::test_design_stage6_execution_boundary_tail_drift_is_rejected`
その node が第 3 選言だけで落ちる根拠: predicates と `stage6_control` が期待値どおりであることを assert し、marker 後方だけを書き換えた `stage6_execution_boundary` のみ replacement と一致させている
走らせた nodeid と結果: 未実走（ファイル全体を `tools/run_tests.py --force-dispatch` へ投入したが、`qstat -Q` preflight failure、rc=16）