#!/usr/bin/env python3
"""CLI and runner seam for synchronous Pegasus pytest dispatch."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Mapping, Sequence

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
import pegasus_policy

if __package__:
    from . import test_dispatch
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_dispatch


_INTERPRETER_CANDIDATES = (
    Path("/usr/local/bin/python3.10"),
    Path("/usr/bin/python3.10"),
    Path("/usr/local/bin/python3"),
    Path("/usr/bin/python3"),
    Path("/bin/python3"),
)
_DEPENDENCY_PROBE = (
    "import importlib.metadata as m,sys; import pytest,xdist; "
    "raise SystemExit(0 if sys.version_info >= (3,10) "
    "and m.version('pytest') and m.version('pytest-xdist') else 125)"
)


def select_dependency_interpreter(
    candidates: Sequence[Path],
    *,
    run=subprocess.run,
) -> Path:
    probe_environment = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    seen: set[Path] = set()
    for lexical in candidates:
        try:
            candidate = lexical.resolve(strict=True)
        except OSError:
            continue
        if candidate in seen or not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        seen.add(candidate)
        try:
            completed = run(
                [str(candidate), "-B", "-s", "-c", _DEPENDENCY_PROBE],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=probe_environment,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode == 0:
            return candidate
    raise test_dispatch.DispatchError(
        "no Python >=3.10 interpreter has same-interpreter pytest/xdist"
    )


def _ensure_dependency_interpreter() -> None:
    current = Path(sys.executable).resolve(strict=True)
    selected = select_dependency_interpreter((Path(sys.executable), *_INTERPRETER_CANDIDATES))
    if selected == current:
        return
    environment = {
        name: value for name, value in os.environ.items()
        if name in {
            "PATH", "LANG", "LC_ALL", "TZ", "PYTHONNOUSERSITE",
            "PYTHONDONTWRITEBYTECODE", "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
            "PIP_NO_INDEX", "PIP_DISABLE_PIP_VERSION_CHECK", "PBS_JOBID",
            "IZANAGI_TEST_DISPATCH_ID", "IZANAGI_TEST_DISPATCH_DIR",
            "IZANAGI_TEST_SNAPSHOT_ROOT", "IZANAGI_TEST_WORKER_AUTH",
            "IZANAGI_TEST_RUNNER_RESULT",
        }
    }
    environment["PYTHONNOUSERSITE"] = "1"
    os.execve(
        str(selected),
        [str(selected), "-B", "-s", str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def _distribution_receipt(name: str) -> dict[str, str]:
    try:
        distribution = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        raise test_dispatch.DispatchError(
            f"same-interpreter dependency is missing: {name}"
        ) from None
    root = Path(distribution.locate_file("")).resolve(strict=True)
    files = distribution.files
    if not files:
        raise test_dispatch.DispatchError(
            f"same-interpreter dependency has no file inventory: {name}"
        )
    digest = hashlib.sha256()
    count = 0
    total_bytes = 0
    for package_path in sorted(files, key=str):
        candidate = Path(distribution.locate_file(package_path))
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            raise test_dispatch.DispatchError(
                f"dependency file escapes distribution root: {name}: {package_path}"
            ) from None
        if not resolved.is_file():
            continue
        info = resolved.stat()
        if info.st_size > 64 * 1024 * 1024:
            raise test_dispatch.DispatchError(
                f"dependency file exceeds receipt bound: {name}: {package_path}"
            )
        total_bytes += info.st_size
        if total_bytes > 512 * 1024 * 1024 or count >= 20_000:
            raise test_dispatch.DispatchError(
                f"dependency inventory exceeds receipt bound: {name}"
            )
        digest.update(str(package_path).encode("utf-8"))
        digest.update(b"\0")
        with resolved.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        after = resolved.stat()
        if (
            after.st_dev != info.st_dev
            or after.st_ino != info.st_ino
            or after.st_size != info.st_size
            or after.st_mode != info.st_mode
        ):
            raise test_dispatch.DispatchError(
                f"dependency file changed while hashing: {name}: {package_path}"
            )
        digest.update(b"\0")
        count += 1
    if count == 0:
        raise test_dispatch.DispatchError(
            f"same-interpreter dependency has no regular files: {name}"
        )
    return {
        "name": name,
        "version": distribution.version,
        "root": str(root),
        "distribution_files": str(count),
        "distribution_files_sha256": digest.hexdigest(),
    }


def _write_worker_environment(
    dispatch_dir: Path,
    observation: pegasus_policy.SiteObservation,
    *,
    snapshot: test_dispatch.Snapshot,
    environment: Mapping[str, str],
) -> str:
    if sys.version_info < (3, 10):
        raise test_dispatch.DispatchError("compute worker requires Python >= 3.10")
    pytest_receipt = _distribution_receipt("pytest")
    xdist_receipt = _distribution_receipt("pytest-xdist")
    document = {
        "schema": "izanagi-test-worker-environment-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "python_executable": sys.executable,
        "python_realpath": str(Path(sys.executable).resolve(strict=True)),
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "python_flags": ["-B", "-s"],
        "sys_path": list(sys.path),
        "pytest_plugin_autoload": False,
        "environment": dict(sorted(environment.items())),
        "pytest": pytest_receipt,
        "pytest_xdist": xdist_receipt,
        "site": {
            "hostname_raw": observation.hostname_raw,
            "hostname_canonical": observation.hostname_canonical,
            "pbs_job_id_raw": observation.pbs_job_id_raw,
            "pbs_job_id_normalized": observation.pbs_job_id_normalized,
            "affinity_cpus": list(observation.affinity_cpus),
            "site_kind": observation.site_kind.value,
        },
    }
    raw = test_dispatch._canonical_json(document)
    test_dispatch.create_file(
        dispatch_dir / "worker-environment.json",
        raw,
    )
    return test_dispatch.sha256_bytes(raw)


def _closed_worker_environment(
    *,
    snapshot: test_dispatch.Snapshot,
    marker_path: Path,
    observation: pegasus_policy.SiteObservation,
) -> dict[str, str]:
    path = os.environ.get("PATH", "")
    if (
        not path
        or "\x00" in path
        or "\n" in path
        or "\r" in path
    ):
        raise test_dispatch.DispatchError("worker PATH is unavailable or unsafe")
    environment = {
        "PATH": path,
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PIP_NO_INDEX": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PBS_JOBID": str(observation.pbs_job_id_raw),
        "IZANAGI_TEST_DISPATCH_ID": snapshot.dispatch_id,
        "IZANAGI_TEST_DISPATCH_DIR": str(snapshot.dispatch_dir),
        "IZANAGI_TEST_SNAPSHOT_ROOT": str(snapshot.snapshot_root),
        "IZANAGI_TEST_WORKER_AUTH": str(marker_path),
        "IZANAGI_TEST_RUNNER_RESULT": str(
            snapshot.dispatch_dir / "runner-result.json"
        ),
    }
    environment.update(snapshot.runner_environment)
    if any(
        not isinstance(name, str)
        or not isinstance(value, str)
        or "\x00" in name
        or "\x00" in value
        for name, value in environment.items()
    ):
        raise test_dispatch.DispatchError("closed worker environment is invalid")
    return environment


def _wait_for_submit_receipt(
    dispatch_dir: Path,
    *,
    timeout_s: int,
    clock=time.monotonic,
    sleep=time.sleep,
) -> None:
    deadline = clock() + timeout_s
    receipt = dispatch_dir / "submit-receipt.json"
    while clock() <= deadline:
        if receipt.is_file() and not receipt.is_symlink():
            return
        sleep(0.1)
    raise test_dispatch.DispatchError("submit receipt visibility timeout")


def worker(
    *,
    dispatch_id: str,
    dispatch_dir: Path,
    snapshot_root: Path,
    marker_path: Path,
) -> int:
    snapshot = test_dispatch.snapshot_from_dispatch(dispatch_dir)
    if snapshot.dispatch_id != dispatch_id:
        raise test_dispatch.DispatchError("worker dispatch ID mismatch")
    if snapshot.snapshot_root != snapshot_root.resolve(strict=True):
        raise test_dispatch.DispatchError("worker snapshot root mismatch")
    if marker_path.resolve(strict=True) != (
        snapshot.dispatch_dir / "pre-submit-authorization.json"
    ):
        raise test_dispatch.DispatchError("worker authorization path mismatch")
    result_env = os.environ.get("IZANAGI_TEST_RUNNER_RESULT")
    if (
        not result_env
        or Path(result_env).resolve(strict=False)
        != snapshot.dispatch_dir / "runner-result.json"
    ):
        raise test_dispatch.DispatchError("worker result path mismatch")
    policy = test_dispatch.load_policy(
        snapshot.snapshot_root
        / "tools"
        / "pegasus"
        / "test_dispatch_policy.json"
    )
    if policy.policy_sha256 != snapshot.policy_sha256:
        raise test_dispatch.DispatchError("worker policy differs from snapshot")
    test_dispatch.verify_snapshot_tree(snapshot, policy)
    test_dispatch.verify_execution_closure(snapshot)
    _wait_for_submit_receipt(
        dispatch_dir,
        timeout_s=policy.visibility_grace_s,
    )
    observation = pegasus_policy.observe_site()
    environment = _closed_worker_environment(
        snapshot=snapshot,
        marker_path=marker_path,
        observation=observation,
    )
    worker_environment_sha = _write_worker_environment(
        dispatch_dir,
        observation,
        snapshot=snapshot,
        environment=environment,
    )
    test_dispatch.claim_worker(
        marker_path=marker_path,
        observation=observation,
        repo_root=snapshot_root,
        worker_environment_sha256=worker_environment_sha,
    )
    argv = test_dispatch.resolve_pytest_argv(
        snapshot.encoded_argv,
        snapshot.snapshot_root,
    )
    runner = snapshot.snapshot_root / "tools" / "run_tests.py"
    if not runner.is_file() or runner.is_symlink():
        raise test_dispatch.DispatchError("snapshot runner is unavailable")
    # This is the last source-tree check before control crosses into the test
    # runner.  Dispatch receipts live beside ``source`` and cannot perturb it.
    test_dispatch.verify_snapshot_tree(snapshot, policy)
    test_dispatch.verify_execution_closure(snapshot)
    command = [sys.executable, "-B", "-s", str(runner), *argv]
    os.execve(sys.executable, command, environment)
    raise AssertionError("os.execve returned")


def dispatch_from_runner(
    *,
    raw_args: Sequence[str],
    source_root: Path,
    caller_cwd: Path,
    scheduler: test_dispatch.Scheduler | None = None,
) -> int:
    policy = test_dispatch.load_policy()
    selected_scheduler = scheduler or test_dispatch.SubprocessScheduler(
        max_output_bytes=policy.max_scheduler_output_bytes,
    )
    snapshot = test_dispatch.create_snapshot(
        source_root=source_root,
        caller_cwd=caller_cwd,
        raw_args=raw_args,
        policy=policy,
        scheduler=selected_scheduler,
    )
    return test_dispatch.submit_and_monitor(
        snapshot=snapshot,
        scheduler=selected_scheduler,
        policy=policy,
        job_script=(
            snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
        ),
    )


def _dispatch_dir(source_root: Path, dispatch_id: str) -> Path:
    policy = test_dispatch.load_policy()
    if test_dispatch._DISPATCH_ID_RE.fullmatch(dispatch_id) is None:
        raise test_dispatch.DispatchError("dispatch ID is invalid")
    root = source_root.resolve(strict=True).parent / policy.dispatch_root_name
    candidate = root / dispatch_id
    resolved = candidate.resolve(strict=True)
    if resolved.parent != root.resolve(strict=True):
        raise test_dispatch.DispatchError("dispatch directory escapes root")
    return resolved


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Izanagi synchronous Pegasus pytest dispatcher",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    resume = subparsers.add_parser("resume")
    resume.add_argument("--dispatch-id", required=True)
    resume.add_argument("--source-root", type=Path, required=True)
    worker_parser = subparsers.add_parser("worker")
    worker_parser.add_argument("--dispatch-id", required=True)
    worker_parser.add_argument("--dispatch-dir", type=Path, required=True)
    worker_parser.add_argument("--snapshot-root", type=Path, required=True)
    worker_parser.add_argument("--marker", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "resume":
            policy = test_dispatch.load_policy()
            return test_dispatch.resume_dispatch(
                dispatch_dir=_dispatch_dir(args.source_root, args.dispatch_id),
                scheduler=test_dispatch.SubprocessScheduler(
                    max_output_bytes=policy.max_scheduler_output_bytes,
                ),
                policy=policy,
            )
        _ensure_dependency_interpreter()
        return worker(
            dispatch_id=args.dispatch_id,
            dispatch_dir=args.dispatch_dir,
            snapshot_root=args.snapshot_root,
            marker_path=args.marker,
        )
    except test_dispatch.DispatchError as exc:
        print(f"test dispatch error: {exc}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
