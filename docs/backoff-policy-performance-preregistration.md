# adaptive backoff の step policy 腕 — trace 無効な性能の事前登録

`patches/cicada-adaptive-counterfactual.patch` が入れた 3 値の step policy (`cw-as-dyn-p0` /
`cw-as-dyn-p1` / `cw-as-dyn-p2`) について、**trace 無効な build における端から端までの throughput** を
測る試験の事前登録である。測定対象の protocol は Silo (`ycsb_silo.exe`) で、「Cicada」は adaptive
backoff 算法の由来を指す。機構の一次資料は
`output/insights/2026-09-07_t2265-backoff-counterfactual/README.md` と
`output/insights/2026-09-07_t2265-backoff-itt/README.md`。

## 0. 本書の版と発効

**v1 (2026-09-08)。** dev-wave `t2417-policy-arm-perf` の段 4 で凍結し、**3 腕の trace 無効な
throughput を 1 つも見る前に** commit した。本走は本書を含む commit を指して起動し、成果物 JSON は
本書の bytes の sha256 を `backoff_policy_performance_prereg_sha256` へ記録する。結果 commit より
後に書かれた変更は事前登録として数えない。発効後の変更は旧版を Git 履歴に残したまま新しい commit で
行い、変更理由と時点を本節へ明記する。

**旧 2 事前登録は本試験を覆わない。**

- `docs/dynamic-backoff-preregistration.md` は 7 腕 (`none` / `stock` / `tuned` / `tuned-u10240` /
  `cw` / `cw-as` / `cw-as-dyn`) の trace 無効 throughput を固定したもので、**step policy を持つ腕を
  1 つも含まない** (patch C 適用前の腕である)。成果物が記録する `prereg_sha256` は旧書を指し続けるが、
  それが束縛するのは旧書が定めた共通の測定条件 (workload の定義、records、build の trace 無効性、
  patch A / B) だけであり、**本試験の腕・順序・反復・推定量・判定は本書だけが束縛する。**
- `docs/backoff-counterfactual-preregistration.md` は同じ 3 腕を扱うが、**trace 有効な診断系における
  1 窓先の局所 ITT** を固定したものである。絶対規律 1 に従い、その build の commit 速度は性能主張に
  使えない。本書はその制約を受けない別 build・別 run の試験を固定する。

### 0.1 本書は盲検の holdout ではない — 見たものを列挙する

前向きに固定できるのは「**指定した outcome を一度も観測していない時点で** §1〜§9 を固定した」ことだけ
である。設計は次を見たうえで決めている。**data-informed な前向き protocol であって、未観測からの
設計ではない。**

1. **反実仮想 3 腕の構造データ** (ITT の段 1 生死確認、job `0:981337.nqsv`)。見たのは割当比・
   割当前の両方向可否・反転の実現率であり、そこから「policy 0 の反転率 0.000、policy 1 は 1.000、
   policy 2 は 0.517〜0.530」「policy 1 の write-heavy 48 だけ割当 1.000 に対し実現 0.492」を
   知っている。**これは処置に依存する構造量である。**§6 の主点の指定に使った。
2. **ITT の主判定が `inconclusive` に終わったこと**と、その原因が事前登録した除外規則
   (`window_commits = 0` の event) の発火であること。**ITT の推定値そのものは見ていない**
   (先行 wave は `seq = 0` を除いた推定値を計算していない)。§7 の欠測規則を層に分ける根拠に使った。
3. **既存 7 腕の trace 無効性能 block** (`stage1-rep0..rep6`) の `cell_order`・hostname・
   所要時間・軸。**throughput の値は見ていない。** §3 の軸と §5 の見積もりに使った。
   これらの block は step policy 腕を含まない。
4. **T-2187 が報告した block 単位 log 比の CI 幅 (±1.0〜1.4%、n=7)。** §5 の標準偏差の想定に使った。
   これは step policy 腕の値ではない。

**見ていないもの (指定 outcome):** 3 腕の trace 無効な `median_tps`、その比、`abort_rate`、
本書が判定に使う 24 点の値。1 つも観測していない。

