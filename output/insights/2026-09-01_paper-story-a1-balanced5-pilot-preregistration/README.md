# 事前登録 — paper-story A-1 均衡 5-rep pilot の測り方と使い方 ([T-1777])

- `authority: preregistration` — 機械可読の正本は
  `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json`。本文書はその人間可読の対であり、
  policy 側から SHA-256 で束縛される。**本文書に policy の hash を書かない** (自己参照の禁止)。
- `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- `study_id: paper-story-a1-20260901-balanced5-pilot-v1`
- **凍結時点: 計測の投入より前。凍結後に値も規則も変えない。**
- **この走行は pilot である。** 目的は本走の反復数を決める材料 (対の散らばりと baseline の水準) を
  作ることだけであり、性能の優劣を述べるためのものではない。何に使えて何に使えないかは 7 節に書く。

---

## 1. 何を測るか

同一 campaign の中で 2 つの構成を測り、その差を出す。workload ごとに variant が異なる。

| workload | `ycsb_rratio` | variant (`role=variant`, `contrast=minuend`) | baseline (`role=baseline`, `contrast=subtrahend`) |
|---|---|---|---|
| write-heavy | `5` | `fixed10` — `BACK_OFF=1`, `BACKOFF_FIXED=10` | `no-backoff` — `BACK_OFF=0`, `BACKOFF_FIXED=-1` |
| balanced | `50` | `fixed5` — `BACK_OFF=1`, `BACKOFF_FIXED=5` | `no-backoff` — `BACK_OFF=0`, `BACKOFF_FIXED=-1` |
| read-heavy | `95` | `fixed2` — `BACK_OFF=1`, `BACKOFF_FIXED=2` | `no-backoff` — `BACK_OFF=0`, `BACKOFF_FIXED=-1` |

両 arm とも protocol は `silo`、`NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0`。

対比は `variant-minus-baseline` である。**これは役割で決まるのであって、物理的にどちらが先に
走ったかで決まるのではない。** 5-rep ブロックの先後がどちらであっても、差は必ず
「variant の TPS から baseline の TPS を引いたもの」とする。

規模は records=1,000,000 / threads=48 / zipf skew=0.9 / rmw=0 / max_ope=10 / extime=3 秒。
verify の構成は `legacy` の 1 本だけを期待する。走行は
`mode=exploration`、`site=pegasus-compute-only`、`formal=false`、`promotion_prohibited=true` とする。

## 2. 配置と、記録する量

配置は `balanced-a5b5-b5a5-v1` である。スケジュールの受領証の schema は
`paper-story-a1-balanced-schedule-receipt/v1` とする。

**2 種類のブロックを区別する。**

- **arm ブロック** = 同じ arm を続けて測る 5 rep のかたまり。
- **対ブロック** = 5 つの対に対応する 2 本の arm ブロック (variant の 5 rep と baseline の 5 rep)。

数はこうなる。

- 1 workload あたり **60 対**。対の番号 `pair_index` は 0 以上 60 未満。
- 対ブロックは **12** 本 (5 対ずつ)。**arm ブロックはその倍の 24 本** (いずれも 5 rep)。
- 12 本の対ブロックのうち、variant 先行が 6 本、baseline 先行が 6 本になる。
- **10 対 = 1 組**とし、1 組は 2 本の対ブロックからなる。組の中には variant 先行の対ブロックと
  baseline 先行の対ブロックがそれぞれ 1 本ずつ入る。組は 6 つある。
- 組の中の先後だけを凍結 seed で決める。物理順は次の 2 通りしかない。
  **`A` は variant、`B` は baseline を指す。**
  - bit が 0 のとき `A^5 B^5 B^5 A^5`
  - bit が 1 のとき `B^5 A^5 A^5 B^5`

順序 bit の作り方は次のとおりで、走行前に完全に決まっている。

- 組ごとの原像は `a1-balanced5/v1|workload=<name>|group=<zero-based decimal>`。
  **原像に study ID と日付を入れない。**
- 原像は root seed の ASCII bytes の直後に UTF-8 bytes として連結する。root seed は
  小文字 16 進 64 文字である。
- 連結した bytes の SHA-256 を取り、その**最下位 1 bit** を順序 bit とする。
- 1 つの workload の順序 bit が全部 0 または全部 1 になった場合だけ、固定 counter を 1 増やして
  その workload の bit 列を丸ごと引き直す。counter は 0 から始まり 16 未満である。
  実効 seed の原像の書式は `<64-lowercase-hex>|counter=<zero-based decimal>` とする
  (小文字 16 進 64 文字、続けて縦棒、続けて 0 起点の 10 進数)。
  **引き直しは、実現したスケジュールを 1 つも観測・選択する前に行う。**
  counter が 16 に達しても同一でない bit 列が得られなければ、そこで停止する (fail-closed)。

workload ごとの root seed は次に凍結する。

| workload | root seed |
|---|---|
| write-heavy | `1698e2cba5aa7853040e2fed47e88e1f682a019878348bfc392b8f8f60eb5447` |
| balanced | `b2ada8029ec867d5188c87076f3d7cc4c1314ca642bb0b3c0cd1e4dd811d1a24` |
| read-heavy | `fb3ffea0fc8bace8166b39558b8ac10f426fb92ac5efa8dbe90acb33d6d33fd1` |

**記録する量は、1 反復あたり次の 8 つに閉じる。** これは反復数を決める手順が受け取る行の
形でもある。

`tps`, `arm`, `pair_index`, `group`, `block`, `block_position`, `started_at_ns`, `ended_at_ns`

行は時刻の昇順で、区間が重ならないことを要求する。重なりや逆順があればその pilot は使わない。

さらに、記録された物理順から次を検査する。ここを満たさない pilot は反復数の材料にしない。

- 12 ブロックのうち variant 先行が 6、baseline 先行が 6 であること。
- 6 つの組それぞれで、2 ブロックの先後が variant 先行と baseline 先行の 1 本ずつであること。

## 3. 推定対象と、その限定

機械可読の正本 `pairing.estimand` は次のとおりである。

> `arithmetic mean of paired differences under the balanced five-rep schedule`

日本語で限定を置く。

> **推定対象は「5-rep 均衡スケジュール下での差」である。残留効果の無い定常状態の直接効果と
> 同一視しない。**

この配置は、対の中の順序と時間隔を釣り合わせることで**識別可能性を上げる**ために選んだもので
あって、時間隔の交絡や残留効果が存在しないことの証拠ではないし、それらを消したという主張でも
ない。1 つの arm ブロックが 5 rep であるため、同じ番号の対を構成する 2 つの測定の間隔は
有限のまま残る。したがってここで測る差は、この配置のもとでの差である。

## 4. pilot から計画 sigma を作る

反復数を決める入力は、次の手順で pilot の観測値から作る。手順は pilot のデータを読む前に凍結する。

1. 対ごとの差を作る。対 `pair_index` の差 = その対の variant の TPS − baseline の TPS。60 個できる。
2. ブロック平均を作る。連続する 5 対の差の平均を取り、12 個作る。
3. `sd(60 個の差)` と `sd(12 個のブロック平均)` を、いずれも標本標準偏差として求める。
4. 上側係数を `c(one-sided, alpha_c, df) = sqrt(df / chi-square-quantile(alpha_c, df))` とし、
   `alpha_c = 1/20` (5%) を使う。
5. `sigma_pair = c(one-sided, alpha_c, df = 59) * sd(60 paired differences)`
6. `sigma_block = sqrt(5) * c(one-sided, alpha_c, df = 11) * sd(12 five-pair block means)`
7. **`planned_sigma = max(sigma_pair, sigma_block)`** — 大きい方を採る。
8. baseline の水準は、その workload の baseline 60 点の算術平均とする。0 以下または有限でない値に
   なった場合は使わない。

**旧配置の計画 sigma を流用しない。** 配置を変えると対の共分散が変わるため、別配置の pilot から
分散設計を正当化することになるからである。

## 5. 反復数の探索と、その判定

反復数 `n` の探索は、上で作った `planned_sigma` と baseline 水準だけを scale として使い、
残りの式・確率・候補・seed・停止規則はすべて pilot のデータを読む前に凍結する。

### 5.1 区間と境界

- `k = t(1 - (1/120)/2, n - 1)`。`1/120` は arm の失敗確率の目標値である。
- `h = k * s / sqrt(n)`。`s` はその走行の対差の標本標準偏差。
- `L = mean - h`、`U = mean + h`。
- **`B = (3/100) * (その workload の baseline 平均)`** — floor は相対量 (3%) として置く。

### 5.2 分類

優先順位つきで次のとおり分類する。名前は反復数を決める手順が使う語彙である。

| 順位 | 条件 | 分類 |
|---|---|---|
| 1 | `L > B` | `resolved-beyond-floor` (improvement) |
| 2 | `U < -B` | `resolved-beyond-floor` (regression) |
| 3 | 上のどちらでもなく、`L >= -B` かつ `U <= B` | `bounded-within-floor` |
| 4 | 上のいずれでもない | `unresolved` |

`mean` または `h` が有限でない、あるいは `h` が負になる試行は `invalid` として数える。

### 5.3 3 つの条件と、要求する成功率

真の差を `baseline 平均 × delta` として置き、次の 3 条件を評価する。括弧内は反復数を決める
手順の側の条件名であり、同じものを指す別名である。

| 条件 | `delta` | 成功とする分類 |
|---|---|---|
| `zero` (`zero`) | `0/1` (0%) | `bounded-within-floor` |
| `positive-six-percent` (`positive-two-floor`) | `+3/50` (+6%) | `resolved-beyond-floor` (improvement) |
| `negative-six-percent` (`negative-two-floor`) | `-3/50` (-6%) | `resolved-beyond-floor` (regression) |

`+3/50` と `-3/50` は floor `3/100` のちょうど 2 倍である。

**3 条件すべてで成功率が `4/5` (80%) 以上でなければならない。**

### 5.4 候補と探索の進み方

- 候補 `n` は step `10` で並べる。登録上の下限は `28`、実際に実現しうる下限は `30`、上限は `4096`
  (実際に評価しうる最大の候補は `4090`) とする。
- **動作特性は、実際の候補 `n` でのみ評価する。**
- 候補を小さい方から順に見て、まず探索で 3 条件すべてが `4/5` 以上になるものを選ぶ。
- 探索を通った候補には、続けて認証を行う。認証では 3 条件それぞれについて、成功回数から
  片側 Clopper–Pearson 下限を作り、それが `4/5` 以上であることを要求する。
- 認証の試行 `j` 回目に使う条件ごとの alpha は `1/(60 * j * (j + 1))` である。
  **この配分は workload ごとに独立している。** 1 つの workload の全試行・全条件の合計 alpha は
  `1/20` を超えない (1 条件あたりの全試行合計は `1/60`)。**3 つの workload を合わせた合計は
  `1/20` ではなく最大で `3/20` である。** 3 workload を同時に `1/20` として扱わない。
- 認証に失敗したら、次の探索通過候補へ進む。**認証を通った最小の `n` を採用する。**
- 上限まで見ても認証を通る候補が無ければ、結果は `no-passing-n` として終わる。
  **この場合に候補範囲・成功率・floor・alpha を後から緩めない。**

### 5.5 数値実験の作り方

- 模型は、正規標本の平均と標本分散の十分統計量を使う Monte Carlo である。
  bootstrap でも再標本化でもない。乱数生成器は PCG64 とする。
- 根 seed の原像は `paper-story-a1-balanced-sizing-root-seed/v1|20260901|paired-mean-block-sigma`、
  その SHA-256 は `e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3` である。
- 子 seed の原像は
  `paper-story-a1-balanced-sizing-seed/v1|root=<root>|phase=<phase>|workload=<workload>|condition=<condition>|n=<n>|trials=<trials>`
  とし、認証のときだけ末尾に `|attempt=<attempt>` を足す。
- **試行回数を次に凍結する。探索 20,000 回、認証 100,000 回。**
  この 2 値は、同じ A-1 族で先に凍結された headline study の値
  (`orchestrator/campaign/paper_story_a1_headline.v1.json` の `search_trials` / `certification_trials`)
  に揃えたものである。**pilot のデータを読んだ後にこの 2 値を変えない。**
- **この 2 値と候補範囲は、ここで登録した値であって、道具が機械的に強制する値ではない。**
  反復数を決める道具は試行回数を 1 以上 1,000,000 以下、候補範囲を `28 <= n_min <= n_max <= 4096` の
  範囲で受け取る。本文書はその範囲の中から使う値を先に決めるものであり、道具がこの値以外を
  拒否すると主張するものではない。
- 生成側と検証側は別の実装として突き合わせるが、**互いに独立な統計の権威ではない。**

## 6. 走行・品質・無効・再走の規則

### 6.1 走行

- 1 workload = 1 campaign。campaign の形は「workload ごとに新しく起こす、arm がちょうど 2 本の
  均衡 5-rep campaign を 1 本」とする。両 arm の build と verify を、最初の bench ブロックより
  **前に**完了する。
- `bench_lock()` は 1 workload につき 1 回だけ取り、全ブロックを通して保持する。保持の範囲は
  「両 arm の build と verify の後の、すべての均衡 5-rep ブロック」である。
- 静定は workload のスケジュール開始時にちょうど 1 回。ラウンドの単位は
  「1 つの workload のスケジュール全体」とする。
- 競合テナントの検査は 5-rep arm ブロックごとに、その前に行う。検知したらその workload を止める。
- `bench_max_rounds = 1`。自動再試行は行わない。
- 計測の durable な置き場は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-pilot-20260901/measurement`、
  成果物の公開先は `output/insights/2026-09-01_paper-story-a1-balanced5-pilot` とする。
  公開は終端の生の束を、**一度しか作れない宛先**へ書き出す形で行う。
