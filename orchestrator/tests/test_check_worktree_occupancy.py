# -*- coding: utf-8 -*-
"""tools/check_worktree_occupancy.py の fail-closed 回帰。"""

from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
import sys
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

    def deny_cwd(_pid_dir: Path) -> Path:
        raise PermissionError("synthetic denial")

    monkeypatch.setattr(checker, "_read_process_cwd", deny_cwd)
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

    def deny_cwd(_pid_dir: Path) -> Path:
        raise PermissionError("synthetic denial")

    monkeypatch.setattr(checker, "_read_process_cwd", deny_cwd)
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
    original = checker._read_process_cwd

    def read_or_deny(pid_dir: Path) -> Path:
        if pid_dir.name == "123":
            raise PermissionError("synthetic denial")
        return original(pid_dir)

    monkeypatch.setattr(checker, "_read_process_cwd", read_or_deny)
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
    proc_root = tmp_path / "proc"
    proc_root.mkdir()

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
        assert payload["status"] == "indeterminate"
        assert payload["issues"][0]["source"] == "worktree"


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


def test_real_proc_unoccupied_directory_returns_zero(tmp_path: Path):
    if not Path("/proc").is_dir():
        pytest.skip("/proc is unavailable")

    target = tmp_path / "unoccupied-worktree"
    target.mkdir()
    completed = subprocess.run(
        [sys.executable, str(checker._CHECKER_PATH), str(target)],
        check=False,
        capture_output=True,
        text=True,
        timeout=20.0,
    )

    assert completed.returncode == 0, completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "unoccupied"
    assert payload["issues"] == []
    assert payload["scanned"] > 0
