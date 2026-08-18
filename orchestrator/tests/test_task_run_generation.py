# -*- coding: utf-8 -*-
"""generation manager の fail-closed、recovery、明示 rollover 回帰。"""
from __future__ import annotations

import ast
import errno
import fcntl
import hashlib
import json
import os
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.task_runs import (
    finish_automatic_test_run,
    init_pilot,
    open_next_generation,
    start_automatic_test_run,
    start_run,
    validate_series,
)
from tools.task_runs import generation, ledger, pytest_stats
from tools.task_runs.aggregate import publish_report
from tools.task_runs.schema import SCHEMA_VERSION


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "generation@example.invalid")
    _git(repo, "config", "user.name", "generation-test")
    (repo / "seed").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed")
    _git(repo, "commit", "-qm", "seed")
    return repo


def _run(root: Path, run_id: str) -> Path:
    return root / run_id


def _write_valid_final_marker(generation_root: Path) -> None:
    report = b"final report\n"
    reports = generation_root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "report.md").write_bytes(report)
    (generation_root / "pilot-final.json").write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "final_report": "report.md",
            "report_sha256": hashlib.sha256(report).hexdigest(),
        }) + "\n",
        encoding="utf-8",
    )


def test_default_base_is_repo_sibling_and_linked_worktrees_share_series(git_repo: Path):
    base = generation.series_base_for_repo(git_repo)
    assert base == git_repo.parent / f"{git_repo.name}-task-runs"
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None
    assert run is not None
    assert run.generation_root.parent == base
    assert run.generation_name == "generation-000001"
    assert (base / generation.SERIES_LOCK_NAME).is_file()


