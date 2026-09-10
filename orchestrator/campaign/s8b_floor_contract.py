# -*- coding: utf-8 -*-
"""S8b floor protocol / cell / schedule の共有 validation leaf。

stdlib と ``perf_preflight``、``s8b_experiment_numbers`` のみに依存し、campaign 内の
それ以外の module は import しない。発行側と検証側が同じ protocol 正規化、
``verify_floor_artifact`` 用射影、
freeze 由来セル集合、決定的 schedule を循環 import なしで利用するための単一源である。

``validate_protocol`` の ``contract_sha256_lookup`` は env registry の単一源を leaf 内へ複製
しないための注入点であり、runtime bypass ではない。producer / live admission の呼び手は
検証時点の current contract hash を、publish 済み artifact の read-only consumer は記録 hash
から解決した contract hash を返す。いずれも未登録 tag は ``FloorContractError`` で拒否する。
"""
from __future__ import annotations

import hashlib
import json
import math
import posixpath
import random
from collections.abc import Callable, Mapping, Sequence
from pathlib import PurePosixPath
from typing import Optional

from ..calibrator import perf_preflight as _perf_preflight
from . import s8b_experiment_numbers as _experiment_numbers


# protocol は凍結 v2、admission receipt を必須化した manifest は v3。
# registry 有効時の producer は result v5、互換用の既定 alias は v4 のまま。
# freeze schema は v1 freeze を読むため据置。
PROTOCOL_SCHEMA = "s8b-floor-protocol/v2"
FREEZE_SCHEMA = "8b-holdout-freeze/v1"
SCHEDULE_ALGORITHM = "round-permutation/v2"
LEGACY_RESULT_SCHEMA = "s8b-floor-result/v4"
RESULT_SCHEMA = LEGACY_RESULT_SCHEMA
RESULT_SCHEMA_V5 = "s8b-floor-result/v5"
READABLE_RESULT_SCHEMAS = frozenset({
    LEGACY_RESULT_SCHEMA,
    RESULT_SCHEMA_V5,
})
MANIFEST_SCHEMA = "s8b-floor-manifest/v3"
JOURNAL_SCHEMA = "s8b-floor-journal/v3"
FORMULA_ID = "s8b-floor-stats/v2"
FLOOR_HOLDOUT_ADMISSION_SCHEMA = "s8b-floor-holdout-admission-receipt/v1"

# Campaign entry で捕捉し、floor claim v2 へ canonical list として記録する
# refreeze 不適格 seam の閉集合。producer と admission validator の単一源である。
REFREEZE_DISQUALIFYING_SEAM_NAMES = frozenset({
    "measure_fn", "probe_fn", "sleep_fn", "monotonic_fn", "prepare_fn",
    "now_fn", "host_provenance_fn", "process_identity_fn",
    "execution_receipt_fn", "build_fn", "repo_root",
    "fetchcontent_base_dir",
    "after_certificate_issued_fn", "durable_root_policy",
    "_floor_preflight_fn", "perf_preflight_fn", "_holdout_repo_root",
    "_holdout_signature_source",
})

_PROTOCOL_KEYS = frozenset({
    "schema", "formula", "env_tag", "ccbench_pin", "freeze", "stock_configuration",
    "n_sessions", "reps", "master_seed", "schedule_algorithm", "extime_s",
    "wired_min_rel_floor", "retry_slots_per_cell",
    "session_cv_max", "cell_cv_max", "scale_adequacy_rel_tolerance",
    "allowed_excluded_reasons", "contract_sha256",
})
_AI_RESEAL_MUTABLE_FIELDS = frozenset({"contract_sha256", "ccbench_pin"})
_AI_RESEAL_INHERITED_FIELDS = _PROTOCOL_KEYS - _AI_RESEAL_MUTABLE_FIELDS
assert len(_AI_RESEAL_MUTABLE_FIELDS) == 2
assert len(_AI_RESEAL_INHERITED_FIELDS) == 16
assert _AI_RESEAL_MUTABLE_FIELDS | _AI_RESEAL_INHERITED_FIELDS == _PROTOCOL_KEYS
assert not (_AI_RESEAL_MUTABLE_FIELDS & _AI_RESEAL_INHERITED_FIELDS)
_FREEZE_RECORD_KEYS = frozenset({"path", "sha256"})
_FLOOR_HOLDOUT_ADMISSION_KEYS = frozenset({
    "schema", "campaign_run_id", "run_relpath", "mode", "protocol_sha256",
    "freeze_sha256", "manifest_sha256", "claim_identities",
    "admission_row_count", "attempt_row_count", "ledger_projection_sha256",
})
_MANIFEST_KEYS = frozenset({
    "schema_version", "protocol_sha256", "freeze", "freeze_sha256", "env_tag",
    "ccbench_pin", "stock_configuration", "schedule_algorithm", "master_seed",
    "n_sessions", "reps", "extime_s", "session_cv_max", "cell_cv_max", "cells",
    "binaries", "schedule",
})
_MANIFEST_CELL_KEYS = frozenset({
    "cell_id", "holdout_id", "configuration_id", "records", "threads", "workload",
})
_SCHEDULE_KEYS = frozenset({"seq", "round", "cell_id"})
_RESULT_V4_KEYS = frozenset({
    "schema", "formula", "mode", "eligible_for_refreeze", "env_tag", "ccbench_pin",
    "protocol_sha256", "freeze_sha256", "manifest_sha256", "stock_configuration",
    "wired_min_rel_floor", "reps", "n_sessions", "scale_adequacy_rel_tolerance",
    "holdouts", "configurations", "binaries", "config", "sessions", "cells", "floors",
    "wall_ledger", "excluded", "attempts", "holdout_admission",
})
_RESULT_KEYS = _RESULT_V4_KEYS
_RESULT_V5_KEYS = _RESULT_V4_KEYS | {"attempt_registry"}
_RESULT_KEYS_BY_SCHEMA = {
    LEGACY_RESULT_SCHEMA: _RESULT_V4_KEYS,
    RESULT_SCHEMA_V5: _RESULT_V5_KEYS,
}
_HEX64 = frozenset("0123456789abcdef")

