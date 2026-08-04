# Wave A campaign transport smoke

DW-G01 の生死確認専用である。Pegasus 計算ノードの 1 ジョブ内で、fixture から得た
planner / coder / auditor 提案を `drive_iteration(...)` へ直接渡す。まず leg A で
legacy+S2 の build 前 abort 予測を実機確認し、結果にかかわらず leg B で
build → legacy verify → bench の transport を試す。性能値の比較・主張には使わない。

これは **sanctioned な campaign 実行経路ではない**。恒久 driver、TASKS、transport policy、
既存の受理集合は変更せず、使い捨て証拠としてこの insight に凍結する。

## ファイル

- `smoke_driver.py`: compute site、明示 opt-in、競合 bench 不在を fail-closed に確認する。
  `FixtureRoleProvider` と `PARSERS` から 3 role の proposal を作り、先頭 workload 1 本を
  records=100,000、threads=4、extime=1、reps=2 で 2 脚の `drive_iteration` に渡す。
- `smoke_job.sh`: bnode と Python 3.10 を確認し、policy で pin された gflags / glog を
  node-local `$TMPDIR` に build/install し、numactl 実在証拠を採取してから driver を起動する。
  driver の rc を job rc にする。
- `README.md`: この再現契約と証拠の読み方を記録する。

## 8c CLI を使わない理由

`p3_autonomous_workload_trial.py` の CLI では `--provider fixture` と実 build が排他である
(brief N1)。さらに Pegasus compute 上の build opt-in は `claude-headless` provider 専用であり、
LLM transport receipt を要求する (brief N2)。その CLI を使うと fixture build は通らず、LLM を
有効にすると [T-276] の分割線に反する。このため provider CLI は呼ばず、fixture をコードとして
再利用して、素の proposal を受ける `drive_iteration` を直接呼ぶ。

## 再現

投入は親または人間が行う。この driver 自身は qsub しない。repo root から、未使用の `/work`
配下 directory を 1 回の job 専用に指定する。

```bash
repo=/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-a-transport-smoke
progress=/work/1/SFC/tanab/dev-wave-jobs/wave-a-transport-smoke/run-001
mkdir -m 700 "$progress"
cd "$repo"
qsub -v "IZANAGI_SMOKE_PROGRESS_DIR=$progress" \
  output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_job.sh
```

同じ progress directory は再利用しない。job script は project `SFC`、queue `gen_S`、1 node、
walltime 6:00:00 を要求する。従量 API key や LLM endpoint の環境変数は設定・参照しない。

## 証拠

- `job-progress.jsonl`: `job-start`、`deps-done`、`driver-start`、`driver-rc`、`job-end`。
- `compute-visible.json`: bnode hostname と PBS job id。
- `deps/`: policy、compiler、gflags / glog build/install、`CMAKE_PREFIX_PATH` の証拠。
  `numactl.command-v.stdout` は `command -v numactl` の解決結果（不在なら空）、見つかった場合の
  `numactl --hardware` / `--show` は各 stdout/stderr に残る。numactl 不在や各 probe の失敗は
  admission ではないため job を落とさない。
- `driver-progress.jsonl`: `driver-start`、`site-admitted`、`single-tenancy-ok`、
  脚ごとの `leg-start`、`fixtures-parsed`、`drive-iteration-start`、`leg-done`、最後の
  `driver-exit`。`leg-start` / `leg-done` は leg、verify_config、outcome、ran、例外情報を常に持つ。
- `drive-iteration-legA.log.jsonl` / `drive-iteration-legB.log.jsonl`: 各脚の build / verify /
  bench 内部から届いた log を 1 行ずつ fsync する。`leg-done.layout_root` は各 campaign WAL /
  report の所在を指す。

各 JSONL は append ごとに flush + fsync する。SIGKILL では次の marker は書けないため、最後に
残った marker が到達点である。leg A の abort / reject / 例外は記録するが rc に影響させず、必ず
leg B を試す。rc=0 は leg B が `ran=true` で、WAL 射影に `build_done`、`verify_done`、
`bench_done` がすべて残った場合だけである。leg B の `outcome` が `certified` か否かは rc に
影響させない。leg B が途中停止・例外なら非 0 とする。bench の数値は判定に使わない。

## 2 脚の分離

- leg A: `trial_id=wave-a-smoke-leg-a-<token>`、`verify=legacy+s2`。Pegasus 契約の
  `numactl=()` により build 前 abort が予測されるが、補正も成功扱いもしない。
- leg B: `trial_id=wave-a-smoke-leg-b-<token>`、`search_config` から `verify` key を削除した
  legacy 単独。leg B の計測直前にも競合 bench 不在を再確認する。

`CampaignConfig.trial` は campaign identity の hash 対象なので、異なる `trial_id` は別
campaign layout を作る。さらに A/B は `verify` key の有無も異なる。Pegasus の
`allow_resume=False` 契約下でも既存 layout の再利用にはならない。

## 既知の静的差分

brief N4 は Pegasus contract の `numactl=("numactl", "--interleave=all")` を前提にするが、
この worktree の `env_contract.py` では `pegasus.numactl=()` である。driver は空 command への
差し替えも `numactl` の補正もせず、`drive_iteration` が受理した契約をそのまま使う。leg A では
現行 gate の abort 原文を残し、leg B で gate を緩めず legacy transport を確認する。

## 失敗点と最後の marker

| 最後の marker / 証拠 | 主な停止箇所 |
|---|---|
| marker なし | progress 環境変数の未設定・空・非 `/work/`・改行、位置引数、作成/realpath 検査 |
| `job-start` | PBS 環境、TMPDIR、hostname admission |
| `compute-visible.json`、`deps-done` なし | interpreter、policy、dependency pin/build |
| `deps-done`、driver 側記録なし | driver 起動・引数・site gate |
| `site-admitted` | authority または共通準備の例外 |
| leg A `leg-start` | A の fixture、checkout、単独性 probe |
| leg A `drive-iteration-start` | A の build 前 numactl gate または campaign 内部。原文は A log / `leg-done` |
| leg A `leg-done` | B 開始前の予期しない driver 障害 |
| leg B `leg-start` | B の fixture、checkout、単独性再 probe |
| leg B `drive-iteration-start` | B の build / legacy verify / bench。詳細は B log と campaign WAL |
| leg B `leg-done`、`driver-exit` rc=1 | B の 3 段未完または例外 |
| leg B `leg-done`、`driver-exit` rc=0 | B の `ran=true` と 3 stage 完了。性能・認証の主張ではない |

marker が途中で途切れた場合は walltime 等の SIGKILL で、最後の fsync 済み marker が到達点である。
