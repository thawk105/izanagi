# -*- coding: utf-8 -*-
"""B-10: cover the complete static backoff range with a certified sweep."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import tempfile
from contextlib import contextmanager, nullcontext
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import (  # noqa: E402
    buildcache,
    ident,
    p2_2,
    patchharness,
    pin,
    pipeline as campaign_pipeline,
    source_digest,
    wal,
)
from .artifact_admission import (  # noqa: E402
    CampaignReadPurpose,
    require_certified_campaign_view,
)
from .backoff_sweep import (  # noqa: E402
    _BASE,
    _official_durable_root_policy,
    _require_backoff_condition_gate,
)
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from .loop import run_campaign  # noqa: E402
from .model import CampaignConfig, Genome  # noqa: E402
from .pipeline import PerfConfig  # noqa: E402
from .replay import discover_campaign_dir  # noqa: E402
from ..calibrator import perf_preflight, runner as calibrator_runner  # noqa: E402


EXTENDED_SWEEP_US = [
    0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 100,
    150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000,
]

STATIC_BACKOFF_MAX_US = 9999
STATIC_BACKOFF_RAW_MAX = 11999


def encode_static_backoff_us(backoff_us: int) -> int:
    """Encode one physical static-backoff value for BACKOFF_FIXED."""
    if type(backoff_us) is not int or not 0 <= backoff_us <= STATIC_BACKOFF_MAX_US:
        raise ValueError("static backoff_us must be an exact integer in [0, 9999]")
    return backoff_us if backoff_us <= 999 else backoff_us + 2000


def decode_static_backoff_us(encoded: int) -> int:
    """Decode one BACKOFF_FIXED value from the static-only wire domain."""
    if type(encoded) is not int or not 0 <= encoded <= STATIC_BACKOFF_RAW_MAX:
        raise ValueError("encoded static backoff must be an exact integer in [0, 11999]")
    if encoded <= 999:
        return encoded
    if encoded >= 3000:
        return encoded - 2000
    raise ValueError("encoded BACKOFF_FIXED value is not in the static wire domain")

EXTENDED_RUN_KIND = "extended"
T2266_RUN_KIND = "t2266-tail"
T2418_RUN_KIND = "t2418-explore"
RUN_KINDS = (EXTENDED_RUN_KIND, T2266_RUN_KIND, T2418_RUN_KIND)

T2266_REQUESTED_US = (150, 200, 300, 500, 750, 1000)
T2266_REALIZED_US = (150, 200, 300, 500, 750, 1000)
T2266_UNREALIZED: dict[int, str] = {}
T2266_REPORT_SCHEMA = "t2266-backoff-static-tail-report/v2"
T2266_CLAIM_SCOPE = "descriptive_backoff_shape_only"

T2418_REQUESTED_US = (2000, 4000, 9999)
T2418_REALIZED_US = (2000, 4000, 9999)
T2418_UNREALIZED: dict[int, str] = {}
T2418_REPORT_SCHEMA = "t2418-backoff-static-explore-report/v2"
T2418_CLAIM_SCOPE = "exploratory_backoff_tail_only_not_formal_series"
T2418_FORMAL_GRID_STATUS = "not_selected_in_this_wave"
T2418_FORMAL_STOPPING_CRITERION_STATUS = "not_defined_in_this_wave"
T2418_MEANING_WITNESS_STATUS = (
    "driver_declared_static_backoff_physical_us"
)

# The literals are an oracle independent of labels and of the legacy sweep.
WORKLOADS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
    ("read-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"}),
]
WORKLOAD_BY_TAG = dict(WORKLOADS)

# One reviewed seed per workload. The resulting order is part of campaign identity.
MEASUREMENT_SEEDS = {
    "write-heavy": 0xB10005,
    "balanced": 0xB10050,
    "read-heavy": 0xB10095,
}

PREFLIGHT_RECEIPT_SCHEMA = "b10-backoff-grid-perf-preflight-stop/v1"
TEMPLATE_PATCH = "patches/silo-backoff-fixed.patch"

_BACKOFF_FIXED_PATCH_MARKERS = {
    "cmake/Options.cmake": (
        "set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING",
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}",
    ),
    "include/backoff.hh": (
        "#ifndef BACKOFF_FIXED",
        "#if BACKOFF_FIXED >= 0",
    ),
}


class PreflightStop(RuntimeError):
    """The durable perf receipt proves that measurement cannot start."""


def _repo_root() -> str:
    return str(Path(__file__).resolve().parents[2])


def _git_worktree_output(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RuntimeError("provided CCBench worktree cannot be inspected") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no diagnostic"
        raise RuntimeError(
            "provided CCBench worktree failed git validation: "
            f"{' '.join(args)}: {detail}"
        )
    return completed.stdout.strip()


def _resolve_ccbench_dir(ccbench_dir: Optional[str]) -> str:
    """Use the legacy shared tree only when no explicit worktree was supplied."""
    if ccbench_dir is None:
        return buildcache._ccbench_dir()
    if type(ccbench_dir) is not str or not ccbench_dir:
        raise RuntimeError("provided CCBench worktree path is empty or non-string")
    candidate = Path(ccbench_dir)
    if candidate.is_symlink():
        raise RuntimeError("provided CCBench worktree path must not be a symlink")
    try:
        root = candidate.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("provided CCBench worktree does not exist") from exc
    if not root.is_dir():
        raise RuntimeError("provided CCBench worktree is not a directory")
    if _git_worktree_output(root, "rev-parse", "--is-inside-work-tree") != "true":
        raise RuntimeError("provided CCBench path is not a git worktree")
    try:
        top = Path(
            _git_worktree_output(root, "rev-parse", "--show-toplevel")
        ).resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("provided CCBench worktree root is not resolvable") from exc
    if top != root:
        raise RuntimeError("provided CCBench path is not the git worktree root")
    head = _git_worktree_output(root, "rev-parse", "--verify", "HEAD^{commit}")
    expected_head = _git_worktree_output(
        root, "rev-parse", "--verify", f"{pin.CURRENT_PIN}^{{commit}}",
    )
    if head != expected_head:
        raise RuntimeError(
            "provided CCBench worktree HEAD mismatch: "
            f"expected={expected_head}, actual={head}"
        )
    tracked_status = _git_worktree_output(
        root, "status", "--porcelain", "--untracked-files=no",
    )
    if tracked_status:
        raise RuntimeError("provided CCBench worktree has tracked modifications")
    return str(root)


def _assert_backoff_fixed_materialized(ccbench_dir: str) -> None:
    """Confirm the applied tree, rather than a discarded CMake staging tree."""
    root = Path(ccbench_dir)
    for relative, markers in _BACKOFF_FIXED_PATCH_MARKERS.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(
                f"BACKOFF_FIXED patch materialization is unreadable: {relative}"
            ) from exc
        missing = [marker for marker in markers if marker not in text]
        if missing:
            raise RuntimeError(
                f"BACKOFF_FIXED patch is not materialized in {relative}: {missing!r}"
            )


def _static_backoff_amount(genome: Genome) -> Optional[int]:
    amount = genome.flags.get("BACKOFF_FIXED")
    if genome.flags.get("BACK_OFF") != 1 or type(amount) is not int or amount < 0:
        return None
    return amount


def _require_distinct_static_binary_hashes(
        builds: dict[tuple[str, bool], buildcache.BuildResult],
) -> None:
    """Fail closed if two requested static magnitudes produced one perf binary."""
    amount_by_sha256: dict[str, int] = {}
    checked_amounts: set[int] = set()
    for (canonical, trace), built in builds.items():
        if trace:
            continue
        if type(built) is not buildcache.BuildResult:
            raise RuntimeError("static binary identity requires an exact BuildResult")
        amount = _static_backoff_amount(built.genome)
        if amount is None:
            continue
        if built.genome.canonical() != canonical:
            raise RuntimeError("prebuilt BACKOFF_FIXED binary lost its genome binding")
        sha256 = built.bin_sha256
        if not buildcache.is_full_sha256(sha256):
            raise RuntimeError(
                f"BACKOFF_FIXED={amount} build returned a non-canonical binary sha256"
            )
        previous = amount_by_sha256.setdefault(sha256, amount)
        if previous != amount:
            raise RuntimeError(
                "distinct BACKOFF_FIXED amounts produced the same binary: "
                f"{previous} and {amount} (sha256={sha256})"
            )
        checked_amounts.add(amount)
    if len(checked_amounts) >= 2 and len(amount_by_sha256) != len(checked_amounts):
        raise RuntimeError("BACKOFF_FIXED binary identity check is incomplete")


def _require_distinct_t2266_binary_hashes(
        builds: dict[tuple[str, bool], buildcache.BuildResult],
        ordered_genomes: Sequence[Genome],
) -> None:
    """Require a distinct trace-disabled binary for every T-2266 genome."""
    expected = {genome.canonical(): genome for genome in ordered_genomes}
    if len(ordered_genomes) != 8 or len(expected) != 8:
        raise RuntimeError("T-2266 binary identity requires exactly eight genomes")
    canonical_by_sha256: dict[str, str] = {}
    for canonical, genome in expected.items():
        built = builds.get((canonical, False))
        if type(built) is not buildcache.BuildResult:
            raise RuntimeError(
                "T-2266 binary identity requires every trace-disabled BuildResult"
            )
        if built.trace is not False or built.genome.canonical() != canonical:
            raise RuntimeError("prebuilt T-2266 binary lost its genome binding")
        sha256 = built.bin_sha256
        if not buildcache.is_full_sha256(sha256):
            raise RuntimeError(
                "T-2266 build returned a non-canonical binary sha256: "
                f"{canonical}"
            )
        previous = canonical_by_sha256.setdefault(sha256, canonical)
        if previous != canonical:
            raise RuntimeError(
                "distinct T-2266 genomes produced the same binary: "
                f"{previous} and {canonical} (sha256={sha256})"
            )
    if len(canonical_by_sha256) != 8:
        raise RuntimeError("T-2266 binary identity check is incomplete")


def _require_distinct_t2418_binary_hashes(
        builds: dict[tuple[str, bool], buildcache.BuildResult],
        ordered_genomes: Sequence[Genome],
) -> None:
    """Require a distinct trace-disabled binary for every T-2418 genome."""
    if len(ordered_genomes) != 5:
        raise RuntimeError("T-2418 binary identity requires exactly five genomes")
    canonical_by_sha256: dict[str, str] = {}
    for genome in ordered_genomes:
        canonical = genome.canonical()
        built = builds.get((canonical, False))
        if type(built) is not buildcache.BuildResult:
            raise RuntimeError(
                "T-2418 binary identity requires every trace-disabled BuildResult"
            )
        if built.trace is not False or built.genome.canonical() != canonical:
            raise RuntimeError("prebuilt T-2418 binary lost its genome binding")
        sha256 = built.bin_sha256
        if not buildcache.is_full_sha256(sha256):
            raise RuntimeError(
                "T-2418 build returned a non-canonical binary sha256: "
                f"{canonical}"
            )
        previous = canonical_by_sha256.setdefault(sha256, canonical)
        if previous != canonical:
            raise RuntimeError(
                "distinct T-2418 genomes produced the same binary: "
                f"{previous} and {canonical} (sha256={sha256})"
            )
    if len(canonical_by_sha256) != 5:
        raise RuntimeError("T-2418 binary identity check is incomplete")


def _prebuild_backoff_binaries(
        ordered_genomes: list[Genome], *, contract, cache_root: str,
        ccbench_dir: str, resolved_cc: str, resolved_cxx: str,
        expected_toolchain_manifest, build_context, capability_resolver,
        trace_modes: tuple[bool, ...] = (True, False),
        require_all_binary_hashes: bool = False,
        require_all_t2418_binary_hashes: bool = False,
) -> dict[tuple[str, bool], buildcache.BuildResult]:
    """Build every requested binary before measurement and check static identity."""
    builds: dict[tuple[str, bool], buildcache.BuildResult] = {}
    for genome in ordered_genomes:
        evidence = source_digest.resolve_evidence(
            genome,
            pin.CURRENT_PIN,
            ccbench_dir=ccbench_dir,
            cxx=resolved_cxx,
        )
        capability = capability_resolver(evidence)
        admission = derive_build_admission(
            build_context,
            evidence,
            generator_receipt=capability,
        )
        for trace in trace_modes:
            built = buildcache.build_v2(
                genome,
                contract=contract,
                ccbench_commit=pin.CURRENT_PIN,
                trace=trace,
                src_token=evidence.src_token,
                cc=resolved_cc,
                cxx=resolved_cxx,
                cache_root=cache_root,
                ccbench_dir=ccbench_dir,
                admission=admission,
                build_context=build_context,
                source_evidence=evidence,
                expected_toolchain_manifest=expected_toolchain_manifest,
                declared_use_class="official",
            )
            builds[(genome.canonical(), trace)] = built
    _require_distinct_static_binary_hashes(builds)
    if require_all_binary_hashes:
        _require_distinct_t2266_binary_hashes(builds, ordered_genomes)
    if require_all_t2418_binary_hashes:
        _require_distinct_t2418_binary_hashes(builds, ordered_genomes)
    return builds


def _write_create_only_json(path: Path, value: object) -> None:
    payload = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, payload) != len(payload):
            raise OSError("short preflight stop receipt write")
        os.fsync(fd)
    finally:
        os.close(fd)
    parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def _write_create_only_text(path: Path, text: str) -> None:
    payload = text.encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.write(fd, payload) != len(payload):
            raise OSError("short T-2266 report write")
        os.fsync(fd)
    finally:
        os.close(fd)
    parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def _materialize_preflight_stop(
        tag: str, output_root: str, receipt_path: Path, error: Exception) -> Path:
    receipt = perf_preflight.validate_perf_preflight_receipt(
        json.loads(receipt_path.read_text(encoding="utf-8"))
    )
    if receipt["status"] != "probe_error":
        raise RuntimeError("perf preflight exception lacks a probe_error receipt") from error
    stop_path = Path(output_root) / f"b10-backoff-grid-{tag}-preflight-stop.json"
    _write_create_only_json(stop_path, {
        "schema_version": PREFLIGHT_RECEIPT_SCHEMA,
        "status": "preflight-error-no-verdict",
        "workload": tag,
        "perf_preflight_receipt": {
            "filename": receipt_path.name,
            "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "status": receipt["status"],
            "reason": receipt["reason"],
        },
    })
    return stop_path


def _ordered_points(tag: str) -> list[tuple[str, dict[str, int]]]:
    if tag not in WORKLOAD_BY_TAG:
        raise ValueError(f"unknown workload: {tag!r}")
    points = [
        ("none", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("adaptive", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1}),
        *[
            (f"fixed-{amount}us", {
                **_BASE,
                "BACK_OFF": 1,
                "BACKOFF_FIXED": encode_static_backoff_us(amount),
            })
            for amount in EXTENDED_SWEEP_US
        ],
    ]
    random.Random(MEASUREMENT_SEEDS[tag]).shuffle(points)
    return points


def _t2266_points(tag: str) -> list[tuple[str, dict[str, int]]]:
    if tag not in WORKLOAD_BY_TAG:
        raise ValueError(f"unknown workload: {tag!r}")
    return [
        ("none", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("adaptive", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1}),
        *[
            (f"fixed-{amount}us", {
                **_BASE,
                "BACK_OFF": 1,
                "BACKOFF_FIXED": encode_static_backoff_us(amount),
            })
            for amount in T2266_REALIZED_US
        ],
    ]


def _t2266_ordered_points(tag: str) -> list[tuple[str, dict[str, int]]]:
    points = _t2266_points(tag)
    random.Random(MEASUREMENT_SEEDS[tag]).shuffle(points)
    return points


def _t2418_points(tag: str) -> list[tuple[str, dict[str, int]]]:
    if tag not in WORKLOAD_BY_TAG:
        raise ValueError(f"unknown workload: {tag!r}")
    return [
        ("none", {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}),
        ("adaptive", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1}),
        *[
            (f"fixed-{amount}us", {
                **_BASE,
                "BACK_OFF": 1,
                "BACKOFF_FIXED": encode_static_backoff_us(amount),
            })
            for amount in T2418_REALIZED_US
        ],
    ]


def _t2418_ordered_points(tag: str) -> list[tuple[str, dict[str, int]]]:
    points = _t2418_points(tag)
    random.Random(MEASUREMENT_SEEDS[tag]).shuffle(points)
    return points


def measurement_order(tag: str) -> list[str]:
    """Return the preregistered, deterministic label permutation."""
    return [label for label, _flags in _ordered_points(tag)]


def genomes(tag: str) -> list[Genome]:
    """Return all reference and static genomes in preregistered run order."""
    return [Genome("silo", flags) for _label, flags in _ordered_points(tag)]


def t2266_measurement_order(tag: str) -> list[str]:
    """Return the T-2266 preregistered, deterministic label permutation."""
    return [label for label, _flags in _t2266_ordered_points(tag)]


def t2266_genomes(tag: str) -> list[Genome]:
    """Return none, adaptive, and the six representable T-2266 static points."""
    return [Genome("silo", flags) for _label, flags in _t2266_ordered_points(tag)]


def t2418_measurement_order(tag: str) -> list[str]:
    """Return the T-2418 deterministic exploratory measurement permutation."""
    return [label for label, _flags in _t2418_ordered_points(tag)]


def t2418_genomes(tag: str) -> list[Genome]:
    """Return two context points and the three T-2418 exploratory points."""
    return [Genome("silo", flags) for _label, flags in _t2418_ordered_points(tag)]


def _require_condition_gate_before_measurement(
        source_root: str, *, stock_root: str, points: list[Genome], cxx: str,
        configure_args: Sequence[str] = (),
        physical_grid: Optional[Sequence[int]] = None,
):
    """Bind this driver's concrete BACKOFF_FIXED requests to the family gate."""
    raw_values = tuple(point.flags["BACKOFF_FIXED"] for point in points)
    if physical_grid is None:
        requested_nonnegative = {value for value in raw_values if value >= 0}
        physical_grid = tuple(
            amount
            for amount in dict.fromkeys((
                *EXTENDED_SWEEP_US,
                *T2266_REALIZED_US,
                *T2418_REALIZED_US,
            ))
            if encode_static_backoff_us(amount) in requested_nonnegative
        )
    return _require_backoff_condition_gate(
        source_root,
        stock_root=stock_root,
        driver_id="orchestrator/campaign/backoff_extended_sweep.py",
        macro_values={"BACKOFF_FIXED": raw_values},
        backoff_fixed_physical_us={
            encode_static_backoff_us(amount): amount
            for amount in physical_grid
        },
        cxx=cxx,
        use_class="raw-measurement",
        configure_args=configure_args,
    )