# 承認済み標本設計の凍結値。共有 validator が別実験への変質を開始前に拒否する。
_APPROVED_N_SESSIONS = 8
_APPROVED_RETRY_SLOTS = 2
_APPROVED_SESSION_CV_MAX = "0.10"
_APPROVED_CELL_CV_MAX = "0.15"
_APPROVED_SCALE_ADEQUACY = "0.10"
_APPROVED_REASONS = (
    "competing_process",
    "launch_failure",
    "nonfinite_or_partial_output",
    "performance_anomaly",
)

_FLOOR_ARTIFACT_PROTOCOL_KEYS = (
    "formula",
    "n_sessions",
    "reps",
    "stock_configuration",
    "wired_min_rel_floor",
    "session_cv_max",
    "cell_cv_max",
)

# calibrator.runner の production command が記録する perf event 集合。runner 側が
# drift した場合、issuer の raw→portable 射影が fail-closed で止める。
_RUN_CMD_PERF_EVENTS = (
    "LLC-load-misses", "LLC-loads", "instructions", "cycles",
)


class FloorContractError(RuntimeError):
    """floor 共有契約を検証できない場合の fail-closed 拒否。"""


def _official_perf_evidence_keys(receipt: object | None) -> frozenset[str]:
    """official receipt から degraded-only evidence keys を返す。"""

    try:
        use_perf = _perf_preflight.use_perf_from_receipt(receipt)
    except _perf_preflight.PerfPreflightError as exc:
        raise FloorContractError(f"perf_preflight receipt が不正: {exc}") from exc
    if receipt is not None and use_perf:
        raise FloorContractError("official mode の available perf_preflight receipt を拒否する")
    if receipt is None:
        return frozenset()
    return frozenset({"perf_preflight", "perf_observation"})


def manifest_perf_validation_context(
        document: Mapping[str, object]) -> tuple[object, Mapping[str, object]]:
    """manifest 自身から degraded observation の必須検証 context を導出する。"""

    binaries = document.get("binaries") if isinstance(document, Mapping) else None
    run_cmd: object = ("floor-manifest-no-perf",)
    if isinstance(binaries, Mapping):
        for cell_id in sorted(binaries, key=str):
            record = binaries[cell_id]
            if isinstance(record, Mapping) and isinstance(record.get("binary"), str):
                run_cmd = (record["binary"],)
                break
    return run_cmd, {
        "ipc": None,
        "llc_miss_rate": None,
        "manifest": document,
    }


def result_keys_for_mode(
        mode: object, *, schema: object = LEGACY_RESULT_SCHEMA,
        perf_preflight: object | None = None) -> frozenset[str]:
    """result schema / mode 条件付き top-level exact key 集合を返す。"""

    if schema == LEGACY_RESULT_SCHEMA:
        base_keys = _RESULT_KEYS_BY_SCHEMA[LEGACY_RESULT_SCHEMA]
    elif schema == RESULT_SCHEMA_V5:
        base_keys = _RESULT_KEYS_BY_SCHEMA[RESULT_SCHEMA_V5]
    else:
        raise FloorContractError("result.schema が readable schema でない")

    if mode == "pilot":
        # Legacy pilot result は receipt の値によらず perf_preflight を必須とする。
        return base_keys | {"perf_preflight"}
    if mode == "official":
        return base_keys | _official_perf_evidence_keys(perf_preflight)
    raise FloorContractError("result.mode が exact {'pilot','official'} でない")


def manifest_keys_for_mode(
        mode: object, *, perf_preflight: object | None = None) -> frozenset[str]:
    """manifest v3 の receipt 条件付き top-level exact key 集合を返す。"""

    if mode == "pilot":
        # Legacy pilot manifest は receipt 無し/有りの二つの exact 集合を許す。
        evidence_keys = {"perf_preflight"} if perf_preflight is not None else set()
        return _MANIFEST_KEYS | evidence_keys
    if mode == "official":
        return _MANIFEST_KEYS | _official_perf_evidence_keys(perf_preflight)
    raise FloorContractError("manifest.mode が exact {'pilot','official'} でない")


