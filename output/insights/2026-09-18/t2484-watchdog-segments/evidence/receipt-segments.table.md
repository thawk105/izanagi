n_receipts=3964; n_parse_error=115; n_wait=3849
Ratios use n_wait; derived waits are lower bounds. Times in seconds.

| kind | reason | n |
| --- | --- | --- |
| child | null | 3834 |
| infra | DispatchError: job bootstrap failure: stage=result-guard | 1 |
| infra | DispatchError: queue-wait-timeout | 4 |
| infra | _SignalAbort: signal 15 | 8 |
| infra | orphan-hold-release-failed | 2 |

| segment | n | min | p50 | p90 | max |
| --- | --- | --- | --- | --- | --- |
| t_first_qstat_s | 3849 | 1.1 | 1.3 | 1.4 | 15.9 |
| queue_wait_s | 3841 | 0.1 | 5.2 | 5.3 | 1601.0 |
| queue_wait_derived_s | 8 | 5.1 | 388.9 | 902.4 | 902.4 |
| run_s | 3835 | 10.2 | 20.5 | 92.3 | 1783.5 |
| post_end_s | 3835 | -1622.6 | 5.2 | 9.3 | 36.5 |
| qdel_cleanup_elapsed_s | 15 | 0.1 | 0.2 | 0.3 | 10.5 |
| job_trace_span_s | 400 | 0.0 | 14.7 | 83.1 | 1112.0 |

| seconds | n | ratio | derived_n | derived_ratio |
| --- | --- | --- | --- | --- |
| 300 | 37 | 0.009612886464016628 | 5 | 0.0012990387113535984 |
| 600 | 19 | 0.004936347103143674 | 4 | 0.0010392309690828788 |
| 900 | 5 | 0.0012990387113535984 | 4 | 0.0010392309690828788 |
| 1200 | 1 | 0.0002598077422707197 | 0 | 0.0 |
| 3000 | 0 | 0.0 | 0 | 0.0 |

| bucket | n | n_wait | p50 | p90 | max | queue_wait_ge_900 |
| --- | --- | --- | --- | --- | --- | --- |
| 0-9 | 2293 | 2293 | 5.2 | 5.3 | 1601.0 | 4 |
| 10-49 | 777 | 777 | 5.2 | 10.3 | 874.9 | 0 |
| 50-99 | 672 | 672 | 5.2 | 5.3 | 902.4 | 1 |
| 100+ | 107 | 107 | 5.2 | 51.1 | 829.5 | 0 |
| unknown | 0 | 0 | null | null | null | 0 |

| submission_dir | request_id | reason | last_state | t_last_s | cleanup_elapsed_s | preflight_que |
| --- | --- | --- | --- | --- | --- | --- |
| 616ca7a2d8402915c91589a4d15382dd | 947995.nqsv | DispatchError: queue-wait-timeout | QUE | 903.6117658428848 | 0.25562387704849243 | 75 |
| 7203691192e48b953f64a871850f52cb | 909493.nqsv | DispatchError: queue-wait-timeout | QUE | 901.5222979709506 | 0.15228038397617638 | 2 |
| 786f9f5ceba9c645c88e0177362fdcc2 | 909506.nqsv | DispatchError: queue-wait-timeout | QUE | 901.4969023000449 | 0.15081396396271884 | 1 |
| 12c57b236572362e1576e27d6776526c | 928116.nqsv | _SignalAbort: signal 15 | QUE | 298.02225427981466 | 0.1567248897626996 | 50 |
| f6bc93dbec8a0925f2b6c9f6823920b9 | 928128.nqsv | _SignalAbort: signal 15 | QUE | 298.14453691104427 | 0.15818513929843903 | 50 |
| 67d1f3cc3ece6949465ddeaaf2dd45c6 | 5156.nqsv | DispatchError: queue-wait-timeout | QUE | 902.7474742119666 | 10.47213269607164 | 9 |
| 0b85509afa7b32a81e34971192766ae3 | 919523.nqsv | _SignalAbort: signal 15 | QUE | 390.17951575596817 | 0.15161366784013808 | 130 |
| 5331036bdddb7d52c56cb1ccfe963dc3 | 978653.nqsv | _SignalAbort: signal 15 | QUE | 6.427214016992366 | 0.257723693997832 | 148 |