def config_for(tag: str, workload: dict[str, str], *, contract=None) -> CampaignConfig:
    expected = WORKLOAD_BY_TAG.get(tag)
    if workload != expected:
        raise ValueError(
            f"workload coordinates differ from literal oracle: tag={tag!r}, "
            f"expected={expected!r}, actual={workload!r}"
        )
    search_config = {
        "scale": "silo-backoff-extended-static-codec-v2",
        "base": "L-W0",
        "sweep_us": list(EXTENDED_SWEEP_US),
        "workload": tag,
        "records": p2_2.RECORDS,
        "threads": p2_2.THREADS,
        "ycsb": dict(workload),
        "measurement_seed": MEASUREMENT_SEEDS[tag],
        "measurement_order": measurement_order(tag),
    }
    cfg = CampaignConfig(
        spec_slug=f"b10-backoff-grid-static-codec-v2-silo-{tag}",
        search_tag="sweep",
        spec_content=f"B-10 certified extended static-backoff grid; workload={tag}",
        ccbench_commit=pin.CURRENT_PIN,
        search_config=search_config,
        trial="b10-backoff-grid-static-codec-v2",
    )
    if contract is None:
        contract = p2_2._legacy_linux_contract()
    return ident.bind_environment_contract(cfg, contract)


def t2266_config_for(
        tag: str, workload: dict[str, str], *, contract=None) -> CampaignConfig:
    expected = WORKLOAD_BY_TAG.get(tag)
    if workload != expected:
        raise ValueError(
            f"workload coordinates differ from literal oracle: tag={tag!r}, "
            f"expected={expected!r}, actual={workload!r}"
        )
    points = _t2266_points(tag)
    search_config = {
        "scale": "t2266-backoff-static-tail-v2",
        "run_kind": T2266_RUN_KIND,
        "base": "L-W0",
        "grid": [
            {"label": label, "flags": dict(flags)} for label, flags in points
        ],
        "requested_us": list(T2266_REQUESTED_US),
        "realized_us": list(T2266_REALIZED_US),
        "unrealized": [
            {"backoff_us": amount, "reason": reason}
            for amount, reason in sorted(T2266_UNREALIZED.items())
        ],
        "workload": tag,
        "records": p2_2.RECORDS,
        "threads": p2_2.THREADS,
        "ycsb": dict(workload),
        "measurement_seed": MEASUREMENT_SEEDS[tag],
        "measurement_order": t2266_measurement_order(tag),
    }
    cfg = CampaignConfig(
        spec_slug=f"t2266-backoff-static-tail-v2-silo-{tag}",
        search_tag="sweep",
        spec_content=f"T-2266 static-backoff tail measurement; workload={tag}",
        ccbench_commit=pin.CURRENT_PIN,
        search_config=search_config,
        trial="t2266-backoff-static-tail-v2",
    )
    if contract is None:
        contract = p2_2._legacy_linux_contract()
    return ident.bind_environment_contract(cfg, contract)


