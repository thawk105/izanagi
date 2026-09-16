# B-7 の材料 — 採用静的 backoff の 3 走行を退行込みで併記する (2026-09-16)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** 同系列は append-only であり、2026-09-04 の稿、
2026-09-07 の `reject` の稿、2026-09-07 の `observed-positive` の稿、その英語稿、
2026-09-14 の B-7 横断稿は、いずれも 1 byte も変えずに残る。**2026-09-14 の稿は 2 attempt・6 cell の
材料として引き続き有効であり、本稿はその訂正版ではない。**

**本稿の純増は 2 つだけである。** (1) [T-1998] の balanced stock-inline 対の**詳細な材料**
— 生標本、条件、実行 identity、正しさの記録、限定、転記元 — を results 系列へ初めて置くこと。
(2) その走行を A-2 / A-6 の 2 attempt と**同じ 1 枚の表で並べる**こと。
2026-09-14 の稿は [T-1998] の存在・受理判定・版への導線を既に持っており (同稿の §0.1 と §4.4)、
「results 系列が [T-1998] に一度も触れていない」のではない。**無かったのは詳細材料と併記である。**

**3 走行を 1 file に収めたのは編集判断であって、系列の規則がそれを要求しているからではない。**
[T-1998] 単独の結果節稿を別に書く道も規則上は開いている。本稿がそちらを選ばなかったのは、
B-7 が求めるのが「勝った workload だけを出さない」ことであり、正負を一緒に読める形が
その目的に合うからである。**本稿は単独稿を将来書くことを禁じない。**

**本稿は B-7 の要件を満たしたという判定を行わない。** 最新版 (`2026-09-14.md`) の §8 の B-7 は、
採用静的 backoff について 3 workload の正負を現行環境で報告できるようになったと書き、同時に
**「これは A-1 が定める横断実験の完了ではない」**と限定している。本稿はその限定の内側にとどまる。
**「3 走行そろった」と本稿が言うのは、掲載対象がそろったという文書作業の完了までである** —
B-7 の証拠が網羅的・十分になったという意味ではなく、B-7 の要件充足の扱いを決める未裁定の項目を
閉じるものでもない。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

results 系列は「1 file = 完走した 1 つの protocol または campaign 群の結果」を単位とする (D1631)。
本稿の単位は、**B-7 の材料として名指しした 3 つの完走済み記録群**である。すなわち

- A-2 認証 attempt `t2364-20260907b` の rr5 (write-heavy) と rr50 (balanced)、
- A-6 認証 attempt `a6-20260908b` の rr95 (read-heavy)、
- [T-1998] の balanced stock-inline 対 (別の事前登録、2026-09-13 の走行)

の 3 走行・4 対比較・8 arm である。**今回限定の campaign 群の結果材料としてこの 3 つを選んだ**のであって、
「B-7 に関係する結果なら随時ここへ足してよい」という一般則を作るものではない。

**この 3 走行を統括する単一の正式実験は存在しない。** protocol も事前登録も attempt も投入日も
ホストも違う (§1.3)。**D1993 項 6 が「A-2 / A-6 / balanced stock-inline 対の 3 走行を 1 つの
横断実験として集計しない」と定めている。** 本稿が作るのは事後の併記であり、3 workload を 1 走で
測った横断実験の結果ではない。**プールした効果量、共通の outer status、平均改善率、全体の標本数、
「成功した workload の数」は作らない。**

**これは A-1 が定める横断実験の完了ではない。** 内訳を数えると、A-2 と A-6 の 2 protocol が
3 workload を覆い、[T-1998] が balanced をもう 1 度測って計 3 走行になる、という形である。
**A-1 の本走は未投入であり、認可も据え置かれている** — D1986 項 5 は「今は認可を出さない。
計測経路に残る試験運転専用の分岐を外す実装が閉じた時点で改めて諮る。認可がユーザー手番であることは
変えない」と定める。**本稿が D1986 項 5 から引けるのは認可の据え置きまでである。**
A-1 の本走が未投入であること、および A-1 の探索走と pilot が `formal=false` で横断結論を禁じて
いることは、版 (`2026-09-14.md`) の §8 が記す実行状態であり、**本稿はそれを独立に確かめていない。**

### 0.2 書くもの

8 arm それぞれの genome、median throughput、生 5 標本、記録されたばらつき、abort 率、正しさの記録、
所属する走行の identity と判定の出力。記録上共通の測定設定と、異なる実行 identity。
この併記が言わないことの一覧。

### 0.3 書かないもの

- **B-7 の要件を満たしたか否かの判定。** 本稿はそれを行わない。
- **研究として成功か失敗か、新規性があるかの宣告** (D12)。
- **`observed-positive` / `reject` / `accepted` を成否のラベルへ読み替えること。** いずれも
  protocol または consumer の出力である。
- **3 走行をプールした効果、共通の outer status、平均、順位。**
- **floor を超える差、有意差、走行間の再現性の判定** (§3 の限定 2)。
- **旧 attempt の判定の取り消し** (絶対規律 7、§3 の限定 8)。
- **D1645 の解除判定。** 判定は D1993 項 1 が済ませており、本稿はそれを引き写す (§3 の限定 7)。
- **この効果が他の read 比率・他の workload・他の機体・他の CCBench pin へ転移するという主張。**

---

## 1. 条件

### 1.1 A-2 / A-6 に記録された共通の設定

両 attempt の権威 bytes が持つ policy (`policy_bytes_base64` を復号した `performance_common`) は、
2 attempt で完全に一致する。

| 項目 | 値 |
|---|---|
| スレッド数 | 48 |
| レコード数 | 1,000,000 |
| Zipf skew | 0.9 |
| read-modify-write | 無効 (`0`) |
| 1 トランザクションの最大 operation 数 | 10 |
| 実行時間 | 3 秒 |
| 反復数 | 5 |
| base | `L-W0` |
| WAL | `0` |
| CCBench protocol | Silo |

