# 事前登録 — paper-story A-1 均衡 5-rep 本走の測り方と使い方

- `authority: preregistration` — 機械可読の正本は
  `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`。本文書はその人間可読の対であり、
  policy 側から SHA-256 で束縛される。**本文書に policy の hash を書かない** (自己参照の禁止)。
- `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- `study_id: paper-story-a1-20260901-balanced5-sized-v1`
- **凍結時点: 計測の投入より前。凍結後に値も規則も変えない。**
- **この走行はまだ投入していない。** 正式測定の認可は人間の手番である ([T-1505])。本文書と機械可読の
  policy は、認可が出た場合に何をどう測るかを先に固定するためのものであって、認可そのものではない。
- 反復数の材料は 2026-09-11 に完走した pilot
  (`output/insights/2026-09-01_paper-story-a1-balanced5-pilot/`) である。pilot から取ったのは
  **散らばりと baseline の水準という尺度だけ**であり、差の符号も大きさも取っていない。

---

## 0. この文書が確定させたこと

| 項目 | 値 |
|---|---|
| 1 workload あたりの対の数 | **30** |
| 自由度 | **29** |
| 区間の係数 `k` | **2.8315526875186725** |
| 対ブロック | 6 本 (5 対ずつ) |
| arm ブロック | 12 本 (5 rep ずつ) |
| 組 | 3 つ (10 対ずつ) |

pilot は 60 対だった。本走はそれより小さい。反復数は 5 節の凍結された手順が選んだ値であって、
こちらで選んだ値ではない。

---

## 1. 何を測るか

pilot と同じものを測る。同一 campaign の中で 2 つの構成を測り、その差を出す。workload ごとに
variant が異なる。

| workload | `ycsb_rratio` | variant (`role=variant`, `contrast=minuend`) | baseline (`role=baseline`, `contrast=subtrahend`) |
|---|---|---|---|
| write-heavy | `5` | `fixed10` — `BACK_OFF=1`, `BACKOFF_FIXED=10` | `no-backoff` — `BACK_OFF=0`, `BACKOFF_FIXED=-1` |
| balanced | `50` | `fixed5` — `BACK_OFF=1`, `BACKOFF_FIXED=5` | `no-backoff` — `BACK_OFF=0`, `BACKOFF_FIXED=-1` |
| read-heavy | `95` | `fixed2` — `BACK_OFF=1`, `BACKOFF_FIXED=2` | `no-backoff` — `BACK_OFF=0`, `BACKOFF_FIXED=-1` |

両 arm とも protocol は `silo`、`NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0`。

対比は `variant-minus-baseline` である。**これは役割で決まるのであって、物理的にどちらが先に
走ったかで決まるのではない。**

規模は records=1,000,000 / threads=48 / zipf skew=0.9 / rmw=0 / max_ope=10 / extime=3 秒。
verify の構成は `legacy` の 1 本だけを期待する。走行は
`mode=exploration`、`site=pegasus-compute-only`、`formal=false`、`promotion_prohibited=true` とする。

### 1.1 `formal=false` のまま本走を登録する理由

この study ID は、実装の 2 箇所 (`orchestrator/campaign/ident.py` の A-1 非認証 lane の identity 集合と
`orchestrator/campaign/wal.py` の同じ集合) に**登録済みの非認証 lane**として入っている。どちらも
`formal is False` と `promotion_prohibited is True` を独立に要求する。したがって `formal=true` を
名乗る policy は campaign の identity 検査で拒否される。ここでの `formal=false` は設計上の選択では
なく、既存の登録に従った結果である。

一方で `final_estimate_eligible` は `true` にする。これは「本走で得た観測値が登録済み解析の対象に
なる」という意味であり、**投入の認可でも、正式な結果への昇格でもない**。pilot は同じ field が
`false` で、観測値を最終推定へ入れられない。

policy の `authority.result_authority` は説明用の文字列で、認可や昇格を決める意味上の分岐には
使われない。ただし policy は内容の一致と bytes の pin を検査されるので、この文字列も凍結の対象で
あり、後から書き換えれば policy の読み込みが落ちる。この文字列自身が何かを拒否すると主張しない。

---

## 2. 配置と、記録する量

配置は pilot と同じ `balanced-a5b5-b5a5-v1` である。スケジュールの受領証の schema も同じく
`paper-story-a1-balanced-schedule-receipt/v1` とする。

**2 種類のブロックを区別する。**

- **arm ブロック** = 同じ arm を続けて測る 5 rep のかたまり。
- **対ブロック** = 5 つの対に対応する 2 本の arm ブロック (variant の 5 rep と baseline の 5 rep)。

本走の数はこうなる。

- 1 workload あたり **30 対**。対の番号 `pair_index` は 0 以上 30 未満。
- 対ブロックは **6** 本 (5 対ずつ)。**arm ブロックはその倍の 12 本** (いずれも 5 rep)。
- 6 本の対ブロックのうち、variant 先行が 3 本、baseline 先行が 3 本になる。
- **10 対 = 1 組**とし、1 組は 2 本の対ブロックからなる。組の中には variant 先行の対ブロックと
  baseline 先行の対ブロックがそれぞれ 1 本ずつ入る。組は 3 つある。
- 組の中の先後だけを凍結 seed で決める。物理順は次の 2 通りしかない。
  **`A` は variant、`B` は baseline を指す。**
  - bit が 0 のとき `A^5 B^5 B^5 A^5`
  - bit が 1 のとき `B^5 A^5 A^5 B^5`

順序 bit の作り方は pilot と同じで、走行前に完全に決まっている。

- 組ごとの原像は `a1-balanced5/v1|workload=<name>|group=<zero-based decimal>`。
  **原像に study ID と日付を入れない。**
- 原像は root seed の ASCII bytes の直後に UTF-8 bytes として連結する。root seed は
  小文字 16 進 64 文字である。
- 連結した bytes の SHA-256 を取り、その**最下位 1 bit** を順序 bit とする。
- 1 つの workload の順序 bit が全部 0 または全部 1 になった場合だけ、固定 counter を 1 増やして
  その workload の bit 列を丸ごと引き直す。counter は 0 から始まり 16 未満である。
  実効 seed の原像の書式は `<64-lowercase-hex>|counter=<zero-based decimal>` とする。
  counter が 0 のときは root seed をそのまま実効 seed として使う。counter が 1 以上のときだけ、
  この原像の UTF-8 bytes の SHA-256 を小文字 16 進で表したものを実効 seed とする。
  **引き直しは、実現したスケジュールを 1 つも観測・選択する前に行う。**
  counter が 16 に達しても同一でない bit 列が得られなければ、そこで停止する (fail-closed)。

### 2.1 本走の root seed

**この 3 値は pilot の完走後・本走の投入前に、ここで新規に凍結した値である。**
pilot より前から凍結されていたものではない。この点を偽らない。

各 workload の root seed は、次の ASCII 文字列の SHA-256 を小文字 16 進で表したものとする。
末尾に改行を含めない。

```
paper-story-a1-balanced5-sized-schedule-root/v1|workload=<name>
```

`<name>` は `write-heavy`、`balanced`、`read-heavy` の逐語である。

| workload | root seed |
|---|---|
| write-heavy | `e82d0c269021faae457924b71e22b720ca881d4ff0ac6726cf4d8c9c774323d3` |
| balanced | `f322d1daa33e1dd5bf15d3566cc81bb817a15233be762ca64a22664bb3c0ff94` |
| read-heavy | `9ad57bf708b51345af6a65c2208493f99e1d3c308cc48b329b816240d9a701ce` |

**pilot の 3 つの root seed は使い回さない。** 使い回すと、同じ組番号の順序 bit が pilot と共有され、
本走の短い系列が pilot の先頭部分と重なりうるからである。別 seed にすることでこの共有は避けられるが、
それは測定値の独立性や残留効果の不在を保証するものではない。

**原像を後から選び直さない。** pilot の TPS、選ばれた反復数、実現した物理順を理由に、接頭辞・版文字列・
区切りを変えた別の原像を試してはならない。引き直しは上に書いた「全 bit 同一のときの counter 規則」
だけに限る。

この規則から導かれる本走の順序 bit は次のとおりである。read-heavy は counter=0 で 3 つとも 1 に
なるため、登録済みの引き直し規則が発火して counter=1 の列を使う。

| workload | counter | 順序 bit (組 0, 1, 2) |
|---|---|---|
| write-heavy | 0 | 1, 0, 0 |
| balanced | 0 | 1, 1, 0 |
| read-heavy | 1 | 1, 0, 1 |

順序 bit が偏っても、1 つの組は必ず variant 先行 1 本と baseline 先行 1 本からなる。したがって
6 本の対ブロックの先後は bit の値によらず 3 本ずつになる。

### 2.2 記録する量

**1 反復あたり次の 8 つに閉じる。** pilot と同じである。

`tps`, `arm`, `pair_index`, `group`, `block`, `block_position`, `started_at_ns`, `ended_at_ns`

行は時刻の昇順で、区間が重ならないことを要求する。重なりや逆順があればその走行は使わない。

さらに、記録された物理順から次を検査する。

- 6 ブロックのうち variant 先行が 3、baseline 先行が 3 であること。
- 3 つの組それぞれで、2 ブロックの先後が variant 先行と baseline 先行の 1 本ずつであること。

---

## 3. 推定対象と、その限定

機械可読の正本 `pairing.estimand` は pilot と同一である。

> `arithmetic mean of paired differences under the balanced five-rep schedule`

日本語で限定を置く。

> **推定対象は「5-rep 均衡スケジュール下での差」である。残留効果の無い定常状態の直接効果と
> 同一視しない。**

この配置は、対の中の順序と時間隔を釣り合わせることで**識別可能性を上げる**ために選んだもので
あって、時間隔の交絡や残留効果が存在しないことの証拠ではないし、それらを消したという主張でも
ない。1 つの arm ブロックが 5 rep であるため、同じ番号の対を構成する 2 つの測定の間隔は
有限のまま残る。したがってここで測る差は、この配置のもとでの差である。

---

## 4. pilot から取った計画 scale

pilot の事前登録 §4 が凍結した手順を、そのまま pilot の観測値へ適用した。手順は変えていない。

1. 対ごとの差を作る (60 個)。
2. 連続する 5 対の差の平均を取り、ブロック平均を作る (12 個)。
3. `sd(60 個の差)` と `sd(12 個のブロック平均)` を標本標準偏差として求める。
4. 上側係数は `c(one-sided, alpha_c, df) = sqrt(df / chi-square-quantile(alpha_c, df))`、`alpha_c = 1/20`。
5. `sigma_pair = c(df = 59) * sd(60 paired differences)`
6. `sigma_block = sqrt(5) * c(df = 11) * sd(12 five-pair block means)`
7. `planned_sigma = max(sigma_pair, sigma_block)`
8. baseline の水準は、その workload の baseline 60 点の算術平均。

結果は次のとおりである。**これは散らばりと水準であって、差の推定値ではない。**

| workload | `sd(60 差)` | `sd(12 ブロック平均)` | `sigma_pair` | `sigma_block` | `planned_sigma` | 採った側 | baseline 水準 |
|---|---|---|---|---|---|---|---|
| write-heavy | 42812.622815101997 | 19151.199917680609 | 50538.920832270931 | 66403.452108019716 | **66403.452108019716** | block | 2396610.9666666668 |
| balanced | 42359.021243474039 | 16351.919843025382 | 50003.458802371359 | 56697.435713574683 | **56697.435713574683** | block | 3785897.2166666668 |
| read-heavy | 63253.307101347236 | 19561.43852591965 | 74668.489566274948 | 67825.883072771554 | **74668.489566274948** | pair | 10162917.35 |

単位はいずれも TPS である。**旧配置の計画 sigma は流用していない** (D1296)。
**pilot の観測値は本走の最終推定へ 1 点も入らない。**

---

## 5. 反復数の探索と、その判定

式・確率・候補・seed の定義域・停止規則は、いずれも pilot のデータを読む前に凍結されている。
本文書はそれらを変えない。以下は pilot 事前登録 §5 の再掲と、その手順が選んだ値である。

### 5.1 区間と境界

- `k = t(1 - (1/120)/2, n - 1)`。`1/120` は arm の失敗確率の目標値である。
- `h = k * s / sqrt(n)`。`s` はその走行の対差の標本標準偏差。
- `L = mean - h`、`U = mean + h`。
- **`B = (3/100) * (その workload の baseline 平均)`** — floor は相対量 (3%) として置く。

### 5.2 分類

| 順位 | 条件 | 分類 |
|---|---|---|
| 1 | `L > B` | `resolved-beyond-floor` (improvement) |
| 2 | `U < -B` | `resolved-beyond-floor` (regression) |
| 3 | 上のどちらでもなく、`L >= -B` かつ `U <= B` | `bounded-within-floor` |
| 4 | 上のいずれでもない | `unresolved` |

`mean` または `h` が有限でない、あるいは `h` が負になる試行は `invalid` として数える。

### 5.3 3 つの条件と、要求する成功率

| 条件 | `delta` | 成功とする分類 |
|---|---|---|
| `zero` | `0/1` (0%) | `bounded-within-floor` |
| `positive-six-percent` (`positive-two-floor`) | `+3/50` (+6%) | `resolved-beyond-floor` (improvement) |
| `negative-six-percent` (`negative-two-floor`) | `-3/50` (-6%) | `resolved-beyond-floor` (regression) |

**3 条件すべてで成功率が `4/5` (80%) 以上でなければならない。**

### 5.4 候補と探索の進み方

- 候補 `n` は step `10`。登録上の下限は `28`、実際に実現しうる下限は `30`、上限は `4096`
  (実際に評価しうる最大の候補は `4090`)。
- 候補を小さい方から順に見て、まず探索で 3 条件すべてが `4/5` 以上になるものを選ぶ。
- 探索を通った候補には認証を行う。認証では 3 条件それぞれについて、成功回数から片側
  Clopper–Pearson 下限を作り、それが `4/5` 以上であることを要求する。
- 認証の試行 `j` 回目に使う条件ごとの alpha は `1/(60 * j * (j + 1))` である。この配分は
  workload ごとに独立している。**3 つの workload を合わせた合計は `1/20` ではなく最大で `3/20` である。**
- 認証に失敗したら次の探索通過候補へ進む。**認証を通った最小の `n` を採用する。**
- 上限まで見ても認証を通る候補が無ければ `no-passing-n` で終わる。**その場合に候補範囲・成功率・
  floor・alpha を後から緩めない。**

### 5.5 数値実験の作り方 (凍結済み)

- 模型は、正規標本の平均と標本分散の十分統計量を使う Monte Carlo である。乱数生成器は PCG64。
- 根 seed の原像は `paper-story-a1-balanced-sizing-root-seed/v1|20260901|paired-mean-block-sigma`、
  その SHA-256 は `e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3`。
- 子 seed の原像は
  `paper-story-a1-balanced-sizing-seed/v1|root=<root>|phase=<phase>|workload=<workload>|condition=<condition>|n=<n>|trials=<trials>`
  とし、認証のときだけ末尾に `|attempt=<attempt>` を足す。
- **試行回数は探索 20,000 回、認証 100,000 回。**
- 生成側と検証側は別の実装として突き合わせるが、**互いに独立な統計の権威ではない。**

### 5.6 手順が選んだ値

3 つの workload はいずれも最小の実現候補 `n = 30` で、探索と認証を 1 回目で通った。
候補格子のうち評価したのは各 workload 1 件である。

| workload | `n` | `df` | `k` | 認証試行 | 3 条件の片側下限 (最小) |
|---|---:|---:|---|---:|---|
| write-heavy | 30 | 29 | 2.8315526875186725 | 1 回目 | 0.99592040309507701 (`zero`) |
| balanced | 30 | 29 | 2.8315526875186725 | 1 回目 | 0.99995212622855378 (3 条件とも 100000/100000) |
| read-heavy | 30 | 29 | 2.8315526875186725 | 1 回目 | 0.99995212622855378 (3 条件とも 100000/100000) |

いずれも要求値 `4/5` を大きく上回る。**これは正規模型の上での値であって、本走で実際にその割合が
実現することの保証ではない** (8 節)。

### 5.7 証拠の束縛

| 役割 | path | SHA-256 |
|---|---|---|
| pilot の結果 (sizing の入力) | `output/insights/2026-09-01_paper-story-a1-balanced5-pilot/sizing-pilot.json` | `b4201083cc02434b6b300eb24b6916304bfcadc17c7259257e5cf2ee5a7451ed` |
| sizing 証明書 | `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-certificate.json` | `41d041963c8f3a175b5501810f52ab2619d9285f6f1eeb176790698131fc8299` |
| 別実装による再現の受領証 | `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-replay-receipt.json` | `5027d9e7a8ef26441f44ee8bde26bb4d1aa18b99a6fa3337382ada29ddbad540` |

受領証が束縛している道具の bytes は次の 2 つである。

| 道具 | SHA-256 |
|---|---|
| `tools/size_paper_story_a1_balanced.py` | `4fa604a121e95c9b9f55c414f25098f7edd1f610e445bf53fc0ef85111315e13` |
| `tools/verify_paper_story_a1_balanced_sizing.py` | `8c3c2066395bc82b6b2499c8adaaf3b833947163a7c2d75e55de05fc8e957607` |

### 5.8 登録値の照合 (D1452)

反復数を決める道具は、試行回数を 1 以上 1,000,000 以下、候補範囲を `28 <= n_min <= n_max <= 4096` の
範囲で受け取る。**道具はこの文書の値を強制しない。** そのため、本走 policy を読む consumer が
証明書の申告値を登録値と照合する。照合する 5 つは次のとおりで、いずれも型込みの exact 一致である。

| 証明書の field | 要求する値 |
|---|---|
| `policy.search.trials` | `20000` |
| `policy.certification.trials` | `100000` |
| `policy.candidate_grid.registered_minimum` | `28` |
| `policy.candidate_grid.maximum` | `4096` |
| `policy.root_seed.digest` | `e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3` |

**この照合が無ければ何が通るか。** 証明書の `candidate_grid.maximum` を `4096` から `4095` に
書き替えても、実現候補列は `30, 40, …, 4090` のままで変わらず、選ばれる `n` も変わらない。
したがって再現側の検査も通る。登録範囲と違う設定で反復数を決めた証明書が、本走 policy に
束縛されうる。上の 5 値の照合はこの経路を閉じる。

**この照合が主張しないこと。** 照合は「申告された設定が登録値と同じか」だけを見る。証明書の
数値そのものの再計算は別実装の再現が担い、その再現は独立な統計の権威ではない。

---

## 6. 走行・品質・無効・再走の規則

### 6.1 走行

pilot 事前登録 §6.1 と同じである。異なるのは出力先だけである。

- 1 workload = 1 campaign。両 arm の build と verify を、最初の bench ブロックより**前に**完了する。
- `bench_lock()` は 1 workload につき 1 回だけ取り、全ブロックを通して保持する。
- 静定は workload のスケジュール開始時にちょうど 1 回。
- 競合テナントの検査は 5-rep arm ブロックごとに、その前に行う。検知したらその workload を止める。
- `bench_max_rounds = 1`。自動再試行は行わない。
- 計測の durable な置き場は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement`、
  成果物の公開先は `output/insights/2026-09-13/paper-story-a1-balanced5-sized` とする。
  公開は終端の生の束を、**一度しか作れない宛先**へ書き出す形で行う。
  **pilot の公開先には何も書き足さない。**
