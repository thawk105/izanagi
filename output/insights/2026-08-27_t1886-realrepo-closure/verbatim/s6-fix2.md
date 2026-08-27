## 総括

共有 fixture 閉包の候補を session / module scope に限定しました。  
function scope は C3 の disjoint・mode 互換性検査に残しています。  
焦点テストは dispatch rc=16、child 未起動のため、実装済み・未実走です。  
commit、add、stash、branch 操作は行っておらず、`closed` とは申告しません。

## 修正内容

[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_real_repo_serialization.py:1311) の `_assert_fixture_closure_complete` だけを修正しました。

- closure 候補を `[session]` / `[module]` に限定。
- function scope は consumer ごとに実体を作り直し、consumer 間で共有しない旨をコメント化。
- `assert not missing` は維持。
- collection report 自体は function fixture を保持するため、[disjoint・mode 互換性検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_real_repo_serialization.py:1206)からは除外していません。

受理: function-scope `repository_candidate_commit[function]` の単独 consumer `test_repository_candidate_uses_real_s8c_budget_module` は共有閉包外として通ります。  
拒否: module/session fixture の consumer が canonical node 集合から一つでも外れれば、従来どおり `assert not missing` で拒否します。

module fixture の負例は既存の `real_known_axes_doc` と `benchmark_snapshots` の consumer を一件ずつ canonical 集合から除く注入で維持されています。

## 見逃し形と代替検査

`repository_candidate_commit[function]` に未知の第二 consumerを追加しても、共有閉包検査は検出しません。これは [_assert_long_lived_fixture_group_contract](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_real_repo_serialization.py:1206) の独立 consumer literal と live collection の exact 比較で捕捉されます。

## 検査結果

実走を試みた nodeid:

`orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

`python3 tools/run_tests.py` 経由で実行しましたが、`qstat -Q preflight rc=1`、dispatch rc=16、`child_started=false` でした。pytest 実行数は 0 です。

静的には以下を通過しました。

- `python3 -m py_compile orchestrator/tests/test_real_repo_serialization.py`
- `git diff --check`
- 対象ファイルの U+0300〜U+036F 不在
- 編集対象は既存差分上の同テストファイルのみ

## 静的な波及可能性

所有外 callerはありません。本 helper の caller は同じ collection テスト内の正走、module fixture consumer 欠落負例、偽 report、空 closure controlだけです。

明示的な共有 fixture と consumer test は次のとおりです。

- `real_known_axes_doc[module]`: `test_generate_builds_registered_cells_comparisons_and_schedule`、`test_generate_refuses_existing_freeze`、`test_verify_rejects_one_byte_freeze_tamper`、`test_verify_rejects_one_byte_workload_flag_tamper`、`test_verify_rejects_stats_implementation_tamper`、`test_verify_rejects_known_axes_material_tamper`、`test_schedule_is_balanced_and_reproducible`、`test_recorded_ccbench_pin_hold_and_release_positive_control`、`test_s1b_pairing_rejects_mismatched_flags`、`test_build_document_rejects_tampered_known_axes_semantics`、`test_receipt_exists_but_measurement_verify_stays_legacy_strict`
- `benchmark_snapshots[module]`: 静的に21 consumer。波及はこの fixture の consumer 閉包に限られ、fixture本体や各 consumerの実行動作は変更していません。
- function fixture側: `repository_candidate_commit[function]` と `test_repository_candidate_uses_real_s8c_budget_module`。共有閉包からのみ除外され、独立 literal/live、resource disjoint、同時生存mode検査には引き続き含まれます。