## 総括

15 本の job body を staging root 経由へ付け替えました。ただし、**所有外テストの契約不整合を発見したため、未完了として停止します。closed ではありません。**

停止対象は [test_mocc_trace_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-b-shell/orchestrator/tests/test_mocc_trace_job_contract.py:238) の `test_mocc_trace_policy_parser_emits_18_values_and_rejects_duplicates` です。旧 locator 2 個を除いた実装は **16 値**ですが、同テストは **18 値と旧添字 12・17**を要求します。所有外なので変更していません。再開には、このテストの所有追加と契約移行の指示が必要です。

**テスト関数の削除は 0 件。commit・stage・push は行っていません。**

実走結果は次のとおりです。表の範囲は `orchestrator/tests/<file>::*`、各ファイルの全 node です。

| file | 実走範囲 | rc |
|---|---:|---:|
| `test_pegasus_tools.py` | 全 69 node 成功 | 0 |
| `test_pegasus_floor_tools.py` | 全 143 node 成功 | 0 |
| `test_p3_s4_loop_job_contract.py` | 全 82 node 成功 | 0 |
| `test_paper_story_a1_job_contract.py` | 全 171 node 成功 | 0 |
| `test_backoff_extended_sweep.py` | 全 49 node 成功 | 0 |
| `test_a5_second_boot_job_contract.py` | 全 9 node 成功 | 0 |
| `test_b4_binary_record.py` | 全 21 node 成功 | 0 |
| `test_pegasus_thirdparty_fetch.py` | 全 102 node 成功 | 0 |
| `test_plain_runner_coverage.py` | 全 3 node 成功 | 0 |

追加の選択実走：

- `test_t126_pegasus_tools.py::test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value` の `[canonical, walltime, walltime-s, member-cap, round-gap, prologue-cap, attestation-cap, finalize-reserve, wmax]`：**9 node 成功、rc=0**。
- `test_ccbench_spawn_sites.py` の次の **3 node 成功、rc=0**：
  - `test_reviewed_process_launch_inventory_is_recursive_and_exact`
  - `test_define_sink_cross_product_has_no_unreviewed_ungated_member`
  - `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`

全走は T-126 が 276 node 中 144 個、台帳が 47 node 中 13 個の成功表示まで進んだところで中断しました。**双方 rc=130、全走成功には数えません。**

Mocc テストの直接起動は rc=0 でしたが、自走 harness がなく **0 node 実行**です。上記不整合は静的確認であり、実走した赤ではありません。その他の所有外 consumer テスト、実 job 投入・計算ノード走行・実 build は未実走です。

付け替えた一覧です。全行で `THIRDPARTY_SOURCE_ROOT` 配下の `gflags` / `glog` を使います。

| job body（`tools/pegasus/` 配下） | root 解決に使う変数 |
|---|---|
| `a5_second_boot_backoff_sweep.sh` | `IZANAGI_THIRDPARTY_SOURCE_ROOT`／`REPO_BASE` |
| `b10_backoff_grid.sh` | 同上／`REPO_ROOT` |
| `certify_calibration.sh` | 同上／`REPO_ROOT` |
| `floor_campaign.sh` | 同上／`REPO_ROOT` |
| `floor_scoping.sh` | 同上／`REPO_ROOT` |
| `mocc_trace_pilot.sh` | 同上／`REPO_ROOT` |
| `oracle_n_pilot.sh` | 同上／`REPO_ROOT` |
| `paper_story_a1_paired.sh` | 同上／`REPO_ROOT` |
| `silo_ladder_rung1.sh` | 同上／`REPO_ROOT` |
| `t126_qualification.sh` | 同上／`REPO_ROOT` |
| `t141_region_profile.sh` | 同上／`IZANAGI_ROOT` |
| `probes/t1683_rr5_cost_probe.pbs` | 同上／`REPO_ROOT` |
| `probes/t2187_adaptive_const_probe.pbs` | 同上／`REPO_ROOT` |
| `probes/t2228_driver_gate_liveness_probe.pbs` | 同上／`REPO_ROOT` |
| `p3_s4_loop_pegasus.sh` | `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` |

T-126 の fixture 配置と HEAD 監視 marker は、受領した C 差分で既に staging 基準でした。今回は `[canonical]` の stderr 完全一致を、旧 `gflags-case` から `repo-case/<staging-relative>/gflags` へ移しました。marker 必須・reservation 拒否集合・拒否診断は保持し、検出力を削っていません。shell の HEAD・dirty・不在検査も保持しました。

台帳の実測値は **起動箇所 1、sink 行番号 118**です。`rg -n` で `prepare_dependencies` 内の `subprocess.run` と `return buildcache.build_v2` の現物を確認し、行番号を両箇所へ反映しました。owner・説明・exact 比較は変更していません。

受理・拒否の変化は、依存の所在が旧 policy locator から staging 配下へ移ることです。投入時の A/C 展開済み状態では、shell が削除済み key を要求して停止していました。変更後は staging の source を既存の pin・clean 検査へ渡します。旧 locator への fallback はありません。configure 到達は静的契約に加え、floor・A1 の stub 実走でも確認しました。

期待赤との突き合わせでは、Pegasus の旧配列添字、P3・A1 の旧 fixture による赤を修正し、再実走で解消しました。T-126・台帳の指定 node も成功しました。一方、**所有外 Mocc の固定値契約が取りこぼしとして残ります**。最終完走した集合に未解消の赤はありませんが、wave 全体の成功は未確認です。

静的に確認した波及先は、T-126 の identity/submission 共有 fixture、A1・P3 の Git/policy stub、Mocc/G2、calibration、floor receipt・perf closure、Silo driver/evidence、T2187/T2228 probe、hooks と起動箇所台帳です。所有外は編集していません。

`git diff --check` は成功しました。読み取り用 Python と `bash -n` は guard に拒否されたため、それらによる検査成功は申告していません。