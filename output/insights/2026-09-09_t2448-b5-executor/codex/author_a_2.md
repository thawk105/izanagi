## 実装した内容

- [parsers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/orchestrator/axis_b5_search/parsers.py:1) を新規実装。
  - 軸 1 を import しない独立 parser。
  - offset 系は現在位置のみ保存し、次位置を計算しない。
  - `actual_count` は response container の要素数のみ使用。
  - occurrence の順序・重複を保持。
  - DBLP cutoff を raw year・採否・要裁定へ分離。
  - OpenAlex AST を重複 key と未知構造を保持できる形で保存。
  - malformed body は例外ではなく固定 `parse_errors` を返す。
- [fixture root](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/orchestrator/tests/fixtures/axis_b5_search) に実応答 10 file と合成 fixture 14 file を追加。
- [test_axis_b5_search_parsers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/orchestrator/tests/test_axis_b5_search_parsers.py:1) に契約 1〜7 の正例・負例、計 20 test と自走 harness を追加。

## 境界契約 (単位 B へ渡す表)

`JsonValue` は `None | bool | int | float | str | JsonObject | tuple[JsonValue, ...]`。JSON array は tuple、object は次の `JsonObject` で表す。

| dataclass | field | 型 | 意味 |
|---|---|---|---|
| `JsonObject` | `members` | `tuple[tuple[str, JsonValue], ...]` | JSON object の順序付き member。重複 key を保持 |
| `Occurrence` | `index_work_id` | `str \| None` | 索引固有 work ID |
| `Occurrence` | `page_number` | `int` | 呼び手が渡した page 番号 |
| `Occurrence` | `ordinal` | `int` | container 内の 0 始まり順序 |
| `Occurrence` | `raw_year` | `JsonValue` | DBLP の raw `year`。他索引または欠落は `None` |
| `Occurrence` | `included_by_cutoff` | `bool \| None` | DBLP の `<= 2026` は `True`、`> 2026` は `False`、欠落・不正は `None` |
| `Occurrence` | `requires_ruling` | `bool` | DBLP year 欠落・非 4 桁なら `True` |
| `ParsedPage` | `index` | `str` | `arxiv` / `openalex` / `dblp` |
| `ParsedPage` | `page_number` | `int \| None` | 有効な入力 page 番号。入力不正時は `None` |
| `ParsedPage` | `declared_total` | `int \| None` | 索引の総件数 field |
| `ParsedPage` | `capacity_echo` | `int \| None` | `itemsPerPage` / `meta.per_page` / `@sent`。判定には使わない |
| `ParsedPage` | `actual_count` | `int` | container の実要素数 |
| `ParsedPage` | `position` | `int \| None` | arXiv `startIndex` または DBLP `@first`。OpenAlex は `None` |
| `ParsedPage` | `next_cursor` | `str \| None` | OpenAlex `meta.next_cursor` の無加工値。offset 系は常に `None` |
| `ParsedPage` | `interpreted_query_text` | `str \| None` | arXiv `feed/title`、OpenAlex `oql`、DBLP `result.query` |
| `ParsedPage` | `interpreted_query_ast` | `JsonValue` | OpenAlex `oqo`。他索引または欠落は `None` |
| `ParsedPage` | `occurrences` | `tuple[Occurrence, ...]` | 重複を除去しない順序付き occurrence |
| `ParsedPage` | `parse_errors` | `tuple[str, ...]` | 固定 snake_case error code 列 |

公開関数は次の 3 本です。

| 関数 | signature |
|---|---|
| arXiv | `parse_arxiv_page(body: bytes, page_number: int) -> ParsedPage` |
| OpenAlex | `parse_openalex_page(body: bytes, page_number: int) -> ParsedPage` |
| DBLP | `parse_dblp_page(body: bytes, page_number: int) -> ParsedPage` |

parse error code の全一覧です。

| 分類 | code |
|---|---|
| 入力 | `invalid_body_type`, `invalid_page_number` |
| body | `invalid_xml`, `invalid_json`, `json_root_not_object` |
| 共通 echo | `missing_declared_total`, `invalid_declared_total`, `missing_capacity_echo`, `invalid_capacity_echo`, `missing_position`, `invalid_position`, `missing_interpreted_query_text`, `invalid_interpreted_query_text` |
| work ID | `missing_index_work_id`, `invalid_index_work_id` |
| OpenAlex | `missing_meta`, `invalid_meta`, `missing_results`, `invalid_results`, `invalid_result`, `missing_x_query`, `invalid_x_query`, `missing_interpreted_query_ast`, `invalid_interpreted_query_ast`, `invalid_next_cursor` |
| DBLP | `missing_result_object`, `invalid_result_object`, `missing_hits_object`, `invalid_hits_object`, `invalid_hit_collection`, `invalid_hit`, `missing_info_object`, `invalid_info_object` |

DBLP year の欠落・不正は page parse failure にせず、`included_by_cutoff=None` と `requires_ruling=True` で運びます。

