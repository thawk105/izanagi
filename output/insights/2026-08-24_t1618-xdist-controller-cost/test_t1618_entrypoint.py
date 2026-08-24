"""One-test dispatcher shim; the measurement implementation itself is pytest-free."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _attempt_id_from_basetemp(pytest_config: Any, measure_module: Any) -> str:
    try:
        raw_basetemp = pytest_config.getoption("basetemp")
    except Exception as exc:
        raise AssertionError(f"cannot read pytest basetemp option: {exc}") from exc
    if not isinstance(raw_basetemp, (str, os.PathLike)):
        raise AssertionError("pytest basetemp option is missing or is not path-like")
    basetemp = Path(raw_basetemp)
    if not basetemp.is_absolute():
        raise AssertionError(f"pytest basetemp is not absolute: {basetemp}")
    basetemp = basetemp.resolve()
    if basetemp.name != "pytest-tmp":
        raise AssertionError(f"pytest basetemp has an unexpected leaf: {basetemp}")
    attempt_id = basetemp.parent.name
    try:
        expected_attempt_dir = measure_module.resolve_attempt_dir(attempt_id)
    except measure_module.MeasurementError as exc:
        raise AssertionError(f"pytest basetemp contains an invalid attempt id: {exc}") from exc
    if basetemp.parent != expected_attempt_dir:
        raise AssertionError(
            "pytest basetemp does not identify the owned attempt directory: "
            f"{basetemp}"
        )
    if basetemp != expected_attempt_dir / "pytest-tmp":
        raise AssertionError(f"pytest basetemp does not match the attempt layout: {basetemp}")
    return attempt_id


def _run_t1618_measurement(pytest_config: Any, *, pilot: bool) -> int:
    import measure

    manifest = (HERE / "input-manifest.json").resolve()
    if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise AssertionError("PYTHONDONTWRITEBYTECODE=1 did not cross dispatch")
    if os.environ.get("IZANAGI_TASK_RUN_AUTO_RECORD") != "0":
        raise AssertionError("IZANAGI_TASK_RUN_AUTO_RECORD=0 did not cross dispatch")
    attempt_id = _attempt_id_from_basetemp(pytest_config, measure)
    args = [
        "--pilot" if pilot else "--measure",
        "--manifest", str(manifest),
        "--attempt-id", attempt_id,
    ]
    if not pilot:
        args.extend([
            "--min-pairs", "30",
            "--max-pairs", "60",
            "--relative-half-width", "0.20",
            "--minimum-practical-effect-s", "0.005",
            "--absolute-noise-bound-s", "0.010",
            "--diagnostic-pairs", "2",
            "--deadline-seconds", "10500",
            "--max-workers", "48",
        ])
    return measure.main(args)


def test_t1618_measurement(pytestconfig: Any) -> None:
    rc = _run_t1618_measurement(pytestconfig, pilot=False)
    if rc != 0:
        raise AssertionError(f"T-1618 measurement returned rc={rc}")
