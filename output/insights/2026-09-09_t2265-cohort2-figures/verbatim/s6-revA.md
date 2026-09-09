### 所見 1

**主張:** 完了待機処理は実機の NQSV 出力を解析できず、生存中の正常な job を最初の poll で監視エラーにする。  
**根拠:** [wait_t2265_perf6.sh:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:60) は `Job Id:`、[wait_t2265_perf6.sh:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:68) は `job_state =` だけを認識するが、実測出力は `Request ID:` と `Current State = Running` である。このため `absent` となり、JSON がまだ無い正常な実行中 job は [wait_t2265_perf6.sh:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:87) で即座に失敗する。  
**これが本当なら何が壊れるか:** 台帳に正しく記録された job でも親はこの script では完了まで待てず、部分投入状態も正しく追跡できない。  
**確度:** real

### 所見 2

**主張:** 台帳の measurement-design commit と SHA256 は文字種しか検査されず、実在 commit や対象 file の bytes と無関係な値を真正な束縛として記録できる。  
**根拠:** 裁定は measurement-design の commit SHA と SHA256 の記録を要求する [s4-ruling.md:65](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:65) [s4-ruling.md:75](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:75)。一方 launcher は環境変数の存在と 40/64 桁 hex だけを検査し [submit_t2265_perf6.sh:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:22) [submit_t2265_perf6.sh:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:27)、その値をそのまま台帳へ書く [submit_t2265_perf6.sh:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:74)。  
**これが本当なら何が壊れるか:** 台帳から「投入前に固定された measurement-design とこの投入が結び付く」と確認できなくなる。  
**確度:** real

### 所見 3

**主張:** qsub が job を受理してから台帳行が永続化されるまでに失敗窓があり、queue に存在する job が台帳から欠落しうる。  
**根拠:** qsub の成功は [submit_t2265_perf6.sh:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:100) で確定するが、その後に job ID 検査、`date`、台帳追記がある [submit_t2265_perf6.sh:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:106) [submit_t2265_perf6.sh:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:109) [submit_t2265_perf6.sh:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:113)。いずれかが失敗すると accepted job の行が無いまま exit 3 になる。なお、指定された「3 本目の qsub 自体が非 0」の場合は `$?` が qsub の rc を正しく指し、先行 2 行を残して exit 3 となるため、その限定ケース自体は整合している [submit_t2265_perf6.sh:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:102)。  
**これが本当なら何が壊れるか:** 親が accepted job を把握できず、監視漏れまたは誤った再投入が起こりうる。  
**確度:** real

### 所見 4

**主張:** 台帳の初期生成も原子的ではなく、metadata 書込み失敗時に空または途中までの台帳を残す。  
**根拠:** launcher はまず空 file を作り [submit_t2265_perf6.sh:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:66)、別の追記操作で metadata を書く [submit_t2265_perf6.sh:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:69)。追記失敗時も file は除去されず、再実行は既存 file 検査で拒否される [submit_t2265_perf6.sh:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:63)。  
**これが本当なら何が壊れるか:** 親には正式台帳と紛らわしい部分 file が残り、同じ台帳 path での安全な再試行もできない。  
**確度:** real

### 所見 5

**主張:** 裁定で最初に行うとされた hostname 検査が launcher に存在しない。  
**根拠:** 裁定は検査順を「hostname が先」としている [s4-ruling.md:41](/home/SFC/tanab/.claude/jobs/4e2c74ed/tmp/wave/s4-ruling.md:41) が、launcher の preflight は入力値検査から submit tree 検査へ進み [submit_t2265_perf6.sh:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:21) [submit_t2265_perf6.sh:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:32)、hostname を確認しないまま qsub する [submit_t2265_perf6.sh:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:100)。  
**これが本当なら何が壊れるか:** 想定外の host や scheduler frontend からの投入を fail-closed で止められない。  
**確度:** real

### 所見 6

**主張:** submit tree の検査は 7 回の qsub に束縛されておらず、検査後の clean checkout 切替や file 交換により、台帳と異なる tree または PBS script を投入できる。  
**根拠:** HEAD、status、ccbench、投入 file は [submit_t2265_perf6.sh:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:37) から [submit_t2265_perf6.sh:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:61) までに一度だけ検査され、qsub は後の loop で 7 回行われる [submit_t2265_perf6.sh:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:94)。PBS 側も runtime HEAD を 40 桁 hex としか検査せず、期待 SHA とは比較しない [t2187_adaptive_const_probe.pbs:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:48)。  
**これが本当なら何が壊れるか:** 7 rep が別 revision や別 script で走っても、台帳は全件を固定 SHA の投入として表示する。  
**確度:** plausible

### 所見 7

**主張:** `IZ_LEDGER` は任意の絶対 path を許すため、repo、submit tree、job-evidence directory 内へ launcher 自身が file を作る直接経路がある。  
**根拠:** path の制約は絶対 path、改行なし、tab なしだけで [submit_t2265_perf6.sh:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:25)、その path を直接作成する [submit_t2265_perf6.sh:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:66)。さらに submit tree の status 検査は作成前かつ untracked file を無視する [submit_t2265_perf6.sh:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:42)。`cd` 後に launcher が直接触る相対出力 path は無い [submit_t2265_perf6.sh:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:92)。  
**これが本当なら何が壊れるか:** `IZ_LEDGER` の指定ミスだけで保護対象 tree が汚れ、その変化を preflight と PBS の tracked-only 検査が見逃す。  
**確度:** real

### 所見 8

**主張:** submit tree から投入しながら batch stdout/stderr の明示先が無いため、NQSV の既定配送先が投入 directory なら submit tree に log file が作られる。  
**根拠:** qsub 直前に submit tree へ移動する [submit_t2265_perf6.sh:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:92) 一方、PBS header には account、queue、資源、job 名だけがあり、stdout/stderr の指定がない [t2187_adaptive_const_probe.pbs:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:2) [t2187_adaptive_const_probe.pbs:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:6)。  
**これが本当なら何が壊れるか:** 測定後に submit tree が意図しない scheduler log で汚れる。  
**確度:** plausible

## 総括

**このまま投入してはいけない。** qsub の実 argv、60 分指定、cell 順、`qsub_argv` 表現、colon 無し job ID の成果物名変換自体は整合するが、NQSV 非対応の待機処理、虚偽 metadata を許す台帳、accepted job の記録欠落窓が残る。