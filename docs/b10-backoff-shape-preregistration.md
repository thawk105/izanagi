# B-10 待ち方 / 待ち量の直交切り分け — 事前登録

論文 `docs/paper-story/2026-08-26.md` §8 の **B-10「機序説明の帯域外への拡張」**のうち、
**「待ち方と待ち量の直交切り分け」** 1 項目の事前登録である。
B-10 の他の 3 項目 (過抑制域の機序、ピーク位置の再現、balanced workload の profile) は
本書の対象外であり、**未取得のまま残る**。

## 0. 本書の版と改訂履歴

**本書は v4 であり、発効している。** §5 の `physical_residual.values` に実測値が入っており、
`FILL_FROM_PROBE_RESULT…` の placeholder は残っていない。

### v3 (placeholder 版) からの改訂

v3 は 3 形 (`constant` / `symmetric-modulo` / `binary`) の grid を登録し、§5 を placeholder のまま
commit して、物理残差 probe の実測値を転記した版を発効版とする手順を定めていた。
その probe を走らせた結果、**`binary` の 4 cell が事前登録済みの上限 1.0% を超えた**。
上限を緩めないという規律に従い、v3 は発効しないまま止まった。

v4 はこの probe の結果を**開示したうえで**、上限を満たす grid へ改訂したものである。
**この改訂は事前登録ではない。probe の結果を見た後に行った改訂 (probe-informed amendment) である。**
本書が前向きに固定したと主張できるのは、§4 の 3 段の順序で書いたとおり、
**shape grid の throughput を一度も観測していない時点で §4 の R1〜R5 と §5 の spec を固定したこと**だけである。

改訂の内容は次のとおり。

- 登録 grid の形を 3 → 2 (`constant`、`symmetric-modulo`) にした。判定は §2 の R1 に従う。
- `schema_version` を `/v3` → `/v4` にした。受理集合が変わるので v3 の文書は受理しない。
- Holm の族を 6 → 3 にした。block あたりの実行点を 21 → 15 にした。
- `physical_residual.values` を 18 行 → 12 行にし、既存 probe の該当行を転記した。
- `physical_residual.provenance` を新設し、転記元 probe の identity と抽出規則を固定した。
- `registration_rules` を新設し、R1〜R5 を機械可読に固定した。

**変えなかったもの。** μ grid、workload の動作点、block 数と実行順の生成規則、threads、extime、
反復数、α、permutation、信頼区間、欠測規則、曝露規則、等価域 ±3.0%、判定手続きの骨格、
C++ の hole line、patch、`formula_sha256`、`patch_sha256`。

### D1270 との対応

D1270 (2026-08-29) は「上限は据え置く」「probe の 18 cell を開示した新しい日付版の事前登録を作ってから
正式投入する」「凍結物は上書きしない」と定めた。本 v4 がその新しい版である。対応は次のとおり。

- **上限は据え置いた。** `maximum_absolute_deviation_pct_exclusive` は 1.0 のままである。
- **18 cell を全件開示した。** §4.1 に `binary` の失敗 4 cell を含む全値がある。
- **版は commit で識別する。** driver は canonical path
  `docs/b10-backoff-shape-preregistration.md` を固定して束縛するので (D1058)、
  別 path の日付入り file を新設せず、**同じ canonical path 上の新しい版**として作った。
  版の日付と改訂内容は本節に、束縛は commit hash に持たせる。
- **凍結物は 1 バイトも上書きしていない。** v3 の bytes は改訂前の commit に残る。
  probe 成果物 (`output/insights/2026-08-28_t1905-b10-backoff-shape-run/`) も変更していない。
  v3 はそもそも placeholder のまま発効しておらず、v3 を束縛した実走成果物は存在しない。

### 発効と本走の手順

- **本走 (`build` / `verify` / `perf`) は本書 v4 を含む commit を指して起動する。**
- **本走成果物は発効版の commit hash を記録する。記録が無い実走は事前登録された実験として扱わない。**
- 発効後の変更は旧版を Git 履歴に残したまま新しい commit で行い、変更理由と変更時点を本書へ明記する。
  **結果 commit より後に書かれた変更は事前登録として数えない。**

## 1. 事前登録の効力とその限界

- ancestry が証明するのは「その bytes の文書がその時点に存在したこと」だけである。
  したがって driver は、文書の blob SHA・その commit・patch SHA・式 SHA・
  spec SHA・解析コード SHA を campaign lock と各 `BUILD_START` とブロック記録へ束縛し、
  束縛の無い / 食い違う既存 WAL への resume を拒否する。
