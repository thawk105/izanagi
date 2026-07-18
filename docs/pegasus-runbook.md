# Pegasus 利用 Runbook

Pegasus で対話ジョブを起動し、PBS バッチジョブを投入・監視・終了するための運用手順。
Izanagi 固有の実験設計や完了状況は持たず、計算機上での操作だけを扱う。

## 0. 前提

- project: `SFC`
- **ログインノードは 3 台で、共通名は DNS ラウンドロビン。tmux・長期セッションはノード別。**
  共通名で入り直すと別ノードに着き、前回の tmux セッションが見えない (2026-07-16 に実際に発生)。
  個別 FQDN = `pegasus01/02/03.ccs.tsukuba.ac.jp` (130.158.240.1〜3、逆引きで実測) を使えば
  ノードを固定できる。手元の `~/.ssh/config` に `Host pegasus03` → `HostName
  pegasus03.ccs.tsukuba.ac.jp` を書いておくとよい。個別名への直接 SSH が塞がれている場合は
  共通名で入ってから内部で `ssh pegasus0N` してホップする
- 利用可能なキューは、ログインの都度 `qstat -Q` で確認する。キュー構成・権限は変わり得るため、
  この文書の列挙を正本にしない。クラスタ全体のキュー一覧は `pegasusinfo` に出る (自分が使えない
  キューも含む)
- 既知のキュー (2026-07-16 実測): バッチ (`qsub` 宛先) は `gen_S`、`gen_M`、`gen_L`。対話
  (`qlogin` 宛先) は `debug` (最大 1 時間)、`interactive` (最大 24 時間)。`gpu` は project
  `SFC` からは使えない (`qsub -q gpu` が `EACCESSDEN` で拒否されることを実測)。`gpu_low` と
  `edu-*` は `qstat -Q` に表示されず、アクセス可否は未検証
- GPU プログラムはログインノードで実行せず、割り当てられた計算ノード上で実行する。gen_S の
  計算ノード (bnode014) にも H100 が載っていることを `nvidia-smi` で実測した (他キュー・他
  node は未確認。§1 の node 仕様上は全 node 同構成)

全体の利用・混雑状況は次で確認する。

```bash
qstat -Q
pegasusinfo
```

## 1. 計算ノード仕様 (2026 年度)

| 項目 | 仕様 |
|---|---|
| CPU | Intel Xeon Platinum 8468 × 1 |
| physical core | 48 |
| HyperThreading | 無効 |
| DRAM | 128 GiB (ユーザー利用上限 約 115 GiB) |
| persistent memory | 2 TiB |
| GPU | NVIDIA H100 PCIe × 1 (80 GiB) |
| local NVMe | 約 5.4 TB (`/scr`) |

1 CPU、48 physical core、HyperThreading 無効の構成である。gen_S ではリクエストごとに CPU 48/48
の logical host が割り当てられ、事実上 node を埋める形になるが、キュー設定は
`Exclusive submit = OFF` であり**専有はスケジューラが保証するものではない** (`qstat -Qf gen_S`
で実測)。計測前の単独性確認は割り当てられたノード上で行う (§7)。各 node の GPU は H100 1 枚で
固定される。通常は CPU 数、メモリ量、GPU 枚数を個別指定する運用ではない。1 CPU 構成のため、
NUMA を意識する必要は基本的にない。

## 2. 短時間の対話ジョブ

デバッグや短時間の動作確認には `qlogin` を使う。`debug` と `interactive` は対話専用キューであり、
`qsub` でバッチ投入する先ではない (`debug` への `qsub` が `EWRNGTYP (Queue type is wrong)` で
拒否されることを実測。`interactive` は未検証だが `qstat -Q` 上は同じ対話型)。次は debug
キューで 10 分を要求する最小例。

```bash
qlogin \
    -A SFC \
    -q debug \
    -l elapstim_req=00:10:00
```

ノードが割り当てられると、プロンプトが概ね次の形に変わる。

```text
bnodeXXX$
```

この状態でコンパイル、テスト、GPU プログラムなどを実行する。終了時は計算ノード上で
`exit` を実行し、割り当てを解放する。

```bash
exit
```

長い処理や、端末切断後も継続すべき処理には `qlogin` ではなくバッチジョブを使う。

## 3. バッチジョブ

PBS directive を冒頭に持つシェルスクリプトを作り、ログインノードから `qsub` で投入する。

```bash
#!/bin/bash

#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:30:00

cd "$PBS_O_WORKDIR" || exit 1

./program
```

例えば上を `job.sh` として保存した場合は、次で投入する。

```bash
qsub job.sh
```

