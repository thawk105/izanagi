# -*- coding: utf-8 -*-
"""tools/check_worktree_occupancy.py の fail-closed 回帰。"""

from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "tools"))

import check_worktree_occupancy as checker  # noqa: E402


def _stat_text(pid: int, starttime: int = 100) -> str:
    fields_after_comm = ["S", *(["0"] * 18), str(starttime)]
    return f"{pid} (comm with ) spaces) {' '.join(fields_after_comm)}\n"


def _make_pid(
    proc_root: Path,
    pid: int,
    *,
    cwd: Path,
    argv: list[str],
    exe: Path | None = None,
    starttime: int = 100,
    ppid: int = 0,
    uid: int | None = None,
    comm: str = "worker",
) -> Path:
    pid_dir = proc_root / str(pid)
    pid_dir.mkdir(parents=True)
    (pid_dir / "cwd").symlink_to(cwd, target_is_directory=True)
    (pid_dir / "cmdline").write_bytes(
        b"\0".join(os.fsencode(arg) for arg in argv) + (b"\0" if argv else b"")
    )
    (pid_dir / "stat").write_text(
        _stat_text(pid, starttime),
        encoding="utf-8",
    )
    process_uid = os.getuid() + 1 if uid is None else uid
    (pid_dir / "status").write_text(
        f"Name:\t{comm}\nPPid:\t{ppid}\n"
        f"Uid:\t{process_uid}\t{process_uid}\t"
        f"{process_uid}\t{process_uid}\n",
        encoding="utf-8",
    )
    (pid_dir / "comm").write_text(f"{comm}\n", encoding="utf-8")
    if exe is not None:
        (pid_dir / "exe").symlink_to(exe)
    return pid_dir


def _scan(target: Path, proc_root: Path) -> checker.ScanReport:
    return checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )


def _shell_exe(tmp_path: Path, name: str = "bash") -> Path:
    exe = tmp_path / "bin" / name
    exe.parent.mkdir(exist_ok=True)
    exe.write_text("synthetic executable\n", encoding="utf-8")
    return exe


def _deny_cwd_readlink(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pid: int | None = None,
) -> None:
    real_readlink = checker.os.readlink

    def deny(path):
        candidate = Path(path)
        matching_pid = pid is None or candidate.parent.name == str(pid)
        if candidate.name == "cwd" and matching_pid:
            raise PermissionError("synthetic denial")
        return real_readlink(path)

    monkeypatch.setattr(checker.os, "readlink", deny)


@contextmanager
def _live_process(cwd: Path, *argv: str):
    ready_read, ready_write = os.pipe()
    release_read, release_write = os.pipe()
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys; os.write(int(sys.argv[-2]),b'1'); "
            "os.read(int(sys.argv[-1]),1)",
            *argv,
            str(ready_write),
            str(release_read),
        ],
        cwd=cwd,
        pass_fds=(ready_write, release_read),
    )
    os.close(ready_write)
    os.close(release_read)
    try:
        readable, _, _ = select.select([ready_read], [], [], 5.0)
        assert readable, "child readiness handshake timed out"
        assert os.read(ready_read, 1) == b"1"
        yield child
    finally:
        os.close(ready_read)
        try:
            os.write(release_write, b"1")
        except BrokenPipeError:
            pass
        os.close(release_write)
        try:
            child.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5.0)


def _limited_proc_view(proc_root: Path, pid: int) -> None:
    proc_root.mkdir(exist_ok=True)
    (proc_root / str(pid)).symlink_to(
        Path("/proc") / str(pid),
        target_is_directory=True,
    )


def test_target_normalizes_relative_symlink_and_trailing_slash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "real-target"
    target.mkdir()
    (target / "child").mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 101, cwd=tmp_path, argv=["worker", "alias/child"])

    monkeypatch.chdir(tmp_path)
    report = _scan(Path("alias/"), proc_root)

    assert report.status == "occupied"
    assert report.worktree == target.resolve()
    assert report.occupants == (
        checker.Occupant(pid=101, sources=("cmdline",)),
    )


def test_scan_detects_cwd_descendant_occupant(tmp_path: Path):
    target = tmp_path / "worktree"
    descendant = target / "nested"
    descendant.mkdir(parents=True)
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 102, cwd=descendant, argv=[])

    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants == (checker.Occupant(pid=102, sources=("cwd",)),)