- **「登録前に一度も性能を見ていない」と機械的に言えるのは formal driver 経路についてだけである。**
  driver を経由しない手動実行を repo 内の preflight で封じることはできない。
  一回限りの capability token による封鎖は本書の範囲外とし、裁定へ送った。
- **本書の場合、上の「登録前に見ていない」が指すのは shape grid の throughput だけである。**
  物理残差 probe の 18 cell は登録前に見ている。§4 で全件開示する。

## 2. 何を分離する実験か

CCBench (silo) の backoff は、abort のたびに `_mm_pause()` の busy spin を
`clocks_per_us × now_backoff` サイクル回すだけの機構である。すなわち
**`now_backoff` が「待ち量」、spin の回し方が「待ち方」**である。

既存の静的 backoff sweep は `now_backoff` を定数に固定して量だけを振っており、
待ち方は「毎回きっかり同じ長さ待つ」1 種類に固定されていた。
したがって「backoff が効く」とは言えても、効いているのが**待つ総量**なのか
**待ち方 (retry の時間的なばらけ方)** なのかを分離できない。

本実験は、**指示する待ち量の平均を μ に固定したまま、待ち方 (ばらつき) を 2 段階に変える**。

| 形 | 指示値 | 構成上の平均 | ばらつき |
|---|---|---|---|
| `constant` | 常に μ | μ | 0 |
| `symmetric-modulo` | μ/2 〜 3μ/2 | μ | 中 |

**どちらの形も待ち量 0 を指示しない** (最小は μ/2)。これは待機ループが 0 を指示されても
最低 1 回は `_mm_pause()` と `rdtscp()` を通るため、0 を含む形だと名目平均と物理平均が
形ごとに違ってずれるからである。半幅にすることでこのずれを構造的に小さくし、
残る差は §5 の実測で上界を押さえる。

### R1 — 形の登録可否を決める記号導出の基準

指示待ち量 `X` の期待値が μ からどれだけずれるかを、撹拌語の最上位 bit `H` (`p = P(H = 1)`) と
補助 draw `r` の条件付き期待値を使って**記号で**導く。導出には
`E[r | H = 0] = E[r | H = 1] = m` を仮定として置く (この仮定は本書が置いた仮定であり、実測していない)。

- `constant` — 指示値は常に μ。`E[X] − μ = 0`。`p` を含まない。
- `symmetric-modulo` — 指示値は `(μ + offset)/2`、`offset` は `H` が立てば `2μ − r`、立たなければ `r`。
  よって `E[X] − μ = (p − 1/2)(μ − m)`。`(p − 1/2)` の係数が `(μ − m)` へ**抑制される**。
  `r` の剰余分布が `[0, 2μ]` 上でほぼ一様なら `m ≈ μ` であり、係数は小さい。
- `binary` — 指示値は `(μ + offset)/2`、`offset ∈ {0, 2μ}` を `H` が選ぶ。
  よって `E[X] − μ = μ(p − 1/2)`。`(p − 1/2)` の係数が μ そのもので、**抑制されない**。

**R1: 登録 grid に入れるのは、`(p − 1/2)` の係数が μ そのものにならない形だけとする。**
この判定は式からのみ行い、probe の実測値も `p` の推定値も参照しない。
判定の粒度は**形の単位**であり、cell の単位では判定しない。

**R1 が主張しないこと。** `p ≠ 1/2` であるとは主張しない。物理残差 probe は待機ループの
経過サイクルだけを保存しており、最上位 bit の出現数を記録していない。したがって `p` は測っていない。
主張するのは次の 2 点だけである。

- (a) `binary` の平均は `(p − 1/2)` のずれに対して無防備である (式から導ける)。
- (b) `binary` の実現平均は 4 cell で上限 1.0% を超えた (§4 の実測)。

(a) と (b) は独立の根拠であり、(b) の原因が (a) であると認証するものではない。

**R1 の射程 (binary の名指しではないこと)。** R1 を満たす形の例は、`constant`、
平均 0 の連続変数 `Z` を足す `X = μ + Z`、2 回の指示の和を常に `2μ` にする antithetic 対である。
R1 を満たさない形の例は、平均 `μ/2` と `3μ/2` の 2 群を偏りうる 1 bit で混ぜる形**全般**であり、
`binary` はその 1 例にすぎない。

