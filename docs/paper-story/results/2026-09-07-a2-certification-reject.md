# A-2 正式 certification の結果節 (改訂) — 測った条件は CCBench 内蔵 backoff の有効/無効であり、外側の protocol status は `reject` (2026-09-07)

**これは投稿本文ではない。** 論文の結果節・表・negative result へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の 2026-09-04 付の稿を改める。** 同系列は append-only なので旧稿は 1 byte も変えずに残る。
旧稿は attempt `t2022-20260828c` の `reject` を「**採用静的 backoff** (fixed 10 µs / fixed 5 µs) が
無 backoff 対照を下回った」と書いていた。**これは誤りである。** 当該 attempt は patch が当たっていない
stock の CCBench 木で走っており、静的量を渡す `BACKOFF_FIXED` は cmake の argv には載ったものの、
pin の CCBench に対応する option 定義が無いため build の条件にならなかった。実際に効いた条件差は
`BACK_OFF` の有効/無効だけである (ユーザー裁定 D1645、F707 の再発)。
本稿は一次資料 (権威 bytes・raw manifest・WAL・裁定・CCBench pin の現物) から作り直した改訂であり、
**旧稿の記述を数値・日付・status の出所にしていない。** 同じ一次事実から同じ短文が再導出されて
旧稿と字面が一致することはありうるが、それは旧稿を出所にしたことを意味しない。

---

## 0. 位置づけ — 何を書き、何を書かないか

- **書くもの:** attempt `t2022-20260828c` (2026-08-28) の 4 cell について、権威 bytes が持つ `cells[].performance.median_tps`・
  `effects`・`status`、**それらの cell で実際に効いていた条件**、status から言えることと言えないこと、表、限定の一覧。
- **書かないもの:** 採用静的 backoff についての判定 (本走行は測っていない)、
  旧系列との符号差の原因 (未同定)、旧系列の値を分母にした効果 (policy が禁じている)、
  研究として成功か失敗かの宣告 (D12)、read-heavy についての主張 (A-6 として未取得)、計算資源の余裕 (D1263 で取り下げ済み)。
- **`reject` は protocol の status であって、研究の失敗宣告ではない。** protocol は「adopted 側 cell の median throughput が
  同一 workload の stock 側 cell を上回るか」を 2 workload の論理積で問い、その答えが「上回らない」だった、という事実である。
- **当時の判定は不変である (絶対規律 7)。** 本稿が改めるのは「その `reject` がどの命題を支持するか」であって、
  当時測った値でも当時の protocol 出力でもない。当時その道具でその測定をし、その結果が出たという事実は後から変わらない。

---

## 1. 測定条件の実体 — 効いていたのは `BACK_OFF` だけである

この節が本稿と旧稿の違いの全部である。値と status は旧稿と同じで、支持する命題が違う。

### 1.1 木は stock だった

durable authority の WAL 2 本 (`jobs/<rr5|rr50>/campaigns/<campaign>/runs/` 配下) の `build_start` 4 record は、
4 件とも次を記録している。rr5 / rr50 の両方を本稿の作成時に読み直して確認した。

| 記録 field | 4 record すべての値 | 意味 |
|---|---|---|
| `payload.src_token`、`build_admission.source.src_token` | `stock` | その genome の digest が同 genome の baseline digest と一致 |
| `build_admission.source.tracked_clean` | `true` | 追跡 file に未 commit の変更なし |
| `build_admission.source.tracked_diff_sha256` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 空 bytes の SHA-256 = diff なし |
| `build_admission.source.tracked_paths` | `[]` | 変更 path ゼロ |
| `build_admission.source.ccbench_commit` | `511c953` | pin どおり |

**patch 不在はこの 4 つの連言から導いている。** `src_token = stock` は単独では「木が HEAD どおり」を意味しない。
`orchestrator/campaign/source_digest.py` の `resolve_evidence` が示すとおり、`src_token` が言うのは
「その genome で正規化した digest が、同じ genome の pin baseline digest と等しい」ことまでである。
追跡木が無変更であることは `tracked_clean`・`tracked_diff_sha256`・`tracked_paths` が別に担う。

当時の driver は patch harness を呼んでおらず、pipeline は patch を当てない契約だった (F707 の 2026-09-04 の再発記録)。

`build_admission.source.source_bytes_sha256` は cell 間で異なる (stock 側 `2d691b45…`、adopted 側 `6454d9f3…`) が、
**これは patch の証拠ではない。** 同じ `resolve_evidence` がこの値を genome 依存の前処理後 digest として計算するからである。

