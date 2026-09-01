## 実装した変更 (file:line)

- [契約 JSON](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:407)
  - `proposal.sha256` 直後へ `proposal.build_source_bindings` を追加。
- [C10 評価器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration_evidence.py:2222)
  - 13 組の単一対応表から `_C10_FIELDS` と期待 field path 集合を導出。
  - 契約 field path を完全一致で比較。
  - `verify is None` の直後に検査し、不一致は既存 `CROSS_BINDING_VERIFIER_INCOMPLETE` へ。
- [DECIDER_VERSION](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/campaign/s8c_preregistration.py:51)
  - `s8c-decider/v7` へ更新。
- [core テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_core.py:801)
  - 独立再計算した hash 4 値と v7 literal 3 箇所、テスト名を更新。
  - 契約 hash: `26f7bd4776bff58753f7f1dc7ebecdc5a3d3f1e0f108e1fbc541fdd33dbc13e5`
- [predicate テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:856)
  - `TOKEN_ONLY_C10` を 13 literal 化。
  - [新設した 3 変異テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:2818)で正例、14 件目、対応表縮小、literal 欠落を検査。
  - テスト名と docstring に literal-only の限界を明記。

## 実走した検査 (nodeid と結果。未実走はそう書く)

pytest node は実行開始できていません。

- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_c10_load_bearing_check_proves_literal_presence_only_not_field_generation_reread_or_value_binding`
  - 指定 runner で起動を試行。
  - compute dispatch の `qstat -Q` が uid 認証エラーとなり `rc=16`。child 未開始、3 parameter とも未実走。
- core hash/version nodes、既存 C10 token fixture、producer tests、invariant testsも未実走。
- 発見した meta testsも未実走:
  - `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  - `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

非 pytest 検査では以下を確認済みです。

- `git diff --check`: 問題なし。
- 変更 Python の AST parse、評価器と変更テスト module の import: 成功。
- JSON の 13 件、挿入順、対応表由来集合の各 13 件: 確認済み。
- 独立 hash 計算と production helper: 一致。
- evaluator 直接 smoke:
  - 13/13: `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`
  - 14 件目、対応表 1 組削除、literal 削除: すべて `UNSATISFIED / cross-binding-verifier-incomplete`

したがって状態は「実装済み・pytest 未実走」です。

## 変更前後の C10 挙動

変更前:

- verifier の旧 12 literal、再読 call、registry 到達が揃えば未定義終端へ進む。
- `proposal_build_source_bindings` の literal 欠落や契約 field path の余分・不足は C10 verdict に影響しない。
- `SATISFIED` は返さない。

変更後:

- 契約と対応表が完全一致し、13 literal がすべて存在する場合のみ同じ未定義終端へ進む。
- 14 件目、対応表縮小、literal 欠落は既存 incomplete reason で拒否。
- registry 判定と正常終端は不変。`SATISFIED` 分岐は追加していない。

## 波及可能性の静的列挙

- `get_registry()`、`evaluate_all()`、`activation_report_at()` を通る C10 consumer は新しい完全一致検査を受ける。
- 親が発行する g12 は新契約 hash と decider v7 を束縛する必要がある。現時点では未発行。
- `test_s8c_preregistration_invariant.py` の freeze/hash/version tests は g12 発行後の consumer。
- `test_autonomous_trial_completeness.py` の全 field 正例、no-build 列挙、`proposal_build_source_bindings` mutation は producer 側の既存 consumer tests。
- `acceptance_duration_ledger.json` には改名前の v6 node key が残る。これは実測 duration ledger であり、本変更では更新していない。
- core/evaluator は closure 内なので dirty 木では一時的な `current-closure-unavailable` があり得る。D1163 により commit 後の closure 差は既存 campaign を失効させない。裁定記載の tracked 32 件中 newly stale は 0 件。
- `test_s8c_gate_report.py` の synthetic v6 fixtureは意図どおり未変更。

## 裁定から外れた点

実装差分の設計上の逸脱はありません。

検査時、指定 runner が禁止対象の `output/pegasus-dispatch/...` に dispatch 用一時ファイル 4 件を自動生成しました。直前に存在しなかったその exact 4 件だけを除去し、既存 output は削除していません。現在の `git status` は指定された 5 file の変更だけです。

docs、g12、禁止 production file、git index、commit、branchには触れていません。

## 総括

D967 の C10 契約拡張、完全一致 drift 検査、v7、hash pin、正負テストまで実装済みです。pytest は実行基盤の `rc=16` により未実走で、g12 発行と commit は親の担当として残しています。