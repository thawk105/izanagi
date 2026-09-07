# 2026-09-07 — backoff 単独論文の主張軸 B5 の文献検索 事前登録 (凍結)

- **作成日:** 2026-09-07
- **入力 commit:** `d19d2182fbc324f67b47f600be70136d6503aa59` (local main、本 wave の base)
- **入力 digest:** 下記 input path の内容は入力 commit の blob そのものである。
  - `docs/related-work/README.md` = `b5153305186918436bd9b53c9516f8658968b211`
  - `docs/related-work/claim-survey/2026-09-05-backoff-axis-registration.md` = `901ba833306e5e20ce902995b0c20b046089eb09`
  - `docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md` = `469d674138dc71ffe4446571e67a5aaeb1ddf9e5`
  - `docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md` = `6eb3150406fa99720d6690f710ea6da0f5de8089`
  - `docs/related-work/claim-survey/2026-08-27-axis3-index-measurements.md` = `c490613dab0e3734df7482e8a2a0cf500746637a`
  - `docs/paper-story-backoff/2026-09-05.md` = `451ad81410b525a66501d9ce9d6835c251593c64`
  - `external/ccbench` は submodule であり、入力 commit の tree では gitlink
    `511c9538e4e8efa54b45cda62e72389ed3b706ec` である。本文書が §4.2 で走査した
    `external/ccbench/README.md` は、その submodule commit の blob
    `cff93802afce1381eef3a370ece436fb3c93eb45` を指す。
- **入力 path:** 上記 6 file、および `docs/related-work/claim-survey/README.md` /
  `docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md` /
  `docs/related-work/literature-map/` / `docs/related-work/notes/` / `external/ccbench/README.md`
- **文献 cutoff:** §2.2 に定める。**本登録で新しい掃引・検索・Web 参照・外部 request は一切行っていない。**
- **規則の正本:** `docs/related-work/README.md` の「7.7 主張軸別の調査状態と、不在主張の成立条件」
- **軸の定義元:** `docs/paper-story-backoff/2026-09-05.md` §3 の B5、および
  `docs/related-work/claim-survey/2026-09-05-backoff-axis-registration.md` §1

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. この文書は何であって、何でないか

**これは登録である。実行ではない。**

**書いたもの:** 軸 B5 について、7.7.4 が `RW3` を名乗る前提として要求する事前登録 —
索引 3 つの操作集合と cutoff、概念ブロックと検索式、母集合の外、候補 3 群の positive control 契約、
完走述語、停止条件、amendment の境界。

**書いていないもの:** 検索の実行結果。ヒット件数。総件数。候補の接地判定。
**索引に対する新しい構文実測。** 本文書の作成中に外部 HTTP request は 1 本も出していない。

**この文書は 7.7.4 の事前登録を単独で満たす完全な登録ではない。部分登録である。**
**本文書だけでは検索の実行を認可しない。** 実行を認可しない理由は次の 3 つで、
**どれか 1 つでも残る限り軸 B5 の走行を開始してはならない。**

1. **候補 3 群の主キー (DOI または arXiv ID) が 1 つも確定していない** (§4.2)。
   したがって本文書は 7.7.6 の positive control を「配置した」とは主張しない。
2. **query catalog の bytes と SHA-256 が seal されていない** (§3.3、§5.3)。
   展開規則は決定的に登録したが、その出力を固定した機械可読 catalog はまだ無い。
3. **補助探索のうち引用・著者経路の起点が確定していない** (§4.5)。
   起点は 1 の主キーに依存する。

これらはいずれも外部照会または実行器の走行を要し、本 wave の範囲外である。
**充足は本文書を書き換えずに、新しい日付の後継凍結物で行う** (D1208)。

**軸 B5 の成熟度は `RW0` のままである。** 本文書は世界の不在を支持しない。
7.7.3 に従い、`RW0` では世界の不在の表現を一切使わない。
本体論文の軸 1〜5 の状態も動かさない。

**内部の不在** (repo の中に軸 B5 へ接地する調査資産があるか) は
`2026-09-05-backoff-axis-registration.md` §2 が母集合と走査語つきで持つ。本文書はそれを更新しない。

## 1. 軸 B5 と分類契約

`2026-09-05-backoff-axis-registration.md` §1 の 4 条件を逐語で継承する。**新しい定義をしない。**

| 条件 | 内容 |
|---|---|
| **A 対象** | トランザクション (または STM) の abort / conflict 後の再試行待ち (backoff) を調整する機構である |
| **B 機構** | 調整器が観測窓 (更新間隔・評価周期) ごとの計測に基づいて待ち量を動かす (hill climbing、勾配符号、確率近似など) |
| **C 動的化** | その観測窓の幅 (更新間隔) 自体を、走行中の観測 (窓あたりの標本数、推定誤差、abort 率など) に基づいて決める。固定定数ではない |
| **D 正しさ** | 待ち量の変更が直列化可能性を変えないことを、検証または論証で扱う |

強さは `直接接地` (A・B・C をすべて満たす) / `部分接地` / `非接地`、
極性は `競合` / `方法論的祖先` / `外部補強` / `反面教師` / `正しさ側の道具` とする。
**D は極性の判定に使い、強さには入れない。**

**検索語が本文に出現することは、A・B・C・D の充足の証拠ではない。**
全候補について一次資料を読み、条件ごとに充足を記録して判定する (7.7.5)。
**D 語が無いことを理由に除外へ倒してはならない。**

判定語彙は 7.7.5 の 5 語 (`検出` / `近傍` / `除外` / `要裁定` / `未完走`) を使う。
**`要裁定` を不在側へ倒してはならない。**

数え上げの単位は index 固有の work ID とする (7.7.5、D1207)。
**軸別の数を足し合わせない。** D1156 が定める軸 1 分類 pilot 29 行の C 欄・D 欄の集計禁止と
行間比較禁止は**期限なしで有効**であり、本文書はそれを解除しない。
D1209 (資料階層が行ごとに違う属性欄の集計禁止) は**追加で**適用する。
**D1209 は D1156 を置き換えない。**

## 2. 索引 3 つ

### 2.1 索引と検索対象フィールド

7.7.4 は「同一 cutoff の arXiv、OpenAlex、DBLP の検索結果の和集合を最小とする」と要求する。
**ただし 3 索引の検索対象フィールドは同一ではない。** 母集合の定型名は
「同一 cutoff の 3 索引」ではなく次とする。