def t2418_config_for(
        tag: str, workload: dict[str, str], *, contract=None) -> CampaignConfig:
    expected = WORKLOAD_BY_TAG.get(tag)
    if workload != expected:
        raise ValueError(
            f"workload coordinates differ from literal oracle: tag={tag!r}, "
            f"expected={expected!r}, actual={workload!r}"
        )
    points = _t2418_points(tag)
    search_config = {
        "scale": "t2418-backoff-static-explore-v2",
        "run_kind": T2418_RUN_KIND,
        "claim_scope": T2418_CLAIM_SCOPE,
        "exploratory": True,
        "formal_series": False,
        "declared_use_class": "official",
        "exploration_values_us": list(T2418_REQUESTED_US),
        "requested_us": list(T2418_REQUESTED_US),
        "realized_us": list(T2418_REALIZED_US),
        "unrealized": [
            {"backoff_us": amount, "reason": reason}
            for amount, reason in sorted(T2418_UNREALIZED.items())
        ],
        "formal_grid_status": T2418_FORMAL_GRID_STATUS,
        "formal_stopping_criterion_status": (
            T2418_FORMAL_STOPPING_CRITERION_STATUS
        ),
        "meaning_witness_status": T2418_MEANING_WITNESS_STATUS,
        "base": "L-W0",
        "grid": [
            {"label": label, "flags": dict(flags)} for label, flags in points
        ],
        "workload": tag,
        "reps": p2_2.REPS,
        "extime_s": p2_2.EXTIME,
        "records": p2_2.RECORDS,
        "threads": p2_2.THREADS,
        "ycsb": dict(workload),
        "measurement_seed": MEASUREMENT_SEEDS[tag],
        "measurement_order": t2418_measurement_order(tag),
    }
    cfg = CampaignConfig(
        spec_slug=f"t2418-backoff-static-explore-v2-silo-{tag}",
        search_tag="sweep",
        spec_content=(
            "T-2418 exploratory static-backoff right-tail measurement; "
            f"not a formal series; workload={tag}"
        ),
        ccbench_commit=pin.CURRENT_PIN,
        search_config=search_config,
        trial="t2418-backoff-static-explore-v2",
    )
    if contract is None:
        contract = p2_2._legacy_linux_contract()
    return ident.bind_environment_contract(cfg, contract)


