# -*- coding: utf-8 -*-
"""P2-4: backoff の spin を分離し、有用 IPC を実測する診断 profile。

``BACKOFF_NOINLINE=1`` で ``Backoff::backoff`` を独立シンボル化し、cycles と
instructions の total と spin 比率を rep ごとに保存する。この診断 build の throughput は
D20 により headline に使えない。

Pegasus では ``dispatch_compute.py --task generic`` から ``balanced`` を明示し、
``output/insights/2026-08-26_b10-balanced-profile/job-body.sh`` の内容を
``/bin/bash -c`` へ渡す。job body は pinned gflags/glog、job 専用 dependency prefix と
build cache を用意してから、この module を起動する。

絶対規律1: perf は trace-disabled build にだけ当てる。
絶対規律4: 単一テナント直列、48 threads、1M records、3 reps、3秒、既存7点を維持する。

  python orchestrator/campaign/backoff_profile.py
  python orchestrator/campaign/backoff_profile.py balanced
"""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.benchparse import (  # noqa: E402
    abort_rate as parse_abort,
    parse_bench_stdout,
    throughput_tps,
)
from ..holdout_observation import (  # noqa: E402
    assert_holdout_observation_admitted,
)
from . import buildcache, patchharness, pin, source_digest  # noqa: E402
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from .layout import env_scope_dir  # noqa: E402
from .model import Genome  # noqa: E402
from .p2_2 import (  # noqa: E402
    CLK,
    ENV_TAG,
    EXTIME,
    NUMA,
    RECORDS,
    THREADS,
    _assert_matches_calibration,
    _assert_single_tenant,
    resolve_site_runtime,
)


_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
REPS = 3
BACKOFF_US = [2, 5, 10, 25, 50, 100]
PERF_EVENTS = "cycles,instructions"
CCBENCH_COMMIT = pin.CURRENT_PIN

