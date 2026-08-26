# e3_sigkill_self — 誘発条件と観測値の対応

## 投入した job script (逐語)

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -N izt1852e3
#PBS -l elapstim_req=00:05:00
echo "E3: job kills itself with SIGKILL"
hostname
date -u +%Y-%m-%dT%H:%M:%SZ
sleep 10
kill -9 $$
sleep 30
exit 0
```

## qsub の出力 (request ID の由来)

```text
Request 949560.nqsv submitted to queue: gen_S.
```

## 介入: job script 内から自分へ SIGKILL

- 外部からの介入なし (job script 自身の終わり方で決まる)

## scheduler stderr (`.e`) 全文

```text
-bash: line 1: 691903 Killed                  /var/opt/nec/nqsv/jsv/jobfile/0.949560.10/user_script

============================================================
Request ID:             949560.nqsv
Request Name:           izt1852e3
Queue:                  gen_S@nqsv
Number of Jobs:         1
User Name:              tanab
Group Name:             SFC
Created Request Time:   Wed Aug 26 16:01:21 2026
Started Request Time:   Wed Aug 26 16:01:30 2026
Ended Request Time:     Wed Aug 26 16:01:40 2026
Resources Information:
  Elapse:               14S
  Remaining Elapse:     286S
============================================================
```

## この case で観測した State Transition Reason の遷移 (poll 全走)

```text
SUBMIT -> STAGEIN_SUCCESS -> RUN -> PRERUN_SUCCESS -> EXIT -> POSTRUN_SUCCESS
```

## -J -f が does-not-exist を返す一方 -f は request を返していた snapshot (job record 作成前の窓)

```text
=== poll 1 t=+0s wall=2026-08-26T07:01:21Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Batch Job: 949560.nqsv does not exist.
--- qstat -f ---
Request ID: 949560.nqsv
    Request Name = izt1852e3
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Queued
    Previous State          = (none)
    State Transition Time   = Wed Aug 26 16:01:21 2026
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
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e3_sigkill_self/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e3_sigkill_self/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:01:21 2026
    Entered Queue Time   = Wed Aug 26 16:01:21 2026
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
=== poll 41 t=+23s wall=2026-08-26T07:01:45Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Request ID: 949560.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 35
    Job Server Name = JobServer0035
    Execution Host = bnode035
    Exit Code = 8900
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
--- qstat -f ---
Request ID: 949560.nqsv
    Request Name = izt1852e3
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Post-running
    Previous State          = Running
    State Transition Time   = Wed Aug 26 16:01:44 2026
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
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e3_sigkill_self/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e3_sigkill_self/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:01:21 2026
    Entered Queue Time   = Wed Aug 26 16:01:21 2026
    Planned Start Time   = Wed Aug 26 16:01:29 2026
    Execute Request Time = (none)
    Started Request Time = Wed Aug 26 16:01:30 2026
    Ended Request Time   = Wed Aug 26 16:01:40 2026
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
    bnode035(35)
  Resources Information:
    Memory    = 0.000000B
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Elapse    = 14S
    Remaining Elapse = 286S
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
=== poll 50 t=+29s wall=2026-08-26T07:01:50Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Request ID: 949560.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 35
    Job Server Name = JobServer0035
    Execution Host = bnode035
    Exit Code = 8900
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
--- qstat -f ---
Request ID: 949560.nqsv
    Request Name = izt1852e3
    User  Name = tanab
    Group Name = SFC
    User  ID   = 31609
    Group ID   = 30410
    Current State           = Exiting
    Previous State          = Post-running
    State Transition Time   = Wed Aug 26 16:01:50 2026
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
    Stdout = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e3_sigkill_self/scheduler.o
    Stderr = pegasus02:/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/e3_sigkill_self/scheduler.e
    Reqlog = (none)
    Shell = (none)
    Mail Address = tanab@pegasus02
    Mail Option  = (none)
    Job Condition:
        Job NO: 0 ""
    Number of Jobs = 1
    Created Request Time = Wed Aug 26 16:01:21 2026
    Entered Queue Time   = Wed Aug 26 16:01:21 2026
    Planned Start Time   = (none)
    Execute Request Time = (none)
    Started Request Time = Wed Aug 26 16:01:30 2026
    Ended Request Time   = Wed Aug 26 16:01:40 2026
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
    bnode035(35)
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
=== poll 51 t=+29s wall=2026-08-26T07:01:50Z jf_rc=0 rf_rc=0 ===
--- qstat -J -f ---
Batch Job: 949560.nqsv does not exist.
--- qstat -f ---
Batch Request: 949560.nqsv does not exist on nqsv.
```