def validate_session_start_authorizations(
    records: Sequence[Mapping[str, object]], *,
    schedule: Sequence[Mapping[str, object]], retry_slots_per_cell: int,
) -> dict[str, Mapping[str, object]]:
    """planned/retry ``session-start`` の正準 authorization を完全検査する。

    attempt ID は自己申告として扱わず、planned は ``cell_id::seqN``、retry は
    ``cell_id::retryN`` を再導出する。seq、attempt ID、retry 枠の一意性も同時に要求する。
    """

    if (
        not isinstance(records, Sequence)
        or isinstance(records, (str, bytes, bytearray))
        or not isinstance(schedule, Sequence)
        or isinstance(schedule, (str, bytes, bytearray))
        or type(retry_slots_per_cell) is not int
        or retry_slots_per_cell < 0
    ):
        raise FloorContractError("session-start authorization 入力が不正")
    planned_by_seq: dict[int, Mapping[str, object]] = {}
    for row in schedule:
        if not isinstance(row, Mapping) or set(row) != set(_SCHEDULE_KEYS):
            raise FloorContractError("authorization schedule の exact key 集合が不一致")
        seq = row["seq"]
        if type(seq) is not int or seq < 0 or seq in planned_by_seq:
            raise FloorContractError("authorization schedule の seq が不正/重複")
        planned_by_seq[seq] = row

    by_attempt: dict[str, Mapping[str, object]] = {}
    seen_seq: set[int] = set()
    seen_retry: set[tuple[str, int]] = set()
    for record in records:
        if not isinstance(record, Mapping) or record.get("event") != "session-start":
            raise FloorContractError("authorization record が session-start でない")
        seq = record.get("seq")
        attempt_id = record.get("attempt_id")
        cell_id = record.get("cell_id")
        if (
            type(seq) is not int or seq < 0 or seq in seen_seq
            or type(attempt_id) is not str or not attempt_id or attempt_id in by_attempt
            or type(cell_id) is not str or not cell_id
        ):
            raise FloorContractError("session-start の seq/attempt/cell が不正または重複")
        seen_seq.add(seq)
        kind = record.get("kind")
        if kind == "planned":
            scheduled = planned_by_seq.get(seq)
            if (
                scheduled is None
                or record.get("cell_id") != scheduled.get("cell_id")
                or record.get("round") != scheduled.get("round")
                or record.get("retry_ordinal") is not None
                or record.get("trigger") is not None
                or attempt_id != f"{cell_id}::seq{seq}"
            ):
                raise FloorContractError("planned session-start が正準 schedule/attempt と不一致")
        elif kind == "retry":
            ordinal = record.get("retry_ordinal")
            retry_key = (cell_id, ordinal)
            if (
                seq in planned_by_seq
                or seq < len(schedule)
                or type(ordinal) is not int
                or not 1 <= ordinal <= retry_slots_per_cell
                or attempt_id != f"{cell_id}::retry{ordinal}"
                or retry_key in seen_retry
            ):
                raise FloorContractError("retry session-start が正準 seq/ordinal/attempt と不一致")
            seen_retry.add(retry_key)
        else:
            raise FloorContractError("session-start.kind が未知")
        by_attempt[attempt_id] = record
    return by_attempt


def validate_manifest_v3(
    document: Mapping[str, object], *, protocol: Mapping[str, object],
    protocol_sha256: str, freeze_sha256: str,
    expected_cells: Sequence[Mapping[str, object]],
    expected_schedule: Sequence[Mapping[str, object]], mode: str,
    run_cmd: object, leading_indicators: Mapping[str, object],
) -> dict[str, object]:
    """manifest v3 の exact shape と protocol/cells/binaries/schedule 束縛を検査する。"""

    received_keys = set(document) if isinstance(document, Mapping) else set()
    receipt = document.get("perf_preflight") if isinstance(document, Mapping) else None
    expected_keys = manifest_keys_for_mode(mode, perf_preflight=receipt)
    if received_keys != set(expected_keys):
        raise FloorContractError("manifest v3 の mode 条件付き exact key 集合が不一致")
    if document["schema_version"] != MANIFEST_SCHEMA:
        raise FloorContractError(f"manifest.schema_version が {MANIFEST_SCHEMA} でない")
    mirrors = {
        "protocol_sha256": protocol_sha256,
        "freeze": dict(protocol["freeze"]),
        "freeze_sha256": freeze_sha256,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"],
        "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "extime_s": protocol["extime_s"],
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
    }
    for key, expected in mirrors.items():
        if document[key] != expected or type(document[key]) is not type(expected):
            raise FloorContractError(f"manifest.{key} が protocol/anchor と不一致")
    if "perf_observation" in expected_keys:
        try:
            normalized_observation = _perf_preflight.validate_perf_observation(
                document.get("perf_observation"), run_cmd=run_cmd,
                leading_indicators=leading_indicators,
            )
        except _perf_preflight.PerfPreflightError as exc:
            raise FloorContractError(f"manifest.perf_observation が不正: {exc}") from exc
        if normalized_observation["preflight"] != receipt:
            raise FloorContractError(
                "manifest.perf_observation.preflight が perf_preflight と不一致"
            )
    if type(document["cells"]) is not list:
        raise FloorContractError("manifest.cells が list でない")
    for cell in document["cells"]:
        if not isinstance(cell, Mapping) or set(cell) != set(_MANIFEST_CELL_KEYS):
            raise FloorContractError("manifest cell の exact key 集合が不一致")
    if document["cells"] != list(expected_cells):
        raise FloorContractError("manifest.cells が外部期待列と不一致")
    if type(document["schedule"]) is not list:
        raise FloorContractError("manifest.schedule が list でない")
    for row in document["schedule"]:
        if not isinstance(row, Mapping) or set(row) != set(_SCHEDULE_KEYS):
            raise FloorContractError("manifest schedule row の exact key 集合が不一致")
    if document["schedule"] != list(expected_schedule):
        raise FloorContractError("manifest.schedule が外部期待列と不一致")
    binaries = document["binaries"]
    cell_by_id = {cell["cell_id"]: cell for cell in expected_cells}
    if len(cell_by_id) != len(expected_cells):
        raise FloorContractError("expected_cells の cell_id が重複")
    if not isinstance(binaries, Mapping) or set(binaries) != set(cell_by_id):
        raise FloorContractError("manifest.binaries の cell 集合が cells と不一致")
    for cell_id, record in binaries.items():
        if not isinstance(record, Mapping):
            raise FloorContractError(f"manifest.binaries[{cell_id}] が object でない")
        cell = cell_by_id[cell_id]
        for field in ("cell_id", "holdout_id", "configuration_id"):
            if record.get(field) != cell[field] or type(record.get(field)) is not str:
                raise FloorContractError(
                    f"manifest.binaries[{cell_id}].{field} が cell と不一致"
                )
    return json.loads(json.dumps(
        dict(document), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ))


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and all(char in _HEX64 for char in value)
    )


