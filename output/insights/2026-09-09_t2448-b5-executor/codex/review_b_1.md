## 受入で赤になる構成

- `real`: 新規 54 node は所要時間台帳に全件欠落している。台帳は既存 22,157 件だけを宣言しており、mapping 数とも一致するが、新規 2 file の nodeid は 0 件である。`orchestrator/tests/acceptance_duration_ledger.json:22160-22163`
  - ただし「この欠落だけで受入が必ず赤になる」は `refuted`。投影範囲で確認できる meta-test は 100% でなく 90% 以上を要求しているためで、54 件は現台帳件数の約 0.244% にすぎない。該当 node 名は `orchestrator/tests/acceptance_duration_ledger.json:17`。
  - 放置時の影響: 受入 scheduler が 54 node を実測値不明として扱い、段 4 の受入所要台帳契約は未完のままになる。
  - 最小是正: 段 4 の指示どおり、JUnit 実測後に `tools/update_acceptance_duration_ledger.py --add-only` を一度だけ使う。手書き値は入れない。`rulings-stage4.md:132-136`

- `refuted`: README の pytest-only allowlist へ追加する必要はない。両 file とも実際に test を起動する `__main__` を持ち、allowlist は「自走 harness がない file」専用である。`orchestrator/tests/README.md:114-126`, `orchestrator/tests/test_axis_b5_search_parsers.py:303-304`, `orchestrator/tests/test_axis_b5_search_executor.py:1001-1002`
  - 放置時の影響: なし。allowlist へ追加すると、むしろ stale/self-runnable 検査の対象になり得る。
  - 最小是正: README allowlist は変更しない。

- `refuted`: repo collection invariant から新規 file が漏れる構成ではない。既定範囲は `orchestrator/tests` で、除外対象は `output`、`external`、dot directory である。`orchestrator/tests/README.md:77-91`
  - 放置時の影響: 新規 54 node は通常の受入 collection に追加される。
  - 最小是正: なし。

- `real`、ただし実測ではなく静的見積り: 新規 54 node の直列費用は約 3〜20 秒と見る。比較対象の catalog 17 node は台帳上合計 2.267 秒、最大 0.38 秒である。`orchestrator/tests/acceptance_duration_ledger.json:81-97`
  - 既存台帳総和 14,766.477 秒に対して約 0.02〜0.14%。xdist の wall 増分は通常これより小さい。
  - 放置時の影響: 総予算超過より、未知コスト配置による小さな shard imbalance のほうが現実的。
  - 最小是正: 推測値を登録せず、JUnit から更新する。

## 不足している台帳 nodeid

