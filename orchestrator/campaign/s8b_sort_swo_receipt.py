# -*- coding: utf-8 -*-
"""Portable な sort SWO PASS receipt の射影と検証。

保証境界: この receipt は「床値 record がどの oracle 実行 receipt を主張しているか」
の durable な辺であって、oracle が実際に走ったことの証明ではない。receipt の全 field
は公開かつ決定的で、oracle を実行せずに合成できる。``receipt_sha256`` は private
evidence への commitment であり、raw receipt が到達可能な環境でだけ検算できる。
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json

from .sort_swo_oracle import (
    COMPILE_FLAGS_SHA256,
    CORPUS_ID,
    CORPUS_VERSION,
    DEPENDENCY_MANIFEST_SHA256,
    ORACLE_CONTRACT_ID,
    TU_TEMPLATE_SHA256,
)


__all__ = (
    "PORTABLE_SORT_SWO_RECEIPT_SCHEMA",
    "SortSwoReceiptError",
    "project_sort_swo_pass_attempt",
    "validate_portable_sort_swo_pass_receipt",
)


PORTABLE_SORT_SWO_RECEIPT_SCHEMA = "s8b-sort-swo-pass-receipt/v2"

_ATTEMPT_KEYS = frozenset({
    "event", "classification", "reason_code", "oracle_contract_id",
    "materialized_hole_sha256", "proposal_sha256", "oracle_receipt",
})
_RAW_RECEIPT_KEYS = frozenset({
    "contract_id", "materialized_hole_sha256", "proposal_sha256", "corpus_id",
    "corpus_version", "compiler_realpath", "compiler_version",
    "compile_flags_sha256", "tu_sha256", "tu_template_sha256",
    "dependency_root_realpath", "dependency_config_sha256",
    "dependency_manifest_sha256",
})
_PORTABLE_KEYS = frozenset({
    "schema", "cell_id", "holdout_id", "configuration_id", "entry_sha256",
    "binary_sha256", "classification", "reason_code", "oracle_contract_id",
    "materialized_hole_sha256", "proposal_sha256", "corpus_id",
    "corpus_version", "compiler_version_sha256", "compile_flags_sha256",
    "tu_sha256", "tu_template_sha256", "dependency_config_sha256",
    "dependency_manifest_sha256", "receipt_sha256",
})
_HEX64 = frozenset("0123456789abcdef")


class SortSwoReceiptError(ValueError):
    """Portable SWO PASS receipt を射影または検証できない。"""


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SortSwoReceiptError("receipt を canonical JSON に変換できない") from exc


def _plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(child) for child in value]
    return value


def _exact_mapping(value: object, keys: frozenset[str], label: str) -> Mapping:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise SortSwoReceiptError(f"{label} の exact key 集合が不一致")
    return value


def _require_text(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise SortSwoReceiptError(f"{label} が空でない str でない")
    return value


def _require_sha256(value: object, label: str) -> str:
    text = _require_text(value, label)
    if len(text) != 64 or any(char not in _HEX64 for char in text):
        raise SortSwoReceiptError(f"{label} が lowercase SHA-256 でない")
    return text


def _validate_identity(
    *, cell_id: object, holdout_id: object, configuration_id: object,
    entry_sha256: object, binary_sha256: object,
) -> None:
    _require_text(cell_id, "cell_id")
    _require_text(holdout_id, "holdout_id")
    _require_text(configuration_id, "configuration_id")
    if configuration_id != "sort_best":
        raise SortSwoReceiptError("configuration identity が sort_best でない")
    _require_sha256(entry_sha256, "entry_sha256")
    _require_sha256(binary_sha256, "binary_sha256")


def _validate_fixed_receipt_fields(value: Mapping[str, object]) -> None:
    if value["classification"] != "pass":
        raise SortSwoReceiptError("classification が pass でない")
    if value["reason_code"] != "sort-swo-oracle-pass":
        raise SortSwoReceiptError("reason_code が PASS 固定値でない")
    if value["oracle_contract_id"] != ORACLE_CONTRACT_ID:
        raise SortSwoReceiptError("oracle_contract_id が現行 contract と不一致")
    if value["corpus_id"] != CORPUS_ID or value["corpus_version"] != CORPUS_VERSION:
        raise SortSwoReceiptError("corpus identity が現行 oracle と不一致")
    if value["compile_flags_sha256"] != COMPILE_FLAGS_SHA256:
        raise SortSwoReceiptError("compile_flags_sha256 が現行 oracle と不一致")
    if value["tu_template_sha256"] != TU_TEMPLATE_SHA256:
        raise SortSwoReceiptError("tu_template_sha256 が現行 oracle と不一致")
    if value["dependency_manifest_sha256"] != DEPENDENCY_MANIFEST_SHA256:
        raise SortSwoReceiptError("dependency_manifest_sha256 が現行 oracle と不一致")
    for key in (
        "materialized_hole_sha256", "proposal_sha256", "compiler_version_sha256",
        "compile_flags_sha256", "tu_sha256", "tu_template_sha256",
        "dependency_config_sha256", "dependency_manifest_sha256",
        "receipt_sha256",
    ):
        _require_sha256(value[key], key)


def project_sort_swo_pass_attempt(
    attempt: object, *, cell_id: str, holdout_id: str, configuration_id: str,
    entry_sha256: str, binary_sha256: str,
) -> dict[str, object]:
    """raw PASS attempt を identity 束縛済み portable receipt へ射影する。

    保証境界: この receipt は「床値 record がどの oracle 実行 receipt を主張しているか」
    の durable な辺であって、oracle が実際に走ったことの証明ではない。receipt の全 field
    は公開かつ決定的で、oracle を実行せずに合成できる。``receipt_sha256`` は private
    evidence への commitment であり、raw receipt が到達可能な環境でだけ検算できる。
    """

    _validate_identity(
        cell_id=cell_id, holdout_id=holdout_id,
        configuration_id=configuration_id, entry_sha256=entry_sha256,
        binary_sha256=binary_sha256,
    )
    outer = _exact_mapping(attempt, _ATTEMPT_KEYS, "sort SWO attempt")
    if outer["event"] != "sort-swo-oracle-attempt":
        raise SortSwoReceiptError("attempt.event が不一致")
    raw = _exact_mapping(outer["oracle_receipt"], _RAW_RECEIPT_KEYS, "oracle_receipt")
    if outer["classification"] != "pass" or outer["reason_code"] != "sort-swo-oracle-pass":
        raise SortSwoReceiptError("attempt が PASS でない")
    if outer["oracle_contract_id"] != raw["contract_id"]:
        raise SortSwoReceiptError("outer/nested oracle contract が不一致")
    for key in ("materialized_hole_sha256", "proposal_sha256"):
        if outer[key] != raw[key]:
            raise SortSwoReceiptError(f"outer/nested {key} が不一致")
    if raw["contract_id"] != ORACLE_CONTRACT_ID:
        raise SortSwoReceiptError("raw receipt contract が現行 oracle と不一致")
    if raw["corpus_id"] != CORPUS_ID or raw["corpus_version"] != CORPUS_VERSION:
        raise SortSwoReceiptError("raw receipt corpus が現行 oracle と不一致")
    if raw["compile_flags_sha256"] != COMPILE_FLAGS_SHA256:
        raise SortSwoReceiptError("raw receipt flags が現行 oracle と不一致")
    if raw["tu_template_sha256"] != TU_TEMPLATE_SHA256:
        raise SortSwoReceiptError("raw receipt TU template が現行 oracle と不一致")
    _require_text(raw["compiler_realpath"], "compiler_realpath")
    compiler_version = _require_text(raw["compiler_version"], "compiler_version")
    _require_text(raw["dependency_root_realpath"], "dependency_root_realpath")
    for key in (
        "materialized_hole_sha256", "proposal_sha256", "compile_flags_sha256",
        "tu_sha256", "tu_template_sha256", "dependency_config_sha256",
        "dependency_manifest_sha256",
    ):
        _require_sha256(raw[key], f"oracle_receipt.{key}")

    portable: dict[str, object] = {
        "schema": PORTABLE_SORT_SWO_RECEIPT_SCHEMA,
        "cell_id": cell_id,
        "holdout_id": holdout_id,
        "configuration_id": configuration_id,
        "entry_sha256": entry_sha256,
        "binary_sha256": binary_sha256,
        "classification": "pass",
        "reason_code": "sort-swo-oracle-pass",
        "oracle_contract_id": raw["contract_id"],
        "materialized_hole_sha256": raw["materialized_hole_sha256"],
        "proposal_sha256": raw["proposal_sha256"],
        "corpus_id": raw["corpus_id"],
        "corpus_version": raw["corpus_version"],
        "compiler_version_sha256": hashlib.sha256(
            compiler_version.encode("utf-8")
        ).hexdigest(),
        "compile_flags_sha256": raw["compile_flags_sha256"],
        "tu_sha256": raw["tu_sha256"],
        "tu_template_sha256": raw["tu_template_sha256"],
        "dependency_config_sha256": raw["dependency_config_sha256"],
        "dependency_manifest_sha256": raw["dependency_manifest_sha256"],
        "receipt_sha256": hashlib.sha256(
            _canonical_bytes(_plain_json(raw))
        ).hexdigest(),
    }
    _validate_fixed_receipt_fields(portable)
    return json.loads(_canonical_bytes(portable))


def validate_portable_sort_swo_pass_receipt(
    value: object, *, expected_cell_id: str, expected_holdout_id: str,
    expected_configuration_id: str, expected_entry_sha256: str,
    expected_binary_sha256: str,
) -> dict[str, object]:
    """portable receipt の exact shape、oracle 定数、identity 束縛を検証する。

    保証境界: この receipt は「床値 record がどの oracle 実行 receipt を主張しているか」
    の durable な辺であって、oracle が実際に走ったことの証明ではない。receipt の全 field
    は公開かつ決定的で、oracle を実行せずに合成できる。``receipt_sha256`` は private
    evidence への commitment であり、raw receipt が到達可能な環境でだけ検算できる。
    """

    if isinstance(value, Mapping) and (
        "compiler_realpath" in value or "dependency_root_realpath" in value
        or "compiler_version" in value
    ):
        raise SortSwoReceiptError("portable receipt への raw compiler/path field 混入")
    receipt = _exact_mapping(value, _PORTABLE_KEYS, "portable sort SWO receipt")
    if receipt["schema"] != PORTABLE_SORT_SWO_RECEIPT_SCHEMA:
        raise SortSwoReceiptError("portable receipt schema が不一致")
    _validate_identity(
        cell_id=receipt["cell_id"], holdout_id=receipt["holdout_id"],
        configuration_id=receipt["configuration_id"],
        entry_sha256=receipt["entry_sha256"],
        binary_sha256=receipt["binary_sha256"],
    )
    expected = (
        expected_cell_id, expected_holdout_id, expected_configuration_id,
        expected_entry_sha256, expected_binary_sha256,
    )
    actual = tuple(receipt[key] for key in (
        "cell_id", "holdout_id", "configuration_id", "entry_sha256", "binary_sha256",
    ))
    if actual != expected:
        raise SortSwoReceiptError("portable receipt identity が外部期待値と不一致")
    _validate_fixed_receipt_fields(receipt)
    return json.loads(_canonical_bytes(_plain_json(receipt)))
