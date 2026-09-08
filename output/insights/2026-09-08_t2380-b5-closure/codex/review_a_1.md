## 所見

表記: P = 部分登録、C = 後継凍結物、I = 実装、T = test、J = 生成 catalog。

**RA-01 — refuted: 85 語の逐語不一致はない。**

P の語列 [P:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:159) と I の `BLOCKS` [I:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:33) を block・位置ごとに比較した。

| block | 照合位置 | 結果 |
|---|---:|---|
| T | T01〜T12 | 12/12 exact |
| M | M01〜M19 | 19/19 exact |
| O | O01〜O10 | 10/10 exact |
| C | C01〜C21 | 21/21 exact |
| W | W01〜W13 | 13/13 exact |
| V | V01〜V10 | 10/10 exact |

大文字の `STM`、`SPSA`、`back-off`、`finite-difference gradient`、`run-time window selection`を含め、表記・ハイフン・語順・block 所属に差はない。J でも T から V の順で始まる [J:2180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2180)。

推奨対応: なし。

**RA-02 — refuted: P §3.3 規則 1〜7 は、採用済みの読みの範囲では一致する。**

| 規則 | 実装箇所 | 生成物での確認 |
|---|---|---|
| 1. 語順 | `BLOCKS` と列挙順の `enumerate` [I:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:33)、[I:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:190) | `blocks` [J:2180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2180)、Q1 の T01 始まり [J:2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2837) |
| 2. block 順 | `BRANCHES` [I:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:151)、block から group を作る [I:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:307) | `branches` の Q1〜Q10 [J:2559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2559) |
| 3. arXiv | `abs:"..."`、OR/AND、日付節 [I:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:222)、encoding と template [I:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:255) | Q1 の完全 URL と literal `{POS}` [J:2833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2833) |
| 4. OpenAlex | 引用符なし、OR/AND、filter [I:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:236)、comma 保存 [I:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:268) | Q1 で `,` は literal、`:` は `%3A`、初回は `cursor=*` [J:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:3330) |
| 5. DBLP | 生の空白で連結後、一度だけ quote [I:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:250) | 登録例は `%20`、`%2520` なし [J:26057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:26057) |
| 6. parameter 順 | arXiv、OpenAlex、DBLP の template [I:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:261)、[I:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:275)、[I:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:282) | 上記 3 entry で登録順どおり |
| 7. query/term ID | 2 桁 ID [I:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:177)、索引別 ID [I:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:307) | `B5-Q10@dblp/T01-O01` [J:26059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:26059) |

`{POS}` / `{CUR}` は encoded value の外に組み立てられ、初回 cursor だけ `*` に置換される [I:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:263)、[I:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:277)。推奨対応: なし。

**RA-03 — refuted: C §3.4 項目 1〜12 の指定済み部分は一致する。**

| 項目 | 実装箇所 | 生成物での確認 |
|---|---|---|
| 1. singleton | `x_group` / `y_group` [I:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:367) | arXiv X は `[[M01]]` [J:2630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2630) |
| 2. OR / AND group | `((x,y),)` と `((x,),(y,))` [I:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:370) | OR [J:2654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2654)、AND [J:2667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2667) |
| 3. AND2023 | 2023 cutoff と DBLP share [I:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:377)、[I:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:393) | arXiv [J:2682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2682)、OpenAlex [J:2749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2749)、DBLP share [J:2803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2803) |
| 4. 配列順 | tuple、索引 loop、直積、control、venue loop [I:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:33)、[I:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:307)、[I:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:367)、[I:413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:413) | SIGMOD-1993 が先頭 [J:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:3)、DISC-2026 が末尾 [J:2171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2171) |
| 5. metadata | 定数 [I:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:17)、document [I:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:432) | blob/path/schema [J:27856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:27856) |
| 6. cardinality key | literal object [I:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:452) | 全 9 key [J:2819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2819) |
| 7. percent encoding | exact safe 集合 [I:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:217) | OpenAlex の comma と cursor [J:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:3330) |
| 8. DBLP 一度だけ | 生語連結後に単一 `_percent_encode` [I:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:250) | Q10 照合例 [J:26057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:26057) |
| 9. term をそのまま使用 | arXiv/OpenAlex の直接展開 [I:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:222)、[I:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:236) | `STM`、`SPSA`、ハイフン形を保持する Q1 [J:2833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2833) |
| 10. DBLP echo を置かない | query entry の閉じた field 集合 [I:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:289) | DBLP entry に echo field なし [J:26055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:26055) |
| 11. venue literal q | encoded literal を直接組立て [I:413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:413) | SIGMOD-1993 [J:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:4) |
| 12. 語 ID | `_term_id` [I:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:177) | T01 [J:2185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:2185) |

