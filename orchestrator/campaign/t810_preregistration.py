"""T-810 凍結事前登録 artifact の fail-closed loader。"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


PREREG_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "pegasus"
    / "policies"
    / "t810_prereg_v1.json"
)
PREREG_SCHEMA_VERSION = "pegasus-t810-preregistration/v1"
APPROVAL_RECEIPT_SCHEMA_VERSION = "pegasus-t810-approval-receipt/v1"
ENVIRONMENT_CONTRACT_SHA256 = (
    "1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c"
)


class T810PreregistrationError(ValueError):
    """artifact、canonical bytes、または承認 receipt が不正である。"""


class T810NotAuthorizedError(PermissionError):
    """dormant seal が T-810 の起動を拒否した。"""


@dataclass(frozen=True)
class ApprovalReceipt:
    artifact_sha256: str
    approval_id: str
    schema_version: str


_VERIFIED_CONSTRUCTION_TOKEN = object()


@dataclass(frozen=True, init=False)
class VerifiedT810Preregistration:
    sha256: str
    approval_id: str
    projection: Mapping[str, Any]

    def __init__(
        self,
        sha256: str,
        approval_id: str,
        projection: Mapping[str, Any],
        *,
        _loader_token: object | None = None,
    ) -> None:
        if _loader_token is not _VERIFIED_CONSTRUCTION_TOKEN:
            raise T810PreregistrationError(
                "VerifiedT810Preregistration can only be constructed by the loader"
            )
        object.__setattr__(self, "sha256", sha256)
        object.__setattr__(self, "approval_id", approval_id)
        object.__setattr__(self, "projection", projection)

    @property
    def run_authorized(self) -> bool:
        return bool(self.projection["protocol"]["run_authorized"])

    def effective_node_count(self, terminal_state: str) -> int:
        states = self.projection["design"]["effective_states"]
        if terminal_state not in states:
            raise T810PreregistrationError(
                "no primary estimator is defined for " + repr(terminal_state)
            )
        return int(states[terminal_state]["effective_node_count"])


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise T810PreregistrationError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_float(token: str) -> None:
    raise T810PreregistrationError(
        f"JSON floating-point numbers are forbidden; use a decimal string: {token!r}"
    )


def _parse_integer(token: str) -> int:
    if token == "-0":
        raise T810PreregistrationError("negative zero is forbidden")
    return int(token)


def _parse_json(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise T810PreregistrationError("UTF-8 BOM is forbidden")
    if b"\r" in raw:
        raise T810PreregistrationError("only LF newlines are accepted")
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise T810PreregistrationError("artifact must end in exactly one LF")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise T810PreregistrationError("artifact is not strict UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_float,
            parse_int=_parse_integer,
            parse_constant=_reject_float,
        )
    except json.JSONDecodeError as exc:
        raise T810PreregistrationError("artifact is not valid JSON") from exc
    if not isinstance(value, dict):
        raise T810PreregistrationError("artifact root must be an object")
    return value


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ": "),
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _normalise_receipt(receipt: ApprovalReceipt | Mapping[str, Any]) -> ApprovalReceipt:
    if isinstance(receipt, ApprovalReceipt):
        normalized = receipt
    elif isinstance(receipt, Mapping):
        expected_keys = {"artifact_sha256", "approval_id", "schema_version"}
        if set(receipt) != expected_keys:
            raise T810PreregistrationError(
                "approval receipt must have exactly artifact_sha256, approval_id, schema_version"
            )
        normalized = ApprovalReceipt(
            artifact_sha256=receipt["artifact_sha256"],
            approval_id=receipt["approval_id"],
            schema_version=receipt["schema_version"],
        )
    else:
        raise T810PreregistrationError("approval_receipt must be a receipt mapping")
    if normalized.schema_version != APPROVAL_RECEIPT_SCHEMA_VERSION:
        raise T810PreregistrationError("approval receipt schema version mismatch")
    if not isinstance(normalized.approval_id, str) or not normalized.approval_id:
        raise T810PreregistrationError("approval_id must be a non-empty string")
    digest = normalized.artifact_sha256
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise T810PreregistrationError("artifact_sha256 must be 64 lowercase hex digits")
    return normalized


def _verify_approval_digest(
    *, raw: bytes, canonical: bytes, receipt: ApprovalReceipt
) -> str:
    """raw bytes を外部 authority と照合する。

    ``canonical`` は raw/canonical の取り違えを狙う変異を単体で検査できるよう明示的に
    受け取るが、digest 入力には決して使わない。
    """

    del canonical
    actual = hashlib.sha256(raw).hexdigest()
    if actual != receipt.artifact_sha256:
        raise T810PreregistrationError("artifact digest does not match approval receipt")
    return actual


def _exact_keys(value: Any, expected: set[str], path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise T810PreregistrationError(f"{path} must be an object")
    if set(value) != expected:
        raise T810PreregistrationError(f"{path} has an unknown or missing field")
    return value


def _expect(value: Mapping[str, Any], key: str, expected: Any, path: str) -> None:
    if value.get(key) != expected or type(value.get(key)) is not type(expected):
        raise T810PreregistrationError(f"{path}/{key} does not match the frozen literal")


def _validate_exact_literal(value: Any, expected: Any, path: str) -> None:
    """object/list の全枝を exact schema と exact literal で閉じる。"""

    if type(value) is not type(expected):
        raise T810PreregistrationError(f"{path} has the wrong frozen type")
    if isinstance(expected, dict):
        if set(value) != set(expected):
            raise T810PreregistrationError(f"{path} has an unknown or missing field")
        for key, expected_child in expected.items():
            _validate_exact_literal(value[key], expected_child, f"{path}/{key}")
        return
    if isinstance(expected, list):
        if len(value) != len(expected):
            raise T810PreregistrationError(f"{path} has the wrong frozen length")
        for index, (child, expected_child) in enumerate(zip(value, expected)):
            _validate_exact_literal(child, expected_child, f"{path}/{index}")
        return
    if value != expected:
        raise T810PreregistrationError(f"{path} does not match the frozen literal")


def _validate_binary64_hex(value: Any, path: str) -> None:
    if not isinstance(value, str):
        raise T810PreregistrationError(f"{path} must be a binary64 hex string")
    try:
        parsed = float.fromhex(value)
    except ValueError as exc:
        raise T810PreregistrationError(f"{path} is not binary64 hex") from exc
    if not isfinite(parsed) or parsed.hex() != value:
        raise T810PreregistrationError(f"{path} is not canonical binary64 hex")


def _validate_decimal_string(value: Any, path: str) -> None:
    if not isinstance(value, str):
        raise T810PreregistrationError(f"{path} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise T810PreregistrationError(f"{path} is not a decimal string") from exc
    if not parsed.is_finite():
        raise T810PreregistrationError(f"{path} must be finite")


def _validate_golden_vectors(value: Any) -> None:
    if not isinstance(value, list):
        raise T810PreregistrationError("/golden_vectors must be an array")
    expected_states = {
        "selected_n13_normal": "valid",
        "reduced_n12_normal": "terminal_reduced",
        "upper_truncated_to_zero": "valid",
        "upper_equality_boundary": "valid",
        "lower_equality_boundary": "valid",
        "slope_gate_fires": "terminal_reduced",
        "slope_gate_strict_boundary": "valid",
    }
    expected_kinds = {
        "selected_n13_normal": "centered-linear-grid",
        "reduced_n12_normal": "centered-linear-grid",
        "upper_truncated_to_zero": "negative-variance-grid",
        "upper_equality_boundary": "centered-linear-grid",
        "lower_equality_boundary": "centered-linear-grid",
        "slope_gate_fires": "centered-linear-grid",
        "slope_gate_strict_boundary": "slope-gate-equality-grid",
    }
    ids = [vector.get("id") if isinstance(vector, dict) else None for vector in value]
    if len(ids) != len(expected_states) or set(ids) != set(expected_states):
        raise T810PreregistrationError("golden vector IDs are not the frozen closed set")
    expected_extras = {
        "upper_equality_boundary": {"boundary"},
        "lower_equality_boundary": {"boundary"},
        "slope_gate_strict_boundary": {"slope_relation"},
    }
    for index, vector_value in enumerate(value):
        path = f"/golden_vectors/{index}"
        vector = _exact_keys(
            vector_value, {"expected", "generation", "id", "terminal_state"}, path
        )
        vector_id = vector["id"]
        _expect(vector, "terminal_state", expected_states[vector_id], path)
        generation = vector["generation"]
        if not isinstance(generation, dict) or not isinstance(generation.get("kind"), str):
            raise T810PreregistrationError(f"{path}/generation is malformed")
        kind = generation["kind"]
        if kind != expected_kinds[vector_id]:
            raise T810PreregistrationError(
                f"{path}/generation kind does not match the frozen vector ID"
            )
        if kind in {"centered-linear-grid", "constant-zero-grid"}:
            generation_keys = {"kind", "node_step", "round_step", "slope_step"}
        elif kind == "negative-variance-grid":
            generation_keys = {"kind", "quadratic_residual_amplitude"}
        elif kind == "slope-gate-equality-grid":
            generation_keys = {
                "kind",
                "node_intercept_step",
                "quadratic_residual_amplitude",
            }
        else:
            raise T810PreregistrationError(f"{path}/generation kind is not frozen")
        _exact_keys(generation, generation_keys, f"{path}/generation")
        if any(not isinstance(item, str) for item in generation.values()):
            raise T810PreregistrationError(f"{path}/generation fields must be strings")
        for key in generation_keys - {"kind"}:
            _validate_decimal_string(generation[key], f"{path}/generation/{key}")

        expected = vector["expected"]
        expected_keys = {
            "conclusion_code",
            "slope_gate_fired",
            "tau_L",
            "tau_U",
            "tau_hat",
        } | expected_extras.get(vector_id, set())
        _exact_keys(expected, expected_keys, f"{path}/expected")
        if type(expected["slope_gate_fired"]) is not bool:
            raise T810PreregistrationError(
                f"{path}/expected/slope_gate_fired must be boolean"
            )
        for key in expected_keys - {"slope_gate_fired"}:
            if not isinstance(expected[key], str):
                raise T810PreregistrationError(f"{path}/expected/{key} must be a string")
        for key in {"tau_L", "tau_U", "tau_hat"}:
            _validate_decimal_string(expected[key], f"{path}/expected/{key}")


def _validate_scalar_golden_vectors(value: Any) -> None:
    if not isinstance(value, list):
        raise T810PreregistrationError("/scalar_golden_vectors must be an array")
    expected_operations = {
        "upper_exact_scalar_equality": "conclusion_code",
        "lower_exact_scalar_equality": "conclusion_code",
        "slope_exact_scalar_equality": "slope_gate_fires",
    }
    ids = [vector.get("id") if isinstance(vector, dict) else None for vector in value]
    if len(ids) != len(expected_operations) or set(ids) != set(expected_operations):
        raise T810PreregistrationError(
            "scalar golden vector IDs are not the frozen closed set"
        )
    for index, vector_value in enumerate(value):
        path = f"/scalar_golden_vectors/{index}"
        vector = _exact_keys(
            vector_value, {"expected", "id", "input", "operation"}, path
        )
        vector_id = vector["id"]
        operation = expected_operations[vector_id]
        _expect(vector, "operation", operation, path)
        if operation == "conclusion_code":
            inputs = _exact_keys(
                vector["input"],
                {
                    "slope_gate_fired",
                    "tau_l_binary64_hex",
                    "tau_star_binary64_hex",
                    "tau_u_binary64_hex",
                    "terminal_state",
                },
                f"{path}/input",
            )
            if type(inputs["slope_gate_fired"]) is not bool:
                raise T810PreregistrationError(
                    f"{path}/input/slope_gate_fired must be boolean"
                )
            _expect(inputs, "terminal_state", "valid", f"{path}/input")
            for key in (
                "tau_l_binary64_hex",
                "tau_star_binary64_hex",
                "tau_u_binary64_hex",
            ):
                _validate_binary64_hex(inputs[key], f"{path}/input/{key}")
            if vector_id == "upper_exact_scalar_equality" and (
                inputs["tau_u_binary64_hex"] != inputs["tau_star_binary64_hex"]
            ):
                raise T810PreregistrationError(
                    f"{path}/input does not encode exact tau_U equality"
                )
            if vector_id == "lower_exact_scalar_equality" and (
                inputs["tau_l_binary64_hex"] != inputs["tau_star_binary64_hex"]
            ):
                raise T810PreregistrationError(
                    f"{path}/input does not encode exact tau_L equality"
                )
            expected = _exact_keys(
                vector["expected"], {"conclusion_code"}, f"{path}/expected"
            )
            _expect(expected, "conclusion_code", "underdetermined", f"{path}/expected")
        else:
            inputs = _exact_keys(
                vector["input"],
                {"s_beta_binary64_hex", "v_beta_binary64_hex"},
                f"{path}/input",
            )
            for key in inputs:
                _validate_binary64_hex(inputs[key], f"{path}/input/{key}")
            if float.fromhex(inputs["s_beta_binary64_hex"]) != (
                2.0 * float.fromhex(inputs["v_beta_binary64_hex"])
            ):
                raise T810PreregistrationError(
                    f"{path}/input does not encode exact slope equality"
                )
            expected = _exact_keys(
                vector["expected"], {"slope_gate_fired"}, f"{path}/expected"
            )
            _expect(expected, "slope_gate_fired", False, f"{path}/expected")


def _validate_schema(root: dict[str, Any]) -> None:
    _exact_keys(
        root,
        {
            "artifacts",
            "assignment",
            "authorization",
            "build_preimage",
            "coordination",
            "decision",
            "design",
            "digest",
            "downstream_decisions",
            "estimator",
            "golden_vectors",
            "limitations",
            "lineage",
            "measurement",
            "preflight",
            "protocol",
            "scalar_golden_vectors",
            "schema_version",
            "terminal",
        },
        "",
    )
    _expect(root, "schema_version", PREREG_SCHEMA_VERSION, "")

    protocol = _exact_keys(root["protocol"], {"id", "run_authorized", "source"}, "/protocol")
    _expect(protocol, "id", "T-810", "/protocol")
    _expect(protocol, "run_authorized", False, "/protocol")

    authorization = _exact_keys(
        root["authorization"], {"missing_components", "stage1_satisfied"}, "/authorization"
    )
    _expect(authorization, "stage1_satisfied", False, "/authorization")
    _expect(authorization, "missing_components", ["a", "b", "c", "d2", "f", "g"], "/authorization")
    limitations = _exact_keys(
        root["limitations"],
        {
            "approval_receipt_trust_root_absent",
            "execution_mediation_incomplete",
            "unfrozen_procedures",
        },
        "/limitations",
    )
    _expect(
        limitations,
        "approval_receipt_trust_root_absent",
        True,
        "/limitations",
    )
    _expect(limitations, "execution_mediation_incomplete", True, "/limitations")
    _expect(
        limitations,
        "unfrozen_procedures",
        [
            "build_argv",
            "qsub_argv",
            "raw_throughput_to_log_matrix",
            "secondary_quantities",
            "downstream_decision_consumer",
        ],
        "/limitations",
    )

    assignment = root["assignment"]
    expected_assignment = {
        "randomized_dimension": "submission-order-only",
        "scheduler_assigns_nodes": True,
        "submission_order": {
            "canonical_encoding": "utf8-json-array-no-whitespace",
            "canonical_permutation": (
                '["slot-02","slot-00","slot-07","slot-11","slot-05",'
                '"slot-09","slot-04","slot-03","slot-12","slot-10",'
                '"slot-01","slot-06","slot-08"]'
            ),
            "expected_permutation": [
                "slot-02",
                "slot-00",
                "slot-07",
                "slot-11",
                "slot-05",
                "slot-09",
                "slot-04",
                "slot-03",
                "slot-12",
                "slot-10",
                "slot-01",
                "slot-06",
                "slot-08",
            ],
            "freeze_before_submission": True,
            "permutation_generation": "Generator(PCG64(seed)).permutation(slot_domain)",
            "prng": "PCG64",
            "receipt_fields": ["seed", "permutation"],
            "seed": 810,
            "seed_source": "approved-attempt-manifest",
            "slot_domain": [f"slot-{index:02d}" for index in range(13)],
            "version": "NumPy-2.2.6",
        },
        "treatment_to_node_assignment_exists": False,
    }
    _validate_exact_literal(assignment, expected_assignment, "/assignment")

    design = _exact_keys(
        root["design"],
        {
            "alpha",
            "alpha_sidedness",
            "assurance",
            "assurance_reproduction",
            "dropout_assurance",
            "effective_states",
            "objective",
            "repetition_precision",
            "selected",
            "tau_star",
            "tau_star_origin",
        },
        "/design",
    )
    expected_design = {
        "alpha": "0.05",
        "alpha_sidedness": "one-sided",
        "assurance": {"minimum": "0.80"},
        "assurance_reproduction": {
            "bit_generator": "PCG64",
            "draw_order": ["MS_A", "MS_E"],
            "draws": 400000,
            "failure_action": "fail-closed",
            "failure_code": "reference_not_reproduced",
            "generator": "Generator",
            "independent_check": {
                "draws": 10000000,
                "dropout": "0.8077",
                "selected": "0.8463",
            },
            "ms_a_draw": "chisquare(N-1,draws)/(N-1)*sigma_e^2",
            "ms_e_draw": (
                "chisquare((N-1)*(R-1),draws)/((N-1)*(R-1))*sigma_e^2"
            ),
            "numpy_version": "2.2.6",
            "pass_predicate": "tau_U < tau_star",
            "reported_dropout": "0.8080",
            "reported_selected": "0.8462",
            "seed": 810,
            "sigma_e": "0.012479",
            "update_values_on_mismatch": False,
            "wins": {"dropout": 323211, "selected": 338491},
        },
        "dropout_assurance": {
            "minimum": "0.80",
            "node_count_expression": "N-1",
        },
        "effective_states": {
            "terminal_reduced": {
                "effective_node_count": 12,
                "nu1": 11,
                "nu2": 99,
            },
            "valid": {"effective_node_count": 13, "nu1": 12, "nu2": 108},
        },
        "objective": "minimize-N-times-R",
        "repetition_precision": {
            "formula": "1/sqrt(2*(R-1))",
            "minimum_round_count": 10,
            "strict_upper_bound": "0.25",
        },
        "selected": {
            "node_count": 13,
            "round_count": 10,
            "total_measurements": 130,
            "unique_minimum": True,
        },
        "tau_star": "0.006",
        "tau_star_origin": "human-value-judgment-rounded-conservatively",
    }
    _validate_exact_literal(design, expected_design, "/design")
    selected = _exact_keys(
        design["selected"],
        {"node_count", "round_count", "total_measurements", "unique_minimum"},
        "/design/selected",
    )
    for key, expected in (
        ("node_count", 13),
        ("round_count", 10),
        ("total_measurements", 130),
        ("unique_minimum", True),
    ):
        _expect(selected, key, expected, "/design/selected")
    _expect(design, "tau_star", "0.006", "/design")

    states = _exact_keys(
        design["effective_states"], {"terminal_reduced", "valid"}, "/design/effective_states"
    )
    for state, expected in (
        ("terminal_reduced", {"effective_node_count": 12, "nu1": 11, "nu2": 99}),
        ("valid", {"effective_node_count": 13, "nu1": 12, "nu2": 108}),
    ):
        state_value = _exact_keys(
            states[state], {"effective_node_count", "nu1", "nu2"},
            f"/design/effective_states/{state}",
        )
        if state_value != expected:
            raise T810PreregistrationError(f"effective degrees of freedom drifted for {state}")

    reproduction = design["assurance_reproduction"]
    required_reproduction = {
        "numpy_version": "2.2.6",
        "generator": "Generator",
        "bit_generator": "PCG64",
        "seed": 810,
        "draws": 400000,
        "draw_order": ["MS_A", "MS_E"],
        "sigma_e": "0.012479",
        "pass_predicate": "tau_U < tau_star",
        "failure_action": "fail-closed",
        "failure_code": "reference_not_reproduced",
        "update_values_on_mismatch": False,
    }
    if not isinstance(reproduction, dict):
        raise T810PreregistrationError("/design/assurance_reproduction must be an object")
    for key, expected in required_reproduction.items():
        _expect(reproduction, key, expected, "/design/assurance_reproduction")
    if reproduction.get("wins") != {"dropout": 323211, "selected": 338491}:
        raise T810PreregistrationError("assurance winner counts drifted")

    measurement = root["measurement"]
    if not isinstance(measurement, dict) or not isinstance(measurement.get("environment"), dict):
        raise T810PreregistrationError("measurement environment is missing")
    _expect(
        measurement["environment"],
        "contract_sha256",
        ENVIRONMENT_CONTRACT_SHA256,
        "/measurement/environment",
    )
    if len(measurement["environment"]["contract_sha256"]) != 64:
        raise T810PreregistrationError("environment contract digest must have length 64")
    _expect(
        measurement,
        "canonical_benchmark_argv",
        [
            "-thread_num=48",
            "-ycsb_tuple_num=1000000",
            "-extime=3",
            "-clocks_per_us=2100",
            "-ycsb_rratio=50",
            "-ycsb_zipf_skew=0.9",
            "-ycsb_rmw=0",
        ],
        "/measurement",
    )

    estimator = root["estimator"]
    expected_estimator = {
        "alpha_use_count": 1,
        "f_quantile_backend": "frozen_binary64_hex_v1",
        "f_quantiles_binary64_hex": {
            "nu1=11,nu2=99": {
                "p_005": "0x1.a0c1a840d05a8p-2",
                "p_095": "0x1.e2fdb254a20a4p+0",
            },
            "nu1=12,nu2=108": {
                "p_005": "0x1.b48318ba0bb12p-2",
                "p_095": "0x1.d7c74477a51acp+0",
            },
        },
        "lower_variance": "max(0,(MS_A/F_quantile(0.95,nu1,nu2)-MS_E)/R)",
        "model": "node-random-effect-round-fixed-effect",
        "node_df": "N-1",
        "point_variance": "max(0,(MS_A-MS_E)/R)",
        "prohibited_alternatives": [
            "componentwise-upper-bound-composition",
            "alpha-reallocation",
            "mu-uncertainty-addition",
        ],
        "required_primary_outputs": ["tau_hat", "tau_L", "tau_U"],
        "required_secondary_outputs": [
            "raw_scale_fit",
            "kappa",
            "ICC",
            "node_mean_min_max_range",
            "per_node_mean_sd_cv_median_iqr",
            "MS_A",
            "MS_E",
            "F",
            "degrees_of_freedom",
            "drift_diagnostics",
        ],
        "residual_df": "(N-1)*(R-1)",
        "response": "natural-log-throughput",
        "select_primary_after_diagnostics": False,
        "truncation_means_zero_effect": False,
        "upper_variance": "max(0,(MS_A/F_quantile(0.05,nu1,nu2)-MS_E)/R)",
        "version_id": "node_random_round_fixed_f_interval_v1",
    }
    if estimator != expected_estimator:
        raise T810PreregistrationError("estimator contract drifted")

    lineage = _exact_keys(
        root["lineage"], {"attempt_schema", "edge_enforcement", "schema_frozen"}, "/lineage"
    )
    _expect(
        lineage,
        "attempt_schema",
        [
            "protocol_digest",
            "attempt_id",
            "submission_nonce",
            "group_manifest_sha256",
            "release_token_sha256",
            "slot_id",
        ],
        "/lineage",
    )
    _expect(lineage, "schema_frozen", True, "/lineage")

    decision = root["decision"]
    if decision.get("order") != [1, 2, 3, 4, 5] or decision.get("strategy") != "first-match":
        raise T810PreregistrationError("decision order drifted")
    slope_gate = decision.get("slope_gate")
    if not isinstance(slope_gate, dict) or slope_gate.get("operator") != ">":
        raise T810PreregistrationError("slope gate must use strict greater-than")
    if slope_gate.get("predicate") != "S_beta > 2*V_beta":
        raise T810PreregistrationError("slope gate predicate drifted")

    terminal = root["terminal"]
    names = [state.get("name") for state in terminal.get("states", [])]
    if names != [
        "pre_release_invalid",
        "post_release_pre_measurement_invalid",
        "incomplete_after_start",
        "terminal_reduced",
        "valid",
    ]:
        raise T810PreregistrationError("terminal states are not the frozen closed order")
    if terminal.get("evaluation") != "ordered-first-match":
        raise T810PreregistrationError("terminal evaluation order drifted")

    _validate_golden_vectors(root["golden_vectors"])
    _validate_scalar_golden_vectors(root["scalar_golden_vectors"])


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


def load_t810_preregistration(
    path: Path = PREREG_PATH,
    *,
    approval_receipt: ApprovalReceipt | Mapping[str, Any],
) -> VerifiedT810Preregistration:
    """外部承認 digest と一致する canonical artifact を immutable に射影する。"""

    receipt = _normalise_receipt(approval_receipt)
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise T810PreregistrationError(f"could not read preregistration: {path}") from exc
    parsed = _parse_json(raw)
    canonical = _canonical_bytes(parsed)
    actual_digest = _verify_approval_digest(
        raw=raw, canonical=canonical, receipt=receipt
    )
    if raw != canonical:
        raise T810PreregistrationError("artifact bytes are not canonical JSON")
    _validate_schema(parsed)
    verified = VerifiedT810Preregistration(
        sha256=actual_digest,
        approval_id=receipt.approval_id,
        projection=_freeze(parsed),
        _loader_token=_VERIFIED_CONSTRUCTION_TOKEN,
    )
    from .t810_estimator_v1 import (  # delayed to avoid a cycle
        T810EstimatorError,
        assert_estimator_conformance,
    )

    try:
        assert_estimator_conformance(verified)
    except T810EstimatorError as exc:
        raise T810PreregistrationError(
            "estimator does not conform to the frozen golden vectors"
        ) from exc
    return verified


def request_t810_launch(preregistration: VerifiedT810Preregistration) -> None:
    """dormant seal。実行 capability を返す正例は意図的に存在しない。"""

    if not preregistration.run_authorized:
        raise T810NotAuthorizedError("T-810 stage 1 is not satisfied; launch is forbidden")
    raise T810NotAuthorizedError("T-810 launch capability is not implemented in this slice")
