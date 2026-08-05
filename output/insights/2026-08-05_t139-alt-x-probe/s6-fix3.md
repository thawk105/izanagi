H1・H2 はともに `closed` です。今回の追加修正は driver と PBS のみで、commit・docs・`output/**`・qsub/qstat・CCBench build/benchmark には触れていません。

### 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| H1 read-only snapshot を consumer へ渡す | `closed` | immutable snapshot を維持したまま、third-party を writable consumer root へ複製し byte 比較・witness 記録。[PBS:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:255)、[PBS:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:273)。CCBench の stock/probe も snapshot から直接 writable copy を作り、patch 前に byte 同一性を記録。[driver:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:369)。masstree は writable root を消費。[driver:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:391)。cleanup 前に stage を owner-writable 化。[PBS:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:34)。 |
| H2 子 directory symlink 検査順 | `closed` | dependency の `gflags/glog` は child path に `-d && ! -L` を適用してから `realpath`。[PBS:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:220)。third-party 3 tree にも同じ順序を適用。[PBS:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:257)。 |

### 直列 cap

driver 内部:

- writable copy・chmod・byte比較・patch: `2×75 + 30 = 180`
- 6 build/receipt: `6×(60+180+10) = 1500`
- liveness: `6×30 = 180`
- performance: `30×15 = 450`
- 合計: `180 + 1500 + 180 + 450 = 2310 ≤ 2400`

PBS 前段:

`33 + 25 + 10 + 90 + 10 + 150 + 60 + 10 + 90 + 420 = 898`

driver 外枠を含む支配総和:

`898 + 2400 = 3298 ≤ 3300`

実装内にも同じ計算を記載しています。[PBS:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:331)

### 既存閉鎖所見の非回帰

- G2: expected commit の必須化・HEAD exact 比較・commit blob 展開を維持。[PBS:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:47)、[PBS:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:65)
- G3: canonical preregistration path の literal exact gate を維持。[PBS:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:102)
- G5: 早期 EXIT trap と既存 terminal state 保持を維持。[PBS:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:15)、[driver:575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:575)
- G6: absolute deadline と全体 cap は `3298秒` で維持。
- F1: transaction/result/util の exact-one と macro exact 検査を未変更。[driver:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:32)
- F3: main/source の clean・index・pin 検査を維持。[PBS:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:81)、[PBS:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:163)
- F7: TPS を primary に確定した後だけ副次診断を処理。[driver:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:515)

### 検査結果

- driver / PBS `bash -n`: rc=0
- H1 fixture:
  - pin: `d706650cdb31e442bef45b9b4216951d4fb40969`
  - object snapshot read-only 化: 成功
  - writable copy: 成功
  - snapshot/copy byte 比較: 一致
  - copy 上の `patch -p1 --dry-run --forward`: accepted
  - `/tmp` fixture: 削除確認済み
- driver self-check: rc=0
  - verdict、row structure、liveness: 正例 accepted／負例 rejected
  - compile JSON: 正例 accepted／ycsb 欠落・重複 rejected
- `git diff --check`: rc=0
- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0

最終 status は許可された3ファイルが modified、親管理の既存未追跡 `output/insights/2026-08-05_t139-alt-x-probe/` が残っています。後者は非接触です。

### qsub 時の env

```text
IZANAGI_T139_EXPECTED_COMMIT=<3 probe file と canonical preregistration を含む40桁commit>
IZANAGI_T139_PREREGISTRATION_RELATIVE_PATH=output/insights/2026-08-05_t139-alt-x-probe/preregistration.md
IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=<直下に非symlink実directoryのgflags/glogを持つroot>
IZANAGI_THIRDPARTY_SOURCE_ROOT=<直下に非symlink実directoryのmasstree/mimalloc/googletestを持つroot>
```

`PBS_JOBID` と `PBS_O_WORKDIR` は scheduler 提供です。`IZANAGI_CONSUMER_COPY_WITNESS` は PBS 内部で生成・exportするため、親からは渡しません。

## 総括

H1・H2 は必要な実装と指定実走で `closed`。直列支配 cap は `3298秒`、既存 G2/G3/G5/G6/F1/F3/F7 の検査・受理条件は維持されています。