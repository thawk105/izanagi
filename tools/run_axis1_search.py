#!/usr/bin/env python3
"""Execute only the finite, Git-bound axis-1 search program."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.axis1_search.checkpoint import load_checkpoint
from orchestrator.axis1_search.runner import (
    HTTPSOnlyTransport,
    PreflightError,
    Transport,
    resume_from_checkpoint,
    run_leaf,
)
from orchestrator.axis1_search.validator import verify_registration


_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _registration_commit(value: str) -> str:
    if not _COMMIT.fullmatch(value):
        raise argparse.ArgumentTypeError("registration commit must be 40 lowercase hex digits")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration-commit", required=True, type=_registration_commit)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--query-id", help="registered catalog ID (start only)")
    operation.add_argument("--checkpoint", type=Path, help="checkpoint (resume/independent pass only)")
    return parser


def _registered_paths(catalog: Path) -> tuple[str, ...]:
    resolved = catalog.resolve()
    try:
        catalog_relative = resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise PreflightError("catalog must be inside the repository") from exc
    return (
        "docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md",
        catalog_relative,
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
    )


def _canonical_argv(args: argparse.Namespace) -> tuple[str, ...]:
    result = [
        "python3",
        "tools/run_axis1_search.py",
        "--registration-commit",
        args.registration_commit,
        "--catalog",
        args.catalog.as_posix(),
        "--bundle",
        args.bundle.as_posix(),
        "--run-id",
        args.run_id,
    ]
    if args.checkpoint is not None:
        result.extend(("--checkpoint", args.checkpoint.as_posix()))
    else:
        result.extend(("--query-id", args.query_id))
    return tuple(result)


def _same_path(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve() == Path(right).resolve()


def _load_catalog(path: Path) -> Any:
    from orchestrator.axis1_search.catalog import load_catalog

    return load_catalog(str(path))


def main(argv: Sequence[str] | None = None, *, transport: Transport | None = None) -> int:
    args = build_parser().parse_args(argv)
    checkpoint: dict[str, Any] | None = None
    if args.checkpoint is not None:
        checkpoint = load_checkpoint(args.checkpoint)
        selected = checkpoint["requests"].get(checkpoint["resume_action"])
        if checkpoint["registration_commit"] != args.registration_commit:
            raise PreflightError("CLI registration commit contradicts checkpoint")
        if not _same_path(checkpoint["catalog_path"], args.catalog):
            raise PreflightError("CLI catalog contradicts checkpoint")
        if not _same_path(checkpoint["bundle_root"], args.bundle):
            raise PreflightError("CLI bundle contradicts checkpoint")
        if not selected or selected.get("target_run_id") != args.run_id:
            raise PreflightError("CLI run ID contradicts checkpoint-selected request")

    verification = verify_registration(
        args.registration_commit,
        args.catalog,
        _registered_paths(args.catalog),
        repo_root=REPO_ROOT,
    )
    if not verification.passed:
        print(json.dumps({"passed": False, "reason_code": verification.reason_code, "detail": verification.detail}))
        return 2

    # Loading the catalog and constructing the production transport happen only
    # after Git/frozen-byte preflight.  Neither preflight nor load_catalog uses HTTP.
    catalog = _load_catalog(args.catalog)
    actual_transport = transport or HTTPSOnlyTransport()
    canonical = _canonical_argv(args)
    if checkpoint is None:
        result = run_leaf(
            catalog,
            args.query_id,
            run_id=args.run_id,
            registration_commit=args.registration_commit,
            catalog_path=args.catalog.as_posix(),
            bundle_root=args.bundle,
            transport=actual_transport,
            preflight=verification,
            canonical_runner_argv=canonical,
        )
    else:
        result = resume_from_checkpoint(
            args.checkpoint,
            catalog,
            transport=actual_transport,
            preflight=verification,
            canonical_runner_argv=canonical,
        )
    print(
        json.dumps(
            {
                "state": result.state,
                "request_count": result.request_count,
                "checkpoint_path": result.checkpoint_path,
                "reason_code": result.reason_code,
            },
            sort_keys=True,
        )
    )
    return 0 if result.state == "branch_complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
