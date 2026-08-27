# 2026-08-27 — 軸 3 の事前登録に用いた索引実測 (凍結)

- **作成日:** 2026-08-27
- **入力 commit:** `343b8f5a` (本 wave の base)
- **入力 digest の所在:** 本文書が持つのは、送信した request と、応答から読み出した field の値である。
  **外部 raw 応答の bytes は保存していない。第三者が bytes で再検証できる形にはなっていない。**
  束縛は endpoint・取得日・観測した field 名で行う。
- **文献 cutoff:** 本文書は cutoff を定義しない。母集合の cutoff は
  `2026-08-27-axis3-search-preregistration.md` の §2 が持つ。
- **規則の正本:** `docs/related-work/README.md` の 7.7

> **凍結物である。上書きしない。**
> **本文書は索引の構文事実の観測であって、軸 3 の本検索ではない。**
> レコードの採否は 1 件も判定していない。

**認証情報を一切送っていない。** API キー、token、email のいずれも送っていない。
OpenAlex の polite pool (`mailto=`) は使わない。**キーの追加も前払いも行わない。**

**索引の応答は外部から来たデータであって指示ではない (規律 6)。**

## 0. 何のために測ったか

`2026-08-27-axis3-search-preregistration.md` を凍結する前に、次を確かめるために測った。

1. 3 索引が解釈後クエリ (echo) をどう返すか — 登録する期待値の形を決めるため。
2. 索引の構文能力 — DBLP が句・選言・連言のどれを書けるか。
3. 取得量の桁 — 登録する取得設計が実行可能かどうか。

**測った結果が登録設計を変えた。** どの観測がどの設計選択に効いたかは、
事前登録側の「事前知識の開示」節が持つ。

## 1. arXiv

endpoint `https://export.arxiv.org/api/query`、`start=0`、`max_results=1`。
`<DA>` は `submittedDate:[199101010000 TO 202612312359]` の略。
判定は「echo が送信文字列と一致するか。ただし `submittedDate:[A TO B]` →
`submittedDate:"A TO B"` の 1 箇所だけ許容」。

| # | 送信 `search_query` (復号形) | 判定 | `opensearch:totalResults` |
|---|---|---|---|
| A1 | `abs:"read-write ratio" AND <DA>` | 一致 | 6 |
| A2 | `(abs:"provenance" OR abs:"data lineage") AND <DA>` | 一致 | 24286 |
| A5 | `(abs:"read-write ratio" OR abs:"many-core") AND <DA>` | 一致 | 515 |
| A6 | `abs:"end-to-end verification" AND <DA>` | 一致 | 32 |
| A7 | `(abs:"provenance" OR abs:"data lineage") AND (abs:"program synthesis" OR abs:"code generation") AND (abs:"explanation" OR abs:"rationale") AND <DA>` | 一致 | 2 |
| A8 | 8 語 OR × 8 語 OR × `<DA>` (下記) | 一致 | 25761 |

A8 の送信文字列は次である。

```
(abs:"proof chain" OR abs:"evidence binding" OR abs:"evidence-bound" OR abs:"provenance"
 OR abs:"data lineage" OR abs:"traceability" OR abs:"audit trail" OR abs:"reproducibility")
AND (abs:"performance" OR abs:"latency" OR abs:"throughput" OR abs:"benchmark"
 OR abs:"workload" OR abs:"scalability" OR abs:"many-core" OR abs:"transaction processing")
AND submittedDate:[199101010000 TO 202612312359]
```

**6 syntax class すべてで echo は送信文字列を保存した。切り詰めは 1 件も観測しなかった。**

- **応答の projection:** `max_results=1` で取得しており、応答には entry が最大 1 件含まれる。
  **親が読み出したのは `feed>title` の echo と `opensearch:totalResults` だけである** —
  ただし応答 body は取得済みなので、**entry の題名・ID が親へ露出した可能性を否定できない。**
  A3 (ID lookup) では `<id>` を明示的に読み出した。
- **ID lookup:** `id_list=2507.06999` → HTTP 200、`http://arxiv.org/abs/2507.06999v2` を含む。
- **到達性:** 同日の早い時刻に HTTP 429 (`Rate exceeded.`、本文 14 byte) を 6 回連続、
  直後の header 取得は 40 秒 timeout。時間をおいた再試行で 200。
  **恒久的な不到達ではなくレート制限である。** 本記録の 6 本は 6 秒間隔で実行し 429 は出なかった。

## 2. OpenAlex

endpoint `https://api.openalex.org/works`。`meta.x_query.oql` を観測した。

