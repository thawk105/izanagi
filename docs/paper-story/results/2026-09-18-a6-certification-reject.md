# A-6 read-heavy 正式 certification の結果節 — attempt `a6-20260908b` の outer status は `reject` (2026-09-18)

**これは投稿本文ではない。** 論文の結果節・表・限定へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** A-6 の rr95 の値は、横断稿
`results/2026-09-14-b7-all-workload-regression.md` と `results/2026-09-16-b7-three-run-materials.md` にも
併記されているが、それらは 2 つまたは 3 つの走行を 1 枚の表に並べる横断の材料であって、A-6 という 1 attempt の
一次資料全体から作った結果節ではない (worklog entry 1488 が「A-6 の単独 results 稿は存在しない」と記録し、
[T-2611] として起票した)。**本稿は横断稿を数値・判定の出所にしていない。** 出所は §5 に挙げる一次資料だけである。
横断稿は凍結物として 1 byte も変えずに残る。

---

## 0. 位置づけ — 何を書き、何を書かないか

- **書くもの:** attempt `a6-20260908b` (2026-09-08、request `982234.nqsv`) の 2 cell について、権威 bytes が持つ
  `cells[].performance.median_tps`・`effects`・`status`・`correctness`・`source_binding_status`、それらの cell で
  実際に効いていた条件、status から言えることと言えないこと、表、限定の一覧。
- **書かないもの:** 研究として成功か失敗かの宣告 (D12)、read-heavy で stock が最良であることの証明、退行の機序の
  同定、他の read 比率・他の機体・他の CCBench pin への転移、A-2 (write-heavy / balanced) との集計、旧環境の
  read-heavy の値の再解釈。
- **`reject` は protocol の status であって、研究の失敗宣告ではない。** protocol は「adopted 側 cell の median
  throughput が同一 workload の stock 側 cell を上回るか」を問い、A-6 では workload が rr95 の 1 つなので
  outer status はその 1 問の答えそのものである。答えは「上回らなかった」だった、という事実である。
- **性能の判定と正しさの証拠は別の段である。** 性能の `reject` は §2.1、別走行の正しさの `certified` は §2.2、
  他の記録との関係は §3 に分けて書く。3 つを 1 文へ畳まない (D1993 項 2 —
  「性能の判定が `reject` であることは、正しさ証拠の欠落ではない」)。
- **主判定文 (結果節へ落とすときの形。文を分けたまま使う):** attempt `a6-20260908b` の trace-disabled 性能測定では、
  採用静的 backoff 2 µs の median throughput は stock を 5.7841% 下回り、当時の protocol の outer status は `reject`
  だった。これは 1 attempt・各 5 標本の中央値比較の結果であり、有意差・between-run floor 超の退行・研究の失敗を
  判定するものではない。別の trace-enabled 走行では、2 cell とも `correctness.status = certified` と記録されており、
  その証拠には §4 の限定 (i)〜(v) が付く。

---

## 1. 何を測ったか

### 1.1 protocol と 2 つの cell

policy `paper-story-a2-certification-policy/v2`、study `paper-story-a6-certification`、protocol SHA-256
`21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`。workload は rr95 (label `read-heavy`、
`rratio` 95、`adopted_backoff_us` 2) の 1 つで、cell は 2 つである。

| cell | role | 要求 genome | 意味 |
|---|---|---|---|
| `rr95-stock` | stock | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 内蔵 backoff 無効・静的 backoff 無し |
| `rr95-fixed2` | adopted | `BACK_OFF=1`, `BACKOFF_FIXED=2` | 採用静的 backoff 2 µs (patch の静的枝) |

効果の定義は `adopted_median / stock_median - 1`、集約は median、性能の反復は 5、正しさは `legacy+performance`
(campaign preimage の `effect` / `aggregate` / `reps` / `verify`)。outer certification は
「policy の workload 順の論理積」と定義されているが、workload が 1 つなので rr95 の判定と一致する。

policy が固定する共通条件は、性能側が records 1,000,000・threads 48・skew 0.9・rmw 0・max_ope 10・extime 3・
reps 5・base `L-W0`・wal 0・protocol silo、legacy 正しさ側が tuple 200・thread 4・skew 0.9・rratio 50・rmw true・
max_ope 5・extime 1 である。controlled define の基底は `NO_WAIT_LOCKING_IN_VALIDATION=1`、
`NO_WAIT_OF_TICTOC=0`、`WAL=0`、`BACKOFF_NOINLINE=0`、`TRACE=0`。policy の `historical_reference`
(CCBench `6656e93`) は「起源となった歴史的 campaign の参照であって現在の比較値ではない」と自ら宣言しており、
権威 bytes も `historical_context.comparison_input = false` と記録する。

