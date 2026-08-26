# qstat / qsub の運用事実 — 逐語と終了コード

取得: 2026-08-26T07:27:39Z / host pegasus02

## 1. 存在しない request に対する qstat の終了コード

本 wave が投入し、既に消えた request 949557.nqsv を引く。

```text
$ qstat -f 949557.nqsv
Batch Request: 949557.nqsv does not exist on nqsv.
rc=0

$ qstat -J -f 949557.nqsv
Batch Job: 949557.nqsv does not exist.
rc=0

$ qstat -T 949557.nqsv
No such request: 949557.nqsv.
rc=0
```

**rc はいずれも 0 である。** 本文だけが存在しないことを述べている。

## 2. 警告値付き elapstim_req の引用符

shell から qsub を呼ぶとき、引用符を qsub の argv へ渡さないと受理されない。

```text
$ qsub -l elapstim_req=00:03:00,00:01:00 <script>   # 引用符が shell に食われる形
Invalid syntax following -l flag.
Syntax: -l resource_list[,resource_list,...]
resource_list: resource_name=["]max_limit[,warning_limit"]
resource_name: elapstim_req cputim_prc  cputim_job  cpunum_job  filenum_prc
               memsz_job    datasz_prc  stacksz_prc coresz_prc  filesz_prc
               vmemsz_prc   vmemsz_job  socknum_job gpunum_job
               vecputim_prc vememsz_prc 
Request not queued.
rc=1
```

成功した形は次である (実際に request 949573 を作った argv)。

```bash
qsub --accept-sigterm --warning-signal=elapstim:SIGTERM \
  -l 'elapstim_req="00:03:00,00:01:00"' \
  -o <stdout> -e <stderr> job_e15_sigterm_warn.sh
```

## 3. 会計 command の権限

```text
$ racctreq 949566.nqsv
===========================================
GROUP          REMAIN   ESTIMATE    INITIAL
===========================================
sudo: パスワードが必要です
rc=1
```

## 4. qstat の usage (履歴照会 mode が無いことの根拠)

```text
usage: 
qstat    [-P privilege] [-V] [-f] [-n] [-l] [-d] [-m] [-s] [-a]
         [-u userlist] [-q quelist] [-c cpumode] [-F Item list]
         [-o Item list] [-O Item list] [--group[=group-name]]
         [--adjust-column] [--planned-start-time] [batch_request_identifier ...]
qstat -B [-P privilege] [-V] [-f] [-n] [-l] [-d] [-F Item list]
         [-o Item list] [-O Item list] [--adjust-column]
         [batch_server_host ...]
qstat -B -L -P m [ -V ] [-n]
qstat -D [-P privilege] [-V] [-f] [-n] [-l] [-F Item list] [-o Item list]
         [-O Item list] [--adjust-column] [scheduler_identifier ...]
qstat -E [-P privilege] [-V] [-f] [-n] [-l] [-t] [-g node_group]
         [-F Item list][-o Item list] [-O Item list] [--adjust-column]
         [execution_host ...]
qstat -G [-P privilege] [-V] [-f] [-n] [-l] [-F Item list] [-o Item list]
         [-O Item list] [node_group ...]
qstat -J [-P privilege] [-V] [-f] [-n] [-l] [-d] [-t] [-m|-c cpumode] [-u userlist]
         [-h execution_host] [-F Item list] [-o Item list] [-O Item list] [-e]
         [--adjust-column] [batch_job_identifier ...]
qstat -Q [-P privilege] [-V] [-f] [-n] [-l] [-d]
         { [-e] [-i] [-r] [-N] | -s } [-t] [-F Item list]
         [-o Item list] [-O Item list] [--group=group-name] [destination ...]
qstat -R [-P privilege] [-V] [-f] [-n] [-l] [-F Item list]
         [-o Item list] [-O Item list] [--adjust-column]
         [parametric_request_identifier ...]
qstat -S [-P privilege] [-V] [-f] [-n] [-l] [-t] [-h execution_host]
         [-g node_group] [-F Item list] [-o Item list] [-O Item list]
         [--adjust-column] [job_server_number ...]
qstat -T [-P privilege] [-V] [-f] [-n] [-l] [-u userlist] [-F Item list]
         [-o Item list] [-O Item list] [--adjust-column]
         [batch_request_identifier ...]
qstat --limit
         [-P privilege] [--group=group-name] [-V]
qstat --template
         [-P privilege] [-V] [-f] [-n] [-l] [--VE] [template_name ...]
qstat --custom
         [-P privilege] [-V]
qstat --venode
         [-P privilege] [-V] [-n] [-l] [execution_host ...]
qstat --cloud_template
         [-P privilege] [-V] [-f] [-n] [-l] [template_name ...]
```