def test_scan_detects_cmdline_only_occupant(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 103, cwd=outside, argv=["worker", str(target)])

    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=103, sources=("cmdline",)),
    )


def test_scan_does_not_match_sibling_prefix(tmp_path: Path):
    target = tmp_path / "wt"
    target.mkdir()
    sibling = tmp_path / "wt-2"
    sibling.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 104, cwd=outside, argv=["worker", str(sibling)])

    report = _scan(target, proc_root)

    assert report.status == "unoccupied"
    assert report.occupants == ()


def test_scan_resolves_relative_cmdline_path_against_process_cwd(tmp_path: Path):
    target = tmp_path / "worktree"
    (target / "nested").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        105,
        cwd=outside,
        argv=["worker", "../worktree/nested"],
    )

    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants[0].sources == ("cmdline",)


def test_scan_matches_equals_rhs_path_in_argv(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        106,
        cwd=outside,
        argv=["worker", f"--cwd={target}"],
    )

    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants[0].sources == ("cmdline",)


def test_scan_ignores_self_cmdline(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 107, cwd=outside, argv=["checker", str(target)])

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=107,
        parent_pid=-1,
    )

    assert report.status == "unoccupied"


def test_scan_does_not_ignore_self_cwd(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 108, cwd=target, argv=["checker", str(target)])

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=108,
        parent_pid=-1,
    )

    assert report.status == "occupied"
    assert report.occupants == (checker.Occupant(pid=108, sources=("cwd",)),)


def test_scan_ignores_parent_shell_invocation_cmdline(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        109,
        cwd=outside,
        argv=["bash", str(checker._CHECKER_PATH), str(target)],
        exe=shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=109,
    )

    assert report.status == "unoccupied"


def test_scan_does_not_ignore_parent_cwd(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        110,
        cwd=target,
        argv=["bash", str(checker._CHECKER_PATH), str(target)],
        exe=shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=110,
    )

    assert report.status == "occupied"
    assert report.occupants == (checker.Occupant(pid=110, sources=("cwd",)),)


def test_scan_does_not_exclude_spoofed_argv0_shell_parent(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    non_shell = _shell_exe(tmp_path, "python3")
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        111,
        cwd=outside,
        argv=["bash", str(checker._CHECKER_PATH), str(target)],
        exe=non_shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=111,
    )

    assert report.status == "occupied"
    assert report.occupants[0].sources == ("cmdline",)


def test_scan_does_not_exclude_shell_parent_without_checker_in_cmdline(
    tmp_path: Path,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        112,
        cwd=outside,
        argv=["bash", str(target)],
        exe=shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=112,
    )

    assert report.status == "occupied"
    assert report.occupants[0].sources == ("cmdline",)


def test_invoker_exe_allowlist_is_exact():
    assert checker._SHELL_EXE_NAMES == frozenset(
        {"bash", "sh", "dash", "zsh", "ksh"}
    )
    assert checker._INVOKER_EXE_NAMES == frozenset(
        {
            "bash", "sh", "dash", "zsh", "ksh",
            "timeout", "flock", "time", "strace",
            "nohup", "env", "stdbuf", "xargs", "setsid", "nice", "ionice",
        }
    )


@pytest.mark.parametrize("wrapper", ("timeout", "flock", "time", "strace"))
def test_scan_ignores_checker_invocation_cmdline_for_direct_wrapper(
    tmp_path: Path,
    wrapper: str,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    wrapper_exe = _shell_exe(tmp_path, wrapper)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        131,
        cwd=outside,
        argv=[wrapper, str(checker._CHECKER_PATH), str(target)],
        exe=wrapper_exe,
        ppid=0,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=131,
    )

    assert report.status == "unoccupied"
    assert report.occupants == ()


def test_scan_ignores_checker_invocation_cmdline_in_deep_ancestor(
    tmp_path: Path,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    wrapper_exe = _shell_exe(tmp_path, "timeout")
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        132,
        cwd=outside,
        argv=["timeout", str(checker._CHECKER_PATH), str(target)],
        exe=wrapper_exe,
        ppid=0,
    )
    _make_pid(
        proc_root,
        133,
        cwd=outside,
        argv=["python3", str(checker._CHECKER_PATH)],
        ppid=132,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=133,
    )

    assert report.status == "unoccupied"
    assert report.occupants == ()