### 1.2 identity の束縛 — adopted cell が patch の当たった木で build されたことの記録

driver は D1644 が定めた **pin + patch に束縛した `src_token`** で cell の identity を計算する。権威 bytes は
2 cell について次を記録している。

| cell | role | `src_token` | `source_binding_status` |
|---|---|---|---|
| `rr95-stock` | stock | `stock` | `bound` |
| `rr95-fixed2` | adopted | `0b3abbe62a6069ff29f8319740444b5196ab714f82e713782fb70bf588fc10a0` (非 `stock`) | `bound` |

条件関門の受理証跡 (`condition-gate-rr95.admissions.jsonl`) は、両 cell の source-evidence record が
CCBench commit `511c953`、tracked 変更 path `cmake/Options.cmake` と `include/backoff.hh`、`tracked_clean = false`、
同一の `tracked_diff_sha256` (`b7b4c79aa2ebd0f7c09761099f716f18f7c8e8b031f61be8ef48a93d4958e4ba`) を持つと
記録する。adopted cell の `source_bytes_sha256` は上の `src_token` と一致する。**したがって A-6 では、
adopted cell が patch の当たった木で build されたことが記録から言える** (D1993 項 2 が A-2 と同じ基準で
A-6 の 2 cell を `bound` と扱うと裁定した)。この記録が何を証明し何を証明しないかは §4 の限定 (v) に書く。

### 1.3 実行 identity

| 項目 | 値 | 出所 |
|---|---|---|
| attempt / study | `a6-20260908b` / `paper-story-a6-certification` | `certification.json` |
| scheduler request | `982234.nqsv` (queue `gen_S`、1 node、CPU 48、walltime 12:00:00) | `submission-receipt.json`、`reservation.json` |
| 実行ホスト | `bnode031` | `raw-manifest.json` の campaign claim、`reservation.json` |
| request の時刻 (JST、2026-09-08) | Created 01:28:55 / Started 01:29:06 / Ended 02:42:03、Elapse 4382 秒 | scheduler の `job.stderr` (会計出力)、`submission-receipt.json` の qstat |
| campaign WAL の時刻 (JST) | stock: build 01:29:45〜、commit 02:05:55。adopted: build 02:05:57〜、commit 02:42:02 | campaign WAL |
| izanagi source commit | `ae8a767eb60118c3f9791141603fa01ad4f28406` | `certification.json`、受領証 3 件 |
| CCBench pin | `511c953` (+ patch、§1.2) | 同上 |
| 投入 | `pegasus02` から `direct-qsub`、cwd は投入用 checkout `submit-tree` | `submission-receipt.json` |
| toolchain | `x86_64-linux-gnu-gcc-11` / `g++-11` 11.4.0、cmake 3.22.1 | raw JSON の `build_evidence.toolchain` |
| 性能 build | `-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF`、`-DCCBENCH_TRACE=0`、依存は staged 供給 (`-DCMAKE_PREFIX_PATH` と FetchContent の 4 path、D1693 の文法) | campaign WAL の `build_done.perf_configure_cmd` |
| 性能 run の argv | `ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio=95 -ycsb_rmw=0 -ycsb_max_ope=10` | campaign WAL の `bench_done.run_cmd` |
| perf | 不使用 (`use_perf = false`、preflight `unavailable`、`counter_status = not_required`、`claim_scope.throughput = eligible`) | campaign WAL の `bench_done.perf_observation` |
| 性能 binary (SHA-256) | stock `d3f945267c953fe5de1f7cea61c081e8b97a1af2d990c99aea90f82bd08e9e2c`、adopted `98f65c2df8aaff8d0b7fdae6d07bd27a85e43701753d1d147dedfcc680229c64` | `certification.json` の `perf_bin_sha256` |
| build attempt | stock `62e3270b73d36c33b19061cb64bab9f0`、adopted `5927ea43e4b2c1015479a9c02f942026` (両 build とも cache 不使用) | `certification.json`、WAL `build_done` の `trace_cached` / `perf_cached` |

**policy bytes は測定後に 1 key だけ変わっている。** 走行時に読まれた policy file の SHA-256 は
`8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8` (`preregistration.json` の `policy_sha256`)、
公開された `certification.json` の `policy_bytes_base64` を復号した policy file bytes の SHA-256 は
`96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a` である (権威 bytes の `policy_sha256`。
producer の canonical JSON 直列化の hash ではなく file bytes の hash)。両者を JSON として比較すると
差は `tracked_destination` の 1 key だけ (`output/insights/2026-09-02_paper-story-a6-certification` →
`output/insights/2026-09-08_t2411-paper-story-a6-certification`) で、この key は protocol の preimage に
含まれないため **`protocol_sha256` は前後で同一**である (本稿の執筆時に producer の実関数で再計算した)。
何を測ったかは変わっていない。変えた理由は attempt の記録 (§5.3) が書いている。

