# 2026-08-27 — 軸 1 の文献検索 事前登録 (凍結)

- **作成日:** 2026-08-27
- **入力 commit:** `9ebd340b` (本 wave の base)
- **入力 digest:** 下記 input path 群の内容は入力 commit `9ebd340b` の blob そのものである。
  索引の実測値だけは repo の外にあり、endpoint・取得日・観測した field 名で束縛する。
- **入力 path:** `docs/related-work/README.md` の 7.6 と 7.7 /
  `docs/related-work/claim-survey/2026-08-26-inventory.md` /
  `docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` /
  `docs/related-work/literature-map/README.md` / `docs/decisions.md` の D350・D351・D384
- **文献 cutoff:** 本文書が定義する。§2 を見よ。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」

> **凍結物である。**
> **この文書に検索結果を書き戻してはならない。** 実行の記録は別の日付の凍結物が持つ (§10)。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

## 0.0 改訂の記録 — この文書は land 前に 1 度訂正されている

**初版は同じ wave の commit `e73590598` である。その版は local main へ着地していない。**
段 6 の敵対レビューが「そのままでは実行契約に使えない」と判定し、**land 前に訂正した。**
訂正した点は §13 に全部挙げる。**どちらの版でも本検索は 1 本も実行していない**ので、
実行記録との食い違いは生じない。

レビューは「上書きせず新しい日付で supersede せよ」と勧めたが採らなかった。同じ日付で 2 つの
契約が並ぶと、どちらが有効かが読者に分からなくなるためである。訂正前後の差分は git 履歴に残る。

---

## 0. この文書は何であって、何でないか

**これは登録であって実行ではない。** 本文書は軸 1 について、7.7.4 が要求する母集合定義・索引・
検索式・cutoff を、**検索結果を見る前に**固定したものである。

**本文書は軸 1 の成熟度を動かさない。軸 1 は `RW1` のままである。**
7.7.3 の `RW2` 以上は「query を実行し、全ページ・総件数・全候補判定が再現可能である」ことを
条件とする。本文書は 1 本も本検索を実行していない。

**本文書は世界の不在を一切作らない。** 既存の世界側の不在の文
(`docs/paper-story/2026-08-26.md` §3 の 1、`docs/related-work/README.md` 7.6 の空白域) を
支持も強化もしない。それらを引くときは 7.7.3 の `RW1` が許す逐語引用に限り、
出典節・掃引日 (2026-07-10)・監査前データである旨を同じ場所に置く。

**本文書が実測したのは索引の生死と構文だけである** — 総件数フィールドが実在するか、
日付境界とページングと論理演算子が機能するか。§4 の値はすべてその範囲の観測である。

## 1. 軸 1 と分類契約

軸 1 = `docs/paper-story/2026-08-26.md` の §3 の 1「対象の空白」。

分類は `2026-08-26-inventory.md` の pilot が定めたものをそのまま使う。**本文書は規則を変えない**
(変えると同 pilot の 29 行と比較できなくなる)。

- **包含条件:** (A) 論文の対象が並行性制御である / (B) 設計・アクション空間そのものをコードで
  生成または拡張する / (C) ワークロード条件づけがある / (D) 正しさ検証器をループ内に持つ。
- **判定規則:** A✓ → `直接接地`。A✗ かつ B✓ → `部分接地`。A✗ かつ B✗ → `除外` (理由コードつき)。
  C と D は gate ではなく記録する属性である。
- **判定語彙:** `検出` / `近傍` / `除外` / `要裁定` / `未完走`。
  **`要裁定` を不在側へ倒さない。**
- **極性:** `競合` / `方法論的祖先` / `外部補強` / `反面教師` / `正しさ側の道具`。

**A の読み方は「主題領域」であって「成果物の種類」ではない。** これは本文書が新しく決めたことでは
なく、pilot が `1905.08406` (成果物は判定手続きであって CC 機構ではない) を A✓ と裁定した時点で
既に採られている読みである。同じ読みは `2026-08-27-axis1-adjudication-3.md` でも使われ、
その記録は同じ読みを一様に当てたときに再監査が要る行も名指ししている。

## 2. cutoff — 索引固有の日付欄へ共有の暦境界を当てる

**「同一 cutoff」を日単位で 3 索引に課すことはできない。** DBLP には日付の範囲指定が無く、
年 facet か record の `year` field しか無い (§4)。日単位を要求したままでは `RW3` に到達できない。

そこで母集合の時間境界を次のとおり定義する。

> **上限境界 = 暦年境界 2026-12-31。** 各索引は自分の日付欄にこの同じ暦境界を当てる。
> - arXiv: `submittedDate` が `199101010000` 以上 `202612312359` 以下
>   (下限は arXiv の開設月 1991-08 より前に置いた閉区間であり、実質的に下限なしである。
>   開いた下限の構文は未実測なので登録しない)。
> - OpenAlex: `to_publication_date=2026-12-31`。下限は置かない。
> - DBLP: **年 facet を使わず全年を取得し、record の `year` field が 2026 以下であることを
>   client 側で判定する** (§3.5)。`year` を持たない record は捨てず `要裁定` とする。
>
> **上限境界が落とすのは、その暦境界より後の日付を持つレコードだけである。**
> 取得日 (2026-08-27) より後で 2026-12-31 以前の日付を持つレコード (例: 2026-09 付) は
> 境界の内側であり、取得の瞬間に索引へ存在すれば母集合に入る。

