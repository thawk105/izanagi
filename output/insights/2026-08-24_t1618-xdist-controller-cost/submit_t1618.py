#!/usr/bin/env python3
"""Submit the pure-Python T-1618 harness through the closed tests task."""
from __future__ import annotations

import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN_BASE = (REPO / "output/runs/t1618-xdist-controller-cost").resolve()


def main() -> int:
    if Path.cwd().resolve() != REPO:
        print(f"run from repository root: {REPO}", file=sys.stderr)
        return 2
    os.environ.pop("PYTHONPATH", None)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import tools.pegasus.dispatch_compute as dispatcher

    module_path = Path(dispatcher.__file__).resolve()
    if not module_path.is_relative_to((REPO / "tools").resolve()):
        print(f"dispatcher import escaped repository tools/: {module_path}", file=sys.stderr)
        return 2

    if set(dispatcher.TASKS) != {"tests", "provenance"}:
        print(f"dispatcher task schema changed: {sorted(dispatcher.TASKS)!r}", file=sys.stderr)
        return 2
    attempt_id = (
        "attempt-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + f"-{os.getpid()}-{secrets.token_hex(4)}"
    )
    attempt_root = RUN_BASE / attempt_id
    tests_spec = dispatcher.TASKS["tests"]
    required_environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "IZANAGI_TASK_RUN_AUTO_RECORD": "0",
    }
    if not set(required_environment) <= tests_spec.env_allowlist:
        print("dispatcher no longer transports the required child environment", file=sys.stderr)
        return 2
    environment = dict(os.environ)
    for name in tests_spec.env_allowlist:
        environment.pop(name, None)
    environment.update(required_environment)
    environment.pop("PYTHONPATH", None)
    args = [
        "-n", "0",
        "-p", "no:cacheprovider",
        f"--basetemp={attempt_root / 'pytest-tmp'}",
        "-q",
        "-s",
        str(HERE / "test_t1618_entrypoint.py"),
    ]
    print(f"T-1618 attempt_id={attempt_id} run_root={attempt_root}")
    return int(dispatcher.dispatch(
        args,
        task="tests",
        repo_root=REPO,
        environ=environment,
        output_root=attempt_root / "dispatch",
        walltime="03:00:00",
        queue_wait_timeout_s=900.0,
        overall_grace_s=600.0,
        accounting_grace_s=120.0,
    ))


if __name__ == "__main__":
    raise SystemExit(main())
