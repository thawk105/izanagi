"""Strict cell-level seed schedules for the 8c preregistration consumer.

``schedule_index`` is a cell ordinal in the closed range 0..5.  It is a
different index space from the within-iteration row index in
``s8b_oracle_manifest``, the observation ``seq`` in ``s8b_oracle_n_pilot``,
and the attempt index in ``s1_direct_comparison``.

This artifact is a cell-level seed schedule, not a complete block of
iterations, attempts, or observations.  ``consume_schedule`` does not track
usage history; one-to-one use for each launch is the responsibility of the
registry layer.

The module is deliberately a leaf.  All authority is supplied by the caller,
and every digest is over the complete, strictly validated authority projection.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import reflux_origin_artifacts


__all__ = [
    "ARMS",
    "GENERATOR_VERSION",
    "HOLDOUTS",
    "INITIAL_STATE_AUTHORITY_KEYS",
    "SCHEDULE_SCHEMA_VERSION",
    "SEARCH_SPACE_AUTHORITY_KEYS",
    "Schedule",
    "ScheduleCell",
    "ScheduleError",
    "consume_schedule",
    "initial_state_digest",
    "load_schedule",
    "regenerate",
    "search_space_digest",
    "validate_authority",
    "verify_exact_schedule_bytes",
    "verify_schedule",
    "verify_shared_search_space_and_initial_state",
]


SCHEDULE_SCHEMA_VERSION = "s8c-schedule/v1"
GENERATOR_VERSION = "s8c-schedule-generator/v1"
ARMS = ("on", "off", "swapped")
HOLDOUTS = ("H1", "H2")


# These are the caller-supplied search-space authorities.  They are kept as a
# closed set so a caller cannot silently omit a new input from the digest.
SEARCH_SPACE_AUTHORITY_KEYS = frozenset({
    "arms",
    "designated_source_context",
    "descriptor_bindings",
    "gating_spec",
    "holdout_bindings",
    "holdouts",
    "role_contracts",
    "role_files",
    "role_payload_allowlist",
    "workloads",
})

# These are the caller-supplied shared starting-state authorities.  The
# schedule has one shared digest per class, so cell-specific history is not
# represented here.
INITIAL_STATE_AUTHORITY_KEYS = frozenset({
    "attempt_policy",
    "baseline",
    "descriptor_binding",
    "gating_snapshot",
    "initial_role_metrics",
    "leakproof_context",
    "stop_policy",
    "whiteboard",
})

_AUTHORITY_KEYS = SEARCH_SPACE_AUTHORITY_KEYS | INITIAL_STATE_AUTHORITY_KEYS
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SEARCH_SPACE_DOMAIN = "s8c-schedule/search-space/v1"
_INITIAL_STATE_DOMAIN = "s8c-schedule/initial-state/v1"
_ORDER_DOMAIN = "s8c-schedule/order/v1"
_MAPPING_AUTHORITY_KEYS = frozenset({
    "attempt_policy",
    "baseline",
    "descriptor_binding",
    "descriptor_bindings",
    "gating_snapshot",
    "holdout_bindings",
    "initial_role_metrics",
    "leakproof_context",
    "role_contracts",
    "role_files",
    "role_payload_allowlist",
    "stop_policy",
    "workloads",
})
_SEQUENCE_AUTHORITY_KEYS = frozenset({
    "arms",
    "holdouts",
    "whiteboard",
})
_STRING_AUTHORITY_KEYS = frozenset({
    "designated_source_context",
    "gating_spec",
})


class ScheduleError(ValueError):
    """A schedule, authority, or schedule input failed a strict check."""


@dataclass(frozen=True)
class ScheduleCell:
    """One cell ordinal and its two shared authority digests.

    ``cell_ordinal`` is the artifact's ``schedule_index`` (0..5), and is not
    the row, observation, or attempt index used by any other layer.
    """

    cell_ordinal: int
    holdout: str
    arm: str
    search_space_sha256: str
    initial_state_sha256: str


@dataclass(frozen=True)
class Schedule:
    """The decoded, immutable six-cell seed schedule."""

    schema_version: str
    generator_version: str
    master_seed: str
    cells: tuple[ScheduleCell, ...]


def _fail(message: str) -> None:
    raise ScheduleError(message)


def _is_int(value: object) -> bool:
    return type(value) is int


def _is_sha256(value: object) -> bool:
    return type(value) is str and _HEX_SHA256.fullmatch(value) is not None


def _validate_canonical_value(value: object, *, key: str) -> None:
    try:
        reflux_origin_artifacts.canonical_json_bytes(value)
    except Exception as exc:  # the helper has its own strict error boundary
        raise ScheduleError(
            f"authority field {key!r} is not canonical JSON data"
        ) from exc


def _validate_non_degenerate_value(
    value: object,
    *,
    path: str,
    seen: set[int] | None = None,
) -> None:
    """Reject empty authority substance at every JSON container depth."""

    if type(value) is str:
        if value == "":
            _fail(f"authority value {path!r} must not be an empty string")
        return
    if isinstance(value, Mapping):
        if not value:
            _fail(f"authority value {path!r} must not be an empty mapping")
        identities = set() if seen is None else seen
        identity = id(value)
        if identity in identities:
            return
        next_seen = {*identities, identity}
        for key, item in value.items():
            _validate_non_degenerate_value(
                item,
                path=f"{path}[{key!r}]",
                seen=next_seen,
            )
        return
    if isinstance(value, (list, tuple)):
        if not value:
            _fail(f"authority value {path!r} must not be an empty array")
        identities = set() if seen is None else seen
        identity = id(value)
        if identity in identities:
            return
        next_seen = {*identities, identity}
        for index, item in enumerate(value):
            _validate_non_degenerate_value(
                item,
                path=f"{path}[{index}]",
                seen=next_seen,
            )


def validate_authority(authority: Mapping[str, Any]) -> None:
    """Validate the complete, non-degenerate authority before digesting it.

    The authority is flat by design.  The two closed key sets partition its
    fields, and both partitions are required even when a caller requests only
    one of the two digest functions.  This prevents a partial authority from
    becoming a silently accepted digest input.

    拒否側: 入れ子を含めてどれか一つでも空の mapping、配列、文字列があれば
    ``ScheduleError`` にする。
    受理側: 全 field が非退化のときだけ authority から digest を計算できる。
    """

    if not isinstance(authority, Mapping):
        _fail("authority must be a mapping")

    actual_keys = set(authority.keys())
    if actual_keys != _AUTHORITY_KEYS:
        missing = sorted(_AUTHORITY_KEYS - actual_keys)
        extra = sorted(actual_keys - _AUTHORITY_KEYS, key=repr)
        _fail(f"authority keys are not exact; missing={missing!r}, extra={extra!r}")

    if _MAPPING_AUTHORITY_KEYS | _SEQUENCE_AUTHORITY_KEYS | _STRING_AUTHORITY_KEYS != _AUTHORITY_KEYS:
        _fail("authority schema is internally incomplete")

    for key in sorted(_AUTHORITY_KEYS):
        value = authority[key]
        if key in _MAPPING_AUTHORITY_KEYS:
            if not isinstance(value, dict):
                _fail(f"authority field {key!r} must be a JSON object")
        elif key in _SEQUENCE_AUTHORITY_KEYS:
            if not isinstance(value, (list, tuple)):
                _fail(f"authority field {key!r} must be a JSON array")
        elif key in _STRING_AUTHORITY_KEYS:
            if type(value) is not str:
                _fail(f"authority field {key!r} must be a string")
        else:  # pragma: no cover - guarded by the schema-completeness check
            _fail(f"authority field {key!r} has no type rule")
        _validate_non_degenerate_value(value, path=key)
        _validate_canonical_value(value, key=key)


def _authority_digest(
    authority: Mapping[str, Any],
    keys: frozenset[str],
    domain: str,
) -> str:
    validate_authority(authority)
    preimage = {
        "authority": {key: authority[key] for key in sorted(keys)},
        "domain": domain,
    }
    try:
        raw = reflux_origin_artifacts.canonical_json_bytes(preimage)
    except Exception as exc:  # validate_authority already checked each field
        raise ScheduleError("authority digest canonicalization failed") from exc
    return hashlib.sha256(raw).hexdigest()


def search_space_digest(authority: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of every search-space authority field."""

    return _authority_digest(authority, SEARCH_SPACE_AUTHORITY_KEYS, _SEARCH_SPACE_DOMAIN)


