# -*- coding: utf-8 -*-
"""Human-reviewed 8b oracle spec の strict schema と approval pin。"""
from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional

from . import s8b_oracle_artifacts as _artifacts
from . import s8b_oracle_manifest as _manifest


ROOT = Path(__file__).resolve().parents[2]

SCHEMA_VERSION = "s8b-oracle-reviewed-spec/v1"
SPEC_REL = "output/s8b-oracle-spec/reviewed_spec.json"

# Human review 後に、その review 対象である exact spec bytes の SHA-256 を
# コード review 付き diff で置く。None は approval 不在を意味し、常に fail-closed。
APPROVED_SPEC_SHA256: Optional[str] = None

_TOP_LEVEL_KEYS = frozenset({
    "allowed_excluded_reasons",
    "binding_identity",
    "campaign_ids",
    "generator_versions",
    "run_contract",
    "schedule_parameters",
    "schedule_sha256",
    "schema_version",
})
_SCHEDULE_PARAMETER_KEYS = frozenset({
    "block_sizes",
    "configuration_ids",
    "holdout_ids",
    "master_seed",
    "n",
})


class ReviewedSpecError(RuntimeError):
    """reviewed spec 拒否。``reason`` は CLI が保持する reason code。"""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        super().__init__(f"[{reason}] {detail}" if detail else reason)


@dataclass(frozen=True)
class ReviewedSpec:
    """同じ raw bytes から検証した spec と再生成 schedule の snapshot。"""

    document: Mapping
    raw_bytes: bytes
    sha256: str
    schedule: Mapping

    def __post_init__(self) -> None:
        object.__setattr__(self, "document", _deep_freeze(self.document))
        object.__setattr__(self, "schedule", _deep_freeze(self.schedule))


def _deep_freeze(value):
    """JSON tree を dict→mapping proxy、list→tuple で再帰凍結する。"""
    if isinstance(value, Mapping):
        return MappingProxyType({
            key: _deep_freeze(item) for key, item in value.items()
        })
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _mutable_json_tree(value):
    if isinstance(value, Mapping):
        return {
            key: _mutable_json_tree(item) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_mutable_json_tree(item) for item in value]
    return value


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _lower_sha256(value: object, *, field: str) -> str:
    if (not isinstance(value, str) or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)):
        raise ReviewedSpecError("invalid-reviewed-spec", f"{field} が lowercase SHA-256 でない")
    return value


def _canonical_bytes(value: Mapping) -> bytes:
    try:
        return _manifest._canonical_bytes(value)
    except _manifest.ManifestError as exc:
        raise ReviewedSpecError("invalid-reviewed-spec", str(exc)) from exc


def validate_reviewed_spec(document: Mapping, *, root=ROOT) -> tuple[dict, dict]:
    """schema と全導出 field を検査し、spec copy と再生成 schedule を返す。"""
    if not isinstance(document, Mapping) or set(document) != _TOP_LEVEL_KEYS:
        raise ReviewedSpecError("invalid-reviewed-spec", "top-level key 集合が不一致")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ReviewedSpecError("invalid-reviewed-spec", "schema_version が不一致")

    parameters = document.get("schedule_parameters")
    if not isinstance(parameters, Mapping) or set(parameters) != _SCHEDULE_PARAMETER_KEYS:
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "schedule_parameters key 集合が不一致",
        )
    if not isinstance(parameters.get("block_sizes"), dict):
        raise ReviewedSpecError("invalid-reviewed-spec", "block_sizes が object でない")
    for field in ("holdout_ids", "configuration_ids"):
        if not isinstance(parameters.get(field), list):
            raise ReviewedSpecError("invalid-reviewed-spec", f"{field} が list でない")

    try:
        schedule = _manifest.build_schedule(
            n=parameters.get("n"),
            master_seed=parameters.get("master_seed"),
            block_sizes=parameters.get("block_sizes"),
            holdout_ids=parameters.get("holdout_ids"),
            configuration_ids=parameters.get("configuration_ids"),
        )
        _manifest.validate_schedule(schedule)
        recorded_schedule_sha = _lower_sha256(
            document.get("schedule_sha256"), field="schedule_sha256",
        )
        if recorded_schedule_sha != _manifest.schedule_sha256(schedule):
            raise ReviewedSpecError(
                "invalid-reviewed-spec", "schedule_sha256 が再生成値と不一致",
            )

        run_contract = document.get("run_contract")
        if (not isinstance(run_contract, Mapping)
                or set(run_contract) != _manifest._RUN_CONTRACT_KEYS):
            raise ReviewedSpecError(
                "invalid-reviewed-spec", "run_contract key 集合が不一致",
            )
        _manifest._validate_run_contract(run_contract)

        blocks = [block["block_id"] for block in schedule["blocks"]]
        campaign_ids = document.get("campaign_ids")
        if not isinstance(campaign_ids, dict) or set(campaign_ids) != set(blocks):
            raise ReviewedSpecError(
                "invalid-reviewed-spec", "campaign_ids が block_sizes と一対一でない",
            )
        campaigns = [
            _manifest._identifier(campaign_ids[block], field=f"campaign_ids.{block}")
            for block in blocks
        ]
        if len(set(campaigns)) != len(campaigns):
            raise ReviewedSpecError("invalid-reviewed-spec", "campaign ID が重複")

        _manifest._validate_binding_identity(
            document.get("binding_identity"), schedule=schedule,
        )
        _manifest._validate_generators(
            document.get("generator_versions"), root=Path(root),
        )
    except ReviewedSpecError:
        raise
    except _manifest.ManifestError as exc:
        raise ReviewedSpecError("invalid-reviewed-spec", str(exc)) from exc

    reasons = document.get("allowed_excluded_reasons")
    if (not isinstance(reasons, list)
            or any(not isinstance(reason, str) or not reason for reason in reasons)
            or len(set(reasons)) != len(reasons)):
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "allowed_excluded_reasons が不正",
        )

    return copy.deepcopy(dict(document)), copy.deepcopy(schedule)