def test_auto_root_override_is_ignored_and_no_repo_bytes_created(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    monkeypatch.setenv("IZANAGI_TASK_RUNS_ROOT", str(tmp_path / "override"))
    run, diagnostic = start_automatic_test_run(git_repo)
    assert run is not None and diagnostic is None
    assert run.generation_root.parent == generation.series_base_for_repo(git_repo)
    assert not (git_repo / "generation-000001").exists()
    assert not (tmp_path / "override").exists()
    assert finish_automatic_test_run(run, "completed") is None


def test_automatic_lifecycle_creates_one_task_and_cleans_sidecar(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None
    assert run is not None
    assert run.sidecar_path is not None
    assert run.sidecar_path.name == "pytest-stats.json"
    assert run.sidecar_path.parent.parent.name == generation.TRANSPORT_DIR_NAME
    assert run.sidecar_path.parent.is_dir()
    assert stat.S_IMODE(run.sidecar_path.parent.stat().st_mode) == 0o700
    assert not run.sidecar_path.exists()
    task = json.loads((_run(run.generation_root, run.task_run_id) / "task.json").read_text())
    assert task["objective"] == "automatic test observation"
    assert task["task_kind"] == "other"
    assert task["base_commit"] == _git(git_repo, "rev-parse", "HEAD")
    assert finish_automatic_test_run(run, "completed") is None
    assert not run.sidecar_path.exists()
    assert not run.sidecar_path.parent.exists()
    report = validate_series(git_repo)
    assert report.is_valid
    assert report.published_run_count == 1


def test_automatic_sidecar_round_trips_through_pytest_stats(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert run.sidecar_path is not None
    sidecar = run.sidecar_path
    lease_directory = sidecar.parent
    assert sidecar.name == "pytest-stats.json"
    assert lease_directory.is_dir()
    assert stat.S_IMODE(lease_directory.stat().st_mode) == 0o700
    assert lease_directory.parent.name == generation.TRANSPORT_DIR_NAME
    assert not sidecar.exists()

    other_run, other_diagnostic = start_automatic_test_run(git_repo)
    assert other_diagnostic is None and other_run is not None
    assert other_run.sidecar_path is not None
    assert other_run.sidecar_path.parent != lease_directory

    reporter = SimpleNamespace(
        stats={
            "passed": [SimpleNamespace(nodeid="integration/test_sidecar.py::test_ok")],
            "failed": [],
            "error": [],
            "skipped": [],
        },
    )
    config = SimpleNamespace(
        pluginmanager=SimpleNamespace(get_plugin=lambda name: reporter),
    )
    session = SimpleNamespace(config=config, testscollected=1)
    monkeypatch.setenv(pytest_stats.SIDECAR_ENV, str(sidecar))
    try:
        pytest_stats.write_session_stats(session)
        assert sidecar.is_file()
        counts_and_digest = pytest_stats.read_sidecar(sidecar)
        assert counts_and_digest is not None
        counts, digest = counts_and_digest
        assert counts == {"collected": 1, "passed": 1, "failed": 0, "skipped": 0}
        assert isinstance(digest, str) and len(digest) == 12
    finally:
        assert finish_automatic_test_run(other_run, "completed") is None
        assert finish_automatic_test_run(run, "completed") is None

    assert not sidecar.exists()
    assert not lease_directory.exists()


def test_read_sidecar_rejects_path_identity_swap_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    payload = {
        "collected": 1,
        "passed": 1,
        "failed": 0,
        "skipped": 0,
        "collected_node_digest": "a" * 12,
    }
    original_dir = tmp_path / "original"
    replacement_dir = tmp_path / "replacement"
    original_dir.mkdir(mode=0o700)
    replacement_dir.mkdir(mode=0o700)
    sidecar = original_dir / pytest_stats._SIDECAR_BASENAME
    replacement = replacement_dir / pytest_stats._SIDECAR_BASENAME
    pytest_stats._create_sidecar(sidecar, payload)
    pytest_stats._create_sidecar(replacement, payload)

    real_open = pytest_stats.os.open
    swapped = False

    def swap_before_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if dir_fd is None and Path(path) == sidecar and not swapped:
            swapped = True
            sidecar.rename(original_dir / "old-sidecar")
            replacement.rename(sidecar)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(pytest_stats.os, "open", swap_before_open)
    assert pytest_stats.read_sidecar(sidecar) is None
    assert swapped


def test_foreign_repo_root_cannot_bind_to_existing_generation(
    git_repo: Path, tmp_path: Path,
):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    _git(foreign, "init", "-q")
    _git(foreign, "config", "user.email", "foreign@example.invalid")
    _git(foreign, "config", "user.name", "foreign")
    (foreign / "seed").write_text("foreign\n", encoding="utf-8")
    _git(foreign, "add", "seed")
    _git(foreign, "commit", "-qm", "foreign")
    before = (run.generation_root / run.task_run_id / "events.jsonl").read_bytes()
    with pytest.raises(ledger.LedgerError):
        start_run(
            run.generation_root,
            slug="foreign",
            objective="foreign binding",
            task_class=2,
            task_kind="other",
            repo_root=foreign,
        )
    assert (run.generation_root / run.task_run_id / "events.jsonl").read_bytes() == before
    assert finish_automatic_test_run(run, "completed") is None


def test_external_start_observes_repo_head_not_generation_root(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    task = json.loads((run.generation_root / run.task_run_id / "task.json").read_text())
    assert task["base_commit"] == _git(git_repo, "rev-parse", "HEAD")
    assert finish_automatic_test_run(run, "completed") is None


def test_external_symlink_or_banned_namespace_is_rejected_before_create(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    base = generation.series_base_for_repo(git_repo)
    outside = tmp_path / "outside"
    outside.mkdir()
    base.symlink_to(outside, target_is_directory=True)
    run, diagnostic = start_automatic_test_run(git_repo)
    assert run is None
    assert diagnostic == "recording-unavailable:filesystem"
    assert not (outside / generation.SERIES_LOCK_NAME).exists()

    base.unlink()
    monkeypatch.setattr(
        generation,
        "series_base_for_repo",
        lambda _repo: git_repo / "output" / "campaigns" / "task-runs",
    )
    run, diagnostic = start_automatic_test_run(git_repo)
    assert run is None
    assert diagnostic == "recording-unavailable:filesystem"
    assert not (git_repo / "output").exists()


def test_external_banned_namespace_is_rejected_with_existing_intermediates(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    intermediate = git_repo / "output" / "campaigns"
    intermediate.mkdir(parents=True)
    series_base = intermediate / "task-runs"
    monkeypatch.setattr(
        generation,
        "series_base_for_repo",
        lambda _repo: series_base,
    )

    run, diagnostic = start_automatic_test_run(git_repo)

    assert run is None
    assert diagnostic == "recording-unavailable:filesystem"
    assert not series_base.exists()


def test_external_root_toctou_swap_creates_no_generation_bytes(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
):
    base = generation.series_base_for_repo(git_repo)
    outside = tmp_path / "outside"
    outside.mkdir()
    real_mkdir = generation.os.mkdir

    def swap_after_mkdir(path, mode=0o777, *, dir_fd=None):
        result = real_mkdir(path, mode, dir_fd=dir_fd)
        if dir_fd is not None and path == base.name:
            moved = tmp_path / "moved-base"
            base.rename(moved)
            base.symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(generation.os, "mkdir", swap_after_mkdir)
    run, diagnostic = start_automatic_test_run(git_repo)
    assert run is None
    assert diagnostic == "recording-unavailable:filesystem"
    assert not (outside / generation.SERIES_LOCK_NAME).exists()


def test_staging_generation_recovers_after_init_before_publish(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    base = run.generation_root.parent
    staging = base / "generation-000002.staging"
    staging.mkdir(mode=0o700)
    init_pilot(staging)
    read_only = validate_series(git_repo)
    assert not read_only.is_valid
    assert "staging-pending" in read_only.invalid_codes
    recovered, diagnostic = start_automatic_test_run(git_repo)
    assert recovered is not None
    assert diagnostic is None
    assert finish_automatic_test_run(recovered, "completed") is None
    assert not staging.exists()
    assert (base / "generation-000002" / "pilot.json").is_file()


def test_staging_generation_recovers_after_init_fsync_fault(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    base = generation.series_base_for_repo(git_repo)
    real_fsync_dir = generation._fsync_dir
    injected = False

    def fail_staging_fsync(fd: int, *, label: str) -> None:
        nonlocal injected
        if label == "staging generation" and not injected:
            injected = True
            raise generation.GenerationError("injected staging fsync failure")
        real_fsync_dir(fd, label=label)

    monkeypatch.setattr(generation, "_fsync_dir", fail_staging_fsync)
    failed, diagnostic = start_automatic_test_run(git_repo)
    assert failed is None
    assert diagnostic == "recording-unavailable:filesystem"
    staging = base / "generation-000001.staging"
    assert injected
    assert (staging / "pilot.json").is_file()

    monkeypatch.setattr(generation, "_fsync_dir", real_fsync_dir)
    recovered, diagnostic = start_automatic_test_run(git_repo)
    assert recovered is not None
    assert diagnostic is None
    assert not staging.exists()
    assert (base / "generation-000001" / "pilot.json").is_file()
    assert finish_automatic_test_run(recovered, "completed") is None


def test_staging_generation_recovers_after_publish_rename_fault(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    base = generation.series_base_for_repo(git_repo)
    real_rename = generation.os.rename
    injected = False

    def fail_publish_rename(source, destination, *, src_dir_fd=None, dst_dir_fd=None):
        nonlocal injected
        if source == "generation-000001.staging" and not injected:
            injected = True
            raise OSError(errno.EIO, "injected staging rename failure")
        return real_rename(source, destination, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(generation.os, "rename", fail_publish_rename)
    failed, diagnostic = start_automatic_test_run(git_repo)
    assert failed is None
    assert diagnostic == "recording-unavailable:filesystem"
    staging = base / "generation-000001.staging"
    assert injected
    assert staging.is_dir()

    monkeypatch.setattr(generation.os, "rename", real_rename)
    recovered, diagnostic = start_automatic_test_run(git_repo)
    assert recovered is not None
    assert diagnostic is None
    assert not staging.exists()
    assert finish_automatic_test_run(recovered, "completed") is None


def test_managed_generation_report_surfaces_invalid_series(git_repo: Path):
    first, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and first is not None
    assert finish_automatic_test_run(first, "completed") is None

    first_report = first.generation_root / "reports" / "generation-one.md"
    publish_report(first.generation_root, first_report, final=True)
    second_root = open_next_generation(git_repo)
    (second_root / "pilot.json").write_bytes(b"{damaged\n")

    report = first.generation_root / "reports" / "series-invalid.md"
    publish_report(first.generation_root, report)
    body = report.read_text(encoding="utf-8")
    assert "series全体の健全性: invalid (generation-invalid)" in body
    assert "## Series health manifest" in body
    assert "| managed-series | `invalid` | generation-invalid |" in body


def test_damaged_staging_is_quarantined_and_series_stays_invalid(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    base = run.generation_root.parent
    staging = base / "generation-000002.staging"
    staging.mkdir(mode=0o700)
    (staging / "pilot.json").write_bytes(b"{damaged\n")
    report = validate_series(git_repo)
    assert not report.is_valid
    assert "staging-pending" in report.invalid_codes
    assert staging.exists()
    result, diagnostic = start_automatic_test_run(git_repo)
    assert result is None
    assert diagnostic == "recording-unavailable:series-invalid"
    assert not staging.exists()
    quarantined = list(base.glob("generation-000002.staging.damaged-*"))
    assert len(quarantined) == 1


def test_damaged_generation_is_checked_before_closure_reason(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    events = run.generation_root / run.task_run_id / "events.jsonl"
    events.write_bytes(b"{\n")
    _write_valid_final_marker(run.generation_root)
    result, diagnostic = start_automatic_test_run(git_repo)
    assert result is None
    assert diagnostic == "recording-unavailable:series-invalid"


def test_damaged_run_does_not_block_new_automatic_start_or_report_pilot_closed(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    events = run.generation_root / run.task_run_id / "events.jsonl"
    events.write_bytes(b"{\n")
    next_run, next_diagnostic = start_automatic_test_run(git_repo)
    assert next_diagnostic is None
    assert next_run is not None
    assert next_run.task_run_id != run.task_run_id


@pytest.mark.parametrize("state", ["damaged", "incomplete"])
def test_cap_counts_damaged_and_incomplete_runs(git_repo: Path, state: str):
    for index in range(9):
        run, diagnostic = start_automatic_test_run(git_repo)
        assert diagnostic is None and run is not None
        assert finish_automatic_test_run(run, "completed") is None

    latest = validate_series(git_repo).generation_roots[-1]
    if state == "damaged":
        run, diagnostic = start_automatic_test_run(git_repo)
        assert diagnostic is None and run is not None
        (run.generation_root / run.task_run_id / "events.jsonl").write_bytes(b"{\n")
    else:
        incomplete = latest / "20260819-incomplete-aaaaaaaa"
        incomplete.mkdir(mode=0o700)
        (incomplete / "events.jsonl").write_bytes(b"")

    report = validate_series(git_repo)
    assert report.published_run_count == 10
    result, diagnostic = start_automatic_test_run(git_repo)
    assert result is None
    assert diagnostic == "pilot-closed:max-task-runs"


def test_closed_generation_returns_diagnostic_without_rollover(git_repo: Path):
    runs = []
    for index in range(10):
        run, diagnostic = start_automatic_test_run(git_repo)
        assert diagnostic is None and run is not None
        runs.append(run)
        assert finish_automatic_test_run(run, "completed") is None
    result, diagnostic = start_automatic_test_run(git_repo)
    assert result is None
    assert diagnostic == "pilot-closed:max-task-runs"
    assert not (generation.series_base_for_repo(git_repo) / "generation-000002").exists()


def test_explicit_open_next_generation_is_the_only_rollover_path(git_repo: Path):
    for _ in range(10):
        run, diagnostic = start_automatic_test_run(git_repo)
        assert diagnostic is None and run is not None
        assert finish_automatic_test_run(run, "completed") is None
    next_root = open_next_generation(git_repo)
    assert next_root.name == "generation-000002"
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert run.generation_name == "generation-000002"
    assert finish_automatic_test_run(run, "completed") is None


def test_series_reader_rejects_unknown_and_staging_entries(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    base = run.generation_root.parent
    (base / "surprise").write_text("x", encoding="utf-8")
    report = validate_series(git_repo)
    assert not report.is_valid
    assert "unknown-series-entry" in report.invalid_codes


def test_series_reader_rejects_one_bad_generation_instead_of_skipping_it(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    _write_valid_final_marker(run.generation_root)
    second = open_next_generation(git_repo)
    (second / "pilot.json").write_bytes(b"{damaged\n")
    report = validate_series(git_repo)
    assert not report.is_valid
    assert len(report.generations) == 2
    assert "generation-invalid" in report.invalid_codes


def test_empty_series_is_explicitly_undecidable(git_repo: Path):
    base = generation.series_base_for_repo(git_repo)
    base.mkdir(mode=0o700)
    lock = base / generation.SERIES_LOCK_NAME
    lock.write_bytes(b"")
    lock.chmod(0o600)
    report = validate_series(git_repo)
    assert report.is_empty
    assert report.is_valid is None
    assert report.invalid_codes == ()
    assert report.as_dict()["is_empty"] is True


def test_final_marker_requires_existing_matching_report(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    (run.generation_root / "reports").mkdir()
    (run.generation_root / "pilot-final.json").write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "final_report": "report.md",
            "report_sha256": "a" * 64,
        }) + "\n",
        encoding="utf-8",
    )
    report = validate_series(git_repo)
    assert not report.is_valid
    assert "generation-invalid" in report.invalid_codes
    result, diagnostic = start_automatic_test_run(git_repo)
    assert result is None
    assert diagnostic == "recording-unavailable:series-invalid"


def test_orphan_sidecar_lease_is_reclaimed_on_next_start(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    transport = run.generation_root.parent / generation.TRANSPORT_DIR_NAME
    orphan = transport / "orphan-lease"
    orphan.mkdir(mode=0o700)
    (orphan / "pytest-stats.json").write_bytes(b"orphan\n")
    next_run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and next_run is not None
    assert not orphan.exists()
    assert finish_automatic_test_run(next_run, "completed") is None


def test_automatic_selfcheck_failure_is_diagnostic_and_runs_continue(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch,
):
    calls: list[Path] = []

    def fail_selfcheck(root: Path) -> None:
        calls.append(root)
        raise ledger.LedgerError("injected selfcheck failure")

    monkeypatch.setattr(ledger, "selfcheck", fail_selfcheck)
    first, diagnostic = start_automatic_test_run(git_repo)
    assert first is not None
    assert diagnostic == "recording-unavailable:filesystem"
    assert (first.generation_root / ledger.GENERATION_SELF_CHECK_NAME).read_bytes() == b"failed\n"
    assert finish_automatic_test_run(first, "completed") is None
    second, diagnostic = start_automatic_test_run(git_repo)
    assert second is not None
    assert diagnostic == "recording-unavailable:filesystem"
    assert calls == [first.generation_root]
    assert finish_automatic_test_run(second, "completed") is None


def test_series_lock_timeout_returns_bounded_diagnostic(git_repo: Path, monkeypatch: pytest.MonkeyPatch):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    base = run.generation_root.parent
    fd = os.open(base / generation.SERIES_LOCK_NAME, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        monkeypatch.setattr(generation, "_LOCK_TIMEOUT_S", 0.02)
        result, diagnostic = start_automatic_test_run(git_repo)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    assert result is None
    assert diagnostic == "recording-unavailable:series-lock-timeout"


def test_parallel_starts_count_unfinished_published_runs_against_cap(git_repo: Path):
    def start_one(_index: int):
        return start_automatic_test_run(git_repo)

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(start_one, range(20)))
    successes = [run for run, diagnostic in results if run is not None]
    diagnostics = [diagnostic for _run, diagnostic in results if diagnostic is not None]
    assert len(successes) == 10
    assert diagnostics.count("pilot-closed:max-task-runs") == 10
    for run in successes:
        assert finish_automatic_test_run(run, "completed") is None
    assert validate_series(git_repo).published_run_count == 10


def test_managed_generation_write_is_rejected_by_cli(git_repo: Path, capsys: pytest.CaptureFixture[str]):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    before = sorted(path.name for path in run.generation_root.iterdir())
    from tools.task_runs.cli import main

    rc = main([
        "--root", str(run.generation_root),
        "start", "--slug", "cli", "--objective", "cli", "--task-class", "2",
        "--task-kind", "other",
    ])
    assert rc == 1
    assert "managed generation" in capsys.readouterr().err
    assert sorted(path.name for path in run.generation_root.iterdir()) == before
    assert finish_automatic_test_run(run, "completed") is None


def test_managed_generation_selfcheck_is_rejected_before_writing(
    git_repo: Path, capsys: pytest.CaptureFixture[str],
):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    before = sorted(
        (path.relative_to(run.generation_root), path.read_bytes())
        for path in run.generation_root.rglob("*")
        if path.is_file()
    )
    from tools.task_runs.cli import main

    rc = main(["--root", str(run.generation_root), "selfcheck"])
    assert rc == 1
    assert "managed generation" in capsys.readouterr().err
    after = sorted(
        (path.relative_to(run.generation_root), path.read_bytes())
        for path in run.generation_root.rglob("*")
        if path.is_file()
    )
    assert after == before
    assert finish_automatic_test_run(run, "completed") is None


def test_cli_write_guard_rechecks_realpath_before_write(tmp_path: Path):
    from tools.task_runs import cli

    root = tmp_path / "root"
    root.mkdir()
    checked = cli._write_root_snapshot(root)
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    root.rename(tmp_path / "old-root")
    root.symlink_to(replacement, target_is_directory=True)
    with pytest.raises(ledger.LedgerError, match="managed generation write path changed"):
        cli._verify_write_root(root, checked)


def test_managed_generation_remains_rejected_after_repo_rename(
    git_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    renamed = tmp_path / "renamed-repo"
    git_repo.rename(renamed)
    from tools.task_runs.cli import main

    rc = main([
        "--root", str(run.generation_root), "event", run.task_run_id,
        "wait", "--wait-kind", "tool", "--duration-s", "0.1",
    ])
    assert rc == 1
    assert "managed generation" in capsys.readouterr().err
    assert finish_automatic_test_run(run, "completed") is None


def test_repo_identity_swap_is_rejected_before_head_is_recorded(
    git_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    assert finish_automatic_test_run(run, "completed") is None
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    _git(replacement, "init", "-q")
    _git(replacement, "config", "user.email", "replacement@example.invalid")
    _git(replacement, "config", "user.name", "replacement")
    (replacement / "seed").write_text("replacement\n", encoding="utf-8")
    _git(replacement, "add", "seed")
    _git(replacement, "commit", "-qm", "replacement")
    moved = tmp_path / "original-repo"
    real_head = ledger._git_head

    def swap_before_head(cwd: Path, **kwargs: object) -> str:
        git_repo.rename(moved)
        replacement.rename(git_repo)
        return real_head(cwd, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(ledger, "_git_head", swap_before_head)
    try:
        with pytest.raises(ledger.LedgerError):
            start_run(
                run.generation_root,
                slug="swap",
                objective="repo identity swap",
                task_class=2,
                task_kind="other",
                repo_root=git_repo,
            )
    finally:
        if git_repo.exists():
            git_repo.rename(replacement)
        moved.rename(git_repo)
    assert tuple(run.generation_root.iterdir())


def test_unrelated_same_name_directory_is_not_managed(tmp_path: Path):
    unrelated = tmp_path / "repo-task-runs" / "generation-000001"
    assert not generation.is_managed_generation_root(unrelated)


def test_generation_documents_remain_exact_task_run_v1(git_repo: Path):
    run, diagnostic = start_automatic_test_run(git_repo)
    assert diagnostic is None and run is not None
    task = json.loads((run.generation_root / run.task_run_id / "task.json").read_text())
    assert task["schema_version"] == SCHEMA_VERSION
    assert set(task) == {
        "schema_version", "task_run_id", "objective", "task_class", "task_kind",
        "started_at", "base_commit", "base_commit_source", "authority",
        "measurement_policy",
    }
    assert (run.generation_root / run.task_run_id / "events.jsonl").read_bytes() == b""
    assert finish_automatic_test_run(run, "completed") is None


def test_call_graph_pins_explicit_generation_and_repo_binding():
    root = Path(__file__).resolve().parents[2]
    generation_tree = ast.parse(
        (root / "tools/task_runs/generation.py").read_text(encoding="utf-8"),
    )
    cli_tree = ast.parse((root / "tools/task_runs/cli.py").read_text(encoding="utf-8"))

    open_callers = []
    start_repo_callers = []

    class CallerVisitor(ast.NodeVisitor):
        def __init__(self, filename: str):
            self.filename = filename
            self.stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef):  # type: ignore[override]
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node: ast.Call):  # type: ignore[override]
            if isinstance(node.func, (ast.Name, ast.Attribute)):
                called_name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
                caller = self.stack[-1] if self.stack else None
                if called_name == "open_next_generation":
                    open_callers.append((self.filename, caller))
                if called_name == "start_run" and any(keyword.arg == "repo_root" for keyword in node.keywords):
                    start_repo_callers.append((self.filename, caller))
            self.generic_visit(node)

    CallerVisitor("generation.py").visit(generation_tree)
    CallerVisitor("cli.py").visit(cli_tree)
    assert open_callers == [("cli.py", "main")]
    assert start_repo_callers == [("generation.py", "start_automatic_test_run")]
