# -*- coding: utf-8 -*-
"""login headroom 観測と user-wide 予約台帳の fail-closed 契約。"""
from __future__ import annotations

import ast
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest


_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from orchestrator.campaign import login_headroom as LH  # noqa: E402


_UID = 4242


def _write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        path.write_text(value, encoding="utf-8")


def _memory_stat(**updates: int) -> str:
    fields = {
        "anon": 101,
        "file": 202,
        "shmem": 303,
        "file_dirty": 404,
        "file_writeback": 505,
        "inactive_anon": 606,
    }
    fields.update(updates)
    return "".join(f"{name} {value}\n" for name, value in fields.items())


def _fake_cgroup(
    tmp_path: Path,
    monkeypatch,
    *,
    root_current: int = 10,
    root_max: int | str = "max",
    user_current: int = 20,
    user_max: int | str = "max",
    slice_current: int = 500,
    slice_max: int | str | None = None,
    memory_stat: str | bytes | None = None,
) -> dict[str, Path]:
    root = tmp_path / "cgroup"
    user = root / "user.slice"
    own = user / f"user-{_UID}.slice"
    proc = tmp_path / "proc-self-cgroup"
    own.mkdir(parents=True)

    if slice_max is None:
        slice_max = LH.CEILING_BYTES + 1000
    if memory_stat is None:
        memory_stat = _memory_stat()
    for directory, current, limit in (
        (root, root_current, root_max),
        (user, user_current, user_max),
        (own, slice_current, slice_max),
    ):
        _write(directory / "memory.current", f"{current}\n")
        _write(directory / "memory.max", f"{limit}\n")
    _write(own / "memory.stat", memory_stat)
    _write(proc, f"0::/user.slice/user-{_UID}.slice/session-9.scope\n")

    monkeypatch.setattr(LH, "_CGROUP_ROOT", str(root))
    monkeypatch.setattr(LH, "_PROC_SELF_CGROUP", str(proc))
    monkeypatch.setattr(LH.os, "getuid", lambda: _UID)
    monkeypatch.setattr(LH, "_filesystem_magic", lambda _fd: LH._CGROUP2_SUPER_MAGIC)
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    return {"root": root, "user": user, "own": own, "proc": proc}


def _observation(*, ceiling: int, current: int, anon: int = 1) -> LH.LoginHeadroom:
    return LH.LoginHeadroom(
        cgroup_path=Path("/fixture/user.slice/user-4242.slice"),
        memory_max_bytes=ceiling,
        effective_ceiling_bytes=ceiling,
        memory_current_bytes=current,
        headroom_bytes=max(0, ceiling - current),
        anon_bytes=anon,
        file_bytes=2,
        shmem_bytes=3,
        file_dirty_bytes=4,
        file_writeback_bytes=5,
    )


def _reservation_files(tmp_path: Path) -> list[Path]:
    directory = tmp_path / "runtime" / LH.ADMISSION_DIRNAME
    return sorted(directory.glob("*.json")) if directory.exists() else []


def test_reads_exact_user_slice_and_returns_every_observation_field(
    tmp_path,
    monkeypatch,
):
    paths = _fake_cgroup(tmp_path, monkeypatch)

    observed = LH.login_headroom()

    assert observed == LH.LoginHeadroom(
        cgroup_path=paths["own"],
        memory_max_bytes=LH.CEILING_BYTES + 1000,
        effective_ceiling_bytes=LH.CEILING_BYTES,
        memory_current_bytes=500,
        headroom_bytes=LH.CEILING_BYTES - 500,
        anon_bytes=101,
        file_bytes=202,
        shmem_bytes=303,
        file_dirty_bytes=404,
        file_writeback_bytes=505,
    )
    assert observed.ceiling_bytes == observed.effective_ceiling_bytes
    assert observed.current_bytes == observed.memory_current_bytes
    assert observed.occupied_bytes == observed.memory_current_bytes


def test_missing_ancestor_memory_interfaces_are_treated_as_unlimited(
    tmp_path,
    monkeypatch,
):
    paths = _fake_cgroup(
        tmp_path,
        monkeypatch,
        slice_current=500,
        slice_max=2000,
    )
    for ancestor in (paths["root"], paths["user"]):
        (ancestor / "memory.current").unlink()
        (ancestor / "memory.max").unlink()

    observed = LH.login_headroom()

    assert observed is not None
    assert observed.memory_max_bytes == 2000
    assert observed.effective_ceiling_bytes == 2000
    assert observed.headroom_bytes == 1500


