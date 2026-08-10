#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""計算ノードの env attestation probe を JSON 化する薄い entry point。"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


# orchestrator/calibrate.py と同じく、repo root を import root にする。
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _REPO_ROOT)


def _write_create_only(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def run(
    *,
    output: Optional[Path] = None,
    importer: Callable[[str], object] = importlib.import_module,
) -> tuple[int, dict[str, Any]]:
    try:
        module = importer("orchestrator.campaign.env_attestation")
        probe_fn = getattr(module, "probe")
        serialize_profile = getattr(module, "observed_profile_to_dict")
    except Exception as exc:  # import/attribute failure must remain visible and non-zero
        payload: dict[str, Any] = {
            "schema_version": "pegasus-probe-output/v2",
            "ok": False,
            "observed_epoch": int(time.time()),
            "error": {
                "stage": "import",
                "type": type(exc).__name__,
                "message": str(exc) or type(exc).__name__,
            },
        }
        rc = 2
    else:
        try:
            profile = serialize_profile(probe_fn())
            payload = {
                "schema_version": "pegasus-probe-output/v2",
                "ok": True,
                "observed_epoch": int(time.time()),
                "profile": profile,
            }
            rc = 0
        except Exception as exc:
            payload = {
                "schema_version": "pegasus-probe-output/v2",
                "ok": False,
                "observed_epoch": int(time.time()),
                "error": {
                    "stage": "probe",
                    "type": type(exc).__name__,
                    "message": str(exc) or type(exc).__name__,
                },
            }
            rc = 3

    if output is not None:
        try:
            _write_create_only(output, payload)
        except Exception as exc:
            payload = {
                "schema_version": "pegasus-probe-output/v2",
                "ok": False,
                "observed_epoch": int(time.time()),
                "error": {
                    "stage": "write",
                    "type": type(exc).__name__,
                    "message": str(exc) or type(exc).__name__,
                },
            }
            rc = 4
    return rc, payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        help="同じ JSON を create-only で保存するパス (stdout には常に出す)",
    )
    args = parser.parse_args(argv)
    rc, payload = run(output=args.output)
    json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
