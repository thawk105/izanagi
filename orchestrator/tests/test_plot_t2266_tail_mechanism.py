# -*- coding: utf-8 -*-
"""T-2266 tail accounting figure: raw repetitions, fits, artists, and proof."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
BACKOFFS = (150, 200, 300, 500, 750, 999)
ALPHAS = (0.20, 0.16, 0.12, 0.09, 0.07, 0.055)


def _load_module():
    path = REPO / "tools/plotting/plot_t2266_tail_mechanism.py"
    spec = importlib.util.spec_from_file_location(
        "plot_t2266_tail_mechanism_under_test", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _report_filename(workload: str) -> str:
    return f"t2266-backoff-static-tail-{workload}.json"


def _synthetic_report(
    workload: str,
    u: float = 22.0,
    r: float = 85.0,
    skew_first_point: bool = False,
) -> dict:
    points = []
    for index, (backoff, alpha) in enumerate(zip(BACKOFFS, ALPHAS)):
        aborts_per_commit = alpha / (1.0 - alpha)
        service = u + aborts_per_commit * (r + backoff)
        throughput = 48e6 / service
        throughput_delta = throughput * 0.0005
        throughput_reps = [
            throughput - 2 * throughput_delta,
            throughput - throughput_delta,
            throughput,
            throughput + throughput_delta,
            throughput + 2 * throughput_delta,
        ]
        abort_reps = [alpha - 0.0002, alpha - 0.0001, alpha,
                      alpha + 0.0001, alpha + 0.0002]
        if skew_first_point and index == 0:
            throughput_reps = [100.0, 100.0, 100.0, 100.0, 200.0]
            abort_reps = [0.10, 0.10, 0.10, 0.10, 0.20]
        points.append({
            "kind": "static",
            "backoff_us": backoff,
            "median_tps": -999.0,
            "representative_abort_rate": -999.0,
            "representative_latency_ns": -999.0,
            "throughput_tps_reps": [-1.0] * 5,
            "abort_rate_reps": [-1.0] * 5,
            "ignored_point_field": "unknown fields are accepted",
            "reps": [
                {
                    "rep": rep,
                    "throughput_tps": throughput_reps[rep],
                    "abort_rate": abort_reps[rep],
                    "ignored_rep_field": True,
                }
                for rep in range(5)
            ],
        })
    points = points[2:] + points[:2]
    context_reps = [
        {"rep": rep, "throughput_tps": 1_000_000.0 + rep,
         "abort_rate": 0.25}
        for rep in range(5)
    ]
    points.insert(1, {"kind": "none", "backoff_us": None,
                      "reps": copy.deepcopy(context_reps)})
    points.insert(4, {"kind": "adaptive", "backoff_us": None,
                      "reps": copy.deepcopy(context_reps)})
    return {
        "schema_version": "t2266-backoff-static-tail-report/v1",
        "run_kind": "t2266-tail",
        "status": "complete",
        "source_measurement": "trace_disabled",
        "performance_certified": False,
        "claim_scope": "descriptive_backoff_shape_only",
        "workload": workload,
        "campaign_id": f"synthetic-{workload}",
        "realized_us": list(BACKOFFS),
        "fixture_note": "unknown top-level fields are accepted",
        "points": points,
    }


def _write_report(root: Path, report: dict, filename_workload: str | None = None) -> Path:
    workload = report["workload"] if filename_workload is None else filename_workload
    path = root / _report_filename(workload)
    path.write_text(json.dumps(report, allow_nan=True), encoding="utf-8")
    return path


def _load_synthetic_triplet(
    plot, root: Path, skew_first_point: bool = False,
) -> tuple[list[dict], list[tuple[float, float]]]:
    reports = []
    expected = []
    for index, workload in enumerate(WORKLOADS):
        u = 22.0 + 3.0 * index
        r = 85.0 + 5.0 * index
        raw = _synthetic_report(workload, u, r, skew_first_point)
        path = _write_report(root, raw)
        reports.append(plot.load_report(path, workload))
        expected.append((u, r))
    return reports, expected


def _expect_rejected(mutator, *, expected_workload: str = "write-heavy") -> None:
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-reject-") as temporary:
        root = Path(temporary)
        report = _synthetic_report("write-heavy")
        mutator(report)
        path = _write_report(root, report)
        try:
            plot.load_report(path, expected_workload)
        except plot.TailMechanismError:
            return
        raise AssertionError("invalid T-2266 report was accepted")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_residual_fit_recovers_known_u_and_r():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-known-fit-") as temporary:
        reports, expected = _load_synthetic_triplet(plot, Path(temporary))
        analyses = plot.analyze_reports(reports)
        assert [report["workload"] for report in reports] == list(WORKLOADS)
        for analysis, (u, r) in zip(analyses, expected):
            assert math.isclose(analysis["u_us"], u, rel_tol=0.0, abs_tol=1e-10)
            assert math.isclose(
                analysis["r_us_per_abort"], r, rel_tol=0.0, abs_tol=1e-10
            )


def test_point_means_are_arithmetic_over_five_reps():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-means-") as temporary:
        raw = _synthetic_report("write-heavy", skew_first_point=True)
        loaded = plot.load_report(_write_report(Path(temporary), raw), "write-heavy")
        point = plot.analyze_report(loaded)["points"][0]
        assert point["throughput_mean_tps"] == 120.0
        assert point["throughput_mean_tps"] != statistics.median(
            [100.0, 100.0, 100.0, 100.0, 200.0]
        )
        assert math.isclose(point["abort_rate_mean"], 0.12, abs_tol=1e-15)
        assert point["abort_rate_mean"] != statistics.median(
            [0.10, 0.10, 0.10, 0.10, 0.20]
        )


def test_confidence_interval_uses_t_distribution_for_n5():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-ci-") as temporary:
        raw = _synthetic_report("write-heavy", skew_first_point=True)
        loaded = plot.load_report(_write_report(Path(temporary), raw), "write-heavy")
        point = plot.analyze_report(loaded)["points"][0]
        tps = [100.0, 100.0, 100.0, 100.0, 200.0]
        expected_t = 2.776 * statistics.stdev(tps) / math.sqrt(5)
        normal = 1.96 * statistics.stdev(tps) / math.sqrt(5)
        assert math.isclose(
            point["throughput_ci95_half_tps"], expected_t,
            rel_tol=0.0, abs_tol=1e-12,
        )
        assert not math.isclose(
            point["throughput_ci95_half_tps"], normal,
            rel_tol=0.0, abs_tol=1e-12,
        )


def test_service_time_uses_48_worker_threads():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-service-") as temporary:
        report = _synthetic_report("write-heavy")
        loaded = plot.load_report(_write_report(Path(temporary), report), "write-heavy")
        point = plot.analyze_report(loaded)["points"][0]
        expected = 48e6 / point["throughput_mean_tps"]
        assert math.isclose(point["service_time_us"], expected, abs_tol=1e-12)
        assert not math.isclose(
            point["service_time_us"],
            47e6 / point["throughput_mean_tps"],
            abs_tol=1e-12,
        )


def test_aborts_per_commit_from_abort_rate():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-aborts-") as temporary:
        report = _synthetic_report("write-heavy")
        loaded = plot.load_report(_write_report(Path(temporary), report), "write-heavy")
        point = plot.analyze_report(loaded)["points"][0]
        alpha = point["abort_rate_mean"]
        assert math.isclose(
            point["aborts_per_commit"], alpha / (1.0 - alpha), abs_tol=1e-15
        )
        assert not math.isclose(point["aborts_per_commit"], alpha, abs_tol=1e-15)


def test_stacked_components_sum_to_model_service_time():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-stack-") as temporary:
        reports, _expected = _load_synthetic_triplet(plot, Path(temporary))
        for analysis in plot.analyze_reports(reports):
            for point in analysis["points"]:
                a = point["aborts_per_commit"]
                assert math.isclose(
                    point["abort_overhead_a_r_us"],
                    a * analysis["r_us_per_abort"],
                    abs_tol=1e-12,
                )
                stack_sum = (
                    point["commit_cost_u_us"]
                    + point["abort_overhead_a_r_us"]
                    + point["backoff_wait_a_b_us"]
                )
                assert math.isclose(
                    stack_sum, point["model_service_time_us"], abs_tol=1e-12
                )


def test_refuted_exponential_uses_50_and_100_us_pins():
    plot = _load_module()
    for workload in WORKLOADS:
        anchors = plot.LEGACY_TAIL_ANCHOR_TPS[workload]
        assert math.isclose(
            plot.refuted_exponential_tps(workload, 50), anchors[50], rel_tol=1e-15
        )
        assert math.isclose(
            plot.refuted_exponential_tps(workload, 100), anchors[100], rel_tol=1e-15
        )
        k = (math.log(anchors[100]) - math.log(anchors[50])) / 50.0
        expected_300 = anchors[100] * math.exp(k * 200.0)
        assert math.isclose(
            plot.refuted_exponential_tps(workload, 300), expected_300,
            rel_tol=1e-15,
        )


def test_real_reports_match_primary_source_refuted_extrapolation_literals():
    plot = _load_module()
    literals = {
        "write-heavy": (1902344, 1537983, 1005255, 429463, 148333, 51451),
        "balanced": (1433048, 1101021, 649928, 226467, 60629, 16317),
        "read-heavy": (3503981, 2763894, 1719652, 665701, 203272, 62364),
    }
    reports = plot.load_reports()
    assert [report["workload"] for report in reports] == list(WORKLOADS)
    for report in reports:
        workload = report["workload"]
        for backoff, expected in zip(BACKOFFS, literals[workload]):
            actual = plot.refuted_exponential_tps(workload, backoff)
            assert math.isclose(actual, expected, rel_tol=1e-4)


def test_rejects_non_static_points_in_the_series():
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-static-only-") as temporary:
        raw = _synthetic_report("write-heavy")
        loaded = plot.load_report(_write_report(Path(temporary), raw), "write-heavy")
        assert len(raw["points"]) == 8
        assert [point["kind"] for point in loaded["static_points"]] == ["static"] * 6
        contaminated = dict(loaded)
        contaminated["static_points"] = list(loaded["static_points"]) + [{
            "kind": "adaptive", "backoff_us": None, "reps": []
        }]
        try:
            plot.analyze_report(contaminated)
        except plot.TailMechanismError:
            pass
        else:
            raise AssertionError("non-static point entered the analysis series")


def test_each_panel_has_a_single_y_axis_and_no_baseline():
    plot = _load_module()
    analyses = plot.analyze_reports(plot.load_reports())
    figure, records = plot.make_figure(analyses)
    try:
        assert len(figure.axes) == 9
        assert len(records) == 3
        for axis in figure.axes:
            assert axis.get_xscale() == "log"
            assert len(axis.containers) == 1
        for column in range(3):
            top = figure.axes[column]
            middle = figure.axes[3 + column]
            bottom = figure.axes[6 + column]
            # Each errorbar contributes its measured line and two cap lines.
            # The remaining lines are exactly the named model series, so an
            # axhline baseline cannot enter unnoticed.
            assert len(top.lines) == 5
            assert len(middle.lines) == 3
            assert len(bottom.lines) == 4
        labels = [
            artist.get_label().lower()
            for axis in figure.axes
            for artist in (*axis.lines, *axis.collections)
        ]
        assert not any("no backoff" in label or "adaptive" in label
                       for label in labels)
    finally:
        plot.plt.close(figure)


def test_figure_caption_contains_claim_boundary_and_six_caveats_once():
    plot = _load_module()
    analyses = plot.analyze_reports(plot.load_reports())
    figure, _records = plot.make_figure(analyses)
    try:
        rendered_text = "\n".join(
            artist.get_text() for artist in figure.findobj(plot.Text)
        )
        for literal in (
            "source_measurement=trace_disabled",
            "performance_certified=false",
            "claim_scope=descriptive_backoff_shape_only",
            "variant adoption",
            "aggregate time across 48 workers",
            "leader-specific costs",
            "aborts per commit",
            "fitted accounting components",
            "not directly observed costs",
            "true static 1000 µs point was not measured",
            "current encoding (F718)",
            "post-hoc analysis",
        ):
            assert rendered_text.count(literal) == 1
    finally:
        plot.plt.close(figure)


def test_bbox_overlap_is_rejected_before_save():
    plot = _load_module()
    plot._load_plot_deps()
    figure = plot.plt.figure(figsize=(4, 3))
    try:
        figure.text(0.5, 0.5, "overlap one", ha="center")
        figure.text(0.5, 0.5, "overlap two", ha="center")
        try:
            plot._validate_text_bboxes(figure)
        except plot.TailMechanismError as exc:
            assert "overlap" in str(exc)
        else:
            raise AssertionError("overlapping text was accepted")
    finally:
        plot.plt.close(figure)


def test_provenance_records_input_report_digests():
    plot = _load_module()
    reports = plot.load_reports()
    analyses = plot.analyze_reports(reports)
    with tempfile.TemporaryDirectory(prefix="t2266-provenance-") as temporary:
        root = Path(temporary)
        png = root / "figure.png"
        pdf = root / "figure.pdf"
        figure, _records = plot.make_figure(analyses)
        try:
            figure.savefig(png, dpi=80)
            figure.savefig(pdf)
        finally:
            plot.plt.close(figure)
        provenance = plot.build_provenance(reports, analyses, (png, pdf))
    assert len(provenance["inputs"]) == 3
    for source, row in zip(reports, provenance["inputs"]):
        path = Path(source["source_path"])
        assert row["sha256"] == _sha256(path)
        assert len(row["sha256"]) == 64
        assert row["campaign_id"] == source["campaign_id"]
        assert not Path(row["path"]).is_absolute()
    for expected, recorded in zip(analyses, provenance["workloads"]):
        assert recorded["u_us"] == expected["u_us"]
        assert recorded["r_us_per_abort"] == expected["r_us_per_abort"]


def test_rejects_schema_version_mismatch():
    _expect_rejected(lambda report: report.__setitem__("schema_version", "v0"))


def test_rejects_run_kind_mismatch():
    _expect_rejected(lambda report: report.__setitem__("run_kind", "other"))


def test_rejects_incomplete_status():
    _expect_rejected(lambda report: report.__setitem__("status", "failed"))


def test_rejects_realized_1000_instead_of_999():
    _expect_rejected(
        lambda report: report.__setitem__(
            "realized_us", [150, 200, 300, 500, 750, 1000]
        )
    )


def test_rejects_five_static_points():
    def mutate(report):
        report["points"] = [
            point for point in report["points"]
            if point.get("kind") != "static" or point.get("backoff_us") != 999
        ]

    _expect_rejected(mutate)


def test_rejects_seven_static_points():
    def mutate(report):
        extra = copy.deepcopy(next(
            point for point in report["points"] if point.get("kind") == "static"
        ))
        extra["backoff_us"] = 900
        report["points"].append(extra)

    _expect_rejected(mutate)


def test_rejects_four_repetitions():
    def mutate(report):
        next(point for point in report["points"]
             if point.get("kind") == "static")["reps"].pop()

    _expect_rejected(mutate)


def test_rejects_invalid_rep_measurements():
    cases = (
        ("abort_rate", 1.0),
        ("abort_rate", -0.1),
        ("abort_rate", float("nan")),
        ("throughput_tps", 0.0),
        ("throughput_tps", float("nan")),
    )
    for field, value in cases:
        def mutate(report, field=field, value=value):
            point = next(item for item in report["points"]
                         if item.get("kind") == "static")
            point["reps"][0][field] = value

        _expect_rejected(mutate)


def test_rejects_workload_field_filename_and_argument_mismatch():
    _expect_rejected(lambda report: report.__setitem__("workload", "balanced"))
    plot = _load_module()
    with tempfile.TemporaryDirectory(prefix="t2266-workload-") as temporary:
        root = Path(temporary)
        report = _synthetic_report("write-heavy")
        wrong_filename = _write_report(root, report, filename_workload="balanced")
        try:
            plot.load_report(wrong_filename, "write-heavy")
        except plot.TailMechanismError:
            pass
        else:
            raise AssertionError("workload/filename mismatch was accepted")
        correct_filename = _write_report(root, report)
        try:
            plot.load_report(correct_filename, "balanced")
        except plot.TailMechanismError:
            pass
        else:
            raise AssertionError("workload/argument mismatch was accepted")


def _run() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