- CCBench は `511c9538e4e8efa54b45cda62e72389ed3b706ec` を canonical pin とし、追跡ファイルが
  汚れていないことを pilot と同じ 5 つの境界で要求する。

### 6.2 品質

- 集約 CV = その arm の全 rep の TPS の標本標準偏差 ÷ 同じ TPS の算術平均。
- ブロックごとの CV は**診断専用**であり、集約 CV の代わりにも、その平均にもしない。
- `unstable` は `集約 CV > 0.05` とする。
- 静定できない・CV が定義できない・throughput が無い場合は、いずれもその workload を止める。

### 6.3 無効の規則

pilot と同じ 16 の規則を、同じ順序・同じ文言で使う。

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
実際に無効化する。

本文書は、ここに書いた各条件を実際に拒否する実装が存在することまでは主張しない。
登録した判定の規則であって、実装の完全性の証明ではない。

### 6.4 再走

再走してよい理由は次の閉じた列挙だけである。いずれも bench が始まる**前**の失敗である。

- `build-failure-before-bench`
- `verify-failure-before-bench`
- `competing-tenant-detected-before-bench`
- `scheduler-or-infrastructure-failure-before-bench`

**性能の出力は再走を正当化しない。** `rep_notes` が空でない・`rounds != 1`・`unstable` は
再走せず、その workload を無効として確定させる。