- CCBench は `511c9538e4e8efa54b45cda62e72389ed3b706ec` を canonical pin とし、追跡ファイルが
  汚れていないことを次の 5 つの境界で要求する。
  `login-submit-before-intent-and-qsub` / `compute-job-body-preflight` /
  `driver-measurement-start` / `before-each-trace-and-perf-build` /
  `artifact-consumer-arm-validation-and-materializer-raw-recollection`

### 6.2 品質

- 集約 CV = その arm の全 rep の TPS の標本標準偏差 ÷ 同じ TPS の算術平均。
- ブロックごとの CV は**診断専用**であり、集約 CV の代わりにも、その平均にもしない。
- `unstable` は `集約 CV > 0.05` とする。
- 静定できない・CV が定義できない・throughput が無い場合は、いずれもその workload を止める。

### 6.3 無効の規則

次のいずれかに当たる走行は無効とする。順番と文言は機械可読の正本のとおりである。

1. `campaign workload arm set is not exactly its registered variant and baseline`
2. `an arm has anything other than exactly one build attempt`
3. `both arms are not built and verified before the first bench block`
4. `a verify_done is not certified true or its workload tag differs`
5. `a competing-tenant probe is missing, raises, or detects a tenant before any five-rep arm block`
6. `settle is missing, fails, or occurs other than once at workload schedule start`
7. `bench throughput has no point`
8. `bench aggregate CV is undefined`
9. `bench aggregate CV is not computed from every rep of its arm`
10. `bench rounds is not exactly integer one`
11. `bench unstable is not exactly false`
12. `a block has anything other than five positive finite throughput points`
13. `schedule receipt is missing or differs from the frozen seed derivation and physical order`
14. `a workload is interrupted, one-sided committed, or lacks both arm completion records`
15. `trace0 source-routed evidence is incomplete or inconsistent`
16. `CCBench HEAD differs from canonical pin or CCBench tracked files are dirty at a required boundary`

