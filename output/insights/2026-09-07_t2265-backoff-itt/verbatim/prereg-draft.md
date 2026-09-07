# adaptive backoff の反実仮想対照 — 事前登録

`patches/cicada-adaptive-counterfactual.patch` が入れた 3 値の step policy を使い、「制御器が選んだ
一歩の向きは、次の窓の throughput を変えるか」を測る試験の事前登録である。機構の一次資料は
`output/insights/2026-09-07_t2265-backoff-counterfactual/README.md`。測定対象の protocol は Silo
(`ycsb_silo.exe`) で、「Cicada」は adaptive backoff 算法の由来を指す。

## 0. 本書の版と発効

**v1 (2026-09-07)。** dev-wave `t2265-backoff-itt` の段 4 で凍結し、**反実仮想の腕の結果を 1 つも
見る前に** commit した。本走は本書を含む commit を指して起動し、成果物 JSON はその commit hash
(`repo_head`) と本書の bytes の sha256 を `counterfactual_preregistration` へ記録する。結果 commit より
後に書かれた変更は事前登録として数えない。発効後の変更は旧版を Git 履歴に残したまま新しい commit で
行い、変更理由と時点を本節へ明記する。

**旧事前登録 `docs/dynamic-backoff-preregistration.md` は本試験を覆わない。** 旧書は 7 腕の run 単位
throughput 比 (等価域 ±3%) を固定したもので、腕 `cw-as-dyn-p1` / `cw-as-dyn-p2`、seed、更新単位の
ITT、その等価域を一度も固定していない。成果物が記録する `prereg_sha256` は旧書を指し続けるが、
それが束縛するのは旧書が定めた測定条件 (workload、records、build、patch stack) だけであり、
**本試験の推定量と判定は本書だけが束縛する。**

**本書は盲検の holdout ではない。** 下記の 2 つの既存実測を見たうえで層・等価域・反復数を決めている。
前向きに固定できるのは「反実仮想の腕の出力を一度も観測していない時点で §2〜§8 を固定した」ことだけである。

- 既存の v1 診断走行 (job `0:978021.nqsv`、policy 0 と同じ更新則) の更新数・窓 log 比の散らばり・
  実現 backoff の分布。逐語は `output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-measurements.md`。
- 48 スレッド write-heavy の静的 backoff 曲線 (`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md`)。
- 反実仮想の腕そのものの**構造データ** (job `0:981337.nqsv`、生死確認)。**outcome は見ていない。**
  見たのは event 数・割当比・割当前の両方向可否・反転の実現率・trace の版だけで、検査器は field を
  allowlist で絞ったうえで artifact を開く前に書いた。逐語は
  `output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-liveness.md` と
  同 dir の `stage1-liveness-inspector.py`。**この job の成果物は本試験の証拠に数えない。**

## 1. 主張してよい範囲と限界

- **主推定量は trace 有効 build で測る。** 絶対規律 1 に従い、この build の throughput は性能主張に
  使わない。成果物は `throughput_scope=diagnostic_only` / `headline_eligible=false` を記録する。
  **本書の主判定は「機構の局所効果」についてのものであって、throughput の性能結果ではない。**
  対比は同一 build・同一 run の中の更新どうしで取るので、観測者効果は両群に共通であり対比を交絡しない。
- **すべて未認証である。** policy≠0 の cell は現行の直列性認証の exact 2 cell 契約に入らない。
  本試験は正しさを主張せず、認証は本 wave の scope 外に置く (次の一手)。
- 単一環境 (Pegasus gen_S、48 物理コア、HT 無効)、単一 protocol (Silo)、YCSB 3 workload、
  records 1,000,000 の下でしか言えない。
- **同一軌跡上の反実仮想ではない。** policy 2 は「同じ pre-state から推奨した一歩と逆の一歩」を
  更新ごとに無作為化するが、更新 i の pre-state 自体は先行する割当の結果である。
  したがって推定するのは「混合方策の軌跡のまわりで 1 歩を反転させたときの限界効果」である。
- 方向的中率は処置効果の推定量ではない。本書はそれを判定に使わない。

## 2. 腕と割当

機械 label と exact な cell 文字列 (12 field 書式):

| label | cell 文字列 | 役割 |
| --- | --- | --- |
| `cw-as-dyn-p0` | `cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0` | stock の更新則 (反転なし) |
| `cw-as-dyn-p1` | `cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1` | 常に反転 |
| `cw-as-dyn-p2` | `cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2` | 更新ごとに 1/2 で反転 (**主推定量の腕**) |

