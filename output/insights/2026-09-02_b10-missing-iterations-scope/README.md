# B-10 正式走の欠測 — 「7」は開始済み分だけの数で、登録格子に対しては 73 枠が埋まっていない

worklog エントリ 1189 が 1 文で触れた「予定 294 反復に対し観測 287、7 反復は実行されずに
終わっている。外側 job の壁時計打ち切りによるもので、検査の拒否ではない。その 2 変種は
45 cell に含まれない」の射程を、既存記録だけで確定した記録である。**新しい測定はしていない。**

決めたのは 3 点である。

1. **欠測した 2 変種はどの主張・図・集計に入っているか。**
   未完了の枠そのものはどこにも入らない。観測済みの 5 反復は 287 件の完全性集計に入り、
   うち 3 反復は所要の回帰 (238 反復) に入る。同じ `variant_id` と point は
   write-heavy の 45 cell に各 3 record 実在する (build attempt は別)。
   **図には 1 件も入らない。** 下流に派生記述が 4 件ある。
2. **45 cell の `correctness_certified=true` の射程は、欠測でどう限定されるか。**
   45 record の値は 1 件も降格しない。欠測 2 attempt はその認証元ではない。
   ただし 45 cell はもともと 1 workload・1 request・15 認証単位の記述的成果であり、
   正式系列の完全性も他 workload の認証も担っていない。
3. **論文で使える範囲。** 45 cell の記述的結果と、観測された範囲の正しさ検査結果は
   但し書き付きで使える。**完全性の開示に「予定 294 / 観測 287 / 欠測 7」を使ってはいけない。**
   事前登録した 3 族の判定は使えない。

**本書は当時の判定を昇格も降格もさせず、追記として記録する (絶対規律 7)。**
worklog エントリ 1189 と既存 insight の bytes は 1 バイトも変えていない。

---

## 1. 数える単位を分ける

エントリ 1189 の 1 文が混ざっていたのは、次の 5 つが別物だからである。

| 単位 | 何か | 個数 |
|---|---|---:|
| `variant_id` | genome の hash。**workload に依存しない** | 15 |
| campaign | workload ごとの 1 正式走 | 4 (write-heavy が 2 本) |
| build attempt | (campaign, variant) の組。`build_attempt_id` は campaign ごとに別 | 開始 49 / commit 47 |
| verify 反復 | 1 回の trace 有効走 (ベンチ → トレース → 直列性検査) | 完了記録 287 |
| cell | 3 block x 15 点の性能 record | 45 (write-heavy のみ) |

**`variant_id` が workload 共通である**ことが、エントリ 1189 の「その 2 変種は 45 cell に
含まれない」を誤りにしている。同じ ID は write-heavy の 45 cell にも入っている。
正しくは「**欠測した balanced / read-heavy の build attempt は 45 cell の認証元ではない**」である。

| 変種 | campaign | `build_attempt_id` |
|---|---|---|
| `c7c331ebe662` (symmetric-modulo-mu100) | balanced (未完) | `358527d389db442ade4e8d1fb789a041` |
| `c7c331ebe662` | write-heavy `e3de15eb` (45 cell) | `ca8336bbaf75ed924981e13357ec9461` |
| `292d58f1dad8` (constant-mu2) | read-heavy (未完) | `4506672584e9ab3f4d012e91ce90f1e3` |
| `292d58f1dad8` | write-heavy `e3de15eb` (45 cell) | `58937c239a567a724717b962ff30d1c4` |

---

## 2. 分母は 3 つある。「7」はそのうち最も狭いものである

**事前登録は 3 workload それぞれに 15 点を登録する。** 生成器の
`POINTS_PER_BLOCK = 3 + len(MEANS_US) * len(SHAPES)` は
`MEANS_US = (2, 5, 10, 25, 50, 100)`、`SHAPES = (("constant", 0), ("symmetric-modulo", 1))`
から 15 になり、campaign は `run_campaign(cfg, genomes(), ...)` に 15 点全部を渡す。
1 点あたりの verify 反復は legacy 1 回 + performance 5 回 = 6 回で、
これは spec の `correctness_mode = "legacy+performance"`、`correctness_reps = 5` から来る。

