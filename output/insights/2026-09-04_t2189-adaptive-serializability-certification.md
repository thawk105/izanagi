# 調整済み adaptive backoff は、測った条件で直列化可能性を破っていない — 24 trace・1.46 億トランザクション・anomaly ゼロ

**種別:** 正しさの認証結果。**認証されたのは正しさだけである。**
性能値そのものは別の trace-disabled 走行で得たものであり、本文書はそれを認証しない
(絶対規律 1 に従い、正しさ検証は trace-enabled build の別 run で行った)。

対象は `2026-09-02_cicada-adaptive-three-constants.md` が測った調整済み 3 定数である。
同文書は「認証されていない」と宣言していた。本文書がその欠落を埋める。

## 結論

固定条件 (records 1,000,000 / threads 48 / extime 3 秒 / max_ope 10 / zipf 0.9 / rmw 0、
workload rr5・rr50・rr95、独立反復 8、計 24 trace) の下で、調整済み定数
(刻み 1 µs / 上限 1000 µs / 更新間隔 2560 µs) の trace-enabled 走行 24 件すべてが
verifier で certified serializable となり、**anomaly を 1 件も観測しなかった**。

| 項目 | 値 |
| --- | --- |
| 走行 | 24 件 |
| 検証したトランザクション | **145,904,299** |
| read / write | 1,115,119,581 / 331,639,309 |
| 依存グラフの辺 | **2,275,338,484** |
| abort | **189,132,818** |
| **anomaly** | **0** |
| cycle | 0 |

workload 別:

| workload | txn | 辺 | abort |
| --- | --- | --- | --- |
| write-heavy (rr5) | 16,250,241 | 159,428,241 | 90,717,878 |
| balanced (rr50) | 25,422,584 | 352,941,303 | 78,424,675 |
| read-heavy (rr95) | 104,231,474 | 1,762,968,940 | 19,990,265 |

**abort が 1.89 億回起きている。** backoff は abort 時にしか働かないので、
この走行群は adaptive backoff の経路を確実に通っている。abort ゼロの走行を認証しても
調整済み定数について何も検査したことにならないため、これは認証の必要条件として
gate に入れてある。

## 主張してよい範囲と、してはいけない範囲

**書いてよいのは上の 1 文だけである。** 次は主張しない。

- 条件を外した一般化 (「調整済み adaptive は直列化可能性を破らない」)。
  測ったのは上記の固定条件だけである。
- 測っていない thread 数・records・extime・workload への外挿。
- **性能値そのものが認証されたという表現。** 認証したのは正しさだけである。
- `1-ε^n` などの形式的な信頼度。**seed を制御していないので算出できない。**
  CCBench に seed CLI は無く、`include/random.hh` の `Xoroshiro128Plus::init()` が
  各 instance で `std::random_device` を読む。8 反復は再現可能な seed 系列ではなく、
  独立 process による schedule の異なる反復である。成果物は `rng_seed_controlled=false` と
  `independent_run_slot` を記録し、`seed` という語を使っていない。

## 証明面 — この認証が何に支えられているか

verifier は 2026-09-03 に、**証明面を持たない protocol が certified を名乗れないよう**変更された。
lock 被覆 (X 行) と permutation 保存 (P 行) の emitter は **Silo にしか無く**、si と mocc は
対応するカウンタが構造的に 0 になる。つまり両者は「検査を通った」のではなく「検査が無い」まま
clean と判定され、Silo より弱い証明面で certified を名乗れていた。さらに証明面の判定は
**build の source snapshot へ束縛**された — 判定の入力と build が実際にコンパイルした bytes が
同一であることを要求する変更である。

**本認証は Silo を対象とし、この新しい判定の下で行っている。**
`--protocol silo` と `--ccbench-root <build が使った隔離 checkout>` を、target と陽性対照の
両方へ渡す。`--ccbench-root` は `buildcache.build()` へ渡した隔離 checkout を patch context 内で
解決したものであり、共有 `external/ccbench` の事後読み直しではない。

