"""Command-line surface for the bounded dev-wave supervisor."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Sequence

from .checker import CheckSpec
from .daemon import (
    Supervisor,
    SupervisorConfig,
    SupervisorProfile,
    doctor,
)
from .effort_levels import CLAUDE_EFFORTS
from .git_state import resolve_main_worktree, resolve_repo_identity
from .protocol import exchange
from .schema import (
    PROTOCOL_VERSION,
    CancelRequest,
    DevWavesError,
    ReasonCode,
    ResourceLimits,
    RunState,
    StatusRequest,
    SubmitRequest,
    canonical_bytes,
    parse_decimal_string,
    parse_response,
    strict_loads,
)


def _positive_int(value: str) -> int:
    try:
        result = int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("positive integer required") from None
    if result < 1 or str(result) != value:
        raise argparse.ArgumentTypeError("canonical positive integer required")
    return result


def _nonnegative_float(value: str) -> float:
    try:
        result = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("non-negative number required") from None
    if result < 0 or result == float("inf") or result != result:
        raise argparse.ArgumentTypeError("finite non-negative number required")
    return result


def _decimal_text(value: str) -> str:
    try:
        parse_decimal_string(value, label="cli-budget")
    except DevWavesError:
        raise argparse.ArgumentTypeError("canonical non-negative decimal required") from None
    return value


def _required_hook(value: str) -> tuple[str, str]:
    matcher, separator, command = value.partition("::")
    if not separator or not matcher or not command or "\x00" in value:
        raise argparse.ArgumentTypeError("required hook must be MATCHER::COMMAND")
    return matcher, command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dev_waves.py")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor_parser = commands.add_parser("doctor")
    doctor_parser.add_argument("--repo-root", default=os.getcwd())
    doctor_parser.add_argument("--claude-executable")
    doctor_parser.add_argument("--probe-cli", action="store_true")
    doctor_parser.add_argument("--probe-timeout-s", type=_nonnegative_float, default=5.0)
    doctor_parser.add_argument("--probe-fs", action="store_true")

    serve = commands.add_parser("serve")
    serve.add_argument("--repo-root", required=True)
    serve.add_argument("--profile", choices=("default",), required=True)
    serve.add_argument("--fake-child-executable", required=True)
    serve.add_argument("--fake-child-sha256", required=True)
    serve.add_argument("--model", required=True)
    serve.add_argument("--allowed-model", action="append", required=True)
    serve.add_argument("--effort", choices=CLAUDE_EFFORTS, required=True)
    serve.add_argument("--check-timeout-s", type=_positive_int, required=True)
    serve.add_argument("--termination-grace-s", type=_nonnegative_float, required=True)
    serve.add_argument("--required-hook", action="append", type=_required_hook, required=True)
    serve.add_argument("--max-waves", type=_positive_int, required=True)
    serve.add_argument("--max-per-wave-timeout-s", type=_positive_int, required=True)
    serve.add_argument("--max-total-timeout-s", type=_positive_int, required=True)
    serve.add_argument("--max-per-wave-budget-usd", type=_decimal_text, required=True)
    serve.add_argument("--max-total-budget-usd", type=_decimal_text, required=True)
    serve.add_argument("--max-wave-output-bytes", type=_positive_int, required=True)
    serve.add_argument("--max-run-bytes", type=_positive_int, required=True)

    client = commands.add_parser("client")
    actions = client.add_subparsers(dest="client_action", required=True)
    submit = actions.add_parser("submit")
    submit.add_argument("--max-waves", type=_positive_int, required=True)
    submit.add_argument("--profile", choices=("default",), required=True)
    submit.add_argument("--per-wave-timeout-s", type=_positive_int, required=True)
    submit.add_argument("--total-timeout-s", type=_positive_int, required=True)
    submit.add_argument("--per-wave-budget-usd", type=_decimal_text, required=True)
    submit.add_argument("--total-budget-usd", type=_decimal_text, required=True)
    submit.add_argument("--max-wave-output-bytes", type=_positive_int, required=True)
    submit.add_argument("--max-run-bytes", type=_positive_int, required=True)
    submit.add_argument("--request-id")

    status = actions.add_parser("status")
    status.add_argument("run_id")
    status_mode = status.add_mutually_exclusive_group()
    status_mode.add_argument("--compact", action="store_true")
    status_mode.add_argument("--json", action="store_true")

    cancel = actions.add_parser("cancel")
    cancel.add_argument("run_id")
    cancel.add_argument("--request-id")

    validate = commands.add_parser("validate")
    validate.add_argument("run_id")
    resume = commands.add_parser("resume")
    resume.add_argument("run_id")
    export = commands.add_parser("export")
    export.add_argument("run_id")
    export.add_argument("--output", required=True)
    return parser


def _repo_context() -> tuple[str, str]:
    identity = resolve_repo_identity(os.getcwd())
    main = resolve_main_worktree(os.getcwd())
    runtime = os.path.join(main.path, "output", "dev-wave-supervisor", "runtime")
    return identity.digest, runtime


def _wire_response(response: object) -> str:
    value = json.loads(canonical_bytes(response).decode("utf-8"))
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _client(args: argparse.Namespace) -> int:
    if args.client_action == "submit" and os.environ.get("CLAUDECODE"):
        raise DevWavesError(ReasonCode.NESTED_LAUNCH_ENVIRONMENT, {
            "label": "environment", "kind": "CLAUDECODE",
        })
    identity, runtime = _repo_context()
    if args.client_action == "submit":
        request_id = args.request_id or str(uuid.uuid4())
        limits = ResourceLimits(
            args.per_wave_timeout_s, args.total_timeout_s,
            None if args.per_wave_budget_usd is None else Decimal(args.per_wave_budget_usd),
            None if args.total_budget_usd is None else Decimal(args.total_budget_usd),
            args.max_wave_output_bytes, args.max_run_bytes,
        )
        request = SubmitRequest(
            PROTOCOL_VERSION, "submit", identity, args.max_waves,
            args.profile, request_id, limits,
        )
    elif args.client_action == "status":
        request = StatusRequest(PROTOCOL_VERSION, "status", identity, args.run_id)
    else:
        request = CancelRequest(
            PROTOCOL_VERSION, "cancel", identity, args.run_id,
            args.request_id or str(uuid.uuid4()),
        )
    response = parse_response(exchange(runtime, request, timeout_s=5.0))
    if args.client_action == "status" and not args.json:
        # Compact output is intentionally a four-field allowlist.
        print(
            f"wave={response.wave_index or 0} state={response.state.value if response.state else '-'} "
            f"elapsed={response.elapsed_s if response.elapsed_s is not None else 0} "
            f"reason={response.reason.value if response.reason else '-'}"
        )
    else:
        print(_wire_response(response))
    return 0 if response.ok else 1


def _default_checks(timeout_s: int) -> tuple[CheckSpec, ...]:
    python = sys.executable
    return (
        CheckSpec("codex-agents", (python, "tools/task_run_check.py", "static-check"), timeout_s),
        CheckSpec("docs", (python, "tools/task_run_check.py", "docs-check"), timeout_s),
        CheckSpec("orchestrator", (python, "tools/run_tests.py", "orchestrator/tests"), timeout_s),
        CheckSpec("provenance", (python, "tools/task_run_check.py", "provenance-check"), timeout_s),
    )


def _serve_config(args: argparse.Namespace) -> SupervisorConfig:
    root = os.path.abspath(args.repo_root)
    profile = SupervisorProfile(
        args.profile, args.model, args.effort, _default_checks(args.check_timeout_s),
        settings_path=os.path.join(root, ".claude", "settings.json"),
        required_hooks=tuple(args.required_hook),
        max_waves=args.max_waves,
        max_per_wave_timeout_s=args.max_per_wave_timeout_s,
        max_total_timeout_s=args.max_total_timeout_s,
        max_per_wave_budget_usd=Decimal(args.max_per_wave_budget_usd),
        max_total_budget_usd=Decimal(args.max_total_budget_usd),
        max_wave_output_bytes=args.max_wave_output_bytes,
        max_run_bytes=args.max_run_bytes,
        allowed_models=tuple(args.allowed_model),
    )
    return SupervisorConfig(
        root, os.path.abspath(args.fake_child_executable), args.fake_child_sha256,
        profile, args.check_timeout_s, args.termination_grace_s,
    )


_SERVER_PROFILE_FIELDS = frozenset({
    "schema_version", "repo_root", "fake_child_executable", "fake_child_sha256",
    "profile", "model", "effort", "allowed_models", "check_specs",
    "settings_path", "settings_sha256", "required_hooks", "caps",
})
_CAP_FIELDS = frozenset({
    "max_waves", "max_per_wave_timeout_s", "max_total_timeout_s",
    "max_per_wave_budget_usd", "max_total_budget_usd",
    "max_wave_output_bytes", "max_run_bytes",
})


def parse_server_profile(raw: bytes) -> dict[str, object]:
    """Strictly decode the persisted closed server profile."""
    value = strict_loads(
        raw, label="server-profile", max_bytes=64 * 1024,
        allowed_fields=_SERVER_PROFILE_FIELDS,
    )
    if not isinstance(value, dict) or set(value) != _SERVER_PROFILE_FIELDS:
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "field-set",
        })
    if value["schema_version"] != 1:
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "version",
        })
    for field in (
        "repo_root", "fake_child_executable", "fake_child_sha256", "profile",
        "model", "effort", "settings_sha256",
    ):
        if not isinstance(value[field], str) or not value[field] or "\x00" in value[field]:
            raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                "label": "server-profile", "kind": "string",
            })
    if value["settings_path"] is not None and not isinstance(value["settings_path"], str):
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "settings-path",
        })
    allowed = value["allowed_models"]
    hooks = value["required_hooks"]
    checks = value["check_specs"]
    caps = value["caps"]
    if (not isinstance(allowed, list) or not allowed or
            not all(isinstance(item, str) for item in allowed) or
            not isinstance(hooks, list) or
            not all(isinstance(item, list) and len(item) == 2 and
                    all(isinstance(part, str) and part for part in item) for item in hooks) or
            not isinstance(checks, list) or not checks or
            not isinstance(caps, dict) or set(caps) != _CAP_FIELDS):
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "shape",
        })
    for item in checks:
        if (not isinstance(item, dict) or set(item) != {"name", "argv", "timeout_s"} or
                not isinstance(item["name"], str) or
                not isinstance(item["argv"], list) or
                not all(isinstance(token, str) for token in item["argv"]) or
                not isinstance(item["timeout_s"], int) or isinstance(item["timeout_s"], bool)):
            raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                "label": "server-profile", "kind": "check-spec",
            })
    for field in _CAP_FIELDS - {"max_per_wave_budget_usd", "max_total_budget_usd"}:
        if not isinstance(caps[field], int) or isinstance(caps[field], bool) or caps[field] < 1:
            raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                "label": "server-profile", "kind": "cap",
            })
    for field in ("max_per_wave_budget_usd", "max_total_budget_usd"):
        parse_decimal_string(caps[field], label=field)
    return value


def _local_supervisor() -> Supervisor:
    identity, runtime = _repo_context()
    main = resolve_main_worktree(os.getcwd()).path
    profile_path = Path(runtime) / "server-profile.json"
    if not profile_path.is_file():
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "missing",
        })
    value = parse_server_profile(profile_path.read_bytes())
    if value["profile"] != "default":
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "profile-mismatch",
        })
    if (os.path.realpath(str(value["repo_root"])) != os.path.realpath(main) or
            resolve_repo_identity(main).digest != identity):
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "repo-root-mismatch",
        })
    settings_path = value["settings_path"]
    try:
        current_settings_sha256 = (
            "-" if settings_path is None
            else hashlib.sha256(Path(str(settings_path)).read_bytes()).hexdigest()
        )
    except OSError:
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "settings-unreadable",
        }) from None
    if current_settings_sha256 != value["settings_sha256"]:
        raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
            "label": "server-profile", "kind": "settings-digest-mismatch",
        })
    executable = str(value["fake_child_executable"])
    digest = str(value["fake_child_sha256"])
    model = str(value["model"])
    effort = str(value["effort"])
    caps = value["caps"]
    checks = tuple(CheckSpec(
        str(item["name"]), tuple(str(token) for token in item["argv"]),
        int(item["timeout_s"]),
    ) for item in value["check_specs"])
    required_hooks = tuple(
        (str(item[0]), str(item[1])) for item in value["required_hooks"]
    )
    allowed_models = tuple(str(item) for item in value["allowed_models"])
    profile = SupervisorProfile(
        "default", model, effort, checks, settings_path=settings_path,
        required_hooks=required_hooks, max_waves=int(caps["max_waves"]),
        max_per_wave_timeout_s=int(caps["max_per_wave_timeout_s"]),
        max_total_timeout_s=int(caps["max_total_timeout_s"]),
        max_per_wave_budget_usd=Decimal(str(caps["max_per_wave_budget_usd"])),
        max_total_budget_usd=Decimal(str(caps["max_total_budget_usd"])),
        max_wave_output_bytes=int(caps["max_wave_output_bytes"]),
        max_run_bytes=int(caps["max_run_bytes"]), allowed_models=allowed_models,
    )
    return Supervisor(SupervisorConfig(
        main, executable, digest, profile, 60, 1.0, runtime_dir=runtime,
    ))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "doctor":
            report = doctor(
                repo_root=os.path.abspath(args.repo_root),
                executable=args.claude_executable, probe_cli=args.probe_cli,
                probe_timeout_s=args.probe_timeout_s, probe_fs=args.probe_fs,
            )
            print(json.dumps({"ok": report.ok, "checks": report.checks}, separators=(",", ":")))
            return 0 if report.ok else 1
        if args.command == "serve":
            Supervisor(_serve_config(args)).serve_forever()
            return 0
        if args.command == "client":
            return _client(args)
        if args.command == "resume" and os.environ.get("CLAUDECODE"):
            raise DevWavesError(ReasonCode.NESTED_LAUNCH_ENVIRONMENT, {
                "label": "environment", "kind": "CLAUDECODE",
            })
        supervisor = _local_supervisor()
        if args.command == "validate":
            result = supervisor.validate(args.run_id)
            print(_wire_response(result))
            return 0 if result.ok else 1
        if args.command == "resume":
            result = supervisor.resume(args.run_id)
            print(_wire_response(result))
            return 0 if result.ok else 1
        supervisor.export(args.run_id, args.output)
        print(args.output)
        return 0
    except DevWavesError as exc:
        print(json.dumps({"ok": False, "reason": exc.code.value, "detail": exc.detail},
                         separators=(",", ":")), file=sys.stderr)
        return 2 if exc.code is ReasonCode.RUNTIME_IO_FAILURE else 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"dev-waves I/O/protocol failure: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main", "parse_server_profile"]