**この境界は work 単位で一様ではない。** 同じ研究が arXiv で 2026、OpenAlex または DBLP で 2027 と
記録されている場合、arXiv 側の record だけが残り、他 2 索引の record は落ちる。
**和集合は record の和なので候補としては残るが、record 数は索引間で一致しない。**
この非一様性は §5 の work-family 台帳で可視化し、隠さない。

**母集合は「同じ概念の検索結果」ではなく、「索引別に凍結した操作的 query の返却集合の和」である。**
3 索引は語の意味論が違い (§4)、同じ語を渡しても同じ集合にはならない。
**この文書および下流の成果物は「同一 cutoff の 3 索引の和集合」という短縮を使ってはならない。**
使う定型は **「索引固有の日付欄へ共有の暦境界を当てた登録取得集合の和」** とする。

## 3. 概念ブロックと query catalog

### 3.1 概念ブロック

軸 1 を 5 つの概念ブロックへ分解する。各ブロックは語の選言である。**この語列は有限である。**

- **T (対象、12 語):** `concurrency control` / `transaction processing` / `serializability` /
  `isolation level` / `two-phase locking` / `optimistic concurrency control` /
  `multi-version concurrency control` / `snapshot isolation` / `transactional memory` /
  `lock manager` / `conflict detection` / `OLTP`
- **M (機構、12 語):** `program synthesis` / `automatic generation` / `code generation` /
  `evolutionary search` / `genetic programming` / `large language model` / `LLM agent` /
  `reinforcement learning` / `learned` / `auto-tuning` / `compiler injection` / `superoptimization`
- **O (出力、9 語):** `protocol` / `algorithm` / `policy` / `source code` / `implementation` /
  `intermediate representation` / `action space` / `design space` / `variant`
- **V (正しさ、7 語):** `verifier` / `model checking` / `anomaly detection` /
  `serializability checking` / `invariant` / `proof` / `correctness oracle`
- **W (ワークロード、8 語):** `workload` / `benchmark` / `YCSB` / `TPC-C` / `contention` /
  `read-write ratio` / `skew` / `many-core`

### 3.2 登録する枝

7.7.4 は「狭い積集合だけでなく、語彙差を拾う広い二項組合せも事前に登録する」と要求する。

| 枝 ID | 論理式 | 役割 |
|---|---|---|
| `Q1` | T ∧ M ∧ O | 狭い積集合 (軸 1 の交点そのもの) |
| `Q2` | T ∧ M | 広い二項組合せ (O の語彙差を拾う) |
| `Q3` | T ∧ O | 広い二項組合せ (M の語彙差を拾う) |
| `Q4` | T ∧ V | 正しさ側から入る経路 |
| `Q5` | T ∧ W | ワークロード側から入る経路 |
| `Q6` | M ∧ O ∧ W | 対象語を落として、CC と名乗らない CC 研究を拾う |

### 3.3 arXiv の完全 query (6 本)

endpoint は `https://export.arxiv.org/api/query`。パラメータは `search_query` / `start` /
`max_results`。escaping は HTTP の application/x-www-form-urlencoded (句の二重引用符は
`%22`、空白は `+`、`[` `]` は `%5B` `%5D`) とする。

ブロック文字列を次のとおり定義する。`<TA>` などは以下の展開を指す略号であり、
送信する `search_query` は略号を展開した文字列である。

```
<TA> = (abs:"concurrency control" OR abs:"transaction processing" OR abs:"serializability"
        OR abs:"isolation level" OR abs:"two-phase locking"
        OR abs:"optimistic concurrency control" OR abs:"multi-version concurrency control"
        OR abs:"snapshot isolation" OR abs:"transactional memory" OR abs:"lock manager"
        OR abs:"conflict detection" OR abs:"OLTP")
<MA> = (abs:"program synthesis" OR abs:"automatic generation" OR abs:"code generation"
        OR abs:"evolutionary search" OR abs:"genetic programming"
        OR abs:"large language model" OR abs:"LLM agent" OR abs:"reinforcement learning"
        OR abs:"learned" OR abs:"auto-tuning" OR abs:"compiler injection"
        OR abs:"superoptimization")
<OA> = (abs:"protocol" OR abs:"algorithm" OR abs:"policy" OR abs:"source code"
        OR abs:"implementation" OR abs:"intermediate representation" OR abs:"action space"
        OR abs:"design space" OR abs:"variant")
<VA> = (abs:"verifier" OR abs:"model checking" OR abs:"anomaly detection"
        OR abs:"serializability checking" OR abs:"invariant" OR abs:"proof"
        OR abs:"correctness oracle")
<WA> = (abs:"workload" OR abs:"benchmark" OR abs:"YCSB" OR abs:"TPC-C" OR abs:"contention"
        OR abs:"read-write ratio" OR abs:"skew" OR abs:"many-core")
<DA> = submittedDate:[199101010000 TO 202612312359]
```