### 登録しない形の開示

`binary` (μ/2 または 3μ/2 を最上位 bit で半々に選ぶ形) は v3 で登録していた。
v4 では R1 により登録しない。式と符号 (`shape_code = 2`) は C++ の hole line に残るが、
driver はこれを発行も受理もしない。**したがって本実験は `binary` を測らない。**
2 形へ減らしたことで失う主張は §3 と §9 に書く。

## 3. 何を主張し、何を主張しないか

**書ける主張:**

- 48 スレッドの Silo / YCSB 3 workload、μ = 2〜100 µs の登録 grid において、
  **`constant` と `symmetric-modulo` という 2 つの特定の実装の間で**、
  指示待ち量の構成上の平均を μ に揃え、合成ループでの物理残差を 1.0% 未満に押さえた条件のもとで、
  待ち方の違いが throughput を動かすかを、事前登録した手続きで検定した。
- 有意な族については、方向・効果量・信頼区間を**この contrast に限って**限定付きで述べる。
- 非有意なら「**この設計では検出しなかった**」とだけ述べる。

**書けない主張:**

- 物理的な実待機時間の平均を完全に同一化した (§5 の実測上界までしか言えない)。
- 差の機序が脱同期だけである (総待ち量 = 呼び出し回数 × μ も同時に動く)。
- **ばらつき全般の効果を測った。** 測ったのは 2 点だけであり、ばらつきの用量反応は取っていない。
- **待ち方と待ち量の直交切り分けを一般に閉じた。** 閉じたのはこの 1 contrast の範囲だけである。
- 過抑制域の機序、ピーク位置の再現、balanced の profile を閉じた。
- 非有意だから待ち量だけで全部説明できる。
- 事前に定めた検出力の範囲内である (**検出力の保証はしない**。§6)。
- **`binary` を含む 3 水準の ladder について何かを言った。** `binary` は測っていない。

## 4. 開示した事実と、固定した規則

本節は、**すでに見ている事実**と、**それを見た後に行った改訂**と、**前向きに固定した規則**を
この順序で分けて書く。順序を入れ替えて書いてはならない。

### 4.1 観測済みの事実 (1) — 物理残差 probe の全 18 cell

v3 の placeholder 版 commit `1549bd92794d72e05aeafe5903568f7d9023614d` を指して走らせた
物理残差 probe の全値である。`clocks_per_us` = 2100、cell あたり 100,000 回呼び出し。
`realized_mean_cycles` は待機ループの実経過サイクルの平均、`commanded_mean_cycles` は `μ × clocks_per_us`。

| shape | μ (µs) | realized_mean_cycles | commanded_mean_cycles | deviation_pct |
|---|---:|---:|---:|---:|
| constant | 2 | 4223.59116 | 4200 | 0.5616942857142844 |
| symmetric-modulo | 2 | 4218.32476 | 4200 | 0.43630380952381964 |
| binary | 2 | 4382.71288 | 4200 | 4.350306666666667 |
| constant | 5 | 10538.38268 | 10500 | 0.3655493333333392 |
| symmetric-modulo | 5 | 10544.10586 | 10500 | 0.42005580952380633 |
| binary | 5 | 10742.28884 | 10500 | 2.307512761904755 |
| constant | 10 | 21035.41464 | 21000 | 0.16864114285713835 |
| symmetric-modulo | 10 | 21047.27694 | 21000 | 0.22512828571428448 |
| binary | 10 | 21313.97052 | 21000 | 1.4950977142857091 |
| constant | 25 | 52530.59194 | 52500 | 0.05827036190475891 |
| symmetric-modulo | 25 | 52275.76334 | 52500 | -0.427117447619052 |
| binary | 25 | 52652.63058 | 52500 | 0.2907249142857091 |
| constant | 50 | 105021.8346 | 105000 | 0.020794857142859006 |
| symmetric-modulo | 50 | 104692.05524 | 105000 | -0.29328072380952236 |
| binary | 50 | 106971.61978 | 105000 | 1.8777331238095178 |
| constant | 100 | 210029.9768 | 210000 | 0.014274666666668573 |
| symmetric-modulo | 100 | 210487.20626 | 210000 | 0.23200298095238395 |
| binary | 100 | 209764.33834 | 210000 | -0.11221983809524404 |

