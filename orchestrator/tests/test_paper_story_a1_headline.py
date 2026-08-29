# -*- coding: utf-8 -*-
"""Pure A-1 headline authority binding, statistics, and negative controls.

Every test is fixture-free so this file also has a closed plain-Python self-run
harness.  The production parser itself performs no I/O; only these tests read
the canonical fixtures before passing their paths and bytes explicitly.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import math
import statistics
import subprocess
import sys
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.campaign import paper_story_a1_headline as headline  # noqa: E402


DOCUMENT = ROOT / headline.CANONICAL_DOCUMENT_PATH
POLICY = ROOT / headline.MIRROR_POLICY_PATH
FAILED_CERTIFICATE = ROOT / headline.FAILED_SIZING_CERTIFICATE_PATH
CERTIFICATE = ROOT / headline.SIZING_CERTIFICATE_PATH
RECEIPT = ROOT / headline.SIZING_REPLAY_RECEIPT_PATH
GENERATOR_SOURCE = ROOT / headline.SIZING_GENERATOR_SOURCE_PATH
VERIFIER_SOURCE = ROOT / headline.SIZING_VERIFIER_SOURCE_PATH
AUTHOR_BASE_COMMIT = "8d014c748286c6fec497d0afa10a395f159861b1"
AUTHOR_TIP_COMMIT = "c6dc4012cf5055f925659366553a2e7301b2aa00"
INTEGRATION_BASE_COMMIT = "61b92342beb259363eb5ed094ac200dd39a7a1f5"
INTEGRATION_TIP_COMMIT = "ff65e61692801b2de3194ede262d9f53ed317f7b"


def _assert_raises(exception_type, function, *args, match: str | None = None, **kwargs):
    try:
        function(*args, **kwargs)
    except exception_type as exc:
        if match is not None and match not in str(exc):
            raise AssertionError(f"exception did not contain {match!r}: {exc}") from exc
        return exc
    except BaseException as exc:
        raise AssertionError(
            f"raised {type(exc).__name__}, expected {exception_type.__name__}"
        ) from exc
    raise AssertionError(f"did not raise {exception_type.__name__}")


def _canonical_indent(value: dict) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_compact(value: dict) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _split_document(document: bytes) -> tuple[bytes, bytes, bytes]:
    start = b"<!-- PAPER_STORY_A1_HEADLINE_SPEC_START -->\n```json\n"
    end = b"```\n<!-- PAPER_STORY_A1_HEADLINE_SPEC_END -->"
    prefix, remainder = document.split(start, 1)
    raw_spec, suffix = remainder.split(end, 1)
    return prefix + start, raw_spec, end + suffix


@lru_cache(maxsize=1)
def _canonical_inputs() -> tuple[bytes, bytes, bytes, bytes, bytes, dict, dict]:
    document = DOCUMENT.read_bytes()
    policy = POLICY.read_bytes()
    failed_certificate = FAILED_CERTIFICATE.read_bytes()
    certificate = CERTIFICATE.read_bytes()
    receipt = RECEIPT.read_bytes()
    _prefix, raw_spec, _suffix = _split_document(document)
    return (
        document, policy, failed_certificate, certificate, receipt,
        json.loads(raw_spec), json.loads(policy),
    )


@lru_cache(maxsize=1)
def _bound() -> headline.BoundSpec:
    (
        document, policy, failed_certificate, certificate, receipt, _spec, _mirror,
    ) = _canonical_inputs()
    return headline.parse_bound_spec(
        headline.CANONICAL_DOCUMENT_PATH,
        document,
        headline.MIRROR_POLICY_PATH,
        policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
    )


def _mirror_bytes(
    document: bytes,
    raw_spec: bytes,
    spec_mirror: dict,
    failed_certificate: bytes,
    certificate: bytes,
    receipt: bytes,
) -> bytes:
    envelope = {
        "canonical_document_path": headline.CANONICAL_DOCUMENT_PATH,
        "canonical_document_sha256": hashlib.sha256(document).hexdigest(),
        "failed_sizing_certificate_path": headline.FAILED_SIZING_CERTIFICATE_PATH,
        "failed_sizing_certificate_sha256": hashlib.sha256(failed_certificate).hexdigest(),
        "mirror_policy_path": headline.MIRROR_POLICY_PATH,
        "raw_embedded_spec_sha256": hashlib.sha256(raw_spec).hexdigest(),
        "sizing_certificate_path": headline.SIZING_CERTIFICATE_PATH,
        "sizing_certificate_sha256": hashlib.sha256(certificate).hexdigest(),
        "sizing_replay_receipt_path": headline.SIZING_REPLAY_RECEIPT_PATH,
        "sizing_replay_receipt_sha256": hashlib.sha256(receipt).hexdigest(),
        "spec_mirror": spec_mirror,
    }
    return _canonical_indent(envelope)


def _bundle(
    spec_mutator=None,
    certificate_mutator=None,
    receipt_mutator=None,
    mirror_from_base=False,
):
    (
        base_document, _base_policy, failed_certificate, base_certificate, base_receipt,
        base_spec, _base_mirror,
    ) = _canonical_inputs()
    spec = copy.deepcopy(base_spec)
    if spec_mutator is not None:
        spec_mutator(spec)
    if certificate_mutator is None:
        certificate = base_certificate
    else:
        certificate_object = json.loads(base_certificate)
        certificate_mutator(certificate_object)
        certificate = _canonical_compact(certificate_object)
    certificate_digest = hashlib.sha256(certificate).hexdigest()
    spec["authority"]["sizing_certificate_sha256"] = certificate_digest
    spec["sizing"]["certificate_sha256"] = certificate_digest
    receipt_object = json.loads(base_receipt)
    receipt_object["certificate"]["sha256"] = certificate_digest
    if receipt_mutator is not None:
        receipt_mutator(receipt_object)
    receipt = _canonical_compact(receipt_object)
    receipt_digest = hashlib.sha256(receipt).hexdigest()
    spec["authority"]["sizing_replay_receipt_sha256"] = receipt_digest
    spec["sizing"]["source_separated_replay_receipt_sha256"] = receipt_digest
    prefix, _old_raw, suffix = _split_document(base_document)
    raw_spec = _canonical_indent(spec)
    document = prefix + raw_spec + suffix
    spec_mirror = base_spec if mirror_from_base else spec
    policy = _mirror_bytes(
        document, raw_spec, spec_mirror, failed_certificate, certificate, receipt
    )
    return document, policy, failed_certificate, certificate, receipt, spec


def _parse_bundle(bundle) -> headline.BoundSpec:
    document, policy, failed_certificate, certificate, receipt, _spec = bundle
    return headline.parse_bound_spec(
        headline.CANONICAL_DOCUMENT_PATH,
        document,
        headline.MIRROR_POLICY_PATH,
        policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
    )


def _constant(value: float, n: int = 28) -> list[float]:
    return [value] * n


def test_canonical_pair_binds_hashes_schema_and_selected_workloads():
    bound = _bound()
    assert bound.document_sha256 == "6133e2143f73c47d8b69909755f5953f926a755df9c62fce4e7bb1a0f29aae03"
    assert bound.raw_spec_sha256 == "b6605ddcfae7d3c2616cc65abce90ac1d912bea7312325123a989415d63b92c2"
    assert bound.failed_sizing_certificate_sha256 == (
        "da511809ba1ef855c39f78aacee3feba5524c222b80d77f2884b61223aa10efd"
    )
    assert bound.sizing_certificate_sha256 == (
        "4f4735cf43f227f421b0bfcc2c9f17328736a105def15071838e0ba5d5a3e18a"
    )
    assert bound.sizing_replay_receipt_sha256 == (
        "269f070b4603e93b42ebc6433d0f8deb370a021be6afcd452320a63e9a9f0ff3"
    )
    assert [
        (
            item.name,
            item.repetitions_per_arm,
            item.lower_index_1based,
            item.upper_index_1based,
        )
        for item in bound.workloads
    ] == [
        ("write-heavy", 218, 90, 129),
        ("balanced", 564, 251, 314),
        ("read-heavy", 28, 7, 22),
    ]


def test_canonical_v2_replay_receipt_binds_tools_runtime_and_certificate():
    (
        _document, _policy, _failed, certificate_bytes, receipt_bytes, spec, _mirror,
    ) = _canonical_inputs()
    certificate = json.loads(certificate_bytes)
    receipt = json.loads(receipt_bytes)
    assert receipt_bytes == _canonical_compact(receipt)
    assert receipt["schema_version"] == (
        "paper-story-a1-headline-sizing-replay-receipt/v1"
    )
    assert receipt["verification"] == {"return_code": 0, "status": "verified"}
    assert receipt["certificate"] == {
        "path": headline.SIZING_CERTIFICATE_PATH,
        "sha256": hashlib.sha256(certificate_bytes).hexdigest(),
    }
    pilot = receipt["pilot"]
    assert pilot == {
        "path": certificate["inputs"]["pilot"]["path"],
        "sha256": certificate["inputs"]["pilot"]["sha256"],
    }
    assert hashlib.sha256((ROOT / pilot["path"]).read_bytes()).hexdigest() == pilot["sha256"]
    for key, source_path, source_digest in (
        (
            "generator", headline.SIZING_GENERATOR_SOURCE_PATH,
            headline.SIZING_GENERATOR_SOURCE_SHA256,
        ),
        (
            "verifier", headline.SIZING_VERIFIER_SOURCE_PATH,
            headline.SIZING_VERIFIER_SOURCE_SHA256,
        ),
    ):
        source = receipt["sources"][key]
        assert source == {"path": source_path, "sha256": source_digest}
        assert hashlib.sha256((ROOT / source_path).read_bytes()).hexdigest() == source_digest
    assert receipt["runtime"] == certificate["runtime"]
    assert receipt["policy"] == {
        "certification_trials": spec["sizing"]["certification_trials"],
        "n_range": certificate["policy"]["n_range"],
        "root_seed": certificate["policy"]["root_seed"],
        "search_trials": spec["sizing"]["search_trials"],
    }


def test_replay_receipt_is_mandatory_and_path_and_raw_bytes_are_bound():
    document, policy, failed, certificate, receipt, base_spec, _mirror = _canonical_inputs()
    arguments = [
        headline.CANONICAL_DOCUMENT_PATH,
        document,
        headline.MIRROR_POLICY_PATH,
        policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
    ]
    _assert_raises(
        TypeError,
        headline.parse_bound_spec,
        *arguments[:-2],
        match="sizing_replay_receipt_path",
    )
    alternate = list(arguments)
    alternate[-2] = "alternate/sizing-replay-receipt.v2.json"
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        *alternate,
        match="sizing replay receipt path differs from the canonical path",
    )
    tampered = receipt.replace(b'"status":"verified"', b'"status":"verifieD"', 1)
    assert tampered != receipt and len(tampered) == len(receipt)
    altered_bytes = list(arguments)
    altered_bytes[-1] = tampered
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        *altered_bytes,
        match="sizing replay receipt SHA-256",
    )
    noncanonical_receipt = receipt.replace(b"{", b"{ ", 1)
    assert json.loads(noncanonical_receipt) == json.loads(receipt)
    spec = copy.deepcopy(base_spec)
    noncanonical_digest = hashlib.sha256(noncanonical_receipt).hexdigest()
    spec["authority"]["sizing_replay_receipt_sha256"] = noncanonical_digest
    spec["sizing"]["source_separated_replay_receipt_sha256"] = noncanonical_digest
    prefix, _raw_spec, suffix = _split_document(document)
    raw_spec = _canonical_indent(spec)
    rebound_document = prefix + raw_spec + suffix
    rebound_policy = _mirror_bytes(
        rebound_document, raw_spec, spec, failed, certificate, noncanonical_receipt
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        rebound_document,
        headline.MIRROR_POLICY_PATH,
        rebound_policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        noncanonical_receipt,
        match="sizing replay receipt is not canonical compact JSON",
    )


def test_replay_receipt_rejects_certificate_and_pilot_binding_tamper():
    def certificate_path(receipt):
        receipt["certificate"]["path"] = "alternate/sizing-certificate.v2.json"

    def certificate_hash(receipt):
        receipt["certificate"]["sha256"] = "0" * 64

    def pilot_path(receipt):
        receipt["pilot"]["path"] = "alternate/result.json"

    def pilot_hash(receipt):
        receipt["pilot"]["sha256"] = "0" * 64

    for mutator, reason in (
        (certificate_path, "receipt/certificate/path"),
        (certificate_hash, "receipt/certificate/sha256"),
        (pilot_path, "receipt/pilot/path"),
        (pilot_hash, "receipt/pilot/sha256"),
    ):
        _assert_raises(
            headline.HeadlineSpecError,
            _parse_bundle,
            _bundle(receipt_mutator=mutator),
            match=reason,
        )


def test_replay_receipt_rejects_tool_source_hash_tamper():
    def generator_hash(receipt):
        receipt["sources"]["generator"]["sha256"] = "0" * 64

    def verifier_hash(receipt):
        receipt["sources"]["verifier"]["sha256"] = "0" * 64

    for mutator, reason in (
        (generator_hash, "receipt/sources/generator/sha256"),
        (verifier_hash, "receipt/sources/verifier/sha256"),
    ):
        _assert_raises(
            headline.HeadlineSpecError,
            _parse_bundle,
            _bundle(receipt_mutator=mutator),
            match=reason,
        )


def test_replay_receipt_rejects_runtime_policy_and_status_reversal():
    def canonical_json(receipt):
        receipt["canonical_json"] = "alternate-canonicalization"

    def schema(receipt):
        receipt["schema_version"] = "paper-story-a1-headline-sizing-replay-receipt/v2"

    def runtime(receipt):
        receipt["runtime"]["numpy"]["version"] = "0.0.0"

    def root_seed(receipt):
        receipt["policy"]["root_seed"]["digest"] = "0" * 64

    def trials(receipt):
        receipt["policy"]["search_trials"] += 1

    def n_range(receipt):
        receipt["policy"]["n_range"]["maximum"] -= 1

    def status(receipt):
        receipt["verification"]["status"] = "failed"

    def return_code(receipt):
        receipt["verification"]["return_code"] = 1

    for mutator, reason in (
        (canonical_json, "receipt/canonical_json"),
        (schema, "receipt/schema_version"),
        (runtime, "receipt/runtime"),
        (root_seed, "receipt/policy"),
        (trials, "receipt/policy"),
        (n_range, "receipt/policy"),
        (status, "receipt/verification/status"),
        (return_code, "receipt/verification/return_code"),
    ):
        _assert_raises(
            headline.HeadlineSpecError,
            _parse_bundle,
            _bundle(receipt_mutator=mutator),
            match=reason,
        )


def test_headline_median_ratio_differs_from_all_pairwise_ratio_median():
    baseline = [1.0] * 14 + [100.0] * 14
    variant = [2.0] * 14 + [3.0] * 14
    result = headline.median_ratio_statistics(_bound(), "read-heavy", baseline, variant)
    expected = statistics.median(variant) / statistics.median(baseline) - 1
    all_pairwise = statistics.median(v / b for v in variant for b in baseline) - 1
    assert expected != all_pairwise
    assert result["point_effect"] == expected
    assert result["point_effect"] != all_pairwise


def test_even_n_median_uses_arithmetic_mean_of_two_central_values():
    baseline = list(range(1, 29))
    variant = [2 * value for value in baseline]
    result = headline.median_ratio_statistics(_bound(), "read-heavy", baseline, variant)
    assert result["baseline_median"] == 14.5
    assert result["variant_median"] == 29.0
    assert result["point_effect"] == 1.0
    assert result["baseline_median"] != 14


def test_floor_rule_mutation_changes_decision():
    canonical = headline.median_ratio_statistics(
        _bound(), "read-heavy", _constant(1.0), _constant(1.035)
    )

    def mutate(spec):
        spec["analysis"]["floor"]["effect_absolute"] = {"denominator": 100, "numerator": 4}
        spec["analysis"]["floor"]["band_lower"] = {"denominator": 100, "numerator": 96}
        spec["analysis"]["floor"]["band_upper"] = {"denominator": 100, "numerator": 104}

    def mutate_certificate(certificate):
        policy = certificate["policy"]
        policy["floor"] = {"denominator": 100, "numerator": 4}
        policy["band"] = {
            "lower": {"denominator": 100, "numerator": 96},
            "upper": {"denominator": 100, "numerator": 104},
        }
        operators = policy["classification_operators"]
        operators["bounded-within-floor"]["lower"]["threshold"] = policy["band"]["lower"]
        operators["bounded-within-floor"]["upper"]["threshold"] = policy["band"]["upper"]
        operators["resolved-beyond-floor"]["regression"]["threshold"] = policy["band"]["lower"]
        operators["resolved-beyond-floor"]["improvement"]["threshold"] = policy["band"]["upper"]
        deltas = (
            {"denominator": 1, "numerator": 0},
            {"denominator": 25, "numerator": 2},
            {"denominator": 25, "numerator": -2},
        )
        population_medians = (
            {"denominator": 1, "numerator": 1},
            {"denominator": 25, "numerator": 27},
            {"denominator": 25, "numerator": 23},
        )
        for index, delta in enumerate(deltas):
            policy["conditions"][index]["delta"] = delta
            certificate["model"]["conditions"][index]["delta"] = delta
            certificate["model"]["conditions"][index]["variant_population_median"] = (
                population_medians[index]
            )

    mutated = headline.median_ratio_statistics(
        _parse_bundle(_bundle(mutate, mutate_certificate)),
        "read-heavy",
        _constant(1.0),
        _constant(1.035),
    )

    assert canonical["classification"] == "resolved-beyond-floor"
    assert canonical["direction"] == "improvement"
    assert mutated["classification"] == "bounded-within-floor"
    assert mutated["direction"] is None


def test_order_index_rule_mutation_changes_interval_and_decision():
    baseline = _constant(1.0)
    variant = [0.95] * 7 + [1.0] * 21
    canonical = headline.median_ratio_statistics(_bound(), "read-heavy", baseline, variant)

    def mutate_spec(spec):
        row = next(item for item in spec["workloads"] if item["name"] == "read-heavy")
        row["lower_index_1based"] = 8

    def mutate_certificate(certificate):
        row = next(item for item in certificate["workloads"] if item["workload"] == "read-heavy")
        row["selected"]["lower_index_1based"] = 8
        selected_n = row["selected"]["n"]
        candidate = next(item for item in row["candidates"] if item["n"] == selected_n)
        candidate["order_interval"]["lower_index_1based"] = 8

    mutated_bound = _parse_bundle(_bundle(mutate_spec, mutate_certificate))
    mutated = headline.median_ratio_statistics(mutated_bound, "read-heavy", baseline, variant)
    assert canonical["ratio_interval"] == (0.95, 1.0)
    assert canonical["classification"] == "unresolved"
    assert mutated["ratio_interval"] == (1.0, 1.0)
    assert mutated["classification"] == "bounded-within-floor"


def test_boundary_operator_rules_control_exact_edges():
    canonical_positive = headline.median_ratio_statistics(
        _bound(), "read-heavy", _constant(100.0), _constant(103.0)
    )
    canonical_negative = headline.median_ratio_statistics(
        _bound(), "read-heavy", _constant(100.0), _constant(97.0)
    )
    assert canonical_positive["classification"] == "bounded-within-floor"
    assert canonical_negative["classification"] == "bounded-within-floor"

    def positive_inclusive(spec):
        spec["analysis"]["classification"]["resolved"]["lower_operator"] = ">="

    def negative_inclusive(spec):
        spec["analysis"]["classification"]["resolved"]["upper_operator"] = "<="

    def positive_certificate(certificate):
        certificate["policy"]["classification_operators"]["resolved-beyond-floor"][
            "improvement"
        ]["operator"] = ">="

    def negative_certificate(certificate):
        certificate["policy"]["classification_operators"]["resolved-beyond-floor"][
            "regression"
        ]["operator"] = "<="

    positive = headline.median_ratio_statistics(
        _parse_bundle(_bundle(positive_inclusive, positive_certificate)),
        "read-heavy",
        _constant(100.0),
        _constant(103.0),
    )
    negative = headline.median_ratio_statistics(
        _parse_bundle(_bundle(negative_inclusive, negative_certificate)),
        "read-heavy",
        _constant(100.0),
        _constant(97.0),
    )
    assert (positive["classification"], positive["direction"]) == (
        "resolved-beyond-floor", "improvement"
    )
    assert (negative["classification"], negative["direction"]) == (
        "resolved-beyond-floor", "regression"
    )


def test_document_and_mirror_raw_spec_bytes_must_match():
    def mutate(spec):
        spec["analysis"]["floor"]["effect_absolute"] = {"denominator": 100, "numerator": 4}
        spec["analysis"]["floor"]["band_lower"] = {"denominator": 100, "numerator": 96}
        spec["analysis"]["floor"]["band_upper"] = {"denominator": 100, "numerator": 104}

    bundle = _bundle(spec_mutator=mutate, mirror_from_base=True)
    _assert_raises(
        headline.HeadlineSpecError,
        _parse_bundle,
        bundle,
        match="README and mirror raw spec bytes differ",
    )


def test_alternate_document_policy_and_sizing_paths_are_rejected():
    (
        document, policy, failed_certificate, certificate, receipt, _spec, _mirror,
    ) = _canonical_inputs()
    arguments = [
        headline.CANONICAL_DOCUMENT_PATH,
        document,
        headline.MIRROR_POLICY_PATH,
        policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
    ]
    for index in (0, 2, 4, 6, 8):
        mutated = list(arguments)
        mutated[index] = "alternate/" + mutated[index]
        _assert_raises(headline.HeadlineSpecError, headline.parse_bound_spec, *mutated, match="canonical path")


def test_strict_json_rejects_duplicate_keys_at_any_depth():
    (
        document, _policy, failed_certificate, certificate, receipt, base_spec, _mirror,
    ) = _canonical_inputs()
    prefix, raw_spec, suffix = _split_document(document)
    needle = b'        "denominator": 100,\n        "numerator": 97'
    replacement = b'        "denominator": 100,\n        "denominator": 100,\n        "numerator": 97'
    assert raw_spec.count(needle) == 1
    duplicate_raw = raw_spec.replace(needle, replacement, 1)
    duplicate_document = prefix + duplicate_raw + suffix
    duplicate_policy = _mirror_bytes(
        duplicate_document, duplicate_raw, base_spec, failed_certificate, certificate,
        receipt,
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        duplicate_document,
        headline.MIRROR_POLICY_PATH,
        duplicate_policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
        match="duplicate JSON key",
    )


def test_semantically_equal_noncanonical_json_is_rejected():
    (
        document, policy, failed_certificate, certificate, receipt, base_spec, _mirror,
    ) = _canonical_inputs()
    prefix, raw_spec, suffix = _split_document(document)
    noncanonical_raw = raw_spec.replace(b"{\n", b"{ \n", 1)
    assert json.loads(noncanonical_raw) == base_spec
    noncanonical_document = prefix + noncanonical_raw + suffix
    matching_policy = _mirror_bytes(
        noncanonical_document, noncanonical_raw, base_spec,
        failed_certificate, certificate, receipt,
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        noncanonical_document,
        headline.MIRROR_POLICY_PATH,
        matching_policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
        match="not canonical indent-2",
    )
    noncanonical_policy = policy.replace(b"{\n", b"{ \n", 1)
    assert json.loads(noncanonical_policy) == json.loads(policy)
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        document,
        headline.MIRROR_POLICY_PATH,
        noncanonical_policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
        match="mirror policy is not canonical",
    )


def test_bound_spec_is_deeply_immutable_and_not_externally_constructible():
    bound = _bound()
    floor = bound.spec["analysis"]["floor"]

    def mutate_nested_floor():
        floor["band_lower"]["numerator"] = 4

    _assert_raises(TypeError, mutate_nested_floor)
    _assert_raises(AttributeError, setattr, bound.workloads[0], "repetitions_per_arm", 1)
    _assert_raises(
        headline.HeadlineSpecError,
        headline.BoundSpec,
        headline.CANONICAL_DOCUMENT_PATH,
        headline.MIRROR_POLICY_PATH,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        headline.SIZING_CERTIFICATE_PATH,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        "0" * 64,
        "0" * 64,
        "0" * 64,
        "0" * 64,
        "0" * 64,
        bound.spec,
        bound.workloads,
        match="only be constructed",
    )


def test_sizing_certificate_tamper_is_rejected_by_raw_digest():
    (
        document, policy, failed_certificate, certificate, receipt, _spec, _mirror,
    ) = _canonical_inputs()
    tampered = certificate.replace(b'"status":"selected"', b'"status":"selecteD"', 1)
    assert tampered != certificate and len(tampered) == len(certificate)
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        document,
        headline.MIRROR_POLICY_PATH,
        policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        tampered,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
        match="certificate SHA-256",
    )


def test_certificate_selected_values_must_match_spec_workloads():
    def mutate_certificate(certificate):
        row = next(item for item in certificate["workloads"] if item["workload"] == "read-heavy")
        row["selected"]["lower_index_1based"] = 8

    bundle = _bundle(certificate_mutator=mutate_certificate)
    _assert_raises(
        headline.HeadlineSpecError,
        _parse_bundle,
        bundle,
        match="selected n/index differs",
    )


def test_missing_unknown_nonfinite_and_bool_are_rejected():
    def remove_key(spec):
        del spec["analysis"]["input"]["positive_required"]

    def add_key(spec):
        spec["reporting"]["b7"]["hidden_default"] = True

    def bool_as_int(spec):
        spec["workloads"][2]["repetitions_per_arm"] = True

    for mutator in (remove_key, add_key, bool_as_int):
        _assert_raises(headline.HeadlineSpecError, _parse_bundle, _bundle(spec_mutator=mutator))

    def unknown_certificate_key(certificate):
        certificate["workloads"][0]["candidates"][0]["search"]["hidden_default"] = True

    _assert_raises(
        headline.HeadlineSpecError,
        _parse_bundle,
        _bundle(certificate_mutator=unknown_certificate_key),
        match="unknown or missing key",
    )

    (
        document, _policy, failed_certificate, certificate, receipt, base_spec, _mirror,
    ) = _canonical_inputs()
    prefix, raw_spec, suffix = _split_document(document)
    needle = b'    "clocks_per_us": 1800,'
    assert raw_spec.count(needle) == 1
    nonfinite_raw = raw_spec.replace(needle, b'    "clocks_per_us": NaN,', 1)
    nonfinite_document = prefix + nonfinite_raw + suffix
    nonfinite_policy = _mirror_bytes(
        nonfinite_document, nonfinite_raw, base_spec, failed_certificate, certificate,
        receipt,
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        nonfinite_document,
        headline.MIRROR_POLICY_PATH,
        nonfinite_policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        failed_certificate,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
        match="non-finite",
    )

    baseline = _constant(1.0)
    invalid_samples = (
        baseline[:-1],
        [True] + baseline[1:],
        ["1.0"] + baseline[1:],
        [math.nan] + baseline[1:],
        [math.inf] + baseline[1:],
        [0.0] + baseline[1:],
        [-1.0] + baseline[1:],
    )
    for invalid in invalid_samples:
        _assert_raises(
            headline.HeadlineSpecError,
            headline.median_ratio_statistics,
            _bound(),
            "read-heavy",
            invalid,
            baseline,
        )


def test_transport_marker_and_fence_rules_are_fail_closed():
    (
        document, policy, failed_certificate, certificate, receipt, _spec, _mirror,
    ) = _canonical_inputs()
    mutations = (
        b"\xef\xbb\xbf" + document,
        document.replace(b"\n", b"\r\n", 1),
        document[:-1],
        document.replace(
            b"<!-- PAPER_STORY_A1_HEADLINE_SPEC_END -->",
            b"<!-- PAPER_STORY_A1_HEADLINE_SPEC_END -->\n<!-- PAPER_STORY_A1_HEADLINE_SPEC_END -->",
            1,
        ),
        document.replace(b"```json\n", b"```JSON\n", 1),
    )
    for mutated in mutations:
        _assert_raises(
            headline.HeadlineSpecError,
            headline.parse_bound_spec,
            headline.CANONICAL_DOCUMENT_PATH,
            mutated,
            headline.MIRROR_POLICY_PATH,
            policy,
            headline.FAILED_SIZING_CERTIFICATE_PATH,
            failed_certificate,
            headline.SIZING_CERTIFICATE_PATH,
            certificate,
            headline.SIZING_REPLAY_RECEIPT_PATH,
            receipt,
        )


def test_public_apis_have_no_defaults_and_raw_mapping_is_rejected():
    expected = {
        headline.parse_bound_spec: (
            "canonical_document_path", "canonical_document_bytes",
            "mirror_policy_path", "mirror_policy_bytes",
            "failed_sizing_certificate_path", "failed_sizing_certificate_bytes",
            "sizing_certificate_path", "sizing_certificate_bytes",
            "sizing_replay_receipt_path", "sizing_replay_receipt_bytes",
        ),
        headline.median_ratio_statistics: (
            "bound_spec", "workload_name", "baseline", "variant",
        ),
    }
    for function, names in expected.items():
        parameters = tuple(inspect.signature(function).parameters.values())
        assert tuple(parameter.name for parameter in parameters) == names
        assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    _assert_raises(
        headline.HeadlineSpecError,
        headline.median_ratio_statistics,
        {"workloads": []},
        "read-heavy",
        _constant(1.0),
        _constant(1.0),
        match="parser-produced BoundSpec",
    )


def test_module_metadata_allowlist_contains_no_rule_defaults():
    source = (ROOT / "orchestrator/campaign/paper_story_a1_headline.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert assignments == {
        "CANONICAL_DOCUMENT_PATH",
        "FAILED_SIZING_CERTIFICATE_PATH",
        "MIRROR_POLICY_PATH",
        "SIZING_CERTIFICATE_PATH",
        "SIZING_GENERATOR_SOURCE_PATH",
        "SIZING_GENERATOR_SOURCE_SHA256",
        "SIZING_REPLAY_RECEIPT_PATH",
        "SIZING_VERIFIER_SOURCE_PATH",
        "SIZING_VERIFIER_SOURCE_SHA256",
    }
    forbidden = {"FLOOR", "WORKLOADS", "ORDER_INDEX", "DEFAULT_N", "CLASSIFICATION_RULES"}
    assert assignments.isdisjoint(forbidden)


def test_mirror_is_exact_nonauthority_envelope_and_has_no_fallback_fields():
    (
        document, policy, failed_certificate, certificate, receipt, spec, mirror,
    ) = _canonical_inputs()
    _prefix, raw_spec, _suffix = _split_document(document)
    assert set(mirror) == {
        "canonical_document_path",
        "canonical_document_sha256",
        "failed_sizing_certificate_path",
        "failed_sizing_certificate_sha256",
        "mirror_policy_path",
        "raw_embedded_spec_sha256",
        "sizing_certificate_path",
        "sizing_certificate_sha256",
        "sizing_replay_receipt_path",
        "sizing_replay_receipt_sha256",
        "spec_mirror",
    }
    assert mirror["canonical_document_sha256"] == hashlib.sha256(document).hexdigest()
    assert mirror["raw_embedded_spec_sha256"] == hashlib.sha256(raw_spec).hexdigest()
    assert mirror["failed_sizing_certificate_sha256"] == hashlib.sha256(
        failed_certificate
    ).hexdigest()
    assert mirror["sizing_certificate_sha256"] == hashlib.sha256(certificate).hexdigest()
    assert mirror["sizing_replay_receipt_sha256"] == hashlib.sha256(receipt).hexdigest()
    assert mirror["spec_mirror"] == spec
    assert policy == _canonical_indent(mirror)
    assert not ({"fallback", "default", "authority"} & set(mirror))


def test_deferred_contract_is_bound_without_claiming_runtime_effect():
    bound = _bound()
    assert bound.spec["execution"]["runtime_binding_status"] == "deferred-unwired"
    assert bound.spec["reporting"]["b7"]["status"] == (
        "deferred-unwired-future-report-consumer-required"
    )
    assert bound.spec["reporting"]["b8"]["status"] == (
        "deferred-unwired-future-validation-consumer-required"
    )
    result = headline.median_ratio_statistics(
        bound, "read-heavy", _constant(1.0), _constant(1.0)
    )
    assert not ({"execution", "reporting", "runtime_wired", "b7", "b8"} & set(result))


def test_spec_and_certificate_policy_are_cross_bound():
    def floor(spec):
        spec["analysis"]["floor"]["effect_absolute"] = {"denominator": 25, "numerator": 1}
        spec["analysis"]["floor"]["band_lower"] = {"denominator": 25, "numerator": 24}
        spec["analysis"]["floor"]["band_upper"] = {"denominator": 25, "numerator": 26}

    def operator(spec):
        spec["analysis"]["classification"]["resolved"]["lower_operator"] = ">="

    def family_alpha(spec):
        spec["analysis"]["interval"]["arm_failure_probability"] = {
            "denominator": 60,
            "numerator": 1,
        }
        spec["analysis"]["interval"]["family_alpha"] = {
            "denominator": 10,
            "numerator": 1,
        }

    def root_seed(spec):
        preimage = "paper-story-a1-headline-sizing-root-seed/v2|different-frozen-input"
        spec["sizing"]["root_seed_preimage"] = preimage
        spec["sizing"]["root_seed"] = hashlib.sha256(preimage.encode("ascii")).hexdigest()

    def trials(spec):
        spec["sizing"]["search_trials"] += 1

    def target_arm(spec):
        spec["workloads"][1]["variant"]["label"] = "fixed6"

    for mutator in (floor, operator, family_alpha, root_seed, trials, target_arm):
        _assert_raises(
            headline.HeadlineSpecError,
            _parse_bundle,
            _bundle(spec_mutator=mutator),
            match="certificate/policy",
        )


def test_failed_v1_certificate_path_bytes_hash_and_status_are_bound():
    document, _policy, failed, certificate, receipt, base_spec, _mirror = _canonical_inputs()
    failed_object = json.loads(failed)
    failed_object["status"] = "selected"
    mutated_failed = _canonical_compact(failed_object)
    spec = copy.deepcopy(base_spec)
    spec["authority"]["failed_sizing_certificate_sha256"] = hashlib.sha256(
        mutated_failed
    ).hexdigest()
    prefix, _raw_spec, suffix = _split_document(document)
    raw_spec = _canonical_indent(spec)
    mutated_document = prefix + raw_spec + suffix
    policy = _mirror_bytes(
        mutated_document, raw_spec, spec, mutated_failed, certificate, receipt
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.parse_bound_spec,
        headline.CANONICAL_DOCUMENT_PATH,
        mutated_document,
        headline.MIRROR_POLICY_PATH,
        policy,
        headline.FAILED_SIZING_CERTIFICATE_PATH,
        mutated_failed,
        headline.SIZING_CERTIFICATE_PATH,
        certificate,
        headline.SIZING_REPLAY_RECEIPT_PATH,
        receipt,
        match="failed certificate/status",
    )


def test_public_construction_token_cannot_bypass_parser():
    bound = _bound()
    assert not hasattr(headline.BoundSpec, "_CONSTRUCTION_TOKEN")
    assert not any("CONSTRUCTION_TOKEN" in name for name in vars(headline))
    forged = object.__new__(headline.BoundSpec)
    for field_name in (
        "canonical_document_path",
        "mirror_policy_path",
        "failed_sizing_certificate_path",
        "sizing_certificate_path",
        "sizing_replay_receipt_path",
        "document_sha256",
        "raw_spec_sha256",
        "failed_sizing_certificate_sha256",
        "sizing_certificate_sha256",
        "sizing_replay_receipt_sha256",
        "spec",
        "workloads",
    ):
        object.__setattr__(forged, field_name, getattr(bound, field_name))
    _assert_raises(
        headline.HeadlineSpecError,
        headline.median_ratio_statistics,
        forged,
        "read-heavy",
        _constant(1.0),
        _constant(1.0),
        match="parser-produced BoundSpec",
    )


def test_registered_bound_spec_mutation_cannot_change_analysis():
    bound = _parse_bundle(_bundle())
    baseline = list(range(1, 29))
    variant = [2 * value for value in baseline]
    expected = headline.median_ratio_statistics(
        bound, "read-heavy", baseline, variant
    )

    workload = next(row for row in bound.workloads if row.name == "read-heavy")
    object.__setattr__(workload, "repetitions_per_arm", 1)
    object.__setattr__(workload, "lower_index_1based", 1)
    object.__setattr__(workload, "upper_index_1based", 1)
    estimand = bound.spec["analysis"]["estimand"]
    object.__setattr__(
        estimand,
        "_items",
        tuple(
            (key, "unsupported-after-registration" if key == "even_sample_median" else value)
            for key, value in estimand._items
        ),
    )

    assert headline.median_ratio_statistics(
        bound, "read-heavy", baseline, variant
    ) == expected


def test_status_sampling_and_deferred_literals_reject_reversal():
    def formal(spec):
        spec["status"]["formal"] = True

    def promotion(spec):
        spec["status"]["promotion_prohibited"] = False

    def observed(spec):
        spec["status"]["result_observed"] = True

    def runtime(spec):
        spec["status"]["runtime_wired"] = True

    def warmup(spec):
        spec["execution"]["warmup_repetitions"] = 1

    def cohort_start(spec):
        spec["execution"]["sampling_cohort"]["first_tps_event_starts_primary_cohort"] = False

    def replacement(spec):
        spec["execution"]["sampling_cohort"]["missing_or_invalid_after_first_tps"] = "replace"

    def retry_reason(spec):
        spec["execution"]["sampling_cohort"]["pre_benchmark_retry_reasons"].append(
            "operator-request"
        )

    def reporting(spec):
        spec["reporting"]["b7"]["status"] = "wired"

    for mutator in (
        formal, promotion, observed, runtime, warmup, cohort_start,
        replacement, retry_reason, reporting,
    ):
        _assert_raises(
            headline.HeadlineSpecError,
            _parse_bundle,
            _bundle(spec_mutator=mutator),
        )


def test_collector_only_rules_are_deferred_out_of_numeric_analysis_schema():
    bound = _bound()
    assert set(bound.spec["analysis"]["input"]) == {
        "boolean_is_numeric",
        "exact_count_required",
        "finite_required",
        "numeric_coercion",
        "positive_required",
    }
    cohort = bound.spec["execution"]["sampling_cohort"]
    assert cohort["duplicate_rep_id"] == "future-collector-invalid"
    assert cohort["outlier_exclusion"] == "future-collector-prohibited"

    def claim_analysis_consumer(spec):
        spec["analysis"]["input"]["duplicate_rep_id"] = "invalid"

    _assert_raises(
        headline.HeadlineSpecError,
        _parse_bundle,
        _bundle(spec_mutator=claim_analysis_consumer),
        match="unknown or missing key",
    )


def test_extreme_numeric_inputs_are_exact_and_nonfinite_outputs_fail_closed():
    large_float_improvement = headline.median_ratio_statistics(
        _bound(), "read-heavy", _constant(2e306), _constant(2.08e306)
    )
    assert (large_float_improvement["classification"], large_float_improvement["direction"]) == (
        "resolved-beyond-floor",
        "improvement",
    )
    equal_large_float = headline.median_ratio_statistics(
        _bound(), "read-heavy", _constant(1e308), _constant(1e308)
    )
    assert equal_large_float["classification"] == "bounded-within-floor"
    assert equal_large_float["point_effect"] == 0.0

    huge = 10**1000
    huge_improvement = headline.median_ratio_statistics(
        _bound(), "read-heavy", [huge] * 28, [104 * 10**998] * 28
    )
    huge_regression = headline.median_ratio_statistics(
        _bound(), "read-heavy", [huge] * 28, [96 * 10**998] * 28
    )
    assert (huge_improvement["classification"], huge_improvement["direction"]) == (
        "resolved-beyond-floor",
        "improvement",
    )
    assert (huge_regression["classification"], huge_regression["direction"]) == (
        "resolved-beyond-floor",
        "regression",
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.median_ratio_statistics,
        _bound(),
        "read-heavy",
        _constant(5e-324),
        _constant(1e308),
        match="finite",
    )


def test_nonzero_effect_underflow_is_rejected_or_preserved_exactly():
    baseline_value = 10**400
    variant_value = baseline_value + 1
    _assert_raises(
        headline.HeadlineSpecError,
        headline.median_ratio_statistics,
        _bound(),
        "read-heavy",
        [baseline_value] * 28,
        [variant_value] * 28,
        match="point effect exact nonzero value underflows",
    )
    _assert_raises(
        headline.HeadlineSpecError,
        headline.median_ratio_statistics,
        _bound(),
        "read-heavy",
        [baseline_value] * 28,
        [baseline_value] * 21 + [variant_value] * 7,
        match="effect interval upper exact nonzero value underflows",
    )


def test_rectangle_ratio_uses_cross_arm_opposite_endpoints():
    baseline = list(range(1, 29))
    variant = [2 * value for value in baseline]
    result = headline.median_ratio_statistics(
        _bound(), "read-heavy", baseline, variant
    )
    expected_lower = variant[6] / baseline[21]
    expected_upper = variant[21] / baseline[6]
    denominator_mutant_upper = variant[21] / baseline[21]
    assert baseline[6] != baseline[21]
    assert variant[6] != variant[21]
    assert result["ratio_interval"] == (expected_lower, expected_upper)
    assert result["ratio_interval"][1] != denominator_mutant_upper
    assert result["classification"] == "unresolved"


def test_existing_a1_non_touch_manifest_is_empty_from_base():
    manifest = (
        ".claude/settings.json",
        "docs/pegasus-runbook.md",
        "hooks/README.md",
        "orchestrator/campaign/materializer_admission.py",
        "orchestrator/campaign/paper_story_a1_paired.py",
        "orchestrator/campaign/paper_story_a1_paired.v1.json",
        "orchestrator/campaign/paper_story_a1_paired.v2.json",
        "orchestrator/tests/acceptance_duration_ledger.json",
        "orchestrator/tests/test_campaign.py",
        "orchestrator/tests/test_hooks.py",
        "orchestrator/tests/test_p3_exploration_namespace.py",
        "orchestrator/tests/test_paper_story_a1_job_contract.py",
        "orchestrator/tests/test_paper_story_a1_paired.py",
        "output/insights/2026-08-24_paper-story-a1-paired",
        "output/insights/2026-08-26_paper-story-a1-sized-preregistration",
        "tools/pegasus/admission_registry.json",
        "tools/pegasus/paper_story_a1_paired.sh",
    )
    ranges = (
        ("author", AUTHOR_BASE_COMMIT, AUTHOR_TIP_COMMIT),
        ("integration", INTEGRATION_BASE_COMMIT, INTEGRATION_TIP_COMMIT),
    )
    for commit in (
        AUTHOR_BASE_COMMIT,
        AUTHOR_TIP_COMMIT,
        INTEGRATION_BASE_COMMIT,
        INTEGRATION_TIP_COMMIT,
    ):
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert ancestor.returncode == 0, (
            f"required proof commit is not a HEAD ancestor: {commit}\n"
            + ancestor.stdout
            + ancestor.stderr
        )
    for label, base, tip in ranges:
        ordered = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, tip],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert ordered.returncode == 0, (
            f"{label} proof range is not ordered: {base}..{tip}\n"
            + ordered.stdout
            + ordered.stderr
        )
        committed = subprocess.run(
            ["git", "diff", "--exit-code", base, tip, "--", *manifest],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert committed.returncode == 0, (
            f"{label} proof range touched the existing A-1 manifest: "
            f"{base}..{tip}\n"
            + committed.stdout
            + committed.stderr
        )
    worktree = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *manifest],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert worktree.returncode == 0, worktree.stderr
    assert worktree.stdout == ""


EXPECTED_SELF_TEST_NAMES = frozenset(
    {
        "test_canonical_pair_binds_hashes_schema_and_selected_workloads",
        "test_canonical_v2_replay_receipt_binds_tools_runtime_and_certificate",
        "test_replay_receipt_is_mandatory_and_path_and_raw_bytes_are_bound",
        "test_replay_receipt_rejects_certificate_and_pilot_binding_tamper",
        "test_replay_receipt_rejects_tool_source_hash_tamper",
        "test_replay_receipt_rejects_runtime_policy_and_status_reversal",
        "test_headline_median_ratio_differs_from_all_pairwise_ratio_median",
        "test_even_n_median_uses_arithmetic_mean_of_two_central_values",
        "test_floor_rule_mutation_changes_decision",
        "test_order_index_rule_mutation_changes_interval_and_decision",
        "test_boundary_operator_rules_control_exact_edges",
        "test_document_and_mirror_raw_spec_bytes_must_match",
        "test_alternate_document_policy_and_sizing_paths_are_rejected",
        "test_strict_json_rejects_duplicate_keys_at_any_depth",
        "test_semantically_equal_noncanonical_json_is_rejected",
        "test_bound_spec_is_deeply_immutable_and_not_externally_constructible",
        "test_sizing_certificate_tamper_is_rejected_by_raw_digest",
        "test_certificate_selected_values_must_match_spec_workloads",
        "test_missing_unknown_nonfinite_and_bool_are_rejected",
        "test_transport_marker_and_fence_rules_are_fail_closed",
        "test_public_apis_have_no_defaults_and_raw_mapping_is_rejected",
        "test_module_metadata_allowlist_contains_no_rule_defaults",
        "test_mirror_is_exact_nonauthority_envelope_and_has_no_fallback_fields",
        "test_deferred_contract_is_bound_without_claiming_runtime_effect",
        "test_spec_and_certificate_policy_are_cross_bound",
        "test_failed_v1_certificate_path_bytes_hash_and_status_are_bound",
        "test_public_construction_token_cannot_bypass_parser",
        "test_registered_bound_spec_mutation_cannot_change_analysis",
        "test_status_sampling_and_deferred_literals_reject_reversal",
        "test_collector_only_rules_are_deferred_out_of_numeric_analysis_schema",
        "test_extreme_numeric_inputs_are_exact_and_nonfinite_outputs_fail_closed",
        "test_nonzero_effect_underflow_is_rejected_or_preserved_exactly",
        "test_rectangle_ratio_uses_cross_arm_opposite_endpoints",
        "test_existing_a1_non_touch_manifest_is_empty_from_base",
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
