"""Pure binding and headline statistics for the separate A-1 headline study.

The README embedded JSON is the sole rule authority.  This module performs no
I/O: callers must supply the five canonical paths and the bytes they read.
Runtime loading, campaign wiring, B-7 reporting, and B-8 validation remain
future consumers and are intentionally not implemented here.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable


CANONICAL_DOCUMENT_PATH = (
    "output/insights/2026-08-27_paper-story-a1-headline-estimand-"
    "preregistration/README.md"
)
MIRROR_POLICY_PATH = "orchestrator/campaign/paper_story_a1_headline.v1.json"
FAILED_SIZING_CERTIFICATE_PATH = (
    "output/insights/2026-08-27_paper-story-a1-headline-estimand-"
    "preregistration/sizing-certificate.failed-v1.json"
)
SIZING_CERTIFICATE_PATH = (
    "output/insights/2026-08-27_paper-story-a1-headline-estimand-"
    "preregistration/sizing-certificate.v2.json"
)
SIZING_REPLAY_RECEIPT_PATH = (
    "output/insights/2026-08-27_paper-story-a1-headline-estimand-"
    "preregistration/sizing-replay-receipt.v2.json"
)
SIZING_GENERATOR_SOURCE_PATH = "tools/size_paper_story_a1_headline.py"
SIZING_GENERATOR_SOURCE_SHA256 = (
    "9755faec6f5f3731f2c1eea25c6ce5568c58f6bb344ac30a66f941841e180596"
)
SIZING_VERIFIER_SOURCE_PATH = "tools/verify_paper_story_a1_headline_sizing.py"
SIZING_VERIFIER_SOURCE_SHA256 = (
    "ab1c0b873d319fc521db301ae56602348b14d6149662b5f40267b73eec2d2b8b"
)


class HeadlineSpecError(ValueError):
    """The supplied authority bytes, mirror, certificates, receipt, or samples are invalid."""


@dataclass(frozen=True)
class FrozenObject(Mapping[str, object]):
    """A recursively immutable JSON object without a mutable backing mapping."""

    _items: tuple[tuple[str, object], ...]

    def __getitem__(self, key: str) -> object:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _value in self._items)

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class WorkloadRule:
    """Typed analysis projection of one workload's authority-owned sizing row."""

    name: str
    repetitions_per_arm: int
    lower_index_1based: int
    upper_index_1based: int


