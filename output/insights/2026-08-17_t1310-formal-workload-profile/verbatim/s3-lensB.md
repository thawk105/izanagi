判定: 現行の `s2-plan.md` はそのままでは着地不可です。主な理由は、正式 profile の producer だけを変更しても、後段の exact predicate、registered campaign、floor、ratified v2 が正式入力を受理できないためです。pytest・build・実測は実行していません。

1. **BLOCKER: layer3 chain が正式 profile を拒否する**

`autonomous_trial_completeness.py:2271` は workload が `producer.WORKLOADS` に存在することを要求し、`2291-2298` で探索用 flags と descriptor を再導出し、`2330-2342` で profile なしの `_campaign_for` と比較します。計画は `WORKLOADS` を探索専用のまま残すため、`rr80/rr20` はここで拒否されます。

`WORKLOADS` に正式名を追加して通すと、探索の accepted set と既存 identity が変わります。

成果物影響: 実装しない場合、正式 run の completeness/campaign-chain 検証が失敗し、追加した場合は探索の workload 集合・campaign ID・descriptor 参照が変わります。

2. **BLOCKER: `pilot_scope` の層間契約が正式値に対応していない**

正式値 `formal-holdout-rr80-rr20` を payload に出すと、`s8c_generation_projection.py:20,621-654` の exact `PILOT_SCOPE` と、`autonomous_trial_completeness.py:241,544-560` の固定 receipt に拒否されます。

逆に payload を `exploratory-ycsb-abc` のまま残すと、producer の正式 campaign identity と role payload/report が食い違います。`p3_autonomous_workload_trial.py:1589-1605,2311-2318,3078-3096` も探索 claim を固定しています。

成果物影響: 正式 run が拒否されるか、正式 scale の結果が探索 run として記録され、scope・claim・参照先が誤ります。

3. **HIGH: 受理述語の exactness は次の通り**

| 層 | 位置 | 正式 profile の扱い |
|---|---|---|
| generation projection | `s8c_generation_projection.py:20,621-654` | formal `pilot_scope` は exact 不一致で拒否 |
| completeness receipt | `autonomous_trial_completeness.py:241,544-560` | formal scope/scientific claim は拒否 |
| completeness nested chain | `autonomous_trial_completeness.py:2271-2342` | formal workload、flags、descriptor、campaign を探索値で再導出 |
| env contract | `env_contract.py:1-19` | `pilot_scope` と `records/threads` の述語なし。契約上も scale は対象外 |
| trial registry | `trial_registry.py:49-57,1119-1166,1268-1273,1406-1412,2608-2625` | profile 名は見ず、registered workload、holdout ratio、campaign ID を別々に検査 |
| campaign identity | `ident.py:151-190` | `pilot_scope` の意味は見ないが、全 `search_config` を hash するため正式値で ID が変化 |
| floor matching | `layer3_report.py:360-381` | `records/threads/workload` の完全一致が必要 |

成果物影響: formal profile 名そのものを一貫して検証する述語がなく、正式値を拒否する層と意味を無視する層が混在します。

4. **BLOCKER: parent の `no-active` 実測を越えていない**

addendum と `parent-measurements.md:M3` は `load_ratified_freeze` が `[no-active]` で失敗することだけを示します。P1a では正式 accepted set は空のままです。v1 の holdout bytes が存在することは、v2 の active pointer、generation approval、実行可能性を意味しません。

` s8b_ratified_freeze.py:1232-1274` は active pointer がない場合に fail-closed です。

成果物影響: loader を pass-through に変えると未承認 v1 を受理し、formal accepted set が黙って拡大します。現状のままなら formal profile の実測成果物は生成できません。

5. **BLOCKER: floor/budget/refreeze が未充填**

v1 freeze は `floor=None`、`budget=None` で、`s8b_holdout_freeze.py:781-800` の `refreeze_note` も再測定・再凍結・承認を要求しています。`docs/phase3-8c-preregistration.md:162-174` の H1/H2 floor、budget、6-cell manifest も未記入です。

`parent-measurements.md:M4,M9` は rr80/rr20 の値と descriptor の受理だけを確認し、layer3 floor の存在を確認していません。

成果物影響: 1,000,000/48 の campaign・perf・descriptor metadata が作れても、正式 floor acceptance と budget 結果は存在せず、正式成果物とは呼べません。

6. **HIGH: campaign identity と manifest の更新が計画から漏れている**

`ident.py:151-190` に formal scope、scale、ratified SHA を入れると campaign ID は変わります。一方、`trial_registry.py:1894-1903,2608-2625` は manifest の campaign ID と最終 report の workload/ratio/campaign を exact 比較します。

既存の `t325_registered_trial` fixture は `test_p3_autonomous_workload_trial.py:5192-5414` 付近で、profile なしの `_prepare_campaign_identity` から manifest ID を作っています。`test_m13_prime_public_launcher_rejects_producer_campaign_derivation_bypass` も同じ前提です。

成果物影響: manifest を更新しない場合は registered launch が拒否され、更新する場合は manifest、registry、preregistration の参照集合が変わります。

7. **HIGH: 探索経路の byte-level 非回帰テストが不足する**

既存の `test_fixture_trial_runs_ycsb_abc_and_binds_descriptor` は descriptor ratio と report wiring を検査しますが、3 sink 全ての `records=100_000`、`threads=4`、campaign preimage、PerfConfig、projection record の同一性を固定していません。`test_no_build_campaign_identity_binds_shared_policy_context` も主に campaign ID の pin です。

特に profile 引数を optional に追加する際、探索側に `formal_scope`、ratified SHA、正式 scale が混入する経路を個別に検査する nodeid がありません。

