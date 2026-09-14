# B-7 の材料 — 現行環境・正式 protocol の 3 workload を退行込みで併記する (2026-09-14)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではない。** 同系列は append-only であり、2026-09-04 の稿、
2026-09-07 の `reject` の稿、2026-09-07 の `observed-positive` の稿、その英語稿は、いずれも 1 byte も
変えずに残る。本稿が足すのは、それらが 1 attempt ずつ書いている事実を **workload 横断で並べた表**である。

**本稿は B-7 の要件を満たしたという判定を行わない。** 2026-09-05 版 §8 の B-7 が書いている
「要件は満たされていない」を訂正するものでもない。増えたのは材料であって、充足の裁定ではない。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

results 系列は「1 file = 完走した 1 つの protocol または campaign 群の結果」を単位とする (D1631)。
本稿の単位は **事前登録の失敗条件 (e) が報告を求める「全 workload」の集合**である。すなわち
現行環境・正式 protocol で判定の出ている 3 workload — write-heavy (rr5)、balanced (rr50)、
read-heavy (rr95) — の 6 cell を 1 つの報告単位として扱う。

この 6 cell は **2 つの attempt に分かれて記録されている。**

| workload | attempt | 所属 study | 記録された outer status |
|---|---|---|---|
| rr5 (write-heavy) | `t2364-20260907b` | `paper-story-a2-certification` | `observed-positive` |
| rr50 (balanced) | `t2364-20260907b` | `paper-story-a2-certification` | `observed-positive` |
| rr95 (read-heavy) | `a6-20260908b` | `paper-story-a6-certification` | `reject` |

**この 2 attempt を統括する単一の正式実験は存在しない。** protocol instance も source commit も
投入日もホストも違う (§1.2)。本稿が作るのは事後の併記であり、3 workload を 1 走で測った横断実験の
結果ではない。3 行をプールした効果や、3 workload に共通の outer status は作らない。

### 0.2 書くもの

6 cell それぞれの genome、median throughput、生 5 標本、記録されたばらつき、集約 abort 率、
正しさの記録、所属 attempt の identity と protocol status。記録上共通の測定設定と、異なる実行 identity。
この併記が言わないことの一覧。

### 0.3 書かないもの

- **B-7 の要件を満たしたか否かの判定。** 本稿はそれを行わない。
- **研究として成功か失敗か、新規性があるかの宣告** (D12)。
- **`observed-positive` / `reject` を成否のラベルへ読み替えること。** どちらも protocol の出力である。
  A-2 の outer status は 2 workload の論理積、A-6 の outer status は 1 workload の判定である。
- **floor を超える差、有意差、attempt 間の再現性の判定** (§3 の限定 2)。
- **旧 attempt の判定の取り消し** (絶対規律 7、§3 の限定 8)。
- **D1645 の解除判定。** 本稿はこれを判定しない (§3 の限定 7)。
- **この効果が他の read 比率・他の workload・他の機体・他の CCBench pin へ転移するという主張。**

---

## 1. 条件

### 1.1 記録上共通の設定

両 attempt の権威 bytes が持つ policy (`policy_bytes_base64` を復号した `performance_common`) は、
性能側の設定として次を記録し、値は一致する。

| 項目 | 値 |
|---|---|
| スレッド数 | 48 |
| レコード数 | 1,000,000 |
| Zipf skew | 0.9 |
| read-modify-write | 無効 (`0`) |
| 1 トランザクションの最大 operation 数 | 10 |
| 実行時間 | 3 秒 |
| 反復数 | 5 |
| CCBench protocol | Silo |
| CCBench pin | `511c953` |
| perf | 不使用 |
| 性能の build | trace-disabled |

workload の違いは read 比率だけである (`ycsb_rratio` = 5 / 50 / 95)。
toolchain は両 attempt の記録が一致する — `x86_64-linux-gnu-gcc-11` / `x86_64-linux-gnu-g++-11`
(いずれも Ubuntu 11.4.0-1ubuntu1~22.04.3)、`cmake version 3.22.1`。

**列挙した性能設定・CCBench pin・toolchain は記録上共通である。実行 identity と環境全体の同一性を
意味しない。** 依存物全体、同時に走っていた他者の負荷、correctness 側の argv の独立観測までが
一致したという証拠ではない。