上限は 1.0% の exclusive であり、`binary` の μ = 2 / 5 / 10 / 50 の 4 cell がこれを超えた。
最大は `binary` / μ = 2 の 4.350306666666667% である。

**この probe が測っていないもの。** 測ったのは合成した待機ループを連続で回したときの経過サイクルだけである。
本走 (実 workload) での `start = rdtscp()` の列、要求待ち量の分布、スレッド間の同時値率は測っていない。
最上位 bit の出現数も記録していない。したがって本 probe から `p` の値を読むことはできない。

**「呼び出し回数を増やせば直る」かどうかについて。** 最上位 bit が公平で独立だと仮定したときの
`binary` の平均の相対標準誤差は、100,000 回で `1 / (2√100000)` = 0.158114% である。
観測した 4.350306666666667% はその約 27.5 倍にあたる。**これは理想化した健全性検査にすぎない。**
実測値には待機ループの固定オーバーヘッド、実行時の雑音、bit の非独立性が混ざっており、
Bernoulli の標準誤差だけで標準化した検定統計量ではない。
本書はこの数値を「呼び出し回数を増やしても直らないことの決定的な証拠」としては使わない。

### 4.2 観測済みの事実 (2) — 登録前から既知だった材料

本実験は**既知の μ grid 上での前向きな形の拡張であり、登録追試である**。
着手前に次を閲覧していた。数値は本実験の材料に流用しない。

| 材料 | SHA-256 | 登録前に既知だった内容 |
|---|---|---|
| `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl` | `9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926` | 一定 10 µs が backoff 無しの +38.3288% |
| `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl` | `8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c` | 一定 5 µs が backoff 無しの +11.2682% |
| `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl` | `c74d5837a4facd071704a515f905d1d638463878850661cf217b96cd694774dc` | 最良でも backoff 無しの -6.6430% |
| `output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/runs/wal.jsonl` | `7afeac668c8ba678f651ef9cab33f95fb87879f0034c138065b243913bb1dc92` | 量の再測材料 |
| `output/campaigns/backoff-repro-silo-write-heavy-repro-181607af/runs/wal.jsonl` | `ea6f9e250960f1bccac3c6c8d5b5029bebebf01eee607e50493e8d6b2aa6f103` | 量の再測材料 |
| `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` | `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` | D15 の下限基準で選択、records 1,000,000、作業集合 / L3 = 4.9275、**miss 率は飽和していない** |
| `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json` | `23c024e467559b238b58ef9c32c144f78d23cb48ad7aafd6bbc02cd108842ce7` | read-heavy の参考 floor 0.22% |
| `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json` | `200ab13614344769bbceaa4f7efe8c4411c4f6d764b3a5c036b77036498b9a11` | write-heavy の参考 floor 0.67% |
| `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json` | `4040eda140572ea0f79d1b16854fc1db84ed18b2de13d7eacdde25ce45971dc8` | balanced の参考 floor 1.07% |
| `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json` | `a6d1657885b2c855a797b71b8565e6c21d282bfb62c94395884b4ba1eac555c5` | read-heavy の参考 floor 0.11% (別環境) |

**レコード数は 1,000,000 とする。** 根拠は上記 calibration 成果物であり、
「cache miss 率が飽和した点」**ではない** (miss 率は単調上昇で飽和しない)。
D15 の下限基準に従い、作業集合が L3 の 4.93 倍になる最小点を採っている。

**曝露の最小値 10,000 回の根拠**も既存の実測である。2026-08-25 の Pegasus 計測で
`BACKOFF_FIXED=10` / write-heavy は 3 秒間に 984,942 回 abort している。
10,000 はその 2 桁下であり、backoff 経路がほとんど使われていないセルだけを弾く。

### 4.3 観測済みの事実 (3) — A-2 実走の逆転

2026-08-28 の A-2 fan-out 4-cell certification 実走
(`output/insights/2026-08-28_t2022-a2-certification-run/README.md`) で、
採用した静的 backoff は stock を大きく下回った。

| workload | stock median TPS | adopted median TPS | effect |
|---|---:|---:|---:|
| rr5 | 2,527,542 | 1,355,011 (`fixed10`) | -46.3902% |
| rr50 | 3,662,448 | 1,248,603 (`fixed5`) | -65.9080% |

4 cell はすべて correctness certified、anomaly 0、performance status は 4 cell とも `complete`。
outer certification status は `reject` である。

