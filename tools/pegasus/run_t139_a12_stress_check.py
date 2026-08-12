#!/usr/bin/env python3
"""Run the T-139 a12 simulation without providing an admission gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.preregistration.stress_check_simulation import (  # noqa: E402
    run_smoke,
    run_stress_check,
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _workers(value: str) -> int | None:
    if value == "auto":
        return None
    return _positive_int(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=_workers, default=None)
    parser.add_argument("--chunk-datasets", type=_positive_int, default=32_768)
    parser.add_argument("--smoke-repetitions", type=_positive_int, default=10_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "full" and args.smoke_repetitions != 10_000:
        _parser().error("--smoke-repetitions cannot modify a full run")
    if args.mode == "full":
        result = run_stress_check(
            repo_root=REPO_ROOT,
            output_path=args.output,
            workers=args.workers,
            chunk_datasets=args.chunk_datasets,
        )
    else:
        result = run_smoke(
            repo_root=REPO_ROOT,
            output_path=args.output,
            repetitions=args.smoke_repetitions,
            workers=args.workers,
            chunk_datasets=args.chunk_datasets,
        )
    print(
        json.dumps(
            {
                "authoritative": result.authoritative,
                "output": str(result.output_path),
                "run_status": result.run_status,
                "verdict": result.verdict,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return 1 if result.run_status == "precondition_failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
