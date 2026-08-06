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


def _ledger_base(tmp_path: Path) -> Path:
    base = tmp_path / "runtime"
    base.mkdir(mode=0o700, exist_ok=True)
    base.chmod(0o700)
    return base


def _reservation_files(tmp_path: Path) -> list[Path]:
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    return sorted(directory.glob("*.json")) if directory.exists() else []


def _write_reservation_record(
    tmp_path: Path,
    *,
    pid: int,
    starttime: int,
    estimate_bytes: int,
    scope_cgroup: Path | None = None,
    name: str = "fixture.json",
) -> Path:
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    record = directory / name
    record.write_text(
        json.dumps(
            {
                "pid": pid,
                "starttime": starttime,
                "estimate_bytes": estimate_bytes,
                "acquired_at": 1.0,
                "scope_cgroup": str(scope_cgroup) if scope_cgroup is not None else None,
            }
        ),
        encoding="utf-8",
    )
    record.chmod(0o600)
    return record


def _write_legacy_reservation_record(
    tmp_path: Path,
    *,
    pid: int,
    estimate_bytes: int,
    acquired_at: float,
    name: str = "legacy.json",
) -> Path:
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    record = directory / name
    record.write_text(
        json.dumps(
            {
                "pid": pid,
                "estimate_bytes": estimate_bytes,
                "acquired_at": acquired_at,
            }
        ),
        encoding="utf-8",
    )
    record.chmod(0o600)
    return record


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
    assert LH.admit(101, _base_dir=_ledger_base(tmp_path))[0] is LH.Admission.DISPATCH


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


def test_filesystem_magic_is_checked_on_root_and_actual_user_slice_directory(
    tmp_path,
    monkeypatch,
):
    paths = _fake_cgroup(tmp_path, monkeypatch)
    checked = []

    def record_magic(fd):
        checked.append(Path(os.readlink(f"/proc/self/fd/{fd}")))
        return LH._CGROUP2_SUPER_MAGIC

    monkeypatch.setattr(LH, "_filesystem_magic", record_magic)

    assert LH.login_headroom() is not None
    assert checked == [paths["root"], paths["own"]]


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
    admission, reason = LH.admit(1, _base_dir=_ledger_base(tmp_path))
    assert admission is LH.Admission.DISPATCH
    assert isinstance(reason, str) and reason
    assert LH.grant_budget(
        max_bytes=1,
        min_bytes=1,
        _base_dir=_ledger_base(tmp_path),
    )[0] is LH.Admission.DISPATCH


@pytest.mark.parametrize("estimate", [0, -1, True, "1"])
def test_nonpositive_or_noninteger_estimate_dispatches_without_observation(
    tmp_path,
    monkeypatch,
    estimate,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: (_ for _ in ()).throw(AssertionError("must not observe")),
    )
    assert LH.admit(estimate, _base_dir=_ledger_base(tmp_path))[0] is LH.Admission.DISPATCH
    with LH.reserve(estimate, _base_dir=_ledger_base(tmp_path)) as decision:
        assert decision[0] is LH.Admission.DISPATCH


def test_admission_accepts_exact_ceiling_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + 100,
            current=50,
        ),
    )

    admission, reason = LH.admit(50, _base_dir=_ledger_base(tmp_path))

    assert admission is LH.Admission.LOCAL
    assert isinstance(reason, str) and reason


def test_grant_budget_is_capped_at_maximum_and_records_diagnostics(
    tmp_path,
    monkeypatch,
):
    current = 12345
    ceiling = current + LH.RESERVE_BYTES + LH.MAX_LOCAL_BUDGET_BYTES + 999
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=ceiling, current=current),
    )

    grant = LH.grant_budget(_base_dir=_ledger_base(tmp_path))
    admission, budget, reason = grant

    assert admission is LH.Admission.LOCAL
    assert budget == LH.MAX_LOCAL_BUDGET_BYTES
    assert f"{budget} bytes" in reason
    assert f"現在使用量={current} bytes" in reason
    assert f"実効天井={ceiling} bytes" in reason
    records = _reservation_files(tmp_path)
    assert len(records) == 1
    assert json.loads(records[0].read_text(encoding="utf-8"))["estimate_bytes"] == budget
    assert "解放しました" in grant.release()
    assert _reservation_files(tmp_path) == []


