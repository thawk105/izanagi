## 実 runner が正常 rep で出す 7 key の実測

`capture_measure_point()` と `measure_point()` の生成箇所を確認しました。floor-pair の `use_perf=False` 正常 rep は以下です。

- `rep_index`: exact `int`
- `returncode`: exact `int`、値は `0`
- `counter_status`: `str`、値は `"not_required"`
- `missing_perf_events`: `list`、値は `[]`
- `perf_raw`: `dict`、4イベントの値はすべて `None`
- `throughput`: `float`
- `execution_failure`: exact `bool`、値は `False`

## 直した fake の位置 (file:line)

共通7-key helperを [test_floor_pair_driver.py:1448](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1/orchestrator/tests/test_floor_pair_driver.py:1448) に追加し、以下を置換しました。

- `test_mutation_12...`: [test_floor_pair_driver.py:1473](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1/orchestrator/tests/test_floor_pair_driver.py:1473)
- `_complete_scale_point`: [test_floor_pair_driver.py:1685](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1/orchestrator/tests/test_floor_pair_driver.py:1685)
- `_run_production`: [test_floor_pair_driver.py:2347](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1/orchestrator/tests/test_floor_pair_driver.py:2347)

## 追加した window record の固定

[test_floor_pair_driver.py:2374](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix1/orchestrator/tests/test_floor_pair_driver.py:2374) に `test_window_record_persists_exact_runner_observation_schema` を追加しました。

保存された `floor-pair-window/v3` の全 observationについて、7-key集合、各値の型、正常値を exact に検査します。`artifact_sha256` の値は固定していません。

## 実走した nodeid と結果

- 範囲: `orchestrator/tests/test_floor_pair_driver.py` 全211 node
- 追加node: `orchestrator/tests/test_floor_pair_driver.py::test_window_record_persists_exact_runner_observation_schema`
- 結果: `211 passed in 101.78s`
- 実行方式: 指定の直接実走、serial scheduler

## 期待値を緩めずに報告した赤 (無ければ「無し」)

無し。

## 総括

所有ファイル1つだけを変更しました。production、`docs/`、`output/` は変更せず、gitおよびcommitも使用していません。