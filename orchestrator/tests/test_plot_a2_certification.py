# -*- coding: utf-8 -*-
"""A-2 certification figure: authority, projection, layout, and mutation pins."""
from __future__ import annotations

import collections
import base64
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, os.fspath(HERE))
from skiputil import skip  # noqa: E402


CANONICAL_CERT = "f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40"
CANONICAL_MANIFEST = "12d8be7a9cabd404ab3147301c2df7998a731b310ec51a93f9a99b37705a7c35"
REAL_ROOT = Path(os.environ.get(
    "IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT",
    "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c",
))
SAMPLES = {
    "rr5-stock": [2715421, 2565367, 2496060, 2470354, 2527542],
    "rr5-fixed10": [1348263, 1355011, 1345709, 1387690, 1362175],
    "rr50-stock": [3894140, 3683727, 3636364, 3627357, 3662448],
    "rr50-fixed5": [1245023, 1196920, 1248603, 1261810, 1260445],
}
ABORT = {"rr5-stock": .7767, "rr5-fixed10": .1189, "rr50-stock": .6903, "rr50-fixed5": .2048}
IDS = {cell: f"build-{index}" for index, cell in enumerate(SAMPLES)}
VARIANTS = {cell: f"variant-{index}" for index, cell in enumerate(SAMPLES)}
GENOMES = {
    "rr5-stock": {"BACKOFF_FIXED": -1, "BACK_OFF": 0},
    "rr5-fixed10": {"BACKOFF_FIXED": 10, "BACK_OFF": 1},
    "rr50-stock": {"BACKOFF_FIXED": -1, "BACK_OFF": 0},
    "rr50-fixed5": {"BACKOFF_FIXED": 5, "BACK_OFF": 1},
}
CAMPAIGNS = {"rr5": "fixture-rr5-campaign", "rr50": "fixture-rr50-campaign"}


