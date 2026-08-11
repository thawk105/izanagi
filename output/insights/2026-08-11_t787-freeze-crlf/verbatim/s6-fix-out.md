段 6 fix を実装しました。今回の追加は [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:764) のみで、production・docs・output・発効層・契約 JSON・既存期待値は変更していません。

| 所見 | 状態 | 追加内容 |
|---|---|---|
| R1 | partial（実装済み・未実走） | `prepare_revision` の初回／既存 freeze、CR/LF-bound g1→clean g2 履歴 |
| R2 | partial（実装済み・未実走） | TAB・BS・FF・U+0001 の exact-hash 受理正例 |
| R3 | partial（実装済み・未実走） | 混在 CR/LF 文書順、root list、深さ10超の交互入れ子 |

追加 test/node:

- `test_prepare_revision_rejects_crlf_path_contract_before_create[cr|lf]`
- `test_prepare_revision_rejects_crlf_path_contract_with_existing_freeze[cr|lf]`
- `test_validate_condition_freeze_at_rejects_legacy_crlf_ancestor_under_clean_revision[cr|lf]`
- `test_evidence_contract_hash_accepts_values_outside_forbidden_boundary[path-tab|path-bs|path-ff|path-u0001]`
- `test_evidence_contract_hash_preserves_first_mixed_crlf_pointer_in_document_order[lf-before-cr|cr-before-lf]`
- `test_evidence_contract_hash_rejects_root_list_path[cr|lf]`
- `test_evidence_contract_hash_rejects_deep_alternating_dict_list_path[cr|lf]`

確認結果:

- `git diff --check`: rc=0
- Python AST parse: 成功
- 4 hash literal: 標準ライブラリのみで独立計算・照合
- 深い JSON fixtureと exact pointer: 静的確認済み
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 焦点テストは `tools/run_tests.py` 経由で起動したものの、Pegasus の `qstat -Q` preflight failureで rc=16。テスト node は未実走です。

## 総括

- R1〜R3 の要求テストを実装。
- production 追加変更なし。
- 既存期待値の変更・緩和・skip・削除なし。
- 禁止対象への変更なし。
- 静的検査は成功。
- 状態は全件 partial（実装済み・未実走）。