class _T2266RepCapture:
    """Observe the parsed values already produced by each pipeline rep."""

    def __init__(self) -> None:
        self.rounds: list[dict[str, object]] = []

    def _record_round(
            self, point, abort_rates: Sequence[Optional[float]],
            rep_observations: Sequence[Mapping[str, object]],
    ) -> None:
        throughputs = list(point.throughputs)
        if len(abort_rates) != len(throughputs):
            raise RuntimeError(
                "T-2266 rep capture requires exactly one abort parser call "
                "per throughput rep, in rep order"
            )
        if len(rep_observations) != len(throughputs):
            raise RuntimeError(
                "T-2266 rep capture requires one runner observation per rep"
            )
        if (
            [item.get("rep_index") for item in rep_observations]
            != list(range(len(throughputs)))
            or [item.get("throughput") for item in rep_observations] != throughputs
        ):
            raise RuntimeError(
                "T-2266 abort parser calls are not bound to runner rep order"
            )
        reps = [
            {
                "rep": rep,
                "throughput_tps": throughput,
                "abort_rate": abort_rate,
            }
            for rep, (throughput, abort_rate) in enumerate(zip(
                throughputs, abort_rates,
            ))
        ]
        self.rounds.append({
            "run_cmd": point.run_cmd,
            "throughput_tps": throughputs,
            "reps": reps,
        })

    @contextmanager
    def installed(self):
        original_measure_point = campaign_pipeline.measure_point

        def measure_point_with_reps(*args, **kwargs):
            abort_rates: list[Optional[float]] = []
            original_parse_abort_rate = calibrator_runner.parse_abort_rate
            rep_observations = kwargs.get("rep_observations")
            if rep_observations is None:
                rep_observations = []
                kwargs["rep_observations"] = rep_observations
            if type(rep_observations) is not list:
                raise RuntimeError("T-2266 rep observations require an exact list")
            observation_start = len(rep_observations)

            def observed_parse_abort_rate(metrics):
                value = original_parse_abort_rate(metrics)
                abort_rates.append(value)
                return value

            calibrator_runner.parse_abort_rate = observed_parse_abort_rate
            try:
                point = original_measure_point(*args, **kwargs)
            finally:
                calibrator_runner.parse_abort_rate = original_parse_abort_rate
            self._record_round(
                point, abort_rates, rep_observations[observation_start:],
            )
            return point

        campaign_pipeline.measure_point = measure_point_with_reps
        try:
            yield self
        finally:
            campaign_pipeline.measure_point = original_measure_point

    def reps_for(self, bench: Mapping[str, object]) -> list[dict[str, object]]:
        run_cmd = bench.get("run_cmd")
        tps = bench.get("tps")
        normalized_tps = tuple(tps) if type(tps) in {list, tuple} else None
        matches = [
            item for item in self.rounds
            if (
                item["run_cmd"] == run_cmd
                and tuple(item["throughput_tps"]) == normalized_tps
            )
        ]
        if not matches:
            raise RuntimeError("T-2266 adopted bench round lacks rep capture")
        canonical = matches[0]["reps"]
        if any(item["reps"] != canonical for item in matches[1:]):
            raise RuntimeError("T-2266 adopted bench round has ambiguous rep capture")
        return [dict(rep) for rep in canonical]


