# Pegasus 利用 Runbook

Pegasus で対話ジョブを起動し、PBS バッチジョブを投入・監視・終了するための運用手順。
Izanagi 固有の実験設計や完了状況は持たず、計算機上での操作だけを扱う。

## 0. 前提

- project: `SFC`
- 利用可能なキューは、ログインの都度 `qstat -Q` で確認する。キュー構成は変わり得るため、
  この文書の列挙を正本にしない
- 既知のキュー: `debug` (最大 1 時間)、`interactive` (最大 24 時間)、`gen_S`、`gen_M`、
  `gen_L`、`gpu`
- GPU プログラムはログインノードで実行せず、`debug`、`gpu`、または `interactive` キューで
  割り当てられた計算ノード上で実行する

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
| GPU | NVIDIA H100 × 1 (80 GiB) |
| local NVMe | 約 5.4 TB (`/scr`) |

1 CPU、48 physical core、HyperThreading 無効の構成である。1 job が 1 node を占有し、各 node の
GPU は H100 1 枚で固定される。通常は CPU 数、メモリ量、GPU 枚数を個別指定する運用ではない。
1 CPU 構成のため、NUMA を意識する必要は基本的にない。

## 2. 短時間の対話ジョブ

デバッグや短時間の動作確認には `qlogin` を使う。次は debug キューで 10 分を要求する最小例。

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
#PBS -q gpu
#PBS -l elapstim_req=00:30:00

cd "$PBS_O_WORKDIR" || exit 1

./program
```

例えば上を `job.sh` として保存した場合は、次で投入する。

```bash
qsub job.sh
```

`qsub` が返す job ID は、状態確認と削除に使うため記録しておく。通常利用する基本 directive は
次の 3 つである。

```bash
#PBS -A SFC
#PBS -q gpu
#PBS -l elapstim_req=HH:MM:SS
```

node 数を指定する場合は `-b` を使う。次は 2 node の例。

```bash
#PBS -b 2
```

1 job が node を占有し、GPU も各 node 1 枚で固定されるため、メモリ量や GPU 枚数を指定する
PBS directive は通常不要である。

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

CUDA 12.3.2 の既知の例:

```bash
module load cuda/12.3.2
nvcc sample.cu -o sample
```

MPI、コンパイラなどは `module avail` に表示された実在するバージョンを指定する。

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

GPU は各 node に NVIDIA H100 80 GiB が 1 枚固定されている。ログインノードでは GPU
プログラムを実行せず、`debug`、`gpu`、または `interactive` キューで割り当てられた計算ノード上で
実行する。バッチの通常例は `gpu` キューを指定する。

```bash
#PBS -q gpu
```

GPU 枚数を個別指定する PBS directive は通常不要である。複数 node を `-b` で要求した場合は、
node ごとに H100 1 枚が割り当てられる。

## 6. ストレージと quota

| 場所 | 用途 | 寿命・注意 |
|---|---|---|
| `/home/<project>/<user>` | 小さい設定、ソースなど | home 領域 |
| `/work/<project>/<user>` | 大きなデータ、ビルド、永続成果物 | 大容量データはこちらを優先 |
| `/scr` | 実行中ジョブのローカル一時領域 | ジョブ終了時に削除される |

`/scr` に置いた必要な結果は、ジョブが終了する前に `/work/SFC/<user>` などの永続領域へ戻す。
最終成果物や唯一のコピーを `/scr` に置かない。

quota とポイント残高は次で確認する。

```bash
check_quota
rbudgetcheck
```

### ファイル転送

ソースコードの取得・更新には `git clone` / `git pull`、通常のファイル転送には `rsync` または
`scp` を使う。大量データは中断後の再開や差分転送ができる `rsync` を推奨する。

## 7. Izanagi で使う場合

Pegasus は当面、ビルド・動作確認・デバッグ用の計算環境として扱う。正式な性能比較へ使うまでは、
Pegasus 上の throughput を既存の `linux-baremetal` 測定値へ混ぜない。正式採用には次が必要になる。

1. Pegasus 専用の環境タグを決める
2. その環境で calibration と noise floor を取り直す
3. thread/process binding と要求 node 数を固定する
4. module、コンパイラ、CCBench pin、ジョブスクリプトを成果物から追跡可能にする

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
- GPU プログラムをログインノードで実行していない
- `/scr` に置くデータの退避処理がある
- `check_quota` と `rbudgetcheck` で容量・ポイント残高を確認した
