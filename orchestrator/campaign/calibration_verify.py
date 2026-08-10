# -*- coding: utf-8 -*-
"""Environment-contract 型に依存しない calibration admission leaf。"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..calibrator import effective_clock_policy
from ..calibrator import schema_v2 as _schema_v2


GRANDFATHERED_V1_SHA256 = (
    "751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5"
)
LEGACY_SCHEMA_VERSION = "calibration/v1"

_HEX64_RE = re.compile(r"[0-9a-f]{64}")


class AttestationError(RuntimeError):
    """probe・比較・calibration admission の fail-closed 拒否。"""


def profile_sha256(profile: _schema_v2.AttestationProfile) -> str:
    if not isinstance(profile, _schema_v2.AttestationProfile):
        raise AttestationError("profile が AttestationProfile でない")
    raw = json.dumps(
        dataclasses.asdict(profile),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class VerifiedCalibration:
    """一つの contract mode に admission 済みの hash-bound calibration artifact。"""

    schema_version: str
    sha256: str
    calibration: Optional[_schema_v2.CalibrationV2]
    attestation_profile_sha256: Optional[str]

    def __post_init__(self) -> None:
        if type(self.sha256) is not str or _HEX64_RE.fullmatch(self.sha256) is None:
            raise AttestationError("verified calibration sha256 が 64 lower-hex でない")
        if self.schema_version == _schema_v2.SCHEMA_VERSION:
            if not isinstance(self.calibration, _schema_v2.CalibrationV2):
                raise AttestationError("calibration/v2 marker に CalibrationV2 値がない")
            actual_profile_sha = profile_sha256(self.calibration.attestation_profile)
            if self.attestation_profile_sha256 != actual_profile_sha:
                raise AttestationError("verified calibration profile sha256 が自己矛盾")
        elif self.schema_version == LEGACY_SCHEMA_VERSION:
            if self.calibration is not None or self.attestation_profile_sha256 is not None:
                raise AttestationError("legacy calibration marker に v2 profile が混入")
        else:
            raise AttestationError(f"未知の verified calibration schema: {self.schema_version!r}")

    @property
    def attestation_profile(self) -> _schema_v2.AttestationProfile:
        if self.calibration is None:
            raise AttestationError("legacy calibration に attestation profile はない")
        return self.calibration.attestation_profile


def _duplicate_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AttestationError(f"calibration JSON has duplicate key: {key!r}")
        result[key] = value
    return result


def load_verified_calibration(
    *,
    env_tag: str,
    clocks_per_us: int,
    attestation_mode: str,
    calibration_path: str,
    calibration_sha256: str,
    repo_root: Path,
) -> VerifiedCalibration:
    """素の契約値を使い、artifact を一回だけ読んで admission する。"""
    if not isinstance(repo_root, Path):
        raise AttestationError("repo_root は Path でなければならない")
    try:
        root = repo_root.resolve(strict=True)
    except OSError as exc:
        raise AttestationError(f"repo_root を解決できない: {exc}") from exc
    relative = Path(calibration_path)
    if relative.is_absolute():
        raise AttestationError("calibration_ref.path は repository-relative でなければならない")
    try:
        artifact = (root / relative).resolve(strict=True)
        artifact.relative_to(root)
    except (OSError, ValueError) as exc:
        raise AttestationError("calibration_ref.path が repo_root 外または存在しない") from exc
    try:
        raw = artifact.read_bytes()
    except OSError as exc:
        raise AttestationError(f"calibration artifact を読めない: {exc}") from exc
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != calibration_sha256:
        raise AttestationError(
            f"calibration sha256 不一致: expected={calibration_sha256} "
            f"observed={actual_sha}"
        )

    if attestation_mode == "required":
        try:
            calibration = _schema_v2.validate_calibration_v2(raw)
        except _schema_v2.CalibrationSchemaError as exc:
            raise AttestationError(f"calibration/v2 検証失敗: {exc}") from exc
        if calibration.env_tag != env_tag:
            raise AttestationError(
                f"calibration env_tag 不一致: {calibration.env_tag!r} != {env_tag!r}"
            )
        if calibration.clocks_per_us != clocks_per_us:
            raise AttestationError(
                "calibration clocks_per_us 不一致: "
                f"{calibration.clocks_per_us} != {clocks_per_us}"
            )
        tolerance = calibration.attestation_profile.effective_clock.tolerance_pct
        if tolerance != effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT:
            raise AttestationError(
                "calibration effective clock tolerance が current policy と不一致: "
                f"{tolerance!r} != "
                f"{effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT!r}"
            )
        return VerifiedCalibration(
            schema_version=_schema_v2.SCHEMA_VERSION,
            sha256=actual_sha,
            calibration=calibration,
            attestation_profile_sha256=profile_sha256(calibration.attestation_profile),
        )

    if attestation_mode == "none":
        if actual_sha != GRANDFATHERED_V1_SHA256:
            raise AttestationError("mode=none は grandfathered v1 artifact bytes だけを受理する")
        try:
            parsed = json.loads(raw, object_pairs_hook=_duplicate_object)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise AttestationError(f"legacy calibration JSON を parse できない: {exc}") from exc
        if type(parsed) is not dict:
            raise AttestationError("legacy calibration JSON top-level が object でない")
        return VerifiedCalibration(
            schema_version=LEGACY_SCHEMA_VERSION,
            sha256=actual_sha,
            calibration=None,
            attestation_profile_sha256=None,
        )
    raise AttestationError(f"未対応 attestation_mode: {attestation_mode!r}")
