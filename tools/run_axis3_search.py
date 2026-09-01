#!/usr/bin/env python3
"""Axis 3 registered-search CLI with sealed fake or single-attempt live transport."""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator import related_work_search as search  # noqa: E402


def _object(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise search.ContractError("cli_input", f"JSONを読めない: {path}") from exc
    if not isinstance(value, Mapping):
        raise search.ContractError("cli_input", f"JSON rootはobjectが必要: {path}")
    return value


def _array(path: Path) -> list[Mapping[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise search.ContractError("cli_input", f"JSONを読めない: {path}") from exc
    if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
        raise search.ContractError("cli_input", f"JSON object arrayが必要: {path}")
    return value


def _inputs(path: Path) -> tuple[list[str], str]:
    value = _object(path)
    argv = value.get("argv")
    commit = value.get("commit")
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) or not item for item in argv)
        or not isinstance(commit, str)
    ):
        raise search.ContractError("cli_input", "registration inputsにargvとcommitが必要")
    return argv, commit


def _write(path: Path, value: Mapping[str, Any]) -> None:
    search._write_json_atomic(path, value)  # Axis 3の同一atomic writerを使う。


def _effective_argv() -> list[str]:
    return [str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]


def _bind_cli_semantics(
    phase: str,
    effective_argv: Sequence[str],
    bindings: Mapping[str, Path | None],
) -> Mapping[str, Any]:
    evidence = search.validate_effective_phase_argv(effective_argv, phase)
    for option, actual in bindings.items():
        search._bind_semantic_path(evidence, option, actual)
    return evidence


def _load_registration(args: argparse.Namespace):
    catalog_data = args.catalog.read_bytes()
    catalog = json.loads(catalog_data.decode("utf-8"))
    seal = _object(args.seal)
    argv, commit = _inputs(args.registration_inputs)
    return catalog_data, catalog, seal, argv, commit


def _validated_registration(args: argparse.Namespace, *, enforce_head: bool):
    catalog_data, catalog, seal, argv, commit = _load_registration(args)
    search.validate_catalog(catalog)
    search.validate_registration_seal(
        seal,
        catalog_data,
        argv=argv,
        commit=commit,
        enforce_head=enforce_head,
    )
    return catalog_data, catalog, seal, argv, commit


def _transport(args: argparse.Namespace):
    if getattr(args, "live", False):
        return search.create_live_search_session(
            timeout_seconds=args.timeout_seconds
        )
    responses = getattr(args, "responses", None)
    if responses is None:
        raise search.ContractError("cli_transport", "--liveまたは--responsesが必要")
    decoded = []
    for response in _array(responses):
        value = dict(response)
        encoded = value.pop("entity_body_base64", None)
        if not isinstance(encoded, str) or "entity_body" in value:
            raise search.ContractError(
                "cli_transport",
                "fake responseはentity_body_base64だけでexact bytesを指定する",
            )
        try:
            value["entity_body"] = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise search.ContractError("cli_transport", "entity_body_base64が不正") from exc
        decoded.append(value)
    return search.ScriptedTransport(decoded)


def _register(args: argparse.Namespace) -> Mapping[str, Any]:
    catalog = search.build_axis3_catalog()
    catalog_data = search.catalog_bytes(catalog)
    commit = search.resolve_head_commit()
    effective_argv = _effective_argv()
    _bind_cli_semantics(
        "register",
        effective_argv,
        {
            "--catalog": args.catalog,
            "--seal": args.seal,
            "--registration-inputs": args.registration_inputs,
        },
    )
    registration_inputs = {
        "argv": effective_argv,
        "commit": commit,
        "argv_sha256": search._sha256(search._canonical_json(effective_argv)),
    }
    seal = search.build_registration_seal(
        catalog_data,
        argv=effective_argv,
        commit=commit,
        enforce_head=True,
    )
    search._write_bytes_atomic(args.catalog, catalog_data)
    _write(args.registration_inputs, registration_inputs)
    _write(args.seal, seal)
    return {
        "valid": True,
        "catalog_sha256": seal["catalog_sha256"],
        "registration_seal_sha256": seal["seal_sha256"],
        "commit": commit,
        "head_verified": True,
    }


