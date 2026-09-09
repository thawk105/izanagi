## parser

実装対象は `orchestrator/axis_b5_search/parsers.py`。軸 1 の [parsers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/parsers.py:14) を写経元にするが、import はしない。

**予定行と型**

- `parsers.py:1-14`: import、Atom/OpenSearch/arXiv namespace、`JsonValue` 型 alias。
- `parsers.py:15-28`: `Occurrence`。
  - `index_work_id: str`
  - `page_number: int`
  - `ordinal: int`
  - `raw_date_value: str | None`
  - `interpreted_date: str | None`
  - `date_missing_reason: str | None`
  - `family_keys: tuple[str, ...]`
- `parsers.py:31-48`: `ParsedPage`。
  - `index: Literal["arxiv", "openalex", "dblp"]`
  - `declared_total: int | None`
  - `declared_page_size: int | None`
  - `actual_count: int`
  - `interpreted_query_text: str`
  - `interpreted_query_ast: JsonValue | None`
  - `position_in: str | None`
  - `position_out: str | None`
  - `occurrences: tuple[Occurrence, ...]`
  - `parse_errors: tuple[str, ...]`
- `parsers.py:50-140`: 非負整数、日付、年、DOI、arXiv ID、family key、重複 JSON member 検出の private helper。
- `parsers.py:142-215`: `parse_arxiv_page(body: bytes, page_number: int) -> ParsedPage`。
- `parsers.py:217-335`: `parse_openalex_page(body: bytes, page_number: int) -> ParsedPage`。
- `parsers.py:337-430`: `parse_dblp_page(body: bytes, page_number: int) -> ParsedPage`。
- `parsers.py:432-445`: `__all__`。

`occurrences[*].index_work_id` が索引固有 work ID の順序つき列である。同じ ID を消さず反復行として保持する。runner はここから `index_work_ids` と、同じ IDの全座標を持つ `duplicate_occurrences` を証拠へ導出する。parser 内で deduplicate しない。

DBLP の `year` 欠落は `Occurrence(raw_date_value=None, interpreted_date=None, date_missing_reason="missing_dblp_year")` で運ぶ。これは parse failure にせず、部分登録 §2.2 の `要裁定` 候補として残す。4 桁でない値は `invalid_dblp_year` とする。

**関数単位の軸 1 との比較**

| 関数 | 同じ点 | B5 で変える点 |
|---|---|---|
| `parse_arxiv_page` | `totalResults`、`itemsPerPage`、`startIndex`、`feed/entry`、`entry/id`、`published`、`arxiv:doi` を読む。実要素数は `len(entry)` | field 名を `capacity_echo` から `declared_page_size` にする。非終端の次位置は実要素数でなく凍結値 200 を使う。条件 3 の判定は runner 側で独立に行う |
| `parse_openalex_page` | `meta.count`、`meta.per_page`、`results`、`results[].id`、`publication_date`、`ids`、`next_cursor`、`x_query.url` を読む。実要素数は `len(results)` | `meta.x_query.oql` を text、`oqo` を typed AST として別 field に保持する。JSON の重複 key を fail-closed にする。軸 1 の `get_rows == "works"` を使わず、B5 登録の文字列 `"200"` と比較する |
| `parse_dblp_page` | `result.hits.@total/@sent/@first/hit`、`info.key/year/doi/ee`、`result.query` を読む。単一 hit object と配列の双方を受ける | `@sent` は証拠だけで、絶対に `actual_count` に使わない。実数は `len(hit)`。次位置は凍結値 100。`year` 欠落を除外や parse failure にしない |

軸 1 の `position_out = position + len(elements)` は、正常な非最終ページでは同値だが、短い非最終ページで登録外位置を作る。B5 は parser が 200 / 100 の固定遷移を出し、runner が短ページを先に拒否する。

## preflight

**registration preflight**

採用するのは、軸 1 の [verify_registration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:749) と同じ git blob 照合方式である。checked-in manifest の SHA-256 表を信頼根にすると、表と対象を同じ変更で差し替えられる。登録 commit、HEAD、clean な exact path set、commit blob、worktree bytes を相互照合する方が、`preflight.py` 自身も外部の commit tree へ束縛できる。

