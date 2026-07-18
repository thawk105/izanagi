# -*- coding: utf-8 -*-
"""S8b official launch certificate の共有 validation leaf。

stdlib のみに依存し、campaign 内の他 module は import しない。発行側と検証側が同じ
certificate / official artifact path 契約を循環 import なしで利用するための単一源である。
"""
from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping


LAUNCH_CERT_SCHEMA = "s8b-floor-launch-certificate/v1"

_CERTIFICATE_KEYS = frozenset({
    "schema",
    "v1_freeze_sha256",
    "clean_scan_digest",
    "protocol_sha256",
    "started_utc",
    "campaign_run_id",
})
_LOWER_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_RUN_TIMESTAMP_RE = re.compile(r"(?P<timestamp>[0-9]{8}T[0-9]{6}Z)")
_OFFICIAL_PATH_RE = re.compile(
    r"output/env/(?P<env_tag>[a-z0-9][a-z0-9._-]*)/"
    r"calibration/s8b-floor-official/"
    r"(?P<timestamp>[0-9]{8}T[0-9]{6}Z)-(?P<proto8>[0-9a-f]{8})/"
    r"(?P<basename>[^/]+)"
)
_PATH_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


class LaunchCertError(RuntimeError):
    """launch certificate または official path の fail-closed 拒否。"""


def _parse_run_timestamp(raw: str, *, source: str) -> dt.datetime:
    """固定幅 UTC timestamp を parse し、表記の round-trip 一致も要求する。"""
    try:
        parsed = dt.datetime.strptime(raw, _PATH_TIMESTAMP_FORMAT)
    except (TypeError, ValueError) as exc:
        raise LaunchCertError(f"{source} の時刻が不正") from exc
    if parsed.strftime(_PATH_TIMESTAMP_FORMAT) != raw:
        raise LaunchCertError(f"{source} の時刻が round-trip 一致しない")
    return parsed.replace(tzinfo=dt.timezone.utc)


def validate_launch_certificate(
        cert: Mapping, *, expected_v1_freeze_sha256: str,
        expected_protocol_sha256: str, expected_run_id: str) -> dict:
    """certificate の構造・UTC・hash pin・run identity / 時刻起点を検証する。"""
    if not isinstance(cert, Mapping):
        raise LaunchCertError("launch certificate が object でない")
    actual_keys = set(cert)
    if actual_keys != _CERTIFICATE_KEYS:
        raise LaunchCertError(
            "launch certificate の key 集合が不一致 "
            f"(欠落={sorted(_CERTIFICATE_KEYS - actual_keys, key=repr)} "
            f"未知={sorted(actual_keys - _CERTIFICATE_KEYS, key=repr)})"
        )
    if cert.get("schema") != LAUNCH_CERT_SCHEMA:
        raise LaunchCertError(
            f"launch certificate.schema が {LAUNCH_CERT_SCHEMA} でない"
        )
    for field in ("v1_freeze_sha256", "clean_scan_digest", "protocol_sha256"):
        value = cert.get(field)
        if not isinstance(value, str) or _LOWER_SHA256_RE.fullmatch(value) is None:
            raise LaunchCertError(
                f"launch certificate.{field} が 64 lower-hex でない"
            )

    started_utc = cert.get("started_utc")
    if not isinstance(started_utc, str) or not started_utc:
        raise LaunchCertError(
            "launch certificate.started_utc が空でない文字列でない"
        )
    try:
        parsed_started = dt.datetime.fromisoformat(
            started_utc[:-1] + "+00:00" if started_utc.endswith("Z") else started_utc
        )
    except ValueError as exc:
        raise LaunchCertError(
            "launch certificate.started_utc が timezone-aware UTC ISO 形式でない"
        ) from exc
    if (parsed_started.tzinfo is None
            or parsed_started.utcoffset() != dt.timedelta(0)):
        raise LaunchCertError(
            "launch certificate.started_utc が timezone-aware UTC ISO 形式でない"
        )

    run_id = cert.get("campaign_run_id")
    if not isinstance(run_id, str) or not run_id:
        raise LaunchCertError(
            "launch certificate.campaign_run_id が空でない文字列でない"
        )
    if cert["v1_freeze_sha256"] != expected_v1_freeze_sha256:
        raise LaunchCertError(
            "launch certificate.v1_freeze_sha256 が expected と不一致"
        )
    if cert["protocol_sha256"] != expected_protocol_sha256:
        raise LaunchCertError(
            "launch certificate.protocol_sha256 が expected と不一致"
        )
    if run_id != expected_run_id:
        raise LaunchCertError(
            "launch certificate.campaign_run_id が expected と不一致"
        )

    if not isinstance(expected_run_id, str):
        raise LaunchCertError("expected_run_id が文字列でない")
    timestamp_match = _RUN_TIMESTAMP_RE.match(expected_run_id)
    if timestamp_match is None:
        raise LaunchCertError(
            "launch certificate.campaign_run_id に UTC 時刻部がない"
        )
    run_timestamp = _parse_run_timestamp(
        timestamp_match.group("timestamp"), source="campaign_run_id",
    )
    started_at_second = parsed_started.astimezone(dt.timezone.utc).replace(microsecond=0)
    if started_at_second != run_timestamp:
        raise LaunchCertError(
            "launch certificate.started_utc が campaign_run_id の時刻と秒単位で不一致"
        )
    return dict(cert)


def parse_official_run_path(path_str: str, *, expected_basename: str) -> dict:
    """raw POSIX official artifact path を正規化せず exact 文法で parse する。"""
    if not isinstance(path_str, str) or not path_str:
        raise LaunchCertError("official path が空でない文字列でない")
    if (not isinstance(expected_basename, str) or not expected_basename
            or expected_basename in {".", ".."}
            or "/" in expected_basename or "\\" in expected_basename
            or any(ord(char) < 32 or ord(char) == 127 for char in expected_basename)):
        raise LaunchCertError("expected_basename が単一の安全な basename でない")

    # Path/PurePosixPath へ渡す前の raw 文字列で拒否する。正規化による交差受理を作らない。
    components = path_str.split("/")
    if (path_str.startswith("/") or path_str.endswith("/") or "//" in path_str
            or "\\" in path_str or "." in components or ".." in components
            or any(ord(char) < 32 or ord(char) == 127 for char in path_str)):
        raise LaunchCertError("official path の raw POSIX 表記が不正")

    match = _OFFICIAL_PATH_RE.fullmatch(path_str)
    if match is None:
        raise LaunchCertError("official path が exact 文法に一致しない")
    if match.group("basename") != expected_basename:
        raise LaunchCertError("official path の basename が expected と不一致")

    timestamp_raw = match.group("timestamp")
    timestamp = _parse_run_timestamp(timestamp_raw, source="official path")
    proto8 = match.group("proto8")
    return {
        "env_tag": match.group("env_tag"),
        "ts": timestamp,
        "proto8": proto8,
        "run_id": f"{timestamp_raw}-{proto8}",
        "basename": match.group("basename"),
    }