**この 16 に加えて、`rep_notes` が空でないことも無効の条件である。**
これは機械可読の正本の 16 文字列の外にあるが、arm の検査が `rep-notes-not-empty` として
実際に無効化する。8 節に、この条件が反復数に対して持つ性質を書く。

### 6.4 再走

再走してよい理由は次の閉じた列挙だけである。いずれも bench が始まる**前**の失敗である。

- `build-failure-before-bench`
- `verify-failure-before-bench`
- `competing-tenant-detected-before-bench`
- `scheduler-or-infrastructure-failure-before-bench`

**性能の出力は再走を正当化しない。** `rep_notes` が空でない・`rounds != 1`・`unstable` は
再走せず、その workload を無効として確定させる。

## 7. この pilot の結果で、何ができて何ができないか

### 7.1 できること (受理)

- 3 つの workload すべてが完走し、2 節の物理順の検査と 6 節の無効の規則を通った pilot から、
  4 節の手順で `planned_sigma` と baseline 水準を作ること。
- そこから 5 節の凍結された式で反復数を探索し、認証された `n` を得ること。

### 7.2 できないこと (拒否)

- **差の符号や大きさについて何かを述べること。** 速い・遅い・改善した・悪化したと言わない。
- **pilot 自身に `resolved-beyond-floor` や `bounded-within-floor` の分類を与えること。**
  この分類式は、反復数の候補を評価するための道具であって、pilot の結果に貼る札ではない。
