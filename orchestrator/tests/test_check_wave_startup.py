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

_BEHIND_GUIDANCE = (
    "HEAD does not contain local main (1 commit behind): "
    "session 開始時は local main を取り込み、clean tree にしてから "
    "--mode resume を再実行する; session 開始 gate が成功した後の受入前は "
    "gate を再実行せず tools/dev_wave_wait.py acceptance の "
    "post-claim merge に任せる; "
    "待ち手・launcher・runnerのbytesを変える前進は先に取り込む（F524）"
)


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


def _repo(
    tmp_path: Path,
    *,
    main_handoffs: tuple[str, ...] = (),
    executable_main_handoffs: tuple[str, ...] = (),
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    _git(tmp_path, "init", "-q", "-b", "main", str(repo))
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("# fixture\n", encoding="utf-8")
    handoff = repo / "docs" / "handoff"
    handoff.mkdir(parents=True)
    (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")
    for name in (*main_handoffs, *executable_main_handoffs):
        candidate = handoff / name
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("state\n", encoding="utf-8")
        if name in executable_main_handoffs:
            candidate.chmod(0o755)
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


def _ignore(repo: Path, relative_path: str) -> None:
    exclude = repo / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8") as stream:
        stream.write(f"/{relative_path}\n")


def _commit_all(repo: Path, message: str) -> None:
    git_entry = repo / "external" / "ccbench" / ".git"
    saved_git_entry = git_entry.read_bytes() if git_entry.is_file() else None
    if saved_git_entry is not None:
        git_entry.unlink()
    try:
        _git(repo, "add", "-A")
        _git(
            repo,
            "-c", "user.name=Test",
            "-c", "user.email=test@example.invalid",
            "commit", "-qm", message,
        )
    finally:
        if saved_git_entry is not None:
            git_entry.write_bytes(saved_git_entry)


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
def test_resume_rejects_rebase_or_merge_state(
    tmp_path: Path, state: str, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    git_dir = Path(_git(repo, "rev-parse", "--absolute-git-dir"))
    path = git_dir / state
    if state == "MERGE_HEAD":
        path.write_text(_git(repo, "rev-parse", "HEAD") + "\n", encoding="ascii")
    else:
        path.mkdir()
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 1
    assert "rebase/merge in progress" in capsys.readouterr().err


@pytest.mark.parametrize("state", ["rebase-merge", "rebase-apply", "MERGE_HEAD"])
def test_fresh_rejects_rebase_or_merge_state(
    tmp_path: Path, state: str, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    git_dir = Path(_git(repo, "rev-parse", "--absolute-git-dir"))
    path = git_dir / state
    if state == "MERGE_HEAD":
        path.write_text(_git(repo, "rev-parse", "HEAD") + "\n", encoding="ascii")
    else:
        path.mkdir()
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo) == 1
    assert "rebase/merge in progress" in capsys.readouterr().err


def test_fresh_rejects_dirty_tree(tmp_path: Path) -> None:
    """V7: clean-tree 検査を恒真化するとこの負例が通って赤になる。"""
    repo = _repo(tmp_path)
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    assert _run(repo) == 1


def test_resume_accepts_clean_head_equal_to_main(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert _git(repo, "symbolic-ref", "--short", "HEAD") == "work"
    assert _git(repo, "rev-parse", "HEAD") == _git(repo, "rev-parse", "main")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 0


@pytest.mark.parametrize("state", ["main", "detached"])
def test_resume_requires_non_main_branch(
    tmp_path: Path,
    state: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    if state == "main":
        _git(repo, "checkout", "-q", "main")
    else:
        _git(repo, "checkout", "-q", "--detach")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 1
    expected = "branch is main" if state == "main" else "detached HEAD"
    assert expected in capsys.readouterr().err


@pytest.mark.parametrize("invalid_marker", ["missing", "directory", "symlink"])
def test_resume_rejects_invalid_submodule_marker(
    tmp_path: Path,
    invalid_marker: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """V6: submodule marker 検査を恒真化するとこの負例が通って赤になる。"""
    repo = _repo(tmp_path)
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.unlink()
    if invalid_marker == "symlink":
        marker.symlink_to(repo / "base.txt")
    _commit_all(repo, f"invalid marker {invalid_marker}")
    if invalid_marker == "directory":
        marker.mkdir()
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 1
    diagnostic = capsys.readouterr().err
    assert "submodule is not initialized" in diagnostic
    assert (
        "external/ccbench/CMakeLists.txt must be a non-symlink regular file"
        in diagnostic
    )
    assert "external/ccbench/.git must exist without being a symlink" in diagnostic
    assert (
        "検査対象の worktree root で python3 tools/dev_wave_submodule_init.py "
        "--worktree <path> を実行し再検査する"
        in diagnostic
    )


@pytest.mark.parametrize("invalid_git_entry", ["missing", "symlink"])
def test_resume_requires_non_symlink_submodule_git_entry(
    tmp_path: Path,
    invalid_git_entry: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    git_entry = repo / "external" / "ccbench" / ".git"
    git_entry.unlink()
    if invalid_git_entry == "symlink":
        git_entry.symlink_to(repo / ".git")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 1
    diagnostic = capsys.readouterr().err
    assert "submodule is not initialized" in diagnostic
    assert (
        "external/ccbench/CMakeLists.txt must be a non-symlink regular file"
        in diagnostic
    )
    assert "external/ccbench/.git must exist without being a symlink" in diagnostic
    assert (
        "検査対象の worktree root で python3 tools/dev_wave_submodule_init.py "
        "--worktree <path> を実行し再検査する"
        in diagnostic
    )


@pytest.mark.parametrize("invalid_marker", ["missing", "directory", "symlink"])
def test_fresh_rejects_invalid_submodule_marker(
    tmp_path: Path,
    invalid_marker: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.unlink()
    if invalid_marker == "symlink":
        marker.symlink_to(repo / "base.txt")
    _commit_all(repo, f"fresh invalid marker {invalid_marker}")
    if invalid_marker == "directory":
        marker.mkdir()
    _git(repo, "branch", "-f", "main", "HEAD")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo) == 1
    assert "submodule is not initialized" in capsys.readouterr().err


@pytest.mark.parametrize("invalid_git_entry", ["missing", "symlink"])
def test_fresh_requires_non_symlink_submodule_git_entry(
    tmp_path: Path,
    invalid_git_entry: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    git_entry = repo / "external" / "ccbench" / ".git"
    git_entry.unlink()
    if invalid_git_entry == "symlink":
        git_entry.symlink_to(repo / ".git")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo) == 1
    assert "submodule is not initialized" in capsys.readouterr().err


def test_worktree_handoff_gate_is_opt_in(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    (repo / "docs" / "handoff" / "active.md").write_text("state\n", encoding="utf-8")
    _ignore(repo, "docs/handoff/active.md")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 0
    capsys.readouterr()
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1
    assert "worktree-local handoff remains" in capsys.readouterr().err


def test_forbid_worktree_handoff_accepts_only_regular_readme(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 0


def test_forbid_worktree_handoff_rejects_handoff_directory_symlink(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """V13: handoff symlink 検査を恒真化するとこの負例が通って赤になる。"""
    repo = _repo(tmp_path)
    handoff = repo / "docs" / "handoff"
    saved = tmp_path / "saved-handoff"
    handoff.rename(saved)
    external = tmp_path / "empty-external-handoff"
    external.mkdir()
    handoff.symlink_to(external, target_is_directory=True)
    _commit_all(repo, "symlink handoff directory")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1
    assert "docs/handoff is a symlink" in capsys.readouterr().err


def test_forbid_worktree_handoff_rejects_handoff_root_regular_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    handoff = repo / "docs" / "handoff"
    (handoff / "README.md").unlink()
    handoff.rmdir()
    handoff.write_text("not a directory\n", encoding="utf-8")
    _commit_all(repo, "replace handoff directory with regular file")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1
    diagnostic = capsys.readouterr().err
    assert "docs/handoff is not a directory" in diagnostic
    assert diagnostic.index("docs/handoff is not a directory") < diagnostic.index(
        "worktree handoff index contains docs/handoff itself"
    )


def test_forbid_worktree_handoff_accepts_missing_handoff_root(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    handoff = repo / "docs" / "handoff"
    (handoff / "README.md").unlink()
    handoff.rmdir()
    _commit_all(repo, "remove handoff directory")
    assert not handoff.exists()
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 0


def test_forbid_worktree_handoff_counts_readme_directory_as_leftover(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    readme = repo / "docs" / "handoff" / "README.md"
    readme.unlink()
    _commit_all(repo, "remove handoff readme")
    readme.mkdir()
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1
    assert "worktree-local handoff remains (README.md)" in capsys.readouterr().err


def test_external_handoff_accepts_existing_file_outside_repo(tmp_path: Path) -> None:
    """P5: worktree handoff の残置なし判定を恒偽化すると正例が赤になる。"""
    repo = _repo(tmp_path)
    external = tmp_path / "external-handoff.md"
    external.write_text("state\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 0


def test_external_handoff_also_rejects_worktree_handoff_leftover(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    external = tmp_path / "external-handoff.md"
    external.write_text("state\n", encoding="utf-8")
    (repo / "docs" / "handoff" / "active.md").write_text("state\n", encoding="utf-8")
    _ignore(repo, "docs/handoff/active.md")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 1
    assert "worktree-local handoff remains" in capsys.readouterr().err


def test_worktree_handoff_accepts_main_landed_regular_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path, main_handoffs=("landed.md",))
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 0


def test_worktree_handoff_accepts_main_landed_executable_file(tmp_path: Path) -> None:
    relative_path = "docs/handoff/executable.md"
    repo = _repo(tmp_path, executable_main_handoffs=("executable.md",))
    assert _git(repo, "ls-files", "--stage", "--", relative_path).startswith("100755 ")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 0


def test_external_handoff_accepts_main_landed_regular_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path, main_handoffs=("landed.md",))
    external = tmp_path / "external-handoff.md"
    external.write_text("state\n", encoding="utf-8")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 0


def test_worktree_handoff_rejects_ignored_untracked_regular_file(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    (repo / "docs" / "handoff" / "untracked.md").write_text(
        "state\n", encoding="utf-8"
    )
    _ignore(repo, "docs/handoff/untracked.md")
    assert _git(repo, "status", "--porcelain") == ""
    failures = CWS._check_worktree_handoff(repo)
    assert failures == [
        "worktree-local handoff remains (untracked.md): "
        "外部 handoff を正本にして worktree 内の残置を除く"
    ]


def test_worktree_handoff_rejects_branch_only_committed_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "docs" / "handoff" / "branch-only.md").write_text(
        "state\n", encoding="utf-8"
    )
    _commit_all(repo, "branch-only handoff")
    assert _git(repo, "status", "--porcelain") == ""
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index entry is absent from main "
        "(docs/handoff/branch-only.md): main に land してから再検査する"
    ]


def test_worktree_handoff_rejects_index_oid_different_from_main(tmp_path: Path) -> None:
    repo = _repo(tmp_path, main_handoffs=("changed.md",))
    relative_path = "docs/handoff/changed.md"
    (repo / relative_path).write_text("changed\n", encoding="utf-8")
    _git(repo, "add", relative_path)
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index OID differs from main "
        "(docs/handoff/changed.md): index を main と同じ内容へ戻す"
    ]


def test_worktree_handoff_rejects_assume_unchanged_entry(tmp_path: Path) -> None:
    repo = _repo(tmp_path, main_handoffs=("flagged.md",))
    relative_path = "docs/handoff/flagged.md"
    _git(repo, "update-index", "--assume-unchanged", relative_path)
    assert _git(repo, "ls-files", "-v", "--", relative_path).startswith("h ")
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index tag is not H "
        "(docs/handoff/flagged.md: h): "
        "assume-unchanged / skip-worktree 等の flag を解除する"
    ]


def test_worktree_handoff_rejects_skip_worktree_entry(tmp_path: Path) -> None:
    repo = _repo(tmp_path, main_handoffs=("flagged.md",))
    relative_path = "docs/handoff/flagged.md"
    _git(repo, "update-index", "--skip-worktree", relative_path)
    assert _git(repo, "ls-files", "-v", "--", relative_path).startswith("S ")
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index tag is not H "
        "(docs/handoff/flagged.md: S): "
        "assume-unchanged / skip-worktree 等の flag を解除する"
    ]


def test_worktree_handoff_rejects_missing_skip_worktree_entry_via_main(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path, main_handoffs=("flagged.md",))
    relative_path = "docs/handoff/flagged.md"
    _git(repo, "update-index", "--skip-worktree", relative_path)
    (repo / relative_path).unlink()
    assert _git(repo, "ls-files", "-v", "--", relative_path).startswith("S ")
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 1
    assert (
        "worktree handoff index tag is not H "
        "(docs/handoff/flagged.md: S)"
        in capsys.readouterr().err
    )


@pytest.mark.parametrize("stage", ["1", "2", "3"])
def test_worktree_handoff_rejects_unmerged_index_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    repo = tmp_path / "repo"
    candidate = repo / "docs" / "handoff" / "unmerged.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("state\n", encoding="utf-8")
    raw = f"H 100644 {'1' * 40} {stage}\tdocs/handoff/unmerged.md\0"
    monkeypatch.setattr(CWS, "_git_raw", lambda repo, *args: CWS.GitResult(0, raw, ""))
    monkeypatch.setattr(
        CWS,
        "_git",
        lambda repo, *args: pytest.fail("stage rejection must precede rev-parse"),
    )
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index stage is not 0 "
        f"(docs/handoff/unmerged.md: {stage}): 未 merge の index record を解消する"
    ]


def _assert_worktree_handoff_rejects_index_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    repo = tmp_path / f"repo-{mode}"
    candidate = repo / "docs" / "handoff" / "mode.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("regular filesystem entry\n", encoding="utf-8")
    raw = f"H {mode} {'1' * 40} 0\tdocs/handoff/mode.md\0"
    monkeypatch.setattr(CWS, "_git_raw", lambda repo, *args: CWS.GitResult(0, raw, ""))
    monkeypatch.setattr(
        CWS,
        "_git",
        lambda repo, *args: pytest.fail("mode rejection must precede rev-parse"),
    )
    assert candidate.is_file() and not candidate.is_symlink()
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index mode is not 100644/100755 "
        f"(docs/handoff/mode.md: {mode}): regular file mode に修復する"
    ]


def test_worktree_handoff_rejects_symlink_index_mode_with_regular_filesystem_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _assert_worktree_handoff_rejects_index_mode(tmp_path, monkeypatch, "120000")


def test_worktree_handoff_rejects_gitlink_index_mode_with_regular_filesystem_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _assert_worktree_handoff_rejects_index_mode(tmp_path, monkeypatch, "160000")


@pytest.mark.parametrize("entry_kind", ["symlink", "directory"])
def test_worktree_handoff_rejects_non_regular_filesystem_entry_with_accepted_index(
    tmp_path: Path, entry_kind: str
) -> None:
    repo = _repo(tmp_path, main_handoffs=("entry.md",))
    candidate = repo / "docs" / "handoff" / "entry.md"
    candidate.unlink()
    if entry_kind == "symlink":
        candidate.symlink_to(repo / "base.txt")
    else:
        candidate.mkdir()
    assert CWS._check_worktree_handoff(repo) == [
        "worktree-local handoff remains (entry.md): "
        "外部 handoff を正本にして worktree 内の残置を除く"
    ]


def test_worktree_handoff_rejects_directory_with_tracked_descendant(
    tmp_path: Path,
) -> None:
    """直下 directory の membership と filesystem 型による二重拒否を固定する。"""
    repo = _repo(tmp_path, main_handoffs=("archive/landed.md",))
    assert _git(repo, "status", "--porcelain") == ""
    assert CWS._check_worktree_handoff(repo) == [
        "worktree-local handoff remains (archive): "
        "外部 handoff を正本にして worktree 内の残置を除く"
    ]


def test_worktree_handoff_rejects_index_record_for_handoff_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    (repo / "docs" / "handoff").mkdir(parents=True)
    raw = f"H 160000 {'1' * 40} 0\tdocs/handoff\0"
    monkeypatch.setattr(CWS, "_git_raw", lambda repo, *args: CWS.GitResult(0, raw, ""))
    failures = CWS._check_worktree_handoff(repo)
    assert failures
    assert "index contains docs/handoff itself" in failures[0]


def test_worktree_handoff_rejects_root_index_record_when_handoff_root_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = f"H 160000 {'1' * 40} 0\tdocs/handoff\0"
    monkeypatch.setattr(CWS, "_git_raw", lambda repo, *args: CWS.GitResult(0, raw, ""))
    assert CWS._check_worktree_handoff(tmp_path / "missing-repo") == [
        "worktree handoff index contains docs/handoff itself: "
        "gitlink 等の root entry を除去する"
    ]


def test_worktree_handoff_rejects_duplicate_index_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    (repo / "docs" / "handoff").mkdir(parents=True)
    record = f"H 100644 {'1' * 40} 0\tdocs/handoff/duplicate.md\0"
    monkeypatch.setattr(
        CWS,
        "_git_raw",
        lambda repo, *args: CWS.GitResult(0, record + record, ""),
    )
    monkeypatch.setattr(
        CWS,
        "_git",
        lambda repo, *args: pytest.fail("duplicate rejection must precede rev-parse"),
    )
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index contains duplicate path "
        "(docs/handoff/duplicate.md): 重複 record を解消する"
    ]


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        pytest.param(CWS.GitResult(1, "", "forced failure"), "git の読み取りに失敗", id="rc"),
        pytest.param(
            CWS.GitResult(0, f"H 100644 {'1' * 40} 0\tdocs/handoff/file.md", ""),
            "NUL 終端でない",
            id="non-nul",
        ),
        pytest.param(CWS.GitResult(0, "malformed\0", ""), "record を解釈できない", id="record"),
    ],
)
def test_worktree_handoff_ls_files_failure_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    result: CWS.GitResult,
    expected: str,
) -> None:
    monkeypatch.setattr(CWS, "_git_raw", lambda repo, *args: result)
    failures = CWS._check_worktree_handoff(tmp_path / "missing-repo")
    assert failures
    assert expected in failures[0]


def test_worktree_handoff_rev_parse_failure_rejects_that_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, main_handoffs=("unreadable.md",))
    real_git = CWS._git

    def fail_one_main_entry(repo: Path, *args: str) -> CWS.GitResult:
        if args[-1] == "refs/heads/main:docs/handoff/unreadable.md":
            return CWS.GitResult(1, "", "forced failure")
        return real_git(repo, *args)

    monkeypatch.setattr(CWS, "_git", fail_one_main_entry)
    assert CWS._check_worktree_handoff(repo) == [
        "worktree handoff index entry is absent from main "
        "(docs/handoff/unreadable.md): main に land してから再検査する"
    ]


def test_worktree_handoff_rejects_untracked_readme(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    readme = repo / "docs" / "handoff" / "README.md"
    readme.unlink()
    _commit_all(repo, "delete readme on work branch")
    readme.write_text("untracked replacement\n", encoding="utf-8")
    _ignore(repo, "docs/handoff/README.md")
    assert _git(repo, "status", "--porcelain") == ""
    assert CWS._check_worktree_handoff(repo) == [
        "worktree-local handoff remains (README.md): "
        "外部 handoff を正本にして worktree 内の残置を除く"
    ]


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("非ASCII.md", id="non-ascii"),
        pytest.param("tab\tname.md", id="tab"),
        pytest.param("line\nname.md", id="newline"),
        pytest.param('quote"name.md', id="quote"),
    ],
)
def test_worktree_handoff_accepts_main_landed_special_character_name(
    tmp_path: Path, name: str
) -> None:
    repo = _repo(tmp_path, main_handoffs=(name,))
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--forbid-worktree-handoff") == 0


