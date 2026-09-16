# B-10 静的 backoff 右 tail の結果節 — 登録した述語では、表現可能域 9999 マイクロ秒までに飽和を観測しなかった (2026-09-16)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である (D1631)。

**本稿は同系列の既存の稿を改めるものではない。** 同系列は append-only であり、A-2 / A-6 / B-7 の既存の稿は
いずれも 1 byte も変えずに残る。それらは採用静的 backoff の certification と退行の材料であり、本稿が書く
静的 backoff 右 tail の記述的な特性化とは別の protocol・別の cohort についての事実である。

**本稿の言い方は事前登録が固定している。** `docs/b10-backoff-static-tail-preregistration.md` §4.5 は、域内非飽和の
結末について「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」とだけ
書き、**「飽和しない」「飽和点が存在しない」とは書かない**と定める。本稿はこの固定に従う。9999 マイクロ秒は
物理的な限界ではなく、現行の符号化が表現できる上限である (同 §3)。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

results 系列は「1 file = 完走した 1 つの protocol または campaign 群の結果」を単位とする (D1631)。
本稿の単位は、**事前登録 `docs/b10-backoff-static-tail-preregistration.md` に対して 2026-09-15 (JST) に完走した
1 つの cohort** — group `b10-backoff-grid-20260915T061814Z-545445`、`run_kind` `t2500-tail-formal`、
3 workload × 8 点 = 24 cell — である。3 つの campaign は事前登録 §4.9 の同一性検査を通って 1 つの cohort を成す
(§1.1)。

### 0.2 書くもの

事前登録が固定した格子・動作点・反復数・判定式の下で得られた、集団 verdict と workload ごとの状態、
18 区間の分類と推定値、同じ格子上の throughput と abort 率 (過抑制の費用)、全 24 cell の生標本、
実行 identity、正しさの記録、この結果が言わないことの一覧、転記元の SHA-256。

### 0.3 書かないもの

- **「飽和しない」「飽和点が存在しない」。** 言えるのは事前登録 §4.5 の固定表現までである。
- **9999 マイクロ秒より右についての主張** (事前登録 §3)。
- **機序。** なぜ abort 率がこの形で下がるのかは本稿の対象外である (D1678、D1724)。
- **性能の認証。** `performance_certified` は `false` である。**ここにある性能値を根拠に variant を
  採用してはならない** (絶対規律 2)。
- **研究として成功か失敗か、新規性があるかの宣告** (D12)。`not-observed-in-any-workload` と `declining` は
  事前登録の述語が出した分類名であり、成否のラベルではない。
- **当時の実行全体を独立に監査したという主張** (§3 の限定 4)。
- **同じ事前登録に対する他の cohort との関係。** 本稿は 09-15 の 1 本の cohort だけを扱う。
- **論文図。** 09-15 cohort を描いた図は存在しない (§3 の限定 11)。
- **B-10 や [T-2647] の閉鎖。** 本稿は結果節の材料を置くだけである。
- **この結果が他の workload・他の機体・他の CCBench pin・他の protocol へ転移するという主張。**

---

## 1. 条件 — 事前登録が固定したものと、成果物が記録したもの

### 1.1 事前登録への束縛

3 つの campaign はいずれも次を記録している (集団報告 `t2500-backoff-static-tail-formal.json` の
`campaigns[].identity` と `-complete.json` の `preregistrations[]`、3 件とも同値)。

| 事項 | 値 |
|---|---|
| 事前登録 commit | `cad6f46d86ae4dc31edadfbdfad39c65ed73d70a` |
| 事前登録文書の blob SHA-256 | `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` |
| spec (§5 の機械可読 spec) の SHA-256 | `08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef` |

本稿の起草時、作業ツリーの `docs/b10-backoff-static-tail-preregistration.md` の raw bytes の SHA-256 は同じ
`8084be04…` であり、commit `cad6f46d8` は HEAD の祖先である (実測)。この commit は 2026-09-10 の追補を含む版で
あり、初版 (`9e97d27b8`) ではない。追補は末尾への 21 行の追加のみで、§5 の spec の bytes は両版で同じである
(`output/insights/2026-09-16/b10-tail-formal-submit/README.md` §3.1)。**ただし、この追補は事前登録 §0 の
更新契約 (「変更理由と変更時点を本節へ明記する」) を満たしていない** — §0 に追補の記載が無い (同 insight §3.2)。
これは文書自身の更新契約違反として残る。**一方で、これを §7 の失敗条件 12 (commit・blob・spec の未記録または
bytes 不一致) や `invalid` へ読み替えない。** 3 campaign の束縛記録はいずれも追補込みの commit・blob・spec と
一致しており、§0 の記載場所違反を §7 のどれかへ当てる規定は事前登録に無い (同 insight §3.2)。

事前登録 §4.9 が 3 job の間で一致を要求する項目 — CCBench の source digest と toolchain、環境契約と較正の
identity、事前登録の commit・blob・spec、動作点の literal — は、3 campaign の `identity` で**すべて同値**である
(実測: 各 field の異なり数が 1)。workload 座標だけが設計どおり 3 job で異なる。

