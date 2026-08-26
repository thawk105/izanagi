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
import hashlib
import json
import math
import os
import re
import statistics
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
from .model import CampaignConfig, Genome, STAGE_BUILD_START, STAGE_COMMIT  # noqa: E402
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
SOURCE_REL = "include/backoff.hh"
OPTIONS_REL = "cmake/Options.cmake"
PREREG_REL = "docs/b10-backoff-shape-preregistration.md"
MARKER_ID = "silo-backoff-magnitude"
EXPECTED_PATCH_PATHS = frozenset({OPTIONS_REL, SOURCE_REL})
MEANS_US = (2, 5, 10, 25, 50, 100)
SHAPES = (("constant", 0), ("symmetric-modulo", 1), ("binary", 2))
SHAPE_CODES = {name: code for name, code in SHAPES}
SHAPE_NAMES = {code: name for name, code in SHAPES}
BLOCK_IDS = ("block-1", "block-2", "block-3")
THREADS = 48
EXTIME = 3
REPS = 5
ALPHA = 0.05
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

# Full applied Options.cmake and applied backoff.hh-with-hole-replaced hashes.
# They pin every byte outside the one authorized source line.  Values are
# filled from the reviewed patch below and independently exercised by tests.
EXPECTED_OPTIONS_SHA256 = "abaf00fa96db1de6db20e8c6314f8b32328820c3a35f1be576b48a16d06a06fa"
EXPECTED_BACKOFF_FRAME_SHA256 = "761b75102b65f407b326efe011bb4bc38064e1fa393383eff7266b0844e8212e"
_FRAME_SENTINEL = b"<IZANAGI-B10-AUTHORIZED-HOLE>"
B10_BUILD_START_BINDING_KEY = "b10_preregistration_binding"
_WAL_BINDING_LOCK = threading.Lock()