推奨対応: 指定済み部分への変更は不要。

**RA-04 — real、must-fix: `index` の JSON 値と一部 main query ID の索引表記が byte 単位で固定されていない。**

C は entry に `index` を要求する [C:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:271) 一方、許可された読みの一覧 [C:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:300) は値を `"arxiv"` / `"openalex"` / `"dblp"` とするとは定めていない。P の main query ID 規則も `<索引>` の置換表記を明示せず、DBLP 例だけが literal `dblp` である [P:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:241)。

I は lower-case 値と suffix を選んでいる [I:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:307)、[I:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:331)、J も `"index": "openalex"` である [J:3331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:3331)。これは妥当そうな選択ではあるが、byte 契約から一意には導けない。

推奨対応: 現在の lower-case 表現を既成事実として承認せず、親の明示裁定後に I・T・J を同時に揃える。凍結済み文書の変更は提案しない。

Catalog bytes への影響: 少なくとも 1622 query + 14 control + 272 venue = 1908 個の `index` 値、裁定次第では arXiv/OpenAlex の main query ID 20 個も変わり、catalog 全体の digest が変わる。

**RA-05 — real、must-fix: `aux_venue_streams[].year` の JSON 型が未登録である。**

C は `year` field を要求するだけで型を定めていない [C:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:276)。P の「4 桁」は stream ID と URL の `<year>` に対する指定であり [P:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:490)、JSON field が number `1993` か string `"1993"` かは固定しない。

I は `range` の整数をそのまま格納し [I:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:415)、J は number にしている [J:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json:9)。

推奨対応: number/string の親裁定を受けてから I・T・J を揃える。凍結済み文書の変更は提案しない。

Catalog bytes への影響: 272 個の `year` 値すべて。string が選ばれれば引用符が加わり、digest が変わる。

**RA-06 — refuted: RA-04/RA-05 以外に、未登録の語変換・endpoint・parameter は見つからない。**

`_term_text` は登録語を直接返し [I:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:201)、trim、大文字化、空白正規化、term sort を行わない。endpoint は P の 3 本と一致する [I:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:29)。URL builder に追加 parameter もない [I:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:255)。

推奨対応: RA-04/RA-05 の解消以外は不要。

**RA-07 — refuted: catalog bytes の network・時刻・環境・cwd・locale・hash seed 依存はない。**

imports は stdlib の引数処理・列挙・JSON・Path・quote に限られる [I:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:9)。配列は tuple、固定 loop、`range`、`product` から作られ [I:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:307)、hash 順で反復する set はない。`dict(BRANCHES)` は key lookup にしか使われない。object key は `sort_keys=True` で固定される [I:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:466)。

生成物の全 string 値を機械抽出した範囲では非 ASCII は 0 件だった。`ensure_ascii=False` でも現在の入力から非 ASCII bytes は出ない。cwd は相対 `--output` の置き場所だけに影響し、`render_catalog_json()` の内容には入らない。

推奨対応: なし。

**RA-08 — real、test must-fix: 17 test のうち 3 本に production 由来の期待値があり、3 本は未登録の index/year literal を正解としている。**

