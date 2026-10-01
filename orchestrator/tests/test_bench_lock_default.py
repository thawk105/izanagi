"""Default-path contract, exercised with real open/flock on reserved negative UIDs."""
from __future__ import annotations

import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import uuid

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from orchestrator.campaign import lock


@pytest.mark.parametrize("uid", [0, 12345])
def test_default_lock_path_uses_uid(monkeypatch, uid):
    monkeypatch.delenv("IZANAGI_BENCH_LOCK", raising=False)
    monkeypatch.setattr(lock.os, "getuid", lambda: uid)
    assert lock.default_lock_path() == f"/tmp/izanagi-bench-{uid}.lock"


@pytest.mark.parametrize("name", ["HOME", "TMPDIR", "TMP", "TEMP"])
def test_default_lock_path_ignores_home_and_temp_dirs(monkeypatch, tmp_path, name):
    monkeypatch.delenv("IZANAGI_BENCH_LOCK", raising=False)
    expected = f"/tmp/izanagi-bench-{os.getuid()}.lock"
    for value in (tmp_path / "one", tmp_path / "two"):
        value.mkdir()
        monkeypatch.setenv(name, str(value))
        # Exercise environment-sensitive tempdir implementations even after
        # pytest has populated tempfile's process-global cache.
        monkeypatch.setattr(tempfile, "tempdir", None)
        assert lock.default_lock_path() == expected


def test_default_lock_path_does_not_create_home_state(monkeypatch, tmp_path):
    monkeypatch.delenv("IZANAGI_BENCH_LOCK", raising=False)
    home = tmp_path / "absent-home"
    monkeypatch.setenv("HOME", str(home))
    lock.default_lock_path()
    assert not home.exists()
    assert not (home / ".izanagi").exists()


def test_empty_bench_lock_env_uses_default(monkeypatch):
    monkeypatch.delenv("IZANAGI_BENCH_LOCK", raising=False)
    expected = lock.default_lock_path()
    monkeypatch.setenv("IZANAGI_BENCH_LOCK", "")
    assert lock.default_lock_path() == expected
    assert expected == f"/tmp/izanagi-bench-{os.getuid()}.lock"


@pytest.mark.parametrize("value", [
    "/absent/bench.lock", "relative/bench.lock", "~/bench.lock",
    "$TMPDIR/bench.lock", " path with spaces ", " ",
])
def test_bench_lock_env_override_is_returned_verbatim(monkeypatch, tmp_path, value):
    monkeypatch.chdir(tmp_path)
    home = tmp_path / "absent-home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("IZANAGI_BENCH_LOCK", value)
    assert lock.default_lock_path() == value
    assert list(tmp_path.iterdir()) == []


# Exec children replace getuid only after importing production code. The audit
# hook observes real os.open calls and stops accidental production-path access
# before the kernel open; it does not replace open, flock or default_lock_path.
_CHILD = r'''
import json
import os
import select
import sys
from orchestrator.campaign import lock

uid, path, mode = int(sys.argv[1]), sys.argv[2], sys.argv[3]
real_path = f"/tmp/izanagi-bench-{os.getuid()}.lock"
assert uid < 0 and path != real_path
opened = []

def audit(event, args):
    if event == "open":
        assert args[0] != real_path, "attempt to open the real UID lock"
        if args[0] == path:
            opened.append(path)

sys.addaudithook(audit)
os.environ.pop("IZANAGI_BENCH_LOCK", None)
lock.os.getuid = lambda: uid
assert lock.default_lock_path() == path

def receive(expected):
    assert select.select([sys.stdin], [], [], 10)[0], "command timeout"
    assert sys.stdin.readline().strip() == expected

if mode == "holder":
    with lock.bench_lock():
        print("held", flush=True)
        receive("release")
    print("released", flush=True)
elif mode == "contender":
    try:
        with lock.bench_lock(blocking=False):
            raise AssertionError("another process entered the held lock")
    except lock.BenchBusy:
        print("busy", flush=True)
    receive("retry")
    with lock.bench_lock(blocking=False):
        print("acquired", flush=True)
elif mode == "mtime":
    with lock.bench_lock():
        st = os.stat(path)
        print(json.dumps({"mtime_ns": st.st_mtime_ns, "inode": st.st_ino}), flush=True)
else:
    raise AssertionError(mode)
assert len(opened) == (2 if mode == "contender" else 1), opened
'''


def _receive(child):
    deadline = time.monotonic() + 10
    data = bytearray()
    while not data.endswith(b"\n"):
        remaining = deadline - time.monotonic()
        assert remaining > 0 and select.select([child.stdout], [], [], remaining)[0], (
            f"child {child.pid} response timed out"
        )
        byte = os.read(child.stdout.fileno(), 1)
        assert byte, f"child {child.pid} closed its response pipe"
        data.extend(byte)
    return data.decode().strip()


def _send(child, command):
    child.stdin.write((command + "\n").encode())
    child.stdin.flush()


def _finished(child):
    assert child.wait(timeout=10) == 0, child.stderr.read().decode()


@pytest.fixture
def reserved_lock():
    uid = -uuid.uuid4().int
    path = Path(f"/tmp/izanagi-bench-{uid}.lock")
    assert path != Path(f"/tmp/izanagi-bench-{os.getuid()}.lock")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        reserved = os.fstat(fd)
    finally:
        os.close(fd)
    children = []

    def start(mode):
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", _CHILD, str(uid), str(path), mode],
            cwd=_REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True,
        )
        children.append(child)
        return child

    try:
        yield path, reserved, start
    finally:
        # Reap every child before checking/removing our reservation, also when
        # a protocol assertion fails while a child still holds the lock.
        try:
            for child in children:
                if child.poll() is None:
                    child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
                finally:
                    for stream in (child.stdin, child.stdout, child.stderr):
                        stream.close()
        finally:
            current = path.lstat()
            assert (current.st_dev, current.st_ino) == (reserved.st_dev, reserved.st_ino)
            path.unlink()


def test_default_lock_excludes_another_process(reserved_lock):
    _, _, start = reserved_lock
    holder = start("holder")
    assert _receive(holder) == "held"
    contender = start("contender")
    assert _receive(contender) == "busy"
    _send(holder, "release")
    assert _receive(holder) == "released"
    _finished(holder)
    _send(contender, "retry")
    assert _receive(contender) == "acquired"
    _finished(contender)


def test_default_lock_acquisition_refreshes_mtime(reserved_lock):
    path, reserved, start = reserved_lock
    past = time.time_ns() - 30 * 24 * 60 * 60 * 1_000_000_000
    os.utime(path, ns=(past, past))
    before = path.stat().st_mtime_ns
    child = start("mtime")
    held = json.loads(_receive(child))
    _finished(child)
    assert held["inode"] == reserved.st_ino
    assert held["mtime_ns"] > before
    assert path.stat().st_mtime_ns == held["mtime_ns"]


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__, *sys.argv[1:]]))