def test_scan_does_not_exclude_nonancestor_with_full_invoker_signature(
    tmp_path: Path,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    wrapper_exe = _shell_exe(tmp_path, "timeout")
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        145,
        cwd=outside,
        argv=["timeout", str(checker._CHECKER_PATH), str(target)],
        exe=wrapper_exe,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=-1,
    )

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=145, sources=("cmdline",)),
    )


def test_scan_does_not_exclude_parent_when_ancestor_snapshot_is_unreadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    wrapper_exe = _shell_exe(tmp_path, "timeout")
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        146,
        cwd=outside,
        argv=["timeout", str(checker._CHECKER_PATH), str(target)],
        exe=wrapper_exe,
    )

    def unreadable_parent(_pid_dir: Path) -> int:
        raise PermissionError("synthetic parent snapshot denial")

    monkeypatch.setattr(checker, "_read_parent_pid", unreadable_parent)
    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=146,
    )

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=146, sources=("cmdline",)),
    )


def test_scan_does_not_exclude_target_token_before_checker(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        134,
        cwd=outside,
        argv=["bash", str(target), str(checker._CHECKER_PATH)],
        exe=shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=134,
    )

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=134, sources=("cmdline",)),
    )


def test_scan_does_not_exclude_relative_checker_token(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        143,
        cwd=checker._CHECKER_PATH.parent,
        argv=["bash", checker._CHECKER_PATH.name, str(target)],
        exe=shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=143,
    )

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=143, sources=("cmdline",)),
    )


def test_scan_does_not_exclude_checker_path_hidden_in_option(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        144,
        cwd=outside,
        argv=["bash", f"--script={checker._CHECKER_PATH}", str(target)],
        exe=shell,
    )

    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=144,
    )

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=144, sources=("cmdline",)),
    )


def test_scan_does_not_exclude_reused_ancestor_pid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    shell = _shell_exe(tmp_path)
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        135,
        cwd=outside,
        argv=["bash", str(checker._CHECKER_PATH), str(target)],
        exe=shell,
    )
    real_read_starttime = checker._read_starttime
    reads = 0

    def reused_starttime(pid_dir: Path) -> str:
        nonlocal reads
        if pid_dir.name != "135":
            return real_read_starttime(pid_dir)
        reads += 1
        return "100" if reads <= 2 else "200"

    monkeypatch.setattr(checker, "_read_starttime", reused_starttime)
    report = checker.scan_worktree_occupancy(
        target,
        proc_root=proc_root,
        self_pid=999,
        parent_pid=135,
    )

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=135, sources=("cmdline",)),
    )
    assert report.issues == ()


def test_ancestor_chain_stops_on_cycle(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 136, cwd=outside, argv=[], ppid=137)
    _make_pid(proc_root, 137, cwd=outside, argv=[], ppid=136)

    assert checker._ancestor_starttimes(
        proc_root,
        self_pid=999,
        parent_pid=136,
    ) == {136: "100", 137: "100"}


def test_scan_flags_pid_starttime_change_as_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 113, cwd=outside, argv=["worker", str(target)])
    values = iter(("100", "200"))
    monkeypatch.setattr(checker, "_read_starttime", lambda _pid_dir: next(values))

    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.occupants == ()
    assert report.issues == (
        checker.ScanIssue(error="pid-reused", pid=113, source="stat"),
    )


def test_scan_live_unreadable_pid_is_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 114, cwd=outside, argv=["worker"])

    def fail_cwd(_pid_dir: Path) -> Path:
        raise OSError("synthetic read failure")

    monkeypatch.setattr(checker, "_read_process_cwd", fail_cwd)
    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.issues == (
        checker.ScanIssue(error="os-error", pid=114, source="cwd"),
    )


def test_scan_cwd_permission_only_is_unoccupied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 119, cwd=outside, argv=["worker"])

    _deny_cwd_readlink(monkeypatch)
    report = _scan(target, proc_root)

    assert report.status == "unoccupied"
    assert report.issues == ()


def test_main_reports_cwd_permission_as_unreachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 120, cwd=outside, argv=["worker"])

    _deny_cwd_readlink(monkeypatch)
    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["issues"] == []
    assert payload["scanned"] == 1
    assert payload["unreachable"] == {"cwd_permission": 1}