_PREREG_FIELD_RE = re.compile(
    r"^(b10_patch_sha256|b10_formula_sha256|b10_minimum_abort_calls|"
    r"b10_expression_eval_p99_cycles|b10_physical_residual_upper_pct|"
    r"b10_equivalence_margin_pct):[ \t]*"
    r"([^\r\n]+)[ \t]*$",
    re.MULTILINE,
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
    patch_sha256: str
    formula_sha256: str

    def core(self) -> dict[str, str]:
        return {
            "prereg_commit": self.prereg_commit,
            "prereg_blob_sha": self.prereg_blob_sha,
            "patch_sha256": self.patch_sha256,
            "formula_sha256": self.formula_sha256,
        }

    @property
    def binding_sha256(self) -> str:
        return _sha256_json(self.core())

    def as_dict(self) -> dict[str, str]:
        return {**self.core(), "binding_sha256": self.binding_sha256}


@dataclass(frozen=True)
class Preregistration:
    binding: PreregistrationBinding
    path: str
    minimum_abort_calls: int
    expression_eval_p99_cycles: int = 1
    physical_residual_upper_pct: float = 0.999
    equivalence_margin_pct: float = 3.0


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
    if len(points) != 21 or len({genome.canonical() for _name, genome in points}) != 21:
        raise AssertionError("B10 genome grid must contain exactly 21 unique points")
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
    if len(order) != 21 or set(order) != {name for name, _genome in named_genomes()}:
        raise AssertionError("B10 block order must be a permutation of all 21 points")
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


def parse_preregistration(raw: bytes) -> tuple[str, str, int, int, float, float]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError("prereg-blob", "事前登録文書が UTF-8 でない") from exc
    pairs = _PREREG_FIELD_RE.findall(text)
    values: dict[str, str] = {}
    for key, raw_value in pairs:
        value = raw_value.strip().strip("`")
        if key in values:
            raise PreflightError("prereg-fields", f"事前登録 field が重複: {key}")
        values[key] = value
    expected = {
        "b10_patch_sha256", "b10_formula_sha256", "b10_minimum_abort_calls",
        "b10_expression_eval_p99_cycles", "b10_physical_residual_upper_pct",
        "b10_equivalence_margin_pct",
    }
    if set(values) != expected:
        raise PreflightError(
            "prereg-fields", f"事前登録 machine fields が不足/余分: {sorted(values)!r}",
        )
    patch_sha = values["b10_patch_sha256"]
    formula_sha = values["b10_formula_sha256"]
    if _SHA256_RE.fullmatch(patch_sha) is None or _SHA256_RE.fullmatch(formula_sha) is None:
        raise PreflightError("prereg-fields", "事前登録 SHA-256 field の形式が不正")
    exposure_text = values["b10_minimum_abort_calls"]
    if re.fullmatch(r"[1-9][0-9]*", exposure_text) is None:
        raise PreflightError("prereg-fields", "minimum abort calls は正整数でなければならない")
    cycle_text = values["b10_expression_eval_p99_cycles"]
    if re.fullmatch(r"[1-9][0-9]*", cycle_text) is None:
        raise PreflightError("prereg-fields", "expression p99 cycles は正整数でなければならない")
    try:
        residual = float(values["b10_physical_residual_upper_pct"])
        equivalence = float(values["b10_equivalence_margin_pct"])
    except ValueError as exc:
        raise PreflightError("prereg-fields", "residual/equivalence が数値でない") from exc
    if not math.isfinite(residual) or not 0 < residual < 1.0:
        raise PreflightError("prereg-fields", "physical residual upper bound は 0% 超 1% 未満が必要")
    if not math.isfinite(equivalence) or not 0 < equivalence < 100:
        raise PreflightError("prereg-fields", "equivalence margin は 0% 超 100% 未満が必要")
    return (
        patch_sha, formula_sha, int(exposure_text), int(cycle_text),
        residual, equivalence,
    )


def load_preregistration(
    repo_root: str | os.PathLike[str],
    prereg_path: str | os.PathLike[str],
    prereg_commit: str,
) -> Preregistration:
    root = Path(repo_root).resolve()
    path = Path(prereg_path)
    if not path.is_absolute():
        path = root / path
    try:
        path = path.resolve(strict=True)
        relative = path.relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise PreflightError("prereg-missing", "事前登録文書が無いか repo 外である") from exc
    if path.is_symlink() or not path.is_file():
        raise PreflightError("prereg-missing", "事前登録文書が regular file でない")
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
    (
        patch_sha, formula_sha, minimum_abort_calls, expression_eval_p99_cycles,
        physical_residual_upper_pct, equivalence_margin_pct,
    ) = parse_preregistration(raw)
    if formula_sha != FORMULA_SHA256:
        raise PreflightError("formula-sha", "事前登録した式 SHA が EXPECTED_HOLE_LINE と不一致")
    patch_path = root / PATCH_REL
    try:
        patch_bytes = patch_path.read_bytes()
        committed_patch = _git(root, "show", f"{prereg_commit}:{PATCH_REL}", binary=True)
    except (OSError, PreflightError) as exc:
        raise PreflightError("patch-sha", "patch を現在/事前登録 commit から読めない") from exc
    if patch_bytes != committed_patch:
        raise PreflightError("patch-sha", "current patch bytes が prereg_commit blob と不一致")
    validate_patch_bytes(patch_bytes, patch_sha)
    binding = PreregistrationBinding(
        prereg_commit=prereg_commit,
        prereg_blob_sha=blob_sha,
        patch_sha256=patch_sha,
        formula_sha256=formula_sha,
    )
    return Preregistration(
        binding=binding, path=relative, minimum_abort_calls=minimum_abort_calls,
        expression_eval_p99_cycles=expression_eval_p99_cycles,
        physical_residual_upper_pct=physical_residual_upper_pct,
        equivalence_margin_pct=equivalence_margin_pct,
    )


def load_calibration(
    contract: env_contract.ExecutionEnvironmentContract,
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
    if threads != THREADS or env_tag != contract.env_tag \
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
    if workload_tag not in WORKLOADS:
        raise ValueError(f"未知 workload: {workload_tag!r}")
    search_config = {
        "scale": "silo-b10-backoff-shape",
        "space_version": SPACE_VERSION,
        "workload": workload_tag,
        "ycsb": WORKLOADS[workload_tag],
        "means_us": list(MEANS_US),
        "shape_codes": dict(SHAPES),
        "references": [name for name, _genome in reference_genomes()],
        "blocks": list(BLOCK_IDS),
        "block_run_order": {block: list(block_run_order(block)) for block in BLOCK_IDS},
        "records": calibration.records,
        "threads": THREADS,
        "extime": EXTIME,
        "reps": REPS,
        "calibration": calibration.as_dict(),
        "preregistration_path": prereg.path,
        "preregistration_binding": prereg.binding.as_dict(),
        "minimum_abort_calls": prereg.minimum_abort_calls,
        "expression_eval_p99_cycles": prereg.expression_eval_p99_cycles,
        "physical_residual_upper_pct": prereg.physical_residual_upper_pct,
        "decision": {
            "version": "paired-sign-flip-holm/v1",
            "pairs_per_family": 18,
            "family_size": 6,
            "alpha": ALPHA,
            "indeterminate_pvalue": 1.0,
            "equivalence_margin_pct": prereg.equivalence_margin_pct,
        },
        SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_PERFORMANCE,
    }
    cfg = CampaignConfig(
        spec_slug=f"b10-backoff-shape-silo-{workload_tag}",
        search_tag="formal",
        spec_content=(
            "B-10 registered equal-target-mean backoff-shape comparison; "
            "21 genomes, three independent paired blocks, no screening; "
            f"workload={workload_tag}"
        ),
        ccbench_commit=PIN,
        search_config=search_config,
        trial=TRIAL,
    )
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    return ident.bind_environment_contract(cfg, contract)


def perf_for(workload_tag: str, calibration: CalibrationSelection) -> PerfConfig:
    return PerfConfig(
        records=calibration.records,
        threads=THREADS,
        workload=dict(WORKLOADS[workload_tag]),
        extime=EXTIME,
        reps=REPS,
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
    """Add the four explicit preregistration values to every BUILD_START.

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


def _record_usable(record: Mapping[str, object], minimum_abort_calls: int) -> bool:
    return (
        record.get("certified") is True
        and record.get("unstable") is False
        and type(record.get("median_tps")) in {int, float}
        and math.isfinite(float(record["median_tps"]))
        and float(record["median_tps"]) > 0
        and type(record.get("backoff_call_count")) is int
        and not isinstance(record.get("backoff_call_count"), bool)
        and int(record["backoff_call_count"]) >= minimum_abort_calls
        and record.get("missing") is False
    )


def _paired_effect(shape: Mapping[str, object], constant: Mapping[str, object]) -> float:
    return float(shape["median_tps"]) / float(constant["median_tps"]) - 1.0


def cell_effects(
    records: Sequence[Mapping[str, object]], minimum_abort_calls: int,
    equivalence_margin_pct: float = 3.0,
) -> list[dict[str, object]]:
    if not math.isfinite(equivalence_margin_pct) or not 0 < equivalence_margin_pct < 100:
        raise ValueError("equivalence_margin_pct must be finite and in (0,100)")
    equivalence_margin = equivalence_margin_pct / 100.0
    indexed = {
        (row.get("workload"), row.get("block_id"), row.get("shape"), row.get("mean_us")): row
        for row in records
        if row.get("shape") in SHAPE_CODES and row.get("mean_us") in MEANS_US
    }
    output = []
    t_critical_df2 = 4.302652729911275
    for workload in WORKLOADS:
        for shape, _code in SHAPES:
            for mean_us in MEANS_US:
                effects = []
                usable = True
                for block_id in BLOCK_IDS:
                    row = indexed.get((workload, block_id, shape, mean_us))
                    constant = indexed.get((workload, block_id, "constant", mean_us))
                    if row is None or constant is None \
                            or not _record_usable(row, minimum_abort_calls) \
                            or not _record_usable(constant, minimum_abort_calls):
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
                        half = t_critical_df2 * statistics.stdev(effects) / math.sqrt(3)
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
    records: Sequence[Mapping[str, object]], minimum_abort_calls: int,
    equivalence_margin_pct: float = 3.0,
) -> dict[str, object]:
    if type(minimum_abort_calls) is not int or minimum_abort_calls <= 0:
        raise ValueError("minimum_abort_calls must be a positive exact integer")
    indexed = {
        (row.get("workload"), row.get("block_id"), row.get("shape"), row.get("mean_us")): row
        for row in records
    }
    raw: dict[tuple[str, str], float] = {}
    family_data: dict[tuple[str, str], dict[str, object]] = {}
    for workload in WORKLOADS:
        for shape in ("symmetric-modulo", "binary"):
            key = (workload, shape)
            differences = []
            reasons = []
            for block_id in BLOCK_IDS:
                for mean_us in MEANS_US:
                    row = indexed.get((workload, block_id, shape, mean_us))
                    constant = indexed.get((workload, block_id, "constant", mean_us))
                    if row is None or constant is None:
                        reasons.append(f"missing:{block_id}:mu{mean_us}")
                    elif not _record_usable(row, minimum_abort_calls) \
                            or not _record_usable(constant, minimum_abort_calls):
                        reasons.append(f"unusable-or-underexposed:{block_id}:mu{mean_us}")
                    else:
                        differences.append(_paired_effect(row, constant))
            complete = len(differences) == 18 and not reasons
            pvalue = sign_flip_permutation_pvalue(differences) if complete else 1.0
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
        elif adjusted[key] <= ALPHA:
            item["outcome"] = "different"
        else:
            item["outcome"] = "not-detected"
        families.append(item)
    return {
        "schema_version": "b10-backoff-shape-judgement/v1",
        "alpha": ALPHA,
        "families": families,
        "cell_effects": cell_effects(
            records, minimum_abort_calls, equivalence_margin_pct,
        ),
    }


def _count_metric(metrics: Mapping[str, str], key: str) -> int:
    value = benchparse._num(metrics.get(key))
    if value is None or not math.isfinite(value) or value < 0 or not float(value).is_integer():
        raise RuntimeError(f"performance output の {key} が一意な非負整数でない")
    return int(value)


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


def _append_jsonl_create_or_append(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (_canonical_json(value) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        written = os.write(descriptor, raw)
        if written != len(raw):
            raise OSError("short append")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows = []
    for line_number, raw in enumerate(path.read_bytes().splitlines(), start=1):
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PreflightError("measurement-wal", f"line {line_number} が不正") from exc
        if type(value) is not dict:
            raise PreflightError("measurement-wal", f"line {line_number} が object でない")
        rows.append(value)
    return rows


def _certification_attempts(
    layout: CampaignLayout, build_context: BuildRunContext,
) -> dict[str, str]:
    states = wal.replay(layout, admission_policy=build_context.policy)
    attempts: dict[str, str] = {}
    for variant, state in states.items():
        if not state.committed or state.last_terminal is None \
                or state.last_terminal.stage != STAGE_COMMIT:
            continue
        attempt = state.last_terminal.payload.get("build_attempt_id")
        if type(attempt) is str and attempt:
            attempts[variant] = attempt
    return attempts


def _formula_generator_resolver(
    context: BuildRunContext, binding: PreregistrationBinding,
):
    return lambda evidence: attest_generator_output(
        context, evidence, generator_input_sha256=binding.binding_sha256,
    )


def _perf_binary(
    genome: Genome,
    *,
    sub: str,
    cache_root: str,
    contract: env_contract.ExecutionEnvironmentContract,
    build_context: BuildRunContext,
    binding: PreregistrationBinding,
    toolchain_manifest: Mapping[str, object],
) -> tuple[str, str]:
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
        trace=False,
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
    return result.binary, variant_id(genome, evidence.src_token)


def _name_metadata(name: str) -> tuple[Optional[str], Optional[int], Optional[int]]:
    if name == "none":
        return None, None, None
    if name == "adaptive":
        return None, None, None
    if name == "zero-loop":
        return "constant", 0, 0
    match = re.fullmatch(r"(constant|symmetric-modulo|binary)-mu([0-9]+)", name)
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
) -> tuple[Path, Path]:
    verdict = judge(
        records, prereg.minimum_abort_calls, prereg.equivalence_margin_pct,
    )
    provenance = {
        "schema_version": "b10-backoff-shape-provenance/v1",
        "space_version": SPACE_VERSION,
        "pin": PIN,
        "preregistration": {
            "path": prereg.path,
            **prereg.binding.as_dict(),
            "minimum_abort_calls": prereg.minimum_abort_calls,
            "expression_eval_p99_cycles": prereg.expression_eval_p99_cycles,
            "physical_residual_upper_pct": prereg.physical_residual_upper_pct,
            "equivalence_margin_pct": prereg.equivalence_margin_pct,
        },
        "calibration": calibration.as_dict(),
        "formula": EXPECTED_HOLE_LINE,
        "formula_sha256": FORMULA_SHA256,
        "block_run_order": {block: list(block_run_order(block)) for block in BLOCK_IDS},
        "applied_tree": dict(applied_evidence),
        "records": list(records),
        "judgement": verdict,
    }
    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / "b10_backoff_shape_provenance.json"
    json_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# B-10 backoff shape report", "",
        f"- preregistration binding: `{prereg.binding.binding_sha256}`",
        f"- records: `{calibration.records}` (calibration artifact)",
        f"- exposure minimum: `{prereg.minimum_abort_calls}` abort/backoff calls per cell", "",
        "| workload | block | point | shape | mean us | median tps | CV | abort rate | abort count | backoff calls | calls/s | nominal total wait us | certified | unstable | exposure |",
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
                certified="yes" if row.get("certified") is True else "no",
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
    md_path = report_root / f"b10_backoff_shape_report_{TRIAL}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_formal(
    *,
    preregistration_path: str = PREREG_REL,
    prereg_commit: str,
    log=print,
) -> tuple[Path, Path, bool]:
    """Run all workloads and all three blocks in one compute allocation."""
    from .patchharness import applied, assert_pinned_clean, checkout

    root = _repo_root()
    prereg = load_preregistration(root, preregistration_path, prereg_commit)
    patch_path = root / PATCH_REL
    patch_bytes = patch_path.read_bytes()
    validate_patch_bytes(patch_bytes, prereg.binding.patch_sha256)

    pipeline._require_measurement_site("B10 formal campaign")
    _site, contract, authorization = p2_2.resolve_site_runtime()
    if contract.env_tag != ENV_TAG or contract.attestation_mode != "required":
        raise PreflightError("site", "B10 formal run は registered Pegasus compute contract 専用")
    calibration, _verified_calibration = load_calibration(contract)
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
            all_records: list[dict[str, object]] = []
            workload_runs = {}
            for workload_tag in WORKLOADS:
                context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
                cfg = config_for(workload_tag, prereg, calibration, context, contract)
                layout = campaign_layout(str(ident.campaign_id(cfg)))
                assert_resumable_binding(layout, prereg.binding)
                block_wal = Path(layout.root) / "reports" / "b10_backoff_shape_blocks.jsonl"
                prior = _read_jsonl(block_wal)
                if prior:
                    if any(
                        row.get("preregistration_binding") != prereg.binding.as_dict()
                        for row in prior
                    ):
                        raise PreflightError(
                            "resume-binding", "B10 block WAL の束縛が欠落/不一致",
                        )
                    raise PreflightError(
                        "resume-disabled", "Pegasus single-process campaign は resume 不可",
                    )
                workload_runs[workload_tag] = (
                    context, cfg, layout, block_wal, perf_for(workload_tag, calibration),
                )
            perf_probe_receipt, use_perf = p2_2_loop_perf_preflight()
            first_cell = True
            for workload_tag in WORKLOADS:
                context, cfg, layout, block_wal, perf = workload_runs[workload_tag]
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
                if summary.committed + summary.skipped + summary.aborted != 21:
                    raise RuntimeError(
                        f"correctness campaign incomplete: workload={workload_tag} "
                        f"committed={summary.committed} skipped={summary.skipped} aborted={summary.aborted}"
                    )
                attempts = _certification_attempts(layout, context)
                named = dict(named_genomes())
                binaries: dict[str, tuple[Optional[str], str, Optional[str]]] = {}
                for name, genome in named.items():
                    evidence = source_digest.resolve_evidence(
                        genome, PIN, ccbench_dir=sub, cxx=resolved_cxx,
                    )
                    vid = variant_id(genome, evidence.src_token)
                    if vid not in attempts:
                        binaries[name] = (None, vid, "correctness-not-certified")
                        continue
                    try:
                        binary, built_vid = _perf_binary(
                            genome, sub=sub, cache_root=cache_root, contract=contract,
                            build_context=context, binding=prereg.binding,
                            toolchain_manifest=toolchain_manifest,
                        )
                        if built_vid != vid:
                            raise RuntimeError("performance binary variant identity drift")
                        binaries[name] = (binary, vid, None)
                    except Exception as exc:  # one cell becomes explicit missing evidence
                        binaries[name] = (
                            None, vid, f"performance-binary-unavailable:{type(exc).__name__}:{exc}",
                        )
                for block_id in BLOCK_IDS:
                    for schedule_index, name in enumerate(block_run_order(block_id)):
                        binary, vid, unavailable = binaries[name]
                        if binary is None:
                            measured = _unavailable_measurement(unavailable or "unavailable")
                        else:
                            try:
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
                            "schema_version": "b10-backoff-shape-block/v1",
                            "workload": workload_tag,
                            "block_id": block_id,
                            "schedule_index": schedule_index,
                            "point": name,
                            "shape": shape,
                            "mean_us": mean_us,
                            "encoded": encoded,
                            "genome": named[name].canonical(),
                            "variant_id": vid,
                            "certification_attempt_id": attempts.get(vid),
                            "certified": vid in attempts,
                            "preregistration_binding": prereg.binding.as_dict(),
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
                        _append_jsonl_create_or_append(block_wal, row)
                        all_records.append(row)
            report_root = (
                root / "output" / "env" / ENV_TAG / "b10-backoff-shape"
                / prereg.binding.binding_sha256[:16] / "reports"
            )
            json_path, markdown_path = _write_reports(
                report_root,
                prereg=prereg,
                calibration=calibration,
                records=all_records,
                applied_evidence=applied_evidence,
            )
            execution_complete = all(
                row.get("certified") is True and row.get("missing") is False
                for row in all_records
            )
            return json_path, markdown_path, execution_complete


def p2_2_loop_perf_preflight() -> tuple[dict, bool]:
    """Use the same perf availability decision as campaign.loop."""
    from . import loop

    return loop._perform_perf_preflight(loop._perf_preflight.probe_perf_availability)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preregistration", default=PREREG_REL)
    parser.add_argument("--prereg-commit", required=True)
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    json_path, markdown_path, execution_complete = run_formal(
        preregistration_path=args.preregistration,
        prereg_commit=args.prereg_commit,
    )
    print(f"provenance: {json_path}")
    print(f"report: {markdown_path}")
    return 0 if execution_complete else 1


if __name__ == "__main__":
    sys.exit(main())