def test_grant_budget_dispatches_below_minimum(tmp_path, monkeypatch):
    available = LH.MIN_LOCAL_BUDGET_BYTES - 1
    ceiling = LH.RESERVE_BYTES + available
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=ceiling, current=0),
    )

    admission, budget, reason = LH.grant_budget(_base_dir=_ledger_base(tmp_path))

    assert admission is LH.Admission.DISPATCH
    assert budget is None
    assert f"算出予算={available} bytes" in reason
    assert _reservation_files(tmp_path) == []


def test_grant_budget_subtracts_live_reservations(tmp_path, monkeypatch):
    available = 1000
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + available,
            current=0,
        ),
    )

    with LH.reserve(250, _base_dir=_ledger_base(tmp_path)) as first:
        assert first[0] is LH.Admission.LOCAL
        admission, budget, reason = LH.grant_budget(
            max_bytes=available,
            min_bytes=1,
            _base_dir=_ledger_base(tmp_path),
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

    monkeypatch.setattr(LH, "_locked_ledger", lambda **_kwargs: LockedLedger())
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
        return 0, []

    def create(directory_fd, budget, *, scope_cgroup=None):
        assert directory_fd == 99
        assert budget == 100
        assert scope_cgroup is None
        events.append("reserve")
        return "reservation.json"

    monkeypatch.setattr(LH, "_collect_live_reservations", collect)
    monkeypatch.setattr(LH, "_create_reservation", create)

    assert LH.grant_budget(max_bytes=100, min_bytes=1)[:2] == (
        LH.Admission.LOCAL,
        100,
    )
    assert events == ["lock-enter", "decide", "reserve", "lock-exit"]


def test_environment_cannot_override_production_ledger_namespace_but_private_argument_can(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(LH.os, "getuid", lambda: _UID)
    assert LH._admission_directory() == (
        Path("/run/user") / str(_UID) / LH.ADMISSION_DIRNAME
    )

    monkeypatch.setenv("IZANAGI_ADMISSION_BASE_DIR", str(tmp_path / "attacker"))
    assert LH._admission_directory() == (
        Path("/run/user") / str(_UID) / LH.ADMISSION_DIRNAME
    )
    assert LH._admission_directory(_base_dir=tmp_path) == tmp_path / LH.ADMISSION_DIRNAME


def test_second_concurrent_reservation_dispatches_when_live_sum_exceeds_ceiling(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    with LH.reserve(40, _base_dir=_ledger_base(tmp_path)) as first:
        assert first[0] is LH.Admission.LOCAL
        assert len(_reservation_files(tmp_path)) == 1
        with LH.reserve(61, _base_dir=_ledger_base(tmp_path)) as second:
            assert second[0] is LH.Admission.DISPATCH
            assert len(_reservation_files(tmp_path)) == 1
    assert _reservation_files(tmp_path) == []


def test_dead_pid_reservation_is_recovered_before_admission(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 10, current=0),
    )
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700)
    stale = directory / "stale.json"
    stale.write_text(
        json.dumps(
            {
                "pid": 99999999,
                "starttime": 1,
                "estimate_bytes": 1000,
                "acquired_at": 1.0,
                "scope_cgroup": None,
            }
        ),
        encoding="utf-8",
    )
    stale.chmod(0o600)
    monkeypatch.setattr(LH, "_process_starttime", lambda pid: None)

    admission, _ = LH.admit(1, _base_dir=_ledger_base(tmp_path))

    assert admission is LH.Admission.LOCAL
    assert not stale.exists()


def test_legacy_schema_dead_pid_is_recovered_by_next_grant(
    tmp_path,
    monkeypatch,
):
    dead_pid = 99999999
    stale = _write_legacy_reservation_record(
        tmp_path,
        pid=dead_pid,
        estimate_bytes=90,
        acquired_at=LH.time.time(),
    )
    real_process_starttime = LH._process_starttime
    monkeypatch.setattr(
        LH,
        "_process_starttime",
        lambda pid: None if pid == dead_pid else real_process_starttime(pid),
    )
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    grant = LH.grant_budget(
        max_bytes=100,
        min_bytes=1,
        _base_dir=_ledger_base(tmp_path),
    )

    assert grant.admission is LH.Admission.LOCAL
    assert grant.budget_bytes == 100
    assert "生存中の予約=0 bytes" in grant.reason
    assert "壊れた予約 record" not in grant.reason
    assert not stale.exists()
    grant.release()


def test_legacy_schema_live_pid_is_kept_and_charged_safely(
    tmp_path,
    monkeypatch,
):
    legacy = _write_legacy_reservation_record(
        tmp_path,
        pid=os.getpid(),
        estimate_bytes=90,
        acquired_at=LH.time.time(),
    )
    monkeypatch.setattr(LH, "_process_starttime", lambda _pid: 12345)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + LH.MAX_LOCAL_BUDGET_BYTES + 100,
            current=0,
        ),
    )

    grant = LH.grant_budget(
        max_bytes=100,
        min_bytes=1,
        _base_dir=_ledger_base(tmp_path),
    )

    assert grant.admission is LH.Admission.LOCAL
    assert grant.budget_bytes == 100
    assert f"生存中の予約={LH.MAX_LOCAL_BUDGET_BYTES} bytes" in grant.reason
    assert "壊れた予約 record legacy.json を最大予算分として算入" in grant.reason
    assert legacy.exists()
    grant.release()