### 1.2 静的量は argv に載ったが、pin の CCBench がそれを消費しない

pin `511c9538` の CCBench には、`CCBENCH_BACKOFF_FIXED` と `CCBENCH_BACKOFF_NOINLINE` が**木全体のどこにも無い**
(`cmake/Options.cmake` だけでなく全 file を検索して 0 件)。両者は patch が供給する option である。

**したがって `-DCCBENCH_BACKOFF_FIXED=10` は cmake へ確かに渡っている。** 届かなかったのではなく、
受け取る側に対応する定義が無いため、使われない cache 変数として残るだけで compile definition にならない (F707)。

一方 `CCBENCH_BACK_OFF` は `cmake/Options.cmake` に実在し (既定 1)、`ccbench_universal_definitions` が
compile definition `BACK_OFF` として全 protocol target へ渡し、silo の `transaction.cc` の `#if BACK_OFF` が
abort 経路と leader 処理で消費する。

### 1.3 要求した条件と、効いた条件

genome の記録は資料ごとに載る範囲が違う。`BACKOFF_FIXED` と `BACK_OFF` は `certification.json` の
`cells[].genome` にある。`BACKOFF_NOINLINE` はそこには無く、WAL の genome 文字列 (`BACKOFF_NOINLINE=0`) と
policy の `controlled_define_base.CCBENCH_BACKOFF_NOINLINE` (値は文字列 `"0"`) にある。

| cell | role | 要求した条件 | 実 cmake 引数の backoff 部分 (`build_done.payload.perf_configure_cmd`) | 実際に効いた差 |
|---|---|---|---|---|
| `rr5-stock` / `rr50-stock` | stock | `BACKOFF_FIXED=-1`, `BACK_OFF=0` (+ 共通 `BACKOFF_NOINLINE=0`) | `-DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_BACK_OFF=0` | `BACK_OFF=0` (内蔵 backoff **無効**) |
| `rr5-fixed10` | adopted | `BACKOFF_FIXED=10`, `BACK_OFF=1` (+ 共通 `BACKOFF_NOINLINE=0`) | `-DCCBENCH_BACKOFF_FIXED=10 -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_BACK_OFF=1` | `BACK_OFF=1` (内蔵 backoff **有効**) |
| `rr50-fixed5` | adopted | `BACKOFF_FIXED=5`, `BACK_OFF=1` (+ 共通 `BACKOFF_NOINLINE=0`) | `-DCCBENCH_BACKOFF_FIXED=5 -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_BACK_OFF=1` | `BACK_OFF=1` (同上) |

**genome の差は `BACKOFF_FIXED` と `BACK_OFF` の 2 つだけであり、前者は build に効いていない。したがって
4 cell の間で実際に効いた条件差は `BACK_OFF` の `0` と `1` だけである。**

**binary hash の差はこの結論の根拠にならない。** 同一の記録 genome を持つ `rr5-stock` と `rr50-stock` でも
`performance.perf_bin_sha256` は異なる (`9d3dba7c…` と `f84d0c7b…`)。一次資料はこの差の原因を記録していない。
hash 単独を compile-out の証拠にしない。本節の結論が依るのは §1.1〜§1.3 の記録だけである。

### 1.4 `BACK_OFF=1` が有効にする機構は適応制御であって、指数 backoff ではない

CCBench の `include/backoff.hh` にある `Backoff` クラスである。直近区間のスループット変化を待機量の変化で
割った勾配を見て、共有待機量を固定幅 `kIncrBackoff = 100` だけ増減し、`kMinBackoff = 0` から
`kMaxBackoff = 1000` の範囲に収める (勾配 0 のときは commit 数の最下位ビットで増減を選ぶ)。
**指数的に増える機構ではない。**

`cmake/Options.cmake` の option 説明文だけが `exponential backoff on abort` と呼んでいる。
**裁定 D1645 の文言「内蔵指数 backoff」はこの説明文に由来すると見られる。** 本稿は D1645 が定めた訂正
(支持する命題を `BACK_OFF` の有効/無効へ書き換えること) をそのまま実行しつつ、機構名は実装に合わせて
「CCBench 内蔵の適応 backoff」と書く。この呼び方は本プロジェクトの既存の論文素材とも一致する。

### 1.5 `certification.json` の `genome` 欄と cell 名の読み方

