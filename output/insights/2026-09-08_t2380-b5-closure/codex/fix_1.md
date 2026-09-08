## 変更した test と対応する所見 (closed / partial / regressed の表)

| test | 所見 | 状態 | 対応 |
|---|---|---|---|
| `test_render_catalog_json_is_canonical_deterministic_and_one_newline` | RA-08 | closed | tracked JSON bytesと固定 SHA-256を独立 oracle 化 |
| `test_cli_output_writes_exact_rendered_bytes` | RA-08 | closed | CLI 出力を tracked bytesおよび固定 digest と照合 |
| `test_cli_verify_accepts_exact_and_rejects_one_byte_change` | RA-08 | closed | tracked bytesを正例にし、末尾 1 byte追加を拒否 |
| `test_main_query_ids_order_and_cardinalities_are_exact` | RB-01 | closed | 全1622件の ID、枝、`term_groups`を独立 literal から完全照合 |
| `test_dblp_cartesian_branch_counts_bounds_and_request_bytes_are_exact` | RB-01 | closed | 全1602件の ID、語 ID、語句、URL、template の対応を完全照合 |
| `test_openalex_q1_full_url_is_unquoted_and_keeps_comma_unencoded` | RB-01、RB-06、RB-07 | closed | 全 cursor／position置換関係と直接 oracle を追加 |
| `test_aux_venue_streams_have_frozen_range_order_ids_and_full_urls` | RB-01 | closed | 裁定済みの小文字 index、number yearを含む全272 entryを完全照合 |
| `test_dblp_q10_frozen_example_is_encoded_once` | RB-05 | closed | 空白が `%20` になる直接 oracle を先頭へ追加 |
| `test_arxiv_q1_full_url_preserves_frozen_terms_order_quotes_and_cutoff` | RB-08 | closed | arXiv式の直接 oracle を追加 |
| `test_term_ids_match_frozen_two_digit_literals` | RB-12 | closed | `_term_id` の直接 oracle を文書構築前へ移動 |

partial、regressed はありません。

## 実走した結果

`PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_catalog.py`

- rc: `0`
- collected: `17`
- passed: `17`
- 実行時間: `3.04s`

## 総括

[orchestrator/tests/test_axis_b5_search_catalog.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py) のみ編集しました。test nodeid は17本を維持しています。

`catalog.py`、生成 JSON、docs、その他の file は変更せず、git の状態を変える操作も行っていません。