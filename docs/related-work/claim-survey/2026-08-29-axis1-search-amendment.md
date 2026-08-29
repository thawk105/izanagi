# 2026-08-29 — 軸 1 の文献検索 契約の改訂 (事前登録・凍結)

- **作成日:** 2026-08-29
- **入力 commit:** `164e2c355` (本 wave の base)
- **入力 digest:** 下記 input path 群の内容は入力 commit `164e2c355` の blob そのものである。
  索引の実測値だけは repo の外にあり、endpoint・取得日・観測した field 名で束縛する。
- **入力 path:** `docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md` (旧契約) /
  `docs/related-work/claim-survey/2026-08-27-axis1-search-execution.md` (旧実行記録) /
  `docs/related-work/README.md` の 7.7 / `docs/decisions.md` の D1155・D1183・D1207・D1208
- **文献 cutoff:** 旧契約 §2 の暦年境界 2026-12-31 をそのまま引き継ぐ。§2 を見よ。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」
- **改訂の根拠:** `docs/decisions.md` の D1207 (完走述語の構造的な不成立は宣言的除外でなく
  契約の改訂で閉じる)。実装は T-2033 / T-2034 / T-2035 / T-2037。

> **凍結物である。**
> **この文書に検索結果を書き戻してはならない。** 実行の記録は別の日付の凍結物が持つ (§10)。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。
> **旧契約と旧実行記録の bytes は 1 byte も変えていない** (D1208)。

---

## 0. この文書は何であって、何でないか

**これは旧契約 (2026-08-27 の事前登録) の改訂であって、実行ではない。**
本文書を凍結した時点で、改訂後の検索は 1 本も実行していない。

**本文書は軸 1 の成熟度を動かさない。軸 1 は `RW1` のままである。**

**本文書は世界の不在を一切作らない。** 既存の世界側の不在の文
(`docs/paper-story/2026-08-26.md` §3 の 1、`docs/related-work/README.md` 7.6 の空白域) を
支持も強化もしない。

### 0.1 これは結果を見た後の改訂である (開示)

**旧走行の結果を見た後に書いた改訂である。** D1207 がまさにその不成立を契約の改訂で閉じよと
裁定しているので改訂自体は正当だが、**結果非依存になったわけではない。**
本文書が prospective なのは**改訂後の新しい走行に対してだけ**である。

旧走行から持ち込んだ観測は次のとおりで、いずれも受理集合を広げる向きに働く。

| 改訂 | 旧入力に対する変化 | 権限 |
|---|---|---|
| 容量エコーと実要素数の分離 (§7 条件 3) | arXiv 105/200、OpenAlex 124/200 が `否` から `可` へ | D1207 |
| 索引固有 work ID と work-family の分離 (§7 条件 4・5) | 同一 DOI の別 OpenAlex work が取得失敗から別 record へ | D1207 |
| 固定日付 shard (§3.4) | `AX1-Q6@arxiv` の 30,753 件 1 枝が完走しうる aggregate へ | D1207 |
| DBLP のハイフン期待 echo (§3.5) | `AX1-T05` / `AX1-T07` が `否` から `可` へ | **未裁定 (§13 の U7)** |

最後の 1 件は D1207 が名指ししていない面である。**本文書は一方に倒さない** — §3.5 と §10.3 の
二重判定で扱う。

## 1. 旧契約のどこを引き継ぎ、どこを置き換えるか

| 旧節 | 扱い |
|---|---|
| §0、§0.0 | 歴史記録として引き継ぐ。 |
| §1 (軸 1 と分類契約) | **逐語で引き継ぐ。** 包含条件 A〜D、判定規則、判定語彙、極性、A の読み方を変えない。 |
| §2 (cutoff) | 暦年境界 2026-12-31 と索引別日付欄の当て方は引き継ぐ。母集合の定型と shard の適用は §2 が置き換える。 |
| §3.1 (概念ブロック) | **逐語で引き継ぐ。** 5 ブロック 48 語を 1 語も変えない。 |
| §3.2 (枝 Q1〜Q6) | **逐語で引き継ぐ。** 論理式を変えない。 |
| §3.3〜§3.5 (query ID) | **全面置換** (§3)。全 ID を新規化し、shard・aggregate・DBLP の期待 echo を固定する。 |
| §3.6、§3.7 | §3.6 の総数は §3.6 が置き換える。§3.7 の「語を足したら別 ID」は引き継ぐ。 |
| §4.1〜§4.3、§4.5 | 旧時点の観測として参照可能。現行 API の恒久仕様としては扱わない。 |
| §4.4 (レート制限と予算) | **全面置換** (§4)。「1 窓 約 7.76 時間」は取り下げる。 |
| §5.1〜§5.3 (主キーと台帳) | **全面置換** (§5)。取得層を索引固有 work ID、統合層を work-family に分ける。 |
| §5.4 (alias) | **逐語で引き継ぐ。** |
| §6.1 (control) | §6 が置き換える。新 ID と完全 request を持つ回帰 control とする。 |
| §6.2 (感度監査)、§6.3 (補助探索) | **義務は緩めず引き継ぐ。** 本改訂でも要求として残る。 |
| §7、§7.1 (完走述語) | **全面置換** (§7)。 |
| §8 (停止条件と amendment) | **全面置換** (§8)。 |
| §9 (母集合の外) | **逐語で引き継ぎ**、旧 ID の参照だけ新 ID へ読み替える。 |
| §10 (実行の記録) | §10 が置き換える。D1183 の再開点を必須にする。 |
| §11 (事前知識の開示) | 旧開示を引き継ぎ、§11 で本改訂固有の開示を足す。 |
| §12 (限界) | 引き継ぎ、§12 で足す。 |
| §13 (訂正の内訳) | 歴史的記録としてのみ残す。現契約ではない。 |

