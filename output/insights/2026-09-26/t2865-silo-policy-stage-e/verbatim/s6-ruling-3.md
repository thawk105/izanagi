# 段 6 裁定 3 巡目 — [T-2865] (2026-09-26、親)

入力: 焦点走 3 (`focus-3.log`、tree = `cc5d8375e` + 未 commit の runbook 編集、4410 passed / 2 failed / 12 skipped)。

| ID | 赤 | 判定 | 処置 |
|---|---|---|---|
| H1 | `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact` — `unreviewed: orchestrator/campaign/p3_s4_loop_policy.py` | real (consumer 取り残し) | `_REVIEWED_PERF_FILES` に新 driver を注記つきで追加登録する (`p3_s4_loop.py` の注記と同型: certified campaign pipeline を呼び preflight 後に perf を起動しうる、perf という名前は較正済み PerfConfig の動作点であって profiler ではない)。driver の識別子を改名して検出を避けることはしない |
| H2 | `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` — `docs/phase3-silo-policy-runbook.md` | 非帰属 (親の操作) | 焦点走の待機中に親が runbook を未 commit で編集し、走行時点の作業ツリーが dirty だった。runbook は `2ee50cc9f` で commit 済み。次の焦点走で再確認する |