| query ID | `search_query` |
|---|---|
| `AX1-Q1@arxiv` | `<TA> AND <MA> AND <OA> AND <DA>` |
| `AX1-Q2@arxiv` | `<TA> AND <MA> AND <DA>` |
| `AX1-Q3@arxiv` | `<TA> AND <OA> AND <DA>` |
| `AX1-Q4@arxiv` | `<TA> AND <VA> AND <DA>` |
| `AX1-Q5@arxiv` | `<TA> AND <WA> AND <DA>` |
| `AX1-Q6@arxiv` | `<MA> AND <OA> AND <WA> AND <DA>` |

**期待 echo:** arXiv は `<feed><title>` に `arXiv Query: search_query=<送信文字列>&id_list=&start=<S>&max_results=<N>`
を返す。**ただし `submittedDate:[A TO B]` は `submittedDate:"A TO B"` へ書き換えられる** (実測)。
したがって期待 echo は、送信文字列のこの 1 箇所だけを置換した文字列とする。
**それ以外の差異が出た走行は無効である。**

ページングは `start` を 0 から `max_results=200` 刻みで進める。

### 3.4 OpenAlex の完全 query (6 本)

endpoint は `https://api.openalex.org/works`。パラメータは `filter` / `per-page` / `cursor`。
escaping は同じ規約。ブロック文字列を次のとおり定義する。

```
<TO> = ("concurrency control" OR "transaction processing" OR "serializability"
        OR "isolation level" OR "two-phase locking" OR "optimistic concurrency control"
        OR "multi-version concurrency control" OR "snapshot isolation"
        OR "transactional memory" OR "lock manager" OR "conflict detection" OR "OLTP")
<MO>, <OO>, <VO>, <WO> = 同様に M / O / V / W の語を OR で並べたもの (語は §3.1 と同一)
<DO> = ,to_publication_date:2026-12-31
```

| query ID | `filter` |
|---|---|
| `AX1-Q1@openalex` | `title_and_abstract.search:<TO> AND <MO> AND <OO>` + `<DO>` |
| `AX1-Q2@openalex` | `title_and_abstract.search:<TO> AND <MO>` + `<DO>` |
| `AX1-Q3@openalex` | `title_and_abstract.search:<TO> AND <OO>` + `<DO>` |
| `AX1-Q4@openalex` | `title_and_abstract.search:<TO> AND <VO>` + `<DO>` |
| `AX1-Q5@openalex` | `title_and_abstract.search:<TO> AND <WO>` + `<DO>` |
| `AX1-Q6@openalex` | `title_and_abstract.search:<MO> AND <OO> AND <WO>` + `<DO>` |

**期待 echo:** `meta.x_query.oql` が
`works where date <= (2026-12-31) and title/abstract has (<解釈後の論理式>)` を返す。
解釈後の論理式では各語が `stemmed "<語>"` になり、ブロックは `or`、ブロック間は `and` で
結ばれる (実測)。**語の集合・ネスト構造・`stemmed` 指定のいずれかが期待と違えばその走行は無効である。**

ページングは `per-page=200` と `cursor` 連鎖で行う。

### 3.5 DBLP の完全 query (12 本) — 設計が他 2 索引と違う理由

**DBLP は句検索も句の選言も表現できない。** `q="concurrency control"` を送ると引用符が剥がれ
`concurrency* control*` (前方一致の連言) として解釈される (実測)。空白が連言、`|` が選言だが、
`|` は語単位にしか効かないため `(句1 OR 句2)` を 1 本の query で書けない。
**さらに DBLP は要旨を索引していない** (実測)。

したがって DBLP の枝は次のように定義する。

> **`AX1-T01@dblp` 〜 `AX1-T12@dblp`:** T ブロックの 12 語それぞれについて、
> `q=<語>` (年 facet なし)、`format=json`、`h=100`、`f` を 0 から 100 刻み。
> 取得後、record の `year` が 2026 以下のものを残す (§2)。
> **枝 Q1〜Q5 の DBLP 側は、この 12 本の和集合に対する client 側の絞り込みとして定義する** —
> DBLP は題名しか持たないので、M / O / V / W の条件を server 側へ足しても偽陰性が増えるだけである。

**期待 echo:** `result.query` が `<語の各単語に * を付けて空白で連ねた文字列>` を返す。

**`AX1-Q6@dblp` は登録するが実行不能と宣言する。** Q6 は T を含まないため上の和集合で覆えず、
M / O / W の句の選言を DBLP の構文で書く手段が無い。**黙って母集合から外さない** (7.7.4)。
**この宣言的除外を許すかどうかは人間の裁定に委ねる。** 許されるなら Q6 は arXiv と OpenAlex の
2 索引で覆われたことになり `RW3` は到達可能である。許されないなら軸 1 は `未完走` であり
`RW3` に到達しない。**本文書は自分でこの可否を決めない。**

### 3.6 登録した query ID の総数

arXiv 6 + OpenAlex 6 + DBLP 12 = **24 本が実行対象**であり、これに実行不能宣言の
`AX1-Q6@dblp` が 1 本加わる。