`certification.json` の各 cell の `genome` は `{"BACKOFF_FIXED": 10, "BACK_OFF": 1}` の 2 field である。
これは**要求された genome の記録**であって、build に効いた条件の記録ではない。**この欄を「静的 backoff を測った」の
根拠に読んではならない。** 本走行の時点では、要求した条件が実際に効いたことを確かめる層がどこにも無かった (F707)。
同じ理由で、`rr5-fixed10` / `rr50-fixed5` という cell 名も要求された genome に由来する名前であり、効いた条件ではない。

---

## 2. 結果節の統制稿

性能、別走行の correctness、旧系列との関係を 3 段に分けて書く。1 段に畳むと、同じ run で正しさと性能の
両方を確かめたように読まれるからである。旧系列の値は本稿の結果より前に置かない (前後比較に読まれる)。

### 2.1 性能 — 2 つの独立 campaign で、内蔵 backoff 有効は無効を下回った

attempt `t2022-20260828c` は、write-heavy (rratio=5) と balanced (rratio=50) の 2 workload × 2 cell = exact 4 cell を、
Pegasus・CCBench pin `511c953`・Izanagi source commit `639c1dbad4b00d8c51993a653cfc1ebfd22cf300` の正式 protocol で測った。
権威 bytes の `schema_version` は `paper-story-a2-certification-result/v3`、その `protocol_schema` は
`paper-story-a2-certification-policy/v2` であり、`protocol_sha256` は `136b823e…d9f4`、`policy_sha256` は `42bfee48…c897e` である。

write-heavy は job `0:954194.nqsv` を host `bnode141` で、balanced は job `0:954195.nqsv` を host `bnode064` で、
それぞれ別時刻に実行した。**2 つは独立に環境契約された別々の campaign であり、外側の status はその論理積である** (D1169)。
「4-cell run」という短縮はこの構成を隠すので使わない。性能は trace-disabled build の別 run で 5 標本を取った (絶対規律 1 の分離)。

**結果: これら 2 つの campaign では、内蔵 backoff を有効にした cell が、無効にした対照を 2 workload とも下回った。**
median throughput の比は write-heavy で **−46.3902%**、balanced で **−65.9080%**、外側の certification status は **`reject`** である (表 1)。

**この効果に付く限定 (効果の直後に置く)。** 権威 bytes (`certification.json`) の `a4_noise_floor_status` は `open`、
`global_minimality_established` は `false`、`smallest_observed_sufficient_in_this_two_point_protocol` は `null` であり、
**`certification.json` 自身は信頼区間も有意差判定も持たない。** status は事前定義された median 比の符号だけで決まっている。
本稿の表が付ける 95% 信頼区間は執筆者が同じ 5 標本から再計算した記述であり、効果や status の判定材料ではない
(図 5 の provenance JSON も同じ性格の記述値を持つ)。

**測定条件の関門について。** 条件の「供給」と「実行側の意味」を独立に見る関門族 (D1198) が driver 全体へ義務化されたのは
2026-09-01 であり、本走行 (2026-08-28) はその前にある。**本走行にはこの関門族が適用されていない。**
§1 が示した「静的量が build に効いていない」は、まさにこの関門が無かったために起きた。
**`reject` は当時の protocol 出力として不変であり (絶対規律 7)、本稿は当時の判定を作り直していない。
改めたのはその判定がどの条件対を指すかの記述である。**

### 2.2 別走行の correctness — certified なのは patch 無しで実際に build された 4 cell の bytes であって、採用静的 backoff ではない

correctness は性能とは別の run で、trace-enabled build を使い、性能を測った workload そのもので直列化可能性を検査した。
`cells[].correctness.status` は 4 cell とも `certified` (anomaly 0)、`legacy_repetitions_observed` は各 1、
`performance_repetitions_observed` は各 5 で、すべて pass である。
`certified` が言うのは、その cell で観測した point-key trace が verifier の射程で直列化可能だったことまでである (限定レジストリ `L01`)。
`independent_observation_limits.correctness_run_argv` は `not-recorded-by-existing-pipeline` であり、
**correctness 実行の argv と executable hash は独立記録されておらず、後付けも再走もしない** (D1257)。
**この段の緑は §2.1 の性能 status を 1 bit も変えない。**

### 2.3 旧系列との関係 — 本稿の結果は旧系列の反証でも再現失敗でもない

