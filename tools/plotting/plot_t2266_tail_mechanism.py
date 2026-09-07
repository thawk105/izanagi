#!/usr/bin/env python3
"""Plot a descriptive accounting fit for the T-2266 static-backoff tail.

Usage:
    python tools/plotting/plot_t2266_tail_mechanism.py OUT_PREFIX

The three checked-in ``t2266-backoff-static-tail-report/v1`` reports are the
only runtime measurements.  Every plotted statistic is recomputed from their
five repetition records.  The refuted exponential is deliberately different:
its two anchors are pinned transcriptions of ``t2216_model_tail.json``
``calibrations[<workload>]`` (schema ``izanagi-t2216-backoff-walk/v2``, SHA-256
``12599199e0694aa7bb7a590c3c34cb53c99a309d22b13e004e9c118e1909a7c9``).
That 3.8 MB model output is never opened at runtime, and its repetition-level
source values are not available in the repository.

This is post-hoc, non-certified, descriptive analysis.  It does not establish
a mechanism, explain the adaptive-backoff valley, or support variant adoption.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import statistics
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = (
    REPO_ROOT
    / "output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail"
)
SCHEMA = "izanagi-t2266-tail-mechanism-figure-provenance/v1"
REPORT_SCHEMA = "t2266-backoff-static-tail-report/v1"
RUN_KIND = "t2266-tail"
STATIC_BACKOFF_US = (150, 200, 300, 500, 750, 999)
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
RRATIOS = {"write-heavy": 5, "balanced": 50, "read-heavy": 95}
THREADS = 48
T95_DF4 = 2.776
CLAIM_BOUNDARY = {
    "source_measurement": "trace_disabled",
    "performance_certified": False,
    "claim_scope": "descriptive_backoff_shape_only",
}
REPORT_FILENAMES = {
    workload: f"t2266-backoff-static-tail-{workload}.json"
    for workload in WORKLOADS
}

# Pinned transcription from t2216_model_tail.json; see module docstring.  The
# source file is intentionally not a runtime dependency.
LEGACY_TAIL_ANCHOR_TPS = {
    "write-heavy": {50: 2910478.0, 100: 2353026.0},
    "balanced": {50: 2427678.0, 100: 1865202.0},
    "read-heavy": {50: 5631740.0, 100: 4442242.0},
}
LEGACY_SOURCE = {
    "path": "t2216_model_tail.json",
    "sha256": "12599199e0694aa7bb7a590c3c34cb53c99a309d22b13e004e9c118e1909a7c9",
    "schema": "izanagi-t2216-backoff-walk/v2",
    "field": "calibrations[<workload>]",
}

CAPTION = (
    "Non-certified measurements: source_measurement=trace_disabled, "
    "performance_certified=false, claim_scope=descriptive_backoff_shape_only;\n"
    "they must not be used as grounds for variant adoption.\n"
    "s = 48 / T is aggregate time across 48 workers and includes, without "
    "separating, leader-specific costs.\n"
    "a = α/(1−α) is aborts per commit, where α = "
    "aborts/(aborts+commits).\n"
    "The stacked areas are fitted accounting components, not directly observed "
    "costs.\n"
    "A true static 1000 µs point was "
    "not measured; 999 µs is the largest value expressible by the current "
    "encoding (F718).\n"
    "This is post-hoc analysis formulated after the "
    "measurements were recorded."
)

plt = None
Text = None
FixedLocator = None
FixedFormatter = None
NullLocator = None


class TailMechanismError(ValueError):
    """A required T-2266 report or figure contract was violated."""


def _reject(message: str) -> None:
    raise TailMechanismError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        _reject(f"input report is outside the repository: {path}")


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _mean_t95(values: Sequence[float]) -> tuple[float, float]:
    samples = [float(value) for value in values]
    mean = statistics.fmean(samples)
    half = T95_DF4 * statistics.stdev(samples) / math.sqrt(len(samples))
    return mean, half


def _ols_intercept_slope(
    xs: Sequence[float], ys: Sequence[float],
) -> tuple[float, float]:
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sum(
        (x - x_mean) ** 2 for x in xs
    )
    return y_mean - slope * x_mean, slope


def load_report(path: Path, expected_workload: str) -> dict:
    """Load one report and admit only its exact six-point static series."""
    path = Path(path)
    if expected_workload not in WORKLOADS:
        _reject(f"unknown expected workload: {expected_workload}")
    if path.name != REPORT_FILENAMES[expected_workload]:
        _reject(
            f"report filename does not match workload {expected_workload}: {path.name}"
        )
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _reject(f"cannot read report {path}: {exc}")
    if not isinstance(report, Mapping):
        _reject(f"report root must be an object: {path}")
    exact_fields = {
        "schema_version": REPORT_SCHEMA,
        "run_kind": RUN_KIND,
        "status": "complete",
        "workload": expected_workload,
        "realized_us": list(STATIC_BACKOFF_US),
    }
    for field, expected in exact_fields.items():
        if report.get(field) != expected:
            _reject(f"{field} mismatch for {expected_workload}")

    all_points = report.get("points")
    if not isinstance(all_points, list):
        _reject(f"points must be a list for {expected_workload}")
    static_points = [point for point in all_points
                     if isinstance(point, Mapping) and point.get("kind") == "static"]
    if len(static_points) != 6:
        _reject(f"static point count must be six for {expected_workload}")
    try:
        static_points.sort(key=lambda point: point.get("backoff_us"))
    except TypeError:
        _reject(f"static backoff values are not sortable for {expected_workload}")
    if [point.get("backoff_us") for point in static_points] != list(
            STATIC_BACKOFF_US):
        _reject(f"static backoff grid mismatch for {expected_workload}")

    admitted = []
    for point in static_points:
        reps = point.get("reps")
        if not isinstance(reps, list) or len(reps) != 5:
            _reject(
                f"static point repetitions must be five at "
                f"{expected_workload}/{point.get('backoff_us')}us"
            )
        for rep in reps:
            throughput = rep.get("throughput_tps") if isinstance(rep, Mapping) else None
            abort_rate = rep.get("abort_rate") if isinstance(rep, Mapping) else None
            if not _finite_number(throughput) or float(throughput) <= 0:
                _reject(
                    f"invalid throughput repetition at "
                    f"{expected_workload}/{point.get('backoff_us')}us"
                )
            if (not _finite_number(abort_rate)
                    or not 0 <= float(abort_rate) < 1):
                _reject(
                    f"invalid abort repetition at "
                    f"{expected_workload}/{point.get('backoff_us')}us"
                )
        admitted.append({
            "kind": "static",
            "backoff_us": int(point["backoff_us"]),
            "reps": [
                {
                    "rep": rep.get("rep"),
                    "throughput_tps": float(rep["throughput_tps"]),
                    "abort_rate": float(rep["abort_rate"]),
                }
                for rep in reps
            ],
        })
    return {
        "workload": expected_workload,
        "campaign_id": report.get("campaign_id"),
        "realized_us": list(report["realized_us"]),
        "source_path": path.resolve(),
        "sha256": _sha256(path),
        "static_points": admitted,
    }


def load_reports() -> list[dict]:
    """Load the three fixed, checked-in reports in figure column order."""
    return [
        load_report(INPUT_DIR / REPORT_FILENAMES[workload], workload)
        for workload in WORKLOADS
    ]


def analyze_report(report: Mapping) -> dict:
    """Recompute repetition means, t-CIs, accounting OLS, and power-law OLS."""
    workload = str(report["workload"])
    points = report["static_points"]
    if (len(points) != 6
            or [point.get("backoff_us") for point in points]
            != list(STATIC_BACKOFF_US)
            or any(point.get("kind") != "static" for point in points)):
        _reject(f"analysis series is not the exact static series: {workload}")

    calculated = []
    for point in points:
        backoff = int(point["backoff_us"])
        throughput_reps = [float(rep["throughput_tps"]) for rep in point["reps"]]
        abort_reps = [float(rep["abort_rate"]) for rep in point["reps"]]
        throughput, throughput_ci = _mean_t95(throughput_reps)
        abort_rate, abort_ci = _mean_t95(abort_reps)
        service = THREADS * 1e6 / throughput
        aborts_per_commit = abort_rate / (1.0 - abort_rate)
        residual = service - aborts_per_commit * backoff
        service_reps = [THREADS * 1e6 / value for value in throughput_reps]
        residual_reps = [
            THREADS * 1e6 / tps - (alpha / (1.0 - alpha)) * backoff
            for tps, alpha in zip(throughput_reps, abort_reps)
        ]
        service_rep_mean, service_ci = _mean_t95(service_reps)
        residual_rep_mean, residual_ci = _mean_t95(residual_reps)
        calculated.append({
            "backoff_us": backoff,
            "throughput_mean_tps": throughput,
            "throughput_ci95_half_tps": throughput_ci,
            "abort_rate_mean": abort_rate,
            "abort_rate_ci95_half": abort_ci,
            "service_time_us": service,
            "service_time_ci95_half_us": service_ci,
            "service_time_ci95_lower_us": service_rep_mean - service_ci,
            "service_time_ci95_upper_us": service_rep_mean + service_ci,
            "aborts_per_commit": aborts_per_commit,
            "residual_us": residual,
            "residual_ci95_half_us": residual_ci,
            "residual_ci95_lower_us": residual_rep_mean - residual_ci,
            "residual_ci95_upper_us": residual_rep_mean + residual_ci,
        })

    abort_counts = [point["aborts_per_commit"] for point in calculated]
    residuals = [point["residual_us"] for point in calculated]
    u, r = _ols_intercept_slope(abort_counts, residuals)
    for point in calculated:
        a = point["aborts_per_commit"]
        b = point["backoff_us"]
        model_service = u + a * (r + b)
        model_tps = THREADS * 1e6 / model_service
        point.update({
            "commit_cost_u_us": u,
            "abort_overhead_a_r_us": a * r,
            "backoff_wait_a_b_us": a * b,
            "model_service_time_us": model_service,
            "cost_model_tps": model_tps,
            "cost_model_error_tps": model_tps - point["throughput_mean_tps"],
            "cost_model_relative_error": (
                model_tps / point["throughput_mean_tps"] - 1.0
            ),
        })

    log_b = [math.log(float(point["backoff_us"])) for point in calculated]
    log_alpha = [math.log(point["abort_rate_mean"]) for point in calculated]
    log_c, g = _ols_intercept_slope(log_b, log_alpha)
    fitted_log_alpha = [log_c + g * value for value in log_b]
    log_mean = statistics.fmean(log_alpha)
    ss_res = sum((actual - fitted) ** 2 for actual, fitted in zip(
        log_alpha, fitted_log_alpha))
    ss_tot = sum((actual - log_mean) ** 2 for actual in log_alpha)
    return {
        "workload": workload,
        "campaign_id": report.get("campaign_id"),
        "source_path": report.get("source_path"),
        "source_sha256": report.get("sha256"),
        "realized_us": list(report["realized_us"]),
        "u_us": u,
        "r_us_per_abort": r,
        "power_law": {
            "c": math.exp(log_c),
            "g": g,
            "r_squared": 1.0 - ss_res / ss_tot,
        },
        "points": calculated,
    }


def analyze_reports(reports: Sequence[Mapping]) -> list[dict]:
    """Analyze the supplied workload reports."""
    return [analyze_report(report) for report in reports]


def refuted_exponential_tps(workload: str, backoff_us: float) -> float:
    """Evaluate the refuted 50/100-us exponential extrapolation."""
    anchors = LEGACY_TAIL_ANCHOR_TPS[workload]
    k = (math.log(anchors[100]) - math.log(anchors[50])) / (100.0 - 50.0)
    return anchors[100] * math.exp(k * (float(backoff_us) - 100.0))


def _load_plot_deps() -> None:
    global plt, Text, FixedLocator, FixedFormatter, NullLocator
    if plt is not None:
        return
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as pyplot
    from matplotlib.text import Text as MatplotlibText
    from matplotlib.ticker import FixedFormatter as MatplotlibFixedFormatter
    from matplotlib.ticker import FixedLocator as MatplotlibFixedLocator
    from matplotlib.ticker import NullLocator as MatplotlibNullLocator

    plt = pyplot
    Text = MatplotlibText
    FixedLocator = MatplotlibFixedLocator
    FixedFormatter = MatplotlibFixedFormatter
    NullLocator = MatplotlibNullLocator


def _style() -> None:
    plt.rcParams.update({
        "font.size": 8.0,
        "axes.titlesize": 9.0,
        "axes.labelsize": 8.0,
        "legend.fontsize": 6.8,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
    })


def _validate_text_bboxes(fig) -> None:
    """Fail before save if visible text overlaps or leaves the figure."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    texts = []
    for item in fig.findobj(Text):
        if not item.get_visible() or not item.get_text().strip():
            continue
        box = item.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if (box.x0 < figure_box.x0 - 1 or box.y0 < figure_box.y0 - 1
                or box.x1 > figure_box.x1 + 1 or box.y1 > figure_box.y1 + 1):
            _reject(f"text bbox leaves figure: {item.get_text()!r}")
        texts.append((item, box))
    overlaps = []
    for index, (left, left_box) in enumerate(texts):
        for right, right_box in texts[index + 1:]:
            if left_box.overlaps(right_box):
                overlaps.append((left.get_text(), right.get_text()))
    if overlaps:
        _reject(f"text bbox overlap (tick labels included): {overlaps}")


