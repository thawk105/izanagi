# -*- coding: utf-8 -*-
"""B-10: cover the complete static backoff range with a certified sweep."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Optional

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import buildcache, ident, p2_2, patchharness, pin, source_digest  # noqa: E402
from .backoff_sweep import _BASE, _official_durable_root_policy  # noqa: E402
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from .loop import run_campaign  # noqa: E402
from .model import CampaignConfig, Genome  # noqa: E402
from .pipeline import PerfConfig  # noqa: E402
from ..calibrator import perf_preflight  # noqa: E402


EXTENDED_SWEEP_US = [
    0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 100,
    150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000,
]

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


def _prebuild_backoff_binaries(
        ordered_genomes: list[Genome], *, contract, cache_root: str,
        ccbench_dir: str, resolved_cc: str, resolved_cxx: str,
        expected_toolchain_manifest, build_context, capability_resolver,
        trace_modes: tuple[bool, ...] = (True, False),
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
                **_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": amount,
            })
            for amount in EXTENDED_SWEEP_US
        ],
    ]
    random.Random(MEASUREMENT_SEEDS[tag]).shuffle(points)
    return points


def measurement_order(tag: str) -> list[str]:
    """Return the preregistered, deterministic label permutation."""
    return [label for label, _flags in _ordered_points(tag)]


def genomes(tag: str) -> list[Genome]:
    """Return all reference and static genomes in preregistered run order."""
    return [Genome("silo", flags) for _label, flags in _ordered_points(tag)]


def config_for(tag: str, workload: dict[str, str], *, contract=None) -> CampaignConfig:
    expected = WORKLOAD_BY_TAG.get(tag)
    if workload != expected:
        raise ValueError(
            f"workload coordinates differ from literal oracle: tag={tag!r}, "
            f"expected={expected!r}, actual={workload!r}"
        )
    search_config = {
        "scale": "silo-backoff-extended",
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
        spec_slug=f"b10-backoff-grid-silo-{tag}",
        search_tag="sweep",
        spec_content=f"B-10 certified extended static-backoff grid; workload={tag}",
        ccbench_commit=pin.CURRENT_PIN,
        search_config=search_config,
        trial="b10-backoff-grid",
    )
    if contract is None:
        contract = p2_2._legacy_linux_contract()
    return ident.bind_environment_contract(cfg, contract)


def run_workload(
        tag: str, workload: dict[str, str], log=print, *, output_root: str = "",
        cache_root: str, ccbench_dir: Optional[str] = None):
    """Run one workload through the unchanged certified campaign pipeline."""
    ccbench_dir = _resolve_ccbench_dir(ccbench_dir)
    p2_2._assert_single_tenant()
    site, contract, authorization = p2_2.resolve_site_runtime()
    p2_2._assert_matches_calibration(contract)
    cfg = p2_2._campaign_cfg_for_site(
        config_for(tag, workload, contract=contract), site, contract,
    )
    ordered_genomes = genomes(tag)
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
        f"\n=== B-10 extended sweep workload={tag} "
        f"seed={MEASUREMENT_SEEDS[tag]} order={measurement_order(tag)} ==="
    )
    preflight_receipt_path = (
        Path(output_root) / f"b10-backoff-grid-{tag}-perf-preflight.json"
    )
    patch_path = os.path.join(_repo_root(), TEMPLATE_PATCH)
    try:
        with patchharness.applied(patch_path, pin.CURRENT_PIN, ccbench_dir):
            _assert_backoff_fixed_materialized(ccbench_dir)
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
            )
            return run_campaign(
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
    args = parser.parse_args(argv)
    try:
        summary = run_workload(
            args.workload,
            WORKLOAD_BY_TAG[args.workload],
            output_root=args.output_root,
            cache_root=args.cache_root,
            ccbench_dir=args.ccbench_dir,
        )
    except PreflightStop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    complete = summary.committed == len(genomes(args.workload)) and summary.aborted == 0
    print(
        f"{args.workload}: {summary.campaign_id} committed={summary.committed} "
        f"aborted={summary.aborted}"
    )
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