**この材料の役割を次に固定する。** A-2 は本書にとって
**動機および先行証拠であり、パラメータ選択の根拠ではない** (`role = motivation-and-prior-evidence; not parameter-selection`)。
A-2 の数値を根拠に μ grid、workload、閾値、等価域、判定手続きを動かすことを禁じる。
本書の結果を A-2 の逆転の説明として書くことも禁じる。
**A-2 の逆転が属するのは B-10 の「過抑制域の機序」であり、本書の対象は「待ち方 / 待ち量の直交切り分け」である。**
両者を同じ結論へ束ねてはならない。

### 4.4 事後改訂 (probe の結果を見た後に行ったこと)

4.1 の 4 cell の失敗を見た後で、次を行った。**ここは前向きな固定ではない。**

1. §2 の R1 を定式化した。
2. R1 を適用して `binary` を登録 grid から外し、2 形 grid へ改訂した。
3. それに伴う派生量 (Holm 族 6→3、block あたり 21→15、residual 表 18→12 行、schema v3→v4) を直した。

**したがって本書は「`binary` を落とす判断が事前登録である」とは主張しない。**
この改訂は probe-informed amendment である。

### 4.5 前向きに固定した規則 (R1〜R5)

**shape grid の throughput を一度も観測していない時点で**、次を固定した。
機械可読な形は §5 の `registration_rules` にある。

- **R1** — 形の登録可否は §2 の記号導出の基準で決める。判定は式からのみ行い、実測値を参照しない。
  除外できる粒度は形の単位だけである。
- **R2** — μ grid、workload の動作点、block 数と実行順の生成規則、threads、extime、反復数、
  cell の切り方は変更しない。
- **R3** — `maximum_absolute_deviation_pct_exclusive` は 1.0 に据え置く。登録 12 cell の**全件**に適用する。
  1 件でも上限以上なら本走に入らない。cell 単位の免除・警告化・flag・環境変数による逃がし道を作らない。
- **R4** — 実測 deviation の値を根拠に cell を落とす規則を作らない。除外できるのは R1 による形の単位だけである。
- **R5** — throughput の判定手続き (α、Holm、permutation、信頼区間、等価域 ±3.0%、欠測、曝露) を
  変更しない。A-2 を根拠に動かさない。

## 5. 機械可読 spec

以下の JSON が判定規則の**正本**である。driver はこれを全件 parse し、
コードの定数ではなくこの spec を引数として解析を行う。
`maximum_absolute_deviation_pct_exclusive` の 1.0 は**実測を見る前に固定した値**であり、
probe の結果を見て変更していない。

