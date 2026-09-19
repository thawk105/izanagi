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

**cgroup による per-job の資源境界は無い (2026-09-09 実測、request `986762.nqsv`、3 ノード、[T-2486])。**
rank process が入るのは per-job cgroup ではなく、node ごとに job 間で共有する NQSV service の
cgroup である (非 head rank は `/system.slice/nqs-jsv.service`、job 番号 0 の head は
`/system.slice/nqs-lchd.service`)。**head から兄弟ノードへ張った ssh session はそこには入らず、
systemd の login session scope (`/user.slice/user-<uid>.slice/session-<N>.scope`) に入る** —
rank が生きているノードでも同じで、rank の終了とは無関係である。採取した PBS 環境変数も
ssh session には継承されない。cpuset と task affinity はどちらの側も全 48 CPU だが、
`memory.max` と `pids.max` の上限文脈は非対称である。詳細と生記録は
`output/insights/2026-09-09_t2486-ssh-cgroup-equivalence/README.md`。
**これは実行場所分類 (§7.0) の実測ではなく、`admission_registry.json` の class 根拠にしてはならない。**

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

### Python の interpreter は `python3.10` を明示する (2026-08-03 実測)

**`python3` が 3.10 未満に解決されるノードがある。** izanagi は 3.10 の構文
(`@dataclass(..., slots=True)`、`match`) を使うため、そのまま呼ぶと
`TypeError: dataclass() got an unexpected keyword argument 'slots'` や
`SyntaxError: invalid syntax` で落ちる。実測値は次のとおりで、**計算ノードだけの問題ではなく
ノードと PATH に依存する**。

| ノード | `python3` | `python3.10` |
|---|---|---|
| 計算ノード (`bnode005` 等) | 3.10 未満 | `/bin/python3.10` = 3.10.12 |
| login `pegasus02` | 3.10 系 | 同上 |
| login `pegasus03` | `.../oneapi/.../intelpython/latest/bin/python3` = **3.9.13** | `/usr/bin/python3.10` = 3.10.12 |

login ノードでは oneAPI の intelpython が PATH 前方に入りうるため、**ノードを跨いだセッションでは
毎回 `python3 -V` を確認する**。repo の tool を手で叩くときは `python3.10` を明示する。

`tools/pegasus/dispatch_compute.py` はこれを内側で吸収しており、`_INTERPRETER_CANDIDATES`
(`python3.10` を優先) で interpreter を選び、`PATH` の先頭へその dirname を足してから子を起動する。
**したがって pytest は `tools/run_tests.py` に任せ、ログインノードから自動 dispatch させるのが
正規経路である。**

生 `qsub` でバッチを書く場合は、同じ吸収を自分で行う。interpreter を `python3.10` に固定するだけでは
不十分で、**孫 process が `PATH` の `python3` を拾う**ため、`python3` → `python3.10` の shim を
`PATH` 先頭へ置く必要がある。実測では、固定なしで 116 failed / 2,085 errors、interpreter 固定だけで
19 failed、shim まで置いて 5,226 passed / rc=0 だった (経緯と request ID は失敗台帳)。

`-o` / `-e` は既定で投入時ディレクトリへ `<script>.o<ID>` / `<script>.e<ID>` として落ちる。
worktree から投入するときは絶対パスを明示し、worktree root を untracked ファイルで汚さない。

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

#### `qstat` の読み方で踏みやすい罠 (2026-08-26 実測、[T-1852])

- **`qstat` は存在しない request に対しても終了コード 0 を返す。** `-f` / `-J -f` / `-T` の
  いずれも rc=0 で、本文だけが `does not exist` と述べる。
  **存在判定を rc で書くと常に「在る」になる。** 本文で判定する。
- **投入直後、job record が作られる前の窓では `qstat -J -f` が `does not exist` を返す。**
  同じ時刻に `qstat -f` は request を `Current State = Queued` で返している。
  「まだ始まっていない」と「もう消えた」を `-J -f` だけでは区別できない。
  request 単位の `qstat -f` を併せて見る。
- **終了した request は約 5〜6 秒で `qstat` から消える。** 終了 status
  (`Exit Code`) と `State Transition Reason` が見えるのはこの窓の中だけで、
  終了後に取りに行く履歴照会 command はこの scheduler に無い。
  終端の記録が要る処理は、job の終了時刻に張り付いて観測する。
- **`Exit Code` は事由ではなく `wait(2)` status の 16 進表記である。**
  実行時間超過も実行中の `qdel` も同じ `9` を返す。値・意味の対応表と未観測の範囲は
  `output/insights/2026-08-26_t1852-nqsv-exit-code-mapping/RESULT.md`。
- 警告値付きの経過時間制限は**引用符を qsub の argv まで届ける**必要がある。shell から呼ぶなら
  `-l 'elapstim_req="HH:MM:SS,HH:MM:SS"'` と外側を single quote で括る
  (`-l elapstim_req="..."` は shell が引用符を外すため `Invalid syntax following -l flag.`
  で rc=1 になり投入されない)。job script の directive に書くなら
  `#PBS -l elapstim_req="HH:MM:SS,HH:MM:SS"`。
  失敗と成功の逐語は上記 insight の
  `evidence/qstat-qsub-behaviour-verbatim.md`。

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

python の既知の乖離 (2026-07-28、job `0:873200.nqsv` で実測): 計算ノードでは module
`intelpython/2022.3.1` が既定ロードされ、`python3` が Intel Python 3.9.13 に解決される。
ログインノードの `python3` は 3.10.12。計算ノードにも `/usr/bin/python3.10` (3.10.12) が実在し、
版付き名で解決できる (job `0:873225.nqsv` で実使用を確認)。
Python 3.10+ を要するジョブは `python3.10` のような版付き名で解決するか、
実行前に版数を検査して fail-closed にする (floor job は候補列 + 版数 gate で対応済み)。

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
**この 2 つはログインノードでも同じ木である** — `/work/SFC/<user>` は `/work/1/SFC/<user>` へ
解決される (2026-08-27 実測)。file system を走査する道具へ両方を別々の探索根として渡すと、
同じ file を二度走査する。走査根を列挙するときは `readlink -f` で畳んでから渡す。

quota とポイント残高は次で確認する。

```bash
check_quota
rbudgetcheck
```

### ファイル転送

ソースコードの取得・更新には `git clone` / `git pull`、通常のファイル転送には `rsync` または
`scp` を使う。大量データは中断後の再開や差分転送ができる `rsync` を推奨する。

### third-party source の永続 cache (2026-08-04, [T-340])

CCBench の FetchContent 依存 (masstree / mimalloc / googletest) は **repo の外**に置く。
worktree 配下に置くと畳んだ時点で実体が消えるためである。本機での値は次のとおり。

```bash
export IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache
```

取得・供給の手順は `tools/pegasus/README.md` §6 を正本とする。**2026-09-16 以降、この helper は
FetchContent 3 本に加えて gflags / glog も同じ cache へ取得し、同じ staging root へ hydrate する
(計 5 本)。** gflags / glog の所在の正本は policy.json の `gflags_source_url` / `glog_source_url` と
`*_expected_head` (url + 40 hex pin) で、機体固有の絶対 path は repo に無い。job body は
staging root 配下の `gflags` / `glog` から使い捨て static build する。**job を投げる前に
`hydrate` を済ませておく** (計算ノードは外部ネットワークを持たない)。

**directory の create-only publish に `renameat2(RENAME_NOREPLACE)` は使えない** — `/home` だけで
なく **`/work` でも EINVAL** である (2026-08-04 実測)。`os.link` は directory に EPERM なので
calibrator の link+unlink fallback も使えない。`os.mkdir` による排他予約 + `os.rename` を使う。

## 7. Izanagi で使う場合

Pegasus は当面、ビルド・動作確認・デバッグ用の計算環境として扱う。対話セッションが動くのは
共有のログインノードである。

> **現行方針 (2026-08-06 ユーザー裁定、[T-300])。** **性能測定 — ベンチ・calibration・noise floor・
> floor / oracle の本走 — は、余裕の有無にかかわらず計算ノードで行う。** それ以外
> (テスト・ビルド・provenance 履歴監査) は、**ログインノードの空きメモリが足りればログインノードで
> 実行する。足りなければ計算ノードへ投げる。** 判定量はユーザーが指した「合計メモリ使用量」
> (`/work/SFC/tanab/scripts/memwatch.sh` が表示する user slice の `memory.current`) で、
> per-user 上限 16 GiB に対し**天井は 14 GiB** とする。
> **`qstat -Q` で対象 queue が `DIS` / `INA` なら投げても実行されないので投げない** — その場合は
> ログインノードで実行し、余裕も無ければ「いまは実行できない」として止める。性能測定なら
> 「いまは測定できない」と判断する。この裁定は 2026-07-30 の「重い処理はログインノードで
> 走らせない」を**非計測面について supersede** する (計測面は不変)。
> 実装は `orchestrator/campaign/login_headroom.py` (観測・予約・予算) と
> `orchestrator/campaign/queue_state.py` (キュー可用性) が正本で、数値定数は前者に 1 箇所だけ置く。

**以下は 2026-07-30 裁定に基づく旧記述であり、上の裁定で置き換わった部分がある。**
**重い処理 — ビルド・テスト (pytest スイートの全走と部分走を含む)・
ベンチ・calibration・noise floor・floor / oracle の本走・provenance 履歴監査
(`tools/check_ai_provenance.py`) — はログインノードで走らせず、
`qlogin` / `qsub` で確保した計算ノード上で行う** (2026-07-30 ユーザー裁定。2026-07-27 の
「ビルドとテストはログインノードで走らせてよい」を再反転したもの)。
**計算ノードでは割り当てられた資源を最大限使い、最大並列で回す** (同裁定)。射程は
**テストの既定並列度と build の `-j` 既定の両方**である — 計算ノードでは affinity 全数、
非 Pegasus では従来値 (テスト cap 32 / build `-j 16`) を保つ。明示 `-n` / `jobs=` は後勝ちで尊重する
(§8 と D103 決定 4)。ログインノードに
残してよいのは編集、静的検査、docs 検査、スケジューラ操作 (`qsub` / `qstat` / `qdel`)、および
`--message-file` の commit 前 preflight だけである。**`tools/check_ai_provenance.py` の履歴監査は
「静的検査」ではない** — 1 回で git subprocess 約 3000 本・130〜150 秒を共有ノードに載せるため、
checker 自身が計算ノードへ自動 dispatch する (D105)。

### 7.0 判定基準はディレクトリではなくメモリ量 (2026-08-01 ユーザー裁定)

上の列挙は**現時点で判明している重い処理**であって閉じた一覧ではない。新しいスクリプトや既存
スクリプトの入力増大は列挙に載らないまま重くなるため、**どこに置かれているか (`tools/` 配下か等)
ではなく、どれだけメモリを使うか**で判定する。

#### 7.0.0 実行場所の自動判定 ([T-300]、2026-08-06)

判定は 2 次元 (空きメモリ × キュー可用性) で行い、`tools/run_tests.py` と
`tools/check_ai_provenance.py` が起動時に自分で決める。

| ログインの空き | キュー | 判定 |
|---|---|---|
| 足りる | 使える / 不明 | ログインノードで上限付き実行 |
| 足りる | 使えない | 同上 |
| 足りない | 使える / 不明 | 計算ノードへ dispatch (従来経路) |
| 足りない | 使えない | 取れるだけの枠で試み、当たったら**投げずに停止** |

- **判定量 = user slice の回収不能メモリ量。** 天井は 14 GiB
  (`login_headroom.CEILING_BYTES`。数値はこの 1 箇所だけに置く)。
  回収不能量 = 基準値 − clean file cache − 回収可能 slab で、clean file cache は `file` から
  `shmem` / `file_dirty` / `file_writeback` / `unevictable` を引いた残り。基準値は
  `memory.stat` の前後で読んだ `memory.current` の大きい方とし、差の結果は `anon + shmem` を
  下回らせない。`slab_reclaimable` または `unevictable` が読めない環境と snapshot 不整合では
  基準値そのもの (従来相当の保守判定) へ degrade する。**ファイルキャッシュが溢れることは
  問題としない** (ユーザー裁定)。既存 5 キーが読めない観測失敗は従来どおり必ず dispatch。
- **1 コマンドへ渡す予算** = `min(4 GiB, 天井 − 判定量 − 生存中の予約 − 予備 2 GiB)`。
  予備 2 GiB は**暫定値で実測根拠が無い**。予算が 1 GiB を割れば dispatch。
- **予約台帳**は `/run/user/<uid>/izanagi-admission/` (repo 外・tmpfs)。同時要求は互いの予約を
  見て減額されるので、`現在使用量 + Σ予約` が天井を超えない。**repo へは実行状態を書かない**
  ので git 差分衝突は起きない。死んだ予約と旧 schema record は自動回収する。
- **実行は上限付き cgroup scope で囲う** (`systemd-run --user --scope` の `MemoryMax` /
  `MemorySwapMax=0` と、child 自身が書く `memory.oom.group=1`)。**見積もりが外れても被害は
  その scope に閉じる**。`MemoryOOMGroup` は systemd 249 では transient property として
  受理されないので child が自分で書く (2026-08-06 実測)。
- **前回の観測ピークを操作ごとに記録し、次回の見積もりに使う。** 前回 cap に当たった操作は
  次回 local を試さず即 dispatch する。key は対象集合から決定的に導く。
- **cap 到達後の自動 fallback は、local 試行の前後で tree と submodule の指紋が変わっていない
  ときだけ**行う。「tree が clean か」で判定してはならない — 開発中の tree はほぼ常に dirty で、
  それでは通常の開発が止まる ([T-300] で実測)。
- 実行場所を確定させたいときは `--force-dispatch` を明示する。判定を迂回して従来の dispatch
  経路をそのまま通る。
- **性能測定はこの判定の対象外**で、常に計算ノードで行う。計測 producer 自身が site を検査し、
  build cache が hit していてもログインノードでは起動も記録もしない (絶対規律 1)。

- **判定量** = その 1 回の実行で、同時に生きる全子孫を含む **cgroup の charged memory のピーク**。
  `/usr/bin/time -f %M` の per-process ピーク RSS を代理値にしてはならない — 多重プロセスを
  worker 数分の 1 に過小評価し、共有ページを二重計上し、file / slab / page table の charge を落とす。
- **測り方 (この機体で実行可能な手順)。** **`memory.peak` はこの kernel (5.15) に存在しない**
  (2026-08-01 実測)。したがって共有 user slice の `memory.current` を読むのではなく、
  **専用 scope を作ってその scope の `memory.current` を sampling する**。

  unit 名を自分で決め、sampler を先に張ってから測る command を起動する (別 shell から PID を
  探す方式は、短命な command に間に合わない)。

  ```bash
  UNIT=izmeas-$$                      # 自分で決める → cgroup path が確定する
  CG=/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/app.slice/$UNIT.scope
  ( until [ -r "$CG/memory.current" ]; do :; done          # 開始 barrier
    max=0; while [ -r "$CG/memory.current" ]; do
      v=$(cat "$CG/memory.current" 2>/dev/null || echo 0)
      [ "$v" -gt "$max" ] && max=$v; done
    echo "$max" > peak.txt ) &                              # busy sampler (間隔 << 1 ms)
  systemd-run --user --scope -q --unit="$UNIT" -p MemoryAccounting=yes -- <測る command>
  wait; cat peak.txt
  ```

  専用 scope なので他 session・並走 job の charge が混ざらない。**この手順の既知の限界**:
  sampling である以上、sample 間隔より短いスパイクは取り落とす。1 秒未満で終わる command は
  **3 回以上繰り返して最大値**を採り、それでも取り落としは margin で吸収する (下記)。
  sampler が cgroup を開く前に command が終わると `peak.txt` が 0 になる — **0 は
  「軽い」ではなく測定失敗**として扱い、`unknown` に倒す。