`qsub` は `Request <ID>.nqsv submitted to queue: gen_S.` の形式で request ID を返す。ID は状態確認と
削除に使うため記録しておく。ジョブ終了後、標準出力・標準エラーは投入時のディレクトリへ
`<script>.o<ID>` / `<script>.e<ID>` として戻り、標準エラー末尾には NQSV の会計サマリが付く
(2026-07-16 に gen_S で投入→完走を 1 回実測。このときは投入 7 秒後に開始した)。通常利用する
基本 directive は次の 3 つである。

```bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=HH:MM:SS
```

node 数を指定する場合は `-b` を使う。次は 2 node の例。

```bash
#PBS -b 2
```

リクエストは node 単位で割り当てられ (gen_S は CPU 48/48 固定、§1)、GPU も各 node 1 枚で
固定されるため、メモリ量や GPU 枚数を指定する PBS directive は通常不要である。

### ジョブの状態確認と削除

自分のジョブ一覧と、特定ジョブの詳細を確認する。

```bash
qstat
qstat -f <JOBID>
```

不要になった待機中・実行中ジョブは削除する。

```bash
qdel <JOBID>
```

## 4. モジュールとビルド

利用可能なソフトウェアとバージョンは実行時に確認する。

```bash
module avail
```

CUDA の既知の例 (2026-07-16 時点の実在版は 11.8.0 / 12.6.3 / 12.9.1 / 13.0.2。12.3.2 は無い):

```bash
module load cuda/12.6.3
nvcc sample.cu -o sample
```

MPI、コンパイラなどは `module avail` に表示された実在するバージョンを指定する。openmpi の版名は
`openmpi/5.0.10/gcc11.4.0-cuda12.6.3` のようにコンパイラ・CUDA を含む複合名である (実測)。

```bash
module load openmpi/<version>
module load intmpi/<version>
module load intel/<version>
```

再現可能性のため、性能計測ジョブではロードした module とバージョンをジョブログまたは実験の
環境メタデータへ残す。

## 5. 並列実行

### OpenMP

次はジョブ環境へ `OMP_NUM_THREADS=48` を渡す例。

```bash
#PBS -v OMP_NUM_THREADS=48
```

OpenMP は最大 48 threads を想定する。HyperThreading は無効で、1 CPU 構成のため NUMA を意識する
必要は基本的にない。

### MPI

OpenMPI の既知の実行例:

```bash
#PBS -T openmpi
#PBS -v NQSV_MPI_VER=<module version>

module load openmpi/<version>

mpirun ${NQSV_MPIOPTS} \
    -np 96 \
    -npernode 48 \
    ./program
```

この例は合計 96 process、1 node あたり 48 process なので、`#PBS -b 2` で 2 node を割り当てる。
`NQSV_MPIOPTS` はスケジューラが提供する値を変更せず渡す。`NQSV_MPI_VER` と `module load` には
同じ OpenMPI version を指定する。

MPI × OpenMP の hybrid 実行では、各 node について次を満たすようにする。

```text
MPIプロセス数 (1 node あたり) × OMP_NUM_THREADS <= 48
```

例えば 1 node で 4 MPI processes を使うなら、`OMP_NUM_THREADS` は最大 12 とする。

### GPU

GPU は各 node に NVIDIA H100 (PCIe、80 GiB) が 1 枚固定される構成である (§1)。実測は gen_S の
1 node (bnode014) で `nvidia-smi -L` により H100 PCIe ×1 を確認したのみ。ログインノードでは GPU
プログラムを実行せず、割り当てられた計算ノード上で実行する。`gpu` キューは project `SFC` からは
使えないため (§0)、バッチは gen 系キューを指定する。

```bash
#PBS -q gen_S
```

GPU 枚数を個別指定する PBS directive は通常不要である。複数 node を `-b` で要求した場合は、
node ごとに H100 1 枚が割り当てられる (§1 の構成から導かれる想定で、未実測)。

## 6. ストレージと quota

| 場所 | 用途 | 寿命・注意 |
|---|---|---|
| `/home/<project>/<user>` | 小さい設定、ソースなど | home 領域 |
| `/work/<project>/<user>` | 大きなデータ、ビルド、永続成果物 | 大容量データはこちらを優先 |
| `/scr` | 実行中ジョブのローカル一時領域 (約 5.4 TB) | 計算ノードのみに存在 (ログインノードには無い)。ジョブ終了時に削除される |

`/scr` に置いた必要な結果は、ジョブが終了する前に `/work/SFC/<user>` などの永続領域へ戻す。
最終成果物や唯一のコピーを `/scr` に置かない。計算ノードでは `/work` 配下が `/work/1/SFC/<user>`
のような実体パスで見えることがあるが、`$PBS_O_WORKDIR` を経由すれば意識しなくてよい (実測)。

quota とポイント残高は次で確認する。