def _canonical_relative_path(value: object, *, field: str) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise FloorContractError(f"{field} が canonical POSIX relative path でない")
    path = PurePosixPath(value)
    if (
        path.is_absolute() or value == "." or "." in path.parts or ".." in path.parts
        or str(path) != value
    ):
        raise FloorContractError(f"{field} が canonical POSIX relative path でない")
    return value


def validate_floor_holdout_admission_receipt(value: object) -> dict:
    """floor holdout admission receipt の exact shape と scalar 束縛を検証する。"""

    if not isinstance(value, Mapping) or set(value) != set(_FLOOR_HOLDOUT_ADMISSION_KEYS):
        raise FloorContractError("holdout admission receipt の exact key 集合が不一致")
    if value["schema"] != FLOOR_HOLDOUT_ADMISSION_SCHEMA:
        raise FloorContractError("holdout admission receipt schema が不一致")
    for field in ("campaign_run_id", "mode"):
        if type(value[field]) is not str or not value[field]:
            raise FloorContractError(f"holdout admission {field} が空でない str でない")
    _canonical_relative_path(value["run_relpath"], field="holdout admission run_relpath")
    for field in (
        "protocol_sha256", "freeze_sha256", "manifest_sha256",
        "ledger_projection_sha256",
    ):
        if not _is_sha256(value[field]):
            raise FloorContractError(f"holdout admission {field} が SHA-256 でない")
    identities = value["claim_identities"]
    if not isinstance(identities, Mapping) or not identities:
        raise FloorContractError("holdout admission claim_identities が非空 mapping でない")
    normalized_identities: dict[str, str] = {}
    for cell_id, digest in identities.items():
        if type(cell_id) is not str or not cell_id or not _is_sha256(digest):
            raise FloorContractError("holdout admission claim identity が不正")
        normalized_identities[cell_id] = digest
    for field in ("admission_row_count", "attempt_row_count"):
        if type(value[field]) is not int or value[field] < 0:
            raise FloorContractError(f"holdout admission {field} が非負 exact int でない")
    if value["admission_row_count"] != len(normalized_identities):
        raise FloorContractError(
            "holdout admission admission_row_count と claim_identities 件数が不一致"
        )
    normalized = dict(value)
    normalized["claim_identities"] = normalized_identities
    try:
        return json.loads(json.dumps(
            normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ))
    except (TypeError, ValueError) as exc:
        raise FloorContractError("holdout admission receipt が canonical JSON 化不能") from exc


def _pos_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FloorContractError(f"protocol.{field} が正整数でない")
    return value


def _non_neg_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FloorContractError(f"protocol.{field} が非負整数でない")
    return value


