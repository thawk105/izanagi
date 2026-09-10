実装は完了しましたが、Pegasus の dispatch 障害によりテストは未実走です。docs 編集・commit は行っておらず、変更は指定された 2 ファイルだけです。

変更ファイル:

- [tools/codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:364)
- [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:68)

### 裁定 §1、§2 の実装内容

- P1: receipt schema を変更せず、一意な `launcher-diagnostics.<pid>.<uuid4hex>.json` sidecar を追加。
- P2: 退避を常時有効化。root は `<repo>/output/runs/pytest-launcher-failures` 固定で、環境変数上書きは未実装。
- P3: receipt の `limit_trigger` は不変。sidecar の `control_limit_trigger` と `conditions_met` を分離。

§2 must-fix 14 行への対応:

- A1: `tryfirst=True` を固定し、実 pytest 子プロセスで未処理 mismatch を起こす live wiring test を追加。
- A3: 当該 module の全未処理 call-phase failure を退避。例外型による限定なし。
- A4: TimeoutExpired の例外連鎖を検出し、`source_live=true`、`snapshot_consistency="incomplete"` を記録。
- A5: 監視ループでは既存 `now_ns` と in-memory 更新だけを使用。sidecar は全 late gate と receipt 公開後に書き、fsync しない。
- A6: receipt を自分で公開した run のみ `sealed`、競合敗者は `foreign`。
- A7+B9: source/destination の祖先関係拒否、4096 files・256 MiB 上限、省略理由、コピー例外隔離、`.complete` を実装。
- A9: 正常時 false、閾値未満、exact-limit、site 別条件の負例を追加。
- A10: forced stopから `_terminate`、residual reason、sidecar までの統合検査を追加。1 引数 lambda consumer も更新。
- B2 部分: launcher 主体フラグ、実際に送信した signal、job/attempt elapsed の送信時刻を記録。
- B5: malformed `/proc/<pid>/stat` を診断へ記録し、count は従来どおり維持。
- B7: sidecar 不在時は archive metadata に `diagnostics_present=false` と理由を記録。
- B8+B15: receipt の exact bytes を保存し、絶対 path の対応は `path-map.json` へ記録。
- B11: run 直下の `index.jsonl` へ bundle ごとに 1 行を排他 append。
- A11: T-190/F57 は閉じていません。「次回再発を観測可能にした」段階に留めています。

裁定 §2 の scope 外 7 項目は実装していません。setup/KeyboardInterrupt/xdist crash salvage、外部資源観測、`worker.py` 計装、dispatch allowlist、reader CLI、retention/GC、env transport は未変更です。

### 新設・改名 nodeid

改名・分割:

- `orchestrator/tests/test_codex_worker_launch.py::test_group_member_count_reports_identity_missing_source`
- `...::test_group_member_count_reports_scandir_failure_source`
- `...::test_group_member_count_reports_stat_read_failure_source`
- `...::test_unknown_residual_source_propagates_without_verifying_normal_reap`

新設:

- `...::test_group_member_count_reports_stat_parse_failure_source`
- `...::test_group_member_count_records_malformed_without_changing_count`
- `...::test_unknown_residual_source_propagates_through_terminate`
- `...::test_evidence_forced_stop_propagates_unknown_residual_to_sidecar`
- `...::test_launcher_diagnostics_phase_durations_use_distinct_boundaries`
- `...::test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary`
- `...::test_launcher_diagnostics_records_all_conditions_and_site_values`
- `...::test_launcher_diagnostics_keeps_control_trigger_separate_from_all_conditions`
- `...::test_launcher_diagnostics_write_failure_does_not_change_control_result`
- `...::test_launcher_diagnostics_sidecar_write_does_not_fsync`
- `...::test_launcher_diagnostics_sidecar_is_outside_receipt_schema`
- `...::test_launcher_failure_artifact_reporter_hook_is_tryfirst`
- `...::test_launcher_failure_artifact_reporter_archives_unhandled_call_failure`
- `...::test_launcher_failure_artifact_reporter_ignores_handled_failure`
- `...::test_launcher_failure_artifact_paths_are_collision_free`
- `...::test_launcher_failure_artifact_copy_error_does_not_mask_failure`
- `...::test_launcher_failure_artifact_limits_record_omission_reasons`
- `...::test_launcher_failure_artifact_byte_limit_records_omission_reason`
- `...::test_launcher_failure_artifact_special_file_is_not_opened`
- `...::test_launcher_failure_artifact_rejects_ancestor_destination`
- `...::test_launcher_failure_artifact_marks_timeout_source_incomplete`
- `...::test_launcher_failure_artifact_live_wiring_probe`
- `...::test_launcher_failure_artifact_reporter_live_wiring`