### 3.7 結果を見てから語を足した場合

**別の query ID (`AX1-Q<n>b@<索引>`) を新規に起こし、追加の理由と時刻を書く。**
既存 ID の定義を書き換えてはならない。扱いは §8 の amendment 規則に従う。

## 4. 索引の実測 (2026-08-27、計算ノードから直接 HTTP、認証情報なし)

**認証情報を一切送っていない。** API キー、token、email のいずれも送っていない。
OpenAlex の polite pool (`mailto=`) は使わない — ユーザーの email を無関係なサービスへ
送らないためであり、代償は §4.4 のレート制限である。**キーの追加も前払いも行わない。**

### 4.1 総件数フィールドと解釈後クエリの echo

| 索引 | endpoint | 総件数フィールド | 解釈後クエリの echo | 宣言件数 | 位置 |
|---|---|---|---|---|---|
| arXiv | `https://export.arxiv.org/api/query` | `opensearch:totalResults` | `feed>title` | `opensearch:itemsPerPage` | `opensearch:startIndex` |
| OpenAlex | `https://api.openalex.org/works` | `meta.count` | `meta.x_query.oql` | `meta.per_page` | `meta.next_cursor` |
| DBLP | `https://dblp.org/search/publ/api` | `result.hits.@total` | `result.query` | `result.hits.@sent` | `result.hits.@first` |

**3 索引とも解釈後のクエリを応答に含める。** これが §7 の解釈照合を実装可能にしている。
**ただし DBLP の `result.query` は検索語だけを表し、`h` と `f` を含まない** (実測。
`h=50` と `h=1000` で同じ echo が返る)。この非単射性が §8 の修繕境界を狭める理由である。

### 4.2 語の意味論は 3 索引で違う

- arXiv はフィールド前置子で指定した語・句を当てる。括弧と `AND` / `OR` が機能する (実測)。
- OpenAlex はステミングする。括弧と `AND` / `OR` が機能する (実測)。
- DBLP は前方一致へ展開する。**引用符は剥がされ句にならない** (実測)。
  空白が連言、`|` が選言で、選言は語単位にしか効かない。
- **DBLP は要旨を索引していない。** DCDS (`2404.13359`) の要旨にある `recency-sorted` で
  DBLP は 0 件を返す一方、同論文は題名で 1 件引ける (実測)。
  **DBLP の枝が返さないことは、要旨だけに現れる語について何も意味しない。**

### 4.3 ページングと黙った切り詰め

- **arXiv:** `max_results=200` を要求して 200 entry・`itemsPerPage` 200 が返る (要求どおり)。
- **OpenAlex:** `per-page=200` と `cursor=*` が機能し、`meta.next_cursor` が返る。
- **DBLP:** **要求超過を黙って切り詰める。** 同じ query (`@total` 4644) に対し
  `h=50` は `@sent` 50 を返すが、**`h=1000` も `h=1001` も `@sent` 100 を返す。**
  エラーは出ない。1 リクエスト 100 件が実効上限であり、`f` (offset) で送る
  (`h=100&f=100` で `@first` 100 が返り、別の hit 集合になることを確認した)。
  **`@sent` と要求 `h` を毎回突き合わせない限り、切り詰めに気づけない。**

### 4.4 レート制限と予算

- **arXiv:** リクエスト間 3 秒以上、429 は 3→6→12 秒の指数バックオフ
  (`docs/related-work/literature-map/README.md` が正本。今回は再測していない)。
  **`http://` は 301 を返し、リダイレクトを追わないクライアントでは空ボディ = 0 件に見える**
  (同文書の 2026-07-10 の教訓。今回は再測していない)。
- **OpenAlex:** 応答ヘッダが `x-ratelimit-limit: 1000` / `x-ratelimit-credits-used: 10` /
  `x-ratelimit-limit-usd: 0.1` / `x-ratelimit-cost-usd: 0.001` /
  `x-ratelimit-prepaid-remaining-usd: 0` / `x-ratelimit-reset: 27950` (秒) を返す。
  すなわち **1 リクエスト = 10 credit = $0.001 相当、1 窓 (約 7.76 時間) の無償枠が
  1000 credit = $0.1 相当、前払い残高は 0。** キーも前払いも足さない前提では
  **1 窓あたり 100 リクエストが上限**である。
- **DBLP:** 実測で **503 を返した** (本文書の probe 中に 1 度発生し、バックオフ後の再試行で
  200 になった)。2026-07-10 の掃引でもレート制限による空応答で 2 クエリが失敗している
  (`docs/related-work/literature-map/gap-research-2026-07-10.md`)。

### 4.5 既存記述との食い違い (訂正)

`docs/related-work/literature-map/README.md` は「OpenAlex は API キー未設定のため今回未使用」と
書いている。**2026-08-27 の実測では、OpenAlex は API キー無しで 200 と `meta.count` を返す。**
「2026-07-10 に未使用だった」は歴史的事実として正しいが、**その原因説明は現状と合わない。**
litmap は監査前の生データとして書き換えず、訂正は本文書が持つ。

## 5. 和集合、主キー、alias、重複除去