> arXiv の要旨、OpenAlex の題名・要旨、DBLP の書誌・題名という**索引別の操作集合**に、
> 共有の暦境界を当てた登録取得集合の和

| 索引 | endpoint | 検索対象フィールド | 版または代替来歴 |
|---|---|---|---|
| arXiv | `https://export.arxiv.org/api/query` | `abs` (要旨)。句と AND / OR を使う | 版を返さないため D1206 の代替来歴を page ごとに保存 |
| OpenAlex | `https://api.openalex.org/works` | `title_and_abstract.search` (題名と要旨、stemming あり) | 同上。`meta.x_query` を証拠として保存 |
| DBLP | `https://dblp.org/search/publ/api` | 書誌・題名。**要旨を索引しない**。複数語は句ではなく各語の前方一致連言 | 同上 |

**索引が API または export の版を返さない場合、版番号を捏造しない。** D1206 に従い、page ごとに
(a) 実際の接続先、(b) 応答に実在した field の exact locator、(c) HTTP client が観測した
response header (同名の重複を落とさない)、(d) parser へ渡す前の entity body bytes の SHA-256 を
保存する。これは wire 上の全 bytes や API 版との同等性を証明せず、取得時点の来歴だけを持つ。

**取得日時**は attempt ごとに request 開始と応答完了を UTC の RFC 3339 で記録する。
未来の時刻を書かない。preflight と本走には別の phase ID を付ける。

**ひとつでも列挙不能・総件数不明・取得失敗があれば `RW3` を名乗らない。**
使えなかった索引を黙って母集合から外さない (7.7.4)。

### 2.2 cutoff — 索引固有の日付欄へ共有の暦境界を当てる

- **上限境界: `2026-12-31` (UTC)。** 3 索引すべてに同じ暦境界を当てる。
- **下限境界: 置かない。** arXiv は API が閉区間を要求するため技術的下限
  `199101010000` (arXiv 開設以前) を書くが、これは操作上の下限なしと同義である。

| 索引 | 日付欄と表現 |
|---|---|
| arXiv | `submittedDate:[199101010000 TO 202612312359]` |
| OpenAlex | `to_publication_date:2026-12-31` |
| DBLP | 年 facet を使わず全年取得し、record の `year <= 2026` を client 側で判定する。**`year` 欠落は除外せず `要裁定`** |

**この境界は work 単位で一様ではない。** 索引ごとに「日付」の意味 (投稿日 / 公開日 / 収録年) が
違うためである。この非一様性は軸 1 事前登録 §2 と同型であり、限界として §9 に残す。

### 2.3 索引構文について本文書が持っていない実測

**本登録は索引に 1 本も request を出していない。** §3 の完全 query は、
`2026-08-27-axis3-index-measurements.md` が 2026-08-27 に**別の語**で観測した構文事実からの
**外挿**である。外挿であることを隠さない。

観測済みで本登録が依拠する事実:

- DBLP は 2 分ハイフンを各片の前方一致へ割る (`many-core` → `many* core*`、
  `read-write` → `read* write*`)。**3 分ハイフンは別形で、中央語に `*` が付かない**
  (`end-to-end verification` → `end* to end* verification*`)。
- OpenAlex はブロック内の語を送信順ではなく辞書順へ並べ替える。
  **AND で結んだブロック自体の順序は未実測**であり、2 仮説を分離できていない。
- OpenAlex は題名・要旨を stemming する。

**したがって §3 の期待 echo は登録値であって観測値ではない。**
一致しなければ §5.4 の意味的 amendment とする。**preflight の観測をそのまま期待値に据えない** —
それは事後登録になる。

## 3. 概念ブロックと検索式

### 3.1 概念ブロック

7.7.4 は「対象・機構・出力・正しさ・ワークロードの概念ブロック」を要求する。軸 B5 では
条件 C (更新間隔そのものの動的化) が軸の核なので、C を独立ブロックとして立てる。
**各語には固定 ID を振り、表記・ハイフン・ブロック所属を登録 bytes の一部とする。**

- **T (対象、A に対応、12 語):** `transaction processing` / `database transaction` /
  `transactional memory` / `software transactional memory` / `STM` / `concurrency control` /
  `optimistic concurrency control` / `transaction abort` / `transaction conflict` /
  `transaction retry` / `retry transaction` / `transaction scheduling`
- **M (調整機構、B に対応、19 語):** `backoff` / `back-off` / `retry delay` / `retry wait` /
  `wait policy` / `waiting policy` / `contention manager` / `contention management` /
  `adaptive contention manager` / `adaptive transaction scheduling` / `hill climbing` /
  `stochastic approximation` / `finite-difference gradient` / `gradient sign` /
  `simultaneous perturbation stochastic approximation` / `SPSA` / `adaptive step size` /
  `adaptive gain` / `variable step size`
- **O (動かす出力・量、B に対応、10 語):** `backoff time` / `backoff interval` /
  `backoff duration` / `retry interval` / `waiting time` / `wait duration` / `sleep time` /
  `contention window` / `step size` / `gain sequence`
- **C (動的化される間隔・窓、C に対応、21 語):** `update interval` / `update period` /
  `evaluation interval` / `evaluation period` / `measurement interval` / `measurement window` /
  `observation interval` / `observation window` / `sampling interval` / `sampling period` /
  `sampling window` / `control interval` / `adaptation interval` / `adaptive window` /
  `dynamic window` / `variable window` / `adaptive update interval` / `dynamic update interval` /
  `online window selection` / `runtime window selection` / `run-time window selection`
- **W (走行中に観測する信号、C に対応、13 語):** `samples per window` / `sample count` /
  `sample size` / `estimation error` / `gradient variance` / `variance estimate` /
  `confidence interval` / `abort rate` / `conflict rate` / `commit rate` / `throughput` /
  `contention level` / `workload`
- **V (正しさ、D に対応、10 語):** `serializability` / `opacity` / `linearizability` /
  `correctness` / `safety` / `invariant` / `verification` / `proof` / `progress guarantee` /
  `liveness`

**6 ブロックは文字列として互いに素である。** 同一語が 2 ブロックに属さないことを登録の一部とする
(これにより DBLP の二項直積に重複 request bytes が生じない)。

**`adaptive step size` / `adaptive gain` / `variable step size` は M に置く。** これらは
「刻みの適応」であって「更新間隔の動的化」ではないため、C に置くと C の意味が薄まる。
確率近似の適応 step は候補群 G2 (方法論的祖先) の主題なので、M から拾う。

