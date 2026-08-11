from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from orchestrator.preregistration import blobref


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        [os.fspath(blobref._GIT_EXECUTABLE), *arguments],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


@pytest.fixture
def git_blob_fixture(tmp_path: Path) -> tuple[Path, bytes, str, blobref.BlobRef]:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "T139 Git trust test")
    _git(root, "config", "user.email", "t139-git-trust@example.invalid")
    data = b"trusted positive blob\n"
    (root / "regular.txt").write_bytes(data)
    _git(root, "add", "regular.txt")
    _git(root, "commit", "-q", "-m", "fixture")
    _git(root, "config", "remote.inert.promisor", "false")
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    ref = blobref.BlobRef("regular.txt", commit, hashlib.sha256(data).hexdigest())
    return root, data, commit, ref


def test_normal_repository_remains_accepted(git_blob_fixture) -> None:
    root, data, _commit, ref = git_blob_fixture

    assert blobref.read_pinned_blob(root, ref) == data


def test_path_pollution_cannot_execute_fake_git(
    git_blob_fixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, data, _commit, ref = git_blob_fixture
    marker = tmp_path / "fake-git-executed"
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/usr/bin/python3\n"
        "from pathlib import Path\n"
        f"Path({os.fspath(marker)!r}).write_text('executed', encoding='ascii')\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", os.fspath(fake_bin) + os.pathsep + os.defpath)

    try:
        actual = blobref.read_pinned_blob(root, ref)
    finally:
        assert not marker.exists(), "PATH 上の偽 git が実行された"
    assert actual == data


def test_parent_git_variables_are_scrubbed_and_hardening_reaches_every_call(
    git_blob_fixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, data, _commit, ref = git_blob_fixture
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    _git(attacker, "init", "-q")
    global_config = tmp_path / "attacker.gitconfig"
    global_config.write_text("[core]\n\tpager = false\n", encoding="utf-8")
    injected = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": os.fspath(
            attacker / ".git" / "objects"
        ),
        "GIT_CONFIG_GLOBAL": os.fspath(global_config),
        "GIT_CONFIG_NOSYSTEM": "0",
        "GIT_DIR": os.fspath(attacker / ".git"),
        "GIT_OBJECT_DIRECTORY": os.fspath(attacker / ".git" / "objects"),
        "GIT_WORK_TREE": os.fspath(attacker),
        "GIT_T139_UNRECOGNIZED": "attacker-controlled",
    }
    for key, value in injected.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("PATH", os.fspath(tmp_path))

    original_run = blobref.subprocess.run
    observed: list[tuple[list[str], dict[str, str]]] = []

    def recording_run(arguments, **kwargs):
        observed.append((list(arguments), dict(kwargs["env"])))
        return original_run(arguments, **kwargs)

    monkeypatch.setattr(blobref.subprocess, "run", recording_run)

    assert blobref.read_pinned_blob(root, ref) == data
    assert observed
    expected_git_env = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }
    expected_prefix = [
        os.fspath(blobref._GIT_EXECUTABLE),
        "--no-pager",
        "-c",
        "core.useReplaceRefs=false",
        "-c",
        "core.commitGraph=false",
        "-c",
        "core.fsmonitor=false",
        "--no-replace-objects",
    ]
    for arguments, env in observed:
        assert arguments[: len(expected_prefix)] == expected_prefix
        assert "PATH" not in env
        assert {key: value for key, value in env.items() if key.startswith("GIT_")} == (
            expected_git_env
        )


def test_missing_fixed_git_path_has_identifiable_resolution_error(
    git_blob_fixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _data, _commit, ref = git_blob_fixture
    monkeypatch.setattr(blobref, "_GIT_EXECUTABLE", tmp_path / "missing-git")

    with pytest.raises(blobref.BlobResolutionError, match="git executable.*解決できない"):
        blobref.read_pinned_blob(root, ref)


def test_external_alternate_object_store_is_rejected(
    git_blob_fixture, tmp_path: Path
) -> None:
    source, data, commit, _ref = git_blob_fixture
    target = tmp_path / "alternate-consumer"
    target.mkdir()
    _git(target, "init", "-q")
    alternate_file = target / ".git" / "objects" / "info" / "alternates"
    alternate_file.write_text(
        os.fspath(source / ".git" / "objects") + "\n", encoding="utf-8"
    )
    ref = blobref.BlobRef("regular.txt", commit, hashlib.sha256(data).hexdigest())

    with pytest.raises(blobref.BlobResolutionError, match="alternates"):
        blobref.read_pinned_blob(target, ref)


def test_promisor_remote_is_rejected(git_blob_fixture) -> None:
    root, _data, _commit, ref = git_blob_fixture
    _git(root, "config", "remote.inert.promisor", "true")

    with pytest.raises(blobref.BlobResolutionError, match="promisor remote"):
        blobref.read_pinned_blob(root, ref)


def test_promisor_pack_marker_is_rejected(git_blob_fixture) -> None:
    root, _data, _commit, ref = git_blob_fixture
    marker = root / ".git" / "objects" / "pack" / "synthetic.promisor"
    marker.write_bytes(b"")

    with pytest.raises(blobref.BlobResolutionError, match="promisor object"):
        blobref.read_pinned_blob(root, ref)


def test_partial_clone_configuration_is_rejected(git_blob_fixture) -> None:
    root, _data, _commit, ref = git_blob_fixture
    _git(root, "config", "extensions.partialClone", "inert")

    with pytest.raises(blobref.BlobResolutionError, match="partial clone"):
        blobref.read_pinned_blob(root, ref)


def test_corrupt_commit_graph_is_not_consulted(git_blob_fixture) -> None:
    root, _data, _commit, _ref = git_blob_fixture
    _git(root, "commit-graph", "write", "--reachable")
    commit_graph = root / ".git" / "objects" / "info" / "commit-graph"
    commit_graph.chmod(0o644)
    commit_graph.write_bytes(b"corrupt\n")

    result = blobref._git(root, blobref._git_env(), ["log", "-1", "--format=%H"])

    assert result.returncode == 0
    assert b"commit-graph" not in result.stderr


def test_fsmonitor_hook_is_not_executed(
    git_blob_fixture, tmp_path: Path
) -> None:
    root, _data, _commit, _ref = git_blob_fixture
    marker = tmp_path / "fsmonitor-executed"
    hook = tmp_path / "fsmonitor-hook"
    hook.write_text(
        "#!/usr/bin/python3\n"
        "from pathlib import Path\n"
        f"Path({os.fspath(marker)!r}).write_text('executed', encoding='ascii')\n"
        "print()\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _git(root, "config", "core.fsmonitor", os.fspath(hook))

    result = blobref._git(root, blobref._git_env(), ["status", "--short"])

    assert result.returncode == 0
    assert not marker.exists()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