def test_uses_raw_memory_current_not_anon_for_occupancy_and_admission(
    tmp_path,
    monkeypatch,
):
    _fake_cgroup(
        tmp_path,
        monkeypatch,
        slice_current=900,
        slice_max=2000,
        memory_stat=_memory_stat(anon=100),
    )
    observed = LH.login_headroom()
    assert observed is not None
    assert observed.memory_current_bytes == 900
    assert observed.occupied_bytes == 900
    assert observed.anon_bytes == 100
    assert observed.headroom_bytes == 1100

    admission_observation = _observation(
        ceiling=LH.RESERVE_BYTES + 1000,
        current=900,
        anon=100,
    )
    monkeypatch.setattr(LH, "login_headroom", lambda: admission_observation)
    assert LH.admit(101)[0] is LH.Admission.DISPATCH


@pytest.mark.parametrize(
    ("ancestor_limits", "expected_ceiling"),
    [
        (
            {"root_current": 100, "root_max": "max", "user_current": 4000, "user_max": 4200},
            700,
        ),
        (
            {"root_current": 900, "root_max": 1000, "user_current": 100, "user_max": "max"},
            600,
        ),
    ],
    ids=["user-slice-parent", "cgroup-root"],
)
def test_effective_ceiling_is_limited_by_each_ancestor_available_bytes(
    tmp_path,
    monkeypatch,
    ancestor_limits,
    expected_ceiling,
):
    _fake_cgroup(
        tmp_path,
        monkeypatch,
        slice_current=500,
        slice_max=LH.CEILING_BYTES + 1000,
        **ancestor_limits,
    )

    observed = LH.login_headroom()

    assert observed is not None
    assert observed.effective_ceiling_bytes == expected_ceiling
    assert observed.headroom_bytes == expected_ceiling - 500


def test_cgroup_walk_uses_directory_fds_with_directory_and_nofollow_flags(
    tmp_path,
    monkeypatch,
):
    _fake_cgroup(tmp_path, monkeypatch)
    real_open = LH.os.open
    calls = []

    def recording_open(path, flags, mode=0o777, *, dir_fd=None):
        calls.append((os.fspath(path), flags, dir_fd))
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(LH.os, "open", recording_open)
    assert LH.login_headroom() is not None

    directory_calls = {
        path: (flags, dir_fd)
        for path, flags, dir_fd in calls
        if path in {str(tmp_path / "cgroup"), "user.slice", f"user-{_UID}.slice"}
    }
    assert set(directory_calls) == {
        str(tmp_path / "cgroup"),
        "user.slice",
        f"user-{_UID}.slice",
    }
    assert directory_calls[str(tmp_path / "cgroup")][1] is None
    for path in ("user.slice", f"user-{_UID}.slice"):
        assert directory_calls[path][1] is not None
    for flags, _dir_fd in directory_calls.values():
        assert flags & os.O_DIRECTORY
        assert flags & os.O_NOFOLLOW


def _missing_current(paths, _monkeypatch):
    (paths["own"] / "memory.current").unlink()


def _missing_max(paths, _monkeypatch):
    (paths["own"] / "memory.max").unlink()


def _missing_stat(paths, _monkeypatch):
    (paths["own"] / "memory.stat").unlink()


def _permission_error(_paths, monkeypatch):
    monkeypatch.setattr(
        LH,
        "_read_at",
        lambda *_args: (_ for _ in ()).throw(PermissionError("denied")),
    )


def _io_error(paths, _monkeypatch):
    target = paths["own"] / "memory.current"
    target.unlink()
    target.mkdir()


def _decode_error(paths, _monkeypatch):
    _write(paths["own"] / "memory.current", b"\xff\n")


def _empty_value(paths, _monkeypatch):
    _write(paths["own"] / "memory.current", "")


def _multiple_tokens(paths, _monkeypatch):
    _write(paths["own"] / "memory.current", "1 2\n")


def _non_decimal(paths, _monkeypatch):
    _write(paths["own"] / "memory.current", "0x20\n")


def _negative(paths, _monkeypatch):
    _write(paths["own"] / "memory.current", "-1\n")


def _uint64_overflow(paths, _monkeypatch):
    _write(paths["own"] / "memory.current", f"{1 << 64}\n")


def _max_empty(paths, _monkeypatch):
    _write(paths["own"] / "memory.max", "")


def _max_multiple_tokens(paths, _monkeypatch):
    _write(paths["own"] / "memory.max", "100 200\n")


def _max_non_decimal(paths, _monkeypatch):
    _write(paths["own"] / "memory.max", "1e9\n")


