"""Offline Axis B5 leaf evaluator and fail-closed production entry.

This module can completely evaluate the six registered conditions from stored
responses.  It intentionally cannot issue a main-run HTTP request until the
six still-unregistered operational policy fields have been registered.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
from urllib.parse import quote, unquote, urlsplit

from .parsers import (
    JsonObject,
    JsonValue,
    Occurrence,
    ParsedPage,
    parse_arxiv_page,
    parse_dblp_page,
    parse_openalex_page,
)
from .preflight import (
    CATALOG_PATH,
    GitBackend,
    LIVE_PREFLIGHT_SCHEMA_PATH,
    _seal_digest,
    _validate_schema,
    build_lookup_request,
    load_anchor_registry,
    verify_registration,
)


PAGE_SIZE = {"arxiv": 200, "openalex": 200, "dblp": 100}
POSITION_PARAMETER = {"arxiv": "start", "dblp": "f"}
PAGINATION_KIND = {
    "arxiv": "offset",
    "openalex": "cursor",
    "dblp": "offset",
}
RETRY_DELAYS_S = (3.0, 6.0, 12.0)
MAX_RETRIES = 3
REGISTERED_ENDPOINTS = {
    "arxiv": ("export.arxiv.org", "/api/query"),
    "openalex": ("api.openalex.org", "/works"),
    "dblp": ("dblp.org", "/search/publ/api"),
}
UNREGISTERED_RUN_POLICY_FIELDS = (
    "expected_content_types",
    "timeout_s",
    "user_agent",
    "request_interval_s",
    "retryable_failures",
    "redirect_policy",
)


@dataclass(frozen=True)
class ConditionResult:
    condition: int
    passed: bool
    reason_code: str | None
    detail: str

    def __post_init__(self) -> None:
        if self.condition not in range(1, 7):
            raise ValueError("condition must be in 1..6")
        if self.passed != (self.reason_code is None):
            raise ValueError("reason_code must be absent exactly for passing results")


@dataclass(frozen=True)
class LeafDefinition:
    leaf_id: str
    kind: str
    index: str
    request_template: str
    first_page_url: str
    term_groups: tuple[tuple[str, ...], ...]
    term_text: Mapping[str, str]
    cutoff: str


@dataclass(frozen=True)
class RequestSpec:
    leaf_id: str
    kind: str
    index: str
    page_number: int
    position: int | str
    url: str
    host: str
    path: str


@dataclass(frozen=True)
class StoredResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    final_url: str


@dataclass(frozen=True)
class PageEvidence:
    leaf_id: str
    kind: str
    index: str
    page_number: int
    request_url: str
    request_position: int | str
    status: int
    headers: tuple[tuple[str, str], ...]
    content_type: str | None
    media_type: str | None
    final_url: str
    response_byte_count: int
    body_sha256: str
    parsed: ParsedPage

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": "izanagi-axis-b5-search-page-evidence/v1",
            "document_type": "page_evidence",
            "leaf_id": self.leaf_id,
            "leaf_kind": self.kind,
            "index": self.index,
            "page_number": self.page_number,
            "request": {
                "url": self.request_url,
                "position": self.request_position,
            },
            "response": {
                "status": self.status,
                "headers": [list(item) for item in self.headers],
                "content_type": self.content_type,
                "media_type": self.media_type,
                "final_url": self.final_url,
                "byte_count": self.response_byte_count,
                "body_sha256": self.body_sha256,
            },
            "parse": {
                "page_number": self.parsed.page_number,
                "declared_total": self.parsed.declared_total,
                "capacity_echo": self.parsed.capacity_echo,
                "actual_count": self.parsed.actual_count,
                "position": self.parsed.position,
                "next_cursor": self.parsed.next_cursor,
                "interpreted_query_text": self.parsed.interpreted_query_text,
                "interpreted_query_ast": _json_value_record(
                    self.parsed.interpreted_query_ast
                ),
                "parse_errors": list(self.parsed.parse_errors),
            },
            "occurrences": [
                {
                    "index_work_id": occurrence.index_work_id,
                    "page_number": occurrence.page_number,
                    "ordinal": occurrence.ordinal,
                    "raw_year": _json_value_record(occurrence.raw_year),
                    "included_by_cutoff": occurrence.included_by_cutoff,
                    "requires_ruling": occurrence.requires_ruling,
                }
                for occurrence in self.parsed.occurrences
            ],
        }


@dataclass(frozen=True)
class RequestCompletion:
    state: str
    condition_results: tuple[ConditionResult, ...]

    @property
    def passed(self) -> bool:
        return self.state == "完走" and all(
            result.passed for result in self.condition_results
        )


@dataclass(frozen=True)
class LeafEvaluation:
    leaf_id: str
    index: str
    completion: RequestCompletion
    duplicate_occurrences: tuple[tuple[str, int, int], ...]
    rerun_requested: bool
    rerun_performed: bool
    evidence_runs: tuple[tuple[PageEvidence, ...], ...]

    @property
    def passed(self) -> bool:
        return self.completion.passed

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": "izanagi-axis-b5-search-leaf-evaluation/v1",
            "document_type": "leaf_evaluation",
            "leaf_id": self.leaf_id,
            "index": self.index,
            "request_state": self.completion.state,
            "conditions": [
                {
                    "condition": result.condition,
                    "passed": result.passed,
                    "reason_code": result.reason_code,
                    "detail": result.detail,
                }
                for result in self.completion.condition_results
            ],
            "duplicate_occurrences": [
                {
                    "index_work_id": work_id,
                    "page_number": page_number,
                    "ordinal": ordinal,
                }
                for work_id, page_number, ordinal in self.duplicate_occurrences
            ],
            "rerun_requested": self.rerun_requested,
            "rerun_performed": self.rerun_performed,
            "evidence_run_count": len(self.evidence_runs),
        }


class LeafResolutionError(ValueError):
    pass


class PreflightError(RuntimeError):
    pass


class UnregisteredRunPolicyError(RuntimeError):
    """Raised for every attempted main-run issuance in this registration."""

    def __init__(self) -> None:
        self.unregistered_fields = UNREGISTERED_RUN_POLICY_FIELDS
        super().__init__(
            "main-run issuance is blocked; unregistered policy fields: "
            + ",".join(self.unregistered_fields)
        )

    def as_record(self) -> dict[str, Any]:
        return {
            "error_code": "unregistered_run_policy",
            "unregistered_fields": list(self.unregistered_fields),
        }


def _catalog_mapping(catalog: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if not isinstance(catalog, Mapping):
        raise LeafResolutionError("catalog must be a mapping")
    return catalog


def _term_table(catalog: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    blocks = catalog.get("blocks")
    if not isinstance(blocks, list):
        raise LeafResolutionError("catalog blocks are malformed")
    for block in blocks:
        if not isinstance(block, Mapping) or not isinstance(block.get("terms"), list):
            raise LeafResolutionError("catalog block is malformed")
        for term in block["terms"]:
            if not isinstance(term, Mapping):
                raise LeafResolutionError("catalog term is malformed")
            term_id = term.get("term_id")
            text = term.get("term")
            if (
                not isinstance(term_id, str)
                or not isinstance(text, str)
                or term_id in result
            ):
                raise LeafResolutionError("catalog term IDs are malformed or duplicated")
            result[term_id] = text
    return result


def _leaf_entries(catalog: Mapping[str, Any]) -> list[tuple[str, str, Mapping[str, Any]]]:
    entries: list[tuple[str, str, Mapping[str, Any]]] = []
    for collection, identity, kind in (
        ("queries", "query_id", "query"),
        ("controls", "control_id", "control"),
        ("aux_venue_streams", "stream_id", "aux_venue"),
    ):
        raw = catalog.get(collection)
        if not isinstance(raw, list):
            raise LeafResolutionError(f"catalog {collection} is malformed")
        for item in raw:
            if not isinstance(item, Mapping) or not isinstance(item.get(identity), str):
                raise LeafResolutionError(f"catalog {collection} entry is malformed")
            entries.append((str(item[identity]), kind, item))
    return entries


def resolve_leaf(catalog: Mapping[str, Any], leaf_id: str) -> LeafDefinition:
    """Resolve exactly one query, request-control, or auxiliary venue leaf."""

    value = _catalog_mapping(catalog)
    matches = [entry for entry in _leaf_entries(value) if entry[0] == leaf_id]
    if len(matches) != 1:
        raise LeafResolutionError(
            f"leaf ID must occur exactly once across all collections: {leaf_id!r}"
        )
    resolved_id, kind, raw = matches[0]
    index = raw.get("index")
    template = raw.get("request_template")
    first_page_url = raw.get("first_page_url")
    if index not in REGISTERED_ENDPOINTS:
        raise LeafResolutionError("leaf has an unsupported index")
    if not isinstance(template, str) or not isinstance(first_page_url, str):
        raise LeafResolutionError("leaf request URLs are malformed")
    expected_host, expected_path = REGISTERED_ENDPOINTS[str(index)]
    for url in (template, first_page_url):
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != expected_host
            or parsed.path != expected_path
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or parsed.fragment
        ):
            raise LeafResolutionError("leaf index conflicts with registered host/path")
    term_groups_raw = raw.get("term_groups", [])
    if not isinstance(term_groups_raw, list) or any(
        not isinstance(group, list) or any(not isinstance(item, str) for item in group)
        for group in term_groups_raw
    ):
        raise LeafResolutionError("leaf term_groups are malformed")
    term_groups = tuple(tuple(group) for group in term_groups_raw)
    terms = _term_table(value)
    if any(term_id not in terms for group in term_groups for term_id in group):
        raise LeafResolutionError("leaf references an unknown term ID")
    cutoff = value.get("cutoff")
    if not isinstance(cutoff, str):
        raise LeafResolutionError("catalog cutoff is malformed")
    return LeafDefinition(
        resolved_id,
        kind,
        str(index),
        template,
        first_page_url,
        term_groups,
        terms,
        cutoff,
    )


def _validate_page_number(page_number: Any) -> int:
    if (
        isinstance(page_number, bool)
        or not isinstance(page_number, int)
        or page_number < 0
    ):
        raise ValueError("page_number must be a nonnegative integer")
    return page_number


def _template_replace(template: str, placeholder: str, replacement: str) -> str:
    registered = re.findall(r"\{[^{}]+\}", template)
    if registered != [placeholder] or template.count(placeholder) != 1:
        raise ValueError("request template has an unregistered placeholder shape")
    prefix, suffix = template.split(placeholder)
    result = prefix + replacement + suffix
    if not result.startswith(prefix) or not result.endswith(suffix):
        raise AssertionError("placeholder replacement changed registered template bytes")
    if result[: len(prefix)] + placeholder + result[len(result) - len(suffix) :] != template:
        raise AssertionError("non-placeholder template bytes changed")
    return result


def build_request(
    leaf: LeafDefinition, page_number: int, position: int | str | None
) -> RequestSpec:
    """Replace only the registered position placeholder for one leaf page."""

    page = _validate_page_number(page_number)
    if leaf.index in POSITION_PARAMETER:
        expected_position = page * PAGE_SIZE[leaf.index]
        if position is not None and (
            isinstance(position, bool)
            or not isinstance(position, (int, str))
            or str(position) != str(expected_position)
        ):
            raise ValueError("offset position is not the registered fixed step")
        raw_position: int | str = expected_position
        url = _template_replace(leaf.request_template, "{POS}", str(expected_position))
    elif leaf.index == "openalex":
        if page == 0:
            if position not in (None, "*"):
                raise ValueError("OpenAlex page 0 cursor must be literal '*'")
            raw_position = "*"
            encoded = "*"
        else:
            if not isinstance(position, str) or not position:
                raise ValueError("OpenAlex continuation requires the preceding next_cursor")
            raw_position = position
            encoded = quote(position, safe="-_.~")
        url = _template_replace(leaf.request_template, "{CUR}", encoded)
    else:  # guarded by LeafDefinition construction
        raise ValueError("unsupported leaf index")
    if page == 0 and url != leaf.first_page_url:
        raise ValueError("page 0 URL differs from catalog first_page_url")
    parsed = urlsplit(url)
    expected_host, expected_path = REGISTERED_ENDPOINTS[leaf.index]
    if parsed.hostname != expected_host or parsed.path != expected_path:
        raise ValueError("request host/path differs from the registered endpoint")
    return RequestSpec(
        leaf.leaf_id,
        leaf.kind,
        leaf.index,
        page,
        raw_position,
        url,
        expected_host,
        expected_path,
    )


def _headers(value: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("response headers must be an ordered sequence")
    result: list[tuple[str, str]] = []
    for item in value:
        if (
            not isinstance(item, (list, tuple))
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], str)
        ):
            raise TypeError("each response header must be a string pair")
        result.append((item[0], item[1]))
    return tuple(result)


def _coerce_response(response: StoredResponse | Mapping[str, Any]) -> StoredResponse:
    if isinstance(response, StoredResponse):
        return response
    status = response.get("status")
    body = response.get("body")
    final_url = response.get("final_url")
    if isinstance(status, bool) or not isinstance(status, int):
        raise TypeError("response status must be an integer")
    if not isinstance(body, bytes) or not isinstance(final_url, str):
        raise TypeError("response body/final_url have invalid types")
    return StoredResponse(status, _headers(response.get("headers")), body, final_url)


def _content_type(headers: Sequence[tuple[str, str]]) -> str | None:
    values = [value for key, value in headers if key.lower() == "content-type"]
    return values[-1] if values else None


def _media_type(content_type: str | None) -> str | None:
    return (
        content_type.split(";", 1)[0].strip().lower()
        if content_type is not None
        else None
    )


def build_page_evidence(
    leaf: LeafDefinition,
    page_number: int,
    position: int | str | None,
    response: StoredResponse | Mapping[str, Any],
) -> PageEvidence:
    """Parse one saved response and retain all response headers and raw digests."""

    request = build_request(leaf, page_number, position)
    stored = _coerce_response(response)
    parser = {
        "arxiv": parse_arxiv_page,
        "openalex": parse_openalex_page,
        "dblp": parse_dblp_page,
    }[leaf.index]
    parsed = parser(stored.body, page_number)
    content_type = _content_type(stored.headers)
    return PageEvidence(
        leaf_id=leaf.leaf_id,
        kind=leaf.kind,
        index=leaf.index,
        page_number=page_number,
        request_url=request.url,
        request_position=request.position,
        status=stored.status,
        headers=stored.headers,
        content_type=content_type,
        media_type=_media_type(content_type),
        final_url=stored.final_url,
        response_byte_count=len(stored.body),
        body_sha256=hashlib.sha256(stored.body).hexdigest(),
        parsed=parsed,
    )


def normalize_interpreted_query(index: str, value: str) -> str:
    """Decode once, collapse whitespace, and normalize only arXiv date delimiters."""

    if not isinstance(value, str):
        raise TypeError("interpreted query must be a string")
    normalized = " ".join(unquote(value).split())
    if index == "arxiv":
        normalized = re.sub(
            r'submittedDate\s*:\s*(?:\[\s*([^\]\"]+?)\s*\]|"\s*([^\]\"]+?)\s*")',
            lambda match: (
                "submittedDate:["
                + " ".join((match.group(1) or match.group(2)).split())
                + "]"
            ),
            normalized,
        )
    return normalized


def _query_parameter(url: str, name: str) -> str:
    for item in urlsplit(url).query.split("&"):
        key, separator, raw_value = item.partition("=")
        if separator and key == name:
            return raw_value
    raise ValueError(f"request URL lacks {name}")


def _expected_text(leaf: LeafDefinition, evidence: PageEvidence) -> str:
    if leaf.index == "arxiv":
        return _query_parameter(evidence.request_url, "search_query")
    if leaf.index == "dblp":
        if leaf.term_groups:
            raw_terms = [
                leaf.term_text[term_id]
                for group in leaf.term_groups
                for term_id in group
            ]
            tokens = [
                token
                for term in raw_terms
                for token in re.split(r"[\s-]+", term)
                if token
            ]
            return " ".join(f"{token}*" for token in tokens)
        return unquote(_query_parameter(evidence.request_url, "q"))
    raise ValueError("OpenAlex uses structured query comparison")


class _InvalidOpenAlexAST(ValueError):
    pass


def _unique_object(value: Any) -> dict[str, Any]:
    if isinstance(value, JsonObject):
        result: dict[str, Any] = {}
        for key, member in value.members:
            if key in result:
                raise _InvalidOpenAlexAST("duplicate object key")
            result[key] = member
        return result
    if isinstance(value, Mapping):
        return dict(value)
    raise _InvalidOpenAlexAST("AST node must be an object")


def _ast_array(value: Any) -> tuple[Any, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    raise _InvalidOpenAlexAST("AST children must be an array")


def _ast_sort_key(value: tuple[Any, ...]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _canonical_openalex_node(value: Any) -> tuple[Any, ...]:
    node = _unique_object(value)
    keys = frozenset(node)
    if keys == {"join", "filters"}:
        join = node["join"]
        if type(join) is not str or join not in {"and", "or"}:
            raise _InvalidOpenAlexAST("group join must be and/or")
        children = _ast_array(node["filters"])
        if not children:
            raise _InvalidOpenAlexAST("group must have children")
        canonical = tuple(
            sorted(
                (_canonical_openalex_node(child) for child in children),
                key=_ast_sort_key,
            )
        )
        return ("group", join, canonical)
    if keys in (
        {"column_id", "value"},
        {"column_id", "operator", "value"},
    ):
        if any(type(node[key]) is not str for key in keys):
            raise _InvalidOpenAlexAST("filter fields must be strings")
        if node["column_id"] not in {
            "title_and_abstract.search",
            "to_publication_date",
        }:
            raise _InvalidOpenAlexAST("unregistered filter field")
        return (
            "filter",
            tuple((key, ("str", node[key])) for key in sorted(keys)),
        )
    if len(keys) == 1:
        field = next(iter(keys))
        if field not in {"title_and_abstract.search", "to_publication_date"}:
            raise _InvalidOpenAlexAST("unregistered direct filter field")
        if type(node[field]) is not str:
            raise _InvalidOpenAlexAST("direct filter value must be a string")
        return ("filter", ((field, ("str", node[field])),))
    raise _InvalidOpenAlexAST("AST object has unknown or missing keys")


def canonicalize_openalex_ast(value: Any) -> tuple[Any, ...]:
    """Canonicalize only sibling order; preserve multiplicity and nesting."""

    root = _unique_object(value)
    if frozenset(root) != {"get_rows", "filter_rows"}:
        raise _InvalidOpenAlexAST("AST root fields must be exact")
    if type(root["get_rows"]) is not str or root["get_rows"] != "200":
        raise _InvalidOpenAlexAST("get_rows must be the string '200'")
    rows = _ast_array(root["filter_rows"])
    if not rows:
        raise _InvalidOpenAlexAST("filter_rows must be nonempty")
    children = tuple(
        sorted(
            (_canonical_openalex_node(row) for row in rows),
            key=_ast_sort_key,
        )
    )
    return ("oqo", ("get_rows", ("str", "200")), ("filter_rows", children))


def build_expected_openalex_ast(leaf: LeafDefinition) -> JsonObject:
    """Derive the registered expected OQO from catalog term groups and cutoff."""

    if leaf.index != "openalex" or not leaf.term_groups:
        raise ValueError("expected OpenAlex AST requires a term-group leaf")
    groups: list[JsonValue] = []
    for group in leaf.term_groups:
        filters = tuple(
            JsonObject(
                (
                    ("column_id", "title_and_abstract.search"),
                    ("value", leaf.term_text[term_id]),
                )
            )
            for term_id in group
        )
        groups.append(JsonObject((("join", "or"), ("filters", filters))))
    cutoff = (
        "2023-12-31"
        if leaf.leaf_id == "B5-CTL-AND2023@openalex"
        else leaf.cutoff
    )
    groups.append(
        JsonObject(
            (("column_id", "to_publication_date"), ("value", cutoff))
        )
    )
    top = JsonObject((("join", "and"), ("filters", tuple(groups))))
    return JsonObject((("get_rows", "200"), ("filter_rows", (top,))))


def openalex_ast_matches(expected: Any, actual: Any) -> bool:
    try:
        return canonicalize_openalex_ast(expected) == canonicalize_openalex_ast(actual)
    except _InvalidOpenAlexAST:
        return False


def _ok(condition: int, detail: str) -> ConditionResult:
    return ConditionResult(condition, True, None, detail)


def _fail(condition: int, code: str, detail: str) -> ConditionResult:
    return ConditionResult(condition, False, code, detail)


def _condition1(leaf: LeafDefinition, pages: Sequence[PageEvidence]) -> ConditionResult:
    if leaf.kind == "aux_venue":
        return _ok(1, "condition 1 is not registered for auxiliary venue streams")
    if leaf.index == "openalex":
        try:
            expected = build_expected_openalex_ast(leaf)
        except ValueError as exc:
            return _fail(1, "expected_ast_unavailable", str(exc))
        if all(openalex_ast_matches(expected, page.parsed.interpreted_query_ast) for page in pages):
            return _ok(1, "all OpenAlex structured echoes match")
        return _fail(1, "interpreted_query_mismatch", "OpenAlex OQO differs from the registered AST")
    for page in pages:
        actual = page.parsed.interpreted_query_text
        if actual is None:
            return _fail(1, "interpreted_query_missing", "interpreted query text is absent")
        try:
            expected = _expected_text(leaf, page)
            if normalize_interpreted_query(leaf.index, actual) != normalize_interpreted_query(leaf.index, expected):
                return _fail(1, "interpreted_query_mismatch", "interpreted query differs after registered normalization")
        except (TypeError, ValueError):
            return _fail(1, "interpreted_query_mismatch", "interpreted query cannot be compared")
    return _ok(1, "all textual query echoes match")


def _condition2(leaf: LeafDefinition, pages: Sequence[PageEvidence]) -> ConditionResult:
    for ordinal, page in enumerate(pages):
        if page.page_number != ordinal:
            return _fail(2, "page_number_discontinuity", "page numbers are not 0-based and continuous")
        if leaf.index in POSITION_PARAMETER:
            expected = ordinal * PAGE_SIZE[leaf.index]
            if page.request_position != expected or page.parsed.position != expected:
                return _fail(2, "position_discontinuity", "offset is not the registered fixed step")
        elif ordinal == 0:
            if page.request_position != "*":
                return _fail(2, "position_discontinuity", "initial OpenAlex cursor is not literal '*'")
        elif page.request_position != pages[ordinal - 1].parsed.next_cursor:
            return _fail(2, "cursor_discontinuity", "cursor does not equal preceding next_cursor")
    return _ok(2, "registered positions are continuous")


def _condition3(leaf: LeafDefinition, pages: Sequence[PageEvidence]) -> ConditionResult:
    for ordinal, page in enumerate(pages):
        actual = page.parsed.actual_count
        total = page.parsed.declared_total
        is_last = ordinal == len(pages) - 1
        if leaf.index in POSITION_PARAMETER:
            position = page.parsed.position
            if total is None or position is None:
                return _fail(3, "declared_count_or_position_missing", "offset page lacks total or position")
            if is_last:
                if position + actual != total:
                    return _fail(3, "actual_count_mismatch", "final offset plus actual_count does not equal declared total")
            elif actual != PAGE_SIZE[leaf.index]:
                return _fail(3, "actual_count_mismatch", "non-final page is not full by actual container count")
        else:
            if not is_last:
                if page.parsed.next_cursor is None or actual != PAGE_SIZE[leaf.index]:
                    return _fail(3, "actual_count_mismatch", "non-final cursor page is not full or lacks next_cursor")
            elif page.parsed.next_cursor is not None:
                return _fail(3, "cursor_not_terminal", "last cursor page still has next_cursor")
    return _ok(3, "actual container counts satisfy terminal/non-terminal rules")


def _all_occurrences(pages: Sequence[PageEvidence]) -> tuple[Occurrence, ...]:
    return tuple(occurrence for page in pages for occurrence in page.parsed.occurrences)


def _duplicates(occurrences: Sequence[Occurrence]) -> tuple[tuple[str, int, int], ...]:
    seen: set[str] = set()
    duplicates: list[tuple[str, int, int]] = []
    for occurrence in occurrences:
        work_id = occurrence.index_work_id
        if work_id is not None and work_id in seen:
            duplicates.append((work_id, occurrence.page_number, occurrence.ordinal))
        if work_id is not None:
            seen.add(work_id)
    return tuple(duplicates)


def _condition4(pages: Sequence[PageEvidence]) -> tuple[ConditionResult, tuple[tuple[str, int, int], ...]]:
    occurrences = _all_occurrences(pages)
    for page in pages:
        if len(page.parsed.occurrences) != page.parsed.actual_count:
            return _fail(4, "occurrence_count_mismatch", "raw occurrence count differs from actual_count"), ()
        coordinates = [(item.page_number, item.ordinal) for item in page.parsed.occurrences]
        expected = [(page.page_number, ordinal) for ordinal in range(page.parsed.actual_count)]
        if coordinates != expected:
            return _fail(4, "occurrence_coordinate_mismatch", "occurrence coordinates are not preserved"), ()
    if any(not occurrence.index_work_id for occurrence in occurrences):
        return _fail(4, "index_work_id_missing", "an occurrence lacks its index-specific work ID"), ()
    duplicate_rows = _duplicates(occurrences)
    if duplicate_rows:
        return _fail(4, "duplicate_index_work_id", "page-local or cross-page duplicate work ID observed"), duplicate_rows
    return _ok(4, "all raw occurrences are retained and work IDs are unique"), ()


def _condition5(pages: Sequence[PageEvidence]) -> ConditionResult:
    totals = [page.parsed.declared_total for page in pages]
    if any(total is None for total in totals):
        return _fail(5, "declared_total_missing", "a page lacks its declared total")
    if len(set(totals)) != 1:
        return _fail(5, "declared_total_drift", "declared total changed between pages")
    occurrences = _all_occurrences(pages)
    unique_ids = {item.index_work_id for item in occurrences if item.index_work_id}
    declared = totals[0]
    if len(unique_ids) != declared:
        return _fail(5, "unique_total_mismatch", "distinct work ID count differs from declared total")
    return _ok(5, "distinct work ID count equals the stable declared total")


def _condition6(
    leaf: LeafDefinition,
    pages: Sequence[PageEvidence],
    expected_content_types: Sequence[str],
) -> ConditionResult:
    expected = {
        item.strip().lower()
        for item in expected_content_types
        if isinstance(item, str) and item.strip()
    }
    if not expected or len(expected) != len(expected_content_types):
        return _fail(6, "expected_content_types_unregistered", "an explicit exact media-type set is required")
    expected_host, _path = REGISTERED_ENDPOINTS[leaf.index]
    for page in pages:
        if page.parsed.parse_errors:
            return _fail(6, "parse_error", ",".join(page.parsed.parse_errors))
        if page.status != 200:
            return _fail(6, "status_not_200", f"page {page.page_number} status is {page.status}")
        if page.media_type not in expected:
            return _fail(6, "content_type_mismatch", f"page {page.page_number} media type is not registered")
        final = urlsplit(page.final_url)
        if final.scheme != "https" or final.hostname != expected_host:
            return _fail(6, "final_url_host_mismatch", "final URL host differs from requested host")
    if pages[-1].parsed.declared_total is None:
        return _fail(6, "declared_total_missing", "final page lacks a total-count field")
    return _ok(6, "all responses and final termination evidence are normal")


def _evaluate_once(
    leaf: LeafDefinition,
    pages: Sequence[PageEvidence],
    expected_content_types: Sequence[str],
) -> tuple[tuple[ConditionResult, ...], tuple[tuple[str, int, int], ...]]:
    if not pages:
        conditions = tuple(
            _fail(number, "no_pages", "leaf has no saved page evidence")
            for number in range(1, 7)
        )
        return conditions, ()
    if any(page.leaf_id != leaf.leaf_id or page.index != leaf.index for page in pages):
        conditions = tuple(
            _fail(number, "leaf_evidence_mismatch", "page belongs to another leaf or index")
            for number in range(1, 7)
        )
        return conditions, ()
    condition4, duplicate_rows = _condition4(pages)
    return (
        _condition1(leaf, pages),
        _condition2(leaf, pages),
        _condition3(leaf, pages),
        condition4,
        _condition5(pages),
        _condition6(leaf, pages, expected_content_types),
    ), duplicate_rows


def evaluate_leaf(
    leaf: LeafDefinition,
    pages: Sequence[PageEvidence],
    *,
    expected_content_types: Sequence[str],
    rerun_pages: Sequence[PageEvidence] | None = None,
) -> LeafEvaluation:
    """Evaluate one leaf; at most one explicit page-0 rerun can replace drift."""

    first_pages = tuple(pages)
    first_results, first_duplicates = _evaluate_once(
        leaf, first_pages, expected_content_types
    )
    drift = first_results[4].reason_code == "declared_total_drift"
    if rerun_pages is not None and not drift:
        raise ValueError("a rerun is permitted only after declared-total drift")
    if drift and rerun_pages is not None:
        second_pages = tuple(rerun_pages)
        results, duplicate_rows = _evaluate_once(
            leaf, second_pages, expected_content_types
        )
        runs = (first_pages, second_pages)
        rerun_performed = True
        rerun_requested = results[4].reason_code == "declared_total_drift"
    else:
        results = first_results
        duplicate_rows = first_duplicates
        runs = (first_pages,)
        rerun_performed = False
        rerun_requested = drift
    state = "完走" if all(result.passed for result in results) else "未完走"
    return LeafEvaluation(
        leaf.leaf_id,
        leaf.index,
        RequestCompletion(state, results),
        duplicate_rows,
        rerun_requested,
        rerun_performed,
        runs,
    )


def _json_value_record(value: JsonValue) -> Any:
    if isinstance(value, JsonObject):
        return {
            "members": [
                [key, _json_value_record(member)] for key, member in value.members
            ]
        }
    if isinstance(value, tuple):
        return [_json_value_record(item) for item in value]
    return value


def issue_run_request(_request: RequestSpec) -> None:
    """The sole main-run issuance boundary, intentionally unavailable."""

    raise UnregisteredRunPolicyError()


def _recorded_lookup_is_consistent(item: Mapping[str, Any]) -> bool:
    index = item.get("index")
    expected_media_type = {
        "arxiv": "application/atom+xml",
        "openalex": "application/json",
        "dblp": "application/json",
    }.get(index)
    raw_headers = item.get("response_headers")
    if not isinstance(raw_headers, list):
        return False
    try:
        observed_media_type = _media_type(_content_type(_headers(raw_headers)))
    except TypeError:
        return False
    if (
        item.get("classification") != "収録"
        or item.get("status") != 200
        or item.get("transport_error") is not None
        or item.get("content_type") != expected_media_type
        or observed_media_type != expected_media_type
        or item.get("final_url") != item.get("request_url")
    ):
        return False
    shape = item.get("observed_shape")
    observed_id = item.get("observed_index_work_id")
    if not isinstance(shape, Mapping) or shape.get("parse_error") is not None:
        return False
    if index == "openalex":
        return (
            shape.get("json_root_type") == "dict"
            and isinstance(observed_id, str)
            and observed_id.startswith("W")
        )
    if index == "arxiv":
        return (
            shape.get("arxiv_entry_count") == 1
            and isinstance(observed_id, str)
            and bool(observed_id)
        )
    if index == "dblp":
        total = shape.get("dblp_total")
        matches = shape.get("dblp_matching_doi_count")
        return (
            isinstance(total, int)
            and not isinstance(total, bool)
            and total > 0
            and isinstance(matches, int)
            and not isinstance(matches, bool)
            and matches > 0
            and isinstance(observed_id, str)
            and bool(observed_id)
            and shape.get("json_root_type") == "dict"
        )
    return False


def _load_live_preflight(
    path: Path,
    *,
    repo_root: Path,
    registration_seal: Mapping[str, Any],
) -> Mapping[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(
            (repo_root / LIVE_PREFLIGHT_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        _validate_schema(schema, record)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise PreflightError(f"live preflight record is not durable/schema-valid: {exc}") from exc
    if record.get("registration_seal") != registration_seal:
        raise PreflightError("live preflight uses a different registration seal")
    if record.get("registration_commit") != registration_seal.get(
        "registration_commit"
    ):
        raise PreflightError("live preflight names a different registration commit")
    if record.get("registration_seal_sha256") != _seal_digest(registration_seal):
        raise PreflightError("live preflight registration seal digest differs")
    anchors = load_anchor_registry(repo_root / "orchestrator/axis_b5_search/anchor_registry.json")
    anchors_by_id = {anchor.anchor_id: anchor for anchor in anchors}
    expected = {
        (anchor.anchor_id, index)
        for anchor in anchors
        for index in anchor.member_indexes
    }
    lookups = record.get("lookups")
    if not isinstance(lookups, list):
        raise PreflightError("live preflight lookup collection is malformed")
    identities = [(item.get("anchor_id"), item.get("index")) for item in lookups if isinstance(item, Mapping)]
    if len(identities) != 30 or len(set(identities)) != 30 or set(identities) != expected:
        raise PreflightError("live preflight does not contain the exact 30 members")
    for item in lookups:
        anchor = anchors_by_id[item["anchor_id"]]
        index = item["index"]
        if (
            item.get("control_id")
            != f"B5-ANC-{anchor.anchor_id}@{index}"
            or item.get("request_url") != build_lookup_request(anchor, index).url
            or item.get("registered_openalex_work_id")
            != (anchor.openalex_work_id if index == "openalex" else None)
        ):
            raise PreflightError("live preflight lookup differs from anchor registration")
        if item.get("classification") == "収録" and not _recorded_lookup_is_consistent(
            item
        ):
            raise PreflightError(
                "live preflight recorded lookup is inconsistent with its observation"
            )
    if (
        record.get("exact_member_set") is not True
        or record.get("passed") is not True
        or record.get("axis_status") != "preflight-passed"
        or record.get("may_start_run") is not True
        or any(item.get("classification") != "収録" for item in lookups)
    ):
        raise PreflightError("live preflight does not authorize leaf issuance")
    return record


def run_leaf(
    leaf_id: str,
    *,
    registration_commit: str,
    repo_root: str | os.PathLike[str],
    live_preflight_path: str | os.PathLike[str],
    _git_backend: GitBackend | None = None,
) -> None:
    """Production entry: recompute registration, verify durable live evidence, stop."""

    root = Path(repo_root).resolve()
    registration = verify_registration(
        registration_commit, repo_root=root, git_backend=_git_backend
    )
    if not registration.passed or registration.seal_record is None:
        raise PreflightError(
            f"registration preflight failed: {registration.reason_code}: {registration.detail}"
        )
    _load_live_preflight(
        Path(live_preflight_path),
        repo_root=root,
        registration_seal=registration.seal_record,
    )
    catalog_value = json.loads((root / CATALOG_PATH).read_text(encoding="utf-8"))
    leaf = resolve_leaf(catalog_value, leaf_id)
    request = build_request(leaf, 0, None)
    issue_run_request(request)


def _run_leaf_for_test(
    leaf: LeafDefinition,
    pages: Sequence[PageEvidence],
    *,
    expected_content_types: Sequence[str],
    rerun_pages: Sequence[PageEvidence] | None = None,
) -> LeafEvaluation:
    """Private deterministic seam; it accepts only already-saved evidence."""

    return evaluate_leaf(
        leaf,
        pages,
        expected_content_types=expected_content_types,
        rerun_pages=rerun_pages,
    )


__all__ = [
    "ConditionResult",
    "LeafDefinition",
    "LeafEvaluation",
    "LeafResolutionError",
    "MAX_RETRIES",
    "PAGE_SIZE",
    "PAGINATION_KIND",
    "POSITION_PARAMETER",
    "PreflightError",
    "REGISTERED_ENDPOINTS",
    "RETRY_DELAYS_S",
    "RequestCompletion",
    "RequestSpec",
    "StoredResponse",
    "UNREGISTERED_RUN_POLICY_FIELDS",
    "UnregisteredRunPolicyError",
    "build_expected_openalex_ast",
    "build_page_evidence",
    "build_request",
    "canonicalize_openalex_ast",
    "evaluate_leaf",
    "issue_run_request",
    "normalize_interpreted_query",
    "openalex_ast_matches",
    "resolve_leaf",
    "run_leaf",
]