- `preflight.py:1-45`: `RegistrationBinding`、`RegistrationSealRecord`、`PreflightResult`。
- `preflight.py:47-105`: exact `REGISTERED_PATHS` と fixture exact set。
- `preflight.py:107-195`: Git backend、regular-file/mode/path-set 検査、SHA-256 算出。
- `preflight.py:197-270`: `verify_registration(registration_commit, repo_root) -> PreflightResult`。
- 成功時に schema-valid な seal recordを返す。record は `registration_commit`、各 path の git blob、mode、byte count、SHA-256を持つ。
- seal record 自身は binding 表へ含めない。実行時出力なので自己 hash も書かない。
- catalog は追加で既知 SHA-256 `7eb838...346f` と照合し、`catalog.render_catalog_json()` との byte equality も確認する。
- 失敗は transport を生成する前に返し、network-zero を構造化する。

**束縛対象の全 path**

コードと登録値:

- `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md`
- `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md`
- `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md`
- `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json`
- `orchestrator/axis_b5_search/__init__.py`
- `orchestrator/axis_b5_search/catalog.py`
- `orchestrator/axis_b5_search/anchor_registry.json`
- `orchestrator/axis_b5_search/parsers.py`
- `orchestrator/axis_b5_search/preflight.py`
- `orchestrator/axis_b5_search/runner.py`
- `orchestrator/schemas/axis_b5_search_page_evidence.schema.json`
- `orchestrator/schemas/axis_b5_search_live_preflight.schema.json`
- `orchestrator/schemas/axis_b5_search_registration_seal.schema.json`

fixture は下記 `fixture` 節の全 25 path を exact set で束縛する。`test_axis_b5_search_executor.py` と所要時間台帳は実行時意味論ではないため seal 対象外とする。

**live preflight**

16 anchor と索引別 membership は、`orchestrator/axis_b5_search/anchor_registry.json` に置く。コード内定数より、16 DOI、arXiv ID、W-ID、A-ID、membership をレビューしやすく、閉包記録 §1、§2、§4 の転記漏れを exact set test で検出できる。registration preflight がこの JSON を seal する。

registry は最低限 `anchor_id`、`slot`、`doi`、nullable `arxiv_id`、登録済み `openalex_work_id`、first/last A-ID、`member_indexes` を持つ。member は次の exact set とする。

- OpenAlex 16: `G1-01`、`G2-01`〜`G2-08`、`G3-01`〜`G3-07`
- arXiv 1: `G2-08`、主キー `1710.11258`
- DBLP 13: `G1-01`、`G2-04`〜`G2-08`、`G3-01`〜`G3-07`
- DBLP 非 member: `G2-01`〜`G2-03`

`preflight.py:272-340` の `build_lookup_request(member)` は閉包登録 1/2 §2.4 (b) のみから URL を作る。

- OpenAlex: `/works/https://doi.org/<DOI>?select=id,doi,title,publication_year,ids,authorships,referenced_works_count`
- arXiv: `/api/query?id_list=<arXiv ID>&max_results=1`
- DBLP: `/search/publ/api?q=<DOI percent encoding>&format=json&h=5`

`preflight.py:342-430` の索引別判定は次の逐語条件をコードへ固定する。

- OpenAlex:
  - `収録`: HTTP 200、JSON の `id` が `https://openalex.org/W...`
  - `非収録`: HTTP 404
  - `不達`: 通信失敗、timeout、上記以外の status、期待外 content type、整形不能 body
- arXiv:
  - `収録`: HTTP 200、`feed/entry` 1 件
  - `非収録`: HTTP 200、`opensearch:totalResults == 0`、entry 0 件
  - `不達`: 通信失敗、timeout、他 status、期待外 content type、整形不能または上記二形以外
- DBLP:
  - `収録`: HTTP 200、`application/json`、`result.hits.hit` に当該 DOI を持つ record
  - `非収録`: HTTP 200、`application/json`、`result.hits.@total == 0`
  - `不達`: 通信失敗、timeout、他 status、期待外 content type、HTML challenge、整形不能 body

`preflight.py:432-485` の `evaluate_live_preflight(records) -> LivePreflightResult` が、exact 30 member、重複なし、欠落なしを検査する。1 件でも `不達` または `非収録` なら `passed=False`、`axis_status="未完走"`、`may_start_run=False` を返す。runner はこの結果が真になる前に request を一切発行しない。

本 wave ではこの関数を fake transport と fixture だけで検査し、実 network へは接続しない。

## runner

**予定構成**