def test_main_cwd_permission_partitions_same_and_other_uid_without_rc_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        125,
        cwd=outside,
        argv=["same-uid-worker", "raw-cmdline-secret"],
        uid=os.getuid(),
        comm="same-uid-worker",
    )
    _make_pid(
        proc_root,
        126,
        cwd=outside,
        argv=["other-uid-worker"],
        uid=os.getuid() + 1,
        comm="other-uid-worker",
    )

    _deny_cwd_readlink(monkeypatch)
    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert rc == 0
    assert payload["status"] == "unoccupied"
    assert payload["issues"] == []
    assert payload["same_uid_cwd_unreachable"] == [
        {"comm": "same-uid-worker", "pid": 125},
    ]
    assert payload["unreachable"] == {"cwd_permission": 1}
    assert "other-uid-worker" not in output
    assert "raw-cmdline-secret" not in output


def test_main_cwd_permission_uid_failure_is_listed_without_rc_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        127,
        cwd=outside,
        argv=["unknown-uid-worker"],
        comm="unknown-uid-worker",
    )

    def deny_uid(_pid_dir: Path) -> int:
        raise PermissionError("synthetic uid denial")

    _deny_cwd_readlink(monkeypatch)
    monkeypatch.setattr(checker, "_read_process_uid", deny_uid)
    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["status"] == "unoccupied"
    assert payload["issues"] == []
    assert payload["same_uid_cwd_unreachable"] == [
        {"comm": "unknown-uid-worker", "pid": 127},
    ]
    assert payload["unreachable"] == {"cwd_permission": 0}


def test_scan_cmdline_permission_error_is_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 121, cwd=outside, argv=["worker"])

    def deny_cmdline(_pid_dir: Path) -> tuple[str, ...]:
        raise PermissionError("synthetic denial")

    monkeypatch.setattr(checker, "_read_cmdline", deny_cmdline)
    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.issues == (
        checker.ScanIssue(error="permission", pid=121, source="cmdline"),
    )


def test_scan_cwd_non_permission_os_error_is_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 124, cwd=outside, argv=["worker"])

    def missing_cwd(_pid_dir: Path) -> Path:
        raise FileNotFoundError("synthetic missing cwd")

    monkeypatch.setattr(checker, "_read_process_cwd", missing_cwd)
    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.issues == (
        checker.ScanIssue(error="missing", pid=124, source="cwd"),
    )


def test_main_zombie_missing_cwd_is_counted_without_issue_mut5(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    pid_dir = _make_pid(proc_root, 129, cwd=outside, argv=["zombie-worker"])
    (pid_dir / "cwd").unlink()
    process_uid = os.getuid()
    (pid_dir / "status").write_text(
        "Name:\tzombie-worker\nState:\tZ (zombie)\n"
        f"Uid:\t{process_uid}\t{process_uid}\t{process_uid}\t{process_uid}\n",
        encoding="utf-8",
    )

    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["status"] == "unoccupied"
    assert payload["issues"] == []
    assert payload["occupants"] == []
    assert payload["unreachable"] == {"cwd_permission": 0, "zombie": 1}


def test_scan_non_zombie_missing_cwd_remains_indeterminate(
    tmp_path: Path,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    pid_dir = _make_pid(proc_root, 130, cwd=outside, argv=["live-worker"])
    (pid_dir / "cwd").unlink()
    process_uid = os.getuid()
    (pid_dir / "status").write_text(
        "Name:\tlive-worker\nState:\tS (sleeping)\n"
        f"Uid:\t{process_uid}\t{process_uid}\t{process_uid}\t{process_uid}\n",
        encoding="utf-8",
    )

    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.issues == (
        checker.ScanIssue(error="missing", pid=130, source="cwd"),
    )
    assert report.unreachable.zombie == 0


def test_scan_deleted_cwd_outside_target_is_unreachable(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    raw_deleted_cwd = tmp_path / "outside" / "gone (deleted)"
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 138, cwd=raw_deleted_cwd, argv=["worker"])

    report = _scan(target, proc_root)

    assert report.status == "unoccupied"
    assert report.issues == ()
    assert report.occupants == ()
    assert report.unreachable.cwd_deleted == 1


def test_scan_suffixless_unresolved_cwd_remains_indeterminate(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    unresolved_cwd = tmp_path / "outside" / "gone"
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 139, cwd=unresolved_cwd, argv=["worker"])

    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.issues == (
        checker.ScanIssue(error="missing", pid=139, source="cwd"),
    )
    assert report.unreachable.cwd_deleted == 0


def test_scan_requires_deleted_suffix_on_raw_readlink_value(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    raw_cwd = tmp_path / "outside" / "gone (deleted)" / "child" / ".."
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 147, cwd=raw_cwd, argv=[])

    report = _scan(target, proc_root)

    assert report.status == "indeterminate"
    assert report.issues == (
        checker.ScanIssue(error="missing", pid=147, source="cwd"),
    )
    assert report.occupants == ()
    assert report.unreachable.cwd_deleted == 0


@pytest.mark.parametrize("matching_spelling", ("raw", "stripped"))
def test_scan_deleted_suffix_ambiguity_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    matching_spelling: str,
):
    if matching_spelling == "raw":
        target = tmp_path / "worktree (deleted)"
        raw_deleted_cwd = target
    else:
        target = tmp_path / "worktree"
        raw_deleted_cwd = Path(f"{target} (deleted)")
    target.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 140, cwd=raw_deleted_cwd, argv=[])

    def missing_resolve(_raw: Path) -> Path:
        raise FileNotFoundError("deleted")

    monkeypatch.setattr(checker, "_resolve_process_cwd", missing_resolve)

    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=140, sources=("cwd",)),
    )
    assert report.unreachable.cwd_deleted == 0


