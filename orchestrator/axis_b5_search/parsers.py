"""Pure parsers for stored Axis B5 search response bodies.

The parsers preserve page occurrences and response echoes.  Pagination decisions
belong to the runner: in particular, offset parsers never calculate a next
position from the number of returned elements.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, TypeAlias, Union


JsonValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    "JsonObject",
    tuple["JsonValue", ...],
]


@dataclass(frozen=True)
class JsonObject:
    """A JSON object whose ordered members retain duplicate keys."""

    members: tuple[tuple[str, JsonValue], ...]


@dataclass(frozen=True)
class Occurrence:
    """One response-container occurrence; duplicates remain separate rows."""

    index_work_id: str | None
    page_number: int
    ordinal: int
    raw_year: JsonValue
    included_by_cutoff: bool | None
    requires_ruling: bool


@dataclass(frozen=True)
class ParsedPage:
    """Index-neutral evidence extracted from one stored response page."""

    index: str
    page_number: int | None
    declared_total: int | None
    capacity_echo: int | None
    actual_count: int
    position: int | None
    next_cursor: str | None
    interpreted_query_text: str | None
    interpreted_query_ast: JsonValue
    occurrences: tuple[Occurrence, ...]
    parse_errors: tuple[str, ...]


PARSE_ERROR_CODES: tuple[str, ...] = (
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


_ATOM = "http://www.w3.org/2005/Atom"
_OPENSEARCH = "http://a9.com/-/spec/opensearch/1.1/"
_DBLP_CUTOFF_YEAR = 2026
_MISSING = object()


def _add_error(errors: list[str], code: str) -> None:
    if code not in PARSE_ERROR_CODES:
        raise AssertionError(f"unregistered parse error code: {code}")
    if code not in errors:
        errors.append(code)


def _valid_page_number(page_number: object) -> bool:
    return (
        isinstance(page_number, int)
        and not isinstance(page_number, bool)
        and page_number >= 0
    )


def _empty_page(index: str, page_number: object, code: str) -> ParsedPage:
    return ParsedPage(
        index=index,
        page_number=page_number if _valid_page_number(page_number) else None,
        declared_total=None,
        capacity_echo=None,
        actual_count=0,
        position=None,
        next_cursor=None,
        interpreted_query_text=None,
        interpreted_query_ast=None,
        occurrences=(),
        parse_errors=(code,),
    )


def _body_is_bytes(body: object) -> bool:
    return isinstance(body, bytes)


def _parse_nonnegative_int(
    raw: object,
    errors: list[str],
    missing_code: str,
    invalid_code: str,
) -> int | None:
    if raw is _MISSING or raw is None:
        _add_error(errors, missing_code)
        return None
    if isinstance(raw, bool):
        _add_error(errors, invalid_code)
        return None
    if isinstance(raw, int):
        if raw >= 0:
            return raw
        _add_error(errors, invalid_code)
        return None
    if isinstance(raw, str) and re.fullmatch(r"[0-9]+", raw.strip()):
        return int(raw.strip())
    _add_error(errors, invalid_code)
    return None


def _work_id(raw: object, errors: list[str]) -> str | None:
    if raw is _MISSING or raw is None or raw == "":
        _add_error(errors, "missing_index_work_id")
        return None
    if not isinstance(raw, str):
        _add_error(errors, "invalid_index_work_id")
        return None
    value = raw.strip()
    if not value:
        _add_error(errors, "missing_index_work_id")
        return None
    return value


def _json_object(pairs: list[tuple[str, Any]]) -> JsonObject:
    return JsonObject(tuple((key, _freeze_json(value)) for key, value in pairs))


def _freeze_json(value: Any) -> JsonValue:
    if isinstance(value, JsonObject):
        return JsonObject(
            tuple((key, _freeze_json(item)) for key, item in value.members)
        )
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _object_get(obj: JsonObject, key: str) -> object:
    for member_key, value in reversed(obj.members):
        if member_key == key:
            return value
    return _MISSING


def _decode_json(
    body: bytes,
    index: str,
    page_number: int,
) -> tuple[JsonObject | None, ParsedPage | None]:
    try:
        payload = json.loads(body, object_pairs_hook=_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return None, _empty_page(index, page_number, "invalid_json")
    if not isinstance(payload, JsonObject):
        return None, _empty_page(index, page_number, "json_root_not_object")
    return payload, None


def _query_text(raw: object, errors: list[str]) -> str | None:
    if raw is _MISSING or raw is None:
        _add_error(errors, "missing_interpreted_query_text")
        return None
    if not isinstance(raw, str):
        _add_error(errors, "invalid_interpreted_query_text")
        return None
    return raw


def parse_arxiv_page(body: bytes, page_number: int) -> ParsedPage:
    """Parse one arXiv Atom page without deriving its next offset."""

    if not _valid_page_number(page_number):
        return _empty_page("arxiv", page_number, "invalid_page_number")
    if not _body_is_bytes(body):
        return _empty_page("arxiv", page_number, "invalid_body_type")
    try:
        root = ET.fromstring(body)
    except (ET.ParseError, ValueError):
        return _empty_page("arxiv", page_number, "invalid_xml")

    errors: list[str] = []
    declared_total = _parse_nonnegative_int(
        root.findtext(f"{{{_OPENSEARCH}}}totalResults"),
        errors,
        "missing_declared_total",
        "invalid_declared_total",
    )
    capacity_echo = _parse_nonnegative_int(
        root.findtext(f"{{{_OPENSEARCH}}}itemsPerPage"),
        errors,
        "missing_capacity_echo",
        "invalid_capacity_echo",
    )
    position = _parse_nonnegative_int(
        root.findtext(f"{{{_OPENSEARCH}}}startIndex"),
        errors,
        "missing_position",
        "invalid_position",
    )
    interpreted_query_text = _query_text(
        root.findtext(f"{{{_ATOM}}}title"), errors
    )

    entries = list(root.findall(f"{{{_ATOM}}}entry"))
    occurrences: list[Occurrence] = []
    for ordinal, entry in enumerate(entries):
        occurrences.append(
            Occurrence(
                index_work_id=_work_id(
                    entry.findtext(f"{{{_ATOM}}}id"), errors
                ),
                page_number=page_number,
                ordinal=ordinal,
                raw_year=None,
                included_by_cutoff=None,
                requires_ruling=False,
            )
        )

    return ParsedPage(
        index="arxiv",
        page_number=page_number,
        declared_total=declared_total,
        capacity_echo=capacity_echo,
        actual_count=len(entries),
        position=position,
        next_cursor=None,
        interpreted_query_text=interpreted_query_text,
        interpreted_query_ast=None,
        occurrences=tuple(occurrences),
        parse_errors=tuple(errors),
    )


def parse_openalex_page(body: bytes, page_number: int) -> ParsedPage:
    """Parse one OpenAlex page and preserve its opaque next cursor and AST."""

    if not _valid_page_number(page_number):
        return _empty_page("openalex", page_number, "invalid_page_number")
    if not _body_is_bytes(body):
        return _empty_page("openalex", page_number, "invalid_body_type")
    payload, failure = _decode_json(body, "openalex", page_number)
    if failure is not None or payload is None:
        return failure or _empty_page("openalex", page_number, "json_root_not_object")

    errors: list[str] = []
    meta_raw = _object_get(payload, "meta")
    if meta_raw is _MISSING:
        _add_error(errors, "missing_meta")
        meta = JsonObject(())
    elif not isinstance(meta_raw, JsonObject):
        _add_error(errors, "invalid_meta")
        meta = JsonObject(())
    else:
        meta = meta_raw

    results_raw = _object_get(payload, "results")
    if results_raw is _MISSING:
        _add_error(errors, "missing_results")
        results: tuple[JsonValue, ...] = ()
    elif not isinstance(results_raw, tuple):
        _add_error(errors, "invalid_results")
        results = ()
    else:
        results = results_raw

    declared_total = _parse_nonnegative_int(
        _object_get(meta, "count"),
        errors,
        "missing_declared_total",
        "invalid_declared_total",
    )
    capacity_echo = _parse_nonnegative_int(
        _object_get(meta, "per_page"),
        errors,
        "missing_capacity_echo",
        "invalid_capacity_echo",
    )

    occurrences: list[Occurrence] = []
    for ordinal, result_raw in enumerate(results):
        if not isinstance(result_raw, JsonObject):
            _add_error(errors, "invalid_result")
            work_id_raw = _MISSING
        else:
            work_id_raw = _object_get(result_raw, "id")
        occurrences.append(
            Occurrence(
                index_work_id=_work_id(work_id_raw, errors),
                page_number=page_number,
                ordinal=ordinal,
                raw_year=None,
                included_by_cutoff=None,
                requires_ruling=False,
            )
        )

    x_query_raw = _object_get(meta, "x_query")
    if x_query_raw is _MISSING:
        _add_error(errors, "missing_x_query")
        x_query = JsonObject(())
    elif not isinstance(x_query_raw, JsonObject):
        _add_error(errors, "invalid_x_query")
        x_query = JsonObject(())
    else:
        x_query = x_query_raw

    interpreted_query_text = _query_text(_object_get(x_query, "oql"), errors)
    ast_raw = _object_get(x_query, "oqo")
    if ast_raw is _MISSING:
        _add_error(errors, "missing_interpreted_query_ast")
        interpreted_query_ast: JsonValue = None
    else:
        interpreted_query_ast = ast_raw  # Preserve unknown types for runner checks.
        if not isinstance(ast_raw, JsonObject):
            _add_error(errors, "invalid_interpreted_query_ast")

    next_cursor_raw = _object_get(meta, "next_cursor")
    if next_cursor_raw is _MISSING or next_cursor_raw is None:
        next_cursor = None
    elif isinstance(next_cursor_raw, str):
        next_cursor = next_cursor_raw
    else:
        _add_error(errors, "invalid_next_cursor")
        next_cursor = None

    return ParsedPage(
        index="openalex",
        page_number=page_number,
        declared_total=declared_total,
        capacity_echo=capacity_echo,
        actual_count=len(results),
        position=None,
        next_cursor=next_cursor,
        interpreted_query_text=interpreted_query_text,
        interpreted_query_ast=interpreted_query_ast,
        occurrences=tuple(occurrences),
        parse_errors=tuple(errors),
    )


def _hit_items(raw: object, errors: list[str]) -> tuple[JsonValue, ...]:
    if raw is _MISSING or raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, JsonObject):
        return (raw,)
    _add_error(errors, "invalid_hit_collection")
    return ()


def _dblp_cutoff(
    raw: JsonValue | object,
) -> tuple[JsonValue, bool | None, bool]:
    if raw is _MISSING or raw is None:
        return None, None, True
    raw_value = raw
    if isinstance(raw, bool):
        text = ""
    elif isinstance(raw, (str, int)):
        text = str(raw)
    else:
        text = ""
    if not re.fullmatch(r"[0-9]{4}", text):
        return raw_value, None, True
    return raw_value, int(text) <= _DBLP_CUTOFF_YEAR, False


def parse_dblp_page(body: bytes, page_number: int) -> ParsedPage:
    """Parse one DBLP page, retaining every hit and its cutoff decision."""

    if not _valid_page_number(page_number):
        return _empty_page("dblp", page_number, "invalid_page_number")
    if not _body_is_bytes(body):
        return _empty_page("dblp", page_number, "invalid_body_type")
    payload, failure = _decode_json(body, "dblp", page_number)
    if failure is not None or payload is None:
        return failure or _empty_page("dblp", page_number, "json_root_not_object")

    errors: list[str] = []
    result_raw = _object_get(payload, "result")
    if result_raw is _MISSING:
        _add_error(errors, "missing_result_object")
        result = JsonObject(())
    elif not isinstance(result_raw, JsonObject):
        _add_error(errors, "invalid_result_object")
        result = JsonObject(())
    else:
        result = result_raw

    hits_raw = _object_get(result, "hits")
    if hits_raw is _MISSING:
        _add_error(errors, "missing_hits_object")
        hits = JsonObject(())
    elif not isinstance(hits_raw, JsonObject):
        _add_error(errors, "invalid_hits_object")
        hits = JsonObject(())
    else:
        hits = hits_raw

    declared_total = _parse_nonnegative_int(
        _object_get(hits, "@total"),
        errors,
        "missing_declared_total",
        "invalid_declared_total",
    )
    capacity_echo = _parse_nonnegative_int(
        _object_get(hits, "@sent"),
        errors,
        "missing_capacity_echo",
        "invalid_capacity_echo",
    )
    position = _parse_nonnegative_int(
        _object_get(hits, "@first"),
        errors,
        "missing_position",
        "invalid_position",
    )
    hit_items = _hit_items(_object_get(hits, "hit"), errors)

    occurrences: list[Occurrence] = []
    for ordinal, hit_raw in enumerate(hit_items):
        if not isinstance(hit_raw, JsonObject):
            _add_error(errors, "invalid_hit")
            info = JsonObject(())
        else:
            info_raw = _object_get(hit_raw, "info")
            if info_raw is _MISSING:
                _add_error(errors, "missing_info_object")
                info = JsonObject(())
            elif not isinstance(info_raw, JsonObject):
                _add_error(errors, "invalid_info_object")
                info = JsonObject(())
            else:
                info = info_raw
        raw_year, included_by_cutoff, requires_ruling = _dblp_cutoff(
            _object_get(info, "year")
        )
        occurrences.append(
            Occurrence(
                index_work_id=_work_id(_object_get(info, "key"), errors),
                page_number=page_number,
                ordinal=ordinal,
                raw_year=raw_year,
                included_by_cutoff=included_by_cutoff,
                requires_ruling=requires_ruling,
            )
        )

    interpreted_query_text = _query_text(_object_get(result, "query"), errors)
    return ParsedPage(
        index="dblp",
        page_number=page_number,
        declared_total=declared_total,
        capacity_echo=capacity_echo,
        actual_count=len(hit_items),
        position=position,
        next_cursor=None,
        interpreted_query_text=interpreted_query_text,
        interpreted_query_ast=None,
        occurrences=tuple(occurrences),
        parse_errors=tuple(errors),
    )