---

## 7. この本走の結果で、何ができて何ができないか

### 7.1 できること (受理、認可後)

- 3 つの workload それぞれについて、30 対の差の算術平均と、5.1 節の区間を作ること。
- 5.2 節の分類を、その workload の走行に対して与えること。

### 7.2 できないこと (拒否)

- **pilot の観測値を最終推定へ混ぜること。** pilot は 1 点も入らない。
- **pilot に 5.2 節の分類を与えること。** その分類式は反復数の候補を評価するための道具であって、
  pilot の結果に貼る札ではない。
- 一部の workload だけが完走した走行、または無効になった workload を含む走行から、
  全体の結論を作ること。workload をまたぐ結論は作らない。
- この走行を認可なしに投入すること。
- `formal=false` / `promotion_prohibited=true` を、この文書や policy の編集だけで反転させること。

### 7.3 現時点の状態

- **本走は未投入である。結果は存在しない。**
- 本文書と機械可読の policy の凍結は、**計測経路が本走を実行できる状態になったことを意味しない。**
  現行の実装には、source 契約・hydrate 入力・依存 source の staging・source binding の生成・
  amended build の受理形が pilot 専用のままになっている箇所が残っている。
  これらを揃える作業は本文書の範囲外であり、別途行う。

---

## 8. この設計で言えないこと

