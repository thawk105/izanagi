## 変更の要約

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py:780)：SHA 定数 2 個のみ更新（+2/−2 行）。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py:576)：独立 literal 3 行、期待 SHA 2 行、bytes assert 2 行、padding 1 行を更新（+8/−8 行）。差分計 16 行は指定された変更のみです。

変更前の検査は rc=1、whole-file SHA 不一致 2 件のみでした。予算上限・検査ロジック・helper・6,205 bytes の拒否期待値は不変です。

## byte 一致の確認

| 対象 | HEAD／現物／fixture bytes | 本文・SHA |
|---|---:|---|
| command | 6,200 | 全一致 |
| overlay | 3,060 | 全一致 |

```text
command: 664815dfb3457e0ed8e0de443edeb0c48c75f76bfc382d2993fa17f61de9f09c
overlay: 3cf0344df609115811d30a30ffe875cca1756e5a5a9aaa2c26e3c9f278269930
```

一時 script で `HEAD == 現物`、`現物 SHA == production 定数 == fixture 期待定数`、`fixture == 本文` を確認。script は削除済みです。

## 既存 test 追随の有無

- 指定の旧本文断片への依存は、更新した fixture 3 行以外には**ありません**。
- SKILL の同種 bytes assert はありません。
- `discard_changes: true` は本文・fixture とも **1 回**。helper は不変です。
- テストの反転・緩和・skip 追加・削除はありません。

## 実走結果

指定の `PYTHONPATH=. python3 -c "...pytest.main(...)"` 経路で実行しました。

| 対象 | 結果 | rc |
|---|---|---:|
| 指定 `-k` 焦点走 | 33 passed、550 deselected | 0 |
| `test_check_docs.py` 全件 | 580 passed、3 skipped（327.21 秒） | 0 |
| `test_plain_runner_coverage.py` | 3 passed | 0 |
| `test_check_subprocess_bytecode_guard.py` | 6 passed | 0 |
| `python3 tools/check_docs.py` | `check_docs: 違反なし` | 0 |
| `git diff --check` | 指摘なし | 0 |

焦点走 nodeid（接頭辞 `orchestrator/tests/test_check_docs.py::` を省略）：

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

meta-test nodeid（接頭辞 `orchestrator/tests/` を省略）：

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

全件走の既存 growth hold による skip（`test_check_docs.py::` 以下）：

```text
test_dev_wave_model_pins_accept_current_docs_contract
test_normative_exact_section_pins_accept_real_repo
test_real_repo_clean
```

## 波及

指定の `orchestrator/ tools/ hooks/ .codex/ .agents/` を検索し、4 識別子の参照は編集対象 2 ファイル内だけでした。所有外参照元はありません。

本文・overlay・`docs/failures.md` 等の歴史記録は未変更です。

## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| 1：must-fix | **closed（本文・pin 整合）** | [fixture:693](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py:693) に非 dir entry 数の不足時停止を反映。本文との byte 一致・検査成功を確認。 |
| 2：nit | **partial** | [command:69](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.claude/commands/cleanup-branches.md:69) の確認義務は維持。**pin 側の作業なし**。親側の対応表・worklog の記録対応は本段では未確認。 |

## 未了・懸念

pin 側の未了はありません。既存 hold の 3 テストは未実走です。本結果は親の全走・変異 matrix・記録対応を代替しません。

## 総括

指定 2 ファイルの追随と検証を完了しました。差分は未コミットの working tree に残しています。