# -*- coding: utf-8 -*-
"""tools/check_wave_startup.py の passive startup gate テスト。"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_CHECKER = _ROOT / "tools" / "check_wave_startup.py"
_SPEC = importlib.util.spec_from_file_location("check_wave_startup_under_test", _CHECKER)
assert _SPEC and _SPEC.loader
CWS = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = CWS
_SPEC.loader.exec_module(CWS)


def _git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, (args, completed.stderr)
    return completed.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "-q", "-b", "main", str(repo))
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("# fixture\n", encoding="utf-8")
    handoff = repo / "docs" / "handoff"
    handoff.mkdir(parents=True)
    (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit", "-qm", "base",
    )
    _git(repo, "checkout", "-qb", "work")
    (marker.parent / ".git").write_text("gitdir: fixture\n", encoding="utf-8")
    return repo


def _run(repo: Path, *extra: str) -> int:
    return CWS.main(["--repo", str(repo), *extra])


def test_fresh_normal_worktree_is_accepted(tmp_path: Path) -> None:
    """P4: local main と同じ HEAD の正常 fresh worktree は rc=0。"""
    assert _run(tmp_path_repo := _repo(tmp_path)) == 0
    assert _git(tmp_path_repo, "status", "--porcelain") == ""


def test_default_repo_is_current_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)
    assert CWS.main([]) == 0


def test_fresh_rejects_head_ahead_of_local_main(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "base.txt").write_text("ahead\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit", "-qm", "ahead",
    )
    assert _run(repo) == 1


@pytest.mark.parametrize("state", ["main", "detached"])
def test_fresh_requires_non_main_branch(tmp_path: Path, state: str) -> None:
    repo = _repo(tmp_path)
    if state == "main":
        _git(repo, "checkout", "-q", "main")
    else:
        _git(repo, "checkout", "-q", "--detach")
    assert _run(repo) == 1


@pytest.mark.parametrize("state", ["rebase-merge", "rebase-apply", "MERGE_HEAD"])
def test_resume_rejects_rebase_or_merge_state(tmp_path: Path, state: str) -> None:
    repo = _repo(tmp_path)
    git_dir = Path(_git(repo, "rev-parse", "--absolute-git-dir"))
    path = git_dir / state
    if state == "MERGE_HEAD":
        path.write_text(_git(repo, "rev-parse", "HEAD") + "\n", encoding="ascii")
    else:
        path.mkdir()
    assert _run(repo, "--mode", "resume") == 1


def test_fresh_rejects_dirty_tree(tmp_path: Path) -> None:
    """V7: clean-tree 検査を恒真化するとこの負例が通って赤になる。"""
    repo = _repo(tmp_path)
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    assert _run(repo) == 1


@pytest.mark.parametrize("invalid_marker", ["missing", "directory", "symlink"])
def test_resume_rejects_invalid_submodule_marker(
    tmp_path: Path, invalid_marker: str
) -> None:
    """V6: submodule marker 検査を恒真化するとこの負例が通って赤になる。"""
    repo = _repo(tmp_path)
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.unlink()
    if invalid_marker == "directory":
        marker.mkdir()
    elif invalid_marker == "symlink":
        marker.symlink_to(repo / "base.txt")
    assert _run(repo, "--mode", "resume") == 1


@pytest.mark.parametrize("invalid_git_entry", ["missing", "symlink"])
def test_resume_requires_non_symlink_submodule_git_entry(
    tmp_path: Path, invalid_git_entry: str
) -> None:
    repo = _repo(tmp_path)
    git_entry = repo / "external" / "ccbench" / ".git"
    git_entry.unlink()
    if invalid_git_entry == "symlink":
        git_entry.symlink_to(repo / ".git")
    assert _run(repo, "--mode", "resume") == 1


def test_worktree_handoff_gate_is_opt_in(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "docs" / "handoff" / "active.md").write_text("state\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume") == 0
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1


def test_forbid_worktree_handoff_accepts_only_regular_readme(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 0


def test_forbid_worktree_handoff_rejects_handoff_directory_symlink(
    tmp_path: Path,
) -> None:
    """V13: handoff symlink 検査を恒真化するとこの負例が通って赤になる。"""
    repo = _repo(tmp_path)
    handoff = repo / "docs" / "handoff"
    saved = tmp_path / "saved-handoff"
    handoff.rename(saved)
    external = tmp_path / "empty-external-handoff"
    external.mkdir()
    handoff.symlink_to(external, target_is_directory=True)
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1


def test_forbid_worktree_handoff_counts_readme_directory_as_leftover(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    readme = repo / "docs" / "handoff" / "README.md"
    readme.unlink()
    readme.mkdir()
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1


def test_external_handoff_accepts_existing_file_outside_repo(tmp_path: Path) -> None:
    """P5: worktree handoff の残置なし判定を恒偽化すると正例が赤になる。"""
    repo = _repo(tmp_path)
    external = tmp_path / "external-handoff.md"
    external.write_text("state\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 0


def test_external_handoff_also_rejects_worktree_handoff_leftover(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    external = tmp_path / "external-handoff.md"
    external.write_text("state\n", encoding="utf-8")
    (repo / "docs" / "handoff" / "active.md").write_text("state\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 1


@pytest.mark.parametrize("invalid_kind", ["missing", "directory", "symlink", "inside"])
def test_external_handoff_rejects_invalid_path(
    tmp_path: Path, invalid_kind: str
) -> None:
    repo = _repo(tmp_path)
    external = tmp_path / "candidate-handoff"
    if invalid_kind == "directory":
        external.mkdir()
    elif invalid_kind == "symlink":
        target = tmp_path / "real-handoff.md"
        target.write_text("state\n", encoding="utf-8")
        external.symlink_to(target)
    elif invalid_kind == "inside":
        external = repo / "handoff.md"
        external.write_text("state\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 1


def test_resume_accepts_head_advance_and_dirty_tree(tmp_path: Path) -> None:
    """resume は HEAD/main・branch・clean-tree を再検査しない正例。"""
    repo = _repo(tmp_path)
    (repo / "base.txt").write_text("resumed\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit", "-qm", "resume",
    )
    assert _git(repo, "rev-parse", "HEAD") != _git(repo, "rev-parse", "main")
    (repo / "untracked-on-resume.txt").write_text("allowed\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume") == 0


def test_git_wrapper_is_sanitized_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    poison = {
        "GIT_DIR": "/poison/git-dir",
        "GIT_WORK_TREE": "/poison/work-tree",
        "GIT_INDEX_FILE": "/poison/index",
        "GIT_OBJECT_DIRECTORY": "/poison/objects",
    }
    for key, value in poison.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "poison")
    seen: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["env"] = kwargs["env"]
        return subprocess.CompletedProcess(argv, 0, "clean\n", "")

    monkeypatch.setattr(CWS.subprocess, "run", fake_run)
    result = CWS._git(tmp_path, "status", "--porcelain=v1")
    assert result.returncode == 0
    assert seen["argv"][:4] == ["git", "--no-optional-locks", "-C", str(tmp_path)]
    child_env = seen["env"]
    assert all(key not in child_env for key in poison)
    assert child_env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert child_env["GIT_TERMINAL_PROMPT"] == "0"
    with pytest.raises(ValueError):
        CWS._git(tmp_path, "checkout", "main")


def test_git_execution_error_becomes_aggregated_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git unavailable")

    monkeypatch.setattr(CWS.subprocess, "run", missing_git)
    failures = CWS.check_repository(tmp_path, mode="resume")
    assert failures
    assert all("git unavailable" in failure for failure in failures[:-1])
    assert "submodule is not initialized" in failures[-1]


def test_git_decode_error_becomes_actionable_aggregated_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)

    def invalid_utf8(*args, **kwargs):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(CWS.subprocess, "run", invalid_utf8)
    failures = CWS.check_repository(repo, mode="resume")
    assert failures
    assert all("UTF-8" in failure for failure in failures)
    assert all("是正" in failure for failure in failures)


def test_fresh_symbolic_ref_decode_error_is_git_failure_not_detached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    real_run = CWS.subprocess.run

    def invalid_symbolic_ref(argv, **kwargs):
        if "symbolic-ref" in argv:
            raise UnicodeDecodeError(
                "utf-8", b"\xff", 0, 1, "invalid start byte"
            )
        return real_run(argv, **kwargs)

    monkeypatch.setattr(CWS.subprocess, "run", invalid_symbolic_ref)
    failures = CWS.check_repository(repo, mode="fresh")
    assert any("git の読み取りに失敗" in failure for failure in failures)
    assert any("UTF-8" in failure for failure in failures)
    assert all("detached HEAD" not in failure for failure in failures)


def _advance_main(repo: Path, count: int) -> None:
    """HEAD を work に残したまま local main だけを count 件進める。"""
    _git(repo, "checkout", "-q", "main")
    for index in range(count):
        (repo / f"main-{index}.txt").write_text("main\n", encoding="utf-8")
        _git(repo, "add", f"main-{index}.txt")
        _git(
            repo,
            "-c", "user.name=Test",
            "-c", "user.email=test@example.invalid",
            "commit", "-qm", f"main {index}",
        )
    _git(repo, "checkout", "-q", "work")


def test_main_divergence_notice_is_shown_when_there_is_no_gap(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """乖離 0 でも表示する。無表示だと「乖離なし」と「表示が壊れた」を区別できない。"""
    repo = _repo(tmp_path)
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "0"
    assert _run(repo) == 0
    out = capsys.readouterr().out
    assert "乖離なし" in out
    assert "0 commit" in out


def test_main_divergence_notice_reports_count_without_changing_rc(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """乖離 N は件数付きで出るが rc は変えない (可視化であって gate ではない)。"""
    repo = _repo(tmp_path)
    _advance_main(repo, 3)
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "3"
    assert _run(repo, "--mode", "resume") == 0
    out = capsys.readouterr().out
    assert "3 commit" in out
    assert "遅れ" in out
    assert "乖離なし" not in out


def test_main_divergence_notice_is_fail_open_when_main_ref_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """main ref が無くても受理集合は変わらず、取得できない旨だけを述べる。"""
    repo = _repo(tmp_path)
    _git(repo, "branch", "-D", "main")
    assert _run(repo, "--mode", "resume") == 0
    out = capsys.readouterr().out
    assert "取得できない" in out
    assert "続行" in out


def test_main_divergence_notice_is_shown_even_when_checks_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """検査が落ちる経路でも表示は出る (緑のときだけ出す変異を殺す)。"""
    repo = _repo(tmp_path)
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    assert _run(repo) == 1
    assert "乖離なし" in capsys.readouterr().out


def test_help_discloses_qsub_is_out_of_scope(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        CWS.main(["--help"])
    assert raised.value.code == 0
    assert "qsub" in capsys.readouterr().out


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