def test_scan_deleted_cwd_outside_target_still_checks_cmdline(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    raw_deleted_cwd = tmp_path / "outside" / "gone (deleted)"
    proc_root = tmp_path / "proc"
    _make_pid(
        proc_root,
        141,
        cwd=raw_deleted_cwd,
        argv=["worker", str(target)],
    )

    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants == (
        checker.Occupant(pid=141, sources=("cmdline",)),
    )
    assert report.unreachable.cwd_deleted == 1


def test_main_reports_deleted_cwd_as_unreachable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    raw_deleted_cwd = tmp_path / "outside" / "gone (deleted)"
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 142, cwd=raw_deleted_cwd, argv=["worker"])

    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["status"] == "unoccupied"
    assert payload["unreachable"] == {"cwd_permission": 0, "cwd_deleted": 1}


def test_main_occupied_wins_over_unreachable_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 122, cwd=outside, argv=["worker", str(target)])
    _make_pid(proc_root, 123, cwd=outside, argv=["worker"])
    _deny_cwd_readlink(monkeypatch, pid=123)
    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["status"] == "occupied"
    assert payload["issues"] == []
    assert payload["occupants"] == [
        {"pid": 122, "sources": ["cmdline"]},
    ]
    assert payload["unreachable"] == {"cwd_permission": 1}


def test_scan_missing_proc_root_is_indeterminate(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()

    report = _scan(target, tmp_path / "missing-proc")

    assert report.status == "indeterminate"
    assert report.issues[0].source == "proc-root"


def test_scan_disappeared_pid_is_ignored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    pid_dir = _make_pid(proc_root, 115, cwd=outside, argv=["worker"])

    def disappear(_pid_dir: Path) -> str:
        shutil.rmtree(pid_dir)
        raise FileNotFoundError(pid_dir / "stat")

    monkeypatch.setattr(checker, "_read_starttime", disappear)
    report = _scan(target, proc_root)

    assert report.status == "unoccupied"
    assert report.issues == ()


def test_scan_occupied_wins_over_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 116, cwd=outside, argv=["worker", str(target)])
    _make_pid(proc_root, 117, cwd=outside, argv=["worker"])
    original = checker._read_cmdline

    def read_or_deny(pid_dir: Path) -> tuple[str, ...]:
        if pid_dir.name == "117":
            raise PermissionError("synthetic denial")
        return original(pid_dir)

    monkeypatch.setattr(checker, "_read_cmdline", read_or_deny)
    report = _scan(target, proc_root)

    assert report.status == "occupied"
    assert report.occupants[0].pid == 116
    assert report.issues == (
        checker.ScanIssue(error="permission", pid=117, source="cmdline"),
    )


def test_main_unoccupied_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 128, cwd=outside, argv=["worker"])

    rc = checker.main([str(target)], proc_root=proc_root)

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["status"] == "unoccupied"


def test_main_json_fields_and_key_order_are_stable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()

    rc = checker.main([str(target)], proc_root=proc_root)

    output = capsys.readouterr().out
    expected = (
        '{"issues":[],"occupants":[],"scanned":0,"status":"unoccupied",'
        '"unreachable":{"cwd_permission":0},"worktree":'
        f"{json.dumps(str(target.resolve()), ensure_ascii=False)}}}\n"
    )
    assert rc == 0
    assert output == expected