def _non_empty_str(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FloorContractError(f"protocol.{field} が空でない文字列でない")
    return value


def _pinned(value, expected, *, field: str):
    """承認凍結値との完全一致を要求する。"""
    if value != expected or type(value) is not type(expected):
        raise FloorContractError(
            f"protocol.{field} が承認凍結値と不一致 (受領 {value!r} != 承認 {expected!r})"
        )
    return value


def validate_protocol(
        document: Mapping, *, contract_sha256_lookup: Callable[[str], str]) -> dict:
    """protocol を full validate し、canonical hash 入力となる正規化 dict を返す。

    未知 key・欠落・型不正・版不一致・承認 pin 不一致・env contract hash 不一致をすべて
    fail-closed で拒否する。戻り値は exact 18-key で、JSON canonicalization 前の唯一の
    正規化表現である。
    """
    if not isinstance(document, Mapping):
        raise FloorContractError("protocol が object でない")
    keys = set(document)
    if keys != set(_PROTOCOL_KEYS):
        missing = sorted(set(_PROTOCOL_KEYS) - keys)
        unknown = sorted(keys - set(_PROTOCOL_KEYS))
        raise FloorContractError(
            f"protocol の key 集合が不一致 (欠落={missing} 未知={unknown})"
        )

    if document["schema"] != PROTOCOL_SCHEMA:
        raise FloorContractError(
            f"protocol.schema が {PROTOCOL_SCHEMA} でない (v1 の交差受理を拒否)"
        )
    if document["schedule_algorithm"] != SCHEDULE_ALGORITHM:
        raise FloorContractError(
            f"protocol.schedule_algorithm が {SCHEDULE_ALGORITHM} でない"
        )

    formula = _non_empty_str(document["formula"], field="formula")
    if formula != FORMULA_ID:
        raise FloorContractError(
            f"protocol.formula ({formula}) が s8b_floor_stats.FORMULA_ID "
            f"({FORMULA_ID}) と不一致"
        )

    env_tag = _non_empty_str(document["env_tag"], field="env_tag")
    contract_sha256 = _non_empty_str(document["contract_sha256"], field="contract_sha256")
    try:
        expected_contract_sha256 = contract_sha256_lookup(env_tag)
    except FloorContractError:
        raise
    except Exception as exc:
        raise FloorContractError(
            f"protocol.env_tag の env contract を照合できない: {exc}"
        ) from exc
    if contract_sha256 != expected_contract_sha256:
        raise FloorContractError(
            "protocol.contract_sha256 が contract_sha256_lookup の選択した contract と不一致"
        )
    ccbench_pin = _non_empty_str(document["ccbench_pin"], field="ccbench_pin")
    stock_configuration = _non_empty_str(
        document["stock_configuration"], field="stock_configuration",
    )
    master_seed = _non_empty_str(document["master_seed"], field="master_seed")

    freeze_record = document["freeze"]
    if not isinstance(freeze_record, Mapping) or set(freeze_record) != set(_FREEZE_RECORD_KEYS):
        raise FloorContractError("protocol.freeze schema が {path, sha256} でない")
    freeze_path = _non_empty_str(freeze_record["path"], field="freeze.path")
    freeze_sha = freeze_record["sha256"]
    if (not isinstance(freeze_sha, str) or len(freeze_sha) != 64
            or any(ch not in "0123456789abcdef" for ch in freeze_sha)):
        raise FloorContractError("protocol.freeze.sha256 が SHA-256 でない")

    n_sessions = _pinned(
        document["n_sessions"], _APPROVED_N_SESSIONS, field="n_sessions",
    )
    reps = _pinned(
        document["reps"], _experiment_numbers.APPROVED_REPS, field="reps",
    )
    retry_slots_per_cell = _pinned(
        document["retry_slots_per_cell"], _APPROVED_RETRY_SLOTS,
        field="retry_slots_per_cell",
    )
    session_cv_max = _pinned(
        document["session_cv_max"], _APPROVED_SESSION_CV_MAX, field="session_cv_max",
    )
    cell_cv_max = _pinned(
        document["cell_cv_max"], _APPROVED_CELL_CV_MAX, field="cell_cv_max",
    )
    scale_adequacy_rel_tolerance = _pinned(
        document["scale_adequacy_rel_tolerance"], _APPROVED_SCALE_ADEQUACY,
        field="scale_adequacy_rel_tolerance",
    )

    extime_s = _pinned(
        document["extime_s"], _experiment_numbers.APPROVED_EXTIME_S, field="extime_s",
    )

    wired_min_rel_floor = document["wired_min_rel_floor"]
    if (isinstance(wired_min_rel_floor, bool)
            or not isinstance(wired_min_rel_floor, (int, float))
            or not math.isfinite(float(wired_min_rel_floor))
            or not (0.0 < float(wired_min_rel_floor) <= 1.0)):
        raise FloorContractError("protocol.wired_min_rel_floor が (0,1] の有限数でない")
    wired_min_rel_floor = float(wired_min_rel_floor)

    reasons_raw = document["allowed_excluded_reasons"]
    if reasons_raw != list(_APPROVED_REASONS):
        raise FloorContractError(
            "protocol.allowed_excluded_reasons が承認凍結 4 行 (固定順) と不一致: "
            f"受領 {reasons_raw!r}"
        )

    return {
        "schema": PROTOCOL_SCHEMA,
        "formula": formula,
        "env_tag": env_tag,
        "ccbench_pin": ccbench_pin,
        "freeze": {"path": freeze_path, "sha256": freeze_sha},
        "stock_configuration": stock_configuration,
        "n_sessions": n_sessions,
        "reps": reps,
        "master_seed": master_seed,
        "schedule_algorithm": SCHEDULE_ALGORITHM,
        "extime_s": extime_s,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": retry_slots_per_cell,
        "session_cv_max": session_cv_max,
        "cell_cv_max": cell_cv_max,
        "scale_adequacy_rel_tolerance": scale_adequacy_rel_tolerance,
        "allowed_excluded_reasons": list(_APPROVED_REASONS),
        "contract_sha256": contract_sha256,
    }


def canonical_protocol_sha256(normalized_protocol: Mapping) -> str:
    """full-validated 正規化戻り値の canonical JSON SHA-256 を返す。"""
    try:
        raw = json.dumps(
            normalized_protocol,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FloorContractError(f"canonical JSON に変換できない: {exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _canonical_protocol_field_bytes(value, *, field: str) -> bytes:
    """AI reseal の継承比較用に field 値を型込み canonical bytes へ写す。"""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise FloorContractError(
            f"protocol.{field} を継承比較用 canonical JSON に変換できない: {exc}"
        ) from exc


def validate_ai_reseal_inheritance(
        predecessor: Mapping, successor: Mapping) -> None:
    """AI reseal が可変 2 field 以外の 16 field を byte-exact 継承したか検証する。"""
    for label, document in (("predecessor", predecessor), ("successor", successor)):
        if not isinstance(document, Mapping) or set(document) != set(_PROTOCOL_KEYS):
            raise FloorContractError(
                f"AI reseal {label} が exact 18-field protocol でない"
            )
    changed = []
    for field in sorted(_AI_RESEAL_INHERITED_FIELDS):
        before = _canonical_protocol_field_bytes(predecessor[field], field=field)
        after = _canonical_protocol_field_bytes(successor[field], field=field)
        if before != after:
            changed.append(field)
    if changed:
        raise FloorContractError(
            f"AI reseal が人間専有 field を変更した: {changed}"
        )


def project_protocol_for_floor_artifact(protocol: Mapping) -> dict:
    """full-validated protocol を ``verify_floor_artifact`` 用 7 scalar へ射影する。"""
    return {key: protocol[key] for key in _FLOOR_ARTIFACT_PROTOCOL_KEYS}


def build_portable_run_cmd(
        *, binary, workload, records, threads, extime_s, clocks_per_us,
        numactl, use_perf: bool = True) -> tuple[str, ...]:
    """検証・artifact 記録用の portable benchmark argv を決定論的に構築する。

    ``binary`` は out-root 相対の portable store path とし、runtime absolute path は
    受理しない。workload flag は key の辞書順で固定するため、入力 Mapping の挿入順に
    依存しない。戻り値は表示・照合専用であり、再実行 API ではない。
    """
    if (not isinstance(binary, str) or not binary or binary.startswith("/")
            or "\\" in binary or "\x00" in binary
            or posixpath.normpath(binary) != binary
            or binary in {".", ".."}
            or any(part in {"", ".", ".."} for part in binary.split("/"))):
        raise FloorContractError("run_cmd.binary が canonical portable relative path でない")
    for field, value in {
            "records": records, "threads": threads, "extime_s": extime_s,
            "clocks_per_us": clocks_per_us,
    }.items():
        if type(value) is not int or value <= 0:
            raise FloorContractError(f"run_cmd.{field} が正整数でない")
    if not isinstance(workload, Mapping) or not workload:
        raise FloorContractError("run_cmd.workload が空でない Mapping でない")
    for key, value in workload.items():
        if (not isinstance(key, str) or not key or not isinstance(value, str)
                or not value or "\x00" in key or "\x00" in value):
            raise FloorContractError("run_cmd.workload が空でない str→str でない")
    if not isinstance(numactl, tuple):
        raise FloorContractError("run_cmd.numactl が tuple でない")
    if not all(isinstance(token, str) and token and "\x00" not in token
               for token in numactl):
        raise FloorContractError("run_cmd.numactl に空または非 str token がある")
    if type(use_perf) is not bool:
        raise FloorContractError("run_cmd.use_perf が bool でない")

    argv = [*numactl]
    if use_perf:
        argv.extend([
            "perf", "stat", "-e", ",".join(_RUN_CMD_PERF_EVENTS), "--",
        ])
    argv.extend([
        binary,
        f"-thread_num={threads}",
        f"-ycsb_tuple_num={records}",
        f"-extime={extime_s}",
        f"-clocks_per_us={clocks_per_us}",
    ])
    argv.extend(f"-{key}={workload[key]}" for key in sorted(workload))
    return tuple(argv)


def _holdout_workload(holdout: Mapping, *, holdout_id: str) -> dict:
    records = holdout.get("records")
    threads = holdout.get("threads")
    workload = holdout.get("ycsb")
    if (isinstance(records, bool) or not isinstance(records, int) or records <= 0
            or isinstance(threads, bool) or not isinstance(threads, int) or threads <= 0):
        raise FloorContractError(f"holdout {holdout_id} の records/threads が正整数でない")
    if not isinstance(workload, Mapping) or not workload:
        raise FloorContractError(f"holdout {holdout_id} の ycsb が空でない object でない")
    for key, value in workload.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise FloorContractError(f"holdout {holdout_id} の ycsb が str→str でない")
    return {"records": records, "threads": threads, "workload": dict(workload)}


def enumerate_cells(freeze: Mapping, *, stock_configuration: str) -> list[dict]:
    """freeze から holdout × configuration セルを決定論的に列挙する。"""
    holdouts_obj = freeze.get("holdouts")
    if not isinstance(holdouts_obj, Mapping) or not holdouts_obj:
        raise FloorContractError("freeze.holdouts が空でない object でない")
    holdout_ids = sorted(holdouts_obj)

    configurations: Optional[list[str]] = None
    per_holdout: dict[str, dict] = {}
    for holdout_id in holdout_ids:
        holdout = holdouts_obj[holdout_id]
        if not isinstance(holdout, Mapping):
            raise FloorContractError(f"holdout {holdout_id} が object でない")
        binding = holdout.get("variant_binding")
        entries = binding.get("entries") if isinstance(binding, Mapping) else None
        if not isinstance(entries, Mapping) or not entries:
            raise FloorContractError(
                f"holdout {holdout_id} の variant_binding.entries が空でない object でない"
            )
        entry_ids = sorted(entries)
        if configurations is None:
            configurations = entry_ids
        elif entry_ids != configurations:
            raise FloorContractError(
                f"holdout {holdout_id} の構成集合が他 holdout と不一致"
            )
        if stock_configuration not in entries:
            raise FloorContractError(
                f"holdout {holdout_id} の entries に stock_configuration "
                f"({stock_configuration}) がない"
            )
        per_holdout[holdout_id] = _holdout_workload(holdout, holdout_id=holdout_id)

    assert configurations is not None
    if "sort_best" not in configurations:
        raise FloorContractError("各 holdout の構成集合に sort_best がない")
    cells: list[dict] = []
    for holdout_id in holdout_ids:
        info = per_holdout[holdout_id]
        for configuration_id in configurations:
            cells.append({
                "cell_id": f"{holdout_id}::{configuration_id}",
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "records": info["records"],
                "threads": info["threads"],
                "workload": info["workload"],
            })
    return cells


def expected_cells_from_cells(cells) -> dict[str, list]:
    """検証済み cell 列から ``expected_cells`` の exact mapping を作る。"""
    expected_cells: dict[str, list] = {}
    for cell in cells:
        expected_cells.setdefault(cell["holdout_id"], []).append(cell["configuration_id"])
    for holdout_id in expected_cells:
        expected_cells[holdout_id] = sorted(expected_cells[holdout_id])
    return expected_cells


def derive_expected_cells(freeze: Mapping, *, stock_configuration: str) -> dict[str, list]:
    """ratified freeze の holdout/variant binding から expected cells を独立導出する。"""
    cells = enumerate_cells(freeze, stock_configuration=stock_configuration)
    return expected_cells_from_cells(cells)


def _round_seed(master_seed: str, round_no: int) -> int:
    """round 種: sha256(f"{master_seed}/{r}") の先頭 8 byte、big-endian。"""
    payload = f"{master_seed}/{round_no}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def build_schedule(*, cells: list[dict], master_seed: str, n_sessions: int) -> list[dict]:
    """round ごとに全 cell_id を seed 置換した決定的 session 列を返す。"""
    if not isinstance(n_sessions, int) or isinstance(n_sessions, bool) or n_sessions <= 0:
        raise FloorContractError("build_schedule: n_sessions が正整数でない")
    cell_ids = sorted(cell["cell_id"] for cell in cells)
    if len(set(cell_ids)) != len(cell_ids):
        raise FloorContractError("build_schedule: cell_id が重複している")
    if not cell_ids:
        raise FloorContractError("build_schedule: cells が空")
    rows: list[dict] = []
    for round_no in range(1, n_sessions + 1):
        permuted = list(cell_ids)
        random.Random(_round_seed(master_seed, round_no)).shuffle(permuted)
        for cell_id in permuted:
            rows.append({"seq": len(rows), "round": round_no, "cell_id": cell_id})
    return rows


_RESUME_STATES = frozenset({
    "L", "M-prestart", "M-running", "M-finalize-pending",
})

# L/M-prestart には、ここで明示的に許可した診断だけを含められる。
# 許可リストにしておくことで、event の絞り込みによる暗黙の受理を避け、
# 別の診断を追加する際は契約変更として明示的に扱える。
_RESUME_DIAGNOSTIC_EVENT_KEYS = {
    "perf-preflight": frozenset({
        "event", "schema", "perf_preflight_receipt",
    }),
}
_RESUME_DIAGNOSTIC_EVENTS = frozenset(_RESUME_DIAGNOSTIC_EVENT_KEYS)
_RESUME_DIAGNOSTIC_POSITION_BLOCKERS = frozenset({
    "campaign-start", "resume-start", "round-start", "round-complete",
    "session-start", "session", "terminal",
})
_RESUME_DIAGNOSTIC_EXPECTED_UNSET = object()


def _validate_resume_diagnostic_events(
        records, *, expected_perf_preflight=_RESUME_DIAGNOSTIC_EXPECTED_UNSET):
    """resume journal の許可済み pre-measure 診断を検証する。

    classifier が不正な record を無視して無害化してはならない。したがって、
    許可する診断は外側の閉じた schema、正準の内側 receipt、単一出現、
    測定前の位置をすべて満たさなければならない。sealed manifest がある場合は
    manifest を考慮する resume verifier から ``expected_perf_preflight`` が渡される。
    manifest field が無い場合は ``None`` として表現し、event とは互換にしない。
    """
    seen_events = set()
    expected_normalized = _RESUME_DIAGNOSTIC_EXPECTED_UNSET
    if expected_perf_preflight is not _RESUME_DIAGNOSTIC_EXPECTED_UNSET:
        if expected_perf_preflight is not None:
            try:
                expected_normalized = (
                    _perf_preflight.validate_perf_preflight_receipt(
                        expected_perf_preflight
                    )
                )
            except _perf_preflight.PerfPreflightError as exc:
                raise FloorContractError(
                    f"resume manifest の perf_preflight が不正: {exc}"
                ) from exc
        else:
            expected_normalized = None

    for index, record in enumerate(records):
        event = record.get("event")
        if not isinstance(event, str):
            raise FloorContractError("resume journal の event が文字列でない")
        expected_keys = _RESUME_DIAGNOSTIC_EVENT_KEYS.get(event)
        if expected_keys is None:
            continue
        if event in seen_events:
            raise FloorContractError(
                f"resume journal の diagnostic event が重複している: {event}"
            )
        if set(record) != expected_keys:
            raise FloorContractError(
                f"resume journal の {event} exact key 集合が不一致"
            )
        if record.get("schema") != JOURNAL_SCHEMA:
            raise FloorContractError(
                f"resume journal の {event}.schema が {JOURNAL_SCHEMA} でない"
            )
        if any(
                previous.get("event") in _RESUME_DIAGNOSTIC_POSITION_BLOCKERS
                for previous in records[:index]
        ):
            raise FloorContractError(
                f"resume journal の {event} が pre-measure 位置にない"
            )
        try:
            normalized = _perf_preflight.validate_perf_preflight_receipt(
                record["perf_preflight_receipt"]
            )
        except _perf_preflight.PerfPreflightError as exc:
            raise FloorContractError(
                f"resume journal の {event} receipt が不正: {exc}"
            ) from exc
        if expected_normalized is not _RESUME_DIAGNOSTIC_EXPECTED_UNSET:
            if expected_normalized is None or normalized != expected_normalized:
                raise FloorContractError(
                    "resume journal の perf-preflight receipt が manifest と不一致"
                )
        seen_events.add(event)


def classify_journal_resume_state(
        records, *, manifest_exists: bool, result_published: bool,
        markdown_published: bool) -> str:
    """L/M resume の構造 substate を fail-closed に分類する共有 pure helper。

    ``L`` は manifest 無し・先頭 launch-start と allowlisted pre-measure diagnostic、
    ``M-prestart`` は sealed manifest 有り・campaign-start 無し、``M-running`` は一意
    campaign-start 有り・terminal 無し、``M-finalize-pending`` は一意 completed terminal
    が最終 record だが result/md publish が片方以上未完、である。cert bytes/path/time と
    manifest/result bytes は issuer/verifier の各境界で別途厳密検証する。

    aborted / artifact-invalid / terminal 重複 / completed 後の record / publish 完了済みは
    再開可能状態に分類しない。L の自己整合 bundle 全体をゼロから捏造する攻撃は、この
    journal 内 hash だけでは閉じない（凍結済み保証境界）。
    """
    if not isinstance(records, list) or not all(isinstance(r, Mapping) for r in records):
        raise FloorContractError("resume journal が object record の list でない")
    for name, value in {
            "manifest_exists": manifest_exists,
            "result_published": result_published,
            "markdown_published": markdown_published,
    }.items():
        if type(value) is not bool:
            raise FloorContractError(f"resume state {name} が bool でない")

    _validate_resume_diagnostic_events(records)

    terminals = [r for r in records if r.get("event") == "terminal"]
    if len(terminals) > 1:
        raise FloorContractError("resume journal の terminal が重複している")
    if terminals:
        terminal = terminals[0]
        if records[-1] is not terminal:
            raise FloorContractError("resume journal の terminal が最終 record でない")
        if terminal.get("status") != "completed":
            raise FloorContractError("aborted/artifact-invalid terminal は再開できない")
        if not manifest_exists:
            raise FloorContractError("completed terminal に sealed manifest がない")
        if result_published and markdown_published:
            raise FloorContractError("publish 完了済み campaign は再開できない")
        return "M-finalize-pending"

    campaign_starts = [r for r in records if r.get("event") == "campaign-start"]
    if len(campaign_starts) > 1:
        raise FloorContractError("resume journal の campaign-start が重複している")
    if not manifest_exists:
        allowed_l_events = {"launch-start"} | _RESUME_DIAGNOSTIC_EVENTS
        if (records and records[0].get("event") == "launch-start"
                and sum(r.get("event") == "launch-start" for r in records) == 1
                and all(r.get("event") in allowed_l_events for r in records)
                and not result_published and not markdown_published):
            return "L"
        raise FloorContractError("manifest 無し journal は厳密な L 状態でない")
    if result_published or markdown_published:
        raise FloorContractError("completed terminal 前に result/md が publish されている")
    if not campaign_starts:
        allowed_prestart_events = {"launch-start"} | _RESUME_DIAGNOSTIC_EVENTS
        if any(r.get("event") not in allowed_prestart_events for r in records):
            raise FloorContractError(
                "M-prestart に許可されていない record がある"
            )
        if sum(r.get("event") == "launch-start" for r in records) > 1:
            raise FloorContractError("M-prestart の launch-start が重複している")
        return "M-prestart"
    return "M-running"
