FIX-1〜FIX-9 をコードとテストへ実装しました。pytest は指示どおり実行していないため、各所見は `partial（静的対応済み・未実走）` と判定します。docs・index・commit・branch は変更していません。

## 所見ごとの対応

| 所見 | 状態 | 根拠・残作業 |
|---|---|---|
| rev1-1 | partial | tail repair のロック区間内、receipt/ftruncate 前に active attempt + truncated tail を拒否。[wal.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:526)、[test_campaign.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:835)。pytest 未実走。 |
| rev1-2 | partial | `build_done`/`verify_done`/`bench_done` のいずれかが start 後にあれば拒否。[wal.py:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1291)、[test_campaign.py:924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:924)。pytest 未実走。 |
| rev1-3 | partial | recovery abort の receiptless/receiptful exact key 集合を共有 validator で強制。[wal.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1028)、[test_artifact_admission.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:331)。pytest 未実走。 |
| rev1-4 | partial | recovery API 内で lock の `build_admission` と渡された policy を照合。[wal.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1243)、[test_campaign.py:943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:943)。pytest 未実走。 |
| rev1-5 | partial | rev2-2 と同じ FIX-6 で検査と射影を分離。[wal.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1118)。pytest・変異未実走。 |
| rev2-1 | partial | backoff/sort/trigger の inner も recovery seam へ変更。[p3_s4_loop.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:708)、[p3_s4_loop_sort.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:238)、[p3_s4_loop_trigger_gating.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:542)。pytest 未実走。 |
| rev2-2 | partial | 事前 `_validate_attempt_topology` の戻り値を射影に使わず、`_project_active_attempts` と suffix 検査を独立化。[wal.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1274)。変異未実走。 |
| rev2-3 | partial | 4 schema key を単独配置する parameterized test を追加。[test_artifact_admission.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:369)。pytest 未実走。 |
| rev2-4 | partial | 外部 fd の `LOCK_EX` 解放まで worker が完了しない決定的テストを追加。[test_campaign.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:1088)。pytest 未実走。 |
| rev2-5 | partial | 過去 signal と別 variant の上限による過剰拒否を admission 到達まで検査。[test_artifact_admission.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:404)、[test_artifact_admission.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:441)。pytest 未実走。 |
| rev2-6 | partial | 親の段7職掌として未対応。権限境界に従い worklog/docs は編集していない。 |

`regressed` と判定した所見はありません。

## 変更ファイルと関数

今回の fix で触れたコードは以下です。

- [wal.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:526): `repair_truncated_tail`
- [wal.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:939): `_validate_attempt_topology`
- [wal.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1118): `_project_active_attempts`
- [wal.py:1141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1141): `_validate_recovery_suffix`
- [wal.py:1219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1219): `recover_interrupted_attempts`
- [ident.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:185): `ensure_resumable_wal`
- [p3_s4_loop.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:663): `run_one_iteration`
- [p3_s4_loop_sort.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:211): `run_one_iteration`
- [p3_s4_loop_trigger_gating.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:519): `_run_one_iteration_resolved`

テストは [test_campaign.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:835)、[test_artifact_admission.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:331)、[test_p3_s4_loop.py:1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop.py:1117)、[test_p3_s4_loop_sort.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_sort.py:383)、[test_p3_s4_loop_trigger_gating.py:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1904) を変更しました。

## 受理・拒否挙動

- FIX-2 の縮小例:
  - 変更前: `build_start(A) → build_done(A)` で crashすると recovery abort を追記できた。
  - 変更後: `build_done` が start 後の当該 attempt record なので、bytes 不変で拒否。
  - `build_start(A)` だけの crash は従来どおり回復する。

- FIX-3 の縮小例:
  - 変更前: recovery abort に `fitness_tps` や `verify` を混ぜても topology/replay/admission が受理した。
  - 変更後: receiptful は `reason + build_attempt_id + receipt SHA`、receiptless は前二者だけ。それ以外を拒否。

- active attempt と truncated tail の併存、lock 無し/pre-policy lock、trigger attempt は追記前に拒否。
- 過去 attempt の signal や別 variant の recovery 上限は、現在の start-only attempt を過剰拒否しない。

## テストと変異対応