- 一部の workload だけが完走した pilot、または無効になった workload を含む pilot を、
  反復数の材料に使うこと。
- 最終推定に pilot の観測値を混ぜること。pilot は本走の推定には 1 点も入らない。
- この走行を正式な結果として扱うこと、または昇格させること
  (`formal=false`、`promotion_prohibited=true`、`final_estimate_eligible=false`)。

## 8. この設計で言えないこと

- **配置は識別可能性を上げるためのものである。** 時間隔の交絡や残留効果が無い、あるいは
  消えたことの証拠ではない。したがって推定対象は 5-rep 均衡スケジュール固有のものにとどまる。
- **反復数の設計は、pilot から作った sigma と baseline 水準を真値として固定した正規模型の上での
  評価である。** 正規性・定常性・pilot と本走の同分布性は、この手順では検査できない。
  したがって 5 節の `4/5` は、本走で実際にその割合が実現することの保証ではない。
- **`rep_notes` が空であることの要求は、反復数に対して急速に壊れる。** 1 反復あたりの
  note 発生確率を p とすると、1 workload が壊れる確率は `1-(1-p)^(2n)` である。
  pilot (n=60、2n=120) なら p=0.1% でも約 11.3% になる。**これは感度分析であって p の推定ではない。**
  それでも再走しないのは、note に残る典型が部分的な rep timeout であり、遅い反復ほど起きやすい
  性能依存の欠測だからである。これを理由に測り直せば、速く完走した試行を選ぶことになる。
- **source-routed な trace0 の証拠は、単体の成果物だけでは閉じない。** 不完全または不整合なら
  その走行は無効になる。
- **workload をまたぐ結論を作らない。** 3 つの workload は独立に扱い、1 つが無効でも他の 2 つの
  値は消さない。逆に、3 つのうち 1 つだけの結果から全体を述べることもしない。
- 本文書は、6 節の各条件を実際に拒否する実装が存在することまでは主張しない。
  ここに書いたのは**登録した判定の規則**であって、実装の完全性の証明ではない。

## 9. 還元判断

CCBench 本体への還元候補は含まない。本文書は探索の妥当性文書である。