def _load_approved_spec_bytes(root: Path) -> tuple[bytes, str]:
    """唯一の approval gate で pin と fixed-path bytes を束縛する。"""
    if APPROVED_SPEC_SHA256 is None:
        raise ReviewedSpecError("no-approved-spec")
    approved_sha = _lower_sha256(
        APPROVED_SPEC_SHA256, field="APPROVED_SPEC_SHA256",
    )
    path = root / SPEC_REL
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReviewedSpecError(
            "approved-spec-unreadable", f"{SPEC_REL} を読めない: {exc}",
        ) from exc
    if _sha256(raw) != approved_sha:
        raise ReviewedSpecError(
            "approved-spec-hash-mismatch", "reviewed spec bytes が approval pin と不一致",
        )
    return raw, approved_sha


def validate_approved_spec_snapshot(value, *, root=ROOT) -> ReviewedSpec:
    """承認時に捕捉済みの単一 ``ReviewedSpec`` snapshot を再束縛する。

    fixed path は再読込しない。canonical module の exact type、approval pin、raw
    bytes、document、再生成 schedule の同一 snapshot 性だけを再照合する。
    generator source の実 byte 検査を含む全 schema 検証は loader が一度だけ担う。
    """
    if type(value) is not ReviewedSpec:
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "ReviewedSpec exact type が必要",
        )
    if APPROVED_SPEC_SHA256 is None:
        raise ReviewedSpecError("no-approved-spec")
    approved_sha = _lower_sha256(
        APPROVED_SPEC_SHA256, field="APPROVED_SPEC_SHA256",
    )
    if value.sha256 != approved_sha or _sha256(value.raw_bytes) != approved_sha:
        raise ReviewedSpecError(
            "approved-spec-hash-mismatch",
            "ReviewedSpec snapshot が approval pin と不一致",
        )
    try:
        parsed = _artifacts.strict_load_json_object(value.raw_bytes)
    except _artifacts.OracleArtifactTypeError as exc:
        raise ReviewedSpecError("invalid-reviewed-spec", str(exc)) from exc
    if _canonical_bytes(parsed) != value.raw_bytes:
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "reviewed spec が strict canonical bytes でない",
        )
    if parsed != _mutable_json_tree(value.document):
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "ReviewedSpec.document が raw bytes と不一致",
        )
    parameters = parsed.get("schedule_parameters")
    if not isinstance(parameters, Mapping) or set(parameters) != _SCHEDULE_PARAMETER_KEYS:
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "schedule_parameters key 集合が不一致",
        )
    try:
        schedule = _manifest.build_schedule(
            n=parameters.get("n"),
            master_seed=parameters.get("master_seed"),
            block_sizes=parameters.get("block_sizes"),
            holdout_ids=parameters.get("holdout_ids"),
            configuration_ids=parameters.get("configuration_ids"),
        )
    except _manifest.ManifestError as exc:
        raise ReviewedSpecError("invalid-reviewed-spec", str(exc)) from exc
    if schedule != _mutable_json_tree(value.schedule):
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "ReviewedSpec.schedule が再生成値と不一致",
        )
    return value


def load_approved_spec(root=ROOT) -> ReviewedSpec:
    """pinned literal と一致する fixed-path spec を一度だけ捕捉して検証する。"""
    raw, approved_sha = _load_approved_spec_bytes(Path(root))
    try:
        document = _artifacts.strict_load_json_object(raw)
    except _artifacts.OracleArtifactTypeError as exc:
        raise ReviewedSpecError("invalid-reviewed-spec", str(exc)) from exc
    if _canonical_bytes(document) != raw:
        raise ReviewedSpecError(
            "invalid-reviewed-spec", "reviewed spec が strict canonical bytes でない",
        )
    validated, schedule = validate_reviewed_spec(document, root=root)
    return ReviewedSpec(
        document=validated,
        raw_bytes=raw,
        sha256=approved_sha,
        schedule=schedule,
    )
