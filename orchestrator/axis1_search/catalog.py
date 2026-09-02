"""Deterministic query catalog for the Axis 1 literature-search retake.

The catalog is deliberately generated from the registered logical matrix.  No
response count, environment variable, wall clock, or network observation is an
input to shard derivation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, TypeAlias
from urllib.parse import quote_plus, urlencode


Index: TypeAlias = Literal["arxiv", "openalex", "dblp"]
LogicalKind: TypeAlias = Literal["aggregate", "leaf", "exclusion"]

REGISTRATION_EPOCH = "AX1-20260902-E1"
REGISTERED_CUTOFF = "2026-12-31"
CATALOG_SCHEMA_VERSION = "izanagi-axis1-search-catalog/v1"


@dataclass(frozen=True)
class RequestSpec:
    request_id: str
    leaf_query_id: str
    logical_query_id: str
    index: str
    method: str
    scheme: str
    host: str
    path: str
    query_parameters: tuple[tuple[str, str], ...]
    encoded_url: str
    headers: tuple[tuple[str, str], ...]
    timeout_s: float
    page_number: int
    position_in: str | None
    expected_interpreted_query: str


@dataclass(frozen=True)
class LogicalQuery:
    query_id: str
    kind: str
    index: str
    branch: str
    parent_id: str | None
    shard_lower: str | None
    shard_upper: str | None
    independent_pass_required: bool
    expected_openalex_oqo: Mapping[str, Any] | None
    reference_openalex_oql: str | None


@dataclass(frozen=True)
class Shard:
    shard_id: str
    shard_lower: str | None
    shard_upper: str


@dataclass(frozen=True)
class Catalog:
    schema_version: str
    registration_epoch: str
    outcome_informed: bool
    amendment_path: str
    supersedes: tuple[str, ...]
    cutoff: str
    proof_scope: tuple[str, ...]
    index_policies: Mapping[str, Mapping[str, Any]]
    shard_policies: tuple[Mapping[str, Any], ...]
    logical_queries: tuple[LogicalQuery, ...]
    request_templates: Mapping[str, Mapping[str, Any]]
    controls: tuple[Mapping[str, Any], ...]
    expected_cardinalities: Mapping[str, int]

    def logical_query(self, query_id: str) -> LogicalQuery:
        for query in self.logical_queries:
            if query.query_id == query_id:
                return query
        raise KeyError(query_id)


_TERMS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "T": (
            "concurrency control",
            "transaction processing",
            "serializability",
            "isolation level",
            "two-phase locking",
            "optimistic concurrency control",
            "multi-version concurrency control",
            "snapshot isolation",
            "transactional memory",
            "lock manager",
            "conflict detection",
            "OLTP",
        ),
        "M": (
            "program synthesis",
            "automatic generation",
            "code generation",
            "evolutionary search",
            "genetic programming",
            "large language model",
            "LLM agent",
            "reinforcement learning",
            "learned",
            "auto-tuning",
            "compiler injection",
            "superoptimization",
        ),
        "O": (
            "protocol",
            "algorithm",
            "policy",
            "source code",
            "implementation",
            "intermediate representation",
            "action space",
            "design space",
            "variant",
        ),
        "V": (
            "verifier",
            "model checking",
            "anomaly detection",
            "serializability checking",
            "invariant",
            "proof",
            "correctness oracle",
        ),
        "W": (
            "workload",
            "benchmark",
            "YCSB",
            "TPC-C",
            "contention",
            "read-write ratio",
            "skew",
            "many-core",
        ),
    }
)

_BRANCH_BLOCKS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "Q1": ("T", "M", "O"),
        "Q2": ("T", "M"),
        "Q3": ("T", "O"),
        "Q4": ("T", "V"),
        "Q5": ("T", "W"),
        "Q6": ("M", "O", "W"),
    }
)

_DBLP_TERMS: Mapping[str, str] = MappingProxyType(
    {f"T{ordinal:02d}": term for ordinal, term in enumerate(_TERMS["T"], 1)}
)

_INDEX_POLICIES: Mapping[str, Mapping[str, Any]] = MappingProxyType(
    {
        "arxiv": MappingProxyType(
            {
                "endpoint": "https://export.arxiv.org/api/query",
                "scheme": "https",
                "host": "export.arxiv.org",
                "path": "/api/query",
                "method": "GET",
                "page_size": 200,
                "pagination_kind": "offset",
                "initial_position": "0",
                "minimum_interval_s": 3.0,
                "timeout_s": 60.0,
                "retry_delays_s": [3.0, 6.0, 12.0],
                "response_byte_limit": 16_777_216,
                "content_types": ["application/atom+xml", "application/xml", "text/xml"],
                "id_extractor": "feed.entry.id",
                "total_field": "opensearch:totalResults",
                "capacity_field": "opensearch:itemsPerPage",
            }
        ),
        "openalex": MappingProxyType(
            {
                "endpoint": "https://api.openalex.org/works",
                "scheme": "https",
                "host": "api.openalex.org",
                "path": "/works",
                "method": "GET",
                "page_size": 200,
                "pagination_kind": "cursor",
                "initial_position": "*",
                "minimum_interval_s": 1.0,
                "timeout_s": 60.0,
                "retry_delays_s": [3.0, 6.0, 12.0],
                "response_byte_limit": 16_777_216,
                "content_types": ["application/json"],
                "id_extractor": "results[].id",
                "total_field": "meta.count",
                "capacity_field": "meta.per_page",
                "quota_credit_reserve": 30,
            }
        ),
        "dblp": MappingProxyType(
            {
                "endpoint": "https://dblp.org/search/publ/api",
                "scheme": "https",
                "host": "dblp.org",
                "path": "/search/publ/api",
                "method": "GET",
                "page_size": 100,
                "pagination_kind": "offset",
                "initial_position": "0",
                "minimum_interval_s": 45.0,
                "timeout_s": 60.0,
                "retry_delays_s": [3.0, 6.0, 12.0],
                "response_byte_limit": 16_777_216,
                "content_types": ["application/json"],
                "id_extractor": "result.hits.hit[].info.key",
                "total_field": "result.hits.@total",
                "capacity_field": "result.hits.@sent",
                "cooldown_after_exhaustion_s": 2700,
            }
        ),
    }
)


def _validate_cutoff(cutoff: str) -> date:
    try:
        parsed = date.fromisoformat(cutoff)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_cutoff") from exc
    if cutoff != REGISTERED_CUTOFF or parsed != date(2026, 12, 31):
        raise ValueError("unregistered_cutoff")
    return parsed


def derive_fixed_shards(index: str, branch: str, cutoff: str) -> tuple[Shard, ...]:
    """Derive the registered calendar grid without observing result counts."""

    _validate_cutoff(cutoff)
    if index == "arxiv" and branch == "Q6":
        shards: list[Shard] = []
        for year in range(1991, 2015):
            shards.append(Shard(f"SY{year}", f"{year}-01-01", f"{year}-12-31"))
        for year in range(2015, 2027):
            for month in range(1, 13):
                if month == 12:
                    upper = date(year, 12, 31)
                else:
                    upper = date(year, month + 1, 1) - timedelta(days=1)
                shards.append(
                    Shard(
                        f"SM{year}{month:02d}",
                        f"{year}-{month:02d}-01",
                        upper.isoformat(),
                    )
                )
        return tuple(shards)
    if index == "openalex" and branch in {"Q3", "Q6"}:
        return (
            Shard("SPRE1991", None, "1990-12-31"),
            *(
                Shard(f"SY{year}", f"{year}-01-01", f"{year}-12-31")
                for year in range(1991, 2027)
            ),
        )
    return ()


def derive_expected_logical_ids(cutoff: str) -> tuple[str, ...]:
    """Independently rederive the complete logical-ID set.

    This function intentionally does not call ``derive_fixed_shards`` and does
    not read the catalog JSON, so a catalog omission cannot erase its own oracle.
    """

    _validate_cutoff(cutoff)
    ids: list[str] = []

    ids.extend(f"{REGISTRATION_EPOCH}-Q{number}@arxiv" for number in range(1, 6))
    ids.append(f"{REGISTRATION_EPOCH}-Q6@arxiv")
    ids.extend(
        f"{REGISTRATION_EPOCH}-Q6-SY{year}@arxiv" for year in range(1991, 2015)
    )
    ids.extend(
        f"{REGISTRATION_EPOCH}-Q6-SM{year}{month:02d}@arxiv"
        for year in range(2015, 2027)
        for month in range(1, 13)
    )

    for branch in ("Q1", "Q2", "Q4", "Q5"):
        ids.append(f"{REGISTRATION_EPOCH}-{branch}@openalex")
    for branch in ("Q3", "Q6"):
        ids.append(f"{REGISTRATION_EPOCH}-{branch}@openalex")
        ids.append(f"{REGISTRATION_EPOCH}-{branch}-SPRE1991@openalex")
        ids.extend(
            f"{REGISTRATION_EPOCH}-{branch}-SY{year}@openalex"
            for year in range(1991, 2027)
        )

    ids.extend(
        f"{REGISTRATION_EPOCH}-T{ordinal:02d}@dblp" for ordinal in range(1, 13)
    )
    ids.append(f"{REGISTRATION_EPOCH}-Q6-EXCLUSION@dblp")
    return tuple(sorted(ids))


def _independent_pass_required(index: str, branch: str, kind: str) -> bool:
    return kind in {"aggregate", "leaf"} and (
        (index == "arxiv" and branch == "Q6")
        or (index == "openalex" and branch in {"Q3", "Q6"})
    )


def _openalex_expected_oqo(
    branch: str, shard_lower: str | None, shard_upper: str | None
) -> dict[str, Any]:
    if shard_upper is None:
        raise ValueError("openalex_leaf_missing_upper_bound")
    filter_rows: list[dict[str, Any]] = []
    if shard_lower is not None:
        filter_rows.append(
            {"column_id": "from_publication_date", "value": shard_lower}
        )
    filter_rows.append(
        {"column_id": "to_publication_date", "value": shard_upper}
    )
    filter_rows.extend(
        {
            "join": "or",
            "filters": [
                {
                    "column_id": "title_and_abstract.search",
                    "value": json.dumps(term, ensure_ascii=False),
                    "operator": "has",
                }
                for term in _TERMS[block]
            ],
        }
        for block in _BRANCH_BLOCKS[branch]
    )
    return {"get_rows": "works", "filter_rows": filter_rows}


def _openalex_reference_oql(
    branch: str, shard_lower: str | None, shard_upper: str | None
) -> str:
    logical = " and ".join(
        "(" + " or ".join(f'stemmed "{term}"' for term in _TERMS[block]) + ")"
        for block in _BRANCH_BLOCKS[branch]
    )
    date_parts: list[str] = []
    if shard_lower is not None:
        date_parts.append(f"date >= ({shard_lower})")
    if shard_upper is None:
        raise ValueError("openalex_leaf_missing_upper_bound")
    date_parts.append(f"date <= ({shard_upper})")
    return f"works where {' and '.join(date_parts)} and title/abstract has ({logical})"


def _make_logical_query(
    query_id: str,
    kind: str,
    index: str,
    branch: str,
    parent_id: str | None,
    shard_lower: str | None,
    shard_upper: str | None,
) -> LogicalQuery:
    is_openalex_leaf = index == "openalex" and kind == "leaf"
    return LogicalQuery(
        query_id=query_id,
        kind=kind,
        index=index,
        branch=branch,
        parent_id=parent_id,
        shard_lower=shard_lower,
        shard_upper=shard_upper,
        independent_pass_required=_independent_pass_required(index, branch, kind),
        expected_openalex_oqo=(
            _openalex_expected_oqo(branch, shard_lower, shard_upper)
            if is_openalex_leaf
            else None
        ),
        reference_openalex_oql=(
            _openalex_reference_oql(branch, shard_lower, shard_upper)
            if is_openalex_leaf
            else None
        ),
    )


def _logical_queries(cutoff: str) -> tuple[LogicalQuery, ...]:
    _validate_cutoff(cutoff)
    queries: list[LogicalQuery] = []
    for branch in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        queries.append(
            _make_logical_query(
                f"{REGISTRATION_EPOCH}-{branch}@arxiv",
                "leaf",
                "arxiv",
                branch,
                None,
                "1991-01-01",
                cutoff,
            )
        )
    arxiv_parent = f"{REGISTRATION_EPOCH}-Q6@arxiv"
    queries.append(
        _make_logical_query(
            arxiv_parent, "aggregate", "arxiv", "Q6", None, None, None
        )
    )
    queries.extend(
        _make_logical_query(
            f"{REGISTRATION_EPOCH}-Q6-{shard.shard_id}@arxiv",
            "leaf",
            "arxiv",
            "Q6",
            arxiv_parent,
            shard.shard_lower,
            shard.shard_upper,
        )
        for shard in derive_fixed_shards("arxiv", "Q6", cutoff)
    )

    for branch in ("Q1", "Q2", "Q4", "Q5"):
        queries.append(
            _make_logical_query(
                f"{REGISTRATION_EPOCH}-{branch}@openalex",
                "leaf",
                "openalex",
                branch,
                None,
                None,
                cutoff,
            )
        )
    for branch in ("Q3", "Q6"):
        parent = f"{REGISTRATION_EPOCH}-{branch}@openalex"
        queries.append(
            _make_logical_query(
                parent, "aggregate", "openalex", branch, None, None, None
            )
        )
        queries.extend(
            _make_logical_query(
                f"{REGISTRATION_EPOCH}-{branch}-{shard.shard_id}@openalex",
                "leaf",
                "openalex",
                branch,
                parent,
                shard.shard_lower,
                shard.shard_upper,
            )
            for shard in derive_fixed_shards("openalex", branch, cutoff)
        )

    queries.extend(
        _make_logical_query(
            f"{REGISTRATION_EPOCH}-T{ordinal:02d}@dblp",
            "leaf",
            "dblp",
            f"T{ordinal:02d}",
            None,
            None,
            cutoff,
        )
        for ordinal in range(1, 13)
    )
    queries.append(
        _make_logical_query(
            f"{REGISTRATION_EPOCH}-Q6-EXCLUSION@dblp",
            "exclusion",
            "dblp",
            "Q6",
            None,
            None,
            cutoff,
        )
    )
    return tuple(sorted(queries, key=lambda item: item.query_id))


def _arxiv_block(block: str) -> str:
    return "(" + " OR ".join(f'abs:"{term}"' for term in _TERMS[block]) + ")"


def _openalex_block(block: str) -> str:
    return "(" + " OR ".join(f'"{term}"' for term in _TERMS[block]) + ")"


def _query_text(query: LogicalQuery) -> str:
    if query.index == "arxiv":
        blocks = " AND ".join(_arxiv_block(block) for block in _BRANCH_BLOCKS[query.branch])
        if query.shard_lower is None or query.shard_upper is None:
            raise ValueError("arxiv_leaf_missing_date_bounds")
        lower = query.shard_lower.replace("-", "") + "0000"
        upper = query.shard_upper.replace("-", "") + "2359"
        return f"{blocks} AND submittedDate:[{lower} TO {upper}]"
    if query.index == "openalex":
        blocks = " AND ".join(_openalex_block(block) for block in _BRANCH_BLOCKS[query.branch])
        filters: list[str] = []
        if query.shard_lower is not None:
            filters.append(f"from_publication_date:{query.shard_lower}")
        if query.shard_upper is None:
            raise ValueError("openalex_leaf_missing_upper_bound")
        filters.append(f"to_publication_date:{query.shard_upper}")
        filters.append(f"title_and_abstract.search:{blocks}")
        return ",".join(filters)
    if query.index == "dblp":
        try:
            return _DBLP_TERMS[query.branch]
        except KeyError as exc:
            raise ValueError("dblp_non_executable_branch") from exc
    raise ValueError("unknown_index")


def _dblp_expected_echo(registered_phrase: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", registered_phrase)
    if not tokens:
        raise ValueError("dblp_phrase_has_no_alphanumeric_token")
    return " ".join(f"{token}*" for token in tokens)


def _canonical_query_object(value: Mapping[str, Any] | None) -> str:
    if value is None:
        raise ValueError("missing_structured_expected_query")
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _headers(index: str) -> tuple[tuple[str, str], ...]:
    if index == "arxiv":
        return (("Accept", "application/atom+xml"),)
    return (("Accept", "application/json"),)


def _logical_parent_id(query: LogicalQuery) -> str:
    return query.parent_id or query.query_id


def build_request(
    catalog: Catalog,
    leaf_query_id: str,
    page_number: int,
    position_in: str | None,
) -> RequestSpec:
    if isinstance(page_number, bool) or not isinstance(page_number, int) or page_number < 0:
        raise ValueError("invalid_page_number")
    try:
        query = catalog.logical_query(leaf_query_id)
    except KeyError as exc:
        raise ValueError("unknown_leaf_query_id") from exc
    if query.kind != "leaf":
        raise ValueError("query_is_not_executable_leaf")

    policy = catalog.index_policies.get(query.index)
    if policy is None:
        raise ValueError("missing_index_policy")
    expected_policy = _INDEX_POLICIES[query.index]
    for key in ("scheme", "host", "path", "method", "page_size", "timeout_s"):
        if policy.get(key) != expected_policy[key]:
            raise ValueError(f"index_policy_mismatch:{key}")
    if policy["scheme"] != "https" or policy["host"] not in {
        "export.arxiv.org",
        "api.openalex.org",
        "dblp.org",
    }:
        raise ValueError("endpoint_not_allowlisted")

    page_size = int(policy["page_size"])
    query_text = _query_text(query)
    if query.index == "arxiv":
        expected_offset = str(page_number * page_size)
        if position_in is not None and position_in != expected_offset:
            raise ValueError("offset_does_not_match_page_number")
        effective_position = expected_offset
        parameters = (
            ("search_query", query_text),
            ("start", effective_position),
            ("max_results", str(page_size)),
        )
        interpreted_search = re.sub(
            r"submittedDate:\[([^\]]+)\]", r'submittedDate:"\1"', query_text
        )
        expected_echo = (
            f"arXiv Query: search_query={interpreted_search}&id_list=&"
            f"start={effective_position}&max_results={page_size}"
        )
    elif query.index == "openalex":
        if page_number == 0:
            if position_in not in (None, "*"):
                raise ValueError("initial_cursor_must_be_star")
            effective_position = "*"
        else:
            if not isinstance(position_in, str) or not position_in:
                raise ValueError("continuation_cursor_required")
            effective_position = position_in
        parameters = (
            ("filter", query_text),
            ("per-page", str(page_size)),
            ("cursor", effective_position),
        )
        expected_echo = _canonical_query_object(query.expected_openalex_oqo)
    else:
        expected_offset = str(page_number * page_size)
        if position_in is not None and position_in != expected_offset:
            raise ValueError("offset_does_not_match_page_number")
        effective_position = expected_offset
        parameters = (
            ("q", query_text),
            ("format", "json"),
            ("h", str(page_size)),
            ("f", effective_position),
        )
        expected_echo = _dblp_expected_echo(query_text)

    encoded_query = urlencode(parameters, doseq=False, quote_via=quote_plus)
    scheme = str(policy["scheme"])
    host = str(policy["host"])
    path = str(policy["path"])
    return RequestSpec(
        request_id=f"{leaf_query_id}#p{page_number}",
        leaf_query_id=leaf_query_id,
        logical_query_id=_logical_parent_id(query),
        index=query.index,
        method="GET",
        scheme=scheme,
        host=host,
        path=path,
        query_parameters=parameters,
        encoded_url=f"{scheme}://{host}{path}?{encoded_query}",
        headers=_headers(query.index),
        timeout_s=float(policy["timeout_s"]),
        page_number=page_number,
        position_in=effective_position,
        expected_interpreted_query=expected_echo,
    )


def _template_for(query: LogicalQuery) -> dict[str, Any]:
    policy = _INDEX_POLICIES[query.index]
    query_text = _query_text(query)
    if query.index == "arxiv":
        parameters = [
            ["search_query", query_text],
            ["start", "{offset}"],
            ["max_results", str(policy["page_size"])],
        ]
        expected = re.sub(
            r"submittedDate:\[([^\]]+)\]", r'submittedDate:"\1"', query_text
        )
        expected = (
            f"arXiv Query: search_query={expected}&id_list=&start={{offset}}&"
            f"max_results={policy['page_size']}"
        )
    elif query.index == "openalex":
        parameters = [
            ["filter", query_text],
            ["per-page", str(policy["page_size"])],
            ["cursor", "{position_in}"],
        ]
        expected = _canonical_query_object(query.expected_openalex_oqo)
    else:
        parameters = [
            ["q", query_text],
            ["format", "json"],
            ["h", str(policy["page_size"])],
            ["f", "{offset}"],
        ]
        expected = _dblp_expected_echo(query_text)
    return {
        "leaf_query_id": query.query_id,
        "logical_query_id": _logical_parent_id(query),
        "method": "GET",
        "scheme": policy["scheme"],
        "host": policy["host"],
        "path": policy["path"],
        "query_parameters": parameters,
        "headers": [list(item) for item in _headers(query.index)],
        "timeout_s": policy["timeout_s"],
        "expected_interpreted_query_template": expected,
    }


def build_catalog_document(cutoff: str = REGISTERED_CUTOFF) -> dict[str, Any]:
    """Build the finite, JSON-serializable registered query program."""

    queries = _logical_queries(cutoff)
    ids = tuple(query.query_id for query in queries)
    independently_expected = derive_expected_logical_ids(cutoff)
    if tuple(sorted(ids)) != independently_expected:
        raise AssertionError("generator_logical_id_matrix_mismatch")

    shard_policies: list[dict[str, Any]] = []
    for index, branch, policy_id in (
        ("arxiv", "Q6", "arxiv-q6-fixed-calendar-grid-v1"),
        ("openalex", "Q3", "openalex-q3-fixed-calendar-years-v1"),
        ("openalex", "Q6", "openalex-q6-fixed-calendar-years-v1"),
    ):
        shard_policies.append(
            {
                "policy_id": policy_id,
                "logical_query_id": f"{REGISTRATION_EPOCH}-{branch}@{index}",
                "generator": (
                    "fixed_calendar_years_then_months_v1"
                    if index == "arxiv"
                    else "fixed_pre1991_and_calendar_years_v1"
                ),
                "first_boundary": "1991-01-01" if index == "arxiv" else None,
                "last_boundary": cutoff,
                "observed_count_is_input": False,
                "adaptive_split": "forbidden",
                "shards": [
                    {
                        "shard_id": shard.shard_id,
                        "shard_lower": shard.shard_lower,
                        "shard_upper": shard.shard_upper,
                    }
                    for shard in derive_fixed_shards(index, branch, cutoff)
                ],
            }
        )

    templates = [_template_for(query) for query in queries if query.kind == "leaf"]
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "registration_epoch": REGISTRATION_EPOCH,
        "outcome_informed": True,
        "amendment_path": (
            "docs/related-work/claim-survey/"
            "2026-09-02-axis1-search-amendment.md"
        ),
        "supersedes": [
            "docs/related-work/claim-survey/"
            "2026-08-29-axis1-search-amendment.md"
        ],
        "cutoff": cutoff,
        "proof_scope": [
            "finite_query_program",
            "fixed_nonoverlapping_date_shards",
            "index_specific_work_ids",
            "deterministic_request_encoding",
        ],
        "index_policies": {
            index: dict(policy) for index, policy in _INDEX_POLICIES.items()
        },
        "shard_policies": shard_policies,
        "logical_queries": [
            {
                "query_id": query.query_id,
                "kind": query.kind,
                "index": query.index,
                "branch": query.branch,
                "parent_id": query.parent_id,
                "shard_lower": query.shard_lower,
                "shard_upper": query.shard_upper,
                "independent_pass_required": query.independent_pass_required,
                "expected_openalex_oqo": query.expected_openalex_oqo,
                "reference_openalex_oql": query.reference_openalex_oql,
            }
            for query in queries
        ],
        "request_templates": templates,
        "controls": [
            {
                "control_id": control_id,
                "indexes": indexes,
                "role": role,
            }
            for control_id, indexes, role in (
                ("C-OP-1", ["arxiv", "openalex", "dblp"], "single_phrase_lookup"),
                ("C-OP-2", ["arxiv", "openalex"], "or_operator"),
                ("C-OP-3", ["arxiv", "openalex"], "and_operator"),
                ("C-OP-4", ["arxiv", "openalex", "dblp"], "cutoff_boundary"),
                ("C-BLK-T", ["arxiv", "openalex", "dblp"], "concept_block_T"),
                ("C-BLK-M", ["arxiv", "openalex"], "concept_block_M"),
                ("C-BLK-O", ["arxiv", "openalex"], "concept_block_O"),
                ("C-BLK-V", ["arxiv", "openalex"], "concept_block_V"),
                ("C-BLK-W", ["arxiv", "openalex"], "concept_block_W"),
            )
        ],
        "expected_cardinalities": {
            "logical_queries": 267,
            "aggregate_queries": 3,
            "executable_leaves": 263,
            "declared_exclusions": 1,
            "arxiv_q6_leaves": 168,
            "openalex_q3_leaves": 37,
            "openalex_q6_leaves": 37,
        },
    }


def render_catalog_json(cutoff: str = REGISTERED_CUTOFF) -> bytes:
    return (
        json.dumps(
            build_catalog_document(cutoff),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def load_catalog(path: str) -> Catalog:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("catalog_unreadable") from exc
    if not isinstance(payload, dict):
        raise ValueError("catalog_root_not_object")
    cutoff = payload.get("cutoff")
    _validate_cutoff(cutoff)

    expected_ids = derive_expected_logical_ids(cutoff)
    logical_payload = payload.get("logical_queries")
    if not isinstance(logical_payload, list):
        raise ValueError("logical_queries_not_array")
    actual_ids = tuple(
        sorted(
            item.get("query_id")
            for item in logical_payload
            if isinstance(item, dict) and isinstance(item.get("query_id"), str)
        )
    )
    if actual_ids != expected_ids or len(actual_ids) != len(logical_payload):
        raise ValueError("logical_id_matrix_mismatch")

    expected_document = build_catalog_document(cutoff)
    if payload != expected_document:
        raise ValueError("catalog_program_mismatch")

    queries = tuple(LogicalQuery(**item) for item in logical_payload)
    templates = {
        item["leaf_query_id"]: MappingProxyType(dict(item))
        for item in payload["request_templates"]
    }
    return Catalog(
        schema_version=payload["schema_version"],
        registration_epoch=payload["registration_epoch"],
        outcome_informed=payload["outcome_informed"],
        amendment_path=payload["amendment_path"],
        supersedes=tuple(payload["supersedes"]),
        cutoff=cutoff,
        proof_scope=tuple(payload["proof_scope"]),
        index_policies=MappingProxyType(
            {
                index: MappingProxyType(dict(policy))
                for index, policy in payload["index_policies"].items()
            }
        ),
        shard_policies=tuple(MappingProxyType(dict(item)) for item in payload["shard_policies"]),
        logical_queries=queries,
        request_templates=MappingProxyType(templates),
        controls=tuple(MappingProxyType(dict(item)) for item in payload["controls"]),
        expected_cardinalities=MappingProxyType(dict(payload["expected_cardinalities"])),
    )


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the registered Axis 1 catalog")
    parser.add_argument("--output", required=True)
    parser.add_argument("--cutoff", default=REGISTERED_CUTOFF)
    args = parser.parse_args()
    Path(args.output).write_bytes(render_catalog_json(args.cutoff))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