| 変異 | 対応 nodeid |
|---|---|
| MU-1 / MU-2 / MU-5 | `orchestrator/tests/test_campaign.py::test_recovery_payload_receipt_matrix_is_exact_and_retryable`、`::test_loop_resume_recovery_aborts_real_pipeline_crash_after_start` |
| MU-3 | `orchestrator/tests/test_campaign.py::test_recovery_fail_closed_after_build_done_but_accepts_start_only`、`::test_recovery_fail_closed_after_verify_or_bench_signal` |
| MU-4 | `orchestrator/tests/test_campaign.py::test_recovery_fail_closed_for_trigger_lock_or_attempt_commitment` |
| MU-6 | `orchestrator/tests/test_campaign.py::test_recovery_exhaustion_is_byte_stable` |
| MU-7 | `orchestrator/tests/test_campaign.py::test_recovery_invalid_topology_and_multiple_active_are_byte_stable` |
| MU-8 | `orchestrator/tests/test_artifact_admission.py::test_historical_signal_does_not_overreject_later_start_only_recovery`、`::test_other_variant_recovery_limit_does_not_overreject_first_recovery` |
| MU-9 | `orchestrator/tests/test_campaign.py::test_resumable_wal_rejects_truncated_tail_with_active_attempt_before_repair` |
| MU-10 | `orchestrator/tests/test_artifact_admission.py::test_recovery_abort_extra_keys_are_rejected_by_replay_and_admission[build-admission\|fitness-tps\|verify]` |
| MU-11 | `orchestrator/tests/test_campaign.py::test_recovery_api_requires_matching_post_policy_lock_without_mutating_wal` |
| MU-12 | `orchestrator/tests/test_p3_s4_loop.py::test_inner_run_recovers_reject_start_before_writing_retry_start`、sort 同名 node、`test_p3_s4_loop_trigger_gating.py::test_inner_run_reject_start_crash_fails_before_second_start` |

追加で、FIX-7 は `test_each_attempt_schema_key_independently_enables_strict_recovery_validation[build-attempt-id|build-admission|receipt-sha256|trigger-commitment]`、FIX-8 は `test_recovery_waits_for_external_exclusive_wal_lock` が担います。これらは更新済み事前登録上、独立した MU 番号を持ちません。

## FIX-6

分離できました。事前 topology 検査の戻り値は捨て、active attempt は `_project_active_attempts` で独立射影し、生成 suffix は `_validate_recovery_suffix` でのみ検査します。

MU-7 で事前 `_validate_attempt_topology` 呼び出しだけを除くと、歴史部分に receipt SHA 違反がある fixtureでも現在の active attempt を射影でき、append まで到達します。未定義変数や prospective 全履歴再検査による別理由の赤にはならないため、再照準はしていません。

## 波及可能性

- 所有外 caller: `loop.py`、`screening_driver.py`、`guided.py`、`s1_direct_comparison.py` の `ensure_resumable_wal` 呼び出し。
- inner caller: 各 `drive_iteration`、backoff/sort fixture CLI、`test_p3_exploration_namespace.py`、`test_p3_build_authority_cli.py`。
- 共有 fixture: `_admission_aware_layout`、`_new_schema_campaign`、各 `_tmp_layout`、`_mock_pipeline`。
- consumer: `wal.replay`、`artifact_admission`、critic digest、Layer3 report、autonomous trial completeness。
- 既存テストで赤を予想する nodeidはありません。予想外の赤は回帰扱いです。

静的検査は `git diff --check`、対象10ファイルの `py_compile`、`tools/check_codex_agents.py`、`tools/check_docs.py` が成功しました。pytest・変異 harness・受入全走は未実走です。

## 総括

- FIX-1〜FIX-9 をコードとテストへ実装した。
- FIX-2 は回復対象を `build_start` だけの attempt に縮小した。
- FIX-3 は recovery abort の exact key 集合を受理側でも強制した。
- FIX-6 は事前検査・射影・suffix 検査を分離し、MU-7 を単一理由化した。
- p3 三系統の inner bypass、lock 検査、schema/lock/過剰拒否テストを補強した。
- docs、git index、commit、branch は変更していない。
- 静的検査は成功した。
- pytest・変異・受入全走は未実走であり、緑は主張しない。