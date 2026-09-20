## 変更の要約

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py:780)：SHA 定数 2 個のみ更新（+2/−2 行）。
- [orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py:576)：独立 fixture literal、期待 SHA、byte 数を更新（+23/−18 行）。計 41 行は本文と旧長依存の境界入力への追随です。

変更前は実測で rc=1、指定本文 2 本の「whole-file SHA-256 が契約と不一致」のみ。予算・構造検査・helper の意味は変更していません。

## byte 一致の確認

| 本文 | HEAD／現物 bytes | fixture bytes | SHA・本文一致 |
|---|---:|---:|---|
| cleanup command | 6,201 | 6,201 | 全一致 |
| cleanup SKILL | 3,052 | 3,052 | 全一致 |

SHA-256 はそれぞれ以下です。

```text
command: a838dbbccac10c9bb31d14c54357d29941a44ce51efbb1faa5375d9f8a4d264b
skill:   c7a840a8cd718c26513f74d063392bbb738d9616d33429c589631b5e79b15876
```

一時 script で両方について `HEAD == file`、`file SHA == production 定数 == fixture 期待定数`、`fixture == file 本文` を実測しました。script は削除済みです。

## 既存 test 追随の有無

- 予算テスト内の旧長 assert は **2 箇所**とも 6,201 に更新。
- 超過入力の追加文字数を 23→3 に変更し、**6,205 bytes の拒否・期待メッセージを維持**。
- SKILL 側の同種 byte 数 assert はありません。
- 例示された旧本文 7 断片について、fixture 外の test・helper・期待メッセージへの依存はありません。
- `discard_changes: true` は新本文・fixture とも **1 回**。helper は変更していません。

## 実走結果

すべて指定の `pytest.main(...)` 経路で実行しました。

| 対象 | 結果 | rc |
|---|---|---:|
| `test_check_docs.py` 指定 `-k` 焦点走 | 33 passed、550 deselected | 0 |
| `test_check_docs.py` 全件 | 580 passed、3 skipped（302.33 秒） | 0 |
| `test_plain_runner_coverage.py` 全件 | 3 passed | 0 |
| `test_check_subprocess_bytecode_guard.py` 全件 | 6 passed | 0 |
| `python3 tools/check_docs.py` | 最終行 `check_docs: 違反なし` | 0 |
| `git diff --check` | 指摘なし | 0 |

焦点走の nodeid は、共通接頭辞 `orchestrator/tests/test_check_docs.py::` を省略して以下の 33 件です。

```text
test_dev_wave_command_budget_literal_is_exact
test_next_tasks_command_budget_literal_is_exact
test_codex_cleanup_branches_skill_contract_pins_exact_surface
test_cleanup_command_budget_is_pinned_and_enforced
test_command_docs_guard_positive_controls[codex_skill_deleted]
test_command_docs_guard_positive_controls[codex_skill_extra_file]
test_command_docs_guard_positive_controls[codex_skill_name_changed]
test_command_docs_guard_positive_controls[codex_skill_adapter_deleted]
test_command_docs_guard_positive_controls[codex_skill_natural_language_stop_contract_deleted]
test_command_docs_guard_positive_controls[codex_skill_protected_path_authoring_contract_deleted]
test_command_docs_guard_positive_controls[codex_skill_stage9_land_literal_deleted]
test_command_docs_guard_positive_controls[codex_skill_openai_changed]
test_command_docs_guard_positive_controls[codex_skill_land_helper_duplicated]
test_cleanup_skill_one_byte_change_is_rejected
test_cleanup_command_one_byte_change_is_rejected
test_cleanup_skill_additional_h2_is_rejected
test_cleanup_command_closing_hash_h2_is_rejected
test_cleanup_command_leading_space_h2_is_rejected
test_cleanup_command_setext_h2_is_rejected
test_cleanup_command_invalid_backtick_info_is_rejected
test_cleanup_metadata_policy_block_is_rejected
test_cleanup_checker_invocation_line_is_required
test_cleanup_checker_rc_rules_are_required_with_invocation
test_cleanup_checker_negated_invocation_is_rejected
test_cleanup_checker_literals_scattered_across_sections_are_rejected
test_cleanup_address_edge_rejects_split_lines
test_cleanup_address_edge_rejects_id_adjacent_decoy
test_cleanup_address_edge_rejects_non_code_span_path_decoy
test_cleanup_address_edge_rejects_raw_html_block
test_cleanup_address_edge_rejects_link_definition
test_cleanup_address_edge_rejects_frontmatter_decoy
test_cleanup_address_edge_accepts_rewording
test_cleanup_address_edge_accepts_baseline
```

meta-test の実走 nodeid（各ファイルの `orchestrator/tests/` を省略）：

```text
test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted
test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries
test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable
test_check_subprocess_bytecode_guard.py::test_guard_patterns_and_direct_callees
test_check_subprocess_bytecode_guard.py::test_non_python_argv_and_function_boundary
test_check_subprocess_bytecode_guard.py::test_literal_python_argv0_variants
test_check_subprocess_bytecode_guard.py::test_dict_unpack_guard_and_nested_scope_boundary
test_check_subprocess_bytecode_guard.py::test_broken_python_is_indeterminate_even_with_violation
test_check_subprocess_bytecode_guard.py::test_real_repo_clean
```

全件走の skip は既存 growth hold の以下 3 nodeid です（同じ `test_check_docs.py::` 接頭辞）。

```text
test_dev_wave_model_pins_accept_current_docs_contract
test_normative_exact_section_pins_accept_real_repo
test_real_repo_clean
```

失敗・環境起因の赤はありません。

## 波及

指定の `orchestrator/ tools/ hooks/ .codex/ .agents/` を静的検索し、4 識別子の参照は編集対象 2 ファイル内だけでした。所有外参照元はありません。

`docs/failures.md` 等の逐語引用は歴史記録として未変更です。本文・docs・その他の所有外ファイルに差分はありません。

## 未了・懸念

本段の未了はありません。親の全走・変異 matrix・統合 commit は本結果では代替しません。既存 growth hold の 3 件は未実走です。

## 総括

実装・指定検証は完了しました。指定の 2 ファイルだけを未コミットの working tree 差分として残しています。