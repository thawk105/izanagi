# Paper-story A-1 balanced five-rep comparison

Study: `paper-story-a1-20260901-balanced5-sized-v1`

All workloads terminal: `true`

All workloads valid: `true`

No cross-workload conclusion is produced. Each row is a terminal workload result.

| workload | status | reps | mean variant-baseline tps | descriptive interval tps | B tps | classification | variance_plan_breach |
|---|---:|---:|---:|---:|---:|---|---:|
| write-heavy | valid | 30 | 1538451.466667 | [1497017.255584, 1579885.677749] | 72952.123000 | resolved-above-floor | true |
| balanced | valid | 30 | 548138.233333 | [522585.848895, 573690.617771] | 110832.746000 | resolved-above-floor | false |
| read-heavy | valid | 30 | -560565.600000 | [-602312.344316, -518818.855684] | 305064.861000 | resolved-above-floor | true |


## Job accounting

CPU is the baseline-subtracted Bash shell plus reaped-descendant CPU window recorded by each workload job.

| workload | request ID | host | CPU total s | elapsed s |
|---|---|---|---:|---:|
| write-heavy | 13220.nqsv | bnode035 | 9080.502000 | 1050.020000 |
| balanced | 13221.nqsv | bnode039 | 9081.926000 | 321.320000 |
| read-heavy | 13222.nqsv | bnode040 | 9108.688000 | 847.450000 |
This result is exploratory, formal=false, and promotion is prohibited. The registered estimand is the arithmetic mean of paired variant-minus-baseline TPS differences under the balanced five-rep schedule. Pilot observations are sizing-only and cannot enter the final estimate. Trace0 evidence is source-routed and is not an artifact-standalone proof.

## この設計が言えないこと

- The estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state direct effect.
- Pilot observations are sizing inputs and are ineligible for the final estimate.
- Source-routed trace0 evidence is not an artifact-standalone proof.
- No cross-workload conclusion is produced.
- EINVAL publish fallback is not atomic no-replace against a non-cooperating destination writer.
PBS evidence scope: the job observes PBS_JOBID, PBS_O_HOST, and PBS_O_WORKDIR. PBS_O_QUEUE is not exported by this NQSV site and is not claimed as a job observation. NQSV stdout/stderr FD targets are not the qsub -o/-e delivery files; their delivered bytes are bound only by the scheduler completion receipt SHA-256 values and the job-terminal SHA-256. Scheduler terminal evidence accepts exactly two forms: a request still visible in a terminal state, or a request proven visible at submission and later absent from qstat. In the absent form, scheduler state and exit status are explicitly recorded as unobserved, not as empty values or zero. Job success remains established independently by driver_rc=0, shell_rc=0, and job terminal status=finished.

Materialization publish: RENAME_NOREPLACE was attempted on this filesystem and returned EINVAL. The fallback held an A-1-specific exclusive sibling claim, refused a destination present at its existence check, and then exposed the complete staging directory with one flags-zero renameat2 call. This is not atomic no-replace against a non-cooperating writer: an empty type-compatible destination created after the check and before that rename may be replaced. No file is written below the destination after the directory publish.