**旧契約の bytes は変更していない。** 上記は本文書側の宣言であり、旧文書への追記ではない (D1208)。

## 2. 母集合 — 1 行で言える定型

> **軸 1 の母集合は、共有暦境界 2026-12-31 を各索引固有の日付欄へ当てた登録 epoch
> `AX1-20260829-E1` の query 群 (固定・非重複の日付 shard を含む) が返した、索引固有 work ID
> レコードの和である。境界の外、登録した query と登録した 3 索引の外は母集合の外であり、
> `AX1-20260829-E1-Q6-EXCLUSION@dblp` の 1 枝だけが D1155 の構文能力を理由とする宣言的除外である。
> 取得失敗・無償枠切れ・未実行は除外ではなく `未完走` である。**

**「同一 cutoff の 3 索引の和集合」という短縮を使ってはならない。** 3 索引は語の意味論が違う。

境界の当て方は旧契約 §2 を引き継ぐ。

- arXiv: `submittedDate` が `199101010000` 以上 `202612312359` 以下。
- OpenAlex: `to_publication_date=2026-12-31`。下限は shard が与える。
- DBLP: 年 facet を使わず全年を取得し、record の `year` が 2026 以下であることを client 側で判定する。
  **`year` を持たない record は捨てず `要裁定` とする。**

**この境界は work 単位で一様ではない。** 同じ研究が索引ごとに違う年で記録されていれば、
片方の record だけが残る。和は record の和なので候補としては残るが、**record 数は索引間で一致しない。**
この非一様性は §5 の work-family 層で可視化し、隠さない。

## 3. 新しい query ID と固定日付 shard

### 3.1 登録 epoch と ID の形

登録 epoch は `AX1-20260829-E1` とする。ID の一般形は次のとおり。

```text
AX1-20260829-E1-<branch>[-S<shard>]@<index>
```

- `<branch>` は `Q1`〜`Q6` (arXiv / OpenAlex) または `T01`〜`T12` (DBLP)。
- `<index>` は `arxiv` / `openalex` / `dblp`。
- **`-S...` を持つ ID だけが HTTP を発行する leaf である。** `-S...` を持たない ID は、
  shard を持つ枝では HTTP を発行しない aggregate、shard を持たない枝では leaf そのものである。
- shard 記法は暦年が `SYyyyy`、暦月が `SMyyyymm`、下限側が `SPRE1991`。

**旧 ID は 1 つも継続しない。** 旧走行は永久に `未完走` の記録として残り、後から `完走` へ変わらない。

### 3.2 shard を持たない枝

arXiv の `Q1`〜`Q5`、OpenAlex の `Q1` / `Q2` / `Q4` / `Q5`、DBLP の `T01`〜`T12` は
単一 leaf とする。query 本体は旧契約 §3.3〜§3.5 の論理式をそのまま使い、ID だけを新規化する。

### 3.3 `AX1-Q6@dblp` の宣言的除外は維持する

`AX1-20260829-E1-Q6-EXCLUSION@dblp` は D1155 により宣言的に除外する。理由は、DBLP が句の選言を
表現できず要旨を索引しないという**索引の構文能力の限界**である。世界に該当文献が無いことを
意味しない。補助的な前方一致 query は本枝の代替ではなく、`RW3` の算入対象でもない。

**この 1 枝以外へ D1155 型の宣言的除外を拡張してはならない** (D1207)。

### 3.4 固定日付 shard

**shard の境界は結果を見る前に固定する。** 導出関数が受け取るのは索引・枝・cutoff だけであり、
**境界を動かしうる入力は cutoff だけ**である。件数・応答・環境変数・現在時刻を一切参照しない。
**件数を見てからの再分割・境界移動は禁止する。**