### 1.2 異なる実行 identity

| 項目 | A-2 (`t2364-20260907b`) | A-6 (`a6-20260908b`) |
|---|---|---|
| izanagi source commit | `31ec382a7841e188e46f93e8de4261c964facfb2` | `ae8a767eb60118c3f9791141603fa01ad4f28406` |
| protocol SHA-256 | `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4` | `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` |
| 公開された policy SHA-256 | `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` | `96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a` |
| scheduler request | rr5 `981476.nqsv` / rr50 `981477.nqsv` | rr95 `982234.nqsv` |
| ホスト | rr5 `bnode077` / rr50 `bnode085` | `bnode031` |
| 日付 | 2026-09-07 | 2026-09-08 |
| protocol schema | `paper-story-a2-certification-policy/v2` | `paper-story-a2-certification-policy/v2` |
| 結果 schema | `paper-story-a2-certification-result/v4` | `paper-story-a2-certification-result/v4`|

A-2 の 2 つの campaign は独立の request であり、campaign claim に記録された時刻 (UTC) は
rr5 が `2026-09-07T12:12:55.607184+00:00`、rr50 が `2026-09-07T12:12:55.388302+00:00` である。
**これは campaign の記録時刻であって、投入時刻として読み替えてはならない。**
A-6 の request は Created 01:28:55 / Started 01:29:06 / Ended 02:42:03 (JST、2026-09-08)、
Elapse 4382 秒と記録されている。

### 1.3 A-6 の policy bytes は測定後に 1 key だけ変わっている

A-6 の走行時の policy bytes の SHA-256 は
`8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8` で、公開された
`certification.json` が持つ値 (`96ed47d0…`) と異なる。attempt の記録は、差が
`tracked_destination` の 1 key だけであり、その key は `_protocol_preimage` に含まれないため
`protocol_sha256` は前後で同一であると書いている。

**本稿はこの前後不変性を独立に再計算していない。** 書けるのは「attempt の記録がそう記録している」
までである。したがって公開 policy hash を投入時の hash として表示しない。

### 1.4 adopted cell が patch の当たった木で build されたことの記録

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

---

## 2. 結果

### 2.1 主表 — 3 workload の利得と退行

**正の効果と負の効果を同じ表に置く。** 節を分けて退行を別扱いにしない。

| workload | attempt | adopted の静的 backoff | stock median (tps) | adopted median (tps) | 効果 | abort 率 stock → adopted | 所属 attempt の status |
|---|---|---:|---:|---:|---:|---|---|
| rr5 (write-heavy) | `t2364-20260907b` | 10 µs | 2,438,295 | 3,987,794 | **+63.5485%** | 0.7845 → 0.3833 | `observed-positive` |
| rr50 (balanced) | `t2364-20260907b` | 5 µs | 3,756,230 | 4,297,929 | **+14.4213%** | 0.685 → 0.4615 | `observed-positive` |
| rr95 (read-heavy) | `a6-20260908b` | 2 µs | 10,088,796 | 9,505,248 | **−5.7841%** | 0.1547 → 0.145 | `reject` |

stock は 3 workload とも `BACKOFF_FIXED=-1, BACK_OFF=0`、adopted は `BACK_OFF=1` に
workload ごとの `BACKOFF_FIXED` (10 / 5 / 2) を組み合わせた genome である。

効果は権威 bytes の `effects` フィールドの値であり、その定義は `adopted median / stock median − 1`
である。掲載した百分率は `100 × effects` を小数点以下 4 桁へ丸めたものである。
権威値は `rr5 = 0.6354846316791036`、`rr50 = 0.14421348000521794`、
`rr95 = -0.057841193339621455`。表の median を入力した比の再計算は 3 件とも権威値と一致した
(照合のための再計算であり、掲載値の権威は `effects` 側にある)。

**status は workload ごとの独立した判定値として新設していない。** 所属する attempt の outer status を
そのまま記した。A-2 の `observed-positive` は rr5 と rr50 の論理積であり、rr5 単独・rr50 単独の
status ではない。

**`observed-positive` と `reject` は、それぞれの protocol が出力した status である。** 研究としての
成功・失敗・新規性、あるいは B-7 の充足を表すラベルではない。

### 2.2 全 6 cell の生標本

