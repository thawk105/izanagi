# -*- coding: utf-8 -*-
"""Pegasus scoping driver の隔離出力・照合・非配線契約を固定する。"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "orchestrator"))

from campaign import pegasus_floor_scoping as scoping  # noqa: E402
from campaign.p2_2 import _assert_single_tenant         # noqa: E402


# 未既知性検索へ静止した三軸 JSON を足さない。key/value は別々に構成する。
_AXIS_PREFIX = "ycsb" + "_"
_SKEW_KEY = _AXIS_PREFIX + "zipf" + "_skew"
_READ_RATIO_KEY = _AXIS_PREFIX + "r" + "ratio"
_RMW_KEY = _AXIS_PREFIX + "rmw"
_SKEW_VALUE = str(9 / 10)
_RMW_VALUE = str(0)
_POINT_RATIOS = {str(5), str(5 * 10)}


def test_scoping_uses_p2_2_single_tenant_guard_by_identity() -> None:
    assert scoping._assert_single_tenant is _assert_single_tenant


@pytest.mark.parametrize(
    "inside",
    [
        REPO,
        REPO / "output",
        REPO / "output" / "env" / "pegasus" / "calibration",
    ],
    ids=("repo-root", "output-root", "registered-calibration-parent"),
)
def test_m1_repo_internal_out_dir_is_rejected_before_runtime(
    inside: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    reached = []
    monkeypatch.setattr(
        scoping, "_run_scoping", lambda *_args, **_kwargs: reached.append(True) or 0,
    )

    with pytest.raises(SystemExit) as caught:
        scoping.main(["pegasus_floor_scoping.py", "--out-dir", str(inside)])

    assert caught.value.code != 0
    assert reached == []


def _run_with_fake_runtime(
    out_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[int, dict[str, object]]:
    calls: dict[str, object] = {
        "tenant": 0,
        "measure": [],
        "build": [],
    }

    def fake_tenant() -> None:
        calls["tenant"] = int(calls["tenant"]) + 1

    def fake_measure(
        binary: str, records: int, threads: int, clocks_per_us: int, **kwargs,
    ) -> SimpleNamespace:
        assert binary == "/fixture/ycsb_silo.exe"
        assert records == scoping.RECORDS
        assert threads == scoping.THREADS
        assert clocks_per_us == scoping.CLOCKS_PER_US
        assert "numactl" not in kwargs
        measure_calls = calls["measure"]
        assert isinstance(measure_calls, list)
        measure_calls.append(kwargs)
        throughputs = [1_000_000.0 + len(measure_calls)] * kwargs["reps"]
        return SimpleNamespace(
            throughputs=throughputs,
            throughput=statistics.median(throughputs),
            abort_rate=0.125,
            run_cmd="fixture perf command",
        )

    def fake_build(*args, **kwargs) -> SimpleNamespace:
        build_calls = calls["build"]
        assert isinstance(build_calls, list)
        build_calls.append((args, kwargs))
        assert kwargs["cache_root"] == str(out_dir / "build-variants")
        assert kwargs["trace"] is False
        return SimpleNamespace(binary="/fixture/ycsb_silo.exe", cached=False)

    context = object()
    evidence = object()
    admission = object()
    monkeypatch.setattr(scoping, "_assert_single_tenant", fake_tenant)
    monkeypatch.setattr(scoping, "measure_point", fake_measure)
    monkeypatch.setattr(scoping.buildcache, "build", fake_build)
    monkeypatch.setattr(
        scoping.buildcache, "compilers_for_current_site", lambda: ("gcc", "g++"),
    )
    monkeypatch.setattr(
        scoping, "build_run_context", lambda **_kwargs: context,
    )
    monkeypatch.setattr(
        scoping.source_digest, "resolve_evidence", lambda *_args, **_kwargs: evidence,
    )
    monkeypatch.setattr(
        scoping, "derive_build_admission", lambda actual_context, actual_evidence:
        admission if (actual_context, actual_evidence) == (context, evidence) else None,
    )

    rc = scoping.main(
        ["pegasus_floor_scoping.py", "--out-dir", str(out_dir)],
    )
    return rc, calls


def test_repo_external_existing_tmp_dir_reaches_measurement_seam(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    out_dir = tmp_path / "accepted-existing-out"
    out_dir.mkdir()

    rc, calls = _run_with_fake_runtime(out_dir, monkeypatch)

    assert rc == 0
    assert calls["tenant"] == 1 + 2 * (scoping.SESSIONS - 1)
    assert len(calls["measure"]) == 2 * (1 + scoping.SESSIONS)
    assert len(calls["build"]) == 1
    point_values = {workload[_READ_RATIO_KEY] for _, workload in scoping.POINTS}
    assert point_values == _POINT_RATIOS
    for _, workload in scoping.POINTS:
        assert workload[_SKEW_KEY] == _SKEW_VALUE
        assert workload[_RMW_KEY] == _RMW_VALUE


@pytest.mark.parametrize(
    "field",
    ("saturation.records", "threads", "clocks_per_us"),
    ids=("records", "threads", "clocks"),
)
def test_m2_registered_calibration_mismatch_raises_value_error(
    field: str, tmp_path: Path,
) -> None:
    source = scoping._registered_calibration_path()
    calibration = json.loads(source.read_text(encoding="utf-8"))
    if field == "saturation.records":
        calibration["saturation"]["records"] = scoping.RECORDS + 1
    elif field == "threads":
        calibration["threads"] = scoping.THREADS + 1
    else:
        calibration["clocks_per_us"] = scoping.CLOCKS_PER_US + 1
    mismatch = tmp_path / "mismatch.json"
    mismatch.write_text(json.dumps(calibration), encoding="utf-8")

    with pytest.raises(ValueError, match="registered calibration と不一致"):
        scoping._assert_matches_calibration(mismatch)


def test_m3_output_contains_estimand_fields_and_environment_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    out_dir = tmp_path / "estimand-out"
    out_dir.mkdir()
    rc, _ = _run_with_fake_runtime(out_dir, monkeypatch)
    assert rc == 0

    paths = sorted(out_dir.glob("scoping_between_run_*.json"))
    assert len(paths) == 2
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["evidence_class"] == scoping.EVIDENCE_CLASS
        assert payload["time_window_clusters"] == 1
        assert payload["eligible_for_compare"] is False
        assert payload["env_tag"] == "pegasus"
        assert set(payload["within_run"]) >= {"reps", "cv", "median", "throughputs"}
        assert set(payload["between_run"]) >= {
            "sessions", "reps_per_session", "cv", "median", "session_throughputs",
        }


def test_m4_scoping_output_is_invisible_to_between_run_floor_consumer_glob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    out_dir = tmp_path / "glob-out"
    out_dir.mkdir()
    rc, _ = _run_with_fake_runtime(out_dir, monkeypatch)
    assert rc == 0

    assert len(list(out_dir.glob("scoping_between_run_*.json"))) == 2
    assert list(out_dir.glob("between_run_noise_*.json")) == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
