"""Pure parsers for stored Axis 1 search response bodies."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable
from urllib.parse import parse_qs, unquote, urlparse


@dataclass(frozen=True)
class Occurrence:
    index_work_id: str
    page_number: int
    ordinal: int
    raw_date_value: str | None
    interpreted_date: str | None
    date_missing_reason: str | None
    family_keys: tuple[str, ...]


@dataclass(frozen=True)
class ParsedPage:
    index: str
    declared_total: int | None
    capacity_echo: int | None
    actual_count: int
    interpreted_query: str
    position_in: str | None
    position_out: str | None
    occurrences: tuple[Occurrence, ...]
    parse_errors: tuple[str, ...]


_ATOM = "http://www.w3.org/2005/Atom"
_OPENSEARCH = "http://a9.com/-/spec/opensearch/1.1/"
_ARXIV = "http://arxiv.org/schemas/atom"


def _parse_int(value: Any, field: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or value is None:
        errors.append(f"missing_integer:{field}")
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"invalid_integer:{field}")
        return None
    if parsed < 0:
        errors.append(f"negative_integer:{field}")
        return None
    return parsed


def _interpret_full_date(
    raw: Any, missing_code: str, invalid_code: str
) -> tuple[str | None, str | None, str | None]:
    if raw is None or raw == "":
        return None, None, missing_code
    raw_text = str(raw)
    candidate = raw_text[:10]
    try:
        interpreted = date.fromisoformat(candidate).isoformat()
    except ValueError:
        return raw_text, None, invalid_code
    return raw_text, interpreted, None


def _interpret_year(raw: Any) -> tuple[str | None, str | None, str | None]:
    if raw is None or raw == "":
        return None, None, "missing_dblp_year"
    raw_text = str(raw)
    if not re.fullmatch(r"[0-9]{4}", raw_text):
        return raw_text, None, "invalid_dblp_year"
    try:
        interpreted = date(int(raw_text), 1, 1).isoformat()
    except ValueError:
        return raw_text, None, "invalid_dblp_year"
    return raw_text, interpreted, None


def _normalise_arxiv_id(value: str) -> str | None:
    text = unquote(value).strip()
    lowered = text.lower()
    marker = "/abs/"
    if marker in lowered:
        start = lowered.index(marker) + len(marker)
        text = text[start:]
    elif lowered.startswith("arxiv:"):
        text = text[len("arxiv:") :]
    text = re.sub(r"v[0-9]+$", "", text, flags=re.IGNORECASE).strip("/")
    if not text:
        return None
    return f"arxiv:{text.lower()}"


def _normalise_doi(value: str) -> str | None:
    text = unquote(value).strip()
    text = re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", text, flags=re.IGNORECASE
    ).strip()
    if not text.lower().startswith("10."):
        return None
    lowered = text.lower()
    match = re.fullmatch(r"10\.48550/arxiv\.(.+)", lowered)
    if match:
        return _normalise_arxiv_id(match.group(1))
    return f"doi:{lowered}"


def _family_keys(arxiv_values: Iterable[Any], doi_values: Iterable[Any]) -> tuple[str, ...]:
    keys: list[str] = []
    for value in arxiv_values:
        if isinstance(value, str):
            key = _normalise_arxiv_id(value)
            if key is not None and key not in keys:
                keys.append(key)
    for value in doi_values:
        if isinstance(value, str):
            key = _normalise_doi(value)
            if key is not None and key not in keys:
                keys.append(key)
    return tuple(sorted(keys))


def _empty_page(index: str, error: str) -> ParsedPage:
    return ParsedPage(index, None, None, 0, "", None, None, (), (error,))


def parse_arxiv_page(body: bytes) -> ParsedPage:
    errors: list[str] = []
    try:
        root = ET.fromstring(body)
    except (ET.ParseError, ValueError) as exc:
        return _empty_page("arxiv", f"invalid_xml:{type(exc).__name__}")

    total = _parse_int(
        root.findtext(f"{{{_OPENSEARCH}}}totalResults"),
        "opensearch.totalResults",
        errors,
    )
    capacity = _parse_int(
        root.findtext(f"{{{_OPENSEARCH}}}itemsPerPage"),
        "opensearch.itemsPerPage",
        errors,
    )
    start = _parse_int(
        root.findtext(f"{{{_OPENSEARCH}}}startIndex"),
        "opensearch.startIndex",
        errors,
    )
    entries = list(root.findall(f"{{{_ATOM}}}entry"))
    page_number = start // capacity if start is not None and capacity not in (None, 0) else 0
    occurrences: list[Occurrence] = []
    for ordinal, entry in enumerate(entries):
        work_id = (entry.findtext(f"{{{_ATOM}}}id") or "").strip()
        if not work_id:
            errors.append(f"missing_index_work_id:entry[{ordinal}].id")
        raw_date, interpreted_date, date_reason = _interpret_full_date(
            entry.findtext(f"{{{_ATOM}}}published"),
            "missing_arxiv_published",
            "invalid_arxiv_published",
        )
        doi = entry.findtext(f"{{{_ARXIV}}}doi")
        occurrences.append(
            Occurrence(
                index_work_id=work_id,
                page_number=page_number,
                ordinal=ordinal,
                raw_date_value=raw_date,
                interpreted_date=interpreted_date,
                date_missing_reason=date_reason,
                family_keys=_family_keys((work_id,), (doi,)),
            )
        )

    position_out: str | None = None
    if start is not None and total is not None and start + len(entries) < total:
        position_out = str(start + len(entries))
    return ParsedPage(
        index="arxiv",
        declared_total=total,
        capacity_echo=capacity,
        actual_count=len(entries),
        interpreted_query=(root.findtext(f"{{{_ATOM}}}title") or "").strip(),
        position_in=str(start) if start is not None else None,
        position_out=position_out,
        occurrences=tuple(occurrences),
        parse_errors=tuple(errors),
    )


def _json_object(body: bytes, index: str) -> tuple[dict[str, Any] | None, ParsedPage | None]:
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, _empty_page(index, f"invalid_json:{type(exc).__name__}")
    if not isinstance(payload, dict):
        return None, _empty_page(index, "json_root_not_object")
    return payload, None


def _openalex_position_in(meta: MappingLike) -> str | None:
    x_query = meta.get("x_query")
    if not isinstance(x_query, dict):
        return None
    raw_url = x_query.get("url")
    if not isinstance(raw_url, str):
        return None
    values = parse_qs(urlparse(raw_url).query).get("cursor")
    return values[0] if values else None


MappingLike = dict[str, Any]


def parse_openalex_page(body: bytes) -> ParsedPage:
    payload, failure = _json_object(body, "openalex")
    if failure is not None or payload is None:
        return failure or _empty_page("openalex", "json_root_not_object")
    errors: list[str] = []
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        errors.append("missing_object:meta")
    results_value = payload.get("results")
    if not isinstance(results_value, list):
        results: list[Any] = []
        errors.append("missing_array:results")
    else:
        results = results_value
    total = _parse_int(meta.get("count"), "meta.count", errors)
    capacity = _parse_int(meta.get("per_page"), "meta.per_page", errors)
    meta_page = meta.get("page")
    page_number = meta_page - 1 if isinstance(meta_page, int) and meta_page > 0 else 0
    occurrences: list[Occurrence] = []
    for ordinal, result in enumerate(results):
        if not isinstance(result, dict):
            errors.append(f"result_not_object:results[{ordinal}]")
            result = {}
        work_id = result.get("id")
        if not isinstance(work_id, str) or not work_id:
            errors.append(f"missing_index_work_id:results[{ordinal}].id")
            work_id = ""
        raw_date, interpreted_date, date_reason = _interpret_full_date(
            result.get("publication_date"),
            "missing_openalex_publication_date",
            "invalid_openalex_publication_date",
        )
        ids = result.get("ids")
        ids = ids if isinstance(ids, dict) else {}
        occurrences.append(
            Occurrence(
                index_work_id=work_id,
                page_number=page_number,
                ordinal=ordinal,
                raw_date_value=raw_date,
                interpreted_date=interpreted_date,
                date_missing_reason=date_reason,
                family_keys=_family_keys(
                    (ids.get("arxiv"),),
                    (result.get("doi"), ids.get("doi")),
                ),
            )
        )
    x_query = meta.get("x_query")
    interpreted_query = x_query.get("oql", "") if isinstance(x_query, dict) else ""
    if not isinstance(interpreted_query, str):
        errors.append("invalid_string:meta.x_query.oql")
        interpreted_query = ""
    next_cursor = meta.get("next_cursor")
    if next_cursor is not None and not isinstance(next_cursor, str):
        errors.append("invalid_string:meta.next_cursor")
        next_cursor = None
    return ParsedPage(
        index="openalex",
        declared_total=total,
        capacity_echo=capacity,
        actual_count=len(results),
        interpreted_query=interpreted_query,
        position_in=_openalex_position_in(meta),
        position_out=next_cursor or None,
        occurrences=tuple(occurrences),
        parse_errors=tuple(errors),
    )


def _as_hit_list(value: Any, errors: list[str]) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    errors.append("invalid_hit_collection:result.hits.hit")
    return []


def _flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_strings(item)
    elif isinstance(value, dict):
        for key in ("text", "value", "url"):
            if key in value:
                yield from _flatten_strings(value[key])


def parse_dblp_page(body: bytes) -> ParsedPage:
    payload, failure = _json_object(body, "dblp")
    if failure is not None or payload is None:
        return failure or _empty_page("dblp", "json_root_not_object")
    errors: list[str] = []
    result = payload.get("result")
    if not isinstance(result, dict):
        result = {}
        errors.append("missing_object:result")
    hits = result.get("hits")
    if not isinstance(hits, dict):
        hits = {}
        errors.append("missing_object:result.hits")
    total = _parse_int(hits.get("@total"), "result.hits.@total", errors)
    capacity = _parse_int(hits.get("@sent"), "result.hits.@sent", errors)
    first = _parse_int(hits.get("@first"), "result.hits.@first", errors)
    hit_list = _as_hit_list(hits.get("hit"), errors)
    page_number = first // 100 if first is not None else 0
    occurrences: list[Occurrence] = []
    for ordinal, hit in enumerate(hit_list):
        if not isinstance(hit, dict):
            errors.append(f"hit_not_object:result.hits.hit[{ordinal}]")
            hit = {}
        info = hit.get("info")
        if not isinstance(info, dict):
            errors.append(f"missing_object:result.hits.hit[{ordinal}].info")
            info = {}
        work_id = info.get("key")
        if not isinstance(work_id, str) or not work_id:
            errors.append(f"missing_index_work_id:result.hits.hit[{ordinal}].info.key")
            work_id = ""
        raw_date, interpreted_date, date_reason = _interpret_year(info.get("year"))
        doi_values = [info.get("doi")]
        arxiv_values: list[str] = []
        for external in _flatten_strings(info.get("ee")):
            if "arxiv.org" in external.lower():
                arxiv_values.append(external)
            doi_values.append(external)
        occurrences.append(
            Occurrence(
                index_work_id=work_id,
                page_number=page_number,
                ordinal=ordinal,
                raw_date_value=raw_date,
                interpreted_date=interpreted_date,
                date_missing_reason=date_reason,
                family_keys=_family_keys(arxiv_values, doi_values),
            )
        )
    query_echo = result.get("query")
    if not isinstance(query_echo, str):
        errors.append("invalid_string:result.query")
        query_echo = ""
    position_out: str | None = None
    if first is not None and total is not None and first + len(hit_list) < total:
        position_out = str(first + len(hit_list))
    return ParsedPage(
        index="dblp",
        declared_total=total,
        capacity_echo=capacity,
        actual_count=len(hit_list),
        interpreted_query=query_echo,
        position_in=str(first) if first is not None else None,
        position_out=position_out,
        occurrences=tuple(occurrences),
        parse_errors=tuple(errors),
    )
