#!/usr/bin/env python3
"""Explicit non-native Codex role launcher。

credentialもexternal modelも使わないwire/namespace probeだけを提供する。``--live``は
実surfaceをprobeした後、常にBLOCKEDを返すactivation負例である。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.codex_roles.events import (EventValidationError,
                                             strict_json_loads)  # noqa: E402
from orchestrator.codex_roles.launcher import (  # noqa: E402
    MAX_PROMPT_BYTES,
    RuntimeIsolationError,
    RuntimeOptions,
    attest_forced_view_image_containment,
    attest_role,
    result_as_json,
    run_role,
)
from orchestrator.codex_roles.probe import WireAttestationError  # noqa: E402
from orchestrator.codex_roles.policy import RolePolicyError  # noqa: E402
from orchestrator.codex_roles.spec import RoleSpecError  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="dormant Codex roleをouter bwrap内でattestする"
    )
    parser.add_argument("--role", required=True, help="manifest上の明示role名")
    parser.add_argument(
        "--input", default="-", metavar="JSON_FILE",
        help="projection JSON file。'-' はstdin (default)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live", action="store_true",
        help="activationを要求（current runtimeはprobe後BLOCKED、official provider未呼出）",
    )
    mode.add_argument(
        "--forced-view-image-probe", action="store_true",
        help="fake Responsesでview_image(host path)のENOENTを検証（external modelなし）",
    )
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--probe-timeout", type=float, default=30.0)
    return parser


def _read_input(path: str) -> object:
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_PROMPT_BYTES + 1)
        label = "stdin"
    else:
        source = Path(path)
        with source.open("rb") as stream:
            raw = stream.read(MAX_PROMPT_BYTES + 1)
        label = str(source)
    if len(raw) > MAX_PROMPT_BYTES:
        raise EventValidationError(f"{label}: input size上限超過")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise EventValidationError(f"{label}: UTF-8でない: {exc}") from exc
    return strict_json_loads(text, label=label, max_bytes=MAX_PROMPT_BYTES)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.probe_timeout <= 0:
        print("error: probe-timeoutは正数でなければならない", file=sys.stderr)
        return 2
    try:
        projected_input = _read_input(args.input)
        options = RuntimeOptions(
            codex_bin=args.codex_bin,
            repo_root=_ROOT,
            probe_timeout_s=args.probe_timeout,
        )
        if args.live:
            result = run_role(args.role, projected_input, options)
        elif args.forced_view_image_probe:
            result = attest_forced_view_image_containment(
                args.role, projected_input, options
            )
        else:
            result = attest_role(args.role, projected_input, options)
        sys.stdout.write(result_as_json(result))
        return 0
    except (EventValidationError, OSError, RolePolicyError, RoleSpecError, RuntimeIsolationError,
            WireAttestationError) as exc:
        # prompt/stdout本文は表示せず、fail-closed理由だけを返す。
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