POINTS = [
    ("write-heavy", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"}),
    ("balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}),
]

D20_DIAGNOSTIC_NOTICE = (
    "BACKOFF_NOINLINE=1 diagnostic only; headline throughput に使用不可。"
)
BACKOFF_TIME_NOTICE = "requested us は contract-calibrated であり実時間は未検証。"
DEPENDENCY_IDENTITY_NOTICE = (
    "legacy buildcache.build は dependency prefix を cache identity へ束縛しない。"
    "job 専用 cache root で既存 cache の継承を避ける緩和に留まる。"
)
_COMPARISON_PATH = (
    "output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json"
)
_CACHE_ROOT_ENV = "IZANAGI_BACKOFF_PROFILE_CACHE_ROOT"
_DEPENDENCY_LOG_ENV = "IZANAGI_BACKOFF_PROFILE_DEPENDENCY_LOG"
_DEPENDENCY_PUBLISH_LOG_ENV = "IZANAGI_BACKOFF_PROFILE_DEPENDENCY_PUBLISH_LOG"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKOFF_PATCH_PATH = _REPO_ROOT / "patches/silo-backoff-fixed.patch"
_CCBENCH_DIR = _REPO_ROOT / "external/ccbench"
_BACKOFF_PATCH_ACTIVE = contextvars.ContextVar(
    "backoff_profile_patch_active", default=False,
)


@dataclass(frozen=True)
class _ProfileRuntime:
    """一度解決し、全7点と writer が object identity ごと共有する runtime。"""

    env_tag: str
    clocks_per_us: int
    numactl: tuple[str, ...]
    profiler_executable: str
    cc: str
    cxx: str
    site: str = "legacy-direct"
    contract_sha256: str = ""
    calibration_ref: str = ""
    calibration_sha256: str = ""
    hostname: str = ""
    pbs_jobid: str | None = None
    ccbench_commit: str = ""
    gflags_pin: str = ""
    glog_pin: str = ""
    dependency_prefix: str = ""
    build_cache_root: str = ""
    dependency_build_log: str = ""


def _policy_path() -> Path:
    return Path(__file__).resolve().parents[2] / "tools/pegasus/policy.json"


def _load_policy_document() -> dict:
    path = _policy_path()
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Pegasus policy を読めない: {path}: {exc}") from exc
    if type(document) is not dict:
        raise RuntimeError("Pegasus policy の top-level は object でなければならない")
    return document


def _resolve_profiler_executable(document=None) -> str:
    """policy 順で最初の absolute regular executable を返し、fallback しない。"""
    if document is None:
        document = _load_policy_document()
    entries = document.get("perf_candidates")
    if type(entries) is not list or not entries:
        raise RuntimeError("Pegasus policy perf_candidates は非空 list でなければならない")
    for candidate in entries:
        if type(candidate) is not str:
            raise RuntimeError("Pegasus policy candidate は str でなければならない")
        path = Path(candidate)
        if not path.is_absolute():
            raise RuntimeError(f"Pegasus policy candidate は absolute path が必要: {candidate!r}")
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
    raise RuntimeError("Pegasus policy の候補に実行可能な profiler がない")


def _dependency_pins(document: dict) -> tuple[str, str]:
    first = document.get("gflags_expected_head")
    second = document.get("glog_expected_head")
    pattern = re.compile(r"[0-9a-f]{40}")
    if type(first) is not str or pattern.fullmatch(first) is None:
        raise RuntimeError("Pegasus policy gflags pin が full 40 hex でない")
    if type(second) is not str or pattern.fullmatch(second) is None:
        raise RuntimeError("Pegasus policy glog pin が full 40 hex でない")
    return first, second


def _read_dependency_pins(
    directory: str, document: dict, dependency_prefix: str, cache_root: str,
) -> tuple[str, str]:
    """job body が記録した実 checkout を読み、policy と一致するときだけ返す。"""
    path = Path(directory) / "dependency-provenance.json"
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"dependency provenance を読めない: {path}: {exc}") from exc
    if type(recorded) is not dict:
        raise RuntimeError("dependency provenance の top-level は object が必要")

    expected = _dependency_pins(document)
    keys = ("gflags_pin", "glog_pin")
    pattern = re.compile(r"[0-9a-f]{40}")
    actual = tuple(recorded.get(key) for key in keys)
    if any(type(value) is not str or pattern.fullmatch(value) is None
           for value in actual):
        raise RuntimeError("dependency provenance の実 checkout が full 40 hex でない")
    if actual != expected:
        raise RuntimeError(
            "dependency checkout が policy pin と不一致: "
            f"actual={actual!r} expected={expected!r}"
        )
    bindings = (
        ("dependency_prefix", dependency_prefix),
        ("ccbench_cache_root", cache_root),
    )
    mismatches = [
        key for key, value in bindings if recorded.get(key) != value
    ]
    if mismatches:
        raise RuntimeError(
            f"dependency provenance の path binding が不一致: {mismatches}"
        )
    return actual


def _checkout_git_dir(checkout: Path) -> Path:
    marker = checkout / ".git"
    if marker.is_dir():
        return marker.resolve()
    try:
        text = marker.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"ccbench gitdir を読めない: {marker}: {exc}") from exc
    prefix = "gitdir: "
    if not text.startswith(prefix):
        raise RuntimeError(f"ccbench .git marker が不正: {marker}")
    return (checkout / text[len(prefix):]).resolve()


def _resolve_full_ccbench_commit() -> str:
    checkout = Path(__file__).resolve().parents[2] / "external/ccbench"
    git_dir = _checkout_git_dir(checkout)
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"ccbench HEAD を読めない: {exc}") from exc
    if head.startswith("ref: "):
        ref = head[5:]
        loose = git_dir / ref
        if loose.is_file():
            head = loose.read_text(encoding="utf-8").strip()
        else:
            packed = git_dir / "packed-refs"
            try:
                records = packed.read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                raise RuntimeError(f"ccbench ref を解決できない: {ref}: {exc}") from exc
            matches = [
                line.split(" ", 1)[0]
                for line in records
                if line and not line.startswith(("#", "^")) and line.endswith(f" {ref}")
            ]
            if len(matches) != 1:
                raise RuntimeError(f"ccbench ref を一意に解決できない: {ref}")
            head = matches[0]
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise RuntimeError(f"ccbench HEAD が full 40 hex でない: {head!r}")
    if not head.startswith(CCBENCH_COMMIT):
        raise RuntimeError(
            f"ccbench HEAD が current pin と不一致: {head} != {CCBENCH_COMMIT}"
        )
    return head