class _T2418RepCapture:
    """Observe the parsed values produced by each T-2418 pipeline rep."""

    def __init__(self) -> None:
        self.rounds: list[dict[str, object]] = []

    def _record_round(
            self, point, abort_rates: Sequence[Optional[float]],
            rep_observations: Sequence[Mapping[str, object]],
    ) -> None:
        throughputs = list(point.throughputs)
        if len(abort_rates) != len(throughputs):
            raise RuntimeError(
                "T-2418 rep capture requires exactly one abort parser call "
                "per throughput rep, in rep order"
            )
        if len(rep_observations) != len(throughputs):
            raise RuntimeError(
                "T-2418 rep capture requires one runner observation per rep"
            )
        if (
            [item.get("rep_index") for item in rep_observations]
            != list(range(len(throughputs)))
            or [item.get("throughput") for item in rep_observations] != throughputs
        ):
            raise RuntimeError(
                "T-2418 abort parser calls are not bound to runner rep order"
            )
        reps = [
            {
                "rep": rep,
                "throughput_tps": throughput,
                "abort_rate": abort_rate,
            }
            for rep, (throughput, abort_rate) in enumerate(zip(
                throughputs, abort_rates,
            ))
        ]
        self.rounds.append({
            "run_cmd": point.run_cmd,
            "throughput_tps": throughputs,
            "reps": reps,
        })

    @contextmanager
    def installed(self):
        original_measure_point = campaign_pipeline.measure_point

        def measure_point_with_reps(*args, **kwargs):
            abort_rates: list[Optional[float]] = []
            original_parse_abort_rate = calibrator_runner.parse_abort_rate
            rep_observations = kwargs.get("rep_observations")
            if rep_observations is None:
                rep_observations = []
                kwargs["rep_observations"] = rep_observations
            if type(rep_observations) is not list:
                raise RuntimeError("T-2418 rep observations require an exact list")
            observation_start = len(rep_observations)

            def observed_parse_abort_rate(metrics):
                value = original_parse_abort_rate(metrics)
                abort_rates.append(value)
                return value

            calibrator_runner.parse_abort_rate = observed_parse_abort_rate
            try:
                point = original_measure_point(*args, **kwargs)
            finally:
                calibrator_runner.parse_abort_rate = original_parse_abort_rate
            self._record_round(
                point, abort_rates, rep_observations[observation_start:],
            )
            return point

        campaign_pipeline.measure_point = measure_point_with_reps
        try:
            yield self
        finally:
            campaign_pipeline.measure_point = original_measure_point

    def reps_for(self, bench: Mapping[str, object]) -> list[dict[str, object]]:
        run_cmd = bench.get("run_cmd")
        tps = bench.get("tps")
        normalized_tps = tuple(tps) if type(tps) in {list, tuple} else None
        matches = [
            item for item in self.rounds
            if (
                item["run_cmd"] == run_cmd
                and tuple(item["throughput_tps"]) == normalized_tps
            )
        ]
        if not matches:
            raise RuntimeError("T-2418 adopted bench round lacks rep capture")
        canonical = matches[0]["reps"]
        if any(item["reps"] != canonical for item in matches[1:]):
            raise RuntimeError("T-2418 adopted bench round has ambiguous rep capture")
        return [dict(rep) for rep in canonical]


def _finite_number(value: object, *, positive: bool = False) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(float(value))
        and (not positive or float(value) > 0.0)
    )


def _t2266_point_label(flags: Mapping[str, int]) -> tuple[str, str, Optional[int]]:
    back_off = flags.get("BACK_OFF")
    amount = flags.get("BACKOFF_FIXED")
    if back_off == 0 and amount == -1:
        return "none", "none", None
    if back_off == 1 and amount == -1:
        return "adaptive", "adaptive", None
    if back_off == 1 and type(amount) is int and amount >= 0:
        try:
            physical_us = decode_static_backoff_us(amount)
        except ValueError:
            pass
        else:
            if physical_us in T2266_REALIZED_US:
                return f"fixed-{physical_us}us", "static", physical_us
    raise RuntimeError("T-2266 campaign contains an unexpected backoff point")


def _t2418_point_label(flags: Mapping[str, int]) -> tuple[str, str, Optional[int]]:
    back_off = flags.get("BACK_OFF")
    amount = flags.get("BACKOFF_FIXED")
    if back_off == 0 and amount == -1:
        return "none", "none", None
    if back_off == 1 and amount == -1:
        return "adaptive", "adaptive", None
    if back_off == 1 and type(amount) is int and amount >= 0:
        try:
            physical_us = decode_static_backoff_us(amount)
        except ValueError:
            pass
        else:
            if physical_us in T2418_REALIZED_US:
                return f"fixed-{physical_us}us", "static", physical_us
    raise RuntimeError("T-2418 campaign contains an unexpected backoff point")


def _load_t2266_report_points(
        tag: str, output_root: str, capture: _T2266RepCapture,
) -> tuple[str, list[dict[str, object]]]:
    cfg = t2266_config_for(tag, WORKLOAD_BY_TAG[tag])
    view = require_certified_campaign_view(discover_campaign_dir(
        cfg.spec_slug,
        cfg.search_tag,
        output_root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ))
    expected = {
        genome.canonical(): (index, label)
        for index, (label, genome) in enumerate(zip(
            t2266_measurement_order(tag), t2266_genomes(tag), strict=True,
        ))
    }
    points: list[dict[str, object]] = []
    seen: set[str] = set()
    campaign_id = os.path.basename(view.layout.root)
    for variant, state in wal.replay_admitted_records(view.records).items():
        if not state.committed:
            continue
        if state.committed_build_start is None or state.committed_bench is None:
            raise RuntimeError("T-2266 committed point lacks attempt-bound records")
        canonical = state.committed_build_start.payload.get("genome")
        if canonical not in expected or canonical in seen:
            raise RuntimeError("T-2266 committed genome set differs from preregistration")
        seen.add(canonical)
        flags = {
            key: int(value)
            for key, value in (
                item.split("=", 1) for item in canonical.split("|", 1)[1].split(",")
            )
        }
        label, kind, amount = _t2266_point_label(flags)
        point_index, expected_label = expected[canonical]
        if label != expected_label:
            raise RuntimeError("T-2266 label and genome order differ")
        bench = state.committed_bench.payload
        reps = capture.reps_for(bench)
        if (
            len(reps) != p2_2.REPS
            or [rep.get("rep") for rep in reps] != list(range(p2_2.REPS))
        ):
            raise RuntimeError("T-2266 report requires every configured rep")
        if not all(
            _finite_number(rep.get("throughput_tps"), positive=True)
            and _finite_number(rep.get("abort_rate"))
            and 0.0 <= float(rep["abort_rate"]) <= 1.0
            for rep in reps
        ):
            raise RuntimeError(
                "T-2266 report requires finite throughput and abort rate per rep"
            )
        indicators = bench.get("leading_indicators")
        if type(indicators) not in {dict, MappingProxyType}:
            raise RuntimeError("T-2266 committed bench lacks leading indicators")
        correctness_verified = bool(state.committed_verify) and all(
            record.payload.get("certified") is True
            for record in state.committed_verify
        )
        if not correctness_verified:
            raise RuntimeError(
                "T-2266 report requires correctness-verified committed points"
            )
        points.append({
            "label": label,
            "point_index": point_index,
            "kind": kind,
            "backoff_us": amount,
            "variant_id": variant,
            "genome": canonical,
            "committed": True,
            "correctness_verified": True,
            "performance_certified": False,
            "certified": False,
            "claim_scope": T2266_CLAIM_SCOPE,
            "source_measurement": "trace_disabled",
            "median_tps": bench.get("median_tps"),
            "reps": reps,
            "representative_abort_rate": indicators.get("abort_rate"),
            "representative_latency_ns": indicators.get("latency_ns"),
            "cv": bench.get("cv"),
            "unstable": bench.get("unstable"),
        })
    if seen != set(expected) or len(points) != 8:
        raise RuntimeError("T-2266 report requires all eight committed genomes")
    points.sort(key=lambda point: point["point_index"])
    return campaign_id, points


