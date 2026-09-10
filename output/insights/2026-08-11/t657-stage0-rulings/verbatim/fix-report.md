LUNA-03〜05 / SOL6-01 の fix を実装しました。commit・docs・fixture の変更はありません。

- [`_read_design`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-rulings/orchestrator/tests/calibration_freeze_authority_contract.py:273) で HTML comment を非貪欲に除去。
- 未閉鎖の `<!--` は `ContractError` で fail-closed。
- 指定名の負例 [`test_design_literals_hidden_in_html_comment_are_not_authoritative`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-rulings/orchestrator/tests/test_calibration_freeze_authority_contract.py:664) を追加。
- 既存 assert、診断文字列、件数、SHA pin は変更していません。

Docstring の分類：

- 狭める
  - `test_design_literals_hidden_in_html_comment_are_not_authoritative`
- 中立（snapshot pin）
  - `test_adjudicated_ruling_and_gate_projection_is_exact`
  - `test_required_gate_entries_have_independent_module_sha_pin`
- 中立（期待値更新・再照準）
  - `test_real_repository_contract_is_consistent_but_incomplete`
  - `test_current_repository_is_rejected_as_stage0_incomplete`
  - `test_required_gate_removed_is_rejected`
  - `test_required_gate_owner_changed_is_rejected`
  - `test_required_gate_resolved_without_evidence_is_rejected`
  - `test_not_applicable_outside_applicability_rule_is_rejected`
  - `test_resolved_ruling_without_design_selection_enum_is_rejected`

`_read_design` の変更は既存抽出器へ次のように波及します。

- `_extract_design_row_ids`: comment 内の §7.2 / §11 row ID を無視。
- `_extract_ruling_ids`: comment 内の §8.1 ruling ID を無視。
- `_extract_design_selection_enums`: comment 内の旧 selection literal を無視。
- `_fixture_assignment_gate_id_from_design`: comment 内の旧 §10 段宣言を無視。
- いずれも未閉鎖 comment があれば抽出前に拒否。

検査結果：

- `git diff --check`: 成功
- Python AST 構文検査: 成功
- `tools/check_codex_agents.py`: 成功
- `tools/check_docs.py`: 成功
- 対象 pytest と collect-only: `qstat -Q` preflight の `rc=16` で本体未起動

## 総括

HTML comment 内の旧設計 literal を権威として扱う経路を `_read_design` で閉鎖しました。  
指定の負例 node を追加し、docstring を snapshot・中立・縮小へ正しく分類しました。  
fixture、固定 SHA、段 0 `incomplete`、先送り 3 件には触れていません。  
静的検査は成功、pytest は dispatch infrastructure failure のため実装済み・未実走です。