def _default_runtime() -> _ProfileRuntime:
    cc, cxx = buildcache.compilers_for_current_site()
    return _ProfileRuntime(
        env_tag=ENV_TAG,
        clocks_per_us=CLK,
        numactl=tuple(NUMA),
        profiler_executable="perf",
        cc=cc,
        cxx=cxx,
        dependency_prefix=os.environ.get("CMAKE_PREFIX_PATH", ""),
        build_cache_root=os.environ.get(_CACHE_ROOT_ENV, ""),
        dependency_build_log=os.environ.get(
            _DEPENDENCY_PUBLISH_LOG_ENV,
            os.environ.get(_DEPENDENCY_LOG_ENV, ""),
        ),
    )


def _build_profile_runtime(site, contract, loaded, document: dict) -> _ProfileRuntime:
    dependency_prefix = os.environ.get("CMAKE_PREFIX_PATH", "")
    cache_root = os.environ.get(_CACHE_ROOT_ENV, "")
    dependency_log_source = os.environ.get(_DEPENDENCY_LOG_ENV, "")
    dependency_log = os.environ.get(_DEPENDENCY_PUBLISH_LOG_ENV, "")
    if contract.attestation_mode == "required":
        if not dependency_prefix:
            raise RuntimeError("Pegasus profile は job 専用 CMAKE_PREFIX_PATH が必要")
        if not cache_root or not os.path.isabs(cache_root):
            raise RuntimeError("Pegasus profile は absolute な job 専用 cache root が必要")
        if not dependency_log_source or not os.path.isabs(dependency_log_source):
            raise RuntimeError("Pegasus profile は dependency build log path が必要")
        if not dependency_log or not os.path.isabs(dependency_log):
            raise RuntimeError("Pegasus profile は dependency publish log path が必要")
    first, second = _read_dependency_pins(
        dependency_log_source, document, dependency_prefix, cache_root,
    )
    cc, cxx = buildcache.compilers_for_current_site()
    return _ProfileRuntime(
        site=site,
        env_tag=contract.env_tag,
        clocks_per_us=contract.clocks_per_us,
        numactl=tuple(contract.numactl),
        profiler_executable=_resolve_profiler_executable(document),
        cc=cc,
        cxx=cxx,
        contract_sha256=contract.contract_sha256,
        calibration_ref=contract.calibration_ref.path,
        calibration_sha256=loaded.verified.sha256,
        hostname=socket.gethostname(),
        pbs_jobid=os.environ.get("PBS_JOBID"),
        ccbench_commit=_resolve_full_ccbench_commit(),
        gflags_pin=first,
        glog_pin=second,
        dependency_prefix=dependency_prefix,
        build_cache_root=cache_root,
        dependency_build_log=dependency_log,
    )


def _genome(backoff_us):
    """backoff_us=None は無 backoff、それ以外は静的固定 + noinline 診断。"""
    if backoff_us is None:
        return Genome(
            "silo",
            {**_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 1},
        )
    return Genome(
        "silo",
        {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": backoff_us,
         "BACKOFF_NOINLINE": 1},
    )


@contextlib.contextmanager
def _applied_backoff_patch():
    """同一 workload 内では一度だけ backoff patch を apply/revert する。"""
    if _BACKOFF_PATCH_ACTIVE.get():
        yield
        return
    with patchharness.applied(
        str(_BACKOFF_PATCH_PATH), CCBENCH_COMMIT, str(_CCBENCH_DIR),
    ):
        token = _BACKOFF_PATCH_ACTIVE.set(True)
        try:
            yield
        finally:
            _BACKOFF_PATCH_ACTIVE.reset(token)


def _find_cmake_cache(binary: str) -> Path:
    """build binary から最寄りの CMakeCache.txt を解決する。"""
    for directory in Path(binary).resolve().parents:
        candidate = directory / "CMakeCache.txt"
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        f"backoff build の CMakeCache.txt を見つけられない: {binary}"
    )


