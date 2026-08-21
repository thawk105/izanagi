#!/usr/bin/env python3
"""Initialize the registered worktree's local submodules without fetching."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.dev_waves.git_state import (  # noqa: E402
    resolve_registered_worktree,
    update_submodules_no_fetch,
)
from tools.dev_waves.schema import DevWavesError  # noqa: E402


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _absolute_worktree(value: str) -> str:
    if not os.path.isabs(value):
        raise argparse.ArgumentTypeError("--worktree must be an absolute path")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        description="Initialize local submodules in a registered dev-wave worktree.",
    )
    parser.add_argument(
        "--worktree", required=True, type=_absolute_worktree,
        metavar="ABSOLUTE_WORKTREE",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if not os.path.isdir(args.worktree):
            raise ValueError("--worktree does not exist or is not a directory")
        record = resolve_registered_worktree(_REPO_ROOT, args.worktree)
        update_submodules_no_fetch(record.path)
    except DevWavesError as exc:
        print(f"ERROR: {exc.code.value}: detail={exc.detail}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"OK: submodules initialized in {record.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