workload の違いは read 比率だけである (`ycsb_rratio` = 5 / 50 / 95)。
CCBench pin は両 attempt とも `current_pin` が `511c953` (7 文字。**この field から完全長の
SHA を補わない**)。toolchain は図 6 の provenance が
`x86_64-linux-gnu-gcc-11` / `x86_64-linux-gnu-g++-11` (いずれも Ubuntu 11.4.0-1ubuntu1~22.04.3)、
`cmake version 3.22.1` を記録する。同 provenance は `trace_disabled_performance` が `true`、
`perf_used` が `false` であることも記録する。

**列挙した設定は記録上共通である。実行 identity と環境全体の同一性を意味しない** (§1.3)。

### 1.2 [T-1998] の条件と、結果を見る前に固定した 2 点

事前登録 (`docs/t1998-balanced-stock-inline-preregistration.md`、**v1**、sha256
`464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c`) が §2 で固定する対照は次である。

| arm | 意味 | genome |
|---|---|---|
| baseline | backoff を使わない対照 | `BACK_OFF=0`、`BACKOFF_FIXED=-1` |
| target | 静的 fixed 5 µs | `BACK_OFF=1`、`BACKOFF_FIXED=5` |

両 arm とも `NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0` を共有すると
同 §2 が書く。workload は `balanced` (`ycsb_zipf_skew=0.9`、`ycsb_rratio=50`、`ycsb_rmw=0`)、
target の静的 backoff は 5 µs である。

**producer は 8 点を測り、事前登録はそのうち 2 点だけを読む。** 同 §6 は「事後に最良点を選ぶことを
しない。8 点のうち他の 6 点を推定量へ入れない」と書き、「どちらか一方でも `unstable` なら、
対全体を `inconclusive` とし、`ratio` と `improvement_percent` を `null` にする」と定める。
**本稿は登録された 2 点だけを載せる。**
なお本稿の著者は転記の過程で campaign WAL を読んでおり、**残る 6 点の値を見ている。**
見た事実は隠さないが、**本稿はそれを転記も要約もしない。**

走行の argv は campaign WAL の `bench_done` に記録されている。登録された 2 arm の両方について
`-thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9
-ycsb_rratio=50 -ycsb_rmw=0` である。**スレッド数・レコード数・実行時間・skew・rmw・read 比率は
§1.1 の A-2 / A-6 の値と一致する。** ただし `max_ope` はこの argv に現れず、`base` と `WAL` は
policy 層の key なので argv からは確かめられない。**したがって「3 走行の測定設定が全部同じである」
とは書かない。** 一致を確認したのは上に挙げた 6 項目である。

事前登録 §8 は、報告に成果物が記録した identity を含めることを求めている。その実値は次である。

