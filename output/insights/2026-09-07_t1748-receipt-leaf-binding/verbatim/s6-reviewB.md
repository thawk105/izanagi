## 所見

1. **新しい負の対照が別の検査に先取りされるという懸念**

- 主張 — `test_v5_rejects_reaggregated_single_cross_binding_leaf_substitution` は、追加された個別 leaf 照合だけを発火させる有効な負の対照である。
- 原典 — `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1067-1089`、`orchestrator/campaign/s8c_acceptance_receipt.py:1976-2038`、`orchestrator/campaign/s8c_acceptance_receipt.py:2053-2076`、`orchestrator/campaign/s8c_acceptance_receipt.py:1576-1733`、`orchestrator/campaign/s8c_acceptance_receipt.py:194-195`
- 判定 — refuted。差し替え前の同じ fixture を無条件で検証してから、最後の trial の leaf と top-level aggregate だけを変更し、受領証を再 commit している。したがって schema、receipt path、HEAD blob、manifest・registry・lifecycle・report・journal hash、arm execution は差し替え前と同一である。aggregate は forged leaf から再計算されており、後段の attempt consumption は leaf を参照しない。新照合は aggregate と attempt 検査より前にあり、削除すれば forged receipt は後段まで通る。`pytest.raises` は `_fail` が生成する `[receipt-cross-binding] trial_id=... leaf differs from independently rederived projection` の全文だけに `^...$` で一致する。
- 深刻度 — nit（是正不要）
- 成果物影響 — 放置しても forged leaf は新照合で拒否され、certified 選択・受理集合・proof 参照の値は変わらない。

2. **登録済み M1〜M8 に殺せない変異があるという懸念**

- 主張 — 事前登録された 8 変異は、すべて既存または今回変更された test node に静的な失敗経路がある。
- 原典 — `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1748-receipt-leaf-binding/s6/s4-adjudication.md:93-106`、`orchestrator/campaign/s8c_acceptance_receipt.py:2026-2038`

| 変異 | 失敗する node と静的根拠 |
|---|---|
| M1 block 削除 | `test_v5_rejects_reaggregated_single_cross_binding_leaf_substitution`。leaf と aggregate を一緒に差し替えているため、block が無ければ `pytest.raises` が例外未発生で失敗する。`test_s8c_acceptance_receipt_v2.py:1072-1089` |
| M2 stored leaf との自己照合 | 同 node。forged leaf 自身との比較になり、M1 と同様に例外未発生になる。`test_s8c_acceptance_receipt_v2.py:1072-1089` |
| M3 `!=` を `==` | `test_v5_attempt_binding_accepts_all_predeclared_observed_units`。正しい再導出 leaf と stored leaf が等しいため、反転条件は正当な受領証を拒否する。`test_s8c_acceptance_receipt_v2.py:1039-1061` |
| M4 guard を v4 に変更 | 新設負例は current v5 なので照合が発火せず、再構成済み aggregate と正しい attempt registry を通過して例外未発生になる。`test_s8c_acceptance_receipt_v2.py:1067-1089`、`s8c_acceptance_receipt.py:2053-2076` |
| M5 `receipt.trials[:-1]` | 負例が明示的に最後の row を改変するため、照合対象から外れて例外未発生になる。`test_s8c_acceptance_receipt_v2.py:1072-1089` |
| M6 `events=()` | `test_p5_six_complete_terminal_reports_pass_acceptance`。この fixture は no-build だが role-attempt events を生成する。発行側 leaf はその invocation IDs を含み、standalone verifier だけ空 events にすると leaf が食い違う。`test_trial_registry.py:973-992`、`test_trial_registry.py:1652-1683`、`test_trial_registry.py:1775-1779`、`autonomous_trial_completeness.py:4165-4188` |
| M7 `run_root=repository_root` | materialized-build node。発行側は journal 親を run root とし、campaign roots から output root を導出する。standalone verifier の root を repository root にすると campaign output root または root-relative proof が食い違い、成功期待が失敗する。`trial_registry.py:6123-6138`、`trial_registry.py:6168-6173`、`test_trial_registry.py:1823-1836`、`test_trial_registry.py:1904-1909` |
| M8 build report を no-build 化 | 同 materialized-build node。fixture は `do_build=True` と materialized campaign を持つため、発行済み build-mode leaf に対して verifier が no-build-mode digest を作り、成功期待が失敗する。`test_trial_registry.py:1304-1311`、`autonomous_trial_completeness.py:4226-4230`、`test_trial_registry.py:1904-1909` |

