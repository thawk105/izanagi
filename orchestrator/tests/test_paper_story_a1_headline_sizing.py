# -*- coding: utf-8 -*-
"""A-1 headline sizing generator and source-separated replay contract tests.

The module has a closed self-run harness.  Its tests intentionally avoid
pytest-only fixtures so the same exact set can run under pytest and as a plain
Python program.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist
from types import SimpleNamespace

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import size_paper_story_a1_headline as generator  # noqa: E402
from tools import verify_paper_story_a1_headline_sizing as verifier  # noqa: E402


PILOT = ROOT / generator.PILOT_RELATIVE_PATH
ROOT_SEED = generator.ROOT_SEED_DIGEST


def _config() -> generator.SizingConfig:
    return generator.SizingConfig(
        root_seed=ROOT_SEED,
        search_trials=16,
        certification_trials=32,
        n_min=1000,
        n_max=1000,
    )


def _verification_config() -> verifier.VerificationConfig:
    return verifier.VerificationConfig(
        root_seed=ROOT_SEED,
        search_trials=16,
        certification_trials=32,
        n_min=1000,
        n_max=1000,
    )


@lru_cache(maxsize=1)
def _small_certificate_cached() -> dict[str, object]:
    return generator.build_certificate(PILOT, _config())


def _small_certificate() -> dict[str, object]:
    return copy.deepcopy(_small_certificate_cached())


def _assert_raises(exception_type, function, *args, **kwargs) -> BaseException:
    try:
        function(*args, **kwargs)
    except exception_type as exc:
        return exc
    except BaseException as exc:
        raise AssertionError(
            f"raised {type(exc).__name__}, expected {exception_type.__name__}"
        ) from exc
    raise AssertionError(f"did not raise {exception_type.__name__}")


def _write_certificate(directory: Path, document: dict[str, object], name: str) -> Path:
    path = directory / name
    generator.write_new_file(path, generator.canonical_json_bytes(document))
    return path


def _verifier_arguments(certificate: Path, receipt: Path) -> list[str]:
    return [
        "--certificate",
        str(certificate),
        "--pilot",
        str(PILOT),
        "--receipt",
        str(receipt),
        "--root-seed",
        ROOT_SEED,
        "--search-trials",
        "16",
        "--certification-trials",
        "32",
        "--n-min",
        "1000",
        "--n-max",
        "1000",
    ]


def test_pilot_arm_cv_rederivation_binds_ddof_max_inflation_and_proxy():
    pilot = generator.derive_pilot(PILOT, require_canonical=True)
    assert pilot["path"] == generator.PILOT_RELATIVE_PATH.as_posix()
    assert pilot["sha256"] == generator.PILOT_SHA256
    assert pilot["ddof"] == 1
    assert pilot["proxy"] == {
        "conditional_on_transferred_two-arm_variability": True,
        "target_arms_measured": False,
        "upper_bound_guarantee": False,
    }
    observed = {
        row["workload"]: {
            "arms": {item["arm"]: item["cv"] for item in row["arm_cvs"]},
            "inflation": row["inflation"],
            "max_arm": row["max_arm"],
            "max_cv": row["max_cv"],
            "planned_cv": row["planned_cv"],
        }
        for row in pilot["planning"]
    }
    assert observed == {
        "write-heavy": {
            "arms": generator.PILOT_ARM_CVS["write-heavy"],
            "inflation": "2.372356",
            "max_arm": "static10",
            "max_cv": "0.02074902601444439",
            "planned_cv": "0.049224076359523236",
        },
        "balanced": {
            "arms": generator.PILOT_ARM_CVS["balanced"],
            "inflation": "2.372356",
            "max_arm": "adaptive",
            "max_cv": "0.033436696688397764",
            "planned_cv": "0.07932374800890056",
        },
        "read-heavy": {
            "arms": generator.PILOT_ARM_CVS["read-heavy"],
            "inflation": "2.372356",
            "max_arm": "adaptive",
            "max_cv": "0.006150361983522758",
            "planned_cv": "0.014590848153782116",
        },
    }


def test_pilot_readers_use_one_nofollow_descriptor_for_fstat_and_read():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-fd-") as raw_dir:
        path = Path(raw_dir) / "pilot.json"
        path.write_bytes(b'{"bound":true}\n')
        symlink = Path(raw_dir) / "pilot-link.json"
        symlink.symlink_to(path)
        for module, reader, error_type in (
            (generator, generator._regular_file_bytes, generator.SizingError),
            (verifier, verifier._read_regular, verifier.VerificationError),
        ):
            real_open = module.os.open
            real_fstat = module.os.fstat
            real_read = module.os.read
            opened: list[tuple[int, int]] = []
            fstat_descriptors: list[int] = []
            read_descriptors: list[int] = []

            def tracked_open(open_path, flags, *args):
                descriptor = real_open(open_path, flags, *args)
                opened.append((descriptor, flags))
                return descriptor

            def tracked_fstat(descriptor):
                fstat_descriptors.append(descriptor)
                return real_fstat(descriptor)

            def tracked_read(descriptor, count):
                read_descriptors.append(descriptor)
                return real_read(descriptor, count)

            module.os.open = tracked_open
            module.os.fstat = tracked_fstat
            module.os.read = tracked_read
            try:
                observed = reader(path, "pilot fixture")
            finally:
                module.os.open = real_open
                module.os.fstat = real_fstat
                module.os.read = real_read

            assert observed == b'{"bound":true}\n'
            assert len(opened) == 1
            descriptor, flags = opened[0]
            assert flags & module.os.O_NOFOLLOW
            assert fstat_descriptors == [descriptor]
            assert read_descriptors and set(read_descriptors) == {descriptor}
            _assert_raises(error_type, reader, symlink, "pilot fixture")

        real_component = Path(raw_dir) / "real-component"
        real_component.mkdir()
        component_link = Path(raw_dir) / "component-link"
        component_link.symlink_to(real_component, target_is_directory=True)
        for checker, error_type in (
            (generator._reject_symlink_components, generator.SizingError),
            (verifier._reject_symlink_components, verifier.VerificationError),
        ):
            _assert_raises(
                error_type,
                checker,
                component_link / "pilot.json",
                "pilot fixture",
            )


def test_canonical_pilot_parent_swap_cannot_cross_dirfd_boundary():
    pilot_raw = PILOT.read_bytes()
    pilot_digest = hashlib.sha256(pilot_raw).hexdigest()
    relative = Path("bound-parent/pilot.json")
    for module, read_pilot in (
        (
            generator,
            lambda path: generator.derive_pilot(path, require_canonical=True),
        ),
        (verifier, verifier.rederive_pilot),
    ):
        with tempfile.TemporaryDirectory(
            prefix="a1-headline-sizing-parent-swap-"
        ) as raw_dir:
            repository = Path(raw_dir) / "repo"
            original_parent = repository / relative.parent
            attacker = repository / "attacker"
            original_parent.mkdir(parents=True)
            attacker.mkdir()
            pilot_path = repository / relative
            pilot_path.write_bytes(pilot_raw)
            (attacker / relative.name).write_bytes(b'{"attacker":true}\n')

            original_root = module.REPO_ROOT
            original_relative = module.PILOT_RELATIVE_PATH
            original_digest = module.PILOT_SHA256
            real_open = module.os.open
            opened: list[tuple[object, int, int | None]] = []
            swapped = False

            def swapping_open(open_path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if dir_fd is None:
                    descriptor = real_open(open_path, flags, mode)
                else:
                    descriptor = real_open(
                        open_path,
                        flags,
                        mode,
                        dir_fd=dir_fd,
                    )
                opened.append((open_path, flags, dir_fd))
                if (
                    open_path == relative.parts[0]
                    and dir_fd is not None
                    and flags & module.os.O_DIRECTORY
                    and not swapped
                ):
                    held_parent = repository / "held-parent"
                    original_parent.rename(held_parent)
                    original_parent.symlink_to(attacker, target_is_directory=True)
                    swapped = True
                return descriptor

            module.REPO_ROOT = repository
            module.PILOT_RELATIVE_PATH = relative
            module.PILOT_SHA256 = pilot_digest
            module.os.open = swapping_open
            try:
                observed = read_pilot(pilot_path)
            finally:
                module.os.open = real_open
                module.REPO_ROOT = original_root
                module.PILOT_RELATIVE_PATH = original_relative
                module.PILOT_SHA256 = original_digest

            assert swapped is True
            assert observed["sha256"] == pilot_digest
            assert observed["path"] == relative.as_posix()
            assert len(opened) == 3
            root_open, parent_open, leaf_open = opened
            assert Path(root_open[0]) == repository
            assert root_open[1] & module.os.O_NOFOLLOW
            assert root_open[1] & module.os.O_DIRECTORY
            assert root_open[2] is None
            assert parent_open[0] == relative.parts[0]
            assert parent_open[1] & module.os.O_NOFOLLOW
            assert parent_open[1] & module.os.O_DIRECTORY
            assert parent_open[2] is not None
            assert leaf_open[0] == relative.name
            assert leaf_open[1] & module.os.O_NOFOLLOW
            assert not leaf_open[1] & module.os.O_DIRECTORY
            assert leaf_open[2] is not None


def test_exact_binomial_order_interval_uses_six_arm_bonferroni_target():
    lower, upper, coverage = generator.median_order_interval(28)
    assert (lower, upper) == (7, 22)
    assert coverage.numerator == 66859275
    assert coverage.denominator == 67108864
    assert coverage >= 1 - generator.Fraction(1, 120)
    next_tail = sum(math.comb(28, value) for value in range(lower + 1))
    next_coverage = generator.Fraction((1 << 28) - 2 * next_tail, 1 << 28)
    assert next_coverage < 1 - generator.Fraction(1, 120)


def test_inverse_normal_cdf_algorithm_has_fixed_golden_values():
    probabilities = np.array([0.001, 0.025, 0.5, 0.975, 0.999])
    values = generator.inverse_normal_cdf(probabilities)
    assert [format(value, ".16g") for value in values] == [
        "-3.090232304709404",
        "-1.959963986120195",
        "0",
        "1.959963986120195",
        "3.090232304709404",
    ]
    assert np.all(np.diff(values) > 0.0)
    _assert_raises(
        generator.SizingError,
        generator.inverse_normal_cdf,
        np.array([0.0, 0.5]),
    )


def test_inverse_normal_matches_stdlib_normaldist_on_fixed_grid():
    probabilities = np.array(
        [1e-6, 0.001, 0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975, 0.999, 1 - 1e-6]
    )
    oracle = np.array([NormalDist().inv_cdf(float(value)) for value in probabilities])
    for implementation in (generator.inverse_normal_cdf, verifier.inverse_normal):
        observed = implementation(probabilities)
        assert np.allclose(observed, oracle, rtol=0.0, atol=6e-9)


def test_root_seed_is_derived_from_frozen_ascii_preimage():
    assert generator.ROOT_SEED_PREIMAGE == (
        "paper-story-a1-headline-sizing-root-seed/v2|20260828|"
        "certification-alpha-spending"
    )
    assert generator.ROOT_SEED_ALGORITHM == "sha256"
    assert generator.ROOT_SEED_ENCODING == "ascii"
    assert generator.ROOT_SEED_DIGEST == (
        "531e720c249e561c768471ffbab1d63885a25a08868128bb5c3212843992bc16"
    )
    assert hashlib.sha256(generator.ROOT_SEED_PREIMAGE.encode("ascii")).hexdigest() == ROOT_SEED
    assert verifier.ROOT_SEED_PREIMAGE == generator.ROOT_SEED_PREIMAGE
    assert verifier.ROOT_SEED_ALGORITHM == generator.ROOT_SEED_ALGORITHM
    assert verifier.ROOT_SEED_ENCODING == generator.ROOT_SEED_ENCODING
    assert verifier.ROOT_SEED_DIGEST == ROOT_SEED
    invalid = generator.SizingConfig("0" * 64, 16, 32, 28, 28)
    error = _assert_raises(generator.SizingError, invalid.validate)
    assert "registered SHA-256 digest" in str(error)
    replay_invalid = verifier.VerificationConfig("0" * 64, 16, 32, 28, 28)
    replay_error = _assert_raises(
        verifier.VerificationError, replay_invalid.validate
    )
    assert str(replay_error) == "root seed differs from the registered digest"


def test_seed_grammar_is_golden_and_search_certification_are_domain_separated():
    search = generator.child_seed(
        ROOT_SEED, "search", "balanced", "zero", 28, 7
    )
    assert search == {
        "digest": "87f5c7e9b095752f22d45c29aea67ab75358710b12c040f767f503c02e885a56",
        "preimage": (
            "paper-story-a1-headline-sizing-seed/v2|"
            f"root={ROOT_SEED}|phase=search|workload=balanced|"
            "condition=zero|n=28|trials=7"
        ),
    }
    certification = generator.child_seed(
        ROOT_SEED, "certification", "balanced", "zero", 28, 7, 1
    )
    assert certification == {
        "digest": "d448021c919e09761ffb7186f3c120b96370fab4931cb621104c97a20ca991ed",
        "preimage": (
            "paper-story-a1-headline-sizing-seed/v2|"
            f"root={ROOT_SEED}|phase=certification|workload=balanced|"
            "condition=zero|n=28|trials=7|attempt=1"
        ),
    }
    assert certification["preimage"] != search["preimage"]
    assert certification["digest"] != search["digest"]
    replay_config = verifier.VerificationConfig(ROOT_SEED, 16, 32, 28, 28)
    assert verifier.seed_record(
        replay_config, "search", "balanced", "zero", 28, 7
    ) == search
    assert verifier.seed_record(
        replay_config, "certification", "balanced", "zero", 28, 7, 1
    ) == certification
    _assert_raises(
        generator.SizingError,
        generator.child_seed,
        "0" * 64,
        "search",
        "balanced",
        "zero",
        28,
        7,
    )
    _assert_raises(
        generator.SizingError,
        generator.child_seed,
        ROOT_SEED,
        "certification",
        "balanced",
        "zero",
        28,
        7,
    )


def test_model_requires_zero_positive_and_negative_two_floor_conditions():
    document = _small_certificate()
    assert document["model"]["pilot_source_arms"] == ["adaptive", "static10"]
    assert document["model"]["simulated_arm_roles"] == {
        "baseline": "target-baseline",
        "variant": "target-variant",
    }
    assert document["model"]["estimand"] == (
        "median-variant-over-median-baseline-minus-1"
    )
    assert document["model"]["even_n_sample_median"] == (
        "arithmetic-mean-of-order-n-over-2-and-n-over-2-plus-1"
    )
    conditions = document["model"]["conditions"]
    assert [item["name"] for item in conditions] == [
        "zero",
        "positive-two-floor",
        "negative-two-floor",
    ]
    assert conditions[-1] == {
        "delta": {"denominator": 50, "numerator": -3},
        "name": "negative-two-floor",
        "success": {
            "classification": "resolved-beyond-floor",
            "direction": "regression",
        },
        "variant_population_median": {"denominator": 50, "numerator": 47},
    }
    for workload in document["workloads"]:
        row = workload["candidates"][0]
        assert [item["condition"] for item in row["search"]["conditions"]] == [
            "zero",
            "positive-two-floor",
            "negative-two-floor",
        ]


def test_invalid_interval_is_failure_with_fixed_trial_denominator():
    result = generator.count_outcomes(
        np.array([1.0, 0.0, 1.0, math.nan]),
        np.array([1.0, 0.0, 1.0, math.nan]),
        np.ones(4),
        np.array([1.0, 1.0, -1.0, 1.0]),
        np.array([1.0, 1.0, -1.0, 1.0]),
        np.ones(4),
        "bounded-within-floor",
        None,
    )
    assert result["invalid"] == 3
    assert result["success"] == 1
    outcomes = result["outcomes"]
    resolved = outcomes["resolved-beyond-floor"]
    assert (
        outcomes["bounded-within-floor"]
        + outcomes["invalid"]
        + resolved["improvement"]
        + resolved["regression"]
        + outcomes["unresolved"]
    ) == 4
    assert result["success"] / 4 == 0.25

    boundaries = generator.count_outcomes(
        np.ones(4),
        np.ones(4),
        np.ones(4),
        np.array([0.97, 1.03, np.nextafter(1.03, 2.0), np.nextafter(0.97, 0.0)]),
        np.array([0.97, 1.03, np.nextafter(1.03, 2.0), np.nextafter(0.97, 0.0)]),
        np.array([0.97, 1.03, np.nextafter(1.03, 2.0), np.nextafter(0.97, 0.0)]),
        "bounded-within-floor",
        None,
    )
    assert boundaries["outcomes"] == {
        "bounded-within-floor": 2,
        "invalid": 0,
        "resolved-beyond-floor": {"improvement": 1, "regression": 1},
        "unresolved": 0,
    }


def test_joint_sampler_rejects_hidden_nonpositive_observation_as_single_reason():
    class FixedBetaRng:
        def __init__(self):
            self._values = iter(
                (
                    np.array([0.001, 0.5]),
                    np.array([0.6, 0.2]),
                    np.array([0.01, 0.01]),
                )
            )

        def beta(self, _a, _b, *, size):
            result = next(self._values).copy()
            assert len(result) == size
            return result

    generated = generator._joint_normal_minimum_and_interval(
        FixedBetaRng(),
        n=28,
        lower_index=7,
        trials=2,
        median=1.0,
        cv=0.5,
    )
    replayed = verifier.joint_minimum_and_interval(
        FixedBetaRng(), 28, 7, 2, 1.0, 0.5
    )
    for minimum, lower, upper in (generated, replayed):
        assert minimum[0] <= 0.0
        assert np.all(np.isfinite(lower)) and np.all(lower > 0.0)
        assert np.all(np.isfinite(upper)) and np.all(upper >= lower)
    generated_counts = generator.count_outcomes(
        *generated,
        np.ones(2),
        generated[1].copy(),
        generated[2].copy(),
        "bounded-within-floor",
        None,
    )
    replayed_counts = verifier.replay_count(
        replayed,
        (np.ones(2), replayed[1].copy(), replayed[2].copy()),
        "bounded-within-floor",
        None,
    )
    assert generated_counts["invalid"] == replayed_counts["invalid"] == 1
    assert generated_counts["success"] == replayed_counts["success"] == 1


def test_one_sided_exact_clopper_pearson_lower_bound_is_not_observed_rate():
    alpha = generator.Fraction(1, 60)
    assert generator.clopper_pearson_lower(0, 10, alpha) == 0.0
    all_success = generator.clopper_pearson_lower(10, 10, alpha)
    assert math.isclose(all_success, (1 / 60) ** (1 / 10), rel_tol=0.0, abs_tol=2e-15)
    assert generator.clopper_pearson_lower(80, 100, alpha) < 0.8
    assert generator.clopper_pearson_lower(90, 100, alpha) > 0.8
    assert [generator.certification_condition_alpha(attempt) for attempt in range(1, 4)] == [
        generator.Fraction(1, 120),
        generator.Fraction(1, 360),
        generator.Fraction(1, 720),
    ]
    maximum_attempts = 4096 - 28 + 1
    maximum_summary = generator._alpha_spending_summary(maximum_attempts)
    maximum_spent = generator.Fraction(
        maximum_summary["spent"]["numerator"],
        maximum_summary["spent"]["denominator"],
    )
    assert maximum_spent == generator.Fraction(
        maximum_attempts, 20 * (maximum_attempts + 1)
    )
    assert maximum_spent < generator.FAMILY_ALPHA


def test_clopper_pearson_matches_stdlib_binomial_tail_oracle_on_fixed_grid():
    alpha = generator.Fraction(1, 60)

    def binomial_tail(probability: float, success: int, trials: int) -> float:
        return math.fsum(
            math.comb(trials, count)
            * probability**count
            * (1.0 - probability) ** (trials - count)
            for count in range(success, trials + 1)
        )

    def oracle(success: int, trials: int) -> float:
        if success == 0:
            return 0.0
        low, high = 0.0, 1.0
        for _ in range(100):
            middle = (low + high) / 2.0
            if binomial_tail(middle, success, trials) < float(alpha):
                low = middle
            else:
                high = middle
        return (low + high) / 2.0

    for success, trials in ((1, 10), (5, 10), (8, 10), (80, 100), (90, 100)):
        expected = oracle(success, trials)
        generated = generator.clopper_pearson_lower(success, trials, alpha)
        replayed = verifier.exact_lower(success, trials, alpha)
        assert math.isclose(generated, expected, rel_tol=0.0, abs_tol=1e-12)
        assert math.isclose(replayed, expected, rel_tol=0.0, abs_tol=1e-12)


def test_first_search_pass_is_certified_once_and_failure_stops_without_retry():
    fixture_generation = "v1"
    assert fixture_generation != generator.STUDY_GENERATION.rsplit("-", 1)[-1]
    config = generator.SizingConfig(ROOT_SEED, 16, 32, 28, 30)
    v1_root_seed = "1e36e892d1d7ec8f611752b848bb4ac66962cbec8e25f62fd223ed4daad8089e"

    def fake_simulation(**kwargs):
        trials = kwargs["trials"]
        n = kwargs["n"]
        phase = kwargs["phase"]
        condition = kwargs["condition"]
        success = 28 if phase == "certification" and condition == "zero" else trials
        outcomes = {
            "bounded-within-floor": 0,
            "invalid": 0,
            "resolved-beyond-floor": {"improvement": 0, "regression": 0},
            "unresolved": trials - success,
        }
        if kwargs["success_classification"] == "bounded-within-floor":
            outcomes["bounded-within-floor"] = success
        else:
            outcomes["resolved-beyond-floor"][kwargs["success_direction"]] = success
        preimage = (
            f"paper-story-a1-headline-sizing-seed/v1|root={v1_root_seed}|"
            f"phase={phase}|workload={kwargs['workload']}|condition={condition}|"
            f"n={n}|trials={trials}"
        )
        return {
            "condition": condition,
            "invalid": 0,
            "outcomes": outcomes,
            "seed": {
                "digest": hashlib.sha256(preimage.encode("ascii")).hexdigest(),
                "preimage": preimage,
            },
            "success": success,
            "trials": trials,
        }

    def run_v1_fixture(lower_bound):
        rows = []
        selected = None
        for n in range(config.n_min, config.n_max + 1):
            lower, upper, coverage = generator.median_order_interval(n)
            search = [
                fake_simulation(
                    phase="search",
                    workload="balanced",
                    condition=name,
                    delta=delta,
                    success_classification=classification,
                    success_direction=direction,
                    n=n,
                    trials=config.search_trials,
                    planned_cv=generator.PLANNED_CVS["balanced"],
                    lower_index=lower,
                )
                for name, delta, classification, direction in generator.CONDITIONS
            ]
            search_passes = all(
                int(item["success"]) * 5 >= config.search_trials * 4
                for item in search
            )
            certification = None
            if search_passes:
                conditions = []
                for name, delta, classification, direction in generator.CONDITIONS:
                    item = fake_simulation(
                        phase="certification",
                        workload="balanced",
                        condition=name,
                        delta=delta,
                        success_classification=classification,
                        success_direction=direction,
                        n=n,
                        trials=config.certification_trials,
                        planned_cv=generator.PLANNED_CVS["balanced"],
                        lower_index=lower,
                    )
                    bound = lower_bound(
                        int(item["success"]),
                        config.certification_trials,
                        generator.Fraction(1, 60),
                    )
                    item["passes"] = bound >= 0.8
                    conditions.append(item)
                certification = {
                    "conditions": conditions,
                    "passes": all(item["passes"] for item in conditions),
                }
            rows.append(
                {
                    "certification": certification,
                    "n": n,
                    "order_interval": {
                        "coverage": generator._fraction(coverage),
                        "lower_index_1based": lower,
                        "upper_index_1based": upper,
                    },
                    "search": {"conditions": search, "passes": search_passes},
                }
            )
            if certification is not None:
                if certification["passes"]:
                    selected = {"n": n}
                break
        return {
            "candidates": rows,
            "selected": selected,
            "status": "selected" if selected is not None else "no-passing-n",
        }

    result = run_v1_fixture(generator.clopper_pearson_lower)
    assert [row["n"] for row in result["candidates"]] == [28]
    assert result["candidates"][0]["search"]["passes"] is True
    assert result["candidates"][0]["certification"]["passes"] is False
    assert [
        item["passes"]
        for item in result["candidates"][0]["certification"]["conditions"]
    ] == [False, True, True]
    assert result["selected"] is None
    assert result["status"] == "no-passing-n"

    replay_result = run_v1_fixture(verifier.exact_lower)
    assert replay_result == result
    assert [row["n"] for row in replay_result["candidates"]] == [28]
    assert replay_result["candidates"][0]["certification"]["passes"] is False
    assert replay_result["selected"] is None
    assert replay_result["status"] == "no-passing-n"
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-v1-inert-") as raw_dir:
        v1_certificate = Path(raw_dir) / "failed-v1.json"
        v1_certificate.write_bytes(
            verifier.canonical_bytes(
                {"schema_version": "paper-story-a1-headline-sizing-certificate/v1"}
            )
        )
        error = _assert_raises(
            verifier.VerificationError, verifier.load_certificate, v1_certificate
        )
        assert str(error) == "certificate schema differs"


def test_v2_attempt_one_failure_then_attempt_two_passes_with_exact_family_spending():
    assert generator.STUDY_GENERATION == (
        "paper-story-a1-headline-estimand-20260828-v2"
    )
    config = generator.SizingConfig(ROOT_SEED, 16, 32, 28, 30)

    def fake_simulation(**kwargs):
        trials = kwargs["trials"]
        n = kwargs["n"]
        phase = kwargs["phase"]
        condition = kwargs["condition"]
        if phase == "search":
            success = 0 if (n == 29 and condition == "zero") else trials
        else:
            success = 28 if (n == 28 and condition == "zero") else trials
        outcomes = {
            "bounded-within-floor": 0,
            "invalid": 0,
            "resolved-beyond-floor": {"improvement": 0, "regression": 0},
            "unresolved": trials - success,
        }
        if kwargs["success_classification"] == "bounded-within-floor":
            outcomes["bounded-within-floor"] = success
        else:
            outcomes["resolved-beyond-floor"][kwargs["success_direction"]] = success
        return {
            "condition": condition,
            "invalid": 0,
            "outcomes": outcomes,
            "seed": generator.child_seed(
                config.root_seed,
                phase,
                kwargs["workload"],
                condition,
                n,
                trials,
                kwargs.get("certification_attempt"),
            ),
            "success": success,
            "trials": trials,
        }

    result = generator.size_workload(
        workload="balanced",
        planned_cv=generator.PLANNED_CVS["balanced"],
        config=config,
        simulate=fake_simulation,
    )
    assert [row["n"] for row in result["candidates"]] == [28, 29, 30]
    first, skipped, second = result["candidates"]
    assert first["search"]["passes"] is True
    assert first["certification"]["attempt"] == 1
    assert first["certification"]["passes"] is False
    assert [item["passes"] for item in first["certification"]["conditions"]] == [
        False,
        True,
        True,
    ]
    assert skipped["search"]["passes"] is False
    assert skipped["certification"] is None
    assert second["certification"]["attempt"] == 2
    assert second["certification"]["passes"] is True
    assert result["selected"]["n"] == 30
    assert result["selected"]["certification_attempt"] == 2

    expected_alphas = [generator.Fraction(1, 120), generator.Fraction(1, 360)]
    for row, expected_alpha in zip((first, second), expected_alphas):
        certification = row["certification"]
        assert certification["condition_alpha"] == generator._fraction(expected_alpha)
        assert [
            generator.Fraction(item["alpha"]["numerator"], item["alpha"]["denominator"])
            for item in certification["conditions"]
        ] == [expected_alpha] * 3
    exact_spent = 3 * sum(expected_alphas, generator.Fraction(0, 1))
    assert exact_spent == generator.Fraction(1, 30)
    assert exact_spent <= generator.FAMILY_ALPHA
    assert result["certification_alpha_spending"] == {
        "attempt_count": 2,
        "condition_count": 3,
        "family_alpha_cap": {"denominator": 20, "numerator": 1},
        "spent": {"denominator": 30, "numerator": 1},
        "within_cap": True,
    }

    def fake_replay(
        replay_config,
        phase,
        replay_workload,
        condition,
        delta,
        classification,
        direction,
        n,
        trials,
        replay_cv,
        lower_index,
        certification_attempt=None,
    ):
        return fake_simulation(
            config=replay_config,
            phase=phase,
            workload=replay_workload,
            condition=condition,
            delta=delta,
            success_classification=classification,
            success_direction=direction,
            n=n,
            trials=trials,
            planned_cv=replay_cv,
            lower_index=lower_index,
            certification_attempt=certification_attempt,
        )

    replay_result = verifier.recompute_workload(
        "balanced",
        generator.PLANNED_CVS["balanced"],
        verifier.VerificationConfig(ROOT_SEED, 16, 32, 28, 30),
        replay=fake_replay,
    )
    assert [row["n"] for row in replay_result["candidates"]] == [28, 29, 30]
    assert [
        row["certification"]["attempt"]
        for row in replay_result["candidates"]
        if row["certification"] is not None
    ] == [1, 2]
    assert replay_result["selected"]["n"] == 30
    assert replay_result["selected"]["certification_attempt"] == 2
    assert (
        replay_result["certification_alpha_spending"]
        == result["certification_alpha_spending"]
    )


def test_small_certificate_has_contiguous_rows_counts_selection_and_canonical_bytes():
    document = _small_certificate()
    assert document["schema_version"] == "paper-story-a1-headline-sizing-certificate/v2"
    assert document["study_generation"] == generator.STUDY_GENERATION
    assert document["status"] == "selected"
    assert document["policy"]["search"]["trials"] == 16
    assert document["policy"]["certification"]["trials"] == 32
    assert document["policy"]["certification"]["condition_count"] == 3
    assert document["policy"]["certification"]["condition_alpha_at_attempt_j"] == (
        "1/(60*j*(j+1))"
    )
    assert document["policy"]["certification"]["all_attempts_per_condition_alpha"] == {
        "denominator": 60,
        "numerator": 1,
    }
    assert document["policy"]["certification"]["all_attempts_total_alpha"] == {
        "denominator": 20,
        "numerator": 1,
    }
    assert [item["workload"] for item in document["workloads"]] == list(
        generator.WORKLOADS
    )
    for workload in document["workloads"]:
        assert [row["n"] for row in workload["candidates"]] == [1000]
        selected = workload["selected"]
        row = workload["candidates"][0]
        assert selected["n"] == row["n"]
        assert selected["certification_attempt"] == 1
        assert selected["coverage"] == row["order_interval"]["coverage"]
        assert row["certification"]["attempt"] == 1
        assert row["certification"]["condition_alpha"] == {
            "denominator": 120,
            "numerator": 1,
        }
        assert workload["certification_alpha_spending"] == {
            "attempt_count": 1,
            "condition_count": 3,
            "family_alpha_cap": {"denominator": 20, "numerator": 1},
            "spent": {"denominator": 40, "numerator": 1},
            "within_cap": True,
        }
        for phase in (row["search"], row["certification"]):
            for condition in phase["conditions"]:
                assert condition["success"] + condition["invalid"] <= condition["trials"]
                outcomes = condition["outcomes"]
                resolved = outcomes["resolved-beyond-floor"]
                total = (
                    outcomes["bounded-within-floor"]
                    + outcomes["invalid"]
                    + resolved["improvement"]
                    + resolved["regression"]
                    + outcomes["unresolved"]
                )
                assert total == condition["trials"]
                if phase is row["certification"]:
                    assert condition["alpha"] == {
                        "denominator": 120,
                        "numerator": 1,
                    }
    raw = generator.canonical_json_bytes(document)
    assert raw.endswith(b"\n")
    assert b"NaN" not in raw and b"Infinity" not in raw
    assert verifier.canonical_bytes(json.loads(raw)) == raw


def test_certificate_policy_separates_sources_targets_and_binds_selection_rules():
    policy = _small_certificate()["policy"]
    assert policy["root_seed"] == {
        "algorithm": "sha256",
        "digest": ROOT_SEED,
        "encoding": "ascii",
        "preimage": (
            "paper-story-a1-headline-sizing-root-seed/v2|20260828|"
            "certification-alpha-spending"
        ),
    }
    assert policy["pilot_source_arms"] == ["adaptive", "static10"]
    assert policy["floor"] == {"denominator": 100, "numerator": 3}
    assert policy["band"] == {
        "lower": {"denominator": 100, "numerator": 97},
        "upper": {"denominator": 100, "numerator": 103},
    }
    assert policy["classification_operators"]["resolved-beyond-floor"] == {
        "improvement": {
            "endpoint": "ratio-lower",
            "operator": ">",
            "threshold": {"denominator": 100, "numerator": 103},
        },
        "regression": {
            "endpoint": "ratio-upper",
            "operator": "<",
            "threshold": {"denominator": 100, "numerator": 97},
        },
    }
    assert policy["interval_family"]["family_alpha"] == {
        "denominator": 20,
        "numerator": 1,
    }
    assert policy["selected_rule"] == (
        "first-certification-pass-among-ascending-search-passing-candidates"
    )
    assert policy["certification"]["condition_alpha_at_attempt_j"] == (
        "1/(60*j*(j+1))"
    )
    assert policy["certification"]["failure_action"] == (
        "continue-to-next-search-passing-n"
    )
    assert policy["n_range"] == {"maximum": 1000, "minimum": 1000, "step": 1}
    assert policy["target_arm_mapping"] == [
        {"baseline": "no-backoff", "variant": "fixed10", "workload": "write-heavy"},
        {"baseline": "no-backoff", "variant": "fixed5", "workload": "balanced"},
        {"baseline": "no-backoff", "variant": "fixed2", "workload": "read-heavy"},
    ]
    assert [item["name"] for item in policy["conditions"]] == [
        "zero",
        "positive-two-floor",
        "negative-two-floor",
    ]


def test_source_separated_replay_recomputes_positive_certificate():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-positive-") as raw_dir:
        directory = Path(raw_dir)
        certificate = _write_certificate(directory, _small_certificate(), "certificate.json")
        digest = verifier.verify_certificate(
            certificate, PILOT, _verification_config()
        )
        assert digest == hashlib.sha256(certificate.read_bytes()).hexdigest()


def test_replay_receipt_binds_tools_runtime_certificate_and_policy():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-receipt-") as raw_dir:
        directory = Path(raw_dir)
        certificate = _write_certificate(
            directory,
            _small_certificate(),
            "certificate.json",
        )
        receipt = directory / "receipt.json"
        assert verifier.main(_verifier_arguments(certificate, receipt)) == 0
        observed, raw = verifier.load_replay_receipt(receipt)
        assert raw == verifier.canonical_bytes(observed)
        assert observed == verifier.build_replay_receipt(
            certificate,
            hashlib.sha256(certificate.read_bytes()).hexdigest(),
            _verification_config(),
        )
        assert observed["schema_version"] == verifier.RECEIPT_SCHEMA
        assert observed["certificate"] == {
            "path": certificate.as_posix(),
            "sha256": hashlib.sha256(certificate.read_bytes()).hexdigest(),
        }
        assert observed["pilot"] == {
            "path": generator.PILOT_RELATIVE_PATH.as_posix(),
            "sha256": generator.PILOT_SHA256,
        }
        assert observed["sources"] == {
            "generator": {
                "path": "tools/size_paper_story_a1_headline.py",
                "sha256": hashlib.sha256(
                    Path(generator.__file__).read_bytes()
                ).hexdigest(),
            },
            "verifier": {
                "path": "tools/verify_paper_story_a1_headline_sizing.py",
                "sha256": hashlib.sha256(
                    Path(verifier.__file__).read_bytes()
                ).hexdigest(),
            },
        }
        assert observed["runtime"] == verifier.runtime_contract()
        assert observed["policy"] == {
            "certification_trials": 32,
            "n_range": {"maximum": 1000, "minimum": 1000, "step": 1},
            "root_seed": {
                "algorithm": "sha256",
                "digest": ROOT_SEED,
                "encoding": "ascii",
                "preimage": generator.ROOT_SEED_PREIMAGE,
            },
            "search_trials": 16,
        }
        assert observed["verification"] == {
            "return_code": 0,
            "status": "verified",
        }
        assert "timestamp" not in raw.decode("utf-8")
        assert '"cwd"' not in raw.decode("utf-8")
        assert verifier.verify_replay_receipt(
            receipt,
            certificate,
            PILOT,
            _verification_config(),
        ) == hashlib.sha256(raw).hexdigest()


def test_replay_receipt_rejects_tamper_runtime_and_certificate_drift():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-receipt-red-") as raw_dir:
        directory = Path(raw_dir)
        certificate = _write_certificate(
            directory,
            _small_certificate(),
            "certificate.json",
        )
        certificate_digest = verifier.verify_certificate(
            certificate,
            PILOT,
            _verification_config(),
        )
        receipt_document = verifier.build_replay_receipt(
            certificate,
            certificate_digest,
            _verification_config(),
        )
        receipt = directory / "receipt.json"
        verifier.write_new_receipt(
            receipt,
            verifier.canonical_bytes(receipt_document),
        )

        tampered_document = copy.deepcopy(receipt_document)
        tampered_document["verification"]["status"] = "unverified"
        tampered = directory / "tampered-receipt.json"
        verifier.write_new_receipt(
            tampered,
            verifier.canonical_bytes(tampered_document),
        )
        tamper_error = _assert_raises(
            verifier.VerificationError,
            verifier.verify_replay_receipt,
            tampered,
            certificate,
            PILOT,
            _verification_config(),
        )
        assert "replay receipt binding differs" in str(tamper_error)

        original_python_version = verifier.platform.python_version
        try:
            verifier.platform.python_version = lambda: "0.0.receipt-runtime-drift"
            runtime_error = _assert_raises(
                verifier.VerificationError,
                verifier.verify_replay_receipt,
                receipt,
                certificate,
                PILOT,
                _verification_config(),
            )
        finally:
            verifier.platform.python_version = original_python_version
        assert "runtime differs" in str(runtime_error)

        changed_certificate = _small_certificate()
        changed_certificate["workloads"][0]["candidates"][0]["n"] = 999
        certificate.write_bytes(generator.canonical_json_bytes(changed_certificate))
        certificate_error = _assert_raises(
            verifier.VerificationError,
            verifier.verify_replay_receipt,
            receipt,
            certificate,
            PILOT,
            _verification_config(),
        )
        assert "certificate does not match" in str(certificate_error)


def test_replay_receipt_detects_tool_source_changes():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-source-drift-") as raw_dir:
        directory = Path(raw_dir)
        certificate = _write_certificate(
            directory,
            _small_certificate(),
            "certificate.json",
        )
        generator_source = directory / "generator.py"
        verifier_source = directory / "verifier.py"
        generator_original = Path(generator.__file__).read_bytes()
        verifier_original = Path(verifier.__file__).read_bytes()
        generator_source.write_bytes(generator_original)
        verifier_source.write_bytes(verifier_original)
        original_generator_path = verifier.GENERATOR_SOURCE_PATH
        original_verifier_path = verifier.VERIFIER_SOURCE_PATH
        verifier.GENERATOR_SOURCE_PATH = generator_source
        verifier.VERIFIER_SOURCE_PATH = verifier_source
        try:
            certificate_digest = verifier.verify_certificate(
                certificate,
                PILOT,
                _verification_config(),
            )
            receipt = directory / "receipt.json"
            verifier.write_new_receipt(
                receipt,
                verifier.canonical_bytes(
                    verifier.build_replay_receipt(
                        certificate,
                        certificate_digest,
                        _verification_config(),
                    )
                ),
            )
            generator_source.write_bytes(generator_original + b"# changed\n")
            generator_error = _assert_raises(
                verifier.VerificationError,
                verifier.verify_replay_receipt,
                receipt,
                certificate,
                PILOT,
                _verification_config(),
            )
            assert "sources.generator.sha256" in str(generator_error)

            generator_source.write_bytes(generator_original)
            verifier_source.write_bytes(verifier_original + b"# changed\n")
            verifier_error = _assert_raises(
                verifier.VerificationError,
                verifier.verify_replay_receipt,
                receipt,
                certificate,
                PILOT,
                _verification_config(),
            )
            assert "sources.verifier.sha256" in str(verifier_error)
        finally:
            verifier.GENERATOR_SOURCE_PATH = original_generator_path
            verifier.VERIFIER_SOURCE_PATH = original_verifier_path


def test_replay_receipt_rejects_noncanonical_json_and_never_overwrites():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-receipt-write-") as raw_dir:
        directory = Path(raw_dir)
        certificate = _write_certificate(
            directory,
            _small_certificate(),
            "certificate.json",
        )
        certificate_digest = verifier.verify_certificate(
            certificate,
            PILOT,
            _verification_config(),
        )
        document = verifier.build_replay_receipt(
            certificate,
            certificate_digest,
            _verification_config(),
        )
        noncanonical = directory / "noncanonical.json"
        noncanonical.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        noncanonical_error = _assert_raises(
            verifier.VerificationError,
            verifier.load_replay_receipt,
            noncanonical,
        )
        assert str(noncanonical_error) == (
            "replay receipt bytes are not canonical JSON"
        )

        existing = directory / "existing-receipt.json"
        existing.write_bytes(b"do not replace\n")
        assert verifier.main(_verifier_arguments(certificate, existing)) == 1
        assert existing.read_bytes() == b"do not replace\n"


def test_runtime_contract_rejects_ambient_python_and_numpy_version_drift():
    document = _small_certificate()
    assert document["runtime"] == generator.runtime_contract()
    assert document["runtime"] == verifier.runtime_contract()
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-runtime-") as raw_dir:
        certificate = _write_certificate(
            Path(raw_dir), document, "certificate.json"
        )
        original_numpy = verifier.np.__version__
        try:
            verifier.np.__version__ = original_numpy + ".simulated-drift"
            numpy_error = _assert_raises(
                verifier.VerificationError,
                verifier.verify_certificate,
                certificate,
                PILOT,
                _verification_config(),
            )
        finally:
            verifier.np.__version__ = original_numpy
        assert str(numpy_error) == (
            "certificate runtime differs from this replay runtime"
        )

        original_python = verifier.platform.python_version
        try:
            verifier.platform.python_version = lambda: "0.0.simulated-drift"
            python_error = _assert_raises(
                verifier.VerificationError,
                verifier.verify_certificate,
                certificate,
                PILOT,
                _verification_config(),
            )
        finally:
            verifier.platform.python_version = original_python
        assert str(python_error) == (
            "certificate runtime differs from this replay runtime"
        )


def test_verifier_rejects_success_seed_selected_order_and_input_tamper():
    mutations = []
    success = _small_certificate()
    success["workloads"][0]["candidates"][0]["search"]["conditions"][0]["success"] -= 1
    mutations.append(success)
    seed = _small_certificate()
    seed["workloads"][1]["candidates"][0]["search"]["conditions"][1]["seed"]["digest"] = "0" * 64
    mutations.append(seed)
    selected = _small_certificate()
    selected["workloads"][2]["selected"]["lower_index_1based"] += 1
    mutations.append(selected)
    pilot_hash = _small_certificate()
    pilot_hash["inputs"]["pilot"]["sha256"] = "f" * 64
    mutations.append(pilot_hash)
    missing_negative = _small_certificate()
    missing_negative["workloads"][0]["candidates"][0]["search"]["conditions"].pop()
    mutations.append(missing_negative)
    attempt = _small_certificate()
    attempt["workloads"][0]["candidates"][0]["certification"]["attempt"] = 2
    mutations.append(attempt)
    condition_alpha = _small_certificate()
    condition_alpha["workloads"][0]["candidates"][0]["certification"]["conditions"][0]["alpha"] = {
        "denominator": 60,
        "numerator": 1,
    }
    mutations.append(condition_alpha)
    alpha_total = _small_certificate()
    alpha_total["workloads"][0]["certification_alpha_spending"]["spent"] = {
        "denominator": 20,
        "numerator": 1,
    }
    mutations.append(alpha_total)
    schedule_total = _small_certificate()
    schedule_total["policy"]["certification"]["all_attempts_total_alpha"] = {
        "denominator": 21,
        "numerator": 1,
    }
    mutations.append(schedule_total)

    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-tamper-") as raw_dir:
        directory = Path(raw_dir)
        for index, mutation in enumerate(mutations):
            certificate = _write_certificate(
                directory, mutation, f"tamper-{index}.json"
            )
            _assert_raises(
                verifier.VerificationError,
                verifier.verify_certificate,
                certificate,
                PILOT,
                _verification_config(),
            )


def test_verifier_rejects_duplicate_nonfinite_and_noncanonical_json_before_simulation():
    documents = (
        b'{"schema_version":"x","schema_version":"y"}\n',
        b'{"schema_version":NaN}\n',
        b'{\n  "schema_version": "paper-story-a1-headline-sizing-certificate/v2"\n}\n',
    )
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-json-") as raw_dir:
        directory = Path(raw_dir)
        for index, raw in enumerate(documents):
            path = directory / f"invalid-{index}.json"
            path.write_bytes(raw)
            _assert_raises(verifier.VerificationError, verifier.load_certificate, path)


def test_generator_never_overwrites_an_existing_output():
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-no-replace-") as raw_dir:
        output = Path(raw_dir) / "certificate.json"
        generator.write_new_file(output, b"first\n")
        _assert_raises(
            generator.SizingError,
            generator.write_new_file,
            output,
            b"second\n",
        )
        assert output.read_bytes() == b"first\n"


def test_cli_has_no_hidden_canonical_defaults_and_verification_red_is_nonzero():
    required_by_parser = (
        (
            generator._parser(),
            {
                "pilot",
                "output",
                "root_seed",
                "search_trials",
                "certification_trials",
                "n_min",
                "n_max",
            },
        ),
        (
            verifier._parser(),
            {
                "certificate",
                "pilot",
                "receipt",
                "root_seed",
                "search_trials",
                "certification_trials",
                "n_min",
                "n_max",
            },
        ),
    )
    for parser, expected in required_by_parser:
        observed = {
            action.dest for action in parser._actions if action.required is True
        }
        assert observed == expected

    mutation = _small_certificate()
    mutation["workloads"][0]["candidates"][0]["n"] = 999
    with tempfile.TemporaryDirectory(prefix="a1-headline-sizing-cli-red-") as raw_dir:
        directory = Path(raw_dir)
        certificate = _write_certificate(directory, mutation, "tampered.json")
        receipt = directory / "must-not-exist.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/verify_paper_story_a1_headline_sizing.py"),
                "--certificate",
                str(certificate),
                "--pilot",
                str(PILOT),
                "--receipt",
                str(receipt),
                "--root-seed",
                ROOT_SEED,
                "--search-trials",
                "16",
                "--certification-trials",
                "32",
                "--n-min",
                "1000",
                "--n-max",
                "1000",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert completed.returncode != 0
        assert "verification failed" in completed.stderr
        assert not receipt.exists()


def test_joint_order_generation_does_not_allocate_trials_by_n_normal_samples():
    source = (ROOT / "tools/size_paper_story_a1_headline.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    beta_calls = []
    forbidden_normal_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "beta":
            beta_calls.append(node)
        if node.func.attr in {"normal", "standard_normal"}:
            forbidden_normal_calls.append(node)
    assert len(beta_calls) == 3
    assert not forbidden_normal_calls
    for call in beta_calls:
        size = next(keyword.value for keyword in call.keywords if keyword.arg == "size")
        assert isinstance(size, ast.Name) and size.id == "trials"
    assert generator.ORDER_ALGORITHM == (
        "joint-uniform-minimum-and-interval-order-statistics-beta-conditional/v2"
    )


def test_verifier_is_source_separated_from_generator_without_independence_claim():
    verifier_source = (
        ROOT / "tools/verify_paper_story_a1_headline_sizing.py"
    ).read_text(encoding="utf-8")
    generator_source = (
        ROOT / "tools/size_paper_story_a1_headline.py"
    ).read_text(encoding="utf-8")
    assert "import size_paper_story_a1_headline" not in verifier_source
    assert "from tools import size_paper_story_a1_headline" not in verifier_source
    assert "verify_paper_story_a1_headline_sizing" not in generator_source
    assert "independent verifier" not in verifier_source.lower()
    assert "independent recomputation" not in verifier_source.lower()
    assert "source-separated replay" in verifier_source.lower()
    assert ast.parse(verifier_source)
    assert ast.parse(generator_source)


EXPECTED_SELF_TEST_NAMES = frozenset(
    {
        "test_pilot_arm_cv_rederivation_binds_ddof_max_inflation_and_proxy",
        "test_pilot_readers_use_one_nofollow_descriptor_for_fstat_and_read",
        "test_canonical_pilot_parent_swap_cannot_cross_dirfd_boundary",
        "test_exact_binomial_order_interval_uses_six_arm_bonferroni_target",
        "test_inverse_normal_cdf_algorithm_has_fixed_golden_values",
        "test_inverse_normal_matches_stdlib_normaldist_on_fixed_grid",
        "test_root_seed_is_derived_from_frozen_ascii_preimage",
        "test_seed_grammar_is_golden_and_search_certification_are_domain_separated",
        "test_model_requires_zero_positive_and_negative_two_floor_conditions",
        "test_invalid_interval_is_failure_with_fixed_trial_denominator",
        "test_joint_sampler_rejects_hidden_nonpositive_observation_as_single_reason",
        "test_one_sided_exact_clopper_pearson_lower_bound_is_not_observed_rate",
        "test_clopper_pearson_matches_stdlib_binomial_tail_oracle_on_fixed_grid",
        "test_first_search_pass_is_certified_once_and_failure_stops_without_retry",
        "test_v2_attempt_one_failure_then_attempt_two_passes_with_exact_family_spending",
        "test_small_certificate_has_contiguous_rows_counts_selection_and_canonical_bytes",
        "test_certificate_policy_separates_sources_targets_and_binds_selection_rules",
        "test_source_separated_replay_recomputes_positive_certificate",
        "test_replay_receipt_binds_tools_runtime_certificate_and_policy",
        "test_replay_receipt_rejects_tamper_runtime_and_certificate_drift",
        "test_replay_receipt_detects_tool_source_changes",
        "test_replay_receipt_rejects_noncanonical_json_and_never_overwrites",
        "test_runtime_contract_rejects_ambient_python_and_numpy_version_drift",
        "test_verifier_rejects_success_seed_selected_order_and_input_tamper",
        "test_verifier_rejects_duplicate_nonfinite_and_noncanonical_json_before_simulation",
        "test_generator_never_overwrites_an_existing_output",
        "test_cli_has_no_hidden_canonical_defaults_and_verification_red_is_nonzero",
        "test_joint_order_generation_does_not_allocate_trials_by_n_normal_samples",
        "test_verifier_is_source_separated_from_generator_without_independence_claim",
        "test_self_run_harness_rejects_invalid_test_sets_before_execution",
    }
)


def _validate_self_test_selection(tests) -> None:
    names = [getattr(test, "__name__", None) for test in tests]
    if any(type(name) is not str for name in names):
        raise ValueError("self-run test has no exact name")
    if len(names) != len(set(names)):
        raise ValueError("self-run test names are duplicated")
    if set(names) != EXPECTED_SELF_TEST_NAMES:
        raise ValueError("self-run exact test set differs")


def test_self_run_harness_rejects_invalid_test_sets_before_execution():
    executed = []

    def named(name):
        def control():
            executed.append(name)

        control.__name__ = name
        return control

    exact = [named(name) for name in sorted(EXPECTED_SELF_TEST_NAMES)]
    _validate_self_test_selection(exact)
    for invalid in ([], exact[:-1], exact + [named("test_extra")], exact + [exact[0]]):
        assert _run(invalid) == 1
        assert not executed


def _run(tests=None) -> int:
    if tests is None:
        tests = [
            value
            for name, value in sorted(globals().items())
            if name.startswith("test_") and callable(value)
        ]
    else:
        tests = list(tests)
    try:
        _validate_self_test_selection(tests)
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
