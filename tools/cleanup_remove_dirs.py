#!/usr/bin/env python3
"""Fixed directory removal launcher for D2104 item 32.

Children share this launcher's process group. TERM/INT/HUP received by the
launcher itself are forwarded; a group-directed signal reaches children directly.
SIGKILL to the launcher PID alone, killing only an upper shell, and Bash tool /
session signal delivery are not covered. PR_SET_PDEATHSIG is out of scope.
The process exit status is authoritative; the JSON summary rc mirrors it.
The success boundary is reap, lstat, restore TERM/INT/HUP to SIG_DFL, then the
final cancel check, JSONL output and stdout flush. Signals after restoration
terminate the launcher by default with nonzero exit status; JSON may be incomplete.
They cannot leave reaped removal children running. Unreaped children are unknown.
Path checks depend on the namespace at inspection time: later symlink replacement
and mounts below a target are not prevented. Ownership, merge and occupancy are
handled by cleanup-branches sections 1-3. rm is resolved through PATH, which is an
operational trust boundary. The 3600-second per-child default is provisional,
not a measured performance guarantee. No prune, detach or branch deletion occurs.
"""
from __future__ import annotations

import errno
import json
import math
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import BinaryIO, Callable

POLL_SECONDS = 0.05
TERM_GRACE_SECONDS = 5.0
KILL_GRACE_SECONDS = 1.0
STATUSES = ("removed", "failed", "interrupted", "unknown")


@dataclass
class Child:
    path: str
    process: subprocess.Popen | None = None
    started: float = 0.0
    pgid: int | None = None
    cancelled: bool = False
    error: str | None = None
    stdout: BinaryIO | None = None
    stderr: BinaryIO | None = None


def parse_argv(argv: list[str]) -> tuple[list[str], float]:
    if "--" not in argv:
        raise ValueError("required separator -- is missing")
    split = argv.index("--")
    options, paths = argv[:split], argv[split + 1:]
    timeout = 3600.0
    if options:
        if len(options) != 2 or options[0] != "--timeout-seconds":
            raise ValueError("only one --timeout-seconds S option is allowed")
        timeout = float(options[1])
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
    if not paths:
        raise ValueError("at least one directory is required")
    cwd = os.path.realpath(os.getcwd(), strict=True)
    for path in paths:
        if (not path or "\0" in path or not path.startswith("/")
                or path.startswith("//") or path == "/"
                or any(p in {"", ".", ".."} for p in path.split("/")[1:])):
            raise ValueError(f"noncanonical absolute path: {path!r}")
        cursor = ""
        for part in path.split("/")[1:]:
            cursor += "/" + part
            mode = os.lstat(cursor).st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise ValueError(f"not a nonsymlink directory: {cursor!r}")
        if os.path.realpath(path, strict=True) != path:
            raise ValueError(f"realpath mismatch: {path!r}")
        if os.path.commonpath([path, cwd]) == path:
            raise ValueError("cwd is inside a target")
    for index, path in enumerate(paths):
        for other in paths[:index]:
            if os.path.commonpath([path, other]) in {path, other}:
                raise ValueError("duplicate or nested targets")
    return paths, timeout


def _live(children: list[Child]) -> list[Child]:
    live = []
    for child in children:
        if child.process is None:
            continue
        try:
            if child.process.poll() is None:
                live.append(child)
        except Exception as exc:
            child.error = f"poll: {exc}"
            live.append(child)
    return live


def cancel(children: list[Child], signum: int,
           interrupted: Callable[[], int | None] = lambda: None) -> None:
    """The sole cancellation path; never wait without a deadline."""
    for sig, grace in ((signum, TERM_GRACE_SECONDS),
                       (signal.SIGKILL, KILL_GRACE_SECONDS)):
        live = _live(children)
        for child in live:
            child.cancelled = True
            try:
                os.kill(child.process.pid, sig)
            except ProcessLookupError:
                pass  # A subsequent poll must still reap it.
            except Exception as exc:
                child.error = f"signal: {exc}"
        deadline = time.monotonic() + grace
        while _live(children) and time.monotonic() < deadline:
            if interrupted():
                return
            time.sleep(POLL_SECONDS)
    for child in _live(children):
        child.error = "unreaped after cancellation"


