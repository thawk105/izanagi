## 総括

U-A の所有5ファイルを実装しました。commit は作成していません。

- harness 接頭辞を追加し、参照は harness の stock-only に限定。exact 4 flags を既存評価経路へ渡し、identity に反映します。
- trace 保全を cleanup 前に追加。失敗時は原本を残し、元の結果・例外を維持します。
- 追加行数：production **116行**、test/inventory **327行**。
- 構文確認・`git diff --check`・`check_docs.py` は通過。

**試験は実装済み・未実走です。** 以下を `PYTHONPATH=. python3 tools/run_tests.py -n 0 -q` 経由で試みましたが、すべて `qstat -Q preflight rc=1`、runner rc=16、child未起動でした。

1. 新規2試験ファイル全件
2. certified-writer caller inventory、B4 wiring、spawn inventory、official perf closure
3. `test_p3_s4_loop.py -k 'b5 or stock_control or machine'`

所有外への波及は、既存 B-5 CLI caller、共有 fixture の `test_p3_s4_loop.py`／`test_campaign.py`、上記 inventory／closure consumer です。編集していません。評価 callsite・既存 import 閉包を増やす変更もありません。

所有外の必要変更：`check_codex_agents.py` は coder役割本文の SHA drift で停止しました（`orchestrator/codex_roles/spec.py:588`）。裁定で U-C に割り当てられた pin 更新が必要です。

変異の対応は以下です。**変異投入・FAIL確認は未実走**であり、kill は未確定です。nodeid の file は `orchestrator/tests/` 配下です。

| 変異 | 対象関数 | 対応 test nodeid |
|---|---|---|
| M1 | `main` | `test_t2849_loop_entry.py::test_harness_machine_slot_accepted` |
| M2 | `_run_stock_control_resolved` | `test_t2849_loop_entry.py::test_read_heavy_reference_exact_flags` |
| M3 | `main` | `test_t2849_loop_entry.py::test_reference_rejected_outside_harness` |
| M4 | `_run_one_repetition` | `test_t2853_trace_preservation.py::test_archive_before_cleanup` |
| M5 | `_run_one_repetition` | `test_t2853_trace_preservation.py::test_failure_retains_original` |
| M6 | `_run_one_repetition` | `test_t2853_trace_preservation.py::test_preservation_error_does_not_replace_result` |
| M7 | `_run_one_repetition` | `test_t2853_trace_preservation.py::test_unset_env_unchanged` |