### 1.2 格子・動作点・反復数・測定順

いずれも事前登録 §4.1 / §4.2 の literal と一致する値が `identity` に記録されている。

- 格子: 右 tail 7 点 (1250 / 1768 / 2500 / 3535 / 5000 / 7070 / 9999 マイクロ秒) + 境界参照 1 点
  (1000 マイクロ秒) の **8 点**。`BACKOFF_FIXED` の raw 値は順に 3250 / 3768 / 4500 / 5535 / 7000 / 9070 /
  11999、境界参照は 3000 (物理値 `b >= 1000` に対し `b + 2000`)。genome は
  `silo|BACKOFF_FIXED=<raw>,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`。
- 境界参照 1000 は測定・報告するが、区間の集合には入らない (事前登録 §4.1 / §4.4)。
- 動作点: `records = 1000000`、`threads = 48`、`extime_s = 3`。zipf skew 0.9、rmw 0、max ope 10。
  read ratio は write-heavy 5 / balanced 50 / read-heavy 95。
- 反復: 性能測定 5 rep/cell、正しさ検査 5 rep/cell。8 点 × 3 workload = 24 cell、性能 120 rep、正しさ 120 記録。
- 測定順 (物理値、マイクロ秒): write-heavy `2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070`
  (seed `0xB10005`)、balanced `1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999` (seed `0xB10050`)、
  read-heavy `3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000` (seed `0xB10095`)。
- 時間枠: sweep 上限 11700 秒、PBS 予約 18000 秒、`reduce_grid_or_reps_on_timeout = false`。

### 1.3 実行 identity

| workload | campaign id | job | 開始 (JST) | ホスト | `sweep_elapsed_s` | `job_elapsed_s` |
|---|---|---|---|---|---:|---:|
| write-heavy | `t2500-backoff-static-tail-formal-silo-write-heavy-sweep-9cda88f0` | `0:998865.nqsv` | 2026-09-15 15:19:06 | `bnode017` | 823.31 | 836.44 |
| balanced | `t2500-backoff-static-tail-formal-silo-balanced-sweep-1c8d08f7` | `0:998866.nqsv` | 2026-09-15 15:19:07 | `bnode018` | 820.90 | 833.08 |
| read-heavy | `t2500-backoff-static-tail-formal-silo-read-heavy-sweep-9064a9e0` | `0:998867.nqsv` | 2026-09-15 15:19:07 | `bnode019` | 825.31 | 837.47 |

開始時刻は `completion.scheduler.job_start_epoch` を JST へ直したもの、ホストは各 job root の
`qstat-f.stdout` の `Execution Hosts` 欄である。3 job は別ノードで同時刻に走った。所要は事前登録 §4.2 の
見積り (約 20 分/job) の内側で、sweep 上限・PBS 予約からは大きく余裕がある。`job_elapsed_s` は driver が
実行 receipt を書く直前までの値であり、job の最終終了時刻までは含まない。

3 campaign に共通の identity:

| 事項 | 値 |
|---|---|
| 測定環境 | `pegasus` (計算ノード、48 スレッド) |
| CCBench pin (`repo_stock_pin`) | `511c953` (各 job の `env/ccbench-worktree.json` は gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec` を detached で checkout し `tracked_clean: true`) |
| CCBench source digest | `db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba` |
| toolchain | `x86_64-linux-gnu-gcc-11` / `g++-11` (Ubuntu 11.4.0) |
| 較正 identity | `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` (`753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`) |
| 環境契約 identity | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| `freeze_trees_sha256` (各 job root の `completion.json`) | `c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3` (3 job で一致) |
| perf | 不使用。`perf_observation.claim_scope` は `throughput: eligible` / `perf_required: unsupported`、preflight は `available: false` |
| 性能測定の build | trace 無効ビルド。`perf_bin_sha256` は 1 workload あたり 8 個が相異なる (事前登録 §4.6 の要求) |

**izanagi 側の source commit は成果物に記録されていない。** 集団報告、`-complete.json`、campaign lock、
execution report、job root の `completion.json` / `env/` / stdout のいずれにも無い (実測)。izanagi 側の identity
として残っているのは、事前登録 commit `cad6f46d8` への束縛と、3 job で一致する `freeze_trees_sha256` である。

### 1.4 正しさの記録

正しさは trace 有効ビルドの別走行から来る (絶対規律 1)。集団報告の `points[].correctness` は
1 workload あたり 40 記録 (8 cell × 5 rep)、**3 workload 合計 120 記録すべてが `payload.certified` = `true`、
`payload.anomalies` = 0、`payload.verdict` = `serializable`** である (実測)。各記録は `source_measurement` =
`trace_enabled`、`source_run_kind` = `t2500-tail-formal` を持ち、`wal_record_digest`・`attempt_id`・
`campaign_lock_digest` で WAL の record と campaign に束縛されている。性能側の rep 記録は `source_measurement` =
`trace_disabled` で、同じ `source_run_kind` を持つ。正しさ検査の mode
(`correctness_mode`) は 3 campaign とも `legacy` で、探索走 `t2418-explore` の記録と同じ値である
(事前登録 §4.6 の要求)。

**正しさ検査の条件は、性能測定の条件と同じではない。** 3 campaign の `identity.correctness_flags` はいずれも
`extime 1`、`thread_num 4`、`ycsb_tuple_num 200`、`ycsb_rratio 50`、`ycsb_rmw true`、`ycsb_max_ope 5`、
`ycsb_zipf_skew 0.9` で、性能側の 48 スレッド・1,000,000 records・3 秒・workload 別の read ratio とは別の
設定である。これは §3 の限定 6 に書く。

**これは性能の認証ではない。** `performance_certified` は `false` である。

---

## 2. 結果

### 2.1 集団 verdict と workload ごとの状態

集団報告 (`t2500-backoff-static-tail-formal.json`) が記録する出力:

| 事項 | 値 |
|---|---|
| `verdict` | **`not-observed-in-any-workload`** |
| `failures` | `[]` (loader が記録した失敗は 0 件。集約 verdict が `invalid` でないことの根拠) |
| `performance_certified` | `false` |
| `schema_version` | `t2500-backoff-static-tail-formal-report/v1` |
| campaign の admission | 3 件とも `admitted` / `admitted-new-schema` |

| workload | `state` | `saturation_location` | `local_flat_intervals` | 6 区間の `state` |
|---|---|---|---|---|
| write-heavy | `not-observed` | `null` | `[]` | 6 件すべて `declining` |
| balanced | `not-observed` | `null` | `[]` | 6 件すべて `declining` |
| read-heavy | `not-observed` | `null` | `[]` | 6 件すべて `declining` |

3 workload × 6 = 18 区間すべてが `declining` で、`saturated` も `indeterminate` も 0 件である。
`confirmed_nonmonotonicity` と `upward_wiggle` は 18 区間とも `false` である (統計的に支持された上昇は無い。
事前登録 §7 の失敗条件 8 に当たらない)。

事前登録 §4.5 の結末表に当てると、3 workload すべてが `not-observed` なので集約 verdict は
`not-observed-in-any-workload` になる。**この cohort について言えるのは、「この事前登録の述語では、
表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」までである。**

### 2.2 区間ごとの推定 — 18 区間の `qhat`、同時区間、分類

事前登録 §4.4 の定義による。`qhat` は隣接 2 点の abort 率の対数傾き (backoff の対数あたり)、`[qL, qU]` は
36 の片側限界に Bonferroni を適用した同時区間 (familywise 0.05)、`L` = `1 − 2^qU` は「backoff 倍増あたり
最小でも何割 abort 率が下がるか」の同時下限、`U` = `1 − 2^qL` は同時上限、`U_flat` は `qhat = 0` と置いて
評価した診断値である。分類は §4.4 の順で、`L > 0.05` を満たす区間が `declining` (低下が続いている) になる。

**write-heavy**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.5437 | −0.5601 | −0.5273 | 0.3062 | 0.3217 | 0.0113 |
| 1768 → 2500 | `declining` | −0.5518 | −0.5800 | −0.5237 | 0.3044 | 0.3310 | 0.0193 |
| 2500 → 3535 | `declining` | −0.5625 | −0.5904 | −0.5346 | 0.3097 | 0.3358 | 0.0191 |
| 3535 → 5000 | `declining` | −0.5771 | −0.6018 | −0.5525 | 0.3182 | 0.3411 | 0.0169 |
| 5000 → 7070 | `declining` | −0.5907 | −0.6151 | −0.5663 | 0.3247 | 0.3471 | 0.0168 |
| 7070 → 9999 | `declining` | −0.6137 | −0.6632 | −0.5642 | 0.3237 | 0.3685 | 0.0337 |

**balanced**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.5355 | −0.5586 | −0.5123 | 0.2989 | 0.3210 | 0.0159 |
| 1768 → 2500 | `declining` | −0.5542 | −0.5859 | −0.5225 | 0.3038 | 0.3338 | 0.0217 |
| 2500 → 3535 | `declining` | −0.5896 | −0.6247 | −0.5545 | 0.3191 | 0.3514 | 0.0240 |
| 3535 → 5000 | `declining` | −0.6265 | −0.6593 | −0.5938 | 0.3374 | 0.3668 | 0.0225 |
| 5000 → 7070 | `declining` | −0.6602 | −0.6992 | −0.6212 | 0.3499 | 0.3841 | 0.0267 |
| 7070 → 9999 | `declining` | −0.7110 | −0.7543 | −0.6676 | 0.3704 | 0.4072 | 0.0296 |

**read-heavy**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.4844 | −0.5073 | −0.4616 | 0.2738 | 0.2965 | 0.0157 |
| 1768 → 2500 | `declining` | −0.4964 | −0.5237 | −0.4690 | 0.2776 | 0.3044 | 0.0188 |
| 2500 → 3535 | `declining` | −0.5068 | −0.5372 | −0.4764 | 0.2812 | 0.3109 | 0.0208 |
| 3535 → 5000 | `declining` | −0.5208 | −0.5539 | −0.4877 | 0.2868 | 0.3188 | 0.0227 |
| 5000 → 7070 | `declining` | −0.5193 | −0.5499 | −0.4887 | 0.2873 | 0.3169 | 0.0210 |
| 7070 → 9999 | `declining` | −0.5518 | −0.6102 | −0.4934 | 0.2896 | 0.3449 | 0.0397 |

値は集団報告の `workloads[].intervals[]` を小数第 4 位に丸めて転記した。`L` は `qU` から `1 − 2^qU` で再計算して
一致を確かめた。

**読めること (記述)。** `L` は 18 区間すべてで 0.27 以上であり、述語の閾値 0.05 を大きく超える。倍増あたりの
低下率の同時下限が 27〜37% ということである。`U_flat` は 18 区間すべてで 0.05 以下 (0.0113〜0.0397) であり、
事前登録 §4.4 が「真に平坦な区間が `U_i <= 0.05` に届くかどうかの目安」と定める診断値の意味で、分解能の不足を
非飽和の証拠に化かしている状態ではない。**この診断値は分類には使わない** (同 §4.4)。

**読めないこと。** `qhat` が右へ行くほど大きな負の値になること (write-heavy −0.54 → −0.61、balanced
−0.54 → −0.71、read-heavy −0.48 → −0.55) は集団報告の数値の記述であり、その機序を本稿は言わない
(D1724 の限界: 静的 tail について書けるのは記述的な会計まで)。

### 2.3 過抑制の費用 — 同じ格子上の throughput と abort 率

事前登録 §3 は「同じ格子上の throughput を、過抑制の費用として必ず併記する」と要求する。次は
`t2500-backoff-static-tail-formal.dat` (1 行のヘッダと 120 行のデータ。列は workload・backoff・rep・aborts・
commits・abort_rate・throughput_tps の 7 つ) から本稿の起草時に再計算した **5 反復の算術平均**である。
中央値ではない。

throughput (毎秒トランザクション数):

| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 993,106.4 | 718,264.8 | 1,703,577.8 |
| 1250 | 905,601.2 | 659,017.0 | 1,545,212.0 |
| 1768 | 787,038.8 | 570,909.6 | 1,322,901.2 |
| 2500 | 684,422.6 | 496,833.6 | 1,133,420.6 |
| 3535 | 595,824.8 | 436,522.8 | 971,805.2 |
| 5000 | 520,175.6 | 387,841.6 | 834,521.0 |
| 7070 | 455,649.6 | 347,912.8 | 715,417.0 |
| 9999 | 401,697.6 | 317,246.2 | 618,689.8 |

abort 率 (`aborts / (aborts + commits)` を rep ごとに整数カウンタから全精度で再計算し、5 反復を平均。
事前登録 §4.3。CCBench が印字する小数第 4 位の丸め値は使っていない):

| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.042344 | 0.058753 | 0.023749 |
| 1250 | 0.037662 | 0.051936 | 0.021324 |
| 1768 | 0.031191 | 0.043137 | 0.018027 |
| 2500 | 0.025764 | 0.035602 | 0.015179 |
| 3535 | 0.021202 | 0.029024 | 0.012735 |
| 5000 | 0.017357 | 0.023357 | 0.010631 |
| 7070 | 0.014145 | 0.018582 | 0.008881 |
| 9999 | 0.011435 | 0.014523 | 0.007335 |

変動係数 (標本標準偏差 ÷ 平均、ddof = 1。throughput / abort 率の順):

| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.14% / 0.18% | 0.39% / 0.37% | 0.26% / 0.25% |
| 1250 | 0.22% / 0.21% | 0.24% / 0.23% | 0.27% / 0.30% |
| 1768 | 0.23% / 0.21% | 0.41% / 0.33% | 0.15% / 0.10% |
| 2500 | 0.39% / 0.40% | 0.43% / 0.45% | 0.26% / 0.35% |
| 3535 | 0.26% / 0.26% | 0.47% / 0.45% | 0.40% / 0.42% |
| 5000 | 0.34% / 0.35% | 0.37% / 0.37% | 0.44% / 0.43% |
| 7070 | 0.22% / 0.23% | 0.57% / 0.56% | 0.22% / 0.24% |
| 9999 | 0.65% / 0.66% | 0.53% / 0.56% | 0.78% / 0.76% |

全 24 cell で throughput の変動係数は 0.14〜0.78%、abort 率の変動係数は 0.10〜0.76% であり、事前登録 §4.7 /
§7 の品質 gate (2% 以上で失敗) の内側である。**abort 率の変動係数と throughput の変動係数は別物である**
(同 §4.7)。

**この表は記述的な集計である。** 性能の認証でも機序の説明でもない。tail の左端 1250 から右端 9999 マイクロ秒
までで、5 反復平均の throughput は write-heavy が 0.444 倍、balanced が 0.481 倍、read-heavy が 0.400 倍に
なっている (3 workload とも半分以下)。同じ帯で abort 率は下がり続けている。**abort 率が下がり続けることと、
その帯で throughput が大きく失われることは、同時に成り立っている。** どちらが望ましいかの判定は本稿の外で
ある。

### 2.4 境界参照 1000 マイクロ秒は同一 cohort の点である

事前登録 §4.1 が境界参照 1000 を入れた理由は、正式格子の上端と tail を**同一 job 内で**接続するためである。
本稿の 1000 の値は本 cohort の測定であり、2026-09-10 に完走した `t2266-tail` v2 系列の 1000 マイクロ秒
(`output/insights/2026-09-10/t2266-formal-1000us/README.md`) とは別の走行である。**流用も混合もしていない。**
本稿はその系列の値を転記しない。

### 2.5 全 24 cell の生標本

`.dat` の 120 行を rep 順 (0〜4) に転記した。throughput は毎秒トランザクション数、右列は
`aborts / commits` の整数カウンタである。

| workload | backoff (µs) | throughput (5 rep) | aborts / commits (5 rep) |
|---|---:|---|---|
| write-heavy | 1000 | 994,152, 991,352, 994,382, 991,750, 993,896 | 131,584 / 2,982,456, 131,774 / 2,974,058, 131,749 / 2,983,147, 131,788 / 2,975,252, 131,774 / 2,981,690 |
| write-heavy | 1250 | 904,835, 903,320, 906,101, 908,608, 905,142 | 106,326 / 2,714,505, 106,310 / 2,709,961, 106,344 / 2,718,305, 106,303 / 2,725,826, 106,332 / 2,715,428 |
| write-heavy | 1768 | 789,960, 786,123, 785,218, 786,888, 787,005 | 76,034 / 2,369,882, 75,941 / 2,358,369, 76,035 / 2,355,655, 76,037 / 2,360,666, 76,037 / 2,361,017 |
| write-heavy | 2500 | 683,586, 681,797, 687,747, 686,694, 682,289 | 54,307 / 2,050,758, 54,314 / 2,045,392, 54,285 / 2,063,242, 54,287 / 2,060,084, 54,297 / 2,046,868 |
| write-heavy | 3535 | 594,226, 594,141, 596,851, 596,491, 597,415 | 38,730 / 1,782,678, 38,716 / 1,782,424, 38,713 / 1,790,554, 38,717 / 1,789,473, 38,718 / 1,792,245 |
| write-heavy | 5000 | 522,442, 518,772, 518,772, 519,181, 521,711 | 27,560 / 1,567,326, 27,573 / 1,556,318, 27,574 / 1,556,316, 27,552 / 1,557,544, 27,561 / 1,565,134 |
| write-heavy | 7070 | 455,963, 454,165, 456,929, 455,710, 455,481 | 19,615 / 1,367,889, 19,621 / 1,362,495, 19,616 / 1,370,787, 19,612 / 1,367,132, 19,600 / 1,366,445 |
| write-heavy | 9999 | 400,579, 399,120, 400,830, 405,973, 401,986 | 13,944 / 1,201,739, 13,943 / 1,197,362, 13,930 / 1,202,490, 13,934 / 1,217,919, 13,942 / 1,205,958 |
| balanced | 1000 | 716,775, 715,615, 721,207, 721,331, 716,396 | 134,516 / 2,150,326, 134,477 / 2,146,846, 134,473 / 2,163,621, 134,515 / 2,163,993, 134,533 / 2,149,190 |
| balanced | 1250 | 658,543, 661,297, 659,441, 658,957, 656,847 | 108,292 / 1,975,629, 108,313 / 1,983,893, 108,314 / 1,978,324, 108,305 / 1,976,871, 108,304 / 1,970,542 |
| balanced | 1768 | 573,718, 570,174, 572,629, 567,723, 570,304 | 77,240 / 1,721,156, 77,238 / 1,710,524, 77,246 / 1,717,888, 77,083 / 1,703,170, 77,251 / 1,710,913 |
| balanced | 2500 | 496,768, 499,925, 495,151, 494,626, 497,698 | 55,035 / 1,490,304, 55,032 / 1,499,776, 55,053 / 1,485,453, 55,049 / 1,483,880, 54,942 / 1,493,095 |
| balanced | 3535 | 435,034, 435,725, 435,561, 440,089, 436,205 | 39,164 / 1,305,104, 39,162 / 1,307,176, 39,092 / 1,306,683, 39,146 / 1,320,269, 39,161 / 1,308,617 |
| balanced | 5000 | 385,968, 386,923, 389,232, 387,803, 389,282 | 27,832 / 1,157,905, 27,824 / 1,160,769, 27,826 / 1,167,696, 27,826 / 1,163,410, 27,823 / 1,167,846 |
| balanced | 7070 | 347,103, 346,136, 349,072, 346,421, 350,832 | 19,745 / 1,041,309, 19,762 / 1,038,408, 19,765 / 1,047,217, 19,771 / 1,039,264, 19,764 / 1,052,497 |
| balanced | 9999 | 315,867, 316,293, 319,358, 315,912, 318,801 | 14,027 / 947,601, 14,033 / 948,879, 14,016 / 958,074, 14,028 / 947,738, 14,025 / 956,403 |
| read-heavy | 1000 | 1,710,270, 1,704,454, 1,704,126, 1,698,979, 1,700,060 | 124,358 / 5,130,810, 124,330 / 5,113,363, 124,405 / 5,112,380, 124,416 / 5,096,939, 124,117 / 5,100,182 |
| read-heavy | 1250 | 1,541,237, 1,541,650, 1,549,685, 1,549,806, 1,543,682 | 100,998 / 4,623,711, 101,055 / 4,624,950, 100,956 / 4,649,056, 100,968 / 4,649,418, 101,034 / 4,631,047 |
| read-heavy | 1768 | 1,325,125, 1,320,334, 1,322,610, 1,321,873, 1,324,564 | 72,883 / 3,975,376, 72,738 / 3,961,004, 72,896 / 3,967,830, 72,879 / 3,965,620, 72,887 / 3,973,694 |
| read-heavy | 2500 | 1,137,537, 1,133,564, 1,130,120, 1,134,771, 1,131,111 | 52,298 / 3,412,611, 52,433 / 3,400,692, 52,423 / 3,390,361, 52,431 / 3,404,313, 52,448 / 3,393,334 |
| read-heavy | 3535 | 969,631, 970,537, 972,025, 968,471, 978,362 | 37,613 / 2,908,894, 37,616 / 2,911,611, 37,594 / 2,916,075, 37,611 / 2,905,413, 37,592 / 2,935,088 |
| read-heavy | 5000 | 838,325, 834,745, 830,215, 837,917, 831,403 | 26,896 / 2,514,976, 26,909 / 2,504,235, 26,884 / 2,490,646, 26,901 / 2,513,753, 26,913 / 2,494,211 |
| read-heavy | 7070 | 713,215, 715,761, 714,746, 717,584, 715,779 | 19,236 / 2,139,647, 19,225 / 2,147,283, 19,230 / 2,144,238, 19,229 / 2,152,752, 19,233 / 2,147,337 |
| read-heavy | 9999 | 620,573, 624,050, 615,853, 611,814, 621,159 | 13,715 / 1,861,720, 13,713 / 1,872,150, 13,721 / 1,847,561, 13,704 / 1,835,444, 13,714 / 1,863,479 |

`.dat` の `abort_rate` 列は各行の `aborts / (aborts + commits)` と一致する (120 行とも実測)。集団報告の
`points[].tps` と `points[].reps[].throughput_tps` も同じ値である (事前登録 §7 の失敗条件 19 の対象)。

---

## 3. 限定 (この結果が言わないこと)

1. **「飽和しない」「飽和点が存在しない」とは言わない。** 事前登録 §4.5 が言い方を固定しており、言えるのは
   「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」までである。
   9999 マイクロ秒より右は、符号化を変えない限り測れない (同 §3、§9)。
2. **機序を言わない。** なぜ abort 率がこの形で下がるのか、なぜ `qhat` が右へ行くほど急になるのかは、
   本稿の対象外である (D1678、D1724)。§2.2 と §2.3 は記述的な集計である。
3. **性能を認証していない。** 性能値は trace 無効ビルドの別走行のもので、`performance_certified` は `false`
   である。**この性能値を根拠に variant を採用してはならない** (絶対規律 2)。正しさが認証されたのは
   trace 有効ビルドの別走行 (§1.4) についてである。
4. **当時の実行全体を独立に監査したとは言わない。** 2026-09-16 に本番 CLI で 09-15 の 3 campaign から
   集団判定を再導出したところ、終了コード 0 で 3 成果物とも 09-15 の成果物と byte 単位で一致した
   (`output/insights/2026-09-16/b10-tail-formal-submit/README.md` §4)。これが示すのは「現行の loader が
   そのデータを受理し、同じ judgement を出した」までであり、当時のビルド・resume 操作・失敗 attempt の
   履歴の独立監査は未実施である。
5. **izanagi 側の source commit は成果物に無い** (§1.3)。当時の driver の版を成果物から一意に同定する
   ことはできない。残るのは事前登録 commit の束縛と `freeze_trees_sha256` の 3 job 一致である。
   また、正しさ検査の mode を読むために driver へ渡した探索走 campaign の argv は成果物に保存されて
   いない (同 insight §3.4)。3 本の探索走 campaign はいずれも mode が `legacy` なので、どれを渡したかは
   mode 比較の結果を変えない。
6. **正しさ検査の条件は性能測定の条件と同じではない** (§1.4)。`legacy` mode の検査は 4 スレッド・
   200 tuple・read ratio 50・rmw 有効・1 秒・max ope 5 で走っており、3 campaign とも同じ設定である。
   したがって「性能を測った 48 スレッド・1,000,000 records・workload 別の条件そのものが直列化可能と
   検査された」とは書かない。書けるのは「同じ genome の trace 有効ビルドが、記録された検査条件で
   120 記録すべて `certified`・anomaly 0 だった」までである。
7. **探索走 (`t2418-explore`) の標本を混ぜていない。** 本格格子と探索走で同じ物理値を持つのは
   9999 マイクロ秒だけであり、その点も本 cohort で新規に測り直した値である (事前登録 §2.4)。
   探索走との比較は本稿の対象外である。
8. **901〜998 マイクロ秒の帯は今も未測である。** 本 cohort の格子にこの帯は無く、D2027 が本走 driver では
   測れないと裁定している。**旧 consumer へ schema v2 を入力した場合の判定も未測定である。** 本 cohort は
   `t2500-backoff-static-tail-formal-report/v1` という別系列の判定であり、v2 への consumer 移行と追加
   tail 測定は D1936 項36 が進めないと裁定したままである。
9. **同じ事前登録に対する他の cohort との関係を言わない。** 本稿は 09-15 の 1 本だけを扱う。
10. **転移を言わない。** 測ったのは silo protocol、Pegasus 計算ノード 48 スレッド、YCSB 3 workload、
    CCBench pin `511c953`、この toolchain・較正・環境契約の下だけである。他の workload・機体・pin・
    protocol へ転移するとは言わない (事前登録 §9)。
11. **論文図は無い。** `docs/paper-story/figures/fig2c_b10_extended_backoff` が描くのは別 cohort (group
    `b10-backoff-grid-20260826T234647Z-783837` の拡張格子、0〜1000 マイクロ秒) であり、生成器
    `tools/plotting/plot_b10_extended_backoff.py` はその group id を定数で持つ。`fig2b_backoff_sweep_3workload`
    も同じ系列の backoff sweep であり、09-15 cohort を入力に取らない。**それらを 09-15 の右 tail を描いた図と
    して引かない。**
    09-15 cohort の図を作るには、置き場所の契約・新図種の完成要件・生成器の実装を先に解く必要がある
    (`output/insights/2026-09-16/t2647-b10-tail-downstream.md` §4)。
12. **統計の意味を広げない。** `[qL, qU]` は 36 の片側限界に Bonferroni を適用した同時区間であり、
    区間ごとの 95% 信頼区間ではない。事前登録 §0 が開示するとおり、**格子の位置と刻み幅、等価幅 5%、
    変動係数の品質 gate 0.02、そして「表現域内で飽和しない」を正当な結末に含めるという選択は、いずれも
    探索走 (`t2418-explore`) の結果を見た後に選んだ**ものである。前向きに固定したのは、まだ観測していない
    本格 cohort に対する測定規則と判定規則だけである (同 §0)。本稿の平均は 5 反復の算術平均であり、
    median ではない。
13. **`not-observed-in-any-workload` と `declining` は protocol の出力であって、研究の成功・失敗の宣告では
    ない** (D12)。本稿はこの結果を B-10 の完了や [T-2647] の閉鎖として扱わない。
14. **反証可能な主張の向きを変えない。** 事前登録 §3 が反証可能な主張として置いたのは「全 workload で
    登録述語を満たす飽和位置が存在する」であり、本 cohort はその反証結果を報告している。「飽和位置が
    ある、または域内非飽和である」という選言を主張として書かない。
15. **物理量の意味の witness を主張しない。** §1.2 の物理値 (マイクロ秒) と `BACKOFF_FIXED` raw 値と genome の
    対応は事前登録 §4.1 の登録表であり、本稿がその対応について独立の pointwise meaning witness を確立した
    ものではない (事前登録 §3)。集団報告 JSON に意味 witness の field は無いが、3 campaign の `campaign.lock`
    (`identity_preimage` 内の spec) はいずれも `meaning_witness_status` =
    `unestablished_for_positive_backoff_fixed_as_in_existing_sweep`、`meaning_witness_gate_required` = `false` を
    記録している (実測)。この境界は既存の sweep 系列と同じであり、本稿はそれを弱めも強めもしない。

---

## 4. 一次資料

### 4.1 権威 bytes (repo 外)

**これらは repo の tracked file ではない。本稿は下の file を現物で読み、SHA-256 を起草時に実計算した。**
root は `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` である。

| 資料 | root 相対 path | SHA-256 (実計算) |
|---|---|---|
| 集団報告 (JSON) | `group-report-20260915/t2500-backoff-static-tail-formal.json` | `5f426ecbc16132048cf0c73eaf6960a395ec821a9f48cc04a83a787dceec8b28` |
| 集団報告 (DAT、rep 単位の生値) | `group-report-20260915/t2500-backoff-static-tail-formal.dat` | `758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44` |
| 完了記録 | `group-report-20260915/t2500-backoff-static-tail-formal-complete.json` | `7192d1da0b4a032251a0e270ec60910a118a5f75844dc9276a6fba00a682d08c` |

`-complete.json` の `artifacts` は上 2 件の SHA-256 を同じ値で束縛している。3 件とも 2026-09-16 の
本番 CLI による再導出で byte 一致した (§3 の限定 4)。

campaign ごとの durable authority (各 job root `b10-backoff-grid-20260915T061814Z-545445-<workload>/`
配下。SHA-256 は集団報告の `campaigns[].completion` と job root の `completion.json` が記録する値):

| workload | campaign lock SHA-256 | WAL (`runs/wal.jsonl`) SHA-256 |
|---|---|---|
| write-heavy | `1953e0fbe2b6448c4e2a7db2a8f18cf586d9813efa7b03fca3b2d279fde02d37` | `ce3247c39b238b026fd83416f713a0ff1249467c492b9644e690530b90763cb5` |
| balanced | `9ed76b03987b26ac09b8033523b7c0eaec1754c1a2f12748571ef149ef9c9a18` | `c472dfc8b4e1b27ed95b0458f235c86b61a076a775a0671ab7c6327e01c780e0` |
| read-heavy | `484f3acf20c39d6570a0501fc65af0b6886fff1d0925d2873484b209f698f4ed` | `5f9ebe362115ac1320d9531a226b6984845fcf84a872c3ea94af0d0a2ac4fde2` |

投入記録は同 root の `b10-backoff-grid-20260915T061814Z-545445.submit.jsonl` (schema
`b10-backoff-grid-submit-event/v1`、job script SHA-256
`c0635ef3c1fa7a589a2c08d079e9ade844e3d100367916f1460026df905b4e5c`) である。

### 4.2 値の出所

| 掲載値 | 出所 |
|---|---|
| 集団 `verdict`、`failures`、`performance_certified`、`schema_version`、`spec_sha256` | 集団報告 JSON の top-level |
| workload の `state`、`saturation_location`、`local_flat_intervals` | 同 `workloads[]` |
| 区間の分類、`qhat`、`qL`、`qU`、`L`、`U`、`U_flat`、`confirmed_nonmonotonicity`、`upward_wiggle` | 同 `workloads[].intervals[]` |
| campaign id、admission、`campaign_lock_digest` | 同 `campaigns[]` と `campaigns[].admission` |
| 事前登録 commit・blob・spec の SHA-256 | 同 `campaigns[].identity` と `-complete.json` の `preregistrations[]` |
| 格子・raw 値・genome・動作点・反復数・測定順・seed・時間枠 | 同 `campaigns[].identity` (`grid`、`workload_coordinates`、`time_budget` ほか) |
| CCBench pin・source digest・toolchain・較正・環境契約・`correctness_mode`・`correctness_flags` | 同 `campaigns[].identity` |
| job id、開始 epoch、所要 (`sweep_elapsed_s` / `job_elapsed_s`)、WAL・lock の SHA-256 | 同 `campaigns[].completion` |
| 正しさ記録の件数・`certified`・`anomalies`・`verdict` | 同 `campaigns[].points[].correctness[].payload` |
| `perf_bin_sha256` の相異、`perf_observation` | 同 `campaigns[].points[]` |
| throughput と abort 率の 5 反復平均、変動係数、生標本 | 集団報告 DAT (rep ごとの `aborts` / `commits` / `throughput_tps`) から本稿の起草時に再計算 |
| ホスト | 各 job root の `qstat-f.stdout` (`Execution Hosts`) |
| `freeze_trees_sha256`、CCBench worktree の gitlink | 各 job root の `completion.json` と `env/ccbench-worktree.json` |

### 4.3 repo 内の一次資料 (tracked)

SHA-256 は本稿の起草時に作業ツリーの現物から実計算した。

| 資料 | path | SHA-256 |
|---|---|---|
| 事前登録 (追補込み、cohort が束縛した版) | `docs/b10-backoff-static-tail-preregistration.md` | `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` |
| 本走の投入・完走の記録 | `output/insights/2026-09-15/t2266-tail-band/README.md` | `b5c26e0204bd1e079056dc927403281566636acc6c2d0bdda24e30913a1be16d` |
| 本番 CLI による再導出と監査限界 | `output/insights/2026-09-16/b10-tail-formal-submit/README.md` | `0325480252502b7fb66d6a5afdafa46ccfb578cb6be05478ccb288aae4319f41` |
| 判定の下流への受け渡しと、図を作らない理由 | `output/insights/2026-09-16/t2647-b10-tail-downstream.md` | `80d2d462426ecca03f5484425e0360a0b497e7eab35700b9cc50364c5a464d72` |

本体系列の入口 `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」項目 3 が、
この cohort の完走と、2026-09-14 版のどの記述が現在地として古くなったかを持つ。

### 4.4 同じ結果についての既存の稿

**results 系列にこの cohort の稿は他に無い。** 本稿が最初である。

版の側では、最新版 `2026-09-14.md` は §0 の前進 9・§2 (g) の項 7・§8 の B-10・§9 の「運用上の証拠」欄で
この本走を**未投入**として扱っている。それらは同版が書かれた 2026-09-14 時点では真であり、執筆時点の誤りでは
ない (README 項目 3)。**本稿は版を改めない。** 版へ取り込むかどうかは、次の版の契約が決める。