- `runner.py:1-75`: 凍結方針定数、例外、dataclass。
- `runner.py:77-150`: catalog loader と `LeafSpec` 正規化。
- `runner.py:152-275`: 期待 arXiv echo、OpenAlex AST、DBLP echo の導出。
- `runner.py:277-390`: catalog-only request builder。
- `runner.py:392-485`: production transport と allowlist。
- `runner.py:487-680`: 条件 1〜6 の page / leaf 評価。
- `runner.py:682-790`: raw body、page evidence、leaf evidence の create-only 出力。
- `runner.py:792-980`: retry、page loop、総件数 drift の 1 回再走。
- `runner.py:982-1060`: control 集合評価、公開 `run_leaf`、test-only seam。

**境界型**

`RequestSpec` は `leaf_kind`、`leaf_id`、`index`、`page_number`、`position_in`、method、scheme、host、path、順序つき query parameter、exact encoded URL、Accept headerを持つ。

`Response` は `status`、`headers: tuple[tuple[str,str], ...]`、`body: bytes`、`final_url` を持つ。同名 response header は順序つきで全て保存し、軸 1 の `_safe_response_headers` のような filter / deduplicate はしない。

`Transport` は `get(request: RequestSpec) -> Response` だけを持つ。fake transport はこの seam に入るが、production `run_leaf` に URL、request builder、parser を注入する引数は置かない。

**catalog-only 構造**

`resolve_leaf(catalog, leaf_id)` は `queries[]`、`controls[]`、`aux_venue_streams[]` の exact 一件だけを `LeafSpec` に変換する。ID が無い、複数に現れる、index と host が矛盾する場合は issuance 前に拒否する。

`build_request(leaf, page_number, position)` は次しか行わない。

- arXiv / DBLP: catalog の `request_template` に一つだけある `{POS}` を登録位置で置換
- OpenAlex: `{CUR}` を初回 literal `*`、二ページ目以降は `quote(cursor, safe="-_.~")` で置換
- 置換後 URL から ordered parameters を復元し、元 template の位置 placeholder 以外の byte が同一か再検査
- `first_page_url` と page 0 の byte equality を要求

production transport も catalog と `leaf_id/page/position` から request を再構築して `RequestSpec` と完全比較する。したがって public API から登録外 URL を組み立てる面がない。

host/path allowlist は以下の exact 三組である。

- `export.arxiv.org` + `/api/query`
- `api.openalex.org` + `/works`
- `dblp.org` + `/search/publ/api`

**B5 固有 policy**

軸 1 の [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:292) は catalog の `index_policies` から読むが、B5 catalog にはその field がない。`runner.py:25-55` に次を逐語転記し、その bytes を registration preflight で seal する。

```text
PAGE_SIZE = {"arxiv": 200, "openalex": 200, "dblp": 100}
PAGINATION = {"arxiv": "start", "openalex": "cursor", "dblp": "f"}
RETRY_DELAYS_S = (3.0, 6.0, 12.0)
MAX_RETRIES = 3
```

3 retry は初回発行後の再試行 3 回、最大 4 attempt とする。各 attempt の body、status、headers、開始・完了 UTC、失敗理由を別証拠に残す。

位置遷移は arXiv `0,200,400,...`、DBLP `0,100,200,...`。実要素数を位置 step に使わない。OpenAlex は初回 `*`、以後直前 response の `meta.next_cursor` のみを使う。

**6 条件**

- 条件 1:
  - arXiv / DBLP は percent decode 1 回、連続空白縮約、arXiv の date range 括弧・引用符差だけを許容。
  - OpenAlex は term group と cutoff から期待 OQO を構築。兄弟順だけ無視し、多重度、入れ子、深さ、join、field、型、`get_rows == "200"` を保存。unknown key、unknown join、重複 JSON key は拒否。
  - DBLP echo は語を空白とハイフンで token 化し、各末尾へ `*`。
- 条件 2:
  - request 位置と response 位置の一致、固定 step、cursor parent chainを検査。
  - 非最終ページが page size より短ければ `silent_truncation`。
- 条件 3:
  - `actual_count` は entry/results/hit の `len` だけ。
  - 非最終は 200/200/100 と一致。
  - 最終は offset 系で `position + actual_count == declared_total`。
  - `itemsPerPage`、`meta.per_page`、`@sent` は証拠にだけ使う。
- 条件 4:
  - page 内・page 間の `index_work_id` の反復を検出し拒否。反復 occurrence は ledger に残す。
- 条件 5:
  - 全 page の `declared_total` が存在し同一。
  - distinct index work ID 数がその値と一致。
  - drift は証拠を保存した上で query 全体を page 0 から一度だけ再走し、二走目も drift なら `未完走`。