**現行 policy との適合。** 本稿を書いた時点の local main (`302b94796`) の
`orchestrator/campaign/paper_story_a6_certification.v2.json` から同じ関数で計算した `protocol_sha256` も
`21427e71…` で一致する。公開 policy との差は `scheduler.nodes` (1 → 5) だけで、これも preimage の外である。
D1693 が「過去の結果と現行 policy の `protocol_sha256` が一致しなくなる旨を明記する」と定めたのは trace0 の
configure 文法へ FetchContent の枠を足す改訂についてであり、A-6 の policy はその枠を含んだ文法で走っている
(上の表の性能 build 行)。将来 preimage に含まれる key が変われば、本 attempt は旧 hash に束縛されたまま残り、
現行コードとの差だけを理由に無効にはならない (絶対規律 7)。

### 1.4 条件関門の記録

`condition-gate-rr95.admissions.jsonl` は 2 cell 分の admission record を持ち、いずれも `admitted = true`、
`use_class = "paper"`、`unestablished_meaning_macros = []` で、`record_ids` として supply-effectuation 2 件と
runtime-meaning 2 件 (cell あたり計 4 件、合計 8 件) の digest を列挙する。**tracked 成果物に保存されているのは
この admission record と `record_ids` までで、supply / meaning record の本体は成果物に含まれない** (D1993 項 3 (iv))。

補足として、durable authority の scheduler stdout (`jobs/rr95/scheduler/job.stdout`、589,570 bytes、SHA-256 は
`completion-receipt.json` が束縛) には、8 件の `record_id` に一致する record 本文が出力されていることを本稿の
執筆時に数えた (各 ID が 1 回ずつ現れる)。これは実行 log への出力であって schema 化された保存ではなく、
本稿は限定 (iv) を外す根拠にしない。

---

## 2. 結果

### 2.1 性能 — adopted (静的 2 µs) は stock を下回り、outer status は `reject`

| cell | role | 要求 genome | median (tps) | mean (tps) | 標本 sd (tps) | cv | 95% CI 半幅 (tps) | min – max (tps) | abort 率 |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `rr95-stock` | stock | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 10,088,796 | 10,132,250.6 | 133,406.6 | 0.0132 | 165,646.2 | 10,029,940 – 10,365,808 | 0.1547 |
| `rr95-fixed2` | adopted | `BACK_OFF=1`, `BACKOFF_FIXED=2` | 9,505,248 | 9,565,649.4 | 112,221.9 | 0.0117 | 139,341.9 | 9,488,225 – 9,753,031 | 0.145 |

median 比の効果は **rr95 が −5.7841%** (`effects.rr95 = -0.057841193339621455`) である。表の median を入力した比の
再計算は権威値と一致する。outer status は **`reject`** である。

生の 5 標本 (記録順、tps) は stock `10365808, 10103030, 10029940, 10088796, 10073679`、adopted
`9753031, 9587735, 9488225, 9494008, 9505248` である (durable authority の raw JSON の
`performance.samples_tps`。campaign WAL の `bench_done.tps` と同じ並び)。両 cell とも raw JSON の `performance` は
`unstable = false`、`rep_notes = []`、campaign WAL の `bench_done` は `high_variance = false`、`rounds = 1` である。

**mean・標本 sd・cv・95% CI 半幅は本稿の執筆者が生の 5 標本から計算した派生値であり、権威 bytes には無い**
(A-6 には図の provenance JSON が無いため、A-2 の稿のように図生成器の値を転記することができない)。
式は mean = 算術平均、標本 sd = 不偏標準偏差 (n − 1)、cv = 標本 sd / mean、95% CI 半幅 = t(0.975, 4) ×
標本 sd / √5 (t = 2.776445)。cv は campaign WAL の `bench_done.cv` (stock 0.013166532966358306、adopted
0.01173175682351728) と 4 桁で一致する。A-6 attempt の記録が載せている 1.18% / 1.06% は別の統計量
(母標準偏差 / median) であり、上の cv 列とは同じ量ではない。

**平均の信頼区間は標本を記述するものであって、効果・判定・median の信頼区間ではない。** 本成果物は有意性の
判定を行わない。権威 bytes は `a4_noise_floor_status = "open"`、`global_minimality_established = false`、
`smallest_observed_sufficient_in_this_two_point_protocol = null` を記録する。

