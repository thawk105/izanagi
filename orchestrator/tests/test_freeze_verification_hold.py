# -*- coding: utf-8 -*-
"""凍結チェーン同一性検証の保留正本。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.campaign import freeze_verification_hold as HOLD


def test_hold_reason_is_machine_readable_and_release_is_literal():
    assert HOLD.HELD is True
    assert dict(HOLD.REASON) == {
        "decision": "freeze-verification-hold",
        "ruling": "rulings-4th-batch-2026-08-12",
        "ruled_on": "2026-08-12",
        "authority": "user",
        "release": "ユーザーの明示命令のみ",
        "release_condition": "explicit-user-command-only",
    }
    marker = HOLD.held_marker("frozen-artifacts.manifest-bytes")
    assert marker["status"] == "held"
    assert "pass" not in marker["status"]


def test_result_markers_do_not_change_artifact_document_keys():
    result = HOLD.result_with_markers(
        {"artifact": "unchanged"},
        [HOLD.held_marker("s1-known-axes.ccbench-submodule-head-pin")],
    )
    assert result == {"artifact": "unchanged"}
    assert set(result) == {"artifact"}
    assert result.held_checks[0]["check_id"] == (
        "s1-known-axes.ccbench-submodule-head-pin"
    )


def test_held_marker_emits_machine_readable_stderr_once_per_process_check_id(
        capsys, monkeypatch):
    monkeypatch.setattr(HOLD, "_EMITTED_MARKERS", set())
    check_id = "s8b-floor.protocol-bytes-expected-pin"

    HOLD.held_marker(check_id)
    HOLD.held_marker(check_id)

    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 1
    prefix, payload_raw = lines[0].split(" ", 1)
    assert prefix == HOLD.MARKER_PREFIX
    assert json.loads(payload_raw) == {
        "check_id": check_id,
        "decision": "freeze-verification-hold",
        "ruling": "rulings-4th-batch-2026-08-12",
        "release_condition": "explicit-user-command-only",
    }


def test_held_marker_is_visible_across_subprocess_boundary():
    check_id = "s1-measurement.recorded-pin-current-pin"
    script = (
        "from orchestrator.campaign import freeze_verification_hold as h; "
        f"h.held_marker({check_id!r})"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=Path(HOLD.__file__).parents[2],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    assert completed.stderr.startswith(f"{HOLD.MARKER_PREFIX} ")
    payload = json.loads(completed.stderr.split(" ", 1)[1])
    assert payload["check_id"] == check_id


def test_held_check_id_registry_count_digest_and_unknown_rejection():
    assert len(HOLD.HELD_CHECK_IDS) == HOLD.HELD_CHECK_ID_COUNT == 21
    assert hashlib.sha256(
        "\n".join(sorted(HOLD.HELD_CHECK_IDS)).encode("utf-8")
    ).hexdigest() == HOLD.HELD_CHECK_IDS_SHA256 == (
        "f60568ada1001c7b95239838300effa32431b5ee01536487f27a013fdac2e00d"
    )
    with pytest.raises(ValueError, match="未登録 check_id"):
        HOLD.held_marker("unregistered-check")


def test_hold_has_no_environment_or_cli_release_surface():
    source = Path(HOLD.__file__).read_text(encoding="utf-8")
    assert "environ" not in source
    assert "getenv" not in source
    assert "argparse" not in source
    assert "click" not in source


def _run():
    return pytest.main([__file__])


if __name__ == "__main__":
    sys.exit(_run())