`real`: 34 executor node と 20 parser node、合計 54 件が不足している。両 file に parametrize はなく、`[...]` 付き nodeid はない。定義位置は `orchestrator/tests/test_axis_b5_search_executor.py:294-999` と `orchestrator/tests/test_axis_b5_search_parsers.py:32-300`。

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal
orchestrator/tests/test_axis_b5_search_executor.py::test_registration_rejects_extra_file_in_exact_directory
orchestrator/tests/test_axis_b5_search_executor.py::test_registration_rejects_invalid_or_non_head_commit
orchestrator/tests/test_axis_b5_search_executor.py::test_registration_rejects_dirty_mode_and_byte_mismatches
orchestrator/tests/test_axis_b5_search_executor.py::test_failed_registration_returns_before_live_transport_creation
orchestrator/tests/test_axis_b5_search_executor.py::test_registry_has_frozen_members_and_g208_doi_primary_key
orchestrator/tests/test_axis_b5_search_executor.py::test_lookup_builder_emits_only_registered_three_forms
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_404_is_nonrecorded_before_content_type_check
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_200_json_id_is_recorded
orchestrator/tests/test_axis_b5_search_executor.py::test_arxiv_media_type_parameters_are_ignored_and_malformed_is_unreachable
orchestrator/tests/test_axis_b5_search_executor.py::test_dblp_matching_doi_is_recorded_but_unknown_json_shape_is_unclassified
orchestrator/tests/test_axis_b5_search_executor.py::test_dblp_zero_total_is_nonrecorded
orchestrator/tests/test_axis_b5_search_executor.py::test_live_preflight_29_recorded_plus_one_unreachable_cannot_start
orchestrator/tests/test_axis_b5_search_executor.py::test_live_preflight_accepts_exact_30_and_wid_drift_is_evidence_only
orchestrator/tests/test_axis_b5_search_executor.py::test_live_preflight_has_no_defaults_for_caller_policy_values
orchestrator/tests/test_axis_b5_search_executor.py::test_resolve_leaf_accepts_one_location_and_rejects_duplicate_or_wrong_host
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_initial_cursor_is_literal_star_and_continuation_is_encoded
orchestrator/tests/test_axis_b5_search_executor.py::test_offset_request_uses_fixed_step_and_rejects_actual_count_style_position
orchestrator/tests/test_axis_b5_search_executor.py::test_text_echo_normalization_decodes_once_and_does_not_accept_parentheses
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_ast_preserves_multiplicity_but_ignores_sibling_order
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_ast_rejects_unknown_key_join_and_get_rows_type
orchestrator/tests/test_axis_b5_search_executor.py::test_condition3_uses_actual_count_not_capacity_echo
orchestrator/tests/test_axis_b5_search_executor.py::test_condition3_accepts_normal_partial_final_despite_capacity_echo
orchestrator/tests/test_axis_b5_search_executor.py::test_condition2_checks_position_only_not_short_page_count
orchestrator/tests/test_axis_b5_search_executor.py::test_declared_total_drift_is_not_accepted_from_final_page_value
orchestrator/tests/test_axis_b5_search_executor.py::test_drift_allows_exactly_one_page_zero_rerun
orchestrator/tests/test_axis_b5_search_executor.py::test_duplicate_occurrence_is_rejected_but_retained_in_ledger
orchestrator/tests/test_axis_b5_search_executor.py::test_dblp_cutoff_fields_flow_without_dropping_raw_occurrences
orchestrator/tests/test_axis_b5_search_executor.py::test_condition6_accepts_media_parameter_and_rejects_wrong_type
orchestrator/tests/test_axis_b5_search_executor.py::test_main_run_issuance_fails_closed_with_all_six_unregistered_fields
orchestrator/tests/test_axis_b5_search_executor.py::test_retry_delays_are_the_frozen_tuple
orchestrator/tests/test_axis_b5_search_executor.py::test_page_and_leaf_records_are_draft07_schema_valid
orchestrator/tests/test_axis_b5_search_executor.py::test_live_record_is_schema_valid_and_unclassified_is_false_side
orchestrator/tests/test_axis_b5_search_executor.py::test_live_missing_member_is_schema_valid_and_false_side
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_1_accepts_valid_page_with_b5_parser
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_1_rejects_axis1_parser_dependency
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_2_accepts_openalex_cursor_chain_verbatim
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_2_rejects_calculated_offset_next_position
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_3_accepts_container_count_for_full_and_final_pages
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_3_rejects_capacity_echo_as_actual_count
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_4_accepts_distinct_occurrences_in_container_order
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_4_rejects_page_local_deduplication
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_4_rejects_cross_page_deduplication
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_5_accepts_four_digit_year_at_cutoff
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_5_rejects_future_year_and_routes_bad_years_to_ruling
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_6_accepts_raw_query_text_and_structured_ast
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_6_rejects_lossy_ast_object_decoding
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_6_rejects_missing_ast_with_literal_error_code
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_7_accepts_only_the_registered_literal_error_vocabulary
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_7_rejects_malformed_bodies_without_raising
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_7_rejects_invalid_page_number_without_raising
orchestrator/tests/test_axis_b5_search_parsers.py::test_missing_total_is_a_literal_parse_error_and_records_occurrence
orchestrator/tests/test_axis_b5_search_parsers.py::test_saved_real_arxiv_hit_and_miss_shapes
orchestrator/tests/test_axis_b5_search_parsers.py::test_saved_real_openalex_lookup_and_404_are_not_search_pages
```

放置時の影響: 更新後の `nodeid_count` は 22,211 になるべきところ、22,157 のまま残る。

最小是正: 上記 54 node を実測 JUnit から add-only で登録する。

## 変異の帰属

Harness は rc=1 かつ失敗 node の正規化集合が期待集合と完全一致するときだけ `KILLED` にする。`tools/mutation_harness.py:2083-2099`。期待 node の collection 実在も事前検証される。`tools/mutation_harness.py:1495-1565`

以下の集合は、投影された新規 2 test file を走らせ、記載した exact replacement を採る場合のもの。候補文だけで変異 file・old・new が決まらないものは `refuted` とした。

1. 初回 cursor `*` から `%2A`
   - 候補文のままでは `refuted`: `catalog.py:279` と `runner.py:396-400` に別の役割の literal があり、変異先で集合が変わる。
   - `runner.py:400` の `encoded = "*"` だけを変えるなら `real`、一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_initial_cursor_is_literal_star_and_continuation_is_encoded
```

   - 放置時の影響: catalog 側を変異すると catalog digest 系へ帰属が拡散し、期待集合が別物になる。
   - 最小是正: replacement を `runner.py:400` の行全体へ固定する。

