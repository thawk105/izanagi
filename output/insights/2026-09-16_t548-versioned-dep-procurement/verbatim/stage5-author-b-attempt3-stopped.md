## 総括

**追補 4 の修正は完了しましたが、wave 全体は未完了です。** 所有外の evidence 契約テストに新たな赤が出たため、禁止に従って変更せず停止しました。commit はしていません。

今回変更したのは `test_mocc_trace_job_contract.py` のみです。parser を実行して **16 値・compiler JSON は添字 10・policy SHA は添字 15** と実測し、全 assert を保持して修正しました。関数名は許可された 1 件だけ改名。**削除した test 関数は 0 件**です。

**実走結果**

以下は `orchestrator/tests/` 配下、各 file の全 node が対象です。

| file | 結果 | rc |
|---|---:|---:|
| `test_mocc_trace_job_contract.py` | 145 passed | 0 |
| `test_pegasus_tools.py` | 69 passed | 0 |
| `test_p3_s4_loop_job_contract.py` | 82 passed | 0 |
| `test_paper_story_a1_job_contract.py` | 171 passed | 0 |
| `test_backoff_extended_sweep.py` | 49 passed | 0 |
| `test_ccbench_spawn_sites.py` | 47 passed | 0 |
| `test_plain_runner_coverage.py` | 3 passed | 0 |
| `test_b4_binary_record.py` | 21 passed | 0 |
| `test_pegasus_thirdparty_fetch.py` | 102 passed | 0 |
| `test_pegasus_floor_tools.py` | 全走失敗 | 1 |
| `test_silo_ladder_rung1_evidence.py` | 1 passed / 1 failed | 1 |
| `test_t126_pegasus_tools.py` | 276 件中、145 成功表示後に中断 | 130 |

MOCC は既存 harness に `PYTEST_ADDOPTS` で追加し、Pegasus tools と合計 214 件を実走しました。

T-126 は collection 順との照合上、先頭の `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` から `test_submit_rejects_each_single_layer_equal_float_type_drift[prologue-cap]` までです。[対応 nodeid 一覧](/tmp/t548-final-t126-completed-nodeids.txt)。残り 131 件は完了未確認で、`[canonical]` の今回の実走成功も申告しません。

**期待赤との突き合わせ・停止理由**

MOCC の本数 pin、台帳の 3 node は解消しました。一方、次は想定外の赤です。

- `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`：凍結 evidence の `pbs_job` SHA `318c2b12…` と変更後 shell の `117b3bb4…` が不一致。[失敗箇所](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-b-shell/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1277)。**所有外テストと過去 evidence は変更していません。**
- floor 全走：`test_floor_time_resolver_bound_counts_matches_not_lifetime_history` が失敗。fork 子のログには `test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` の失敗もあります。該当 4 ケースの選択再走は rc=0・4 passed でしたが、全走失敗は未解消として残します。[全走ログ](/tmp/t548-final-pegasus_floor_tools.log)。

**15 job body の解決変数**

全件 `THIRDPARTY_SOURCE_ROOT` 配下の `gflags` / `glog` を使います。

| file | root の入力／既定基準 | source 変数 |
|---|---|---|
| `a5_second_boot_backoff_sweep.sh` | 共通 env／`REPO_BASE` | `GFLAGS_SOURCE`, `GLOG_SOURCE` |
| `b10_backoff_grid.sh` | 共通 env／`REPO_ROOT` | 同上 |
| `certify_calibration.sh` | 共通 env／`REPO_ROOT` | `GFLAGS_SOURCE_PATH`, `GLOG_SOURCE_PATH` |
| `floor_campaign.sh` | 同上 | 同上 |
| `floor_scoping.sh` | 同上 | 同上 |
| `mocc_trace_pilot.sh` | 同上 | 同上 |
| `oracle_n_pilot.sh` | 同上 | 同上 |
| `p3_s4_loop_pegasus.sh` | `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` | 同上 |
| `paper_story_a1_paired.sh` | 共通 env／`REPO_ROOT` | 同上 |
| `silo_ladder_rung1.sh` | 共通 env／`REPO_ROOT` | `GFLAGS_SOURCE`, `GLOG_SOURCE` |
| `t126_qualification.sh` | 同上 | 同上 |
| `t141_region_profile.sh` | 共通 env／`IZANAGI_ROOT` | `GFLAGS_SOURCE_PATH`, `GLOG_SOURCE_PATH` |
| `probes/t1683_rr5_cost_probe.pbs` | 共通 env／`REPO_ROOT` | 同上 |
| `probes/t2187_adaptive_const_probe.pbs` | 同上 | 同上 |
| `probes/t2228_driver_gate_liveness_probe.pbs` | 同上 | 同上 |

共通 env は既存の `IZANAGI_THIRDPARTY_SOURCE_ROOT` です。

**既存差分の確認**

- T-126：`_attempt`／`_submit_fixture` の依存 repo を staging 配下へ移し、HEAD 監視 marker の対象も移動。`[canonical]` の exact stderr assert は新しい `repo-case/.../thirdparty-src/gflags` を要求します。assert の削除・緩和はありません。HEAD・dirty・不在の拒否処理も保持しています。
- 台帳：既存差分の **呼出し 1 本・sink 118 行（両箇所）**を AST と現物で確認しました。owner・説明・exact 比較は不変です。
- 変更前は policy の絶対 locator を受理。変更後は staging 配下のみを使い、旧 locator への fallback はありません。pin・dirty・存在検査、build/install、prefix 供給は保持しています。

所有外への波及として、Python consumer 5 本、T-126 共有 fixture、B4 起動台帳、MOCC 本数 pin、silo の凍結 evidence binding、関連 submitter／consumer 契約を確認しました。旧 locator の live consumer は検索で残っていません。add-only 台帳の旧 nodeid と `verify-deps` 廃止の負例は保持しています。

`test_silo_ladder_rung1_driver.py`、`test_hooks.py`、その他未列挙 suite は今回未実走です。実 job・計算ノード・実 build は **実装済み・未実走**で、closed とは申告しません。未解決事項は所有外の evidence 契約と floor の全走失敗です。