- 条件 6:
  - 最終 page の status 200、期待 content type、final URL の同一 host、総件数 field 存在。
  - 全 page の status、content type、final URL、byte count、全 header、body SHA-256 を保存。

0 件は、総件数 0、実要素 0、正常終端を満たせば完走とする。

control と補助 stream は、凍結文が要求する条件 2、3、5、6 を gating 条件にする。条件 1、4 も診断値として記録するが、追加 gate にはしない。`shares_request_with` は exact URL の取得 cacheで一回だけ発行し、双方の control ID が同じ取得証拠を参照する。

checkpoint / resume、複数窓の二走一致は P3 のとおりこの fileへ入れない。

## schema

追加する file は次の三つ。

**`orchestrator/schemas/axis_b5_search_page_evidence.schema.json`**

draft-07、self-contained、全 object `additionalProperties: false`。

- `header_pair`
- `identity`
- `request`
- `response`
- `occurrence`
- `parse`
- `duplicate_occurrence`
- `condition_result`
- `page_evidence`
- `leaf_evidence`
- `record_occurrence_ledger`

page evidence は request bytes と SHA-256、位置、開始・完了 UTC、全 response header、body path/hash/bytes、宣言総数、宣言 page size、実要素数、解釈後 query text/AST、ID 列、条件結果を必須にする。

**`orchestrator/schemas/axis_b5_search_live_preflight.schema.json`**

- `anchor_registry`
- `anchor`
- `lookup_request`
- `lookup_response`
- `lookup_result`
- `live_preflight_record`

`lookup_result.state` は `収録` / `非収録` / `不達` の enum。top-level は expected/observed member count を index ごとに持ち、`30` を schema と cross-field checker の双方で検査する。

**`orchestrator/schemas/axis_b5_search_registration_seal.schema.json`**

- `file_binding`
- `registration_seal_record`

binding は path、mode、git blob、byte count、SHA-256。record は registration commit、catalog SHA-256、exact path set、検査時刻、`passed`、reason codeを持つ。record 自身の digest field は置かない。

軸 1 schema からは SHA-256、header pair、identity、request、response、occurrence、condition result の閉じた object 設計を写す。WAL、quota、checkpoint、axis status の未実装層、bundle manifest は写さない。外部共通 schema を新設せず、各 B5 schema に必要な小定義だけ重複させる。

## fixture

`orchestrator/tests/fixtures/axis_b5_search/` に次を置く。

**probe から byte exact に複製する live fixture**

- `live/arxiv_present.body` ← `probe/ax_known.body`
- `live/arxiv_present.hdr` ← `probe/ax_known.hdr`
- `live/arxiv_absent.body` ← `probe/ax_missing.body`
- `live/arxiv_absent.hdr` ← `probe/ax_missing.hdr`
- `live/openalex_present.body` ← `probe/oa_ccbench.body`
- `live/openalex_present.hdr` ← `probe/oa_ccbench.hdr`
- `live/openalex_absent.body` ← `probe/oa_missing.body`
- `live/openalex_absent.hdr` ← `probe/oa_missing.hdr`
- `live/dblp_unreachable.body` ← `probe/dblp_api_doi.body`
- `live/dblp_unreachable.hdr` ← `probe/dblp_api_doi.hdr`

OpenAlex 404 は実応答が HTML なので、404 を content type より先に `非収録` とする precedence test に使える。DBLP body は Anubis HTML、header は HTTP 200 `text/html` なので、status だけ見て `収録` にしない負例になる。

**凍結文から合成する page fixture**

- `pages/arxiv_terminal_partial.xml`
- `pages/arxiv_page_0_full.xml`
- `pages/arxiv_page_1_terminal.xml`
- `pages/openalex_terminal_partial.json`
- `pages/openalex_page_0_full.json`
- `pages/openalex_page_1_terminal.json`
- `pages/openalex_nonterminal_short.json`
- `pages/openalex_total_drift_page_1.json`
- `pages/openalex_duplicate_across_pages_1.json`
- `pages/dblp_terminal_partial.json`
- `pages/dblp_page_0_full.json`
- `pages/dblp_page_1_terminal.json`
- `pages/dblp_nonterminal_sent_full_hits_short.json`
- `pages/dblp_missing_year.json`
- `pages/dblp_duplicate_within_page.json`

合成値は test file 冒頭で先に固定する。

