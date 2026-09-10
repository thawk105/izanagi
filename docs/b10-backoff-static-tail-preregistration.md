# B-10 静的 backoff の右 tail — 本格格子と停止基準の事前登録

論文 `docs/paper-story/2026-08-26.md` の残件 **B-10「機序説明の帯域外への拡張」**のうち、
静的 backoff の**右側 (物理値 1000 マイクロ秒超)** を記述的に特性化する 1 項目の事前登録である。

**本書が扱うのは記述であって機序ではない。** B-10 の「過抑制域の**機序**」は D1678 が見送りと裁定した
項目であり、本書はそれを再開しない。本書が固定するのは、abort 抑制が backoff を増やすにつれて
飽和するかどうかを、格子・反復数・判定式・失敗条件を結果より前に決めたうえで測るための規則だけである。

D1813 が定めた 2 段構成の**第 2 段**にあたる。第 1 段 (探索走 `t2418-explore`) は完走しており、
その結果は §2 で全件開示する。

## 0. 本書の版と発効

**本書は v1 である。** 機械可読 spec (§5) に placeholder は無く、すべての値が確定している。

- **発効 = 本書を含む commit が存在すること。** 本走はその commit を指して起動し、成果物へ
  commit hash・本書の blob SHA-256・spec の SHA-256 を記録する。記録が無い実走は
  事前登録された実験として扱わない。
- 発効後の変更は旧版を Git 履歴に残したまま新しい commit で行い、変更理由と変更時点を本節へ明記する。
  **結果 commit より後に書かれた変更は事前登録として数えない。**
- 本書の中に本書自身の hash を書かない。同一性は commit と blob が持つ。

### 本書が前向きに固定したもの、していないもの

**正直に区別する。** 第 1 段の探索は本書より前に完走しており、その abort 率・throughput・
飽和の不在は**既知の状態で本書を書いた**。

- **前向きに固定したのは、まだ 1 度も観測していない本格 cohort に対する測定規則と判定規則だけである。**
  格子、反復数、動作点、測定順、飽和述語、閾値、失敗条件、開示規則、束縛。
- **前向きではないもの:** 格子の位置と刻み幅の選択、5% という等価幅の選択、
  変動係数の品質 gate 0.02 という値の選択、
  「表現域内で飽和しない」を正当な結末に含めるという選択。**いずれも探索結果を見た後に選んだ。**
  これは先例 `docs/b10-backoff-shape-preregistration.md` が
  「これは事前登録ではない。probe の結果を見た後に行った改訂である」と限定したのと同じ型である。
- したがって本書は「静的 tail 研究全体の事前登録」ではない。**「探索開示済み・本格 cohort 前の事前登録」**である。

## 1. 事前登録の効力とその限界

- ancestry が証明するのは「その bytes の文書がその時点に存在したこと」だけである。
- **本書は現時点で後続の実走を機械的に拘束していない。** 本書の spec を parse する consumer は
  まだ存在しない。本書が現時点で持つ効力は次の 2 つに限る。
  1. 後続実装への**規範** — 本走 driver が満たすべき関係を、結果より前に書いた文書として。
  2. **時点証拠** — 本格 cohort の結果が出る前にこの bytes が存在したという証拠。
- **したがって「本書が拘束している」と書いてはならない。** §8 の投入前条件が満たされるまで、
  本格 cohort を投入してはならない。
- 本書は測定の正しさを保証しない。正しさは trace 有効ビルドの直列性検査が判定する (§4.6)。
- **repo の docs 検査 (`tools/check_docs.py`) が緑であることは、本書の中身が正しいことの証拠ではない。**
  同検査は予算・dispatch・節・孤児・住所の構造 lint であって、本書の本文を検査対象にしていない。
  本書の中身を検査したのは敵対レビューと、規則からの値の再生成である。

## 2. 開示 — 第 1 段の探索で何を観測し、そこから何を選んだか

D1813 は「探索値・探索で選んだ格子・停止基準を開示する」ことを求めている。本節がその開示である。

### 2.1 探索走の identity

