from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.axis_b5_search.catalog import (
    _arxiv_expression,
    _openalex_filter,
    _percent_encode,
    _term_id,
    build_catalog_document,
    render_catalog_json,
)


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = (
    ROOT
    / "docs"
    / "related-work"
    / "claim-survey"
    / "2026-09-08-backoff-axis-b5-search-catalog.json"
)
EXPECTED_CATALOG_SHA256 = (
    "7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f"
)

EXPECTED_BLOCKS = (
    (
        "T",
        (
            "transaction processing",
            "database transaction",
            "transactional memory",
            "software transactional memory",
            "STM",
            "concurrency control",
            "optimistic concurrency control",
            "transaction abort",
            "transaction conflict",
            "transaction retry",
            "retry transaction",
            "transaction scheduling",
        ),
    ),
    (
        "M",
        (
            "backoff",
            "back-off",
            "retry delay",
            "retry wait",
            "wait policy",
            "waiting policy",
            "contention manager",
            "contention management",
            "adaptive contention manager",
            "adaptive transaction scheduling",
            "hill climbing",
            "stochastic approximation",
            "finite-difference gradient",
            "gradient sign",
            "simultaneous perturbation stochastic approximation",
            "SPSA",
            "adaptive step size",
            "adaptive gain",
            "variable step size",
        ),
    ),
    (
        "O",
        (
            "backoff time",
            "backoff interval",
            "backoff duration",
            "retry interval",
            "waiting time",
            "wait duration",
            "sleep time",
            "contention window",
            "step size",
            "gain sequence",
        ),
    ),
    (
        "C",
        (
            "update interval",
            "update period",
            "evaluation interval",
            "evaluation period",
            "measurement interval",
            "measurement window",
            "observation interval",
            "observation window",
            "sampling interval",
            "sampling period",
            "sampling window",
            "control interval",
            "adaptation interval",
            "adaptive window",
            "dynamic window",
            "variable window",
            "adaptive update interval",
            "dynamic update interval",
            "online window selection",
            "runtime window selection",
            "run-time window selection",
        ),
    ),
    (
        "W",
        (
            "samples per window",
            "sample count",
            "sample size",
            "estimation error",
            "gradient variance",
            "variance estimate",
            "confidence interval",
            "abort rate",
            "conflict rate",
            "commit rate",
            "throughput",
            "contention level",
            "workload",
        ),
    ),
    (
        "V",
        (
            "serializability",
            "opacity",
            "linearizability",
            "correctness",
            "safety",
            "invariant",
            "verification",
            "proof",
            "progress guarantee",
            "liveness",
        ),
    ),
)

EXPECTED_TERM_IDS = (
    (
        "T",
        ("T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12"),
    ),
    (
        "M",
        (
            "M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M09", "M10",
            "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18", "M19",
        ),
    ),
    ("O", ("O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09", "O10")),
    (
        "C",
        (
            "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10",
            "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21",
        ),
    ),
    (
        "W",
        ("W01", "W02", "W03", "W04", "W05", "W06", "W07", "W08", "W09", "W10", "W11", "W12", "W13"),
    ),
    ("V", ("V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09", "V10")),
)

EXPECTED_BRANCHES = (
    ("B5-Q1", ("T", "M", "C")),
    ("B5-Q2", ("T", "O", "C")),
    ("B5-Q3", ("M", "C", "W")),
    ("B5-Q4", ("T", "M")),
    ("B5-Q5", ("T", "C")),
    ("B5-Q6", ("M", "C")),
    ("B5-Q7", ("O", "C")),
    ("B5-Q8", ("C", "W")),
    ("B5-Q9", ("T", "V")),
    ("B5-Q10", ("T", "O")),
)

