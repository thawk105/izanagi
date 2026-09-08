# 段 4 裁定 — [T-2380] (2026-09-08 08:05 JST)

## 段 3 所見の裁定 (real / refuted、採否、scope)

| 所見 | 判定 | 採否 | 反映先 |
|---|---|---|---|
| A-1 (E-1 が非収録を見てから control を外せる) | real | 採用。索引別 control 集合を lookup 前に鍵型と索引の収録範囲だけで固定し、集合の全 anchor が `収録` かつ包含でなければ `未完走`。`非収録` を見て除外しない。control ID `B5-ANC-<anchor>@<索引>` を新設 | 1/2 §2.4、§2.5 E-1 |
| A-2 (通りやすさで選んだ) | refuted | — | — |
| A-3 (凍結語彙で届きにくい anchor が多数) | real | 部分採用。各 anchor に「届くと想定する枝と語」列を足し、G2 は C 語の想定なしと明記。anchor の差し替え・役割分割はしない (通りやすさで選ばない規則の帰結)。G2 の包含枝がすべて C を要求する構造的懸念はユーザーへ裁定パッケージとして返す | 1/2 §2.1、§2.2、§7、最終報告 |
| A-4 (選定規則の裁量) | real | 採用。§5.4 の「旧契約を `未完走` に固定・開示・新 ID・全枝再実行」を §2.1 に逐語継承 | 1/2 §2.1 |
| A-5 (名称を主キーにしている) | refuted | — | — |
| A-6 (訂正識別子・版・alias・landing page) | real | 採用。候補発見は Crossref `query.bibliographic` 等で可、固定は登録機関 record か arXiv API record で全書誌を確認できた場合だけ。版 (`type`、preprint/出版版、arXiv 版番号) と名称 alias を record に置く。landing page だけの確認は `要裁定` | 1/2 §2.3 |
| A-7 (実行前 = live preflight) | refuted (E-2 維持) | — | — |
| A-8 / B-17 (DBLP 全 anchor 不達の書き方) | real | 採用。「anchor 固有 request 未送信、共有 endpoint の環境 preflight が challenge」と粒度を明記 | 1/2 §2.4、§6、2/2 |
| A-9 (実測の一般化が広い) | real | 採用。exact request に狭め、`鍵不適用` は本文書が登録する request 形に相対的と定義。未検証の OpenAlex 経路を「検証すべき経路」として列挙 | 1/2 §2.4、§6、§7 |
| A-10 (全頁取得後の辞書順) | refuted (維持) | — | — |
| A-11 / B-16 (上限の意味、全 record 台帳、非収録起点の適用不能、同順位) | real | 採用。上限 = 採用集合の上限。正常終端まで取得し採用集合だけ切る。採用外は生証拠のみで候補にしない。起点集合は lookup 前に全 16 件で固定し、OpenAlex で `収録` でなければ stream `未完走` (適用不能は廃止)。全順序 = (DOI または OpenAlex ID、OpenAlex work ID) | 1/2 §4 |
| A-12 (規律 2) | real | A-1・A-11 の採用で閉じる。開示文を保つ | 1/2 §0、§2.5 |
| B-1 | refuted | — | — |
| B-2 (venue builder の契約) | real | 採用。`_dblp_url(q_encoded)` は符号化済み q を受ける。venue q は literal template から作る | 1/2 §3.4、実装 prompt |
| B-3 (実行順と catalog 配列順) | real | 採用。実行順は §5.3 で一意、catalog の配列順は直列化順であり実行器が索引別に query ID 辞書順へ sort する | 1/2 §3.4 |
| B-4 (OpenAlex 複数語の意味) | real | 採用。bytes は一意、意味は live preflight の検証点として §3.4 に残す | 1/2 §3.4 |
| B-5 (byte 単位で未決の点) | real | 採用。§3.4 に全部固定してから commit | 1/2 §3.4 |
| B-6 | refuted | — | — |
| B-7 (test の独立 literal) | real | 採用。arXiv / OpenAlex / control / venue の期待 URL を test 側 literal にする。production helper で期待値を作らない | 実装 prompt |
| B-8 (変異 5・8 の oracle) | real | 採用。変異 5 の primary oracle は request 内語順の literal test、変異 8 は `_term_id()` seam を定義 | 変異事前登録 |
| B-9 | refuted | — | — |
| B-10 (control の group 構造、DBLP echo の総関数) | real | 採用。`queries[]` と `controls[]` に `term_groups` (group 内 OR、group 間 AND) を置く。期待 echo は置かず、導出規則を §3.4 に固定 | 1/2 §3.2、§3.4 |
| B-11 | refuted | — | — |
| B-12 (author_position) | real | 採用。`author_position` が `first` / `last` と配列位置の一致を要求、不一致・欠落は `要裁定` | 1/2 §4 |
| B-13 (後方引用の完走述語) | real | 採用。`select=id,referenced_works,referenced_works_count` とし、配列長 == `referenced_works_count` を条件 5 相当に、条件 6 を要求。条件 2・3 は 1 request なので該当なし、と明記 | 1/2 §4 |
| B-14 (不達時の slot 配置、§5.2 への射程) | real | 採用。`不達` と control 集合 member の `非収録` は「当該索引の走行と軸全体を `未完走`、当該 slot の control を未配置」に戻す。E-1 の射程に §4.2 項目 3・§4.3・§5.2 を明記 | 1/2 §2.4、§2.5、§7 |
| B-15 (3 経路を gate 閉鎖前に凍結) | real | 採用。1/2 は形 (symbolic template) の登録、2/2 が anchor ごとの stream を確定する、と役割を分ける | 1/2 §4 |
| B-18 (新規 test file のメタテスト) | real | 採用。`__main__` harness を持たせる。受入台帳の被覆は全走で確認 | 実装 prompt、段 6 |
| B-19 (lint の射程) | real | 採用 (記述の限定)。README 一覧行の追加漏れは親が目視 | 段 7 |
| B-20 (§3.4 の placeholder) | real | 採用。commit 前に埋め、未来形を除く | 1/2 §3.4 |