| 項目 | 値 | 出所 |
|---|---|---|
| `repository_commit` | `a551cdd3014708993475108f014aacbf32c21137` | 走行成果物 |
| CCBench gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` | 走行成果物 |
| 環境契約 digest | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` | 解析記録 |
| job body script digest | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` | `reservation.json` の `binding.script_sha256` |
| arm 別 source digest | baseline `2d691b45…`、target `678b7203…` (全桁は §1.4) | campaign WAL の `build_start` |
| baseline の性能 binary digest | `660543647aa9b8bf0b6ff087ec461c901fd186296dc2751cd7d1deb89ae565d9` | 解析記録。campaign WAL の `build_done` の `payload.perf_bin_sha256` にも同値 |
| target の性能 binary digest | `6c89ebd91efddfd6c01fa5fbff1d5d6cf16e8488b7e2fc85f98ec76e1a8dfec4` | 同上 |

**事前登録の sha は 2 か所で束縛されており、同 §8 はその両方を報告に含めることを求めている。**
consumer は**成果物側の定数**と**解析規則側の定数**を別々に持ち、今回はどちらも
`464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` で、
事前登録 file の実計算値とも一致した。**2 つの定数が同じ値であることと、束縛が 1 つしかないことは
別である。**

### 1.3 走行別の実行 identity

| 項目 | A-2 (`t2364-20260907b`) | A-6 (`a6-20260908b`) | [T-1998] (balanced 対) |
|---|---|---|---|
| study | `paper-story-a2-certification` | `paper-story-a6-certification` | 事前登録 v1 (別系統) |
| izanagi source commit | `31ec382a7841e188e46f93e8de4261c964facfb2` | `ae8a767eb60118c3f9791141603fa01ad4f28406` | `a551cdd3014708993475108f014aacbf32c21137` |
| CCBench | `current_pin` = `511c953` | `current_pin` = `511c953` | gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| protocol SHA-256 | `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4` | `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` | — (別系統) |
| 公開された policy SHA-256 | `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` | `96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a` | — (別系統) |
| 環境契約 digest | — (この field を持たない) | — (同左) | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| scheduler request | rr5 `981476.nqsv` / rr50 `981477.nqsv` | rr95 `982234.nqsv` | `0:995755.nqsv` (投入側の表記は `995755.nqsv`) |
| ホスト | rr5 `bnode077` / rr50 `bnode085` | `bnode031` | `bnode024` |
| 日付 | 2026-09-07 | 2026-09-08 | 2026-09-13 |
| protocol schema | `paper-story-a2-certification-policy/v2` | `paper-story-a2-certification-policy/v2` | — |
| 結果 schema | `paper-story-a2-certification-result/v4` | `paper-story-a2-certification-result/v4` | `a5-second-boot-result/v1` |

「—」は**その走行にその形式の記録が無い**という意味であり、該当する保証が無いという意味でも、
値がゼロという意味でもない。3 走行は別の記録形式を持つ。

A-2 の 2 つの campaign は独立の request であり、campaign claim に記録された時刻 (UTC) は
rr5 が `2026-09-07T12:12:55.607184+00:00`、rr50 が `2026-09-07T12:12:55.388302+00:00` である。
**これは campaign の記録時刻であって、投入時刻として読み替えてはならない。**
A-6 の request は Created 01:28:55 / Started 01:29:06 / Ended 02:42:03 (JST、2026-09-08)、
Elapse 4382 秒と記録されている。
[T-1998] は投入 2026-09-13 13:27:23Z、13:27:36Z 開始、13:39:23Z 終了、**記録された Elapse は 712 秒**
である。**Elapse は記録された値であり、開始と終了の時刻差から導いた値ではない** (時刻差は 707 秒で、
記録と 5 秒ずれる。どちらかを訂正する根拠は本稿が読んだ資料には無い)。

**A-6 の policy bytes は測定後に 1 key だけ変わっている。** 走行時の policy bytes の SHA-256 は
`8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8` で、公開された成果物が持つ値
(`96ed47d0…`) と異なる。attempt の記録は、差が `tracked_destination` の 1 key だけであり、
その key は `_protocol_preimage` に含まれないため `protocol_sha256` は前後で同一であると書いている。
**本稿はこの前後不変性を独立に再計算していない。** 書けるのは「attempt の記録がそう記録している」
までであり、公開 policy hash を投入時の hash として表示しない。

### 1.4 adopted / target が patch の当たった木で build されたことの記録

A-2 の 4 cell と A-6 の 2 cell は、いずれも `source_binding_status` が `bound` で、
stock cell の `src_token` は `stock`、adopted cell の `src_token` は非 `stock` である。

| cell | role | `src_token` |
|---|---|---|
| `rr5-stock` | stock | `stock` |
| `rr5-fixed10` | adopted | `955b452a332d…` |
| `rr50-stock` | stock | `stock` |
| `rr50-fixed5` | adopted | `21def77c944b…` |
| `rr95-stock` | stock | `stock` |
| `rr95-fixed2` | adopted | `0b3abbe62a60…` |

**[T-1998] の走行成果物 (`result.json`) はこの形の field を持たない。** 同走行が使う束縛は
**事前登録 §4.2 が固定した arm 別の source bytes digest** であり、その実値は campaign WAL の
`build_start` にある。同 WAL は `payload.src_token` も記録しているので、**`src_token` という
field 自体が無いのではなく、走行成果物の側に無い**と読む。登録された 2 arm は次のとおりである
(digest は `payload.build_admission.source.source_bytes_sha256`)。

- baseline — genome は `silo` に `BACKOFF_FIXED=-1`、`BACK_OFF=0`、`NO_WAIT_LOCKING_IN_VALIDATION=1`、
  `NO_WAIT_OF_TICTOC=0`、`WAL=0`。`src_token` は `stock`。
  arm 別 source bytes SHA-256 は `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6`。
- target — genome は `BACKOFF_FIXED=5`、`BACK_OFF=1` で、他の 3 つは baseline と同じ。
  `src_token` は source bytes digest そのもので、
  `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12`。

**走行成果物の `reservation.json` が持つのは `source_binding.repository_commit` と
`source_binding.ccbench_gitlink_commit` の 2 値だけであり、arm 別 digest はそこには無い。**
投入時に事前登録 §4 の表と 5 値すべてが一致したことは、投入・回収の記録 §1 が書いている。

事前登録 §9 は compiler の同一性について次のように書いている (連続した 4 文を切らずに引く)。

> §4.2 の source digest は、この論文環境のログインノードの `g++` で導いた。計算ノードの `g++` が
> 同一の前処理結果を与えることは証明していない。版はどちらも GNU 11.4.0 だが、版の一致は
> header 閉包の一致ではない。**食い違えば `source-identity-unbound` で fail-closed に落ちる。**

---

## 2. 結果

### 2.1 主表 — 3 走行・4 対比較の利得と退行

**正の効果と負の効果を同じ表に置く。** 節を分けて退行を別扱いにしない。
**1 行 = 1 対比較である。行をまたいで足し合わせた量は作らない。**

| 所属走行 (登録の単位) | workload | 比較対 | stock / baseline median (tps) | adopted / target median (tps) | 効果 | abort 率 | 判定の出力 |
|---|---|---|---:|---:|---:|---|---|
| A-2 `t2364-20260907b` (A-2 policy) | rr5 (write-heavy) | stock / fixed 10 µs | 2,438,295 | 3,987,794 | **+63.5485%** | 0.7845 → 0.3833 | A-2 outer (rr5 ∧ rr50) = `observed-positive` |
| A-2 `t2364-20260907b` (A-2 policy) | rr50 (balanced) | stock / fixed 5 µs | 3,756,230 | 4,297,929 | **+14.4213%** | 0.685 → 0.4615 | A-2 outer (rr5 ∧ rr50) = `observed-positive` (上行と同一の判定) |
| A-6 `a6-20260908b` (A-6 policy) | rr95 (read-heavy) | stock / fixed 2 µs | 10,088,796 | 9,505,248 | **−5.7841%** | 0.1547 → 0.145 | A-6 outer (rr95) = `reject` |
| [T-1998] (事前登録 v1) | balanced | baseline / target fixed 5 µs | 3,893,509 | 4,330,570 | **+11.225375361916456%** | 0.6795 → 0.4613 | consumer = `accepted` (`reason` = `preregistered-balanced-stock-inline-pair`) |

stock / baseline は 4 対比較とも `BACK_OFF=0, BACKOFF_FIXED=-1`、adopted / target は `BACK_OFF=1` に
対ごとの `BACKOFF_FIXED` (10 / 5 / 2 / 5) を組み合わせた genome である。

**効果の出所と計算は走行ごとに違う。**

- A-2 / A-6 の効果は権威 bytes の `effects` フィールドの値であり、その定義は
  `adopted median / stock median − 1` である。掲載した百分率は `100 × effects` を小数点以下 4 桁へ
  丸めたものである。権威値は `rr5 = 0.6354846316791036`、`rr50 = 0.14421348000521794`、
  `rr95 = -0.057841193339621455`。表の median を入力した比の再計算は 3 件とも権威値と一致した
  (照合のための再計算であり、掲載値の権威は `effects` 側にある)。
- [T-1998] の効果は走行成果物が持つ `improvement_percent` を**丸めずに全桁**転記した。
  同成果物の `ratio` は `1.1122537536191646` で、事前登録 §6 の定義
  (`ratio = target の median / baseline の median`、`improvement_percent = (ratio - 1) * 100`) に従う。

**判定の出力も走行ごとに単位が違う。** A-2 の `observed-positive` は**復号した policy の
`certification_composition.outer_certification` が `logical conjunction in policy workload order` と
定めるとおり、rr5 と rr50 の論理積**であって、rr5 単独・rr50 単独の status ではない。
A-6 の `reject` は rr95 の 1 workload に対する outer status である。
[T-1998] の `accepted` は**事前登録された 2 点対に対する consumer の出力**であって、
A-2 / A-6 と同じ certification protocol の outer status ではない。
**3 つを 1 つの階層に置いて共通の status を作ることはできない。**

**`observed-positive`・`reject`・`accepted` は、それぞれの protocol または consumer が出力した
値である。** 研究としての成功・失敗・新規性、あるいは B-7 の充足を表すラベルではない。

### 2.2 全 8 arm の生標本

各資料に記録された順序をそのまま保持して載せる。

| arm / cell | 5 標本 (tps、記録順) |
|---|---|
| `rr5-stock` | 2601945, 2438295, 2395095, 2449052, 2429806 |
| `rr5-fixed10` | 4066753, 3987794, 4008033, 3983201, 3976744 |
| `rr50-stock` | 4003328, 3738171, 3756230, 3799369, 3745012 |
| `rr50-fixed5` | 4378620, 4279072, 4304483, 4297929, 4252521 |
| `rr95-stock` | 10365808, 10103030, 10029940, 10088796, 10073679 |
| `rr95-fixed2` | 9753031, 9587735, 9488225, 9494008, 9505248 |
| [T-1998] baseline | 4079966, 3891020, 3978513, 3859794, 3893509 |
| [T-1998] target | 4437166, 4326276, 4361949, 4330570, 4289164 |

**8 arm すべてについて、2 つ以上の記録が同じ並びを持つことを確かめた。**

| arm / cell | 記録 1 | 記録 2 | 記録 3 |
|---|---|---|---|
| A-2 の 4 cell | durable authority の raw JSON の `performance.samples_tps` | 同走行の campaign WAL の `bench_done` の `payload.tps` | 図 6 provenance の `cells[].samples_tps` |
| A-6 の 2 cell | durable authority の raw JSON の `performance.samples_tps` | 同走行の campaign WAL の `bench_done` の `payload.tps` | attempt の記録と事後解析の本文 |
| [T-1998] の 2 arm | 走行成果物の `no_backoff_tps` / `target_tps` | 同走行の campaign WAL の `bench_done` の `payload.tps` | — |

**これは独立した再測定ではない。** 同じ 1 回の走行を、producer が複数の場所へ書き出したものである。
確かめたのは記載順と値が食い違っていないことだけであり、標本が 2 度取られたという意味ではない。

### 2.3 ばらつき — producer の `cv` は 3 走行で同じ field、表示資料の定義は違う

**3 走行の campaign WAL は、いずれも `bench_done` の `payload.cv` に同じ名前でばらつきを記録している。**
本稿はその値を 8 arm そろえて載せる。

| arm / cell | campaign WAL の `cv` | 標本標準偏差 (tps、分母 n−1) | 95% 信頼区間の半幅 (tps) |
|---|---:|---:|---:|
| `rr5-stock` | 0.03262426529519532 | 80348.29986564744 | 99765.59126005495 |
| `rr5-fixed10` | 0.0091676473320761 | 36711.889579535404 | 45583.83159694112 |
| `rr50-stock` | 0.02928349930898821 | 111523.9230053355 | 138475.2401341739 |
| `rr50-fixed5` | 0.010942253518241333 | 47079.31931857129 | 58456.69585780905 |
| `rr95-stock` | 0.013166532966358306 | — | — |
| `rr95-fixed2` | 0.01173175682351728 | — | — |
| [T-1998] baseline | 0.022721229214372803 | — | — |
| [T-1998] target | 0.012790608817328908 | — | — |

「—」は**その値を記録した資料を本稿が読んでいない**という意味であり、ゼロではない。標本標準偏差と
信頼区間の半幅は図 6 の provenance が A-2 の 4 cell についてだけ持つ。生標本 (§2.2) は 8 arm すべてに
ついて載せてあるので、必要なら任意の定義で計算できる。

**`cv` の定義は、本稿が読んだ資料のどれも明文で書いていない。** そこで本稿は、§2.2 の生標本から
`標本標準偏差 (分母 n−1) / 標本平均` を 8 arm すべてについて計算し、WAL の `cv` と突き合わせた。
**8 arm とも倍精度の全桁で一致した。** これは定義の確認であって新しい測定ではなく、掲載値の権威は
WAL の `cv` 側にある。**それでも「producer が `cv` をこの式で定義している」と断定はしない** —
確かめたのは値の一致であって、実装の定義そのものではない。

**A-6 の insight README が載せている 1.18% / 1.06% は別の統計量である。** 同 README はそれを
「母標準偏差を中央値で割った値」と書いており、生標本から同じ式で計算すると `rr95-stock` 1.1827%、
`rr95-fixed2` 1.0560% になる (丸めて 1.18% / 1.06%)。**上の `cv` 列と同じ量ではないので、
同じ列に置かない。**

**平均の信頼区間は標本を記述するものであって、効果・判定・median の信頼区間ではない。**
本稿は有意性の判定を行わない。

[T-1998] の campaign WAL は登録 2 arm の `unstable` をいずれも `false` と記録している。
事前登録 §6 はどちらかが `unstable` なら対全体を `inconclusive` にすると定めるので、
**`accepted` が出たことは 2 arm とも `unstable=false` だったことと整合する。**

### 2.4 正しさの記録 — 3 走行で形式が同じではない

**A-2 と A-6** は、6 cell すべての `correctness.status` が `certified` で、`disposition` は `pass`、
`legacy` と `performance` がいずれも `pass`、`legacy_repetitions_observed` は 1、
`performance_repetitions_observed` は 5 と記録している。同じ field が
`workload_argv_observation` を `not-independently-recorded-by-existing-pipeline` と記録している。

**この反復数は durable authority 側の cell ごとの raw JSON でも確かめた。** 6 cell とも
`correctness.legacy` の要素数が 1、`correctness.performance` の要素数が 5 である。
同じ raw JSON は `build_evidence.performance_trace_disabled_build` を `true` と記録しており、
**性能値が trace 無効のビルドから来ていることが、図の provenance とは独立に durable authority 側にも
記録されている** (絶対規律 1)。

**[T-1998]** の走行成果物 (`result.json`) には `correctness` 欄が無い (全 23 key を列挙して確認した)。
正しさの記録は campaign WAL の側にある。同 WAL は 8 genome それぞれに `verify_done` を 1 件持ち、
**登録された 2 arm の両方について `verdict` = `serializable`、`certified` = `true`、
`anomalies` = 0、`workload.tag` = `legacy`** と記録している。

**この 2 つは同じ強さの記録ではない。** A-2 / A-6 は legacy 1 回に加えて**性能条件側の正しさ検査を
5 回**観測した記録を持つが、[T-1998] の WAL が持つのは genome あたり 1 件の `legacy` タグの検査だけで
ある。**本稿は [T-1998] について「performance 条件の正しさ検査が何回通った」とは書かない。**
同時に、**「[T-1998] の正しさを検査していない」とも書かない** — 検査は記録されている。

**いずれの走行についても、これは性能の認証ではない。** 正しさは trace-enabled の走行から来ており、
性能値は trace-disabled の走行である (絶対規律 1)。A-2 / A-6 の `correctness` の中に
`performance` という名の field があるが、これは「performance 条件で行った正しさ検査」の意味であって
性能の判定ではない。[T-1998] の事前登録 §7 も同じ分離を、2 つの項目として次のように書いている。

> - 性能計測は trace-disabled build で行う。正しさ検証は別走・別ビルドである (絶対規律 1)。
> - verifier が anomaly を出した variant は即 reject する (絶対規律 2)。本書はこの gate を緩めない。

**退行した rr95 の adopted cell も certified である。** 「正しさを保ったまま性能で負けた」と
書けるのは、検査された範囲と観測された median についてであり、正しさの合格は性能の優越の
十分条件ではない。逆に、性能で勝ったことが正しさの証拠になることもない。

### 2.5 [T-1998] の producer 完了と consumer 判定は別の出力である

走行成果物のトップレベル `status` は `complete` である。**これは producer の走行完了状態であって、
事前登録された対の判定ではない。** 判定は同じ保全成果物を consumer
(`orchestrator/campaign/t1998_stock_inline_pair.py`) へ通した解析記録の側にあり、
`status` = `accepted`、`reason` = `preregistered-balanced-stock-inline-pair` である。
**後者を前者の field として扱わない。**

**この対は 3 度解析されている。** 1 度目 (2026-09-13) は consumer が拒否を返し、原因は測定側ではなく
consumer 側にあった。2 度目は consumer の是正 (2026-09-14) の後で、**再測定なしで**同じ保全成果物を
通し直して `accepted` になった。3 度目は着地後の main からの解析 (2026-09-15) で、同じ値が全桁再現した。
**再解析は追加の標本でも独立な再現でもない。** 同じ 10 標本を読み直しただけである。

---

## 3. 限定 — この併記が言わないこと

1. **同一 variant を他 workload へ当てた退行の比較ではない。** adopted / target の genome は
   対ごとに異なる (rr5 = fixed 10 µs、rr50 = fixed 5 µs、rr95 = fixed 2 µs、[T-1998] = fixed 5 µs)。
   rr95 の負の効果は、rr5 で勝った fixed 10 µs を rr95 へ当てた結果ではない。**本表は workload 別に
   指定された採用構成と各 stock の比較であり、同一 variant の workload 間退行を検証したものではない。**

2. **floor を超える差は 4 対比較とも判定していない。** A-2 / A-6 の `a4_noise_floor_status` は
   `open` である。[T-1998] の成果物はこの field を持たず、事前登録も floor 超の判定を課していない。
   **正の効果 (+63.5485% / +14.4213% / +11.225375361916456%) にも、負の効果 (−5.7841%) にも、
   同じ留保が掛かる。** between-run floor を超える差、有意差、別走行での再現性は本表から判定しない。
   §2.3 のばらつきは走行内の記述であり、between-run floor の代用にしない。

3. **事前登録の失敗条件 (e) の前件が成立したとは言えない。** (e) は「target workload では勝つが
   他の workload で **floor 超の**退行がある」を前件とする。床値が未確定である以上、前件の成立は
   立証できない。**同時に「発火しない」と確定したわけでもない。** 選択的報告を禁じる (e) の趣旨に
   従い、床値の判定を待たずに正負をそろえて載せた。載せたこと自体を義務の履行として宣告しない。

4. **本稿の材料には、同一 variant の workload 間比較が含まれていない。** その比較を行う測定の形を
   言葉にすると「対象 workload で評価する variant を固定し、その同一 variant と対応する stock を
   対象 workload と他 workload の全件で比較する。正しさは別の trace-enabled 走行、性能は
   trace-disabled 走行とし、between-run floor を評価できる反復と束縛された条件のもとで正負の差を
   報告する」となる。**これは失敗条件 (e) と観測者効果の分離 (絶対規律 1) に照らした説明であって、
   B-7 の充足条件の確定でも、新しい事前登録でも、測定の実施要求でもない。**

5. **abort 率は arm あたり 1 点の集約値である。** A-2 / A-6 の定義は
   `aborts / (aborts + commits)`。[T-1998] の値は campaign WAL の `bench_done` の
   `leading_indicators.abort_rate` である。標本ごとの率でも、信頼区間を持つ量でもなく、
   因果の機序を主張する量でもない。記述的な先行指標として読む。

6. **3 走行を統括する単一の正式実験は存在しない。** protocol instance、事前登録、source commit、
   投入日、ホストが違う (§1.3)。**D1993 項 6 に従い、主表の 4 行をプールした効果も共通の outer status も
   作っていない。** 符号が 3 workload とも旧環境と一致したことは記述的な照合であって、再現判定ではない。

7. **D1645 の解除は本稿が判定したものではない。** D1993 項 1 が、attempt `t2364-20260907b` が
   D1645 の解除条件 (「正しい identity で取り直した attempt が出るまで」) を満たすと裁定している。
   **本稿はその裁定を引き写すだけで、独立に裁定し直さない。** §1.4 の `src_token` の記録を挙げることも、
   解除の裁定そのものではない。
   なお旧 `figures/fig5_a2_certification_reject` の用途制限は、2026-09-11 の追補により
   **期限なし**であり、新 attempt の取得によって解除されない (`figures/README.md` の該当節が正本)。

8. **旧 attempt の判定を取り消すものではない。** attempt `t2022-20260828c` の `reject` は、
   patch の当たっていない木で `BACK_OFF` の有効/無効を測った別の事実として記録に残る
   (絶対規律 7、D1645)。本稿の値と前後比較として読んではならない。
   **[T-1998] の 1 度目の拒否と 2 度目の受理も、前後比較として読んではならない** — 動いたのは
   consumer であって測定ではない (§2.5)。

9. **最小性も一般性も主張しない。** A-2 / A-6 の `global_minimality_established` は `false`、
   `smallest_observed_sufficient_in_this_two_point_protocol` は `null` である。
   `−5.7841%` は read-heavy のこの 1 点 (rratio 95 / 48 スレッド / zipf 0.9 / extime 3) の値で
   あって read-heavy 一般の値ではない。[T-1998] の `+11.225375361916456%` も balanced のこの
   1 対の値である。他の read 比率・他の機体・他の pin へ外挿しない。

10. **条件関門について言えるのは記録までである。** A-2 / A-6 は canonical な admission record を
    cell 分束縛しているが、元の supply / meaning records は成果物に保存されていない。
    「関門を実施し通過した」ではなく「そう記録された受領証が束縛されている」と書く。

11. **compile-out の証拠は source 経由である。** A-2 / A-6 の `compile_out_evidence_scope` は
    `source-routed evidence; artifact hashes are not standalone compile-out proof` と記録する。
    成果物の hash 単独では trace のコンパイル除去の証明にならない。[T-1998] の性能 binary の
    digest も、それ単独では compile-out の証明にならない。

12. **独立観測の限界が記録されている。** A-2 / A-6 の `independent_observation_limits` は
    `correctness_run_argv` を `not-recorded-by-existing-pipeline`、`correctness_workload_binding` を
    `campaign-lock-and-pipeline-constructor; not an independent argv observation` と記録する。
    加えて A-2 側の正しさの証拠は、限定 L01 により point-key trace に限られる。
    **D1993 項 3 が残した 4 つの限定 — (i) L01 の point-key trace、(ii) correctness argv の独立記録の
    不在、(iii) 成果物 hash 単独では compile-out の証明にならないこと、(iv) 条件関門について
    保存されているのは admission record と `record_ids` までであること — は、本稿でも外れない。**
    **A-2 / A-6 による但し書きの解除を、[T-1998] の独立した certification として読み替えない。**

13. **[T-1998] の consumer は 2026-09-14 の是正で受理集合が広がっている。** 是正の記録は
    「事前登録 §6 が列挙する判定規則は 1 つも動かない」と書いたうえで、**「受理集合は広がる」**と
    明記している。撤去されたのは腕内の toolchain digest 再導出という、実成果物では原理的に成立しない
    等式である。**これは同じ成果物の解析側の是正であって、性能の改善でも正しさの向上でもない。**
    「受理条件はすべて不変だった」と書いてはならない。

14. **[T-1998] の toolchain 保証には穴が残る。** 同じ是正の記録が「両腕の digest を同じ別値へ
    置換した改竄は、この層では拒否できない」と明記している。回収成果物に全文 manifest が無いため、
    digest の再計算と identity 射影との暗号学的対応は検証されない。**本稿はこの穴を塞いでいない。**

15. **[T-1998] の compiler 同一性は保証されていない。** 事前登録 §9 が「計算ノードの `g++` が
    同一の前処理結果を与えることは証明していない」と書く。着地後の main での再解析も、
    同じ成果物に対する非独立な確認にすぎない。

16. **1 つの成果物が受理されたことから、consumer 全体に欠陥が無いことは導けない。**
    言えるのはこの成果物で追加の拒否に遭遇しなかったことだけである。

17. **事前登録前に取れた値は混ぜていない。** [T-1998] の事前登録 §3 は 2026-09-07 に A-5 経路で
    取れた balanced の対の生値を開示したうえで、D1874 に従い主張へ転用しないと定める。
    **本稿はその 2 値を載せず、推定量にも入れていない。** A-2 の rr50 は別の certification attempt の
    値であり、日付が 2026-09-07 であることだけを理由に禁止対象になるものではない。

18. **この certification は旧 `linux-baremetal` の 3 値へは遡らない** (D1993 項 4)。
    旧環境の性能値を本稿の値で裏付け済みと説明してはならない。

19. **本稿の性能値は認証されておらず、併記は採用の許可ではない。** 正の効果と `accepted` または
    `observed-positive` が同じ行に並んでいることを、variant を採用してよいという判断として
    読んではならない。**絶対規律 2 が禁じるのは、正しさを破る variant を採ることである。**
    本稿はその gate を緩めない — verifier が anomaly を出した variant は即 reject という扱いは
    3 走行とも不変である。**本稿は性能値を採用判断の材料に使うこと自体を禁じる文書ではない。**
    禁じているのは、ここに並ぶ値だけで採用を正当化することである。

20. **[T-1998] は A-5 の但し書きを外していない。** 事前登録 §9 は「『計算機を別に起動し直して
    取り直す』ことは D1525 により Pegasus では充足しないと確定しており、本書はそれを外さない。
    本書が扱うのは別の穴である」と書く。**別ホスト・別日付で測ったこと、prospective な事前登録が
    あることを、再起動による取り直しの証拠として読んではならない。**

---

## 4. 一次資料

### 4.1 権威 bytes と転記元 (repo 内、tracked)

SHA-256 は本稿の起草時に現物から実計算した。

| 資料 | path | SHA-256 |
|---|---|---|
| A-2 認証成果物 | `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` | `e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671` |
| A-6 認証成果物 | `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json` | `3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab` |
| A-2 raw manifest | `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json` | `b23ee2ee6ff36d2377da80c2cf4eccc925bae9c3d89aab8a6a8543edfe9ae319` |
| A-6 raw manifest | `output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json` | `8d17953575afc4594df052d5b5b778291c4d41a1564bb1fbc2d29e8d1df94ef9` |
| A-2 図 6 の provenance | `docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json` | `760b899b331719ff947f3f8df591e56f57f956f97c3d2debb20d392d427299e6` |
| A-6 attempt の記録 | `output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md` | `8a00ba625bb3f681518275cc9873f3d555b370b5c341f7e51852394157839410` |
| A-6 退行の事後解析 | `output/insights/2026-09-08/t2430-a6-readheavy-mechanism/README.md` | `fb38eaa68cb0d2d0681b9d3f8ace33d6b103608957c73c486182bc67a8ca881b` |
| [T-1998] 事前登録 (v1) | `docs/t1998-balanced-stock-inline-preregistration.md` | `464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` |
| [T-1998] 投入・回収・1 度目の解析 | `output/insights/2026-09-13_t2557-balanced-stock-inline/README.md` | `b30d40df1af83293c78716b08ba3aafa8894a3c9ee0601e165a838d4ba226674` |
| [T-1998] consumer 是正と 2 度目の解析 | `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md` | `d01e374f90299071d60f7bb7f0bea7ab48bc9a745403791f00daa44f913958c9` |
| [T-1998] 着地後 main での 3 度目の解析 | `output/insights/2026-09-15/t1998-landed-main-recheck/README.md` | `2c7a5a9063f53e8aa26c7001da3ab61839f77b8a6aab86112a13a9856edba881` |
| 事前登録の失敗条件 (e) | `docs/phase3-main-experiment.md` | `e544de1969dd4df13dc42aa3d165e22b70fab2ab399dc011baa46359727bea45` |

A-2 の `certification.json` の SHA-256 は、同じ dir の `artifact-manifest.json` の
`files["certification.json"]` と `COMPLETE.json` の `certification_sha256` にも同じ値が
記録されている。A-6 についても同様である。

**`raw-manifest.json` と `artifact-manifest.json` は別物である。** 前者
(schema `paper-story-a2-full-raw-manifest/v4`) は durable authority 側の生成物 — campaign lock、
campaign WAL、cell ごとの raw JSON、条件関門の受領証 — を root 相対 path と SHA-256 で束縛し、
campaign claim (host、job id、boot id、protocol digest) を記録する。後者は insight dir に公開した
file 群の hash を持つ。§3 の限定 10 が言う admission record の束縛は前者にある。

### 4.2 値の出所

| 掲載値 | 出所 |
|---|---|
| A-2 / A-6 の median、genome、role、workload、正しさ、`src_token`、`source_binding_status` | 両 `certification.json` の `cells[]` |
| A-2 / A-6 の効果 | 両 `certification.json` の `effects` |
| A-2 / A-6 の attempt、study、schema、source commit、protocol / policy hash、request | 両 `certification.json` の `attempt_id`、`study`、`schema_version`、`protocol_schema`、`source_commit`、`protocol_sha256`、`policy_sha256`、`request_ids` |
| 床値状態、最小性、compile-out の射程、独立観測の限界 | 両 `certification.json` の `a4_noise_floor_status`、`global_minimality_established`、`smallest_observed_sufficient_in_this_two_point_protocol`、`compile_out_evidence_scope`、`independent_observation_limits` |
| §1.1 の共通設定と §2.1 の判定合成規則 | 両 `certification.json` の `policy_bytes_base64` を復号した `performance_common` と `certification_composition` |
| §1.1 の CCBench pin | 両 `certification.json` の `current_pin` |
| §1.1 の toolchain・perf・性能の build | 図 6 provenance の `measurement_conditions` (`toolchain`、`perf_used` = `false`、`trace_disabled_performance` = `true`) |
| rr5 / rr50 の標本標準偏差・CI 半幅・ホスト・campaign 時刻 | 図 6 provenance の `cells[]` (`sample_stdev_tps`、`ci95_half_tps`) と `measurement_conditions.workloads` |
| 6 cell の生標本 | durable authority の cell ごとの raw JSON の `performance.samples_tps`。図 6 provenance の `cells[].samples_tps` (rr5 / rr50) と A-6 の 2 つの insight README (rr95) にも同じ並びがある |
| 8 arm の `cv` と abort 率 | 3 走行の campaign WAL の `bench_done` の `payload.cv` と `payload.leading_indicators.abort_rate` |
| rr95 の 1.18% / 1.06% (母標準偏差 / median) | A-6 attempt の記録の「結論」節 (事後解析 §1 にも同値)。**同 attempt 記録に abort 率の掲載はない** |
| 6 cell の trace 無効ビルドと正しさの反復数 | durable authority の raw JSON の `build_evidence.performance_trace_disabled_build`、`correctness.legacy`、`correctness.performance` |
| A-6 の走行時 policy hash と 1 key 差の説明 | A-6 attempt の記録 |
| [T-1998] の genome 対・固定 5 µs・8 点中 2 点・`unstable` 規則・trace 分離・compiler 非保証 | 事前登録の §2・§6・§7・§9 |
| [T-1998] の生標本・median・`ratio`・`improvement_percent`・identity・toolchain・perf・`status=complete` | 走行成果物 `result.json` |
| [T-1998] の走行 argv・`cv`・`unstable`・abort 率・`verify_done` の judgement | 同走行の campaign WAL (`bench_done` と `verify_done`) |
| [T-1998] の job body digest と source binding | 同走行の `reservation.json` (`binding.script_sha256`、`source_binding`) |
| [T-1998] の投入・開始・終了時刻と Elapse、投入器 | 投入・回収の記録 §1 |
| [T-1998] の consumer 判定 (`accepted` / `reason`)、環境契約 digest、binary digest、事前登録の 2 つの sha | consumer 是正の記録 §1 と着地後 main の再解析 §2 (両者は全桁一致する) |
| [T-1998] の受理集合の拡大と toolchain 保証の穴 | consumer 是正の記録 §2.2 と §2.3 |
| 事前登録の失敗条件 (e) | `docs/phase3-main-experiment.md` の「失敗条件 (何が出たら negative か、正直に)」節 |
| B-7 の項目本文と A-1 の実行状態 | `docs/paper-story/2026-09-14.md` の §8 |

**照合した範囲と、していない範囲を分けて書く。照合先は走行によって違う。**

- **A-2 と A-6** — 4 + 2 cell の raw JSON と 2 + 1 本の campaign WAL を durable authority の現物で
  読み、**その attempt の `raw-manifest.json` の `files` が束縛する SHA-256 と 9 件すべて
  突き合わせた** (§4.3)。
- **[T-1998]** — 走行成果物・`reservation.json`・campaign WAL を現物で読んだ。**この走行に
  `raw-manifest.json` は無い。** campaign WAL の照合先は走行成果物の `wal_sha256` であり、
  A-2 / A-6 とは束縛の出所が違う。

**照合していないのは、A-2 / A-6 の raw manifest が束縛する残りの file** — campaign lock、
環境の claim、条件関門の受領証 (`receipts/condition-gate-*.admissions.jsonl`) — **の中身である。**
これらについては SHA-256 の束縛が manifest にあることを確認したにとどまる。
[T-1998] については campaign lock の中身も読んでいない。

### 4.3 durable authority (repo 外)

**これらは repo の tracked file ではない。本稿は下に挙げた file を現物で読み、SHA-256 を実計算した。**

**A-2** の root は
`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b`、
**A-6** の root は
`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b` である。
下の path は各 root からの相対で、**SHA-256 は対応する `raw-manifest.json` の `files` が束縛する値と
6 件 + 3 件すべて一致した。**

| 走行 | root 相対 path | SHA-256 (実計算) |
|---|---|---|
| A-2 | `jobs/rr5/raw/rr5-stock.json` | `881fa172e406f6888909ad95a1cf1fc5d464892ae746fa648581f9873c522800` |
| A-2 | `jobs/rr5/raw/rr5-fixed10.json` | `d3d99911b33a6b0ade553be2d17d05f9fb03c519c12454f548077bd394b5b8d3` |
| A-2 | `jobs/rr50/raw/rr50-stock.json` | `8dd7d18659a9ff2614d622f3453ec806e33e3d78a1f47a5fedbdebee6b103f36` |
| A-2 | `jobs/rr50/raw/rr50-fixed5.json` | `84a34693d4bd35ad2548600165116d13158560690ce839571f5e3bdb00f993e9` |
| A-2 | rr5 の campaign WAL (`.../runs/wal.jsonl`) | `adf736557389f139574523d631d27727d40060a70d6a35f6d89952664cd4e158` |
| A-2 | rr50 の campaign WAL (`.../runs/wal.jsonl`) | `fb40ee26c89638cbec021be04f3ff25438f2c44a63a9153d1255bfb7bc018ec9` |
| A-6 | `jobs/rr95/raw/rr95-stock.json` | `d0a47903ee33f24465c3e934cb59f01d07056416d9486750f880208b716eec4d` |
| A-6 | `jobs/rr95/raw/rr95-fixed2.json` | `91173824743d83e89971eb3ec94d32262fe2e895667d1d3f4e7e547e862ba261` |
| A-6 | rr95 の campaign WAL (`.../runs/wal.jsonl`) | `36d11c6bf461c9acf6d2ede24ba13549005d0552bac87950d0df4d95da55eaeb` |

campaign の名前は A-2 が `paper-story-a2-rr5-paper-story-a2-certification-rr5-1af9fc2b` と
`paper-story-a2-rr50-paper-story-a2-certification-rr50-5efd479e`、A-6 が
`paper-story-a2-rr95-paper-story-a6-certification-rr95-1e7d99f2` である。

**[T-1998]** の保全成果物の root は
`/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced`
である。

- `result.json` の SHA-256 = `354ecd5f6c71f26bec3adf6ba95dd3d82142d5c9deb70849180fcec19306c183` (実計算)
- `reservation.json` の SHA-256 = `45cb2cf13f8a247d44a2275c53a7fabb60861078bcce44c99bcc15a7d13f1c7d` (実計算)
- campaign WAL は同 root 配下の campaign `backoff-sweep-silo-balanced-sweep-0dd37c05` にあり、
  その SHA-256 は走行成果物の `wal_sha256` = `154ab894a9955885036fcaff03478001153ba015c50f395cbb59b3e20dcf594e`
  として記録されている。campaign lock の SHA-256 は同成果物の `lock_sha256` =
  `ba24c65d01ce80bb17d0ae1ff8f5242078c2cb7b9a6b3c502959542b61ba0c61` である。

A-2 の durable authority は、図 6 の provenance JSON の `external_inputs` が root 相対 path と
SHA-256 で 12 件記録している。

### 4.4 同じ結果についての既存の稿

- `results/2026-09-14-b7-all-workload-regression.md` — B-7 の材料として A-2 の rr5 / rr50 と
  A-6 の rr95 を横断で併記した稿。**[T-1998] を明示的に対象外としている。**
  同稿は 2 attempt・6 cell の材料として有効なまま残り、本稿はその訂正版ではない。
- `results/2026-09-07-a2-certification-observed-positive.md` — attempt `t2364-20260907b` の
  結果節 (rr5 / rr50 の 4 cell、図 6、限定 6 件)。
- `results/2026-09-09-a2-certification-observed-positive-en.md` — 直上の英語稿。
- `results/2026-09-07-a2-certification-reject.md` — 別 attempt `t2022-20260828c` の改訂稿。
- `results/2026-09-04-a2-certification-reject.md` — 同 attempt の初版 (執筆材料には使わない)。

**A-6 単独の results 稿は存在しない。** 本稿は横断の表であり、A-6 の 1 attempt の一次資料全体からの
結果節を兼ねない。**[T-1998] 単独の results 稿も存在しない。** 本稿は [T-1998] の詳細材料を持つが、
同走行の一次資料全体 (8 genome 分の campaign 記録を含む) からの結果節ではない。

版の側の要約は `2026-09-14.md` の §8 の B-7 が持つ。同項は本稿と同じ 3 走行を数え、
「A-1 が定める横断実験の完了ではない」と限定している。
**本稿はその材料の詳細版である** — 生標本、ばらつきの定義差、実行 identity、正しさの記録形式の違い、
転記元の SHA-256 は版ではなく本稿が持つ。
