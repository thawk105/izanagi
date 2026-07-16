# -*- coding: utf-8 -*-
"""段 8b workload descriptor の決定論射影と fails-closed 検証。

生成元 ``campaign_search_config_projection`` だけを本モジュールで実装する。
設計書 §2.2 の第二の生成元 ``human_declared`` は未実装であり、この API から生成する
経路は設けない。descriptor は schema 検証の後に禁止キー走査を通さなければならず、
どちらか一方でも失敗した入力を警告だけで続行しない。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema


class DescriptorError(RuntimeError):
    """descriptor の射影、検証、provenance 契約への違反。"""


PROJECTION_VERSION = "8b-descriptor-projection/v1"

DECLARED_CONTENTION_LABELS = {"0.9": "high"}

FORBIDDEN_KEY_TOKENS = (
    "winner", "variant", "tps", "throughput", "rank", "recommend",
    "fitness", "delta", "faster", "slower", "argmax", "reference",
    "best", "measured",
)

_SCHEMA_PATH = Path(__file__).resolve().with_name("s8b_descriptor_schema.json")


def _canonical_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
    except (TypeError, ValueError) as exc:
        raise DescriptorError("canonical JSON に変換できない") from exc
    return encoded.encode("utf-8")


def _read_schema() -> dict:
    try:
        with _SCHEMA_PATH.open(encoding="utf-8") as stream:
            schema = json.load(stream)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DescriptorError("descriptor schema を読めない: %s" % _SCHEMA_PATH) from exc
    if not isinstance(schema, dict):
        raise DescriptorError("descriptor schema が object でない")
    return schema


def _required(mapping: Any, key: str, path: str) -> Any:
    if not isinstance(mapping, dict):
        raise DescriptorError("型不正: %s は object でなければならない" % path)
    if key not in mapping:
        raise DescriptorError("必須キー欠落: %s.%s" % (path, key))
    return mapping[key]


def _strict_int_string(value: Any, path: str) -> int:
    if not isinstance(value, str):
        raise DescriptorError("型不正: %s は canonical 整数文字列でなければならない" % path)
    try:
        converted = int(value)
    except ValueError as exc:
        raise DescriptorError("型不正: %s は canonical 整数文字列でなければならない" % path) from exc
    if str(converted) != value:
        raise DescriptorError("非 canonical 整数文字列: %s=%r" % (path, value))
    return converted


def _strict_positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DescriptorError("型不正: %s は bool でない int でなければならない" % path)
    if value < 1:
        raise DescriptorError("値域不正: %s は 1 以上でなければならない" % path)
    return value


def project_from_search_config(search_config) -> dict:
    """campaign ``search_config`` から ``8b-v1`` descriptor を決定論射影する。

    ``records`` / ``threads`` は bool を明示的に拒否する。YCSB の ``rratio`` と
    ``rmw`` は canonical な整数文字列だけを受理し、skew の分類は設計時宣言から
    引く。未知 skew を数値から再分類する経路は持たない。
    """
    records = _strict_positive_int(
        _required(search_config, "records", "$"), "$.records"
    )
    threads = _strict_positive_int(
        _required(search_config, "threads", "$"), "$.threads"
    )
    ycsb = _required(search_config, "ycsb", "$")
    if not isinstance(ycsb, dict):
        raise DescriptorError("型不正: $.ycsb は object でなければならない")

    raw_skew = _required(ycsb, "ycsb_zipf_skew", "$.ycsb")
    if not isinstance(raw_skew, str):
        raise DescriptorError("型不正: $.ycsb.ycsb_zipf_skew は str でなければならない")
    if raw_skew not in DECLARED_CONTENTION_LABELS:
        raise DescriptorError(
            "未知 skew は宣言済み分類へ射影できない: $.ycsb.ycsb_zipf_skew=%r" % raw_skew
        )
    try:
        skew = float(raw_skew)
    except ValueError as exc:
        raise DescriptorError("skew を float へ変換できない: %r" % raw_skew) from exc

    read_ratio = _strict_int_string(
        _required(ycsb, "ycsb_rratio", "$.ycsb"), "$.ycsb.ycsb_rratio"
    )
    rmw = _strict_int_string(
        _required(ycsb, "ycsb_rmw", "$.ycsb"), "$.ycsb.ycsb_rmw"
    )

    return {
        "schema_version": "8b-v1",
        "source": "campaign_search_config_projection",
        "read_write": {"read_ratio_percent": read_ratio, "rmw": rmw},
        "contention": {
            "skew": skew,
            "label": DECLARED_CONTENTION_LABELS[raw_skew],
        },
        "scale": {"records": records, "threads": threads},
        "objective": "maximize_throughput_tps",
        "correctness": "serializable_legacy_and_s2",
    }


def _json_path(parent: str, key: Any) -> str:
    base = parent or "$"
    if isinstance(key, str) and key.isidentifier():
        return "%s.%s" % (base, key)
    try:
        rendered = json.dumps(key, ensure_ascii=False)
    except (TypeError, ValueError):
        rendered = repr(key)
    return "%s[%s]" % (base, rendered)


def scan_forbidden_keys(obj, path="") -> None:
    """dict の全キーを再帰走査し、禁止 token の部分一致を拒否する。

    比較は大文字小文字を無視する。list は各要素を再帰走査する一方、文字列を
    含む値そのものは走査しない。正当な enum 値
    ``maximize_throughput_tps`` が ``throughput`` / ``tps`` を含むため、禁止対象は
    あくまでキー名に限定する。
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = _json_path(path, key)
            if not isinstance(key, str):
                raise DescriptorError("禁止キー走査で文字列でないキーを検出: path=%s" % key_path)
            lowered = key.lower()
            token = next((item for item in FORBIDDEN_KEY_TOKENS if item in lowered), None)
            if token is not None:
                raise DescriptorError(
                    "禁止フィールドを検出: path=%s key=%r token=%r" % (key_path, key, token)
                )
            scan_forbidden_keys(value, key_path)
    elif isinstance(obj, list):
        base = path or "$"
        for index, value in enumerate(obj):
            scan_forbidden_keys(value, "%s[%d]" % (base, index))


