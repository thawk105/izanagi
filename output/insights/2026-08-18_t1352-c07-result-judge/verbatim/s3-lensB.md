pytestは未実行。以下は静的検査のみの所見です。

[severity: must-fix] [未登録の `_evaluate_c07` は実効 gate にならず、専用テスト以外の consumer がない] [orchestrator/campaign/s8c_preregistration_evidence.py:1806-1818,1821-1858,1902-1934; artifacts/s2-plan.md:188-217; s1-brief.md:42-45] [提案: 今 wave は「静的形状の準備」と明記し、実効化は契約反転、g8、registry、negative control、正式 caller を同一 bundle にする。staged registry は作らない。]

影響: certified 選択は生成されず、activation report の C07 は `floor-judge-contract-undefined` のまま、台帳行と受理集合は変わらない。

[severity: must-fix] [C07 の machine_checkable 一手反転は、checked 集合不足と欠落関数の二重障害で成立しない] [orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:268-301; orchestrator/tests/test_s8c_preregistration_invariant.py:43-122,206-329,427-449; artifacts/s2-plan.md:15-18,180-193] [提案: C07 の実際の acceptance caller と module path を裁定し、契約、invariant の checked set、実装を同時に g8 へ反映する。欠落を exclusion pin で隠さない。]

C07 の `reachable_from` を全列挙すると次のとおりです。

| path | name | 計画後の実在 | C07 の checked/exclusion | 判定 |
|---|---|---:|---:|---|
| s8c_result_judge.py | accept_trial | なし | なし / なし | 欠落 |
| s8c_result_judge.py | verify_floor_bytes | あり | なし / なし | C07 checked mapping 欠落 |
| s8c_result_judge.py | judge | あり | なし / なし | C07 checked mapping 欠落 |
| s8c_result_judge.py | publish_result_table | あり | なし / なし | C07 checked mapping 欠落 |
| s8b_ratified_freeze.py | accept_trial | なし | なし / なし | 欠落 |
| s8b_ratified_freeze.py | load_ratified_freeze | あり。現行:1333 | C01 のみ / なし | C07 checked mapping 欠落 |
| s8b_ratified_freeze.py | verify_floor_bytes | なし | なし / なし | 欠落 |

`MACHINE_CONTRACT_FUNCTION_CHECKS` に C07 はなく、`MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` にも C07 はありません。従って flag だけを反転すると `checked == ...` で落ち、mapping を足しても `accept_trial` 2件と `s8b` 側の `verify_floor_bytes` が残ります。

影響: flag 反転はテスト赤と g8 要求を発生させ、C07 の正式 status、certified 選択、report、台帳、受理集合は安全側の未発効状態から変わらない。

[severity: must-fix] [caller supplied path だけでは正式 run の出力先を repo 外へ強制できない] [artifacts/s2-plan.md:114-138; s1-brief.md:50-51; ruling-full8.md:81-82] [提案: formal caller と `publish_result_table` の双方で絶対 path、repo 外、symlink 解決後の非 descendant を検査する。file-like 出力を許すなら、正式 run では repo 外の管理済み destination だけを渡せる API に限定する。]

影響: `official_status` の6 cell、result-table reference、report/台帳の参照先が repo 内になり得て、正式 run の受理集合を開く前提が崩れる。

[severity: should-fix] [親の4赤は登録変異の結果であり、C07 全体の失敗集合へ一般化できない] [s1-brief.md:22-38; orchestrator/tests/test_s8c_preregistration_predicates.py:1974-2027,2229-2239; artifacts/s2-plan.md:211-217] [提案: 少なくとも「registry 登録のみ」「契約 flag 反転」「C07 path mapping 追加」「直接 evaluator のみ」「decoy 名」「repo 内 output path」を別変異として静的に切り分け、4赤をその範囲の観測値として報告する。]

`test_machine_contract_function_names_exist_and_checked_set_is_exact`、実行 consumer 不在、出力先、同名識別子の誤結合は、親の4件だけでは検出されません。

影響: 4赤を「束ね wave が反転可能」と解釈すると、実際には未検査の欠落を残したまま、certified 選択 0、report/台帳不変、受理集合閉鎖という現状を誤って完了扱いする。