各資料に記録された順序をそのまま保持して載せる。

| cell | 5 標本 (tps、記録順) |
|---|---|
| `rr5-stock` | 2601945, 2438295, 2395095, 2449052, 2429806 |
| `rr5-fixed10` | 4066753, 3987794, 4008033, 3983201, 3976744 |
| `rr50-stock` | 4003328, 3738171, 3756230, 3799369, 3745012 |
| `rr50-fixed5` | 4378620, 4279072, 4304483, 4297929, 4252521 |
| `rr95-stock` | 10365808, 10103030, 10029940, 10088796, 10073679 |
| `rr95-fixed2` | 9753031, 9587735, 9488225, 9494008, 9505248 |

A-2 の 4 cell は図 6 の provenance JSON が、A-6 の 2 cell は attempt の記録と事後解析が
同じ並びで持つ。A-6 は durable authority 側の raw JSON と campaign WAL でも同じ並びである。
**3 つの資料に同じ 30 標本があるという照合ではない** — A-2 の資料と A-6 の資料は別の cell を
収録しており、確かめたのは「各資料が記載順を保持している」ことである。

### 2.3 ばらつき — 定義が attempt 間で揃っていない

**2 つの attempt は別の定義でばらつきを記録している。共通の「CV」列へ押し込まない。**

| cell | 標本標準偏差 (tps、分母 n−1) | CV = 標本標準偏差 / 標本平均 | 母標準偏差 / median (分母 n) |
|---|---:|---:|---:|
| `rr5-stock` | 80348.29986564744 | 0.03262426529519532 | — |
| `rr5-fixed10` | 36711.889579535404 | 0.0091676473320761 | — |
| `rr50-stock` | 111523.9230053355 | 0.02928349930898821 | — |
| `rr50-fixed5` | 47079.31931857129 | 0.010942253518241333 | — |
| `rr95-stock` | — | — | 1.18% |
| `rr95-fixed2` | — | — | 1.06% |

「—」は**その定義の値を本稿では掲載しない**という意味であり、ゼロではない。生標本 (§2.2) は
6 cell すべてについて載せてあるので、必要なら任意の定義で計算できる。

**本稿は定義を揃え直さない。** 揃えるための再計算は新しい測定ではないが、どの定義を代表にするかの
選択を含むため、一次資料の転記でも機械射影でもなくなる。D12 は事実層を機械コンパイルし、
判定を事実として焼き込まないことを求めている。そこで既存の定義と値をそのまま露出させ、
統一した指標を新設しない方を採った。将来の再計算を禁じる判断ではない。

A-2 側の 95% 信頼区間の半幅は `rr5-stock` 99765.59126005495、`rr5-fixed10` 45583.83159694112、
`rr50-stock` 138475.2401341739、`rr50-fixed5` 58456.69585780905 と記録されている。
**平均の信頼区間は標本を記述するものであって、効果・判定・median の信頼区間ではない。**
本稿は有意性の判定を行わない。

### 2.4 正しさ — 6 cell すべて certified、ただし別走行の記録である

6 cell すべての `correctness.status` が `certified` で、`disposition` は `pass`、
legacy の反復は 1 回、performance 条件側の反復は 5 回と記録されている。

**これは性能の認証ではない。** 正しさは trace-enabled の別走行から来ており、性能値は
trace-disabled の走行である (絶対規律 1)。`correctness` の中に `performance` という名の
フィールドがあるが、これは「performance 条件で行った正しさ検査」の意味であって性能の判定ではない。

記録された独立観測の限界は 2 つある。**correctness の実行 argv は既存 pipeline では独立に
記録されていない。** また **workload の対応づけは campaign lock と pipeline constructor による
もので、独立した argv の観測ではない。** 加えて A-2 側の正しさの証拠は、限定 L01 により
point-key trace に限られる。

**退行した rr95 の adopted cell も certified である。** 「正しさを保ったまま性能で負けた」と
書けるのは、検査された trace の範囲と観測された median についてであり、正しさの合格は
性能の優越の十分条件ではない。逆に、性能で勝ったことが正しさの証拠になることもない。

---

## 3. 限定 — この併記が言わないこと