旧 `linux-baremetal`・CCBench `6656e93` の記述的 sweep が持つ値は、本稿の comparator ではない。本稿はその値を再掲せず、
旧値を分母にした効果も計算しない。policy 自身が旧 commit の役割を
`"originating historical campaign only; never a current comparison value"` と限定しているからである。
条件差は CCBench commit、環境、toolchain (旧は gcc/g++-13、本走行は GCC 11.4.0 / CMake 3.22.1)、
`clocks_per_us`、numactl、計装 (旧 sweep は `perf stat` 下、本走行は perf 無し)、workload 被覆にわたる。
**加えて本走行は静的 backoff を測っていない** (§1)。**旧 sweep の静的 backoff 系列と本走行は同じ量を測っていないので、
「同じ設定の別環境での再測定」として並べてはならない。** 符号差の原因は同定されていない。

---

## 3. 表 1 — exact 4 cell の値 (attempt `t2022-20260828c`)

| workload | cell | role | 効いた条件 | throughput 5 標本 (tps、記録順) | median (tps) | mean ± 95% CI (tps) | cv | abort 率 (集約 1 点) | correctness (別の trace-enabled run) | 効果 (median 比) |
|---|---|---|---|---|---:|---:|---:|---:|---|---:|
| write-heavy (rratio=5) | `rr5-stock` | stock | `BACK_OFF=0` | 2715421, 2565367, 2496060, 2470354, 2527542 | 2,527,542 | 2,554,949 ± 119,798 | 0.0378 | 0.7767 | certified (legacy 1 + full-scale 5) | 分母 |
| write-heavy (rratio=5) | `rr5-fixed10` | adopted | `BACK_OFF=1` | 1348263, 1355011, 1345709, 1387690, 1362175 | 1,355,011 | 1,359,770 ± 20,944 | 0.0124 | 0.1189 | certified (legacy 1 + full-scale 5) | **−46.3902%** |
| balanced (rratio=50) | `rr50-stock` | stock | `BACK_OFF=0` | 3894140, 3683727, 3636364, 3627357, 3662448 | 3,662,448 | 3,700,807 ± 136,990 | 0.0298 | 0.6903 | certified (legacy 1 + full-scale 5) | 分母 |
| balanced (rratio=50) | `rr50-fixed5` | adopted | `BACK_OFF=1` | 1245023, 1196920, 1248603, 1261810, 1260445 | 1,248,603 | 1,242,560 ± 32,945 | 0.0214 | 0.2048 | certified (legacy 1 + full-scale 5) | **−65.9080%** |

外側の certification status は **`reject`** である (2 workload の論理積、D1169)。

**表の脚注。**

- **`fixed10` / `fixed5` という cell 名は要求された genome に由来する名前であって、効いた条件ではない** (§1.5)。
  cell 名を静的量の記述として読んではならない。
- **表の数値の転記元は図 5 の provenance JSON の `cells` である** (D1631 が図を伴う稿へ課す規則)。
  同 `cells` は `samples_tps`・`median_tps`・`mean_tps`・`ci95_half_tps`・`cv`・`abort_rate` を持ち、
  各 cell に `raw_crosscheck` と `certification_crosscheck` を `true` として記録している。
  検算先として、durable authority の raw cell JSON の `performance.samples_tps` と
  `certification.json` の `cells[].performance.median_tps`・`effects` を本稿の作成時に読み直し、
  三者が一致することを確認した (5 標本から再計算した効果は `effects.rr5 = -0.4639016878849095`、
  `effects.rr50 = -0.6590796647488237` で権威 bytes と一致)。図と表は同じ凍結 provenance に束縛されている。
- 効果 = `adopted median / stock median − 1`。protocol が判定に使う量であり、論文本文もこの量だけを使う。
  mean ± CI は不確かさを見せる付記であり、**効果を平均比で計算し直さない。** 本稿は平均比の値を書かない。
- 95% CI は 5 標本の t 分布 (`t_{0.975,4} = 2.7764451`、半幅 = `t · s / √5`) で再計算した。
  **`certification.json` 自身は信頼区間も有意差判定も持たない** (§2.1)。
- abort 率は WAL の `bench_done.payload.leading_indicators.abort_rate` の集約 1 点で、反復値が無い。
  descriptive な指標であり、CI は付けられず、機序の同定にも使わない。
  **backoff 有効側で abort 率が大きく下がりながら throughput も下がっている、という並びを機序の説明として書かない。**
- correctness の欄の出所は `cells[].correctness` であり、性能とは別の trace-enabled run の判定である。
  射程は `L01` (point-key trace まで)、`legacy_repetitions_observed` は各 1、argv の独立記録は無い (D1257)。**性能の判定ではない。**
