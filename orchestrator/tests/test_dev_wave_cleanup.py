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
    argv = [
        "--main-worktree", values["main"],
        "--wave-worktree", values["wave"],
        "--wave-branch", values["branch"],
        "--tested-wave-tip-sha", values["tip"],
    ]
    landing_tip = values.get("landing_tip")
    if landing_tip is not None:
        argv.extend(("--landing-wave-tip-sha", landing_tip))
    return argv


def _run(repo: Repo, capsys, **overrides: str) -> tuple[int, str, str]:
    rc = cleanup.main(_argv(repo, **overrides))
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


def _unoccupied_payload(path: Path) -> dict[str, object]:
    return {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 1,
        "same_uid_cwd_unreachable": [],
        "unreachable": {"cwd_permission": 0},
        "worktree": os.fspath(path),
    }


def _stub_unoccupied(monkeypatch) -> None:
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.UNOCCUPIED_RC, _unoccupied_payload(path)),
    )


def _assert_success_output(
    result: tuple[int, str, str],
    outcome: str,
    *,
    occupancy_phases: tuple[str, ...],
) -> None:
    rc, stdout, stderr = result
    assert (rc, stdout) == (0, f"{outcome}\n")
    lines = stderr.splitlines()
    assert len(lines) == len(occupancy_phases)
    for line, phase in zip(lines, occupancy_phases, strict=True):
        assert line.startswith(
            f"dev-wave-cleanup: diagnostic=occupancy phase={phase} cwd_permission="
        )
        assert " same_uid_cwd_unreachable=" in line


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
    _assert_success_output(
        _run(repo, capsys),
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    _assert_removed(repo)


@pytest.mark.parametrize(
    "pass_optional_tip",
    (False, True),
    ids=("derived", "asserted"),
)
def test_forward_merged_landing_tip_is_used_for_cleanup(
    tmp_path,
    monkeypatch,
    capsys,
    pass_optional_tip,
):
    repo = _make_repo(tmp_path, monkeypatch, landed=False)
    tested_tip = repo.tip
    (repo.main / "main-after.txt").write_text("main advance\n", encoding="utf-8")
    _git(repo.main, "add", "main-after.txt")
    _git(repo.main, "commit", "-m", "main advance")
    incorporated_main = _sha(repo.main)
    _git(repo.wave, "merge", "--no-ff", "--no-edit", incorporated_main)
    landing_tip = _sha(repo.wave)
    assert landing_tip != tested_tip
    _git(repo.main, "merge", "--ff-only", landing_tip)

    overrides = {"landing_tip": landing_tip} if pass_optional_tip else {}
    _assert_success_output(
        _run(repo, capsys, **overrides),
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    _assert_removed(repo)


def test_optional_landing_tip_must_match_derived_wave_head(
    tmp_path,
    monkeypatch,
    capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _assert_rejected_preserving(repo, capsys, landing_tip=repo.base)


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
    expected = "already-clean\n" if state == "e" else "removed\n"
    occupancy_phases = ("preflight", "recheck") if state in {"a", "b"} else ()
    _assert_success_output(
        _run(repo, capsys),
        expected.rstrip("\n"),
        occupancy_phases=occupancy_phases,
    )
    _assert_removed(repo)
    assert (("checkout", "--detach") in calls) is (state == "a")
    assert any(call[:2] == ("worktree", "prune") and "--dry-run" in call for call in calls) is (
        state in {"a", "b", "c"}
    )
    assert any(call[:2] == ("branch", "-d") for call in calls) is (state != "e")


def test_rejects_stale_record_bound_to_a_different_branch(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    admin = Path(
        (repo.wave / ".git").read_text(encoding="utf-8").removeprefix("gitdir: ").strip()
    )
    _git(repo.main, "branch", "other", repo.tip)
    (admin / "HEAD").write_text("ref: refs/heads/other\n", encoding="utf-8")
    shutil.rmtree(repo.wave)
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize("appeared", ("path", "record", "ref"))
def test_already_clean_rechecks_each_absence_before_success(
    tmp_path, monkeypatch, capsys, appeared,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _prepare_state(repo, "e")
    if appeared == "path":
        original_lexists = cleanup.os.path.lexists
        target_calls = 0

        def path_appears(path):
            nonlocal target_calls
            if Path(path) == repo.wave:
                target_calls += 1
                if target_calls == 2:
                    return True
            return original_lexists(path)

        monkeypatch.setattr(cleanup.os.path, "lexists", path_appears)
    elif appeared == "record":
        original_records = cleanup._worktree_records
        record_calls = 0

        def record_appears(main):
            nonlocal record_calls
            records = original_records(main)
            record_calls += 1
            if record_calls == 2:
                records.append(cleanup.WorktreeRecord(
                    os.fsencode(repo.wave), repo.wave, repo.tip, None, True, False, True,
                ))
            return records

        monkeypatch.setattr(cleanup, "_worktree_records", record_appears)
    elif appeared == "ref":
        original_resolve = cleanup._resolve_commit
        ref_calls = 0

        def ref_appears(main, expression):
            nonlocal ref_calls
            if expression == f"refs/heads/{repo.branch}^{{commit}}":
                ref_calls += 1
                if ref_calls == 2:
                    return repo.tip
            return original_resolve(main, expression)

        monkeypatch.setattr(cleanup, "_resolve_commit", ref_appears)
    else:  # pragma: no cover - parameter list is the registry
        raise AssertionError(appeared)

    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout) == (20, "")
    assert "status=rejected phase=preflight" in stderr


def _assert_rejected_preserving(repo: Repo, capsys, *, expected_rc=20, **overrides):
    before = _snapshot(repo)
    rc, stdout, stderr = _run(repo, capsys, **overrides)
    assert rc == expected_rc
    assert stdout == ""
    assert stderr.startswith("dev-wave-cleanup: status=rejected phase=")
    assert stderr.count("\n") == 1
    assert len(stderr.encode("utf-8")) < 600
    _assert_preserved(repo, before)


def test_occupancy_payload_maps_invalid_target_status(tmp_path):
    rc, payload = cleanup._occupancy_payload(tmp_path / "missing-worktree")

    assert rc == cleanup.occupancy.INDETERMINATE_RC
    assert payload["status"] == "invalid-target"
    assert payload["issues"][0]["source"] == "worktree"


def test_assert_unoccupied_accepts_empty_same_uid_cwd_unreachable(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (
            cleanup.occupancy.UNOCCUPIED_RC,
            _unoccupied_payload(path),
        ),
    )

    diagnostics = cleanup._assert_unoccupied(target)

    assert type(diagnostics.same_uid_cwd_unreachable) is list
    assert diagnostics.same_uid_cwd_unreachable == []


def test_assert_unoccupied_accepts_real_empty_proc_scan_payload(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    original_scan = cleanup.occupancy.scan_worktree_occupancy

    def scan_empty_proc(path, **kwargs):
        return original_scan(
            path,
            proc_root=proc_root,
            parent_pid=-1,
            **kwargs,
        )

    monkeypatch.setattr(
        cleanup.occupancy,
        "scan_worktree_occupancy",
        scan_empty_proc,
    )

    diagnostics = cleanup._assert_unoccupied(target)

    assert type(diagnostics.same_uid_cwd_unreachable) is list
    assert diagnostics.same_uid_cwd_unreachable == []


def test_assert_unoccupied_requires_same_uid_cwd_unreachable_field(
    tmp_path,
    monkeypatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    payload = _unoccupied_payload(target)
    del payload["same_uid_cwd_unreachable"]
    monkeypatch.setattr(
        cleanup,
        "_occupancy_payload",
        lambda path: (cleanup.occupancy.UNOCCUPIED_RC, payload),
    )

    with pytest.raises(cleanup.CleanupFailure) as caught:
        cleanup._assert_unoccupied(target)

    assert caught.value.rc == cleanup.RC_OCCUPANCY_INDETERMINATE
    assert caught.value.reason == (
        "occupancy payload lacks required fields; attempts=1 retry_count=0"
    )


def test_rejects_non_ancestor_without_mutation(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch, landed=False, locked=True)
    _assert_rejected_preserving(repo, capsys)


def test_preflight_ancestry_gate_rejects_before_any_removal(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, landed=False, locked=True)
    # Isolate the direct branch-tip gate from the separate reflog ancestry gate.
    monkeypatch.setattr(cleanup, "_assert_reflog_commits_reachable", lambda *args: None)
    before = _snapshot(repo)
    tracked = repo.wave / "tracked.txt"
    tracked_before = tracked.read_bytes()
    gitfile_before = (repo.wave / ".git").read_bytes()
    administrative = Path(
        gitfile_before.decode("utf-8").removeprefix("gitdir: ").strip()
    )
    administrative_head_before = (administrative / "HEAD").read_bytes()
    lock_before = (administrative / "locked").read_bytes()

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (20, "")
    assert stderr.startswith("dev-wave-cleanup: status=rejected phase=preflight ")
    assert "status=partial" not in stderr
    assert repo.wave.is_dir()
    assert tracked.is_file()
    assert tracked.read_bytes() == tracked_before
    assert (repo.wave / ".git").read_bytes() == gitfile_before
    assert administrative.is_dir()
    assert (administrative / "HEAD").read_bytes() == administrative_head_before
    assert (administrative / "locked").read_bytes() == lock_before
    _assert_preserved(repo, before)


@pytest.mark.parametrize("kind", ("tracked", "untracked"))
def test_rejects_dirty_worktree_without_mutation(tmp_path, monkeypatch, capsys, kind):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    if kind == "tracked":
        (repo.wave / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    else:
        (repo.wave / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize(
    ("signal", "expected"),
    (
        ("rc-occupied", 21),
        ("status-occupied", 21),
        ("occupants", 21),
        ("indeterminate-occupants", 21),
        ("rc-indeterminate", 22),
        ("issues", 22),
        ("mixed-issues", 22),
    ),
)
def test_rejects_occupancy_payload_failures_without_mutation(
    tmp_path, monkeypatch, capsys, signal, expected,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    rc = 0
    payload = {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 1,
        "same_uid_cwd_unreachable": [],
        "unreachable": {"cwd_permission": 0},
        "worktree": os.fspath(repo.wave),
    }
    if signal == "rc-occupied":
        rc = 1
    elif signal == "status-occupied":
        payload["status"] = "occupied"
    elif signal == "occupants":
        payload["occupants"] = [{"pid": 1}]
    elif signal == "indeterminate-occupants":
        rc = 2
        payload["status"] = "indeterminate"
        payload["occupants"] = [{"pid": 1}]
        payload["issues"] = [{"error": "missing", "pid": 2, "source": "cwd"}]
    elif signal == "rc-indeterminate":
        rc = 2
    elif signal == "issues":
        payload["issues"] = [{"error": "x"}]
    elif signal == "mixed-issues":
        rc = 2
        payload["status"] = "indeterminate"
        payload["issues"] = [
            {"error": "missing", "pid": 2, "source": "cwd"},
            {"error": "permission", "pid": 3, "source": "cmdline"},
        ]
    else:  # pragma: no cover - parameter list is the registry
        raise AssertionError(signal)
    calls = 0

    def occupancy_result(path):
        nonlocal calls
        calls += 1
        return rc, payload

    monkeypatch.setattr(cleanup, "_occupancy_payload", occupancy_result)
    _assert_rejected_preserving(repo, capsys, expected_rc=expected)
    assert calls == 1


def test_retries_disappeared_pid_issue_then_removes(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    transient = _unoccupied_payload(repo.wave)
    transient.update({
        "status": "indeterminate",
        "issues": [{"error": "missing", "pid": 1234, "source": "cwd"}],
    })
    calls = 0

    def occupancy_sequence(path):
        nonlocal calls
        calls += 1
        if calls == 1:
            return cleanup.occupancy.INDETERMINATE_RC, transient
        return cleanup.occupancy.UNOCCUPIED_RC, _unoccupied_payload(path)

    monkeypatch.setattr(cleanup, "_occupancy_payload", occupancy_sequence)

    result = _run(repo, capsys)

    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert calls == 3
    diagnostic_lines = result[2].splitlines()
    assert "phase=preflight " in diagnostic_lines[0]
    assert "retry_count=1" in diagnostic_lines[0]
    assert "phase=recheck " in diagnostic_lines[1]
    assert "retry_count=0" in diagnostic_lines[1]
    _assert_removed(repo)


def test_three_disappeared_pid_issue_scans_remain_indeterminate(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    transient = _unoccupied_payload(repo.wave)
    transient.update({
        "status": "indeterminate",
        "issues": [{"error": "missing", "pid": 1234, "source": "cmdline"}],
    })
    calls = 0

    def always_transient(path):
        nonlocal calls
        calls += 1
        return cleanup.occupancy.INDETERMINATE_RC, transient

    monkeypatch.setattr(cleanup, "_occupancy_payload", always_transient)
    before = _snapshot(repo)

    rc, stdout, stderr = _run(repo, capsys)

    assert (rc, stdout) == (22, "")
    assert calls == 3
    assert "status=rejected phase=occupancy" in stderr
    assert "attempts=3 retry_count=2" in stderr
    _assert_preserved(repo, before)


@pytest.mark.parametrize(
    "diagnostics",
    (
        {
            "same_uid_cwd_unreachable": [],
            "unreachable": {"cwd_permission": 2030},
        },
        {
            "same_uid_cwd_unreachable": [
                {"pid": 7, "comm": "sshd"},
                {"pid": 8, "comm": "ssh-agent"},
                {"pid": 9, "comm": "(sd-pam)"},
                {"pid": 10, "comm": "systemd"},
            ],
            "unreachable": {"cwd_permission": 2030},
        },
        {
            "same_uid_cwd_unreachable": [],
            "unreachable": {"cwd_permission": 0, "cwd_deleted": 2},
        },
    ),
    ids=("cwd-permission", "same-uid-cwd", "cwd-deleted"),
)
def test_accepts_nonblocking_occupancy_diagnostics(
    tmp_path, monkeypatch, capsys, diagnostics,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    payload = {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 2035,
        "worktree": os.fspath(repo.wave),
        **diagnostics,
    }
    monkeypatch.setattr(cleanup, "_occupancy_payload", lambda path: (0, payload))

    result = _run(repo, capsys)
    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert result[2].count(
        f"cwd_permission={diagnostics['unreachable']['cwd_permission']}"
    ) == 2
    assert result[2].count(
        f"cwd_deleted={diagnostics['unreachable'].get('cwd_deleted', 0)}"
    ) == 2
    _assert_removed(repo)


def test_accepts_arbitrary_same_uid_unreachable_process_with_diagnostics(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    payload = {
        "status": "unoccupied",
        "occupants": [],
        "issues": [],
        "scanned": 1,
        "same_uid_cwd_unreachable": [{"pid": 7, "comm": "nqs_shpd"}],
        "unreachable": {"cwd_permission": 2030},
        "worktree": os.fspath(repo.wave),
    }
    monkeypatch.setattr(cleanup, "_occupancy_payload", lambda path: (0, payload))
    result = _run(repo, capsys)
    _assert_success_output(
        result,
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert result[2].count("nqs_shpd") == 2
    assert result[2].count('"pid": 7') == 2
    _assert_removed(repo)


def test_real_occupancy_scan_rejects_live_process_cwd(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    process = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdin.buffer.read(1)"],
        cwd=repo.wave,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert process.poll() is None
        _assert_rejected_preserving(repo, capsys, expected_rc=21)
    finally:
        assert process.stdin is not None
        process.stdin.write(b"x")
        process.stdin.close()
        assert process.wait(timeout=10) == 0


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
    tree = _sha(repo.main, f"{repo.base}^{{tree}}")
    unrelated_tested_tip = _git(
        repo.main,
        "commit-tree",
        tree,
        "-p",
        repo.base,
        "-m",
        "unrelated tested tip",
    ).stdout.decode().strip()
    _assert_rejected_preserving(repo, capsys, tip=unrelated_tested_tip)


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
        if args == ("worktree", "list", "--porcelain"):
            raw = (
                b"worktree " + os.fsencode(repo.main) + b"\n"
                b"HEAD " + repo.tip.encode() + b"\n"
                b"mystery x\n\n"
            )
            return subprocess.CompletedProcess(args, 0, raw, b"")
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", malformed)
    _assert_rejected_preserving(repo, capsys)


def test_rejects_porcelain_record_with_newline_in_target_path_without_mutation(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    original = cleanup._git

    def newline_path(cwd, *args):
        result = original(cwd, *args)
        if args == ("worktree", "list", "--porcelain"):
            result = subprocess.CompletedProcess(
                result.args,
                result.returncode,
                result.stdout.replace(
                    b"worktree " + os.fsencode(repo.wave) + b"\n",
                    b"worktree " + os.fsencode(repo.wave) + b"\ncontinued\n",
                ),
                result.stderr,
            )
        return result

    monkeypatch.setattr(cleanup, "_git", newline_path)
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
    admin = Path(
        (repo.wave / ".git").read_text(encoding="utf-8").removeprefix("gitdir: ").strip()
    )
    _git(repo.wave, "checkout", "--detach")
    (repo.wave / "tracked.txt").write_text("unreachable\n", encoding="utf-8")
    _git(repo.wave, "commit", "-am", "unreachable reflog entry")
    unreachable = _sha(repo.wave)
    _git(repo.wave, "reset", "--hard", repo.tip)
    branch_reflog = _git(
        repo.main, "rev-list", "--walk-reflogs", f"refs/heads/{repo.branch}",
    ).stdout.decode().splitlines()
    assert unreachable not in branch_reflog
    assert unreachable.encode() in (admin / "logs" / "HEAD").read_bytes()
    _git(repo.main, "worktree", "lock", "--reason", "synthetic", os.fspath(repo.wave))
    _assert_rejected_preserving(repo, capsys)


@pytest.mark.parametrize("mode", ("empty", "fatal"))
def test_rejects_uninspectable_branch_reflog_without_mutation(
    tmp_path, monkeypatch, capsys, mode,
):
    repo = _make_repo(tmp_path, monkeypatch, locked=True)
    original = cleanup._git

    def uninspectable(cwd, *args):
        if args == ("rev-list", "--walk-reflogs", f"refs/heads/{repo.branch}"):
            return subprocess.CompletedProcess(
                args,
                0 if mode == "empty" else 128,
                b"",
                b"" if mode == "empty" else b"fatal: synthetic missing reflog\n",
            )
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", uninspectable)
    _assert_rejected_preserving(repo, capsys)


def test_prune_dry_run_stops_when_any_candidate_directory_exists(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
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


@pytest.mark.parametrize(
    "argv",
    (
        ("worktree", "remove", "--force"),
        ("worktree", "remove"),
        ("worktree", "remove", "--force", "--", "x"),
        ("submodule", "deinit", "-f", "--", "external/ccbench"),
        ("submodule", "deinit"),
        ("branch", "-D", "--", "x"),
        ("branch", "-D", "x"),
    ),
)
def test_git_argv_validator_directly_rejects_forbidden_commands(argv):
    with pytest.raises(RuntimeError, match="git argv is not allowlisted"):
        cleanup._validate_git_argv(argv)


@pytest.mark.parametrize(
    "argv",
    (
        ("branch", "-d", "-f", "--", "wave"),
        ("branch", "-f", "-d", "--", "wave"),
        ("branch", "-d", "--force", "--", "wave"),
        ("branch", "--force", "-d", "--", "wave"),
        ("branch", "-d", "--", "wave", "-f"),
    ),
)
def test_git_argv_schema_rejects_force_delete_permutations(monkeypatch, argv):
    calls = []
    monkeypatch.setattr(
        cleanup.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    with pytest.raises(RuntimeError):
        cleanup._git(Path("/tmp"), *argv)
    assert calls == []


@pytest.mark.parametrize(
    "allowed",
    (
        ("cat-file", "-e", "a" * 40 + "^{commit}"),
        ("check-ref-format", "--branch", "wave"),
        ("merge-base", "--is-ancestor", "a" * 40, "refs/heads/main"),
        ("merge-base", "--is-ancestor", "a" * 40, "b" * 40),
        ("rev-list", "--walk-reflogs", "refs/heads/wave"),
        ("rev-parse", "--git-common-dir"),
        ("rev-parse", "--git-dir"),
        ("rev-parse", "--git-path", "izanagi-spool-fold-state.json"),
        ("rev-parse", "--verify", "refs/heads/wave^{commit}"),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"),
        ("symbolic-ref", "--quiet", "HEAD"),
        ("worktree", "list", "--porcelain"),
        ("worktree", "unlock", "/tmp/wave"),
        ("worktree", "prune", "--dry-run", "--verbose", "--expire=now"),
        ("worktree", "prune", "--expire=now"),
        ("checkout", "--detach"),
        ("branch", "-d", "--", "wave"),
    ),
)
def test_git_argv_schema_rejects_trailing_arguments_for_every_allowed_form(
    monkeypatch, allowed,
):
    calls = []
    monkeypatch.setattr(
        cleanup.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    with pytest.raises(RuntimeError):
        cleanup._git(Path("/tmp"), *allowed, "--force")
    assert calls == []


def test_git_argv_spy_sees_only_allowlisted_cleanup_commands(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)
    calls: list[tuple[str, ...]] = []
    original = cleanup._git

    def spy(cwd, *args):
        calls.append(tuple(args))
        return original(cwd, *args)

    monkeypatch.setattr(cleanup, "_git", spy)
    _assert_success_output(
        _run(repo, capsys),
        "removed",
        occupancy_phases=("preflight", "recheck"),
    )
    assert calls
    assert ("worktree", "list", "--porcelain") in calls
    assert all("-z" not in call for call in calls if call[:2] == ("worktree", "list"))
    assert any(call[:2] == ("rev-list", "--walk-reflogs") for call in calls)
    assert all("--not" not in call for call in calls if call[:2] == ("rev-list", "--walk-reflogs"))
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
    _stub_unoccupied(monkeypatch)
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
    assert failed, (
        f"injection did not fire: phase={phase} state={state} "
        f"rc={rc} stdout={stdout!r} stderr={stderr!r}"
    )
    assert rc == 30 and stdout == ""
    assert f"status=partial phase={phase}" in stderr
    assert stderr.count("\n") == 1


def test_keyboard_interrupt_after_mutation_start_reports_partial(
    tmp_path, monkeypatch, capsys,
):
    repo = _make_repo(tmp_path, monkeypatch)
    _stub_unoccupied(monkeypatch)

    def interrupt(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(cleanup, "_remove_verified_tree", interrupt)
    rc, stdout, stderr = _run(repo, capsys)
    assert (rc, stdout) == (30, "")
    assert "status=partial phase=remove-directory" in stderr
    assert stderr.count("\n") == 1
    assert repo.wave.is_dir()
    assert _sha(repo.main, f"refs/heads/{repo.branch}") == repo.tip


def test_keyboard_interrupt_during_preflight_is_not_partial(tmp_path, monkeypatch, capsys):
    main = tmp_path / "main"
    main.mkdir()
    wave = tmp_path / "wave"
    monkeypatch.setattr(
        cleanup,
        "_preflight",
        lambda args: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    with pytest.raises(KeyboardInterrupt):
        cleanup.main([
            "--main-worktree", os.fspath(main),
            "--wave-worktree", os.fspath(wave),
            "--wave-branch", "wave",
            "--tested-wave-tip-sha", "a" * 40,
        ])
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")


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
        [
            "--main-worktree", "/tmp/a",
            "--wave-worktree", "/tmp/b",
            "--wave-branch", "wave",
            "--tested-wave-tip-sha", "a" * 40,
            "--landing-wave-tip-sha", "B" * 40,
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