1. **同一 variant を他 workload へ当てた退行の比較ではない。** adopted の genome は workload ごとに
   異なる (rr5 = fixed 10 µs、rr50 = fixed 5 µs、rr95 = fixed 2 µs)。rr95 の負の効果は、rr5 で
   勝った fixed 10 µs を rr95 へ当てた結果ではない。**本表は workload 別に指定された採用構成と
   各 stock の比較であり、同一 variant の workload 間退行を検証したものではない。**

2. **floor を超える差は 3 workload とも判定していない。** 両 attempt の `a4_noise_floor_status` は
   `open` である。**rr5 / rr50 では正、rr95 では負の中央値効果を記録した。正負いずれについても、
   between-run floor を超える差、有意差、別 attempt での再現性は本表から判定しない。**
   §2.3 のばらつきは within-attempt の記述であり、between-run floor の代用にしない。

3. **事前登録の失敗条件 (e) の前件が成立したとは言えない。** (e) は「target workload では勝つが
   他の workload で **floor 超の**退行がある」を前件とする。床値が未確定である以上、前件の成立は
   立証できない。**同時に「発火しない」と確定したわけでもない。** 選択的報告を禁じる (e) の趣旨に
   従い、床値の判定を待たずに正負をそろえて載せた。載せたこと自体を義務の履行として宣告しない。

4. **B-7 の要件を満たすために必要な測定の形は、本稿の材料とは別である。** 要件の形を言葉にすると
   「対象 workload で評価する variant を固定し、その同一 variant と対応する stock を対象 workload と
   他 workload の全件で比較する。正しさは別の trace-enabled 走行、性能は trace-disabled 走行とし、
   between-run floor を評価できる反復と束縛された条件のもとで正負の差を報告する」となる。
   **本稿はその測定を実施しておらず、実施を要求もしない。** 形の言語化だけを残す。

5. **abort 率は cell あたり 1 点の集約値である。** 定義は `aborts / (aborts + commits)`。
   標本ごとの率でも、信頼区間を持つ量でもなく、因果の機序を主張する量でもない。記述的な
   先行指標として読む。

6. **2 attempt を統括する単一の正式実験は存在しない。** protocol instance、source commit、
   投入日、ホストが違う (§1.2)。3 行をプールした効果も、共通の outer status も作っていない。