EXPECTED_ARXIV_Q1_URL = (
    "https://export.arxiv.org/api/query?search_query="
    "%28abs%3A%22transaction%20processing%22%20OR%20abs%3A%22database%20transaction%22%20OR%20abs%3A%22transactional%20memory%22%20OR%20abs%3A%22software%20transactional%20memory%22%20OR%20abs%3A%22STM%22%20OR%20abs%3A%22concurrency%20control%22%20OR%20abs%3A%22optimistic%20concurrency%20control%22%20OR%20abs%3A%22transaction%20abort%22%20OR%20abs%3A%22transaction%20conflict%22%20OR%20abs%3A%22transaction%20retry%22%20OR%20abs%3A%22retry%20transaction%22%20OR%20abs%3A%22transaction%20scheduling%22%29"
    "%20AND%20"
    "%28abs%3A%22backoff%22%20OR%20abs%3A%22back-off%22%20OR%20abs%3A%22retry%20delay%22%20OR%20abs%3A%22retry%20wait%22%20OR%20abs%3A%22wait%20policy%22%20OR%20abs%3A%22waiting%20policy%22%20OR%20abs%3A%22contention%20manager%22%20OR%20abs%3A%22contention%20management%22%20OR%20abs%3A%22adaptive%20contention%20manager%22%20OR%20abs%3A%22adaptive%20transaction%20scheduling%22%20OR%20abs%3A%22hill%20climbing%22%20OR%20abs%3A%22stochastic%20approximation%22%20OR%20abs%3A%22finite-difference%20gradient%22%20OR%20abs%3A%22gradient%20sign%22%20OR%20abs%3A%22simultaneous%20perturbation%20stochastic%20approximation%22%20OR%20abs%3A%22SPSA%22%20OR%20abs%3A%22adaptive%20step%20size%22%20OR%20abs%3A%22adaptive%20gain%22%20OR%20abs%3A%22variable%20step%20size%22%29"
    "%20AND%20"
    "%28abs%3A%22update%20interval%22%20OR%20abs%3A%22update%20period%22%20OR%20abs%3A%22evaluation%20interval%22%20OR%20abs%3A%22evaluation%20period%22%20OR%20abs%3A%22measurement%20interval%22%20OR%20abs%3A%22measurement%20window%22%20OR%20abs%3A%22observation%20interval%22%20OR%20abs%3A%22observation%20window%22%20OR%20abs%3A%22sampling%20interval%22%20OR%20abs%3A%22sampling%20period%22%20OR%20abs%3A%22sampling%20window%22%20OR%20abs%3A%22control%20interval%22%20OR%20abs%3A%22adaptation%20interval%22%20OR%20abs%3A%22adaptive%20window%22%20OR%20abs%3A%22dynamic%20window%22%20OR%20abs%3A%22variable%20window%22%20OR%20abs%3A%22adaptive%20update%20interval%22%20OR%20abs%3A%22dynamic%20update%20interval%22%20OR%20abs%3A%22online%20window%20selection%22%20OR%20abs%3A%22runtime%20window%20selection%22%20OR%20abs%3A%22run-time%20window%20selection%22%29"
    "%20AND%20submittedDate%3A%5B199101010000%20TO%20202612312359%5D"
    "&start=0&max_results=200"
)

