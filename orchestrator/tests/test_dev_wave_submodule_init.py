"""CLI tests for registered local-only dev-wave submodule initialization."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from tools import dev_wave_submodule_init as initializer  # noqa: E402
from tools.dev_waves.git_state import create_exact_worktree  # noqa: E402
from tools.dev_waves.schema import DevWavesError, ReasonCode  # noqa: E402


def _git(repo: Path, *args: str, ok: tuple[int, ...] = (0,)) -> str:
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})
    result = subprocess.run(
        ["git", *args], cwd=repo, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode in ok, (args, result.stderr)
    return result.stdout.strip()


def _repo(path: Path, value: str = "base") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(path.parent, "init", "-b", "main", str(path))
    _git(path, "config", "user.name", "Test")
    _git(path, "config", "user.email", "test@example.invalid")
    (path / "value.txt").write_text(f"{value}\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "base")
    return path


def _nested_repo(root: Path) -> Path:
    leaf = _repo(root / "leaf", "leaf")
    middle = _repo(root / "middle", "middle")
    _git(
        middle, "-c", "protocol.file.allow=always", "submodule", "add",
        str(leaf), "nested/leaf",
    )
    _git(middle, "commit", "-am", "add nested submodule")
    repo = _repo(root / "repo", "repo")
    _git(
        repo, "-c", "protocol.file.allow=always", "submodule", "add",
        str(middle), "vendor/middle",
    )
    _git(repo, "commit", "-am", "add middle submodule")
    return repo


def _invoke(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    repo: Path,
    worktree: Path | str,
) -> tuple[int, str, str]:
    monkeypatch.setattr(initializer, "_REPO_ROOT", repo)
    rc = initializer.main(["--worktree", os.fspath(worktree)])
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def test_initializes_nested_submodules_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _nested_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    wave = create_exact_worktree(repo, "submodule-init", 1, base)
    worktree = Path(wave.path)
    nested_value = worktree / "vendor/middle/nested/leaf/value.txt"
    assert not nested_value.exists()

    first_rc, first_out, first_err = _invoke(monkeypatch, capsys, repo, worktree)
    assert first_rc == 0
    assert first_out.startswith("OK: ")
    assert first_err == ""
    assert nested_value.read_text(encoding="utf-8") == "leaf\n"
    first_status = _git(worktree, "submodule", "status", "--recursive").splitlines()
    assert first_status and all(not line.startswith(("-", "+", "U")) for line in first_status)

    second_rc, second_out, second_err = _invoke(monkeypatch, capsys, repo, worktree)
    assert second_rc == 0
    assert second_out.startswith("OK: ")
    assert second_err == ""
    assert _git(worktree, "submodule", "status", "--recursive").splitlines() == first_status


@pytest.mark.parametrize("candidate_kind", ["other-repository", "subdirectory"])
def test_rejects_unregistered_worktree_without_running_update(
    tmp_path: Path,
    candidate_kind: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path / "repo")
    if candidate_kind == "other-repository":
        candidate = _repo(tmp_path / "other")
    else:
        candidate = repo / "inside"
        candidate.mkdir()
    calls: list[str] = []
    monkeypatch.setattr(initializer, "update_submodules_no_fetch", calls.append)

    rc, out, err = _invoke(monkeypatch, capsys, repo, candidate)
    assert rc == 2
    assert out == ""
    assert err.startswith("ERROR: ")
    assert calls == []


def test_rejects_nonexistent_worktree_without_running_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path / "repo")
    calls: list[str] = []
    monkeypatch.setattr(initializer, "update_submodules_no_fetch", calls.append)

    rc, out, err = _invoke(monkeypatch, capsys, repo, tmp_path / "missing")
    assert rc == 2
    assert out == ""
    assert err.startswith("ERROR: ")
    assert calls == []


def test_rejects_stale_registry_entry_from_another_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path / "repo")
    base = _git(repo, "rev-parse", "HEAD")
    wave = create_exact_worktree(repo, "stale-entry", 1, base)
    stale_path = Path(wave.path)
    shutil.rmtree(stale_path)
    _repo(stale_path, "foreign")
    registry = _git(repo, "worktree", "list", "--porcelain")
    assert str(stale_path) in registry
    calls: list[str] = []
    monkeypatch.setattr(initializer, "update_submodules_no_fetch", calls.append)

    rc, out, err = _invoke(monkeypatch, capsys, repo, stale_path)
    assert rc == 2
    assert out == ""
    assert "does not belong to this repository" in err
    assert calls == []


def test_rejects_relative_worktree_without_running_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path / "repo")
    calls: list[str] = []
    monkeypatch.setattr(initializer, "update_submodules_no_fetch", calls.append)

    rc, out, err = _invoke(monkeypatch, capsys, repo, "relative-worktree")
    assert rc == 2
    assert out == ""
    assert "absolute path" in err
    assert calls == []


def test_maps_update_dev_waves_error_to_rc_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path / "repo")
    base = _git(repo, "rev-parse", "HEAD")
    wave = create_exact_worktree(repo, "update-failure", 1, base)

    def fail(_worktree: str) -> None:
        raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
            "label": "submodule", "kind": "test-failure",
        })

    monkeypatch.setattr(initializer, "update_submodules_no_fetch", fail)
    rc, out, err = _invoke(monkeypatch, capsys, repo, Path(wave.path))
    assert rc == 1
    assert out == ""
    assert "ERROR: runtime-io-failure" in err
    assert "test-failure" in err


def test_help_exits_successfully() -> None:
    result = subprocess.run(
        [sys.executable, str(_ROOT / "tools/dev_wave_submodule_init.py"), "--help"],
        cwd=_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0
    assert "--worktree ABSOLUTE_WORKTREE" in result.stdout


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