def _validate_registration(args: argparse.Namespace) -> Mapping[str, Any]:
    catalog_data = args.catalog.read_bytes()
    catalog = json.loads(catalog_data.decode("utf-8"))
    argv, commit = _inputs(args.registration_inputs)
    search.validate_catalog(catalog)
    if args.create_seal:
        seal = search.build_registration_seal(catalog_data, argv=argv, commit=commit)
        _write(args.seal, seal)
    else:
        seal = _object(args.seal)
    search.validate_registration_seal(seal, catalog_data, argv=argv, commit=commit)
    return {
        "valid": True,
        "catalog_sha256": seal["catalog_sha256"],
        "registration_seal_sha256": seal["seal_sha256"],
    }


def _preflight(args: argparse.Namespace) -> Mapping[str, Any]:
    catalog_data, catalog, seal, argv, commit = _validated_registration(
        args, enforce_head=args.live
    )
    if args.live and args.bundle is None:
        raise search.ContractError("cli_bundle", "live preflightには--bundleが必要")
    transport = _transport(args)
    effective_argv = _effective_argv()
    _bind_cli_semantics(
        "preflight",
        effective_argv,
        {
            "--catalog": args.catalog,
            "--seal": args.seal,
            "--registration-inputs": args.registration_inputs,
            "--responses": args.responses,
            "--output": args.output,
            "--checkpoint": args.checkpoint,
            "--bundle": args.bundle,
        },
    )
    report = search.run_preflight(
        catalog,
        catalog_data,
        seal,
        argv=argv,
        commit=commit,
        transport=transport,
        checkpoint_path=args.checkpoint,
        bundle_dir=args.bundle,
        effective_argv=effective_argv,
    )
    _write(args.output, report)
    return {
        "valid": True,
        "wire_attempt_count": report["wire_attempt_count"],
        "status_counts": report["status_counts"],
        "axis_complete": False,
    }


def _run_ready(args: argparse.Namespace) -> Mapping[str, Any]:
    catalog_data, catalog, seal, argv, commit = _validated_registration(
        args, enforce_head=args.live
    )
    if args.preflight_bundle is None:
        raise search.ContractError("cli_bundle", "run-readyには--preflight-bundleが必要")
    if args.live and args.bundle is None:
        raise search.ContractError("cli_bundle", "live run-readyには--bundleが必要")
    preflight_report = _object(args.preflight_report) if args.preflight_report else None
    transport = _transport(args)
    effective_argv = _effective_argv()
    _bind_cli_semantics(
        "run-ready",
        effective_argv,
        {
            "--catalog": args.catalog,
            "--seal": args.seal,
            "--registration-inputs": args.registration_inputs,
            "--responses": args.responses,
            "--preflight-report": args.preflight_report,
            "--preflight-bundle": args.preflight_bundle,
            "--bundle": args.bundle,
            "--output": args.output,
        },
    )
    result = search.run_ready(
        catalog,
        catalog_data,
        seal,
        preflight_report,
        argv=argv,
        commit=commit,
        transport=transport,
        preflight_bundle_dir=args.preflight_bundle,
        bundle_dir=args.bundle,
        effective_argv=effective_argv,
    )
    _write(args.output, result)
    return {
        "valid": True,
        "executed_rows": len(result["execution_order"]),
        "wire_attempt_count": result["wire_attempt_count"],
        "axis_complete": False,
    }


def _resume(args: argparse.Namespace) -> Mapping[str, Any]:
    catalog_data, catalog, seal, argv, commit = _validated_registration(
        args, enforce_head=args.live
    )
    transport = _transport(args)
    effective_argv = _effective_argv()
    _bind_cli_semantics(
        "resume",
        effective_argv,
        {
            "--catalog": args.catalog,
            "--seal": args.seal,
            "--registration-inputs": args.registration_inputs,
            "--responses": args.responses,
            "--bundle": args.bundle,
            "--preflight-bundle": args.preflight_bundle,
        },
    )
    return search.resume_bundle(
        args.bundle,
        catalog,
        catalog_data,
        seal,
        argv=argv,
        commit=commit,
        transport=transport,
        preflight_bundle_dir=args.preflight_bundle,
        effective_argv=effective_argv,
    )