- page size: 部分登録 §3.3、§5.1
- offset: 0→200、0→100
- 例示総数: 201 / 101 は test 用に先に選ぶ
- 最終実数: 1
- OpenAlex cursor token: 固定 literal
- work ID: test 側で固定した distinct ID 列
- expected AST / DBLP echo: 部分登録 §3.4、閉包登録 1/2 §3.4 項目 10

fixture を読み込んでから `len`、総数、cursor、ID を期待値に転用しない。特に負例は次の形にする。

- OpenAlex: `meta.per_page=200`、`results` 199、`next_cursor` 有り
- DBLP: `@sent=100`、`hit` 99、`@total>99`
- total drift: page 0 と page 1 の `meta.count` が異なる
- 最終部分 page: 宣言 page size 200 / 100、実要素 1

## test 一覧

`orchestrator/tests/test_axis_b5_search_executor.py` の予定 test は以下。括弧内は期待値の根拠。

**parser と条件 1**

- `test_arxiv_parser_preserves_positions_totals_declared_size_actual_ids_and_echo`（部分登録 §5.1 条件 1〜4、§7）
- `test_openalex_parser_preserves_oql_and_typed_oqo_separately`（部分登録 §3.4、§5.1 条件 1）
- `test_openalex_parser_rejects_duplicate_json_members`（部分登録 §5.1 条件 1）
- `test_dblp_parser_keeps_missing_year_as_ruling_item`（部分登録 §2.2）
- `test_c1_accepts_registered_arxiv_normalizations` / `test_c1_rejects_arxiv_semantic_echo_change`（部分登録 §5.1 条件 1）
- `test_c1_accepts_openalex_sibling_permutation` / `test_c1_rejects_openalex_multiplicity_nesting_join_key_type_or_get_rows_change`（部分登録 §3.4、§5.1 条件 1）
- `test_c1_accepts_registered_dblp_hyphen_echo` / `test_c1_rejects_dblp_token_change`（閉包登録 1/2 §3.4 項目 10）

**条件 2**

- `test_c2_accepts_registered_position_sequences_by_index`（部分登録 §3.3、§5.1 条件 2）
- `test_c2_rejects_offset_gap_or_cursor_not_from_parent`（同）
- `test_c2_rejects_short_nonterminal_page_even_when_declared_size_is_full`（部分登録 §5.1 条件 2、規律 2）

**条件 3**

- `test_c3_accepts_full_nonterminal_and_partial_terminal_pages`（部分登録 §5.1 条件 3）
- `test_c3_rejects_openalex_per_page_used_as_actual_count`（`meta.per_page=200`、実 results 199、同条件 3、規律 2）
- `test_c3_rejects_dblp_sent_used_as_actual_count`（`@sent=100`、実 hit 99、同条件 3、規律 2）
- `test_c3_accepts_terminal_declared_page_size_different_from_actual_count`（同条件 3 の最終 page 規則）

**条件 4**

- `test_c4_accepts_distinct_index_work_ids`（部分登録 §5.1 条件 4）
- `test_c4_rejects_and_records_duplicate_ids_within_or_across_pages`（同）
- `test_c4_does_not_merge_distinct_work_ids_with_same_family_key`（部分登録 §7 work-family）

**条件 5**

- `test_c5_accepts_distinct_id_count_equal_to_stable_total`（部分登録 §5.1 条件 5）
- `test_c5_rejects_unique_count_mismatch`（同）
- `test_c5_reruns_total_drift_once_and_accepts_stable_second_run`（同条件 5）
- `test_c5_rejects_total_drift_on_second_run_without_third_run`（同条件 5）

**条件 6**

- `test_c6_accepts_exact_status_content_host_total_and_complete_evidence`（部分登録 §5.1 条件 6、§2.1）
- `test_c6_rejects_bad_status_content_host_missing_total_or_empty_body`（部分登録 §5.1 条件 6、§5.3）
- `test_zero_result_terminal_leaf_is_complete`（部分登録 §5.1 の「0 件」）

**registration preflight**

- `test_registration_preflight_accepts_exact_commit_blobs_and_emits_schema_valid_seal`（部分登録 §5.3）
- `test_registration_preflight_rejects_each_bound_path_one_byte_mutation`（同）
- `test_registration_preflight_rejects_missing_extra_symlink_or_dirty_fixture`（同）
- `test_registration_preflight_failure_causes_zero_transport_calls`（部分登録 §0、§5.3）
- `test_registration_seal_does_not_hash_itself`（自己参照禁止）

**live preflight**