### 2.2 正しさ — 別走行で 2 cell とも certified

正しさは trace-enabled build の別走行から来る (stock の trace binary は
`098cdd82953c7a603fce58243a760ecb2823327bfa50313e9cfefea5da25bcbf`、adopted は
`f9eeb78e03c55bca5acf1c756eeac1684ce477a317c25f1ed0bb79ee675a23b9`、いずれも性能 binary とは別の bytes)。
2 cell とも `correctness.status = certified`、`disposition = pass`、legacy 1 回・performance 条件 5 回の
検査がすべて `pass` である。campaign WAL の `verify_done` 12 件はすべて `verdict = serializable`、
`certified = true`、`anomalies = 0`、`proof_surfaces` は `{protocol: silo, X: evidence-present,
P: evidence-present, I: evidence-absent}` と記録する。

| cell | 検査 | 回数 | commits (記録順) | aborts (記録順) |
|---|---|---:|---|---|
| `rr95-stock` | legacy | 1 | 637,777 | 249,953 |
| `rr95-stock` | performance 条件 | 5 | 16,549,865 / 16,447,449 / 16,525,479 / 16,441,072 / 16,504,533 | 2,954,714 / 2,947,410 / 2,932,849 / 2,915,825 / 2,923,634 |
| `rr95-fixed2` | legacy | 1 | 615,507 | 221,747 |
| `rr95-fixed2` | performance 条件 | 5 | 16,636,998 / 16,742,621 / 16,496,139 / 16,531,524 / 16,598,730 | 2,757,203 / 2,747,515 / 2,711,660 / 2,717,244 / 2,750,899 |

**これは性能の認証ではない。** `correctness.performance` という field 名は「performance 条件で行った正しさ検査」の
意味であって性能の判定ではない。性能値は trace-disabled build (`performance_trace_disabled_build = true`) の
走行から来ており、正しさ検査の走行とは build も run も別である (絶対規律 1)。adopted cell の `correctness.status` は、
別の trace-enabled 走行の検査結果として `certified` と記録されている。その射程は §4 の限定 (i)〜(v) に従う。
性能の観測値と `reject` 判定は §2.1 に示した。正しさ検査の合格は性能の優越を保証せず、性能の `reject` は取得済みの
正しさ証拠を取り消さない。

検査の射程は限定 (i)〜(v) (§4) のとおりである。正しさ側の run argv は既存 pipeline では独立に記録されておらず
(権威 bytes の `independent_observation_limits.correctness_run_argv = not-recorded-by-existing-pipeline`、
`cells[].correctness.workload_argv_observation = not-independently-recorded-by-existing-pipeline`)、workload の
束縛は campaign lock と pipeline constructor による (D1257)。

### 2.3 abort 率 — 記述的な先行指標

表の abort 率は campaign WAL の `bench_done.leading_indicators.abort_rate` で、CCBench が出力する
`abort_rate` (定義 `aborts / (commits + aborts)`) を、**5 rep のうち throughput が中央値に最も近い rep から 1 点**
採った値である (走行時 source `ae8a767eb` の `orchestrator/calibrator/runner.py` の代表 rep 規則。5 標本なので
median の rep そのもの)。標本ごとの率でも、信頼区間を持つ量でもない。

adopted 側で abort 率が 0.1547 から 0.145 へ下がりながら throughput も下がっている、という並びを機序の説明として
書かない (`results/2026-09-07-a2-certification-reject.md` §3 の脚注が定めた禁止を本稿も維持する)。機序に
ついて本稿が引けるのは §3.1 の事後整合性検査の記録までで、それも機序の同定ではない。

なお §2.2 のうち、performance 条件の trace-enabled 走行各 5 回における aborts / commits は、stock 0.1771〜0.1792、
adopted 0.1641〜0.1657 である。これは §2.1 の abort 率とは分母が異なり、別 build の値なので性能走行の代表 rep の
独立反復ではない。legacy 各 1 回は §1.1 に示した別 workload (rratio 50・4 thread・200 tuple・rmw true) の検査であり、
この範囲に含めない。

---

## 3. この結果と他の記録の関係 — 関係の記述であって、結果の一部ではない

### 3.1 B-10 read-heavy 本走の 3 block は同符号・同程度を示す — 近接条件の別実行であって再現ではない