def make_figure(analyses: Sequence[Mapping]):
    """Return the real 3x3 matplotlib Figure and semantic artist records."""
    _load_plot_deps()
    _style()
    fig, axes = plt.subplots(
        3, 3, figsize=(12.8, 9.8), squeeze=False, sharex=False, sharey=False
    )
    colors = {
        "measured": "#202020",
        "cost": "#1f77b4",
        "legacy": "#d62728",
        "u": "#b8cbe3",
        "ar": "#74a9cf",
        "ab": "#2b8cbe",
        "power": "#6a3d9a",
    }
    artist_records = []
    for column, analysis in enumerate(analyses):
        workload = str(analysis["workload"])
        points = analysis["points"]
        xs = [point["backoff_us"] for point in points]

        top = axes[0, column]
        top.errorbar(
            xs,
            [point["throughput_mean_tps"] / 1e6 for point in points],
            yerr=[point["throughput_ci95_half_tps"] / 1e6 for point in points],
            fmt="o", color=colors["measured"], ecolor=colors["measured"],
            elinewidth=0.9, capsize=2.0, markersize=3.7, label="measured",
            zorder=4,
        )
        top.plot(
            xs, [point["cost_model_tps"] / 1e6 for point in points],
            color=colors["cost"], linewidth=1.5, label="cost model", zorder=3,
        )
        top.plot(
            xs, [refuted_exponential_tps(workload, x) / 1e6 for x in xs],
            color=colors["legacy"], linewidth=1.3, linestyle="--",
            label="refuted exponential", zorder=2,
        )
        top.set_title(f"{workload} (read ratio {RRATIOS[workload]}%)")
        top.set_ylabel("throughput (million transactions/s)")
        top.legend(loc="best", frameon=False)

        middle = axes[1, column]
        components = [
            [point["commit_cost_u_us"] for point in points],
            [point["abort_overhead_a_r_us"] for point in points],
            [point["backoff_wait_a_b_us"] for point in points],
        ]
        middle.stackplot(
            xs, *components,
            labels=("commit cost u", "abort overhead a·r", "backoff wait a·b"),
            colors=(colors["u"], colors["ar"], colors["ab"]), alpha=0.9,
        )
        middle.errorbar(
            xs, [point["service_time_us"] for point in points],
            yerr=[
                [
                    point["service_time_us"]
                    - point["service_time_ci95_lower_us"]
                    for point in points
                ],
                [
                    point["service_time_ci95_upper_us"]
                    - point["service_time_us"]
                    for point in points
                ],
            ],
            fmt="o", color=colors["measured"], ecolor=colors["measured"],
            elinewidth=0.9, capsize=2.0, markersize=3.5, label="measured",
            zorder=4,
        )
        middle.set_ylabel("aggregate time s (µs)")
        middle.legend(loc="best", frameon=False)

        bottom = axes[2, column]
        bottom.errorbar(
            xs, [point["abort_rate_mean"] for point in points],
            yerr=[point["abort_rate_ci95_half"] for point in points],
            fmt="o", color=colors["measured"], ecolor=colors["measured"],
            elinewidth=0.9, capsize=2.0, markersize=3.7, label="measured",
            zorder=4,
        )
        dense_x = [
            math.exp(math.log(STATIC_BACKOFF_US[0]) + index / 119.0 * (
                math.log(STATIC_BACKOFF_US[-1]) - math.log(STATIC_BACKOFF_US[0])))
            for index in range(120)
        ]
        power = analysis["power_law"]
        bottom.plot(
            dense_x, [power["c"] * value ** power["g"] for value in dense_x],
            color=colors["power"], linewidth=1.5, label="power law", zorder=3,
        )
        bottom.set_ylabel("abort rate α")
        bottom.set_xlabel("static backoff b (µs)")
        bottom.legend(loc="best", frameon=False)

        for row in range(3):
            axis = axes[row, column]
            axis.set_xscale("log")
            axis.set_xlim(140, 1070)
            axis.xaxis.set_major_locator(FixedLocator((150, 300, 500, 999)))
            axis.xaxis.set_major_formatter(
                FixedFormatter(("150", "300", "500", "999"))
            )
            axis.xaxis.set_minor_locator(NullLocator())
            axis.grid(axis="y", color="#dddddd", linewidth=0.6, zorder=0)
        artist_records.append({
            "workload": workload,
            "labels": [
                "measured", "cost model", "refuted exponential",
                "commit cost u", "abort overhead a·r", "backoff wait a·b",
                "power law",
            ],
        })

    fig.suptitle(
        "T-2266 static-backoff tail — descriptive accounting fits\n"
        "48 threads, 1,000,000 records, Zipf 0.9, "
        "read-modify-write disabled",
        fontsize=10.0, y=0.985,
    )
    fig.text(
        0.075, 0.012, CAPTION, ha="left", va="bottom", fontsize=6.4,
        linespacing=1.18,
    )
    fig.subplots_adjust(
        left=0.075, right=0.985, top=0.91, bottom=0.18,
        wspace=0.31, hspace=0.34,
    )
    _validate_text_bboxes(fig)
    fig._t2266_artist_series = artist_records
    return fig, artist_records