> **この語列は同義語閉包ではなく、有限な操作的定義である。** 未登録語を暗黙に含めない。
> 語の追加・削除・表記変更・ブロック所属の変更は登録取得集合を変えうるため、
> §5.4 の意味的 amendment とする。同じ語列でも索引ごとに field・stemming・前方一致が異なるため、
> 3 索引が同じ集合を表すとは主張しない。

### 3.2 登録する枝

7.7.4 は「狭い積集合だけでなく、語彙差を拾う広い二項組合せも事前に登録する」と要求する。

| 枝 ID | 論理式 | 役割 |
|---|---|---|
| `B5-Q1` | T ∧ M ∧ C | 狭い積集合 (A・B・C の交点そのもの) |
| `B5-Q2` | T ∧ O ∧ C | 機構名を使わずに待ち量と窓だけを書く直接候補 |
| `B5-Q3` | M ∧ C ∧ W | 対象 A を満たさない方法論的祖先 (確率近似の適応窓) |
| `B5-Q4` | T ∧ M | 広い二項 (C の語彙差を拾う。固定窓の adaptive backoff・STM 近傍) |
| `B5-Q5` | T ∧ C | 広い二項 (M の語彙差を拾う) |
| `B5-Q6` | M ∧ C | 広い二項 (対象語を落とし、CC と名乗らない研究を拾う) |
| `B5-Q7` | O ∧ C | 広い二項 (制御出力と窓の側から入る) |
| `B5-Q8` | C ∧ W | 広い二項 (標本数・推定誤差による動的窓を拾う) |
| `B5-Q9` | T ∧ V | 正しさ側から入る経路 |
| `B5-Q10` | T ∧ O | 広い二項 (backoff 語を使わない再試行待ち機構を拾う) |

**`B5-Q4` / `B5-Q9` / `B5-Q10` は C を含まない。** これらは「C を満たす候補を引く枝」ではなく、
**語彙差による偽陰性を拾うための広い近傍枝**である。この区別を実行記録で保つ。

### 3.3 canonical request と展開規則

本文中の `T` などは説明用の略号である。**request bytes は次の展開規則で一意に決まる。**
規則の出力と異なる bytes を持つ catalog は、本文書が登録した catalog ではない。

**展開規則 (すべて決定的):**

1. **語順は §3.1 の列挙順とする。** 辞書順ではない。索引が並べ替えて echo することは
   §5.1 条件 1 の正規化で扱い、送信 bytes の側は §3.1 の順を保つ。
2. **ブロック順は枝 ID の論理式に書いた順とする** (例: `B5-Q1` は T、M、C の順)。
3. **arXiv:** 各語を `abs:"<語>"` とし、ブロック内を ` OR ` で連結して丸括弧で囲む。
   ブロック間を ` AND ` で連結し、末尾に ` AND submittedDate:[199101010000 TO 202612312359]`
   を足す。この文字列を UTF-8 の percent encoding で符号化する
   (符号化しない文字は `A-Z a-z 0-9 - _ . ~` のみ。空白は `%20`、`"` は `%22`、
   `(` は `%28`、`)` は `%29`、`:` は `%3A`、`[` は `%5B`、`]` は `%5D`)。
4. **OpenAlex:** 各語をそのまま (引用符なし) 用い、ブロック内を ` OR `、ブロック間を ` AND ` で
   連結し、各ブロックを丸括弧で囲む。`filter` の値として
   `title_and_abstract.search:<式>,to_publication_date:2026-12-31` を作り、
   同じ percent encoding 規則で符号化する (`,` は filter の区切りなので符号化しない)。
5. **DBLP:** 二項組合せ `(語X, 語Y)` の出力を `<語X>%20<語Y>` とする
   (**`q=` は template 側が持つ。規則 5 の出力に `q=` を含めない**)。
   語内の空白も `%20` とし、ハイフンはそのまま送る (DBLP 側の正規化は §3.5 の期待 echo で扱う)。
6. **parameter の順序は下の template の並びのまま**とし、並べ替えない。
7. **query ID は `<枝 ID>@<索引>` とし、DBLP の直積は
   `<枝 ID>@dblp/<語X の ID>-<語Y の ID>` とする。** 語 ID は
   `<ブロック文字><§3.1 の列挙順の 2 桁 0 埋め>` (例: M の第 1 語は `M01`)。

```text
arXiv:
https://export.arxiv.org/api/query?search_query=<規則 3 の出力>&start={POS}&max_results=200

OpenAlex:
https://api.openalex.org/works?filter=<規則 4 の出力>&per-page=200&cursor={CUR}

DBLP:
https://dblp.org/search/publ/api?q=<規則 5 の出力>&format=json&h=100&f={POS}
```

`{POS}` は arXiv が 0 から 200 刻み、DBLP が 0 から 100 刻み。
`{CUR}` は **初回だけ符号化しない literal `*` (`cursor=*`) とし、
2 ページ目以降は前ページの `meta.next_cursor` の値を規則 3 と同じ percent encoding で
符号化して入れる。** `cursor=%2A` を初回に使わない。

**照合可能な例 (`B5-Q10@dblp/T01-O01`):** T の第 1 語 `transaction processing` と
O の第 1 語 `backoff time` の組は
`https://dblp.org/search/publ/api?q=transaction%20processing%20backoff%20time&format=json&h=100&f=0`
になる。

**この規則から生成した機械可読 catalog (1622 主 query + §4 の control) の bytes と SHA-256 は、
§5.3 の registration preflight が seal する。** 本文書はその digest を持たない。
**したがって本文書は、7.7.4 が要求する「完全な query 文字列の保存」を単独では満たさない
部分登録である** (§0、§9)。

### 3.4 arXiv と OpenAlex — 枝ごとに 1 本

arXiv と OpenAlex はブロック内を OR、ブロック間を AND で結んだ 1 本の式で書ける。
したがって **10 枝 = 各索引 10 本**である。

- arXiv は `abs:"語"` を OR で結んだブロックを括弧でくくり、ブロック間を `AND` で結ぶ。
  日付節を `AND submittedDate:[...]` で足す。
- OpenAlex は `title_and_abstract.search` の値に `(語 OR 語) AND (語 OR 語)` を置き、
  `to_publication_date` を filter へ足す。

**期待値は生文字列でなく typed AST とする。** OpenAlex は `meta.x_query.oql` を整形済み文字列で
返すため、空白正規化だけでは安定に一致させられない (軸 1 再改訂 §3 が実測で確定済み)。
判定は §5.1 条件 1 に従う。

