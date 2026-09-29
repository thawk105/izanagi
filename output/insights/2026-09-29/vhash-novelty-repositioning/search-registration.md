# 検索の事前登録 (逐語)

- 出典: job dir の handoff を取得前に複製した凍結写し 2 つ。本 file は各写しの該当節を加工せずに切り出したもの。
- 凍結写し 1: `registration-frozen-0922.md` (SHA-256 `f493f0091e044d89992bab07d6af726534e5aecdce806652f3be465f56fd2458`、複製 2026-09-29 09:21:35 JST)。見出しの「09:22」は記入時の予定時刻で、実際の凍結はこの複製時刻。
- 凍結写し 2: `registration-addendum-1008.md` (SHA-256 `1199003acf968635ee82f67d8dbddf9e4b7c4c8e253fcbd9bc0df29e90057cfb`、複製 2026-09-29 10:07:52 JST)。登録節 (下の 1) は写し 1 と 1 字も違わない (diff で確認)。追記は下の 2 だけ。
- **訂正 (逐語は変えず、ここで訂正する):** 1 の冒頭の「OpenAlex 構文確認 12 本 (… 6 本は 429)」は数え違いで、生ログ (`probe/syntax_probe.log`・`syntax_probe2.log`) では
  12 本のうち 429 が 8 本、400 (語尾の `*` を受け付けない) が 1 本、200 が 3 本だった。arXiv の生死確認は http→https の転送を含めて 2 本、
  DBLP は検索 API 1 本に加え、書き出しの HEAD 3 本・先頭 64 KiB の部分取得 1 本・release 一覧 1 本を出した。いずれも本走の結果とは無関係の語か、コーパスそのものの取得である。

## 1. 事前登録 (写し 1 の該当節)

これより前に出した request は、(i) 主題と無関係の語 ("cache coherence"・snoop) による OpenAlex 構文確認 12 本 (probe/syntax_probe*.log、6 本は 429)、(ii) arXiv の生死確認 1 本 (同じ無関係語)、(iii) DBLP 検索 API の生死確認 1 本 (無関係語、bot 判定 HTML を確認)、(iv) DBLP 書き出しの取得、だけである。

### 索引
- **OpenAlex**: `https://api.openalex.org/works?filter=title_and_abstract.search:<Q>&per-page=200&cursor=<c>&select=id,doi,display_name,publication_year,type,primary_location,abstract_inverted_index`。cursor 終端まで。検索対象 = 題名 + 要旨 (OpenAlex の語幹化あり、句は語幹化した句)。構文 AND / OR / 括弧 / "句" (09:1x の構文確認で OR・AND・句の効きを確認)。実要素数 = `results` の個数、distinct `results[].id` を `meta.count` と照合。cutoff = 各 page の取得時刻
- **arXiv**: `https://export.arxiv.org/api/query?search_query=<Q_arxiv>&start=<n>&max_results=200&sortBy=submittedDate&sortOrder=ascending`。フィールドは `all:` (題名・要旨・著者・コメント等)。実要素数 = `feed/entry` の個数、宣言総数 = `opensearch:totalResults`。要求間 3 秒以上
- **DBLP**: 全件書き出し `https://dblp.org/xml/dblp.xml.gz` (1,106,838,299 bytes、SHA-256 4ed8c4614244b755…、Last-Modified 2026-09-28 20:23:37 GMT、取得 2026-09-29 09:16〜09:18 JST)。対象レコード = article / inproceedings / incollection / book / phdthesis / mastersthesis (proceedings・www は除く)。**検索対象は title 要素だけ** (DBLP は要旨を持たない)。照合: title を NFKC・小文字化・非英数字で分割した語列にし、検索式の各語は「語の前方一致」(DBLP 検索 API の既定と同じ向き)、"句" は連続する語の前方一致列、AND / OR / 括弧は論理どおり。版 = 書き出しの SHA-256 と Last-Modified
- 3 索引で同じ検索式 (論理構造と語) を使う。arXiv は各語を `all:` に展開する (句は `all:"..."`)

### 概念ブロック
- TS (tx の直列化位置を動かす): `(timestamp AND (forward OR forwarding OR advance OR adjust OR adjustment OR reassign OR reassignment OR shift)) OR "serialization order" OR "timestamp range" OR "timestamp interval" OR "dynamic timestamp" OR "order forwarding" OR "commit timestamp"`
- MV (多版): `multiversion OR "multi-version" OR MVCC OR "version chain" OR "old version" OR "older version"`
- GC (版の回収・保持): `"garbage collection" OR reclamation OR "version retention" OR "version pruning" OR watermark`
- LT (長い tx): `"long-running transaction" OR "long-running transactions" OR "long transaction" OR "long transactions" OR "long-lived transaction" OR "long-lived transactions"`
- PL (版の物理位置・アクセスコスト): `hot OR cold OR "cache miss" OR "cache misses" OR "memory access" OR "version search" OR "version traversal" OR inlining OR "version storage"`
- CX (文脈): `concurrency OR serializability OR serializable OR transaction OR transactions OR database`

