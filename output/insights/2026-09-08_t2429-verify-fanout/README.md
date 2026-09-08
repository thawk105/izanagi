# [T-2429] 認証 campaign の正しさ検査をノードへ分割する — 生死確認 3 本と裁定

## 結論

- **1 回建てた実行ファイルは、建てたノードとは別のノードで同一 bytes のまま動く** (生死確認 1)。
  A-6 attempt `a6-20260908b` が bnode031 で建てた 4 本 (stock / 採用版 × trace / perf) は共有 `/work` の
  durable cache に certification.json の記録どおりの sha256 で残っており、bnode012 で原本・`/work` 複製・
  `/scr` (ノード内蔵) 複製の 3 か所とも記録値に一致し、trace 版は rc=0 で trace を出し、perf 版は rc=0 で
  trace を出さなかった。
- **1 要求で複数ノードを取り、head から兄弟ノードへ ssh で仕事を届けられる** (生死確認 2)。`-b 2` の
  要求で `PBS_NODEFILE` に 2 ノードが並び、head から兄弟へ BatchMode の ssh が通った。
- **CLI の `-b` は script 内の `#PBS -b` directive に優先する** (生死確認 3)。job body の directive を
  変えずに submitter が渡す `-b $SCHEDULER_NODES` だけでノード数を増やせる。
- 裁定: 「配る」を採り、再現可能ビルドは採らない。輸送は単一の multi-node request と ssh。詳細は
  「裁定」節。

## 「ノードを跨いで建て直すと bytes が変わる」の一次資料

D1763 と `output/insights/2026-09-08_t2411-a6-readheavy-submitted/README.md` は「ノードを跨いで
建て直すと bytes が変わることは 2026-09-02 に実測済み」と書く。一次資料を辿ると、実測の本体は
`output/insights/2026-08-31_t1905-b10-formal-run/README.md` (88-108 行) の **「job 固有の作業 path が
binary に混入する」実測** (`.rodata` の `__FILE__` 由来 8 件と RUNPATH、path 非依存化 2 巡で差分が
149 → 56 → 45,454 bytes と収束せず) であり、**別ノード 2 台で建て直して sha256 を突き合わせた生記録は
無い**。正確には「別 job で建て直すと bytes が変わる」が実測で、「別ノード」はその含意である。
含意自体は正しい (別ノードで建てるとは別 job で建てることだから) が、後続文書の言い切りは一次資料より
強い。本 wave はこの点を書き分け、実測で置き換えた。

## 生死確認 1 — 別ノードでの同一 bytes と実走 (job 982835.nqsv)

- 投入 06:53 JST、開始 07:01:12 (Pre-running が約 8 分)、Elapse 9 秒、host **bnode012** (建て元 bnode031)、
  boot_id `1cb51557-9e47-4cab-9deb-6c0b6fdea735`、glibc 2.35、競合 `ycsb_` プロセス 0。
- 対象: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/cache/contracts/e576e9cd…/<store>/cc/silo/ycsb_silo.exe`

| binary | 記録値 (certification.json) | 原本 / `/work` 複製 / `/scr` 複製 | ldd 未解決 |
|---|---|---|---|
| stock trace | `098cdd82…d25bcbf` | 3 か所とも一致 | 0 |
| stock perf | `d3f94526…8e9e2c` | 3 か所とも一致 | 0 |
| 採用版 trace | `f9eeb78e…675a23b9` | 3 か所とも一致 | 0 |
| 採用版 perf | `98f65c2d…0229c64` | 3 か所とも一致 | 0 |

- 実走 (legacy 構成 `-ycsb_tuple_num=200 -thread_num=4 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=true
  -ycsb_max_ope=5 -extime=1 -clocks_per_us=2100`、`IZANAGI_TRACE_DIR` 設定、`/scr` 複製を実行):

| run | rc | wall | trace file | trace C 行 | stdout の `commit_counts_` |
|---|---|---|---|---|---|
| stock trace | 0 | 1.02 s | 4 | 512,567 | 512,567 (batch 0) |
| 採用版 trace | 0 | 1.01 s | 4 | 503,567 | (同様) |
| stock perf | 0 | 1.02 s | 0 | 0 | 1,523,288 |
| 採用版 perf | 0 | 1.01 s | 0 | 0 | (同様) |

- 動的依存: NEEDED は libstdc++ / libm / libgcc_s / libc のみ。RUNPATH は消滅した
  `/scr/tanab/paper-story-a2-certification/0_982234.nqsv/dependencies/lib` を指すが解決対象が無く無害。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/summary.txt`。

## 生死確認 2 — 2 ノード要求と ssh (job 982842.nqsv)