EXPECTED_OPENALEX_Q1_URL = (
    "https://api.openalex.org/works?filter=title_and_abstract.search%3A"
    "%28transaction%20processing%20OR%20database%20transaction%20OR%20transactional%20memory%20OR%20software%20transactional%20memory%20OR%20STM%20OR%20concurrency%20control%20OR%20optimistic%20concurrency%20control%20OR%20transaction%20abort%20OR%20transaction%20conflict%20OR%20transaction%20retry%20OR%20retry%20transaction%20OR%20transaction%20scheduling%29"
    "%20AND%20"
    "%28backoff%20OR%20back-off%20OR%20retry%20delay%20OR%20retry%20wait%20OR%20wait%20policy%20OR%20waiting%20policy%20OR%20contention%20manager%20OR%20contention%20management%20OR%20adaptive%20contention%20manager%20OR%20adaptive%20transaction%20scheduling%20OR%20hill%20climbing%20OR%20stochastic%20approximation%20OR%20finite-difference%20gradient%20OR%20gradient%20sign%20OR%20simultaneous%20perturbation%20stochastic%20approximation%20OR%20SPSA%20OR%20adaptive%20step%20size%20OR%20adaptive%20gain%20OR%20variable%20step%20size%29"
    "%20AND%20"
    "%28update%20interval%20OR%20update%20period%20OR%20evaluation%20interval%20OR%20evaluation%20period%20OR%20measurement%20interval%20OR%20measurement%20window%20OR%20observation%20interval%20OR%20observation%20window%20OR%20sampling%20interval%20OR%20sampling%20period%20OR%20sampling%20window%20OR%20control%20interval%20OR%20adaptation%20interval%20OR%20adaptive%20window%20OR%20dynamic%20window%20OR%20variable%20window%20OR%20adaptive%20update%20interval%20OR%20dynamic%20update%20interval%20OR%20online%20window%20selection%20OR%20runtime%20window%20selection%20OR%20run-time%20window%20selection%29"
    ",to_publication_date%3A2026-12-31&per-page=200&cursor=*"
)

EXPECTED_DBLP_Q10_URL = (
    "https://dblp.org/search/publ/api?"
    "q=transaction%20processing%20backoff%20time&format=json&h=100&f=0"
)

EXPECTED_CONTROL_IDS = (
    "B5-CTL-X@arxiv",
    "B5-CTL-Y@arxiv",
    "B5-CTL-OR@arxiv",
    "B5-CTL-AND@arxiv",
    "B5-CTL-AND2023@arxiv",
    "B5-CTL-X@openalex",
    "B5-CTL-Y@openalex",
    "B5-CTL-OR@openalex",
    "B5-CTL-AND@openalex",
    "B5-CTL-AND2023@openalex",
    "B5-CTL-X@dblp",
    "B5-CTL-Y@dblp",
    "B5-CTL-AND@dblp",
    "B5-CTL-AND2023@dblp",
)

EXPECTED_CONTROL_GROUPS = {
    "B5-CTL-X@arxiv": [["M01"]],
    "B5-CTL-Y@arxiv": [["C01"]],
    "B5-CTL-OR@arxiv": [["M01", "C01"]],
    "B5-CTL-AND@arxiv": [["M01"], ["C01"]],
    "B5-CTL-AND2023@arxiv": [["M01"], ["C01"]],
    "B5-CTL-X@openalex": [["M01"]],
    "B5-CTL-Y@openalex": [["C01"]],
    "B5-CTL-OR@openalex": [["M01", "C01"]],
    "B5-CTL-AND@openalex": [["M01"], ["C01"]],
    "B5-CTL-AND2023@openalex": [["M01"], ["C01"]],
    "B5-CTL-X@dblp": [["M01"]],
    "B5-CTL-Y@dblp": [["C01"]],
    "B5-CTL-AND@dblp": [["M01"], ["C01"]],
    "B5-CTL-AND2023@dblp": [["M01"], ["C01"]],
}