### 検索式と主張の対応 (主張 ID は md_1 §8.3)
| ID | 式 | 支える主張 |
|---|---|---|
| N01 | (TS) AND (GC) AND (CX) | U0 |
| N02 | timestamp AND "garbage collection" AND (CX) | U0 |
| N03 | (LT) AND (MV) | U0 |
| N04 | (LT) AND (GC) | U0 |
| N05 | ("garbage collection" OR reclamation) AND (MV) | U0 |
| N06 | (TS) AND (PL) AND (MV) | U1, U2 |
| N07 | "version chain" AND timestamp | U1 |
| N08 | (MV) AND ("cache miss" OR "cache misses" OR "memory access" OR "version search" OR "version traversal") | U1 |
| N09 | (TS) AND ("old version" OR "older version" OR "stale version" OR "previous version" OR "earlier version" OR "non-latest") AND (CX) | U2 |
| N10 | ("timestamp range" OR "timestamp interval" OR "dynamic timestamp" OR "order forwarding" OR "serialization order") AND (CX) | U2 |
- 主張 Ux を「見当たらなかった (範囲: …)」と書けるのは、対応する式が **3 索引すべてで完走し、検出 0 かつ要裁定 0** のときだけ。1 つでも未完走・要裁定・検出があれば未確定 (または既知)
- U3 (本案 (4)) は md_1 §8.3 のとおり U1・U2 に従属するので検索を割り当てない

### 陽性対照 (既知アンカー。欠けたらその索引・式の偽陰性として記録し、その式を根拠にした文に併記する)
| 対照 | 期待する式 | 期待する索引 |
|---|---|---|
| Lomet ほか 2012 "Multi-version Concurrency via Timestamp Range Conflict Management" | N10 | OpenAlex・DBLP |
| Böttcher ほか 2019 Steam "Scalable Garbage Collection for In-Memory MVCC Systems" | N05 | OpenAlex・DBLP |
| Lee ほか 2016 SAP HANA "Hybrid Garbage Collection for Multi-Version Concurrency Control in SAP HANA" | N05 | OpenAlex・DBLP |
| Bayer ほか 1982 "Dynamic Timestamp Allocation for Transactions in Database Systems" | N10 | OpenAlex・DBLP |
| Konana ほか 1997 OCC-TI "Updating timestamp interval for dynamic adjustment of serialization order ..." | N10 | OpenAlex・DBLP |
| Kim ほか 2020 vDriver "Long-lived Transactions Made Less Harmful" | N03 | OpenAlex (要旨経由)。DBLP は題名に MV の語が無いので出ないのが期待 |
| Tanabe ほか Shirakami (arXiv 2303.18142) | N03 または N10 | arXiv |

### 判定規則 (1 レコード 1 判定、触れる主張を併記)
- 検出 (Ux): tx の直列化位置 (timestamp・区間・epoch) を **abort せず既読を保って**動かし、かつ U0: その移動を版データの回収境界・保持に反映する / U1: その移動の契機が版の物理位置・アクセスコスト (hot・cold・cache miss・記憶階層) / U2: 前へ (後の時刻へ) 動いて最新でない版を選んで読む、のどれかを示すもの
- 近傍 (Ux): 構成要素の一部だけ (例: timestamp 調整だが GC に結ばない、長い tx の GC だが tx の位置を動かさない)
- 除外 (理由コード): X1 分野外 (DB・tx・並行性制御でない。題名と掲載先の両方で判断)、X2 DB だが本主題と無関係 (索引・問合せ最適化等)、X3 tx の位置を動かさず本案の要素にも触れない、X4 同じ研究の別版 (既に判定した ID を記す)
- 要裁定: 要旨が無く題名と掲載先で X1/X2 と決められないもの、要旨を読んでも決められないもの。要旨を別経路 (OpenAlex 単体取得・Crossref・Semantic Scholar) で取れたら再判定、取れなければ要裁定のまま
- 1 次判定は子 (sonnet) に規則を渡して行わせてよい。親は全レコードの題名一覧を見て、検出・近傍・要裁定・X3 の全件と、X1・X2 から疑わしいものを要旨で再判定する。親と子の判定が割れたら親の判定を採り、割れた件数を記録する

### 打ち切り・再試行
- 1 式 1 索引の宣言総数が 800 を超えたら全件判定せず `未完走 (過大)` とし、対応主張は未確定。後から語を狭めた式を足す場合は別 ID (N11〜) とし理由と時刻を残す
- OpenAlex の 429 は `retryAfter` + 5 秒待って同じ request を再送 (最大 5 回)。各試行を記録し、採るのは 200 の応答。5 回で取れなければその式は未完走。5xx・空ボディ・JSON でない応答も未完走
- OpenAlex の request 予算: 本走 80 本以内 (無料枠 1000 credit、絞り込み 1 本 10 credit)。超えそうなら残りを次の窓へ送り、その式は未完走のまま記録
- arXiv: 429・503・空ボディ・totalResults 欠落は未完走。要求間 3 秒以上
- 停止条件は以上で固定。結果を見て判定規則を変えない


## 2. 登録の追記 (写し 2 の該当節)

- OpenAlex 1 走目 (09:49〜10:07、request 35): N01〜N07 complete、N08〜N10 は 5 試行とも 429 で incomplete
- 再走規則: N08〜N10 を**式を変えずに**同じ取得器で再走する (R2)。1 走目の証拠は search/openalex/ に残し、R2 は search-r2/ に書く。R2 は 10:18 以降に 1 式ずつ (--only) 直列に起動。
  R2 でも incomplete の式は 10 分空けて R3 を 1 回だけ (search-r3/)。R3 でも incomplete ならその式は未完走で確定し、対応主張は未確定
- OpenAlex の request 総数は 1 走目 + R2 + R3 で 80 以内 (各走の取得器の予算は 80 固定なので、親が走ごとの使用数を足して超えないよう止める)
- 判定には、各式について最後に complete になった走の結果を使う。1 走目で complete の N01〜N07 は再走しない