def _max_negative(paths, _monkeypatch):
    _write(paths["own"] / "memory.max", "-1\n")


def _max_uint64_overflow(paths, _monkeypatch):
    _write(paths["own"] / "memory.max", f"{1 << 64}\n")


def _stat_missing(paths, _monkeypatch):
    _write(paths["own"] / "memory.stat", "anon 1\nfile 2\nshmem 3\nfile_dirty 4\n")


def _stat_duplicate(paths, _monkeypatch):
    _write(paths["own"] / "memory.stat", _memory_stat() + "anon 999\n")


def _stat_multiple_tokens(paths, _monkeypatch):
    _write(paths["own"] / "memory.stat", _memory_stat() + "extra 1 2\n")


def _stat_non_decimal(paths, _monkeypatch):
    invalid = _memory_stat(file_dirty=4).replace("file_dirty 4", "file_dirty nope")
    _write(paths["own"] / "memory.stat", invalid)


def _slice_max(paths, _monkeypatch):
    _write(paths["own"] / "memory.max", "max\n")


def _uid_mismatch(paths, _monkeypatch):
    _write(paths["proc"], "0::/user.slice/user-4243.slice/session.scope\n")


def _proc_inconsistent(paths, _monkeypatch):
    _write(paths["proc"], "0::/system.slice/example.service\n")


def _proc_empty(paths, _monkeypatch):
    _write(paths["proc"], "")


def _proc_multiple_unified(paths, _monkeypatch):
    entry = f"0::/user.slice/user-{_UID}.slice/session.scope\n"
    _write(paths["proc"], entry + entry)


def _proc_decode_error(paths, _monkeypatch):
    _write(paths["proc"], b"\xff\n")


def _magic_mismatch(_paths, monkeypatch):
    monkeypatch.setattr(LH, "_filesystem_magic", lambda _fd: 0)


def _magic_io_error(_paths, monkeypatch):
    monkeypatch.setattr(
        LH,
        "_filesystem_magic",
        lambda _fd: (_ for _ in ()).throw(OSError("fstatfs failed")),
    )


@pytest.mark.parametrize(
    "mutation",
    [
        _missing_current,
        _missing_max,
        _missing_stat,
        _permission_error,
        _io_error,
        _decode_error,
        _empty_value,
        _multiple_tokens,
        _non_decimal,
        _negative,
        _uint64_overflow,
        _max_empty,
        _max_multiple_tokens,
        _max_non_decimal,
        _max_negative,
        _max_uint64_overflow,
        _stat_missing,
        _stat_duplicate,
        _stat_multiple_tokens,
        _stat_non_decimal,
        _slice_max,
        _uid_mismatch,
        _proc_inconsistent,
        _proc_empty,
        _proc_multiple_unified,
        _proc_decode_error,
        _magic_mismatch,
        _magic_io_error,
    ],
    ids=lambda mutation: mutation.__name__.removeprefix("_"),
)
def test_every_observation_failure_is_none_and_dispatch(
    tmp_path,
    monkeypatch,
    mutation,
):
    paths = _fake_cgroup(tmp_path, monkeypatch)
    mutation(paths, monkeypatch)

    assert LH.login_headroom() is None
    admission, reason = LH.admit(1)
    assert admission is LH.Admission.DISPATCH
    assert isinstance(reason, str) and reason
    assert LH.grant_budget(max_bytes=1, min_bytes=1)[0] is LH.Admission.DISPATCH


@pytest.mark.parametrize("estimate", [0, -1, True, "1"])
def test_nonpositive_or_noninteger_estimate_dispatches_without_observation(
    tmp_path,
    monkeypatch,
    estimate,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: (_ for _ in ()).throw(AssertionError("must not observe")),
    )
    assert LH.admit(estimate)[0] is LH.Admission.DISPATCH
    with LH.reserve(estimate) as decision:
        assert decision[0] is LH.Admission.DISPATCH


def test_admission_accepts_exact_ceiling_boundary(tmp_path, monkeypatch):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + 100,
            current=50,
        ),
    )

    admission, reason = LH.admit(50)

    assert admission is LH.Admission.LOCAL
    assert isinstance(reason, str) and reason


def test_grant_budget_is_capped_at_maximum_and_records_diagnostics(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    current = 12345
    ceiling = current + LH.RESERVE_BYTES + LH.MAX_LOCAL_BUDGET_BYTES + 999
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=ceiling, current=current),
    )

    admission, budget, reason = LH.grant_budget()

    assert admission is LH.Admission.LOCAL
    assert budget == LH.MAX_LOCAL_BUDGET_BYTES
    assert f"{budget} bytes" in reason
    assert f"現在使用量={current} bytes" in reason
    assert f"実効天井={ceiling} bytes" in reason
    records = _reservation_files(tmp_path)
    assert len(records) == 1
    assert json.loads(records[0].read_text(encoding="utf-8"))["estimate_bytes"] == budget