2. OpenAlex AST children の set 化
   - `real`: `runner.py:587-593` の canonical children だけを重複排除するなら一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_ast_preserves_multiplicity_but_ignores_sibling_order
```

   - 放置時の影響: 多重度欠落を mutation が検出できない。
   - 最小是正: `tuple(sorted(set(...)))` への exact replacement として登録する。

3. live preflight の `all` を `any` へ
   - `real`: 一意だが 2 node fanout。双方とも「1 件でも非収録なら開始不可」という同じ理由で赤になる。`preflight.py:764-767`

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_live_preflight_29_recorded_plus_one_unreachable_cannot_start
orchestrator/tests/test_axis_b5_search_executor.py::test_live_record_is_schema_valid_and_unclassified_is_false_side
```

   - 放置時の影響: 1 件だけ `不達` または `unclassified` の record が開始可能になる。
   - 最小是正: この 2 node をともに expected_nodes へ登録する。

4. drift を最終 page の値で受理
   - 候補文のままでは `refuted`: drift check の削除だけか、比較基準を最後へ変えるかが決まっていない。
   - `runner.py:780-784` を「drift を返さず `declared = totals[-1]`」へ固定するなら `real`、一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_declared_total_drift_is_not_accepted_from_final_page_value
orchestrator/tests/test_axis_b5_search_executor.py::test_drift_allows_exactly_one_page_zero_rerun
```

   - 放置時の影響: 後者は初回を drift と認識せず、rerun 注入時に別経路で赤になるため、1 node 想定だと `MISMATCH` になる。
   - 最小是正: 2 node を登録する。1 node だけに絞るための `len(pages)==3` 特例変異は production defect を忠実に表さないので採らない。

5. 条件 3 の実要素数を `capacity_echo` へ
   - `real`: `runner.py:722` の `actual` 代入だけを置換すれば一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_condition3_uses_actual_count_not_capacity_echo
orchestrator/tests/test_axis_b5_search_executor.py::test_condition3_accepts_normal_partial_final_despite_capacity_echo
```

   - 放置時の影響: 短い非最終 page を通し、部分最終 pageを逆に落とす。
   - 最小是正: 2 node を expected_nodes にする。

6. 本走発行の fail-closed を外す
   - `real`: `issue_run_request` の raise を return にするなら一意。`runner.py:900-903`

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_main_run_issuance_fails_closed_with_all_six_unregistered_fields
```

   - 放置時の影響: 未登録運用値のまま発行境界を通過する。
   - 最小是正: 上記 1 node を登録する。

7. directory exact set を部分集合へ
   - `real`: `preflight.py:325-333` の等値を `set(tree).issubset(worktree_paths)` へ緩めるなら一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_registration_rejects_extra_file_in_exact_directory
```

   - 放置時の影響: 未登録 file が seal 対象 directory に混入しても通る。
   - 最小是正: 上記 1 node を登録する。

8. DBLP cutoff 判定を落とす
   - 候補文のままでは `refuted`: `None` 化、全件採用、年 field 無視で集合が異なる。
   - `parsers.py:422` を「妥当な 4 桁年は常に `included_by_cutoff=True`」へ固定するなら `real`、一意:

