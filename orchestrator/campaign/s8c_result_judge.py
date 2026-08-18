# -*- coding: utf-8 -*-
"""The sealed result judge for the stage 8c formal series.

The module deliberately keeps its public surface small.  The private frozen
records are the boundary between the preregistration consumer and callers;
in particular, a floor receipt is never an input to :func:`judge`.
Observation attestations are checked for raw-value binding here, but the
external producer/issuer is the trust root and remains outside this wave.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import shutil
import statistics
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .s8b_ratified_freeze import load_ratified_freeze


__all__ = ("verify_floor_bytes", "judge", "publish_result_table")


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONDITION_IDS = (
    "on_off_prediction_difference",
    "swapped_follow_through",
    "paired_repeat_contrast",
)
_CONDITION_SET = frozenset(_CONDITION_IDS)
_TABLE_NAMES = ("descriptive_only", "official_status", "selection_evaluation")
_PARAM_UNIT = "throughput_tps"
_PARAM_DIRECTION = "on_minus_off"
_MISSING = object()


class _ResultJudgeError(ValueError):
    """Base class for fail-closed consumer errors."""


class _FloorVerificationError(_ResultJudgeError):
    """A ratified floor binding or its bytes could not be verified."""


class _PreregistrationNotEffectiveError(_ResultJudgeError):
    """The supplied contrast contract cannot make the preregistration effective."""


class _InputContractError(_ResultJudgeError):
    """A caller supplied an input shape that is not an accepted contract."""


class _ResultTableError(_ResultJudgeError):
    """A result table cannot be published atomically."""


class _Status(str, Enum):
    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class _ContrastParams:
    """The only parameter object accepted by ``judge``.

    ``source_binding`` is an opaque preregistration binding.  It is kept in
    the frozen object even though the current producer does not yet provide a
    repository-wide commit binding.
    """

    n: int
    delta_min: float
    sd_max: float
    unit: str
    direction: str
    source_binding: str


@dataclass(frozen=True)
class _FloorArtifactBinding:
    path: str
    sha256: str


@dataclass(frozen=True)
class _RatifiedFloorBinding:
    floor_protocol: _FloorArtifactBinding
    floor_source: _FloorArtifactBinding
    env_tag: str
    frozen_at_head: str
    root: Path


@dataclass(frozen=True)
class _VerifiedFloorEvidence:
    """Verification provenance only; no floor value or raw measurement lives here."""

    floor_protocol_path: str
    floor_protocol_sha256: str
    floor_source_path: str
    floor_source_sha256: str
    env_tag: str
    frozen_at_head: str


@dataclass(frozen=True)
class _ConditionResult:
    condition_id: str
    status: _Status
    diagnostics: Mapping[str, Any]


@dataclass(frozen=True)
class _JudgeResult:
    conditions: Mapping[str, _ConditionResult]
    conclusion: _Status
    cell_rows: tuple[Mapping[str, Any], ...]
    selection_rows: tuple[Mapping[str, Any], ...]
    official_by_holdout: Mapping[str, _Status]


@dataclass(frozen=True)
class _ScheduleRow:
    schedule_index: int
    cell_id: str
    holdout_id: str
    arm: str
    replicate: int
    block: object


@dataclass(frozen=True)
class _Cell:
    cell_id: str
    holdout_id: str
    arm: str
    configuration_id: str
    declared_n: object


@dataclass(frozen=True)
class _ObservationContext:
    medians: Mapping[tuple[str, int], float]
    replicate_values: Mapping[tuple[str, int], tuple[float, ...]]
    blocks: Mapping[tuple[str, int], object]


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(child) for child in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(child) for child in value]
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _InputContractError(f"{label} must be a mapping")
    return value


def _sequence(value: Any, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise _InputContractError(f"{label} must be a sequence")
    return value


def _first(mapping: Mapping[str, Any], *keys: str, default: Any = _MISSING) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    if default is not _MISSING:
        return default
    raise _InputContractError(f"missing one of {keys!r}")


def _text(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise _InputContractError(f"{label} must be a non-empty string")
    return value


def _int(value: Any, label: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise _InputContractError(f"{label} must be an int")
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _InputContractError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise _InputContractError(f"{label} must be finite")
    return result


def _validate_contrast_params(params: Any) -> _ContrastParams:
    """Validate the sealed contract before any observation can affect status."""
    if type(params) is not _ContrastParams:
        raise _PreregistrationNotEffectiveError(
            "judge requires the frozen contrast params object",
        )
    if type(params.n) is not int or isinstance(params.n, bool) or params.n < 2:
        raise _PreregistrationNotEffectiveError("registered n is not an int >= 2")
    if isinstance(params.delta_min, bool) or not isinstance(params.delta_min, (int, float)):
        raise _PreregistrationNotEffectiveError("delta_min has an invalid type")
    if not math.isfinite(float(params.delta_min)) or float(params.delta_min) <= 0:
        raise _PreregistrationNotEffectiveError("delta_min is not finite and positive")
    if isinstance(params.sd_max, bool) or not isinstance(params.sd_max, (int, float)):
        raise _PreregistrationNotEffectiveError("sd_max has an invalid type")
    if not math.isfinite(float(params.sd_max)) or float(params.sd_max) < 0:
        raise _PreregistrationNotEffectiveError("sd_max is not finite and non-negative")
    if params.unit != _PARAM_UNIT:
        raise _PreregistrationNotEffectiveError("contrast unit is not the frozen unit")
    if params.direction != _PARAM_DIRECTION:
        raise _PreregistrationNotEffectiveError("contrast direction is not on-minus-off")
    if type(params.source_binding) is not str or not params.source_binding:
        raise _PreregistrationNotEffectiveError("contrast source binding is absent")
    return params


def _validate_condition_declarations(manifest: Any, prediction: Any) -> None:
    """Require every declared condition list to be the exact closed set."""
    for owner_name, owner in (("manifest", manifest), ("prediction", prediction)):
        if not isinstance(owner, Mapping):
            continue
        for field in ("condition_ids", "conditions"):
            if field not in owner:
                continue
            raw = owner[field]
            if isinstance(raw, Mapping):
                identifiers = list(raw.keys())
            else:
                identifiers = list(_sequence(raw, f"{owner_name}.{field}"))
            try:
                duplicate = len(identifiers) != len(set(identifiers))
                exact = set(identifiers) == _CONDITION_SET
            except TypeError as exc:
                raise _InputContractError(f"{owner_name}.{field} has an unhashable ID") from exc
            if duplicate:
                raise _InputContractError(f"{owner_name}.{field} contains duplicate condition IDs")
            if len(identifiers) != 3 or not exact:
                raise _InputContractError(f"{owner_name}.{field} is not the exact three-condition set")


def _normalise_cells(manifest: Mapping[str, Any]) -> tuple[tuple[_Cell, ...], tuple[str, ...]]:
    raw_cells = _sequence(manifest.get("cells"), "manifest.cells")
    if len(raw_cells) != 6:
        raise _InputContractError("manifest must declare exactly six cells")
    cells: list[_Cell] = []
    seen: set[str] = set()
    by_holdout_arm: set[tuple[str, str]] = set()
    by_holdout_configuration: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_cells):
        item = _mapping(raw, f"manifest.cells[{index}]")
        cell_id = _text(item.get("cell_id"), f"cells[{index}].cell_id")
        holdout_id = _text(item.get("holdout_id"), f"cells[{index}].holdout_id")
        arm = _text(_first(item, "arm", "condition"), f"cells[{index}].arm")
        if arm not in {"on", "off", "swapped"}:
            raise _InputContractError(f"unknown arm {arm!r}")
        configuration_id = _text(
            _first(item, "configuration_id", "config_id"),
            f"cells[{index}].configuration_id",
        )
        if (
            cell_id in seen
            or (holdout_id, arm) in by_holdout_arm
            or (holdout_id, configuration_id) in by_holdout_configuration
        ):
            raise _InputContractError("cell identity or holdout/arm is duplicated")
        seen.add(cell_id)
        by_holdout_arm.add((holdout_id, arm))
        by_holdout_configuration.add((holdout_id, configuration_id))
        cells.append(
            _Cell(
                cell_id=cell_id,
                holdout_id=holdout_id,
                arm=arm,
                configuration_id=configuration_id,
                declared_n=item.get("n", _MISSING),
            )
        )
    holdouts = tuple(dict.fromkeys(cell.holdout_id for cell in cells))
    if len(holdouts) != 2:
        raise _InputContractError("the formal manifest must contain two holdouts")
    expected_pairs = {(holdout, arm) for holdout in holdouts for arm in ("on", "off", "swapped")}
    if by_holdout_arm != expected_pairs:
        raise _InputContractError("manifest holdout/arm cells are incomplete")
    return tuple(cells), holdouts


def _validate_complete_block(
    manifest: Mapping[str, Any], cells: Sequence[_Cell], n: int,
) -> tuple[dict[int, _ScheduleRow], dict[tuple[str, int], _ScheduleRow]]:
    """Bind every schedule row to one cell and one 1-based replicate."""
    if "n" in manifest and (type(manifest["n"]) is not int or manifest["n"] != n):
        raise _InputContractError("manifest n differs from the sealed params n")
    for cell in cells:
        if (
            cell.declared_n is not _MISSING
            and (type(cell.declared_n) is not int or cell.declared_n != n)
        ):
            raise _InputContractError("cell n differs from the sealed params n")
    raw_schedule = _sequence(manifest.get("schedule"), "manifest.schedule")
    expected_count = len(cells) * n
    if len(raw_schedule) != expected_count:
        raise _InputContractError("schedule is not a complete block")
    cell_by_id = {cell.cell_id: cell for cell in cells}
    rows: dict[int, _ScheduleRow] = {}
    by_cell_replicate: dict[tuple[str, int], _ScheduleRow] = {}
    for index, raw in enumerate(raw_schedule):
        item = _mapping(raw, f"manifest.schedule[{index}]")
        schedule_index = _int(
            _first(item, "schedule_index", "seq", "index"),
            f"schedule[{index}].schedule_index",
        )
        cell_id = _text(item.get("cell_id"), f"schedule[{index}].cell_id")
        cell = cell_by_id.get(cell_id)
        if cell is None:
            raise _InputContractError("schedule references an unknown cell")
        replicate = _int(
            _first(item, "replicate", "replicate_index", "repeat"),
            f"schedule[{index}].replicate",
            minimum=1,
        )
        if replicate > n:
            raise _InputContractError("schedule replicate is outside the registered n")
        holdout = item.get("holdout_id", cell.holdout_id)
        arm = item.get("arm", item.get("condition", cell.arm))
        if holdout != cell.holdout_id or arm != cell.arm:
            raise _InputContractError("schedule identity differs from its cell")
        block = item.get("block", item.get("round", replicate))
        row = _ScheduleRow(schedule_index, cell_id, cell.holdout_id, cell.arm, replicate, block)
        if schedule_index in rows or (cell_id, replicate) in by_cell_replicate:
            raise _InputContractError("schedule index or cell replicate is duplicated")
        rows[schedule_index] = row
        by_cell_replicate[(cell_id, replicate)] = row
    indices = sorted(rows)
    if not indices or indices not in (list(range(0, len(indices))), list(range(1, len(indices) + 1))):
        raise _InputContractError("schedule indices are not one contiguous sequence")
    for cell in cells:
        observed = {
            replicate for (cell_id, replicate) in by_cell_replicate if cell_id == cell.cell_id
        }
        if observed != set(range(1, n + 1)):
            raise _InputContractError("a cell does not have the exact replicate block")
    return rows, by_cell_replicate


_DERIVED_INPUT_KEYS = frozenset({
    "median", "delta", "rank", "ranking", "within_config_median", "sample_sd",
    "mean_delta", "covariance", "correlation", "relative_difference", "spread_ratio",
})


def _gate_passed(item: Mapping[str, Any]) -> bool:
    for key in ("correctness_gate_passed", "gate_passed", "certified"):
        if key in item:
            return item[key] is True
    gate = item.get("correctness_gate", item.get("gate", _MISSING))
    if isinstance(gate, Mapping):
        return gate.get("passed") is True or gate.get("status") in {"passed", "PASS", "serializable"}
    return gate is True or (isinstance(gate, str) and gate in {"passed", "PASS", "serializable"})


def _trace_disabled(item: Mapping[str, Any]) -> bool:
    if "trace_enabled" in item:
        return item["trace_enabled"] is False
    if "trace_disabled" in item:
        return item["trace_disabled"] is True
    if "trace_mode" in item:
        return isinstance(item["trace_mode"], str) and item["trace_mode"] in {"disabled", "trace-disabled", "off"}
    return False


def _raw_values(item: Mapping[str, Any]) -> tuple[float, ...]:
    if _DERIVED_INPUT_KEYS & set(item):
        raise _InputContractError("caller supplied a derived statistic")
    sequence_keys = [key for key in ("values", "measurements", "throughputs", "raw_values") if key in item]
    scalar_keys = [key for key in ("throughput", "value", "raw_value") if key in item]
    if sequence_keys and scalar_keys:
        raise _InputContractError("observation mixes raw sequence and scalar value")
    if len(sequence_keys) > 1 or len(scalar_keys) > 1:
        raise _InputContractError("observation has multiple raw value fields")
    if sequence_keys:
        raw = _sequence(item[sequence_keys[0]], "observation raw values")
    elif scalar_keys:
        raw = (item[scalar_keys[0]],)
    else:
        raise _InputContractError("observation has no raw measurement")
    if not raw:
        raise _InputContractError("observation raw values are empty")
    values: list[float] = []
    for value in raw:
        values.append(_number(value, "observation raw value"))
    return tuple(values)


def _observation_raw_digest(values: Sequence[float]) -> str:
    canonical = json.dumps(
        [float(value) for value in values],
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _observation_attestation_matches(
    item: Mapping[str, Any], values: Sequence[float],
) -> bool:
    attestation_keys = [
        key for key in ("attestation", "gate_attestation", "observation_attestation")
        if key in item
    ]
    if len(attestation_keys) != 1:
        return False
    attestation = item[attestation_keys[0]]
    if not isinstance(attestation, Mapping):
        return False
    if set(attestation) != {"raw_values_sha256", "issuer"}:
        return False
    digest = attestation.get("raw_values_sha256")
    issuer = attestation.get("issuer")
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
        or type(issuer) is not str
        or not issuer
    ):
        return False
    return hmac.compare_digest(digest, _observation_raw_digest(values))


def _build_observation_context(
    observations: Any,
    schedule: Mapping[int, _ScheduleRow],
    by_cell_replicate: Mapping[tuple[str, int], _ScheduleRow],
) -> _ObservationContext:
    raw_observations = _sequence(observations, "observations")
    if len(raw_observations) != len(schedule):
        raise _InputContractError("observation count differs from the complete schedule")
    medians: dict[tuple[str, int], float] = {}
    replicate_values: dict[tuple[str, int], tuple[float, ...]] = {}
    blocks: dict[tuple[str, int], object] = {}
    seen_indices: set[int] = set()
    for index, raw in enumerate(raw_observations):
        item = _mapping(raw, f"observations[{index}]")
        schedule_index = _int(
            _first(item, "schedule_index", "seq", "index"),
            f"observations[{index}].schedule_index",
        )
        row = schedule.get(schedule_index)
        if row is None or schedule_index in seen_indices:
            raise _InputContractError("observation schedule index is missing, extra, or duplicated")
        seen_indices.add(schedule_index)
        for field, expected in (
            ("cell_id", row.cell_id),
            ("holdout_id", row.holdout_id),
            ("arm", row.arm),
            ("condition", row.arm),
            ("replicate", row.replicate),
            ("replicate_index", row.replicate),
        ):
            if field in item and (
                (field in {"replicate", "replicate_index"} and type(item[field]) is not int)
                or item[field] != expected
            ):
                raise _InputContractError(f"observation {field} differs from schedule binding")
        values = _raw_values(item)
        if (
            not _gate_passed(item)
            or not _trace_disabled(item)
            or not _observation_attestation_matches(item, values)
        ):
            raise _InputContractError("observation did not pass the correctness/trace gate attestation")
        median = float(statistics.median(values))
        if not math.isfinite(median):
            raise _InputContractError("derived configuration median is non-finite")
        key = (row.cell_id, row.replicate)
        if key in medians or key not in by_cell_replicate:
            raise _InputContractError("observation does not form a unique cell replicate")
        medians[key] = median
        replicate_values[key] = values
        blocks[key] = row.block
    if seen_indices != set(schedule):
        raise _InputContractError("observation schedule coverage is incomplete")
    if len(medians) != len(by_cell_replicate):
        raise _InputContractError("observation cell coverage is incomplete")
    return _ObservationContext(
        medians=MappingProxyType(dict(medians)),
        replicate_values=MappingProxyType(dict(replicate_values)),
        blocks=MappingProxyType(dict(blocks)),
    )


def _prediction_value(item: Mapping[str, Any], keys: tuple[str, ...], label: str) -> str:
    value = _first(item, *keys)
    return _text(value, label)


def _canonical_configuration_id(
    value: Any, cells: Sequence[_Cell],
) -> str | None:
    if type(value) is not str or not value:
        return None
    matches = {
        cell.configuration_id
        for cell in cells
        if value == cell.cell_id or value == cell.configuration_id
    }
    if len(matches) != 1:
        return None
    return next(iter(matches))


def _normalise_on_off(
    prediction: Any, holdouts: Sequence[str], cells: Sequence[_Cell] | None = None,
) -> dict[str, tuple[str, str]] | None:
    if not isinstance(prediction, Mapping):
        return None
    if _DERIVED_INPUT_KEYS & set(prediction):
        return None
    source = prediction.get("on_off", prediction.get("predictions", _MISSING))
    result: dict[str, tuple[str, str]] = {}
    if isinstance(source, Mapping):
        for holdout_id, raw in source.items():
            if not isinstance(raw, Mapping):
                return None
            if _DERIVED_INPUT_KEYS & set(raw):
                return None
            try:
                result[_text(holdout_id, "prediction holdout")] = (
                    _prediction_value(raw, ("on_prediction", "on", "on_configuration_id"), "on prediction"),
                    _prediction_value(raw, ("off_prediction", "off", "off_configuration_id"), "off prediction"),
                )
            except _InputContractError:
                return None
    elif source is not _MISSING:
        try:
            for index, raw in enumerate(_sequence(source, "prediction.on_off")):
                item = _mapping(raw, f"prediction.on_off[{index}]")
                if _DERIVED_INPUT_KEYS & set(item):
                    return None
                holdout_id = _text(item.get("holdout_id"), "prediction holdout")
                if holdout_id in result:
                    return None
                result[holdout_id] = (
                    _prediction_value(item, ("on_prediction", "on", "on_configuration_id"), "on prediction"),
                    _prediction_value(item, ("off_prediction", "off", "off_configuration_id"), "off prediction"),
                )
        except _InputContractError:
            return None
    else:
        on = prediction.get("on_predictions", _MISSING)
        off = prediction.get("off_predictions", _MISSING)
        if not isinstance(on, Mapping) or not isinstance(off, Mapping):
            return None
        if set(on) != set(off):
            return None
        for holdout_id in on:
            if type(holdout_id) is not str or type(on[holdout_id]) is not str or type(off[holdout_id]) is not str:
                return None
            result[holdout_id] = (on[holdout_id], off[holdout_id])
    if set(result) != set(holdouts) or len(result) != len(holdouts):
        return None
    if cells is not None:
        canonical: dict[str, tuple[str, str]] = {}
        for holdout_id, pair in result.items():
            on = _canonical_configuration_id(pair[0], cells)
            off = _canonical_configuration_id(pair[1], cells)
            if on is None or off is None:
                return None
            canonical[holdout_id] = (on, off)
        return canonical
    return result


def _normalise_swap_mapping(
    manifest: Mapping[str, Any], holdouts: Sequence[str],
) -> dict[str, str] | None:
    raw = manifest.get("swapped_mapping", manifest.get("swap_mapping", _MISSING))
    if not isinstance(raw, Mapping) or set(raw) != set(holdouts):
        return None
    result: dict[str, str] = {}
    for holdout_id, value in raw.items():
        try:
            if isinstance(value, str):
                source = value
            else:
                if not isinstance(value, Mapping):
                    return None
                source = _first(value, "source_holdout", "source", "mapped_from")
            source = _text(source, "swapped mapping source")
        except _InputContractError:
            return None
        if source == holdout_id or source not in holdouts or source in result.values():
            return None
        result[holdout_id] = source
    if set(result.values()) != set(holdouts):
        return None
    return result


def _normalise_swapped_prediction(
    prediction: Any, holdouts: Sequence[str], cells: Sequence[_Cell] | None = None,
) -> dict[str, str] | None:
    if not isinstance(prediction, Mapping):
        return None
    source = prediction.get(
        "swapped",
        prediction.get("swapped_predictions", prediction.get("swapped_follow_through", _MISSING)),
    )
    if source is _MISSING:
        return None
    result: dict[str, str] = {}
    try:
        if isinstance(source, Mapping):
            for holdout_id, raw in source.items():
                if isinstance(raw, Mapping):
                    if _DERIVED_INPUT_KEYS & set(raw):
                        return None
                    value = _prediction_value(raw, ("predicted", "prediction", "selected", "configuration_id"), "swapped prediction")
                else:
                    value = _text(raw, "swapped prediction")
                if holdout_id in result:
                    return None
                result[_text(holdout_id, "swapped holdout")] = value
        else:
            for index, raw in enumerate(_sequence(source, "prediction.swapped")):
                item = _mapping(raw, f"prediction.swapped[{index}]")
                if _DERIVED_INPUT_KEYS & set(item):
                    return None
                holdout_id = _text(item.get("holdout_id"), "swapped holdout")
                if holdout_id in result:
                    return None
                result[holdout_id] = _prediction_value(
                    item, ("predicted", "prediction", "selected", "configuration_id"), "swapped prediction",
                )
    except _InputContractError:
        return None
    if set(result) != set(holdouts):
        return None
    if cells is not None:
        canonical: dict[str, str] = {}
        for holdout_id, value in result.items():
            configuration_id = _canonical_configuration_id(value, cells)
            if configuration_id is None:
                return None
            canonical[holdout_id] = configuration_id
        return canonical
    return result


def _condition(
    condition_id: str, status: _Status, diagnostics: Mapping[str, Any],
) -> _ConditionResult:
    return _ConditionResult(condition_id, status, _freeze(dict(diagnostics)))


def _evaluate_prediction_difference(
    prediction: Any, holdouts: Sequence[str], cells: Sequence[_Cell],
) -> tuple[_ConditionResult, dict[str, tuple[str, str]] | None]:
    values = _normalise_on_off(prediction, holdouts, cells)
    if not holdouts or values is None:
        return _condition(
            _CONDITION_IDS[0], _Status.INDETERMINATE,
            {"reason": "prediction-missing-or-invalid"},
        ), None
    per_holdout = {
        holdout_id: {"on": pair[0], "off": pair[1], "different": pair[0] != pair[1]}
        for holdout_id, pair in values.items()
    }
    status = _Status.SATISFIED if any(item["different"] for item in per_holdout.values()) else _Status.UNSATISFIED
    return _condition(_CONDITION_IDS[0], status, {"holdouts": per_holdout}), values


def _evaluate_swapped(
    manifest: Mapping[str, Any], prediction: Any, holdouts: Sequence[str],
    on_off: Mapping[str, tuple[str, str]] | None, cells: Sequence[_Cell],
) -> _ConditionResult:
    mapping = _normalise_swap_mapping(manifest, holdouts)
    swapped = _normalise_swapped_prediction(prediction, holdouts, cells)
    if not holdouts or mapping is None or swapped is None or on_off is None:
        return _condition(
            _CONDITION_IDS[1], _Status.INDETERMINATE,
            {"reason": "swapped-mapping-or-prediction-invalid"},
        )
    per_holdout: dict[str, Any] = {}
    follows = True
    for holdout_id, source_holdout in mapping.items():
        expected = on_off[source_holdout][0]
        actual = swapped[holdout_id]
        matched = actual == expected
        follows = follows and matched
        per_holdout[holdout_id] = {
            "source_holdout": source_holdout,
            "predicted": actual,
            "follows_on_prediction": matched,
        }
    return _condition(
        _CONDITION_IDS[1],
        _Status.SATISFIED if follows else _Status.UNSATISFIED,
        {"holdouts": per_holdout},
    )


def _sample_covariance(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    value = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right)) / (len(left) - 1)
    return value if math.isfinite(value) else None


def _correlation(left: Sequence[float], right: Sequence[float], covariance: float | None) -> float | None:
    if covariance is None:
        return None
    left_sd = statistics.stdev(left)
    right_sd = statistics.stdev(right)
    if left_sd == 0 or right_sd == 0:
        return None
    value = covariance / (left_sd * right_sd)
    return value if math.isfinite(value) else None


def _safe_diagnostic(function: Any) -> Any:
    try:
        value = function()
    except (ArithmeticError, ValueError, statistics.StatisticsError):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _cell_matches(cell: _Cell, prediction: str) -> bool:
    return prediction == cell.configuration_id


def _evaluate_contrast(
    cells: Sequence[_Cell], holdouts: Sequence[str],
    context: _ObservationContext | None,
    on_off: Mapping[str, tuple[str, str]] | None,
    params: _ContrastParams,
    source_binding_ok: bool,
) -> tuple[_ConditionResult, dict[str, _Status]]:
    if not holdouts or context is None or on_off is None or not source_binding_ok:
        return _condition(
            _CONDITION_IDS[2], _Status.INDETERMINATE,
            {"reason": "observation-block-or-source-binding-invalid"},
        ), {holdout: _Status.INDETERMINATE for holdout in holdouts}
    by_holdout_arm = {(cell.holdout_id, cell.arm): cell for cell in cells}
    holdout_diagnostics: dict[str, Any] = {}
    holdout_statuses: dict[str, _Status] = {}
    for holdout_id in holdouts:
        on_cell = by_holdout_arm[(holdout_id, "on")]
        off_cell = by_holdout_arm[(holdout_id, "off")]
        on_prediction, off_prediction = on_off[holdout_id]
        same_prediction = on_prediction == off_prediction
        if same_prediction:
            holdout_statuses[holdout_id] = _Status.UNSATISFIED
            holdout_diagnostics[holdout_id] = {
                "status": _Status.UNSATISFIED.value,
                "same_prediction": True,
                "reason": "prediction-configurations-are-identical",
            }
            continue
        if not _cell_matches(on_cell, on_prediction) or not _cell_matches(off_cell, off_prediction):
            holdout_statuses[holdout_id] = _Status.INDETERMINATE
            holdout_diagnostics[holdout_id] = {"status": _Status.INDETERMINATE.value, "reason": "prediction-cell-binding-invalid"}
            continue
        on_values: list[float] = []
        off_values: list[float] = []
        deltas: list[float] = []
        block_pairs: list[dict[str, Any]] = []
        for replicate in range(1, params.n + 1):
            on_key = (on_cell.cell_id, replicate)
            off_key = (off_cell.cell_id, replicate)
            if on_key not in context.medians or off_key not in context.medians:
                holdout_statuses[holdout_id] = _Status.INDETERMINATE
                holdout_diagnostics[holdout_id] = {
                    "status": _Status.INDETERMINATE.value,
                    "reason": "paired-replicate-missing",
                }
                break
            if context.blocks[on_key] != context.blocks[off_key]:
                holdout_statuses[holdout_id] = _Status.INDETERMINATE
                holdout_diagnostics[holdout_id] = {
                    "status": _Status.INDETERMINATE.value,
                    "reason": "paired-block-mismatch",
                }
                break
            on_schedule = context.medians[on_key]
            off_schedule = context.medians[off_key]
            on_values.append(on_schedule)
            off_values.append(off_schedule)
            delta = on_schedule - off_schedule
            if not math.isfinite(delta):
                holdout_statuses[holdout_id] = _Status.INDETERMINATE
                holdout_diagnostics[holdout_id] = {
                    "status": _Status.INDETERMINATE.value,
                    "reason": "non-finite-paired-delta",
                }
                break
            deltas.append(delta)
            block_pairs.append({"replicate": replicate, "delta": delta})
        else:
            if len(deltas) != params.n or len(deltas) < 2:
                holdout_statuses[holdout_id] = _Status.INDETERMINATE
                holdout_diagnostics[holdout_id] = {
                    "status": _Status.INDETERMINATE.value,
                    "reason": "replicate-count-invalid",
                }
                continue
            try:
                mean_delta = float(statistics.fmean(deltas))
                sample_sd = float(statistics.stdev(deltas))
            except (ArithmeticError, ValueError, statistics.StatisticsError):
                holdout_statuses[holdout_id] = _Status.INDETERMINATE
                holdout_diagnostics[holdout_id] = {
                    "status": _Status.INDETERMINATE.value,
                    "reason": "summary-calculation-failed",
                }
                continue
            if not math.isfinite(mean_delta) or not math.isfinite(sample_sd):
                holdout_statuses[holdout_id] = _Status.INDETERMINATE
                holdout_diagnostics[holdout_id] = {
                    "status": _Status.INDETERMINATE.value,
                    "reason": "non-finite-summary",
                }
                continue
            covariance = _safe_diagnostic(lambda: _sample_covariance(on_values, off_values))
            correlation = _safe_diagnostic(lambda: _correlation(on_values, off_values, covariance))
            relative_difference = _safe_diagnostic(
                lambda: (
                    mean_delta / abs(statistics.fmean(off_values))
                    if statistics.fmean(off_values) != 0 else None
                )
            )
            spread_ratio = _safe_diagnostic(
                lambda: (
                    statistics.stdev(on_values) / statistics.stdev(off_values)
                    if statistics.stdev(off_values) != 0 else None
                )
            )
            status = (
                _Status.SATISFIED
                if mean_delta > float(params.delta_min) and sample_sd <= float(params.sd_max)
                else _Status.UNSATISFIED
            )
            holdout_statuses[holdout_id] = status
            holdout_diagnostics[holdout_id] = {
                "status": status.value,
                "deltas": tuple(deltas),
                "mean_delta": mean_delta,
                "sample_sd": sample_sd,
                "same_prediction": same_prediction,
                "covariance": covariance,
                "correlation": correlation,
                "relative_difference": relative_difference,
                "spread_ratio": spread_ratio,
                "paired_blocks": tuple(block_pairs),
            }
    if any(status is _Status.INDETERMINATE for status in holdout_statuses.values()):
        status = _Status.INDETERMINATE
    elif any(status is _Status.UNSATISFIED for status in holdout_statuses.values()):
        status = _Status.UNSATISFIED
    else:
        status = _Status.SATISFIED
    return _condition(_CONDITION_IDS[2], status, {"holdouts": holdout_diagnostics}), holdout_statuses


def _derived_cell_rows(
    cells: Sequence[_Cell], context: _ObservationContext | None,
    holdouts: Sequence[str],
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    rows: list[dict[str, Any]] = []
    for cell in cells:
        raw_values: tuple[tuple[float, ...], ...] = ()
        replicate_medians: tuple[float, ...] = ()
        if context is not None:
            replicate_keys = tuple(
                (cell.cell_id, replicate)
                for replicate in sorted(
                    replicate for cell_id, replicate in context.medians if cell_id == cell.cell_id
                )
            )
            raw_values = tuple(context.replicate_values[key] for key in replicate_keys)
            replicate_medians = tuple(
                context.medians[(cell.cell_id, replicate)]
                for _cell_id, replicate in replicate_keys
            )
        median = float(statistics.median(replicate_medians)) if replicate_medians else None
        rows.append({
            "cell_id": cell.cell_id,
            "holdout_id": cell.holdout_id,
            "arm": cell.arm,
            "configuration_id": cell.configuration_id,
            "replicate_values": raw_values,
            "replicate_medians": replicate_medians,
            "within_config_median": median,
            "rank": None,
        })
    for holdout_id in holdouts:
        candidates = [row for row in rows if row["holdout_id"] == holdout_id and row["within_config_median"] is not None]
        candidates.sort(key=lambda row: (-row["within_config_median"], row["cell_id"]))
        for rank, row in enumerate(candidates, 1):
            row["rank"] = rank
    frozen_rows = tuple(_freeze(row) for row in rows)
    selection_rows = tuple(
        _freeze({
            "cell_id": row["cell_id"],
            "holdout_id": row["holdout_id"],
            "arm": row["arm"],
            "configuration_id": row["configuration_id"],
            "within_config_rank": row["rank"],
        })
        for row in rows
    )
    return frozen_rows, selection_rows


def _source_binding_matches(manifest: Mapping[str, Any], params: _ContrastParams) -> bool:
    declared = manifest.get("source_binding", _MISSING)
    return type(declared) is str and bool(declared) and declared == params.source_binding


def _selection_evaluation_rows(
    cells: Sequence[_Cell],
    rows: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    prediction: Any,
    holdouts: Sequence[str],
    conditions: Mapping[str, _ConditionResult],
) -> tuple[Mapping[str, Any], ...]:
    """Keep selection evidence separate from the official performance table."""
    on_off = _normalise_on_off(prediction, holdouts, cells)
    swapped = _normalise_swapped_prediction(prediction, holdouts, cells)
    swap_mapping = _normalise_swap_mapping(manifest, holdouts)
    on_off_status = conditions[_CONDITION_IDS[0]].status.value
    swapped_status = conditions[_CONDITION_IDS[1]].status.value
    by_cell_id = {cell.cell_id: row for cell, row in zip(cells, rows)}
    enriched: list[Mapping[str, Any]] = []
    for cell, row in zip(cells, rows):
        predicted: str | None = None
        rank_holdout_id = cell.holdout_id
        if on_off is not None and cell.arm in {"on", "off"}:
            pair = on_off.get(cell.holdout_id)
            if pair is not None:
                predicted = pair[0] if cell.arm == "on" else pair[1]
        elif swapped is not None and cell.arm == "swapped":
            predicted = swapped.get(cell.holdout_id)
            if swap_mapping is not None:
                rank_holdout_id = swap_mapping.get(cell.holdout_id, cell.holdout_id)
        predicted_rank: int | None = None
        if predicted is not None:
            for candidate in cells:
                if candidate.holdout_id == rank_holdout_id and _cell_matches(candidate, predicted):
                    candidate_row = by_cell_id[candidate.cell_id]
                    predicted_rank = candidate_row.get("within_config_rank")
                    break
        enriched.append(_freeze({
            "cell_id": row["cell_id"],
            "holdout_id": row["holdout_id"],
            "arm": row["arm"],
            "configuration_id": row["configuration_id"],
            "within_config_rank": row["within_config_rank"],
            "predicted_configuration_id": predicted,
            "prediction_rank_holdout_id": rank_holdout_id,
            "predicted_rank": predicted_rank,
            "prediction_matches_rank": (
                predicted_rank is not None and row["within_config_rank"] == predicted_rank
            ),
            "on_off_prediction_difference": on_off_status,
            "swapped_follow_through": swapped_status,
        }))
    return tuple(enriched)


def _derive_conclusion(conditions: Mapping[str, _ConditionResult]) -> _Status:
    statuses = tuple(conditions[condition_id].status for condition_id in _CONDITION_IDS)
    if any(status is _Status.INDETERMINATE for status in statuses):
        return _Status.INDETERMINATE
    if any(status is _Status.UNSATISFIED for status in statuses):
        return _Status.UNSATISFIED
    return _Status.SATISFIED


def judge(
    manifest: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    prediction: Mapping[str, Any],
    params: _ContrastParams,
) -> _JudgeResult:
    """Derive all three condition statuses from sealed, raw observation inputs."""
    params = _validate_contrast_params(params)
    _validate_condition_declarations(manifest, prediction)
    manifest_map = _mapping(manifest, "manifest")
    cells: tuple[_Cell, ...]
    holdouts: tuple[str, ...]
    try:
        cells, holdouts = _normalise_cells(manifest_map)
    except _InputContractError:
        cells = ()
        holdouts = ()
    complete_block = False
    context: _ObservationContext | None = None
    if cells:
        try:
            schedule, by_cell_replicate = _validate_complete_block(manifest_map, cells, params.n)
            context = _build_observation_context(observations, schedule, by_cell_replicate)
            complete_block = True
        except _InputContractError:
            context = None
    if not cells or not holdouts or not complete_block:
        conditions = MappingProxyType({
            condition_id: _condition(
                condition_id,
                _Status.INDETERMINATE,
                {"reason": "manifest-or-complete-block-missing"},
            )
            for condition_id in _CONDITION_IDS
        })
        official_by_holdout: Mapping[str, _Status] = MappingProxyType({})
    else:
        first, on_off = _evaluate_prediction_difference(prediction, holdouts, cells)
        second = _evaluate_swapped(manifest_map, prediction, holdouts, on_off, cells)
        third, official_by_holdout = _evaluate_contrast(
            cells, holdouts, context, on_off, params,
            _source_binding_matches(manifest_map, params),
        )
        conditions = MappingProxyType({
            _CONDITION_IDS[0]: first,
            _CONDITION_IDS[1]: second,
            _CONDITION_IDS[2]: third,
        })
    cell_rows, selection_rows = _derived_cell_rows(cells, context, holdouts)
    selection_rows = _selection_evaluation_rows(
        cells, selection_rows, manifest_map, prediction, holdouts, conditions,
    )
    return _JudgeResult(
        conditions=conditions,
        conclusion=_derive_conclusion(conditions),
        cell_rows=cell_rows,
        selection_rows=selection_rows,
        official_by_holdout=MappingProxyType(dict(official_by_holdout)),
    )


def _ratified_artifact_binding(
    document: Mapping[str, Any], field: str,
) -> _FloorArtifactBinding:
    value = document.get(field, _MISSING)
    if not isinstance(value, Mapping) or set(value) != {"path", "sha256"}:
        raise _FloorVerificationError(f"ratified {field} record is invalid")
    path = _text(value.get("path"), f"ratified {field} path")
    sha256 = _text(value.get("sha256"), f"ratified {field} sha256")
    if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
        raise _FloorVerificationError(f"ratified {field} sha256 is invalid")
    return _FloorArtifactBinding(path=path, sha256=sha256)


def _ratified_floor_binding(ratified: Any) -> _RatifiedFloorBinding:
    document = _mapping(getattr(ratified, "document", None), "ratified freeze document")
    floor_protocol = _ratified_artifact_binding(document, "floor_protocol")
    floor_source = _ratified_artifact_binding(document, "floor_source")
    env_tag = _text(document.get("env_tag", _MISSING), "ratified env_tag")
    frozen_at_head = _text(
        document.get("frozen_at_head", _MISSING), "ratified frozen_at_head",
    )
    if len(frozen_at_head) != 40 or any(
        char not in "0123456789abcdef" for char in frozen_at_head
    ):
        raise _FloorVerificationError("ratified frozen_at_head is invalid")
    root = Path(getattr(ratified, "root", _REPO_ROOT))
    protocol_path = Path(floor_protocol.path)
    source_path = Path(floor_source.path)
    if not protocol_path.is_absolute():
        protocol_path = root / protocol_path
    if not source_path.is_absolute():
        source_path = root / source_path
    if protocol_path.resolve(strict=False) == source_path.resolve(strict=False):
        raise _FloorVerificationError("ratified floor artifacts resolve to one path")
    return _RatifiedFloorBinding(
        floor_protocol=floor_protocol,
        floor_source=floor_source,
        env_tag=env_tag,
        frozen_at_head=frozen_at_head,
        root=root,
    )


def _floor_candidate_path(floor_refs: Any) -> tuple[tuple[Path, str], ...]:
    if isinstance(floor_refs, Mapping):
        if set(floor_refs) != {"floor_protocol", "floor_source"}:
            raise _FloorVerificationError(
                "floor_refs must name floor_protocol and floor_source",
            )
        candidates = (floor_refs["floor_protocol"], floor_refs["floor_source"])
    else:
        candidates = tuple(_sequence(floor_refs, "floor_refs"))
    if len(candidates) != 2:
        raise _FloorVerificationError(
            "floor_refs must contain exactly two artifact references",
        )
    result: list[tuple[Path, str]] = []
    resolved_seen: set[Path] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise _FloorVerificationError(f"floor ref {index} is not a mapping")
        named = [
            key for key in ("floor_protocol", "floor_source")
            if key in candidate
        ]
        if len(named) == 1 and isinstance(candidate[named[0]], Mapping):
            candidate = candidate[named[0]]
        path = candidate.get("path")
        sha256 = candidate.get("sha256")
        if not isinstance(path, (str, os.PathLike)):
            raise _FloorVerificationError(f"floor ref {index} path is invalid")
        if type(sha256) is not str or len(sha256) != 64 or any(
            char not in "0123456789abcdef" for char in sha256
        ):
            raise _FloorVerificationError(f"floor ref {index} sha256 is invalid")
        resolved = Path(path).resolve(strict=False)
        if resolved in resolved_seen:
            raise _FloorVerificationError("floor refs contain a duplicate artifact path")
        resolved_seen.add(resolved)
        result.append((Path(path), sha256))
    return tuple(result)


def verify_floor_bytes(
    floor_refs: Sequence[Mapping[str, Any]] | Mapping[str, Mapping[str, Any]],
) -> _VerifiedFloorEvidence:
    """Verify both ratified floor artifacts and return provenance only."""
    try:
        ratified = load_ratified_freeze()
        binding = _ratified_floor_binding(ratified)
        candidates = _floor_candidate_path(floor_refs)
        expected = (
            (binding.floor_protocol, "floor_protocol"),
            (binding.floor_source, "floor_source"),
        )
        candidate_by_path: dict[Path, tuple[Path, str]] = {}
        for candidate_path, candidate_sha256 in candidates:
            effective_path = (
                candidate_path
                if candidate_path.is_absolute()
                else binding.root / candidate_path
            )
            resolved = effective_path.resolve(strict=False)
            if resolved in candidate_by_path:
                raise _FloorVerificationError("floor refs contain a duplicate artifact path")
            candidate_by_path[resolved] = (effective_path, candidate_sha256)
        for artifact_binding, label in expected:
            expected_path = Path(artifact_binding.path)
            if not expected_path.is_absolute():
                expected_path = binding.root / expected_path
            expected_resolved = expected_path.resolve(strict=False)
            candidate = candidate_by_path.get(expected_resolved)
            if candidate is None:
                raise _FloorVerificationError(
                    f"caller floor refs do not contain ratified {label} path",
                )
            candidate_path, candidate_sha256 = candidate
            if candidate_sha256 != artifact_binding.sha256:
                raise _FloorVerificationError(
                    f"caller {label} sha256 differs from ratified binding",
                )
            try:
                raw = candidate_path.read_bytes()
            except OSError as exc:
                raise _FloorVerificationError(
                    f"ratified {label} artifact cannot be read",
                ) from exc
            actual_sha256 = hashlib.sha256(raw).hexdigest()
            if actual_sha256 != artifact_binding.sha256:
                raise _FloorVerificationError(
                    f"{label} bytes sha256 differs from ratified binding",
                )
        return _VerifiedFloorEvidence(
            floor_protocol_path=binding.floor_protocol.path,
            floor_protocol_sha256=binding.floor_protocol.sha256,
            floor_source_path=binding.floor_source.path,
            floor_source_sha256=binding.floor_source.sha256,
            env_tag=binding.env_tag,
            frozen_at_head=binding.frozen_at_head,
        )
    except _FloorVerificationError:
        raise
    except Exception as exc:  # noqa: BLE001 - public boundary is one dedicated error
        raise _FloorVerificationError("floor artifact verification failed") from exc


def _validate_verified_floor(evidence: Any) -> _VerifiedFloorEvidence:
    if type(evidence) is not _VerifiedFloorEvidence:
        raise _ResultTableError("publish requires a verified floor receipt")
    for field_name in (
        "floor_protocol_path", "floor_protocol_sha256",
        "floor_source_path", "floor_source_sha256", "env_tag", "frozen_at_head",
    ):
        try:
            _text(getattr(evidence, field_name), f"floor receipt {field_name}")
        except _InputContractError as exc:
            raise _ResultTableError("floor receipt is invalid") from exc
    if any(
        len(getattr(evidence, field_name)) != 64
        or any(char not in "0123456789abcdef" for char in getattr(evidence, field_name))
        for field_name in ("floor_protocol_sha256", "floor_source_sha256")
    ):
        raise _ResultTableError("floor receipt contains an invalid artifact sha256")
    if len(evidence.frozen_at_head) != 40 or any(
        char not in "0123456789abcdef" for char in evidence.frozen_at_head
    ):
        raise _ResultTableError("floor receipt contains an invalid frozen_at_head")
    try:
        current = _ratified_floor_binding(load_ratified_freeze())
    except Exception as exc:  # noqa: BLE001 - publish has one fail-closed boundary
        raise _ResultTableError("current ratified floor binding is unavailable") from exc
    expected = (
        current.floor_protocol.path,
        current.floor_protocol.sha256,
        current.floor_source.path,
        current.floor_source.sha256,
        current.env_tag,
        current.frozen_at_head,
    )
    actual = (
        evidence.floor_protocol_path,
        evidence.floor_protocol_sha256,
        evidence.floor_source_path,
        evidence.floor_source_sha256,
        evidence.env_tag,
        evidence.frozen_at_head,
    )
    if actual != expected:
        raise _ResultTableError("floor receipt is not from the current ratified freeze")
    return evidence


def _floor_provenance_metadata(
    floor_receipt: _VerifiedFloorEvidence,
) -> Mapping[str, str]:
    """Project only verified floor provenance into the published tables."""
    return _freeze({
        "floor_protocol_path": floor_receipt.floor_protocol_path,
        "floor_protocol_sha256": floor_receipt.floor_protocol_sha256,
        "floor_source_path": floor_receipt.floor_source_path,
        "floor_source_sha256": floor_receipt.floor_source_sha256,
        "env_tag": floor_receipt.env_tag,
        "frozen_at_head": floor_receipt.frozen_at_head,
    })


def _expected_cell_ids(predeclared_cells: Any) -> tuple[str, ...]:
    raw = _sequence(predeclared_cells, "predeclared_cells")
    if len(raw) != 6:
        raise _ResultTableError("the predeclared result-cell set must contain six cells")
    result: list[str] = []
    for index, item in enumerate(raw):
        cell_id = item if isinstance(item, str) else _mapping(item, f"predeclared_cells[{index}]").get("cell_id")
        result.append(_text(cell_id, f"predeclared_cells[{index}].cell_id"))
    if len(result) != len(set(result)):
        raise _ResultTableError("predeclared result-cell set contains a duplicate")
    return tuple(result)


def _validate_exact_cell_set(
    generated_rows: Sequence[Mapping[str, Any]], predeclared_cells: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    generated_ids: list[str] = []
    for index, row in enumerate(generated_rows):
        item = _mapping(row, f"generated result row {index}")
        cell_id = _text(item.get("cell_id"), f"generated result row {index}.cell_id")
        generated_ids.append(cell_id)
    if len(generated_ids) != len(set(generated_ids)):
        raise _ResultTableError("generated result rows contain a duplicate cell")
    if len(generated_ids) != len(predeclared_cells) or set(generated_ids) != set(predeclared_cells):
        raise _ResultTableError("generated result rows do not exactly match predeclared cells")
    by_id = {row["cell_id"]: row for row in generated_rows}
    return tuple(by_id[cell_id] for cell_id in predeclared_cells)


def _safe_output_paths(output_paths: Mapping[str, os.PathLike[str] | str]) -> dict[str, Path]:
    if not isinstance(output_paths, Mapping) or set(output_paths) != set(_TABLE_NAMES):
        raise _ResultTableError("output paths must name exactly the three result tables")
    result: dict[str, Path] = {}
    resolved_seen: set[Path] = set()
    repo = _REPO_ROOT.resolve()
    for name in _TABLE_NAMES:
        raw = output_paths[name]
        if not isinstance(raw, (str, os.PathLike)):
            raise _ResultTableError(f"output path for {name} is invalid")
        path = Path(raw)
        if not path.is_absolute():
            raise _ResultTableError("result output paths must be absolute")
        if os.path.lexists(path):
            raise _ResultTableError(f"result output already exists: {path}")
        parent = path.parent
        if not parent.is_dir():
            raise _ResultTableError(f"result output parent does not exist: {parent}")
        resolved = path.resolve(strict=False)
        try:
            resolved.relative_to(repo)
        except ValueError:
            pass
        else:
            raise _ResultTableError("result output resolves inside the repository")
        if resolved in resolved_seen:
            raise _ResultTableError("result output paths resolve to the same destination")
        resolved_seen.add(resolved)
        result[name] = path
    return result


def _table_bytes(
    name: str,
    rows: Sequence[Mapping[str, Any]],
    result: _JudgeResult,
    floor_provenance: Mapping[str, str],
) -> bytes:
    payload = {
        "schema": "s8c-result-table/v1",
        "table": name,
        "official_conclusion": result.conclusion.value if name == "official_status" else None,
        "metadata": _plain(floor_provenance),
        "result_table": {"cells": [_plain(row) for row in rows]},
    }
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _official_rows(
    rows: Sequence[Mapping[str, Any]], result: _JudgeResult,
) -> tuple[Mapping[str, Any], ...]:
    output: list[Mapping[str, Any]] = []
    for row in rows:
        holdout_id = row["holdout_id"]
        status = result.official_by_holdout.get(holdout_id, _Status.INDETERMINATE)
        output.append(_freeze({
            "cell_id": row["cell_id"],
            "holdout_id": holdout_id,
            "arm": row["arm"],
            "official_status": status.value,
        }))
    return tuple(output)


def _selection_rows(
    rows: Sequence[Mapping[str, Any]], result: _JudgeResult,
) -> tuple[Mapping[str, Any], ...]:
    by_id = {row["cell_id"]: row for row in result.selection_rows}
    output: list[Mapping[str, Any]] = []
    for row in rows:
        selected = by_id.get(row["cell_id"])
        if selected is None:
            raise _ResultTableError("selection table is missing a result cell")
        output.append(selected)
    return tuple(output)


def _exclusive_write(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    fd: int | None = None
    try:
        fd = os.open(path, flags | no_follow, 0o644)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short result table write")
            view = view[written:]
        os.fsync(fd)
    except BaseException:
        if fd is not None:
            try:
                os.close(fd)
            except OSError as close_exc:
                raise _ResultTableError("result table write close failed") from close_exc
        if fd is not None:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_exc:
                raise _ResultTableError("result table write rollback failed") from cleanup_exc
        raise
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _remove_transaction_directory(path: Path) -> None:
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise _ResultTableError("result transaction rollback failed") from exc


def publish_result_table(
    result: _JudgeResult,
    predeclared_cells: Sequence[Mapping[str, Any] | str],
    output_paths: Mapping[str, os.PathLike[str] | str],
    floor_receipt: _VerifiedFloorEvidence,
) -> Mapping[str, Path]:
    """Publish three create-only tables from one completed transaction."""
    if type(result) is not _JudgeResult:
        raise _ResultTableError("publish requires a judge result object")
    floor_receipt = _validate_verified_floor(floor_receipt)
    floor_provenance = _floor_provenance_metadata(floor_receipt)
    expected = _expected_cell_ids(predeclared_cells)
    paths = _safe_output_paths(output_paths)
    descriptive_rows = _validate_exact_cell_set(result.cell_rows, expected)
    official_rows = _official_rows(descriptive_rows, result)
    selection_rows = _selection_rows(descriptive_rows, result)
    staged = {
        "descriptive_only": _table_bytes(
            "descriptive_only", descriptive_rows, result, floor_provenance,
        ),
        "official_status": _table_bytes(
            "official_status", official_rows, result, floor_provenance,
        ),
        "selection_evaluation": _table_bytes(
            "selection_evaluation", selection_rows, result, floor_provenance,
        ),
    }
    created: list[Path] = []
    transaction_dir: Path | None = None
    try:
        transaction_dir = Path(tempfile.mkdtemp(
            prefix=".s8c-result-transaction-",
            dir=str(paths[_TABLE_NAMES[0]].parent),
        ))
        for name, raw in staged.items():
            _exclusive_write(transaction_dir / f"{name}.json", raw)
        _sync_directory(transaction_dir)
        for name in _TABLE_NAMES:
            destination = paths[name]
            _exclusive_write(destination, staged[name])
            created.append(destination)
        marker = {
            "schema": "s8c-result-transaction/v1",
            "tables": {
                name: hashlib.sha256(staged[name]).hexdigest()
                for name in _TABLE_NAMES
            },
        }
        _exclusive_write(
            transaction_dir / "COMPLETE",
            (json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"),
        )
        _sync_directory(transaction_dir)
    except BaseException as exc:
        cleanup_errors: list[BaseException] = []
        for destination in created:
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_exc:
                cleanup_errors.append(cleanup_exc)
        if transaction_dir is not None:
            try:
                _remove_transaction_directory(transaction_dir)
            except _ResultTableError as cleanup_exc:
                cleanup_errors.append(cleanup_exc)
        if cleanup_errors:
            raise _ResultTableError("result table publication rollback failed") from cleanup_errors[0]
        if isinstance(exc, _ResultTableError):
            raise
        raise _ResultTableError("result table publication failed") from exc
    else:
        if transaction_dir is not None:
            _remove_transaction_directory(transaction_dir)
    return MappingProxyType(dict(paths))
