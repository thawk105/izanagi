## 所見

[severity: must-fix] [P2 の片方向 membership は drift を閉じない] 提案する `all(field_path in requirement.field_paths ...)` は期待値が契約に含まれることしか確認せず、契約側の余分な field を許す。また `_C10_EXPECTED_FIELD_PATHS` と `_C10_FIELDS` が独立した手書き集合なので、片方だけ弱めても production evaluator 内では相互不整合を検出できない。C06 の `field_paths` idiom は片方向 `all` ではなく exact 集合比較であり、`all` は別属性 `reachable_from` 用である。成果物影響: 契約が未検証 field を要求していても C10 が従来終端へ進み、proof chain の契約記述と実際の強制面が乖離する。[根拠 s2/plan.md:42-55; orchestrator/campaign/s8c_preregistration_evidence.py:3243-3251,3279-3285,3513-3517] [提案] `(実装 literal, artifact kind, 契約 field path)` の単一対応表から `_C10_FIELDS` と期待 field path を導出し、`cross_binding_verifier.field_paths` は `frozenset(...) == expected` で exact 比較する。

[severity: should-fix] [`_strings` gate は semantic な field 検査ではない] 検知力はゼロではない。具体的には、`_cross_binding_source_bindings()` の生成・append、bindings の `"proposal_build_source_bindings"` entry、および `S8C_CROSS_BINDING_FIELDS` の同名 entry をまとめて削る弱体化は、変更前なら旧12 literal、`read_and_verify_bytes` call、registry call が残るため `EVIDENCE_UNDEFINED` まで進むが、変更後は新 literal 不在により `UNSATISFIED / cross-binding-verifier-incomplete` になる。ただし、未使用式や `if False:` 内へ `"proposal_build_source_bindings"` を残す、あるいは key は残したまま値を未検証入力へ差し替えると、新旧とも通る。`_strings` と `_called_names` はいずれも `ast.walk` の全 descendant を集め、live branch・dataflow・値の由来を見ない。計画は構文上の subset だとは説明する一方、「load-bearing」と呼び、dead branch／shadow／到達不能定数でも通ることを明記していない。成果物影響: 受理集合を直接広げる `SATISFIED` 経路は生じないが、弱体 verifier を正式 C10 gate が拒否するという proof-chain 主張は、その種の変異には成立しない。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:301-311,373-378,2240-2262; orchestrator/campaign/autonomous_trial_completeness.py:4453-4464,4566-4578; s2/plan.md:38,144-170,188] [提案] analyzer の汎化を scope 外に保つなら、少なくとも「literal 欠落だけを検出し、到達性・値束縛は保証しない」と plan、test 名、worklog に明記する。専用テストにも dead literal が通る limitation control を置き、実検証の根拠は既存 functional tests と分離する。

[severity: nit] [変異 kill の一部は既存検査と冗長] production verifier から entry を削除・改名する単独変異は、既存 positive test が receipt の同 key を直接読むため新 C10 test より先に赤になり得る。`proposal_build_source_bindings` 自体も既存 reference-mutation parameter に含まれる。契約 field の単独削除も repository 全体では frozen contract hash と freeze invariant が先に検出する。計画の tmp-repo テストは evaluator 単体の kill を分離して示す点では有効だが、repository-wide の独立検知器として数えてはならない。成果物影響: 受理集合は変わらないが、proof-chain の検知器数と mutation 帰属を過大報告することになる。[根拠 orchestrator/tests/test_autonomous_trial_completeness.py:4044-4071,4332-4397; orchestrator/tests/test_s8c_preregistration_core.py:1195-1198; s2/plan.md:144-170] [提案] mutation matrix では「formal C10 evaluator の isolated kill」と「既存 runtime/freeze test の先行 kill」を別列にし、後者を冗長 gate と明記する。

## 親 brief 自身の欠陥

[severity: should-fix] [scope の検知力主張が literal 欠落より広く読める] brief:14-15 は `proposal_build_source_bindings` を「落とす実装弱体化」一般を正式 gate が検知すると述べるが、裏付けられるのは関数 AST から同 literal が消える形だけである。値生成・検証呼出しを外して literal を残す弱体化は検知しない。成果物影響: proof chain が保証していない semantic binding まで保証済みと解釈される。[根拠 s1-brief.md:12-15,19-22; orchestrator/campaign/s8c_preregistration_evidence.py:373-378,2244-2248] [提案] scope を「同 field literal を verifier AST から落とす弱体化」に限定し、semantic binding は functional tests の責務と記す。

