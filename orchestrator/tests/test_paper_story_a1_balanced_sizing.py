#!/usr/bin/env python3
"""Tests for the paired-mean balanced A-1 sizing generator and replay."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import statistics
import sys
import tempfile
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import size_paper_story_a1_balanced as generator  # noqa: E402
from tools import verify_paper_story_a1_balanced_sizing as verifier  # noqa: E402


def _pilot_document() -> dict[str, object]:
    workloads = []
    clock = 1_000_000
    for workload_index, name in enumerate(generator.WORKLOADS):
        mapping = generator.TARGET_ARM_MAPPING[name]
        rows = []
        for block in range(12):
            pair_indexes = list(range(block * 5, block * 5 + 5))
            arm_order = (
                [mapping["variant"], mapping["baseline"]]
                if block % 2 == 0
                else [mapping["baseline"], mapping["variant"]]
            )
            for arm in arm_order:
                for pair in pair_indexes:
                    position = pair % 5
                    baseline = 1_000.0 + workload_index * 100.0 + block * 0.2 + position * 0.01
                    # Nonzero pair and block variation, deliberately tiny relative
                    # to the 3% floor so the one-candidate positive certificate passes.
                    difference = (block - 5.5) * 0.03 + (position - 2) * 0.01
                    tps = baseline + difference if arm == mapping["variant"] else baseline
                    rows.append(
                        {
                            "arm": arm,
                            "block": block,
                            "block_position": position,
                            "ended_at_ns": clock + 5,
                            "group": pair // 10,
                            "pair_index": pair,
                            "started_at_ns": clock,
                            "tps": tps,
                        }
                    )
                    clock += 10
        workloads.append({"observations": rows, "workload": name})
    return {
        "final_estimate_eligible": False,
        "schema_version": generator.PILOT_SCHEMA,
        "study_id": generator.PILOT_STUDY_ID,
        "workloads": workloads,
    }


def _write_pilot(directory: Path, document: dict[str, object] | None = None) -> Path:
    path = directory / "pilot.json"
    path.write_bytes(
        generator.canonical_json_bytes(document if document is not None else _pilot_document())
    )
    return path


def _config(n_min: int = 28, n_max: int = 30) -> generator.SizingConfig:
    return generator.SizingConfig(generator.ROOT_SEED_DIGEST, 32, 128, n_min, n_max)


def _verify_config(n_min: int = 28, n_max: int = 30) -> verifier.VerificationConfig:
    return verifier.VerificationConfig(verifier.ROOT_SEED_DIGEST, 32, 128, n_min, n_max)


def _assert_raises(exception_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except exception_type as exc:
        return exc
    raise AssertionError(f"{exception_type.__name__} was not raised")


def test_pilot_exact_shape_accepts_positive_and_rejects_uncoerced_or_unbalanced_rows():
    with tempfile.TemporaryDirectory(prefix="a1-balanced-pilot-shape-") as raw_dir:
        directory = Path(raw_dir)
        positive = _write_pilot(directory)
        derived = generator.derive_pilot(positive)
        assert [item["workload"] for item in derived["planning"]] == list(generator.WORKLOADS)
        assert all(item["pair_count"] == 60 for item in derived["planning"])
        assert all(item["block_lead_counts"] == {"baseline-first": 6, "variant-first": 6} for item in derived["planning"])

        base = _pilot_document()
        mutations = []
        bool_tps = copy.deepcopy(base)
        bool_tps["workloads"][0]["observations"][0]["tps"] = True
        mutations.append((bool_tps, "uncoerced numeric"))
        text_tps = copy.deepcopy(base)
        text_tps["workloads"][0]["observations"][0]["tps"] = "1000"
        mutations.append((text_tps, "uncoerced numeric"))
        bool_index = copy.deepcopy(base)
        bool_index["workloads"][0]["observations"][0]["pair_index"] = False
        mutations.append((bool_index, "exact integer"))
        nonpositive = copy.deepcopy(base)
        nonpositive["workloads"][0]["observations"][0]["tps"] = 0.0
        mutations.append((nonpositive, "finite positive"))
        wrong_count = copy.deepcopy(base)
        wrong_count["workloads"][0]["observations"].pop()
        mutations.append((wrong_count, "observation count"))
        wrong_coordinate = copy.deepcopy(base)
        wrong_coordinate["workloads"][0]["observations"][0]["group"] = 1
        mutations.append((wrong_coordinate, "schedule coordinates"))
        wrong_order = copy.deepcopy(base)
        first = wrong_order["workloads"][0]["observations"][0]
        first["started_at_ns"], first["ended_at_ns"] = 99_000_000, 99_000_005
        mutations.append((wrong_order, "chronological"))
        for index, (document, message) in enumerate(mutations):
            path = directory / f"bad-{index}.json"
            path.write_bytes(generator.canonical_json_bytes(document))
            error = _assert_raises(generator.SizingError, generator.derive_pilot, path)
            assert message in str(error)


def test_m6_sigma_certificate_binds_block_chi_square_coefficient_and_conservative_reason():
    with tempfile.TemporaryDirectory(prefix="a1-balanced-sigma-") as raw_dir:
        pilot = _write_pilot(Path(raw_dir))
        derived = generator.derive_pilot(pilot)
        source = _pilot_document()["workloads"][0]["observations"]
        mapping = generator.TARGET_ARM_MAPPING["write-heavy"]
        by_pair = {}
        for row in source:
            by_pair.setdefault(row["pair_index"], {})[row["arm"]] = row["tps"]
        differences = [
            by_pair[index][mapping["variant"]] - by_pair[index][mapping["baseline"]]
            for index in range(60)
        ]
        block_means = [statistics.fmean(differences[start : start + 5]) for start in range(0, 60, 5)]
        expected = (
            math.sqrt(5)
            * generator.chi_square_upper_sd_factor(Fraction(1, 20), 11)
            * statistics.stdev(block_means)
        )
        observed = derived["planning"][0]
        assert math.isclose(float(observed["sigma_block_tps"]), expected, rel_tol=1e-15)
        policy = generator._sigma_policy()
        assert policy["alpha_c"] == {"denominator": 20, "numerator": 1}
        assert policy["block"] == {
            "chi_square_coefficient_applied": True,
            "d1296_explicitly_specified_block_coefficient": False,
            "df": 11,
            "formula": "sqrt(5) * c(one-sided, alpha_c, df=11) * sd(12 five-pair block means)",
            "reason": "conservative-choice-because-coefficient-increases-sigma-and-repetitions",
        }


def test_m7_candidate_grid_is_only_realizable_multiples_of_ten_with_order_indexes():
    assert generator.candidate_grid(28, 59) == (30, 40, 50)
    assert verifier.grid(28, 59) == (30, 40, 50)

    def never_pass(**kwargs):
        trials = kwargs["trials"]
        return {
            "condition": kwargs["condition"],
            "invalid": 0,
            "outcomes": {
                "bounded-within-floor": 0,
                "invalid": 0,
                "resolved-beyond-floor": {"improvement": 0, "regression": 0},
                "unresolved": trials,
            },
            "seed": generator.child_seed(
                kwargs["config"].root_seed,
                kwargs["phase"],
                kwargs["workload"],
                kwargs["condition"],
                kwargs["n"],
                trials,
                kwargs.get("certification_attempt"),
            ),
            "success": 0,
            "trials": trials,
        }

    result = generator.size_workload(
        workload="balanced",
        planned_sigma_tps="1",
        baseline_mean_tps="1000",
        config=generator.SizingConfig(generator.ROOT_SEED_DIGEST, 2, 2, 28, 59),
        simulate=never_pass,
    )
    assert [(row["order_index"], row["n"]) for row in result["candidates"]] == [
        (0, 30), (1, 40), (2, 50)
    ]


def test_frozen_probabilities_seed_and_numeric_algorithms_have_fixed_controls():
    assert generator.FLOOR == Fraction(3, 100)
    assert generator.FAMILY_ALPHA == Fraction(1, 20)
    assert generator.ARM_FAILURE == Fraction(1, 120)
    assert generator.REQUIRED_PROBABILITY == Fraction(4, 5)
    assert [item[0] for item in generator.CONDITIONS] == [
        "zero", "positive-two-floor", "negative-two-floor"
    ]
    assert hashlib.sha256(generator.ROOT_SEED_PREIMAGE.encode("ascii")).hexdigest() == generator.ROOT_SEED_DIGEST
    assert math.isclose(generator.chi_square_upper_sd_factor(Fraction(1, 20), 59), 1.18049, rel_tol=2e-4)
    assert math.isclose(generator.student_t_quantile(Fraction(39, 40), 29), 2.045229642, rel_tol=1e-9)
    assert math.isclose(verifier._sigma_factor(59), generator.chi_square_upper_sd_factor(Fraction(1, 20), 59), rel_tol=1e-14)


def test_certificate_replay_recomputes_pilot_candidates_counts_bounds_alpha_selection_and_order():
    with tempfile.TemporaryDirectory(prefix="a1-balanced-replay-") as raw_dir:
        directory = Path(raw_dir)
        pilot = _write_pilot(directory)
        document = generator.build_certificate(pilot, _config())
        assert document["replay_claim"] == "source-separated-replay-of-the-same-rules-not-an-independent-oracle"
        assert document["policy"]["candidate_grid"] == {
            "effective_minimum": 30,
            "maximum": 30,
            "registered_minimum": 28,
            "step": 10,
            "values": [30],
        }
        assert all(item["selected"]["n"] == 30 for item in document["workloads"])
        assert all(item["selected"]["order_index"] == 0 for item in document["workloads"])
        certificate = directory / "certificate.json"
        certificate.write_bytes(generator.canonical_json_bytes(document))
        expected_digest = hashlib.sha256(certificate.read_bytes()).hexdigest()
        assert verifier.verify_certificate(certificate, pilot, _verify_config()) == expected_digest

        tamper_paths = []
        changed = copy.deepcopy(document)
        changed["workloads"][0]["candidates"][0]["order_index"] = 1
        tamper_paths.append(changed)
        changed = copy.deepcopy(document)
        changed["workloads"][0]["candidates"][0]["search"]["conditions"][0]["trials"] += 1
        tamper_paths.append(changed)
        changed = copy.deepcopy(document)
        changed["workloads"][0]["candidates"][0]["search"]["conditions"][0]["seed"]["digest"] = "0" * 64
        tamper_paths.append(changed)
        changed = copy.deepcopy(document)
        changed["workloads"][0]["candidates"][0]["certification"]["conditions"][0]["lower_bound"] = "0.8"
        tamper_paths.append(changed)
        changed = copy.deepcopy(document)
        changed["workloads"][0]["candidates"][0]["certification"]["condition_alpha"] = {"numerator": 1, "denominator": 121}
        tamper_paths.append(changed)
        changed = copy.deepcopy(document)
        changed["workloads"][0]["selected"]["n"] = 40
        tamper_paths.append(changed)
        for index, changed in enumerate(tamper_paths):
            path = directory / f"tampered-{index}.json"
            path.write_bytes(generator.canonical_json_bytes(changed))
            error = _assert_raises(
                verifier.VerificationError,
                verifier.verify_certificate,
                path,
                pilot,
                _verify_config(),
            )
            assert "source-separated replay" in str(error)


def test_replay_receipt_binds_sources_runtime_pilot_and_certificate_without_oracle_claim():
    with tempfile.TemporaryDirectory(prefix="a1-balanced-receipt-") as raw_dir:
        directory = Path(raw_dir)
        pilot = _write_pilot(directory)
        certificate = directory / "certificate.json"
        certificate.write_bytes(
            generator.canonical_json_bytes(generator.build_certificate(pilot, _config()))
        )
        receipt = directory / "receipt.json"
        args = [
            "--certificate", str(certificate),
            "--pilot", str(pilot),
            "--receipt", str(receipt),
            "--root-seed", generator.ROOT_SEED_DIGEST,
            "--search-trials", "32",
            "--certification-trials", "128",
            "--n-min", "28",
            "--n-max", "30",
        ]
        assert verifier.main(args) == 0
        observed = json.loads(receipt.read_bytes())
        assert receipt.read_bytes() == verifier.canonical_bytes(observed)
        assert observed["replay_claim"] == "source-separated-replay-of-the-same-rules-not-an-independent-oracle"
        assert observed["sources"]["generator"]["sha256"] == hashlib.sha256(
            (ROOT / "tools/size_paper_story_a1_balanced.py").read_bytes()
        ).hexdigest()
        assert observed["sources"]["verifier"]["sha256"] == hashlib.sha256(
            (ROOT / "tools/verify_paper_story_a1_balanced_sizing.py").read_bytes()
        ).hexdigest()
        assert observed["runtime"] == verifier.runtime_contract()
        assert observed["pilot"]["sha256"] == hashlib.sha256(pilot.read_bytes()).hexdigest()
        assert verifier.verify_replay_receipt(
            receipt, certificate, pilot, _verify_config()
        ) == hashlib.sha256(receipt.read_bytes()).hexdigest()


def test_canonical_json_and_exclusive_output_reject_tamper_without_overwrite():
    with tempfile.TemporaryDirectory(prefix="a1-balanced-canonical-") as raw_dir:
        directory = Path(raw_dir)
        pilot = _write_pilot(directory)
        document = generator.build_certificate(pilot, _config())
        raw = generator.canonical_json_bytes(document)
        assert raw.endswith(b"\n") and b"NaN" not in raw and b"Infinity" not in raw
        certificate = directory / "certificate.json"
        generator.write_new_file(certificate, raw)
        error = _assert_raises(generator.SizingError, generator.write_new_file, certificate, raw)
        assert "exclusively create" in str(error)
        noncanonical = directory / "noncanonical.json"
        noncanonical.write_bytes(json.dumps(document, indent=2).encode("utf-8"))
        error = _assert_raises(verifier.VerificationError, verifier.load_certificate, noncanonical)
        assert "canonical JSON" in str(error)


def test_generator_and_verifier_are_source_separated_and_name_algorithms():
    generator_source = (ROOT / "tools/size_paper_story_a1_balanced.py").read_text(encoding="utf-8")
    verifier_source = (ROOT / "tools/verify_paper_story_a1_balanced_sizing.py").read_text(encoding="utf-8")
    assert "verify_paper_story_a1_balanced_sizing" not in generator_source
    assert "import size_paper_story_a1_balanced" not in verifier_source
    assert "from tools import size_paper_story_a1_balanced" not in verifier_source
    assert "not-an-independent-oracle" in generator_source
    assert "not-an-independent-oracle" in verifier_source
    for name in (
        "numpy-pcg64-normal-chisquare-sufficient-statistics/v1",
        "regularized-beta-bisection/v1",
        "regularized-gamma-bisection/v1",
    ):
        assert name in generator_source and name in verifier_source
    ast.parse(generator_source)
    ast.parse(verifier_source)


EXPECTED_SELF_TEST_NAMES = frozenset(
    {
        "test_pilot_exact_shape_accepts_positive_and_rejects_uncoerced_or_unbalanced_rows",
        "test_m6_sigma_certificate_binds_block_chi_square_coefficient_and_conservative_reason",
        "test_m7_candidate_grid_is_only_realizable_multiples_of_ten_with_order_indexes",
        "test_frozen_probabilities_seed_and_numeric_algorithms_have_fixed_controls",
        "test_certificate_replay_recomputes_pilot_candidates_counts_bounds_alpha_selection_and_order",
        "test_replay_receipt_binds_sources_runtime_pilot_and_certificate_without_oracle_claim",
        "test_canonical_json_and_exclusive_output_reject_tamper_without_overwrite",
        "test_generator_and_verifier_are_source_separated_and_name_algorithms",
        "test_self_run_harness_has_exact_test_set",
    }
)


def _validate_self_tests(tests) -> None:
    names = [getattr(test, "__name__", None) for test in tests]
    if any(type(name) is not str for name in names) or len(names) != len(set(names)):
        raise ValueError("self-run test names are invalid")
    if set(names) != EXPECTED_SELF_TEST_NAMES:
        raise ValueError("self-run exact test set differs")


def test_self_run_harness_has_exact_test_set():
    exact = [globals()[name] for name in sorted(EXPECTED_SELF_TEST_NAMES)]
    _validate_self_tests(exact)
    for invalid in ([], exact[:-1], exact + [exact[0]]):
        assert _run(invalid) == 1


def _run(tests=None) -> int:
    if tests is None:
        tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    else:
        tests = list(tests)
    try:
        _validate_self_tests(tests)
    except ValueError as exc:
        print(f"FAIL self-test selection: {exc}")
        return 1
    failures = 0
    for test in tests:
        try:
            test()
        except BaseException as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {test.__name__}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run())
