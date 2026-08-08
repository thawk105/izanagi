実装済み・未実走です。production・docs・commit には触れていません。

変更前は合成契約を receipt に差し替えていたため、`authorize()` が未登録 env を正しく拒否していました。変更後は test fixture 内でのみ、合成 registry・canonical activation record・head pin・calibration 検証を構成し、production の `authorize()` から認可値を取得します。fixture 外では未登録・inactive env の拒否を維持します。

検査順序テストは process seal を一致させ、正常 receipt なら registry/runtime/site/selector の各検査が実際に発火することを確認した後、同じ入力で receipt の serial/state hash 不一致が先に拒否される形へ強化しました。

## 総括

### 1. 赤 15 件の対応表

| # | nodeid | 状態 |
|---:|---|---|
| 1 | `test_campaign.py::test_activation_receipt_check_precedes_registry_runtime_site_and_selector_checks` | partial（実装済み・未実走） |
| 2 | `test_p3_exploration_namespace.py::test_coder_driver_flag_reaches_build_spy_with_exact_run_context[trigger_gating]` | partial（実装済み・未実走） |
| 3 | `test_p3_s4_loop_trigger_gating.py::test_empty_numactl_contract_flows_as_empty_list` | partial（実装済み・未実走） |
| 4 | `test_p3_s4_loop_trigger_gating.py::test_contract_sentinel_flows_to_run_campaign` | partial（実装済み・未実走） |
| 5 | `test_p3_s4_loop_trigger_gating.py::test_fresh_default_seams_flow_distinct_contract_to_measurement_sink` | partial（実装済み・未実走） |
| 6 | `test_s8b_oracle_driver.py::test_required_secondary_calibration_identity_recheck_fires_with_monkeypatched_loader` | partial（実装済み・未実走） |
| 7 | `test_s8b_oracle_driver.py::test_required_verified_calibration_from_other_contract_is_refused_without_side_effects` | partial（実装済み・未実走） |
| 8 | `test_s8b_oracle_driver.py::test_required_oracle_claim_root_outside_durable_approval_is_fail_closed` | partial（実装済み・未実走） |
| 9 | `test_s8b_oracle_driver.py::test_required_existing_claim_refuses_production_entry_without_new_side_effects` | partial（実装済み・未実走） |
| 10 | `test_s8b_oracle_driver.py::test_required_missing_preprovisioned_oracle_claim_root_is_fail_closed` | partial（実装済み・未実走） |
| 11 | `test_s8b_oracle_driver.py::test_required_recheck_real_reservation_shortfall_writes_aborted_terminal` | partial（実装済み・未実走） |
| 12 | `test_s8b_oracle_driver.py::test_required_recheck_real_receipt_validation_catches_midcampaign_drift` | partial（実装済み・未実走） |
| 13 | `test_s8b_oracle_driver.py::test_required_binding_missing_refuses_at_production_entry_without_side_effects` | partial（実装済み・未実走） |
| 14 | `test_s8b_oracle_driver.py::test_required_v1_receipt_refuses_at_production_entry_without_side_effects` | partial（実装済み・未実走） |
| 15 | `test_t126_pegasus_tools.py::test_every_required_identity_path_is_tracked_in_this_repo[...]` | partial（指示どおり未変更、親 commit 待ち） |

`regressed` と判定した項目はありません。ただし pytest 未実走のため `closed` は主張しません。

### 2. 変更ファイルと行数

`git HEAD` 比です。`test_campaign.py` と `test_s8b_oracle_driver.py` は開始時点で先行 fix の差分を含んでいました。

| ファイル | 現在行数 | HEAD 比 |
|---|---:|---:|
| [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/conftest.py:44) | 283 | +58/-1 |
| [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_campaign.py:2263) | 7,562 | +150/-59 |
| [test_p3_exploration_namespace.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_p3_exploration_namespace.py:79) | 424 | +14/-4 |
| [test_p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:354) | 2,229 | +19/-6 |
| [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_oracle_driver.py:1461) | 4,273 | +62/-28 |

### 3. 走らせた検査と結果

- 上表 1〜14 の exact nodeidを `python3 tools/run_tests.py -q -rf ...` で試行
  - rc=16
  - `qstat -Q preflight rc=1`
  - pytest開始前に停止
- 影響4ファイルの `--collect-only` も同じ rc=16で開始前停止
- 対象5ファイルの `compileall`: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

### 4. 未実走・未達

- 対象14 node、影響ファイル全体、受入全走はいずれも未実走です。
- tracked-path の1件は親 commitで閉じる対象のため未変更です。
- production、docs、activation data、commit、provenance監査は変更・実施していません。

### 5. 親への申し送り

キュー復旧後、まず表1〜14の exact nodeidを再実走してください。その後、変更した4 test file全体と `test_env_contract_activation.py`、最後に親 commit後の全走を推奨します。

共有 fixture は synthetic contract を直接認可せず、registry登録・active activation record・head pin・calibration検証を通します。production の未登録 env 拒否、inactive env拒否、side-effectゼロ、fail-closed の期待値は緩めていません。