B-10 read-heavy 正式系列 (campaign `b10-backoff-shape-silo-read-heavy-formal-acf840c8`、request `977647.nqsv`、
`bnode088`、2026-09-05、izanagi source `2a338449b`、pin `511c953` + patch) は、A-6 と同じ 2 genome
(`none` = `BACK_OFF=0, BACKOFF_FIXED=-1`、`constant-mu2` = `BACK_OFF=1, BACKOFF_FIXED=2`) を 1 job 内の
3 block × 5 標本で測っている。record の median から計算した block 別の効果は **−6.609% / −5.377% / −5.317%**
(none median 10,311,699 / 10,179,288 / 10,158,776 tps、constant-mu2 median 9,630,186 / 9,631,925 / 9,618,673 tps)
で、A-6 の −5.7841% はこの帯に入る。B-10 record の abort 率 (none 0.1549 / 0.1549 / 0.1547、constant-mu2
0.1447 / 0.1447 / 0.1450) も A-6 の 0.1547 / 0.145 と 3 桁目まで並ぶ。

**これは「近接条件の別実行による同符号・同程度の履歴的照合」であって、A-6 protocol の独立再現ではない**
([T-2430] の事後解析、§5.3)。共通するのは CC protocol の Silo、read-heavy (`rratio` 95)、2 genome、cell / block あたり
5 標本、CCBench pin と patch である。A-6 の認証 protocol と B-10 の測定契約が同一という意味ではない。実行 argv の一致は
観測ではなく B-10 の spec によるもので、node・日付・source commit・build 経路・依存の版は異なるか未照合である。
3 block は同一 job・同一 node・同一 build の
反復であって独立な attempt ではなく、実行機会は A-6 と B-10 の 2 つである。B-10 record は
`official_certification = false` (`correctness_certified = true`) で、A-6 と同じく性能値は非認証である。
**本稿は「再現した」と書かない。** 符号の一致は記述的な照合であって再現判定ではない (D1993 項 6 の表現規律と同じ)。

同じ事後解析は、集約 abort 率を条件にした名目待機会計 (1 abort につき 2 µs の spin) が差の大部分と整合することを
記録しているが、それは整合性検査であって機序の同定ではない。本稿は §2.3 の禁止に従い、その数値を A-6 の結果として
転記しない。

### 3.2 反復 attempt は行わない

[T-2430] は「反復 attempt で確かめるか、機序として説明する」という起票に対し、**新しい反復 attempt は行わない**と
裁定した。符号は近接条件の別実行で一致し (§3.1)、大きさは名目会計と整合するので、追加標本が結論の成立条件ではない
(絶対規律 4・5)。反復しても `a4_noise_floor_status` は `open` のまま (producer が定数で書き、validator が
それ以外を拒否する) で、複数 attempt を集約する schema field も無い。**反復しないことで失うのは、別に schedule された
attempt 間の変動 (符号と効果) の観測である。** 本稿はこの不確かさを限定として残す (§4)。

### 3.3 実行基盤の測定に付随して得た A-6 の値は attempt に数えない

遠隔検査の実行基盤を測る過程で得た A-6 の性能値 (効果 −4.876%) は、**A-6 の 2 本目の attempt として扱わない**
(D1870)。attempt として数えるには attempt 数と停止基準の事前登録および `tracked_destination` の新 leaf が要り、
値を見た後の昇格は事前登録の規範 (絶対規律 3) を崩す。本稿はその値を A-6 の結果にも B-10 との照合にも使わない。

### 3.4 A-2 (write-heavy / balanced) と集計しない

A-2 attempt `t2364-20260907b` の outer `observed-positive` (rr5 / rr50) と A-6 の `reject` (rr95) は、別の policy・
別の事前登録・別の attempt であり、**1 つの横断実験として集計しない** (D1993 項 6)。A-2 の outer status は
rr5 と rr50 の論理積、A-6 は rr95 だけの判定であり、論理積を取る workload の集合が違う。adopted の genome も
workload ごとに違う
(rr5 = 10 µs、rr50 = 5 µs、rr95 = 2 µs) ので、A-6 の負の効果は「rr5 で勝った variant を rr95 へ当てた退行」ではない。
3 workload を 1 枚の表に並べる材料は横断稿の側にあり (冒頭)、本稿はそれを引き写さない。

### 3.5 旧環境の値にも、非認証の較正にも遡らない

この certification は旧 `linux-baremetal` の 3 値へ遡らない (D1993 項 4)。policy の `historical_reference`
(CCBench `6656e93`) は比較値ではない (§1.1)。また D1506 (2026-09-02) が read-heavy について「この負荷の正直な答えは
『素のまま』」と書いた根拠は、無 backoff・調整済み adaptive・既定 adaptive を比べた**非認証**の較正であって
(同決定の「限界」節が「variant 採用の根拠には使えない」と明記する)、A-6 の正式 protocol とは測った genome も
検査の有無も違う。A-6 の `reject` を D1506 の裏付けとして、あるいは D1506 を A-6 の予告として読まない。
両者は別の条件を測った別の事実である。

