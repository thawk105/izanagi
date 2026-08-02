# -*- coding: utf-8 -*-
"""T-316 admission policy の単一理由 mutation controls。"""
from __future__ import annotations

import sys
from pathlib import Path

ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR))

from campaign.build_admission import (  # noqa: E402
    BuildAdmission,
    BuildAdmissionError,
    BuildProvenance,
    require_build_admission,
)


def _assert_rejected(*args, message, **kwargs):
    caught = None
    try:
        BuildAdmission(*args, **kwargs)
    except BuildAdmissionError as exc:
        caught = exc
    assert caught is not None
    assert message in str(caught)


def test_m1_coder_derived_without_opt_in_has_one_rejection_reason():
    _assert_rejected(
        BuildProvenance.CODER_DERIVED,
        message="明示 opt-in",
    )


def test_m2_noncoder_opt_in_has_one_rejection_reason():
    _assert_rejected(
        BuildProvenance.MACHINE_SWEEP,
        coder_derived_opt_in=True,
        message="CODER_DERIVED build にだけ",
    )


def test_m5_stock_or_pinned_is_the_minimal_positive_control():
    admission = require_build_admission(
        BuildAdmission(BuildProvenance.STOCK_OR_PINNED)
    )
    assert admission.as_wal_receipt() == {
        "provenance_class": "STOCK_OR_PINNED",
        "coder_derived_opt_in": False,
    }


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {fn.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
