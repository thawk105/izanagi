## 所見

1. 発行器の leaf と引数可用性

   - 主張 — 検証案は `run_root` / `output_root` を復元できず、発行器の正当な leaf を拒否する。
   - 原典 — `s1-brief-addendum.md:8-19`、`s2-plan.md:58-90`、`orchestrator/campaign/trial_registry.py:6078-6084,6123-6137,6168-6173,6306-6308`、`orchestrator/campaign/s8c_acceptance_receipt.py:1136-1158,1972-1980`、`orchestrator/campaign/autonomous_trial_completeness.py:4217-4230,4270-4277,4579-4588`
   - 判定 — refuted。式は次のとおり一致する。

     ```text
     issuer:     R = resolve(journal).parent
                 O = None または campaign_root.parent.parent = R.parent.parent
                 L = verify_s8c_cross_binding(report, events, R, O)["receipt_sha256"]

     standalone: R' = resolve(receipt.attempt_journal_path).parent
                 O' = None または R'.parent.parent
                 L' = verify_s8c_cross_binding(decoded_report, decoded_events, R', O')["receipt_sha256"]
     ```

     `_assert_digest` が発行時と同じ report / journal bytes を再読し、materialized build では発行側が `O == R.parent.parent` を強制済みである。したがって未変更の現物では `R'=R`、`O'=O`、`L'=L` になる。
   - 深刻度 — nit
   - 成果物影響 — 放置しても正当な発行 leaf の受理集合は狭まらず、`certifying=False` と certified 選択は不変で、既存の cross-binding proof 参照値がそのまま再導出される。

2. mode、fallback、C02 による過剰拒否

   - 主張 — no-build、build-failure、campaignless fallback、または `C02_ARM_BINDING_UNPROVEN` を持つ正当な受領証が新検査で拒否される。
   - 原典 — `orchestrator/campaign/autonomous_trial_completeness.py:336-367,4165-4214,4225-4261`、`orchestrator/campaign/trial_registry.py:6092-6157,6310-6329`、`orchestrator/campaign/s8c_acceptance_receipt.py:1425-1445,1471-1478,1990-2003`、`orchestrator/tests/test_trial_registry.py:527-575,1652-1683,2934-2959`
   - 判定 — refuted。

     - no-build は `do_build=False` で root 使用前に専用式へ返り、発行側と再検証側が同じ `trial_id`、cell 数、journal role ID を使う。
     - materialized build は所見 1 の式で通る。
     - build-failure leaf は全 cell が exact campaignless fallback のとき生成可能だが、現行 issuer は leaf 発行前に fallback を明示拒否する。さらに exact fallback は descriptor を持てず、standalone の既存 descriptor gate と両立しない。したがってこれは現行の正当な acceptance receipt 形ではない。
     - C02 は descriptor proof が不足する no-build receipt に issuer が積む。新 leaf 検査は reason code を入力にせず、既存 gate も C02 が存在すれば descriptor 不足を許容するため通る。
   - 深刻度 — nit
   - 成果物影響 — no-build、materialized build、C02 付き no-build の受理集合は不変で、campaignless build-failure は従来どおり集合外、certified 選択も不変である。

