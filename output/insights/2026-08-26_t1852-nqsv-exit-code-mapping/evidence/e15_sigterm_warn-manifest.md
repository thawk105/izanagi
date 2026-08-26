# e15_sigterm_warn — 誘発条件と観測値の対応

## 投入した job script (逐語)

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -N izt1852ef
echo "E15: scheduler sends SIGTERM at the elapstim warning point (--accept-sigterm)"
hostname
date -u +%Y-%m-%dT%H:%M:%SZ
sleep 300
exit 0
```

## qsub の出力 (request ID の由来)

```text
Request 949573.nqsv submitted to queue: gen_S.
```

## 介入: なし (--accept-sigterm と警告値付きで投入)

- 外部からの介入なし (job script 自身の終わり方で決まる)

## scheduler stderr (`.e`) 全文

```text

%NQSV(INFO): Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)

============================================================
Request ID:             949573.nqsv
Request Name:           izt1852ef
Queue:                  gen_S@nqsv
Number of Jobs:         1
User Name:              tanab
Group Name:             SFC
Created Request Time:   Wed Aug 26 16:10:19 2026
Started Request Time:   Wed Aug 26 16:10:26 2026
Ended Request Time:     Wed Aug 26 16:13:26 2026
Resources Information:
  Elapse:               184S
  Remaining Elapse:     0S
============================================================
```

## この case で観測した State Transition Reason の遷移 (poll 全走)

```text
STAGEIN_SUCCESS -> RUN -> PRERUN_SUCCESS -> EXIT -> POSTRUN_SUCCESS
```

## -J -f が does-not-exist を返す一方 -f は request を返していた snapshot (job record 作成前の窓)

該当なし (この case ではこの境界を観測していない)

## 終端 Exit Code を最初に観測した snapshot

```text
=== poll 327 t=+191s wall=2026-08-26T07:13:30Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Request ID: 949573.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 9
    Job Server Name = JobServer0009
    Execution Host = bnode009
    Exit Code = 9
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
--- qstat -f ---
Request ID: 949573.nqsv
    Request Name = izt1852ef
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Post-running
    Previous State          = Running
    State Transition Time   = Wed Aug 26 16:13:30 2026
    State Transition Reason = EXIT
    Queue = gen_S@nqsv (Execution Queue)
    Job Topology = Distribute Job
    Request Priority  = 0
    Request Loglevel  = 0
    Rerunable    = No
    Holdable     = Yes
    Hold Type    = (none)
    Migratable   = Yes
    Suspend Type = (none)
    Account Code = SFC
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e15_sigterm_warn/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e15_sigterm_warn/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:10:19 2026
    Entered Queue Time   = Wed Aug 26 16:10:19 2026
    Planned Start Time   = Wed Aug 26 16:10:29 2026
    Execute Request Time = (none)
    Started Request Time = Wed Aug 26 16:10:26 2026
    Ended Request Time   = Wed Aug 26 16:13:26 2026
    Requested Start Time = (none)
    Deadline Time        = (none)
    UMASK = 022
    Reservation ID      = (none)
    qattach command = Enable
    Attach = No
    Cluster Type Select = NONE
    UserPP Script = (none)
    Exclusive = (none)
    HCA Number = (none)
    Accept Sigterm = No
    Enable Cloud Bursting = No
  Custom Resources:
    Share           = 1
  Execution Hosts(JSVNO):
    bnode009(9)
  Resources Information:
    Memory    = 0.000000B
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Elapse    = 184S
    Remaining Elapse = 0S
    Virtual Memory = 0.000000B
  Logical Host Resources:
    VE Node Number        = Max:         0 Warn:       --- 
    CPU Number            = Max:        48 Warn:       --- 
    GPU Number            = Max:         0 Warn:       --- 
    CPU Time              = Max: UNLIMITED Warn: UNLIMITED 
    Memory Size           = Max: UNLIMITED Warn: UNLIMITED 
    Virtual Memory Size   = Max: UNLIMITED Warn: UNLIMITED 
    VE CPU Time           = Max: UNLIMITED Warn: UNLIMITED 
    VE Memory Size        = Max: UNLIMITED Warn: UNLIMITED 
    Stdout Size           = Max: UNLIMITED Warn: UNLIMITED 
    Stderr Size           = Max: UNLIMITED Warn: UNLIMITED 
  VE Node Resources:
    VE CPU Time           = Max: UNLIMITED Warn: UNLIMITED 
    VE Memory Size        = Max: UNLIMITED Warn: UNLIMITED 
  Resources Limits:
    (Per-Req) Elapse Time Limit       = Max:      180S Warn:       60S 
    (Per-Job) CPU Time                = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Job) CPU Number              = Max:        48 Warn:       --- 
    (Per-Job) Memory Size             = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Job) Virtual Memory Size     = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Job) GPU Number              = Max:         0 Warn:       --- 
    (Per-Prc) CPU Time                = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Open File Number        = Max:    262144 Warn:       --- 
    (Per-Prc) Virtual Memory Size     = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Data Segment Size       = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Stack Segment Size      = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Core File Size          = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Permanent File Size     = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) VE CPU Time             = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) VE Memory Size          = Max: UNLIMITED Warn: UNLIMITED 
  Kernel Parameter:
    Resource Sharing Group     = 0
    Nice Value                 = 0
  User Attributes:
    (none)