**期待 AST の構成規則 (枝ごとに一意に決まる):** 最上位は `join` が `and` のグループとし、
その子を **§3.2 の論理式に書いたブロック順**に並べる。各ブロックの子は `join` が `or` の
グループとし、その子を **§3.1 の列挙順**に並べた `title_and_abstract.search` の filter とする。
最後の子として `to_publication_date` の filter を 1 個置く。
**`get_rows` の期待値は文字列 `"200"` とする** — §3.3 の template が `per-page=200` を送るためで、
値の型は文字列である。**live preflight で型または値が違うと判明したら §5.4 の意味的 amendment とし、
観測値をそのまま期待値へ据えない。**
**この構成規則が 10 枝それぞれの期待 AST を与える。** 比較は D1432 に従い
兄弟要素の順序だけを無視し、多重度・入れ子・`join`・field の有無と型は保存する。

### 3.5 DBLP — 二項の有限直積

DBLP は要旨を索引せず、複数語を句ではなく各語の前方一致連言へ展開する。したがって
arXiv / OpenAlex の OR ブロックを 1 本の request へ写せない。**二項組合せの有限直積を列挙する。**

| 枝 | 直積 | 本数 |
|---|---|---:|
| `B5-Q4` | T × M | 12 × 19 = 228 |
| `B5-Q5` | T × C | 12 × 21 = 252 |
| `B5-Q6` | M × C | 19 × 21 = 399 |
| `B5-Q7` | O × C | 10 × 21 = 210 |
| `B5-Q8` | C × W | 21 × 13 = 273 |
| `B5-Q9` | T × V | 12 × 10 = 120 |
| `B5-Q10` | T × O | 12 × 10 = 120 |
| **計** | | **1602** |

**三項枝 (`B5-Q1` / `B5-Q2` / `B5-Q3`) は DBLP では別取得しない。** 対応する二項枝の
部分集合であり、母集合へ record を追加しないためである。**「DBLP の三項枝の件数を取得した」とは
書かない。** 必要になれば新規 query ID として別途登録する。

**登録する主 query ID の総数: arXiv 10 + OpenAlex 10 + DBLP 1602 = 1622 本。**

**ハイフンを含む語の DBLP 期待 echo を登録時に固定する** (§2.3 の外挿):

| 語 | 期待 echo |
|---|---|
| `back-off` | `back* off*` |
| `finite-difference gradient` | `finite* difference* gradient*` |
| `run-time window selection` | `run* time* window* selection*` |

**登録語に 3 分ハイフンは無い。** 実行時に 3 分ハイフン形の echo が現れたら、
それは登録の誤りであり §5.4 の意味的 amendment とする。

### 3.6 結果を見てから語を足した場合

7.7.4 に従い、**別の query ID とし、理由と時刻を残す。** 既存 ID の結果へ混ぜない。

## 4. positive control と偽陰性対策

### 4.1 演算子・概念ブロックの control (主キーを要しない)

**未知の交点ごとに既知アンカーを要求してはならない。** `B5-Q1` のような交点枝は、
そこに該当する研究が在るかを調べるために引くものであり、完全一致アンカーの存在を必須にすると
調べたい当のものを前提にすることになる (軸 1 事前登録 §6.1)。したがって control を
**演算子と概念ブロック**にも置く。

**operand を結果の前に固定する。** 以下の 2 語を `X` = `backoff`、`Y` = `update interval` とし、
`X` は M の第 1 語、`Y` は C の第 1 語である (§3.1 の列挙順で定める。順序も登録 bytes の一部)。
**実行者が語を選ぶ余地を残さない。**

| control ID | 索引 | 実行式 (operand を束縛済み) | 期待 |
|---|---|---|---|
| `B5-OP-1` | arXiv, OpenAlex | `(X OR Y)` を 1 本、`X` 単独を 1 本、`Y` 単独を 1 本 | `(X OR Y)` の返却集合が `X` 単独と `Y` 単独の返却集合を両方含む |
| `B5-OP-1D` | DBLP | `X` 単独と `Y` 単独の 2 本を取得し、client 側で和を作る | server 側 OR は DBLP に無いため、**client 側の和が定義どおり作れること**を確かめる。`B5-OP-1` を DBLP へ写して server 側 OR を要求してはならない |
| `B5-OP-2` | arXiv, OpenAlex | `(X AND Y)` を 1 本 | `(X AND Y)` の返却集合が `X` 単独と `Y` 単独の返却集合の両方に含まれる |
| `B5-OP-2D` | DBLP | `q=<X の各語> <Y の各語>` の server 側連言 1 本 | 連言の返却集合が `X` 単独と `Y` 単独の返却集合の両方に含まれる |
| `B5-OP-3` | 3 索引 | 上限境界だけを `2023-12-31` へ狭めた `B5-OP-2` / `B5-OP-2D` | 狭めた集合が広い集合の部分集合であり、2024-01-01 以降の日付を持つ record が返らない |
| `B5-OP-4` | DBLP | `B5-OP-1D` の 2 集合を client 側で交差した集合と、`B5-OP-2D` の返却集合 | 両者が一致する |

**control が使う request は次の 14 本である。** ID 規約は `B5-CTL-<役割>@<索引>`。
bytes は §3.3 の展開規則を `X` = `backoff`、`Y` = `update interval` に当てて作る。

| control request ID | 索引 | 式 (展開前) | 使う control |
|---|---|---|---|
| `B5-CTL-X@arxiv` | arXiv | `X` 単独 | `B5-OP-1`, `B5-OP-2` |
| `B5-CTL-Y@arxiv` | arXiv | `Y` 単独 | `B5-OP-1`, `B5-OP-2` |
| `B5-CTL-OR@arxiv` | arXiv | `X OR Y` | `B5-OP-1` |
| `B5-CTL-AND@arxiv` | arXiv | `X AND Y` | `B5-OP-2`, `B5-OP-3` |
| `B5-CTL-AND2023@arxiv` | arXiv | `X AND Y`、上限だけ `2023-12-31` | `B5-OP-3` |
| `B5-CTL-X@openalex` | OpenAlex | `X` 単独 | `B5-OP-1`, `B5-OP-2` |
| `B5-CTL-Y@openalex` | OpenAlex | `Y` 単独 | `B5-OP-1`, `B5-OP-2` |
| `B5-CTL-OR@openalex` | OpenAlex | `X OR Y` | `B5-OP-1` |
| `B5-CTL-AND@openalex` | OpenAlex | `X AND Y` | `B5-OP-2`, `B5-OP-3` |
| `B5-CTL-AND2023@openalex` | OpenAlex | `X AND Y`、上限だけ `2023-12-31` | `B5-OP-3` |
| `B5-CTL-X@dblp` | DBLP | `q=backoff` | `B5-OP-1D`, `B5-OP-2D`, `B5-OP-4` |
| `B5-CTL-Y@dblp` | DBLP | `q=update%20interval` | `B5-OP-1D`, `B5-OP-2D`, `B5-OP-4` |
| `B5-CTL-AND@dblp` | DBLP | `q=backoff%20update%20interval` | `B5-OP-2D`, `B5-OP-3`, `B5-OP-4` |
| `B5-CTL-AND2023@dblp` | DBLP | `B5-CTL-AND@dblp` と同じ `q`、client 側で `year <= 2023` を判定 | `B5-OP-3` |

