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

取得・供給の手順は `tools/pegasus/README.md` §6 を正本とする。3 本の合計は 43 MB 程度で、
certify が使う gflags / glog の pinned source はこの helper の管理単位ではない (所在の正本は
policy.json の `gflags_source_path` / `glog_source_path`)。**2026-08-06 に home 配下から移した
時点で 2 本とも非 shallow** (`rev-parse --is-shallow-repository=false` を実測)。

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

- **判定量 = user slice の raw `memory.current`。** 天井は 14 GiB
  (`login_headroom.CEILING_BYTES`。数値はこの 1 箇所だけに置く)。**reclaim できる file cache を
  差し引く案は採らない** — ユーザーが指した「合計」の再定義になるため。差し引けば実効許容量は
  ほぼ倍になるが、それは別裁定が要る。
- **1 コマンドへ渡す予算** = `min(4 GiB, 天井 − 現在使用量 − 生存中の予約 − 予備 2 GiB)`。
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
| `tools/claude_session_ledger.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/certify_calibration.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/collect_receipt.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/collect_t126_qualification.py` | `unknown` | `unmeasured; unbounded input surfaces remain` |
| `tools/pegasus/dispatch_compute.py` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/exec_calibrate.py` | `dispatch-required` | `static arbitrary-exec classification` |
| `tools/pegasus/fetch_third_party.py` | `local-ok` | `runbook §7.0 実測` |
| `tools/pegasus/floor_campaign.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/floor_scoping.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/make_acquisition_receipt.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t139_positive_control_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t139_positive_control_probe.sh` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t139_r4_env_probe.pbs` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/probes/t139_r4_env_probe.py` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t139_r4_env_probe.sh` | `dispatch-required` | `static compute-side call-site classification` |
| `tools/pegasus/probes/t293_perf_site_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t293_perf_site_probe.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t419_probe_causality.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t419_probe_causality.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_probe.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_probe.py` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_recover.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/probes/t503_restore_durability_verdict.pbs` | `unknown` | `unmeasured probe artifact` |
| `tools/pegasus/run_probe.py` | `dispatch-required` | `static semantic-site classification` |
| `tools/pegasus/silo_ladder_rung1.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/smoke_probe.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/submit_certify.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_floor.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | `local-ok` | `legacy-admitted (未実測)` |
| `tools/pegasus/submit_t126_qualification.sh` | `unknown` | `unmeasured; preflight input surfaces remain` |
| `tools/pegasus/t126_qualification.sh` | `dispatch-required` | `static job-body classification` |
| `tools/pegasus/t141_region_profile.sh` | `dispatch-required` | `static job-body classification` |

- **この投影検査が保証しないこと。** 検査するのは正本と docs の間の (path, class, evidence) の
  一致だけである。`reason` / `primary_gate` の散文が正本と食い違っても検出しない ([T-522] で
  裁定へ返した)。class の正しさ、資源の実測、hook が `.claude/settings.json` に実配線されて
  いること、`python3 -c` や cwd 経路など parser が実行体として認識しない綴りは、いずれも
  この検査の範囲外である。
- **分類の測定はユーザー端末の手番である (2026-08-05 ユーザー裁定)。** 上の
  `systemd-run --user --scope` 手順は計算ノードでは動かない (2026-08-05 実測: PBS ジョブに
  user systemd session が無く `$DBUS_SESSION_BUS_ADDRESS` / `$XDG_RUNTIME_DIR` が未設定。
  ジョブ自身の cgroup は `nqs-jsv.service` 配下で他テナントと混ざる)。一方 hook は
  `tools/pegasus/` 配下の未登録実行体をログインノードで拒否する。**したがって「登録には実測が要る / 実測には登録が要る」という
  循環がある** (F123)。裁定はこの循環を当面そのまま追認したものであり、**ログインノード上の
  ユーザー端末 (hook の管轄外) が現行唯一の正規な測定面である。** 手番は次のとおり。
  - **AI セッション・子エージェント・自動化は分類の実測を自分で行わない。** hook の拒否を
    迂回して得た値は、綴りを問わず分類の根拠にしない (迂回自体が禁止である)。hook が未配線または
    解析できない実行面を測定の抜け道に使うことも同じく禁止で、本節が下で列挙する「機械強制なし」の
    面を抜け道の目録として読んではならない。
  - 実測が無い実行体は `unknown` に倒して**止める**。止めた事実と、必要な測定を、上の
    「記録すること」の全項目 (commit / argv / 入力の総 bytes と件数 / `memory.max` / 観測ピーク /
    繰り返し数 / 測定日) を満たす依頼としてユーザーへ返す。本節の記録欄と実測表へ入れてよいのは、
    ユーザーが端末で実行して返した値だけである。
  - **測定専用の bounded surface を設ける案は [T-481] の族再設計に同梱して決める** (未実装)。
    **計算ノードで動く測定手順へ本節を改訂する案は採らない** — 上の実測がその前提を否定しており、
    再提案には新しい実測が要る。
  - この手番が確定した帰結として、**hook 面で `systemd-run` 経由の綴りを塞いでも正規の測定面は
    失われない** ([T-518] (d) の閉じ方の入力。閉じるかどうかは [T-481] の族再設計で決める)。
