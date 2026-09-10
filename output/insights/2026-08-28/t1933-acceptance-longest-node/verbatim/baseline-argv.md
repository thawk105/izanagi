# 変更前後の固定 argv

checkout: `61b92342beb259363eb5ed094ac200dd39a7a1f5`

```text
python3 tools/run_tests.py --force-dispatch -n 0 --durations=0 -q -rf
orchestrator/tests/test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes
```

上の改行は表示用で、実 argv はこの順の単一 command とする。after も node 順、wrapper/pytest option、計算ノード強制を一字一句同じにする。

## baseline結果

- request: `954274.nqsv`、Pegasus計算ノード、dispatch receipt outcome=`child`, rc=0。
- pytest: 4 passed / 147.55秒、effective scheduler=`serial`。
- node順のduration: floor snapshot 4.18秒、t080 single-defect 86.57秒、t080 draft-finalize 51.93秒、t080 snapshot 2.61秒。
- ledgerの79/50秒snapshot値はこの現行checkout・固定argvでは再現せず、4 node内の最長はt080 single-defectだった。