def test_main_occupied_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    target = tmp_path / "worktree"
    target.mkdir()
    proc_root = tmp_path / "proc"
    _make_pid(proc_root, 118, cwd=target, argv=[])

    rc = checker.main(
        [str(target)],
        proc_root=proc_root,
        self_pid=-1,
        parent_pid=-1,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["status"] == "occupied"


def test_main_indeterminate_returns_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    target = tmp_path / "worktree"
    target.mkdir()

    rc = checker.main([str(target)], proc_root=tmp_path / "missing-proc")

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["status"] == "indeterminate"


def test_main_rejects_missing_or_nondirectory_target(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    nondirectory = tmp_path / "file"
    nondirectory.write_text("not a directory\n", encoding="utf-8")
    for target in (tmp_path / "missing", nondirectory):
        rc = checker.main([str(target)], proc_root=tmp_path / "unused-proc")
        payload = json.loads(capsys.readouterr().out)
        assert rc == 2
        assert payload["status"] == "invalid-target"
        assert payload["issues"][0]["source"] == "worktree"


def test_main_reports_invalid_target_to_stderr(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    rc = checker.main(
        [str(tmp_path / "missing")],
        proc_root=tmp_path / "unused-proc",
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert json.loads(captured.out)["status"] == "invalid-target"
    assert captured.err == "check_worktree_occupancy: status=invalid-target\n"


def test_real_proc_deleted_cwd_outside_target_is_non_issue(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    deleted_cwd = tmp_path / "outside"
    deleted_cwd.mkdir()
    proc_root = tmp_path / "proc"

    with _live_process(deleted_cwd) as child:
        deleted_cwd.rmdir()
        _limited_proc_view(proc_root, child.pid)
        assert os.readlink(Path("/proc") / str(child.pid) / "cwd").endswith(
            " (deleted)"
        )

        report = _scan(target, proc_root)

        assert report.status == "unoccupied"
        assert report.issues == ()
        assert report.occupants == ()
        assert report.unreachable.cwd_deleted == 1


def test_real_proc_deleted_cwd_inside_target_is_occupant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "worktree"
    deleted_cwd = target / "nested"
    deleted_cwd.mkdir(parents=True)
    proc_root = tmp_path / "proc"

    with _live_process(deleted_cwd) as child:
        deleted_cwd.rmdir()
        _limited_proc_view(proc_root, child.pid)
        monkeypatch.setattr(checker, "_read_cmdline", lambda _pid_dir: ())

        report = _scan(target, proc_root)

        assert report.status == "occupied"
        assert report.issues == ()
        assert report.occupants == (
            checker.Occupant(pid=child.pid, sources=("cwd",)),
        )
        assert report.unreachable.cwd_deleted == 0


def test_real_proc_deleted_cwd_is_relative_argv_base(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    deleted_cwd = tmp_path / "outside"
    deleted_cwd.mkdir()
    proc_root = tmp_path / "proc"

    with _live_process(deleted_cwd, "../worktree") as child:
        deleted_cwd.rmdir()
        _limited_proc_view(proc_root, child.pid)

        report = _scan(target, proc_root)

        assert report.status == "occupied"
        assert report.issues == ()
        assert report.occupants == (
            checker.Occupant(pid=child.pid, sources=("cmdline",)),
        )
        assert report.unreachable.cwd_deleted == 1


@pytest.mark.parametrize(
    ("uid_mode", "expected_permission", "expected_same_uid"),
    (
        ("same", 0, True),
        ("other", 1, False),
        ("unknown", 0, True),
    ),
)
def test_real_proc_resolve_permission_is_partitioned_by_uid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    uid_mode: str,
    expected_permission: int,
    expected_same_uid: bool,
):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"

    with _live_process(outside) as child:
        _limited_proc_view(proc_root, child.pid)

        def deny_resolve(_raw_cwd: Path) -> Path:
            raise PermissionError("synthetic resolve-stage denial")

        def process_uid(_pid_dir: Path) -> int:
            if uid_mode == "same":
                return os.getuid()
            if uid_mode == "other":
                return os.getuid() + 1
            raise PermissionError("synthetic uid denial")

        monkeypatch.setattr(checker, "_resolve_process_cwd", deny_resolve)
        monkeypatch.setattr(checker, "_read_process_uid", process_uid)

        report = _scan(target, proc_root)

        assert report.status == "unoccupied"
        assert report.issues == ()
        assert report.unreachable.cwd_permission == expected_permission
        assert bool(report.same_uid_cwd_unreachable) is expected_same_uid
        if expected_same_uid:
            assert report.same_uid_cwd_unreachable[0].pid == child.pid


def test_real_proc_cmdline_positive_control(tmp_path: Path):
    target = tmp_path / "worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    ready_read, ready_write = os.pipe()
    release_read, release_write = os.pipe()
    child_code = (
        "import os,sys; "
        "os.write(int(sys.argv[2]), b'1'); "
        "os.read(int(sys.argv[3]), 1)"
    )
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            child_code,
            str(target.resolve()),
            str(ready_write),
            str(release_read),
        ],
        cwd=outside,
        pass_fds=(ready_write, release_read),
    )
    os.close(ready_write)
    os.close(release_read)
    try:
        readable, _, _ = select.select([ready_read], [], [], 5.0)
        assert readable, "child readiness handshake timed out"
        assert os.read(ready_read, 1) == b"1"
        (proc_root / str(child.pid)).symlink_to(
            Path("/proc") / str(child.pid),
            target_is_directory=True,
        )

        report = _scan(target, proc_root)

        assert report.status == "occupied"
        assert report.occupants == (
            checker.Occupant(pid=child.pid, sources=("cmdline",)),
        )
    finally:
        os.close(ready_read)
        try:
            os.write(release_write, b"1")
        except BrokenPipeError:
            pass
        os.close(release_write)
        try:
            child.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            child.terminate()
            try:
                child.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5.0)


def test_real_proc_unoccupied_directory_returns_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    target = tmp_path / "unoccupied-worktree"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    ready_read, ready_write = os.pipe()
    release_read, release_write = os.pipe()
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys; os.write(int(sys.argv[1]),b'1'); "
            "os.read(int(sys.argv[2]),1)",
            str(ready_write),
            str(release_read),
        ],
        cwd=outside,
        pass_fds=(ready_write, release_read),
    )
    os.close(ready_write)
    os.close(release_read)
    try:
        readable, _, _ = select.select([ready_read], [], [], 5.0)
        assert readable, "child readiness handshake timed out"
        assert os.read(ready_read, 1) == b"1"
        (proc_root / str(child.pid)).symlink_to(
            Path("/proc") / str(child.pid), target_is_directory=True
        )

        rc = checker.main(
            [str(target)], proc_root=proc_root, self_pid=-1, parent_pid=-1
        )

        payload = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert payload["status"] == "unoccupied"
        assert payload["issues"] == []
        assert payload["scanned"] == 1
    finally:
        os.close(ready_read)
        try:
            os.write(release_write, b"1")
        except BrokenPipeError:
            pass
        os.close(release_write)
        try:
            child.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5.0)