```

## request が最後に存在していた snapshot

```text
=== poll 336 t=+196s wall=2026-08-26T07:13:36Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Request ID: 949573.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 9
    Job Server Name = JobServer0009
    Execution Host = bnode009
    Exit Code = 9
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
--- qstat -f ---
Request ID: 949573.nqsv
    Request Name = izt1852ef
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Exiting
    Previous State          = Post-running
    State Transition Time   = Wed Aug 26 16:13:35 2026
    State Transition Reason = POSTRUN_SUCCESS
    Queue = gen_S@nqsv (Execution Queue)
    Job Topology = Distribute Job
    Request Priority  = 0
    Request Loglevel  = 0
    Rerunable    = No
    Holdable     = Yes
    Hold Type    = (none)
    Migratable   = Yes
    Suspend Type = (none)
    Account Code = SFC
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e15_sigterm_warn/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e15_sigterm_warn/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:10:19 2026
    Entered Queue Time   = Wed Aug 26 16:10:19 2026
    Planned Start Time   = (none)
    Execute Request Time = (none)
    Started Request Time = Wed Aug 26 16:10:26 2026
    Ended Request Time   = Wed Aug 26 16:13:26 2026
    Requested Start Time = (none)
    Deadline Time        = (none)
    UMASK = 022
    Reservation ID      = (none)
    qattach command = Enable
    Attach = No
    Cluster Type Select = NONE
    UserPP Script = (none)
    Exclusive = (none)
    HCA Number = (none)
    Accept Sigterm = No
    Enable Cloud Bursting = No
  Custom Resources:
    Share           = 1
  Execution Hosts(JSVNO):
    bnode009(9)
  Resources Information:
    Memory    = 0.000000B
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Elapse    = 0S
    Remaining Elapse = 180S
    Virtual Memory = 0.000000B
  Logical Host Resources:
    VE Node Number        = Max:         0 Warn:       --- 
    CPU Number            = Max:        48 Warn:       --- 
    GPU Number            = Max:         0 Warn:       --- 
    CPU Time              = Max: UNLIMITED Warn: UNLIMITED 
    Memory Size           = Max: UNLIMITED Warn: UNLIMITED 
    Virtual Memory Size   = Max: UNLIMITED Warn: UNLIMITED 
    VE CPU Time           = Max: UNLIMITED Warn: UNLIMITED 
    VE Memory Size        = Max: UNLIMITED Warn: UNLIMITED 
    Stdout Size           = Max: UNLIMITED Warn: UNLIMITED 
    Stderr Size           = Max: UNLIMITED Warn: UNLIMITED 
  VE Node Resources:
    VE CPU Time           = Max: UNLIMITED Warn: UNLIMITED 
    VE Memory Size        = Max: UNLIMITED Warn: UNLIMITED 
  Resources Limits:
    (Per-Req) Elapse Time Limit       = Max:      180S Warn:       60S 
    (Per-Job) CPU Time                = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Job) CPU Number              = Max:        48 Warn:       --- 
    (Per-Job) Memory Size             = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Job) Virtual Memory Size     = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Job) GPU Number              = Max:         0 Warn:       --- 
    (Per-Prc) CPU Time                = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Open File Number        = Max:    262144 Warn:       --- 
    (Per-Prc) Virtual Memory Size     = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Data Segment Size       = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Stack Segment Size      = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Core File Size          = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) Permanent File Size     = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) VE CPU Time             = Max: UNLIMITED Warn: UNLIMITED 
    (Per-Prc) VE Memory Size          = Max: UNLIMITED Warn: UNLIMITED 
  Kernel Parameter:
    Resource Sharing Group     = 0
    Nice Value                 = 0
  Scheduler Message:
    Start time was cleared.
  User Attributes:
    (none)
```

## 最初に does-not-exist を返した snapshot

```text
=== poll 337 t=+197s wall=2026-08-26T07:13:36Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Batch Job: 949573.nqsv does not exist.
--- qstat -f ---
Batch Request: 949573.nqsv does not exist on nqsv.
```