def test_reservation_context_releases_record_when_body_raises(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    with pytest.raises(RuntimeError, match="body failed"):
        with LH.reserve(1, _base_dir=_ledger_base(tmp_path)) as decision:
            assert decision[0] is LH.Admission.LOCAL
            records = _reservation_files(tmp_path)
            assert len(records) == 1
            record = json.loads(records[0].read_text(encoding="utf-8"))
            assert set(record) == {
                "pid",
                "starttime",
                "estimate_bytes",
                "acquired_at",
                "scope_cgroup",
            }
            assert record["pid"] == os.getpid()
            assert isinstance(record["starttime"], int)
            assert record["estimate_bytes"] == 1
            assert isinstance(record["acquired_at"], float)
            assert record["scope_cgroup"] is None
            raise RuntimeError("body failed")
    assert _reservation_files(tmp_path) == []


def test_reservation_context_releases_record_on_keyboard_interrupt(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    with pytest.raises(KeyboardInterrupt):
        with LH.reserve(1, _base_dir=_ledger_base(tmp_path)) as decision:
            assert decision[0] is LH.Admission.LOCAL
            raise KeyboardInterrupt
    assert _reservation_files(tmp_path) == []


@pytest.mark.parametrize(
    "violation",
    ["owner", "mode"],
    ids=["wrong-owner", "wrong-mode"],
)
def test_ledger_directory_wrong_owner_or_mode_dispatches(
    tmp_path,
    monkeypatch,
    violation,
):
    base = _ledger_base(tmp_path)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    if violation == "owner":
        actual_euid = os.geteuid()
        monkeypatch.setattr(LH.os, "geteuid", lambda: actual_euid + 1)
    else:
        base.chmod(0o755)

    admission, budget, reason = LH.grant_budget(
        max_bytes=100,
        min_bytes=1,
        _base_dir=base,
    )

    assert admission is LH.Admission.DISPATCH
    assert budget is None
    assert "予約台帳を安全に更新できない" in reason


def test_ledger_directory_and_record_modes_are_private(tmp_path, monkeypatch):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    grant = LH.grant_budget(max_bytes=100, min_bytes=1, _base_dir=_ledger_base(tmp_path))

    assert grant.admission is LH.Admission.LOCAL
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    assert directory.stat().st_mode & 0o777 == 0o700
    assert (directory / ".lock").stat().st_mode & 0o777 == 0o600
    assert _reservation_files(tmp_path)[0].stat().st_mode & 0o777 == 0o600
    grant.release()


def test_grant_handle_can_bind_scope_after_scope_path_is_known(tmp_path, monkeypatch):
    paths = _fake_cgroup(tmp_path, monkeypatch)
    scope = paths["root"] / "user.slice" / f"user-{_UID}.slice" / "late.scope"
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    grant = LH.grant_budget(
        max_bytes=100,
        min_bytes=1,
        _base_dir=_ledger_base(tmp_path),
    )

    reason = grant.bind_scope(scope)

    assert "結び付けました" in reason
    record = json.loads(_reservation_files(tmp_path)[0].read_text(encoding="utf-8"))
    assert record["scope_cgroup"] == str(scope)
    grant.release()


def test_dead_pid_with_populated_scope_cgroup_keeps_reservation(
    tmp_path,
    monkeypatch,
):
    paths = _fake_cgroup(tmp_path, monkeypatch)
    scope = paths["root"] / "user.slice" / f"user-{_UID}.slice" / "run.scope"
    scope.mkdir()
    _write(scope / "cgroup.events", "populated 1\nfrozen 0\n")
    record = _write_reservation_record(
        tmp_path,
        pid=99999999,
        starttime=1,
        estimate_bytes=90,
        scope_cgroup=scope,
    )
    monkeypatch.setattr(LH, "_process_starttime", lambda _pid: None)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    admission, reason = LH.admit(20, _base_dir=_ledger_base(tmp_path))

    assert admission is LH.Admission.DISPATCH
    assert "生存中の予約=90 bytes" in reason
    assert record.exists()


def test_dead_pid_and_missing_scope_cgroup_reclaims_reservation(
    tmp_path,
    monkeypatch,
):
    paths = _fake_cgroup(tmp_path, monkeypatch)
    missing_scope = paths["root"] / "missing.scope"
    record = _write_reservation_record(
        tmp_path,
        pid=99999999,
        starttime=1,
        estimate_bytes=90,
        scope_cgroup=missing_scope,
    )
    monkeypatch.setattr(LH, "_process_starttime", lambda _pid: None)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    assert LH.admit(20, _base_dir=_ledger_base(tmp_path))[0] is LH.Admission.LOCAL
    assert not record.exists()


def test_pid_reuse_with_same_pid_and_different_starttime_reclaims_reservation(
    tmp_path,
    monkeypatch,
):
    record = _write_reservation_record(
        tmp_path,
        pid=os.getpid(),
        starttime=111,
        estimate_bytes=90,
    )
    monkeypatch.setattr(LH, "_process_starttime", lambda _pid: 222)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )

    assert LH.admit(20, _base_dir=_ledger_base(tmp_path))[0] is LH.Admission.LOCAL
    assert not record.exists()


def test_ledger_lock_deadline_dispatches_without_hanging(tmp_path, monkeypatch):
    base = _ledger_base(tmp_path)
    directory = base / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700)
    lock_path = directory / ".lock"
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    os.chmod(lock_path, 0o600)
    LH.fcntl.flock(lock_fd, LH.fcntl.LOCK_EX | LH.fcntl.LOCK_NB)
    monkeypatch.setattr(LH, "LEDGER_LOCK_TIMEOUT_S", 0.02)
    monkeypatch.setattr(LH, "LEDGER_LOCK_RETRY_S", 0.001)
    started = LH.time.monotonic()
    try:
        admission, reason = LH.admit(1, _base_dir=base)
    finally:
        LH.fcntl.flock(lock_fd, LH.fcntl.LOCK_UN)
        os.close(lock_fd)

    assert admission is LH.Admission.DISPATCH
    assert "台帳 lock を取得できなかった" in reason
    assert LH.time.monotonic() - started < 0.5


