## 所見

[severity: must-fix] [M01-COND の SURVIVED control が実装されていない] 新設テストの変異は `unexpected-extra-field-path`、`binding-pair-removed`、`verifier-literal-removed` の3種だけで、全件を `UNSATISFIED` としている。裁定が要求した「literal を残したまま値検証だけを恒真化し、C10 が `EVIDENCE_UNDEFINED` のまま生存する」条件版がなく、無条件版との非対称を機械的に露出できていない。成果物影響: 受理集合そのものは変わらないが、certified 選択の proof chain が literal-presence gate の検知力を値束縛まで過大評価できる状態になる。[根拠 s4-adjudication.md:107-124; orchestrator/tests/test_s8c_preregistration_predicates.py:2818-2824,2885-2887] [提案] production verifier の該当照合だけを恒真化しつつ `proposal_build_source_bindings` literal を残す M01-COND を追加し、`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` の生存を明示的に assert する。

[severity: should-fix] [新設テストの正例が production verifier を検査していない] baseline は実ファイル名へ `TOKEN_ONLY_C10` と `TOKEN_ONLY_C10_REGISTRY` を書いた合成 stub であり、「production-equivalent」と命名しているだけで実際の `verify_s8c_cross_binding` を読まない。このテストは契約比較と evaluator は通すが、production verifier から対象 literal が消えても単独では緑のままである。既存の current-repository snapshot が C10 の実体を通すため全体としては部分的に補われる。成果物影響: 受理集合は広がらないが、新設テストを単独の正例証拠にすると proof chain の production witness が合成物へ置き換わる。[根拠 orchestrator/tests/test_s8c_preregistration_predicates.py:856-873,2835-2843; orchestrator/tests/test_s8c_preregistration_predicates.py:293-295; orchestrator/campaign/autonomous_trial_completeness.py:4217-4224,4575] [提案] current HEAD の実 verifier と registry を評価する、`proposal_build_source_bindings` を名指しした正例を追加する。M01-COND を実 production source の変異として構成すれば併せて解消できる。

## 実装子の報告のうち裏が取れなかった主張

- 「実装差分の設計上の逸脱はない」は裏が取れない。M01-COND が欠落し、専用正例も合成 stub である。
- 現在の `git status` は clean で通常の `git diff` は空だった。そこで実差分は `HEAD^..HEAD` を読んだ。現在は6ファイル差分で、報告時に未発行だった g12 も含まれるため、「5 file の変更だけ」「g12 未発行／未接触」は現レビュー時点の状態とは一致しない。親による後続処理の可能性はある。
- evaluator 直接 smoke の実走履歴は再現していない。書き込み可能 tmp がないためである。ただし報告された4結果はコードから静的に導ける。
- pytest は本レビューでも未実走。

## 裁定への適合

- 裁定 §3 の単一対応表: **適合**。13組の表から `_C10_FIELDS` と `_C10_EXPECTED_FIELD_PATHS` の双方を導出している。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2222-2242]
- 完全一致: **適合**。契約値を `frozenset` 化して `==` で比較し、片方向包含ではない。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2245-2251]
- 14件目の未実装 field path: **適合**。契約集合14件と期待集合13件が不一致になり、literal 検査前に incomplete へ落ちる。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2258-2266]
- 対応表から1組削除: **適合**。両導出集合が12件になっても契約は13件のため、同じ完全一致検査で落ちる。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2237-2251; orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:399-412]
- 恒真化防止: **適合**。期待値は契約自身から作られていない。対応表だけを空にしても現行13件契約と不一致になるため、空集合 subset 単独の恒真にはならない。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2237-2264]
- 受理集合不変: **適合**。C10 正常終端は `EVIDENCE_UNDEFINED`、`SATISFIABLE_CONDITION_IDS` は空で、`evaluate_all` の不正な `SATISFIED` 再チェックも残る。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2273-2278,3092,3202-3210]
- テストの緩和禁止: **適合**。skip・xfail・削除・期待反転は差分にない。変更された4つの hash は固定 domain と canonical JSON から独立再計算して一致し、作業ツリー hash ではない。[根拠 orchestrator/tests/test_s8c_preregistration_core.py:801-830,1195-1198]
- production 正例: **逸脱**。新設専用テストは両層 stub。既存 repository snapshot による実体検査はあるが、裁定 §4 の専用正例にはなっていない。[根拠 orchestrator/tests/test_s8c_preregistration_predicates.py:2835-2843]
- A2 の限界表明: **適合**。テスト名と docstring の双方が、生成・再読・値束縛を証明しないと明記している。[根拠 orchestrator/tests/test_s8c_preregistration_predicates.py:2826-2831]
- M01-UNCOND／M01-COND の対: **逸脱**。KILLED 側だけがあり、必須の SURVIVED 側がない。[根拠 s4-adjudication.md:107-124; orchestrator/tests/test_s8c_preregistration_predicates.py:2818-2887]
- 定義順序: **適合**。対応表と導出集合は `_evaluate_c10` より先に定義されており、今回の追加による import 時 `NameError` はない。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2222-2254]
- D967 の成果物: **適合**。契約 field、decider v7、g12 が実差分に存在する。[根拠 orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:407; orchestrator/campaign/s8c_preregistration.py:51; output/s8c-preregistration/condition-freeze/condition-freeze.v1.g12.json:1]

## 総括

production の完全一致 gate 自体は裁定 §3 を正しく実装しており、受理集合も広がっていない。ただし裁定が検知限界の証拠として必須化した M01-COND が欠落しているため、現状は **must-fix 1件、should-fix 1件**。

pytest は未実走。静的には `HEAD^..HEAD` の `git diff --check`、変更 Python の AST parse、契約 hash 4値の独立再計算まで確認した。