| 枝 | shard |
|---|---|
| `AX1-20260829-E1-Q6@arxiv` | 暦年 `SY1991`〜`SY2014` の 24 本 + 暦月 `SM201501`〜`SM202612` の 144 本 = **168 leaf** |
| `AX1-20260829-E1-Q3@openalex` | `SPRE1991` + 暦年 `SY1991`〜`SY2026` = **37 leaf** |
| `AX1-20260829-E1-Q6@openalex` | 同上 **37 leaf** |

境界規則。

- arXiv `SYyyyy` は `submittedDate:[yyyy01010000 TO yyyy12312359]`。
  `SMyyyymm` は当該月の初日 0000 から末日 2359 まで。
- OpenAlex `SPRE1991` は下限なし・`to_publication_date=1990-12-31`。
  `SYyyyy` は `from_publication_date=yyyy-01-01,to_publication_date=yyyy-12-31`。
- 隣接・重複 0・未被覆 0 を機械検査する。閉区間は内部で半開区間へ変換して検査する。

**arXiv の結果窓。** 旧走行は `start=10000` で HTTP 500 を 3 回受けた (旧記録 §4.3)。
したがって任意 shard の `declared_total > 10000` は**その leaf を `未完走` とする。**
`== 10000` は 10,000 行すべてを正常に取得できた場合だけ受理する。
**同じ epoch の中で追加分割してはならない。** 必要なら新しい amendment・新しい epoch・新しい ID を要する。

**arXiv Q6 で暦月まで細かくした理由。** 旧走行の宣言 30,753 件は近年に偏在しうる。
暦年のままでは近年の shard が 10,000 件窓を超えて `未完走` になる公算がある。
**細かい格子を選んだのは実行可能性の理由であり、母集合は変わらない** —
shard の和は元の枝と同じ日付域を過不足なく覆う。この選択は**結果を見る前に**固定した。

**OpenAlex に shard を置く理由は結果窓ではない。** OpenAlex は cursor で歩ける。
shard の目的は、無償枠の窓をまたぐときの cursor 失効を避け、再開点の粒度を leaf に揃えることである。

**独立第 2 走の要否は登録事項である。** 各 logical query に `independent_pass_required` を登録し、
**無償枠の窓数から導出してはならない** (窓数は実行時の事情であって契約ではない)。
本改訂は shard を持つ 3 枝 (`Q6@arxiv`、`Q3@openalex`、`Q6@openalex`) を `true`、
それ以外を `false` として登録する。

### 3.5 DBLP の期待 echo — 索引の実測トークン化に合わせる

**旧契約 §3.5 の期待 echo は「語の各単語に `*` を付けて空白で連ねた文字列」だった。**
DBLP は**ハイフンも語の区切りとして扱う**ため、`two-phase locking` は
`two* phase* locking*` と解釈される。旧走行はこの不一致で `AX1-T05@dblp` と
`AX1-T07@dblp` を条件 1 で落とした (旧記録 §3.1)。

本改訂が登録する期待 echo は次の決定的規則とする。

> **登録句を英数字 token へ分割し (ハイフンも区切りとする)、各 token に `*` を付け、
> 単一空白で連ねた文字列。**

**根拠は軸 1 と無関係な中立語での実測である** (§4.2)。すなわち規則そのものは軸 1 の結果を
見なくても導ける。**一方、旧走行で実 echo を見た後に規則を採ることは事実であり、§0.1 に開示した。**

**本文書は、この規則を採るか旧の逐語期待を保つかを決めない。**
実行記録は DBLP の全枝について**両方の判定を併記する** (§10.3)。可否は人間の裁定に委ねる (§13 の U7)。

### 3.6 登録した ID の総数

- arXiv: `Q1`〜`Q5` の 5 leaf + `Q6` の aggregate 1 と leaf 168 = leaf **173 本**。
- OpenAlex: `Q1` / `Q2` / `Q4` / `Q5` の 4 leaf + `Q3` の aggregate 1 と leaf 37
  + `Q6` の aggregate 1 と leaf 37 = leaf **78 本**。
- DBLP: `T01`〜`T12` の 12 leaf + 宣言的除外 1 本。

**HTTP を発行する leaf は 263 本**であり、これに宣言的除外の `Q6-EXCLUSION@dblp` が 1 本加わる。

## 4. 索引の実測 (2026-08-29、pegasus02 login node から直接 HTTP、認証情報なし)

**認証情報を一切送っていない。** API キー、token、email のいずれも送っていない。
OpenAlex の polite pool (`mailto=`) は使わない。**キーの追加も前払いも行わない。**

### 4.1 OpenAlex の無償枠 — 旧契約 §4.4 を取り下げる

10:00 JST 付近の 1 応答が返したヘッダ。