def classify(child: Child) -> dict:
    """Recheck the actual path even after a successful child exit."""
    absent = False
    error = child.error
    try:
        os.lstat(child.path)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            absent = True
        else:
            error = f"lstat: {exc}"
    rc = child.process.returncode if child.process is not None else None
    if error:
        status, reason = "unknown", error
    elif child.process is None:
        status, reason = "interrupted", "not-started"
    elif rc is None or child.pgid is None:
        status, reason = "unknown", "unreaped or unverified pgid"
    elif child.cancelled or rc < 0:
        status, reason = "interrupted", "cancelled or signal exit"
    elif rc > 0 or not absent:
        status, reason = "failed", "nonzero exit or path remains"
    else:
        status, reason = "removed", "absent"
    return dict(type="path", path=child.path, status=status, returncode=rc,
                reason=reason, pid=child.process.pid if child.process else None,
                pgid=child.pgid, parent_pgid=os.getpgrp())


def summarize(results: list[dict], total: int, cancel_signal: int | None,
              fault: bool = False) -> dict:
    counts = {s: sum(r["status"] == s for r in results) for s in STATUSES}
    complete = (total > 0 and len(results) == total
                and len({r["path"] for r in results}) == total
                and sum(counts.values()) == total)
    if not complete or fault or cancel_signal or counts["unknown"] or counts["interrupted"]:
        rc = 2
    elif counts["failed"]:
        rc = 1
    elif counts["removed"] == total:
        rc = 0
    else:
        rc = 2
    return dict(type="summary", total=total, **counts, cancel_signal=cancel_signal, rc=rc)


def main(argv: list[str] | None = None) -> int:
    cancelled = None
    fault = False
    usage = False
    children: list[Child] = []
    results = []
    summary = None

    def handler(signum, frame):
        nonlocal cancelled
        if cancelled is None:
            cancelled = signum

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, handler)
    try:
        paths, timeout = parse_argv(sys.argv[1:] if argv is None else argv)
    except (ValueError, OSError) as exc:
        usage = True
        try:
            print(f"cleanup-remove-dirs: {exc}\nusage: cleanup_remove_dirs.py "
                  "[--timeout-seconds S] -- <absolute-directory>...", file=sys.stderr)
        except OSError:
            fault = True
    if not usage:
        children = [Child(path) for path in paths]
        current = None
        try:
            for current in children:
                if cancelled:
                    break
                current.stdout = tempfile.TemporaryFile()
                current.stderr = tempfile.TemporaryFile()
                current.started = time.monotonic()
                current.process = subprocess.Popen(
                    ["rm", "-rf", "--", current.path], stdin=subprocess.DEVNULL,
                    stdout=current.stdout, stderr=current.stderr)
                current.pgid = os.getpgid(current.process.pid)
                if current.pgid != os.getpgrp():
                    raise RuntimeError("pgid mismatch")
            current = None
            while True:
                live = _live(children)
                if any(c.error for c in children):
                    raise RuntimeError("child polling failed")
                expired = [c for c in live if time.monotonic() - c.started >= timeout]
                if expired and not cancelled:
                    for child in expired:
                        child.cancelled = True
                    cancel(expired, signal.SIGTERM, interrupted=lambda: cancelled)
                if cancelled:
                    cancel(children, cancelled)
                    break
                if not live:
                    break
                if not expired:
                    time.sleep(POLL_SECONDS)
        except Exception as exc:
            fault = True
            if current is not None:
                current.error = str(exc)
            cancel(children, cancelled or signal.SIGTERM)
        try:
            # All children have been reaped, or explicitly marked unknown above.
            results = [classify(c) for c in children]
            if any(r["status"] == "unknown" for r in results):
                cancel(children, cancelled or signal.SIGTERM)
            for child in children:
                if child.stderr is not None:
                    child.stderr.seek(0)
                    diagnostic = child.stderr.read(4096)
                    if diagnostic:
                        print(f"{child.path!r}: {diagnostic.decode('utf-8', 'replace')}",
                              file=sys.stderr)
                for stream in (child.stdout, child.stderr):
                    if stream is not None:
                        stream.close()
            for sig in (signal.SIGTERM, signal.SIGINT,
                        signal.SIGHUP):
                signal.signal(sig, signal.SIG_DFL)
            summary = summarize(results, len(paths), cancelled, fault)
            for result in [*results, summary]:
                print(json.dumps(result, ensure_ascii=True))
            sys.stdout.flush()
        except Exception:
            fault = True
            cancel(children, cancelled or signal.SIGTERM)
        finally:
            for child in children:
                for stream in (child.stdout, child.stderr):
                    if stream is not None:
                        try:
                            stream.close()
                        except Exception:
                            fault = True
                            cancel(children, cancelled or signal.SIGTERM)
    # The only CLI return site, including output failures and late cancellation.
    return (64 if usage else summarize(results, len(children), cancelled, fault)["rc"])


if __name__ == "__main__":
    sys.exit(main())
