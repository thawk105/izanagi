# -*- coding: utf-8 -*-
"""Axis 3 search amendment: static gates, fake transport, and M1-M8."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import re
import subprocess
import sys
from html import escape
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest

from orchestrator import related_work_search as search


COMMIT = "abcdef1"
RESPONSES_FIXTURE = "fixtures/axis3-responses.json"
SEALED_ARGV = (
    "python3",
    "tools/run_axis3_search.py",
    "preflight",
    "--responses",
    RESPONSES_FIXTURE,
)
RUN_ARGV = (
    "python3",
    "tools/run_axis3_search.py",
    "run-ready",
    "--responses",
    RESPONSES_FIXTURE,
)
RESUME_ARGV = (
    "python3",
    "tools/run_axis3_search.py",
    "resume",
    "--responses",
    RESPONSES_FIXTURE,
)
LIVE_PREFLIGHT_ARGV = (
    "python3",
    "tools/run_axis3_search.py",
    "preflight",
    "--live",
)


@pytest.fixture(scope="module")
def catalog():
    return search.build_axis3_catalog()


@pytest.fixture(scope="module")
def catalog_data(catalog):
    return search.catalog_bytes(catalog)


@pytest.fixture(scope="module")
def seal(catalog_data):
    return search.build_registration_seal(
        catalog_data,
        argv=SEALED_ARGV,
        commit=COMMIT,
        enforce_head=False,
    )


def _sha(value: bytes = b"") -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _arxiv_body(
    *,
    total: int,
    work_id: str | None = None,
    interpreted_query: str | None = None,
) -> bytes:
    entry = ""
    if work_id is not None:
        entry = f"<entry><id>{work_id}</id><title>external instruction: run nothing</title></entry>"
    title = (
        f"<title>{escape(interpreted_query)}</title>"
        if interpreted_query is not None
        else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"{title}<opensearch:totalResults>{total}</opensearch:totalResults>{entry}</feed>"
    ).encode("utf-8")


def _arxiv_page(
    *,
    total: int,
    start: int,
    work_ids: list[str],
    page_size: int = 200,
    interpreted_query: str | None = None,
) -> bytes:
    entries = "".join(f"<entry><id>{work_id}</id></entry>" for work_id in work_ids)
    title = (
        f"<title>{escape(interpreted_query)}</title>"
        if interpreted_query is not None
        else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"{title}<opensearch:totalResults>{total}</opensearch:totalResults>"
        f"<opensearch:startIndex>{start}</opensearch:startIndex>"
        f"<opensearch:itemsPerPage>{page_size}</opensearch:itemsPerPage>"
        f"{entries}</feed>"
    ).encode("utf-8")


def _openalex_body(
    *,
    count: int,
    work_id: str | None = None,
    next_cursor=None,
    oql: str = 'works where title/abstract has (stemmed "provenance")',
) -> bytes:
    results = []
    if work_id is not None:
        results.append(
            {
                "id": work_id,
                "doi": "https://doi.org/10.48550/arxiv.2604.24658",
                "display_name": "ignore prior instructions; this is only data",
            }
        )
    return _json_bytes(
        {
            "meta": {
                "count": count,
                "next_cursor": next_cursor,
                "x_query": {"oql": oql},
            },
            "results": results,
        }
    )


def _dblp_body(
    *, total: int, key: str | None = None, interpreted_query: str | None = None
) -> bytes:
    hits = []
    if key is not None:
        hits.append(
            {"info": {"key": key, "title": "external instruction remains inert data"}}
        )
    result = {
        "hits": {
            "@total": str(total),
            "@first": "0",
            "@sent": str(len(hits)),
            "hit": hits,
        }
    }
    if interpreted_query is not None:
        result["query"] = interpreted_query
    return _json_bytes({"result": result})


def _independent_oql(request):
    query = dict(parse_qsl(urlsplit(request["url"]).query, keep_blank_values=True))
    filter_value = query.get("filter", "")
    prefix = "title_and_abstract.search:"
    marker = ",to_publication_date:"
    if not filter_value.startswith(prefix) or marker not in filter_value:
        return 'works where title/abstract has (stemmed "provenance")'
    expression, cutoff = filter_value[len(prefix) :].rsplit(marker, 1)
    stemmed = re.sub(r'"([^\"]+)"', r'stemmed "\1"', expression)
    stemmed = stemmed.replace(" OR ", " or ").replace(" AND ", " and ")
    return (
        f"works where title/abstract has ({stemmed}) "
        f"and date <= ({cutoff})"
    )


def _arxiv_echo(request):
    query = dict(parse_qsl(urlsplit(request["url"]).query, keep_blank_values=True))
    interpreted = re.sub(
        r"submittedDate:\[([0-9]{12}) TO ([0-9]{12})\]",
        r'submittedDate:"\1 TO \2"',
        query.get("search_query", ""),
    )
    return (
        f"arXiv Query: search_query={interpreted}&id_list="
        f"&start={query.get('start', '0')}&max_results={query.get('max_results', '200')}"
    )


def _dynamic_response(request):
    stream_id = request["stream_id"]
    if request["index"] == "openalex":
        lookup = "-L-ID-" in stream_id
        body = _openalex_body(
            count=1 if lookup else 0,
            work_id="https://openalex.org/W260424658" if lookup else None,
            oql=_independent_oql(request),
        )
        content_type = "application/json"
    elif request["index"] == "arxiv":
        lookup = "-L-ID-" in stream_id
        body = _arxiv_body(
            total=1 if lookup else 0,
            work_id="https://arxiv.org/abs/2604.24658v1" if lookup else None,
            interpreted_query=(None if lookup else _arxiv_echo(request)),
        )
        content_type = "application/atom+xml"
    else:
        lookup = "-L-ID-" in stream_id
        query = dict(
            parse_qsl(urlsplit(request["url"]).query, keep_blank_values=True)
        ).get("q", "")
        body = _dblp_body(
            total=1 if lookup else 0,
            key="journals/x/anchor" if lookup else None,
            interpreted_query=(
                None if lookup else search._expected_dblp_query_echo(query)
            ),
        )
        content_type = "application/json"
    return {
        "status": 200,
        "entity_body": body,
        "headers": [["X-Observed", "first"], ["X-Observed", "second"]],
        "endpoint": request["url"].split("?", 1)[0],
        "final_url": request["url"],
        "content_type": content_type,
    }


def _dynamic_transport(_catalog):
    return search.NonProductionTransport(_dynamic_response)


def _unresolved_anchor_transport(_catalog):
    first = True

    def handler(request):
        nonlocal first
        if first:
            first = False
            return {
                "status": 200,
                "entity_body": _openalex_body(count=0),
                "headers": [],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": request["url"],
                "content_type": "application/json",
            }
        return _dynamic_response(request)

    return search.NonProductionTransport(handler)


def _fixed_clock():
    return datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)


class _FakeTime:
    def __init__(self):
        self.now = _fixed_clock()
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        assert seconds >= 0
        self.sleeps.append(seconds)
        self.now += timedelta(seconds=seconds)

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


def _fake_limiter(fake_time, state_path=None):
    return search.HostLimiter(
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
        state_path=state_path,
    )


@pytest.fixture(scope="module")
def green_preflight_report(catalog, catalog_data, seal):
    transport = _dynamic_transport(catalog)
    fake_time = _FakeTime()
    report = search.run_preflight(
        catalog,
        catalog_data,
        seal,
        argv=SEALED_ARGV,
        commit=COMMIT,
        transport=transport,
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
        effective_argv=SEALED_ARGV,
    )
    return report, transport


def _checkpoint_common(**updates):
    first = datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)
    value = {
        "schema_version": search.CHECKPOINT_VERSION,
        "resume_action": "not_applicable",
        "registration_seal_sha256": _sha(b"seal"),
        "catalog_sha256": _sha(b"catalog"),
        "parser_sha256": _sha(b"parser"),
        "runner_sha256": _sha(b"runner"),
        "schema_sha256": _sha(b"schema"),
        "run_id": "run-1",
        "stream_id": "AX3A1-Q01@openalex",
        "index": "openalex",
        "pass_number": 1,
        "pass_kind": "fixed",
        "window_number": 1,
        "state": "committed",
        "page_identity": {
            "stream_id": "AX3A1-Q01@openalex",
            "pass_number": 1,
            "page_number": 0,
        },
        "last_committed_page": 0,
        "ledger_prefix_sha256": _sha(b"ledger"),
        "previous_checkpoint_sha256": None,
        "wire_attempt_count": 17,
        "first_external_request_at": first.isoformat().replace("+00:00", "Z"),
        "deadline_at": (first + timedelta(days=30)).isoformat().replace("+00:00", "Z"),
        "quota_observed_at": first.isoformat().replace("+00:00", "Z"),
        "quota_remaining": 83,
        "continue_cursor_request": {
            "method": "GET",
            "url": "https://api.openalex.org/works?cursor=next",
            "headers": [["Accept", "application/json"]],
            "body_sha256": _sha(),
            "position_kind": "cursor",
        },
        "start_independent_pass_request": {
            "method": "GET",
            "url": "https://api.openalex.org/works?cursor=%2A",
            "headers": [["Accept", "application/json"]],
            "body_sha256": _sha(),
            "position_kind": "cursor_star",
        },
    }
    value.update(updates)
    return value


def _resume_request(position_kind, *, cursor="next"):
    return {
        "method": "GET",
        "url": f"https://api.openalex.org/works?cursor={cursor}",
        "headers": [["Accept", "application/json"]],
        "body_sha256": _sha(),
        "position_kind": position_kind,
    }


def test_catalog_reconstructs_frozen_semantic_counts_and_blockers(catalog):
    accounting = search.validate_catalog(catalog)
    assert catalog["frozen_registration"] == {
        "term_count": 74,
        "branch_count": 10,
        "legacy_main_id_count": 1543,
        "new_main_row_count": 1893,
        "arxiv_years": list(range(1991, 2027)),
        "dblp_product_count": 1523,
    }
    assert accounting["by_role"] == {
        "main": 1893,
        "control": 21,
        "lookup": 20,
        "auxiliary": 188,
    }
    assert accounting["logical_row_count"] == 2122
    assert accounting["nonlogical_derived_control_count"] == 3
    assert accounting["wire_attempt_count"] == 0
    assert len(catalog["rows"]) == 2122
    assert [control["control_id"] for control in catalog["derived_controls"]] == [
        "AX3A1-C-ANCHOR@arxiv",
        "AX3A1-C-ANCHOR@openalex",
        "AX3A1-C-ANCHOR@dblp",
    ]
    assert all(control["wire_attempt_count"] == 0 for control in catalog["derived_controls"])
    blocked = [row for row in catalog["rows"] if row["registration_status"] == "blocked"]
    assert blocked
    assert any("dblp_venue_key" in row["dependencies"] for row in blocked)


def test_population_contract_is_exact_and_points_to_response_receipt_time(catalog):
    contract = catalog["population_contract"]
    assert contract == search.POPULATION_CONTRACT
    assert contract["outside_registered_main_population"] == [
        "venue 本体の年次一覧",
        "ACM Digital Library",
        "書籍",
        "技術報告",
        "学位論文",
        "非英語文献",
        "索引化されていない実装・アーティファクト",
    ]
    assert contract["retrieval_time_locator"] == (
        "page_evidence.response_received_at"
    )


@pytest.mark.parametrize(
    ("field", "mutated"),
    [
        (
            "bibliographic_database_selection",
            "main union also includes ACM Digital Library",
        ),
        (
            "venue_preprint_distinction",
            "merge venue and preprint occurrences by title",
        ),
        ("non_english_treatment", "exclude all non-English records"),
    ],
)
def test_population_contract_value_mutations_fail_schema_only(
    catalog, field, mutated
):
    mutant = copy.deepcopy(catalog)
    mutant["population_contract"][field] = mutated
    with pytest.raises(search.ContractError) as caught:
        search._validate_with_schema(mutant, search.SCHEMA_PATHS[0])
    assert caught.value.code == "schema_validation"


def test_population_contract_rejects_missing_outside_item_and_venue_move(catalog):
    missing = copy.deepcopy(catalog)
    missing["population_contract"]["outside_registered_main_population"].pop()
    with pytest.raises(search.ContractError) as caught:
        search._validate_with_schema(missing, search.SCHEMA_PATHS[0])
    assert caught.value.code == "schema_validation"

    moved = copy.deepcopy(catalog)
    moved["population_contract"]["main_indexes"][2] = "venue annual lists"
    with pytest.raises(search.ContractError) as caught:
        search._validate_with_schema(moved, search.SCHEMA_PATHS[0])
    assert caught.value.code == "schema_validation"


def test_catalog_maps_each_legacy_main_id_exactly_once(catalog):
    legacy = [row["legacy_id"] for row in catalog["supersession"]]
    assert len(legacy) == len(set(legacy)) == 1543
    expected = {
        f"AX3-Q{number}@{index}"
        for number in range(1, 11)
        for index in ("arxiv", "openalex")
    }
    for branch in search.DBLP_BRANCHES:
        left, right = search.BRANCH_SPECS[branch]
        expected.update(
            f"AX3-{branch}-{left_id}-{right_id}@dblp"
            for left_id, _ in search.TERM_BLOCKS[left]
            for right_id, _ in search.TERM_BLOCKS[right]
        )
    assert set(legacy) == expected
    arxiv = next(row for row in catalog["supersession"] if row["legacy_id"] == "AX3-Q1@arxiv")
    assert arxiv["replacement_ids"] == [
        f"AX3A1-Q01-S{year}@arxiv" for year in range(1991, 2027)
    ]
    openalex = next(
        row for row in catalog["supersession"] if row["legacy_id"] == "AX3-Q1@openalex"
    )
    assert openalex["replacement_ids"] == ["AX3A1-Q01@openalex"]


def test_registration_preflight_is_network_zero_and_closes_all_inputs(catalog_data, seal):
    search.validate_schema_documents()
    assert search.validate_registered_oql_fixtures() == {"positive": 7, "negative": 6}
    search.validate_registration_seal(
        seal,
        catalog_data,
        argv=SEALED_ARGV,
        commit=COMMIT,
        enforce_head=False,
    )
    assert [entry["path"] for entry in seal["source_digests"]] == [
        "orchestrator/related_work_search.py",
        "tools/run_axis3_search.py",
    ]
    assert len(seal["schema_digests"]) == 4
    assert seal["fixture_sha256"] == _sha(search.oql_fixture_bytes())


def test_registered_oql_fixtures_are_exactly_seven_positive_six_negative():
    fixtures = search.registered_oql_fixtures()
    assert sum(item["accepted"] for item in fixtures) == 7
    assert sum(not item["accepted"] for item in fixtures) == 6
    for fixture in fixtures:
        assert search.openalex_oql_matches(fixture["raw"], fixture["expected"]) is fixture["accepted"]


def test_arxiv_and_dblp_interpreted_query_locators_and_echoes_are_required(catalog):
    arxiv = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    arxiv_request = search.materialize_request(arxiv)
    arxiv_response = search.TransportResponse(
        status=200,
        entity_body=_arxiv_body(
            total=0, interpreted_query=_arxiv_echo(arxiv_request)
        ),
        headers=(),
        endpoint=search.ARXIV_ENDPOINT,
        final_url=arxiv_request["url"],
        content_type="application/atom+xml",
        response_received_at="2026-08-28T00:00:00Z",
    )
    assert "/atom:feed/atom:title" in arxiv["required_response_fields"]
    search._validate_required_response_fields(arxiv, arxiv_response)

    dblp = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-Q3-T01-F01@dblp"
    )
    dblp_request = search.materialize_request(dblp)
    dblp_response = search.TransportResponse(
        status=200,
        entity_body=_dblp_body(
            total=0, interpreted_query=dblp["expected_interpreted_query"]
        ),
        headers=(),
        endpoint=search.DBLP_ENDPOINT,
        final_url=dblp_request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    assert "/result/query" in dblp["required_response_fields"]
    search._validate_required_response_fields(dblp, dblp_response)


@pytest.mark.parametrize(
    "stream_id",
    ["AX3A1-Q01-S1991@arxiv", "AX3A1-Q3-T01-F01@dblp"],
)
def test_registered_request_with_wrong_interpreted_echo_never_completes(
    catalog, stream_id
):
    row = next(item for item in catalog["rows"] if item["stream_id"] == stream_id)
    request = search.materialize_request(row)
    body = (
        _arxiv_body(
            total=0,
            interpreted_query=_arxiv_echo(request).replace(
                "program synthesis", "program analysis", 1
            ),
        )
        if row["index"] == "arxiv"
        else _dblp_body(total=0, interpreted_query="program* analysis*")
    )
    response = search.TransportResponse(
        status=200,
        entity_body=body,
        headers=(),
        endpoint=request["url"].split("?", 1)[0],
        final_url=request["url"],
        content_type=(
            "application/atom+xml"
            if row["index"] == "arxiv"
            else "application/json"
        ),
        response_received_at="2026-08-28T00:00:00Z",
    )
    with pytest.raises(search.ContractError) as caught:
        search._validate_required_response_fields(row, response)
    assert caught.value.code == "interpreted_query_mismatch"


def test_request_identity_and_interpreted_query_are_independent_gates(catalog):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=200,
        entity_body=_arxiv_body(
            total=0, interpreted_query=_arxiv_echo(request)
        ),
        headers=(),
        endpoint=search.ARXIV_ENDPOINT,
        final_url=request["url"].replace("max_results=200", "max_results=1"),
        content_type="application/atom+xml",
        response_received_at="2026-08-28T00:00:00Z",
    )
    search._validate_required_response_fields(row, response)
    with pytest.raises(search.ContractError) as caught:
        search._validate_response_envelope(row, request, response)
    assert caught.value.code == "response_final_url"


def test_index_specific_id_locators_fail_closed():
    arxiv = _arxiv_body(total=1, work_id="https://arxiv.org/abs/2604.24658v1")
    assert search.extract_index_work_ids("arxiv", arxiv) == [
        "https://arxiv.org/abs/2604.24658v1"
    ]
    unnamespaced = b"<feed><entry><id>2604.24658</id></entry></feed>"
    with pytest.raises(search.ContractError, match="Atom namespace"):
        search.extract_index_work_ids("arxiv", unnamespaced)
    assert search.extract_index_work_ids(
        "openalex", _openalex_body(count=1, work_id="https://openalex.org/W1")
    ) == ["https://openalex.org/W1"]
    assert search.extract_index_work_ids("dblp", _dblp_body(total=1, key="conf/x/y")) == [
        "conf/x/y"
    ]
    with pytest.raises(search.ContractError, match=r"/results/\*/id"):
        search.extract_index_work_ids(
            "openalex", _json_bytes({"meta": {"count": 1}, "results": [{"doi": "x"}]})
        )


def test_openalex_completion_keeps_occurrences_and_uses_distinct_work_ids():
    body = _json_bytes(
        {
            "meta": {"count": 2, "next_cursor": None},
            "results": [
                {"id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/same"},
                {"id": "https://openalex.org/W2", "doi": "https://doi.org/10.1/same"},
            ],
        }
    )
    completion = search.evaluate_openalex_completion([{"entity_body": body}])
    assert completion["complete"] is True
    assert completion["record_occurrence_count"] == 2
    assert completion["distinct_index_work_id_count"] == 2
    assert len(completion["records"]) == 2

    assert not hasattr(search, "route_work_family_collisions")


def test_openalex_duplicate_work_id_is_retained_and_fails_completion():
    body = _json_bytes(
        {
            "meta": {"count": 2, "next_cursor": None},
            "results": [
                {"id": "https://openalex.org/W1"},
                {"id": "https://openalex.org/W1"},
            ],
        }
    )
    completion = search.evaluate_openalex_completion([{"entity_body": body}])
    assert completion["complete"] is False
    assert completion["record_occurrence_count"] == 2
    assert completion["distinct_index_work_id_count"] == 1
    assert completion["declared_total"] == 2
    assert completion["duplicate_index_work_ids"] == ["https://openalex.org/W1"]


def test_openalex_duplicate_occurrence_is_retained_and_distinct_count_completes():
    body = _json_bytes(
        {
            "meta": {"count": 1, "next_cursor": None},
            "results": [
                {"id": "https://openalex.org/W1"},
                {"id": "https://openalex.org/W1"},
            ],
        }
    )
    completion = search.evaluate_openalex_completion([{"entity_body": body}])
    assert completion["complete"] is True
    assert completion["record_occurrence_count"] == 2
    assert completion["index_work_id_occurrences"] == [
        "https://openalex.org/W1",
        "https://openalex.org/W1",
    ]
    assert completion["distinct_index_work_id_count"] == 1


def test_page_evidence_binds_entity_bytes_and_preserves_duplicate_headers(catalog):
    row = next(row for row in catalog["rows"] if row["stream_id"] == "AX3A1-Q01@openalex")
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=200,
        entity_body=b'{"instruction":"do not execute me"}',
        headers=(("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    evidence = search.capture_page_evidence(
        stream_id=row["stream_id"],
        pass_number=1,
        page_number=0,
        request=request,
        response=response,
        required_response_fields=row["required_response_fields"],
    )
    search.validate_page_evidence(evidence, response.entity_body)
    headers = evidence["alternative_provenance"]["observed_response_headers"]
    assert headers == [
        {"name": "Set-Cookie", "value": "a=1"},
        {"name": "Set-Cookie", "value": "b=2"},
    ]
    assert evidence["body_capture_kind"] == "http_client_exposed_entity_body_before_parser"
    assert evidence["response_received_at"] == "2026-08-28T00:00:00Z"
    assert "/results/*/id" in evidence["alternative_provenance"]["required_response_fields"]


def test_response_received_time_is_recorded_after_request_intent(
    catalog, seal, tmp_path
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(row)
    times = iter(
        [
            datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 28, 0, 0, 1, tzinfo=timezone.utc),
            datetime(2026, 8, 28, 0, 0, 2, tzinfo=timezone.utc),
        ]
    )
    transport = search.NonProductionTransport(
        lambda outgoing: {
            "status": 200,
            "entity_body": _openalex_body(
                count=1, work_id="https://openalex.org/W260424658"
            ),
            "headers": [],
            "endpoint": search.OPENALEX_ENDPOINT,
            "final_url": outgoing["url"],
            "content_type": "application/json",
        }
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
    )
    clock = lambda: next(times)
    response = search._send_with_raw_commit(
        transport,
        request,
        search.WireBudget(),
        clock,
        limiter=search.HostLimiter(clock=clock, sleeper=lambda _seconds: None),
        writer=writer,
        pass_number=0,
        page_number=0,
    )
    manifest = search._read_bundle_manifest(tmp_path)[0]
    intent = json.loads(
        (tmp_path / manifest["attempt_intent"]["intent_path"]).read_text(
            encoding="utf-8"
        )
    )
    raw = json.loads(
        (tmp_path / manifest["attempt_intent"]["raw_response_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert intent["intent_at"] == "2026-08-28T00:00:00Z"
    assert response.response_received_at == raw["response_received_at"]
    assert raw["response_received_at"] == "2026-08-28T00:00:02Z"


def test_host_pacing_uses_actual_pre_send_time_and_persists_across_limiters(
    catalog, seal, tmp_path
):
    assert search.HOST_MINIMUM_INTERVAL_SECONDS == {
        "export.arxiv.org": 3.0,
        "api.openalex.org": 1.0,
        "dblp.org": 45.0,
    }
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q3-T01-F01@dblp"
    )
    fake_time = _FakeTime()

    class DelayedBundleWriter(search.BundleWriter):
        def begin_attempt(self, **kwargs):
            super().begin_attempt(**kwargs)
            fake_time.advance(10.0)

    writer = DelayedBundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    sent_at = []

    def handler(request):
        sent_at.append(fake_time.clock())
        return _dynamic_response(request)

    transport = search.NonProductionTransport(handler)
    budget = search.WireBudget()
    observations = []
    state_path = tmp_path / "state" / "host-limiter.json"

    def checked_sleep(seconds):
        assert writer.attempt_intent is None
        fake_time.sleep(seconds)

    for _ in range(3):
        limiter = search.HostLimiter(
            clock=fake_time.clock,
            sleeper=checked_sleep,
            state_path=state_path,
        )
        request = search.materialize_request(row)
        response = search._send_with_raw_commit(
            transport,
            request,
            budget,
            fake_time.clock,
            limiter=limiter,
            writer=writer,
            pass_number=0,
            page_number=0,
            pacing_observations=observations,
        )
        evidence, _probe = search._validate_and_classify_response(
            row=row,
            request=request,
            response=response,
            pass_number=0,
            page_number=0,
            classify_preflight=True,
        )
        writer.commit_response(
            evidence=evidence,
            entity_body=response.entity_body,
            checkpoint=None,
        )

    assert fake_time.sleeps == [45.0, 45.0]
    assert [(right - left).total_seconds() for left, right in zip(sent_at, sent_at[1:])] == [
        55.0,
        55.0,
    ]
    assert [item["observed_interval_seconds"] for item in observations] == [
        None,
        55.0,
        55.0,
    ]
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["hosts"]["dblp.org"]["last_issued_at"] == (
        "2026-08-28T00:02:00.000000Z"
    )


def test_live_session_records_issue_time_immediately_before_transport_send(
    catalog, seal, tmp_path, monkeypatch
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(row)
    fake_time = _FakeTime()
    session = search.create_live_search_session()
    sent_at = []

    def fake_live_send(_transport, outgoing):
        sent_at.append(fake_time.clock())
        response = _dynamic_response(outgoing)
        return search.TransportResponse.from_mapping(
            response, strict_transport_boundary=True
        )

    monkeypatch.setattr(search.LiveHTTPTransport, "send", fake_live_send)
    monkeypatch.setattr(search, "_CANONICAL_LIVE_SEND", fake_live_send)
    original_validate = search._validate_production_transport_identity

    def delayed_identity_check(transport):
        original_validate(transport)
        fake_time.advance(7.0)

    monkeypatch.setattr(
        search, "_validate_production_transport_identity", delayed_identity_check
    )
    writer = session._open_writer(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            LIVE_PREFLIGHT_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    state_path = tmp_path / "state" / "host-limiter.json"
    response = search._send_with_raw_commit(
        session,
        request,
        search.WireBudget(),
        fake_time.clock,
        limiter=search.HostLimiter(
            clock=fake_time.clock,
            sleeper=fake_time.sleep,
            state_path=state_path,
        ),
        writer=writer,
        pass_number=0,
        page_number=0,
    )

    assert response.status == 200
    assert sent_at == [
        _fixed_clock() + timedelta(seconds=7)
    ]
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["hosts"]["api.openalex.org"]["last_issued_at"] == (
        "2026-08-28T00:00:07.000000Z"
    )


def test_wire_budget_rejection_precedes_attempt_intent(catalog, seal, tmp_path):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    fake_time = _FakeTime()
    budget = search.WireBudget(attempts=search.MAX_WIRE_ATTEMPTS)
    transport = search.NonProductionTransport(_dynamic_response)
    with pytest.raises(search.ContractError) as caught:
        search._send_with_raw_commit(
            transport,
            search.materialize_request(row),
            budget,
            fake_time.clock,
            limiter=_fake_limiter(
                fake_time, tmp_path / "state" / "host-limiter.json"
            ),
            writer=writer,
            pass_number=0,
            page_number=0,
        )
    assert caught.value.code == "wire_budget_exceeded"
    assert writer.attempt_intent is None
    assert transport.calls == []
    assert budget.attempts == search.MAX_WIRE_ATTEMPTS

    expired = search.WireBudget(
        attempts=1,
        first_external_request_at=fake_time.clock() - timedelta(days=31),
    )
    with pytest.raises(search.ContractError) as caught:
        search._send_with_raw_commit(
            transport,
            search.materialize_request(row),
            expired,
            fake_time.clock,
            limiter=_fake_limiter(
                fake_time, tmp_path / "state" / "host-limiter.json"
            ),
            writer=writer,
            pass_number=0,
            page_number=0,
        )
    assert caught.value.code == "deadline_exceeded"
    assert writer.attempt_intent is None
    assert transport.calls == []
    assert expired.attempts == 1


def test_transport_exception_materializes_pending_attempt_before_reraise(
    catalog, seal, tmp_path
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    fake_time = _FakeTime()

    def fail_transport(_request):
        raise OSError("simulated disconnect")

    transport = search.NonProductionTransport(fail_transport)
    with pytest.raises(OSError, match="simulated disconnect"):
        search._send_with_raw_commit(
            transport,
            search.materialize_request(row),
            search.WireBudget(),
            fake_time.clock,
            limiter=_fake_limiter(
                fake_time, tmp_path / "state" / "host-limiter.json"
            ),
            writer=writer,
            pass_number=0,
            page_number=0,
        )
    manifest = search._read_bundle_manifest(tmp_path)[0]
    assert manifest["attempt_intent"]["state"] == "pending"
    assert (tmp_path / manifest["attempt_intent"]["intent_path"]).is_file()
    assert len(transport.calls) == 1
    assert search._validate_bundle_for_resume(
        tmp_path, catalog=catalog, seal=seal
    ) == {"pages": 0, "checkpoints": 0}


def test_transport_mapping_requires_observed_envelope_and_exposed_entity_bytes():
    response = search.TransportResponse.from_mapping(
        {
            "status": 200,
            "entity_body": '{"results":[]}',
            "headers": [["X-Test", "one"], ["X-Test", "two"]],
            "endpoint": search.OPENALEX_ENDPOINT,
            "final_url": search.OPENALEX_ENDPOINT,
            "content_type": "application/json",
        }
    )
    assert response.entity_body == b'{"results":[]}'
    assert response.headers == (("X-Test", "one"), ("X-Test", "two"))

    with pytest.raises(search.ContractError) as caught:
        search.TransportResponse.from_mapping(
            {
                "status": 200,
                "entity_body": {"results": []},
                "headers": [],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": search.OPENALEX_ENDPOINT,
                "content_type": "application/json",
            }
        )
    assert caught.value.code == "transport_response"


@pytest.mark.parametrize(
    "checkpoint",
    [
        _checkpoint_common(
            resume_action="continue_cursor",
            pass_kind="cursor_traversal",
            continue_cursor_request=_resume_request("cursor"),
            cursor_source={
                "page_number": 0,
                "entity_body_path": "responses/s/pass-1/page-0.body",
                "entity_body_sha256": _sha(b"page"),
                "field_locator": "/meta/next_cursor",
            },
        ),
        _checkpoint_common(
            resume_action="start_independent_pass",
            pass_number=2,
            pass_kind="independent",
            state="pass_complete",
            page_identity={
                "stream_id": "AX3A1-Q01@openalex",
                "pass_number": 2,
                "page_number": 0,
            },
            start_independent_pass_request=_resume_request("cursor_star", cursor="%2A"),
            previous_pass_complete=True,
            previous_pass_ledger_sha256=_sha(b"pass1"),
        ),
        _checkpoint_common(
            resume_action="restart_branch",
            state="http_failure",
            restart_branch_request=_resume_request("cursor_star", cursor="%2A"),
            failed_ledger_sha256=_sha(b"failed"),
        ),
        _checkpoint_common(
            resume_action="blocked_on_ruling",
            state="blocked_on_ruling",
            blocking_ruling_ids=["D-next"],
        ),
        _checkpoint_common(resume_action="not_applicable"),
    ],
    ids=[
        "continue_cursor",
        "start_independent_pass",
        "restart_branch",
        "blocked_on_ruling",
        "not_applicable",
    ],
)
def test_checkpoint_all_five_discriminator_arms_pass(checkpoint):
    search.validate_checkpoint(checkpoint)


def test_checkpoint_atomic_replace_writes_valid_state(tmp_path):
    path = tmp_path / "checkpoints" / "0001.json"
    checkpoint = _checkpoint_common(resume_action="not_applicable")
    search.write_checkpoint_atomic(path, checkpoint)
    assert json.loads(path.read_text(encoding="utf-8")) == checkpoint
    assert list(path.parent.glob(f".{path.name}.*")) == []


@pytest.mark.parametrize(
    ("stream_id", "position_name", "position_value"),
    [
        ("AX3A1-Q01-S1991@arxiv", "start", "0"),
        ("AX3A1-Q01@openalex", "cursor", "*"),
        ("AX3A1-Q3-T01-F01@dblp", "f", "0"),
    ],
)
def test_restart_branch_request_is_always_the_registered_branch_head(
    catalog, stream_id, position_name, position_value
):
    row = next(item for item in catalog["rows"] if item["stream_id"] == stream_id)
    request = search._branch_start_checkpoint_request(row)
    query = dict(parse_qsl(urlsplit(request["url"]).query, keep_blank_values=True))
    assert query[position_name] == position_value
    assert search._is_branch_start_request(row["index"], request)


def test_nonzero_failure_checkpoint_restarts_at_zero_not_failed_offset(
    catalog, seal
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    failed_request = search.materialize_request(row, 200)
    response = search.TransportResponse(
        status=503,
        entity_body=b"unavailable",
        headers=(),
        endpoint=search.ARXIV_ENDPOINT,
        final_url=failed_request["url"],
        content_type="text/plain",
        response_received_at="2026-08-28T00:00:00Z",
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._response_checkpoint(
        row=row,
        request=failed_request,
        response=response,
        seal=seal,
        budget=budget,
        now=_fixed_clock(),
        run_id="axis3-run-ready",
        pass_number=1,
        page_number=1,
        next_request=None,
    )
    search.validate_checkpoint(checkpoint)
    assert checkpoint["resume_action"] == "restart_branch"
    assert dict(
        parse_qsl(
            urlsplit(checkpoint["restart_branch_request"]["url"]).query
        )
    )["start"] == "0"
    assert dict(
        parse_qsl(
            urlsplit(checkpoint["continue_cursor_request"]["url"]).query
        )
    )["start"] == "200"


def test_manifest_generation_recovers_abandoned_unpointed_pair(seal, tmp_path):
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(SEALED_ARGV, "preflight"),
    )
    first_manifest = (tmp_path / "manifest.json").read_bytes()
    abandoned = tmp_path / search._GENERATION_ROOT / "000000000002"
    abandoned.mkdir()
    (abandoned / "manifest.json").write_bytes(b"incomplete generation")
    writer._write_manifest()
    assert (tmp_path / search._GENERATION_ROOT / "000000000001" / "manifest.json").read_bytes() == (
        first_manifest
    )
    assert (tmp_path / search._GENERATION_ROOT / "current").readlink().as_posix() == (
        "000000000002"
    )
    assert search._read_bundle_manifest(tmp_path)[3] == 2


def test_finalized_report_material_is_immutable_and_double_finalize_fails(
    catalog, seal, tmp_path
):
    writer, response, evidence = _packed_preflight_attempt(
        catalog, seal, tmp_path
    )
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence, entity_body=response.entity_body, checkpoint=None
    )
    writer.finalize_preflight({"generation": 1})
    first_manifest = search._read_bundle_manifest(tmp_path)[0]
    first_descriptor = first_manifest["preflight_report"]
    first_bytes = (tmp_path / first_descriptor["path"]).read_bytes()
    with pytest.raises(search.ContractError) as caught:
        writer.finalize_preflight({"generation": 2})
    assert caught.value.code == "bundle_finalized"
    assert (tmp_path / first_descriptor["path"]).read_bytes() == first_bytes


def test_bundle_checkpoint_string_downgrade_is_rejected():
    replayed_entries = [{"path": "checkpoints/000001.json", "sha256": _sha()}]
    assert search._validate_bundle_checkpoint_entries(replayed_entries) == (
        replayed_entries
    )
    with pytest.raises(search.ContractError) as caught:
        search._validate_bundle_checkpoint_entries(
            ["checkpoints/000001.json"]
        )
    assert caught.value.code == "bundle_checkpoint_downgrade"


def test_raw_response_survives_parse_gate_and_pending_intent_blocks_resume(
    catalog, seal, tmp_path
):
    availability = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(availability)
    transport = search.ScriptedTransport(
        [
            {
                "status": 200,
                "entity_body": b"not JSON but retained exactly",
                "headers": [["X-Raw", "kept"]],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": request["url"],
                "content_type": "text/plain",
            }
        ]
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    fake_time = _FakeTime()
    response = search._send_with_raw_commit(
        transport,
        request,
        search.WireBudget(),
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
        writer=writer,
        pass_number=0,
        page_number=0,
    )
    with pytest.raises(search.ContractError) as caught:
        search._validate_and_classify_response(
            row=availability,
            request=request,
            response=response,
            pass_number=0,
            page_number=0,
            classify_preflight=True,
        )
    assert caught.value.code == "response_mime"
    writer.materialize_pending_attempt()
    manifest = search._read_bundle_manifest(tmp_path)[0]
    assert manifest["attempt_intent"]["state"] == "response_received"
    raw = json.loads(
        (tmp_path / manifest["attempt_intent"]["raw_response_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert raw["response_received_at"] == "2026-08-28T00:00:00Z"
    assert (tmp_path / raw["entity_body_path"]).read_bytes() == (
        b"not JSON but retained exactly"
    )
    assert search._validate_bundle_for_resume(tmp_path, catalog=catalog, seal=seal) == {
        "pages": 0,
        "checkpoints": 0,
    }
    assert search._replay_preflight_wal(
        tmp_path, manifest["journal"]
    )["attempt_intent"]["state"] == "response_received"


def test_checkpoint_deadline_is_exactly_thirty_days():
    checkpoint = _checkpoint_common(resume_action="not_applicable")
    search.validate_checkpoint(checkpoint)
    first = datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)
    checkpoint["deadline_at"] = (first + timedelta(days=29)).isoformat().replace(
        "+00:00", "Z"
    )
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(checkpoint)
    assert caught.value.code == "checkpoint_deadline"


def test_checkpoint_wire_attempt_ceiling_is_inclusive():
    checkpoint = _checkpoint_common(
        resume_action="not_applicable",
        wire_attempt_count=search.MAX_WIRE_ATTEMPTS,
    )
    search.validate_checkpoint(checkpoint)
    checkpoint["wire_attempt_count"] += 1
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(checkpoint)
    assert caught.value.code == "schema_validation"


def test_preflight_200_separates_availability_from_lookup_resolution(
    catalog, seal, green_preflight_report
):
    report, transport = green_preflight_report
    search.validate_preflight_report(report, catalog, seal)
    first = next(row for row in report["rows"] if row["stream_id"] == "AX3A1-L-ID-01@openalex")
    assert first["transport_available"] is True
    assert first["lookup_resolved"] is True
    assert first["status"] == "ready"
    assert first["preflight_response_reusable_for_run"] is False
    assert transport.calls[0]["stream_id"] == "AX3A1-L-ID-01@openalex"
    assert report["wire_attempt_count"] == 1929
    assert report["axis_complete"] is False


def test_full_catalog_preflight_report_round_trips_without_wal(
    catalog, seal, green_preflight_report
):
    report, _transport = green_preflight_report
    restored = json.loads(search._canonical_json(report).decode("utf-8"))
    search.validate_preflight_report(restored, catalog, seal)
    assert len(restored["rows"]) == 2122
    assert len(restored["preflight_evidence"]) == 1929
    assert len(restored["pacing_observations"]) == 1929
    assert [
        observation["stream_id"]
        for observation in restored["pacing_observations"]
    ] == [evidence["stream_id"] for evidence in restored["preflight_evidence"]]
    assert [
        evidence["stream_id"] for evidence in restored["preflight_evidence"]
    ] == search._preflight_planned_stream_ids(catalog)
    assert restored["status_counts"]["blocked"] == 193


def test_preflight_report_observed_interval_is_nonblocking_n3(
    catalog, seal, green_preflight_report
):
    report, _transport = green_preflight_report
    mutant = copy.deepcopy(report)
    seen_dblp = 0
    for observation in mutant["pacing_observations"]:
        if observation["host"] == "dblp.org":
            seen_dblp += 1
            if seen_dblp == 2:
                observation["observed_interval_seconds"] = 44.87
                break
    assert seen_dblp == 2
    mutant["report_sha256"] = search._report_digest(mutant)
    search.validate_preflight_report(mutant, catalog, seal)


def test_preflight_200_can_be_available_but_unresolved_and_continues(
    catalog, catalog_data, seal
):
    transport = _unresolved_anchor_transport(catalog)
    fake_time = _FakeTime()
    report = search.run_preflight(
        catalog,
        catalog_data,
        seal,
        argv=SEALED_ARGV,
        commit=COMMIT,
        transport=transport,
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
    )
    first = next(
        row
        for row in report["rows"]
        if row["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    assert first["transport_available"] is True
    assert first["lookup_resolved"] is False
    assert first["status"] == "blocked"
    assert len(transport.calls) == 1929
    assert transport.calls[1]["stream_id"] != transport.calls[0]["stream_id"]


def test_run_ready_reissues_page_zero_orders_indices_and_never_completes_axis(
    catalog, green_preflight_report
):
    report, _preflight_transport = green_preflight_report
    statuses = {row["stream_id"]: row["status"] for row in report["rows"]}
    ready_rows = search._ordered_ready_rows(catalog, statuses)
    ready_ids = [row["stream_id"] for row in ready_rows]
    indices = [row["index"] for row in ready_rows]
    assert indices == sorted(
        indices, key={"arxiv": 0, "openalex": 1, "dblp": 2}.get
    )
    rank = {"arxiv": 0, "openalex": 1, "dblp": 2}
    assert ready_ids == [
        row["stream_id"]
        for row in sorted(
            (
                row
                for row in catalog["rows"]
                if statuses[row["stream_id"]] == "ready"
            ),
            key=lambda row: (rank[row["index"]], row["stream_id"]),
        )
    ]

    row = ready_rows[0]
    transport = search.NonProductionTransport(_dynamic_response)
    fake_time = _FakeTime()
    result = search._run_stream(
        row,
        transport,
        search.WireBudget(),
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
    )
    assert transport.calls[0] == search.materialize_request(row)
    assert result["stream_id"] == row["stream_id"]
    assert report["axis_complete"] is False


def test_unimplemented_count_only_control_never_claims_completion(catalog):
    row = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-C-OR-1-A@arxiv"
    )
    request = search.materialize_request(row)
    transport = search.ScriptedTransport(
        [
            {
                "status": 200,
                "entity_body": _arxiv_body(
                    total=250, interpreted_query=_arxiv_echo(request)
                ),
                "headers": [],
                "endpoint": search.ARXIV_ENDPOINT,
                "final_url": request["url"],
                "content_type": "application/atom+xml",
            }
        ]
    )
    fake_time = _FakeTime()
    result = search._run_stream(
        row,
        transport,
        search.WireBudget(),
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
    )
    assert result["complete"] is False
    assert result["reason"] == "control_evaluator_unimplemented"
    assert result["completion"] == {
        "complete": False,
        "completion_kind": "count_only",
        "declared_total": 250,
        "reason": "control_evaluator_unimplemented",
    }
    assert len(transport.calls) == 1


def test_bundle_rederived_count_only_control_never_claims_completion(
    catalog, seal
):
    row = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-C-OR-1-A@arxiv"
    )
    request = search.materialize_request(row)
    body = _arxiv_body(total=250, interpreted_query=_arxiv_echo(request))
    response = search.TransportResponse(
        status=200,
        entity_body=body,
        headers=(),
        endpoint=search.ARXIV_ENDPOINT,
        final_url=request["url"],
        content_type="application/atom+xml",
        response_received_at="2026-08-28T00:00:00Z",
    )
    evidence = search.capture_page_evidence(
        stream_id=row["stream_id"],
        pass_number=1,
        page_number=0,
        request=request,
        response=response,
        required_response_fields=row["required_response_fields"],
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._response_checkpoint(
        row=row,
        request=request,
        response=response,
        seal=seal,
        budget=budget,
        now=_fixed_clock(),
        run_id="axis3-run-ready",
        pass_number=1,
        page_number=0,
        next_request=None,
    )

    result = search._derive_stream_result(
        row, [(evidence, body, checkpoint)]
    )

    assert result["complete"] is False
    assert result["reason"] == "control_evaluator_unimplemented"
    assert result["completion"] == {
        "complete": False,
        "completion_kind": "count_only",
        "declared_total": 250,
        "reason": "control_evaluator_unimplemented",
    }
    assert result["pages"] == [evidence]
    assert result["checkpoint"] == checkpoint
    assert result["next_position"] is None


def test_wire_budget_includes_preflight_and_starts_thirty_day_clock():
    first = datetime(2026, 8, 1, tzinfo=timezone.utc)
    budget = search.WireBudget()
    budget.consume(first)
    assert budget.attempts == 1
    assert budget.deadline_at == first + timedelta(days=30)
    budget.attempts = search.MAX_WIRE_ATTEMPTS
    with pytest.raises(search.ContractError) as caught:
        budget.consume(first)
    assert caught.value.code == "wire_budget_exceeded"


def test_tier_enforcement_remains_outside_registration_executor_scope():
    assert not hasattr(search, "validate_tier_analysis")


def test_cli_exposes_only_required_axis3_phases():
    result = subprocess.run(
        [sys.executable, "tools/run_axis3_search.py", "--help"],
        cwd=search.REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "{validate-registration,preflight,run-ready,validate-bundle}" in result.stdout
    for command in ("preflight", "run-ready"):
        command_help = subprocess.run(
            [sys.executable, "tools/run_axis3_search.py", command, "--help"],
            cwd=search.REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        assert "--responses RESPONSES" in command_help.stdout


def test_mutation_m1_legacy_namespace_is_rejected(catalog):
    search.validate_catalog(catalog)
    mutant = copy.deepcopy(catalog)
    mutant["supersession"][0]["replacement_ids"][0] = mutant["supersession"][0]["legacy_id"]
    with pytest.raises(search.ContractError) as caught:
        search.validate_catalog(mutant)
    assert caught.value.code == "schema_validation"


def test_mutation_m2_one_minute_year_gap_is_rejected(catalog):
    search.validate_year_shards(catalog)
    mutant = copy.deepcopy(catalog)
    row = next(row for row in mutant["rows"] if row["stream_id"] == "AX3A1-Q01-S1991@arxiv")
    row["date_shard"]["end"] = "199112312358"
    with pytest.raises(search.ContractError) as caught:
        search.validate_catalog(mutant)
    assert caught.value.code == "year_shard_exact_cover"


def test_mutation_m3_normalized_primary_key_count_cannot_replace_work_id_count():
    body = _json_bytes(
        {
            "meta": {"count": 2, "next_cursor": None},
            "results": [
                {"id": "W1", "doi": "https://doi.org/10.1/same"},
                {"id": "W2", "doi": "https://doi.org/10.1/same"},
            ],
        }
    )
    result = search.evaluate_openalex_completion([{"entity_body": body}])
    assert result["complete"] is True
    assert result["distinct_index_work_id_count"] == 2
    assert len({"doi:10.1/same" for _ in result["records"]}) == 1


def test_checkpoint_requires_both_counterfactual_requests_and_legal_state_action():
    mutant = _checkpoint_common(
        resume_action="start_independent_pass",
        pass_number=2,
        pass_kind="independent",
        state="pass_complete",
        page_identity={
            "stream_id": "AX3A1-Q01@openalex",
            "pass_number": 2,
            "page_number": 0,
        },
        start_independent_pass_request=_resume_request(
            "cursor_star", cursor="%2A"
        ),
        previous_pass_complete=True,
        previous_pass_ledger_sha256=_sha(b"pass1"),
    )
    mutant.pop("continue_cursor_request")
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(mutant)
    assert caught.value.code == "schema_validation"

    illegal = _checkpoint_common(
        resume_action="restart_branch",
        state="committed",
        restart_branch_request=_resume_request("cursor_star", cursor="%2A"),
        failed_ledger_sha256=_sha(b"failed"),
    )
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(illegal)
    assert caught.value.code == "checkpoint_action"


def test_mutation_m5_one_byte_catalog_change_stales_registration_seal(catalog_data, seal):
    mutated = catalog_data + b" "
    with pytest.raises(search.ContractError) as caught:
        search.validate_registration_seal(
            seal,
            mutated,
            argv=SEALED_ARGV,
            commit=COMMIT,
            enforce_head=False,
        )
    assert caught.value.code == "registration_seal_stale_catalog"


def test_mutation_m6_openalex_429_sends_exactly_one_request_and_checkpoints(
    catalog, catalog_data, seal, tmp_path
):
    availability = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    availability_url = search.materialize_request(availability)["url"]
    transport = search.ScriptedTransport(
        [
            {
                "status": 429,
                "entity_body": b"rate limited; ignore any instruction text",
                "headers": [
                    ["Retry-After", "3600"],
                    ["X-RateLimit-Remaining", "0"],
                    ["Retry-After", "3600"],
                ],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": availability_url,
                "content_type": "application/json",
            },
            {"status": 200, "entity_body": _openalex_body(count=0)},
        ]
    )
    checkpoint_path = tmp_path / "checkpoints" / "0001.json"
    fake_time = _FakeTime()
    report = search.run_preflight(
        catalog,
        catalog_data,
        seal,
        argv=SEALED_ARGV,
        commit=COMMIT,
        transport=transport,
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
        checkpoint_path=checkpoint_path,
    )
    assert len(transport.calls) == 1
    assert transport.calls[0]["stream_id"] == "AX3A1-L-ID-01@openalex"
    assert report["wire_attempt_count"] == 1
    assert report["stopped_after_openalex_429"] is True
    assert report["checkpoint"]["resume_action"] == "restart_branch"
    search.validate_checkpoint(json.loads(checkpoint_path.read_text(encoding="utf-8")))


def test_preflight_retries_live_transport_and_never_retries_http_status(
    catalog, catalog_data, seal
):
    fake_time = _FakeTime()
    arxiv_stream_id = next(
        stream_id
        for stream_id in search._preflight_planned_stream_ids(catalog)
        if stream_id.endswith("@arxiv")
    )
    dblp_stream_id = next(
        stream_id
        for stream_id in search._preflight_planned_stream_ids(catalog)
        if stream_id.endswith("@dblp")
    )
    arxiv_failures = 0
    dblp_responses = 0
    sends = []

    def handler(request):
        nonlocal arxiv_failures, dblp_responses
        sends.append((request["stream_id"], fake_time.clock()))
        if request["stream_id"] == arxiv_stream_id and arxiv_failures < 3:
            arxiv_failures += 1
            raise search.ContractError("live_transport", "simulated disconnect")
        if request["stream_id"] == dblp_stream_id:
            dblp_responses += 1
            return {
                "status": 503,
                "entity_body": b"DBLP unavailable",
                "headers": [],
                "endpoint": search.DBLP_ENDPOINT,
                "final_url": request["url"],
                "content_type": "text/plain",
            }
        return _dynamic_response(request)

    transport = search.NonProductionTransport(handler)
    report = search.run_preflight(
        catalog,
        catalog_data,
        seal,
        argv=SEALED_ARGV,
        commit=COMMIT,
        transport=transport,
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
    )

    arxiv_sends = [sent_at for stream_id, sent_at in sends if stream_id == arxiv_stream_id]
    assert len(arxiv_sends) == 4
    assert [
        (right - left).total_seconds()
        for left, right in zip(arxiv_sends, arxiv_sends[1:])
    ] == [3.0, 6.0, 12.0]
    arxiv_row = next(row for row in report["rows"] if row["stream_id"] == arxiv_stream_id)
    assert arxiv_row["status"] == "ready"
    arxiv_offset = next(
        offset for offset, (stream_id, _sent_at) in enumerate(sends)
        if stream_id == arxiv_stream_id
    )
    assert [stream_id for stream_id, _sent_at in sends[arxiv_offset : arxiv_offset + 4]] == [
        arxiv_stream_id
    ] * 4
    assert sends[arxiv_offset + 4][0] != arxiv_stream_id

    assert dblp_responses == 1
    dblp_evidence = [
        evidence
        for evidence in report["preflight_evidence"]
        if evidence["stream_id"] == dblp_stream_id
    ]
    assert [evidence["status"] for evidence in dblp_evidence] == [503]
    dblp_row = next(row for row in report["rows"] if row["stream_id"] == dblp_stream_id)
    assert dblp_row["status"] == "unavailable"
    assert dblp_row["reason"] == "http_503"
    assert report["wire_attempt_count"] == 1932
    assert len(transport.calls) == 1932
    assert len(report["preflight_evidence"]) == 1929
    assert len(report["pacing_observations"]) == 1932


def test_preflight_exhausts_four_dblp_transport_attempts_then_cools_down(
    catalog, catalog_data, seal
):
    fake_time = _FakeTime()
    failed_stream_id = None
    failed_attempts = 0
    sends = []

    def handler(request):
        nonlocal failed_stream_id, failed_attempts
        sends.append((request["stream_id"], fake_time.clock()))
        if request["index"] == "dblp" and failed_stream_id is None:
            failed_stream_id = request["stream_id"]
        if request["stream_id"] == failed_stream_id and failed_attempts < 4:
            failed_attempts += 1
            raise search.ContractError("live_transport", "simulated DBLP disconnect")
        return _dynamic_response(request)

    transport = search.NonProductionTransport(handler)
    report = search.run_preflight(
        catalog,
        catalog_data,
        seal,
        argv=SEALED_ARGV,
        commit=COMMIT,
        transport=transport,
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
    )

    assert failed_stream_id is not None
    failed_evidence = [
        evidence
        for evidence in report["preflight_evidence"]
        if evidence["stream_id"] == failed_stream_id
    ]
    assert failed_evidence == []
    assert report["wire_attempt_count"] == 1932
    assert len(transport.calls) == 1932
    assert search.DBLP_FAILURE_COOLDOWN_SECONDS in fake_time.sleeps
    failure_offsets = [
        offset
        for offset, (stream_id, _sent_at) in enumerate(sends)
        if stream_id == failed_stream_id
    ]
    assert failure_offsets == list(
        range(failure_offsets[0], failure_offsets[0] + 4)
    )
    failed_send_times = [sends[offset][1] for offset in failure_offsets]
    assert [
        (right - left).total_seconds()
        for left, right in zip(failed_send_times, failed_send_times[1:])
    ] == [45.0, 45.0, 60.0]
    last_failure_offset = failure_offsets[-1]
    assert sends[last_failure_offset + 1][1] - sends[last_failure_offset][1] == (
        timedelta(seconds=search.DBLP_FAILURE_COOLDOWN_SECONDS)
    )
    failed_row = next(
        row for row in report["rows"] if row["stream_id"] == failed_stream_id
    )
    assert failed_row["status"] == "unavailable"
    assert failed_row["reason"] == "live_transport_retry_exhausted"


def test_preflight_does_not_swallow_non_transport_contract_errors(
    catalog, catalog_data, seal
):
    transport = search.NonProductionTransport(
        lambda _request: (_ for _ in ()).throw(
            search.ContractError("wire_budget_exceeded", "simulated budget failure")
        )
    )
    fake_time = _FakeTime()
    with pytest.raises(search.ContractError) as caught:
        search.run_preflight(
            catalog,
            catalog_data,
            seal,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=transport,
            clock=fake_time.clock,
            sleeper=fake_time.sleep,
        )
    assert caught.value.code == "wire_budget_exceeded"
    assert len(transport.calls) == 1


def test_registration_seal_failure_calls_no_transport(catalog, catalog_data, seal):
    mutant = copy.deepcopy(seal)
    mutant["catalog_sha256"] = _sha(b"wrong")
    transport = search.ScriptedTransport([])
    with pytest.raises(search.ContractError):
        search.run_preflight(
            catalog,
            catalog_data,
            mutant,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=transport,
            clock=_fixed_clock,
        )
    assert transport.calls == []


def test_mutation_m7_one_byte_entity_change_breaks_bundle_validation(
    catalog, seal, tmp_path
):
    row = next(row for row in catalog["rows"] if row["stream_id"] == "AX3A1-Q01@openalex")
    request = search.materialize_request(row)
    body = _openalex_body(count=0, oql=row["expected_interpreted_query"])
    response = search.TransportResponse(
        status=200,
        entity_body=body,
        headers=(("X-Test", "one"), ("X-Test", "two")),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    evidence = search.capture_page_evidence(
        stream_id=row["stream_id"],
        pass_number=0,
        page_number=0,
        request=request,
        response=response,
        required_response_fields=row["required_response_fields"],
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(SEALED_ARGV, "preflight"),
    )
    writer.commit_response(
        evidence=evidence,
        entity_body=body,
        checkpoint=search._response_checkpoint(
            row=row,
            request=request,
            response=response,
            seal=seal,
            budget=budget,
            now=_fixed_clock(),
            run_id="axis3-live-preflight",
            pass_number=1,
            page_number=0,
            next_request=None,
        ),
    )
    assert search._validate_bundle_for_resume(tmp_path, catalog=catalog, seal=seal) == {
        "pages": 1,
        "checkpoints": 1,
    }
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    body_path = tmp_path / manifest["pages"][0]["entity_body_path"]
    body_path.write_bytes(body[:-1] + (b"]" if body[-1:] != b"]" else b"}"))
    with pytest.raises(search.ContractError) as caught:
        search._validate_bundle_for_resume(tmp_path, catalog=catalog, seal=seal)
    assert caught.value.code == "evidence_body_digest"


def test_old_outgoing_id_is_rejected(catalog):
    row = copy.deepcopy(catalog["rows"][0])
    row["stream_id"] = "AX3-Q1@arxiv"
    with pytest.raises(search.ContractError) as caught:
        search.materialize_request(row)
    assert caught.value.code == "legacy_outgoing"


def test_review_canonicalizers_collapse_aliases_and_preserve_raw_locator():
    assert search.canonicalize_index_work_id(
        "arxiv", "https://arxiv.org/abs/2604.24658v3"
    ) == "2604.24658"
    assert search.canonicalize_index_work_id(
        "openalex", "https://openalex.org/W1"
    ) == "W1"
    records = search.extract_index_work_records(
        "openalex", _openalex_body(count=1, work_id="https://openalex.org/W1")
    )
    assert records == [
        {
            "raw_index_work_id": "https://openalex.org/W1",
            "index_work_id": "W1",
            "field_locator": "/results/0/id",
        }
    ]
    raw_arxiv = _arxiv_body(
        total=1, work_id="  https://arxiv.org/abs/2604.24658v3  "
    )
    arxiv_records = search.extract_index_work_records("arxiv", raw_arxiv)
    assert arxiv_records[0]["raw_index_work_id_before_strip"] == (
        "  https://arxiv.org/abs/2604.24658v3  "
    )
    assert arxiv_records[0]["raw_index_work_id"] == (
        "https://arxiv.org/abs/2604.24658v3"
    )
    assert arxiv_records[0]["index_work_id"] == "2604.24658"
    aliases = _json_bytes(
        {
            "meta": {"count": 2, "next_cursor": None},
            "results": [{"id": "W1"}, {"id": "https://openalex.org/W1"}],
        }
    )
    assert search.evaluate_openalex_completion([{"entity_body": aliases}])["complete"] is False
    for index, value in (
        ("openalex", "https://example.invalid/W1"),
        ("arxiv", "https://arxiv.org/pdf/2604.24658"),
        ("dblp", "../escape"),
    ):
        with pytest.raises(search.ContractError) as caught:
            search.canonicalize_index_work_id(index, value)
        assert caught.value.code == "index_work_id_invalid"


@pytest.mark.parametrize(
    ("count", "ids", "reason"),
    [
        (0, [], "lookup_zero_results"),
        (2, ["W1"], "lookup_multiple_results"),
        (1, [], "lookup_result_missing"),
        (1, [None], "lookup_work_id_missing"),
    ],
)
def test_review_lookup_requires_declared_and_actual_exact_one(
    catalog, count, ids, reason
):
    row = next(
        item for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    results = [{} if value is None else {"id": value} for value in ids]
    response = search.TransportResponse(
        status=200,
        entity_body=_json_bytes(
            {"meta": {"count": count, "next_cursor": None}, "results": results}
        ),
        headers=(),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=search.materialize_request(row)["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    probe = search._probe_response(row, response)
    assert probe["status"] == "blocked"
    assert probe["lookup_resolved"] is False
    assert probe["reason"] == reason


def test_run_stream_reapplies_lookup_exact_one(catalog):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(row)
    transport = search.ScriptedTransport(
        [
            {
                "status": 200,
                "entity_body": _json_bytes(
                    {
                        "meta": {"count": 2, "next_cursor": None},
                        "results": [{"id": "W1"}, {"id": "W2"}],
                    }
                ),
                "headers": [],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": request["url"],
                "content_type": "application/json",
            }
        ]
    )
    fake_time = _FakeTime()
    result = search._run_stream(
        row,
        transport,
        search.WireBudget(),
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
    )
    assert result["complete"] is False
    assert result["reason"] == "lookup_multiple_results"


def test_review_page_continuity_rejects_short_and_shifted_pages(catalog):
    openalex = next(
        item for item in catalog["rows"] if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    short = search.TransportResponse(
        status=200,
        entity_body=_openalex_body(count=2, work_id="W1", next_cursor="next"),
        headers=(),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=search.materialize_request(openalex)["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    with pytest.raises(search.ContractError) as caught:
        search._page_progress(openalex, short, None)
    assert caught.value.code == "page_short_nonterminal"

    dblp = next(
        item for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q3-T01-F01@dblp"
    )
    shifted_body = _json_bytes(
        {
            "result": {
                "hits": {
                    "@total": "1",
                    "@first": "100",
                    "@sent": "1",
                    "hit": [{"info": {"key": "conf/x/y", "year": "2026"}}],
                }
            }
        }
    )
    shifted = search.TransportResponse(
        status=200,
        entity_body=shifted_body,
        headers=(),
        endpoint=search.DBLP_ENDPOINT,
        final_url=search.materialize_request(dblp)["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    with pytest.raises(search.ContractError) as caught:
        search._page_progress(dblp, shifted, 0)
    assert caught.value.code == "page_response_position"


def test_review_preflight_report_rejects_self_redigest_tampering(
    catalog, seal, green_preflight_report
):
    report, _transport = green_preflight_report
    mutant = copy.deepcopy(report)
    ready = next(item for item in mutant["rows"] if item["status"] == "ready")
    ready["declared_total"] += 1
    mutant["report_sha256"] = search._report_digest(mutant)
    evidences = report["preflight_evidence"]
    bodies = [
        _dynamic_response(evidence["request"])["entity_body"]
        for evidence in evidences
    ]
    with pytest.raises(search.ContractError) as caught:
        search._validate_preflight_report_against_bundle_material(
            mutant, catalog, seal, evidences, bodies, []
        )
    assert caught.value.code == "bundle_preflight"

    mutant = copy.deepcopy(report)
    mutant["wire_attempt_count"] = -1
    mutant["report_sha256"] = search._report_digest(mutant)
    with pytest.raises(search.ContractError) as caught:
        search.validate_preflight_report(mutant, catalog, seal)
    assert caught.value.code == "preflight_report_schema"


def test_review_run_ready_rejects_serialized_report_without_bundle(
    catalog, catalog_data, seal, green_preflight_report
):
    report, _transport = green_preflight_report
    serialized_report = json.loads(json.dumps(report))
    transport = search.ScriptedTransport([])
    with pytest.raises(search.ContractError) as caught:
        search.run_ready(
            catalog,
            catalog_data,
            seal,
            serialized_report,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=transport,
            clock=_fixed_clock,
        )
    assert caught.value.code == "bundle_preflight"
    assert transport.calls == []


def test_review_transport_boundary_and_final_query_are_strict(catalog):
    with pytest.raises(search.ContractError) as caught:
        search.TransportResponse.from_mapping(
            {
                "status": 200,
                "entity_body": "{}",
                "headers": [],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": search.OPENALEX_ENDPOINT,
                "content_type": "application/json",
            },
            strict_transport_boundary=True,
        )
    assert caught.value.code == "transport_response"

    row = next(
        item for item in catalog["rows"] if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=200,
        entity_body=_openalex_body(count=0, oql=row["expected_interpreted_query"]),
        headers=(),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"].replace("per-page=200", "per-page=1"),
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    with pytest.raises(search.ContractError) as caught:
        search._validate_response_envelope(row, request, response)
    assert caught.value.code == "response_final_url"


def test_nonproduction_http_transport_is_one_attempt_without_redirect(catalog):
    row = next(
        item for item in catalog["rows"] if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    request = search.materialize_request(row)

    class LocalResponse:
        status = 302

        def read(self):
            return b"redirect response is saved as data"

        def getheaders(self):
            return [("Location", "https://example.invalid/redirect")]

    class LocalConnection:
        def __init__(self):
            self.requests = []
            self.responses = 0
            self.closed = 0

        def request(self, method, target, headers):
            self.requests.append((method, target, headers))

        def getresponse(self):
            self.responses += 1
            return LocalResponse()

        def close(self):
            self.closed += 1

    connections = []

    def factory(host, *, port, timeout):
        connection = LocalConnection()
        connections.append((host, port, timeout, connection))
        return connection

    transport = search.NonProductionHTTPTransport(connection_factory=factory)
    budget = search.WireBudget()
    response = search._send(transport, request, budget, _fixed_clock)
    assert response.status == 302
    assert response.final_url == request["url"]
    assert budget.attempts == 1
    assert len(transport.calls) == len(connections) == 1
    assert len(connections[0][3].requests) == connections[0][3].responses == 1
    assert connections[0][3].closed == 1

    with pytest.raises(TypeError):
        search.LiveHTTPTransport(connection_factory=factory)


def test_production_transport_factory_has_structural_consistency_only():
    """No network-zero test can legitimately exercise production send receipts."""

    session = search.create_live_search_session()
    assert type(session) is search.LiveSearchSession
    assert type(session._transport) is search.LiveHTTPTransport

    class UnregisteredTransport:
        def send(self, _request):
            raise AssertionError("send must not be reached")

    phase = search.validate_effective_phase_argv(
        LIVE_PREFLIGHT_ARGV, "preflight"
    )
    with pytest.raises(search.ContractError) as caught:
        search._bind_transport_semantics(phase, UnregisteredTransport())
    assert caught.value.code == "bundle_phase_argv"


def test_review_dblp_year_locator_missing_and_2026_boundary():
    valid = _json_bytes(
        {
            "result": {
                "hits": {
                    "hit": [{"info": {"key": "conf/x/y", "year": "2026"}}]
                }
            }
        }
    )
    assert search.validate_dblp_record_years(valid) == [
        {
            "raw_year": "2026",
            "year": 2026,
            "field_locator": "/result/hits/hit/0/info/year",
        }
    ]
    missing = _json_bytes(
        {"result": {"hits": {"hit": [{"info": {"key": "conf/x/y"}}]}}}
    )
    with pytest.raises(search.ContractError) as caught:
        search.validate_dblp_record_years(missing)
    assert caught.value.code == "dblp_year_missing"
    future = _json_bytes(
        {
            "result": {
                "hits": {
                    "hit": [{"info": {"key": "conf/x/y", "year": "2027"}}]
                }
            }
        }
    )
    with pytest.raises(search.ContractError) as caught:
        search.validate_dblp_record_years(future)
    assert caught.value.code == "dblp_cutoff_exceeded"


def test_review_429_non_success_mime_is_raw_bundled_before_stop(
    catalog, seal, tmp_path
):
    body = b"<html>rate limited data only</html>"
    availability = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    transport = search.ScriptedTransport(
        [
            {
                "status": 429,
                "entity_body": body,
                "headers": [["Retry-After", "60"]],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": search.materialize_request(availability)["url"],
                "content_type": "text/html",
            }
        ]
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    budget = search.WireBudget()
    request = search.materialize_request(availability)
    fake_time = _FakeTime()
    response = search._send_with_raw_commit(
        transport,
        request,
        budget,
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
        writer=writer,
        pass_number=0,
        page_number=0,
    )
    evidence, _probe = search._validate_and_classify_response(
        row=availability,
        request=request,
        response=response,
        pass_number=0,
        page_number=0,
        classify_preflight=True,
    )
    checkpoint = search._quota_checkpoint(
        row=availability,
        request=request,
        response=response,
        seal=seal,
        budget=budget,
        now=_fixed_clock(),
    )
    writer.commit_response(
        evidence=evidence,
        entity_body=body,
        checkpoint=checkpoint,
    )
    assert len(transport.calls) == 1
    assert search._validate_bundle_for_resume(
        tmp_path, catalog=catalog, seal=seal
    ) == {
        "pages": 1,
        "checkpoints": 1,
    }
    manifest = search._read_bundle_manifest(tmp_path)[0]
    assert manifest["lifecycle"] == "in_progress"
    page = manifest["pages"][0]
    assert (tmp_path / page["entity_body_path"]).read_bytes() == body
    assert isinstance(manifest["checkpoints"][0]["sha256"], str)
    assert manifest["ledger"]["sha256"] == _sha(
        search._canonical_json(search._load_manifest_ledger(tmp_path, manifest))
    )


def test_non_200_final_query_mismatch_is_raw_committed_then_rejected(
    catalog, seal, tmp_path
):
    availability = next(
        row
        for row in catalog["rows"]
        if row["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(availability)
    transport = search.ScriptedTransport(
        [
            {
                "status": 429,
                "entity_body": b"wrong-query response remains raw data",
                "headers": [["Retry-After", "60"]],
                "endpoint": search.OPENALEX_ENDPOINT,
                "final_url": request["url"].replace("per-page=1", "per-page=2"),
                "content_type": "text/html",
            }
        ]
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(
            SEALED_ARGV, "preflight"
        ),
        defer_manifest_fold=True,
    )
    fake_time = _FakeTime()
    response = search._send_with_raw_commit(
        transport,
        request,
        search.WireBudget(),
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
        writer=writer,
        pass_number=0,
        page_number=0,
    )
    with pytest.raises(search.ContractError) as caught:
        search._validate_response_envelope(availability, request, response)
    assert caught.value.code == "response_final_url"
    writer.materialize_pending_attempt()
    manifest = search._read_bundle_manifest(tmp_path)[0]
    assert manifest["attempt_intent"]["state"] == "response_received"
    raw = json.loads(
        (tmp_path / manifest["attempt_intent"]["raw_response_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert (tmp_path / raw["entity_body_path"]).read_bytes() == (
        b"wrong-query response remains raw data"
    )


def test_registration_seal_binds_frozen_closure_but_not_runtime_tree(catalog_data, seal):
    assert seal["frozen_semantics_sha256"] == search.FROZEN_SEMANTICS_SHA256
    assert [item["path"] for item in seal["frozen_input_digests"]] == [
        "docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md",
        "docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md",
    ]
    assert "runtime_digests" not in seal
    assert set(seal["environment_identity"]) == {
        "jsonschema_distribution_version",
        "python_implementation",
        "python_version",
    }
    assert seal["frozen_input_digests"][0]["sha256"] == (
        "eace24a94ed3e206b401e8264675f81b7e7278b6aa90b39a55ac26353d1cb89c"
    )
    assert seal["frozen_input_digests"][1]["sha256"] == (
        "1fb7517081f5cc73a37021768aabf08443970b71365ba41816c623be90302b39"
    )
    assert seal["phase_argv_contracts_sha256"] == search._sha256(
        search._canonical_json(search.PHASE_ARGV_CONTRACTS)
    )
    assert seal["resolved_head_commit"] == search.resolve_head_commit()
    assert seal["commit"] == COMMIT


def test_head_gate_is_blob_closure_not_global_commit_identity():
    search._verify_head_closure([search.FROZEN_INPUT_PATHS[0]], search.REPO_ROOT)
    source = inspect.getsource(search.build_registration_seal)
    assert "_verify_head_closure(closure_paths, repo_root)" in source
    assert "commit != actual_head" not in source


def test_frozen_registration_extracts_all_ids_and_query_bytes(catalog):
    frozen = search.FROZEN_INPUT_PATHS[0].read_bytes()
    extracted = search.extract_frozen_registration_closure(frozen)
    assert len(extracted["legacy_ids"]) == 1543
    assert sum(len(values) for values in extracted["term_blocks"].values()) == 74
    assert len(extracted["branches"]) == 10
    assert len(extracted["dblp_products"]) == 8
    search.validate_frozen_registration_closure(catalog, frozen)

    mutant = copy.deepcopy(catalog)
    main = next(
        row
        for row in mutant["rows"]
        if row["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    main["request_factory"]["canonical_template"] = main["request_factory"][
        "canonical_template"
    ].replace("program+synthesis", "program+analysis", 1)
    with pytest.raises(search.ContractError) as caught:
        search.validate_frozen_registration_closure(mutant, frozen)
    assert caught.value.code == "frozen_preregistration_query_semantics"


def test_frozen_main_request_oracle_remains_effective_after_semantics_gate(catalog):
    frozen = search.FROZEN_INPUT_PATHS[0].read_bytes()
    mutant = copy.deepcopy(catalog)
    main = next(
        row
        for row in mutant["rows"]
        if row["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    main["role"] = "auxiliary"
    with pytest.raises(search.ContractError) as caught:
        search.validate_frozen_registration_closure(mutant, frozen)
    assert caught.value.code == "frozen_main_request_oracle"


def test_review_normal_page_checkpoint_resumes_and_rejoins_ready_loop(
    catalog, seal
):
    row = next(
        item for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    request = search.materialize_request(row)
    next_request = search.materialize_request(row, 200)
    body = _arxiv_page(
        total=201,
        start=0,
        work_ids=[f"2601.{number:05d}" for number in range(1, 201)],
        interpreted_query=_arxiv_echo(request),
    )
    response = search.TransportResponse(
        status=200,
        entity_body=body,
        headers=(),
        endpoint=search.ARXIV_ENDPOINT,
        final_url=request["url"],
        content_type="application/atom+xml",
        response_received_at="2026-08-28T00:00:00Z",
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._response_checkpoint(
        row=row, request=request, response=response, seal=seal, budget=budget,
        now=_fixed_clock(), run_id="axis3-run-ready", pass_number=1,
        page_number=0, next_request=next_request,
    )
    search.validate_checkpoint(checkpoint)
    assert checkpoint["resume_action"] == "continue_cursor"
    assert checkpoint["continue_cursor_request"] == search._request_without_stream(
        next_request
    )
    assert checkpoint["start_independent_pass_request"] == (
        search._branch_start_checkpoint_request(row)
    )


def test_resume_continues_every_nonterminal_page_before_next_ready_row(
    catalog
):
    row = next(
        item for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    first_request = search.materialize_request(row)
    second_request = search.materialize_request(row, 200)
    third_request = search.materialize_request(row, 400)
    transport = search.ScriptedTransport(
        [
            {
                "status": 200,
                "entity_body": _arxiv_page(
                    total=401, start=0,
                    work_ids=[f"2601.{number:05d}" for number in range(1, 201)],
                    interpreted_query=_arxiv_echo(first_request),
                ),
                "headers": [], "endpoint": search.ARXIV_ENDPOINT,
                "final_url": first_request["url"],
                "content_type": "application/atom+xml",
            },
            {
                "status": 200,
                "entity_body": _arxiv_page(
                    total=401, start=200,
                    work_ids=[f"2601.{number:05d}" for number in range(201, 401)],
                    interpreted_query=_arxiv_echo(second_request),
                ),
                "headers": [], "endpoint": search.ARXIV_ENDPOINT,
                "final_url": second_request["url"],
                "content_type": "application/atom+xml",
            },
            {
                "status": 200,
                "entity_body": _arxiv_page(
                    total=401, start=400, work_ids=["2601.00401"],
                    interpreted_query=_arxiv_echo(third_request),
                ),
                "headers": [], "endpoint": search.ARXIV_ENDPOINT,
                "final_url": third_request["url"],
                "content_type": "application/atom+xml",
            },
        ]
    )
    fake_time = _FakeTime()
    result = search._run_stream(
        row,
        transport,
        search.WireBudget(),
        fake_time.clock,
        limiter=_fake_limiter(fake_time),
    )
    assert transport.calls == [first_request, second_request, third_request]
    assert result["complete"] is True
    assert result["completion"]["distinct_index_work_id_count"] == 401


def test_resume_terminal_tail_advances_without_resending_committed_page(
    catalog, seal
):
    row = next(
        item for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01-S1991@arxiv"
    )
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=200,
        entity_body=_arxiv_page(
            total=1, start=0, work_ids=["2601.00001"],
            interpreted_query=_arxiv_echo(request),
        ),
        headers=(), endpoint=search.ARXIV_ENDPOINT, final_url=request["url"],
        content_type="application/atom+xml",
        response_received_at="2026-08-28T00:00:00Z",
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._response_checkpoint(
        row=row, request=request, response=response, seal=seal, budget=budget,
        now=_fixed_clock(), run_id="axis3-run-ready", pass_number=1,
        page_number=0, next_request=None,
    )
    search.validate_checkpoint(checkpoint)
    assert checkpoint["state"] == "committed"
    assert checkpoint["resume_action"] == "not_applicable"
    assert "restart_branch_request" not in checkpoint


def test_review_producer_bundle_rejects_self_redigested_ledger_prefix(
    catalog, seal
):
    row = next(
        item for item in catalog["rows"] if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=200,
        entity_body=_openalex_body(
            count=0, oql=row["expected_interpreted_query"]
        ),
        headers=(),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._response_checkpoint(
        row=row,
        request=request,
        response=response,
        seal=seal,
        budget=budget,
        now=_fixed_clock(),
        run_id="axis3-live-preflight",
        pass_number=1,
        page_number=0,
        next_request=None,
    )
    expected_prefix = checkpoint["ledger_prefix_sha256"]
    search._validate_checkpoint_ledger_prefix(checkpoint, expected_prefix)
    checkpoint["ledger_prefix_sha256"] = _sha(b"forged-prefix")
    with pytest.raises(search.ContractError) as caught:
        search._validate_checkpoint_ledger_prefix(checkpoint, expected_prefix)
    assert caught.value.code == "bundle_checkpoint_ledger"


def _packed_preflight_attempt(catalog, seal, bundle):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(row)
    body = _openalex_body(count=1, work_id="https://openalex.org/W260424658")
    response = search.TransportResponse(
        status=200,
        entity_body=body,
        headers=(("X-WAL", "exact"),),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    evidence = search.capture_page_evidence(
        stream_id=row["stream_id"],
        pass_number=0,
        page_number=0,
        request=request,
        response=response,
        required_response_fields=row["required_response_fields"],
    )
    writer = search.BundleWriter(
        bundle,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(SEALED_ARGV, "preflight"),
        defer_manifest_fold=True,
    )
    writer.begin_attempt(
        request=request,
        pass_number=0,
        page_number=0,
        expected_wire_attempt_count=1,
        intent_at=_fixed_clock(),
    )
    return writer, response, evidence


@pytest.fixture
def finalized_one_attempt_preflight(catalog, seal, tmp_path):
    writer, response, evidence = _packed_preflight_attempt(
        catalog, seal, tmp_path
    )
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence,
        entity_body=response.entity_body,
        checkpoint=None,
    )
    writer.finalize_preflight({"crash_test": "single-attempt"})
    search._read_bundle_manifest(tmp_path)
    search._replay_preflight_wal(
        tmp_path, search._read_bundle_manifest(tmp_path)[0]["journal"]
    )
    return tmp_path


def test_preflight_wal_partial_commit_recovers_pending_prefix_without_resend(
    catalog, seal, tmp_path
):
    writer, response, evidence = _packed_preflight_attempt(catalog, seal, tmp_path)
    writer.record_raw_response(response)
    prefix_size = writer.journal_byte_count
    writer.commit_response(
        evidence=evidence,
        entity_body=response.entity_body,
        checkpoint=None,
    )
    wal_path = tmp_path / search._PREFLIGHT_WAL_RELATIVE
    complete = wal_path.read_bytes()
    wal_path.write_bytes(complete[: prefix_size + (len(complete) - prefix_size) // 2])

    assert search._validate_bundle_for_resume(tmp_path, catalog=catalog, seal=seal) == {
        "pages": 0,
        "checkpoints": 0,
    }
    replayed = search._replay_preflight_wal(
        tmp_path, search._read_bundle_manifest(tmp_path)[0]["journal"]
    )
    assert replayed["attempt_intent"]["state"] == "response_received"


def test_preflight_wal_pending_intent_blocks_without_send(
    catalog, seal, tmp_path
):
    writer, _response, _evidence = _packed_preflight_attempt(
        catalog, seal, tmp_path
    )
    replayed = search._replay_preflight_wal(
        tmp_path, writer._journal_descriptor(sealed=False)
    )
    assert replayed["attempt_intent"]["state"] == "pending"


def test_preflight_wal_one_byte_change_is_rejected(catalog, seal, tmp_path):
    writer, response, evidence = _packed_preflight_attempt(catalog, seal, tmp_path)
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence,
        entity_body=response.entity_body,
        checkpoint=None,
    )
    writer.finalize_preflight({"crash_test": "sealed"})
    manifest = search._read_bundle_manifest(tmp_path)[0]
    assert manifest["journal"]["record_count"] == 2
    assert manifest["checkpoints"] == []
    assert not (tmp_path / "attempts").exists()
    assert not (tmp_path / "responses").exists()
    assert not (tmp_path / "checkpoints").exists()
    wal_path = tmp_path / search._PREFLIGHT_WAL_RELATIVE
    mutant = bytearray(wal_path.read_bytes())
    mutant[-1] ^= 1
    wal_path.write_bytes(bytes(mutant))
    with pytest.raises(search.ContractError) as caught:
        search.validate_bundle(
            tmp_path, catalog=catalog, seal=seal, _allow_nonproduction=True
        )
    assert caught.value.code == "bundle_journal"


def test_preflight_wal_raw_frame_is_durable_before_parse_or_commit(
    catalog, seal, tmp_path
):
    writer, response, _evidence = _packed_preflight_attempt(catalog, seal, tmp_path)
    writer.record_raw_response(response)
    replayed = search._replay_preflight_wal(
        tmp_path, writer._journal_descriptor(sealed=False)
    )
    assert replayed["descriptor"]["frame_count"] == 2
    assert replayed["descriptor"]["record_count"] == 1
    assert replayed["attempt_intent"]["state"] == "response_received"
    assert replayed["pending_raw"][1] == response.entity_body
    assert search._validate_bundle_for_resume(
        tmp_path, catalog=catalog, seal=seal
    ) == {"pages": 0, "checkpoints": 0}


def test_in_progress_bundle_is_resume_only(catalog, seal, tmp_path):
    writer, response, evidence = _packed_preflight_attempt(catalog, seal, tmp_path)
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence,
        entity_body=response.entity_body,
        checkpoint=None,
    )
    assert search._validate_bundle_for_resume(
        tmp_path, catalog=catalog, seal=seal
    ) == {"pages": 1, "checkpoints": 0}
    with pytest.raises(search.ContractError) as caught:
        search.validate_bundle(
            tmp_path, catalog=catalog, seal=seal, _allow_nonproduction=True
        )
    assert caught.value.code == "bundle_lifecycle"


def test_preflight_wal_nonprefix_row_is_rejected_before_resume_send(
    catalog, seal, tmp_path
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    request = search.materialize_request(row)
    body = _openalex_body(count=0, oql=row["expected_interpreted_query"])
    response = search.TransportResponse(
        status=200,
        entity_body=body,
        headers=(),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    evidence = search.capture_page_evidence(
        stream_id=row["stream_id"],
        pass_number=0,
        page_number=0,
        request=request,
        response=response,
        required_response_fields=row["required_response_fields"],
    )
    writer = search.BundleWriter(
        tmp_path,
        kind="preflight",
        seal=seal,
        phase_argv=search.validate_effective_phase_argv(SEALED_ARGV, "preflight"),
        defer_manifest_fold=True,
    )
    writer.begin_attempt(
        request=request,
        pass_number=0,
        page_number=0,
        expected_wire_attempt_count=1,
        intent_at=_fixed_clock(),
    )
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence,
        entity_body=body,
        checkpoint=None,
    )
    with pytest.raises(search.ContractError) as caught:
        search._validate_preflight_wal_attempt_sequence(catalog, [evidence])
    assert caught.value.code == "bundle_preflight_sequence"


def test_finalized_preflight_report_deletion_is_rejected(
    catalog, seal, finalized_one_attempt_preflight
):
    bundle = finalized_one_attempt_preflight
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["lifecycle"] == "finalized"
    (bundle / manifest["preflight_report"]["path"]).unlink()
    with pytest.raises(search.ContractError) as caught:
        search.validate_bundle(
            bundle, catalog=catalog, seal=seal, _allow_nonproduction=True
        )
    assert caught.value.code == "bundle_preflight"


def test_finalized_run_result_deletion_is_rejected(
    catalog, seal, tmp_path
):
    parent_digest = _sha(b"parent-preflight-manifest")
    phase_argv = search.validate_effective_phase_argv(RUN_ARGV, "run-ready")
    writer = search.BundleWriter(
        tmp_path,
        kind="final",
        seal=seal,
        phase_argv=phase_argv,
        parent_preflight_manifest_sha256=parent_digest,
        defer_manifest_fold=True,
    )
    writer.finalize_run({"axis_complete": False})
    manifest = search._read_bundle_manifest(tmp_path)[0]
    (tmp_path / manifest["run_result"]["path"]).unlink()
    with pytest.raises(search.ContractError) as caught:
        search.validate_bundle(
            tmp_path,
            catalog=catalog,
            seal=seal,
            _allow_nonproduction=True,
        )
    assert caught.value.code == "bundle_run"


def test_simulation_bundle_is_rejected_by_production_acceptance(
    catalog, seal, finalized_one_attempt_preflight
):
    bundle = finalized_one_attempt_preflight
    with pytest.raises(search.ContractError) as caught:
        search.load_preflight_bundle(bundle, catalog, seal)
    assert caught.value.code == "bundle_nonproduction"


def test_production_phase_rejects_simulation_transport_before_send(
    catalog, catalog_data, seal
):
    transport = search.ScriptedTransport([])
    with pytest.raises(search.ContractError) as caught:
        search.run_preflight(
            catalog,
            catalog_data,
            seal,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=transport,
            clock=_fixed_clock,
            effective_argv=LIVE_PREFLIGHT_ARGV,
        )
    assert caught.value.code == "bundle_phase_argv"
    assert transport.calls == []


def test_runtime_loaded_module_drift_does_not_stale_registration(
    catalog_data, seal, tmp_path
):
    module = search.sys.modules["json"]
    original_file = module.__file__
    drift = tmp_path / "json.py"
    drift.write_bytes(Path(original_file).read_bytes() + b"\n# runtime drift\n")
    module.__file__ = str(drift)
    try:
        search.validate_registration_seal(
            seal,
            catalog_data,
            argv=SEALED_ARGV,
            commit=COMMIT,
            enforce_head=False,
        )
    finally:
        module.__file__ = original_file


def test_runtime_loaded_stdlib_submodule_drift_does_not_stale_registration(
    catalog_data, seal, tmp_path
):
    module = search.sys.modules["json.decoder"]
    original_file = module.__file__
    drift = tmp_path / "decoder.py"
    drift.write_bytes(Path(original_file).read_bytes() + b"\n# submodule drift\n")
    module.__file__ = str(drift)
    try:
        search.validate_registration_seal(
            seal,
            catalog_data,
            argv=SEALED_ARGV,
            commit=COMMIT,
            enforce_head=False,
        )
    finally:
        module.__file__ = original_file


@pytest.mark.parametrize(
    "effective_argv",
    [
        (
            "python3",
            "tools/run_axis3_search.py",
            "preflight",
            "--live",
            "--responses",
            "fixture.json",
        ),
        (
            "python3",
            "tools/run_axis3_search.py",
            "run-ready",
            "--live",
            "--unknown-semantic-option",
            "value",
        ),
        (
            "python3",
            "tools/run_axis3_search.py",
            "resume",
            "--live",
            "--timeout-seconds",
            "30",
            "--timeout-seconds",
            "30",
        ),
    ],
    ids=["dual-transport", "unknown-option", "duplicate-timeout"],
)
def test_phase_semantic_argv_mutations_fail_closed(effective_argv):
    phase = effective_argv[2]
    with pytest.raises(search.ContractError) as caught:
        search.validate_effective_phase_argv(effective_argv, phase)
    assert caught.value.code == "effective_argv"


def test_independent_main_request_oracle_is_exact(catalog):
    oracle = search.extract_frozen_main_request_oracle(
        search.FROZEN_INPUT_PATHS[0].read_bytes()
    )
    assert len(oracle["main_requests"]) == 1893
    search.validate_frozen_registration_closure(
        catalog, search.FROZEN_INPUT_PATHS[0].read_bytes()
    )


def test_preflight_successful_prefix_resumes_without_checkpoint(catalog):
    planned = search._preflight_planned_stream_ids(catalog)
    assert len(planned) == 1929
    prefix = [
        {"stream_id": stream_id, "status": 200}
        for stream_id in planned[:-1]
    ]
    state = search._validate_preflight_wal_attempt_sequence(catalog, prefix)
    assert state["next_initial_stream_id"] == planned[-1]
    assert state["initial_plan_complete"] is False


def test_preflight_wal_accepts_four_transport_attempts_and_rejects_fifth(catalog):
    first = search._preflight_planned_stream_ids(catalog)[0]
    four_attempts = [
        {"stream_id": first, "transport_error": "live_transport"},
        {"stream_id": first, "transport_error": "live_transport"},
        {"stream_id": first, "transport_error": "live_transport"},
        {"stream_id": first, "transport_error": "live_transport"},
    ]
    state = search._validate_preflight_wal_attempt_sequence(
        catalog, four_attempts
    )
    assert state["current_stream_attempts"] == 4
    assert state["retry_stream_id"] is None

    with pytest.raises(search.ContractError) as caught:
        search._validate_preflight_wal_attempt_sequence(
            catalog,
            [
                *four_attempts,
                {"stream_id": first, "transport_error": "live_transport"},
            ],
        )
    assert caught.value.code == "bundle_preflight_sequence"


def test_later_row_retry_does_not_replace_availability_evidence(
    catalog, green_preflight_report
):
    report, _transport = green_preflight_report
    initial = copy.deepcopy(report["preflight_evidence"])
    failure = {
        "stream_id": initial[-1]["stream_id"],
        "request": copy.deepcopy(initial[-1]["request"]),
        "transport_error": "live_transport",
    }
    retry = copy.deepcopy(initial[-1])
    sequence = [*initial[:-1], failure, retry]
    state = search._validate_preflight_wal_attempt_sequence(catalog, sequence)
    assert state["initial_plan_complete"] is True
    assert state["retry_stream_id"] is None
    assert sequence[0] == report["availability_evidence"]
    assert sequence[0]["stream_id"] == (
        "AX3A1-L-ID-01@openalex"
    )


def test_http_failure_cannot_be_followed_by_inline_success(
    catalog, green_preflight_report
):
    report, _transport = green_preflight_report
    initial = copy.deepcopy(report["preflight_evidence"])
    failure = copy.deepcopy(initial[-1])
    failure["status"] = 503
    retry = copy.deepcopy(initial[-1])
    sequence = [*initial[:-1], failure, retry]
    with pytest.raises(search.ContractError) as caught:
        search._validate_preflight_wal_attempt_sequence(catalog, sequence)
    assert caught.value.code == "bundle_preflight_sequence"
    assert sequence[0] == report["availability_evidence"]
    assert sequence[0]["stream_id"] == (
        "AX3A1-L-ID-01@openalex"
    )


def test_final_retryable_tail_remains_nonfinalizable():
    eligibility = search._derive_finalize_eligibility(
        kind="final",
        ledger=[{"stream_id": "AX3A1-Q01@openalex", "status": 503}],
        attempt_intent=None,
        wire_attempt_count=1,
    )
    assert eligibility["finalize_eligible"] is False
    assert eligibility["reason"] == "retryable_http_503"


def test_resume_pacing_intervals_are_unmeasured_null(catalog):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(row)
    observations = search._pacing_observations_from_intents(
        [
            {"request": request, "intent_at": "2026-08-28T00:00:00Z"},
            {"request": request, "intent_at": "2026-08-28T00:00:10Z"},
        ]
    )
    assert [
        observation["observed_interval_seconds"]
        for observation in observations
    ] == [None, None]


def test_cooldown_and_missing_limiter_state_survive_new_instance(
    catalog, seal, tmp_path
):
    fake_time = _FakeTime()
    cooldown_state = tmp_path / "cooldown" / "host-limiter.json"
    limiter = search.HostLimiter(
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
        state_path=cooldown_state,
    )
    limiter.acquire("dblp.org", 45.0)
    issued_at, _observed = limiter.issue("dblp.org")
    limiter.finish_issue("dblp.org", issued_at)
    limiter.enter_cooldown("dblp.org", 45.0, 2700.0)

    resumed_limiter = search.HostLimiter(
        clock=fake_time.clock,
        sleeper=fake_time.sleep,
        state_path=cooldown_state,
    )
    resumed_limiter.acquire("dblp.org", 45.0)
    resumed_limiter.release()
    assert fake_time.sleeps == [2700.0]

    bundle = tmp_path / "missing-state-bundle"
    writer, response, evidence = _packed_preflight_attempt(
        catalog, seal, bundle
    )
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence,
        entity_body=response.entity_body,
        checkpoint=None,
    )
    manifest = search._read_bundle_manifest(bundle)[0]
    missing_state = bundle / "state" / "host-limiter.json"
    assert not missing_state.exists()
    fallback = search._preflight_resume_limiter_fallback(bundle, manifest)
    resumed_time = _FakeTime()
    recovered_limiter = search.HostLimiter(
        clock=resumed_time.clock,
        sleeper=resumed_time.sleep,
        state_path=missing_state,
        fallback_last_issued=fallback,
    )
    recovered_limiter.acquire("api.openalex.org", 1.0)
    recovered_limiter.release()
    assert resumed_time.sleeps == [1.0]


def test_packed_wal_commits_transport_failure_without_pending_intent(
    catalog, seal, tmp_path
):
    writer, response, evidence = _packed_preflight_attempt(
        catalog, seal, tmp_path
    )
    writer.materialize_pending_attempt()
    writer.commit_transport_failure("live_transport")
    replayed = search._replay_preflight_wal(
        tmp_path, writer._journal_descriptor(sealed=False)
    )
    assert replayed["attempt_intent"] is None
    assert replayed["attempt_outcomes"] == [
        {
            "stream_id": "AX3A1-L-ID-01@openalex",
            "request": replayed["attempt_intents"][0]["request"],
            "transport_error": "live_transport",
        }
    ]
    assert replayed["descriptor"]["record_count"] == 2
    writer.begin_attempt(
        request=evidence["request"],
        pass_number=0,
        page_number=0,
        expected_wire_attempt_count=2,
        intent_at=_fixed_clock() + timedelta(seconds=3),
    )
    writer.record_raw_response(response)
    writer.commit_response(
        evidence=evidence,
        entity_body=response.entity_body,
        checkpoint=None,
    )
    replayed = search._replay_preflight_wal(
        tmp_path, writer._journal_descriptor(sealed=False)
    )
    assert len(replayed["attempt_outcomes"]) == 2
    assert replayed["committed_intents"][0]["expected_wire_attempt_count"] == 2
    assert replayed["ledger"][0]["raw_response_path"] == (
        "attempts/000002.response.json"
    )


def test_non_200_parseable_body_preserves_observed_locators():
    body = _openalex_body(
        count=1, work_id="https://openalex.org/W260424658"
    )
    observed = search.observed_response_locators("openalex", body, 503)
    assert "/meta/count" in observed
    assert "/results/0/id" in observed
    assert search.observed_response_locators(
        "openalex", b"unparseable response", 503
    ) == []


def test_mutation_mu1_live_http_transport_subclass_is_rejected():
    class DerivedLiveHTTPTransport(search.LiveHTTPTransport):
        pass

    with pytest.raises(search.ContractError) as caught:
        search._validate_production_transport_identity(
            DerivedLiveHTTPTransport()
        )
    assert caught.value.code == "production_transport_identity"


def test_mutation_mu5_dirty_head_blob_is_rejected_directly(tmp_path):
    git_dir = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=search.REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    repo = tmp_path / "closure-repo"
    candidate = repo / "orchestrator" / "related_work_search.py"
    candidate.parent.mkdir(parents=True)
    (repo / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
    head_bytes = subprocess.run(
        ["git", "show", "HEAD:orchestrator/related_work_search.py"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    candidate.write_bytes(head_bytes)
    search._verify_head_closure([candidate], repo)
    candidate.write_bytes(head_bytes + b"\n# one-byte-class drift\n")
    with pytest.raises(search.ContractError) as caught:
        search._verify_head_closure([candidate], repo)
    assert caught.value.code == "head_closure_dirty"


def test_mutation_mu6a_normal_producer_missing_independent_request_is_rejected(
    catalog, seal
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=200,
        entity_body=_openalex_body(
            count=0, oql=row["expected_interpreted_query"]
        ),
        headers=(),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="application/json",
        response_received_at="2026-08-28T00:00:00Z",
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._response_checkpoint(
        row=row,
        request=request,
        response=response,
        seal=seal,
        budget=budget,
        now=_fixed_clock(),
        run_id="axis3-run-ready",
        pass_number=1,
        page_number=0,
        next_request=None,
    )
    checkpoint.pop("start_independent_pass_request")
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(checkpoint)
    assert caught.value.code == "schema_validation"


def test_mutation_mu6b_quota_producer_missing_cursor_request_is_rejected(
    catalog, seal
):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-L-ID-01@openalex"
    )
    request = search.materialize_request(row)
    response = search.TransportResponse(
        status=429,
        entity_body=b"quota",
        headers=(("Retry-After", "60"),),
        endpoint=search.OPENALEX_ENDPOINT,
        final_url=request["url"],
        content_type="text/plain",
        response_received_at="2026-08-28T00:00:00Z",
    )
    budget = search.WireBudget()
    budget.consume(_fixed_clock())
    checkpoint = search._quota_checkpoint(
        row=row,
        request=request,
        response=response,
        seal=seal,
        budget=budget,
        now=_fixed_clock(),
    )
    checkpoint.pop("continue_cursor_request")
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(checkpoint)
    assert caught.value.code == "schema_validation"


def test_mutation_mu8_amendment_bytes_match_literal_without_seal_fixture():
    data = search.FROZEN_INPUT_PATHS[1].read_bytes()
    search._validate_frozen_amendment_bytes(data)
    mutant = bytearray(data)
    mutant[-1] ^= 1
    with pytest.raises(search.ContractError) as caught:
        search._validate_frozen_amendment_bytes(bytes(mutant))
    assert caught.value.code == "frozen_input_stale"


def test_frozen_closure_rejects_missing_amendment_bytes(tmp_path):
    preregistration = (
        tmp_path
        / "docs/related-work/claim-survey/"
        / "2026-08-27-axis3-search-preregistration.md"
    )
    amendment = preregistration.with_name(
        "2026-09-01-axis3-search-amendment.md"
    )
    preregistration.parent.mkdir(parents=True)
    preregistration.write_bytes(search.FROZEN_INPUT_PATHS[0].read_bytes())
    with pytest.raises(search.ContractError) as caught:
        search._frozen_input_digest_entries(
            [preregistration, amendment], tmp_path
        )
    assert caught.value.code == "seal_path"


def test_mutation_m4_cursor_request_in_independent_pass_arm_is_rejected():
    checkpoint = _checkpoint_common(
        resume_action="continue_cursor",
        pass_kind="cursor_traversal",
        continue_cursor_request=_resume_request("cursor"),
        cursor_source={
            "page_number": 0,
            "entity_body_path": "responses/s/pass-1/page-0.body",
            "entity_body_sha256": _sha(b"page"),
            "field_locator": "/meta/next_cursor",
        },
        start_independent_pass_request=_resume_request(
            "cursor_star", cursor="next"
        ),
    )
    with pytest.raises(search.ContractError) as caught:
        search.validate_checkpoint(checkpoint)
    assert caught.value.code == "checkpoint_action"


def test_bundle_first_pass_must_be_one(catalog):
    row = next(
        item
        for item in catalog["rows"]
        if item["stream_id"] == "AX3A1-Q01@openalex"
    )
    with pytest.raises(search.ContractError) as caught:
        search._derive_latest_stream_result(
            row, [({"pass_number": 99}, b"", {})]
        )
    assert caught.value.code == "bundle_page_progress"


def test_finalized_resume_keeps_axis_incomplete_separate_from_lifecycle(
    tmp_path
):
    result_bytes = search._canonical_json({"axis_complete": False})
    digest = _sha(result_bytes)
    relative = f"results/run-{digest}.json"
    (tmp_path / "results").mkdir()
    (tmp_path / relative).write_bytes(result_bytes)
    resumed = search._finalized_run_resume_status(
        tmp_path,
        {"path": relative, "sha256": digest},
        search.validate_effective_phase_argv(RESUME_ARGV, "resume"),
    )
    assert resumed["lifecycle_complete"] is True
    assert resumed["axis_complete"] is False
    assert resumed["complete"] is False


def test_production_seal_entrypoints_default_to_head_closure():
    assert inspect.signature(search.build_registration_seal).parameters[
        "enforce_head"
    ].default is True
    assert inspect.signature(search.validate_registration_seal).parameters[
        "enforce_head"
    ].default is True


def test_top_level_simulation_artifact_consumers_reject_without_send(
    catalog,
    catalog_data,
    seal,
    finalized_one_attempt_preflight,
    tmp_path,
):
    preflight_transport = search.ScriptedTransport([])
    with pytest.raises(search.ContractError) as caught:
        search.run_preflight(
            catalog,
            catalog_data,
            seal,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=preflight_transport,
            clock=_fixed_clock,
            bundle_dir=tmp_path / "forbidden-preflight",
            effective_argv=SEALED_ARGV,
        )
    assert caught.value.code == "bundle_nonproduction"
    assert preflight_transport.calls == []

    run_transport = search.ScriptedTransport([])
    with pytest.raises(search.ContractError) as caught:
        search.run_ready(
            catalog,
            catalog_data,
            seal,
            None,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=run_transport,
            preflight_bundle_dir=finalized_one_attempt_preflight,
            bundle_dir=tmp_path / "forbidden-final",
            effective_argv=RUN_ARGV,
        )
    assert caught.value.code == "bundle_nonproduction"
    assert run_transport.calls == []

    resume_transport = search.ScriptedTransport([])
    with pytest.raises(search.ContractError) as caught:
        search.resume_bundle(
            finalized_one_attempt_preflight,
            catalog,
            catalog_data,
            seal,
            argv=SEALED_ARGV,
            commit=COMMIT,
            transport=resume_transport,
            effective_argv=RESUME_ARGV,
        )
    assert caught.value.code == "bundle_nonproduction"
    assert resume_transport.calls == []


def _run() -> int:
    """新規test fileを直接起動しても全nodeをpytestで自己検査する。"""

    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
