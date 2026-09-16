"""Whole-namespace evacuation, integrity failures, and real clean scan."""
from pathlib import Path
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import s8b_floor_evacuation as E
from orchestrator.campaign import s8b_holdout_freeze as F

ENV = "pegasus"
NS = "output/env/pegasus/calibration/s8b-floor-official"
R1 = "20260810T235900Z-12345678"
R2 = "20260811T000000Z-abcdef01"


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _put(root, run=R1, raw=b'{ "unfinished": true }\n\x00\xff'):
    directory = root / NS / run
    (directory / "empty").mkdir(parents=True)
    (directory / "journal.jsonl").write_bytes(raw)
    return directory


def _bytes(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


def test_bundle_root_is_fixed_and_has_no_override(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    expected = root / ".git/izanagi/s8b-floor-evacuation/pegasus"
    for key in ("S8B_FLOOR_EVACUATION_ROOT", "S8B_FLOOR_EVACUATION_BUNDLE", "BUNDLE_ROOT"):
        monkeypatch.setenv(key, str(tmp_path / "override"))
    assert E.bundle_root(root, env_tag=ENV) == expected
    assert tuple(inspect.signature(E.bundle_root).parameters) == ("repo_root", "env_tag")
    assert tuple(inspect.signature(E.evacuate).parameters) == ("root", "env_tag", "references")
    assert tuple(inspect.signature(E.restore).parameters) == ("root", "env_tag")
    _put(root)
    for command in ("evacuate", "restore"):
        result = subprocess.run(
            [sys.executable, "-m", E.__name__, command, "--repo-root", str(root), "--env-tag", ENV],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        assert result.returncode == 0, result.stderr
        for flag in ("--bundle", "--runs", "--proto8", "--timestamp", "--references"):
            with pytest.raises(SystemExit) as error:
                E.main([command, "--env-tag", ENV, flag, "value"])
            assert error.value.code == 2


def test_bundle_root_ignores_git_location_environment(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    other = tmp_path / "other"
    subprocess.run(["git", "init", "-q", str(other)], check=True)
    expected = E.bundle_root(root, env_tag=ENV)
    overrides = {"GIT_DIR": str(other / ".git"),
                 "GIT_COMMON_DIR": str(other / ".git"),
                 "GIT_WORK_TREE": str(other)}
    for environment in [{key: value} for key, value in overrides.items()] + [overrides]:
        with monkeypatch.context() as patch:
            for key, value in environment.items():
                patch.setenv(key, value)
            assert E.bundle_root(root, env_tag=ENV) == expected


def test_evacuate_double_rename_failure_preserves_accumulated_bytes(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    first = _put(root)
    original = _bytes(first)
    E.evacuate(root=root, env_tag=ENV)
    assert not first.exists()
    second = _put(root, R2)
    second_bytes = _bytes(second)
    bundle = E.bundle_root(root, env_tag=ENV)
    saved = _bytes(bundle)
    rename = Path.rename
    failures = []
    backups = []

    def fail_publication_and_rollback(path, target):
        if Path(target) == bundle:
            failures.append(path)
            raise OSError("injected publish/rollback failure")
        result = rename(path, target)
        if path == bundle:
            backups.append(Path(target))
        return result

    with monkeypatch.context() as patch:
        patch.setattr(Path, "rename", fail_publication_and_rollback)
        with pytest.raises(E.FloorEvacuationError) as error:
            E.evacuate(root=root, env_tag=ENV)
    assert len(failures) == 2
    assert len(backups) == 1
    backup = backups[0]
    assert _bytes(backup / "payload" / NS / R1) == original
    assert _bytes(backup) == saved
    assert str(backup) in str(error.value)
    assert _bytes(second) == second_bytes
    # Recover the reported backup; its retained sibling must not affect validation.
    shutil.copytree(backup, bundle)
    E.evacuate(root=root, env_tag=ENV)
    E.restore(root=root, env_tag=ENV)
    assert _bytes(first) == original
    assert _bytes(second) == second_bytes
    assert _bytes(backup) == saved


def test_evacuate_accumulates_all_namespace_runs(tmp_path):
    root = _repo(tmp_path)
    first = _put(root)
    original = _bytes(first)
    E.evacuate(root=root, env_tag=ENV)
    second = _put(root, R2)
    (second / "result.json").write_bytes(b'{"eligible_for_refreeze":false}\n')
    third = _put(root, "20260812T000000Z-12345678")
    doc = E.evacuate(root=root, env_tag=ENV)
    assert {r["run_id"] for r in doc["runs"]} == {R1, R2, third.name}
    assert {r["proto8"] for r in doc["runs"]} == {"12345678", "abcdef01"}
    assert _bytes(E.bundle_root(root, env_tag=ENV) / "payload" / NS / R1) == original
    # An identical retry is allowed, but a conflicting same-path run is not.
    _put(root)
    E.evacuate(root=root, env_tag=ENV)
    conflict = _put(root, raw=b"different")
    with pytest.raises(E.FloorEvacuationError, match="different bytes"):
        E.evacuate(root=root, env_tag=ENV)
    assert (conflict / "journal.jsonl").read_bytes() == b"different"


def test_evacuate_removes_empty_namespace_directory(tmp_path):
    root = _repo(tmp_path)
    _put(root)
    E.evacuate(root=root, env_tag=ENV)
    assert not (root / NS).exists()
    E.restore(root=root, env_tag=ENV)
    assert (root / NS / R1).is_dir()


def test_evacuate_failure_preserves_source(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    run = _put(root)
    original = _bytes(run)
    copy = E.shutil.copytree

    def corrupt(source, destination, *args, **kwargs):
        result = copy(source, destination, *args, **kwargs)
        if Path(source) == run:
            (Path(destination) / "journal.jsonl").write_bytes(b"corrupt")
        return result

    monkeypatch.setattr(E.shutil, "copytree", corrupt)
    with pytest.raises(E.FloorEvacuationError, match="copied paths/sha256 mismatch"):
        E.evacuate(root=root, env_tag=ENV)
    assert _bytes(run) == original
    assert not E.bundle_root(root, env_tag=ENV).exists()


def test_evacuate_retry_preserves_accumulated_runs(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    first = _put(root)
    expected = _bytes(first)
    E.evacuate(root=root, env_tag=ENV)
    second = _put(root, R2)
    bundle = E.bundle_root(root, env_tag=ENV)
    saved = _bytes(bundle)
    copy = E.shutil.copytree

    def corrupt_previous(source, destination, *args, **kwargs):
        result = copy(source, destination, *args, **kwargs)
        if Path(source) == bundle:
            (Path(destination) / "payload" / NS / R1 / "journal.jsonl").write_bytes(b"corrupt old run")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(E.shutil, "copytree", corrupt_previous)
        with pytest.raises(E.FloorEvacuationError, match="manifest/payload mismatch"):
            E.evacuate(root=root, env_tag=ENV)
    assert _bytes(bundle) == saved
    assert second.is_dir()
    remove = E.shutil.rmtree

    def fail_source(path, *args, **kwargs):
        if Path(path) == second:
            raise OSError("injected source removal failure")
        return remove(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(E.shutil, "rmtree", fail_source)
        with pytest.raises(E.FloorEvacuationError, match="source removal failure"):
            E.evacuate(root=root, env_tag=ENV)
    assert second.is_dir()
    E.evacuate(root=root, env_tag=ENV)
    E.restore(root=root, env_tag=ENV)
    assert _bytes(first) == expected
    assert second.is_dir()


def test_restore_recreates_entire_namespace_byte_exact(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    _put(root)
    _put(root, R2, b' {"z": 1, "a":2}\r\n')
    expected = _bytes(root / NS)
    E.evacuate(root=root, env_tag=ENV)
    bundle = E.bundle_root(root, env_tag=ENV)
    saved = _bytes(bundle)
    # Corruption during expansion must fail before any run is published.
    copy = E.shutil.copytree

    def corrupt(source, destination, *args, **kwargs):
        result = copy(source, destination, *args, **kwargs)
        if Path(source) == bundle:
            (Path(destination) / "payload" / NS / R1 / "journal.jsonl").write_bytes(b"bad")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(E.shutil, "copytree", corrupt)
        with pytest.raises(E.FloorEvacuationError, match="manifest/payload mismatch"):
            E.restore(root=root, env_tag=ENV)
    assert not (root / NS).exists()
    (root / NS).mkdir()  # An empty namespace is explicitly permitted.
    assert E.restore(root=root, env_tag=ENV) == (f"{NS}/{R1}", f"{NS}/{R2}")
    assert _bytes(root / NS) == expected
    assert all((root / NS / run / "empty").is_dir() for run in (R1, R2))
    assert _bytes(bundle) == saved
    assert not (root / NS / "manifest.json").exists()


def test_restore_rejects_bundle_mismatch(tmp_path):
    for kind in ("hash", "run", "file", "extra", "duplicate", "duplicate-file", "env", "namespace", "escape"):
        case = tmp_path / kind
        case.mkdir()
        root = _repo(case)
        _put(root)
        doc = E.evacuate(root=root, env_tag=ENV)
        bundle = E.bundle_root(root, env_tag=ENV)
        run = bundle / "payload" / NS / R1
        if kind == "hash":
            (run / "journal.jsonl").write_bytes(b"bad")
        elif kind == "run":
            shutil.rmtree(run)
        elif kind == "file":
            (run / "journal.jsonl").unlink()
        elif kind == "extra":
            (run / "extra").write_bytes(b"extra")
        elif kind == "duplicate":
            doc["runs"].append(doc["runs"][0])
        elif kind == "escape":
            doc["runs"][0]["dir"] = "../outside"
        elif kind in ("env", "namespace"):
            doc["env_tag" if kind == "env" else "namespace"] = "other"
        raw = json.dumps(doc)
        if kind == "duplicate-file":
            key, value = next(iter(doc["files"].items()))
            raw = raw.replace('"files": {', '"files": {' + json.dumps(key) + ': ' + json.dumps(value) + ',')
        (bundle / "manifest.json").write_text(raw)
        with pytest.raises(E.FloorEvacuationError):
            E.restore(root=root, env_tag=ENV)
        assert not (root / NS).exists()


def test_restore_rejects_existing_runs_at_destination(tmp_path):
    root = _repo(tmp_path)
    _put(root)
    E.evacuate(root=root, env_tag=ENV)
    run = _put(root, raw=b"existing")
    with pytest.raises(E.FloorEvacuationError, match="already contains"):
        E.restore(root=root, env_tag=ENV)
    assert (run / "journal.jsonl").read_bytes() == b"existing"
    shutil.rmtree(run)
    run.mkdir()  # Even an empty run directory may not be merged.
    with pytest.raises(E.FloorEvacuationError, match="already contains"):
        E.restore(root=root, env_tag=ENV)


def test_transfer_rejects_unsafe_paths(tmp_path):
    for kind in ("entry", "symlink", "fifo", "namespace-symlink", "bundle-symlink", "escape"):
        case = tmp_path / kind
        case.mkdir()
        root = _repo(case)
        run = _put(root)
        outside = case / "outside"
        outside.mkdir()
        if kind == "entry":
            run.rename(run.with_name("not-a-run"))
        elif kind == "symlink":
            (run / "link").symlink_to(outside, target_is_directory=True)
        elif kind == "fifo":
            os.mkfifo(run / "pipe")
        elif kind == "namespace-symlink":
            (root / NS).rename(outside / "namespace")
            (root / NS).symlink_to(outside / "namespace", target_is_directory=True)
        elif kind == "bundle-symlink":
            bundle = E.bundle_root(root, env_tag=ENV)
            bundle.parent.mkdir(parents=True)
            bundle.symlink_to(outside, target_is_directory=True)
        with pytest.raises(E.FloorEvacuationError):
            E.evacuate(root=root, env_tag="../escape" if kind == "escape" else ENV)
    # Restoration must reject unsafe payload too, without following it.
    root = _repo(tmp_path)
    _put(root)
    E.evacuate(root=root, env_tag=ENV)
    payload = E.bundle_root(root, env_tag=ENV) / "payload" / NS / R1
    (payload / "journal.jsonl").unlink()
    (payload / "journal.jsonl").symlink_to(tmp_path / "outside")
    with pytest.raises(E.FloorEvacuationError):
        E.restore(root=root, env_tag=ENV)


def test_references_do_not_claim_payload_preservation(tmp_path):
    root = _repo(tmp_path)
    _put(root)
    reference = tmp_path / "external"
    reference.mkdir()
    (reference / "binary").write_bytes(b"external bytes")
    doc = E.evacuate(root=root, env_tag=ENV, references=[reference, reference / "binary"])
    assert doc["references"][str(reference)] == {
        "type": "directory", "files": {"binary": hashlib.sha256(b"external bytes").hexdigest()}}
    assert doc["references"][str(reference / "binary")]["type"] == "file"
    assert not any("external" in path for path in doc["files"])
    shutil.rmtree(reference)
    E.restore(root=root, env_tag=ENV)
    assert not reference.exists()


def test_untracked_holdout_hit_disappears_only_after_evacuation(tmp_path):
    root = _repo(tmp_path)
    ccbench = root / "external" / "ccbench"
    ccbench.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(ccbench)], check=True)
    def text(ratio):
        axes = F.HOLDOUTS["rr80"]["ycsb"]
        return "\n".join(F.concrete_axis_encodings(axis, value)[0] for axis, value in (
            ("rratio", ratio), ("skew", axes[F.SKEW_KEY]), ("rmw", axes[F.RMW_KEY])))
    (root / "positive.txt").write_text(text("50"))
    run = _put(root, raw=text("80").encode())
    with pytest.raises(F.FreezeError, match="holdout hit"):
        F._assert_search_pass(F.search_repository(root))
    E.evacuate(root=root, env_tag=ENV)
    assert not run.exists()
    F._assert_search_pass(F.search_repository(root))
    (root / "remaining.txt").write_text(text("80"))
    with pytest.raises(F.FreezeError, match="holdout hit"):
        F._assert_search_pass(F.search_repository(root))


if __name__ == "__main__":
    integration = str(Path(__file__).with_name("test_s8b_holdout_freeze.py"))
    raise SystemExit(pytest.main([
        "-v", __file__,
        integration + "::test_restored_namespace_restores_candidate_inputs",
        integration + "::test_restored_namespace_rejects_later_eligible_run",
    ] + sys.argv[1:]))