def test_standalone_cli_real_proc_occupied_positive_control(tmp_path: Path):
    if not Path("/proc").is_dir():
        pytest.skip("/proc is unavailable")
    target = tmp_path / "occupied-worktree"
    target.mkdir()
    ready_read, ready_write = os.pipe()
    release_read, release_write = os.pipe()
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import os,sys; os.write(int(sys.argv[1]),b'1'); "
            "os.read(int(sys.argv[2]),1)",
            str(ready_write),
            str(release_read),
        ],
        cwd=target,
        pass_fds=(ready_write, release_read),
    )
    os.close(ready_write)
    os.close(release_read)
    try:
        readable, _, _ = select.select([ready_read], [], [], 5.0)
        assert readable, "child readiness handshake timed out"
        assert os.read(ready_read, 1) == b"1"
        completed = subprocess.run(
            [sys.executable, str(checker._CHECKER_PATH), str(target)],
            check=False,
            capture_output=True,
            text=True,
            timeout=20.0,
        )

        assert completed.returncode == 1, completed.stdout
        payload = json.loads(completed.stdout)
        assert payload["status"] == "occupied"
        assert child.pid in {occupant["pid"] for occupant in payload["occupants"]}
    finally:
        os.close(ready_read)
        try:
            os.write(release_write, b"1")
        except BrokenPipeError:
            pass
        os.close(release_write)
        try:
            child.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5.0)
