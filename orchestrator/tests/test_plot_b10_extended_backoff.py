# -*- coding: utf-8 -*-
"""B-10 extended backoff generator: data, artists, axes, and layout contract."""
from __future__ import annotations

import importlib.util
import json
import math
import os
import statistics
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, os.fspath(HERE))

from skiputil import Skip, skip  # noqa: E402


MEASUREMENT_ROOT = Path(os.environ.get(
    "IZANAGI_B10_MEASUREMENT_ROOT",
    "/work/1/SFC/tanab/b10-backoff-grid-runs5",
))
T95_DF4 = 2.7764451051977987
GRID_28 = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75,
           100, 150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900)
TICKS = (0, 1, 3, 10, 35, 100, 300, 900)
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
REAL_PROVENANCE = (
    REPO
    / "docs/paper-story/figures/"
    "fig2c_b10_extended_backoff.provenance.json"
)


def _pinned_measurement_paths() -> tuple[str, ...]:
    provenance = json.loads(REAL_PROVENANCE.read_text(encoding="utf-8"))
    return tuple(sorted(row["path"] for row in provenance["external_inputs"]))


def _missing_pinned_measurements(
    measurement_root: Path,
    relative_paths: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    missing = []
    requirements = (
        _pinned_measurement_paths()
        if relative_paths is None
        else relative_paths
    )
    for relative in requirements:
        try:
            os.stat(measurement_root / relative)
        except FileNotFoundError:
            missing.append(relative)
    return tuple(missing)


def _require_pinned_measurements(
    measurement_root: Path,
    relative_paths: tuple[str, ...] | None = None,
) -> None:
    missing = _missing_pinned_measurements(measurement_root, relative_paths)
    if missing:
        detail = ", ".join(missing)
        skip(
            "pinned external measurement inputs are unavailable; missing "
            f"relative paths: {detail}; with the complete input set, all "
            "assertions in this test would run"
        )


def _load_module():
    path = REPO / "tools" / "plotting" / "plot_b10_extended_backoff.py"
    spec = importlib.util.spec_from_file_location("plot_b10_extended_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.backoff._load_plot_deps()
    return module


def _campaign(workload: str, index: int) -> dict:
    scale = float(10 ** index)
    raw = []
    for value in GRID_28 + (1000,):
        mean = scale * 1_000_000.0 + value * 1000.0
        half = (index + 1) * 10_000.0 + value
        abort = 0.08 + index * 0.25 + value / 10_000.0
        row = {
            "backoff_us": value,
            "throughput_dat_tps": mean,
            "throughput_repetitions_tps": [mean - 2, mean - 1, mean, mean + 1, mean + 2],
            "throughput_wal_mean_tps": mean,
            "throughput_ci95_half_tps": half,
            "abort_rate": abort,
            "abort_ci95_half": None,
            "wal_metrics": {
                "abort_rate": abort,
                "latency_ns": 48e9 / mean,
                "cv": 0.01,
            },
            "latency_ns": 48e9 / mean,
            "cv": 0.01,
            "included": value != 1000,
            "exclusion": None,
            "encoding_authority": None,
        }
        if value == 1000:
            row["exclusion"] = {
                "reason_code": "F718", "requested_backoff_us": 1000,
                "encoded_mode": 1, "encoded_amplitude_us": 0,
                "not_pooled_with_0us": True,
            }
            row["encoding_authority"] = {
                "authority_kind": "canonical_ruling",
                "authority_ids": ["F718", "D1106"],
                "assertion_kind": "backoff_encoding_interpretation",
                "derivation_kind": "ruling_assertion_not_measurement_derived",
            }
        raw.append(row)
    return {
        "workload": workload,
        "campaign_id": f"fixture-{workload}",
        "job_id": str(951689 + index),
        "raw_points": raw,
        "included_points": [dict(row) for row in raw if row["included"]],
        "excluded_points": [dict(row) for row in raw if not row["included"]],
        "conditions": {
            "thread_num": 48, "ycsb_tuple_num": 1_000_000,
            "ycsb_zipf_skew": 0.9, "ycsb_rratio": (5, 50, 95)[index],
            "ycsb_rmw": False, "measurement_host": f"bnode{index}",
        },
        "claim_boundary": {},
        "campaign_read_purpose": "HISTORICAL_RAW",
        "campaign_verifier_epoch": {},
    }


def _campaigns() -> list[dict]:
    return [_campaign(workload, index) for index, workload in enumerate(WORKLOADS)]


def _as_floats(values) -> list[float]:
    return [float(value) for value in values]


def test_nine_artist_series_have_exact_x_y_and_labels():
    plot = _load_module()
    campaigns = _campaigns()
    figure, records = plot.make_figure(campaigns)
    try:
        assert len(records) == 9
        assert sum(len(axis.lines) + len(axis.collections) for axis in figure.axes) == 9
        top_axes = figure.axes[:3]
        bottom_axes = figure.axes[3:]
        for index, workload in enumerate(WORKLOADS):
            points = campaigns[index]["included_points"]
            expected_x = [row["backoff_us"] for row in points]
            expected_mean = [row["throughput_wal_mean_tps"] / 1e6 for row in points]
            expected_ci = [row["throughput_ci95_half_tps"] / 1e6 for row in points]
            expected_abort = [row["abort_rate"] for row in points]

            top = top_axes[index]
            assert len(top.lines) == 1
            assert len(top.collections) == 1
            line = top.lines[0]
            interval = top.collections[0]
            assert line.get_label() == f"{workload} throughput"
            assert interval.get_label() == f"{workload} throughput 95% CI"
            assert _as_floats(line.get_xdata()) == expected_x
            assert _as_floats(line.get_ydata()) == expected_mean
            segments = interval.get_segments()
            assert len(segments) == 28
            for value, mean, half, segment in zip(
                    expected_x, expected_mean, expected_ci, segments):
                assert _as_floats(segment[:, 0]) == [value, value]
                assert _as_floats(segment[:, 1]) == [mean - half, mean + half]

            bottom = bottom_axes[index]
            assert len(bottom.lines) == 1
            assert len(bottom.collections) == 0
            abort_line = bottom.lines[0]
            assert abort_line.get_label() == f"{workload} abort rate"
            assert _as_floats(abort_line.get_xdata()) == expected_x
            assert _as_floats(abort_line.get_ydata()) == expected_abort
            assert all("abort" not in collection.get_label().lower()
                       for collection in bottom.collections)
    finally:
        plot.backoff.plt.close(figure)


def test_throughput_ci_is_wal_t95_and_abort_has_no_ci_in_canonical_data():
    _require_pinned_measurements(MEASUREMENT_ROOT)
    plot = _load_module()
    campaigns, external_inputs, receipt_chain = plot.load_measurements(MEASUREMENT_ROOT)
    assert len(external_inputs) == 22
    assert [row["workload"] for row in receipt_chain["workloads"]] == list(WORKLOADS)
    for campaign in campaigns:
        assert len(campaign["raw_points"]) == 29
        assert len(campaign["included_points"]) == 28
        assert [row["backoff_us"] for row in campaign["included_points"]] == list(GRID_28)
        for row in campaign["raw_points"]:
            repetitions = [float(value) for value in row["throughput_repetitions_tps"]]
            center = statistics.fmean(repetitions)
            half = T95_DF4 * statistics.stdev(repetitions) / math.sqrt(5)
            assert math.isclose(row["throughput_wal_mean_tps"], center, abs_tol=1e-9)
            assert math.isclose(row["throughput_ci95_half_tps"], half, abs_tol=1e-9)
            assert row["throughput_dat_tps"] == statistics_median(
                row["throughput_repetitions_tps"])
            assert row["abort_ci95_half"] is None
        zero = campaign["included_points"][0]
        excluded = campaign["excluded_points"][0]
        assert zero["backoff_us"] == 0 and zero["included"] is True
        assert excluded["backoff_us"] == 1000 and excluded["included"] is False
        assert excluded["exclusion"] == {
            "reason_code": "F718", "requested_backoff_us": 1000,
            "encoded_mode": 1, "encoded_amplitude_us": 0,
            "not_pooled_with_0us": True,
        }
        assert excluded["encoding_authority"] == {
            "authority_kind": "canonical_ruling",
            "authority_ids": ["F718", "D1106"],
            "assertion_kind": "backoff_encoding_interpretation",
            "derivation_kind": "ruling_assertion_not_measurement_derived",
        }


def statistics_median(values) -> float:
    ordered = sorted(float(value) for value in values)
    return ordered[len(ordered) // 2]


def test_axes_are_symlog_sparse_and_workload_local():
    plot = _load_module()
    figure, _records = plot.make_figure(_campaigns())
    try:
        assert len(figure.axes) == 6
        for axis in figure.axes:
            assert axis.get_xscale() == "symlog"
            scale = axis.xaxis._scale
            assert scale.base == 10
            assert scale.linthresh == 1
            assert scale.linscale == 1
            assert tuple(int(value) for value in axis.get_xticks()) == TICKS
            assert [label.get_text() for label in axis.get_xticklabels()] == [
                str(value) for value in TICKS]
        for row in (figure.axes[:3], figure.axes[3:]):
            for left_index, left in enumerate(row):
                for right in row[left_index + 1:]:
                    assert not left.get_shared_y_axes().joined(left, right)
            assert len({tuple(round(value, 9) for value in axis.get_ylim())
                        for axis in row}) == 3
        assert [axis.get_ylabel() for axis in figure.axes[:3]] == [
            "throughput (M tps)"] * 3
        assert [axis.get_ylabel() for axis in figure.axes[3:]] == [
            "abort rate (fraction)"] * 3
        assert [axis.get_xlabel() for axis in figure.axes[3:]] == [
            "static backoff (µs)"] * 3
    finally:
        plot.backoff.plt.close(figure)


def test_comparison_prohibition_is_identical_in_figure_caption_and_contract():
    plot = _load_module()
    figure, records = plot.make_figure(_campaigns())
    try:
        visible = [text.get_text() for text in figure.texts]
        assert plot.COMPARISON_WARNING in visible
        assert plot.COMPARISON_WARNING in figure._b10_caption
        assert figure._b10_caption.count(
            "M tps = million transactions per second") == 1
        assert figure._b10_caption.count(
            "read-modify-write (RMW) disabled") == 1
        assert figure._b10_comparison_warning == plot.COMPARISON_WARNING
        assert len(records) == plot._axis_contract()["artist_series_count"]
        assert "no backoff" not in " ".join(record["label"] for record in records)
        assert "adaptive" not in " ".join(record["label"] for record in records)
    finally:
        plot.backoff.plt.close(figure)


def test_bbox_overlap_is_a_failure_and_includes_ordinary_text_artists():
    plot = _load_module()
    figure = plot.backoff.plt.figure(figsize=(4, 3))
    try:
        figure.text(0.5, 0.5, "same place", ha="center")
        figure.text(0.5, 0.5, "overlap", ha="center")
        try:
            plot._validate_text_bboxes(figure)
        except plot.B10FigureError as exc:
            assert "overlap" in str(exc)
        else:
            raise AssertionError("overlapping text was accepted")
    finally:
        plot.backoff.plt.close(figure)


def test_bbox_overlap_failure_directly_includes_tick_labels():
    plot = _load_module()
    figure, axis = plot.backoff.plt.subplots(figsize=(6, 3))
    try:
        axis.set_xticks([0.5, 0.5001], labels=["tick-alpha", "tick-beta"])
        try:
            plot._validate_text_bboxes(figure)
        except plot.B10FigureError as exc:
            assert "overlap" in str(exc)
            assert "tick-alpha" in str(exc) and "tick-beta" in str(exc)
        else:
            raise AssertionError("overlapping tick labels were accepted")
    finally:
        plot.backoff.plt.close(figure)


def test_cli_requires_exact_out_prefix_and_measurement_root():
    plot = _load_module()
    assert plot._parse_cli(["plot", "out", "/measurements"]) == (
        Path("out"), Path("/measurements"))
    assert plot._parse_cli(["plot", "--help"]) is None
    for argv in (["plot"], ["plot", "out"], ["plot", "out", "root", "extra"]):
        try:
            plot._parse_cli(argv)
        except plot.B10FigureError:
            pass
        else:
            raise AssertionError(f"invalid CLI accepted: {argv}")


def _expected_measurement_paths() -> tuple[str, ...]:
    group = "b10-backoff-grid-20260826T234647Z-783837"
    campaigns = {
        "write-heavy": "b10-backoff-grid-silo-write-heavy-sweep-0a386b45",
        "balanced": "b10-backoff-grid-silo-balanced-sweep-9ded73c4",
        "read-heavy": "b10-backoff-grid-silo-read-heavy-sweep-e2d75497",
    }
    paths = {f"{group}.submit.jsonl"}
    for workload, campaign in campaigns.items():
        job_dir = f"{group}-{workload}"
        campaign_dir = f"{job_dir}/campaigns/{campaign}"
        reports = f"{campaign_dir}/reports"
        paths.update({
            f"{job_dir}/completion.json",
            f"{job_dir}/reservation.json",
            f"{campaign_dir}/campaign.lock",
            f"{campaign_dir}/runs/wal.jsonl",
            f"{reports}/b10-backoff-grid-{workload}.dat",
            f"{reports}/b10-backoff-overthrottle-{workload}.manifest.json",
            f"{reports}/b10-backoff-grid-{workload}_verdict.json",
        })
    return tuple(sorted(paths))


def test_pinned_measurement_requirements_are_exact():
    assert len(_pinned_measurement_paths()) == 22
    assert _pinned_measurement_paths() == _expected_measurement_paths()


def _write_pinned_measurement_stubs(
    measurement_root: Path,
    paths: tuple[str, ...],
) -> None:
    for relative in paths:
        target = measurement_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"stub\n")


def test_pinned_measurement_guard_skips_when_root_exists_but_one_file_is_missing():
    import tempfile

    with tempfile.TemporaryDirectory(prefix="b10-plot-guard-missing-") as temp:
        measurement_root = Path(temp)
        paths = _pinned_measurement_paths()
        _write_pinned_measurement_stubs(measurement_root, paths[1:])
        skip_exception = Skip
        if os.environ.get("PYTEST_CURRENT_TEST"):
            import pytest
            skip_exception = pytest.skip.Exception

        try:
            _require_pinned_measurements(measurement_root)
        except skip_exception as exc:
            assert paths[0] in str(exc)
            assert (
                "complete input set, all assertions in this test would run"
                in str(exc)
            )
        else:
            raise AssertionError("missing pinned measurement did not skip")


def test_pinned_measurement_guard_does_not_skip_for_complete_input_set():
    import tempfile

    with tempfile.TemporaryDirectory(prefix="b10-plot-guard-complete-") as temp:
        measurement_root = Path(temp)
        _write_pinned_measurement_stubs(
            measurement_root, _pinned_measurement_paths())

        _require_pinned_measurements(measurement_root)


def _run() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    passed = failed = skipped = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {test.__name__}: {exc}")
            skipped += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
