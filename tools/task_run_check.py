#!/usr/bin/env python3
"""Run one fixed repository check and best-effort record its result."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence


_REPO = Path(__file__).resolve().parents[1]
_COMMANDS: dict[str, tuple[str, list[str]]] = {
    "docs-check": ("docs-check", ["python3", "tools/check_docs.py"]),
    "provenance-check": (
        "provenance-check", ["python3", "tools/check_ai_provenance.py"],
    ),
    "static-check": ("static-check", ["python3", "tools/check_codex_agents.py"]),
}
_TRIGGERS = frozenset({
    "baseline", "after-change", "after-failure", "final", "review-fix",
    "unspecified",
})


def _record(suite_kind: str, duration_s: float, exit_status: int) -> None:
    task_run_id = os.environ.get("IZANAGI_TASK_RUN_ID")
    if not task_run_id:
        return
    root = Path(os.environ.get(
        "IZANAGI_TASK_RUNS_ROOT", str(_REPO / "output" / "task-runs"),
    ))
    trigger = os.environ.get("IZANAGI_TEST_TRIGGER", "unspecified")
    if trigger not in _TRIGGERS:
        trigger = "unspecified"
    try:
        if str(_REPO) not in sys.path:
            sys.path.insert(0, str(_REPO))
        from tools.task_runs import record_test_run

        record_test_run(
            root, task_run_id, suite_id=suite_kind, suite_kind=suite_kind,
            duration_s=duration_s, exit_status=exit_status, counts=None,
            trigger=trigger, collected_node_digest=None,
        )
    except Exception:
        pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=tuple(_COMMANDS))
    args = parser.parse_args(argv)
    suite_kind, command = _COMMANDS[args.check]
    task_run_id = os.environ.get("IZANAGI_TASK_RUN_ID")
    if not task_run_id:
        return subprocess.call(command, cwd=_REPO)
    try:
        started = time.monotonic()
    except Exception:
        started = None
    rc = subprocess.call(command, cwd=_REPO)
    if started is not None:
        try:
            duration_s = time.monotonic() - started
        except Exception:
            pass
        else:
            try:
                _record(suite_kind, duration_s, rc)
            except Exception:
                pass
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
