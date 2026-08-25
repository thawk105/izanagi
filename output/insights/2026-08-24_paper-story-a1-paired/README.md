# Paper-story A-1 exploratory positional comparison

Study: `paper-story-a1-20260824-exploratory-v1`

Complete: `true`

All-workload observed negative direction: `no`

The three workloads do not all have a negative observed mean of their five signed positional differences in this run.

This result is exploratory, formal=false, and promotion is prohibited. The five positions are arm-grouped ordinal matches, not shared time blocks. They do not support causal, population, significance, confidence-interval, or repeatability claims. Trace0 evidence is source-routed and is not an artifact-standalone proof. Invalid input always means no cross-workload conclusion.

PBS evidence scope: the job observes PBS_JOBID, PBS_O_HOST, and PBS_O_WORKDIR. PBS_O_QUEUE is not exported by this NQSV site and is not claimed as a job observation. NQSV stdout/stderr FD targets are not the qsub -o/-e delivery files; their delivered bytes are bound only by the scheduler completion receipt SHA-256 values and the job-terminal SHA-256. Scheduler terminal evidence accepts exactly two forms: a request still visible in a terminal state, or a request proven visible at submission and later absent from qstat. In the absent form, scheduler state and exit status are explicitly recorded as unobserved, not as empty values or zero. Job success remains established independently by driver_rc=0, shell_rc=0, and job terminal status=finished.

Materialization publish: RENAME_NOREPLACE was attempted on this filesystem and returned EINVAL. The fallback held an A-1-specific exclusive sibling claim, refused a destination present at its existence check, and then exposed the complete staging directory with one flags-zero renameat2 call. This is not atomic no-replace against a non-cooperating writer: an empty type-compatible destination created after the check and before that rename may be replaced. No file is written below the destination after the directory publish.
