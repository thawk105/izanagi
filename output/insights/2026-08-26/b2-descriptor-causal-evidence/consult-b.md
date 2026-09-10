## 総括

- 再凍結を伴わない「ユーザー裁定後の別文書」で generation 判定規則を固定できる手順になっており、8b §8 を迂回する。
- 「pilot を B-2 証拠に数えない」は pilot 固有の consumer を持たず、現在は全系列共通の `certifying=false` により恒真化しているだけである。
- brief の「判定パラメータ consumer は実在する」は production 到達可能性まで一般化できず、8b §10.2 の解除条件を満たさない。

現状は **NO-GO**。ユーザー裁定だけでなく、実際の 8b 再凍結と対応する 8c 改訂を先に完了させる必要がある。静的検査のみで、テストは実走しておらず緑とは報告しない。

1. [severity: must-fix] [real] 「裁定後は 8b/8c を変更しない」まま別文書で generation 出力規則を固定する手順は、8b §8 の再凍結を迂回する。
   [根拠 `plan.md:44-48`, `plan.md:59-69`, `plan.md:120-131`, `ref-phase3-8b-descriptor-design.md:255-267`, `ref-phase3-8c-preregistration.md:289-301`]
   [成果物影響] 未批准の generation outcome 定義から導出した `n` / `delta_min` / `sd_max` が正式 judge に入り、`official_status` の成立条件と certified 受理集合を変えうる。
   [提案] author 開始条件を「裁定」ではなく「旧 freeze・変更理由を残した 8b 再凍結 commit＋ユーザー承認＋対応する 8c 条件契約世代の改訂完了」にする。それまでは ruling package のみとし、新 prereg を作らない。

2. [severity: must-fix] [real] `b2_causal_evidence=false` 等を三か所へ書いても、それを読む pilot 固有の起動・manifest・judge・受入 consumer が計画されていない。
   [根拠 `plan.md:58-69`, `plan.md:86-93`, `plan.md:105-114`, `tools/check_docs.py:124-164`, `orchestrator/campaign/trial_registry.py:4021-4028`, `orchestrator/campaign/trial_registry.py:6120-6123`]
   [成果物影響] 現在の全件共通 `certifying=false` が将来解除された際、pilot 行を正式 6 cell・三表・B-2 レポートから拒否する pilot 固有条件がなく、参照・受理集合へ混入しうる。
   [提案] pilot schema/namespace と immutable な `experiment_role=pair_planning_pilot` を設け、正式 manifest・result judge・acceptance がその role を必ず拒否するよう結線し、pilot artifact を formal 入力へ差し込む positive control を置く。それまでは「非算入は未機械強制」と明記する。

3. [severity: must-fix] [real] brief の「判定パラメータの機械検証 consumer は既に実在する」は、validator の存在を production consumer の存在へ過大一般化している。
   [根拠 `brief.md:31-36`, `orchestrator/campaign/s8c_preregistration.py:818-820`, `orchestrator/campaign/s8c_preregistration.py:1042-1045`, `orchestrator/campaign/s8c_preregistration.py:1925-1956`, `orchestrator/campaign/s8c_result_judge.py:217-239`, `orchestrator/campaign/s8c_result_judge.py:1012-1019`]
   [成果物影響] 誤って §5 を記入すると、`section5_value_violations` を無視したまま `all_filled` が成立し、将来 C01〜C12 の閂が開いた際に不正な閾値が `official_status` を左右する。
   [提案] brief は plan 同様「parser と judge 内 validator はあるが production consumer は無い」へ訂正する。§5 の歴史 bytes から sealed parameter を構築し、violations 空を発効条件へ結線し、formal acceptance→judge の実呼び出しを追加した世代だけを解除根拠にする。受理意味の変更なので必要な decider bump・8c 世代 record・8b §8 承認も行う。

4. [severity: must-fix] [real] 値の先入れは避けているが、「結果前に導出関数を commit」だけでは、pilot 結果に自動適合する恒真的な閾値関数を排除できない。
   [根拠 `brief.md:61-66`, `plan.md:61-63`, `ref-phase3-8b-descriptor-design.md:464-484`]
   [悪用例] candidate `n` ごとの prefix から平均/SD 比が最大の `n` を選び、`delta_min=pilot平均/2`、`sd_max=pilot標本SD+ε` とする関数を事前 commit する。結果閲覧前登録の形式は満たすが、好都合な prefix と、その pilot が通る境界を結果から選べる。
   [成果物影響] pilot ノイズに応じて formal の `n` と成立境界が動き、同じ正式観測でも `paired_repeat_contrast` と `official_status` の受理結果が変わる。
   [提案] `delta_min` は pilot と独立な実質的重要性から固定し、pilot は固定済み α/β・効果量・分散上側限界から `n`/`sd_max` を導く用途へ限定する。欠測、prefix、丸め、上限到達、候補不成立時の `null` を含む完全な純関数と source binding を凍結し、データ依存の候補選択を禁止する。

5. [severity: nit] [refuted] correctness gate を片側化する、screen-reject を certified にする、pilot だから gate を省く、といった緩和は該当なし。
   [根拠 `brief.md:46-55`, `plan.md:60-65`, `plan.md:105-114`, `ref-phase3-8b-descriptor-design.md:199-205`]
   [成果物影響] legacy + S2、不通過時の判定不能、screen-reject 非認証の受理集合は設計上変更されない。
   [提案] 現文言を維持し、pilot 実走を起票する段階では両 gate の受領証を消費する consumer まで焦点検査する。

6. [severity: nit] [refuted] 観測者効果について、設計上の trace-enabled verify と trace-disabled bench の混同は該当なし。
   [根拠 `plan.md:60`, `ref-phase3-8b-descriptor-design.md:203-205`]
   [成果物影響] 設計どおりなら性能表へ trace-enabled 側の数値は入らず、順位・対差・`official_status` は変わらない。
   [提案] 文書要件は維持する。ただし本 wave は文書しか変更しないため、実走時の build identity・trace flag の機械照合は未証明と明記する。

7. [severity: nit] [real] brief の「§5 の未凍結は 7 欄」は実測と内部矛盾し、正しくは 9 欄中 8 欄が未記入である。
   [根拠 `brief.md:24-30`, `measured-activation-report.txt:3-11`, `plan.md:3-7`]
   [成果物影響] activation の受理集合は引き続き閉じるため変わらないが、現在地レポートの未記入件数と後続 checklist が 1 欄ずれる。
   [提案] author へ渡す正本は plan の「8 UNFILLED / 1 FILLED」に統一し、brief の「7 欄」を引用しない。