def _plot():
    path = REPO / "tools/plotting/plot_a2_certification.py"
    spec = importlib.util.spec_from_file_location("plot_a2_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _payloads(cell: str) -> list[dict]:
    samples = SAMPLES[cell]
    mean, stdev = statistics.fmean(samples), statistics.stdev(samples)
    genome = "silo|" + ",".join(f"{k}={v}" for k, v in GENOMES[cell].items())
    common = {"variant": VARIANTS[cell], "env_tag": "pegasus", "ts": 1.0}
    rows = [
        {**common, "stage": "build_start", "payload": {
            "genome": genome, "src_token": "stock", "build_attempt_id": IDS[cell],
            "build_admission": {}, "build_admission_receipt_sha256": "receipt"}},
        {**common, "stage": "build_done", "payload": {
            "trace_bin": "trace", "perf_bin": "perf", "build_attempt_id": IDS[cell],
            "build_admission_receipt_sha256": "receipt", "trace_bin_sha256": "trace-sha",
            "perf_bin_sha256": "perf-sha", "trace_cached": False, "perf_cached": False,
            "perf_configure_cmd": "cmake", "perf_build_cmd": "cmake --build",
            "toolchain": {"cc": {"version_first_line": "gcc 11.4.0"}}, "toolchain_record_sha256": "toolchain"}},
    ]
    for index in range(6):
        rows.append({**common, "stage": "verify_done", "payload": {
            "build_attempt_id": IDS[cell], "verdict": "serializable", "certified": True,
            "commits": 100 + index, "aborts": 999999 + index, "commit_witness": {},
            "anomalies": 0, "workload": {"tag": "legacy" if index == 0 else "performance"}}})
    rows.extend([
        {**common, "stage": "bench_done", "payload": {
            "build_attempt_id": IDS[cell], "median_tps": statistics.median(samples), "cv": stdev / mean,
            "bench_wall_s": 16.0, "high_variance": False, "unstable": False, "rounds": 1,
            "cv_history": [stdev / mean], "tps": samples, "settled": True,
            "leading_indicators": {"throughput_tps": statistics.median(samples), "abort_rate": ABORT[cell],
                                   "latency_ns": 1.0, "llc_miss_rate": None, "ipc": None},
            "rep_notes": [], "run_cmd": "ycsb", "perf_observation": {"use_perf": False}}},
        {**common, "stage": "commit", "payload": {
            "fitness_tps": 999999999, "cv": stdev / mean, "high_variance": False, "unstable": False,
            "verify_configs": ["legacy", "performance"], "build_attempt_id": IDS[cell],
            "build_admission_receipt_sha256": "receipt", "contract_sha256": "contract",
            "commit_verification_receipt": {}}},
    ])
    return rows


def _raw(cell: str) -> dict:
    workload = cell.split("-")[0]
    condition = {"extime": 3, "records": 1_000_000, "reps": 5, "threads": 48,
                 "workload": {"ycsb_max_ope": "10", "ycsb_rmw": "0",
                              "ycsb_rratio": "5" if workload == "rr5" else "50", "ycsb_zipf_skew": "0.9"}}
    correctness = {
        "legacy": [{"status": "pass", "certified": True, "trace_enabled": True}],
        "performance": [{"status": "pass", "certified": True, "trace_enabled": True} for _ in range(5)],
    }
    return {
        "abort": None, "attempt_id": "fixture-attempt", "build_attempt_id": IDS[cell],
        "build_evidence": {"compile_out_evidence_scope": "source-routed evidence", "perf_bin_sha256": "perf-sha",
                           "performance_trace_disabled_build": True, "source_commit": "511c953",
                           "toolchain": {"cc": {"version_first_line": "gcc 11.4.0"}},
                           "trace_bin_sha256": "trace-sha", "trace_enabled_build": True},
        "campaign_evidence": {"campaign_id": CAMPAIGNS[workload]}, "campaign_preimage": {},
        "cell_id": cell, "correctness": correctness, "current_pin": "511c953", "genome": GENOMES[cell],
        "performance": {"build_attempt_id": IDS[cell], "perf_bin_sha256": "perf-sha", "rep_notes": [],
                        "samples_tps": SAMPLES[cell], "status": "complete", "trace_enabled": False,
                        "unstable": False, "workload": condition},
        "protocol_sha256": "protocol-sha", "schema_version": "paper-story-a2-cell-result/v2",
        "terminal": "commit", "trace0_evidence": {}, "variant": VARIANTS[cell],
    }


def _certification() -> dict:
    cells = []
    for cell in SAMPLES:
        workload, role = cell.split("-")[0], ("stock" if cell.endswith("stock") else "adopted")
        cells.append({"build_attempt_id": IDS[cell], "cell_id": cell,
                      "correctness": {"status": "certified", "legacy_repetitions_observed": 1,
                                      "performance_repetitions_observed": 5,
                                      "workload_argv_observation": "not-independently-recorded-by-existing-pipeline"},
                      "genome": GENOMES[cell], "performance": {"median_tps": statistics.median(SAMPLES[cell]),
                                                                 "status": "complete"},
                      "role": role, "workload": workload})
    return {
        "attempt_id": "fixture-attempt", "cells": cells, "current_pin": "511c953",
        "effects": {"rr5": statistics.median(SAMPLES["rr5-fixed10"]) / statistics.median(SAMPLES["rr5-stock"]) - 1,
                    "rr50": statistics.median(SAMPLES["rr50-fixed5"]) / statistics.median(SAMPLES["rr50-stock"]) - 1},
        "independent_observation_limits": {"correctness_run_argv": "not-recorded-by-existing-pipeline"},
        "protocol_sha256": "protocol-sha", "request_ids": {"rr5": "100.nqsv", "rr50": "101.nqsv"},
        "schema_version": "paper-story-a2-certification-result/v3", "source_commit": "izanagi-source",
        "status": "reject", "study": "paper-story-a2-certification",
    }


def _fixture(tmp_path: Path) -> dict:
    root = tmp_path / "measurements"
    files = {}
    for workload in ("rr5", "rr50"):
        wal = root / f"jobs/{workload}/campaigns/{CAMPAIGNS[workload]}/runs/wal.jsonl"
        wal.parent.mkdir(parents=True, exist_ok=True)
        records = sum((_payloads(cell) for cell in SAMPLES if cell.startswith(workload + "-")), [])
        wal.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")
        files[wal.relative_to(root).as_posix()] = _sha(wal)
    for cell in SAMPLES:
        raw = root / f"jobs/{cell.split('-')[0]}/raw/{cell}.json"
        _write(raw, _raw(cell))
        files[raw.relative_to(root).as_posix()] = _sha(raw)
    for workload in ("rr5", "rr50"):
        files[f"jobs/{workload}/campaigns/{CAMPAIGNS[workload]}/campaign.lock"] = "0" * 64
        files[f"jobs/{workload}/env/pegasus/claims/{CAMPAIGNS[workload]}.claim"] = "0" * 64
    claims = {workload: {"campaign_id": CAMPAIGNS[workload],
                         "claim_path": f"jobs/{workload}/env/pegasus/claims/{CAMPAIGNS[workload]}.claim",
                         "claim": {"host": f"bnode-{workload}", "job_id": f"0:{100 if workload == 'rr5' else 101}.nqsv",
                                   "created_utc": f"2026-08-27T0{5 if workload == 'rr5' else 6}:00:00Z"}}
              for workload in ("rr5", "rr50")}
    manifest = {"attempt_id": "fixture-attempt", "campaign_claims": claims, "current_pin": "511c953",
                "files": files, "protocol_sha256": "protocol-sha",
                "schema_version": "paper-story-a2-raw-manifest/v3", "study": "paper-story-a2-certification"}
    cert, manifest_path = tmp_path / "certification.json", tmp_path / "raw-manifest.json"
    _write(cert, _certification())
    _write(manifest_path, manifest)
    return {"root": root, "cert": cert, "manifest": manifest_path, "prefix": tmp_path / "fig5_fixture"}


def _producer():
    from orchestrator.campaign import paper_story_a2_certification as producer
    return producer


def _current_fixture(tmp_path: Path, *, reverse_policy_order: bool = False) -> dict:
    """Build the real producer's current full schema chain around local bytes."""
    fixture = _fixture(tmp_path)
    producer = _producer()
    frozen = json.loads((REPO / "output/insights/2026-08-24_paper-story-a2-certification/certification.json").read_text())
    policy_document = json.loads(base64.b64decode(frozen["policy_bytes_base64"], validate=True))
    if reverse_policy_order:
        policy_document["workloads"] = list(reversed(policy_document["workloads"]))
        policy_document["cells"] = policy_document["cells"][2:] + policy_document["cells"][:2]
    policy_bytes = (json.dumps(policy_document, ensure_ascii=True, indent=2) + "\n").encode()
    policy_path = tmp_path / "embedded-policy.json"
    policy_path.write_bytes(policy_bytes)
    policy = producer.load_policy(policy_path)

    tokens = {
        cell.cell_id: (
            producer.source_digest.STOCK if cell.role == "stock"
            else hashlib.sha256(f"source:{cell.cell_id}".encode()).hexdigest()
        )
        for cell in policy.cells
    }
    evidences = {}
    for cell in policy.cells:
        genome = producer._genome_for_cell(policy, cell)
        evidences[cell.cell_id] = producer.source_digest.SourceEvidence(
            schema_version=producer.source_digest.SOURCE_EVIDENCE_SCHEMA,
            source_root="/fixture/current-source",
            ccbench_commit="511c953",
            genome_sha256=hashlib.sha256(genome.canonical().encode()).hexdigest(),
            src_token=tokens[cell.cell_id],
            source_bytes_sha256=hashlib.sha256(f"bytes:{cell.cell_id}".encode()).hexdigest(),
            tracked_clean=True,
            tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
            tracked_paths=(),
        )

    protocol = policy.protocol_sha256
    for cell in policy.cells:
        raw_path = fixture["root"] / f"jobs/{cell.workload_id}/raw/{cell.cell_id}.json"
        raw = json.loads(raw_path.read_text())
        raw["schema_version"] = producer.RAW_RESULT_SCHEMA
        raw["protocol_sha256"] = protocol
        raw["src_token"] = tokens[cell.cell_id]
        _write(raw_path, raw)

    for workload in (row["id"] for row in policy.document["workloads"]):
        wal_path = fixture["root"] / f"jobs/{workload}/campaigns/{CAMPAIGNS[workload]}/runs/wal.jsonl"
        records = [json.loads(line) for line in wal_path.read_text().splitlines()]
        for cell in (cell for cell in policy.cells if cell.workload_id == workload):
            start = next(row for row in records if row["stage"] == "build_start" and row["payload"]["build_attempt_id"] == IDS[cell.cell_id])
            start["payload"]["src_token"] = tokens[cell.cell_id]
            start["payload"]["build_admission"] = {"source": evidences[cell.cell_id].as_receipt()}
        wal_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")

    receipt_paths = {}
    for workload in (row["id"] for row in policy.document["workloads"]):
        frames = []
        for cell in (cell for cell in policy.cells if cell.workload_id == workload):
            admission = {
                "admission_id": f"admission-{cell.cell_id}",
                "admission_digest": hashlib.sha256(f"admission:{cell.cell_id}".encode()).hexdigest(),
                "use_class": "paper", "admitted": True, "record_ids": [],
                "unestablished_meaning_macros": [],
            }
            frames.extend((admission, evidences[cell.cell_id].as_receipt()))
        receipt = fixture["root"] / f"receipts/condition-gate-{workload}.admissions.jsonl"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in frames), encoding="ascii")
        receipt_paths[workload] = receipt

    certification = _certification()
    by_cell = {row["cell_id"]: row for row in certification["cells"]}
    certification["cells"] = [by_cell[cell.cell_id] for cell in policy.cells]
    for row in certification["cells"]:
        row.update({
            "src_token": tokens[row["cell_id"]], "source_binding_status": "bound",
            "trace_bin_sha256": "trace-sha", "perf_bin_sha256": "perf-sha",
        })
    certification.update({
        "schema_version": producer.CERTIFICATION_SCHEMA,
        "protocol_schema": producer.POLICY_SCHEMA,
        "protocol_sha256": protocol,
        "policy_sha256": hashlib.sha256(policy_bytes).hexdigest(),
        "policy_bytes_base64": base64.b64encode(policy_bytes).decode("ascii"),
        "historical_context": {"ccbench_commit": "6656e93", "comparison_input": False},
        "a4_noise_floor_status": "open",
        "legacy_role": "historically inherited companion",
        "smallest_observed_sufficient_in_this_two_point_protocol": None,
        "global_minimality_established": False,
        "compile_out_evidence_scope": producer.COMPILE_OUT_SCOPE,
        "independent_observation_limits": {
            "correctness_run_argv": "not-recorded-by-existing-pipeline",
            "correctness_workload_binding": "campaign-lock-and-pipeline-constructor; not an independent argv observation",
        },
    })
    certification["request_ids"] = {
        workload: certification["request_ids"][workload]
        for workload in (row["id"] for row in policy.document["workloads"])
    }
    fixture["cert"].write_text(
        json.dumps(certification, separators=(",", ":")) + "\n", encoding="utf-8")

    claims = {}
    files = {}
    for workload in (row["id"] for row in policy.document["workloads"]):
        campaign = CAMPAIGNS[workload]
        claim_path = fixture["root"] / f"jobs/{workload}/env/pegasus/claims/{campaign}.claim"
        lock_path = fixture["root"] / f"jobs/{workload}/campaigns/{campaign}/campaign.lock"
        _write(claim_path, {"campaign_identity": campaign, "workload": workload})
        lock_path.write_text(f"lock:{campaign}\n", encoding="utf-8")
        claims[workload] = {
            "campaign_id": campaign,
            "claim_path": claim_path.relative_to(fixture["root"]).as_posix(),
            "claim": {"host": f"bnode-{workload}",
                      "job_id": f"0:{100 if workload == 'rr5' else 101}.nqsv",
                      "created_utc": f"2026-08-27T0{5 if workload == 'rr5' else 6}:00:00Z"},
        }
        paths = [
            fixture["root"] / f"jobs/{workload}/campaigns/{campaign}/runs/wal.jsonl",
            lock_path, claim_path, receipt_paths[workload],
            *(fixture["root"] / f"jobs/{workload}/raw/{cell.cell_id}.json"
              for cell in policy.cells if cell.workload_id == workload),
        ]
        files.update({path.relative_to(fixture["root"]).as_posix(): _sha(path) for path in paths})
    manifest = {
        "attempt_id": "fixture-attempt", "campaign_claims": claims,
        "current_pin": "511c953", "files": files, "protocol_sha256": protocol,
        "schema_version": producer.RAW_MANIFEST_SCHEMA, "study": "paper-story-a2-certification",
    }
    fixture["manifest"].write_text(
        json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8")
    fixture.update({"policy": policy, "tokens": tokens})
    return fixture


def _hashes(fixture: dict) -> dict[str, str]:
    return {"certification": _sha(fixture["cert"]), "raw_manifest": _sha(fixture["manifest"])}


def _load(plot, fixture):
    return plot.load_measurements(fixture["root"], fixture["cert"], fixture["manifest"], _hashes(fixture))


def _change_raw(fixture, cell, change) -> None:
    path = fixture["root"] / f"jobs/{cell.split('-')[0]}/raw/{cell}.json"
    value = json.loads(path.read_text(encoding="utf-8")); change(value); _write(path, value)
    manifest = json.loads(fixture["manifest"].read_text(encoding="utf-8"))
    manifest["files"][path.relative_to(fixture["root"]).as_posix()] = _sha(path); _write(fixture["manifest"], manifest)


def _change_cert(fixture, change) -> None:
    value = json.loads(fixture["cert"].read_text(encoding="utf-8")); change(value); _write(fixture["cert"], value)


def _change_manifest(fixture, change) -> None:
    value = json.loads(fixture["manifest"].read_text(encoding="utf-8")); change(value); _write(fixture["manifest"], value)


def _rebind_member(fixture, path: Path) -> None:
    _change_manifest(
        fixture,
        lambda manifest: manifest["files"].__setitem__(
            path.relative_to(fixture["root"]).as_posix(), _sha(path)),
    )


def _change_wal_start(fixture, cell: str, change) -> None:
    workload = cell.split("-")[0]
    path = fixture["root"] / f"jobs/{workload}/campaigns/{CAMPAIGNS[workload]}/runs/wal.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    start = next(row for row in rows if row["stage"] == "build_start" and row["payload"]["build_attempt_id"] == IDS[cell])
    change(start)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    _rebind_member(fixture, path)


def _change_wal_start_payload_token(fixture, cell: str, token: str) -> None:
    _change_wal_start(
        fixture, cell,
        lambda start: start["payload"].__setitem__("src_token", token),
    )


def _change_wal_admission_source_token(fixture, cell: str, token: str) -> None:
    _change_wal_start(
        fixture, cell,
        lambda start: start["payload"]["build_admission"]["source"].__setitem__(
            "src_token", token),
    )


def _duplicate_wal_build_start(fixture, cell: str) -> None:
    workload = cell.split("-")[0]
    path = fixture["root"] / f"jobs/{workload}/campaigns/{CAMPAIGNS[workload]}/runs/wal.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    index = next(
        index for index, row in enumerate(rows)
        if row["stage"] == "build_start"
        and row["payload"]["build_attempt_id"] == IDS[cell]
    )
    rows.insert(index + 1, json.loads(json.dumps(rows[index])))
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    _rebind_member(fixture, path)