- `test_live_preflight_builds_exact_16_1_13_registered_requests`（閉包登録 1/2 §2.4 (a)(b)）
- `test_live_preflight_classifies_each_registered_positive_and_negative_shape`（同 §2.4 (b)）
- `test_openalex_404_html_is_nonincluded_not_unreachable`（同表と probe）
- `test_dblp_http_200_html_challenge_is_unreachable`（同 §2.4 (b)、§6）
- `test_live_preflight_any_nonincluded_or_unreachable_blocks_entire_axis`（同 §2.4 (c)）
- `test_live_preflight_rejects_missing_extra_or_duplicate_member_record`（同 §2.4 (a)(d)）

**runner と schema**

- `test_runner_resolves_query_control_and_venue_stream_from_catalog_only`（catalog 3 collection）
- `test_public_runner_has_no_url_request_builder_or_parser_injection`（catalog-only 要求）
- `test_transport_rejects_unknown_host_path_parameter_order_or_header`（部分登録 §3.3、§5.1 条件 6）
- `test_openalex_first_cursor_is_literal_star_and_later_cursor_is_percent_encoded`（部分登録 §3.3）
- `test_retry_uses_exact_three_six_twelve_delays_and_stops_after_three_retries`（部分登録 §5.3）
- `test_control_shared_request_is_fetched_once_and_referenced_twice`（部分登録 §4.1）
- `test_page_and_leaf_evidence_validate_draft7_schemas`（部分登録 §7）
- `test_parser_fields_equal_schema_required_fields`（軸 1 test の先例）
- `test_fixture_exact_set_matches_registration_binding`（部分登録 §5.3）

末尾には軸 1 と同じ次の自走 harness を置く。

```python
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
```

## 曖昧・不足・矛盾

| 項目 | 判定 | 推奨 |
|---|---|---|
| page size 200 / 200 / 100 と offset step | 凍結文から一意に読める | runner 定数へ逐語転記 |
| retry 3 回と 3→6→12 秒 | 凍結文から一意に読める | 初回 + retry 3 回、最大 4 attempt |
| 実要素数の locator | 凍結文から一意に読める | entry/results/hit の `len` のみ |
| OpenAlex `get_rows` | 凍結文から一意に読める | 軸 1 の `"works"` でなく文字列 `"200"` |
| DBLP `year` 欠落 | 凍結文から一意に読める | 除外せず `要裁定` 情報を保持 |
| live member 16 / 1 / 13 | 凍結文から一意に読める | registry の exact set とする |
| 本走の期待 content type の exact 集合 | 読めないので親の erratum 裁定が要る | arXiv は `application/atom+xml`、OpenAlex / DBLP は `application/json` の media type exact、charset parameter は無視 |
| connect/read timeout | 読めないので親の erratum 裁定が要る | 30 秒を request ごとの固定 timeout として登録 |
| 通常 request 間隔、User-Agent、rate-limit threshold | 読めないので親の erratum 裁定が要る | live preflight で値を記録するだけにし、実行 policy は人間認可時に追補。閉包登録 §5 の 1 秒規則を本走へ無断転用しない |
| OpenAlex 条件 3 の「位置 + 実要素数」 | cursor は加算不能なので読めない。部分登録内に型矛盾がある | 非終端は `actual_count == 200`、終端は `next_cursor == null` かつ累積実要素数 `== meta.count` |
| arXiv の解釈後 query の exact feed title 形 | 正規化規則はあるが prefix と paging parameter の期待形が読めない | parser が feed title を勝手に切らず、親 erratum で expected title construction を固定 |
| retry 対象となる失敗集合 | 上限は読めるが、どの失敗を retry するか読めない | 429、503、通信失敗、timeout、空 bodyだけを retry。その他 status と整形済み不一致は即 `未完走` |
| OpenAlex 404 が HTML の場合 | 表と実 probe から一意に読める | status 404 を先に `非収録` とし、content type 判定を適用しない |
| DBLP が正常 JSON、total > 0、しかし exact DOI 無し | `収録` と表の `非収録` のどちらにも一致せず読めない | 正常応答だが当該 record 不在なので `非収録` とする erratum |
| DBLP record 内の DOI locator | 「当該 DOI を持つ」だけで exact field が読めない | `info.doi` と DOI URL を含む `info.ee` の双方を正規化して照合 |
| same-host redirect を追うか | 条件 6 は final host のみを規定し、redirect policy は読めない | automatic redirect を無効化し、3xx を失敗とする。catalog 外 URL への自動 issuance を防ぐ |
| live OpenAlex lookup の W-ID / A-ID が閉包記録と変化した場合 | 3 値だけでは帰結が読めない | `収録` のまま通さず、identity drift reason を付けて `may_start_run=False` とする追補が必要 |
| control に条件 1 / 4 を gating するか | §4.1 は条件 2、3、5、6 だけを明記するため読めるが、主 query の六条件とは非対称 | 1 / 4 は記録のみ、gate は 2 / 3 / 5 / 6 |
| 閉包記録 §4 の anchor 依存 61 stream を本 runner に含めるか | scope は frozen catalog leaf を指定する一方、61 stream は catalog 外なので読めない | 本 wave は catalog の query/control/venue stream に限定。61 stream の executable registry は次 waveで別途 seal |
| S6 を「各単位が自分の test」としつつ単一 test path を重複なく所有する方法 | brief 内で両立せず、親の分割裁定が要る | B が統合 test file を所有し、A は parser 型と fixture 期待表を handoff する |

