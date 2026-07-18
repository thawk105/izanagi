#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AcquisitionReceipt 候補を W0 の dataclass で検証し canonical JSON 化する。"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_REPO_ROOT, "orchestrator"))

from calibrator.schema_v2 import (  # noqa: E402
    AcquisitionReceipt,
    AllocationReceipt,
    CcbenchReceipt,
    KnownValuesCheck,
    QsubReceipt,
    ToolchainReceipt,
    WalltimeReceipt,
)


_TOP = {
    "qsub", "allocation", "toolchain", "ccbench", "job_script_sha256",
    "walltime", "known_values_check",
}


def build(candidate: Mapping[str, Any]) -> dict[str, Any]:
    if type(candidate) is not dict or set(candidate) != _TOP:
        raise ValueError("acquisition receipt candidate has a non-exact top-level key set")
    receipt = AcquisitionReceipt(
        qsub=QsubReceipt(**candidate["qsub"]),
        allocation=AllocationReceipt(**candidate["allocation"]),
        toolchain=ToolchainReceipt(**candidate["toolchain"]),
        ccbench=CcbenchReceipt(**candidate["ccbench"]),
        job_script_sha256=candidate["job_script_sha256"],
        walltime=WalltimeReceipt(**candidate["walltime"]),
        known_values_check=KnownValuesCheck(**candidate["known_values_check"]),
    )
    return dataclasses.asdict(receipt)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with args.input.open("r", encoding="utf-8") as handle:
            candidate = json.load(handle)
        result = build(candidate)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except Exception as exc:
        print(f"make_acquisition_receipt: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