### M01〜M14、P01 の検出 node

- M01: `test_positive_p3_exact_limit_natural_exit_is_accepted`
- M02: `test_launcher_diagnostics_limit_conditions_negative_and_exact_boundary`
- M03: `test_launcher_diagnostics_phase_durations_use_distinct_boundaries`
- M04: `test_evidence_forced_stop_propagates_unknown_residual_to_sidecar`
- M05: `test_launcher_failure_artifact_reporter_live_wiring`
- M06: `test_launcher_failure_artifact_reporter_archives_unhandled_call_failure`
- M07: `test_launcher_failure_artifact_paths_are_collision_free`
- M08: `test_complete_receipt_publication_is_atomic_create_only_at_run_callsite`
- M09: `test_launcher_failure_artifact_reporter_archives_unhandled_call_failure`
- M10: `test_launcher_failure_artifact_copy_error_does_not_mask_failure`
- M11: `test_rollout_missing_after_grace_is_stopped_and_not_accepted`
- M12: `test_group_member_count_records_malformed_without_changing_count`
- M13: `test_launcher_failure_artifact_reporter_archives_unhandled_call_failure`
- M14: `test_positive_p3_exact_limit_natural_exit_is_accepted`
- P01: `test_launcher_diagnostics_write_failure_does_not_change_control_result` は sidecar writer の `OSError` 下でも通るべき正例。

### 実走結果

実走 nodeidは 0 件です。

2 回とも指定の `tools/run_tests.py --force-dispatch` を使用しましたが、テスト process 起動前に失敗しました。

- 1 回目: runner rc=16、`qstat -Q preflight rc=1`
- 2 回目: launcher焦点集合と `test_plain_runner_coverage.py` の3 meta-testを指定。runner rc=16、同じ `qstat` failure
- queue state: ENA/STS/待ち数/実行数すべて観測不能
- login nodeは `pegasus02`。指示どおり local pytestへ切り替えていません。

実施済みの静的検査:

- 両 Python fileの AST parse: 成功
- `git diff --check`: 成功
- U+0300〜U+036F: 0 件
- 編集対象: 指定された2ファイルのみ

したがって、テスト上の既知の赤はありませんが、緑も申告しません。残件は「実装済み・未実走」です。

### 波及可能性

- `tools/dev_wave_codex.py`: CLI argv、receipt path、schema は不変。artifact dir にsidecarが増えるだけです。
- `orchestrator/tests/test_dev_wave_codex.py`: artifact directory の存在・modeを検査しますが、内容の閉集合検査はありません。
- receipt checker群: sidecarを読まず、receiptのclosed schemaとrcは不変です。
- `_group_member_count` の monkeypatch consumer: optional callback keywordを受けられる形へ明示更新済み。
- test module全体: autouse fixtureにより各testで `tmp_path` とplugin登録が増えます。保存は未処理call failure時だけです。
- xdist/shared FS: worker別directory、原子的な一意leaf、`flock`付き `index.jsonl` appendを使用します。
- 旧nodeid参照は履歴的な `output/insights` にのみ存在し、active consumerには見つかりませんでした。
- 新規test fileはないため file集合は不変です。関連する `test_plain_runner_coverage` は実走対象へ含めましたが、dispatch障害で未実行です。

### 受理・拒否挙動

変更前後とも、attemptの受理条件は次の全成立です。

- launcher内部failureでない
- `limit_trigger is None`
- child rc=0
- validator rc=0
- evidence/meteringがcomplete
- residual=0
- termination verified

`_LIMIT_REASONS`、natural/seal/final gateの `>`、live/retry gateの `>=`、既存優先順位、`_writer_truth`、receipt field集合、checker rc、fixture予算、parser既定は変更していません。

追加clock取得による実時間上の境界完全同一性は裁定 A5 のとおり保証しませんが、値・述語・制御分岐・receipt公開順の意図的変更はありません。

## 総括

段4裁定のP1〜P3とmust-fix 14行を、指定2ファイル内へ実装しました。receiptと受理集合は維持し、独立sidecarと失敗bundleで次回再発を帰属可能にしています。T-190/F57はopenのままです。テストはPegasus dispatch infrastructure failureにより未実走で、親による焦点走・全走・mutation確認が必要です。