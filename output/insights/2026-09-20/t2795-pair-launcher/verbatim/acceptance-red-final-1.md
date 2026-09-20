# 受入 final-1 (tested_main b88b56b6b、tip 906b1c9dd + post-claim merge a03ee4693) の赤 2 件 — assertion 本文 (junit.xml から抽出)

全体: 2 failed / 25874 passed / 69 skipped (3 shard、計算ノード)。赤はどちらも本 wave の差分 (`orchestrator/campaign/p3_s4_loop.py`) に帰属する
repo 全体 inventory pin。

## red 1 — orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed

```text
AssertionError: new/unregistered caller: orchestrator/campaign/p3_s4_loop.py target=campaign.loop.run_campaign expected=1 actual=2 delta=1
callsites=[orchestrator/campaign/p3_s4_loop.py:1986:19 run_campaign -> campaign.loop.run_campaign,
           orchestrator/campaign/p3_s4_loop.py:2165:19 run_campaign -> campaign.loop.run_campaign]
assert (not Counter({('orchestrator/campaign/p3_s4_loop.py', 'campaign.loop.run_campaign'): 1}))
>       assert not new_callers and not stale_inventory, inventory_message
```

`expected_inventory` (test_campaign.py:5388 付近) の `("orchestrator/campaign/p3_s4_loop.py", "campaign.loop.run_campaign"): 1` に対し、現物は 2 箇所
(`_run_stock_control_resolved` の stock 経路 :1986 と候補経路 `_run_one_iteration_resolved` の :2165)。

## red 2 — orchestrator/tests/test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact

```text
AssertionError: unreviewed: orchestrator/campaign/p3_s4_loop.py
assert {'orchestrato...weep.py', ...} == frozenset({'o...eep.py', ...})
  Extra items in the left set:
  'orchestrator/campaign/p3_s4_loop.py'
>       assert actual_perf_files == _REVIEWED_PERF_FILES, _perf_file_drift(actual_perf_files)
```

`_python_has_perf_predicate` は `if` / `IfExp` / `while` の test 式に perf 名 (`_is_perf_name`: `perf` / `use_perf` / `perf_preflight`、`perf_` 先頭、`_perf` 末尾、
`_perf_` 含む) が現れる file を perf file と見る。本 wave の `main` には `if a.verify_performance and not (a.calibrated_perf and a.perf_workload)` /
`if a.calibrated_perf != (a.perf_workload is not None)` / `if a.calibrated_perf:` があり、`calibrated_perf` (末尾 `_perf`) と `perf_workload` (先頭 `perf_`) が当たる。
p3_s4_loop.py は certified pipeline (`run_campaign` → `pipeline.evaluate`) を呼ぶので、`backoff_extended_sweep.py` と同じ理由で「reviewed」に登録する。