- **配置は識別可能性を上げるためのものである。** 時間隔の交絡や残留効果が無い、あるいは
  消えたことの証拠ではない。推定対象は 5-rep 均衡スケジュール固有のものにとどまる。
- **反復数の設計は、pilot から作った sigma と baseline 水準を真値として固定した正規模型の上での
  評価である。** 正規性・定常性・pilot と本走の同分布性は、この手順では検査できない。
  したがって 5 節の `4/5` も 5.6 節の下限も、本走で実際にその割合が実現することの保証ではない。
- **`rep_notes` が空であることの要求は、反復数に対して急速に壊れる。** 各反復で note が出るかどうかが
  互いに独立で、共通の確率 p を持つと仮定すると、1 workload が壊れる確率は `1-(1-p)^(2n)` である。
  本走 (n=30、2n=60) なら p=0.1% でも約 5.8% になる。**これは独立を仮定した感度分析であって、
  p の推定でも、反復間の依存を測った結果でもない。** 依存が強ければこの値より小さくなる。
  それでも再走しないのは、note に残る典型が部分的な rep timeout であり、遅い反復ほど起きやすい
  性能依存の欠測だからである。これを理由に測り直せば、速く完走した試行を選ぶことになる。
- **本走の root seed は pilot の後に選んだ値である。** 導出原像を先に固定し、pilot の観測も
  本走の観測も見てから選び直さないことで前向き性を保つが、「pilot より前から決まっていた」とは言えない。
- **source-routed な trace0 の証拠は、単体の成果物だけでは閉じない。**
- **workload をまたぐ結論を作らない。** 3 つの workload は独立に扱う。

---

## 9. 還元判断

CCBench 本体への還元候補は含まない。本文書は本走の妥当性文書である。
