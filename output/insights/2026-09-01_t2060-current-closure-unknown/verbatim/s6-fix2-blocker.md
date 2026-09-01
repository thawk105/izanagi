## 現行の受理・拒否挙動

- 5 session を manifest から列挙し、session identity が一意に解決でき、SHA-256 が一致した場合だけ受理します。
- rollout 不在だけを skip とし、理由へ失効 label を列挙します。
- 重複は [test_codex_reasoning_ab.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:883)、SHA 不一致は [test_codex_reasoning_ab.py:890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:890) から例外をそのまま伝播し、skip になりません。
- production resolver と pin は変更していません。

## 実装した内容 (file:line)

- 5 pin の manifest 駆動列挙: [test_codex_reasoning_ab.py:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:782)
- session identity、一意性、SHA を検査する一括 resolver: [test_codex_reasoning_ab.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:851)
- label 付き欠落 skip: [test_codex_reasoning_ab.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:899)
- 外部証拠専用 fixture: [test_codex_reasoning_ab.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:917)
- rollout 非依存 consumer 用 portable fixture: [test_codex_reasoning_ab.py:975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:975)
- supervisor/replay consumer 用 verifier 配線: [test_codex_reasoning_ab.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:1039)

変更はこの test file 1 本だけです。

## skip になる node / 実走を維持する node

現在の 5 rollout 全欠落環境で、本修正により skip になるのは次の 6 node です。

- `test_parent_numstat_controls_remain_pinned`
- `test_m2_production_golden_requires_both_routes`
- `test_prompt_replacement_count_zero_expected_and_excess[0]`
- `test_prompt_replacement_count_zero_expected_and_excess[9]`
- `test_prompt_replacement_count_zero_expected_and_excess[10]`
- `test_real_rollout_collector_golden_is_source_bound`

portable fixture に移して、本修正では skip しない 22 node は次のとおりです。

- `test_forbidden_commits_are_unreachable_in_both_cases`
- `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`
- `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`
- `test_m1_snapshot_head_pin_is_independent`
- `test_m3_snapshot_mode_change`
- `test_m3_symbolic_head_is_required`
- `test_m3_ignored_extra_and_missing`
- `test_m3_focus_artifact_directions[POS-focus1.md]`
- `test_m3_focus_artifact_directions[POS-focus2.md]`
- `test_m3_focus_artifact_directions[NEG-focus2.md]`
- `test_snapshot_submodule_object_store_is_recursive`
- `test_pos_neg_submodule_initialization_state_mismatch_is_rejected`
- `test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid`
- `test_git_answer_object_reinjection_is_rejected`
- `test_supervisor_launches_pair_and_scrubs_git_environment`
- `test_agent_sandbox_binds_exclude_attempt_receipt_directory`
- `test_verify_replays_complete_fake_codex_experiment`
- `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers`
- `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`
- `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run`
- `test_attempt_four_is_rejected_before_launch`
- `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation`

## 追加したテスト (node 名と意図)

- `test_historical_rollout_preflight_skips_missing_label`: 欠落時の skip と理由内の `author` label。
- `test_historical_rollout_preflight_duplicate_is_red`: 2 rollout が `RC_SESSION` の赤になること。
- `test_historical_rollout_preflight_sha_mismatch_is_red`: SHA 不一致が `RC_SNAPSHOT` の赤になること。

実体は [test_codex_reasoning_ab.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_codex_reasoning_ab.py:1089) 以降です。

## 実走結果 (nodeid と範囲、赤の内訳)

実装済み・未実走です。

次の 3 nodeid を `tools/run_tests.py` 経由で投入しました。

- `test_historical_rollout_preflight_skips_missing_label`
- `test_historical_rollout_preflight_duplicate_is_red`
- `test_historical_rollout_preflight_sha_mismatch_is_red`

ただし pytest child 起動前に `qstat -Q` が `API EACCTAUTH Unknown user-id` で失敗し、runner は infrastructure rc=16 で停止しました。したがって pytest の赤・緑・skip 実測はありません。生成された dispatch receipt は禁止面へ残さないよう除去済みです。

静的確認は以下を通過しています。

- Python AST parse
- `git diff --check`
- 結合文字 U+0300〜U+036F なし
- 変更 file は対象 test file 1 本だけ

## 波及可能性

- `benchmark_snapshots` の20 consumer function、展開後22 nodeが portable snapshotを使います。
- `_supervisor_pair` と `_full_manifest` は test-local monkeypatch scopeでportable specを渡します。
- 将来、外部 rollout 自体を検査する node を追加する場合は `historical_rollouts` を明示的に要求する必要があります。
- productionの `tools/codex_reasoning_ab.py`、所有外 caller、hold registryには変更がありません。

## 未実走・未確認

- 追加3 nodeのpytest実走
- skip対象6 nodeの実 skip理由
- portable fixture consumer 22 nodeの実走
- 対象module全走および受入全走

いずれもqueue認証復旧後の確認が必要です。

## 総括

案5として、外部証拠依存6 nodeだけを理由付きskipへ限定し、従来巻き添えだった22 nodeをportable fixtureで実走側へ戻しました。既存assertの変更・削除は0件で、`TASK_MANIFEST`、`SESSION_IDS`、`ROLLOUT_SHA256`、golden SHAを含むpin値は一切変更していません。禁止されたdocs、output、hold、本waveの既存実装面、Git操作には変更を残していません。