指定 3 ファイルだけを修正し、commit・docs/output 編集・qsub/qstat は行っていません。既知の実装不備は残していませんが、dev-wave 実装子契約に従い、計算ノード/PBS E2E 未実走の所見は `partial` としています。

### G1〜G6 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| G1 共有 liveness 起点 | `partial` | `TxExecutor::begin()` の non-thread-local magic static を共有起点にし、thread-local は報告済み bit のみに限定。[patch:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:70)、[patch:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:84)、[patch:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:112)。固定 `[0,1500ms)` / `[1500,3000ms)`、3000ms 以後無出力。patch dry-run は緑、C++ build/liveness 実走は未実施。 |
| G2 qsub 時点 commit 束縛 | `partial` | 必須 `IZANAGI_T139_EXPECTED_COMMIT` と job 開始時 HEAD を exact 比較し、一致後だけ同 commit を `cat-file` 展開。[PBS:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:46)、[PBS:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:64)、[PBS:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:105)。scheduler queue drift E2E は未実施。 |
| G3 canonical prereg gate | `closed` | repo 相対 path 全体の literal exact 比較へ変更し、本文 literal 検査を維持。[PBS:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:101)、[PBS:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:122)。canonical 正例 accepted、旧 basename 負例 rejected を実走。 |
| G4 Git object snapshot | `partial` | source ごとの単一 cap 内で pin/clean 検査後、third-party/CCBench を一時 indexの `read-tree "$pin"` + `checkout-index` から生成。[PBS:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:157)、[PBS:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:193)、[PBS:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:252)、[PBS:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:275)。CCBench pin に対する object checkout はローカル実走成功、全 6 source の PBS E2E は未実施。 |
| G5 早期 terminal state | `partial` | `OUT` 確定直後に `run_commit=unavailable` と EXIT trap を設置し、その後に必須 env/HEAD 検査。[PBS:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:8)、[PBS:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:15)、[PBS:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:39)。必須 env 欠落を実走し、rc=2、pre-performance state、`run_commit=unavailable` を確認。HEAD timeout 実走は未実施。 |
| G6 timeout 総和 | `closed` | source 検査と snapshot を単一 cap に集約し、直列支配 cap を3238秒へ再配分。[PBS:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:304)、[driver:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:367)。実算 assert 成功。 |

### G6 cap 実算

- repo identity/status/index: `10 + 3 + 10 + 10 = 33`
- commit blob 5本: `5 × 5 = 25`
- dependency policy: `10`
- dependency snapshot: `2 × 45 = 90`
- third-party policy: `10`
- third-party snapshot: `3 × 50 = 150`
- CCBench gitlink: `10`
- CCBench snapshot: `90`
- dependency build/install: `60 + 120 + 30 + 60 + 120 + 30 = 420`

前段は `838` 秒です。

driver 内部は `copy/patch 150 + build/receipt 1500 + liveness 180 + performance 450 = 2280` 秒、外枠 cap は `2400` 秒です。したがって直列支配 cap は:

`838 + 2400 = 3238 ≤ 3300`

absolute deadline まで62秒、PBS walltime 3600秒まで362秒の余裕があります。

### qsub 時に渡す env

- `IZANAGI_T139_EXPECTED_COMMIT=<40桁commit>`
  - 3 probe file と canonical preregistration を統合した、投入対象 commit。
- `IZANAGI_T139_PREREGISTRATION_RELATIVE_PATH=output/insights/2026-08-05_t139-alt-x-probe/preregistration.md`
  - この literal 以外は拒否。
- `IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=<root>`
  - 直下に clean/pinned な非symlink実 directory `gflags`、`glog` を持つ root。
- `IZANAGI_THIRDPARTY_SOURCE_ROOT=<root>`
  - 直下に clean/pinned な `masstree`、`mimalloc`、`googletest` を持つ root。

`PBS_JOBID` と `PBS_O_WORKDIR` は scheduler 提供値です。

### 検査結果

- driver / PBS `bash -n`: rc=0
- CCBench一時コピーへの `patch -p1 --dry-run --forward`: rc=0
- 一時コピー: 削除確認済み
- driver self-check: rc=0
  - verdict、row structure、liveness: 正例 accepted / 負例 rejected
  - compile JSON: 正例 accepted / ycsb欠落・重複 rejected
- early trap fixture: rc=2、pre-performance state、`run_commit=unavailable`
- Git object checkout fixture: CCBench pin `d706650cdb31e442bef45b9b4216951d4fb40969` で成功、一時物削除済み
- `git diff --check`: rc=0
- 最終 status: 指定3ファイルのみ modified。親管理の未追跡 `output/insights/2026-08-05_t139-alt-x-probe/` は非接触

自己申告する残余リスクは、5秒の blob cap・60秒の copy capが極端に遅い filesystem で infra timeoutになり得ること、CCBench build/PBS E2E未実施のためC++コンパイルや全source snapshot統合の回帰余地が残ることです。受理集合、既存期待値、docs、policy、submodule本体は変更していません。

## 総括

G1〜G6の実装修正はすべて投入済みで、`regressed` は0件です。G3・G6は `closed`、G1・G2・G4・G5は実装完了ながら計算ノード/PBS E2E未実走のため契約上 `partial` と報告します。