7. **D1645 の解除条件を満たすかどうかは本稿の対象外であり、未了として扱う。**
   `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと（stale 注記）」節は、
   A-2 の新 attempt の統制稿について「この統制稿が D1645 の条件を満たすかどうかを判定していない」と
   書き、D1645 による A-2 の結論の除外を解除せずそのまま有効としている。**本稿も判定しない。**
   §1.4 の `src_token` の記録を挙げることは、解除の裁定そのものではない。
   旧 `figures/fig5_a2_certification_reject` の用途制限は、2026-09-11 の追補により
   **期限なし**である (`figures/README.md` の該当節が正本)。新 attempt の取得によって解除されない。

8. **旧 attempt の判定を取り消すものではない。** attempt `t2022-20260828c` の `reject` は、
   patch の当たっていない木で `BACK_OFF` の有効/無効を測った別の事実として記録に残る
   (絶対規律 7、D1645)。本稿の値と前後比較として読んではならない。

9. **最小性も一般性も主張しない。** 両 attempt の `global_minimality_established` は `false`、
   `smallest_observed_sufficient_in_this_two_point_protocol` は `null` である。
   `−5.7841%` は read-heavy のこの 1 点 (rratio 95 / 48 スレッド / zipf 0.9 / extime 3) の値で
   あって read-heavy 一般の値ではない。他の read 比率・他の機体・他の pin へ外挿しない。

10. **条件関門について言えるのは記録までである。** 両 attempt は canonical な admission record を
    cell 分束縛しているが、元の supply / meaning records は成果物に保存されていない。
    「関門を実施し通過した」ではなく「そう記録された受領証が束縛されている」と書く。

11. **compile-out の証拠は source 経由である。** 両 attempt の
    `compile_out_evidence_scope` は「source-routed evidence; artifact hashes are not standalone
    compile-out proof」と記録する。成果物の hash 単独では trace のコンパイル除去の証明にならない。

---

## 4. 一次資料

### 4.1 権威 bytes と転記元 (repo 内、tracked)

| 資料 | path | SHA-256 |
|---|---|---|
| A-2 認証成果物 | `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` | `e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671` |
| A-6 認証成果物 | `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json` | `3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab` |
| A-2 図 6 の provenance | `docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json` | `760b899b331719ff947f3f8df591e56f57f956f97c3d2debb20d392d427299e6` |
| A-6 attempt の記録 | `output/insights/2026-09-08/t2411-a6-readheavy-submitted/README.md` | `8a00ba625bb3f681518275cc9873f3d555b370b5c341f7e51852394157839410` |
| A-6 退行の事後解析 | `output/insights/2026-09-08/t2430-a6-readheavy-mechanism/README.md` | `fb38eaa68cb0d2d0681b9d3f8ace33d6b103608957c73c486182bc67a8ca881b` |

A-2 の `certification.json` の SHA-256 は、同じ dir の `artifact-manifest.json` の
`files["certification.json"]` と `COMPLETE.json` の `certification_sha256` にも同じ値が
記録されている。A-6 についても同様である。

### 4.2 値の出所

| 掲載値 | 出所 |
|---|---|
| median、genome、role、workload、正しさ、`src_token`、`source_binding_status` | 両 `certification.json` の `cells[]` |
| 効果 | 両 `certification.json` の `effects` |
| 床値状態、最小性、compile-out の射程、独立観測の限界 | 両 `certification.json` の `a4_noise_floor_status`、`global_minimality_established`、`smallest_observed_sufficient_in_this_two_point_protocol`、`compile_out_evidence_scope`、`independent_observation_limits` |
| 共通の測定設定 | 両 `certification.json` の `policy_bytes_base64` を復号した `performance_common` |
| rr5 / rr50 の生標本・標本標準偏差・CI 半幅・CV・abort 率・toolchain | 図 6 の provenance JSON の `cells[]` と `measurement_conditions` |
| rr95 の生標本と母標準偏差 / median | A-6 attempt の記録の「結論」節 (事後解析 §1 にも同値) |
| rr95 の abort 率 (0.1547 / 0.145) | campaign WAL の `stage=bench_done` の `payload.leading_indicators.abort_rate` (事後解析 §1 に転記されている)。**attempt の記録 README 自体には掲載がない。** raw JSON のトップレベル `abort` は `null` である |
| rr95 のホストと request の時刻 | A-6 attempt の記録の「実行 identity」節、事後解析 §1 |
| 事前登録の失敗条件 (e) | `docs/phase3-main-experiment.md` の「失敗条件 (何が出たら negative か、正直に)」節 |
| B-7 の項目本文 | `docs/paper-story/2026-09-05.md` の §8 |

### 4.3 durable authority (repo 外)

A-6 の生標本・abort 率・toolchain は次の measurements root にある原記録でも照合できる。
**これは repo の tracked file ではない。**

- `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/raw/rr95-stock.json`
  (SHA-256 `d0a47903ee33f24465c3e934cb59f01d07056416d9486750f880208b716eec4d`)
- `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/raw/rr95-fixed2.json`
  (SHA-256 `91173824743d83e89971eb3ec94d32262fe2e895667d1d3f4e7e547e862ba261`)
- 同 attempt の campaign WAL (SHA-256 `36d11c6bf461c9acf6d2ede24ba13549005d0552bac87950d0df4d95da55eaeb`。
  raw JSON の `campaign_evidence.wal_sha256` に束縛されている値と一致する)

A-2 の durable authority は、図 6 の provenance JSON の `external_inputs` が root 相対 path と
SHA-256 で 12 件記録している。

### 4.4 同じ結果についての既存の稿

- `results/2026-09-07-a2-certification-observed-positive.md` — attempt `t2364-20260907b` の
  結果節 (rr5 / rr50 の 4 cell、図 6、限定 6 件)。
- `results/2026-09-09-a2-certification-observed-positive-en.md` — 直上の英語稿。
- `results/2026-09-07-a2-certification-reject.md` — 別 attempt `t2022-20260828c` の改訂稿。
- `results/2026-09-04-a2-certification-reject.md` — 同 attempt の初版 (執筆材料には使わない)。

**A-6 の結果についての単独の results 稿は存在しない。** 本稿は A-6 単独の結果節を兼ねない —
本稿が書くのは横断の表であり、A-6 の 1 attempt の一次資料全体からの結果節ではない。