def test_remembered_peak_larger_than_available_dispatches_immediately(
    tmp_path,
    monkeypatch,
):
    base = _ledger_base(tmp_path)
    LH.remember_peak("tests", LH.MAX_LOCAL_BUDGET_BYTES * 2, _base_dir=base)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + LH.MAX_LOCAL_BUDGET_BYTES,
            current=0,
        ),
    )

    grant = LH.grant_budget(operation="tests", _base_dir=base)

    assert grant.admission is LH.Admission.DISPATCH
    assert grant.budget_bytes is None
    assert f"前回ピーク {LH.MAX_LOCAL_BUDGET_BYTES * 2} bytes" in grant.reason
    assert f"今の余裕 {LH.MAX_LOCAL_BUDGET_BYTES} bytes" in grant.reason


def test_operation_without_remembered_peak_can_use_maximum_local_budget(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + LH.MAX_LOCAL_BUDGET_BYTES,
            current=0,
        ),
    )

    grant = LH.grant_budget(operation="first-probe", _base_dir=_ledger_base(tmp_path))

    assert grant.admission is LH.Admission.LOCAL
    assert grant.budget_bytes == LH.MAX_LOCAL_BUDGET_BYTES
    grant.release()


def test_remembered_peak_narrows_budget_to_estimate_instead_of_all_available(
    tmp_path,
    monkeypatch,
):
    base = _ledger_base(tmp_path)
    peak = 2 * 1024**3
    expected = int(peak * 1.25)
    LH.remember_peak("tests", peak, _base_dir=base)
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(
            ceiling=LH.RESERVE_BYTES + LH.MAX_LOCAL_BUDGET_BYTES,
            current=0,
        ),
    )

    grant = LH.grant_budget(operation="tests", _base_dir=base)

    assert grant.admission is LH.Admission.LOCAL
    assert grant.budget_bytes == expected
    assert grant.budget_bytes < LH.MAX_LOCAL_BUDGET_BYTES
    assert LH.recall_peak("tests", _base_dir=base) == peak
    assert LH.estimate_for("tests", _base_dir=base) == expected
    grant.release()


