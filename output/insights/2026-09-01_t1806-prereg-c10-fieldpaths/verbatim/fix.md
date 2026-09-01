## 実装した変更 (file:line)

- [test_s8c_preregistration_predicates.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:243)
  - 既存の実 HEAD snapshot テストへ production verifier の AST literal と C10 判定を名指しで追加。
- [test_s8c_preregistration_predicates.py:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:895)
  - `ACTIVE_VALUE_CHECK_C10` と `NEUTERED_VALUE_CHECK_C10` を新設。
  - 後者は値比較の条件だけを常に通る形へ変更し、13 literal は保持。
- [test_s8c_preregistration_predicates.py:2932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1806-prereg-c10-fieldpaths/orchestrator/tests/test_s8c_preregistration_predicates.py:2932)
  - active が値不一致を拒否し、neutered が同じ不一致を通すことを検査。
  - 両 source の C10 が同じ未定義終端になることを明示的に assert。

変更はこのテストファイルへの 97 行追加だけです。既存期待値、production、docs、既存 tracked output、index、commit、branchは変更していません。

## fix 1 が露出させる事実 (どの source 対で、何が区別できないのか)

`ACTIVE_VALUE_CHECK_C10` は `proposal_build_source_bindings` の actual/expected 不一致を例外化します。`NEUTERED_VALUE_CHECK_C10` は同じ literal とデータ参照を残し、拒否条件だけを恒偽化します。

テストは両方について次を要求します。

- `EVIDENCE_UNDEFINED`
- `completion-proof-not-machine-checkable`

つまり C10 は active な値束縛と無効化された値束縛を区別できません。この生存が意図された限界であり、producer 側 functional test の責務であることを docstring に明記しました。既存の M01-UNCOND `binding-pair-removed` の KILLED assertionも変更していません。

## 実走した検査 (nodeid と結果。未実走はそう書く)

pytest 実走は 0 件です。以下を指定 runner へ渡しましたが、`qstat -Q` preflight が失敗して `rc=16`、`child_started=false` となりました。

- `test_s8c_preregistration_predicates.py::test_c10_gate_intentionally_survives_neutered_proposal_value_check`
- `test_s8c_preregistration_predicates.py::test_c10_load_bearing_check_proves_literal_presence_only_not_field_generation_reread_or_value_binding` の全 3 parameter
- `test_s8c_preregistration_predicates.py::test_current_repository_snapshot_exactly_matches_head`

user cgroup は実効上限 14 GiB に対して現在値約 15.3 GiB、headroom 0 だったため local 実走もできませんでした。

未実走の meta test:

- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

非 pytest 検査:

- `git diff --check`: 問題なし
- 変更テスト module の AST parse: 成功
- active/neutered source が各 13 unique field literalを持ち、比較条件だけ異なることの AST 検査: 成功
- HEAD `9feff6b07` の production verifier AST に `proposal_build_source_bindings` が存在: 成功
- git index 不変: 確認済み

## 波及可能性の静的列挙

- `current_commit_snapshot` の consumer 数と node 名は不変。既存 consumer 内で HEAD verifier の追加読取りが発生します。
- 新規 survivor test は `_init_repo`、`_write`、`_commit`、`_result`、`TOKEN_ONLY_C10_REGISTRY` を共有します。
- production evaluator、`get_registry()`、`evaluate_all()` の実装や受理集合への変更はありません。
- producer 側の `test_verify_s8c_cross_binding_positive_binds_all_fields` と13 field mutation testsが値束縛の functional consumerとして残ります。
- 新規 unmarked node が 1 件増えるため duration ledger coverage に未収録 node が増えます。
- 新規 test は `s8c-predicate-snapshot` markerと共有 fixtureを持たないため、real-repo canonical group集合は変わりません。

## 裁定・レビューから外れた点 (あれば。無ければ「無し」)

指定 runner が child 起動前に次の ignored output receipt を自動生成しました。禁止に従い、編集・削除していません。

- `output/pegasus-dispatch/49c54da02844d2abd4ed7e085228311a/receipt.json`
- `output/pegasus-dispatch/7bb3ad383a2ff6f5903bba9d4d6d1b6e/receipt.json`

それ以外の逸脱はありません。

## 総括

must-fix の M01-COND survivorと、実 HEADを読む production 正例をテスト側だけで実装しました。状態は「実装済み・pytest 未実走」であり、`closed` とは申告しません。