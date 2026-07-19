# -*- coding: utf-8 -*-
"""8b oracle artifact の schema・runtime type・strict loader の leaf 契約。

runtime type は JSON 互換の marker であり、provenance 検証の証明ではない。
全 consumer はこの module を canonical name ``campaign.s8b_oracle_artifacts`` で
import し、同名 class が別 module identity で複製されることを避ける。

この module は stdlib-only leaf とし、他の campaign module を import しない。
"""
from __future__ import annotations

import json
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeAlias


OFFICIAL_MANIFEST_SCHEMA = "8b-oracle-manifest/v1"
OFFICIAL_OBSERVATIONS_SCHEMA = "8b-oracle-observations/v1"
OFFICIAL_VERDICT_SCHEMA = "8b-oracle-verdict/v1"
COMBINED_VERDICT_SCHEMA = "8b-combined-verdict/v2"
EXPLORATION_ARTIFACT_SCHEMA = "8b-oracle-exploration-artifact/v1"

EXPLORATION_ARTIFACT_ROLES = frozenset({"manifest", "observations", "verdict"})
EXPLORATION_ARTIFACT_KEYS = frozenset({
    "schema_version", "artifact_role", "campaign_id", "measurement_hint", "payload",
})
MEASUREMENT_HINT_KEYS = frozenset({"extime_s", "reps"})


class OracleArtifactTypeError(TypeError):
    """artifact の schema/runtime role が official 境界と一致しない。"""


class OfficialManifest(dict):
    """Official manifest marker。provenance 検証済みであることは意味しない。"""


class LegacyManifest(dict):
    """Stage 0 で report だけが受理する legacy manifest marker。"""


class OfficialObservations(dict):
    """Official observations marker。provenance 検証済みであることは意味しない。"""


class OfficialVerdict(dict):
    """Official oracle verdict marker。provenance 検証済みであることは意味しない。"""


class ExplorationArtifact(dict):
    """Official 型とは継承関係を持たない探索 artifact marker。"""


JsonSource: TypeAlias = str | os.PathLike[str] | bytes


def _reject_json_constant(token: str):
    raise OracleArtifactTypeError(f"JSON に非数値定数リテラルがある: {token}")


def _parse_finite_json_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise OracleArtifactTypeError(f"JSON に有限でない浮動小数点値がある: {token}")
    return value


def _reject_duplicate_keys(pairs):
    document: dict = {}
    for key, value in pairs:
        if key in document:
            raise OracleArtifactTypeError(f"JSON に重複キーがある: {key!r}")
        document[key] = value
    return document


def strict_load_json_object(source: JsonSource) -> dict:
    """path または UTF-8 JSON bytes を duplicate/non-finite 拒否で読む。"""
    label: object
    if isinstance(source, bytes):
        label = "<bytes>"
        try:
            text = source.decode("utf-8")
        except UnicodeError as exc:
            raise OracleArtifactTypeError(f"JSON を読めない: {label}: {exc}") from exc
    elif isinstance(source, (str, os.PathLike)):
        path = Path(source)
        label = path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise OracleArtifactTypeError(f"JSON を読めない: {path}: {exc}") from exc
    else:
        raise OracleArtifactTypeError("JSON source は path または bytes でなければならない")
    try:
        value = json.loads(
            text,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_json_float,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except json.JSONDecodeError as exc:
        raise OracleArtifactTypeError(f"JSON を読めない: {label}: {exc}") from exc
    if type(value) is not dict:
        raise OracleArtifactTypeError(f"JSON top-level が object でない: {label}")
    return value


def project_finite_float_sequence(value: object) -> list[float] | None:
    """数値 array を各要素一度だけ float 化する。不正・overflow は None。"""
    if (not isinstance(value, Sequence)
            or isinstance(value, (str, bytes, bytearray)) or not value):
        return None
    projected: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return None
        try:
            number = float(item)
        except (OverflowError, TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        projected.append(number)
    return projected


def load_official_manifest(source: JsonSource) -> OfficialManifest | LegacyManifest:
    """manifest を schema classifier として読む。full verification は行わない。

    schema または run_contract を欠く保存済み形式は Stage 0 の legacy marker と
    して分離する。明示された未知 schema と exploration schema は拒否する。
    """
    document = strict_load_json_object(source)
    if "schema_version" not in document:
        return LegacyManifest(document)
    schema = document["schema_version"]
    if schema == OFFICIAL_MANIFEST_SCHEMA and "run_contract" not in document:
        return LegacyManifest(document)
    if schema != OFFICIAL_MANIFEST_SCHEMA:
        raise OracleArtifactTypeError(
            f"manifest schema_version が official でない: {schema!r}")
    return OfficialManifest(document)


def load_official_observations(source: JsonSource) -> OfficialObservations:
    document = strict_load_json_object(source)
    if document.get("schema_version") != OFFICIAL_OBSERVATIONS_SCHEMA:
        raise OracleArtifactTypeError("observations schema_version が official でない")
    return OfficialObservations(document)


def load_official_verdict(source: JsonSource) -> OfficialVerdict:
    document = strict_load_json_object(source)
    if document.get("schema_version") != OFFICIAL_VERDICT_SCHEMA:
        raise OracleArtifactTypeError("oracle verdict schema_version が official でない")
    return OfficialVerdict(document)


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise OracleArtifactTypeError(f"{field} は非 bool の正整数でなければならない")
    return value


def validate_exploration_artifact(document: Mapping) -> ExplorationArtifact:
    if not isinstance(document, Mapping) or set(document) != EXPLORATION_ARTIFACT_KEYS:
        raise OracleArtifactTypeError("exploration artifact top-level schema が不一致")
    if document.get("schema_version") != EXPLORATION_ARTIFACT_SCHEMA:
        raise OracleArtifactTypeError("exploration artifact schema_version が不一致")
    if document.get("artifact_role") not in EXPLORATION_ARTIFACT_ROLES:
        raise OracleArtifactTypeError("exploration artifact_role が閉集合外")
    campaign_id = document.get("campaign_id")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise OracleArtifactTypeError("exploration campaign_id が空でない文字列でない")
    hint = document.get("measurement_hint")
    if not isinstance(hint, Mapping) or set(hint) != MEASUREMENT_HINT_KEYS:
        raise OracleArtifactTypeError("measurement_hint schema が不一致")
    _positive_int(hint.get("extime_s"), field="measurement_hint.extime_s")
    _positive_int(hint.get("reps"), field="measurement_hint.reps")
    if not isinstance(document.get("payload"), Mapping):
        raise OracleArtifactTypeError("exploration payload が object でない")
    return ExplorationArtifact(document)


def load_exploration_artifact(source: JsonSource) -> ExplorationArtifact:
    return validate_exploration_artifact(strict_load_json_object(source))
