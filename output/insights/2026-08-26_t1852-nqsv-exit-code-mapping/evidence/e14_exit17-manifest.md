# e14_exit17 — 誘発条件と観測値の対応

## 投入した job script (逐語)

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -N izt1852ee
#PBS -l elapstim_req=00:05:00
echo "E14: script exits 17 (predicts Exit Code 1100 if the field is hex wait status)"
hostname
date -u +%Y-%m-%dT%H:%M:%SZ
sleep 15
exit 17
```

## qsub の出力 (request ID の由来)

```text
Request 949571.nqsv submitted to queue: gen_S.
```

## 介入: なし

- 外部からの介入なし (job script 自身の終わり方で決まる)

## scheduler stderr (`.e`) 全文

```text

============================================================
Request ID:             949571.nqsv
Request Name:           izt1852ee
Queue:                  gen_S@nqsv
Number of Jobs:         1
User Name:              tanab
Group Name:             SFC
Created Request Time:   Wed Aug 26 16:05:59 2026
Started Request Time:   Wed Aug 26 16:06:07 2026
Ended Request Time:     Wed Aug 26 16:06:22 2026
Resources Information:
  Elapse:               19S
  Remaining Elapse:     281S
============================================================
```

## この case で観測した State Transition Reason の遷移 (poll 全走)

```text
SUBMIT -> RUN -> PRERUN_SUCCESS -> EXIT -> POSTRUN_SUCCESS
```

## -J -f が does-not-exist を返す一方 -f は request を返していた snapshot (job record 作成前の窓)

```text
=== poll 1 t=+0s wall=2026-08-26T07:05:59Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Batch Job: 949571.nqsv does not exist.
--- qstat -f ---
Request ID: 949571.nqsv
    Request Name = izt1852ee
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Queued
    Previous State          = (none)
    State Transition Time   = Wed Aug 26 16:05:59 2026
    State Transition Reason = SUBMIT
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
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e14_exit17/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e14_exit17/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:05:59 2026
    Entered Queue Time   = Wed Aug 26 16:05:59 2026
    Planned Start Time   = (none)
    Execute Request Time = (none)
    Started Request Time = (none)
    Ended Request Time   = (none)
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
    -  
  Resources Information:
    Memory    = 0.000000B
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Elapse    = 0S
    Remaining Elapse = 300S
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
    (Per-Req) Elapse Time Limit       = Max:      300S Warn:      300S 
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

## 終端 Exit Code を最初に観測した snapshot

```text
=== poll 49 t=+27s wall=2026-08-26T07:06:27Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Request ID: 949571.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 9
    Job Server Name = JobServer0009
    Execution Host = bnode009
    Exit Code = 1100
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
--- qstat -f ---
Request ID: 949571.nqsv
    Request Name = izt1852ee
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Post-running
    Previous State          = Running
    State Transition Time   = Wed Aug 26 16:06:26 2026
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
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e14_exit17/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e14_exit17/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:05:59 2026
    Entered Queue Time   = Wed Aug 26 16:05:59 2026
    Planned Start Time   = Wed Aug 26 16:06:29 2026
    Execute Request Time = (none)
    Started Request Time = Wed Aug 26 16:06:07 2026
    Ended Request Time   = Wed Aug 26 16:06:22 2026
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
    Elapse    = 19S
    Remaining Elapse = 281S
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
    (Per-Req) Elapse Time Limit       = Max:      300S Warn:      300S 
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
=== poll 58 t=+33s wall=2026-08-26T07:06:32Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Request ID: 949571.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 9
    Job Server Name = JobServer0009
    Execution Host = bnode009
    Exit Code = 1100
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
--- qstat -f ---
Request ID: 949571.nqsv
    Request Name = izt1852ee
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Exiting
    Previous State          = Post-running
    State Transition Time   = Wed Aug 26 16:06:32 2026
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
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e14_exit17/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e14_exit17/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:05:59 2026
    Entered Queue Time   = Wed Aug 26 16:05:59 2026
    Planned Start Time   = (none)
    Execute Request Time = (none)
    Started Request Time = Wed Aug 26 16:06:07 2026
    Ended Request Time   = Wed Aug 26 16:06:22 2026
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
    Remaining Elapse = 300S
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
    (Per-Req) Elapse Time Limit       = Max:      300S Warn:      300S 
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
=== poll 59 t=+33s wall=2026-08-26T07:06:32Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Batch Job: 949571.nqsv does not exist.
--- qstat -f ---
Batch Request: 949571.nqsv does not exist on nqsv.
```

