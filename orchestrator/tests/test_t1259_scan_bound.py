"""Exercise fixture scan bounds using real Git operations in temporary repositories."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.tests import t1259_scan_bound
from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe


def _temporary_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    for relative in (
        probe.PROBE_RELATIVE_PATH, probe.PBS_RELATIVE_PATH, probe.CAMPAIGN_RELATIVE_PATH
    ):
        source = root / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"temporary source: {relative}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Scan Test",
         "-c", "user.email=scan@example.invalid", "commit", "-m", "initial"],
        check=True, capture_output=True,
    )
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    (root / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    return root, head


def _spy(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []
    real_run = subprocess.run

    def run(*args, **kwargs):
        calls.append(dict(kwargs))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(probe.subprocess, "run", run)
    return calls


def test_production_snapshot_keeps_thirty_second_bound(tmp_path, monkeypatch):
    root, head = _temporary_repo(tmp_path)
    calls = _spy(monkeypatch)
    snapshot = probe._repo_snapshot(root)
    assert len(calls) == 4
    assert all(call["timeout"] == 30.0 for call in calls)
    assert snapshot["head"] == head
    assert "untracked.txt" in snapshot["untracked_paths"]


def test_fixture_snapshot_uses_local_candidate_bound(tmp_path, monkeypatch):
    assert t1259_scan_bound.FIXTURE_GIT_TIMEOUT_SECONDS == 120.0
    root, head = _temporary_repo(tmp_path)
    production = probe._repo_snapshot(root)
    calls = _spy(monkeypatch)
    snapshot = t1259_scan_bound.fixture_repo_snapshot(root)
    assert len(calls) == 4
    assert all(
        call["timeout"] == t1259_scan_bound.FIXTURE_GIT_TIMEOUT_SECONDS
        and call["timeout"] != 30.0 for call in calls
    )
    assert snapshot.keys() == production.keys()
    assert snapshot["head"] == production["head"] == head
    assert snapshot == production


def test_fixture_snapshot_propagates_timeout(tmp_path, monkeypatch):
    root, _ = _temporary_repo(tmp_path)
    failure = subprocess.TimeoutExpired(
        cmd=["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        timeout=t1259_scan_bound.FIXTURE_GIT_TIMEOUT_SECONDS,
    )

    def timeout(*args, **kwargs):
        raise failure

    monkeypatch.setattr(probe.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        t1259_scan_bound.fixture_repo_snapshot(root)
    assert caught.value is failure


def _run():
    return pytest.main([__file__])


if __name__ == "__main__":
    raise SystemExit(_run())