```
x-ratelimit-limit: 1000
x-ratelimit-remaining: 990
x-ratelimit-credits-used: 10
x-ratelimit-cost-usd: 0.001
x-ratelimit-limit-usd: 0.1
x-ratelimit-prepaid-remaining-usd: 0
x-ratelimit-reset: 84194
```

**観測したのはこのヘッダ値だけである。窓が明ける瞬間は観測していない。**
したがって次を守る。

- **`reset` の値は「観測時点の reset 秒数」としてだけ記録する。「窓長」と書かない。**
  旧契約 §4.4 の「1 窓 (約 7.76 時間)」は本改訂で取り下げる。旧記録 §4.4 の観測 (83,401 秒) と
  本日の 84,194 秒は同じ桁だが、いずれも窓長の測定ではない。
- **request 数で予算を運転しない。** 各応答の `x-ratelimit-remaining` /
  `x-ratelimit-credits-used` / body の `meta.cost_usd` を正本とし、
  `remaining - 30 (予約) >= 直近観測の cost` のときだけ次を発行する。
  予約を割ったら即座に停止して再開点を発行する (§8)。
- **1 request = 10 credit は 1 種類の request についての観測である。** anchor、cursor 後続頁、
  複雑な検索、429/503、再試行が同じ cost だとは確かめていない。実際の cost は毎回ヘッダから読む。

### 4.2 DBLP のトークン化 — 中立語での実測

軸 1 の登録語ではない中立語で測った。

```
request      : https://dblp.org/search/publ/api?q=alpha-beta+gamma&format=json&h=1
result.query : "alpha* beta* gamma*"
```

**DBLP はハイフンを語の区切りとして扱い、各 token に `*` を付けて空白で連ねた文字列を返す。**
`@total` と `@sent` は**文字列**で返る。

その直前の別 probe (`q=izanagi`) では HTTP 503 が返った。旧記録 §4.5 と同型の不安定さである。

### 4.3 arXiv の生死と opensearch field

```
request                 : https://export.arxiv.org/api/query?search_query=all:electron&start=0&max_results=3
opensearch:totalResults : 185491
opensearch:itemsPerPage : 3
opensearch:startIndex   : 0
<entry> の実数          : 3
```

**`itemsPerPage` は要求値のエコーである。** この probe は満頁なので実要素数と一致するが、
旧記録 §4.1 の実測では最終頁で要求 200 / 宣言 200 / 実数 105 になっている。

### 4.4 OpenAlex の応答の形と、複合 filter の echo

`meta` は `count` / `per_page` / `page` / `next_cursor` / `x_query.oql` / `x_query.oqo` /
`cost_usd` を持つ。`results[].id` は `https://openalex.org/W...` の URL 形、
`doi` は `https://doi.org/10.xxxx/...` の小文字形で返る。
**cursor で歩くとき `meta.page` は `null` である** — 頁番号は応答から復元できないので、
発行した request 側の頁番号を occurrence へ当てる。

**複合 filter の echo を中立語で測った。** 送信したのは
`title_and_abstract.search:("alpha beta" OR "gamma delta") AND ("epsilon zeta" OR "eta theta"),
to_publication_date:2026-12-31` である。返った `meta.x_query.oql` は次のとおり。

```
works where date <= (2026-12-31)
  and title/abstract has (
    (stemmed "alpha beta" or stemmed "gamma delta")
    and (stemmed "epsilon zeta" or stemmed "eta theta")
  )
```

**日付が先に来る。改行とインデントを含む整形済み文字列である。**
同じ応答の `meta.x_query.oqo` は、`filter_rows` に `to_publication_date` を先頭とし、
続けて各概念ブロックを `{"join": "or", "filters": [...]}` の形で持つ構造を返す。
**§7 の条件 1 が OpenAlex について構造比較を採るのは、この実測による。**

### 4.5 引き継ぐ実測 (旧契約 §4.1〜§4.3、§4.5 — 再測していない)

- arXiv はリクエスト間 3 秒以上、429 は 3→6→12 秒の指数バックオフ。`http://` は 301 を返す。
- DBLP は要求超過を黙って切り詰める (`h=1000` でも `@sent` 100)。1 リクエスト 100 件が実効上限。
- DBLP は連続取得で接続を切る。2 秒間隔で 24 リクエスト目付近、15 秒間隔でも 7 リクエスト程度で
  切断し、45 分の冷却の後 30 秒間隔で回復した (旧記録 §4.5)。

## 5. 取得完全性と work-family — 二層に分ける (D1207)

### 5.1 取得層の主キーは索引固有 work ID である

**取得完全性は索引固有の work ID で数える。**

| 索引 | 索引固有 work ID |
|---|---|
| arXiv | `entry/id` |
| OpenAlex | `id` (`https://openalex.org/W...`) |
| DBLP | `info.key` |

