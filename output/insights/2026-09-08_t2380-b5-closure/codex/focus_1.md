## 所見ごとの closed / partial / regressed 表

| 所見 | 判定 | 根拠 |
|---|---|---|
| RA-04 / RA-05 裁定整合 | closed | `index` は小文字、venue の `year` は number の独立 literal で照合され、親裁定どおり。 |
| RA-08 | closed | renderer、CLI output、CLI verify の期待値は tracked bytes 由来。production renderer 由来の fixture は除去され、固定 SHA-256 `7eb8385e...c346f` も照合する。[現 test:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:579) |
| RB-01 | closed | test 内の `EXPECTED_BLOCKS`、`EXPECTED_TERM_IDS`、`EXPECTED_BRANCHES` から全 1622 query の ID・branch・`term_groups` を構築。[現 test:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:341) 全 1602 DBLP record は ID・groups・URL・template を完全照合する。[現 test:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:390) |
| RB-01 replacement 関係 | closed | OpenAlex 15 entry と arXiv / DBLP 1893 entry、合計 1908 entry について `{CUR}` / `{POS}` 置換を検査する。[現 test:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:476) |
| RB-01 venue | closed | 8 venue × 34 year の 272 dict を test 側で構築し、配列全体を完全一致させる。[現 test:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:534) |
| RB-05 | closed | `_percent_encode("a b") == "a%20b"` が既存 DBLP Q10 node 内に追加され、spec #1 も `quote_plus as quote` へ修正済み。 |
| RB-06 | closed | comma 保存の直接 oracle が既存 OpenAlex node 内にある。 |
| RB-07 | closed | `_openalex_filter` の非 quote literal が同じ既存 node 内にある。 |
| RB-08 | closed | `_arxiv_expression` の `abs:"..."` literal が既存 arXiv node 内にある。 |
| RB-09 | closed | sort 変異は既存 blocks node の全 85 語順 literal が直接検出する。 |
| RB-10 | closed | `product` から `zip` への変異は既存 main-query / DBLP node の総数・枝別件数・全列比較で直接検出する。 |
| RB-11 | closed | spec #7 は裁定どおり Q10 除去。既存 DBLP node が Q10 の件数と完全列を要求する。 |
| RB-12 | closed | `_term_id` の直接 oracle が document 構築より前へ移動している。[現 test:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py:321) |
| node 数と配置 | closed | 旧新とも同名の 17 test 関数。直接 oracle は既存関数内だけに追加され、新規 node はない。 |
| 退行 | closed | 旧 assertion の削除や期待値緩和はない。自己参照期待値は tracked bytes に置換され、それ以外は保持または強化された。production の `BLOCKS`、`BRANCHES`、URL helper は期待値生成に使われていない。 |
| `catalog.py` / 生成 bytes | closed | 現行 renderer は 938,806 bytes、SHA-256 は固定 literalと同じ `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f`。現行 production はレビュー記載の各変異対象とも一致し、退行を認めない。 |

## 変異 13 件の赤 node 見積り

以下の略号はすべて `test_axis_b5_search_catalog.py` 内の node。

| 略号 | test 関数 |
|---|---|
| T02 | `test_blocks_match_frozen_terms_order_counts_and_disjointness` |
| T03 | `test_term_ids_match_frozen_two_digit_literals` |
| T05 | `test_main_query_ids_order_and_cardinalities_are_exact` |
| T06 | `test_dblp_cartesian_branch_counts_bounds_and_request_bytes_are_exact` |
| T07 | `test_arxiv_q1_full_url_preserves_frozen_terms_order_quotes_and_cutoff` |
| T08 | `test_openalex_q1_full_url_is_unquoted_and_keeps_comma_unencoded` |
| T09 | `test_dblp_q10_frozen_example_is_encoded_once` |
| T10 | `test_controls_match_frozen_ids_groups_and_all_full_urls` |
| T11 | `test_dblp_and2023_shares_exact_request_bytes_only_with_dblp_and` |
| T12 | `test_aux_venue_streams_have_frozen_range_order_ids_and_full_urls` |
| T13 | `test_render_catalog_json_is_canonical_deterministic_and_one_newline` |
| T14 | `test_checked_in_catalog_matches_rendered_bytes` |
| T15 | `test_cli_output_writes_exact_rendered_bytes` |
| T16 | `test_cli_verify_accepts_exact_and_rejects_one_byte_change` |

| 変異 | 静的な赤 node 完全集合 | 判定 |
|---|---|---|
| #1 `quote_plus as quote` | T06, T07, T08, T09, T10, T13, T14, T15, T16 | KILLED |
| #2 OpenAlex comma encode | T08, T10, T13, T14, T15, T16 | KILLED |
| #3 OpenAlex terms quote | T08, T10, T13, T14, T15, T16 | KILLED |
| #4 arXiv `abs` quote 除去 | T07, T10, T13, T14, T15, T16 | KILLED |
| #5 block term sort | T02, T06, T07, T08, T09, T10, T13, T14, T15, T16 | KILLED |
| #6 DBLP `product` → `zip` | T05, T06, T08, T13, T14, T15, T16 | KILLED |
| #7 DBLP Q10 除去 | T05, T06, T08, T09, T13, T14, T15, T16 | KILLED |
| #8 term ID zero-pad 除去 | T03, T05, T06, T07, T08, T09, T10, T13, T14, T15, T16 | KILLED |
| #9 AND2023 DBLP share を `None` | T11, T13, T14, T15, T16 | KILLED |
| #10 venue の 2026 除去 | T08, T12, T13, T14, T15, T16 | KILLED |
| #11 renderer 末尾 newline 除去 | T13, T14, T15, T16 | KILLED |
| #12 verify を JSON 意味比較へ変更 | T16 | KILLED |
| #13 `list(group)` → `[*group]` | なし | SURVIVED |

#13 は要素、順序、型、生成 JSON bytesのいずれも変えない等価変異であり、17 node 全て緑になる見積り。

## 総括

焦点再レビューの結論は、対象所見はすべて closed、partial と regressed はなし。17 node は維持され、旧検査は保持または強化されている。静的見積りでは #1〜#12 が KILLED、等価変異 #13 だけが SURVIVED となる。ファイル変更、git、pytest、network 操作は行っていない。