### 5.1 主キーの正規化 (全 record に適用する total な規則)

record ごとに **正規化主キー** を次の順で決める。

1. arXiv ID があれば `arxiv:<id>` (版接尾辞 `vN` は落とす)。
2. 無ければ DOI を正規化して `doi:<値>` — `https://doi.org/` と `http://dx.doi.org/` の前置を
   除去し、**小文字化する。**
   **正規化しないと突き合わせに失敗する** — DBLP は `10.48550/ARXIV.2404.13359`、
   OpenAlex は `https://doi.org/10.48550/arxiv.2404.13359` を返す (実測)。
   `10.48550/arxiv.<id>` の形の DOI は `arxiv:<id>` へ写像し、1 と同一視する。
3. どちらも無ければ `<索引名>:<索引固有 ID>` を主キーとし、
   **`要裁定` として印を付ける** (他索引の record と統合できないため)。

### 5.2 台帳は 2 段にする

- **record 台帳:** 索引が返したレコードを 1 つも落とさずそのまま持つ。完全性はここで数える。
  各 record に正規化主キー、索引名、query ID、ページ番号、索引固有の日付欄の値を持たせる。
- **work-family 台帳:** DOI・arXiv の DOI 欄・DBLP の `ee`・著者・版履歴の複数証拠で
  `work-family-id` を付ける。**共有識別子が無ければ自動統合せず `要裁定` とする。**
  **題名一致だけの重複除去を禁じる** (7.7.6)。
  各 family には、構成 record の索引別日付欄の値と、§2 の境界に対する適格性を残す。

### 5.3 件数の単位

取得完全性は record 数、重複除去後は work-family 数、主張表は研究数で数え、
変換の対応表と未解決 family 数を残す。**単位の違う数を足さない。**

### 5.4 alias

旧題・新題・略称・改名前後を 1 つの alias レコードへ束ねる。既知の実例は `2503.10036` —
`CCaaLF` は v4 で `Modeling Concurrency Control as a Learnable Function` へ改題され
`NeurCC` へ改名された。

## 6. positive control と補助探索

### 6.1 control は演算子と概念ブロックに置く

**未知の交点ごとに既知アンカーを要求してはならない。** Q1 のような交点枝は、そこに該当する
研究が在るかどうかを調べるために引くものである。その枝に完全一致アンカーの存在を必須にすると、
調べたい当のものを前提にすることになり、`RW3` が循環的に到達不能になる。

したがって control は **検索演算子と概念ブロック**に置き、索引別の実行式と期待 hit を対応づける。

| control ID | 索引 | 実行式 | 期待 |
|---|---|---|---|
| `C-OP-1` | 3 索引 | 単一句 (arXiv/OpenAlex) または単一語 (DBLP) で `2404.13359` を狙う | 当該 record が返る |
| `C-OP-2` | arXiv, OpenAlex | 2 句の OR。片方だけを含む既知 record を狙う | 当該 record が返る |
| `C-OP-3` | arXiv, OpenAlex | 2 句の AND。片方だけの既知 record を狙う | 当該 record が返らない |
| `C-OP-4` | 3 索引 | 上限境界を 2023-12-31 へ動かした Q2 相当 | 2024 以降の anchor が返らない |
| `C-BLK-T` | 3 索引 | `<TA>` / `<TO>` / T 12 語の和 | anchor 5 件のうち T を要旨または題名に持つものが返る |
| `C-BLK-M` | arXiv, OpenAlex | `<MA>` / `<MO>` | `2105.10329` と `2503.10036` が返る |
| `C-BLK-O` | arXiv, OpenAlex | `<OA>` / `<OO>` | `2105.10329` が返る |
| `C-BLK-V` | arXiv, OpenAlex | `<VA>` / `<VO>` | `1905.08406` が返る |
| `C-BLK-W` | arXiv, OpenAlex | `<WA>` / `<WO>` | `2009.11558` が返る |

既知アンカー (主キーで指定する): `2105.10329` (Polyjuice) / `2503.10036` (CCaaLF→NeurCC) /
`2603.13906` (ATCC) / `2009.11558` (CCBench) / `2404.13359` (DCDS)。

**まず 3 索引すべてで、この 5 件が主キーで到達できることを実行前に確かめる。**
これは ID lookup であって control ではない。**到達できない索引があれば、その事実を記録し、
母集合から黙って外さない。**

**control が期待どおりに発火しなかった場合、その索引のその走行は `未完走` とする。**
control の失敗を記録だけして先へ進んではならない。

### 6.2 control の通過は根拠にならない (D351)

**D351 は「gate の通過を根拠にしてはならない」と裁定している** — 陽性対照の hit を残したまま
通常形式の hit を落とす式が書けるからである。したがって control に加えて次を課す。

> **感度監査:** §6.3 の補助経路で得た候補も全件を台帳へ入れる。
> **包含条件を満たす候補が主 query の和集合に無ければ、その走行を無効とする。**

**これは構造的証明ではなく、有限の感度監査である。** D384 が言うとおり有限観測は
普遍性を含意しない。文献検索には、コード検索の厳格 parser に相当する「安価側と高価側が
同じ意味論を通る」構造がないので、根拠を構造的制約に置くことができない。
**この限界を落として `RW3` を語ってはならない。**