EXPECTED_CONTROL_URLS = {
    "B5-CTL-X@arxiv": "https://export.arxiv.org/api/query?search_query=%28abs%3A%22backoff%22%29%20AND%20submittedDate%3A%5B199101010000%20TO%20202612312359%5D&start=0&max_results=200",
    "B5-CTL-Y@arxiv": "https://export.arxiv.org/api/query?search_query=%28abs%3A%22update%20interval%22%29%20AND%20submittedDate%3A%5B199101010000%20TO%20202612312359%5D&start=0&max_results=200",
    "B5-CTL-OR@arxiv": "https://export.arxiv.org/api/query?search_query=%28abs%3A%22backoff%22%20OR%20abs%3A%22update%20interval%22%29%20AND%20submittedDate%3A%5B199101010000%20TO%20202612312359%5D&start=0&max_results=200",
    "B5-CTL-AND@arxiv": "https://export.arxiv.org/api/query?search_query=%28abs%3A%22backoff%22%29%20AND%20%28abs%3A%22update%20interval%22%29%20AND%20submittedDate%3A%5B199101010000%20TO%20202612312359%5D&start=0&max_results=200",
    "B5-CTL-AND2023@arxiv": "https://export.arxiv.org/api/query?search_query=%28abs%3A%22backoff%22%29%20AND%20%28abs%3A%22update%20interval%22%29%20AND%20submittedDate%3A%5B199101010000%20TO%20202312312359%5D&start=0&max_results=200",
    "B5-CTL-X@openalex": "https://api.openalex.org/works?filter=title_and_abstract.search%3A%28backoff%29,to_publication_date%3A2026-12-31&per-page=200&cursor=*",
    "B5-CTL-Y@openalex": "https://api.openalex.org/works?filter=title_and_abstract.search%3A%28update%20interval%29,to_publication_date%3A2026-12-31&per-page=200&cursor=*",
    "B5-CTL-OR@openalex": "https://api.openalex.org/works?filter=title_and_abstract.search%3A%28backoff%20OR%20update%20interval%29,to_publication_date%3A2026-12-31&per-page=200&cursor=*",
    "B5-CTL-AND@openalex": "https://api.openalex.org/works?filter=title_and_abstract.search%3A%28backoff%29%20AND%20%28update%20interval%29,to_publication_date%3A2026-12-31&per-page=200&cursor=*",
    "B5-CTL-AND2023@openalex": "https://api.openalex.org/works?filter=title_and_abstract.search%3A%28backoff%29%20AND%20%28update%20interval%29,to_publication_date%3A2023-12-31&per-page=200&cursor=*",
    "B5-CTL-X@dblp": "https://dblp.org/search/publ/api?q=backoff&format=json&h=100&f=0",
    "B5-CTL-Y@dblp": "https://dblp.org/search/publ/api?q=update%20interval&format=json&h=100&f=0",
    "B5-CTL-AND@dblp": "https://dblp.org/search/publ/api?q=backoff%20update%20interval&format=json&h=100&f=0",
    "B5-CTL-AND2023@dblp": "https://dblp.org/search/publ/api?q=backoff%20update%20interval&format=json&h=100&f=0",
}


def _query(doc: dict, query_id: str) -> dict:
    return next(item for item in doc["queries"] if item["query_id"] == query_id)


def _expected_template(index: str, first_page_url: str) -> str:
    if index == "arxiv":
        return first_page_url.replace("&start=0&max_results=200", "&start={POS}&max_results=200")
    if index == "openalex":
        return first_page_url.replace("&cursor=*", "&cursor={CUR}")
    return first_page_url.replace("&f=0", "&f={POS}")


def test_catalog_metadata_and_field_surface_match_contract() -> None:
    doc = build_catalog_document()
    assert set(doc) == {
        "schema_version",
        "registration_path",
        "registration_blob",
        "closure_preregistration_path",
        "cutoff",
        "blocks",
        "branches",
        "queries",
        "controls",
        "aux_venue_streams",
        "expected_cardinalities",
    }
    assert doc["schema_version"] == "izanagi-axis-b5-search-catalog/v1"
    assert doc["registration_path"] == "docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md"
    assert doc["registration_blob"] == "f7e3190f9ce92345fd4a91caecae8cd6bf7a5666"
    assert doc["closure_preregistration_path"] == "docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md"
    assert doc["cutoff"] == "2026-12-31"
    assert all(set(item) == {"block_id", "terms"} for item in doc["blocks"])
    assert all(set(term) == {"term_id", "term"} for item in doc["blocks"] for term in item["terms"])
    assert all(set(item) == {"branch_id", "block_ids"} for item in doc["branches"])
    assert all(set(item) == {"query_id", "index", "branch_id", "term_groups", "request_template", "first_page_url"} for item in doc["queries"])
    assert all(set(item) == {"control_id", "index", "term_groups", "request_template", "first_page_url", "shares_request_with"} for item in doc["controls"])
    assert all(set(item) == {"stream_id", "index", "venue", "year", "request_template", "first_page_url"} for item in doc["aux_venue_streams"])