@pytest.mark.parametrize("invalid_kind", ["missing", "directory", "symlink", "inside"])
def test_external_handoff_rejects_invalid_path(
    tmp_path: Path,
    invalid_kind: str,
    capsys: pytest.CaptureFixture[str],
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
        _commit_all(repo, "inside handoff candidate")
        assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume", "--external-handoff", str(external)) == 1
    assert "external handoff" in capsys.readouterr().err


def test_resume_accepts_clean_head_advance(tmp_path: Path) -> None:
    """resume は local main を包含する clean な自 wave commit を受理する。"""
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
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "0"
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 0


def test_resume_rejects_dirty_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    (repo / "untracked-on-resume.txt").write_text("dirty\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume") == 1
    assert "working tree is not clean" in capsys.readouterr().err


def test_check_repository_rejects_unknown_mode(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert _git(repo, "status", "--porcelain") == ""
    failures = CWS.check_repository(repo, mode="unsafe")
    assert failures == [
        "unsupported startup mode 'unsafe': "
        "fresh / resume / midflight のいずれかを明示する"
    ]


def test_mode_parser_contract_is_exact(capsys: pytest.CaptureFixture[str]) -> None:
    mode_action = next(action for action in CWS._parser()._actions if action.dest == "mode")
    assert mode_action.choices == ("fresh", "resume", "midflight")
    assert mode_action.default == "fresh"
    with pytest.raises(SystemExit) as raised:
        CWS.main(["--mode", "unsafe"])
    assert raised.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_default_mode_remains_fresh_despite_resume_environment_and_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    (repo / "base.txt").write_text("ahead\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit", "-qm", "ahead",
    )
    _git(repo, "config", "check-wave-startup.mode", "resume")
    monkeypatch.setenv("CHECK_WAVE_STARTUP_MODE", "resume")
    monkeypatch.setenv("IZANAGI_WAVE_STARTUP_MODE", "resume")
    monkeypatch.setenv("CLAUDECODE", "resume")
    assert CWS.main(["--repo", str(repo)]) == 1
    assert CWS.main(["--repo", str(repo), "--mode", "resume"]) == 0


def test_default_mode_does_not_follow_midflight_environment_or_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    _advance_work(repo)
    _git(repo, "config", "check-wave-startup.mode", "midflight")
    monkeypatch.setenv("CHECK_WAVE_STARTUP_MODE", "midflight")
    monkeypatch.setenv("IZANAGI_WAVE_STARTUP_MODE", "midflight")
    monkeypatch.setenv("CLAUDECODE", "midflight")
    assert CWS.main(["--repo", str(repo)]) == 1
    assert CWS.main(["--repo", str(repo), "--mode", "midflight"]) == 0


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr", "expected"),
    [
        pytest.param(1, "0", "forced failure", "git の読み取りに失敗", id="rc-nonzero-zero"),
        pytest.param(0, "", "", "ASCII 整数でない", id="empty"),
        pytest.param(0, "text", "", "ASCII 整数でない", id="text"),
        pytest.param(0, "+0", "", "ASCII 整数でない", id="signed"),
        pytest.param(0, "０", "", "ASCII 整数でない", id="full-width"),
        pytest.param(0, "0 0", "", "ASCII 整数でない", id="multiple-tokens"),
        pytest.param(0, "00", "", "ASCII 整数でない", id="leading-zero"),
    ],
)
def test_head_contains_main_fails_closed_for_invalid_rev_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    stderr: str,
    expected: str,
) -> None:
    monkeypatch.setattr(CWS, "_check_no_grafts", lambda repo: [])
    rev_list_calls: list[tuple[str, ...]] = []

    def fake_git(repo: Path, *args: str) -> CWS.GitResult:
        assert args[0] == "rev-list"
        rev_list_calls.append(args)
        return CWS.GitResult(returncode, stdout, stderr)

    monkeypatch.setattr(CWS, "_git", fake_git)
    failures = CWS._check_head_contains_main(tmp_path)
    assert failures
    assert any(expected in failure for failure in failures)
    assert rev_list_calls == [("rev-list", "--count", "HEAD..refs/heads/main")]


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        pytest.param(CWS.GitResult(1, "", "forced failure"), "git の読み取りに失敗", id="rc"),
        pytest.param(CWS.GitResult(0, "", ""), "git common directory が空", id="empty"),
        pytest.param(CWS.GitResult(0, "relative", ""), "絶対 path でない", id="relative"),
    ],
)
def test_grafts_check_fails_closed_for_invalid_common_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    result: CWS.GitResult,
    expected: str,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(repo: Path, *args: str) -> CWS.GitResult:
        calls.append(args)
        return result

    monkeypatch.setattr(CWS, "_git", fake_git)
    failures = CWS._check_no_grafts(tmp_path)
    assert failures
    assert expected in failures[0]
    assert calls == [("rev-parse", "--path-format=absolute", "--git-common-dir")]


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
    monkeypatch.setenv("GIT_NO_REPLACE_OBJECTS", "0")
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
    assert child_env["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert CWS._READ_ONLY_GIT_SUBCOMMANDS == frozenset(
        {"ls-files", "rev-list", "rev-parse", "status", "symbolic-ref"}
    )
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
    git_failures = failures[:-1]
    assert git_failures
    assert all("git unavailable" in failure for failure in git_failures)
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