def test_grant_budget_dispatches_below_minimum(tmp_path, monkeypatch):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    available = LH.MIN_LOCAL_BUDGET_BYTES - 1
    ceiling = LH.RESERVE_BYTES + available
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=ceiling, current=0),
    )

    admission, budget, reason = LH.grant_budget()

    assert admission is LH.Admission.DISPATCH
    assert budget is None
    assert f"算出予算={available} bytes" in reason
    assert _reservation_files(tmp_path) == []


def test_grant_budget_subtracts_live_reservations(tmp_path, monkeypatch):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    available = 1000
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + available,
            current=0,
        ),
    )

    with LH.reserve(250) as first:
        assert first[0] is LH.Admission.LOCAL
        admission, budget, reason = LH.grant_budget(
            max_bytes=available,
            min_bytes=1,
        )

    assert admission is LH.Admission.LOCAL
    assert budget == 750
    assert "生存中の予約=250 bytes" in reason


def test_grant_budget_decides_and_reserves_under_one_lock(monkeypatch):
    events = []

    class LockedLedger:
        def __enter__(self):
            events.append("lock-enter")
            return 99

        def __exit__(self, exc_type, exc, traceback):
            events.append("lock-exit")
            return False

    monkeypatch.setattr(LH, "_locked_ledger", LockedLedger)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + 100,
            current=0,
        ),
    )

    def collect(directory_fd):
        assert directory_fd == 99
        events.append("decide")
        return 0

    def create(directory_fd, budget):
        assert directory_fd == 99
        assert budget == 100
        events.append("reserve")
        return "reservation.json"

    monkeypatch.setattr(LH, "_collect_live_reservations", collect)
    monkeypatch.setattr(LH, "_create_reservation", create)

    assert LH.grant_budget(max_bytes=100, min_bytes=1)[:2] == (
        LH.Admission.LOCAL,
        100,
    )
    assert events == ["lock-enter", "decide", "reserve", "lock-exit"]


def test_admission_directory_uses_uid_default_and_environment_override(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv(LH.ADMISSION_BASE_DIR_ENV, raising=False)
    monkeypatch.setattr(LH.os, "getuid", lambda: _UID)
    assert LH._admission_directory() == (
        Path("/run/user") / str(_UID) / LH.ADMISSION_DIRNAME
    )

    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path))
    assert LH._admission_directory() == tmp_path / LH.ADMISSION_DIRNAME


def test_second_concurrent_reservation_dispatches_when_live_sum_exceeds_ceiling(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    with LH.reserve(40) as first:
        assert first[0] is LH.Admission.LOCAL
        assert len(_reservation_files(tmp_path)) == 1
        with LH.reserve(61) as second:
            assert second[0] is LH.Admission.DISPATCH
            assert len(_reservation_files(tmp_path)) == 1
    assert _reservation_files(tmp_path) == []


def test_dead_pid_reservation_is_recovered_before_admission(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 10, current=0),
    )
    directory = tmp_path / "runtime" / LH.ADMISSION_DIRNAME
    directory.mkdir(parents=True)
    stale = directory / "stale.json"
    stale.write_text(
        json.dumps({"pid": 99999999, "estimate_bytes": 1000, "acquired_at": 1.0}),
        encoding="utf-8",
    )
    monkeypatch.setattr(LH, "_pid_is_alive", lambda pid: False)

    admission, _ = LH.admit(1)

    assert admission is LH.Admission.LOCAL
    assert not stale.exists()


