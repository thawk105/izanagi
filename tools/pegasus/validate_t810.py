#!/usr/bin/env python3
"""T-810 pre/post 共通 validator CLI。"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign.t810_preregistration import (  # noqa: E402
    ApprovalReceipt,
    load_t810_preregistration,
)
from orchestrator.campaign.t810_validator import (  # noqa: E402
    GitIdentity,
    T810ValidationError,
    consume_current_pass_witness,
    load_baseline,
    validate_t810,
    write_baseline_create_only,
    write_pass_witness_create_only,
)


def _read_object(path: Path, name: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise T810ValidationError(f"could not read {name}") from exc
    if not isinstance(value, dict):
        raise T810ValidationError(f"{name} must be an object")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pre", "post"))
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--approval-receipt", type=Path, required=True)
    parser.add_argument("--approved-git-identity", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--pass-witness", type=Path, required=True)
    parser.add_argument("--attempt-nonce", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    invocation_nonce = secrets.token_hex(16)
    try:
        request = _read_object(args.request, "request")
        approval_value = _read_object(args.approval_receipt, "approval receipt")
        approval = ApprovalReceipt(**approval_value)
        preregistration = load_t810_preregistration(
            Path(request["preregistration"]), approval_receipt=approval
        )
        previous = None if args.mode == "pre" else load_baseline(args.baseline)
        identity = GitIdentity(**_read_object(args.approved_git_identity, "approved git identity"))
        result = validate_t810(
            preregistration=preregistration,
            repo_root=Path(request["repo_root"]),
            approved_git_identity=identity,
            writable_root=Path(request["writable_root"]),
            manifest_path=Path(request["manifest_path"]),
            manifest_root=Path(request["manifest_root"]),
            expected_manifest_sha256=request["expected_manifest_sha256"],
            executable=Path(request["executable"]),
            expected_executable_sha256=request["expected_executable_sha256"],
            attempt_root=Path(request["attempt_root"]),
            attempt_receipt=_read_object(Path(request["attempt_receipt"]), "attempt receipt"),
            claimed_state=request["claimed_state"],
            previous_baseline=previous,
            canonical_forbidden_roots={
                key: Path(value) for key, value in request.get("canonical_forbidden_roots", {}).items()
            } or None,
        )
        if not result.ok:
            raise T810ValidationError("validation failed")
        if args.mode == "pre":
            write_baseline_create_only(args.baseline, result.baseline, invocation_nonce)
        created = write_pass_witness_create_only(
            args.pass_witness,
            result=result,
            attempt_nonce=args.attempt_nonce,
            invocation_nonce=invocation_nonce,
        )
        consume_current_pass_witness(
            args.pass_witness,
            process_returncode=0,
            invocation_nonce=invocation_nonce,
            created_identity=created,
        )
        print(json.dumps({
            "baseline_digest": result.baseline_digest,
            "findings": [finding.__dict__ for finding in result.findings],
            "limitations": result.limitations,
            "ok": True,
            "terminal_state": result.terminal_state,
        }, sort_keys=True))
        return 0
    except BaseException as exc:
        # finalize failure・KeyboardInterrupt・SystemExit も rc=0 に倒さない。
        print(f"T-810 validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
