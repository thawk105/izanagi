## 実装した内容

変更前は site を参照せず、常に `linux-baremetal` 契約と `ENV_TAG` / `CLK` / `NUMA` を使用していました。変更後の計測受理集合は `{OTHER, PEGASUS_COMPUTE}` の exact set で、login・suspect・未知 site は `ExecutionGuardError` になります。

- [p3_s4_loop.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:62)
  - `execution_guard` / `site_policy`、site→env 対応、admission、cfg 射影を移植。
  - 対応元: [p3_s4_loop_trigger_gating.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop_trigger_gating.py:57)、[:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop_trigger_gating.py:103)、[:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop_trigger_gating.py:444)。
  - `default_cfg` は未束縛で返すよう変更。既存 OTHER golden ID は維持。
  - [内部 resolved 実装:1412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1412)、[公開入口:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1557)、[drive pair 注入:1871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1871)へ分割。対応元は移植元 `:734-907`、`:984-1031`。
  - [run_campaign 呼出し:1524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1524)を契約由来の tag・clock・numactl・authorization へ変更し、compute だけ `env_contract` と非空 `dependency_prefix` を転送。対応元は移植元 `:802-819`。
  - reject 3 経路すべてへ `env_tag=contract.env_tag` を指定。
  - [main:2088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:2088)は authority gate 後に一度だけ site を解決し、planner-context と実行経路へ射影。

- [p3_b4_wiring_probe.py:1464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_wiring_probe.py:1464)
  - 未束縛になった `default_cfg` の consumer 側で linux 契約を解決・bindしてから contract hash を読むよう修正。

- [test_p3_s4_loop.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:84)
  - C11 M1〜M13、公開 API 制約、reject 3 sink の contract tag を検査。
  - [自動 compute 正例:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:181)は `_current_site`→`_admit_env_contract`→`_campaign_cfg_for_site` の実体を通し、実際に `run_campaign` が受けた cfg、contract object 同一性、marker、全実測引数を同時検査。
  - `drive_iteration` の既存 mock は resolved 内部 seam へ追随。期待値は緩和していません。

- [test_p3_b4_raw_record_producer.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_raw_record_producer.py:149)
  - lock writer が未束縛 cfg を受けた場合だけ契約を解決・bindしてから hash を読むよう修正。

## 変異 M1〜M13 の対応表

| 変異 | 殺すテスト | 単一の赤理由 |
|---|---|---|
| M1 | `test_base_site_admission_is_exact_two_site_set` | exact set に login・suspect・未知値が混入する。 |
| M2 | `test_base_site_admission_is_exact_two_site_set` | exact set から OTHER だけが欠落する。 |
| M3 | `test_base_campaign_projection_preserves_other_golden_and_splits_compute` | compute と OTHER の campaign identity が同一になる。 |
| M4 | 同上 | OTHER に `measurement_env` が付与される最初の検査だけが赤になる。 |
| M5 | `test_base_automatic_compute_resolution_flows_one_projected_cfg_to_campaign` | sink の `env_tag` 一項目だけが sentinel contract と不一致。 |
| M6 | 同上 | sink の `clocks_per_us` 一項目だけが不一致。 |
| M7 | 同上 | sink の `numactl` 一項目だけが不一致。 |
| M8 | 同上 | authorization 呼出し tag だけが contract tag と不一致。 |
| M9 | `test_base_campaign_projection_preserves_other_golden_and_splits_compute` | `default_cfg.bound_environment_contract is None` の検査だけが最初に赤になる。 |
| M10 | `test_base_drive_iteration_rejects_one_sided_site_contract_injection` | downstream site mappingを正例化してあり、pair TypeError のみが拒否層。 |
| M11 | `test_base_drive_iteration_rejects_injected_unadmitted_site_only_at_site_gate` | downstream tag mappingを用意済みで、site admission のみが拒否層。 |
| M12 | `test_base_drive_iteration_rejects_only_injected_contract_tag_mismatch` | OTHER は受理済みなので、contract tag 照合のみが拒否層。 |
| M13 | `test_base_automatic_compute_resolution_flows_one_projected_cfg_to_campaign` | compute sink の `env_contract is contract` 一項目だけが欠落する。 |

## 実走結果

実装済み・pytest 未実走です。

`python3 tools/run_tests.py` で新設 8 nodeid を要求しましたが、`qstat -Q preflight rc=1`、`child_started=false`、rc=16 となりテスト本体は開始されませんでした。runner が生成した `output/pegasus-dispatch/...` の一時ファイルとディレクトリは除去済みです。

代わりに以下は成功しています。

- 編集 4 ファイルの AST parse
- `git diff --check`
- OTHER の既存 golden ID 2件、compute identity 分離、公開 signature の pure smoke
- 自動 compute 解決から `run_campaign` までの behavioral smoke
- M10〜M12 注入境界の behavioral smoke

## 所有外への波及

grepで確認した未編集 consumerです。

- [conftest.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/conftest.py:239): autouse fixture が通常テストの自動解決を OTHER に固定。
- [p3_b4_launcher.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:141)、[:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_b4_launcher.py:152): base `main` / `default_cfg` consumer。compute の base site 射影漏れは C10-1 の scope 外として残存。
- [materializer_admission.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/materializer_admission.py:122): `main` の登録 consumer。
- [test_p3_b4_launcher.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_launcher.py:45): base cfg/main の launcher tests。
- [test_p3_b4_closed_critic.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:331)、[:2918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_closed_critic.py:2918): cfg/drive consumer。`:2918` は公開 `run_one_iteration` を mockしていますが、drive は裁定どおり内部 resolved seam を呼ぶため、段 6 全走で要確認です。
- [test_p3_b4_wiring_probe.py:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_b4_wiring_probe.py:330): producer inventoryと default cfg identity consumer。
- [test_p3_exploration_namespace.py:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_exploration_namespace.py:416)、[:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_exploration_namespace.py:665): main authority・routing・AST cardinality consumer。静的再計数は layout 10、run_campaign 1で既存期待どおり。
- 新規 test 名の exact 登録 meta-test は見つかりませんでした。[test_acceptance_schedule_order.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_acceptance_schedule_order.py:705)は ledger coverage 90%以上のみを要求します。

## 総括

plan v2 の site-aware 配線を移植し、受理集合を無条件から `{OTHER, PEGASUS_COMPUTE}` へ縮小しました。  
OTHER の既存 golden identity は維持し、compute のみ marker付き別 identityになります。  
C11 M1〜M13 は各拒否・転送面を単独原因として検査する形で追加済みです。  
commit、docs、移植元、launcher、output成果物には変更を残していません。  
親の段 6 では全走、とくに `test_p3_b4_closed_critic.py` の旧 mock seamを必ず確認してください。