def test_reservation_context_releases_record_when_body_raises(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    with pytest.raises(RuntimeError, match="body failed"):
        with LH.reserve(1) as decision:
            assert decision[0] is LH.Admission.LOCAL
            records = _reservation_files(tmp_path)
            assert len(records) == 1
            record = json.loads(records[0].read_text(encoding="utf-8"))
            assert set(record) == {
                "pid",
                "estimate_bytes",
                "acquired_at",
            }
            assert record["pid"] == os.getpid()
            assert record["estimate_bytes"] == 1
            assert isinstance(record["acquired_at"], float)
            raise RuntimeError("body failed")
    assert _reservation_files(tmp_path) == []


def test_reservation_context_releases_record_on_keyboard_interrupt(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    with pytest.raises(KeyboardInterrupt):
        with LH.reserve(1) as decision:
            assert decision[0] is LH.Admission.LOCAL
            raise KeyboardInterrupt
    assert _reservation_files(tmp_path) == []


def test_corrupt_reservation_and_ledger_acquisition_failure_dispatch(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(tmp_path / "runtime"))
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    directory = tmp_path / "runtime" / LH.ADMISSION_DIRNAME
    directory.mkdir(parents=True)
    (directory / "broken.json").write_text("not-json", encoding="utf-8")
    assert LH.admit(1)[0] is LH.Admission.DISPATCH
    assert LH.grant_budget(max_bytes=1, min_bytes=1)[0] is LH.Admission.DISPATCH
    with LH.reserve(1) as decision:
        assert decision[0] is LH.Admission.DISPATCH

    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("x", encoding="utf-8")
    monkeypatch.setenv(LH.ADMISSION_BASE_DIR_ENV, str(blocking_file))
    assert LH.admit(1)[0] is LH.Admission.DISPATCH
    assert LH.grant_budget(max_bytes=1, min_bytes=1)[0] is LH.Admission.DISPATCH
    with LH.reserve(1) as decision:
        assert decision[0] is LH.Admission.DISPATCH


def test_ceiling_numeric_literal_occurs_only_in_login_headroom_module():
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=_REPO,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    needle = "".join(("14", "*", "1024", "**", "3"))
    hits = []
    for relative in completed.stdout.splitlines():
        path = _REPO / relative
        if not path.is_file():
            continue
        try:
            compact = "".join(path.read_text(encoding="utf-8").split())
        except (OSError, UnicodeDecodeError):
            continue
        if needle in compact:
            hits.append(relative)
    assert hits == ["orchestrator/campaign/login_headroom.py"]


def test_local_budget_constants_are_defined_only_in_login_headroom_leaf():
    names = {"MAX_LOCAL_BUDGET_BYTES", "MIN_LOCAL_BUDGET_BYTES"}
    definitions = {name: [] for name in names}
    roots = (_REPO / "orchestrator", _REPO / "tools")
    for root in roots:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                targets = []
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        node.targets if isinstance(node, ast.Assign) else [node.target]
                    )
                for target in targets:
                    if isinstance(target, ast.Name) and target.id in names:
                        definitions[target.id].append(path.relative_to(_REPO).as_posix())
    assert definitions == {
        name: ["orchestrator/campaign/login_headroom.py"] for name in names
    }


def test_login_headroom_is_stdlib_only_and_defers_annotations():
    source = (
        _REPO / "orchestrator" / "campaign" / "login_headroom.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    assert imports == {
        "__future__",
        "contextlib",
        "ctypes",
        "dataclasses",
        "enum",
        "errno",
        "fcntl",
        "json",
        "math",
        "os",
        "pathlib",
        "secrets",
        "time",
        "typing",
    }
    assert isinstance(tree.body[0], ast.Expr)  # module docstring
    future = next(node for node in tree.body if isinstance(node, ast.ImportFrom))
    assert future.module == "__future__"
    assert [alias.name for alias in future.names] == ["annotations"]


def _parameter_cases(test):
    cases = [({}, "")]
    for mark in getattr(test, "pytestmark", ()):
        if mark.name != "parametrize":
            continue
        raw_names, values = mark.args[:2]
        names = (
            [name.strip() for name in raw_names.split(",")]
            if isinstance(raw_names, str)
            else list(raw_names)
        )
        expanded = []
        for base, base_label in cases:
            for index, value in enumerate(values):
                if hasattr(value, "values"):
                    value = value.values
                row = (value,) if len(names) == 1 else tuple(value)
                parameters = dict(base, **dict(zip(names, row)))
                expanded.append((parameters, f"{base_label}[{index}]"))
        cases = expanded
    return cases


def _run():
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        for parameters, label in _parameter_cases(test):
            case_name = test.__name__ + label
            try:
                with tempfile.TemporaryDirectory(
                    prefix="izanagi_login_headroom_",
                ) as temporary, pytest.MonkeyPatch.context() as monkeypatch:
                    signature = inspect.signature(test).parameters
                    if "tmp_path" in signature:
                        parameters["tmp_path"] = Path(temporary)
                    if "monkeypatch" in signature:
                        parameters["monkeypatch"] = monkeypatch
                    test(**parameters)
                print(f"PASS {case_name}")
                passed += 1
            except AssertionError as exc:
                print(f"FAIL {case_name}: {exc}")
                failed += 1
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {case_name}: {type(exc).__name__}: {exc}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
