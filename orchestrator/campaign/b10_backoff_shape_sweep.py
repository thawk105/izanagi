# -*- coding: utf-8 -*-
"""B-10: equal-target-mean backoff-shape campaign.

The fixed template is human-owned.  This driver does not route it through the
literal-only coder grammar and does not widen that grammar or source allowlist.
Before creating campaign state it binds a committed preregistration blob, the
template patch, and the exact one-line expression, then validates the applied
tree and the inert stock references.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import platform
import re
import shutil
import socket
import statistics
import struct
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator import benchparse
from ..calibrator.runner import (  # noqa: E402
    competing_bench_pids,
    run_once,
    settle,
)
from ..calibrator.stability import noise_floor  # noqa: E402
from . import (  # noqa: E402
    buildcache,
    campaign_lock,
    env_contract,
    ident,
    p2_2,
    pin,
    pipeline,
    source_digest,
    wal,
)
from .build_admission import (  # noqa: E402
    BuildRunContext,
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from .layout import CampaignLayout, campaign_layout  # noqa: E402
from .lock import bench_lock  # noqa: E402
from .loop import run_campaign  # noqa: E402
from .model import (  # noqa: E402
    CampaignConfig,
    Genome,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
)
from .pipeline import (  # noqa: E402
    SEARCH_CONFIG_VERIFY_KEY,
    VERIFY_LEGACY_PLUS_PERFORMANCE,
    PerfConfig,
    variant_id,
)


PIN = pin.CURRENT_PIN
SPACE_VERSION = "b10-backoff-shape/v2"
TRIAL = "b10-backoff-shape-v2"
ENV_TAG = "pegasus"
PATCH_REL = "patches/silo-backoff-fixed.patch"
ANALYSIS_REL = "orchestrator/campaign/b10_backoff_shape_sweep.py"
SOURCE_REL = "include/backoff.hh"
OPTIONS_REL = "cmake/Options.cmake"
PREREG_REL = "docs/b10-backoff-shape-preregistration.md"
MARKER_ID = "silo-backoff-magnitude"
EXPECTED_PATCH_PATHS = frozenset({OPTIONS_REL, SOURCE_REL})
MEANS_US = (2, 5, 10, 25, 50, 100)
SHAPES = (("constant", 0), ("symmetric-modulo", 1))
SHAPE_CODES = {name: code for name, code in SHAPES}
SHAPE_NAMES = {code: name for name, code in SHAPES}
POINTS_PER_BLOCK = 3 + len(MEANS_US) * len(SHAPES)
BLOCK_IDS = ("block-1", "block-2", "block-3")
THREADS = 48
EXTIME = 3
REPS = 5
RUN_PHASES = ("build", "verify", "perf", "probe")
PROBE_CALLS_PER_CELL = 100_000
PROBE_SCHEMA = "izanagi-b10-backoff-shape-probe/v2"
MIXER = 0x9E3779B97F4A7C15
_MASK64 = (1 << 64) - 1
_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}

WORKLOADS = {
    "write-heavy": {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "balanced": {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "read-heavy": {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
}

# This is the exact physical source line after applying PATCH_REL, including
# indentation.  Its SHA-256 is part of the preregistration binding.
EXPECTED_HOLE_LINE = "    double now_backoff = (static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 0ULL) ? static_cast<double>(BACKOFF_FIXED) : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 1ULL) ? static_cast<double>((static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + (((start * 0x9e3779b97f4a7c15ULL) >> 63) ? (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) - ((((start * 0x9e3779b97f4a7c15ULL) << 1) >> 1) % (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + 1ULL))) : ((((start * 0x9e3779b97f4a7c15ULL) << 1) >> 1) % (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + 1ULL)))) / 2.0 : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 2ULL) ? static_cast<double>((static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + (((start * 0x9e3779b97f4a7c15ULL) >> 63) * (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL)))) / 2.0 : static_cast<double>(static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL)));"
FORMULA_SHA256 = hashlib.sha256(EXPECTED_HOLE_LINE.encode("utf-8")).hexdigest()
EXPECTED_WAIT_LOOP = """    for (;;) {
      _mm_pause();
      stop = rdtscp();
      if (chkClkSpan(start, stop,
                     static_cast<uint64_t>(static_cast<double>(clocks_per_us) *
                                           now_backoff)))
        break;
    }"""
EXPECTED_CHK_CLK_SPAN = """[[maybe_unused]] inline static bool chkClkSpan(const uint64_t start,
                                               const uint64_t stop,
                                               const uint64_t threshold) {
  uint64_t diff = 0;
  diff = stop - start;
  if (diff > threshold)
    return true;
  else
    return false;
}"""

# Full applied Options.cmake and applied backoff.hh-with-hole-replaced hashes.
# They pin every byte outside the one authorized source line.  Values are
# filled from the reviewed patch below and independently exercised by tests.
EXPECTED_OPTIONS_SHA256 = "abaf00fa96db1de6db20e8c6314f8b32328820c3a35f1be576b48a16d06a06fa"
EXPECTED_BACKOFF_FRAME_SHA256 = "761b75102b65f407b326efe011bb4bc38064e1fa393383eff7266b0844e8212e"
_FRAME_SENTINEL = b"<IZANAGI-B10-AUTHORIZED-HOLE>"
B10_BUILD_START_BINDING_KEY = "b10_preregistration_binding"
_WAL_BINDING_LOCK = threading.Lock()
_SPEC_BEGIN = "<!-- IZANAGI-B10-SPEC-BEGIN -->"
_SPEC_END = "<!-- IZANAGI-B10-SPEC-END -->"
_SPEC_SCHEMA = "izanagi-b10-backoff-shape-preregistration/v4"
_SPEC_BLOCK_RE = re.compile(
    re.escape(_SPEC_BEGIN)
    + r"[ \t]*\r?\n```json[ \t]*\r?\n(.*?)\r?\n```[ \t]*\r?\n"
    + re.escape(_SPEC_END),
    re.DOTALL,
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_DIFF_HEADER_RE = re.compile(rb"(?m)^diff --git a/([^\r\n]+) b/([^\r\n]+)\r?$")


class PreflightError(RuntimeError):
    """Fail-closed B10 admission error with a mutation-addressable code."""

    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code


@dataclass(frozen=True)
class PreregistrationBinding:
    prereg_commit: str
    prereg_blob_sha: str
    spec_sha256: str
    patch_sha256: str
    formula_sha256: str
    analysis_commit: str
    analysis_code_sha256: str

    def __post_init__(self) -> None:
        for name in ("prereg_commit", "analysis_commit"):
            if _COMMIT_RE.fullmatch(getattr(self, name) or "") is None:
                raise ValueError(f"{name} must be a full lowercase commit ID")
        if re.fullmatch(r"[0-9a-f]{40,64}", self.prereg_blob_sha or "") is None:
            raise ValueError("prereg_blob_sha must be a Git object ID")
        for name in (
            "spec_sha256", "patch_sha256", "formula_sha256", "analysis_code_sha256",
        ):
            if _SHA256_RE.fullmatch(getattr(self, name) or "") is None:
                raise ValueError(f"{name} must be a full lowercase SHA-256")

    def core(self) -> dict[str, str]:
        return {
            "prereg_commit": self.prereg_commit,
            "prereg_blob_sha": self.prereg_blob_sha,
            "spec_sha256": self.spec_sha256,
            "patch_sha256": self.patch_sha256,
            "formula_sha256": self.formula_sha256,
            "analysis_commit": self.analysis_commit,
            "analysis_code_sha256": self.analysis_code_sha256,
        }

    @property
    def binding_sha256(self) -> str:
        return _sha256_json(self.core())

    def as_dict(self) -> dict[str, str]:
        return {**self.core(), "binding_sha256": self.binding_sha256}


@dataclass(frozen=True)
class PreregistrationSpec:
    """Deeply immutable interpretation of the canonical machine spec."""

    canonical_json: str
    spec_sha256: str
    patch_sha256: str
    formula_sha256: str
    registration_rules: tuple[tuple[str, str], ...]
    means_us: tuple[int, ...]
    shapes: tuple[tuple[str, int, str], ...]
    references: tuple[tuple[str, int, int], ...]
    block_ids: tuple[str, ...]
    block_orders: tuple[tuple[str, tuple[str, ...]], ...]
    workloads: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]
    threads: int
    extime_s: int
    performance_reps: int
    correctness_reps: int
    correctness_mode: str
    alpha: float
    holm_families: tuple[tuple[str, str], ...]
    permutation_method: str
    permutation_sided: str
    permutation_statistic: str
    permutation_enumeration: str
    pairs_per_family: int
    ci_method: str
    ci_confidence_level: float
    ci_degrees_of_freedom: int
    ci_critical_value: float
    missing_conditions: tuple[str, ...]
    missing_pair_action: str
    missing_family_action: str
    indeterminate_pvalue: float
    exposure_metric: str
    minimum_abort_calls: int
    exposure_below_minimum_action: str
    equivalence_margin_pct: float
    decision_procedure: tuple[str, ...]
    physical_residual_measurement: str
    maximum_absolute_deviation_pct_exclusive: float
    physical_residual_provenance: tuple[tuple[str, str | int], ...]
    physical_residual_values: tuple[tuple[str, int, float, float, float], ...]
    reference_width_terminology: str
    reference_width_power_guarantee: bool
    reference_widths: tuple[tuple[str, float, float, str], ...]

    def as_dict(self) -> dict[str, object]:
        return json.loads(self.canonical_json)

    @property
    def shape_codes(self) -> dict[str, int]:
        return {name: code for name, code, _support in self.shapes}

    @property
    def workload_map(self) -> dict[str, dict[str, str]]:
        return {name: dict(flags) for name, flags in self.workloads}

    @property
    def block_order_map(self) -> dict[str, tuple[str, ...]]:
        return dict(self.block_orders)


@dataclass(frozen=True)
class Preregistration:
    binding: PreregistrationBinding
    path: str
    spec: PreregistrationSpec

    def __post_init__(self) -> None:
        if self.path != PREREG_REL:
            raise ValueError("preregistration path must be canonical")
        if self.binding.spec_sha256 != self.spec.spec_sha256 \
                or self.binding.patch_sha256 != self.spec.patch_sha256 \
                or self.binding.formula_sha256 != self.spec.formula_sha256:
            raise ValueError("preregistration binding/spec mismatch")

    @property
    def minimum_abort_calls(self) -> int:
        return self.spec.minimum_abort_calls

    @property
    def maximum_absolute_deviation_pct_exclusive(self) -> float:
        return self.spec.maximum_absolute_deviation_pct_exclusive

    @property
    def equivalence_margin_pct(self) -> float:
        return self.spec.equivalence_margin_pct


@dataclass(frozen=True)
class CertificationAttempt:
    attempt_id: str
    perf_bin_sha256: str


@dataclass(frozen=True)
class SubmissionIdentity:
    receipt_path: str
    receipt_sha256: str
    request_id: str
    nonce: str
    source_commit: str
    prereg_commit: str
    job_script_sha256: str
    phase: str
    workload: Optional[str]

    @property
    def trial(self) -> str:
        request = re.sub(r"[^A-Za-z0-9._-]", "-", self.request_id)
        return f"{request}-{self.nonce[:12]}"


@dataclass(frozen=True)
class CalibrationSelection:
    path: str
    sha256: str
    schema_version: str
    records: int
    threads: int
    env_tag: str
    clocks_per_us: int
    saturated: bool
    lower_bound_selected: bool
    cache_floor_warning: bool

    def as_dict(self) -> dict[str, object]:
        return dict(vars(self))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    )


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _git(root: Path, *args: str, binary: bool = False) -> bytes | str:
    env = source_digest._sanitized_git_env()
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(root), *args], capture_output=True,
            text=not binary, env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreflightError("git", f"git {' '.join(args)} を起動できない: {exc}") from exc
    if result.returncode != 0:
        stderr = result.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise PreflightError(
            "git", f"git {' '.join(args)} が失敗した: {(stderr or '').strip()[-300:]}",
        )
    return result.stdout


def _canonical_submission_root(root: Path) -> Path:
    common_raw = str(
        _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    ).strip()
    common = Path(common_raw)
    if not common.is_absolute():
        raise PreflightError("submission-receipt", "git common dir が絶対 path でない")
    durable = common.parent.parent / "izanagi-job-evidence" \
        / "b10-backoff-shape" / "submissions"
    try:
        durable_resolved = durable.resolve(strict=True)
        root_resolved = root.resolve(strict=True)
        common_repo = common.parent.resolve(strict=True)
    except OSError as exc:
        raise PreflightError("submission-receipt", "durable submission root を解決できない") from exc
    for repository in (root_resolved, common_repo):
        try:
            durable_resolved.relative_to(repository)
        except ValueError:
            pass
        else:
            raise PreflightError("submission-receipt", "durable root が repository 内にある")
    return durable_resolved


def load_submission_identity(
    repo_root: str | os.PathLike[str],
    receipt_path: str | os.PathLike[str],
    *,
    prereg_commit: str,
    phase: str,
    workload: Optional[str],
) -> SubmissionIdentity:
    root = Path(repo_root).resolve()
    path = Path(receipt_path)
    try:
        path = path.resolve(strict=True)
        durable_root = _canonical_submission_root(root)
        relative = path.relative_to(durable_root)
    except (OSError, ValueError) as exc:
        raise PreflightError(
            "submission-receipt", "submission receipt が canonical durable root 外にある",
        ) from exc
    if path.is_symlink() or not path.is_file() or len(relative.parts) != 2 \
            or relative.parts[1] != "submit-receipt.json" \
            or re.fullmatch(r"[0-9a-f]{32}", relative.parts[0]) is None:
        raise PreflightError("submission-receipt", "submission receipt path shape が不正")
    try:
        raw = path.read_bytes()
        document = _strict_json(raw.decode("utf-8"), label="submission receipt")
    except (OSError, UnicodeError) as exc:
        raise PreflightError("submission-receipt", "submission receipt を読めない") from exc
    document = _exact_object(
        document,
        {
            "schema_version", "source_commit", "prereg_commit", "nonce",
            "request_id", "dry_run", "submitted_epoch", "job_script_path",
            "job_script_sha256", "phase", "workload", "request",
        },
        "submission receipt",
    )
    if document["schema_version"] != "pegasus-b10-submit-receipt/v2" \
            or document["dry_run"] is not False:
        raise PreflightError("submission-receipt", "real v2 submission receipt が必要")
    source_commit = document["source_commit"]
    nonce = document["nonce"]
    request_id = document["request_id"]
    job_script_sha = document["job_script_sha256"]
    if type(source_commit) is not str or _COMMIT_RE.fullmatch(source_commit) is None \
            or source_commit != str(_git(root, "rev-parse", "--verify", "HEAD^{commit}")).strip():
        raise PreflightError("submission-receipt", "receipt source commit が current HEAD と不一致")
    if document["prereg_commit"] != prereg_commit:
        raise PreflightError("submission-receipt", "receipt prereg commit が不一致")
    if type(nonce) is not str or re.fullmatch(r"[0-9a-f]{32}", nonce) is None \
            or nonce != relative.parts[0]:
        raise PreflightError("submission-receipt", "receipt nonce が path と不一致")
    if type(request_id) is not str or not request_id \
            or re.fullmatch(r"[A-Za-z0-9:._-]+", request_id) is None:
        raise PreflightError("submission-receipt", "receipt request ID が不正")
    if document["job_script_path"] != "tools/pegasus/b10_backoff_shape_campaign.sh" \
            or type(job_script_sha) is not str or _SHA256_RE.fullmatch(job_script_sha) is None:
        raise PreflightError("submission-receipt", "receipt job script binding が不正")
    if document["phase"] != phase or document["workload"] != workload:
        raise PreflightError("submission-receipt", "receipt phase/workload が CLI と不一致")
    if type(document["submitted_epoch"]) is not int or document["submitted_epoch"] <= 0:
        raise PreflightError("submission-receipt", "receipt submitted_epoch が不正")
    request = _exact_object(
        document["request"], {"project", "queue", "nodes", "elapstim_req_s"},
        "submission receipt request",
    )
    if request != {
        "project": "SFC", "queue": "gen_S", "nodes": 1, "elapstim_req_s": 21600,
    }:
        raise PreflightError("submission-receipt", "receipt request が B10 PBS contract と不一致")
    return SubmissionIdentity(
        receipt_path=os.fspath(path),
        receipt_sha256=_sha256_bytes(raw),
        request_id=request_id,
        nonce=nonce,
        source_commit=source_commit,
        prereg_commit=prereg_commit,
        job_script_sha256=job_script_sha,
        phase=phase,
        workload=workload,
    )


def encode(shape: str, mean_us: int) -> int:
    if type(shape) is not str or shape not in SHAPE_CODES:
        raise ValueError(f"grid 外 shape: {shape!r}")
    if type(mean_us) is not int or isinstance(mean_us, bool) or mean_us not in MEANS_US:
        raise ValueError(f"grid 外 mean: {mean_us!r}")
    return SHAPE_CODES[shape] * 1000 + mean_us


def decode(encoded: int) -> tuple[str, int]:
    if type(encoded) is not int or isinstance(encoded, bool) or encoded < 0:
        raise ValueError(f"grid 外 encoding: {encoded!r}")
    code, mean_us = divmod(encoded, 1000)
    if code not in SHAPE_NAMES or mean_us not in MEANS_US:
        raise ValueError(f"grid 外 encoding: {encoded!r}")
    return SHAPE_NAMES[code], mean_us


def reference_genomes() -> tuple[tuple[str, Genome], ...]:
    return (
        ("none", Genome("silo", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1})),
        ("adaptive", Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})),
        ("zero-loop", Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 0})),
    )


def factorial_genomes() -> tuple[tuple[str, Genome], ...]:
    return tuple(
        (
            f"{shape}-mu{mean_us}",
            Genome(
                "silo",
                {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": encode(shape, mean_us)},
            ),
        )
        for mean_us in MEANS_US
        for shape, _code in SHAPES
    )


def named_genomes() -> tuple[tuple[str, Genome], ...]:
    points = reference_genomes() + factorial_genomes()
    if len(points) != POINTS_PER_BLOCK \
            or len({genome.canonical() for _name, genome in points}) != POINTS_PER_BLOCK:
        raise AssertionError(
            f"B10 genome grid must contain exactly {POINTS_PER_BLOCK} unique points",
        )
    return points


def genomes() -> tuple[Genome, ...]:
    return tuple(genome for _name, genome in named_genomes())


def block_run_order(block_id: str) -> tuple[str, ...]:
    try:
        block_index = BLOCK_IDS.index(block_id)
    except ValueError as exc:
        raise ValueError(f"未知 block: {block_id!r}") from exc
    references = [name for name, _genome in reference_genomes()]
    references = references[block_index:] + references[:block_index]
    order = list(references)
    shape_names = [name for name, _code in SHAPES]
    for mean_index, mean_us in enumerate(MEANS_US):
        offset = (block_index + mean_index) % len(shape_names)
        rotated = shape_names[offset:] + shape_names[:offset]
        order.extend(f"{shape}-mu{mean_us}" for shape in rotated)
    if len(order) != POINTS_PER_BLOCK \
            or set(order) != {name for name, _genome in named_genomes()}:
        raise AssertionError(
            f"B10 block order must be a permutation of all {POINTS_PER_BLOCK} points",
        )
    return tuple(order)


def exact_model(encoded: int, start: int):
    """Exact Fraction model for the one-line expression."""
    from fractions import Fraction

    if type(encoded) is not int or encoded < 0:
        raise ValueError("encoded must be a non-negative exact integer")
    if type(start) is not int or start < 0 or start > _MASK64:
        raise ValueError("start must be a uint64")
    code, mean_us = divmod(encoded, 1000)
    if code == 0:
        return Fraction(encoded)
    if code >= 3:
        return Fraction(mean_us)
    mixed = (start * MIXER) & _MASK64
    high = mixed >> 63
    if code == 2:
        return Fraction(mean_us + high * 2 * mean_us, 2)
    low = mixed & ((1 << 63) - 1)
    residue = low % (2 * mean_us + 1)
    offset = 2 * mean_us - residue if high else residue
    return Fraction(mean_us + offset, 2)


def validate_formula_contract(line: str = EXPECTED_HOLE_LINE) -> None:
    if type(line) is not str or "\n" in line or "\r" in line:
        raise PreflightError("hole", "hole は単一 physical line でなければならない")
    if not line.startswith("    double now_backoff = ") or not line.endswith(";"):
        raise PreflightError("hole", "hole は exact one-declarator statement でない")
    if line.count("double now_backoff =") != 1:
        raise PreflightError("hole", "hole の宣言子が一意でない")
    constants = {
        int(value, 16)
        for value in re.findall(r"0x([0-9a-fA-F]+)ULL", line)
    }
    if constants != {MIXER}:
        raise PreflightError("mixer", "両乱数形は同じ単一 mixer を使わなければならない")
    forbidden = ("#include", "#define", "#if", "#else", "#endif", " signed ")
    if any(token in line for token in forbidden):
        raise PreflightError("hole", "hole に禁止された定義/条件指令/符号付き演算指定がある")


def parse_patch_paths(patch_bytes: bytes) -> frozenset[str]:
    if type(patch_bytes) is not bytes or not patch_bytes:
        raise PreflightError("patch-paths", "patch bytes が空または bytes でない")
    paths: list[str] = []
    for left_raw, right_raw in _DIFF_HEADER_RE.findall(patch_bytes):
        try:
            left = left_raw.decode("utf-8")
            right = right_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PreflightError("patch-paths", "patch path が UTF-8 でない") from exc
        if left != right or not left or left.startswith("/") or ".." in Path(left).parts:
            raise PreflightError("patch-paths", "patch の左右 path が安全な同一相対 path でない")
        paths.append(left)
    if len(paths) != 2 or len(set(paths)) != 2:
        raise PreflightError("patch-paths", "patch は正確に 2 file の diff でなければならない")
    result = frozenset(paths)
    if result != EXPECTED_PATCH_PATHS:
        raise PreflightError(
            "patch-paths",
            f"patch 変更先が閉集合と不一致: {sorted(result)!r}",
        )
    return result


def validate_patch_bytes(patch_bytes: bytes, expected_sha256: str) -> str:
    parse_patch_paths(patch_bytes)
    observed = _sha256_bytes(patch_bytes)
    if not _SHA256_RE.fullmatch(expected_sha256 or "") or observed != expected_sha256:
        raise PreflightError(
            "patch-sha", f"patch SHA 不一致: expected={expected_sha256!r} observed={observed}",
        )
    expected_patch_hole = b"+" + EXPECTED_HOLE_LINE.encode("utf-8")
    hole_lines = [
        line for line in patch_bytes.splitlines()
        if line.startswith(b"+    double now_backoff =")
    ]
    if hole_lines != [expected_patch_hole]:
        raise PreflightError("hole", "patch の authorized hole line が byte 一致しない")
    validate_formula_contract()
    return observed


def _frame_sha256(source_bytes: bytes, *, expected_line: bytes | None = None) -> str:
    expected = EXPECTED_HOLE_LINE.encode("utf-8") if expected_line is None else expected_line
    lines = source_bytes.splitlines(keepends=True)
    candidates = []
    for index, line in enumerate(lines):
        payload = line[:-1] if line.endswith(b"\n") else line
        if payload.endswith(b"\r"):
            payload = payload[:-1]
        if payload == expected:
            candidates.append(index)
    if len(candidates) != 1:
        raise PreflightError("hole", "applied source の exact hole line が 1 行でない")
    index = candidates[0]
    newline = b"\n" if lines[index].endswith(b"\n") else b""
    lines[index] = _FRAME_SENTINEL + newline
    return _sha256_bytes(b"".join(lines))


def _inert_reference_genomes() -> tuple[Genome, ...]:
    return tuple(
        genome for _name, genome in reference_genomes()
        if genome.flags["BACKOFF_FIXED"] == -1
    )


def validate_applied_tree(
    sub: str | os.PathLike[str],
    *,
    patch_bytes: bytes,
    patch_sha256: str,
    ccbench_commit: str = PIN,
    cxx: str = buildcache.DEFAULT_CXX,
    expected_options_sha256: str = EXPECTED_OPTIONS_SHA256,
    expected_frame_sha256: str = EXPECTED_BACKOFF_FRAME_SHA256,
    digest_compute: Callable[..., str] = source_digest.compute,
    digest_baseline: Callable[..., str] = source_digest.baseline,
    token_resolver: Callable[..., str] = source_digest.src_token,
    applied_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    """Validate the exact applied tree; patch absence is always an error."""
    root = Path(sub)
    source_path = root / SOURCE_REL
    options_path = root / OPTIONS_REL
    try:
        source_bytes = source_path.read_bytes()
        options_bytes = options_path.read_bytes()
    except OSError as exc:
        raise PreflightError("patch-unapplied", f"applied tree を読めない: {exc}") from exc
    begin = f"EVOLVE-BLOCK-BEGIN {MARKER_ID}".encode("ascii")
    end = f"EVOLVE-BLOCK-END {MARKER_ID}".encode("ascii")
    if source_bytes.count(begin) == 0 and source_bytes.count(end) == 0:
        raise PreflightError("patch-unapplied", "template patch が適用されていない")
    if source_bytes.count(begin) != 1 or source_bytes.count(end) != 1:
        raise PreflightError("markers", "BEGIN/END marker は各 1 個でなければならない")
    if source_bytes.count(b"EVOLVE-BLOCK-BEGIN") != 1 \
            or source_bytes.count(b"EVOLVE-BLOCK-END") != 1:
        raise PreflightError("markers", "重複または別 ID marker を検出した")
    expected_line = EXPECTED_HOLE_LINE.encode("utf-8")
    physical = [line.rstrip(b"\r") for line in source_bytes.splitlines()]
    if physical.count(expected_line) != 1:
        raise PreflightError("hole", "applied hole が単一行で EXPECTED_HOLE_LINE と byte 不一致")
    i_begin = source_bytes.index(begin)
    i_if = source_bytes.find(b"#if BACKOFF_FIXED >= 0", i_begin)
    i_hole = source_bytes.find(expected_line, i_if)
    i_else = source_bytes.find(b"#else", i_hole)
    i_stock = source_bytes.find(
        b"double now_backoff = Backoff_.load(std::memory_order_acquire);", i_else,
    )
    i_endif = source_bytes.find(b"#endif", i_stock)
    i_end = source_bytes.find(end, i_endif)
    if min(i_if, i_hole, i_else, i_stock, i_endif, i_end) < 0 \
            or not (i_begin < i_if < i_hole < i_else < i_stock < i_endif < i_end):
        raise PreflightError("frame", "stock 枝または EVOLVE-BLOCK 骨格の順序が不正")
    options_sha = _sha256_bytes(options_bytes)
    frame_sha = _frame_sha256(source_bytes)
    if options_sha != expected_options_sha256 or frame_sha != expected_frame_sha256:
        raise PreflightError(
            "frame", "Options/stock 枝/待機 loop/骨格が reviewed bytes と一致しない",
        )
    validate_patch_bytes(patch_bytes, patch_sha256)
    observed_paths = (
        source_digest._tracked_status_paths(os.fspath(root))
        if applied_paths is None else tuple(sorted(set(applied_paths)))
    )
    if frozenset(observed_paths) != EXPECTED_PATCH_PATHS:
        raise PreflightError(
            "applied-tree", "事前登録 patch の変更先と適用後 tracked tree が不一致",
        )
    inert = []
    for genome in _inert_reference_genomes():
        current = digest_compute(genome, os.fspath(root), cxx)
        baseline = digest_baseline(genome, ccbench_commit, os.fspath(root), cxx)
        token = token_resolver(genome, ccbench_commit, os.fspath(root), cxx)
        if current != baseline:
            raise PreflightError("inert-digest", "BACKOFF_FIXED=-1 reference が baseline と不一致")
        if token != source_digest.STOCK:
            raise PreflightError("inert-token", "BACKOFF_FIXED=-1 reference の src_token が stock でない")
        inert.append({"genome": genome.canonical(), "digest": current, "src_token": token})
    return {
        "patch_sha256": patch_sha256,
        "applied_tree_sha256": _sha256_json({
            OPTIONS_REL: options_sha,
            SOURCE_REL: _sha256_bytes(source_bytes),
        }),
        "options_sha256": options_sha,
        "frame_sha256": frame_sha,
        "inert_references": inert,
    }


def _strict_json(raw: str, *, label: str) -> object:
    def no_duplicates(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_constant(token):
        raise ValueError(f"non-finite JSON constant: {token}")

    try:
        return json.loads(
            raw, object_pairs_hook=no_duplicates, parse_constant=reject_constant,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise PreflightError("prereg-spec", f"{label} が strict JSON でない: {exc}") from exc


def _exact_object(value: object, keys: set[str], label: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        observed = sorted(value) if type(value) is dict else type(value).__name__
        raise PreflightError(
            "prereg-spec", f"{label} key set 不一致: {observed!r}",
        )
    return value


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise PreflightError("prereg-spec", f"{label} は正の exact integer が必要")
    return value


def _finite_number(value: object, label: str) -> float:
    if type(value) not in {int, float} or not math.isfinite(float(value)):
        raise PreflightError("prereg-spec", f"{label} は有限実数が必要")
    return float(value)


def parse_preregistration(raw: bytes) -> PreregistrationSpec:
    """Parse every registered decision field from one canonical JSON block."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError("prereg-blob", "事前登録文書が UTF-8 でない") from exc
    matches = _SPEC_BLOCK_RE.findall(text)
    if len(matches) != 1:
        raise PreflightError("prereg-spec", "canonical machine spec block が正確に 1 個でない")
    document = _exact_object(
        _strict_json(matches[0], label="machine spec"),
        {
            "schema_version", "artifacts", "registration_rules", "grid",
            "blocks", "workloads", "execution", "analysis",
            "physical_residual", "external_floor_reference_widths",
        },
        "machine spec",
    )
    if document["schema_version"] != _SPEC_SCHEMA:
        raise PreflightError("prereg-spec", "machine spec schema_version 不一致")

    artifacts = _exact_object(
        document["artifacts"], {"patch_sha256", "formula_sha256"}, "artifacts",
    )
    patch_sha = artifacts["patch_sha256"]
    formula_sha = artifacts["formula_sha256"]
    if type(patch_sha) is not str or _SHA256_RE.fullmatch(patch_sha) is None:
        raise PreflightError("prereg-spec", "artifacts.patch_sha256 が不正")
    if type(formula_sha) is not str or _SHA256_RE.fullmatch(formula_sha) is None:
        raise PreflightError("prereg-spec", "artifacts.formula_sha256 が不正")

    registration_rules = _exact_object(
        document["registration_rules"],
        {
            "shape_eligibility_criterion", "shape_eligibility_evidence",
            "shape_exclusion_granularity", "means_us_and_cell_partition",
            "physical_residual_cell_policy", "throughput_decision_procedure",
            "a2_material_role", "shape_rule_formulation_timing",
        },
        "registration_rules",
    )
    expected_registration_rules = {
        "shape_eligibility_criterion": (
            "symbolic-mean-deviation-has-no-unsuppressed-mu-coefficient-"
            "on-mixer-high-bit-frequency"
        ),
        "shape_eligibility_evidence": "formula-only-not-observed-deviation",
        "shape_exclusion_granularity": "whole-shape-only",
        "means_us_and_cell_partition": "unchanged",
        "physical_residual_cell_policy": (
            "evaluate-all-registered-cells-without-exemption"
        ),
        "throughput_decision_procedure": "unchanged-and-independent-of-a2",
        "a2_material_role": (
            "motivation-and-prior-evidence-not-parameter-selection"
        ),
        "shape_rule_formulation_timing": (
            "after-physical-residual-probe-before-shape-grid-throughput"
        ),
    }
    if registration_rules != expected_registration_rules:
        raise PreflightError("prereg-spec", "registration_rules が v4 閉集合と不一致")

    grid = _exact_object(
        document["grid"], {"means_us", "shapes", "encoding", "references"}, "grid",
    )
    means_raw = grid["means_us"]
    if type(means_raw) is not list or tuple(means_raw) != MEANS_US:
        raise PreflightError("prereg-spec", "grid.means_us が裁定済み μ grid と不一致")
    if grid["encoding"] != "BACKOFF_FIXED=shape_code*1000+mu":
        raise PreflightError("prereg-spec", "grid.encoding が裁定済み符号化と不一致")
    shape_rows = grid["shapes"]
    expected_supports = {
        "constant": "mu",
        "symmetric-modulo": "closed-half-width-mu/2-through-3mu/2",
    }
    if type(shape_rows) is not list or len(shape_rows) != len(SHAPES):
        raise PreflightError("prereg-spec", "grid.shapes 件数不一致")
    shapes = []
    for index, value in enumerate(shape_rows):
        row = _exact_object(value, {"name", "code", "support"}, f"grid.shapes[{index}]")
        name, code = SHAPES[index]
        if row != {"name": name, "code": code, "support": expected_supports[name]}:
            raise PreflightError("prereg-spec", f"grid.shapes[{index}] が閉集合と不一致")
        shapes.append((name, code, expected_supports[name]))
    reference_rows = grid["references"]
    expected_references = (
        ("none", 0, -1), ("adaptive", 1, -1), ("zero-loop", 1, 0),
    )
    if type(reference_rows) is not list or len(reference_rows) != 3:
        raise PreflightError("prereg-spec", "grid.references 件数不一致")
    references = []
    for index, value in enumerate(reference_rows):
        row = _exact_object(
            value, {"name", "back_off", "backoff_fixed"},
            f"grid.references[{index}]",
        )
        expected = expected_references[index]
        observed = (row["name"], row["back_off"], row["backoff_fixed"])
        if observed != expected:
            raise PreflightError("prereg-spec", f"grid.references[{index}] が不一致")
        references.append(expected)

    blocks = _exact_object(document["blocks"], {"count", "ids", "run_order"}, "blocks")
    if blocks["count"] != 3 or type(blocks["ids"]) is not list \
            or tuple(blocks["ids"]) != BLOCK_IDS:
        raise PreflightError("prereg-spec", "blocks count/ids が裁定済み値と不一致")
    run_order = _exact_object(blocks["run_order"], set(BLOCK_IDS), "blocks.run_order")
    block_orders = []
    for block_id in BLOCK_IDS:
        order = run_order[block_id]
        expected = block_run_order(block_id)
        if type(order) is not list or tuple(order) != expected:
            raise PreflightError("prereg-spec", f"blocks.run_order.{block_id} が不一致")
        block_orders.append((block_id, expected))

    workload_rows = document["workloads"]
    if type(workload_rows) is not list or len(workload_rows) != len(WORKLOADS):
        raise PreflightError("prereg-spec", "workloads 件数不一致")
    workloads = []
    workload_keys = {"name", "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw", "ycsb_max_ope"}
    for index, (expected_name, expected_flags) in enumerate(WORKLOADS.items()):
        row = _exact_object(workload_rows[index], workload_keys, f"workloads[{index}]")
        if row.get("name") != expected_name or {
            key: row.get(key) for key in expected_flags
        } != expected_flags:
            raise PreflightError("prereg-spec", f"workloads[{index}] が裁定済み動作点と不一致")
        workloads.append((expected_name, tuple(expected_flags.items())))

    execution = _exact_object(
        document["execution"],
        {
            "threads", "extime_s", "performance_reps", "correctness_reps",
            "correctness_mode", "screening",
        },
        "execution",
    )
    expected_execution = {
        "threads": THREADS, "extime_s": EXTIME, "performance_reps": REPS,
        "correctness_reps": 5, "correctness_mode": VERIFY_LEGACY_PLUS_PERFORMANCE,
        "screening": False,
    }
    if execution != expected_execution:
        raise PreflightError("prereg-spec", "execution が裁定済み動作点と不一致")

    analysis = _exact_object(
        document["analysis"],
        {
            "alpha", "holm_families", "permutation", "confidence_interval",
            "missingness", "exposure", "equivalence_margin_pct",
            "decision_procedure",
        },
        "analysis",
    )
    alpha = _finite_number(analysis["alpha"], "analysis.alpha")
    if alpha != 0.05:
        raise PreflightError("prereg-spec", "analysis.alpha は 0.05 が必要")
    family_rows = analysis["holm_families"]
    expected_families = tuple(
        (workload, shape)
        for workload in WORKLOADS
        for shape in ("symmetric-modulo",)
    )
    if type(family_rows) is not list or len(family_rows) != len(expected_families):
        raise PreflightError("prereg-spec", "analysis.holm_families 件数不一致")
    families = []
    for index, expected in enumerate(expected_families):
        row = _exact_object(
            family_rows[index], {"workload", "shape"},
            f"analysis.holm_families[{index}]",
        )
        observed = (row["workload"], row["shape"])
        if observed != expected:
            raise PreflightError("prereg-spec", "Holm family の順序/閉集合が不一致")
        families.append(expected)
    permutation = _exact_object(
        analysis["permutation"],
        {"method", "sided", "statistic", "enumeration", "pairs_per_family"},
        "analysis.permutation",
    )
    expected_permutation = {
        "method": "exact-sign-flip", "sided": "two-sided",
        "statistic": "absolute-sum-paired-relative-effect",
        "enumeration": "all-2^18", "pairs_per_family": 18,
    }
    if permutation != expected_permutation:
        raise PreflightError("prereg-spec", "permutation 手続きが裁定済み値と不一致")
    confidence = _exact_object(
        analysis["confidence_interval"],
        {"method", "confidence_level", "degrees_of_freedom", "critical_value"},
        "analysis.confidence_interval",
    )
    if confidence.get("method") != "student-t-paired-block-mean" \
            or _finite_number(confidence.get("confidence_level"), "confidence level") != 0.95 \
            or confidence.get("degrees_of_freedom") != 2 \
            or not math.isclose(
                _finite_number(confidence.get("critical_value"), "critical value"),
                4.302652729911275, rel_tol=0.0, abs_tol=1e-15,
            ):
        raise PreflightError("prereg-spec", "confidence interval 手続きが不一致")
    missingness = _exact_object(
        analysis["missingness"],
        {"conditions", "pair_action", "family_action", "indeterminate_pvalue"},
        "analysis.missingness",
    )
    expected_missing = (
        "missing", "performance-error", "correctness-not-certified",
        "unstable", "underexposed",
    )
    if type(missingness["conditions"]) is not list \
            or tuple(missingness["conditions"]) != expected_missing \
            or missingness["pair_action"] != "invalidate-entire-family" \
            or missingness["family_action"] != "indeterminate" \
            or _finite_number(missingness["indeterminate_pvalue"], "indeterminate p") != 1.0:
        raise PreflightError("prereg-spec", "missingness 規則が裁定済み値と不一致")
    exposure = _exact_object(
        analysis["exposure"], {"metric", "minimum_calls_per_cell", "below_minimum_action"},
        "analysis.exposure",
    )
    minimum_calls = _positive_int(exposure["minimum_calls_per_cell"], "minimum calls")
    if exposure["metric"] != "sum-performance-rep-abort-counts" \
            or exposure["below_minimum_action"] != "indeterminate":
        raise PreflightError("prereg-spec", "exposure 規則が不一致")
    equivalence = _finite_number(analysis["equivalence_margin_pct"], "equivalence margin")
    if not 0 < equivalence < 100:
        raise PreflightError("prereg-spec", "equivalence margin は (0,100) が必要")
    expected_decision = (
        "construct-all-18-within-block-paired-relative-effects",
        "mark-family-indeterminate-on-any-unusable-pair",
        "enumerate-two-sided-sign-flip-pvalue-for-each-testable-family",
        "set-indeterminate-family-pvalue-to-1",
        "holm-adjust-all-three-families",
        "different-iff-testable-and-holm-p-less-than-or-equal-alpha",
        "otherwise-not-detected",
        "report-all-cell-effects-confidence-intervals-and-equivalence-relations",
    )
    if type(analysis["decision_procedure"]) is not list \
            or tuple(analysis["decision_procedure"]) != expected_decision:
        raise PreflightError("prereg-spec", "decision procedure が不一致")

    residual = _exact_object(
        document["physical_residual"],
        {
            "measurement", "maximum_absolute_deviation_pct_exclusive",
            "provenance", "values",
        },
        "physical_residual",
    )
    residual_measurement = "realized-backoff-loop-cycles"
    if residual["measurement"] != residual_measurement:
        raise PreflightError("prereg-spec", "physical residual measurement が不一致")
    maximum_absolute_deviation = _finite_number(
        residual["maximum_absolute_deviation_pct_exclusive"],
        "maximum absolute deviation",
    )
    if maximum_absolute_deviation != 1.0:
        raise PreflightError(
            "prereg-spec", "physical residual 上限は exact 1.0 が必要",
        )
    residual_provenance = _exact_object(
        residual["provenance"],
        {
            "probe_schema_version", "probe_result_sha256",
            "probe_source_commit", "placeholder_preregistration_commit",
            "probe_request_id", "probe_nonce", "submission_receipt_sha256",
            "probe_host", "probe_measured_at_utc", "probe_clocks_per_us",
            "probe_calls_per_cell", "probe_cells_total", "extraction_rule",
        },
        "physical_residual.provenance",
    )
    expected_residual_provenance = {
        "probe_schema_version": "izanagi-b10-backoff-shape-probe/v1",
        "probe_result_sha256": (
            "6e7d8ed7d27be091ce94de4b85ac61a50e99d97167e75c4328e8a54982224bc3"
        ),
        "probe_source_commit": "8df4fa25da01311e887336b6f454f6d33ec28a2c",
        "placeholder_preregistration_commit": (
            "1549bd92794d72e05aeafe5903568f7d9023614d"
        ),
        "probe_request_id": "953543.nqsv",
        "probe_nonce": "6f8cea40fcf2193f4e4157e9c89adde1",
        "submission_receipt_sha256": (
            "782b25fc0aecf78d0aa9dfa36ef2d036c777eb171b3ebe654405b7364dc7eb54"
        ),
        "probe_host": "bnode142",
        "probe_measured_at_utc": "2026-08-27T16:26:55.628726Z",
        "probe_clocks_per_us": 2100,
        "probe_calls_per_cell": 100000,
        "probe_cells_total": 18,
        "extraction_rule": (
            "select-probe-rows-whose-shape-is-in-the-registered-grid"
        ),
    }
    if residual_provenance["probe_schema_version"] \
            != "izanagi-b10-backoff-shape-probe/v1" \
            or residual_provenance["extraction_rule"] \
            != "select-probe-rows-whose-shape-is-in-the-registered-grid":
        raise PreflightError("prereg-spec", "physical residual provenance 規則が不一致")
    for key in ("probe_result_sha256", "submission_receipt_sha256"):
        value = residual_provenance[key]
        if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            raise PreflightError("prereg-spec", f"physical residual {key} が不正")
    for key in ("probe_source_commit", "placeholder_preregistration_commit"):
        value = residual_provenance[key]
        if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
            raise PreflightError("prereg-spec", f"physical residual {key} が不正")
    if type(residual_provenance["probe_request_id"]) is not str \
            or re.fullmatch(
                r"[A-Za-z0-9:._-]+", residual_provenance["probe_request_id"],
            ) is None \
            or type(residual_provenance["probe_nonce"]) is not str \
            or re.fullmatch(r"[0-9a-f]{32}", residual_provenance["probe_nonce"]) is None \
            or type(residual_provenance["probe_host"]) is not str \
            or not residual_provenance["probe_host"]:
        raise PreflightError("prereg-spec", "physical residual probe identity が不正")
    measured_at = residual_provenance["probe_measured_at_utc"]
    if type(measured_at) is not str:
        raise PreflightError("prereg-spec", "physical residual probe timestamp が不正")
    try:
        measured_timestamp = dt.datetime.fromisoformat(measured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PreflightError(
            "prereg-spec", "physical residual probe timestamp が ISO-8601 でない",
        ) from exc
    if measured_timestamp.tzinfo is None \
            or measured_timestamp.utcoffset() != dt.timedelta(0):
        raise PreflightError("prereg-spec", "physical residual probe timestamp が UTC でない")
    _positive_int(residual_provenance["probe_clocks_per_us"], "probe clocks_per_us")
    _positive_int(residual_provenance["probe_calls_per_cell"], "probe calls_per_cell")
    if _positive_int(residual_provenance["probe_cells_total"], "probe cells total") != 18:
        raise PreflightError("prereg-spec", "転記元 probe は exact 18 cell が必要")
    if residual_provenance != expected_residual_provenance:
        raise PreflightError(
            "prereg-spec", "physical residual provenance が v4 正本値と不一致",
        )
    residual_rows = residual["values"]
    expected_residual_cells = tuple(
        (shape, mean_us)
        for mean_us in MEANS_US
        for shape, _code in SHAPES
    )
    if type(residual_rows) is not list \
            or len(residual_rows) != len(expected_residual_cells):
        raise PreflightError("prereg-spec", "physical residual 実測表の件数が不一致")
    residual_values = []
    for index, (shape, mean_us) in enumerate(expected_residual_cells):
        row = _exact_object(
            residual_rows[index],
            {
                "shape", "mean_us", "realized_mean_cycles",
                "commanded_mean_cycles", "deviation_pct",
            },
            f"physical_residual.values[{index}]",
        )
        if row["shape"] != shape or row["mean_us"] != mean_us:
            raise PreflightError(
                "prereg-spec", "physical residual 実測表の順序/閉集合が不一致",
            )
        realized = _finite_number(
            row["realized_mean_cycles"], "realized mean cycles",
        )
        commanded = _finite_number(
            row["commanded_mean_cycles"], "commanded mean cycles",
        )
        deviation = _finite_number(row["deviation_pct"], "deviation pct")
        if realized <= 0 or commanded <= 0:
            raise PreflightError(
                "prereg-spec", "physical residual cycle 平均は正数が必要",
            )
        recomputed_deviation = 100.0 * (realized - commanded) / commanded
        if not math.isclose(
            deviation, recomputed_deviation, rel_tol=1e-12, abs_tol=1e-12,
        ):
            raise PreflightError(
                "prereg-spec", "physical residual deviation_pct が実測平均と不一致",
            )
        residual_values.append(
            (shape, mean_us, realized, commanded, deviation),
        )

    widths = _exact_object(
        document["external_floor_reference_widths"],
        {"terminology", "power_guarantee", "values"},
        "external_floor_reference_widths",
    )
    terminology = "external-floor-derived-reference-width"
    if widths["terminology"] != terminology or widths["power_guarantee"] is not False:
        raise PreflightError("prereg-spec", "参考幅の語/検出力非保証が不一致")
    width_rows = widths["values"]
    if type(width_rows) is not list or len(width_rows) != len(WORKLOADS):
        raise PreflightError("prereg-spec", "external floor reference widths 件数不一致")
    reference_widths = []
    expected_reference_values = {
        "write-heavy": (0.67, 1.9),
        "balanced": (1.07, 3.0),
        "read-heavy": (0.22, 0.62),
    }
    for index, workload in enumerate(WORKLOADS):
        row = _exact_object(
            width_rows[index],
            {"workload", "between_run_cv_pct", "reference_width_pct", "source_environment"},
            f"external_floor_reference_widths.values[{index}]",
        )
        cv = _finite_number(row["between_run_cv_pct"], "between-run CV")
        width = _finite_number(row["reference_width_pct"], "reference width")
        expected_environment = "pegasus" if workload == "read-heavy" else "linux-baremetal"
        if row["workload"] != workload or row["source_environment"] != expected_environment \
                or cv <= 0 or width <= 0:
            raise PreflightError("prereg-spec", "external floor reference width row が不正")
        expected_cv, expected_width = expected_reference_values[workload]
        if not math.isclose(cv, expected_cv, abs_tol=1e-12) \
                or not math.isclose(width, expected_width, abs_tol=1e-12):
            raise PreflightError(
                "prereg-spec", f"{workload} の外部 floor 由来参考幅が裁定値と不一致",
            )
        reference_widths.append((workload, cv, width, expected_environment))

    canonical = _canonical_json(document)
    return PreregistrationSpec(
        canonical_json=canonical,
        spec_sha256=_sha256_bytes(canonical.encode("utf-8")),
        patch_sha256=patch_sha,
        formula_sha256=formula_sha,
        registration_rules=tuple(expected_registration_rules.items()),
        means_us=tuple(means_raw),
        shapes=tuple(shapes),
        references=tuple(references),
        block_ids=BLOCK_IDS,
        block_orders=tuple(block_orders),
        workloads=tuple(workloads),
        threads=execution["threads"],
        extime_s=execution["extime_s"],
        performance_reps=execution["performance_reps"],
        correctness_reps=execution["correctness_reps"],
        correctness_mode=execution["correctness_mode"],
        alpha=alpha,
        holm_families=tuple(families),
        permutation_method=permutation["method"],
        permutation_sided=permutation["sided"],
        permutation_statistic=permutation["statistic"],
        permutation_enumeration=permutation["enumeration"],
        pairs_per_family=permutation["pairs_per_family"],
        ci_method=confidence["method"],
        ci_confidence_level=float(confidence["confidence_level"]),
        ci_degrees_of_freedom=confidence["degrees_of_freedom"],
        ci_critical_value=float(confidence["critical_value"]),
        missing_conditions=expected_missing,
        missing_pair_action=missingness["pair_action"],
        missing_family_action=missingness["family_action"],
        indeterminate_pvalue=float(missingness["indeterminate_pvalue"]),
        exposure_metric=exposure["metric"],
        minimum_abort_calls=minimum_calls,
        exposure_below_minimum_action=exposure["below_minimum_action"],
        equivalence_margin_pct=equivalence,
        decision_procedure=expected_decision,
        physical_residual_measurement=residual_measurement,
        maximum_absolute_deviation_pct_exclusive=maximum_absolute_deviation,
        physical_residual_provenance=tuple(residual_provenance.items()),
        physical_residual_values=tuple(residual_values),
        reference_width_terminology=terminology,
        reference_width_power_guarantee=False,
        reference_widths=tuple(reference_widths),
    )


def validate_runtime_physical_residual(
    spec: PreregistrationSpec, clocks_per_us: int,
) -> float:
    if type(spec) is not PreregistrationSpec:
        raise TypeError("spec は exact PreregistrationSpec が必要")
    if type(clocks_per_us) is not int or clocks_per_us <= 0:
        raise PreflightError("physical-residual", "clocks_per_us は正整数が必要")
    if spec.maximum_absolute_deviation_pct_exclusive != 1.0:
        raise PreflightError("physical-residual", "事前登録上限は exact 1.0 が必要")
    absolute_deviations = []
    expected_cells = tuple(
        (shape, mean_us)
        for mean_us in spec.means_us
        for shape, _code, _support in spec.shapes
    )
    observed_cells = tuple(
        (shape, mean_us)
        for shape, mean_us, _realized, _commanded, _deviation
        in spec.physical_residual_values
    )
    if observed_cells != expected_cells:
        raise PreflightError("physical-residual", "実測表が grid の閉集合と不一致")
    for shape, mean_us, realized, commanded, deviation in spec.physical_residual_values:
        expected_commanded = float(mean_us * clocks_per_us)
        if not math.isclose(
            commanded, expected_commanded, rel_tol=0.0, abs_tol=1e-12,
        ):
            raise PreflightError(
                "physical-residual",
                f"{shape}/mu{mean_us} の指示平均が環境 clocks_per_us と不一致",
            )
        recomputed = 100.0 * (realized - commanded) / commanded
        if not math.isclose(
            deviation, recomputed, rel_tol=1e-12, abs_tol=1e-12,
        ):
            raise PreflightError(
                "physical-residual",
                f"{shape}/mu{mean_us} の実測 deviation_pct が再計算値と不一致",
            )
        absolute_deviations.append(abs(recomputed))
    maximum_observed = max(absolute_deviations)
    if maximum_observed >= spec.maximum_absolute_deviation_pct_exclusive:
        raise PreflightError(
            "physical-residual",
            "実測待機平均の絶対偏差が事前登録上限未満でない",
        )
    return maximum_observed


def load_preregistration(
    repo_root: str | os.PathLike[str],
    prereg_commit: str,
) -> Preregistration:
    root = Path(repo_root).resolve()
    path = root / PREREG_REL
    try:
        path = path.resolve(strict=True)
        relative = path.relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise PreflightError("prereg-missing", "事前登録文書が無いか repo 外である") from exc
    if path.is_symlink() or not path.is_file():
        raise PreflightError("prereg-missing", "事前登録文書が regular file でない")
    if relative != PREREG_REL:
        raise PreflightError("prereg-path", "事前登録文書は canonical path でなければならない")
    if _COMMIT_RE.fullmatch(prereg_commit or "") is None:
        raise PreflightError("prereg-commit", "prereg_commit は full lowercase commit ID が必要")
    head = str(_git(root, "rev-parse", "--verify", "HEAD^{commit}")).strip()
    ancestor = subprocess.run(
        ["git", "-C", os.fspath(root), "merge-base", "--is-ancestor", prereg_commit, head],
        capture_output=True, env=source_digest._sanitized_git_env(),
    )
    if ancestor.returncode != 0:
        raise PreflightError("prereg-ancestor", "prereg_commit が HEAD の祖先でない")
    status = str(_git(root, "status", "--porcelain", "--untracked-files=all"))
    if status:
        raise PreflightError("dirty", "repository working tree が dirty")
    raw = path.read_bytes()
    try:
        blob_raw = _git(root, "show", f"{prereg_commit}:{relative}", binary=True)
        blob_sha = str(_git(root, "rev-parse", f"{prereg_commit}:{relative}")).strip()
    except PreflightError as exc:
        raise PreflightError("prereg-blob", "事前登録文書 blob を commit から読めない") from exc
    if raw != blob_raw or not re.fullmatch(r"[0-9a-f]{40,64}", blob_sha):
        raise PreflightError("prereg-blob", "事前登録文書 bytes/blob SHA が commit と不一致")
    spec = parse_preregistration(raw)
    if spec.formula_sha256 != FORMULA_SHA256:
        raise PreflightError("formula-sha", "事前登録した式 SHA が EXPECTED_HOLE_LINE と不一致")
    patch_path = root / PATCH_REL
    try:
        patch_bytes = patch_path.read_bytes()
        committed_patch = _git(root, "show", f"{prereg_commit}:{PATCH_REL}", binary=True)
    except (OSError, PreflightError) as exc:
        raise PreflightError("patch-sha", "patch を現在/事前登録 commit から読めない") from exc
    if patch_bytes != committed_patch:
        raise PreflightError("patch-sha", "current patch bytes が prereg_commit blob と不一致")
    validate_patch_bytes(patch_bytes, spec.patch_sha256)
    analysis_path = root / ANALYSIS_REL
    try:
        analysis_bytes = analysis_path.read_bytes()
        committed_analysis = _git(root, "show", f"{head}:{ANALYSIS_REL}", binary=True)
    except (OSError, PreflightError) as exc:
        raise PreflightError("analysis-binding", "解析コードを current HEAD へ束縛できない") from exc
    if analysis_bytes != committed_analysis:
        raise PreflightError("analysis-binding", "解析コード bytes が current HEAD blob と不一致")
    analysis_code_sha256 = _sha256_bytes(analysis_bytes)
    binding = PreregistrationBinding(
        prereg_commit=prereg_commit,
        prereg_blob_sha=blob_sha,
        spec_sha256=spec.spec_sha256,
        patch_sha256=spec.patch_sha256,
        formula_sha256=spec.formula_sha256,
        analysis_commit=head,
        analysis_code_sha256=analysis_code_sha256,
    )
    return Preregistration(binding=binding, path=relative, spec=spec)


def load_calibration(
    contract: env_contract.ExecutionEnvironmentContract,
    spec: PreregistrationSpec,
) -> tuple[CalibrationSelection, object]:
    loaded = p2_2._load_calibration_once(contract)
    parsed = loaded.parsed
    if hasattr(parsed, "saturation"):
        saturation = parsed.saturation
        quality = parsed.quality
        threads = parsed.threads
        env_tag = parsed.env_tag
        clocks_per_us = parsed.clocks_per_us
        schema_version = loaded.verified.schema_version
        if quality.status != "accepted":
            raise PreflightError("calibration", "calibration quality.status が accepted でない")
    else:
        saturation = parsed.get("saturation")
        threads = parsed.get("threads")
        env_tag = parsed.get("env_tag")
        clocks_per_us = parsed.get("clocks_per_us")
        schema_version = loaded.verified.schema_version
    if type(saturation) is not dict:
        raise PreflightError("calibration", "calibration saturation が欠落")
    records = saturation.get("records")
    saturated = saturation.get("saturated")
    lower_bound = saturation.get("lower_bound_selected")
    cache_warning = saturation.get("cache_floor_warning")
    if type(records) is not int or isinstance(records, bool) or records <= 0:
        raise PreflightError("calibration", "selected records が正整数でない")
    if threads != spec.threads or env_tag != contract.env_tag \
            or clocks_per_us != contract.clocks_per_us:
        raise PreflightError("calibration", "calibration と formal 動作点/env contract が不一致")
    if saturated is not True and lower_bound is not True:
        raise PreflightError("calibration", "saturated/lower_bound_selected のどちらも成立しない")
    if cache_warning is not False:
        raise PreflightError("calibration", "cache_floor_warning が false でない")
    return CalibrationSelection(
        path=contract.calibration_ref.path,
        sha256=contract.calibration_ref.sha256,
        schema_version=schema_version,
        records=records,
        threads=threads,
        env_tag=env_tag,
        clocks_per_us=clocks_per_us,
        saturated=bool(saturated),
        lower_bound_selected=bool(lower_bound),
        cache_floor_warning=cache_warning,
    ), loaded.verified


def config_for(
    workload_tag: str,
    prereg: Preregistration,
    calibration: CalibrationSelection,
    build_context: BuildRunContext,
    contract: env_contract.ExecutionEnvironmentContract,
) -> CampaignConfig:
    spec = prereg.spec
    workloads = spec.workload_map
    if workload_tag not in workloads:
        raise ValueError(f"未知 workload: {workload_tag!r}")
    search_config = {
        "scale": "silo-b10-backoff-shape",
        "space_version": SPACE_VERSION,
        "workload": workload_tag,
        "ycsb": workloads[workload_tag],
        "means_us": list(spec.means_us),
        "shape_codes": {name: code for name, code, _support in spec.shapes},
        "references": [name for name, _back_off, _fixed in spec.references],
        "blocks": list(spec.block_ids),
        "block_run_order": {
            block: list(order) for block, order in spec.block_orders
        },
        "records": calibration.records,
        "threads": spec.threads,
        "extime": spec.extime_s,
        "reps": spec.performance_reps,
        "calibration": calibration.as_dict(),
        "preregistration_path": prereg.path,
        "preregistration_binding": prereg.binding.as_dict(),
        "preregistration_spec": spec.as_dict(),
        "minimum_abort_calls": prereg.minimum_abort_calls,
        "physical_residual": {
            "measurement": spec.physical_residual_measurement,
            "maximum_absolute_deviation_pct_exclusive": (
                prereg.maximum_absolute_deviation_pct_exclusive
            ),
            "values": [
                {
                    "shape": shape,
                    "mean_us": mean_us,
                    "realized_mean_cycles": realized,
                    "commanded_mean_cycles": commanded,
                    "deviation_pct": deviation,
                }
                for shape, mean_us, realized, commanded, deviation
                in spec.physical_residual_values
            ],
        },
        "decision": {
            "version": "paired-sign-flip-holm/v1",
            "pairs_per_family": spec.pairs_per_family,
            "family_size": len(spec.holm_families),
            "alpha": spec.alpha,
            "indeterminate_pvalue": spec.indeterminate_pvalue,
            "equivalence_margin_pct": prereg.equivalence_margin_pct,
        },
        SEARCH_CONFIG_VERIFY_KEY: spec.correctness_mode,
    }
    cfg = CampaignConfig(
        spec_slug=f"b10-backoff-shape-silo-{workload_tag}",
        search_tag="formal",
        spec_content=(
            "B-10 registered equal-target-mean backoff-shape comparison; "
            "15 genomes, three independent paired blocks, no screening; "
            f"workload={workload_tag}"
        ),
        ccbench_commit=PIN,
        search_config=search_config,
        trial=f"{TRIAL}-{spec.spec_sha256[:16]}",
    )
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    return ident.bind_environment_contract(cfg, contract)


def perf_for(
    workload_tag: str,
    calibration: CalibrationSelection,
    spec: PreregistrationSpec,
) -> PerfConfig:
    workloads = spec.workload_map
    if workload_tag not in workloads:
        raise ValueError(f"未知 workload: {workload_tag!r}")
    return PerfConfig(
        records=calibration.records,
        threads=spec.threads,
        workload=workloads[workload_tag],
        extime=spec.extime_s,
        reps=spec.performance_reps,
    )


def _decode_lock_search_config(raw: str) -> Mapping[str, object]:
    try:
        decoded = campaign_lock.decode_campaign_lock(raw)
    except campaign_lock.CampaignLockCodecError as exc:
        raise PreflightError("resume-binding", "campaign.lock schema が不正") from exc
    search_config = decoded.identity.get("search_config")
    if type(search_config) is not dict:
        raise PreflightError("resume-binding", "campaign.lock search_config が object でない")
    return search_config


def assert_resumable_binding(
    layout: CampaignLayout,
    binding: PreregistrationBinding,
) -> None:
    """Reject legacy/mismatched WAL before layout creation or repair."""
    lock_exists = os.path.lexists(layout.lock_file)
    wal_exists = os.path.lexists(layout.wal_file)
    if wal_exists and not lock_exists:
        raise PreflightError("resume-binding", "WAL があるのに campaign.lock が無い")
    if lock_exists:
        raw = wal.read_lock(layout)
        if raw is None:
            raise PreflightError("resume-binding", "campaign.lock を読めない")
        stored = _decode_lock_search_config(raw).get("preregistration_binding")
        if stored != binding.as_dict():
            raise PreflightError("resume-binding", "campaign.lock の事前登録束縛が欠落/不一致")
    if not wal_exists:
        return
    records, truncated = wal.read_records_checked(layout)
    if truncated:
        raise PreflightError("resume-binding", "既存 WAL が未終端")
    for record in records:
        if record.stage != STAGE_BUILD_START:
            continue
        if record.payload.get(B10_BUILD_START_BINDING_KEY) != binding.as_dict():
            raise PreflightError(
                "resume-binding", "既存 BUILD_START の事前登録値が欠落/不一致",
            )
        admission = record.payload.get("build_admission")
        input_sha = admission.get("input_sha256") if isinstance(admission, dict) else None
        if input_sha != binding.binding_sha256:
            raise PreflightError(
                "resume-binding", "既存 BUILD_START の事前登録 commitment が欠落/不一致",
            )


@contextlib.contextmanager
def bind_build_start_wal(binding: PreregistrationBinding):
    """Add the complete prereg/spec/analysis binding to every BUILD_START.

    The shared pipeline has no caller-owned BUILD_START extension seam.  B10 is
    a registered single-process campaign, so this scoped adapter serializes the
    process-wide writer replacement, adds one closed key without changing WAL
    admission semantics, and restores the exact original writer on exit.
    """
    if type(binding) is not PreregistrationBinding:
        raise TypeError("binding は exact PreregistrationBinding が必要")
    with _WAL_BINDING_LOCK:
        original = wal.log

        def bound_log(layout, variant, stage, env_tag, payload, *args, **kwargs):
            if stage == STAGE_BUILD_START:
                if type(payload) is not dict or B10_BUILD_START_BINDING_KEY in payload:
                    raise PreflightError("build-start-binding", "BUILD_START payload が拡張不能")
                payload = {
                    **payload,
                    B10_BUILD_START_BINDING_KEY: binding.as_dict(),
                }
            return original(layout, variant, stage, env_tag, payload, *args, **kwargs)

        wal.log = bound_log
        try:
            yield
        finally:
            if wal.log is not bound_log:
                wal.log = original
                raise RuntimeError("B10 実行中に WAL writer が別値へ置換された")
            wal.log = original


def sign_flip_permutation_pvalue(differences: Sequence[float]) -> float:
    values = tuple(float(value) for value in differences)
    if not values or any(not math.isfinite(value) for value in values):
        raise ValueError("differences must be a non-empty finite sequence")
    observed = abs(sum(values))
    extreme = 0
    total = 1 << len(values)
    tolerance = 1e-15 * max(1.0, observed)
    for mask in range(total):
        permuted = sum(
            value if mask & (1 << index) else -value
            for index, value in enumerate(values)
        )
        if abs(permuted) + tolerance >= observed:
            extreme += 1
    return extreme / total


def holm_adjust(pvalues: Mapping[object, float]) -> dict[object, float]:
    if not pvalues:
        return {}
    ordered = sorted(pvalues.items(), key=lambda item: (item[1], repr(item[0])))
    m = len(ordered)
    running = 0.0
    adjusted: dict[object, float] = {}
    for rank, (key, raw) in enumerate(ordered):
        if not math.isfinite(raw) or raw < 0 or raw > 1:
            raise ValueError("p-values must be finite values in [0,1]")
        running = max(running, min(1.0, (m - rank) * raw))
        adjusted[key] = running
    return adjusted


def _record_usable(
    record: Mapping[str, object], spec: PreregistrationSpec,
) -> bool:
    return (
        record.get("correctness_certified") is True
        and record.get("official_certification") is False
        and record.get("unstable") is False
        and type(record.get("median_tps")) in {int, float}
        and math.isfinite(float(record["median_tps"]))
        and float(record["median_tps"]) > 0
        and type(record.get("backoff_call_count")) is int
        and not isinstance(record.get("backoff_call_count"), bool)
        and int(record["backoff_call_count"]) >= spec.minimum_abort_calls
        and record.get("missing") is False
    )


def _paired_effect(shape: Mapping[str, object], constant: Mapping[str, object]) -> float:
    return float(shape["median_tps"]) / float(constant["median_tps"]) - 1.0


def cell_effects(
    records: Sequence[Mapping[str, object]], spec: PreregistrationSpec,
) -> list[dict[str, object]]:
    if type(spec) is not PreregistrationSpec:
        raise TypeError("spec は exact PreregistrationSpec が必要")
    equivalence_margin_pct = spec.equivalence_margin_pct
    if not math.isfinite(equivalence_margin_pct) or not 0 < equivalence_margin_pct < 100:
        raise ValueError("equivalence_margin_pct must be finite and in (0,100)")
    equivalence_margin = equivalence_margin_pct / 100.0
    indexed = {
        (row.get("workload"), row.get("block_id"), row.get("shape"), row.get("mean_us")): row
        for row in records
        if row.get("shape") in spec.shape_codes and row.get("mean_us") in spec.means_us
    }
    output = []
    for workload, _flags in spec.workloads:
        for shape, _code, _support in spec.shapes:
            for mean_us in spec.means_us:
                effects = []
                usable = True
                for block_id in spec.block_ids:
                    row = indexed.get((workload, block_id, shape, mean_us))
                    constant = indexed.get((workload, block_id, "constant", mean_us))
                    if row is None or constant is None \
                            or not _record_usable(row, spec) \
                            or not _record_usable(constant, spec):
                        usable = False
                        break
                    effects.append(0.0 if shape == "constant" else _paired_effect(row, constant))
                effect = low = high = None
                equivalence_relation = "indeterminate"
                if usable:
                    effect = statistics.fmean(effects)
                    if shape == "constant":
                        low = high = 0.0
                    else:
                        half = (
                            spec.ci_critical_value
                            * statistics.stdev(effects)
                            / math.sqrt(len(spec.block_ids))
                        )
                        low, high = effect - half, effect + half
                    if low >= -equivalence_margin and high <= equivalence_margin:
                        equivalence_relation = "inside-equivalence-range"
                    elif high < -equivalence_margin or low > equivalence_margin:
                        equivalence_relation = "outside-equivalence-range"
                    else:
                        equivalence_relation = "overlaps-equivalence-boundary"
                output.append({
                    "workload": workload, "shape": shape, "mean_us": mean_us,
                    "effect": effect, "ci95_low": low, "ci95_high": high,
                    "status": "estimable" if usable else "indeterminate",
                    "equivalence_margin_pct": equivalence_margin_pct,
                    "equivalence_relation": equivalence_relation,
                })
    return output


def judge(
    records: Sequence[Mapping[str, object]], spec: PreregistrationSpec,
) -> dict[str, object]:
    if type(spec) is not PreregistrationSpec:
        raise TypeError("spec は exact PreregistrationSpec が必要")
    indexed = {
        (row.get("workload"), row.get("block_id"), row.get("shape"), row.get("mean_us")): row
        for row in records
    }
    raw: dict[tuple[str, str], float] = {}
    family_data: dict[tuple[str, str], dict[str, object]] = {}
    for workload, shape in spec.holm_families:
        key = (workload, shape)
        differences = []
        reasons = []
        for block_id in spec.block_ids:
            for mean_us in spec.means_us:
                row = indexed.get((workload, block_id, shape, mean_us))
                constant = indexed.get((workload, block_id, "constant", mean_us))
                if row is None or constant is None:
                    reasons.append(f"missing:{block_id}:mu{mean_us}")
                elif not _record_usable(row, spec) \
                        or not _record_usable(constant, spec):
                    reasons.append(f"unusable-or-underexposed:{block_id}:mu{mean_us}")
                else:
                    differences.append(_paired_effect(row, constant))
        complete = len(differences) == spec.pairs_per_family and not reasons
        pvalue = (
            sign_flip_permutation_pvalue(differences)
            if complete else spec.indeterminate_pvalue
        )
        raw[key] = pvalue
        family_data[key] = {
            "workload": workload, "shape": shape,
            "pairs": len(differences), "differences": differences,
            "raw_p": pvalue, "reasons": reasons,
            "status": "testable" if complete else "indeterminate",
        }
    adjusted = holm_adjust(raw)
    families = []
    for key in sorted(family_data):
        item = family_data[key]
        item["holm_p"] = adjusted[key]
        if item["status"] == "indeterminate":
            item["outcome"] = "indeterminate"
        elif adjusted[key] <= spec.alpha:
            item["outcome"] = "different"
        else:
            item["outcome"] = "not-detected"
        families.append(item)
    return {
        "schema_version": "b10-backoff-shape-judgement/v1",
        "alpha": spec.alpha,
        "spec_sha256": spec.spec_sha256,
        "families": families,
        "cell_effects": cell_effects(records, spec),
    }


def _count_metric(metrics: Mapping[str, str], key: str) -> int:
    value = benchparse._num(metrics.get(key))
    if value is None or not math.isfinite(value) or value < 0 or not float(value).is_integer():
        raise RuntimeError(f"performance output の {key} が一意な非負整数でない")
    return int(value)


def _extract_applied_probe_contract(sub: str | os.PathLike[str]) -> tuple[str, str]:
    """Return the applied hole and CompileOptions hash after exact-source checks."""
    root = Path(sub)
    try:
        source_bytes = (root / SOURCE_REL).read_bytes()
        options_bytes = (root / OPTIONS_REL).read_bytes()
        util_text = (root / "include/util.hh").read_text(encoding="utf-8")
        compile_options_bytes = (root / "cmake/CompileOptions.cmake").read_bytes()
        source_text = source_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise PreflightError("probe-source", "applied probe source を読めない") from exc
    hole_lines = [
        line for line in source_text.splitlines()
        if line == EXPECTED_HOLE_LINE
    ]
    if hole_lines != [EXPECTED_HOLE_LINE]:
        raise PreflightError(
            "probe-source", "applied backoff.hh から exact hole を一意に抽出できない",
        )
    if source_text.count(EXPECTED_WAIT_LOOP) != 1:
        raise PreflightError(
            "probe-source", "applied backoff.hh の待機 loop が reviewed bytes と不一致",
        )
    if util_text.count(EXPECTED_CHK_CLK_SPAN) != 1:
        raise PreflightError(
            "probe-source", "chkClkSpan が CCBench reviewed bytes と不一致",
        )
    if _sha256_bytes(options_bytes) != EXPECTED_OPTIONS_SHA256 \
            or _frame_sha256(source_bytes) != EXPECTED_BACKOFF_FRAME_SHA256:
        raise PreflightError(
            "probe-source", "applied Options/backoff frame が reviewed bytes と不一致",
        )
    return hole_lines[0], _sha256_bytes(compile_options_bytes)


def _render_probe_harness(hole_line: str) -> str:
    if hole_line != EXPECTED_HOLE_LINE:
        raise PreflightError("probe-source", "probe harness hole が applied source と不一致")
    return f"""#include <x86intrin.h>

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

[[maybe_unused]] static uint64_t rdtscp() {{
  uint64_t rax;
  uint64_t rdx;
  uint32_t aux;
  asm volatile("rdtscp" : "=a"(rax), "=d"(rdx), "=c"(aux)::);
  return (rdx << 32) | rax;
}}

{EXPECTED_CHK_CLK_SPAN}

static uint64_t probe_once(const size_t clocks_per_us) {{
    uint64_t start(rdtscp()), stop;
{hole_line}
{EXPECTED_WAIT_LOOP}
    return stop - start;
}}

static bool parse_positive(const char* text, size_t& value) {{
  errno = 0;
  char* end = nullptr;
  const unsigned long long parsed = std::strtoull(text, &end, 10);
  if (errno != 0 || end == text || *end != '\\0' || parsed == 0) return false;
  value = static_cast<size_t>(parsed);
  return static_cast<unsigned long long>(value) == parsed;
}}

int main(int argc, char** argv) {{
  if (argc != 3) return 2;
  size_t clocks_per_us = 0;
  size_t calls = 0;
  if (!parse_positive(argv[1], clocks_per_us) || !parse_positive(argv[2], calls)) return 2;
  std::vector<uint64_t> elapsed;
  elapsed.reserve(calls);
  for (size_t index = 0; index < calls; ++index) {{
    elapsed.push_back(probe_once(clocks_per_us));
  }}
  const size_t written = std::fwrite(
      elapsed.data(), sizeof(uint64_t), elapsed.size(), stdout);
  return written == elapsed.size() ? 0 : 3;
}}
"""


def _run_probe_command(argv: Sequence[str], *, label: str) -> subprocess.CompletedProcess:
    try:
        completed = subprocess.run(
            list(argv), capture_output=True, text=True, timeout=120.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreflightError("probe-build", f"{label} を起動できない: {exc}") from exc
    if completed.returncode != 0:
        raise PreflightError(
            "probe-build",
            f"{label} が失敗した: {(completed.stderr or completed.stdout)[-500:]}",
        )
    return completed


def _compile_probe_harnesses(
    sub: str,
    build_root: Path,
    *,
    hole_line: str,
    compile_options_sha256: str,
    cxx: str,
) -> tuple[dict[tuple[str, int], Path], dict[str, object]]:
    cmake = shutil.which("cmake")
    if cmake is None:
        raise PreflightError("probe-build", "cmake が見つからない")
    compiler_candidate = shutil.which(cxx) or cxx
    compiler = Path(compiler_candidate).resolve(strict=True)
    source_dir = build_root / "source"
    binary_dir = build_root / "build"
    source_dir.mkdir()
    (source_dir / "probe.cc").write_text(
        _render_probe_harness(hole_line), encoding="utf-8",
    )
    targets: list[tuple[str, int, str]] = []
    cmake_lines = [
        "cmake_minimum_required(VERSION 3.10)",
        "project(izanagi_b10_probe LANGUAGES CXX)",
        f'include("{Path(sub, "cmake/CompileOptions.cmake").as_posix()}")',
    ]
    for mean_us in MEANS_US:
        for shape, _code in SHAPES:
            target = f"b10_probe_{shape.replace('-', '_')}_mu{mean_us}"
            encoded = encode(shape, mean_us)
            targets.append((shape, mean_us, target))
            cmake_lines.extend([
                f"add_executable({target} probe.cc)",
                f"target_compile_definitions({target} PRIVATE BACKOFF_FIXED={encoded})",
                f"set_compile_options({target})",
            ])
    (source_dir / "CMakeLists.txt").write_text(
        "\n".join(cmake_lines) + "\n", encoding="utf-8",
    )
    _run_probe_command(
        (
            cmake, "-S", os.fspath(source_dir), "-B", os.fspath(binary_dir),
            "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            f"-DCMAKE_CXX_COMPILER={compiler}",
        ),
        label="probe CMake configure",
    )
    _run_probe_command(
        (
            cmake, "--build", os.fspath(binary_dir), "--parallel",
            str(min(len(targets), os.cpu_count() or 1)),
        ),
        label="probe CMake build",
    )
    try:
        commands_raw = (binary_dir / "compile_commands.json").read_bytes()
        commands = _strict_json(commands_raw.decode("utf-8"), label="compile commands")
    except (OSError, UnicodeError) as exc:
        raise PreflightError("probe-build", "compile_commands.json を読めない") from exc
    if type(commands) is not list or len(commands) != len(targets):
        raise PreflightError("probe-build", "probe compile command 数が登録 grid と不一致")
    required_flags = ("-O3", "-DNDEBUG", "-Wall", "-Wextra", "-Werror", "-std=c++20")
    for command in commands:
        if type(command) is not dict or type(command.get("command")) is not str:
            raise PreflightError("probe-build", "probe compile command schema が不正")
        tokens = command["command"].split()
        if any(flag not in tokens for flag in required_flags):
            raise PreflightError(
                "probe-build", "CCBench Release/CompileOptions flags と probe が不一致",
            )
    version = _run_probe_command((os.fspath(compiler), "--version"), label="C++ compiler")
    cmake_version = _run_probe_command((cmake, "--version"), label="cmake")
    binaries = {
        (shape, mean_us): binary_dir / target
        for shape, mean_us, target in targets
    }
    if any(not path.is_file() or path.is_symlink() for path in binaries.values()):
        raise PreflightError("probe-build", "probe binary の閉集合が揃わない")
    return binaries, {
        "build_system": "cmake",
        "cmake_path": os.path.realpath(cmake),
        "cmake_version": cmake_version.stdout.splitlines()[0],
        "build_type": "Release",
        "cxx_standard": 20,
        "cxx_extensions": False,
        "compiler_path": os.fspath(compiler),
        "compiler_version": version.stdout.splitlines()[0],
        "required_flags": list(required_flags),
        "compile_options_path": "cmake/CompileOptions.cmake",
        "compile_options_sha256": compile_options_sha256,
        "compile_commands_sha256": _sha256_bytes(commands_raw),
    }


def _measure_probe_binary(
    binary: Path, *, clocks_per_us: int, calls: int,
) -> list[int]:
    if type(calls) is not int or calls < PROBE_CALLS_PER_CELL:
        raise PreflightError("probe-measurement", "probe calls は最低 100,000 が必要")
    pipeline._require_measurement_site("B10 backoff-shape realized-wait probe")
    try:
        completed = subprocess.run(
            [os.fspath(binary), str(clocks_per_us), str(calls)],
            capture_output=True, timeout=300.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreflightError("probe-measurement", f"probe binary を実行できない: {exc}") from exc
    if completed.returncode != 0 or completed.stderr:
        raise PreflightError(
            "probe-measurement",
            f"probe binary が失敗した: rc={completed.returncode} "
            f"stderr={completed.stderr[-300:]!r}",
        )
    expected_bytes = calls * struct.calcsize("=Q")
    if len(completed.stdout) != expected_bytes:
        raise PreflightError("probe-measurement", "probe sample byte 数が calls と不一致")
    return [value[0] for value in struct.iter_unpack("=Q", completed.stdout)]


def _summarize_probe_cell(
    shape: str,
    mean_us: int,
    samples: Sequence[int],
    *,
    clocks_per_us: int,
) -> dict[str, object]:
    if len(samples) < PROBE_CALLS_PER_CELL \
            or any(type(value) is not int or value <= 0 for value in samples):
        raise PreflightError("probe-measurement", "probe sample 分布が不正")
    ordered = sorted(samples)
    realized_mean = statistics.fmean(ordered)
    median = float(statistics.median(ordered))
    p99 = ordered[math.ceil(0.99 * len(ordered)) - 1]
    commanded = mean_us * clocks_per_us
    deviation = realized_mean - commanded
    return {
        "shape": shape,
        "mean_us": mean_us,
        "encoded": encode(shape, mean_us),
        "calls": len(ordered),
        "realized_mean_cycles": realized_mean,
        "realized_median_cycles": median,
        "realized_p50_cycles": median,
        "realized_p99_cycles": p99,
        "realized_min_cycles": ordered[0],
        "commanded_mean_cycles": commanded,
        "deviation_cycles": deviation,
        "absolute_deviation_cycles": abs(deviation),
        "deviation_pct": 100.0 * deviation / commanded,
    }


def _shape_differences(cells: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    indexed = {
        (row["shape"], row["mean_us"]): float(row["realized_mean_cycles"])
        for row in cells
    }
    differences = []
    for mean_us in MEANS_US:
        constant = indexed[("constant", mean_us)]
        for shape in ("symmetric-modulo",):
            difference = indexed[(shape, mean_us)] - constant
            differences.append({
                "shape": shape,
                "mean_us": mean_us,
                "realized_mean_difference_cycles": difference,
                "realized_mean_difference_pct": 100.0 * difference / constant,
            })
    return differences


def _validate_probe_result(result: object) -> dict[str, object]:
    result = _exact_object(
        result,
        {
            "schema_version", "source_commit", "patch_sha256", "formula_sha256",
            "clocks_per_us", "host", "measured_at_utc", "calls_per_cell",
            "compile", "cells", "shape_differences_from_constant", "submission",
        },
        "probe result",
    )
    if result["schema_version"] != PROBE_SCHEMA \
            or type(result["source_commit"]) is not str \
            or _COMMIT_RE.fullmatch(result["source_commit"]) is None \
            or type(result["patch_sha256"]) is not str \
            or _SHA256_RE.fullmatch(result["patch_sha256"]) is None \
            or result["formula_sha256"] != FORMULA_SHA256:
        raise PreflightError("probe-schema", "probe identity/schema が不正")
    clocks_per_us = _positive_int(result["clocks_per_us"], "probe clocks_per_us")
    calls = _positive_int(result["calls_per_cell"], "probe calls_per_cell")
    if calls < PROBE_CALLS_PER_CELL:
        raise PreflightError("probe-schema", "probe calls_per_cell が 100,000 未満")
    host = _exact_object(result["host"], {"hostname", "fqdn", "machine"}, "probe host")
    if any(type(host[key]) is not str or not host[key] for key in host):
        raise PreflightError("probe-schema", "probe host が不正")
    if type(result["measured_at_utc"]) is not str:
        raise PreflightError("probe-schema", "probe timestamp が文字列でない")
    try:
        timestamp = dt.datetime.fromisoformat(result["measured_at_utc"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise PreflightError("probe-schema", "probe timestamp が ISO-8601 でない") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() != dt.timedelta(0):
        raise PreflightError("probe-schema", "probe timestamp が UTC でない")
    compile_info = _exact_object(
        result["compile"],
        {
            "build_system", "cmake_path", "cmake_version", "build_type",
            "cxx_standard", "cxx_extensions", "compiler_path", "compiler_version",
            "required_flags", "compile_options_path", "compile_options_sha256",
            "compile_commands_sha256",
        },
        "probe compile",
    )
    if compile_info["build_system"] != "cmake" \
            or compile_info["build_type"] != "Release" \
            or compile_info["cxx_standard"] != 20 \
            or compile_info["cxx_extensions"] is not False \
            or compile_info["compile_options_path"] != "cmake/CompileOptions.cmake" \
            or any(
                type(compile_info[key]) is not str or not compile_info[key]
                for key in (
                    "cmake_path", "cmake_version", "compiler_path", "compiler_version",
                )
            ) \
            or type(compile_info["required_flags"]) is not list \
            or type(compile_info["compile_options_sha256"]) is not str \
            or _SHA256_RE.fullmatch(compile_info["compile_options_sha256"]) is None \
            or type(compile_info["compile_commands_sha256"]) is not str \
            or _SHA256_RE.fullmatch(compile_info["compile_commands_sha256"]) is None:
        raise PreflightError("probe-schema", "probe compile contract が不正")
    submission = _exact_object(
        result["submission"],
        {"request_id", "nonce", "receipt_path", "receipt_sha256"},
        "probe submission",
    )
    if type(submission["request_id"]) is not str or not submission["request_id"] \
            or type(submission["nonce"]) is not str \
            or re.fullmatch(r"[0-9a-f]{32}", submission["nonce"]) is None \
            or type(submission["receipt_path"]) is not str or not submission["receipt_path"] \
            or type(submission["receipt_sha256"]) is not str \
            or _SHA256_RE.fullmatch(submission["receipt_sha256"]) is None:
        raise PreflightError("probe-schema", "probe submission binding が不正")
    cells = result["cells"]
    expected_cells = tuple((shape, mean_us) for mean_us in MEANS_US for shape, _ in SHAPES)
    if type(cells) is not list or len(cells) != len(expected_cells):
        raise PreflightError("probe-schema", "probe cell 数が登録 grid と不一致")
    for index, (shape, mean_us) in enumerate(expected_cells):
        row = _exact_object(
            cells[index],
            {
                "shape", "mean_us", "encoded", "calls", "realized_mean_cycles",
                "realized_median_cycles", "realized_p50_cycles", "realized_p99_cycles",
                "realized_min_cycles", "commanded_mean_cycles", "deviation_cycles",
                "absolute_deviation_cycles", "deviation_pct",
            },
            f"probe cells[{index}]",
        )
        if row["shape"] != shape or row["mean_us"] != mean_us \
                or row["encoded"] != encode(shape, mean_us) or row["calls"] != calls:
            raise PreflightError("probe-schema", "probe cell identity/calls が不一致")
        numeric = {
            key: _finite_number(row[key], f"probe {key}")
            for key in (
                "realized_mean_cycles", "realized_median_cycles",
                "realized_p50_cycles", "realized_p99_cycles", "realized_min_cycles",
                "commanded_mean_cycles", "deviation_cycles",
                "absolute_deviation_cycles", "deviation_pct",
            )
        }
        commanded = mean_us * clocks_per_us
        deviation = numeric["realized_mean_cycles"] - commanded
        if numeric["realized_min_cycles"] <= 0 \
                or numeric["realized_mean_cycles"] < numeric["realized_min_cycles"] \
                or not numeric["realized_min_cycles"] \
                    <= numeric["realized_p50_cycles"] \
                    <= numeric["realized_p99_cycles"] \
                or numeric["realized_median_cycles"] != numeric["realized_p50_cycles"] \
                or numeric["commanded_mean_cycles"] != commanded \
                or not math.isclose(numeric["deviation_cycles"], deviation, abs_tol=1e-12) \
                or not math.isclose(
                    numeric["absolute_deviation_cycles"], abs(deviation), abs_tol=1e-12,
                ) \
                or not math.isclose(
                    numeric["deviation_pct"], 100.0 * deviation / commanded,
                    rel_tol=1e-12, abs_tol=1e-12,
                ):
            raise PreflightError("probe-schema", "probe cell 統計/差分が内部不整合")
    expected_differences = _shape_differences(cells)
    if result["shape_differences_from_constant"] != expected_differences:
        raise PreflightError("probe-schema", "probe shape 差分が cell 平均と不一致")
    return result


def _write_probe_result_create_only(path: Path, result: Mapping[str, object]) -> None:
    validated = _validate_probe_result(dict(result))
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise PreflightError("probe-output", "probe output parent が real directory でない")
    raw = (json.dumps(
        validated, ensure_ascii=False, indent=2, allow_nan=False,
    ) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        written = os.write(descriptor, raw)
        if written != len(raw):
            raise OSError("short create-only write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def measure_performance_cell(
    binary: str,
    perf: PerfConfig,
    *,
    clocks_per_us: int,
    numactl: Sequence[str],
    use_perf: bool,
    do_settle: bool,
) -> dict[str, object]:
    """One fixed five-repetition block with aggregate abort exposure."""
    pipeline._require_measurement_site("B10 backoff-shape performance block")
    base_flags = [
        f"-thread_num={perf.threads}", f"-ycsb_tuple_num={perf.records}",
        f"-extime={perf.extime}", f"-clocks_per_us={clocks_per_us}",
        *(f"-{key}={value}" for key, value in perf.workload.items()),
    ]
    throughputs: list[float] = []
    abort_counts: list[int] = []
    commit_counts: list[int] = []
    rep_walltime_s: list[float] = []
    with tempfile.TemporaryDirectory(prefix="izanagi_b10_notrace_") as trace_dir:
        with bench_lock():
            competing = competing_bench_pids()
            if competing:
                raise RuntimeError(f"競合 ccbench process を検出: {competing!r}")
            settled = settle() if do_settle else None
            for _rep in range(perf.reps):
                metrics, _counters, wall = run_once(
                    binary, base_flags, numactl=tuple(numactl),
                    extra_env={"IZANAGI_TRACE_DIR": trace_dir},
                    timeout_s=120.0, strict_returncode=True, use_perf=use_perf,
                )
                tps = benchparse.throughput_tps(metrics)
                if tps is None or not math.isfinite(tps) or tps <= 0:
                    raise RuntimeError("performance repetition に throughput が無い")
                throughputs.append(float(tps))
                abort_counts.append(_count_metric(metrics, "abort_counts_"))
                commits = _count_metric(metrics, "commit_counts_")
                batch = _count_metric(metrics, "batch_commit_counts_")
                commit_counts.append(commits + batch)
                rep_walltime_s.append(float(wall))
    floor = noise_floor(throughputs)
    if floor.median is None or floor.cv is None:
        raise RuntimeError("performance block の median/CV を確定できない")
    abort_count = sum(abort_counts)
    commit_count = sum(commit_counts)
    denominator = abort_count + commit_count
    return {
        "median_tps": floor.median,
        "cv": floor.cv,
        "unstable": bool(floor.high_variance),
        "throughputs": throughputs,
        "abort_count": abort_count,
        "commit_count": commit_count,
        "abort_rate": abort_count / denominator if denominator else None,
        "backoff_call_count": abort_count,
        "backoff_calls_per_second": abort_count / (perf.extime * perf.reps),
        "rep_abort_counts": abort_counts,
        "rep_commit_counts": commit_counts,
        "rep_walltime_s": rep_walltime_s,
        "settled": None if settled is None else settled.get("settled"),
        "missing": False,
    }


def _write_block_record_create_only(path: Path, value: Mapping[str, object]) -> str:
    """Publish one hash-enveloped block record exactly once."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise PreflightError("measurement-record", "block record parent が real directory でない")
    record = dict(value)
    record_sha256 = _sha256_json(record)
    envelope = {
        "schema_version": "b10-backoff-shape-block-envelope/v1",
        "record_sha256": record_sha256,
        "record": record,
    }
    raw = (_canonical_json(envelope) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        written = os.write(descriptor, raw)
        if written != len(raw):
            raise OSError("short create-only write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return record_sha256


def _load_block_record(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise PreflightError("measurement-record", f"block record が regular file でない: {path}")
    try:
        envelope = _strict_json(path.read_text(encoding="utf-8"), label=os.fspath(path))
    except (OSError, UnicodeError) as exc:
        raise PreflightError("measurement-record", f"block record を読めない: {path}") from exc
    envelope = _exact_object(
        envelope, {"schema_version", "record_sha256", "record"}, "block envelope",
    )
    if envelope["schema_version"] != "b10-backoff-shape-block-envelope/v1" \
            or type(envelope["record"]) is not dict \
            or type(envelope["record_sha256"]) is not str \
            or _SHA256_RE.fullmatch(envelope["record_sha256"]) is None \
            or _sha256_json(envelope["record"]) != envelope["record_sha256"]:
        raise PreflightError("measurement-record", "block record envelope/hash が不正")
    return {**envelope["record"], "record_sha256": envelope["record_sha256"]}


def _read_block_records(root: Path) -> list[dict[str, object]]:
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        raise PreflightError("measurement-record", "block record root が real directory でない")
    unexpected = [path for path in root.iterdir() if path.suffix != ".json"]
    if unexpected:
        raise PreflightError("measurement-record", "block record root に未知 entry がある")
    rows = []
    for path in sorted(root.glob("*.json")):
        row = _load_block_record(path)
        schedule_index = row.get("schedule_index")
        if type(schedule_index) is not int:
            raise PreflightError("measurement-record", "block record schedule_index が不正")
        expected_name = _block_record_filename(
            str(row.get("block_id")), schedule_index,
            str(row.get("point")),
        )
        if path.name != expected_name:
            raise PreflightError("measurement-record", "block record filename/identity 不一致")
        rows.append(row)
    return rows


def _block_record_filename(block_id: str, schedule_index: int, point: str) -> str:
    if block_id not in BLOCK_IDS or type(schedule_index) is not int \
            or schedule_index < 0 or schedule_index >= POINTS_PER_BLOCK \
            or re.fullmatch(r"[a-z0-9-]+", point or "") is None:
        raise PreflightError("measurement-record", "block record cell identity が不正")
    return f"{block_id}--{schedule_index:02d}--{point}.json"


def _validate_prior_block_records(
    records: Sequence[Mapping[str, object]],
    *,
    workload: str,
    prereg: Preregistration,
) -> dict[tuple[str, str], Mapping[str, object]]:
    indexed = {}
    expected_order = prereg.spec.block_order_map
    for row in records:
        block_id = row.get("block_id")
        point = row.get("point")
        index = row.get("schedule_index")
        request_id = row.get("request_id")
        nonce = row.get("submission_nonce")
        expected_trial = None
        if type(request_id) is str and type(nonce) is str:
            expected_trial = (
                re.sub(r"[^A-Za-z0-9._-]", "-", request_id)
                + f"-{nonce[:12]}"
            )
        if row.get("schema_version") != "b10-backoff-shape-block/v2" \
                or row.get("official_certification") is not False \
                or row.get("workload") != workload \
                or row.get("preregistration_binding") != prereg.binding.as_dict() \
                or row.get("spec_sha256") != prereg.spec.spec_sha256 \
                or row.get("analysis_commit") != prereg.binding.analysis_commit \
                or row.get("analysis_code_sha256") != prereg.binding.analysis_code_sha256 \
                or row.get("source_commit") != prereg.binding.analysis_commit \
                or type(request_id) is not str or not request_id \
                or type(nonce) is not str or re.fullmatch(r"[0-9a-f]{32}", nonce) is None \
                or row.get("trial") != expected_trial \
                or type(row.get("submission_receipt")) is not str \
                or type(row.get("submission_receipt_sha256")) is not str \
                or _SHA256_RE.fullmatch(row["submission_receipt_sha256"]) is None \
                or type(row.get("job_script_sha256")) is not str \
                or _SHA256_RE.fullmatch(row["job_script_sha256"]) is None \
                or block_id not in expected_order \
                or type(index) is not int \
                or index < 0 or index >= len(expected_order[block_id]) \
                or expected_order[block_id][index] != point:
            raise PreflightError("resume-binding", "既存 block record の束縛/identity が不一致")
        expected_shape, expected_mean_us, expected_encoded = _name_metadata(point)
        expected_genome = dict(named_genomes())[point].canonical()
        if (
            row.get("shape"), row.get("mean_us"),
            row.get("encoded"), row.get("genome"),
        ) != (
            expected_shape, expected_mean_us, expected_encoded, expected_genome,
        ):
            raise PreflightError(
                "resume-binding",
                "既存 block record の point/metadata が正規 grid と不一致",
            )
        receipt_path = Path(row["submission_receipt"])
        try:
            receipt_bytes = receipt_path.read_bytes()
        except OSError as exc:
            raise PreflightError(
                "measurement-record", "block record の submission receipt を再読できない",
            ) from exc
        if receipt_path.is_symlink() or _sha256_bytes(receipt_bytes) \
                != row["submission_receipt_sha256"]:
            raise PreflightError(
                "measurement-record", "block record の submission receipt hash が不一致",
            )
        key = (block_id, point)
        if key in indexed:
            raise PreflightError("measurement-record", "同一 block cell record が重複")
        indexed[key] = row
    return indexed


def _certification_attempts(
    layout: CampaignLayout, build_context: BuildRunContext,
) -> dict[str, CertificationAttempt]:
    states = wal.replay(layout, admission_policy=build_context.policy)
    records, truncated = wal.read_records_checked(layout)
    if truncated:
        raise PreflightError("resume-binding", "certification WAL が未終端")
    attempts: dict[str, CertificationAttempt] = {}
    for variant, state in states.items():
        if not state.committed:
            continue
        attempt = state.committed_attempt_id
        if type(attempt) is not str or not attempt:
            raise PreflightError("perf-binary-binding", "COMMIT attempt ID が不正")
        build_done = [
            record for record in records
            if record.variant == variant
            and record.stage == STAGE_BUILD_DONE
            and record.payload.get("build_attempt_id") == attempt
        ]
        if len(build_done) != 1:
            raise PreflightError(
                "perf-binary-binding", "committed attempt の BUILD_DONE が一意でない",
            )
        perf_sha = build_done[0].payload.get("perf_bin_sha256")
        if type(perf_sha) is not str or not buildcache.is_full_sha256(perf_sha):
            raise PreflightError(
                "perf-binary-binding", "committed attempt の perf_bin_sha256 が不正",
            )
        attempts[variant] = CertificationAttempt(attempt, perf_sha)
    return attempts


def verify_performance_binary(
    binary: str,
    built_sha256: str,
    certified: CertificationAttempt,
) -> str:
    """Rehash immediately before measurement and bind to certified BUILD_DONE."""
    if type(certified) is not CertificationAttempt:
        raise TypeError("certified は exact CertificationAttempt が必要")
    if not buildcache.is_full_sha256(built_sha256):
        raise PreflightError("perf-binary-binding", "build result SHA が不正")
    try:
        current_sha256 = buildcache.full_sha256(binary)
    except Exception as exc:
        raise PreflightError("perf-binary-binding", "performance binary を再 hash できない") from exc
    if built_sha256 != certified.perf_bin_sha256 \
            or current_sha256 != certified.perf_bin_sha256:
        raise PreflightError(
            "perf-binary-binding",
            "performance binary SHA が correctness-certified BUILD_DONE と不一致",
        )
    return current_sha256


def _formula_generator_resolver(
    context: BuildRunContext, binding: PreregistrationBinding,
):
    return lambda evidence: attest_generator_output(
        context, evidence, generator_input_sha256=binding.binding_sha256,
    )


def _build_binary(
    genome: Genome,
    *,
    trace: bool,
    sub: str,
    cache_root: str,
    contract: env_contract.ExecutionEnvironmentContract,
    build_context: BuildRunContext,
    binding: PreregistrationBinding,
    toolchain_manifest: Mapping[str, object],
) -> tuple[str, str, str]:
    cc, cxx = buildcache.toolchain_compilers_from_manifest(toolchain_manifest)
    evidence = source_digest.resolve_evidence(
        genome, PIN, ccbench_dir=sub, cxx=cxx,
    )
    capability = attest_generator_output(
        build_context, evidence, generator_input_sha256=binding.binding_sha256,
    )
    admission = derive_build_admission(
        build_context, evidence, generator_receipt=capability,
    )
    result = buildcache.build_v2(
        genome,
        trace=trace,
        contract=contract,
        ccbench_commit=PIN,
        src_token=evidence.src_token,
        cc=cc,
        cxx=cxx,
        cache_root=cache_root,
        ccbench_dir=sub,
        admission=admission,
        build_context=build_context,
        source_evidence=evidence,
        expected_toolchain_manifest=toolchain_manifest,
        declared_use_class="official",
    )
    return result.binary, variant_id(genome, evidence.src_token), result.bin_sha256


def _perf_binary(
    genome: Genome,
    **kwargs,
) -> tuple[str, str, str]:
    return _build_binary(genome, trace=False, **kwargs)


def _name_metadata(name: str) -> tuple[Optional[str], Optional[int], Optional[int]]:
    if name == "none":
        return None, None, None
    if name == "adaptive":
        return None, None, None
    if name == "zero-loop":
        return "constant", 0, 0
    match = re.fullmatch(r"(constant|symmetric-modulo)-mu([0-9]+)", name)
    if match is None:
        raise ValueError(f"未知 B10 point name: {name}")
    shape, mean_text = match.groups()
    mean_us = int(mean_text)
    return shape, mean_us, encode(shape, mean_us)


def _nominal_wait(abort_count: int, mean_us: Optional[int]) -> Optional[int]:
    return None if mean_us is None else abort_count * mean_us


def _unavailable_measurement(error: str) -> dict[str, object]:
    return {
        "median_tps": None,
        "cv": None,
        "unstable": False,
        "throughputs": [],
        "abort_count": None,
        "commit_count": None,
        "abort_rate": None,
        "backoff_call_count": None,
        "backoff_calls_per_second": None,
        "rep_abort_counts": [],
        "rep_commit_counts": [],
        "rep_walltime_s": [],
        "settled": None,
        "missing": True,
        "error": error,
    }


def _write_reports(
    report_root: Path,
    *,
    prereg: Preregistration,
    calibration: CalibrationSelection,
    records: Sequence[Mapping[str, object]],
    applied_evidence: Mapping[str, object],
    submission: SubmissionIdentity,
) -> tuple[Path, Path]:
    verdict = judge(records, prereg.spec)
    provenance = {
        "schema_version": "b10-backoff-shape-provenance/v1",
        "official_certification": False,
        "space_version": SPACE_VERSION,
        "pin": PIN,
        "preregistration": {
            "path": prereg.path,
            **prereg.binding.as_dict(),
            "minimum_abort_calls": prereg.minimum_abort_calls,
            "physical_residual_measurement": prereg.spec.physical_residual_measurement,
            "maximum_absolute_deviation_pct_exclusive": (
                prereg.maximum_absolute_deviation_pct_exclusive
            ),
            "physical_residual_values": [
                {
                    "shape": shape,
                    "mean_us": mean_us,
                    "realized_mean_cycles": realized,
                    "commanded_mean_cycles": commanded,
                    "deviation_pct": deviation,
                }
                for shape, mean_us, realized, commanded, deviation
                in prereg.spec.physical_residual_values
            ],
            "equivalence_margin_pct": prereg.equivalence_margin_pct,
            "spec": prereg.spec.as_dict(),
        },
        "submission": dict(vars(submission)),
        "calibration": calibration.as_dict(),
        "formula": EXPECTED_HOLE_LINE,
        "formula_sha256": FORMULA_SHA256,
        "block_run_order": {
            block: list(order) for block, order in prereg.spec.block_orders
        },
        "external_floor_reference_widths": {
            "terminology": prereg.spec.reference_width_terminology,
            "power_guarantee": prereg.spec.reference_width_power_guarantee,
            "values": [
                {
                    "workload": workload,
                    "between_run_cv_pct": cv,
                    "reference_width_pct": width,
                    "source_environment": source,
                }
                for workload, cv, width, source in prereg.spec.reference_widths
            ],
        },
        "applied_tree": dict(applied_evidence),
        "records": list(records),
        "judgement": verdict,
    }
    report_root.mkdir(parents=True, exist_ok=False)
    json_path = report_root / "b10_backoff_shape_provenance.json"
    with json_path.open("x", encoding="utf-8") as stream:
        json.dump(provenance, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")

    lines = [
        "# B-10 backoff shape report", "",
        "- official certification: `false`",
        f"- preregistration binding: `{prereg.binding.binding_sha256}`",
        f"- preregistration spec SHA-256: `{prereg.spec.spec_sha256}`",
        f"- analysis code: `{prereg.binding.analysis_commit}` / `{prereg.binding.analysis_code_sha256}`",
        f"- submission request: `{submission.request_id}` (`{submission.receipt_sha256}`)",
        f"- records: `{calibration.records}` (calibration artifact)",
        f"- exposure minimum: `{prereg.minimum_abort_calls}` abort/backoff calls per cell", "",
        "Formal driver 経路について、登録前に性能を見ていないという限定主張だけを行う。", "",
        "| workload | block | point | shape | mean us | median tps | CV | abort rate | abort count | backoff calls | calls/s | nominal total wait us | correctness certified | unstable | exposure |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in sorted(
        records,
        key=lambda item: (
            str(item.get("workload")), str(item.get("block_id")),
            int(item.get("schedule_index", 0)),
        ),
    ):
        abort_count = row.get("abort_count")
        backoff_calls = row.get("backoff_call_count")
        exposed = (
            type(backoff_calls) is int
            and backoff_calls >= prereg.minimum_abort_calls
        )
        lines.append(
            "| {workload} | {block_id} | {point} | {shape} | {mean} | {tps} | {cv} | "
            "{abort_rate} | {abort_count} | {backoff_calls} | {calls} | {wait} | {certified} | {unstable} | {exposure} |".format(
                workload=row.get("workload"), block_id=row.get("block_id"),
                point=row.get("point"), shape=row.get("shape") or "—",
                mean=row.get("mean_us") if row.get("mean_us") is not None else "—",
                tps=f"{float(row['median_tps']):.0f}" if row.get("median_tps") is not None else "—",
                cv=f"{float(row['cv']):.4f}" if row.get("cv") is not None else "—",
                abort_rate=f"{float(row['abort_rate']):.4f}" if row.get("abort_rate") is not None else "—",
                abort_count=abort_count if abort_count is not None else "—",
                backoff_calls=backoff_calls if backoff_calls is not None else "—",
                calls=f"{float(row['backoff_calls_per_second']):.2f}" if row.get("backoff_calls_per_second") is not None else "—",
                wait=row.get("nominal_total_wait_us") if row.get("nominal_total_wait_us") is not None else "—",
                certified="yes" if row.get("correctness_certified") is True else "no",
                unstable="yes" if row.get("unstable") is True else "no",
                exposure="met" if exposed else "indeterminate",
            )
        )
    lines.extend(["", "## Paired sign-flip permutation + Holm", ""])
    for family in verdict["families"]:
        lines.append(
            f"- {family['workload']} / {family['shape']}: outcome={family['outcome']}, "
            f"pairs={family['pairs']}, raw_p={family['raw_p']:.8g}, "
            f"holm_p={family['holm_p']:.8g}"
        )
    lines.extend(["", "## Cell effects and 95% paired-block intervals", ""])
    for cell in verdict["cell_effects"]:
        lines.append(
            f"- {cell['workload']} / {cell['shape']} / mu={cell['mean_us']}: "
            f"effect={cell['effect']!r}, CI=[{cell['ci95_low']!r}, {cell['ci95_high']!r}], "
            f"status={cell['status']}, equivalence={cell['equivalence_relation']}"
        )
    lines.extend(["", "## External-floor-derived reference widths", ""])
    for workload, cv, width, source in prereg.spec.reference_widths:
        lines.append(
            f"- {workload}: reference width={width:.4g}% (between-run CV={cv:.4g}%, "
            f"source={source}); this is not a power guarantee."
        )
    lines.extend([
        "",
        "Non-significance means only that this registered design did not detect a difference; "
        "it is not a claim of guaranteed detection power.",
    ])
    md_path = report_root / f"b10_backoff_shape_report_{submission.trial}.md"
    with md_path.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return json_path, md_path


def run_probe(
    *,
    prereg_commit: str,
    submission_receipt: str | os.PathLike[str],
) -> Path:
    """Measure the applied wait loop without starting a performance campaign."""
    from .patchharness import applied, assert_pinned_clean, checkout

    pipeline._require_measurement_site("B10 backoff-shape realized-wait probe")
    _site, contract, _authorization = p2_2.resolve_site_runtime()
    if contract.env_tag != ENV_TAG or contract.attestation_mode != "required":
        raise PreflightError("site", "B10 probe は registered Pegasus compute contract 専用")
    root = _repo_root()
    submission = load_submission_identity(
        root, submission_receipt,
        prereg_commit=prereg_commit, phase="probe", workload=None,
    )
    status = str(_git(root, "status", "--porcelain", "--untracked-files=all"))
    if status:
        raise PreflightError("dirty", "repository working tree が dirty")
    patch_path = root / PATCH_REL
    try:
        patch_bytes = patch_path.read_bytes()
        committed_patch = _git(
            root, "show", f"{submission.source_commit}:{PATCH_REL}", binary=True,
        )
    except (OSError, PreflightError) as exc:
        raise PreflightError("patch-sha", "probe patch を source commit へ束縛できない") from exc
    if patch_bytes != committed_patch:
        raise PreflightError("patch-sha", "probe patch が source commit blob と不一致")
    patch_sha256 = _sha256_bytes(patch_bytes)
    validate_patch_bytes(patch_bytes, patch_sha256)
    p2_2._assert_single_tenant()
    ccbench_base = root / "external" / "ccbench"
    assert_pinned_clean(os.fspath(ccbench_base), PIN)
    _resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    with checkout(PIN, base_dir=os.fspath(ccbench_base)) as sub:
        with applied(os.fspath(patch_path), PIN, sub):
            hole_line, compile_options_sha256 = _extract_applied_probe_contract(sub)
            with tempfile.TemporaryDirectory(prefix="izanagi_b10_probe_build_") as temp:
                binaries, compile_info = _compile_probe_harnesses(
                    sub, Path(temp), hole_line=hole_line,
                    compile_options_sha256=compile_options_sha256,
                    cxx=resolved_cxx,
                )
                cells = []
                for mean_us in MEANS_US:
                    for shape, _code in SHAPES:
                        samples = _measure_probe_binary(
                            binaries[(shape, mean_us)],
                            clocks_per_us=contract.clocks_per_us,
                            calls=PROBE_CALLS_PER_CELL,
                        )
                        cells.append(_summarize_probe_cell(
                            shape, mean_us, samples,
                            clocks_per_us=contract.clocks_per_us,
                        ))
    measured_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    result = {
        "schema_version": PROBE_SCHEMA,
        "source_commit": submission.source_commit,
        "patch_sha256": patch_sha256,
        "formula_sha256": _sha256_bytes(hole_line.encode("utf-8")),
        "clocks_per_us": contract.clocks_per_us,
        "host": {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "machine": platform.machine(),
        },
        "measured_at_utc": measured_at,
        "calls_per_cell": PROBE_CALLS_PER_CELL,
        "compile": compile_info,
        "cells": cells,
        "shape_differences_from_constant": _shape_differences(cells),
        "submission": {
            "request_id": submission.request_id,
            "nonce": submission.nonce,
            "receipt_path": submission.receipt_path,
            "receipt_sha256": submission.receipt_sha256,
        },
    }
    output_path = Path(submission.receipt_path).parent / "probe-result.json"
    _write_probe_result_create_only(output_path, result)
    return output_path


def run_formal(
    *,
    phase: str,
    workload: Optional[str],
    prereg_commit: str,
    submission_receipt: str | os.PathLike[str],
    log=print,
) -> tuple[Optional[Path], Optional[Path], bool]:
    """Run one closed B10 phase in one compute allocation."""
    from .patchharness import applied, assert_pinned_clean, checkout

    if phase not in RUN_PHASES:
        raise PreflightError("phase", "phase は build/verify/perf/probe の閉集合が必要")
    if phase in {"build", "probe"}:
        if workload is not None:
            raise PreflightError("phase", "build/probe phase に workload を指定してはならない")
    elif workload not in WORKLOADS:
        raise PreflightError("phase", "verify/perf phase は workload 指定が必要")
    if phase == "probe":
        return run_probe(
            prereg_commit=prereg_commit,
            submission_receipt=submission_receipt,
        ), None, True
    root = _repo_root()
    prereg = load_preregistration(root, prereg_commit)
    submission = load_submission_identity(
        root, submission_receipt,
        prereg_commit=prereg_commit, phase=phase, workload=workload,
    )
    patch_path = root / PATCH_REL
    patch_bytes = patch_path.read_bytes()
    validate_patch_bytes(patch_bytes, prereg.binding.patch_sha256)

    pipeline._require_measurement_site("B10 formal campaign")
    _site, contract, authorization = p2_2.resolve_site_runtime()
    if contract.env_tag != ENV_TAG or contract.attestation_mode != "required":
        raise PreflightError("site", "B10 formal run は registered Pegasus compute contract 専用")
    calibration, _verified_calibration = load_calibration(contract, prereg.spec)
    validate_runtime_physical_residual(prereg.spec, calibration.clocks_per_us)
    p2_2._assert_single_tenant()
    ccbench_base = root / "external" / "ccbench"
    assert_pinned_clean(os.fspath(ccbench_base), PIN)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    toolchain_manifest = buildcache.observed_toolchain_manifest(resolved_cc, resolved_cxx)

    with checkout(PIN, base_dir=os.fspath(ccbench_base)) as sub:
        with applied(os.fspath(patch_path), PIN, sub):
            applied_evidence = validate_applied_tree(
                sub,
                patch_bytes=patch_bytes,
                patch_sha256=prereg.binding.patch_sha256,
                cxx=resolved_cxx,
            )
            cache_root = os.fspath(ccbench_base / "build-variants")
            context = build_run_context(
                generator_id=GeneratorId.BACKOFF_SWEEP,
            )
            build_kwargs = {
                "sub": sub,
                "cache_root": cache_root,
                "contract": contract,
                "build_context": context,
                "binding": prereg.binding,
                "toolchain_manifest": toolchain_manifest,
            }

            if phase == "build":
                for _name, genome in named_genomes():
                    _build_binary(genome, trace=True, **build_kwargs)
                    _build_binary(genome, trace=False, **build_kwargs)
                return None, None, True

            assert workload is not None
            cfg = config_for(workload, prereg, calibration, context, contract)
            layout = campaign_layout(str(ident.campaign_id(cfg)))
            assert_resumable_binding(layout, prereg.binding)
            perf = perf_for(workload, calibration, prereg.spec)
            if phase == "verify":
                with bind_build_start_wal(prereg.binding):
                    summary = run_campaign(
                        cfg, genomes(), perf, contract.env_tag, contract.clocks_per_us,
                        numactl=contract.numactl, do_bench=False, log=log,
                        ccbench_dir=sub, cache_root=cache_root, env_contract=contract,
                        expected_toolchain_manifest=toolchain_manifest,
                        authorization_contract=authorization,
                        build_context=context,
                        capability_resolver=_formula_generator_resolver(
                            context, prereg.binding,
                        ),
                        declared_use_class="official",
                    )
                if summary.committed + summary.skipped + summary.aborted \
                        != POINTS_PER_BLOCK:
                    raise RuntimeError(
                        f"correctness campaign incomplete: workload={workload} "
                        f"committed={summary.committed} skipped={summary.skipped} aborted={summary.aborted}"
                    )
                return None, None, summary.aborted == 0

            if not os.path.lexists(layout.lock_file) or not os.path.lexists(layout.wal_file):
                raise PreflightError("resume-binding", "perf phase 前に verify WAL/lock が無い")
            attempts = _certification_attempts(layout, context)
            named = dict(named_genomes())
            block_root = Path(layout.runs_dir) / "b10-backoff-shape-blocks"
            prior = _read_block_records(block_root)
            completed = _validate_prior_block_records(
                prior, workload=workload, prereg=prereg,
            )
            binaries: dict[
                str,
                tuple[
                    Optional[str], str, Optional[str], Optional[str],
                    Optional[CertificationAttempt],
                ],
            ] = {}
            for name, genome in named.items():
                evidence = source_digest.resolve_evidence(
                    genome, PIN, ccbench_dir=sub, cxx=resolved_cxx,
                )
                vid = variant_id(genome, evidence.src_token)
                certified = attempts.get(vid)
                if certified is None:
                    binaries[name] = (
                        None, vid, None, "correctness-not-certified", None,
                    )
                    continue
                try:
                    binary, built_vid, built_sha = _perf_binary(genome, **build_kwargs)
                    if built_vid != vid:
                        raise RuntimeError("performance binary variant identity drift")
                    binaries[name] = (binary, vid, built_sha, None, certified)
                except Exception as exc:  # one cell becomes explicit missing evidence
                    binaries[name] = (
                        None, vid, None,
                        f"performance-binary-unavailable:{type(exc).__name__}:{exc}",
                        certified,
                    )

            perf_probe_receipt, use_perf = p2_2_loop_perf_preflight()
            first_cell = not prior
            for block_id, order in prereg.spec.block_orders:
                for schedule_index, name in enumerate(order):
                    if (block_id, name) in completed:
                        continue
                    binary, vid, built_sha, unavailable, certified = binaries[name]
                    performance_binary_sha256 = None
                    if binary is None or built_sha is None or certified is None:
                        measured = _unavailable_measurement(unavailable or "unavailable")
                    else:
                        try:
                            performance_binary_sha256 = verify_performance_binary(
                                binary, built_sha, certified,
                            )
                            measured = measure_performance_cell(
                                binary, perf,
                                clocks_per_us=contract.clocks_per_us,
                                numactl=contract.numactl,
                                use_perf=use_perf,
                                do_settle=first_cell,
                            )
                            first_cell = False
                        except Exception as exc:
                            measured = _unavailable_measurement(
                                f"performance-measurement-failed:{type(exc).__name__}:{exc}",
                            )
                    shape, mean_us, encoded = _name_metadata(name)
                    row = {
                        "schema_version": "b10-backoff-shape-block/v2",
                        "official_certification": False,
                        "workload": workload,
                        "block_id": block_id,
                        "schedule_index": schedule_index,
                        "point": name,
                        "shape": shape,
                        "mean_us": mean_us,
                        "encoded": encoded,
                        "genome": named[name].canonical(),
                        "variant_id": vid,
                        "correctness_certified": certified is not None,
                        "build_attempt_id": (
                            None if certified is None else certified.attempt_id
                        ),
                        "performance_binary_sha256": performance_binary_sha256,
                        "source_commit": submission.source_commit,
                        "trial": submission.trial,
                        "submission_receipt": submission.receipt_path,
                        "submission_receipt_sha256": submission.receipt_sha256,
                        "request_id": submission.request_id,
                        "submission_nonce": submission.nonce,
                        "job_script_sha256": submission.job_script_sha256,
                        "preregistration_binding": prereg.binding.as_dict(),
                        "spec_sha256": prereg.spec.spec_sha256,
                        "analysis_commit": prereg.binding.analysis_commit,
                        "analysis_code_sha256": prereg.binding.analysis_code_sha256,
                        "perf_preflight_receipt": perf_probe_receipt,
                        **measured,
                    }
                    if name == "none" and row["abort_count"] is not None:
                        row["backoff_call_count"] = 0
                        row["backoff_calls_per_second"] = 0.0
                    row["nominal_total_wait_us"] = (
                        None if row["backoff_call_count"] is None else
                        _nominal_wait(int(row["backoff_call_count"]), mean_us)
                    )
                    record_path = block_root / _block_record_filename(
                        block_id, schedule_index, name,
                    )
                    _write_block_record_create_only(record_path, row)

            all_records: list[dict[str, object]] = []
            for other_workload in prereg.spec.workload_map:
                other_cfg = config_for(
                    other_workload, prereg, calibration, context, contract,
                )
                other_layout = campaign_layout(str(ident.campaign_id(other_cfg)))
                other_root = Path(other_layout.runs_dir) / "b10-backoff-shape-blocks"
                if not other_root.exists():
                    continue
                assert_resumable_binding(other_layout, prereg.binding)
                other_records = _read_block_records(other_root)
                _validate_prior_block_records(
                    other_records, workload=other_workload, prereg=prereg,
                )
                all_records.extend(other_records)
            report_root = (
                root / "output" / "env" / ENV_TAG / "b10-backoff-shape"
                / prereg.binding.binding_sha256[:16] / "reports" / submission.trial
            )
            json_path, markdown_path = _write_reports(
                report_root,
                prereg=prereg,
                calibration=calibration,
                records=all_records,
                applied_evidence=applied_evidence,
                submission=submission,
            )
            current_records = [
                row for row in all_records if row.get("workload") == workload
            ]
            execution_complete = all(
                row.get("correctness_certified") is True
                and row.get("performance_binary_sha256") is not None
                and row.get("missing") is False
                for row in current_records
            ) and len(current_records) \
                == len(prereg.spec.block_ids) * POINTS_PER_BLOCK
            return json_path, markdown_path, execution_complete


def p2_2_loop_perf_preflight() -> tuple[dict, bool]:
    """Use the same perf availability decision as campaign.loop."""
    from . import loop

    return loop._perform_perf_preflight(loop._perf_preflight.probe_perf_availability)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=RUN_PHASES)
    parser.add_argument("--workload", choices=tuple(WORKLOADS))
    parser.add_argument("--prereg-commit", required=True)
    parser.add_argument("--submission-receipt", required=True)
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    json_path, markdown_path, execution_complete = run_formal(
        phase=args.phase,
        workload=args.workload,
        prereg_commit=args.prereg_commit,
        submission_receipt=args.submission_receipt,
    )
    if args.phase == "probe" and json_path is not None:
        print(f"probe: {json_path}")
    elif json_path is not None:
        print(f"provenance: {json_path}")
    if markdown_path is not None:
        print(f"report: {markdown_path}")
    return 0 if execution_complete else 1


if __name__ == "__main__":
    sys.exit(main())
