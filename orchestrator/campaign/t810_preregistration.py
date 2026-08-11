"""T-810 凍結事前登録 artifact の fail-closed loader。"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
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


@dataclass(frozen=True)
class VerifiedT810Preregistration:
    sha256: str
    approval_id: str
    projection: Mapping[str, Any]

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


def _walk_no_hidden_design(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if "candidate" in lowered or "design_option" in lowered:
                raise T810PreregistrationError(
                    f"hidden candidate design field is forbidden at {path}/{key}"
                )
            _walk_no_hidden_design(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_no_hidden_design(child, f"{path}/{index}")
    elif isinstance(value, float):
        raise T810PreregistrationError(f"float is forbidden at {path}")


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
        root["limitations"], {"execution_mediation_incomplete"}, "/limitations"
    )
    _expect(limitations, "execution_mediation_incomplete", True, "/limitations")

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

    estimator = root["estimator"]
    expected_estimator = {
        "alpha_use_count": 1,
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

    if not isinstance(root["golden_vectors"], list) or len(root["golden_vectors"]) < 7:
        raise T810PreregistrationError("golden vector closure is incomplete")
    _walk_no_hidden_design(root)


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
    return VerifiedT810Preregistration(
        sha256=actual_digest,
        approval_id=receipt.approval_id,
        projection=_freeze(parsed),
    )


def request_t810_launch(preregistration: VerifiedT810Preregistration) -> None:
    """dormant seal。実行 capability を返す正例は意図的に存在しない。"""

    if not preregistration.run_authorized:
        raise T810NotAuthorizedError("T-810 stage 1 is not satisfied; launch is forbidden")
    raise T810NotAuthorizedError("T-810 launch capability is not implemented in this slice")
