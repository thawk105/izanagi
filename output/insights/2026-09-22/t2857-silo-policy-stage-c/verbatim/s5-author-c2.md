## 実装した内容

所有範囲内の10 fileを変更・追加しました。

| file | 内容 |
|---|---|
| `condition_meaning_gate.py` | DefineSpec **40→43**、branch witness **22→25**。軸・PROBE・BREAKを追加。site数は **15／21／1**。主張境界は維持 |
| `test_condition_meaning_gate.py` | 新3 macroの登録・route・companion・site数の期待を追加。meaning集合 **23→26**、cache route **23→24**、CXX_FLAGS route **17→19** |
| `materializer_admission.py` | registry **23→24**。`silo_policy_coverage._build_variant` を `NON_ADMISSIBLE` 登録 |
| `test_p3_build_authority_cli.py` | manual build file **14→15**、非認定 materializer **16→17** |
| `test_ccbench_spawn_sites.py` | 診断 process site **5→6**、非CCBench site **126→127**。新build sinkとhelper呼出し4か所を追加。新macro分の件数を追随 |
| `test_p3_s4_loop.py` | path別token許容集合 **19→30**。新11 patchを追加 |
| `test_campaign.py` | 軸／SOURCE_RELの組 **4→5** |
| `silo_policy_coverage.py` | 指定された赤・緑集合の完全一致判定に変更 |
| `test_silo_policy_coverage.py` | test **9→11**。no-lock-hookの赤過多・赤不足を追加。既存成功期待は維持し、合成観測値を指定表に追随 |
| `test_silo_policy_smoke_entry.py` | 新規4 testと自走harness。実`run_smoke`から4段検査を通す接続試験 |

既存登録entry・行番号pinは変更していません。新sinkのみ変更後の348行を登録しました。

PROBEは変異patchのcontextにも現れ、既存inventoryでは除外されます。そのため、**導入patchの追加conditionalが実在する場合だけ**発見するpath限定memberを追加しました。既存norw／lockskip entryは変更不要でした。

## 確認の実測

- 変更・追加したPython **10 fileの`py_compile`: rc=0**。
- owner TUへ実patchをメモリ上で適用し、各hunkの旧本文と行数を照合しました。完全一致directiveは骨格 **15**、probe **21**、機構変異8枚は各 **1**。新norw／lockskipも各 **1**。
- AST・文字列の読み取りで、上表の登録件数を確認しました。
- A・B・C1・C2の新test計5 fileに、plain-runnerが要求する自走harnessを確認しました。
- test moduleのimport・実行、compiler実行、buildは行っていません。

以下は**実装済み・未実走**です。pathは`orchestrator/tests/`基準です。

```text
test_silo_policy_smoke_entry.py::
  test_smoke_entry_rejects_grammar_violation_before_build
  test_smoke_entry_builds_checked_body_once_with_matching_sha256
  test_smoke_entry_rejects_unavailable_compiler_before_build
  test_smoke_entry_compile_exception_stops_before_build

test_silo_policy_coverage.py::
  test_no_lock_hook_rejects_extra_commit_mismatch
  test_no_lock_hook_rejects_missing_abort_mismatch
  test_judge_rejects_missing_or_empty_checks
  test_characterization_and_mechanism_predicates

test_condition_meaning_gate.py::
  test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches
  test_compile_time_branch_selection_accepts_each_registry_macro
  test_new_branch_selection_supply_meaning_and_admission
  test_new_branch_green_schema_rejects_count_value_and_argv_mutations
  test_v1_domain_and_claim_boundaries_are_exact
  test_module_claim_names_the_exact_38_define_supply_domain

test_ccbench_spawn_sites.py::
  test_reviewed_process_launch_inventory_is_recursive_and_exact
  test_patch_define_inventory_matches_condition_gate_registry
  test_production_build_sinks_include_certify_calibration_script
  test_silo_policy_diagnostic_helper_sites_are_exact
  test_define_sink_cross_product_has_no_unreviewed_ungated_member
  test_define_sink_cross_product_classifies_t2155_production_sinks_exactly
  test_define_sink_cross_product_t2520_certify_entry_removal

test_p3_build_authority_cli.py::
  test_python_ccbench_manual_materializers_are_explicitly_non_admissible
  test_single_registry_has_typed_compatible_projections

test_p3_s4_loop.py::
  test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted

test_campaign.py::
  test_axis_driver_source_rel_within_edit_surface
```

smoke試験はstockの2 buildを外側の記録器で処理した後、候補のbuild到達を検査します。負例では候補build **0回**、正例では最初の候補build **1回**で停止し、materializeされた本文のSHA256を入力本文と比較します。4段検査内部の呼出しは差し替えていません。

## 残る赤の見込み

**define／build-sink cross-product検査は赤になる見込みです。未実走のため確定結果ではありません。**

C1の`_build_variant`は`for macro in gate_macros`内でgateを呼びます。一方、既存解析はループ0回の経路を残し、ループ内のgate証拠を後続sinkへ持ち越しません。新sinkは登録しましたが、この解析との不整合は残っています。

修正にはdriverのgate経路などへの追加変更が必要です。今回許可された`coverage.py`の変更は§3だけなので、検査の緩和・deferred追加はしていません。

- `patches/README.md`への新patch・適用順・診断用途の説明は親側の残件です。
- 新testのREADME allowlist追加は不要です。
- 所有外consumerの`test_s8b_floor_campaign.py`内materializer走査への波及は未実走です。変更していません。

## 未了と疑問

- 全test、M-SMOKE-SKIPの変異実走、CCBench build・動的観測は未了です。
- cross-productの赤見込みを解消する追加修正と実走確認が必要です。
- docs・他単位成果物・所有外tracked fileは変更していません。
- git index／履歴を書き込む操作は実行していません。

## 総括

登録追随、smoke接続4試験、機構変異の集合完全一致判定を実装し、10 fileの構文検査は通りました。**閉集合検査の赤見込みが1件残るため、C2完了・テスト合格は主張しません。**