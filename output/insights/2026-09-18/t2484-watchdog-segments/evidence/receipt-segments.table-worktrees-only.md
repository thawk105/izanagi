n_receipts=587; n_parse_error=102; n_wait=485
Ratios use n_wait; derived waits are lower bounds. Times in seconds.

| kind | reason | n |
| --- | --- | --- |
| child | null | 477 |
| infra | DispatchError: job bootstrap failure: stage=result-guard | 1 |
| infra | DispatchError: queue-wait-timeout | 1 |
| infra | _SignalAbort: signal 15 | 4 |
| infra | orphan-hold-release-failed | 2 |

| segment | n | min | p50 | p90 | max |
| --- | --- | --- | --- | --- | --- |
| t_first_qstat_s | 485 | 1.2 | 1.3 | 1.5 | 11.7 |
| queue_wait_s | 482 | 2.2 | 5.2 | 10.3 | 829.5 |
| queue_wait_derived_s | 3 | 5.1 | 388.9 | 901.5 | 901.5 |
| run_s | 478 | 10.2 | 35.9 | 358.3 | 1783.5 |
| post_end_s | 478 | 0.5 | 5.2 | 6.0 | 36.5 |
| qdel_cleanup_elapsed_s | 8 | 0.1 | 0.1 | 10.5 | 10.5 |
| job_trace_span_s | 340 | 0.0 | 17.7 | 84.7 | 1112.0 |

| seconds | n | ratio | derived_n | derived_ratio |
| --- | --- | --- | --- | --- |
| 300 | 13 | 0.026804123711340205 | 2 | 0.004123711340206186 |
| 600 | 6 | 0.012371134020618556 | 1 | 0.002061855670103093 |
| 900 | 1 | 0.002061855670103093 | 1 | 0.002061855670103093 |
| 1200 | 0 | 0.0 | 0 | 0.0 |
| 3000 | 0 | 0.0 | 0 | 0.0 |

| bucket | n | n_wait | p50 | p90 | max | queue_wait_ge_900 |
| --- | --- | --- | --- | --- | --- | --- |
| 0-9 | 316 | 316 | 5.2 | 5.6 | 901.5 | 1 |
| 10-49 | 58 | 58 | 5.2 | 205.1 | 430.2 | 0 |
| 50-99 | 56 | 56 | 5.2 | 10.3 | 619.8 | 0 |
| 100+ | 55 | 55 | 5.2 | 15.4 | 829.5 | 0 |
| unknown | 0 | 0 | null | null | null | 0 |

| submission_dir | request_id | reason | last_state | t_last_s | cleanup_elapsed_s | preflight_que |
| --- | --- | --- | --- | --- | --- | --- |
| 67d1f3cc3ece6949465ddeaaf2dd45c6 | 5156.nqsv | DispatchError: queue-wait-timeout | QUE | 902.7474742119666 | 10.47213269607164 | 9 |
| 0b85509afa7b32a81e34971192766ae3 | 919523.nqsv | _SignalAbort: signal 15 | QUE | 390.17951575596817 | 0.15161366784013808 | 130 |
| 5331036bdddb7d52c56cb1ccfe963dc3 | 978653.nqsv | _SignalAbort: signal 15 | QUE | 6.427214016992366 | 0.257723693997832 | 148 |