- **記録すること**: commit、argv、入力の総 bytes と件数、`memory.max`、観測ピーク、繰り返し数、
  測定日。**certified peak = 観測ピーク + `max(25%, 128 MiB)`** とし、
  **規範値と比較するのは certified peak のほう**である (観測ピークではない)。
- **規範値 = 512 MiB。これは実測から導いた最適値ではなく、暫定の分類値である。**
  現時点で根拠になっているのは「実測済みの軽量 tools 群 (per-process RSS で 13〜30 MB) と、
  既に dispatch 済みの 2 本 (pytest 全走・provenance 履歴監査) の間に置いた」という分離だけで、
  **どちらの群も上の手順では測り直していない**。ログインノードの per-user cgroup 上限は
  16 GiB・swap 0 で、複数 session と並走 job がこの 1 つの上限を共有する。
  **「規範値 × 同時実行数」で安全域を見積もってはならない** — 規範値は下限であって上限ではなく、
  1 本が 4 GiB でも「規範値以上」を満たす。値の確定はこの手順での再測定を待つ。
- **分類は 3 値。** `local-ok` = 上の測り方で実測して規範値未満、`dispatch-required` = 規範値以上、
  `unknown` = 未計測、または入力サイズに上限が無く実行ごとに変わる。
  **`unknown` は `dispatch-required` と同じに扱う** — 測っていないものを軽い側へ倒さない。
  **例外が 1 つある。** registry の `local-ok` のうち evidence が `legacy-admitted` のものは、
  この定義を**満たしていない** — 実測されないまま以前から許可されていた 4 本であり、
  2026-08-05 のユーザー裁定で grandfather として追認したものである ([T-522])。
  したがって「`local-ok` と書いてあるから実測済み」と読んではならない。判定には evidence を見る。
- **測定が保証するのは記録した argv と入力だけである ([T-482] 択 (a))。** 上の手順は
  「その 1 回の実行」を測る。したがって分類は**そのとき測った既定 argv と入力**に対してのみ有効で、
  同じ path を別 argv・別入力で呼んだときの資源量を保証しない。`hooks/guard_bash.py` の admission は
  **path 粒度**なので、許可された path が任意 argv で規範値未満であることは意味しない。
  pin・入力・cap が変わったら測り直す。argv / env を含む admission と CLI 側の入力 cap の比較は
  [T-482] (b)(c) として裁定待ちに残る。
- **admission registry と証拠クラス。** 実行体をログインノードで
  実行してよいかの判定は **`tools/pegasus/admission_registry.json` が正本**で、path ごとに 3 値の
  class と `reason` / `primary_gate` / `evidence` を持つ ([T-522])。`hooks/guard_bash.py` と
  `tools/check_docs.py` は、共有 validator (`tools/pegasus_admission_registry.py`) を通した
  **投影**であって正本ではない。拒否の射程はちょうど次の 2 つで、それ以外は素通りする。
  (i) **registry に exact 登録された path のうち class が `local-ok` でないもの** —
  repo 内のどこにあってもよい ([T-639])。(ii) **`tools/pegasus/` 配下の未登録 path**
  (subdirectory を含む)。**未登録 = 拒否の閉包はこの subtree にだけ残る**のであって、
  `tools/pegasus/` 外の未登録 path は従来どおり通る — 全 tool の分類完備は目指さない
  縮小版だからである。**許可するのは `local-ok` だけ**という原則は (i) の内側で変わらない。
  **`tools/pegasus/` の外に登録できるのは deny 側の class (`unknown` / `dispatch-required`) だけ**で、
  非 `tools/pegasus/` の `local-ok` は loader と hook の双方が拒否する。この制約により、
  適用 path を広げても受理集合は単調に縮むだけになる。
  **この「拒否する」の射程は、正しく `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` と判定された上で、
  hook の parser が実行 target と認識した綴りに限られる。** `python3 -c`、cwd 相対で組み立てた path、
  変数展開、未解析 launcher、script file 越しの実行は原理的に見えない (F121 の残穴。[T-518])。
  **Claude Code の Bash tool 以外の実行面 — Codex 子、ユーザー端末・IDE・cron、subprocess の内側 —
  もこの gate の外である。** 適用 path を広げてもこの限界は変わらない ([T-639] で裁定へ返した)。
  正本が読めない・schema に反する・未知の class を含むときは、hook は空 registry へ縮退し
  `tools/pegasus/` 配下を**すべて拒否する** (fail-closed)。**縮退時も、hook が静的に持つ
  非 `tools/pegasus/` の登録 path (fallback 投影) は拒否側に倒れる。** この異常時には現在 `local-ok` の 5 本も
  拒否されるため、単調性 (D175 決定 6) の射程は**正常系 (valid canonical registry) に限られる**。
  `evidence` は現在 2 種類ある — 本節の手順で実測したもの (`fetch_third_party.py`) と、
  **本節の手順で測られないまま以前から許可されていたもの (`legacy-admitted`)** である。
  後者を「実測済み」と読み替えてはならない。**未実測の 4 本は grandfather として追認済みで
  (2026-08-05 ユーザー裁定)、`class` は `local-ok` に据え置き、`evidence` も
  `legacy-admitted (未実測)` のまま残す。** 実測して変わるのは `evidence` であって class ではない。
  この grandfather は当該 4 本限りの例外であり、他の entry を `local-ok` にするには下の手番手順
  での実測が要る。`legacy-admitted` を他 entry の許可根拠に流用しない。
- **正本の投影表 (機械検査対象)。** 次の表は `tools/pegasus/admission_registry.json` の
  (path, class, evidence) を投影したものである。`tools/check_docs.py` が正本との集合完全一致を
  検査するので、**この 3 つの値のどれかを片方だけ編集すると赤になる**。値を変えるときは正本を先に直す。
  **`reason` と `primary_gate` は投影しておらず、片方だけ変えても赤にならない** ([T-522] で裁定へ返した)。

| path | class | evidence |
|---|---|---|
| `tools/claude_session_ledger.py` | `unknown` | `compute-node shared-service cgroup delta sampling at commit 04d85f93 (not runbook 7.0 isolated-scope evidence; non-certifying); default --json argv, 25 of 1045 files read, 4728545 bytes, limit_reached; 5 positive-delta samples of 6, all command rc=2; max +19.7 MiB, +128 MiB margin = 147.7 MiB` |
| `tools/pegasus/a5_second_boot_backoff_sweep.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/acceptance_nproc_study.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/b10_backoff_grid.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/b10_backoff_shape_campaign.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/certify_calibration.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/collect_receipt.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/collect_t126_qualification.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/dispatch_compute.py` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/exec_calibrate.py` | `dispatch-required` | `static arbitrary-exec classification` |
| `tools/pegasus/fetch_third_party.py` | `local-ok` | `runbook §7.0 実測` |
| `tools/pegasus/floor_campaign.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/floor_pair_campaign.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/floor_scoping.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/generate_floor_masstree_payload_policy.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/make_acquisition_receipt.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/mocc_trace_pilot.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/oracle_n_pilot.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/p3_s4_loop_pegasus.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/paper_story_a1_paired.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/paper_story_a2_certification.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/run_t139_a12_stress_check.py` | `dispatch-required` | `compute-node full run: 48 workers / 5.32 seconds; tens of MB per worker` |
| `tools/pegasus/t139_a12_stress_check.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t139_positive_control_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t139_positive_control_probe.sh` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t139_r4_env_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t139_r4_env_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t139_r4_env_probe.sh` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t1403_walltime_sigterm_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t1403_walltime_sigterm_probe.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t1683_rr5_cost_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t1683_rr5_cost_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t2187_adaptive_const_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t2187_adaptive_const_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t2228_driver_gate_liveness_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t293_perf_site_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t293_perf_site_probe.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t316_sandbox_backend_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t316_sandbox_backend_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t419_probe_causality.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t419_probe_causality.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_probe.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_recover.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_verdict.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/run_acceptance_nproc_study.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/run_probe.py` | `dispatch-required` | `static semantic-site classification` |
| `tools/pegasus/run_ss2pl_lock_study.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/silo_ladder_rung1.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/ss2pl_lock_study.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_b10_backoff_grid.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_b10_backoff_shape.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_certify.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_floor.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_floor_pair.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_mocc_trace.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_oracle_n_pilot.sh` | `local-ok` | `login-side submitter; compute work stays in job body (未実測)` |
| `tools/pegasus/submit_paper_story_a2_certification.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_t126_qualification.sh` | `unknown` | `unmeasured; preflight input surfaces remain` |
| `tools/pegasus/submit_t1998_balanced_stock_inline.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/submit_t2417_backoff_policy_performance.sh` | `local-ok` | `static login-side submitter classification` |
| `tools/pegasus/t126_qualification.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/t141_region_profile.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/t810_budget.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/t810_coordinator.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/t810_guard.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/t810_harness_schema.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/t810_pbs_wrapper.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/t810_runner_policy.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/validate_t810.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |

- **この投影検査が保証しないこと。** 検査するのは正本と docs の間の (path, class, evidence) の
  一致だけである。`reason` / `primary_gate` の散文が正本と食い違っても検出しない ([T-522] で
  裁定へ返した)。class の正しさ、資源の実測、hook が `.claude/settings.json` に実配線されて
  いること、`python3 -c` や cwd 経路など parser が実行体として認識しない綴りは、いずれも
  この検査の範囲外である。
