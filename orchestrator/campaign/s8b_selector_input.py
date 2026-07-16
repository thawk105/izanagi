# -*- coding: utf-8 -*-
"""段 8b selector の固定 catalog と descriptor-only 入力を構築する。

``CHOICE_TO_BINDING`` は予測後に信頼中核だけが使う対応表である。binding key や
この対応表を selector payload へ渡してはいけない。
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from . import s8b_descriptor


class SelectorInputError(RuntimeError):
    """selector catalog または入力 payload の契約違反。"""


CHOICE_TO_BINDING: dict = {
    "c01": "p2_2_flag_opt",
    "c02": "backoff_fixed_best",
    "c03": "sort_best",
    "c04": "system_gate",
    "c05": "ident_all",
    "c06": "stock_common",
}

STATIC_DEFAULT_CHOICE_ID = "c06"

_EXPECTED_CATALOG = {
    "schema_version": "8b-selector-catalog/v1",
    "candidates": [
        {"choice_id": "c01", "mechanism": "protocol_flag_bundle"},
        {"choice_id": "c02", "mechanism": "fixed_abort_backoff"},
        {"choice_id": "c03", "mechanism": "write_set_ordering"},
        {"choice_id": "c04", "mechanism": "subset_abort_reason_gate"},
        {"choice_id": "c05", "mechanism": "all_abort_reason_gate"},
        {"choice_id": "c06", "mechanism": "upstream_defaults"},
    ],
}

_CATALOG_PATH = Path(__file__).resolve().with_name("s8b_selector_catalog.json")
_PAYLOAD_KEYS = {"schema_version", "descriptor", "candidates"}
_EXPECTED_CATALOG_CANONICAL_SHA256 = hashlib.sha256(
    json.dumps(
        _EXPECTED_CATALOG, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
    except (TypeError, ValueError) as exc:
        raise SelectorInputError("canonical JSON に変換できない") from exc
    return encoded.encode("utf-8")


def _reject_duplicate_keys(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise SelectorInputError(f"selector catalog に duplicate key がある: {key}")
        value[key] = child
    return value


def load_catalog() -> dict:
    """凍結 catalog を読み、6候補を含む逐語構造との完全一致を要求する。"""
    try:
        with _CATALOG_PATH.open(encoding="utf-8") as stream:
            catalog = json.load(stream, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SelectorInputError("selector catalog を読めない: %s" % _CATALOG_PATH) from exc

    if catalog != _EXPECTED_CATALOG:
        raise SelectorInputError("selector catalog が凍結済み逐語構造と一致しない")
    if hashlib.sha256(_canonical_bytes(catalog)).hexdigest() != (
            _EXPECTED_CATALOG_CANONICAL_SHA256):
        raise SelectorInputError("selector catalog の凍結 canonical hash が不一致")

    candidates = catalog["candidates"]
    choice_ids = [candidate["choice_id"] for candidate in candidates]
    expected_ids = [candidate["choice_id"] for candidate in _EXPECTED_CATALOG["candidates"]]
    if len(candidates) != 6 or len(set(choice_ids)) != 6 or choice_ids != expected_ids:
        raise SelectorInputError("selector catalog の件数・ID 一意性・順序が不正")
    return copy.deepcopy(catalog)


def _validate_descriptor(descriptor: Any) -> None:
    # validate_descriptor 自身も禁止キー走査を行うが、builder 契約上の二段 gate を
    # 明示し、将来 descriptor 側の内部実装が変わっても独立走査を残す。
    s8b_descriptor.validate_descriptor(descriptor)
    s8b_descriptor.scan_forbidden_keys(descriptor)


def build_selector_payload(descriptor) -> dict:
    """検証済み descriptor と固定6候補だけから selector 入力を構築する。"""
    _validate_descriptor(descriptor)
    catalog = load_catalog()
    payload = {
        "schema_version": "8b-selector-input/v1",
        "descriptor": copy.deepcopy(descriptor),
        "candidates": catalog["candidates"],
    }
    return payload


def validate_selector_payload(payload) -> None:
    """selector input の追加フィールド、catalog 差異、descriptor 違反を拒否する。"""
    if not isinstance(payload, dict):
        raise SelectorInputError("selector payload は object でなければならない")
    if set(payload) != _PAYLOAD_KEYS:
        missing = sorted(_PAYLOAD_KEYS - set(payload))
        unknown = sorted(set(payload) - _PAYLOAD_KEYS)
        raise SelectorInputError(
            "selector payload のキーが不正: missing=%r unknown=%r" % (missing, unknown)
        )
    if payload["schema_version"] != "8b-selector-input/v1":
        raise SelectorInputError("selector payload schema_version が不正")

    catalog = load_catalog()
    if _canonical_bytes(payload["candidates"]) != _canonical_bytes(catalog["candidates"]):
        raise SelectorInputError("selector payload candidates が凍結 catalog と一致しない")
    _validate_descriptor(payload["descriptor"])


def selector_payload_sha256(payload) -> str:
    """検証済み selector payload の canonical JSON SHA-256 を返す。"""
    validate_selector_payload(payload)
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()