def test_blocks_match_frozen_terms_order_counts_and_disjointness() -> None:
    doc = build_catalog_document()
    actual = tuple(
        (item["block_id"], tuple(term["term"] for term in item["terms"]))
        for item in doc["blocks"]
    )
    assert actual == EXPECTED_BLOCKS
    all_terms = [term for _, terms in actual for term in terms]
    assert len(all_terms) == 85
    assert len(set(all_terms)) == 85
    assert [len(terms) for _, terms in actual] == [12, 19, 10, 21, 13, 10]


def test_term_ids_match_frozen_two_digit_literals() -> None:
    assert _term_id("T", 1) == "T01"
    assert _term_id("C", 21) == "C21"
    doc = build_catalog_document()
    actual = tuple(
        (item["block_id"], tuple(term["term_id"] for term in item["terms"]))
        for item in doc["blocks"]
    )
    assert actual == EXPECTED_TERM_IDS


def test_branches_match_frozen_block_order() -> None:
    doc = build_catalog_document()
    actual = tuple(
        (item["branch_id"], tuple(item["block_ids"]))
        for item in doc["branches"]
    )
    assert actual == EXPECTED_BRANCHES


def test_main_query_ids_order_and_cardinalities_are_exact() -> None:
    doc = build_catalog_document()
    queries = doc["queries"]
    term_ids_by_block = dict(EXPECTED_TERM_IDS)
    expected_records = []
    for index in ("arxiv", "openalex"):
        for branch_id, block_ids in EXPECTED_BRANCHES:
            expected_records.append(
                (
                    f"{branch_id}@{index}",
                    branch_id,
                    [list(term_ids_by_block[block_id]) for block_id in block_ids],
                )
            )
    for branch_id, block_ids in EXPECTED_BRANCHES[3:]:
        left_block, right_block = block_ids
        for left_id in term_ids_by_block[left_block]:
            for right_id in term_ids_by_block[right_block]:
                expected_records.append(
                    (
                        f"{branch_id}@dblp/{left_id}-{right_id}",
                        branch_id,
                        [[left_id], [right_id]],
                    )
                )
    expected_counts = {
        "blocks": 6,
        "terms": 85,
        "branches": 10,
        "arxiv_queries": 10,
        "openalex_queries": 10,
        "dblp_queries": 1602,
        "queries": 1622,
        "controls": 14,
        "aux_venue_streams": 272,
    }
    assert doc["expected_cardinalities"] == expected_counts
    assert [item["index"] for item in queries[:10]] == ["arxiv"] * 10
    assert [item["branch_id"] for item in queries[:10]] == [item[0] for item in EXPECTED_BRANCHES]
    assert [item["index"] for item in queries[10:20]] == ["openalex"] * 10
    assert [item["branch_id"] for item in queries[10:20]] == [item[0] for item in EXPECTED_BRANCHES]
    assert all(item["index"] == "dblp" for item in queries[20:])
    assert len({item["query_id"] for item in queries}) == 1622
    assert len(expected_records) == 1622
    assert [item["query_id"] for item in queries] == [item[0] for item in expected_records]
    assert [item["branch_id"] for item in queries] == [item[1] for item in expected_records]
    assert [item["term_groups"] for item in queries] == [item[2] for item in expected_records]