- 判定 — refuted。特に M3 は正例を拒否する向き、M5 は最後の row を外す向きを直接識別している。既存 test の再照準が必要な変異は見つからない。
- 深刻度 — nit（是正不要）
- 成果物影響 — 放置しても M1/M2/M4/M5 による forged proof 受理と、M3/M6/M7/M8 による正当 receipt 拒否の双方が test で観測されるため、certified 選択・受理集合・proof 参照に未検出の変化は残らない。

3. **正例全体が同じ計算の反復で恒真になるという懸念**

- 主張 — `_upgrade_to_current` の no-build 正例単体は同じ計算の反復だが、materialized-build 正例が production 発行経路と standalone 検証経路の引数導出を独立に突き合わせており、正例集合全体は恒真ではない。
- 原典 — `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:506-519`、`orchestrator/campaign/s8c_acceptance_receipt.py:2008-2032`、`orchestrator/campaign/s8c_acceptance_receipt.py:1366-1394`、`orchestrator/campaign/trial_registry.py:5060-5100`、`orchestrator/campaign/trial_registry.py:6078-6173`、`orchestrator/tests/test_trial_registry.py:1823-1836`、`orchestrator/tests/test_trial_registry.py:1904-1909`
- 判定 — refuted。no-build fixture では双方とも receipt の `report_path` と `attempt_journal_path` を読み、journal 親を `run_root`、`output_root=None` として同じ `verify_s8c_cross_binding` を呼ぶため、この正例単体は引数導出の正しさを独立には証明しない。一方、materialized-build receipt は `trial_registry` が snapshot 済み report/events、journal 親、campaign roots 由来の output root から発行する。standalone verifier は receipt の参照 bytes と journal path から再構成し、別コードで `output_root=run_root.parent.parent` を導出する。materialized node はその発行物を追跡して standalone verifier へ渡すため、M7/M8を含む引数・mode の食い違いを観測でき、この穴を埋めている。
- 深刻度 — nit（是正不要）
- 成果物影響 — 放置しても production 発行済み materialized-build receipt が独立再構成で受理されることを確認でき、正当 receipt の受理集合や参照される leaf proof は変わらない。

4. **`"do_build": False` が 12 node の元の意味を変えるという懸念**

