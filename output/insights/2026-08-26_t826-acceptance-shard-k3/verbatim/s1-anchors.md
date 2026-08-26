# 段 1 実アンカー表 (親が実測で確定した位置。分類文は置かない)

## 変更面の候補 (production)

| path:line | 実体 |
|---|---|
| `orchestrator/tests/conftest.py:464` | `class RealRepoAccess` |
| `orchestrator/tests/conftest.py:576` | `_build_real_repo_access_map()` |
| `orchestrator/tests/conftest.py:623-631` | `REAL_REPO_ACCESS_BY_NODE` / `REAL_REPO_RESOURCE_NODES` / `REAL_REPO_CCBENCH_WRITER_NODES` |
| `orchestrator/tests/conftest.py:632-639` | `REAL_REPO_PROCESS_MEMO_NODES` (4 node) |
| `orchestrator/tests/conftest.py:762` | `_real_repo_node_id(item)` |
| `orchestrator/tests/conftest.py:981-986` | `_REAL_REPO_LOCK_DIRECTORY = Path("/tmp")` / `_REAL_REPO_LOCK_TIMEOUT_S = 245.0` / `_REAL_REPO_LOCK_RESOURCES` |
| `orchestrator/tests/conftest.py:989` | `_real_repo_lock_path(resource, *, repo_root)` |
| `orchestrator/tests/conftest.py:1065` | `_real_repo_file_lock(...)` (`LOCK_SH` / `LOCK_EX`) |
| `orchestrator/tests/conftest.py:1116` | `_real_repo_locks(access)` |
| `orchestrator/tests/conftest.py:1702` | `_strip_real_repo_loadgroup_suffix(item)` |
| `orchestrator/tests/conftest.py:1742-1758` | `pytest_collection_modifyitems`、1756-1757 が `xdist_group("real-repo")` を付与 |
| `orchestrator/tests/conftest.py:1827-1843` | `pytest_runtest_protocol`、1841 で lock を保持 |
| `tools/acceptance_shards.py:86` | `class ItemRecord(nodeid, file, group)` |
| `tools/acceptance_shards.py:288-322` | `_components()` の file↔group union-find |
| `tools/acceptance_shards.py:323-330` | `allocate()`、`shard_count not in {2,3}` を `ShardError` |
| `tools/acceptance_shards.py:388` | `assignment_closure_gate()` |
| `tools/acceptance_shards.py:440` | `_scheduler_gate()` (`{"loadgroup"}` 固定) |
| `tools/acceptance_shards.py:679-707` | `_canonical_item()`、687 で `xdist_group` marker を読む |
| `tools/acceptance_shards.py:834` | `_scheduler(config)` |
| `tools/run_tests.py:78` | `_ACCEPTANCE_SHARDS_ENV` |
| `tools/run_tests.py:253-265` | `_acceptance_shard_request()`、`{"1","2","3"}` の閉集合 |
| `tools/run_tests.py:267-` | `_resolve_acceptance_shard_count()` |
| `tools/run_tests.py:376-382` | `_available_cpus()` → `site_policy.available_cpus()` (= 48) |

## consumer (grep による参照関係。名前の推測ではない)

- `acceptance_shards` を参照: `orchestrator/tests/test_dev_wave_wait.py`,
  `orchestrator/tests/test_real_repo_serialization.py`, `orchestrator/tests/test_run_tests_shards.py`,
  `tools/pegasus/run_acceptance_nproc_study.py`, `tools/run_tests.py`
- `IZANAGI_ACCEPTANCE_SHARDS` を参照: `orchestrator/tests/test_acceptance_launcher.py`,
  `tools/pegasus/run_acceptance_nproc_study.py`, `tools/run_tests.py`
- `real-repo` / `REAL_REPO_RESOURCE_NODES` を参照 (test、17 file):
  `orchestrator/tests/README.md`, `conftest.py`, `growth_test_holds.py`,
  `real_repo_ratified_memo.py`, `real_repo_receipt_memo.py`, `test_acceptance_schedule_order.py`,
  `test_check_acceptance_reds.py`, `test_dev_waves_isolation_contract.py`,
  `test_growth_test_holds_contract.py`, `test_hold_inventory.py`,
  `test_real_repo_serialization.py`, `test_s8b_binding_driftguards.py`,
  `test_s8b_floor_campaign.py`, `test_s8b_oracle_driver.py`, `test_s8b_protocol_builder.py`,
  `test_spool_fold.py`, `test_update_acceptance_duration_ledger.py`

## 親が実測した数値 (一次資料つき)

一次資料 = `output/insights/2026-08-26_t1814-shard-time-balance/README.md` (実走 a1k2、
計測 tip `9463bcbc`) と `orchestrator/tests/acceptance_duration_ledger.json` (15,909 node)。

| 値 | 出所 |
|---|---|
| shard-0 pytest wall 307.29 秒 = 鎖 222.68 秒 + 残差 84.61 秒 | 実走 a1k2 |
| shard-0 非鎖 worker 185.71〜191.4 秒、`W_shard0/48 = 187.1` 秒 | 実走 a1k2 |
| 鎖の最長単体 42.77 秒 (`test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment`) | 実走 a1k2 |
| 同 node 94.0 秒 | 台帳 |
| `real-repo` 鎖の直列総和 236.7 秒 / cohort 内訳 parent-read+ccbench-read 209.6 秒 (52 関数)、parent-read のみ 23.5 秒 (28 関数)、ccbench-read のみ 3.6 秒 (6 関数)、write 系 0.0 秒 (4 関数) | 台帳 |
| `real-repo` 連結成分 = 16 file / 2534 node / 2174.1 秒 | 台帳 |
| 最大 shard 仕事量 (台帳): K=2 → 3937.1 秒、K=3 → 2624.7 秒、K=4 以上 → 2174.1 秒で一定 | 台帳 + `_components()` 再実装 |
| 他 group の鎖: `s8c-preregistration-candidate` 156.2 秒 / 5 件、`s8c-predicate-snapshot` 64.3 秒 / 3 件、`dev-waves-runtime` 18.3 秒 / 22 件 | 実走 a1k2 |
