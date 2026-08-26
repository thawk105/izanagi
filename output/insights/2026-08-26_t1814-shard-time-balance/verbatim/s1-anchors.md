# 実アンカー表 — [T-1814]

repo = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1814-shard-time-balance`
(base main `9463bcbcb1541625db59abb97cf6a76934b4c80c`)

| 位置 | 内容 |
|---|---|
| `tools/acceptance_shards.py:288` | `_components()`。`"weight": len(nodeids)` を返す唯一の場所 |
| `tools/acceptance_shards.py:323` | `allocate(records, shard_count)`。group 優先 + 残り LPT の bin-packing |
| `tools/acceptance_shards.py:344-346` | `grouped` / `remaining` の分離と `group_names` |
| `tools/acceptance_shards.py:349-360` | `shard_count >= len(group_names)` の group 1 対 1 割付枝 |
| `tools/acceptance_shards.py:361-372` | else 枝。`-weight` 降順 + 最小 load への LPT |
| `tools/acceptance_shards.py:374-379` | `remaining` の LPT |
| `tools/acceptance_shards.py:388` | `assignment_closure_gate()`。allocator と独立の閉包再検査 |
| `tools/acceptance_shards.py:455` | `validate_report_evidence()` |
| `tools/acceptance_shards.py:763` | `pytest_collection_modifyitems()`。`allocate()` の呼び手 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 所要台帳。2,030,196 bytes、15,909 nodeid、document schema は `schema_version: 1` / `unit: seconds` (`izanagi_acceptance_duration_ledger_v1` は文書 schema ではなく `workerinput` の key。`orchestrator/tests/conftest.py:763-765`) |
| `orchestrator/tests/conftest.py:783` | `_validate_acceptance_duration_ledger_document()` |
| `orchestrator/tests/conftest.py:823` | `_load_acceptance_duration_ledger()`。不在・破損は `{}` |
| `orchestrator/tests/conftest.py:885` | `_configure_acceptance_duration_ledger()`。controller が 1 度読み `workerinput` で配る |
| `orchestrator/tests/conftest.py:1848` | 上記の呼び出し (`pytest_configure`) |
| `orchestrator/tests/conftest.py:338` | `REAL_REPO_SERIAL_NODES` (73 件)。排他鎖の正本 |
| `orchestrator/tests/conftest.py:1333` | `item.add_marker(pytest.mark.xdist_group("real-repo"))` |
| `tools/update_acceptance_duration_ledger.py` | 台帳生成器 (本 wave では走らせない) |
| `tools/run_tests.py:253-297` | `_acceptance_shard_request()` / `_resolve_acceptance_shard_count()`。`IZANAGI_ACCEPTANCE_SHARDS=1` が K=1 opt-out。**本 wave は編集しない** |
| `orchestrator/tests/test_run_tests_shards.py` | shard の consumer test |
| `orchestrator/tests/test_acceptance_schedule_order.py` | 台帳と投入順の consumer test |
| `orchestrator/tests/test_update_acceptance_duration_ledger.py:307` | 現物台帳の schema 検査 |
| `orchestrator/tests/test_update_acceptance_duration_ledger.py:328` | 台帳 node 差分の exact 検査 (再生成すると赤) |
| `orchestrator/tests/test_real_repo_serialization.py:1103` | group marker と real-repo node 集合の独立 golden |

## 一次資料 (repo 外)

| 位置 | 内容 |
|---|---|
| `/work/1/SFC/tanab/.izanagi-acceptance-shards/e6887cb4d4059ee0ec0dbb6aea880485/shard-{0,1}/report.json` | `selected` (各 7450)、`observed_universe` (14900 records)、`worker_occupancy` (48 worker の `duration_s` と `items`)、`group_to_workers` |
| 同 `shard-{0,1}/junit.xml` | 全 testcase の time |
| 同 `shard-{0,1}/dispatcher.log` | PBS の Created / Started / Ended と Elapse |
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1580-shard-default-pegasus/acceptance2-receipt.json` | `tested_tip 4b40d17f`、`verdict child-green` (K は載らない — D724 既知) |
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1814-shard-time-balance/probe_alloc.py` | 親のオフライン再現 probe (repo へ入れない) |

## 実測値 (参照走 K=2、tested_tip `4b40d17f`)

| 層 | shard-0 | shard-1 |
|---|---|---|
| queue 待ち | 10 秒 (00:01:27→00:01:37) | 8 秒 (00:01:29→00:01:37) |
| job Elapse | 279 秒 | 182 秒 |
| pytest wall | 267.21 秒 | 171.50 秒 |
| 選択 node 数 | 7450 | 7450 |
| junit 直列総和 | 4215.5 秒 | 3257.0 秒 |
| 最遅 worker | gw0 210.5 秒 / 72 件 (`real-repo`) | gw7 132.0 秒 / 68 件 |
| group の所在 | `real-repo` | `dev-waves-runtime` (64.3 秒 / 56 件)、`s8c-preregistration-candidate` (85.8 秒 / 6 件) |
| 固定費 (wall − 最遅 worker) | 56.4 秒 | 39.2 秒 |

外側 wall は親 log にレイヤ分解が残っていない (`acceptance2.log` は collected と結果のみ)。
本 wave の実測ではここも記録する。

## 本 wave の実測 (計測 tip `9463bcbc`、clean tree、同一 tip で交互 4 走)

**a3k1 と a4k2 は本文書作成時点で未完了。** 完了後に追記する。

| arm | K | queue 待ち | job Elapse | pytest wall | 外側 wall | 収集 |
|---|---|---|---|---|---|---|
| a1k2 | 2 | 8 秒 (両 shard) | 318 / 226 秒 | **307.29 / 215.15 秒** | 339.09 秒 | 8580 + 8580 |
| a2k1 | 1 | 249 秒 | 270 秒 | **261.45 秒** | 535.18 秒 | 17160 |

**K=1 が K=2 より pytest wall で 45.84 秒速い。親の事前予測は反証された。**

### a1k2 の shard 内訳

| | shard-0 | shard-1 |
|---|---|---|
| 選択 node 数 | 8580 | 8580 |
| 直列総和 (worker occupancy 合計) | 8981.5 秒 | 5880.5 秒 |
| 最遅 worker | gw0 222.68 秒 / 76 件 (`real-repo`) | gw1 156.17 秒 / 6 件 |
| 2 番目 | gw7 191.4 秒 / 48 件 | gw3 154.9 秒 / 2 件 |
| 中央値 worker | 186.0 秒 | 121.0 秒 |
| 最速 worker | 185.71 秒 | 120.93 秒 |
| 固定費 (wall − 最遅 worker) | 84.61 秒 | 58.98 秒 |
| group | `real-repo` → gw0 | `dev-waves-runtime` → gw0、`s8c-predicate-snapshot` → gw2 |

- 要素数は 8580/8580 で完全に均等だが、仕事量は **3101 秒 (34%) 偏っている**
  (参照走 `4b40d17f` の 958.5 秒 = 12.8% より拡大)。
- shard-0 は gw0 以外の 47 worker が 185.7〜191.4 秒に密集しており、gw0 だけが 222.68 秒。
- 総仕事量 14862 秒。K=2 の完全均衡なら 1 worker 154.8 秒。鎖 222.68 秒 > 154.8 秒。
- K=1 の wall 261.45 秒から逆算した仕事量は約 9000 秒であり、K=2 の 14862 秒より小さい。
  **分割は worker を 48 本から 96 本へ増やし、worker ごとの準備費を倍払わせる。**
- 一次資料: `/work/1/SFC/tanab/.izanagi-acceptance-shards/e4a77eb86b3e8ad9c4855255307be11c/`
  と `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1814-shard-time-balance/arm-*.log`、
  `arm-*.meta`、抽出器は同 dir の `extract_layers.py`。
- `worker_occupancy` の `duration_s` は `report.duration` (setup+call+teardown) の合計であり、
  worker ごとの collection と起動は含まない (`tools/acceptance_shards.py:799-811`)。
  「固定費」はその差分である。