[severity: should-fix] [P2 の「JSON は文書のまま」は過度に強い] P2 が無くても契約 semantic hash は freeze の `evidence_contract_sha256` と `protected_sha256` に束縛されるため、JSON は単なる文書ではない。一方、現行 `_evaluate_c10` は `field_paths` を読まないので、新 field が C10 verdict に対して load-bearing でない、という限定した主張なら正しい。成果物影響: freeze/provenance の束縛と evaluator の field semantics を混同すると、どの proof-chain 層を P2 が強化するか誤認する。[根拠 s1-brief.md:33-38; orchestrator/campaign/s8c_preregistration.py:203-211,2006-2032; orchestrator/campaign/s8c_preregistration_evidence.py:2240-2262] [提案] 「freeze には既に load-bearing だが、C10 verdict には非 load-bearing」と書き分ける。

[severity: nit] [DECIDER_VERSION の「exact 4箇所」は誤り] brief:26 が挙げる gate_report:84 は production version の pin ではなく synthetic report の自己投影である。実際の4件目は invariant test の tip freeze と現行 decider の動的整合で、plan:172-177 が既に訂正している。成果物影響: brief 単独で実装すると無関係 fixture を編集し、g12/v7 proof-chain の本当の検査を取り落とす可能性がある。[根拠 s1-brief.md:26; s2/plan.md:172-177; orchestrator/tests/test_s8c_preregistration_core.py:2403-2404,2439-2457,2460-2480; orchestrator/tests/test_s8c_preregistration_invariant.py:449-479] [提案] brief の事実6を plan の訂正内容へ更新する。

## (P1)〜(P4) への評価 (賛成 / 反対 / 条件付き + 根拠)

- **(P1) 賛成。** JSON の追加だけでは `_evaluate_c10` の判定条件は変わらない。`_C10_FIELDS` への追加によって、少なくとも新 literal の削除・改名を `EVIDENCE_UNDEFINED` から `UNSATISFIED` へ変えられる。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2222-2262; verbatim-D967.md:3-9]

- **(P2) 条件付き賛成。** これは変更対象である契約 field と evaluator を直接束縛するため、無関係な仮想リスク向け gate ではなく D967 の本題に含めてよい。ただし plan の片方向 `all` と二重手書き集合には反対する。単一対応表から導出した exact 整合に直すことが条件である。[根拠 verbatim-D967.md:3-9; orchestrator/campaign/s8c_preregistration_evidence.py:3513-3517; s2/plan.md:42-55]

- **(P3) 賛成。** 条件10本文は field 名を列挙しておらず、個別 condition hash は Markdown の条件文から算出される。JSON 変更が動かすのは evidence contract hash と、それを preimage に含む protected hash である。[根拠 docs/phase3-8c-preregistration.md:257-259; orchestrator/campaign/s8c_preregistration.py:203-211,1027-1051]

- **(P4) 賛成。** 既存の `proposal.path`／`proposal.sha256` と実装 key `proposal_path`／`proposal_sha256` の対応に従えば、契約表記 `proposal.build_source_bindings`、実装 literal `proposal_build_source_bindings` は整合する。[根拠 orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:399-412; orchestrator/campaign/autonomous_trial_completeness.py:4566-4578]

## 同意する箇所 (短くてよい)

- 親の「現行実装は追加後も回帰しない」という狭い推論は正しい。`_functions` は top-level の `verify_s8c_cross_binding` を取得し、`_strings` はその body の dict key、実物 line 4575 を収集する。
- C10 の正常終端は変更されず、`SATISFIABLE_CONDITION_IDS` も空集合のままである。誤って `SATISFIED` を返しても `evaluate_all` が `ERROR` へ倒すため、計画から受理集合を広げる経路は見つからない。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2258-2262,3075,3185-3193]
- phase doc 不変、v7/g12 再発行、既存 campaign の E1-stale 記録という移行方針は D967 と整合する。

## 総括

変更は恒真ゲートではなく、`proposal_build_source_bindings` literal を実際に消す弱体化に対して検知力を増やす。ただし増えるのは構文上の literal-presence 検知だけであり、field の生成・再読・値束縛までは証明しない。

実装前の必須修正は P2 を単一対応表＋exact 整合へ直すこと。加えて、literal-only の既知限界と既存 functional/freeze tests との冗長性を plan と mutation 帰属へ明記すべきである。pytest は実走しておらず、静的検査のみである。