3. 合成 leaf fixture の既存 test 巻き添え

   - 主張 — プランの fixture 是正では、合成 leaf に依存する既存 test の全巻き添えを直せない。
   - 原典 — `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:163-294,490-524,1008-1262,1288-1301,1332-1349`、`s2-plan.md:126-133`
   - 判定 — refuted。production 検査だけを先に入れれば、v5 のまま検証する次の既存 12 node が合成 leaf mismatch で赤になる。

     ```text
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v3_requires_cross_binding_receipt_sha256
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_attempt_binding_accepts_all_predeclared_observed_units
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_rejects_attempt_registry_bound_to_another_manifest
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_rejects_attempt_registry_bound_to_another_content_commit
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_rejects_attempt_registry_bound_to_another_effective_commit
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_rejects_registry_first_tracked_after_prereg_commit
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_rejects_second_registry_root_on_another_ref
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_m3_v5_rejects_predeclared_unit_without_final_terminal
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_m3b_v5_rejects_receipt_projection_divergent_from_registry
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_p1_v5_accepts_observed_and_terminal_failure_mix
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_p2_v5_accepts_retryable_failure_followed_by_next_attempt
     orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v3_aggregate_is_recomputed_from_trial_leaves
     ```

     `_upgrade_to_current` の呼出し自体は 14 件あるが、`test_m4_downstream_capability_rejects_readable_v4_receipt` と `test_v4_remains_readable_without_v5_attempt_binding` は検証前に v4 へ下げるので対象外である。プランは `_fixture` に `do_build=False` を加え、同じ helper で全 6 leaf を実式へ置換するため12件すべてに効く。terminal status の変更は no-build leaf の preimage に含まれないため、mixed-status 2件にも不足はない。
   - 深刻度 — nit
   - 成果物影響 — 是正後は fixture の proof leaf が現物由来へ変わるだけで、各 test の意図した受理・拒否結果と certified 選択値は変わらない。

4. scope 逸脱

   - 主張 — プランは schema、別参照、成果物、台帳、一般化、互換層へ変更を広げている。
   - 原典 — `s1-brief.md:15-27,31-37`、`s2-plan.md:94-138,140-159,179-185,223-237`、`orchestrator/campaign/s8c_acceptance_receipt.py:26-35,69-103`、`orchestrator/campaign/autonomous_trial_completeness.py:4566-4588`
   - 判定 — refuted。production 変更は current v5 の既存 cross-binding leaf 再導出だけである。schema version、field 集合、canonical bytes、reason code、certifying、他の receipt reference は変更しない。build 時に再読する Layer 3、WAL、proposal 等は既存 cross-binding leaf の preimage 13 fieldであり、cross-binding 外への検査追加ではない。v3/v4 guard は既存 reader を維持する分岐で、新しい互換層ではない。
   - 深刻度 — nit
   - 成果物影響 — certified 選択と schema bytes は不変で、受理集合から除かれるのは外部現物と一致しない current-v5 leaf だけ、proof 参照の新設もない。

5. 隠れた機械検査

   - 主張 — subprocess pin、duration ledger、または別の構造 pin がプラン適用で赤になる。
   - 原典 — `orchestrator/tests/test_ccbench_spawn_sites.py:230,293-375,2600-2607`、`orchestrator/tests/conftest.py:1513-1554`、`orchestrator/tests/test_update_acceptance_duration_ledger.py:306-325,329-389`、`orchestrator/tests/acceptance_duration_ledger.json:15561-15585,19525-19527`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:565-606`、`s2-plan.md:100-120,161-169`
   - 判定 — refuted。

     - 新 helper は関数内 import と Python 呼出しだけなので、`s8c_acceptance_receipt.py` の syntactic process site は引き続き `<module>._git` の1件である。
     - 新 node ID の duration 登録は不要で、未登録 node は `None` へ fail-soft する。ledger の検査も `nodeid_count == len(durations)` であり、全 collection との一致は要求しない。
     - import 名を key にする既存 pin は `trial_registry` / `layer3_report` の直接 import だけを禁じる。関数内の `autonomous_trial_completeness` importは該当せず、module import 時にも実行されない。
     - C10 の関数 pin は evidence contract が名指す pathだけを対象とし、今回の新 consumer callを全 repository の追加 call siteとして列挙する仕組みではない。
   - 深刻度 — nit
   - 成果物影響 — 機械検査用台帳や pin の値を変える必要はなく、certified 選択・受理集合・proof 参照にも追加変化はない。

## 総括

must-fix は 0 件です。発行式、正当な mode、C02 付き受領証、既存 test 12件の是正、scope、隠れた pin のいずれにも、過剰拒否または scope 逸脱は確認できませんでした。判定不能として残した点もありません。

pytest は実行しておらず、以上は静的読解による判定です。