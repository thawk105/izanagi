"""land 後 cleanup CLI の破壊安全性と再入状態を固定する。"""

from __future__ import annotations

import ast
import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_TOOL = _REPO / "tools" / "dev_wave_cleanup.py"
sys.path.insert(0, os.fspath(_REPO / "tools"))
_SPEC = importlib.util.spec_from_file_location("dev_wave_cleanup_under_test", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
cleanup = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = cleanup
_SPEC.loader.exec_module(cleanup)


@dataclass(frozen=True)
class Repo:
    main: Path
    wave: Path
    branch: str
    base: str
    tip: str


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", os.fspath(cwd), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git {args!r} rc={result.returncode}: "
            f"{result.stderr.decode('utf-8', 'replace')}"
        )
    return result


def _sha(cwd: Path, expression: str = "HEAD") -> str:
    return _git(cwd, "rev-parse", expression).stdout.decode().strip()


def _line_porcelain_to_z(raw: bytes) -> bytes:
    """Git 2.34 test host の line porcelain を production parser の -z bytes にする。"""

    stripped = raw.rstrip(b"\n")
    if not stripped:
        return b""
    records = stripped.split(b"\n\n")
    return b"\x00\x00".join(b"\x00".join(record.splitlines()) for record in records) + b"\x00\x00"


@pytest.fixture(autouse=True)
def _git_234_porcelain_adapter(monkeypatch):
    """production の必須 -z 呼出しを保ち、旧 Git の test output だけ NUL 化する。"""

    original = cleanup._git

    def adapted(cwd, *args):
        if args == ("worktree", "list", "--porcelain", "-z"):
            result = _git(Path(cwd), "worktree", "list", "--porcelain")
            return subprocess.CompletedProcess(
                result.args,
                result.returncode,
                _line_porcelain_to_z(result.stdout),
                result.stderr,
            )
        if (
            len(args) == 5
            and args[:2] == ("rev-list", "--walk-reflogs")
            and args[3:] == ("--not", "refs/heads/main")
        ):
            reflog = _git(Path(cwd), "reflog", "show", "--format=%H", args[2])
            unreachable = []
            for sha in dict.fromkeys(reflog.stdout.decode().splitlines()):
                ancestor = _git(
                    Path(cwd), "merge-base", "--is-ancestor", sha, "refs/heads/main",
                    check=False,
                )
                if ancestor.returncode != 0:
                    unreachable.append(sha)
            output = (("\n".join(unreachable) + "\n") if unreachable else "").encode()
            return subprocess.CompletedProcess(reflog.args, 0, output, b"")
        return original(Path(cwd), *args)

    monkeypatch.setattr(cleanup, "_git", adapted)


