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
    discard_current_pass_witness,
    git_identity_digest,
    load_baseline,
    pass_witness_sha256,
    require_writable_descendant,
    validate_t810,
    verify_pre_witness,
    verify_result_snapshot,
    write_baseline_create_only,
    write_pass_witness_create_only,
)


def _read_object(path: Path, name: str) -> dict:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
        value: dict[str, object] = {}
        for key, child in pairs:
            if key in value:
                raise T810ValidationError(f"duplicate JSON key in {name}: {key}")
            value[key] = child
        return value

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
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
    parser.add_argument("--pre-pass-witness", type=Path)
    parser.add_argument("--attempt-nonce", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    invocation_nonce = secrets.token_hex(16)
    try:
        request = _read_object(args.request, "request")
        if "canonical_forbidden_roots" in request:
            raise T810ValidationError(
                "canonical forbidden roots are derived internally from repo_root"
            )
        approval_value = _read_object(args.approval_receipt, "approval receipt")
        if set(approval_value) != {
            "approval_id", "artifact_sha256", "git_identity_sha256", "schema_version"
        }:
            raise T810ValidationError(
                "approval receipt must bind artifact and git identity digests"
            )
        approved_identity_sha256 = approval_value["git_identity_sha256"]
        approval = ApprovalReceipt(**{
            key: approval_value[key]
            for key in ("artifact_sha256", "approval_id", "schema_version")
        })
        preregistration = load_t810_preregistration(
            Path(request["preregistration"]), approval_receipt=approval
        )
        writable_root = Path(request["writable_root"])
        baseline_path = require_writable_descendant(
            args.baseline, writable_root, must_exist=args.mode == "post"
        )
        witness_path = require_writable_descendant(
            args.pass_witness, writable_root, must_exist=False
        )
        attempt_root = require_writable_descendant(
            Path(request["attempt_root"]), writable_root, must_exist=True
        )
        if baseline_path.is_relative_to(attempt_root) or witness_path.is_relative_to(attempt_root):
            raise T810ValidationError("baseline and pass witness must be outside attempt_root")
        previous = None if args.mode == "pre" else load_baseline(baseline_path)
        if args.mode == "post":
            if args.pre_pass_witness is None:
                raise T810ValidationError("post mode requires --pre-pass-witness")
            pre_witness_path = require_writable_descendant(
                args.pre_pass_witness, writable_root, must_exist=True
            )
            if pre_witness_path.is_relative_to(attempt_root):
                raise T810ValidationError("pre pass witness must be outside attempt_root")
            verify_pre_witness(pre_witness_path, previous)
            pre_invocation_nonce = previous.lineage.pre_invocation_nonce
        else:
            if args.pre_pass_witness is not None:
                raise T810ValidationError("pre mode forbids --pre-pass-witness")
            pre_invocation_nonce = invocation_nonce
        identity = GitIdentity(**_read_object(args.approved_git_identity, "approved git identity"))
        if git_identity_digest(identity) != approved_identity_sha256:
            raise T810ValidationError("approved git identity does not match approval receipt digest")
        result = validate_t810(
            preregistration=preregistration,
            repo_root=Path(request["repo_root"]),
            approved_git_identity=identity,
            approved_git_identity_sha256=approved_identity_sha256,
            writable_root=Path(request["writable_root"]),
            manifest_path=Path(request["manifest_path"]),
            manifest_root=Path(request["manifest_root"]),
            expected_manifest_sha256=request["expected_manifest_sha256"],
            executable=Path(request["executable"]),
            expected_executable_sha256=request["expected_executable_sha256"],
            attempt_root=attempt_root,
            attempt_receipt=_read_object(Path(request["attempt_receipt"]), "attempt receipt"),
            attempt_nonce=args.attempt_nonce,
            pre_invocation_nonce=pre_invocation_nonce,
            claimed_state=request["claimed_state"],
            previous_baseline=previous,
        )
        if not result.ok:
            raise T810ValidationError("validation failed")
        if args.mode == "pre":
            witness_digest = pass_witness_sha256(
                result=result,
                attempt_nonce=args.attempt_nonce,
                invocation_nonce=invocation_nonce,
                phase="pre",
            )
        created = write_pass_witness_create_only(
            witness_path,
            result=result,
            attempt_nonce=args.attempt_nonce,
            invocation_nonce=invocation_nonce,
            phase=args.mode,
        )
        try:
            consume_current_pass_witness(
                witness_path,
                process_returncode=0,
                invocation_nonce=invocation_nonce,
                created_identity=created,
            )
            verify_result_snapshot(
                result,
                repo_root=Path(request["repo_root"]),
                approved_git_identity=identity,
                writable_root=writable_root,
            )
            if args.mode == "pre":
                write_baseline_create_only(
                    baseline_path,
                    result.baseline,
                    invocation_nonce,
                    lineage=result.lineage,
                    pre_witness_sha256=witness_digest,
                )
        except BaseException:
            discard_current_pass_witness(
                witness_path, created_identity=created
            )
            raise
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