## 1. 主張してよい範囲と限界

- **推定対象は trace 無効な build における端から端までの throughput 比である。**
- **3 腕はいずれも未認証である (正しさを主張しない)。** 現行の `--mode certify` の受理集合は
  `tuned` と `cw-as-dyn` の 2 cell だけで、step policy 腕を受け付けない。
  **成果物は `headline_eligible=false` と `correctness_status="uncertified"` を記録し、
  headline・採用判断・fitness から機械的に隔離する。**
- **自動撤回機構は存在しない。** policy 腕を受ける verifier、anomaly の受領証、成果物への束縛、
  解析が読む撤回 field のいずれも現時点で存在しない。したがって「anomaly が出たら撤回する」は
  現状では発火しない。**本試験の結果は常に未認証であり、採用・性能優劣の判断に使わない。**
  撤回を有効化するには上記 4 点を別タスクで実装する必要がある (§10)。
- **単一環境・単一 protocol・単一 record 数の結果である。** 他環境・他 protocol・他 workload 族へ
  外挿しない。
- **推定対象は「実現した 18 block-node 上の等重み平均」に限る。** Pegasus 全体・特定 node 型・
  将来の投入分布へ一般化しない。
- **旧 7 腕の block と混ぜた確認的判定を出さない。** 別時期・別 block・別 patch stack であり、
  対内比が取れない。旧結果は文脈と再現性の確認までに使い、本書の判定には数えない。
- **thread 軸の縦比較 (6 対 48 など) を因果に使わない。** driver は threads を昇順に回すので、
  縦比較は job 内時刻と交絡する。腕の同一点対比だけが順序均衡の保護を受ける。
- **本試験は機構の採否を決めない。** 決めるのは 3 対比の CI と判定語だけである。

## 2. 腕と順序

3 腕は次の逐語で固定する。

```
p0 = cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0
p1 = cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1
p2 = cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2
```

| 腕 | step policy | 意味 |
| --- | --- | --- |
| p0 | 0 | 制御器が推奨した向きへ常に進む |
| p1 | 1 | 推奨と逆向きへ常に進む |
| p2 | 2 | seed 由来の決定的 LCG で向きを半々に選ぶ |

**腕の実行順は 3 腕の全 6 permutation を使う。** driver は `workload → threads → cell` の順に
回すので、腕は最内であり、`--cells` の並びが各測定点の中での順序になる。block `i`
(`i = 0..17`) の順序は `i mod 6` で次の表から引く。

| `i mod 6` | 順序 |
| --- | --- |
| 0 | p0, p1, p2 |
| 1 | p0, p2, p1 |
| 2 | p1, p0, p2 |
| 3 | p1, p2, p0 |
| 4 | p2, p0, p1 |
| 5 | p2, p1, p0 |

**6 permutation を使う理由 (循環 3 通りでは足りない)。** 開始位置だけを回す循環 3 通りは、
位置効果は消すが**一次持越しを消さない**。循環 3 通りでは 6 通りの有向遷移のうち
`p0→p1` / `p1→p2` / `p2→p0` の 3 通りしか現れず、逆向き 3 通りは 1 回も現れない
(18 block・各 job 71 遷移で数えて確認した)。全 6 permutation × 3 replicate では
6 通りの有向遷移が各 213 回、各腕が各位置に各 6 回で、位置と一次持越しの両方が均衡する。
driver は washout を置かないので、この均衡が持越しへの唯一の防護である。

**受理する `--cells` はこの 6 通りだけ**とし、`i mod 6` と一致しない組合せは拒否する。
順序と hostname は成果物 JSON へ記録する。

**seed。** p2 だけが seed を使い、**seed は p2 の genome と binary を変える** (p0 / p1 の binary は
seed に依らない)。block `i` の seed は §8.1 の逐語一覧の `i` 番目に固定する。slot と seed の対応は
driver・PBS・解析 module・独立テストの 4 面で束縛し、別 seed の成果物が本書の sha256 を
名乗れないようにする。**推定対象は「事前登録した 18 seed 上の平均」**であり、任意 seed や既定 seed
での性能ではない。**決定的 LCG を「厳密に独立」とは呼ばない。**

