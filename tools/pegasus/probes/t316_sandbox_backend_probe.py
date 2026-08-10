#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
"""Pegasus 計算ノード上で sandbox backend を S1〜S7 に分けて実測する。

外部 command の stdout/stderr は receipt に保存する観測データであり、probe の
命令や verdict の理由として解釈しない。verdict 核は subprocess から独立した純関数である。
"""
from __future__ import annotations

import argparse
import ctypes
import dataclasses
import errno
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence
from urllib.parse import urlparse


SCHEMA_VERSION = "t316-sandbox-backend-probe/v1"
POLICY_SCHEMA_VERSION = "t316-sandbox-backend-policy/v1"
VERDICT_VALUES = frozenset({"go", "no-go", "inconclusive", "blocked"})
S3_CATEGORIES = (
    "network_dns",
    "network_direct_ip",
    "network_proxy",
    "credential_home",
    "credential_ssh_agent",
    "credential_ssh_dir",
    "credential_codex_dir",
    "write_home",
    "write_repo",
    "write_tmp",
    "source_read_only",
)
S5_CATEGORIES = ("system_command", "network", "file_write", "infinite_loop")
_JOB_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_OUTPUT_LIMIT = 16 * 1024


@dataclasses.dataclass(frozen=True)
class StageVerdict:
    stage: str
    verdict: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.verdict not in VERDICT_VALUES:
            raise ValueError(f"unknown verdict: {self.verdict}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
        }


def _paired_verdict(
    stage: str, category: str, observation: Mapping[str, Any]
) -> StageVerdict:
    """正例と封じ込め負例の一対を副作用なしで判定する。"""
    prefix = f"{stage}_{category}".upper().replace("-", "_")
    if observation.get("attempted") is not True:
        return StageVerdict(stage, "blocked", (f"{prefix}_NOT_ATTEMPTED",))
    if observation.get("outside_success") is not True:
        return StageVerdict(
            stage, "inconclusive", (f"{prefix}_POSITIVE_CONTROL_FAILED",)
        )
    if observation.get("inside_blocked") is not True:
        return StageVerdict(stage, "no-go", (f"{prefix}_CONTAINMENT_FAILED",))
    return StageVerdict(stage, "go", (f"{prefix}_CONTAINED",))


def _merge_stage_verdicts(stage: str, verdicts: Sequence[StageVerdict]) -> StageVerdict:
    """同一 stage のカテゴリ判定を no-go 優先で畳み込む純関数。"""
    reasons = tuple(reason for item in verdicts for reason in item.reason_codes)
    values = {item.verdict for item in verdicts}
    for value in ("no-go", "blocked", "inconclusive", "go"):
        if value in values:
            return StageVerdict(stage, value, reasons)
    return StageVerdict(stage, "blocked", (f"{stage}_EMPTY".upper(),))


