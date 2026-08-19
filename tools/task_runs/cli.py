# -*- coding: utf-8 -*-
"""task-run ledger の型付き CLI。任意 JSON/raw command は受け取らない。"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from .ledger import PilotClosedError, selfcheck
from .schema import DamagedRunError, LedgerError
from . import (
    is_managed_generation_root,
    open_next_generation,
    append_event,
    finish_run,
    init_pilot,
    record_test_run,
    start_run,
    validate_root,
    validate_series,
    validate_run,
)


_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_ROOT = _REPO / "output" / "task-runs"
_WRITE_COMMANDS = frozenset({"init-pilot", "selfcheck", "start", "event", "finish"})
_MANAGED_WRITE_GUARD_ERROR = "managed generation write path changed"


def _root(args: argparse.Namespace) -> Path:
    command_root = getattr(args, "command_root", None)
    if command_root is not None:
        return Path(command_root)
    return Path(args.root)


def _write_root_snapshot(root: Path) -> Path:
    """Capture the pre-write realpath and reject managed generation roots."""

    checked = root.resolve(strict=False)
    if is_managed_generation_root(root):
        raise LedgerError("managed generation への CLI write は禁止")
    return checked


def _verify_write_root(root: Path, checked: Path) -> None:
    """Re-check the namespace immediately before a CLI write."""

    try:
        current = root.resolve(strict=False)
    except OSError as exc:
        raise LedgerError(_MANAGED_WRITE_GUARD_ERROR) from exc
    if current != checked or is_managed_generation_root(root):
        raise LedgerError(_MANAGED_WRITE_GUARD_ERROR)


def _add_stage_reference(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--stage-id")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="task-run/v1 development-observation ledger")
    parser.add_argument(
        "--root",
        default=os.environ.get("IZANAGI_TASK_RUNS_ROOT", str(_DEFAULT_ROOT)),
        help="ledger root (default: checkout-local output/task-runs)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init-pilot", help="pilot.json を create-only 生成")
    init.add_argument("command_root", nargs="?")
    check = commands.add_parser("selfcheck", help="実 filesystem 前提を canary 実測")
    check.add_argument("command_root", nargs="?")

    start = commands.add_parser("start", help="task-run を開始")
    start.add_argument("--slug", required=True)
    start.add_argument("--objective", required=True)
    start.add_argument("--task-class", required=True, type=int, choices=(1, 2, 3))
    start.add_argument(
        "--task-kind", required=True,
        choices=("implementation", "audit-review", "investigation", "documentation", "integration", "other"),
    )

    event = commands.add_parser("event", help="型付き event を追記")
    event.add_argument("task_run_id")
    event_types = event.add_subparsers(dest="event_type", required=True)

    stage_start = event_types.add_parser("stage_start")
    stage_start.add_argument("--stage-id", required=True)
    stage_start.add_argument("--stage", required=True, choices=("planning", "research", "implementation", "test", "review", "documentation", "integration", "other"))

    stage_end = event_types.add_parser("stage_end")
    stage_end.add_argument("--stage-id", required=True)
    stage_end.add_argument("--stage", required=True, choices=("planning", "research", "implementation", "test", "review", "documentation", "integration", "other"))
    stage_end.add_argument("--outcome", required=True, choices=("completed", "failed", "interrupted"))

    agent = event_types.add_parser("agent_run")
    _add_stage_reference(agent)
    agent.add_argument("--agent-run-id", required=True)
    agent.add_argument("--product", required=True)
    agent.add_argument("--model", required=True)
    agent.add_argument("--reasoning", required=True)
    agent.add_argument("--role", required=True, choices=("author", "reviewer", "researcher", "manager", "integrator"))
    agent.add_argument("--scope")
    agent.add_argument("--status", required=True, choices=("completed", "failed", "cancelled", "timed-out"))
    agent.add_argument("--duration-s", required=True, type=float)
    for name in ("input", "output", "cached", "total"):
        agent.add_argument(f"--{name}-tokens", type=int)

    test = event_types.add_parser("test_run")
    _add_stage_reference(test)
    test.add_argument("--suite-id", required=True)
    test.add_argument("--suite-kind", required=True, choices=("targeted", "full", "docs-check", "provenance-check", "static-check"))
    test.add_argument("--duration-s", required=True, type=float)
    for name in ("collected", "passed", "failed", "skipped"):
        test.add_argument(f"--{name}", type=int)
    test.add_argument("--exit-status", required=True, type=int)
    test.add_argument("--trigger", default="unspecified", choices=("baseline", "after-change", "after-failure", "final", "review-fix", "unspecified"))
    test.add_argument("--collected-node-digest")

    wait = event_types.add_parser("wait")
    wait.add_argument("--wait-kind", required=True, choices=("user", "approval", "scheduler", "resource", "tool", "external", "other"))
    wait.add_argument("--duration-s", required=True, type=float)

    finding = event_types.add_parser("finding_summary")
    _add_stage_reference(finding)
    finding.add_argument("--review-id", required=True)
    finding.add_argument("--review-kind", required=True, choices=("self", "independent", "user", "automated"))
    for name in ("real", "refuted", "unresolved"):
        finding.add_argument(f"--{name}", required=True, type=int)

    commit = event_types.add_parser("commit")
    commit.add_argument("--commit-sha", required=True)
    commit.add_argument("--relation", required=True, choices=("authored", "integrated", "referenced"))

    rework = event_types.add_parser("rework")
    _add_stage_reference(rework)
    rework.add_argument("--rework-id", required=True)
    rework.add_argument("--cause", required=True, choices=("test-failure", "review-finding", "requirement-change", "integration-conflict", "implementation-defect", "other"))
    rework.add_argument("--duration-s", required=True, type=float)

    finish = commands.add_parser("finish", help="task_end を追記")
    finish.add_argument("task_run_id")
    finish.add_argument("--outcome", required=True, choices=("completed", "blocked", "abandoned", "interrupted"))

    validate = commands.add_parser("validate", help="run/root を strict validate")
    validate.add_argument("task_run_id", nargs="?")
    validate.add_argument("--all", action="store_true", dest="validate_all")
    validate.add_argument("--require-finished", action="store_true")

    commands.add_parser(
        "validate-series",
        help="repo sibling series を read-only に fail-closed validate",
    )
    commands.add_parser(
        "open-next-generation",
        help="明示操作として次世代 generation を作成",
    )
    return parser


def _event_payload(args: argparse.Namespace) -> Mapping[str, object]:
    event = args.event_type
    if event == "stage_start":
        return {"stage_id": args.stage_id, "stage": args.stage}
    if event == "stage_end":
        return {"stage_id": args.stage_id, "stage": args.stage, "outcome": args.outcome}
    if event == "agent_run":
        return {
            "stage_id": args.stage_id,
            "agent_run_id": args.agent_run_id,
            "product": args.product,
            "model": args.model,
            "reasoning": args.reasoning,
            "role": args.role,
            "scope": args.scope,
            "status": args.status,
            "duration_s": args.duration_s,
            "tokens": {
                "input_tokens": args.input_tokens,
                "output_tokens": args.output_tokens,
                "cached_tokens": args.cached_tokens,
                "total_tokens": args.total_tokens,
            },
        }
    if event == "test_run":
        return {
            "stage_id": args.stage_id,
            "suite_id": args.suite_id,
            "suite_kind": args.suite_kind,
            "duration_s": args.duration_s,
            "collected": args.collected,
            "passed": args.passed,
            "failed": args.failed,
            "skipped": args.skipped,
            "exit_status": args.exit_status,
            "trigger": args.trigger,
            "collected_node_digest": args.collected_node_digest,
        }
    if event == "wait":
        return {"wait_kind": args.wait_kind, "duration_s": args.duration_s}
    if event == "finding_summary":
        return {
            "stage_id": args.stage_id,
            "review_id": args.review_id,
            "review_kind": args.review_kind,
            "real": args.real,
            "refuted": args.refuted,
            "unresolved": args.unresolved,
        }
    if event == "commit":
        return {"commit_sha": args.commit_sha, "relation": args.relation}
    if event == "rework":
        return {
            "stage_id": args.stage_id,
            "rework_id": args.rework_id,
            "cause": args.cause,
            "duration_s": args.duration_s,
        }
    raise LedgerError(f"unknown CLI event: {event}")


def _print_record(record: Mapping[str, object]) -> None:
    print(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _cli_diagnostic(exc: LedgerError) -> str:
    """Project task-run exceptions into the fixed CLI vocabulary."""

    if isinstance(exc, PilotClosedError):
        return f"pilot-closed:{exc.reason.replace('_', '-')}"
    if isinstance(exc, DamagedRunError):
        return "recording-unavailable:series-invalid"
    if exc.args and exc.args[0] in {
        "managed generation への CLI write は禁止",
        _MANAGED_WRITE_GUARD_ERROR,
    }:
        # Keep the stable human-facing phrase used by the CLI guard without
        # echoing the exception object or any path/selector supplied to it.
        return "recording-unavailable:managed-generation (managed generation)"
    return "recording-unavailable:filesystem"


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = _root(args)
    checked_write_root: Path | None = None
    try:
        if args.command in _WRITE_COMMANDS:
            checked_write_root = _write_root_snapshot(root)
        if args.command == "init-pilot":
            assert checked_write_root is not None
            _verify_write_root(root, checked_write_root)
            init_pilot(root)
        elif args.command == "selfcheck":
            assert checked_write_root is not None
            _verify_write_root(root, checked_write_root)
            selfcheck(root)
        elif args.command == "start":
            assert checked_write_root is not None
            _verify_write_root(root, checked_write_root)
            print(start_run(
                root,
                slug=args.slug,
                objective=args.objective,
                task_class=args.task_class,
                task_kind=args.task_kind,
            ))
        elif args.command == "event":
            assert checked_write_root is not None
            _verify_write_root(root, checked_write_root)
            _print_record(append_event(root, args.task_run_id, args.event_type, _event_payload(args)))
        elif args.command == "finish":
            assert checked_write_root is not None
            _verify_write_root(root, checked_write_root)
            _print_record(finish_run(root, args.task_run_id, args.outcome))
        elif args.command == "validate":
            if args.validate_all:
                if args.task_run_id is not None:
                    raise LedgerError("validate --all と task_run_id は同時指定できない")
                report = validate_series(root)
                print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
                if not report.is_valid:
                    return 1
            else:
                if args.task_run_id is None:
                    raise LedgerError("validate には task_run_id または --all が必要")
                validated = validate_run(root / args.task_run_id, require_finished=args.require_finished)
                print(f"valid {validated.task['task_run_id']}")
        elif args.command == "validate-series":
            report = validate_series(_REPO)
            print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            if not report.is_valid:
                return 1
        elif args.command == "open-next-generation":
            print(open_next_generation(_REPO))
        return 0
    except (DamagedRunError, LedgerError) as exc:
        print(f"task-run: {_cli_diagnostic(exc)}", file=sys.stderr)
        cause = exc.__cause__
        if isinstance(cause, OSError) and cause.errno not in {
            getattr(os, "ENOENT", 2), getattr(os, "EEXIST", 17), getattr(os, "ELOOP", 40),
        }:
            return 2
        return 1
    except OSError as exc:
        del exc
        print("task-run: recording-unavailable:filesystem", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
