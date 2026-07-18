# -*- coding: utf-8 -*-
"""``campaign.s8b_launch_cert`` leaf の certificate / raw path 契約テスト。"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR))

from campaign import s8b_launch_cert  # noqa: E402


_RUN_ID = "20260718T123456Z-abcdef01"
_BASENAME = "launch_certificate.json"
_VALID_PATH = (
    "output/env/linux-baremetal/calibration/s8b-floor-official/"
    f"{_RUN_ID}/{_BASENAME}"
)


def _certificate(*, started_utc: str = "2026-07-18T12:34:56.987654+00:00") -> dict:
    return {
        "schema": s8b_launch_cert.LAUNCH_CERT_SCHEMA,
        "v1_freeze_sha256": "a" * 64,
        "clean_scan_digest": "b" * 64,
        "protocol_sha256": "c" * 64,
        "started_utc": started_utc,
        "campaign_run_id": _RUN_ID,
    }


def _validate(cert: dict) -> dict:
    return s8b_launch_cert.validate_launch_certificate(
        cert,
        expected_v1_freeze_sha256="a" * 64,
        expected_protocol_sha256="c" * 64,
        expected_run_id=_RUN_ID,
    )


def test_validate_launch_certificate_accepts_same_second_time_origin():
    cert = _certificate()
    assert _validate(cert) == cert


def test_validate_launch_certificate_rejects_different_run_id_second():
    cert = _certificate(started_utc="2026-07-18T12:34:57+00:00")
    with pytest.raises(s8b_launch_cert.LaunchCertError, match="秒単位で不一致"):
        _validate(cert)


def test_parse_official_run_path_returns_typed_components():
    assert s8b_launch_cert.parse_official_run_path(
        _VALID_PATH, expected_basename=_BASENAME,
    ) == {
        "env_tag": "linux-baremetal",
        "ts": dt.datetime(2026, 7, 18, 12, 34, 56, tzinfo=dt.timezone.utc),
        "proto8": "abcdef01",
        "run_id": _RUN_ID,
        "basename": _BASENAME,
    }


@pytest.mark.parametrize(
    "path",
    [
        "/" + _VALID_PATH,
        _VALID_PATH + "/",
        _VALID_PATH.replace("output/env", "output/./env"),
        _VALID_PATH.replace("output/env", "output/../env"),
        _VALID_PATH.replace("output/env", "output//env"),
        _VALID_PATH.replace("output/env", r"output\env"),
        _VALID_PATH.replace("output/env", "output/\x00env"),
        _VALID_PATH.replace("linux-baremetal", "Linux-baremetal"),
        _VALID_PATH.replace("20260718T123456Z", "20260718T12345Z"),
        _VALID_PATH.replace("20260718T123456Z", "20260230T123456Z"),
        _VALID_PATH.replace("abcdef01", "abcdef0"),
        _VALID_PATH.replace("abcdef01", "ABCDEF01"),
    ],
    ids=[
        "absolute", "trailing-slash", "dot", "dot-dot", "double-slash",
        "backslash", "control", "invalid-env", "invalid-ts-width",
        "invalid-ts-date", "short-proto8", "uppercase-proto8",
    ],
)
def test_parse_official_run_path_rejects_invalid_raw_grammar(path):
    with pytest.raises(s8b_launch_cert.LaunchCertError):
        s8b_launch_cert.parse_official_run_path(
            path, expected_basename=_BASENAME,
        )


def test_parse_official_run_path_rejects_wrong_basename():
    with pytest.raises(s8b_launch_cert.LaunchCertError, match="basename"):
        s8b_launch_cert.parse_official_run_path(
            _VALID_PATH, expected_basename="result.json",
        )


def test_parse_official_run_path_rejects_noncanonical_timestamp_round_trip():
    path = _VALID_PATH.replace("20260718T123456Z", "00010101T123456Z")
    with pytest.raises(s8b_launch_cert.LaunchCertError, match="round-trip"):
        s8b_launch_cert.parse_official_run_path(
            path, expected_basename=_BASENAME,
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