def verdict_s1(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S1", "blocked", ("S1_INVENTORY_NOT_ATTEMPTED",))
    tools = observation.get("tools")
    if not isinstance(tools, Mapping):
        return StageVerdict("S1", "blocked", ("S1_TOOL_INVENTORY_MISSING",))
    bwrap = tools.get("bwrap")
    if not isinstance(bwrap, Mapping) or bwrap.get("available") is not True:
        return StageVerdict("S1", "no-go", ("S1_BWRAP_UNAVAILABLE",))
    return StageVerdict("S1", "go", ("S1_INVENTORY_COMPLETE",))


def verdict_s2(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S2", "blocked", ("S2_NAMESPACE_NOT_ATTEMPTED",))
    checks = observation.get("namespace_checks")
    if not isinstance(checks, Mapping):
        return StageVerdict("S2", "blocked", ("S2_NAMESPACE_CHECKS_MISSING",))
    missing = [name for name in ("user", "pid", "net", "mnt") if name not in checks]
    if missing:
        return StageVerdict(
            "S2", "blocked", tuple(f"S2_{name.upper()}_NOT_ATTEMPTED" for name in missing)
        )
    failed = [name for name in ("user", "pid", "net", "mnt") if checks.get(name) is not True]
    if failed:
        return StageVerdict(
            "S2", "no-go", tuple(f"S2_{name.upper()}_NAMESPACE_FAILED" for name in failed)
        )
    return StageVerdict("S2", "go", ("S2_REQUIRED_NAMESPACES_STARTED",))


def verdict_s3(observations: Mapping[str, Mapping[str, Any]]) -> StageVerdict:
    verdicts = [
        _paired_verdict("S3", category, observations.get(category, {}))
        for category in S3_CATEGORIES
    ]
    scratch = observations.get("scratch_write")
    if not isinstance(scratch, Mapping) or scratch.get("attempted") is not True:
        verdicts.append(StageVerdict("S3", "blocked", ("S3_SCRATCH_WRITE_NOT_ATTEMPTED",)))
    elif scratch.get("inside_success") is not True:
        verdicts.append(StageVerdict("S3", "no-go", ("S3_SCRATCH_WRITE_FAILED",)))
    else:
        verdicts.append(StageVerdict("S3", "go", ("S3_SCRATCH_WRITE_ALLOWED",)))
    return _merge_stage_verdicts("S3", verdicts)


def verdict_s4(observation: Mapping[str, Any]) -> StageVerdict:
    return _paired_verdict("S4", "escaped_descendant", observation)


def verdict_s5(observations: Mapping[str, Mapping[str, Any]]) -> StageVerdict:
    return _merge_stage_verdicts(
        "S5",
        [
            _paired_verdict("S5", category, observations.get(category, {}))
            for category in S5_CATEGORIES
        ],
    )


def verdict_s6(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S6", "blocked", ("S6_BUILD_NOT_ATTEMPTED",))
    if observation.get("failure_stage") == "walltime":
        return StageVerdict("S6", "blocked", ("S6_WALLTIME_RESERVE_REACHED",))
    if observation.get("success") is not True:
        return StageVerdict("S6", "no-go", ("S6_SANDBOX_BUILD_FAILED",))
    if observation.get("trace_disabled") is not True:
        return StageVerdict("S6", "no-go", ("S6_TRACE_DISABLED_NOT_PROVEN",))
    return StageVerdict("S6", "go", ("S6_SANDBOX_BUILD_SUCCEEDED",))


def verdict_s7(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S7", "blocked", ("S7_PERFORMANCE_NOT_ATTEMPTED",))
    if observation.get("outside_success") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_OUTSIDE_RUN_FAILED",))
    if observation.get("inside_success") is not True:
        return StageVerdict("S7", "no-go", ("S7_SANDBOX_RUN_FAILED",))
    if observation.get("same_binary") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_BINARY_IDENTITY_MISMATCH",))
    if observation.get("trace_disabled") is not True:
        return StageVerdict("S7", "no-go", ("S7_TRACE_DISABLED_NOT_PROVEN",))
    ratio = observation.get("overhead_ratio")
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or ratio <= 0:
        return StageVerdict("S7", "inconclusive", ("S7_OVERHEAD_RATIO_UNAVAILABLE",))
    return StageVerdict("S7", "go", ("S7_OVERHEAD_RATIO_RECORDED",))


def aggregate_verdicts(verdicts: Sequence[StageVerdict]) -> StageVerdict:
    """S1〜S7 の総合 verdict。1 個でも no-go なら決して go にしない。"""
    by_stage = {item.stage: item for item in verdicts}
    missing = [f"S{index}" for index in range(1, 8) if f"S{index}" not in by_stage]
    if missing:
        return StageVerdict(
            "overall", "blocked", tuple(f"OVERALL_{stage}_MISSING" for stage in missing)
        )
    reasons = tuple(reason for item in verdicts for reason in item.reason_codes)
    values = {item.verdict for item in verdicts}
    for value in ("no-go", "blocked", "inconclusive", "go"):
        if value in values:
            return StageVerdict("overall", value, reasons)
    return StageVerdict("overall", "blocked", ("OVERALL_EMPTY",))


def _error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bounded_output(value: bytes) -> dict[str, Any]:
    return {
        "sha256": _sha256_bytes(value),
        "bytes": len(value),
        "tail": value[-_OUTPUT_LIMIT:].decode("utf-8", errors="replace"),
        "truncated": len(value) > _OUTPUT_LIMIT,
    }


def _descendants(root_pid: int) -> set[int]:
    parents: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text(encoding="utf-8").split()
            parents[int(entry.name)] = int(fields[3])
        except (OSError, ValueError, IndexError):
            continue
    result: set[int] = set()
    frontier = {root_pid}
    while frontier:
        children = {pid for pid, ppid in parents.items() if ppid in frontier and pid not in result}
        result.update(children)
        frontier = children
    return result


def _kill_tree(root_pid: int) -> None:
    targets = _descendants(root_pid) | {root_pid}
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in sorted(targets, reverse=True):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        if sig == signal.SIGTERM:
            time.sleep(0.2)


def _run_command(
    argv: Sequence[str], *, timeout_s: float, env: Optional[Mapping[str, str]] = None
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "attempted": True,
        "executed": False,
        "argv": list(argv),
        "timeout_s": timeout_s,
        "rc": None,
        "timed_out": False,
    }
    started = time.monotonic_ns()
    process: Optional[subprocess.Popen[bytes]] = None
    try:
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=None if env is None else dict(env),
            start_new_session=True,
        )
        record["executed"] = True
        stdout, stderr = process.communicate(timeout=timeout_s)
        record["rc"] = process.returncode
    except subprocess.TimeoutExpired:
        record["timed_out"] = True
        assert process is not None
        _kill_tree(process.pid)
        stdout, stderr = process.communicate()
        record["rc"] = process.returncode
    except OSError as exc:
        stdout = b""
        stderr = b""
        record["error"] = _error(exc)
    record["elapsed_ns"] = time.monotonic_ns() - started
    record["stdout"] = _bounded_output(stdout)
    record["stderr"] = _bounded_output(stderr)
    return record


def _run_group_timeout(argv: Sequence[str], *, timeout_s: float) -> dict[str, Any]:
    """process group だけを timeout kill し、setsid() escape の対照を作る。"""
    record: dict[str, Any] = {
        "attempted": True,
        "executed": False,
        "argv": list(argv),
        "timeout_s": timeout_s,
        "rc": None,
        "timed_out": False,
    }
    started = time.monotonic_ns()
    process: Optional[subprocess.Popen[bytes]] = None
    try:
        process = subprocess.Popen(
            list(argv), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True,
        )
        record["executed"] = True
        try:
            stdout, stderr = process.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        record["rc"] = process.returncode
    except OSError as exc:
        stdout = b""
        stderr = b""
        record["error"] = _error(exc)
    record["elapsed_ns"] = time.monotonic_ns() - started
    record["stdout"] = _bounded_output(stdout)
    record["stderr"] = _bounded_output(stderr)
    return record


def _tool_record(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    record: dict[str, Any] = {"available": path is not None, "path": path}
    if path is not None:
        record["version"] = _run_command([path, "--version"], timeout_s=10)
    return record


def _other_user_processes() -> dict[str, Any]:
    own_uid = os.getuid()
    pids: list[int] = []
    uids: set[int] = set()
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            line = next(
                item for item in (entry / "status").read_text(encoding="utf-8").splitlines()
                if item.startswith("Uid:")
            )
            uid = int(line.split()[1])
        except (OSError, StopIteration, ValueError, IndexError):
            continue
        if uid not in (0, own_uid):
            pids.append(int(entry.name))
            uids.add(uid)
    return {"present": bool(pids), "count": len(pids), "uids": sorted(uids), "pids": sorted(pids)}


def _landlock_record() -> dict[str, Any]:
    if platform.machine() not in {"x86_64", "aarch64"}:
        return {"attempted": False, "available": None, "reason": "unsupported syscall table"}
    libc = ctypes.CDLL(None, use_errno=True)
    result = int(libc.syscall(444, 0, 0, 1))
    saved_errno = ctypes.get_errno()
    return {
        "attempted": True,
        "available": result >= 1,
        "abi_version": result if result >= 1 else None,
        "errno": None if result >= 1 else saved_errno,
        "errno_name": None if result >= 1 else errno.errorcode.get(saved_errno),
    }


def observe_s1() -> dict[str, Any]:
    status = Path("/proc/self/status").read_text(encoding="utf-8")
    seccomp_lines = [line for line in status.splitlines() if line.startswith("Seccomp")]
    userns_path = Path("/proc/sys/user/max_user_namespaces")
    return {
        "attempted": True,
        "tools": {name: _tool_record(name) for name in ("bwrap", "unshare", "setpriv", "nsenter")},
        "kernel_release": platform.release(),
        "hostname": socket.gethostname(),
        "PBS_JOBID": os.environ.get("PBS_JOBID"),
        "seccomp": {
            "status": seccomp_lines,
            "actions_available": Path("/proc/sys/kernel/seccomp/actions_avail").read_text(encoding="utf-8").strip()
            if Path("/proc/sys/kernel/seccomp/actions_avail").is_file() else None,
        },
        "user_namespace": {
            "max_user_namespaces": userns_path.read_text(encoding="utf-8").strip()
            if userns_path.is_file() else None,
        },
        "landlock": _landlock_record(),
        "exclusivity_evidence": {
            "load_average": list(os.getloadavg()),
            "other_non_root_user_processes": _other_user_processes(),
            "nproc": os.cpu_count(),
            "cpu_affinity": sorted(os.sched_getaffinity(0)),
        },
    }


class SandboxProfile:
    def __init__(
        self,
        bwrap: Optional[str],
        repo_root: Path,
        scratch: Path,
        readonly_roots: Sequence[Path],
    ) -> None:
        self.bwrap = bwrap
        self.repo_root = repo_root
        self.scratch = scratch
        unique = {path.resolve(strict=True) for path in readonly_roots if path.exists()}
        unique.add(repo_root.resolve(strict=True))
        self.readonly_roots = tuple(sorted(unique, key=str))

    def argv(
        self,
        command: Sequence[str],
        *,
        build: bool = False,
        extra_env: Optional[Mapping[str, str]] = None,
    ) -> Optional[list[str]]:
        if self.bwrap is None:
            return None
        argv = [
            self.bwrap,
            "--unshare-user",
            "--unshare-pid",
            "--unshare-net",
            "--unshare-ipc",
            "--unshare-uts",
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            "--proc", "/proc",
            "--dev", "/dev",
        ]
        for source in (Path("/usr"), Path("/lib"), Path("/lib64"), Path("/etc")):
            if source.exists():
                argv.extend(("--ro-bind", str(source), str(source)))
        if build and Path("/bin").exists():
            argv.extend(("--ro-bind", "/bin", "/bin"))
        else:
            argv.extend(("--dir", "/bin"))
        argv.extend(("--ro-bind", str(self.scratch / "empty-tmp"), "/tmp"))
        argv.extend(("--dir", "/home"))
        for source in self.readonly_roots:
            argv.extend(("--ro-bind", str(source), str(source)))
        argv.extend(("--bind", str(self.scratch), str(self.scratch)))
        environment = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.scratch / "home"),
            "TMPDIR": str(self.scratch / "tmp"),
            "LC_ALL": "C",
        }
        environment.update(extra_env or {})
        for key, value in sorted(environment.items()):
            argv.extend(("--setenv", key, value))
        argv.extend(("--chdir", str(self.scratch), "--"))
        argv.extend(command)
        return argv

    def run(
        self,
        command: Sequence[str],
        *,
        timeout_s: float,
        build: bool = False,
        extra_env: Optional[Mapping[str, str]] = None,
    ) -> dict[str, Any]:
        argv = self.argv(command, build=build, extra_env=extra_env)
        if argv is None:
            return {"attempted": False, "executed": False, "reason": "bwrap unavailable"}
        return _run_command(argv, timeout_s=timeout_s)


def observe_s2(profile: SandboxProfile, python: str) -> dict[str, Any]:
    helper = (
        "import json,os; print(json.dumps({n:os.readlink('/proc/self/ns/'+n) "
        "for n in ('user','pid','net','mnt')}))"
    )
    outside = _run_command([python, "-I", "-B", "-c", helper], timeout_s=10)
    inside = profile.run([python, "-I", "-B", "-c", helper], timeout_s=20)
    checks: dict[str, bool] = {}
    try:
        outside_ns = json.loads(outside["stdout"]["tail"])
        inside_ns = json.loads(inside["stdout"]["tail"])
        for name in ("user", "pid", "net", "mnt"):
            checks[name] = inside.get("rc") == 0 and outside_ns[name] != inside_ns[name]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        checks = {}
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside": outside,
        "inside": inside,
        "namespace_checks": checks,
    }


def _paired_command(
    profile: SandboxProfile,
    command: Sequence[str],
    *,
    timeout_s: float = 15,
    build_profile: bool = False,
    extra_env: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    outside = _run_command(command, timeout_s=timeout_s, env={**os.environ, **(extra_env or {})})
    inside = profile.run(
        command, timeout_s=timeout_s, build=build_profile, extra_env=extra_env
    )
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside_success": outside.get("rc") == 0,
        "inside_blocked": inside.get("executed") is True and inside.get("rc") != 0,
        "outside": outside,
        "inside": inside,
    }


def _network_command(python: str, host: str, port: int) -> list[str]:
    code = (
        "import socket,sys; s=socket.create_connection((sys.argv[1],int(sys.argv[2])),4);"
        "s.close()"
    )
    return [python, "-I", "-B", "-c", code, host, str(port)]


def _proxy_command(python: str) -> list[str]:
    code = "import urllib.request; r=urllib.request.urlopen('https://example.com/',timeout=8); r.read(1)"
    return [python, "-I", "-B", "-c", code]


def _network_targets() -> tuple[str, str, int]:
    """名前解決 target、同 endpoint の直接 IP、port を返す。"""
    proxy_value = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy_value:
        parsed = urlparse(proxy_value)
        if parsed.hostname:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            try:
                addresses = socket.getaddrinfo(parsed.hostname, port, socket.AF_INET, socket.SOCK_STREAM)
                if addresses:
                    return parsed.hostname, str(addresses[0][4][0]), port
            except socket.gaierror:
                pass
    return "example.com", "1.1.1.1", 443


def _read_command(python: str, path: Path, *, socket_path: bool = False) -> list[str]:
    if socket_path:
        code = (
            "import socket,sys; s=socket.socket(socket.AF_UNIX); s.settimeout(3);"
            "s.connect(sys.argv[1]); s.close()"
        )
    else:
        code = "import os,sys; os.listdir(sys.argv[1])"
    return [python, "-I", "-B", "-c", code, str(path)]


def _write_command(python: str, path: Path) -> list[str]:
    code = "import os,sys; fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,b't316'); os.close(fd)"
    return [python, "-I", "-B", "-c", code, str(path)]


def _cleanup_marker(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def observe_s3(profile: SandboxProfile, python: str, repo_root: Path, scratch: Path) -> dict[str, Any]:
    job_tag = re.sub(r"[^A-Za-z0-9_.-]", "_", os.environ.get("PBS_JOBID", "unknown"))
    home = Path(os.environ.get("HOME", "/nonexistent"))
    observations: dict[str, Any] = {}
    dns_host, direct_ip, network_port = _network_targets()
    observations["network_dns"] = _paired_command(
        profile, _network_command(python, dns_host, network_port)
    )
    observations["network_dns"]["target"] = {"host": dns_host, "port": network_port}
    observations["network_direct_ip"] = _paired_command(
        profile, _network_command(python, direct_ip, network_port)
    )
    observations["network_direct_ip"]["target"] = {"ip": direct_ip, "port": network_port}

    proxy_env = {
        key: value for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
        if (value := os.environ.get(key))
    }
    if proxy_env:
        observations["network_proxy"] = _paired_command(
            profile, _proxy_command(python), timeout_s=15, extra_env=proxy_env
        )
        observations["network_proxy"]["proxy_endpoints"] = {
            key: {"scheme": urlparse(value).scheme, "hostname": urlparse(value).hostname, "port": urlparse(value).port}
            for key, value in proxy_env.items()
        }
    else:
        observations["network_proxy"] = {"attempted": False, "reason": "no HTTP(S) proxy environment variable"}

    credential_targets = {
        "credential_home": (home, False),
        "credential_ssh_agent": (Path(os.environ.get("SSH_AUTH_SOCK", "/nonexistent")), True),
        "credential_ssh_dir": (home / ".ssh", False),
        "credential_codex_dir": (home / ".codex", False),
    }
    for category, (path, is_socket) in credential_targets.items():
        observations[category] = _paired_command(
            profile, _read_command(python, path, socket_path=is_socket)
        )

    write_targets = {
        "write_home": home / f".t316-write-{job_tag}",
        "write_repo": repo_root / f".t316-write-{job_tag}",
        "write_tmp": Path("/tmp") / f"t316-write-{job_tag}",
        "source_read_only": repo_root / f".t316-source-ro-{job_tag}",
    }
    for category, path in write_targets.items():
        _cleanup_marker(path)
        observations[category] = _paired_command(profile, _write_command(python, path))
        _cleanup_marker(path)

    scratch_marker = scratch / "s3-scratch-write"
    _cleanup_marker(scratch_marker)
    inside = profile.run(_write_command(python, scratch_marker), timeout_s=10)
    observations["scratch_write"] = {
        "attempted": inside.get("attempted") is True,
        "inside_success": inside.get("rc") == 0 and scratch_marker.is_file(),
        "inside": inside,
    }
    _cleanup_marker(scratch_marker)
    return observations


def observe_s4(profile: SandboxProfile, python: str, scratch: Path) -> dict[str, Any]:
    helper = (
        "import os,sys,time; marker,pidfile=sys.argv[1:3]; pid=os.fork();"
        "\nif pid==0:\n os.setsid(); os.close(0); os.close(1); os.close(2); open(pidfile,'x').write(str(os.getpid())); time.sleep(2); open(marker,'x').write('alive'); os._exit(0)"
        "\ntime.sleep(30)"
    )
    outside_marker = scratch / "s4-outside-marker"
    outside_pidfile = scratch / "s4-outside-pid"
    inside_marker = scratch / "s4-inside-marker"
    inside_pidfile = scratch / "s4-inside-pid"
    for path in (outside_marker, outside_pidfile, inside_marker, inside_pidfile):
        _cleanup_marker(path)
    outside = _run_group_timeout(
        [python, "-I", "-B", "-c", helper, str(outside_marker), str(outside_pidfile)],
        timeout_s=1,
    )
    time.sleep(1.5)
    outside_survived = outside_marker.is_file()
    inside_argv = profile.argv(
        [python, "-I", "-B", "-c", helper, str(inside_marker), str(inside_pidfile)]
    )
    inside = (
        _run_group_timeout(inside_argv, timeout_s=1)
        if inside_argv is not None
        else {"attempted": False, "executed": False, "reason": "bwrap unavailable"}
    )
    time.sleep(1.5)
    inside_survived = inside_marker.is_file()
    for path in (outside_marker, outside_pidfile, inside_marker, inside_pidfile):
        _cleanup_marker(path)
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside_success": outside.get("timed_out") is True and outside_survived,
        "inside_blocked": inside.get("timed_out") is True and not inside_survived,
        "outside": outside,
        "inside": inside,
        "outside_escaped_descendant_survived": outside_survived,
        "inside_escaped_descendant_survived": inside_survived,
    }


_THREAT_SOURCE = r'''
#include <arpa/inet.h>
#include <cstdlib>
#include <fstream>
#include <netinet/in.h>
#include <string>
#include <sys/socket.h>
#include <unistd.h>
int main(int argc, char** argv) {
  if (argc < 2) return 64;
  std::string mode(argv[1]);
  if (mode == "system" && argc == 3) {
    std::string command = "/usr/bin/touch " + std::string(argv[2]);
    return std::system(command.c_str()) == 0 ? 0 : 1;
  }
  if (mode == "network" && argc == 4) {
    int fd = socket(AF_INET, SOCK_STREAM, 0); if (fd < 0) return 2;
    sockaddr_in addr{}; addr.sin_family = AF_INET; addr.sin_port = htons(std::atoi(argv[3]));
    if (inet_pton(AF_INET, argv[2], &addr.sin_addr) != 1) return 3;
    int rc = connect(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)); close(fd);
    return rc == 0 ? 0 : 4;
  }
  if (mode == "write" && argc == 3) {
    std::ofstream stream(argv[2]); stream << "t316"; stream.close();
    return stream.good() ? 0 : 5;
  }
  if (mode == "loop") { for (;;) {} }
  return 65;
}
'''


def observe_s5(profile: SandboxProfile, scratch: Path) -> dict[str, Any]:
    source = scratch / "t316-threats.cc"
    binary = scratch / "t316-threats"
    source.write_text(_THREAT_SOURCE, encoding="utf-8")
    compiler = shutil.which("g++-13") or shutil.which("g++")
    if compiler is None:
        return {category: {"attempted": False, "reason": "C++ compiler unavailable"} for category in S5_CATEGORIES}
    compile_record = _run_command(
        [compiler, "-std=c++17", "-O2", str(source), "-o", str(binary)], timeout_s=120
    )
    if compile_record.get("rc") != 0 or not binary.is_file():
        return {
            category: {"attempted": False, "reason": "threat fixture compilation failed", "compile": compile_record}
            for category in S5_CATEGORIES
        }

    system_marker = scratch / "s5-system-marker"
    file_marker = Path(os.environ.get("HOME", "/nonexistent")) / "t316-s5-write-marker"
    for path in (system_marker, file_marker):
        _cleanup_marker(path)

    system_pair = _paired_command(profile, [str(binary), "system", str(system_marker)])
    system_pair["outside_success"] = system_pair["outside_success"] and system_marker.exists()
    _cleanup_marker(system_marker)

    _, direct_ip, network_port = _network_targets()
    network_pair = _paired_command(
        profile, [str(binary), "network", direct_ip, str(network_port)]
    )
    network_pair["target"] = {"ip": direct_ip, "port": network_port}

    write_pair = _paired_command(profile, [str(binary), "write", str(file_marker)])
    write_pair["outside_success"] = write_pair["outside_success"] and file_marker.exists()
    _cleanup_marker(file_marker)

    outside_loop = _run_command([str(binary), "loop"], timeout_s=1)
    inside_loop = profile.run([str(binary), "loop"], timeout_s=1)
    loop_pair = {
        "attempted": outside_loop.get("executed") is True and inside_loop.get("attempted") is True,
        "outside_success": outside_loop.get("timed_out") is True,
        "inside_blocked": inside_loop.get("timed_out") is True,
        "outside": outside_loop,
        "inside": inside_loop,
    }
    result = {
        "system_command": system_pair,
        "network": network_pair,
        "file_write": write_pair,
        "infinite_loop": loop_pair,
    }
    for observation in result.values():
        observation["fixture"] = {"source_sha256": _sha256_file(source), "binary_sha256": _sha256_file(binary)}
        observation["compile"] = compile_record
    return result


def _git_head(path: Path) -> Optional[str]:
    record = _run_command(
        ["git", "--no-replace-objects", "-C", str(path), "rev-parse", "HEAD"], timeout_s=10
    )
    if record.get("rc") != 0:
        return None
    value = record["stdout"]["tail"].strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def _build_step(
    profile: SandboxProfile, argv: Sequence[str], timeout_s: int
) -> dict[str, Any]:
    return profile.run(argv, timeout_s=timeout_s, build=True)


def _cmake_cache_equals(path: Path, key: str, expected: str) -> bool:
    if not path.is_file():
        return False
    prefix = f"{key}:"
    matches = [
        line.split("=", 1)[1]
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith(prefix) and "=" in line
    ]
    return matches == [expected]


def observe_s6(
    profile: SandboxProfile,
    repo_root: Path,
    scratch: Path,
    policy: Mapping[str, Any],
    deadline_ns: int,
) -> dict[str, Any]:
    minimum_ns = int(policy["stage_budgets_s"]["s6_minimum_remaining_s"]) * 1_000_000_000
    if deadline_ns - time.monotonic_ns() < minimum_ns:
        return {"attempted": False, "reason": "S6 walltime reserve reached"}
    cache_root = Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"]).resolve(strict=True)
    dependency_root = Path(os.environ["IZANAGI_T139_DEPENDENCY_SOURCE_ROOT"]).resolve(strict=True)
    shared_policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    pins = shared_policy["silo_ladder_rung1"]["dependency_pins"]
    third_items = shared_policy["silo_ladder_rung1"]["third_party_sources"]
    source_heads = {
        "gflags": _git_head(dependency_root / "gflags"),
        "glog": _git_head(dependency_root / "glog"),
        **{item["source_name"]: _git_head(cache_root / item["source_name"]) for item in third_items},
    }
    expected_heads = {"gflags": pins["gflags"], "glog": pins["glog"], **{item["source_name"]: item["pin"] for item in third_items}}
    gitlink_record = _run_command(
        ["git", "--no-replace-objects", "-C", str(repo_root), "ls-tree", "HEAD", "external/ccbench"],
        timeout_s=10,
    )
    gitlink_fields = gitlink_record["stdout"]["tail"].strip().split()
    expected_ccbench_head = gitlink_fields[2] if len(gitlink_fields) >= 4 else None
    observed_ccbench_head = _git_head(repo_root / "external/ccbench")
    source_heads["ccbench"] = observed_ccbench_head
    expected_heads["ccbench"] = expected_ccbench_head
    if source_heads != expected_heads:
        return {
            "attempted": True,
            "success": False,
            "trace_disabled": False,
            "failure_stage": "dependency-pins",
            "source_heads": source_heads,
            "expected_heads": expected_heads,
        }

    prefix = scratch / "install"
    gflags_build = scratch / "gflags-build"
    glog_build = scratch / "glog-build"
    ccbench_build = scratch / "ccbench-build-trace0"
    for path in (prefix, gflags_build, glog_build, ccbench_build):
        path.mkdir()
    steps: list[dict[str, Any]] = []
    commands = [
        ("gflags-configure", ["cmake", "-S", str(dependency_root / "gflags"), "-B", str(gflags_build), "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON", "-DREGISTER_INSTALL_PREFIX=OFF", f"-DCMAKE_INSTALL_PREFIX={prefix}"], 180),
        ("gflags-build", ["cmake", "--build", str(gflags_build), "-j", "48"], 300),
        ("gflags-install", ["cmake", "--install", str(gflags_build)], 120),
        ("glog-configure", ["cmake", "-S", str(dependency_root / "glog"), "-B", str(glog_build), "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON", "-DWITH_GTEST=OFF", "-DBUILD_TESTING=OFF", "-DWITH_UNWIND=OFF", f"-DCMAKE_PREFIX_PATH={prefix}", f"-DCMAKE_INSTALL_PREFIX={prefix}"], 180),
        ("glog-build", ["cmake", "--build", str(glog_build), "-j", "48"], 300),
        ("glog-install", ["cmake", "--install", str(glog_build)], 120),
    ]
    source = repo_root / "external/ccbench"
    compiler_c_path = shutil.which("gcc-13") or shutil.which("gcc")
    compiler_cxx_path = shutil.which("g++-13") or shutil.which("g++")
    if compiler_c_path is None or compiler_cxx_path is None or shutil.which("cmake") is None:
        return {
            "attempted": True,
            "success": False,
            "trace_disabled": False,
            "failure_stage": "toolchain",
            "source_heads": source_heads,
            "expected_heads": expected_heads,
        }
    compiler_c = str(Path(compiler_c_path).resolve(strict=True))
    compiler_cxx = str(Path(compiler_cxx_path).resolve(strict=True))
    configure = [
        "cmake", "-S", str(source), "-B", str(ccbench_build),
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF", "-DCCBENCH_TRACE=0",
        "-DCCBENCH_BACK_OFF=0", "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1", "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
        "-DCCBENCH_WAL=0", "-DCCBENCH_CCACHE=OFF", "-DCCBENCH_ADD_ANALYSIS=0",
        "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=", "-DCMAKE_CXX_FLAGS=",
        f"-DCMAKE_PREFIX_PATH={prefix}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={cache_root / 'masstree'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={cache_root / 'mimalloc'}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={cache_root / 'googletest'}",
        f"-DIZANAGI_GFLAGS_SRC_HEAD={pins['gflags']}",
        f"-DIZANAGI_GLOG_SRC_HEAD={pins['glog']}",
        f"-DCMAKE_C_COMPILER={compiler_c}", f"-DCMAKE_CXX_COMPILER={compiler_cxx}",
    ]
    commands.extend((
        ("ccbench-configure", configure, 300),
        ("ccbench-build", ["cmake", "--build", str(ccbench_build), "--target", "ycsb_silo.exe", "-j", "48"], int(policy["stage_budgets_s"]["ccbench_build_cap_s"])),
    ))
    failure_stage: Optional[str] = None
    for label, argv, cap in commands:
        if deadline_ns - time.monotonic_ns() < 30_000_000_000:
            failure_stage = "walltime"
            break
        record = _build_step(profile, argv, min(cap, max(1, int((deadline_ns - time.monotonic_ns()) / 1_000_000_000))))
        steps.append({"label": label, "command": record})
        if record.get("rc") != 0:
            failure_stage = label
            break
    binary = ccbench_build / "cc/silo/ycsb_silo.exe"
    cache = ccbench_build / "CMakeCache.txt"
    trace_disabled = _cmake_cache_equals(cache, "CCBENCH_TRACE", "0")
    return {
        "attempted": True,
        "success": failure_stage is None and binary.is_file() and trace_disabled,
        "failure_stage": failure_stage,
        "trace_disabled": trace_disabled,
        "steps": steps,
        "source_heads": source_heads,
        "expected_heads": expected_heads,
        "binary": str(binary),
        "binary_sha256": _sha256_file(binary) if binary.is_file() else None,
        "cmake_cache_sha256": _sha256_file(cache) if cache.is_file() else None,
    }


def _resolve_perf(repo_root: Path) -> Optional[str]:
    policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    for candidate in policy["perf_candidates"]:
        if Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which("perf")


def observe_s7(
    profile: SandboxProfile,
    repo_root: Path,
    s6: Mapping[str, Any],
    policy: Mapping[str, Any],
    deadline_ns: int,
) -> dict[str, Any]:
    minimum_ns = int(policy["stage_budgets_s"]["s7_minimum_remaining_s"]) * 1_000_000_000
    if deadline_ns - time.monotonic_ns() < minimum_ns:
        return {"attempted": False, "reason": "S7 walltime reserve reached"}
    if s6.get("success") is not True:
        return {"attempted": False, "reason": "S6 trace-disabled build unavailable"}
    perf = _resolve_perf(repo_root)
    numactl = shutil.which("numactl")
    if perf is None or numactl is None:
        return {"attempted": False, "reason": "numactl or perf unavailable"}
    binary = Path(str(s6["binary"])).resolve(strict=True)
    binary_sha = _sha256_file(binary)
    workload = [
        "-ycsb_rmw=true", "-ycsb_zipf_skew=0.9", "-ycsb_tuple_num=10000",
        "-ycsb_max_ope=10", "-thread_num=48", "-extime=3",
    ]
    perf_prefix = [
        numactl, "--physcpubind=0-47", "--membind=0", perf, "stat", "-x,",
        "-e", "cycles,instructions,LLC-loads,LLC-load-misses", "--",
    ]
    outside_argv = [*perf_prefix, str(binary), *workload]
    inside_payload = profile.argv([str(binary), *workload])
    if inside_payload is None:
        return {"attempted": False, "reason": "bwrap unavailable"}
    inside_argv = [*perf_prefix, *inside_payload]
    run_cap = int(policy["stage_budgets_s"]["performance_run_cap_s"])
    outside = _run_command(outside_argv, timeout_s=run_cap)
    inside = _run_command(inside_argv, timeout_s=run_cap)
    outside_elapsed = outside.get("elapsed_ns")
    inside_elapsed = inside.get("elapsed_ns")
    ratio = (
        inside_elapsed / outside_elapsed
        if outside.get("rc") == 0 and inside.get("rc") == 0
        and isinstance(outside_elapsed, int) and outside_elapsed > 0
        and isinstance(inside_elapsed, int)
        else None
    )
    return {
        "attempted": outside.get("executed") is True and inside.get("executed") is True,
        "outside_success": outside.get("rc") == 0,
        "inside_success": inside.get("rc") == 0,
        "same_binary": binary_sha == s6.get("binary_sha256"),
        "trace_disabled": s6.get("trace_disabled") is True,
        "overhead_ratio": ratio,
        "metric_semantics": "sandbox/non-sandbox elapsed ratio; not an absolute CC throughput claim",
        "thread_count": 48,
        "outside": outside,
        "inside": inside,
        "binary": str(binary),
        "binary_sha256": binary_sha,
    }


def _blocked_observation(reason: str, exc: Optional[BaseException] = None) -> dict[str, Any]:
    result: dict[str, Any] = {"attempted": False, "reason": reason}
    if exc is not None:
        result["error"] = _error(exc)
    return result


def _load_policy(repo_root: Path) -> Mapping[str, Any]:
    path = repo_root / "tools/pegasus/policies/t316_sandbox_backend_v1.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping) or value.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise ValueError("invalid T316 policy schema")
    return value


def _git_metadata(repo_root: Path) -> dict[str, Any]:
    head = _run_command(["git", "-C", str(repo_root), "rev-parse", "HEAD"], timeout_s=10)
    status = _run_command(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"], timeout_s=15
    )
    return {"head": head, "status": status}


def run_probe(repo_root: Path, scratch_root: Path) -> tuple[int, dict[str, Any]]:
    job_id = os.environ.get("PBS_JOBID", "")
    if not _JOB_ID_RE.fullmatch(job_id):
        raise ValueError("PBS_JOBID is missing or malformed")
    policy = _load_policy(repo_root)
    started_epoch = int(time.time())
    started_ns = time.monotonic_ns()
    deadline_ns = started_ns + int(policy["probe_deadline_s"]) * 1_000_000_000
    scratch = Path(tempfile.mkdtemp(prefix=f"t316-{job_id.replace(':', '_')}-", dir=scratch_root))
    (scratch / "home").mkdir()
    (scratch / "tmp").mkdir()
    (scratch / "empty-tmp").mkdir(mode=0o555)
    readonly_roots = [
        Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"]),
        Path(os.environ["IZANAGI_T139_DEPENDENCY_SOURCE_ROOT"]),
    ]
    python = str(Path(sys.executable).resolve(strict=True))
    observations: dict[str, Any] = {}
    verdicts: list[StageVerdict] = []
    try:
        try:
            observations["S1"] = observe_s1()
        except Exception as exc:
            observations["S1"] = _blocked_observation("S1 raised", exc)
        verdicts.append(verdict_s1(observations["S1"]))

        bwrap = None
        tools = observations["S1"].get("tools")
        if isinstance(tools, Mapping) and isinstance(tools.get("bwrap"), Mapping):
            bwrap = tools["bwrap"].get("path")
        profile = SandboxProfile(bwrap, repo_root, scratch, readonly_roots)

        for stage, observer, judge in (
            ("S2", lambda: observe_s2(profile, python), verdict_s2),
            ("S3", lambda: observe_s3(profile, python, repo_root, scratch), verdict_s3),
            ("S4", lambda: observe_s4(profile, python, scratch), verdict_s4),
            ("S5", lambda: observe_s5(profile, scratch), verdict_s5),
        ):
            try:
                observations[stage] = observer()
            except Exception as exc:
                observations[stage] = _blocked_observation(f"{stage} raised", exc)
            verdicts.append(judge(observations[stage]))

        try:
            observations["S6"] = observe_s6(profile, repo_root, scratch, policy, deadline_ns)
        except Exception as exc:
            observations["S6"] = _blocked_observation("S6 raised", exc)
        verdicts.append(verdict_s6(observations["S6"]))

        try:
            observations["S7"] = observe_s7(profile, repo_root, observations["S6"], policy, deadline_ns)
        except Exception as exc:
            observations["S7"] = _blocked_observation("S7 raised", exc)
        verdicts.append(verdict_s7(observations["S7"]))

        overall = aggregate_verdicts(verdicts)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "measurement_id": job_id,
            "PBS_JOBID": job_id,
            "started_epoch": started_epoch,
            "finished_epoch": int(time.time()),
            "elapsed_ns": time.monotonic_ns() - started_ns,
            "hostname": socket.gethostname(),
            "repo_root": str(repo_root),
            "policy": policy,
            "git": _git_metadata(repo_root),
            "profile": {
                "backend": "bwrap",
                "runtime_hides_bin_shell": True,
                "network_namespace": "unshared",
                "source_mount": "read-only",
                "scratch_mount": "read-write",
                "environment": "clearenv + explicit minimum",
            },
            "observations": observations,
            "stage_verdicts": [item.as_dict() for item in verdicts],
            "overall_verdict": overall.as_dict(),
            "limitations": [
                "single PBS allocation sample; do not generalize to every gen_S node",
                "S7 is an overhead ratio from one trace-disabled binary, not an absolute CC performance claim",
                "missing external positive controls make their category inconclusive rather than proving containment",
            ],
        }
        return (0 if overall.verdict == "go" else 3), receipt
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _ensure_output_parent(repo_root: Path) -> Path:
    current = repo_root
    for component in ("output", "env", "pegasus", "t316-sandbox-backend"):
        current /= component
        if current.is_symlink():
            raise ValueError(f"receipt path component is a symlink: {current}")
        current.mkdir(exist_ok=True)
        if not current.is_dir() or current.resolve(strict=True).is_relative_to(repo_root) is False:
            raise ValueError(f"receipt path component escapes repository: {current}")
    return current


def _write_receipt_create_only(repo_root: Path, job_id: str, receipt: Mapping[str, Any]) -> Path:
    parent = _ensure_output_parent(repo_root)
    job_dir = parent / job_id
    job_dir.mkdir(mode=0o700, exist_ok=False)
    path = job_dir / "receipt.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve(strict=True)
    scratch_root = args.scratch_root.resolve(strict=True)
    job_id = os.environ.get("PBS_JOBID", "")
    if not _JOB_ID_RE.fullmatch(job_id):
        parser.error("PBS_JOBID is missing or malformed")
    output_dir = repo_root / "output/env/pegasus/t316-sandbox-backend" / job_id
    if output_dir.exists() or output_dir.is_symlink():
        sys.stderr.write(f"create-only receipt namespace already exists: {output_dir}\n")
        return 4
    rc, receipt = run_probe(repo_root, scratch_root)
    try:
        path = _write_receipt_create_only(repo_root, job_id, receipt)
    except FileExistsError:
        sys.stderr.write("create-only receipt collision\n")
        return 4
    sys.stdout.write(json.dumps({"receipt": str(path), "overall_verdict": receipt["overall_verdict"]}, ensure_ascii=False) + "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
