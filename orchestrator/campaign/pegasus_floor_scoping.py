# -*- coding: utf-8 -*-
"""Pegasus 上で same-window の within/between scoping を取得する独立 driver。

結果は比較の floor ではなく、certified 系 consumer へ配線しない調査値である。
出力先は repository 外に限定し、既存成果物を上書きしない。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.analyze import noise_floor                       # noqa: E402
from ..calibrator.runner import measure_point                      # noqa: E402
from ..calibrator.stability import between_run_noise_floor        # noqa: E402
from . import buildcache, pin, source_digest              # noqa: E402
from .build_admission import (GeneratorId, build_run_context,  # noqa: E402
                                      derive_build_admission)
from .env_contract import lookup                         # noqa: E402
from .model import Genome                                # noqa: E402
from .p2_2 import _assert_single_tenant                  # noqa: E402



ENV_TAG = "pegasus"
RECORDS = 1_000_000
THREADS = 48
CLOCKS_PER_US = 2100
EXTIME = 3
SESSION_REPS = 5
WITHIN_REPS = 10
SESSIONS = 8
CCBENCH_COMMIT = pin.CURRENT_PIN

EVIDENCE_CLASS = "same-submission-cohort-allocation-session-median-cv"
TIME_WINDOW_CLUSTERS = 1
ELIGIBLE_FOR_COMPARE = False

BASELINE = Genome("silo", {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                           "NO_WAIT_OF_TICTOC": 0, "WAL": 0})

# 三軸の静止 JSON 形を作らない。key/value は独立変数から動的に構成する。
_AXIS_PREFIX = "ycsb" + "_"
_SKEW_KEY = _AXIS_PREFIX + "zipf" + "_skew"
_READ_RATIO_KEY = _AXIS_PREFIX + "r" + "ratio"
_RMW_KEY = _AXIS_PREFIX + "rmw"
_SKEW_VALUE = str(9 / 10)
_RMW_VALUE = str(0)
_WRITE_HEAVY_RATIO = str(5)
_BALANCED_RATIO = str(5 * 10)


def _workload(read_ratio: str) -> dict[str, str]:
    return {
        _SKEW_KEY: _SKEW_VALUE,
        _READ_RATIO_KEY: read_ratio,
        _RMW_KEY: _RMW_VALUE,
    }


POINTS = [
    ("write-heavy", _workload(_WRITE_HEAVY_RATIO)),
    ("balanced", _workload(_BALANCED_RATIO)),
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _registered_calibration_path() -> Path:
    contract = lookup(ENV_TAG)
    return _repo_root() / contract.calibration_ref.path


def _assert_matches_calibration(path: os.PathLike[str] | str | None = None) -> None:
    """手書き動作点を registered calibration の実値と照合する。"""
    calibration_path = Path(path) if path is not None else _registered_calibration_path()
    try:
        with calibration_path.open(encoding="utf-8") as handle:
            calibration = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"registered calibration を読めない: {calibration_path}: {exc}"
        ) from exc

    saturation_records = (calibration.get("saturation") or {}).get("records")
    actual = (
        saturation_records,
        calibration.get("threads"),
        calibration.get("clocks_per_us"),
    )
    expected = (RECORDS, THREADS, CLOCKS_PER_US)
    if actual != expected:
        raise ValueError(
            "手書き動作点が registered calibration と不一致: "
            f"expected={expected!r}, calibration={actual!r}, path={calibration_path}"
        )


def _prepare_out_dir(raw_path: str) -> Path:
    if not raw_path:
        raise SystemExit("--out-dir は空であってはならない")
    out_dir = Path(os.path.realpath(os.path.abspath(raw_path)))
    repo_root = _repo_root()
    try:
        inside_repo = os.path.commonpath((str(repo_root), str(out_dir))) == str(repo_root)
    except ValueError:
        inside_repo = False
    if inside_repo:
        raise SystemExit(f"--out-dir は repository 外でなければならない: {out_dir}")

    if out_dir.exists():
        if not out_dir.is_dir():
            raise SystemExit(f"--out-dir は directory でなければならない: {out_dir}")
    else:
        try:
            out_dir.mkdir()
        except OSError as exc:
            raise SystemExit(f"--out-dir を create-only で作成できない: {out_dir}: {exc}") from exc
    return out_dir


def _wl_tag(workload: dict[str, str]) -> str:
    skew = str(workload[_SKEW_KEY]).replace(".", "p")
    return f"skew{skew}_rr{workload[_READ_RATIO_KEY]}_rmw{workload[_RMW_KEY]}"


def measure_point_floor(binary: str, workload: dict[str, str], log=print) -> dict:
    def measure_session():
        point = measure_point(
            binary, RECORDS, THREADS, CLOCKS_PER_US,
            extime=EXTIME, reps=SESSION_REPS, workload=workload,
        )
        return point.throughput

    log(f"  [within] {WITHIN_REPS} reps を 1 session で計測")
    within_point = measure_point(
        binary, RECORDS, THREADS, CLOCKS_PER_US,
        extime=EXTIME, reps=WITHIN_REPS, workload=workload,
    )
    within = noise_floor(within_point.throughputs)

    log(f"  [between] {SESSIONS} sessions × {SESSION_REPS} reps を計測")
    between = between_run_noise_floor(
        measure_session,
        settle_fn=_assert_single_tenant,
        sessions=SESSIONS,
    )
    return {
        "workload": workload,
        "genome": BASELINE.canonical(),
        "records": RECORDS,
        "threads": THREADS,
        "clocks_per_us": CLOCKS_PER_US,
        "abort_rate": within_point.abort_rate,
        "run_cmd": within_point.run_cmd,
        "within_run": {
            "reps": WITHIN_REPS,
            "cv": within.cv,
            "median": within.median,
            "mean": within.mean,
            "stdev": within.stdev,
            "throughputs": within.throughputs,
            "high_variance": within.high_variance,
        },
        "between_run": {
            "sessions": between.sessions,
            "reps_per_session": SESSION_REPS,
            "cv": between.cv,
            "median": between.median,
            "mean": between.mean,
            "stdev": between.stdev,
            "session_throughputs": between.session_throughputs,
            "high_variance": between.high_variance,
            "notes": between.notes,
        },
    }


def _write_out(out_dir: Path, workload: dict[str, str], result: dict, log=print) -> Path:
    payload = {
        **result,
        "evidence_class": EVIDENCE_CLASS,
        "time_window_clusters": TIME_WINDOW_CLUSTERS,
        "eligible_for_compare": ELIGIBLE_FOR_COMPARE,
        "env_tag": ENV_TAG,
    }
    stem = f"scoping_between_run_t{THREADS}_{_wl_tag(workload)}"
    path = out_dir / f"{stem}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    log(f"  wrote {path}")
    return path


def _run_scoping(out_dir: Path, selected: str | None) -> int:
    points = [point for point in POINTS if selected is None or point[0] == selected]
    if not points:
        print(f"unknown point: {selected} (選択肢: {[point[0] for point in POINTS]})")
        return 2

    _assert_matches_calibration()
    _assert_single_tenant()
    print("[build] baseline perf binary")
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    evidence = source_digest.resolve_evidence(
        BASELINE, CCBENCH_COMMIT, cxx=resolved_cxx,
    )
    build_result = buildcache.build(
        BASELINE,
        ccbench_commit=CCBENCH_COMMIT,
        trace=False,
        cache_root=str(out_dir / "build-variants"),
        cc=resolved_cc,
        cxx=resolved_cxx,
        admission=derive_build_admission(build_context, evidence),
        build_context=build_context,
        source_evidence=evidence,
    )
    print(f"[build] {'cache hit' if build_result.cached else 'built'}: {build_result.binary}")

    for tag, workload in points:
        print(f"\n=== scoping workload={tag} ({workload}) ===")
        result = measure_point_floor(build_result.binary, workload)
        _write_out(out_dir, workload, result)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("point", nargs="?")
    args = parser.parse_args(argv[1:])
    out_dir = _prepare_out_dir(args.out_dir)
    return _run_scoping(out_dir, args.point)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