def _change_receipt_frame(fixture, workload: str, index: int, change, *, canonical: bool = True) -> None:
    path = fixture["root"] / f"receipts/condition-gate-{workload}.admissions.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    change(rows[index])
    separators = (",", ":") if canonical else None
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=separators) + "\n" for row in rows),
        encoding="ascii",
    )
    _rebind_member(fixture, path)


def _set_all_current_token_authorities(fixture, cell: str, token: str) -> None:
    workload = cell.split("-")[0]
    policy_cells = [item.cell_id for item in fixture["policy"].cells if item.workload_id == workload]
    receipt_source_index = 2 * policy_cells.index(cell) + 1
    _change_receipt_frame(
        fixture, workload, receipt_source_index,
        lambda row: row.__setitem__("src_token", token),
    )
    _change_raw(fixture, cell, lambda row: row.__setitem__("src_token", token))
    _change_wal_start_payload_token(fixture, cell, token)
    _change_wal_admission_source_token(fixture, cell, token)
    _change_cert(
        fixture,
        lambda report: next(row for row in report["cells"] if row["cell_id"] == cell).__setitem__("src_token", token),
    )


def test_current_full_profile_uses_producer_policy_and_exact_twelve_file_closure(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    data = _load(plot, fixture)
    assert data["measurement_conditions"]["artifact_profile"] == "current-full"
    assert [row["id"] for row in data["measurement_conditions"]["workloads"]] == ["rr5", "rr50"]
    assert [row["cell_id"] for row in data["cells"]] == list(SAMPLES)
    assert len(data["external_inputs"]) == 12
    assert all(row["source_binding_status"] == "bound" for row in json.loads(fixture["cert"].read_text())["cells"])
    assert data["effect_crosschecks"]["rr5"]["authority_matches"] is True
    assert _run_main(plot, fixture, _hashes(fixture)) == 0
    provenance = json.loads(Path(str(fixture["prefix"]) + ".provenance.json").read_text())
    assert len(provenance["external_inputs"]) == 12
    assert provenance["gate_note"] == data["gate_note"]


def test_current_rejects_embedded_policy_hash_mismatch(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_cert(fixture, lambda report: report.__setitem__("policy_sha256", "0" * 64))
    with pytest.raises(plot.FigureDataError, match="embedded policy SHA-256 mismatch"):
        _load(plot, fixture)


def test_current_top_level_status_uses_verdict_vocabulary_not_bound(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_cert(fixture, lambda report: report.__setitem__("status", "bound"))
    with pytest.raises(plot.FigureDataError, match="top-level status"):
        _load(plot, fixture)


def test_current_full_policy_order_is_artifact_derived(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path, reverse_policy_order=True)
    data = _load(plot, fixture)
    assert [row["id"] for row in data["measurement_conditions"]["workloads"]] == ["rr50", "rr5"]
    assert [row["cell_id"] for row in data["cells"]] == [
        "rr50-stock", "rr50-fixed5", "rr5-stock", "rr5-fixed10",
    ]


@pytest.mark.parametrize(
    ("target", "schema"),
    [
        ("cert", "paper-story-a2-certification-result/v3"),
        ("manifest", "paper-story-a2-raw-manifest/v3"),
        ("cert", "paper-story-a2-partial-result/v1"),
        ("cert", "paper-story-a2-partial-result/v2"),
        ("manifest", "paper-story-a2-raw-manifest/v4"),
        ("manifest", "paper-story-a2-raw-manifest/v5"),
    ],
)
def test_current_rejects_schema_crosses_and_partial_families(tmp_path, target, schema):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    path = fixture[target]
    value = json.loads(path.read_text()); value["schema_version"] = schema; _write(path, value)
    with pytest.raises(plot.FigureDataError, match="schema pair"):
        _load(plot, fixture)


def test_current_rejects_legacy_raw_cell_schema(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_raw(
        fixture, "rr5-fixed10",
        lambda raw: raw.__setitem__("schema_version", plot.LEGACY_RAW_SCHEMA),
    )
    with pytest.raises(plot.FigureDataError, match="raw cell schema/identity mismatch"):
        _load(plot, fixture)


def test_current_rejects_embedded_policy_protocol_identity_mismatch(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    other_protocol = "e" * 64
    _change_cert(
        fixture,
        lambda certification: certification.__setitem__(
            "protocol_sha256", other_protocol),
    )
    for cell in SAMPLES:
        _change_raw(
            fixture, cell,
            lambda raw: raw.__setitem__("protocol_sha256", other_protocol),
        )
    _change_manifest(
        fixture,
        lambda manifest: manifest.__setitem__(
            "protocol_sha256", other_protocol),
    )
    with pytest.raises(
            plot.FigureDataError,
            match="current certification and embedded policy identity mismatch"):
        _load(plot, fixture)


def test_current_rejects_duplicate_wal_build_start_mapping(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _duplicate_wal_build_start(fixture, "rr5-fixed10")
    with pytest.raises(plot.FigureDataError, match="WAL build_start mapping is not unique"):
        _load(plot, fixture)


def test_current_rejects_policy_mismatched_workload_condition(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_raw(
        fixture, "rr5-fixed10",
        lambda raw: raw["performance"]["workload"].__setitem__("extime", 4),
    )
    with pytest.raises(plot.FigureDataError, match="structured workload conditions are missing"):
        _load(plot, fixture)


def test_current_rejects_noncanonical_campaign_claim_path(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    workload = "rr5"
    campaign = CAMPAIGNS[workload]
    canonical_relative = f"jobs/{workload}/env/pegasus/claims/{campaign}.claim"
    alias_relative = f"jobs/{workload}/env/pegasus/claims/{campaign}.alias"
    canonical = fixture["root"] / canonical_relative
    alias = fixture["root"] / alias_relative
    alias.write_bytes(canonical.read_bytes())
    canonical.unlink()

    def change(manifest):
        digest = manifest["files"].pop(canonical_relative)
        manifest["files"][alias_relative] = digest
        manifest["campaign_claims"][workload]["claim_path"] = alias_relative

    _change_manifest(fixture, change)
    with pytest.raises(plot.FigureDataError, match="current campaign claim path mismatch"):
        _load(plot, fixture)


def test_current_rejects_symlinked_campaign_claim_path(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    workload = "rr5"
    campaign = CAMPAIGNS[workload]
    claim = fixture["root"] / f"jobs/{workload}/env/pegasus/claims/{campaign}.claim"
    outside = tmp_path / "outside-claim"
    outside.write_bytes(claim.read_bytes())
    claim.unlink()
    claim.symlink_to(outside)
    with pytest.raises(plot.FigureDataError, match="external input path traverses a symlink"):
        _load(plot, fixture)


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_current_rejects_twelve_file_closure_underflow_and_overflow(tmp_path, change):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    if change == "missing":
        _change_manifest(fixture, lambda manifest: manifest["files"].pop(next(iter(manifest["files"]))))
    else:
        _change_manifest(fixture, lambda manifest: manifest["files"].__setitem__("unexpected", "0" * 64))
    with pytest.raises(plot.FigureDataError, match="12-file closure"):
        _load(plot, fixture)


def test_current_rejects_missing_manifest_bound_condition_receipt(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    path = fixture["root"] / "receipts/condition-gate-rr5.admissions.jsonl"
    path.unlink()
    with pytest.raises(plot.FigureDataError, match="external input missing"):
        _load(plot, fixture)


def test_current_rejects_condition_receipt_hash_mismatch(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    path = fixture["root"] / "receipts/condition-gate-rr5.admissions.jsonl"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(plot.FigureDataError, match="SHA-256 mismatch"):
        _load(plot, fixture)


def test_current_hash_checks_passive_campaign_closure_members(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    path = fixture["root"] / f"jobs/rr5/campaigns/{CAMPAIGNS['rr5']}/campaign.lock"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(plot.FigureDataError, match="SHA-256 mismatch"):
        _load(plot, fixture)


def test_current_rejects_noncanonical_condition_receipt(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_receipt_frame(fixture, "rr5", 0, lambda row: None, canonical=False)
    with pytest.raises(plot.FigureDataError, match="condition receipt is invalid"):
        _load(plot, fixture)


def test_current_rejects_condition_receipt_admitted_false(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_receipt_frame(fixture, "rr5", 0, lambda row: row.__setitem__("admitted", False))
    with pytest.raises(plot.FigureDataError, match="condition receipt is invalid"):
        _load(plot, fixture)


@pytest.mark.parametrize("authority", ["receipt", "raw", "certification"])
def test_current_rejects_each_src_token_authority_mismatch(tmp_path, authority):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    other = "f" * 64
    if authority == "receipt":
        _change_receipt_frame(fixture, "rr5", 3, lambda row: row.__setitem__("src_token", other))
    elif authority == "raw":
        _change_raw(fixture, "rr5-fixed10", lambda row: row.__setitem__("src_token", other))
    else:
        _change_cert(fixture, lambda row: row["cells"][1].__setitem__("src_token", other))
    with pytest.raises(plot.FigureDataError, match="src_token mismatch"):
        _load(plot, fixture)


def test_current_rejects_wal_build_start_payload_src_token_mismatch(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_wal_start_payload_token(fixture, "rr5-fixed10", "f" * 64)
    with pytest.raises(plot.FigureDataError, match="src_token mismatch"):
        _load(plot, fixture)


def test_current_rejects_wal_build_admission_source_src_token_mismatch(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_wal_admission_source_token(fixture, "rr5-fixed10", "f" * 64)
    with pytest.raises(plot.FigureDataError, match="src_token mismatch"):
        _load(plot, fixture)


def test_current_rejects_nonbound_source_binding_status(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _change_cert(fixture, lambda row: row["cells"][1].__setitem__("source_binding_status", "token-mismatch"))
    with pytest.raises(plot.FigureDataError, match="source_binding_status is not bound"):
        _load(plot, fixture)


@pytest.mark.parametrize(
    ("cell", "token", "message"),
    [
        ("rr5-stock", "e" * 64, "stock cell src_token is not stock"),
        ("rr5-fixed10", "stock", "adopted cell src_token is not a non-stock"),
    ],
)
def test_current_rejects_role_wrong_tokens_even_when_all_four_authorities_agree(
        tmp_path, cell, token, message):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    _set_all_current_token_authorities(fixture, cell, token)
    with pytest.raises(plot.FigureDataError, match=message):
        _load(plot, fixture)


@pytest.mark.parametrize("projection", ["median", "effect"])
def test_current_recomputes_certification_medians_and_effects(tmp_path, projection):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    if projection == "median":
        _change_cert(
            fixture,
            lambda report: report["cells"][0]["performance"].__setitem__(
                "median_tps", report["cells"][0]["performance"]["median_tps"] + 1),
        )
        message = "certification median mismatch"
    else:
        _change_cert(
            fixture,
            lambda report: report["effects"].__setitem__("rr5", report["effects"]["rr5"] + .01),
        )
        message = "certification effect mismatch"
    with pytest.raises(plot.FigureDataError, match=message):
        _load(plot, fixture)


def test_current_gate_copy_is_receipt_observation_not_legacy_fixed_copy(tmp_path):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    data = _load(plot, fixture)
    caption = plot._caption(data, fixture["prefix"])
    expected_gate_note = (
        "The raw manifest binds canonical condition-admission records reporting "
        f'use_class="paper" and admitted=true for all {len(fixture["policy"].cells)} policy cells; '
        "the original supply and meaning records are not retained in this artifact."
    )
    assert data["gate_note"] == expected_gate_note
    assert caption.count(expected_gate_note) == 1
    assert "gate family was not applied" not in caption


def test_cli_has_no_caller_selected_hash_options():
    plot = _plot()
    destinations = {action.dest for action in plot._parser()._actions}
    assert "certification_sha256" not in destinations
    assert "raw_manifest_sha256" not in destinations


def test_cli_rejects_exact_bytes_at_certification_path_missing_from_pin_table(tmp_path):
    plot = _plot()
    certification = tmp_path / "certification.json"
    certification.write_bytes(plot.DEFAULT_CERT.read_bytes())
    root = tmp_path / "empty-root"; root.mkdir(); prefix = tmp_path / "fig5_missing_pin"
    completed = _run_script(certification, plot.DEFAULT_MANIFEST, root, prefix)
    assert completed.returncode != 0
    assert "repository-owned pin table" in completed.stderr
    assert not any(Path(str(prefix) + suffix).exists() for suffix in (".png", ".pdf", ".provenance.json"))


def test_current_cli_reads_repository_owned_pin_table(tmp_path, monkeypatch):
    plot, fixture = _plot(), _current_fixture(tmp_path)
    key = plot._display_path(fixture["cert"])

    class ObservedPinTable(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.lookups = []

        def get(self, requested, default=None):
            self.lookups.append(requested)
            return super().get(requested, default)

    pin_table = ObservedPinTable({key: _hashes(fixture)})
    monkeypatch.setattr(plot, "CANONICAL_SHA256", pin_table)
    argv = [
        "--measurement-root", str(fixture["root"]),
        "--certification", str(fixture["cert"]),
        "--raw-manifest", str(fixture["manifest"]),
        str(fixture["prefix"]),
    ]
    assert plot.main(argv) == 0
    assert pin_table.lookups == [key]

    rejected_prefix = tmp_path / "fig5_rejected_pin"
    pin_table[key] = {
        "certification": "0" * 64,
        "raw_manifest": _sha(fixture["manifest"]),
    }
    argv[-1] = str(rejected_prefix)
    assert plot.main(argv) == 2
    assert pin_table.lookups == [key, key]
    assert not any(
        Path(str(rejected_prefix) + suffix).exists()
        for suffix in (".png", ".pdf", ".provenance.json")
    )


def _assert_named_landed_bundle(plot, prefix: Path, figures_readme: Path) -> None:
    """Reusable closure frame for the parent-owned current figure once landed."""
    paths = [Path(f"{prefix}{suffix}") for suffix in (".png", ".pdf", ".provenance.json")]
    assert all(path.is_file() for path in paths), "named figure integration bundle is incomplete"
    provenance = json.loads(paths[-1].read_text(encoding="utf-8"))
    plot.validate_repo_closure(provenance, REPO)
    assert provenance["caption"] in figures_readme.read_text(encoding="utf-8")


def test_fixture_has_production_shape_and_recomputes_statistics(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    data = _load(plot, fixture)
    counts = collections.Counter()
    for path in fixture["root"].glob("jobs/*/campaigns/*/runs/wal.jsonl"):
        counts.update(json.loads(line)["stage"] for line in path.read_text().splitlines())
    assert counts == {"build_start": 4, "build_done": 4, "verify_done": 24, "bench_done": 4, "commit": 4}
    assert len(data["external_inputs"]) == 6 and len(json.loads(fixture["manifest"].read_text())["files"]) == 10
    first = data["cells"][0]
    assert first["median_tps"] == 2527542 and first["mean_tps"] == pytest.approx(2554948.8)
    assert first["ci95_half_tps"] == pytest.approx(119798.329, abs=.001)


def test_m1_bench_done_rows_ignore_real_nonbench_stage_keys(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    wal = fixture["root"] / f"jobs/rr5/campaigns/{CAMPAIGNS['rr5']}/runs/wal.jsonl"
    rows = plot._bench_done_rows(wal)
    assert len(rows) == 2
    assert all(row["stage"] == "bench_done" for row in rows)


def test_m2_five_samples_are_required_when_all_projections_agree(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    cert = json.loads(fixture["cert"].read_text())
    manifest = json.loads(fixture["manifest"].read_text())
    for cell in SAMPLES:
        workload = cell.split("-")[0]; wal = fixture["root"] / f"jobs/{workload}/campaigns/{CAMPAIGNS[workload]}/runs/wal.jsonl"
        rows = [json.loads(line) for line in wal.read_text().splitlines()]
        bench = next(row for row in rows if row["stage"] == "bench_done" and row["payload"]["build_attempt_id"] == IDS[cell])
        values = bench["payload"]["tps"][:4]; bench["payload"]["tps"] = values
        bench["payload"]["median_tps"] = statistics.median(values); bench["payload"]["cv"] = statistics.stdev(values) / statistics.fmean(values)
        wal.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        manifest["files"][wal.relative_to(fixture["root"]).as_posix()] = _sha(wal)
        raw = fixture["root"] / f"jobs/{workload}/raw/{cell}.json"; doc = json.loads(raw.read_text())
        doc["performance"]["samples_tps"] = values; _write(raw, doc); manifest["files"][raw.relative_to(fixture["root"]).as_posix()] = _sha(raw)
        next(row for row in cert["cells"] if row["cell_id"] == cell)["performance"]["median_tps"] = statistics.median(values)
    med = {row["cell_id"]: row["performance"]["median_tps"] for row in cert["cells"]}
    cert["effects"] = {"rr5": med["rr5-fixed10"] / med["rr5-stock"] - 1, "rr50": med["rr50-fixed5"] / med["rr50-stock"] - 1}
    _write(fixture["cert"], cert); _write(fixture["manifest"], manifest)
    with pytest.raises(plot.FigureDataError, match="exactly five"):
        _load(plot, fixture)


def test_m3_external_sha256_mismatch_is_rejected(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    raw = fixture["root"] / "jobs/rr5/raw/rr5-stock.json"; raw.write_text(raw.read_text() + " \n")
    with pytest.raises(plot.FigureDataError, match="SHA-256 mismatch"):
        _load(plot, fixture)


def test_m4a_raw_samples_must_match_wal_after_manifest_rebind(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_raw(fixture, "rr5-stock", lambda d: d["performance"]["samples_tps"].__setitem__(0, d["performance"]["samples_tps"][0] + 7))
    with pytest.raises(plot.FigureDataError, match="samples_tps mismatch"):
        _load(plot, fixture)


def test_m4b_raw_build_attempt_must_match_wal_after_manifest_rebind(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_raw(fixture, "rr5-stock", lambda d: (
        d.__setitem__("build_attempt_id", "other-build"),
        d["performance"].__setitem__("build_attempt_id", "other-build")))
    with pytest.raises(plot.FigureDataError, match="build_attempt_id mismatch"):
        _load(plot, fixture)


def test_m4c_raw_variant_must_match_wal_after_manifest_rebind(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_raw(fixture, "rr5-stock", lambda d: d.__setitem__("variant", "other-variant"))
    with pytest.raises(plot.FigureDataError, match="variant mismatch"):
        _load(plot, fixture)


def test_m4d_nested_performance_build_attempt_must_match_raw_after_manifest_rebind(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_raw(fixture, "rr5-stock", lambda d: d["performance"].__setitem__("build_attempt_id", "other-build"))
    with pytest.raises(plot.FigureDataError, match="raw/performance build_attempt_id mismatch"):
        _load(plot, fixture)


def test_m5_certification_median_mismatch_is_rejected(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_cert(fixture, lambda d: d["cells"][0]["performance"].__setitem__("median_tps", d["cells"][0]["performance"]["median_tps"] + 1))
    with pytest.raises(plot.FigureDataError, match="certification median mismatch"):
        _load(plot, fixture)


def test_m6_certification_effect_mismatch_is_rejected(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_cert(fixture, lambda d: d["effects"].__setitem__("rr5", d["effects"]["rr5"] + .01))
    with pytest.raises(plot.FigureDataError, match="certification effect mismatch"):
        _load(plot, fixture)


def test_m7_outer_status_is_copied_into_provenance(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_cert(fixture, lambda d: d.__setitem__("status", "sentinel-status"))
    data = _load(plot, fixture)
    outputs = [Path(f"{fixture['prefix']}.png"), Path(f"{fixture['prefix']}.pdf")]
    for path in outputs:
        path.write_bytes(b"fixture")
    assert plot.build_provenance(data, outputs, ["plot"])["outer_status"] == "sentinel-status"


def test_m8_artist_baseline_is_stock_median_with_stock_genome(tmp_path):
    plot, data = _plot(), None
    fixture = _fixture(tmp_path); data = _load(plot, fixture)
    baselines = [row for row in plot._artist_series(data) if row["kind"] == "baseline"]
    assert [(row["value_tps"], row["genome"]) for row in baselines] == [
        (2527542, GENOMES["rr5-stock"]), (3662448, GENOMES["rr50-stock"])]


def test_m9_caption_distinguishes_correctness_from_performance(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    caption = plot._caption(_load(plot, fixture), fixture["prefix"])
    assert "separate trace-enabled runs" in caption and "not a performance certification" in caption
    assert "no significance decision" in caption and "no causal mechanism claim" in caption


def test_real_size_figure_passes_layout_and_artist_contract(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    figure, axes = plot.make_figure(_load(plot, fixture))
    try:
        plot.check_figure_layout(figure, axes)
        assert len(figure.axes) == 4 and len(figure._a2_artist_series) == 20
        assert {line.get_color() for axis in figure.axes for line in axis.lines} <= {"#777777", "#666666", "#b24a00"}
    finally:
        plot.plt.close(figure)


def test_m10_layout_failure_publishes_no_outputs(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path); data = _load(plot, fixture)
    figure, axes = plot.make_figure(data); figure.text(.5, .5, "collision"); figure.text(.5, .5, "overlap")
    try:
        with pytest.raises(plot.FigureLayoutError, match="overlap"):
            plot._publish_outputs(figure, axes, fixture["prefix"], data, ["plot"])
        assert not any(Path(str(fixture["prefix"]) + suffix).exists() for suffix in (".png", ".pdf", ".provenance.json"))
    finally:
        plot.plt.close(figure)


def _run_main(plot, fixture, expected):
    return plot.main(["--measurement-root", str(fixture["root"]), "--certification", str(fixture["cert"]),
                      "--raw-manifest", str(fixture["manifest"]), str(fixture["prefix"])], expected_hashes=expected)


def _run_script(certification: Path, manifest: Path, root: Path, prefix: Path):
    return subprocess.run(
        [sys.executable, "tools/plotting/plot_a2_certification.py", "--certification", str(certification),
         "--raw-manifest", str(manifest), "--measurement-root", str(root), str(prefix)],
        cwd=REPO, text=True, capture_output=True, check=False)


def test_caption_uses_figure_number_from_output_prefix(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    fixture["prefix"] = tmp_path / "fig6_a2_certification_observed_positive"
    assert _run_main(plot, fixture, _hashes(fixture)) == 0
    provenance = json.loads(
        Path(f"{fixture['prefix']}.provenance.json").read_text(encoding="utf-8")
    )
    assert provenance["caption"].startswith("Figure 6.")


def test_output_prefix_without_figure_number_is_rejected(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    fixture["prefix"] = tmp_path / "a2_certification_without_figure_number"
    assert _run_main(plot, fixture, _hashes(fixture)) == 2
    assert not any(
        Path(f"{fixture['prefix']}{suffix}").exists()
        for suffix in (".png", ".pdf", ".provenance.json")
    )


def test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs(tmp_path):
    plot = _plot(); certification = tmp_path / "certification.json"
    certification.write_text(plot.DEFAULT_CERT.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    root = tmp_path / "empty-root"; root.mkdir(); prefix = tmp_path / "fig5_changed_certification"
    completed = _run_script(certification, plot.DEFAULT_MANIFEST, root, prefix)
    assert completed.returncode != 0 and "canonical SHA-256 mismatch" in completed.stderr
    assert not any(Path(str(prefix) + suffix).exists() for suffix in (".png", ".pdf", ".provenance.json"))


def test_m12_whitespace_changed_raw_manifest_fails_cli_with_zero_outputs(tmp_path):
    plot = _plot(); manifest = tmp_path / "raw-manifest.json"
    manifest.write_text(plot.DEFAULT_MANIFEST.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    root = tmp_path / "empty-root"; root.mkdir(); prefix = tmp_path / "fig5_changed_manifest"
    completed = _run_script(plot.DEFAULT_CERT, manifest, root, prefix)
    assert completed.returncode != 0 and "canonical SHA-256 mismatch" in completed.stderr
    assert not any(Path(str(prefix) + suffix).exists() for suffix in (".png", ".pdf", ".provenance.json"))


def test_m13_raw_source_commit_must_equal_current_pin_after_manifest_rebind(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    _change_raw(fixture, "rr5-stock", lambda d: d["build_evidence"].__setitem__("source_commit", "wrong-pin"))
    with pytest.raises(plot.FigureDataError, match="source_commit"):
        _load(plot, fixture)


def test_cli_writes_complete_provenance_with_repo_relative_argv(tmp_path, monkeypatch):
    plot, fixture = _plot(), _fixture(tmp_path)
    monkeypatch.setattr(plot, "REPO_ROOT", tmp_path)
    assert _run_main(plot, fixture, _hashes(fixture)) == 0
    outputs = [Path(str(fixture["prefix"]) + suffix) for suffix in (".png", ".pdf", ".provenance.json")]
    assert all(path.is_file() and path.stat().st_size for path in outputs)
    provenance = json.loads(outputs[-1].read_text())
    assert set(provenance) == {
        "schema", "generated_utc", "generator", "outputs", "tracked_inputs", "external_source_locator",
        "external_inputs", "measurement_conditions", "cells", "artist_series", "outer_status", "effects",
        "effect_crosschecks", "correctness", "correctness_performance_note", "gate_note", "caption", "reproduction"}
    assert provenance["schema"] == plot.SCHEMA and provenance["outer_status"] == "reject"
    assert len(provenance["tracked_inputs"]) == 2 and len(provenance["external_inputs"]) == 6
    assert len(provenance["cells"]) == 4 and len(provenance["artist_series"]) == 20
    assert provenance["generator"]["sha256"] == _sha(REPO / provenance["generator"]["path"])
    assert {row["path"]: row["sha256"] for row in provenance["outputs"]} == {
        path.relative_to(tmp_path).as_posix(): _sha(path) for path in outputs[:2]}
    conditions = provenance["measurement_conditions"]
    assert conditions["izanagi_source_commit"] == "izanagi-source" and conditions["ccbench_pin"] == "511c953"
    argv = provenance["reproduction"]["argv"]
    assert argv[3] == str(fixture["root"].resolve())
    assert argv[5:] == ["certification.json", "--raw-manifest", "raw-manifest.json", "fig5_fixture"]
    assert str(REPO) not in " ".join(argv) and provenance["reproduction"]["cwd"] == "repository-root"


def test_tracked_authority_literals_and_run_readme_record_agree():
    plot = _plot()
    cert = REPO / "output/insights/2026-08-24_paper-story-a2-certification/certification.json"
    manifest = REPO / "output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json"
    run_readme = REPO / "output/insights/2026-08-28_t2022-a2-certification-run/README.md"
    assert len(plot.CANONICAL_SHA256) == 2
    assert plot.CANONICAL_SHA256[
        "output/insights/2026-08-24_paper-story-a2-certification/certification.json"
    ] == {"certification": CANONICAL_CERT, "raw_manifest": CANONICAL_MANIFEST}
    assert plot.CANONICAL_SHA256[
        "output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json"
    ] == {
        "certification": "e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671",
        "raw_manifest": "b23ee2ee6ff36d2377da80c2cf4eccc925bae9c3d89aab8a6a8543edfe9ae319",
    }
    assert _sha(cert) == CANONICAL_CERT and _sha(manifest) == CANONICAL_MANIFEST
    assert CANONICAL_CERT in run_readme.read_text(encoding="utf-8")


def _require_complete_external_root(root: Path, relative: list[str]) -> None:
    if not root.exists():
        skip(f"A-2 durable authority root is unavailable: {root}")
    missing = [value for value in relative if not (root / value).is_file()]
    assert not missing, f"A-2 durable authority is partially missing: {missing}"


def test_external_root_partial_absence_is_failure_not_skip(tmp_path):
    root = tmp_path / "present-root"; root.mkdir()
    with pytest.raises(AssertionError, match="partially missing"):
        _require_complete_external_root(root, ["one", "two"])


def test_real_external_inputs_when_available():
    plot = _plot()
    cert = json.loads(plot.DEFAULT_CERT.read_text(encoding="utf-8")); manifest = json.loads(plot.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    paths = [row["path"] for row in plot._external_plan(manifest, cert)]
    _require_complete_external_root(REAL_ROOT, paths)
    data = plot.load_measurements(REAL_ROOT)
    assert [row["median_tps"] for row in data["cells"]] == [2527542, 1355011, 3662448, 1248603]


def test_landed_fig5_repo_closure_and_caption_when_present():
    plot = _plot()
    prefix = REPO / "docs/paper-story/figures/fig5_a2_certification_reject"
    paths = [Path(f"{prefix}{suffix}") for suffix in (".png", ".pdf", ".provenance.json")]
    figures_readme = REPO / "docs/paper-story/figures/README.md"
    readme = figures_readme.read_text(encoding="utf-8")
    if not any(path.exists() for path in paths) and "fig5_a2_certification_reject" not in readme:
        skip("fig5 integration artifacts are parent-owned and not landed yet")
    assert all(path.is_file() for path in paths), "fig5 integration bundle is incomplete"
    provenance = json.loads(paths[-1].read_text(encoding="utf-8"))
    plot.validate_repo_closure(provenance, REPO)
    assert provenance["caption"] in readme


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
