## 読んだ資料

指定された以下の資料を全文確認しました。

- `s4-adjudication.md`
- `s5-author.md`
- `s6-reviewA.md`
- `s6-reviewB.md`
- `orchestrator/campaign/p3_s4_loop.py`
- `orchestrator/campaign/condition_meaning_gate.py`

あわせて既存差分、対象の2テストファイル、関連 caller・consumer を静的確認しました。

## 所見対応表 (closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 原子的な証拠公開 | partial | 実装・破壊検知テスト済み。pytest は child 未起動のため未実走 |
| F2 診断整形による原失敗の置換 | partial | 固定 fallback と reason code 保持テストを追加。未実走 |
| F3 切詰め argv の衝突 | partial | 全文 SHA-256 を追加し、同長・同 prefix の識別テストを追加。未実走 |
| regressed | なし | 静的確認上、受理集合・reason code・rc・green 経路は変更なし |

`except Exception` は `BaseException` に変更していません。

## 実装した内容 (file:line)

- [p3_s4_loop.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:378)

  - 同一 directory の一意な一時名へ書込み。
  - write → flush → file fsync → `os.replace` → directory fsync の順で公開。
  - 同じ digest の再試行を冪等な上書きとして正常処理。
  - 失敗時の一時ファイル削除を `Exception` 境界で隔離。

- [condition_meaning_gate.py:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1559)

  - argv 整形時の通常例外を `<argv detail unavailable>` へ畳む。
  - 切詰め時に切詰め前全文の SHA-256 を追加。
  - 短い argv の出力は従来どおり `shlex.join()` と同一。

- [test_p3_s4_loop.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop.py:186)

  - 最終名の公開前不存在、同 digest 再試行、正しい内容、file/directory fsync を検査。
  - [test_p3_s4_loop.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop.py:307) に部分書込失敗時の最終名・一時ファイル不残存テストを追加。

- [test_condition_meaning_gate.py:2328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:2328)

  - 切詰め印に SHA-256 が含まれることを追加検査。
  - [test_condition_meaning_gate.py:2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:2355) に formatter 失敗時の fallback・元 reason code 保持テスト。
  - [test_condition_meaning_gate.py:2387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:2387) に同 prefix・同 byte 数・異なる末尾の識別と短い argv の不変テスト。

## 実走した検査 (nodeid と結果)

`tools/run_tests.py` へ以下の12 nodeidを一括指定しましたが、`qstat -Q preflight rc=1` により `rc=16`、`child_started=false` でした。したがって全 nodeid とも pytest 未実走で、緑とは申告しません。

- `test_condition_meaning_gate.py` の6件

  - `test_run_process_real_failures_report_exact_argv_and_stderr`
  - `test_run_process_timeout_and_execution_failures_report_exact_argv`
  - `test_run_process_argv_detail_is_bounded_and_marks_truncation`
  - `test_run_process_argv_detail_failure_preserves_original_rejection`
  - `test_run_process_truncated_argv_detail_binds_full_command_and_short_is_unchanged`
  - `test_run_process_success_returns_completed_process_unchanged`

- `test_p3_s4_loop.py` の6件

  - `test_condition_gate_rejection_persists_records_by_digest_across_retry`
  - `test_condition_gate_partial_temp_write_failure_leaves_no_final_or_temp`
  - `test_condition_gate_rejection_without_evidence_root_does_not_write`
  - `test_condition_gate_unwritable_destinations_preserve_gate_rejection`
  - `test_condition_gate_serialization_failure_preserves_gate_rejection`
  - `test_condition_gate_green_path_does_not_read_environment_or_write`

静的検査結果:

- `git diff --check`: PASS
- 対象4ファイルの `ast.parse`: PASS
- 変更ファイル集合: 許可された4ファイルのみ

## 未実走・未着手

- 上記12 nodeidの pytest 実走。
- 受入台帳更新。12 nodeidとも現台帳には未登録で、親の正本 producer による JUnit 実走後の `--add-only` 更新が必要です。
- docs、台帳、兄弟 driver は未編集です。
- commit は作成していません。

## 波及可能性の静的列挙

- `condition_meaning_gate` の process 失敗 detail を消費し得る production caller は、`backoff_sweep`、`p3_kickoff`、P3 S4 base/sort/trigger/red、`s1_direct_comparison`、`s1_verify_extime_calibration`、`s2_verify_calibration`、`s3_lock_coverage`、`s3_mocc_lock_coverage`、`s5_permutation_coverage`、`s6_sort_sweep`、`s8a_trigger_coverage/sweep`、paper story drivers、`screening_driver`、`silo_ladder_rung1`、`t152_write_intent_coverage` です。影響は red detail とそれを含む record digest に限定されます。
- `_run_process` の直接的な test consumer は `test_condition_meaning_gate.py` のほか、`test_ccbench_spawn_sites.py`、`test_ss2pl_lock_study.py`、`test_t152_write_intent_coverage.py` にあります。
- `p3_s4_loop.py` は `p3_b4_closed_critic.projection_closure_manifest` の base/sort/trigger 共通 member です。ファイル hash は変わるため、次回 B-4 起動では現行 live hash の宣言が必要です。
- `test_p3_b4_closed_critic.py` と B-4 launcher/material/wiring 系 consumer test が projection hash 変更の波及候補です。
- 新規 test file はないため plain-runner のファイル集合登録は不要です。両既存ファイルの self-run harness は追加 test を動的に列挙します。

## 総括

F1〜F3 の実装と破壊検知テストは完了しています。現行の「supply が全 green、meaning が red でない場合だけ admitted」という判定、reason code 語彙、driver rc、green 経路は変更していません。

ただし pytest child が起動していないため、最終状態は3所見とも `partial（実装済み・未実走）` です。