## plan の曖昧点の読み (§3.4 へ書く)

1. 単一 operand control は singleton block。arXiv `(abs:"backoff") AND submittedDate:[...]`、OpenAlex `(backoff),to_publication_date:...` (percent encoding 前)。
2. `X OR Y` は 1 group 2 語、`X AND Y` は singleton group 2 個。
3. JSON surface: top-level 11 field。`blocks[]{block_id,terms[]{term_id,term}}`、`branches[]{branch_id,block_ids}`、`queries[]{query_id,index,branch_id,term_groups,request_template,first_page_url}`、`controls[]{control_id,index,term_groups,request_template,first_page_url,shares_request_with}`、`aux_venue_streams[]{stream_id,index,venue,year,request_template,first_page_url}`。
4. list 順: 登録表順。queries は arXiv Q1..Q10、OpenAlex Q1..Q10、DBLP は Q4..Q10 の枝順で左語外側・右語内側。
5. `schema_version` = `izanagi-axis-b5-search-catalog/v1`。`registration_blob` = 小文字 40 桁。
6. `expected_cardinalities` = blocks 6 / terms 85 / branches 10 / arxiv_queries 10 / openalex_queries 10 / dblp_queries 1602 / queries 1622 / controls 14 / aux_venue_streams 272。
7. `shares_request_with` は全 control に置き通常 `null`。
8. CLI: `--output` と `--verify` は排他かつどちらか必須。不一致・読取不能は rc=1。診断文は seal 対象外。
9. `B5-CTL-AND2023@arxiv` は `submittedDate:[199101010000 TO 202312312359]`、`@openalex` は `to_publication_date:2023-12-31`。
10. DBLP 期待 echo の導出規則 (catalog に置かない): 送信語を空白とハイフンで分割し各 token に `*` を付ける。大文字小文字は送信どおり (登録値、未観測)。
11. venue stream: q は literal `venue%3A<venue>%3A%20year%3A<year>%3A`、`_dblp_url` は符号化済み q を受ける。

## 変異事前登録 (実装後に node を確定、probe → 本走)

| # | 位置 | 変異 | primary oracle (独立 literal test) |
|---:|---|---|---|
| 1 | `_percent_encode` | `quote` → `quote_plus` | DBLP 照合例 literal |
| 2 | `_percent_encode` | OpenAlex safe から `,` を外す | OpenAlex literal |
| 3 | `_openalex_filter` | 複数語を `"` で囲む | OpenAlex literal |
| 4 | `_arxiv_expression` | `abs:"..."` の quote を落とす | arXiv literal |
| 5 | 語順 seam (`_term_records` or block tuple) | block 内語順を sort | arXiv Q1 literal (語順) |
| 6 | DBLP 直積 | `product` → `zip` | 直積件数 test |
| 7 | DBLP 対象枝 | Q3 を追加 | 件数・ID test |
| 8 | `_term_id` | `T01` → `T1` | 語 ID literal test |
| 9 | control | AND2023@dblp に year param | 共有 bytes test |
| 10 | venue | `range(1993, 2026)` | venue literal/件数 test |
| 11 | `render_catalog_json` | 末尾 `\n` を除く | canonical bytes test |
| 12 | `_verify` | bytes 比較 → `json.loads` 比較 | verify 1 byte 改変 test |
| 13 (等価、SURVIVED 期待) | 任意 | `list(x)` → `[*x]` 等の等価変換 | なし (harness の SURVIVED 正例) |

## 裁定パッケージ (ユーザーへ返す、本 wave では実装しない)

- G2-SA の包含枝 (`B5-Q3`/`Q6`/`Q7`/`Q8`) はすべて C block を要求するが、G2 の既知メンバー (Robbins–Monro、Kiefer–Wolfowitz、Kesten、SPSA、適応 sampling) の題名・要旨は登録 C 語 (`update interval` 等) を含まない見込み。
  現行のまま実行すると G2 の包含 control が不発 → 軸 `未完走` → §5.4 の語彙 amendment、が既定の経路。実行前に語彙 amendment (別 wave) を選ぶ余地はあるが、本 wave の scope 外。
