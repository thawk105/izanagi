#!/usr/bin/env python3
"""Comparison mutations against T-145's pre-change test at integrated HEAD^."""
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


ROOT = Path(
    "/home/SFC/tanab/github/izanagi/.codex/worktrees/"
    "dev-wave-t145-old-mutation",
)
OUT = Path(__file__).with_name("mutation-results-old.json")
LOCK = Path(__file__).with_name("mutation-old.lock")
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
    expected: str
    comparison: str


MUTATIONS = (
    Mutation(
        "M1", "tools/dev_waves/daemon.py",
        "                                conn.shutdown(socket.SHUT_WR)\n",
        "                                conn.shutdown(socket.SHUT_WR)\n"
        "                                return\n",
        "SURVIVED", "pure-added-detection",
    ),
    Mutation(
        "M2", "tools/dev_waves/daemon.py",
        "                    while not self._shutdown.is_set():\n",
        "                    while True:\n",
        "OLD_SLOW_FAILURE", "fixed-join-120",
    ),
    Mutation(
        "M3", "tools/dev_waves/daemon.py",
        "    def shutdown(self) -> None:\n"
        "        self._shutdown.set()\n"
        "        with self._lock:\n",
        "    def shutdown(self) -> None:\n"
        "        with self._lock:\n",
        "OLD_SLOW_FAILURE", "fixed-join-120",
    ),
    Mutation(
        "M4", "tools/dev_waves/daemon.py",
        "                        ready, _, _ = select.select("
        "[bound.sock, relay.fileno()], [], [], 0.25)\n",
        "                        ready, _, _ = select.select("
        "[bound.sock, relay.fileno()], [], [], 3600.0)\n",
        "OLD_SLOW_FAILURE", "fixed-join-120",
    ),
    Mutation(
        "M5", "orchestrator/tests/test_dev_waves_integration.py",
        "            thread = threading.Thread(target=_serve, daemon=True)\n",
        "            thread = threading.Thread(target=_serve, daemon=False)\n",
        "SURVIVED", "preservation-gap",
    ),
)


def run(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=ROOT, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, check=False, timeout=timeout,
    )


def git_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def restore(path: str, expected: bytes) -> None:
    subprocess.run(
        ["git", "checkout", "--", path], cwd=ROOT, check=True,
        stdin=subprocess.DEVNULL,
    )
    if (ROOT / path).read_bytes() != expected:
        raise RuntimeError(f"{path}: restore differs from comparison HEAD")
    if run("git", "diff", "--", path).stdout:
        raise RuntimeError(f"{path}: tracked diff remains after restore")


def main() -> int:
    expected_head = subprocess.run(
        ["git", "-C", str(ROOT.parent / "dev-wave-t145"),
         "rev-parse", "HEAD^"],
        text=True, stdout=subprocess.PIPE, check=True,
    ).stdout.strip()
    actual_head = run("git", "rev-parse", "HEAD").stdout.strip()
    compared_paths = sorted({item.path for item in MUTATIONS})
    for path in compared_paths:
        actual_blob = run("git", "rev-parse", f"HEAD:{path}").stdout.strip()
        expected_blob = subprocess.run(
            ["git", "-C", str(ROOT.parent / "dev-wave-t145"),
             "rev-parse", f"HEAD^:{path}"],
            text=True, stdout=subprocess.PIPE, check=True,
        ).stdout.strip()
        if actual_blob != expected_blob:
            raise RuntimeError(
                f"{path}: comparison blob {actual_blob} != "
                f"integrated HEAD^ blob {expected_blob}",
            )
    if run("git", "diff", "--name-only").stdout:
        raise RuntimeError("comparison worktree must be clean before mutation")
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
        path.write_text(mutated, encoding="utf-8")
        diff = run("git", "diff", "--numstat", "--", mutation.path)
        changed_paths = run("git", "diff", "--name-only").stdout.splitlines()
        if changed_paths != [mutation.path]:
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
                timeout=150,
            )
            rc = test.returncode
            output = test.stdout
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            rc = None
            output = exc.stdout if isinstance(exc.stdout, str) else ""
        finally:
            restore(mutation.path, original)
        elapsed = round(time.monotonic() - started, 3)
        failed_nodes = re.findall(
            r"^FAILED (\S+)(?: - .*)?$", output, re.MULTILINE,
        )
        if timed_out:
            observed = "INFRA_TIMEOUT_NOT_EVIDENCE"
        elif rc == 0:
            observed = "SURVIVED"
        elif elapsed >= 115:
            observed = "OLD_SLOW_FAILURE"
        else:
            observed = "OLD_EARLY_FAILURE"
        results.append({
            "id": mutation.mutation_id,
            "expected": mutation.expected,
            "observed": observed,
            "comparison": mutation.comparison,
            "rc": rc,
            "timed_out": timed_out,
            "elapsed_s": elapsed,
            "failed_nodes": failed_nodes,
            "diff_numstat": diff.stdout.strip(),
            "mutated_sha256": hashlib.sha256(
                mutated.encode("utf-8"),
            ).hexdigest(),
            "output_tail": "\n".join(output.splitlines()[-30:]),
            "restored_to_head": True,
        })
        print(
            mutation.mutation_id, observed, f"rc={rc}",
            f"elapsed={elapsed}s", flush=True,
        )

    payload = {
        "schema_version": 1,
        "comparison_commit": actual_head,
        "comparison_equivalent_to_integrated_parent": expected_head,
        "integrated_commit": subprocess.run(
            ["git", "-C", str(ROOT.parent / "dev-wave-t145"),
             "rev-parse", "HEAD"],
            text=True, stdout=subprocess.PIPE, check=True,
        ).stdout.strip(),
        "node": NODE,
        "baseline": "1 passed in 1.39s",
        "results": results,
        "m6": {
            "observed": "NOT_APPLICABLE",
            "reason": "target-thread proxy did not exist in pre-change test",
        },
        "m7": {
            "observed": "NOT_RUN",
            "reason": "design-invalid",
        },
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if all(
        item["observed"] == item["expected"] for item in results
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