- 主張 — 追加された flag は各 node を no-build leaf の正当な分岐へ通すためのもので、12 node は引き続き元の受理理由または拒否文言を観測する。
- 原典 — `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:232-259`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:492-536`、`orchestrator/campaign/autonomous_trial_completeness.py:4165-4188`、`orchestrator/campaign/autonomous_trial_completeness.py:4226-4230`

| node | fixture 変更後も残る元の意味 |
|---|---|
| `test_v3_requires_cross_binding_receipt_sha256` | 正しい current receipt を一度受理し、top-level aggregate 欠落だけを schema error にする。`test_s8c_acceptance_receipt_v2.py:1020-1036` |
| `test_v5_attempt_binding_accepts_all_predeclared_observed_units` | 正しい全 6 unit と current capability を受理する。`test_s8c_acceptance_receipt_v2.py:1039-1061` |
| `test_v5_rejects_attempt_registry_bound_to_another_manifest` | leaf は正しいまま、manifest digest の不一致で拒否する。`test_s8c_acceptance_receipt_v2.py:1120-1136` |
| `test_v5_rejects_attempt_registry_bound_to_another_content_commit` | leaf は report/journal から一致し、attempt row の content commit 不一致で拒否する。`test_s8c_acceptance_receipt_v2.py:1139-1162` |
| `test_v5_rejects_attempt_registry_bound_to_another_effective_commit` | 同様に effective commit 不一致で拒否する。`test_s8c_acceptance_receipt_v2.py:1165-1186` |
| `test_v5_rejects_registry_first_tracked_after_prereg_commit` | leaf は一致し、prereg content commit に genesis が無い理由で拒否する。`test_s8c_acceptance_receipt_v2.py:1189-1203` |
| `test_v5_rejects_second_registry_root_on_another_ref` | report/journal は変更せず、alternate genesis の history 検査で拒否する。`test_s8c_acceptance_receipt_v2.py:1206-1226` |
| `test_m3_v5_rejects_predeclared_unit_without_final_terminal` | attempt registry の最後の terminal だけを除き、元の consumption 理由で拒否する。`test_s8c_acceptance_receipt_v2.py:1229-1251` |
| `test_m3b_v5_rejects_receipt_projection_divergent_from_registry` | receipt-side slot projection だけを変更し、projection 不一致で拒否する。`test_s8c_acceptance_receipt_v2.py:1254-1272` |
| `test_p1_v5_accepts_observed_and_terminal_failure_mix` | report status は後から partial に変わるが、no-build leaf は status を preimage に含めない。更新済み report hash と terminal-failure が対応し、元どおり mixed status を受理する。`test_s8c_acceptance_receipt_v2.py:425-434`、`test_s8c_acceptance_receipt_v2.py:1275-1289` |
| `test_p2_v5_accepts_retryable_failure_followed_by_next_attempt` | attempt registry の retry/final 列だけが変わり、report/journal leaf は変わらないため元どおり受理する。`test_s8c_acceptance_receipt_v2.py:1292-1302` |
| `test_v3_aggregate_is_recomputed_from_trial_leaves` | 個別 leaf はすべて一致した後、top-level aggregate だけを壊して従来の aggregate gate で拒否する。`test_s8c_acceptance_receipt_v2.py:1328-1341` |

- 判定 — refuted。no-build leaf の preimage は `trial_id`、cell 数、journal の role-attempt IDsであり、12 node が変更する attempt binding、history、slot projection、aggregate、statusを先取りしない。P1 の status 変更も明示的に preimage 外である。
- 深刻度 — nit（是正不要）
- 成果物影響 — 放置しても 12 node の受理集合と拒否理由は維持され、attempt proof・aggregate proof・current capability の参照値は別理由へすり替わらない。

5. **v3/v4 legacy receipt の受理集合が狭まるという懸念**

- 主張 — `_upgrade_to_current` の leaf 生成変更と fixture の `do_build` 追加は、v4 へ下げる 2 nodeおよび一般の legacy v3/v4 leaf 受理集合を狭めない。
- 原典 — `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1092-1117`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1372-1389`、`orchestrator/campaign/s8c_acceptance_receipt.py:2026-2038`、`orchestrator/campaign/s8c_acceptance_receipt.py:2053-2074`、`orchestrator/campaign/s8c_acceptance_receipt.py:2088-2104`
- 判定 — refuted。両 node は leaf 作成後に schema を `CROSS_BINDING_V2_SCHEMA_VERSION` へ下げる。個別 leaf 再導出は `schema_version == SCHEMA_VERSION` の current v5 にだけ発火するため、v4 では従来どおり aggregate だけを検査する。`test_v4_remains_readable_without_v5_attempt_binding` は readable v4 の受理を維持し、`test_m4_downstream_capability_rejects_readable_v4_receipt` は receipt 自体を受理した後、current capability 境界だけで拒否する。
- 深刻度 — nit（是正不要）
- 成果物影響 — 放置しても legacy v3/v4 の受理集合は不変で、v4 から certified 選択へ進む経路は従来どおり capability gate で閉じ、aggregate proof 参照も変わらない。

## 総括

must-fix は 0 件。新しい負の対照は追加照合だけを識別でき、M1〜M8 はすべて静的に失敗する node が特定できた。no-build fixture 単体の正例は同一計算の反復だが、materialized-build の発行・再検証正例が引数導出の穴を埋めている。12 node と v4 の 2 node に別理由での先取りや legacy 受理集合の縮小は見つからなかった。

判定不能として残した点はない。pytest は依頼どおり実行しておらず、以上は working tree の現物に対する静的判定である。