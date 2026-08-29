#!/usr/bin/env python3
"""Offline-only registration, preflight, and evidence-bundle checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.axis1_search.checkpoint import load_checkpoint
from orchestrator.axis1_search.validator import VerificationResult, verify_bundle, verify_registration


def _commit(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise argparse.ArgumentTypeError("commit must be 40 lowercase hex digits")
    return value


def _add_registration_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--registration-commit", required=True, type=_commit)
    parser.add_argument("--catalog", required=True, type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    registration = subparsers.add_parser("registration", help="verify Git and frozen-byte binding")
    _add_registration_arguments(registration)
    preflight = subparsers.add_parser("preflight", help="verify registration plus optional checkpoint binding")
    _add_registration_arguments(preflight)
    preflight.add_argument("--checkpoint", type=Path)
    bundle = subparsers.add_parser("bundle", help="verify manifest exact-set and digests")
    bundle.add_argument("--bundle", required=True, type=Path)
    bundle.add_argument(
        "--catalog",
        type=Path,
        default=REPO_ROOT / "docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json",
    )
    return parser


def _default_registered_paths(catalog: Path) -> tuple[str, ...]:
    relative = catalog.resolve().relative_to(REPO_ROOT).as_posix()
    return (
        "docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md",
        relative,
        "orchestrator/axis1_search/__init__.py",
        "orchestrator/axis1_search/catalog.py",
        "orchestrator/axis1_search/parsers.py",
        "orchestrator/axis1_search/checkpoint.py",
        "orchestrator/axis1_search/validator.py",
        "orchestrator/axis1_search/runner.py",
        "orchestrator/schemas/axis1_search_catalog.schema.json",
        "orchestrator/schemas/axis1_search_page_evidence.schema.json",
        "orchestrator/schemas/axis1_search_checkpoint.schema.json",
        "tools/run_axis1_search.py",
        "tools/check_axis1_search.py",
        "orchestrator/tests/test_axis1_search_catalog.py",
        "orchestrator/tests/test_axis1_search_runner.py",
        "orchestrator/tests/fixtures/axis1_search",
    )


def _print(result: VerificationResult) -> int:
    print(json.dumps({
        "passed": result.passed,
        "reason_code": result.reason_code,
        "detail": result.detail,
        "status": result.status,
    }, sort_keys=True))
    return 0 if result.passed else 2


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "bundle":
        return _print(verify_bundle(args.bundle, catalog_path=args.catalog))
    try:
        paths = _default_registered_paths(args.catalog)
    except ValueError:
        return _print(VerificationResult(False, "catalog_outside_repo", "catalog path is outside repository"))
    result = verify_registration(
        args.registration_commit,
        args.catalog,
        paths,
        repo_root=REPO_ROOT,
    )
    if not result.passed or args.command == "registration" or args.checkpoint is None:
        return _print(result)
    try:
        checkpoint = load_checkpoint(args.checkpoint)
    except (OSError, ValueError) as exc:
        return _print(VerificationResult(False, "checkpoint_invalid", str(exc)))
    if checkpoint["registration_commit"] != args.registration_commit:
        return _print(VerificationResult(False, "checkpoint_registration_mismatch", "checkpoint names another commit"))
    if Path(checkpoint["catalog_path"]).resolve() != args.catalog.resolve():
        return _print(VerificationResult(False, "checkpoint_catalog_mismatch", "checkpoint names another catalog"))
    return _print(VerificationResult(True, None, "registration and checkpoint binding pass"))


if __name__ == "__main__":
    raise SystemExit(main())
