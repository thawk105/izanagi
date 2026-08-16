# -*- coding: utf-8 -*-
"""Non-authoritative 8b oracle ``n`` pilot.

The pilot records raw trace-disabled performance observations and derives an
indifference-zone selection-error table.  Its output is never a certified,
floor, oracle, or ``n`` decision input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import shutil
import stat
import statistics
import struct
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.runner import measure_point

from . import buildcache, env_contract, s8b_floor_contract, s8b_oracle_manifest
from .build_admission import (
    GeneratorId,
    ReviewId,
    build_run_context,
    derive_build_admission,
)
from .p2_2 import _assert_single_tenant
from .s1_direct_comparison import _PREPARE_CELL_CONFIGURATIONS, prepare_cell
from .s8b_experiment_numbers import APPROVED_EXTIME_S, APPROVED_REPS
from .s8b_floor_campaign import (
    _canonical_floor_fetchcontent_base,
    _prepare_floor_oracle_dependency,
)
from .s8b_freeze_io import load_verified_freeze
from .s8b_holdout_freeze import holdout_conjunction_hits, verify_document
from .s8b_materialization import prepared_binding, reviewed_source_capability
from . import source_digest


ROOT = Path(__file__).resolve().parents[2]
FREEZE_REL = Path("output/s8b-freeze/holdout_freeze.json")
JOB_SCRIPT_REL = Path("tools/pegasus/oracle_n_pilot.sh")
PROTOCOL_SCHEMA = "pilot-protocol/v1"
RESULT_SCHEMA = "pilot-result/v1"
AGGREGATE_SCHEMA = "pilot-aggregate/v1"
SCHEDULE_ALGORITHM = "s8b-oracle-manifest/complete-block-v1"
_HEX40 = frozenset("0123456789abcdef")
_HEX64 = _HEX40


class PilotError(RuntimeError):
    """The pilot cannot prove an input, execution, or output invariant."""


@dataclass(frozen=True)
class PilotProtocol:
    document: Mapping[str, object]
    protocol_sha256: str
    freeze_path: str
    freeze_sha256: str
    source_commit: str
    driver_path: str
    driver_sha256: str
    job_script_path: str
    job_script_sha256: str
    ccbench_pin: str
    env_tag: str
    contract_sha256: str
    activation_generation: int
    pilot_rounds: int | None
    master_seed: str
    allocation_count: int
    allocation_role: str
    stock_configuration: str
    candidate_ns: tuple[int, ...]
    resampling_seed: str
    resampling_iterations: int
    ucl_confidence: float
    deltas: tuple[float, ...]
    alphas: tuple[float, ...]
    max_abs_position_correlation: float
    max_abs_relative_time_slope_per_second: float
    measurement_declaration: Mapping[str, object]


@dataclass(frozen=True)
class PilotInputs:
    protocol: PilotProtocol
    freeze: Mapping[str, object]
    freeze_sha256: str
    cells: tuple[Mapping[str, object], ...]
    held_markers: tuple[Mapping[str, object], ...]
    freeze_verification_status: str
    contract: object


@dataclass(frozen=True)
class PilotBinary:
    cell_id: str
    entry_sha256: str
    binding_sha256: str
    binary_sha256: str
    binary_path: Path
    cache_hit: bool
    materialize_elapsed_s: float
    worktree_identity_sha256: str
    isolated_worktree: bool
    pre_materialization_clean_assertion: bool
    source_tracked_clean: bool
    source_tracked_paths: tuple[str, ...]

    def public_record(self) -> dict[str, object]:
        return {
            "cell_id": self.cell_id,
            "entry_sha256": self.entry_sha256,
            "binding_sha256": self.binding_sha256,
            "binary_sha256": self.binary_sha256,
            "cache_hit": self.cache_hit,
            "cache_state": "hit" if self.cache_hit else "miss",
            "materialize_elapsed_s": self.materialize_elapsed_s,
            "worktree_identity_sha256": self.worktree_identity_sha256,
            "isolated_worktree": self.isolated_worktree,
            "pre_materialization_clean_assertion": {
                "passed": self.pre_materialization_clean_assertion,
                "gateway": "patchharness.checkout/assert_pinned_clean",
            },
            "source_clean_assertion": {
                "tracked_clean": self.source_tracked_clean,
                "tracked_paths": list(self.source_tracked_paths),
                "allowlist_checked": True,
            },
        }


@dataclass(frozen=True)
class SessionObservation:
    seq: int
    pilot_round: int
    position: int
    cell_id: str
    monotonic_start_s: float
    monotonic_end_s: float
    duration_s: float
    load1_before: float
    load1_after: float
    throughputs: tuple[float, ...]
    throughput_binary64_hex: tuple[str, ...]
    outer_median: float
    abort_rate: float | None
    returncodes: tuple[int, ...]
    binary_sha256_at_measure: str
    cache_hit: bool
    materialize_elapsed_s: float

    def as_record(self) -> dict[str, object]:
        return {
            "seq": self.seq,
            "pilot_round": self.pilot_round,
            "position": self.position,
            "cell_id": self.cell_id,
            "monotonic_start_s": self.monotonic_start_s,
            "monotonic_end_s": self.monotonic_end_s,
            "duration_s": self.duration_s,
            "load1_before": self.load1_before,
            "load1_after": self.load1_after,
            "throughputs": list(self.throughputs),
            "throughput_binary64_hex": list(self.throughput_binary64_hex),
            "outer_median": self.outer_median,
            "abort_rate": self.abort_rate,
            "returncodes": list(self.returncodes),
            "binary_sha256_at_measure": self.binary_sha256_at_measure,
            "cache_hit": self.cache_hit,
            "cache_state": "hit" if self.cache_hit else "miss",
            "materialize_elapsed_s": self.materialize_elapsed_s,
        }


def _is_hex(value: object, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and value == value.lower()
        and all(character in _HEX64 for character in value)
    )


def _strict_object_pairs(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PilotError(f"protocol JSON に重複 key がある: {key}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise PilotError(f"protocol JSON に非有限定数がある: {token}")


def _exact_mapping(value: object, keys: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        got = sorted(value) if isinstance(value, Mapping) else type(value).__name__
        raise PilotError(f"{label} key 集合が不正: {got!r}")
    return value


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise PilotError(f"{label} が正整数でない")
    return value


def _finite_probability(value: object, label: str) -> float:
    if type(value) not in {int, float}:
        raise PilotError(f"{label} が有限確率でない")
    result = float(value)
    if not math.isfinite(result) or not 0.0 < result < 1.0:
        raise PilotError(f"{label} が 0 と 1 の間でない")
    return result


def _positive_finite(value: object, label: str) -> float:
    if type(value) not in {int, float}:
        raise PilotError(f"{label} が正の有限値でない")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise PilotError(f"{label} が正の有限値でない")
    return result


def load_protocol(path: Path) -> PilotProtocol:
    """Load one exact, duplicate-free preregistered pilot protocol."""
    try:
        document = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object_pairs,
            parse_constant=_reject_constant,
        )
    except PilotError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"protocol を strict parse できない: {exc}") from exc
    top = _exact_mapping(document, {
        "schema_version", "authority", "default_effect", "freeze", "source",
        "environment", "design", "measurement_declaration",
    }, "protocol")
    if (
        top["schema_version"] != PROTOCOL_SCHEMA
        or top["authority"] != "none"
        or top["default_effect"] != "no-state-change"
    ):
        raise PilotError("protocol authority/schema/default effect が不正")
    freeze = _exact_mapping(top["freeze"], {"path", "sha256"}, "freeze")
    source = _exact_mapping(top["source"], {
        "commit", "driver_path", "driver_sha256", "job_script_path",
        "job_script_sha256",
    }, "source")
    environment = _exact_mapping(top["environment"], {
        "env_tag", "contract_sha256", "activation_generation", "ccbench_pin",
    }, "environment")
    design = _exact_mapping(top["design"], {
        "pilot_rounds", "master_seed", "allocation_count", "allocation_role",
        "reps", "extime_s", "stock_configuration", "candidate_ns",
        "resampling_seed", "resampling_iterations", "ucl_confidence", "deltas",
        "alphas", "conditioning", "selection_error", "tie_rule",
        "schedule_algorithm", "counterbalance_analysis", "drift_diagnostics",
        "lower_bound",
    }, "design")
    drift = _exact_mapping(design["drift_diagnostics"], {
        "position_metric", "max_abs_position_correlation", "time_metric",
        "max_abs_relative_time_slope_per_second",
    }, "design.drift_diagnostics")
    for label, value in {
        "freeze.path": freeze["path"],
        "source.driver_path": source["driver_path"],
        "source.job_script_path": source["job_script_path"],
        "environment.env_tag": environment["env_tag"],
        "design.master_seed": design["master_seed"],
        "design.allocation_role": design["allocation_role"],
        "design.stock_configuration": design["stock_configuration"],
        "design.resampling_seed": design["resampling_seed"],
    }.items():
        if type(value) is not str or not value:
            raise PilotError(f"{label} が空でない str でない")
    if freeze["path"] != FREEZE_REL.as_posix():
        raise PilotError("freeze.path が canonical holdout freeze path でない")
    if source["driver_path"] != "orchestrator/campaign/s8b_oracle_n_pilot.py":
        raise PilotError("source.driver_path が pilot driver canonical path でない")
    if source["job_script_path"] != JOB_SCRIPT_REL.as_posix():
        raise PilotError("source.job_script_path が pilot job canonical path でない")
    for label, value, length in (
        ("freeze.sha256", freeze["sha256"], 64),
        ("source.commit", source["commit"], 40),
        ("source.driver_sha256", source["driver_sha256"], 64),
        ("source.job_script_sha256", source["job_script_sha256"], 64),
        ("environment.contract_sha256", environment["contract_sha256"], 64),
        ("environment.ccbench_pin", environment["ccbench_pin"], 40),
    ):
        if not _is_hex(value, length):
            raise PilotError(f"{label} が full lowercase hex でない")
    pilot_rounds = design["pilot_rounds"]
    if pilot_rounds is not None:
        pilot_rounds = _positive_int(pilot_rounds, "design.pilot_rounds")
    if design["reps"] != APPROVED_REPS or design["extime_s"] != APPROVED_EXTIME_S:
        raise PilotError("design reps/extime が approved experiment numbers と不一致")
    if (
        design["conditioning"] != "all-rows-eligible"
        or design["selection_error"] != "indifference-zone-relative"
        or design["tie_rule"] != "not-an-error"
        or design["schedule_algorithm"] != SCHEDULE_ALGORITHM
        or design["counterbalance_analysis"]
        != "position-and-monotonic-drift-diagnostics-only"
        or design["lower_bound"] is not True
    ):
        raise PilotError("design の事前登録済み選択規則が不一致")
    if (
        drift["position_metric"] != "spearman-rank-correlation"
        or drift["time_metric"] != "relative-ols-slope-per-second"
    ):
        raise PilotError("drift diagnostic metric が事前登録済み規則と不一致")
    max_abs_position_correlation = _finite_probability(
        drift["max_abs_position_correlation"],
        "design.drift_diagnostics.max_abs_position_correlation",
    )
    max_abs_relative_time_slope = _positive_finite(
        drift["max_abs_relative_time_slope_per_second"],
        "design.drift_diagnostics.max_abs_relative_time_slope_per_second",
    )
    candidate_ns_raw = design["candidate_ns"]
    if not isinstance(candidate_ns_raw, list) or not candidate_ns_raw:
        raise PilotError("design.candidate_ns が空でない list でない")
    candidate_ns = tuple(_positive_int(item, "candidate_ns item") for item in candidate_ns_raw)
    if candidate_ns != tuple(sorted(set(candidate_ns))):
        raise PilotError("design.candidate_ns が昇順 unique でない")
    deltas_raw = design["deltas"]
    alphas_raw = design["alphas"]
    deltas = tuple(_finite_probability(item, "delta") for item in deltas_raw) \
        if isinstance(deltas_raw, list) else ()
    alphas = tuple(_finite_probability(item, "alpha") for item in alphas_raw) \
        if isinstance(alphas_raw, list) else ()
    if deltas != (0.005, 0.01, 0.02, 0.05) or alphas != (0.05, 0.1):
        raise PilotError("delta/alpha grid が裁定済み格子と不一致")
    declaration = _exact_mapping(
        top["measurement_declaration"], {"artifacts", "statement"},
        "measurement_declaration",
    )
    artifacts = declaration["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise PilotError("measurement_declaration.artifacts が空でない list でない")
    for index, artifact in enumerate(artifacts):
        checked = _exact_mapping(artifact, {"canonical_path", "sha256"}, f"artifact[{index}]")
        if type(checked["canonical_path"]) is not str or not checked["canonical_path"]:
            raise PilotError(f"artifact[{index}].canonical_path が空でない str でない")
        artifact_path = Path(str(checked["canonical_path"]))
        if (
            not artifact_path.is_absolute()
            or any(part in {"", ".", ".."} for part in artifact_path.parts[1:])
            or artifact_path.as_posix() != checked["canonical_path"]
        ):
            raise PilotError(f"artifact[{index}].canonical_path が canonical absolute path でない")
        if not _is_hex(checked["sha256"], 64):
            raise PilotError(f"artifact[{index}].sha256 が full lowercase sha256 でない")
    if type(declaration["statement"]) is not str or not declaration["statement"].strip():
        raise PilotError("measurement_declaration.statement が空でない str でない")
    allocation_count = _positive_int(design["allocation_count"], "allocation_count")
    if allocation_count != 3:
        raise PilotError("allocation_count は裁定済みの 3 でなければならない")
    if pilot_rounds is not None and (pilot_rounds < 32 or pilot_rounds % allocation_count != 0):
        raise PilotError("pilot_rounds は 32 以上かつ allocation_count で割り切れる必要がある")
    assert_holdout_safe_bytes(Path(path).name, canonical_result_bytes(top))
    return PilotProtocol(
        document=top,
        protocol_sha256=hashlib.sha256(canonical_result_bytes(top)).hexdigest(),
        freeze_path=str(freeze["path"]),
        freeze_sha256=str(freeze["sha256"]),
        source_commit=str(source["commit"]),
        driver_path=str(source["driver_path"]),
        driver_sha256=str(source["driver_sha256"]),
        job_script_path=str(source["job_script_path"]),
        job_script_sha256=str(source["job_script_sha256"]),
        ccbench_pin=str(environment["ccbench_pin"]),
        env_tag=str(environment["env_tag"]),
        contract_sha256=str(environment["contract_sha256"]),
        activation_generation=_positive_int(
            environment["activation_generation"], "activation_generation"
        ),
        pilot_rounds=pilot_rounds,
        master_seed=str(design["master_seed"]),
        allocation_count=allocation_count,
        allocation_role=str(design["allocation_role"]),
        stock_configuration=str(design["stock_configuration"]),
        candidate_ns=candidate_ns,
        resampling_seed=str(design["resampling_seed"]),
        resampling_iterations=_positive_int(
            design["resampling_iterations"], "resampling_iterations"
        ),
        ucl_confidence=_finite_probability(design["ucl_confidence"], "ucl_confidence"),
        deltas=deltas,
        alphas=alphas,
        max_abs_position_correlation=max_abs_position_correlation,
        max_abs_relative_time_slope_per_second=max_abs_relative_time_slope,
        measurement_declaration=dict(declaration),
    )


def _repo_relative_file(root: Path, raw: str, label: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise PilotError(f"{label} が canonical repo-relative path でない")
    target = root.joinpath(path)
    if target.is_symlink() or not target.is_file():
        raise PilotError(f"{label} が non-symlink regular file でない")
    if target.resolve() != root.resolve().joinpath(path):
        raise PilotError(f"{label} が symlink 経由である")
    return target


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PilotError(f"file hash を取得できない: {path}: {exc}") from exc
    return digest.hexdigest()


def _git_output(root: Path, args: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError as exc:
        raise PilotError(f"git を実行できない: {exc}") from exc
    if result.returncode != 0:
        raise PilotError(f"git {' '.join(args)} が失敗: {result.stderr[-300:]}")
    return result.stdout.strip()


def load_inputs(
    protocol: PilotProtocol,
    *,
    root: Path = ROOT,
    load_freeze_fn: Callable[..., object] = load_verified_freeze,
    verify_fn: Callable[..., object] = verify_document,
    contract_resolver: Callable[..., object] = env_contract.resolve_by_contract_sha256,
    active_contract_fn: Callable[[str], object] = env_contract.lookup,
    current_head_fn: Callable[[Path], str] | None = None,
    gitlink_fn: Callable[[Path], str] | None = None,
    submodule_head_fn: Callable[[Path], str] | None = None,
) -> PilotInputs:
    """Bind protocol, freeze, held verification status, environment, and pin."""
    root = Path(root).resolve()
    driver = _repo_relative_file(root, protocol.driver_path, "source.driver_path")
    job_script = _repo_relative_file(root, protocol.job_script_path, "source.job_script_path")
    if _sha256_file(driver) != protocol.driver_sha256:
        raise PilotError("driver sha256 が protocol と不一致")
    if _sha256_file(job_script) != protocol.job_script_sha256:
        raise PilotError("job script sha256 が protocol と不一致")
    current_head = (current_head_fn or (lambda base: _git_output(base, ["rev-parse", "HEAD"])))(root)
    if current_head != protocol.source_commit:
        raise PilotError("source commit が protocol と不一致")
    freeze_path = _repo_relative_file(root, protocol.freeze_path, "freeze.path")
    verified = load_freeze_fn(freeze_path, expected_hash=protocol.freeze_sha256)
    try:
        freeze = verified.document
        freeze_sha256 = verified.sha256
    except AttributeError as exc:
        raise PilotError("freeze loader が VerifiedFreeze shape を返さない") from exc
    held = verify_fn(freeze, root=root)
    if not isinstance(held, tuple) or any(not isinstance(item, Mapping) for item in held):
        raise PilotError("verify_document の held marker shape が不正")
    cells = s8b_floor_contract.enumerate_cells(
        freeze, stock_configuration=protocol.stock_configuration,
    )
    expected_configurations = set(_PREPARE_CELL_CONFIGURATIONS)
    if len(cells) != 12:
        raise PilotError(f"pilot cell 数が 12 でない: {len(cells)}")
    by_holdout: dict[str, set[str]] = {}
    for cell in cells:
        by_holdout.setdefault(str(cell["holdout_id"]), set()).add(
            str(cell["configuration_id"])
        )
        _positive_int(cell.get("records"), "cell.records")
        _positive_int(cell.get("threads"), "cell.threads")
    if len(by_holdout) != 2 or any(value != expected_configurations for value in by_holdout.values()):
        raise PilotError("pilot が 2 holdout × exact 6 configuration でない")
    gitlink = (gitlink_fn or (
        lambda base: _git_output(base, ["rev-parse", "HEAD:external/ccbench"])
    ))(root)
    submodule_head = (submodule_head_fn or (
        lambda base: _git_output(base / "external/ccbench", ["rev-parse", "HEAD"])
    ))(root)
    if gitlink != protocol.ccbench_pin or submodule_head != protocol.ccbench_pin:
        raise PilotError("gitlink/submodule HEAD が protocol ccbench pin と不一致")
    entry = contract_resolver(
        protocol.contract_sha256, expected_env_tag=protocol.env_tag,
    )
    contract = getattr(entry, "contract", None)
    generation = getattr(entry, "generation", None)
    active_contract = active_contract_fn(protocol.env_tag)
    if (
        contract is None
        or getattr(contract, "contract_sha256", None) != protocol.contract_sha256
        or getattr(contract, "env_tag", None) != protocol.env_tag
        or generation != protocol.activation_generation
        or getattr(active_contract, "contract_sha256", None) != protocol.contract_sha256
    ):
        raise PilotError("active environment contract/generation が protocol と不一致")
    return PilotInputs(
        protocol=protocol,
        freeze=freeze,
        freeze_sha256=freeze_sha256,
        cells=tuple(dict(cell) for cell in cells),
        held_markers=tuple(dict(item) for item in held),
        freeze_verification_status="held" if held else "verified",
        contract=contract,
    )


def _existing_symlink_component(path: Path) -> Path | None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            if current.is_symlink():
                return current
            if not current.exists():
                return None
        except OSError as exc:
            raise PilotError(f"path component を検査できない: {current}: {exc}") from exc
    return None


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def discover_git_worktrees(root: Path = ROOT) -> tuple[Path, ...]:
    output = _git_output(Path(root), ["worktree", "list", "--porcelain"])
    paths = []
    for line in output.splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line.removeprefix("worktree ")).resolve())
    if not paths:
        raise PilotError("git worktree list が空")
    return tuple(paths)


def assert_external_cache_root(
    cache_root: Path,
    *,
    repo_root: Path = ROOT,
    worktree_roots: Sequence[Path] | None = None,
) -> Path:
    """Reject repo/freeze/worktree containment and every symlink-mediated path."""
    requested = Path(os.fspath(cache_root))
    if not requested.is_absolute() or any(part in {"", ".", ".."} for part in requested.parts[1:]):
        raise PilotError("cache_root が canonical absolute path でない")
    raw = Path(os.path.abspath(os.fspath(requested)))
    symlink = _existing_symlink_component(raw)
    if symlink is not None:
        raise PilotError(f"cache_root が symlink 経由である: {symlink}")
    try:
        if not raw.exists() or not raw.is_dir():
            raise PilotError("cache_root は呼出し前に作成済みの directory でなければならない")
        canonical = raw.resolve(strict=True)
    except PilotError:
        raise
    except OSError as exc:
        raise PilotError(f"cache_root を canonicalize できない: {exc}") from exc
    repo = Path(repo_root).resolve()
    roots = tuple(Path(item).resolve() for item in (
        worktree_roots if worktree_roots is not None else discover_git_worktrees(repo)
    ))
    forbidden = (repo, repo / FREEZE_REL, *roots)
    if any(_is_within(canonical, parent) for parent in forbidden):
        raise PilotError("cache_root が repo/freeze/git worktree の外側でない")
    if canonical == Path(canonical.anchor):
        raise PilotError("cache_root に filesystem root は使えない")
    return canonical


def _directory_identity(path: Path, label: str) -> tuple[int, int]:
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise PilotError(f"{label} identity を取得できない: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise PilotError(f"{label} が directory でない")
    return metadata.st_dev, metadata.st_ino


def _assert_directory_identity(
    path: Path,
    expected: tuple[int, int],
    label: str,
) -> None:
    if _existing_symlink_component(path) is not None:
        raise PilotError(f"{label} が使用中に symlink 経由へ変化した")
    if _directory_identity(path, label) != expected:
        raise PilotError(f"{label} identity が使用中に変化した")


def _observe_toolchain(cc: str, cxx: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for role, requested in (("cc", cc), ("cxx", cxx), ("cmake", "cmake")):
        found = shutil.which(requested)
        if not found:
            raise PilotError(f"toolchain {role} が PATH にない")
        realpath = os.path.realpath(found)
        observed = subprocess.run(
            [realpath, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        lines = observed.stdout.splitlines()
        version = (observed.stdout + observed.stderr).strip()
        if observed.returncode != 0 or not lines or not version:
            raise PilotError(f"toolchain {role} version を観測できない")
        result[role] = {
            "requested": requested,
            "realpath": realpath,
            "version_first_line": lines[0],
            "version": version,
        }
    return result


def _prepare_sort_swo_oracle_environment(
    *,
    toolchain_manifest: Mapping[str, object],
    ccbench_pin: str,
    repo_root: Path,
    fetchcontent_base_fn: Callable[..., Path],
    dependency_fn: Callable[..., object],
) -> tuple[Path, str]:
    """Prebuild the pinned SWO dependency and bind it to the observed C++ compiler."""
    try:
        cxx_manifest = toolchain_manifest.get("cxx")
        if not isinstance(cxx_manifest, Mapping):
            raise ValueError("toolchain manifest に cxx がない")
        compiler = cxx_manifest.get("realpath")
        if type(compiler) is not str or not os.path.isabs(compiler):
            raise ValueError("cxx.realpath が絶対 path でない")
        fetchcontent_base = fetchcontent_base_fn(None, repo_root=repo_root)
        dependency = dependency_fn(
            fetchcontent_base,
            ccbench_pin=ccbench_pin,
            expected_toolchain_manifest=toolchain_manifest,
            repo_root=repo_root,
        )
        dependency_root = Path(getattr(dependency, "source_root"))
        if not dependency_root.is_absolute():
            raise ValueError("oracle dependency source_root が絶対 path でない")
    except Exception as exc:
        raise PilotError(f"sort_best SWO oracle preflight に失敗: {exc}") from exc
    return dependency_root, compiler


def build_binaries(
    inputs: PilotInputs,
    *,
    cache_root: Path,
    prepare_fn: Callable[..., object] = prepare_cell,
    build_fn: Callable[..., object] = buildcache.build_v2,
    repo_root: Path = ROOT,
    worktree_roots: Sequence[Path] | None = None,
    monotonic_fn: Callable[[], float] = time.monotonic,
    toolchain_fn: Callable[[str, str], Mapping[str, object]] = _observe_toolchain,
    compiler_fn: Callable[[], tuple[str, str]] = buildcache.compilers_for_current_site,
    oracle_fetchcontent_base_fn: Callable[..., Path] = _canonical_floor_fetchcontent_base,
    oracle_dependency_fn: Callable[..., object] = _prepare_floor_oracle_dependency,
    evidence_fn: Callable[..., object] = source_digest.resolve_evidence,
    review_fn: Callable[..., object] = reviewed_source_capability,
    admission_fn: Callable[..., object] = derive_build_admission,
    context_fn: Callable[..., object] = build_run_context,
) -> dict[str, PilotBinary]:
    """Build all 12 trace-disabled binaries after a side-effect-free containment gate."""
    canonical_cache = assert_external_cache_root(
        cache_root, repo_root=repo_root, worktree_roots=worktree_roots,
    )
    cache_identity = _directory_identity(canonical_cache, "cache_root")
    try:
        cc, cxx = compiler_fn()
        toolchain_manifest = toolchain_fn(cc, cxx)
    except Exception as exc:
        raise PilotError(f"build toolchain preflight に失敗: {exc}") from exc
    oracle_dependency_root = None
    oracle_compiler = None
    if any(cell.get("configuration_id") == "sort_best" for cell in inputs.cells):
        oracle_dependency_root, oracle_compiler = _prepare_sort_swo_oracle_environment(
            toolchain_manifest=toolchain_manifest,
            ccbench_pin=inputs.protocol.ccbench_pin,
            repo_root=Path(repo_root),
            fetchcontent_base_fn=oracle_fetchcontent_base_fn,
            dependency_fn=oracle_dependency_fn,
        )
    effective_prepare_fn = prepare_fn
    if oracle_dependency_root is not None:
        def pilot_prepare(
            prepared_cell,
            prepared_pin,
            *,
            cxx,
            _dependency_root=oracle_dependency_root,
            _compiler=oracle_compiler,
        ):
            return prepare_fn(
                prepared_cell,
                prepared_pin,
                cxx=cxx,
                oracle_dependency_root=_dependency_root,
                oracle_compiler=_compiler,
                oracle_phase_marker=None,
            )

        effective_prepare_fn = pilot_prepare
    build_context = context_fn(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    results: dict[str, PilotBinary] = {}
    seen_worktrees: set[str] = set()
    for cell in inputs.cells:
        cell_id = str(cell["cell_id"])
        started = monotonic_fn()
        with prepared_binding(
            freeze=inputs.freeze,
            holdout_id=str(cell["holdout_id"]),
            configuration_id=str(cell["configuration_id"]),
            ccbench_pin=inputs.protocol.ccbench_pin,
            cxx=cxx,
            prepare_fn=effective_prepare_fn,
        ) as (identity, prepared):
            elapsed = monotonic_fn() - started
            if not math.isfinite(elapsed) or elapsed < 0.0:
                raise PilotError("materialize elapsed が非負有限値でない")
            requested_worktree = Path(os.path.abspath(prepared.ccbench_dir))
            if _existing_symlink_component(requested_worktree) is not None:
                raise PilotError(f"cell worktree が symlink 経由である: {cell_id}")
            worktree = os.path.realpath(requested_worktree)
            if _is_within(Path(worktree), Path(repo_root).resolve()):
                raise PilotError(f"cell worktree が repo 外でない: {cell_id}")
            if worktree in seen_worktrees:
                raise PilotError(f"cell worktree が再利用された: {cell_id}")
            seen_worktrees.add(worktree)
            evidence = evidence_fn(
                prepared.genome,
                inputs.protocol.ccbench_pin,
                ccbench_dir=prepared.ccbench_dir,
                cxx=cxx,
            )
            review = review_fn(
                review_id=ReviewId.S8B_ORACLE,
                source=evidence,
                input_sha256=str(identity["entry_sha256"]),
            )
            admission = admission_fn(
                build_context, evidence, review_receipt=review,
            )
            _assert_directory_identity(canonical_cache, cache_identity, "cache_root")
            try:
                built = build_fn(
                    prepared.genome,
                    admission=admission,
                    build_context=build_context,
                    source_evidence=evidence,
                    contract=inputs.contract,
                    ccbench_commit=inputs.protocol.ccbench_pin,
                    trace=False,
                    cache_root=str(canonical_cache),
                    src_token=prepared.src_token,
                    cc=cc,
                    cxx=cxx,
                    ccbench_dir=prepared.ccbench_dir,
                    timeout_s=900,
                    expected_toolchain_manifest=toolchain_manifest,
                )
            finally:
                _assert_directory_identity(canonical_cache, cache_identity, "cache_root")
            if getattr(built, "trace", None) is not False:
                raise PilotError(f"trace-disabled build receipt でない: {cell_id}")
            if getattr(built, "contract_sha256", None) != getattr(
                inputs.contract, "contract_sha256", None
            ):
                raise PilotError(f"build contract sha256 が不一致: {cell_id}")
            binary_path = Path(getattr(built, "binary", ""))
            binary_sha = getattr(built, "bin_sha256", None)
            if not binary_path.is_absolute() or not _is_hex(binary_sha, 64):
                raise PilotError(f"build binary identity が不正: {cell_id}")
            if _sha256_file(binary_path) != binary_sha:
                raise PilotError(f"build 直後の binary sha256 が不一致: {cell_id}")
            results[cell_id] = PilotBinary(
                cell_id=cell_id,
                entry_sha256=str(identity["entry_sha256"]),
                binding_sha256=str(identity["binding_sha256"]),
                binary_sha256=str(binary_sha),
                binary_path=binary_path,
                cache_hit=bool(getattr(built, "cached", False)),
                materialize_elapsed_s=elapsed,
                worktree_identity_sha256=hashlib.sha256(worktree.encode("utf-8")).hexdigest(),
                isolated_worktree=True,
                pre_materialization_clean_assertion=prepare_fn is prepare_cell,
                source_tracked_clean=bool(evidence.tracked_clean),
                source_tracked_paths=tuple(evidence.tracked_paths),
            )
    if set(results) != {str(cell["cell_id"]) for cell in inputs.cells}:
        raise PilotError("全 cell の build receipt が揃わない")
    return results


def build_pilot_schedule(
    inputs: PilotInputs,
    *,
    master_seed: str,
    rounds: int,
) -> tuple[dict[str, object], ...]:
    """Use the oracle manifest complete-block scheduler, never the floor scheduler."""
    rounds = _positive_int(rounds, "rounds")
    holdout_ids = sorted({str(cell["holdout_id"]) for cell in inputs.cells})
    configuration_ids = sorted({str(cell["configuration_id"]) for cell in inputs.cells})
    schedule = s8b_oracle_manifest.build_schedule(
        n=rounds,
        master_seed=master_seed,
        block_sizes={"pilot": rounds},
        holdout_ids=holdout_ids,
        configuration_ids=configuration_ids,
    )
    rows = []
    for row in schedule["rows"]:
        rows.append({
            "seq": int(row["schedule_index"]),
            "pilot_round": int(row["replicate_index"]) + 1,
            "cell_id": f"{row['holdout_id']}::{row['configuration_id']}",
        })
    return tuple(rows)


def _load1() -> float:
    try:
        value = float(os.getloadavg()[0])
    except (AttributeError, OSError) as exc:
        raise PilotError(f"load1 を取得できない: {exc}") from exc
    if not math.isfinite(value) or value < 0.0:
        raise PilotError("load1 が非負有限値でない")
    return value


def _binary64_hex(value: float) -> str:
    return struct.pack("!d", value).hex()


def run_sessions(
    inputs: PilotInputs,
    binaries: Mapping[str, PilotBinary],
    schedule: Sequence[Mapping[str, object]],
    *,
    measure_fn: Callable[..., object] = measure_point,
    single_tenant_fn: Callable[[], None] = _assert_single_tenant,
    monotonic_fn: Callable[[], float] = time.monotonic,
    load1_fn: Callable[[], float] = _load1,
) -> tuple[SessionObservation, ...]:
    """Measure the complete blocked schedule with no retry or partial completion."""
    cells = {str(cell["cell_id"]): cell for cell in inputs.cells}
    if set(binaries) != set(cells):
        raise PilotError("binary cell 集合が input cell 集合と不一致")
    single_tenant_fn()
    observations = []
    width = len(cells)
    for expected_seq, row in enumerate(schedule):
        if set(row) != {"seq", "pilot_round", "cell_id"} or row["seq"] != expected_seq:
            raise PilotError("schedule row schema/seq が不正")
        cell_id = str(row["cell_id"])
        if cell_id not in cells:
            raise PilotError(f"schedule に未知 cell がある: {cell_id}")
        cell = cells[cell_id]
        binary = binaries[cell_id]
        single_tenant_fn()
        measured_sha = _sha256_file(binary.binary_path)
        if measured_sha != binary.binary_sha256:
            raise PilotError(f"測定直前 binary sha256 が不一致: {cell_id}")
        start = monotonic_fn()
        load_before = load1_fn()
        returncodes: list[int] = []
        point = None
        measure_error: BaseException | None = None
        try:
            point = measure_fn(
                str(binary.binary_path),
                int(cell["records"]),
                int(cell["threads"]),
                getattr(inputs.contract, "clocks_per_us"),
                extime=APPROVED_EXTIME_S,
                reps=APPROVED_REPS,
                workload=dict(cell["workload"]),
                numactl=tuple(getattr(inputs.contract, "numactl")),
                settle_first=False,
                require_all_reps=True,
                rep_returncodes=returncodes,
                use_perf=True,
            )
        except BaseException as exc:  # post-check is mandatory even for measurement failure
            measure_error = exc
        finally:
            single_tenant_fn()
        end = monotonic_fn()
        load_after = load1_fn()
        if measure_error is not None:
            raise PilotError(f"measurement failed for {cell_id}: {measure_error}") from measure_error
        raw = tuple(float(value) for value in getattr(point, "throughputs", ()))
        if len(raw) != APPROVED_REPS or any(
            not math.isfinite(value) or value <= 0.0 for value in raw
        ):
            raise PilotError(f"measurement raw reps が exact finite positive でない: {cell_id}")
        outer = getattr(point, "throughput", None)
        if outer != statistics.median(raw):
            raise PilotError(f"outer trial が statistics.median と不一致: {cell_id}")
        if len(returncodes) != APPROVED_REPS or any(type(value) is not int for value in returncodes):
            raise PilotError(f"rep return code が exact {APPROVED_REPS} 件でない: {cell_id}")
        duration = end - start
        if not math.isfinite(duration) or duration < 0.0:
            raise PilotError("session duration が非負有限値でない")
        observations.append(SessionObservation(
            seq=expected_seq,
            pilot_round=int(row["pilot_round"]),
            position=(expected_seq % width) + 1,
            cell_id=cell_id,
            monotonic_start_s=start,
            monotonic_end_s=end,
            duration_s=duration,
            load1_before=load_before,
            load1_after=load_after,
            throughputs=raw,
            throughput_binary64_hex=tuple(_binary64_hex(value) for value in raw),
            outer_median=float(outer),
            abort_rate=getattr(point, "abort_rate", None),
            returncodes=tuple(returncodes),
            binary_sha256_at_measure=measured_sha,
            cache_hit=binary.cache_hit,
            materialize_elapsed_s=binary.materialize_elapsed_s,
        ))
    return tuple(observations)


def _summary(values: Sequence[float]) -> dict[str, float | None]:
    mean = statistics.mean(values)
    median = statistics.median(values)
    sd = statistics.stdev(values) if len(values) >= 2 else None
    return {
        "mean": mean,
        "median": median,
        "sample_sd": sd,
        "cv": None if sd is None or mean == 0.0 else sd / mean,
    }


def _difference_summary(values: Sequence[float]) -> dict[str, float | None]:
    summary = _summary(values)
    mean = summary.pop("mean")
    summary.pop("cv")
    sd = summary["sample_sd"]
    return {
        "mean": mean,
        **summary,
        "dispersion_ratio": None if sd is None or mean == 0.0 else sd / abs(mean),
    }


def _sample_covariance(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / (len(xs) - 1)


def _sample_correlation(xs: Sequence[float], ys: Sequence[float]) -> tuple[float | None, str | None]:
    covariance = _sample_covariance(xs, ys)
    if covariance is None:
        return None, "fewer-than-two-rounds"
    sd_x, sd_y = statistics.stdev(xs), statistics.stdev(ys)
    if sd_x == 0.0 or sd_y == 0.0:
        return None, "zero-variance"
    return covariance / (sd_x * sd_y), None


def _ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        rank = (start + 1 + end) / 2.0
        for original_index, _value in indexed[start:end]:
            result[original_index] = rank
        start = end
    return result


def diagnose_drift(
    inputs: PilotInputs,
    observations: Sequence[SessionObservation],
) -> dict[str, object]:
    """Apply preregistered position and monotonic-time drift thresholds per cell."""
    rounds, by_cell = _observation_matrix(inputs, observations)
    cells: dict[str, object] = {}
    reasons: list[str] = []
    for cell_id in sorted(by_cell):
        rows = [by_cell[cell_id][round_no] for round_no in rounds]
        values = [row.outer_median for row in rows]
        positions = [float(row.position) for row in rows]
        times = [(row.monotonic_start_s + row.monotonic_end_s) / 2.0 for row in rows]
        position_correlation, position_reason = _sample_correlation(
            _ranks(positions), _ranks(values)
        )
        time_variance = _sample_covariance(times, times)
        time_covariance = _sample_covariance(times, values)
        population_median = statistics.median(values)
        if time_variance in {None, 0.0} or time_covariance is None:
            relative_time_slope = None
            time_reason = "fewer-than-two-distinct-monotonic-times"
        else:
            relative_time_slope = (time_covariance / time_variance) / abs(population_median)
            time_reason = None
        position_exceeded = (
            position_correlation is not None
            and abs(position_correlation) > inputs.protocol.max_abs_position_correlation
        )
        time_exceeded = (
            relative_time_slope is not None
            and abs(relative_time_slope)
            > inputs.protocol.max_abs_relative_time_slope_per_second
        )
        if position_reason is not None:
            reasons.append(f"{cell_id}:position:{position_reason}")
        if time_reason is not None:
            reasons.append(f"{cell_id}:time:{time_reason}")
        if position_exceeded:
            reasons.append(f"{cell_id}:position-threshold-exceeded")
        if time_exceeded:
            reasons.append(f"{cell_id}:time-threshold-exceeded")
        cells[cell_id] = {
            "position_rank_correlation": position_correlation,
            "position_null_reason": position_reason,
            "relative_time_slope_per_second": relative_time_slope,
            "time_slope_null_reason": time_reason,
            "position_threshold_exceeded": position_exceeded,
            "time_threshold_exceeded": time_exceeded,
        }
    return {
        "metrics": {
            "position": "spearman-rank-correlation",
            "time": "relative-ols-slope-per-second",
        },
        "thresholds": {
            "max_abs_position_correlation":
                inputs.protocol.max_abs_position_correlation,
            "max_abs_relative_time_slope_per_second":
                inputs.protocol.max_abs_relative_time_slope_per_second,
        },
        "valid_for_n_analysis": not reasons,
        "invalidation_reasons": reasons,
        "cells": cells,
    }


def _observation_matrix(
    inputs: PilotInputs,
    observations: Sequence[SessionObservation],
) -> tuple[list[int], dict[str, dict[int, SessionObservation]]]:
    expected_cells = {str(cell["cell_id"]) for cell in inputs.cells}
    by_cell: dict[str, dict[int, SessionObservation]] = {cell_id: {} for cell_id in expected_cells}
    for observation in observations:
        if observation.cell_id not in by_cell:
            raise PilotError(f"observation に未知 cell がある: {observation.cell_id}")
        if observation.pilot_round in by_cell[observation.cell_id]:
            raise PilotError("observation の cell/round が重複している")
        by_cell[observation.cell_id][observation.pilot_round] = observation
    round_sets = {tuple(sorted(rows)) for rows in by_cell.values()}
    if len(round_sets) != 1:
        raise PilotError("cell 間で round index が不一致")
    rounds = list(next(iter(round_sets), ()))
    if not rounds or rounds != list(range(1, len(rounds) + 1)):
        raise PilotError("pilot round が 1 始まり連続でない")
    if len(observations) != len(expected_cells) * len(rounds):
        raise PilotError("observation が完全 block でない")
    return rounds, by_cell


def summarize_sessions(
    inputs: PilotInputs,
    observations: Sequence[SessionObservation],
) -> dict[str, object]:
    """Preserve raw outer trials and separate candidates from stock diagnostics."""
    rounds, by_cell = _observation_matrix(inputs, observations)
    candidate_set: dict[str, dict[str, object]] = {}
    diagnostic: dict[str, dict[str, object]] = {}
    covariance: dict[str, object] = {}
    correlation: dict[str, object] = {}
    cells_by_holdout: dict[str, list[Mapping[str, object]]] = {}
    for cell in inputs.cells:
        cells_by_holdout.setdefault(str(cell["holdout_id"]), []).append(cell)
    for holdout_id, cells in sorted(cells_by_holdout.items()):
        candidate_set[holdout_id] = {}
        diagnostic[holdout_id] = {}
        values_by_configuration: dict[str, list[float]] = {}
        for cell in sorted(cells, key=lambda item: str(item["configuration_id"])):
            configuration = str(cell["configuration_id"])
            cell_id = str(cell["cell_id"])
            values = [by_cell[cell_id][round_no].outer_median for round_no in rounds]
            values_by_configuration[configuration] = values
            candidate_set[holdout_id][configuration] = {
                "raw_outer_trials": values,
                "raw_outer_trials_binary64_hex": [_binary64_hex(value) for value in values],
                "summary": _summary(values),
            }
        stock = values_by_configuration.get(inputs.protocol.stock_configuration)
        if stock is None or any(value <= 0.0 for value in stock):
            raise PilotError(f"holdout {holdout_id} の stock が欠損または非正")
        for configuration, values in sorted(values_by_configuration.items()):
            if configuration == inputs.protocol.stock_configuration:
                continue
            absolute = [value - base for value, base in zip(values, stock)]
            relative = [(value - base) / base for value, base in zip(values, stock)]
            corr, corr_reason = _sample_correlation(values, stock)
            diagnostic[holdout_id][configuration] = {
                "kind": "diagnostic-stock-contrast",
                "stock_configuration": inputs.protocol.stock_configuration,
                "absolute_difference": {
                    "raw": absolute, "summary": _difference_summary(absolute),
                },
                "relative_difference": {
                    "raw": relative, "summary": _difference_summary(relative),
                },
                "sample_covariance": _sample_covariance(values, stock),
                "pearson_correlation": corr,
                "correlation_null_reason": corr_reason,
            }
        configurations = sorted(values_by_configuration)
        covariance[holdout_id] = {
            left: {
                right: _sample_covariance(
                    values_by_configuration[left], values_by_configuration[right]
                )
                for right in configurations
            }
            for left in configurations
        }
        correlation[holdout_id] = {
            left: {
                right: _sample_correlation(
                    values_by_configuration[left], values_by_configuration[right]
                )[0]
                for right in configurations
            }
            for left in configurations
        }
    return {
        "candidate_set": candidate_set,
        "diagnostic_contrasts": diagnostic,
        "joint_covariance": covariance,
        "joint_correlation": correlation,
        "drift_diagnostics": diagnose_drift(inputs, observations),
    }


def _wilson_upper(errors: int, trials: int, confidence: float) -> float:
    if trials <= 0 or not 0 <= errors <= trials:
        raise PilotError("Wilson UCL input が不正")
    z = statistics.NormalDist().inv_cdf(confidence)
    p = errors / trials
    denominator = 1.0 + z * z / trials
    centre = p + z * z / (2.0 * trials)
    radius = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    upper = 1.0 if errors == trials else (centre + radius) / denominator
    return max(0.0, min(1.0, upper))


def _conservative_candidate_selection(
    candidate_ns: Sequence[int],
    passes: Sequence[bool],
) -> dict[str, object]:
    if len(candidate_ns) != len(passes) or not candidate_ns:
        raise PilotError("candidate pass/fail 列が不正")
    nonmonotonic = any(
        passed and any(not later for later in passes[index + 1:])
        for index, passed in enumerate(passes)
    )
    selected = next((
        candidate_ns[index]
        for index in range(len(candidate_ns))
        if all(passes[index:])
    ), None)
    if selected is None:
        reason = (
            "nonmonotonic-no-passing-suffix" if nonmonotonic
            else "no-passing-suffix"
        )
    else:
        reason = None
    return {
        "passes": [
            {"candidate_n": candidate_n, "passed": passed}
            for candidate_n, passed in zip(candidate_ns, passes)
        ],
        "nonmonotonic": nonmonotonic,
        "selected_n": selected,
        "null_reason": reason,
    }


def derive_n_table(
    inputs: PilotInputs,
    observations: Sequence[SessionObservation],
    *,
    rng_factory: Callable[[str], object] = random.Random,
) -> dict[str, object]:
    """Reproduce median/exact-argmax selection under round-block resampling."""
    rounds, by_cell = _observation_matrix(inputs, observations)
    if inputs.protocol.pilot_rounds is None or len(rounds) != inputs.protocol.pilot_rounds:
        raise PilotError("n analysis には aggregate 後の total pilot_rounds が必要")
    holdouts = sorted({str(cell["holdout_id"]) for cell in inputs.cells})
    configurations = sorted({str(cell["configuration_id"]) for cell in inputs.cells})
    cell_id = {
        (str(cell["holdout_id"]), str(cell["configuration_id"])): str(cell["cell_id"])
        for cell in inputs.cells
    }
    population = {
        holdout: {
            configuration: statistics.median([
                by_cell[cell_id[(holdout, configuration)]][round_no].outer_median
                for round_no in rounds
            ])
            for configuration in configurations
        }
        for holdout in holdouts
    }
    if any(best <= 0.0 for values in population.values() for best in values.values()):
        raise PilotError("n analysis population median が非正")
    candidates: dict[str, object] = {}
    for candidate_n in inputs.protocol.candidate_ns:
        errors = {delta: {holdout: 0 for holdout in holdouts} for delta in inputs.protocol.deltas}
        family_errors = {delta: 0 for delta in inputs.protocol.deltas}
        ties = {holdout: 0 for holdout in holdouts}
        for iteration in range(inputs.protocol.resampling_iterations):
            rng = rng_factory(
                f"{inputs.protocol.resampling_seed}/{candidate_n}/{iteration}"
            )
            sampled_rounds = [rng.choice(rounds) for _ in range(candidate_n)]
            iteration_errors = {delta: False for delta in inputs.protocol.deltas}
            for holdout in holdouts:
                estimates = {
                    configuration: statistics.median([
                        by_cell[cell_id[(holdout, configuration)]][round_no].outer_median
                        for round_no in sampled_rounds
                    ])
                    for configuration in configurations
                }
                maximum = max(estimates.values())
                winners = [key for key, value in estimates.items() if value == maximum]
                if len(winners) != 1:
                    ties[holdout] += 1
                    continue
                selected = winners[0]
                true_best = max(population[holdout].values())
                relative_loss = (true_best - population[holdout][selected]) / true_best
                for delta in inputs.protocol.deltas:
                    if relative_loss > delta:
                        errors[delta][holdout] += 1
                        iteration_errors[delta] = True
            for delta, is_error in iteration_errors.items():
                family_errors[delta] += int(is_error)
        total = inputs.protocol.resampling_iterations
        candidates[str(candidate_n)] = {
            "per_holdout": {
                str(delta): {
                    holdout: {
                        "errors": errors[delta][holdout],
                        "rate": errors[delta][holdout] / total,
                        "ucl": _wilson_upper(
                            errors[delta][holdout], total, inputs.protocol.ucl_confidence
                        ),
                        "tie_rate": ties[holdout] / total,
                    }
                    for holdout in holdouts
                }
                for delta in inputs.protocol.deltas
            },
            "familywise": {
                str(delta): {
                    "errors": family_errors[delta],
                    "rate": family_errors[delta] / total,
                    "ucl": _wilson_upper(
                        family_errors[delta], total, inputs.protocol.ucl_confidence
                    ),
                }
                for delta in inputs.protocol.deltas
            },
        }
    table = []
    for delta in inputs.protocol.deltas:
        for alpha in inputs.protocol.alphas:
            per_holdout_selection = {}
            for holdout in holdouts:
                passes = [
                    candidates[str(candidate_n)]["per_holdout"][str(delta)][holdout][
                        "ucl"
                    ] <= alpha
                    for candidate_n in inputs.protocol.candidate_ns
                ]
                per_holdout_selection[holdout] = _conservative_candidate_selection(
                    inputs.protocol.candidate_ns, passes,
                )
            familywise_selection = _conservative_candidate_selection(
                inputs.protocol.candidate_ns,
                [
                    candidates[str(candidate_n)]["familywise"][str(delta)]["ucl"]
                    <= alpha
                    for candidate_n in inputs.protocol.candidate_ns
                ],
            )
            table.append({
                "delta": delta,
                "alpha": alpha,
                "per_holdout_n": {
                    holdout: selection["selected_n"]
                    for holdout, selection in per_holdout_selection.items()
                },
                "per_holdout_pass": {
                    holdout: selection["passes"]
                    for holdout, selection in per_holdout_selection.items()
                },
                "per_holdout_nonmonotonic": {
                    holdout: selection["nonmonotonic"]
                    for holdout, selection in per_holdout_selection.items()
                },
                "per_holdout_null_reason": {
                    holdout: selection["null_reason"]
                    for holdout, selection in per_holdout_selection.items()
                },
                "familywise_n": familywise_selection["selected_n"],
                "familywise_pass": familywise_selection["passes"],
                "familywise_nonmonotonic": familywise_selection["nonmonotonic"],
                "familywise_null_reason": familywise_selection["null_reason"],
            })
    return {
        "status": "lower-bound",
        "conditioning": "all-rows-eligible/three-allocations/exact-pin-and-binaries",
        "allocation_variation_in_ucl": False,
        "selection_error": "indifference-zone-relative",
        "tie_rule": "not-an-error",
        "resampling_unit": "complete-round-vector",
        "estimator": "statistics.median-then-exact-float-argmax",
        "iterations": inputs.protocol.resampling_iterations,
        "ucl_method": "one-sided-wilson",
        "ucl_confidence": inputs.protocol.ucl_confidence,
        "population_medians": population,
        "candidate_results": candidates,
        "n_table": table,
    }


def canonical_result_bytes(document: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(
                document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PilotError(f"result を canonical JSON にできない: {exc}") from exc


def assert_holdout_safe_bytes(logical_name: str, payload: bytes) -> None:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise PilotError(f"{logical_name} が UTF-8 bytes でない") from exc
    hits = holdout_conjunction_hits({logical_name: text})
    contaminated = {key: value for key, value in hits.items() if value}
    if contaminated:
        raise PilotError(f"holdout conjunction contamination: {sorted(contaminated)}")


def _guarded_payload(value: Mapping[str, object] | str | bytes) -> bytes:
    if isinstance(value, Mapping):
        return canonical_result_bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, bytes):
        return value
    raise PilotError("guarded writer payload が Mapping/str/bytes でない")


def write_guarded_result(
    path: Path,
    document: Mapping[str, object] | str | bytes,
    *,
    root: Path = ROOT,
    open_fn: Callable[..., int] = os.open,
    write_fn: Callable[[int, bytes | memoryview], int] = os.write,
    fsync_fn: Callable[[int], None] = os.fsync,
    unlink_fn: Callable[..., None] = os.unlink,
) -> str:
    """The sole JSON/Markdown/spool writer: gate bytes before making any path."""
    destination = Path(os.path.abspath(os.fspath(path)))
    payload = _guarded_payload(document)
    assert_holdout_safe_bytes(destination.name, payload)
    if _existing_symlink_component(destination) is not None:
        raise PilotError("guarded writer destination が symlink 経由である")
    freeze_root = Path(root).resolve() / FREEZE_REL.parent
    if _is_within(destination.resolve(strict=False), freeze_root):
        raise PilotError("output/s8b-freeze 配下への書込みを拒否")
    directory_fd: int | None = None
    created = False
    try:
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if _existing_symlink_component(destination) is not None:
            raise PilotError("guarded writer parent が作成後に symlink 経由になった")
        directory_fd = open_fn(
            destination.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        if not stat.S_ISDIR(os.fstat(directory_fd).st_mode):
            raise PilotError("guarded writer parent fd が directory でない")
        file_fd = open_fn(
            destination.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory_fd,
        )
        created = True
        try:
            remaining = memoryview(payload)
            while remaining:
                written = write_fn(file_fd, remaining)
                if written <= 0:
                    raise OSError("guarded writer write made no progress")
                remaining = remaining[written:]
            fsync_fn(file_fd)
        finally:
            os.close(file_fd)
        fsync_fn(directory_fd)
    except BaseException as exc:
        cleanup_errors = []
        if created and directory_fd is not None:
            try:
                unlink_fn(destination.name, dir_fd=directory_fd)
            except BaseException as cleanup_exc:
                cleanup_errors.append(f"unlink={type(cleanup_exc).__name__}:{cleanup_exc}")
            try:
                fsync_fn(directory_fd)
            except BaseException as cleanup_exc:
                cleanup_errors.append(f"directory-fsync={type(cleanup_exc).__name__}:{cleanup_exc}")
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if cleanup_errors:
            raise PilotError(
                f"guarded write 失敗後の回収にも失敗: {destination}: "
                + "; ".join(cleanup_errors)
            ) from exc
        if isinstance(exc, PilotError):
            raise
        if isinstance(exc, FileExistsError):
            raise PilotError(
                f"guarded writer は create-only open で既存 destination を拒否: {destination}"
            ) from exc
        raise PilotError(f"guarded create-only write に失敗: {destination}: {exc}") from exc
    finally:
        if directory_fd is not None:
            os.close(directory_fd)
    return hashlib.sha256(payload).hexdigest()


def _load_strict_json_mapping(path: Path, label: str) -> tuple[Mapping[str, object], bytes]:
    try:
        raw = Path(path).read_bytes()
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_strict_object_pairs,
            parse_constant=_reject_constant,
        )
    except PilotError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"{label} を strict parse できない: {exc}") from exc
    if not isinstance(document, Mapping):
        raise PilotError(f"{label} が JSON object でない")
    return document, raw


def _record_float(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in {int, float}:
        raise PilotError(f"{label} が有限数でない")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        raise PilotError(f"{label} が期待範囲の有限数でない")
    return result


def _observation_from_record(record: object, label: str) -> SessionObservation:
    checked = _exact_mapping(record, {
        "seq", "pilot_round", "position", "cell_id", "monotonic_start_s",
        "monotonic_end_s", "duration_s", "load1_before", "load1_after",
        "throughputs", "throughput_binary64_hex", "outer_median", "abort_rate",
        "returncodes", "binary_sha256_at_measure", "cache_hit", "cache_state",
        "materialize_elapsed_s",
    }, label)
    throughputs_raw = checked["throughputs"]
    hex_raw = checked["throughput_binary64_hex"]
    returncodes_raw = checked["returncodes"]
    if (
        not isinstance(throughputs_raw, list)
        or not isinstance(hex_raw, list)
        or not isinstance(returncodes_raw, list)
        or len(throughputs_raw) != APPROVED_REPS
        or len(hex_raw) != APPROVED_REPS
        or len(returncodes_raw) != APPROVED_REPS
    ):
        raise PilotError(f"{label} の replicate vector shape が不正")
    throughputs = tuple(
        _record_float(value, f"{label}.throughputs", positive=True)
        for value in throughputs_raw
    )
    expected_hex = tuple(_binary64_hex(value) for value in throughputs)
    if tuple(hex_raw) != expected_hex:
        raise PilotError(f"{label} の binary64 hex が throughput と不一致")
    outer_median = _record_float(checked["outer_median"], f"{label}.outer_median", positive=True)
    if outer_median != statistics.median(throughputs):
        raise PilotError(f"{label} の outer median が replicate median と不一致")
    if type(checked["seq"]) is not int or checked["seq"] < 0:
        raise PilotError(f"{label}.seq が非負 int でない")
    pilot_round = _positive_int(checked["pilot_round"], f"{label}.pilot_round")
    position = _positive_int(checked["position"], f"{label}.position")
    if type(checked["cell_id"]) is not str or "::" not in checked["cell_id"]:
        raise PilotError(f"{label}.cell_id が不正")
    start = _record_float(checked["monotonic_start_s"], f"{label}.monotonic_start_s")
    end = _record_float(checked["monotonic_end_s"], f"{label}.monotonic_end_s")
    duration = _record_float(checked["duration_s"], f"{label}.duration_s")
    if end < start or duration < 0.0:
        raise PilotError(f"{label} の monotonic duration が不正")
    abort_rate_raw = checked["abort_rate"]
    abort_rate = None if abort_rate_raw is None else _record_float(
        abort_rate_raw, f"{label}.abort_rate"
    )
    if abort_rate is not None and not 0.0 <= abort_rate <= 1.0:
        raise PilotError(f"{label}.abort_rate が範囲外")
    if any(type(value) is not int for value in returncodes_raw):
        raise PilotError(f"{label}.returncodes が int vector でない")
    if not _is_hex(checked["binary_sha256_at_measure"], 64):
        raise PilotError(f"{label}.binary_sha256_at_measure が不正")
    if type(checked["cache_hit"]) is not bool:
        raise PilotError(f"{label}.cache_hit が bool でない")
    if checked["cache_state"] != ("hit" if checked["cache_hit"] else "miss"):
        raise PilotError(f"{label}.cache_state が cache_hit と不一致")
    return SessionObservation(
        seq=checked["seq"],
        pilot_round=pilot_round,
        position=position,
        cell_id=checked["cell_id"],
        monotonic_start_s=start,
        monotonic_end_s=end,
        duration_s=duration,
        load1_before=_record_float(checked["load1_before"], f"{label}.load1_before"),
        load1_after=_record_float(checked["load1_after"], f"{label}.load1_after"),
        throughputs=throughputs,
        throughput_binary64_hex=expected_hex,
        outer_median=outer_median,
        abort_rate=abort_rate,
        returncodes=tuple(returncodes_raw),
        binary_sha256_at_measure=checked["binary_sha256_at_measure"],
        cache_hit=checked["cache_hit"],
        materialize_elapsed_s=_record_float(
            checked["materialize_elapsed_s"], f"{label}.materialize_elapsed_s"
        ),
    )


def _aggregation_inputs(
    protocol: PilotProtocol,
    cell_ids: set[str],
) -> PilotInputs:
    cells = []
    by_holdout: dict[str, set[str]] = {}
    for cell_id in sorted(cell_ids):
        holdout, separator, configuration = cell_id.rpartition("::")
        if not separator or not holdout or not configuration:
            raise PilotError(f"aggregate cell_id が不正: {cell_id}")
        by_holdout.setdefault(holdout, set()).add(configuration)
        cells.append({
            "cell_id": cell_id,
            "holdout_id": holdout,
            "configuration_id": configuration,
        })
    expected = set(_PREPARE_CELL_CONFIGURATIONS)
    if len(by_holdout) != 2 or any(configurations != expected for configurations in by_holdout.values()):
        raise PilotError("aggregate が 2 holdout × exact 6 configuration でない")
    return PilotInputs(
        protocol=protocol,
        freeze={},
        freeze_sha256=protocol.freeze_sha256,
        cells=tuple(cells),
        held_markers=(),
        freeze_verification_status="aggregate-from-allocation-results",
        contract=None,
    )


def _allocation_shift(
    allocations: Sequence[tuple[str, Sequence[SessionObservation]]],
    cell_ids: set[str],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for cell_id in sorted(cell_ids):
        medians = {
            attempt_id: statistics.median([
                observation.outer_median
                for observation in observations
                if observation.cell_id == cell_id
            ])
            for attempt_id, observations in allocations
        }
        attempts = list(medians)
        differences = []
        for left_index, left in enumerate(attempts):
            for right in attempts[left_index + 1:]:
                difference = medians[right] - medians[left]
                differences.append({
                    "from": left,
                    "to": right,
                    "difference": difference,
                    "direction": "higher" if difference > 0.0 else (
                        "lower" if difference < 0.0 else "equal"
                    ),
                })
        result[cell_id] = {
            "allocation_medians": medians,
            "pairwise_differences": differences,
            "max_minus_min": max(medians.values()) - min(medians.values()),
        }
    return {
        "interpretation": "presence-and-direction-only;not-a-variance-component-estimate",
        "allocation_count": len(allocations),
        "cells": result,
    }


def aggregate_results(
    protocol: PilotProtocol,
    result_paths: Sequence[Path],
) -> dict[str, object]:
    """Aggregate exactly three same-protocol allocation results before deriving n."""
    if len(result_paths) != protocol.allocation_count:
        raise PilotError("aggregate result 数が protocol allocation_count と不一致")
    parsed = []
    canonical_schedule = None
    canonical_identity = None
    canonical_design = None
    canonical_binary_identity = None
    cell_ids: set[str] | None = None
    attempts: set[str] = set()
    rounds_per_allocation: int | None = None
    for index, path in enumerate(result_paths):
        document, raw = _load_strict_json_mapping(Path(path), f"aggregate result[{index}]")
        expected_fields = {
            "schema_version", "status", "eligibility", "input_identity", "design",
            "allocation", "measurement_declaration", "schedule", "binaries", "sessions",
            "statistics", "n_analysis", "n_analysis_null_reason", "redactions",
        }
        if set(document) != expected_fields or document["schema_version"] != RESULT_SCHEMA:
            raise PilotError(f"aggregate result[{index}] schema が不正")
        if document["status"] != "completed" or document["n_analysis"] is not None:
            raise PilotError(f"aggregate result[{index}] が解析前 completed result でない")
        if document["n_analysis_null_reason"] != "per-allocation-result-does-not-derive-n":
            raise PilotError(f"aggregate result[{index}] の per-allocation n null 理由が不正")
        identity = document["input_identity"]
        design = document["design"]
        allocation = document["allocation"]
        if not isinstance(identity, Mapping) or identity.get("protocol_sha256") != protocol.protocol_sha256:
            raise PilotError("aggregate results が同一 protocol でない")
        expected_identity = {
            "source_commit": protocol.source_commit,
            "driver_sha256": protocol.driver_sha256,
            "job_script_sha256": protocol.job_script_sha256,
            "freeze_path": protocol.freeze_path,
            "freeze_sha256": protocol.freeze_sha256,
            "ccbench_pin": protocol.ccbench_pin,
            "env_tag": protocol.env_tag,
            "contract_sha256": protocol.contract_sha256,
            "activation_generation": protocol.activation_generation,
        }
        if any(identity.get(key) != value for key, value in expected_identity.items()):
            raise PilotError("aggregate result identity が protocol と不一致")
        if canonical_identity is None:
            canonical_identity = dict(identity)
        elif identity != canonical_identity:
            raise PilotError("aggregate results の input identity が不一致")
        if not isinstance(design, Mapping) or design.get("master_seed") != protocol.master_seed:
            raise PilotError("aggregate results が同一 schedule seed でない")
        if design.get("allocation_count") != protocol.allocation_count:
            raise PilotError("aggregate result allocation_count が protocol と不一致")
        if canonical_design is None:
            canonical_design = dict(design)
        elif design != canonical_design:
            raise PilotError("aggregate results の design が不一致")
        if document["measurement_declaration"] != protocol.measurement_declaration:
            raise PilotError("aggregate result measurement declaration が protocol と不一致")
        binaries = document["binaries"]
        if not isinstance(binaries, list) or not binaries:
            raise PilotError("aggregate result binaries が空でない list でない")
        binary_identity = {
            str(binary.get("cell_id")): (
                binary.get("entry_sha256"),
                binary.get("binding_sha256"),
                binary.get("binary_sha256"),
            )
            for binary in binaries if isinstance(binary, Mapping)
        }
        if len(binary_identity) != len(binaries):
            raise PilotError("aggregate result binary identity が不正または重複")
        if canonical_binary_identity is None:
            canonical_binary_identity = binary_identity
        elif binary_identity != canonical_binary_identity:
            raise PilotError("aggregate results の binary identity が不一致")
        if not isinstance(allocation, Mapping) or type(allocation.get("attempt_id")) is not str:
            raise PilotError("aggregate result attempt identity が不正")
        attempt_id = allocation["attempt_id"]
        if not attempt_id or attempt_id in attempts:
            raise PilotError("aggregate result attempt identity が空または重複")
        attempts.add(attempt_id)
        schedule = document["schedule"]
        if not isinstance(schedule, list) or not schedule:
            raise PilotError("aggregate result schedule が空でない list でない")
        if canonical_schedule is None:
            canonical_schedule = schedule
        elif schedule != canonical_schedule:
            raise PilotError("aggregate results の schedule が同一 seed の出力と不一致")
        sessions_raw = document["sessions"]
        if not isinstance(sessions_raw, list) or not sessions_raw:
            raise PilotError("aggregate result sessions が空でない list でない")
        observations = tuple(
            _observation_from_record(record, f"result[{index}].sessions[{record_index}]")
            for record_index, record in enumerate(sessions_raw)
        )
        observed_cells = {observation.cell_id for observation in observations}
        if cell_ids is None:
            cell_ids = observed_cells
        elif observed_cells != cell_ids:
            raise PilotError("aggregate results の cell 集合が不一致")
        assert cell_ids is not None
        inputs = _aggregation_inputs(protocol, cell_ids)
        rounds, _by_cell = _observation_matrix(inputs, observations)
        expected_schedule = [
            dict(row) for row in build_pilot_schedule(
                inputs,
                master_seed=protocol.master_seed,
                rounds=len(rounds),
            )
        ]
        if schedule != expected_schedule:
            raise PilotError("aggregate result schedule が preregistered seed の出力でない")
        if len(observations) != len(schedule):
            raise PilotError("aggregate result sessions と schedule の長さが不一致")
        width = len(cell_ids)
        for expected_seq, (row, observation) in enumerate(zip(schedule, observations)):
            if (
                row.get("seq") != expected_seq
                or observation.seq != expected_seq
                or observation.pilot_round != row.get("pilot_round")
                or observation.cell_id != row.get("cell_id")
                or observation.position != (expected_seq % width) + 1
            ):
                raise PilotError("aggregate result session が schedule row と不一致")
        if rounds_per_allocation is None:
            rounds_per_allocation = len(rounds)
        elif len(rounds) != rounds_per_allocation:
            raise PilotError("aggregate results の allocation round 数が不一致")
        parsed.append((attempt_id, observations, hashlib.sha256(raw).hexdigest()))
    assert cell_ids is not None and rounds_per_allocation is not None
    if protocol.pilot_rounds is None or rounds_per_allocation * len(parsed) != protocol.pilot_rounds:
        raise PilotError("aggregate total round 数が protocol.pilot_rounds と不一致")
    parsed.sort(key=lambda item: item[0])
    combined = []
    for allocation_index, (_attempt, observations, _sha) in enumerate(parsed):
        round_offset = allocation_index * rounds_per_allocation
        for observation in observations:
            combined.append(replace(
                observation,
                seq=len(combined),
                pilot_round=round_offset + observation.pilot_round,
            ))
    aggregate_inputs = _aggregation_inputs(protocol, cell_ids)
    statistics_document = summarize_sessions(aggregate_inputs, combined)
    allocation_drifts = {
        attempt: diagnose_drift(aggregate_inputs, observations)
        for attempt, observations, _sha in parsed
    }
    drift_reasons = [
        f"{attempt}:{reason}"
        for attempt, diagnostics in allocation_drifts.items()
        for reason in diagnostics["invalidation_reasons"]
    ]
    drift = {
        "scope": "per-allocation-monotonic-clock",
        "thresholds": {
            "max_abs_position_correlation": protocol.max_abs_position_correlation,
            "max_abs_relative_time_slope_per_second":
                protocol.max_abs_relative_time_slope_per_second,
        },
        "valid_for_n_analysis": not drift_reasons,
        "invalidation_reasons": drift_reasons,
        "allocations": allocation_drifts,
    }
    statistics_document["drift_diagnostics"] = drift
    if drift["valid_for_n_analysis"]:
        n_analysis = derive_n_table(aggregate_inputs, combined)
        null_reason = None
    else:
        n_analysis = None
        null_reason = "drift-diagnostics-invalid:" + ";".join(
            drift["invalidation_reasons"]
        )
    return {
        "schema_version": AGGREGATE_SCHEMA,
        "status": "completed",
        "eligibility": {
            "certified": False,
            "floor_input": False,
            "oracle_input": False,
            "n_decision": False,
        },
        "input_identity": {
            "protocol_sha256": protocol.protocol_sha256,
            "source_commit": protocol.source_commit,
            "freeze_sha256": protocol.freeze_sha256,
            "ccbench_pin": protocol.ccbench_pin,
            "contract_sha256": protocol.contract_sha256,
        },
        "design": {
            "master_seed": protocol.master_seed,
            "allocation_count": protocol.allocation_count,
            "total_pilot_rounds": protocol.pilot_rounds,
            "allocation_variation_use": "presence-and-direction-only",
            "allocation_variation_in_ucl": False,
        },
        "source_results": [
            {"attempt_id": attempt, "sha256": sha}
            for attempt, _observations, sha in parsed
        ],
        "statistics": statistics_document,
        "allocation_shift": _allocation_shift(
            [(attempt, observations) for attempt, observations, _sha in parsed],
            cell_ids,
        ),
        "n_analysis": n_analysis,
        "n_analysis_null_reason": null_reason,
    }


def _result_document(
    inputs: PilotInputs,
    binaries: Mapping[str, PilotBinary],
    *,
    attempt_id: str,
    rounds: int | None,
    build_only: bool,
    schedule: Sequence[Mapping[str, object]],
    observations: Sequence[SessionObservation],
    statistics_document: Mapping[str, object] | None,
    n_analysis: Mapping[str, object] | None,
    run_wall_time_s: float | None,
    n_analysis_null_reason: str | None = None,
) -> dict[str, object]:
    if n_analysis is not None:
        raise PilotError("allocation result は n_analysis を持てない; aggregate を使う")
    if n_analysis_null_reason is None:
        n_analysis_null_reason = (
            "build-only-result" if build_only
            else "per-allocation-result-does-not-derive-n"
        )
    return {
        "schema_version": RESULT_SCHEMA,
        "status": "built" if build_only else "completed",
        "eligibility": {
            "certified": False,
            "floor_input": False,
            "oracle_input": False,
            "n_decision": False,
        },
        "input_identity": {
            "protocol_sha256": inputs.protocol.protocol_sha256,
            "source_commit": inputs.protocol.source_commit,
            "driver_sha256": inputs.protocol.driver_sha256,
            "job_script_sha256": inputs.protocol.job_script_sha256,
            "freeze_path": inputs.protocol.freeze_path,
            "freeze_sha256": inputs.freeze_sha256,
            "ccbench_pin": inputs.protocol.ccbench_pin,
            "env_tag": inputs.protocol.env_tag,
            "contract_sha256": inputs.protocol.contract_sha256,
            "activation_generation": inputs.protocol.activation_generation,
            "freeze_verification_status": inputs.freeze_verification_status,
            "freeze_verification_held_markers": list(inputs.held_markers),
        },
        "design": {
            "total_pilot_rounds": inputs.protocol.pilot_rounds,
            "rounds_this_allocation": rounds,
            "reps": APPROVED_REPS,
            "extime_s": APPROVED_EXTIME_S,
            "master_seed": inputs.protocol.master_seed,
            "schedule_algorithm": SCHEDULE_ALGORITHM,
            "counterbalance_analysis": "position-and-monotonic-drift-diagnostics-only",
            "drift_diagnostics": {
                "position_metric": "spearman-rank-correlation",
                "max_abs_position_correlation":
                    inputs.protocol.max_abs_position_correlation,
                "time_metric": "relative-ols-slope-per-second",
                "max_abs_relative_time_slope_per_second":
                    inputs.protocol.max_abs_relative_time_slope_per_second,
            },
            "stock_configuration": inputs.protocol.stock_configuration,
            "candidate_set": sorted(_PREPARE_CELL_CONFIGURATIONS),
            "diagnostic_contrasts": "configuration-minus-stock diagnostics only",
            "conditioning": "all-rows-eligible",
            "selection_error": "indifference-zone-relative",
            "tie_rule": "not-an-error",
            "allocation_count": inputs.protocol.allocation_count,
            "lower_bound": True,
            "failure_rule": "invalidate-entire-allocation",
            "missing_rule": "no-imputation",
            "retry_rule": "new-attempt-only",
        },
        "allocation": {
            "attempt_id": attempt_id,
            "role": inputs.protocol.allocation_role,
            "pbs_job_id": os.environ.get("PBS_JOBID"),
            "hostname": os.uname().nodename,
            "boot_id": _read_boot_id(),
            "run_wall_time_s": run_wall_time_s,
            "one_round_wall_time_s": run_wall_time_s if rounds == 1 else None,
        },
        "measurement_declaration": dict(inputs.protocol.measurement_declaration),
        "schedule": [dict(row) for row in schedule],
        "binaries": [binaries[key].public_record() for key in sorted(binaries)],
        "sessions": [observation.as_record() for observation in observations],
        "statistics": statistics_document,
        "n_analysis": n_analysis,
        "n_analysis_null_reason": n_analysis_null_reason,
        "redactions": {
            "run_cmd": "omitted",
            "workload": "omitted; reconstruct from freeze sha and cell id",
            "absolute_binary_path": "omitted",
        },
    }


def _read_boot_id() -> str | None:
    try:
        value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    except OSError:
        return None
    return value or None


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attempt-id")
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--aggregate", type=Path, nargs="+")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        protocol = load_protocol(args.protocol)
        if args.aggregate is not None:
            if (
                args.attempt_id is not None
                or args.cache_root is not None
                or args.build_only
                or args.rounds is not None
            ):
                raise PilotError(
                    "--aggregate は --attempt-id/--cache-root/--build-only/--rounds と併用できない"
                )
            write_guarded_result(args.output, aggregate_results(protocol, args.aggregate))
            return 0
        if args.attempt_id is None or args.cache_root is None:
            raise PilotError("allocation run には --attempt-id と --cache-root が必要")
        if type(args.attempt_id) is not str or not args.attempt_id or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for character in args.attempt_id
        ):
            raise PilotError("attempt-id が安全な identifier でない")
        if args.rounds is not None:
            rounds = _positive_int(args.rounds, "--rounds")
            registered_allocation_rounds = (
                None if protocol.pilot_rounds is None
                else protocol.pilot_rounds // protocol.allocation_count
            )
            if registered_allocation_rounds is not None and rounds not in {
                1, registered_allocation_rounds,
            }:
                raise PilotError(
                    "--rounds は生死実験の 1 または protocol の allocation rounds と一致が必要"
                )
        else:
            rounds = (
                None if protocol.pilot_rounds is None
                else protocol.pilot_rounds // protocol.allocation_count
            )
        if not args.build_only and rounds is None:
            raise PilotError("実走には protocol.pilot_rounds または --rounds が必要")
        inputs = load_inputs(protocol)
        binaries = build_binaries(inputs, cache_root=args.cache_root)
        schedule: tuple[Mapping[str, object], ...] = ()
        observations: tuple[SessionObservation, ...] = ()
        statistics_document = None
        n_analysis = None
        n_analysis_null_reason = "build-only-result" if args.build_only else None
        run_wall_time = None
        if not args.build_only:
            assert rounds is not None
            schedule = build_pilot_schedule(
                inputs, master_seed=protocol.master_seed, rounds=rounds,
            )
            run_start = time.monotonic()
            observations = run_sessions(inputs, binaries, schedule)
            run_wall_time = time.monotonic() - run_start
            statistics_document = summarize_sessions(inputs, observations)
            n_analysis_null_reason = "per-allocation-result-does-not-derive-n"
        result = _result_document(
            inputs,
            binaries,
            attempt_id=args.attempt_id,
            rounds=rounds,
            build_only=args.build_only,
            schedule=schedule,
            observations=observations,
            statistics_document=statistics_document,
            n_analysis=n_analysis,
            run_wall_time_s=run_wall_time,
            n_analysis_null_reason=n_analysis_null_reason,
        )
        write_guarded_result(args.output, result)
        return 0
    except PilotError as exc:
        print(f"oracle n pilot refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
