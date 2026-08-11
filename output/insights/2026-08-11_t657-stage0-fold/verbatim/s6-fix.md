実装は完了しましたが、指定テストは dispatch 障害で未実走です。したがって I1〜I4 は `closed` と申告しません。

変更対象は指定された 3 ファイルのみです。

- [contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:349): fence scanner、段6実行境界 pin、R4 gate pin を実装。
- [contract tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:844): 削除型 decoy、fence 境界、相反 control、R4 gate 負例を追加。
- [manifest.v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/fixtures/calibration_freeze_authority/manifest.v1.json): gate 13 件、指定 hash、R4 unresolved を反映。

親所有の docs 差分には触れず、`git add` / `git commit` も実行していません。

静的検査結果:

- Python AST: OK
- `git diff --check`: OK
- required gates: count 13、昇順、再計算 hashと指定 literalが一致
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- 指定 runner: rc=16、`qstat -Q preflight rc=1`。pytest node 実行なし

所有外への静的波及可能性:

- `calibration_freeze_authority_execution.py` と対応 consumer test は `load_manifest()` を共有するため、13-gate validation の影響を受けます。ただし execution 側は fixture entries のみを消費し、gate 件数の独自期待値はありません。
- `_extract_stage6_contract` の private 戻り値は3要素から4要素へ変更しました。repo 内 caller は更新済み contract test のみでした。
- 既存 mutation spec/ledger は新規 nodeid を含まないため、親の mutation matrix 再登録・再走対象です。
- `cases/*.json`、ruling profile、execution 層2ファイルは未変更です。

## 総括

- I1: 実装済み・未実走（dispatch infrastructure failure のため closed 未申告）
- I2: 実装済み・未実走（dispatch infrastructure failure のため closed 未申告）
- I3: 実装済み・未実走（dispatch infrastructure failure のため closed 未申告）
- I4: 実装済み・未実走（dispatch infrastructure failure のため closed 未申告）
- 追加 nodeid: `test_r4_cancellation_record_required_gate_removed_is_rejected`, `test_design_revocation_table_only_in_tilde_fence_is_rejected`, `test_design_revocation_table_only_in_long_backtick_fence_is_rejected`, `test_design_stage6_row_only_in_tilde_fence_is_rejected`, `test_design_stage6_row_only_in_long_backtick_fence_is_rejected`, `test_design_long_fence_is_not_closed_by_shorter_marker`, `test_design_fence_is_not_closed_by_different_marker`, `test_design_longer_fence_closer_is_accepted`, `test_design_stage6_contradictory_control_suffix_is_rejected`
- 更新 nodeid: `test_current_repository_is_rejected_as_stage0_incomplete`, `test_adjudicated_ruling_and_gate_projection_is_exact`, `test_design_stage6_structural_contract_matches_validator`, `test_stage0_remains_incomplete_after_r1_r2_r3_projection`
- 走らせた nodeid と結果: 未実走。指定2ファイル範囲を投入したが `qstat -Q` preflight failure、rc=16
- 回帰と判断した赤: なし（pytest 未実走）