"""Generate the frozen Axis B5 literature-search request catalog.

Every input below is transcribed from the frozen preregistrations.  Generation
does not inspect the network, clock, environment, or response counts.
"""

from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
from typing import Any, Iterator, Sequence
from urllib.parse import quote


SCHEMA_VERSION = "izanagi-axis-b5-search-catalog/v1"
REGISTRATION_PATH = (
    "docs/related-work/claim-survey/"
    "2026-09-07-backoff-axis-b5-search-preregistration.md"
)
REGISTRATION_BLOB = "f7e3190f9ce92345fd4a91caecae8cd6bf7a5666"
CLOSURE_PREREGISTRATION_PATH = (
    "docs/related-work/claim-survey/"
    "2026-09-08-backoff-axis-b5-closure-preregistration.md"
)
CUTOFF = "2026-12-31"

ARXIV_ENDPOINT = "https://export.arxiv.org/api/query"
OPENALEX_ENDPOINT = "https://api.openalex.org/works"
DBLP_ENDPOINT = "https://dblp.org/search/publ/api"

BLOCKS: tuple[tuple[str, tuple[str, ...]], ...] = (
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

BRANCHES: tuple[tuple[str, tuple[str, ...]], ...] = (
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

DBLP_BRANCH_IDS = (
    "B5-Q4",
    "B5-Q5",
    "B5-Q6",
    "B5-Q7",
    "B5-Q8",
    "B5-Q9",
    "B5-Q10",
)

VENUES = ("SIGMOD", "PVLDB", "ICDE", "EDBT", "PPoPP", "SPAA", "PODC", "DISC")


def _term_id(block_id: str, position: int) -> str:
    """Return the sole registered spelling of an Axis B5 term ID."""

    return f"{block_id}{position:02d}"


def _terms_for_block(block_id: str) -> tuple[str, ...]:
    for candidate_id, terms in BLOCKS:
        if candidate_id == block_id:
            return terms
    raise KeyError(block_id)


def _term_records(block_id: str) -> tuple[dict[str, str], ...]:
    return tuple(
        {"term_id": _term_id(block_id, position), "term": term}
        for position, term in enumerate(_terms_for_block(block_id), 1)
    )


def _block_term_ids(block_id: str) -> tuple[str, ...]:
    return tuple(record["term_id"] for record in _term_records(block_id))


def _term_text(term_id: str) -> str:
    for block_id, _ in BLOCKS:
        for record in _term_records(block_id):
            if record["term_id"] == term_id:
                return record["term"]
    raise KeyError(term_id)


def _term_groups_for_blocks(block_ids: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(_block_term_ids(block_id) for block_id in block_ids)


def _json_term_groups(term_groups: Sequence[Sequence[str]]) -> list[list[str]]:
    return [list(group) for group in term_groups]


def _percent_encode(value: str, *, preserve_comma: bool = False) -> str:
    safe = "-_.~," if preserve_comma else "-_.~"
    return quote(value, safe=safe, encoding="utf-8", errors="strict")


def _arxiv_expression(
    term_groups: Sequence[Sequence[str]], *, upper_date: str
) -> str:
    groups = (
        "(" + " OR ".join(f'abs:"{_term_text(term_id)}"' for term_id in group) + ")"
        for group in term_groups
    )
    upper = upper_date.replace("-", "") + "2359"
    return (
        " AND ".join(groups)
        + f" AND submittedDate:[199101010000 TO {upper}]"
    )


def _openalex_filter(
    term_groups: Sequence[Sequence[str]], *, upper_date: str
) -> str:
    groups = (
        "(" + " OR ".join(_term_text(term_id) for term_id in group) + ")"
        for group in term_groups
    )
    expression = " AND ".join(groups)
    return (
        f"title_and_abstract.search:{expression},"
        f"to_publication_date:{upper_date}"
    )


def _dblp_q(term_ids: Sequence[str]) -> str:
    raw = " ".join(_term_text(term_id) for term_id in term_ids)
    return _percent_encode(raw)


def _arxiv_urls(
    term_groups: Sequence[Sequence[str]], *, upper_date: str
) -> tuple[str, str]:
    encoded = _percent_encode(
        _arxiv_expression(term_groups, upper_date=upper_date)
    )
    template = (
        f"{ARXIV_ENDPOINT}?search_query={encoded}"
        "&start={POS}&max_results=200"
    )
    return template, template.replace("{POS}", "0")


def _openalex_urls(
    term_groups: Sequence[Sequence[str]], *, upper_date: str
) -> tuple[str, str]:
    encoded = _percent_encode(
        _openalex_filter(term_groups, upper_date=upper_date),
        preserve_comma=True,
    )
    template = (
        f"{OPENALEX_ENDPOINT}?filter={encoded}"
        "&per-page=200&cursor={CUR}"
    )
    return template, template.replace("{CUR}", "*")


def _dblp_urls(encoded_q: str) -> tuple[str, str]:
    """Build DBLP URLs from an already percent-encoded q value."""

    template = f"{DBLP_ENDPOINT}?q={encoded_q}&format=json&h=100&f={{POS}}"
    return template, template.replace("{POS}", "0")


def _query_entry(
    *,
    query_id: str,
    index: str,
    branch_id: str,
    term_groups: Sequence[Sequence[str]],
    urls: tuple[str, str],
) -> dict[str, Any]:
    return {
        "query_id": query_id,
        "index": index,
        "branch_id": branch_id,
        "term_groups": _json_term_groups(term_groups),
        "request_template": urls[0],
        "first_page_url": urls[1],
    }


def _iter_main_queries() -> Iterator[dict[str, Any]]:
    for index in ("arxiv", "openalex"):
        for branch_id, block_ids in BRANCHES:
            term_groups = _term_groups_for_blocks(block_ids)
            urls = (
                _arxiv_urls(term_groups, upper_date=CUTOFF)
                if index == "arxiv"
                else _openalex_urls(term_groups, upper_date=CUTOFF)
            )
            yield _query_entry(
                query_id=f"{branch_id}@{index}",
                index=index,
                branch_id=branch_id,
                term_groups=term_groups,
                urls=urls,
            )

    branch_blocks = dict(BRANCHES)
    for branch_id in DBLP_BRANCH_IDS:
        left_block, right_block = branch_blocks[branch_id]
        for left_id, right_id in product(
            _block_term_ids(left_block), _block_term_ids(right_block)
        ):
            term_groups = ((left_id,), (right_id,))
            yield _query_entry(
                query_id=f"{branch_id}@dblp/{left_id}-{right_id}",
                index="dblp",
                branch_id=branch_id,
                term_groups=term_groups,
                urls=_dblp_urls(_dblp_q((left_id, right_id))),
            )


def _control_entry(
    *,
    control_id: str,
    index: str,
    term_groups: Sequence[Sequence[str]],
    upper_date: str,
    shares_request_with: str | None = None,
) -> dict[str, Any]:
    if index == "arxiv":
        urls = _arxiv_urls(term_groups, upper_date=upper_date)
    elif index == "openalex":
        urls = _openalex_urls(term_groups, upper_date=upper_date)
    elif index == "dblp":
        flat_ids = tuple(term_id for group in term_groups for term_id in group)
        urls = _dblp_urls(_dblp_q(flat_ids))
    else:
        raise ValueError("unknown_index")
    return {
        "control_id": control_id,
        "index": index,
        "term_groups": _json_term_groups(term_groups),
        "request_template": urls[0],
        "first_page_url": urls[1],
        "shares_request_with": shares_request_with,
    }


def _build_controls() -> list[dict[str, Any]]:
    x = _term_id("M", 1)
    y = _term_id("C", 1)
    x_group = ((x,),)
    y_group = ((y,),)
    or_group = ((x, y),)
    and_groups = ((x,), (y,))
    controls: list[dict[str, Any]] = []

    for index in ("arxiv", "openalex"):
        for role, groups, upper_date in (
            ("X", x_group, CUTOFF),
            ("Y", y_group, CUTOFF),
            ("OR", or_group, CUTOFF),
            ("AND", and_groups, CUTOFF),
            ("AND2023", and_groups, "2023-12-31"),
        ):
            controls.append(
                _control_entry(
                    control_id=f"B5-CTL-{role}@{index}",
                    index=index,
                    term_groups=groups,
                    upper_date=upper_date,
                )
            )

    for role, groups in (
        ("X", x_group),
        ("Y", y_group),
        ("AND", and_groups),
        ("AND2023", and_groups),
    ):
        controls.append(
            _control_entry(
                control_id=f"B5-CTL-{role}@dblp",
                index="dblp",
                term_groups=groups,
                upper_date=CUTOFF,
                shares_request_with=(
                    "B5-CTL-AND@dblp" if role == "AND2023" else None
                ),
            )
        )
    return controls


def _build_aux_venue_streams() -> list[dict[str, Any]]:
    streams: list[dict[str, Any]] = []
    for venue in VENUES:
        for year in range(1993, 2027):
            encoded_q = f"venue%3A{venue}%3A%20year%3A{year}%3A"
            request_template, first_page_url = _dblp_urls(encoded_q)
            streams.append(
                {
                    "stream_id": f"B5-AUX-VENUE@dblp/{venue}-{year}",
                    "index": "dblp",
                    "venue": venue,
                    "year": year,
                    "request_template": request_template,
                    "first_page_url": first_page_url,
                }
            )
    return streams


def build_catalog_document() -> dict[str, Any]:
    """Build the complete JSON-serializable frozen catalog."""

    return {
        "schema_version": SCHEMA_VERSION,
        "registration_path": REGISTRATION_PATH,
        "registration_blob": REGISTRATION_BLOB,
        "closure_preregistration_path": CLOSURE_PREREGISTRATION_PATH,
        "cutoff": CUTOFF,
        "blocks": [
            {"block_id": block_id, "terms": list(_term_records(block_id))}
            for block_id, _ in BLOCKS
        ],
        "branches": [
            {"branch_id": branch_id, "block_ids": list(block_ids)}
            for branch_id, block_ids in BRANCHES
        ],
        "queries": list(_iter_main_queries()),
        "controls": _build_controls(),
        "aux_venue_streams": _build_aux_venue_streams(),
        "expected_cardinalities": {
            "blocks": 6,
            "terms": 85,
            "branches": 10,
            "arxiv_queries": 10,
            "openalex_queries": 10,
            "dblp_queries": 1602,
            "queries": 1622,
            "controls": 14,
            "aux_venue_streams": 272,
        },
    }


def render_catalog_json() -> bytes:
    doc = build_catalog_document()
    return (
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _verify(path: Path) -> int:
    try:
        actual = path.read_bytes()
    except OSError:
        return 1
    return 0 if actual == render_catalog_json() else 1


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the frozen Axis B5 catalog")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output", type=Path)
    modes.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)

    if args.output is not None:
        try:
            args.output.write_bytes(render_catalog_json())
        except OSError:
            return 1
        return 0
    return _verify(args.verify)


if __name__ == "__main__":
    raise SystemExit(_main())