def _make_repo(
    tmp_path: Path,
    monkeypatch,
    *,
    locked: bool = False,
    landed: bool = True,
) -> Repo:
    main = tmp_path / "main"
    wave = main / ".claude" / "worktrees" / "wave"
    subprocess.run(
        ["git", "init", "-b", "main", os.fspath(main)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    _git(main, "config", "user.name", "Cleanup Test")
    _git(main, "config", "user.email", "cleanup@example.invalid")
    (main / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(main, "add", "tracked.txt")
    _git(main, "commit", "-m", "base")
    base = _sha(main)
    wave.parent.mkdir(parents=True)
    _git(main, "worktree", "add", "-b", "wave", os.fspath(wave))
    (wave / "tracked.txt").write_text("wave\n", encoding="utf-8")
    _git(wave, "commit", "-am", "wave")
    tip = _sha(wave)
    if landed:
        _git(main, "merge", "--ff-only", "wave")
    if locked:
        _git(main, "worktree", "lock", "--reason", "synthetic", os.fspath(wave))
    monkeypatch.setattr(cleanup, "_REPO", main)
    return Repo(main, wave, "wave", base, tip)


def _argv(repo: Repo, **overrides: str) -> list[str]:
    values = {
        "main": os.fspath(repo.main),
        "wave": os.fspath(repo.wave),
        "branch": repo.branch,
        "tip": repo.tip,
    }
    values.update(overrides)
    return [
        "--main-worktree", values["main"],
        "--wave-worktree", values["wave"],
        "--wave-branch", values["branch"],
        "--tested-wave-tip-sha", values["tip"],
    ]


def _run(repo: Repo, capsys, **overrides: str) -> tuple[int, str, str]:
    rc = cleanup.main(_argv(repo, **overrides))
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def _record_bytes(repo: Repo) -> bytes:
    return _git(repo.main, "worktree", "list", "--porcelain").stdout


def _snapshot(repo: Repo) -> tuple[bool, bytes, str | None, str | None, bytes | None]:
    exists = repo.wave.is_dir()
    branch_result = _git(repo.main, "rev-parse", "--verify", f"refs/heads/{repo.branch}", check=False)
    branch = branch_result.stdout.decode().strip() if branch_result.returncode == 0 else None
    head = _sha(repo.wave) if exists else None
    gitfile = (repo.wave / ".git").read_bytes() if exists else None
    return exists, _record_bytes(repo), branch, head, gitfile


def _assert_preserved(repo: Repo, before) -> None:
    assert _snapshot(repo) == before


def _assert_removed(repo: Repo) -> None:
    assert not os.path.lexists(repo.wave)
    assert os.fsencode(repo.wave) not in _record_bytes(repo)
    assert _git(
        repo.main,
        "rev-parse", "--verify", f"refs/heads/{repo.branch}",
        check=False,
    ).returncode != 0


def _prepare_state(repo: Repo, state: str) -> None:
    if state in {"b", "c", "d", "e"}:
        _git(repo.wave, "checkout", "--detach")
    if state in {"c", "d", "e"}:
        shutil.rmtree(repo.wave)
    if state in {"d", "e"}:
        _git(repo.main, "worktree", "prune", "--expire=now")
    if state == "e":
        _git(repo.main, "branch", "-d", "--", repo.branch)


@pytest.mark.parametrize("locked", (False, True), ids=("unlocked", "locked"))
def test_landed_attached_worktree_is_removed(tmp_path, monkeypatch, capsys, locked):
    repo = _make_repo(tmp_path, monkeypatch, locked=locked)
    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout, stderr) == (0, "removed\n", "")
    _assert_removed(repo)


@pytest.mark.parametrize("state", ("a", "b", "c", "d", "e"))
def test_reentry_states_run_only_remaining_cleanup(tmp_path, monkeypatch, capsys, state):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, state)
    calls: list[tuple[str, ...]] = []
    original = cleanup._git

    def spy(cwd, *args):
        calls.append(tuple(args))
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", spy)
    rc, stdout, stderr = _run(repo, capsys)
    expected = "already-clean\n" if state == "e" else "removed\n"
    assert (rc, stdout, stderr) == (0, expected, "")
    _assert_removed(repo)
    assert (("checkout", "--detach") in calls) is (state == "a")
    assert any(call[:2] == ("worktree", "prune") and "--dry-run" in call for call in calls) is (
        state in {"a", "b", "c"}
    )
    assert any(call[:2] == ("branch", "-d") for call in calls) is (state != "e")


def _assert_rejected_preserving(repo: Repo, capsys, *, expected_rc=20, **overrides):
    before = _snapshot(repo)
    rc, stdout, stderr = _run(repo, capsys, **overrides)
    assert rc == expected_rc
    assert stdout == ""
    assert stderr.startswith("dev-wave-cleanup: status=rejected phase=")
    assert stderr.count("\n") == 1
    assert len(stderr.encode("utf-8")) < 600
    _assert_preserved(repo, before)


def test_rejects_non_ancestor_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, landed=False, locked=True)
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize("kind", ("tracked", "untracked"))
def test_rejects_dirty_worktree_without_mutation(tmp_path, monkeypatch, capsys, kind):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    if kind == "tracked":
        (repo.wave / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    else:
        (repo.wave / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize(
    ("rc", "payload", "expected"),
    (
        (1, {"status": "occupied", "occupants": [{"pid": 1}], "issues": [],
             "scanned": 1, "same_uid_cwd_unreachable": [],
             "unreachable": {"cwd_permission": 0}}, 21),
        (2, {"status": "indeterminate", "occupants": [], "issues": [{"error": "x"}],
             "scanned": 1, "same_uid_cwd_unreachable": [],
             "unreachable": {"cwd_permission": 0}}, 22),
        (0, {"status": "unoccupied", "occupants": [], "issues": [],
             "scanned": 1, "same_uid_cwd_unreachable": [],
             "unreachable": {"cwd_permission": 1}}, 22),
        (0, {"status": "unoccupied", "occupants": [], "issues": [],
             "scanned": 1,
             "same_uid_cwd_unreachable": [{"pid": 7, "comm": "worker"}],
             "unreachable": {"cwd_permission": 0}}, 22),
    ),
    ids=("occupied-rc1", "indeterminate-rc2", "cwd-permission", "same-uid-cwd"),
)
def test_rejects_occupancy_payload_failures_without_mutation(
    tmp_path, monkeypatch, capsys, rc, payload, expected,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    payload = {**payload, "worktree": os.fspath(repo.wave)}
    monkeypatch.setattr(cleanup, "_occupancy_payload", lambda path: (rc, payload))
    _assert_rejected_preserving(repo, capsys, expected_rc=expected)


def test_rejects_cwd_inside_target_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    before = _snapshot(repo)
    monkeypatch.chdir(repo.wave)
    monkeypatch.setenv("PWD", os.fspath(repo.wave))
    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout) == (20, "")
    assert "status=rejected" in stderr
    _assert_preserved(repo, before)


def test_rejects_primary_as_wave_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    _assert_rejected_preserving(repo, capsys, wave=os.fspath(repo.main))


def test_rejects_wave_from_different_common_dir(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path / "one", monkeypatch, locked=True)
    other = _make_repo(tmp_path / "two", monkeypatch)
    monkeypatch.setattr(cleanup, "_REPO", other.main)
    before = _snapshot(repo)
    rc = cleanup.main(_argv(repo, main=os.fspath(other.main)))
    captured = capsys.readouterr()
    assert rc == 20 and captured.out == "" and "status=rejected" in captured.err
    _assert_preserved(repo, before)


def test_rejects_branch_tip_mismatch_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    _assert_rejected_preserving(repo, capsys, tip=repo.base)


@pytest.mark.parametrize("spelling", ("symlink", "dotdot", "trailing"))
def test_rejects_unsafe_raw_path_spellings(tmp_path, monkeypatch, capsys, spelling):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    if spelling == "symlink":
        link = tmp_path / "wave-link"
        link.symlink_to(repo.wave, target_is_directory=True)
        raw = os.fspath(link)
    elif spelling == "dotdot":
        raw = os.fspath(repo.wave.parent / "unused" / ".." / repo.wave.name)
    else:
        raw = os.fspath(repo.wave) + "/"
    _assert_rejected_preserving(repo, capsys, expected_rc=2, wave=raw)


def test_rejects_malformed_porcelain_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    original = cleanup._git

    def malformed(cwd, *args):
        if args == ("worktree", "list", "--porcelain", "-z"):
            raw = b"worktree " + os.fsencode(repo.main) + b"\x00HEAD " + repo.tip.encode() + b"\x00mystery x\x00\x00"
            return subprocess.CompletedProcess(args, 0, raw, b"")
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", malformed)
    _assert_rejected_preserving(repo, capsys)


def test_rejects_active_fold_state_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    common = Path(_git(repo.main, "rev-parse", "--git-common-dir").stdout.decode().strip())
    if not common.is_absolute():
        common = repo.main / common
    (common / "izanagi-spool-fold-state.json").write_text("{}\n", encoding="utf-8")
    _assert_rejected_preserving(repo, capsys)


def test_rejects_reflog_only_unreachable_commit_without_mutation(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    _git(repo.main, "worktree", "unlock", os.fspath(repo.wave))
    (repo.wave / "tracked.txt").write_text("unreachable\n", encoding="utf-8")
    _git(repo.wave, "commit", "-am", "unreachable reflog entry")
    _git(repo.wave, "reset", "--hard", repo.tip)
    _git(repo.main, "worktree", "lock", "--reason", "synthetic", os.fspath(repo.wave))
    _assert_rejected_preserving(repo, capsys)


def test_prune_dry_run_stops_when_any_candidate_directory_exists(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _git(repo.wave, "checkout", "--detach")
    other = repo.main / ".claude" / "worktrees" / "other"
    _git(repo.main, "worktree", "add", "-b", "other", os.fspath(other))
    original_must = cleanup._must_git

    def dry_run_with_existing_record(cwd, *args):
        if args == ("worktree", "prune", "--dry-run", "--verbose", "--expire=now"):
            return subprocess.CompletedProcess(
                args,
                0,
                b"Removing worktrees/other: synthetic candidate\n",
                b"",
            )
        return original_must(cwd, *args)

    monkeypatch.setattr(cleanup, "_must_git", dry_run_with_existing_record)
    rc, stdout, stderr = _run(repo, capsys)
    assert rc == 30 and stdout == ""
    assert "status=partial phase=prune-dry-run" in stderr
    assert other.is_dir()
    assert _sha(repo.main, f"refs/heads/{repo.branch}") == repo.tip


def test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist(monkeypatch):
    tree = ast.parse(_TOOL.read_text(encoding="utf-8"))
    forbidden = {("worktree", "remove"), ("submodule", "deinit"), ("branch", "-D")}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None)
        if name not in {"_git", "_must_git"}:
            continue
        constants = tuple(
            arg.value for arg in node.args[1:3]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        )
        assert constants not in forbidden

    calls = []
    monkeypatch.setattr(cleanup.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    for verb in forbidden:
        with pytest.raises(RuntimeError):
            cleanup._git(Path("/tmp"), *verb)
    assert calls == []


def test_git_argv_spy_sees_only_allowlisted_cleanup_commands(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    calls: list[tuple[str, ...]] = []
    original = cleanup._git

    def spy(cwd, *args):
        calls.append(tuple(args))
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", spy)
    assert _run(repo, capsys) == (0, "removed\n", "")
    assert calls
    assert all(
        call[:2] not in {("worktree", "remove"), ("submodule", "deinit"), ("branch", "-D")}
        for call in calls
    )


@pytest.mark.parametrize(
    ("phase", "state"),
    (
        ("unlock", "a-locked"),
        ("detach", "a"),
        ("recheck", "a"),
        ("remove-directory", "a"),
        ("prune-dry-run", "c"),
        ("prune", "c"),
        ("registry", "c"),
        ("branch-recheck", "d"),
        ("branch-delete", "d"),
        ("postcondition", "d"),
    ),
)
def test_each_mutation_phase_failure_is_partial_and_calls_nothing_afterward(
    tmp_path, monkeypatch, capsys, phase, state,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=(state == "a-locked"))
    if state in {"c", "d"}:
        _prepare_state(repo, state)
    failed = False

    def boom():
        nonlocal failed
        failed = True
        raise RuntimeError(f"injected {phase}")

    original_git = cleanup._git

    def no_git_after_failure(cwd, *args):
        assert not failed, f"git called after injected {phase}: {args}"
        return original_git(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", no_git_after_failure)

    if phase in {"unlock", "detach", "prune"}:
        original_must = cleanup._must_git

        def fail_selected(cwd, *args):
            selected = (
                (phase == "unlock" and args[:2] == ("worktree", "unlock"))
                or (phase == "detach" and args[:2] == ("checkout", "--detach"))
                or (phase == "prune" and args == ("worktree", "prune", "--expire=now"))
            )
            if selected:
                boom()
            return original_must(cwd, *args)

        monkeypatch.setattr(cleanup, "_must_git", fail_selected)
    elif phase == "recheck":
        original = cleanup._assert_clean_and_head
        count = 0

        def fail_second(*args):
            nonlocal count
            count += 1
            if count == 2:
                boom()
            return original(*args)

        monkeypatch.setattr(cleanup, "_assert_clean_and_head", fail_second)
    elif phase == "remove-directory":
        monkeypatch.setattr(cleanup, "_remove_verified_tree", lambda *args: boom())
    elif phase == "prune-dry-run":
        monkeypatch.setattr(cleanup, "_dry_run_candidates", lambda *args: boom())
    elif phase == "registry":
        monkeypatch.setattr(cleanup, "_verify_record_state", lambda *args, **kwargs: boom())
    elif phase == "branch-recheck":
        original = cleanup._resolve_commit
        ref_calls = 0

        def fail_second_ref(cwd, expression):
            nonlocal ref_calls
            if expression == f"refs/heads/{repo.branch}^{{commit}}":
                ref_calls += 1
                if ref_calls == 2:
                    boom()
            return original(cwd, expression)

        monkeypatch.setattr(cleanup, "_resolve_commit", fail_second_ref)
    elif phase == "branch-delete":
        monkeypatch.setattr(cleanup, "_delete_branch", lambda *args: boom())
    elif phase == "postcondition":
        monkeypatch.setattr(cleanup, "_verify_record_state", lambda *args, **kwargs: boom())
    else:  # pragma: no cover - parameter list is the registry
        raise AssertionError(phase)

    rc, stdout, stderr = _run(repo, capsys)
    assert failed
    assert rc == 30 and stdout == ""
    assert f"status=partial phase={phase}" in stderr
    assert stderr.count("\n") == 1


def test_argv_requires_each_option_once_and_full_lowercase_sha(capsys):
    cases = (
        [],
        ["--main-worktree", "/tmp/a"] * 4,
        [
            "--main-worktree", "/tmp/a",
            "--wave-worktree", "/tmp/b",
            "--wave-branch", "wave",
            "--tested-wave-tip-sha", "A" * 40,
        ],
    )
    for argv in cases:
        rc = cleanup.main(argv)
        captured = capsys.readouterr()
        assert rc == 2 and captured.out == ""
        assert captured.err.startswith("dev-wave-cleanup: status=rejected phase=argv reason=")
        assert captured.err.count("\n") == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
