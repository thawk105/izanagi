実装済み・実走済みです。所有外 file、親配置の `.claude/commands/next-tasks.md`、staged gitlink 削除には触れていません。

### 実装済み・実走済み

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py:283)

  - `COMMAND_LIMITS`: `TextLimit(27_100, 100)`
  - `COMMAND_INTERFACES`: frontmatter 2 key、`arguments_count=0`

- [orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/orchestrator/tests/test_check_docs.py:2528)

  - `_build_min_repo` に合成 `next-tasks.md` を追加
  - `test_next_tasks_command_budget_literal_is_exact` を追加
  - 自走 harness の自動列挙に入り、最終走で PASS

- [known-violation JSON](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/known_violations/c12e25078ad155486c19eae633fde14e59753272--missing-codex-author--e71feba76c46009a79736502615fb83ee633e1f59fe27b71f07421f28289904b.json:1)

  - digest: `e71feba76c46009a79736502615fb83ee633e1f59fe27b71f07421f28289904b`
  - loader 検証 rc=0、新 file 名の列挙を確認
  - canonical JSON と file 名 SHA-256 の一致を確認

実走結果:

- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- 新規 test 単独正常系: rc=0
- `git diff --check`: rc=0
- tracked diff: 2 files、30 insertions
- M1: `COMMAND_LIMITS` 登録削除で新規 test は rc=1、`KeyError`
- M2: 予算を `27_101` に変更すると新規 test は rc=1、固定値 assertion で失敗
- M1/M2 は復元済み

自走 harness は素の指定 commandでは growth-hold により test 前に拒否されました。明示ユーザー指示用の解除値を付けて実走した結果は `461 passed, 42 failed`、新規 test は PASS、通常の `FAIL` は 0 件でした。42 件はすべて manual runner が引数付き test に fixture/parameter を渡さない既存 `TypeError` です。

失敗 nodeidの共通 prefix は `orchestrator/tests/test_check_docs.py::` です。

```text
test_archive_malformed_filename_is_violation
test_backlog_guard_carry_candidate_parse_break_is_positive_control
test_backlog_guard_carry_findings_are_sampled_without_early_stop
test_backlog_guard_carry_index_failures_count_every_occurrence
test_backlog_guard_carry_reference_existing_in_current_is_clean
test_backlog_guard_carry_reference_population_floor_rejects_shrink
test_backlog_guard_carry_references_are_streamed
test_backlog_guard_carry_target_index_states_are_distinct
test_backlog_guard_dangling_carry_reference_is_violation
test_backlog_guard_entry_universe_and_index_must_match
test_backlog_guard_incomplete_numbered_archive_stops_carry_validation
test_backlog_guard_non_carry_parenthetical_item_is_clean
test_backlog_guard_same_target_and_id_from_new_source_is_violation
test_backlog_guard_unnumbered_archive_carry_is_out_of_scope
test_dev_wave_dispatch_conditionality_retyping_is_rejected
test_dev_wave_dispatch_rejects_bare_path
test_dev_wave_dispatch_rejects_unchecked_text_between_path_and_section
test_dev_wave_dispatch_route_accepts_separator_outside_candidate
test_dev_wave_dispatch_route_rejects_separator_in_normative_candidate
test_dev_wave_dispatch_route_requires_visible_top_level_full_match
test_dev_wave_layer_budget_rejects_plus_one
test_dev_wave_layer_slicing_ignores_fenced_heading
test_dev_wave_shared_reference_edges_are_typed
test_non_attributable_landing_contract_mutations_have_one_finding
test_numbered_archive_readme_requires_range_syntax
test_provenance_dispatch_condition_literal_change_is_rejected
test_provenance_dispatch_pair_multiple_key_ownership_is_rejected
test_provenance_dispatch_table_structure_is_exact
test_provenance_member_limit_accepts_exact_boundary
test_provenance_member_limit_rejects_plus_one
test_provenance_registry_three_faces_asymmetry_is_rejected
test_provenance_required_h2_multiplicity_is_rejected
test_r33_role_contract_generation_round_allocation_mismatch_fails
test_read_text_cache_invalidates_ctime_only_change
test_read_text_cache_invalidates_inode_only_replacement
test_read_text_cache_invalidates_mtime_only_change
test_read_text_cache_invalidates_replaced_file_identity
test_read_text_cache_invalidates_revoked_read_permission
test_read_text_cache_keeps_newline_modes_distinct
test_read_text_cache_replays_failure_for_each_caller
test_read_text_cache_uses_one_open_across_newline_modes
test_read_text_cache_uses_one_physical_open_per_main
```

### 実装済み・未実走

- `python3 tools/check_ai_provenance.py` の全史監査は、指示どおり親へ委ねて未実走です。
- `tools/run_tests.py` と pytest は禁止境界に従い未実走です。
- pytest fixture/parameter を伴う consumer の正規 runner 経由確認は未実走です。

### 静的な波及範囲

- `check_docs.py` の全 caller は、今後 `next-tasks.md` の存在、byte・行長、frontmatter、`$ARGUMENTS` 不使用、自己改善文書への到達性を検査します。
- `_build_min_repo` を共有する同 file 内の全 test は、4 件目の登録 command を含む合成 repo を受け取ります。
- command guard の既存 consumer test は、新登録 file の欠落や不正から余計な finding を受けなくなります。
- provenance checker は新 JSON を既知違反として読みますが、履歴全体での解消確認は親の監査待ちです。

scope 前は、`next-tasks.md` が在る場合「command byte予算が未登録」で赤、無い場合はこの観点では緑でした。登録後は、現物が契約どおりなら緑、欠落・超過・interface 不一致なら赤になります。

## 総括

変更 file は `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`、known-violation JSON の3件です。追加 nodeid は `orchestrator/tests/test_check_docs.py::test_next_tasks_command_budget_literal_is_exact`。checker rc=0、新規 test rc=0、self-run は 461 passed / 42 existing TypeError failures。M1/M2 は各 rc=1 を実測して復元済みです。未実走は全史 provenance、`tools/run_tests.py`、pytest 経由の正規 consumer testです。