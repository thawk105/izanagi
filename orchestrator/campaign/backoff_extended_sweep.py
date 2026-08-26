# -*- coding: utf-8 -*-
"""B-10: cover the complete static backoff range with a certified sweep."""
from __future__ import annotations

import argparse
import hashlib
import random
import sys
from pathlib import Path
from typing import Optional

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import buildcache, ident, p2_2, pin  # noqa: E402
from .backoff_sweep import _BASE, _official_durable_root_policy  # noqa: E402
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
)
from .loop import run_campaign  # noqa: E402
from .model import CampaignConfig, Genome  # noqa: E402
from .pipeline import PerfConfig  # noqa: E402


EXTENDED_SWEEP_US = [
    1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 100,
    150, 250, 400, 560, 680, 1000,
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
        tag: str, workload: dict[str, str], log=print, *, output_root: str = ""):
    """Run one workload through the unchanged certified campaign pipeline."""
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
    return run_campaign(
        cfg,
        ordered_genomes,
        perf,
        contract.env_tag,
        contract.clocks_per_us,
        numactl=list(contract.numactl),
        output_root=output_root,
        log=log,
        authorization_contract=authorization,
        env_contract=contract,
        expected_toolchain_manifest=expected_toolchain_manifest,
        build_context=build_context,
        declared_use_class="official",
        capability_resolver=capability_resolver,
        durable_root_policy=_official_durable_root_policy(
            Path(output_root) if output_root else None,
        ),
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="B-10 certified extended backoff sweep")
    parser.add_argument("workload", choices=[tag for tag, _workload in WORKLOADS])
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args(argv)
    summary = run_workload(
        args.workload,
        WORKLOAD_BY_TAG[args.workload],
        output_root=args.output_root,
    )
    complete = summary.committed == len(genomes(args.workload)) and summary.aborted == 0
    print(
        f"{args.workload}: {summary.campaign_id} committed={summary.committed} "
        f"aborted={summary.aborted}"
    )
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