上の「読めない」項目はコード側の便宜で固定すると事後的な実行契約になる。少なくとも content type、timeout、OpenAlex terminal、arXiv echo、DBLP lookup の中間形は、author 着手前に親が erratum として裁定すべきである。

## 変異候補

| # | 変異位置の目安 | 変異 | 期待する赤 test | 単一理由性の懸念 |
|---:|---|---|---|---|
| 1 | `parsers.py:180/285/385` | `actual_count` を declared page size に置換 | `test_c3_rejects_openalex_per_page_used_as_actual_count` または DBLP 版 | parser field test も赤になるため mutation spec は一方だけを expected nodeにする |
| 2 | `parsers.py:200,410` | 次 offset を `position + actual_count` にする | `test_c2_rejects_offset_gap_or_cursor_not_from_parent` | C3 と同時に赤になり得るので short page の C2 test を独立構成 |
| 3 | `runner.py:330` | 初回 `*` を `%2A` にする | `test_openalex_first_cursor_is_literal_star_and_later_cursor_is_percent_encoded` | catalog byte test とは分離する |
| 4 | `runner.py:410` | host を suffix match に緩和 | `test_transport_rejects_unknown_host_path_parameter_order_or_header` | path mutationと同じ param caseに混ぜず、明示 id を付ける |
| 5 | `runner.py:520` | OpenAlex AST の children を set 化 | `test_c1_rejects_openalex_multiplicity_nesting_join_key_type_or_get_rows_change[multiplicity]` | parameterized nodeid を事前登録する |
| 6 | `runner.py:590` | duplicate ID 検査前に deduplicate | `test_c4_rejects_and_records_duplicate_ids_within_or_across_pages` | C5 mismatchも赤にならない同数置換 fixtureを使う |
| 7 | `runner.py:620` | 条件 5 を occurrence 数で判定 | `test_c5_rejects_unique_count_mismatch` | C4 を通る distinct fixtureに限定 |
| 8 | `runner.py:650` | total drift を最終 page の値で受理 | `test_c5_rejects_total_drift_on_second_run_without_third_run` | request count assertionで第三走も同時検出 |
| 9 | `runner.py:850` | retry delay の 6 を削除 | `test_retry_uses_exact_three_six_twelve_delays_and_stops_after_three_retries` | attempt 数と delay 列のどちらを理由にするか assertion を分ける |
| 10 | `preflight.py:455` | `all(state=="収録")` を `any` にする | `test_live_preflight_any_nonincluded_or_unreachable_blocks_entire_axis` | member count failureを混ぜない |
| 11 | `preflight.py:220` | fixture pathを binding set から一件削除 | `test_fixture_exact_set_matches_registration_binding` | byte mutation testと別 mutantにする |
| 12 | `runner.py:445` | final host 検査を削除 | `test_c6_rejects_bad_status_content_host_missing_total_or_empty_body[host]` | content type/status paramと nodeidを分離 |

## リスク

[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:6614) は主に living docs、参照 path、handoff、archive、dispatch 文書を検査する。今回の frozen docs は変更しないため、新 schema や fixtureを文書へ追記する必要はない。むしろ凍結文へ path を追記すると不変条件違反になる。実装後は full checker を走らせ、既存文書の path referenceが新 file名と食い違っていないことだけ確認する。