`B5-OP-1D` と `B5-OP-4` は既存 request の返却集合を client 側で合成するだけで、
**新しい request を出さない。** DBLP の日付上限は client 側判定なので
`B5-CTL-AND2023@dblp` の request bytes は `B5-CTL-AND@dblp` と同一であり、
**同じ bytes を 2 度取得せず 1 回の取得を両 control で使う。**

control query も §5.1 の完走述語 (条件 2・3・5・6) を満たさなければならない。
**control が期待どおりに発火しなければ、その索引のその走行を `未完走` とする。**
記録だけして先へ進んではならない。**登録していない control を実行時に足して
`all(control)` を通してはならない。**

### 4.2 候補 3 群の主キー確定 gate — **本登録の時点で閉じていない**

`2026-09-05-backoff-axis-registration.md` §3 が名指しした候補 3 群を control のアンカー群とする。
**3 群のいずれも DOI / arXiv ID が確定していない。**

**内部の不在の実測 (母集合と走査語を併記する)。**

- **母集合:** 入力 commit `d19d2182fbc324f67b47f600be70136d6503aa59` の tree にある
  `docs/related-work/` 配下の全 tracked file と、submodule commit
  `511c9538e4e8efa54b45cda62e72389ed3b706ec` の `external/ccbench/README.md`
  (blob `cff93802afce1381eef3a370ece436fb3c93eb45`)。
- **走査語 (7 語、大文字小文字を区別しない部分一致):** `cicada` / `SPSA` / `Kiefer` /
  `Wolfowitz` / `stochastic approximation` / `contention manager` / `contention management`。
- **主キーの走査に使った正規表現 (逐語):** `10\.[0-9]{4,}/[^ )\"',]+` /
  `arxiv\.org/abs` / `arXiv:[0-9]{4}\.`。

実測値: `cicada` は母集合全体で **5 file・7 行・8 occurrence**
(`docs/related-work/` の 4 file・5 行・5 occurrence、`external/ccbench/README.md` の
2 行・3 occurrence)。G2 / G3 の語は `2026-09-05-backoff-axis-registration.md` (5 行) と
`claim-survey/README.md` (1 行) にしか現れず、いずれも「書誌未確定」と明記されている。
**上記 7 語のいずれかを含む行のうち、上記 3 正規表現のいずれかに当たる行は 0 行である。**
`external/ccbench/README.md` が持つ DOI は CCBench 自身の論文のもので、`cicada` を含む行には無い。

**したがって、この母集合とこの走査語の範囲では、候補 3 群の主キーを固定できない。**
**この文は「我々がまだ調べていない」ことも意味する。世界の不在の証拠にはならない。**
**走査語を落とした短縮形を書いてはならない。**

7.7.6 は「名称で引かない。主キーは arXiv ID または DOI とし、旧題・新題・略称・改名前後の
システム名を同じ alias レコードに束ねる」と要求する。**したがって名称を control の主キーにできない。**

| slot | 群 | 確定後に包含を要求する枝 |
|---|---|---|
| `G1-CICADA` | Cicada 原論文 | arXiv / OpenAlex: `B5-Q4` または `B5-Q10`。DBLP: 対応する二項直積の和 |
| `G2-SA` | 確率近似の適応 step・適応窓 | arXiv / OpenAlex: `B5-Q3` / `B5-Q6` / `B5-Q7` / `B5-Q8` の和。DBLP: 対応する二項直積の和 |
| `G3-STM` | STM の適応 contention manager | arXiv / OpenAlex: `B5-Q4` / `B5-Q5` / `B5-Q10` の和。DBLP: 対応する二項直積の和 |

gate が要求するもの:

1. **各群について、主キー (DOI または arXiv ID)、著者、題名、版を一次書誌資料で相互確認し、
   新しい日付の凍結物へ locator つきで固定する。** 名称・著者・venue は同定候補を見つける
   手掛かりにだけ使ってよい。
2. **`G2-SA` と `G3-STM` は単一の work ではなく群である。** 代表を結果を見てから選んではならない。
   **有限な anchor 集合そのもの**を、結果を見る前に凍結する。
3. **3 索引それぞれについて、固定した主キーで ID lookup が到達することを実行前に確かめる。**
   到達しない索引があればその事実を記録し、**黙って母集合から外さない。**
   ID lookup は収録の確認であって control ではない (§4.3)。
   **1 件でも ID lookup が不達なら、当該索引のその走行と軸全体を `未完走` とし、
   当該 slot は未配置のままとする。** 不達の索引を §4.3 の control の適用対象から
   外して論理積を通してはならない — それは不達索引を実質的に母集合から外すことである。
4. **1 群でも主キーを固定できなければ、その群の control は「未配置」である。**
   未配置がある限り、軸 B5 の走行を開始してはならず、`RW3` を名乗らない。
   **演算子 control (§4.1) を代替にしてはならない** — 演算子 control は特定のアンカーが
   主 query の和集合に含まれることを検査しないためである。

**本登録の時点で 3 slot すべてが未配置である。** 主キーの確定は本文書を書き換えずに、
新しい日付の後継凍結物で行う (D1208)。

### 4.3 anchor 包含 control

ID lookup で到達できた主キーが、**追加の名称 query ではなく、§4.2 の表が指す
登録済み主 query の和集合に含まれること**を control とする。
**適用対象の索引で包含に失敗したら、その索引のその走行を `未完走` とする。**

### 4.4 control の通過は根拠にならない (D351)

**D351 は「gate の通過を根拠にしてはならない」と裁定している** — 陽性対照の hit を残したまま
通常形式の hit を落とす式が書けるからである。したがって次を課す。

