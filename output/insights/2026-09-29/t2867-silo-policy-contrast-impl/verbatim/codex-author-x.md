## 総括

所有 path に、対照用 cfg、機械 proposal と初期点、slot 計測、台帳単位の実行入口、job body の `contrast` mode を追加しました。**実走による確認は未完了**です。台帳 module はこの tree に未着地で、テスト runner も qstat の事前確認に失敗しました。

## 変更 file と行数

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py): +399/−20
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_policy.py): +56
- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/tools/pegasus/p3_s4_loop_pegasus.sh): +14/−3
- [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_job_contract.py): +23/−1
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_campaign.py): caller inventory を 2→3 に更新

## 実装した interface

`default_cfg(..., contrast=None)`、`contrast_cfg(header, *, campaign_env, slot=None, index=None, attempt=0)`、`measure_slot(...)`、`run_contrast_unit(...)` を追加しました。CLI は `--contrast-ledger ROOT` と `--contrast-run-unit UNIT.json`、job body は `IZANAGI_S4_POLICY_MODE=contrast` を受けます。単位実行では `slot-start`、`slot-result` を追記します。

## テスト

`py_compile` と `git diff --check` は通過しました。`python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_policy.py` は **rc=16、qstat 事前確認失敗**で、テストは開始されていません。追加した `test_contrast_cfg_keeps_default_identity_and_separates_attempts`、`test_contrast_initial_points_and_machine_arm_provenance`、`test_machine_origin_can_write_only_after_shared_gate`、`test_policy_actual_job_argv_archive_and_lock[contrast]`、`test_policy_contrast_requires_exclusive_absolute_unit` は未実走です。

## 所有外への波及

`run_campaign` の caller 数が増えるため、所有内の `test_campaign.py` inventory を更新しました。`test_p3_exploration_namespace.py`、`test_p3_b4_wiring_probe.py`、`test_pegasus_tools.py`、`test_pegasus_policy_registry.py` への参照を静的に確認し、所有外 file は編集していません。

## 変異の位置

- M1: `p3_s4_loop_policy.py:103` → `test_contrast_initial_points_and_machine_arm_provenance`
- M2・M3: 同 file `:178`、`:613` → `test_contrast_cfg_keeps_default_identity_and_separates_attempts`
- M4: 同 file `:260` → `test_machine_origin_can_write_only_after_shared_gate`
- M5: 同 file `:769`。台帳実体を使う検出 test は未追加です。
- M6: `p3_s4_loop_pegasus.sh:253` → `test_policy_contrast_requires_exclusive_absolute_unit`

## 未解決・報告して止めたこと

台帳 module `silo_policy_contrast.py` が未着地のため、`next_unit` との結合、M5 の test、score の `endpoint-fixed` field、ref-fixed10 の実測経路は未確認です。親で統合後に該当テストと計測経路を確認してください。