**ところが read-heavy は 15 点のうち 4 点しか開始していない。** 残り 11 点 x 6 = 66 枠は
そもそも走っていない。したがって `294 = 49 build_start x 6` は
**開始済み attempt に条件づけた事後の分母**であって、登録格子の予定数ではない。

| 母集団 | 予定 | 完了記録 | 差 |
|---|---:|---:|---:|
| 開始済み 49 attempt に条件づけた分 | 294 | 287 | **7** |
| 登録された 3 workload の組 (write-heavy は完走した `e3de15eb` を採る) | 270 | 197 | **73** |
| 4 campaign の履歴すべて (先行 write-heavy `068fd2cd` を含む) | 360 | 287 | **73** |

73 の内訳は balanced 5 + read-heavy 68 (未開始 11 点 x 6 = 66 と、開始済み constant-mu2 の 2)。
タグ別には legacy が 11 枠、performance が 62 枠欠けている。

**完全性を開示するときに「予定 294 / 欠測 7」だけを書くと、欠測を 66 枠過小に見せる。**

### 4 campaign の内訳 (WAL 実測)

| campaign | 更新 | build_start | build_done | commit | verify_done | 位置づけ |
|---|---|---:|---:|---:|---:|---|
| write-heavy `068fd2cd` | 09-01 05:00 | 15 | 15 | 15 | 90 | 相を分けた先行 attempt。perf が binary SHA 不一致で全滅 |
| balanced `15e75b3f` | 09-01 11:00 | 15 | 15 | **14** | 85 | 6 時間枠で打ち切り |
| write-heavy `e3de15eb` | 09-02 00:52 | 15 | 15 | 15 | 90 | **45 cell を認証した完走 attempt** |
| read-heavy `ed8a676b` | 09-02 06:52 | **4** | 4 | **3** | 22 | 15 点中 4 点だけ開始、3 点で撤去 |
| 合計 | | 49 | 49 | 47 | **287** | |

`abort` stage は 4 campaign とも **0 件**である。**検査が拒否した走行は 1 件も無い。**

---

## 3. 欠測 7 枠の同定 — すべて performance タグである

commit へ到達しなかった attempt は 2 つで、genome 文字列の exact 一致で point が確定する。

| campaign | 変種 | genome | point | legacy | performance | 欠け |
|---|---|---|---|---:|---:|---:|
| balanced | `c7c331ebe662` | `BACKOFF_FIXED=1100` | symmetric-modulo-mu100 | 1 | 0 | **5** |
| read-heavy | `292d58f1dad8` | `BACKOFF_FIXED=2` | constant-mu2 | 1 | 3 | **2** |

- **欠けた 7 枠はすべて performance タグである。legacy の欠測は 0 件** —
  開始済み 49 attempt はすべて legacy 反復を 1 回取り終えている
  (**この「0 件」も開始済み分に条件づいた数である。**登録格子に対しては legacy が 11 枠欠けている)。
- 287 件の内訳は legacy 49 + performance 238。
- 観測された 5 反復 (balanced の legacy 1、read-heavy の legacy 1 + performance 3) は
  いずれも `verdict = serializable`、`anomalies = 0`、`certified = true` だった。

---

## 4. 「実行されずに終わった」とは書けない。ただし上界は出せる

`verify_done` は検査器が返った後にだけ WAL へ書かれる。**反復の開始を記録するイベントは無い。**
したがって記録が証明するのは「完了記録が無い」までであって、「一度も実行されなかった」ではない。

最後の完了記録から job 終了までの空白は測れる。

| campaign | 最後の完了記録 | job 終了 | 空白 |
|---|---|---|---:|
| balanced | 09-01 11:00:56 | 09-01 11:02:16 | 80 秒 |
| read-heavy | 09-02 06:52:31 | 09-02 06:56:55 | 264 秒 |

**ここから上界が出る。** 反復は
`for _repetition in range(workload.reps): _run_one_repetition(...)` で厳密に逐次に走る。
完了記録が 1 件も増えていない以上、空白の中で開始できた反復は attempt あたり高々 1 件である。

> **7 枠のうち開始されたのは高々 2 件で、少なくとも 5 件は一度も開始されていない。
> 7 枠のどれにも完了記録は無い。**

検査器が返ってから WAL へ書くまでの間に落ちた窓は原理的に残るが、その窓は
返り値の取得から書き込みまでに限られる。**7 枠のどれにも verdict・anomaly・integrity の
主張を付けてはいけない。**