### 6.3 補助探索の有限化

補助経路は結果を見る前に有限値で固定する。**上限内の選択順序も固定する** — 上限に達した場合は
主キーの辞書順昇順で先頭から採り、乱数も関連度順も使わない。

| 経路 | 起点 | 索引 | 上限 |
|---|---|---|---|
| 後方引用 (参考文献) | §6.1 の既知アンカー 5 件 | OpenAlex `referenced_works` | 1 hop、全件 |
| 前方引用 (被引用) | 同上 | OpenAlex `cites` filter | 1 hop、1 起点あたり最大 200 件 |
| 著者 | 同 5 件の第一著者と最終著者 | OpenAlex `author.id` filter | 著者あたり最大 100 件 |
| venue 年次一覧 | SIGMOD / PVLDB / OSDI / SOSP | DBLP の venue API | 2015〜2026 年、venue×年あたり全件 |

**venue 年次一覧は 7.7.6 が要求する補助経路である。** §9 が言う「母集合の外」は
**網羅を保証しない**という意味であって、補助経路として引かない理由にはならない。
venue 由来の候補は主 query 由来と区別して台帳に入れ、§6.2 の感度監査の入力にする。

**途中で hop 数・起点・年範囲・上限を増やしてはならない。** 増やす場合は §8 の amendment に従う。

## 7. 完走述語 — 「全件取得した」の機械的な定義

各 (query ID) について、次の全部が成立したときに限りその query を `完走` とする。

1. **解釈照合:** 送信した request と、索引が返した解釈後クエリ (§4.1) が、§3.3〜3.5 に
   登録した期待値と一致する。**比較は正規化後に行う** — 連続空白を 1 個へ、
   URL エンコードを復号、arXiv の `submittedDate` の角括弧と二重引用符の差だけを許容する。
   それ以外の差異は不一致とする。
2. **連続性:** arXiv は `startIndex` が 0 から `max_results` 刻みで欠落なく連続し、
   OpenAlex は cursor が前ページの `next_cursor` と一致して連鎖し、
   DBLP は `@first` が 0 から 100 刻みで連続する。**全ページの位置値を保存する。**
3. **宣言と実数の一致:** 各ページについて、要求件数・索引が宣言した件数
   (`itemsPerPage` / `meta.per_page` / `@sent`)・実際の要素数が一致する。
   **最終ページだけは、宣言件数と実要素数が一致し、かつ
   `位置 + 実要素数 == 総件数` であればよい。**
   **DBLP はここで切り詰めを検出する。**
4. **主キー重複なし:** §5.1 の正規化主キーが、ページ内・ページ間で重複しない。
5. **総数一致:** unique record 数が、索引が返した総件数フィールドの値と一致する。
   **総件数がページ間で変わった場合は不一致とし、その枝を再走する。**
6. **正常終端:** 最終ページの HTTP status が 200、content type が期待どおり、
   最終 URL が要求 URL と同一ホストであり、必須要素 (§4.1 の総件数フィールド) が存在する。
   **HTTP status・content type・最終 URL・応答 byte 数を全ページ分保存する。**

**軸 1 が `RW3` を名乗れるのは、登録した全 24 本が `完走` で、§6.1 の control が全部発火し、
§6.2 の感度監査が無効化せず、かつ `AX1-Q6@dblp` の宣言的除外が人間に許されたときだけである。**
論理積であり、部分積ではない。

### 7.1 6 条件を全部満たしても全件取得にならない場合がある

**同数の入れ替えは検出できない。** offset 方式で、開始時の集合が `{a,b,c,d}` で最初のページが
`{a,b}` を返し、ページ間に索引側が `{x,b,y,d}` へ同数で置換され、次の連続 offset が `{y,d}` を
返したとする。解釈 echo は同じ、位置は連続、各ページ 2 件、主キーは重複なし、
unique 数と総件数はともに 4、正常終端である。**しかし取得集合 `{a,b,y,d}` はどちらの
snapshot とも一致せず、開始時の `c` と終了時の `x` を落としている。**

3 索引とも snapshot token を提供しないので、これを構造的に排除することはできない。
**登録する緩和策は次の 2 つで、どちらも有限の監査であって証明ではない。**

- 全ページの応答証拠 (位置値・宣言件数・実要素数・主キー列・HTTP status) を保存する。
- **複数窓にまたがった枝は、独立した連続 2 走の主キー集合 digest が一致することを要求する。**
  一致しなければ、その枝は観測期間を明示した別走行として扱い、`完走` にしない。

**0 件そのものは走行無効の理由にしない。** 正しい query が真に空集合を返すこともあるからである。
誤設定は 1 の解釈照合と §6 の control で検査する。

## 8. 停止条件と amendment (結果を見る前に固定する)

- **本検索の停止条件:** §3.6 の 24 本をすべて完走させたら終わり。枝を足さない。
  **「新しい候補が出る間だけ続ける」型の停止条件を禁じる。**
