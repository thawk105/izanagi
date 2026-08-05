"""T-244 P3 fixture-only liveness probe の変異検出ラッパ。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py"
PREVIEW = ROOT / "output/insights/2026-08-05_t244-p3-liveness/preview-wire-11111.json"
CHECKS = ("C-a", "C-b", "C-c1", "C-c2", "C-d", "C-e")


def test_t244_p3_liveness_probe_kills_registered_ledger_mutations() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            PROBE,
            "--wire",
            "11111",
            "--preview-json",
            PREVIEW,
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
    )
    diagnostic = f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    assert completed.returncode == 0, diagnostic
    lines = set(completed.stdout.splitlines())
    assert {f"{name}\tPASS" for name in CHECKS} <= lines, diagnostic


def _run() -> int:
    """Keep this new test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