> **感度監査:** §4.5 の補助経路で得た候補も全件を台帳へ入れる。
> **§1 の包含条件を満たす候補が主 query の和集合に無ければ、その走行を無効とする。**

**これは構造的証明ではなく、有限の感度監査である。** D384 が言うとおり有限観測は
普遍性を含意しない。文献検索には、コード検索の厳格 parser に相当する
「安価側と高価側が同じ意味論を通る」構造が無いので、根拠を構造的制約に置けない。
**この限界を落として `RW3` を語ってはならない。**

### 4.5 補助探索の有限化

7.7.6 は引用の前方・後方探索、著者名、venue 年次一覧の併用を要求する。
**上限内の選択順序も固定する** — 上限に達した場合は主キーの辞書順昇順で先頭から採り、
関連度順も乱数も使わない。

| 経路 | 起点 | 索引 | 上限 |
|---|---|---|---|
| 後方引用 (参考文献) | §4.2 で確定した全 anchor | OpenAlex `referenced_works` | 1 hop、全件 |
| 前方引用 (被引用) | 同上 | OpenAlex `cites` filter | 1 hop、1 起点あたり最大 200 件 |
| 著者 | 同 anchor の第一著者と最終著者 | OpenAlex `author.id` filter | 著者あたり最大 100 件 |
| venue 年次一覧 | 下記 8 venue | DBLP の venue API | 1993〜2026 年 (34 暦年)、venue × 年あたり全件 |

登録する venue (8 件、有限列挙): `SIGMOD` / `PVLDB` / `ICDE` / `EDBT` /
`PPoPP` / `SPAA` / `PODC` / `DISC`。**venue × 年 = 8 × 34 = 272 stream。**
下限を 1993 年に置くのは、STM の系譜が 1990 年代前半に始まるためである
(軸 1 の 2015 年下限をそのまま使うと `G3-STM` の系譜を構造的に落とす)。

**途中で hop 数・起点・年範囲・venue・上限を増やしてはならない。**
増やす場合は §5.4 の amendment に従う。

**補助探索の完走述語:** 各経路の各 stream (起点 1 件 × 経路 1 本、または venue × 年 1 組) は、
§5.1 の条件 2 (連続性)・条件 3 (実要素数)・条件 5 (総数一致)・条件 6 (正常終端) を満たしたときだけ
`完走` とする。上限で打ち切った stream は、**打ち切りを明示した `完走` とする** —
上限そのものは結果を見る前に固定されており、上限内の選択順序も固定されているためである。
ページ欠落・総件数フィールド不在・正常終端の不成立は、その stream を `未完走` とし、
軸全体も `未完走` とする。**stream ID・request template・ページング規則は、
anchor に依存する 3 経路については §4.2 の gate が閉じた後の後継凍結物が確定する。**
venue 年次一覧の 272 stream の request template だけは本文書の登録範囲であり、次で固定する。

```text
https://dblp.org/search/publ/api?q=venue%3A<venue>%3A%20year%3A<year>%3A&format=json&h=100&f={POS}
```

stream ID は `B5-AUX-VENUE@dblp/<venue>-<year>`。`<venue>` は §4.5 の 8 件を上表の綴りのまま、
`<year>` は 1993 から 2026 までの 4 桁。`{POS}` は 0 から 100 刻み。
**この `venue:` / `year:` の構文は、射影した入力の実測に含まれていない。**
§2.3 と同じく登録値であって観測値ではなく、live preflight で構文が異なると判明したら
§5.4 の意味的 amendment とする。**preflight の観測をそのまま期待値に据えない。**

**§4.2 の gate が閉じるまで、引用探索と著者探索の起点は確定しない。**
したがって補助探索 catalog は本登録の時点で未完成であり、これも実行を認可しない理由である。
venue 年次一覧の 272 stream だけは anchor に依存しないため、本文書で確定している。

## 5. 完走述語、停止条件、amendment

### 5.1 query ごとの完走述語

各 query ID について、次の全部が成立したときに限りその query を `完走` とする。
軸 1 事前登録 §7 の 6 条件を軸 B5 へ当てたものである。**継承と置換の内訳を明示する。**

- **逐語で継承:** 条件 1 の arXiv / DBLP 節、条件 2、条件 6、および「6 条件を満たしても
  全件取得にならない場合がある」の 2 つの緩和策。
- **置換:** 条件 1 の OpenAlex 節は `2026-09-02-axis1-search-amendment.md` §3 に従う。
  条件 3 は 7.7.4 の実要素数の定義に従い、索引別に書き下す (軸 1 の当該文は
  `meta.per_page` を最終ページの実要素数と突き合わせる形になっており、
  そのままでは正常な部分ページが必ず `否` になる)。条件 4・5 は D1207 と 7.7.5 に従い、
  横断主キーでなく**索引固有 work ID** で数える形へ置き換える。
- **受理集合の向き (来歴として明示する):** 置換はいずれも規則の正本 (7.7.4 / 7.7.5) と
  それを解いた裁定 (D1207、D1432) の側へ寄せたものである。軸 1 の旧述語と比べたとき、
  **受理集合を広げる置換が 3 つある。**
  - 条件 4・5 を索引固有 work ID で数える置換は、同じ横断主キーへ写る別 work ID を
    落とさなくなるぶん**広い** (D1207 が明示的に意図した変更である)。
  - 条件 1 の OpenAlex 節は、兄弟要素の順序だけ**広い** (D1432 の置換の射程そのもの)。
  - 条件 3 の索引別の書き下しは、軸 1 の当該文が正常な最終ページを必ず `否` にする
    書き方だったのを 7.7.4 の定義へ戻したものであり、**そのぶん広い。**

  **これら 3 点は緩和である。隠さずここに書く。** それ以外の条件は軸 1 と同じか厳しい。
  **本文書は、正本と裁定が定めていない緩和を 1 つも入れていない。**

1. **解釈照合:** 送信した request と、索引が返した解釈後クエリが §3 の登録値と一致する。
   **比較は正規化後に行う** — 連続空白を 1 個へ、URL エンコードを復号、arXiv の
   `submittedDate` の角括弧と二重引用符の差だけを許容する。**それ以外の差異は不一致とする。**
   この正規化規則は arXiv と DBLP に当てる。**OpenAlex は
   `docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md` (blob
   `6eb3150406fa99720d6690f710ea6da0f5de8089`) の「§3. 完走述語 — 条件 1 の OpenAlex 節を置き換える」
   が定める `meta.x_query.oqo` の順序非依存な構造比較を、軸 B5 の応答へそのまま適用する。**
   多重度・入れ子の境界と深さ・`join` の値・field の有無と型・`get_rows` を保存し、
   差があれば `否` とする。`and` / `or` 以外の `join`、登録していない key、想定外の型、
   同一 object 内の重複 key は fail-closed で `否` とする。
   `meta.x_query.oql` の生文字列は証拠として保存するが判定に使わない。
