"""Real-process tests of directory removal, without mechanism replacement."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import cleanup_remove_dirs as removal

CLI = ROOT / "tools/cleanup_remove_dirs.py"


def _launch(paths, *, env, cwd, timeout=None):
    args = [sys.executable, str(CLI)]
    if timeout is not None:
        args += ["--timeout-seconds", str(timeout)]
    return subprocess.Popen(args + ["--", *map(str, paths)], env=env, cwd=cwd,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)


def _read_results(stdout):
    lines = [json.loads(line) for line in stdout.splitlines()]
    rows, summary = lines[:-1], lines[-1]
    assert summary["type"] == "summary"
    assert len(rows) == summary["total"]
    assert len({r["path"] for r in rows}) == len(rows)
    assert all(r["type"] == "path" for r in rows)
    for status in removal.STATUSES:
        assert summary[status] == sum(r["status"] == status for r in rows)
    assert summary == removal.summarize(rows, len(rows), summary["cancel_signal"])
    return rows, summary


def _state(pid):
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]


def _shdpnd(pid):
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("ShdPnd:"):
            return int(line.split()[1], 16)
    raise AssertionError("ShdPnd missing")


def _children(launcher_pid):
    children = set()
    for path in Path(f"/proc/{launcher_pid}/task").glob("*/children"):
        children.update(map(int, path.read_text().split()))
    return sorted(children)


def _child_states(children):
    states = {}
    for pid in children:
        try:
            states[pid] = _state(pid)
        except (OSError, IndexError) as exc:
            states[pid] = f"/proc/{pid}/stat unavailable: {exc}"
    return f"observed children pid -> /proc/<pid>/stat state: {states}"


def _wait_until(pred, deadline, *, children):
    while time.monotonic() < deadline:
        try:
            value = pred()
        except (OSError, AssertionError) as exc:
            raise AssertionError(f"synchronization failed: {exc}; {_child_states(children)}") from exc
        if value:
            return value
        time.sleep(0.005)
    raise AssertionError(f"synchronization deadline exceeded; {_child_states(children)}")


@pytest.fixture
def stopping_rm_bin(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    wrapper = bindir / "rm"
    wrapper.write_text('#!/bin/bash\nkill -STOP $$\nexec /bin/rm "$@"\n')
    wrapper.chmod(0o755)
    return dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"])


def _targets(tmp_path, count=1):
    paths = [tmp_path / f"target-{i}" for i in range(count)]
    for path in paths:
        path.mkdir()
        (path / "sentinel").write_text("keep until rm runs")
    return paths


def _stopped(proc, count, deadline):
    observed = set()
    def ready():
        children = _children(proc.pid)
        observed.update(children)
        return children if len(children) == count and all(_state(p) == "T" for p in children) else None
    return _wait_until(ready, deadline, children=observed)


def _finish(proc, deadline):
    stdout, stderr = proc.communicate(timeout=max(0.01, deadline - time.monotonic()))
    rows, summary = _read_results(stdout)
    assert proc.returncode == summary["rc"], stderr
    return rows, summary


def _cleanup(proc, children):
    if proc.poll() is None:
        children = set(children) | set(_children(proc.pid))
    for pid in children:
        try:
            os.kill(pid, signal.SIGCONT)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate(timeout=2)


def test_two_dirs_removed_without_wrapper(tmp_path):
    paths = _targets(tmp_path, 2)
    proc = _launch(paths, env=os.environ.copy(), cwd=tmp_path)
    try:
        rows, summary = _finish(proc, time.monotonic() + 6)
        assert summary["rc"] == 0
        assert [r["status"] for r in rows] == ["removed", "removed"]
        assert not any(p.exists() for p in paths)
    finally:
        _cleanup(proc, [])


def test_children_share_parent_pgid_then_remove(tmp_path, stopping_rm_bin):
    paths = _targets(tmp_path, 2)
    deadline = time.monotonic() + 6
    proc = _launch(paths, env=stopping_rm_bin, cwd=tmp_path)
    children = []
    try:
        children = _stopped(proc, 2, deadline)
        for pid in children:
            assert os.getpgid(pid) == os.getpgid(proc.pid)
        for pid in children:
            os.kill(pid, signal.SIGCONT)
        rows, summary = _finish(proc, deadline)
        assert summary["rc"] == 0
        assert all(r["status"] == "removed" for r in rows)
        assert not any(p.exists() for p in paths)
    finally:
        _cleanup(proc, children)


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGINT, signal.SIGHUP], ids=["TERM", "INT", "HUP"])
def test_launcher_signal_is_forwarded_before_removal(tmp_path, stopping_rm_bin, signum):
    paths = _targets(tmp_path)
    deadline = time.monotonic() + 6
    proc = _launch(paths, env=stopping_rm_bin, cwd=tmp_path)
    children = []
    try:
        children = _stopped(proc, 1, deadline)
        os.kill(proc.pid, signum)
        _wait_until(lambda: _shdpnd(children[0]) & (1 << (signum - 1)),
                    min(deadline, time.monotonic() + 2), children=children)
        os.kill(children[0], signal.SIGCONT)
        rows, summary = _finish(proc, deadline)
        assert summary["rc"] == 2
        assert summary["cancel_signal"] == signum
        assert rows[0]["status"] == "interrupted"
        assert rows[0]["returncode"] == -signum
        assert (paths[0] / "sentinel").is_file()
    finally:
        _cleanup(proc, children)


def test_timeout_is_interrupted(tmp_path, stopping_rm_bin):
    paths = _targets(tmp_path)
    deadline = time.monotonic() + 6
    proc = _launch(paths, env=stopping_rm_bin, cwd=tmp_path, timeout=0.5)
    children = []
    try:
        children = _stopped(proc, 1, deadline)
        _wait_until(lambda: _shdpnd(children[0]) & (1 << (signal.SIGTERM - 1)),
                    min(deadline, time.monotonic() + 2), children=children)
        os.kill(children[0], signal.SIGCONT)
        rows, summary = _finish(proc, deadline)
        assert summary["rc"] == 2
        assert summary["cancel_signal"] is None
        assert rows[0]["status"] == "interrupted"
        assert rows[0]["returncode"] == -signal.SIGTERM
        assert (paths[0] / "sentinel").exists()
    finally:
        _cleanup(proc, children)


def test_failed_path_does_not_hide_other_removal(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("root bypasses directory chmod; not acceptance evidence")
    parent = tmp_path / "locked"
    parent.mkdir()
    failed = _targets(parent)[0]
    removed = _targets(tmp_path)[0]
    parent.chmod(0o500)
    proc = None
    try:
        proc = _launch([failed, removed], env=os.environ.copy(), cwd=tmp_path)
        rows, summary = _finish(proc, time.monotonic() + 6)
        assert summary["rc"] == 1
        assert [r["status"] for r in rows] == ["failed", "removed"]
        assert failed.exists() and not removed.exists()
    finally:
        parent.chmod(0o700)
        if proc is not None:
            _cleanup(proc, [])


@pytest.mark.parametrize("case", ["nested", "duplicate", "relative", "missing", "symlink", "mid-symlink", "file", "root", "trailing-slash", "dotdot", "empty", "double-slash", "dot"])
def test_usage_rejects_paths_without_removal(tmp_path, case):
    target = _targets(tmp_path)[0]
    nested = target / "nested"
    nested.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    paths = {
        "nested": [target, nested], "duplicate": [target, target],
        "relative": [target.name], "missing": [tmp_path / "missing"],
        "symlink": [link], "mid-symlink": [link / "nested"],
        "file": [target / "sentinel"], "root": ["/"],
        "trailing-slash": [str(target) + "/"],
        "dotdot": [str(target) + "/../" + target.name], "empty": [""],
        "double-slash": ["/" + str(target)], "dot": [str(target) + "/."],
    }[case]
    proc = _launch([target, *paths] if case not in {"nested", "duplicate"} else paths,
                   env=os.environ.copy(), cwd=tmp_path)
    stdout, stderr = proc.communicate(timeout=8)
    assert proc.returncode == 64 and stdout == "", stderr
    assert (target / "sentinel").exists()


@pytest.mark.parametrize("case", ["exact", "descendant"])
def test_usage_rejects_cwd_inside_target(tmp_path, case):
    target = _targets(tmp_path)[0]
    child = target / "child"
    child.mkdir()
    proc = _launch([target], env=os.environ.copy(), cwd=target if case == "exact" else child)
    stdout, stderr = proc.communicate(timeout=8)
    assert proc.returncode == 64 and stdout == "", stderr
    assert (target / "sentinel").exists()


@pytest.mark.parametrize("options", [[], ["--"], ["--unknown", "--"],
    ["--timeout-seconds", "--"], ["--timeout-seconds", "bad", "--"],
    ["--timeout-seconds", "nan", "--"], ["--timeout-seconds", "inf", "--"],
    ["--timeout-seconds", "0", "--"], ["--timeout-seconds", "-1", "--"],
    ["--timeout-seconds", "1", "--timeout-seconds", "2", "--"]],
    ids=["no-separator", "no-paths", "unknown", "missing-value", "nonnumeric", "nan", "infinity", "zero", "negative", "duplicate"])
def test_usage_rejects_invalid_options(tmp_path, options):
    target = _targets(tmp_path)[0]
    args = options if options == ["--"] else [*options, str(target)]
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=tmp_path,
                            capture_output=True, text=True, timeout=8)
    assert result.returncode == 64 and result.stdout == "", result.stderr
    assert (target / "sentinel").exists()


def test_nul_path_is_rejected_before_spawn():
    with pytest.raises(ValueError):
        removal.parse_argv(["--", "/tmp/a\0b"])


def _exited_child(path, rc):
    process = subprocess.Popen([sys.executable, "-c", f"raise SystemExit({rc})"])
    process.wait(timeout=5)
    return removal.Child(str(path), process=process, pgid=os.getpgrp())


def test_zero_returncode_with_existing_path_is_failed(tmp_path):
    assert removal.classify(_exited_child(tmp_path, 0))["status"] == "failed"


def test_nonzero_returncode_with_absent_path_is_failed(tmp_path):
    assert removal.classify(_exited_child(tmp_path / "absent", 1))["status"] == "failed"


def test_summary_never_succeeds_for_incomplete_results():
    removed = dict(path="/a", status="removed")
    unknown = dict(path="/b", status="unknown")
    interrupted = dict(path="/b", status="interrupted")
    failed = dict(path="/b", status="failed")
    for rows, total, sig in [([], 0, None), ([removed], 2, None),
                             ([removed, dict(path="/b", status="removed"),
                               dict(path="/c", status="removed")], 2, None),
                             ([removed, dict(path="/b", status="done")], 2, None),
                             ([failed, dict(path="/c", status="interrupted")], 2, None),
                             ([removed, removed], 2, None),
                             ([removed, unknown], 2, None),
                             ([removed, interrupted], 2, None),
                             ([removed], 1, signal.SIGTERM)]:
        assert removal.summarize(rows, total, sig)["rc"] == 2
    assert removal.summarize([removed, failed], 2, None)["rc"] == 1
    assert removal.summarize([removed], 1, None, fault=True)["rc"] == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
