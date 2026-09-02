# -*- coding: utf-8 -*-
"""B-4 floor の対照対を凍結 spec どおりに測る専用 driver。

この module は、同一 candidate の二つの独立 session と一つの共通 reference
session から ``D = |gain_1 - gain_2|`` を作り、閉じた stratum の最大だけを
create-only 成果物へ記録する。汎用測定基盤ではなく、統計関数、session 構成、
runner 引数を閉じた専用 adapter である。

証明していないこと

* 測定手順 spec が結果を見る前に凍結されたことを証明しない (freeze receipt は無い)。
* 測定が人間の認可後に行われたことを証明しない。
* 成果物の削除・改名・改変を防がない。防ぐのは「同じ path が残っている間の再作成」だけ。
* 標本の統計的独立性を判定しない。window / campaign を記録するだけ。
* strip 済み binary の trace 混入を検出しない。
* ``nm`` の PATH 解決先を binary identity として束縛しない。
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import hmac
import json
import math
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..calibrator import runner
from ..calibrator.model import ScalePoint
from . import (
    buildcache,
    calibration_verify,
    env_contract,
    s8b_binary_admission,
    site_policy,
)


SPEC_SCHEMA = "floor-pair-spec/v1"
PLAN_SCHEMA = "floor-pair-plan/v1"
WINDOW_SCHEMA = "floor-pair-window/v1"
SUMMARY_SCHEMA = "floor-pair-summary/v1"
RANDOMIZATION_ID = "hmac-sha256-rank/v1"
SESSION_REDUCER_ID = "median/v1"
STRATUM_UPPER_ID = "sample_max/v1"
FINAL_COMBINER_ID = "max_over_closed_strata/v1"
FAILURE_POLICY_ID = "all_planned_samples_required/v1"
WINDOW_FORMAT_ID = "floor-pair-jsonl/v1"
SUMMARY_FORMAT_ID = "floor-pair-summary-json/v1"
COMPETING_PROBE_ARGV = ("pgrep", "-af", r"ycsb_.*\.exe")
_GIT_TIMEOUT_S = 10

NOT_PROVEN = (
    "測定手順 spec が結果を見る前に凍結されたことを証明しない (freeze receipt は無い)。",
    "測定が人間の認可後に行われたことを証明しない。",
    "成果物の削除・改名・改変を防がない。防ぐのは「同じ path が残っている間の再作成」だけ。",
    "標本の統計的独立性を判定しない。window / campaign を記録するだけ。",
    "strip 済み binary の trace 混入を検出しない。",
    "``nm`` の PATH 解決先を binary identity として束縛しない。",
)

_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_HEX40_RE = re.compile(r"[0-9a-f]{40}")
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_WORKLOAD_KEYS = frozenset(
    {"ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw"}
)
_ROLES = ("candidate_1", "candidate_2", "reference")
SESSION_STATUSES = frozenset(
    {
        "complete",
        "pre_probe_competing",
        "pre_probe_indeterminate",
        "measure_failed",
        "measure_incomplete",
        "post_probe_competing",
        "post_probe_indeterminate",
        "binary_binding_failed",
        "outside_window",
        "not_run_after_fail_closed",
    }
)


class FloorPairSpecError(ValueError):
    """凍結 spec の構文、型、閉包、値域が不正。"""


class FloorPairBindingError(RuntimeError):
    """spec と checkout、calibration、artifact の束縛が不正。"""


class FloorPairRunError(RuntimeError):
    """window を開始できない fail-closed な実行拒否。"""

    def __init__(self, message: str, *, status: str):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class BoundReference:
    path: str
    sha256: str


@dataclass(frozen=True)
class CalibrationReference:
    path: str
    sha256: str
    attestation_mode: str


@dataclass(frozen=True)
class ProvenanceConfig:
    calibration: CalibrationReference
    source_commit: str


@dataclass(frozen=True)
class EnvironmentConfig:
    site: str
    env_tag: str
    clocks_per_us: int
    numactl_argv: tuple[str, ...]
    use_perf: bool
    timeout_s: int
    extra_env: tuple[tuple[str, str], ...]
    probe_timeout_s: int


@dataclass(frozen=True)
class ArtifactConfig:
    artifact_id: str
    binary_relpath: str
    binary_sha256: str
    build_receipt: BoundReference
    trace: bool


@dataclass(frozen=True)
class FrozenPerfConfig:
    records: int
    threads: int
    workload: tuple[tuple[str, str], ...]
    extime: int
    reps: int
    ycsb_max_ope: int


@dataclass(frozen=True)
class CellConfig:
    cell_id: str
    perf_config: FrozenPerfConfig


@dataclass(frozen=True)
class PairSide:
    side_id: str
    candidate_artifact_id: str


@dataclass(frozen=True)
class PairConfig:
    pair_id: str
    cell_id: str
    reference_artifact_id: str
    sides: tuple[PairSide, ...]


@dataclass(frozen=True)
class WindowConfig:
    window_id: str
    campaign_id: str
    not_before: datetime
    not_after: datetime
    sample_count: int
    pair_ids: tuple[str, ...]
    artifact_relpath: str


@dataclass(frozen=True)
class RandomizationConfig:
    algorithm: str
    seed_hex: str


@dataclass(frozen=True)
class StatisticsConfig:
    session_reducer: str
    stratum_upper: str
    closed_strata: tuple[tuple[str, str], ...]
    final_combiner: str


@dataclass(frozen=True)
class FailurePolicy:
    policy: str
    retry_count: int
    require_all_reps: bool


@dataclass(frozen=True)
class OutputsConfig:
    window_format: str
    summary_format: str
    summary_relpath: str


@dataclass(frozen=True)
class FloorPairSpec:
    schema: str
    provenance: ProvenanceConfig
    environment: EnvironmentConfig
    artifacts: tuple[ArtifactConfig, ...]
    cells: tuple[CellConfig, ...]
    pairs: tuple[PairConfig, ...]
    windows: tuple[WindowConfig, ...]
    randomization: RandomizationConfig
    statistics: StatisticsConfig
    failure_policy: FailurePolicy
    outputs: OutputsConfig
    repo_root: Path
    spec_relpath: str
    spec_sha256: str
    loaded_head: str


@dataclass(frozen=True)
class PlannedSession:
    session_id: str
    window_id: str
    campaign_id: str
    pair_id: str
    cell_id: str
    sample_index: int
    role: str
    artifact_id: str
    schedule_index: int


@dataclass(frozen=True)
class MeasurementPlan:
    schema: str
    spec_sha256: str
    randomization_algorithm: str
    seed_hex: str
    sessions: tuple[PlannedSession, ...]
    plan_sha256: str


@dataclass(frozen=True)
class MeasurementRequest:
    session_id: str
    binary_path: str
    perf_config: FrozenPerfConfig
    clocks_per_us: int
    numactl_argv: tuple[str, ...]
    use_perf: bool
    timeout_s: int
    extra_env: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class MeasurementResult:
    session_id: str
    point_records: int
    point_threads: int
    throughputs: tuple[float, ...]
    rep_returncodes: tuple[int, ...]
    rep_observations: tuple[Mapping[str, object], ...]
    rep_timestamps: tuple[Mapping[str, int], ...]


@dataclass(frozen=True)
class GainDifference:
    gain_1: float
    gain_2: float
    difference: float


@dataclass(frozen=True)
class WindowRunResult:
    status: str
    window_id: str
    artifact_relpath: str
    artifact_sha256: str
    session_count: int


@dataclass(frozen=True)
class FinalFloorResult:
    status: str
    upper: float | None
    candidate_floor: float | None
    summary_relpath: str
    summary_sha256: str


def _raise_json_constant(token: str, *, error_type: type[Exception], label: str) -> None:
    raise error_type(f"{label}: JSON に非有限定数がある: {token}")


def _load_json(raw: bytes, *, label: str, error_type: type[Exception]) -> object:
    def duplicate_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise error_type(f"{label}: duplicate JSON key: {key!r}")
            result[key] = value
        return result

    def reject_constant(token: str) -> None:
        _raise_json_constant(token, error_type=error_type, label=label)

    try:
        value = json.loads(
            raw,
            object_pairs_hook=duplicate_object,
            parse_constant=reject_constant,
        )
    except error_type:
        raise
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise error_type(f"{label}: JSON を parse できない: {exc}") from exc
    _reject_nonfinite_tree(value, label=label, error_type=error_type)
    return value


def _reject_nonfinite_tree(
    value: object, *, label: str, error_type: type[Exception]
) -> None:
    if type(value) is float and not math.isfinite(value):
        raise error_type(f"{label}: 非有限数値がある")
    if type(value) is list:
        for item in value:
            _reject_nonfinite_tree(item, label=label, error_type=error_type)
    if type(value) is dict:
        for item in value.values():
            _reject_nonfinite_tree(item, label=label, error_type=error_type)


def _exact_object(
    value: object, expected: set[str], *, label: str
) -> dict[str, object]:
    if type(value) is not dict:
        raise FloorPairSpecError(f"{label} は object でなければならない")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise FloorPairSpecError(
            f"{label} key 不一致: missing={missing}, unknown={unknown}"
        )
    return value


def _exact_list(value: object, *, label: str, allow_empty: bool) -> list[object]:
    if type(value) is not list:
        raise FloorPairSpecError(f"{label} は array でなければならない")
    if not allow_empty and len(value) == 0:
        raise FloorPairSpecError(f"{label} は空であってはならない")
    return value


def _exact_text(value: object, *, label: str) -> str:
    if type(value) is not str or value == "":
        raise FloorPairSpecError(f"{label} は空でない exact string でなければならない")
    return value


def _identifier(value: object, *, label: str) -> str:
    text = _exact_text(value, label=label)
    if _ID_RE.fullmatch(text) is None:
        raise FloorPairSpecError(f"{label} は canonical ID でなければならない")
    return text


def _exact_int(value: object, *, label: str, minimum: int) -> int:
    if type(value) is not int:
        raise FloorPairSpecError(f"{label} は exact int でなければならない")
    if value < minimum:
        raise FloorPairSpecError(f"{label} は {minimum} 以上でなければならない")
    return value


def _exact_bool(value: object, *, label: str) -> bool:
    if type(value) is not bool:
        raise FloorPairSpecError(f"{label} は exact bool でなければならない")
    return value


def _sha256_text(value: object, *, label: str) -> str:
    text = _exact_text(value, label=label)
    if _HEX64_RE.fullmatch(text) is None:
        raise FloorPairSpecError(f"{label} は 64 桁 lowercase SHA-256 でなければならない")
    return text


def _relative_path(value: object, *, label: str) -> str:
    text = _exact_text(value, label=label)
    path = Path(text)
    if path.is_absolute() or text != path.as_posix():
        raise FloorPairSpecError(f"{label} は canonical repository-relative path でなければならない")
    if len(path.parts) == 0 or any(part in {"", ".", ".."} for part in path.parts):
        raise FloorPairSpecError(f"{label} に空、dot、親参照 component は使えない")
    return text


def _parse_utc(value: object, *, label: str) -> datetime:
    text = _exact_text(value, label=label)
    if not text.endswith("Z"):
        raise FloorPairSpecError(f"{label} は UTC の Z 表記でなければならない")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise FloorPairSpecError(f"{label} は RFC3339 UTC timestamp でない") from exc
    if parsed.tzinfo != timezone.utc:
        raise FloorPairSpecError(f"{label} は UTC でなければならない")
    return parsed


def _format_utc(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise FloorPairRunError("clock が timezone-aware datetime を返さない", status="clock_invalid")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _assert_components_no_symlink(root: Path, target: Path, *, label: str) -> None:
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise FloorPairBindingError(f"{label} が repo_root 外にある") from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        try:
            mode = cursor.lstat().st_mode
        except OSError as exc:
            raise FloorPairBindingError(f"{label} を lstat できない: {cursor}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise FloorPairBindingError(f"{label} に symlink component がある: {cursor}")


def _resolve_regular(root: Path, relpath: str, *, label: str) -> Path:
    target = root / relpath
    _assert_components_no_symlink(root, target, label=label)
    try:
        mode = target.lstat().st_mode
    except OSError as exc:
        raise FloorPairBindingError(f"{label} が存在しない: {target}") from exc
    if not stat.S_ISREG(mode):
        raise FloorPairBindingError(f"{label} は regular file でなければならない: {target}")
    return target


def _validate_output_path(root: Path, relpath: str, *, label: str) -> Path:
    target = root / relpath
    parent = target.parent
    _assert_components_no_symlink(root, parent, label=f"{label}.parent")
    try:
        mode = parent.lstat().st_mode
    except OSError as exc:
        raise FloorPairBindingError(f"{label} の parent が存在しない: {parent}") from exc
    if not stat.S_ISDIR(mode):
        raise FloorPairBindingError(f"{label} の parent は directory でなければならない")
    try:
        leaf_mode = target.lstat().st_mode
    except FileNotFoundError:
        return target
    except OSError as exc:
        raise FloorPairBindingError(f"{label} の leaf を lstat できない: {exc}") from exc
    if stat.S_ISLNK(leaf_mode):
        raise FloorPairBindingError(f"{label} の leaf は symlink であってはならない")
    return target


def _git_show_head(root: Path, relpath: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:{relpath}"],
            capture_output=True,
            check=False,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise FloorPairBindingError(
            f"git show HEAD を起動または完了できない: {relpath}: {exc}"
        ) from exc
    if completed.returncode != 0:
        stderr = bytes(completed.stderr).decode("utf-8", errors="replace")
        raise FloorPairBindingError(
            f"HEAD に tracked blob がない: {relpath}: {stderr[-200:]}"
        )
    return bytes(completed.stdout)


def _git_head(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            check=False,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise FloorPairBindingError(
            f"git rev-parse HEAD を起動または完了できない: {exc}"
        ) from exc
    if completed.returncode != 0:
        raise FloorPairBindingError("git rev-parse HEAD に失敗した")
    try:
        value = bytes(completed.stdout).decode("ascii").strip()
    except UnicodeError as exc:
        raise FloorPairBindingError("HEAD が ASCII でない") from exc
    if _HEX40_RE.fullmatch(value) is None:
        raise FloorPairBindingError(f"HEAD が 40 桁 lowercase hex でない: {value!r}")
    return value


def _read_tracked_bound(
    root: Path, reference: BoundReference | CalibrationReference, *, label: str
) -> bytes:
    target = _resolve_regular(root, reference.path, label=label)
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise FloorPairBindingError(f"{label} を読めない: {exc}") from exc
    actual = hashlib.sha256(raw).hexdigest()
    if actual != reference.sha256:
        raise FloorPairBindingError(
            f"{label} sha256 不一致: expected={reference.sha256}, observed={actual}"
        )
    head_raw = _git_show_head(root, reference.path)
    if raw != head_raw:
        raise FloorPairBindingError(f"{label} が HEAD tracked blob と byte 一致しない")
    return raw


def _parse_bound_reference(value: object, *, label: str) -> BoundReference:
    obj = _exact_object(value, {"path", "sha256"}, label=label)
    return BoundReference(
        path=_relative_path(obj["path"], label=f"{label}.path"),
        sha256=_sha256_text(obj["sha256"], label=f"{label}.sha256"),
    )


def _parse_calibration_reference(value: object) -> CalibrationReference:
    label = "provenance.calibration"
    obj = _exact_object(value, {"path", "sha256", "attestation_mode"}, label=label)
    mode = _exact_text(obj["attestation_mode"], label=f"{label}.attestation_mode")
    if mode not in {"required", "none"}:
        raise FloorPairSpecError(f"{label}.attestation_mode が未対応: {mode!r}")
    return CalibrationReference(
        path=_relative_path(obj["path"], label=f"{label}.path"),
        sha256=_sha256_text(obj["sha256"], label=f"{label}.sha256"),
        attestation_mode=mode,
    )


def _parse_provenance(value: object) -> ProvenanceConfig:
    obj = _exact_object(
        value,
        {"calibration", "source_commit"},
        label="provenance",
    )
    source_commit = _exact_text(obj["source_commit"], label="provenance.source_commit")
    if _HEX40_RE.fullmatch(source_commit) is None:
        raise FloorPairSpecError("provenance.source_commit は 40 桁 lowercase hex でなければならない")
    return ProvenanceConfig(
        calibration=_parse_calibration_reference(obj["calibration"]),
        source_commit=source_commit,
    )


def _parse_string_tuple(value: object, *, label: str, allow_empty: bool) -> tuple[str, ...]:
    values = _exact_list(value, label=label, allow_empty=allow_empty)
    result = tuple(_exact_text(item, label=f"{label}[{index}]") for index, item in enumerate(values))
    return result


def _parse_string_map(value: object, *, label: str) -> tuple[tuple[str, str], ...]:
    if type(value) is not dict:
        raise FloorPairSpecError(f"{label} は object でなければならない")
    result: list[tuple[str, str]] = []
    for key in sorted(value):
        clean_key = _exact_text(key, label=f"{label}.key")
        clean_value = _exact_text(value[key], label=f"{label}.{clean_key}")
        result.append((clean_key, clean_value))
    return tuple(result)


def _parse_environment(value: object) -> EnvironmentConfig:
    obj = _exact_object(
        value,
        {
            "site", "env_tag", "clocks_per_us", "numactl_argv", "use_perf",
            "timeout_s", "extra_env", "probe_timeout_s",
        },
        label="environment",
    )
    site = _exact_text(obj["site"], label="environment.site")
    if site not in {
        site_policy.OTHER,
        site_policy.PEGASUS_LOGIN,
        site_policy.PEGASUS_COMPUTE,
        site_policy.PEGASUS_SUSPECT,
    }:
        raise FloorPairSpecError(f"environment.site が未対応: {site!r}")
    use_perf = _exact_bool(obj["use_perf"], label="environment.use_perf")
    if use_perf is not False:
        raise FloorPairSpecError("environment.use_perf はこの driver では false でなければならない")
    extra_env = _parse_string_map(obj["extra_env"], label="environment.extra_env")
    forbidden_env = sorted(
        key for key, _value in extra_env if key == "PATH" or key.startswith("LD_")
    )
    if forbidden_env:
        raise FloorPairSpecError(
            "environment.extra_env は PATH / LD_ 接頭辞を上書きできない: "
            f"{forbidden_env}"
        )
    return EnvironmentConfig(
        site=site,
        env_tag=_identifier(obj["env_tag"], label="environment.env_tag"),
        clocks_per_us=_exact_int(
            obj["clocks_per_us"], label="environment.clocks_per_us", minimum=1
        ),
        numactl_argv=_parse_string_tuple(
            obj["numactl_argv"], label="environment.numactl_argv", allow_empty=True
        ),
        use_perf=use_perf,
        timeout_s=_exact_int(obj["timeout_s"], label="environment.timeout_s", minimum=1),
        extra_env=extra_env,
        probe_timeout_s=_exact_int(
            obj["probe_timeout_s"], label="environment.probe_timeout_s", minimum=1
        ),
    )


def _parse_artifacts(value: object) -> tuple[ArtifactConfig, ...]:
    values = _exact_list(value, label="artifacts", allow_empty=False)
    result: list[ArtifactConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        label = f"artifacts[{index}]"
        obj = _exact_object(
            item,
            {"artifact_id", "binary_relpath", "binary_sha256", "build_receipt", "trace"},
            label=label,
        )
        artifact_id = _identifier(obj["artifact_id"], label=f"{label}.artifact_id")
        if artifact_id in seen:
            raise FloorPairSpecError(f"duplicate artifact_id: {artifact_id}")
        seen.add(artifact_id)
        trace = _exact_bool(obj["trace"], label=f"{label}.trace")
        if trace is not False:
            raise FloorPairSpecError(f"{label}.trace は false でなければならない")
        result.append(
            ArtifactConfig(
                artifact_id=artifact_id,
                binary_relpath=_relative_path(
                    obj["binary_relpath"], label=f"{label}.binary_relpath"
                ),
                binary_sha256=_sha256_text(
                    obj["binary_sha256"], label=f"{label}.binary_sha256"
                ),
                build_receipt=_parse_bound_reference(
                    obj["build_receipt"], label=f"{label}.build_receipt"
                ),
                trace=trace,
            )
        )
    return tuple(result)


def _parse_perf(value: object, *, label: str) -> FrozenPerfConfig:
    obj = _exact_object(
        value,
        {"records", "threads", "workload", "extime", "reps", "ycsb_max_ope"},
        label=label,
    )
    workload_obj = _exact_object(value=obj["workload"], expected=set(_WORKLOAD_KEYS), label=f"{label}.workload")
    workload = tuple(
        (key, _exact_text(workload_obj[key], label=f"{label}.workload.{key}"))
        for key in sorted(workload_obj)
    )
    return FrozenPerfConfig(
        records=_exact_int(obj["records"], label=f"{label}.records", minimum=1),
        threads=_exact_int(obj["threads"], label=f"{label}.threads", minimum=1),
        workload=workload,
        extime=_exact_int(obj["extime"], label=f"{label}.extime", minimum=1),
        reps=_exact_int(obj["reps"], label=f"{label}.reps", minimum=1),
        ycsb_max_ope=_exact_int(
            obj["ycsb_max_ope"], label=f"{label}.ycsb_max_ope", minimum=1
        ),
    )


def _parse_cells(value: object) -> tuple[CellConfig, ...]:
    values = _exact_list(value, label="cells", allow_empty=False)
    result: list[CellConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        label = f"cells[{index}]"
        obj = _exact_object(item, {"cell_id", "perf_config"}, label=label)
        cell_id = _identifier(obj["cell_id"], label=f"{label}.cell_id")
        if cell_id in seen:
            raise FloorPairSpecError(f"duplicate cell_id: {cell_id}")
        seen.add(cell_id)
        result.append(
            CellConfig(
                cell_id=cell_id,
                perf_config=_parse_perf(obj["perf_config"], label=f"{label}.perf_config"),
            )
        )
    return tuple(result)


def _parse_pairs(value: object) -> tuple[PairConfig, ...]:
    values = _exact_list(value, label="pairs", allow_empty=False)
    result: list[PairConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        label = f"pairs[{index}]"
        obj = _exact_object(
            item, {"pair_id", "cell_id", "reference_artifact_id", "sides"}, label=label
        )
        pair_id = _identifier(obj["pair_id"], label=f"{label}.pair_id")
        if pair_id in seen:
            raise FloorPairSpecError(f"duplicate pair_id: {pair_id}")
        seen.add(pair_id)
        sides_raw = _exact_list(obj["sides"], label=f"{label}.sides", allow_empty=False)
        if len(sides_raw) != 2:
            raise FloorPairSpecError(f"{label}.sides は exact 2 件でなければならない")
        sides: list[PairSide] = []
        for side_index, side_item in enumerate(sides_raw):
            side_label = f"{label}.sides[{side_index}]"
            side_obj = _exact_object(
                side_item, {"side_id", "candidate_artifact_id"}, label=side_label
            )
            sides.append(
                PairSide(
                    side_id=_identifier(side_obj["side_id"], label=f"{side_label}.side_id"),
                    candidate_artifact_id=_identifier(
                        side_obj["candidate_artifact_id"],
                        label=f"{side_label}.candidate_artifact_id",
                    ),
                )
            )
        if {side.side_id for side in sides} != {"candidate_1", "candidate_2"}:
            raise FloorPairSpecError(f"{label}.sides の ID は candidate_1/2 exact でなければならない")
        if sides[0].candidate_artifact_id != sides[1].candidate_artifact_id:
            raise FloorPairSpecError(f"{label}.sides は同一 candidate artifact を共有しなければならない")
        reference_id = _identifier(
            obj["reference_artifact_id"], label=f"{label}.reference_artifact_id"
        )
        if reference_id == sides[0].candidate_artifact_id:
            raise FloorPairSpecError(f"{label} の candidate と reference は別 artifact でなければならない")
        result.append(
            PairConfig(
                pair_id=pair_id,
                cell_id=_identifier(obj["cell_id"], label=f"{label}.cell_id"),
                reference_artifact_id=reference_id,
                sides=tuple(sides),
            )
        )
    return tuple(result)


def _parse_windows(value: object) -> tuple[WindowConfig, ...]:
    values = _exact_list(value, label="windows", allow_empty=False)
    result: list[WindowConfig] = []
    seen_windows: set[str] = set()
    seen_campaigns: set[str] = set()
    for index, item in enumerate(values):
        label = f"windows[{index}]"
        obj = _exact_object(
            item,
            {
                "window_id", "campaign_id", "not_before", "not_after",
                "sample_count", "pair_ids", "artifact_relpath",
            },
            label=label,
        )
        window_id = _identifier(obj["window_id"], label=f"{label}.window_id")
        campaign_id = _identifier(obj["campaign_id"], label=f"{label}.campaign_id")
        if window_id in seen_windows:
            raise FloorPairSpecError(f"duplicate window_id: {window_id}")
        if campaign_id in seen_campaigns:
            raise FloorPairSpecError(f"duplicate campaign_id: {campaign_id}")
        seen_windows.add(window_id)
        seen_campaigns.add(campaign_id)
        not_before = _parse_utc(obj["not_before"], label=f"{label}.not_before")
        not_after = _parse_utc(obj["not_after"], label=f"{label}.not_after")
        if not_before >= not_after:
            raise FloorPairSpecError(f"{label} は空でない半開区間でなければならない")
        pair_ids = tuple(
            _identifier(item_id, label=f"{label}.pair_ids[{pair_index}]")
            for pair_index, item_id in enumerate(
                _exact_list(obj["pair_ids"], label=f"{label}.pair_ids", allow_empty=False)
            )
        )
        if len(pair_ids) != len(set(pair_ids)):
            raise FloorPairSpecError(f"{label}.pair_ids に重複がある")
        result.append(
            WindowConfig(
                window_id=window_id,
                campaign_id=campaign_id,
                not_before=not_before,
                not_after=not_after,
                sample_count=_exact_int(
                    obj["sample_count"], label=f"{label}.sample_count", minimum=1
                ),
                pair_ids=pair_ids,
                artifact_relpath=_relative_path(
                    obj["artifact_relpath"], label=f"{label}.artifact_relpath"
                ),
            )
        )
    ordered = sorted(result, key=lambda item: item.not_before)
    for earlier, later in zip(ordered, ordered[1:]):
        if earlier.not_after > later.not_before:
            raise FloorPairSpecError(
                f"windows が重なる: {earlier.window_id}, {later.window_id}"
            )
    return tuple(result)


def _parse_randomization(value: object) -> RandomizationConfig:
    obj = _exact_object(value, {"algorithm", "seed_hex"}, label="randomization")
    algorithm = _exact_text(obj["algorithm"], label="randomization.algorithm")
    if algorithm != RANDOMIZATION_ID:
        raise FloorPairSpecError(f"randomization.algorithm は {RANDOMIZATION_ID!r} でなければならない")
    seed_hex = _sha256_text(obj["seed_hex"], label="randomization.seed_hex")
    return RandomizationConfig(algorithm=algorithm, seed_hex=seed_hex)


def _parse_statistics(value: object) -> StatisticsConfig:
    obj = _exact_object(
        value,
        {"session_reducer", "stratum_upper", "closed_strata", "final_combiner"},
        label="statistics",
    )
    reducer = _exact_text(obj["session_reducer"], label="statistics.session_reducer")
    stratum_upper = _exact_text(obj["stratum_upper"], label="statistics.stratum_upper")
    final_combiner = _exact_text(obj["final_combiner"], label="statistics.final_combiner")
    if reducer != SESSION_REDUCER_ID:
        raise FloorPairSpecError(f"statistics.session_reducer は {SESSION_REDUCER_ID!r} でなければならない")
    if stratum_upper != STRATUM_UPPER_ID:
        raise FloorPairSpecError(f"statistics.stratum_upper は {STRATUM_UPPER_ID!r} でなければならない")
    if final_combiner != FINAL_COMBINER_ID:
        raise FloorPairSpecError(f"statistics.final_combiner は {FINAL_COMBINER_ID!r} でなければならない")
    strata_raw = _exact_list(obj["closed_strata"], label="statistics.closed_strata", allow_empty=False)
    strata: list[tuple[str, str]] = []
    for index, item in enumerate(strata_raw):
        label = f"statistics.closed_strata[{index}]"
        stratum_obj = _exact_object(item, {"window_id", "pair_id"}, label=label)
        strata.append(
            (
                _identifier(stratum_obj["window_id"], label=f"{label}.window_id"),
                _identifier(stratum_obj["pair_id"], label=f"{label}.pair_id"),
            )
        )
    if len(strata) != len(set(strata)):
        raise FloorPairSpecError("statistics.closed_strata に重複がある")
    return StatisticsConfig(
        session_reducer=reducer,
        stratum_upper=stratum_upper,
        closed_strata=tuple(strata),
        final_combiner=final_combiner,
    )


def _parse_failure_policy(value: object) -> FailurePolicy:
    obj = _exact_object(
        value, {"policy", "retry_count", "require_all_reps"}, label="failure_policy"
    )
    policy = _exact_text(obj["policy"], label="failure_policy.policy")
    if policy != FAILURE_POLICY_ID:
        raise FloorPairSpecError(f"failure_policy.policy は {FAILURE_POLICY_ID!r} でなければならない")
    retry_count = _exact_int(obj["retry_count"], label="failure_policy.retry_count", minimum=0)
    if retry_count != 0:
        raise FloorPairSpecError("failure_policy.retry_count は 0 でなければならない")
    require_all_reps = _exact_bool(
        obj["require_all_reps"], label="failure_policy.require_all_reps"
    )
    if require_all_reps is not True:
        raise FloorPairSpecError("failure_policy.require_all_reps は true でなければならない")
    return FailurePolicy(
        policy=policy,
        retry_count=retry_count,
        require_all_reps=require_all_reps,
    )


def _parse_outputs(value: object) -> OutputsConfig:
    obj = _exact_object(
        value, {"window_format", "summary_format", "summary_relpath"}, label="outputs"
    )
    window_format = _exact_text(obj["window_format"], label="outputs.window_format")
    summary_format = _exact_text(obj["summary_format"], label="outputs.summary_format")
    if window_format != WINDOW_FORMAT_ID:
        raise FloorPairSpecError(f"outputs.window_format は {WINDOW_FORMAT_ID!r} でなければならない")
    if summary_format != SUMMARY_FORMAT_ID:
        raise FloorPairSpecError(f"outputs.summary_format は {SUMMARY_FORMAT_ID!r} でなければならない")
    return OutputsConfig(
        window_format=window_format,
        summary_format=summary_format,
        summary_relpath=_relative_path(obj["summary_relpath"], label="outputs.summary_relpath"),
    )


def _index_unique(items: Sequence[object], attribute: str, *, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in items:
        key = getattr(item, attribute)
        if key in result:
            raise FloorPairSpecError(f"{label} に duplicate key: {key}")
        result[key] = item
    return result


def _validate_cross_references(
    *,
    artifacts: tuple[ArtifactConfig, ...],
    cells: tuple[CellConfig, ...],
    pairs: tuple[PairConfig, ...],
    windows: tuple[WindowConfig, ...],
    statistics: StatisticsConfig,
) -> None:
    artifact_index = _index_unique(artifacts, "artifact_id", label="artifacts")
    cell_index = _index_unique(cells, "cell_id", label="cells")
    pair_index = _index_unique(pairs, "pair_id", label="pairs")
    for pair in pairs:
        if pair.cell_id not in cell_index:
            raise FloorPairSpecError(f"pair {pair.pair_id} が未知 cell を参照する")
        if pair.reference_artifact_id not in artifact_index:
            raise FloorPairSpecError(f"pair {pair.pair_id} が未知 reference artifact を参照する")
        for side in pair.sides:
            if side.candidate_artifact_id not in artifact_index:
                raise FloorPairSpecError(f"pair {pair.pair_id} が未知 candidate artifact を参照する")
    planned_strata: set[tuple[str, str]] = set()
    for window in windows:
        for pair_id in window.pair_ids:
            if pair_id not in pair_index:
                raise FloorPairSpecError(f"window {window.window_id} が未知 pair を参照する")
            planned_strata.add((window.window_id, pair_id))
    if set(statistics.closed_strata) != planned_strata:
        raise FloorPairSpecError(
            "statistics.closed_strata が全 planned (window_id, pair_id) と exact 一致しない"
        )


def _validate_build_receipt(raw: bytes, artifact: ArtifactConfig) -> None:
    """実 ``s8b-binary-admission/v2`` receipt を binary bytes と束縛する。"""
    record = _load_json(
        raw,
        label=f"build receipt {artifact.artifact_id}",
        error_type=FloorPairBindingError,
    )
    try:
        receipt = s8b_binary_admission.validate_portable_binary_record(
            record,
            expected_policy=None,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise FloorPairBindingError(
            f"build receipt {artifact.artifact_id} の strict 検証に失敗: {exc}"
        ) from exc
    if record["binary_sha256"] != artifact.binary_sha256:
        raise FloorPairBindingError(
            f"build receipt {artifact.artifact_id} binary_sha256 が spec と不一致"
        )
    subject = receipt["subject"]
    if subject["binary_sha256"] != artifact.binary_sha256:
        raise FloorPairBindingError(
            f"build receipt {artifact.artifact_id} subject.binary_sha256 が spec と不一致"
        )
    if subject["trace"] is not False:
        raise FloorPairBindingError(
            f"build receipt {artifact.artifact_id} subject.trace が false でない"
        )


def _bind_checkout_inputs(
    *,
    root: Path,
    provenance: ProvenanceConfig,
    environment: EnvironmentConfig,
    artifacts: tuple[ArtifactConfig, ...],
    cells: tuple[CellConfig, ...],
) -> None:
    _read_tracked_bound(root, provenance.calibration, label="calibration artifact")
    receipt_raw_by_reference: dict[BoundReference, bytes] = {}
    for artifact in artifacts:
        binary = _resolve_regular(root, artifact.binary_relpath, label=f"binary {artifact.artifact_id}")
        try:
            buildcache.assert_binary_sha256(str(binary), artifact.binary_sha256)
        except Exception as exc:
            raise FloorPairBindingError(
                f"binary {artifact.artifact_id} sha256 を検証できない: {exc}"
            ) from exc
        if artifact.build_receipt not in receipt_raw_by_reference:
            receipt_raw_by_reference[artifact.build_receipt] = _read_tracked_bound(
                root, artifact.build_receipt, label=f"build receipt {artifact.artifact_id}"
            )
        _validate_build_receipt(
            receipt_raw_by_reference[artifact.build_receipt], artifact
        )
    try:
        verified = calibration_verify.load_verified_calibration(
            env_tag=environment.env_tag,
            clocks_per_us=environment.clocks_per_us,
            attestation_mode=provenance.calibration.attestation_mode,
            calibration_path=provenance.calibration.path,
            calibration_sha256=provenance.calibration.sha256,
            repo_root=root,
        )
    except Exception as exc:
        raise FloorPairBindingError(f"calibration admission に失敗: {exc}") from exc
    calibration = verified.calibration
    if calibration is None:
        raise FloorPairBindingError(
            "この driver は校正済み動作点だけを測るため、"
            "calibration=None の attestation mode は意図的に受理しない"
        )
    quality = getattr(calibration, "quality", None)
    if getattr(quality, "status", None) != "accepted":
        raise FloorPairBindingError("calibration quality.status が accepted でない")
    saturation = getattr(calibration, "saturation", None)
    if type(saturation) is not dict:
        raise FloorPairBindingError("accepted calibration の saturation が非 null object でない")
    if "records" not in saturation:
        raise FloorPairBindingError("calibration saturation.records が欠落")
    saturation_records = saturation["records"]
    if type(saturation_records) is not int or saturation_records < 1:
        raise FloorPairBindingError("calibration saturation.records が exact 正 int でない")
    for cell in cells:
        perf = cell.perf_config
        # verifier が production 入力で同値を既に要求するため env/clocks は冗長 gate。
        # 防御的な再照合として残すが、単独変異の証拠には数えない。
        if calibration.env_tag != environment.env_tag:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration env_tag 不一致")
        if calibration.threads != perf.threads:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration threads 不一致")
        if calibration.clocks_per_us != environment.clocks_per_us:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration clocks_per_us 不一致")
        if calibration.workload != dict(perf.workload):
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration workload 不一致")
        if perf.records != saturation_records:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration records 不一致")


def load_frozen_spec(
    path: Path, expected_sha256: str, *, repo_root: Path
) -> FloorPairSpec:
    """HEAD tracked JSON と byte 一致する凍結 spec を strict に読み、参照を束縛する。

    この専用 driver は校正済み動作点だけを測るため、正常な legacy
    ``attestation_mode=none`` が返す ``calibration=None`` も意図的に受理しない。
    """
    if not isinstance(path, Path) or not isinstance(repo_root, Path):
        raise FloorPairBindingError("path と repo_root は Path でなければならない")
    try:
        root = repo_root.resolve(strict=True)
    except OSError as exc:
        raise FloorPairBindingError(f"repo_root を解決できない: {exc}") from exc
    try:
        lexical = path if path.is_absolute() else root / path
        relpath = lexical.relative_to(root).as_posix()
    except ValueError as exc:
        raise FloorPairBindingError("spec path が repo_root 外にある") from exc
    relative_parts = Path(relpath).parts
    if (
        relpath != Path(relpath).as_posix()
        or len(relative_parts) == 0
        or any(part in {"", ".", ".."} for part in relative_parts)
    ):
        raise FloorPairBindingError("spec path が canonical repository-relative path でない")
    target = _resolve_regular(root, relpath, label="frozen spec")
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise FloorPairBindingError(f"frozen spec を読めない: {exc}") from exc
    if type(expected_sha256) is not str or _HEX64_RE.fullmatch(expected_sha256) is None:
        raise FloorPairBindingError("expected_sha256 は 64 桁 lowercase hex でなければならない")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise FloorPairBindingError(
            f"frozen spec sha256 不一致: expected={expected_sha256}, observed={actual_sha256}"
        )
    head_raw = _git_show_head(root, relpath)
    if raw != head_raw:
        raise FloorPairBindingError("frozen spec が HEAD tracked blob と byte 一致しない")
    document = _load_json(raw, label="frozen spec", error_type=FloorPairSpecError)
    top = _exact_object(
        document,
        {
            "schema", "provenance", "environment", "artifacts", "cells", "pairs",
            "windows", "randomization", "statistics", "failure_policy", "outputs",
        },
        label="frozen spec",
    )
    schema = _exact_text(top["schema"], label="schema")
    if schema != SPEC_SCHEMA:
        raise FloorPairSpecError(f"schema は {SPEC_SCHEMA!r} でなければならない")
    provenance = _parse_provenance(top["provenance"])
    environment = _parse_environment(top["environment"])
    artifacts = _parse_artifacts(top["artifacts"])
    cells = _parse_cells(top["cells"])
    pairs = _parse_pairs(top["pairs"])
    windows = _parse_windows(top["windows"])
    randomization = _parse_randomization(top["randomization"])
    statistics = _parse_statistics(top["statistics"])
    failure_policy = _parse_failure_policy(top["failure_policy"])
    outputs = _parse_outputs(top["outputs"])
    _validate_cross_references(
        artifacts=artifacts,
        cells=cells,
        pairs=pairs,
        windows=windows,
        statistics=statistics,
    )
    output_paths = [window.artifact_relpath for window in windows]
    output_paths.append(outputs.summary_relpath)
    if len(output_paths) != len(set(output_paths)):
        raise FloorPairSpecError("window と summary の output path は全件相異ならなければならない")
    for index, output_path in enumerate(output_paths):
        _validate_output_path(root, output_path, label=f"output[{index}]")
    _bind_checkout_inputs(
        root=root,
        provenance=provenance,
        environment=environment,
        artifacts=artifacts,
        cells=cells,
    )
    loaded_head = _git_head(root)
    if provenance.source_commit != loaded_head:
        raise FloorPairBindingError(
            "provenance.source_commit が spec load 時の HEAD と一致しない"
        )
    return FloorPairSpec(
        schema=schema,
        provenance=provenance,
        environment=environment,
        artifacts=artifacts,
        cells=cells,
        pairs=pairs,
        windows=windows,
        randomization=randomization,
        statistics=statistics,
        failure_policy=failure_policy,
        outputs=outputs,
        repo_root=root,
        spec_relpath=relpath,
        spec_sha256=actual_sha256,
        loaded_head=loaded_head,
    )


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _hmac_rank(seed: bytes, fields: Sequence[object]) -> bytes:
    message = b"\0".join(str(field).encode("utf-8") for field in fields)
    return hmac.new(seed, message, hashlib.sha256).digest()


def _pair_candidate_artifact(pair: PairConfig) -> str:
    candidate_ids = {side.candidate_artifact_id for side in pair.sides}
    if len(candidate_ids) != 1:
        raise FloorPairSpecError(f"pair {pair.pair_id} の candidate artifact が一意でない")
    return next(iter(candidate_ids))


def make_measurement_plan(spec: FloorPairSpec) -> MeasurementPlan:
    """global PRNG を使わず、HMAC-SHA256 rank だけで全 session 順を決める。"""
    if not isinstance(spec, FloorPairSpec):
        raise TypeError("spec は FloorPairSpec でなければならない")
    seed = bytes.fromhex(spec.randomization.seed_hex)
    pair_index = {pair.pair_id: pair for pair in spec.pairs}
    sessions: list[PlannedSession] = []
    schedule_index = 0
    for window in spec.windows:
        samples = [
            (pair_id, sample_index)
            for pair_id in window.pair_ids
            for sample_index in range(window.sample_count)
        ]
        samples.sort(
            key=lambda item: _hmac_rank(
                seed,
                (
                    spec.schema, spec.spec_sha256, window.window_id,
                    item[0], item[1], "sample",
                ),
            )
        )
        for pair_id, sample_index in samples:
            pair = pair_index[pair_id]
            candidate_artifact = _pair_candidate_artifact(pair)
            roles = list(_ROLES)
            roles.sort(
                key=lambda role: _hmac_rank(
                    seed,
                    (
                        spec.schema, spec.spec_sha256, window.window_id,
                        pair_id, sample_index, role,
                    ),
                )
            )
            for role in roles:
                artifact_id = (
                    pair.reference_artifact_id
                    if role == "reference"
                    else candidate_artifact
                )
                session_id = (
                    f"{window.window_id}.{pair_id}.s{sample_index:06d}.{role}"
                )
                sessions.append(
                    PlannedSession(
                        session_id=session_id,
                        window_id=window.window_id,
                        campaign_id=window.campaign_id,
                        pair_id=pair_id,
                        cell_id=pair.cell_id,
                        sample_index=sample_index,
                        role=role,
                        artifact_id=artifact_id,
                        schedule_index=schedule_index,
                    )
                )
                schedule_index += 1
    plan_payload = {
        "schema": PLAN_SCHEMA,
        "spec_sha256": spec.spec_sha256,
        "randomization_algorithm": spec.randomization.algorithm,
        "seed_hex": spec.randomization.seed_hex,
        "sessions": [dataclasses.asdict(session) for session in sessions],
    }
    plan_sha256 = hashlib.sha256(_canonical_bytes(plan_payload)).hexdigest()
    return MeasurementPlan(
        schema=PLAN_SCHEMA,
        spec_sha256=spec.spec_sha256,
        randomization_algorithm=spec.randomization.algorithm,
        seed_hex=spec.randomization.seed_hex,
        sessions=tuple(sessions),
        plan_sha256=plan_sha256,
    )


def _assert_plan_exact(
    spec: FloorPairSpec,
    plan: MeasurementPlan,
    *,
    error_type: type[Exception],
) -> None:
    expected = make_measurement_plan(spec)
    if plan != expected:
        raise error_type("measurement plan が frozen spec の canonical plan と exact 一致しない")


def _finite_positive(value: object, *, label: str) -> float:
    if type(value) not in {int, float}:
        raise ValueError(f"{label} は exact finite number でなければならない")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{label} は有限正数でなければならない")
    return numeric


def compute_gain_difference(
    candidate_1_tps: float,
    candidate_2_tps: float,
    reference_tps: float,
) -> GainDifference:
    """一つの共通 reference を分母として二つの相対利得の差を返す。"""
    candidate_1 = _finite_positive(candidate_1_tps, label="candidate_1_tps")
    candidate_2 = _finite_positive(candidate_2_tps, label="candidate_2_tps")
    reference = _finite_positive(reference_tps, label="reference_tps")
    gain_1 = candidate_1 / reference - 1.0
    gain_2 = candidate_2 / reference - 1.0
    difference = abs(gain_1 - gain_2)
    if not all(math.isfinite(value) for value in (gain_1, gain_2, difference)):
        raise ValueError("gain または D が非有限になった")
    return GainDifference(gain_1=gain_1, gain_2=gain_2, difference=difference)


def _sample_max(values: Sequence[float]) -> float:
    return max(values)


def _max_over_closed_strata(values: Sequence[float]) -> float:
    return max(values)


_UPPER_STATISTICS: dict[str, Callable[[Sequence[float]], float]] = {
    STRATUM_UPPER_ID: _sample_max,
    FINAL_COMBINER_ID: _max_over_closed_strata,
}


def apply_upper_statistic(function_id: str, values: Sequence[float]) -> float:
    """裁定済みの二つの最大関数だけを exact ID で適用する。"""
    if type(function_id) is not str or function_id not in _UPPER_STATISTICS:
        raise ValueError(f"未登録 upper statistic: {function_id!r}")
    if not isinstance(values, Sequence) or len(values) == 0:
        raise ValueError("upper statistic の入力は空でない sequence でなければならない")
    checked: list[float] = []
    for index, value in enumerate(values):
        if type(value) not in {int, float}:
            raise ValueError(f"values[{index}] は exact number でなければならない")
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < 0:
            raise ValueError(f"values[{index}] は有限非負でなければならない")
        checked.append(numeric)
    result = _UPPER_STATISTICS[function_id](checked)
    if not math.isfinite(result):
        raise ValueError("upper statistic が非有限を返した")
    return result


def _measure_with_runner(request: MeasurementRequest) -> MeasurementResult:
    """``measure_point`` へ凍結 field と固定不変条件をすべて明示して射影する。

    ``require_all_reps=True`` は一部 rep だけの採用を禁止する。
    ``require_complete_metrics=False`` とする理由は、runner.py:1220-1230 の True が
    perf counter の完備を要求する一方、この計算は ``use_perf=False`` で走るため、
    True では全標本が落ちるからである。``settle_first=False`` とする理由は、
    runner.py:1085 が settle の戻り値を捨て、admission 判定にならないからである。
    admission は前後の competing-process probe が担う。この三値を spec field にせず、
    caller が緩める面を作らない。
    """
    if not isinstance(request, MeasurementRequest):
        raise TypeError("request は MeasurementRequest でなければならない")
    returncodes: list[int] = []
    observations: list[dict[str, object]] = []
    timestamps: list[dict[str, int]] = []
    workload = dict(request.perf_config.workload)
    workload["ycsb_max_ope"] = str(request.perf_config.ycsb_max_ope)
    point = runner.measure_point(
        request.binary_path,
        request.perf_config.records,
        request.perf_config.threads,
        request.clocks_per_us,
        extime=request.perf_config.extime,
        reps=request.perf_config.reps,
        workload=workload,
        numactl=list(request.numactl_argv),
        settle_first=False,
        extra_env=dict(request.extra_env),
        timeout_s=request.timeout_s,
        require_all_reps=True,
        require_complete_metrics=False,
        rep_returncodes=returncodes,
        rep_observations=observations,
        rep_timestamps=timestamps,
        use_perf=request.use_perf,
    )
    if not isinstance(point, ScalePoint):
        raise FloorPairRunError("measure_point が ScalePoint を返さない", status="measure_failed")
    return MeasurementResult(
        session_id=request.session_id,
        point_records=point.records,
        point_threads=point.threads,
        throughputs=tuple(point.throughputs),
        rep_returncodes=tuple(returncodes),
        rep_observations=tuple(dict(item) for item in observations),
        rep_timestamps=tuple(dict(item) for item in timestamps),
    )


def _run_probe(argv: Sequence[str], timeout_s: int) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _machine_env_tag_for_site(site: str) -> str:
    if site == site_policy.PEGASUS_COMPUTE:
        try:
            return env_contract.lookup_required_attestation_contract().env_tag
        except Exception as exc:
            raise FloorPairRunError(
                "required attestation contract から env_tag を一意に導出できない",
                status="environment_mismatch",
            ) from exc
    if site == site_policy.OTHER:
        try:
            contracts = tuple(env_contract.REGISTRY.values())
            candidates = tuple(
                contract for contract in contracts if contract.attestation_mode == "none"
            )
            tags = {contract.env_tag for contract in candidates}
            registry_tags = tuple(contract.env_tag for contract in contracts)
        except Exception as exc:
            raise FloorPairRunError(
                "none attestation contract から env_tag を一意に導出できない",
                status="environment_mismatch",
            ) from exc
        if len(candidates) != 1 or len(tags) != 1 or len(registry_tags) != len(set(registry_tags)):
            raise FloorPairRunError(
                "none attestation contract から env_tag を一意に導出できない",
                status="environment_mismatch",
            )
        return candidates[0].env_tag
    raise FloorPairRunError(
        f"測定を許可しない live site: {site!r}", status="environment_mismatch"
    )


def _assert_live_environment(spec: FloorPairSpec) -> None:
    site = site_policy.current_site(require_evidence=True)
    if site in {site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT}:
        raise FloorPairRunError(
            f"測定を許可しない live site: {site!r}", status="environment_mismatch"
        )
    if site != spec.environment.site:
        raise FloorPairRunError(
            f"live site {site!r} が spec {spec.environment.site!r} と一致しない",
            status="environment_mismatch",
        )
    live_env_tag = _machine_env_tag_for_site(site)
    if live_env_tag != spec.environment.env_tag:
        raise FloorPairRunError(
            f"live env_tag {live_env_tag!r} が spec {spec.environment.env_tag!r} と一致しない",
            status="environment_mismatch",
        )


class _ExclusiveWriter:
    def __init__(self, path: Path):
        if not hasattr(os, "O_NOFOLLOW"):
            raise FloorPairRunError("O_NOFOLLOW が利用できない", status="output_unsafe")
        flags = os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW
        self.path = path
        self.fd = os.open(path, flags, 0o600)
        self.closed = False

    def write_object(self, value: object) -> None:
        raw = _canonical_bytes(value)
        offset = 0
        while offset < len(raw):
            written = os.write(self.fd, raw[offset:])
            if written <= 0:
                raise OSError("artifact write が進行しない")
            offset += written
        os.fsync(self.fd)

    def close(self) -> None:
        if not self.closed:
            os.close(self.fd)
            self.closed = True

    def __enter__(self) -> _ExclusiveWriter:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()


def _find_window(spec: FloorPairSpec, window_id: str) -> WindowConfig:
    matches = [window for window in spec.windows if window.window_id == window_id]
    if len(matches) != 1:
        raise FloorPairRunError(f"未知または重複 window_id: {window_id!r}", status="window_invalid")
    return matches[0]


def _window_sessions(plan: MeasurementPlan, window_id: str) -> tuple[PlannedSession, ...]:
    sessions = tuple(session for session in plan.sessions if session.window_id == window_id)
    if len(sessions) == 0:
        raise FloorPairRunError("window に planned session がない", status="window_invalid")
    return sessions


def _probe_once(
    environment: EnvironmentConfig,
    probe_fn: Callable[[Sequence[str], int], tuple[int, str, str]],
) -> dict[str, object]:
    try:
        raw = probe_fn(COMPETING_PROBE_ARGV, environment.probe_timeout_s)
        if type(raw) is not tuple or len(raw) != 3:
            raise TypeError("probe result は exact (rc, stdout, stderr) でなければならない")
        rc, stdout, stderr = raw
        if type(rc) is not int or type(stdout) is not str or type(stderr) is not str:
            raise TypeError("probe result の型が不正")
        competitors = runner.classify_competing_probe(
            rc, stdout, stderr, COMPETING_PROBE_ARGV
        )
        status = "clear" if len(competitors) == 0 else "competing"
        return {
            "status": status,
            "returncode": rc,
            "stdout": stdout,
            "stderr": stderr,
            "competitors": competitors,
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "indeterminate",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "competitors": [],
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }


def _json_safe(value: object) -> object:
    if type(value) is float and not math.isfinite(value):
        return None
    if type(value) is tuple:
        return [_json_safe(item) for item in value]
    if type(value) is list:
        return [_json_safe(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _measurement_complete(
    result: MeasurementResult,
    request: MeasurementRequest,
) -> tuple[bool, str | None]:
    if not isinstance(result, MeasurementResult):
        return False, "production measurement adapter が MeasurementResult を返さない"
    if result.session_id != request.session_id:
        return False, "MeasurementResult.session_id 不一致"
    if result.point_records != request.perf_config.records:
        return False, "ScalePoint.records 不一致"
    if result.point_threads != request.perf_config.threads:
        return False, "ScalePoint.threads 不一致"
    reps = request.perf_config.reps
    if len(result.throughputs) != reps:
        return False, "throughputs 件数が reps と不一致"
    for value in result.throughputs:
        if type(value) not in {int, float}:
            return False, "throughput が exact number でない"
        if not math.isfinite(float(value)) or float(value) <= 0:
            return False, "throughput が有限正数でない"
    if len(result.rep_returncodes) != reps:
        return False, "rep_returncodes 件数が reps と不一致"
    if any(type(code) is not int or code != 0 for code in result.rep_returncodes):
        return False, "rep returncode が exact 0 でない"
    if len(result.rep_observations) != reps:
        return False, "rep_observations 件数が reps と不一致"
    if len(result.rep_timestamps) != reps:
        return False, "rep_timestamps 件数が reps と不一致"
    for index, observation in enumerate(result.rep_observations):
        if type(observation) is not dict:
            return False, "rep_observation が object でない"
        if "rep_index" not in observation or observation["rep_index"] != index:
            return False, "rep_observation.rep_index 不一致"
        if "returncode" not in observation or observation["returncode"] != 0:
            return False, "rep_observation.returncode 不一致"
        if "throughput" not in observation:
            return False, "rep_observation.throughput 欠落"
        observed = observation["throughput"]
        if type(observed) not in {int, float} or not math.isfinite(float(observed)):
            return False, "rep_observation.throughput が非有限または型不正"
        if float(observed) != float(result.throughputs[index]):
            return False, "rep_observation.throughput が raw throughput と不一致"
    for index, timestamp in enumerate(result.rep_timestamps):
        if type(timestamp) is not dict:
            return False, "rep_timestamp が object でない"
        if set(timestamp) != {"rep_index", "started_at_ns", "finished_at_ns"}:
            return False, "rep_timestamp key 不一致"
        if timestamp["rep_index"] != index:
            return False, "rep_timestamp.rep_index 不一致"
        for key in ("started_at_ns", "finished_at_ns"):
            if type(timestamp[key]) is not int or timestamp[key] < 0:
                return False, f"rep_timestamp.{key} が exact 非負 int でない"
        if timestamp["started_at_ns"] > timestamp["finished_at_ns"]:
            return False, "rep_timestamp の時刻順が逆"
    return True, None


def _session_record_base(session: PlannedSession) -> dict[str, object]:
    return {
        "event": "session",
        "session_id": session.session_id,
        "window_id": session.window_id,
        "campaign_id": session.campaign_id,
        "pair_id": session.pair_id,
        "cell_id": session.cell_id,
        "sample_index": session.sample_index,
        "role": session.role,
        "artifact_id": session.artifact_id,
        "schedule_index": session.schedule_index,
    }


def _not_run_record(session: PlannedSession, now_fn: Callable[[], datetime]) -> dict[str, object]:
    record = _session_record_base(session)
    observed = _format_utc(now_fn())
    record.update(
        {
            "status": "not_run_after_fail_closed",
            "throughputs": [],
            "rep_returncodes": [],
            "rep_observations": [],
            "rep_timestamps": [],
            "binary_sha256": None,
            "pre_probe": None,
            "post_probe": None,
            "started_at": observed,
            "finished_at": observed,
            "error": "earlier session failed closed",
        }
    )
    return record


def _run_planned_session(
    *,
    spec: FloorPairSpec,
    window: WindowConfig,
    session: PlannedSession,
    probe_fn: Callable[[Sequence[str], int], tuple[int, str, str]],
    now_fn: Callable[[], datetime],
) -> dict[str, object]:
    artifacts = {artifact.artifact_id: artifact for artifact in spec.artifacts}
    cells = {cell.cell_id: cell for cell in spec.cells}
    artifact = artifacts[session.artifact_id]
    cell = cells[session.cell_id]
    binary = _resolve_regular(
        spec.repo_root,
        artifact.binary_relpath,
        label=f"session {session.session_id} binary",
    )
    record = _session_record_base(session)
    started = now_fn()
    if started < window.not_before or started >= window.not_after:
        observed = _format_utc(started)
        record.update(
            {
                "status": "outside_window",
                "throughputs": [],
                "rep_returncodes": [],
                "rep_observations": [],
                "rep_timestamps": [],
                "binary_sha256": None,
                "pre_probe": None,
                "post_probe": None,
                "started_at": observed,
                "finished_at": observed,
                "error": "session start が半開時間窓の外",
            }
        )
        return record
    try:
        buildcache.assert_binary_sha256(str(binary), artifact.binary_sha256)
        buildcache._assert_no_trace_symbols(str(binary))
    except Exception as exc:
        record.update(
            {
                "status": "binary_binding_failed",
                "throughputs": [],
                "rep_returncodes": [],
                "rep_observations": [],
                "rep_timestamps": [],
                "binary_sha256": None,
                "pre_probe": None,
                "post_probe": None,
                "started_at": _format_utc(started),
                "finished_at": _format_utc(now_fn()),
                "error": f"{type(exc).__name__}: {str(exc)[:500]}",
            }
        )
        return record
    pre_probe = _probe_once(spec.environment, probe_fn)
    measurement: MeasurementResult | None = None
    measurement_error: str | None = None
    if pre_probe["status"] == "clear":
        request = MeasurementRequest(
            session_id=session.session_id,
            binary_path=str(binary),
            perf_config=cell.perf_config,
            clocks_per_us=spec.environment.clocks_per_us,
            numactl_argv=spec.environment.numactl_argv,
            use_perf=spec.environment.use_perf,
            timeout_s=spec.environment.timeout_s,
            extra_env=spec.environment.extra_env,
        )
        try:
            measurement = _measure_with_runner(request)
        except Exception as exc:
            measurement_error = f"{type(exc).__name__}: {str(exc)[:500]}"
    post_probe = _probe_once(spec.environment, probe_fn)
    status = "complete"
    error: str | None = None
    if pre_probe["status"] == "competing":
        status = "pre_probe_competing"
        error = "pre probe detected competing process"
    elif pre_probe["status"] == "indeterminate":
        status = "pre_probe_indeterminate"
        error = str(pre_probe["error"])
    elif measurement_error is not None:
        status = "measure_failed"
        error = measurement_error
    elif measurement is None:
        status = "measure_failed"
        error = "measurement result がない"
    elif post_probe["status"] == "competing":
        status = "post_probe_competing"
        error = "post probe detected competing process"
    elif post_probe["status"] == "indeterminate":
        status = "post_probe_indeterminate"
        error = str(post_probe["error"])
    else:
        request = MeasurementRequest(
            session_id=session.session_id,
            binary_path=str(binary),
            perf_config=cell.perf_config,
            clocks_per_us=spec.environment.clocks_per_us,
            numactl_argv=spec.environment.numactl_argv,
            use_perf=spec.environment.use_perf,
            timeout_s=spec.environment.timeout_s,
            extra_env=spec.environment.extra_env,
        )
        complete, incomplete_reason = _measurement_complete(measurement, request)
        if not complete:
            status = "measure_incomplete"
            error = incomplete_reason
    record.update(
        {
            "status": status,
            "throughputs": (
                [] if measurement is None else _json_safe(measurement.throughputs)
            ),
            "rep_returncodes": (
                [] if measurement is None else _json_safe(measurement.rep_returncodes)
            ),
            "rep_observations": (
                [] if measurement is None else _json_safe(measurement.rep_observations)
            ),
            "rep_timestamps": (
                [] if measurement is None else _json_safe(measurement.rep_timestamps)
            ),
            "binary_sha256": artifact.binary_sha256,
            "pre_probe": pre_probe,
            "post_probe": post_probe,
            "started_at": _format_utc(started),
            "finished_at": _format_utc(now_fn()),
            "error": error,
        }
    )
    return record


def run_window(
    spec: FloorPairSpec,
    plan: MeasurementPlan,
    window_id: str,
    *,
    probe_fn: Callable[[Sequence[str], int], tuple[int, str, str]],
    now_fn: Callable[[], datetime],
) -> WindowRunResult:
    """一つの時間窓を create-only JSONL へ実行する。

    権威経路の測定実体は常に :func:`_measure_with_runner` であり、高位の
    measurement callable を caller から受け取る seam は持たない。
    live env の一致は output path を確保する前に検査する。output の確保は測定前の
    最初の副作用であり、以後は header、各 planned session、terminal を追記する。
    """
    if not isinstance(spec, FloorPairSpec) or not isinstance(plan, MeasurementPlan):
        raise TypeError("spec/plan の型が不正")
    try:
        _assert_plan_exact(spec, plan, error_type=FloorPairBindingError)
    except FloorPairBindingError as exc:
        raise FloorPairRunError(str(exc), status="plan_invalid") from exc
    window = _find_window(spec, window_id)
    sessions = _window_sessions(plan, window_id)
    _assert_live_environment(spec)
    runtime_head = _git_head(spec.repo_root)
    if (
        runtime_head != spec.loaded_head
        or runtime_head != spec.provenance.source_commit
    ):
        raise FloorPairRunError(
            "runtime HEAD が loaded HEAD / provenance.source_commit と一致しない",
            status="source_commit_mismatch",
        )
    output_path = _validate_output_path(
        spec.repo_root, window.artifact_relpath, label=f"window {window.window_id} output"
    )
    header = {
        "event": "header",
        "schema": WINDOW_SCHEMA,
        "format": spec.outputs.window_format,
        "spec_relpath": spec.spec_relpath,
        "spec_sha256": spec.spec_sha256,
        "loaded_head": spec.loaded_head,
        "runtime_head": runtime_head,
        "plan_sha256": plan.plan_sha256,
        "randomization_algorithm": plan.randomization_algorithm,
        "seed_hex": plan.seed_hex,
        "window_id": window.window_id,
        "campaign_id": window.campaign_id,
        "planned_sessions": [dataclasses.asdict(session) for session in sessions],
        "window_count": len(spec.windows),
        "pair_sample_count": sum(window.sample_count for _pair_id in window.pair_ids),
        "session_count": len(sessions),
        "reps_per_session": {
            cell.cell_id: cell.perf_config.reps for cell in spec.cells
        },
    }
    records: list[dict[str, object]] = []
    failed = False
    with _ExclusiveWriter(output_path) as writer:
        writer.write_object(header)
        for session in sessions:
            if failed:
                record = _not_run_record(session, now_fn)
            else:
                record = _run_planned_session(
                    spec=spec,
                    window=window,
                    session=session,
                    probe_fn=probe_fn,
                    now_fn=now_fn,
                )
                if record["status"] != "complete":
                    failed = True
            writer.write_object(record)
            records.append(record)
        terminal_status = "complete" if not failed else "incomplete"
        writer.write_object(
            {
                "event": "terminal",
                "status": terminal_status,
                "window_id": window.window_id,
                "planned_session_count": len(sessions),
                "recorded_session_count": len(records),
            }
        )
    artifact_raw = output_path.read_bytes()
    return WindowRunResult(
        status=terminal_status,
        window_id=window.window_id,
        artifact_relpath=window.artifact_relpath,
        artifact_sha256=hashlib.sha256(artifact_raw).hexdigest(),
        session_count=len(records),
    )


def _read_jsonl(path: Path, *, label: str) -> tuple[dict[str, object], ...]:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise FloorPairBindingError(f"{label} が存在しない: {exc}") from exc
    if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
        raise FloorPairBindingError(f"{label} は symlink でない regular file でなければならない")
    raw = path.read_bytes()
    if len(raw) == 0 or not raw.endswith(b"\n"):
        raise FloorPairBindingError(f"{label} は空でなく末尾改行が必要")
    lines = raw.splitlines()
    result: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        if len(line) == 0:
            raise FloorPairBindingError(f"{label}[{index}] は空行")
        value = _load_json(
            line,
            label=f"{label}[{index}]",
            error_type=FloorPairBindingError,
        )
        if type(value) is not dict:
            raise FloorPairBindingError(f"{label}[{index}] は object でない")
        result.append(value)
    return tuple(result)


def _validate_window_artifact(
    *, spec: FloorPairSpec, plan: MeasurementPlan, window: WindowConfig
) -> tuple[bytes, tuple[dict[str, object], ...]]:
    path = _resolve_regular(
        spec.repo_root, window.artifact_relpath, label=f"window artifact {window.window_id}"
    )
    records = _read_jsonl(path, label=f"window artifact {window.window_id}")
    if len(records) < 3:
        raise FloorPairBindingError(f"window artifact {window.window_id} の record が少なすぎる")
    header = records[0]
    terminal = records[-1]
    expected_sessions = _window_sessions(plan, window.window_id)
    expected_plans = [dataclasses.asdict(session) for session in expected_sessions]
    expected_header = {
        "event": "header",
        "schema": WINDOW_SCHEMA,
        "format": spec.outputs.window_format,
        "spec_relpath": spec.spec_relpath,
        "spec_sha256": spec.spec_sha256,
        "loaded_head": spec.loaded_head,
        "runtime_head": spec.provenance.source_commit,
        "plan_sha256": plan.plan_sha256,
        "randomization_algorithm": plan.randomization_algorithm,
        "seed_hex": plan.seed_hex,
        "window_id": window.window_id,
        "campaign_id": window.campaign_id,
        "planned_sessions": expected_plans,
        "window_count": len(spec.windows),
        "pair_sample_count": window.sample_count * len(window.pair_ids),
        "session_count": len(expected_sessions),
        "reps_per_session": {
            cell.cell_id: cell.perf_config.reps for cell in spec.cells
        },
    }
    if header != expected_header:
        raise FloorPairBindingError(f"window artifact {window.window_id} header が不正")
    session_records = records[1:-1]
    expected_terminal = {
        "event": "terminal",
        "status": "complete",
        "window_id": window.window_id,
        "planned_session_count": len(expected_sessions),
        "recorded_session_count": len(session_records),
    }
    if terminal != expected_terminal:
        raise FloorPairBindingError(f"window artifact {window.window_id} terminal が不正")
    planned_ids = [session.session_id for session in expected_sessions]
    expected_by_id = {session.session_id: session for session in expected_sessions}
    recorded_ids: list[str] = []
    for index, record in enumerate(session_records):
        if "event" not in record or "session_id" not in record:
            raise FloorPairBindingError(
                f"window artifact {window.window_id} session[{index}] に event/session_id がない"
            )
        if record["event"] != "session" or type(record["session_id"]) is not str:
            raise FloorPairBindingError(
                f"window artifact {window.window_id} session[{index}] が不正"
            )
        recorded_ids.append(record["session_id"])
    planned_counts = Counter(planned_ids)
    recorded_counts = Counter(recorded_ids)
    if planned_counts != recorded_counts:
        raise FloorPairBindingError(
            f"window artifact {window.window_id} session ID/count が plan と exact 一致しない"
        )
    if recorded_ids != planned_ids:
        raise FloorPairBindingError(
            f"window artifact {window.window_id} session 順が plan と exact 一致しない"
        )
    metadata_fields = (
        "window_id", "campaign_id", "pair_id", "cell_id", "sample_index",
        "role", "artifact_id", "schedule_index",
    )
    for record in session_records:
        expected = expected_by_id[record["session_id"]]
        for field in metadata_fields:
            if field not in record or record[field] != getattr(expected, field):
                raise FloorPairBindingError(
                    f"window artifact {window.window_id} session {record['session_id']} "
                    f"metadata.{field} 不一致"
                )
        if "status" not in record or record["status"] not in SESSION_STATUSES:
            raise FloorPairBindingError(
                f"window artifact {window.window_id} session status が閉集合外"
            )
    raw = path.read_bytes()
    return raw, tuple(session_records)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(float(value) for value in values)
    count = len(ordered)
    middle = count // 2
    if count % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _status_from_records(
    spec: FloorPairSpec,
    records: Sequence[dict[str, object]],
) -> str | None:
    cells = {cell.cell_id: cell for cell in spec.cells}
    for record in records:
        if record["status"] != "complete":
            return "not_generated_missing_samples"
        values = record["throughputs"]
        expected_reps = cells[record["cell_id"]].perf_config.reps
        if type(values) is not list or len(values) != expected_reps:
            return "not_generated_missing_samples"
        for value in values:
            if type(value) not in {int, float}:
                return "not_generated_missing_samples"
            if not math.isfinite(float(value)) or float(value) <= 0:
                return "not_generated_missing_samples"
        returncodes = record["rep_returncodes"]
        observations = record["rep_observations"]
        timestamps = record["rep_timestamps"]
        if type(returncodes) is not list or len(returncodes) != expected_reps:
            return "not_generated_missing_samples"
        if any(type(code) is not int or code != 0 for code in returncodes):
            return "not_generated_missing_samples"
        if type(observations) is not list or len(observations) != expected_reps:
            return "not_generated_missing_samples"
        if type(timestamps) is not list or len(timestamps) != expected_reps:
            return "not_generated_missing_samples"
        for index, observation in enumerate(observations):
            if type(observation) is not dict:
                return "not_generated_missing_samples"
            if not {"rep_index", "returncode", "throughput"}.issubset(observation):
                return "not_generated_missing_samples"
            if observation["rep_index"] != index or observation["returncode"] != 0:
                return "not_generated_missing_samples"
            observed = observation["throughput"]
            if type(observed) not in {int, float}:
                return "not_generated_missing_samples"
            if not math.isfinite(float(observed)):
                return "not_generated_missing_samples"
            if float(observed) != float(values[index]):
                return "not_generated_missing_samples"
        for index, timestamp in enumerate(timestamps):
            if type(timestamp) is not dict:
                return "not_generated_missing_samples"
            if set(timestamp) != {"rep_index", "started_at_ns", "finished_at_ns"}:
                return "not_generated_missing_samples"
            if timestamp["rep_index"] != index:
                return "not_generated_missing_samples"
            started = timestamp["started_at_ns"]
            finished = timestamp["finished_at_ns"]
            if type(started) is not int or type(finished) is not int:
                return "not_generated_missing_samples"
            if started < 0 or finished < started:
                return "not_generated_missing_samples"
    return None


def _derive_strata(
    *,
    spec: FloorPairSpec,
    plan: MeasurementPlan,
    records: Sequence[dict[str, object]],
) -> tuple[list[dict[str, object]], float]:
    by_session = {record["session_id"]: record for record in records}
    strata_values: dict[tuple[str, str], list[float]] = {
        stratum: [] for stratum in spec.statistics.closed_strata
    }
    sample_keys = sorted(
        {
            (session.window_id, session.pair_id, session.sample_index)
            for session in plan.sessions
        }
    )
    derived_samples: list[dict[str, object]] = []
    for window_id, pair_id, sample_index in sample_keys:
        matching = [
            session
            for session in plan.sessions
            if session.window_id == window_id
            and session.pair_id == pair_id
            and session.sample_index == sample_index
        ]
        roles = {session.role: session for session in matching}
        if set(roles) != set(_ROLES):
            raise FloorPairBindingError("pair sample の 3 role が exact 完備でない")
        medians: dict[str, float] = {}
        for role in _ROLES:
            record = by_session[roles[role].session_id]
            raw_values = record["throughputs"]
            medians[role] = _median(raw_values)
        gain = compute_gain_difference(
            medians["candidate_1"],
            medians["candidate_2"],
            medians["reference"],
        )
        strata_values[(window_id, pair_id)].append(gain.difference)
        derived_samples.append(
            {
                "window_id": window_id,
                "pair_id": pair_id,
                "sample_index": sample_index,
                "session_medians": medians,
                "gain_1": gain.gain_1,
                "gain_2": gain.gain_2,
                "difference": gain.difference,
            }
        )
    strata: list[dict[str, object]] = []
    stratum_uppers: list[float] = []
    for window_id, pair_id in spec.statistics.closed_strata:
        values = strata_values[(window_id, pair_id)]
        upper = apply_upper_statistic(spec.statistics.stratum_upper, values)
        stratum_uppers.append(upper)
        strata.append(
            {
                "window_id": window_id,
                "pair_id": pair_id,
                "values": values,
                "upper_function": spec.statistics.stratum_upper,
                "upper": upper,
            }
        )
    final_upper = apply_upper_statistic(
        spec.statistics.final_combiner, stratum_uppers
    )
    return [{"samples": derived_samples, "strata": strata}], final_upper


def finalize_floor(
    spec: FloorPairSpec,
    plan: MeasurementPlan,
    *,
    now_fn: Callable[[], datetime],
) -> FinalFloorResult:
    """全 planned window を raw から再計算し、summary を exclusive-create する。"""
    _assert_plan_exact(spec, plan, error_type=FloorPairBindingError)
    window_entries: list[dict[str, object]] = []
    all_records: list[dict[str, object]] = []
    for window in spec.windows:
        raw, records = _validate_window_artifact(spec=spec, plan=plan, window=window)
        window_entries.append(
            {
                "window_id": window.window_id,
                "campaign_id": window.campaign_id,
                "artifact_relpath": window.artifact_relpath,
                "artifact_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        all_records.extend(records)
    status = _status_from_records(spec, all_records)
    derived: list[dict[str, object]] = []
    upper: float | None = None
    candidate_floor: float | None = None
    if status is None:
        try:
            derived, upper = _derive_strata(spec=spec, plan=plan, records=all_records)
        except (ValueError, OverflowError):
            status = "not_generated_missing_samples"
            upper = None
        if status is None:
            if upper is None or not math.isfinite(upper):
                status = "not_generated_missing_samples"
                upper = None
            elif upper >= 1.0:
                status = "not_generated_upper_out_of_domain"
            else:
                status = "generated"
                candidate_floor = upper
    summary = {
        "schema": SUMMARY_SCHEMA,
        "format": spec.outputs.summary_format,
        "spec_relpath": spec.spec_relpath,
        "spec_sha256": spec.spec_sha256,
        "loaded_head": spec.loaded_head,
        "plan_sha256": plan.plan_sha256,
        "generated_at": _format_utc(now_fn()),
        "status": status,
        "upper": upper,
        "candidate_floor": candidate_floor,
        "window_artifacts": window_entries,
        "derivation": derived,
        "proof_limitations": {
            "section": "証明していないこと",
            "items": list(NOT_PROVEN),
        },
    }
    summary_path = _validate_output_path(
        spec.repo_root, spec.outputs.summary_relpath, label="summary output"
    )
    with _ExclusiveWriter(summary_path) as writer:
        writer.write_object(summary)
    raw = summary_path.read_bytes()
    return FinalFloorResult(
        status=str(status),
        upper=upper,
        candidate_floor=candidate_floor,
        summary_relpath=spec.outputs.summary_relpath,
        summary_sha256=hashlib.sha256(raw).hexdigest(),
    )


def _plan_document(plan: MeasurementPlan) -> dict[str, object]:
    return {
        "schema": plan.schema,
        "spec_sha256": plan.spec_sha256,
        "randomization_algorithm": plan.randomization_algorithm,
        "seed_hex": plan.seed_hex,
        "sessions": [dataclasses.asdict(session) for session in plan.sessions],
        "plan_sha256": plan.plan_sha256,
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--execute-window")
    modes.add_argument("--finalize", action="store_true")
    args = parser.parse_args(argv)
    spec = load_frozen_spec(
        args.spec,
        args.expected_sha256,
        repo_root=args.repo_root,
    )
    plan = make_measurement_plan(spec)
    if args.validate_only:
        sys.stdout.buffer.write(_canonical_bytes(_plan_document(plan)))
        return 0
    if args.execute_window is not None:
        result = run_window(
            spec,
            plan,
            args.execute_window,
            probe_fn=_run_probe,
            now_fn=_utc_now,
        )
        sys.stdout.buffer.write(_canonical_bytes(dataclasses.asdict(result)))
        return 0
    result = finalize_floor(spec, plan, now_fn=_utc_now)
    sys.stdout.buffer.write(_canonical_bytes(dataclasses.asdict(result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
