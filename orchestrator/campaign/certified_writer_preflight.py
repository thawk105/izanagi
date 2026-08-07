#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin stdin-executable CLI adapter for certified-writer static admission."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("invalid arguments")


def _emit(gate: str, reason: str) -> None:
    sys.stderr.write(json.dumps(
        {"gate": gate, "reason": reason},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ) + "\n")


def _arguments(argv):
    parser = _Parser(add_help=False, exit_on_error=False)
    parser.add_argument("mode", choices=("floor", "t126"))
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--receipt", required=True)
    try:
        args, extras = parser.parse_known_args(argv)
    except (argparse.ArgumentError, SystemExit, TypeError, ValueError) as exc:
        raise ValueError("invalid arguments") from exc
    if extras:
        raise ValueError("invalid arguments")
    return args


def main(argv=None) -> int:
    try:
        args = _arguments(sys.argv[1:] if argv is None else argv)
    except ValueError as exc:
        _emit("input", str(exc))
        return 4
    orchestrator = str(Path(args.repo_root) / "orchestrator")
    if orchestrator not in sys.path:
        sys.path.insert(0, orchestrator)
    try:
        from campaign.certified_writer_admission import (
            AdmissionInputError,
            AdmissionRejected,
            admit,
        )
    except Exception as exc:  # import/bootstrap failures are input/environment errors
        _emit("input", f"{type(exc).__name__}: {exc}")
        return 4
    try:
        admit(
            args.mode,
            repo_root=Path(args.repo_root),
            receipt_path=Path(args.receipt),
        )
    except AdmissionRejected as exc:
        _emit("admission", str(exc))
        return 3
    except AdmissionInputError as exc:
        _emit("input", str(exc))
        return 4
    except Exception as exc:  # unexpected environment/import failures are not admission facts
        _emit("input", f"{type(exc).__name__}: {exc}")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