```text
orchestrator/tests/test_axis_b5_search_parsers.py::test_contract_5_rejects_future_year_and_routes_bad_years_to_ruling
orchestrator/tests/test_axis_b5_search_executor.py::test_dblp_cutoff_fields_flow_without_dropping_raw_occurrences
```

   - 放置時の影響: 2027 年が採用側へ入る。
   - 最小是正: 上記 exact replacement と 2 node を登録する。

9. 3 値外応答を `収録` へ丸める
   - 候補文のままでは `refuted`: 初期値 `classification` 全体を変えるか、DBLP の unknown branch だけを変えるかで波及が異なる。
   - DBLP の `total > 0` かつ DOI 不一致 branch だけを `収録` にするなら `real`、一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_dblp_matching_doi_is_recorded_but_unknown_json_shape_is_unclassified
```

   - 放置時の影響: 登録された 3 形に属さない応答を開始許可へ数える。
   - 最小是正: `preflight.py:674-693` の DBLP branch に限定した replacement にする。

10. OpenAlex の content type 先行
   - `real`: OpenAlex branch 内だけを入れ替えるなら一意。`preflight.py:616-624`

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_openalex_404_is_nonrecorded_before_content_type_check
```

   - 放置時の影響: 登録上の `非収録` 404 が `不達` に化ける。
   - 最小是正: 上記 1 node を登録する。