<!-- IZANAGI-B10-SPEC-BEGIN -->
```json
{
  "schema_version": "izanagi-b10-backoff-shape-preregistration/v4",
  "artifacts": {
    "patch_sha256": "36cd974c56c6f103d894a53048ac734d9859def266c05898d3794d2c48470832",
    "formula_sha256": "5b3d8deefed35d05597891592d7af442c96b2fa094cdebc8376b2e9bc9cd7662"
  },
  "registration_rules": {
    "shape_eligibility_criterion": "symbolic-mean-deviation-has-no-unsuppressed-mu-coefficient-on-mixer-high-bit-frequency",
    "shape_eligibility_evidence": "formula-only-not-observed-deviation",
    "shape_exclusion_granularity": "whole-shape-only",
    "means_us_and_cell_partition": "unchanged",
    "physical_residual_cell_policy": "evaluate-all-registered-cells-without-exemption",
    "throughput_decision_procedure": "unchanged-and-independent-of-a2",
    "a2_material_role": "motivation-and-prior-evidence-not-parameter-selection",
    "shape_rule_formulation_timing": "after-physical-residual-probe-before-shape-grid-throughput"
  },
  "grid": {
    "means_us": [
      2,
      5,
      10,
      25,
      50,
      100
    ],
    "shapes": [
      {
        "name": "constant",
        "code": 0,
        "support": "mu"
      },
      {
        "name": "symmetric-modulo",
        "code": 1,
        "support": "closed-half-width-mu/2-through-3mu/2"
      }
    ],
    "encoding": "BACKOFF_FIXED=shape_code*1000+mu",
    "references": [
      {
        "name": "none",
        "back_off": 0,
        "backoff_fixed": -1
      },
      {
        "name": "adaptive",
        "back_off": 1,
        "backoff_fixed": -1
      },
      {
        "name": "zero-loop",
        "back_off": 1,
        "backoff_fixed": 0
      }
    ]
  },
  "blocks": {
    "count": 3,
    "ids": [
      "block-1",
      "block-2",
      "block-3"
    ],
    "run_order": {
      "block-1": [
        "none",
        "adaptive",
        "zero-loop",
        "constant-mu2",
        "symmetric-modulo-mu2",
        "symmetric-modulo-mu5",
        "constant-mu5",
        "constant-mu10",
        "symmetric-modulo-mu10",
        "symmetric-modulo-mu25",
        "constant-mu25",
        "constant-mu50",
        "symmetric-modulo-mu50",
        "symmetric-modulo-mu100",
        "constant-mu100"
      ],
      "block-2": [
        "adaptive",
        "zero-loop",
        "none",
        "symmetric-modulo-mu2",
        "constant-mu2",
        "constant-mu5",
        "symmetric-modulo-mu5",
        "symmetric-modulo-mu10",
        "constant-mu10",
        "constant-mu25",
        "symmetric-modulo-mu25",
        "symmetric-modulo-mu50",
        "constant-mu50",
        "constant-mu100",
        "symmetric-modulo-mu100"
      ],
      "block-3": [
        "zero-loop",
        "none",
        "adaptive",
        "constant-mu2",
        "symmetric-modulo-mu2",
        "symmetric-modulo-mu5",
        "constant-mu5",
        "constant-mu10",
        "symmetric-modulo-mu10",
        "symmetric-modulo-mu25",
        "constant-mu25",
        "constant-mu50",
        "symmetric-modulo-mu50",
        "symmetric-modulo-mu100",
        "constant-mu100"
      ]
    }
  },
  "workloads": [
    {
      "name": "write-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "5",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10"
    },
    {
      "name": "balanced",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "50",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10"
    },
    {
      "name": "read-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "95",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10"
    }
  ],
  "execution": {
    "threads": 48,
    "extime_s": 3,
    "performance_reps": 5,
    "correctness_reps": 5,
    "correctness_mode": "legacy+performance",
    "screening": false
  },
  "analysis": {
    "alpha": 0.05,
    "holm_families": [
      {
        "workload": "write-heavy",
        "shape": "symmetric-modulo"
      },
      {
        "workload": "balanced",
        "shape": "symmetric-modulo"
      },
      {
        "workload": "read-heavy",
        "shape": "symmetric-modulo"
      }
    ],
    "permutation": {
      "method": "exact-sign-flip",
      "sided": "two-sided",
      "statistic": "absolute-sum-paired-relative-effect",
      "enumeration": "all-2^18",
      "pairs_per_family": 18
    },
    "confidence_interval": {
      "method": "student-t-paired-block-mean",
      "confidence_level": 0.95,
      "degrees_of_freedom": 2,
      "critical_value": 4.302652729911275
    },
    "missingness": {
      "conditions": [
        "missing",
        "performance-error",
        "correctness-not-certified",
        "unstable",
        "underexposed"
      ],
      "pair_action": "invalidate-entire-family",
      "family_action": "indeterminate",
      "indeterminate_pvalue": 1.0
    },
    "exposure": {
      "metric": "sum-performance-rep-abort-counts",
      "minimum_calls_per_cell": 10000,
      "below_minimum_action": "indeterminate"
    },
    "equivalence_margin_pct": 3.0,
    "decision_procedure": [
      "construct-all-18-within-block-paired-relative-effects",
      "mark-family-indeterminate-on-any-unusable-pair",
      "enumerate-two-sided-sign-flip-pvalue-for-each-testable-family",
      "set-indeterminate-family-pvalue-to-1",
      "holm-adjust-all-three-families",
      "different-iff-testable-and-holm-p-less-than-or-equal-alpha",
      "otherwise-not-detected",
      "report-all-cell-effects-confidence-intervals-and-equivalence-relations"
    ]
  },
  "physical_residual": {
    "measurement": "realized-backoff-loop-cycles",
    "maximum_absolute_deviation_pct_exclusive": 1.0,
    "provenance": {
      "probe_schema_version": "izanagi-b10-backoff-shape-probe/v1",
      "probe_result_sha256": "6e7d8ed7d27be091ce94de4b85ac61a50e99d97167e75c4328e8a54982224bc3",
      "probe_source_commit": "8df4fa25da01311e887336b6f454f6d33ec28a2c",
      "placeholder_preregistration_commit": "1549bd92794d72e05aeafe5903568f7d9023614d",
      "probe_request_id": "953543.nqsv",
      "probe_nonce": "6f8cea40fcf2193f4e4157e9c89adde1",
      "submission_receipt_sha256": "782b25fc0aecf78d0aa9dfa36ef2d036c777eb171b3ebe654405b7364dc7eb54",
      "probe_host": "bnode142",
      "probe_measured_at_utc": "2026-08-27T16:26:55.628726Z",
      "probe_clocks_per_us": 2100,
      "probe_calls_per_cell": 100000,
      "probe_cells_total": 18,
      "extraction_rule": "select-probe-rows-whose-shape-is-in-the-registered-grid"
    },
    "values": [
      {
        "shape": "constant",
        "mean_us": 2,
        "realized_mean_cycles": 4223.59116,
        "commanded_mean_cycles": 4200,
        "deviation_pct": 0.5616942857142844
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 2,
        "realized_mean_cycles": 4218.32476,
        "commanded_mean_cycles": 4200,
        "deviation_pct": 0.43630380952381964
      },
      {
        "shape": "constant",
        "mean_us": 5,
        "realized_mean_cycles": 10538.38268,
        "commanded_mean_cycles": 10500,
        "deviation_pct": 0.3655493333333392
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 5,
        "realized_mean_cycles": 10544.10586,
        "commanded_mean_cycles": 10500,
        "deviation_pct": 0.42005580952380633
      },
      {
        "shape": "constant",
        "mean_us": 10,
        "realized_mean_cycles": 21035.41464,
        "commanded_mean_cycles": 21000,
        "deviation_pct": 0.16864114285713835
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 10,
        "realized_mean_cycles": 21047.27694,
        "commanded_mean_cycles": 21000,
        "deviation_pct": 0.22512828571428448
      },
      {
        "shape": "constant",
        "mean_us": 25,
        "realized_mean_cycles": 52530.59194,
        "commanded_mean_cycles": 52500,
        "deviation_pct": 0.05827036190475891
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 25,
        "realized_mean_cycles": 52275.76334,
        "commanded_mean_cycles": 52500,
        "deviation_pct": -0.427117447619052
      },
      {
        "shape": "constant",
        "mean_us": 50,
        "realized_mean_cycles": 105021.8346,
        "commanded_mean_cycles": 105000,
        "deviation_pct": 0.020794857142859006
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 50,
        "realized_mean_cycles": 104692.05524,
        "commanded_mean_cycles": 105000,
        "deviation_pct": -0.29328072380952236
      },
      {
        "shape": "constant",
        "mean_us": 100,
        "realized_mean_cycles": 210029.9768,
        "commanded_mean_cycles": 210000,
        "deviation_pct": 0.014274666666668573
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 100,
        "realized_mean_cycles": 210487.20626,
        "commanded_mean_cycles": 210000,
        "deviation_pct": 0.23200298095238395
      }
    ]
  },
  "external_floor_reference_widths": {
    "terminology": "external-floor-derived-reference-width",
    "power_guarantee": false,
    "values": [
      {
        "workload": "write-heavy",
        "between_run_cv_pct": 0.67,
        "reference_width_pct": 1.9,
        "source_environment": "linux-baremetal"
      },
      {
        "workload": "balanced",
        "between_run_cv_pct": 1.07,
        "reference_width_pct": 3.0,
        "source_environment": "linux-baremetal"
      },
      {
        "workload": "read-heavy",
        "between_run_cv_pct": 0.22,
        "reference_width_pct": 0.62,
        "source_environment": "pegasus"
      }
    ]
  }
}
```
<!-- IZANAGI-B10-SPEC-END -->