- 全 occurrence を頁番号・頁内 ordinal とともに保存する。同じ work ID の再出現も**削除せず**
  multiplicity として記録する。
- **DOI・arXiv ID・題名などの正規化 family key を取得完全性の主キーに用いてはならない。**
- **取得層で family key による dedup を行ってはならない。**
- 索引固有 work ID を取り出せない要素が 1 つでもあれば、その頁は条件 4 で `否` とする。

### 5.2 統合層は work-family で扱う

正規化 family key は旧契約 §5.1 の規則を引き継ぐ。

1. arXiv ID があれば `arxiv:<id>` (版接尾辞 `vN` は落とす)。
2. 無ければ DOI を正規化して `doi:<小文字>` (`https://doi.org/` と `http://dx.doi.org/` の前置を除去)。
   `10.48550/arxiv.<id>` の形は `arxiv:<id>` へ写像する。
3. どちらも無ければ `<索引名>:<索引固有 ID>` とし、**`要裁定` の印を付ける。**

**異なる索引固有 work ID が同じ family key を持つことは、取得の重複ではない。**
work-family 候補として別層に記録する。共有識別子が無ければ自動統合せず `要裁定` とする。
**題名一致だけの重複除去を禁じる** (7.7.6)。

### 5.3 件数の単位

取得完全性は**索引固有 work ID 数**、重複除去後は **work-family 数**、主張表は**研究数**で数え、
変換の対応表と未解決 family 数を残す。**単位の違う数を足さない。**

### 5.4 alias

旧契約 §5.4 を逐語で引き継ぐ。既知の実例は `2503.10036` — `CCaaLF` は v4 で
`Modeling Concurrency Control as a Learnable Function` へ改題され `NeurCC` へ改名された。

### 5.5 record ごとに日付を保存する

occurrence ごとに、索引固有の日付欄の**生値**と、そこから解釈した暦日を保存する。
解釈できない場合は欠損理由を保存する。**捨ててはならない。**

- leaf は shard 境界の外の暦日を持つ record を**拒否する** (その leaf は `否`)。
- 暦日を導出できない record は範囲外にせず、`要裁定` として leaf に残す。
  DBLP の `year` 欠損はここに当たる。

## 6. control と補助探索

旧契約 §6 の義務を引き継ぐ。ただし control は新 ID と完全 request を持ち、
**旧走行の結果を知った後に設計した回帰 control である**と明記する。

- **control の通過を、取りこぼしが無いことの根拠にしてはならない** (D351、旧契約 §6.2)。
  control は演算子と概念ブロックの健全性だけを見る。
- §6.2 の感度監査と §6.3 の補助探索は**義務として残る。** 実施していなければ `not_run` とし、
  §7 の導出式により `axis_complete` は偽になる。

## 7. 完走述語 — 改訂した 6 条件と最上位の導出式

各 leaf について、次の全部が成立したときに限り `完走` とする。

1. **解釈照合。** catalog から生成した正規化 request と、索引が返した解釈後 query が、
   登録した期待値と一致する。**比較の方法は索引ごとに違う。**
   - **arXiv と DBLP は文字列比較**とし、正規化は 3 つだけ許す — 連続空白を 1 個へ、
     URL エンコードを復号、arXiv の `submittedDate` の角括弧と二重引用符の差。
     それ以外の差異は不一致とする。DBLP の期待 echo は §3.5 の決定的規則で生成する。
   - **OpenAlex は `meta.x_query.oqo` の構造比較**とする。登録した構造 (`filter_rows` の順序、
     各 row の `column_id` / `operator` / `value`、ブロックの `join`) との完全一致を要求する。
     `meta.x_query.oql` の生文字列は証拠として保存するが**判定には使わない** — 実測 (§4.4) の
     とおり、複合 filter の `oql` は改行とインデントを含む整形済み文字列であり、
     空白正規化だけで安定に一致させられないためである。
   - **頁ごとに期待値が違う場合は頁ごとに比較する。** arXiv の echo は `start` を含むので、
     最終頁の期待値を全頁へ当ててはならない。

2. **ページングの連続性と黙った切り詰めの検出。** offset 方式は直前の位置と実要素数から、
   cursor 方式は直前の頁の `next_cursor` とその応答本文の SHA-256 からのみ次 request を生成する。
   欠落・巻き戻り・別応答由来の cursor・同一 request ID で異なる request bytes を認めない。
   **非終端頁の実要素数が要求頁サイズ未満なら、黙った切り詰めとして `否` とする。**

