from __future__ import annotations

import inspect
import json
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from orchestrator.axis1_search.catalog import (
    REGISTERED_CUTOFF,
    REGISTRATION_EPOCH,
    build_request,
    derive_expected_logical_ids,
    derive_fixed_shards,
    load_catalog,
    render_catalog_json,
)
from orchestrator.axis1_search.parsers import (
    parse_arxiv_page,
    parse_dblp_page,
    parse_openalex_page,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures") / "axis1_search"
CATALOG_PATH = (
    ROOT
    / "docs"
    / "related-work"
    / "claim-survey"
    / "2026-08-29-axis1-search-catalog.json"
)
CATALOG_SCHEMA = ROOT / "orchestrator" / "schemas" / "axis1_search_catalog.schema.json"
PAGE_SCHEMA = ROOT / "orchestrator" / "schemas" / "axis1_search_page_evidence.schema.json"


def _closed_dates(shards):
    return [
        (
            date.min if shard.shard_lower is None else date.fromisoformat(shard.shard_lower),
            date.fromisoformat(shard.shard_upper),
        )
        for shard in shards
    ]


def test_fixed_shards_cover_date_domain_exactly_once() -> None:
    arxiv = derive_fixed_shards("arxiv", "Q6", REGISTERED_CUTOFF)
    assert len(arxiv) == 168
    assert arxiv[0].shard_id == "SY1991"
    assert arxiv[23].shard_id == "SY2014"
    assert arxiv[24].shard_id == "SM201501"
    assert arxiv[-1].shard_id == "SM202612"
    ranges = _closed_dates(arxiv)
    assert ranges[0][0] == date(1991, 1, 1)
    assert ranges[-1][1] == date(2026, 12, 31)
    assert all(left_upper + timedelta(days=1) == right_lower for (_, left_upper), (right_lower, _) in zip(ranges, ranges[1:]))

    for branch in ("Q3", "Q6"):
        openalex = derive_fixed_shards("openalex", branch, REGISTERED_CUTOFF)
        assert len(openalex) == 37
        assert asdict(openalex[0]) == {
            "shard_id": "SPRE1991",
            "shard_lower": None,
            "shard_upper": "1990-12-31",
        }
        assert openalex[1].shard_lower == "1991-01-01"
        assert openalex[-1].shard_upper == REGISTERED_CUTOFF
        assert all(
            date.fromisoformat(left.shard_upper) + timedelta(days=1)
            == date.fromisoformat(right.shard_lower)
            for left, right in zip(openalex[1:], openalex[2:])
        )


def test_fixed_shards_are_pairwise_disjoint() -> None:
    for index, branch in (("arxiv", "Q6"), ("openalex", "Q3"), ("openalex", "Q6")):
        ranges = _closed_dates(derive_fixed_shards(index, branch, REGISTERED_CUTOFF))
        for ordinal, (left_lower, left_upper) in enumerate(ranges):
            for right_lower, right_upper in ranges[ordinal + 1 :]:
                assert left_upper < right_lower or right_upper < left_lower


def test_shard_derivation_takes_only_cutoff() -> None:
    signature = inspect.signature(derive_fixed_shards)
    assert tuple(signature.parameters) == ("index", "branch", "cutoff")
    assert all(
        parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for parameter in signature.parameters.values()
    )
    assert derive_fixed_shards("arxiv", "Q1", REGISTERED_CUTOFF) == ()
    with pytest.raises(TypeError):
        derive_fixed_shards("arxiv", "Q6", REGISTERED_CUTOFF, 30_753)  # type: ignore[call-arg]


def test_catalog_matches_independently_derived_logical_ids() -> None:
    catalog = load_catalog(str(CATALOG_PATH))
    actual = tuple(sorted(query.query_id for query in catalog.logical_queries))
    expected = derive_expected_logical_ids(REGISTERED_CUTOFF)
    assert actual == expected
    assert len(actual) == 267
    assert catalog.expected_cardinalities["executable_leaves"] == 263
    assert CATALOG_PATH.read_bytes() == render_catalog_json()


def test_catalog_and_evidence_schemas_are_valid_draft_07() -> None:
    catalog_schema = json.loads(CATALOG_SCHEMA.read_text(encoding="utf-8"))
    page_schema = json.loads(PAGE_SCHEMA.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(catalog_schema)
    Draft7Validator.check_schema(page_schema)
    Draft7Validator(catalog_schema).validate(
        json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    )


def test_condition2_rejects_silent_truncation() -> None:
    parsed = parse_dblp_page((FIXTURES / "f5_dblp_silent_truncation.json").read_bytes())
    requested_page_size = 1000
    is_nonterminal = parsed.position_out is not None
    reason_code = (
        "silent_truncation"
        if is_nonterminal and parsed.actual_count < requested_page_size
        else None
    )
    assert parsed.declared_total == 500
    assert parsed.capacity_echo == 100
    assert parsed.actual_count == 100
    assert parsed.position_out == "100"
    assert reason_code == "silent_truncation"


def test_dblp_expected_echo_splits_on_hyphen() -> None:
    catalog = load_catalog(str(CATALOG_PATH))
    request = build_request(
        catalog,
        f"{REGISTRATION_EPOCH}-T05@dblp",
        page_number=0,
        position_in=None,
    )
    assert request.expected_interpreted_query == "two* phase* locking*"
    assert request.query_parameters == (
        ("q", "two-phase locking"),
        ("format", "json"),
        ("h", "100"),
        ("f", "0"),
    )


def test_parser_preserves_occurrence_dates_and_missing_reason() -> None:
    arxiv = parse_arxiv_page((FIXTURES / "f1_arxiv_terminal.xml").read_bytes())
    assert arxiv.actual_count == 105
    assert arxiv.capacity_echo == 200
    assert arxiv.occurrences[0].raw_date_value == "2026-08-01T00:00:00Z"
    assert arxiv.occurrences[0].interpreted_date == "2026-08-01"
    assert arxiv.occurrences[0].date_missing_reason is None
    assert arxiv.occurrences[0].family_keys == ("arxiv:2608.00001",)

    dblp = parse_dblp_page((FIXTURES / "f7_dblp_missing_year.json").read_bytes())
    assert dblp.actual_count == 1
    assert dblp.occurrences[0].raw_date_value is None
    assert dblp.occurrences[0].interpreted_date is None
    assert dblp.occurrences[0].date_missing_reason == "missing_dblp_year"


def test_parser_does_not_dedup_by_family_key() -> None:
    parsed = parse_openalex_page((FIXTURES / "f4_openalex_shared_doi.json").read_bytes())
    assert parsed.actual_count == 2
    assert len(parsed.occurrences) == 2
    assert {item.index_work_id for item in parsed.occurrences} == {
        "https://openalex.org/W400001",
        "https://openalex.org/W400002",
    }
    assert parsed.occurrences[0].family_keys == ("doi:10.9999/shared",)
    assert parsed.occurrences[1].family_keys == ("doi:10.9999/shared",)


def test_parser_preserves_repeated_index_work_id_across_pages() -> None:
    first = parse_openalex_page((FIXTURES / "f3_openalex_adjacent_page_0.json").read_bytes())
    second = parse_openalex_page((FIXTURES / "f3_openalex_adjacent_page_1.json").read_bytes())
    occurrences = first.occurrences + second.occurrences
    assert len(occurrences) == 2
    assert len({item.index_work_id for item in occurrences}) == 1
    assert first.position_out == "page-1-cursor"
    assert second.position_out is None


def test_openalex_id_is_index_work_id_not_doi() -> None:
    parsed = parse_openalex_page((FIXTURES / "f4_openalex_shared_doi.json").read_bytes())
    assert parsed.occurrences[0].index_work_id == "https://openalex.org/W400001"
    assert parsed.occurrences[0].index_work_id != "https://doi.org/10.9999/shared"


def test_actual_count_is_body_element_count_not_capacity_echo() -> None:
    arxiv = parse_arxiv_page((FIXTURES / "f1_arxiv_terminal.xml").read_bytes())
    openalex = parse_openalex_page((FIXTURES / "f2_openalex_terminal.json").read_bytes())
    dblp = parse_dblp_page((FIXTURES / "f6_dblp_terminal.json").read_bytes())
    assert (arxiv.actual_count, arxiv.capacity_echo) == (105, 200)
    assert (openalex.actual_count, openalex.capacity_echo) == (124, 200)
    assert (dblp.actual_count, dblp.capacity_echo) == (36, 36)
    assert arxiv.position_out is None
    assert openalex.position_out is None
    assert dblp.position_out is None


def test_missing_index_work_id_has_exact_parse_error() -> None:
    payload = {
        "meta": {
            "count": 1,
            "per_page": 200,
            "next_cursor": None,
            "page": None,
            "x_query": {"oql": "fixture", "url": "/works?cursor=%2A"},
        },
        "results": [{"id": None, "doi": None, "publication_date": "2026-01-01"}],
    }
    parsed = parse_openalex_page(json.dumps(payload).encode("utf-8"))
    assert parsed.actual_count == 1
    assert len(parsed.occurrences) == 1
    assert parsed.occurrences[0].index_work_id == ""
    assert parsed.parse_errors == ("missing_index_work_id:results[0].id",)


def test_build_request_uses_only_registered_https_hosts_and_ordered_parameters() -> None:
    catalog = load_catalog(str(CATALOG_PATH))
    cases = (
        (f"{REGISTRATION_EPOCH}-Q1@arxiv", "export.arxiv.org", ("search_query", "start", "max_results")),
        (f"{REGISTRATION_EPOCH}-Q1@openalex", "api.openalex.org", ("filter", "per-page", "cursor")),
        (f"{REGISTRATION_EPOCH}-T01@dblp", "dblp.org", ("q", "format", "h", "f")),
    )
    for query_id, host, parameter_names in cases:
        request = build_request(catalog, query_id, 0, None)
        assert request.scheme == "https"
        assert request.host == host
        assert request.encoded_url.startswith(f"https://{host}/")
        assert tuple(name for name, _ in request.query_parameters) == parameter_names


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
