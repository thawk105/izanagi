#!/usr/bin/env python3
"""Build and validate the T-189 price snapshot from saved HTML bytes.

This module deliberately has no fetch operation.  The caller supplies the saved
HTML and the acquisition metadata.  The parser derives prices and byte-level
evidence from the HTML; it never treats prose, links, scripts, or footnotes in
that HTML as metadata.

The ``metadata`` mapping accepted by :func:`parse_price_snapshot` is closed and
has these fields::

    requested_url, resolved_url, http, capture_command, captured_at,
    price_table_version, raw_snapshot_path, excerpt_path

``http`` has ``requested`` and ``resolved`` response objects.  Their only
permitted fields are ``status``, ``location``, ``etag``, ``last-modified``, and
``content-type``.  Header values which were not recorded may be omitted.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.dev_waves.schema import (  # noqa: E402
    DEFAULT_MAX_JSON_BYTES,
    DevWavesError,
    canonical_bytes,
    canonical_decimal,
    strict_loads,
)


SCHEMA_VERSION = "t189-price-snapshot/v1"
REQUESTED_URL = "https://platform.openai.com/docs/pricing"
RESOLVED_URL = "https://developers.openai.com/api/docs/pricing"
TIERS = ("standard", "batch", "flex", "fast")
TARGET_MODELS = ("gpt-5.6-sol", "gpt-5.6-luna")
PRICE_CATEGORIES = ("input", "cached_input", "cache_write", "output")
TABLE_COLUMNS = ("Model", "Input", "Cached input", "Cache writes", "Output")

_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_MODEL_RE = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*\Z")
_CATEGORY_RE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_VERSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")
_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z"
)
_VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})
_HTTP_FIELDS = frozenset({
    "status", "location", "etag", "last-modified", "content-type",
})
_METADATA_FIELDS = frozenset({
    "requested_url", "resolved_url", "http", "capture_command", "captured_at",
    "price_table_version", "raw_snapshot_path", "excerpt_path",
})
_ARTIFACT_FIELDS = frozenset({
    "schema_version", "requested_url", "resolved_url", "http",
    "capture_command", "capture_command_status", "captured_at", "effective_at",
    "effective_at_status", "currency", "price_unit", "price_table_version",
    "raw_snapshot", "excerpt", "unknown_token_categories",
    "reasoning_output_tokens_accounting", "sku_mapping",
})
_SKU_FIELDS = frozenset({
    "tier", "context_band", "prices", "receipt_token_mapping",
})
_RECEIPT_TOKEN_MAPPING: dict[str, dict[str, object]] = {
    "input": {
        "receipt_fields": ["input_tokens", "cached_input_tokens"],
        "operation": "input_tokens-minus-cached_input_tokens",
    },
    "cached_input": {
        "receipt_fields": ["cached_input_tokens"],
        "operation": "identity",
    },
    "cache_write": {
        "receipt_fields": [],
        "operation": None,
    },
    "output": {
        "receipt_fields": ["output_tokens"],
        "operation": "identity",
    },
}


class PriceSnapshotError(ValueError):
    """The saved source, caller metadata, or artifact violates the contract."""


@dataclass
class _Frame:
    tag: str
    pane_tier: str | None = None
    pane_start: int | None = None
    target: "_Island | None" = None


@dataclass
class _Island:
    pane_tier: str | None
    pane_start: int | None
    props_text: str
    start: int
    start_tag_end: int
    end: int | None = None
    headers: list[str] | None = None


def _fail(label: str, kind: str) -> "Any":
    raise PriceSnapshotError(f"{label}: {kind}")


def _object(value: object, fields: frozenset[str], *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        return _fail(label, "must be an object")
    if set(value) != fields:
        return _fail(label, "field set mismatch")
    return value


def _copy_json_value(value: object, *, label: str, depth: int = 1) -> object:
    """Copy the ordinary JSON tree while rejecting float/Decimal and NUL."""
    if depth > 32:
        return _fail(label, "nesting depth exceeded")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if "\x00" in value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            return _fail(label, "invalid string")
        return value
    if isinstance(value, int):
        if abs(value) > (1 << 63) - 1:
            return _fail(label, "integer out of range")
        return value
    if isinstance(value, (float, Decimal)):
        return _fail(label, "float and Decimal values are forbidden")
    if isinstance(value, list):
        return [
            _copy_json_value(item, label=f"{label}[{index}]", depth=depth + 1)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or "\x00" in key:
                return _fail(label, "object key must be a NUL-free string")
            result[key] = _copy_json_value(
                item, label=f"{label}.{key}", depth=depth + 1,
            )
        return result
    return _fail(label, "unsupported JSON value")


def _nonempty_string(value: object, *, label: str, maximum: int = 1 << 16) -> str:
    if (not isinstance(value, str) or not value or len(value) > maximum or
            "\x00" in value):
        return _fail(label, "must be a non-empty string")
    return value


def _relative_path(value: object, *, label: str, repository_local: bool) -> str:
    text = _nonempty_string(value, label=label, maximum=4096)
    if "\\" in text:
        return _fail(label, "must use POSIX separators")
    path = PurePosixPath(text)
    if path.is_absolute() or text != path.as_posix() or text == ".":
        return _fail(label, "must be a normalized relative path")
    if repository_local and ".." in path.parts:
        return _fail(label, "repository excerpt path may not escape the repository")
    if not repository_local and (not path.parts or path.parts[0] != ".."):
        return _fail(label, "external raw path must escape the repository")
    return text


def _timestamp(value: object, *, label: str) -> str:
    text = _nonempty_string(value, label=label, maximum=64)
    if not _TIMESTAMP_RE.fullmatch(text):
        return _fail(label, "must be an RFC3339 UTC timestamp")
    try:
        datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return _fail(label, "invalid timestamp")
    return text


def _optional_header(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, label=label, maximum=1 << 16)


def _validate_http(
    value: object, *, requested_url: str, resolved_url: str,
) -> dict[str, object]:
    item = _object(value, frozenset({"requested", "resolved"}), label="http")
    result: dict[str, object] = {}
    for name, required_status in (("requested", 301), ("resolved", 200)):
        response = item[name]
        if not isinstance(response, dict):
            return _fail(f"http.{name}", "must be an object")
        if not set(response) <= _HTTP_FIELDS or "status" not in response:
            return _fail(f"http.{name}", "contains missing or forbidden header fields")
        status = response["status"]
        if (not isinstance(status, int) or isinstance(status, bool) or
                status != required_status):
            return _fail(f"http.{name}.status", f"must be {required_status}")
        normalized: dict[str, object] = {"status": status}
        for header in ("location", "etag", "last-modified", "content-type"):
            if header in response:
                normalized[header] = _optional_header(
                    response[header], label=f"http.{name}.{header}",
                )
        result[name] = normalized
    requested = result["requested"]
    resolved = result["resolved"]
    assert isinstance(requested, dict) and isinstance(resolved, dict)
    if requested.get("location") != resolved_url:
        return _fail("http.requested.location", "must equal resolved_url")
    if resolved.get("location") not in (None,):
        return _fail("http.resolved.location", "final response may not redirect")
    if requested_url != REQUESTED_URL or resolved_url != RESOLVED_URL:
        return _fail("http", "URL binding mismatch")
    return result


class _PricingHTMLParser(HTMLParser):
    """Collect target islands, their enclosing pane, and exact byte bounds."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self._text = text
        self._line_starts = [0]
        for line in text.splitlines(keepends=True):
            self._line_starts.append(self._line_starts[-1] + len(line))
        self._stack: list[_Frame] = []
        self._th_parts: list[str] | None = None
        self.islands: list[_Island] = []

    def _character_offset(self) -> int:
        line, column = self.getpos()
        if line < 1 or line > len(self._line_starts):
            return _fail("html", "parser position is outside source")
        return self._line_starts[line - 1] + column

    def _byte_offset(self, character_offset: int) -> int:
        return len(self._text[:character_offset].encode("utf-8"))

    def _active_target(self) -> _Island | None:
        for frame in reversed(self._stack):
            if frame.target is not None:
                return frame.target
        return None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = [name for name, _ in attrs]
        if len(names) != len(set(names)):
            return _fail("html", "duplicate attribute")
        attributes = dict(attrs)
        start_text = self.get_starttag_text()
        if start_text is None:
            return _fail("html", "missing start tag text")
        char_start = self._character_offset()
        start = self._byte_offset(char_start)
        start_tag_end = self._byte_offset(char_start + len(start_text))

        pane_tier: str | None = None
        pane_start: int | None = None
        if tag == "div" and attributes.get("data-content-switcher-pane") == "true":
            pane_tier = attributes.get("data-value")
            pane_start = start
        frame = _Frame(tag=tag, pane_tier=pane_tier, pane_start=pane_start)
        self._stack.append(frame)

        if (tag == "astro-island" and
                attributes.get("component-export") == "TextTokenPricingTables"):
            containing = next(
                (candidate for candidate in reversed(self._stack[:-1])
                 if candidate.pane_tier is not None),
                None,
            )
            props_text = attributes.get("props")
            if props_text is None:
                return _fail("html", "pricing island has no props")
            island = _Island(
                pane_tier=None if containing is None else containing.pane_tier,
                pane_start=None if containing is None else containing.pane_start,
                props_text=props_text,
                start=start,
                start_tag_end=start_tag_end,
                headers=[],
            )
            frame.target = island
            self.islands.append(island)

        if tag == "th" and self._active_target() is not None:
            if self._th_parts is not None:
                return _fail("html", "nested table header")
            self._th_parts = []

        if tag in _VOID_ELEMENTS:
            self._stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self._stack and self._stack[-1].tag == tag:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._th_parts is not None:
            self._th_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "th" and self._th_parts is not None:
            target = self._active_target()
            if target is None or target.headers is None:
                return _fail("html", "table header outside pricing island")
            target.headers.append(" ".join("".join(self._th_parts).split()))
            self._th_parts = None

        matching_index = next(
            (index for index in range(len(self._stack) - 1, -1, -1)
             if self._stack[index].tag == tag),
            None,
        )
        if matching_index is None:
            return
        frame = self._stack[matching_index]
        if tag == "astro-island" and frame.target is not None:
            char_start = self._character_offset()
            char_end = self._text.find(">", char_start)
            if char_end < 0:
                return _fail("html", "unterminated pricing island")
            frame.target.end = self._byte_offset(char_end + 1)
        del self._stack[matching_index:]