def _load_t2418_report_points(
        tag: str, output_root: str, capture: _T2418RepCapture,
) -> tuple[str, list[dict[str, object]]]:
    cfg = t2418_config_for(tag, WORKLOAD_BY_TAG[tag])
    view = require_certified_campaign_view(discover_campaign_dir(
        cfg.spec_slug,
        cfg.search_tag,
        output_root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ))
    expected = {
        genome.canonical(): (index, label)
        for index, (label, genome) in enumerate(zip(
            t2418_measurement_order(tag), t2418_genomes(tag), strict=True,
        ))
    }
    points: list[dict[str, object]] = []
    seen: set[str] = set()
    campaign_id = os.path.basename(view.layout.root)
    for variant, state in wal.replay_admitted_records(view.records).items():
        if not state.committed:
            continue
        if state.committed_build_start is None or state.committed_bench is None:
            raise RuntimeError("T-2418 committed point lacks attempt-bound records")
        canonical = state.committed_build_start.payload.get("genome")
        if canonical not in expected or canonical in seen:
            raise RuntimeError("T-2418 committed genome set differs from preregistration")
        seen.add(canonical)
        flags = {
            key: int(value)
            for key, value in (
                item.split("=", 1) for item in canonical.split("|", 1)[1].split(",")
            )
        }
        label, kind, amount = _t2418_point_label(flags)
        point_index, expected_label = expected[canonical]
        if label != expected_label:
            raise RuntimeError("T-2418 label and genome order differ")
        bench = state.committed_bench.payload
        reps = capture.reps_for(bench)
        if (
            len(reps) != p2_2.REPS
            or [rep.get("rep") for rep in reps] != list(range(p2_2.REPS))
        ):
            raise RuntimeError("T-2418 report requires every configured rep")
        if not all(
            _finite_number(rep.get("throughput_tps"), positive=True)
            and _finite_number(rep.get("abort_rate"))
            and 0.0 <= float(rep["abort_rate"]) <= 1.0
            for rep in reps
        ):
            raise RuntimeError(
                "T-2418 report requires finite throughput and abort rate per rep"
            )
        indicators = bench.get("leading_indicators")
        if type(indicators) not in {dict, MappingProxyType}:
            raise RuntimeError("T-2418 committed bench lacks leading indicators")
        correctness_verified = bool(state.committed_verify) and all(
            record.payload.get("certified") is True
            for record in state.committed_verify
        )
        if not correctness_verified:
            raise RuntimeError(
                "T-2418 report requires correctness-verified committed points"
            )
        points.append({
            "label": label,
            "point_index": point_index,
            "kind": kind,
            "backoff_us": amount,
            "variant_id": variant,
            "genome": canonical,
            "committed": True,
            "correctness_verified": True,
            "performance_certified": False,
            "certified": False,
            "claim_scope": T2418_CLAIM_SCOPE,
            "source_measurement": "trace_disabled",
            "median_tps": bench.get("median_tps"),
            "reps": reps,
            "representative_abort_rate": indicators.get("abort_rate"),
            "representative_latency_ns": indicators.get("latency_ns"),
            "cv": bench.get("cv"),
            "unstable": bench.get("unstable"),
        })
    if seen != set(expected) or len(points) != 5:
        raise RuntimeError("T-2418 report requires all five committed genomes")
    points.sort(key=lambda point: point["point_index"])
    return campaign_id, points