2. **連続性:** arXiv は `startIndex` が 0 から `max_results` 刻みで欠落なく連続し、
   OpenAlex は cursor が前ページの `next_cursor` と一致して連鎖し、
   DBLP は `@first` が 0 から 100 刻みで連続する。**全ページの位置値を保存する。**
3. **宣言と実数の一致:** **実要素数**は arXiv=`feed/entry` の個数、
   OpenAlex=`results` の個数、DBLP=`result/hits/hit` の個数で数える。
   **request 件数をこだまする `itemsPerPage` / `meta.per_page` / `@sent` を
   実要素数として使わない** (7.7.4)。判定は 7.7.4 に従い次の 2 つに分ける。
   - **非最終ページ:** 実要素数が要求件数 (arXiv `max_results=200` /
     OpenAlex `per-page=200` / DBLP `h=100`) と一致する。
   - **最終ページ:** `位置 + 実要素数 == 索引が宣言した総件数` に到達する。
     **最終ページで宣言 page size と実要素数の一致を要求しない** — この 3 索引の宣言
     page size は要求件数のこだまであり、正常な部分ページで必ず食い違うためである。

   宣言 page size は全ページ分を証拠として保存するが、実要素数の代用にしない。
4. **主キー重複なし:** 索引固有 work ID が、ページ内・ページ間で重複しない。
   **重複 occurrence 自体は record 台帳へ残す** (7.7.5)。
5. **総数一致:** unique record 数が、索引が返した総件数フィールドの値と一致する。
   OpenAlex は cursor 終端までの distinct `results[].id` を `meta.count` と照合する (7.7.4)。
   **総件数がページ間で変わった場合は不一致とし、その query を再走する。**
   **再走は 1 query あたり 1 回までとする。** 再走でも総件数がページ間で変われば、
   その query を `未完走` とし、軸全体も `未完走` とする。**再走を連鎖させない。**
6. **正常終端:** 最終ページの HTTP status が 200、content type が期待どおり、
   最終 URL が要求 URL と同一ホストであり、**総件数フィールドが存在する。**
   HTTP status・content type・最終 URL・応答 byte 数を全ページ分保存する。

**6 条件を全部満たしても全件取得にならない場合がある。** 同数の入れ替えは検出できず、
3 索引とも snapshot token を提供しないので構造的に排除できない。登録する緩和策は次の 2 つで、
どちらも有限の監査であって証明ではない。

- 全ページの応答証拠 (位置値・宣言件数・実要素数・主キー列・HTTP status) を保存する。
- **複数窓にまたがった枝は、独立した連続 2 走の主キー集合 digest が一致することを要求する。**
  一致しなければ、その枝は観測期間を明示した別走行として扱い `完走` にしない。

**0 件そのものは走行無効の理由にしない。** 正しい query が真に空集合を返すこともある。

**軸 1 の未解決 (U11、条件 4 / 5 の追認) は「状態」としては継承しない。**
軸 B5 は上記の**厳しい述語そのもの**を自分の応答へ適用する。軸 1 側で述語が緩む裁定が出ても、
軸 B5 は自動では追随せず、追随するなら §5.4 の amendment を要する。
**本文書は既存の条件へ免除を与えない。**

### 5.2 軸 B5 が `RW3` を名乗れる条件

次の**論理積**が成立したときだけである。部分積ではない。

```text
all(arXiv の 10 本が完走)
AND all(OpenAlex の 10 本が完走)
AND all(DBLP の 1602 本が完走)
AND all(§4.1 の演算子 control が発火)
AND §4.2 の主キー未配置 slot == 0
AND all(§4.3 の anchor 包含 control が発火)
AND all(§4.5 の補助探索が完走)
AND §4.4 の感度監査が無効化しない
AND 全 record に §1 の A/B/C/D 判定と判定語彙が付いている
AND 未解決の `要裁定` == 0
```

**最後の 1 行を落としてはならない。** `要裁定` を残したまま論理積が通ると、
一次資料が足りないだけの候補を抱えたまま限定付きの未検出を受理してしまう。
**`要裁定` を不在側へ倒すことは 7.7.5 が禁じている。**

**`RW3` に達しても、無限定の「先行なし」「世界初」「系譜の何本目」は使えない** (7.7.3)。
完走で得られるのは、母集合と cutoff を併記した限定付きの未検出を人間の最終裁定へ
提出する資格だけである。

### 5.3 停止条件と preflight (結果を見る前に固定する)

- **本検索の停止条件:** §3.5 の 1622 本と §4 の control・補助探索をすべて完走させたら終わり。
  索引順、query ID の辞書順に一度だけ処理する。**枝を足さない。**
  **「新しい候補が出る間だけ続ける」型の停止条件を禁じる。**
- **再試行上限:** 1 request あたり 3 回 (バックオフ 3→6→12 秒)。超えたらその走行は `未完走`。
- **予算切れ・429・503・通信失敗・空ボディ・総件数フィールドの不在・ページング欠落・
  再試行上限到達・control 不発は、いずれも該当 query を `未完走` とし、軸全体も `未完走` とする。**
  完走した枝だけを取り出して成熟度を名乗ってはならない。
  **枝を削って予算に合わせない。**
- **窓をまたぐ実行:** 7.7.8 が要求する機械可読 checkpoint に従う (D1183)。
  ここへ機構を再記述しない。
- **preflight は 2 段に分ける。**
  - **registration preflight (network-zero):** query catalog、canonical template、parser と
    fixture、schema、実行器の bytes を束縛して seal する。外部 request を出さない。
  - **live preflight:** 固定済み request の現在の構文・echo・availability・総件数・page 数・
    rate limit を観測する。**その応答を本走の page 0 として再利用しない。**
    **観測結果を期待値に据えない** (§2.3)。

### 5.4 非意味的修繕と意味的 amendment の境界

- **非意味的修繕:** **正規化 request が同一である**変更だけを指す。正規化 request は
  endpoint・検索フィールド・filter 本体・sort・page size・位置パラメータの遷移規則・
  取得フィールドの射影からなる。**解釈後クエリの一致だけを根拠にしてはならない** —
  DBLP の `result.query` は `h` と `f` を含まないため、ページング条件を変えても echo は
  同じままである。