参考までに、同 campaign の performance 反復 1 回の所要は balanced が 197.9-270.5 秒、
read-heavy が約 1350-1470 秒である。どちらの空白もそれより短い。

---

## 5. 打ち切り理由は 2 種類ある — エントリ 1189 の帰属は片方だけ正しい

| campaign | request | 経過上限 | Elapse | Remaining | scheduler の文言 |
|---|---|---:|---:|---:|---|
| balanced | `963545.nqsv` | 21600 秒 (6h) | 21609 秒 | **0 秒** | `Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)` |
| read-heavy | `965996.nqsv` | 43200 秒 (12h) | 20950 秒 | **22250 秒** | `Terminated` |

- **balanced の 5 枠は壁時計打ち切りである。** 受領証が理由を明記し、残余は 0 秒である。
- **read-heavy の 2 枠は壁時計打ち切りではない。** 12 時間枠の 48% しか使っておらず、
  6 時間 11 分が残っていた。受領証が書くのは `Terminated` までで、送信主体は記録されない。
- **撤去主体は同時代の worklog エントリ 1187 が確定する。** ユーザー裁定を記録し、
  `qdel` を実行したと明記している。claim 競合は WAL 作成前の `acquire_claim` で止まるので、
  22 件の完了記録まで進んだ read-heavy の終端原因にはならない。

両 job attempt dir に `failure.json` は無く、`driver.stdout` / `driver.stderr` は 0 byte である。
read-heavy の scheduler.stderr には `user_script: line 108: number: unbound variable` が残っており、
壊れた signal handler が発火して `write_failure` へ到達しなかった痕跡である
(この欠陥は worklog エントリ 1193 で修理済み)。

**どちらも検査の拒否ではない。** これはエントリ 1189 の結論そのままで、`abort` stage 0 件が裏づける。

---

## 6. 問い 1 — どの主張・図・集計に入っているか

入り先は 3 層に分かれる。

| 対象 | 287 の完全性集計 | 238 反復の所要回帰 | 「read-heavy は約 7 倍」 | write-heavy 45 cell | 図 |
|---|---|---|---|---|---|
| 未完了の 7 枠 | 入らない | 入らない | 入らない | 入らない | 入らない |
| balanced `c7c331ebe662` の観測分 | legacy 1 件が入る | **0 件** | 入らない | — | 入らない |
| read-heavy `292d58f1dad8` の観測分 | legacy 1 + performance 3 が入る | **performance 3 件が入る** (read-heavy 18 のうち 3) | **入る** | — | 入らない |
| 同じ `variant_id` / point | — | — | — | **write-heavy record が各 3 件** | 入らない |

### 図には 1 件も入らない

`fig2b_backoff_sweep_3workload` の入力 campaign は `backoff-sweep-silo-<workload>-sweep-<hash>`、
`fig2c_b10_extended_backoff` は `b10-backoff-grid-silo-<workload>-sweep-<hash>` で、
生成時の外部 root は `/work/1/SFC/tanab/b10-backoff-grid-runs5` である。
**正式走 4 campaign (`b10-backoff-shape-silo-<workload>-formal-<hash>`) は
どちらの図の入力にも現れない。** 根拠は figure provenance の入力 field だけに置く。

### 直接集計の下流に派生記述が 4 件ある

- 正式走 insight の「read-heavy の commit は 1690 万件」と検査 1 回の所要。
- 現行 worklog の T-2191 (直列性検査の並列化)。238 反復回帰から
  70.0-87.0 マイクロ秒/commit と 15 認証単位を導いている。
- `docs/b10-multinode-formal-run-design.md` の read-heavy 5 時間・3 変種・約 25 時間の外挿。
  job の壁時計には、commit へ到達しなかった 4 変種目に使った時間も含まれる。
- `docs/decisions.md` の D1485 が「直列性検査 1 回 23 分」を優先順位判断に使っている。

**いずれも値の向きは変わらない。**欠測変種の 3 反復は他の read-heavy 変種と同じ帯にあり、
外れ値ではない。ただし母集団の但し書き (commit へ到達しなかった attempt の 3/5 反復を含む) が
付いていない。本 wave はこれらの文書を変更していない。

### 「約 7 倍」の再現

対応する点の平均 commit 数の比は次のとおりである。