def test_corrupt_peak_is_treated_as_no_record(tmp_path):
    base = _ledger_base(tmp_path)
    directory = base / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700)
    peak = directory / "peak-tests.peak"
    peak.write_text("not-json", encoding="utf-8")
    peak.chmod(0o600)

    assert LH.recall_peak("tests", _base_dir=base) is None
    assert LH.estimate_for("tests", _base_dir=base) is None


def test_explicit_lease_release_failure_is_retained_in_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    grant = LH.grant_budget(max_bytes=100, min_bytes=1, _base_dir=_ledger_base(tmp_path))
    real_unlink = LH.os.unlink

    def fail_reservation_unlink(path, *args, **kwargs):
        if os.fspath(path).endswith(".json"):
            raise OSError("injected release failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(LH.os, "unlink", fail_reservation_unlink)

    reason = grant.release()

    assert "解放できなかった" in reason
    assert grant.release_reason == reason
    assert grant.lease is not None and grant.lease.released is False


def test_corrupt_reservation_is_charged_safely_and_reported_without_crashing(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700)
    broken = directory / "broken.json"
    broken.write_text("not-json", encoding="utf-8")
    broken.chmod(0o600)

    admission, reason = LH.admit(1, _base_dir=_ledger_base(tmp_path))
    assert admission is LH.Admission.DISPATCH
    assert "壊れた予約 record" in reason
    grant = LH.grant_budget(max_bytes=1, min_bytes=1, _base_dir=_ledger_base(tmp_path))
    assert grant[0] is LH.Admission.DISPATCH
    assert "生存中の予約=4294967296 bytes" in grant.reason
    assert "壊れた予約 record" in grant.reason
    assert broken.exists()
    with LH.reserve(1, _base_dir=_ledger_base(tmp_path)) as decision:
        assert decision[0] is LH.Admission.DISPATCH


def test_expired_corrupt_reservation_is_recovered_by_next_grant(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700)
    broken = directory / "expired.json"
    broken.write_text("not-json", encoding="utf-8")
    broken.chmod(0o600)
    expired = LH.time.time() - LH.STALE_RECORD_MAX_AGE_S - 1
    os.utime(broken, (expired, expired))

    grant = LH.grant_budget(
        max_bytes=100,
        min_bytes=1,
        _base_dir=_ledger_base(tmp_path),
    )

    assert grant.admission is LH.Admission.LOCAL
    assert grant.budget_bytes == 100
    assert "生存中の予約=0 bytes" in grant.reason
    assert "壊れた予約 record" not in grant.reason
    assert not broken.exists()
    grant.release()


def test_expired_corrupt_reservation_reclaim_failure_is_reported(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    directory = _ledger_base(tmp_path) / LH.ADMISSION_DIRNAME
    directory.mkdir(mode=0o700)
    broken = directory / "expired.json"
    broken.write_text("not-json", encoding="utf-8")
    broken.chmod(0o600)
    expired = LH.time.time() - LH.STALE_RECORD_MAX_AGE_S - 1
    os.utime(broken, (expired, expired))
    real_unlink = LH.os.unlink

    def fail_expired_unlink(path, *args, **kwargs):
        if os.fspath(path) == broken.name:
            raise OSError("injected reclaim failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(LH.os, "unlink", fail_expired_unlink)

    grant = LH.grant_budget(
        max_bytes=100,
        min_bytes=1,
        _base_dir=_ledger_base(tmp_path),
    )

    assert grant.admission is LH.Admission.DISPATCH
    assert "失効した予約 record expired.json を回収できず算入" in grant.reason
    assert "壊れた予約 record expired.json を最大予算分として算入" in grant.reason
    assert broken.exists()


def test_non_directory_private_ledger_base_dispatches(tmp_path, monkeypatch):
    monkeypatch.setattr(
        LH,
        "login_headroom",
        lambda: _observation(ceiling=LH.RESERVE_BYTES + 100, current=0),
    )
    blocking_file = tmp_path / "not-a-directory"
    blocking_file.write_text("x", encoding="utf-8")
    assert LH.admit(1, _base_dir=blocking_file)[0] is LH.Admission.DISPATCH
    assert LH.grant_budget(
        max_bytes=1,
        min_bytes=1,
        _base_dir=blocking_file,
    )[0] is LH.Admission.DISPATCH
    with LH.reserve(1, _base_dir=blocking_file) as decision:
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
        "stat",
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