11. `G2-08` 主キーを arXiv ID にする
   - JSON の DOI だけを変える案は `refuted`: loader 自身の literal guard が先に落ち、`load_anchor_registry()` を呼ぶ少なくとも 11 node が連鎖して、本来の主キー assertion へ到達しない。`preflight.py:482-484`
   - 単一理由化する具体案: `anchor_registry.json:87` の DOI と `preflight.py:483` の自己検査 literal を同時に `1710.11258` へ変える。すると投影範囲で一意:

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_registry_has_frozen_members_and_g208_doi_primary_key
```

   - 放置時の影響: JSON だけの変異では「主キー検出」ではなく「registry loader 全停止」の mutation になる。
   - 最小是正: 2 replacement を同一 mutation に入れる。

12. retry delay `6.0` から `7.0`
   - `real`: node 集合は一意。`runner.py:46`

```text
orchestrator/tests/test_axis_b5_search_executor.py::test_retry_delays_are_the_frozen_tuple
```

   - ただし実効性は `nit`: この定数を読む retry production 経路が存在しない。
   - 放置時の影響: 現在の成果物動作は変わらず、定数表だけが変わる。
   - 最小是正: mutation 自体は登録可能だが、実効 mutation として数えるなら retry consumer が存在する後続 wave まで保留する。

## test の実効性

- `real`: OpenAlex の正常 AST と production 期待 AST の表現が一致しない。
  - production builder は filter を `{"column_id": ..., "value": ...}` 形で作る。`runner.py:639-662`
  - parser fixture と AST の positive test は `{"title_and_abstract.search": "backoff"}` の直接-key形を正常形としている。`orchestrator/tests/fixtures/axis_b5_search/synthetic/openalex_cursor_page_1.json:8-12`, `orchestrator/tests/test_axis_b5_search_executor.py:661-686`
  - canonicalizer は両形を別 tuple にするため、意味的に同じ field/value へ統一しない。`runner.py:594-615`
  - 現 test は production builder の出力を同じ production matcherへ戻しており、実応答形との比較をしていない。`orchestrator/tests/test_axis_b5_search_executor.py:643-658`
  - 放置時の影響: 正常な OpenAlex page が条件 1 の `interpreted_query_mismatch` になり、leaf が `未完走` になる。
  - 最小是正: 凍結文から独立 literal の expected/actual AST を test に置き、まず builder と実応答形を直接比較する。修正先は builder または canonicalizer の一方に限定する。

- `real`: 成功側 `run_live_preflight` は production 経路を通る test がない。唯一の直接呼出しは registration failure で transport 作成前に止まる。`orchestrator/tests/test_axis_b5_search_executor.py:345-364`
  - transport 作成、30 request loop、interval sleep、schema validation、atomic write は未実走。`preflight.py:887-913`
  - `test_live_preflight_*` は `_lookup_result` が作る stub 同士を aggregator に渡すだけで、request builder、classifier、transport を通らない。`orchestrator/tests/test_axis_b5_search_executor.py:263-291`, `orchestrator/tests/test_axis_b5_search_executor.py:545-578`
  - 放置時の影響: member loop や出力保存を壊しても新規 suite は緑のまま。
  - 最小是正: 既存 `_transport_factory` seam で 30 応答を返す成功 test を 1 node 追加し、30 request、29 sleep、schema-valid durable record を確認する。

- `real`: production 入口 `run_leaf` と durable live record loader は未実走である。test は `issue_run_request` を直接呼ぶだけ。`orchestrator/tests/test_axis_b5_search_executor.py:905-920`
  - 未検査範囲は seal equality、commit/digest、exact 30 lookup、各 request URL、全 classification、最終 issuance 結線。`runner.py:906-986`
  - 放置時の影響: `run_leaf` が preflight を迂回、または issuance を呼ばず黙って return しても直接 fail-closed test は緑。
  - 最小是正: `run_leaf` の production 順序を 1 node で通し、正しい durable record の後に必ず `UnregisteredRunPolicyError` へ到達することを検査する。

- `real`: `test_condition3_accepts_normal_partial_final_despite_capacity_echo` は leaf 全体の正例ではない。page 0 request に対し fixture の `startIndex` は 2 なので条件 2 は失敗する。`orchestrator/tests/test_axis_b5_search_executor.py:731-745`, `orchestrator/tests/fixtures/axis_b5_search/synthetic/arxiv_final.xml:4-7`, `runner.py:704-717`
  - 放置時の影響: 条件 3 単体は守るが、部分最終 page が 6 条件すべてを通る統合正例はない。
  - 最小是正: start 0、total 1、actual 1、capacity echo 2 の極小応答をこの test 内で使い、`result.passed is True` まで確認する。

- `nit`: `test_retry_delays_are_the_frozen_tuple` は `RETRY_DELAYS_S` の値だけを読む。実装側には retry consumer がない。`runner.py:46-47`, `orchestrator/tests/test_axis_b5_search_executor.py:923-924`
  - 放置時の影響: 現在の request 動作は変わらない。
  - 最小是正: 現 wave では定数凍結 test と明記し、実効 retry test を名乗らない。

- 残る test 群の production 対応は次のとおりで、上記以外に明白な stub 閉包は見つからない。
  - parser contract 1〜4: arXiv/OpenAlex/DBLP container、cursor、position、occurrence。`test_axis_b5_search_parsers.py:32-135` → `parsers.py:224-394`, `parsers.py:425-519`
  - cutoff: `test_axis_b5_search_parsers.py:137-167` → `parsers.py:408-422`
  - duplicate-key AST と error vocabulary: `test_axis_b5_search_parsers.py:170-272` → `parsers.py:179-211`, `parsers.py:353-380`
  - registration seal: `test_axis_b5_search_executor.py:294-364` → `preflight.py:274-402`
  - registry/request/classification: `test_axis_b5_search_executor.py:367-542` → `preflight.py:405-714`
  - leaf resolution/request/normalization: `test_axis_b5_search_executor.py:588-640` → `runner.py:255-545`
  - 条件 2〜6、rerun、duplicate: `test_axis_b5_search_executor.py:702-902` → `runner.py:704-885`
  - record/schema: `test_axis_b5_search_executor.py:927-999` → `runner.py:126-227`, `preflight.py:724-787`

## 凍結文との照合

- `real`: 段 4 に逐語で射影された範囲では、次は一致している。
  - offset step 200/100、pagination kind の分離: `rulings-stage4.md:115-126`, `runner.py:39-45`, `runner.py:385-406`
  - `capacity_echo` 非 gate: `rulings-stage4.md:121-122`, `runner.py:720-740`
  - OpenAlex 初回 cursor literal `*`: `rulings-stage4.md:167`, `catalog.py:275-279`, `runner.py:396-410`
  - exact 30 member: `rulings-stage4.md:72-78`, `anchor_registry.json:3-164`, `preflight.py:455-484`
  - `G2-08` DOI 主キーと arXiv lookup key: `rulings-stage4.md:78`, `anchor_registry.json:85-92`
  - OpenAlex 404 status 先行: `rulings-stage4.md:70-72`, `preflight.py:614-624`
  - fail-closed と未登録 6 field: `rulings-stage4.md:48-57`, `runner.py:53-60`, `runner.py:238-252`, `runner.py:900-903`
  - retry tuple の中央値 6.0: `rulings-stage4.md:178`, `runner.py:46`

- 一方、完全な「凍結文との 1 文字比較」は `refuted` ではなく `判定不能`。指定射影には 2 本の preregistration 本文と closure record 本文が含まれておらず、単独段 dispatch 規則上、それらを追加で読むことはできない。`rulings-stage4.md:41-58` は要約された実装契約であり、全 request/member literal の原文ではない。
  - 放置時の影響: catalog、全 anchor、全 request URL が凍結原文と一字一致するとの独立主張は、この review からは出せない。
  - 最小是正: 文字単位監査が必要なら、次の review 射影へ当該凍結 3 文書を追加する。凍結文や catalog 自体の変更提案ではない。

- `real`: 投影内の二重写し同士では anchor 全 16 件と 30 member、三つの lookup request 例が exact に一致する。`anchor_registry.json:3-164`, `orchestrator/tests/test_axis_b5_search_executor.py:367-417`
  - 放置時の影響: この内部一致だけでは、双方が同じ転記誤りを持つ可能性を排除できない。
  - 最小是正: 上記の凍結原文投影後に独立照合する。

## schema と出力

- `refuted`: production record が要求 field を欠く、または schema 外 field を出す直接不整合は見つからない。
  - page evidence: production `runner.py:126-171` と schema `axis_b5_search_page_evidence.schema.json:166-195`
  - leaf evaluation: production `runner.py:200-227` と schema `axis_b5_search_page_evidence.schema.json:244-273`
  - registration seal: production `preflight.py:373-390` と schema `axis_b5_search_registration_seal.schema.json:7-109`
  - live record: production `preflight.py:769-787`, `preflight.py:724-741` と schema `axis_b5_search_live_preflight.schema.json:7-84`, `axis_b5_search_live_preflight.schema.json:168-204`
  - 放置時の影響: 現 production builder が作る通常 record は schema field 集合の理由では落ちない。
  - 最小是正: なし。

- `real`: live schema 内へ複製された `registration_seal` 定義は standalone seal schema より弱い。
  - live 側は `includes`/`excludes` に minItems だけを置き、exact enum/maxItems を持たない。また `files` の uniqueItems と path pattern も欠く。`axis_b5_search_live_preflight.schema.json:111-146`
  - standalone 側は exact enum、min=max、uniqueItems、安全な path pattern を要求する。`axis_b5_search_registration_seal.schema.json:39-108`
  - production `_load_live_preflight` は再計算 seal との equality と digest で補償する。`runner.py:920-927`
  - 放置時の影響: live schema だけを使う外部 consumer は、standalone schema が拒否する弱い embedded seal を schema-valid と判定できる。
  - 最小是正: live schema 内の複製定義を standalone と同じ制約へ揃える。production output の変更は不要。

- `refuted`: 29 member の失敗 record が schema-validなのは field 不整合ではない。schema は失敗証拠も保存でき、production loader が `exact_member_set/passed/may_start_run` と 30 member を別途要求する設計である。`orchestrator/tests/test_axis_b5_search_executor.py:979-998`, `runner.py:935-959`
  - 放置時の影響: 失敗 preflight の証拠保存は維持され、発行には使えない。
  - 最小是正: なし。

## 総括

受入を必ず赤にする新規構成は、指定射影からは確認できなかった。README/self-run/collection は整合している。一方、台帳の 54 node 欠落は `real` であり、段 4 の完了条件を満たしていない。

実装上の最重要欠陥は OpenAlex AST である。production builder の filter 表現と、fixtureおよび positive test が正常扱いする表現が canonical 化後も一致しないため、正常 OpenAlex leaf を条件 1 で落とし得る。次点は、成功側 `run_live_preflight` と production `run_leaf` が未実走であること。

変異は m03、m05、m06、m07、m10、m12 が現状でも exact set を固定しやすい。m01、m04、m08、m09 は replacement を行単位へ具体化すべきで、m11 は registry と自己検査 literal の同時変異にしないと loader 全停止へ帰属が崩れる。m12 は kill できるが、現時点では dead constant の検査に留まる。

ファイル変更、git 操作、pytest 実行、外部通信は行っていない。