def build_provenance(
    reports: Sequence[Mapping], analyses: Sequence[Mapping], outputs: Sequence[Path],
) -> dict:
    """Build the narrow proof record required for the generated PNG and PDF."""
    generator = Path(__file__).resolve()
    inputs = []
    for report in reports:
        source_path = Path(report["source_path"])
        inputs.append({
            "path": _repo_relative(source_path),
            "sha256": _sha256(source_path),
            "campaign_id": report.get("campaign_id"),
            "realized_us": list(report["realized_us"]),
        })
    workload_results = []
    for analysis in analyses:
        workload_results.append({
            "workload": analysis["workload"],
            "u_us": analysis["u_us"],
            "r_us_per_abort": analysis["r_us_per_abort"],
            "power_law": dict(analysis["power_law"]),
            "points": [dict(point) for point in analysis["points"]],
        })
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "inputs": inputs,
        "generator": {
            "path": _repo_relative(generator),
            "sha256": _sha256(generator),
        },
        "outputs": [
            {"path": os.fspath(Path(path)), "sha256": _sha256(Path(path))}
            for path in outputs
        ],
        "measurement_conditions": {
            "threads": THREADS,
            "records": 1_000_000,
            "zipf_skew": 0.9,
            "rmw": 0,
            "rratio": dict(RRATIOS),
        },
        "claim_boundary": dict(CLAIM_BOUNDARY),
        "workloads": workload_results,
        "legacy_exponential": {
            "anchors_tps": LEGACY_TAIL_ANCHOR_TPS,
            "source": dict(LEGACY_SOURCE),
        },
        "caption": CAPTION,
    }


def generate(out_prefix: Path) -> tuple[Path, Path, Path]:
    """Generate PNG, PDF, and provenance JSON from the fixed repo inputs."""
    reports = load_reports()
    analyses = analyze_reports(reports)
    figure, _artists = make_figure(analyses)
    prefix = Path(out_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    png = Path(f"{prefix}.png")
    pdf = Path(f"{prefix}.pdf")
    provenance_path = Path(f"{prefix}.provenance.json")
    try:
        for output in (png, pdf):
            _validate_text_bboxes(figure)
            figure.savefig(output, dpi=200, bbox_inches="tight")
        provenance = build_provenance(reports, analyses, (png, pdf))
        provenance_path.write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    finally:
        plt.close(figure)
    return png, pdf, provenance_path


def main(argv: Sequence[str]) -> int:
    """CLI entry point."""
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    if len(argv) != 2:
        print("[error] OUT_PREFIX is required", file=sys.stderr)
        return 2
    try:
        outputs = generate(Path(argv[1]))
    except (TailMechanismError, OSError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    print("wrote " + " / ".join(os.fspath(path) for path in outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
