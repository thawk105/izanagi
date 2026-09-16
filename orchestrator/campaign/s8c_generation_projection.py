"""8c 世代間還流の閉じた射影と role payload 関所。

この module は campaign の他 module を import しない純粋 leaf である。caller は
workload descriptor、binding、whiteboard の origin を外部期待値として渡し、ここでは
その同一性と閉じた schema だけを検査する。
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any


ROLE_SCHEMA_VERSION = "p3-autonomous-workload-trial/v4"
VALIDATION_RECEIPT_SCHEMA_VERSION = "s8c-role-payload-validation-receipt/v1"
PILOT_SCOPE = "exploratory-ycsb-abc"
PLANNER_AXIS = "silo-backoff-trigger-gating"
LEAKPROOF_CONTEXT = (
    "Use only this campaign's projected descriptor, metrics, planner direction, "
    "and abstract whiteboard. No prior sweep winner, candidate ranking, or "
    "unmeasured performance is available."
)

ATTEMPT_POLICY = MappingProxyType({
    "attempts_per_role_generation": 1,
    "retry": False,
})
STOP_POLICY = MappingProxyType({
    "performance_early_stop": False,
    "generation_budget_is_fixed": True,
})

_COMMON_KEYS = frozenset({
    "schema_version",
    "pilot_scope",
    "scientific_claim",
    "workload",
    "generation",
    "workload_descriptor",
    "descriptor_binding",
    "attempt_policy",
    "stop_policy",
})
_PLANNER_ONLY_KEYS = frozenset({
    "current_perf", "leading_indicators", "whiteboard",
})
_CODER_ONLY_KEYS = frozenset({
    "leakproof_context",
    "gating_spec",
    "planner_direction",
    "baseline",
    "whiteboard",
})
_PERF_KEYS = frozenset({
    "throughput_tps",
    "abort_rate_pct",
    "latency_ns",
    "llc_miss_rate",
    "ipc",
})
_LEADING_KEYS = frozenset({
    "contention_level", "cache_miss_rate_pct", "IPC_overall",
})
_WHITEBOARD_KEYS = frozenset({
    "iteration", "direction", "magnitude", "result", "delta_pct",
})
_DIRECTIONS = frozenset({"increase", "decrease", "explore_both"})
_MAGNITUDES = frozenset({"small", "medium", "large"})
_RESULTS = frozenset({"success", "fail", "rejected"})
_CRITIC_KEYS = frozenset({
    "attribution", "recommend", "avoid", "uncertainty", "reverse_recommended",
})
_SOURCE_METRIC_KEYS = frozenset({
    "throughput_tps", "abort_rate", "latency_ns", "llc_miss_rate", "ipc",
})
_DIAGNOSTIC_METRICS = (
    "abort_rate", "latency_ns", "llc_miss_rate", "ipc",
)
_CRITIC_PROJECTION_KEYS = frozenset({
    "source_generation", "diagnostics", "uncertainty_present", "reverse_recommended",
})
_DIAGNOSTIC_KEYS = frozenset({"metric", "value"})


class GenerationProjectionError(ValueError):
    """8c 世代間射影の契約違反。"""


class CriticFeedbackError(GenerationProjectionError):
    """critic 入力または第二層射影の契約違反。"""


class PayloadValidationError(GenerationProjectionError):
    """planner / coder payload の閉包違反。"""


class GatingSpecError(GenerationProjectionError):
    """run 単位 GATING_SPEC snapshot の契約違反。"""


@dataclasses.dataclass(frozen=True, slots=True)
class PayloadValidationReceipt:
    """payload bytes と白名単仕様へ束縛した immutable receipt。"""

    role: str
    payload_sha256: str
    payload_allowlist_sha256: str
    safe_projection_sha256: str
    seal_sha256: str
    _safe_projection_bytes: bytes = dataclasses.field(repr=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VALIDATION_RECEIPT_SCHEMA_VERSION,
            "role": self.role,
            "payload_sha256": self.payload_sha256,
            "payload_allowlist_sha256": self.payload_allowlist_sha256,
            "safe_projection": json.loads(
                self._safe_projection_bytes.decode("utf-8")
            ),
            "safe_projection_sha256": self.safe_projection_sha256,
            "seal_sha256": self.seal_sha256,
        }

    def assert_bound_to(
        self,
        *,
        role: str,
        payload: Mapping[str, Any],
        payload_allowlist_sha256: str,
    ) -> None:
        if type(role) is not str or role != self.role:
            raise PayloadValidationError("validation receipt role が一致しない")
        if payload_allowlist_sha256 != self.payload_allowlist_sha256:
            raise PayloadValidationError(
                "validation receipt の白名単仕様 digest が一致しない"
            )
        if _sha256_canonical(payload) != self.payload_sha256:
            raise PayloadValidationError(
                "validation receipt の payload digest が一致しない"
            )
        projection_sha256 = hashlib.sha256(
            self._safe_projection_bytes
        ).hexdigest()
        if projection_sha256 != self.safe_projection_sha256:
            raise PayloadValidationError(
                "validation receipt の safe projection digest が一致しない"
            )
        seal_preimage = {
            "schema_version": VALIDATION_RECEIPT_SCHEMA_VERSION,
            "role": self.role,
            "payload_sha256": self.payload_sha256,
            "payload_allowlist_sha256": self.payload_allowlist_sha256,
            "safe_projection_sha256": self.safe_projection_sha256,
        }
        if _sha256_canonical(seal_preimage) != self.seal_sha256:
            raise PayloadValidationError("validation receipt seal が一致しない")


@dataclasses.dataclass(frozen=True, slots=True)
class AppliedCriticFeedback:
    """自由文を捨てた critic の第二層射影。"""

    planner_projection: Mapping[str, Any]
    prior_reverse: bool


@dataclasses.dataclass(frozen=True, slots=True)
class GatingSpecSnapshot:
    """全 workload より前に一度だけ作る run 単位 snapshot。"""

    text: str
    utf8_bytes: bytes
    sha256: str

    @classmethod
    def capture(cls, gating_spec: str) -> GatingSpecSnapshot:
        if type(gating_spec) is not str:
            raise GatingSpecError("GATING_SPEC は exact str 必須")
        try:
            encoded = gating_spec.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise GatingSpecError("GATING_SPEC を UTF-8 bytes にできない") from exc
        return cls(
            text=gating_spec,
            utf8_bytes=encoded,
            sha256=hashlib.sha256(encoded).hexdigest(),
        )

    def validate_payload_field(self, value: Any) -> None:
        if type(value) is not str:
            raise GatingSpecError("payload.gating_spec は exact str 必須")
        try:
            encoded = value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise GatingSpecError(
                "payload.gating_spec を UTF-8 bytes にできない"
            ) from exc
        if encoded != self.utf8_bytes:
            raise GatingSpecError(
                "payload.gating_spec bytes が run snapshot と一致しない"
            )


def snapshot_gating_spec(gating_spec: str) -> GatingSpecSnapshot:
    """run 開始時に一度呼び、同じ holder を全 workload へ渡す。"""

    return GatingSpecSnapshot.capture(gating_spec)


def validate_gating_spec_payload(
    value: Any, *, snapshot: GatingSpecSnapshot,
) -> None:
    """payload field を run 単位 snapshot と byte 比較する。"""

    if type(snapshot) is not GatingSpecSnapshot:
        raise GatingSpecError("snapshot は exact GatingSpecSnapshot 必須")
    snapshot.validate_payload_field(value)


def _require_mapping(value: Any, *, path: str, error_type: type[Exception]) -> Mapping:
    if not isinstance(value, Mapping):
        raise error_type(f"{path} は Mapping 必須")
    return value


def _require_exact_keys(
    value: Any,
    expected: frozenset[str],
    *,
    path: str,
    error_type: type[Exception],
) -> Mapping:
    mapping = _require_mapping(value, path=path, error_type=error_type)
    if set(mapping) != expected:
        raise error_type(f"{path} の key 集合が契約と一致しない")
    return mapping


def _require_exact_int(value: Any, *, path: str, error_type: type[Exception]) -> int:
    if type(value) is not int:
        raise error_type(f"{path} は exact int 必須")
    return value


def _require_positive_generation(
    value: Any, *, path: str, error_type: type[Exception],
) -> int:
    generation = _require_exact_int(value, path=path, error_type=error_type)
    if generation < 1:
        raise error_type(f"{path} は 1 以上必須")
    return generation


def _require_finite_float_or_none(
    value: Any, *, path: str, error_type: type[Exception],
) -> float | None:
    if value is None:
        return None
    if type(value) is not float or not math.isfinite(value):
        raise error_type(f"{path} は有限 float または None 必須")
    return value


def _assert_expected_tree(
    actual: Any,
    expected: Any,
    *,
    path: str,
    error_type: type[Exception],
) -> None:
    """外部期待値と型、key、順序、scalar 値を再帰的に exact 照合する。"""

    if isinstance(expected, Mapping):
        actual_mapping = _require_mapping(
            actual, path=path, error_type=error_type,
        )
        if set(actual_mapping) != set(expected):
            raise error_type(f"{path} の key 集合が外部期待値と一致しない")
        for key in expected:
            _assert_expected_tree(
                actual_mapping[key],
                expected[key],
                path=f"{path}.{key}",
                error_type=error_type,
            )
        return
    if isinstance(expected, list):
        if type(actual) is not list or len(actual) != len(expected):
            raise error_type(f"{path} の list shape が外部期待値と一致しない")
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            _assert_expected_tree(
                actual_item,
                expected_item,
                path=f"{path}[{index}]",
                error_type=error_type,
            )
        return
    if type(actual) is not type(expected) or actual != expected:
        raise error_type(f"{path} の型または値が外部期待値と一致しない")


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PayloadValidationError("receipt 対象を canonical JSON 化できない") from exc


def _sha256_canonical(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nested_key_sets(value: Any) -> dict[str, list[str]]:
    """値を残さず、再検査可能な再帰 key 射影だけを作る。"""

    projected: dict[str, list[str]] = {}

    def walk(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            keys = sorted(item)
            if not all(type(key) is str for key in keys):
                raise PayloadValidationError(f"{path} の key は exact str 必須")
            previous = projected.setdefault(path, keys)
            if previous != keys:
                raise PayloadValidationError(
                    f"{path} の反復 mapping key 集合が一致しない"
                )
            for key in keys:
                walk(item[key], f"{path}.{key}")
        elif type(item) is list:
            for child in item:
                walk(child, f"{path}[]")

    walk(value, "$")
    return projected


def _metric_nullness(value: Mapping[str, Any], keys: frozenset[str]) -> dict[str, bool]:
    return {key: value[key] is None for key in sorted(keys)}


def _safe_critic_projection(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "source_generation": value["source_generation"],
        "diagnostics": [
            {
                "metric": item["metric"],
                "value_is_null": item["value"] is None,
                "value_sha256": _sha256_canonical(item["value"]),
            }
            for item in value["diagnostics"]
        ],
        "uncertainty_present": value["uncertainty_present"],
        "reverse_recommended": value["reverse_recommended"],
    }


def _validation_receipt(
    payload: Mapping[str, Any],
    *,
    role: str,
    payload_allowlist_sha256: str,
    whiteboard_origin: Sequence[Mapping[str, Any]],
    critic_feedback: Mapping[str, Any] | None = None,
    gating_spec_sha256: str | None = None,
) -> PayloadValidationReceipt:
    if (
        type(payload_allowlist_sha256) is not str
        or len(payload_allowlist_sha256) != 64
        or any(char not in "0123456789abcdef" for char in payload_allowlist_sha256)
    ):
        raise PayloadValidationError("白名単仕様 digest は lowercase SHA-256 必須")
    fixed_literals: dict[str, Any] = {
        "schema_version": payload["schema_version"],
        "pilot_scope": payload["pilot_scope"],
        "scientific_claim": payload["scientific_claim"],
        "attempt_policy": dict(payload["attempt_policy"]),
        "stop_policy": dict(payload["stop_policy"]),
    }
    safe_projection: dict[str, Any] = {
        "role": role,
        "workload": payload["workload"],
        "generation": payload["generation"],
        "descriptor_sha256": payload["descriptor_binding"]["output_sha256"],
        "workload_descriptor_sha256": _sha256_canonical(
            payload["workload_descriptor"]
        ),
        "descriptor_binding_sha256": _sha256_canonical(
            payload["descriptor_binding"]
        ),
        "fixed_literals": fixed_literals,
        "nested_key_sets": _nested_key_sets(payload),
        "whiteboard_origin": [dict(entry) for entry in whiteboard_origin],
        "whiteboard_origin_sha256": _sha256_canonical(whiteboard_origin),
    }
    if role == "planner":
        safe_projection.update({
            "current_perf_nullness": _metric_nullness(
                payload["current_perf"], _PERF_KEYS
            ),
            "leading_metric_nullness": {
                key: payload["leading_indicators"][key] is None
                for key in ("IPC_overall", "cache_miss_rate_pct")
            },
            "contention_level_sha256": _sha256_canonical(
                payload["leading_indicators"]["contention_level"]
            ),
            "critic_feedback": _safe_critic_projection(critic_feedback),
        })
    elif role == "coder":
        fixed_literals.update({
            "leakproof_context": payload["leakproof_context"],
            "planner_axis": payload["planner_direction"]["axis"],
        })
        safe_projection.update({
            "baseline_nullness": _metric_nullness(payload["baseline"], _PERF_KEYS),
            "gating_spec_sha256": gating_spec_sha256,
            "planner_direction_sha256": _sha256_canonical(
                payload["planner_direction"]
            ),
        })
    else:  # pragma: no cover - private caller contract
        raise PayloadValidationError("validation receipt role が未対応")

    payload_sha256 = _sha256_canonical(payload)
    projection_bytes = _canonical_bytes(safe_projection)
    projection_sha256 = hashlib.sha256(projection_bytes).hexdigest()
    seal_preimage = {
        "schema_version": VALIDATION_RECEIPT_SCHEMA_VERSION,
        "role": role,
        "payload_sha256": payload_sha256,
        "payload_allowlist_sha256": payload_allowlist_sha256,
        "safe_projection_sha256": projection_sha256,
    }
    return PayloadValidationReceipt(
        role=role,
        payload_sha256=payload_sha256,
        payload_allowlist_sha256=payload_allowlist_sha256,
        safe_projection_sha256=projection_sha256,
        seal_sha256=_sha256_canonical(seal_preimage),
        _safe_projection_bytes=projection_bytes,
    )


def apply_critic_feedback(
    critic: Mapping[str, Any],
    *,
    source_metrics: Mapping[str, Any],
    source_generation: int,
) -> AppliedCriticFeedback:
    """critic 自由文を捨て、source metrics から診断を機械射影する。"""

    critic_map = _require_exact_keys(
        critic, _CRITIC_KEYS, path="critic", error_type=CriticFeedbackError,
    )
    for field in ("attribution", "recommend", "avoid", "uncertainty"):
        if type(critic_map[field]) is not str:
            raise CriticFeedbackError(f"critic.{field} は exact str 必須")
    reverse = critic_map["reverse_recommended"]
    if type(reverse) is not bool:
        raise CriticFeedbackError("critic.reverse_recommended は exact bool 必須")

    generation = _require_positive_generation(
        source_generation,
        path="source_generation",
        error_type=CriticFeedbackError,
    )
    metrics = _require_exact_keys(
        source_metrics,
        _SOURCE_METRIC_KEYS,
        path="source_metrics",
        error_type=CriticFeedbackError,
    )
    canonical_metrics = {
        name: _require_finite_float_or_none(
            metrics[name],
            path=f"source_metrics.{name}",
            error_type=CriticFeedbackError,
        )
        for name in _SOURCE_METRIC_KEYS
    }
    diagnostics = [
        {"metric": name, "value": canonical_metrics[name]}
        for name in _DIAGNOSTIC_METRICS
    ]
    projection = {
        "source_generation": generation,
        "diagnostics": diagnostics,
        "uncertainty_present": bool(critic_map["uncertainty"].strip()),
        "reverse_recommended": reverse,
    }
    return AppliedCriticFeedback(
        planner_projection=projection,
        prior_reverse=reverse,
    )


def _validate_critic_projection(
    value: Any, *, expected_source_generation: int,
) -> Mapping[str, Any]:
    projection = _require_exact_keys(
        value,
        _CRITIC_PROJECTION_KEYS,
        path="payload.critic_feedback",
        error_type=PayloadValidationError,
    )
    source_generation = _require_positive_generation(
        projection["source_generation"],
        path="payload.critic_feedback.source_generation",
        error_type=PayloadValidationError,
    )
    if source_generation != expected_source_generation:
        raise PayloadValidationError(
            "critic projection の source_generation identity が一致しない"
        )
    if type(projection["uncertainty_present"]) is not bool:
        raise PayloadValidationError("uncertainty_present は exact bool 必須")
    if type(projection["reverse_recommended"]) is not bool:
        raise PayloadValidationError("reverse_recommended は exact bool 必須")

    diagnostics = projection["diagnostics"]
    if type(diagnostics) is not list or len(diagnostics) != len(_DIAGNOSTIC_METRICS):
        raise PayloadValidationError("diagnostics は固定長 list 必須")
    for index, metric in enumerate(_DIAGNOSTIC_METRICS):
        item = _require_exact_keys(
            diagnostics[index],
            _DIAGNOSTIC_KEYS,
            path=f"payload.critic_feedback.diagnostics[{index}]",
            error_type=PayloadValidationError,
        )
        if type(item["metric"]) is not str or item["metric"] != metric:
            raise PayloadValidationError("diagnostics の metric 順序が契約と一致しない")
        _require_finite_float_or_none(
            item["value"],
            path=f"payload.critic_feedback.diagnostics[{index}].value",
            error_type=PayloadValidationError,
        )
    return projection


def validate_whiteboard(
    whiteboard: Any,
    *,
    current_generation: int,
    expected_origin: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    """8c payload の whiteboard を現世代と origin に束縛する。"""

    generation = _require_positive_generation(
        current_generation,
        path="current_generation",
        error_type=PayloadValidationError,
    )
    if type(whiteboard) is not list:
        raise PayloadValidationError("whiteboard は list 必須")
    maximum_count = generation - 1
    if len(whiteboard) > maximum_count:
        raise PayloadValidationError("whiteboard 件数が現世代の上限を超える")

    previous_iteration = 0
    for index, raw_entry in enumerate(whiteboard):
        entry = _require_exact_keys(
            raw_entry,
            _WHITEBOARD_KEYS,
            path=f"whiteboard[{index}]",
            error_type=PayloadValidationError,
        )
        iteration = _require_exact_int(
            entry["iteration"],
            path=f"whiteboard[{index}].iteration",
            error_type=PayloadValidationError,
        )
        if not 1 <= iteration <= maximum_count:
            raise PayloadValidationError(
                "whiteboard iteration は 1 から前世代までの範囲必須"
            )
        if iteration <= previous_iteration:
            raise PayloadValidationError(
                "whiteboard iteration は狭義単調増加必須"
            )
        previous_iteration = iteration
        for field, allowed in (
            ("direction", _DIRECTIONS),
            ("magnitude", _MAGNITUDES),
            ("result", _RESULTS),
        ):
            item = entry[field]
            if type(item) is not str or item not in allowed:
                raise PayloadValidationError(
                    f"whiteboard[{index}].{field} は閉じた str 値域必須"
                )
        if entry["delta_pct"] is not None:
            raise PayloadValidationError("whiteboard.delta_pct は None 固定")

    if expected_origin is not None:
        if isinstance(expected_origin, (str, bytes)) or not isinstance(
            expected_origin, Sequence
        ):
            raise PayloadValidationError("expected_origin は entry Sequence 必須")
        _assert_expected_tree(
            whiteboard,
            list(expected_origin),
            path="whiteboard",
            error_type=PayloadValidationError,
        )


def _validate_common_payload(
    payload: Mapping[str, Any],
    *,
    expected_workload: str,
    expected_generation: int,
    expected_workload_descriptor: Mapping[str, Any],
    expected_descriptor_binding: Mapping[str, Any],
) -> int:
    if type(expected_workload) is not str:
        raise PayloadValidationError("expected_workload は exact str 必須")
    generation = _require_positive_generation(
        expected_generation,
        path="expected_generation",
        error_type=PayloadValidationError,
    )
    fixed = {
        "schema_version": ROLE_SCHEMA_VERSION,
        "pilot_scope": PILOT_SCOPE,
        "scientific_claim": False,
        "workload": expected_workload,
        "generation": generation,
        "workload_descriptor": expected_workload_descriptor,
        "descriptor_binding": expected_descriptor_binding,
        "attempt_policy": ATTEMPT_POLICY,
        "stop_policy": STOP_POLICY,
    }
    for key, expected in fixed.items():
        _assert_expected_tree(
            payload[key],
            expected,
            path=f"payload.{key}",
            error_type=PayloadValidationError,
        )
    return generation


def _validate_expected_perf(
    value: Any,
    *,
    expected: Mapping[str, Any],
    path: str,
) -> None:
    metrics = _require_exact_keys(
        value, _PERF_KEYS, path=path, error_type=PayloadValidationError,
    )
    expected_metrics = _require_exact_keys(
        expected,
        _PERF_KEYS,
        path=f"expected {path}",
        error_type=PayloadValidationError,
    )
    for key in _PERF_KEYS:
        _require_finite_float_or_none(
            metrics[key],
            path=f"{path}.{key}",
            error_type=PayloadValidationError,
        )
        _require_finite_float_or_none(
            expected_metrics[key],
            path=f"expected {path}.{key}",
            error_type=PayloadValidationError,
        )
    _assert_expected_tree(
        metrics,
        expected_metrics,
        path=path,
        error_type=PayloadValidationError,
    )


def _validate_expected_leading(
    value: Any,
    *,
    expected: Mapping[str, Any],
) -> None:
    leading = _require_exact_keys(
        value,
        _LEADING_KEYS,
        path="payload.leading_indicators",
        error_type=PayloadValidationError,
    )
    expected_leading = _require_exact_keys(
        expected,
        _LEADING_KEYS,
        path="expected payload.leading_indicators",
        error_type=PayloadValidationError,
    )
    if (
        type(leading["contention_level"]) is not str
        or type(expected_leading["contention_level"]) is not str
    ):
        raise PayloadValidationError(
            "leading_indicators.contention_level は exact str 必須"
        )
    for key in ("cache_miss_rate_pct", "IPC_overall"):
        _require_finite_float_or_none(
            leading[key],
            path=f"payload.leading_indicators.{key}",
            error_type=PayloadValidationError,
        )
        _require_finite_float_or_none(
            expected_leading[key],
            path=f"expected payload.leading_indicators.{key}",
            error_type=PayloadValidationError,
        )
    _assert_expected_tree(
        leading,
        expected_leading,
        path="payload.leading_indicators",
        error_type=PayloadValidationError,
    )


def validate_planner_payload(
    payload: Mapping[str, Any],
    *,
    expected_workload: str,
    expected_generation: int,
    expected_workload_descriptor: Mapping[str, Any],
    expected_descriptor_binding: Mapping[str, Any],
    expected_whiteboard_origin: Sequence[Mapping[str, Any]],
    expected_current_perf: Mapping[str, Any],
    expected_leading_indicators: Mapping[str, Any],
    expected_critic_feedback: Mapping[str, Any] | None,
    payload_allowlist_sha256: str,
) -> PayloadValidationReceipt:
    """planner payload を再帰的 exact-key と外部 identity で閉じる。"""

    generation = _require_positive_generation(
        expected_generation,
        path="expected_generation",
        error_type=PayloadValidationError,
    )
    expected_keys = _COMMON_KEYS | _PLANNER_ONLY_KEYS
    if generation >= 2:
        expected_keys = expected_keys | {"critic_feedback"}
    planner = _require_exact_keys(
        payload,
        frozenset(expected_keys),
        path="planner payload",
        error_type=PayloadValidationError,
    )
    _validate_common_payload(
        planner,
        expected_workload=expected_workload,
        expected_generation=generation,
        expected_workload_descriptor=expected_workload_descriptor,
        expected_descriptor_binding=expected_descriptor_binding,
    )
    _validate_expected_perf(
        planner["current_perf"],
        expected=expected_current_perf,
        path="payload.current_perf",
    )
    _validate_expected_leading(
        planner["leading_indicators"],
        expected=expected_leading_indicators,
    )
    validate_whiteboard(
        planner["whiteboard"],
        current_generation=generation,
        expected_origin=expected_whiteboard_origin,
    )

    if generation == 1:
        if expected_critic_feedback is not None:
            raise PayloadValidationError(
                "世代 1 の expected critic feedback は None 必須"
            )
    else:
        if expected_critic_feedback is None:
            raise PayloadValidationError(
                "世代 2 以降は critic feedback の外部期待値が必須"
            )
        projection = _validate_critic_projection(
            planner["critic_feedback"],
            expected_source_generation=generation - 1,
        )
        _validate_critic_projection(
            expected_critic_feedback,
            expected_source_generation=generation - 1,
        )
        _assert_expected_tree(
            projection,
            expected_critic_feedback,
            path="payload.critic_feedback",
            error_type=PayloadValidationError,
        )
    return _validation_receipt(
        planner,
        role="planner",
        payload_allowlist_sha256=payload_allowlist_sha256,
        whiteboard_origin=expected_whiteboard_origin,
        critic_feedback=expected_critic_feedback,
    )


def validate_coder_payload(
    payload: Mapping[str, Any],
    *,
    expected_workload: str,
    expected_generation: int,
    expected_workload_descriptor: Mapping[str, Any],
    expected_descriptor_binding: Mapping[str, Any],
    expected_whiteboard_origin: Sequence[Mapping[str, Any]],
    expected_baseline: Mapping[str, Any],
    gating_spec_snapshot: GatingSpecSnapshot,
    payload_allowlist_sha256: str,
) -> PayloadValidationReceipt:
    """coder payload を再帰的 exact-key と run snapshot で閉じる。"""

    coder = _require_exact_keys(
        payload,
        frozenset(_COMMON_KEYS | _CODER_ONLY_KEYS),
        path="coder payload",
        error_type=PayloadValidationError,
    )
    generation = _validate_common_payload(
        coder,
        expected_workload=expected_workload,
        expected_generation=expected_generation,
        expected_workload_descriptor=expected_workload_descriptor,
        expected_descriptor_binding=expected_descriptor_binding,
    )
    _assert_expected_tree(
        coder["leakproof_context"],
        LEAKPROOF_CONTEXT,
        path="payload.leakproof_context",
        error_type=PayloadValidationError,
    )
    validate_gating_spec_payload(
        coder["gating_spec"], snapshot=gating_spec_snapshot,
    )

    direction = _require_exact_keys(
        coder["planner_direction"],
        frozenset({"axis", "direction", "magnitude"}),
        path="payload.planner_direction",
        error_type=PayloadValidationError,
    )
    if type(direction["axis"]) is not str or direction["axis"] != PLANNER_AXIS:
        raise PayloadValidationError("planner_direction.axis が固定 literal と一致しない")
    for field, allowed in (
        ("direction", _DIRECTIONS),
        ("magnitude", _MAGNITUDES),
    ):
        if type(direction[field]) is not str or direction[field] not in allowed:
            raise PayloadValidationError(
                f"planner_direction.{field} は閉じた str 値域必須"
            )
    _validate_expected_perf(
        coder["baseline"],
        expected=expected_baseline,
        path="payload.baseline",
    )
    validate_whiteboard(
        coder["whiteboard"],
        current_generation=generation,
        expected_origin=expected_whiteboard_origin,
    )
    return _validation_receipt(
        coder,
        role="coder",
        payload_allowlist_sha256=payload_allowlist_sha256,
        whiteboard_origin=expected_whiteboard_origin,
        gating_spec_sha256=gating_spec_snapshot.sha256,
    )