3. **索引別の実要素数。** 各頁の実要素数 `actual_count` は、**保存した応答本文を登録済み parser で
   解析して得た要素列の長さ**として定義する。arXiv は Atom の `entry` 数、OpenAlex は `results` 数、
   DBLP は `result.hits.hit` 数を用いる。
   **arXiv の `itemsPerPage` と OpenAlex の `meta.per_page` は要求容量のエコーであって実要素数ではない。**
   したがって `actual_count` との一致を要求しない。ただし catalog に登録した要求頁サイズとの一致は要求する。
   DBLP の `@sent` は実要素数のエコーであり、`actual_count` との一致を要求する。
   offset 方式では `actual_count == min(頁サイズ, max(宣言総件数 - 位置, 0))`、
   cursor 方式では非終端頁の `actual_count == 頁サイズ`、終端頁は `0 <= actual_count <= 頁サイズ`。
   **この条件を容量エコーまたは要求値だけから真と判定してはならない。**

4. **索引固有 work ID の全要素抽出と occurrence 保存。** 返却された全要素から §5.1 の
   索引固有 work ID を抽出できなければならない。全 occurrence を頁番号・頁内 ordinal・
   日付の生値・解釈暦日とともに保存し、同じ work ID の再出現も削除せず multiplicity として記録する。
   **取得層で family key による先行 dedup を行ってはならない。**
   索引固有 work ID を持たない要素、先行 dedup、保存 occurrence 数と実要素数の不一致が
   1 つでもあれば `否` とする。

5. **索引固有 work ID による総数一致と aggregate の完走。** leaf ごとに、全頁で観測した総件数
   field が同一であり、その値が当該 leaf の **distinct な索引固有 work ID 数**と一致しなければならない。
   返却行数が同一 work ID の再出現により総件数を上回る場合も、全 occurrence と multiplicity を
   保存したうえで distinct work ID 数で判定する。
   shard を持つ枝は、**登録済み leaf がすべて完走し、leaf 間の索引固有 work ID 集合が互いに素で、
   aggregate の work ID 数が各 leaf の distinct 数の和と一致した**場合に限り完走とする。
   複数の無償枠窓にまたがった枝は、固定 shard の先頭から始めた独立第 2 走の
   sorted work-ID digest が第 1 走と一致することを追加で要求する。
   総数の drift、ID 数の不一致、leaf 間の重複、leaf の欠落、2 走 digest の不一致のいずれかがあれば `否`。
   **work-family 数・研究数・family 統合の成否をこの条件の帳尻合わせに用いてはならない。**

6. **正常終端と証拠保存。** 全 attempt が HTTPS、許可 host、status 200、期待 content type、
   byte 上限内であり、応答本文・request・安全な header・時刻・位置/cursor・digest を保存する。
   `issued` の後に結果が不明な attempt、429/503 の再試行上限到達、parse 失敗、部分書き込み、
   digest 不一致は成功にしない。

### 7.1 最上位の状態は導出する。申告を読まない

```text
retrieval_complete = 全 aggregate と全 leaf が上の 6 条件を満たす

axis_complete = retrieval_complete
                AND controls_valid
                AND supplemental_complete
                AND sensitivity_complete
                AND classification_complete
                AND family_ledger_complete
                AND 未実装の schema 層が 0 である
```

- `not_run` / `paused_quota` / `outcome_unknown` / `blocked_on_ruling` は**すべて偽側**に数える。
- `not_applicable` は、完走済みの枝と D1155 の 1 枝にだけ許す。
- **検査器は bundle が申告した `axis_complete` を読んではならない。必ず導出する。**
- `accounting_complete` (会計が揃った) と `retrieval_complete` (取得が完了した) は別の field である。
  receipt が揃っただけでは完走にならない。

### 7.2 6 条件を全部満たしても全件取得にならない場合がある

旧契約 §7.1 の限界をそのまま引き継ぐ。**同数の入れ替えは検出できない。**
3 索引とも snapshot token を提供しないので、これを構造的に排除することはできない。
登録する緩和策は次の 2 つで、**どちらも有限の監査であって証明ではない。**

- 全頁の応答証拠 (位置値・宣言件数・実要素数・work ID 列・HTTP status) を保存する。
- 複数の無償枠窓にまたがった枝は、独立した連続 2 走の work-ID 集合 digest の一致を要求する。

**0 件そのものは走行無効の理由にしない。** 正しい query が真に空集合を返すこともある。

## 8. 停止条件、無償枠、amendment (結果を見る前に固定する)

- **本検索の停止条件:** §3.6 の全 leaf を完走させたら終わり。枝を足さない。
  **「新しい候補が出る間だけ続ける」型の停止条件を禁じる。**
- **再試行上限:** 1 リクエストあたり 3 回 (バックオフ 3→6→12 秒)。超えたらその走行は `未完走`。
- **最小間隔:** arXiv 3 秒、DBLP 45 秒、OpenAlex 1 秒。**host 単位の limiter を control・枝・
  再試行で共有する。再試行の待ちが最小間隔を迂回してはならない。**