| point | read-heavy 平均 commit | write-heavy 平均 commit | 比 |
|---|---:|---:|---:|
| none | 16.888M (n=5) | 2.339M (n=5) | 7.22 |
| zero-loop | 17.089M (n=5) | 2.393M (n=5) | 7.14 |
| constant-mu2 (**欠測 attempt**) | 16.928M (**n=3**) | 2.478M (n=5) | 6.83 |
| adaptive | 5.588M (n=5) | 1.111M (n=5) | 5.03 |

**「約 7 倍」は commit が飽和した 3 点の 6.83-7.22 倍であり、adaptive は約 5.03 倍である。**
15 点の格子全体の比ではない。3 点のうち 1 点は欠測 attempt の 3 反復から出ている。

---

## 7. 問い 2 — 45 cell の `correctness_certified=true` の射程

### 変わらないもの

- **45 record は今も 45/45 が `correctness_certified=true` / `missing=false` である。**
  欠測はこの値を 1 件も降格させない (絶対規律 7)。
- 45 cell の出所は単一 request `965564.nqsv`、workload は write-heavy、campaign は `e3de15eb`。
  認証単位は distinct `(variant_id, build_attempt_id)` の **15 組**で、
  同一点の 3 block が 1 変種の認証を共有する。
- 認証元は `e3de15eb` の legacy 15 + performance 75 = 90 回の trace 有効走である。
  **欠測した 2 attempt は、この 90 回のどれでもない。**

### もともと限定されていたもの (欠測とは無関係)

45 cell は 1 workload・1 request の記述的成果であり、**正式系列の完全性も他 workload の認証も
担っていない。** これは欠測が新たに課した制限ではなく、当初からの射程である。

- provenance の top-level `official_certification` は **`false`**。全 45 record も `false`。
- 事前登録の 3 族判定は、balanced と read-heavy が **`pairs=0` / `indeterminate`** (理由は各 18 件、
  すべて `missing:block-<1|2|3>:mu<2|5|10|25|50|100>`)、write-heavy だけが
  `pairs=18` / `testable` / `not-detected` (`raw_p=0.025566101`、`holm_p=0.076698303`) である。

**つまり「欠測 7 枠が 45 cell の射程を狭めた」のではない。** 45 cell はもとから
1 workload に閉じており、2 族が indeterminate なのは両 campaign が性能相を一度も走らせず
18 pair 全部が欠けているからである。7 枠が関わるのは balanced mu100 の 3 pair と
read-heavy mu2 の 3 pair だけで、残り 15 pair ずつの欠落は 7 枠と無関係である。

### `certified` の意味を 4 項に縮めない (エントリ 1189 の追記訂正)

エントリ 1189 は `certified` を「読んだ committed txn 数 = counter」「txid に欠番なし」
「取引 frame が閉じている」「orphan read なし」の 4 条件で説明したが、これは**代表例であって
全条件ではない**。`Integrity.clean()` は orphan read、version 重複、txid 重複、genesis commit、
txid 欠番、write-version 不一致、不正 key、framing、lock coverage、write intent、permutation、
commit witness の **12 項の連言**であり、`certified` はさらに `n_txns > 0` と
`serializable` を要求する。commit witness は expected / observed が両方 None でも
clean を通るが、B-10 の pipeline は witness の存在と batch count 0 を先に要求してから
expected を検査器へ渡す。

**これは正しさゲートを強い側へ言い直す訂正であり、規律 2 を緩めない。**

---

## 8. 問い 3 — 論文で使える範囲

### 但し書き付きで使える

| 使えるもの | 必ず添える但し書き |
|---|---|
| request `965564.nqsv` の write-heavy 45 record が全件 `correctness_certified=true` / `missing=false` だったこと | 1 workload・1 request・15 認証単位。top-level `official_certification` は `false` |
| 45 cell の throughput・abort 率・backoff 呼び出し回数を記述的結果として | 3 workload の形の結論にしない。絶対 throughput を headline 値の出所にしない |
| 完了記録が残る 287 反復すべてが `certified=true` で `abort` が 0 件だったこと | 「観測された範囲では」を必ず残す。4 attempt にまたがり write-heavy が重複、read-heavy は 15 点中 4 点。D295 の非検出限界 (common-mode failure と個数を保存する破損) は閉じていない |
| 238 反復の所要と commit 数の回帰を、検査の運用費用の事後分析として | B-10 の throughput 効果でも機構上の限界費用でもない。read-heavy 18 件のうち 3 件は commit へ到達しなかった attempt のもの。打ち切りによる打ち切り効果 (censoring) がある |
| 「read-heavy の検査対象は write-heavy の約 7 倍」を運用説明として | commit が飽和した 3 点の 6.83-7.22 倍。adaptive は約 5.03 倍。格子全体の比ではない。3 点のうち 1 点は欠測 attempt 由来 |
| balanced 85 件・read-heavy 22 件の整合性検査が通ったこと | 未完了枠、common-mode failure、trace 無効ビルドの走行は覆わない |

