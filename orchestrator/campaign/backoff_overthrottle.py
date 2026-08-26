# -*- coding: utf-8 -*-
"""B-10 ADD_ANALYSIS diagnostics bound to certified extended-sweep variants."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
from pathlib import Path
from typing import Iterable, Mapping, Optional

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator.benchparse import abort_rate, latency_ns, throughput_tps  # noqa: E402
from ..calibrator.runner import run_once  # noqa: E402
from . import buildcache, p2_2, pin, screening_driver, source_digest, wal  # noqa: E402
from .artifact_admission import CampaignReadPurpose, require_certified_campaign_view  # noqa: E402
from .backoff_extended_sweep import (  # noqa: E402
    WORKLOADS,
    WORKLOAD_BY_TAG,
    config_for,
    genomes,
)
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from .lock import bench_lock  # noqa: E402
from .model import Genome  # noqa: E402
from .replay import discover_campaign_dir  # noqa: E402


EXTIME = 3
REPS = 3
JSONL_SCHEMA = "b10-backoff-overthrottle-rep/v1"
MANIFEST_SCHEMA = "b10-backoff-overthrottle-manifest/v1"
SOURCE_MEASUREMENT = "add_analysis"


def _aa_genome(reference: Genome) -> Genome:
    if "ADD_ANALYSIS" in reference.flags:
        raise ValueError("certified reference genome unexpectedly contains ADD_ANALYSIS")
    return Genome(reference.protocol, {**reference.flags, "ADD_ANALYSIS": 1})


def _point_label(genome: Genome) -> str:
    if genome.flags.get("BACK_OFF") == 0:
        return "none"
    amount = genome.flags.get("BACKOFF_FIXED")
    return "adaptive" if amount == -1 else f"fixed-{amount}us"


def _flags(workload: Mapping[str, str], contract) -> list[str]:
    return [
        f"-thread_num={p2_2.THREADS}",
        f"-ycsb_tuple_num={p2_2.RECORDS}",
        f"-extime={EXTIME}",
        f"-clocks_per_us={contract.clocks_per_us}",
        *[f"-{key}={value}" for key, value in workload.items()],
    ]


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _append_jsonl(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        payload = _canonical_json_bytes(value)
        written = os.write(fd, payload)
        if written != len(payload):
            raise OSError(f"short JSONL append: {written}/{len(payload)}")
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_create_only(path: Path, value: object) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        payload = _canonical_json_bytes(value)
        written = os.write(fd, payload)
        if written != len(payload):
            raise OSError(f"short manifest write: {written}/{len(payload)}")
        os.fsync(fd)
    finally:
        os.close(fd)


def _parse_flags(canonical: str) -> dict[str, int]:
    try:
        protocol, body = canonical.split("|", 1)
        if protocol != "silo":
            raise ValueError("protocol")
        return {
            key: int(value)
            for key, value in (item.split("=", 1) for item in body.split(","))
        }
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid committed genome: {canonical!r}") from exc


def require_complete_bindings(
        expected_genomes: Iterable[Genome], bindings: Mapping[str, str]) -> None:
    """Fail closed unless every expected non-AA genome has one variant binding."""
    expected = {genome.canonical() for genome in expected_genomes}
    if set(bindings) != expected or any(type(value) is not str or not value for value in bindings.values()):
        missing = sorted(expected - set(bindings))
        extra = sorted(set(bindings) - expected)
        raise RuntimeError(
            f"certified AA reference set mismatch: missing={missing!r}, extra={extra!r}"
        )


def certified_reference_bindings(
        tag: str, output_root: str) -> tuple[str, dict[str, str], object]:
    """Bind every AA point to a committed and certified non-AA variant."""
    cfg = config_for(tag, WORKLOAD_BY_TAG[tag])
    view = require_certified_campaign_view(discover_campaign_dir(
        cfg.spec_slug,
        cfg.search_tag,
        output_root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ))
    states = wal.replay_admitted_records(view.records)
    bindings: dict[str, str] = {}
    for variant, state in states.items():
        if not state.committed:
            continue
        start = state.committed_build_start
        verifies = state.committed_verify
        if start is None or not verifies or not all(
                record.payload.get("certified") is True for record in verifies):
            raise RuntimeError(
                f"AA reference is not attempt-bound and certified: variant={variant}"
            )
        canonical = start.payload.get("genome")
        parsed = _parse_flags(canonical)
        if "ADD_ANALYSIS" in parsed:
            raise RuntimeError("AA reference campaign contains ADD_ANALYSIS")
        previous = bindings.setdefault(canonical, variant)
        if previous != variant:
            raise RuntimeError(f"duplicate certified reference genome: {canonical}")

    require_complete_bindings(genomes(tag), bindings)
    return os.path.basename(view.layout.root), bindings, view.layout


def _finite(value: object, *, field: str, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{field} is missing or non-numeric")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise RuntimeError(f"{field} is non-finite or outside its admitted range: {value!r}")
    return result


def extract_rep_values(metrics: Mapping[str, str], reference: Genome) -> dict[str, float]:
    """Parse one AA rep; only BACK_OFF=0 admits a missing spin line as zero."""
    raw_spin = metrics.get("backoff_latency_rate")
    if raw_spin in {None, ""}:
        if reference.flags.get("BACK_OFF") != 0:
            raise RuntimeError("BACK_OFF=1 is missing backoff_latency_rate")
        spin = 0.0
    else:
        try:
            spin = _finite(float(raw_spin), field="backoff_latency_rate")
        except (TypeError, ValueError) as exc:
            raise RuntimeError("backoff_latency_rate is invalid") from exc
        if reference.flags.get("BACK_OFF") == 0 and spin != 0.0:
            raise RuntimeError("BACK_OFF=0 reported non-zero backoff_latency_rate")
    tps = _finite(throughput_tps(dict(metrics)), field="throughput_tps", positive=True)
    abort = _finite(abort_rate(dict(metrics)), field="abort_rate")
    latency = _finite(latency_ns(dict(metrics)), field="latency_ns", positive=True)
    if not 0.0 <= abort <= 1.0:
        raise RuntimeError(f"abort_rate outside [0,1]: {abort!r}")
    if spin >= 1.0:
        raise RuntimeError(f"backoff_latency_rate leaves no finite effective TPS: {spin!r}")
    return {
        "backoff_latency_rate": spin,
        "abort_rate": abort,
        "latency_ns": latency,
        "tps_aa": tps,
        "eff_tps": tps / (1.0 - spin),
    }


def _value(value: float) -> dict[str, object]:
    return {
        "value": value,
        "source_measurement": SOURCE_MEASUREMENT,
        "certified": False,
        "diagnostic_only": True,
    }


def _load_existing(path: Path, *, workload: str, campaign_id: str) -> list[dict]:
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise RuntimeError("AA JSONL has a partial trailing record")
    rows = []
    seen: set[tuple[str, int]] = set()
    for line_number, line in enumerate(raw.splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"AA JSONL parse error at line {line_number}") from exc
        if (
            type(row) is not dict
            or row.get("schema_version") != JSONL_SCHEMA
            or row.get("workload") != workload
            or row.get("campaign_id") != campaign_id
            or row.get("certified") is not False
            or row.get("diagnostic_only") is not True
        ):
            raise RuntimeError(f"AA JSONL binding mismatch at line {line_number}")
        key = (row.get("reference_variant_id"), row.get("rep"))
        if key in seen or type(key[0]) is not str or type(key[1]) is not int:
            raise RuntimeError(f"AA JSONL duplicate or malformed key at line {line_number}")
        seen.add(key)
        rows.append(row)
    return rows


def _summaries(rows: Iterable[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["reference_variant_id"], []).append(row)
    summaries = []
    for variant, reps in sorted(grouped.items(), key=lambda item: item[1][0]["point_index"]):
        reps.sort(key=lambda row: row["rep"])
        summary = {
            "workload": reps[0]["workload"],
            "workload_coordinates": reps[0]["workload_coordinates"],
            "campaign_id": reps[0]["campaign_id"],
            "reference_variant_id": variant,
            "reference_genome": reps[0]["reference_genome"],
            "aa_genome": reps[0]["aa_genome"],
            "label": reps[0]["label"],
            "point_index": reps[0]["point_index"],
            "back_off": reps[0]["back_off"],
            "backoff_us": reps[0]["backoff_us"],
            "rep_count": len(reps),
            "certified": False,
            "diagnostic_only": True,
            "values": {},
        }
        for field in (
                "backoff_latency_rate", "abort_rate", "latency_ns", "tps_aa", "eff_tps"):
            values = [row["values"][field]["value"] for row in reps]
            summary["values"][field] = _value(statistics.median(values))
        summaries.append(summary)
    return summaries


def _validate_existing_bindings(
        rows: Iterable[Mapping], references: Iterable[Genome], bindings: Mapping[str, str]) -> None:
    by_variant = {
        bindings[genome.canonical()]: (index, genome)
        for index, genome in enumerate(references)
    }
    required_values = {
        "backoff_latency_rate", "abort_rate", "latency_ns", "tps_aa", "eff_tps",
    }
    for row in rows:
        bound = by_variant.get(row.get("reference_variant_id"))
        if bound is None:
            raise RuntimeError("AA JSONL contains a variant outside the certified binding set")
        point_index, reference = bound
        if (
            row.get("rep") not in range(REPS)
            or row.get("point_index") != point_index
            or row.get("reference_genome") != reference.canonical()
            or row.get("aa_genome") != _aa_genome(reference).canonical()
            or row.get("label") != _point_label(reference)
            or row.get("back_off") != reference.flags["BACK_OFF"]
            or row.get("backoff_us") != reference.flags["BACKOFF_FIXED"]
        ):
            raise RuntimeError("AA JSONL genome or rep binding mismatch")
        values = row.get("values")
        if type(values) is not dict or set(values) != required_values:
            raise RuntimeError("AA JSONL value set mismatch")
        for value in values.values():
            if (
                type(value) is not dict
                or value.get("source_measurement") != SOURCE_MEASUREMENT
                or value.get("certified") is not False
                or value.get("diagnostic_only") is not True
                or not _finite(value.get("value"), field="AA JSONL value") == value["value"]
            ):
                raise RuntimeError("AA JSONL value provenance mismatch")


def _run_rep(binary: str, flags: list[str], numactl: list[str]):
    """Keep the no-perf and strict-return-code contract on one spyable call site."""
    with bench_lock():
        p2_2._assert_single_tenant()
        return run_once(
            binary,
            flags,
            numactl=numactl,
            use_perf=False,
            strict_returncode=True,
        )


def measure(
        tag: str, *, output_root: str, log=print,
        cache_root: str,
        binding_loader=certified_reference_bindings) -> dict:
    """Measure one workload and finish its append-only log with a manifest."""
    workload = WORKLOAD_BY_TAG[tag]
    p2_2._assert_single_tenant()
    _site, contract, _authorization = p2_2.resolve_site_runtime()
    loaded_calibration = p2_2._assert_matches_calibration(contract)
    execution_receipt, verified_calibration = screening_driver.attest_runtime_contract(
        contract,
        verified_calibration=(
            loaded_calibration.verified if contract.attestation_mode == "required" else None
        ),
    )
    verified_for_manifest = verified_calibration or loaded_calibration.verified
    campaign_id, bindings, layout = binding_loader(tag, output_root)
    require_complete_bindings(genomes(tag), bindings)
    reports_dir = Path(layout.reports_dir)
    jsonl_path = reports_dir / f"b10-backoff-overthrottle-{tag}.jsonl"
    manifest_path = reports_dir / f"b10-backoff-overthrottle-{tag}.manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"AA manifest already exists: {manifest_path}")
    existing = _load_existing(jsonl_path, workload=tag, campaign_id=campaign_id)
    _validate_existing_bindings(existing, genomes(tag), bindings)
    completed = {(row["reference_variant_id"], row["rep"]) for row in existing}

    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    toolchain_manifest = buildcache.observed_toolchain_manifest(resolved_cc, resolved_cxx)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_OVERTHROTTLE)
    ordered_references = genomes(tag)
    for point_index, reference in enumerate(ordered_references):
        reference_variant = bindings.get(reference.canonical())
        if reference_variant is None:
            raise RuntimeError(f"missing certified AA reference: {reference.canonical()}")
        missing_reps = [rep for rep in range(REPS) if (reference_variant, rep) not in completed]
        if not missing_reps:
            continue
        aa_genome = _aa_genome(reference)
        evidence = source_digest.resolve_evidence(
            aa_genome,
            pin.CURRENT_PIN,
            cxx=resolved_cxx,
        )
        generator_receipt = attest_generator_output(
            build_context,
            evidence,
            generator_input_sha256=hashlib.sha256(
                f"backoff-overthrottle/v2|{aa_genome.canonical()}".encode("utf-8")
            ).hexdigest(),
        )
        admission = derive_build_admission(
            build_context,
            evidence,
            generator_receipt=generator_receipt,
        )
        built = buildcache.build_v2(
            aa_genome,
            contract=contract,
            ccbench_commit=pin.CURRENT_PIN,
            trace=False,
            cc=resolved_cc,
            cxx=resolved_cxx,
            cache_root=cache_root,
            admission=admission,
            build_context=build_context,
            source_evidence=evidence,
            expected_toolchain_manifest=toolchain_manifest,
            declared_use_class="official",
        )
        for rep in missing_reps:
            metrics, _counters, _wall = _run_rep(
                built.binary,
                _flags(workload, contract),
                list(contract.numactl),
            )
            values = extract_rep_values(metrics, reference)
            row = {
                "schema_version": JSONL_SCHEMA,
                "workload": tag,
                "workload_coordinates": dict(workload),
                "campaign_id": campaign_id,
                "reference_variant_id": reference_variant,
                "reference_genome": reference.canonical(),
                "aa_genome": aa_genome.canonical(),
                "label": _point_label(reference),
                "point_index": point_index,
                "rep": rep,
                "back_off": reference.flags["BACK_OFF"],
                "backoff_us": reference.flags["BACKOFF_FIXED"],
                "certified": False,
                "diagnostic_only": True,
                "values": {field: _value(value) for field, value in values.items()},
            }
            _append_jsonl(jsonl_path, row)
            existing.append(row)
            completed.add((reference_variant, rep))
            log(f"[{tag}] append {_point_label(reference)} rep={rep}")

    expected_count = len(ordered_references) * REPS
    if len(existing) != expected_count:
        raise RuntimeError(
            f"AA JSONL incomplete after measurement: {len(existing)}/{expected_count}"
        )
    jsonl_sha256 = hashlib.sha256(jsonl_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "complete",
        "workload": tag,
        "workload_coordinates": dict(workload),
        "campaign_id": campaign_id,
        "record_count": len(existing),
        "records_sha256": jsonl_sha256,
        "certified": False,
        "diagnostic_only": True,
        "runtime_contract": {
            "env_tag": contract.env_tag,
            "contract_sha256": contract.contract_sha256,
            "clocks_per_us": contract.clocks_per_us,
            "numactl": list(contract.numactl),
            "records": p2_2.RECORDS,
            "threads": p2_2.THREADS,
            "ccbench_commit": pin.CURRENT_PIN,
            "toolchain_manifest": toolchain_manifest,
            "execution_receipt": execution_receipt,
            "calibration": {
                "schema_version": verified_for_manifest.schema_version,
                "sha256": verified_for_manifest.sha256,
                "attestation_profile_sha256": verified_for_manifest.attestation_profile_sha256,
            },
        },
        "points": _summaries(existing),
    }
    _write_create_only(manifest_path, manifest)
    return {"jsonl": str(jsonl_path), "manifest": str(manifest_path), **manifest}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="B-10 ADD_ANALYSIS diagnostics")
    parser.add_argument("workload", choices=[tag for tag, _workload in WORKLOADS])
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--cache-root", required=True)
    args = parser.parse_args(argv)
    result = measure(
        args.workload, output_root=args.output_root, cache_root=args.cache_root,
    )
    print(
        f"{args.workload}: {result['record_count']} rep records, "
        f"manifest={result['manifest']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
