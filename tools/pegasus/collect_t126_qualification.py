#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Close one finished T-126 PBS attempt into a final or failure receipt."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    collect_p = sub.add_parser("collect")
    collect_p.add_argument("--repo-root", type=Path, required=True)
    collect_p.add_argument("--attempt-id", required=True)
    collect_p.add_argument("--submission-receipt", type=Path, required=True)
    collect_p.add_argument("--job-result", type=Path)
    collect_p.add_argument(
        "--stdout", type=Path, required=True, dest="stdout_path")
    collect_p.add_argument(
        "--stderr", type=Path, required=True, dest="stderr_path")
    collect_p.add_argument("--accounting", type=Path, required=True)
    verify_p = sub.add_parser("verify")
    verify_p.add_argument("--repo-root", type=Path, required=True)
    verify_p.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    sys.path.insert(0, str(args.repo_root))
    try:
        from orchestrator.qualification.collector import (
            collect,
            verify_post_job_receipt,
        )
        if args.mode == "verify":
            result = verify_post_job_receipt(
                args.receipt, repo_root=args.repo_root)
            print(result)
            return 0 if result.integrity_status == "valid" else 2
        target = collect(
            repo_root=args.repo_root,
            attempt_id=args.attempt_id,
            submission_receipt=args.submission_receipt,
            job_result=args.job_result,
            scheduler_stdout=args.stdout_path,
            scheduler_stderr=args.stderr_path,
            accounting=args.accounting,
        )
    except Exception as exc:
        print(f"collect_t126_qualification: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
