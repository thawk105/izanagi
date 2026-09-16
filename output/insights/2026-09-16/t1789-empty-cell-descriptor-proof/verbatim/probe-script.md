# 再現 probe の逐語 (repo へは入れない)

Codex `role=author` が作成 (job `t1789-p0-probe-author-1`)。親が login node で実走した。
sha256 = c7b676ba6f67960470e3cae6bfcf11d616838569f5e2efe85d5bab4ff301b442、6292 bytes。
保全先: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1789-empty-cell-descriptor-proof/probe/probe_t1789_counterexample.py`

```python
"""Observe T-1789 using disposable repositories; no expected verdicts.

Run by the parent: fixture helpers create and commit their own temporary repos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

from orchestrator.tests import test_s8c_acceptance_receipt_v2 as t
from orchestrator.campaign import layer3_report
from orchestrator.campaign import s8c_acceptance_receipt as receipt


CASES = (
    "A0-v2-baseline",
    "A1-v2-existing-node",
    "A2-v2-empty-cells-keep-c02",
    "A3-v2-all-six-empty-keep-c02",
    "B1-v2-contradicting-descriptor",
    "B2-v2-contradicting-descriptor-then-empty-keep-c02",
    "C0-v5-baseline",
    "C1-v5-existing-node",
    "C2-v5-empty-cells-keep-c02",
    "C3-v5-contradicting-descriptor-then-empty-keep-c02",
    "C4-v5-build-report-empty-keep-c02",
)
REJECTIONS = (receipt.AcceptanceReceiptError, layer3_report.Layer3ReportError)


def change_report(repo, row, notes, *, contradict=False, empty=False, build=False):
    path = repo / row["report_path"]
    report = json.loads(path.read_bytes())
    if contradict:
        descriptor = report["cells"][0]["descriptor"]
        original = descriptor["read_write"]["read_ratio_percent"]
        notes.update({
            "original_read_ratio_percent": original,
            "original_read_ratio_type": type(original).__name__,
            "original_read_ratio_is_int_80": type(original) is int and original == 80,
        })
        if not notes["original_read_ratio_is_int_80"]:
            raise ValueError("H1/on descriptor read_ratio_percent is not int 80")
        descriptor["read_write"]["read_ratio_percent"] = 79
        notes["descriptor_canonical_sha256"] = hashlib.sha256(
            t._canonical(descriptor)
        ).hexdigest()
        notes["receipt_content_digest_sha256"] = row["arm_execution"][
            "content_digest_sha256"
        ]
    if empty:
        report["cells"] = []
    if build:
        report["do_build"] = True
    report_bytes = t._canonical(report)
    path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()


def observe_downstream(call):
    try:
        call()
    except REJECTIONS as exc:
        return str(exc)
    return "accepted"


def run_case(case, work_root):
    key = case.split("-", 1)[0]
    result = {
        "case": case,
        "schema_version": None,
        "verdict": None,
        "error": None,
        "reason_codes": None,
        "downstream": None,
        "notes": {},
    }
    value = None
    try:
        tmp_path = Path(tempfile.mkdtemp(prefix=f"{key}-", dir=work_root))
        repo, path, value = t._fixture(tmp_path)
        notes = result["notes"]
        if key in {"A1", "A2", "C1", "C2"}:
            change_report(repo, t._trial(value, "H2", "off"), notes, empty=True)
        elif key == "A3":
            for row in value["trials"]:
                change_report(repo, row, notes, empty=True)
        elif key in {"B1", "B2", "C3"}:
            change_report(
                repo, t._trial(value, "H1", "on"), notes,
                contradict=True, empty=key != "B1",
            )
        if key.startswith("C"):
            t._upgrade_to_current(repo, value)
        if key in {"A2", "A3", "B2", "C2", "C3", "C4"}:
            value["non_certifying_reason_codes"] = sorted(
                set(value["non_certifying_reason_codes"]) | {"c02-arm-binding-unproven"}
            )
        if key == "C4":
            change_report(
                repo, t._trial(value, "H2", "off"), notes, empty=True, build=True,
            )
        if key != "A0":
            t._rewrite_receipt(repo, path, value, case)
        verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
        result["verdict"] = "verified"
        result["reason_codes"] = list(verified.receipt.non_certifying_reason_codes)
        if key in {"A2", "C2"}:
            row = t._trial(value, "H2", "off")
            claimed = row["arm_execution"]["content_digest_sha256"]
            expected = receipt._expected_arm_content_digest(
                repo, "H2", "off", row["measurement_head"],
            )
            notes.update({
                "receipt_content_digest_sha256": claimed,
                "expected_arm_content_digest_sha256": expected,
                "content_digest_matches_expected": claimed == expected,
            })
        if key in {"A2", "C0", "C2", "C3"}:
            current = observe_downstream(
                lambda: receipt.require_current_verified_receipt(verified)
            )
            result["downstream"] = current
            if key in {"C2", "C3"}:
                result["downstream"] = {
                    "require_current_verified_receipt": current,
                    "build_accepted_report": observe_downstream(
                        lambda: layer3_report.build_accepted_report(
                            work_root / "nonexistent-campaign",
                            acceptance_receipt=verified,
                        )
                    ),
                }
    except REJECTIONS as exc:
        result.update(verdict="rejected", error=str(exc), reason_codes=None)
    except Exception:
        result.update(
            verdict="probe-error", error=traceback.format_exc(), reason_codes=None,
        )
    finally:
        if value is not None:
            result["schema_version"] = value.get("schema_version")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.work_root.is_absolute() or not args.work_root.is_dir():
        parser.error("--work-root must be an existing absolute directory")
    results = [run_case(case, args.work_root) for case in CASES]
    output = json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    args.out.write_text(output, encoding="utf-8")
    sys.stdout.write(output)
    return 3 if any(row["verdict"] == "probe-error" for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```