def _advance_work(repo: Path, name: str = "work-ahead.txt") -> None:
    (repo / name).write_text("work\n", encoding="utf-8")
    _git(repo, "add", name)
    _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit", "-qm", "work ahead",
    )


def test_midflight_check_sequence_is_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def check(name: str):
        def record(repo: Path) -> list[str]:
            calls.append(name)
            return []

        return record

    def measure(repo: Path) -> tuple[list[str], str | None]:
        calls.append("measure")
        return [], "7"

    monkeypatch.setattr(CWS, "_check_no_grafts", check("grafts"))
    monkeypatch.setattr(CWS, "_check_main_divergence_measurable", measure)
    monkeypatch.setattr(CWS, "_check_main_is_direct_ref", check("direct-main"))
    monkeypatch.setattr(CWS, "_check_fresh_branch", check("branch"))
    monkeypatch.setattr(CWS, "_check_no_operation_in_progress", check("operation"))
    monkeypatch.setattr(CWS, "_check_submodule_marker", check("submodule"))
    monkeypatch.setattr(
        CWS,
        "_check_head_matches_main",
        lambda repo: pytest.fail("midflight must not check HEAD==main"),
    )
    monkeypatch.setattr(
        CWS,
        "_check_head_contains_main",
        lambda repo: pytest.fail("midflight must not check main containment"),
    )
    monkeypatch.setattr(
        CWS,
        "_check_clean_tree",
        lambda repo: pytest.fail("Python API midflight must not gate on clean tree"),
    )
    monkeypatch.setattr(
        CWS,
        "_check_worktree_handoff",
        lambda repo: pytest.fail("midflight must not inspect worktree handoff"),
    )
    monkeypatch.setattr(
        CWS,
        "_check_external_handoff_file",
        lambda repo, handoff: pytest.fail("midflight must not inspect external handoff"),
    )

    assert CWS.check_repository(tmp_path, mode="midflight") == []
    assert calls == [
        "grafts",
        "measure",
        "direct-main",
        "branch",
        "operation",
        "submodule",
    ]