- **投げ先。** ログインノードから**自動**で計算ノードへ dispatch されるのは下表の exact task だけ
  である (D103 決定 2 / D105 決定 3 が enum を閉じている)。表に無い重い処理は自動化されていない
  ので、`qsub` / `qlogin` で自分で計算ノードを確保して走らせる。sanctioned な経路が無ければ
  **走らせずに止める**。task を勝手に増やさない (追加には D105 の supersede が要る)。
- **未充足の明示。** ユーザー依頼は「一定メモリ以上のものを計算ノードへ**投げる**」だったが、
  **本節が実装したのは admission 規範 (login で走らせない) だけで、第 3 の entry point を
  閾値判定後に自動 dispatch する経路は実装していない**。D105 決定 3 が task enum を 2 値に
  固定しており、拡張には (a) D105 の supersede、(b) `_job_run` 側の `env_allowlist` 強制、
  (c) stdin / cwd / artifact 可視性、(d) 子 rc の意味の確定が同時に要る。
  **この差分は依頼のうち「自動で投げる」部分を満たしていない** — 裁定待ちとして worklog に残す。
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
- 計算ノードに gflags / glog は無い。永続領域の pinned ソース (gflags v2.2.2、glog v0.5.0。
  所在の正本は policy.json の `gflags_source_path` / `glog_source_path` で、現在は
  `/work/SFC/<user>/github/` 配下。home 配下ではない) から /scr で使い捨て static build する
  (certify が自動実行)
- perf は dispatcher (/usr/bin/perf) がカーネル不一致で使えない。実体
  (/usr/lib/linux-tools/<版>/perf) を policy.json の候補から機能 smoke つきで選定し PATH 注入
  する (ノードにより導入版が異なる: 実測では bnode 側 5.15.0-100/135、ログイン側 101/136/173)
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

`tools/audit_dangling_commits.py` はこの directory を「repo 外の同一実体」の探索根として使う。
repo 内のコードに機体固有の絶対 path を焼かないため、所在の指定は次のどちらかで外から渡す。

```
python3 tools/audit_dangling_commits.py --offrepo-root /work/1/SFC/tanab/dev-wave-jobs
export IZANAGI_DEV_WAVE_JOBS_DIR=/work/1/SFC/tanab/dev-wave-jobs   # 上と同義。CLI 指定が優先する
```

- 指す先は **`dev-wave-jobs/` そのもの**である。§7.3 の `IZANAGI_WAVE_LEASE_DIR` は
  その下の `land-lease/` を指す別変数で、探索根に渡しても意味がない (成果物が無い)。
- どちらも未指定なら探索は行われず、その旨が出力される。**黙って縮まることはない。**
- 抑止されるのは、到達不能側が regular blob で、basename・実行 mode・bytes が一致し、かつ
  **main に land 済みの文書がその絶対 path (または探索根より下位の祖先 dir) を参照している**
  場合だけである。bytes だけ一致する候補は抑止せず、報告行に注記が付く。

### 7.3 並行 wave の受入 lease (`tools/wave_land_window.py`)

並行 dev-wave が同じ main を base に受入全走を重ね、追い越された側の約 1055 秒が丸ごと無駄に
なるのを減らすための**排他予約**である。lease directory は
**`/work/1/SFC/tanab/dev-wave-jobs/land-lease/`** (作成済み、mode 700)。repo 外に置くのは
wave worktree の clean-tree gate と land の untracked 検査に掛けないためである。