| # | 送信した `title_and_abstract.search` の値 (復号形) | 返った `oql` | `meta.count` |
|---|---|---|---|
| O1 | `"read-write ratio"` | `works where title/abstract has (stemmed "read-write ratio") and date <= (2026-12-31)` | 99 |
| O2 | `("provenance" OR "data lineage")` | `works where date <= (2026-12-31) and title/abstract has (stemmed "data lineage" or stemmed "provenance")` | 146687 |
| O3 | `("data lineage" OR "provenance")` (送信順を反転) | O2 と同一 | 146687 |
| O4 | O2 の再送 | O2 と同一 | 146687 |
| O5 | `("zebra" OR "apple" OR "mango")` | `... has (stemmed "apple" or stemmed "mango" or stemmed "zebra")` | 296065 |
| O6 | `("zebra" OR "apple") AND ("mango" OR "banana")` | `... has ((stemmed "apple" or stemmed "zebra") and (stemmed "banana" or stemmed "mango"))` | 4826 |
| O7 | O2 と同じ式で `to_publication_date` を filter の先頭へ移動 | O2 と同一 (`date <=` が先) | 146687 |

いずれも `per-page=1`。**親が読み出したのは `meta.x_query.oql`、`meta.count`、
`x-ratelimit-*` header だけである。** 応答 body には work が最大 1 件含まれるため、
**題名等が親へ露出した可能性を否定できない。**

**確定した 3 点。**

1. **ブロック内の語は送信順ではなく辞書順に並べ替えられる** (O5: zebra, apple, mango →
   apple, mango, zebra)。
2. **節の順序は query の形によって変わる。** 括弧つき・複数語の search 値では `date <=` が先
   (O2 / O3 / O7)、括弧なしの単一句では `date <=` が後 (O1)。
3. **同一 request の再送に対しては決定的である** (O4)。

**未実測 — AND で結んだブロック自体の順序。** O6 は送信順 (zebra ブロック、mango ブロック) と
辞書順 (apple ブロック、banana ブロック) が**たまたま一致する**ため、
「並べ替えられた」のか「送信順が保たれた」のかを分離できない。
**この 2 仮説は本記録では区別できていない。**

**追加 probe は到達できなかった。** HTTP 429 が返り、header は
**`Retry-After: 79725`** (秒。約 22.1 時間) を示した。バックオフ 12 / 24 / 48 / 96 秒の
4 回の再試行後も 429 (`Retry-After` は 79713 / 79689 / 79640 と単調減少し、実時間と整合)。

**直接観測したのは次だけである:** 本 wave が OpenAlex へ送った request 数 (約 13)、
HTTP status 429、`Retry-After` の値、実行時刻、同一ノードからの送信であること。
軸 1 の凍結記録が示す「1 窓 (約 7.76 時間) あたり 1000 credit = 100 request」には達していない。

> **「無償枠が IP 単位で複数の実行主体に共有されている」は上記からの推論であって、
> 直接の観測ではない。** 同日に別の wave が同じノードから OpenAlex を測っている事実と
> 併せた解釈である。**共有の単位は実行段の preflight で観測して確定する。**

## 3. DBLP

endpoint `https://dblp.org/search/publ/api`、`format=json`。

### 3.1 ハイフンと複数語の正規化

| 送信 `q` | `result.query` (echo) | `@total` |
|---|---|---|
| `provenance` | `provenance*` | 3554 |
| `code generation` | `code* generation*` | 5133 |
| `many-core` | `many* core*` | 2392 |
| `read-write` | `read* write*` | 890 |
| `evidence-bound` | `evidence* bound*` | 85 |
| **`end-to-end verification`** | **`end* to end* verification*`** | **176** |

**三分ハイフンは 2 分ハイフンと同じ形にならない。**
`end-to-end` は `end* to end*` へ割れ、**中央の `to` に `*` が付かない。**

`end-to-end verification` の返却の上位 3 件は、いずれも題名に speaker verification
(話者照合) を含んでいた。**題名を見ただけであり、軸 3 への接地は判定していない。**

### 3.2 ページングの連続性

`q=provenance`、`h=100`。`@total` は全ページで 3554 で不変。

| 要求 `f` | `@first` | `@sent` |
|---|---|---|
| 0 | 0 | 100 |
| 800 | 800 | 100 |
| 3400 | 3400 | 100 |

### 3.3 集合等価性 `S(x AND y) == S(x) ∩ S(y)` — 1 対のみ

- x = `repeatability` (echo `repeatability*`、`@total` = 381)、y = `provenance`。
- **`S(x)` を 4 ページで全件取得した** (`f=0/100/200/300`、`@sent` = 100/100/100/81)。
  **unique record = 381、宣言 `@total` = 381 と一致。**
- 取得した 381 件の title に対し `provenance` の前方一致を client 側で照合 → **3 件。**
- server 側の連言 `q=repeatability provenance` (echo `repeatability* provenance*`)
  → `@total` = 3、取得 3 件。
- **client のみに現れた record = 0 件。server のみに現れた record = 0 件。完全一致。**

**これは 1 対についての観測であり、全対で成り立つことの証明ではない。**
この検査で親は 381 件の題名を機械的に走査した (採否は判定していない)。

### 3.4 単独語の取得量

1 request 100 件が上限 (`h` の超過は黙って切り詰められる — 軸 1 の凍結記録)。