@dataclass(frozen=True, init=False)
class BoundSpec:
    """Verified, deeply immutable projection sealed by the parser closure."""

    canonical_document_path: str
    mirror_policy_path: str
    failed_sizing_certificate_path: str
    sizing_certificate_path: str
    sizing_replay_receipt_path: str
    document_sha256: str
    raw_spec_sha256: str
    failed_sizing_certificate_sha256: str
    sizing_certificate_sha256: str
    sizing_replay_receipt_sha256: str
    spec: FrozenObject
    workloads: tuple[WorkloadRule, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        raise HeadlineSpecError("BoundSpec can only be constructed by parse_bound_spec")


@dataclass(frozen=True)
class _BoundSpecSnapshot:
    """Registry-owned copy of every parser-verified BoundSpec field."""

    canonical_document_path: str
    mirror_policy_path: str
    failed_sizing_certificate_path: str
    sizing_certificate_path: str
    sizing_replay_receipt_path: str
    document_sha256: str
    raw_spec_sha256: str
    failed_sizing_certificate_sha256: str
    sizing_certificate_sha256: str
    sizing_replay_receipt_sha256: str
    spec: FrozenObject
    workloads: tuple[WorkloadRule, ...]


def _freeze(value: object) -> object:
    if type(value) is dict:
        return FrozenObject(tuple((key, _freeze(child)) for key, child in value.items()))
    if type(value) is list:
        return tuple(_freeze(child) for child in value)
    return value


def _copy_frozen(value: object) -> object:
    """Copy a frozen JSON projection without sharing reflectively mutable nodes."""

    if isinstance(value, FrozenObject):
        return FrozenObject(
            tuple((key, _copy_frozen(child)) for key, child in value._items)
        )
    if type(value) is tuple:
        return tuple(_copy_frozen(child) for child in value)
    return value


def _copy_bound_spec_snapshot(snapshot: _BoundSpecSnapshot) -> _BoundSpecSnapshot:
    spec = _copy_frozen(snapshot.spec)
    if not isinstance(spec, FrozenObject):  # pragma: no cover - snapshot invariant
        raise AssertionError("snapshot spec root is not an object")
    workloads = tuple(
        WorkloadRule(
            row.name,
            row.repetitions_per_arm,
            row.lower_index_1based,
            row.upper_index_1based,
        )
        for row in snapshot.workloads
    )
    return _BoundSpecSnapshot(
        snapshot.canonical_document_path,
        snapshot.mirror_policy_path,
        snapshot.failed_sizing_certificate_path,
        snapshot.sizing_certificate_path,
        snapshot.sizing_replay_receipt_path,
        snapshot.document_sha256,
        snapshot.raw_spec_sha256,
        snapshot.failed_sizing_certificate_sha256,
        snapshot.sizing_certificate_sha256,
        snapshot.sizing_replay_receipt_sha256,
        spec,
        workloads,
    )


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise HeadlineSpecError(f"duplicate JSON key: {key!r}")
        value[key] = child
    return value


def _reject_nonfinite(token: str) -> None:
    raise HeadlineSpecError(f"non-finite JSON number is forbidden: {token!r}")


def _transport_text(raw: bytes, path: str) -> str:
    if type(raw) is not bytes:
        raise HeadlineSpecError(f"{path} bytes must have exact type bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise HeadlineSpecError(f"{path} must not start with a UTF-8 BOM")
    if b"\r" in raw:
        raise HeadlineSpecError(f"{path} must use LF, never CR")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise HeadlineSpecError(f"{path} must end in exactly one terminal LF")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise HeadlineSpecError(f"{path} is not strict UTF-8") from exc


def _parse_json_object(raw: bytes, path: str) -> dict[str, Any]:
    text = _transport_text(raw, path)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite,
        )
    except json.JSONDecodeError as exc:
        raise HeadlineSpecError(f"{path} is not valid JSON") from exc
    if type(value) is not dict:
        raise HeadlineSpecError(f"{path} JSON root must be an object")
    return value


def _canonical_indent_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise HeadlineSpecError("JSON value cannot be rendered canonically") from exc
    return (rendered + "\n").encode("utf-8")


def _canonical_compact_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise HeadlineSpecError("JSON value cannot be rendered canonically") from exc
    return (rendered + "\n").encode("utf-8")


def _exact_object(value: object, keys: set[str], path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise HeadlineSpecError(f"{path} must be an object")
    if set(value) != keys:
        raise HeadlineSpecError(f"{path} has an unknown or missing key")
    return value


def _require_string(value: object, path: str) -> str:
    if type(value) is not str or not value:
        raise HeadlineSpecError(f"{path} must be a non-empty string")
    return value


def _require_bool(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise HeadlineSpecError(f"{path} must be a boolean")
    return value


def _require_int(value: object, path: str, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise HeadlineSpecError(f"{path} must be an integer; bool is not an integer")
    if minimum is not None and value < minimum:
        raise HeadlineSpecError(f"{path} is below its minimum")
    return value


def _require_sha256(value: object, path: str) -> str:
    digest = _require_string(value, path)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise HeadlineSpecError(f"{path} must be 64 lowercase hexadecimal digits")
    return digest


def _require_literal(value: object, expected: object, path: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise HeadlineSpecError(f"{path} is unsupported by this schema version")


def _fraction_rule(value: object, path: str) -> Fraction:
    rule = _exact_object(value, {"denominator", "numerator"}, path)
    numerator = _require_int(rule["numerator"], f"{path}/numerator")
    denominator = _require_int(rule["denominator"], f"{path}/denominator", minimum=1)
    return Fraction(numerator, denominator)


def _validate_analysis(value: object) -> None:
    analysis = _exact_object(
        value, {"classification", "estimand", "floor", "input", "interval"}, "/analysis"
    )
    classification = _exact_object(
        analysis["classification"], {"bounded", "otherwise", "resolved"},
        "/analysis/classification",
    )
    bounded = _exact_object(
        classification["bounded"], {"label", "lower_operator", "upper_operator"},
        "/analysis/classification/bounded",
    )
    resolved = _exact_object(
        classification["resolved"],
        {
            "direction_negative", "direction_positive", "label",
            "lower_operator", "upper_operator",
        },
        "/analysis/classification/resolved",
    )
    for key in ("label", "lower_operator", "upper_operator"):
        _require_string(bounded[key], f"/analysis/classification/bounded/{key}")
    for key in (
        "direction_negative", "direction_positive", "label",
        "lower_operator", "upper_operator",
    ):
        _require_string(resolved[key], f"/analysis/classification/resolved/{key}")
    _require_string(classification["otherwise"], "/analysis/classification/otherwise")
    supported_operators = {"<", "<=", ">", ">="}
    for rule, path in (
        (bounded, "/analysis/classification/bounded"),
        (resolved, "/analysis/classification/resolved"),
    ):
        if rule["lower_operator"] not in supported_operators:
            raise HeadlineSpecError(f"{path}/lower_operator is unsupported")
        if rule["upper_operator"] not in supported_operators:
            raise HeadlineSpecError(f"{path}/upper_operator is unsupported")

    estimand = _exact_object(
        analysis["estimand"],
        {
            "effect", "even_sample_median", "point_formula",
            "population_parameter", "rounding_for_decision",
        },
        "/analysis/estimand",
    )
    _require_literal(estimand["effect"], "median-ratio-minus-one", "/analysis/estimand/effect")
    _require_literal(
        estimand["even_sample_median"],
        "arithmetic-mean-of-two-central-order-statistics",
        "/analysis/estimand/even_sample_median",
    )
    _require_literal(
        estimand["point_formula"],
        "median(variant_tps)/median(baseline_tps)-1",
        "/analysis/estimand/point_formula",
    )
    _require_literal(
        estimand["population_parameter"],
        "population-median(variant)/population-median(baseline)-1",
        "/analysis/estimand/population_parameter",
    )
    _require_literal(
        estimand["rounding_for_decision"], "prohibited",
        "/analysis/estimand/rounding_for_decision",
    )

    floor = _exact_object(
        analysis["floor"], {"band_lower", "band_upper", "effect_absolute", "scale"},
        "/analysis/floor",
    )
    lower = _fraction_rule(floor["band_lower"], "/analysis/floor/band_lower")
    upper = _fraction_rule(floor["band_upper"], "/analysis/floor/band_upper")
    effect = _fraction_rule(floor["effect_absolute"], "/analysis/floor/effect_absolute")
    _require_literal(floor["scale"], "ratio-minus-one", "/analysis/floor/scale")
    if effect <= 0 or lower != 1 - effect or upper != 1 + effect:
        raise HeadlineSpecError("/analysis/floor fractions are not one coherent ratio band")

    input_rule = _exact_object(
        analysis["input"],
        {
            "boolean_is_numeric", "exact_count_required", "finite_required",
            "numeric_coercion", "positive_required",
        },
        "/analysis/input",
    )
    _require_literal(input_rule["boolean_is_numeric"], False, "/analysis/input/boolean_is_numeric")
    _require_literal(input_rule["exact_count_required"], True, "/analysis/input/exact_count_required")
    _require_literal(input_rule["finite_required"], True, "/analysis/input/finite_required")
    _require_literal(input_rule["numeric_coercion"], "prohibited", "/analysis/input/numeric_coercion")
    _require_literal(input_rule["positive_required"], True, "/analysis/input/positive_required")

    interval = _exact_object(
        analysis["interval"],
        {
            "arm_failure_probability", "cross_arm_independence_required_for_union_bound",
            "family", "family_alpha", "method", "runtime_quantile_or_randomness",
            "ties_or_nonunique_median_coverage", "within_arm_sampling",
        },
        "/analysis/interval",
    )
    arm_failure = _fraction_rule(
        interval["arm_failure_probability"], "/analysis/interval/arm_failure_probability"
    )
    family_alpha = _fraction_rule(interval["family_alpha"], "/analysis/interval/family_alpha")
    if arm_failure <= 0 or family_alpha <= 0 or arm_failure * 6 != family_alpha:
        raise HeadlineSpecError("/analysis/interval Bonferroni fractions are incoherent")
    _require_literal(
        interval["cross_arm_independence_required_for_union_bound"], False,
        "/analysis/interval/cross_arm_independence_required_for_union_bound",
    )
    _require_literal(interval["family"], "three-workloads-six-arms", "/analysis/interval/family")
    _require_literal(
        interval["method"], "exact-binomial-order-statistic-median-rectangle-ratio",
        "/analysis/interval/method",
    )
    _require_literal(
        interval["runtime_quantile_or_randomness"], "prohibited",
        "/analysis/interval/runtime_quantile_or_randomness",
    )
    _require_literal(
        interval["ties_or_nonunique_median_coverage"],
        "at-least-nominal-conservative",
        "/analysis/interval/ties_or_nonunique_median_coverage",
    )
    _require_literal(
        interval["within_arm_sampling"],
        "iid-from-fixed-population-required",
        "/analysis/interval/within_arm_sampling",
    )


def _validate_deferred_sections(spec: dict[str, Any], workload_names: tuple[str, ...]) -> None:
    applicability = _exact_object(
        spec["applicability"], {"encoding_grid", "mu_grid", "shape_grid"}, "/applicability"
    )
    for key, expected in (
        ("encoding_grid", "not-applicable-no-generated-proposal-encoding"),
        ("mu_grid", "not-applicable-no-mu-grid"),
        ("shape_grid", "not-applicable-no-shape-grid"),
    ):
        _require_literal(applicability[key], expected, f"/applicability/{key}")

    execution = _exact_object(
        spec["execution"],
        {
            "arm_order", "block_count", "build_type", "clocks_per_us",
            "env_tag", "extime_seconds", "instrumentation", "numa",
            "phase_order", "runtime_binding_status", "sampling_cohort",
            "source_and_binary_binding", "warmup_repetitions",
        },
        "/execution",
    )
    for key, expected in (
        (
            "arm_order",
            "alternate-by-block-baseline-first-on-odd-block-variant-first-on-even-block",
        ),
        ("block_count", "selected-n-per-workload"),
        ("build_type", "Release"),
        ("env_tag", "linux-baremetal"),
        ("numa", "numactl-interleave-all"),
        ("runtime_binding_status", "deferred-unwired"),
        (
            "source_and_binary_binding",
            "future-campaign-lock-build-start-block-report-required",
        ),
    ):
        _require_literal(execution[key], expected, f"/execution/{key}")
    _require_literal(execution["clocks_per_us"], 1800, "/execution/clocks_per_us")
    _require_literal(execution["extime_seconds"], 3, "/execution/extime_seconds")
    _require_literal(execution["warmup_repetitions"], 0, "/execution/warmup_repetitions")
    instrumentation = _exact_object(
        execution["instrumentation"], {"ccbench_trace", "performance_build_trace_disabled"},
        "/execution/instrumentation",
    )
    _require_literal(
        instrumentation["ccbench_trace"], 0, "/execution/instrumentation/ccbench_trace"
    )
    _require_literal(
        instrumentation["performance_build_trace_disabled"], True,
        "/execution/instrumentation/performance_build_trace_disabled",
    )
    phase_order = execution["phase_order"]
    if type(phase_order) is not list or tuple(phase_order) != workload_names:
        raise HeadlineSpecError("/execution/phase_order must match workload order exactly")
    if any(type(name) is not str for name in phase_order):
        raise HeadlineSpecError("/execution/phase_order entries must be strings")
    cohort = _exact_object(
        execution["sampling_cohort"],
        {
            "duplicate_rep_id", "first_tps_event_starts_primary_cohort",
            "missing_or_invalid_after_first_tps", "outlier_exclusion",
            "pre_benchmark_retry_reasons",
        },
        "/execution/sampling_cohort",
    )
    _require_literal(
        cohort["duplicate_rep_id"], "future-collector-invalid",
        "/execution/sampling_cohort/duplicate_rep_id",
    )
    _require_literal(
        cohort["first_tps_event_starts_primary_cohort"], True,
        "/execution/sampling_cohort/first_tps_event_starts_primary_cohort",
    )
    _require_literal(
        cohort["missing_or_invalid_after_first_tps"],
        "retain-as-failure-no-replacement",
        "/execution/sampling_cohort/missing_or_invalid_after_first_tps",
    )
    _require_literal(
        cohort["outlier_exclusion"], "future-collector-prohibited",
        "/execution/sampling_cohort/outlier_exclusion",
    )
    _require_literal(
        cohort["pre_benchmark_retry_reasons"],
        [
            "allocation-lost-before-first-tps",
            "build-failed-before-benchmark",
            "scheduler-never-started",
        ],
        "/execution/sampling_cohort/pre_benchmark_retry_reasons",
    )

    reporting = _exact_object(
        spec["reporting"], {"b7", "b8", "exposure", "missing"}, "/reporting"
    )
    b7 = _exact_object(
        reporting["b7"],
        {"all_workloads_required", "invalid_omission", "regression_omission", "status"},
        "/reporting/b7",
    )
    _require_literal(b7["all_workloads_required"], True, "/reporting/b7/all_workloads_required")
    _require_literal(b7["invalid_omission"], "prohibited", "/reporting/b7/invalid_omission")
    _require_literal(b7["regression_omission"], "prohibited", "/reporting/b7/regression_omission")
    _require_literal(
        b7["status"], "deferred-unwired-future-report-consumer-required",
        "/reporting/b7/status",
    )
    b8 = _exact_object(
        reporting["b8"],
        {"distinct_seed_required", "long_duration_required", "primary_result_replacement", "status"},
        "/reporting/b8",
    )
    _require_literal(b8["distinct_seed_required"], True, "/reporting/b8/distinct_seed_required")
    _require_literal(b8["long_duration_required"], True, "/reporting/b8/long_duration_required")
    _require_literal(
        b8["primary_result_replacement"], "prohibited",
        "/reporting/b8/primary_result_replacement",
    )
    _require_literal(
        b8["status"], "deferred-unwired-future-validation-consumer-required",
        "/reporting/b8/status",
    )
    exposure = _exact_object(
        reporting["exposure"],
        {"attempt_history_required", "post_exposure_rule_change", "result_exposure_before_freeze"},
        "/reporting/exposure",
    )
    _require_literal(
        exposure["attempt_history_required"], True,
        "/reporting/exposure/attempt_history_required",
    )
    _require_literal(
        exposure["post_exposure_rule_change"], "prohibited",
        "/reporting/exposure/post_exposure_rule_change",
    )
    _require_literal(
        exposure["result_exposure_before_freeze"], "prohibited",
        "/reporting/exposure/result_exposure_before_freeze",
    )
    missing = _exact_object(
        reporting["missing"],
        {"partial_workload_report", "rerun_to_replace_missing_after_first_tps"},
        "/reporting/missing",
    )
    _require_literal(
        missing["partial_workload_report"], "invalid",
        "/reporting/missing/partial_workload_report",
    )
    _require_literal(
        missing["rerun_to_replace_missing_after_first_tps"], "prohibited",
        "/reporting/missing/rerun_to_replace_missing_after_first_tps",
    )

    status = _exact_object(
        spec["status"], {"formal", "promotion_prohibited", "result_observed", "runtime_wired"},
        "/status",
    )
    for key, expected in (
        ("formal", False),
        ("promotion_prohibited", True),
        ("result_observed", False),
        ("runtime_wired", False),
    ):
        _require_literal(status[key], expected, f"/status/{key}")


def _validate_sizing(value: object) -> tuple[str, str]:
    sizing = _exact_object(
        value,
        {
            "certificate_sha256", "certification_alpha_spending",
            "certification_trials", "conditions", "invalid_trial", "n_max", "n_min",
            "planning_cv_is_target_arm_upper_bound", "root_seed",
            "root_seed_preimage", "search_trials", "selection",
            "source_separated_replay_receipt_sha256",
            "success_probability_required",
        },
        "/sizing",
    )
    digest = _require_sha256(sizing["certificate_sha256"], "/sizing/certificate_sha256")
    receipt_digest = _require_sha256(
        sizing["source_separated_replay_receipt_sha256"],
        "/sizing/source_separated_replay_receipt_sha256",
    )
    spending = _exact_object(
        sizing["certification_alpha_spending"],
        {"all_attempts_total_alpha", "condition_alpha_at_attempt_j"},
        "/sizing/certification_alpha_spending",
    )
    if _fraction_rule(
        spending["all_attempts_total_alpha"],
        "/sizing/certification_alpha_spending/all_attempts_total_alpha",
    ) != Fraction(1, 20):
        raise HeadlineSpecError("/sizing certification alpha cap must equal 1/20")
    _require_literal(
        spending["condition_alpha_at_attempt_j"], "1/(60*j*(j+1))",
        "/sizing/certification_alpha_spending/condition_alpha_at_attempt_j",
    )
    if _fraction_rule(
        sizing["success_probability_required"], "/sizing/success_probability_required"
    ) != Fraction(4, 5):
        raise HeadlineSpecError("/sizing success probability must equal 4/5")
    for key in ("certification_trials", "n_max", "n_min", "search_trials"):
        _require_int(sizing[key], f"/sizing/{key}", minimum=1)
    if sizing["n_min"] > sizing["n_max"]:
        raise HeadlineSpecError("/sizing n_min exceeds n_max")
    conditions = sizing["conditions"]
    if type(conditions) is not list or conditions != [
        "zero", "positive-two-floor", "negative-two-floor"
    ]:
        raise HeadlineSpecError("/sizing/conditions must be the exact three-condition family")
    _require_literal(
        sizing["invalid_trial"], "failure-in-fixed-denominator", "/sizing/invalid_trial"
    )
    _require_literal(
        sizing["planning_cv_is_target_arm_upper_bound"], False,
        "/sizing/planning_cv_is_target_arm_upper_bound",
    )
    root_seed = _require_sha256(sizing["root_seed"], "/sizing/root_seed")
    root_seed_preimage = _require_string(
        sizing["root_seed_preimage"], "/sizing/root_seed_preimage"
    )
    try:
        encoded_preimage = root_seed_preimage.encode("ascii", errors="strict")
    except UnicodeEncodeError as exc:
        raise HeadlineSpecError("/sizing/root_seed_preimage must be ASCII") from exc
    if hashlib.sha256(encoded_preimage).hexdigest() != root_seed:
        raise HeadlineSpecError("/sizing root seed digest differs from its preimage")
    _require_literal(
        sizing["selection"],
        "ascending-every-n-first-search-and-alpha-spent-certification-pass",
        "/sizing/selection",
    )
    return digest, receipt_digest


def _validate_workloads(value: object, n_min: int, n_max: int) -> tuple[WorkloadRule, ...]:
    if type(value) is not list or len(value) != 3:
        raise HeadlineSpecError("/workloads must contain exactly three objects")
    rows: list[WorkloadRule] = []
    names: set[str] = set()
    for index, raw in enumerate(value):
        path = f"/workloads/{index}"
        row = _exact_object(
            raw,
            {
                "baseline", "lower_index_1based", "name", "records",
                "repetitions_per_arm", "rmw", "rratio", "skew", "threads",
                "upper_index_1based", "variant",
            },
            path,
        )
        name = _require_string(row["name"], f"{path}/name")
        if name in names:
            raise HeadlineSpecError("/workloads names must be unique")
        names.add(name)
        repetitions = _require_int(row["repetitions_per_arm"], f"{path}/repetitions_per_arm", minimum=1)
        lower = _require_int(row["lower_index_1based"], f"{path}/lower_index_1based", minimum=1)
        upper = _require_int(row["upper_index_1based"], f"{path}/upper_index_1based", minimum=1)
        if repetitions < n_min or repetitions > n_max:
            raise HeadlineSpecError(f"{path}/repetitions_per_arm is outside sizing range")
        if not (1 <= lower <= upper <= repetitions):
            raise HeadlineSpecError(f"{path} order indices are outside the arm")
        for key in ("records", "rmw", "rratio", "threads"):
            _require_int(row[key], f"{path}/{key}", minimum=0)
        _require_string(row["skew"], f"{path}/skew")
        for arm_key in ("baseline", "variant"):
            arm_path = f"{path}/{arm_key}"
            arm = _exact_object(
                row[arm_key], {"BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACK_OFF", "label"}, arm_path
            )
            for flag in ("BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACK_OFF"):
                _require_int(arm[flag], f"{arm_path}/{flag}")
            _require_string(arm["label"], f"{arm_path}/label")
        rows.append(WorkloadRule(name, repetitions, lower, upper))
    return tuple(rows)


def _validate_spec(
    spec: dict[str, Any],
) -> tuple[tuple[WorkloadRule, ...], str, str, str]:
    _exact_object(
        spec,
        {
            "analysis", "applicability", "authority", "execution", "reporting",
            "schema_version", "sizing", "status", "study_id", "workloads",
        },
        "/",
    )
    _require_literal(
        spec["schema_version"], "paper-story-a1-headline-preregistration-spec/v2",
        "/schema_version",
    )
    _require_literal(
        spec["study_id"], "paper-story-a1-headline-estimand-20260828-v2",
        "/study_id",
    )
    _validate_analysis(spec["analysis"])
    sizing_digest, sizing_receipt_digest = _validate_sizing(spec["sizing"])
    sizing = spec["sizing"]
    workloads = _validate_workloads(spec["workloads"], sizing["n_min"], sizing["n_max"])
    _validate_deferred_sections(spec, tuple(row.name for row in workloads))
    authority = _exact_object(
        spec["authority"],
        {
            "canonical_document_path", "canonicalization", "mirror_policy_path",
            "failed_sizing_certificate_path", "failed_sizing_certificate_sha256",
            "sizing_certificate_path", "sizing_certificate_sha256",
            "sizing_replay_receipt_path", "sizing_replay_receipt_sha256",
        },
        "/authority",
    )
    _require_literal(authority["canonical_document_path"], CANONICAL_DOCUMENT_PATH, "/authority/canonical_document_path")
    _require_literal(
        authority["canonicalization"], "strict-utf8-json-object-indent-2-sorted-keys-lf-v1",
        "/authority/canonicalization",
    )
    _require_literal(authority["mirror_policy_path"], MIRROR_POLICY_PATH, "/authority/mirror_policy_path")
    _require_literal(
        authority["failed_sizing_certificate_path"], FAILED_SIZING_CERTIFICATE_PATH,
        "/authority/failed_sizing_certificate_path",
    )
    failed_digest = _require_sha256(
        authority["failed_sizing_certificate_sha256"],
        "/authority/failed_sizing_certificate_sha256",
    )
    _require_literal(authority["sizing_certificate_path"], SIZING_CERTIFICATE_PATH, "/authority/sizing_certificate_path")
    authority_digest = _require_sha256(
        authority["sizing_certificate_sha256"], "/authority/sizing_certificate_sha256"
    )
    if authority_digest != sizing_digest:
        raise HeadlineSpecError("authority and sizing certificate SHA-256 differ")
    _require_literal(
        authority["sizing_replay_receipt_path"], SIZING_REPLAY_RECEIPT_PATH,
        "/authority/sizing_replay_receipt_path",
    )
    authority_receipt_digest = _require_sha256(
        authority["sizing_replay_receipt_sha256"],
        "/authority/sizing_replay_receipt_sha256",
    )
    if authority_receipt_digest != sizing_receipt_digest:
        raise HeadlineSpecError("authority and sizing replay receipt SHA-256 differ")
    return workloads, failed_digest, sizing_digest, sizing_receipt_digest


def _extract_embedded_spec(document_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    _transport_text(document_bytes, CANONICAL_DOCUMENT_PATH)
    start_marker = b"<!-- PAPER_STORY_A1_HEADLINE_SPEC_START -->"
    end_marker = b"<!-- PAPER_STORY_A1_HEADLINE_SPEC_END -->"
    json_fence = b"```json\n"
    closing_fence = b"```\n"
    if document_bytes.count(start_marker) != 1 or document_bytes.count(end_marker) != 1:
        raise HeadlineSpecError("README must contain each spec marker exactly once")
    if document_bytes.count(json_fence) != 1 or document_bytes.count(closing_fence) != 1:
        raise HeadlineSpecError("README must contain each spec fence exactly once")
    start_token = start_marker + b"\n" + json_fence
    end_token = closing_fence + end_marker
    if document_bytes.count(start_token) != 1 or document_bytes.count(end_token) != 1:
        raise HeadlineSpecError("README marker and fence grammar differs")
    prefix, remainder = document_bytes.split(start_token, 1)
    raw_spec, suffix = remainder.split(end_token, 1)
    del prefix
    if not suffix.startswith(b"\n"):
        raise HeadlineSpecError("README closing marker must end its own line")
    spec = _parse_json_object(raw_spec, "README embedded spec")
    if raw_spec != _canonical_indent_bytes(spec):
        raise HeadlineSpecError("README embedded spec is not canonical indent-2 sorted-key JSON")
    return raw_spec, spec


def _fraction_object(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def _expected_certificate_policy(spec: dict[str, Any]) -> dict[str, Any]:
    analysis = spec["analysis"]
    floor = analysis["floor"]
    interval = analysis["interval"]
    classification = analysis["classification"]
    resolved = classification["resolved"]
    bounded = classification["bounded"]
    sizing = spec["sizing"]
    effect = _fraction_rule(floor["effect_absolute"], "/analysis/floor/effect_absolute")
    condition_names = sizing["conditions"]
    condition_rules = (
        (condition_names[0], Fraction(0), bounded["label"], None),
        (condition_names[1], 2 * effect, resolved["label"], resolved["direction_positive"]),
        (condition_names[2], -2 * effect, resolved["label"], resolved["direction_negative"]),
    )
    conditions = [
        {
            "delta": _fraction_object(delta),
            "name": name,
            "success": {"classification": label, "direction": direction},
        }
        for name, delta, label, direction in condition_rules
    ]
    target_arm_mapping = [
        {
            "baseline": row["baseline"]["label"],
            "variant": row["variant"]["label"],
            "workload": row["name"],
        }
        for row in spec["workloads"]
    ]
    return {
        "arm_count": 6,
        "arm_failure_target": interval["arm_failure_probability"],
        "band": {"lower": floor["band_lower"], "upper": floor["band_upper"]},
        "certification": {
            "all_attempts_per_condition_alpha": {"denominator": 60, "numerator": 1},
            "all_attempts_total_alpha": sizing["certification_alpha_spending"]["all_attempts_total_alpha"],
            "alpha_accounting": "exact-rational-three-conditions-all-attempts-per-workload",
            "condition_alpha_at_attempt_j": sizing["certification_alpha_spending"]["condition_alpha_at_attempt_j"],
            "condition_count": 3,
            "failure_action": "continue-to-next-search-passing-n",
            "family_alpha": interval["family_alpha"],
            "method": "one-sided-exact-clopper-pearson-lower",
            "trials": sizing["certification_trials"],
        },
        "classification_operators": {
            bounded["label"]: {
                "lower": {
                    "endpoint": "ratio-lower",
                    "operator": bounded["lower_operator"],
                    "threshold": floor["band_lower"],
                },
                "upper": {
                    "endpoint": "ratio-upper",
                    "operator": bounded["upper_operator"],
                    "threshold": floor["band_upper"],
                },
            },
            "fallback": classification["otherwise"],
            resolved["label"]: {
                resolved["direction_positive"]: {
                    "endpoint": "ratio-lower",
                    "operator": resolved["lower_operator"],
                    "threshold": floor["band_upper"],
                },
                resolved["direction_negative"]: {
                    "endpoint": "ratio-upper",
                    "operator": resolved["upper_operator"],
                    "threshold": floor["band_lower"],
                },
            },
        },
        "conditions": conditions,
        "family_alpha": interval["family_alpha"],
        "floor": floor["effect_absolute"],
        "interval_family": {
            "arm_count": 6,
            "arm_failure_target": interval["arm_failure_probability"],
            "family_alpha": interval["family_alpha"],
            "median_interval": "exact-binomial-order-statistic-equal-tail",
            "ratio_mapping": "rectangle-opposite-arm-endpoints",
        },
        "invalid_rule": "invalid-is-failure-with-fixed-trial-denominator",
        "n_max": sizing["n_max"],
        "n_min": sizing["n_min"],
        "n_range": {"maximum": sizing["n_max"], "minimum": sizing["n_min"], "step": 1},
        "pilot_source_arms": ["adaptive", "static10"],
        "required_probability": sizing["success_probability_required"],
        "root_seed": {
            "algorithm": "sha256",
            "digest": sizing["root_seed"],
            "encoding": "ascii",
            "preimage": sizing["root_seed_preimage"],
        },
        "search": {
            "method": "ascending-every-n-until-first-certification-pass",
            "pass_operator": ">=",
            "trials": sizing["search_trials"],
        },
        "seed_grammar": "paper-story-a1-headline-sizing-seed/v2",
        "selected_rule": "first-certification-pass-among-ascending-search-passing-candidates",
        "target_arm_mapping": target_arm_mapping,
    }


def _validate_failed_certificate(certificate: dict[str, Any]) -> None:
    _exact_object(
        certificate,
        {
            "canonical_json", "inputs", "model", "policy", "runtime",
            "schema_version", "status", "workloads",
        },
        "failed certificate",
    )
    _require_literal(
        certificate["canonical_json"], "utf8-sort-keys-compact-no-nonfinite-final-lf/v1",
        "failed certificate/canonical_json",
    )
    _require_literal(
        certificate["schema_version"], "paper-story-a1-headline-sizing-certificate/v1",
        "failed certificate/schema_version",
    )
    _require_literal(certificate["status"], "no-passing-n", "failed certificate/status")


def _validate_pilot_inputs(value: object, workload_names: tuple[str, ...]) -> None:
    inputs = _exact_object(value, {"pilot"}, "certificate/inputs")
    pilot = _exact_object(
        inputs["pilot"], {"ddof", "path", "planning", "proxy", "sha256", "source_arms"},
        "certificate/inputs/pilot",
    )
    _require_literal(pilot["ddof"], 1, "certificate/inputs/pilot/ddof")
    _require_string(pilot["path"], "certificate/inputs/pilot/path")
    _require_sha256(pilot["sha256"], "certificate/inputs/pilot/sha256")
    _require_literal(
        pilot["source_arms"], ["adaptive", "static10"],
        "certificate/inputs/pilot/source_arms",
    )
    proxy = _exact_object(
        pilot["proxy"],
        {
            "conditional_on_transferred_two-arm_variability", "target_arms_measured",
            "upper_bound_guarantee",
        },
        "certificate/inputs/pilot/proxy",
    )
    for key, expected in (
        ("conditional_on_transferred_two-arm_variability", True),
        ("target_arms_measured", False),
        ("upper_bound_guarantee", False),
    ):
        _require_literal(proxy[key], expected, f"certificate/inputs/pilot/proxy/{key}")
    planning = pilot["planning"]
    if type(planning) is not list or len(planning) != len(workload_names):
        raise HeadlineSpecError("certificate/inputs/pilot/planning has the wrong length")
    for index, raw_plan in enumerate(planning):
        path = f"certificate/inputs/pilot/planning/{index}"
        plan = _exact_object(
            raw_plan,
            {"arm_cvs", "inflation", "max_arm", "max_cv", "planned_cv", "workload"},
            path,
        )
        _require_literal(plan["workload"], workload_names[index], f"{path}/workload")
        for key in ("inflation", "max_arm", "max_cv", "planned_cv"):
            _require_string(plan[key], f"{path}/{key}")
        arm_cvs = plan["arm_cvs"]
        if type(arm_cvs) is not list or len(arm_cvs) != 2:
            raise HeadlineSpecError(f"{path}/arm_cvs must contain two arms")
        for arm_index, raw_arm in enumerate(arm_cvs):
            arm_path = f"{path}/arm_cvs/{arm_index}"
            arm = _exact_object(raw_arm, {"arm", "cv", "sample_count"}, arm_path)
            _require_string(arm["arm"], f"{arm_path}/arm")
            _require_string(arm["cv"], f"{arm_path}/cv")
            _require_int(arm["sample_count"], f"{arm_path}/sample_count", minimum=1)


def _validate_certificate(
    certificate: dict[str, Any], spec: dict[str, Any], workloads: tuple[WorkloadRule, ...]
) -> None:
    _exact_object(
        certificate,
        {
            "canonical_json", "inputs", "model", "policy", "runtime", "schema_version",
            "status", "study_generation", "workloads",
        },
        "certificate",
    )
    _require_literal(
        certificate["canonical_json"], "utf8-sort-keys-compact-no-nonfinite-final-lf/v1",
        "certificate/canonical_json",
    )
    _require_literal(
        certificate["schema_version"], "paper-story-a1-headline-sizing-certificate/v2",
        "certificate/schema_version",
    )
    _require_literal(certificate["status"], "selected", "certificate/status")
    _require_literal(
        certificate["study_generation"], spec["study_id"], "certificate/study_generation"
    )
    workload_names = tuple(row.name for row in workloads)
    _validate_pilot_inputs(certificate["inputs"], workload_names)
    runtime = _exact_object(certificate["runtime"], {"numpy", "python"}, "certificate/runtime")
    numpy_runtime = _exact_object(runtime["numpy"], {"version"}, "certificate/runtime/numpy")
    python_runtime = _exact_object(
        runtime["python"], {"implementation", "version"}, "certificate/runtime/python"
    )
    _require_string(numpy_runtime["version"], "certificate/runtime/numpy/version")
    _require_string(python_runtime["implementation"], "certificate/runtime/python/implementation")
    _require_string(python_runtime["version"], "certificate/runtime/python/version")

    expected_policy = _expected_certificate_policy(spec)
    _require_literal(certificate["policy"], expected_policy, "certificate/policy")
    expected_model_conditions = []
    for condition in expected_policy["conditions"]:
        delta = _fraction_rule(condition["delta"], "certificate/policy/conditions/delta")
        expected_model_conditions.append(
            {
                **condition,
                "variant_population_median": _fraction_object(1 + delta),
            }
        )
    expected_model = {
        "arm_independence": "independent-normal-iid",
        "baseline_population_median": {"denominator": 1, "numerator": 1},
        "conditions": expected_model_conditions,
        "equal_cv_within_workload": True,
        "estimand": "median-variant-over-median-baseline-minus-1",
        "even_n_sample_median": "arithmetic-mean-of-order-n-over-2-and-n-over-2-plus-1",
        "joint_order_algorithm": "joint-uniform-minimum-and-interval-order-statistics-beta-conditional/v2",
        "normal_inverse_algorithm": "acklam-inverse-normal-cdf/v1",
        "pilot_source_arms": ["adaptive", "static10"],
        "ratio_interval": "variant-lower-over-baseline-upper-to-variant-upper-over-baseline-lower",
        "rng_algorithm": "numpy-pcg64-generator-beta/v1",
        "simulated_arm_roles": {"baseline": "target-baseline", "variant": "target-variant"},
    }
    _require_literal(certificate["model"], expected_model, "certificate/model")

    rows = certificate["workloads"]
    if type(rows) is not list or len(rows) != len(workloads):
        raise HeadlineSpecError("certificate/workloads has the wrong length")
    if [row.get("workload") if type(row) is dict else None for row in rows] != list(workload_names):
        raise HeadlineSpecError("certificate workload order differs from the spec")
    search_trials = spec["sizing"]["search_trials"]
    certification_trials = spec["sizing"]["certification_trials"]
    condition_names = tuple(spec["sizing"]["conditions"])
    required_probability = _fraction_rule(
        spec["sizing"]["success_probability_required"],
        "/sizing/success_probability_required",
    )
    root_seed = spec["sizing"]["root_seed"]
    n_min = spec["sizing"]["n_min"]
    for index, (raw, workload) in enumerate(zip(rows, workloads)):
        row_path = f"certificate/workloads/{index}"
        row = _exact_object(
            raw,
            {
                "candidates", "certification_alpha_spending", "planned_cv", "selected",
                "status", "workload",
            },
            row_path,
        )
        _require_literal(row["workload"], workload.name, f"{row_path}/workload")
        _require_literal(row["status"], "selected", f"{row_path}/status")
        _require_string(row["planned_cv"], f"{row_path}/planned_cv")
        candidates = row["candidates"]
        if type(candidates) is not list or not candidates:
            raise HeadlineSpecError(f"{row_path}/candidates must be non-empty")
        selected = _exact_object(
            row["selected"],
            {
                "certification_attempt", "coverage", "lower_index_1based", "n",
                "upper_index_1based",
            },
            f"{row_path}/selected",
        )
        selected_n = _require_int(selected["n"], f"{row_path}/selected/n", minimum=1)
        expected_ns = list(range(n_min, selected_n + 1))
        observed_ns = [
            candidate.get("n") if type(candidate) is dict else None for candidate in candidates
        ]
        if observed_ns != expected_ns:
            raise HeadlineSpecError(f"{row_path}/candidates must be an ascending contiguous n range")
        certification_attempt = 0
        passing_candidate: dict[str, Any] | None = None
        for candidate_index, raw_candidate in enumerate(candidates):
            candidate_path = f"{row_path}/candidates/{candidate_index}"
            candidate = _exact_object(
                raw_candidate, {"certification", "n", "order_interval", "search"},
                candidate_path,
            )
            n = _require_int(candidate["n"], f"{candidate_path}/n", minimum=1)
            _validate_certificate_order_interval(
                candidate["order_interval"], f"{candidate_path}/order_interval"
            )
            search_passes = _validate_certificate_phase(
                candidate["search"], f"{candidate_path}/search",
                certification=False, attempt=None, condition_names=condition_names,
                trials=search_trials, required_probability=required_probability,
                root_seed=root_seed, workload=workload.name, n=n,
            )
            if (candidate["certification"] is not None) != search_passes:
                raise HeadlineSpecError(
                    f"{candidate_path}/certification must exist exactly when search passes"
                )
            if search_passes:
                certification_attempt += 1
                cert_passes = _validate_certificate_phase(
                    candidate["certification"], f"{candidate_path}/certification",
                    certification=True, attempt=certification_attempt,
                    condition_names=condition_names, trials=certification_trials,
                    required_probability=required_probability, root_seed=root_seed,
                    workload=workload.name, n=n,
                )
                if cert_passes:
                    if passing_candidate is not None:
                        raise HeadlineSpecError(f"{row_path} has multiple passing certifications")
                    passing_candidate = candidate
        if passing_candidate is not candidates[-1]:
            raise HeadlineSpecError(f"{row_path} does not stop at the first certification pass")
        selected_interval = passing_candidate["order_interval"]
        observed = (
            selected_n,
            _require_int(
                selected["lower_index_1based"], f"{row_path}/selected/lower_index_1based",
                minimum=1,
            ),
            _require_int(
                selected["upper_index_1based"], f"{row_path}/selected/upper_index_1based",
                minimum=1,
            ),
        )
        expected = (
            workload.repetitions_per_arm,
            workload.lower_index_1based,
            workload.upper_index_1based,
        )
        if observed != expected:
            raise HeadlineSpecError(
                f"certificate selected n/index differs for workload {workload.name!r}"
            )
        _require_literal(
            selected["coverage"], selected_interval["coverage"],
            f"{row_path}/selected/coverage",
        )
        _require_literal(
            selected["lower_index_1based"], selected_interval["lower_index_1based"],
            f"{row_path}/selected/lower_index_1based",
        )
        _require_literal(
            selected["upper_index_1based"], selected_interval["upper_index_1based"],
            f"{row_path}/selected/upper_index_1based",
        )
        _require_literal(
            selected["certification_attempt"], certification_attempt,
            f"{row_path}/selected/certification_attempt",
        )
        spent = Fraction(certification_attempt, 20 * (certification_attempt + 1))
        expected_spending = {
            "attempt_count": certification_attempt,
            "condition_count": 3,
            "family_alpha_cap": {"denominator": 20, "numerator": 1},
            "spent": _fraction_object(spent),
            "within_cap": True,
        }
        _require_literal(
            row["certification_alpha_spending"], expected_spending,
            f"{row_path}/certification_alpha_spending",
        )


def _validate_certificate_order_interval(value: object, path: str) -> None:
    interval = _exact_object(
        value, {"coverage", "lower_index_1based", "upper_index_1based"}, path
    )
    coverage = _exact_object(interval["coverage"], {"denominator", "numerator"}, f"{path}/coverage")
    _require_int(coverage["denominator"], f"{path}/coverage/denominator", minimum=1)
    _require_int(coverage["numerator"], f"{path}/coverage/numerator", minimum=1)
    _require_int(interval["lower_index_1based"], f"{path}/lower_index_1based", minimum=1)
    _require_int(interval["upper_index_1based"], f"{path}/upper_index_1based", minimum=1)


def _validate_certificate_outcomes(value: object, path: str) -> None:
    outcomes = _exact_object(
        value,
        {"bounded-within-floor", "invalid", "resolved-beyond-floor", "unresolved"},
        path,
    )
    for key in ("bounded-within-floor", "invalid", "unresolved"):
        _require_int(outcomes[key], f"{path}/{key}", minimum=0)
    resolved = _exact_object(
        outcomes["resolved-beyond-floor"], {"improvement", "regression"},
        f"{path}/resolved-beyond-floor",
    )
    for key in resolved:
        _require_int(resolved[key], f"{path}/resolved-beyond-floor/{key}", minimum=0)


def _validate_certificate_seed(value: object, path: str, expected_preimage: str) -> None:
    seed = _exact_object(value, {"digest", "preimage"}, path)
    digest = _require_sha256(seed["digest"], f"{path}/digest")
    _require_literal(seed["preimage"], expected_preimage, f"{path}/preimage")
    if hashlib.sha256(expected_preimage.encode("ascii")).hexdigest() != digest:
        raise HeadlineSpecError(f"{path}/digest differs from its preimage")


def _validate_certificate_phase(
    value: object,
    path: str,
    *,
    certification: bool,
    attempt: int | None,
    condition_names: tuple[str, ...],
    trials: int,
    required_probability: Fraction,
    root_seed: str,
    workload: str,
    n: int,
) -> bool:
    expected_phase_keys = {"conditions", "passes"}
    if certification:
        expected_phase_keys |= {"attempt", "condition_alpha"}
    phase = _exact_object(value, expected_phase_keys, path)
    phase_passes = _require_bool(phase["passes"], f"{path}/passes")
    expected_alpha: Fraction | None = None
    if certification:
        if attempt is None:
            raise AssertionError("certification attempt is absent")
        _require_literal(phase["attempt"], attempt, f"{path}/attempt")
        expected_alpha = Fraction(1, 60 * attempt * (attempt + 1))
        if _fraction_rule(phase["condition_alpha"], f"{path}/condition_alpha") != expected_alpha:
            raise HeadlineSpecError(f"{path}/condition_alpha differs from alpha spending")
    conditions = phase["conditions"]
    if type(conditions) is not list or len(conditions) != len(condition_names):
        raise HeadlineSpecError(f"{path}/conditions has the wrong length")
    expected_keys = {
        "condition", "invalid", "outcomes", "seed", "success", "trials"
    }
    if certification:
        expected_keys |= {"alpha", "lower_bound", "passes"}
    observed_condition_passes: list[bool] = []
    for index, raw_condition in enumerate(conditions):
        condition_path = f"{path}/conditions/{index}"
        condition = _exact_object(raw_condition, expected_keys, condition_path)
        condition_name = condition_names[index]
        _require_literal(condition["condition"], condition_name, f"{condition_path}/condition")
        invalid = _require_int(condition["invalid"], f"{condition_path}/invalid", minimum=0)
        success = _require_int(condition["success"], f"{condition_path}/success", minimum=0)
        _require_literal(condition["trials"], trials, f"{condition_path}/trials")
        _validate_certificate_outcomes(condition["outcomes"], f"{condition_path}/outcomes")
        outcomes = condition["outcomes"]
        resolved = outcomes["resolved-beyond-floor"]
        outcome_total = (
            outcomes["bounded-within-floor"] + outcomes["invalid"]
            + resolved["improvement"] + resolved["regression"] + outcomes["unresolved"]
        )
        if outcome_total != trials or invalid != outcomes["invalid"]:
            raise HeadlineSpecError(f"{condition_path} outcome accounting differs from trials")
        expected_success = (
            outcomes["bounded-within-floor"]
            if index == 0
            else resolved["improvement"] if index == 1 else resolved["regression"]
        )
        if success != expected_success:
            raise HeadlineSpecError(f"{condition_path}/success differs from its target outcome")
        phase_name = "certification" if certification else "search"
        preimage = (
            "paper-story-a1-headline-sizing-seed/v2"
            f"|root={root_seed}|phase={phase_name}|workload={workload}"
            f"|condition={condition_name}|n={n}|trials={trials}"
        )
        if certification:
            preimage += f"|attempt={attempt}"
        _validate_certificate_seed(condition["seed"], f"{condition_path}/seed", preimage)
        if certification:
            if _fraction_rule(condition["alpha"], f"{condition_path}/alpha") != expected_alpha:
                raise HeadlineSpecError(f"{condition_path}/alpha differs from alpha spending")
            lower_bound_text = _require_string(
                condition["lower_bound"], f"{condition_path}/lower_bound"
            )
            try:
                lower_bound = Fraction(lower_bound_text)
            except (ValueError, ZeroDivisionError) as exc:
                raise HeadlineSpecError(f"{condition_path}/lower_bound is not finite decimal") from exc
            if not 0 <= lower_bound <= 1:
                raise HeadlineSpecError(f"{condition_path}/lower_bound is outside [0, 1]")
            condition_passes = _require_bool(condition["passes"], f"{condition_path}/passes")
            if condition_passes != (lower_bound >= required_probability):
                raise HeadlineSpecError(f"{condition_path}/passes differs from its lower bound")
        else:
            condition_passes = (
                success * required_probability.denominator
                >= trials * required_probability.numerator
            )
        observed_condition_passes.append(condition_passes)
    if phase_passes != all(observed_condition_passes):
        raise HeadlineSpecError(f"{path}/passes differs from its conditions")
    return phase_passes


def _validate_replay_receipt(
    receipt: dict[str, Any],
    spec: dict[str, Any],
    certificate: dict[str, Any],
    certificate_digest: str,
) -> None:
    _exact_object(
        receipt,
        {
            "canonical_json", "certificate", "pilot", "policy", "runtime",
            "schema_version", "sources", "verification",
        },
        "receipt",
    )
    _require_literal(
        receipt["canonical_json"],
        "utf8-sort-keys-compact-no-nonfinite-final-lf/v1",
        "receipt/canonical_json",
    )
    _require_literal(
        receipt["schema_version"],
        "paper-story-a1-headline-sizing-replay-receipt/v1",
        "receipt/schema_version",
    )

    verification = _exact_object(
        receipt["verification"], {"return_code", "status"}, "receipt/verification"
    )
    _require_literal(verification["status"], "verified", "receipt/verification/status")
    _require_literal(verification["return_code"], 0, "receipt/verification/return_code")

    receipt_certificate = _exact_object(
        receipt["certificate"], {"path", "sha256"}, "receipt/certificate"
    )
    _require_literal(
        receipt_certificate["path"], SIZING_CERTIFICATE_PATH,
        "receipt/certificate/path",
    )
    _require_literal(
        _require_sha256(receipt_certificate["sha256"], "receipt/certificate/sha256"),
        certificate_digest,
        "receipt/certificate/sha256",
    )

    certificate_pilot = certificate["inputs"]["pilot"]
    receipt_pilot = _exact_object(
        receipt["pilot"], {"path", "sha256"}, "receipt/pilot"
    )
    _require_literal(
        receipt_pilot["path"], certificate_pilot["path"], "receipt/pilot/path"
    )
    _require_literal(
        _require_sha256(receipt_pilot["sha256"], "receipt/pilot/sha256"),
        certificate_pilot["sha256"],
        "receipt/pilot/sha256",
    )

    sources = _exact_object(
        receipt["sources"], {"generator", "verifier"}, "receipt/sources"
    )
    for key, expected_path, expected_digest in (
        (
            "generator", SIZING_GENERATOR_SOURCE_PATH,
            SIZING_GENERATOR_SOURCE_SHA256,
        ),
        (
            "verifier", SIZING_VERIFIER_SOURCE_PATH,
            SIZING_VERIFIER_SOURCE_SHA256,
        ),
    ):
        source = _exact_object(
            sources[key], {"path", "sha256"}, f"receipt/sources/{key}"
        )
        _require_literal(source["path"], expected_path, f"receipt/sources/{key}/path")
        _require_literal(
            _require_sha256(source["sha256"], f"receipt/sources/{key}/sha256"),
            expected_digest,
            f"receipt/sources/{key}/sha256",
        )

    runtime = _exact_object(receipt["runtime"], {"numpy", "python"}, "receipt/runtime")
    numpy_runtime = _exact_object(runtime["numpy"], {"version"}, "receipt/runtime/numpy")
    python_runtime = _exact_object(
        runtime["python"], {"implementation", "version"}, "receipt/runtime/python"
    )
    _require_string(numpy_runtime["version"], "receipt/runtime/numpy/version")
    _require_string(python_runtime["implementation"], "receipt/runtime/python/implementation")
    _require_string(python_runtime["version"], "receipt/runtime/python/version")
    _require_literal(runtime, certificate["runtime"], "receipt/runtime")

    sizing = spec["sizing"]
    expected_policy = {
        "certification_trials": sizing["certification_trials"],
        "n_range": {
            "maximum": sizing["n_max"],
            "minimum": sizing["n_min"],
            "step": 1,
        },
        "root_seed": {
            "algorithm": "sha256",
            "digest": sizing["root_seed"],
            "encoding": "ascii",
            "preimage": sizing["root_seed_preimage"],
        },
        "search_trials": sizing["search_trials"],
    }
    policy = _exact_object(
        receipt["policy"],
        {"certification_trials", "n_range", "root_seed", "search_trials"},
        "receipt/policy",
    )
    _require_literal(policy, expected_policy, "receipt/policy")
    certificate_policy = certificate["policy"]
    _require_literal(
        policy["certification_trials"], certificate_policy["certification"]["trials"],
        "receipt/policy/certification_trials",
    )
    _require_literal(
        policy["search_trials"], certificate_policy["search"]["trials"],
        "receipt/policy/search_trials",
    )
    _require_literal(policy["n_range"], certificate_policy["n_range"], "receipt/policy/n_range")
    _require_literal(
        policy["root_seed"], certificate_policy["root_seed"], "receipt/policy/root_seed"
    )


def _parse_bound_spec_body(
    canonical_document_path: str,
    canonical_document_bytes: bytes,
    mirror_policy_path: str,
    mirror_policy_bytes: bytes,
    failed_sizing_certificate_path: str,
    failed_sizing_certificate_bytes: bytes,
    sizing_certificate_path: str,
    sizing_certificate_bytes: bytes,
    sizing_replay_receipt_path: str,
    sizing_replay_receipt_bytes: bytes,
    construct: Callable[..., BoundSpec],
) -> BoundSpec:
    for observed, expected, label in (
        (canonical_document_path, CANONICAL_DOCUMENT_PATH, "canonical document path"),
        (mirror_policy_path, MIRROR_POLICY_PATH, "mirror policy path"),
        (
            failed_sizing_certificate_path,
            FAILED_SIZING_CERTIFICATE_PATH,
            "failed sizing certificate path",
        ),
        (sizing_certificate_path, SIZING_CERTIFICATE_PATH, "sizing certificate path"),
        (
            sizing_replay_receipt_path,
            SIZING_REPLAY_RECEIPT_PATH,
            "sizing replay receipt path",
        ),
    ):
        if type(observed) is not str or observed != expected:
            raise HeadlineSpecError(f"{label} differs from the canonical path")

    raw_spec, spec = _extract_embedded_spec(canonical_document_bytes)
    mirror = _parse_json_object(mirror_policy_bytes, MIRROR_POLICY_PATH)
    if mirror_policy_bytes != _canonical_indent_bytes(mirror):
        raise HeadlineSpecError("mirror policy is not canonical indent-2 sorted-key JSON")
    mirror = _exact_object(
        mirror,
        {
            "canonical_document_path", "canonical_document_sha256",
            "failed_sizing_certificate_path", "failed_sizing_certificate_sha256",
            "mirror_policy_path", "raw_embedded_spec_sha256", "sizing_certificate_path",
            "sizing_certificate_sha256", "sizing_replay_receipt_path",
            "sizing_replay_receipt_sha256", "spec_mirror",
        },
        "mirror",
    )
    _require_literal(mirror["canonical_document_path"], CANONICAL_DOCUMENT_PATH, "mirror/canonical_document_path")
    _require_literal(mirror["mirror_policy_path"], MIRROR_POLICY_PATH, "mirror/mirror_policy_path")
    _require_literal(
        mirror["failed_sizing_certificate_path"], FAILED_SIZING_CERTIFICATE_PATH,
        "mirror/failed_sizing_certificate_path",
    )
    _require_literal(mirror["sizing_certificate_path"], SIZING_CERTIFICATE_PATH, "mirror/sizing_certificate_path")
    _require_literal(
        mirror["sizing_replay_receipt_path"], SIZING_REPLAY_RECEIPT_PATH,
        "mirror/sizing_replay_receipt_path",
    )
    document_digest = hashlib.sha256(canonical_document_bytes).hexdigest()
    raw_spec_digest = hashlib.sha256(raw_spec).hexdigest()
    if _require_sha256(mirror["canonical_document_sha256"], "mirror/canonical_document_sha256") != document_digest:
        raise HeadlineSpecError("README SHA-256 differs from the mirror envelope")
    if _require_sha256(mirror["raw_embedded_spec_sha256"], "mirror/raw_embedded_spec_sha256") != raw_spec_digest:
        raise HeadlineSpecError("raw embedded spec SHA-256 differs from the mirror envelope")
    spec_mirror = mirror["spec_mirror"]
    if type(spec_mirror) is not dict:
        raise HeadlineSpecError("mirror/spec_mirror must be an object")
    if _canonical_indent_bytes(spec_mirror) != raw_spec:
        raise HeadlineSpecError("README and mirror raw spec bytes differ")

    (
        workloads,
        expected_failed_digest,
        expected_certificate_digest,
        expected_receipt_digest,
    ) = _validate_spec(spec)
    if type(failed_sizing_certificate_bytes) is not bytes:
        raise HeadlineSpecError("failed sizing certificate bytes must have exact type bytes")
    failed_certificate_digest = hashlib.sha256(failed_sizing_certificate_bytes).hexdigest()
    mirror_failed_digest = _require_sha256(
        mirror["failed_sizing_certificate_sha256"],
        "mirror/failed_sizing_certificate_sha256",
    )
    if failed_certificate_digest != expected_failed_digest or mirror_failed_digest != expected_failed_digest:
        raise HeadlineSpecError("failed sizing certificate SHA-256 differs from the bound artifacts")
    failed_certificate = _parse_json_object(
        failed_sizing_certificate_bytes, FAILED_SIZING_CERTIFICATE_PATH
    )
    if failed_sizing_certificate_bytes != _canonical_compact_bytes(failed_certificate):
        raise HeadlineSpecError("failed sizing certificate is not canonical compact JSON")
    _validate_failed_certificate(failed_certificate)

    if type(sizing_certificate_bytes) is not bytes:
        raise HeadlineSpecError("sizing certificate bytes must have exact type bytes")
    certificate_digest = hashlib.sha256(sizing_certificate_bytes).hexdigest()
    mirror_certificate_digest = _require_sha256(
        mirror["sizing_certificate_sha256"], "mirror/sizing_certificate_sha256"
    )
    if (
        certificate_digest != expected_certificate_digest
        or mirror_certificate_digest != expected_certificate_digest
    ):
        raise HeadlineSpecError("sizing certificate SHA-256 differs from the bound artifacts")
    certificate = _parse_json_object(sizing_certificate_bytes, SIZING_CERTIFICATE_PATH)
    if sizing_certificate_bytes != _canonical_compact_bytes(certificate):
        raise HeadlineSpecError("sizing certificate is not canonical compact JSON")
    _validate_certificate(certificate, spec, workloads)

    if type(sizing_replay_receipt_bytes) is not bytes:
        raise HeadlineSpecError("sizing replay receipt bytes must have exact type bytes")
    receipt_digest = hashlib.sha256(sizing_replay_receipt_bytes).hexdigest()
    mirror_receipt_digest = _require_sha256(
        mirror["sizing_replay_receipt_sha256"],
        "mirror/sizing_replay_receipt_sha256",
    )
    if receipt_digest != expected_receipt_digest or mirror_receipt_digest != expected_receipt_digest:
        raise HeadlineSpecError("sizing replay receipt SHA-256 differs from the bound artifacts")
    receipt = _parse_json_object(sizing_replay_receipt_bytes, SIZING_REPLAY_RECEIPT_PATH)
    if sizing_replay_receipt_bytes != _canonical_compact_bytes(receipt):
        raise HeadlineSpecError("sizing replay receipt is not canonical compact JSON")
    _validate_replay_receipt(receipt, spec, certificate, certificate_digest)

    frozen = _freeze(spec)
    if not isinstance(frozen, FrozenObject):  # pragma: no cover - construction invariant
        raise AssertionError("frozen spec root is not an object")
    return construct(
        canonical_document_path,
        mirror_policy_path,
        failed_sizing_certificate_path,
        sizing_certificate_path,
        sizing_replay_receipt_path,
        document_digest,
        raw_spec_digest,
        failed_certificate_digest,
        certificate_digest,
        receipt_digest,
        frozen,
        workloads,
    )


def _make_bound_spec_apis() -> tuple[
    Callable[..., BoundSpec],
    Callable[[object], _BoundSpecSnapshot | None],
]:
    registry: dict[int, tuple[BoundSpec, _BoundSpecSnapshot]] = {}

    def construct(*values: object) -> BoundSpec:
        field_names = (
            "canonical_document_path", "mirror_policy_path",
            "failed_sizing_certificate_path", "sizing_certificate_path",
            "sizing_replay_receipt_path",
            "document_sha256", "raw_spec_sha256", "failed_sizing_certificate_sha256",
            "sizing_certificate_sha256", "sizing_replay_receipt_sha256",
            "spec", "workloads",
        )
        if len(values) != len(field_names):  # pragma: no cover - internal invariant
            raise AssertionError("BoundSpec construction arity differs")
        bound = object.__new__(BoundSpec)
        for field_name, value in zip(field_names, values):
            object.__setattr__(bound, field_name, value)
        spec = _copy_frozen(values[10])
        if not isinstance(spec, FrozenObject):  # pragma: no cover - construction invariant
            raise AssertionError("snapshot spec root is not an object")
        workloads = tuple(
            WorkloadRule(
                row.name,
                row.repetitions_per_arm,
                row.lower_index_1based,
                row.upper_index_1based,
            )
            for row in values[11]
        )
        snapshot = _BoundSpecSnapshot(
            values[0], values[1], values[2], values[3], values[4], values[5],
            values[6], values[7], values[8], values[9], spec, workloads,
        )
        registry[id(bound)] = (bound, snapshot)
        return bound

    def parse_bound_spec(
        canonical_document_path: str,
        canonical_document_bytes: bytes,
        mirror_policy_path: str,
        mirror_policy_bytes: bytes,
        failed_sizing_certificate_path: str,
        failed_sizing_certificate_bytes: bytes,
        sizing_certificate_path: str,
        sizing_certificate_bytes: bytes,
        sizing_replay_receipt_path: str,
        sizing_replay_receipt_bytes: bytes,
    ) -> BoundSpec:
        """Verify five caller-supplied path/bytes pairs and seal an immutable spec.

        This is a pair-consistency verifier, not a filesystem authority loader.  It
        deliberately cannot prove where the caller obtained the supplied bytes.
        """

        return _parse_bound_spec_body(
            canonical_document_path,
            canonical_document_bytes,
            mirror_policy_path,
            mirror_policy_bytes,
            failed_sizing_certificate_path,
            failed_sizing_certificate_bytes,
            sizing_certificate_path,
            sizing_certificate_bytes,
            sizing_replay_receipt_path,
            sizing_replay_receipt_bytes,
            construct,
        )

    def parser_bound_snapshot(value: object) -> _BoundSpecSnapshot | None:
        registered = registry.get(id(value))
        if type(value) is not BoundSpec or registered is None or registered[0] is not value:
            return None
        return _copy_bound_spec_snapshot(registered[1])

    return parse_bound_spec, parser_bound_snapshot


parse_bound_spec, _parser_bound_spec_snapshot = _make_bound_spec_apis()
del _make_bound_spec_apis


def _sample_median(values: list[Fraction], rule: str) -> Fraction:
    if rule != "arithmetic-mean-of-two-central-order-statistics":
        raise HeadlineSpecError("bound even-sample median rule is unsupported")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _comparison(left: Fraction, operator: str, right: Fraction) -> bool:
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    raise HeadlineSpecError(f"bound comparison operator is unsupported: {operator!r}")


def _ratio_comparison(
    numerator: Fraction,
    denominator: Fraction,
    operator: str,
    boundary: Fraction,
) -> bool:
    """Compare a raw ratio to an exact fraction without float arithmetic."""

    left = numerator * boundary.denominator
    right = denominator * boundary.numerator
    return _comparison(left, operator, right)


def _validated_sample(values: object, n: int, label: str) -> list[Fraction]:
    if isinstance(values, (str, bytes, bytearray, Mapping)) or not isinstance(values, Sequence):
        raise HeadlineSpecError(f"{label} must be a sized numeric sequence")
    if len(values) != n:
        raise HeadlineSpecError(f"{label} length differs from the bound exact n")
    accepted: list[Fraction] = []
    for index, value in enumerate(values):
        if type(value) not in (int, float):
            raise HeadlineSpecError(
                f"{label}[{index}] requires exact int or float without coercion; bool is rejected"
            )
        if type(value) is float and not math.isfinite(value):
            raise HeadlineSpecError(f"{label}[{index}] is not finite")
        if value <= 0:
            raise HeadlineSpecError(f"{label}[{index}] is not positive")
        accepted.append(Fraction(value))
    return accepted


def _finite_float(value: Fraction, label: str, *, positive: bool = False) -> float:
    try:
        rendered = float(value)
    except (OverflowError, ValueError) as exc:
        raise HeadlineSpecError(f"{label} cannot be represented as a finite float") from exc
    if not math.isfinite(rendered) or (positive and rendered <= 0):
        raise HeadlineSpecError(f"{label} cannot be represented as a finite positive float")
    if rendered == 0.0 and value != 0:
        raise HeadlineSpecError(f"{label} exact nonzero value underflows a finite float")
    return rendered


def _public_median(value: Fraction, label: str) -> int | float | Fraction:
    if value.denominator == 1:
        return value.numerator
    try:
        rendered = float(value)
    except (OverflowError, ValueError):
        return value
    if math.isfinite(rendered):
        return rendered
    if value <= 0:  # pragma: no cover - positive samples make this unreachable
        raise HeadlineSpecError(f"{label} is not positive")
    return value


def median_ratio_statistics(
    bound_spec: BoundSpec,
    workload_name: str,
    baseline: Sequence[int | float],
    variant: Sequence[int | float],
) -> dict[str, object]:
    """Compute the preregistered point, rectangle interval, and 3-way decision."""

    snapshot = _parser_bound_spec_snapshot(bound_spec)
    if snapshot is None:
        raise HeadlineSpecError("bound_spec must be the parser-produced BoundSpec")
    if type(workload_name) is not str:
        raise HeadlineSpecError("workload_name must be an exact string")
    matches = tuple(row for row in snapshot.workloads if row.name == workload_name)
    if len(matches) != 1:
        raise HeadlineSpecError("workload_name is not uniquely present in BoundSpec")
    workload = matches[0]
    baseline_values = _validated_sample(baseline, workload.repetitions_per_arm, "baseline")
    variant_values = _validated_sample(variant, workload.repetitions_per_arm, "variant")

    analysis = snapshot.spec["analysis"]
    if not isinstance(analysis, FrozenObject):  # pragma: no cover - frozen schema invariant
        raise AssertionError("analysis projection is not frozen")
    estimand = analysis["estimand"]
    interval_rule = analysis["interval"]
    floor = analysis["floor"]
    classification = analysis["classification"]
    if not all(isinstance(value, FrozenObject) for value in (estimand, interval_rule, floor, classification)):
        raise AssertionError("analysis rule projection is not frozen")
    if estimand["point_formula"] != "median(variant_tps)/median(baseline_tps)-1":
        raise HeadlineSpecError("bound point formula is unsupported")
    if interval_rule["method"] != "exact-binomial-order-statistic-median-rectangle-ratio":
        raise HeadlineSpecError("bound interval method is unsupported")

    baseline_ordered = sorted(baseline_values)
    variant_ordered = sorted(variant_values)
    median_rule = estimand["even_sample_median"]
    if type(median_rule) is not str:
        raise AssertionError("median rule is not a string")
    baseline_median = _sample_median(baseline_ordered, median_rule)
    variant_median = _sample_median(variant_ordered, median_rule)
    ratio_exact = variant_median / baseline_median
    point_effect_exact = ratio_exact - 1

    lower_index = workload.lower_index_1based - 1
    upper_index = workload.upper_index_1based - 1
    ratio_lower_exact = variant_ordered[lower_index] / baseline_ordered[upper_index]
    ratio_upper_exact = variant_ordered[upper_index] / baseline_ordered[lower_index]
    if not (0 < ratio_lower_exact <= ratio_upper_exact):
        raise HeadlineSpecError("rectangle ratio interval is not positive and ordered")

    band_lower_rule = floor["band_lower"]
    band_upper_rule = floor["band_upper"]
    if not isinstance(band_lower_rule, FrozenObject) or not isinstance(band_upper_rule, FrozenObject):
        raise AssertionError("floor fractions are not frozen objects")
    band_lower = Fraction(band_lower_rule["numerator"], band_lower_rule["denominator"])
    band_upper = Fraction(band_upper_rule["numerator"], band_upper_rule["denominator"])
    resolved = classification["resolved"]
    bounded = classification["bounded"]
    if not isinstance(resolved, FrozenObject) or not isinstance(bounded, FrozenObject):
        raise AssertionError("classification branches are not frozen objects")

    regression = _ratio_comparison(
        variant_ordered[upper_index], baseline_ordered[lower_index],
        resolved["upper_operator"], band_lower,
    )
    improvement = _ratio_comparison(
        variant_ordered[lower_index], baseline_ordered[upper_index],
        resolved["lower_operator"], band_upper,
    )
    within_lower = _ratio_comparison(
        variant_ordered[lower_index], baseline_ordered[upper_index],
        bounded["lower_operator"], band_lower,
    )
    within_upper = _ratio_comparison(
        variant_ordered[upper_index], baseline_ordered[lower_index],
        bounded["upper_operator"], band_upper,
    )
    if regression or improvement:
        decision = resolved["label"]
        direction = (
            resolved["direction_negative"] if regression
            else resolved["direction_positive"]
        )
    elif within_lower and within_upper:
        decision = bounded["label"]
        direction = None
    else:
        decision = classification["otherwise"]
        direction = None

    _finite_float(ratio_exact, "point ratio", positive=True)
    point_effect = _finite_float(point_effect_exact, "point effect")
    ratio_lower = _finite_float(ratio_lower_exact, "ratio interval lower", positive=True)
    ratio_upper = _finite_float(ratio_upper_exact, "ratio interval upper", positive=True)
    effect_lower = _finite_float(ratio_lower_exact - 1, "effect interval lower")
    effect_upper = _finite_float(ratio_upper_exact - 1, "effect interval upper")

    return {
        "baseline_median": _public_median(baseline_median, "baseline median"),
        "classification": decision,
        "direction": direction,
        "effect_interval": (effect_lower, effect_upper),
        "interval_indices_1based": (
            workload.lower_index_1based,
            workload.upper_index_1based,
        ),
        "n": workload.repetitions_per_arm,
        "point_effect": point_effect,
        "ratio_interval": (ratio_lower, ratio_upper),
        "variant_median": _public_median(variant_median, "variant median"),
        "workload": workload.name,
    }
