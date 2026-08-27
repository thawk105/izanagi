# -*- coding: utf-8 -*-
"""B-10 provenance v1: repo closure and relocatable external-source gates."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import shutil
import statistics
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MEASUREMENT_ROOT = Path(os.environ.get(
    "IZANAGI_B10_MEASUREMENT_ROOT",
    "/work/1/SFC/tanab/b10-backoff-grid-runs5",
))
REAL_PROVENANCE = Path(
    "docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json")
REAL_OUTPUTS = (
    "docs/paper-story/figures/fig2c_b10_extended_backoff.png",
    "docs/paper-story/figures/fig2c_b10_extended_backoff.pdf",
)
REAL_OUTPUT_SHA256 = {
    "docs/paper-story/figures/fig2c_b10_extended_backoff.png": (
        "2703fab70d412933bad52422dc91861b36db1283c40ef227f471409e12aaffd6"),
    "docs/paper-story/figures/fig2c_b10_extended_backoff.pdf": (
        "70d4b5e295a6a0c7a52313370806146f62efbc4cf4e0732e09ad3199b8195794"),
}
SCHEMA = "izanagi-b10-extended-backoff-figure-provenance/v1"
GROUP = "b10-backoff-grid-20260826T234647Z-783837"
SUBMIT = f"{GROUP}.submit.jsonl"
GRID_29 = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75,
           100, 150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000)
GRID_28 = GRID_29[:-1]
TICKS = (0, 1, 3, 10, 35, 100, 300, 900)
WARNING = (
    "Panel heights and slopes use workload-local y scales and must not be "
    "compared across panels."
)
LATENCY_NOTE = (
    "Latency is retained for provenance but is not drawn or treated as "
    "independent mechanism evidence: in this 48-thread closed-loop benchmark "
    "it is the reciprocal-throughput quantity."
)
CLAIMS = {
    "claim_scope": "descriptive_backoff_shape_only",
    "estimand_matches_paper_headline": False,
    "paper_gain_eligible": False,
    "same_campaign_contrast": True,
    "prereg_frozen_comparison_rule": False,
}
PLOT_BACKOFF_SHA256 = (
    "bdb3c223192835379661e6ba3b288d871e36da9201e89438c41fd10840c0bf5e")
T95_DF4 = 2.7764451051977987
SPECS = (
    ("write-heavy", "951689", "bnode007", 5,
     "b10-backoff-grid-silo-write-heavy-sweep-0a386b45",
     "0a386b454829f7d3487ba016b81fe1360d6bf7c8a54666a9f33830dbfd196c7a"),
    ("balanced", "951690", "bnode009", 50,
     "b10-backoff-grid-silo-balanced-sweep-9ded73c4",
     "9ded73c4e7d0ffc7ef77d0f909194b3aa83823d72414872c137b7b419ddc86c8"),
    ("read-heavy", "951691", "bnode016", 95,
     "b10-backoff-grid-silo-read-heavy-sweep-e2d75497",
     "e2d75497facce68e80ee5468ac14070d51a96af7b0f9a297ac87bed8758e0c6a"),
)


# Independent, literal full hashes for the canonical measurement inputs.
# No fixture hashes are populated from the current files or generator module.
HASHES = {
    SUBMIT: "e97d2c5e08087debbea8d8506a5e2136e877d4331ed0cf12bce4feee64b15375",
    f"{GROUP}-write-heavy/completion.json": "59e92658d304e6d75884890d249caab3eb2aa35724d558d9a72e7ffbd3374bf0",
    f"{GROUP}-write-heavy/reservation.json": "b57ddb10431ce363676d58eae9d884a7607dbf30179c31634de40fbd843a520c",
    f"{GROUP}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/campaign.lock": "6cd61ee3a9f1a155ddcc2163be11f7fb7952cb686064358a3bd453913c95b47b",
    f"{GROUP}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/runs/wal.jsonl": "19945f68e6828b3857befc67fa7b6d8c0c4ec5777dea82d631fa7ea93bcc7830",
    f"{GROUP}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/reports/b10-backoff-grid-write-heavy.dat": "ca49f4e7145152cc0d77658bc31dcd911d4db0227d30ade05f40905a286e12e8",
    f"{GROUP}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/reports/b10-backoff-overthrottle-write-heavy.manifest.json": "e7cfe84c6797cfa847be7aa5d252a6febf0aca41459e3fe355a84258d6201de9",
    f"{GROUP}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/reports/b10-backoff-grid-write-heavy_verdict.json": "36f17ca0d66c2f63957f5e48b6a35c92d671b7da43b31c0ecb47779425e3aa69",
    f"{GROUP}-balanced/completion.json": "d7cf6ae2eb465ea9afda2c916f066ea81c2e97255398dd8f2816246ce8127351",
    f"{GROUP}-balanced/reservation.json": "5109f6212f3bd8319528356e57e8f0cd4294e1baf1870a538940620f7593cb49",
    f"{GROUP}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/campaign.lock": "618ce8fe76318f230efcabef69fa224a0be4558bfe74402b6d6b0a76d4ce3e2c",
    f"{GROUP}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/runs/wal.jsonl": "56c05900946f26817d87a365390bdff35cf84abc6295c1490176490a4e3fe502",
    f"{GROUP}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/reports/b10-backoff-grid-balanced.dat": "dae5cfa93288984b3145a755454f31a8b4f733bad4c72b703e3784a9d7f968d6",
    f"{GROUP}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/reports/b10-backoff-overthrottle-balanced.manifest.json": "4b5ef338a80ad9e69795e5327912e42c4a3256450aac6f7a9508b9483103c57d",
    f"{GROUP}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/reports/b10-backoff-grid-balanced_verdict.json": "29da3878a96b6c0f2a2e3fc72da16e13a36fa170308139ea7c2effba0b2f83c6",
    f"{GROUP}-read-heavy/completion.json": "8d45030aea88d7fee61ca95b45774df37350a6b42109f306f89878a67a3ed172",
    f"{GROUP}-read-heavy/reservation.json": "0f8b4569b825c37dd2863fe294b46f183dc5e63a9540847b708823d2d08da751",
    f"{GROUP}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/campaign.lock": "2cd310205f49b62012aa90170b13aa196f4a9b85f0b9c2005ffb0e4b5fc4b6df",
    f"{GROUP}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/runs/wal.jsonl": "6006bbef7391da2bcba04b0000c7f72ec6c4c4304645040d5347fc7f393d49dc",
    f"{GROUP}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/reports/b10-backoff-grid-read-heavy.dat": "fd286c07c303e56dbbd10a75f0fcf4cecc8cf03d6a8a03b7fc99336eb6f093f9",
    f"{GROUP}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/reports/b10-backoff-overthrottle-read-heavy.manifest.json": "fee1317c0ce5a6e8b384d4d51de70b7f4da62d4913bb08d8545911f485a4b482",
    f"{GROUP}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/reports/b10-backoff-grid-read-heavy_verdict.json": "12fe9936fdf3743ff9be7e9252fff55f9f28aace4aee66b215db8dbf5d55bc81",
}


def _load_module():
    path = REPO / "tools" / "plotting" / "plot_b10_extended_backoff.py"
    spec = importlib.util.spec_from_file_location("b10_provenance_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _paths(workload: str, campaign: str) -> dict[str, str]:
    job_dir = f"{GROUP}-{workload}"
    cdir = f"{job_dir}/campaigns/{campaign}"
    reports = f"{cdir}/reports"
    return {
        "completion": f"{job_dir}/completion.json",
        "reservation": f"{job_dir}/reservation.json",
        "campaign_lock": f"{cdir}/campaign.lock",
        "wal": f"{cdir}/runs/wal.jsonl",
        "dat": f"{reports}/b10-backoff-grid-{workload}.dat",
        "manifest": f"{reports}/b10-backoff-overthrottle-{workload}.manifest.json",
        "verdict": f"{reports}/b10-backoff-grid-{workload}_verdict.json",
    }


def _conditions(rratio: int, host: str) -> dict:
    return {
        "thread_num": 48,
        "ycsb_tuple_num": 1_000_000,
        "extime": 3,
        "clocks_per_us": 2100,
        "ycsb_zipf_skew": 0.9,
        "ycsb_rratio": rratio,
        "ycsb_rmw": False,
        "numactl_args": [],
        "env": "pegasus",
        "CCBENCH_TRACE": 0,
        "ccbench_commit": "511c953",
        "unresolved_fields": [],
        "trace_disabled": True,
        "repository_commit": "78c7a2c1408da05c9c6391451192d81963b84034",
        "ccbench_gitlink_commit": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
        "measurement_host": host,
    }


def _external_provenance() -> dict:
    external_inputs = [{
        "role": "submit", "workload": None, "path": SUBMIT,
        "sha256": HASHES[SUBMIT],
    }]
    workloads = []
    for workload, job_id, host, _rratio, campaign, identity_sha in SPECS:
        paths = _paths(workload, campaign)
        for role, path in paths.items():
            external_inputs.append({
                "role": role, "workload": workload, "path": path,
                "sha256": HASHES[path],
            })
        workloads.append({
            "workload": workload,
            "job_id": job_id,
            "measurement_host": host,
            "job_directory": f"{GROUP}-{workload}",
            "campaign_id": campaign,
            "campaign_identity_sha256": identity_sha,
            "campaign_suffix": identity_sha[:8],
            "repository_commit": "78c7a2c1408da05c9c6391451192d81963b84034",
            "ccbench_commit": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
            **{role: {"path": path, "sha256": HASHES[path]}
               for role, path in paths.items()},
        })
    return {
        "external_source_locator": {
            "root_at_generation": str(MEASUREMENT_ROOT.resolve()),
            "validation_key": "root-relative-path-plus-sha256",
        },
        "external_inputs": external_inputs,
        "receipt_chain": {
            "binding_kind": "scheduler_receipt_chain",
            "submit": {
                "path": SUBMIT,
                "sha256": HASHES[SUBMIT],
                "group_id": GROUP,
                "submission_nonce": "ef2fe956851ac4f1bec500fd7a2dbf0e",
                "job_script_sha256": (
                    "9579690d44c49842eefc00fcf459f2717cda1dccc66857e1b0137ff5abbbeefb"),
            },
            "workloads": workloads,
        },
    }


@contextmanager
def _relocated_root():
    provenance = _external_provenance()
    with tempfile.TemporaryDirectory(prefix="b10-relocated-") as temp:
        root = Path(temp)
        for row in provenance["external_inputs"]:
            source = MEASUREMENT_ROOT / row["path"]
            destination = root / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        yield root, provenance


def _set_negative_fixture_hash(provenance: dict, relative: str, digest: str) -> None:
    """Refresh only deliberately mutated negative fixtures, never positive pins."""
    row = next(item for item in provenance["external_inputs"]
               if item["path"] == relative)
    row["sha256"] = digest
    if relative == SUBMIT:
        provenance["receipt_chain"]["submit"]["sha256"] = digest
        return
    for workload_row in provenance["receipt_chain"]["workloads"]:
        for role in _paths(workload_row["workload"], workload_row["campaign_id"]):
            if workload_row[role]["path"] == relative:
                workload_row[role]["sha256"] = digest
                return
    raise AssertionError(f"negative fixture path is not declared: {relative}")


def _rewrite_json_negative(
    root: Path, provenance: dict, relative: str, mutate,
) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    _set_negative_fixture_hash(provenance, relative, _sha256(path))


def _refresh_completion_for_negative(
    root: Path, provenance: dict, workload: str, campaign: str, role: str,
) -> None:
    paths = _paths(workload, campaign)
    child_relative = paths[role]
    child_digest = _sha256(root / child_relative)
    _set_negative_fixture_hash(provenance, child_relative, child_digest)
    completion_relative = paths["completion"]
    completion_path = root / completion_relative
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    artifact_relative = child_relative.split(f"{GROUP}-{workload}/", 1)[1]
    completion["artifacts"][artifact_relative] = child_digest
    completion_path.write_text(
        json.dumps(completion, sort_keys=True) + "\n", encoding="utf-8")
    _set_negative_fixture_hash(
        provenance, completion_relative, _sha256(completion_path))


def _expect_rejected(call, reason: str) -> None:
    plot = _load_module()
    try:
        call(plot)
    except plot.B10FigureError as exc:
        assert reason in str(exc), str(exc)
    else:
        raise AssertionError("invalid provenance/source was accepted")


def test_canonical_full_hashes_are_independent_constants_and_match_inputs():
    assert len(HASHES) == 22
    assert set(HASHES) == {row["path"] for row in _external_provenance()["external_inputs"]}
    for relative, expected in HASHES.items():
        assert len(expected) == 64
        assert _sha256(MEASUREMENT_ROOT / relative) == expected


def test_frozen_plot_backoff_dependency_bytes_are_independently_pinned():
    assert _sha256(REPO / "tools/plotting/plot_backoff.py") == PLOT_BACKOFF_SHA256


def test_external_layer_is_explicitly_skipped_only_when_root_is_omitted():
    plot = _load_module()
    result = plot.validate_external_sources(_external_provenance(), None)
    assert result == {
        "status": "skipped",
        "layer": "external_measurement_sources",
        "reason": "measurement_root_not_provided",
    }


def test_canonical_external_root_and_receipt_mapping_are_admitted():
    plot = _load_module()
    result = plot.validate_external_sources(_external_provenance(), MEASUREMENT_ROOT)
    assert result == {"status": "validated", "layer": "external_measurement_sources"}


def test_relocated_external_root_is_admitted_by_relative_path_and_hash():
    plot = _load_module()
    with _relocated_root() as (root, provenance):
        result = plot.validate_external_sources(provenance, root)
        assert result["status"] == "validated"


def test_specified_missing_root_is_rejected_not_skipped():
    with tempfile.TemporaryDirectory(prefix="b10-missing-root-parent-") as temp:
        missing = Path(temp) / "absent"
        _expect_rejected(
            lambda plot: plot.validate_external_sources(_external_provenance(), missing),
            "measurement root missing")


def test_specified_root_missing_input_is_rejected():
    with _relocated_root() as (root, provenance):
        (root / provenance["external_inputs"][-1]["path"]).unlink()
        _expect_rejected(
            lambda plot: plot.validate_external_sources(provenance, root),
            "external input missing")


def test_input_byte_drift_is_rejected():
    with _relocated_root() as (root, provenance):
        dat = next(row for row in provenance["external_inputs"]
                   if row["role"] == "dat" and row["workload"] == "write-heavy")
        path = root / dat["path"]
        path.write_bytes(path.read_bytes() + b"# byte drift\n")
        _expect_rejected(
            lambda plot: plot.validate_external_sources(provenance, root),
            "external input SHA256 mismatch")


def test_relocated_completion_job_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        relative = _paths(workload, campaign)["completion"]
        _rewrite_json_negative(
            root, provenance, relative,
            lambda payload: payload.__setitem__("pbs_jobid", "0:951999.nqsv"))
        assert next(row for row in provenance["external_inputs"]
                    if row["path"] == relative)["sha256"] == _sha256(root / relative)
        _expect_rejected(
            lambda plot: plot._receipt_chain(root),
            "completion job/workload/campaign mismatch")


def test_relocated_manifest_workload_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        relative = _paths(workload, campaign)["manifest"]
        _rewrite_json_negative(
            root, provenance, relative,
            lambda payload: payload.__setitem__("workload", "balanced"))
        _refresh_completion_for_negative(
            root, provenance, workload, campaign, "manifest")
        _expect_rejected(
            lambda plot: plot._receipt_chain(root),
            "manifest campaign/workload mismatch")


def test_relocated_completion_campaign_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        relative = _paths(workload, campaign)["completion"]
        _rewrite_json_negative(
            root, provenance, relative,
            lambda payload: payload.__setitem__("campaign_id", campaign + "-drift"))
        _expect_rejected(
            lambda plot: plot._receipt_chain(root),
            "completion job/workload/campaign mismatch")


def test_relocated_lock_suffix_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        relative = _paths(workload, campaign)["campaign_lock"]

        def mutate(payload):
            identity = json.loads(payload["identity_preimage"])
            identity["trial"] = "b10-backoff-grid-mutated-negative"
            payload["identity_preimage"] = json.dumps(
                identity, sort_keys=True, separators=(",", ":"))

        _rewrite_json_negative(root, provenance, relative, mutate)
        _refresh_completion_for_negative(
            root, provenance, workload, campaign, "campaign_lock")
        _expect_rejected(
            lambda plot: plot._receipt_chain(root),
            "campaign suffix is not identity_preimage SHA256 prefix")


def test_relocated_reservation_nonce_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        relative = _paths(workload, campaign)["reservation"]
        _rewrite_json_negative(
            root, provenance, relative,
            lambda payload: payload["binding"].__setitem__("nonce", "wrong-nonce"))
        _expect_rejected(
            lambda plot: plot._receipt_chain(root),
            "reservation mapping mismatch")


def test_relocated_reservation_host_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        relative = _paths(workload, campaign)["reservation"]
        _rewrite_json_negative(
            root, provenance, relative,
            lambda payload: payload["binding"].__setitem__("host", "bnode999"))
        _expect_rejected(
            lambda plot: plot._receipt_chain(root),
            "reservation mapping mismatch")


def test_relocated_dat_metric_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        paths = _paths(workload, campaign)
        dat_path = root / paths["dat"]
        lines = dat_path.read_text(encoding="utf-8").splitlines()
        row_index = next(index for index, line in enumerate(lines)
                         if line and not line.startswith("#"))
        fields = lines[row_index].split()
        fields[2] = str(float(fields[2]) + 0.001)
        lines[row_index] = " ".join(fields)
        dat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _refresh_completion_for_negative(
            root, provenance, workload, campaign, "dat")
        assert next(row for row in provenance["external_inputs"]
                    if row["path"] == paths["dat"])["sha256"] == _sha256(dat_path)

        def validate(plot):
            spec = plot.WORKLOAD_SPECS[0]
            dat_rows = plot._parse_dat(dat_path, spec)
            wal_points = plot._wal_points(root / paths["wal"])
            plot._validate_dat_wal_semantics(dat_rows, wal_points, spec)

        _expect_rejected(validate, "dat/WAL metric mismatch")


def test_relocated_wal_metric_edge_is_rejected_after_hash_refresh():
    with _relocated_root() as (root, provenance):
        workload, _job, _host, _rratio, campaign, _identity = SPECS[0]
        paths = _paths(workload, campaign)
        wal_path = root / paths["wal"]
        records = [json.loads(line) for line in wal_path.read_text(
            encoding="utf-8").splitlines() if line]
        record = next(row for row in records if row.get("stage") == "bench_done")
        indicators = record["payload"]["leading_indicators"]
        indicators["abort_rate"] = float(indicators["abort_rate"]) + 0.001
        wal_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in records) + "\n",
            encoding="utf-8")
        _refresh_completion_for_negative(
            root, provenance, workload, campaign, "wal")

        def validate(plot):
            spec = plot.WORKLOAD_SPECS[0]
            dat_rows = plot._parse_dat(root / paths["dat"], spec)
            wal_points = plot._wal_points(wal_path)
            plot._validate_dat_wal_semantics(dat_rows, wal_points, spec)

        _expect_rejected(validate, "dat/WAL metric mismatch")


def test_provenance_receipt_mapping_drift_is_rejected():
    provenance = _external_provenance()
    provenance["receipt_chain"]["workloads"][0]["job_id"] = "951690"
    _expect_rejected(
        lambda plot: plot.validate_external_sources(provenance, MEASUREMENT_ROOT),
        "provenance receipt mapping mismatch")


def test_rootless_validation_still_requires_external_proof_structure():
    provenance = _external_provenance()
    provenance["external_inputs"].pop()
    _expect_rejected(
        lambda plot: plot.validate_external_sources(provenance, None),
        "external_inputs canonical 22-row mapping mismatch")


def test_lexical_external_path_escape_is_rejected():
    provenance = _external_provenance()
    provenance["external_inputs"][0]["path"] = "../outside-submit.jsonl"
    _expect_rejected(
        lambda plot: plot.validate_external_sources(provenance, MEASUREMENT_ROOT),
        "lexical escape")


def test_symlink_external_path_escape_is_rejected():
    with _relocated_root() as (root, provenance):
        dat = next(row for row in provenance["external_inputs"]
                   if row["role"] == "dat" and row["workload"] == "balanced")
        inside = root / dat["path"]
        with tempfile.TemporaryDirectory(prefix="b10-outside-") as outside_temp:
            outside = Path(outside_temp) / "balanced.dat"
            outside.write_bytes(inside.read_bytes())
            inside.unlink()
            inside.symlink_to(outside)
            _expect_rejected(
                lambda plot: plot.validate_external_sources(provenance, root),
                "symlink escape")


def _semantic_provenance() -> dict:
    data = []
    artists = []
    for index, (workload, job_id, host, rratio, campaign, _identity) in enumerate(SPECS):
        raw = []
        for value in GRID_29:
            mean = float((index + 1) * 1_000_000 + value)
            repetitions = [mean - 2, mean - 1, mean, mean + 1, mean + 2]
            half = T95_DF4 * statistics.stdev(repetitions) / math.sqrt(5)
            abort = float(0.1 + index * 0.1 + value / 10_000)
            row = {
                "backoff_us": value,
                "throughput_dat_tps": mean,
                "throughput_repetitions_tps": repetitions,
                "throughput_wal_mean_tps": mean,
                "throughput_ci95_half_tps": half,
                "abort_rate": abort,
                "abort_ci95_half": None,
                "latency_ns": 48e9 / mean,
                "cv": 0.01,
                "wal_metrics": {
                    "abort_rate": abort,
                    "latency_ns": 48e9 / mean,
                    "cv": 0.01,
                },
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
        included = [dict(row) for row in raw if row["included"]]
        excluded = [dict(row) for row in raw if not row["included"]]
        data.append({
            "workload": workload, "campaign_id": campaign, "job_id": job_id,
            "raw_points": raw, "included_points": included,
            "excluded_points": excluded, "conditions": _conditions(rratio, host),
            "claim_boundary": dict(CLAIMS),
            "campaign_read_purpose": "HISTORICAL_RAW",
            "campaign_verifier_epoch": {},
        })
        xs = list(GRID_28)
        means = [row["throughput_wal_mean_tps"] / 1e6 for row in included]
        cis = [row["throughput_ci95_half_tps"] / 1e6 for row in included]
        aborts = [row["abort_rate"] for row in included]
        artists.extend([
            {"workload": workload, "metric": "throughput_mean", "kind": "line",
             "label": f"{workload} throughput", "x": xs, "y": means,
             "unit": "M tps"},
            {"workload": workload, "metric": "throughput_ci95", "kind": "interval",
             "label": f"{workload} throughput 95% CI", "x": xs, "y": cis,
             "lower": [y - h for y, h in zip(means, cis)],
             "upper": [y + h for y, h in zip(means, cis)], "unit": "M tps"},
            {"workload": workload, "metric": "abort_rate", "kind": "line",
             "label": f"{workload} abort rate", "x": xs, "y": aborts,
             "unit": "fraction", "ci_artist": False},
        ])
    provenance = {
        **_external_provenance(),
        "schema": SCHEMA,
        "claim_boundary": dict(CLAIMS),
        "text_contract": {
            "figure_body": WARNING,
            "caption": (
                "Fixture; M tps = million transactions per second; "
                "read-modify-write (RMW) disabled; canonical F718/D1106 ruling "
                "assertion rather than a value derived from measurement artifacts. "
                + WARNING),
            "provenance": WARNING, "comparison_warning": WARNING,
            "latency_note": LATENCY_NOTE, "static_zero_is_no_backoff": False,
            "add_analysis_drawn": False,
            "legacy_three_percent_floor_drawn": False,
            "noise_band_or_onset_drawn": False,
            "no_backoff_or_adaptive_baseline_drawn": False,
        },
        "axis_contract": {
            "layout": {"rows": 2, "columns": 3,
                       "workload_order": [row[0] for row in SPECS],
                       "top_metric": "throughput_mean", "bottom_metric": "abort_rate"},
            "x": {"scale": "symlog", "base": 10, "linthresh": 1, "linscale": 1,
                  "fixed_ticks": list(TICKS), "includes_zero": True,
                  "includes_900": True},
            "y": {"shared": False, "scope": "workload-local", "autoscale": True,
                  "throughput_unit": "M tps", "abort_unit": "fraction"},
            "artist_series_count": 9, "abort_ci_artist": False,
            "bbox_overlap_policy": "fail-before-save-including-tick-labels",
        },
        "data": data,
        "artist_series": artists,
    }
    return provenance


@contextmanager
def _repo_fixture():
    with tempfile.TemporaryDirectory(prefix="b10-repo-closure-") as temp:
        root = Path(temp)
        generator = root / "tools/plotting/plot_b10_extended_backoff.py"
        dependency = root / "tools/plotting/plot_backoff.py"
        png = root / REAL_OUTPUTS[0]
        pdf = root / REAL_OUTPUTS[1]
        for path in (generator, dependency, png, pdf):
            path.parent.mkdir(parents=True, exist_ok=True)
        generator.write_bytes(b"fixture b10 generator\n")
        dependency.write_bytes(b"fixture frozen dependency\n")
        png.write_bytes(b"fixture png\n")
        pdf.write_bytes(b"fixture pdf\n")
        provenance = _semantic_provenance()
        provenance.update({
            "generator": {
                "path": "tools/plotting/plot_b10_extended_backoff.py",
                "sha256": "a1c95ed8678623acb51e577e4b363308a75860d7d7c6b3fb8a7b439fa5764e4a",
            },
            "dependencies": [{
                "role": "admitted-wal-conditions-t95-ci-style",
                "path": "tools/plotting/plot_backoff.py",
                "sha256": "bf31bcf65f3ad532abf1aa02f86149ffe91bc115d07c5a6529e536e1ce2a7ca2",
            }],
            "outputs": [
                {"path": REAL_OUTPUTS[0],
                 "sha256": "7539faf634686590b837d8156cdc348822a3f9e4c0f328507336ab4c9331e928"},
                {"path": REAL_OUTPUTS[1],
                 "sha256": "e06ec2ffa2a76bc324267d2a941a8e9701f3053e9c64f58135083ef4c62d2a39"},
            ],
        })
        yield root, provenance


def test_repo_closure_accepts_independently_pinned_fixture_bytes():
    plot = _load_module()
    with _repo_fixture() as (root, provenance):
        plot.validate_repo_closure(provenance, root)


def test_generator_byte_drift_is_rejected():
    with _repo_fixture() as (root, provenance):
        (root / provenance["generator"]["path"]).write_bytes(b"changed")
        _expect_rejected(
            lambda plot: plot.validate_repo_closure(provenance, root),
            "generator SHA256 mismatch")


def test_dependency_byte_drift_is_rejected():
    with _repo_fixture() as (root, provenance):
        (root / provenance["dependencies"][0]["path"]).write_bytes(b"changed")
        _expect_rejected(
            lambda plot: plot.validate_repo_closure(provenance, root),
            "dependency SHA256 mismatch")


def test_output_byte_drift_is_rejected():
    with _repo_fixture() as (root, provenance):
        (root / provenance["outputs"][0]["path"]).write_bytes(b"changed")
        _expect_rejected(
            lambda plot: plot.validate_repo_closure(provenance, root),
            "output SHA256 mismatch")


def test_1000_inclusion_is_rejected_even_when_values_are_preserved():
    provenance = _semantic_provenance()
    campaign = provenance["data"][0]
    campaign["raw_points"][-1]["included"] = True
    campaign["included_points"].append(copy.deepcopy(campaign["raw_points"][-1]))
    campaign["excluded_points"] = []
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "included provenance grid mismatch")


def test_static_zero_drop_is_rejected():
    provenance = _semantic_provenance()
    provenance["data"][0]["included_points"].pop(0)
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "included provenance grid mismatch")


def test_d1107_five_field_claim_boundary_drift_is_rejected():
    provenance = _semantic_provenance()
    assert set(provenance["claim_boundary"]) == set(CLAIMS)
    provenance["claim_boundary"]["paper_gain_eligible"] = True
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "D1107 claim boundary mismatch")


def test_artist_abort_percent_forge_is_rejected():
    provenance = _semantic_provenance()
    abort = next(row for row in provenance["artist_series"]
                 if row["metric"] == "abort_rate")
    abort["y"] = [value * 100 for value in abort["y"]]
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "artist series differ")


def test_stored_measurement_statistics_are_independently_recomputed():
    def mutate_point(provenance, mutate):
        raw = provenance["data"][0]["raw_points"][0]
        included = provenance["data"][0]["included_points"][0]
        mutate(raw)
        mutate(included)

    cases = [
        (lambda point: point.__setitem__(
            "throughput_wal_mean_tps", point["throughput_wal_mean_tps"] + 1),
         "stored WAL mean does not match repetitions"),
        (lambda point: point.__setitem__(
            "throughput_ci95_half_tps", point["throughput_ci95_half_tps"] + 1),
         "stored t95 CI does not match repetitions"),
        (lambda point: point.__setitem__(
            "throughput_dat_tps", point["throughput_dat_tps"] + 1),
         "stored dat throughput is not the repetitions median"),
        (lambda point: point.__setitem__(
            "abort_rate", point["abort_rate"] + 0.01),
         "stored dat/WAL abort-latency-CV mapping mismatch"),
        (lambda point: point.__setitem__("cv", point["cv"] + 0.01),
         "stored dat/WAL abort-latency-CV mapping mismatch"),
    ]
    for mutate, reason in cases:
        provenance = _semantic_provenance()
        mutate_point(provenance, mutate)
        _expect_rejected(
            lambda plot, value=provenance: plot.validate_provenance_semantics(value),
            reason)

    provenance = _semantic_provenance()
    raw = provenance["data"][0]["raw_points"][0]
    included = provenance["data"][0]["included_points"][0]
    for point in (raw, included):
        point["latency_ns"] += 1000
    raw["wal_metrics"]["latency_ns"] = raw["latency_ns"]
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "stored latency reciprocal contract mismatch")


def test_conditions_and_f718_ruling_authority_are_semantic_requirements():
    provenance = _semantic_provenance()
    provenance["data"][0]["conditions"]["ycsb_rratio"] = 50
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "measurement conditions exact-field mismatch")

    provenance = _semantic_provenance()
    raw = provenance["data"][0]["raw_points"][-1]
    excluded = provenance["data"][0]["excluded_points"][0]
    raw["encoding_authority"]["authority_kind"] = "measurement"
    excluded["encoding_authority"]["authority_kind"] = "measurement"
    _expect_rejected(
        lambda plot: plot.validate_provenance_semantics(provenance),
        "F718/D1106 canonical ruling authority mismatch")


def test_real_fig2c_repo_closure_is_complete():
    """Parent lands the real PNG/PDF/provenance; absence is the planned red."""
    provenance_path = REPO / REAL_PROVENANCE
    assert provenance_path.is_file(), (
        f"parent must generate the real fig2c artifact: {REAL_PROVENANCE}")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert [row.get("path") for row in provenance.get("outputs", [])] == list(
        REAL_OUTPUTS)
    assert all((REPO / relative).is_file() for relative in REAL_OUTPUTS)
    provenance_output_hashes = {
        row["path"]: row.get("sha256") for row in provenance["outputs"]
    }
    assert provenance_output_hashes == REAL_OUTPUT_SHA256
    assert {
        relative: _sha256(REPO / relative) for relative in REAL_OUTPUTS
    } == REAL_OUTPUT_SHA256
    plot = _load_module()
    plot.validate_repo_closure(provenance, REPO)
    assert plot.validate_external_sources(provenance, None)["status"] == "skipped"


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
