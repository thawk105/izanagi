# probe 逐語 — t1157_probe.py

実体は repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/wave-t1157-fetchcontent-reuse/`)。
実装面の `.py` を repo へ入れない規約に従い逐語で貼る。
著者 = Codex `role=author` (段 5 + 段 6 fix 第 1〜4 巡)。schema `v4`。

権威走行 = `Request 912911.nqsv` / `bnode009` / 2026-08-16 09:43-09:45 JST / `verdict=REUSED`。

```python
#!/usr/bin/env python3.10
"""T-1157: measure reuse of one production FetchContent base in one PBS job."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any, Iterator, Mapping, Optional, Sequence


SCHEMA = "izanagi-t1157-fetchcontent-reuse-probe/v4"
CONFIGURE_TIMEOUT_S = 300
TARGET_TIMEOUT_S = 420
FETCH_TIMEOUT_S = 300
SHORT_TIMEOUT_S = 30
CALL_TIMEOUT_S = 780
OUTER_CAP_S = 4800
FINAL_RESERVE_S = 90
SNAPSHOT_CAP_S = SHORT_TIMEOUT_S * 4
CHECKOUT_CAP_S = SHORT_TIMEOUT_S * 2
SINGLE_TENANT_SAMPLE_COUNT = 4
SINGLE_TENANT_SAMPLE_INTERVAL_S = 10
SINGLE_TENANT_EXTRA_CAP_S = (
    (SINGLE_TENANT_SAMPLE_COUNT - 1)
    * (SINGLE_TENANT_SAMPLE_INTERVAL_S + SHORT_TIMEOUT_S * 2)
)
DEPENDENCY_STAGE_TIMEOUTS_S = {"gflags": 60, "glog": 120}
DEPENDENCY_BUILD_JOBS = 48
DEPENDENCY_PROVISIONING_CAP_S = (
    sum(DEPENDENCY_STAGE_TIMEOUTS_S.values()) * 3
    + SHORT_TIMEOUT_S * 6
)
LEG_CAPS_S = {
    "leg0": SHORT_TIMEOUT_S * 15 + SINGLE_TENANT_EXTRA_CAP_S,
    "leg1": SHORT_TIMEOUT_S,
    "dependency_provisioning": DEPENDENCY_PROVISIONING_CAP_S,
    "leg2": CHECKOUT_CAP_S + CALL_TIMEOUT_S + SNAPSHOT_CAP_S,
    "leg3": (
        CHECKOUT_CAP_S + CONFIGURE_TIMEOUT_S
        + TARGET_TIMEOUT_S + SNAPSHOT_CAP_S * 2
    ),
    "leg4": (
        CHECKOUT_CAP_S + CONFIGURE_TIMEOUT_S
        + TARGET_TIMEOUT_S + SNAPSHOT_CAP_S
    ),
    "leg3_diagnostic": TARGET_TIMEOUT_S + SNAPSHOT_CAP_S,
    "leg5_clone_positive_control": (
        SHORT_TIMEOUT_S + CHECKOUT_CAP_S + CALL_TIMEOUT_S
        + CONFIGURE_TIMEOUT_S + SNAPSHOT_CAP_S * 2
    ),
    "leg6_update_checkout_positive_control": (
        CHECKOUT_CAP_S + CALL_TIMEOUT_S + SHORT_TIMEOUT_S * 4
        + CONFIGURE_TIMEOUT_S + SNAPSHOT_CAP_S * 2
    ),
    "leg7_fetch_detector_positive_control": (
        FETCH_TIMEOUT_S + SNAPSHOT_CAP_S * 2
    ),
}
MAX_CAPTURE_CHARS = 16_000
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
HEAD_RE = re.compile(r"[0-9a-f]{40}\Z")
POPULATE_STAMP_VERDICT_FIELDS = ("exists", "st_ino", "sha256")
POPULATE_STAMP_DIAGNOSTIC_FIELDS = ("path", "st_mtime_ns")


class ProbeError(RuntimeError):
    pass


class CallTimeout(ProbeError):
    pass


class BudgetExhausted(ProbeError):
    pass


class SignalCaught(BaseException):
    def __init__(self, signum: int):
        super().__init__(f"caught signal {signum}")
        self.signum = signum


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def tail_text(value: str, limit: int = MAX_CAPTURE_CHARS) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[-limit:], True


def command_record(
    argv: Sequence[str], *, timeout_s: int, cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None, raw_output: bool = False,
) -> dict[str, Any]:
    started = time.monotonic()
    record: dict[str, Any] = {
        "argv": list(argv),
        "cwd": str(cwd) if cwd is not None else None,
        "timeout_s": timeout_s,
        "rc": None,
        "elapsed_s": None,
        "timed_out": False,
    }
    try:
        completed = subprocess.run(
            list(argv), cwd=str(cwd) if cwd is not None else None,
            env=dict(env) if env is not None else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout_s, check=False,
        )
        record["rc"] = completed.returncode
        if raw_output:
            record["stdout"] = completed.stdout
            record["stderr"] = completed.stderr
        else:
            stdout, stdout_truncated = tail_text(completed.stdout)
            stderr, stderr_truncated = tail_text(completed.stderr)
            record.update({
                "stdout_tail": stdout,
                "stdout_truncated": stdout_truncated,
                "stderr_tail": stderr,
                "stderr_truncated": stderr_truncated,
            })
    except subprocess.TimeoutExpired as exc:
        record["timed_out"] = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        if raw_output:
            record["stdout"] = stdout
            record["stderr"] = stderr
        else:
            record["stdout_tail"] = tail_text(stdout)[0]
            record["stderr_tail"] = tail_text(stderr)[0]
    except OSError as exc:
        record["launch_error"] = f"{type(exc).__name__}: {exc}"
    finally:
        record["elapsed_s"] = time.monotonic() - started
    return record


def require_command(record: Mapping[str, Any], label: str) -> str:
    if record.get("rc") != 0:
        raise ProbeError(
            f"{label} failed: rc={record.get('rc')} "
            f"timeout={record.get('timed_out')}"
        )
    return str(record.get("stdout", record.get("stdout_tail", ""))).strip()


@contextlib.contextmanager
def bounded_call(seconds: int, label: str) -> Iterator[None]:
    def handler(_signum: int, _frame: Any) -> None:
        raise CallTimeout(f"{label} exceeded {seconds}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, float(seconds))
    signal.signal(signal.SIGALRM, handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


@contextlib.contextmanager
def production_checkout(
    patchharness: Any, pin: str, ccbench_root: Path,
    cleanup_errors: list[dict[str, str]], label: str,
) -> Iterator[Path]:
    manager = patchharness.checkout(pin, base_dir=str(ccbench_root))
    entered = False
    sub: Optional[str] = None
    try:
        with bounded_call(SHORT_TIMEOUT_S, f"{label}:checkout-enter"):
            sub = manager.__enter__()
            entered = True
        yield Path(sub).resolve(strict=True)
    finally:
        if entered:
            try:
                with bounded_call(SHORT_TIMEOUT_S, f"{label}:checkout-exit"):
                    manager.__exit__(*sys.exc_info())
            except BaseException as exc:
                cleanup_errors.append({
                    "label": label,
                    "error": f"{type(exc).__name__}: {exc}",
                })
                raise


@contextlib.contextmanager
def observe_production_run(buildcache: Any, events: list[dict[str, Any]]) -> Iterator[None]:
    """Forward to the real _run while recording its exact argv and duration."""
    original = buildcache._run

    def observed(
        cmd: list[str], what: str, timeout_s: Optional[int] = None,
        *, site: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        event: dict[str, Any] = {
            "argv": list(cmd),
            "production_what": what,
            "stage": "target" if what == "build" else what,
            "timeout_s": timeout_s,
            "site": site,
            "rc": None,
            "elapsed_s": None,
            "timed_out": False,
        }
        started = time.monotonic()
        try:
            original(cmd, what, timeout_s=timeout_s, site=site, env=env)
            event["rc"] = 0
        except subprocess.TimeoutExpired:
            event["timed_out"] = True
            raise
        except BaseException as exc:
            match = re.search(r"\brc=(-?[0-9]+)", str(exc))
            if match is not None:
                event["rc"] = int(match.group(1))
            event["exception"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            event["elapsed_s"] = time.monotonic() - started
            events.append(event)

    buildcache._run = observed
    try:
        yield
    finally:
        buildcache._run = original


def run_prepare(
    buildcache: Any, *, ccbench_dir: Path, base: Path,
    expected_manifest: Mapping[str, object], label: str,
    record: dict[str, Any],
) -> Any:
    events: list[dict[str, Any]] = []
    record.update({
        "production_seam": "buildcache.prepare_masstree_fetchcontent",
        "arguments": {
            "ccbench_dir": str(ccbench_dir),
            "fetchcontent_base_dir": str(base),
            "configure_timeout_s": CONFIGURE_TIMEOUT_S,
            "target_timeout_s": TARGET_TIMEOUT_S,
            "site": None,
            "dependency_prefix": "",
        },
        "elapsed_s": None,
        "events": events,
    })
    started = time.monotonic()
    try:
        with observe_production_run(buildcache, events):
            with bounded_call(CALL_TIMEOUT_S, label):
                prepared = buildcache.prepare_masstree_fetchcontent(
                    ccbench_dir=str(ccbench_dir),
                    fetchcontent_base_dir=str(base),
                    expected_toolchain_manifest=expected_manifest,
                    configure_timeout_s=CONFIGURE_TIMEOUT_S,
                    target_timeout_s=TARGET_TIMEOUT_S,
                    site=None,
                    dependency_prefix="",
                )
        record["returned"] = {
            "fetchcontent_base_dir": prepared.fetchcontent_base_dir,
            "build_dir": prepared.build_dir,
            "configure_argv": list(prepared.configure_argv),
            "build_argv": list(prepared.build_argv),
        }
        record["rc"] = 0
        return prepared
    except BaseException as exc:
        record["rc"] = None
        record["exception"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record["elapsed_s"] = time.monotonic() - started


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def masstree_pin_from_third_party(path: Path) -> tuple[str, dict[str, Any]]:
    observation = file_observation(path)
    if observation.get("observed") is not True:
        raise ProbeError(
            f"cannot observe masstree pin source: {observation.get('error')}"
        )
    if observation.get("exists") is not True:
        raise ProbeError("masstree pin source does not exist")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProbeError(f"cannot read masstree pin source: {exc}") from exc
    matches = re.findall(
        r'^\s*set\(CCBENCH_MASSTREE_TAG\s+"?([0-9a-f]{40})"?\s*\)\s*(?:#.*)?$',
        text,
        flags=re.MULTILINE,
    )
    if len(matches) != 1:
        raise ProbeError(
            f"expected exactly one full-SHA CCBENCH_MASSTREE_TAG, found {len(matches)}"
        )
    return matches[0], {
        "source": observation,
        "matched_values": matches,
        "is_full_sha": HEAD_RE.fullmatch(matches[0]) is not None,
    }


def file_observation(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "path": str(path), "observed": False, "error": None,
        "exists": None, "sha256": None,
    }
    try:
        info = path.lstat()
    except FileNotFoundError:
        out.update({"observed": True, "exists": False})
        return out
    except OSError as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    out.update({
        "observed": True,
        "exists": True,
        "st_ino": info.st_ino,
        "st_size": info.st_size,
        "st_mtime_ns": info.st_mtime_ns,
        "st_ctime_ns": info.st_ctime_ns,
        "mode": stat.S_IFMT(info.st_mode),
    })
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        out["observed"] = False
        out["error"] = "not a non-symlink regular file"
        return out
    try:
        out["sha256"] = sha256_file(path)
    except OSError as exc:
        out["observed"] = False
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def directory_observation(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "path": str(path), "observed": False, "error": None, "exists": None,
    }
    try:
        info = path.lstat()
    except FileNotFoundError:
        out.update({"observed": True, "exists": False})
        return out
    except OSError as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    out.update({
        "observed": True,
        "exists": True,
        "st_dev": info.st_dev,
        "st_ino": info.st_ino,
        "st_mtime_ns": info.st_mtime_ns,
        "st_ctime_ns": info.st_ctime_ns,
        "is_directory": stat.S_ISDIR(info.st_mode),
        "is_symlink": stat.S_ISLNK(info.st_mode),
    })
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        out["observed"] = False
        out["error"] = "not a non-symlink directory"
    return out


def selected_signature(
    observation: dict[str, Any], fields: Sequence[str],
) -> None:
    if observation.get("observed") is not True:
        observation["verdict_signature"] = None
        return
    observation["verdict_signature"] = {
        field: observation.get(field) for field in fields
    }


def command_output_observation(
    record: Mapping[str, Any], *, expected_head: bool = False,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "observed": False, "error": None, "output_sha256": None,
        "line_count": None, "output": None,
    }
    if record.get("rc") != 0:
        out["error"] = (
            f"command failed: rc={record.get('rc')} "
            f"timeout={record.get('timed_out')}"
        )
        return out
    output = str(record.get("stdout", "")).strip()
    if expected_head and HEAD_RE.fullmatch(output) is None:
        out["error"] = f"unexpected HEAD output: {output!r}"
        return out
    out.update({
        "observed": True,
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "line_count": len(output.splitlines()) if output else 0,
        "output": output,
    })
    return out


def stamp_candidates(base: Path, pattern: str) -> tuple[list[Path], Optional[str]]:
    subbuild = base / "masstree-subbuild"
    subbuild_observation = directory_observation(subbuild)
    if subbuild_observation.get("observed") is not True:
        return [], str(subbuild_observation.get("error"))
    if subbuild_observation.get("exists") is not True:
        return [], None
    try:
        return sorted(subbuild.glob(f"**/{pattern}"), key=str), None
    except OSError as exc:
        return [], f"{type(exc).__name__}: {exc}"


def observe_stamp_role(
    base: Path, requested: Path, pattern: str, *, require_one: bool,
) -> dict[str, Any]:
    direct: list[Path] = []
    error: Optional[str] = None
    requested_observation = directory_observation(requested)
    if requested_observation.get("observed") is not True:
        error = str(requested_observation.get("error"))
    try:
        if error is None and requested_observation.get("exists") is True:
            direct = sorted(requested.glob(pattern), key=str)
    except OSError as exc:
        error = f"{type(exc).__name__}: {exc}"
    candidates = direct
    resolution = "fixed"
    if error is None and ((require_one and len(candidates) != 1) or not candidates):
        candidates, error = stamp_candidates(base, pattern)
        resolution = "glob-fallback"
    out: dict[str, Any] = {
        "observed": False,
        "error": error,
        "pattern": pattern,
        "resolution": resolution,
        "paths": [str(path) for path in candidates],
        "files": [],
        "exists": None,
        "verdict_signature": None,
        "diagnostic_signature": None,
    }
    if error is not None:
        return out
    if require_one and len(candidates) != 1:
        out["error"] = f"expected exactly one {pattern}, found {len(candidates)}"
        return out
    observations = [file_observation(path) for path in candidates]
    out["files"] = observations
    if any(item.get("observed") is not True for item in observations):
        out["error"] = "one or more matched stamp files were unobservable"
        return out
    out.update({
        "observed": True,
        "exists": bool(candidates),
        "verdict_signature": [
            {
                key: item.get(key)
                for key in POPULATE_STAMP_VERDICT_FIELDS
            }
            for item in observations
        ],
        "diagnostic_signature": [
            {
                key: item.get(key)
                for key in POPULATE_STAMP_DIAGNOSTIC_FIELDS
            }
            for item in observations
        ],
    })
    return out


def observe_stamps(base: Path) -> dict[str, Any]:
    requested = (
        base / "masstree-subbuild" / "masstree-populate-prefix" / "src"
        / "masstree-populate-stamp"
    )
    requested_observation = directory_observation(requested)
    fixed = (
        requested_observation.get("observed") is True
        and requested_observation.get("exists") is True
    )
    result: dict[str, Any] = {
        "observed": False,
        "error": None,
        "requested_path": str(requested),
        "requested_observation": requested_observation,
        "resolution": "fixed" if fixed else "glob-fallback",
        "resolved_path": str(requested) if fixed else None,
        "entries": [],
        "glob_candidates": {},
        "required": {},
        "populate_steps": {},
    }
    if fixed:
        try:
            for entry in sorted(requested.iterdir(), key=lambda path: path.name):
                observed = file_observation(entry)
                observed["name"] = entry.name
                result["entries"].append(observed)
        except OSError as exc:
            result["enumeration_error"] = f"{type(exc).__name__}: {exc}"
    elif requested_observation.get("observed") is not True:
        result["enumeration_error"] = requested_observation.get("error")

    required_patterns = {
        "gitclone_lastrun": "*-gitclone-lastrun.txt",
        "gitinfo": "*-gitinfo.txt",
    }
    for role, pattern in required_patterns.items():
        observed = observe_stamp_role(base, requested, pattern, require_one=True)
        if observed["resolution"] == "glob-fallback":
            result["glob_candidates"][role] = observed["paths"]
        if observed.get("observed") is True:
            item = dict(observed["files"][0])
            selected_signature(item, POPULATE_STAMP_VERDICT_FIELDS)
            result["required"][role] = item
        else:
            result["required"][role] = observed
    for role in ("download", "update", "patch"):
        result["populate_steps"][role] = observe_stamp_role(
            base, requested, f"*-{role}", require_one=False,
        )
    children = [
        *result["required"].values(),
        *result["populate_steps"].values(),
    ]
    child_errors = [
        str(item.get("error"))
        for item in children if item.get("observed") is not True
    ]
    if result.get("enumeration_error") is not None:
        child_errors.insert(0, str(result["enumeration_error"]))
    if child_errors:
        result["error"] = "; ".join(child_errors)
    else:
        result["observed"] = True
    return result


def take_snapshot(
    label: str, base: Path, git_path: str, expected_pin: str,
) -> dict[str, Any]:
    src = base / "masstree-src"
    src_observation = directory_observation(src)
    selected_signature(src_observation, ("exists", "st_dev", "st_ino"))
    config_observation = file_observation(src / "config.h")
    selected_signature(config_observation, ("exists", "st_ino", "sha256"))
    archive_observation = file_observation(src / "libkohler_masstree_json.a")
    selected_signature(archive_observation, ("exists", "st_ino", "sha256"))
    snapshot: dict[str, Any] = {
        "label": label,
        "taken_at": utc_now(),
        "base": str(base),
        "src_dir": src_observation,
        "config_h": config_observation,
        "archive": archive_observation,
        "porcelain_lines": None,
        "stamp_dir": observe_stamps(base),
        "git_state": {},
        "commands": {},
    }
    head = command_record(
        [git_path, "-C", str(src), "rev-parse", "HEAD"],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    snapshot["commands"]["head"] = head
    snapshot["git_state"]["head"] = command_output_observation(
        head, expected_head=True,
    )
    head_sha = snapshot["git_state"]["head"].get("output")
    snapshot["head_sha"] = head_sha
    snapshot["expected_pin"] = expected_pin
    snapshot["head_matches_pin"] = (
        head_sha == expected_pin
        if snapshot["git_state"]["head"].get("observed") is True
        else None
    )
    refs = command_record(
        [git_path, "-C", str(src), "for-each-ref",
         "--format=%(refname) %(objectname)"],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    snapshot["commands"]["refs"] = refs
    snapshot["git_state"]["refs"] = command_output_observation(refs)
    git_dir_record = command_record(
        [git_path, "-C", str(src), "rev-parse", "--absolute-git-dir"],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    snapshot["commands"]["git_dir"] = git_dir_record
    git_dir_output = command_output_observation(git_dir_record)
    snapshot["git_state"]["git_dir_command"] = git_dir_output
    if git_dir_output.get("observed") is True:
        git_dir = Path(str(git_dir_output["output"]))
        git_dir_observation = directory_observation(git_dir)
        snapshot["git_state"]["git_dir"] = git_dir_observation
        fetch_head = file_observation(git_dir / "FETCH_HEAD")
        selected_signature(fetch_head, ("exists", "st_mtime_ns", "sha256"))
        snapshot["git_state"]["fetch_head"] = fetch_head
        packed_refs = file_observation(git_dir / "packed-refs")
        selected_signature(packed_refs, ("exists", "sha256"))
        snapshot["git_state"]["packed_refs"] = packed_refs
    else:
        error = str(git_dir_output.get("error"))
        for role in ("git_dir", "fetch_head", "packed_refs"):
            snapshot["git_state"][role] = {
                "observed": False, "error": error, "exists": None,
                "verdict_signature": None,
            }
    porcelain = command_record(
        [git_path, "-C", str(src), "status", "--porcelain", "-uall"],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    snapshot["commands"]["porcelain"] = porcelain
    if porcelain.get("rc") == 0:
        snapshot["porcelain_lines"] = len(
            str(porcelain.get("stdout", "")).splitlines()
        )
    else:
        snapshot["porcelain_error"] = "git status failed"
    return snapshot


def get_path(value: Mapping[str, Any], dotted: str) -> tuple[bool, Any]:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    if current is None:
        return False, None
    return True, current


def get_observed_path(
    value: Mapping[str, Any], dotted: str,
) -> tuple[str, Any]:
    current: Any = value
    for part in dotted.split("."):
        if isinstance(current, Mapping) and current.get("observed") is False:
            return "unobservable", None
        if not isinstance(current, Mapping) or part not in current:
            return "unavailable", None
        current = current[part]
    if current is None:
        return "unavailable", None
    return "comparable", current


SIGNATURE_FIELDS = (
    "src_dir.verdict_signature",
    "config_h.verdict_signature",
    "archive.verdict_signature",
    "stamp_dir.required.gitclone_lastrun.verdict_signature",
    "stamp_dir.required.gitinfo.verdict_signature",
    "git_state.fetch_head.verdict_signature",
    "git_state.packed_refs.verdict_signature",
    "git_state.head.output_sha256",
    "git_state.refs.output_sha256",
    "stamp_dir.populate_steps.download.verdict_signature",
    "stamp_dir.populate_steps.update.verdict_signature",
    "stamp_dir.populate_steps.patch.verdict_signature",
)

OBSERVATION_FIELDS = SIGNATURE_FIELDS + (
    "src_dir.st_mtime_ns",
    "src_dir.st_ctime_ns",
    "config_h.st_size",
    "config_h.st_mtime_ns",
    "archive.st_size",
    "archive.st_mtime_ns",
    "stamp_dir.resolved_path",
    "stamp_dir.required.gitclone_lastrun.st_mtime_ns",
    "stamp_dir.required.gitinfo.st_mtime_ns",
    "stamp_dir.populate_steps.download.diagnostic_signature",
    "stamp_dir.populate_steps.update.diagnostic_signature",
    "stamp_dir.populate_steps.patch.diagnostic_signature",
)

REPLACED_FIELDS = {
    "src_dir.verdict_signature",
    "config_h.verdict_signature",
    "archive.verdict_signature",
}

REFETCHED_FIELDS = {
    "stamp_dir.required.gitclone_lastrun.verdict_signature",
    "git_state.fetch_head.verdict_signature",
    "git_state.packed_refs.verdict_signature",
    "git_state.head.output_sha256",
    "git_state.refs.output_sha256",
    "stamp_dir.populate_steps.download.verdict_signature",
    "stamp_dir.populate_steps.update.verdict_signature",
    "stamp_dir.populate_steps.patch.verdict_signature",
}


def transition(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    changed: list[str] = []
    comparable: list[str] = []
    unavailable: list[str] = []
    unobservable: list[str] = []
    for field in OBSERVATION_FIELDS:
        before_state, before_value = get_observed_path(before, field)
        after_state, after_value = get_observed_path(after, field)
        if "unobservable" in {before_state, after_state}:
            unobservable.append(field)
            continue
        if "unavailable" in {before_state, after_state}:
            unavailable.append(field)
            continue
        comparable.append(field)
        if before_value != after_value:
            changed.append(field)
    signature_unavailable = [field for field in SIGNATURE_FIELDS if field in unavailable]
    signature_unobservable = [field for field in SIGNATURE_FIELDS if field in unobservable]
    signature_changed = [field for field in SIGNATURE_FIELDS if field in changed]
    return {
        "from": before.get("label"),
        "to": after.get("label"),
        "changed_fields": changed,
        "comparable_fields": comparable,
        "unavailable_fields": unavailable,
        "unobservable_fields": unobservable,
        "signature_changed_fields": signature_changed,
        "signature_unavailable_fields": signature_unavailable,
        "signature_unobservable_fields": signature_unobservable,
        "signature_equal": (
            not signature_changed
            and not signature_unavailable
            and not signature_unobservable
        ),
    }


def compute_verdict(
    transitions: Sequence[Mapping[str, Any]], positive_control_fired: bool,
    *, refetch_detection_proven: bool, single_tenant_observed: bool,
    forced_reasons: Sequence[str] = (),
) -> tuple[str, list[str]]:
    inconclusive_reasons = list(forced_reasons)
    if not positive_control_fired:
        inconclusive_reasons.append("clone positive control did not fire")
    if not refetch_detection_proven:
        inconclusive_reasons.append("fetch detector positive control did not fire")
    if not single_tenant_observed:
        inconclusive_reasons.append("single_tenant_observed=false")
    if any(item.get("signature_unobservable_fields") for item in transitions):
        inconclusive_reasons.append(
            "one or more required signature fields were unobservable"
        )
    if any(item.get("signature_unavailable_fields") for item in transitions):
        inconclusive_reasons.append(
            "one or more required signature fields were unavailable"
        )
    if inconclusive_reasons:
        return "INCONCLUSIVE", inconclusive_reasons
    changed = {
        field
        for item in transitions
        for field in item.get("signature_changed_fields", [])
    }
    if changed & REFETCHED_FIELDS:
        return "REFETCHED", [
            "clone, update/fetch, ref, HEAD, or populate-step evidence changed"
        ]
    if changed & REPLACED_FIELDS:
        return "REPLACED", [
            "source inode or generated dependency artifact changed"
        ]
    if all(item.get("signature_equal") is True for item in transitions):
        return "REUSED", ["all three cold production signature transitions were equal"]
    return "INCONCLUSIVE", ["changes did not match a closed verdict predicate"]


def parse_ps_candidates(raw: str, self_pid: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_pid: dict[int, dict[str, Any]] = {}
    for line in raw.splitlines():
        parts = line.strip().split(None, 6)
        if len(parts) < 6:
            continue
        try:
            pid, ppid, uid = map(int, parts[:3])
            pcpu = float(parts[4])
        except ValueError:
            continue
        row = {
            "pid": pid, "ppid": ppid, "uid": uid, "stat": parts[3],
            "pcpu": pcpu, "comm": parts[5],
            "args": parts[6] if len(parts) > 6 else "",
        }
        rows.append(row)
        by_pid[pid] = row
    ancestry = {self_pid}
    current = self_pid
    while current in by_pid:
        parent = int(by_pid[current]["ppid"])
        if parent <= 0 or parent in ancestry:
            break
        ancestry.add(parent)
        current = parent
    compute_names = re.compile(
        r"^(python(?:3(?:\.10)?)?|cmake|make|gmake|ninja|gcc|g\+\+|cc|c\+\+|"
        r"cc1|cc1plus|ld|ycsb_.*|perf)$"
    )
    candidates = [
        row for row in rows
        if row["pid"] not in ancestry
        and row["comm"] not in {"ps", "timeout"}
        and (row["pcpu"] >= 1.0 or compute_names.fullmatch(row["comm"]) is not None)
    ]
    predicate = {
        "excluded_pids": sorted(ancestry),
        "candidate_rule": (
            "pid not in probe ancestry and comm not ps/timeout and "
            "(pcpu >= 1.0 or comm matches compute-name allowlist)"
        ),
    }
    return candidates, predicate


def observe_single_tenant() -> tuple[bool, dict[str, Any]]:
    cpu_count = os.cpu_count() or 1
    load_threshold = max(1.0, cpu_count * 0.05)
    sampling_started = time.monotonic()
    samples: list[dict[str, Any]] = []
    details: dict[str, Any] = {}
    for index in range(SINGLE_TENANT_SAMPLE_COUNT):
        if index:
            time.sleep(SINGLE_TENANT_SAMPLE_INTERVAL_S)
        load = command_record(
            ["/bin/cat", "/proc/loadavg"], timeout_s=SHORT_TIMEOUT_S,
            raw_output=True,
        )
        ps = command_record(
            ["/bin/ps", "-eo", "pid=,ppid=,uid=,stat=,pcpu=,comm=,args="],
            timeout_s=SHORT_TIMEOUT_S, raw_output=True,
        )
        sample: dict[str, Any] = {
            "index": index,
            "sampled_at": utc_now(),
            "elapsed_since_sampling_start_s": time.monotonic() - sampling_started,
            "loadavg_command": load,
            "process_command": ps,
            "observed": False,
            "error": None,
            "load1": None,
            "load_ok": False,
            "other_compute_processes": [],
            "other_compute_process_count": None,
            "process_predicate": None,
        }
        if load.get("rc") != 0 or ps.get("rc") != 0:
            sample["error"] = "both bounded observations must succeed"
            samples.append(sample)
            continue
        load_fields = str(load.get("stdout", "")).split()
        try:
            load1 = float(load_fields[0])
        except (IndexError, ValueError):
            sample["error"] = "loadavg first field must parse as float"
            samples.append(sample)
            continue
        candidates, process_predicate = parse_ps_candidates(
            str(ps.get("stdout", "")), os.getpid(),
        )
        sample.update({
            "observed": True,
            "load1": load1,
            "load_ok": load1 <= load_threshold,
            "other_compute_processes": candidates,
            "other_compute_process_count": len(candidates),
            "process_predicate": process_predicate,
        })
        samples.append(sample)

    last_sample = samples[-1]
    all_samples_observed = all(
        sample.get("observed") is True for sample in samples
    )
    all_process_samples_empty = all(
        sample.get("observed") is True
        and sample.get("other_compute_process_count") == 0
        for sample in samples
    )
    last_load_ok = (
        last_sample.get("observed") is True
        and last_sample.get("load_ok") is True
    )
    observed = all_samples_observed and last_load_ok and all_process_samples_empty
    details.update({
        "sampling": {
            "sample_count": SINGLE_TENANT_SAMPLE_COUNT,
            "sample_interval_s": SINGLE_TENANT_SAMPLE_INTERVAL_S,
            "target_span_s": (
                (SINGLE_TENANT_SAMPLE_COUNT - 1)
                * SINGLE_TENANT_SAMPLE_INTERVAL_S
            ),
            "elapsed_s": time.monotonic() - sampling_started,
        },
        "samples": samples,
        "cpu_count": cpu_count,
        "load_threshold": load_threshold,
        "last_sample_index": last_sample["index"],
        "loadavg_command": last_sample["loadavg_command"],
        "process_command": last_sample["process_command"],
        "load1": last_sample["load1"],
        "other_compute_processes": last_sample["other_compute_processes"],
        "process_predicate": last_sample["process_predicate"],
        "predicate": (
            "all samples must be observable, the last sample load1 must be "
            "<= max(1.0, os.cpu_count()*0.05), and other_compute_processes "
            "must be empty in every sample"
        ),
        "predicate_values": {
            "all_samples_observed": all_samples_observed,
            "last_sample_load_ok": last_load_ok,
            "all_process_samples_empty": all_process_samples_empty,
            "other_compute_process_counts": [
                sample["other_compute_process_count"] for sample in samples
            ],
        },
    })
    return observed, details


def resolve_tool(name: str) -> tuple[str, dict[str, Any]]:
    which = command_record(
        ["/bin/bash", "-c", 'command -v -- "$1"', "t1157", name],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    found = require_command(which, f"command -v {name}")
    real = command_record(
        ["/usr/bin/realpath", "-e", "--", found],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    resolved = require_command(real, f"realpath -e {name}")
    path = Path(resolved)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ProbeError(f"tool is not an executable regular file: {resolved}")
    return resolved, {"requested": name, "command_v": which, "realpath_e": real}


def tool_manifest_entry(name: str) -> tuple[dict[str, str], dict[str, Any]]:
    realpath, observation = resolve_tool(name)
    version = command_record(
        [realpath, "--version"], timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    if version.get("rc") != 0:
        raise ProbeError(f"{name} --version failed")
    stdout = str(version.get("stdout", ""))
    stderr = str(version.get("stderr", ""))
    lines = stdout.splitlines()
    full = (stdout + stderr).strip()
    if not lines or not lines[0].strip() or not full:
        raise ProbeError(f"{name} --version produced no usable version")
    observation["version"] = version
    return {
        "requested": name,
        "realpath": realpath,
        "version_first_line": lines[0],
        "version": full,
    }, observation


def dependency_policy(
    repo_root: Path, record: dict[str, Any],
) -> dict[str, dict[str, str]]:
    policy_path = repo_root / "tools" / "pegasus" / "policy.json"
    policy_record: dict[str, Any] = {
        "path": str(policy_path),
        "observation": file_observation(policy_path),
        "required_fields": {},
    }
    record["policy"] = policy_record
    if policy_record["observation"].get("observed") is not True:
        raise ProbeError("dependency policy is not an observable regular file")
    try:
        document = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        policy_record["error"] = f"{type(exc).__name__}: {exc}"
        raise ProbeError(f"cannot read dependency policy: {exc}") from exc
    if not isinstance(document, dict):
        policy_record["error"] = "top-level value is not an object"
        raise ProbeError("dependency policy top-level value is not an object")

    specifications: dict[str, dict[str, str]] = {}
    for name in ("gflags", "glog"):
        source_key = f"{name}_source_path"
        head_key = f"{name}_expected_head"
        source_path = document.get(source_key)
        expected_head = document.get(head_key)
        policy_record["required_fields"][source_key] = source_path
        policy_record["required_fields"][head_key] = expected_head
        if (
            type(source_path) is not str or not source_path
            or "\n" in source_path
        ):
            raise ProbeError(f"invalid dependency policy field: {source_key}")
        if (
            type(expected_head) is not str
            or HEAD_RE.fullmatch(expected_head) is None
        ):
            raise ProbeError(f"invalid dependency policy field: {head_key}")
        specifications[name] = {
            "source_path": source_path,
            "expected_head": expected_head,
        }
    return specifications


def _compact_raw_command_output(record: dict[str, Any]) -> tuple[str, str]:
    stdout = str(record.pop("stdout", ""))
    stderr = str(record.pop("stderr", ""))
    stdout_tail, stdout_truncated = tail_text(stdout)
    stderr_tail, stderr_truncated = tail_text(stderr)
    record.update({
        "stdout_tail": stdout_tail,
        "stdout_truncated": stdout_truncated,
        "stderr_tail": stderr_tail,
        "stderr_truncated": stderr_truncated,
    })
    return stdout, stderr


def validate_dependency_source(
    git_path: str, name: str, specification: Mapping[str, str],
    record: dict[str, Any],
) -> list[str]:
    source_path = specification["source_path"]
    expected_head = specification["expected_head"]
    source = Path(source_path)
    record.update({
        "source_path": source_path,
        "expected_head": expected_head,
        "source_path_exists": source.exists(),
        "source_path_is_directory": source.is_dir(),
        "observed_head": None,
        "head_matches_expected": False,
        "status_porcelain_line_count": None,
        "status_clean": False,
        "validation_errors": [],
    })
    errors: list[str] = record["validation_errors"]
    if not source.is_dir():
        errors.append(f"{name} source path is missing or not a directory")
        return errors

    head_command = command_record(
        [git_path, "-C", source_path, "rev-parse", "HEAD"],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    record["head_command"] = head_command
    head_stdout, _head_stderr = _compact_raw_command_output(head_command)
    observed_head = head_stdout.strip()
    if head_command.get("rc") != 0:
        errors.append(f"{name} source HEAD command failed")
    elif HEAD_RE.fullmatch(observed_head) is None:
        errors.append(f"{name} source HEAD is not a full lowercase SHA-1")
    else:
        record["observed_head"] = observed_head
        record["head_matches_expected"] = observed_head == expected_head
        if observed_head != expected_head:
            errors.append(f"{name} source HEAD does not match policy")

    status_command = command_record(
        [
            git_path, "-C", source_path, "status", "--porcelain",
            "--untracked-files=all",
        ],
        timeout_s=SHORT_TIMEOUT_S, raw_output=True,
    )
    record["status_command"] = status_command
    status_stdout, _status_stderr = _compact_raw_command_output(status_command)
    if status_command.get("rc") != 0:
        errors.append(f"{name} source status command failed")
    else:
        status_lines = status_stdout.splitlines()
        record["status_porcelain_line_count"] = len(status_lines)
        record["status_clean"] = not status_lines
        record["status_porcelain_sha256"] = hashlib.sha256(
            status_stdout.encode("utf-8")
        ).hexdigest()
        if status_lines:
            errors.append(f"{name} source working tree is dirty")
    return errors


def provision_dependencies(
    *, repo_root: Path, scratch: Path, git_path: str,
    identity_manifest: Mapping[str, Mapping[str, str]],
    record: dict[str, Any],
) -> str:
    record.update({
        "completed": False,
        "source": {
            "kind": "mirrors-production-job-script",
            "path": "tools/pegasus/floor_campaign.sh",
            "policy_field_lines": "315-318",
            "provisioning_lines": "781-923",
            "detail": (
                "This dependency provisioning mirrors the production floor job "
                "script and is not a probe-specific build variation."
            ),
        },
        "dependencies": {},
        "cmake_prefix_path": {
            "previously_set": "CMAKE_PREFIX_PATH" in os.environ,
            "previous_value": os.environ.get("CMAKE_PREFIX_PATH"),
            "effective_value": None,
            "overwritten": False,
        },
    })
    specifications = dependency_policy(repo_root, record)
    cmake_path = identity_manifest["cmake"]["realpath"]
    cc_path = identity_manifest["cc"]["realpath"]
    cxx_path = identity_manifest["cxx"]["realpath"]
    all_validation_errors: list[str] = []
    for name in ("gflags", "glog"):
        dependency_record: dict[str, Any] = {}
        record["dependencies"][name] = dependency_record
        all_validation_errors.extend(validate_dependency_source(
            git_path, name, specifications[name], dependency_record,
        ))
    record["source_validation_passed"] = not all_validation_errors
    if all_validation_errors:
        raise ProbeError(
            "dependency source validation failed: "
            + "; ".join(all_validation_errors)
        )

    install_dirs: dict[str, Path] = {}
    for name in ("gflags", "glog"):
        dependency_record = record["dependencies"][name]
        source_path = specifications[name]["source_path"]
        build_dir = scratch / f"{name}-build"
        install_dir = scratch / f"{name}-install"
        dependency_record.update({
            "build_dir": str(build_dir),
            "install_dir": str(install_dir),
        })
        try:
            build_dir.mkdir(mode=0o700)
        except OSError as exc:
            dependency_record["build_dir_error"] = f"{type(exc).__name__}: {exc}"
            raise ProbeError(f"cannot create {name} build directory: {exc}") from exc

        configure_argv = [
            cmake_path, "-S", source_path, "-B", str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        ]
        if name == "gflags":
            configure_argv.append("-DREGISTER_INSTALL_PREFIX=OFF")
        else:
            configure_argv.extend([
                "-DWITH_GTEST=OFF", "-DBUILD_TESTING=OFF", "-DWITH_UNWIND=OFF",
                f"-DCMAKE_PREFIX_PATH={install_dirs['gflags']}",
            ])
        configure_argv.extend([
            f"-DCMAKE_INSTALL_PREFIX={install_dir}",
            f"-DCMAKE_C_COMPILER={cc_path}",
            f"-DCMAKE_CXX_COMPILER={cxx_path}",
        ])
        build_argv = [
            cmake_path, "--build", str(build_dir), "-j",
            str(DEPENDENCY_BUILD_JOBS),
        ]
        install_argv = [cmake_path, "--install", str(build_dir)]
        stage_timeout_s = DEPENDENCY_STAGE_TIMEOUTS_S[name]
        stage_commands = (
            ("configure", configure_argv),
            ("build", build_argv),
            ("install", install_argv),
        )
        for stage, stage_argv in stage_commands:
            dependency_record[stage] = {
                "argv": list(stage_argv),
                "cwd": None,
                "timeout_s": stage_timeout_s,
                "rc": None,
                "elapsed_s": None,
                "timed_out": False,
                "not_run": True,
                "not_run_reason": "an earlier dependency stage did not complete",
            }
        for stage, stage_argv in stage_commands:
            dependency_record[stage] = command_record(
                stage_argv, timeout_s=stage_timeout_s,
            )
            dependency_record[stage]["not_run"] = False
            require_command(
                dependency_record[stage], f"{name} dependency {stage}",
            )
        install_dirs[name] = install_dir

    effective_prefix = os.pathsep.join(
        str(install_dirs[name]) for name in ("gflags", "glog")
    )
    os.environ["CMAKE_PREFIX_PATH"] = effective_prefix
    record["cmake_prefix_path"].update({
        "effective_value": effective_prefix,
        "exported_value": effective_prefix,
        "overwritten": record["cmake_prefix_path"]["previously_set"],
    })
    record["completed"] = True
    return effective_prefix


def actual_sort_best_genome(repo_root: Path, Genome: Any) -> tuple[Any, dict[str, Any]]:
    freeze_path = repo_root / "output" / "s8b-freeze" / "holdout_freeze.json"
    provenance: dict[str, Any] = {"path": str(freeze_path), "fallback": False}
    try:
        document = json.loads(freeze_path.read_text(encoding="utf-8"))
        holdouts = document.get("holdouts")
        if not isinstance(holdouts, dict) or len(holdouts) != 2:
            raise ProbeError("freeze does not contain exactly two holdouts")
        found: list[dict[str, int]] = []
        holdout_genomes: dict[str, str] = {}
        for holdout_id, holdout in sorted(holdouts.items()):
            try:
                flags = holdout["variant_binding"]["entries"]["sort_best"]["flags"]
            except (KeyError, TypeError) as exc:
                raise ProbeError(f"{holdout_id}: sort_best flags missing") from exc
            if not isinstance(flags, dict) or not flags or not all(
                isinstance(key, str) and type(item) is int
                for key, item in flags.items()
            ):
                raise ProbeError(f"{holdout_id}: sort_best flags invalid")
            normalized = dict(flags)
            found.append(normalized)
            holdout_genomes[str(holdout_id)] = Genome("silo", normalized).canonical()
        unique = {
            json.dumps(item, sort_keys=True, separators=(",", ":")): item
            for item in found
        }
        provenance["matching_entries"] = len(found)
        provenance["unique_flag_sets"] = len(unique)
        provenance["holdout_genomes"] = holdout_genomes
        if len(unique) == 1:
            flags = next(iter(unique.values()))
            genome = Genome("silo", flags)
            provenance["canonical"] = genome.canonical()
            return genome, provenance
        raise ProbeError(f"sort_best flags were not unique: {len(unique)}")
    except BaseException as exc:
        flags = {
            "BACK_OFF": 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0,
        }
        genome = Genome("silo", flags)
        provenance.update({
            "fallback": True,
            "fallback_reason": f"{type(exc).__name__}: {exc}",
            "canonical": genome.canonical(),
        })
        return genome, provenance


def worktree_paths(git_path: str, ccbench_root: Path) -> tuple[Optional[list[str]], dict[str, Any]]:
    record = command_record(
        [git_path, "-C", str(ccbench_root), "worktree", "list", "--porcelain"],
        timeout_s=SHORT_TIMEOUT_S,
    )
    if record.get("rc") != 0:
        return None, record
    paths = [
        line[len("worktree "):]
        for line in str(record.get("stdout_tail", "")).splitlines()
        if line.startswith("worktree ")
    ]
    return sorted(os.path.realpath(path) for path in paths), record


def write_create_only(path: Path, payload: Mapping[str, Any]) -> None:
    if not path.is_absolute():
        raise ProbeError("--output must be absolute")
    encoded = (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2)
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        view = memoryview(encoded)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("create-only JSON write made no progress")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def budget_gate(
    result: dict[str, Any], leg: str, started: float,
) -> None:
    cap_s = LEG_CAPS_S[leg]
    elapsed_s = time.monotonic() - started
    remaining_s = OUTER_CAP_S - elapsed_s
    check = {
        "leg": leg,
        "checked_at_elapsed_s": elapsed_s,
        "remaining_s": remaining_s,
        "leg_cap_s": cap_s,
        "required_with_final_reserve_s": cap_s + FINAL_RESERVE_S,
        "admitted": remaining_s >= cap_s + FINAL_RESERVE_S,
    }
    result["budget"]["leg_checks"].append(check)
    if check["admitted"]:
        return
    result["legs"][leg] = {
        "skipped_for_budget": True,
        "budget_check": check,
    }
    result["budget"]["skipped_for_budget"].append(leg)
    raise BudgetExhausted(
        f"{leg}: remaining {remaining_s:.3f}s < "
        f"cap {cap_s}s + reserve {FINAL_RESERVE_S}s"
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    output = Path(args.output)
    started = time.monotonic()
    no_refetch_withheld_note = {
        "code": "no-refetch-claim-withheld",
        "basis": "fetch-detector-not-proven",
        "claim_status": "withheld",
        "detail": (
            "the no-refetch claim is withheld because detector capability "
            "was not proven"
        ),
        "fetch_detector_outcome": "not-run",
    }
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "job": {
            "pbs_jobid": os.environ.get("PBS_JOBID"),
            "pbs_o_workdir": os.environ.get("PBS_O_WORKDIR"),
            "started_at": utc_now(),
            "argv": sys.argv,
        },
        "host": {
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "uid": os.geteuid(),
            "cpu_count": os.cpu_count(),
        },
        "mocked": False,
        "deviations": [
            {
                "code": "minimal-expected-toolchain-manifest",
                "detail": (
                    "The full production _bind_current_toolchain path requires a verified "
                    "calibration receipt. The probe instead builds the exact minimal dict "
                    "accepted by buildcache._split_expected_toolchain_manifest, using "
                    "command -v then realpath -e and live --version output."
                ),
            },
            {
                "code": "direct-v2-argv-execution",
                "detail": (
                    "both cell configure/build pairs execute the exact argv returned by "
                    "buildcache._v2_commands directly, without build_or_reuse admission, "
                    "cache-hit, publication, or postflight layers."
                ),
            },
            {
                "code": "unmaterialized-sort-comparator",
                "detail": (
                    "The probe reads the real floor sort_best genome flags from the frozen "
                    "holdout document, but does not apply prepare_cell's comparator source "
                    "materialization to checkout #2. This does not change the FetchContent "
                    "base argv or the dependency target under observation."
                ),
            },
            {
                "code": "forwarding-run-observer",
                "detail": (
                    "During prepare_masstree_fetchcontent only, buildcache._run is wrapped "
                    "by a forwarding observer to record per-stage argv, rc, and elapsed. "
                    "The observer calls the original production _run and substitutes no result."
                ),
            },
            {
                "code": "positive-control-touch",
                "detail": (
                    "The positive control advances gitinfo.txt mtime without changing its "
                    "repository text; this exercises the same generated gitclone-script branch "
                    "but does not represent a real repository or pin change."
                ),
            },
        ],
        "scope_notes": [
            {
                "code": "cold-path-configure-count",
                "basis": "probe-construction",
                "cold_path": {
                    "prebuild_configures": 1,
                    "sort_best_cell_configures": 2,
                    "total_configures": 3,
                },
                "production_cache_hit_can_reduce_count": True,
            },
            {
                "code": "production-dependency-provisioning",
                "basis": "mirrored-production-job-script",
                "source": "tools/pegasus/floor_campaign.sh:781-923",
                "claim": (
                    "dependency provisioning mirrors the production job script "
                    "and is not a probe-specific build variation"
                ),
            },
            {
                "code": "cmake-update-fetch-required",
                "basis": "source-reading",
                "source": (
                    "/usr/share/cmake-3.22/Modules/"
                    "ExternalProject-gitupdate.cmake.in"
                ),
                "claim": (
                    "the CMake update step starts git fetch only when fetch_required "
                    "is YES; a full-SHA GIT_TAG whose object is already local follows "
                    "the fetch_required NO branch"
                ),
            },
            {
                "code": "no-production-fetch-inference",
                "basis": "measurement-plus-detector-positive-control",
                "production_measurement": (
                    "the three production transitions change no REFETCHED field"
                ),
                "detector_measurement": (
                    "a direct git fetch changes at least one REFETCHED field"
                ),
                "inference": "the production transitions did not fetch",
                "requires_refetch_detection_proven": True,
            },
            {
                "code": "production-head-pin-premise",
                "basis": "measurement",
                "snapshot_field": "head_matches_pin",
                "claim": (
                    "every production snapshot must observe head_sha equal to the "
                    "full-SHA masstree pin"
                ),
            },
            no_refetch_withheld_note,
        ],
        "single_tenant_observed": False,
        "single_tenant_evidence": {},
        "snapshots": {},
        "transitions": [],
        "diagnostic_transitions": [],
        "positive_control_fired": False,
        "positive_control": {},
        "update_checkout_positive_control_fired": False,
        "update_checkout_positive_control": {},
        "fetch_detector_fired": False,
        "fetch_detector_positive_control": {},
        "dependency_provisioning": {
            "completed": False,
            "source": {
                "kind": "mirrors-production-job-script",
                "path": "tools/pegasus/floor_campaign.sh",
                "provisioning_lines": "781-923",
            },
        },
        "refetch_detection_proven": False,
        "verdict": "INCONCLUSIVE",
        "verdict_reasons": ["probe did not complete"],
        "inconclusive_reasons": ["probe did not complete"],
        "legs": {},
        "cleanup": {"errors": []},
        "errors": [],
        "budget": {
            "leg_caps_s": dict(LEG_CAPS_S),
            "planned_cap_total_s": sum(LEG_CAPS_S.values()),
            "outer_cap_s": OUTER_CAP_S,
            "final_reserve_s": FINAL_RESERVE_S,
            "leg_checks": [],
            "skipped_for_budget": [],
            "elapsed_s": None,
        },
    }
    cleanup_errors: list[dict[str, str]] = result["cleanup"]["errors"]
    exit_code = 1
    ccbench_root: Optional[Path] = None
    git_path: Optional[str] = None
    initial_worktrees: Optional[list[str]] = None
    published = False

    def publish_once(*, reason: str) -> None:
        nonlocal published
        if published:
            return
        elapsed_s = time.monotonic() - started
        result["job"]["finished_at"] = utc_now()
        result["job"]["elapsed_s"] = elapsed_s
        result["budget"]["elapsed_s"] = elapsed_s
        result["publish"] = {
            "create_only": True,
            "reason": reason,
            "published_at": utc_now(),
        }
        write_create_only(output, result)
        published = True

    def signal_handler(signum: int, _frame: Any) -> None:
        result["job"]["caught_signal"] = signum
        result["verdict"] = "INCONCLUSIVE"
        result["verdict_reasons"] = [f"caught signal {signum}"]
        result["inconclusive_reasons"] = [f"caught signal {signum}"]
        try:
            publish_once(reason=f"signal-{signum}")
        except BaseException as exc:
            print(f"t1157: signal publish failed: {exc}", file=sys.stderr)
        raise SignalCaught(signum)

    previous_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    previous_sigint = signal.signal(signal.SIGINT, signal_handler)
    try:
        repo_root = Path(args.repo_root).resolve(strict=True)
        scratch = Path(os.environ["TMPDIR"]).resolve(strict=True)
        if not repo_root.is_dir() or not scratch.is_dir():
            raise ProbeError("repo root and TMPDIR must be directories")
        if os.path.commonpath((str(scratch), str(repo_root))) == str(repo_root):
            raise ProbeError("TMPDIR must be outside the repository")
        if not output.is_absolute() or output.exists() or output.is_symlink():
            raise ProbeError("output must be a new absolute path")
        if os.path.commonpath((str(output), str(scratch))) == str(scratch):
            raise ProbeError("output must be outside scratch")
        if os.path.commonpath((str(output), str(repo_root))) == str(repo_root):
            raise ProbeError("output must be outside the repository")

        sys.path.insert(0, str(repo_root))
        from orchestrator.campaign import buildcache
        from orchestrator.campaign import patchharness
        from orchestrator.campaign import s8b_floor_campaign
        from orchestrator.campaign.model import Genome

        result["production_imports"] = {
            "buildcache": str(Path(buildcache.__file__).resolve()),
            "patchharness": str(Path(patchharness.__file__).resolve()),
            "s8b_floor_campaign": str(Path(s8b_floor_campaign.__file__).resolve()),
        }

        budget_gate(result, "leg0", started)
        single, evidence = observe_single_tenant()
        result["single_tenant_observed"] = single
        result["single_tenant_evidence"] = evidence
        result["legs"]["leg0"] = {
            "single_tenant_observation_completed": True,
            "completed": False,
        }

        ccbench_root = (repo_root / "external" / "ccbench").resolve(strict=True)
        tool_names = buildcache.compilers_for_current_site()
        expected_manifest: dict[str, dict[str, str]] = {}
        tool_observations: dict[str, Any] = {}
        for role, name in (("cc", tool_names[0]), ("cxx", tool_names[1]), ("cmake", "cmake")):
            entry, observation = tool_manifest_entry(name)
            expected_manifest[role] = entry
            tool_observations[role] = observation
        identity_manifest, versions = buildcache._split_expected_toolchain_manifest(
            expected_manifest,
        )
        result["toolchain"] = {
            "expected_manifest": expected_manifest,
            "identity_manifest": identity_manifest,
            "versions": versions,
            "observations": tool_observations,
        }
        git_path, git_observation = resolve_tool("git")
        result["git_tool"] = git_observation
        pin_record = command_record(
            [git_path, "-C", str(ccbench_root), "rev-parse", "HEAD"],
            timeout_s=SHORT_TIMEOUT_S,
        )
        ccbench_pin = require_command(pin_record, "CCBench HEAD")
        if HEAD_RE.fullmatch(ccbench_pin) is None:
            raise ProbeError(f"invalid CCBench HEAD: {ccbench_pin!r}")
        result["ccbench_pin"] = ccbench_pin
        result["ccbench_pin_command"] = pin_record
        initial_worktrees, initial_record = worktree_paths(git_path, ccbench_root)
        if initial_worktrees is None:
            raise ProbeError("cannot record initial CCBench worktree list")
        result["cleanup"]["initial_worktrees"] = initial_worktrees
        result["cleanup"]["initial_worktree_command"] = initial_record
        result["legs"]["leg0"]["completed"] = True

        budget_gate(result, "leg1", started)
        configured_argument = None
        with bounded_call(SHORT_TIMEOUT_S, "canonical floor base"):
            base = s8b_floor_campaign._canonical_floor_fetchcontent_base(
                configured_argument,
            )
        base = Path(base).resolve(strict=True)
        if os.path.commonpath((str(base), str(scratch))) != str(scratch):
            raise ProbeError("canonical floor base is not under TMPDIR")
        result["legs"]["leg1"] = {
            "production_seam": "s8b_floor_campaign._canonical_floor_fetchcontent_base",
            "arguments": {"configured": configured_argument},
            "returned_path": str(base),
            "under_tmpdir": True,
        }

        budget_gate(result, "dependency_provisioning", started)
        result["legs"]["dependency_provisioning"] = {
            "completed": False,
            "evidence_key": "dependency_provisioning",
        }
        effective_dependency_prefix = provision_dependencies(
            repo_root=repo_root,
            scratch=scratch,
            git_path=git_path,
            identity_manifest=identity_manifest,
            record=result["dependency_provisioning"],
        )
        result["legs"]["dependency_provisioning"].update({
            "completed": True,
            "effective_cmake_prefix_path": effective_dependency_prefix,
        })

        budget_gate(result, "leg2", started)
        with production_checkout(
            patchharness, ccbench_pin, ccbench_root, cleanup_errors, "leg2",
        ) as sub1:
            masstree_pin, masstree_pin_evidence = masstree_pin_from_third_party(
                sub1 / "cmake" / "ThirdParty.cmake"
            )
            result["masstree_pin"] = masstree_pin
            result["masstree_pin_evidence"] = masstree_pin_evidence
            prepare1_record: dict[str, Any] = {}
            result["legs"]["leg2"] = prepare1_record
            _prepared1 = run_prepare(
                buildcache, ccbench_dir=sub1, base=base,
                expected_manifest=expected_manifest, label="leg2 prepare",
                record=prepare1_record,
            )
            result["snapshots"]["after_prebuild"] = take_snapshot(
                "after_prebuild", base, git_path, masstree_pin,
            )

        genome, genome_provenance = actual_sort_best_genome(repo_root, Genome)
        result["genome"] = genome_provenance
        if genome_provenance.get("fallback"):
            result["deviations"].append({
                "code": "stock-genome-fallback",
                "detail": str(genome_provenance.get("fallback_reason")),
            })
        cell_holdouts = sorted(genome_provenance.get("holdout_genomes", {}))
        if len(cell_holdouts) != 2:
            cell_holdouts = ["unresolved-holdout-1", "unresolved-holdout-2"]
        result["cell_holdouts"] = cell_holdouts
        budget_gate(result, "leg3", started)
        bdir = Path(tempfile.mkdtemp(prefix="t1157-cell-build-1-", dir=str(scratch)))
        with production_checkout(
            patchharness, ccbench_pin, ccbench_root, cleanup_errors, "leg3",
        ) as sub2:
            configure_cmd, build_cmd = buildcache._v2_commands(
                genome, False, str(sub2), str(bdir), identity_manifest,
                jobs=None, site=None, dependency_prefix="",
                fetchcontent_base_dir=str(base),
            )
            leg3: dict[str, Any] = {
                "production_seam": "buildcache._v2_commands",
                "cell_ordinal": 1,
                "holdout_id": cell_holdouts[0],
                "arguments": {
                    "genome": genome.canonical(), "trace": False,
                    "sub": str(sub2), "bdir": str(bdir), "jobs": None,
                    "site": None, "dependency_prefix": "",
                    "fetchcontent_base_dir": str(base),
                },
                "configure_argv": configure_cmd,
                "build_argv": build_cmd,
            }
            result["legs"]["leg3"] = leg3
            leg3["configure"] = command_record(
                configure_cmd, timeout_s=CONFIGURE_TIMEOUT_S,
            )
            result["snapshots"]["after_configure2"] = take_snapshot(
                "after_configure2", base, git_path, masstree_pin,
            )
            require_command(leg3["configure"], "configure #2")
            leg3["build"] = command_record(build_cmd, timeout_s=TARGET_TIMEOUT_S)
            result["snapshots"]["after_build2"] = take_snapshot(
                "after_build2", base, git_path, masstree_pin,
            )
            require_command(leg3["build"], "cell build #2")

            budget_gate(result, "leg4", started)
            bdir2 = Path(tempfile.mkdtemp(
                prefix="t1157-cell-build-2-", dir=str(scratch),
            ))
            with production_checkout(
                patchharness, ccbench_pin, ccbench_root, cleanup_errors, "leg4",
            ) as sub3:
                configure_cmd2, build_cmd2 = buildcache._v2_commands(
                    genome, False, str(sub3), str(bdir2), identity_manifest,
                    jobs=None, site=None, dependency_prefix="",
                    fetchcontent_base_dir=str(base),
                )
                leg4: dict[str, Any] = {
                    "production_seam": "buildcache._v2_commands",
                    "cell_ordinal": 2,
                    "holdout_id": cell_holdouts[1],
                    "arguments": {
                        "genome": genome.canonical(), "trace": False,
                        "sub": str(sub3), "bdir": str(bdir2), "jobs": None,
                        "site": None, "dependency_prefix": "",
                        "fetchcontent_base_dir": str(base),
                    },
                    "configure_argv": configure_cmd2,
                    "build_argv": build_cmd2,
                }
                result["legs"]["leg4"] = leg4
                leg4["configure"] = command_record(
                    configure_cmd2, timeout_s=CONFIGURE_TIMEOUT_S,
                )
                require_command(leg4["configure"], "configure #3 / cell #2")
                leg4["build"] = command_record(
                    build_cmd2, timeout_s=TARGET_TIMEOUT_S,
                )
                require_command(leg4["build"], "cell build #3 / cell #2")
                result["snapshots"]["after_cell_build3"] = take_snapshot(
                    "after_cell_build3", base, git_path, masstree_pin,
                )

            budget_gate(result, "leg3_diagnostic", started)
            masstree_cmd = [
                identity_manifest["cmake"]["realpath"], "--build", str(bdir),
                "--target", "masstree_build", "-j", build_cmd[-1],
            ]
            diagnostic: dict[str, Any] = {
                "production_path": False,
                "argv": masstree_cmd,
            }
            result["legs"]["leg3_diagnostic"] = diagnostic
            diagnostic["command"] = command_record(
                masstree_cmd, timeout_s=TARGET_TIMEOUT_S,
            )
            result["snapshots"]["after_masstree_diagnostic"] = take_snapshot(
                "after_masstree_diagnostic", base, git_path, masstree_pin,
            )
            require_command(diagnostic["command"], "diagnostic masstree target")
            result["diagnostic_transitions"] = [transition(
                result["snapshots"]["after_cell_build3"],
                result["snapshots"]["after_masstree_diagnostic"],
            )]

        budget_gate(result, "leg5_clone_positive_control", started)
        with bounded_call(SHORT_TIMEOUT_S, "clone positive-control base"):
            pc_base = Path(
                s8b_floor_campaign._canonical_floor_fetchcontent_base(None)
            ).resolve(strict=True)
        if os.path.commonpath((str(pc_base), str(scratch))) != str(scratch):
            raise ProbeError("clone positive-control base is not under TMPDIR")
        pc_record: dict[str, Any] = {
            "kind": "clone-path",
            "base": str(pc_base),
            "base_production_seam": "s8b_floor_campaign._canonical_floor_fetchcontent_base",
            "base_argument": None,
        }
        result["positive_control"] = pc_record
        with production_checkout(
            patchharness, ccbench_pin, ccbench_root, cleanup_errors, "leg5",
        ) as pc_sub:
            pc_prepare_record: dict[str, Any] = {}
            pc_record["prepare"] = pc_prepare_record
            pc_prepared = run_prepare(
                buildcache, ccbench_dir=pc_sub, base=pc_base,
                expected_manifest=expected_manifest, label="clone positive-control prepare",
                record=pc_prepare_record,
            )
            pc_before = take_snapshot(
                "pc_before", pc_base, git_path, masstree_pin,
            )
            result["snapshots"]["pc_before"] = pc_before
            lastrun = pc_before["stamp_dir"]["required"]["gitclone_lastrun"]
            gitinfo = pc_before["stamp_dir"]["required"]["gitinfo"]
            if (
                lastrun.get("observed") is not True
                or gitinfo.get("observed") is not True
                or lastrun.get("exists") is not True
                or gitinfo.get("exists") is not True
            ):
                raise ProbeError("positive-control stamp files were not both observed")
            gitinfo_path = Path(str(gitinfo["path"]))
            info_stat = gitinfo_path.stat()
            future_ns = max(
                time.time_ns() + 10_000_000_000,
                int(lastrun["st_mtime_ns"]) + 10_000_000_000,
            )
            os.utime(gitinfo_path, ns=(info_stat.st_atime_ns, future_ns))
            touched = gitinfo_path.stat()
            pc_record["touch"] = {
                "path": str(gitinfo_path),
                "before_mtime_ns": info_stat.st_mtime_ns,
                "lastrun_mtime_ns": lastrun["st_mtime_ns"],
                "requested_future_mtime_ns": future_ns,
                "observed_mtime_ns": touched.st_mtime_ns,
                "strictly_newer_than_lastrun": touched.st_mtime_ns > int(lastrun["st_mtime_ns"]),
            }
            if touched.st_mtime_ns <= int(lastrun["st_mtime_ns"]):
                raise ProbeError("positive-control gitinfo mtime did not become newer")
            pc_record["second_configure"] = command_record(
                list(pc_prepared.configure_argv), timeout_s=CONFIGURE_TIMEOUT_S,
            )
            pc_after = take_snapshot(
                "pc_after", pc_base, git_path, masstree_pin,
            )
            result["snapshots"]["pc_after"] = pc_after
            require_command(pc_record["second_configure"], "positive-control configure")
            pc_transition = transition(pc_before, pc_after)
            pc_record["transition"] = pc_transition
            before_src_ok, before_src = get_path(pc_before, "src_dir.st_ino")
            after_src_ok, after_src = get_path(pc_after, "src_dir.st_ino")
            before_config_ok, before_config = get_path(pc_before, "config_h.exists")
            after_config_ok, after_config = get_path(pc_after, "config_h.exists")
            fired = (
                pc_before["src_dir"].get("observed") is True
                and pc_after["src_dir"].get("observed") is True
                and pc_before["config_h"].get("observed") is True
                and pc_after["config_h"].get("observed") is True
                and before_src_ok and after_src_ok and before_src != after_src
                and before_config_ok and after_config_ok
                and before_config is True and after_config is False
            )
            pc_record["firing_predicate"] = (
                "all four endpoint observations have observed=true and "
                "pc_before.src_dir.st_ino != pc_after.src_dir.st_ino and "
                "pc_before.config_h.exists is true and pc_after.config_h.exists is false"
            )
            pc_record["changed_fields"] = pc_transition["changed_fields"]
            result["positive_control_fired"] = fired

        budget_gate(result, "leg6_update_checkout_positive_control", started)
        with bounded_call(SHORT_TIMEOUT_S, "update-checkout positive-control base"):
            update_base = Path(
                s8b_floor_campaign._canonical_floor_fetchcontent_base(None)
            ).resolve(strict=True)
        if os.path.commonpath((str(update_base), str(scratch))) != str(scratch):
            raise ProbeError("update-checkout positive-control base is not under TMPDIR")
        update_record: dict[str, Any] = {
            "kind": "update-checkout-path",
            "base": str(update_base),
            "base_production_seam": "s8b_floor_campaign._canonical_floor_fetchcontent_base",
            "base_argument": None,
        }
        result["update_checkout_positive_control"] = update_record
        with production_checkout(
            patchharness, ccbench_pin, ccbench_root, cleanup_errors, "leg6",
        ) as update_sub:
            update_prepare_record: dict[str, Any] = {}
            update_record["prepare"] = update_prepare_record
            update_prepared = run_prepare(
                buildcache, ccbench_dir=update_sub, base=update_base,
                expected_manifest=expected_manifest,
                label="update-checkout positive-control prepare",
                record=update_prepare_record,
            )
            update_src = update_base / "masstree-src"
            pin_record = command_record(
                [git_path, "-C", str(update_src), "rev-parse", "HEAD"],
                timeout_s=SHORT_TIMEOUT_S, raw_output=True,
            )
            observed_update_pin = require_command(
                pin_record, "update-checkout-control masstree pin",
            )
            if observed_update_pin != masstree_pin:
                raise ProbeError(
                    "update-checkout-control source HEAD did not match masstree pin"
                )
            parent_record = command_record(
                [git_path, "-C", str(update_src), "rev-parse", f"{masstree_pin}^"],
                timeout_s=SHORT_TIMEOUT_S, raw_output=True,
            )
            parent_pin = require_command(
                parent_record, "update-checkout-control parent pin",
            )
            checkout_record = command_record(
                [git_path, "-C", str(update_src), "checkout", "--detach", parent_pin],
                timeout_s=SHORT_TIMEOUT_S,
            )
            require_command(
                checkout_record, "update-checkout-control checkout parent",
            )
            update_record["divergence"] = {
                "masstree_pin": masstree_pin,
                "parent_pin": parent_pin,
                "pin_command": pin_record,
                "parent_command": parent_record,
                "checkout_command": checkout_record,
            }
            update_before = take_snapshot(
                "update_checkout_pc_before", update_base, git_path, masstree_pin,
            )
            result["snapshots"]["update_checkout_pc_before"] = update_before
            if update_before["git_state"]["head"].get("output") != parent_pin:
                raise ProbeError(
                    "update-checkout-control HEAD did not diverge to pin parent"
                )
            update_record["second_configure"] = command_record(
                list(update_prepared.configure_argv), timeout_s=CONFIGURE_TIMEOUT_S,
            )
            require_command(
                update_record["second_configure"],
                "update-checkout positive-control configure",
            )
            update_after = take_snapshot(
                "update_checkout_pc_after", update_base, git_path, masstree_pin,
            )
            result["snapshots"]["update_checkout_pc_after"] = update_after
            update_transition = transition(update_before, update_after)
            update_record["transition"] = update_transition
            update_changed = set(update_transition["signature_changed_fields"])
            update_fired = (
                update_before["git_state"]["head"].get("observed") is True
                and update_after["git_state"]["head"].get("observed") is True
                and update_after["git_state"]["head"].get("output") == masstree_pin
                and not update_transition["signature_unobservable_fields"]
                and not update_transition["signature_unavailable_fields"]
                and bool(update_changed & REFETCHED_FIELDS)
            )
            update_record["firing_predicate"] = (
                "HEAD was observably moved from masstree_pin^ back to masstree_pin, "
                "all refetch signature observations were observable, and at least one "
                "REFETCHED field changed; this proves update checkout re-entry only"
            )
            update_record["changed_refetch_fields"] = sorted(
                update_changed & REFETCHED_FIELDS
            )
            result["update_checkout_positive_control_fired"] = update_fired

        budget_gate(result, "leg7_fetch_detector_positive_control", started)
        fetch_src = update_base / "masstree-src"
        fetch_record: dict[str, Any] = {
            "kind": "direct-git-fetch",
            "base": str(update_base),
            "source": str(fetch_src),
            "observed": False,
            "error": None,
        }
        result["fetch_detector_positive_control"] = fetch_record
        fetch_before = take_snapshot(
            "fetch_detector_before", update_base, git_path, masstree_pin,
        )
        result["snapshots"]["fetch_detector_before"] = fetch_before
        fetch_record["command"] = command_record(
            [git_path, "-C", str(fetch_src), "fetch", "--tags", "--force", "origin"],
            timeout_s=FETCH_TIMEOUT_S,
        )
        fetch_after = take_snapshot(
            "fetch_detector_after", update_base, git_path, masstree_pin,
        )
        result["snapshots"]["fetch_detector_after"] = fetch_after
        fetch_transition = transition(fetch_before, fetch_after)
        fetch_record["transition"] = fetch_transition
        changed_refetch_fields = sorted(
            set(fetch_transition["signature_changed_fields"])
            & REFETCHED_FIELDS
        )
        unavailable_refetch_fields = sorted(
            set(fetch_transition["signature_unavailable_fields"])
            & REFETCHED_FIELDS
        )
        unobservable_refetch_fields = sorted(
            set(fetch_transition["signature_unobservable_fields"])
            & REFETCHED_FIELDS
        )
        comparable_refetch_fields = sorted(
            set(fetch_transition["comparable_fields"])
            & REFETCHED_FIELDS
        )
        fetch_succeeded = fetch_record["command"].get("rc") == 0
        detector_observed = fetch_succeeded and bool(comparable_refetch_fields)
        if not fetch_succeeded:
            fetch_record["error"] = (
                "direct git fetch failed: "
                f"rc={fetch_record['command'].get('rc')} "
                f"timeout={fetch_record['command'].get('timed_out')} "
                f"launch_error={fetch_record['command'].get('launch_error')}"
            )
            fetch_record["outcome"] = "fetch-command-failed"
        elif not comparable_refetch_fields:
            fetch_record["error"] = (
                "no REFETCHED field was comparable across the fetch snapshots"
            )
            fetch_record["outcome"] = "detector-unobservable"
        elif changed_refetch_fields:
            fetch_record["outcome"] = "detector-fired"
        else:
            fetch_record["outcome"] = "detector-did-not-fire"
        fetch_record.update({
            "observed": detector_observed,
            "fetch_succeeded": fetch_succeeded,
            "changed_refetch_fields": changed_refetch_fields,
            "comparable_refetch_fields": comparable_refetch_fields,
            "unavailable_refetch_fields": unavailable_refetch_fields,
            "unobservable_refetch_fields": unobservable_refetch_fields,
            "firing_predicate": (
                "direct git fetch succeeded and at least one comparable "
                "REFETCHED field changed"
            ),
        })
        fetch_detector_fired = detector_observed and bool(changed_refetch_fields)
        result["fetch_detector_fired"] = fetch_detector_fired
        result["refetch_detection_proven"] = fetch_detector_fired
        if fetch_detector_fired:
            result["scope_notes"].remove(no_refetch_withheld_note)
        else:
            no_refetch_withheld_note["fetch_detector_outcome"] = fetch_record["outcome"]

        labels = (
            ("after_prebuild", "after_configure2"),
            ("after_configure2", "after_build2"),
            ("after_build2", "after_cell_build3"),
        )
        result["transitions"] = [
            transition(result["snapshots"][before], result["snapshots"][after])
            for before, after in labels
        ]
        production_snapshot_labels = (
            "after_prebuild",
            "after_configure2",
            "after_build2",
            "after_cell_build3",
        )
        result["production_snapshot_head_pin_checks"] = {
            label: {
                "head_sha": result["snapshots"][label]["head_sha"],
                "expected_pin": result["snapshots"][label]["expected_pin"],
                "head_matches_pin": result["snapshots"][label]["head_matches_pin"],
            }
            for label in production_snapshot_labels
        }
        forced_reasons = []
        if not all(
            result["snapshots"][label]["head_matches_pin"] is True
            for label in production_snapshot_labels
        ):
            forced_reasons.append(
                "one or more production snapshot HEADs did not observably match "
                "the full-SHA masstree pin"
            )
        result["verdict"], result["verdict_reasons"] = compute_verdict(
            result["transitions"], result["positive_control_fired"],
            refetch_detection_proven=result["refetch_detection_proven"],
            single_tenant_observed=result["single_tenant_observed"],
            forced_reasons=forced_reasons,
        )
        result["inconclusive_reasons"] = (
            result["verdict_reasons"] if result["verdict"] == "INCONCLUSIVE" else []
        )
        if result["verdict"] != "INCONCLUSIVE":
            exit_code = 0
        else:
            exit_code = 4
    except SignalCaught as exc:
        exit_code = 128 + exc.signum
    except BudgetExhausted as exc:
        result["errors"].append({
            "type": type(exc).__name__,
            "message": str(exc),
        })
        result["verdict"] = "INCONCLUSIVE"
        result["verdict_reasons"] = ["one or more legs were skipped_for_budget"]
        result["inconclusive_reasons"] = list(result["verdict_reasons"])
        exit_code = 4
    except BaseException as exc:
        result["errors"].append({
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        })
        result["verdict"] = "INCONCLUSIVE"
        result["verdict_reasons"] = ["probe raised before completing all required legs"]
        result["inconclusive_reasons"] = list(result["verdict_reasons"])
        exit_code = 1
    finally:
        if ccbench_root is not None and git_path is not None:
            final_worktrees, final_record = worktree_paths(git_path, ccbench_root)
            result["cleanup"]["final_worktrees"] = final_worktrees
            result["cleanup"]["final_worktree_command"] = final_record
            if initial_worktrees is not None and final_worktrees is not None:
                residue = sorted(set(final_worktrees) - set(initial_worktrees))
                result["cleanup"]["added_worktree_residue"] = residue
                result["cleanup"]["no_added_worktree_residue"] = not residue
                if residue:
                    result["verdict"] = "INCONCLUSIVE"
                    result["inconclusive_reasons"].append(
                        "disposable CCBench worktree residue remains"
                    )
                    result["verdict_reasons"] = list(result["inconclusive_reasons"])
                    exit_code = 1
            else:
                result["cleanup"]["no_added_worktree_residue"] = False
                result["verdict"] = "INCONCLUSIVE"
                result["inconclusive_reasons"].append(
                    "final CCBench worktree list was unavailable"
                )
                result["verdict_reasons"] = list(result["inconclusive_reasons"])
                exit_code = 1
        if cleanup_errors:
            result["verdict"] = "INCONCLUSIVE"
            result["inconclusive_reasons"].append(
                "checkout cleanup reported an error"
            )
            result["verdict_reasons"] = list(result["inconclusive_reasons"])
            exit_code = 1
        try:
            publish_once(reason="normal-finally")
        except BaseException as exc:
            print(f"t1157: cannot publish create-only JSON: {exc}", file=sys.stderr)
            return 2
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
            signal.signal(signal.SIGINT, previous_sigint)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
```