fixture manifest は次のとおりです。path は fixture root 相対です。

| path | 表す形 |
|---|---|
| `real/2026-09-07_ax_known.body` | arXiv 命中実応答の byte copy |
| `real/2026-09-07_ax_known.hdr` | 同応答 header |
| `real/2026-09-07_ax_missing.body` | arXiv 不在実応答の byte copy |
| `real/2026-09-07_ax_missing.hdr` | 同応答 header |
| `real/2026-09-07_oa_ccbench.body` | OpenAlex 命中 lookup 実応答の byte copy |
| `real/2026-09-07_oa_ccbench.hdr` | 同応答 header |
| `real/2026-09-07_oa_missing.body` | OpenAlex 404 実応答の byte copy |
| `real/2026-09-07_oa_missing.hdr` | 同応答 header |
| `real/2026-09-07_dblp_api_doi.body` | DBLP anti-bot HTML 実応答の byte copy |
| `real/2026-09-07_dblp_api_doi.hdr` | 同応答 header |
| `synthetic/arxiv_nonfinal_full.xml` | 小容量の非最終満杯 page |
| `synthetic/arxiv_nonfinal_short.xml` | `capacity_echo=200`、実要素 1 の非最終短 page |
| `synthetic/arxiv_final.xml` | 部分的な最終 page |
| `synthetic/arxiv_page_duplicate.xml` | page 内 work ID 重複 |
| `synthetic/arxiv_cross_page_1.xml` | page 間重複の第 1 page |
| `synthetic/arxiv_cross_page_2.xml` | page 間重複の第 2 page |
| `synthetic/arxiv_missing_total.xml` | 総件数 field 欠落 |
| `synthetic/arxiv_invalid.xml` | malformed XML |
| `synthetic/openalex_cursor_page_1.json` | cursor 連鎖第 1 page、非 null `next_cursor` |
| `synthetic/openalex_cursor_page_2.json` | cursor 終端、`next_cursor=null` |
| `synthetic/openalex_ast_duplicate_unknown.json` | AST の重複 key・未知 key・未知構造 |
| `synthetic/openalex_invalid.json` | malformed JSON |
| `synthetic/dblp_cutoff.json` | year 2026、2027、欠落、非 4 桁を含む最終 page |
| `synthetic/dblp_nonfinal_short.json` | `capacity_echo=100`、実 hit 1 の非最終短 page |

## 実走した test

pytest test child は実走できていません。次の範囲を repository dispatcher へ計 3 回渡しましたが、すべて child 起動前に `qstat -Q preflight rc=1`、dispatcher `rc=16` となりました。

- `orchestrator/tests/test_axis_b5_search_parsers.py`
- `orchestrator/tests/test_axis_b5_search_parsers.py` と `orchestrator/tests/test_plain_runner_coverage.py`

したがって緑は主張しません。

非 pytest の診断では次を確認済みです。

- production/test 両 Python file の `ast.parse` 成功。
- production module の import 成功、error code は 33 個。
- 合成 fixture 14 個を対応 parser へ入力し、例外なし。
- 実応答 body/header 10 file は `cmp` で出所と byte 一致。
- production parser に `axis1_search`、`position_out`、位置と `len` を組み合わせた次位置計算が無いことを静的確認。
- U+0300〜U+036F が所有成果物に無いことを確認。

## 波及可能性

| 対象 | 波及 |
|---|---|
| 単位 B の `runner.py` | 上表の `ParsedPage`、`Occurrence`、`JsonObject` と 3 parser を直接 consumer とする |
| 単位 B の schema | `JsonObject.members` と tuple、DBLP cutoff の 3 値を直列化する必要がある |
| 単位 B の preflight / seal | parser file と fixture root の exact file set に今回の全 path を含める必要がある |
| `orchestrator/axis_b5_search/__init__.py` | 公開 re-export が必要なら単位 B の所有範囲で行う |
| executor consumer test | cursor、短 page、重複、総件数欠落、cutoff fixture を共有可能 |
| acceptance duration ledger | 段 4 裁定どおり、単位 B が JUnit 実測から一度だけ更新する。単位 A は未編集 |
| DBLP year consumer | year 欠落・不正を `parse_errors` ではなく `requires_ruling` で判定する必要がある |

dispatcher の失敗 receipt は通常動作として `output/pegasus-dispatch/` に生成されています。docs、catalog、`__init__.py`、既存 test、台帳は編集していません。

## 未実走・未実装

- 新規 parser test 20 node と `test_plain_runner_coverage.py` は未実走です。
- queue 状態も観測不能で、計算 node child は一度も開始されませんでした。
- 所有範囲の実装項目に意図的な未実装はありません。
- `closed` とは申告しません。
- commit と git 操作は行っていません。

## 総括

parser、実応答・合成 fixture、契約 test の実装は完了しています。境界契約は上表で単位 B へ渡せますが、Pegasus dispatcher の `rc=16` により pytest は未実走のため、状態は「実装済み・未実走」です。