- `run_kind` = `t2418-explore`、`claim_scope` = `exploratory_backoff_tail_only_not_formal_series`
- 投入 2026-09-09、request 986597 / 986598 / 986599、3 job とも `status=complete`
- 出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/`
- 一次資料 `output/insights/2026-09-09_t2418-backoff-static-explore/README.md`
- 探索点は物理値 2000 / 4000 / 9999 マイクロ秒の 3 点、各 5 rep、
  `records=1000000` / `threads=48` / `extime_s=3`

### 2.2 探索の実測値 — 5 rep の生の配列で開示する

**代表値や中央値ではなく反復の生値を載せる。** 集約前の値を出すことで、中央値と平均のどちらを
載せたかという曖昧さが構造的に起きない。出所は各 workload の
`campaigns/<campaign-id>/reports/t2418-backoff-static-explore-<workload>.json` の `points[]` である。

abort 率 (無次元、**CCBench が小数第 4 位まで印字した値**。§4.3 の理由により本格走ではこの値を
解析入力にしない):

| workload | 2000 マイクロ秒 | 4000 マイクロ秒 | 9999 マイクロ秒 |
|---|---|---|---|
| write-heavy | 0.0292, 0.0296, 0.0292, 0.0293, 0.0292 | 0.0199, 0.0198, 0.0199, 0.0198, 0.0198 | 0.0114, 0.0114, 0.0114, 0.0115, 0.0114 |
| balanced | 0.0404, 0.0402, 0.0404, 0.0404, 0.0402 | 0.0269, 0.0267, 0.0270, 0.0267, 0.0268 | 0.0145, 0.0147, 0.0145, 0.0145, 0.0145 |
| read-heavy | 0.0170, 0.0170, 0.0170, 0.0170, 0.0169 | 0.0120, 0.0119, 0.0119, 0.0119, 0.0119 | 0.0073, 0.0074, 0.0074, 0.0074, 0.0074 |

throughput (毎秒トランザクション):

| workload | 2000 マイクロ秒 | 4000 マイクロ秒 | 9999 マイクロ秒 |
|---|---|---|---|
| write-heavy | 746370, 736061, 746680, 746465, 747783 | 564585, 565390, 564565, 567031, 565924 | 401829, 402820, 404392, 401306, 403220 |
| balanced | 542511, 544933, 542115, 541955, 545305 | 418499, 420932, 417170, 420822, 420293 | 316986, 313957, 317205, 318574, 317705 |
| read-heavy | 1248419, 1253190, 1247026, 1251217, 1256866 | 918776, 921117, 922824, 920568, 924012 | 619695, 616015, 616949, 613431, 614907 |

観測された性質 (**探索の観察であって判定ではない**):

- 3 workload すべてで abort 率は 9999 マイクロ秒まで単調に下がり続け、**飽和の兆候が無い**。
- throughput も同じ区間で単調に下がる。abort 抑制の追加分を throughput の低下が買っている。
- 静的 3 点の throughput の変動係数は 0.001822〜0.006508。
  **この値は throughput の変動係数であって abort 率のそれではない** (§4.7)。

### 2.3 探索から何を選んだか

- **格子の位置と刻み幅** — 飽和が右端まで現れなかったため、右端の分解能を最優先し、
  **表現上限 9999 マイクロ秒を起点に下向きへ半オクターブ**で刻む格子を選んだ (§4.1)。
- **等価幅 5%** — 「backoff を倍にしても abort 率の追加低下が 5% 以下」を平坦と呼ぶ実用的な幅として
  選んだ。外部標準から導いた値ではない。探索で観測された低下 (倍増あたりの点推定で 29.8〜37.1%) を
  無理に平坦へ分類しない水準であることを確かめて選んだ。
- **変動係数の品質 gate 0.02** — 探索で観測した変動係数のおよそ 3 倍として選んだ。
  **選定時に参照した「探索の最大変動係数」は throughput のものであり、abort 率のものではなかった。**
  その取り違えを開示したうえで値は 0.02 のまま据え置く。この gate は品質のためのものであり、
  検出可能性は §4.4 の 3 分割が区間ごとに判定するので、gate の値に検出力を負わせていない。
- **域内非飽和を正当な結末に含めること** — 探索が上限まで飽和を示さなかったという事実を踏まえ、
  本格走でも飽和が現れない可能性が高いと考えたうえで、その結末を前向きに定義した (§4.5)。

### 2.4 探索の測定値は本格標本に混ぜない

- 探索の rep、分散、区間、順位、途中成果物を本格推定へ入れない。
- 本格格子の abscissa として探索と同じ物理値を使うのは 9999 マイクロ秒だけである。
  **同じ abscissa でも測定は本格 cohort で新規に取り直す。**
- **本書は探索の再現性を検証する設計ではない。** 2000 と 4000 マイクロ秒は本格格子に入らないので、
  同じ座標で探索と本格を比べられるのは 9999 マイクロ秒だけである。これは上限アンカーの均一格子を
  選んだことの代償であり、意図した設計である。
- 混入を機械的に検出できるようにするため、本格 observation ごとに出所を必須化する (§4.8)。

## 3. 何を主張し、何を主張しないか

### 主張しうること

- 登録した格子・反復数・判定式の下で、**abort 率の飽和位置が存在するか、表現可能域内には
  現れなかったか**を、workload ごとに報告する。
- 同じ格子上の throughput を、過抑制の費用として必ず併記する。

### 主張しないこと

- **機序を主張しない。** なぜ abort 率がその形で下がるのかは本書の対象外である (D1678)。
- **9999 マイクロ秒より右を主張しない。** 9999 は物理的な限界ではなく、
  現行の符号化が表現できる上限である。域内非飽和は「飽和しない」ではなく
  「**表現可能域内では飽和を観測しなかった**」としか言えない。
- **性能の認証を主張しない。** 本走は trace 無効ビルドの性能測定であり、
  `performance_certified` は false のままである。正しさだけが認証される。
- **物理量の意味の witness を主張しない。** 正値 `BACKOFF_FIXED` の pointwise meaning witness は
  既存 sweep 全体と同じく未確立である。本書はこの境界を既存系列より弱めも強めもしない。
  witness を確立する gate の新設は [T-2501] としてユーザー裁定待ちであり、本書の対象外である。
- **「飽和位置がある、または域内非飽和である」という選言は科学的主張ではない。** それは結果分類が
  全域を覆っているというだけである。反証可能な主張は「**全 workload で登録述語を満たす飽和位置が
  存在する**」であり、域内非飽和はその反証結果として報告される。

## 4. 前向きに固定した規則

### 4.1 格子 (R1)

物理値 `b` の格子は次の規則で生成する。

```text
b_k = round(9999 / 2^(k/2))   for k = 6, 5, 4, 3, 2, 1, 0
ただし b_k > 1000 のものだけを採る
round は四捨五入 (端数 0.5 はゼロから遠い側へ) とする
```

**上限から下向きに割って作る。** 下端から上向きに掛けて作ると別の値になる (例えば
1250 から 2 段上は 2500 だが、上限から 3 段下は 3535 であって 3536 ではない)。
規則と値のどちらかを写し間違えると格子が壊れるので、**値は必ずこの規則から再生成して照合する。**

結果として本格 tail は **7 点**である。

| 物理値 (マイクロ秒) | `BACKOFF_FIXED` raw |
|---:|---:|
| 1250 | 3250 |
| 1768 | 3768 |
| 2500 | 4500 |
| 3535 | 5535 |
| 5000 | 7000 |
| 7070 | 9070 |
| 9999 | 11999 |

これに**境界参照 1000 マイクロ秒 (raw 3000)** を 1 点加え、1 workload あたり **8 genome** とする。

- **上限を起点に下向きへ刻む理由。** 1000 を起点に上向きへ刻むと、上限 9999 の手前で
  半オクターブが入りきらず、終端だけ短い区間が残る。短い区間は同じ反復数では判別力が落ち、
  **飽和が最も起こりうる右端でだけ述語が届かなくなる** (§6)。上限を起点にすると、
  tail の隣接区間の対数比が 0.34642〜0.34673 に収まり均一になる (境界参照区間だけは 0.22314)。
  この均一性は本書の判定の前提であり、**格子を変えるなら判定の検出力も測り直す**必要がある。
- **点数をこれ以上増やさない理由。** 均一な半オクターブで域内に 7 点入り、隣接 6 区間が得られる。
  これは飽和の有無と、あれば位置の粗い bracket を出すのに足りる。増やしても位置の細分化にしかならず、
  絶対規律 4 (飽和する最小の規模を使う) に反する。1 workload 8 genome は先例 `t2266-tail` と同数で、
  実走 11 分の実績がある規模である。
- **境界参照 1000 を入れる理由。** 正式格子 `EXTENDED_SWEEP_US` の上端と tail を**同一 job 内で**
  接続するためである。過去の正式系列の数値を流用すると campaign を跨いだ標本の継ぎ合わせになる。
- **境界参照を飽和述語に入れない理由。** 1000 と 1250 の対数比は 0.22314 で、
  tail 内の 0.34642〜0.34673 と異なる。区間ごとに述語の強さが変わるのを避ける (§4.4)。
  **その代償として、両側から挟める最も左の飽和位置は 1768 マイクロ秒になる。**
  全区間が平坦だった場合は「1250 以下」の左側打切りとしか言えない (§4.4 の表)。

**raw 値の発行禁止域。** 符号化は物理値 `b` に対し `b <= 999` なら `b`、`b >= 1000` なら `b + 2000`
である。raw 値 `[1000, 2999]` は C++ 側の hole (`patches/silo-backoff-fixed.patch` の合成枝) で
別の形 (商 1 = 対称剰余、商 2 = 二値) へ落ちるため、**本書の登録点はこの域の raw 値を 1 つも発行しない。**
登録した raw 値はすべて 3000 以上であり、商 3 以上の定数枝 (`BACKOFF_FIXED - 2000`) だけを通る。

### 4.2 動作点・反復数・測定順 (literal で固定する)

**共有定数を参照しない。** 生産コード・loader・テストが同じ定数へ追随すると、
定数が変わったときに全体が追随して本書に反したまま緑になる。以下は本書に直接書いた数字であり、
本走はこれと一致することを確かめてから測る。

- workload は 3 つ。`write-heavy` (read ratio 5) / `balanced` (read ratio 50) / `read-heavy` (read ratio 95)。
  いずれも zipf skew 0.9、rmw 0、max ope 10。
- `records = 1000000`、`threads = 48`、`extime_s = 3`。
- 性能測定 5 rep/cell、正しさ検査 5 rep/cell。
- 8 点 × 3 workload = **24 cell**。性能・正しさとも期待 rep 総数は **120**。
- workload ごとに 1 job、計 3 job。

**測定順**は、昇順に並べた 8 label に対し `random.Random(<seed>).shuffle` を 1 回適用した
決定的な順列とする。seed は既存の workload seed を使う。解決した順序は次のとおりであり、
本走はこの literal と一致することを確かめる。

| workload | seed | 測定順 (物理値 マイクロ秒) |
|---|---|---|
| write-heavy | 0xB10005 | 2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070 |
| balanced | 0xB10050 | 1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999 |
| read-heavy | 0xB10095 | 3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000 |

**時間枠**は既存の枠を保持する。sweep の上限 11700 秒、PBS の予約 18000 秒。

- 先例は 8 genome を 11 分で完走している。ただし**その 11 分は 1 cell あたり正しさ検査 1 回の実績**で
  あり、本書が要求する 1 cell 5 回とは同型でない。探索走で観測した最長の検査時間を追加分へ
  保守的に足すと、**約 20 分/job** である。いずれも 195 分の sweep 上限と 300 分の予約の内側にある。
- **実行時間を理由に点や反復を削らない。**

### 4.3 解析に使う abort 率は整数カウンタから再計算する (R3)

**CCBench は abort 率を小数第 4 位までしか印字しない** (`external/ccbench/common/result.cc` の
`Result::displayAbortRate`)。tail の右端では abort 率が 0.007〜0.015 まで下がるため、
1e-4 の量子は平均の 0.7〜1.4% に当たる。この丸め値を精密な観測として扱うと、
反復間の標本標準偏差が量子化に支配されて不当に小さくなり、区間推定が狭まり、
**「測れていないこと」が「飽和」と判定される**向きに倒れる。これは規律 2 と規律 3 に触れる。

したがって次を要求する。

- 本走は rep ごとに `abort_counts_` と `commit_counts_` を**整数のまま**保存する。
  両者は CCBench が abort 率と同じ表示経路で必ず印字しており (`Result::displayAbortCounts` /
  `Result::displayCommitCounts`)、解析側の parser も両 key を既に知っている
  (`orchestrator/calibrator/benchparse.py` の `abort_rate`)。
- 解析の abort 率は `aborts / (aborts + commits)` として全精度で再計算する。
- **小数第 4 位に丸めた `abort_rate` を解析入力にしない。** 整数カウンタが保存されていない走行は
  失敗とし、丸め値への fallback を認めない (§7)。

**現状の実測 (探索走 `t2418-explore` の WAL を直に読んだ結果)。**

- 性能測定の記録 (`bench_done`) は、rep ごとの throughput の配列と、**cell 全体で 1 つの**
  丸めた abort 率しか持たない。rep ごとの abort 率は WAL に無く、実行中の捕捉から report へ
  直接書かれている。したがって**現状の WAL からは rep ごとの abort 率を再構成できない。**
- 一方、正しさ検査の記録 (`verify_done`) は `commits` と `aborts` を**整数のまま**持っている。
  つまり整数カウンタを WAL へ載せること自体は既にこの family で行われている。
  ただしそれは trace 有効ビルドの走行の値であり、**性能測定の値の代わりにはならない。**
- したがって本走は、**性能測定の rep ごとの整数カウンタを WAL へ保存する**必要がある。
  これは新しい捕捉であり、**投入前条件**である (§8.1)。

### 4.4 飽和判定 (停止基準)

**これは測定を途中で止める規則ではない。全点を測り終えてから飽和位置を報告する規則である。**
早期打ち切りを禁じる。

workload `w`、格子点 `b_i`、rep `r = 1..5` の (再計算した) abort 率を `a_wir` として、次を計算する。

```text
m_wi  = 平均(a_wi1..a_wi5)
s_wi  = 標本標準偏差(a_wi1..a_wi5)   (ddof = 1)
cv_wi = s_wi / m_wi
v_wi  = cv_wi^2 / 5