def validate_descriptor(descriptor) -> None:
    """schema 検証、禁止キー走査の順で二段検証し、違反時は必ず停止する。"""
    schema = _read_schema()
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        jsonschema.Draft7Validator(schema).validate(descriptor)
    except (jsonschema.SchemaError, jsonschema.ValidationError) as exc:
        path = ""
        for item in getattr(exc, "absolute_path", ()):
            path = _json_path(path, item)
        path = path or "$"
        if (getattr(exc, "validator", None) == "additionalProperties"
                and isinstance(getattr(exc, "instance", None), dict)
                and isinstance(getattr(exc, "schema", None), dict)):
            declared = exc.schema.get("properties", {})
            extras = sorted(key for key in exc.instance if key not in declared)
            if len(extras) == 1:
                path = _json_path(path, extras[0])
        raise DescriptorError("descriptor schema 検証に失敗: path=%s: %s" % (path, exc.message)) from exc
    scan_forbidden_keys(descriptor)


def projection_record(search_config, descriptor) -> dict:
    """manifest 用の射影版と canonical JSON / schema の SHA-256 を返す。"""
    try:
        schema_bytes = _SCHEMA_PATH.read_bytes()
    except OSError as exc:
        raise DescriptorError("descriptor schema を読めない: %s" % _SCHEMA_PATH) from exc
    return {
        "projection_version": PROJECTION_VERSION,
        "input_sha256": hashlib.sha256(_canonical_bytes(search_config)).hexdigest(),
        "output_sha256": hashlib.sha256(_canonical_bytes(descriptor)).hexdigest(),
        "schema_sha256": hashlib.sha256(schema_bytes).hexdigest(),
    }


def descriptor_for_holdout(holdout_entry) -> dict:
    """holdout freeze の一エントリを射影し、二段検証済み descriptor として返す。"""
    descriptor = project_from_search_config(holdout_entry)
    validate_descriptor(descriptor)
    return descriptor