@pytest.mark.parametrize("count", ["0", "1", "343", "123456789012345678901234567890"])
def test_midflight_divergence_measurement_accepts_any_canonical_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    count: str,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(repo: Path, *args: str) -> CWS.GitResult:
        calls.append(args)
        return CWS.GitResult(0, count, "")

    monkeypatch.setattr(CWS, "_git", fake_git)
    failures, observation = CWS._check_main_divergence_measurable(tmp_path)
    assert failures == []
    assert observation == count
    assert calls == [("rev-list", "--count", "HEAD..refs/heads/main")]


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr", "expected"),
    [
        pytest.param(1, "0", "forced failure", "git の読み取りに失敗", id="rc"),
        pytest.param(0, "", "", "ASCII 整数でない", id="empty"),
        pytest.param(0, "+0", "", "ASCII 整数でない", id="plus-signed"),
        pytest.param(0, "-1", "", "ASCII 整数でない", id="minus-signed"),
        pytest.param(0, "０", "", "ASCII 整数でない", id="full-width"),
        pytest.param(0, "0 0", "", "ASCII 整数でない", id="multiple-tokens"),
        pytest.param(0, "00", "", "ASCII 整数でない", id="leading-zero"),
    ],
)
def test_midflight_divergence_measurement_fails_closed_for_invalid_rev_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    stderr: str,
    expected: str,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(repo: Path, *args: str) -> CWS.GitResult:
        calls.append(args)
        return CWS.GitResult(returncode, stdout, stderr)

    monkeypatch.setattr(CWS, "_git", fake_git)
    failures, observation = CWS._check_main_divergence_measurable(tmp_path)
    assert len(failures) == 1
    assert expected in failures[0]
    assert observation is None
    assert calls == [("rev-list", "--count", "HEAD..refs/heads/main")]


