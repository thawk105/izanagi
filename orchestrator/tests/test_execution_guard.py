# -*- coding: utf-8 -*-
"""共有 execution guard leaf (C3-10) の machine-pin / receipt / 照合契約テスト。

env_contract の唯一の登録 env (linux-baremetal) を実 lookup し、machine-pin の同値・
receipt の形・照合ヘルパ (存在と一致の両検査) を固定する。pytest 非依存の _run() 自走
harness を末尾に持つ (二重 runner 規律)。
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)
sys.path.insert(0, _HERE)

from calibrator import schema_v2 as sv2  # noqa: E402
from campaign import env_attestation as ea  # noqa: E402
from campaign import env_contract as ec  # noqa: E402
from campaign import execution_guard as eg  # noqa: E402
from test_schema_v2 import _valid_document  # noqa: E402


_ENV = "linux-baremetal"


def _contract():
    return ec.lookup(_ENV)


def test_assert_machine_pin_accepts_matching_env_tag():
    eg.assert_machine_pin(_contract(), machine_env_tag=_ENV)  # 例外なし


def test_assert_machine_pin_rejects_foreign_env_tag():
    try:
        eg.assert_machine_pin(_contract(), machine_env_tag="foreign-machine")
    except eg.ExecutionGuardError as exc:
        assert "machine-pin" in str(exc)
    else:
        raise AssertionError("foreign machine env_tag が machine-pin で拒否されない")


def test_build_receipt_shape_and_contract_binding():
    contract = _contract()
    receipt = eg.build_receipt(contract, now_fn=lambda: _FixedNow())
    assert receipt["schema"] == eg.RECEIPT_SCHEMA
    assert receipt["env_tag"] == _ENV
    assert receipt["contract_sha256"] == contract.contract_sha256
    assert set(receipt["attestation"]) == {
        "hostname", "boot_id", "cpuset", "captured_utc",
    }
    assert receipt["attestation"]["captured_utc"] == "2026-07-18T00:00:00+00:00"


def test_receipt_matches_contract_accepts_consistent_receipt():
    contract = _contract()
    receipt = eg.build_receipt(contract)
    assert eg.receipt_matches_contract(
        receipt, env_tag=_ENV, contract_sha256=contract.contract_sha256,
        attestation_mode="none",
    )


def test_receipt_matches_contract_requires_explicit_attestation_mode():
    contract = _contract()
    try:
        eg.receipt_matches_contract(
            eg.build_receipt(contract),
            env_tag=_ENV,
            contract_sha256=contract.contract_sha256,
        )
    except TypeError:
        return
    raise AssertionError("attestation_mode 省略を暗黙 mode=none として受理した")


def test_receipt_matches_contract_rejects_mismatch_and_missing_attestation():
    contract = _contract()
    receipt = eg.build_receipt(contract)
    # contract_sha256 不一致。
    assert not eg.receipt_matches_contract(
        receipt, env_tag=_ENV, contract_sha256="1" * 64,
        attestation_mode="none",
    )
    # env_tag 不一致。
    assert not eg.receipt_matches_contract(
        receipt, env_tag="other", contract_sha256=contract.contract_sha256,
        attestation_mode="none",
    )
    # attestation 欠落は恒真受理でなく拒否。
    stripped = dict(receipt)
    stripped.pop("attestation")
    assert not eg.receipt_matches_contract(
        stripped, env_tag=_ENV, contract_sha256=contract.contract_sha256,
        attestation_mode="none",
    )
    # attestation の key 集合が不完全なら拒否。
    bad_attest = dict(receipt)
    bad_attest["attestation"] = {"hostname": "h"}
    assert not eg.receipt_matches_contract(
        bad_attest, env_tag=_ENV, contract_sha256=contract.contract_sha256,
        attestation_mode="none",
    )
    # 非 Mapping は拒否。
    assert not eg.receipt_matches_contract(
        None, env_tag=_ENV, contract_sha256=contract.contract_sha256,
        attestation_mode="none",
    )


def _receipt_v2():
    return {
        "schema": eg.RECEIPT_SCHEMA_V2,
        "env_tag": _ENV,
        "contract_sha256": "a" * 64,
        "attestation_profile_sha256": "b" * 64,
        "captured_utc": "2026-07-18T00:00:00Z",
        "probe": {"method": "strict-sysfs", "version": "1"},
        "comparisons": [
            {"field": "cpu.model", "expected": 143, "observed": 143,
             "verdict": "pass"},
        ],
    }


def test_validate_receipt_v2_accepts_exact_all_pass_shape():
    assert eg.validate_receipt_v2(_receipt_v2()) is None


def test_validate_receipt_v2_rejects_each_shape_or_value_error():
    mutations = []
    for key in _receipt_v2():
        mutations.append((f"missing {key}", lambda r, key=key: r.pop(key)))
    mutations.extend([
        ("unknown", lambda r: r.__setitem__("unknown", 1)),
        ("schema", lambda r: r.__setitem__("schema", eg.RECEIPT_SCHEMA)),
        ("env type", lambda r: r.__setitem__("env_tag", True)),
        ("contract hash", lambda r: r.__setitem__("contract_sha256", "A" * 64)),
        ("profile hash", lambda r: r.__setitem__("attestation_profile_sha256", None)),
        ("captured naive", lambda r: r.__setitem__("captured_utc", "2026-07-18T00:00:00")),
        ("captured non-UTC", lambda r: r.__setitem__("captured_utc", "2026-07-18T09:00:00+09:00")),
        ("probe missing", lambda r: r["probe"].pop("version")),
        ("probe unknown", lambda r: r["probe"].__setitem__("extra", 1)),
        ("probe type", lambda r: r["probe"].__setitem__("method", 1)),
        ("comparisons type", lambda r: r.__setitem__("comparisons", {})),
        ("comparisons empty", lambda r: r.__setitem__("comparisons", [])),
        ("comparison unknown", lambda r: r["comparisons"][0].__setitem__("extra", 1)),
        ("field empty", lambda r: r["comparisons"][0].__setitem__("field", "")),
        ("verdict fail", lambda r: r["comparisons"][0].__setitem__("verdict", "fail")),
        ("nonfinite", lambda r: r["comparisons"][0].__setitem__("observed", float("nan"))),
    ])
    for label, mutate in mutations:
        receipt = _receipt_v2()
        mutate(receipt)
        try:
            eg.validate_receipt_v2(receipt)
        except eg.ExecutionGuardError:
            continue
        raise AssertionError(f"不正 receipt v2 を拒否しなかった: {label}")


def test_validate_receipt_v2_rejects_duplicate_comparison_field():
    receipt = _receipt_v2()
    receipt["comparisons"].append(dict(receipt["comparisons"][0]))
    try:
        eg.validate_receipt_v2(receipt)
    except eg.ExecutionGuardError:
        return
    raise AssertionError("comparison field 重複を拒否しなかった")


def _required_binding():
    document = _valid_document()
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    calibration = sv2.validate_calibration_v2(raw)
    sha = hashlib.sha256(raw).hexdigest()
    contract = ec.ExecutionEnvironmentContract(
        env_tag=calibration.env_tag,
        clocks_per_us=calibration.clocks_per_us,
        numactl=(),
        attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(path="fixture.json", sha256=sha),
    )
    verified = ea.VerifiedCalibration(
        schema_version=sv2.SCHEMA_VERSION,
        sha256=sha,
        calibration=calibration,
        attestation_profile_sha256=ea.profile_sha256(calibration.attestation_profile),
    )
    return contract, verified


def test_attest_and_build_receipt_uses_production_comparator_and_v2_validator():
    contract, verified = _required_binding()
    receipt = eg.attest_and_build_receipt(
        contract,
        verified,
        probe_fn=lambda: verified.attestation_profile,
        now_fn=lambda: "2026-07-18T00:00:00Z",
    )
    assert receipt["schema"] == eg.RECEIPT_SCHEMA_V2
    assert receipt["contract_sha256"] == contract.contract_sha256
    assert receipt["captured_utc"] == "2026-07-18T00:00:00Z"
    assert len(receipt["comparisons"]) > 10
    assert eg.validate_receipt_v2(receipt) is None
    assert eg.receipt_matches_contract(
        receipt,
        env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
        attestation_mode="required",
        verified_calibration=verified,
    )


def test_attest_and_build_receipt_rejects_mismatch_through_production_comparator():
    """This becomes red if compare_profiles is mutated to return all-pass."""
    contract, verified = _required_binding()
    observed = dataclasses.replace(
        verified.attestation_profile,
        cpu=dataclasses.replace(verified.attestation_profile.cpu, model=144),
    )
    try:
        eg.attest_and_build_receipt(
            contract, verified, probe_fn=lambda: observed,
            now_fn=lambda: "2026-07-18T00:00:00Z",
        )
    except eg.ExecutionGuardError as exc:
        assert "cpu.model" in str(exc)
        return
    raise AssertionError("production comparator の不一致から v2 receipt が発行された")


def test_attest_and_build_receipt_translates_strict_probe_failure():
    contract, verified = _required_binding()

    def failed_probe():
        raise ea.AttestationError("partial cache")

    try:
        eg.attest_and_build_receipt(
            contract, verified, probe_fn=failed_probe,
            now_fn=lambda: "2026-07-18T00:00:00Z",
        )
    except eg.ExecutionGuardError as exc:
        assert "partial cache" in str(exc)
        return
    raise AssertionError("strict probe failure から receipt が発行された")


def test_attest_and_build_receipt_mode_none_delegates_to_v1_builder():
    contract = _contract()
    receipt = eg.attest_and_build_receipt(
        contract,
        ea.VerifiedCalibration(
            schema_version="calibration/v1",
            sha256=ea.GRANDFATHERED_V1_SHA256,
            calibration=None,
            attestation_profile_sha256=None,
        ),
        probe_fn=lambda: (_ for _ in ()).throw(AssertionError("probe must not run")),
        now_fn=lambda: _FixedNow(),
    )
    assert receipt == eg.build_receipt(contract, now_fn=lambda: _FixedNow()) | {
        "attestation": receipt["attestation"],
    }
    assert receipt["schema"] == eg.RECEIPT_SCHEMA


def test_required_contract_rejects_v1_receipt():
    contract, verified = _required_binding()
    legacy = eg.build_receipt(contract)
    assert not eg.receipt_matches_contract(
        legacy,
        env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
        attestation_mode="required",
        verified_calibration=verified,
    )


def test_receipt_v2_recomputes_recorded_expected_observed_and_profile_sha():
    contract, verified = _required_binding()
    receipt = eg.attest_and_build_receipt(
        contract, verified,
        probe_fn=lambda: verified.attestation_profile,
        now_fn=lambda: "2026-07-18T00:00:00Z",
    )

    def accepted(candidate):
        return eg.receipt_matches_contract(
            candidate,
            env_tag=contract.env_tag,
            contract_sha256=contract.contract_sha256,
            attestation_mode="required",
            verified_calibration=verified,
        )

    missing_calibration = copy.deepcopy(receipt)
    assert not eg.receipt_matches_contract(
        missing_calibration,
        env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
        attestation_mode="required",
    )
    bad_profile_sha = copy.deepcopy(receipt)
    bad_profile_sha["attestation_profile_sha256"] = "0" * 64
    assert not accepted(bad_profile_sha)
    bad_expected = copy.deepcopy(receipt)
    next(item for item in bad_expected["comparisons"]
         if item["field"] == "cpu.model")["expected"] = 144
    assert not accepted(bad_expected)
    bad_observed = copy.deepcopy(receipt)
    next(item for item in bad_observed["comparisons"]
         if item["field"] == "cpu.model")["observed"] = 144
    assert not accepted(bad_observed)

    self_consistent_other_machine = copy.deepcopy(receipt)
    cpu_model = next(
        item for item in self_consistent_other_machine["comparisons"]
        if item["field"] == "cpu.model"
    )
    cpu_model.update(expected=144, observed=144, verdict="pass")
    assert not accepted(self_consistent_other_machine)


def test_receipt_consumer_is_independent_of_constant_true_issuer_comparator():
    contract, verified = _required_binding()
    observed = dataclasses.replace(
        verified.attestation_profile,
        cpu=dataclasses.replace(verified.attestation_profile.cpu, model=144),
    )
    original = ea._recorded_verdict
    try:
        ea._recorded_verdict = lambda _field, _expected, _observed: "pass"
        forged_by_mutant = eg.attest_and_build_receipt(
            contract, verified, probe_fn=lambda: observed,
            now_fn=lambda: "2026-07-18T00:00:00Z",
        )
    finally:
        ea._recorded_verdict = original
    assert not eg.receipt_matches_contract(
        forged_by_mutant,
        env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
        attestation_mode="required",
        verified_calibration=verified,
    )


def test_effective_clock_canonical_predicate_golden_vectors():
    """Pin explicit outcomes, including median/mean drift and raw type edges."""
    vectors = [
        {
            "label": "odd-all-inside",
            "expected": {"samples_mhz": [99.0, 100.0, 101.0], "tolerance_pct": 2.0},
            "observed": {"samples_mhz": [99.0, 100.0, 101.0]},
            "want": True,
        },
        {
            "label": "even-inclusive-boundaries",
            "expected": {"samples_mhz": [90.0, 100.0, 100.0, 110.0],
                         "tolerance_pct": 10.0},
            "observed": {"samples_mhz": [90.0, 110.0]},
            "want": True,
        },
        {
            "label": "pegasus-shaped-one-outlier",
            "expected": {"samples_mhz": [100.0, 100.0, 150.0], "tolerance_pct": 2.0},
            "observed": {"samples_mhz": [100.0, 100.0, 150.0]},
            "want": False,
        },
        {
            "label": "mean-drift-same-median-inside",
            "expected": {"samples_mhz": [100.0, 100.0, 119.0], "tolerance_pct": 20.0},
            "observed": {"samples_mhz": [100.0, 100.0, 119.0]},
            "want": True,
        },
        {
            "label": "mean-drift-same-median-outside",
            "expected": {"samples_mhz": [100.0, 100.0, 130.0], "tolerance_pct": 20.0},
            "observed": {"samples_mhz": [100.0, 100.0, 130.0]},
            "want": False,
        },
        {
            "label": "expected-not-mapping",
            "expected": [],
            "observed": {"samples_mhz": [100.0]},
            "want": False,
        },
        {
            "label": "observed-not-mapping",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 2.0},
            "observed": [],
            "want": False,
        },
        {
            "label": "expected-samples-not-list",
            "expected": {"samples_mhz": (100.0,), "tolerance_pct": 2.0},
            "observed": {"samples_mhz": [100.0]},
            "want": False,
        },
        {
            "label": "observed-samples-not-list",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 2.0},
            "observed": {"samples_mhz": (100.0,)},
            "want": False,
        },
        {
            "label": "expected-empty",
            "expected": {"samples_mhz": [], "tolerance_pct": 2.0},
            "observed": {"samples_mhz": [100.0]},
            "want": False,
        },
        {
            "label": "observed-empty",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 2.0},
            "observed": {"samples_mhz": []},
            "want": False,
        },
        {
            "label": "tolerance-bool",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": True},
            "observed": {"samples_mhz": [100.0]},
            "want": False,
        },
        {
            "label": "nonnumeric-sample",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 2.0},
            "observed": {"samples_mhz": ["bad"]},
            "want": False,
        },
        {
            "label": "near-zero-tolerance-inside",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 1e-12},
            "observed": {"samples_mhz": [100.0 + 5e-13]},
            "want": True,
        },
        {
            "label": "near-zero-tolerance-outside",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 1e-12},
            "observed": {"samples_mhz": [100.0 + 2e-12]},
            "want": False,
        },
        {
            "label": "zero-tolerance-exact",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 0.0},
            "observed": {"samples_mhz": [100.0]},
            "want": True,
        },
        {
            "label": "hundred-tolerance-boundaries",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 100.0},
            "observed": {"samples_mhz": [0.0, 200.0]},
            "want": True,
        },
        {
            "label": "hundred-tolerance-outside",
            "expected": {"samples_mhz": [100.0], "tolerance_pct": 100.0},
            "observed": {"samples_mhz": [200.001]},
            "want": False,
        },
    ]

    for vector in vectors:
        got = eg.effective_clock_comparison_passes(
            vector["expected"], vector["observed"],
        )
        assert got is vector["want"], vector["label"]
        consumer_got = eg._independent_comparison_passes(
            "effective_clock.samples_mhz", vector["expected"], vector["observed"],
        )
        assert consumer_got is vector["want"], vector["label"]


class _FixedNow:
    def isoformat(self):
        return "2026-07-18T00:00:00+00:00"


# ===== 二重 runner (pytest 非依存) =====

def _run():
    import traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    npass = nfail = nerr = 0
    for fn in fns:
        try:
            fn()
            npass += 1
        except AssertionError as e:
            nfail += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception:  # noqa: BLE001
            nerr += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(f"\n{npass} passed, {nfail} failed, {nerr} errors (of {len(fns)})")
    return 0 if (nfail == 0 and nerr == 0) else 1


if __name__ == "__main__":
    sys.exit(_run())