---

## 4. 限定 (この結果が言わないこと)

1. **1 attempt・5 標本の中央値比較である。** 別に schedule された attempt も別ノードでの再現も取っていない (§3.2)。
   `a4_noise_floor_status` は `open` で、between-run floor を超える差・有意差・別走行での再現性は判定しない。
   §2.1 の cv と CI は走行内の記述であり、floor の代用にしない。
2. **read-heavy のこの 1 点の値である。** −5.7841% は rratio 95 / 48 スレッド / 1,000,000 records / zipf 0.9 /
   extime 3 / この pin と patch / この機体の値であって、read-heavy 一般の値ではない。他の read 比率・他の機体・
   他の pin・他の CC protocol へ外挿しない。`global_minimality_established = false`、
   `smallest_observed_sufficient_in_this_two_point_protocol = null` である。
3. **性能の `reject` は正しさ証拠の欠落ではない (D1993 項 2)。** 逆に、正しさの `certified` は性能の認証ではない
   (§2.2)。`reject` が言うのは「この protocol の 2 点比較で adopted の median が stock を上回らなかった」までで、
   read-heavy で stock が最良であることの証明でも、静的 backoff 一般が read-heavy で有害であることの証明でもない。
4. **正しさの証拠は次の 5 つの限定つきである (D1993 項 3 と、その後の [T-2630] / D2108)。**
   - **(i)** verifier の射程は YCSB の point read / write に限った観測 trace 上の直列化可能性である (L01)。
   - **(ii)** correctness 側の run argv は既存 pipeline では独立に記録されておらず、workload の束縛は campaign lock と
     pipeline constructor による (D1257、§2.2)。
   - **(iii)** 成果物自身が `compile_out_evidence_scope` で「source-routed evidence であって、artifact hash 単独では
     compile-out の証明にならない」と宣言している。
   - **(iv)** 条件関門について成果物が保存しているのは admission record と `record_ids` までで、元の record の本体は
     成果物に残らない (§1.4。scheduler stdout への出力は限定を外す根拠にしない)。
   - **(v)** `src_token` の一致だけでは、実翻訳単位全体の意味の一致を保証しない。[T-2630] (2026-09-16) は、変異した
     template の前処理指令 (`#define` / `#undef`) が include 先や別 file に及ぼす効果を identity が捉えない例を
     実測した。**A-6 の attempt でこの変異が発生したことや、誤った認証結果が継承されたことを示すものではない**
     — 到達したのは変異した template を当てた後の identity 層であり、A-6 は無変異の template で走っている。
     ただし「無変異だから安全」を identity の一致から循環して導かない。修正 (D2108、2026-09-17、`-dD` を足し
     環境 prefix を剥がす) は本稿の時点で local main に着地している。D2108 は「EVOLVE_BLOCK_SOURCES 3 file
     (pin `511c953`) と template に指令が無いため、既存の stock / template variant の pre-image は byte 一致する
     (silo 8 genome で旧版 / 新版 8/8 一致を実測)。記録済み測定の無効化・再認証は行わない」と記録する。
     **本稿は A-6 の `src_token` を新実装で再計算して照合していない**し、**この修正を理由に A-6 を再認証も
     昇格もしない** (絶対規律 7)。D2108 が scope 外として残した限界 (指令と include の相対位置、
     `#pragma push_macro` / `pop_macro` の復元値) は D2120 項 7 が「現状維持 + 限界明記」と裁定しており、
     identity の証明力の上限として残る。
5. **条件関門について言えるのは記録までである。** 「関門を実施し通過した」ではなく「そう記録された受領証が
   束縛されている」と書く (§1.4)。
6. **abort 率は代表 rep 1 点の記述的な先行指標である** (§2.3)。因果の機序を主張しない。
7. **B-10 との一致は履歴的照合であって独立再現ではない** (§3.1)。機序は同定していない。B-10 の値は本稿の結果の
   一部ではなく、B-10 record は実行 argv・依存の版・`clocks_per_us` を持たないため A-6 との条件一致は spec による。
8. **反復しないことで失うもの** — attempt 間変動の観測 (§3.2)。反復を行う場合の手順 (attempt 数・停止基準・
   `tracked_destination` の新 leaf の事前登録) は [T-2430] の記録が残しているが、本稿はそれを予定として書かない。
9. **前後比較として読んではならない対象** — A-2 の 2 attempt (別 policy・別 workload、§3.4)、旧環境の read-heavy の
   値 (§3.5)、実行基盤測定の −4.876% (§3.3)、B-10 (§3.1)。いずれも別の条件を測った別の事実である。