def test_midflight_integrated_gate_rejects_unborn_work_branch(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "unborn"
    _git(tmp_path, "init", "-q", "-b", "work", str(repo))
    empty_tree = _git(repo, "hash-object", "-t", "tree", "-w", "/dev/null")
    main_commit = _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit-tree", empty_tree, "-m", "main base",
    )
    _git(repo, "update-ref", "refs/heads/main", main_commit)
    exclude = repo / ".git" / "info" / "exclude"
    exclude.write_text("external/\ndocs/\n", encoding="ascii")
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("# fixture\n", encoding="utf-8")
    (marker.parent / ".git").write_text("gitdir: fixture\n", encoding="utf-8")
    handoff = repo / "docs" / "handoff"
    handoff.mkdir(parents=True)
    (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")

    assert _git(repo, "symbolic-ref", "--short", "HEAD") == "work"
    assert CWS._git(repo, "symbolic-ref", "--quiet", "refs/heads/main").returncode == 1
    assert _git(repo, "status", "--porcelain") == ""
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    assert "HEAD/local main divergence measurement: git の読み取りに失敗" in failures[0]


@pytest.mark.parametrize("state", ["main", "detached"])
def test_midflight_rejects_main_or_detached_branch(
    tmp_path: Path,
    state: str,
) -> None:
    repo = _repo(tmp_path)
    if state == "main":
        _git(repo, "checkout", "-q", "main")
    else:
        _git(repo, "checkout", "-q", "--detach")
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    expected = "branch is main" if state == "main" else "detached HEAD"
    assert expected in failures[0]


@pytest.mark.parametrize("state", ["rebase-merge", "rebase-apply", "MERGE_HEAD"])
def test_midflight_rejects_rebase_or_merge_state(
    tmp_path: Path,
    state: str,
) -> None:
    repo = _repo(tmp_path)
    git_dir = Path(_git(repo, "rev-parse", "--absolute-git-dir"))
    path = git_dir / state
    if state == "MERGE_HEAD":
        path.write_text(_git(repo, "rev-parse", "HEAD") + "\n", encoding="ascii")
    else:
        path.mkdir()
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    assert "rebase/merge in progress" in failures[0]


@pytest.mark.parametrize("invalid_marker", ["missing", "directory", "symlink"])
def test_midflight_rejects_invalid_submodule_marker(
    tmp_path: Path,
    invalid_marker: str,
) -> None:
    repo = _repo(tmp_path)
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.unlink()
    if invalid_marker == "symlink":
        marker.symlink_to(repo / "base.txt")
    _commit_all(repo, f"midflight invalid marker {invalid_marker}")
    if invalid_marker == "directory":
        marker.mkdir()
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    assert "submodule is not initialized" in failures[0]


@pytest.mark.parametrize("invalid_git_entry", ["missing", "symlink"])
def test_midflight_requires_non_symlink_submodule_git_entry(
    tmp_path: Path,
    invalid_git_entry: str,
) -> None:
    repo = _repo(tmp_path)
    git_entry = repo / "external" / "ccbench" / ".git"
    git_entry.unlink()
    if invalid_git_entry == "symlink":
        git_entry.symlink_to(repo / ".git")
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    assert "submodule is not initialized" in failures[0]


def test_midflight_rejects_symbolic_main(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "symbolic-ref", "refs/heads/main", "refs/heads/work")
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    assert "local main is a symbolic ref" in failures[0]


@pytest.mark.parametrize("kind", ["file", "dangling-symlink"])
def test_midflight_rejects_legacy_graft_metadata(
    tmp_path: Path,
    kind: str,
) -> None:
    repo = _repo(tmp_path)
    grafts = Path(
        _git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts")
    )
    grafts.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        _advance_main(repo, 1)
        _advance_work(repo)
        head = _git(repo, "rev-parse", "HEAD")
        main = _git(repo, "rev-parse", "refs/heads/main")
        grafts.write_text(f"{head} {main}\n", encoding="ascii")
    else:
        grafts.symlink_to(tmp_path / "missing-grafts-target")
    failures = CWS.check_repository(repo, mode="midflight")
    assert len(failures) == 1
    assert "legacy graft metadata exists" in failures[0]


@pytest.mark.parametrize("option", ["forbid_worktree_handoff", "external_handoff"])
def test_midflight_rejects_handoff_options_in_python_api_before_repo_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    option: str,
) -> None:
    calls: list[str] = []

    def unexpected(repo: Path) -> list[str]:
        calls.append("repository check")
        return []

    for name in (
        "_check_no_grafts",
        "_check_main_is_direct_ref",
        "_check_fresh_branch",
        "_check_no_operation_in_progress",
        "_check_submodule_marker",
    ):
        monkeypatch.setattr(CWS, name, unexpected)

    def unexpected_measurement(repo: Path) -> tuple[list[str], str | None]:
        calls.append("repository measurement")
        return [], "0"

    monkeypatch.setattr(
        CWS, "_check_main_divergence_measurable", unexpected_measurement
    )

    kwargs = {option: True if option == "forbid_worktree_handoff" else tmp_path / "handoff"}
    failures = CWS.check_repository(tmp_path / "not-a-repo", mode="midflight", **kwargs)
    assert failures == [
        "midflight mode does not accept --forbid-worktree-handoff / "
        "--external-handoff; 開始 gate には fresh / resume を使う"
    ]
    assert calls == []