def _assert_build_accepted_backoff_defines(binary: str, backoff_us) -> None:
    """生成 cache が要求した backoff define を型つきで受理したことを検査する。"""
    cache = _find_cmake_cache(binary)
    try:
        lines = cache.read_text(encoding="utf-8", errors="strict").splitlines()
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"backoff build cache を読めない: {cache}: {exc}") from exc
    entries = {}
    for line in lines:
        if not line or line.startswith(("#", "//")) or "=" not in line:
            continue
        key_and_type, value = line.split("=", 1)
        if ":" not in key_and_type:
            continue
        key, cache_type = key_and_type.split(":", 1)
        entries[key] = (cache_type, value)

    expected = {
        "CCBENCH_BACKOFF_FIXED": str(-1 if backoff_us is None else backoff_us),
        "CCBENCH_BACKOFF_NOINLINE": "1",
    }
    rejected = {
        key: {"expected": ("STRING", value), "actual": entries.get(key)}
        for key, value in expected.items()
        if entries.get(key) != ("STRING", value)
    }
    if rejected:
        raise RuntimeError(
            "backoff build が要求 define を受理していない: "
            f"cache={cache}, entries={rejected}"
        )


def _flags(workload, clocks_per_us=CLK):
    flags = [
        f"-thread_num={THREADS}",
        f"-ycsb_tuple_num={RECORDS}",
        f"-extime={EXTIME}",
        f"-clocks_per_us={clocks_per_us}",
    ]
    for key, value in workload.items():
        flags.append(f"-{key}={value}")
    return flags


def _parse_perf_report(report_text):
    """report から event total と Backoff::backoff entry の比率を取る。"""
    totals = {}
    spin_pct = {}
    current = None
    for line in report_text.splitlines():
        match = re.search(r"of event '([^']+)'", line)
        if match:
            current = match.group(1)
            continue
        match = re.search(r"Event count \(approx\.\):\s*(\d+)", line)
        if match and current:
            totals[current] = int(match.group(1))
            continue
        if current:
            match = re.match(
                r"\s*([\d.]+)%\s+.*?\[[^]]+\]\s+(.+?)\s*$", line,
            )
            if match and match.group(2) == "Backoff::backoff":
                spin_pct[current] = float(match.group(1))
    return totals, spin_pct


