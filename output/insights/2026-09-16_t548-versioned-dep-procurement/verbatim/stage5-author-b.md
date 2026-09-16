## 総括

追補 5 の実装を完了しました。今回編集したのは [test_silo_ladder_rung1_evidence.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-b-shell/orchestrator/tests/test_silo_ladder_rung1_evidence.py:83) のみです。

- 親指定の歴史 SHA・現行 SHA を定数化。
- `pbs_job` を歴史 binding に移し、現行 bytes の完全一致検査を追加。
- `binding != current` を維持。
- 凍結 evidence の変更、commit、test 関数の削除は **0 件**。

実走はすべて `PYTHONPATH=. python3 orchestrator/tests/<file>.py` の自走 harness です。

| 実走範囲 | 結果 | rc |
|---|---:|---:|
| `test_silo_ladder_rung1_evidence.py` 全 node | 2 passed | 0 |
| `test_plain_runner_coverage.py` 全 node | 3 passed | 0 |
| `test_ccbench_spawn_sites.py` 全 node | 47 passed | 0 |
| `test_growth_test_holds_contract.py` 全 node | 83 passed | 0 |

evidence の実走 nodeid は次の 2 件です。

- `test_silo_ladder_rung1_commit_witness_matches_committed_raw_data`
- `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`

変更前は正当な shell 更新も「凍結 binding と現行 SHA が違う」と拒否していました。変更後は、指定された歴史値・現行値の組だけを受理します。今回の期待赤だった `pbs_job` 不一致は解消し、実走範囲に想定外の赤はありません。

前回差分の静的確認結果は以下です。今回これらは編集していません。

| job body（`tools/pegasus/` 相対） | 解決に使う入力／repo 変数 |
|---|---|
| `a5_second_boot_backoff_sweep.sh` | `IZANAGI_THIRDPARTY_SOURCE_ROOT`／`REPO_BASE` |
| `t141_region_profile.sh` | 同上／`IZANAGI_ROOT` |
| `p3_s4_loop_pegasus.sh` | `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` |
| `b10_backoff_grid.sh`, `certify_calibration.sh`, `floor_campaign.sh`, `floor_scoping.sh`, `mocc_trace_pilot.sh`, `oracle_n_pilot.sh`, `paper_story_a1_paired.sh`, `silo_ladder_rung1.sh`, `t126_qualification.sh` | `IZANAGI_THIRDPARTY_SOURCE_ROOT`／`REPO_ROOT` |
| `probes/t1683_rr5_cost_probe.pbs`, `probes/t2187_adaptive_const_probe.pbs`, `probes/t2228_driver_gate_liveness_probe.pbs` | 同上／`REPO_ROOT` |

全 15 本が `THIRDPARTY_SOURCE_ROOT` 配下を使います。

T-126 は fixture の依存 source と HEAD 監視対象を staging 配下へ移し、`[canonical]` の診断文も新 path の完全一致へ変更済みです。確認した差分に assert 削除はありません。ただし今回は T-126 を再走していません。

spawn 台帳の値は **起動箇所 1、sink 行番号 118（両箇所）**です。現物の起動呼出し・`buildcache.build_v2` の位置を確認し、exact 台帳テストも通りました。

静的に確認した波及先は、凍結 evidence、PBS shell、共有 policy golden、および evidence テストを名指しする growth-hold meta-test です。今回の定数を参照する別 caller は見つかりませんでした。

wave 全体、T-126、floor の再走と実 job・計算ノード・実 build は未実走です。実装済みの範囲と実走済みの範囲を区別し、wave 全体の `closed` は申告しません。floor の既知の赤は親の段 6 判定に残しています。

追加のメモリ内 1 byte 変異検証は、PreToolUse 自動審査が「防護対象 path と不透明構文の併用」を理由に拒否したため未実走です。現行 SHA の完全一致検査による検出力は静的確認に留まります。