@pytest.mark.parametrize("option", ["forbid-worktree-handoff", "external-handoff"])
def test_midflight_rejects_handoff_options_in_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    option: str,
) -> None:
    repo = _repo(tmp_path)
    argv = ["--repo", str(repo), "--mode", "midflight", f"--{option}"]
    if option == "external-handoff":
        argv.append(str(tmp_path / "handoff.md"))
    with pytest.raises(SystemExit) as raised:
        CWS.main(argv)
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "--mode midflight does not accept" in captured.err


@pytest.mark.parametrize("dirty_kind", ["tracked", "untracked"])
def test_midflight_accepts_self_commit_behind_main_and_dirty_tree_while_fresh_and_resume_reject(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    dirty_kind: str,
) -> None:
    repo = _repo(tmp_path)
    _advance_work(repo)
    _advance_main(repo, 1)
    if dirty_kind == "tracked":
        (repo / "base.txt").write_text("tracked dirt\n", encoding="utf-8")
    else:
        (repo / "untracked-midflight.txt").write_text("untracked dirt\n", encoding="utf-8")

    fresh_failures = CWS.check_repository(repo, mode="fresh")
    resume_failures = CWS.check_repository(repo, mode="resume")
    assert any("HEAD != local main" in failure for failure in fresh_failures)
    assert any("working tree is not clean" in failure for failure in fresh_failures)
    assert any("HEAD does not contain local main" in failure for failure in resume_failures)
    assert any("working tree is not clean" in failure for failure in resume_failures)
    assert _run(repo, "--mode", "midflight") == 0
    captured = capsys.readouterr()
    assert "OK: wave startup checks passed (midflight;" in captured.out
    assert "NOTE: local main より 1 commit 遅れている (gate の実測値; これは関門ではない)" in captured.out
    assert "NOTE: working tree is not clean (midflight は clean tree を検査しない)" in captured.out
    assert captured.err == ""