def _profile_run(binary, workload, tmp, runtime, backoff_us):
    """1 run record/report し、complete な生値を返す。"""
    data = os.path.join(tmp, "perf.data")
    cmd = list(runtime.numactl) + [
        runtime.profiler_executable,
        "record",
        "-o",
        data,
        "-e",
        PERF_EVENTS,
        "--",
        binary,
    ] + _flags(workload, runtime.clocks_per_us)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp, timeout=180)
    if proc.returncode != 0 or not os.path.exists(data):
        raise RuntimeError(
            f"perf record failed (rc={proc.returncode}, "
            f"perf.data={'有' if os.path.exists(data) else '無'}): "
            f"{proc.stderr[-400:]}"
        )
    metrics = parse_bench_stdout(proc.stdout)
    if not metrics:
        raise RuntimeError(f"ccbench produced no metrics. stderr={proc.stderr[-300:]}")
    tps = throughput_tps(metrics)
    abort = parse_abort(metrics)
    rep = subprocess.run(
        [runtime.profiler_executable, "report", "-i", data, "--stdio",
         "--percent-limit", "0"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if rep.returncode != 0:
        raise RuntimeError(
            f"perf report failed (rc={rep.returncode}): {rep.stderr[-300:]}"
        )
    totals, spin = _parse_perf_report(rep.stdout)
    events = ("cycles", "instructions")
    missing_totals = [event for event in events
                      if type(totals.get(event)) is not int or totals[event] <= 0]
    if missing_totals:
        raise RuntimeError(f"perf report total が欠落: {missing_totals}")
    missing_symbols = [event for event in events if event not in spin]
    if backoff_us is not None and missing_symbols:
        raise RuntimeError(
            "backoff 有効点で Backoff::backoff entry が欠落: "
            f"{missing_symbols}"
        )
    return {
        "tps": tps,
        "abort": abort,
        "cycles": totals["cycles"],
        "instructions": totals["instructions"],
        "spin_cyc_pct": spin.get("cycles", 0.0),
        "spin_instr_pct": spin.get("instructions", 0.0),
    }


def _median(xs):
    values = sorted(value for value in xs if value is not None)
    return values[len(values) // 2] if values else None


def _derive_rep(run):
    cycles = run["cycles"]
    instructions = run["instructions"]
    spin_cycles = run["spin_cyc_pct"] / 100.0
    spin_instructions = run["spin_instr_pct"] / 100.0
    total_ipc = (instructions / cycles) if cycles and instructions else None
    useful_cycles = cycles * (1 - spin_cycles) if cycles else None
    useful_instructions = instructions * (1 - spin_instructions) if instructions else None
    useful_ipc = (
        useful_instructions / useful_cycles
        if useful_cycles and useful_instructions else None
    )
    tps = run["tps"]
    abort = run["abort"]
    k_total = (
        tps / ((1 - abort) * total_ipc)
        if tps and abort is not None and total_ipc else None
    )
    k_useful = (
        tps / ((1 - abort) * useful_ipc)
        if tps and abort is not None and useful_ipc else None
    )
    return {
        "tps": tps,
        "abort": abort,
        "cycles": cycles,
        "instructions": instructions,
        "spin_cyc_pct": run["spin_cyc_pct"],
        "spin_instr_pct": run["spin_instr_pct"],
        "total_ipc": total_ipc,
        "useful_ipc": useful_ipc,
        "k_total": k_total,
        "k_useful": k_useful,
    }


def _profile_point_in_patch(backoff_us, workload_snapshot, log, runtime):
    """適用済み patch scope 内で 1 backoff 量を build/profile する。"""
    genome = _genome(backoff_us)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_PROFILE)
    evidence = source_digest.resolve_evidence(
        genome, CCBENCH_COMMIT, cxx=runtime.cxx,
    )
    capability = attest_generator_output(
        build_context,
        evidence,
        generator_input_sha256=hashlib.sha256(
            f"backoff-profile/v1|{genome.canonical()}".encode("utf-8")
        ).hexdigest(),
    )
    built = buildcache.build(
        genome,
        ccbench_commit=CCBENCH_COMMIT,
        trace=False,
        cache_root=runtime.build_cache_root,
        cc=runtime.cc,
        cxx=runtime.cxx,
        admission=derive_build_admission(
            build_context, evidence, generator_receipt=capability,
        ),
        build_context=build_context,
        source_evidence=evidence,
    )
    _assert_build_accepted_backoff_defines(built.binary, backoff_us)
    _assert_single_tenant()
    runs = []
    for _ in range(REPS):
        tmp = tempfile.mkdtemp(prefix="izanagi_prof_")
        try:
            runs.append(
                _profile_run(built.binary, workload_snapshot, tmp, runtime, backoff_us)
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    tps_median = _median([run["tps"] for run in runs])
    representative = min(
        (run for run in runs if run["tps"] is not None),
        key=lambda run: abs(run["tps"] - tps_median),
        default=runs[-1],
    )
    derived = _derive_rep(representative)
    abort = representative["abort"]
    k_total = (
        tps_median / ((1 - abort) * derived["total_ipc"])
        if tps_median and abort is not None and derived["total_ipc"] else None
    )
    k_useful = (
        tps_median / ((1 - abort) * derived["useful_ipc"])
        if tps_median and abort is not None and derived["useful_ipc"] else None
    )
    row = {
        "backoff_us": backoff_us if backoff_us is not None else 0,
        "is_none": backoff_us is None,
        "genome": genome.canonical(),
        "tps_median": tps_median,
        "abort": abort,
        "total_ipc": derived["total_ipc"],
        "useful_ipc": derived["useful_ipc"],
        "spin_cyc_pct": representative["spin_cyc_pct"],
        "spin_instr_pct": representative["spin_instr_pct"],
        "k_total": k_total,
        "k_useful": k_useful,
        "tps_all": [run["tps"] for run in runs],
        "reps": [_derive_rep(run) for run in runs],
    }
    log(
        f"  backoff={row['backoff_us']:>4}us  tps={tps_median:>12,.0f}  "
        f"abort={abort * 100:5.1f}%  spin_cyc={row['spin_cyc_pct']:5.1f}%  "
        f"total_ipc={row['total_ipc']:.3f}  useful_ipc={row['useful_ipc']:.3f}  "
        f"K_useful={k_useful:,.0f}"
    )
    return row


def profile_point(backoff_us, workload, log=print, *, runtime=None):
    """1 backoff 量を REPS 回 profile し、有用 IPC を含む集計を返す。"""
    workload_snapshot = dict(workload)
    clock = runtime.clocks_per_us if runtime is not None else CLK
    assert_holdout_observation_admitted(
        gflags=tuple(_flags(workload_snapshot, clock)), admission=None,
    )
    if runtime is None:
        runtime = _default_runtime()
    with _applied_backoff_patch():
        return _profile_point_in_patch(
            backoff_us, workload_snapshot, log, runtime,
        )


def profile_workload(tag, workload, log=print, *, runtime=None):
    effective = runtime
    if effective is None:
        effective = _default_runtime()
    log(f"\n=== backoff profile  workload={tag}  ({workload}) ===")
    log(
        f"  {'pt':>6} {'tps':>14} {'abort':>7} {'spin_cyc':>9} "
        f"{'tot_ipc':>8} {'use_ipc':>8} {'K_useful':>12}"
    )
    with _applied_backoff_patch():
        rows = [profile_point(None, workload, log, runtime=effective)]
        for amount in BACKOFF_US:
            rows.append(profile_point(amount, workload, log, runtime=effective))
    return rows


def _spread(values):
    return (
        (max(values) - min(values)) / (sum(values) / len(values))
        if values else None
    )


def _comparison_receipt() -> dict[str, str]:
    path = Path(__file__).resolve().parents[2] / _COMPARISON_PATH
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"比較対象を読めない: {_COMPARISON_PATH}: {exc}") from exc
    return {"path": _COMPARISON_PATH, "sha256": hashlib.sha256(raw).hexdigest()}


def _finite_positive(value) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(value)
        and value > 0
    )


def _evaluation_band(rows):
    required = ((0, True), (2, False), (5, False), (10, False))
    grouped = {
        key: [
            row for row in rows
            if (row.get("backoff_us"), row.get("is_none")) == key
        ]
        for key in required
    }
    missing = [key for key, entries in grouped.items() if len(entries) != 1]
    if missing:
        return None, None, (
            "評価帯 S の凍結4点 (none, 2, 5, 10us) が一意に揃わない: "
            f"{missing}"
        )
    ordered = [grouped[key][0] for key in required]
    invalid_useful = [
        key for key, row in zip(required, ordered)
        if not _finite_positive(row.get("useful_ipc"))
    ]
    if invalid_useful:
        return None, None, (
            "評価帯 S の useful_ipc が有限の正値でない: "
            f"{invalid_useful}"
        )
    invalid_total = [
        key for key, row in zip(required, ordered)
        if not _finite_positive(row.get("total_ipc"))
    ]
    if invalid_total:
        return None, None, (
            "評価帯 S の total_ipc が有限の正値でないため判定不能: "
            f"{invalid_total}"
        )
    return (
        [row["useful_ipc"] for row in ordered],
        [row["total_ipc"] for row in ordered],
        None,
    )


def _format_spread(value) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def _publish_pair(staged_json: Path, staged_md: Path, final_json: Path, final_md: Path):
    """両 staging file 完成後に publish し、途中失敗なら片残りを戻す。"""
    if final_json.exists() != final_md.exists():
        raise RuntimeError("既存成果物 pair が片方だけであり、安全に更新できない")
    previous_json = staged_json.with_name("previous.json")
    previous_md = staged_md.with_name("previous.md")
    had_previous = final_json.exists()
    if had_previous:
        shutil.copy2(final_json, previous_json)
        shutil.copy2(final_md, previous_md)
    published = []
    try:
        os.replace(staged_json, final_json)
        published.append(final_json)
        os.replace(staged_md, final_md)
        published.append(final_md)
    except BaseException:
        if had_previous:
            if final_json in published:
                os.replace(previous_json, final_json)
            if final_md in published:
                os.replace(previous_md, final_md)
        else:
            for path in published:
                path.unlink(missing_ok=True)
        raise


def _write_out(tag, workload, rows, env_tag, runtime, log=print):
    """JSON/MD を同じ runtime provenance で書く。env_tag に default は持たない。"""
    if env_tag != runtime.env_tag:
        raise RuntimeError(
            f"writer env_tag が runtime と不一致: {env_tag!r} != {runtime.env_tag!r}"
        )
    out_dir = os.path.join(env_scope_dir(env_tag), "profile")
    os.makedirs(out_dir, exist_ok=True)
    workload_name = (
        f"skew{workload['ycsb_zipf_skew'].replace('.', 'p')}_"
        f"rr{workload['ycsb_rratio']}"
    )
    stem = os.path.join(out_dir, f"backoff_profile_t{THREADS}_{workload_name}")
    useful_all = [row["useful_ipc"] for row in rows
                  if _finite_positive(row.get("useful_ipc"))]
    total_all = [row["total_ipc"] for row in rows
                 if _finite_positive(row.get("total_ipc"))]
    useful_band, total_band, inconclusive_reason = _evaluation_band(rows)
    useful_band_spread = _spread(useful_band)
    total_band_spread = _spread(total_band)
    condition_met = (
        inconclusive_reason is None
        and useful_band_spread <= total_band_spread
        and useful_band_spread <= 0.044
    )
    decision_status = (
        "inconclusive"
        if inconclusive_reason is not None or not condition_met
        else "condition-met"
    )
    workload_claim = f"{tag} の headline 利得そのものを説明したとは言わない。"
    comparison_limitation = (
        "既存 +11.3% は別環境かつ別 ccbench source の値である。"
        if tag == "balanced"
        else f"{tag} の既存比較値は別環境または別 source と交絡しうる。"
    )
    comparison = _comparison_receipt()
    payload = {
        "workload": workload,
        "tag": tag,
        "threads": THREADS,
        "records": RECORDS,
        "site": runtime.site,
        "contract_sha256": runtime.contract_sha256,
        "calibration_ref": runtime.calibration_ref,
        "calibration_sha256": runtime.calibration_sha256,
        "hostname": runtime.hostname,
        "pbs_jobid": runtime.pbs_jobid,
        "ccbench_commit": runtime.ccbench_commit,
        "gflags_pin": runtime.gflags_pin,
        "glog_pin": runtime.glog_pin,
        "dependency_prefix": runtime.dependency_prefix,
        "build_cache_root": runtime.build_cache_root,
        "dependency_build_log": runtime.dependency_build_log,
        "perf_executable": runtime.profiler_executable,
        "clocks_per_us": runtime.clocks_per_us,
        "env_tag": env_tag,
        "use_perf": True,
        "diagnostic_only": True,
        "headline_eligible": False,
        "diagnostic_notice": D20_DIAGNOSTIC_NOTICE,
        "backoff_time_live_verified": False,
        "backoff_time_notice": BACKOFF_TIME_NOTICE,
        "dependency_prefix_cache_identity_bound": False,
        "dependency_identity_notice": DEPENDENCY_IDENTITY_NOTICE,
        "comparison": comparison,
        "comparison_confounds": ["environment", "ccbench_commit"],
        "preregistered_decision": {
            "evaluation_band": "backoff_us <= 10",
            "evaluation_band_source": "existing write-heavy profile",
            "spread_definition": "(max - min) / mean",
            "replication_bar": 0.044,
            "claim_condition": (
                "spread(useful_ipc,S) <= spread(total_ipc,S) and "
                "spread(useful_ipc,S) <= 0.044"
            ),
            "inconclusive_if_condition_not_met": True,
            "headline_gain_explained": False,
        },
        "decision": {
            "status": decision_status,
            "inconclusive_reason": inconclusive_reason,
            "useful_ipc_spread": useful_band_spread,
            "total_ipc_spread": total_band_spread,
            "spin_dilution_condition_met": (
                condition_met if inconclusive_reason is None else None
            ),
            "headline_gain_explained": False,
        },
        "remaining_limitations": [
            comparison_limitation,
            "BACKOFF_NOINLINE=1 の診断 build は headline に使えない。",
            "同一 env/source の stock-inline 対照をこの wave では取らない。",
            BACKOFF_TIME_NOTICE,
            DEPENDENCY_IDENTITY_NOTICE,
        ],
        "rows": rows,
    }
    verdict = (
        f"評価帯が不完全なため判定を出さない。inconclusive: {inconclusive_reason}"
        if inconclusive_reason is not None
        else (
            f"事前登録した判定2の条件を満たす。{tag} の total IPC 低下は "
            "spin 希釈で説明できる。"
            if condition_met
            else "この走では事前登録した判定2に到達しない。"
                 "反証ではなく inconclusive とする。"
        )
    )
    lines = [
        f"# backoff profile — {env_tag} / {tag} ({workload_name})",
        "",
        f"> {D20_DIAGNOSTIC_NOTICE}",
        "",
        "## provenance と限界",
        "",
        f"- site: `{runtime.site}`",
        f"- contract_sha256: `{runtime.contract_sha256}`",
        f"- calibration_ref: `{runtime.calibration_ref}`",
        f"- calibration_sha256: `{runtime.calibration_sha256}`",
        f"- hostname: `{runtime.hostname}`",
        f"- pbs_jobid: `{runtime.pbs_jobid}`",
        f"- ccbench_commit: `{runtime.ccbench_commit}`",
        f"- gflags_pin: `{runtime.gflags_pin}`",
        f"- glog_pin: `{runtime.glog_pin}`",
        f"- dependency_prefix: `{runtime.dependency_prefix}`",
        f"- build_cache_root: `{runtime.build_cache_root}`",
        f"- dependency_build_log: `{runtime.dependency_build_log}`",
        f"- perf_executable: `{runtime.profiler_executable}`",
        f"- clocks_per_us: `{runtime.clocks_per_us}`",
        f"- comparison: `{comparison['path']}` sha256 `{comparison['sha256']}`",
        "- comparison_confounds: `environment`, `ccbench_commit`",
        f"- backoff_time_live_verified: `false` — {BACKOFF_TIME_NOTICE}",
        "- dependency_prefix_cache_identity_bound: `false` — "
        f"{DEPENDENCY_IDENTITY_NOTICE}",
        "",
        "## 事前登録した判定",
        "",
        "- 評価帯 S: `backoff_us <= 10`。既存 write-heavy 成果物から固定し、この実測から選ばない。",
        "- 散布: `(max - min) / mean`。replication bar は `0.044`。",
        f"- total_ipc の散布 (S) = **{_format_spread(total_band_spread)}**",
        f"- useful_ipc の散布 (S) = **{_format_spread(useful_band_spread)}**",
        f"- 判定: {verdict}",
        f"- {workload_claim}",
        "",
        "## 有用 IPC と spin",
        "",
        f"- total_ipc の散布 (全域) = **{_format_spread(_spread(total_all))}**",
        f"- useful_ipc の散布 (全域) = **{_format_spread(_spread(useful_all))}**",
        "",
        "| backoff us | tps (median) | abort% | spin cyc% | spin instr% | "
        "total IPC | useful IPC | K_total | K_useful |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['backoff_us']}{'(none)' if row['is_none'] else ''} | "
            f"{row['tps_median']:,.0f} | {row['abort'] * 100:.1f} | "
            f"{row['spin_cyc_pct']:.1f} | {row['spin_instr_pct']:.1f} | "
            f"{row['total_ipc']:.3f} | {row['useful_ipc']:.3f} | "
            f"{(row['k_total'] or 0):,.0f} | {(row['k_useful'] or 0):,.0f} |"
        )
    lines += [
        "",
        "残るもの: 既存値との環境/source 交絡、同一 env/source の stock-inline 対照、"
        "実効 TSC の live 検証、dependency prefix の cache identity 束縛。",
        "",
        f"> {D20_DIAGNOSTIC_NOTICE}",
        "",
    ]
    json_text = json.dumps(payload, indent=2, ensure_ascii=False)
    markdown_text = "\n".join(lines)
    final_json = Path(stem + ".json")
    final_md = Path(stem + ".md")
    staging = Path(tempfile.mkdtemp(prefix=f".{Path(stem).name}.", dir=out_dir))
    staged_json = staging / final_json.name
    staged_md = staging / final_md.name
    try:
        staged_json.write_text(json_text, encoding="utf-8")
        staged_md.write_text(markdown_text, encoding="utf-8")
        _publish_pair(staged_json, staged_md, final_json, final_md)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    log(
        f"  wrote {stem}.json / .md  "
        f"(useful_ipc 散布 {_format_spread(_spread(useful_all))} vs "
        f"total_ipc {_format_spread(_spread(total_all))})"
    )
    return str(final_json)


def main(argv):
    sel = argv[1] if len(argv) > 1 else "write-heavy"
    points = POINTS if sel == "all" else [point for point in POINTS if point[0] == sel]
    if not points:
        print(f"unknown point: {sel} (選択肢: {[point[0] for point in POINTS]} / all)")
        return 2

    site, contract, _authorization = resolve_site_runtime()
    loaded = _assert_matches_calibration(contract)
    runtime = _build_profile_runtime(site, contract, loaded, _load_policy_document())
    _assert_single_tenant()

    measured = []
    for tag, workload in points:
        measured.append((tag, workload, profile_workload(
            tag, workload, runtime=runtime,
        )))
    for tag, workload, rows in measured:
        _write_out(tag, workload, rows, runtime.env_tag, runtime)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
