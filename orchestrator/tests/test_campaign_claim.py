# -*- coding: utf-8 -*-
"""single-process one-shot claim の原子性と所有者記録。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
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


def _record(identity: str = "campaign-a") -> ClaimRecord:
    return ClaimRecord(
        campaign_identity=identity,
        job_id="123.server",
        host="node-a",
        boot_id="boot-a",
        pid=os.getpid(),
        proc_starttime=read_proc_starttime(),
        created_utc="2026-07-18T00:00:00+00:00",
    )


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
        "boot_id": "boot-a",
        "campaign_identity": "campaign-a",
        "created_utc": "2026-07-18T00:00:00+00:00",
        "host": "node-a",
        "job_id": "123.server",
        "pid": os.getpid(),
        "proc_starttime": record.proc_starttime,
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
from orchestrator.campaign.campaign_claim import ClaimError, ClaimRecord, acquire_claim, read_proc_starttime

ready_fd = int(sys.argv[1])
start_fd = int(sys.argv[2])
root = sys.argv[3]
os.write(ready_fd, b"R")
os.read(start_fd, 1)
record = ClaimRecord(
    campaign_identity="race", job_id="123.server", host="node-a", boot_id="boot-a",
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
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 0, stderr
        results.append(json.loads(stdout))
    assert sum(result["ok"] for result in results) == 1
    winner_pid = next(result["pid"] for result in results if result["ok"])
    loser = next(result for result in results if not result["ok"])
    assert loser["owner_pid"] == winner_pid


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
