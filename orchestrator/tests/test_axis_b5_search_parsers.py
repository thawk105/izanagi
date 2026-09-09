"""Contract tests for the Axis B5 stored-response parsers."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

import orchestrator.axis_b5_search.parsers as parser_module
from orchestrator.axis_b5_search.parsers import (
    PARSE_ERROR_CODES,
    JsonObject,
    parse_arxiv_page,
    parse_dblp_page,
    parse_openalex_page,
)


_FIXTURES = Path(__file__).parent / "fixtures" / "axis_b5_search"


def _fixture(relative_path: str) -> bytes:
    return (_FIXTURES / relative_path).read_bytes()


def _member_values(value: JsonObject, key: str) -> tuple[object, ...]:
    return tuple(item for member_key, item in value.members if member_key == key)


def test_contract_1_accepts_valid_page_with_b5_parser() -> None:
    page = parse_arxiv_page(_fixture("synthetic/arxiv_nonfinal_full.xml"), 0)

    assert page.index == "arxiv"
    assert page.actual_count == 2
    assert page.parse_errors == ()


def test_contract_1_rejects_axis1_parser_dependency() -> None:
    source = inspect.getsource(parser_module)
    tree = ast.parse(source)
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    assert all("axis1_search" not in name for name in imported_modules)
    assert "orchestrator.axis1_search" not in source


def test_contract_2_accepts_openalex_cursor_chain_verbatim() -> None:
    first = parse_openalex_page(
        _fixture("synthetic/openalex_cursor_page_1.json"), 0
    )
    terminal = parse_openalex_page(
        _fixture("synthetic/openalex_cursor_page_2.json"), 1
    )

    assert first.next_cursor == "cursor-token:2/+=="
    assert terminal.next_cursor is None
    assert first.position is None
    assert terminal.position is None


def test_contract_2_rejects_calculated_offset_next_position() -> None:
    arxiv = parse_arxiv_page(_fixture("synthetic/arxiv_nonfinal_full.xml"), 0)
    dblp = parse_dblp_page(_fixture("synthetic/dblp_nonfinal_short.json"), 0)

    assert arxiv.position == 0
    assert dblp.position == 0
    assert arxiv.next_cursor is None
    assert dblp.next_cursor is None
    assert "position_out" not in arxiv.__dataclass_fields__
    assert "position_out" not in dblp.__dataclass_fields__


def test_contract_3_accepts_container_count_for_full_and_final_pages() -> None:
    full = parse_arxiv_page(_fixture("synthetic/arxiv_nonfinal_full.xml"), 0)
    final = parse_arxiv_page(_fixture("synthetic/arxiv_final.xml"), 1)

    assert (full.declared_total, full.capacity_echo, full.actual_count) == (4, 2, 2)
    assert (final.declared_total, final.capacity_echo, final.actual_count) == (3, 2, 1)


def test_contract_3_rejects_capacity_echo_as_actual_count() -> None:
    arxiv = parse_arxiv_page(_fixture("synthetic/arxiv_nonfinal_short.xml"), 0)
    dblp = parse_dblp_page(_fixture("synthetic/dblp_nonfinal_short.json"), 0)

    assert (arxiv.capacity_echo, arxiv.actual_count) == (200, 1)
    assert (dblp.capacity_echo, dblp.actual_count) == (100, 1)
    assert arxiv.actual_count != arxiv.capacity_echo
    assert dblp.actual_count != dblp.capacity_echo


def test_contract_4_accepts_distinct_occurrences_in_container_order() -> None:
    page = parse_arxiv_page(_fixture("synthetic/arxiv_nonfinal_full.xml"), 7)

    assert tuple(item.index_work_id for item in page.occurrences) == (
        "https://arxiv.org/abs/0001.00001v1",
        "https://arxiv.org/abs/0001.00002v1",
    )
    assert tuple((item.page_number, item.ordinal) for item in page.occurrences) == (
        (7, 0),
        (7, 1),
    )


def test_contract_4_rejects_page_local_deduplication() -> None:
    page = parse_arxiv_page(_fixture("synthetic/arxiv_page_duplicate.xml"), 3)

    assert page.actual_count == 2
    assert tuple(item.index_work_id for item in page.occurrences) == (
        "https://arxiv.org/abs/0004.00001v1",
        "https://arxiv.org/abs/0004.00001v1",
    )
    assert tuple(item.ordinal for item in page.occurrences) == (0, 1)


def test_contract_4_rejects_cross_page_deduplication() -> None:
    first = parse_arxiv_page(_fixture("synthetic/arxiv_cross_page_1.xml"), 0)
    second = parse_arxiv_page(_fixture("synthetic/arxiv_cross_page_2.xml"), 1)
    combined = first.occurrences + second.occurrences

    assert tuple(item.index_work_id for item in combined) == (
        "https://arxiv.org/abs/0005.00001v1",
        "https://arxiv.org/abs/0005.00001v1",
    )
    assert tuple((item.page_number, item.ordinal) for item in combined) == (
        (0, 0),
        (1, 0),
    )


def test_contract_5_accepts_four_digit_year_at_cutoff() -> None:
    page = parse_dblp_page(_fixture("synthetic/dblp_cutoff.json"), 0)
    included = page.occurrences[0]

    assert included.index_work_id == "conf/test/Included2026"
    assert included.raw_year == "2026"
    assert included.included_by_cutoff is True
    assert included.requires_ruling is False


def test_contract_5_rejects_future_year_and_routes_bad_years_to_ruling() -> None:
    page = parse_dblp_page(_fixture("synthetic/dblp_cutoff.json"), 0)
    future, missing, invalid = page.occurrences[1:]

    assert page.actual_count == 4
    assert (future.raw_year, future.included_by_cutoff, future.requires_ruling) == (
        "2027",
        False,
        False,
    )
    assert (missing.raw_year, missing.included_by_cutoff, missing.requires_ruling) == (
        None,
        None,
        True,
    )
    assert (invalid.raw_year, invalid.included_by_cutoff, invalid.requires_ruling) == (
        "20X6",
        None,
        True,
    )
    assert page.parse_errors == ()


def test_contract_6_accepts_raw_query_text_and_structured_ast() -> None:
    page = parse_openalex_page(
        _fixture("synthetic/openalex_cursor_page_1.json"), 0
    )

    assert page.interpreted_query_text == "title_and_abstract.search:(backoff)"
    assert isinstance(page.interpreted_query_ast, JsonObject)
    assert _member_values(page.interpreted_query_ast, "join") == ("and",)
    filters = _member_values(page.interpreted_query_ast, "filters")
    assert len(filters) == 1
    assert isinstance(filters[0], tuple)
    assert page.parse_errors == ()


def test_contract_6_rejects_lossy_ast_object_decoding() -> None:
    page = parse_openalex_page(
        _fixture("synthetic/openalex_ast_duplicate_unknown.json"), 0
    )

    assert page.interpreted_query_text == "registered raw query text"
    assert isinstance(page.interpreted_query_ast, JsonObject)
    assert _member_values(page.interpreted_query_ast, "join") == ("and", "or")
    future_nodes = _member_values(page.interpreted_query_ast, "future_node")
    assert len(future_nodes) == 1
    assert isinstance(future_nodes[0], JsonObject)
    assert _member_values(future_nodes[0], "typed_value") == (7,)
    assert page.parse_errors == ()


def test_contract_6_rejects_missing_ast_with_literal_error_code() -> None:
    body = (
        b'{"meta":{"count":0,"per_page":200,"next_cursor":null,'
        b'"x_query":{"oql":"raw"}},"results":[]}'
    )
    page = parse_openalex_page(body, 0)

    assert page.interpreted_query_ast is None
    assert page.parse_errors == ("missing_interpreted_query_ast",)


def test_contract_7_accepts_only_the_registered_literal_error_vocabulary() -> None:
    assert PARSE_ERROR_CODES == (
        "invalid_body_type",
        "invalid_page_number",
        "invalid_xml",
        "invalid_json",
        "json_root_not_object",
        "missing_declared_total",
        "invalid_declared_total",
        "missing_capacity_echo",
        "invalid_capacity_echo",
        "missing_position",
        "invalid_position",
        "missing_interpreted_query_text",
        "invalid_interpreted_query_text",
        "missing_index_work_id",
        "invalid_index_work_id",
        "missing_meta",
        "invalid_meta",
        "missing_results",
        "invalid_results",
        "invalid_result",
        "missing_x_query",
        "invalid_x_query",
        "missing_interpreted_query_ast",
        "invalid_interpreted_query_ast",
        "invalid_next_cursor",
        "missing_result_object",
        "invalid_result_object",
        "missing_hits_object",
        "invalid_hits_object",
        "invalid_hit_collection",
        "invalid_hit",
        "missing_info_object",
        "invalid_info_object",
    )


def test_contract_7_rejects_malformed_bodies_without_raising() -> None:
    arxiv = parse_arxiv_page(_fixture("synthetic/arxiv_invalid.xml"), 0)
    openalex = parse_openalex_page(_fixture("synthetic/openalex_invalid.json"), 0)
    dblp = parse_dblp_page(_fixture("real/2026-09-07_dblp_api_doi.body"), 0)

    assert arxiv.parse_errors == ("invalid_xml",)
    assert openalex.parse_errors == ("invalid_json",)
    assert dblp.parse_errors == ("invalid_json",)
    assert (arxiv.actual_count, openalex.actual_count, dblp.actual_count) == (0, 0, 0)


def test_contract_7_rejects_invalid_page_number_without_raising() -> None:
    page = parse_arxiv_page(_fixture("synthetic/arxiv_final.xml"), -1)

    assert page.page_number is None
    assert page.parse_errors == ("invalid_page_number",)


def test_missing_total_is_a_literal_parse_error_and_records_occurrence() -> None:
    page = parse_arxiv_page(_fixture("synthetic/arxiv_missing_total.xml"), 0)

    assert page.declared_total is None
    assert page.actual_count == 1
    assert page.occurrences[0].index_work_id == "https://arxiv.org/abs/0006.00001v1"
    assert page.parse_errors == ("missing_declared_total",)


def test_saved_real_arxiv_hit_and_miss_shapes() -> None:
    hit = parse_arxiv_page(_fixture("real/2026-09-07_ax_known.body"), 0)
    miss = parse_arxiv_page(_fixture("real/2026-09-07_ax_missing.body"), 0)

    assert (hit.declared_total, hit.capacity_echo, hit.actual_count) == (1, 1, 1)
    assert hit.occurrences[0].index_work_id == "http://arxiv.org/abs/1706.03762v7"
    assert (miss.declared_total, miss.capacity_echo, miss.actual_count) == (0, 1, 0)
    assert hit.parse_errors == ()
    assert miss.parse_errors == ()


def test_saved_real_openalex_lookup_and_404_are_not_search_pages() -> None:
    lookup = parse_openalex_page(_fixture("real/2026-09-07_oa_ccbench.body"), 0)
    missing = parse_openalex_page(_fixture("real/2026-09-07_oa_missing.body"), 0)

    assert lookup.actual_count == 0
    assert lookup.parse_errors == (
        "missing_meta",
        "missing_results",
        "missing_declared_total",
        "missing_capacity_echo",
        "missing_x_query",
        "missing_interpreted_query_text",
        "missing_interpreted_query_ast",
    )
    assert missing.parse_errors == ("invalid_json",)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