[check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_ai_provenance.py:1536) は `orchestrator/` 配下の非 Markdown/RSTを全て実装面とする。したがって Python、schema JSON、anchor registry、fixture、test、`acceptance_duration_ledger.json` の全てが D95 対象である。commit には Codex `role=author` trailer が必要で、commit 後に履歴監査を実施する。

新 test file は [test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_plain_runner_coverage.py:35) の `_self_runnable` 判定を満たす必要がある。pytest fixtureと parametrize を使うため、README allowlistを変更せず、末尾の `pytest.main([__file__])` を採る。焦点走には新 test fileと `test_plain_runner_coverage.py` を含める。

所要時間台帳は現状 `schema_version=1`、`unit="seconds"`、`duration_seconds_by_nodeid`、`nodeid_count` の形である。追加手順は次のとおり。

1. 新 test の全 parameter IDを明示して nodeidを安定化する。
2. `tools/run_tests.py` 経由で新 test fileを単独実行し、JUnit XMLを出す。
3. 緑の JUnit に対して `python3 tools/update_acceptance_duration_ledger.py --add-only <JUnit>` を実行する。
4. 同じ JUnit と `--add-only --check` で生成 bytes が一致することを確認する。
5. `nodeid_count` と追加された全 nodeidを確認し、失敗または error case が台帳へ入っていないことを確認する。
6. `test_update_acceptance_duration_ledger.py`、`test_plain_runner_coverage.py`、新 test fileを焦点走する。
7. 全受入、`check_codex_agents.py`、`check_docs.py` を通し、commit 後に `check_ai_provenance.py` を通す。

台帳は共有 fileなので、B が最後に JUnit から一度だけ `--add-only` 更新する。手書きの秒数や fixture 観測値を転記しない。

本 wave の read-only plan では checker、pytest、live preflight は実行していない。

## 所有分割

先に次の境界を固定する。

- A が `Occurrence` と `ParsedPage` の field、型、parse error codeを確定する。
- B はその型を `orchestrator.axis_b5_search.parsers` から importする。
- B は parser の private helperへ依存しない。
- B が使うのは `parse_*_page(body, page_number)` と dataclass fieldだけ。
- `actual_count` は実 container 長、`declared_page_size` は response宣言値という意味を変更しない。
- `occurrences` は重複を含む順序つき列である。
- OpenAlex AST は `interpreted_query_ast`、raw OQL は `interpreted_query_text`。
- A 完了後、B は dataclass field exact-set testを最初に置いて境界 driftを検出する。

**単位 A = S1 + S5**

- `orchestrator/axis_b5_search/parsers.py`
- `orchestrator/tests/fixtures/axis_b5_search/**`

A は frozen docs、`catalog.py`、catalog JSON、schema、preflight、runner、統合 test、台帳を編集しない。A の handoff は型表、fixture path表、凍結節由来の期待値表を持つ。

**単位 B = S2 + S3 + S4 + 統合 S6**

- `orchestrator/axis_b5_search/anchor_registry.json`
- `orchestrator/axis_b5_search/preflight.py`
- `orchestrator/axis_b5_search/runner.py`
- `orchestrator/schemas/axis_b5_search_page_evidence.schema.json`
- `orchestrator/schemas/axis_b5_search_live_preflight.schema.json`
- `orchestrator/schemas/axis_b5_search_registration_seal.schema.json`
- `orchestrator/tests/test_axis_b5_search_executor.py`
- `orchestrator/tests/acceptance_duration_ledger.json`

既存 `orchestrator/axis_b5_search/__init__.py` は、公開 exportが不要なら変更しない。registration preflight は現在 bytesも sealする。

この分割なら所有 path は重複しない。brief の「各単位が自分の test」を文字どおり満たすには単一 test fileの共同所有が必要になり、依頼の非重複条件と矛盾するため、B が統合 testを所有する読みを推奨する。

## 総括

実装の核は、軸 1 の parser/evidence 構造を局所的に写しつつ、B5 固有の三点を分離することである。

- policy は catalog に後付けせず、runner の sealed 定数に置く。
- live member と anchor 主キーは sealed `anchor_registry.json` に置く。
- `actual_count`、declared page size、索引固有 ID、OpenAlex ASTを別 fieldにし、規律 2 の混同を型と負例で防ぐ。

着手前に親の erratum が特に必要なのは、期待 content type、timeout、OpenAlex cursor終端、arXiv echo exact形、DBLP lookup の「total > 0だが DOIなし」の扱いである。凍結 catalog、`catalog.py`、三つの凍結文書は一切変更しない。