# 親の実測 (dev-wave [T-2448])

凍結文が定めていない実行器の運用値を裁定するために、親が本 wave で実測した事実。
**新しい外部 request は 1 本も出していない。** 出所は前 wave が保存した生応答 (`output/insights/2026-09-08_t2380-b5-closure/probe/`) と、
本 wave の名前解決 probe だけである。

## 1. 名前解決 (2026-09-09、login node `pegasus02`)

| host | 解決結果 |
|---|---|
| `api.openalex.org` | `104.20.26.229` |
| `export.arxiv.org` | `199.232.163.42` |
| `dblp.org` | `192.76.146.204` |

DNS のみ。HTTP request は出していない。3 索引への経路が login node から存在することの最安の生死確認である
(HTTP 層の可用性は下記 2 の 2026-09-07 観測が最後の実測)。

## 2. 保存済み生応答の header (2026-09-07 取得、前 wave の `probe/`)

| 応答 | HTTP | `content-type` |
|---|---|---|
| arXiv `id_list` 命中 (`ax_known`) | 200 | `application/atom+xml; charset=utf-8` |
| arXiv `id_list` 不在 (`ax_missing`) | 200 | `application/atom+xml; charset=utf-8` |
| OpenAlex 命中 (`oa_ccbench`) | 200 | `application/json` |
| OpenAlex 不在 (`oa_missing`) | 404 | **`text/html; charset=utf-8`** |
| DBLP API (`dblp_api_doi`) | 200 | `text/html; charset=utf-8` (body は anti-bot challenge の HTML) |

**この表が裁定に効く点:**

1. arXiv の media type は `application/atom+xml` で、`charset` parameter が付く。
   content type の照合は media type だけを見て parameter を無視しなければ、正常応答を落とす。
2. **OpenAlex の `非収録` (404) は `text/html` を返す。** 閉包登録 1/2 §2.4 (b) の `非収録` は
   「HTTP 404」だけを条件にしており content type を条件にしていない。実装が content type 検査を
   status 判定より先に置くと、**登録どおりなら `非収録` になる応答が `不達` に化ける。**
   3 値の判定順序は status を先に見る形でなければならない。
3. DBLP の `不達` は「HTTP 200 だが content type が `text/html`」の形で現れる。
   status だけでは `不達` を検出できないので、DBLP は content type と body 形の両方を見る必要がある。

**限界:** これは 2026-09-07 の 1 時点の観測であって、live preflight 時点の索引の振る舞いを保証しない。
部分登録 §2.3・§5.3 に従い、**この観測を登録済みの期待値へ据えることはしない。**
ここで使うのは、凍結文が定めていない実装側の運用値 (content type の照合方法、3 値の判定順序) を決めるためだけである。
実行器が実際に観測した値は毎回そのまま実行記録へ保存する。