### 使える

- **図 `fig2b` / `fig2c` の入力は正式走ではない**という事実。したがって本件の欠測は
  両図の欠測ではない。

### 使えない

| 使えないもの | 理由 |
|---|---|
| **「予定 294 / 観測 287 / 欠測 7」を完全性の開示として書くこと** | 開始済み attempt に条件づけた分母である。登録格子に対しては 270 / 197 / **73** |
| 「3 workload で一定と対称 modulo の差を事前登録の手続きにより確定した」 | 3 族のうち 2 族が indeterminate、`official_certification=false` |
| balanced の symmetric-modulo-mu100、read-heavy の constant-mu2 を、5 反復が揃った cell として報告すること | 前者は performance 0 回、後者は 3 回。両 campaign に性能 record は 1 件も無い |
| 完了記録の無い 7 枠に serializable / anomaly なし / certified を付けること | 記録が存在しない |
| 「7 反復は実行されずに終わった」と断定すること | 記録が証明するのは完了記録の不在まで。高々 2 件は開始されていた可能性がある |
| 「7 反復はすべて外側 job の壁時計打ち切りによる」と書くこと | read-heavy は 6 時間 11 分を残していた |
| write-heavy の `not-detected` を正式系列全体の結論として使うこと | 1 族だけの結果であり、`holm_p=0.076698303` で有意でもない。正式走 insight 自身が結論化を拒否している |
| 「欠測 7 枠は無害だった」と書くこと | 下記の反実仮想 |

---

## 9. 反実仮想 — 欠測 7 枠は「無害」ではない

事前登録の `analysis.missingness` は
`conditions = [missing, performance-error, correctness-not-certified, unstable, underexposed]`、
`pair_action = invalidate-entire-family`、`family_action = indeterminate`、
`indeterminate_pvalue = 1.0` を定める。

- **実際に起きたこと:** balanced と read-heavy が indeterminate なのは 7 枠のせいではない。
  両 campaign は性能相を一度も走らせておらず、`reports/`・`variants/`・`spec/` は空で、
  残るのは `runs/wal.jsonl` と `campaign.lock` だけである。18 pair 全部が missing である。
- **反実仮想:** 他がすべて揃っていたとしても、両 attempt は認証へ到達していないので
  その点の 3 block record は `missing` または `correctness-not-certified` になり、
  `pair_action = invalidate-entire-family` により 2 族とも indeterminate になる。

**この反実仮想は、発効した spec と、そこへ束縛された解析実装の合成として成立する。
spec の字義だけからは出ない。** 必要な前提は次のとおりで、いずれも実装側にある。

1. attempt は legacy 1 回 + performance 5 回を全部通るまで commit されない。
2. commit 済み attempt だけが性能 cell の認証源になる。
3. 同じ `variant_id` の write-heavy の認証を balanced / read-heavy へ移送しない。
4. 認証が無ければ、その点の 3 block record は `missing` または `correctness-not-certified` になる。
5. 残り 15 pair がすべて usable である (これは実測されていない反実仮想の前提である)。

**必要なのは「7 件全部」ではない。各 attempt に未完了枠が 1 件でもあれば足りる。**

---

## 10. worklog エントリ 1189 への追記訂正 (5 件)

**エントリ 1189 の bytes は変更していない。** 絶対規律 7 に従い、追記でのみ訂正する。
当時の判定 (トレース側だけで件数が減る切り捨ては起きていない) は昇格も降格もさせない。