def test_dblp_cartesian_branch_counts_bounds_and_request_bytes_are_exact() -> None:
    doc = build_catalog_document()
    dblp = [item for item in doc["queries"] if item["index"] == "dblp"]
    term_ids_by_block = dict(EXPECTED_TERM_IDS)
    terms_by_block = dict(EXPECTED_BLOCKS)
    expected_records = []
    for branch_id, block_ids in EXPECTED_BRANCHES[3:]:
        left_block, right_block = block_ids
        left_terms = zip(term_ids_by_block[left_block], terms_by_block[left_block])
        right_terms = tuple(
            zip(term_ids_by_block[right_block], terms_by_block[right_block])
        )
        for left_id, left_term in left_terms:
            for right_id, right_term in right_terms:
                encoded_q = f"{left_term} {right_term}".replace(" ", "%20")
                first_page_url = (
                    "https://dblp.org/search/publ/api?"
                    f"q={encoded_q}&format=json&h=100&f=0"
                )
                expected_records.append(
                    (
                        f"{branch_id}@dblp/{left_id}-{right_id}",
                        [[left_id], [right_id]],
                        first_page_url,
                        first_page_url.replace("&f=0", "&f={POS}"),
                    )
                )
    expected_counts = {
        "B5-Q4": 228,
        "B5-Q5": 252,
        "B5-Q6": 399,
        "B5-Q7": 210,
        "B5-Q8": 273,
        "B5-Q9": 120,
        "B5-Q10": 120,
    }
    expected_bounds = {
        "B5-Q4": ("B5-Q4@dblp/T01-M01", "B5-Q4@dblp/T12-M19"),
        "B5-Q5": ("B5-Q5@dblp/T01-C01", "B5-Q5@dblp/T12-C21"),
        "B5-Q6": ("B5-Q6@dblp/M01-C01", "B5-Q6@dblp/M19-C21"),
        "B5-Q7": ("B5-Q7@dblp/O01-C01", "B5-Q7@dblp/O10-C21"),
        "B5-Q8": ("B5-Q8@dblp/C01-W01", "B5-Q8@dblp/C21-W13"),
        "B5-Q9": ("B5-Q9@dblp/T01-V01", "B5-Q9@dblp/T12-V10"),
        "B5-Q10": ("B5-Q10@dblp/T01-O01", "B5-Q10@dblp/T12-O10"),
    }
    for branch_id, count in expected_counts.items():
        branch = [item for item in dblp if item["branch_id"] == branch_id]
        assert len(branch) == count
        assert (branch[0]["query_id"], branch[-1]["query_id"]) == expected_bounds[branch_id]
    assert len(dblp) == 1602
    assert len({item["request_template"].encode("utf-8") for item in dblp}) == 1602
    assert [
        (
            item["query_id"],
            item["term_groups"],
            item["first_page_url"],
            item["request_template"],
        )
        for item in dblp
    ] == expected_records


def test_arxiv_q1_full_url_preserves_frozen_terms_order_quotes_and_cutoff() -> None:
    assert _arxiv_expression(
        (("M01",),), upper_date="2026-12-31"
    ) == '(abs:"backoff") AND submittedDate:[199101010000 TO 202612312359]'
    item = _query(build_catalog_document(), "B5-Q1@arxiv")
    assert item["first_page_url"] == EXPECTED_ARXIV_Q1_URL
    assert item["request_template"] == _expected_template("arxiv", EXPECTED_ARXIV_Q1_URL)
    assert item["term_groups"][0][0] == "T01"
    assert item["term_groups"][1][0] == "M01"
    assert item["term_groups"][2][-1] == "C21"