policy 2 の割当は、更新ごとに 1 回だけ進む 64 bit LCG
`state <- state * 6364136223846793005 + 1442695040888963407 (mod 2^64)` の bit 63 である。
LCG は**勾配 0・推奨差分 0・clamp のときも毎更新で進む**ので、割当列は run の物理過程と独立である
(patch C の該当行で確認済み)。反転は clamp の**前**に当たるので、反転した一歩も clamp されうる。
`both_actions_feasible` は**割当を当てる前**の pre-state から決まる。

## 3. 測定条件

| 項目 | 値 |
| --- | --- |
| workload | write-heavy (rr 5) / balanced (rr 50) / read-heavy (rr 95)、zipf 0.9、rmw 0、max_ope 10 |
| threads | 24, 48 |
| records | 1,000,000 |
| extime | 3 秒、1 job あたり 1 rep、rep index 0 |
| build | trace 有効 (`BACKOFF_TRACE=1`)。診断専用 |
| ccbench | pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` + patch A (`9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b`) + patch B (`f3fe6b7e67931775bcef0a7831dda8c6cb53dfc7fc52a74f4508360e1fedf824`) + patch C (`794b7b48dd19e30560dddc27f4408d67923d801241046df53257a8aefe82a396`)、`patch_stack_sha256` = `192be42db83b314b0eddd399eb47d6a47ac7afb859bc7085cd5f035e8cd7433c` |
| driver | `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` の `--backoff-trace` |
| 反復 | 独立 seed 12 本 = 12 job。1 job が 3 腕 x 3 workload x 2 threads = 18 run を回す |

## 4. 主推定量

run j の更新 i について、trace の窓から `T = window_commits / window_us` を作り、

- **outcome** `Y_ij = ln(T_{i+1,j} / T_{i,j})` — 更新 i の直前の窓から、更新後の backoff が支配する
  次の窓への log 変化。`T` が 0 になる更新は outcome が定義できないので落とす (割当と独立)。
- **run 内効果** `d_j = mean{Y_ij : Z_ij = 1} - mean{Y_ij : Z_ij = 0}`。`Z` は `assigned_invert`。
- **主推定量** `D = mean_j d_j`、run を cluster とする。95% CI は t 分布 (n=12 なら t_{0.975,11}=2.201)、
  `D +- t * s_d / sqrt(n)`。表示は `100 * (exp(x) - 1)` % で行う。

**主層は (write-heavy, 48 threads, `cw-as-dyn-p2`) の 12 run だけ。** 他の 5 つの (workload, threads) は
副次であり、主判定に使わない。

**主層の根拠 (結果を見る前に固定した実測):** 既存 v1 診断で、この regime だけ backoff が 0 の床を離れ
(中央値 5〜6 µs、p90 10〜11 µs、最大 17〜21 µs)、勾配 0 の更新が 0.1〜0.3% しかない。他の regime は
backoff 中央値 0〜2 µs で更新の 39〜51% が勾配 0 であり、反転しても差分が 0 のままで腕が届かない。

## 5. 等価域と検出力

- **等価域は次窓 throughput 比 [0.97, 1.03] (±3%、log で ±0.02956)。** 旧事前登録および B-10 と同じ幅を
  使う。この幅を採るのは、静的 backoff 曲線 (§0 の 2 本目) で制御器の滞在点 (b ≈ 5〜6 µs) が曲線の頂点に
  あり、順方向と逆方向が作る b の差 2δ (δ = 刻み 1〜4 µs) を当てると、静的曲線の内挿では次窓の log
  throughput が数 % 動きうるからである。**機構が効いているなら ±3% の外に出る幅**であり、恒真な等価判定に
  ならない。静的曲線は定常応答であり過渡応答ではないので、効果量の予測にだけ使い判定式には使わない。
- **検出力の見積り (結果を見る前):** 既存 v1 診断の write-heavy 48 で、窓 log 比の標準偏差は
  0.1197〜0.3379、run 内で半々に割った平均差の標準誤差は 0.0082〜0.0231 (log) だった。
  生死確認の実測では主層 (policy 2、write-heavy 48) の event 数は **583** で、v1 診断の 844〜985 より
  少ない。同じ標準偏差なら run 内 SE は `0.34 * sqrt(4/583) = 0.0282` が上限になる。
  run 間の `d_j` の散らばりがこれと同程度なら、n=12 で CI の半幅は
  `2.201 * 0.0282 / sqrt(12) = 0.0179` = 1.8% となり、±3% の等価域を解像できる。
  **半幅が 3% を超えた場合は「解像できなかった」と書き、等価と呼ばない。**

判定語 (主層について):

- **効果あり**: CI が 0 を含まず、かつ CI のいずれかの端が等価域の外。
- **等価**: CI 全体が [-3%, +3%] の内。
- **inconclusive**: それ以外。**非有意を等価と呼ばない。**

## 6. 層と副次解析

副次は記述であり、主判定を置き換えない。多重比較の補正はせず、副次はすべて探索的と書く。

1. (workload, threads) の残り 5 組それぞれの `d_j` と CI。
2. `recommended_delta_sign` (+1 / -1 / 0) による層別。
3. `both_actions_feasible` (0 / 1) による層別。
4. run 内の時間 block (更新 index の前半 / 後半) による層別。
5. 腕どうしの記述比較 (`p1` と `p0` の median_tps)。**trace 有効 build の値なので性能主張に使わない。**

**2〜4 の層別変数はいずれも更新 i の時点では pre-state だが、先行する割当に対しては処置後である。**
したがってこれらの層内の対比は因果効果として解釈せず、機序の手がかりとしてだけ読む。

## 7. 除外規則

- **落としてよいのは 2 つだけ:** (a) run の最後の更新 (次の窓が無い)、(b) `T_i` または `T_{i+1}` が 0 で
  outcome が定義できない更新。どちらも割当と独立である。
- **禁止する除外:** clamp が当たったか、実適用差分が 0 か、`inversion_realized`、outcome の値、
  および結果を見てからの run・層の取捨。**これらはすべて処置後の量である。**
- run が 1 本でも欠けたら欠けたまま報告し、代わりの run を足さない。

## 8. seed と停止規則

- **seed 12 本** (10 進、`CCBENCH_BACKOFF_STEP_POLICY_SEED` へ与える 64 bit 値):
  既定 `11400714819323198485` と、`splitmix64` を既定 seed に順次適用して得る 11 本。
  実際の 12 値は §8.1 に逐語で列挙し、driver が artifact へ記録する。
- **停止規則:** 12 job を投入し、完走した job だけを使う。**結果を見てから job を足さない。**
  中間解析をしない。job が失敗した場合は同じ seed で 1 度だけ再投入してよく、その事実を記録する。
- 12 job すべてが失敗した場合は「測定できなかった」と書き、判定を出さない。

## 8.1 seed の逐語一覧

seed 1 は patch C の既定値 `11400714819323198485` (= `0x9E3779B97F4A7C15`) である。seed 2〜12 は
`splitmix64` を seed 1 を初期状態として順に 11 回進めた出力である
(`state += 0x9E3779B97F4A7C15; z = state; z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9;
z = (z ^ (z >> 27)) * 0x94D049BB133111EB; return z ^ (z >> 31)`、すべて mod 2^64)。

| # | seed (10 進) | 最初の 16 割当 (bit 63、1 = 反転) | 先頭 1000 割当の平均 |
| ---: | ---: | --- | ---: |
| 1 | 11400714819323198485 | `0111001000100110` | 0.517 |
| 2 | 7960286522194355700 | `0011010111110001` | 0.534 |
| 3 | 487617019471545679 | `1011011110111100` | 0.508 |
| 4 | 17909611376780542444 | `1000100110110000` | 0.488 |
| 5 | 1961750202426094747 | `0100010110110011` | 0.491 |
| 6 | 6038094601263162090 | `0010000000101110` | 0.480 |
| 7 | 3207296026000306913 | `0011110101110010` | 0.519 |
| 8 | 14232521865600346940 | `1110011010111110` | 0.483 |
| 9 | 4532161160992623299 | `1011001010111110` | 0.500 |
| 10 | 17561866513979060390 | `1101100111110010` | 0.488 |
| 11 | 7313543279846440201 | `0010110000110001` | 0.487 |
| 12 | 14038607207048404726 | `1011000111111010` | 0.474 |

12 値は相異なり、いずれも 0 でない。seed 1 の最初の 16 割当は、機構の一次資料が実装を読まずに
式から独立に再計算した値と一致する。

**seed を複数使う理由。** 割当 Z_i は seed と更新 index だけで決まる決定的な列である。同じ seed の
run はどれも同一の割当列を持つので、その列が run の周期的な物理過程と偶然そろった場合、その偏りは
run を増やしても平均化されない。独立な seed はこの偏りを平均化する。

**無作為化の検査 (pre-treatment):** 各 run の実測割当比 (Z=1 の割合) を記録し、0.5 から大きく外れる
run があればその事実を報告する。**この検査の結果で run を除外しない。**

## 9. 記録する束縛

各成果物 JSON に次を記録する: `repo_head`、`counterfactual_preregistration` (本書の sha256)、
`prereg_sha256` (旧書の sha256、測定条件の束縛)、`patch_stack` と各 sha256、`binary_sha256`、
`step_policy`、`step_policy_seed`、`hostname`、`pbs_jobid`、`measured_utc`、
`backoff_trace_symbol_count` / `backoff_trace_string_count`、`throughput_scope`、`headline_eligible`。
