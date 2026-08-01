#!/usr/bin/env python3
"""T-136 preservation controls required by the T-145 wave."""
from __future__ import annotations

import fcntl
import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("preservation-results.json")
LOCK = Path(__file__).with_name("preservation.lock")


@dataclass(frozen=True)
class Control:
    control_id: str
    path: str
    old: str
    new: str
    node: str
    signature: str


BASE = (
    "orchestrator/tests/test_dev_waves_integration.py::"
)
CONTROLS = (
    Control(
        "PM1", "tools/dev_waves/worker.py",
        "        if timed_out:\n"
        "            reason = ReasonCode.TIMEOUT\n",
        "        if False and timed_out:\n"
        "            reason = ReasonCode.TIMEOUT\n",
        BASE + "test_child_failure_injection_stops_before_next_wave"
        "[sleep_timeout-timeout]",
        "ReasonCode.NONZERO_EXIT vs ReasonCode.TIMEOUT",
    ),
    Control(
        "PM2", "tools/dev_waves/daemon.py",
        "        if remaining_ns <= 0:\n",
        "        if remaining_ns < 0:\n",
        BASE + "test_expired_deadline_prevents_next_real_artifact_side_effect",
        "DID NOT RAISE DevWavesError",
    ),
    Control(
        "PM3", "tools/dev_waves/worker.py",
        "        elif limited:\n"
        "            reason = ReasonCode.LOG_LIMIT\n",
        "        elif False and limited:\n"
        "            reason = ReasonCode.LOG_LIMIT\n",
        BASE + "test_child_failure_injection_stops_before_next_wave"
        "[log_cap-log-limit]",
        "ReasonCode.NONZERO_EXIT vs ReasonCode.LOG_LIMIT",
    ),
    Control(
        "PM4v2", "tools/dev_waves/worker.py",
        "        residual = bool(_group_members(identity.pid))\n",
        "        residual = False\n",
        BASE + "test_child_failure_injection_stops_before_next_wave"
        "[grandchild_residual-nonzero-exit]",
        "RunState.COMPLETED vs RunState.FAILED",
    ),
)


def run(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, check=False, timeout=timeout,
    )


def committed(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def restore(path: str, original: bytes) -> None:
    subprocess.run(
        ["git", "checkout", "--", path], cwd=ROOT,
        stdin=subprocess.DEVNULL, check=True,
    )
    if (ROOT / path).read_bytes() != original:
        raise RuntimeError(f"{path}: restore differs from integrated HEAD")
    if run("git", "diff", "--", path).stdout:
        raise RuntimeError(f"{path}: tracked diff remains after restore")


def main() -> int:
    if run("git", "diff", "--name-only").stdout:
        raise RuntimeError("tracked worktree must be clean")
    lock = LOCK.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("another preservation harness holds the lock")

    rows: list[dict[str, object]] = []
    for control in CONTROLS:
        path = ROOT / control.path
        original = committed(control.path)
        source = original.decode("utf-8")
        count = source.count(control.old)
        if count != 1:
            raise RuntimeError(
                f"{control.control_id}: anchor count {count}, expected 1",
            )
        mutated = source.replace(control.old, control.new, 1)
        path.write_text(mutated, encoding="utf-8")
        diff = run("git", "diff", "--numstat", "--", control.path)
        if run("git", "diff", "--name-only").stdout.splitlines() != [control.path]:
            restore(control.path, original)
            raise RuntimeError(f"{control.control_id}: non-single mutation")
        started = time.monotonic()
        timed_out = False
        try:
            test = run(
                sys.executable, "-m", "pytest", "-q", "-rf", control.node,
                timeout=90,
            )
            rc = test.returncode
            output = test.stdout
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            rc = None
            output = exc.stdout if isinstance(exc.stdout, str) else ""
        finally:
            restore(control.path, original)
        failed_nodes = re.findall(
            r"^FAILED (\S+)(?: - .*)?$", output, re.MULTILINE,
        )
        observed = (
            "INFRA_TIMEOUT_NOT_EVIDENCE" if timed_out
            else "SURVIVED" if rc == 0
            else "KILLED"
        )
        rows.append({
            "id": control.control_id,
            "expected": "KILLED",
            "observed": observed,
            "rc": rc,
            "timed_out": timed_out,
            "elapsed_s": round(time.monotonic() - started, 3),
            "node": control.node,
            "failed_nodes": failed_nodes,
            "expected_signature": control.signature,
            "diff_numstat": diff.stdout.strip(),
            "mutated_sha256": hashlib.sha256(
                mutated.encode("utf-8"),
            ).hexdigest(),
            "output_tail": "\n".join(output.splitlines()[-35:]),
            "restored_to_head": True,
        })
        print(
            control.control_id, observed, f"rc={rc}",
            f"elapsed={rows[-1]['elapsed_s']}s", flush=True,
        )

    OUT.write_text(
        json.dumps({
            "schema_version": 1,
            "integrated_commit": run("git", "rev-parse", "HEAD").stdout.strip(),
            "source_contract": (
                "output/insights/"
                "2026-07-28_t136-timing-flake-generalized-limits.md#4"
            ),
            "results": rows,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if all(row["observed"] == "KILLED" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