def test_midflight_does_not_require_wave_commit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 3)
    assert _git(repo, "rev-list", "--count", "refs/heads/main..HEAD") == "0"
    assert _git(repo, "rev-list", "--count", "HEAD..refs/heads/main") == "3"
    assert _run(repo, "--mode", "midflight") == 0
    captured = capsys.readouterr()
    assert "NOTE: local main より 3 commit 遅れている (gate の実測値; これは関門ではない)" in captured.out
    assert "NOTE: working tree is clean (midflight は clean tree を検査しない)" in captured.out
    assert captured.err == ""


def test_midflight_scope_notes_are_shown_when_gate_rejects(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    assert _run(repo, "--mode", "midflight") == 1
    captured = capsys.readouterr()
    assert "開始 gate (fresh / resume) の代用ではない" in captured.out
    assert "HEAD/main 関係・clean tree・handoff を検査しない" in captured.out
    assert "NOTE: local main より 0 commit 遅れている (gate の実測値; これは関門ではない)" in captured.out
    assert "NOTE: working tree is clean (midflight は clean tree を検査しない)" in captured.out
    assert "branch is main" in captured.err


def test_midflight_main_reports_gate_measurement_not_info_measurement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    real_git = CWS._git
    counts = iter(("0", "343"))

    def staged_rev_list(repo: Path, *args: str) -> CWS.GitResult:
        if args == ("rev-list", "--count", "HEAD..refs/heads/main"):
            return CWS.GitResult(0, next(counts), "")
        return real_git(repo, *args)

    monkeypatch.setattr(CWS, "_git", staged_rev_list)
    assert _run(repo, "--mode", "midflight") == 0
    captured = capsys.readouterr()
    assert "INFO: local main との乖離なし (0 commit" in captured.out
    assert "NOTE: local main より 343 commit 遅れている (gate の実測値; これは関門ではない)" in captured.out
    assert "NOTE: local main より 0 commit 遅れている" not in captured.out
    assert captured.err == ""


def test_resume_rejects_head_behind_local_main(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    assert _git(repo, "rev-list", "--count", "HEAD..refs/heads/main") == "1"
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 1
    assert capsys.readouterr().err == f"NG: {_BEHIND_GUIDANCE}\n"


def test_resume_behind_guidance_names_acceptance_postclaim_merge(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    completed = subprocess.run(
        [
            sys.executable,
            str(_CHECKER),
            "--repo",
            str(repo),
            "--mode",
            "resume",
        ],
        cwd=repo,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stderr == f"NG: {_BEHIND_GUIDANCE}\n"
    assert (
        "待ち手・launcher・runnerのbytesを変える前進は先に取り込む（F524）"
        in completed.stderr
    )


def test_resume_behind_with_dirty_tree_keeps_single_failure_rc(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    assert _run(repo, "--mode", "resume") == 1
    diagnostics = capsys.readouterr().err.splitlines()
    assert diagnostics == [
        f"NG: {_BEHIND_GUIDANCE}",
        "NG: working tree is not clean: 変更を commit または退避してから再実行する",
    ]


def test_resume_malformed_behind_count_is_rejected_without_acceptance_guidance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CWS, "_check_no_grafts", lambda repo: [])
    monkeypatch.setattr(
        CWS,
        "_git",
        lambda repo, *args: CWS.GitResult(0, "00", ""),
    )
    failures = CWS._check_head_contains_main(tmp_path)
    assert failures == [
        "HEAD/local main containment: rev-list の出力が canonical な非負の "
        "ASCII 整数でない (00): git repository を確認する"
    ]
    assert all("tools/dev_wave_wait.py acceptance" not in item for item in failures)
    assert all("post-claim merge" not in item for item in failures)


def test_resume_rejects_diverged_head(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    _advance_work(repo)
    assert _git(repo, "rev-list", "--count", "HEAD..refs/heads/main") == "1"
    assert _git(repo, "rev-list", "--count", "refs/heads/main..HEAD") == "1"
    assert _git(repo, "status", "--porcelain") == ""
    assert _run(repo, "--mode", "resume") == 1
    assert "HEAD does not contain local main" in capsys.readouterr().err


def test_resume_rejects_unborn_head(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "unborn"
    _git(tmp_path, "init", "-q", "-b", "work", str(repo))
    empty_tree = _git(repo, "hash-object", "-t", "tree", "-w", "/dev/null")
    main_commit = _git(
        repo,
        "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid",
        "commit-tree", empty_tree, "-m", "main base",
    )
    _git(repo, "update-ref", "refs/heads/main", main_commit)
    exclude = repo / ".git" / "info" / "exclude"
    exclude.write_text("external/\ndocs/\n", encoding="ascii")
    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("# fixture\n", encoding="utf-8")
    (marker.parent / ".git").write_text("gitdir: fixture\n", encoding="utf-8")
    handoff = repo / "docs" / "handoff"
    handoff.mkdir(parents=True)
    (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")
    assert _git(repo, "status", "--porcelain") == ""
    failures = CWS.check_repository(repo, mode="resume")
    assert len(failures) == 1
    assert "HEAD/local main containment: git の読み取りに失敗" in failures[0]
    assert _run(repo, "--mode", "resume") == 1
    assert "HEAD/local main containment: git の読み取りに失敗" in capsys.readouterr().err


def test_resume_does_not_accept_replace_forged_containment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    _advance_work(repo)
    head = _git(repo, "rev-parse", "HEAD")
    main = _git(repo, "rev-parse", "refs/heads/main")
    assert _git(repo, "--no-replace-objects", "rev-list", "--count", "HEAD..main") == "1"
    _git(repo, "replace", "--graft", head, main)
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "0"
    monkeypatch.setenv("GIT_NO_REPLACE_OBJECTS", "0")
    assert _run(repo, "--mode", "resume") == 1
    assert "HEAD does not contain local main" in capsys.readouterr().err


def test_resume_rejects_legacy_graft_forged_containment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    _advance_work(repo)
    head = _git(repo, "rev-parse", "HEAD")
    main = _git(repo, "rev-parse", "refs/heads/main")
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "1"
    grafts = Path(
        _git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts")
    )
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(f"{head} {main}\n", encoding="ascii")
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "0"
    assert _run(repo, "--mode", "resume") == 1
    assert "legacy graft metadata exists" in capsys.readouterr().err


def test_resume_rejects_dangling_grafts_symlink(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    grafts = Path(
        _git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/grafts")
    )
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.symlink_to(tmp_path / "missing-grafts-target")
    assert grafts.is_symlink() and not grafts.exists()
    assert _run(repo, "--mode", "resume") == 1
    assert "legacy graft metadata exists" in capsys.readouterr().err


def test_resume_rejects_symbolic_main_forged_containment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    _git(repo, "symbolic-ref", "refs/heads/main", "refs/heads/work")
    assert _git(repo, "symbolic-ref", "refs/heads/main") == "refs/heads/work"
    assert _git(repo, "rev-list", "--count", "HEAD..refs/heads/main") == "0"
    assert _run(repo, "--mode", "resume") == 1
    assert "local main is a symbolic ref" in capsys.readouterr().err


def test_fresh_rejects_symbolic_main_forged_equality(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    _advance_work(repo)
    _git(repo, "symbolic-ref", "refs/heads/main", "refs/heads/work")
    assert _git(repo, "rev-parse", "HEAD") == _git(
        repo, "rev-parse", "refs/heads/main"
    )
    assert _run(repo, "--mode", "fresh") == 1
    assert "local main is a symbolic ref" in capsys.readouterr().err


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


def test_main_divergence_notice_reports_count_while_resume_gate_rejects_lag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """INFO は件数を示し、独立した resume gate は lag を拒否する。"""
    repo = _repo(tmp_path)
    _advance_main(repo, 3)
    assert _git(repo, "rev-list", "--count", "HEAD..main") == "3"
    assert _run(repo, "--mode", "resume") == 1
    captured = capsys.readouterr()
    out = captured.out
    assert "3 commit" in out
    assert "遅れ" in out
    assert "乖離なし" not in out
    assert "HEAD does not contain local main" in captured.err


def test_main_divergence_notice_is_fail_open_but_resume_gate_is_fail_closed_when_main_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """main ref 不在時も INFO は続行を述べるが resume gate は拒否する。"""
    repo = _repo(tmp_path)
    _git(repo, "branch", "-D", "main")
    assert _run(repo, "--mode", "resume") == 1
    captured = capsys.readouterr()
    out = captured.out
    assert "取得できない" in out
    assert "続行" in out
    assert "HEAD/local main containment: git の読み取りに失敗" in captured.err


def test_resume_gate_does_not_trust_info_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    _advance_main(repo, 1)
    monkeypatch.setattr(CWS, "describe_main_divergence", lambda repo: "local main との乖離なし")
    assert _run(repo, "--mode", "resume") == 1


def test_info_failure_text_does_not_reject_valid_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    _advance_work(repo)
    monkeypatch.setattr(
        CWS,
        "describe_main_divergence",
        lambda repo: "local main との乖離を取得できない: 可視化のみ省略し検査は続行する",
    )
    assert _run(repo, "--mode", "resume") == 0


def test_info_exception_does_not_reject_valid_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path)
    _advance_work(repo)

    def raise_unexpected(repo: Path) -> str:
        raise RuntimeError("unexpected info failure")

    monkeypatch.setattr(CWS, "describe_main_divergence", raise_unexpected)
    assert _run(repo, "--mode", "resume") == 0
    assert "可視化のみ省略し検査は続行する" in capsys.readouterr().out


def test_repo_argument_is_used_for_both_info_and_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inspected = _repo(tmp_path / "inspected")
    decoy = _repo(tmp_path / "decoy")
    _advance_main(inspected, 1)
    monkeypatch.chdir(decoy)
    assert CWS.main(["--repo", str(inspected), "--mode", "resume"]) == 1
    captured = capsys.readouterr()
    assert "1 commit" in captured.out
    assert "HEAD does not contain local main" in captured.err


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
    out = capsys.readouterr().out
    assert "qsub" in out
    assert "wave identity" in out
    assert "branch 所有" in out
    assert "--repo" in out
    assert "同一性は認証しない" in out


def test_help_discloses_midflight_scope_and_non_guarantees(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        CWS.main(["--help"])
    assert raised.value.code == 0
    out = capsys.readouterr().out
    assert "midflight は段 5 実装子 dispatch" in out
    assert "直前専用で、開始 gate" in out
    assert "開始 gate (fresh / resume) の代用ではない" in out
    assert "HEAD/main" in out
    assert "関係・clean tree・handoff を検査せず" in out
    assert "main 乖離量は関門でない" in out


def test_ok_reports_resolved_repo_and_non_guarantees(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path)
    assert CWS.main(["--repo", str(repo / ".." / "repo")]) == 0
    out = capsys.readouterr().out
    assert f"repo={repo.resolve()}" in out
    assert "wave identity" in out
    assert "branch 所有" in out
    assert "--repo の同一性は認証しない" in out


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
