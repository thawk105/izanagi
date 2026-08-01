# -*- coding: utf-8 -*-
"""T-126 の pure protocol / SPRT 境界を固定する。"""
from __future__ import annotations

import itertools
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from qualification.contract import (  # noqa: E402
    ProtocolError,
    balanced_order,
    load_protocol,
    observe_relative,
    operating_characteristics,
    protocol_sha256,
    sprt_decide,
    series_identity,
    validate_protocol,
)


def _reference(bits, cfg):
    upper = math.log((1.0 - cfg["beta"]) / cfg["alpha"])
    lower = math.log(cfg["beta"] / (1.0 - cfg["alpha"]))
    llr = 0.0
    for index, bit in enumerate(bits, 1):
        llr += (
            math.log(cfg["p1"] / cfg["p0"])
            if bit else math.log((1.0 - cfg["p1"]) / (1.0 - cfg["p0"]))
        )
        if llr > upper:
            return "upper_boundary", index
        if llr < lower:
            return "lower_boundary", index
    return ("indeterminate", len(bits)) if len(bits) == cfg["rmax"] else (
        "continuing", len(bits))


def test_protocol_freezes_observational_envelope_and_wmax():
    protocol = load_protocol()
    timing = protocol["timing"]
    assert protocol["authority"] == "evidence-only/no-promotion"
    assert protocol["hold_enforced"] is False
    assert protocol["statistical_claim"] == "none"
    assert timing["member_cap_s"] == 900
    assert timing["round_gap_s"] == 1800
    assert timing["wmax_s"] == 29100
    assert timing["qualification_walltime_s"] == 36000
    assert len(protocol_sha256(protocol)) == 64


def test_all_machine_readable_evidence_schemas_are_valid_draft7():
    schema_dir = _HERE.parent / "qualification"
    names = {
        "t126_marker_schema.json",
        "t126_event_schema.json",
        "t126_evaluation_event_schema.json",
        "t126_series_result_schema.json",
        "t126_final_receipt_schema.json",
        "t126_failure_receipt_schema.json",
    }
    for name in names:
        Draft7Validator.check_schema(json.loads(
            (schema_dir / name).read_text(encoding="utf-8")))


def test_m1_exact_threshold_is_zero_side_and_strictly_above_is_one():
    exact = observe_relative(103.0, 100.0, 0.03)
    above = observe_relative(math.nextafter(103.0, math.inf), 100.0, 0.03)
    negative_exact = observe_relative(97.0, 100.0, 0.03)
    assert (exact.bit, exact.direction) == (0, "within-borrowed-threshold")
    assert (above.bit, above.direction) == (1, "subject-above-threshold")
    assert (negative_exact.bit, negative_exact.direction) == (
        0, "within-borrowed-threshold")


def test_all_256_prefixes_match_reference_and_terminal_suffixes_reject():
    cfg = load_protocol()["sprt"]
    checked = 0
    for length in range(0, cfg["rmax"] + 1):
        for bits in itertools.product((0, 1), repeat=length):
            expected, terminal_index = _reference(bits, cfg)
            if terminal_index < len(bits):
                with pytest.raises(ProtocolError, match="suffix"):
                    sprt_decide(bits, cfg)
            else:
                actual = sprt_decide(bits, cfg)
                assert actual.terminal == expected
                assert actual.rounds == length
            checked += 1
    assert checked == 511


@pytest.mark.parametrize(
    ("true_p", "upper", "lower", "indeterminate", "expected_rounds"),
    [
        (0.5, 0.07812500, 0.78906250, 0.13281250, 4.41406250),
        (0.7, 0.33892516, 0.39182670, 0.26924814, 5.54956630),
        (0.9, 0.84741876, 0.04275010, 0.10983114, 5.20088690),
    ],
)
def test_all_256_sequence_operating_characteristics_golden(
        true_p, upper, lower, indeterminate, expected_rounds):
    actual = operating_characteristics(true_p, load_protocol()["sprt"])
    assert actual["upper_boundary"] == pytest.approx(upper, abs=5e-9)
    assert actual["lower_boundary"] == pytest.approx(lower, abs=5e-9)
    assert actual["indeterminate"] == pytest.approx(indeterminate, abs=5e-9)
    assert actual["expected_rounds"] == pytest.approx(
        expected_rounds, abs=5e-9)


@pytest.mark.parametrize(
    ("bits", "terminal"),
    [
        ((0, 0), "lower_boundary"),
        ((1, 1, 1, 1), "upper_boundary"),
        ((0, 1, 1, 0, 1, 1, 1, 0), "indeterminate"),
    ],
)
def test_clean_synthetic_terminal_positive_controls(bits, terminal):
    assert sprt_decide(bits, load_protocol()["sprt"]).terminal == terminal


def test_sprt_rejects_bool_nonbinary_and_nonfinite_observations():
    cfg = load_protocol()["sprt"]
    for bits in ([True], [2], [0.0]):
        with pytest.raises(ProtocolError):
            sprt_decide(bits, cfg)
    for values in ((math.nan, 1.0), (1.0, math.inf), (0.0, 1.0)):
        with pytest.raises(ProtocolError):
            observe_relative(values[0], values[1], 0.03)


def test_balanced_order_is_seeded_then_exactly_alternating():
    protocol = load_protocol()
    orders = [balanced_order(protocol["order"]["seed"], index)
              for index in range(1, 9)]
    assert all(set(order) == {"subject", "reference"} for order in orders)
    assert all(orders[index] == orders[index - 2] for index in range(2, 8))
    assert all(orders[index] != orders[index - 1] for index in range(1, 8))


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("threshold", "relative"), 0.031),
        (("sprt", "upper_comparison"), ">="),
        (("timing", "member_cap_s"), 901),
        (("environment", "numactl"), ["numactl", "--interleave=all"]),
        (("authority",), "formal"),
    ],
)
def test_protocol_mutations_fail_closed(path, replacement):
    mutated = deepcopy(load_protocol())
    target = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(ProtocolError):
        validate_protocol(mutated)


def test_empty_identity_is_rejected_before_it_can_name_a_series():
    protocol = load_protocol()
    empty = {
        "schema_version": "t126-qualification-series-identity/v1",
        "protocol_sha256": protocol_sha256(protocol),
        "superproject_commit": "a" * 40,
        "superproject_tree": "b" * 40,
        "ccbench_gitlink": "c" * 40,
        "source_snapshots": {},
        "pair_roles": protocol["source"]["members"],
        "workload": protocol["workload"],
        "verification": protocol["verification"],
        "threshold": protocol["threshold"],
        "sprt": protocol["sprt"],
        "timing": protocol["timing"],
        "order_seed": protocol["order"]["seed"],
        "code_identity": {},
        "script_identity": {},
        "toolchain_manifest": {},
    }
    with pytest.raises(ProtocolError, match="source snapshots|required set"):
        series_identity(empty)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