## 恒真な緑を殺す仕掛け

**認証が「検査するものが無いので緑」にならないことを、機構で保証している。**
1 件でも欠ければ reject する連言である。

1. trace-enabled build であること。判定は自己申告ではなく
   `buildcache.cache_key()` の戻り値末尾が `_t1` であること。
2. run の rc が 0。
3. trace directory が run 直前に空で作られていること。
4. **verifier JSON の `results[0].trace_dir` が、その run のために生成した directory の
   正規化済み exact path と一致すること。** これが無いと、target だけ既知の緑 trace へ
   差し替えて認証を得られる。親は `g6_silo_serial_1thread` を渡すと certified が返ることを
   実測して、この攻撃が実在することを確認した。
5. verifier の exit code が **0 ちょうど**。argv に `--lenient` を含めない。
   `--protocol` と `--ccbench-root` が期待値と一致すること。
6. `--expected-commits` に stdout の単一 `commit_counts_` 行を渡し、
   `batch_commit_counts_` が 0 であること。
7. **非空振り:** `txns > 1` / `reads > 0` / `writes > 0` / `edges > 0` かつ
   **stdout の `abort_counts_` が正の整数**であること。
8. `integrity.clean` が true。
9. **同一 job 内で陽性対照が先に走り、契約を満たすこと。**
10. verifier closure の identity が事前固定値と exact 一致すること。

### 陽性対照

`orchestrator/tests/fixtures/r8_silo_broken_norw/` を、target と同じ helper・同じ argv 構成で
先に通す。実 emitter 由来 (broken-Silo の `CCBENCH_TRACE=1` 実走から切り出した静的 fixture で、
live broken build ではない)。要求は exit code 1 ちょうど、`non_serializable == 1`、
`total_cycles == 4`、全 anomaly が `phenomenon == "G2"`、各 edge の `reasons` 非空、
少なくとも 1 つが `type == "rw"`。

**版 field は型別に要求する。** `ww` と `rw` は `u_ver` と `v_ver`、**`wr` は `u_ver` のみ**。
親が実データで確認した — 全 edge に版 2 つを要求すると陽性対照自身が偽赤になる。

## 規律 3 — 構造化して返している

verifier は pass/fail で終わらせず、anomaly ごとに trx の環 (`cycle`)、各辺の `from`/`to`、
依存の種別 (`ww`/`wr`/`rw`)、`key`、版の対を返す。本走行では anomaly がゼロだったので
witness は空だが、**機構が実際に発火することは陽性対照で毎 job 確認している**。

親が陽性対照を通した実例 (証明面の 2 引数を付けた形):

```
verdict=non-serializable, certified=False, total_cycles=4
anomaly[0]: phenomenon=G2, cycle=[191, 192, 195]
  191 -> 192  ww key=...0000 (1,135)->(1,136) / wr key=...0001 (1,135) / wr key=...0000 (1,135)
  192 -> 195  ww key=...0000 (1,136)->(1,137)
  195 -> 191  rw key=...0000 read(1,133)->overwritten(1,135)   <- 環を閉じる rw = G2 の根拠
```

## 相ごとの CPU と経過

**律速はビルドでも計測でもなく直列性検査である。** 相を混ぜた比は意味を持たないので分けて記録した。

| 相 | 内容 | 実測 |
| --- | --- | --- |
| **run** | 48 スレッド x 3 秒 | CPU/経過 = **9.30〜28.17** |
| **verify** | 検査器 | 経過 **87.1〜458.9 秒**、最大 RSS **37.4 GiB** |

**verify 相の比が 1.0 近傍になるのは設計どおりである** — これを run 相と混ぜて 1 つの比にすると
何も意味しない。run 相はいずれも 1.0 から十分離れている。

**CPU 時間は job body 側で採っている。** この機体の `qstat` に履歴 option が無く、
job 終了後に CPU 時間を取れない。稼働中に採れる CPU 列も子プロセスを集計しないため、
比の根拠にできない。

