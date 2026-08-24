#!/usr/bin/env python3
"""Promote one explicitly selected successful full-measurement attempt."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN_BASE = (REPO / "output/runs/t1618-xdist-controller-cost").resolve()
COMPRESSED_DESTINATION = HERE / "measurement-result.json.gz"
SUMMARY_DESTINATION = HERE / "measurement-summary.json"
SUMMARY_MAX_BYTES = 64 * 1024
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import measure


def _selected(source: Mapping[str, Any], names: Sequence[str]) -> dict[str, Any]:
    return {name: source[name] for name in names if name in source}


def _confidence_interval_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return _selected(source, ("low_s", "mean_s", "high_s", "n", "relative_half_width"))


def _measurement_summary(
    source: Mapping[str, Any], *, include_order_effect: bool = False
) -> dict[str, Any]:
    result = _selected(source, (
        "status", "marginal_replay_cpu_saving_vs_o1_control_s",
        "negative_control_ci_gate", "negative_control_order_gate",
    ))
    result["confidence_interval_95"] = _confidence_interval_summary(
        source["confidence_interval_95"]
    )
    if include_order_effect:
        result["abba_baab_balanced"] = source["abba_baab_balanced"]
        order_effect = source["order_effect"]
        result["order_effect"] = {
            **_selected(
                order_effect,
                ("gate", "balanced", "absolute_noise_bound_s"),
            ),
            "confidence_interval_95": (
                None
                if order_effect["confidence_interval_95"] is None
                else _confidence_interval_summary(
                    order_effect["confidence_interval_95"]
                )
            ),
        }
    return result


def _occupancy_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    result = _selected(source, (
        "status", "adopt_path_b", "sorted_item_count_vector_match", "group_to_workers_match",
        "expected_item_distribution", "observed_item_distribution",
        "expected_group_to_workers", "observed_group_to_workers",
    ))
    for name in ("expected_sorted_item_count_vector", "observed_sorted_item_count_vector"):
        if name in source:
            result[f"{name}_length"] = len(source[name])
    for name in ("missing_item_counts", "unexpected_item_counts"):
        if name in source:
            result[f"{name}_record_count"] = len(source[name])
    return result


def _linearity_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    result = _selected(source, (
        "status", "model", "all_k_measurement_gates_passed", "slope_ci_excludes_zero",
        "block_slope_count",
        "maximum_block_relative_residual", "relative_residual_threshold",
        "k1_cost_equivalence_claimed", "beta_hot_repetition_s",
    ))
    result["block_slope_confidence_interval_95"] = _confidence_interval_summary(
        source["block_slope_confidence_interval_95"]
    )
    return result


def _tests_finished_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in source.items() if key != "workers_scanned_by_event"}
    scans = source["workers_scanned_by_event"]
    result["workers_scanned_by_event_summary"] = {
        "event_count": len(scans),
        "maximum": max(scans),
        "minimum": min(scans),
        "sum": sum(scans),
    }
    return result


def _path_a_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_selected(source, (
            "adopted", "actual_controller_cpu_seconds_claimed", "hot_replay",
            "list_index_slot_probes", "marginal_replay_cpu_saving_vs_o1_control_s",
            "all_worker_clone_certification", "adoption_gate_results",
        )),
        "primary_first_worker_identity_alias": _measurement_summary(
            source["primary_first_worker_identity_alias"],
            include_order_effect=True,
        ),
        "negative_control": _measurement_summary(source["negative_control"]),
    }


def _path_b_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_selected(source, (
            "scenario", "adopted", "performance_values_emitted",
            "actual_controller_cpu_seconds_claimed", "hot_replay",
            "adoption_gate_results", "caller_values_are_additive_breakdown",
            "interaction_residual_s", "caller_counts", "item_visits", "scope_visits",
            "worker_workload_distribution",
        )),
        "total_all_real_minus_all_oracle": _measurement_summary(
            source["total_all_real_minus_all_oracle"]
        ),
        "by_caller_conditional_marginals": {
            caller: _measurement_summary(value)
            for caller, value in sorted(source["by_caller_conditional_marginals"].items())
        },
        "negative_control": _measurement_summary(source["negative_control"]),
        "occupancy_gate": _occupancy_summary(source["occupancy_gate"]),
        "tests_finished": _tests_finished_summary(source["tests_finished"]),
        "amplification_linearity": _linearity_summary(source["amplification_linearity"]),
    }


def _build_summary(
    raw: Mapping[str, Any],
    *,
    raw_sha256: str,
    raw_bytes: int,
    compressed_sha256: str,
    compressed_bytes: int,
    receipt_sha256: str,
    receipt_bytes: int,
    current_source_sha256: Mapping[str, str],
) -> dict[str, Any]:
    certification = _selected(
        raw["certification"],
        ("status", "all_controller_scenario_count", "observed_wall_s", "occupancy_adoption_summary"),
    )
    isolation = {
        "status": raw["isolation_status"],
        "authoritative": raw["authoritative"],
        **_selected(
            raw["isolation_evidence"], ("exclusive_placement_proven", "reason", "sampling")
        ),
    }
    populations = []
    for population in raw["population_results"]:
        populations.append({
            **_selected(population, (
                "population_id", "controller_id", "n", "worker_count", "pilot",
                "hot_replay", "isolation_status", "authoritative",
            )),
            "path_a": _path_a_summary(population["path_a"]),
            "path_b": {
                scenario: _path_b_summary(value)
                for scenario, value in sorted(population["path_b"].items())
            },
        })
    return {
        "schema_version": "t1618-measurement-summary/v2",
        "source_result_schema_version": raw["schema_version"],
        "status": raw["status"],
        "pilot": raw["pilot"],
        "generated_at_utc": raw["generated_at_utc"],
        "attempt": _selected(raw["attempt"], ("attempt_id", "pbs_job_id")),
        "observed_wall_s": raw["observed_wall_s"],
        "estimated_wall_s": raw["estimated_wall_s"],
        "hot_replay": raw["hot_replay"],
        "performance_values_emitted": raw["performance_values_emitted"],
        "hash_binding": {
            "raw_result": {
                "sha256": raw_sha256,
                "uncompressed_bytes": raw_bytes,
            },
            "compressed_artifact": {
                "name": COMPRESSED_DESTINATION.name,
                "format": "gzip",
                "sha256": compressed_sha256,
                "bytes": compressed_bytes,
                "decompressed_raw_result_sha256": raw_sha256,
                "decompressed_raw_result_sha256_verified_at_promotion": True,
            },
            "success_receipt": {
                "sha256": receipt_sha256,
                "bytes": receipt_bytes,
            },
            "manifest_sha256": raw["inputs"]["manifest_sha256"],
            "measured_source_sha256": raw["inputs"]["source_sha256"],
            "promotion_utility_sha256": current_source_sha256["promote_result.py"],
        },
        "environment": raw["environment"],
        "xdist_import_verification": raw["inputs"]["xdist_import_verification"],
        "certification": certification,
        "isolation": isolation,
        "artifacts": _selected(
            raw["artifacts"], ("certification_trace_records", "certification_trace_sha256")
        ),
        "population_results": populations,
        "k2_aggregate": raw["k2_aggregate"],
        "decision_rule": raw["decision_rule"],
        "limitations": raw["limitations"],
    }


def _validate_current_sources(raw: Mapping[str, Any]) -> dict[str, str]:
    current = measure._source_hashes()
    measured = raw["inputs"]["source_sha256"]
    if set(current) != set(measured):
        raise measure.MeasurementError("current and measured source file sets differ")
    changed = {name for name in current if current[name] != measured[name]}
    if changed - {"promote_result.py"}:
        raise measure.MeasurementError(
            f"current measurement source differs from measured source: {sorted(changed)}"
        )
    return current


def _write_artifacts(
    compressed_payload: bytes,
    summary_payload: bytes,
    *,
    raw_sha256: str,
    raw_bytes: int,
) -> None:
    destinations = (
        (COMPRESSED_DESTINATION, compressed_payload),
        (SUMMARY_DESTINATION, summary_payload),
    )
    created: list[Path] = []
    try:
        for destination, payload in destinations:
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            created.append(destination)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        digest = hashlib.sha256()
        expanded_bytes = 0
        with gzip.open(COMPRESSED_DESTINATION, "rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                expanded_bytes += len(chunk)
        if digest.hexdigest() != raw_sha256 or expanded_bytes != raw_bytes:
            raise OSError("on-disk gzip expansion differs from the verified payload")
    except (OSError, EOFError, gzip.BadGzipFile):
        for destination in created:
            destination.unlink(missing_ok=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args(argv)
    try:
        attempt_dir = measure.resolve_attempt_dir(args.attempt_id)
    except measure.MeasurementError as exc:
        print(f"invalid attempt: {exc}", file=sys.stderr)
        return 2
    if attempt_dir.parent != RUN_BASE:
        print("attempt directory escaped the owned run base", file=sys.stderr)
        return 2
    raw_path = attempt_dir / "raw-result.json"
    receipt_path = attempt_dir / "success-receipt.json"
    manifest_path = HERE / "input-manifest.json"
    try:
        raw_payload = raw_path.read_bytes()
        raw = json.loads(raw_payload.decode("ascii"))
        receipt = json.loads(receipt_path.read_text(encoding="ascii"))
        manifest = measure.load_manifest(manifest_path)
        measure.validate_raw_result_schema(raw)
        measure.validate_raw_result(raw, manifest)
        measure.validate_receipt(receipt, raw, raw_payload)
    except (OSError, UnicodeError, json.JSONDecodeError, measure.MeasurementError) as exc:
        print(f"attempt validation failed: {exc}", file=sys.stderr)
        return 2
    if raw.get("pilot") is not False:
        print("pilot results cannot be promoted", file=sys.stderr)
        return 2
    if raw["attempt"]["attempt_id"] != args.attempt_id:
        print("raw result attempt id mismatch", file=sys.stderr)
        return 2
    if raw["attempt"]["pbs_job_id"] != args.job_id:
        print("raw result PBS job id mismatch", file=sys.stderr)
        return 2
    if Path(receipt["raw_result_path"]).resolve() != raw_path:
        print("receipt raw-result path differs from selected attempt", file=sys.stderr)
        return 2
    if measure._sha256_path(manifest_path) != raw["inputs"]["manifest_sha256"]:
        print("current durable manifest differs from measured manifest", file=sys.stderr)
        return 2
    try:
        current_source_sha256 = _validate_current_sources(raw)
    except measure.MeasurementError as exc:
        print(f"current harness source validation failed: {exc}", file=sys.stderr)
        return 2
    raw_sha256 = hashlib.sha256(raw_payload).hexdigest()
    receipt_payload = receipt_path.read_bytes()
    receipt_sha256 = hashlib.sha256(receipt_payload).hexdigest()
    compressed_payload = gzip.compress(raw_payload, compresslevel=9, mtime=0)
    try:
        expanded_payload = gzip.decompress(compressed_payload)
    except (EOFError, gzip.BadGzipFile) as exc:
        print(f"generated gzip failed to expand: {exc}", file=sys.stderr)
        return 2
    if hashlib.sha256(expanded_payload).hexdigest() != raw_sha256:
        print("generated gzip expansion hash differs from raw result", file=sys.stderr)
        return 2
    summary = _build_summary(
        raw,
        raw_sha256=raw_sha256,
        raw_bytes=len(raw_payload),
        compressed_sha256=hashlib.sha256(compressed_payload).hexdigest(),
        compressed_bytes=len(compressed_payload),
        receipt_sha256=receipt_sha256,
        receipt_bytes=len(receipt_payload),
        current_source_sha256=current_source_sha256,
    )
    summary_payload = (
        json.dumps(summary, ensure_ascii=True, indent=1, sort_keys=True) + "\n"
    ).encode("ascii")
    if len(summary_payload) > SUMMARY_MAX_BYTES:
        print(
            f"measurement summary is too large: {len(summary_payload)} > {SUMMARY_MAX_BYTES} bytes",
            file=sys.stderr,
        )
        return 2
    try:
        _write_artifacts(
            compressed_payload,
            summary_payload,
            raw_sha256=raw_sha256,
            raw_bytes=len(raw_payload),
        )
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        print(f"cannot create durable result artifacts: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "attempt_id": args.attempt_id,
        "pbs_job_id": args.job_id,
        "compressed_destination": str(COMPRESSED_DESTINATION),
        "compressed_bytes": len(compressed_payload),
        "compressed_sha256": hashlib.sha256(compressed_payload).hexdigest(),
        "summary_destination": str(SUMMARY_DESTINATION),
        "summary_bytes": len(summary_payload),
        "raw_result_uncompressed_bytes": len(raw_payload),
        "raw_result_sha256": raw_sha256,
        "receipt_sha256": receipt_sha256,
    }, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
