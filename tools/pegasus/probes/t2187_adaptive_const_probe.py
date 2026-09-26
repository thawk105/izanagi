#!/usr/bin/env python3
"""Measure or explicitly certify Cicada adaptive-backoff constants.

The default performance mode is unchanged: it builds trace-disabled binaries,
never uses perf, and makes no correctness claim.  Only ``--mode certify`` runs
the trace-enabled, fail-closed serializability contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import re
import resource
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from orchestrator.calibrator.runner import measure_point  # noqa: E402
from orchestrator.campaign import buildcache, env_contract, site_policy, source_digest  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.patchharness import (  # noqa: E402
    applied,
    apply_patch,
    assert_pinned_clean,
    patch_files,
)
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402

LEGACY_SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-probe/v2"
LEGACY_TRACE_SCHEMA_VERSION = "izanagi-dynamic-backoff-trace/v2"
# v2 read compatibility ends at performance artifacts.  These reject-only
# sentinels make the unsupported certification/group boundary explicit.
UNSUPPORTED_V2_CERTIFICATION_SCHEMA_VERSION = (
    "izanagi-cicada-adaptive-3const-certification/v2"
)
UNSUPPORTED_V2_GROUP_RECEIPT_SCHEMA_VERSION = (
    "izanagi-cicada-adaptive-3const-certification-group/v2"
)
SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-probe/v3"
TRACE_SCHEMA_VERSION = "izanagi-dynamic-backoff-trace/v3"
COHORT2_TRACE_SCHEMA_VERSION = "izanagi-dynamic-backoff-trace/v4"
CERTIFICATION_SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-certification/v3"
GROUP_RECEIPT_SCHEMA_VERSION = (
    "izanagi-cicada-adaptive-3const-certification-group/v3"
)
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
DIAGNOSTIC_NOT_CERTIFIED = (
    "trace-enabled diagnostic runs only; no serializability check was run"
)
PIN_FULL = "68106660686232781bca3be792a750d3e19d7a8a"
PATCH_A_REL = "patches/cicada-adaptive-params.patch"
PATCH_B_REL = "patches/cicada-adaptive-dynamic.patch"
PATCH_C_REL = "patches/cicada-adaptive-counterfactual.patch"
PATCH_A = ROOT / PATCH_A_REL
PATCH_B = ROOT / PATCH_B_REL
PATCH_C = ROOT / PATCH_C_REL
# Kept as the legacy name for callers that bind the immutable A patch.
PATCH = PATCH_A
EXPECTED_PATCH_A_SHA256 = (
    "9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b"
)
PREREGISTRATION = ROOT / "docs" / "dynamic-backoff-preregistration.md"
COUNTERFACTUAL_PREREGISTRATION = (
    ROOT / "docs" / "backoff-counterfactual-preregistration.md"
)
BACKOFF_POLICY_PERFORMANCE_PREREGISTRATION = (
    ROOT / "docs" / "backoff-policy-performance-preregistration.md"
)
COUNTERFACTUAL_COHORT2_PREREGISTRATION = (
    ROOT / "docs" / "backoff-counterfactual-cohort2-preregistration.md"
)
PBS_DRIVER = Path(__file__).with_suffix(".pbs").resolve()
DYNAMIC_OUT_PREFIX = Path(
    "/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/"
)
DYNAMIC_CERTIFY_PREFIX = DYNAMIC_OUT_PREFIX / "certify"
DYNAMIC_PERFORMANCE_PREFIX = DYNAMIC_OUT_PREFIX / "perf"
DYNAMIC_POLICY_PERFORMANCE_PREFIX = DYNAMIC_PERFORMANCE_PREFIX / "t2417-policy"

CONTRACT = env_contract.lookup("pegasus")
ENV_TAG = CONTRACT.env_tag
CLOCKS_PER_US = CONTRACT.clocks_per_us
NUMA = list(CONTRACT.numactl)

LOGICAL_CORES = 48
DEFAULT_THREADS = (48,)
DEFAULT_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
EXTIME = 3
RUN_TIMEOUT_S = 180.0

# Frozen cohort1 seeds: docs/backoff-counterfactual-preregistration.md §8.1.
COUNTERFACTUAL_PREREGISTERED_STEP_POLICY_SEEDS = (
    5744733223455690259,
    781552995023334429,
    1606918558588661,
    16736322205931003081,
    1227967287010452276,
    2171878327641984105,
    2057459156086657874,
    11135758292722279839,
    13576760736062537317,
    5470969369189575692,
    2410271300384854639,
    13467815584134101060,
)

CERT_RECORDS = 1_000_000
CERT_PREREGISTERED_STEP_POLICY_SEEDS = (
    14_481_721_328_008_317_845,
    7_453_732_891_837_486_670,
    766_609_016_836_229_506,
    14_479_507_243_158_715_447,
    3_736_279_228_254_271_919,
    6_574_519_577_559_702_715,
    15_525_319_108_568_766_040,
    13_039_315_294_558_381_935,
    16_889_140_200_793_892_447,
    15_536_816_158_447_092_057,
    13_171_317_188_614_694_465,
    3_421_410_286_381_859_835,
)
# Compatibility constant for the two original certification cells.
CERT_EXTIME = 3
COHORT2_EXTIME = 6
COHORT2_BACKOFF_TRACE_TERMINAL_US = 5_000_000
CERT_REPS_PER_JOB = 1
CERT_SLOTS = tuple(range(8))
CERT_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
CERT_PROTOCOL = "silo"
POSITIVE_CONTROL_EXPECTED_COMMITS = 288
POSITIVE_CONTROL_TIMEOUT_S = 120.0
DEFAULT_VERIFIER_TIMEOUT_S = 5_400.0
DEFAULT_BUILD_BUDGET_S = 900.0
DEFAULT_PROLOGUE_BUDGET_S = 540.0
DEFAULT_OUTER_WALLTIME_S = 8_100.0
DEFAULT_EXIT_MARGIN_S = 300.0
GROUP_RECEIPT_WAIT_S = 300.0
POSITIVE_CONTROL_TRACE = (
    ROOT / "orchestrator" / "tests" / "fixtures" / "r8_silo_broken_norw"
)
VERIFIER_ENTRY = ROOT / "orchestrator" / "verify.py"
VERIFIER_PACKAGE = ROOT / "orchestrator" / "verifier"
ALLOWED_GROUP_CLAIM = (
    "固定条件 (records=1,000,000 / threads=48 / extime=3 / max_ope=10 / "
    "zipf=0.9 / rmw=0、workload rr5・rr50・rr95、独立反復 8、計 24 trace) "
    "の下で、調整済み定数の trace-enabled 走行 24 件すべてが verifier で "
    "certified serializable となり、anomaly を 1 件も観測しなかった。"
)
DYNAMIC_GROUP_CLAIM = (
    "固定条件 (records=1,000,000 / threads=48 / extime=3 / max_ope=10 / "
    "zipf=0.9 / rmw=0、workload rr5・rr50・rr95、独立反復 8、計 24 trace) "
    "の下で、全機構 on (計数窓 K=10000 / 最小 2560 µs / 最大 10240 µs、"
    "適応刻み 1〜4 µs、動的上限 下限 50 µs) の `cw-as-dyn` build の "
    "trace-enabled 走行 24 件すべてが verifier で certified serializable "
    "となり、anomaly を 1 件も観測しなかった。機構の各枝の被覆は認証しない。"
)
COHORT2_POLICY1_GROUP_CLAIM = (
    "固定条件 (records=1,000,000 / threads=48 / extime=6 / max_ope=10 / "
    "zipf=0.9 / rmw=0、workload rr5・rr50・rr95、独立反復 8、計 24 trace) "
    "の下で、count 窓 K=10000 / 最小 2560 us / cap "
    "9223372036854775807 us、適応刻み 1〜4 us、動的上限 下限 50 us、"
    "step policy 1 の `cw-as-dyn-c2-p1` build の trace-enabled 走行 "
    "24 件すべてが verifier で certified serializable となり、anomaly を "
    "1 件も観測しなかった。認証対象は 48 threads の既定 seed 実行体に限り、"
    "機構の各枝の被覆は認証しない。"
)
COHORT2_POLICY2_GROUP_CLAIM = (
    "固定条件 (records=1,000,000 / threads=48 / extime=6 / max_ope=10 / "
    "zipf=0.9 / rmw=0、workload rr5・rr50・rr95、独立反復 8、計 24 trace) "
    "の下で、count 窓 K=10000 / 最小 2560 us / cap "
    "9223372036854775807 us、適応刻み 1〜4 us、動的上限 下限 50 us、"
    "step policy 2、default compile seed 11400714819323198485 の "
    "`cw-as-dyn-c2-p2` build の trace-enabled 走行 24 件すべてが verifier "
    "で certified serializable となり、anomaly を 1 件も観測しなかった。"
    "認証対象はこの既定 seed 実行体と 48 threads に限り、12 seed 別実行体、"
    "24 threads、機構の各枝の被覆は認証しない。"
)
CLAIM_LIMITATIONS = (
    "固定条件外へ直列化可能性を一般化しない",
    "未測定の thread 数・records・extime・workload へ外挿しない",
    "trace-disabled performance 値そのものが認証されたとは表現しない",
    "RNG seed を制御していないため形式的信頼度を算出しない",
)

STOCK_STEP_US = 100.0
STOCK_INCR_MILLI = 100_000
STOCK_MAX_US = 1_000
STOCK_UPDATE_US = 10
STOCK_COUNT_WINDOW = 0
STOCK_COUNT_CAP_US = 0
STOCK_STEP_ADAPT = 0
STOCK_STEP_MIN_US = 100.0
STOCK_STEP_MAX_US = 100.0
STOCK_DYN_CEILING = 0
STOCK_STEP_POLICY_SEED = 11_400_714_819_323_198_485

BASE = {
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
}

WORKLOADS = {
    "write-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "5",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "balanced": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "50",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "read-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "95",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
}

_LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_INTEGER_RE = re.compile(r"[0-9]+")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class Cell:
    """One runtime grid cell, normalized to an exact 1/1000 us build value."""

    label: str
    back_off: int
    step_us: float
    ceiling_us: int
    update_us: int
    count_window: int = STOCK_COUNT_WINDOW
    count_cap_us: int = STOCK_COUNT_CAP_US
    step_adapt: int = STOCK_STEP_ADAPT
    step_min_us: float = STOCK_STEP_MIN_US
    step_max_us: float = STOCK_STEP_MAX_US
    dyn_ceiling: int = STOCK_DYN_CEILING
    extended: bool = False
    step_policy: int = 0
    has_step_policy: bool = False

    @property
    def incr_milli(self) -> int:
        return int(Decimal(str(self.step_us)) * 1000)

    @property
    def is_stock_control(self) -> bool:
        return is_stock_control(self)

    @property
    def step_min_milli(self) -> int:
        return int(Decimal(str(self.step_min_us)) * 1000)

    @property
    def step_max_milli(self) -> int:
        return int(Decimal(str(self.step_max_us)) * 1000)


CERT_TUNED_CELL = Cell("tuned", 1, 1.0, 1_000, 2_560)
CERT_DYNAMIC_CELL = Cell(
    "cw-as-dyn",
    1,
    1.0,
    1_000,
    2_560,
    count_window=10_000,
    count_cap_us=10_240,
    step_adapt=1,
    step_min_us=1.0,
    step_max_us=4.0,
    dyn_ceiling=1,
    extended=True,
)
CERT_COHORT2_POLICY1_CELL = Cell(
    "cw-as-dyn-c2-p1",
    1,
    1.0,
    1_000,
    2_560,
    count_window=10_000,
    count_cap_us=9_223_372_036_854_775_807,
    step_adapt=1,
    step_min_us=1.0,
    step_max_us=4.0,
    dyn_ceiling=1,
    extended=True,
    step_policy=1,
    has_step_policy=True,
)
CERT_COHORT2_POLICY2_CELL = Cell(
    "cw-as-dyn-c2-p2",
    1,
    1.0,
    1_000,
    2_560,
    count_window=10_000,
    count_cap_us=9_223_372_036_854_775_807,
    step_adapt=1,
    step_min_us=1.0,
    step_max_us=4.0,
    dyn_ceiling=1,
    extended=True,
    step_policy=2,
    has_step_policy=True,
)
CERT_CELLS = (
    CERT_TUNED_CELL,
    CERT_DYNAMIC_CELL,
    CERT_COHORT2_POLICY1_CELL,
    CERT_COHORT2_POLICY2_CELL,
)
DYNAMIC_CERT_CELLS = (
    CERT_DYNAMIC_CELL,
    CERT_COHORT2_POLICY1_CELL,
    CERT_COHORT2_POLICY2_CELL,
)
# Compatibility alias: its literal and five-field genome remain unchanged.
CERT_CELL = CERT_TUNED_CELL
CERT_CLAIMS = {
    CERT_TUNED_CELL: ALLOWED_GROUP_CLAIM,
    CERT_DYNAMIC_CELL: DYNAMIC_GROUP_CLAIM,
    CERT_COHORT2_POLICY1_CELL: COHORT2_POLICY1_GROUP_CLAIM,
    CERT_COHORT2_POLICY2_CELL: COHORT2_POLICY2_GROUP_CLAIM,
}
CERT_TUNED_CELL_TEXT = "tuned:1:1:1000:2560"
CERT_DYNAMIC_CELL_TEXT = (
    "cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1"
)
CERT_COHORT2_POLICY1_CELL_TEXT = (
    "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1"
)
CERT_COHORT2_POLICY2_CELL_TEXT = (
    "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2"
)
CERT_CELL_BY_TEXT = {
    CERT_TUNED_CELL_TEXT: CERT_TUNED_CELL,
    CERT_DYNAMIC_CELL_TEXT: CERT_DYNAMIC_CELL,
    CERT_COHORT2_POLICY1_CELL_TEXT: CERT_COHORT2_POLICY1_CELL,
    CERT_COHORT2_POLICY2_CELL_TEXT: CERT_COHORT2_POLICY2_CELL,
}
CERT_EXTIME_BY_CELL = {
    CERT_TUNED_CELL: CERT_EXTIME,
    CERT_DYNAMIC_CELL: CERT_EXTIME,
    CERT_COHORT2_POLICY1_CELL: COHORT2_EXTIME,
    CERT_COHORT2_POLICY2_CELL: COHORT2_EXTIME,
}
CERT_PREREGISTRATION_BY_CELL = {
    CERT_TUNED_CELL: PREREGISTRATION,
    CERT_DYNAMIC_CELL: PREREGISTRATION,
    CERT_COHORT2_POLICY1_CELL: COUNTERFACTUAL_COHORT2_PREREGISTRATION,
    CERT_COHORT2_POLICY2_CELL: COUNTERFACTUAL_COHORT2_PREREGISTRATION,
}
CERT_THREADS_BY_CELL = {
    CERT_TUNED_CELL: (48,),
    CERT_DYNAMIC_CELL: (48,),
    CERT_COHORT2_POLICY1_CELL: (24, 48),
    CERT_COHORT2_POLICY2_CELL: (24, 48),
}
CERT_POLICY2_STEP_POLICY_SEEDS = frozenset(
    (*CERT_PREREGISTERED_STEP_POLICY_SEEDS, STOCK_STEP_POLICY_SEED)
)


@dataclass(frozen=True)
class CertificationAxes:
    """Validated certification identity used by every claim consumer."""

    cell: Cell
    threads: int
    step_policy_seed: int | None

    def __post_init__(self) -> None:
        allowed_threads = CERT_THREADS_BY_CELL.get(self.cell)
        if (
            allowed_threads is None
            or type(self.threads) is not int
            or self.threads not in allowed_threads
        ):
            raise ValueError("certification threads are outside the cell closed table")
        if self.cell == CERT_COHORT2_POLICY2_CELL:
            if (
                type(self.step_policy_seed) is not int
                or self.step_policy_seed not in CERT_POLICY2_STEP_POLICY_SEEDS
            ):
                raise ValueError("policy 2 seed is outside the certification closed table")
        elif self.cell == CERT_COHORT2_POLICY1_CELL:
            if self.step_policy_seed != STOCK_STEP_POLICY_SEED:
                raise ValueError("policy 1 must use the exact default compile seed")
        elif self.step_policy_seed is not None:
            raise ValueError("this certification cell has no step-policy seed axis")


def _make_certification_axes(
    cell: Cell,
    threads: object,
    step_policy_seed: object,
    *,
    reason: str,
    detail: str,
) -> CertificationAxes:
    try:
        return CertificationAxes(cell, threads, step_policy_seed)  # type: ignore[arg-type]
    except ValueError as exc:
        raise CertificationReject(reason, detail) from exc


def _certification_claim(axes: CertificationAxes) -> str:
    """Build a claim only from a closed-table, immutable certification identity."""
    if type(axes) is not CertificationAxes:
        raise TypeError("claim construction requires CertificationAxes")
    published_claims = {
        CertificationAxes(CERT_TUNED_CELL, 48, None): ALLOWED_GROUP_CLAIM,
        CertificationAxes(CERT_DYNAMIC_CELL, 48, None): DYNAMIC_GROUP_CLAIM,
        CertificationAxes(
            CERT_COHORT2_POLICY1_CELL, 48, STOCK_STEP_POLICY_SEED
        ): COHORT2_POLICY1_GROUP_CLAIM,
        CertificationAxes(
            CERT_COHORT2_POLICY2_CELL, 48, STOCK_STEP_POLICY_SEED
        ): COHORT2_POLICY2_GROUP_CLAIM,
    }
    published_claim = published_claims.get(axes)
    if published_claim is not None:
        return published_claim
    build_scope = (
        "BACKOFF_TRACE=0 かつ BACKOFF_TRACE_TERMINAL_US の terminal define なしで "
        "build した実行体"
    )
    prefix = (
        f"固定条件 (records=1,000,000 / threads={axes.threads} / "
        f"extime={CERT_EXTIME_BY_CELL[axes.cell]} / max_ope=10 / zipf=0.9 / "
        "rmw=0、workload rr5・rr50・rr95、独立反復 8、計 24 trace) の下で、"
    )
    if axes.cell == CERT_TUNED_CELL:
        subject = "調整済み定数"
        seed_scope = "step policy seed 非適用"
        limitation = "固定条件外と機構の各枝の被覆は認証しない。"
    elif axes.cell == CERT_DYNAMIC_CELL:
        subject = (
            "全機構 on (計数窓 K=10000 / 最小 2560 us / 最大 10240 us、"
            "適応刻み 1〜4 us、動的上限 下限 50 us) の `cw-as-dyn`"
        )
        seed_scope = "step policy seed 非適用"
        limitation = "機構の各枝の被覆は認証しない。"
    elif axes.cell == CERT_COHORT2_POLICY1_CELL:
        subject = (
            "count 窓 K=10000 / 最小 2560 us / cap 9223372036854775807 us、"
            "適応刻み 1〜4 us、動的上限 下限 50 us、step policy 1 の "
            "`cw-as-dyn-c2-p1`"
        )
        seed_scope = f"compile seed {axes.step_policy_seed}"
        limitation = "機構の各枝の被覆は認証しない。"
    else:
        subject = (
            "count 窓 K=10000 / 最小 2560 us / cap 9223372036854775807 us、"
            "適応刻み 1〜4 us、動的上限 下限 50 us、step policy 2 の "
            "`cw-as-dyn-c2-p2`"
        )
        seed_scope = f"compile seed {axes.step_policy_seed}"
        default_seed_note = (
            "この既定 seed は事前登録 12 seed のいずれでもない。"
            if axes.step_policy_seed == STOCK_STEP_POLICY_SEED
            else ""
        )
        limitation = (
            f"{default_seed_note}他の seed、thread 数、機構の各枝は認証しない。"
        )
    return (
        f"{prefix}{subject} build の trace-enabled 走行 24 件すべてが verifier "
        "で certified serializable となり、anomaly を 1 件も観測しなかった。"
        f"認証対象は {axes.threads} threads、{seed_scope}、{build_scope}に限る。"
        f"{limitation}"
    )

TRACE_CELLS = (
    Cell(
        "cw", 1, 1.0, 1_000, 2_560, 10_000, 10_240, 0, 100.0, 100.0, 0,
        True,
    ),
    Cell(
        "cw-as", 1, 1.0, 1_000, 2_560, 10_000, 10_240, 1, 1.0, 4.0, 0,
        True,
    ),
    CERT_DYNAMIC_CELL,
)
TRACE_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
TRACE_THREADS = (24, 48)
TRACE_CELLS_TEXT = (
    "cw:1:1:1000:2560:10000:10240:0:100:100:0,"
    "cw-as:1:1:1000:2560:10000:10240:1:1:4:0,"
    "cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1"
)
COUNTERFACTUAL_TRACE_CELLS_TEXT = (
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2"
)
POLICY_PERFORMANCE_PERMUTATIONS_TEXT = (
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2",
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1",
    "cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2,"
    "cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1,"
    "cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0",
)
POLICY_PERFORMANCE_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
POLICY_PERFORMANCE_THREADS = (6, 12, 18, 24, 30, 36, 42, 48)
POLICY_PERFORMANCE_SEEDS = (
    7170359757993337886,
    17989269546948137795,
    3716960512023197351,
    2309627334396074330,
    17927187949116432153,
    3065832495472073934,
    4312234405970990967,
    427285116805996036,
    3640648522570663905,
    6418011988295890983,
    8628608498907907249,
    3020250207517407008,
    2373385927424670485,
    12508141252750115867,
    5818589253263944573,
    13760661656174455019,
    16587099826641119208,
    13478069633953621058,
)
POLICY_PERFORMANCE_CONTRACT = "backoff-policy-arm-perf/v1"
COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT = (
    "cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0,"
    "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1,"
    "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2"
)
NONMONOTONIC_TRACE_CELLS_TEXT = (
    "nm-step0.5:1:0.5:1000:10:0:0:0:100:100:0,"
    "nm-step1:1:1:1000:10:0:0:0:100:100:0,"
    "nm-step1-u2560:1:1:1000:2560:0:0:0:100:100:0,"
    "nm-step2:1:2:1000:10:0:0:0:100:100:0,"
    "nm-step25:1:25:1000:10:0:0:0:100:100:0,"
    "nm-step100:1:100:1000:10:0:0:0:100:100:0"
)


class CertificationReject(RuntimeError):
    """One fail-closed certification rejection with a stable reason."""

    def __init__(self, reason: str, detail: str):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


def is_stock_control(cell: Cell) -> bool:
    """Return true only for exact stock adaptive settings."""
    return (
        cell.back_off == 1
        and cell.step_us == STOCK_STEP_US
        and cell.ceiling_us == STOCK_MAX_US
        and cell.update_us == STOCK_UPDATE_US
        and cell.count_window == STOCK_COUNT_WINDOW
        and cell.count_cap_us == STOCK_COUNT_CAP_US
        and cell.step_adapt == STOCK_STEP_ADAPT
        and cell.step_min_us == STOCK_STEP_MIN_US
        and cell.step_max_us == STOCK_STEP_MAX_US
        and cell.dyn_ceiling == STOCK_DYN_CEILING
        and cell.step_policy == 0
    )


def _parse_positive_integer(text: str, field: str) -> int:
    if _INTEGER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a positive integer: {text!r}")
    value = int(text)
    if value <= 0:
        raise ValueError(f"{field} must be positive: {value}")
    return value


def _parse_exact_step_us(text: str, field: str) -> tuple[float, int]:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not a decimal: {text!r}") from exc
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{field} must be finite and positive: {text!r}")
    milli = value * 1000
    integral = milli.to_integral_value()
    if milli != integral:
        raise ValueError(
            f"{field} cannot be represented exactly in 1/1000 us: {text!r}"
        )
    return float(value), int(integral)


def _parse_step_us(text: str) -> tuple[float, int]:
    return _parse_exact_step_us(text, "step_us")


def _parse_nonnegative_integer(text: str, field: str) -> int:
    if _INTEGER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a nonnegative integer: {text!r}")
    return int(text)


def parse_cells(text: str) -> tuple[Cell, ...]:
    """Parse exact five-, eleven-, or twelve-field cells."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("cells must not be empty")
    cells: list[Cell] = []
    labels: set[str] = set()
    for index, raw_cell in enumerate(text.split(",")):
        fields = [field.strip() for field in raw_cell.split(":")]
        if len(fields) not in {5, 11, 12} or any(not field for field in fields):
            raise ValueError(
                f"cell {index} must have five, eleven, or twelve nonempty "
                "colon-separated fields: "
                f"{raw_cell!r}"
            )
        label, back_off_text, step_text, ceiling_text, update_text = fields[:5]
        if _LABEL_RE.fullmatch(label) is None:
            raise ValueError(f"cell label is unsafe: {label!r}")
        if label in labels:
            raise ValueError(f"duplicate cell label: {label!r}")
        if back_off_text not in {"0", "1"}:
            raise ValueError(f"back_off must be 0 or 1: {back_off_text!r}")
        step_us, incr_milli = _parse_step_us(step_text)
        ceiling_us = _parse_positive_integer(ceiling_text, "ceiling_us")
        update_us = _parse_positive_integer(update_text, "update_us")
        if len(fields) == 5:
            cell = Cell(label, int(back_off_text), step_us, ceiling_us, update_us)
        else:
            (
                count_window_text,
                count_cap_text,
                step_adapt_text,
                step_min_text,
                step_max_text,
                dyn_ceiling_text,
            ) = fields[5:11]
            step_policy_text = fields[11] if len(fields) == 12 else None
            count_window = _parse_nonnegative_integer(
                count_window_text, "count_window"
            )
            count_cap_us = _parse_nonnegative_integer(
                count_cap_text, "count_cap_us"
            )
            if step_adapt_text not in {"0", "1"}:
                raise ValueError(
                    f"step_adapt must be 0 or 1: {step_adapt_text!r}"
                )
            if dyn_ceiling_text not in {"0", "1"}:
                raise ValueError(
                    f"dyn_ceiling must be 0 or 1: {dyn_ceiling_text!r}"
                )
            if step_policy_text is not None and step_policy_text not in {
                "0",
                "1",
                "2",
            }:
                raise ValueError(
                    "step_policy must be 0, 1, or 2: "
                    f"{step_policy_text!r}"
                )
            step_min_us, step_min_milli = _parse_exact_step_us(
                step_min_text, "step_min_us"
            )
            step_max_us, step_max_milli = _parse_exact_step_us(
                step_max_text, "step_max_us"
            )
            step_adapt = int(step_adapt_text)
            dyn_ceiling = int(dyn_ceiling_text)
            if step_min_milli > step_max_milli:
                raise ValueError("step_min_us must not exceed step_max_us")
            if step_adapt and not (
                step_min_milli <= incr_milli <= step_max_milli
            ):
                raise ValueError(
                    "step_us must lie within step_min_us..step_max_us when "
                    "step_adapt=1"
                )
            if count_window == 0 and count_cap_us != 0:
                raise ValueError("count_window=0 requires count_cap_us=0")
            if dyn_ceiling and step_max_milli * 4 > 50_000:
                raise ValueError(
                    "dyn_ceiling=1 requires step_max_us * 4 <= 50 us"
                )
            cell = Cell(
                label,
                int(back_off_text),
                step_us,
                ceiling_us,
                update_us,
                count_window,
                count_cap_us,
                step_adapt,
                step_min_us,
                step_max_us,
                dyn_ceiling,
                True,
                int(step_policy_text) if step_policy_text is not None else 0,
                step_policy_text is not None,
            )
        if cell.incr_milli != incr_milli:
            raise ValueError(f"step_us normalization changed value: {step_text!r}")
        cells.append(cell)
        labels.add(label)
    if not cells:
        raise ValueError("cells must not be empty")
    return tuple(cells)