登録 12 cell の最大絶対偏差は `constant` / μ = 2 の 0.5616942857142844% であり、
exclusive 上限 1.0% を満たす。

## 6. 検出力について主張しないこと

上の `external_floor_reference_widths` は**外部 floor 由来の参考幅**であり、
本実験が実装した検定 (18 対を束ねた両側 exact 符号反転検定 + 3 族 Holm) の検出力ではない。
`pairs_per_family` の 18 は、1 族あたりの 3 block × μ 6 点の対の数であり、
物理残差の cell 数 (12) とは別のものである。
検出力は効果の μ 間の向き、対の差の分散と相関、Holm の順位に依存するので、
片側の stock の変動係数だけからは単一の最小検出効果量にならない。
`power_guarantee` は `false` に固定している。

**したがって非有意のときに書けるのは「この設計では検出しなかった」までである。**
「事前に定めた検出力の範囲内で検出しなかった」とは書かない。
代わりに全セルの効果量と 95% 信頼区間を報告し、
等価範囲 ±3.0% に対して信頼区間が内側か、外側か、境界を跨ぐかを必ず明記する。

read-heavy の参考幅は Pegasus の実測 (0.22%) を使う。
linux-baremetal の 0.11% は別環境の値なので参考として併記するに留める。

## 7. 実行と正しさ