| # | エントリ 1189 の記述 | 訂正 |
|---|---|---|
| 1 | 「予定 294 反復」 | 開始済み 49 attempt に条件づけた事後の分母である。登録格子に対しては 270 枠に対し完了記録 197、差 73 |
| 2 | 「7 反復は実行されずに終わっている」 | 記録が証明するのは完了記録が無いことまで。開始されたのは高々 2 件、少なくとも 5 件は一度も開始されていない |
| 3 | 「外側 job の壁時計打ち切りによるもの」 | balanced の 5 枠は壁時計 (残余 0 秒)。read-heavy の 2 枠は壁時計ではない (残余 22250 秒)。撤去はユーザー裁定によるもので、エントリ 1187 が `qdel` を記録している |
| 4 | 「その 2 変種は 45 cell に含まれない」 | `variant_id` は workload 共通なので、同じ ID と point は 45 cell に各 3 record 実在する。正しくは「欠測した balanced / read-heavy の build attempt は 45 cell の認証元ではない」 |
| 5 | 「7 反復は何の正しさ主張も担っていない」 | 完了記録の無い枠が正しさの肯定的主張を担わないという意味では正しい。ただし事前登録の欠測規則の下では族の判定可能性を左右するので、「何も担っていない」とは書けない |

あわせて、エントリ 1189 が挙げた `certified` の 4 条件は代表例であって全条件ではない (§7)。

**訂正しないもの:** 「検査が拒否した走行は 1 件も無い」(`abort` stage 0 件で裏づけ済み)、
「45 cell の `correctness_certified=true` はそのまま維持される」、
所要を説明するのは試行数でなく commit 数であること。

---

## 11. この判定が保証しないこと

- **反復が開始されたかどうかは、記録からは決められない。** 言えるのは完了記録の不在と、
  逐次実行から出る上界 (開始は高々 2 件) までである。
- **トレースの実体はもう残っていない。** 検査を通った走行の一時ディレクトリは削除される。
  欠測枠については、そもそも成果物が何も無い。
- **D295 の非検出限界は閉じていない。** trace と counter は同じ実行体から出るので、
  両方が同時に落ちる common-mode failure と、個数を保存する破損は検出しない。
  これはエントリ 1189 の射程のままで、本書はそれを広げない。
- **本書は「73 枠が欠けている」ことの原因を全部説明していない。** balanced の 5 枠と
  read-heavy の 2 枠の外因は上記で確定したが、read-heavy の未開始 11 点 (66 枠) は
  同じ撤去に巻き込まれた分であり、個別の外因を記録から分けていない。
- **図の非帰属は、tracked な論文図 2 件と、それぞれの provenance の入力 field についてである。**
  repo の外にある図一般については何も言っていない。
- 派生記述 4 件について、値を直すべきかどうかは本書では裁定していない。次の一手へ送る。

---

## 12. 集計の再現手順

公式出力 root は
`/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output`、
各 campaign の WAL は `<root>/campaigns/<campaign_id>/runs/wal.jsonl`、
投入証拠 root は `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions` である。

- stage 内訳: `jq -r '.stage' <WAL> | sort | uniq -c`
- 未 commit attempt: `build_start` の `.variant` 集合から `commit` の `.variant` 集合を引く
- point の同定: WAL の `.payload.genome` を、write-heavy provenance
  (`output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json`)
  の `.records[].genome` と exact 一致で突き合わせる
- タグ内訳: `jq -r 'select(.stage=="verify_done") | .payload.workload.tag' <WAL> | sort | uniq -c`
- 45 cell: 同 provenance の `.records | length`、
  `[.records[] | [.variant_id, .build_attempt_id]] | unique | length`、
  `[.records[].request_id] | unique`
- 族判定: 同 provenance の `.judgement.families[]` と `.official_certification`
- 打ち切り理由: `<submissions>/<nonce>/scheduler.stderr` の
  `Elapse` / `Remaining Elapse` と終了理由の行
- 空白時間: WAL 末尾の `.ts` と scheduler の `Ended Request Time` の差

集計に使った使い捨てのコマンドは repo へ入れていない (実装面の差分を 0 に保つため)。

段 2 のプラン、段 3 の敵対相談 2 本、段 4 の裁定の逐語は `verbatim/` に置いた。
**子が出した数値・path・行参照は親がすべて独立に確かめ、一致しなかったものは無い。**
親の実測のうち 3 件が誤っており (§10 と裁定文書)、いずれも子の指摘で見つかった。
