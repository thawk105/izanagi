# probe 逐語 — t1094_floor_probe.py

実体は repo 外 (job tmp)。実装面の `.py` を repo へ入れない規約に従い逐語で貼る。
著者 = Codex author (段 5)。段 6 fix では 1 byte も変更されていない。

```python
#!/usr/bin/env python3
"""T-1094 floor-path probe.

This program is an observational probe.  It does not implement the rejected
floor FetchContent seam and does not publish measurement evidence anywhere
except the create-only JSON path supplied by the PBS wrapper.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterator, Mapping, Sequence


SCHEMA_VERSION = "izanagi-t1094-floor-probe/v1"
TAIL_LIMIT = 4096
PROCESS_KILL_GRACE_S = 10
OVERALL_BUDGET_S = 2520


class ProbeDeadline(RuntimeError):
    """A bounded production call or the overall probe exceeded its deadline."""


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _empty_stream() -> dict[str, object]:
    return {
        "sha256": hashlib.sha256(b"").hexdigest(),
        "bytes": 0,
        "tail": "",
    }


def _stream_summary(handle) -> tuple[dict[str, object], bytes, int]:
    handle.flush()
    handle.seek(0)
    digest = hashlib.sha256()
    total = 0
    tail = b""
    parse_prefix = bytearray()
    newline_count = 0
    final_byte = b""
    while True:
        block = handle.read(1024 * 1024)
        if not block:
            break
        digest.update(block)
        total += len(block)
        newline_count += block.count(b"\n")
        final_byte = block[-1:]
        tail = (tail + block)[-TAIL_LIMIT:]
        if len(parse_prefix) < 1024 * 1024:
            remaining = 1024 * 1024 - len(parse_prefix)
            parse_prefix.extend(block[:remaining])
    line_count = newline_count + int(total > 0 and final_byte != b"\n")
    return (
        {
            "sha256": digest.hexdigest(),
            "bytes": total,
            "tail": tail.decode("utf-8", errors="replace"),
        },
        bytes(parse_prefix),
        line_count,
    )


class CommandRunner:
    """Run every direct subprocess with a timeout and bounded stream receipt."""

    def __init__(self, deadline: float):
        self.deadline = deadline

    def remaining(self) -> float:
        return max(0.0, self.deadline - time.monotonic())

    def run(
        self,
        argv: Sequence[os.PathLike[str] | str],
        *,
        timeout_s: int,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> tuple[dict[str, object], bytes, int]:
        command = [os.fspath(item) for item in argv]
        effective_timeout = min(float(timeout_s), self.remaining())
        record: dict[str, object] = {
            "argv": command,
            "timeout_s": timeout_s,
            "returncode": None,
            "timed_out": False,
            "elapsed_s": 0.0,
            "stdout": _empty_stream(),
            "stderr": _empty_stream(),
        }
        if effective_timeout <= 0:
            record["timed_out"] = True
            record["error"] = "overall-probe-deadline-exhausted-before-spawn"
            return record, b"", 0

        started = time.monotonic()
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            process: subprocess.Popen[bytes] | None = None
            try:
                process = subprocess.Popen(
                    command,
                    cwd=None if cwd is None else os.fspath(cwd),
                    env=None if env is None else dict(env),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    start_new_session=True,
                )
                try:
                    record["returncode"] = process.wait(timeout=effective_timeout)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    try:
                        record["returncode"] = process.wait(
                            timeout=PROCESS_KILL_GRACE_S
                        )
                    except subprocess.TimeoutExpired:
                        record["error"] = "process-did-not-reap-after-kill"
            except OSError as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
            finally:
                record["elapsed_s"] = round(time.monotonic() - started, 6)
                record["stdout"], stdout_prefix, stdout_lines = _stream_summary(
                    stdout_file
                )
                record["stderr"], _, _ = _stream_summary(stderr_file)
        return record, stdout_prefix, stdout_lines


@contextlib.contextmanager
def _alarm_timeout(seconds: int) -> Iterator[None]:
    """Bound production helpers whose internal subprocess API has no timeout."""

    if seconds <= 0:
        raise ProbeDeadline("no time remains for bounded production call")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def deadline_handler(_signum, _frame) -> None:
        raise ProbeDeadline(f"production call exceeded {seconds}s")

    signal.signal(signal.SIGALRM, deadline_handler)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def _bounded_seconds(runner: CommandRunner, requested: int) -> int:
    return max(1, min(requested, int(runner.remaining())))


def _bounded_production_call(
    runner: CommandRunner,
    timeout_s: int,
    function: Callable[..., Any],
    *args: object,
    **kwargs: object,
) -> tuple[Any | None, dict[str, object]]:
    started = time.monotonic()
    receipt: dict[str, object] = {
        "timeout_s": timeout_s,
        "timed_out": False,
        "elapsed_s": 0.0,
    }
    try:
        with _alarm_timeout(_bounded_seconds(runner, timeout_s)):
            value = function(*args, **kwargs)
        receipt["completed"] = True
        return value, receipt
    except ProbeDeadline as exc:
        receipt["completed"] = False
        receipt["timed_out"] = True
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        receipt["completed"] = False
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        receipt["elapsed_s"] = round(time.monotonic() - started, 6)
    return None, receipt


def _decode_line(value: bytes) -> str:
    return value.decode("utf-8", errors="strict").strip()


def _file_receipt(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            total += len(block)
    return {
        "path": str(path.resolve()),
        "exists": True,
        "bytes": total,
        "sha256": digest.hexdigest(),
    }


def _output_snapshot(source_root: Path | None) -> dict[str, object]:
    if source_root is None:
        return {
            "source_root": None,
            "config_h": {"path": None, "exists": False},
            "archive": {"path": None, "exists": False},
        }
    return {
        "source_root": str(source_root),
        "config_h": _file_receipt(source_root / "config.h"),
        "archive": _file_receipt(source_root / "libkohler_masstree_json.a"),
    }


def _generated_entries(build_dir: Path) -> dict[str, object]:
    deps = build_dir / "_deps"
    if not deps.is_dir():
        return {"root": str(deps), "entry_count": 0, "entries": []}
    entries = sorted(item.name for item in deps.iterdir())
    return {"root": str(deps.resolve()), "entry_count": len(entries), "entries": entries}


def _cmake_cache_source_override(build_dir: Path) -> str | None:
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        return None
    prefix = "FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH="
    with cache.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith(prefix):
                value = line[len(prefix):].rstrip("\n")
                return value or None
    return None


def _configured_masstree_root(
    condition: str,
    build_dir: Path,
    local_sources: Mapping[str, Path],
) -> tuple[Path | None, str]:
    override = _cmake_cache_source_override(build_dir)
    if override:
        return Path(override).resolve(), "CMakeCache.txt:FETCHCONTENT_SOURCE_DIR_MASSTREE"
    if condition == "C2" and "masstree" in local_sources:
        return local_sources["masstree"].resolve(), "probe-C2-production-helper-flag"
    candidate = build_dir / "_deps" / "masstree-src"
    if candidate.is_dir():
        return candidate.resolve(), "configured-_deps/masstree-src"
    return None, "not-observed"


def _same_root(lhs: Path, rhs: Path) -> bool:
    try:
        return os.path.samefile(lhs, rhs)
    except OSError:
        return lhs.resolve() == rhs.resolve()


def _git_observation(
    runner: CommandRunner,
    source: Path,
) -> dict[str, object]:
    common = [
        "git", "--no-replace-objects", "-c", "core.fsmonitor=false",
        "-c", "core.hooksPath=/dev/null", "-C", str(source),
    ]
    status, _, status_lines = runner.run(
        common + ["status", "--porcelain", "--untracked-files=all"],
        timeout_s=30,
    )
    ignored, _, ignored_lines = runner.run(
        common + ["ls-files", "--others", "--ignored", "--exclude-standard"],
        timeout_s=30,
    )
    return {
        "source": str(source),
        "status_porcelain_line_count": status_lines,
        "ignored_other_count": ignored_lines,
        "status_command": status,
        "ignored_command": ignored,
        "completed": (
            status.get("returncode") == 0
            and status.get("timed_out") is False
            and ignored.get("returncode") == 0
            and ignored.get("timed_out") is False
        ),
    }


def _build_dependency_prefix(
    runner: CommandRunner,
    *,
    policy: Mapping[str, object],
    scratch: Path,
    cmake: str,
    cc: str,
    cxx: str,
    jobs: int,
) -> tuple[str, dict[str, object]]:
    receipt: dict[str, object] = {"attempted": True, "dependencies": {}}
    installs: dict[str, Path] = {
        "gflags": scratch / "gflags-install",
        "glog": scratch / "glog-install",
    }
    specs = {
        "gflags": {
            "source": Path(str(policy["gflags_source_path"])),
            "pin": str(policy["gflags_expected_head"]),
            "configure": [
                "-DBUILD_SHARED_LIBS=OFF",
                "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
                "-DREGISTER_INSTALL_PREFIX=OFF",
            ],
            "cap": 60,
        },
        "glog": {
            "source": Path(str(policy["glog_source_path"])),
            "pin": str(policy["glog_expected_head"]),
            "configure": [
                "-DBUILD_SHARED_LIBS=OFF",
                "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
                "-DWITH_GTEST=OFF",
                "-DBUILD_TESTING=OFF",
                "-DWITH_UNWIND=OFF",
                f"-DCMAKE_PREFIX_PATH={installs['gflags']}",
            ],
            "cap": 120,
        },
    }
    for name in ("gflags", "glog"):
        spec = specs[name]
        source = spec["source"]
        build = scratch / f"{name}-build"
        install = installs[name]
        item: dict[str, object] = {
            "source": str(source),
            "expected_head": spec["pin"],
            "commands": [],
        }
        receipt["dependencies"][name] = item
        if not source.is_dir():
            item["completed"] = False
            item["error"] = "source-directory-missing"
            continue
        head, head_bytes, _ = runner.run(
            ["git", "--no-replace-objects", "-C", source, "rev-parse", "--verify", "HEAD"],
            timeout_s=30,
        )
        item["commands"].append(head)
        item["observed_head"] = _decode_line(head_bytes) if head.get("returncode") == 0 else None
        configure_argv = [
            cmake, "-S", str(source), "-B", str(build),
            "-DCMAKE_BUILD_TYPE=Release",
            *spec["configure"],
            f"-DCMAKE_INSTALL_PREFIX={install}",
            f"-DCMAKE_C_COMPILER={cc}",
            f"-DCMAKE_CXX_COMPILER={cxx}",
        ]
        commands = (
            (configure_argv, int(spec["cap"])),
            ([cmake, "--build", str(build), "-j", str(jobs)], int(spec["cap"])),
            ([cmake, "--install", str(build)], int(spec["cap"])),
        )
        command_ok = head.get("returncode") == 0 and item["observed_head"] == spec["pin"]
        for argv, cap in commands:
            command, _, _ = runner.run(argv, timeout_s=cap)
            item["commands"].append(command)
            command_ok = command_ok and command.get("returncode") == 0
        item["completed"] = command_ok

    prefix = f"{installs['gflags']};{installs['glog']}"
    receipt["dependency_prefix"] = prefix
    receipt["completed"] = all(
        item.get("completed") is True
        for item in receipt["dependencies"].values()
    )
    return prefix, receipt


def _hydrate_c2_sources(
    runner: CommandRunner,
    *,
    policy_items: Sequence[Mapping[str, object]],
    source_root: Path,
    destination_root: Path,
) -> tuple[list[dict[str, object]], dict[str, Path], dict[str, object]]:
    destination_root.mkdir(mode=0o700, parents=False, exist_ok=False)
    records: list[dict[str, object]] = []
    paths: dict[str, Path] = {}
    receipt: dict[str, object] = {
        "method": "bounded git clone --no-hardlinks --no-checkout plus detached checkout",
        "sources": {},
    }
    git_env = dict(os.environ)
    git_env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PROTOCOL_FROM_USER": "0",
    })
    for policy_item in policy_items:
        name = str(policy_item["name"])
        source_name = str(policy_item["source_name"])
        pin = str(policy_item["pin"])
        source = source_root / source_name
        destination = destination_root / source_name
        paths[name] = destination
        item_receipt: dict[str, object] = {"commands": []}
        receipt["sources"][name] = item_receipt
        clone, _, _ = runner.run(
            [
                "git", "--no-replace-objects", "clone", "--local", "--no-hardlinks",
                "--no-checkout", "-c", "core.hooksPath=/dev/null",
                str(source), str(destination),
            ],
            timeout_s=120,
            env=git_env,
        )
        item_receipt["commands"].append(clone)
        checkout, _, _ = runner.run(
            [
                "git", "--no-replace-objects", "-c", "core.hooksPath=/dev/null",
                "-C", str(destination), "checkout", "--detach", pin,
            ],
            timeout_s=60,
            env=git_env,
        )
        item_receipt["commands"].append(checkout)
        head, head_bytes, _ = runner.run(
            ["git", "--no-replace-objects", "-C", str(destination), "rev-parse", "HEAD"],
            timeout_s=30,
            env=git_env,
        )
        item_receipt["commands"].append(head)
        observed_head = _decode_line(head_bytes) if head.get("returncode") == 0 else None
        item_receipt["observed_head"] = observed_head
        item_receipt["completed"] = (
            clone.get("returncode") == 0
            and checkout.get("returncode") == 0
            and observed_head == pin
        )
        records.append({**dict(policy_item), "resolved_path": str(destination)})
    receipt["completed"] = all(
        item.get("completed") is True for item in receipt["sources"].values()
    )
    return records, paths, receipt


def _condition_configure(
    runner: CommandRunner,
    *,
    condition: str,
    checkout: Path,
    build_dir: Path,
    dependency_prefix: str,
    toolchain: Mapping[str, Mapping[str, str]],
    source_flags: Sequence[str],
    local_sources: Mapping[str, Path],
    buildcache_module: Any,
    genome_class: Any,
) -> dict[str, object]:
    record: dict[str, object] = {"attempted": True, "condition": condition}
    configure_argv, _ = buildcache_module._v2_commands(
        genome_class("silo", {}),
        False,
        str(checkout),
        str(build_dir),
        dict(toolchain),
        jobs=48,
        dependency_prefix=dependency_prefix,
    )
    configure_argv.extend(source_flags)
    record["dependency_prefix_via"] = "orchestrator.campaign.buildcache._v2_commands"
    record["dependency_prefix_token_present"] = (
        f"-DCMAKE_PREFIX_PATH={dependency_prefix}" in configure_argv
    )
    record["source_dir_tokens"] = list(source_flags)
    run_env = dict(os.environ)
    run_env.pop("CMAKE_PREFIX_PATH", None)
    for name in ("MASSTREE", "MIMALLOC", "GOOGLETEST"):
        run_env.pop(f"FETCHCONTENT_SOURCE_DIR_{name}", None)
    command, _, _ = runner.run(configure_argv, timeout_s=300, env=run_env)
    record["command"] = command
    record["deps"] = _generated_entries(build_dir)
    source, origin = _configured_masstree_root(
        condition, build_dir, local_sources
    )
    record["masstree_source_root"] = None if source is None else str(source)
    record["masstree_source_origin"] = origin
    record["completed"] = command.get("returncode") == 0
    return record


def _condition_build(
    runner: CommandRunner,
    *,
    condition: str,
    build_dir: Path,
    masstree_source: Path | None,
    cmake: str,
) -> dict[str, object]:
    before = _output_snapshot(masstree_source)
    command, _, _ = runner.run(
        [cmake, "--build", str(build_dir), "--target", "masstree_build", "-j", "48"],
        timeout_s=420,
    )
    after = _output_snapshot(masstree_source)
    generated = {
        key: (
            before[key].get("exists") is False
            and after[key].get("exists") is True
        )
        for key in ("config_h", "archive")
    }
    return {
        "attempted": True,
        "condition": condition,
        "command": command,
        "source_root": None if masstree_source is None else str(masstree_source),
        "before": before,
        "after": after,
        "generated_by_this_build": generated,
        "completed": (
            command.get("returncode") == 0
            and after["config_h"].get("exists") is True
            and after["archive"].get("exists") is True
            and generated["config_h"] is True
            and generated["archive"] is True
        ),
    }


def _publish_create_only(path: Path, value: Mapping[str, object]) -> None:
    if not path.is_absolute():
        raise ValueError("output path must be absolute")
    parent = path.parent.resolve(strict=True)
    if not parent.is_dir() or path.is_symlink():
        raise ValueError("output parent must be a real directory and output not a symlink")
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(parent / path.name, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)


def _initial_result(args: argparse.Namespace) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "started_at_utc": _utc_now(),
        "finished_at_utc": None,
        "job": {
            "pbs_job_id": os.environ.get("PBS_JOBID"),
            "hostname": socket.gethostname(),
            "repo_root": str(args.repo_root),
            "scratch_root": str(args.scratch_root),
            "expected_commit": args.expected_commit,
        },
        "budget": {
            "pbs_walltime_s": 2700,
            "probe_internal_budget_s": OVERALL_BUDGET_S,
            "basis": {
                "t139_r4_observed_complete_s": 614.046,
                "t139_r4_observed_ccbench_configure_s": [1.484, 1.523],
                "t139_r4_observed_ccbench_build_s": [14.001, 4.585],
                "t316_observed_complete_s": [99.417, 85.165],
                "t419_observed_complete_s": [6.0, 32.0, 90.0, 93.0],
                "independent_reason": (
                    "2700s is a probe-only envelope: two 300s configure caps, "
                    "two 420s masstree caps, bounded dependency builds and clones, "
                    "plus finalization reserve; it is not derived from floor_walltime_s"
                ),
            },
        },
        "production_modules": {},
        "simulation_vs_production": {
            "mocked": False,
            "differences": [
                (
                    "C2 is probe orchestration: it uses the existing production "
                    "silo_ladder_rung1._third_party_configure_flags helper, because "
                    "the floor/buildcache SOURCE_DIR seam was rejected and is absent"
                ),
                (
                    "job-local C2 sources are bounded fresh Git clones made by this "
                    "probe; production floor code is not changed to consume them"
                ),
                (
                    "patchharness.checkout and the floor dependency resolver are real "
                    "production helpers; their internal commands lack native timeout "
                    "parameters, so the probe wraps entry and cleanup in signal deadlines"
                ),
            ],
        },
        "input_identity": {},
        "root_comparison": {"attempted": False, "completed": False},
        "shared_source_pollution": {"attempted": False, "completed": False},
        "oracle_resolver": {"attempted": False, "completed": False},
        "dependency_prefix_setup": {"attempted": False, "completed": False},
        "cmake_configure": {
            "attempted": False,
            "completed": False,
            "conditions": {
                "C1": {"attempted": False, "completed": False},
                "C2": {"attempted": False, "completed": False},
            },
        },
        "masstree_build": {
            "attempted": False,
            "completed": False,
            "conditions": {
                "C1": {"attempted": False, "completed": False},
                "C2": {"attempted": False, "completed": False},
            },
        },
        "all_pass": False,
        "fatal_error": None,
    }


def run_probe(args: argparse.Namespace, result: dict[str, object]) -> None:
    repo_root = args.repo_root.resolve(strict=True)
    scratch = args.scratch_root.resolve(strict=True)
    deadline = time.monotonic() + OVERALL_BUDGET_S
    runner = CommandRunner(deadline)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from orchestrator.campaign import buildcache
    from orchestrator.campaign import patchharness
    from orchestrator.campaign import s8b_floor_campaign
    from orchestrator.campaign import silo_ladder_rung1
    from orchestrator.campaign import sort_swo_oracle
    from orchestrator.campaign.model import Genome

    modules = result["production_modules"]
    for name, module in (
        ("orchestrator.campaign.sort_swo_oracle", sort_swo_oracle),
        ("orchestrator.campaign.patchharness", patchharness),
        ("orchestrator.campaign.buildcache", buildcache),
        ("orchestrator.campaign.s8b_floor_campaign", s8b_floor_campaign),
        ("orchestrator.campaign.silo_ladder_rung1", silo_ladder_rung1),
    ):
        modules[name] = str(Path(module.__file__).resolve())

    observed_head_cmd, observed_head_bytes, _ = runner.run(
        ["git", "--no-replace-objects", "-C", repo_root, "rev-parse", "--verify", "HEAD"],
        timeout_s=30,
    )
    observed_head = (
        _decode_line(observed_head_bytes)
        if observed_head_cmd.get("returncode") == 0
        else None
    )
    gitlink_cmd, gitlink_bytes, _ = runner.run(
        [
            "git", "--no-replace-objects", "-C", repo_root,
            "rev-parse", "--verify", "HEAD:external/ccbench",
        ],
        timeout_s=30,
    )
    gitlink = _decode_line(gitlink_bytes) if gitlink_cmd.get("returncode") == 0 else None
    result["input_identity"] = {
        "observed_head": observed_head,
        "head_matches_expected": observed_head == args.expected_commit,
        "ccbench_gitlink": gitlink,
        "repo_head_command": observed_head_cmd,
        "ccbench_gitlink_command": gitlink_cmd,
    }

    policy_path = repo_root / "tools" / "pegasus" / "policy.json"
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = json.load(handle)
    policy_items = silo_ladder_rung1.third_party_policy(repo_root)

    cache_root = args.cache_root.resolve(strict=True)
    source_root = args.source_root.resolve(strict=True)
    floor_binding, floor_receipt = _bounded_production_call(
        runner,
        60,
        s8b_floor_campaign._resolve_floor_oracle_dependency,
        cache_root,
        repo_root=repo_root,
    )
    root_comparison = result["root_comparison"]
    root_comparison.update({
        "attempted": True,
        "floor_resolver_call": floor_receipt,
        "oracle_dependency_root": (
            str(floor_binding.source_root) if floor_binding is not None else None
        ),
        "configure_source_root": None,
        "same_root": None,
    })

    pollution = result["shared_source_pollution"]
    pollution["attempted"] = True
    pollution["roots"] = {}
    pollution_ok = True
    try:
        for label, root in (("cache", cache_root), ("staging", source_root)):
            root_record: dict[str, object] = {"root": str(root), "sources": {}}
            pollution["roots"][label] = root_record
            for item in policy_items:
                name = str(item["name"])
                observation = _git_observation(
                    runner, root / str(item["source_name"])
                )
                root_record["sources"][name] = observation
                pollution_ok = pollution_ok and observation["completed"] is True
        pollution["completed"] = pollution_ok
    except Exception as exc:
        pollution["completed"] = False
        pollution["error"] = f"{type(exc).__name__}: {exc}"

    cmake = shutil.which("cmake")
    cc = shutil.which("gcc")
    cxx = shutil.which("g++")
    if not cmake or not cc or not cxx:
        raise RuntimeError("cmake/gcc/g++ must all resolve on the compute node")
    toolchain = {
        "cmake": {"realpath": str(Path(cmake).resolve())},
        "cc": {"realpath": str(Path(cc).resolve())},
        "cxx": {"realpath": str(Path(cxx).resolve())},
    }

    checkout_manager = None
    checkout_path: Path | None = None
    try:
        if gitlink is None:
            raise RuntimeError("ccbench gitlink could not be resolved")
        checkout_manager = patchharness.checkout(
            gitlink, base_dir=str(repo_root / "external" / "ccbench")
        )
        with _alarm_timeout(_bounded_seconds(runner, 120)):
            checkout_path = Path(checkout_manager.__enter__()).resolve(strict=True)
        if scratch not in checkout_path.parents:
            raise RuntimeError("patchharness checkout is outside the job scratch root")

        oracle = result["oracle_resolver"]
        oracle["attempted"] = True
        oracle_value, oracle_call = _bounded_production_call(
            runner,
            60,
            sort_swo_oracle.resolve_oracle_environment,
            checkout_path,
            compiler=toolchain["cxx"]["realpath"],
            dependency_root=cache_root / "masstree",
        )
        oracle["call"] = oracle_call
        if oracle_call.get("completed") is True:
            if oracle_value is None:
                oracle["exact_result"] = "None"
                oracle["completed"] = True
            elif type(oracle_value) is sort_swo_oracle.OracleEnvironment:
                oracle["exact_result"] = "OracleEnvironment"
                oracle["value"] = {
                    "compiler": str(oracle_value.compiler),
                    "ccbench_dir": str(oracle_value.ccbench_dir),
                    "dependency_root": str(oracle_value.dependency_root),
                }
                oracle["completed"] = True
            elif type(oracle_value) is sort_swo_oracle.OracleEnvironmentResolutionFailure:
                oracle["exact_result"] = "OracleEnvironmentResolutionFailure"
                oracle["value"] = oracle_value.private_dict()
                oracle["completed"] = True
            else:
                oracle["exact_result"] = f"unexpected:{type(oracle_value).__qualname__}"
                oracle["completed"] = False
        oracle["passed"] = oracle.get("exact_result") == "OracleEnvironment"

        dependency_prefix = (
            f"{scratch / 'gflags-install'};{scratch / 'glog-install'}"
        )
        try:
            dependency_prefix, dependency_receipt = _build_dependency_prefix(
                runner,
                policy=policy,
                scratch=scratch,
                cmake=toolchain["cmake"]["realpath"],
                cc=toolchain["cc"]["realpath"],
                cxx=toolchain["cxx"]["realpath"],
                jobs=48,
            )
            result["dependency_prefix_setup"] = dependency_receipt
        except Exception as exc:
            result["dependency_prefix_setup"] = {
                "attempted": True,
                "completed": False,
                "dependency_prefix": dependency_prefix,
                "error": f"{type(exc).__name__}: {exc}",
            }

        c2_root = scratch / "c2-third-party-sources"
        c2_paths = {
            str(item["name"]): c2_root / str(item["source_name"])
            for item in policy_items
        }
        c2_records = [
            {**dict(item), "resolved_path": str(c2_paths[str(item["name"])])}
            for item in policy_items
        ]
        try:
            c2_records, c2_paths, c2_hydration = _hydrate_c2_sources(
                runner,
                policy_items=policy_items,
                source_root=source_root,
                destination_root=c2_root,
            )
        except Exception as exc:
            c2_hydration = {
                "completed": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        source_flags = silo_ladder_rung1._third_party_configure_flags(c2_records)

        configure = result["cmake_configure"]
        configure["attempted"] = True
        configure["c2_source_hydration"] = c2_hydration
        build_dirs = {
            "C1": scratch / "ccbench-c1-build",
            "C2": scratch / "ccbench-c2-build",
        }
        local_sources: dict[str, Mapping[str, Path]] = {"C1": {}, "C2": c2_paths}
        for condition in ("C1", "C2"):
            try:
                configure["conditions"][condition] = _condition_configure(
                    runner,
                    condition=condition,
                    checkout=checkout_path,
                    build_dir=build_dirs[condition],
                    dependency_prefix=dependency_prefix,
                    toolchain=toolchain,
                    source_flags=() if condition == "C1" else source_flags,
                    local_sources=local_sources[condition],
                    buildcache_module=buildcache,
                    genome_class=Genome,
                )
            except Exception as exc:
                configure["conditions"][condition] = {
                    "attempted": True,
                    "completed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
        configure["completed"] = all(
            configure["conditions"][condition].get("completed") is True
            for condition in ("C1", "C2")
        )

        c1_record = configure["conditions"]["C1"]
        c1_source_text = c1_record.get("masstree_source_root")
        c1_source = Path(c1_source_text) if isinstance(c1_source_text, str) else None
        root_comparison["configure_source_root"] = c1_source_text
        root_comparison["configure_source_origin"] = c1_record.get("masstree_source_origin")
        if floor_binding is not None and c1_source is not None:
            root_comparison["same_root"] = _same_root(
                floor_binding.source_root, c1_source
            )
            root_comparison["completed"] = True

        builds = result["masstree_build"]
        builds["attempted"] = True
        for condition in ("C1", "C2"):
            configure_record = configure["conditions"][condition]
            source_text = configure_record.get("masstree_source_root")
            source = Path(source_text) if isinstance(source_text, str) else None
            try:
                builds["conditions"][condition] = _condition_build(
                    runner,
                    condition=condition,
                    build_dir=build_dirs[condition],
                    masstree_source=source,
                    cmake=toolchain["cmake"]["realpath"],
                )
            except Exception as exc:
                builds["conditions"][condition] = {
                    "attempted": True,
                    "completed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
        builds["completed"] = all(
            builds["conditions"][condition].get("completed") is True
            for condition in ("C1", "C2")
        )
    finally:
        if checkout_manager is not None and checkout_path is not None:
            cleanup_started = time.monotonic()
            try:
                with _alarm_timeout(_bounded_seconds(runner, 120)):
                    checkout_manager.__exit__(None, None, None)
                result["input_identity"]["checkout_cleanup"] = {
                    "completed": True,
                    "elapsed_s": round(time.monotonic() - cleanup_started, 6),
                }
            except Exception as exc:
                result["input_identity"]["checkout_cleanup"] = {
                    "completed": False,
                    "elapsed_s": round(time.monotonic() - cleanup_started, 6),
                    "error": f"{type(exc).__name__}: {exc}",
                }

    configure = result["cmake_configure"]
    builds = result["masstree_build"]
    result["all_pass"] = (
        result["input_identity"].get("head_matches_expected") is True
        and result["root_comparison"].get("attempted") is True
        and result["root_comparison"].get("completed") is True
        and result["shared_source_pollution"].get("attempted") is True
        and result["shared_source_pollution"].get("completed") is True
        and result["oracle_resolver"].get("attempted") is True
        and result["oracle_resolver"].get("passed") is True
        and result["dependency_prefix_setup"].get("completed") is True
        and configure.get("attempted") is True
        and configure.get("completed") is True
        and configure.get("c2_source_hydration", {}).get("completed") is True
        and builds.get("attempted") is True
        and builds.get("completed") is True
        and (
            result["input_identity"].get("checkout_cleanup", {}).get("completed")
            is True
        )
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if len(args.expected_commit) != 40 or any(
        char not in "0123456789abcdef" for char in args.expected_commit
    ):
        parser.error("--expected-commit must be 40 lowercase hexadecimal characters")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    result = _initial_result(args)

    def terminate(_signum, _frame) -> None:
        raise ProbeDeadline("probe received termination signal")

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        run_probe(args, result)
    except BaseException as exc:
        result["fatal_error"] = f"{type(exc).__name__}: {exc}"
        result["all_pass"] = False
    finally:
        result["finished_at_utc"] = _utc_now()
        _publish_create_only(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