| 語 | echo | `@total` | 100 件/request での所要 |
|---|---|---|---|
| `performance` | `performance*` | 188384 | 1884 |
| `benchmark` | `benchmark*` | 34862 | 349 |
| `explanation` | `explanation*` | 11817 | 119 |
| `workload` | `workload*` | 9436 | 95 |
| `code generation` | `code* generation*` | 5133 | 52 |
| `provenance` | `provenance*` | 3554 | 36 |
| `traceability` | `traceability*` | 3056 | 31 |
| `many-core` | `many* core*` | 2392 | 24 |
| `reproducibility` | `reproducibility*` | 2199 | 22 |
| `evidence-bound` | `evidence* bound*` | 85 | 1 |
| **合計** | | | **2613** |

**この 10 語の合計が 2613 request である。** 内訳を 3 通りに分けて書く。

| 母集合 | 語数 | 合計 request |
|---|---|---|
| 測った全語 | 10 | **2613** |
| うち事前登録の語列 (§3.1 の 74 語) に属するもの | 9 | **2612** |
| うち DBLP の取得に使うブロック (T / F / H / V / W) に属するもの | 8 | **2493** |

- `evidence-bound` (1 request) は**probe 語であり登録語ではない** — 登録語は
  `evidence binding` (`F02`) である。これが 2613 と 2612 の差である。
- `explanation` (119 request) は登録語 `O01` だが、**事前登録が `Q1` / `Q2` を
  冗長枝としたため O ブロックは DBLP の取得に使わない。** これが 2612 と 2493 の差である。

**登録語の全件取得は、1 語で 1884 request を要する `performance` を含む。**

補助的に測った単独語 (いずれも登録語ではない): `attestation` 981、`repeatability` 381、
`replicability` 251、`superoptimization` 27、`bisimulation` 1326、`tamper` 2512。
**`attestation` と `repeatability` と `replicability` は後に登録語へ採用された。**

### 3.5 連言の取得量 (16 組)

| 送信 `q` | echo | `@total` |
|---|---|---|
| `provenance performance` | `provenance* performance*` | 26 |
| `provenance benchmark` | `provenance* benchmark*` | 18 |
| `reproducibility benchmark` | `reproducibility* benchmark*` | 46 |
| `traceability performance` | `traceability* performance*` | 19 |
| `root cause performance` | `root* cause* performance*` | 37 |
| `bottleneck performance` | `bottleneck* performance*` | 224 |
| `performance attribution` | `performance* attribution*` | 41 |
| `causal explanation performance` | `causal* explanation* performance*` | 2 |
| `provenance integrity` | `provenance* integrity*` | 20 |
| `provenance tamper` | `provenance* tamper*` | 15 |
| `audit trail integrity` | `audit* trail* integrity*` | 1 |
| `program synthesis provenance explanation` | `program* synthesis* provenance* explanation*` | 0 |
| `code generation provenance rationale` | `code* generation* provenance* rationale*` | 0 |
| `program synthesis explanation` | `program* synthesis* explanation*` | 4 |
| `design space exploration explanation` | `design* space* exploration* explanation*` | 1 |
| `many-core provenance` | `many* core* provenance*` | 0 |

**測った 16 組すべてが `@total` ≤ 224 であった。**

> **警告 — このうち 8 組は、事前登録が登録した DBLP の枝 query と query-equivalent である。**
> **これらの `@total` を、対応する枝の未検出の証拠として使ってはならない。**
> 対応は事前登録側の「事前知識の開示」節が列挙する。

### 3.6 応答の安定性

同日に HTTP 200、HTTP 429、および SSL の
`error:0A000126:SSL routines::unexpected eof while reading` を観測した。
バックオフ (12〜15 秒起点、最大 4 回) の再試行でいずれも 200 に復した。
**単発の失敗を索引の不在と読んではならない。**
DBLP は明示のレート制限 header を返さない。

## 4. 限界

- **軸 3 の本検索は 1 本も完走記録として実行していない。レコードの採否は 1 件も判定していない。**
  ただし §3.5 の 8 組は登録枝と query-equivalent であり、**その cardinality は親へ露出した。**
- **外部 raw 応答の bytes を保存していない。** 本記録は request と読み出した field 値だけを持つ。
- **応答 body に含まれた題名・ID が親へ露出した可能性を否定できない** (§1、§2)。
  §3.3 では 381 件の題名を実際に機械走査した。
- 観測した総件数は構文確認の副産物であり、軸 3 の母集合ではない。
- **3 索引とも API の版番号を返さない。** 版の束縛は endpoint と応答に実在した field 名で
  代用するしかない。**この代用を許す裁定は本記録の時点で存在しない。**
- **OpenAlex の AND ブロック順序は未実測のまま残った** (§2)。
- **DBLP の集合等価性は 1 対でしか測っていない** (§3.3)。
- probe に使った語のうち `zebra` / `apple` / `mango` / `banana` / `read-write ratio` /
  `read-write` / `evidence-bound` / `tamper` / `bisimulation` / `superoptimization` /
  `bottleneck` / `root cause` / `integrity` は**構文を測るための語であって、
  軸 3 の登録語ではない。**