```bash
check_quota
rbudgetcheck
```

### ファイル転送

ソースコードの取得・更新には `git clone` / `git pull`、通常のファイル転送には `rsync` または
`scp` を使う。大量データは中断後の再開や差分転送ができる `rsync` を推奨する。

## 7. Izanagi で使う場合

Pegasus は当面、ビルド・動作確認・デバッグ用の計算環境として扱う。対話セッションが動くのは
共有のログインノードであり、ビルド・テスト・ベンチなど重い処理は必ず `qlogin` / `qsub` で
確保した計算ノード上で行う。単独性確認 (pgrep・load average) は計測を走らせる計算ノード上で
行う — ジョブがノードを割り当てられても専有が保証されるわけではない (§1)。共有ログインノード
上の確認は他ユーザーのプロセスを拾って意味をなさない。正式な性能比較へ使うまでは、Pegasus
上の throughput を既存の `linux-baremetal` 測定値へ混ぜない。正式採用には次が必要になる。

1. Pegasus 専用の環境タグを決める
2. その環境で calibration と noise floor を取り直す
3. thread/process binding と要求 node 数を固定する
4. module、コンパイラ、CCBench pin、ジョブスクリプトを成果物から追跡可能にする

**env contract 登録段の要件 (2026-07-18、F4 裁定 + wave3 実装の帰結):** v2 計測経路
(floor / oracle) で Pegasus を使うには `orchestrator/campaign/env_contract.py` の registry へ
Pegasus entry を追加する。追加には上記 1〜4 (D59) に加えて次を要する。

- calibration 成果物は `calibration_ref {path, sha256}` の構造化参照で束縛する (自由文不可)。
  env_tag の値はユーザーが確定する
- **calibration / clocks_per_us / noise floor は割り当て計算ノード (bnodeXXX) 上のジョブで取得する。
  ログインノード (pegasus0X) の値は計測環境でないため使わない** (2026-07-18 ユーザー指摘)。全 node
  同構成 (§1) を前提に env_tag は単一で足りるが、計算ノードは割当ごとに変わり専有も保証されない
  (Exclusive submit=OFF) ため、その前提を実行時に検証する **実測照合 attestation を Pegasus では
  必須**とする (下記 enforcement の「実環境 attestation」を暫定の env_tag 文字列 machine-pin から
  格上げ)。照合対象 = CPU model / 実効クロック / core 数 / cache / NUMA が登録契約と一致するか、
  floor・oracle 実行直前に検査し不一致 = fail-closed。calibration の取得場所と実行時照合を登録段で
  同時に設計する
- `isolation_policy` は single_process=True / allow_resume=False で登録する (G12: campaign を
  単一 allocation/node/process で完遂。walltime 不足・途中 kill は WAL を証拠として保存した上で
  全数値を不採用にする)
- 登録時に実装が必要な enforcement (wave3 時点では**未実装**と記録): 残 walltime の事前予約検査 /
  WAL・成果物の永続領域 allowlist (resolved path で検査、`/scr` 拒否) / PID 可視性の canary
  probe / build cache の contract_sha256 による namespace 分離 / 実環境 attestation
  (契約値と実機の実測照合)
- テスト側 `ENV_LITERAL_VALUES` (orchestrator/tests/test_env_contract.py) へ新 env の値を追加する
  (registry↔禁止 literal の同期 assert が更新漏れを機械検出する)
- floor driver は暫定 machine-pin (`contract.env_tag == p2_2.ENV_TAG`) を持つ。これは attestation
  導入までの取り違え防止 gate であり、Pegasus 実行にはこの pin の扱いを登録段で同時に設計する

Izanagi の性能計測では、trace-enabled の正しさ検証と trace-disabled の性能測定を別 build・別 run
にする。CCBench は共有 submodule を直接変更して実行せず、orchestrator が pinned-clean を確認する
既存の隔離・評価経路を使う。計測機と環境タグの現行方針は `docs/roadmap.md` §5 および
`docs/orchestrator-design.md`「環境タグ」を正本とする。

## 8. 投入前チェックリスト

- `qstat -Q` で現在利用可能なキューを確認した
- `pegasusinfo` で混雑状況を確認した
- wall time と node 数 (`-b`) が処理に適切である
- OpenMP threads は 48 以下である
- hybrid 実行は node あたり `MPI processes × OMP_NUM_THREADS <= 48` である
- GPU プログラムやビルド・テスト・ベンチ等の重い処理をログインノードで実行していない
- 単独性の確認 (pgrep 等) は、割り当てられた計算ノード上で行う (割当てを専有の保証と見なさない)
- `/scr` に置くデータの退避処理がある
- `check_quota` と `rbudgetcheck` で容量・ポイント残高を確認した
