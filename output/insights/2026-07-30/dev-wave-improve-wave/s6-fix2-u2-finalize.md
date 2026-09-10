結論は **NO-GO** です。R2〜R7/R9は静的に closed、R8は lookup pairing の直接 expected-red が不足するため partial と判定しました。finalizerによる追加変更はありません。

### R2〜R9

| ID | 判定 | 実装関数 | 対応test・根拠 |
|---|---|---|---|
| R2 | closed（静的） | `_tree_summary`、`verify_snapshot_tree`。worker直前とrunner終了後にfull-treeを再検証 | `test_dirty_snapshot_binds_execution_closure_and_detects_mode_drift` |
| R3 | closed（静的） | `validate_nqsv_accounting`。separator付き14行末尾block、順序、exact IDを要求。同じstable `stderr_raw`からreceipt/accountingを生成 | `test_monitor_rejects_missing_or_wrong_nqsv_accounting_footer`、`test_transient_after_runner_result_recovers_running` |
| R4 | closed（静的） | `SubprocessScheduler.run`、`submit_and_monitor`、`resume_dispatch`、`cancel_job`、pending final | qsub OSError/timeout/signal、intent/result/submit/cancel/final各crash/resumeの直接testあり |
| R5 | closed（静的） | `parse_qstat`、`parse_qstat_candidates`、`monitor_job` | `test_per_job_qstat_rejects_wrong_request_id_before_terminal_success`、同名旧時刻/別user decoyを含む`test_qsub_rc0_unparseable_id_recovers_single_exact_name_and_monitors`、`test_running_qstat_host_must_match_runner_claim_host` |
| R6 | closed（静的） | `monitor_job`の`spool_policy_failed` latch | `test_post_terminal_combined_spool_growth_cannot_return_child_result` |
| R7 | closed（静的） | `validate_runner_result_object`でreceipt size prefixをSHA照合後、event一意性を検証 | `test_task_run_growth_still_hashes_producer_receipt_prefix` |
| R8 | **partial** | `_validate_scheduler_lookup_chain`はintent/result cardinality・順序・matched candidate→submit→final IDを検証。`lookup_scheduler_job`はqsub absolute deadlineを共有 | deadlineは`test_resume_lookup_cannot_reset_qsub_absolute_deadline`、ID結合は既存testあり。ただしintent/resultの欠落・重複・並べ替えを直接拒否するexpected-redがない |
| R9 | closed（静的） | `_resolve_compute_symbolic_nproc`がcomputeのauto/logicalをU1 API経由でaffinity整数化。OTHERは保持 | `test_compute_symbolic_nproc_reaches_actual_pytest_argv_as_affinity_integer`、`test_other_preserves_xdist_auto_and_logical_spellings` |

### Mutation確認

| 対象 | current test | 判定 |
|---|---|---|
| M10 WAL fsync除去 | `test_append_journal_requires_injected_durability_sync` | 検出nodeあり・未実走 |
| M12 runner-result不在をrc0化 | `test_missing_runner_result_is_infrastructure_failure_not_zero` | 検出nodeあり・未実走 |
| M14 qdel retry除去 | `test_qdel_retries_after_first_failure_and_latches_second_success` | 検出nodeあり・未実走 |
| M15 task-run greenを成功正本化 | `test_green_task_run_event_cannot_mask_accounting_failure` | 検出nodeあり・未実走 |
| qdel durable latch | `test_qdel_success_before_latch_crash_resumes_without_second_qdel`、forged latch拒否test | 検出nodeあり・未実走 |
| full-tree/footer/spool/ledger/compute | 上表の直接test | 検出nodeあり・未実走 |
| lookup pairing | deadline・ID結合はあり、intent/result cardinality/orderの直接negativeなし | **partial** |

「KILLED」はpytest/mutation未実走のため主張しません。

### 変更file

finalizerによる変更はありません。current U2差分は次の10 filesです。

- `tools/pegasus/test_dispatch.py`
- `tools/pegasus/submit_tests.py`
- `tools/pegasus/run_tests_job.sh`
- `tools/pegasus/test_dispatch_policy.json`
- `tools/run_tests.py`
- `orchestrator/tests/test_pegasus_test_dispatch.py`
- `orchestrator/tests/test_pegasus_tools.py`
- `orchestrator/tests/test_run_tests_nproc.py`
- `orchestrator/tests/test_run_tests_preflight.py`
- `orchestrator/tests/test_run_tests_task_run.py`

`tools/pegasus/policy.json`はcurrent bytesがHEADとbyte-exactで、双方のSHA-256は `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` です。U1の2未追跡fileは未編集です。

### 静的確認

通過:

- `git diff --check`
- `git diff HEAD --check`
- `git diff --cached --check`
- Python 3.10 AST parse：所有Python 8 files
- isolated import：policy / submitter / dispatcher / runner
- pyflakes：8 files
- AST call-signature照合
- R2〜R9実装関数／test symbolのAST・`rg`照合
- duplicate module-level definition検査
- `bash -n tools/pegasus/run_tests_job.sh`
- dispatch policy canonical JSON・exact 31 keys
- job script mode 755

undefined名、call signature不整合、schema exact-keyの片側破断は見つからず、最小修正対象はありませんでした。

未実走:

- pytest、mutation harness
- build
- qsub/qstat/qdel
- compute-node targeted/full acceptance
- repository全走、docs/provenance checker

残must-fixは、lookup WALのintent/result欠落・重複・順序変更を直接拒否するexpected-red追加と、計算ノードでの対象test／mutation実走です。

## 総括

R2〜R7/R9はcurrent bytesで静的closed、R8は実装済みながら必須pairing negativeの検出力証明が不足してpartialです。実走証拠もないため、live投入判定は **NO-GO** を維持します。