h_i    = log(b_i / b_(i-1))
qhat_i = log(m_wi / m_w(i-1)) / h_i
se_i   = sqrt(v_wi + v_w(i-1)) / h_i
nu_i   = (v_wi + v_w(i-1))^2 / (v_wi^2 / 4 + v_w(i-1)^2 / 4)
t_i    = t(1 - 0.05/36, nu_i)          両側 18 区間ぶんの同時被覆
qL_i   = qhat_i - t_i * se_i
qU_i   = qhat_i + t_i * se_i
U_i    = 1 - exp(qL_i * log(2))        倍増あたり低下率の同時上限
L_i    = 1 - exp(qU_i * log(2))        倍増あたり低下率の同時下限
```

- `U_i` は「真の abort 率が backoff 倍増あたり**最大で**何割下がりうるか」、
  `L_i` は「**最小でも**何割下がるか」の同時限界である。`L_i` は負にもなりうる (上昇側)。
- 対象は **tail 内の隣接 6 区間**だけである。3 workload × 6 = **18 区間**、各区間で両側を見るので
  **36 の片側限界**に Bonferroni を適用し、familywise の有意水準を 0.05 に固定する。
- 境界参照 1000 マイクロ秒は測定・報告するが、区間の集合には入れない。

**区間の分類 — 3 つに分ける。相互排他かつ全域を覆う。**

計算の**前に**次を確かめる。満たさない入力は §7 の失敗であり、対数を取ってはならない。

- 各 rep の abort 回数・commit 回数が非負の厳密な整数で、`abort + commit > 0` であること。
- 各 rep の throughput が有限かつ正であること。
- 区間の左端 cell が全 rep で abort 0、右端 cell が正値である (ゼロから正値へ上がる) 状態でないこと。
  この状態は `log(m_i / 0)` が定義できないため、`qL` を経ずに直接 cohort を `invalid` にする。

そのうえで、上から順に判定する。**先に当たった分類を採り、後の分類は見ない。**

1. **`saturated` (両端とも abort ゼロ)** — 隣接 2 cell がともに全 5 rep で abort 数 0。
   `qhat = qL = qU = 0`、`U = L = 0`、`U_flat = 0` とする。対数は取らない。
2. **`declining` (正値から全ゼロへ落ちた)** — 左端 cell が正値、右端 cell が全 rep で abort 0。
   低下が完全なので `declining` とする。対数は取らない。
   この区間では `qhat` / `qL` / `qU` / `U` / `L` / `U_flat` を**すべて `null`** とし、
   理由 (低下が完全) を併記する。数値を省略したり、無限大を書いたりしない。
3. **`indeterminate` (分散なし)** — 1・2 に当たらず、`v_wi + v_w(i-1) == 0`
   (両端とも標本分散ちょうど 0 で、少なくとも一方が正値)。自由度が定義できない。
   **`se = 0` として通してはならない** — 偽の飽和を作る。この入力は仮想ではない。
   既存の正式系列成果物に、正値かつ 5 rep が完全に同値の cell が実在する。
   この区間では `qL` / `qU` / `U` / `L` / `U_flat` を**すべて `null`** とし、理由を併記する。
4. **`saturated` (平坦)** — `qhat_i <= 0` かつ `U_i <= 0.05`。
   最大に見積もっても倍増あたりの低下が 5% 以下である。
5. **`declining` (低下が続いている)** — `L_i > 0.05`。
   最小に見積もっても倍増あたりの低下が 5% を超える。**平坦でないことが積極的に言える。**
6. **`indeterminate` (判別不能)** — 上のどれにも当たらない。平坦とも低下継続とも言えない。
   反復ばらつきが大きい、または区間が短くて分解能が足りない場合がここへ来る。

**この 3 分割にした理由。** 区間が短い、あるいは分散が大きいと、真に平坦でも `U_i` は 5% を超える。
その状態を「飽和しなかった」と読むと、**分解能の不足を非飽和の証拠に化かす**ことになる。
逆に、観測が明らかに強い低下を示しているのに検出力だけを理由に `indeterminate` へ落とすと、
今度は**明白な低下が非飽和の根拠から消える**。`L_i > 0.05` を積極的な低下の判定に使うことで、
両方を避ける。参考として、真に平坦な区間が `U_i <= 0.05` に届くかどうかの目安を `U_flat_i`
(`qhat_i = 0` と置いて `U_i` を評価したもの) として**併記する**。これは分類には使わない診断値であり、
分類 1・2・3 の区間では上に書いたとおり `0` または `null` になる。

**飽和位置 — 上限まで続くことを要求する。** tail の格子点を `b_1 = 1250` から `b_7 = 9999` と番号付け、
区間を `I_i = (b_i, b_(i+1))`、`i = 1..6` とする (`I_1` は 1250→1768、`I_6` は 7070→9999)。
`I_j` から `I_6` まで**すべてが `saturated`** であり、かつその本数が 2 以上であるような最小の `j` を
飽和の開始とする。

| `j` | 報告する位置 | bracket | 打切り |
|---|---|---|---|
| `j >= 2` | `b_j` | `[b_(j-1), b_j]` | 無し (両側から挟めている) |
| `j = 1` | 「1250 マイクロ秒以下」 | 下端なし | **左側打切り** |

- `j = 1` は 6 区間すべてが `saturated` の場合である。境界区間 (1000→1250) を述語に入れていないため、
  開始が 1250 より左のどこにあるかを本書は言えない。位置を `1250` という点として報告してはならない。
- したがって、**両側から挟める最も左の飽和位置は `b_2 = 1768` マイクロ秒、その bracket は
  `[1250, 1768]`** である。
- **局所的に平坦な 2 区間があっても、その右で `declining` に戻るなら飽和位置を出さない。**
  それは tail の飽和ではなく局所的な平坦区間であり、そう呼んで開示する。

### 4.5 結末の集合 — workload ごとに排他、集約は一意に導出する

**workload の状態は次の 3 つで排他である。上から順に当てはめる。**

1. `indeterminate` — その workload の 6 区間に `indeterminate` が 1 つでもある。
   どの区間かを必ず併記する。**この状態を「飽和しなかった」と読み替えない。**
2. `saturated` — **`indeterminate` が 0 件**であり、かつ §4.4 の意味で上限まで続く飽和開始が存在する。
3. `not-observed` — **`indeterminate` が 0 件**であり、かつ上限まで続く飽和開始が存在しない。
   局所的な平坦区間があればその位置を併記する。

2 と 3 はどちらも「`indeterminate` が 0 件」を条件に含み、後半の条件が互いの否定になっている。
したがって評価順に依存せず排他である。

**集約 verdict は 3 workload の状態の組から一意に決まる。**

| verdict | 条件 |
|---|---|
| `invalid` | §7 の失敗条件のいずれかに当たった (他のすべてに優先する) |
| `indeterminate-in-region` | 1 つ以上の workload が `indeterminate` |
| `saturated-in-all-workloads` | 3 workload すべてが `saturated` |
| `not-observed-in-any-workload` | 3 workload すべてが `not-observed` |
| `not-observed-in-at-least-one-workload` | 上のどれでもない (`saturated` と `not-observed` が混在) |

**この表は上から順に評価する。**最初に当てはまった 1 つだけを採る。
`invalid` は他のどれとも同時に成立しうる (失敗条件は数値の分類と独立に発火する) ので、
一意性を与えているのは条件そのものの排他性ではなく**この評価順**である。
一方、workload 状態の 3 つ (§4.5 前半) は条件自体が排他であり、評価順に依存しない。

**域内非飽和の言い方を固定する。** 「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに
飽和を観測しなかった」とだけ書く。「飽和しない」「飽和点が存在しない」とは書かない。

### 4.6 正しさ (規律 2 を緩めない)

- 正しさ検査は **trace 有効ビルド**で行い、性能測定は **trace 無効ビルド**で行う。別ビルド・別走行とする。
- 24 cell すべてについて 5 rep の正しさ検査が揃い、各 verify record が `certified` であり、
  anomaly が 0 件であることを要求する。
- **正しさの権威は WAL の committed verify record の `certified` である。** report の point 側にある
  `certified` field は現行実装では常に false の literal であり (性能認証の意味で使われている)、
  正しさの判定に使ってはならない。この取り違えは全 cell を誤って失敗させる。
- 正しさに不合格の cell を性能測定へ到達させない。
- **時間を理由に正しさの反復を減らさない。**
- 静的 8 genome それぞれについて、trace 無効ビルドの成果物が完全に揃い、genome に束縛され、
  完全長の SHA-256 を持ち、8 個がすべて相異なることを fail-closed で要求する。
  **確認できた個数が少ないときに成功と見なす一般 helper の挙動に依存してはならない。**
  比較する SHA-256 は**性能測定に使った trace 無効ビルドのもの**であり、trace 有効ビルドのものと
  取り違えない。両者は別の値であり、取り違えると別の受理集合になる。

**観測ごとに要求する型と範囲。** 既存 loader が実際に検査している強さを下回らないよう、
次を明示的に要求する。**どれか 1 つでも満たさない観測があれば cohort 全体を `invalid` にする。**

- abort 回数・commit 回数は非負の厳密な整数で、`abort + commit > 0`。
- throughput は有限かつ正。abort 率 (再計算値) は `[0, 1]`。
- rep の添字は `0..4` の重複なし全数。cell ごとに 5 本ちょうど。
- 観測は期待する workload・格子点・genome の組と一致し、重複が無い。
- 各観測が、label・物理値・raw 値・canonical genome の対応と一致する。
- 正しさの record は、採用された attempt に束縛された `verify_done` のものである。
- 正しさ検査の mode を記録し、探索走 `t2418-explore` と同じ mode であることを要求する。
  **mode の名前を本書で発明しない。** 比較の基準は、探索走の WAL の `verify_done` 記録が持つ
  `payload.workload.tag` の値である (探索走の実測ではその値は `legacy` である)。
  本走はこの座標を記録し、同じ値であることを要求する。
- **1 cell あたり 5 本の正しさ記録が実際に発行されること。** 探索走の WAL は 1 cell あたり
  `verify_done` 1 本しか持たず、現行 loader も件数 5 を検査していない。本書は 5 本を要求するので、
  **5 本が発行されることの確認は投入前条件である** (§8.1)。これを確かめずに投入すると、
  正常な走行が §7 の失敗条件 1 で必ず無効になる。

### 4.7 変動係数の扱い

- **abort 率の変動係数と throughput の変動係数は別物である。** 既存 report の `cv` field は
  throughput のものである。両者を別の key で開示し、混同しない。
- 品質 gate は abort 率・throughput の双方に掛け、cell の変動係数が 0.02 以上なら失敗とする。
- **量子化された率から再計算した変動係数を検出精度の根拠に使わない。** 検出力の議論は
  §4.4 の `U_flat` によって、走行ごとに実測から自動的に行う。

### 4.8 出所は自己申告させない

本格の observation ごとに、`source_run_kind`、campaign id、campaign lock の digest、attempt id、
rep index、source measurement を必須とする。しかし **field が付いているだけでは足りない。**
成果物に「自分は本格である」と書かせるなら、探索の数値を写したものが同じことを書けてしまう。

- **出所は observation の payload から読まず、本格 campaign の admitted WAL の envelope から導出する。**
- 導出した campaign id と lock digest を、信用している campaign lock と**厳密一致**で照合する。
- `source_run_kind` が本走の run kind と一致することを要求する。
- WAL record の digest と canonical genome を必須とし、rep と attempt の対応を WAL 側で解決する。
- 解析は WAL から再構成し、入力 report が載せている `qL` / `U` / verdict / 正しさの真偽値を
  権威として受け取らない。

### 4.9 3 job の同一性

本書の主張は 3 workload をまとめた 1 つの cohort についてのものである。**別々の条件で測った 3 job を
1 つの cohort と呼んではならない。** 3 つの campaign lock の間で次が一致することを要求する。

- CCBench の source digest と toolchain。
- 環境契約 (environment contract) と較正 (calibration) の identity。
- 本書の commit・blob SHA-256・spec SHA-256。
- 動作点の literal (`records` / `threads` / `extime_s` / 性能 rep 数 / 正しさ rep 数)。

**workload 座標は 3 job で一致しない。一致させてはならない。** 3 job は設計上それぞれ別の workload を
測るからである。workload については代わりに次を要求する。

- 各 job の workload 座標が、§4.2 に登録した**自分の行**と一致すること。
- 3 job の workload 名の集合が `write-heavy` / `balanced` / `read-heavy` を**重複なく過不足なく**
  覆うこと。

一致しなければ cohort 全体を `invalid` にする。単独占有の確認など、投入時に既存機構が要求している
条件を緩めることはしない。

## 5. 機械可読 spec

以下の JSON が判定規則の**正本**である。本走 driver はこれを全件 parse し、コードの定数ではなく
この spec を引数として測定と解析を行う。

**区切りの契約。** spec は直後の HTML comment 対で囲む。開始 marker は `IZANAGI-B10-STATIC-TAIL-SPEC`
に `-BEGIN` を、終了 marker は同じ語に `-END` を付けたものである。
**この 2 つの marker 文字列を JSON の中に値として置いてはならない。** 置くと marker を走査する
consumer が JSON を途中で切る。marker は容器の契約であって中身ではないので、prose 側にだけ書く。

<!-- IZANAGI-B10-STATIC-TAIL-SPEC-BEGIN -->
```json
{
  "schema_version": "izanagi-b10-backoff-static-tail-preregistration/v1",
  "preregistration": {
    "document_path": "docs/b10-backoff-static-tail-preregistration.md",
    "stage_of_d1813": 2,
    "formal_run_must_record_containing_commit": true,
    "formal_run_must_record_document_blob_sha256": true,
    "formal_run_must_record_spec_sha256": true,
    "post_result_edits_count_as_preregistration": false,
    "prospective_scope": "formal-cohort-measurement-and-decision-rules-only",
    "not_prospective": [
      "grid-position-and-spacing-choice",
      "five-percent-equivalence-width-choice",
      "two-percent-cv-quality-gate-choice",
      "inclusion-of-in-domain-non-saturation-as-a-valid-outcome"
    ],
    "document_blob_sha256_covers": "raw file bytes without any git blob header",
    "spec_sha256_covers": "the utf-8 bytes between the marker lines with the opening and closing code fence lines removed, lf newlines, one trailing newline, no json canonicalization",
    "extracted_spec_bytes_must_parse_as_json": true,
    "binding_status_at_v1": "normative-and-time-evidence-only-no-consumer-exists",
    "formal_submission_blocked_until_consumer_verified": true
  },
  "study": {
    "formal": true,
    "claim_scope": "descriptive-static-backoff-right-tail-abort-saturation-with-throughput-cost",
    "mechanism_claim": false,
    "performance_certification_claim": false,
    "physical_domain_us": {
      "lower": 1000,
      "lower_inclusive": false,
      "upper": 9999,
      "upper_inclusive": true
    },
    "upper_bound_is_representational_not_physical": true,
    "exploration_measurements_in_formal_estimation": false,
    "measure_all_points_before_analysis": true,
    "early_measurement_stop_allowed": false,
    "falsifiable_claim": "a-registered-saturation-location-exists-in-every-workload",
    "outcome_disjunction_is_classification_not_hypothesis": true
  },
  "disclosed_exploration": {
    "run_kind": "t2418-explore",
    "physical_values_us": [2000, 4000, 9999],
    "reps": 5,
    "abort_rate_reps_as_printed": {
      "write-heavy": {
        "2000": [0.0292, 0.0296, 0.0292, 0.0293, 0.0292],
        "4000": [0.0199, 0.0198, 0.0199, 0.0198, 0.0198],
        "9999": [0.0114, 0.0114, 0.0114, 0.0115, 0.0114]
      },
      "balanced": {
        "2000": [0.0404, 0.0402, 0.0404, 0.0404, 0.0402],
        "4000": [0.0269, 0.0267, 0.0270, 0.0267, 0.0268],
        "9999": [0.0145, 0.0147, 0.0145, 0.0145, 0.0145]
      },
      "read-heavy": {
        "2000": [0.0170, 0.0170, 0.0170, 0.0170, 0.0169],
        "4000": [0.0120, 0.0119, 0.0119, 0.0119, 0.0119],
        "9999": [0.0073, 0.0074, 0.0074, 0.0074, 0.0074]
      }
    },
    "throughput_tps_reps": {
      "write-heavy": {
        "2000": [746370, 736061, 746680, 746465, 747783],
        "4000": [564585, 565390, 564565, 567031, 565924],
        "9999": [401829, 402820, 404392, 401306, 403220]
      },
      "balanced": {
        "2000": [542511, 544933, 542115, 541955, 545305],
        "4000": [418499, 420932, 417170, 420822, 420293],
        "9999": [316986, 313957, 317205, 318574, 317705]
      },
      "read-heavy": {
        "2000": [1248419, 1253190, 1247026, 1251217, 1256866],
        "4000": [918776, 921117, 922824, 920568, 924012],
        "9999": [619695, 616015, 616949, 613431, 614907]
      }
    },
    "abort_rate_printed_decimal_places": 4,
    "maximum_reported_throughput_cv_static_points": 0.006508357807082461,
    "maximum_recomputed_abort_cv_from_quantized_rates_static_points": 0.006151493748,
    "abort_cv_from_quantized_rates_is_not_a_precision_basis": true,
    "the_cv_field_of_the_existing_report_is_the_throughput_cv": true,
    "exploration_abort_reduction_per_doubling_point_estimate_range": "0.298-to-0.371",
    "observed_abort_direction": "strictly-decreasing-at-all-three-workloads",
    "observed_throughput_direction": "strictly-decreasing-at-all-three-workloads",
    "observed_saturation_status": "exploratory-interpretation-not-a-formal-verdict",
    "observed_saturation_summary": "not-observed-through-9999us",
    "grid_selection_timing": "after-exploration-before-formal-run",
    "exploration_abscissae_reused_in_formal_grid_us": [9999],
    "formal_remeasurement_required_at_reused_abscissae": true,
    "exploration_sample_reuse_allowed": false
  },
  "grid": {
    "generation_rule": "b_k = round(9999 / 2^(k/2)) for k in [6,5,4,3,2,1,0], keep b_k > 1000",
    "anchor": "representation-cap",
    "regular_ratio": 1.4142135623730951,
    "representation_cap_us": 9999,
    "authoritative_values": "analysis_values_us",
    "boundary_reference_values_us": [1000],
    "boundary_reference_in_saturation_intervals": false,
    "formal_tail_values_us": [1250, 1768, 2500, 3535, 5000, 7070, 9999],
    "analysis_values_us": [1000, 1250, 1768, 2500, 3535, 5000, 7070, 9999],
    "encoding_rule": "raw = physical_us + 2000 for every registered point",
    "encoded_static_points": [
      {"physical_us": 1000, "backoff_fixed_raw": 3000},
      {"physical_us": 1250, "backoff_fixed_raw": 3250},
      {"physical_us": 1768, "backoff_fixed_raw": 3768},
      {"physical_us": 2500, "backoff_fixed_raw": 4500},
      {"physical_us": 3535, "backoff_fixed_raw": 5535},
      {"physical_us": 5000, "backoff_fixed_raw": 7000},
      {"physical_us": 7070, "backoff_fixed_raw": 9070},
      {"physical_us": 9999, "backoff_fixed_raw": 11999}
    ],
    "forbidden_raw_range": {"lower": 1000, "upper": 2999, "reason": "falls into shape branches quotient-1-and-2"},
    "all_registered_raw_values_use_constant_branch": true,
    "excluded_context_references": ["none", "adaptive"],
    "point_counts": {
      "boundary_references_per_workload": 1,
      "formal_tail_points_per_workload": 7,
      "total_points_per_workload": 8,
      "saturation_intervals_per_workload": 6
    }
  },
  "workloads": [
    {
      "name": "write-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "5",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10",
      "measurement_seed": 11599877,
      "measurement_order_us": [2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070]
    },
    {
      "name": "balanced",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "50",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10",
      "measurement_seed": 11599952,
      "measurement_order_us": [1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999]
    },
    {
      "name": "read-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "95",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10",
      "measurement_seed": 11600021,
      "measurement_order_us": [3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000]
    }
  ],
  "measurement_order_rule": "single random.Random(measurement_seed).shuffle over the ascending label list",
  "execution": {
    "records": 1000000,
    "threads": 48,
    "extime_s": 3,
    "performance_reps_per_cell": 5,
    "correctness_reps_per_cell": 5,
    "performance_trace_enabled": false,
    "correctness_trace_enabled": true,
    "jobs": 3,
    "one_workload_per_job": true,
    "cells_per_workload": 8,
    "total_cells": 24,
    "expected_performance_rep_observations": 120,
    "expected_correctness_rep_observations": 120,
    "shared_execution_constants_are_authoritative": false,
    "static_meaning_witness_status": "unestablished_for_positive_backoff_fixed_as_in_existing_sweep",
    "new_pointwise_meaning_witness_gate_required": false,
    "time_budget": {
      "sweep_cap_s": 11700,
      "pbs_walltime_s": 18000,
      "reduce_grid_or_reps_on_timeout": false
    }
  },
  "analysis_input_contract": {
    "abort_rate_source": "recomputed-from-integer-counters",
    "abort_rate_formula": "aborts / (aborts + commits)",
    "required_per_rep_integer_fields": ["abort_counts_", "commit_counts_"],
    "printed_abort_rate_is_not_an_analysis_input": true,
    "fallback_to_printed_abort_rate_allowed": false,
    "counters_currently_persisted_by_campaign_wal": false,
    "field_names_are_normalized_and_do_not_yet_exist_in_the_current_producer": true,
    "each_field_must_declare_its_source": true,
    "fields": [
      {"name": "backoff_us", "type": "integer", "unit": "microseconds",
       "wal_stage": "build_start", "payload_key": "genome",
       "source": "parse BACKOFF_FIXED out of the canonical genome string and decode it with the registered encoding rule; the decoded value must equal one registered grid value"},
      {"name": "per_rep_records", "type": "array[5] of object", "unit": "record",
       "wal_stage": "bench_done", "payload_key": "reps",
       "source": "the formal driver must persist this array; the current bench_done payload does not have it. Each element has exactly the keys rep_index, abort_counts_, commit_counts_, throughput_tps"},
      {"name": "abort_counts_reps", "type": "array[5] of nonnegative integer", "unit": "count",
       "wal_stage": "bench_done", "payload_key": "reps[].abort_counts_",
       "source": "bench stdout key abort_counts_ of that rep"},
      {"name": "commit_counts_reps", "type": "array[5] of nonnegative integer", "unit": "count",
       "wal_stage": "bench_done", "payload_key": "reps[].commit_counts_",
       "source": "bench stdout key commit_counts_ of that rep"},
      {"name": "abort_rate_reps_recomputed", "type": "array[5] of number in [0,1]", "unit": "dimensionless",
       "wal_stage": "derived", "payload_key": null,
       "source": "aborts/(aborts+commits) from the two counter arrays; never the printed abort_rate, and never the single leading_indicators.abort_rate of bench_done"},
      {"name": "throughput_tps_reps", "type": "array[5] of finite positive number", "unit": "transactions-per-second",
       "wal_stage": "bench_done", "payload_key": "tps",
       "source": "the existing per-rep throughput array of the bench_done payload; this array is authoritative for throughput, and reps[i].throughput_tps must equal tps[i] for every i"},
      {"name": "abort_rate_cv", "type": "number", "unit": "dimensionless",
       "wal_stage": "derived", "payload_key": null,
       "source": "computed from abort_rate_reps_recomputed"},
      {"name": "throughput_tps_cv", "type": "number", "unit": "dimensionless",
       "wal_stage": "bench_done", "payload_key": "cv",
       "source": "the existing throughput cv of the bench_done payload; this is the field the report surfaces as cv"},
      {"name": "rep_index", "type": "integer in 0..4", "unit": "index",
       "wal_stage": "bench_done", "payload_key": "reps[].rep_index",
       "source": "an explicit field written by the runner in rep order, not a positional guess made at read time"},
      {"name": "correctness_verify_records", "type": "array[5] of record", "unit": "verdict",
       "wal_stage": "verify_done", "payload_key": "certified",
       "source": "verify_done records of the admitted wal whose payload.build_attempt_id equals the committed attempt"},
      {"name": "correctness_anomalies", "type": "integer", "unit": "count",
       "wal_stage": "verify_done", "payload_key": "anomalies",
       "source": "must be 0 for every record"},
      {"name": "correctness_mode_coordinate", "type": "string", "unit": "mode",
       "wal_stage": "verify_done", "payload_key": "workload.tag",
       "source": "must equal the same coordinate recorded by the t2418-explore run of this family"},
      {"name": "trace_disabled_binary_sha256", "type": "string", "unit": "lowercase-hex-64",
       "wal_stage": "build_done", "payload_key": "perf_bin_sha256",
       "source": "the performance (trace-disabled) binary digest; the trace-enabled digest is a different key and must not be substituted"},
      {"name": "canonical_genome", "type": "string", "unit": "genome",
       "wal_stage": "build_start", "payload_key": "genome",
       "source": "canonical genome string of the admitted wal record"},
      {"name": "attempt_id", "type": "string", "unit": "identifier",
       "wal_stage": "build_done", "payload_key": "build_attempt_id",
       "source": "the committed attempt; every observation of a cell must carry the same value"},
      {"name": "source_run_kind", "type": "string", "unit": "identifier",
       "wal_stage": "campaign-envelope", "payload_key": null,
       "source": "derived from the formal campaign envelope and its lock, not from an observation payload"},
      {"name": "campaign_id", "type": "string", "unit": "identifier",
       "wal_stage": "campaign-envelope", "payload_key": null,
       "source": "derived from the formal campaign envelope and matched exactly against the trusted campaign lock"},
      {"name": "campaign_lock_digest", "type": "string", "unit": "lowercase-hex-64",
       "wal_stage": "campaign-lock", "payload_key": null,
       "source": "the trusted campaign lock of this workload job"},
      {"name": "wal_record_digest", "type": "string", "unit": "lowercase-hex-64",
       "wal_stage": "derived", "payload_key": null,
       "source": "sha-256 over the exact stored bytes of the wal jsonl line the observation was reconstructed from, without re-serializing the json"},
      {"name": "source_measurement", "type": "string", "unit": "identifier",
       "wal_stage": "derived", "payload_key": null,
       "source": "trace_disabled for observations reconstructed from bench_done, trace_enabled for records reconstructed from verify_done"}
    ],
    "campaign_lock_digest_covers": "sha-256 over the raw bytes of the campaign lock file",
    "any_field_without_a_resolvable_source_invalidates_the_cohort": true,
    "correctness_authority": "certified-field-of-each-committed-verify-record-in-the-formal-campaign-wal",
    "point_level_certified_field_is_not_the_correctness_authority": true,
    "report_level_verdicts_are_not_authoritative": true,
    "existing_report_field_cv_is_throughput_cv": true
  },
  "variability": {
    "metrics": ["abort_rate_recomputed", "throughput_tps"],
    "rep_count": 5,
    "sample_standard_deviation_ddof": 1,
    "cv_formula": "sample-standard-deviation-divided-by-arithmetic-mean",
    "maximum_cv_exclusive": 0.02,
    "all_zero_abort_cell_cv": 0.0,
    "failure_action": "invalidate-entire-formal-cohort"
  },
  "analysis": {
    "primary_metric": "abort_rate_recomputed",
    "throughput_role": "mandatory-cost-context-not-part-of-saturation-predicate",
    "abort_rate_point_estimator": "arithmetic-mean-of-five-reps",
    "also_report_median": true,
    "interval_axis": "adjacent-formal-tail-values-us",
    "slope_scale": "log-abort-rate-per-log-backoff-us",
    "canonical_effect_span": "one-backoff-doubling",
    "familywise_alpha": 0.05,
    "adjacent_intervals_per_workload": 6,
    "workload_count": 3,
    "simultaneous_intervals": 18,
    "one_sided_limits_per_interval": 2,
    "simultaneous_one_sided_limit_count": 36,
    "multiplicity_correction": "bonferroni",
    "per_limit_one_sided_alpha": 0.001388888888888889,
    "confidence_method": "delta-log-ratio-with-welch-satterthwaite-t",
    "formulas": {
      "abort_mean": "m_i = sum(a_i_r) / 5",
      "abort_cv": "cv_i = sample_sd(a_i_r) / m_i",
      "variance_term": "v_i = cv_i^2 / 5",
      "log_slope": "qhat_i = log(m_i / m_prev) / log(b_i / b_prev)",
      "log_slope_se": "se_i = sqrt(v_i + v_prev) / log(b_i / b_prev)",
      "welch_df": "nu_i = (v_i + v_prev)^2 / (v_i^2 / 4 + v_prev^2 / 4)",
      "t_quantile": "t_i = t_quantile(1 - 0.05/36, nu_i)",
      "simultaneous_lower_slope": "qL_i = qhat_i - t_i * se_i",
      "simultaneous_upper_slope": "qU_i = qhat_i + t_i * se_i",
      "maximum_abort_reduction_per_doubling": "U_i = 1 - exp(qL_i * log(2))",
      "minimum_abort_reduction_per_doubling": "L_i = 1 - exp(qU_i * log(2))",
      "flat_case_detectability_diagnostic": "U_flat_i = U_i evaluated with qhat_i set to 0 and observed cv values kept"
    },
    "preconditions_checked_before_taking_logs": {
      "counters_are_nonnegative_exact_integers": true,
      "abort_plus_commit_greater_than_zero": true,
      "throughput_finite_and_positive": true,
      "recomputed_abort_rate_within_unit_interval": true,
      "rep_index_is_exactly_zero_through_four_without_duplicates": true,
      "all_zero_left_cell_with_positive_right_cell": "invalid-cohort-before-any-log"
    },
    "interval_classification": {
      "evaluation_order": "first-match-wins",
      "single_table_no_separate_zero_abort_table": true,
      "rules": [
        {
          "state": "saturated",
          "reason": "both-adjacent-cells-all-zero-abort",
          "definition": "every rep of both cells has abort count 0",
          "no_logarithm_taken": true,
          "diagnostics": "qhat=qL=qU=0, U=L=0, U_flat=0"
        },
        {
          "state": "declining",
          "reason": "positive-to-all-zero",
          "definition": "left cell positive and every rep of the right cell has abort count 0",
          "no_logarithm_taken": true,
          "diagnostics": "qhat, qL, qU, U, L and U_flat are all null with the reason complete-reduction recorded"
        },
        {
          "state": "indeterminate",
          "reason": "zero-pooled-dispersion",
          "definition": "not one of the two rules above and v_i + v_prev == 0",
          "treating_se_as_zero_is_forbidden": true,
          "observed_in_existing_artifacts": true,
          "diagnostics": "qL, qU, U, L and U_flat are all null with the reason recorded"
        },
        {
          "state": "saturated",
          "definition": "qhat_i <= 0 and U_i <= 0.05"
        },
        {
          "state": "declining",
          "definition": "L_i > 0.05"
        },
        {
          "state": "indeterminate",
          "reason": "cannot-distinguish-flat-from-declining",
          "definition": "none-of-the-above"
        }
      ],
      "u_flat_is_reported_but_not_used_for_classification": true,
      "states_are_mutually_exclusive_and_exhaustive": true,
      "all_zero_left_cell_with_positive_right_cell_is_handled_by_the_preconditions": true
    },
    "saturation_location": {
      "requires_persistence_to_the_representation_cap": true,
      "tail_point_indexing": "b_1=1250, b_2=1768, b_3=2500, b_4=3535, b_5=5000, b_6=7070, b_7=9999",
      "interval_indexing": "I_i = (b_i, b_(i+1)) for i in 1..6",
      "rule": "smallest j such that intervals I_j..I_6 are all saturated and the run length is at least 2",
      "reported_location_when_j_at_least_2": "b_j",
      "reported_bracket_when_j_at_least_2": "[b_(j-1), b_j]",
      "reported_location_when_j_equals_1": "at-or-below-1250us-left-censored",
      "reported_bracket_when_j_equals_1": "no-lower-endpoint",
      "reporting_j_equals_1_as_the_point_1250_is_forbidden": true,
      "leftmost_two_sided_bracketable_location_us": 1768,
      "local_flat_pairs_that_do_not_persist": "disclosed-as-local-flat-region-not-a-saturation-location"
    },
    "per_workload_state": {
      "rules": [
        {"state": "indeterminate", "definition": "indeterminate_interval_count >= 1"},
        {"state": "saturated", "definition": "indeterminate_interval_count == 0 and a persistent saturation location exists"},
        {"state": "not-observed", "definition": "indeterminate_interval_count == 0 and no persistent saturation location exists"}
      ],
      "conditions_are_mutually_exclusive_without_relying_on_order": true,
      "indeterminate_is_not_evidence_of_non_saturation": true
    },
    "aggregate_verdict": {
      "evaluation_order": "first-match-wins",
      "rules": [
        {"verdict": "invalid", "definition": "any failure condition holds"},
        {"verdict": "indeterminate-in-region", "definition": "at least one workload state is indeterminate"},
        {"verdict": "saturated-in-all-workloads", "definition": "all three workload states are saturated"},
        {"verdict": "not-observed-in-any-workload", "definition": "all three workload states are not-observed"},
        {"verdict": "not-observed-in-at-least-one-workload", "definition": "none of the above"}
      ],
      "exactly_one_verdict_applies": true
    },
    "no_saturation_wording": "no-preregistered-saturation-observed-within-the-representable-domain-through-9999us",
    "stopping_rule_kind": "reporting-rule-after-full-grid-not-measurement-early-stop"
  },
  "correctness": {
    "separate_trace_enabled_build_required": true,
    "required_verdict": "certified",
    "verdict_location": "committed-verify-record-payload-in-the-formal-campaign-wal",
    "maximum_anomalies_per_rep": 0,
    "all_reps_for_all_cells_required": true,
    "failed_cell_may_reach_performance_measurement": false,
    "reduce_correctness_reps_for_time": false,
    "correctness_mode_must_be_recorded": true,
    "correctness_mode_coordinate": "verify_done payload workload.tag",
    "correctness_mode_must_equal_the_t2418_explore_value_of_that_coordinate": true,
    "this_document_does_not_invent_a_mode_name": true,
    "verify_records_per_cell": 5,
    "current_family_emits_one_verify_record_per_cell": true,
    "emitting_five_is_a_precondition_not_an_assumption": true,
    "failure_action": "invalidate-entire-formal-cohort"
  },
  "binary_identity": {
    "physical_amounts_us": [1000, 1250, 1768, 2500, 3535, 5000, 7070, 9999],
    "expected_trace_disabled_build_results_per_workload": 8,
    "digest_is_the_trace_disabled_performance_binary": true,
    "trace_enabled_binary_digest_must_not_be_substituted": true,
    "require_exact_build_result_type": true,
    "require_canonical_genome_binding": true,
    "require_full_lowercase_sha256": true,
    "require_complete_amount_set_equality": true,
    "require_all_binary_sha256_values_distinct": true,
    "generic_helper_that_passes_on_fewer_than_two_amounts_may_not_be_the_only_check": true,
    "failure_action": "invalidate-entire-formal-cohort"
  },
  "provenance": {
    "required_per_observation_fields": [
      "source_run_kind",
      "campaign_id",
      "campaign_lock_digest",
      "attempt_id",
      "rep_index",
      "wal_record_digest",
      "canonical_genome",
      "source_measurement"
    ],
    "derived_from": "admitted-wal-envelope-of-the-formal-campaign",
    "self_declared_observation_payload_is_not_trusted": true,
    "campaign_id_and_lock_digest_must_match_the_trusted_campaign_lock_exactly": true,
    "source_run_kind_must_equal_the_formal_run_kind": true,
    "analysis_reconstructed_from": "admitted-wal-of-the-formal-campaign",
    "input_report_verdicts_are_not_authoritative": true
  },
  "cohort_identity": {
    "scope": "the three workload jobs form one cohort and must agree",
    "must_match_across_all_three_campaign_locks": [
      "ccbench_source_digest",
      "toolchain",
      "environment_contract_identity",
      "calibration_identity",
      "preregistration_commit",
      "preregistration_document_blob_sha256",
      "spec_sha256",
      "records",
      "threads",
      "extime_s",
      "performance_reps_per_cell",
      "correctness_reps_per_cell"
    ],
    "workload_coordinates_must_not_match_across_jobs": true,
    "workload_rules": {
      "each_lock_must_equal_its_own_registered_row": true,
      "the_three_workload_names_must_cover_the_registered_set_exactly_once": [
        "write-heavy",
        "balanced",
        "read-heavy"
      ]
    },
    "mismatch_action": "invalidate-entire-formal-cohort",
    "existing_submission_time_conditions_are_not_relaxed": true
  },
  "failure_conditions": {
    "scope": "any-failure-invalidates-the-entire-formal-cohort-for-the-preregistered-claim",
    "items": [
      "any-of-24-cells-lacks-five-certified-correctness-reps-or-has-any-anomaly",
      "a-correctness-failing-cell-reaches-performance-measurement",
      "integer-abort-and-commit-counters-are-not-persisted-per-rep",
      "analysis-uses-the-printed-four-decimal-abort-rate",
      "the-eight-trace-disabled-build-results-are-incomplete-mis-bound-truncated-or-not-all-distinct",
      "any-workload-point-or-rep-is-missing-duplicated-nonfinite-or-out-of-registered-range",
      "any-cell-abort-or-throughput-cv-is-at-or-above-0.02",
      "any-adjacent-interval-has-qL-greater-than-zero",
      "the-sweep-exceeds-11700-seconds-or-the-job-does-not-reach-completion-within-18000-seconds",
      "a-job-is-interrupted-and-resumed-without-identical-campaign-identity-preregistration-commit-spec-sha-source-and-toolchain",
      "exploration-samples-enter-formal-reps-cv-intervals-or-verdicts",
      "the-preregistration-commit-blob-sha256-or-spec-sha256-is-unrecorded-or-mismatched",
      "a-counter-is-negative-non-integer-or-abort-plus-commit-is-zero",
      "a-throughput-value-is-non-positive-or-non-finite",
      "a-recomputed-abort-rate-falls-outside-the-unit-interval",
      "rep-indices-are-not-exactly-zero-through-four-without-duplicates",
      "an-interval-has-an-all-zero-left-cell-and-a-positive-right-cell",
      "a-required-provenance-field-is-missing-or-disagrees-with-the-wal-envelope",
      "source-run-kind-is-not-the-formal-run-kind",
      "an-execution-literal-measurement-order-workload-coordinate-or-label-physical-raw-genome-correspondence-differs-from-the-registered-value",
      "the-three-campaign-locks-disagree-on-any-cohort-identity-field",
      "the-correctness-mode-is-unrecorded-or-differs-from-the-t2418-explore-mode",
      "the-trace-enabled-binary-digest-is-used-in-place-of-the-trace-disabled-one",
      "a-per-rep-throughput-value-disagrees-with-the-same-index-of-the-authoritative-tps-array"
    ],
    "confirmed_nonmonotonicity": {
      "definition": "qL_i greater than zero for any adjacent interval",
      "action": "invalidate-saturation-and-no-saturation-claims"
    },
    "unconfirmed_upward_wiggle": {
      "definition": "qhat_i greater than zero and qL_i less than or equal to zero",
      "action": "report-and-do-not-count-that-interval-as-saturated"
    },
    "cross_campaign_cell_pooling_allowed": false,
    "failure_reporting": "report-all-observed-values-and-the-failure-reason-as-descriptive-only"
  },
  "future_driver_binding": {
    "must_parse_entire_spec": true,
    "code_constants_may_override_spec": false,
    "run_kind": "t2500-tail-formal",
    "report_schema": "t2500-backoff-static-tail-formal-report/v1",
    "artifact_stem": "t2500-backoff-static-tail-formal",
    "forbidden_existing_run_kinds": ["extended", "t2266-tail", "t2418-explore"],
    "campaign_identity_must_be_disjoint_from_existing_series": true,
    "existing_series_acceptance_sets_may_change": false,
    "existing_series_artifacts_may_change": false,
    "existing_series_report_schemas_may_change": false,
    "extended_sweep_us_constant_may_change": false,
    "exploration_artifacts_may_be_consumed_as_formal_samples": false,
    "preconditions_before_formal_submission": [
      "a-consumer-parses-this-spec-and-its-firing-is-demonstrated",
      "per-rep-integer-abort-and-commit-counters-of-the-performance-run-are-persisted-in-the-wal-and-verified",
      "per-observation-provenance-fields-are-emitted-and-derivable-from-the-wal-envelope",
      "five-verify-records-per-cell-are-actually-emitted-the-current-family-emits-one",
      "the-correctness-mode-coordinate-is-recorded-and-comparable-to-the-t2418-explore-value"
    ],
    "preconditions_cannot_be_satisfied-by-documentation-alone": true
  }
}
```
<!-- IZANAGI-B10-STATIC-TAIL-SPEC-END -->

## 6. 検出力について主張しないこと

- **5 rep が特定の効果量に対する検出力を保証するとは主張しない。** 本書は事前の検出力計算を
  据え置く代わりに、走行ごとに区間を `saturated` / `declining` / `indeterminate` の 3 つへ分け、
  どちらとも言えない区間を正直に `indeterminate` として出す方法を採る (§4.4)。
- **参考値 (非規範。分類には使わない)。** 探索で印字された abort 率から再計算した最大の変動係数
  (0.0061515) を両端に置き、自由度 8、36 の片側限界に対する t 分位点 (4.2556) で評価すると、
  半オクターブ区間の `U_flat` は 3.26% で 5% 基準に届く。対数比が 0.11 程度しかない短い区間では
  9.78% になり、真に平坦でも 5% 基準に届かない。**この差が §4.1 で上限アンカーの均一格子を
  選んだ理由である。**
  この 2 つの数字は**量子化された率から作った変動係数に基づく試算**であって、§4.7 が禁じている
  「量子化率を精度の根拠に使うこと」を判定へ持ち込むものではない。格子設計の説明にだけ使う。
- 変動係数の gate (0.02) は検出可能性を保証しない。gate を通っても判別できない区間はありうる。
  だから gate と 3 分割の両方を持つ。
- 本書の外側の分解能 — CCBench が印字する値の精度 — は §4.3 の再計算で外している。
  それでも残る分解能の限界 (整数カウンタそのものの粒度) については何も主張しない。

## 7. 失敗条件

次のいずれかが起きたら、登録した飽和・域内非飽和の**いずれの主張にも使わない**。
観測値は失敗理由とともに全件を記述的に報告する (隠さない)。

1. 24 cell のどれかで、trace 有効の正しさ検査 5 rep が揃わない、`certified` でない、
   または anomaly が 1 件以上ある。
2. 正しさに不合格の cell が性能測定へ到達した。
3. rep ごとの整数カウンタ (`abort_counts_` / `commit_counts_`) が保存されていない。
4. 解析が小数第 4 位に丸めた `abort_rate` を入力に使った。
5. 静的 8 genome の trace 無効ビルド成果物が、完全に揃わない、genome 束縛が違う、
   SHA-256 が完全長でない、または 8 個の中に同値がある。
6. workload・格子点・rep のいずれかが欠測、重複、非有限、または登録集合の外である。
7. cell の abort 率または throughput の変動係数が 0.02 以上である。
8. 統計的に支持された abort 率の上昇 (`qL > 0`) が 1 区間でもある。
   この場合、単調な tail を前提とする飽和位置・域内非飽和の**両方**の主張を行わない。
9. sweep が 11700 秒を超えた、または PBS の 18000 秒以内に完了へ到達しなかった。
10. job が途中終了し、同一 campaign identity・同一の事前登録 commit と spec SHA・
    同一 source と toolchain に束縛された resume 以外で再開した。別 campaign の cell を継ぎ合わせない。
11. 探索の標本が本格の rep・変動係数・区間・判定のいずれかへ入った。
12. 事前登録の commit・blob SHA-256・spec SHA-256 のいずれかを記録していない、
    または実行時の bytes と一致しない。
13. **観測の型・範囲が §4.6 の要求を満たさない。** abort 回数・commit 回数が非負整数でない、
    `abort + commit == 0`、throughput が非正または非有限、abort 率が `[0, 1]` の外、
    rep の添字が `0..4` の重複なし全数でない。
14. **左端 cell が全 rep で abort 0、右端 cell が正値**である区間がある (対数を取る前に判定する)。
15. **出所の必須 field が欠けている、または WAL の envelope から導出した値と一致しない。**
    `source_run_kind` が本走の run kind でない場合を含む。
16. **動作点の literal・測定順・label と物理値と raw 値と genome の対応**のいずれかが
    §4.1 / §4.2 の登録値と一致しない。ある job の workload 座標が、§4.2 に登録した
    **その job 自身の行**と一致しない場合も含む。
17. **3 job の間で §4.9 の同一性が成り立たない**、または 3 job の workload 名の集合が
    登録した 3 つを重複なく過不足なく覆っていない。
18. 正しさ検査の mode を記録していない、または探索走 `t2418-explore` と同じ mode でない。
19. **同じ rep の throughput が 2 か所で食い違う。** rep ごとの記録に載せた throughput が、
    既存の throughput 配列の同じ添字の値と一致しない。既存配列を権威とし、不一致は失敗にする。

## 8. 発効・束縛・本走 driver への要求

### 8.1 投入前条件 (これを満たすまで本格 cohort を投入しない)

1. **本書の spec を parse する consumer が実装され、その発火が実測で示されていること。**
   現時点で consumer は存在しない。本書だけでは後続走を機械的に拘束しない (§1)。
2. **性能測定の rep ごとの整数カウンタが WAL へ保存され、abort 率の再計算経路が実測で
   確かめられていること** (§4.3)。現状の `bench_done` は rep ごとの abort 率も整数カウンタも
   持たない。`verify_done` が `commits` / `aborts` を整数で持っているのは trace 有効側の値であり、
   代用できない。
3. **observation ごとの出所 field が発行され、WAL の envelope から導出できること** (§4.8)。
4. **1 cell あたり 5 本の正しさ記録が実際に発行されること** (§4.6)。現状は 1 本である。
5. **正しさ検査の mode の座標が記録され、探索走の値と比較できること** (§4.6)。
   現状の report にはこの field が無い。

**これらは docs だけでは満たせない。** どれも次 wave の実装で満たし、実測で確かめてから投入する。

### 8.2 本走 driver への要求

- 上記 marker 間の JSON 全体を parse し、格子・動作点・測定順・判定値をコードの定数で置換しない。
- 初回の本格投入時に、本書を含む commit hash・本書の blob SHA-256・spec の SHA-256 を
  campaign lock・report・完了成果物へ記録する。

**hash の対象 bytes を一意に決める。** 曖昧なままだと、同じ文書での走行が読み手の解釈だけで
valid にも invalid にもなる。

- `document_blob_sha256` = **file の raw bytes** の SHA-256。Git の blob header は含めない。
- `spec_sha256` = §5 の**開始 marker 行の次の行から、終了 marker 行の前の行まで**を取り出し、
  そこから先頭の code fence 行 (` ```json `) と末尾の code fence 行 (` ``` `) を除いた残りの
  **UTF-8 bytes** の SHA-256。改行は LF、末尾の改行を 1 つ含める。JSON の再整形・キー並べ替えは
  行わない (canonical 化しない)。取り出した bytes がそのまま JSON として parse できることも要求する。
- `run_kind` は `t2500-tail-formal`、report schema は
  `t2500-backoff-static-tail-formal-report/v1`、成果物 stem は
  `t2500-backoff-static-tail-formal` とする。いずれも本書の v1 時点で repo 内に出現が無いことを
  確認済みである。
- 既存 3 系列 (`extended` / `t2266-tail` / `t2418-explore`) の受理集合・成果物・report schema を
  変更しない。`EXTENDED_SWEEP_US` とその上端を pin しているテストも変更しない。
- 探索走の成果物を本格 loader の入力にしない。

## 9. 本書が閉じないもの

- **機序。** なぜ abort 率がこの形で下がるのかは本書の対象外である (D1678)。
- **9999 マイクロ秒より右。** 符号化を変えない限り測れない。本書は符号化の変更を提案しない。
- **正値 `BACKOFF_FIXED` の pointwise meaning witness。** 既存 sweep 全体と同じく未確立のままである。
  gate の新設は [T-2501] としてユーザー裁定待ちである。
- **性能の認証。** 本走は trace 無効の性能測定であり、認証されるのは正しさだけである。
- **他環境への転移。** 本書が固定するのは Pegasus 計算ノード 48 スレッド・YCSB 3 workload・
  silo protocol の条件下の測定である。

## 2026-09-10 追補 — 静的物理量の意味宣言と T-2418 新走の v2

D1859・D1936 項19に従い、既存 driver が要求する静的物理量を既存の意味宣言へ渡す。
期待値は要求側の物理マイクロ秒から作り、捕捉した C++ の観測値や符号の decoder から逆算しない。
screening でも同じ宣言を転送し、乱択設定を静的 scalar と宣言しない。共通 gate の判定式は変更しない。

この変更後の `t2418-explore` 新走は `scale` / `trial` を
`t2418-backoff-static-explore-v2`、`spec_slug` を
`t2418-backoff-static-explore-v2-silo-<workload>`、JSON report schema を
`t2418-backoff-static-explore-report/v2` とする。campaign 設定・JSON report・DAT provenance の
`meaning_witness_status` は `driver_declared_static_backoff_physical_us` に揃える。
これは要求側が静的物理量を宣言することを表し、全 macro の意味確立や性能認証を表さない。
新走の loader は v2 の campaign を選び、v1 への fallback は設けない。

§5 の本格系列 spec は変更対象外として保持し、T-2418 新走の status は本追補に従う。
§9 の「未確立」は本追補前の記述として保持する。
§8.2 の既存系列不変更は過去 artifact に適用し、今回の新走版には本追補を適用する。
旧 campaign の lock・WAL・report と記録された測定事実は変更せず、現行 gate の結果で
過去の意味状態を遡及的に昇格させない。§5 の本格系列 spec の bytes、格子・反復数・測定順・
停止基準は本追補で変更しない。