10. **policy bytes は測定後に 1 key 変わっている** (§1.3)。`protocol_sha256` は同一だが、事前登録の policy SHA
    (`8969a7e4…`) は下流の受領証の必須 field に無いので機械的には照合されない。この射程の限界は attempt の記録が
    挙げている。
11. **図は無い。** A-6 の 2 cell を描いた凍結図は `figures/` に存在しない。本稿の表と生標本が材料である。
12. **perf は不使用である** (§1.3)。LLC miss 率・IPC は無い (`leading_indicators` の該当 field は `null`)。

---

## 5. 一次資料

### 5.1 権威 bytes と転記元 (repo 内、tracked) — `output/insights/2026-09-08_t2411-paper-story-a6-certification/`

| file | schema | SHA-256 |
|---|---|---|
| `certification.json` | `paper-story-a2-certification-result/v4` | `3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab` |
| `raw-manifest.json` | `paper-story-a2-full-raw-manifest/v4` | `8d17953575afc4594df052d5b5b778291c4d41a1564bb1fbc2d29e8d1df94ef9` |
| `completion-receipt.json` | `paper-story-a2-completion-receipt/v3` | `b3132faf47a60ac73b964f05fb210905828d00d65fc5ffdc19af5b1ce7478247` |
| `submission-receipt.json` | `paper-story-a2-submission-receipt/v4` | `bed969b83c407085bbf2a567ac32057978a97e55d5f223fe044277894b137a20` |
| `acquisition-receipt.json` | `paper-story-a2-acquisition-receipt/v3` | `4885ff482784e5df19f3ee99bd530086d19c9022aa56f6de34262520448cecaf` |
| `condition-gate-rr95.admissions.jsonl` | admission record + `source-evidence/v1` | `79ffe046cfc78d2a42014a28508edcecc3fab5a9cbfde489dcaf32c4594eba0a` |
| `artifact-manifest.json` | `paper-story-a2-artifact-manifest/v1` | `340ee6124c5f0d5a6c72f901c940477a810c664e6acdc50b278fb3639c1b95fc` |
| `COMPLETE.json` | `paper-story-a2-materialization-complete/v1` (上の certification / manifest / protocol の SHA-256 を束縛) | — |

`artifact-manifest.json` は上の 6 file の SHA-256 を列挙し、本稿の執筆時に現物と全件一致した。

### 5.2 durable authority (repo 外)

root は `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b` である。
`raw-manifest.json` が束縛する 6 file と、受領証が束縛する file の SHA-256 は次のとおりで、本稿の執筆時に現物と
全件一致した。

| file (root 相対) | SHA-256 | 束縛元 |
|---|---|---|
| `jobs/rr95/raw/rr95-stock.json` | `d0a47903ee33f24465c3e934cb59f01d07056416d9486750f880208b716eec4d` | raw manifest |
| `jobs/rr95/raw/rr95-fixed2.json` | `91173824743d83e89971eb3ec94d32262fe2e895667d1d3f4e7e547e862ba261` | raw manifest |
| `jobs/rr95/campaigns/paper-story-a2-rr95-paper-story-a6-certification-rr95-1e7d99f2/runs/wal.jsonl` | `36d11c6bf461c9acf6d2ede24ba13549005d0552bac87950d0df4d95da55eaeb` | raw manifest |
| 同 campaign の `campaign.lock` | `f2c841a5c4ff1c930511dab2ff2f99ec5f1e4563bd8bded9518c0b0ef25fc00e` | raw manifest |
| `jobs/rr95/env/pegasus/claims/…-1e7d99f2.claim` | `785968ebc2b0a4c68955721d1ab9e6ad002a072fb615b556f110e28e79a2f0b3` | raw manifest |
| `receipts/condition-gate-rr95.admissions.jsonl` | `79ffe046cfc78d2a42014a28508edcecc3fab5a9cbfde489dcaf32c4594eba0a` | raw manifest |
| `raw-manifest.json` | `8d17953575afc4594df052d5b5b778291c4d41a1564bb1fbc2d29e8d1df94ef9` | completion receipt |
| `jobs/rr95/reservation.json` | `a08081518c1b69a3a7e7c2756f151d8d34a7c244b2548e51b3c3dddbb15877c6` | completion receipt / raw manifest |
| `jobs/rr95/compute-result.json` (`driver_rc = 0`) | `a66d7ae8a521dea137bb56116ba5df34c00c295b5c6d47625346157f69de8d6c` | completion receipt |
| `jobs/rr95/scheduler/job.stdout` (589,570 bytes) | `e8b352f7e8154db55e5eb89aae8e6c17968ff00c1ed82a5205424cd3b6311b89` | completion receipt |
| `jobs/rr95/scheduler/job.stderr` (547 bytes、会計出力) | `546960acf812612f1865f2d97d9308adb3130064e7e86cb69cc30978d44dec7e` | completion receipt |
| `preregistration.json` (`policy_sha256 = 8969a7e4…`、`automatic_retry = false`) | — | attempt root |

