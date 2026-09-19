# B-10 静的 backoff 右 tail の第 2 cohort (独立再現) — 登録した述語では、表現可能域 9999 マイクロ秒までに飽和を観測しなかった (2026-09-19)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である (D1631)。

**本稿は cohort 1 の稿 `results/2026-09-16-b10-static-tail-not-observed.md` を改めるものではない。** 同稿は
主結果 (cohort 1、group `b10-backoff-grid-20260915T061814Z-545445`) の凍結物としてそのまま残り、本稿はその
**独立再現 (cohort 2)** を 1 本の稿として併記する。地位は結果を見る前に事前登録の 2026-09-19 追記が固定した:
第 2 cohort は独立再現であり置換ではない、cohort 1 の verdict を主として保持する、第 2 cohort の verdict は
再現欄に併記する、2 つの cohort を合成しない、結果にかかわらず 1 本を報告する (同追記の項 1〜4、D2050)。

**本稿の言い方は事前登録が固定している。** `docs/b10-backoff-static-tail-preregistration.md` §4.5 は、域内非飽和の
結末について「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」とだけ
書き、**「飽和しない」「飽和点が存在しない」とは書かない**と定める。本稿はこの固定に従う。同追記の項 7 は
「再現された」を「飽和しない」へ読み替えることも禁じる。9999 マイクロ秒は物理的な限界ではなく、現行の符号化が
表現できる上限である (同 §3)。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

results 系列は「1 file = 完走した 1 つの protocol または campaign 群の結果」を単位とする (D1631)。
本稿の単位は、**事前登録 `docs/b10-backoff-static-tail-preregistration.md` (2026-09-19 追記込み、commit
`8737cacb4`) に対して 2026-09-19 (JST) に完走した 1 つの cohort** — group
`b10-backoff-grid-20260919T131526Z-2235286`、`run_kind` `t2500-tail-formal`、3 workload × 8 点 = 24 cell —
である。3 つの campaign は事前登録 §4.9 の同一性検査を通って 1 つの cohort を成す (§1.1)。

本稿の file 名は結果を見る前に中立名 (`cohort2`) で固定した。verdict の slug を file 名に入れていない。

### 0.2 書くもの

事前登録が固定した格子・動作点・反復数・判定式の下で得られた、集団 verdict と workload ごとの状態、
18 区間の分類と推定値、同じ格子上の throughput と abort 率 (過抑制の費用)、全 24 cell の生標本、
実行 identity、正しさの記録、投入時に失敗した attempt の開示、この結果が言わないことの一覧、転記元の SHA-256。
**再現欄** (§2.6) には、主結果である cohort 1 と本 cohort の group id・集団 verdict・束縛情報・一次成果物参照を
区別して併記する。

### 0.3 書かないもの

- **「飽和しない」「飽和点が存在しない」「再現されたので飽和しない」。** 言えるのは事前登録 §4.5 の固定表現までである。
- **9999 マイクロ秒より右についての主張** (事前登録 §3)。
- **機序** (D1678、D1724)。
- **性能の認証。** `performance_certified` は `false` のままである。
- **2 つの cohort の合成。** 標本・区間推定・verdict をまたいで合成しない。cohort をまたぐ有意水準の保証、統合
  verdict、プール推定を作らない (事前登録 2026-09-19 追記の項 3)。
- **cohort 1 の判定・稿・図の変更。** 本稿は cohort 1 について新しいことを何も言わない (同追記「この追記が言わないこと」)。
- **901〜998 マイクロ秒の帯** (D2044 項 14)、**v2 consumer への移行** (D1936 項 36)。

---

## 1. 条件 — 事前登録が固定したものと、成果物が記録したもの

### 1.1 事前登録への束縛

3 つの campaign はいずれも次を記録している (集団報告 `t2500-backoff-static-tail-formal.json` の
`campaigns[].identity` と `-complete.json` の `preregistrations[]`、3 件とも同値)。

| 事項 | 値 |
|---|---|
| 事前登録 commit | `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` |
| 事前登録文書の blob SHA-256 | `8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e` |
| spec (§5 の機械可読 spec) の SHA-256 | `08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef` |

**cohort 1 の束縛 (commit `cad6f46d8`、blob `8084be04…`) とは commit と blob が異なり、spec SHA-256 は同一である。**
commit `8737cacb4` は `cad6f46d8` の文書 (71,231 bytes) を先頭部分としてそのまま含み、末尾に 2026-09-19 追記
(第 2 cohort の地位) を 51 行加えたものである (既存行の変更・削除は 0)。§5 の spec bytes は変えていないので、
格子・動作点・反復数・測定順・判定式・失敗条件は両 cohort で同一の登録値である。追記は第 2 cohort の投入前に
commit した (commit 2026-09-19 22:01:23 JST、投入 同日 22:15:25 JST)。ただし、cohort 1 の稿 §1.1 が開示した
「2026-09-10 追補の変更理由・時点が §0 に記載されていない」という文書契約上の留保は残る。今回の追記は
過去の手続を遡及的に正当化しない (追記本文にそう明記した)。この留保を §7 の失敗条件 12 や `invalid` へ読み替えない。本稿の起草時、作業ツリーの
`docs/b10-backoff-static-tail-preregistration.md` の raw bytes の SHA-256 は同じ `8511d479…` であり、
commit `8737cacb4` は HEAD の祖先である (実測)。

事前登録 §4.9 が 3 job の間で一致を要求する項目 — CCBench の source digest と toolchain、環境契約と較正の
identity、事前登録の commit・blob・spec、動作点の literal — は、3 campaign の `identity` で**すべて同値**である
(実測: 各 field の異なり数が 1)。workload 座標だけが設計どおり 3 job で異なる。