- 相は `probe` → `build` → `verify` → `perf` の順に分ける。
  `verify` と `perf` は workload ごとに分ける。事前登録束縛が一致する WAL は再開できる。
- **性能計測は trace 無効ビルド、正しさ検証は trace 有効ビルドの別 run** で行う (絶対規律 1)。
  既存 pipeline が同じ genome / source から trace 有無の 2 つを別々に build し、
  verify は trace binary、bench は trace 無効 binary で走る。
  `IZANAGI_TRACE_DIR` は perf 側にも対称に設定され、環境変数の有無自体が判別子にならない。
- **verifier が anomaly を返した variant は即 reject する** (絶対規律 2)。
  bench へ到達させず fitness も付けない。正しさ検証の反復回数は 5 回で、
  実行時間を理由に減らさない。
- 性能測定に使う binary は、正しさを認証した attempt の binary の SHA-256 と完全一致させる。
  一致しないセルは bench へ送らず判定不能とする。
- perf に依存する診断は本実験の範囲外とする (この計算ノードに perf は無い)。

## 8. 報告に必ず含めるもの

- 全セルの中央値 throughput、反復のばらつき、abort 率、
  **backoff 呼び出し回数 (= abort 回数)**、毎秒呼び出し回数、
  **名目総待ち量 (= 呼び出し回数 × μ)**、正しさの認証状態。
  対象は block あたり 15 点 (reference 3 + 登録 cell 12) である。
- Holm は 3 族、1 族あたり 18 対であることを明示する。物理残差の 12 cell と混同させない。
- 全 workload の結果を退行込みで報告する。対象 workload で勝っても、
  他 workload で退行があれば退行込みで全件報告する。
- 判定不能セル・判定不能族は、分母から消さずに判定不能として明示する。
- 本走で使った発効版 commit hash、patch SHA、式 SHA、spec SHA、解析コード SHA。
- 物理残差については、**開示した 18 cell の probe**、**登録した 12 cell**、
  **v4 の束縛**を区別して書く。

**報告に書いてはならないこと。**

- `binary` を測った、あるいは 3 水準を比較した。
- `binary` の除外が事前登録された判断だった。
- 本書の結果で A-2 の逆転や過抑制域の機序を説明した。
- 待ち方と待ち量の直交切り分けを一般に閉じた。

## 9. 本書が閉じない B-10 の残り

- 過抑制域の機序
- ピーク位置の再現
- balanced workload の profile
- 実走での要求待ち量そのものの分布 (分位点・自己相関・スレッド間同時値率) の診断
- **`binary` を含む 3 水準の ladder と、ばらつきの用量反応**
- **待ち方と待ち量の一般的な直交切り分け** (本書が閉じるのは 1 contrast の範囲だけである)
- **本走中の実要求待ち量・実待機時間が形の間で一致しているかの確認**
  (合成ループの残差しか測っていない)
- **乱数計算そのものと撹拌器のオーバーヘッドを、待ち方の効果から分離すること**
- **結果を見ていない設計による独立な追試** (本書の grid は probe-informed amendment である)

これらは未取得のまま残る。本書の結果をもってこれらが閉じたと書いてはならない。

### 後継設計 (本書では実装しない)

3 水準の ladder を回復する設計として、二値の形を**折り返し構造**へ変える案がある。
2 つの bit `H1`、`H2` を使い、両者が一致したときだけ高い側を選べば
高い側の頻度は `1/2 + 2(p1 − 1/2)(p2 − 1/2)` となり、
`E[X] − μ` の `(p − 1/2)` に対する依存が**積**へ落ちて R1 を満たしうる。

この案は formula と patch の SHA を変えるので、D1098 に従って旧 formula の消費者を別名で凍結し、
新しい placeholder を凍結してから物理残差 probe を走らせ直す必要がある。
**本書では実装せず、設計として記録するに留める。**