| test | 判定 |
|---|---|
| `test_catalog_metadata_and_field_surface_match_contract` [T:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:274) | 独立 literal。entry の key surface は検査するが index 値/year 型は固定しない |
| `test_blocks_match_frozen_terms_order_counts_and_disjointness` [T:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:302) | 独立 literal |
| `test_term_ids_match_frozen_two_digit_literals` [T:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:315) | 独立 literal。`_term_id` は検査対象であり期待値ではない |
| `test_branches_match_frozen_block_order` [T:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:326) | 独立 literal |
| `test_main_query_ids_order_and_cardinalities_are_exact` [T:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:335) | count/order は独立。ただし lower-case `index` literal [T:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:350) は RA-04 の未登録選択 |
| `test_dblp_cartesian_branch_counts_bounds_and_request_bytes_are_exact` [T:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:358) | 独立 literal/property |
| `test_arxiv_q1_full_url_preserves_frozen_terms_order_quotes_and_cutoff` [T:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:387) | 独立の完全 URL |
| `test_openalex_q1_full_url_is_unquoted_and_keeps_comma_unencoded` [T:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:396) | 独立の完全 URL |
| `test_dblp_q10_frozen_example_is_encoded_once` [T:405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:405) | 独立の完全 URL |
| `test_controls_match_frozen_ids_groups_and_all_full_urls` [T:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:414) | ID/group/URL は独立。ただし lower-case index 列 [T:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:417) は未登録 |
| `test_dblp_and2023_shares_exact_request_bytes_only_with_dblp_and` [T:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:425) | 独立した関係制約 |
| `test_aux_venue_streams_have_frozen_range_order_ids_and_full_urls` [T:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:435) | venue/range/URL は独立。ただし `"dblp"` と整数 year [T:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:443) は RA-04/RA-05 の未登録選択 |
| `test_render_catalog_json_is_canonical_deterministic_and_one_newline` [T:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:462) | **自己参照**。期待値が production の `build_catalog_document()` と production と同じ `json.dumps` 式 [T:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:465) |
| `test_checked_in_catalog_matches_rendered_bytes` [T:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:474) | 指示どおり catch-all として許容 |
| `test_cli_output_writes_exact_rendered_bytes` [T:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:478) | 書込み配線は有効だが、byte 期待値は production の `render_catalog_json()` 由来で自己参照 |
| `test_cli_verify_accepts_exact_and_rejects_one_byte_change` [T:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:489) | 負例・読取不能は有効。正例 fixture は production renderer 由来で自己参照 |
| `test_cli_requires_exactly_one_mode` [T:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:502) | 独立 literal |

これは実装子報告の「17 test は独立 literal」[author_1.md:5](/home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/author_1.md:5) と一致しない。

推奨対応: 新しい test を増やさず、既存の renderer/CLI test 3 本を、production renderer から作らない固定 byte fixture に置き換える。index/year の期待値は RA-04/RA-05 の裁定後の literal に揃える。

Catalog bytes への影響: test 自己参照の修正自体は 0 byte。index/year 裁定の影響は RA-04/RA-05 のとおり。

**RA-09 — refuted: CLI 実装は登録契約に一致する。**

`argparse` の required mutually-exclusive group が排他・どちらか必須を担う [I:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:481)。`--verify` は `read_bytes()` と比較だけを行い、不一致・`OSError` とも rc=1 [I:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:473)。書込みは `--output` 分岐だけにある [I:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py:488)。both/neither の argparse rc=2 は、rc=1 を不一致・読取不能にだけ要求した C [C:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:258) と矛盾しない。

推奨対応: 実装変更なし。

## 総括

判定は **changes requested**。

指定済みの語列、枝、URL 展開、percent encoding、control、配列順、metadata、cardinality、venue literal、CLI には byte 不一致を見つけなかった。一方、次の 3 件は real である。

- RA-04: `index` 値と一部 main query ID の索引表記が未登録。
- RA-05: venue `year` の JSON 型が未登録。
- RA-08: renderer/CLI test 3 本の期待値が production 由来で自己参照し、別の 3 本が RA-04/RA-05 の未登録選択を正解として固定している。

したがって、現在の J は「採用された実装上の読みとは一致」するが、「凍結規則から一意に導かれる bytes」としてはまだ承認できない。