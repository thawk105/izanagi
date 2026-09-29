#!/usr/bin/env python3
"""Stop hook that reminds a landed linked worktree to run DW-O28 cleanup."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


REASON = (
    "この worktree の branch は local main に land 済みの可能性がある。"
    "DW-O28 に従い子木と wave 木を撤去する。"
    "撤去できない・未 land・撤去中なら、その旨と残置 path を 1 行書いて終えてよい。"
)
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _git(cwd: Path, *args: str, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", os.fspath(cwd), *args], capture_output=True,
        text=True, stdin=subprocess.DEVNULL, timeout=timeout, check=False,
    )


def decide(payload: object, *, git=_git) -> tuple[bool, str]:
    """Return (block, reason); every uncertain state passes through."""
    if not isinstance(payload, dict) or payload.get("stop_hook_active") is True:
        return False, ""
    if "stop_hook_active" in payload and not isinstance(payload["stop_hook_active"], bool):
        return False, ""
    cwd_value = payload.get("cwd")
    if not isinstance(cwd_value, str) or not cwd_value or not Path(cwd_value).is_dir():
        return False, ""
    cwd = Path(cwd_value)
    deadline = time.monotonic() + 5

    def run(*args: str) -> tuple[int, str]:
        remaining = min(2, deadline - time.monotonic())
        if remaining <= 0:
            raise TimeoutError
        result = git(cwd, *args, timeout=remaining)
        return result.returncode, result.stdout.strip()

    try:
        code, bare = run("rev-parse", "--is-bare-repository")
        if code or bare != "false":
            return False, ""
        code, superproject = run("rev-parse", "--show-superproject-working-tree")
        if code or superproject:
            return False, ""
        code, git_dir = run("rev-parse", "--git-dir")
        if code or not git_dir:
            return False, ""
        code, common_dir = run("rev-parse", "--git-common-dir")
        if code or not common_dir or (cwd / git_dir).resolve() == (cwd / common_dir).resolve():
            return False, ""
        code, branch = run("symbolic-ref", "--quiet", "HEAD")
        if code or not branch.startswith("refs/heads/"):
            return False, ""
        code, head = run("rev-parse", "--verify", "HEAD^{commit}")
        if code or not _OID.fullmatch(head):
            return False, ""
        code, entries = run("reflog", "show", "--format=%H", branch)
        if code or not entries:
            return False, ""
        oids = entries.splitlines()
        if any(not _OID.fullmatch(oid) for oid in oids) or oids[-1] == head:
            return False, ""
        code, _ = run("merge-base", "--is-ancestor", head, "refs/heads/main")
        return (True, REASON) if code == 0 else (False, "")
    except Exception:  # noqa: BLE001 — this advisory hook must fail open
        return False, ""


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return 0
        block, reason = decide(json.loads(raw.decode("utf-8")))
        if block:
            print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    except Exception:  # noqa: BLE001 — Stop must always exit successfully
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
