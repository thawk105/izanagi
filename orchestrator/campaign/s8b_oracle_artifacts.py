# -*- coding: utf-8 -*-
"""8b oracle artifact の schema・runtime type・strict loader の leaf 契約。

runtime type は JSON 互換の marker であり、provenance 検証の証明ではない。
全 consumer はこの module を canonical name ``orchestrator.campaign.s8b_oracle_artifacts`` で
import し、同名 class が別 module identity で複製されることを避ける。

この module は他の campaign module を import しない。runtime measurement sidecar だけは
calibrator の共有 perf observation validator を信頼境界として使う。
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeAlias

from orchestrator.calibrator import perf_preflight as _perf_preflight


OFFICIAL_MANIFEST_SCHEMA = "8b-oracle-manifest/v1"
OFFICIAL_OBSERVATIONS_SCHEMA = "8b-oracle-observations/v1"
OFFICIAL_VERDICT_SCHEMA = "8b-oracle-verdict/v1"
COMBINED_VERDICT_SCHEMA = "8b-combined-verdict/v3"
EXPLORATION_ARTIFACT_SCHEMA = "8b-oracle-exploration-artifact/v1"
MEASUREMENT_MANIFEST_SCHEMA = "8b-oracle-measurement-manifest/v1"

EXPLORATION_ARTIFACT_ROLES = frozenset({"manifest", "observations", "verdict"})
EXPLORATION_ARTIFACT_KEYS = frozenset({
    "schema_version", "artifact_role", "campaign_id", "measurement_hint", "payload",
})
MEASUREMENT_HINT_KEYS = frozenset({"extime_s", "reps"})
MEASUREMENT_MANIFEST_KEYS = frozenset({
    "schema_version", "oracle_manifest_sha256", "campaign_id", "block_id",
    "perf_observation",
})
CAMPAIGN_VERIFIER_EPOCH_KEYS = frozenset({
    "campaign_id", "campaign_verifier_epoch", "state", "reason_code",
    "identity_scope", "excluded_scope", "certified_eligible", "rejection",
})
CAMPAIGN_VERIFIER_EPOCH_REJECTION_KEYS = frozenset({"code", "message"})
CAMPAIGN_VERIFIER_EPOCH_REJECTION_CODES = frozenset({
    "campaign-verifier-epoch-rejected",
    "campaign-verifier-epoch-unavailable",
})
_SHA256_CHARS = frozenset("0123456789abcdef")


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


def validate_campaign_verifier_epochs(value: object) -> tuple[dict, ...]:
    """Official observations の campaign 別 epoch 証拠を exact 検査する。"""
    if (not isinstance(value, Sequence)
            or isinstance(value, (str, bytes, bytearray)) or not value):
        raise OracleArtifactTypeError(
            "campaign_verifier_epochs は空でない array でなければならない"
        )
    projected: list[dict] = []
    campaign_ids: set[str] = set()
    for entry in value:
        if not isinstance(entry, Mapping) or set(entry) != CAMPAIGN_VERIFIER_EPOCH_KEYS:
            raise OracleArtifactTypeError(
                "campaign_verifier_epochs entry の exact key 集合が不一致"
            )
        campaign_id = entry.get("campaign_id")
        if (not isinstance(campaign_id, str) or not campaign_id
                or campaign_id in campaign_ids):
            raise OracleArtifactTypeError(
                "campaign_verifier_epochs campaign_id が空・重複・非文字列"
            )
        campaign_ids.add(campaign_id)
        state = entry.get("state")
        epoch = entry.get("campaign_verifier_epoch")
        reason_code = entry.get("reason_code")
        eligible = entry.get("certified_eligible")
        rejection = entry.get("rejection")
        if (not isinstance(entry.get("identity_scope"), str)
                or not entry["identity_scope"]
                or not isinstance(entry.get("excluded_scope"), str)
                or not entry["excluded_scope"]):
            raise OracleArtifactTypeError(
                "campaign_verifier_epochs scope が空でない文字列でない"
            )
        if state == "E1":
            valid = (
                isinstance(epoch, str)
                and epoch.startswith("E1:")
                and len(epoch) == 67
                and set(epoch[3:]) <= _SHA256_CHARS
                and reason_code == "recorded-closure"
                and eligible is True
                and rejection is None
            )
        elif state == "E0":
            valid = (
                epoch == "E0"
                and reason_code == "v1-authority-absent"
                and eligible is False
            )
        elif state == "E1-stale":
            valid = (
                isinstance(epoch, str)
                and epoch.startswith("E1:")
                and len(epoch) == 67
                and set(epoch[3:]) <= _SHA256_CHARS
                and reason_code in {
                    "recorded-current-closure-mismatch",
                    "current-closure-unavailable",
                }
                and eligible is False
            )
        elif state == "unavailable":
            valid = (
                epoch is None
                and reason_code == "campaign-verifier-epoch-unavailable"
                and eligible is False
            )
        else:
            valid = False
        if not valid:
            raise OracleArtifactTypeError(
                "campaign_verifier_epochs epoch/eligibility 対応が不正"
            )
        if eligible is False:
            if (not isinstance(rejection, Mapping)
                    or set(rejection) != CAMPAIGN_VERIFIER_EPOCH_REJECTION_KEYS
                    or rejection.get("code")
                    not in CAMPAIGN_VERIFIER_EPOCH_REJECTION_CODES
                    or not isinstance(rejection.get("message"), str)
                    or not rejection["message"]):
                raise OracleArtifactTypeError(
                    "campaign_verifier_epochs rejection が不正"
                )
            expected_code = (
                "campaign-verifier-epoch-unavailable"
                if state == "unavailable"
                else "campaign-verifier-epoch-rejected"
            )
            if rejection["code"] != expected_code:
                raise OracleArtifactTypeError(
                    "campaign_verifier_epochs rejection code が state と不一致"
                )
        projected.append(dict(entry))
    return tuple(projected)


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


def _validate_measurement_manifest(
        document: object, *, run_cmd: object,
        leading_indicators: Mapping[str, object]) -> dict:
    if not isinstance(document, Mapping) or set(document) != MEASUREMENT_MANIFEST_KEYS:
        raise OracleArtifactTypeError(
            "measurement manifest top-level の exact key 集合が不一致"
        )
    if document.get("schema_version") != MEASUREMENT_MANIFEST_SCHEMA:
        raise OracleArtifactTypeError(
            "measurement manifest schema_version が不一致"
        )
    oracle_sha256 = document.get("oracle_manifest_sha256")
    if (not isinstance(oracle_sha256, str) or len(oracle_sha256) != 64
            or not set(oracle_sha256) <= _SHA256_CHARS):
        raise OracleArtifactTypeError(
            "measurement manifest oracle_manifest_sha256 が lowercase hex でない"
        )
    for field in ("campaign_id", "block_id"):
        value = document.get(field)
        if not isinstance(value, str) or not value:
            raise OracleArtifactTypeError(
                f"measurement manifest {field} が空でない文字列でない"
            )
    try:
        observation = _perf_preflight.validate_perf_observation(
            document.get("perf_observation"),
            run_cmd=run_cmd,
            leading_indicators=leading_indicators,
        )
    except _perf_preflight.PerfPreflightError as exc:
        raise OracleArtifactTypeError(
            f"measurement manifest perf_observation が不正: {exc}"
        ) from exc
    if observation["use_perf"] is not False:
        raise OracleArtifactTypeError(
            "measurement manifest は degraded measurement 専用"
        )
    normalized = dict(document)
    normalized["perf_observation"] = observation
    return normalized


def write_measurement_manifest(
        path: str | os.PathLike[str], *, oracle_manifest_sha256: str,
        campaign_id: str, block_id: str, perf_observation: object,
        run_cmd: object, leading_indicators: Mapping[str, object]) -> dict:
    """degraded runtime sidecar を create-only で書く。"""
    document = _validate_measurement_manifest(
        {
            "schema_version": MEASUREMENT_MANIFEST_SCHEMA,
            "oracle_manifest_sha256": oracle_manifest_sha256,
            "campaign_id": campaign_id,
            "block_id": block_id,
            "perf_observation": perf_observation,
        },
        run_cmd=run_cmd,
        leading_indicators=leading_indicators,
    )
    payload = (
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return document


def load_measurement_manifest(
        source: JsonSource, *, run_cmd: object,
        leading_indicators: Mapping[str, object]) -> dict:
    """runtime sidecar を strict JSON と semantic contract の両方で読む。"""
    return _validate_measurement_manifest(
        strict_load_json_object(source),
        run_cmd=run_cmd,
        leading_indicators=leading_indicators,
    )


def measurement_manifest_sha256(source: JsonSource) -> str:
    """sidecar の raw bytes に対する SHA-256 を返す。"""
    if isinstance(source, bytes):
        payload = source
    elif isinstance(source, (str, os.PathLike)):
        try:
            payload = Path(source).read_bytes()
        except OSError as exc:
            raise OracleArtifactTypeError(
                f"measurement manifest を読めない: {source}: {exc}"
            ) from exc
    else:
        raise OracleArtifactTypeError(
            "measurement manifest source は path または bytes でなければならない"
        )
    return hashlib.sha256(payload).hexdigest()
