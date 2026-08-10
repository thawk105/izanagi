#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin stdin-executable CLI adapter for certified-writer static admission."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("invalid arguments")


class _SourceBindingRejected(RuntimeError):
    """Receipt source identity does not match the imported repository code."""


class _SourceBindingInputError(RuntimeError):
    """The source-binding check cannot inspect its local environment."""


_SOURCE_COMMIT = re.compile(r"[0-9a-f]{40}")


def _duplicate_rejector(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise _SourceBindingRejected(f"duplicate receipt key: {key}")
        value[key] = item
    return value


def _receipt_source_commit(receipt_path: Path) -> str:
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise _SourceBindingInputError("receipt is not a non-symlink regular file")
    try:
        raw = receipt_path.read_bytes()
        receipt = json.loads(
            raw,
            object_pairs_hook=_duplicate_rejector,
            parse_constant=lambda token: (_ for _ in ()).throw(
                _SourceBindingRejected(
                    f"non-finite receipt constant: {token}"
                )
            ),
        )
    except _SourceBindingRejected:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _SourceBindingRejected("receipt cannot be decoded for source binding") from exc
    if type(receipt) is not dict:
        raise _SourceBindingRejected("receipt must be an object for source binding")
    commit = receipt.get("source_commit")
    if type(commit) is not str or _SOURCE_COMMIT.fullmatch(commit) is None:
        raise _SourceBindingRejected("receipt source_commit is invalid")
    return commit


def _committed_blob(repo_root: Path, commit: str, relative: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "blob",
             f"{commit}:{relative}"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _SourceBindingInputError(
            "git is unavailable for imported-module source binding"
        ) from exc
    if completed.returncode != 0:
        raise _SourceBindingRejected(
            f"source commit has no imported module blob: {relative}"
        )
    return completed.stdout


def _verify_loaded_repo_modules(
        repo_root: Path, receipt_path: Path,
) -> None:
    """Bind every already-imported repository module to ``source_commit``."""
    try:
        root = repo_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _SourceBindingInputError("repo root is unavailable") from exc
    commit = _receipt_source_commit(receipt_path)
    checked: set[str] = set()
    for name, module in sorted(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if type(module_file) is not str or module_file.startswith("<"):
            continue
        lexical = Path(os.path.abspath(module_file))
        try:
            lexical.relative_to(root)
        except ValueError:
            continue
        if lexical.is_symlink():
            raise _SourceBindingRejected(
                f"imported repository module is a symlink: {name}"
            )
        try:
            resolved = lexical.resolve(strict=True)
            relative = resolved.relative_to(root).as_posix()
            raw = resolved.read_bytes()
        except ValueError as exc:
            raise _SourceBindingRejected(
                f"imported repository module escapes repo root: {name}"
            ) from exc
        except (OSError, RuntimeError) as exc:
            raise _SourceBindingInputError(
                f"imported repository module is unreadable: {name}"
            ) from exc
        if relative in checked:
            continue
        checked.add(relative)
        if raw != _committed_blob(root, commit, relative):
            raise _SourceBindingRejected(
                f"imported module differs from source commit: {relative}"
            )


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
    repo_root = str(Path(args.repo_root))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        from orchestrator.campaign.certified_writer_admission import (
            AdmissionInputError,
            AdmissionRejected,
            admit,
        )
    except Exception as exc:  # import/bootstrap failures are input/environment errors
        _emit("input", f"{type(exc).__name__}: {exc}")
        return 4
    try:
        _verify_loaded_repo_modules(
            Path(args.repo_root), Path(args.receipt),
        )
        admit(
            args.mode,
            repo_root=Path(args.repo_root),
            receipt_path=Path(args.receipt),
        )
    except _SourceBindingRejected as exc:
        _emit("admission", str(exc))
        return 3
    except _SourceBindingInputError as exc:
        _emit("input", str(exc))
        return 4
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