def test_openalex_q1_full_url_is_unquoted_and_keeps_comma_unencoded() -> None:
    assert _percent_encode("a,b", preserve_comma=True) == "a,b"
    assert _openalex_filter(
        (("M01", "C01"),), upper_date="2026-12-31"
    ) == "title_and_abstract.search:(backoff OR update interval),to_publication_date:2026-12-31"
    doc = build_catalog_document()
    item = _query(doc, "B5-Q1@openalex")
    assert item["first_page_url"] == EXPECTED_OPENALEX_Q1_URL
    assert item["request_template"] == _expected_template("openalex", EXPECTED_OPENALEX_Q1_URL)
    assert "%22" not in item["first_page_url"]
    assert "%29,to_publication_date" in item["first_page_url"]
    assert item["first_page_url"].endswith("&per-page=200&cursor=*")
    cursor_entries = [
        entry
        for entry in doc["queries"] + doc["controls"]
        if entry["index"] == "openalex"
    ]
    assert len(cursor_entries) == 15
    for entry in cursor_entries:
        assert entry["request_template"].endswith("&cursor={CUR}")
        assert entry["first_page_url"].endswith("&cursor=*")
        assert entry["first_page_url"] == entry["request_template"].replace("{CUR}", "*")

    position_entries = [
        entry
        for entry in doc["queries"] + doc["controls"] + doc["aux_venue_streams"]
        if entry["index"] in ("arxiv", "dblp")
    ]
    assert len(position_entries) == 1893
    for entry in position_entries:
        if entry["index"] == "arxiv":
            assert entry["request_template"].endswith("&start={POS}&max_results=200")
            assert entry["first_page_url"].endswith("&start=0&max_results=200")
        else:
            assert entry["request_template"].endswith("&f={POS}")
            assert entry["first_page_url"].endswith("&f=0")
        assert entry["first_page_url"] == entry["request_template"].replace("{POS}", "0")


def test_dblp_q10_frozen_example_is_encoded_once() -> None:
    assert _percent_encode("a b") == "a%20b"
    item = _query(build_catalog_document(), "B5-Q10@dblp/T01-O01")
    assert item["first_page_url"] == EXPECTED_DBLP_Q10_URL
    assert item["request_template"] == _expected_template("dblp", EXPECTED_DBLP_Q10_URL)
    assert item["term_groups"] == [["T01"], ["O01"]]
    assert "+" not in item["first_page_url"]
    assert "%2520" not in item["first_page_url"]


def test_controls_match_frozen_ids_groups_and_all_full_urls() -> None:
    controls = build_catalog_document()["controls"]
    assert tuple(item["control_id"] for item in controls) == EXPECTED_CONTROL_IDS
    assert [item["index"] for item in controls] == ["arxiv"] * 5 + ["openalex"] * 5 + ["dblp"] * 4
    for item in controls:
        control_id = item["control_id"]
        assert item["term_groups"] == EXPECTED_CONTROL_GROUPS[control_id]
        assert item["first_page_url"] == EXPECTED_CONTROL_URLS[control_id]
        assert item["request_template"] == _expected_template(item["index"], EXPECTED_CONTROL_URLS[control_id])


def test_dblp_and2023_shares_exact_request_bytes_only_with_dblp_and() -> None:
    controls = {item["control_id"]: item for item in build_catalog_document()["controls"]}
    regular = controls["B5-CTL-AND@dblp"]
    narrowed = controls["B5-CTL-AND2023@dblp"]
    assert narrowed["request_template"].encode("utf-8") == regular["request_template"].encode("utf-8")
    assert narrowed["first_page_url"].encode("utf-8") == regular["first_page_url"].encode("utf-8")
    assert narrowed["shares_request_with"] == "B5-CTL-AND@dblp"
    assert all(item["shares_request_with"] is None for key, item in controls.items() if key != "B5-CTL-AND2023@dblp")