- **DBLP の切断:** 再試行上限に達したら `outcome_unknown` + `restart_branch` の再開点を発行する。
  45 分の冷却後に 1 度だけ枝の先頭から再走し、再発したらその索引を中断する。
- **無償枠:** §4.1 の credit 会計に従う。予約 (30 credit) を割る前に停止し、
  `paused_quota` の再開点を発行する。**枠切れを除外へ読み替えない。`未完走` である。**
- **予算切れ・429・503・通信失敗・再試行上限到達は、いずれも軸全体を `未完走` にする。**
  完走した枝だけを取り出して軸の成熟度を名乗ってはならない。
  部分結果から書いてよいのは、**完全に完走した単一 leaf についての内部的な取得報告だけ**であり、
  そこに不在の表現を置いてはならない。
- **死んだ式の扱い。**
  - **非意味的修繕:** **正規化 request が同一である**変更だけを指す。正規化 request は
    endpoint・検索フィールド・filter 本体・sort・頁サイズ・位置パラメータの遷移規則・
    取得フィールドの射影からなる。**解釈後 query の一致だけを根拠にしてはならない。**
  - **意味的 amendment:** それ以外すべて。旧走行を `未完走` に固定し、
    新しい日付の amendment 文書・新しい epoch・新しい query ID・全枝の再実行・独立レビューを要求する。
    **旧結果を見た後の改訂であることを明記する。**
- **shard 境界は動かさない。** 件数を見てからの再分割・境界移動・粒度変更は、
  非意味的修繕ではなく意味的 amendment である。

## 9. 母集合の外 (網羅を保証しない)

旧契約 §9 をそのまま保持する。**この一覧を成果物から落としてはならない。**

> SIGMOD / PVLDB / OSDI / SOSP などの venue 本体の年次一覧、ACM Digital Library、書籍、
> 技術報告、学位論文、非英語文献、索引化されていない実装・アーティファクト。

これに次を足す。

- **2026-12-31 より後の日付を持つレコード** (§2 の上限境界で 3 索引から落ちる)。
- **DBLP の要旨** — DBLP は要旨を索引しないので、DBLP の枝は題名 (と著者・venue) しか当たらない。
- **`AX1-20260829-E1-Q6-EXCLUSION@dblp`** — DBLP の構文では書けないため実行不能と宣言した (§3.3)。
- **旧契約 §6.3 の上限を超える引用・著者・venue の探索範囲。**
- **本文書が登録しなかった概念語。** §3.1 の語列は有限であり、語を変えれば結果は変わりうる。

## 10. 実行の記録が持つもの

**本文書に実行値を書き戻してはならない。** 実行は新しい日付の凍結物
(`claim-survey/<日付>-axis1-search-execution.md`) と証拠 bundle が持つ。

### 10.1 leaf ごと

旧契約 §10 の field を引き継ぎ、次を足す。

| field | 中身 |
|---|---|
| `registration_commit` | 本改訂と catalog を封じた commit の 40 桁 SHA |
| `logical_query_id` / `leaf_query_id` | aggregate と leaf を区別する |
| `index_work_ids` | 索引固有 work ID の全 occurrence (頁番号・ordinal・日付の生値・解釈暦日つき) |
| `distinct_index_work_ids` | distinct 数 |
| `primary_key_digest` | distinct 索引固有 work ID 集合の digest |
| `ledger_sha256` | 台帳 file 自体の SHA-256 (`primary_key_digest` とは別 field) |
| `capacity_echo` / `actual_count` | 頁ごとに別 field で保存する |
| `quota` | 応答ごとの limit / remaining / credits used / cost / reset の観測値と観測時刻 |
| `completion` | §7 の 6 条件それぞれの成否と**条件別の理由コード** |

### 10.2 再開点 (D1183) — 必須

無償枠や転送制限で 1 セッションに収まらない取得は、証拠 bundle の `checkpoints/<連番>.json` に
再開点を置く。枝ごとに次を持たせる。

- `run_id` / `pass_number` / `window_number` / `state`
- `resume_action` — `continue_cursor` / `start_independent_pass` / `restart_branch` /
  `blocked_on_ruling` / `not_applicable` の 5 値。**増やさない。**
- **cursor を継ぐ場合と、独立した 2 走目を始める場合の、完全な request を 2 本とも**
- 完了済み台帳の path、`ledger_sha256`、`primary_key_digest`。
  2 走目があればその digest と一致の可否
- 枝別に待っている裁定の ID、無償枠の観測時刻と残量
- `registration_commit` / catalog の path と SHA-256 / bundle root / 対象 leaf ID / 正規 runner argv