- **再試行上限:** 1 リクエストあたり 3 回 (バックオフ 3→6→12 秒)。超えたらその走行は `未完走`。
- **予算切れ・429・503・通信失敗・再試行上限到達は、いずれも軸全体を `未完走` にする。**
  完走した枝だけを取り出して軸の成熟度を名乗ってはならない。
  部分結果から書いてよいのは、**完全に完走した単一 query ID についての内部的な取得報告だけ**で、
  そこに不在の表現を置いてはならない。
- **窓をまたぐ実行:** OpenAlex の無償枠は 1 窓 100 リクエストなので、実行は複数窓に分かれうる。
  **preflight を必ず置く** — 各枝の初回応答の総件数から所要リクエスト数を算出し、
  窓単位の実行計画を登録してから本取得に入る。§7.1 の 2 走一致もこの計画に含める。
- **索引スナップショットの不一致:** §7.1 に従う。補えない範囲は限界として記録する。
- **死んだ式の扱い (非意味的修繕と意味的 amendment の境界):**
  - **非意味的修繕:** **正規化 request が同一である**変更だけを指す。正規化 request は
    endpoint・検索フィールド・filter 本体・sort・page size・位置パラメータの遷移規則・
    取得フィールドの射影からなる。**解釈後クエリの一致だけを根拠にしてはならない** —
    DBLP の `result.query` は `h` と `f` を含まないので、ページング条件を変えても
    echo は同じままである (§4.1)。
    ページングの変更は、§7 の条件 2 が定める遷移規則に従うものだけを許す。
  - **意味的 amendment:** それ以外すべて。旧走行を `未完走` に固定し、
    **新しい日付の amendment 文書・新しい query ID・全枝の再実行・独立レビュー**を要求する。
    **旧結果を見た後の改訂であることを amendment に明記する。**

## 9. 母集合の外 (網羅を保証しない)

7.7.4 の列挙をそのまま保持する。**この一覧を成果物から落としてはならない。**

> SIGMOD / PVLDB / OSDI / SOSP などの venue 本体の年次一覧、ACM Digital Library、書籍、
> 技術報告、学位論文、非英語文献、索引化されていない実装・アーティファクト。

**venue 年次一覧は §6.3 で補助経路として引くが、それは網羅の保証にならない** — 対象 venue と
年範囲を有限に固定しているためである。母集合の外であることは変わらない。

本文書はこれに次を足す。

- **2026-12-31 より後の日付を持つレコード** (§2 の上限境界で 3 索引から落ちる)。
- **DBLP の要旨** — DBLP は要旨を索引しないので、DBLP の枝は題名 (と著者・venue) しか当たらない。
- **`AX1-Q6@dblp`** — DBLP の構文では書けないため実行不能と宣言した (§3.5)。可否は人間の裁定。
- **§6.3 の上限を超える引用・著者・venue の探索範囲。**
- **本文書が登録しなかった概念語。** §3.1 の語列は有限であり、語を変えれば結果は変わりうる。

## 10. 実行の記録 (別の凍結物が持つ)

**本文書に実行値を書き戻してはならない。** 実行は新しい日付の凍結物
(`claim-survey/<日付>-axis1-search-execution.md` を想定) が持ち、次を保存する。

**query ID ごと:**

| field | 中身 |
|---|---|
| `query_id` | `AX1-Q<n>[b]@<索引>` または `AX1-T<nn>@dblp` |
| `request` | 送信した完全な request (URL とパラメータ、escaping 込み) |
| `normalized_request` | §8 が定める正規化 request |
| `interpreted_query` | 索引が返した解釈後クエリ |
| `expected_interpreted_query` | §3.3〜3.5 が登録した期待値 |
| `retrieved_at` | 取得の開始日時と終了日時 (UTC と JST) |
| `api_identification` | endpoint と、応答に実在した必須 field 名の一覧 (3 索引とも版番号を返さない) |
| `declared_total` | 索引が返した総件数。ページごとに再取得して変化の有無も残す |
| `pages` | ページごとに 位置値 / 要求件数 / 宣言件数 / 実要素数 / HTTP status / content type / 最終 URL / 応答 byte 数 / 主キー列 |
| `retrieved_unique` | 重複除去前の unique record 数 |
| `primary_key_digest` | unique 主キー集合の digest |
| `second_pass_digest` | §7.1 の 2 走目の digest (複数窓の枝のみ) |
| `completion` | §7 の 6 条件それぞれの成否 |
| `failure` | 429 / 503 / 空ボディ / 予算切れ / 再試行上限 の別 |

**control ごと:** `control_id` / `request` / 期待 / 実際 / 発火の成否。

**record ごと:** 正規化主キー / 索引名 / query ID / ページ番号 / 索引固有の日付欄の値 /
判定 (`検出` / `近傍` / `除外` / `要裁定` / `未完走`) / 除外理由コード / 由来 (主 query か補助経路か)。

**work-family ごと:** `work-family-id` / 構成 record の主キー列 / 統合に使った証拠 /
未解決なら `要裁定`。

**題名だけで除外しない。要旨が取れない・本文確認が要るものは `要裁定` とする。**

## 11. 登録前に親が目にしたもの (事前知識の開示)