## 投入設計と、正直に書くべき差

**1 request = 1 workload x 1 slot の 24 request** に割って投入した。
1 ノードに 3 workload を束ねると検査時間が 3 倍積み上がるため採らなかった。
最悪条件 (read-heavy) の 1 本を pilot として先に流し、gate が通ることを確かめてから
残り 23 本を投げた。pilot は 24 件のうちの 1 件として数えている。

**24 job は 9 ノードに分かれて走った** (`bnode004`, `bnode009`, `bnode014`, `bnode017`,
`bnode018`, `bnode019`, `bnode077`, `bnode089`, `bnode097`)。クラスタが混んでおり、
1 ノードへ複数 job が載った。**直列化可能性の判定は trace の性質なのでノード共有で変わらないが、
上記の時間の数値は共有下で得たものである。** 性能値としては使えない。

## 再現条件

| 項目 | 値 |
| --- | --- |
| 定数 | `BACKOFF_INCR_MILLI=1000` / `BACKOFF_MAX_US=1000` / `BACKOFF_UPDATE_US=2560` / `BACK_OFF=1` |
| protocol | Silo |
| ccbench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` + `patches/cicada-adaptive-params.patch` |
| ビルド | trace-enabled (`-DCCBENCH_TRACE=1`)、perf 計測なし |
| 環境 | Pegasus 計算ノード 9 台、gen_S |
| job | `977197` (pilot) と `977221`〜`977243` |
| driver | `tools/pegasus/probes/t2187_adaptive_const_probe.py --mode certify` |
| verifier | `orchestrator/verify.py` + `orchestrator/verifier/*.py`。identity を事前固定して照合 |

## 成果物

- group receipt: `izanagi-job-evidence/t2189-adaptive-certify/attempt-2/group-receipt.json`
  (repo 外、sha256 `b1186d54da7f1174f610b2c850f5449957443ab2d25a28bc3799f35371182b6e`)。
  24 件の個別 receipt を内容で再検証し、24 件すべてが certified のときだけ発行される。
  `proof_surface` field を持つ。
- 個別 receipt 24 件と生 trace: 同 directory (repo 外)。

**group が 24 件の同一性を束縛する対象はソース内容とゲノムであり、binary の bytes ではない。**
24 台が独立にビルドし、cache key に job ごとの admission receipt が入るため、binary は
bit 単位では一致しない。束縛すべきは「同じコードを試したか」であって build 成果物の bytes
ではないので、`source_bytes_sha256` と `genome_sha256` の一致を要求している。

## 先行する attempt-1 の扱い

**2026-09-03 に、同じ条件で 24 件を認証した走行がある** (job `971189`, `972815`〜`972837`、
24 ノード、txn 1 億 4,451 万、辺 22 億 5,362 万、anomaly 0、group receipt sha256
`5c5311e6f0c4fef52cb3e680d4983595d116e608e3078c811ad2d85f91f623a9`)。

その直後に verifier の意味論が変わった (上記「証明面」)。10 module のうち 6 つが変わっている。
**絶対規律 7 は「意味論の版の変更」を再検証の発火条件として挙げる。**
そこで新しい verifier で 24 件を取り直したのが本文書の attempt-2 である。

**attempt-1 を取り消さない。** 同規律は「再現できないことと、事実でないことは別」とも定める。
attempt-1 は、それを行った verifier 版における事実として有効である。identity を事前固定して
あるため、どの版で認証したかは今も参照できる。**現行コードでの認証は attempt-2 である。**

なお attempt-1 の生 trace を保持していたため、やり直しにあたって走行の再現は不要だった。

## この走行が言えないこと

- **単一環境である。** Pegasus の 48 コア機のみ。
- 測った条件の外は何も言っていない。
- 性能値は依然として trace-disabled 走行の産物であり、本文書は認証しない。
- 有限の 24 trace で anomaly を観測しなかったという操作的事実であって、
  設定一般が直列化可能であることの証明ではない。