- **意味的 amendment:** それ以外すべて。語・ブロック所属・枝・cutoff・検索フィールド・
  control anchor・補助探索の範囲・完走述語の変更が該当する。旧走行を `未完走` に固定し、
  **新しい日付の amendment 文書・新しい query ID・全枝の再実行・独立レビュー**を要求する
  (D1207)。**旧結果を見た後の改訂であることを amendment に明記する。**
  旧 ID の応答を後継 ID の preflight や本走へ再利用しない。

## 6. 母集合の外 (網羅を保証しない)

7.7.4 の列挙をそのまま保持する。**この一覧を成果物から落としてはならない。**

> SIGMOD / PVLDB / OSDI / SOSP などの venue 本体の年次一覧、ACM Digital Library、書籍、
> 技術報告、学位論文、非英語文献、索引化されていない実装・アーティファクト。

**venue 年次一覧は §4.5 で補助経路として引くが、それは網羅の保証にならない** —
対象 venue と年範囲を有限に固定しているためである。母集合の外であることは変わらない。

本文書はこれに次を足す。

- **`2026-12-31` より後の日付を持つ record** (§2.2 の上限境界で 3 索引から落ちる)。
- **取得時点で索引に未収録だった、cutoff 内の日付を持つ record。**
- **arXiv / OpenAlex の検索対象フィールドの外にだけ語がある本文。**
- **DBLP の要旨と本文** — DBLP は要旨を索引しないので、DBLP の枝は書誌・題名にしか当たらない。
- **DBLP の三項枝** (§3.5 で別取得しないと決めた `B5-Q1` / `B5-Q2` / `B5-Q3`)。
- **本文書が登録しなかった概念語・別綴り・数式記号だけで表現された窓や刻みの規則。**
  §3.1 の語列は有限であり、語を変えれば結果は変わりうる。
- **source code・コメント・パッチにだけ存在する適応 backoff 実装。**
- **特許、標準文書、ベンダー文書、blog、未刊行の workshop material。**
- **§4.5 が固定した引用 hop 数・著者上限・venue・年範囲の外。**

**「主キーが未確定の候補群」をここへ書かない。** 7.7.4 の「全件」は
**事前登録した検索式群が返した全レコード**を指す。登録 query が返した record は、
DOI / arXiv ID へ同定できなくても索引固有 work ID で母集合に留め、`要裁定` とする (7.7.5、D1207)。
未確定であるのは §4.2 の control 側であって、母集合ではない。

## 7. 実行の記録は別の凍結物が持つ

本文書は件数・応答・判定値を 1 つも持たない。実行記録は新しい日付の凍結物が持ち、
少なくとも次の型の field を保存する (値はここに書かない)。

- query ID、送信 request の bytes と SHA-256、解釈後クエリ、全ページの位置値・宣言件数・実要素数
- HTTP status、content type、最終 URL、応答 byte 数、response header、entity body の SHA-256
- 索引固有 work ID の列 (重複 occurrence を含む)、総件数フィールドの値
- **work-family 層:** 異なる索引固有 work ID が同じ横断主キー (DOI / arXiv ID) へ
  正規化された場合も、**record を 1 件も消さない。** 衝突は work-family 層へ送り、
  **共有識別子などの独立した証拠でだけ統合する。題名一致だけでは統合しない** (7.7.5、D1207)。
  統合したときは、統合の根拠となった証拠の locator を残す。
  **統合によって `要裁定` を消してはならない** — 消せば §5.2 の「未解決の `要裁定` == 0」が
  不当に成立する
- §5.1 の 6 条件それぞれの `可` / `否`、query ごとの `完走` / `未完走` と理由コード
- control ID ごとの発火・不発、感度監査の結果
- 候補ごとの A/B/C/D の充足記録、強さ、極性、判定語彙、一次資料の locator と証拠階層
- 生証拠の所在 (`output/insights/` 配下)

## 8. 登録前に見えていたもの (事前知識の開示)

**これは完全な pre-result 登録ではない。** 登録者が本登録の前に目にしていたものを開示する。

- `2026-09-05-backoff-axis-registration.md` の内部の不在の実測 (直接接地 0 件、近傍 1 件) と、
  候補 3 群の名称・想定される強さ。
- 軸 1 と軸 3 の事前登録・改訂・実行記録の**構造** (完走述語、control 設計、停止条件、
  母集合の外)。および軸 1 が `未完走` で `RW1` に留まっている状態。
- `2026-08-27-axis3-index-measurements.md` の 3 索引の構文実測 (別の語によるもの)。
- `docs/paper-story-backoff/2026-09-05.md` の B1〜B6 と、B6 が未取得であること。

**軸 B5 の検索結果は 1 件も見ていない。** 本 wave で外部 request を出していないためである。

## 9. この登録自身の限界

- **本検索、live preflight、候補判定のいずれも実行していない。** 件数を 1 つも持たない。
- **軸 B5 は `RW0` のままである。** 本文書は世界の不在も、B6 の新規性も支持しない。
- **本文書は部分登録である。** §0 が挙げた 3 つ (候補主キー未確定、catalog の seal 未了、
  引用・著者経路の起点未確定) が残っており、7.7.4 の事前登録を単独では満たさない。
- **§4.2 の主キー確定 gate が 3 slot とも未配置である。**
  したがって本文書は 7.7.6 の positive control を配置したとは主張せず、実行を認可しない。
- **§3 の期待 echo と AST は 2026-08-27 の別語での構文実測からの外挿**であり、
  2026-09-07 時点の live 意味論は未確認である。
- **有限な英語語彙による登録**であり、同義語閉包でも全文検索でも非英語検索でもない。
- **索引ごとに検索フィールド・stemming・前方一致が異なる。** 同じ語列でも返却集合は異なる。
- **共有暦境界は work 単位で一様でない。** 取得時点の索引状態も固定 snapshot ではない。
- **D1206 の代替来歴は取得時点の来歴であって、API 版や wire 全体の同一性ではない。**
- **positive control と感度監査は有限の偽陰性監査であって、完全性の証明ではない** (D351、D384)。
- **`RW4` に達しても無限定の「先行なし」「世界初」は認可されない** (7.7.3)。
- **§4.2 の内部の不在の実測は、§4.2 が列挙した母集合と、そこに逐語で書いた走査語 7 語および
  主キー正規表現 3 本の範囲**に限る。repo 全体・世界の不在を主張するものではない。