def _validate_bundle(args: argparse.Namespace) -> Mapping[str, Any]:
    _phase = _bind_cli_semantics(
        "validate-bundle",
        _effective_argv(),
        {
            "<bundle>": args.bundle,
            "--catalog": args.catalog,
            "--seal": args.seal,
            "--registration-inputs": args.registration_inputs,
            "--preflight-bundle": args.preflight_bundle,
        },
    )
    _catalog_data, catalog, seal, _argv, _commit = _validated_registration(
        args, enforce_head=False
    )
    manifest, _, _, _ = search._read_bundle_manifest(args.bundle)
    counts = search.validate_bundle(
        args.bundle,
        catalog=catalog,
        seal=seal,
        parent_preflight_bundle_dir=(
            args.preflight_bundle if manifest.get("kind") == "final" else None
        ),
    )
    if manifest.get("kind") == "preflight":
        search.load_preflight_bundle(args.bundle, catalog, seal)
    return {"valid": True, **counts}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Additional commands: register, resume.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="{validate-registration,preflight,run-ready,validate-bundle}",
    )

    register = subparsers.add_parser("register")
    register.add_argument("--catalog", type=Path, required=True)
    register.add_argument("--seal", type=Path, required=True)
    register.add_argument("--registration-inputs", type=Path, required=True)
    register.set_defaults(handler=_register)

    registration = subparsers.add_parser("validate-registration")
    registration.add_argument("--catalog", type=Path, required=True)
    registration.add_argument("--seal", type=Path, required=True)
    registration.add_argument("--registration-inputs", type=Path, required=True)
    registration.add_argument("--create-seal", action="store_true")
    registration.set_defaults(handler=_validate_registration)

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--catalog", type=Path, required=True)
    preflight.add_argument("--seal", type=Path, required=True)
    preflight.add_argument("--registration-inputs", type=Path, required=True)
    preflight_transport = preflight.add_mutually_exclusive_group(required=True)
    preflight_transport.add_argument("--responses", type=Path)
    preflight_transport.add_argument("--live", action="store_true")
    preflight.add_argument("--timeout-seconds", type=float, default=30.0)
    preflight.add_argument("--output", type=Path, required=True)
    preflight.add_argument("--checkpoint", type=Path)
    preflight.add_argument("--bundle", type=Path)
    preflight.set_defaults(handler=_preflight)

    run_ready = subparsers.add_parser("run-ready")
    run_ready.add_argument("--catalog", type=Path, required=True)
    run_ready.add_argument("--seal", type=Path, required=True)
    run_ready.add_argument("--registration-inputs", type=Path, required=True)
    run_ready.add_argument("--preflight-report", type=Path)
    run_ready.add_argument("--preflight-bundle", type=Path, required=True)
    run_transport = run_ready.add_mutually_exclusive_group(required=True)
    run_transport.add_argument("--responses", type=Path)
    run_transport.add_argument("--live", action="store_true")
    run_ready.add_argument("--timeout-seconds", type=float, default=30.0)
    run_ready.add_argument("--bundle", type=Path, required=True)
    run_ready.add_argument("--output", type=Path, required=True)
    run_ready.set_defaults(handler=_run_ready)

    bundle = subparsers.add_parser("validate-bundle")
    bundle.add_argument("bundle", type=Path)
    bundle.add_argument("--catalog", type=Path, required=True)
    bundle.add_argument("--seal", type=Path, required=True)
    bundle.add_argument("--registration-inputs", type=Path, required=True)
    bundle.add_argument("--preflight-bundle", type=Path)
    bundle.set_defaults(handler=_validate_bundle)

    resume = subparsers.add_parser("resume")
    resume.add_argument("--catalog", type=Path, required=True)
    resume.add_argument("--seal", type=Path, required=True)
    resume.add_argument("--registration-inputs", type=Path, required=True)
    resume.add_argument("--bundle", type=Path, required=True)
    resume.add_argument("--preflight-bundle", type=Path)
    resume_transport = resume.add_mutually_exclusive_group(required=True)
    resume_transport.add_argument("--responses", type=Path)
    resume_transport.add_argument("--live", action="store_true")
    resume.add_argument("--timeout-seconds", type=float, default=30.0)
    resume.set_defaults(handler=_resume)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if argv is not None and "--live" in argv:
        print(
            json.dumps(
                {
                    "valid": False,
                    "code": "programmatic_live_invocation",
                    "error": "programmatic main(argv) cannot start live Axis 3 transport",
                },
                ensure_ascii=False,
            )
        )
        return 2
    args = _parser().parse_args(argv)
    try:
        result = args.handler(args)
    except (search.ContractError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        code = exc.code if isinstance(exc, search.ContractError) else "cli_failure"
        print(json.dumps({"valid": False, "code": code, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
