# -*- coding: utf-8 -*-
"""single-process one-shot claim の原子性と所有者記録。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign.campaign_claim import (  # noqa: E402
    ClaimError,
    ClaimRecord,
    acquire_claim,
    read_proc_starttime,
)


def _boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()


def _record(
    identity: str = "campaign-a",
    protocol_digest: str = "a" * 64,
) -> ClaimRecord:
    return ClaimRecord(
        campaign_identity=identity,
        protocol_digest=protocol_digest,
        job_id="123.server",
        host="node-a",
        boot_id=_boot_id(),
        pid=os.getpid(),
        proc_starttime=read_proc_starttime(),
        created_utc="2026-07-18T00:00:00+00:00",
    )


def _write_record(root: Path, record: ClaimRecord, *, legacy: bool = False) -> bytes:
    payload = asdict(record)
    if legacy:
        del payload["protocol_digest"]
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (root / f"{record.campaign_identity}.claim").write_bytes(raw)
    return raw


def test_read_proc_starttime_uses_field_22_with_spaced_comm():
    # fields 3..21 = state + 18 numeric tokens; the next token is field 22.
    stat_text = "321 (worker with spaces) S " + " ".join(str(i) for i in range(4, 22)) + " 987 0 0\n"
    assert read_proc_starttime(stat_text=stat_text) == 987


def test_acquire_writes_durable_json_and_duplicate_exposes_owner(tmp_path: Path):
    record = _record()
    acquired = acquire_claim(tmp_path, record)
    assert acquired.path == tmp_path / "campaign-a.claim"
    assert acquired.record == record
    assert json.loads(acquired.path.read_text(encoding="utf-8")) == {
        "boot_id": record.boot_id,
        "campaign_identity": "campaign-a",
        "created_utc": "2026-07-18T00:00:00+00:00",
        "host": "node-a",
        "job_id": "123.server",
        "pid": os.getpid(),
        "proc_starttime": record.proc_starttime,
        "protocol_digest": "a" * 64,
    }

    with pytest.raises(ClaimError) as exc_info:
        acquire_claim(tmp_path, record)
    assert exc_info.value.existing_record == record
    assert exc_info.value.claim_path == acquired.path


def test_acquire_fsyncs_claim_file_and_parent_directory(tmp_path: Path, monkeypatch):
    import orchestrator.campaign.campaign_claim as module

    calls = []
    monkeypatch.setattr(module.os, "fsync", lambda fd: calls.append(fd))
    acquired = acquire_claim(tmp_path, _record("fsync-count"))
    assert acquired.path.exists()
    assert len(calls) == 2


def test_claim_has_no_release_or_stale_recovery_api():
    import orchestrator.campaign.campaign_claim as module

    assert not hasattr(module, "release_claim")
    assert not hasattr(module, "recover_stale_claim")


def test_acquire_rejects_identity_path_traversal(tmp_path: Path):
    with pytest.raises(ClaimError):
        acquire_claim(tmp_path, _record("../escape"))


def test_two_real_processes_racing_acquire_have_exactly_one_winner(tmp_path: Path):
    ready_r, ready_w = os.pipe()
    start_r, start_w = os.pipe()
    script = r'''
import json
import os
import sys
from pathlib import Path
from orchestrator.campaign.campaign_claim import (
    ClaimError, ClaimRecord, acquire_claim, read_proc_starttime,
)

ready_fd = int(sys.argv[1])
start_fd = int(sys.argv[2])
root = sys.argv[3]
os.write(ready_fd, b"R")
os.read(start_fd, 1)
record = ClaimRecord(
    campaign_identity="race", protocol_digest="a" * 64,
    job_id="123.server", host="node-a",
    boot_id=Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
    pid=os.getpid(), proc_starttime=read_proc_starttime(),
    created_utc="2026-07-18T00:00:00+00:00",
)
try:
    acquire_claim(root, record)
except ClaimError as exc:
    print(json.dumps({"ok": False, "owner_pid": getattr(exc.existing_record, "pid", None)}))
else:
    print(json.dumps({"ok": True, "pid": os.getpid()}))
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ORCHESTRATOR.parent)
    children = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(ready_w), str(start_r), str(tmp_path)],
            pass_fds=(ready_w, start_r),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for _ in range(2)
    ]
    os.close(ready_w)
    os.close(start_r)
    try:
        ready = b""
        while len(ready) < 2:
            ready += os.read(ready_r, 2 - len(ready))
        assert ready == b"RR"
        os.write(start_w, b"GG")
    finally:
        os.close(ready_r)
        os.close(start_w)

    results = []
    for child in children:
        stdout, stderr = child.communicate(timeout=180)
        assert child.returncode == 0, stderr
        results.append(json.loads(stdout))
    assert sum(result["ok"] for result in results) == 1
    winner_pid = next(result["pid"] for result in results if result["ok"])
    loser = next(result for result in results if not result["ok"])
    assert loser["owner_pid"] == winner_pid


def test_same_protocol_live_owner_with_different_identity_is_rejected(tmp_path: Path):
    owner = _record("live-owner")
    acquire_claim(tmp_path, owner)

    with pytest.raises(ClaimError) as exc_info:
        acquire_claim(tmp_path, _record("contender"))

    assert exc_info.value.existing_record == owner
    assert exc_info.value.claim_path == tmp_path / "contender.claim"
    assert not exc_info.value.claim_path.exists()
    conflict = exc_info.value.conflict
    assert conflict is not None
    assert conflict.path == tmp_path / "live-owner.claim"
    assert conflict.record == owner
    assert conflict.observed_boot_id == _boot_id()
    assert conflict.observed_state != "Z"
    assert conflict.observed_starttime == owner.proc_starttime
    assert conflict.classification_reason == "live-owner"


def test_different_protocol_live_owner_is_accepted(tmp_path: Path):
    acquire_claim(tmp_path, _record("protocol-a", "a" * 64))

    acquired = acquire_claim(tmp_path, _record("protocol-b", "b" * 64))

    assert acquired.path == tmp_path / "protocol-b.claim"


def test_different_protocol_claim_being_written_is_retried_and_accepted(
        tmp_path: Path, monkeypatch):
    import orchestrator.campaign.campaign_claim as module

    owner = _record("protocol-a", "a" * 64)
    owner_path = tmp_path / "protocol-a.claim"
    owner_path.write_bytes(b"{")
    owner_raw = (
        json.dumps(asdict(owner), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    sleep_calls = []

    def finish_owner_write(seconds):
        sleep_calls.append(seconds)
        owner_path.write_bytes(owner_raw)

    monkeypatch.setattr(module.time, "sleep", finish_owner_write)

    acquired = acquire_claim(tmp_path, _record("protocol-b", "b" * 64))

    assert sleep_calls == [module._SCAN_DECODE_RETRY_SECONDS]
    assert acquired.path == tmp_path / "protocol-b.claim"
    assert owner_path.read_bytes() == owner_raw


def test_same_protocol_absent_owner_is_accepted(tmp_path: Path):
    absent_pid = os.getpid() + 1_000_000
    while Path(f"/proc/{absent_pid}").exists():
        absent_pid += 1
    stale = replace(_record("absent-owner"), pid=absent_pid, proc_starttime=1)
    _write_record(tmp_path, stale)

    acquired = acquire_claim(tmp_path, _record("successor"))

    assert acquired.path == tmp_path / "successor.claim"
    assert (tmp_path / "absent-owner.claim").exists()


def test_same_protocol_reused_pid_starttime_is_accepted(tmp_path: Path):
    stale = replace(
        _record("reused-pid-owner"),
        proc_starttime=read_proc_starttime() + 1,
    )
    _write_record(tmp_path, stale)

    acquired = acquire_claim(tmp_path, _record("successor"))

    assert acquired.path == tmp_path / "successor.claim"


def test_other_boot_same_protocol_is_indeterminate_and_accepted(tmp_path: Path):
    other_boot = replace(_record("other-boot-owner"), boot_id=f"{_boot_id()}-other")
    _write_record(tmp_path, other_boot)

    acquired = acquire_claim(tmp_path, _record("successor"))

    assert acquired.path == tmp_path / "successor.claim"


def test_legacy_claim_without_protocol_digest_is_indeterminate_and_accepted(tmp_path: Path):
    _write_record(tmp_path, _record("legacy-owner"), legacy=True)

    acquired = acquire_claim(tmp_path, _record("successor"))

    assert acquired.path == tmp_path / "successor.claim"
    assert (tmp_path / "legacy-owner.claim").exists()


def test_zombie_owner_is_dead_and_same_protocol_is_accepted(tmp_path: Path):
    import orchestrator.campaign.campaign_claim as module

    ready_r, ready_w = os.pipe()
    exit_r, exit_w = os.pipe()
    script = "import os,sys; os.write(int(sys.argv[1]), b'R'); os.read(int(sys.argv[2]), 1)"
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(ready_w), str(exit_r)],
        pass_fds=(ready_w, exit_r),
    )
    os.close(ready_w)
    os.close(exit_r)
    try:
        assert os.read(ready_r, 1) == b"R"
        stat_path = Path(f"/proc/{child.pid}/stat")
        state, starttime = module._parse_proc_stat(stat_path.read_text(encoding="ascii"))
        assert state != "Z"
        zombie_record = replace(
            _record("zombie-owner"),
            pid=child.pid,
            proc_starttime=starttime,
        )
        _write_record(tmp_path, zombie_record)
        os.write(exit_w, b"G")
        os.close(exit_w)
        exit_w = -1

        deadline = time.monotonic() + 120
        while True:
            state, _ = module._parse_proc_stat(stat_path.read_text(encoding="ascii"))
            if state == "Z":
                break
            if time.monotonic() >= deadline:
                pytest.fail("child process が zombie にならなかった")
            time.sleep(0.05)

        acquired = acquire_claim(tmp_path, _record("successor"))
        assert acquired.path == tmp_path / "successor.claim"
    finally:
        os.close(ready_r)
        if exit_w >= 0:
            os.close(exit_w)
        child.wait(timeout=180)


def test_malformed_existing_record_is_claim_error(tmp_path: Path):
    broken = tmp_path / "broken.claim"
    broken.write_bytes(b"{\n")

    with pytest.raises(ClaimError) as exc_info:
        acquire_claim(tmp_path, _record("contender"))

    assert exc_info.value.claim_path == broken
    assert exc_info.value.raw_payload == b"{\n"


def test_existing_record_io_error_is_claim_error(tmp_path: Path, monkeypatch):
    import orchestrator.campaign.campaign_claim as module

    _write_record(tmp_path, _record("owner"))

    def read_fails(_fd, _size):
        raise OSError("read failure")

    monkeypatch.setattr(module.os, "read", read_fails)
    with pytest.raises(ClaimError, match="読み取れない"):
        acquire_claim(tmp_path, _record("contender"))


def test_proc_permission_error_is_claim_error(tmp_path: Path, monkeypatch):
    import builtins

    owner = _record("owner")
    _write_record(tmp_path, owner)
    real_open = builtins.open

    def permission_denied(path, *args, **kwargs):
        if os.fspath(path) == f"/proc/{owner.pid}/stat":
            raise PermissionError("denied")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", permission_denied)
    with pytest.raises(ClaimError, match="読み取れない"):
        acquire_claim(tmp_path, _record("contender"))


def test_malformed_proc_stat_is_claim_error(tmp_path: Path, monkeypatch):
    import builtins
    import io

    owner = _record("owner")
    _write_record(tmp_path, owner)
    real_open = builtins.open

    def malformed_stat(path, *args, **kwargs):
        if os.fspath(path) == f"/proc/{owner.pid}/stat":
            return io.StringIO("malformed")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", malformed_stat)
    with pytest.raises(ClaimError, match="構造化して読めない"):
        acquire_claim(tmp_path, _record("contender"))


def test_unreadable_current_boot_id_is_claim_error(tmp_path: Path, monkeypatch):
    import builtins

    record = _record()
    real_open = builtins.open

    def permission_denied(path, *args, **kwargs):
        if os.fspath(path) == "/proc/sys/kernel/random/boot_id":
            raise PermissionError("denied")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", permission_denied)
    with pytest.raises(ClaimError, match="boot_id を読み取れない"):
        acquire_claim(tmp_path, record)


@pytest.mark.parametrize("field", ["pid", "proc_starttime", "boot_id"])
def test_acquire_rejects_record_not_matching_self_measurement(tmp_path: Path, field: str):
    record = _record()
    mismatch = {
        "pid": record.pid + 1,
        "proc_starttime": record.proc_starttime + 1,
        "boot_id": f"{record.boot_id}-other",
    }[field]

    with pytest.raises(ClaimError, match="self の実測値"):
        acquire_claim(tmp_path, replace(record, **{field: mismatch}))

    assert not (tmp_path / "campaign-a.claim").exists()


def test_exact_collision_legacy_schema_returns_raw_payload_without_deletion(tmp_path: Path):
    record = _record("exact")
    raw = _write_record(tmp_path, record, legacy=True)
    path = tmp_path / "exact.claim"

    with pytest.raises(ClaimError) as exc_info:
        acquire_claim(tmp_path, record)

    assert exc_info.value.claim_path == path
    assert exc_info.value.raw_payload == raw
    assert path.read_bytes() == raw


def test_prescan_permission_error_on_writable_root_is_claim_error(
        tmp_path: Path, monkeypatch):
    import orchestrator.campaign.campaign_claim as module

    claim_root = tmp_path / "claims"
    claim_root.mkdir()
    real_scandir = module.os.scandir
    calls = 0

    def fail_first_scan(path):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError("prescan denied")
        return real_scandir(path)

    monkeypatch.setattr(module.os, "scandir", fail_first_scan)
    with pytest.raises(ClaimError, match="列挙できない"):
        acquire_claim(claim_root, _record())

    assert calls == 1
    assert os.access(claim_root, os.W_OK)
    assert not (claim_root / "campaign-a.claim").exists()


def test_postscan_chmod_permission_error_is_claim_error_and_keeps_claim(
        tmp_path: Path, monkeypatch):
    import orchestrator.campaign.campaign_claim as module

    claim_root = tmp_path / "claims"
    claim_root.mkdir()
    real_fsync = module.os.fsync
    calls = 0

    def revoke_after_directory_fsync(fd):
        nonlocal calls
        calls += 1
        real_fsync(fd)
        if calls == 2:
            claim_root.chmod(0o000)

    monkeypatch.setattr(module.os, "fsync", revoke_after_directory_fsync)
    try:
        with pytest.raises(ClaimError, match="列挙できない"):
            acquire_claim(claim_root, _record())
    finally:
        claim_root.chmod(0o700)

    assert calls == 2
    assert (claim_root / "campaign-a.claim").exists()


def test_forced_postscan_both_reject_then_dead_owners_allow_next_acquire(tmp_path: Path):
    sync_root = tmp_path / "sync"
    claim_root = tmp_path / "claims"
    sync_root.mkdir()
    claim_root.mkdir()
    script = r'''
import json
import os
import sys
import time
from pathlib import Path
import orchestrator.campaign.campaign_claim as module

identity, claim_root_arg, sync_root_arg = sys.argv[1:]
claim_root = Path(claim_root_arg)
sync_root = Path(sync_root_arg)
original_scan = module._scan_protocol_conflicts
call_count = 0

def wait_for(prefix):
    deadline = time.monotonic() + 120
    ready_count = len([name for name in os.listdir(sync_root) if name.startswith(prefix)])
    while ready_count < 2:
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"barrier timeout: prefix={prefix!r}, ready={ready_count}/2"
            )
        time.sleep(0.05)
        ready_count = len(
            [name for name in os.listdir(sync_root) if name.startswith(prefix)]
        )

def synchronized_scan(*args, **kwargs):
    global call_count
    call_count += 1
    if call_count == 1:
        result = original_scan(*args, **kwargs)
        (sync_root / f"pre-{identity}").write_text("ready", encoding="ascii")
        wait_for("pre-")
        return result
    (sync_root / f"post-{identity}").write_text("ready", encoding="ascii")
    wait_for("post-")
    return original_scan(*args, **kwargs)

module._scan_protocol_conflicts = synchronized_scan
record = module.ClaimRecord(
    campaign_identity=identity,
    protocol_digest="a" * 64,
    job_id="123.server",
    host="node-a",
    boot_id=Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
    pid=os.getpid(),
    proc_starttime=module.read_proc_starttime(),
    created_utc="2026-07-18T00:00:00+00:00",
)
try:
    module.acquire_claim(claim_root, record)
except module.ClaimError:
    print(json.dumps({"ok": False}))
else:
    print(json.dumps({"ok": True}))
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ORCHESTRATOR.parent)
    children = [
        subprocess.Popen(
            [sys.executable, "-c", script, identity, str(claim_root), str(sync_root)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for identity in ("owner-a", "owner-b")
    ]
    results = []
    for child in children:
        stdout, stderr = child.communicate(timeout=180)
        assert child.returncode == 0, stderr
        results.append(json.loads(stdout))
    assert [result["ok"] for result in results] == [False, False]

    acquired = acquire_claim(claim_root, _record("successor"))
    assert acquired.path == claim_root / "successor.claim"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