def _strict_props(raw: str, *, label: str) -> dict[str, object]:
    try:
        value = strict_loads(
            raw.encode("utf-8"), label=label, max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    except (DevWavesError, UnicodeEncodeError):
        return _fail(label, "props must be strict JSON")
    if not isinstance(value, dict):
        return _fail(label, "props must be an object")
    return value


def _tagged_scalar(value: object, *, label: str) -> object:
    if not isinstance(value, list) or len(value) != 2 or value[0] != 0:
        return _fail(label, "must be an Astro tagged scalar")
    return value[1]


def _rows(value: object, *, label: str) -> list[object]:
    if not isinstance(value, list) or len(value) != 2 or value[0] != 1:
        return _fail(label, "must be an Astro tagged row list")
    if not isinstance(value[1], list):
        return _fail(label, "row payload must be a list")
    return value[1]


def _source_price(value: object, *, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        return _fail(label, "price must be a JSON number")
    number = Decimal(value) if isinstance(value, int) else value
    if not number.is_finite() or number <= 0:
        return _fail(label, "price must be finite and positive")
    try:
        return canonical_decimal(number)
    except ValueError:
        return _fail(label, "price is outside the canonical decimal grammar")


def _extract_target_prices(props: dict[str, object], *, tier: str) -> dict[str, dict[str, str]]:
    source_rows = _rows(props.get("rows"), label=f"{tier}.rows")
    found: dict[str, dict[str, str]] = {}
    for row_index, row in enumerate(source_rows):
        label = f"{tier}.rows[{row_index}]"
        if not isinstance(row, list) or len(row) != 2 or row[0] != 1:
            return _fail(label, "must be an Astro tagged row")
        cells = row[1]
        if not isinstance(cells, list) or not cells:
            return _fail(label, "row cells must be a non-empty list")
        model = _tagged_scalar(cells[0], label=f"{label}.model")
        if not isinstance(model, str):
            return _fail(f"{label}.model", "must be a string")
        if model not in TARGET_MODELS:
            continue
        if model in found:
            return _fail(label, "duplicate target model row")
        if len(cells) != len(PRICE_CATEGORIES) + 1:
            return _fail(label, "target row is missing a price category")
        prices: dict[str, str] = {}
        for column, category in enumerate(PRICE_CATEGORIES, start=1):
            raw_price = _tagged_scalar(
                cells[column], label=f"{label}.{category}",
            )
            prices[category] = _source_price(
                raw_price, label=f"{label}.{category}",
            )
        found[model] = prices
    return found


def _has_expected_columns(headers: list[str] | None) -> bool:
    if headers is None:
        return False
    width = len(TABLE_COLUMNS)
    return any(tuple(headers[index:index + width]) == TABLE_COLUMNS
               for index in range(len(headers) - width + 1))


def _parse_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    copied = _copy_json_value(dict(metadata), label="metadata")
    item = _object(copied, _METADATA_FIELDS, label="metadata")
    requested_url = _nonempty_string(item["requested_url"], label="requested_url")
    resolved_url = _nonempty_string(item["resolved_url"], label="resolved_url")
    if requested_url != REQUESTED_URL or resolved_url != RESOLVED_URL:
        return _fail("metadata", "requested_url or resolved_url mismatch")
    version = _nonempty_string(
        item["price_table_version"], label="price_table_version", maximum=256,
    )
    if not _VERSION_RE.fullmatch(version):
        return _fail("price_table_version", "invalid identifier")
    return {
        "requested_url": requested_url,
        "resolved_url": resolved_url,
        "http": _validate_http(
            item["http"], requested_url=requested_url, resolved_url=resolved_url,
        ),
        "capture_command": _nonempty_string(
            item["capture_command"], label="capture_command",
        ),
        "captured_at": _timestamp(item["captured_at"], label="captured_at"),
        "price_table_version": version,
        "raw_snapshot_path": _relative_path(
            item["raw_snapshot_path"], label="raw_snapshot_path",
            repository_local=False,
        ),
        "excerpt_path": _relative_path(
            item["excerpt_path"], label="excerpt_path", repository_local=True,
        ),
    }


def parse_price_snapshot(
    raw_html: bytes, *, metadata: Mapping[str, object],
) -> dict[str, object]:
    """Parse saved pricing HTML and return a validated Standard-tier artifact."""
    if not isinstance(raw_html, bytes):
        raise TypeError("raw_html must be bytes")
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")
    if not raw_html:
        return _fail("raw_html", "must not be empty")
    if b"\x00" in raw_html:
        return _fail("raw_html", "contains NUL")
    try:
        text = raw_html.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _fail("raw_html", "must be valid UTF-8")

    normalized_metadata = _parse_metadata(metadata)
    parser = _PricingHTMLParser(text)
    try:
        parser.feed(text)
        parser.close()
    except (PriceSnapshotError, RecursionError):
        raise

    by_tier: dict[str, tuple[_Island, dict[str, object]]] = {}
    for index, island in enumerate(parser.islands):
        label = f"pricing_island[{index}]"
        if island.pane_tier not in TIERS or island.pane_start is None:
            return _fail(label, "must be nested in a known pricing pane")
        props = _strict_props(island.props_text, label=f"{label}.props")
        props_tier = _tagged_scalar(props.get("tier"), label=f"{label}.tier")
        if props_tier != island.pane_tier:
            return _fail(label, "pane tier and props tier differ")
        if props_tier in by_tier:
            return _fail(label, "duplicate pricing tier")
        if island.end is None:
            return _fail(label, "pricing island is not closed")
        by_tier[props_tier] = (island, props)
    if set(by_tier) != set(TIERS):
        return _fail("raw_html", "must contain exactly one pricing island for every tier")

    standard_island, standard_props = by_tier["standard"]
    if not _has_expected_columns(standard_island.headers):
        return _fail("standard.headers", "price column order mismatch")
    prices = _extract_target_prices(standard_props, tier="standard")
    if set(prices) != set(TARGET_MODELS):
        return _fail("standard.rows", "required Standard model row missing")

    assert standard_island.pane_start is not None and standard_island.end is not None
    excerpt_offset = standard_island.pane_start
    excerpt_length = standard_island.end - excerpt_offset
    if excerpt_length <= 0:
        return _fail("excerpt", "invalid byte bounds")
    excerpt = raw_html[excerpt_offset:standard_island.end]
    sku_mapping = {
        model: {
            "tier": "standard",
            "context_band": "short-context",
            "prices": prices[model],
            "receipt_token_mapping": _copy_json_value(
                _RECEIPT_TOKEN_MAPPING, label="receipt_token_mapping",
            ),
        }
        for model in TARGET_MODELS
    }
    artifact: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "requested_url": normalized_metadata["requested_url"],
        "resolved_url": normalized_metadata["resolved_url"],
        "http": normalized_metadata["http"],
        "capture_command": normalized_metadata["capture_command"],
        "capture_command_status": "recorded-exact",
        "captured_at": normalized_metadata["captured_at"],
        "effective_at": None,
        "effective_at_status": "not-published-in-source",
        "currency": "USD",
        "price_unit": "per-million-tokens",
        "price_table_version": normalized_metadata["price_table_version"],
        "raw_snapshot": {
            "storage": "outside-repository",
            "path": normalized_metadata["raw_snapshot_path"],
            "sha256": hashlib.sha256(raw_html).hexdigest(),
            "byte_length": len(raw_html),
        },
        "excerpt": {
            "storage": "repository",
            "path": normalized_metadata["excerpt_path"],
            "sha256": hashlib.sha256(excerpt).hexdigest(),
            "byte_offset": excerpt_offset,
            "byte_length": excerpt_length,
        },
        "unknown_token_categories": ["cache_write"],
        "reasoning_output_tokens_accounting": (
            "included-in-output_tokens-not-added-separately"
        ),
        "sku_mapping": sku_mapping,
    }
    return validate_price_snapshot(artifact)


def _validate_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not _HEX64_RE.fullmatch(value):
        return _fail(label, "must be a lowercase sha256")
    return value


def _positive_int(value: object, *, label: str, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if (not isinstance(value, int) or isinstance(value, bool) or value < minimum):
        return _fail(label, "must be an integer in range")
    return value


def _validate_record(value: object, *, label: str, excerpt: bool) -> dict[str, object]:
    fields = ({"storage", "path", "sha256", "byte_offset", "byte_length"}
              if excerpt else {"storage", "path", "sha256", "byte_length"})
    item = _object(value, frozenset(fields), label=label)
    expected_storage = "repository" if excerpt else "outside-repository"
    if item["storage"] != expected_storage:
        return _fail(f"{label}.storage", "storage scope mismatch")
    result: dict[str, object] = {
        "storage": expected_storage,
        "path": _relative_path(
            item["path"], label=f"{label}.path", repository_local=excerpt,
        ),
        "sha256": _validate_digest(item["sha256"], label=f"{label}.sha256"),
        "byte_length": _positive_int(
            item["byte_length"], label=f"{label}.byte_length",
        ),
    }
    if excerpt:
        result["byte_offset"] = _positive_int(
            item["byte_offset"], label=f"{label}.byte_offset", allow_zero=True,
        )
        # Preserve the artifact's fixed field spelling while returning a fresh tree.
        return {
            "storage": result["storage"], "path": result["path"],
            "sha256": result["sha256"], "byte_offset": result["byte_offset"],
            "byte_length": result["byte_length"],
        }
    return result


def _validate_receipt_mapping(value: object, *, label: str) -> dict[str, object]:
    item = _object(value, frozenset(PRICE_CATEGORIES), label=label)
    expected = _RECEIPT_TOKEN_MAPPING
    if item != expected:
        return _fail(label, "receipt token accounting mismatch")
    copied = _copy_json_value(expected, label=label)
    assert isinstance(copied, dict)
    return copied


def _validate_prices(value: object, *, label: str) -> dict[str, str]:
    item = _object(value, frozenset(PRICE_CATEGORIES), label=label)
    result: dict[str, str] = {}
    for category in PRICE_CATEGORIES:
        price = item[category]
        if not isinstance(price, str):
            return _fail(f"{label}.{category}", "price must be a decimal string")
        try:
            number = Decimal(price)
        except InvalidOperation:
            return _fail(f"{label}.{category}", "invalid decimal string")
        if not number.is_finite() or number <= 0:
            return _fail(f"{label}.{category}", "price must be finite and positive")
        try:
            canonical = canonical_decimal(number)
        except ValueError:
            return _fail(f"{label}.{category}", "invalid decimal string")
        if price != canonical:
            return _fail(f"{label}.{category}", "price must be canonical")
        result[category] = price
    return result


def validate_price_snapshot(value: object) -> dict[str, object]:
    """Validate the closed price snapshot schema and return a fresh JSON tree."""
    copied = _copy_json_value(value, label="price_snapshot")
    item = _object(copied, _ARTIFACT_FIELDS, label="price_snapshot")
    if item["schema_version"] != SCHEMA_VERSION:
        return _fail("schema_version", "unsupported version")
    if item["requested_url"] != REQUESTED_URL or item["resolved_url"] != RESOLVED_URL:
        return _fail("price_snapshot", "required source URLs are missing")
    requested_url = str(item["requested_url"])
    resolved_url = str(item["resolved_url"])
    http = _validate_http(
        item["http"], requested_url=requested_url, resolved_url=resolved_url,
    )
    command = _nonempty_string(item["capture_command"], label="capture_command")
    if item["capture_command_status"] != "recorded-exact":
        return _fail("capture_command_status", "must be recorded-exact")
    captured_at = _timestamp(item["captured_at"], label="captured_at")
    if item["effective_at"] is not None:
        return _fail("effective_at", "must be null")
    if item["effective_at_status"] != "not-published-in-source":
        return _fail(
            "effective_at_status", "must be not-published-in-source",
        )
    if item["currency"] != "USD" or item["price_unit"] != "per-million-tokens":
        return _fail("price_snapshot", "currency or price unit mismatch")
    version = _nonempty_string(
        item["price_table_version"], label="price_table_version", maximum=256,
    )
    if not _VERSION_RE.fullmatch(version):
        return _fail("price_table_version", "invalid identifier")

    raw_record = _validate_record(item["raw_snapshot"], label="raw_snapshot", excerpt=False)
    excerpt_record = _validate_record(item["excerpt"], label="excerpt", excerpt=True)
    raw_length = raw_record["byte_length"]
    excerpt_offset = excerpt_record["byte_offset"]
    excerpt_length = excerpt_record["byte_length"]
    assert isinstance(raw_length, int)
    assert isinstance(excerpt_offset, int) and isinstance(excerpt_length, int)
    if excerpt_offset + excerpt_length > raw_length:
        return _fail("excerpt", "byte range exceeds raw snapshot")

    unknown = item["unknown_token_categories"]
    if not isinstance(unknown, list) or not unknown:
        return _fail("unknown_token_categories", "must be a non-empty list")
    normalized_unknown: list[str] = []
    for index, category in enumerate(unknown):
        if (not isinstance(category, str) or not _CATEGORY_RE.fullmatch(category) or
                category in normalized_unknown):
            return _fail(
                f"unknown_token_categories[{index}]", "invalid or duplicate category",
            )
        normalized_unknown.append(category)
    if "cache_write" not in normalized_unknown:
        return _fail("unknown_token_categories", "must contain cache_write")
    normalized_unknown.sort()
    if item["reasoning_output_tokens_accounting"] != (
            "included-in-output_tokens-not-added-separately"):
        return _fail(
            "reasoning_output_tokens_accounting", "double-counting guard mismatch",
        )

    mapping = item["sku_mapping"]
    if not isinstance(mapping, dict) or not mapping:
        return _fail("sku_mapping", "must be a non-empty object")
    normalized_mapping: dict[str, object] = {}
    for model, raw_sku in mapping.items():
        if not isinstance(model, str) or not _MODEL_RE.fullmatch(model):
            return _fail("sku_mapping", "invalid model slug")
        sku = _object(raw_sku, _SKU_FIELDS, label=f"sku_mapping.{model}")
        if sku["tier"] != "standard":
            return _fail(f"sku_mapping.{model}.tier", "only standard is accepted")
        if sku["context_band"] != "short-context":
            return _fail(f"sku_mapping.{model}.context_band", "must be short-context")
        normalized_mapping[model] = {
            "tier": "standard",
            "context_band": "short-context",
            "prices": _validate_prices(
                sku["prices"], label=f"sku_mapping.{model}.prices",
            ),
            "receipt_token_mapping": _validate_receipt_mapping(
                sku["receipt_token_mapping"],
                label=f"sku_mapping.{model}.receipt_token_mapping",
            ),
        }

    result: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "requested_url": requested_url,
        "resolved_url": resolved_url,
        "http": http,
        "capture_command": command,
        "capture_command_status": "recorded-exact",
        "captured_at": captured_at,
        "effective_at": None,
        "effective_at_status": "not-published-in-source",
        "currency": "USD",
        "price_unit": "per-million-tokens",
        "price_table_version": version,
        "raw_snapshot": raw_record,
        "excerpt": excerpt_record,
        "unknown_token_categories": normalized_unknown,
        "reasoning_output_tokens_accounting": (
            "included-in-output_tokens-not-added-separately"
        ),
        "sku_mapping": normalized_mapping,
    }
    try:
        canonical_bytes(result)
    except (TypeError, ValueError):
        return _fail("price_snapshot", "is not canonical JSON data")
    return result


def price_snapshot_bytes(value: object) -> bytes:
    """Return canonical UTF-8 JSON with exactly one trailing LF."""
    return canonical_bytes(validate_price_snapshot(value)) + b"\n"


def _load_metadata(path: Path) -> Mapping[str, object]:
    try:
        raw = path.read_bytes()
        value = strict_loads(
            raw, label="price-metadata", max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    except (OSError, DevWavesError) as exc:
        raise PriceSnapshotError("metadata file is unreadable or not strict JSON") from exc
    if not isinstance(value, dict):
        raise PriceSnapshotError("metadata top level must be an object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="parse a saved T-189 pricing HTML snapshot; never fetches",
    )
    parser.add_argument("raw_html", type=Path)
    parser.add_argument("metadata_json", type=Path)
    args = parser.parse_args(argv)
    try:
        raw_html = args.raw_html.read_bytes()
        metadata = _load_metadata(args.metadata_json)
        output = price_snapshot_bytes(
            parse_price_snapshot(raw_html, metadata=metadata),
        )
    except (OSError, PriceSnapshotError, TypeError, ValueError) as exc:
        print(f"t189_price_snapshot: {exc}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PriceSnapshotError", "main", "parse_price_snapshot",
    "price_snapshot_bytes", "validate_price_snapshot",
]
