#!/usr/bin/env python3
"""Tracked, single-run mutation harness for T-145's integrated test."""
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
OUT = Path(__file__).with_name("mutation-results-new.json")
LOCK = Path(__file__).with_name("mutation.lock")
NODE = (
    "orchestrator/tests/test_dev_waves_integration.py::"
    "test_socket_roundtrip_works_beyond_108_byte_repository_path"
)


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    path: str
    old: str
    new: str
    classification: str
    expected: str


MUTATIONS = (
    Mutation(
        "M1", "tools/dev_waves/daemon.py",
        "                                conn.shutdown(socket.SHUT_WR)\n",
        "                                conn.shutdown(socket.SHUT_WR)\n"
        "                                return\n",
        "pure-added-detection", "KILLED",
    ),
    Mutation(
        "M2", "tools/dev_waves/daemon.py",
        "                    while not self._shutdown.is_set():\n",
        "                    while True:\n",
        "diagnostic-latency-pin", "DIAGNOSTIC_KILLED",
    ),
    Mutation(
        "M3", "tools/dev_waves/daemon.py",
        "    def shutdown(self) -> None:\n"
        "        self._shutdown.set()\n"
        "        with self._lock:\n",
        "    def shutdown(self) -> None:\n"
        "        with self._lock:\n",
        "diagnostic-latency-pin", "DIAGNOSTIC_KILLED",
    ),
    Mutation(
        "M4", "tools/dev_waves/daemon.py",
        "                        ready, _, _ = select.select("
        "[bound.sock, relay.fileno()], [], [], 0.25)\n",
        "                        ready, _, _ = select.select("
        "[bound.sock, relay.fileno()], [], [], 3600.0)\n",
        "diagnostic-sensitivity-pin", "DIAGNOSTIC_KILLED",
    ),
    Mutation(
        "M5", "orchestrator/tests/test_dev_waves_integration.py",
        "            thread = threading.Thread(target=_serve, daemon=True)\n",
        "            thread = threading.Thread(target=_serve, daemon=False)\n",
        "preservation", "KILLED",
    ),
    Mutation(
        "M6", "orchestrator/tests/test_dev_waves_integration.py",
        "        if threading.current_thread() is not self._target_thread:\n",
        "        if False:\n",
        "harness-isolation-control", "DIAGNOSTIC_KILLED",
    ),
)


def run(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, check=False, timeout=timeout,
    )


def git_bytes(path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout


def restore(path: str, expected: bytes) -> None:
    subprocess.run(
        ["git", "checkout", "--", path], cwd=ROOT, check=True,
        stdin=subprocess.DEVNULL,
    )
    actual = (ROOT / path).read_bytes()
    if actual != expected:
        raise RuntimeError(f"{path}: restore differs from integrated HEAD")
    status = run("git", "diff", "--", path)
    if status.returncode != 0 or status.stdout:
        raise RuntimeError(f"{path}: tracked diff remains after restore")


def main() -> int:
    if run("git", "diff", "--name-only").stdout:
        raise RuntimeError("tracked worktree must be clean before mutation")
    lock = LOCK.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("another T-145 mutation harness holds the lock")

    results: list[dict[str, object]] = []
    for mutation in MUTATIONS:
        path = ROOT / mutation.path
        original = git_bytes(mutation.path)
        source = original.decode("utf-8")
        count = source.count(mutation.old)
        if count != 1:
            raise RuntimeError(
                f"{mutation.mutation_id}: anchor count {count}, expected 1",
            )
        mutated = source.replace(mutation.old, mutation.new, 1)
        if mutated == source:
            raise RuntimeError(f"{mutation.mutation_id}: injection absent")
        path.write_text(mutated, encoding="utf-8")
        diff = run("git", "diff", "--numstat", "--", mutation.path)
        changed_paths = run("git", "diff", "--name-only").stdout.splitlines()
        if diff.returncode != 0 or changed_paths != [mutation.path]:
            restore(mutation.path, original)
            raise RuntimeError(
                f"{mutation.mutation_id}: non-single mutation diff "
                f"{changed_paths!r}",
            )
        started = time.monotonic()
        timed_out = False
        try:
            test = run(
                sys.executable, "-m", "pytest", "-q", "-rf", NODE,
                timeout=210,
            )
            rc = test.returncode
            output = test.stdout
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            rc = None
            output = (
                (exc.stdout or "") + (exc.stderr or "")
                if isinstance(exc.stdout, str) else ""
            )
        finally:
            restore(mutation.path, original)
        failed_nodes = re.findall(
            r"^FAILED (\S+)(?: - .*)?$", output, re.MULTILINE,
        )
        skipped = len(re.findall(r"\bskipped\b", output, re.IGNORECASE))
        observed = (
            "INFRA_TIMEOUT_NOT_EVIDENCE" if timed_out
            else "SURVIVED" if rc == 0
            else "KILLED" if mutation.classification in {
                "pure-added-detection", "preservation"
            }
            else "DIAGNOSTIC_KILLED"
        )
        results.append({
            "id": mutation.mutation_id,
            "path": mutation.path,
            "classification": mutation.classification,
            "expected": mutation.expected,
            "observed": observed,
            "rc": rc,
            "timed_out": timed_out,
            "elapsed_s": round(time.monotonic() - started, 3),
            "failed_nodes": failed_nodes,
            "skip_mentions": skipped,
            "diff_numstat": diff.stdout.strip(),
            "mutated_sha256": hashlib.sha256(
                mutated.encode("utf-8"),
            ).hexdigest(),
            "output_tail": "\n".join(output.splitlines()[-35:]),
            "restored_to_head": True,
        })
        print(
            mutation.mutation_id, observed, f"rc={rc}",
            f"elapsed={results[-1]['elapsed_s']}s",
            flush=True,
        )

    payload = {
        "schema_version": 1,
        "integrated_commit": run("git", "rev-parse", "HEAD").stdout.strip(),
        "node": NODE,
        "results": results,
        "m7": {
            "observed": "NOT_RUN",
            "reason": "design-invalid: cleanup success is not independently observable",
        },
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if any(item["observed"] != item["expected"] for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