**「窓をまたいで cursor を継ぐ」と「独立 2 走目を先頭から始める」は別状態として区別する。**
`state` と `resume_action` の合法な組合せを行列で定め、非合法な組合せを拒否する。
**未開始の枝に `not_applicable` を許してはならない。**

旧 bundle の `checkpoints/0001.json` は `AX1-Q3@openalex` / `AX1-Q6@openalex` を
`blocked_on_ruling` (U1・U2・U6 待ち) で残している。**D1207 がその裁定を与えたので、
本改訂の後継 checkpoint はこの 2 枝を `superseded` とし、`restart_branch` で新 ID から取り直す。
旧 bytes は変更しない。**

### 10.3 DBLP は 2 つの判定を併記する

DBLP の全枝について、実行記録は次の 2 つを別 field で持つ。

- `completion_under_registered_tokenizer` — §3.5 の規則で判定した結果。
- `completion_under_legacy_literal_echo` — 旧契約 §3.5 の逐語期待で判定した結果。

**どちらを正とするかは人間の裁定に委ねる** (§13 の U7)。本改訂の下でも軸 1 は `未完走` であり、
下流の値はどちらでも変わらない。

### 10.4 証拠 bundle

- `manifest.json` は file ごとの SHA-256 で束縛する。**自分自身と `MANIFEST.sha256` を列挙しない**
  (自己参照を作らないため)。
- `manifest の path 集合 == bundle 内の regular file − {manifest.json, MANIFEST.sha256, README.md}`
  を機械検査する。
- 応答本文は gzip で保存する。1 頁の byte 上限は 16 MiB。

## 11. 登録前に親が目にしたもの (事前知識の開示)

旧契約 §11 の開示をそのまま引き継ぐ。**本改訂に固有の開示は次のとおり。**

1. **旧走行の全枝の宣言件数・完走判定・失敗の内訳を見た。** これが §3.4 の shard 設計、
   §4.1 の credit 会計、§7 の条件 3〜5 の条文に影響している。**§0.1 に表として開示した。**
2. **旧走行の DBLP の実 echo (`two* phase* locking*`、`multi* version* concurrency* control*`) を見た。**
   §3.5 の規則はこの後に書いた。規則自体は中立語 probe で再現できるが、影響経路は存在する。
3. **本日、3 索引へ中立語で probe を出した** (§4.2、§4.3、§4.4)。
   軸 1 の登録 query は 1 本も叩いていない。
4. **旧 bundle の `checkpoints/0001.json` を読んだ。** §10.2 の後継 checkpoint 設計に影響している。

**因果的影響がなかったと断定はしない。**

## 12. この改訂自身の限界

旧契約 §12 の限界を引き継ぎ、次を足す。

- **無償枠の窓の長さを測っていない。** 観測したのは reset 秒数と remaining の減り方だけである。
  日数の見積りはすべて「旧件数を使った planning estimate (失敗無しの baseline)」であり、
  上界ではない。件数の drift・再試行・共有単位の消費で増えうる。
- **arXiv の 10,000 件天井は 2 つの query についての観測である** (旧記録 §4.3)。API 仕様の確認ではない。
- **`itemsPerPage` / `meta.per_page` が要求値のエコーであるという観測は、旧走行の 10 枝と
  本日の probe の範囲である。** 恒久的な API 契約としては断定しない。
- **登録 commit が証明するのは、固定 commit の bytes と、その commit を要求する runner が
  発行した request の関係だけである。** 人間が別の client で事前に閲覧していないこと、外部の時刻、
  索引の snapshot は証明しない。
- **D1208 の 3 経路のうち README 導線が本改訂では未充足である。**
  `docs/related-work/claim-survey/README.md` と `docs/related-work/README.md` 7.7 は、
  並行する軸 3 の amendment 作業と編集面が重なるため本変更単位では触らない。
  **本文書は README の一覧に載らない。** 軸 3 側の着地後に別の変更単位で閉じる必要がある。
- **分類・work-family 統合・control・補助探索・感度監査の schema 層は本改訂では実装しない。**
  §7.1 の導出式により、未実装層がある限り `axis_complete` は偽である。
- **本改訂は独立レビューを受けている** — 段 3 の敵対相談 2 本と段 6 のレビューが検査した。

## 13. 人間の裁定へ返す項目

| ID | 問い |
|---|---|
| U7 | DBLP の期待 echo を §3.5 の実測トークン化規則にするか、旧の逐語期待を保って `T05` / `T07` を `未完走` に残すか。**本文書は決めていない。実行記録が両方の判定を併記する。** |
| U8 | D1208 の README 導線 (§12) を、軸 3 側の着地後にどの変更単位で閉じるか。 |
| U9 | `axis_complete=false` の bundle から論文 §3 へ値が流れる経路を、report checker と `docs/paper-story/` 側でも塞ぐか。本改訂は実行記録の規範文だけを置いている。 |