## 3. 測定条件

| 項目 | 値 |
| --- | --- |
| workload | write-heavy (rr 5) / balanced (rr 50) / read-heavy (rr 95)、zipf 0.9、rmw 0、max_ope 10 |
| threads | 6, 12, 18, 24, 30, 36, 42, 48 |
| records | 1,000,000 |
| extime | 3 秒、1 job あたり 1 rep |
| stage | 1 |
| 反復 | **18 block** (block = job)。1 job が 3 腕 × 3 workload × 8 threads = 72 process を回す |
| 腕の実行順 | §2 の 6 permutation。`rep_index mod 6` が順序を決め、契約が一致を要求する |
| build | **trace 無効**。perf 計測なし |
| ccbench | pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` + patch A `cicada-adaptive-params.patch` + patch B `cicada-adaptive-dynamic.patch` + patch C `cicada-adaptive-counterfactual.patch` (順序付き patch stack と sha256 を成果物へ記録) |
| driver | `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` (performance mode、trace 無効、step policy 契約) |
| 出力 | `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/t2417-policy/` |
| 集約 | 生値。腕の比較は同一 block 内の対内 log 比 (§4)。CI は t 分布 (n=18、df=17) |

### 3.1 trace 無効であることの証拠

成果物は次をすべて記録し、解析が検査する。

- `backoff_trace` が偽であること。
- perf binary に診断 symbol (`izanagi_backoff_trace` 接頭辞) と文字列 (`IZANAGI_BACKOFF_TRACE`) が
  **0 個**であること (`nm` と `strings` による負の走査)。
- **`build_trace_enabled` が偽であること、build cache key、source evidence、admission receipt、
  exact な compile define。** 負の symbol 走査だけでは正しさ trace の無効を証明できないため、
  build 側の正の証拠を併せて記録する。

### 3.2 腕の間で許す差

**`BACKOFF_STEP_POLICY` と、p2 の `BACKOFF_STEP_POLICY_SEED` だけ**を許す。それ以外の source bytes、
compiler の完全 identity、trace mode、compile flags、patch stack は 3 腕で一致することを要求する。
block 間では p0 / p1 の genome と binary identity が一定であることを要求し、p2 の genome は
その block の事前登録 seed と一致することを要求する。

### 3.3 見積もりと投入

既存 7 腕 block の実測は 168 process で wall 714〜737 秒、prologue 約 10 秒。本試験は 72 process と
build 3 本である。**prologue と build は固定費なので単純比例にはならない。** 計画範囲は
6〜9 分程度とし、walltime は既存と同じ 40 分を採る。1 process の timeout は 180 秒なので、
timeout が重なると 40 分に届きうる。job 全体の退出余裕を設け、部分成果物を確実に閉じる。

**18 block を 1 本の detached checkout から連続して `qsub` する。同時「投入」だけを契約し、
同時「開始」・別 node 配置・開始順は契約しない。** 開始時刻の差と hostname の重複を除外理由に
しない。hostname・投入時刻・開始終了時刻・distinct node 数を provenance に記録する。
permutation は `rep_index mod 6` で周期 6 と速く回るので、遅い queue ドリフトは permutation 間へ散る。

## 4. 主推定量

block `b` (`0..17`)、workload `w`、threads `t` について、腕 `a` と `c` の対内 log 比

```
d_b(a, c; w, t) = ln(TPS[b,a,w,t] / TPS[b,c,w,t])
theta           = mean over b of d_b            (18 block の等重み平均)
s               = 標本標準偏差 (分母 17)
SE              = s / sqrt(18)
CI95            = theta +- 2.1098156 * SE       (t_{0.975,17})
```

表示用の百分率は `100 * expm1(x)`。**固定する対比は次の 3 本だけ**で、正の値は左の腕が速いことを
意味する。

| 対比 | 意味 |
| --- | --- |
| p0 / p1 | 推奨方向 対 常時反転 |
| p0 / p2 | 推奨方向 対 混合 |
| p2 / p1 | 混合 対 常時反転 |

`TPS` は各 (block, 腕, workload, threads) の `median_tps` を採る。0・負値・非有限は log 比へ入れず
§7 の欠測として扱う。

## 5. 等価域と検出力

**等価域は対称な `[-ln(1.03), +ln(1.03)]`**、すなわち `+-0.02955880224154443` (throughput 比では
`[1/1.03, 1.03]`) とする。旧 7 腕事前登録と同じ幅 (±3%) で、ITT の段 3 が是正した対称形を採る
(`ln(0.97) = -0.030459` ではない)。

判定語 (対比ごと・点ごと、strict inequality):

- **実用優越** `practical_superiority`: CI 下端 > `+ln(1.03)`
- **非劣性** `non_inferior`: CI 下端 > `-ln(1.03)`
- **等価** `equivalent`: CI 全体が等価域の内側
- **実用劣化** `practical_degradation`: CI 上端 < `-ln(1.03)`
- それ以外は **`inconclusive`**。**非有意を等価と呼ばない。**

### 5.1 反復数 18 の根拠

標準偏差の想定には**2 つの参照級**があり、どちらか一方だけでは決められない。

1. **同じ量・別の腕**: T-2187 が報告した block 単位 log 比の CI 幅 ±1.0〜1.4% (n=7、t=2.4469119) が
   含意する SD は **0.0108〜0.0151**。
2. **同じ腕・別の量**: ITT が計画に使った窓単位 log 比の SD **0.032**。本試験の推定量は
   block 単位の throughput 比なので、これは**より粗い上限側の想定**である。

正規な対内 log 差を仮定した計画計算 (親が 20 万試行の模擬で算出)。

| SD | n=12 の等価判定力 (θ=0) | n=18 | n=24 | n=18 の 80% 最小検出優越 |
| ---: | ---: | ---: | ---: | ---: |
| 0.013 | 100% | 100% | 100% | 3.94% |
| 0.015 | 100% | 100% | 100% | 4.09% |
| 0.022 | 97.6% | 99.9% | 100% | 4.60% |
| 0.032 | 66.2% | 91.5% | 98.2% | 5.33% |

**n = 18 を採る。** 6 permutation の均衡に必要な 6 の倍数であり、悲観側の SD = 0.032 でも
等価判定力 91.5%、80% 最小検出優越は 3.94〜5.33% である。n = 24 の上積みは小さく、
実験規模を無造作に大きくしない規律に反する。

**「検出対象は 3%」とは書かない。** 等価域が ±3% であることと、80% で検出できる優越が
3.94〜5.33% であることは別である。3〜4% の実用差は `inconclusive` になりうる。

## 6. 仮説と層

**主点は (write-heavy, 48 threads)** とする。根拠は §0.1(1) の構造データ — この regime だけ
policy 1 の反転が実現 0.492 に落ち、腕が backoff を clamp 領域へ追い込む。**「唯一腕が届く層」とは
言わない** (構造データでは 3 腕とも全 regime で処置が届いている)。

| 仮説 | 対比と受理条件 | 答えられる問い | 答えられない問い |
| --- | --- | --- | --- |
| H1 向きの効果 (主) | 主点で `p0 / p1` が実用優越 | 制御器が選ぶ向きが、その regime の throughput を実用的に上げるか | 機構のどの枝が効いたか、他環境 |
| H2 用量反応 | 24 点すべてで `p0 / p2` と `p2 / p1` がともに非劣性 | 反転率 0 / 0.5 / 1 に対し throughput が単調に並ぶか | 単調性の関数形 |
| H3 abort 不要域の予測 (「効果なし」) | read-heavy の 8 点すべてで `p0 / p1` が等価 | abort がほぼ無い regime で向きの選択が実用差を生まないという予測 | backoff 機構一般 |

**仮説単位の判定は三値。** `accepted` = 受理条件の全述語を満たす。`rejected` = 受理条件が満たされ得ない
ことを示す (実用優越なら「主点の CI 上端 ≤ `+ln(1.03)`」、非劣性なら「いずれかの点で CI 上端 <
`-ln(1.03)`」、等価なら「いずれかの点で CI 全体が等価域の外」)。それ以外は `inconclusive`。
判定対象の点は H1 が 1 点、H2 が 24 点、H3 が read-heavy の 8 点である。

**結果を見てから点・層・対比を選ばない。全点から勝者を選ばない。** 副次として 3 対比 × 24 点を
CI 付きで表に出すが、H1〜H3 以外は事前登録した判定に数えない。family-wise の主張が要るなら
対比ごとに 24 検定を Holm 補正する。`abort_rate` は生値を記録するだけで、本書では解析しない。

## 7. 欠測規則 — 構造違反と測定欠測を分ける

**外れ値除外はしない。補完もしない。**

**(a) 構造違反は成果物ごと拒否する。** schema、腕の逐語、permutation と `rep_index mod 6` の対応、
seed と slot の対応、workload 軸、thread 軸、`records`、`extime`、`reps_per_job`、`stage`、
trace 無効の証拠 (§3.1)、腕間 build 差の allowlist (§3.2)、事前登録 sha256 のいずれかが
一致しなければ、その成果物を解析の入力にしない。理由 code を返す。

**(b) 測定欠測は点単位で扱う。** 構造が正しい成果物の中で、ある (腕, workload, threads) 座標の
`median_tps` が欠落・非正・非有限のときは、**理由付きの missing として最終成果物に残し**、
解析はその座標を含む対比の点だけを `inconclusive` (理由 `n-insufficient`) にする。
**「exact 72 row 必須」は採らない** — 1 件の欠測で成果物全体を落とすと、点単位の処理へ到達できず、
ITT が経験した「規則の発火で主判定が全部潰れる」型を再演する。

要求するのは「exact 72 個の (腕, workload, threads) 座標を持ち、各座標が値または理由付き missing の
いずれかであること」である。

**(c) block 単位の欠落。** 1 block が完走しない (walltime 超過・例外) 場合、最終 JSON は生成されず、
その block の全点が欠ける。**journal は正式な入力にしない** (表には出す)。

**(d) 点ごとの `n`。** 対内比が 18 対そろわない点は判定を出さず `inconclusive` (`n-insufficient`) と
し、欠けた `rep_index` を列挙する。**df を切り替えない。**

**(e) 再投入。** **outcome を見る前に判定できる infra 失敗 (queue・ノード障害) に限る。**
**timeout と 0 TPS は policy 由来でありうるので、無条件の再測定理由にしない。**
同一 `rep_index` の再投入上限は 1 回。複数の有効な成果物ができたら**最初に完走した job** を採る。
理由と job ID を insight に記録する。

**(f) hostname の重複・開始時刻の差は除外理由にしない** (§3.3)。distinct node 数を provenance に
書き、少数 node に偏った場合はその事実を結果に併記する。

## 8. seed と停止規則

- **固定 18 job。途中解析をしない。結果を見てから block を足さない。**
- p2 の seed は block ごとに 1 つ、§8.1 の逐語一覧で固定する。
- seed は `sha256("izanagi-t2417-policy2-seed-NN")` の先頭 8 byte を big-endian の uint64 と読んで
  導出した (`NN` は 2 桁 10 進、`00`〜`17`)。**導出規則と逐語一覧の両方を書く**が、束縛するのは
  逐語一覧の値である。18 値はすべて相異なることを確認済み。

### 8.1 seed の逐語一覧

| block (`rep_index`) | 腕の順序 | seed (10 進 uint64) |
| ---: | --- | ---: |
| 0 | p0, p1, p2 | 7170359757993337886 |
| 1 | p0, p2, p1 | 17989269546948137795 |
| 2 | p1, p0, p2 | 3716960512023197351 |
| 3 | p1, p2, p0 | 2309627334396074330 |
| 4 | p2, p0, p1 | 17927187949116432153 |
| 5 | p2, p1, p0 | 3065832495472073934 |
| 6 | p0, p1, p2 | 4312234405970990967 |
| 7 | p0, p2, p1 | 427285116805996036 |
| 8 | p1, p0, p2 | 3640648522570663905 |
| 9 | p1, p2, p0 | 6418011988295890983 |
| 10 | p2, p0, p1 | 8628608498907907249 |
| 11 | p2, p1, p0 | 3020250207517407008 |
| 12 | p0, p1, p2 | 2373385927424670485 |
| 13 | p0, p2, p1 | 12508141252750115867 |
| 14 | p1, p0, p2 | 5818589253263944573 |
| 15 | p1, p2, p0 | 13760661656174455019 |
| 16 | p2, p0, p1 | 16587099826641119208 |
| 17 | p2, p1, p0 | 13478069633953621058 |

## 9. 記録する束縛

成果物 JSON は次を記録する。

- **`backoff_policy_performance_prereg_sha256`** (本書の bytes の sha256)。**本書の exact な腕・
  順序・seed・軸・`extime`・`reps_per_job`・`stage` で走った成果物にだけ付く。**
- **`performance_contract`** — 本試験の成果物であることを示す識別子。既存の認証経路
  (`--mode certify` の性能成果物束縛) はこの識別子を持つ成果物を**拒否する**。
- **`headline_eligible=false`**、**`correctness_status="uncertified"`**。
- 既存 field を二義化しない: `prereg_sha256` は旧 7 腕書のまま、`counterfactual_preregistration` は
  trace 有効 ITT 専用のまま。
- `repo_head`、`repo_status_clean`、ccbench pin (短縮 `ccbench_commit` と full `ccbench_head`)、
  patch A / B / C の sha256、順序付き `patch_stack` と `patch_stack_sha256`、`driver_sha256`、
  `pbs_sha256`、`driver_argv`、`cc` / `cxx`、腕ごとの `binary_sha256` と genome、`step_policy_seed`、
  `cell_order`、`rep_index`、hostname、prologue と job 全体の所要、`schema_version`、
  `records`、`extime_s`、`reps_per_job`、`stage`、`kind`、`not_certified`、`throughput_scope`、
  §3.1 の trace 無効の証拠、§3.2 の腕間 build 差の証拠。
- 投入 (qsub) の argv と job ID は親が job dir の台帳と insight に記録する。

解析は `orchestrator/campaign/backoff_policy_performance_analysis.py` の公開関数 1 本で行い、
CLI を持たない。本書の sha256 は同 module に逐語 literal として pin し、渡された doc の bytes と
比較する。

**この pin の射程を誇張しない。** 本書・module の literal・成果物を同じ commit で同時に変えれば
runtime の検査は通る。**repo 内の検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への
完全な防壁ではない。** 本書はこの限界を主張せず明記する。事前登録 commit と測定 commit の時系列は
Git 履歴で確かめる。

## 10. 本書が覆わない次の一手

- **step policy 腕の直列性認証。** 現行の受理集合は 2 cell だけで、3 腕を受け付けない。かつ
  `--step-policy-seed` は `--mode certify` と併用が明示拒否される。現行の identity 束縛のまま
  全 identity を認証すると、p0 + p1 + seed 別 p2 が 18 で **20 identity × 24 request = 480 request**
  になる。認証の要否と受理集合の改訂はユーザー裁定。
- **撤回機構の 4 点** — policy 腕を受ける verifier、anomaly の受領証、成果物への束縛、解析または
  公表 consumer が読む撤回 field。これらが揃うまで自動撤回は有効化しない。
- `abort_rate` の対内解析。
- 他環境・他 protocol・他 record 数への展開。
- 旧 7 腕 campaign との因果的比較 (対内比が取れないため本書の枠外)。
- 機構の採否判断。
