#!/usr/bin/env python3
"""staging に固定した argv で calibrator にプロセス置換する。"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: exec_calibrate.py ARGV_JSON", file=sys.stderr)
        return 2

    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"cannot read calibrate argv JSON: {exc}", file=sys.stderr)
        return 2

    if (
        not isinstance(payload, list)
        or not payload
        or not all(isinstance(arg, str) for arg in payload)
        or not payload[0]
    ):
        print("calibrate argv JSON must be a non-empty string array", file=sys.stderr)
        return 2

    executable = payload[0]
    if os.sep not in executable:
        resolved = shutil.which(executable)
        if resolved is None:
            print(f"calibrate executable not found: {executable}", file=sys.stderr)
            return 2
        executable = resolved

    try:
        os.execv(executable, payload)
    except OSError as exc:
        print(f"cannot exec calibrate argv: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
