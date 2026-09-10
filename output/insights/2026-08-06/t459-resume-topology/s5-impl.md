実装を完了し、`orchestrator/` 配下のコード・テストだけに差分を残しました。docs、git add/commit、branch 操作、pytest 実行は行っていません。

## 変更箇所

- [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/model.py:105)
  - `INCOMPLETE_ATTEMPT_RECOVERY_REASON`
  - `RETRYABLE_ABORT_REASONS` への追加
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:123)
  - `InterruptedAttemptRecoveryError`
  - locked-fd scan、active attempt 射影、exact abort record 生成、locked append
  - `recover_interrupted_attempts`（[1140行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1140)）
- [ident.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/ident.py:185)
  - `ensure_resumable_wal`: identity → tail repair → recovery
  - `ensure_resumable_attempts`: tail repair を伴わない identity + recovery seam
- public entry 配線
  - [s6_sort_sweep.run_sweep](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s6_sort_sweep.py:277)
  - [s8a_trigger_sweep.run_sweep](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/s8a_trigger_sweep.py:379)
  - [p3_s4_loop.drive_iteration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:826)
  - [p3_s4_loop_sort.drive_iteration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:322)
  - [p3_s4_loop_trigger_gating.drive_iteration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:714)

`wal._validate_attempt_topology`、`pipeline.evaluate`、`artifact_admission` 本体、`wal.replay` には差分がありません。

## 受理・拒否挙動

|入力|変更前|変更後|
|---|---|---|
|非 trigger、verify/bench 前の未終端 attempt|再評価が二つ目の start を書き、次 replay/admission で拒否|旧 attempt を exact recovery-abort で閉じ、新 attempt と admission を受理|
|verify/bench 後、trigger、上限到達、既存 topology 違反、同一 variant 複数 active|入口では停止せず後続書き込みへ進み得た|`condition / variant / attempt_id(s)` 付き専用例外。WAL は byte 不変|
|attempt-schema key が全くない pseudo-WAL|通常 replay 対象|recovery seam は no-op、byte 不変|
|複数 variant が各一つ active|各 variant の再評価で topology を壊し得た|一つの `LOCK_EX` 区間で全 active を prospective 検査後に終端|

受理集合の拡大例は「receiptful start 後、signal 前に crash した非 trigger campaign」です。縮小例は「`verify_done` 後に crash した attempt」で、現在は再評価へ進まず `signal-after-start` で停止します。

## 新設テストと MU 対応

- MU-1 / MU-2 / MU-5
  - `orchestrator/tests/test_campaign.py::test_recovery_payload_receipt_matrix_is_exact_and_retryable`
  - receiptless/receiptful の exact payload、attempt ID、SHA、retryable を検査。旧実装には recovery suffix がなく赤です。
- MU-3
  - `orchestrator/tests/test_campaign.py::test_recovery_fail_closed_after_verify_or_bench_signal`
  - guard を外すと abort が追記され、byte 不変・専用拒否が崩れます。
- MU-4
  - `orchestrator/tests/test_campaign.py::test_recovery_fail_closed_for_trigger_lock_or_attempt_commitment`
  - `orchestrator/tests/test_s8a_trigger_sweep.py::test_public_sweep_trigger_crash_tail_fails_before_quarantine_write`
  - `orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_drive_trigger_crash_tail_fails_before_stop_checkpoint_and_provenance`
  - guard を外すと trigger WAL、checkpoint/provenance 側へ進むため赤です。
- MU-6
  - `orchestrator/tests/test_campaign.py::test_recovery_exhaustion_is_byte_stable`
  - 3 回回復済み variant に第4の abort が追加されれば赤です。
- MU-7
  - `orchestrator/tests/test_campaign.py::test_recovery_invalid_topology_and_multiple_active_are_byte_stable`
  - 既存違反への追記、または複数 active の修復を試みると byte 不変保証が赤です。
- MU-8
  - `orchestrator/tests/test_campaign.py::test_loop_resume_recovery_aborts_real_pipeline_crash_after_start`
  - 実 `pipeline.evaluate` / `wal.log` で `BaseException` crash を作成。旧実装では [pipeline.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:709) の二つ目の start が [wal.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:942) で拒否されます。修正後は `start(A) → recovery abort(A) → start(B) → commit(B)` になります。
  - `orchestrator/tests/test_artifact_admission.py::test_recovered_attempt_then_retry_is_admitted_without_read_mutation`
  - admission 直呼びが回復済み campaign を受理し、read 中に WAL を変えないことを固定します。
  - `orchestrator/tests/test_s6_sort_sweep.py::test_public_sweep_recovers_real_wal_start_before_quarantine_write`
  - `orchestrator/tests/test_p3_s4_loop.py::test_drive_iteration_recovers_real_wal_start_before_entry_stop`
  - `orchestrator/tests/test_p3_s4_loop_sort.py::test_drive_iteration_recovers_real_wal_start_before_entry_stop`

追加の原子性・B7 テスト:

- `orchestrator/tests/test_campaign.py::test_concurrent_recovery_appends_one_terminal_abort`
- `orchestrator/tests/test_campaign.py::test_recovery_schema_detection_noops_only_without_attempt_keys`

## 波及可能性

所有外で新 side effect を受ける既存 caller:

- `loop.run_campaign`
- `screening_driver.prepare_screening_campaign` / `evaluate_candidate`
- `s1_direct_comparison._ensure_campaign`
- `guided.cmd_evaluate`

guided の attempt-schema key 無し pseudo-WAL は B7 no-op です。qualification の別 event sink は対象外です。

共有 fixture は [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:66) の `_BUILD_CONTEXT`、attempt helper、`_mock_pipeline` と、[test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:153) の `_new_schema_campaign` を利用しています。

admission 経由 consumer の波及候補は critic digest、Layer3、p3 loop/red/sort、s6/s8 report、campaign replay、autonomous completeness です。共有 validator は変更していないため、回復済みの正規列だけが新たに到達します。

既存テストの期待値は削除・変更していません。静的には既存テストで赤を予想していません。予想外の赤は回帰として扱う必要があります。

## 検査

- `git diff --check`: 成功
- 変更したコード・テスト15ファイルの `python3 -m py_compile`: 成功
- AST による変更テスト名の重複検査: 成功
- pytest: 環境制約に従い未実走
- git add / commit: 未実施

実装できなかった項目はありません。

## 総括

- identity 照合済み seam で未終端 attempt を exact recovery-abort にしました。
- scan・事前検査・prospective 検査・append は同一 `LOCK_EX` 区間です。
- 5つの禁止条件は byte 不変の専用例外で停止します。
- `wal.replay`、topology validator、pipeline start emit、artifact admission 本体は無変更です。
- owner lease 不在による生存 evaluator との競合は scope 外の残リスクです。
- 静的検査済みですが、pytest は未実走であり緑は主張しません。