```
export IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease
W=<wave slug (branch 名の末尾。例 dev-wave-t642-s04-scope)>
M=$(git rev-parse main)           # 40 桁。自分の checkout の local main
python3 tools/wave_land_window.py claim --wave "$W" --main-sha "$M"
```

- `state=acquired` のときだけ受入全走を投入する。`held` / `queued` / `stale-held` / `unavailable`
  および非 0 rc では**投入しない**。`held` / `queued` なら local main を取り直して再度 `claim` する。
- **待ちは 30〜120 秒周期の loop にする ([T-684])。** `claim` は待ち行列 (FIFO 相当) の待ち札を
  作り、呼ぶたびにその生存を更新する。**待ち札は最後の `claim` から 300 秒で失効する**ので、
  一度だけ `claim` して長く放置すると順番を失い、後から来た wave に追い越される。
  `queued` は「lease は空いているが自分より先に待っている wave がいる」を意味する。
- **受入を直ちに投入できる状態になってから待ち始める。** 先頭を取ってから準備に手間取ると、
  その間ほかの wave 全部が待つ (head-of-line blocking)。
- **FIFO が保証するのは「後着が先着を追い越さない」ことだけで、待ち時間の上界ではない。**
  待ち時間は待ち行列の長さと受入 1 回の所要 (1055〜1273 秒) に比例する。
- **`acquired` の直後に local main を取り込んでから投入する。** 待っている間に先行 holder が land
  するので、`claim` 時の `main_sha` は待ち始めた時点の main ではない。取り込まずに走らせると
  land 対象 tip が main の子孫でなくなり、全走をもう一度やり直すことになる (2026-08-09 に
  12 commit 差で 1324 秒を空費)。
- 受入と land の**どの終わり方でも** `release --wave "$W"` する (赤・失敗・中断を含む)。
  他 wave の lease は消せない (holder digest 不一致なら `not-owner` で何もしない)。
- land が成功したときだけ、保存した land 結果 JSON を渡して通知文を作り、`ListAgents` で
  照合した peer へ 1 度だけ送る。

```
python3 tools/dev_wave_land.py ... > land-result.json    # rc と JSON を保存する
python3 tools/wave_land_window.py message --kind landed --wave "$W" --land-json land-result.json
```

- 取り残した lease は TTL (既定 2400 秒) で自然失効する。失効までの間は他 wave の受入投入が
  止まるので、release を忘れないこと。
- **既知の限界 (裁定パッケージ)**: TTL 超過で lease を取り直した場合、旧 holder の受入は
  止められない (fencing token が無い)。その場合の帰結は本機構が無かった場合と同じ競合であり、
  悪化はしない。release の権限証明は wave slug の digest だけである。
- **待ち行列の既知の限界 ([T-684])**: 待ち行列を扱えない状況 — 走査の失敗、entry 4096 件または
  待ち札 64 枚の cap 超過、自分の待ち札を登録できないこと — では待ち行列を捨てて従来の競争へ
  縮退する。**停止しないことを公平性より優先する**設計である。旧版の `claim` を走らせる wave は
  待ち札を無視するので、混在中は公平性を保証しない (退行はせず、待ち行列が無い状態へ戻るだけ)。
  同着 (mtime 粒度内) は holder digest で決定的に割るため厳密な FIFO ではない。

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
  build / bench の計測は `_site_admits_measurement` が Pegasus を拒否したままであり ([T-277])、
  この拒否が生きている間は role 出力が build / run へ到達しない
- `/scr` に置くデータの退避処理がある
- `check_quota` と `rbudgetcheck` で容量・ポイント残高を確認した
- **投入する `qsub` の呼出し形を sanctioned な submit script と突き合わせた。** 使い捨ての job script でも
  パラメータの渡し方を自分で発明しない。この scheduler にスクリプトへ位置引数を渡す syntax は無く、
  既存の submit script は例外なく `qsub -v VAR=value <script>` の環境変数経由である
  (`tools/pegasus/submit_floor.sh`)。逐語再利用の対象は環境正規化だけでなく**投入インタフェースも含む**
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