def test_aux_venue_streams_have_frozen_range_order_ids_and_full_urls() -> None:
    streams = build_catalog_document()["aux_venue_streams"]
    expected_streams = []
    for venue in ("SIGMOD", "PVLDB", "ICDE", "EDBT", "PPoPP", "SPAA", "PODC", "DISC"):
        for year in range(1993, 2027):
            url_prefix = (
                "https://dblp.org/search/publ/api?"
                f"q=venue%3A{venue}%3A%20year%3A{year}%3A&format=json&h=100&f="
            )
            expected_streams.append(
                {
                    "stream_id": f"B5-AUX-VENUE@dblp/{venue}-{year}",
                    "index": "dblp",
                    "venue": venue,
                    "year": year,
                    "request_template": url_prefix + "{POS}",
                    "first_page_url": url_prefix + "0",
                }
            )
    assert len(streams) == 272
    assert [(item["venue"], item["year"]) for item in streams] == [
        (venue, year)
        for venue in ("SIGMOD", "PVLDB", "ICDE", "EDBT", "PPoPP", "SPAA", "PODC", "DISC")
        for year in range(1993, 2027)
    ]
    assert streams == expected_streams
    assert streams[0] == {
        "stream_id": "B5-AUX-VENUE@dblp/SIGMOD-1993",
        "index": "dblp",
        "venue": "SIGMOD",
        "year": 1993,
        "request_template": "https://dblp.org/search/publ/api?q=venue%3ASIGMOD%3A%20year%3A1993%3A&format=json&h=100&f={POS}",
        "first_page_url": "https://dblp.org/search/publ/api?q=venue%3ASIGMOD%3A%20year%3A1993%3A&format=json&h=100&f=0",
    }
    assert streams[-1] == {
        "stream_id": "B5-AUX-VENUE@dblp/DISC-2026",
        "index": "dblp",
        "venue": "DISC",
        "year": 2026,
        "request_template": "https://dblp.org/search/publ/api?q=venue%3ADISC%3A%20year%3A2026%3A&format=json&h=100&f={POS}",
        "first_page_url": "https://dblp.org/search/publ/api?q=venue%3ADISC%3A%20year%3A2026%3A&format=json&h=100&f=0",
    }
    assert len({item["stream_id"] for item in streams}) == 272


def test_render_catalog_json_is_canonical_deterministic_and_one_newline() -> None:
    expected = CATALOG_PATH.read_bytes()
    first = render_catalog_json()
    second = render_catalog_json()
    assert first == second == expected
    assert hashlib.sha256(expected).hexdigest() == EXPECTED_CATALOG_SHA256
    assert hashlib.sha256(first).hexdigest() == EXPECTED_CATALOG_SHA256
    assert first.endswith(b"\n")
    assert not first.endswith(b"\n\n")
    assert first.decode("utf-8").count("\n") > 1


def test_checked_in_catalog_matches_rendered_bytes() -> None:
    assert CATALOG_PATH.read_bytes() == render_catalog_json()


def test_cli_output_writes_exact_rendered_bytes(tmp_path: Path) -> None:
    expected = CATALOG_PATH.read_bytes()
    output = tmp_path / "catalog.json"
    result = subprocess.run(
        [sys.executable, "-m", "orchestrator.axis_b5_search.catalog", "--output", str(output)],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0
    actual = output.read_bytes()
    assert actual == expected
    assert hashlib.sha256(actual).hexdigest() == EXPECTED_CATALOG_SHA256


def test_cli_verify_accepts_exact_and_rejects_one_byte_change(tmp_path: Path) -> None:
    expected = CATALOG_PATH.read_bytes()
    candidate = tmp_path / "catalog.json"
    candidate.write_bytes(expected)
    command = [sys.executable, "-m", "orchestrator.axis_b5_search.catalog", "--verify", str(candidate)]
    exact = subprocess.run(command, cwd=ROOT, check=False)
    assert exact.returncode == 0
    candidate.write_bytes(expected + b"\n")
    changed = subprocess.run(command, cwd=ROOT, check=False)
    assert changed.returncode == 1
    missing = subprocess.run(command[:-1] + [str(tmp_path / "missing.json")], cwd=ROOT, check=False)
    assert missing.returncode == 1


def test_cli_requires_exactly_one_mode(tmp_path: Path) -> None:
    base = [sys.executable, "-m", "orchestrator.axis_b5_search.catalog"]
    neither = subprocess.run(base, cwd=ROOT, check=False, stderr=subprocess.DEVNULL)
    both = subprocess.run(
        base + ["--output", str(tmp_path / "out.json"), "--verify", str(tmp_path / "in.json")],
        cwd=ROOT,
        check=False,
        stderr=subprocess.DEVNULL,
    )
    assert neither.returncode != 0
    assert both.returncode != 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