[severity: should-fix] [g7 の frozen bytes が不変でも evaluator identity と波の scan 閉包は変わる] [s1-brief.md:55-63; orchestrator/campaign/s8c_preregistration.py:1272-1285,1661-1675,1759-1772; orchestrator/tests/test_s8c_preregistration_invariant.py:31-41,546-568; docs/phase3-8c-preregistration.md:289-301] [提案: `evidence_contract_sha256` と g7 の不変性とは別に、evaluator module blob hash、ActivationReport の参照、new file の holdout scan と wave path closure を監査する。受理意味を変える登録時は必ず DECIDER_VERSION と g8 を更新する。]

契約 JSON と g7 はこの plan のままなら変わりませんが、`s8c_preregistration_evidence.py` の変更で `ActivationReport.evaluator_module_blob_sha256` は変わります。新規 `s8c_result_judge.py` は現行 `WAVE_REQUIRED_PATHS` に含まれず、wave-specific scan の閉包も明示されていません。

影響: g7 の generation、`evidence_contract_sha256`、protected hash は不変だが、activation report の evaluator reference は変わる。未登録のため certified 選択と台帳は不変、登録すれば g8 と受理集合再評価が必要になる。

[severity: should-fix] [同名 token が旧 judge、非権威 floor ledger、正式 report の値へ誤結合し得る] [orchestrator/campaign/s8b_verdict.py:9-16,841-850,1130-1149; orchestrator/campaign/s8b_oracle_judge.py:452-460; orchestrator/campaign/s8b_holdout_admission.py:2072-2099; orchestrator/campaign/trial_registry.py:2654-2663; orchestrator/campaign/s8c_acceptance_receipt.py:383-427,661-664; orchestrator/campaign/s8b_ratified_freeze.py:3278-3339; artifacts/s2-plan.md:155-180] [提案: `judge`、`verify_floor_bytes`、`publish_result_table` を module-qualified AST binding で確認し、`measurement_head` と `env_tag` は producer、schema、role まで検証する。旧 `judge_combined`、floor ledger、decoy import を負の対照にする。]

`judge` は既存の floor 使用判定と oracle 判定にも存在します。`measurement_head` は floor ledger では非権威的ですが、trial report と receipt では coherence binding に使われます。`env_tag` は generation、path、protocol、result、manifest、journal の別々の値を束ねます。

影響:誤った judge または metadata producer を受理すると、6 cell の `official_status`、floor reference、report/台帳の binding が誤り、受理集合を不正に広げる可能性がある。

[severity: must-fix] [必要層の大半が scope 外であり、result judge の実装だけでは正式成果物にならない] [artifacts/s2-plan.md:15-225; docs/phase3-8c-preregistration.md:213-250,327-330; docs/worklog.md:3003-3006; ruling-full8.md:10-16,81-82] [提案: 下表の scope 外層を裁定パッケージ候補として返し、全層が揃うまで formal completion や certified selection を主張しない。]

| 必要層 | 本 wave の扱い |
|---|---|
| C07 contract、condition-freeze、DECIDER_VERSION、g8 | scope 外。凍結 bytes は変更不可 |
| evaluator registry、negative control、activation dispatch | scope 外。P1 で未登録 |
| result judge 本体と直接テスト | scope 内 |
| attempt registry、manifest、schedule、observations、complete-block producer | scope 外 |
| ratified freeze と floor provenance の正式 caller | scope 外 |
| formal acceptance caller と registry append | scope 外。現行名は `assert_trial_registry_acceptance` |
| publish destination の repo 外強制 | scope 外 |
| report、receipt、ledger、proof chain | scope 外 |
| certified-selection consumer | 現 checkout に存在せず scope 外 |
| activation/admission gate と bundle acceptance tests | scope 外 |

影響: 本 wave 単体では certified 選択値も台帳行も増えず、正式 report は生成されず、C07 は未発効のままなので、成果物の受理集合は閉じたままになる。

## 総括

C07 の一手反転は、現状の checked set と欠落関数のため成立しない。  
P1 の `_evaluate_c07` は直接テスト用の静的準備であり、実効 gate ではない。  
親の4赤は registry 変異の観測で、全失敗経路の一般化ではない。  
g7 と契約 hash は不変でも evaluator reference は変わる。  
正式出力先の repo 外強制も未実装である。  
同名 metadata と旧 judge の誤結合を追加検査すべきである。  
以上を裁定パッケージへ返し、formal completion は不可とする。