必要な nodeid 例:

`orchestrator/tests/test_p3_autonomous_workload_trial.py::test_exploratory_default_keeps_three_sink_projection_and_campaign_identity`

成果物影響: 実装しない場合、探索の records/threads、campaign ID、descriptor projection record が変わっても既存テストが緑のままになります。

8. **HIGH: profile selector の fail-closed が不足する**

`p3_autonomous_workload_trial.py:3298-3309` は CLI で `rr80/rr20` を既に parse できます。探索 admission の拒否は `trial_registry.py:1268-1273,1406-1412` にありますが、profile 名自体の programmatic exact check は計画に明記されていません。

`if profile == "formal" else exploration` なら、未知 profile の typo が探索として受理されます。正式 profile に `ycsb-a` を渡す場合、または rr80 を H2 entry に混ぜる場合も、入口で fail-closed にすべきです。

必要な nodeid 例:

- `test_unknown_workload_profile_fails_closed_before_run_root`
- `test_workload_profile_selector_routes_exploratory_and_formal_without_crossing`
- `test_formal_profile_rejects_exploration_workload`

成果物影響: 実装しない場合、未知 selector や profile/workload の混成が探索 accepted set に入り、report scope と campaign identity が誤ります。

9. **変異帰属に穴がある**

| 変異 | 赤になるべき nodeid | 判定 |
|---|---|---|
| 正式 scale literal を `100_000` に変更 | `test_formal_profile_binds_ratified_holdout_to_campaign_perf_and_descriptor`、更新後の `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` | 全 sink の実値を assert すれば殺せる |
| profile 選択分岐を反転 | `test_main_forwards_explicit_formal_profile_and_holdout` だけでは不十分。上記の selector semantic test が必要 | 現計画の AST default test だけでは殺せない |
| 3 sink のうち 1 つだけ探索 scale のまま | bind test が campaign、perf、descriptor を個別 assert すれば殺せる。C01 も literal 欠落なら検出 | dead literal を残して実値だけ 100K にする変異は C01 では殺せない |
| fail-closed の `raise` を `pass` に変更 | `test_formal_profile_scale_mismatch_fails_closed_in_each_sink[campaign|perf|descriptor]`、各 ycsb mismatch nodeid | bad profile を実際に sink に渡し `pytest.raises` する必要がある |

特に `test_formal_profile_scale_mismatch...` が loader の失敗だけを検査し、sink に不一致 profile を渡さない場合、sink 内の `raise -> pass` 変異は赤になりません。

成果物影響: 実装しない場合、formal scale の未使用 token や fail-open sink が残っても検出力のないテスト集合になります。

10. **HIGH: C01 snapshot の予測 reason はまだ根拠不足**

計画は `s2-plan.md:195-200` で次の reason を `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable` と予測しています。しかし C01 は `s8c_preregistration_evidence.py:1414-1445` の AST literal、reachability、loader 属性を確認する静的 predicate です。

`test_s8c_preregistration_predicates.py:395-415` の `TOKEN_ONLY_C01` と `:1849-1877` の `:1869` negative control が示す通り、C01 は token-only 実装を完全には排除しません。` :151` は実装を含む commit blob を実測した後だけ更新すべきで、` :1869` は緩めてはいけません。

成果物影響: 実測前に `:151` を予測値へ更新すると、実装が到達不能でも C01 reason と snapshot 参照を誤って固定します。

11. **HIGH: parent measurements の一般化が過大**

- M1 は現状の literal 欠落を示すだけで、正式 loader から三 sink へ値が到達することを示さない。
- M2 は C01 が literal の上集合しか見ない弱点を示す。
- M3 は current root の no-active だけで、別 generation の承認を示さない。
- M4 は v1 holdout の存在だけで、v2 ratification を示さない。
- M5/M6 は registry binding と探索拒否だけで、正式 profile selector の正しさを示さない。
- M9 は descriptor が正の integer を受理するだけで、floor、budget、campaign、実行結果を示さない。

成果物影響: 「v1 に rr80 があるから正式 profile は実装可能」と一般化すると、formal acceptance、floor、budget、active ratification の空白を隠した成果物になります。

12. **SCOPE 外として裁定へ返すべき層**

計画の実装 scope は `p3_autonomous_workload_trial.py`、そのテスト、C01 snapshot の三面だけです。一方、実際に正式成果物へ効く層は以下です。

- `s8c_generation_projection.py` と `autonomous_trial_completeness.py` の formal payload/chain
- `trial_registry.py` の manifest/campaign binding
- `ident.py` の formal preimage
- `s8b_ratified_freeze.py` の v2 generation、approval、active pointer
- `s8b_holdout_freeze.py` の floor/budget/refreeze
- `s8b_floor_contract.py`、`s8b_floor_campaign.py`、`s8b_oracle_driver.py`、`layer3_report.py`
- env calibration と 6-cell preregistration manifest
- formal result acceptance と非 p3 producer/consumer

これらを同一 wave で実装するなら scope 拡大の裁定が必要です。実装しないなら、この wave の成果物は「探索非回帰と C01 static wiring の確認」に限定し、formal accepted set は空と記録すべきです。

成果物影響: scope 外の層を実装済みと扱うと、producer metadata だけを正式測定・承認済みの結果として参照することになります。

## 総括

安全な結論は、探索 `ycsb-a/b/c @ 100,000/4` の byte-level 非回帰を先に固定し、正式 profile は `no-active`、floor、budget、manifest が埋まるまで受理しないことです。現計画の C01 予測、layer3 接続、変異 matrix、campaign manifest 更新は不足しています。