#!/usr/bin/env python3
"""dev-wave の Claude session 使用量を repo 外 artifact へ保存する。"""
from __future__ import annotations

import sys

_ORIGINAL_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    import argparse
    import json
    import os
    import tempfile
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any, Sequence

    _REPO_ROOT = Path(__file__).resolve().parents[1]
    if os.fspath(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, os.fspath(_REPO_ROOT))

    from orchestrator.campaign import site_policy  # noqa: E402
    from tools.claude_session_ledger import (  # noqa: E402
        MAX_MAX_FILES,
        collect_report,
    )
finally:
    sys.dont_write_bytecode = _ORIGINAL_DONT_WRITE_BYTECODE


def _absolute_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("絶対 path を指定すること")
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="dev-wave の Claude session 使用量 artifact を収集する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "先頭が '-' の project slug は --project=<slug> の等号形で指定すること。\n"
            "終了値:\n"
            "  0  collection.status=complete または --help\n"
            "  1  PEGASUS_SUSPECT の blocked、incomplete、missing、error、未知 status、\n"
            "     その他の失敗\n"
            "  2  外側 argv を argparse が拒否\n"
            "  3  PEGASUS_LOGIN と確証できた site の blocked"
        ),
    )
    parser.add_argument("--wave-id", required=True)
    parser.add_argument("--out", required=True, type=_absolute_path)
    parser.add_argument("--project", action="append", default=[], metavar="SLUG")
    parser.add_argument("--cwd-under", required=True, type=_absolute_path)
    parser.add_argument("--projects-root", type=Path)
    parser.add_argument("--since", metavar="ISO8601")
    parser.add_argument("--until", metavar="ISO8601")
    parser.add_argument(
        "--max-files", type=int, default=MAX_MAX_FILES, metavar="N"
    )
    return parser


def _selector(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "projects_root": (
            os.fspath(args.projects_root) if args.projects_root is not None else None
        ),
        "projects": list(args.project),
        "cwd_under": os.fspath(args.cwd_under),
        "since": args.since,
        "until": args.until,
        "max_files": args.max_files,
        "include_sidechains": True,
    }


def _artifact(
    args: argparse.Namespace,
    *,
    site: str,
    status: str,
    reasons: list[str],
    collector_exit_code: int | None = None,
    ledger_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "artifact_type": "izanagi.dev-wave.claude-usage",
        "schema_version": 1,
        "wave_id": args.wave_id,
        "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "selector": _selector(args),
        "collection": {
            "status": status,
            "reasons": reasons,
            "collector_exit_code": collector_exit_code,
            "site": site,
        },
        "ledger_report": ledger_report,
    }


def _collector_argv(args: argparse.Namespace) -> list[str]:
    argv: list[str] = []
    if args.projects_root is not None:
        argv.append(f"--projects-root={os.fspath(args.projects_root)}")
    for project in args.project:
        argv.append(f"--project={project}")
    argv.append(f"--cwd-under={os.fspath(args.cwd_under)}")
    if args.since is not None:
        argv.append(f"--since={args.since}")
    if args.until is not None:
        argv.append(f"--until={args.until}")
    argv.extend((f"--max-files={args.max_files}", "--include-sidechains"))
    return argv


def _collect(args: argparse.Namespace, site: str) -> dict[str, Any]:
    try:
        result = collect_report(_collector_argv(args))
        report = result.report
        model_calls = report["root"]["model_calls"] + report["sidechains"][
            "model_calls"
        ]
        if model_calls == 0:
            status = "missing"
            reasons = ["root.model_calls + sidechains.model_calls is zero"]
        else:
            reasons = []
            if report["population"]["limit_reached"]:
                reasons.append("population.limit_reached is true")
            if report["issues"]:
                reasons.append("collector reported issues")
            status = "incomplete" if reasons else "complete"
        return _artifact(
            args,
            site=site,
            status=status,
            reasons=reasons,
            collector_exit_code=result.exit_code,
            ledger_report=report,
        )
    except SystemExit as exc:
        return _artifact(
            args,
            site=site,
            status="error",
            reasons=[f"collector rejected arguments with SystemExit({exc.code})"],
        )
    except Exception as exc:
        return _artifact(
            args,
            site=site,
            status="error",
            reasons=[f"collector failed: {type(exc).__name__}: {exc}"],
        )


def _validated_out(path: Path) -> Path:
    resolved = path.resolve()
    for ancestor in resolved.parents:
        marker = ancestor / ".git"
        if marker.is_file() or (marker.is_dir() and (marker / "HEAD").exists()):
            raise ValueError("--out は repo 外を指定すること")
    return resolved


def _publish_create_only(out: Path, artifact: dict[str, Any]) -> None:
    fd, temporary = tempfile.mkstemp(
        prefix=f".{out.name}.", suffix=".tmp", dir=out.parent
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = -1
            json.dump(
                artifact,
                stream,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_path, out)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _run(argv: Sequence[str] | None) -> int:
    args = _parser().parse_args(argv)
    out = _validated_out(args.out)
    site = site_policy.current_site(require_evidence=True)
    if not args.project:
        artifact = _artifact(
            args,
            site=site,
            status="error",
            reasons=["at least one --project is required"],
        )
    elif site_policy.refuses_heavy_work(site):
        reason = (
            "Pegasus login node blocks the unclassified collector"
            if site_policy.is_pegasus_login(site)
            else "site evidence is insufficient to run the unclassified collector"
        )
        artifact = _artifact(
            args,
            site=site,
            status="blocked",
            reasons=[reason],
        )
    else:
        artifact = _collect(args, site)

    _publish_create_only(out, artifact)
    if artifact["collection"]["status"] != "complete":
        for reason in artifact["collection"]["reasons"]:
            print(
                f"collect_wave_usage: {artifact['collection']['status']}: {reason}",
                file=sys.stderr,
            )
    status = artifact["collection"]["status"]
    if status == "complete":
        return 0
    if status == "blocked" and site_policy.is_pegasus_login(
        artifact["collection"]["site"]
    ):
        return 3
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return _run(argv)
    except SystemExit as exc:
        return exc.code if exc.code in (0, 2) else 1
    except Exception as exc:
        print(f"collect_wave_usage: error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