_parse_cells = parse_cells
COUNTERFACTUAL_TRACE_CELLS = parse_cells(COUNTERFACTUAL_TRACE_CELLS_TEXT)
POLICY_PERFORMANCE_PERMUTATIONS = tuple(
    parse_cells(text) for text in POLICY_PERFORMANCE_PERMUTATIONS_TEXT
)
POLICY_PERFORMANCE_CELL_SET = frozenset(POLICY_PERFORMANCE_PERMUTATIONS[0])
COUNTERFACTUAL_COHORT2_TRACE_CELLS = parse_cells(
    COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT
)
NONMONOTONIC_TRACE_CELLS = parse_cells(NONMONOTONIC_TRACE_CELLS_TEXT)
BACKOFF_TRACE_CONTRACTS = {
    TRACE_CELLS_TEXT: (
        TRACE_CELLS,
        TRACE_WORKLOADS,
        TRACE_THREADS,
        EXTIME,
        0,
    ),
    COUNTERFACTUAL_TRACE_CELLS_TEXT: (
        COUNTERFACTUAL_TRACE_CELLS,
        TRACE_WORKLOADS,
        TRACE_THREADS,
        EXTIME,
        0,
    ),
    COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT: (
        COUNTERFACTUAL_COHORT2_TRACE_CELLS,
        TRACE_WORKLOADS,
        TRACE_THREADS,
        COHORT2_EXTIME,
        COHORT2_BACKOFF_TRACE_TERMINAL_US,
    ),
    NONMONOTONIC_TRACE_CELLS_TEXT: (
        NONMONOTONIC_TRACE_CELLS,
        ("write-heavy",),
        (48,),
        EXTIME,
        0,
    ),
}


def _validate_grid_contract(cells: tuple[Cell, ...]) -> None:
    disabled = [cell for cell in cells if cell.back_off == 0]
    if len(disabled) != 1 or disabled[0] != Cell(
        "none", 0, STOCK_STEP_US, STOCK_MAX_US, STOCK_UPDATE_US
    ):
        raise ValueError(
            "grid must contain exactly none:0:100:1000:10 as its disabled cell"
        )
    if sum(cell.is_stock_control for cell in cells) != 1:
        raise ValueError("grid must contain exactly one stock adaptive control")
    configurations = {
        (
            cell.back_off,
            cell.incr_milli,
            cell.ceiling_us,
            cell.update_us,
            cell.count_window,
            cell.count_cap_us,
            cell.step_adapt,
            cell.step_min_milli,
            cell.step_max_milli,
            cell.dyn_ceiling,
            cell.step_policy,
            cell.has_step_policy,
        )
        for cell in cells
    }
    if len(configurations) != len(cells):
        raise ValueError("grid contains duplicate build configurations")