- `#PBS -b 2`、Elapse 5 秒。head **bnode011**、`PBS_NODEFILE` = `bnode011`, `bnode016`。job script は
  job 0 (head) でだけ走った。
- `ssh -o BatchMode=yes bnode016 'hostname; cat /proc/sys/kernel/random/boot_id'` → `bnode016`、
  `2fc2eb68-e86c-46b1-9f67-b3c3719e2f97`。続けて読もうとした `/work/.../bin/stock-trace.exe` は
  生死確認 1 がまだ走っておらず未作成だったため `ssh_rc=1`。到達と実行は成立している。
- `mpirun` は Intel oneAPI (intelpython) の hydra で、OpenMPI 流の引数を受けない。使わない。
- 計算ノードからの `qsub` は、probe が `/bin/hostname` (binary) を script として渡した誤りで
  `UnicodeDecodeError` になり、可否は未確定。本裁定では使わない。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/multinode-summary.txt`。

## 生死確認 3 — CLI `-b` の優先 (job 982936.nqsv)

- script に `#PBS -b 1` を書いたまま `qsub -b 2` で投入 → `PBS_NODEFILE` は 2 行 (`bnode011`, `bnode015`)、
  Elapse 4 秒。CLI が directive に優先する。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/boverride-summary.txt`。

## 生死確認 4 — 1 ノード要求の `PBS_NODEFILE` (job 982979.nqsv)

- `-b 1` の要求でも `PBS_NODEFILE` (`/var/opt/nec/nqsv/jsv/jobfile/<job>/nodelist`) は実在し、自 host
  1 行だけ (`bnode016`)。nodes=1 の A-2 policy でも job body の nodefile 契約 (兄弟 0 台) が成立する。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/nodefile1-summary.txt`。

## 裁定 (段 4)

- **配る / 再現可能ビルド:** 配る。主 job が建てて durable cache に置いた trace-enabled binary を兄弟
  ノードが `/work` から読み、ノード内蔵 `/scr` へ同一 bytes で複製して実行する。建て直しは禁止。
- **輸送:** 単一 multi-node request。A-6 policy の `scheduler.nodes` を 1 → 5 にし、job body が
  `PBS_NODEFILE` から兄弟ノード (ちょうど 4 台) を取り `run-workload --verify-fanout-hosts` で渡す。
  head は rep 0 を既存経路で、兄弟 4 ノードで rep 1..4 を ssh 経由で並列に走らせる。legacy (1 回) と
  bench は head だけ。cell の順序 (stock → 採用版) は変えない。
- **束縛 (規律 2):** task.json (build_attempt_id、trace_bin_sha256、tag、rep、flags、clocks_per_us、
  numactl、genome、source / build admission receipt、期待 HEAD、task_sha256) と result.json の echo。
  worker は複製 binary の sha256 一致を要求し、ノード内蔵 lock と pgrep で単独性を確かめ、local と
  同じ repetition executor を走らせる。欠落・不一致・ssh 失敗は `verify-remote-unavailable`
  (indeterminate) であり pass にはならない。verifier の capability は発行 PID に束縛されるため、
  `commit_receipt` に狭い橋 (worker 側 serialize、head 側 admit → PID 束縛・単回使用の evidence) を足す。
- **変えないもの:** reps / records / threads / extime、`verify_done` payload の key、`_raw_cell_from_wal`
  以降の認証判定、A-2 policy (nodes=1 のまま)。`scheduler` は `_protocol_preimage` に入らないので
  `protocol_sha256` は不変、policy bytes の sha256 だけ変わる。変更後の fresh attempt だけが対象で、
  既存成果物は書き換えない。
- **見込み:** 検査の critical path が 10 回 × 約 425 秒から 2 cell × (legacy + 1 rep 分) へ縮み、
  73 分が 16〜18 分程度になる (段 3 レンズ B の見積、未実測)。

## 主張の上限

1. 生死確認 1 は A-6 の特定 attempt の 4 本、bnode031 → bnode012 の 1 回だけである。別 toolchain や
   A-2 (rr5 / rr50) の binary へ無検査で一般化しない。実装は attempt ごとに sha256 を照合する。
2. 生死確認 1 の実走は legacy 構成 (4 thread、200 tuple、1 秒) であり、48 thread・100 万 record の
   full-scale trace と verifier を別ノードで完走させた実測ではない。それは実装後の fresh attempt で得る。
3. 「1 ノード内では並べられない」は CPU (parse 16 worker + DSG の ProcessPool) を根拠にした判断で、
   memory 上の並列可否は未実測。本 wave は扱わない (裁定パッケージ候補)。
4. 計算ノードからの qsub 可否は未確定のまま (使わない)。

## 実装・検査 (段 5〜7 で追記)

(実装子の報告、変異 matrix、受入結果をここに追記する。)