def initial_state_digest(authority: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of every initial-state authority field."""

    return _authority_digest(authority, INITIAL_STATE_AUTHORITY_KEYS, _INITIAL_STATE_DOMAIN)


def _validate_master_seed(master_seed: object) -> None:
    if type(master_seed) is not str:
        _fail("master_seed must be a string")


def _order_key(master_seed: str, holdout: str, arm: str) -> bytes:
    try:
        raw = reflux_origin_artifacts.canonical_json_bytes({
            "arm": arm,
            "domain": _ORDER_DOMAIN,
            "holdout": holdout,
            "master_seed": master_seed,
        })
    except Exception as exc:  # all inputs are validated strings
        raise ScheduleError("schedule order canonicalization failed") from exc
    return hashlib.sha256(raw).digest()


def _ordered_cells(master_seed: str) -> list[tuple[str, str]]:
    candidates = [
        (holdout, arm)
        for holdout in HOLDOUTS
        for arm in ARMS
    ]
    return [
        (holdout, arm)
        for _digest, holdout, arm in sorted(
            (
                (_order_key(master_seed, holdout, arm), holdout, arm)
                for holdout, arm in candidates
            ),
            key=lambda item: (item[0], HOLDOUTS.index(item[1]), ARMS.index(item[2])),
        )
    ]


def regenerate(master_seed: str, *, authority: Mapping[str, Any]) -> bytes:
    """Generate canonical bytes for the six-cell seed schedule.

    The artifact's ``schedule_index`` is a cell ordinal (0..5), distinct from
    the iteration row, observation sequence, and attempt index in other
    artifacts.  This is a cell-level seed schedule, not a complete repetition
    or observation block, and no consumption history is recorded here.
    """

    _validate_master_seed(master_seed)
    validate_authority(authority)
    search_digest = search_space_digest(authority)
    initial_digest = initial_state_digest(authority)
    cells = [
        {
            "arm": arm,
            "holdout": holdout,
            "initial_state_sha256": initial_digest,
            "schedule_index": index,
            "search_space_sha256": search_digest,
        }
        for index, (holdout, arm) in enumerate(_ordered_cells(master_seed))
    ]
    artifact = {
        "cells": cells,
        "generator_version": GENERATOR_VERSION,
        "master_seed": master_seed,
        "schema_version": SCHEDULE_SCHEMA_VERSION,
    }
    try:
        return reflux_origin_artifacts.canonical_json_bytes(artifact)
    except Exception as exc:  # every artifact field is already canonical data
        raise ScheduleError("schedule artifact canonicalization failed") from exc


def load_schedule(path: str | Path) -> bytes:
    """Read schedule bytes without changing or normalizing them."""

    try:
        return Path(path).read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise ScheduleError("schedule path could not be read") from exc


def _decode_schedule(artifact_bytes: bytes) -> Schedule:
    if type(artifact_bytes) is not bytes:
        _fail("artifact_bytes must be bytes")
    try:
        value = reflux_origin_artifacts.strict_json_loads(artifact_bytes)
    except Exception as exc:
        raise ScheduleError("artifact bytes are not strict canonical JSON") from exc
    if not isinstance(value, dict):
        _fail("schedule artifact must be a JSON object")
    expected_top_keys = {
        "cells",
        "generator_version",
        "master_seed",
        "schema_version",
    }
    if set(value) != expected_top_keys:
        _fail("schedule artifact top-level keys are not exact")
    if type(value["schema_version"]) is not str or value["schema_version"] != SCHEDULE_SCHEMA_VERSION:
        _fail("schedule schema_version is invalid")
    if type(value["generator_version"]) is not str or value["generator_version"] != GENERATOR_VERSION:
        _fail("schedule generator_version is invalid")
    master_seed = value["master_seed"]
    _validate_master_seed(master_seed)
    raw_cells = value["cells"]
    if not isinstance(raw_cells, list) or len(raw_cells) != len(HOLDOUTS) * len(ARMS):
        _fail("schedule must contain exactly six cells")

    cell_keys = {
        "arm",
        "holdout",
        "initial_state_sha256",
        "schedule_index",
        "search_space_sha256",
    }
    cells: list[ScheduleCell] = []
    for raw_cell in raw_cells:
        if not isinstance(raw_cell, dict) or set(raw_cell) != cell_keys:
            _fail("schedule cell keys are not exact")
        ordinal = raw_cell["schedule_index"]
        holdout = raw_cell["holdout"]
        arm = raw_cell["arm"]
        search_digest = raw_cell["search_space_sha256"]
        initial_digest = raw_cell["initial_state_sha256"]
        if not _is_int(ordinal) or not 0 <= ordinal < 6:
            _fail("schedule_index must be an integer in 0..5")
        if type(holdout) is not str or holdout not in HOLDOUTS:
            _fail("schedule cell holdout is invalid")
        if type(arm) is not str or arm not in ARMS:
            _fail("schedule cell arm is invalid")
        if not _is_sha256(search_digest) or not _is_sha256(initial_digest):
            _fail("schedule cell digest is not lowercase SHA-256")
        cells.append(ScheduleCell(
            cell_ordinal=ordinal,
            holdout=holdout,
            arm=arm,
            search_space_sha256=search_digest,
            initial_state_sha256=initial_digest,
        ))

    schedule = Schedule(
        schema_version=value["schema_version"],
        generator_version=value["generator_version"],
        master_seed=master_seed,
        cells=tuple(cells),
    )
    _validate_schedule_object(schedule)
    return schedule


def _validate_schedule_object(schedule: Schedule) -> None:
    if type(schedule) is not Schedule:
        _fail("schedule must be a Schedule")
    if schedule.schema_version != SCHEDULE_SCHEMA_VERSION:
        _fail("schedule schema_version is invalid")
    if schedule.generator_version != GENERATOR_VERSION:
        _fail("schedule generator_version is invalid")
    _validate_master_seed(schedule.master_seed)
    if type(schedule.cells) is not tuple or len(schedule.cells) != 6:
        _fail("schedule must contain exactly six cells")
    ordinals: list[int] = []
    pairs: list[tuple[str, str]] = []
    for cell in schedule.cells:
        if type(cell) is not ScheduleCell:
            _fail("schedule contains a non-ScheduleCell value")
        if not _is_int(cell.cell_ordinal) or not 0 <= cell.cell_ordinal < 6:
            _fail("cell ordinal is outside 0..5")
        if type(cell.holdout) is not str or cell.holdout not in HOLDOUTS:
            _fail("schedule cell holdout is invalid")
        if type(cell.arm) is not str or cell.arm not in ARMS:
            _fail("schedule cell arm is invalid")
        if not _is_sha256(cell.search_space_sha256):
            _fail("schedule cell search-space digest is invalid")
        if not _is_sha256(cell.initial_state_sha256):
            _fail("schedule cell initial-state digest is invalid")
        ordinals.append(cell.cell_ordinal)
        pairs.append((cell.holdout, cell.arm))
    if set(ordinals) != set(range(6)) or len(ordinals) != len(set(ordinals)):
        _fail("schedule cell ordinals are not a 0..5 bijection")
    expected_pairs = {(holdout, arm) for holdout in HOLDOUTS for arm in ARMS}
    if set(pairs) != expected_pairs or len(pairs) != len(set(pairs)):
        _fail("schedule cells do not equal HOLDOUTS x ARMS")


def verify_exact_schedule_bytes(
    artifact_bytes: bytes,
    *,
    master_seed: str,
    authority: Mapping[str, Any],
) -> None:
    """Require canonical artifact bytes to equal independent regeneration."""

    _decode_schedule(artifact_bytes)
    expected = regenerate(master_seed, authority=authority)
    if artifact_bytes != expected:
        _fail("schedule bytes do not equal regenerated bytes")


def verify_shared_search_space_and_initial_state(
    schedule: Schedule,
    *,
    expected_search_space_sha256: str,
    expected_initial_state_sha256: str,
) -> None:
    """Require every cell to carry the supplied shared authority digests."""

    _validate_schedule_object(schedule)
    if not _is_sha256(expected_search_space_sha256):
        _fail("expected search-space digest is invalid")
    if not _is_sha256(expected_initial_state_sha256):
        _fail("expected initial-state digest is invalid")
    for cell in schedule.cells:
        if cell.search_space_sha256 != expected_search_space_sha256:
            _fail("schedule search-space digest is not shared authority")
        if cell.initial_state_sha256 != expected_initial_state_sha256:
            _fail("schedule initial-state digest is not shared authority")


def verify_schedule(
    artifact_bytes: bytes,
    *,
    master_seed: str,
    authority: Mapping[str, Any],
    expected_search_space_sha256: str | None = None,
    expected_initial_state_sha256: str | None = None,
) -> Schedule:
    """Verify exact bytes and shared authority before returning a schedule.

    When an expected digest is omitted, it is derived from the validated
    authority for compatibility with the original call shape.  A supplied
    digest is an independent external expectation for the shared check.
    """

    validate_authority(authority)
    if expected_search_space_sha256 is None:
        expected_search_space_sha256 = search_space_digest(authority)
    if expected_initial_state_sha256 is None:
        expected_initial_state_sha256 = initial_state_digest(authority)
    verify_exact_schedule_bytes(
        artifact_bytes,
        master_seed=master_seed,
        authority=authority,
    )
    schedule = _decode_schedule(artifact_bytes)
    verify_shared_search_space_and_initial_state(
        schedule,
        expected_search_space_sha256=expected_search_space_sha256,
        expected_initial_state_sha256=expected_initial_state_sha256,
    )
    return schedule


def consume_schedule(
    artifact_bytes: bytes,
    *,
    master_seed: str,
    authority: Mapping[str, Any],
    schedule_index: int,
    expected_search_space_sha256: str | None = None,
    expected_initial_state_sha256: str | None = None,
) -> ScheduleCell:
    """Verify the artifact and return one cell ordinal without usage tracking."""

    schedule = verify_schedule(
        artifact_bytes,
        master_seed=master_seed,
        authority=authority,
        expected_search_space_sha256=expected_search_space_sha256,
        expected_initial_state_sha256=expected_initial_state_sha256,
    )
    if not _is_int(schedule_index) or not 0 <= schedule_index < len(schedule.cells):
        _fail("schedule_index must be an integer in 0..5")
    for cell in schedule.cells:
        if cell.cell_ordinal == schedule_index:
            return cell
    _fail("schedule_index is absent from the verified schedule")
