# -*- coding: utf-8 -*-
"""Pure B-10 shape verdicts and workload-local report materialization."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import wal  # noqa: E402
from .artifact_admission import CampaignReadPurpose, require_certified_campaign_view  # noqa: E402
from .backoff_extended_sweep import (  # noqa: E402
    EXTENDED_SWEEP_US,
    WORKLOADS,
    WORKLOAD_BY_TAG,
    config_for,
    genomes,
)
from .backoff_overthrottle import JSONL_SCHEMA, MANIFEST_SCHEMA, REPS  # noqa: E402
from .model import Genome  # noqa: E402
from .replay import discover_campaign_dir  # noqa: E402
from ..reports.plot import DatFile, PlotSpec, Series, make_plot  # noqa: E402


DELTA = 0.030
TRACE_DISABLED = "trace_disabled"
ADD_ANALYSIS = "add_analysis"
NOISE_FLOOR_PROVENANCE = {
    "delta": DELTA,
    "source": "historical_cross_campaign_write_heavy_and_balanced",
    "environment": "legacy_environment",
    "includes_read_heavy": False,
}
CLAIM_BOUNDARY = {
    "paper_gain_eligible": False,
    "same_campaign_contrast": True,
    "prereg_frozen_comparison_rule": False,
    "estimand_matches_paper_headline": False,
    "claim_scope": "descriptive_backoff_shape_only",
}


def _finite(value: object, *, positive: bool = False) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and (not positive or float(value) > 0.0)
    )


def _contrast_interval(candidate: Mapping, peak: Mapping) -> tuple[float, float]:
    contrasts = [
        1.0 - float(candidate_rep) / float(peak_rep)
        for candidate_rep in candidate["tps_reps"]
        for peak_rep in peak["tps_reps"]
        if float(peak_rep) > 0.0
    ]
    if not contrasts:
        raise ValueError("raw-rep contrast interval is empty")
    return min(contrasts), max(contrasts)


def _perf_state(status: str) -> str:
    if status == "available":
        return "available"
    if status == "unavailable":
        return "unavailable-degraded"
    if status == "probe_error":
        return "preflight-error-no-verdict"
    raise ValueError(f"unknown perf preflight status: {status!r}")


def _input_errors(points: Sequence[Mapping]) -> list[str]:
    errors: list[str] = []
    if len(points) != len(EXTENDED_SWEEP_US) + 2:
        errors.append("all_31_points_required")
    keys = [(point.get("kind"), point.get("backoff_us")) for point in points]
    if len(set(keys)) != len(keys):
        errors.append("duplicate_points")
    statics = [point for point in points if point.get("kind") == "static"]
    if {point.get("backoff_us") for point in statics} != set(EXTENDED_SWEEP_US):
        errors.append("static_grid_mismatch")
    if sum(point.get("kind") == "none" for point in points) != 1:
        errors.append("none_reference_mismatch")
    if sum(point.get("kind") == "adaptive" for point in points) != 1:
        errors.append("adaptive_reference_mismatch")
    for point in points:
        if point.get("committed") is not True or point.get("certified") is not True:
            errors.append("non_committed_or_non_certified")
            break
        if point.get("unstable") is not False:
            errors.append("unstable_point")
            break
        if not _finite(point.get("median_tps"), positive=True):
            errors.append("non_finite_tps")
            break
        reps = point.get("tps_reps")
        if (
            type(reps) is not list
            or len(reps) < 2
            or not all(_finite(value, positive=True) for value in reps)
        ):
            errors.append("invalid_raw_tps_reps")
            break
        if not _finite(point.get("cv")) or float(point["cv"]) < 0.0:
            errors.append("invalid_cv")
            break
    return sorted(set(errors))


def shape_decision(
        points: Sequence[Mapping], *, delta: float = DELTA,
        perf_preflight_status: str = "available") -> dict:
    """Determine peak and onset from certified trace-disabled TPS only."""
    perf_state = _perf_state(perf_preflight_status)
    base = {
        **CLAIM_BOUNDARY,
        "noise_floor": dict(NOISE_FLOOR_PROVENANCE),
        "perf_state": perf_state,
    }
    if perf_state == "preflight-error-no-verdict":
        return {
            **base,
            "status": "preflight-error-no-verdict",
            "input_errors": ["perf_preflight_probe_error"],
            "peak": None,
            "onset": None,
        }
    errors = _input_errors(points)
    if errors:
        return {
            **base,
            "status": "incomplete",
            "input_errors": errors,
            "peak": None,
            "onset": None,
        }

    statics = sorted(
        (point for point in points if point["kind"] == "static"),
        key=lambda point: point["backoff_us"],
    )
    tmax = max(float(point["median_tps"]) for point in statics)
    argmax = min(
        (point for point in statics if float(point["median_tps"]) == tmax),
        key=lambda point: point["backoff_us"],
    )
    equivalent = {
        point["backoff_us"]
        for point in statics
        if 1.0 - float(point["median_tps"]) / tmax <= delta
    }
    contrast_intervals = {}
    for point in statics:
        low, high = _contrast_interval(point, argmax)
        contrast_intervals[str(point["backoff_us"])] = [low, high]
        if low <= delta <= high:
            equivalent.add(point["backoff_us"])
    equivalent_points = sorted(equivalent)
    positions = [EXTENDED_SWEEP_US.index(amount) for amount in equivalent_points]
    contiguous = positions == list(range(min(positions), max(positions) + 1))
    if not contiguous:
        peak_status = "noncontiguous_noise_plateau"
    elif EXTENDED_SWEEP_US[0] in equivalent or EXTENDED_SWEEP_US[-1] in equivalent:
        peak_status = "boundary_censored"
    elif len(equivalent) == 1:
        peak_status = "resolved"
    else:
        peak_status = "noise_bounded_interval"
    peak = {
        "status": peak_status,
        "source_measurements": [TRACE_DISABLED],
        "peak_grid_argmax_us": argmax["backoff_us"],
        "tmax": _sourced(tmax, TRACE_DISABLED),
        "noise_equivalent_peak_points_us": equivalent_points,
        "noise_bounded_interval_us": [min(equivalent), max(equivalent)],
        "raw_rep_contrast_intervals": _derived(
            contrast_intervals, TRACE_DISABLED,
        ),
    }

    onset = {
        "status": "onset_unresolved",
        "source_measurements": [TRACE_DISABLED],
        "onset_grid_us": None,
        "onset_bracket_us": None,
        "observed_lower_bound_us": None,
    }
    if contiguous:
        right = max(equivalent)
        right_index = EXTENDED_SWEEP_US.index(right)
        candidates = statics[right_index + 1:]
        for index in range(len(candidates) - 1):
            first, second = candidates[index:index + 2]
            first_drop = 1.0 - float(first["median_tps"]) / tmax
            second_drop = 1.0 - float(second["median_tps"]) / tmax
            if first_drop > delta and second_drop > delta:
                previous_us = (
                    right if index == 0 else candidates[index - 1]["backoff_us"]
                )
                onset = {
                    "status": "resolved",
                    "source_measurements": [TRACE_DISABLED],
                    "onset_grid_us": first["backoff_us"],
                    "onset_bracket_us": [previous_us, first["backoff_us"]],
                    "observed_lower_bound_us": first["backoff_us"],
                }
                break
        else:
            if candidates:
                last = candidates[-1]
                last_drop = 1.0 - float(last["median_tps"]) / tmax
                if last_drop > delta:
                    previous_us = (
                        right if len(candidates) == 1
                        else candidates[-2]["backoff_us"]
                    )
                    onset = {
                        "status": "right_censored",
                        "source_measurements": [TRACE_DISABLED],
                        "onset_grid_us": None,
                        "onset_bracket_us": [previous_us, last["backoff_us"]],
                        "observed_lower_bound_us": last["backoff_us"],
                    }
    return {
        **base,
        "status": "complete",
        "input_errors": [],
        "point_cvs": _sourced({
                (
                    str(point["backoff_us"])
                    if point["kind"] == "static"
                    else point["kind"]
                ): point["cv"]
                for point in points
            }, TRACE_DISABLED),
        "peak": peak,
        "onset": onset,
    }


def _sourced(value: object, source: str) -> dict[str, object]:
    return {"value": value, "source_measurement": source}


def _derived(value: object, *sources: str) -> dict[str, object]:
    return {"value": value, "source_measurements": list(sources)}


def _aa_genome_canonical(reference_canonical: str) -> str:
    protocol, _body = reference_canonical.split("|", 1)
    flags = _parse_flags(reference_canonical)
    if "ADD_ANALYSIS" in flags:
        raise ValueError("normal point unexpectedly contains ADD_ANALYSIS")
    return Genome(protocol, {**flags, "ADD_ANALYSIS": 1}).canonical()


def _expected_aa_binding(point: Mapping) -> dict[str, object]:
    reference = point.get("reference_genome")
    if type(reference) is not str:
        raise ValueError("normal point lacks its full reference genome")
    flags = _parse_flags(reference)
    kind = point.get("kind")
    amount = point.get("backoff_us")
    label = "none" if kind == "none" else (
        "adaptive" if kind == "adaptive" else f"fixed-{amount}us"
    )
    expected_amount = flags.get("BACKOFF_FIXED")
    if (
        flags.get("BACK_OFF") not in {0, 1}
        or expected_amount != (-1 if kind in {"none", "adaptive"} else amount)
    ):
        raise ValueError("normal point kind/backoff fields differ from full flags")
    return {
        "workload": point.get("workload"),
        "workload_coordinates": point.get("workload_coordinates"),
        "campaign_id": point.get("campaign_id"),
        "reference_variant_id": point.get("variant_id"),
        "reference_genome": reference,
        "aa_genome": _aa_genome_canonical(reference),
        "label": label,
        "point_index": point.get("point_index"),
        "back_off": flags["BACK_OFF"],
        "backoff_us": expected_amount,
        "certified": False,
        "diagnostic_only": True,
    }


def _validate_aa_values(values: object) -> None:
    required_values = {
        "backoff_latency_rate", "abort_rate", "latency_ns", "tps_aa", "eff_tps",
    }
    if type(values) is not dict or set(values) != required_values:
        raise ValueError("AA value set mismatch")
    for value in values.values():
        if (
            type(value) is not dict
            or value.get("source_measurement") != ADD_ANALYSIS
            or value.get("certified") is not False
            or value.get("diagnostic_only") is not True
            or not _finite(value.get("value"))
        ):
            raise ValueError("AA value provenance mismatch")


def _validated_aa_groups(
        normal_points: Sequence[Mapping], aa_records: Sequence[Mapping]) -> dict[str, list[Mapping]]:
    expected_by_variant = {
        point["variant_id"]: _expected_aa_binding(point) for point in normal_points
    }
    normal_variants = set(expected_by_variant)
    grouped: dict[str, list[Mapping]] = {}
    seen: set[tuple[str, int]] = set()
    for row in aa_records:
        expected = expected_by_variant.get(row.get("reference_variant_id"))
        if (
            row.get("schema_version") != JSONL_SCHEMA
            or expected is None
            or any(row.get(field) != value for field, value in expected.items())
        ):
            raise ValueError("AA record is not bound to a certified campaign point")
        key = (row["reference_variant_id"], row.get("rep"))
        if key in seen or type(key[1]) is not int or key[1] not in range(REPS):
            raise ValueError("AA record key is duplicate or malformed")
        seen.add(key)
        _validate_aa_values(row.get("values"))
        grouped.setdefault(row["reference_variant_id"], []).append(row)
    if set(grouped) != normal_variants or any(len(rows) != REPS for rows in grouped.values()):
        raise ValueError("AA point/rep set is incomplete")
    return grouped


def _spin_equivalent(static_rows: Sequence[Mapping], adaptive_spin: float) -> dict:
    ordered = sorted(static_rows, key=lambda row: row["backoff_us"])
    medians = [
        statistics.median(
            rep["values"]["backoff_latency_rate"]["value"] for rep in row["reps"]
        )
        for row in ordered
    ]
    if any(right < left for left, right in zip(medians, medians[1:])):
        return {
            "status": "ambiguous", "bracket_us": None,
            "source_measurements": ["configuration", ADD_ANALYSIS],
        }
    brackets = [
        [ordered[index]["backoff_us"], ordered[index + 1]["backoff_us"]]
        for index in range(len(ordered) - 1)
        if medians[index] <= adaptive_spin <= medians[index + 1]
    ]
    if len(brackets) > 1:
        return {
            "status": "ambiguous", "bracket_us": None,
            "source_measurements": ["configuration", ADD_ANALYSIS],
        }
    if len(brackets) == 1:
        return {
            "status": "bounded", "bracket_us": brackets[0],
            "source_measurements": ["configuration", ADD_ANALYSIS],
        }
    if adaptive_spin > medians[-1]:
        return {
            "status": "right_censored", "bracket_us": [1000, None],
            "source_measurements": ["configuration", ADD_ANALYSIS],
        }
    return {
        "status": "ambiguous", "bracket_us": None,
        "source_measurements": ["configuration", ADD_ANALYSIS],
    }


def evaluate_workload(
        normal_points: Sequence[Mapping], aa_records: Sequence[Mapping], *,
        perf_preflight_status: str = "available") -> dict:
    """Combine separately sourced tables without feeding AA values into shape decisions."""
    decision = shape_decision(
        normal_points,
        perf_preflight_status=perf_preflight_status,
    )
    groups = _validated_aa_groups(normal_points, aa_records)
    normal_by_variant = {point["variant_id"]: point for point in normal_points}
    aa_rows = [
        {
            "variant_id": variant,
            "kind": normal_by_variant[variant]["kind"],
            "backoff_us": normal_by_variant[variant]["backoff_us"],
            "reps": sorted(rows, key=lambda row: row["rep"]),
        }
        for variant, rows in groups.items()
    ]
    static_aa = [row for row in aa_rows if row["kind"] == "static"]
    adaptive = next(row for row in aa_rows if row["kind"] == "adaptive")
    adaptive_spin = statistics.median(
        row["values"]["backoff_latency_rate"]["value"] for row in adaptive["reps"]
    )
    mechanism = {
        "spin_occupancy_static_equivalent_bracket_us": _spin_equivalent(
            static_aa, adaptive_spin,
        ),
        "spin_range_separated": _derived(None, TRACE_DISABLED, ADD_ANALYSIS),
        "trace_disabled_table": [],
        "add_analysis_table": [],
    }
    selected_us: list[int] = []
    if decision["peak"] is not None:
        selected_us.extend(decision["peak"]["noise_equivalent_peak_points_us"])
    if decision["onset"] is not None and decision["onset"]["onset_grid_us"] is not None:
        onset_us = decision["onset"]["onset_grid_us"]
        selected_us.append(onset_us)
        onset_index = EXTENDED_SWEEP_US.index(onset_us)
        if onset_index + 1 < len(EXTENDED_SWEEP_US):
            selected_us.append(EXTENDED_SWEEP_US[onset_index + 1])
    selected_us = sorted(set(selected_us))
    normal_by_us = {
        point["backoff_us"]: point for point in normal_points if point["kind"] == "static"
    }
    aa_by_us = {row["backoff_us"]: row for row in static_aa}
    for amount in selected_us:
        normal = normal_by_us[amount]
        aa = aa_by_us[amount]
        mechanism["trace_disabled_table"].append({
            "backoff_us": _sourced(amount, "configuration"),
            "abort_rate": _sourced(normal.get("abort_rate"), TRACE_DISABLED),
            "latency_ns": _sourced(normal.get("latency_ns"), TRACE_DISABLED),
            "throughput_tps": _sourced(normal["median_tps"], TRACE_DISABLED),
        })
        mechanism["add_analysis_table"].append({
            "backoff_us": _sourced(amount, "configuration"),
            "backoff_latency_rate_reps": _sourced(
                [rep["values"]["backoff_latency_rate"]["value"] for rep in aa["reps"]],
                ADD_ANALYSIS,
            ),
        })
    if decision["peak"] is not None and decision["onset"]["onset_grid_us"] is not None:
        peak_spins = [
            rep["values"]["backoff_latency_rate"]["value"]
            for amount in decision["peak"]["noise_equivalent_peak_points_us"]
            for rep in aa_by_us[amount]["reps"]
        ]
        onset_index = EXTENDED_SWEEP_US.index(decision["onset"]["onset_grid_us"])
        onset_amounts = EXTENDED_SWEEP_US[onset_index:onset_index + 2]
        if len(onset_amounts) == 2:
            onset_spins = [
                rep["values"]["backoff_latency_rate"]["value"]
                for amount in onset_amounts
                for rep in aa_by_us[amount]["reps"]
            ]
            mechanism["spin_range_separated"] = _derived(
                min(onset_spins) > max(peak_spins), TRACE_DISABLED, ADD_ANALYSIS,
            )
    return {**decision, "mechanism": mechanism}


def _parse_flags(canonical: str) -> dict[str, int]:
    _protocol, body = canonical.split("|", 1)
    return {key: int(value) for key, value in (item.split("=", 1) for item in body.split(","))}


def load_normal_points(tag: str, output_root: str) -> tuple[list[dict], str, object]:
    cfg = config_for(tag, WORKLOAD_BY_TAG[tag])
    view = require_certified_campaign_view(discover_campaign_dir(
        cfg.spec_slug,
        cfg.search_tag,
        output_root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ))
    points = []
    perf_statuses = set()
    campaign_id = os.path.basename(view.layout.root)
    expected_indexes = {
        genome.canonical(): index
        for index, genome in enumerate(genomes(tag))
    }
    for variant, state in wal.replay_admitted_records(view.records).items():
        if not state.committed:
            continue
        if state.committed_build_start is None or state.committed_bench is None:
            raise ValueError(f"committed point lacks attempt-bound records: {variant}")
        flags = _parse_flags(state.committed_build_start.payload["genome"])
        bench = state.committed_bench.payload
        observation = bench.get("perf_observation")
        if observation is None:
            raise ValueError("extended sweep lacks perf preflight observation")
        perf_statuses.add(observation["preflight"]["status"])
        if flags["BACK_OFF"] == 0:
            kind, amount = "none", None
        elif flags["BACKOFF_FIXED"] < 0:
            kind, amount = "adaptive", None
        else:
            kind, amount = "static", flags["BACKOFF_FIXED"]
        indicators = bench["leading_indicators"]
        points.append({
            "variant_id": variant,
            "workload": tag,
            "workload_coordinates": dict(WORKLOAD_BY_TAG[tag]),
            "campaign_id": campaign_id,
            "reference_genome": state.committed_build_start.payload["genome"],
            "point_index": expected_indexes[state.committed_build_start.payload["genome"]],
            "kind": kind,
            "backoff_us": amount,
            "committed": True,
            "certified": bool(state.committed_verify) and all(
                record.payload.get("certified") is True for record in state.committed_verify
            ),
            "median_tps": bench["median_tps"],
            "tps_reps": list(bench["tps"]),
            "cv": bench["cv"],
            "unstable": bench["unstable"],
            "abort_rate": indicators.get("abort_rate"),
            "latency_ns": indicators.get("latency_ns"),
        })
    if len(perf_statuses) != 1:
        raise ValueError(f"perf preflight status differs within campaign: {perf_statuses!r}")
    return points, next(iter(perf_statuses)), view.layout


def load_aa_records(layout, tag: str, normal_points: Sequence[Mapping]) -> list[dict]:
    reports = Path(layout.reports_dir)
    jsonl_path = reports / f"b10-backoff-overthrottle-{tag}.jsonl"
    manifest_path = reports / f"b10-backoff-overthrottle-{tag}.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = jsonl_path.read_bytes()
    campaign_ids = {point.get("campaign_id") for point in normal_points}
    if len(campaign_ids) != 1:
        raise ValueError("normal points do not identify one campaign")
    campaign_id = next(iter(campaign_ids))
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA
        or manifest.get("status") != "complete"
        or manifest.get("workload") != tag
        or manifest.get("workload_coordinates") != WORKLOAD_BY_TAG[tag]
        or manifest.get("campaign_id") != campaign_id
        or manifest.get("certified") is not False
        or manifest.get("diagnostic_only") is not True
        or manifest.get("records_sha256") != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError("AA terminal manifest does not bind the append-only JSONL")
    rows = [json.loads(line) for line in raw.splitlines() if line]
    if manifest.get("record_count") != len(rows):
        raise ValueError("AA terminal manifest record count mismatch")
    groups = _validated_aa_groups(normal_points, rows)
    expected_by_variant = {
        point["variant_id"]: _expected_aa_binding(point) for point in normal_points
    }
    manifest_points = manifest.get("points")
    if type(manifest_points) is not list or len(manifest_points) != len(normal_points):
        raise ValueError("AA manifest point set is incomplete")
    seen_manifest = set()
    for point in manifest_points:
        if type(point) is not dict:
            raise ValueError("AA manifest point is malformed")
        variant = point.get("reference_variant_id")
        expected = expected_by_variant.get(variant)
        if (
            expected is None
            or variant in seen_manifest
            or any(point.get(field) != value for field, value in expected.items())
            or point.get("rep_count") != REPS
        ):
            raise ValueError("AA manifest point binding mismatch")
        _validate_aa_values(point.get("values"))
        if len(groups[variant]) != REPS:
            raise ValueError("AA manifest point rep binding mismatch")
        seen_manifest.add(variant)
    if seen_manifest != set(expected_by_variant):
        raise ValueError("AA manifest point binding set mismatch")
    return rows


def _markdown(tag: str, verdict: Mapping, png: str, dat: str) -> str:
    claim_boundary = {key: verdict[key] for key in CLAIM_BOUNDARY}
    claim_json = json.dumps(
        claim_boundary, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    lines = [
        f"# B-10 extended backoff report: {tag}",
        "",
        (
            "Each workload uses an independent y axis. Heights and slopes must not be "
            "compared across workloads."
        ),
        "",
        f"![{tag}]({png})",
        "",
        f"Data: `{dat}`",
        "",
        "The claim boundary below is generated directly from the verdict JSON.",
        "",
        f"Claim boundary JSON: `{claim_json}`",
        "",
        f"Peak status: `{verdict['peak']['status'] if verdict['peak'] else 'none'}`",
        f"Onset status: `{verdict['onset']['status'] if verdict['onset'] else 'none'}`",
        "",
        "## Trace-disabled measurements",
        "",
        (
            "| backoff us (configuration) | throughput tps (trace_disabled) | "
            "abort rate (trace_disabled) | latency ns (trace_disabled) |"
        ),
        "|---:|---:|---:|---:|",
    ]
    for row in verdict["mechanism"]["trace_disabled_table"]:
        lines.append(
            f"| {row['backoff_us']['value']} | {row['throughput_tps']['value']} | "
            f"{row['abort_rate']['value']} | {row['latency_ns']['value']} |"
        )
    lines += [
        "",
        "## ADD_ANALYSIS diagnostics",
        "",
        "| backoff us (configuration) | backoff latency rate reps (add_analysis) |",
        "|---:|---|",
    ]
    for row in verdict["mechanism"]["add_analysis_table"]:
        lines.append(
            f"| {row['backoff_us']['value']} | {row['backoff_latency_rate_reps']['value']} |"
        )
    lines.append("")
    return "\n".join(lines)


def report_workload(tag: str, output_root: str, log=print) -> dict:
    normal, perf_status, layout = load_normal_points(tag, output_root)
    aa = load_aa_records(layout, tag, normal)
    verdict = evaluate_workload(normal, aa, perf_preflight_status=perf_status)
    reports = Path(layout.reports_dir)
    stem = reports / f"b10-backoff-grid-{tag}"
    statics = sorted(
        (point for point in normal if point["kind"] == "static"),
        key=lambda point: point["backoff_us"],
    )
    dat_file = DatFile(
        title=f"B-10 extended static backoff: {tag}",
        columns=["backoff_us", "throughput_tps", "abort_rate", "latency_ns", "cv"],
        rows=[[
            point["backoff_us"], point["median_tps"],
            point["abort_rate"] if point["abort_rate"] is not None else float("nan"),
            point["latency_ns"] if point["latency_ns"] is not None else float("nan"),
            point["cv"],
        ] for point in statics],
        provenance={
            "campaign": os.path.basename(layout.root),
            "workload": tag,
            "claim_scope": CLAIM_BOUNDARY["claim_scope"],
            "source_measurement": TRACE_DISABLED,
        },
        build_command="orchestrator/campaign/backoff_extended_sweep.py",
        repro_command=f"python -m orchestrator.campaign.backoff_extended_sweep {tag}",
    )
    plot_spec = PlotSpec(
        title=f"B-10 extended static backoff: {tag}",
        xlabel="static backoff (us)",
        ylabel="throughput (tps; workload-local axis)",
        y2label="abort rate",
        series=[
            Series("1:2", "throughput", "x1y1", style="linespoints"),
            Series("1:3", "abort rate", "x1y2", style="linespoints"),
        ],
        extra_setup=["set yrange [0:*]", "set y2range [0:*]"],
    )
    paths = make_plot(dat_file, plot_spec, str(stem))
    verdict_path = Path(f"{stem}_verdict.json")
    verdict_path.write_text(
        json.dumps(verdict, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    report_path = Path(f"{stem}_report.md")
    report_path.write_text(
        _markdown(tag, verdict, os.path.basename(paths["png"]), os.path.basename(paths["dat"])),
        encoding="utf-8",
    )
    log(f"[{tag}] report={report_path} verdict={verdict_path}")
    return {"verdict": verdict, "report": str(report_path), "verdict_path": str(verdict_path)}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="B-10 extended backoff report")
    parser.add_argument("workload", choices=[tag for tag, _workload in WORKLOADS])
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args(argv)
    result = report_workload(args.workload, args.output_root)
    return 0 if result["verdict"]["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
