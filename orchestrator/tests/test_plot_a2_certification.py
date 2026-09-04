# -*- coding: utf-8 -*-
"""A-2 certification figure: authority, projection, layout, and mutation pins."""
from __future__ import annotations

import collections
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
    return {"root": root, "cert": cert, "manifest": manifest_path, "prefix": tmp_path / "figure"}


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
    assert plot.build_provenance(data, [], ["plot"])["outer_status"] == "sentinel-status"


def test_m8_artist_baseline_is_stock_median_with_stock_genome(tmp_path):
    plot, data = _plot(), None
    fixture = _fixture(tmp_path); data = _load(plot, fixture)
    baselines = [row for row in plot._artist_series(data) if row["kind"] == "baseline"]
    assert [(row["value_tps"], row["genome"]) for row in baselines] == [
        (2527542, GENOMES["rr5-stock"]), (3662448, GENOMES["rr50-stock"])]


def test_m9_caption_distinguishes_correctness_from_performance(tmp_path):
    plot, fixture = _plot(), _fixture(tmp_path)
    caption = plot._caption(_load(plot, fixture))
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


def test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs(tmp_path):
    plot = _plot(); certification = tmp_path / "certification.json"
    certification.write_text(plot.DEFAULT_CERT.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    root = tmp_path / "empty-root"; root.mkdir(); prefix = tmp_path / "figure"
    completed = _run_script(certification, plot.DEFAULT_MANIFEST, root, prefix)
    assert completed.returncode != 0 and "canonical SHA-256 mismatch" in completed.stderr
    assert not any(Path(str(prefix) + suffix).exists() for suffix in (".png", ".pdf", ".provenance.json"))


def test_m12_whitespace_changed_raw_manifest_fails_cli_with_zero_outputs(tmp_path):
    plot = _plot(); manifest = tmp_path / "raw-manifest.json"
    manifest.write_text(plot.DEFAULT_MANIFEST.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    root = tmp_path / "empty-root"; root.mkdir(); prefix = tmp_path / "figure"
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
    assert argv[5:] == ["certification.json", "--raw-manifest", "raw-manifest.json", "figure"]
    assert str(REPO) not in " ".join(argv) and provenance["reproduction"]["cwd"] == "repository-root"


def test_tracked_authority_literals_and_run_readme_record_agree():
    plot = _plot()
    cert = REPO / "output/insights/2026-08-24_paper-story-a2-certification/certification.json"
    manifest = REPO / "output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json"
    run_readme = REPO / "output/insights/2026-08-28_t2022-a2-certification-run/README.md"
    assert plot.CANONICAL_SHA256 == {"certification": CANONICAL_CERT, "raw_manifest": CANONICAL_MANIFEST}
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
