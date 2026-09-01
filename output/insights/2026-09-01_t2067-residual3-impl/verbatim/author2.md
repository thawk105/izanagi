## 実装した内容

- [s8b_ratified_freeze.py:3558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:3558)
  - `assert_g1_floor_selection_identity(ratified: RatifiedFreeze, root=ROOT) -> None`
  - exact 型検査後、非 g1 は即 return。
  - g1 のみ `_hf._assert_floor_selection_identity(...)` を実行。`validate_selected_certificate` は未指定（既定 `False`）。
  - protocol は generation commit の記録 blobを historical resolver で解決。選択規則に必要な protocol 検証を保ちつつ、現行 contract との一致という追加条件を避けるため。
  - activation HEAD、build policy、closure、binding graph、live scan は不使用。
  - `launch_validate`／`_launch_validate` は呼んでいない。
  - `_verify_generation_semantics` と `reverify_published_freeze` の本体は未変更。

- [s8c_result_judge.py:2067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8c_result_judge.py:2067)
  - `_load_selection_checked_ratified_floor() -> Any`
  - `load_ratified_freeze()` 直後に新 API を呼ぶ共通経路を追加。
  - [verify_floor_bytes:2113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8c_result_judge.py:2113) と [_validate_verified_floor:2180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8c_result_judge.py:2180) を同経路へ変更。
  - `_FloorVerificationError`／`_ResultTableError` の本文へ `RatifiedFreezeError.reason` を保持。

- [test_s8b_ratified_verify.py:872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:872)
  - g1 mismatch、valid g1、実体の g2 no-op を追加。
  - historical reverify の既存 test は未変更。

- [test_s8c_result_judge.py:1584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8c_result_judge.py:1584)
  - verify の mismatch・床値 bytes 読込前停止。
  - publish の mismatch・3 表完全不在。
  - valid g1 の verify／publish 正例を追加。
  - 既存 assert は変更せず、patch fixture を新 API が通る形へ追随。

## 現行 → 実装後の受理・拒否対比

| 入力の型／状態 | 現行 | 実装後 | 狭める・不変 |
|---|---|---|---|
| 非 `RatifiedFreeze` | 新 API なし | `floor-artifact-invalid`, cause=`argument-type` | fail-closed 境界 |
| exact `RatifiedFreeze`, valid g1 | s8c は bytes／binding が正しければ受理 | 選択規則通過後、従来どおり受理 | 不変 |
| exact g1、より早い適格 run あり | s8c verify／publish は受理可能 | `floor-selection-rule-mismatch` で拒否 | 狭める |
| exact g1、適格性導出不能 | s8c は受理可能 | `floor-selection-eligibility-underivable` で拒否 | 狭める |
| exact g1、選択検証不能 | s8c は受理可能 | `floor-selection-unverifiable` で拒否 | 狭める |
| exact g2 | 従来の loader／s8c 挙動 | 新 API は無観測で return | 不変 |
| historical reverify | 選択規則を課さない | 呼出経路・受理集合とも未変更 | 不変 |
| bytes／binding 不一致 | 拒否 | 引き続き拒否 | 不変 |

## g2 不変性の根拠

コードでは exact 型検査直後の [generation 分岐:3572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:3572) で、`generation_number != 1` を即 return させた。

[test_g1_only_selection_helper_is_noop_for_g2:1461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:1461) は `build_production_emitter_g1` → `append_production_emitter_g2` で生成し、`load_ratified_freeze` が返した実体の g2 を使用する。さらに `_source_record_path_sha` を発火 sentinel に置換し、g2 では source record すら検査しないことを固定した。

## 実走結果

実装済み・未実走。

`tools/run_tests.py` へ以下の 7 nodeid を渡したが、Pegasus の `qstat -Q` preflight が rc=1、child 未起動の infrastructure rc=16 で停止した。したがって緑とは申告しない。

- `test_s8b_ratified_verify.py::test_g1_selection_helper_rejects_rule_mismatch`
- `test_s8b_ratified_verify.py::test_g1_selection_helper_accepts_valid_selection`
- `test_s8b_ratified_verify.py::test_g1_only_selection_helper_is_noop_for_g2`
- `test_s8b_ratified_verify.py::test_historical_reverify_does_not_apply_current_floor_selection`
- `test_s8c_result_judge.py::test_floor_verification_rejects_selection_mismatch`
- `test_s8c_result_judge.py::test_publish_rejects_when_selection_mismatch`
- `test_s8c_result_judge.py::test_valid_g1_selection_still_verifies_and_publishes_three_tables`

補助検査は `git diff --check` 成功、指定 4 file の静的 syntax compilation 成功。

## 波及の静的列挙

`s8b_ratified_freeze` の exact grep 該当:

- 直接・静的 consumer test:
  `test_autonomous_trial_completeness.py`, `test_ccbench_spawn_sites.py`,
  `test_official_perf_closure.py`, `test_p3_autonomous_workload_trial.py`,
  `test_s8b_approved.py`, `test_s8b_binding_driftguards.py`,
  `test_s8b_floor_stats.py`, `test_s8b_holdout_admission.py`,
  `test_s8b_oracle_driver.py`, `test_s8b_oracle_manifest.py`,
  `test_s8b_oracle_report.py`, `test_s8b_protocol_builder.py`,
  `test_s8b_ratified_freeze.py`, `test_s8b_ratified_verify.py`,
  `test_s8b_verdict.py`, `test_s8c_acceptance_receipt_v2.py`,
  `test_s8c_preregistration_invariant.py`,
  `test_s8c_preregistration_predicates.py`。
- support／metadata:
  `calibration_freeze_authority_execution.py`,
  `real_repo_ratified_memo.py`, `README.md`,
  `acceptance_duration_ledger.json`,
  `fixtures/calibration_freeze_authority/cases/{freeze-history-immutability,orphan-generation-no-authority,unapproved-generation-no-authority}.json`。
- 判断: 既存 loader、launch、reverify、定数、subprocess site は未変更。直接影響は新 API test と、間接 consumer の `test_s8c_result_judge.py`。oracle manifest 経路は本 wave では未配線・未変更。

`s8c_result_judge` の exact grep 該当:

- `test_s8c_result_judge.py`
- `test_s8c_preregistration_invariant.py`
- `test_s8c_preregistration_predicates.py`
- `acceptance_duration_ledger.json`

`test_s8c_preregistration_predicates.py` の C07 は reachable private helper を辿るため、新 loader call も静的到達範囲内。公開 3 entrypoint と `__all__` は不変。ただし未実走。

production 側では `s8c_result_judge` の importer/caller は引き続き 0。新 API の production consumer は `s8c_result_judge.py` のみ。共有 fixture は `test_s8b_ratified_verify.py` が既存 `test_s8b_ratified_freeze` emitter builder を利用する。

新規 test file はないため、file 集合メタテストや自走 harness への追加登録は不要。既存 `_run()` と pytest discovery の範囲内である。duration ledger は所有外かつ実測未取得のため未変更。

## 残した赤・未了

既知の test failure はないが、Pegasus dispatch infrastructure failure により nodeid 実走と consumer test 全走は未了。親側で queue／実行基盤が利用可能になった時点の再走が必要。

変更は指定された 4 file のみに残しており、commit／add／stash は行っていない。

## 総括

g1 の選択規則だけを s8c verify／publish に追加した。  
g2、静的 loader、historical reverify の挙動は維持した。  
mismatch 時は bytes 読込前／表作成前に理由付きで拒否する。  
valid g1 の正例と実体 g2 の無観測 test を追加した。  
実テストは Pegasus rc=16 のため未実走で、closed とは申告しない。