- 共通条件 (raw cell JSON の `performance.workload`): threads 48、records 1,000,000、`ycsb_zipf_skew` 0.9、`ycsb_rmw` 0、
  `ycsb_max_ope` 10、extime 3 s、reps 5、trace-disabled 性能 build、perf 無し、
  toolchain は gcc/g++ 11.4.0 (`x86_64-linux-gnu-g++-11`)、cmake 3.22.1。
- 絶対スループットは論文の headline 値の出所にしない。本稿の主張は同一 workload 内の比だけである。

---

## 4. 限定

| # | 限定 | 出所 |
|---|---|---|
| L-A2R-1 | **本走行は採用静的 backoff を測っていない。** 要求した `BACKOFF_FIXED` は cmake argv に載ったが、pin の CCBench に対応する option 定義が無く build に効かなかった。効いた差は `BACK_OFF` の 0/1 だけ | WAL `build_start` の `src_token` と tracked fields、`build_done` の argv、pin の CCBench 全木検索、F707、D1645 |
| L-A2R-2 | `certification.json` の `cells[].genome` と cell 名は要求された genome の記録であり、効いた条件の記録ではない | `certification.json` の `cells[].genome`、F707 |
| L-A2R-3 | `BACK_OFF=1` の機構は適応制御であり指数 backoff ではない。CMake の option 説明文だけが exponential と呼ぶ | CCBench の `include/backoff.hh`、`cmake/Options.cmake` |
| L-A2R-4 | correctness 実行の argv と executable hash は独立記録されておらず、後付けも再走もしない。correctness run も patch 無しの木である | `independent_observation_limits`、D1257 |
| L-A2R-5 | legacy correctness の観測反復は各 cell 1 回 | `cells[].correctness.legacy_repetitions_observed` |
| L-A2R-6 | read-heavy は protocol の対象外 (A-6 として未取得) | policy の 2 workload 定義 |
| L-A2R-7 | `a4_noise_floor_status = open`、`global_minimality_established = false`、`smallest_observed_sufficient… = null`。`certification.json` に CI も有意差判定も無い | `certification.json` |
| L-A2R-8 | 32 GB のメモリ余裕の主張は取り下げ済み。本稿は資源余裕を主張しない | D1263 |
| L-A2R-9 | D1198 の関門族は本走行の後に義務化され、本走行には適用されていない。当時の status は不変 | D1198、D1611 |
| L-A2R-10 | 2 workload は別 job・別 host・別時刻の独立 campaign であり、外側の status はその論理積 | D1169、`raw-manifest.json` の `campaign_claims` |
| L-A2R-11 | 旧 sweep とは測っている量が違う (静的 backoff 対 内蔵 backoff の on/off)。旧値を comparator にしない | §2.3、policy の `historical_context` |
| L-A2R-12 | 性能値は trace-disabled build、perf 無し。絶対値は headline の出所にしない | raw cell JSON の `build_evidence.performance_trace_disabled_build`、D20 |
| L-A2R-13 | verifier の保証範囲は本走行で広がらない。判定は point-key の Read/Write 事象で構成した依存から導く射程に留まる | `orchestrator/verifier/parse.py` の key 単位事象、`docs/isolation-phenomena.md` の被覆範囲 |
| L-A2R-14 | 表の平均 ± CI は効果・status・median の信頼区間ではない。abort 率は descriptive な集約 1 点で機序を同定しない | 表 1 脚注 |
| L-A2R-15 | 図 5 は凍結物であり、その cell label とキャプションは要求された genome に基づく。**取り直しまで論文の A-2 の結論にも図にも使わない** | `docs/paper-story/figures/README.md` の fig5 節、D1645 |

---

## 5. 図 5 の扱い — 取り直しまで論文には使わない

図の現物 `docs/paper-story/figures/fig5_a2_certification_reject.{png,pdf}` と同名の provenance JSON は
**凍結物であり、本稿は変更しない。** 図が描く 5 標本・median・平均と CI・abort 率は本稿の表 1 と同じ生値から出ており、
**値としては正しい。** しかし図と provenance の caption は cell を「採用静的 backoff」と記述しており、
**効いた条件の記述としては誤りである** (§1)。