- **分類の実測は AI が担当する (2026-09-10 ユーザー裁定、rulings 項2 / T-2267)。**
  D1677、D1936 項49、D233 決定4のユーザー端末専任を、この対象について解除した。
  既存の上限付き実行経路と本節の専用 scope 計測を優先し、対象・入力・実行条件の確認、
  実測、記録を AI が行う。担当変更のために同じ実行をユーザーへ返さない。
  - 実効資源上限と全子孫を含む charged memory の計測を保つ。実測が無い実行体は
    `unknown` のままとし、委任を `local-ok` の根拠にしない。
    本節の「記録すること」の全項目を満たした AI の実測も、記録欄と実測表へ入れてよい。
  - **hook の拒否を迂回しない。** 未配線・解析できない面や別の綴りを抜け道にしない。
    計測対象自身が未登録の場合は、既存の認可された上限付き実行経路を確認してから実行する。
    実行可能な経路が無ければ、その不足を AI の実装課題として特定する。
    新しい承認儀式や汎用測定基盤の新設を担当変更の前提にしない。
  - 上の `systemd-run --user --scope` 手順は計算ノードでは動かなかった
    (2026-08-05 実測: user systemd session がなく、ジョブの cgroup は他テナントと共有)。
    この制約を担当変更だけで解消済みとはしない。性能測定は引き続き計算ノードで行う。
  - **過去の非 canonical 測定は前例にしない。** 2026-08-13 の委任下で
    `tools/claude_session_ledger.py` を計算ノードの共有 service cgroup の差分で測った値には
    同居 job の charge が混入し、1走は負 delta となった。この値は `local-ok` の根拠にならず、
    `unknown` を維持する。D1677 が当時の委任を1件限りとした記録も遡及変更しない。
    非 canonical な結果は evidence として保存できるが、class を軽い側へ倒す根拠にはしない
    (2026-08-13 /rulings 第9回 #5、T-1031)。
- **投げ先。** ログインノードから**自動**で計算ノードへ dispatch されるのは下表の exact task だけ
  である (D103 決定 2 が経路を定め、D842 / D895 が現行 enum を定める)。表に無い重い処理は
  自動化されていないので、`qsub` / `qlogin` で自分で計算ノードを確保して走らせる。
  sanctioned な経路が無ければ **走らせずに止める**。task を勝手に増やさない
  (追加は D842 / D895 と同じくユーザー裁定を要する)。
- **任意コマンドは `generic` task で送る (D895)。** 子 script 欄の `<argv>` は固定 script を
  持たないことを表す sentinel であり、渡された argv 自体を `shell=False` で実行する。
  受理するのは非空の string list だけで、shell 文字列は受理しない。request からの環境値を
  一切受け取らず、stdin は閉じ、cwd は repo root に固定し、子 rc をそのまま伝播する。
  **`generic` も計算ノードでしか子を起動しない** — `_job_script` と `_job_run` の
  二重 bnode gate を通る。したがって「login で任意 argv を実行しない」という D103 決定 5 の
  一次層の性質は保たれる。
  `--walltime` は **`HH:MM:SS` 形式**でなければ投入前に
  `Pegasus dispatch setup failure: ValueError: walltime は HH:MM:SS 形式で指定してください` と
  rc=16 (`kind=infra`, `reason=setup-failure`, `child_started=false`) になる。秒数は受理しない
  (2026-09-14 [T-1643] 実測)。
- **`mutation` task の射程 (D842)。** 変異 wrapper 1 呼び出しを計算ノードの 1 job へ束ねる。
  **既存の `--runner-mode dispatch` 経路を置き換えるものではなく、並存する。**
  束ねた job の内側は local 実行になるため、**変異対象が runner 実行経路
  (`tools/run_tests.py` / `tools/pegasus/dispatch_compute.py`) を含む場合は使わない** —
  `docs/dev-wave/mutation.md` の `DW-M07` が言う「runner が自壊し収集段が `rc=16` になる」が
  そのまま起きる。含まない変異でだけ使い、queue 回数の削減は実測値でだけ主張する。
  `--task mutation` の内側runnerはdispatcherと同じPythonの**絶対path**を指定する
  (`sys.executable` で確認)。`--walltime` は秒数でなく `HH:MM:SS`（例 `01:00:00`）。
- **なお未充足のもの。** 「実測メモリが閾値を超えたら**自動で**投げる」判定は依然として
  実装していない。本節が持つのは admission 規範 (login で走らせない) と、上表の task を
  明示的に呼んだときの dispatch だけである。閾値判定からの自動 dispatch は裁定待ちとして残る。
  また `hooks/guard_bash.py` は `generic` gateway の内側 argv を綴りによって
  拒否したりしなかったりする (`-- pytest` は通り `-- python -m pytest` は拒否される)。
  hooks subtree は `hooks/guard_write.py` が編集を拒否するため本節の変更単位では直せない。
  正規手順は `hooks/README.md` に従う。**裁定待ちである。**
- **開発 harness そのものは、当面この規範の dispatch 要求から除外する (暫定例外)。** 対象は
  `tools/codex_worker_launch.py` / `tools/codex_reasoning_ab.py` / `tools/dev_waves/*` が起こす
  codex・claude 子と、`tools/dev_waves/checker.py` および `tools/check_docs.py` の login 実行である。
  これらは分類上 `unknown` だが、除外しないと標準の dev-wave 経路が「規範違反」か
  「sanctioned 経路なしで停止」の二択になり harness が回らない。
  **この例外の根拠は D106 / D108 ではない** — 両決定の射程は CC 合成 campaign の LLM 4 役に
  限られ、汎用 launcher や checker の免除根拠にはならない。**本 wave が新設した暫定例外であり、
  恒久化にはユーザー裁定が要る**。射程を勝手に広げてはならない。
- **この例外は OOM 対策としては穴である。** 約 390 MB の LLM 子が多数並走する事象が
  per-user 16 GiB を埋める主経路であり、本節の単体閾値では扱えない。実効のある対策は
  同時数 / headroom の admission gate だが**未実装であり裁定待ち**である。
  `checker.py` の隔離 clone 経路も同様に未解決のまま残る。

| task | 子 script |
|---|---|
| `tests` | `tools/run_tests.py` |
| `provenance` | `tools/check_ai_provenance.py` |
| `mutation` | `tools/mutation_worktree.py` |
| `generic` | `<argv>` |

`tools/check_docs.py` がこの表と `tools/pegasus/dispatch_compute.py` の `TASKS` の乖離を検査する。
同 checker は本節の admission 投影表・`unknown` 表・実測表と、`tools/pegasus/README.md` の
実行体宣言表も正本 JSON と照合する ([T-522])。
**これらの検査が保証するのは公表 inventory と docs の同期だけである** — メモリの計測、
重いプログラムの発見、規範値の遵守、自動 dispatch の網羅性はいずれも保証しない。

**現時点で `unknown` (入力に hard cap が無い) と判明している login 側経路** (2026-08-01 の静的調査。
**この一覧も閉じていない** — 走らせる前に測るのが規範であって、一覧に載ることが条件ではない)。

| 経路 | なぜ `unknown` か |
|---|---|
| `tools/codex_worker_ledger.py` | `~/.codex/sessions` を再帰走査し rollout を保持 (調査時点で約 887 MB / 941 rollout) |
| `tools/strip_claude_session_trailers.sh` | clone + 全履歴 rewrite |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | login で外部 3 repo を clone。**入力量としては `unknown` 相当だが、registry 上は `local-ok` / `legacy-admitted (未実測)` として grandfather 追認済みであり hook は許可する** |
| `tools/plotting/plot_backoff.py` | matplotlib の import より前に campaign WAL を全読み |
| `tools/check_workflow_models.py --dir` / `tools/ruleops.py` | 入力・履歴サイズに比例 |
| `tools/check_docs.py` | archive / insight を全読みし本文をリスト保持 (総数・総 bytes 上限なし) |
| `tools/dev_waves/checker.py` | 履歴量に上限の無い repo を 2 回 clone する |
| `tools/codex_worker_launch.py` / `tools/codex_reasoning_ab.py` | prompt bytes・rollout JSONL に上限なし (ただし LLM 子の実行場所は上記の除外に従う) |

**実測して `local-ok` に分類した経路** (2026-08-04、上の手順で専用 scope を作り測定。
certified peak = 観測ピーク + max(25%, 128 MiB) を規範値 512 MiB と比較)。

| 経路 | 観測ピーク | certified peak | 分類 |
|---|---|---|---|
| `tools/pegasus/fetch_third_party.py fetch` (cold: 3 本 clone) | 94 MiB | 222 MiB | local-ok |
| 同 `fetch` (warm: 検査のみ) | 12 MiB | 140 MiB | local-ok |
| 同 `hydrate` | 61 MiB | 189 MiB | local-ok |
| 同 `verify` / `verify-deps` | 12 MiB | 140 MiB | local-ok |

**pin が変われば入力サイズが変わるので再分類が要る。** 現在の pin (policy.json の
`third_party_sources`) での測定値である。

強制の層と射程は次のとおりで、**全経路の機械保証はできない**。

- **一次強制 (fail-closed)**: `tools/run_tests.py` はログインノードでのテスト実行を拒否し、
  計算ノードへ自動 dispatch する。`tools/check_ai_provenance.py` も同型で、履歴監査を計算ノードへ
  自動 dispatch し、`PEGASUS_SUSPECT` では rc=16 で拒否する。`--message-file` の preflight だけを
  免除する。**実 cmake build の機械強制は「全経路」でも「buildcache だけ」でもない** —
  site gate を持つのは `orchestrator/campaign/` の `buildcache.py` / `s2_verify_calibration.py` /
  `s3_lock_coverage.py` / `s5_permutation_coverage.py` / `s8a_trigger_coverage.py` /
  `p3_s4_loop_trigger_gating.py` で、`t152_write_intent_coverage.py` と `silo_ladder_rung1.py` の
  直接 CMake 呼び出しには**無い**。**禁止規範は全 build に掛かるが、機械強制は前者だけである**
  (2026-08-01 実測。本節は当初「実 cmake build もログインノードで拒否される」と全経路を主張し、
  次に「buildcache だけ」と過小に振れた。どちらも誤りだった)
- **二次防壁**: `hooks/guard_bash.py` が直接の重量コマンド (`pytest`、`cmake --build`、`make -j`、
  `ninja`、`ctest`、計測バイナリ) を Claude の Bash 面で拒否する。provenance については
  sanctioned exact path を許可し、それ以外の綴り (repo 外 copy、cwd 相対) を拒否する。
  **hook が閉じるのはこの綴り差だけである**
- **規律 (機械強制なし)**: Codex 子には hook が未配線 (`hooks/README.md`)。script file 越し・
  変数展開・`python3 -c`・他 AI・ユーザー端末・IDE・cron は原理的に見えない。ここは
  `AGENTS.md` と本節の規律で塞ぐ。**`tools/dev_waves/checker.py` の隔離 clone 経路は
  「安全な拒否」の射程内だが「成功する dispatch」の射程外**である — site gate 自体は発火するが、
  計算ノードから clone を見られないので dispatch が失敗し rc=16 が check 失敗として記録される。
  ただしこれは**構造的な不可能ではなく既定環境での条件付き事実**である:
  `tempfile.TemporaryDirectory()` は `dir` を固定せず `TMPDIR` に従うので、共有 FS
  (`/home` は共有) を `TMPDIR` にすれば前提は消える。`orchestrator` check が既に同型で、
  clone 置き場の是正は別タスク

計算ノードの実測 (2026-07-30、request `874129`、bnode114): 48 コア / affinity 48。pytest 全走は
`-n 48` = 205 秒、`-n 32` = 207 秒。queue 待ちは 86 秒 (別の request では 6 秒)。
`-n 16` 以下との対照は未取得であり、**「並列度を上げるほど速い」とは言えない** (2026-07-26 には
より小さい suite で `-n 16` が `-n 48` より速い実測がある)。既定を最大並列にするのは
ユーザー裁定に基づく方針であり、最速の実測に基づくものではない。
provenance 履歴監査の**試作実装**の実測 (2026-07-30、request `874712`、bnode041、596 commit。
出荷実装は並列度に上限 32 を置くので下表の 48 並列の値ではない): ログインノードの
130〜150 秒に対し計算ノードの逐次が 25.24 秒、thread pool 16 並列で 5.60 秒、32 / 48 並列はいずれも
5.23 秒 (改善が止まる)、祖先 bitset を併用した 48 並列で 4.58 秒。**全 arm で findings と
forward-correction が baseline と完全一致することを検査条件にした** (速いだけで答えが変わる変更を採らないため)。
一次資料は `output/insights/2026-07-30_t200-suite-floor/s7-negative-result.md` §11。

`g++-13` は**ログインノードにも計算ノードにも無い** (計算ノードには `g++-12` が在る)。C++
toolchain 依存のテスト群はどちらでも skip されるため、**移設で検出力は増えない**。全走 rc=0 は
受入判定として成立するが、その群の検出力が無いことは結果と一緒に記録する。単独性確認
(pgrep・load average) は計測を走らせる計算ノード上で行う — ジョブがノードを割り当てられても
専有が保証されるわけではない (§1)。共有ログインノード上の確認は他ユーザーのプロセスを拾って
意味をなさない。正式な性能比較へ使うまでは、Pegasus 上の throughput を既存の `linux-baremetal`
測定値へ混ぜない。正式採用には次が必要になる。

**repo のコードを走らせるジョブは interpreter 版をジョブ内で検査してから使う。** 計算ノードの
`python3` はログインノードより古いことがある (2026-07-27 実測: bnode010 の `python3` は 3.9 で、
`match` 文を含む `tools/dev_waves/daemon.py` が SyntaxError になった。同ノードに
`/usr/bin/python3.10` は在る)。検査せずに投げたジョブは全段 0 データで返り、実測したつもりの
空振りになる。版を検査して満たす実体を選ぶか、満たさなければジョブを fail-closed で止める。

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

> **登録段の現況 (2026-08-01 実測):** 上の要件表は登録段の設計要件として残すが、**登録自体は完了
> している**。Pegasus entry は `env_contract.py` の registry に在り (`clocks_per_us=2100`、
> `numactl=()`、`attestation_mode="required"`、single_process=True / allow_resume=False、
> registered calibration を `calibration_ref` で束縛)。enforcement も 5 件中 4 件が実装され
> floor / oracle が消費している — 残 walltime の事前予約検査 = `campaign/reservation.py`、
> 永続領域 allowlist = `campaign/durable_root.py`、build cache の namespace 分離 =
> `campaign/buildcache.py` の `contract_sha256`、実環境 attestation = `campaign/env_attestation.py`。
> **未実装は「PID 可視性の canary probe」だけ**である (2026-08-01 の検索では実体なし。
> ベンチ直前の競合検知 `competing_bench_pids()` は `campaign/pipeline.py` に在るが、これは
> 「他テナントの PID が見えること」自体を確かめる canary ではない)。

Izanagi の性能計測では、trace-enabled の正しさ検証と trace-disabled の性能測定を別 build・別 run
にする。CCBench は共有 submodule を直接変更して実行せず、orchestrator が pinned-clean を確認する
既存の隔離・評価経路を使う。計測機と環境タグの現行方針は `docs/roadmap.md` §5 および
`docs/orchestrator-design.md`「環境タグ」を正本とする。

### 7.1 登録段の実装完了と実機で確定した事実 (2026-07-19)

env_contract registry へ `pegasus` entry を登録済み (clocks_per_us=2100 / numactl なし (NUMA 1
node) / single_process=True / allow_resume=False / attestation_mode=required / calibration_ref =
`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`)。certification
ジョブは `tools/pegasus/` 一式 (submit_certify.sh → certify_calibration.sh → collect_receipt.py)
で再現できる。実機で確定した注意点 (attempt 1〜10 の実測、forensic = 同 calibration/job-staging/):

- `$PBS_JOBID` は `0:NNN.nqsv` 形式。qstat -f へは先頭 `0:` を除いた形で渡す。receipt 照合も
  正規化形 (先頭 `0:` のみ除去) で行う
- qstat -f の開始時刻 field は `Started Request Time = <日時>` (PBS 系の stime ではない)
- **/scr 配下のパスに `:` を含めない** (CMake が PATH 型変数の `:` をリスト区切りとして `;` 化
  する)。ジョブ dir は `${PBS_JOBID//:/_}` 形で作る
- 計算ノードに gflags / glog は無い。`tools/pegasus/fetch_third_party.py` が cache から
  staging root へ hydrate した pinned source (pin の正本は policy.json の `gflags_expected_head` /
  `glog_expected_head`、取得元は `*_source_url`) から /scr で使い捨て static build する
  (certify が自動実行)。login node にも system の gflags / glog は無く、`~/.cmake/packages` の
  残骸 registry で最小 cmake project の probe だけが緑になる。事前検査は本番と同じ finder
  (実 CCBench configure) で行う
- perf は dispatcher (/usr/bin/perf) がカーネル不一致で使えない。実体
  (/usr/lib/linux-tools/<版>/perf) を policy.json の候補から機能 smoke つきで選定し PATH 注入
  する (ノードにより導入版が異なる: 実測では bnode 側 5.15.0-100/135、ログイン側 101/136/173)。
  **床値 campaign (`floor_campaign.sh`) はこの選定をしない** — PATH の literal `perf` だけを
  probe し、候補は receipt の evidence に留める。perf が使えなければ perf 無しで測る
  (裁定 `perf-optional-measurement`、絶対 path 採用は F89 が未裁定)
- /home (共有 FS) では renameat2(RENAME_NOREPLACE) が EINVAL — publish は link+unlink fallback
  (no-replace 意味論は不変)
- PID namespace の host 判定は /proc/1/ns が非 root で読めないため /proc/2/comm==kthreadd 指標
  (comm はプロセス側で詐称可能 — 正直なコンテナには fail-closed、既知限界)
- git worktree で運用する場合は CCBench submodule の実体化 (ローカル clone) が必要
- **`perf report --sort=srcline` は ccbench 級の static -g バイナリでハングする** (サンプル数
  非依存で 300 秒 stdout 0 バイト。小バイナリでは再現しない。2026-07-29 request
  873737/873759/873846 実測)。file 帰属は perf script の IP 集計 → addr2line 一括バッチで
  行う (`tools/pegasus/t141_region_profile.sh` が前例)。addr2line に runtime IP を渡すには
  **非 PIE build (-fno-pie/-no-pie) が必要** (既定 PIE では全件 `??:0`、request 873855 実測)
- ccbench ソースの /scr へのコピーは `git archive` 不可 (.gitattributes の `oze* export-ignore`
  が cc/oze を落とす) — `git ls-files -z | tar` の tracked 限定コピーを使う (request 873732 実測)
- floor/oracle を Pegasus で走らせる際は out_root 配下 `claims/` の事前作成と
  IZANAGI_RESERVATION_* の export (certify_calibration.sh 参照) が必要 (floor 実測は次段)
- **計算ノードは直結の外部 network 不可。ただし HTTP(S) proxy が在る** (訂正 2026-08-01)。
  当初は「外部 network 不可」とだけ記録していたが (2026-07-29、github への DNS 解決不能を request
  873903/873904 で 2 回実測)、これは**直接解決・直接接続についての事実**であり、経路全体の不在では
  なかった。2026-08-01 の実測 (request 876527/876528/876529、bnode002): `getent hosts` と
  `/dev/tcp` は名前解決不能のままだが、計算ノードの shell profile が `http_proxy` / `https_proxy`
  (`10.120.96.1:8080`) を設定しており、**Claude CLI はこの proxy 経由で API に到達する**
  (算術 nonce 3 問を rc=0・3 秒で正答)。env を `PATH/HOME/LANG/LC_ALL/TERM` だけに絞ると
  `ENOTIMP` で 172 秒後に失敗し、proxy 2 変数を戻すと成功する、という 3 条件の対照も取った。
  **ここから先へ一般化してはならない** — 実測したのは「特定 profile 下で Claude CLI が
  proxy 経由で成功した」ことだけである。git clone / CMake FetchContent / pip が proxy を honor
  するかは command・ノード・profile ごとに未確定であり、「https が通るなら FetchContent も通る」
  と読み替えない。依存ソースはログインノードで pinned staging し、`FETCHCONTENT_SOURCE_DIR_*` で
  渡す運用を維持する (再現性と offline fallback のため。silo_ladder_rung1 は submitter が自動実行。
  SOURCE_DIR 指定時は GIT_TAG pin が効かないため HEAD 照合を fail-closed で行うこと)。
  なお当初この訂正では「計算ノードで `claude -p` を起動しない」を緩めなかったが、
  **[T-276] のユーザー裁定 (択 (b) 解禁) を受けて D122 が条件付きで解禁した** (§8 を参照)。
  **2026-08-02 の再実測 (request `877155`、bnode009)**: proxy は lowercase 2 key だけで
  uppercase・`no_proxy`・TLS trust override 系はいずれも未設定、allowlist 5 key + proxy 2 key で
  rc=0、proxy を落とすと約 180 秒後に `api_error` で rc=1。**これは 1 ノード・1 profile・
  1 CLI 版の観測であり、全 bnode や将来 profile へ一般化しない** (設計は drift に対して
  fail-closed である)

### 7.2 稼働 wave の handoff と裁定 inbox の所在 (2026-08-04 実測)

生きた handoff と、台帳へ未記録のユーザー裁定の一次控えは **repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/`** にある。`handoff/<wave>.md` が稼働中 wave の進捗、
`rulings-inbox/*.md` が別セッションで下されて台帳へ未記録の裁定、`<wave>/` が各 wave の成果物
(裁定パッケージを含む) である。**`docs/handoff/` は README のみが正常**であり、そこだけを見ると
稼働中の裁定を取りこぼす。`/rulings` の収集はここも読む。

`tools/audit_dangling_commits.py` の救出 triage (`--offrepo-scan full`) はこの directory を
「repo 外の同一実体」の探索根として使う。掃除の入口 (`--offrepo-scan off`、D2120 項 24) は走査しないので
この directory を渡さない。repo 内のコードに機体固有の絶対 path を焼かないため、所在の指定は次のどちらかで
外から渡す。

```
python3 tools/audit_dangling_commits.py --offrepo-scan full --offrepo-root /work/1/SFC/tanab/dev-wave-jobs
export IZANAGI_DEV_WAVE_JOBS_DIR=/work/1/SFC/tanab/dev-wave-jobs   # 探索根の既定値。利用時は --offrepo-scan full。CLI 指定が優先する
```

- 指す先は **`dev-wave-jobs/` そのもの**である。§7.3 の `IZANAGI_WAVE_LEASE_DIR` は
  その下の `land-lease/` を指す別変数で、探索根に渡しても意味がない (成果物が無い)。
- 掃除の単独監査と rescue gate の子 process は明示 off とし、環境変数の探索根も使わない (子へ継承しない)。
  救出 triage の明示 full は、CLI にも環境変数にも探索根が無ければ実行不能 (rc 2) になる。
  flag 省略の互換経路では、どちらも未指定なら探索は行われず、その旨が出力される。**黙って縮まることはない。**
- 抑止されるのは、到達不能側が regular blob で、basename・実行 mode・bytes が一致し、かつ
  **main に land 済みの文書がその絶対 path (または探索根より下位の祖先 dir) を参照している**
  場合だけである。bytes だけ一致する候補は抑止せず、報告行に注記が付く。

`/next-tasks` (Claude) と `$next-tasks` (Codex) が毎回使う道具の置き場 (command 本文の `<tools>`) は
**repo 外の `/work/1/SFC/tanab/scripts/`** である。`next_tasks_snapshot.sh` / `next_tasks_consult.sh` /
`worklog_carry_resolve.py` / `next_tasks_paper_gaps.py` / `next_tasks_carry_p1.py` を置く。手順と権限は
command が正本で、ここには機体固有の所在だけを書く (D1890 (2)、2026-09-17)。

### 7.3 待ち手の正本 (`tools/dev_wave_wait.py`) と受入 lease (`tools/wave_land_window.py`)

役割は 2 層に分かれる。**`tools/wave_land_window.py` が lease の primitive、
`tools/dev_wave_wait.py` が待ち手の正本**である。**待ち手を自分で書き起こさない ([T-740])。**
散文から書き起こす限り同型の欠陥が入ることは実測済みで、実際に (i) `claim` の JSON 出力を
`case "$out" in *acquired*)` で glob 判定した例 (F192)、(ii) producer の死を
`until ! pgrep -f "$PAT"` で判定して待ち手自身の argv に自己マッチし、`.done` も成果物も
揃った後に 20 時間 23 分と 7 時間 36 分 滞留して wave が無音で死んだ例 (F32 の再発) がある。

lease directory は **`/work/1/SFC/tanab/dev-wave-jobs/land-lease/`** (作成済み、mode 700)。
repo 外に置くのは wave worktree の clean-tree gate と land の untracked 検査に掛けないためである。

#### 受入 lease の待ち手

```
export IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease
W=<wave slug (branch 名の末尾。例 dev-wave-t642-s04-scope)>
N=<attempt 番号。再走のたびに 1 ずつ増やす>
python3 tools/dev_wave_wait.py acceptance --wave "$W" \
  --merge-message-file <merge 用 message file> \
  --receipt-file <repo 外の job directory>/acceptance-receipt-$N.json \
  --log-file <repo 外の job directory>/acceptance-child-$N.log \
  -- python3 tools/run_tests.py
```

- **`--receipt-file` は必須である ([T-908])。** 待ち手経由の受入だけが権威ある dev-wave 受入で
  あり、ここへ出る receipt が無ければ `tools/dev_wave_land.py` は main を 1 bit も進めない。
  path は **repo 外の絶対 path**・親 directory 既存・target 未存在でなければ claim 前に rc=2。
  receipt は走行後 clean・index flag 検査通過・走行前後の fingerprint 一致が成立し
  (lease を取得した走行はさらに TTL 残量と所有の再確認)、かつ**受入 command が rc=0
  (`verdict = "child-green"`)** のときだけ発行される。発行は temp へ書いて
  fsync → 再確認 → `os.rename` の二段階で、**final path の存在だけが「待ち手が成功終端まで
  到達した」証拠**である。予約 temp 名前空間の path を land へ渡しても rc=23 で拒否される。
- **`--log-file` も必須である ([T-1019])。** 受入 command の stdout / stderr は
  **待ち手自身が**この path へ捕獲する。親が別途取った log を渡す形は採らない — receipt に入る
  log hash (launcher が書いた log を待ち手が独立に読み直して照合する)・実効 scheduler の
  attestation・判定なし終了の再試行証拠はいずれもこの log から取るためである。
  path の条件は `--receipt-file` と同じ
  (repo 外・親 directory 既存・target 未存在・dangling symlink 不可、違反は claim 前に rc=2)。
  **shell 側の `> acceptance.log` と同じ名前を使わない** — shell が先に作るので target 既存で弾かれる。
  待ち手自身の診断出力を取りたいなら別名へ redirect する。
- **`--receipt-file` / `--log-file` は attempt ごとに別 path にする。** target 未存在が必須なので、
  同じ path のまま再走すると claim 前に rc=2 で止まる。消して撮り直すと、
  赤の帰属を人・AI が判定する一次資料 (`DW-O18`) である log を失う。上の例のように attempt 番号を付ける。
  ここでの attempt は**外部 invocation** の番号である。
- **1 回の invocation は内部で最大 2 attempt 走る ([T-1275])。** 受入 command が
  **pytest の判定を 1 つも産まずに戻った**ことを肯定的証拠で確定できたときだけ、待ち手は
  lease を保持したまま同一 process 内で 1 度だけ再投入する。判定 (rc=0 / rc=1) が出た走行、
  証拠が曖昧・欠落・重複・relay 経由・矛盾のいずれか、log に pytest 痕跡がある走行、
  claim 前 failure、cleanup 失敗はいずれも再試行しない。attempt 上限と
  `--max-wait-seconds` 由来の共有 deadline の両方で必ず止まる。
- **内部再試行が起きたときの一次資料の所在。** 失敗 attempt の log は
  `<--log-file の値>.attempt-<2 桁>.no-verdict` へ退避され (既存があれば上書きせず停止)、
  `--log-file` が指す path には**最後の内部 attempt の log**が残る。受領証は成功 attempt の値だけを
  収録し、path も版 (`dev-wave-acceptance-receipt/v5`) も root field も変わらない。
  attempt 番号・分類・rc・退避先・log hash・claim した main は待ち手の stderr へ
  機械可読な retry journal 行として出る (成功終端でも消えない)。
- **受理は `child-green` の 1 本だけである (D690 決定 2、2026-08-23)。** 受入 command が rc=0 →
  `verdict = "child-green"`。rc=1 ちょうど (pytest の「テストが落ちた」) は `acceptance-command` の
  失敗としてそのまま返り、待ち手は赤の帰属判定器を起動しない (自動起動経路は機構から遮断済みで、
  flag でも環境変数でも戻せない)。赤の帰属は `DW-O18` に従い人・AI が判定して根拠を worklog へ残し、
  赤の受領証は作らない。rc が 0 でも 1 でもない非 0 (`_DELETION_GATE_RC = 13` /
  `_PEGASUS_DISPATCH_RC = 16` / signal 由来など) は**テスト失敗以外の理由で落ちた走行**で、
  上の内部再試行の条件を満たす場合を除きそのまま失敗として返る。
  outer receipt の schema は `dev-wave-acceptance-receipt/v5` で、v4 以前は受理しない。
- **受領証の内容は待ち手ではなく `tools/acceptance_launcher.py` が作る ([T-1283])。**
  待ち手は launcher の source を Git blob から取り、`python3 -I -c` の stdin へ渡して実行する。
  launcher は `tested_main:tools/run_tests.py` の blob bytes を同じ形で exec して runner の rc を
  観測し、canonical な v5 receipt を待ち手が渡した一時 path へ書く (D838)。実行前に
  `tested_tip:tools/run_tests.py` も blob として別に読み、欠落・読取不能なら suite を一度も起動せず
  rc=70 で止まるが、tested main との bytes 等値は要求しない。実行 bytes は常に tested main から
  取得し、実行後の独立再読と全 shard の binding report も同じ main digest へ照合する。
  実行器に `tested-tip-bootstrap` 相当の例外は無く、`tested_main` 側の欠落も fail-closed である。待ち手は保管と publish
  だけを担い、launcher が非 0 で終われば receipt を publish しない。
  **この形は runner が `main(argv)` を公開していることを要求する** (pathname から import
  しないため)。v5 は `launcher_source_revision` / `launcher_blob_sha` /
  `launcher_executed_sha256` / `waiter_executed_sha256` / `runner_executed_sha256` を必須にし、
  land は 3 本の内容 SHA-256 を Git tree から独立に再計算して照合する。
  **この照合は `child-green` の受領証に掛かる** (現行の権威経路が発行する受領証はこれだけである)。
  launcher source は `tested_main` にあればそれを使い、無いときだけ `tested-tip-bootstrap` を
  名乗る。land は `tested_main` と `locked_main` の双方で launcher 不在を要求するので、
  launcher が main へ入った後は bootstrap を名乗れない。
  **dispatch した `tests` 子は main の blob を実行する ([T-1974] 段階 P)。** launcher が
  session nonce と exact K を所有し、継承 write-fd で全 shard の申告を**無条件に**要求する。
  dispatcher は launcher 所有の manifest がある走行にだけ束縛を適用し、manifest が無ければ
  従来の pathname 起動のままとする。計算ノード側は `tested_main` の blob を 1 回読んで
  同じ buffer を hash と子の stdin に使い、その digest を申告する。launcher は自分が読んだ
  main blob の digest と照合し、受領証を書く**前**に fail-closed する。
  **この結果、dispatch しない authoritative 受入は受領証を作れない。** queue が停止していて
  ログインノードに余裕がある場合、従前はログインノードで suite を走らせて受領証を出していたが、
  段階 P 以降その経路は申告 0 件で拒否される。復旧は段階 R ([T-1976]) が bounded local を
  main blob 実行へ移すまで待つ。
  **閉じていない残余**: 改変された tip 側待ち手は launcher を起動せず受領証を自作できる。
  束縛が及ぶのは dispatch された `tests` 子 1 層だけで、login 側の dispatcher import、
  job script、login の collect-only pytest、bounded local の pathname runner、
  計算ノードの pytest controller と xdist worker は束縛外である。
  **dispatcher 自身は tip 側 bytes なので、dispatcher を編集した wave は段階 P では捕まらない。**
  land verifier 自身も候補コードである。いずれも [T-696] の協調境界に残る。
- **`tools/run_tests.py` を変更した wave も受入を通せる。** launcher と land は
  `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` が双方 blob として実在することを
  要求するが、両者の blob SHA / bytes 等値は要求しない。実行する runner、全 shard の binding report、
  受領証の `runner_executed_sha256` の照合先は常に tested main 側の blob である。
  受入後に clean な forward-main merge を足して同じ受領証を再利用するとき、land は最後に取り込んだ
  main と tested main の runner blob を比較する。最終着地物の runner が変わっていれば再利用を拒否し、
  新しい main を基準に受入をやり直させる。runner が同じ main 取り込みは再走させない (D987)。
- **`stage=restart-required` (rc=70) は待ち手を再起動しろという意味である。** 受入 command を
  投入する直前に、待ち手が module 初期化直後に束縛した自 source の bytes と、その走行が束縛する
  tip の `tools/dev_wave_wait.py` blob 内容を照合し、不一致・照合不能なら command を投入せずに
  止める。stderr の detail に期待 sha・実 sha・tested tip・理由が出る (**ただし停止後の lease 解放が
  失敗した場合は cleanup 側の結果が primary を置換するため、この detail は表示されない**)。
  直し方は、その待ち手 process
  を止め、**新しい tip の木から待ち手を起動し直して再投入する**ことだけである。同じ process を
  待たせ直しても直らない。走行前に止まるので計算資源は消費していない。
  **保証の範囲**は「canonical direct 起動、または origin が束縛 source と同一 inode を指す
  file loader 経由で、module 初期化直後に束縛した source inode の bytes」であり、Python が
  compile した bytes そのものではない。**この gate を持たないコードで既に起動している待ち手は
  本契約の被覆外である** — 契約が入った tip より前に起動した待ち手は、この検査を実行しない。
- **投入前に `git submodule update --recursive` を実行する。** 未初期化 (`-`) の submodule が
  あると claim 前に `preflight-submodule-ready` で rc=2 になる。これは、受入 command 自身が
  submodule を初期化して走行後 fingerprint を変え、緑なのに receipt が出せなくなる罠を
  静かに踏まないための fail-closed である。
- **`PYTEST_ADDOPTS` / `PYTEST_PLUGINS` を設定したまま投入しない。** claim 前に rc=2 で止まる。
  `IZANAGI_TASK_RUN_ID` を使う場合は `IZANAGI_TASK_RUNS_ROOT` を **repo 外**へ向ける
  (repo 内 root は claim 前に rc=2。走行中に tracked な台帳へ追記して走行後検査を
  真に赤くするため)。
- **走行後にも検査がある ([T-907])。** 受入 command が返った後、child rc を評価する前に
  `postrun-clean` / index flag / fingerprint 比較を行う。**child rc が非 0 でも必ず走り**、
  木が変わっていれば rc=70 が child rc に優先する。20〜40 分の走行中に木が変わった受入は
  権威を持たない。
- **受入 command は `--` の後ろへ裸形で渡す。** `-q` / `-rf` などを足すと
  `tools/run_tests.py` の acceptance shape 判定が False になり、受入専用の事前検査が
  黙って無効化される (`_is_acceptance_run` の default-deny に落ちる)。報告用の整形が要るなら
  受入とは別の走行を立てる。
- **`--merge-message-file` は待機を始める前に用意しておく。** behind が判明した時点で必須になり、
  無ければ投入せず止まる。message には `DW-O17` に従った `AI-Agent:` trailer を書く。
  **親が自分で merge commit を作った wave では、待ち手へ渡す message file を親の merge の
  message file と別にする。** 両親が同じ実装面 path を変えた merge は `DW-O17` により Codex
  `role=author` を要し、その message file には Codex の著者行が入る。同じ file を待ち手へ渡すと、
  待ち手が作る別の merge commit まで Codex 著述を名乗ることになる。待ち手用は自己申告の
  `role=integrator` だけを持つ file にし、実装面 overlap があれば待ち手が fail-closed で止まるのに
  任せる (2026-08-23 実測、取り残し branch の回収 wave)。
- **rc=0 は「receipt が発行された」を意味する** (lease を取得した走行は保持したまま返る)。
  現行の権威経路では受入 command 自身が rc=0 のときだけ発行されるので、receipt の `verdict` は
  `child-green`、`red_nodeids` / `flake_nodeids` は空である。**台帳へ「全テスト緑」と書く前に
  receipt の `verdict` と両 field を読んで確かめること** (land 結果 JSON の
  `acceptance_red_nodeids` / `acceptance_flake_nodeids` も同様に空)。成功時は release
  しない。**land の終端で親が `release --wave "$W"` する**こと。それ以外の終わり方
  (claim 異常・Git 異常・merge 中止・受入赤・例外・signal・中断) では待ち手が release する。
  **例外は `held-self` 経路** — その呼出しが lease を作っていないので release 権限を持たず、
  失敗しても保持したまま返して親の終端 release に委ねる (下の「自己保持」を見よ)。
- 主な rc: `2` = 起動前の入力・tree identity 不正、`70` = fail-closed (進行不可。
  Git 失敗、自己保持なのに進めない、**投入直前に木が汚れている
  (`prerun-clean`)**、**message の provenance preflight が非 0 (`merge-message-provenance`)** 等)、
  `74` = cleanup (merge abort / release) の完了を確認できない、それ以外の非 0 = 受入 command の rc。
  **`prerun-clean` と `merge-message-provenance` の rc=70 は lease 取得後の fail-closed 失敗**で、
  `ACQUIRED` なら release、`HELD_SELF` なら保持する。検査を通っただけでは成功ではなく、
  受入 command が rc=0 になるまで lease は保持される。
- **`release` の「確実さ」の限界。** 待ち手は SIGTERM / SIGHUP / SIGINT を捕捉して cleanup へ
  倒すが、**SIGKILL と host 停止は捕捉できない** (shell の `trap` でも同じ)。これらと、
  cleanup 開始直後に 2 発目の signal が入る狭い窓では lease が残留し、TTL 2,400 秒で失効するまで
  回収されない (裁定パッケージへ返却済み)。
- **`--max-wait-seconds` (既定 7,200 秒) は受入全体の deadline であって lease の待ち上限ではない。**
  claim は待たないので、この値を使い切るのは受入 command 自身が長いときである。

script が担う判定は次のとおりで、**同じ内容を別 shell loop として書き直さない**。

- `claim` の出力は rc=0 のときだけ JSON として parse し、トップレベル `state` を
  **exact 一致で判定する** ([T-812])。`acquired` / `held-self` / `held` (と旧版の `queued`) は
  投入し、`stale-held` / `unavailable` は fail-closed で止める。出力全体への
  部分一致 (`case *acquired*` / glob / grep) では判定しない — `state` 以外の field や診断文に
  同じ語が出れば偽陽性になる。**`claim` の出力は JSON、`status` の出力は key=value である**
  (`status --json` のときだけ JSON)。
- 各段は 1 コマンド 1 値へ分解し、rc と値を別々に判定する。rc をパイプへ通さない、
  `|| true` で潰さない、複合条件を 1 行にまとめない。これらはいずれも赤を緑に見せる。
- claim の前に tree identity を検査する — git worktree の中であること、HEAD が detached で
  ないこと、`git rev-parse --show-toplevel` が起動 cwd と一致すること、branch 名が wave slug で
  終わること、木が clean であること。自動 merge/commit が別 checkout へ入るのを止めるためである。
  **clean の述語は `git status --porcelain --untracked-files=all --ignore-submodules=none` の
  stdout が空**である ([T-725]、`tools/dev_wave_wait.py` の `_CLEAN_STATUS_ARGV` で実測、
  2026-08-19 [T-1303] で `--untracked-files=no` という旧記載との食い違いを確認し是正)。
  `--ignore-submodules=none` は `tools/run_tests.py` と `tools/dev_wave_land.py` に揃えたもので、
  **submodule の dirt を拒否する** — land が既に submodule dirt を拒否する以上、受入側で
  拒否しても新たに止まる wave はない。汚れていれば **claim せず rc=2** で返るので
  **lease を消費しない**。
  **untracked も現在は拒否する (`--untracked-files=all`)。** F191 が観測した
  2026-08-12 時点の挙動 (`output/env/pegasus/floor/attempts/submissions/` 等の
  `.gitignore` に無い実在の生成物を持つ wave でも untracked は claim を止めなかった) から
  変わっている。commit されていない生成物・記録 fragment があると `preflight-clean` で
  claim 前 rc=2 になるため、受入投入前に untracked を repo 外へ退避するか commit すること。
- **claim の直後に待ち手自身が local main を取り直して取り込む
  ([T-732] 裁定 (a) の正本)。**
  並行 wave が随時 land するので、`claim` 時の `main_sha` は投入時点の main とは限ら
  ない。取り込まずに走らせると land 対象 tip が main の子孫でなくなり、全走をやり直すことになる。
  順序は `git rev-parse main` → `git rev-list --count HEAD..main` → (非 0 のときだけ)
  **所有実装面の overlap 判定** → `git merge --no-ff --no-commit main` →
  `python3 tools/check_ai_provenance.py --message-file <message>` →
  `git commit --dry-run -F` → `git commit -F` →
  作成 commit の SHA を固定して message の trailer を確認 → `HEAD..main` の再検査、である。
  **provenance preflight (`--message-file`) は `docs/ai-provenance.md` が commit 前に要求する
  正本の検査**であり、`git commit --dry-run` では代替できない ([T-725])。`AI-Agent:` 行の
  存在だけを見る検査は形式違反 (product/model/reasoning/role の順・許可値) を通してしまい、
  land 時の全史監査まで赤が遅れて受入 1 走と lease 窓を失う。
  **checker は merge の後に置く。** checker は `MERGE_HEAD` の有無で検査対象 path を変え、
  merge 後なら prospective parents を使って merge 固有の実装面 path まで見るためである。
  merge 前に置くと staged path が空になり、その検出力が落ちる。非 0 なら
  `stage=merge-message-provenance` の rc=70 で、`merge --abort` してから lease を返す
  (`merge_pending` は merge の前に立つのでこの経路に正しく載る)。
  取り込んだ main SHA は**作成された merge commit の second parent が記録する**ので、
  message 本文へ SHA を差し込む必要はない (F191 点 1 の erratum)。
  **`--merge-message-file` は repo の外 (`dev-wave-jobs/<wave>/` 等) へ置く。**
  repo 内に置くと、その message file 自身が tree を汚す。
  **`--ff-only` と `--no-edit` は使わない** (wave branch が自前 commit を持つと fast-forward
  できず `Not possible to fast-forward` で止まる)。中断は `git merge --abort` → `release` の順。
- **merge の前に所有実装面の overlap を見る。** `git diff --name-only HEAD...main` の結果に
  本 wave が触った実装面 path が含まれるなら、**待ち手では merge せず親へ戻す** (fail-closed)。
  両親が同じ実装面を変えた merge 結果はどちらの親とも異なるため `DW-O17` が Codex
  `role=author` を要求するが、trailer を固定した待ち手の message file では条件を満たせない。
  待ち手が判定しなければ無審査の merge commit ができ、land の provenance 監査まで赤にならない。
  本 wave が触った実装面 path は `--owned-path` で外から渡す (repo へ固定値を焼かない)。
- **`HEAD..main` の再検査の後、受入 command 投入の直前に、木が clean であることを
  もう一度単独で確認する** (`stage=prerun-clean`、[T-725] = F191 の安全配線 点 3 の後半)。
  述語は claim 前の tree identity 検査と**一字一句同じ**で、stdout が空であることだけを
  成功条件にする (rc だけを見ると clean も dirty も 0 なので恒真になる)。
  **`behind` が 0 の経路にも無条件で適用する。**
  claim 前の検査結果を保存して使い回さず、投入直前に必ず新しく実行する。
  `behind` が非 0 でも merge 後に clean とは限らない — `git merge --no-ff --no-commit` と
  `git commit` が commit するのは index であって、merge と衝突しない未 stage の tracked 編集は
  そのまま残るからである。
  **この検査が保証するのは「`git status` を実行したその時点で tracked 木が HEAD と一致していた」
  ことだけである。** status の完了から受入 command の process 起動までにも隙があり、
  **走行中に入った変更は覆わない**。したがって受入結果に「投入の瞬間に一致した」とも
  「走行中ずっと一致していた」とも書かない。走行中まで覆う設計は裁定パッケージへ返した。
- **待機中に親が同じ worktree へ書かない。** `CLAUDE.md` の「作業の進め方 9」は長時間待機中に
  文書を進めよと指示するが、その書き先を受入対象の worktree にすると `prerun-clean` が
  正しく赤になる。待機中の文書は **repo 外 (`dev-wave-jobs/`) か別 worktree** へ書き、
  受入に含める変更は**待機を始める前に commit しておく**。これは operator の規律であって
  機械保証ではない。
- **段 7 の記録と最終受入の順序。** land は wave HEAD と `tested_tip` の exact 一致を要求するので、
  `docs/spool/` の fragment は**最終受入より前に commit する**。順序は
  「fragment 作成 → `check_docs.py` と `spool_fold.py --dry-run` → `git commit` →
  **最終受入** → tested tip 固定 → land」である。受入の後に記録を足すと land が rc=23 で拒否し、
  受入 1 走が無駄になる。
- **この契約が効くのは、新しい main を取り込んだ待ち手 process を起動し直した走行からである。**
  既に起動済みの待ち手はロード済みのコードで走り続けるので、走行中に新 main を merge しても
  新しい検査は発火しない。稼働中 wave では「取り込み → 待ち手を起動し直す」まで済ませて
  はじめてこの契約下の受入と数える。
- **claim の待ちは無い (D662、2026-08-23 実装)。** `claim` は 1 回だけ呼ばれ、`held` でも
  待たずに受入を投入する。`--poll-seconds` は後方互換で受理するだけの no-op であり、
  `--max-wait-seconds` は受入全体の deadline であって lease の待ち上限ではない。
- `claim` が構造化された `held` / `held-self` を返した時点で「この呼出しが lease を
  作った可能性」は消えるので、**その後の失敗では release しない**。`release` の権限証明は
  wave slug の digest だけであり、同一 slug の別 invocation が保持中の lease を消してしまう
  ためである。

#### 自己保持 (`held-self`) — 2 走目や再開でそのまま進む ([T-812])

**同じ wave が lease を保持したまま `claim` すると、TTL (lease の mtime) を更新して
`held-self` を返す。** 待ち手はこれを受理して受入を投入するので、**保持したまま 2 走目を回すのに
release して取り直す必要はない** (取り直すと解放窓で他 wave に lease を取られる)。
恒久対応前は自己保持が `held` を返し、待ち手が `acquired` を待って**最大 7200 秒無言で空転**した
(実害 4 例)。

- 更新は `claim` の自己保持分岐だけで起こる。**`status` は lease を一切変更しない。**
- **stale な自己保持 (TTL 超過) は `held-self` にしない。** 排他が失われた可能性があるので、
  従来どおり unlink → 再取得 (`acquired`) に倒す。
- **自己保持なのに進めないときは polling せず fail-closed する** — 更新に失敗したら
  `stage=claim-self-renew-failed`、`held-self` の形が契約を満たさない (holder が 12 桁 hex で
  ない、age が int でない、`source` が `{"status":"ok","reason":null}` でない) か、`held` /
  `queued` / `stale-held` / `unavailable` が自己 holder を指すなら `stage=claim-self-unverified`。
  いずれも rc=70 で、**lease は保持したまま**返る (親の終端 release に委ねる)。
- **既知限界 (裁定パッケージへ返却済み)**: holder は wave slug の digest 12 桁であり
  **invocation を識別しない**。同一 slug の別 invocation も `held-self` を得て進めるため、
  **1 slug につき active な待ち手は 1 本**という運用前提が要る (機械保証ではない)。
  自己更新の連続回数に上限は設けていない。

#### 背景 producer の待ち手

```
python3 tools/dev_wave_wait.py producer \
  --done-file <job>/<name>.done \
  --artifact-file <job>/<name>.md \
  --pid-file <job>/<name>.pid
```

- 完了は **`.done` 実在・成果物実在・producer の死**の 3 点照合で判定する。
- **producer の生死は pid で見る** — exact PID の `kill(pid, 0)` と `/proc/<pid>/stat` の
  starttime 束縛だけを使う。PID 再利用は starttime の差で死と判定し、zombie は死として扱う。
  **照合 pattern を受け取る CLI 面は無い。** `pgrep -f <pattern>` の待ちループは、待ち手自身の
  argv がその pattern を含むため常に自己マッチして終わらない (F32)。
- **PID は producer script 自身が `echo $$` で書き出す** (`--pid-file`)。待ち手が `pgrep` で
  推測すると起動ラッパの PID を掴む (F156)。`.done` の除去は producer script の冒頭に置く。
- producer の死後に `.done` か成果物が欠けていれば、最大 30 秒の猶予で再確認してから
  fail-closed で非 0 を返す (NFS の可視性遅延で成功済み producer を失敗扱いにしないため)。

#### 計算ノード job (qsub) の待ち手 ([T-1281]、D1290)

```
python3 tools/dev_wave_wait.py compute \
  --request-id <qsub が返した request ID> \
  --done-file <job body が書く done-marker> \
  --accounting-file <qsub の -e が返る会計本文の file> \
  [--max-wait-seconds 21600] \
  [--receipt-file <job>/<name>.compute-receipt.json]
```

論文のための実測 (A-1 / A-2 / B-4 / 床値) はすべて計算ノード job であり、**その完了待ちは
この subcommand が正本である。shell で書き起こさない**。producer の待ち手は local の pid を
必須とするので scheduler へ投げた job に対応しない。

- **完了判定は 2 材料の論理和だけである** (D1290)。(i) done-marker が実在し非空、
  (ii) 会計本文が対象 request ID に束縛された `Ended Request Time:` 行を持つ。
  **`qstat` は rc も状態も見ない。この経路は `qstat` を 1 度も呼ばない。**
  終了した request は数秒で `qstat` から消えるので、終了後に問い合わせる待ち手は作れない。
- **会計本文の束縛は「ID 行がちょうど 1 本」かつ「その行より後ろに `Ended` 行がある」ことを要求する。**
  他 job のレコードが同じ file に混ざると、ID 行が 2 本になって永久に偽になるか、
  対象より前の `Ended` 行が `ended-before-target-request-id` で拒否される。
  **会計の返り先 (`-e`) は request ごとに一意な path にする。**
- **done-marker は request ごとに一意な path にし、投入前に消す。** 前回の走行の marker が
  残っていると初回 poll で即座に完了と判定される。job body は成果物を flush した後、
  最後に marker を公開する。**空白だけの内容は証拠にならない** (`echo done > $DONE` のように
  空白以外を書く)。これは意図的に「非空」より厳しい側であり、緩めない。
- **done 証拠が真になった poll では会計側を評価しない** (論理和の短絡)。受領証の
  `accounting_evidence` はそのとき `false` になるが、これは「会計が終了を示さなかった」ではなく
  「評価していない」の意味である。
- poll 間隔は 15 秒、`--max-wait-seconds` の既定は 21,600 秒 (6 時間) で、**queue 待ち・実行時間・
  会計の追記待ちをすべて含む**。deadline 超過は `stage=compute-timeout` の rc=70 で fail-closed。
  producer と同じ式 (`経過 + 15 > 上限`) なので、**15 秒未満の値は sleep せず即 timeout し、
  15 秒の倍数でない値は最大 14 秒早く終わる**。
- **投入に失敗した job、起動前に消えた job、hold のままの job は早期に検知しない。** 上の 2 材料が
  どちらも立たないまま deadline まで待って非 0 になる。早期離脱のための `qstat` 参照は D1290 の
  外側なので持たない。
- `--request-id` は parse 時に正規化可能性を検査し、不能なら rc=2 で投入前に落ちる
  (`0:` 接頭辞と末尾ドットは正規化して同一視する)。
- `--receipt-file` は省略可。渡すと成功時だけ `dev-wave-compute-receipt/v1` を atomic に publish し、
  真になった側の証拠 file の `mtime_ns` を記録する (偽側は `null`)。**producer 受領証とは別 schema
  なので path を分ける** — 同じ path を渡すと後の publish が前の受領証を置き換える。
  失敗時に前回の成功受領証は消えないので、request ごとに新しい path を使い、**受領証の実在ではなく
  待ち手自身の rc で完了を判定する**。
- **rc=0 は「job が終端した」ことだけを意味する。** job の成功・成果物の正しさ・dispatcher の
  受領証とは別である。`tools/pegasus/dispatch_compute.py` の私有述語は project 名・
  `Started Request Time:`・`Elapse:` まで要求する別の判定であり、相互に代用しない。

#### lease そのものの性質と既知限界

- **待ち行列 (待ち札) は無い。** D662 で廃止し、2026-08-23 に `claim` から機構ごと除去した。
  `claim` は待ち札を作らず参照もせず、`queued` を返さない。lease が空いていれば即取得、
  他 wave が保持中なら即 `held` を返す。順番待ちも head-of-line blocking も発生しない。
  旧版が残した `ticket.*` は `release` 側の legacy cleanup が回収し、`claim` の結果を変えない。
  廃止の理由は D662 — 一つの wave の受入が全体の land を止める設計を否定した (歴史は D253)。
- **claim の loop・main の取り直し・merge・受入投入は同じ待ち手 script に置く。** 取り込みを親の
  事前作業にし、待ち手を `git rev-list --count HEAD..main` の検査だけにすると、待機中に main が
  進むたびに取得した lease を捨てる (2026-08-10 実測: 24 分待って `acquired`、その時点で
  15 commit 遅れ。別 wave では 4 回空振り)。
- 待ち手が閉じない残余 race が 1 つ残る — 最後の `HEAD..main` 再検査から受入 command 起動までの
  間に main が進む場合である (fencing token が無いので閉じられない)。
- 受入と land の**どの終わり方でも** lease を手放す。待ち手が保持したまま返すのは成功時と
  `held-self` 経路の失敗時なので、**land の終端では親が `release --wave "$W"` を実行する**
  (赤・失敗・中断を含む)。他 wave の lease は消せない (holder digest 不一致なら `not-owner`)。
- land が成功したときは、保存した land 結果 JSON を渡して通知文を作り、`ListAgents` で
  照合した peer へ 1 度だけ送る。

```
J=<repo 外の job directory>
python3 tools/dev_wave_land.py ... \
  --acceptance-wave "$W" --acceptance-receipt "$J/acceptance-receipt.json" \
  > "$J/land-result.json"                                # rc と JSON を保存する
python3 tools/wave_land_window.py message --kind landed --wave "$W" --land-json "$J/land-result.json"
```

- **land が rc=26 (`fold-failed`) で終わり、main が wave tip でない SHA にある場合** (fold 失敗で merge 前へ
  巻き戻した場合と、merge 前の失敗で main が動かなかった場合を含む、F977) は、同じ JSON で
  `python3 tools/wave_land_window.py message --kind rolled-back --wave "$W" --land-json "$J/land-result.json"`
  を実行し、rc=0 の通知文を同じ照合済み peer へ 1 度送る。rc=3 (述語不成立) なら送らない。
  rc=28 (`fold-rollback-failed`、巻き戻し不完全) はこの kind の対象外で、親が手で復旧する。
  通知は advisory であり、受け手は取り込んだ main の SHA について
  `git merge-base --is-ancestor <SHA> refs/heads/main` が rc=1 なら受入完走後に受入 tip へ reset して
  取り込み直す (F977 の恒久対応の手順)。

- **`--acceptance-wave` / `--acceptance-receipt` は必須である ([T-908])。** 省略すると
  argparse の rc=2、receipt が欠落・不正なら rc=23 (`acceptance-receipt-rejected`) で
  **main は 1 bit も変わらない**。`already-landed` 経路も valid な receipt 無しでは成功しない。
  bypass flag も環境変数の逃がし道も無い。
- **land 結果 JSON は repo 外へ書く。** wave の cwd へリダイレクトすると、land 起動前に
  repo 内 untracked file を作ってしまう。
- **旧待ち手で受入済み・未 land の wave は receipt を持たない。** 互換 bypass は作らないので、
  新しい待ち手で受入を 1 走やり直す必要がある。これは裁定 [T-908] (a) を機械で担保する費用である。

- 取り残した lease は TTL (既定 2400 秒) で自然失効する。**他 wave の受入投入は止まらない**
  (待ち行列廃止後は `held` でも即投入する) が、自分の 2 走目のために release は忘れないこと。
  **受入を 2 度走らせると 2 走で TTL を超える** (1 走
  1055〜1273 秒)。2 走目の前に `claim` し直す — 保持したままなら `held-self` が返って TTL が
  更新され、そのまま進める ([T-812])。`held-self` 以外 (`claim-self-renew-failed` /
  `claim-self-unverified` / stale で取り直せない) なら 2 走目を投入しない。
- **既知の限界 (裁定パッケージ)**: TTL 超過で lease を取り直した場合、旧 holder の受入は
  止められない (fencing token が無い)。その場合の帰結は本機構が無かった場合と同じ競合であり、
  悪化はしない。release の権限証明は wave slug の digest だけである。
- **公平性は保証しない。** 待ち行列を消した以上、lease の取得順は競争であり先着順ではない。
  D662 はこれを承知の上で「止めないこと」を公平性より優先すると裁定した。

### 7.4 変異 harness の runner argv

`tools/mutation_harness.py --runner-mode dispatch` は「runner が計算ノードへ投げる」ことを
保証しない。`tools/run_tests.py` はログインノードに余裕があると local で走り、その経路は
harness が要求する dispatch receipt 行を出さないため、baseline が `PARSE_ERROR` で中断する。
**runner argv に `--force-dispatch` を必ず付ける。**

**`--spec` は試験対象 checkout の外を指す。** commit 済み spec を repo 内の path で渡すと
`runtime artifact は試験対象 checkout 外でなければならない: --spec` で rc=2 になる
(2026-08-09 実測)。commit したうえで repo 外へ複製し、`--expected-spec-sha256` で内容を束縛する。

```
python3 tools/mutation_harness.py --repo <worktree> --spec <spec> \
  --expected-spec-sha256 <sha> --out <ledger> --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py --force-dispatch <対象テスト> -q -rf
```

**spec には `schema` と時間 3 field が要る** (2026-08-26 実測)。`schema`
(`izanagi-dev-wave-mutation-spec/v1`)、`estimated_run_seconds`、`timeout_seconds`、
`hang_timeout_seconds` のどれかを欠くと `spec の field 集合が不正: missing=[...]` で
**変異を 1 件も走らせずに起動前へ中止する**。上の起動例は argv だけを示しており、
spec 側の必須 field は含まない。

**`--attempt-out` は `--wrapper-attempt` と同時指定でなければならない** (2026-08-26 実測)。
片方だけを渡すと `mutation harness aborted: --attempt-out と --wrapper-attempt は同時指定が必要`
で起動前に落ちる。attempt 記録を取るなら両方渡す。

**spec の `category` は `negative` / `positive` / `both-layers` の 3 値だけである** (2026-08-26 実測)。
`DW-M01` が要求する「承認外の過剰拒否を検出する正例」は `positive` で登録する。
`positive-control` のような値を書くと `category が未知` で起動 1 分以内に中止し、台帳も作られない。
このとき待ち手は成果物不在のまま待ち続けて `rc=70` (timeout) を返すので、
**外からは「まだ走っている」ように見える。** producer の生死を `ps` で確かめる。

**`expected_nodes` の nodeid は ASCII だけにする。** `tools/run_tests.py` は子の出力を中継する
とき非 ASCII を `\uXXXX` へエスケープするため、parametrize の表示 ID に日本語を含む nodeid は
harness の collection と一致せず `期待 node が pytest collection に実在しない` で必ず落ちる。
対象テストには `pytest.param(..., id="ascii-only-id")` を先に付ける。

### 7.5 独立ジョブは並行投入する (2026-08-11 ユーザー裁定)

**§5 の「並列」も §7 の「最大並列で回す」も、すべて job の内側 (OpenMP / MPI / pytest `-n` /
build `-j`) の話である。本節は job どうし、すなわち複数の request を同時に走らせてよいかを扱う。**

> **規範 (2026-08-11 ユーザー裁定)。** 計算ノードへ投げられる仕事が互いに独立なら、
> **既定で並行投入する。** 順番待ちを 1 本ずつ払う直列は、下の「並行にしない面」に当たるときだけ
> 選ぶ。**「同じ protocol を別の workload / 別のパラメータで回す」は fan-out してよい典型である。**

gen_S に紐づく job server は 149 で、node 仕様は全台同構成である (§1)。`Submit Number Limit` と
`Submit User Number Limit` はどちらも UNLIMITED (group は 200)、logical host は
`CPU Number` Min=Max=Std=48 で node の CPU を使い切る (`qstat -Qf gen_S` 2026-08-11 実測)。
**並行化が増やすのは総ノード時間ではなくその使い方の密度である** — 増えるのは job ごとの
prologue (module・build・probe) の重複分だけで、混雑時は超過分が待つ。唯一の按分は
「1 本あたりの正味の仕事が prologue を十分上回るか」で、下回るなら束ねる
(floor job の見積では prologue ≈ 900 秒。§7.4 直上の job script 参照)。
**未確認:** 大量投入が fair-share でどう扱われるか (自分の後続 request の優先度が下がるか) は
測っていない。「直列より遅くなることはない」とまでは言わない。

#### 「独立」の判定 — 次の 3 つを満たすことを言う

1. **共有して奪い合うものが無い。** 入力・出力 path・作業木・lock・journal・予約・
   process 観測対象のいずれも共有しない。
2. **protocol が順序・単一テナント・同一 campaign 内比較を要求していない。**
3. **固定費が見合う。** 1 本の正味の仕事が job ごとの prologue (module・build・probe) を上回る。
   下回るなら束ねる (floor job の見積では prologue ≈ 900 秒。§7.4 直上の job script 参照)。
   両方とも未計測なら、1 回測ってから決める。

**いずれかが不明なら不明と書き、fan-out の根拠にしない。**逆に、**protocol 由来の禁止は
「技術的に不可能」ではなく「現行 protocol では禁止」と書き分ける** — 前者は諦めるしかないが、
後者は protocol 側の裁定で解ける。

#### 並行にしない面 (これだけ)

1. **protocol が直列 schedule を定めている計測。** `s8b_floor_campaign` は 12 セルを
   「protocol が定める schedule どおり直列・単一テナントで」測り、floor を単一 campaign 内の
   session dispersion と定義する。**これは手続き上の束縛であって、ノード間差の大きさを根拠に
   していない。**変えたければ protocol 側の裁定を先に取る。実装の都合で崩さない。
2. **受入全走の隣。** 全走中に、同じ作業木の `output/`・git index・tracked / untracked 集合を
   変える dispatch・監査・編集を走らせない。**正本は F136** — 並走させた provenance 監査が
   書いた receipt そのもので `output/` の副作用スナップショット検査が 9 件赤になり、
   単独再走では消えた。別に F57 (全走時の subprocess wall-clock flake) の族もあるが、
   **こちらは full 単独でも再発しており根本原因は未確定である。**F57 型の赤を並走のせいと
   決めつけて緑扱いしない。
3. **read / write 集合を共有する job どうし。** 判定は出力ファイル名ではなく**共有する
   read / write 集合全体**で行う。作業木と git index、campaign lock と `runs/wal.jsonl`、
   build-cache claim、campaign claim、freeze / selector の namespace、receipt / registry、
   そして **`output/` の親 directory を走査する consumer** のいずれかを共有する job は、
   producer と consumer の双方が並行 writer を明示的に受理していない限り並べない。
   **job 専用の nonce path を切っても、親 directory を検査する consumer がいれば独立ではない。**
4. **同じ作業木を書き換える走行の同時実行。** 変異 harness は木を in-place で書き換えるので、
   並行させるなら**変異ごとに別の使い捨て作業木**が要る (`tools/mutation_worktree.py`)。
   同じ木に 2 本入れてはならない。

#### ノード間の性能差は未測定である — これを禁止の根拠にしない

**CC ベンチをノードを変えて測った実測は本 repo に存在しない。**「仕様が同じだから性能も同じ」も
「別ノードだからズレる」も、どちらも測っていない。手元にある唯一のノード間比較は pytest 全走の
wall-clock (bnode002 116.25 秒 / bnode009 200.72 秒 / bnode010 214.34 秒、[T-057] 2026-07-31) だが、
**これはプロセス生成とファイル I/O が支配する作業であり、CC の throughput 計測の代理値にならない。**
登録済み calibration は **2 件あり互いに別ノード**である (第 1 世代 bnode011 = within-run CV 1.17%、
第 2 世代 bnode048 = 同 1.25%)。同一 CCBench head・同一 workload・同一 thread 数で noise floor の
平均差は 1.774% だが、**取得が 19 日離れており実行ファイルの bytes も異なる**ため、node 効果・
occasion 効果・binary 効果が完全交絡している。**ノード間の分散は依然として答えられない。**

したがって**ノード間差の大きさを理由に fan-out を禁止しない。**

**ただし、差の大小とは別に交絡の問題がある。**処置 (workload / パラメータ / 構成) と node が
一対一に対応する配置は、**差がどれだけ小さくても処置差と node 差を推定上分離できない。**
`hostname` の記録は provenance にはなるが補正量にはならない (`s8b_floor_campaign` の
`host_provenance` が既に記録している。それでも分離はできない)。したがって:

- **job の内側で比較が閉じている fan-out は、集約する量が node 作用に対して不変なときに許す。**
  各 job が自分の中で stock と variant を対にして測る形が典型である。
  **「同一 job 内だから node は消える」を量の形を確かめずに使ってはならない** — 消える作用は
  量の形ごとに違う。**差 (`A − B`) が消すのは共通の加法 offset だけ**であり共通の乗数は残る
  (`q` 倍される)。**比 (`A/B`) が消すのは共通の乗数だけ**であり加法 offset は残る。
  **対照差と水準値を混ぜた量** (例: `劣化幅 − κ·stock`) は**どちらの作用も残る。**
  仮定した node 作用に対して集約量が不変だと言えないなら、job 間で並べずに protocol の
  明示的な写像へ送る。
- **性能値を job どうしで比較する fan-out は、protocol が投入前に node を block /
  randomization の因子として定義し、各処置の node 内対照または node 間反復と推定量と
  集約手順を固定している場合だけ許す。**一処置一ノードの割付けは完全交絡なので採らない。
  条件を満たせない比較は、同一 job・同一 node で protocol の schedule を保つ。

差の大きさそのものを知りたければ、同一 binary・同一 workload を N ノードへ同時投入して
分散を測ればよい。これは既存 protocol の通常運用ではなく**新しい測定 protocol**であり、
目的・N・割付け・推定量・成果物へ流入させないことを事前に固定してから実施する。
その設計は `docs/pegasus-node-variance-protocol.md` が正本である ([T-810])。
**同文書の land はいかなる投入の承認でもない** — 投入には同文書の 2 段階の承認が要る。
第 1 段 (実装・凍結・受入・予算・並走ガード・人間承認) が builder と生死確認を、
第 2 段 (第 1 段に生死確認の成功 receipt を加えたもの) が本走を解禁する。

#### 計測面は「臨界区間」と「準備」を分ける

計測の臨界区間 — probe → bench → post-probe → journal、および CV / floor / oracle の判定 —
は現行 protocol のまま維持する。**計測値を生成しない準備** (build、binary store、spec 検査など) は、
read / write 集合を分離できるなら fan-out の候補として扱ってよい。

#### fan-out が変えてよいのは投入時刻だけである (絶対規律 4)

**並行にしたからといって実験集合を増やさない。** workload・パラメータ・構成・レコード数・
thread 数・反復数・session 数・retry 枠は、凍結 protocol または calibrator の決定と exact に
一致させる。**「空きノードがある」「並行なら wall-clock が安い」は本数を足す理由にならない。**
floor / oracle の集約は expected cell 集合との完全一致を要求するので、余分なセルは受理されない。
追加の実験が要るなら、目的・N・割付け・推定量・成果物へ流入させないことを別 protocol で
事前に固定する。

#### 並行投入するときの手順

**本節は運用規範であり、汎用の並行投入 gate も N-job 完了 verifier も存在しない。**
太字の要件を機械強制済みと読まない。下の照合を機械が代わりにやってくれる consumer が無い場合、
それは人手確認であり、機械保証として報告しない。

- 投入の作法は 1 本のときと同じ (§8 のチェックリスト、`-o` / `-e` を repo 外へ、
  sanctioned な submit 形の逐語再利用)。
- **投入前に期待集合を書き出す。** 期待する job の集合、各 request ID、入力 hash、
  出力 namespace、期待成果物を先に記録する。完了時は全 request の terminal state・rc・
  receipt・成果物 hash が exact に揃ったことを照合する。
  **先に終わった成功 job だけで集計しない** — 欠落セル・欠落変異を含む ledger を
  完成扱いにすると参照集合が変わる。
- **request ごとに投入先と出力を一意化する。** submission directory と nonce を request 単位で
  分け、どの request がどの receipt・stdout・stderr に対応するかを 1 つの group manifest へ書く。
  `tools/pegasus/dispatch_compute.py` は **1 invocation = 1 request** で、N 本まとめて投げる
  CLI 面も group で待つ CLI 面も持たない。N 本並べるのは呼び手の責任である。
- **rc と request の対応を失わない。** 各 invocation を背景化したら PID を控え、
  request 単位で rc・`request_id`・scheduler state・receipt を回収する。
  パイプ・`xargs`・shell の一括 `wait` で rc を潰さない (F37 と同型)。
- **待ち手は 1 条件 1 本にまとめる。** N 本を投げたら「N 個そろう」ことを 1 本の待ち手で待つ。
  job ごとに待ち手を立てない。`tools/dev_wave_wait.py` は producer / 受入 lease 用であり、
  **scheduler request N 本を待つ CLI ではない。**代用に書き換えない。
- **単独性確認は各 job が自分に割り当てられたノード上で行う。** gen_S の logical host は
  `CPU Number` Min=Max=Std=48 で node の CPU を使い切るため、自分の request どうしが同じ node の
  CPU を分け合う構成にはならない (`qstat -Qf gen_S` 実測)。ただし `Exclusive submit = OFF` は
  変わらないので、**割当てを専有の保証と読まない** (§1)。
  なお計測の競合 probe (`composite_competing_probe`) は `pgrep` で**自ノードだけ**を見るので、
  **別ノードで走る自分の job は互いの probe に映らない** — この点で fan-out は同居より安全である。
- **1 本の失敗を全体の成功で塗り潰さない。** 失敗は infra 失敗 / 子 command 失敗 / timeout /
  成果物欠落に分類し、元 request の receipt を終端として保存する。**再投入は新しい nonce と
  新しい request で行い、元の request ID を控えておく。**成功した request を巻き添えで
  再実行しない。部分成功を「揃った」と報告しない。
- **`qdel` は自分の receipt に載っている request ID にだけ打つ。** 打つ前に `qstat -f <ID>` で
  request ID・job name・所有者・state を照合し、**QUE / HLD だけを対象にする。**
  RUN・所有者不明・receipt 不一致・`qstat` に見えない場合は打たず、ID と状態を handoff へ残す
  (並行 session の走行を潰した実害がある)。
- 投入本数の上限は queue 側にほぼ無い (`Submit Number Limit` と `Submit User Number Limit` は
  UNLIMITED、group は 200。2026-08-11 実測)。混雑時は超過分が待つ。

#### 現状 — まだ直列で、規約が追いついていない箇所

- **変異本走は「1 変異 = 1 qsub」を逐次に払う。** T-243 台帳 42 execution run の paired 差は
  9161.6 秒 (2.545 時間) で、D130 決定 (2) はこれを**順番待ち除去による削減量の上限側の目安**と
  位置付けている。**9161.6 秒の全量を順番待ちとして分離実測したものではなく、41 変異規模の
  束ね・fan-out はどちらも未実測である。**D130 / D131 が比べたのは「逐次 dispatch」と
  「1 job へ束ねて job 内直列」の 2 択で、**N 本同時投入は選択肢に入っていない。**
  束ねが消すのは順番待ちだけで内側の合計時間は不変だが、fan-out は内側も縮む。

  **D130 / D131 の未充足前提を fan-out の前提と読み違えない。** あれらは
  **harness 自体を計算ノードの 1 ジョブへ束ねる**経路に対する条件である。現行の
  `--runner-mode dispatch` は **harness がログインノードに居て**各変異の pytest だけを
  計算ノードへ投げる形 (§7.4 の呼出し) なので、N 本の fan-out も harness はログインに並ぶ。
  したがって cross-node `flock` (D130 条件 2) は掛からない — lock は
  `sha256(str(repo))` を鍵とする node-local `/tmp` のファイルで、作業木が別なら鍵も別である。
  walltime kill で `finally` 復元が飛ぶ懸念 (同条件 3) も、harness が計算ノードに載る前提の話である。

  **fan-out に本当に残っているのは実装・設計であって裁定ではない。** 未解決は
  (i) spec の分割と期待 node 集合の分割整合、(ii) N 本の ledger の併合と
  「registered == recorded」の担保、(iii) request・attempt・ledger 行の対応付け、
  (iv) 同時 dispatch 負荷とログインノードの admission、(v) `mutation_worktree.py` の
  container 名が固定 (`.izanagi-mutation-worktree`) なので **`--scratch-root` を N 個に分ける**必要。
  **いずれも未実測である。**着手は起票済みタスクで行う。
- **8c trial の workload fan-out は「探索 pilot を `--workloads` 単数で N 起動する」形だけを許す**
  ([T-809] 2026-08-11 ユーザー裁定)。`p3_autonomous_workload_trial.py` の
  `for workload in selected:` を割る実装はしない — 足りないのは起動側ではなく**検証側**であり、
  N 本を 1 成果物として束ねる verifier が存在しない。
  **満たすべき全条件は `docs/phase3-s8c-autonomous-trial-runbook.md` §5 が正本である。**
  N 起動自体は今日そのまま動く (fixture + `--no-build` の 3 process 同時が衝突ゼロで完走)。
  **ただし測ったのは supervisor 配線だけで、本番の律速 (role 呼び・build・verify・bench) への
  利得は測っていない。この比を fan-out の利得として主張しない。**
- **build を伴う 8c fan-out は許さない** (同上の裁定)。同一ノードでは他 process の compiler が
  bench を汚し (`bench_lock` は bench だけを排除し、`competing_bench_pids` は compiler を見ない)、
  別ノードでは上記の交絡と run 内 build cache 再利用の喪失が乗る。
  **正式系列 6 trial を 6 node へ散らしてよいという意味ではない** — 処置と node が一対一に
  対応する配置は完全交絡なので採らない (上の「ノード間の性能差」を参照)。現 manifest は
  `{trial_id, arm, holdout, campaign_id}` しか持たず node 因子が無い。配置は正式系列の
  着手時に prereg 側で再評価する。
- **既に job 内で並列化済みのものを候補に数えない。** 履歴監査 (`check_ai_provenance.py`) は
  commit 単位の thread pool を持ち、pytest は worker 並列、build は `-j` を持つ。
  これらは job 間 fan-out の対象ではない。
- **過去の並列化 survey の射程に注意する。** worklog (191) の survey は依頼文自体が
  「コア数を使い切る並列化」= job 内並列で、job 間 fan-out を探索軸に含めていない。
  **「並列化は調査済み」と読まない。**

### 7.6 孤児 job の hold (`orphan-hold.json`) — 止まったときの読み方と解除 ([T-403]、2026-08-16)

自動 qdel は「直前の照会が取消可能だった」ときだけ発行する (D142)。見送られた job は
**孤児として計算ノードに残り得る**。署名は保守側に倒してあり、実際には既に終端していた job でも
止まることがある (qdel が非ゼロ・例外を返した場合、dispatch mode の timeout など)。
孤児が生きうる間、次の 4 経路が fail-closed で止まる。

判定の権威は dispatch 出力 root 直下の **`output/pegasus-dispatch/orphan-hold.json`** で、
create-only の latch である。**lock ではない** — 「同一 checkout で harness を経由しない
並行 dispatch を作らない」運用契約の下でのみ後続を止める。自動解除はしない。
**この file 自体を書けなかった場合** (権限・容量など) は、変異 harness が書く停止記録
`<--out>.orphan-stop.json` が権威になる。その `reason.hold_error` に書込み失敗の理由が入る。

| 止まる経路 | 症状 |
|---|---|
| 次回投入 | scheduler command を 1 本も打たずに `rc=16`。nonce directory も作られない |
| 変異 source の復元 | 変異 harness が `rc=2`。**変異 bytes を作業ツリーに残したまま止まる** |
| 変異 worktree の廃棄 | container を保全して `failure="orphan-hold"` を wrapper receipt に書く |
| 受入赤の再確認 probe | probe worktree も dispatch 成果物も削除せず判定不能で止まる |

F47 型ラッチ (`submission-disabled.json`) と両方あるときは **F47 の文言が先に出る**。
F47 だけ解除しても hold で再び止まる。

**解除の手順 (順序を守る)。**

1. `qstat` で hold record の `request_id` を確認する。**RUN なら終端まで待つ。**
   **変異 harness が作った hold は `job_name` が null で、timeout 経路では `request_id` と
   `submission_dir` も null になり得る。** その場合は dispatch receipt → attempt sidecar
   (`--attempt-out`) → `output/pegasus-dispatch/` の submission directory 一覧、の順で照合する。
2. **手動 qdel は最後の手段。待ち時間の短縮だけを理由に取り消さない。** 自分の dispatch job を qdel すると F47 ラッチが武装し、
   その解除もユーザー手番になる。
3. 対象の不在または終端を確認してから、変異 harness が残した dirty path を
   `git checkout --` で復元する。dirty path は停止記録の `reason.dirty_paths` にある。
4. `git status` の clean と HEAD を確認する。
5. **最後に** hold file と停止記録 (`<--out>.orphan-stop.json`) の**両方**を手で削除する。
   停止記録が残っている限り、変異 harness は fresh でも `--resume` でも起動しない。

**変異 harness の停止記録は `<--out>.orphan-stop.json` (別 file)** で、`--out` の通常台帳
(`izanagi-dev-wave-mutation/v4`) は壊さない。表示される `--resume` コマンドは
**hold と停止記録を解除した後にだけ有効**である。

**受入全走の最中に hold が立つと acceptance receipt は発行されない。** 受入 lease の解放と、
probe worktree / dispatch 成果物の掃除は別物である — lease が解放されても、
保全された probe worktree と evidence は人手で処理するまで残る。

**fan-out では hold は shard の checkout 単位。** 兄弟 shard は完走するが merge されない。
**driver report と top-level stderr は hold path・request ID・`hold_error` を転記しない**ので、
どの shard が止まったかは driver report の preserved container から辿る。

**この機構が保護しない範囲 (誤読しないこと)。**

- `tools/pegasus/dispatch_compute.py` 経由の dispatch と、変異 harness / 変異 worktree /
  受入赤 checker だけを止める。
- `tools/pegasus/submit_*.sh` の直接 qsub、`orchestrator/campaign/patchharness.py` の
  checkout 復元・worktree 強制削除、ログインノードの local 実行は**対象外**である。
- qsub 前の永続 claim を持たないため、**SIGKILL と request ID 照会中の再 signal では
  hold が立たないまま終了しうる**。「全 job が fail-closed になった」とは読まない。

### 7.7 A-1 対測定の正式投入 ([T-1819] 2026-08-29 実測、[T-2272] / [T-2301] 2026-09-05 更新)

- **投入器は login 側 shell ではなく driver の `submit` サブコマンドである。** job body
  `tools/pegasus/paper_story_a1_paired.sh` は冒頭で「親が直接 qsub し、この file は投入器ではない」と
  宣言している。A-2 が login 側 shell に投入器を置くのは 2 workload の fan-out / fan-in を shell が
  担うためで、A-1 は fan-out / fan-in を driver が担う。この差は欠落ではない。
- **`--study-id` は必須で、既定値は無い (D1619)。** 値は凍結 policy の `study_id` のいずれかに限る:
  旧 v2 study `paper-story-a1-20260826-sized-v1` (1 job)、v3 pilot
  `paper-story-a1-20260901-balanced5-pilot-v1`、v3 sized `paper-story-a1-20260901-balanced5-sized-v1`
  (いずれも workload 別 3 job)。これ以外の ID と省略は qsub 前に拒否される。job body 側も
  `IZANAGI_A1_STUDY_ID` の未設定を `study ID differs` で拒否し、既定の study を持たない。
- login node から次の形で投入する。

  ```bash
  python3 -B -m orchestrator.campaign.paper_story_a1_paired submit \
    --study-id <凍結 policy の study_id> \
    --expected-head <現 HEAD の 40 桁> \
    --attempt-root <durable base>/<attempt-id>
  ```

- **`<durable base>` は policy の `execution.durable_measurement_base` が固定する。**
  投入器がこの base を `parents=True, exist_ok=True` で作るので、事前に作らない。
  attempt root 自体は作らない — 既存だと拒否される。
- **`<attempt-id>` は base 直下 1 階層の名前**で、`[A-Za-z0-9][A-Za-z0-9._-]*` に収める。
  同名の attempt root・intent・submission receipt・completion receipt・stdout・stderr の
  いずれかが残っていると qsub 前に拒否される。作り直すときは新しい attempt-id を使う。
- 投入前に tracked worktree が clean で、`--expected-head` が現 HEAD と一致している必要がある。
  どちらも driver が qsub 前に検査する。
- **v3 study は workload 別に 3 request を driver が順に qsub する** (`write-heavy` → `balanced` →
  `read-heavy`)。qsub の前に group intent `<base>/<attempt-id>.intent.json` を create-only で書き、
  attempt root 直下に `receipts/`・`raw/`・`barrier/`・`jobs/<workload>/scheduler/` を作る。
  request ごとの qsub stdout / stderr・request-id・qstat 可視性は `jobs/<workload>/scheduler/` に、
  job 本体の stdout / stderr も同じ場所に返るので repo は汚れない (D1291 の規範に適合)。
- **3 request が揃って初めて group receipt `receipts/submission.json` が出る。** 途中の request が
  失敗・不定 (qsub 非 0、stderr 非空、request ID を読めない、request ID の三つ組が一意でない) なら
  driver は `receipts/submission-failure.json` に workload ごとの状態
  (`accepted` / `failed` / `indeterminate`) を書いて rc=2 で止まる。**受理済みの request を driver は
  取り消さない。** 残った job は job body 側で group receipt を 60 秒待ち、現れなければ prebench の
  failure terminal を書いて bench に入らず終わる。
  この attempt は再利用せず、新しい attempt-id で取り直す。
- **intent があって group receipt も failure も無い状態は「投入したかどうか不明」である。**
  driver は同じ attempt へ二度目の qsub をしない。これは意図的な fail-closed であり迂回しない。
- **bench の前に 3 job の barrier がある。** 各 job は自分の workload の両 arm を build・verify してから
  `barrier/ready/<workload>.json` を書き、ちょうど 3 つの ready が揃ったときだけ `barrier/bench-go.json`
  と `barrier/bench-start/<workload>.json` を経て bench に入る。**同じ base の先行 attempt が
  bench barrier に達していると、同じ study の group 再投入は拒否される**
  (`prior attempt reached the bench barrier; group rerun is prohibited`)。途中中断と片側 commit を
  invalid に閉じる D1295 決定 7 の実装であり、迂回しない。
- **group completion は 3 job がすべて終端してから login で行う。**

  ```bash
  python3 -B -m orchestrator.campaign.paper_story_a1_paired complete \
    --study-id <submit と同じ study_id> \
    --expected-head <submit と同じ HEAD> \
    --attempt-root <submit と同じ attempt root>
  ```

  `complete` は group receipt を intent と突き合わせ、`jobs/<workload>/raw/results/` の
  `result.json` / `receipt.json` と scheduler の終了状態、barrier の三つ組を検査してから
  `raw/job-terminal.json` (group terminal) と `receipts/completion.json` (group completion receipt) を
  書く。1 workload でも欠ければ receipt は出ない。materialize はこの 2 file を入力に取る
  (引数は driver の `materialize --help`)。
- **estimand の読み (D1619):** 論文の contrast は D1262 (各 workload の「固定 X − backoff なし」) が現行で、
  D1295 の 5-rep ブロック交互 + AB/BA 均衡はその estimand の上で使う配置である。D1295 決定 4 の
  「常に static10 − adaptive」は配置の記述であって estimand の再定義ではない。
- この経路は `tools/pegasus/` の admission 登録簿の対象外である。登録簿は `tools/` 配下の実行体を
  分類するもので、driver の subcommand は管轄外である。§7.0 の実行場所判定にも掛からない —
  qsub 自体は login 側で行う軽い操作である。

### 7.8 B-4 床値 (floor-pair) の窓 job と finalize job の投入 ([T-2288] 2026-09-18 着地、w1 は 2026-09-19 に初回実投入)

凍結済み spec 3 本 (`output/env/pegasus/floor-pair/t2288-f1/`、D2138) を `orchestrator/campaign/floor_pair_driver.py` の
`--execute-window` / `--finalize` で走らせる資材は、login 側の `tools/pegasus/submit_floor_pair.sh` (submitter) と
計算ノードの `tools/pegasus/floor_pair_campaign.sh` (job body) である。着地 wave では実 qsub・計算ノードでの実行・
8 変数の伝播・実効 walltime・signal 配送を実測していなかった (F660)。**初回実投入 (w1、2026-09-19、3 spec とも
terminal `complete`) で実測した事実**は `output/insights/2026-09-19/t2288-floor-pair-w1/README.md` が一次資料で、
この機体で次回 (w2 / finalize) に効く点だけを挙げる: (1) 計算ノード側の `PBS_JOBID` は `0:10711.nqsv` の形 (`0:`
接頭辞)、(2) NQSV の request accounting (`Ended Request Time` / `Elapse`) は `-e` で指定した `scheduler.stderr` に出る
(`scheduler.stdout` は空。`tools/dev_wave_wait.py compute --accounting-file` に渡すのはこちら)、(3) `job-result.json` は
8 変数のうち `FP_EVIDENCE_DIR` と `FP_ELAPSTIM_REQ` の受信値を写さない (6 変数は値で、残り 2 個は出力先と形式検査の通過で
確認)、(4) 1 窓 job の所要は 69〜77 分 (124 session、1 session ≈ 34〜37 秒)、(5) `place` は login node で完了する
(`place_record` は site 検査を持たない)。signal 配送と SIG_IGN 継承 (F1012) は walltime 前に終わる走では検証されない。

- **1 job = 1 spec × (1 窓 | finalize)。** 3 spec × 2 窓 = 6 window job + 3 finalize job。並走できるかは admission に
  依存し、資材は保証しない。
- **投入元 checkout は detached で、各 spec の w1・w2・finalize の 3 job を同じ HEAD `H` から投入する** (申し送り 2)。
  driver は finalize で両窓 header の `loaded_head` と finalize 時の HEAD の exact 一致を要求する。3 spec を同じ `H` から
  投げるのは運用の単純化であって要件ではない。**測定の途中で checkout の HEAD を進めない** (成果物の commit は
  3 段が終わってから)。submitter は同 spec の他窓 JSONL が既にあればその header の
  `loaded_head` と現 HEAD の一致を、finalize では両窓 JSONL の存在・header 一致・末尾 record が terminal であることを、
  qsub 前に確認する (driver の検査の代替ではない早期拒否)。
- **binary は checkout ごとに `place` する** (D2069 項 7)。ignored file なので merge で移らない。
  `python3 -m orchestrator.campaign.b4_binary_record place --record output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json --source-root /work/1/SFC/tanab/izanagi-b4-floor-binaries --env-tag pegasus`
  を投入元 checkout で先に実行する。
- **窓の手前・末端に投入しない** (申し送り 4)。submitter と job body は `now >= not_before` かつ
  `now + elapstim_req <= not_after` (UTC 実時計、半開区間) を検査し、外れれば driver を起動せず rc=4 で止める
  (create-only の path は未消費のまま残る)。walltime は submitter が 1 箇所で決める: window job `24:00:00`
  (gen_S の上限。窓の喪失は回復不能で、要求超過の費用は queue 待ちだけ)、finalize job `00:30:00`。24 h は
  成功保証ではない — walltime 切れ・node 障害で terminal の無い JSONL が残ればその窓は失われ、再走は無い。
- **spec × 窓は 1 回だけ投入する。** submitter は対象窓の JSONL が既にあれば拒否するが、同時投入は排除しない。
  qsub の結果が不明 (`indeterminate`) でも自動再投入しない。
- **finalize は両窓の terminal が出て結果を受け入れてから投げる。** driver は `incomplete` terminal の窓からも
  `not_generated_*` の summary を create-only で作る (失敗の記録)。失敗 summary も 1 回限りで、成功 summary への
  再生成には使えない。
- **既存の出力を削除・置換・延長しない** (申し送り 5、D2138 却下肢)。窓を使えずに終わった場合は未実施の凍結として
  記録し、新しい凍結を別 commit で行う。
- **証拠の置き場** は repo 外 `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/<nonce>/`。submitter が
  `pre-submit.json` / `qsub.*` / `submit-receipt.json`、scheduler が `scheduler.stdout` / `scheduler.stderr`、job body が
  `driver.stdout` / `driver.stderr` / `job-result.json` を書く (投入側は job body の file を先に置かない)。
  測定 JSONL と summary は凍結 spec が指す repo 内 path (投入元 checkout) に create-only で書かれる。
- 投入 (login node、投入元 checkout の root で):

  ```bash
  bash tools/pegasus/submit_floor_pair.sh --workload rr95 --window w1 --dry-run   # qsub だけを省く (gate は同一)
  bash tools/pegasus/submit_floor_pair.sh --workload rr95 --window w1             # w1 は 2026-09-19T00:00Z 以降
  bash tools/pegasus/submit_floor_pair.sh --workload rr95 --window w2             # w2 は 2026-09-29T00:00Z 以降
  bash tools/pegasus/submit_floor_pair.sh --workload rr95 --finalize              # 両窓の terminal の後
  ```

  `--workload` は `rr95` / `rr50` / `rr5`。spec の relpath と sha256 は submitter が D2138 項 7 の値で pin しており、
  引数で差し替えられない。
- **未検証の前提**: 計算ノードの時計が走行中に安定していること、scheduler の終了猶予、`nm` / `pgrep` の存在
  (job body は起動時に `command -v` で確認する。finalize は session を走らせないので `nm` / `pgrep` を使わないが、
  同じ集合を要求する)、compute での動的 link 解決 (binary の NEEDED は system lib 4 本)。**job body の bash が
  SIGTERM を ignore も block もしない状態で起動することは未検証** — 計算ノードの job は SIGTERM を SIG_IGN で継承する
  (F1012) ので、その場合 `record_signal` は発火せず、walltime 到達時は KILL で driver が止まり、terminal の無い JSONL と
  `job-result.json` の欠落が残りうる。trap の存在を終了記録の保証と読まない。
- job rc=0 は「床値が生成された」を意味しない。driver は window / finalize の result JSON (`driver.stdout`) を書いて
  rc=0 を返し、`status` は別に持つ。n = 62、欠測率、実 campaign の 24 時間以上の分離、採用は証拠確認者
  (D1641、申し送り 6) と集約 (D1974、申し送り 7) に残る。

## 8. 投入前チェックリスト

- `qstat -Q` で現在利用可能なキューを確認した
- **repo を submit directory にする job は `qsub -o <file> -e <file>` で scheduler 出力を repo 外へ
  向けた。** 既定では submit directory へ書かれるため、tree の clean を要求する job は
  **前回 job の出力自体で落ちる**。`-o` / `-e` には directory でなくファイル path を渡す
  (directory は `NQScrereq: [BSV EINVAL] Not a regular file.` で受理されない)。
  job script に絶対 path を書く形は採らない — 機体固有値を repo へ持ち込むため
- **wave worktree から exploration campaign / 8c trial を実走する job は、job script が
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` を job 専用の `/work` 配下へ export した** ([T-422] / F98。
  実 path は job script が組み立て、shared code・test・docs へ固定値を書かない。process 起動前に
  一度だけ設定し実行中に変更しない。未設定のまま worktree 内で materialize しようとすると
  `ensure()` が fail-fast で拒否する)
- `pegasusinfo` で混雑状況を確認した
- **独立に投げられる job を 1 本ずつ直列で払っていない。** 並行投入してよいかの判定は §7.5
- wall time と node 数 (`-b`) が処理に適切である
- OpenMP threads は 48 以下である
- hybrid 実行は node あたり `MPI processes × OMP_NUM_THREADS <= 48` である
- **重い処理をログインノードで実行していない** — GPU プログラム、ベンチ、calibration、
  floor/oracle に加え、**ビルドとテスト (pytest の全走・部分走を含む) も計算ノードで行う** (§7)。
  **provenance 履歴監査 (§7)** も同じ扱いとし、免除は `--message-file` の preflight だけである
- **この列挙に無いスクリプトも、§7.0 の基準 (量で判定・3 値分類・測り方・規範値) で分類してから
  実行場所を決めた。** 数値と手順は §7.0 が唯一の正本で、ここには再掲しない。
  入口は `tools/README.md`
- `python3 tools/check_ai_provenance.py` をログインノードで打つと自動 dispatch され、
  receipt が `output/pegasus-dispatch/<nonce>/` に残る。**`rc=16` は dispatch の infra 失敗であって
  監査結果ではない** (違反件数は rc=1 で返る)
- `tools/mutation_harness.py` の pytest collection/実行 dispatch が queue 混雑で `rc=16`
  になった場合も同様に infra 失敗であって変異判定の結果ではない。spec の `timeout_seconds` と
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE` (既定 900s) を広げた上で再試行する
- 計算ノードでは**テストの既定並列度が affinity 全数**になっている (明示 `-n` /
  `IZANAGI_TEST_NPROC` / `jobs=1` は従来どおり後勝ち = 「既定が最大」であって「全実行が最大」ではない)
- ビルドは**規範として計算ノードで行い、`-j` 既定も site 由来**にする。**「強制」は全 build に
  掛からない** — 機械強制が発火するのは §7 が列挙した 6 module だけで、
  `t152_write_intent_coverage.py` と `silo_ladder_rung1.py` の直接 CMake には site gate が無い
  (計算ノードで affinity
  全数、非 Pegasus は 16)。cache hit 時に記録される `-j` が cache 作成時の値と食い違う場合は
  受理する — 並列度はバイナリ bytes に影響しないという裁定である (D103 決定 4)。
  binary identity の検査 (`bin_sha256`、trace diff、`src_token` 再照合) は緩めない
- 単独性の確認 (pgrep 等) は、割り当てられた計算ノード上で行う (割当てを専有の保証と見なさない)
- **CC 合成 campaign** は supervisor と LLM 4 役 (planner / coder / auditor / critic) をログインノード、
  build / verify / bench を計算ノードに置く (D106)。
  **`campaign` の dispatch task は未実装**であり、driver の終了コードが iteration の `outcome` を
  反映しない等の契約不足が解消するまで、campaign を計算ノードへ送る sanctioned 経路は存在しない
- **計算ノードでの role 実行は D122 が条件付きで解禁した** (旧「計算ノードで `claude -p` を
  起動しない」を supersede)。許されるのは `p3_autonomous_workload_trial.py` の
  `--allow-pegasus-compute-transport` を**明示指定**した場合だけで、compute site・qsub 文法に
  適合する `PBS_JOBID`・committed policy と exact 一致する lowercase proxy 2 key・TLS trust
  override 不在・従量経路 env 不在・policy surface 健全のすべてが揃わなければ fail-closed で拒否する。
  flag 省略時は従来どおり proxy を落とす。**MITM を防いだとは主張しない** (D122 決定 (7) の残余)。
  **(2026-08-11 訂正) 本項にはかつて「build / bench の計測は `_site_admits_measurement` が
  Pegasus を拒否したままであり ([T-277])、この拒否が生きている間は role 出力が build / run へ
  到達しない」とあったが、逆である。**引用している [T-277] / D122 の commit `6a51426c`
  「計測パスの受理集合・env 契約・build identity・attestation を開く」が、まさにその拒否を開いた。
  現行の `orchestrator/campaign/p3_s4_loop_trigger_gating.py::_site_admits_measurement` は
  `{OTHER, PEGASUS_COMPUTE}` を受理し、拒否するのは `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` /
  未知値だけである (`orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_site_admission_matrix`
  が exact に固定している)。**計算ノードでの計測は site gate では止まっていない。**
- `/scr` に置くデータの退避処理がある
- `check_quota` と `rbudgetcheck` で容量・ポイント残高を確認した
- **投入する `qsub` の呼出し形を sanctioned な submit script と突き合わせた。** 使い捨ての job script でも
  パラメータの渡し方を自分で発明しない。この scheduler にスクリプトへ位置引数を渡す syntax は無く、
  既存の submit script は例外なく `qsub -v VAR=value <script>` の環境変数経由である
  (`tools/pegasus/submit_floor.sh`)。逐語再利用の対象は環境正規化だけでなく**投入インタフェースも含む**
- **床値 official の sanctioned な投入は `tools/pegasus/submit_floor.sh --confirm-official-floor-run`
  だけである** ([T-2324]、方式は D926)。承認は submission nonce に束ねて運ばれ、job script が exact
  一致を確かめる。**`qsub -v` を自分で組み立てて `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` を渡す経路は
  D926 の保証範囲外である** — nonce 束縛の意味が失われるので、認証された走行として扱わない。
- ジョブ投入 (`qsub` / submit wrapper) の実行環境を確認した。原則はユーザー自身の端末。
  対話セッション内 shell (`!` 実行を含む) からの投入は、書き込み不永続・資格情報差で無効な
  request を作る (F47、2026-07-28 に request 873213 で実測) ため引き続き禁止。
  **例外 (2026-07-29 ユーザー裁定 = F49 (ii))**: 背景 job セッションの Bash tool のように
  書き込みが実 FS へ永続するセッション型からは投入してよい (反例実測 = request 873583)。
  その場合、投入直後に有効性検査を必ず行う — (a) 出力 dir が実 FS に永続している、
  (b) `qstat` で request が可視である、(c) 終了後に PBS 会計痕跡 (`.e`/`.o`、ポイント消費) が
  実在する。**証拠の取り方と失敗の型は分ける** (`tools/pegasus/dispatch_compute.py` が正本):
  (a) は**計算ノード側が書いた marker の実在**で確かめる (親が自分で書いた dir を読み直しても
  自己確認にしかならない)。(b) の `qstat` が**権限系エラー** (`Not permitted` 等) を返す、
  または成功したのに request が不在なら **F47 型 (不永続・資格情報不整合)** とみなし、
  以後の自動投入を止めてユーザー端末へ引き渡す。接続不能・timeout 等の**一時的エラーは再試行し、
  全滅でもその 1 回を失敗にするだけで恒久停止しない** (瞬断で harness を止めない)。
  (c) の会計痕跡は猶予付きで再取得し、欠けてもその 1 回を失敗にするだけとする