**izanagi 側の source commit は job root の `reservation.json` (`source_binding.repository_commit`) に
`8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` として 3 job とも記録されている** (実測)。集団報告と
`-complete.json` にはこの field は無い。

### 1.2 格子・動作点・反復数・測定順

いずれも事前登録 §4.1 / §4.2 の literal と一致する値が `identity` に記録されている (cohort 1 と同一の登録値)。

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
| write-heavy | `t2500-backoff-static-tail-formal-silo-write-heavy-sweep-45feee64` | `0:10752.nqsv` | 2026-09-19 22:15:37 | `bnode084` | 822.14 | 834.67 |
| balanced | `t2500-backoff-static-tail-formal-silo-balanced-sweep-d7cbfe58` | `0:10753.nqsv` | 2026-09-19 22:15:37 | `bnode107` | 820.43 | 831.96 |
| read-heavy | `t2500-backoff-static-tail-formal-silo-read-heavy-sweep-ed0b204e` | `0:10754.nqsv` | 2026-09-19 22:15:37 | `bnode108` | 822.64 | 834.67 |

開始時刻は `completion.scheduler.job_start_epoch` を JST へ直したもの、ホストは各 job root の
`qstat-f.stdout` の `Execution Hosts(JSVNO)` 欄である。3 job は別ノードで同時刻に走った。所要は事前登録 §4.2 の
見積り (約 20 分/job) の内側で、cohort 1 (823.31 / 820.90 / 825.31 秒) とほぼ同じである。`job_elapsed_s` は
driver が実行 receipt を書く直前までの値であり、job の最終終了時刻までは含まない (scheduler の記録では
3 job とも 22:29:31 JST 前後に終了、Elapse 839 秒)。

3 campaign に共通の identity:

| 事項 | 値 |
|---|---|
| 測定環境 | `pegasus` (計算ノード、48 スレッド) |
| CCBench pin (`repo_stock_pin`) | `511c953` (各 job の `env/ccbench-worktree.json` は gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec` を detached で checkout し `tracked_clean: true`) |
| CCBench source digest | `db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba` |
| toolchain | `x86_64-linux-gnu-gcc-11` / `g++-11` (Ubuntu 11.4.0)、cmake 3.22.1 |
| 較正 identity | `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` (`753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`) |
| 環境契約 identity | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| `freeze_trees_sha256` (各 job root の `completion.json`) | `c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3` (3 job で一致) |
| perf | 不使用。`perf_observation.claim_scope` は `throughput: eligible` / `perf_required: unsupported`、preflight は `available: false` |
| 性能測定の build | trace 無効ビルド。`perf_bin_sha256` は 1 workload あたり 8 個が相異なる (事前登録 §4.6 の要求) |

CCBench pin・source digest・toolchain・較正・環境契約・`freeze_trees_sha256` は cohort 1 の稿 §1.3 が記録する値と
同じである (同稿からの転記ではなく、本 cohort の成果物の実測値を並べたうえで一致を確かめた)。

**投入元の差。** 本 cohort の job body は、cohort 1 以後の [T-548] (2026-09-16) により gflags / glog を
hydrate 済み staging (`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/`) から読む。この staging は
git 管理外であり、投入前に親が用意する。job body の committed bytes (`job_script_sha256`
`8422011d985ec1eef24fe94d0f5f3f50b12715a1dc008e10d3fec763d197783b`) は cohort 1 のもの (`c0635ef3…`) と異なる
(差分は T-548 の依存 source path の付け替え 15 行だけ)。

### 1.4 正しさの記録

正しさは trace 有効ビルドの別走行から来る (絶対規律 1)。集団報告の `points[].correctness` は
1 workload あたり 40 記録 (8 cell × 5 rep)、**3 workload 合計 120 記録すべてが `payload.certified` = `true`、
`payload.anomalies` = 0、`payload.verdict` = `serializable`** である (実測)。各記録は `source_measurement` =
`trace_enabled`、`source_run_kind` = `t2500-tail-formal` を持ち、`wal_record_digest`・`attempt_id`・
`campaign_lock_digest` で WAL の record と campaign に束縛されている。性能側の rep 記録は `source_measurement` =
`trace_disabled` で、同じ `source_run_kind` を持つ。正しさ検査の mode
(`correctness_mode`) は 3 campaign とも `legacy` で、探索走 `t2418-explore` の記録と同じ値である
(事前登録 §4.6 の要求。比較先は 2026-09-19 追記の項 6 が固定した探索走 campaign
`…/b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8`
を投入時・報告時とも渡した)。

**正しさ検査の条件は、性能測定の条件と同じではない。** 3 campaign の `identity.correctness_flags` はいずれも
`extime 1`、`thread_num 4`、`ycsb_tuple_num 200`、`ycsb_rratio 50`、`ycsb_rmw true`、`ycsb_max_ope 5`、
`ycsb_zipf_skew 0.9` で、性能側の 48 スレッド・1,000,000 records・3 秒・workload 別の read ratio とは別の
設定である。これは §3 の限定 6 に書く。

**これは性能の認証ではない。** `performance_certified` は `false` である。

### 1.5 投入時に失敗した attempt (開示)

同日 22:11:18 JST に投入した最初の 3 job (group `b10-backoff-grid-20260919T131120Z-2159341`、job
`0:10743.nqsv` / `0:10744.nqsv` / `0:10745.nqsv`) は、計算ノード起動から約 5 秒後に
`stage=dependency_policy_contract`、理由 `gflags source is not a real directory`、rc=2 で 3 job とも停止した
(各 job root の `.failure.json`)。原因は投入元 worktree に §1.3 の hydrate 済み staging が無かったことである。
この attempt では campaign も WAL も測定も 1 つも作られていない (`.failure.json` の `campaign_wals: []`、
`reports: []`)。この失敗 attempt には集団報告による機械生成 verdict は無い。campaign 作成前に停止したためであり、
生成済みの `invalid` を報告しているのではない。staging を用意して再投入したのが本 cohort (attempt 2) である。事前登録 2026-09-19 追記の項 4
(未完走も報告対象とし、失敗理由を開示する) に従い、ここに記す。**失敗 attempt の出力 root は削除していない。**

---

## 2. 結果

### 2.1 集団 verdict と workload ごとの状態

集団報告 (`t2500-backoff-static-tail-formal.json`) が記録する出力:

| 事項 | 値 |
|---|---|
| `verdict` | **`not-observed-in-any-workload`** |
| `failures` | `[]` (loader が記録した失敗は 0 件。集約 verdict が `invalid` でないことの根拠。本番 CLI の終了コードは 0) |
| `performance_certified` | `false` |
| `schema_version` | `t2500-backoff-static-tail-formal-report/v1` |
| campaign の admission | 3 件とも `admitted` |

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
| 1250 → 1768 | `declining` | −0.5475 | −0.5618 | −0.5331 | 0.3090 | 0.3226 | 0.0099 |
| 1768 → 2500 | `declining` | −0.5445 | −0.5593 | −0.5297 | 0.3073 | 0.3214 | 0.0102 |
| 2500 → 3535 | `declining` | −0.5690 | −0.6027 | −0.5354 | 0.3100 | 0.3415 | 0.0230 |
| 3535 → 5000 | `declining` | −0.5735 | −0.6068 | −0.5402 | 0.3123 | 0.3434 | 0.0228 |
| 5000 → 7070 | `declining` | −0.5965 | −0.6230 | −0.5699 | 0.3264 | 0.3507 | 0.0182 |
| 7070 → 9999 | `declining` | −0.6194 | −0.6591 | −0.5797 | 0.3309 | 0.3667 | 0.0271 |

**balanced**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.5380 | −0.5546 | −0.5214 | 0.3033 | 0.3192 | 0.0115 |
| 1768 → 2500 | `declining` | −0.5649 | −0.5828 | −0.5469 | 0.3155 | 0.3323 | 0.0124 |
| 2500 → 3535 | `declining` | −0.5885 | −0.6184 | −0.5586 | 0.3210 | 0.3486 | 0.0205 |
| 3535 → 5000 | `declining` | −0.6143 | −0.6450 | −0.5836 | 0.3327 | 0.3605 | 0.0211 |
| 5000 → 7070 | `declining` | −0.6766 | −0.7133 | −0.6399 | 0.3583 | 0.3901 | 0.0251 |
| 7070 → 9999 | `declining` | −0.7126 | −0.7512 | −0.6740 | 0.3732 | 0.4059 | 0.0264 |

**read-heavy**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.4900 | −0.5051 | −0.4749 | 0.2805 | 0.2954 | 0.0104 |
| 1768 → 2500 | `declining` | −0.4956 | −0.5127 | −0.4784 | 0.2822 | 0.2991 | 0.0118 |
| 2500 → 3535 | `declining` | −0.5087 | −0.5394 | −0.4779 | 0.2820 | 0.3120 | 0.0211 |
| 3535 → 5000 | `declining` | −0.5074 | −0.5443 | −0.4704 | 0.2782 | 0.3143 | 0.0253 |
| 5000 → 7070 | `declining` | −0.5298 | −0.5725 | −0.4872 | 0.2866 | 0.3275 | 0.0291 |
| 7070 → 9999 | `declining` | −0.5340 | −0.5750 | −0.4930 | 0.2895 | 0.3287 | 0.0280 |

値は集団報告の `workloads[].intervals[]` を小数第 4 位に丸めて転記した。

**読めること (記述)。** `L` は 18 区間すべてで 0.27 以上 (0.2782〜0.3732) であり、述語の閾値 0.05 を大きく超える。
倍増あたりの低下率の同時下限が 28〜37% ということである。`U_flat` は 18 区間すべてで 0.05 以下 (0.0099〜0.0291)
であり、事前登録 §4.4 が「真に平坦な区間が `U_i <= 0.05` に届くかどうかの目安」と定める診断値の意味で、分解能の
不足を非飽和の証拠に化かしている状態ではない。**この診断値は分類には使わない** (同 §4.4)。

**読めないこと。** 最右区間の `qhat` は最左区間より負側にある (write-heavy −0.55 → −0.62、balanced
−0.54 → −0.71、read-heavy −0.49 → −0.53)。ただし区間列全体で単調に負側へ進むわけではない (write-heavy の
1768 → 2500 は −0.5445 で左隣の −0.5475 より小さい負、read-heavy の 3535 → 5000 も同様)。この端の区間同士の
比較から機序を説明しない (D1724 の限界: 静的 tail について書けるのは記述的な会計まで)。cohort 1 の同じ表との数値の近さも、本稿は
「一致」「再現精度」として評価しない (§2.6、限定 9)。

### 2.3 過抑制の費用 — 同じ格子上の throughput と abort 率

事前登録 §3 は「同じ格子上の throughput を、過抑制の費用として必ず併記する」と要求する。次は
`t2500-backoff-static-tail-formal.dat` (1 行のヘッダと 120 行のデータ。列は workload・backoff_us・rep・aborts・
commits・abort_rate・throughput_tps の 7 つ) から本稿の起草時に再計算した **5 反復の算術平均**である。
中央値ではない。

throughput (毎秒トランザクション数):

| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 992,686.2 | 719,938.2 | 1,704,680.0 |
| 1250 | 905,498.2 | 657,520.8 | 1,544,381.8 |
| 1768 | 787,963.4 | 570,451.4 | 1,324,328.0 |
| 2500 | 683,409.0 | 498,175.2 | 1,134,612.0 |
| 3535 | 596,273.8 | 437,637.6 | 973,173.6 |
| 5000 | 519,930.4 | 386,980.0 | 832,181.8 |
| 7070 | 456,397.6 | 349,144.4 | 715,848.0 |
| 9999 | 403,188.2 | 318,499.4 | 615,347.8 |

abort 率 (`aborts / (aborts + commits)` を rep ごとに整数カウンタから全精度で再計算し、5 反復を平均。
事前登録 §4.3。CCBench が印字する小数第 4 位の丸め値は使っていない):

| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.042370 | 0.058623 | 0.023743 |
| 1250 | 0.037671 | 0.052048 | 0.021342 |
| 1768 | 0.031158 | 0.043191 | 0.018008 |
| 2500 | 0.025802 | 0.035514 | 0.015167 |
| 3535 | 0.021186 | 0.028965 | 0.012716 |
| 5000 | 0.017365 | 0.023408 | 0.010665 |
| 7070 | 0.014124 | 0.018517 | 0.008877 |
| 9999 | 0.011395 | 0.014464 | 0.007377 |

変動係数 (標本標準偏差 ÷ 平均、ddof = 1。throughput / abort 率の順):

| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.24% / 0.23% | 0.30% / 0.27% | 0.21% / 0.22% |
| 1250 | 0.18% / 0.19% | 0.14% / 0.15% | 0.16% / 0.18% |
| 1768 | 0.18% / 0.18% | 0.24% / 0.24% | 0.22% / 0.21% |
| 2500 | 0.20% / 0.20% | 0.23% / 0.22% | 0.23% / 0.23% |
| 3535 | 0.45% / 0.46% | 0.41% / 0.42% | 0.41% / 0.43% |
| 5000 | 0.37% / 0.38% | 0.35% / 0.36% | 0.48% / 0.51% |
| 7070 | 0.23% / 0.24% | 0.51% / 0.52% | 0.54% / 0.58% |
| 9999 | 0.56% / 0.55% | 0.47% / 0.46% | 0.31% / 0.31% |

全 24 cell で throughput の変動係数は 0.14〜0.56%、abort 率の変動係数は 0.15〜0.58% であり、事前登録 §4.7 /
§7 の品質 gate (2% 以上で失敗) の内側である (集団報告の `statistics[].gate_passed` も 24 cell とも `true`)。
**abort 率の変動係数と throughput の変動係数は別物である** (同 §4.7)。

**この表は記述的な集計である。** 性能の認証でも機序の説明でもない。tail の左端 1250 から右端 9999 マイクロ秒
までで、5 反復平均の throughput は write-heavy が 0.445 倍、balanced が 0.484 倍、read-heavy が 0.398 倍に
なっている (3 workload とも半分以下)。同じ帯で abort 率は下がり続けている。**abort 率が下がり続けることと、
その帯で throughput が大きく失われることは、同時に成り立っている。** どちらが望ましいかの判定は本稿の外で
ある。

### 2.4 境界参照 1000 マイクロ秒は同一 cohort の点である

事前登録 §4.1 が境界参照 1000 を入れた理由は、正式格子の上端と tail を**同一 job 内で**接続するためである。
本稿の 1000 の値は本 cohort の測定であり、cohort 1 の 1000 の値とも、2026-09-10 に完走した `t2266-tail` v2 系列の
1000 マイクロ秒とも別の走行である。**流用も混合もしていない。** 本稿はそれらの値を転記しない。

### 2.5 全 24 cell の生標本

`.dat` の 120 行を rep 順 (0〜4) に転記した。throughput は毎秒トランザクション数、右列は
`aborts / commits` の整数カウンタである。

| workload | backoff (µs) | throughput (5 rep) | aborts / commits (5 rep) |
|---|---:|---|---|
| write-heavy | 1000 | 992,053, 995,149, 994,970, 989,654, 991,605 | 131,802 / 2,976,159, 131,728 / 2,985,448, 131,759 / 2,984,911, 131,733 / 2,968,964, 131,793 / 2,974,817 |
| write-heavy | 1250 | 904,186, 908,206, 905,133, 904,414, 905,552 | 106,339 / 2,712,559, 106,307 / 2,724,619, 106,359 / 2,715,399, 106,359 / 2,713,242, 106,336 / 2,716,657 |
| write-heavy | 1768 | 785,904, 789,006, 787,173, 789,207, 788,527 | 76,041 / 2,357,713, 76,025 / 2,367,019, 76,021 / 2,361,519, 76,022 / 2,367,621, 76,010 / 2,365,583 |
| write-heavy | 2500 | 685,684, 682,546, 683,314, 682,083, 683,418 | 54,304 / 2,057,053, 54,298 / 2,047,640, 54,295 / 2,049,942, 54,310 / 2,046,249, 54,295 / 2,050,254 |
| write-heavy | 3535 | 597,902, 599,285, 592,794, 594,322, 597,066 | 38,716 / 1,793,708, 38,705 / 1,797,855, 38,733 / 1,778,383, 38,721 / 1,782,968, 38,710 / 1,791,199 |
| write-heavy | 5000 | 517,177, 520,704, 522,468, 519,659, 519,644 | 27,571 / 1,551,531, 27,566 / 1,562,112, 27,558 / 1,567,405, 27,559 / 1,558,977, 27,568 / 1,558,932 |
| write-heavy | 7070 | 456,313, 454,878, 456,395, 457,848, 456,554 | 19,614 / 1,368,939, 19,618 / 1,364,635, 19,617 / 1,369,187, 19,611 / 1,373,546, 19,614 / 1,369,662 |
| write-heavy | 9999 | 401,342, 406,474, 401,396, 404,525, 402,204 | 13,939 / 1,204,028, 13,941 / 1,219,423, 13,943 / 1,204,189, 13,942 / 1,213,575, 13,941 / 1,206,612 |
| balanced | 1000 | 718,772, 721,322, 720,062, 722,488, 717,047 | 134,523 / 2,156,318, 134,504 / 2,163,968, 134,463 / 2,160,186, 134,521 / 2,167,465, 134,489 / 2,151,143 |
| balanced | 1250 | 655,992, 657,731, 658,013, 657,396, 658,472 | 108,324 / 1,967,977, 108,312 / 1,973,193, 108,271 / 1,974,040, 108,303 / 1,972,188, 108,312 / 1,975,417 |
| balanced | 1768 | 572,139, 571,401, 568,644, 570,331, 569,742 | 77,242 / 1,716,419, 77,240 / 1,714,205, 77,250 / 1,705,933, 77,268 / 1,710,994, 77,259 / 1,709,227 |
| balanced | 2500 | 497,369, 496,741, 499,106, 499,506, 498,154 | 55,026 / 1,492,108, 55,039 / 1,490,223, 55,036 / 1,497,320, 55,035 / 1,498,519, 55,021 / 1,494,462 |
| balanced | 3535 | 438,497, 436,097, 437,347, 440,297, 435,950 | 39,158 / 1,315,492, 39,173 / 1,308,291, 39,163 / 1,312,043, 39,149 / 1,320,893, 39,167 / 1,307,851 |
| balanced | 5000 | 387,990, 387,774, 388,166, 385,577, 385,393 | 27,830 / 1,163,971, 27,819 / 1,163,324, 27,824 / 1,164,498, 27,828 / 1,156,732, 27,832 / 1,156,180 |
| balanced | 7070 | 349,978, 349,901, 350,707, 346,151, 348,985 | 19,757 / 1,049,935, 19,760 / 1,049,703, 19,756 / 1,052,122, 19,766 / 1,038,453, 19,766 / 1,046,957 |
| balanced | 9999 | 316,201, 317,947, 319,573, 319,947, 318,829 | 14,022 / 948,603, 14,025 / 953,841, 14,023 / 958,719, 14,022 / 959,842, 14,025 / 956,489 |
| read-heavy | 1000 | 1,705,581, 1,709,860, 1,705,535, 1,701,971, 1,700,453 | 124,341 / 5,116,744, 124,378 / 5,129,582, 124,375 / 5,116,605, 124,363 / 5,105,915, 124,424 / 5,101,361 |
| read-heavy | 1250 | 1,545,127, 1,545,144, 1,544,732, 1,540,162, 1,546,744 | 100,993 / 4,635,383, 101,048 / 4,635,432, 101,074 / 4,634,198, 101,060 / 4,620,486, 101,016 / 4,640,232 |
| read-heavy | 1768 | 1,320,691, 1,327,113, 1,324,955, 1,326,895, 1,321,986 | 72,841 / 3,962,073, 72,875 / 3,981,341, 72,835 / 3,974,866, 72,858 / 3,980,687, 72,872 / 3,965,959 |
| read-heavy | 2500 | 1,137,265, 1,134,488, 1,136,860, 1,130,889, 1,133,558 | 52,418 / 3,411,796, 52,398 / 3,403,466, 52,430 / 3,410,580, 52,427 / 3,392,667, 52,429 / 3,400,675 |
| read-heavy | 3535 | 967,985, 978,019, 971,473, 976,385, 972,006 | 37,624 / 2,903,956, 37,594 / 2,934,059, 37,601 / 2,914,419, 37,599 / 2,929,157, 37,599 / 2,916,020 |
| read-heavy | 5000 | 830,154, 827,885, 838,195, 834,033, 830,642 | 26,919 / 2,490,464, 26,917 / 2,483,657, 26,900 / 2,514,585, 26,906 / 2,502,101, 26,920 / 2,491,928 |
| read-heavy | 7070 | 722,286, 716,371, 712,179, 714,427, 713,977 | 19,219 / 2,166,858, 19,231 / 2,149,115, 19,240 / 2,136,538, 19,240 / 2,143,281, 19,237 / 2,141,931 |
| read-heavy | 9999 | 617,053, 612,177, 616,298, 615,160, 616,051 | 13,717 / 1,851,159, 13,720 / 1,836,533, 13,720 / 1,848,896, 13,721 / 1,845,481, 13,717 / 1,848,154 |

`.dat` の `abort_rate` 列は各行の `aborts / (aborts + commits)` と一致する (120 行とも実測)。集団報告の
`points[].tps` と `points[].reps[].throughput_tps` も同じ値である (事前登録 §7 の失敗条件 19 の対象)。

### 2.6 再現欄 — 主結果 (cohort 1) と独立再現 (本 cohort) の併記

事前登録 2026-09-19 追記の項 2 に従い、主結果と独立再現を区別して併記する。**両者を合成しない。統合 verdict を
作らない。** 各 cohort の verdict は、それぞれの集団報告が §4.5 の結末表を独立に適用した出力である。

| 欄 | 主結果: cohort 1 | 独立再現: cohort 2 (本稿) |
|---|---|---|
| group id | `b10-backoff-grid-20260915T061814Z-545445` | `b10-backoff-grid-20260919T131526Z-2235286` |
| 完走 (JST) | 2026-09-15 | 2026-09-19 |
| job | `0:998865.nqsv` / `0:998866.nqsv` / `0:998867.nqsv` | `0:10752.nqsv` / `0:10753.nqsv` / `0:10754.nqsv` |
| 事前登録の束縛 | commit `cad6f46d8`、blob `8084be04…` | commit `8737cacb4`、blob `8511d479…` |
| spec SHA-256 | `08f5849b…` | `08f5849b…` (同一) |
| 集団 verdict | `not-observed-in-any-workload` | `not-observed-in-any-workload` |
| workload 状態 | 3 つとも `not-observed` | 3 つとも `not-observed` |
| 区間分類 | 18 区間すべて `declining` | 18 区間すべて `declining` |
| `failures` | `[]` | `[]` |
| `performance_certified` | `false` | `false` |
| 正しさ | 120 記録 certified・anomaly 0 (trace 有効の別走行) | 120 記録 certified・anomaly 0 (trace 有効の別走行) |
| 集団報告 (repo 外) | `group-report-20260915/` (JSON `5f426ecb…`、DAT `758b3121…`、complete `7192d1da…`) | `group-report-20260919-cohort2/` (JSON `932f6ccc…`、DAT `15b99944…`、complete `93421187…`) |
| 稿 | `results/2026-09-16-b10-static-tail-not-observed.md` | 本稿 |
| 図 | `figures/fig8_b10_static_tail_not_observed` (cohort 1 の記述図) | 無い。fig8 への再現欄の追加は生成器の改変を要し、本稿の対象外 (限定 11) |

**この表が言うこと。** 同じ格子・同じ判定式の下で独立に走らせた第 2 cohort が、主結果と同じ集団 verdict
(`not-observed-in-any-workload`) を出した。言い方は §4.5 の固定表現のままである: 「この事前登録の述語では、
表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」が、独立な 2 つの cohort のそれぞれについて成り立つ。

**この表が言わないこと。** 「飽和しない」「飽和点が存在しない」「再現されたので飽和しない」とは言わない
(追記の項 7)。2 つの cohort の数値 (§2.2 の `qhat`、§2.3 の平均) の近さを再現精度・一致度として評価しない。
cohort をまたぐ有意水準・統合 verdict・プール推定を作らない (追記の項 3)。

---

## 3. 限定 (この結果が言わないこと)

1. **「飽和しない」「飽和点が存在しない」とは言わない。** 事前登録 §4.5 が言い方を固定しており、言えるのは
   「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」までである。
   9999 マイクロ秒より右は、符号化を変えない限り測れない (同 §3、§9)。第 2 cohort が同じ verdict を出したことは、
   この言い方を強める根拠にしない (2026-09-19 追記の項 7)。
2. **機序を言わない。** なぜ abort 率がこの形で下がるのか、なぜ区間ごとの `qhat` がこの値になるのかは、
   本稿の対象外である (D1678、D1724)。§2.2 と §2.3 は記述的な集計である。
3. **性能を認証していない。** 性能値は trace 無効ビルドの別走行のもので、`performance_certified` は `false`
   である。**この性能値を根拠に variant を採用してはならない** (絶対規律 2)。正しさが認証されたのは
   trace 有効ビルドの別走行 (§1.4) についてである。
4. **当時の実行全体を独立に監査したとは言わない。** 集団報告は完走直後の 2026-09-19 22:30 JST に本番 CLI
   (`orchestrator/campaign/b10_backoff_static_tail_formal.py report`、手順書 §4 の argv) で 1 回生成したものであり、
   終了コード 0 で `failures` は空だった。これが示すのは「現行の loader がそのデータを受理し、この judgement を
   出した」までであり、ビルド・resume 操作・失敗 attempt の履歴の独立監査は未実施である。
5. **izanagi 側の source commit は集団報告と `-complete.json` に無い** (§1.1)。ただし job root の
   `reservation.json` (`source_binding.repository_commit`) には `8737cacb4` が 3 job とも記録されている。
   残る束縛は事前登録 commit と `freeze_trees_sha256` の 3 job 一致である。正しさ検査の mode を読むために
   driver へ渡した探索走 campaign は、2026-09-19 追記の項 6 が固定した 1 本を投入時・報告時とも渡した。
   job の成果物にはその argv は保存されない (cohort 1 と同じ)。
6. **正しさ検査の条件は性能測定の条件と同じではない** (§1.4)。`legacy` mode の検査は 4 スレッド・
   200 tuple・read ratio 50・rmw 有効・1 秒・max ope 5 で走っており、3 campaign とも同じ設定である。
   したがって「性能を測った 48 スレッド・1,000,000 records・workload 別の条件そのものが直列化可能と
   検査された」とは書かない。書けるのは「同じ genome の trace 有効ビルドが、記録された検査条件で
   120 記録すべて `certified`・anomaly 0 だった」までである。
7. **探索走 (`t2418-explore`) の標本を混ぜていない。** 本格格子と探索走で同じ物理値を持つのは
   9999 マイクロ秒だけであり、その点も本 cohort で新規に測り直した値である (事前登録 §2.4)。
   探索走との比較は本稿の対象外である。
8. **901〜998 マイクロ秒の帯は今も未測である。** 本 cohort の格子にこの帯は無く、D2044 項 14 が現状維持と
   裁定している。**旧 consumer へ schema v2 を入力した場合の判定も未測定である。** v2 への consumer 移行と追加
   tail 測定は D1936 項 36 が進めないと裁定したままである。
9. **2 つの cohort を合成しない。** 本稿は cohort 1 の稿を改めず、cohort 1 について新しいことを言わない。
   §2.6 の併記は主結果と独立再現の区別を保った並置であり、統合 verdict・プール推定・cohort をまたぐ有意水準の
   保証ではない。§2.2 / §2.3 の数値が cohort 1 と近いことを、再現精度や一致度として評価しない。**第 3 cohort の
   実施・地位は本稿も事前登録追記も定めない。**
10. **転移を言わない。** 測ったのは silo protocol、Pegasus 計算ノード 48 スレッド、YCSB 3 workload、
    CCBench pin `511c953`、この toolchain・較正・環境契約の下だけである。他の workload・機体・pin・
    protocol へ転移するとは言わない (事前登録 §9)。
11. **論文図は無い。** `figures/fig8_b10_static_tail_not_observed` は cohort 1 の記述図であり、生成器
    `tools/plotting/plot_b10_static_tail_formal.py` は cohort 1 の group id と 3 成果物の SHA-256 を定数で持つ。
    本 cohort を fig8 の再現欄として描くには生成器・provenance・検査の改変 (実装面) が要り、本稿の対象外である。
    **fig8 を本 cohort の図として引かない。** 本 cohort の図の材料は §2.6 と §4.1 に揃えてある。
12. **統計の意味を広げない。** `[qL, qU]` は 36 の片側限界に Bonferroni を適用した同時区間であり、
    区間ごとの 95% 信頼区間ではない。事前登録 §0 が開示するとおり、**格子の位置と刻み幅、等価幅 5%、
    変動係数の品質 gate 0.02、そして「表現域内で飽和しない」を正当な結末に含めるという選択は、いずれも
    探索走 (`t2418-explore`) の結果を見た後に選んだ**ものである。第 2 cohort について前向きに固定したのは、
    その地位と報告方法 (2026-09-19 追記) と、cohort 1 と共通の測定規則・判定規則だけである。本稿の平均は
    5 反復の算術平均であり、median ではない。
13. **`not-observed-in-any-workload` と `declining` は protocol の出力であって、研究の成功・失敗の宣告では
    ない** (D12)。本稿はこの結果を B-10 の完了や [T-2647] の閉鎖として扱わない。
14. **反証可能な主張の向きを変えない。** 事前登録 §3 が反証可能な主張として置いたのは「全 workload で
    登録述語を満たす飽和位置が存在する」であり、本 cohort もその反証結果を報告している。「飽和位置が
    ある、または域内非飽和である」という選言を主張として書かない。
15. **物理量の意味の witness を主張しない。** §1.2 の物理値 (マイクロ秒) と `BACKOFF_FIXED` raw 値と genome の
    対応は事前登録 §4.1 の登録表であり、本稿がその対応について独立の pointwise meaning witness を確立した
    ものではない (事前登録 §3)。集団報告 JSON に意味 witness の field は無いが、3 campaign の `campaign.lock`
    (`identity_preimage` 内の spec) はいずれも `meaning_witness_status` =
    `unestablished_for_positive_backoff_fixed_as_in_existing_sweep`、`meaning_witness_gate_required` = `false` を
    記録している (実測)。この境界は既存の sweep 系列と同じであり、本稿はそれを弱めも強めもしない。
16. **失敗 attempt (§1.5) は本 cohort の標本に入っていない。** 同 attempt は campaign を作る前に停止しており、
    継ぎ合わせの対象になる cell が存在しない (事前登録 §7 の失敗条件 10 に当たらない)。

---

## 4. 一次資料

### 4.1 権威 bytes (repo 外)

**これらは repo の tracked file ではない。本稿は下の file を現物で読み、SHA-256 を起草時に実計算した。**
root は `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` である。

| 資料 | root 相対 path | SHA-256 (実計算) |
|---|---|---|
| 集団報告 (JSON) | `group-report-20260919-cohort2/t2500-backoff-static-tail-formal.json` | `932f6cccbf1a4be2ccbd4c11af31fe2a402b26fc352eb05e22b87b14cef504fd` |
| 集団報告 (DAT、rep 単位の生値) | `group-report-20260919-cohort2/t2500-backoff-static-tail-formal.dat` | `15b99944b8429c0c2bb0d36d4498c7ab2a57d3f90c97d2430f34838905881fd6` |
| 完了記録 | `group-report-20260919-cohort2/t2500-backoff-static-tail-formal-complete.json` | `934211874c779c7bfbffd9a596ef9b7094b7bfa2f7a660203065759abf59420c` |

`-complete.json` の `artifacts` は上 2 件の SHA-256 を同じ値で束縛している。

campaign ごとの durable authority (各 job root `b10-backoff-grid-20260919T131526Z-2235286-<workload>/`
配下。SHA-256 は集団報告の `campaigns[].completion` と job root の `completion.json` が記録する値):

| workload | campaign lock SHA-256 | WAL (`runs/wal.jsonl`) SHA-256 |
|---|---|---|
| write-heavy | `5503fb0181efe38022beeb08c85775076f3cd1c3d90b5135daf21d40e156cfa7` | `d59b2c7f1ef7855b06dba9fc3d17ec236f6fe9923ce15871bb74fcc330f72927` |
| balanced | `7c975f4715ccf20b73311e8aa8e199f87ddcd9271204735b02c466d108d83d71` | `3986d1ad9116fe09aa8fe7ed1fd9443506e68122403c467d7ed4f4f680fad23c` |
| read-heavy | `4af8d0a2d6f1d6c395556f80fc685ee85cfb792b91126a33023aa1ab3a6fedc8` | `942445f90c2c7970f7b72f83eb210697b6f14542381a09433ec2ffe66073e043` |

投入記録は同 root の `b10-backoff-grid-20260919T131526Z-2235286.submit.jsonl` (schema
`b10-backoff-grid-submit-event/v1`、job script SHA-256
`8422011d985ec1eef24fe94d0f5f3f50b12715a1dc008e10d3fec763d197783b`、file の SHA-256
`a3117267c80fa15e3c2ad431bee88506fd792d9c6dd483ecb508ecb7e91eb439`) である。失敗 attempt (§1.5) の記録は
同 root の `b10-backoff-grid-20260919T131120Z-2159341.submit.jsonl` と 3 つの
`b10-backoff-grid-20260919T131120Z-2159341-<workload>.failure.json` である。

### 4.2 値の出所

| 掲載値 | 出所 |
|---|---|
| 集団 `verdict`、`failures`、`performance_certified`、`schema_version`、`spec_sha256` | 集団報告 JSON の top-level |
| workload の `state`、`saturation_location`、`local_flat_intervals`、`statistics[].gate_passed` | 同 `workloads[]` |
| 区間の分類、`qhat`、`qL`、`qU`、`L`、`U`、`U_flat`、`confirmed_nonmonotonicity`、`upward_wiggle` | 同 `workloads[].intervals[]` |
| campaign id、admission、`campaign_lock_digest` | 同 `campaigns[]` と `campaigns[].admission` |
| 事前登録 commit・blob・spec の SHA-256 | 同 `campaigns[].identity` と `-complete.json` の `preregistrations[]` |
| 格子・raw 値・genome・動作点・反復数・測定順・seed・時間枠 | 同 `campaigns[].identity` (`grid`、`workload_coordinates`、`time_budget` ほか) |
| CCBench pin・source digest・toolchain・較正・環境契約・`correctness_mode`・`correctness_flags` | 同 `campaigns[].identity` |
| job id、開始 epoch、所要 (`sweep_elapsed_s` / `job_elapsed_s`)、WAL・lock の SHA-256 | 同 `campaigns[].completion` |
| 正しさ記録の件数・`certified`・`anomalies`・`verdict` | 同 `campaigns[].points[].correctness[].payload` |
| `perf_bin_sha256` の相異、`perf_observation` | 同 `campaigns[].points[]` |
| throughput と abort 率の 5 反復平均、変動係数、生標本 | 集団報告 DAT (rep ごとの `aborts` / `commits` / `throughput_tps`) から本稿の起草時に再計算 |
| ホスト、scheduler の終了時刻 | 各 job root の `qstat-f.stdout` (`Execution Hosts(JSVNO)`)、各 job の `.stderr` (NQSV の request 要約) |
| `freeze_trees_sha256`、CCBench worktree の gitlink、izanagi commit | 各 job root の `completion.json`、`env/ccbench-worktree.json`、`reservation.json` |
| 失敗 attempt の段・理由・rc | 各 job root の `.failure.json` (`stage`、`returncode`) と `.stderr` |
| cohort 1 の欄 (§2.6) と §1.3 の cohort 1 の所要 | `group-report-20260915/` の集団報告 JSON・DAT・完了記録 (SHA-256 は本稿の起草時に実計算: JSON `5f426ecb…`、DAT `758b3121…`、完了記録 `7192d1da…`) と、対応する job root (`b10-backoff-grid-20260915T061814Z-545445-<workload>/`) の `completion.json`。掲載した group id・job id・束縛 (commit・blob・spec)・集団 verdict・workload 状態・18 区間の分類・`failures`・`performance_certified`・正しさ 120 記録・所要を、これらの一次資料へ直接照合した (本稿と同じ抽出手順を cohort 1 の成果物に当て、値の一致を確かめた)。旧稿 `results/2026-09-16-b10-static-tail-not-observed.md` は主結果の凍結稿として参照するだけで、数値の出所にしない |

### 4.3 repo 内の一次資料 (tracked)

SHA-256 は本稿の起草時に作業ツリーの現物から実計算した。

| 資料 | path | SHA-256 |
|---|---|---|
| 事前登録 (2026-09-19 追記込み、本 cohort が束縛した版) | `docs/b10-backoff-static-tail-preregistration.md` | `8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e` |
| cohort 1 の稿 (主結果) | `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` | `9bf74beb5c9251e797e3501e87122b11c9a8157c9bfbe4ce4a04d3e55daeaed9` |
| 2 本目の地位を先に決めるという裁定 | `docs/decisions.md` の D2050 | (台帳は追記型なので file 全体の SHA-256 は書かない) |
| 本 wave の記録 (投入・失敗 attempt・集団報告・consult とレビューの逐語) | `output/insights/2026-09-19/b10-tail-cohort2/README.md` | (本稿と同じ commit で作り、commit 前に bytes が確定しないため SHA-256 は書かない。同 insight は本稿の hash を持たないので循環はしない) |

### 4.4 同じ結果についての既存の稿

**results 系列にこの cohort の稿は他に無い。** 本稿が最初である。cohort 1 の稿
`results/2026-09-16-b10-static-tail-not-observed.md` は別 cohort (主結果) の稿であり、本稿はそれを改めない。

版の側では、最新版 `2026-09-17.md` は B-10 を cohort 1 の 1 本で書いている。**本稿は版を改めない。** 版へ
取り込むかどうかは、次の版の契約が決める。