campaign WAL は 20 行 (`build_start` 2・`build_done` 2・`verify_done` 12・`bench_done` 2・`commit` 2) で、campaign は
`2 committed / 0 aborted / 0 skipped (of 2)` で終わっている (scheduler stdout の末尾)。

### 5.3 値の出所

| 値 | 出所 |
|---|---|
| median、genome、role、workload、`correctness` の要約、`src_token`、`source_binding_status`、`perf_bin_sha256`、`trace_bin_sha256`、`build_attempt_id` | `certification.json` の `cells[]` |
| 効果 | `certification.json` の `effects.rr95` |
| status、attempt、study、schema、source commit、protocol / policy SHA-256、request、`a4_noise_floor_status`、`global_minimality_established`、`historical_context`、`independent_observation_limits`、`compile_out_evidence_scope` | `certification.json` の対応 field と、埋め込まれた policy bytes |
| 生の 5 標本、`unstable` / `rep_notes`、各 cell の正しさ検査 6 件の verdict と commit witness、toolchain | raw JSON 2 file の `performance` / `correctness` / `build_evidence` |
| `high_variance` / `rounds`、abort 率、`cv`、run argv、configure argv、perf の観測、時刻、`verify_done` の commits / aborts / anomalies / `proof_surfaces` | campaign WAL |
| §3.4 の A-2 attempt、outer status、adopted genome、判定の合成規則 | `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` (SHA-256 `e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671`) の `attempt_id` / `status` / `cells[].genome` と、`policy_bytes_base64` を復号した `workloads` / `certification_composition` |
| request の作成・開始・終了時刻と Elapse | scheduler `job.stderr` の会計出力 (`submission-receipt.json` の qstat に Created、`reservation.json` に開始 epoch) |
| 実行ホスト、campaign claim | `raw-manifest.json` の `campaign_claims`、`reservation.json` |
| 走行時の policy SHA-256 と 1 key 差 | `preregistration.json`、公開 policy bytes との JSON 比較 (§1.3)、attempt の記録 `output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md` (SHA-256 `8a00ba625bb3f681518275cc9873f3d555b370b5c341f7e51852394157839410`) |
| B-10 3 block の median・効果・abort 率・認証 field | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-read-heavy-formal-acf840c8/runs/b10-backoff-shape-blocks/block-{1,2,3}--*--{none,constant-mu2}.json` の `record` (本稿の執筆時に現物から再計算)。事後解析 `output/insights/2026-09-08/t2430-a6-readheavy-mechanism/README.md` (SHA-256 `fb38eaa68cb0d2d0681b9d3f8ace33d6b103608957c73c486182bc67a8ca881b`) と一致 |
| 限定 (v) の実測 | `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` (SHA-256 `faa9b55864d2250ff337ba338f59435a3d2412feed24b7c00fb65c60aa90321b`) |
| 派生統計 (mean・標本 sd・cv・95% CI 半幅・min – max) | 本稿の執筆者が raw JSON の `performance.samples_tps` から §2.1 の式で計算 |

### 5.4 裁定

D12 (protocol status を成功・失敗の宣告へ拡張しない)、D1257 (correctness argv の独立記録)、D1506 (2026-09-02 の
非認証較正に基づく、無 backoff と調整済み adaptive の基準線の裁定)、D1644 (pin + patch 束縛の `src_token`)、D1693 (trace0 configure 文法と旧結果の hash 束縛)、
D1870 (−4.876% は attempt に数えない)、D1993 (項 2・3・4・6)、D2108 ([T-2731] の修正、既存 identity は不変)、
D2120 項 15 (単独 results 稿の経路)、[T-2430] の裁定 (反復 attempt を行わない)。

### 5.5 同じ結果についての既存の稿 (本稿の出所ではない)

`results/2026-09-14-b7-all-workload-regression.md` (2 attempt・6 cell の横断)、
`results/2026-09-16-b7-three-run-materials.md` (3 走行・8 arm の横断) は A-6 の rr95 の median・効果・生標本を
併記している。本稿はそれらを参照して書いていない。値が一致するのは、同じ権威 bytes と durable authority から
それぞれ独立に転記しているからである。**A-6 の 1 attempt の執筆材料には本稿を使い、3 workload を並べる材料には
横断稿を使う。** どちらも凍結物として残る。
