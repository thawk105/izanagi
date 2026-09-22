## 直した内容

以下のパスは作業root Uからの相対パスです。

- **F1 — `orchestrator/campaign/silo_policy_coverage.py:324,362`**：gate集合の検査・全結果の成功確認を行うhelperをbuild前に無条件で呼び、非stockの空集合・不成功を拒否します。交差検査の根拠は`test_ccbench_spawn_sites.py:1088,1924,1988`で、完全gateのwrapper呼出しは後続へ証拠を伝播しますが、for本体の証拠はゼロ回経路へ伝播しません。
- **F2 — `orchestrator/tests/condition_gate_test_support.py:26,39`**：cache変数とuniversal definitionを追加し、SILO_POLICY_VARIANTの条件選択をfixtureで観測可能にしました。既存gateの受理条件は維持し、同経路で追加修正が必要な別fixtureは見つかりませんでした。
- **F3 — `orchestrator/campaign/silo_policy_coverage.py:275`**：描画・DiffQuarantine・effect gateを既存`quarantine(..., write=False)`経由に統一しました。構文・compileの拒否や本文不一致ではmaterialize/buildへ進まず、sha256一致確認も維持しています。
- **F4 — `orchestrator/campaign/screening_driver.py:71`**：3 macroの既定値0を追加し、要求生成時の欠落を解消しました。要求はGenome内のmacroからだけ生成されるため、既存Genomeの条件要求・build引数は増えず、gateの拒否条件も変わりません。
- **F5 — `orchestrator/campaign/silo_policy_coverage.py:67,78,552`**：同じprefix unlock変異をabort0／maxwaitで走らせ、case名とJSONの`target_exit`で出口を区別しました。各正常対照には同方策のcertifiedを要求し、変異がtrace-timeoutにならなければ不合格です。
- **F6 — `orchestrator/campaign/silo_policy_coverage.py:80,531,569`**：重複対照5件を焦点走の観測へ対応付け、参照元をJSONに記録します。対照判定式とcase/check集合の完全一致を維持し、欠落・不成功は拒否します。
- **F7 — `orchestrator/tests/test_silo_policy_smoke_entry.py:142`**：実compilerを遅延させる既存fixture方式でtimeout接続試験を追加しました。`timed_out=True`で候補buildへ到達した場合は試験が失敗します。
- **F8 — `patches/instr-silo-function-policy-probe.patch:35,136`、`orchestrator/campaign/silo_policy_coverage.py:92,213`、`orchestrator/tests/test_silo_policy_coverage.py:222`**：同一workerの成功commit後の比較を別計数し、parse対象とfocus判定へ接続しました。一致0回または不一致ありの観測を拒否する`test_focus_requires_post_commit_state_observation`を追加しました。

## 確認の実測

- **py_compile成功**：変更したPython 5ファイル。
- **厳密適用成功**：骨格→probe、および骨格→probe→機構変異8枚それぞれについて`git apply --check`／`git apply`と実ファイルの変化を確認。
- **単独TU構文検査成功**：7方策と、probe・実際の`after_abort`比較関数を含む抽出TUを`g++ -std=c++17 -Wall -Wextra -Werror -fsyntax-only`で確認。
- `.scratch-t2857-fix1/`は削除済み。

以下はすべて**実装済み・未実走**です。各一覧のファイル名とnode名を`::`で結合します。

`orchestrator/tests/test_silo_policy_coverage.py`：

```text
test_judge_rejects_missing_or_empty_checks
test_smoke_judge_requires_every_policy_and_real_success
test_norw_judgement_requires_exit_code_one
test_characterization_and_mechanism_predicates
test_coverage_reuses_controls_and_separates_prefix_exits
test_focus_requires_post_commit_state_observation
test_no_lock_hook_rejects_extra_commit_mismatch
test_no_lock_hook_rejects_missing_abort_mismatch
test_probe_parser_rejects_incomplete_duplicate_unknown_negative_records
test_strict_patch_stacks_and_one_site_mutations
test_probe_sites_independently_stamp_all_seven_reasons
test_focus_accepted_by_real_unit_b_interface
test_prepare_policy_real_four_stages_and_body_binding
```

`orchestrator/tests/test_silo_policy_smoke_entry.py`：

```text
test_smoke_entry_rejects_grammar_violation_before_build
test_smoke_entry_builds_checked_body_once_with_matching_sha256
test_smoke_entry_rejects_unavailable_compiler_before_build
test_smoke_entry_compile_exception_stops_before_build
test_smoke_entry_compile_timeout_stops_before_build
```

既存の赤8件も未再実走です。

```text
test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2520_certify_entry_removal
test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly
test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member
test_condition_meaning_gate.py::test_compile_time_branch_selection_accepts_each_registry_macro[SILO_POLICY_VARIANT]
test_condition_meaning_gate.py::test_new_branch_selection_supply_meaning_and_admission[SILO_POLICY_VARIANT]
test_condition_meaning_gate.py::test_new_branch_green_schema_rejects_count_value_and_argv_mutations[SILO_POLICY_VARIANT]
test_p3_s4_loop.py::test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty
test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs
```

## 変えていないことの根拠

最終差分は許可された6ファイルだけで、index差分・未追跡ファイルはありません。docs、所有外ファイル、機構変異patch、閉集合・condition登録簿は変更していません。

既存assertの緩和・削除・skip・xfailはありません。新設testの入力カウンタとpatch参照をproductionへ追随させ、追加試験を書いています。

`quarantine`呼び手の閉集合を検索し、確認できたのは既存の`render_hole`入口閉集合です。これを拡張せず、直接呼出しを除去しました。

## 未了と疑問

pytest、coverage／smoke driver、変異matrixは未実走です。F1の交差検査合格とM-POSTCOMMITの実測KILLEDは、親による確認が必要です。

coverageの静的構成は**23 build・22 trace**です。従来26 buildから重複5件を減らし、prefix上限変異と正常対照を各1件追加しています。

## 総括

F1〜F8を許可範囲で修正しました。静的コンパイル・patch厳密適用は成功しましたが、動的な合格は未認定です。commitは作成していません。