def _parse_threads(text: str) -> tuple[int, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("threads must not be empty")
    values = []
    for token in text.split(","):
        token = token.strip()
        if _INTEGER_RE.fullmatch(token) is None:
            raise ValueError(f"thread count must be an integer: {token!r}")
        value = int(token)
        if value <= 0 or value > LOGICAL_CORES:
            raise ValueError(f"thread count is outside 1..{LOGICAL_CORES}: {value}")
        values.append(value)
    if len(set(values)) != len(values):
        raise ValueError(f"thread list contains duplicates: {text!r}")
    return tuple(values)


def _parse_workloads(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("workloads must not be empty")
    values = tuple(token.strip() for token in text.split(","))
    if any(not token for token in values):
        raise ValueError(f"workload list contains an empty item: {text!r}")
    unknown = [token for token in values if token not in WORKLOADS]
    if unknown:
        raise ValueError(f"unknown workloads: {unknown}")
    if len(set(values)) != len(values):
        raise ValueError(f"workload list contains duplicates: {text!r}")
    return values


def _nonnegative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def _uint64_decimal(text: str) -> int:
    if type(text) is not str or _INTEGER_RE.fullmatch(text) is None:
        raise argparse.ArgumentTypeError("must be an ASCII decimal uint64")
    value = int(text)
    if value >= 2**64:
        raise argparse.ArgumentTypeError("must be smaller than 2**64")
    if text != str(value):
        raise argparse.ArgumentTypeError("must use canonical decimal spelling")
    return value


def _positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def _ccbench_head(submodule: Path) -> str:
    head = subprocess.run(
        ["git", "-C", str(submodule), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if CURRENT_PIN != PIN_FULL[: len(CURRENT_PIN)] or head != PIN_FULL:
        raise RuntimeError(
            f"ccbench HEAD {head!r} does not match required pin {PIN_FULL!r}"
        )
    return head


@contextmanager
def isolated_checkout(submodule: Path, pin_commit: str):
    """Create a node-local ``--shared`` clone under ``$TMPDIR``."""
    tmpdir = os.environ.get("TMPDIR")
    if not tmpdir:
        raise RuntimeError("TMPDIR is required for the node-local checkout")
    path = Path(tmpdir) / "ccbench-src"
    if path.exists():
        raise FileExistsError(f"isolated checkout already exists: {path}")
    subprocess.run(
        ["git", "clone", "--shared", "--no-checkout", str(submodule), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "checkout", "--detach", pin_commit],
        check=True,
        capture_output=True,
        text=True,
    )
    assert_pinned_clean(str(path), pin_commit)
    try:
        yield str(path)
    finally:
        assert_pinned_clean(str(path), pin_commit)


def genome_for(
    cell: Cell,
    *,
    backoff_trace: bool = False,
    step_policy_seed: int | None = None,
    backoff_trace_terminal_us: int = 0,
) -> Genome:
    if type(backoff_trace_terminal_us) is not int or backoff_trace_terminal_us < 0:
        raise ValueError("backoff trace terminal us must be a nonnegative integer")
    if backoff_trace_terminal_us and not backoff_trace:
        raise ValueError("backoff trace terminal us requires backoff trace mode")
    flags = {
        **BASE,
        "BACK_OFF": cell.back_off,
        "BACKOFF_INCR_MILLI": cell.incr_milli,
        "BACKOFF_MAX_US": cell.ceiling_us,
        "BACKOFF_UPDATE_US": cell.update_us,
    }
    if cell.extended or backoff_trace:
        flags.update(
            BACKOFF_COUNT_WINDOW=cell.count_window,
            BACKOFF_COUNT_CAP_US=cell.count_cap_us,
            BACKOFF_STEP_ADAPT=cell.step_adapt,
            BACKOFF_STEP_MIN_MILLI=cell.step_min_milli,
            BACKOFF_STEP_MAX_MILLI=cell.step_max_milli,
            BACKOFF_DYN_CEILING=cell.dyn_ceiling,
            BACKOFF_TRACE=int(backoff_trace),
        )
    if cell.has_step_policy:
        flags.update(
            BACKOFF_STEP_POLICY=cell.step_policy,
            BACKOFF_STEP_POLICY_SEED=(
                step_policy_seed
                if cell.step_policy == 2 and step_policy_seed is not None
                else STOCK_STEP_POLICY_SEED
            ),
        )
    if backoff_trace_terminal_us:
        flags["BACKOFF_TRACE_TERMINAL_US"] = backoff_trace_terminal_us
    return Genome("silo", flags)


def _cell_identity(cell: Cell) -> dict:
    identity = {
        "cell": cell.label,
        "back_off": cell.back_off,
        "step_us": cell.step_us,
        "ceiling_us": cell.ceiling_us,
        "update_us": cell.update_us,
        "count_window": cell.count_window,
        "count_cap_us": cell.count_cap_us,
        "step_adapt": cell.step_adapt,
        "step_min_us": cell.step_min_us,
        "step_max_us": cell.step_max_us,
        "dyn_ceiling": cell.dyn_ceiling,
        "cell_format_fields": (
            12 if cell.has_step_policy else 11 if cell.extended else 5
        ),
    }
    if cell.has_step_policy:
        identity["step_policy"] = cell.step_policy
    return identity


def _cell_from_document(document: dict) -> Cell:
    fields = document.get("cell_format_fields")
    if type(fields) is not int or fields not in {5, 11, 12}:
        raise CertificationReject(
            "group-workload-contract-mismatch",
            "certification cell format must be exactly 5, 11, or 12 fields",
        )
    has_step_policy_key = "step_policy" in document
    if has_step_policy_key != (fields == 12):
        raise CertificationReject(
            "group-workload-contract-mismatch",
            "certification cell format and step_policy presence disagree",
        )
    step_policy = document.get("step_policy") if has_step_policy_key else 0
    if fields == 12 and (
        type(step_policy) is not int or step_policy not in {0, 1, 2}
    ):
        raise CertificationReject(
            "group-workload-contract-mismatch",
            "certification step_policy must be an exact integer in 0..2",
        )
    values = (
        document.get("cell"),
        document.get("back_off"),
        document.get("step_us"),
        document.get("ceiling_us"),
        document.get("update_us"),
        document.get("count_window"),
        document.get("count_cap_us"),
        document.get("step_adapt"),
        document.get("step_min_us"),
        document.get("step_max_us"),
        document.get("dyn_ceiling"),
    )
    expected_types = (str, int, float, int, int, int, int, int, float, float, int)
    if any(type(value) is not expected for value, expected in zip(values, expected_types)):
        raise CertificationReject(
            "group-workload-contract-mismatch",
            "certification cell identity has an invalid type",
        )
    cell = Cell(
        *values,
        extended=fields in {11, 12},
        step_policy=step_policy,
        has_step_policy=fields == 12,
    )
    if _cell_identity(cell) != {
        key: document.get(key) for key in _cell_identity(cell)
    }:
        raise CertificationReject(
            "group-workload-contract-mismatch",
            "certification cell identity is not canonical",
        )
    return cell


def _certification_axes_from_document(
    document: dict,
    *,
    cell: Cell | None = None,
    reason: str,
    detail: str,
) -> CertificationAxes:
    """Validate document axes against the same closed tables as live requests."""
    actual_cell = _cell_from_document(document) if cell is None else cell
    seed_required = actual_cell in {
        CERT_COHORT2_POLICY1_CELL,
        CERT_COHORT2_POLICY2_CELL,
    }
    if ("step_policy_seed" in document) != seed_required:
        raise CertificationReject(reason, detail)
    seed = document.get("step_policy_seed") if seed_required else None
    return _make_certification_axes(
        actual_cell,
        document.get("threads"),
        seed,
        reason=reason,
        detail=detail,
    )


def _group_certification_axes(
    rows: list[dict],
    *,
    reason: str = "group-cell-identity-mismatch",
    detail: str = "group thread and seed axes are not one exact identity",
) -> CertificationAxes:
    axes = {
        _certification_axes_from_document(
            row,
            reason=reason,
            detail=detail,
        )
        for row in rows
    }
    if len(axes) != 1:
        raise CertificationReject(reason, detail)
    return next(iter(axes))


def _patch_stack_identity() -> dict:
    if not PATCH_A.is_file():
        raise FileNotFoundError(f"patch A is missing: {PATCH_A}")
    a_sha256 = hashlib.sha256(PATCH_A.read_bytes()).hexdigest()
    if a_sha256 != EXPECTED_PATCH_A_SHA256:
        raise RuntimeError(
            "immutable patch A SHA-256 mismatch: "
            f"expected {EXPECTED_PATCH_A_SHA256}, got {a_sha256}"
        )
    if not PATCH_B.is_file():
        raise FileNotFoundError(f"patch B is missing: {PATCH_B}")
    b_sha256 = hashlib.sha256(PATCH_B.read_bytes()).hexdigest()
    if not PATCH_C.is_file():
        raise FileNotFoundError(f"patch C is missing: {PATCH_C}")
    c_sha256 = hashlib.sha256(PATCH_C.read_bytes()).hexdigest()
    stack = [
        {"path": PATCH_A_REL, "sha256": a_sha256},
        {"path": PATCH_B_REL, "sha256": b_sha256},
        {"path": PATCH_C_REL, "sha256": c_sha256},
    ]
    encoded = "izanagi-patch-stack/v1\n" + "".join(
        f"{entry['path']} {entry['sha256']}\n" for entry in stack
    )
    return {
        "patch_sha256": a_sha256,
        "dynamic_patch_sha256": b_sha256,
        "counterfactual_patch_sha256": c_sha256,
        "patch_stack": stack,
        "patch_stack_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    }


@contextmanager
def _applied_patch_stack(work_root: str):
    """Apply exact-path A, B, then C; outer A cleanup reverts the stack."""
    with applied(str(PATCH_A), CURRENT_PIN, work_root) as a_files:
        b_files = patch_files(str(PATCH_B), work_root)
        if set(b_files) != set(a_files):
            raise RuntimeError(
                "patch B must touch exactly the same existing paths as patch A"
            )
        for relative in b_files:
            result = subprocess.run(
                ["git", "-C", work_root, "cat-file", "-e", f"HEAD:{relative}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"patch B path does not exist at pinned HEAD: {relative}"
                )
        apply_patch(str(PATCH_B), work_root)
        c_files = patch_files(str(PATCH_C), work_root)
        if set(c_files) != set(a_files):
            raise RuntimeError(
                "patch C must touch exactly the same existing paths as patches A and B"
            )
        for relative in c_files:
            result = subprocess.run(
                ["git", "-C", work_root, "cat-file", "-e", f"HEAD:{relative}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"patch C path does not exist at pinned HEAD: {relative}"
                )
        apply_patch(str(PATCH_C), work_root)
        yield tuple(c_files)


def _validated_repo_head(value: str | None) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise RuntimeError("--repo-head must be the exact PBS_O_WORKDIR commit")
    actual = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if value != actual:
        raise RuntimeError(
            f"--repo-head {value!r} does not match driver repository {actual!r}"
        )
    return value


def _validated_repo_clean(value: str | None) -> bool:
    if value != "1":
        raise RuntimeError("--repo-clean must attest the PBS clean-repository check")
    status = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status:
        raise RuntimeError(
            "driver repository is not tracked-clean despite the PBS attestation"
        )
    return True


def _execution_identity(repo_clean: str | None) -> dict:
    return {
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "pbs_sha256": hashlib.sha256(PBS_DRIVER.read_bytes()).hexdigest(),
        "driver_argv": list(sys.argv),
        "repo_status_clean": _validated_repo_clean(repo_clean),
    }


def _validate_recorded_execution_identity(
    document: dict, *, reason: str
) -> dict:
    identity = {
        key: document.get(key)
        for key in (
            "driver_sha256",
            "pbs_sha256",
            "driver_argv",
            "repo_status_clean",
        )
    }
    if (
        type(identity["driver_sha256"]) is not str
        or _SHA256_RE.fullmatch(identity["driver_sha256"]) is None
        or type(identity["pbs_sha256"]) is not str
        or _SHA256_RE.fullmatch(identity["pbs_sha256"]) is None
        or type(identity["driver_argv"]) is not list
        or not identity["driver_argv"]
        or any(type(item) is not str for item in identity["driver_argv"])
        or identity["repo_status_clean"] is not True
    ):
        raise CertificationReject(reason, "execution identity is missing or invalid")
    return identity


def _prereg_sha256() -> str:
    if not PREREGISTRATION.is_file():
        raise FileNotFoundError(f"preregistration is missing: {PREREGISTRATION}")
    return hashlib.sha256(PREREGISTRATION.read_bytes()).hexdigest()


def _counterfactual_prereg_sha256() -> str:
    if not COUNTERFACTUAL_PREREGISTRATION.is_file():
        raise FileNotFoundError(
            "counterfactual preregistration is missing: "
            f"{COUNTERFACTUAL_PREREGISTRATION}"
        )
    return hashlib.sha256(COUNTERFACTUAL_PREREGISTRATION.read_bytes()).hexdigest()


def _backoff_policy_performance_prereg_sha256() -> str:
    if not BACKOFF_POLICY_PERFORMANCE_PREREGISTRATION.is_file():
        raise FileNotFoundError(
            "backoff policy performance preregistration is missing: "
            f"{BACKOFF_POLICY_PERFORMANCE_PREREGISTRATION}"
        )
    return hashlib.sha256(
        BACKOFF_POLICY_PERFORMANCE_PREREGISTRATION.read_bytes()
    ).hexdigest()


def _counterfactual_cohort2_prereg_sha256() -> str:
    if not COUNTERFACTUAL_COHORT2_PREREGISTRATION.is_file():
        raise FileNotFoundError(
            "cohort 2 counterfactual preregistration is missing: "
            f"{COUNTERFACTUAL_COHORT2_PREREGISTRATION}"
        )
    return hashlib.sha256(
        COUNTERFACTUAL_COHORT2_PREREGISTRATION.read_bytes()
    ).hexdigest()


def _certification_prereg_sha256(cell: Cell) -> str:
    path = CERT_PREREGISTRATION_BY_CELL.get(cell)
    if path is None:
        raise CertificationReject(
            "certification-cell-mismatch",
            "certification cell has no exact preregistration binding",
        )
    if not path.is_file():
        raise FileNotFoundError(f"certification preregistration is missing: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_dynamic_output_path(out: Path) -> None:
    candidate = out.resolve(strict=False)
    prefix = DYNAMIC_OUT_PREFIX.resolve(strict=False)
    try:
        candidate.relative_to(prefix)
    except ValueError as exc:
        raise ValueError(
            f"dynamic output must be below {str(DYNAMIC_OUT_PREFIX)!r}"
        ) from exc


def _validate_backoff_policy_performance_output_path(out: Path) -> None:
    candidate = out.resolve(strict=False)
    prefix = DYNAMIC_POLICY_PERFORMANCE_PREFIX.resolve(strict=False)
    try:
        relative = candidate.relative_to(prefix)
    except ValueError as exc:
        raise ValueError(
            "policy-performance-output-prefix-violation: output must resolve "
            f"below {str(DYNAMIC_POLICY_PERFORMANCE_PREFIX)!r}"
        ) from exc
    if not relative.parts:
        raise ValueError(
            "policy-performance-output-prefix-violation: output must be a true "
            f"child of {str(DYNAMIC_POLICY_PERFORMANCE_PREFIX)!r}"
        )


def _require_child_path(path: Path, root: Path, *, binding: str) -> None:
    candidate = path.resolve(strict=False)
    canonical_root = root.resolve(strict=False)
    try:
        relative = candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise CertificationReject(
            "dynamic-certification-namespace-invalid",
            f"{binding} must be a canonical child of {canonical_root}",
        ) from exc
    if not relative.parts:
        raise CertificationReject(
            "dynamic-certification-namespace-invalid",
            f"{binding} must be a child, not the namespace root",
        )


def _validate_dynamic_certification_namespaces(
    args: argparse.Namespace, cell: Cell
) -> None:
    if cell not in DYNAMIC_CERT_CELLS:
        return
    assert args.group_receipt_out is not None
    assert args.performance_artifact is not None
    _require_child_path(
        args.group_receipt_out,
        DYNAMIC_CERTIFY_PREFIX,
        binding="group receipt",
    )
    for path in args.group_result_path:
        _require_child_path(
            path, DYNAMIC_CERTIFY_PREFIX, binding="group result path"
        )
    _require_child_path(
        Path(args.out), DYNAMIC_CERTIFY_PREFIX, binding="certification output"
    )
    _require_child_path(
        args.performance_artifact,
        DYNAMIC_PERFORMANCE_PREFIX,
        binding="performance artifact",
    )


def _trace_binary_counts(binary: str) -> tuple[int, int]:
    nm = subprocess.run(
        ["nm", "-C", binary], check=True, capture_output=True, text=True
    )
    strings = subprocess.run(
        ["strings", binary], check=True, capture_output=True, text=True
    )
    symbol_count = sum(
        "izanagi_backoff_trace" in line for line in nm.stdout.splitlines()
    )
    string_count = sum(
        "IZANAGI_BACKOFF_TRACE" in line for line in strings.stdout.splitlines()
    )
    return symbol_count, string_count


def _validate_trace_binary_counts(
    symbol_count: int, string_count: int, *, backoff_trace: bool
) -> None:
    if backoff_trace:
        if symbol_count < 1 or string_count < 1:
            raise RuntimeError(
                "diagnostic binary must contain backoff trace symbols and strings"
            )
    elif symbol_count != 0 or string_count != 0:
        raise RuntimeError(
            "trace-disabled binary contains backoff trace symbols or strings"
        )


_TRACE_RECORD_RE = re.compile(
    r"^IZANAGI_BACKOFF_TRACE v=(?P<version>1|2|3) "
    r"seq=(?P<seq>[0-9]+) tsc=(?P<tsc>[0-9]+) "
    r"window_us=(?P<window_us>[0-9]+) "
    r"window_commits=(?P<window_commits>[0-9]+) "
    r"trigger=(?P<trigger>0|1|2|3) "
    r"backoff_before=(?P<backoff_before>[0-9]+(?:[.][0-9]+)?) "
    r"backoff_after=(?P<backoff_after>[0-9]+(?:[.][0-9]+)?) "
    r"gradient_sign=(?P<gradient_sign>-1|0|1) "
    r"step_us=(?P<step_us>[0-9]+(?:[.][0-9]+)?) "
    r"ceiling_us=(?P<ceiling_us>[0-9]+(?:[.][0-9]+)?) "
    r"ceiling_changed=(?P<ceiling_changed>0|1) "
    r"parity_branch=(?P<parity_branch>-1|0|1)"
    r"(?: recommended_delta_sign=(?P<recommended_delta_sign>-1|0|1)"
    r" assigned_invert=(?P<assigned_invert>-1|0|1)"
    r" inversion_realized=(?P<inversion_realized>0|1)"
    r" both_actions_feasible=(?P<both_actions_feasible>0|1)"
    r"(?: terminal_flush=(?P<terminal_flush>0|1))?)?$"
)
_TRACE_TRIGGER_NAMES = {0: "time", 1: "count", 2: "cap", 3: "terminal"}
_TRACE_PARITY_BRANCH_NAMES = {-1: "none", 0: "decrement", 1: "increment"}
_TRACE_SUMMARY_RE = re.compile(
    r"^IZANAGI_BACKOFF_TRACE_SUMMARY v=(?P<version>1|2|3) "
    r"updates=(?P<updates>[0-9]+) retained=(?P<retained>[0-9]+) "
    r"dropped=(?P<dropped>[0-9]+)"
    r"(?: flushes=(?P<flushes>[0-9]+))?$"
)


def _sign(value: Decimal) -> int:
    return (value > 0) - (value < 0)


def _directional_success(events: list[dict]) -> dict:
    scored = 0
    successes = 0
    is_v2 = bool(events) and "assigned_invert" in events[0]
    # These assignment strata are descriptive counts, not a counterfactual
    # estimator.  The next wave must preregister that estimator before use.
    strata = (
        {
            "assigned_forward": [0, 0],
            "assigned_invert": [0, 0],
            "realized_invert": [0, 0],
        }
        if is_v2
        else None
    )
    for current, following in zip(events, events[1:]):
        action = _sign(
            Decimal(str(current["backoff_after"]))
            - Decimal(str(current["backoff_before"]))
        )
        if action == 0:
            continue
        current_tput = Decimal(current["window_commits"]) / Decimal(
            str(current["window_us"])
        )
        following_tput = Decimal(following["window_commits"]) / Decimal(
            str(following["window_us"])
        )
        success = int(action == _sign(following_tput - current_tput))
        scored += 1
        successes += success
        if strata is not None:
            memberships = {
                "assigned_forward": current["assigned_invert"] == 0,
                "assigned_invert": current["assigned_invert"] == 1,
                "realized_invert": current["inversion_realized"] == 1,
            }
            for name, included in memberships.items():
                if included:
                    strata[name][0] += 1
                    strata[name][1] += success
    result = {
        "scored": scored,
        "successes": successes,
        "rate": successes / scored if scored else None,
    }
    if strata is not None:
        for name, (stratum_scored, stratum_successes) in strata.items():
            result[name] = {
                "scored": stratum_scored,
                "successes": stratum_successes,
                "rate": (
                    stratum_successes / stratum_scored
                    if stratum_scored
                    else None
                ),
            }
    return result


def _parse_backoff_trace(
    stdout: str, allow_overflow: bool = False
) -> tuple[list[dict], dict, dict]:
    events = []
    summary = None
    trace_version = None
    for line in stdout.splitlines():
        if not line.startswith("IZANAGI_BACKOFF_TRACE"):
            continue
        record_match = _TRACE_RECORD_RE.fullmatch(line)
        summary_match = _TRACE_SUMMARY_RE.fullmatch(line)
        if record_match is not None:
            if summary is not None:
                raise ValueError("trace record appeared after summary")
            raw = record_match.groupdict()
            version = int(raw["version"])
            tail_present = raw["recommended_delta_sign"] is not None
            terminal_field_present = raw["terminal_flush"] is not None
            if (version in {2, 3}) != tail_present:
                raise ValueError("trace version and counterfactual tail disagree")
            if (version == 3) != terminal_field_present:
                raise ValueError("trace version and terminal field disagree")
            if trace_version is not None and version != trace_version:
                raise ValueError("backoff trace record versions must not mix")
            trace_version = version
            event = {
                "seq": int(raw["seq"]),
                "tsc": int(raw["tsc"]),
                "window_us": int(raw["window_us"]),
                "window_commits": int(raw["window_commits"]),
                "trigger": _TRACE_TRIGGER_NAMES[int(raw["trigger"])],
                "backoff_before": float(raw["backoff_before"]),
                "backoff_after": float(raw["backoff_after"]),
                "gradient_sign": int(raw["gradient_sign"]),
                "step_us": float(raw["step_us"]),
                "ceiling_us": float(raw["ceiling_us"]),
                "ceiling_changed": int(raw["ceiling_changed"]),
                "parity_branch": _TRACE_PARITY_BRANCH_NAMES[
                    int(raw["parity_branch"])
                ],
            }
            if version != 3 and event["trigger"] == "terminal":
                raise ValueError("terminal trigger requires trace version 3")
            if version in {2, 3}:
                event.update(
                    recommended_delta_sign=int(raw["recommended_delta_sign"]),
                    assigned_invert=int(raw["assigned_invert"]),
                    inversion_realized=int(raw["inversion_realized"]),
                    both_actions_feasible=int(raw["both_actions_feasible"]),
                )
                if version == 3:
                    event["terminal_flush"] = int(raw["terminal_flush"])
                is_terminal = version == 3 and event["terminal_flush"] == 1
                if is_terminal:
                    if (
                        event["trigger"] != "terminal"
                        or event["assigned_invert"] != -1
                        or event["recommended_delta_sign"] != 0
                        or event["inversion_realized"] != 0
                        or event["both_actions_feasible"] != 0
                    ):
                        raise ValueError("terminal trace event fields are invalid")
                elif (
                    event["trigger"] == "terminal"
                    or event["assigned_invert"] not in {0, 1}
                ):
                    raise ValueError("nonterminal trace event fields are invalid")
                if not is_terminal and (
                    event["inversion_realized"] > event["assigned_invert"]
                ):
                    raise ValueError(
                        "trace inversion_realized exceeds assigned_invert"
                    )
                if (
                    not is_terminal
                    and event["recommended_delta_sign"] == 0
                    and event["inversion_realized"] != 0
                ):
                    raise ValueError(
                        "zero recommended delta cannot realize an inversion"
                    )
                if not is_terminal and event["inversion_realized"] == 1:
                    applied_delta = Decimal(raw["backoff_after"]) - Decimal(
                        raw["backoff_before"]
                    )
                    recommended_delta = Decimal(
                        event["recommended_delta_sign"]
                    ) * Decimal(raw["step_us"])
                    if applied_delta != -recommended_delta:
                        raise ValueError(
                            "realized inversion is not the exact recommended delta inverse"
                        )
            if event["window_us"] <= 0 or event["step_us"] <= 0:
                raise ValueError("trace window_us and step_us must be positive")
            events.append(event)
        elif summary_match is not None and summary is None:
            raw_summary = summary_match.groupdict()
            summary_version = int(raw_summary.pop("version"))
            flushes_present = raw_summary["flushes"] is not None
            if (summary_version == 3) != flushes_present:
                raise ValueError("trace summary version and flushes field disagree")
            if trace_version is not None and summary_version != trace_version:
                raise ValueError("trace summary version differs from record version")
            summary = {
                key: int(value)
                for key, value in raw_summary.items()
                if value is not None
            }
        else:
            raise ValueError(f"malformed backoff trace line: {line!r}")
    if summary is None:
        raise ValueError("backoff trace summary is missing")
    if not events:
        raise ValueError("backoff trace must contain at least one event")
    if (
        not allow_overflow
        and [event["seq"] for event in events] != list(range(len(events)))
    ):
        raise ValueError("backoff trace seq must be contiguous from zero")
    if any(
        following["tsc"] < current["tsc"]
        for current, following in zip(events, events[1:])
    ):
        raise ValueError("backoff trace tsc must be monotonic")
    terminal_positions = []
    if trace_version == 3:
        terminal_positions = [
            index
            for index, event in enumerate(events)
            if event["terminal_flush"] == 1
        ]
        if terminal_positions not in ([], [len(events) - 1]):
            raise ValueError("v3 trace permits zero terminals or one final terminal")
    if allow_overflow:
        updates = summary["updates"]
        retained = summary["retained"]
        dropped = summary["dropped"]
        sequence = [event["seq"] for event in events]
        if (
            updates != retained + dropped
            or retained != min(updates, 65_536)
            or len(events) != retained
            or sequence[0] != dropped
            or sequence[-1] != updates - 1
            or sequence != list(range(dropped, updates))
            or (
                trace_version == 3
                and summary["flushes"] != len(terminal_positions)
            )
        ):
            raise ValueError("backoff trace overflow contract failed")
    else:
        if trace_version == 3:
            expected_summary = {
                "updates": len(events) - len(terminal_positions),
                "retained": len(events) - len(terminal_positions),
                "dropped": 0,
                "flushes": len(terminal_positions),
            }
        else:
            expected_summary = {
                "updates": len(events),
                "retained": len(events),
                "dropped": 0,
            }
        if summary != expected_summary:
            raise ValueError("backoff trace summary/count or dropped contract failed")
    return events, summary, _directional_success(events)


def _capturing_subprocess_runner(chunks: list[str]):
    def run(*args, **kwargs):
        completed = subprocess.run(*args, **kwargs)
        stdout = completed.stdout
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="strict")
        if isinstance(stdout, str):
            chunks.append(stdout)
        return completed

    return run


def _append_journal(out: Path, row: dict) -> None:
    journal = Path(str(out) + ".journal.jsonl")
    journal.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
    with journal.open("a", encoding="utf-8") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def _certification_protocol(genome: Genome) -> str:
    protocol = getattr(genome, "protocol", None)
    if protocol != CERT_PROTOCOL:
        raise CertificationReject(
            "certification-protocol-mismatch",
            f"certify requires genome protocol {CERT_PROTOCOL!r}, got {protocol!r}",
        )
    return protocol


def _cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def _assert_single_tenant() -> None:
    """Load the existing tenant gate only after a concrete mode is selected."""
    from orchestrator.campaign.p2_2 import _assert_single_tenant as check

    check()


def _validate_output_path(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")


def _positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive number") from exc
    if not value > 0:
        raise argparse.ArgumentTypeError("must be a positive number")
    return value


def _certification_contract(
    args: argparse.Namespace,
) -> tuple[CertificationAxes, str]:
    """Return the exact one-request certification axes or reject widening."""
    if (
        args.step_policy_seed is not None
        and args.cells != CERT_COHORT2_POLICY2_CELL_TEXT
    ):
        raise CertificationReject(
            "step-policy-seed-certification-conflict",
            "--step-policy-seed cannot be combined with this certification cell",
        )
    expected_cell = CERT_CELL_BY_TEXT.get(args.cells)
    if expected_cell is None:
        raise CertificationReject(
            "certification-cell-mismatch",
            "certify requires one exact preregistered cell string",
        )
    cells = parse_cells(args.cells)
    workloads = _parse_workloads(args.workloads)
    if type(args.threads) is not str or _INTEGER_RE.fullmatch(args.threads) is None:
        raise CertificationReject(
            "certification-workload-shape-mismatch",
            "certify requires one canonical raw thread literal",
        )
    threads = _parse_threads(args.threads)
    if len(cells) != 1 or cells[0] != expected_cell:
        raise CertificationReject(
            "certification-cell-mismatch",
            "certify requires exactly one of the four preregistered cells",
        )
    if len(workloads) != 1 or workloads[0] not in CERT_WORKLOADS:
        raise CertificationReject(
            "certification-workload-mismatch",
            "certify requires exactly one of write-heavy, balanced, read-heavy",
        )
    expected_extime = CERT_EXTIME_BY_CELL[expected_cell]
    allowed_threads = CERT_THREADS_BY_CELL[expected_cell]
    if (
        len(threads) != 1
        or args.threads != str(threads[0])
        or threads[0] not in allowed_threads
        or args.extime != expected_extime
    ):
        raise CertificationReject(
            "certification-workload-shape-mismatch",
            "certify requires records=1000000, one exact cell-allowed thread "
            "literal, and the exact cell-specific extime",
        )
    if expected_cell == CERT_COHORT2_POLICY2_CELL:
        if args.step_policy_seed is None:
            raise CertificationReject(
                "certification-step-policy-seed-missing",
                "policy 2 certification requires an explicit step-policy seed",
            )
        if args.step_policy_seed not in CERT_POLICY2_STEP_POLICY_SEEDS:
            raise CertificationReject(
                "certification-step-policy-seed-mismatch",
                "policy 2 certification seed is outside the exact closed table",
            )
        compile_seed = args.step_policy_seed
    elif expected_cell == CERT_COHORT2_POLICY1_CELL:
        compile_seed = STOCK_STEP_POLICY_SEED
    else:
        compile_seed = None
    axes = _make_certification_axes(
        expected_cell,
        threads[0],
        compile_seed,
        reason="certification-workload-shape-mismatch",
        detail="certification axes are outside the exact cell contract",
    )
    if args.reps_per_job != CERT_REPS_PER_JOB:
        raise CertificationReject(
            "certification-repetition-mismatch",
            "certify requires reps-per-job=1",
        )
    if args.rep_index not in CERT_SLOTS:
        raise CertificationReject(
            "certification-slot-mismatch",
            "certify requires rep-index in 0..7",
        )
    if (
        args.group_receipt_out is None
        or args.performance_artifact is None
        or args.performance_artifact_sha256 is None
        or args.expected_verifier_identity is None
        or args.expected_verifier_identity_sha256 is None
        or args.attempt_id is None
    ):
        raise CertificationReject(
            "certification-group-binding-missing",
            "certify requires group, performance, verifier, and attempt bindings",
        )
    if _LABEL_RE.fullmatch(args.attempt_id) is None:
        raise CertificationReject(
            "certification-attempt-invalid", "attempt id is not a safe exact label"
        )
    if any(
        not path.is_absolute()
        for path in (
            args.group_receipt_out,
            args.performance_artifact,
            args.expected_verifier_identity,
        )
    ):
        raise CertificationReject(
            "certification-group-binding-invalid",
            "group/performance/verifier binding paths must be absolute",
        )
    if (
        type(args.prologue_elapsed_s) is not float
        or args.prologue_elapsed_s < 0
        or type(args.prologue_cpu_s) is not float
        or args.prologue_cpu_s < 0
    ):
        raise CertificationReject(
            "certification-prologue-measurement-invalid",
            "prologue elapsed/CPU measurements must be nonnegative",
        )
    result_paths = [path.resolve(strict=False) for path in args.group_result_path]
    if (
        len(result_paths) != 24
        or len(set(result_paths)) != 24
        or any(not path.is_absolute() for path in args.group_result_path)
        or Path(args.out).resolve(strict=False) not in set(result_paths)
    ):
        raise CertificationReject(
            "certification-result-path-set-invalid",
            "certify requires 24 unique absolute result paths including --out",
        )
    inner_budget = (
        args.prologue_budget_s
        + args.build_budget_s
        + RUN_TIMEOUT_S
        + POSITIVE_CONTROL_TIMEOUT_S
        + args.verifier_timeout_s
        + args.exit_margin_s
    )
    if not inner_budget < args.outer_walltime_s:
        raise CertificationReject(
            "certification-time-budget-invalid",
            "build + run + positive-control + target-verifier + exit margin "
            "must be strictly below the outer walltime",
        )
    return axes, workloads[0]


def _validate_verifier_identity_shape(identity: object) -> dict:
    if type(identity) is not dict or set(identity) != {
        "repository_commit",
        "module_sha256",
    }:
        raise CertificationReject(
            "verifier-identity-invalid", "verifier identity has an invalid schema"
        )
    commit = identity.get("repository_commit")
    modules = identity.get("module_sha256")
    if (
        type(commit) is not str
        or _COMMIT_RE.fullmatch(commit) is None
        or type(modules) is not dict
        or not modules
        or any(
            type(name) is not str
            or not name
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
            for name, digest in modules.items()
        )
    ):
        raise CertificationReject(
            "verifier-identity-invalid",
            "verifier commit/modules are not exact full identities",
        )
    return identity


def _load_expected_verifier_identity(
    path: Path, expected_file_sha256: str
) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
        identity = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "verifier-identity-invalid", "expected verifier identity is unavailable"
        ) from exc
    actual_file_sha256 = hashlib.sha256(raw).hexdigest()
    if (
        type(expected_file_sha256) is not str
        or _SHA256_RE.fullmatch(expected_file_sha256) is None
        or actual_file_sha256 != expected_file_sha256
    ):
        raise CertificationReject(
            "verifier-identity-mismatch",
            "expected verifier identity file does not match its preregistered SHA",
        )
    validated = _validate_verifier_identity_shape(identity)
    return validated, actual_file_sha256


def _require_expected_verifier_identity(actual: object, expected: dict) -> None:
    if _validate_verifier_identity_shape(actual) != expected:
        raise CertificationReject(
            "verifier-identity-mismatch",
            "verifier closure does not match the preregistered identity",
        )


def _build_worker(connection, builder) -> None:
    """Run one build in its own process group and return a pickled result."""
    try:
        os.setsid()
        connection.send(("ok", builder()))
    except BaseException as exc:  # child boundary: parent converts to one reject
        connection.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        connection.close()


def _run_build_with_deadline(builder, timeout_s: float):
    """Enforce the build budget while also terminating spawned descendants."""
    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_build_worker, args=(sender, builder))
    process.start()
    sender.close()
    if not receiver.poll(timeout_s):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            process.terminate()
        process.join(timeout=2.0)
        if process.is_alive():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                process.kill()
            process.join()
        receiver.close()
        raise CertificationReject(
            "trace-build-budget-exceeded",
            "trace build exceeded its preregistered hard deadline",
        )
    try:
        status, value = receiver.recv()
    except EOFError as exc:
        raise RuntimeError("trace build worker exited without a result") from exc
    finally:
        receiver.close()
        process.join()
    if status != "ok":
        raise RuntimeError(f"trace build failed in deadline worker: {value}")
    if process.exitcode != 0:
        raise RuntimeError(f"trace build worker exited {process.exitcode}")
    return value


def _phase_measurement(started_wall: float, started_cpu: float) -> dict:
    elapsed = max(0.0, time.monotonic() - started_wall)
    cpu = max(0.0, _cpu_seconds() - started_cpu)
    return {
        "elapsed_seconds": elapsed,
        "cpu_seconds": cpu,
        "cpu_over_elapsed": cpu / elapsed if elapsed > 0 else None,
    }


def _verifier_identity() -> dict:
    """Bind the verifier entry and complete Python package closure."""
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10.0,
    ).stdout.strip()
    paths = [VERIFIER_ENTRY, *sorted(VERIFIER_PACKAGE.glob("*.py"))]
    modules = {}
    for path in paths:
        if not path.is_file():
            raise CertificationReject(
                "verifier-identity-unavailable", f"missing verifier module: {path}"
            )
        modules[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return {"repository_commit": commit, "module_sha256": modules}


def _verifier_argv(
    trace_dir: Path,
    expected_commits: int,
    protocol: str,
    ccbench_root: Path,
) -> list[str]:
    return [
        sys.executable,
        "-B",
        "orchestrator/verify.py",
        str(trace_dir.resolve(strict=True)),
        "--json",
        "--expected-commits",
        str(expected_commits),
        "--protocol",
        protocol,
        "--ccbench-root",
        str(ccbench_root.resolve(strict=True)),
    ]


def _run_verifier(
    trace_dir: Path,
    expected_commits: int,
    timeout_s: float,
    protocol: str,
    ccbench_root: Path,
) -> dict:
    """Run the exact verifier child and collect per-child CPU/RSS with wait4."""
    argv = _verifier_argv(trace_dir, expected_commits, protocol, ccbench_root)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        proc = subprocess.Popen(
            argv,
            cwd=ROOT,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
        )
        status = None
        usage = None
        while status is None:
            waited_pid, waited_status, waited_usage = os.wait4(proc.pid, os.WNOHANG)
            if waited_pid == proc.pid:
                status = waited_status
                usage = waited_usage
                break
            if time.monotonic() - started >= timeout_s:
                timed_out = True
                proc.kill()
                _waited_pid, status, usage = os.wait4(proc.pid, 0)
                break
            time.sleep(0.05)
        assert status is not None and usage is not None
        proc.returncode = os.waitstatus_to_exitcode(status)
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")
    elapsed = max(0.0, time.monotonic() - started)
    cpu = max(0.0, usage.ru_utime + usage.ru_stime)
    parsed = None
    parse_error = None
    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        parse_error = f"{type(exc).__name__}: {exc}"
    return {
        "argv": argv,
        "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
        "exit_code": proc.returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout_s,
        "elapsed_seconds": elapsed,
        "cpu_seconds": cpu,
        "cpu_over_elapsed": cpu / elapsed if elapsed > 0 else None,
        "max_rss_kib": usage.ru_maxrss,
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed,
        "json_parse_error": parse_error,
    }


def _normalized_path(value: object) -> str | None:
    if type(value) is not str:
        return None
    try:
        return str(Path(value).resolve(strict=True))
    except (OSError, RuntimeError):
        return None


def _single_result(invocation: dict, reason_prefix: str) -> tuple[dict, dict]:
    document = invocation.get("json")
    if type(document) is not dict or type(document.get("results")) is not list:
        raise CertificationReject(
            f"{reason_prefix}-json-invalid", "verifier did not return structured JSON"
        )
    if len(document["results"]) != 1 or type(document["results"][0]) is not dict:
        raise CertificationReject(
            f"{reason_prefix}-json-invalid", "verifier must return exactly one result"
        )
    return document, document["results"][0]


def _verifier_argv_has_exact_surface(
    invocation: dict,
    *,
    protocol: str,
    ccbench_root: Path,
) -> None:
    argv = invocation.get("argv")
    expected_root = str(ccbench_root.resolve(strict=False))

    def exact_option(option: str, expected: str) -> bool:
        if type(argv) is not list or argv.count(option) != 1:
            return False
        index = argv.index(option)
        return index + 1 < len(argv) and argv[index + 1] == expected

    if (
        type(argv) is not list
        or argv[:3] != [sys.executable, "-B", "orchestrator/verify.py"]
        or "--lenient" in argv
        or not exact_option("--protocol", protocol)
        or not exact_option("--ccbench-root", expected_root)
    ):
        raise CertificationReject(
            "verifier-argv-contract",
            "verifier argv must use python -B without --lenient and bind the "
            "exact protocol/source checkout proof surface",
        )


def _validate_positive_control(
    invocation: dict,
    protocol: str,
    ccbench_root: Path,
) -> None:
    _verifier_argv_has_exact_surface(
        invocation, protocol=protocol, ccbench_root=ccbench_root
    )
    if invocation.get("timed_out") is not False or invocation.get("exit_code") != 1:
        raise CertificationReject(
            "positive-control-exit", "static broken-Silo fixture must exit exactly 1"
        )
    document, result = _single_result(invocation, "positive-control")
    if (
        document.get("runs") != 1
        or document.get("non_serializable") != 1
        or document.get("certified_serializable") != 0
        or result.get("verdict") != "non-serializable"
        or result.get("certified") is not False
        or _normalized_path(result.get("trace_dir"))
        != str(POSITIVE_CONTROL_TRACE.resolve(strict=True))
        or result.get("total_cycles") != 4
    ):
        raise CertificationReject(
            "positive-control-contract", "broken-Silo aggregate/result contract mismatch"
        )
    anomalies = result.get("anomalies")
    if type(anomalies) is not list or not anomalies:
        raise CertificationReject(
            "positive-control-anomalies", "broken-Silo fixture has no anomaly witness"
        )
    saw_rw = False
    for anomaly in anomalies:
        if type(anomaly) is not dict or anomaly.get("phenomenon") != "G2":
            raise CertificationReject(
                "positive-control-phenomenon", "every positive-control anomaly must be G2"
            )
        edges = anomaly.get("edges")
        if type(edges) is not list or not edges:
            raise CertificationReject(
                "positive-control-edge", "every G2 witness must have edges"
            )
        for edge in edges:
            if (
                type(edge) is not dict
                or type(edge.get("from")) is not int
                or type(edge.get("to")) is not int
                or type(edge.get("reasons")) is not list
                or not edge["reasons"]
            ):
                raise CertificationReject(
                    "positive-control-edge", "every edge must have endpoints and reasons"
                )
            for reason in edge["reasons"]:
                if type(reason) is not dict or reason.get("type") not in {"ww", "wr", "rw"}:
                    raise CertificationReject(
                        "positive-control-reason", "unknown or malformed edge reason"
                    )
                required = {"type", "key", "u_ver"}
                if reason["type"] in {"ww", "rw"}:
                    required.add("v_ver")
                if not required.issubset(reason) or not reason.get("key"):
                    raise CertificationReject(
                        "positive-control-version", "edge reason lacks type-specific versions"
                    )
                saw_rw = saw_rw or reason["type"] == "rw"
    if not saw_rw:
        raise CertificationReject(
            "positive-control-rw-missing", "positive control must contain an rw reason"
        )


def _validate_target(
    invocation: dict,
    trace_dir: Path,
    trace_result: object,
    expected_verifier_identity: dict,
    verifier_identity_after: dict,
    protocol: str,
    ccbench_root: Path,
) -> tuple[dict, dict]:
    _require_expected_verifier_identity(
        verifier_identity_after, expected_verifier_identity
    )
    _verifier_argv_has_exact_surface(
        invocation, protocol=protocol, ccbench_root=ccbench_root
    )
    if invocation.get("timed_out") is not False or invocation.get("exit_code") != 0:
        raise CertificationReject(
            "target-verifier-exit", "target verifier must exit exactly 0"
        )
    document, result = _single_result(invocation, "target")
    if _normalized_path(result.get("trace_dir")) != str(trace_dir.resolve(strict=True)):
        raise CertificationReject(
            "target-trace-dir-mismatch", "verifier result is not bound to the generated trace"
        )
    if (
        document.get("runs") != 1
        or document.get("certified_serializable") != 1
        or document.get("non_serializable") != 0
        or document.get("indeterminate") != 0
        or result.get("verdict") != "serializable"
        or result.get("certified") is not True
        or result.get("anomalies") != []
    ):
        raise CertificationReject(
            "target-verdict", "target is not exactly one certified serializable result"
        )
    integrity = result.get("integrity")
    if type(integrity) is not dict or integrity.get("clean") is not True:
        raise CertificationReject("target-integrity", "target integrity is not clean")
    stats = result.get("stats")
    if type(stats) is not dict:
        raise CertificationReject("target-stats", "target stats are missing")
    for field, lower_bound in (("txns", 2), ("reads", 1), ("writes", 1), ("edges", 1)):
        value = stats.get(field)
        if type(value) is not int or value < lower_bound:
            reason = "target-edges-empty" if field == "edges" else f"target-{field}-empty"
            raise CertificationReject(reason, f"target stats.{field} is below {lower_bound}")
    abort_count_stdout = getattr(trace_result, "abort_counts", None)
    if type(abort_count_stdout) is not int or abort_count_stdout <= 0:
        raise CertificationReject(
            "target-abort-empty",
            "target abort_count_stdout must be a positive exact integer",
        )
    if (
        getattr(trace_result, "returncode", None) != 0
        or getattr(trace_result, "commit_count_witness", None) is None
        or getattr(trace_result, "batch_commit_count_witness", None) != 0
        or getattr(trace_result, "trace_c_lines", None)
        != getattr(trace_result, "commit_count_witness", None)
    ):
        raise CertificationReject(
            "target-commit-witness", "run rc/commit line/batch/trace-C witness mismatch"
        )
    return document, result


def _trace_manifest(trace_dir: Path) -> dict:
    files = []
    total_bytes = 0
    total_lines = 0
    for path in sorted(trace_dir.glob("trace_*.log")):
        size = path.stat().st_size
        digest = hashlib.sha256()
        lines = 0
        last_byte = b""
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                lines += chunk.count(b"\n")
                last_byte = chunk[-1:]
        if size and last_byte != b"\n":
            lines += 1
        files.append(
            {
                "name": path.name,
                "size_bytes": size,
                "lines": lines,
                "sha256": digest.hexdigest(),
            }
        )
        total_bytes += size
        total_lines += lines
    return {
        "file_count": len(files),
        "bytes": total_bytes,
        "lines": total_lines,
        "files": files,
    }


def _write_json_create_only(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def _performance_artifact_identity(
    path: Path,
    expected_sha256: str,
    *,
    expected_repo_head: str | None = None,
    expected_prereg_sha256: str | None = None,
    expected_patch_stack_sha256: str | None = None,
    required_cell: Cell | None = None,
    expected_extime: int | None = None,
    expected_axes: CertificationAxes | None = None,
) -> dict:
    if type(expected_sha256) is not str or _SHA256_RE.fullmatch(expected_sha256) is None:
        raise CertificationReject(
            "performance-artifact-identity-mismatch",
            "expected performance artifact sha256 is not exact",
        )
    raw = path.read_bytes()
    try:
        document = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "performance-artifact-invalid", "performance artifact is not JSON"
        ) from exc
    registered_cohort2_identity = required_cell in {
        CERT_COHORT2_POLICY1_CELL,
        CERT_COHORT2_POLICY2_CELL,
    }
    if type(document) is dict and (
        "performance_contract" in document
        or (
            _contains_step_policy_cell(document)
            and not registered_cohort2_identity
        )
    ):
        raise CertificationReject(
            "performance-artifact-contract-rejected",
            "policy performance artifacts cannot satisfy certification performance "
            "artifact requirements",
        )
    if (
        type(document) is not dict
        or document.get("schema_version")
        not in {LEGACY_SCHEMA_VERSION, SCHEMA_VERSION}
        or document.get("kind") != "performance-only-probe"
        or document.get("not_certified") != NOT_CERTIFIED
    ):
        raise CertificationReject(
            "performance-artifact-invalid",
            "performance artifact lacks the exact performance-only identity",
        )
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise CertificationReject(
            "performance-artifact-identity-mismatch",
            "performance artifact does not match the preregistered path/SHA",
        )
    expected_values = (
        expected_repo_head,
        expected_prereg_sha256,
        expected_patch_stack_sha256,
        required_cell,
        expected_extime,
        expected_axes,
    )
    if any(value is not None for value in expected_values):
        if any(value is None for value in expected_values):
            raise CertificationReject(
                "performance-artifact-identity-mismatch",
                "dynamic performance identity expectations are incomplete",
            )
        assert required_cell is not None and expected_axes is not None
        cells = document.get("cells")
        expected_cell_identity = _cell_identity(required_cell)
        if expected_axes.cell != required_cell:
            raise CertificationReject(
                "performance-artifact-identity-mismatch",
                "dynamic performance identity expects inconsistent cell axes",
            )
        matching_rows = (
            [
                row
                for row in cells
                if type(row) is dict
                and {key: row.get(key) for key in expected_cell_identity}
                == expected_cell_identity
            ]
            if type(cells) is list
            else []
        )
        if (
            (
                expected_patch_stack_sha256
                == _patch_stack_identity()["patch_stack_sha256"]
                and document.get("schema_version") != SCHEMA_VERSION
            )
            or document.get("repo_head") != expected_repo_head
            or document.get("prereg_sha256") != expected_prereg_sha256
            or document.get("patch_stack_sha256")
            != expected_patch_stack_sha256
            or document.get("extime_s") != expected_extime
            or type(cells) is not list
            or not matching_rows
            or not any(
                type(row.get("threads")) is int
                and row["threads"] == expected_axes.threads
                for row in matching_rows
            )
        ):
            raise CertificationReject(
                "performance-artifact-identity-mismatch",
                "dynamic performance artifact identity/cell does not match certify",
            )
        _validate_recorded_execution_identity(
            document, reason="performance-artifact-identity-mismatch"
        )
        if document.get("ccbench_head") != PIN_FULL:
            raise CertificationReject(
                "performance-artifact-identity-mismatch",
                "dynamic performance artifact lacks the full ccbench pin",
            )
        if required_cell in {
            CERT_COHORT2_POLICY1_CELL,
            CERT_COHORT2_POLICY2_CELL,
        }:
            expected_genome = genome_for(
                required_cell,
                step_policy_seed=expected_axes.step_policy_seed,
            ).canonical()
            expected_seed = expected_axes.step_policy_seed
            if (
                any(row.get("genome") != expected_genome for row in matching_rows)
                or (
                    required_cell == CERT_COHORT2_POLICY2_CELL
                    and any(
                        row.get("step_policy_seed") != expected_seed
                        for row in matching_rows
                    )
                )
                or (
                    required_cell == CERT_COHORT2_POLICY1_CELL
                    and any("step_policy_seed" in row for row in matching_rows)
                )
            ):
                raise CertificationReject(
                    "performance-artifact-identity-mismatch",
                    "cohort 2 performance artifact is not the exact request-seed "
                    "certification build identity",
                )
    return {
        "path": str(path.resolve(strict=True)),
        "sha256": actual_sha256,
    }


@dataclass(frozen=True)
class _ReceiptTraceResult:
    trace_c_lines: object
    returncode: object
    abort_counts: object
    commit_count_witness: object
    batch_commit_count_witness: object


def _validated_proof_surface(document: dict) -> dict:
    proof_surface = document.get("proof_surface")
    source_evidence = document.get("source_evidence")
    if type(proof_surface) is not dict or set(proof_surface) != {
        "protocol",
        "ccbench_root",
        "source_snapshot_identity",
    }:
        raise CertificationReject(
            "group-proof-surface-mismatch", "proof-surface binding schema is invalid"
        )
    ccbench_root = proof_surface.get("ccbench_root")
    if (
        proof_surface.get("protocol") != CERT_PROTOCOL
        or type(ccbench_root) is not str
        or not Path(ccbench_root).is_absolute()
        or str(Path(ccbench_root).resolve(strict=False)) != ccbench_root
        or proof_surface.get("source_snapshot_identity") != source_evidence
    ):
        raise CertificationReject(
            "group-proof-surface-mismatch",
            "proof surface is not bound to Silo and the recorded source evidence",
        )
    return proof_surface


def _validate_trace_manifest_receipt(trace_dir: Path, manifest: object) -> None:
    if not (trace_dir / "log").is_dir():
        raise CertificationReject(
            "group-trace-dir-invalid", "raw trace directory no longer has log/"
        )
    if type(manifest) is not dict or set(manifest) != {
        "file_count",
        "bytes",
        "lines",
        "files",
    }:
        raise CertificationReject(
            "group-trace-manifest-mismatch", "trace manifest schema is invalid"
        )
    files = manifest.get("files")
    if (
        type(files) is not list
        or not files
        or manifest.get("file_count") != len(files)
        or type(manifest.get("bytes")) is not int
        or manifest["bytes"] <= 0
        or type(manifest.get("lines")) is not int
        or manifest["lines"] <= 0
    ):
        raise CertificationReject(
            "group-trace-manifest-mismatch", "trace manifest totals are invalid"
        )
    names = set()
    total_bytes = 0
    total_lines = 0
    for item in files:
        if type(item) is not dict or set(item) != {
            "name",
            "size_bytes",
            "lines",
            "sha256",
        }:
            raise CertificationReject(
                "group-trace-manifest-mismatch", "trace file manifest is invalid"
            )
        name = item.get("name")
        size = item.get("size_bytes")
        lines = item.get("lines")
        digest = item.get("sha256")
        if (
            type(name) is not str
            or re.fullmatch(r"trace_[0-9]+\.log", name) is None
            or name in names
            or type(size) is not int
            or size <= 0
            or type(lines) is not int
            or lines <= 0
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise CertificationReject(
                "group-trace-manifest-mismatch", "trace file metadata is invalid"
            )
        trace_file = trace_dir / name
        if not trace_file.is_file() or trace_file.stat().st_size != size:
            raise CertificationReject(
                "group-trace-manifest-mismatch",
                "raw trace is missing or its size differs before aggregation",
            )
        names.add(name)
        total_bytes += size
        total_lines += lines
    if total_bytes != manifest["bytes"] or total_lines != manifest["lines"]:
        raise CertificationReject(
            "group-trace-manifest-mismatch", "trace manifest totals do not add up"
        )


def _validated_certification_row(
    path: Path,
    *,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
    performance_identity: dict,
) -> tuple[dict, tuple[str, int]]:
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-result-invalid", f"certification result is unreadable: {path}"
        ) from exc
    if (
        type(document) is dict
        and document.get("schema_version")
        == UNSUPPORTED_V2_CERTIFICATION_SCHEMA_VERSION
    ):
        raise CertificationReject(
            "legacy-certification-schema-unsupported",
            "v2 certification artifacts are unsupported; group aggregation "
            "accepts v3 certification artifacts only",
        )
    if (
        type(document) is not dict
        or document.get("schema_version") != CERTIFICATION_SCHEMA_VERSION
        or document.get("kind") != "correctness-certification-request"
        or document.get("terminal_status") != "certified"
        or document.get("certified") is not True
        or document.get("certification_gate") != "all-10-conditions-passed"
        or document.get("attempt_id") != attempt_id
        or document.get("performance_artifact") != performance_identity
    ):
        raise CertificationReject(
            "group-result-not-certified",
            f"result is not one certified receipt for attempt {attempt_id}: {path}",
        )
    workload = document.get("workload")
    slot = document.get("independent_run_slot")
    if workload not in CERT_WORKLOADS or type(slot) is not int or slot not in CERT_SLOTS:
        raise CertificationReject(
            "group-result-invalid", f"result workload/slot is invalid: {path}"
        )
    cell = _cell_from_document(document)
    expected_extime = CERT_EXTIME_BY_CELL.get(cell)
    if expected_extime is None:
        raise CertificationReject(
            "group-workload-contract-mismatch",
            f"result cell is not an exact certification cell: {path}",
        )
    axes = _certification_axes_from_document(
        document,
        cell=cell,
        reason="group-workload-contract-mismatch",
        detail=f"result thread/seed axes are outside the closed table: {path}",
    )
    expected_workload_flags = {
        **WORKLOADS[workload],
        "ycsb_tuple_num": str(CERT_RECORDS),
        "thread_num": str(axes.threads),
        "extime": str(expected_extime),
    }
    if (
        document.get("workload_flags") != expected_workload_flags
        or document.get("records") != CERT_RECORDS
        or document.get("extime_s") != expected_extime
        or document.get("cell_order") != [cell.label]
        or document.get("allowed_group_claim") != _certification_claim(axes)
        or document.get("prereg_sha256")
        != _certification_prereg_sha256(cell)
        or document.get("rng_seed_controlled") is not False
    ):
        raise CertificationReject(
            "group-workload-contract-mismatch",
            f"result workload constants/flags are invalid: {path}",
        )
    request_id = document.get("pbs_jobid")
    if type(request_id) is not str or not request_id:
        raise CertificationReject(
            "group-result-invalid", f"result request id is invalid: {path}"
        )
    actual_identity = _validate_verifier_identity_shape(
        document.get("verifier_identity")
    )
    _require_expected_verifier_identity(actual_identity, expected_verifier_identity)
    if document.get("expected_verifier_identity_file_sha256") != (
        expected_verifier_identity_file_sha256
    ):
        raise CertificationReject(
            "group-verifier-identity-mismatch",
            "result is not bound to the preregistered verifier manifest file",
        )
    expected_patch_identity = _patch_stack_identity()
    execution_identity = _validate_recorded_execution_identity(
        document, reason="group-build-identity-mismatch"
    )
    if cell == CERT_COHORT2_POLICY2_CELL:
        driver_argv = execution_identity["driver_argv"]
        option = "--step-policy-seed"
        if (
            driver_argv.count(option) != 1
            or driver_argv.index(option) + 1 >= len(driver_argv)
            or driver_argv[driver_argv.index(option) + 1]
            != str(axes.step_policy_seed)
        ):
            raise CertificationReject(
                "group-workload-contract-mismatch",
                f"result driver argv does not bind the policy 2 seed: {path}",
            )
    expected_genome = genome_for(
        cell, step_policy_seed=axes.step_policy_seed
    ).canonical()
    expected_genome_sha256 = hashlib.sha256(
        expected_genome.encode("utf-8")
    ).hexdigest()
    if (
        document.get("build_trace_enabled") is not True
        or type(document.get("build_cache_key")) is not str
        or not document["build_cache_key"].endswith("_t1")
        or type(document.get("binary_sha256")) is not str
        or _SHA256_RE.fullmatch(document["binary_sha256"]) is None
        or any(
            document.get(key) != value
            for key, value in expected_patch_identity.items()
        )
        or document.get("ccbench_commit") != PIN_FULL
        or document.get("ccbench_head") != PIN_FULL
        or document.get("genome") != expected_genome
        or type(document.get("repo_head")) is not str
        or _COMMIT_RE.fullmatch(document["repo_head"]) is None
        or type(document.get("hostname")) is not str
        or not document["hostname"]
        or document.get("backoff_trace_symbol_count") != 0
        or document.get("backoff_trace_string_count") != 0
        or document.get("backoff_trace") is not False
        or type(document.get("build_admission_receipt_sha256")) is not str
        or _SHA256_RE.fullmatch(document["build_admission_receipt_sha256"]) is None
        or type(document.get("source_evidence")) is not dict
        or document["source_evidence"].get("ccbench_commit") != CURRENT_PIN
        or type(document["source_evidence"].get("genome_sha256")) is not str
        or _SHA256_RE.fullmatch(
            document["source_evidence"]["genome_sha256"]
        )
        is None
        or document["source_evidence"]["genome_sha256"]
        != expected_genome_sha256
        or type(document["source_evidence"].get("source_bytes_sha256")) is not str
        or _SHA256_RE.fullmatch(
            document["source_evidence"]["source_bytes_sha256"]
        )
        is None
    ):
        raise CertificationReject(
            "group-build-identity-mismatch",
            f"result build/pin/patch/trace identity is invalid: {path}",
        )
    proof_surface = _validated_proof_surface(document)
    trace_value = document.get("trace_directory")
    normalized_trace = _normalized_path(trace_value)
    if normalized_trace is None or normalized_trace != trace_value:
        raise CertificationReject(
            "group-trace-dir-invalid", f"result trace_dir is not exact: {path}"
        )
    trace_dir = Path(normalized_trace)
    _validate_trace_manifest_receipt(trace_dir, document.get("trace_manifest"))
    positive = document.get("positive_control")
    if type(positive) is not dict:
        raise CertificationReject(
            "group-result-invalid", f"positive-control receipt is missing: {path}"
        )
    try:
        positive_stdout_json = json.loads(positive.get("stdout"))
    except (TypeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-result-invalid", f"positive-control stdout is invalid: {path}"
        ) from exc
    if positive.get("json_parse_error") is not None or positive_stdout_json != positive.get(
        "json"
    ):
        raise CertificationReject(
            "group-result-invalid", f"positive-control JSON binding differs: {path}"
        )
    proof_protocol = proof_surface["protocol"]
    proof_root = Path(proof_surface["ccbench_root"])
    _validate_positive_control(positive, proof_protocol, proof_root)
    run = document.get("run")
    target = document.get("target_verifier")
    if type(run) is not dict or type(target) is not dict:
        raise CertificationReject(
            "group-result-invalid", f"run/verifier receipt is missing: {path}"
        )
    try:
        target_stdout_json = json.loads(target.get("stdout"))
    except (TypeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-result-invalid", f"target verifier stdout is invalid: {path}"
        ) from exc
    if target.get("json_parse_error") is not None or target_stdout_json != target.get(
        "json"
    ):
        raise CertificationReject(
            "group-result-invalid", f"target verifier JSON binding differs: {path}"
        )
    trace_result = _ReceiptTraceResult(
        trace_c_lines=run.get("trace_c_lines"),
        returncode=run.get("exit_code"),
        abort_counts=run.get("abort_count_stdout"),
        commit_count_witness=run.get("commit_count"),
        batch_commit_count_witness=run.get("batch_commit_count"),
    )
    target_document, target_result = _validate_target(
        target,
        trace_dir,
        trace_result,
        expected_verifier_identity,
        actual_identity,
        proof_protocol,
        proof_root,
    )
    if document.get("verifier_json") != target_document:
        raise CertificationReject(
            "group-result-invalid", f"verifier JSON binding differs: {path}"
        )
    abort_reasons = target_result.get("stats", {}).get("abort_reasons")
    if type(abort_reasons) is not dict or any(
        type(value) is not int or value < 0 for value in abort_reasons.values()
    ):
        raise CertificationReject(
            "group-result-invalid", f"abort reason information is malformed: {path}"
        )
    return (
        {
            "path": str(path.resolve(strict=True)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "workload": workload,
            "independent_run_slot": slot,
            "request_id": request_id,
            "terminal_status": "certified",
            "certified": True,
            "trace_dir": normalized_trace,
            "verifier_identity": actual_identity,
            "binary_sha256": document["binary_sha256"],
            "build_cache_key": document["build_cache_key"],
            "build_trace_enabled": document["build_trace_enabled"],
            "build_admission_receipt_sha256": document[
                "build_admission_receipt_sha256"
            ],
            "source_evidence": {
                **document["source_evidence"],
            },
            "proof_surface": proof_surface,
            "genome": document["genome"],
            **_cell_identity(cell),
            "cell_order": document["cell_order"],
            "claim": document["allowed_group_claim"],
            "workload_flags": document["workload_flags"],
            "records": document["records"],
            "threads": document["threads"],
            "extime_s": document["extime_s"],
            "patch_sha256": document["patch_sha256"],
            "dynamic_patch_sha256": document["dynamic_patch_sha256"],
            "counterfactual_patch_sha256": document[
                "counterfactual_patch_sha256"
            ],
            "patch_stack": document["patch_stack"],
            "patch_stack_sha256": document["patch_stack_sha256"],
            "ccbench_commit": document["ccbench_commit"],
            "ccbench_head": document["ccbench_head"],
            "repo_head": document["repo_head"],
            "prereg_sha256": document["prereg_sha256"],
            "hostname": document["hostname"],
            **execution_identity,
            "backoff_trace_symbol_count": document[
                "backoff_trace_symbol_count"
            ],
            "backoff_trace_string_count": document[
                "backoff_trace_string_count"
            ],
            "backoff_trace": document["backoff_trace"],
            "attempt_id": attempt_id,
            **(
                {"step_policy_seed": axes.step_policy_seed}
                if axes.step_policy_seed is not None
                else {}
            ),
        },
        (workload, slot),
    )


def _group_receipt_payload(
    result_files: list[Path],
    performance_artifact: Path,
    performance_artifact_sha256: str,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
    *,
    performance_expectations: dict | None = None,
    execution_identity: dict | None = None,
) -> dict:
    expected = {(workload, slot) for workload in CERT_WORKLOADS for slot in CERT_SLOTS}
    normalized_files = [path.resolve(strict=False) for path in result_files]
    if len(normalized_files) != 24:
        raise CertificationReject(
            "group-incomplete",
            "group aggregation requires exactly 24 explicit result paths",
        )
    if len(set(normalized_files)) != 24:
        raise CertificationReject(
            "group-result-path-set-invalid",
            "group aggregation requires 24 unique result paths",
        )
    rows = []
    actual = set()
    performance_identity = _performance_artifact_identity(
        performance_artifact,
        performance_artifact_sha256,
        **(performance_expectations or {}),
    )
    for path in sorted(normalized_files):
        row, pair = _validated_certification_row(
            path,
            attempt_id=attempt_id,
            expected_verifier_identity=expected_verifier_identity,
            expected_verifier_identity_file_sha256=(
                expected_verifier_identity_file_sha256
            ),
            performance_identity=performance_identity,
        )
        if pair in actual:
            raise CertificationReject("group-duplicate-request", f"duplicate pair: {pair}")
        actual.add(pair)
        rows.append(row)
    if actual != expected or len(rows) != 24:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected, key=repr)
        raise CertificationReject(
            "group-incomplete",
            f"group requires exact 24 workload/slot pairs; missing={missing} extra={extra}",
        )
    if len({row["request_id"] for row in rows}) != 24:
        raise CertificationReject(
            "group-request-identity-duplicate", "request ids must be unique"
        )
    row_cells = [_cell_from_document(row) for row in rows]
    group_axes = _group_certification_axes(rows)
    if (
        len({row["trace_dir"] for row in rows}) != 24
        or len(
            {
                json.dumps(
                    row["source_evidence"], sort_keys=True, separators=(",", ":")
                )
                for row in rows
            }
        ) != 1
        or len({row["genome"] for row in rows}) != 1
        or len(set(row_cells)) != 1
        or len({row["claim"] for row in rows}) != 1
        or len({tuple(row["cell_order"]) for row in rows}) != 1
        or len({row["proof_surface"]["protocol"] for row in rows}) != 1
        or len(
            {
                json.dumps(
                    row["proof_surface"]["source_snapshot_identity"],
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for row in rows
            }
        )
        != 1
        or any(row["build_trace_enabled"] is not True for row in rows)
        or len({row["patch_sha256"] for row in rows}) != 1
        or len({row["dynamic_patch_sha256"] for row in rows}) != 1
        or len({row["counterfactual_patch_sha256"] for row in rows}) != 1
        or len({row["patch_stack_sha256"] for row in rows}) != 1
        or len(
            {
                json.dumps(row["patch_stack"], sort_keys=True, separators=(",", ":"))
                for row in rows
            }
        ) != 1
        or len({row["ccbench_commit"] for row in rows}) != 1
        or len({row["ccbench_head"] for row in rows}) != 1
        or len({row["repo_head"] for row in rows}) != 1
        or len({row["prereg_sha256"] for row in rows}) != 1
        or any(row["backoff_trace_symbol_count"] != 0 for row in rows)
        or any(row["backoff_trace_string_count"] != 0 for row in rows)
        or any(row["backoff_trace"] is not False for row in rows)
        or any(
            type(row[field]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", row[field]) is None
            for row in rows
            for field in (
                "binary_sha256",
                "patch_sha256",
                "dynamic_patch_sha256",
                "counterfactual_patch_sha256",
            )
        )
        or any(
            type(row["ccbench_commit"]) is not str
            or re.fullmatch(r"[0-9a-f]{40}", row["ccbench_commit"]) is None
            for row in rows
        )
        or any(row["ccbench_head"] != PIN_FULL for row in rows)
        or len({row["driver_sha256"] for row in rows}) != 1
        or len({row["pbs_sha256"] for row in rows}) != 1
        or any(row["repo_status_clean"] is not True for row in rows)
    ):
        raise CertificationReject(
            "group-build-identity-mismatch",
            "a complete group requires unique traces and exact build identities",
        )
    proof_surface = {
        "protocol": rows[0]["proof_surface"]["protocol"],
        "source_snapshot_identity": rows[0]["proof_surface"][
            "source_snapshot_identity"
        ],
    }
    cell = group_axes.cell
    expected_extime = CERT_EXTIME_BY_CELL.get(cell)
    if (
        expected_extime is None
        or rows[0]["claim"] != _certification_claim(group_axes)
        or any(row["records"] != CERT_RECORDS for row in rows)
        or any(row["extime_s"] != expected_extime for row in rows)
        or any(
            row["workload_flags"]
            != {
                **WORKLOADS[row["workload"]],
                "ycsb_tuple_num": str(CERT_RECORDS),
                "thread_num": str(group_axes.threads),
                "extime": str(expected_extime),
            }
            for row in rows
        )
        or any(
            row["prereg_sha256"] != _certification_prereg_sha256(cell)
            for row in rows
        )
    ):
        raise CertificationReject(
            "group-cell-identity-mismatch",
            "group cell, extime, preregistration, seed, and claim are not one "
            "exact certification identity",
        )
    group_execution_identity = execution_identity or {
        key: rows[0][key]
        for key in (
            "driver_sha256",
            "pbs_sha256",
            "driver_argv",
            "repo_status_clean",
        )
    }
    _validate_recorded_execution_identity(
        group_execution_identity, reason="group-build-identity-mismatch"
    )
    return {
        "schema_version": GROUP_RECEIPT_SCHEMA_VERSION,
        "complete": True,
        "attempt_id": attempt_id,
        "expected_requests": 24,
        "terminal_requests": 24,
        "certified_requests": 24,
        "claim": _certification_claim(group_axes),
        **_cell_identity(cell),
        "cell_order": [cell.label],
        "backoff_trace": False,
        "records": CERT_RECORDS,
        "threads": group_axes.threads,
        "extime_s": expected_extime,
        "claim_limitations": list(CLAIM_LIMITATIONS),
        # The correctness campaign binds the trace-disabled performance
        # artifact, but never relabels its measurements as verifier outputs.
        "performance_values_remain_uncertified": True,
        "hostname": os.uname().nodename,
        "verifier_identity": expected_verifier_identity,
        "expected_verifier_identity_file_sha256": (
            expected_verifier_identity_file_sha256
        ),
        "performance_artifact": performance_identity,
        "repo_head": rows[0]["repo_head"],
        "prereg_sha256": rows[0]["prereg_sha256"],
        "patch_sha256": rows[0]["patch_sha256"],
        "dynamic_patch_sha256": rows[0]["dynamic_patch_sha256"],
        "counterfactual_patch_sha256": rows[0][
            "counterfactual_patch_sha256"
        ],
        "patch_stack": rows[0]["patch_stack"],
        "patch_stack_sha256": rows[0]["patch_stack_sha256"],
        "ccbench_commit": rows[0]["ccbench_commit"],
        "ccbench_head": rows[0]["ccbench_head"],
        **group_execution_identity,
        "genome": rows[0]["genome"],
        "source_evidence": rows[0]["source_evidence"],
        "proof_surface": proof_surface,
        **(
            {"step_policy_seed": group_axes.step_policy_seed}
            if group_axes.step_policy_seed is not None
            else {}
        ),
        "results": rows,
    }


def _validate_published_group(
    group_out: Path,
    result_files: list[Path],
    performance_artifact: Path,
    performance_artifact_sha256: str,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
    *,
    performance_expectations: dict | None = None,
) -> None:
    try:
        receipt = json.loads(group_out.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-receipt-collision", "published group receipt is incomplete"
        ) from exc
    if type(receipt) is not dict:
        raise CertificationReject(
            "group-receipt-collision", "published group receipt is not an object"
        )
    if (
        receipt.get("schema_version")
        == UNSUPPORTED_V2_GROUP_RECEIPT_SCHEMA_VERSION
    ):
        raise CertificationReject(
            "legacy-group-receipt-schema-unsupported",
            "v2 group receipt artifacts are unsupported; published receipt "
            "validation accepts v3 group receipt artifacts only",
        )
    expected_paths = {str(path.resolve(strict=True)): path for path in result_files}
    rows = receipt.get("results")
    proof_surface = receipt.get("proof_surface")
    cell = _cell_from_document(receipt)
    expected_extime = CERT_EXTIME_BY_CELL.get(cell)
    receipt_axes = _certification_axes_from_document(
        receipt,
        cell=cell,
        reason="group-receipt-collision",
        detail="published receipt axes are outside the exact closed tables",
    )
    if type(rows) is not list or len(rows) != 24:
        raise CertificationReject(
            "group-receipt-collision",
            "published group receipt does not contain exactly 24 rows",
        )
    row_axes = [
        _certification_axes_from_document(
            row,
            reason="group-receipt-collision",
            detail="published row axes are outside the exact closed tables",
        )
        for row in rows
        if type(row) is dict
    ]
    if len(row_axes) != 24 or set(row_axes) != {receipt_axes}:
        raise CertificationReject(
            "group-receipt-collision",
            "published group rows do not share the receipt thread/seed axes",
        )
    expected_patch_identity = _patch_stack_identity()
    expected_genome = genome_for(
        cell, step_policy_seed=receipt_axes.step_policy_seed
    ).canonical()
    receipt_execution_identity = _validate_recorded_execution_identity(
        receipt, reason="group-receipt-collision"
    )
    if (
        receipt.get("schema_version") != GROUP_RECEIPT_SCHEMA_VERSION
        or receipt.get("complete") is not True
        or receipt.get("certified_requests") != 24
        or receipt.get("attempt_id") != attempt_id
        or receipt.get("verifier_identity") != expected_verifier_identity
        or receipt.get("expected_verifier_identity_file_sha256")
        != expected_verifier_identity_file_sha256
        or receipt.get("performance_artifact")
        != _performance_artifact_identity(
            performance_artifact,
            performance_artifact_sha256,
            **(performance_expectations or {}),
        )
        or expected_extime is None
        or receipt.get("cell_order") != [cell.label]
        or receipt.get("claim") != _certification_claim(receipt_axes)
        or receipt.get("backoff_trace") is not False
        or receipt.get("records") != CERT_RECORDS
        or receipt.get("extime_s") != expected_extime
        or type(receipt.get("hostname")) is not str
        or not receipt["hostname"]
        or receipt.get("prereg_sha256")
        != _certification_prereg_sha256(cell)
        or type(receipt.get("repo_head")) is not str
        or _COMMIT_RE.fullmatch(receipt["repo_head"]) is None
        or any(
            receipt.get(key) != value
            for key, value in expected_patch_identity.items()
        )
        or receipt.get("ccbench_commit") != PIN_FULL
        or receipt.get("ccbench_head") != PIN_FULL
        or receipt.get("genome") != expected_genome
        or type(receipt.get("source_evidence")) is not dict
        or receipt["source_evidence"]
        != (
            proof_surface.get("source_snapshot_identity")
            if type(proof_surface) is dict
            else None
        )
        or {row.get("path") for row in rows if type(row) is dict}
        != set(expected_paths)
    ):
        raise CertificationReject(
            "group-receipt-collision", "published group receipt has another identity"
        )
    if (
        type(proof_surface) is not dict
        or set(proof_surface) != {"protocol", "source_snapshot_identity"}
        or proof_surface.get("protocol") != CERT_PROTOCOL
        or any(
            type(row.get("proof_surface")) is not dict
            or row["proof_surface"].get("protocol") != proof_surface["protocol"]
            or row["proof_surface"].get("source_snapshot_identity")
            != proof_surface["source_snapshot_identity"]
            for row in rows
        )
    ):
        raise CertificationReject(
            "group-receipt-collision",
            "published group receipt has another proof-surface identity",
        )
    if any(
        type(row) is not dict
        or {key: row.get(key) for key in _cell_identity(cell)}
        != _cell_identity(cell)
        or row.get("cell_order") != [cell.label]
        or row.get("claim") != receipt.get("claim")
        or row.get("backoff_trace") is not False
        or row.get("records") != CERT_RECORDS
        or row.get("extime_s") != expected_extime
        or row.get("workload") not in CERT_WORKLOADS
        or row.get("workload_flags")
        != {
            **WORKLOADS[row["workload"]],
            "ycsb_tuple_num": str(CERT_RECORDS),
            "thread_num": str(receipt_axes.threads),
            "extime": str(expected_extime),
        }
        or row.get("repo_head") != receipt["repo_head"]
        or row.get("prereg_sha256") != receipt["prereg_sha256"]
        or row.get("ccbench_commit") != receipt["ccbench_commit"]
        or row.get("ccbench_head") != receipt["ccbench_head"]
        or row.get("driver_sha256") != receipt_execution_identity["driver_sha256"]
        or row.get("pbs_sha256") != receipt_execution_identity["pbs_sha256"]
        or row.get("repo_status_clean") is not True
        or type(row.get("driver_argv")) is not list
        or not row["driver_argv"]
        or any(type(item) is not str for item in row["driver_argv"])
        or row.get("genome") != receipt["genome"]
        or row.get("source_evidence") != receipt["source_evidence"]
        or any(
            row.get(key) != receipt.get(key)
            for key in expected_patch_identity
        )
        for row in rows
    ):
        raise CertificationReject(
            "group-receipt-collision",
            "published group receipt has another cell or source identity",
        )
    if (
        len({row.get("genome") for row in rows}) != 1
        or len(
            {
                json.dumps(
                    row.get("source_evidence"),
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for row in rows
            }
        )
        != 1
        or any(
            row.get("source_evidence")
            != row["proof_surface"].get("source_snapshot_identity")
            for row in rows
        )
    ):
        raise CertificationReject(
            "group-receipt-collision",
            "published group receipt has non-unique genome/source identity",
        )
    for row in rows:
        path = expected_paths[row["path"]]
        if row.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            raise CertificationReject(
                "group-receipt-collision", "published group result hash differs"
            )


def _try_finalize_group(
    result_files: list[Path],
    group_out: Path,
    performance_artifact: Path,
    performance_artifact_sha256: str,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
    *,
    performance_expectations: dict | None = None,
    execution_identity: dict | None = None,
) -> bool:
    if any(not path.is_file() for path in result_files):
        return False
    group_out.parent.mkdir(parents=True, exist_ok=True)
    reservation = group_out.with_name(group_out.name + ".reserve")
    deadline = time.monotonic() + GROUP_RECEIPT_WAIT_S
    while True:
        if group_out.is_file():
            _validate_published_group(
                group_out,
                result_files,
                performance_artifact,
                performance_artifact_sha256,
                attempt_id,
                expected_verifier_identity,
                expected_verifier_identity_file_sha256,
                performance_expectations=performance_expectations,
            )
            return True
        try:
            reservation.mkdir(mode=0o700)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise CertificationReject(
                    "group-receipt-timeout",
                    "timed out waiting for the reserved group receipt",
                )
            time.sleep(0.1)

    temporary = reservation / "group-receipt.tmp"
    try:
        if group_out.exists():
            _validate_published_group(
                group_out,
                result_files,
                performance_artifact,
                performance_artifact_sha256,
                attempt_id,
                expected_verifier_identity,
                expected_verifier_identity_file_sha256,
                performance_expectations=performance_expectations,
            )
            return True
        try:
            receipt = _group_receipt_payload(
                result_files,
                performance_artifact,
                performance_artifact_sha256,
                attempt_id,
                expected_verifier_identity,
                expected_verifier_identity_file_sha256,
                performance_expectations=performance_expectations,
                execution_identity=execution_identity,
            )
        except CertificationReject as exc:
            try:
                failure_out = group_out.with_name(
                    f"group-failure-{attempt_id}.json"
                )
                _write_json_create_only(
                    failure_out,
                    {
                        "reason": exc.reason,
                        "detail": exc.detail,
                        "attempt_id": attempt_id,
                        "failed_utc": datetime.now(timezone.utc).isoformat(),
                    },
                )
            except (OSError, TypeError, ValueError):
                pass
            return False
        encoded = (
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if group_out.exists():
            raise CertificationReject(
                "group-receipt-collision", "group receipt appeared under reservation"
            )
        os.rename(temporary, group_out)
        parent_fd = os.open(
            group_out.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return True
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        try:
            reservation.rmdir()
        except OSError:
            pass


def _remove_group_traces(group_out: Path) -> None:
    """Delete raw traces only after a complete group receipt is published."""
    import shutil

    receipt = json.loads(group_out.read_text(encoding="utf-8"))
    for row in receipt["results"]:
        trace_dir = row.get("trace_dir")
        if type(trace_dir) is str:
            shutil.rmtree(trace_dir, ignore_errors=True)


class _StoreOnceAction(argparse.Action):
    """Store one option value while rejecting a repeated option token."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        seen_attribute = f"_{self.dest}_option_seen"
        if getattr(namespace, seen_attribute, False):
            raise argparse.ArgumentError(
                self, f"{option_string or self.dest} may not be repeated"
            )
        setattr(namespace, seen_attribute, True)
        setattr(namespace, self.dest, values)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("performance", "certify"), default="performance"
    )
    parser.add_argument("--backoff-trace", action="store_true")
    parser.add_argument(
        "--repo-head", default=os.environ.get("IZANAGI_T2187_REPO_HEAD")
    )
    parser.add_argument(
        "--repo-clean",
        choices=("1",),
        default=os.environ.get("IZANAGI_T2187_REPO_CLEAN"),
    )
    parser.add_argument("--cells", required=True)
    parser.add_argument(
        "--workloads", default=",".join(DEFAULT_WORKLOADS)
    )
    parser.add_argument(
        "--threads",
        action=_StoreOnceAction,
        default=",".join(str(value) for value in DEFAULT_THREADS),
    )
    parser.add_argument("--rep-index", type=_nonnegative_int, default=0)
    parser.add_argument("--reps-per-job", type=_positive_int, default=1)
    parser.add_argument(
        "--step-policy-seed", action=_StoreOnceAction, type=_uint64_decimal
    )
    parser.add_argument(
        "--backoff-trace-terminal-us", type=_nonnegative_int, default=0
    )
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--extime", type=_positive_int, default=EXTIME)
    parser.add_argument(
        "--verifier-timeout-s",
        type=_positive_float,
        default=DEFAULT_VERIFIER_TIMEOUT_S,
    )
    parser.add_argument(
        "--build-budget-s", type=_positive_float, default=DEFAULT_BUILD_BUDGET_S
    )
    parser.add_argument(
        "--prologue-budget-s",
        type=_positive_float,
        default=DEFAULT_PROLOGUE_BUDGET_S,
    )
    parser.add_argument("--prologue-elapsed-s", type=float, default=0.0)
    parser.add_argument("--prologue-cpu-s", type=float, default=0.0)
    parser.add_argument(
        "--outer-walltime-s",
        type=_positive_float,
        default=DEFAULT_OUTER_WALLTIME_S,
    )
    parser.add_argument(
        "--exit-margin-s", type=_positive_float, default=DEFAULT_EXIT_MARGIN_S
    )
    parser.add_argument("--group-receipt-out", type=Path)
    parser.add_argument("--group-result-path", action="append", type=Path, default=[])
    parser.add_argument("--attempt-id")
    parser.add_argument("--performance-artifact", type=Path)
    parser.add_argument("--performance-artifact-sha256")
    parser.add_argument("--expected-verifier-identity", type=Path)
    parser.add_argument("--expected-verifier-identity-sha256")
    parser.add_argument("--out", required=True)
    return parser


def _validate_backoff_trace_contract(
    args: argparse.Namespace,
    cells: tuple[Cell, ...],
    workloads: tuple[str, ...],
    threads: tuple[int, ...],
) -> None:
    expected_contract = BACKOFF_TRACE_CONTRACTS.get(args.cells)
    (
        expected_cells,
        expected_workloads,
        expected_threads,
        expected_extime,
        expected_terminal_us,
    ) = (
        expected_contract
        if expected_contract is not None
        else (None, None, None, None, None)
    )
    if (
        expected_cells is None
        or cells != expected_cells
        or args.workloads != ",".join(expected_workloads)
        or args.threads != ",".join(str(value) for value in expected_threads)
        or workloads != expected_workloads
        or threads != expected_threads
        or args.rep_index != 0
        or args.reps_per_job != 1
        or args.extime != expected_extime
        or args.backoff_trace_terminal_us != expected_terminal_us
    ):
        raise ValueError(
            "--backoff-trace requires exact diagnostic axes and one exact "
            "diagnostic cell set, "
            "cell-specific workloads/threads, rep index 0, reps 1, and exact "
            "cell-specific extime/terminal settings"
        )

    if args.cells == COUNTERFACTUAL_TRACE_CELLS_TEXT and (
        type(args.step_policy_seed) is not int
        or args.step_policy_seed not in COUNTERFACTUAL_PREREGISTERED_STEP_POLICY_SEEDS
    ):
        raise ValueError("--step-policy-seed must be one preregistered cohort1 integer seed")
    if args.cells == COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT and (
        type(args.step_policy_seed) is not int
        or args.step_policy_seed not in CERT_PREREGISTERED_STEP_POLICY_SEEDS
    ):
        raise ValueError("--step-policy-seed must be one preregistered cohort2 integer seed")


def _is_backoff_policy_performance_cell_set(cells: tuple[Cell, ...]) -> bool:
    return len(cells) == 3 and frozenset(cells) == POLICY_PERFORMANCE_CELL_SET


def _matches_backoff_policy_performance_contract(
    *,
    mode: str,
    backoff_trace: bool,
    cells_text: str,
    cells: tuple[Cell, ...],
    workloads_text: str,
    workloads: tuple[str, ...],
    threads_text: str,
    threads: tuple[int, ...],
    rep_index: int,
    reps_per_job: int,
    extime: int,
    stage: int,
    step_policy_seed: int | None,
) -> bool:
    if type(rep_index) is not int or not 0 <= rep_index <= 17:
        return False
    rotation_index = rep_index % 6
    return (
        mode == "performance"
        and backoff_trace is False
        and cells_text == POLICY_PERFORMANCE_PERMUTATIONS_TEXT[rotation_index]
        and cells == POLICY_PERFORMANCE_PERMUTATIONS[rotation_index]
        and workloads_text == "write-heavy,balanced,read-heavy"
        and workloads == POLICY_PERFORMANCE_WORKLOADS
        and threads_text == "6,12,18,24,30,36,42,48"
        and threads == POLICY_PERFORMANCE_THREADS
        and extime == 3
        and reps_per_job == 1
        and stage == 1
        and step_policy_seed == POLICY_PERFORMANCE_SEEDS[rep_index]
    )


def _validate_backoff_policy_performance_contract(
    args: argparse.Namespace,
    cells: tuple[Cell, ...],
    workloads: tuple[str, ...],
    threads: tuple[int, ...],
) -> None:
    if not _matches_backoff_policy_performance_contract(
        mode=args.mode,
        backoff_trace=args.backoff_trace,
        cells_text=args.cells,
        cells=cells,
        workloads_text=args.workloads,
        workloads=workloads,
        threads_text=args.threads,
        threads=threads,
        rep_index=args.rep_index,
        reps_per_job=args.reps_per_job,
        extime=args.extime,
        stage=args.stage,
        step_policy_seed=args.step_policy_seed,
    ):
        raise ValueError(
            "policy-performance-contract-violation: requires exact trace-disabled "
            "performance mode, 18-block permutation/seed assignment, workloads, "
            "threads, extime 3, reps 1, and stage 1"
        )


def _artifact_contract_metadata(
    *,
    backoff_trace: bool,
    cells_text: str,
    workloads_text: str,
    threads_text: str,
    rep_index: int,
    reps_per_job: int,
    extime: int,
    step_policy_seed: int | None = None,
    stage: int = 1,
    mode: str = "performance",
    cells: tuple[Cell, ...] | None = None,
    workloads: tuple[str, ...] | None = None,
    threads: tuple[int, ...] | None = None,
    backoff_trace_terminal_us: int = 0,
) -> dict:
    metadata = {
        "schema_version": (
            TRACE_SCHEMA_VERSION if backoff_trace else SCHEMA_VERSION
        ),
        "not_certified": (
            DIAGNOSTIC_NOT_CERTIFIED if backoff_trace else NOT_CERTIFIED
        ),
    }
    if (
        backoff_trace is True
        and cells_text == COUNTERFACTUAL_TRACE_CELLS_TEXT
        and workloads_text == ",".join(TRACE_WORKLOADS)
        and threads_text == ",".join(str(value) for value in TRACE_THREADS)
        and rep_index == 0
        and reps_per_job == 1
        and extime == 3 and backoff_trace_terminal_us == 0
        and type(step_policy_seed) is int
        and step_policy_seed in COUNTERFACTUAL_PREREGISTERED_STEP_POLICY_SEEDS
    ):
        metadata["counterfactual_preregistration"] = (
            _counterfactual_prereg_sha256()
        )
    if (
        cells is not None
        and workloads is not None
        and threads is not None
        and _matches_backoff_policy_performance_contract(
            mode=mode,
            backoff_trace=backoff_trace,
            cells_text=cells_text,
            cells=cells,
            workloads_text=workloads_text,
            workloads=workloads,
            threads_text=threads_text,
            threads=threads,
            rep_index=rep_index,
            reps_per_job=reps_per_job,
            extime=extime,
            stage=stage,
            step_policy_seed=step_policy_seed,
        )
    ):
        metadata.update(
            backoff_policy_performance_prereg_sha256=(
                _backoff_policy_performance_prereg_sha256()
            ),
            performance_contract=POLICY_PERFORMANCE_CONTRACT,
            headline_eligible=False,
            correctness_status="uncertified",
        )
    if (
        backoff_trace is True
        and cells_text == COUNTERFACTUAL_COHORT2_TRACE_CELLS_TEXT
        and workloads_text == ",".join(TRACE_WORKLOADS)
        and threads_text == ",".join(str(value) for value in TRACE_THREADS)
        and rep_index == 0
        and reps_per_job == 1
        and extime == COHORT2_EXTIME
        and backoff_trace_terminal_us == COHORT2_BACKOFF_TRACE_TERMINAL_US
        and type(step_policy_seed) is int
        and step_policy_seed in CERT_PREREGISTERED_STEP_POLICY_SEEDS
    ):
        metadata["schema_version"] = COHORT2_TRACE_SCHEMA_VERSION
        metadata["counterfactual_preregistration"] = (
            _counterfactual_cohort2_prereg_sha256()
        )
    return metadata


def _validate_step_policy_seed(
    cells: tuple[Cell, ...], step_policy_seed: int | None
) -> None:
    if any(cell.step_policy == 2 for cell in cells) and step_policy_seed is None:
        raise ValueError(
            "--step-policy-seed is required when a policy 2 cell is present"
        )


def _counterfactual_row_metadata(
    *,
    preregistration_sha256: str | None,
    cell: Cell,
    step_policy_seed: int | None,
) -> dict:
    metadata = {}
    if preregistration_sha256 is not None:
        metadata["counterfactual_preregistration"] = preregistration_sha256
    if cell.step_policy == 2:
        if step_policy_seed is None:
            raise ValueError("policy 2 row cannot be recorded without its seed")
        metadata["step_policy_seed"] = step_policy_seed
    return metadata


def _certify_main(args: argparse.Namespace) -> int:
    """Run one exact workload × independent-slot certification request."""
    out = Path(args.out)
    _validate_output_path(out)
    axes, workload_id = _certification_contract(args)
    cell = axes.cell
    threads = axes.threads
    claim = _certification_claim(axes)
    _validate_dynamic_certification_namespaces(args, cell)
    if cell.extended:
        _validate_dynamic_output_path(out)
    assert args.group_receipt_out is not None
    assert args.performance_artifact is not None
    assert args.performance_artifact_sha256 is not None
    assert args.expected_verifier_identity is not None
    assert args.expected_verifier_identity_sha256 is not None
    assert args.attempt_id is not None
    group_out = args.group_receipt_out
    performance_artifact = args.performance_artifact
    performance_artifact_sha256 = args.performance_artifact_sha256
    result_files = [path.resolve(strict=False) for path in args.group_result_path]
    expected_verifier_identity, expected_verifier_identity_file_sha256 = (
        _load_expected_verifier_identity(
            args.expected_verifier_identity,
            args.expected_verifier_identity_sha256,
        )
    )
    patch_identity = _patch_stack_identity()
    repo_head = _validated_repo_head(args.repo_head)
    prereg_sha256 = _certification_prereg_sha256(cell)
    cert_extime = CERT_EXTIME_BY_CELL[cell]
    cert_step_policy_seed = axes.step_policy_seed
    execution_identity = _execution_identity(args.repo_clean)
    performance_expectations = (
        {
            "expected_repo_head": repo_head,
            # Performance artifacts retain the dynamic-backoff preregistration
            # identity.  The certification receipt itself is bound by the
            # cell-specific preregistration table above.
            "expected_prereg_sha256": _prereg_sha256(),
            "expected_patch_stack_sha256": patch_identity[
                "patch_stack_sha256"
            ],
            "required_cell": cell,
            "expected_extime": cert_extime,
            "expected_axes": axes,
        }
        if cell in DYNAMIC_CERT_CELLS
        else {}
    )
    if not performance_artifact.is_file():
        raise FileNotFoundError(
            f"performance artifact is missing: {performance_artifact}"
        )
    performance_identity = _performance_artifact_identity(
        performance_artifact,
        performance_artifact_sha256,
        **performance_expectations,
    )

    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(
            site_policy.heavy_work_refusal(
                site, "T-2187 adaptive constant certification"
            )
        )
    _assert_single_tenant()

    started_utc = datetime.now(timezone.utc).isoformat()
    job_wall_started = time.monotonic()
    job_cpu_started = _cpu_seconds()
    out.parent.mkdir(parents=True, exist_ok=True)
    trace_dir: Path | None = None
    payload = {
        "schema_version": CERTIFICATION_SCHEMA_VERSION,
        "kind": "correctness-certification-request",
        "claim_status": "not-yet-group-certified",
        "allowed_group_claim": claim,
        "claim_limitations": list(CLAIM_LIMITATIONS),
        "performance_values_remain_uncertified": True,
        "attempt_id": args.attempt_id,
        "stage": args.stage,
        "site": "pegasus",
        "host": os.uname().nodename,
        "hostname": os.uname().nodename,
        "repo_head": repo_head,
        "prereg_sha256": prereg_sha256,
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "workload": workload_id,
        "workload_flags": {
            **WORKLOADS[workload_id],
            "ycsb_tuple_num": str(CERT_RECORDS),
            "thread_num": str(threads),
            "extime": str(cert_extime),
        },
        "records": CERT_RECORDS,
        "threads": threads,
        "extime_s": cert_extime,
        "independent_run_slot": args.rep_index,
        "rng_seed_controlled": False,
        **_cell_identity(cell),
        "cell_order": [cell.label],
        "backoff_trace": False,
        "ccbench_commit": PIN_FULL,
        "ccbench_head": PIN_FULL,
        **execution_identity,
        **patch_identity,
        "performance_artifact": performance_identity,
        "expected_verifier_identity": expected_verifier_identity,
        "expected_verifier_identity_file_sha256": (
            expected_verifier_identity_file_sha256
        ),
        "positive_control_provenance": {
            "kind": "static-fixture-not-live-broken-build",
            "trace_dir": str(POSITIVE_CONTROL_TRACE.resolve(strict=True)),
            "producer_patch": "patches/broken-silo-norw-validation.patch",
            "producer_function": (
                "orchestrator/campaign/s2_verify_calibration.py:"
                "_broken_build_and_verify"
            ),
            "producer_change": "TxExecutor::validationPhase()",
            "defines": {
                "IZANAGI_BREAK_NOREAD_VALIDATION": 1,
                "CCBENCH_TRACE": 1,
            },
            "workload": {
                "records": 200,
                "rratio": 50,
                "rmw": True,
                "threads": 4,
                "extime_s": 1,
            },
        },
        "time_budget": {
            "prologue_seconds": args.prologue_budget_s,
            "build_seconds": args.build_budget_s,
            "run_seconds": RUN_TIMEOUT_S,
            "positive_control_seconds": POSITIVE_CONTROL_TIMEOUT_S,
            "target_verifier_seconds": args.verifier_timeout_s,
            "exit_margin_seconds": args.exit_margin_s,
            "outer_walltime_seconds": args.outer_walltime_s,
        },
        "prologue_phase": {
            "elapsed_seconds": args.prologue_elapsed_s,
            "cpu_seconds": args.prologue_cpu_s,
            "cpu_over_elapsed": (
                args.prologue_cpu_s / args.prologue_elapsed_s
                if args.prologue_elapsed_s > 0
                else None
            ),
        },
        "started_utc": started_utc,
        **(
            {"step_policy_seed": cert_step_policy_seed}
            if cert_step_policy_seed is not None
            else {}
        ),
    }
    rejected: CertificationReject | None = None
    try:
        # Trace and pipeline dependencies stay wholly inside the explicit mode.
        from orchestrator.campaign.pipeline import _run_trace

        submodule = ROOT / "external" / "ccbench"
        head = _ccbench_head(submodule)
        assert_pinned_clean(str(submodule), CURRENT_PIN)
        cc, cxx = buildcache.compilers_for_current_site()
        cache_root = Path(os.environ["TMPDIR"]) / "build-variants"
        cache_root.mkdir(mode=0o700)
        genome = genome_for(cell, step_policy_seed=cert_step_policy_seed)
        protocol = _certification_protocol(genome)

        build_wall_started = time.monotonic()
        build_cpu_started = _cpu_seconds()
        with isolated_checkout(submodule, CURRENT_PIN) as work_root:
            with _applied_patch_stack(work_root):
                evidence = source_digest.resolve_evidence(
                    genome,
                    CURRENT_PIN,
                    cxx=cxx,
                    ccbench_dir=work_root,
                )
                build_context = build_run_context(
                    generator_id=GeneratorId.BACKOFF_SWEEP
                )
                receipt = attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=hashlib.sha256(
                        (
                            f"{CERTIFICATION_SCHEMA_VERSION}|"
                            f"{evidence.genome_sha256}"
                        ).encode("utf-8")
                    ).hexdigest(),
                )
                admission = derive_build_admission(
                    build_context, evidence, generator_receipt=receipt
                )
                build_cache_key = buildcache.cache_key(
                    genome,
                    CURRENT_PIN,
                    True,
                    src_token=evidence.src_token,
                    cc=cc,
                    cxx=cxx,
                    admission=admission,
                )
                if not build_cache_key.endswith("_t1"):
                    raise CertificationReject(
                        "trace-build-identity",
                        "trace build cache identity is not trace-enabled",
                    )

                def _build_trace_binary():
                    return buildcache.build(
                        genome,
                        ccbench_commit=CURRENT_PIN,
                        trace=True,
                        cc=cc,
                        cxx=cxx,
                        admission=admission,
                        build_context=build_context,
                        source_evidence=evidence,
                        cache_root=str(cache_root),
                        ccbench_dir=work_root,
                    )

                build = _run_build_with_deadline(
                    _build_trace_binary, args.build_budget_s
                )
                payload["build_phase"] = _phase_measurement(
                    build_wall_started, build_cpu_started
                )
                if payload["build_phase"]["elapsed_seconds"] > args.build_budget_s:
                    raise CertificationReject(
                        "trace-build-budget-exceeded",
                        "trace build exceeded its preregistered inner budget",
                    )
                payload["build_trace_enabled"] = True
                payload["build_cache_key"] = build_cache_key
                payload["build_admission_receipt_sha256"] = (
                    admission.receipt_sha256
                )
                payload["source_evidence"] = {
                    "ccbench_commit": evidence.ccbench_commit,
                    "genome_sha256": evidence.genome_sha256,
                    "src_token": evidence.src_token,
                    "source_bytes_sha256": evidence.source_bytes_sha256,
                }
                proof_root = Path(work_root).resolve(strict=True)
                payload["proof_surface"] = {
                    "protocol": protocol,
                    "ccbench_root": str(proof_root),
                    "source_snapshot_identity": dict(payload["source_evidence"]),
                }
                payload["binary_sha256"] = build.bin_sha256
                payload["ccbench_head"] = head
                payload["genome"] = genome.canonical()
                symbol_count, string_count = _trace_binary_counts(build.binary)
                payload["backoff_trace_symbol_count"] = symbol_count
                payload["backoff_trace_string_count"] = string_count
                try:
                    _validate_trace_binary_counts(
                        symbol_count, string_count, backoff_trace=False
                    )
                except RuntimeError as exc:
                    raise CertificationReject(
                        "backoff-trace-leaked-into-certification", str(exc)
                    ) from exc
                if (
                    getattr(build, "trace", None) is not True
                    or not re.fullmatch(r"[0-9a-f]{64}", build.bin_sha256)
                ):
                    raise CertificationReject(
                        "trace-build-identity",
                        "trace binary lacks trace identity or a full sha256",
                    )

                trace_dir = Path(
                    tempfile.mkdtemp(
                        prefix=(
                            f"t2187-cert-{workload_id}-slot{args.rep_index}-"
                        ),
                        dir=out.parent,
                    )
                )
                if any(trace_dir.iterdir()):
                    raise CertificationReject(
                        "trace-directory-not-empty",
                        "new trace directory was not empty immediately before run",
                    )
                payload["trace_directory"] = str(trace_dir.resolve(strict=True))

                run_wall_started = time.monotonic()
                run_cpu_started = _cpu_seconds()
                trace_result = _run_trace(
                    build.binary,
                    str(trace_dir),
                    payload["workload_flags"],
                    CLOCKS_PER_US,
                    timeout_s=RUN_TIMEOUT_S,
                    numactl=NUMA,
                )
                payload["run_phase"] = _phase_measurement(
                    run_wall_started, run_cpu_started
                )
                payload["run"] = {
                    "exit_code": trace_result.returncode,
                    "trace_c_lines": trace_result.trace_c_lines,
                    "commit_count": trace_result.commit_count_witness,
                    "batch_commit_count": trace_result.batch_commit_count_witness,
                    "abort_count_stdout": trace_result.abort_counts,
                }
                if trace_result.returncode != 0:
                    raise CertificationReject(
                        "target-run-exit", "trace-enabled target run must exit 0"
                    )
                if not (trace_dir / "log").is_dir():
                    raise CertificationReject(
                        "trace-directory-log-missing", "target trace directory lacks log/"
                    )
                if (
                    trace_result.commit_count_witness is None
                    or trace_result.batch_commit_count_witness != 0
                    or trace_result.trace_c_lines
                    != trace_result.commit_count_witness
                ):
                    raise CertificationReject(
                        "target-commit-witness",
                        "commit_counts/batch_commit_counts/trace C-line witness mismatch",
                    )

                verifier_identity_before = _verifier_identity()
                _require_expected_verifier_identity(
                    verifier_identity_before, expected_verifier_identity
                )
                payload["verifier_identity"] = verifier_identity_before
                positive = _run_verifier(
                    POSITIVE_CONTROL_TRACE,
                    POSITIVE_CONTROL_EXPECTED_COMMITS,
                    POSITIVE_CONTROL_TIMEOUT_S,
                    protocol,
                    proof_root,
                )
                payload["positive_control"] = positive
                _validate_positive_control(positive, protocol, proof_root)

                target = _run_verifier(
                    trace_dir,
                    trace_result.commit_count_witness,
                    args.verifier_timeout_s,
                    protocol,
                    proof_root,
                )
                payload["target_verifier"] = target
                verifier_identity_after = _verifier_identity()
                target_document, target_result = _validate_target(
                    target,
                    trace_dir,
                    trace_result,
                    expected_verifier_identity,
                    verifier_identity_after,
                    protocol,
                    proof_root,
                )
                payload["verify_phase"] = {
                    key: target[key]
                    for key in (
                        "elapsed_seconds",
                        "cpu_seconds",
                        "cpu_over_elapsed",
                        "max_rss_kib",
                    )
                }
                payload["trace_manifest"] = _trace_manifest(trace_dir)
                payload["abort_reasons"] = target_result["stats"]["abort_reasons"]
                payload["abort_count"] = trace_result.abort_counts
                payload["verifier_json"] = target_document
    except CertificationReject as exc:
        rejected = exc
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        rejected = CertificationReject(
            "certification-execution-error", f"{type(exc).__name__}: {exc}"
        )
    finally:
        if trace_dir is not None and trace_dir.is_dir():
            if "trace_manifest" not in payload:
                try:
                    payload["trace_manifest"] = _trace_manifest(trace_dir)
                except OSError:
                    pass
        driver_wall_seconds = max(0.0, time.monotonic() - job_wall_started)
        driver_cpu_seconds = max(0.0, _cpu_seconds() - job_cpu_started)
        wall_seconds = args.prologue_elapsed_s + driver_wall_seconds
        cpu_seconds = args.prologue_cpu_s + driver_cpu_seconds
        if (
            rejected is None
            and wall_seconds + args.exit_margin_s >= args.outer_walltime_s
        ):
            rejected = CertificationReject(
                "certification-outer-budget-exhausted",
                "completed phases left less than the preregistered exit margin",
            )
        payload["job_phase"] = {
            "elapsed_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "cpu_over_elapsed": cpu_seconds / wall_seconds if wall_seconds > 0 else None,
            "driver_elapsed_seconds": driver_wall_seconds,
            "driver_cpu_seconds": driver_cpu_seconds,
        }
        payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
        if rejected is None:
            payload["terminal_status"] = "certified"
            payload["certified"] = True
            payload["certification_gate"] = "all-10-conditions-passed"
        else:
            payload["terminal_status"] = "rejected"
            payload["certified"] = False
            payload["reject_reason"] = rejected.reason
            payload["reject_detail"] = rejected.detail
            payload["performance_values_remain_uncertified"] = True
        _write_json_create_only(out, payload)

    group_complete = _try_finalize_group(
        result_files,
        group_out,
        performance_artifact,
        performance_artifact_sha256,
        args.attempt_id,
        expected_verifier_identity,
        expected_verifier_identity_file_sha256,
        performance_expectations=performance_expectations,
        execution_identity=execution_identity,
    )
    if group_complete:
        _remove_group_traces(group_out)
    if rejected is not None:
        print(f"[reject] {rejected}", file=sys.stderr, flush=True)
        return 1
    print(f"[certified-request] {out}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    cells = parse_cells(args.cells)
    is_policy_performance_request = (
        args.mode == "performance"
        and args.backoff_trace is False
        and _is_backoff_policy_performance_cell_set(cells)
    )
    if args.mode == "certify":
        if args.backoff_trace:
            raise CertificationReject(
                "backoff-trace-certification-conflict", "--backoff-trace cannot be combined with --mode certify")
        return _certify_main(args)
    _validate_step_policy_seed(cells, args.step_policy_seed)
    if not args.backoff_trace and args.backoff_trace_terminal_us != 0:
        raise ValueError(
            "--backoff-trace-terminal-us requires --backoff-trace"
        )
    workloads = _parse_workloads(args.workloads)
    threads_axis = _parse_threads(args.threads)
    out = Path(args.out)
    if is_policy_performance_request:
        _validate_backoff_policy_performance_contract(
            args, cells, workloads, threads_axis
        )
        _validate_backoff_policy_performance_output_path(out)
    _validate_output_path(out)
    if args.backoff_trace:
        _validate_backoff_trace_contract(
            args, cells, workloads, threads_axis
        )
        _validate_dynamic_output_path(out)
    elif not is_policy_performance_request:
        _validate_grid_contract(cells)
        if any(cell.extended for cell in cells):
            _validate_dynamic_output_path(out)
    from orchestrator.campaign.p2_2 import RECORDS

    patch_identity = _patch_stack_identity()
    repo_head = _validated_repo_head(args.repo_head)
    prereg_sha256 = _prereg_sha256()
    execution_identity = _execution_identity(args.repo_clean)
    if (
        type(args.prologue_elapsed_s) is not float
        or args.prologue_elapsed_s < 0
        or type(args.prologue_cpu_s) is not float
        or args.prologue_cpu_s < 0
    ):
        raise ValueError("prologue elapsed/CPU measurements must be nonnegative")

    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(
            site_policy.heavy_work_refusal(site, "T-2187 adaptive constant probe")
        )
    _assert_single_tenant()

    started_utc = datetime.now(timezone.utc).isoformat()
    wall_started = time.monotonic()
    cpu_started = _cpu_seconds()

    submodule = ROOT / "external" / "ccbench"
    head = _ccbench_head(submodule)
    assert_pinned_clean(str(submodule), CURRENT_PIN)
    cc, cxx = buildcache.compilers_for_current_site()
    cache_root = Path(os.environ["TMPDIR"]) / "build-variants"
    cache_root.mkdir(mode=0o700)

    contract_metadata = _artifact_contract_metadata(
        backoff_trace=args.backoff_trace,
        cells_text=args.cells,
        cells=cells,
        workloads_text=args.workloads,
        workloads=workloads,
        threads_text=args.threads,
        threads=threads_axis,
        rep_index=args.rep_index,
        reps_per_job=args.reps_per_job,
        extime=args.extime,
        step_policy_seed=args.step_policy_seed,
        stage=args.stage,
        mode=args.mode,
        backoff_trace_terminal_us=args.backoff_trace_terminal_us,
    )
    payload = {
        **contract_metadata,
        "kind": (
            "diagnostic-backoff-trace"
            if args.backoff_trace
            else "performance-only-probe"
        ),
        "headline_eligible": (
            False
            if args.backoff_trace or any(cell.has_step_policy for cell in cells)
            else True
        ),
        "throughput_scope": (
            "diagnostic_only" if args.backoff_trace else "performance"
        ),
        "stage": args.stage,
        "grid_spec": args.cells,
        "cell_order": [cell.label for cell in cells],
        "env_tag": ENV_TAG,
        "site": "pegasus",
        "host": os.uname().nodename,
        "hostname": os.uname().nodename,
        "repo_head": repo_head,
        "prereg_sha256": prereg_sha256,
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "rep_index": args.rep_index,
        "records": RECORDS,
        "extime_s": args.extime,
        "reps_per_job": args.reps_per_job,
        "clocks_per_us": CLOCKS_PER_US,
        "numactl": NUMA,
        "use_perf": False,
        "ccbench_commit": CURRENT_PIN,
        "ccbench_head": head,
        **execution_identity,
        "cc": cc,
        "cxx": cxx,
        **patch_identity,
        "stock": {
            "step_us": STOCK_STEP_US,
            "ceiling_us": STOCK_MAX_US,
            "update_us": STOCK_UPDATE_US,
        },
        "started_utc": started_utc,
        ("trace_runs" if args.backoff_trace else "cells"): [],
    }
    if any(cell.step_policy == 2 for cell in cells):
        payload["step_policy_seed"] = args.step_policy_seed

    with isolated_checkout(submodule, CURRENT_PIN) as work_root:
        with _applied_patch_stack(work_root):
            build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
            built = []
            for cell in cells:
                genome = genome_for(
                    cell,
                    backoff_trace=args.backoff_trace,
                    step_policy_seed=args.step_policy_seed,
                    backoff_trace_terminal_us=args.backoff_trace_terminal_us,
                )
                evidence = source_digest.resolve_evidence(
                    genome,
                    CURRENT_PIN,
                    cxx=cxx,
                    ccbench_dir=work_root,
                )
                receipt = attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=hashlib.sha256(
                        (
                            f"{payload['schema_version']}|"
                            f"{evidence.genome_sha256}"
                        ).encode("utf-8")
                    ).hexdigest(),
                )
                admission = derive_build_admission(
                    build_context, evidence, generator_receipt=receipt
                )
                build_started = time.monotonic()
                build = buildcache.build(
                    genome,
                    ccbench_commit=CURRENT_PIN,
                    trace=False,
                    cc=cc,
                    cxx=cxx,
                    admission=admission,
                    build_context=build_context,
                    source_evidence=evidence,
                    cache_root=str(cache_root),
                    ccbench_dir=work_root,
                )
                build_cache_key = buildcache.cache_key(
                    genome,
                    CURRENT_PIN,
                    False,
                    src_token=evidence.src_token,
                    cc=cc,
                    cxx=cxx,
                    admission=admission,
                )
                if not build_cache_key.endswith("_t0"):
                    raise RuntimeError(
                        "performance build cache identity is not trace-disabled"
                    )
                symbol_count, string_count = _trace_binary_counts(build.binary)
                _validate_trace_binary_counts(
                    symbol_count, string_count,
                    backoff_trace=args.backoff_trace,
                )
                if getattr(build, "trace", None) is not False:
                    raise RuntimeError(
                        "performance binary lacks trace-disabled build identity"
                    )
                source_evidence = {
                    "ccbench_commit": evidence.ccbench_commit,
                    "genome_sha256": evidence.genome_sha256,
                    "src_token": evidence.src_token,
                    "source_bytes_sha256": evidence.source_bytes_sha256,
                }
                built.append(
                    (
                        cell,
                        genome,
                        build,
                        symbol_count,
                        string_count,
                        build_cache_key,
                        admission.receipt_sha256,
                        source_evidence,
                    )
                )
                print(
                    f"[build] {cell.label} sha={build.bin_sha256[:16]} "
                    f"cached={build.cached} "
                    f"{time.monotonic() - build_started:.1f}s",
                    flush=True,
                )

            if any(cell.has_step_policy for cell in cells):
                payload["correctness_status"] = "uncertified"
            binary_shas = {
                cell.label: build.bin_sha256
                for (
                    cell,
                    _genome,
                    build,
                    _symbols,
                    _strings,
                    _cache_key,
                    _admission_sha256,
                    _source_evidence,
                ) in built
            }
            if len(set(binary_shas.values())) != len(binary_shas):
                raise RuntimeError(
                    "cells produced duplicate binaries; a build define may be inert: "
                    f"{binary_shas}"
                )

            for workload_id in workloads:
                workload = WORKLOADS[workload_id]
                for threads in threads_axis:
                    for (
                        cell,
                        genome,
                        build,
                        symbol_count,
                        string_count,
                        build_cache_key,
                        admission_sha256,
                        source_evidence,
                    ) in built:
                        measure_started = time.monotonic()
                        stdout_chunks: list[str] = []
                        point = measure_point(
                            build.binary,
                            records=RECORDS,
                            threads=threads,
                            clocks_per_us=CLOCKS_PER_US,
                            extime=args.extime,
                            reps=args.reps_per_job,
                            workload=workload,
                            numactl=NUMA,
                            timeout_s=RUN_TIMEOUT_S,
                            use_perf=False,
                            require_all_reps=args.backoff_trace,
                            subprocess_runner=(
                                _capturing_subprocess_runner(stdout_chunks)
                                if args.backoff_trace
                                else subprocess.run
                            ),
                        )
                        throughputs, median_tps, missing_reason = (
                            _performance_measurement_summary(point.throughputs)
                        )
                        row = {
                            **_cell_identity(cell),
                            **_counterfactual_row_metadata(
                                preregistration_sha256=payload.get(
                                    "counterfactual_preregistration"
                                ),
                                cell=cell,
                                step_policy_seed=args.step_policy_seed,
                            ),
                            "hostname": payload["hostname"],
                            "repo_head": repo_head,
                            "prereg_sha256": prereg_sha256,
                            "ccbench_head": head,
                            **execution_identity,
                            **patch_identity,
                            "rep_index": args.rep_index,
                            "cell_order": payload["cell_order"],
                            "workload": workload_id,
                            "workload_flags": dict(workload),
                            "threads": threads,
                            "is_stock_control": cell.is_stock_control,
                            "genome": genome.canonical(),
                            "binary_sha256": build.bin_sha256,
                            "build_trace_enabled": False,
                            "build_cache_key": build_cache_key,
                            "build_admission_receipt_sha256": admission_sha256,
                            "source_evidence": dict(source_evidence),
                            "backoff_trace_symbol_count": symbol_count,
                            "backoff_trace_string_count": string_count,
                            "backoff_trace": args.backoff_trace,
                            "throughputs": throughputs,
                            "median_tps": median_tps,
                            "abort_rate": point.abort_rate,
                            "latency_ns": point.latency_ns,
                            "run_cmd": point.run_cmd,
                            "measured_utc": datetime.now(timezone.utc).isoformat(),
                        }
                        if missing_reason is not None:
                            row["missing_reason"] = missing_reason
                        if args.backoff_trace:
                            events, summary, directional = _parse_backoff_trace(
                                "".join(stdout_chunks),
                                allow_overflow=(
                                    args.cells == NONMONOTONIC_TRACE_CELLS_TEXT
                                ),
                            )
                            row.update(
                                trace_events=events,
                                trace_summary=summary,
                                directional_success=directional,
                                throughput_scope="diagnostic_only",
                            )
                            payload["trace_runs"].append(row)
                        else:
                            row["throughput_scope"] = "performance"
                            payload["cells"].append(row)
                        _append_journal(out, row)
                        shown = (
                            "none" if median_tps is None else f"{median_tps:,.0f}"
                        )
                        print(
                            f"[run] workload={workload_id} t={threads:2d} "
                            f"cell={cell.label} median={shown} tps "
                            f"({time.monotonic() - measure_started:.1f}s)",
                            flush=True,
                        )

    wall_seconds = time.monotonic() - wall_started
    cpu_seconds = _cpu_seconds() - cpu_started
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["wall_seconds"] = wall_seconds
    payload["cpu_seconds"] = cpu_seconds
    payload["cpu_over_elapsed"] = cpu_seconds / wall_seconds
    payload["prologue_elapsed_s"] = args.prologue_elapsed_s
    payload["prologue_cpu_s"] = args.prologue_cpu_s
    payload["job_total_seconds"] = args.prologue_elapsed_s + wall_seconds

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(
        f"[done] {out} wall={wall_seconds:.1f}s cpu={cpu_seconds:.1f}s "
        f"cpu/wall={payload['cpu_over_elapsed']:.2f}",
        flush=True,
    )
    return 0


def _contains_step_policy_cell(document: dict) -> bool:
    cells = document.get("cells")
    return type(cells) is list and any(
        type(row) is dict
        and (row.get("cell_format_fields") == 12 or "step_policy" in row)
        for row in cells
    )


def _performance_measurement_summary(
    values: object,
) -> tuple[list[int | float], float | None, str | None]:
    import math

    throughputs = list(values)
    if not throughputs:
        return [], None, "no-throughput-samples"
    if any(
        type(value) not in {int, float} or not math.isfinite(value)
        for value in throughputs
    ):
        return [], None, "nonfinite-throughput"
    if any(value <= 0 for value in throughputs):
        return throughputs, None, "nonpositive-throughput"
    return throughputs, statistics.median(throughputs), None


if __name__ == "__main__":
    sys.exit(main())