**D1645 に従い、正しい identity で取り直した attempt が出るまで、図 5 を論文の A-2 の結論にも図にも使わない。**
条件名を補って使うこともしない。当時の値と `reject` は履歴資料として参照できる、というところまでである。
恒久の erratum は腐らない入口である `docs/paper-story/figures/README.md` の fig5 節が持つ。

取り直した attempt が出たら、その結果は新しい図と新しい日付の results file で扱う。

---

## 6. 一次資料と束縛

- 権威 bytes: `output/insights/2026-08-24_paper-story-a2-certification/certification.json`
  (SHA-256 `f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40`、
  `schema_version` は `paper-story-a2-certification-result/v3`、その `protocol_schema` は `paper-story-a2-certification-policy/v2`)
- 入力 hash 束縛: 同 dir の `raw-manifest.json`
  (SHA-256 `12d8be7a9cabd404ab3147301c2df7998a731b310ec51a93f9a99b37705a7c35`、schema `paper-story-a2-raw-manifest/v3`)。
  同 file の `files` map が外部入力 10 件 (WAL 2 本、raw cell 4 本、campaign.lock 2 本、claim 2 本) の SHA-256 を束縛する。
- 測定条件と生反復値 (repo 外の durable authority):
  `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c/`
  - write-heavy の WAL: `jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-b571889a/runs/` 配下
    (`31c0d97fad66513a2d5f643ebfdd35187b76996234c2c4b7e0e54c5106726cd7`)
  - balanced の WAL: `jobs/rr50/campaigns/paper-story-a2-rr50-paper-story-a2-certification-rr50-57427bf5/runs/` 配下
    (`c93ece700f81e16a939d39699b9c4c1ed2e032736f475d3e7bb6c82ec0fed4d9`)
  - raw cell 4 本: `jobs/rr5/raw/rr5-stock.json` (`884632f9d344aea31991af514fed0b932a162963c7610864f5cee7fccd449bd7`)、
    `jobs/rr5/raw/rr5-fixed10.json` (`81a61ad6776e4e076de47fa82201d2e80e76e71271c568323c4635fafab3f630`)、
    `jobs/rr50/raw/rr50-stock.json` (`d4786f8318a0fbf27f938b79ba0f2a656016646fe76f046e8febf8751865304e`)、
    `jobs/rr50/raw/rr50-fixed5.json` (`18b9ec76496ebcc8e2922eddcccac485b636142f61285c5f3166082169046b48`)
  - 上記 6 件の SHA-256 は本稿の作成時にすべて再計算し、`raw-manifest.json` の `files` map と一致することを確認した。
- CCBench pin `511c9538` の現物: `cmake/Options.cmake` (option の実在と不在)、`include/backoff.hh` (機構の実装)、
  silo の `transaction.cc` (`#if BACK_OFF` の消費点)
- 図 5 の provenance JSON: `docs/paper-story/figures/fig5_a2_certification_reject.provenance.json` —
  本稿の作成時に現物 bytes から再計算した SHA-256 は
  `30113d5000f66a15dce5a50ccaa70cd70f79e7b8912e6617451379a1cdae3fef`
- 実走の索引: `output/insights/2026-08-28_t2022-a2-certification-run/README.md`
  (同 file の「測定条件の実体」節が本稿と同じ訂正を持つ)。materialization 側は
  `output/insights/2026-08-24_paper-story-a2-certification/README.md`
- 裁定: D1645 (本稿を書くこと自体の裁定)、D1631 (results 系列の規則)、D1169 (outer は論理積)、
  D1257 (argv の独立記録は後付けしない)、D1263 (32 GB 余裕の取り下げ)、D1198 (測定条件の 2 関門族)、D1611 (inert 比較の差分分類)
- 欠陥の記録: F707 (要求した build 条件が黙って効かず、別条件の測定として記録される) とその 2026-09-04 の再発記録

---

## 7. この文書が確かめていないこと

- **採用静的 backoff (fixed 10 µs / fixed 5 µs) の現行環境での判定。** 本走行は測っていない。
  取り直しは、adopted cell の canonical identity を pin と patch に束縛した `src_token` で計算する実装 (D1644 / T-2337) の後に行う。
- 内蔵 backoff の有効/無効の差が**なぜ**この向きと大きさになるかの機序。abort 率の並びは機序の同定に使わない。
- 同一の記録 genome を持つ cell 間で binary hash が異なる理由。一次資料はこの差の原因を記録していない。
- 旧系列との符号差の原因。旧環境の再測定も、現行環境での旧 commit の測定も行っていない。
- read-heavy の同一 workload certification (A-6)。