def _t2266_report_document(
        tag: str, campaign_id: str,
        points: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    serialized_points = []
    for point in points:
        row = dict(point)
        reps = row.get("reps")
        if type(reps) is not list or len(reps) != p2_2.REPS:
            raise RuntimeError("T-2266 JSON requires all rep records")
        row["throughput_tps_reps"] = [rep["throughput_tps"] for rep in reps]
        row["abort_rate_reps"] = [rep["abort_rate"] for rep in reps]
        serialized_points.append(row)
    return {
        "schema_version": T2266_REPORT_SCHEMA,
        "status": "complete",
        "run_kind": T2266_RUN_KIND,
        "claim_scope": T2266_CLAIM_SCOPE,
        "source_measurement": "trace_disabled",
        "performance_certified": False,
        "correctness_verified": True,
        "campaign_id": campaign_id,
        "workload": tag,
        "workload_coordinates": dict(WORKLOAD_BY_TAG[tag]),
        "requested_us": list(T2266_REQUESTED_US),
        "realized_us": list(T2266_REALIZED_US),
        "unrealized": [
            {"backoff_us": amount, "reason": reason}
            for amount, reason in sorted(T2266_UNREALIZED.items())
        ],
        "measurement_order": t2266_measurement_order(tag),
        "points": serialized_points,
    }


def _t2418_report_document(
        tag: str, campaign_id: str,
        points: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    serialized_points = []
    for point in points:
        row = dict(point)
        reps = row.get("reps")
        if type(reps) is not list or len(reps) != p2_2.REPS:
            raise RuntimeError("T-2418 JSON requires all rep records")
        row["throughput_tps_reps"] = [rep["throughput_tps"] for rep in reps]
        row["abort_rate_reps"] = [rep["abort_rate"] for rep in reps]
        serialized_points.append(row)
    return {
        "schema_version": T2418_REPORT_SCHEMA,
        "status": "complete",
        "run_kind": T2418_RUN_KIND,
        "claim_scope": T2418_CLAIM_SCOPE,
        "exploratory": True,
        "formal_series": False,
        "declared_use_class": "official",
        "exploration_values_us": list(T2418_REQUESTED_US),
        "requested_us": list(T2418_REQUESTED_US),
        "realized_us": list(T2418_REALIZED_US),
        "unrealized": [
            {"backoff_us": amount, "reason": reason}
            for amount, reason in sorted(T2418_UNREALIZED.items())
        ],
        "formal_grid_status": T2418_FORMAL_GRID_STATUS,
        "formal_stopping_criterion_status": (
            T2418_FORMAL_STOPPING_CRITERION_STATUS
        ),
        "meaning_witness_status": T2418_MEANING_WITNESS_STATUS,
        "reps": p2_2.REPS,
        "extime_s": p2_2.EXTIME,
        "records": p2_2.RECORDS,
        "threads": p2_2.THREADS,
        "source_measurement": "trace_disabled",
        "performance_certified": False,
        "correctness_verified": True,
        "campaign_id": campaign_id,
        "workload": tag,
        "workload_coordinates": dict(WORKLOAD_BY_TAG[tag]),
        "measurement_order": t2418_measurement_order(tag),
        "points": serialized_points,
    }


def materialize_t2266_report(
        tag: str, output_root: str, capture: _T2266RepCapture,
) -> dict[str, str]:
    """Create the T-2266 numeric artifacts without adding a shape verdict."""
    campaign_id, points = _load_t2266_report_points(tag, output_root, capture)
    document = _t2266_report_document(tag, campaign_id, points)
    reports = Path(output_root) / "campaigns" / campaign_id / "reports"
    stem = reports / f"t2266-backoff-static-tail-{tag}"
    dat_path = Path(f"{stem}.dat")
    json_path = Path(f"{stem}.json")
    if dat_path.exists() or json_path.exists():
        raise FileExistsError("T-2266 report artifacts are create-only")
    # Validate the complete JSON payload before creating either report file.
    json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    provenance = {
        "campaign": campaign_id,
        "workload": tag,
        "run_kind": T2266_RUN_KIND,
        "claim_scope": T2266_CLAIM_SCOPE,
        "source_measurement": "trace_disabled",
        "performance_certified": False,
        "correctness_verified": True,
        "requested_us": list(T2266_REQUESTED_US),
        "realized_us": list(T2266_REALIZED_US),
        "unrealized": [
            {"backoff_us": amount, "reason": reason}
            for amount, reason in sorted(T2266_UNREALIZED.items())
        ],
    }
    lines = [
        f"# T-2266 static backoff tail: {tag}",
        "# columns: backoff_us throughput_tps abort_rate latency_ns cv",
        "# provenance: " + json.dumps(
            provenance, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ),
        "# build command: orchestrator/campaign/backoff_extended_sweep.py",
        (
            "# reproduce data: python -m "
            f"orchestrator.campaign.backoff_extended_sweep {tag} "
            f"--run-kind {T2266_RUN_KIND}"
        ),
    ]
    for point in sorted(
        (point for point in points if point["kind"] == "static"),
        key=lambda point: point["backoff_us"],
    ):
        values = (
            point["backoff_us"],
            point["median_tps"],
            point["representative_abort_rate"],
            point["representative_latency_ns"],
            point["cv"],
        )
        lines.append(" ".join(
            "nan" if value is None else str(value) for value in values
        ))
    _write_create_only_text(dat_path, "\n".join(lines) + "\n")
    _write_create_only_json(json_path, document)
    return {"dat": str(dat_path), "json": str(json_path)}


def materialize_t2418_report(
        tag: str, output_root: str, capture: _T2418RepCapture,
) -> dict[str, str]:
    """Create the disclosed T-2418 exploratory numeric artifacts."""
    campaign_id, points = _load_t2418_report_points(tag, output_root, capture)
    document = _t2418_report_document(tag, campaign_id, points)
    reports = Path(output_root) / "campaigns" / campaign_id / "reports"
    stem = reports / f"t2418-backoff-static-explore-{tag}"
    dat_path = Path(f"{stem}.dat")
    json_path = Path(f"{stem}.json")
    if dat_path.exists() or json_path.exists():
        raise FileExistsError("T-2418 report artifacts are create-only")
    json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    provenance = {
        "run_kind": T2418_RUN_KIND,
        "claim_scope": T2418_CLAIM_SCOPE,
        "exploratory": True,
        "formal_series": False,
        "declared_use_class": "official",
        "exploration_values_us": list(T2418_REQUESTED_US),
        "requested_us": list(T2418_REQUESTED_US),
        "realized_us": list(T2418_REALIZED_US),
        "unrealized": [
            {"backoff_us": amount, "reason": reason}
            for amount, reason in sorted(T2418_UNREALIZED.items())
        ],
        "formal_grid_status": T2418_FORMAL_GRID_STATUS,
        "formal_stopping_criterion_status": (
            T2418_FORMAL_STOPPING_CRITERION_STATUS
        ),
        "meaning_witness_status": T2418_MEANING_WITNESS_STATUS,
        "reps": p2_2.REPS,
        "extime_s": p2_2.EXTIME,
        "records": p2_2.RECORDS,
        "threads": p2_2.THREADS,
        "campaign": campaign_id,
        "workload": tag,
        "source_measurement": "trace_disabled",
        "performance_certified": False,
        "correctness_verified": True,
    }
    lines = [
        f"# T-2418 exploratory static backoff tail: {tag}",
        "# columns: backoff_us throughput_tps abort_rate latency_ns cv",
        "# provenance: " + json.dumps(
            provenance, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ),
        "# build command: orchestrator/campaign/backoff_extended_sweep.py",
        (
            "# reproduce data: python -m "
            f"orchestrator.campaign.backoff_extended_sweep {tag} "
            f"--run-kind {T2418_RUN_KIND}"
        ),
    ]
    for point in sorted(
        (point for point in points if point["kind"] == "static"),
        key=lambda point: point["backoff_us"],
    ):
        values = (
            point["backoff_us"],
            point["median_tps"],
            point["representative_abort_rate"],
            point["representative_latency_ns"],
            point["cv"],
        )
        lines.append(" ".join(
            "nan" if value is None else str(value) for value in values
        ))
    _write_create_only_text(dat_path, "\n".join(lines) + "\n")
    _write_create_only_json(json_path, document)
    return {"dat": str(dat_path), "json": str(json_path)}


def run_workload(
        tag: str, workload: dict[str, str], log=print, *, output_root: str = "",
        cache_root: str, ccbench_dir: Optional[str] = None,
        run_kind: str = EXTENDED_RUN_KIND):
    """Run one workload through the unchanged certified campaign pipeline."""
    if run_kind not in RUN_KINDS:
        raise ValueError(f"unknown B-10 run kind: {run_kind!r}")
    ccbench_dir = _resolve_ccbench_dir(ccbench_dir)
    p2_2._assert_single_tenant()
    site, contract, authorization = p2_2.resolve_site_runtime()
    p2_2._assert_matches_calibration(contract)
    if run_kind == T2266_RUN_KIND:
        selected_config = t2266_config_for
        selected_genomes = t2266_genomes
        selected_order = t2266_measurement_order
        selected_physical_grid = T2266_REALIZED_US
        run_label = "T-2266 static tail"
        rep_capture: Optional[_T2266RepCapture | _T2418RepCapture] = (
            _T2266RepCapture()
        )
    elif run_kind == T2418_RUN_KIND:
        selected_config = t2418_config_for
        selected_genomes = t2418_genomes
        selected_order = t2418_measurement_order
        selected_physical_grid = T2418_REALIZED_US
        run_label = "T-2418 exploratory static tail"
        rep_capture = _T2418RepCapture()
    else:
        selected_config = config_for
        selected_genomes = genomes
        selected_order = measurement_order
        selected_physical_grid = EXTENDED_SWEEP_US
        run_label = "B-10 extended sweep"
        rep_capture = None
    cfg = p2_2._campaign_cfg_for_site(
        selected_config(tag, workload, contract=contract), site, contract,
    )
    ordered_genomes = selected_genomes(tag)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    expected_toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx,
    )
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)

    def capability_resolver(evidence):
        return attest_generator_output(
            build_context,
            evidence,
            generator_input_sha256=hashlib.sha256(
                f"backoff-extended-sweep/v1|{evidence.genome_sha256}".encode("utf-8")
            ).hexdigest(),
        )

    perf = PerfConfig(
        records=p2_2.RECORDS,
        threads=p2_2.THREADS,
        workload=workload,
        extime=p2_2.EXTIME,
        reps=p2_2.REPS,
    )
    log(
        f"\n=== {run_label} workload={tag} "
        f"seed={MEASUREMENT_SEEDS[tag]} order={selected_order(tag)} ==="
    )
    preflight_receipt_path = (
        Path(output_root) / f"b10-backoff-grid-{tag}-perf-preflight.json"
    )
    patch_path = os.path.join(_repo_root(), TEMPLATE_PATCH)
    try:
        with patchharness.checkout(
                pin.CURRENT_PIN, base_dir=ccbench_dir,
        ) as stock_root:
            with patchharness.applied(patch_path, pin.CURRENT_PIN, ccbench_dir):
                _assert_backoff_fixed_materialized(ccbench_dir)
                canonical_ccbench_dir = os.fspath(Path(ccbench_dir).resolve())
                with tempfile.TemporaryDirectory(
                        prefix="izanagi-backoff-condition-gate-",
                ) as fetchcontent_base:
                    canonical_base = os.fspath(Path(fetchcontent_base).resolve())
                    buildcache.prepare_masstree_fetchcontent(
                        ccbench_dir=canonical_ccbench_dir,
                        fetchcontent_base_dir=canonical_base,
                        expected_toolchain_manifest=expected_toolchain_manifest,
                        configure_timeout_s=900,
                        target_timeout_s=900,
                        site=site,
                    )
                    _require_condition_gate_before_measurement(
                        canonical_ccbench_dir,
                        stock_root=stock_root,
                        points=ordered_genomes,
                        cxx=resolved_cxx,
                        configure_args=(
                            f"-DFETCHCONTENT_BASE_DIR={canonical_base}",
                        ),
                        physical_grid=selected_physical_grid,
                    )
                _prebuild_backoff_binaries(
                    ordered_genomes,
                    contract=contract,
                    cache_root=cache_root,
                    ccbench_dir=ccbench_dir,
                    resolved_cc=resolved_cc,
                    resolved_cxx=resolved_cxx,
                    expected_toolchain_manifest=expected_toolchain_manifest,
                    build_context=build_context,
                    capability_resolver=capability_resolver,
                    require_all_binary_hashes=(run_kind == T2266_RUN_KIND),
                    require_all_t2418_binary_hashes=(run_kind == T2418_RUN_KIND),
                )
                capture_context = (
                    rep_capture.installed()
                    if rep_capture is not None else nullcontext()
                )
                with capture_context:
                    summary = run_campaign(
                        cfg,
                        ordered_genomes,
                        perf,
                        contract.env_tag,
                        contract.clocks_per_us,
                        numactl=list(contract.numactl),
                        output_root=output_root,
                        log=log,
                        ccbench_dir=ccbench_dir,
                        cache_root=cache_root,
                        authorization_contract=authorization,
                        env_contract=contract,
                        expected_toolchain_manifest=expected_toolchain_manifest,
                        build_context=build_context,
                        declared_use_class="official",
                        capability_resolver=capability_resolver,
                        perf_preflight_receipt_path=str(preflight_receipt_path),
                        durable_root_policy=_official_durable_root_policy(
                            Path(output_root) if output_root else None,
                        ),
                    )
                if (
                    rep_capture is not None
                    and summary.total == len(ordered_genomes)
                    and summary.committed == len(ordered_genomes)
                    and summary.aborted == 0
                ):
                    if run_kind == T2266_RUN_KIND:
                        materialize_t2266_report(tag, output_root, rep_capture)
                    elif run_kind == T2418_RUN_KIND:
                        materialize_t2418_report(tag, output_root, rep_capture)
                return summary
    except perf_preflight.PerfPreflightError as exc:
        if not preflight_receipt_path.is_file():
            raise
        stop_path = _materialize_preflight_stop(
            tag, output_root, preflight_receipt_path, exc,
        )
        raise PreflightStop(
            f"perf preflight stopped B-10 before measurement: {stop_path.name}"
        ) from exc


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="B-10 certified extended backoff sweep")
    parser.add_argument("workload", choices=[tag for tag, _workload in WORKLOADS])
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--ccbench-dir")
    parser.add_argument("--run-kind", choices=RUN_KINDS, default=EXTENDED_RUN_KIND)
    args = parser.parse_args(argv)
    try:
        summary = run_workload(
            args.workload,
            WORKLOAD_BY_TAG[args.workload],
            output_root=args.output_root,
            cache_root=args.cache_root,
            ccbench_dir=args.ccbench_dir,
            run_kind=args.run_kind,
        )
    except PreflightStop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.run_kind == T2266_RUN_KIND:
        expected_genomes = t2266_genomes(args.workload)
    elif args.run_kind == T2418_RUN_KIND:
        expected_genomes = t2418_genomes(args.workload)
    else:
        expected_genomes = genomes(args.workload)
    complete = summary.committed == len(expected_genomes) and summary.aborted == 0
    if args.run_kind == T2266_RUN_KIND:
        complete = complete and summary.total == len(expected_genomes)
        reports = Path(summary.layout_root) / "reports"
        stem = reports / f"t2266-backoff-static-tail-{args.workload}"
        complete = (
            complete
            and Path(f"{stem}.dat").is_file()
            and Path(f"{stem}.json").is_file()
        )
    elif args.run_kind == T2418_RUN_KIND:
        complete = complete and summary.total == len(expected_genomes)
        reports = Path(summary.layout_root) / "reports"
        stem = reports / f"t2418-backoff-static-explore-{args.workload}"
        complete = (
            complete
            and Path(f"{stem}.dat").is_file()
            and Path(f"{stem}.json").is_file()
        )
    print(
        f"{args.workload}: {summary.campaign_id} committed={summary.committed} "
        f"aborted={summary.aborted}"
    )
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
