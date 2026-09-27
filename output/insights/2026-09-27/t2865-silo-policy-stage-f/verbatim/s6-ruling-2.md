# 段 6 裁定 2 — 焦点走 1 回目の赤 (2026-09-27)

焦点走 1 回目 (wave `6b4100077`、計算ノード request 31353.nqsv、Elapse 87 秒): 2,187 passed / 32 failed / 10 skipped。log = job dir `focus-1.log`。赤はすべて本 wave の差分に帰属する (非帰属 0)。

| 型 | 件数 | 失敗 test | 原因 (失敗本文から) | 採否 |
|---|---|---|---|---|
| R1 | 1 | `test_p3_s4_loop_job_contract.py::test_interpreter_resolver_hides_an_old_bare_python3` | job body の `resolve_python` が `policy_mode` を裸で参照し、resolver の snippet だけを `set -u` で走らせる既存 test で `policy_mode: unbound variable` | real、fix-2b |
| R2 | 23 | `test_p3_s4_loop_job_contract.py::test_b5_*` (22)・`test_t2849_job_contract.py::test_harness_bench_lock` (1) | 単位 B が共有の偽 driver に `IZANAGI_TRACE_ARCHIVE_ROOT` の記録を足し、既存 test が照合する driver 環境 dict に `'IZANAGI_TRACE_ARCHIVE_ROOT': None` が増えた (既存期待値の実質的な変更) | real、fix-2b |
| R3 | 5 | `test_p3_s4_loop_job_contract.py::test_policy_archive_root_*` | 単位 B の新 test 自体が赤 (本文は job dir の `focus-1.log`) | real、fix-2b |
| R4 | 3 | `test_ccbench_spawn_sites.py::test_define_sink_cross_product_*` | 方策 driver の `run_campaign` 呼出しを新関数 `_run_measurement` へ移したため、`SILO_POLICY_VARIANT` に到達しうる build 入口が gate に支配されない未登録 sink になった (`('SILO_POLICY_VARIANT', _BuildSink('orchestrator/campaign/p3_s4_loop_policy.py', '<module>._run_measurement', 336, 'campaign'), 'reachable')`) | real、fix-2a |

fix の分割 (所有 path が素集合):
- **fix-2a (単位 A の worktree):** `orchestrator/campaign/p3_s4_loop_policy.py`・`orchestrator/tests/test_p3_s4_loop_policy.py`。R4 を、既存の define sink 検査 (T-2155) を緩めず、`test_ccbench_spawn_sites.py` を編集せずに閉じる。base (`ad114fba0`) で方策 driver の sink がどう扱われていたか (検査が緑だった理由) を実測してから、同じ形に戻す。
- **fix-2b (単位 B の worktree):** `tools/pegasus/p3_s4_loop_pegasus.sh`・`orchestrator/tests/test_p3_s4_loop_job_contract.py`。R1 は job body の参照を未定義でも安全な形にする。R2 は共有の偽 driver が既存 test に返す環境 dict を base と同一に戻し、保全 root の到達は方策 test だけが別に観測する。R3 は新 test を直す (job body の保全 root 検査が誤りなら job body を直す)。
- `test_t2849_job_contract.py` と `test_ccbench_spawn_sites.py` は編集しない (既存期待値を変えない)。