**本文書を凍結する前に、親は次を目にした。**
**「本走行の record を見ていない」であって「何も見ていない」ではない。**
語・枝・停止条件はこれらの観測を根拠に変えていないが、**影響経路は存在する。**

1. **arXiv の構文 probe で、狭い積集合に近い形の query の総件数を見た。** 送信したのは
   `(abs:"concurrency control" OR abs:"transaction processing") AND (abs:"program synthesis" OR abs:"large language model") AND submittedDate:[201001010000 TO 202612312359]`
   で、`totalResults` は 10 であった。レコードは見ていない。
   **これは `AX1-Q2@arxiv` の縮小版であり、Q2 の語彙・広さ・予算判断に影響しうる。**
2. **arXiv の日付境界 probe の応答に entry が 1 件含まれており、その arXiv ID
   (`2603.13897`) を目にした。** 題名の断片以上は見ていない。
3. **単一ブロック相当の総件数を見た** — arXiv `all:"concurrency control"` 234、
   OpenAlex `title_and_abstract.search:"concurrency control"` 9464 (2020-01-01〜2026-07-10 では 1740)、
   DBLP `q=concurrency` 4644、DBLP `q="concurrency control"` 1336。
   **これらは T ブロックを含む Q1〜Q5 の広さとページ予算の見積もりに影響しうる。**
4. **登録前に、pilot の 29 件、既知 anchor と alias、および 3 本の一次資料
   (`2404.13359` / `2512.18746` / `2605.22721`) を読んでいる。**
   `2404.13359` は §6.1 の control anchor に採用されている。

**因果的影響がなかったと断定はしない。** 実行する段では、上記を見た後に設計された契約であることを
実行記録へ書く。

## 12. この登録自身の限界

- **本検索を 1 本も実行していない。** 網羅率についても不在についても何も言わない。
- **3 索引とも API の版番号を返さない。** 版の束縛は endpoint と、応答に実在した必須 field 名の
  一覧で代用する。索引の内容は本文書の凍結後に変わりうる。
- **arXiv と DBLP のレート制限・301 の挙動は 2026-07-10 の記録を引いており、
  今回再測していない項目がある** (§4.4 に明記した)。
- **§6.2 の感度監査は有限の監査であって構造的証明ではない** (D384)。
- **§7.1 の同数入れ替えは構造的に排除できない。**
- **概念語は有限である** (§9)。語を変えれば結果は変わる。
- **`AX1-Q6@dblp` は実行不能であり、その可否を本文書は決めない** (§3.5)。
- **本文書は軸 1 だけを登録している。** 軸 2〜5 は登録していない。

## 13. 訂正の内訳 (段 6 敵対レビューの指摘)

初版 (commit `e73590598`) からの変更点である。**いずれも land 前に行った。**

| # | 指摘 | 訂正 |
|---|---|---|
| 1 | 完全な query 文字列が無く、返却集合が一意でない | §3.3〜3.6 で 24 本の完全 query と期待 echo を登録した |
| 2 | 「上限境界が働くのは未来日付だけ」は誤り | §2 を訂正した。落ちるのは暦境界より後の日付だけであり、取得日より後でも境界内なら残る |
| 3 | 境界は work 単位で一様ではない | §2 に非一様性と、それを work-family 台帳で可視化する規則を足した |
| 4 | DBLP の `year <= 2026` の実行方法が無い | §3.5 で年 facet を捨て、全年取得 + record の `year` による client 側判定に変えた |
| 5 | arXiv の開いた下限は未実測 | §2 で 1991-01-01 を下限とする閉区間に変えた |
| 6 | 完走述語が機械判定できない | §7 の 6 条件を証拠 schema つきに書き直し、§10 の保存 field を拡張した |
| 7 | 6 条件を満たしても全件でない場合がある | §7.1 に同数入れ替えの反例と、2 走 digest 一致の緩和策を足した |
| 8 | venue 年次一覧の補助探索が無い | §6.3 に足した。§9 の「母集合の外」との関係も書いた |
| 9 | `C-BLK-O` が無い、control の索引別実行式と期待が無い、control 失敗の帰結が無い | §6.1 を表に書き直した |
| 10 | 補助探索の上限内の選択順序が未定義 | §6.3 に主キー辞書順昇順を登録した |
| 11 | 非意味的修繕が echo の単射性を仮定していた | §8 を正規化 request による比較へ変えた。DBLP の echo が `h`/`f` を含まない実測も §4.1 に足した |
| 12 | 主キーが全 record に適用できる規則になっていない | §5.1 を 3 段の total な規則に書き直した |
| 13 | 事前知識の開示が狭い | §11 を「本走行の record を見ていない」へ言い換え、影響経路と追加の観測を足した |
| 14 | `RW1` で許されない不在方向の文があった | §6.1 の該当文を「在るかどうかを調べる」表現へ書き換えた |
| 15 | DBLP の総件数 field 名が §4 と §7 で不一致 | §4.1 の表に統一した |
| 16 | DBLP は句検索を表現できない (レビュー後に実測) | §3.5 と §4.2 に足し、DBLP の枝の設計を変えた |
