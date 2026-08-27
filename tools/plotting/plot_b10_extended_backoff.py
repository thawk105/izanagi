#!/usr/bin/env python3
"""Generate the B-10 extended static-backoff paper figure.

Usage:
    python tools/plotting/plot_b10_extended_backoff.py OUT_PREFIX MEASUREMENT_ROOT

The measurement root is relocatable.  Every external input is addressed by a
root-relative path and pinned by SHA-256; scheduler receipts and campaign
identity are checked before the existing plot_backoff admission/CI layer is
allowed to consume the campaigns.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import re
import statistics
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.plotting import plot_backoff as backoff  # noqa: E402


SCHEMA = "izanagi-b10-extended-backoff-figure-provenance/v1"
GROUP_ID = "b10-backoff-grid-20260826T234647Z-783837"
SUBMIT_PATH = f"{GROUP_ID}.submit.jsonl"
DAT_COLUMNS = "backoff_us throughput_tps abort_rate latency_ns cv"
RAW_GRID = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75,
            100, 150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000)
INCLUDED_GRID = RAW_GRID[:-1]
SPARSE_TICKS = (0, 1, 3, 10, 35, 100, 300, 900)
T95_DF4 = 2.7764451051977987
REPOSITORY_COMMIT = "78c7a2c1408da05c9c6391451192d81963b84034"
CCBENCH_COMMIT = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
SUBMISSION_NONCE = "ef2fe956851ac4f1bec500fd7a2dbf0e"
JOB_SCRIPT_SHA256 = (
    "9579690d44c49842eefc00fcf459f2717cda1dccc66857e1b0137ff5abbbeefb")
REAL_OUTPUT_PATHS = (
    "docs/paper-story/figures/fig2c_b10_extended_backoff.png",
    "docs/paper-story/figures/fig2c_b10_extended_backoff.pdf",
)
COMPARISON_WARNING = (
    "Panel heights and slopes use workload-local y scales and must not be "
    "compared across panels."
)
LATENCY_NOTE = (
    "Latency is retained for provenance but is not drawn or treated as "
    "independent mechanism evidence: in this 48-thread closed-loop benchmark "
    "it is the reciprocal-throughput quantity."
)
CLAIM_BOUNDARY = {
    "claim_scope": "descriptive_backoff_shape_only",
    "estimand_matches_paper_headline": False,
    "paper_gain_eligible": False,
    "same_campaign_contrast": True,
    "prereg_frozen_comparison_rule": False,
}
F718_AUTHORITY = {
    "authority_kind": "canonical_ruling",
    "authority_ids": ["F718", "D1106"],
    "assertion_kind": "backoff_encoding_interpretation",
    "derivation_kind": "ruling_assertion_not_measurement_derived",
}


WORKLOAD_SPECS = (
    {
        "workload": "write-heavy",
        "job_id": "951689",
        "host": "bnode007",
        "rratio": 5,
        "campaign_id": "b10-backoff-grid-silo-write-heavy-sweep-0a386b45",
        "identity_sha256": (
            "0a386b454829f7d3487ba016b81fe1360d6bf7c8a54666a9f33830dbfd196c7a"),
    },
    {
        "workload": "balanced",
        "job_id": "951690",
        "host": "bnode009",
        "rratio": 50,
        "campaign_id": "b10-backoff-grid-silo-balanced-sweep-9ded73c4",
        "identity_sha256": (
            "9ded73c4e7d0ffc7ef77d0f909194b3aa83823d72414872c137b7b419ddc86c8"),
    },
    {
        "workload": "read-heavy",
        "job_id": "951691",
        "host": "bnode016",
        "rratio": 95,
        "campaign_id": "b10-backoff-grid-silo-read-heavy-sweep-e2d75497",
        "identity_sha256": (
            "e2d75497facce68e80ee5468ac14070d51a96af7b0f9a297ac87bed8758e0c6a"),
    },
)


def _job_dir(spec: Mapping) -> str:
    return f"{GROUP_ID}-{spec['workload']}"


def _campaign_dir(spec: Mapping) -> str:
    return f"{_job_dir(spec)}/campaigns/{spec['campaign_id']}"


def _paths(spec: Mapping) -> dict[str, str]:
    workload = str(spec["workload"])
    campaign = _campaign_dir(spec)
    reports = f"{campaign}/reports"
    return {
        "completion": f"{_job_dir(spec)}/completion.json",
        "reservation": f"{_job_dir(spec)}/reservation.json",
        "campaign_lock": f"{campaign}/campaign.lock",
        "wal": f"{campaign}/runs/wal.jsonl",
        "dat": f"{reports}/b10-backoff-grid-{workload}.dat",
        "manifest": f"{reports}/b10-backoff-overthrottle-{workload}.manifest.json",
        "verdict": f"{reports}/b10-backoff-grid-{workload}_verdict.json",
    }


# Canonical source bytes are deliberately pinned here.  The provenance tests
# carry an independent copy of these full digests; they never learn them by
# hashing a fixture at run time.
CANONICAL_SHA256 = {
    SUBMIT_PATH: "e97d2c5e08087debbea8d8506a5e2136e877d4331ed0cf12bce4feee64b15375",
    f"{GROUP_ID}-write-heavy/completion.json": "59e92658d304e6d75884890d249caab3eb2aa35724d558d9a72e7ffbd3374bf0",
    f"{GROUP_ID}-write-heavy/reservation.json": "b57ddb10431ce363676d58eae9d884a7607dbf30179c31634de40fbd843a520c",
    f"{GROUP_ID}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/campaign.lock": "6cd61ee3a9f1a155ddcc2163be11f7fb7952cb686064358a3bd453913c95b47b",
    f"{GROUP_ID}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/runs/wal.jsonl": "19945f68e6828b3857befc67fa7b6d8c0c4ec5777dea82d631fa7ea93bcc7830",
    f"{GROUP_ID}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/reports/b10-backoff-grid-write-heavy.dat": "ca49f4e7145152cc0d77658bc31dcd911d4db0227d30ade05f40905a286e12e8",
    f"{GROUP_ID}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/reports/b10-backoff-overthrottle-write-heavy.manifest.json": "e7cfe84c6797cfa847be7aa5d252a6febf0aca41459e3fe355a84258d6201de9",
    f"{GROUP_ID}-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/reports/b10-backoff-grid-write-heavy_verdict.json": "36f17ca0d66c2f63957f5e48b6a35c92d671b7da43b31c0ecb47779425e3aa69",
    f"{GROUP_ID}-balanced/completion.json": "d7cf6ae2eb465ea9afda2c916f066ea81c2e97255398dd8f2816246ce8127351",
    f"{GROUP_ID}-balanced/reservation.json": "5109f6212f3bd8319528356e57e8f0cd4294e1baf1870a538940620f7593cb49",
    f"{GROUP_ID}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/campaign.lock": "618ce8fe76318f230efcabef69fa224a0be4558bfe74402b6d6b0a76d4ce3e2c",
    f"{GROUP_ID}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/runs/wal.jsonl": "56c05900946f26817d87a365390bdff35cf84abc6295c1490176490a4e3fe502",
    f"{GROUP_ID}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/reports/b10-backoff-grid-balanced.dat": "dae5cfa93288984b3145a755454f31a8b4f733bad4c72b703e3784a9d7f968d6",
    f"{GROUP_ID}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/reports/b10-backoff-overthrottle-balanced.manifest.json": "4b5ef338a80ad9e69795e5327912e42c4a3256450aac6f7a9508b9483103c57d",
    f"{GROUP_ID}-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/reports/b10-backoff-grid-balanced_verdict.json": "29da3878a96b6c0f2a2e3fc72da16e13a36fa170308139ea7c2effba0b2f83c6",
    f"{GROUP_ID}-read-heavy/completion.json": "8d45030aea88d7fee61ca95b45774df37350a6b42109f306f89878a67a3ed172",
    f"{GROUP_ID}-read-heavy/reservation.json": "0f8b4569b825c37dd2863fe294b46f183dc5e63a9540847b708823d2d08da751",
    f"{GROUP_ID}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/campaign.lock": "2cd310205f49b62012aa90170b13aa196f4a9b85f0b9c2005ffb0e4b5fc4b6df",
    f"{GROUP_ID}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/runs/wal.jsonl": "6006bbef7391da2bcba04b0000c7f72ec6c4c4304645040d5347fc7f393d49dc",
    f"{GROUP_ID}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/reports/b10-backoff-grid-read-heavy.dat": "fd286c07c303e56dbbd10a75f0fcf4cecc8cf03d6a8a03b7fc99336eb6f093f9",
    f"{GROUP_ID}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/reports/b10-backoff-overthrottle-read-heavy.manifest.json": "fee1317c0ce5a6e8b384d4d51de70b7f4da62d4913bb08d8545911f485a4b482",
    f"{GROUP_ID}-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/reports/b10-backoff-grid-read-heavy_verdict.json": "12fe9936fdf3743ff9be7e9252fff55f9f28aace4aee66b215db8dbf5d55bc81",
}


class B10FigureError(ValueError):
    """The fixed B-10 source or figure contract was violated."""


def _reject(message: str) -> None:
    raise B10FigureError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _reject(f"cannot read JSON {path}: {exc}")
    if not isinstance(value, dict):
        _reject(f"JSON root must be an object: {path}")
    return value


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_external(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        _reject(f"external path must be a non-empty string: {value!r}")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        _reject(f"external path lexical escape: {value}")
    root_resolved = root.resolve()
    candidate = root_resolved / relative
    if not candidate.exists():
        _reject(f"external input missing: {value}")
    resolved = candidate.resolve()
    if not _inside(root_resolved, resolved):
        _reject(f"external path symlink escape: {value}")
    if not resolved.is_file():
        _reject(f"external input is not a file: {value}")
    return resolved


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    if not _inside(REPO_ROOT.resolve(), resolved):
        _reject(f"repo artifact path leaves repository: {path}")
    return resolved.relative_to(REPO_ROOT.resolve()).as_posix()


def _canonical_external_rows() -> list[dict]:
    rows = [{
        "role": "submit",
        "workload": None,
        "path": SUBMIT_PATH,
        "sha256": CANONICAL_SHA256[SUBMIT_PATH],
    }]
    for spec in WORKLOAD_SPECS:
        for role, relative in _paths(spec).items():
            rows.append({
                "role": role,
                "workload": spec["workload"],
                "path": relative,
                "sha256": CANONICAL_SHA256[relative],
            })
    return rows


def _external_rows(root: Path) -> list[dict]:
    rows = _canonical_external_rows()
    for row in rows:
        actual = _sha256(_resolve_external(root, row["path"]))
        if actual != row["sha256"]:
            _reject(f"external input SHA256 mismatch: {row['path']}")
    return rows


def _canonical_receipt_chain() -> dict:
    workloads = []
    for spec in WORKLOAD_SPECS:
        paths = _paths(spec)
        workloads.append({
            "workload": spec["workload"],
            "job_id": spec["job_id"],
            "measurement_host": spec["host"],
            "job_directory": _job_dir(spec),
            "campaign_id": spec["campaign_id"],
            "campaign_identity_sha256": spec["identity_sha256"],
            "campaign_suffix": str(spec["identity_sha256"])[:8],
            "repository_commit": REPOSITORY_COMMIT,
            "ccbench_commit": CCBENCH_COMMIT,
            **{role: {
                "path": path,
                "sha256": CANONICAL_SHA256[path],
            } for role, path in paths.items()},
        })
    return {
        "binding_kind": "scheduler_receipt_chain",
        "submit": {
            "path": SUBMIT_PATH,
            "sha256": CANONICAL_SHA256[SUBMIT_PATH],
            "group_id": GROUP_ID,
            "submission_nonce": SUBMISSION_NONCE,
            "job_script_sha256": JOB_SCRIPT_SHA256,
        },
        "workloads": workloads,
    }


def _validate_external_provenance_structure(provenance: Mapping) -> None:
    locator = provenance.get("external_source_locator")
    if (not isinstance(locator, Mapping)
            or set(locator) != {"root_at_generation", "validation_key"}
            or locator.get("validation_key") != "root-relative-path-plus-sha256"
            or not isinstance(locator.get("root_at_generation"), str)
            or not locator["root_at_generation"]
            or not Path(locator["root_at_generation"]).is_absolute()):
        _reject("external source locator mismatch")
    rows = provenance.get("external_inputs")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            value = row.get("path")
            if isinstance(value, str):
                relative = Path(value)
                if relative.is_absolute() or ".." in relative.parts:
                    _reject(f"external path lexical escape: {value}")
    if rows != _canonical_external_rows():
        _reject("external_inputs canonical 22-row mapping mismatch")
    if provenance.get("receipt_chain") != _canonical_receipt_chain():
        _reject("provenance receipt mapping mismatch")


def _job_number(value: object) -> str:
    match = re.search(r"(?:0:|Request\s+)?(\d+)\.nqsv", str(value))
    if not match:
        _reject(f"cannot normalize scheduler job id: {value!r}")
    return match.group(1)


def _campaign_identity(lock: Mapping, campaign_id: str) -> tuple[str, dict]:
    preimage = lock.get("identity_preimage")
    if not isinstance(preimage, str):
        _reject("campaign.lock identity_preimage is missing")
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
    suffix = digest[:8]
    if campaign_id.rsplit("-", 1)[-1] != suffix:
        _reject(f"campaign suffix is not identity_preimage SHA256 prefix: {campaign_id}")
    try:
        identity = json.loads(preimage)
    except json.JSONDecodeError as exc:
        _reject(f"campaign identity_preimage is not JSON: {exc}")
    if not isinstance(identity, dict):
        _reject("campaign identity_preimage JSON must be an object")
    return digest, identity


def _read_submit(path: Path) -> tuple[dict, dict[str, dict]]:
    try:
        events = [json.loads(line) for line in path.read_text(
            encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _reject(f"cannot parse submit receipt: {exc}")
    manifests = [row for row in events if row.get("event") == "manifest"]
    submitted = [row for row in events if row.get("event") == "submitted"]
    if len(manifests) != 1 or len(submitted) != 3:
        _reject("submit receipt must contain one manifest and three submissions")
    manifest = manifests[0]
    if (manifest.get("group_id") != GROUP_ID
            or manifest.get("workloads") != [s["workload"] for s in WORKLOAD_SPECS]):
        _reject("submit manifest group/workload order mismatch")
    by_workload = {row.get("workload"): row for row in submitted}
    if tuple(by_workload) != tuple(s["workload"] for s in WORKLOAD_SPECS):
        _reject("submit workload mapping mismatch")
    return manifest, by_workload


def _receipt_chain(root: Path) -> dict:
    submit_path = _resolve_external(root, SUBMIT_PATH)
    manifest_event, submitted = _read_submit(submit_path)
    nonce = manifest_event.get("submission_nonce")
    script_hash = manifest_event.get("job_script_sha256")
    if nonce != SUBMISSION_NONCE or script_hash != JOB_SCRIPT_SHA256:
        _reject("submit nonce/script identity mismatch")
    workloads = []
    for spec in WORKLOAD_SPECS:
        workload = str(spec["workload"])
        expected_job = str(spec["job_id"])
        campaign_id = str(spec["campaign_id"])
        paths = _paths(spec)
        submission = submitted[workload]
        if _job_number(submission.get("job_id")) != expected_job:
            _reject(f"submit job/workload mismatch: {workload}")
        if Path(str(submission.get("output_root"))).name != _job_dir(spec):
            _reject(f"submit output_root/workload mismatch: {workload}")

        completion = _json(_resolve_external(root, paths["completion"]))
        reservation = _json(_resolve_external(root, paths["reservation"]))
        lock = _json(_resolve_external(root, paths["campaign_lock"]))
        manifest = _json(_resolve_external(root, paths["manifest"]))
        verdict = _json(_resolve_external(root, paths["verdict"]))
        if (completion.get("status") != "complete"
                or completion.get("workload") != workload
                or completion.get("campaign_id") != campaign_id
                or _job_number(completion.get("pbs_jobid")) != expected_job):
            _reject(f"completion job/workload/campaign mismatch: {workload}")
        binding = reservation.get("binding", {})
        if (not isinstance(binding, Mapping)
                or _job_number(binding.get("job_id")) != expected_job
                or binding.get("nonce") != nonce
                or binding.get("script_sha256") != script_hash
                or binding.get("host") != spec["host"]):
            _reject(f"reservation mapping mismatch: {workload}")

        identity_sha, identity = _campaign_identity(lock, campaign_id)
        if identity_sha != spec["identity_sha256"]:
            _reject(f"campaign lock identity mismatch: {workload}")
        config = identity.get("search_config", {})
        if (not isinstance(config, Mapping)
                or config.get("workload") != workload
                or tuple(config.get("sweep_us", ())) != RAW_GRID
                or config.get("threads") != 48
                or config.get("records") != 1_000_000):
            _reject(f"campaign identity/grid mismatch: {workload}")
        if int(config.get("ycsb", {}).get("ycsb_rratio", -1)) != spec["rratio"]:
            _reject(f"campaign identity read-ratio mismatch: {workload}")

        if (manifest.get("campaign_id") != campaign_id
                or manifest.get("workload") != workload
                or manifest.get("status") != "complete"):
            _reject(f"manifest campaign/workload mismatch: {workload}")
        observed_claim = {key: verdict.get(key) for key in CLAIM_BOUNDARY}
        if observed_claim != CLAIM_BOUNDARY:
            _reject(f"D1107 claim boundary mismatch: {workload}")

        completion_artifacts = completion.get("artifacts")
        if not isinstance(completion_artifacts, Mapping):
            _reject(f"completion artifacts missing: {workload}")
        campaign_prefix = f"campaigns/{campaign_id}/"
        source_hashes = {
            role: _sha256(_resolve_external(root, relative))
            for role, relative in paths.items()
        }
        for role in ("campaign_lock", "wal", "dat", "manifest", "verdict"):
            relative = paths[role]
            artifact_relative = relative.split(f"{_job_dir(spec)}/", 1)[1]
            if not artifact_relative.startswith(campaign_prefix):
                _reject(f"internal artifact path mismatch: {workload}/{role}")
            if completion_artifacts.get(artifact_relative) != source_hashes[role]:
                _reject(f"completion artifact digest mismatch: {workload}/{role}")

        source_binding = reservation.get("source_binding", {})
        runtime = manifest.get("runtime_contract", {})
        if (runtime.get("threads") != 48 or runtime.get("records") != 1_000_000
                or runtime.get("env_tag") != "pegasus"
                or runtime.get("clocks_per_us") != 2100
                or runtime.get("numactl") != []):
            _reject(f"manifest runtime conditions mismatch: {workload}")
        if (not str(source_binding.get("ccbench_gitlink_commit", "")).startswith(
                str(runtime.get("ccbench_commit", "")))
                or not str(source_binding.get("ccbench_gitlink_commit", "")).startswith(
                    str(identity.get("ccbench_commit", "")))):
            _reject(f"CCBench source mapping mismatch: {workload}")
        if (source_binding.get("repository_commit") != REPOSITORY_COMMIT
                or source_binding.get("ccbench_gitlink_commit") != CCBENCH_COMMIT):
            _reject(f"source commit identity mismatch: {workload}")

        workloads.append({
            "workload": workload,
            "job_id": expected_job,
            "measurement_host": spec["host"],
            "job_directory": _job_dir(spec),
            "campaign_id": campaign_id,
            "campaign_identity_sha256": identity_sha,
            "campaign_suffix": identity_sha[:8],
            "repository_commit": source_binding.get("repository_commit"),
            "ccbench_commit": source_binding.get("ccbench_gitlink_commit"),
            **{role: {
                "path": paths[role],
                "sha256": source_hashes[role],
            } for role in paths},
        })
    return {
        "binding_kind": "scheduler_receipt_chain",
        "submit": {
            "path": SUBMIT_PATH,
            "sha256": _sha256(submit_path),
            "group_id": GROUP_ID,
            "submission_nonce": nonce,
            "job_script_sha256": script_hash,
        },
        "workloads": workloads,
    }


def validate_external_sources(provenance: Mapping, measurement_root: Path | None) -> dict:
    """Validate canonical proof structure; skip only live source-byte access."""
    _validate_external_provenance_structure(provenance)
    if measurement_root is None:
        return {
            "status": "skipped",
            "layer": "external_measurement_sources",
            "reason": "measurement_root_not_provided",
        }
    root = Path(measurement_root)
    if not root.exists() or not root.is_dir():
        _reject(f"measurement root missing or not a directory: {root}")
    for row in _canonical_external_rows():
        path = row["path"]
        resolved = _resolve_external(root, path)
        if _sha256(resolved) != row["sha256"]:
            _reject(f"external input SHA256 mismatch: {path}")
    observed_chain = _receipt_chain(root)
    if provenance.get("receipt_chain") != observed_chain:
        _reject("provenance receipt mapping mismatch")
    for spec in WORKLOAD_SPECS:
        paths = _paths(spec)
        dat_rows = _parse_dat(_resolve_external(root, paths["dat"]), spec)
        wal_points = _wal_points(_resolve_external(root, paths["wal"]))
        _validate_dat_wal_semantics(dat_rows, wal_points, spec)
    return {"status": "validated", "layer": "external_measurement_sources"}


def _parse_dat(path: Path, spec: Mapping) -> list[dict]:
    rows = []
    columns = []
    source_meta = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        _reject(f"cannot read dat {path}: {exc}")
    for line in lines:
        if line.startswith("# columns:"):
            columns.append(line.split(":", 1)[1].strip())
        elif line.startswith("# provenance:"):
            try:
                source_meta = json.loads(line.split(":", 1)[1].strip())
            except json.JSONDecodeError as exc:
                _reject(f"invalid dat provenance JSON: {exc}")
        elif line and not line.startswith("#"):
            fields = line.split()
            if len(fields) != 5:
                _reject(f"dat row does not have exact five fields: {line}")
            try:
                backoff_us = int(fields[0])
                throughput, abort_rate, latency_ns, cv = map(float, fields[1:])
            except ValueError as exc:
                _reject(f"invalid dat scalar: {exc}")
            values = (throughput, abort_rate, latency_ns, cv)
            if any(not math.isfinite(value) for value in values):
                _reject(f"non-finite dat value at {backoff_us}us")
            if throughput <= 0 or not 0 <= abort_rate <= 1 or latency_ns <= 0 or cv < 0:
                _reject(f"out-of-domain dat value at {backoff_us}us")
            rows.append({
                "backoff_us": backoff_us,
                "throughput_dat_tps": throughput,
                "abort_rate": abort_rate,
                "latency_ns": latency_ns,
                "cv": cv,
            })
    if columns != [DAT_COLUMNS]:
        _reject(f"dat columns must be exact: {columns!r}")
    if tuple(row["backoff_us"] for row in rows) != RAW_GRID:
        _reject("dat raw grid must contain the exact ordered 29 points")
    expected_meta = {
        "campaign": spec["campaign_id"],
        "claim_scope": "descriptive_backoff_shape_only",
        "source_measurement": "trace_disabled",
        "workload": spec["workload"],
    }
    if source_meta != expected_meta:
        _reject(f"dat provenance metadata mismatch: {spec['workload']}")
    return rows


def _wal_points(path: Path) -> dict[int, dict]:
    try:
        records = [json.loads(line) for line in path.read_text(
            encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _reject(f"cannot parse admitted WAL bytes: {exc}")
    genomes = {}
    pending = {}
    committed = {}
    for record in records:
        variant = record.get("variant")
        payload = record.get("payload", {})
        if record.get("stage") == "build_start":
            genomes[variant] = backoff._parse_genome(payload.get("genome", ""))
        elif record.get("stage") == "bench_done":
            pending[variant] = payload
        elif record.get("stage") == "commit" and variant in pending:
            committed[variant] = pending.pop(variant)
    points = {}
    for variant, payload in committed.items():
        genome = genomes.get(variant, {})
        fixed = genome.get("BACKOFF_FIXED")
        if genome.get("BACK_OFF") != "1" or fixed in (None, "-1"):
            continue
        value = int(fixed)
        if value in points:
            _reject(f"duplicate committed static WAL point: {value}")
        points[value] = {"variant": variant, "genome": genome, "payload": payload}
    if tuple(sorted(points)) != RAW_GRID:
        _reject("admitted WAL static grid must contain exact 29 points")
    return points


def _same_number(left: object, right: object, tolerance: float = 1e-9) -> bool:
    return (isinstance(left, (int, float)) and not isinstance(left, bool)
            and isinstance(right, (int, float)) and not isinstance(right, bool)
            and math.isfinite(float(left)) and math.isfinite(float(right))
            and math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance))


def _independent_t95(values: Sequence[object]) -> tuple[float, float]:
    if (len(values) != 5
            or any(not isinstance(value, (int, float)) or isinstance(value, bool)
                   or not math.isfinite(float(value)) for value in values)):
        _reject("throughput repetitions must be five finite numbers")
    samples = [float(value) for value in values]
    mean = statistics.fmean(samples)
    half = T95_DF4 * statistics.stdev(samples) / math.sqrt(len(samples))
    return mean, half


def _validate_dat_wal_semantics(
    rows: Sequence[Mapping], wal_points: Mapping[int, Mapping], spec: Mapping,
) -> None:
    """Validate dat values against decoded WAL payloads, without hash gates."""
    for row in rows:
        value = int(row["backoff_us"])
        point = wal_points.get(value)
        if not isinstance(point, Mapping):
            _reject(f"WAL point missing at {spec['workload']}/{value}us")
        raw = point.get("payload", {})
        reps = raw.get("tps") if isinstance(raw, Mapping) else None
        if not isinstance(reps, list) or len(reps) != 5:
            _reject(f"WAL repetitions mismatch at {spec['workload']}/{value}us")
        median = statistics.median(float(item) for item in reps)
        if (not _same_number(row.get("throughput_dat_tps"), median)
                or not _same_number(row.get("throughput_dat_tps"),
                                    raw.get("median_tps"))):
            _reject(f"dat throughput is not the WAL center at {spec['workload']}/{value}us")
        indicators = raw.get("leading_indicators", {})
        if (not isinstance(indicators, Mapping)
                or not _same_number(row.get("abort_rate"), indicators.get("abort_rate"))
                or not _same_number(row.get("latency_ns"),
                                    indicators.get("latency_ns"), 1e-6)
                or not _same_number(row.get("cv"), raw.get("cv"))):
            _reject(f"dat/WAL metric mismatch at {spec['workload']}/{value}us")
        reciprocal_threads = (float(row["throughput_dat_tps"])
                              * float(row["latency_ns"]) / 1e9)
        if not math.isclose(reciprocal_threads, 48.0, rel_tol=0.0, abs_tol=0.01):
            _reject(f"latency reciprocal contract mismatch: {spec['workload']}/{value}us")


def _expected_conditions(spec: Mapping, chain_row: Mapping) -> dict:
    return {
        "thread_num": 48,
        "ycsb_tuple_num": 1_000_000,
        "extime": 3,
        "clocks_per_us": 2100,
        "ycsb_zipf_skew": 0.9,
        "ycsb_rratio": spec["rratio"],
        "ycsb_rmw": False,
        "numactl_args": [],
        "env": "pegasus",
        "CCBENCH_TRACE": 0,
        "ccbench_commit": "511c953",
        "unresolved_fields": [],
        "trace_disabled": True,
        "repository_commit": chain_row["repository_commit"],
        "ccbench_gitlink_commit": chain_row["ccbench_commit"],
        "measurement_host": chain_row["measurement_host"],
    }


def _measurement_conditions(
    loaded: Mapping, spec: Mapping, chain_row: Mapping, identity: Mapping,
    manifest: Mapping,
) -> dict:
    conditions = dict(loaded.get("conditions", {}))
    runtime = manifest.get("runtime_contract", {})
    conditions["numactl_args"] = runtime.get("numactl")
    conditions["ccbench_commit"] = runtime.get("ccbench_commit")
    conditions["unresolved_fields"] = []
    required = _expected_conditions(spec, chain_row)
    if conditions.get("incomplete_fields") != []:
        _reject(f"incomplete WAL conditions: {spec['workload']}")
    source_condition_keys = (
        "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us",
        "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw", "numactl_args",
        "env", "CCBENCH_TRACE", "ccbench_commit", "unresolved_fields",
    )
    for key in source_condition_keys:
        value = required[key]
        if conditions.get(key) != value:
            _reject(f"measurement condition mismatch: {spec['workload']}/{key}")
    config = identity.get("search_config", {})
    if (config.get("records") != required["ycsb_tuple_num"]
            or config.get("threads") != required["thread_num"]
            or config.get("measurement_env") not in (None, required["env"])):
        _reject(f"lock/WAL measurement condition mismatch: {spec['workload']}")
    return required


def _load_workload(root: Path, spec: Mapping, chain_row: Mapping) -> dict:
    paths = _paths(spec)
    campaign_path = root.resolve() / _campaign_dir(spec)
    # Reuse the frozen generator's admission, WAL conditions and campaign parser.
    loaded = backoff.load_campaign(str(campaign_path))
    if loaded.get("campaign") != spec["campaign_id"]:
        _reject(f"load_campaign campaign mismatch: {spec['workload']}")
    rows = _parse_dat(_resolve_external(root, paths["dat"]), spec)
    wal_points = _wal_points(_resolve_external(root, paths["wal"]))
    _validate_dat_wal_semantics(rows, wal_points, spec)
    loaded_reps = {int(value): list(reps) for value, reps in loaded.get("pts", ())}
    if tuple(sorted(loaded_reps)) != RAW_GRID:
        _reject(f"load_campaign returned wrong grid: {spec['workload']}")

    for row in rows:
        value = row["backoff_us"]
        raw = wal_points[value]["payload"]
        reps = loaded_reps[value]
        if reps != raw.get("tps") or len(reps) != 5:
            _reject(f"WAL repetitions mismatch at {spec['workload']}/{value}us")
        indicators = raw.get("leading_indicators", {})
        mean, half = _independent_t95(reps)
        row.update({
            "throughput_repetitions_tps": [float(item) for item in reps],
            "throughput_wal_mean_tps": float(mean),
            "throughput_ci95_half_tps": float(half),
            "abort_ci95_half": None,
            "wal_metrics": {
                "abort_rate": float(indicators["abort_rate"]),
                "latency_ns": float(indicators["latency_ns"]),
                "cv": float(raw["cv"]),
            },
            "included": value != 1000,
            "exclusion": None,
            "encoding_authority": None,
        })
        if value == 1000:
            row["exclusion"] = {
                "reason_code": "F718",
                "requested_backoff_us": 1000,
                "encoded_mode": 1,
                "encoded_amplitude_us": 0,
                "not_pooled_with_0us": True,
            }
            row["encoding_authority"] = dict(F718_AUTHORITY)

    included = [dict(row) for row in rows if row["included"]]
    excluded = [dict(row) for row in rows if not row["included"]]
    if (tuple(row["backoff_us"] for row in included) != INCLUDED_GRID
            or len(excluded) != 1 or excluded[0]["backoff_us"] != 1000
            or included[0]["backoff_us"] != 0):
        _reject(f"F718 include/exclude contract mismatch: {spec['workload']}")

    lock = _json(_resolve_external(root, paths["campaign_lock"]))
    _digest, identity = _campaign_identity(lock, str(spec["campaign_id"]))
    manifest = _json(_resolve_external(root, paths["manifest"]))
    conditions = _measurement_conditions(loaded, spec, chain_row, identity, manifest)
    verdict = _json(_resolve_external(root, paths["verdict"]))
    return {
        "workload": spec["workload"],
        "campaign_id": spec["campaign_id"],
        "job_id": spec["job_id"],
        "raw_points": rows,
        "included_points": included,
        "excluded_points": excluded,
        "conditions": conditions,
        "claim_boundary": {key: verdict[key] for key in CLAIM_BOUNDARY},
        "campaign_read_purpose": loaded.get("read_purpose"),
        "campaign_verifier_epoch": loaded.get("campaign_verifier_epoch"),
    }


def load_measurements(measurement_root: Path) -> tuple[list[dict], list[dict], dict]:
    root = Path(measurement_root)
    # The frozen admission and plotting dependency initializes NumPy lazily.
    backoff._load_plot_deps()
    external_inputs = _external_rows(root)
    chain = _receipt_chain(root)
    chain_by_workload = {row["workload"]: row for row in chain["workloads"]}
    campaigns = [_load_workload(root, spec, chain_by_workload[spec["workload"]])
                 for spec in WORKLOAD_SPECS]
    return campaigns, external_inputs, chain


def _caption(campaigns: Sequence[Mapping]) -> str:
    hosts = "/".join(str(c["conditions"]["measurement_host"]) for c in campaigns)
    return (
        "Extended static backoff under trace-disabled committed measurements "
        "(48 threads, 1,000,000 records, Zipf skew 0.9, read ratios 5/50/95%, "
        f"read-modify-write (RMW) disabled, Pegasus hosts {hosts}). Throughput "
        "is reported in M tps = million transactions per second and is the mean "
        "of five WAL "
        "repetitions with t-distribution 95% confidence intervals; abort rate is "
        "the dat fraction and has no repetition-level confidence interval. Static "
        "0 µs means BACK_OFF=1 and BACKOFF_FIXED=0, not no backoff. The requested "
        "1000 µs row is retained in provenance but excluded under the canonical "
        "F718/D1106 ruling, which asserts mode 1 and amplitude 0 as a ruling "
        "interpretation rather than a value derived from measurement artifacts. "
        + LATENCY_NOTE + " " + COMPARISON_WARNING
    )


def _set_x_contract(axis) -> None:
    axis.set_xscale("symlog", base=10, linthresh=1, linscale=1)
    axis.xaxis.set_major_locator(backoff.FixedLocator(SPARSE_TICKS))
    axis.xaxis.set_major_formatter(backoff.FixedFormatter([str(x) for x in SPARSE_TICKS]))
    axis.xaxis.set_minor_locator(backoff.NullLocator())


def _validate_text_bboxes(fig) -> None:
    """Fail on out-of-figure or overlapping visible text, including tick labels."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    texts = []
    for item in fig.findobj(backoff.mpl.text.Text):
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


def make_figure(campaigns: Sequence[Mapping]):
    """Return the figure and the nine semantic artist-series records."""
    if tuple(c.get("workload") for c in campaigns) != tuple(
            spec["workload"] for spec in WORKLOAD_SPECS):
        _reject("workload order must be write-heavy/balanced/read-heavy")
    backoff._load_plot_deps()
    backoff._style()
    fig, axes = backoff.plt.subplots(
        2, 3, figsize=(10.8, 6.3), squeeze=False, sharex=False, sharey=False)
    artists = []
    for column, campaign in enumerate(campaigns):
        workload = str(campaign["workload"])
        points = campaign["included_points"]
        xs = [row["backoff_us"] for row in points]
        throughput = [row["throughput_wal_mean_tps"] / 1e6 for row in points]
        ci = [row["throughput_ci95_half_tps"] / 1e6 for row in points]
        abort = [row["abort_rate"] for row in points]
        if tuple(xs) != INCLUDED_GRID:
            _reject(f"artist x grid mismatch before drawing: {workload}")

        top = axes[0, column]
        throughput_label = f"{workload} throughput"
        errorbar = top.errorbar(
            xs, throughput, yerr=ci, fmt="o-", color=backoff.FOCAL,
            ecolor=backoff.FOCAL, elinewidth=0.9, capsize=0, markersize=3.6,
            label=throughput_label, zorder=3)
        errorbar.lines[0].set_label(throughput_label)
        ci_label = f"{workload} throughput 95% CI"
        if len(errorbar.lines[2]) != 1:
            _reject(f"unexpected throughput CI artist count: {workload}")
        errorbar.lines[2][0].set_label(ci_label)
        top.set_ylabel("throughput (M tps)")
        top.set_title(f"{workload}\nread ratio {campaign['conditions']['ycsb_rratio']}%")
        top.margins(y=0.13)
        _set_x_contract(top)

        bottom = axes[1, column]
        abort_label = f"{workload} abort rate"
        bottom.plot(xs, abort, "s-", color=backoff.ABORT, markersize=3.3,
                    label=abort_label, zorder=3)
        bottom.set_ylabel("abort rate (fraction)")
        bottom.set_xlabel("static backoff (µs)")
        bottom.margins(y=0.13)
        _set_x_contract(bottom)

        artists.extend([
            {"workload": workload, "metric": "throughput_mean", "kind": "line",
             "label": throughput_label, "x": xs, "y": throughput,
             "unit": "M tps"},
            {"workload": workload, "metric": "throughput_ci95", "kind": "interval",
             "label": ci_label, "x": xs, "y": ci,
             "lower": [y - h for y, h in zip(throughput, ci)],
             "upper": [y + h for y, h in zip(throughput, ci)],
             "unit": "M tps"},
            {"workload": workload, "metric": "abort_rate", "kind": "line",
             "label": abort_label, "x": xs, "y": abort, "unit": "fraction",
             "ci_artist": False},
        ])

    fig.suptitle(
        "B-10 extended static backoff — trace disabled, 48 threads, "
        "1M records, skew 0.9, RMW off",
        fontsize=9.5, y=0.985)
    fig.text(0.5, 0.018, COMPARISON_WARNING, ha="center", va="bottom", fontsize=7)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.83, bottom=0.18,
                        wspace=0.28, hspace=0.36)
    _validate_text_bboxes(fig)
    fig._b10_artist_series = artists  # direct artist/provenance bridge for tests
    fig._b10_caption = _caption(campaigns)
    fig._b10_comparison_warning = COMPARISON_WARNING
    return fig, artists


def _axis_contract() -> dict:
    return {
        "layout": {"rows": 2, "columns": 3,
                   "workload_order": [spec["workload"] for spec in WORKLOAD_SPECS],
                   "top_metric": "throughput_mean", "bottom_metric": "abort_rate"},
        "x": {"scale": "symlog", "base": 10, "linthresh": 1, "linscale": 1,
              "fixed_ticks": list(SPARSE_TICKS), "includes_zero": True,
              "includes_900": True},
        "y": {"shared": False, "scope": "workload-local", "autoscale": True,
              "throughput_unit": "M tps", "abort_unit": "fraction"},
        "artist_series_count": 9,
        "abort_ci_artist": False,
        "bbox_overlap_policy": "fail-before-save-including-tick-labels",
    }


def build_provenance(
    campaigns: Sequence[Mapping], external_inputs: list[dict], receipt_chain: dict,
    outputs: Sequence[Path], artist_series: list[dict], measurement_root: Path,
) -> dict:
    generator = Path(__file__).resolve()
    dependency = REPO_ROOT / "tools" / "plotting" / "plot_backoff.py"
    data = []
    for campaign in campaigns:
        data.append({
            "workload": campaign["workload"],
            "campaign_id": campaign["campaign_id"],
            "job_id": campaign["job_id"],
            "raw_points": campaign["raw_points"],
            "included_points": campaign["included_points"],
            "excluded_points": campaign["excluded_points"],
            "conditions": campaign["conditions"],
            "claim_boundary": campaign["claim_boundary"],
            "campaign_read_purpose": campaign["campaign_read_purpose"],
            "campaign_verifier_epoch": campaign["campaign_verifier_epoch"],
        })
    caption = _caption(campaigns)
    provenance = {
        "schema": SCHEMA,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": {"path": _repo_relative(generator), "sha256": _sha256(generator)},
        "dependencies": [{
            "role": "admitted-wal-conditions-t95-ci-style",
            "path": _repo_relative(dependency),
            "sha256": _sha256(dependency),
        }],
        "outputs": [{"path": _repo_relative(path), "sha256": _sha256(path)}
                    for path in outputs],
        "external_source_locator": {
            "root_at_generation": str(Path(measurement_root).resolve()),
            "validation_key": "root-relative-path-plus-sha256",
        },
        "external_inputs": external_inputs,
        "receipt_chain": receipt_chain,
        "data": data,
        "artist_series": artist_series,
        "axis_contract": _axis_contract(),
        "claim_boundary": dict(CLAIM_BOUNDARY),
        "text_contract": {
            "figure_body": COMPARISON_WARNING,
            "caption": caption,
            "provenance": COMPARISON_WARNING,
            "comparison_warning": COMPARISON_WARNING,
            "latency_note": LATENCY_NOTE,
            "static_zero_is_no_backoff": False,
            "add_analysis_drawn": False,
            "legacy_three_percent_floor_drawn": False,
            "noise_band_or_onset_drawn": False,
            "no_backoff_or_adaptive_baseline_drawn": False,
        },
    }
    validate_provenance_semantics(provenance)
    return provenance


def validate_provenance_semantics(provenance: Mapping) -> None:
    if provenance.get("schema") != SCHEMA:
        _reject(f"unsupported provenance schema: {provenance.get('schema')}")
    _validate_external_provenance_structure(provenance)
    if provenance.get("claim_boundary") != CLAIM_BOUNDARY:
        _reject("D1107 claim boundary mismatch")
    text = provenance.get("text_contract")
    if not isinstance(text, Mapping):
        _reject("text_contract is missing")
    for field in ("figure_body", "provenance", "comparison_warning"):
        if text.get(field) != COMPARISON_WARNING:
            _reject(f"panel comparison prohibition mismatch: {field}")
    if COMPARISON_WARNING not in str(text.get("caption", "")):
        _reject("caption lacks panel comparison prohibition")
    caption = str(text.get("caption", ""))
    if caption.count("M tps = million transactions per second") != 1:
        _reject("caption must expand M tps exactly once")
    if caption.count("read-modify-write (RMW) disabled") != 1:
        _reject("caption must expand RMW exactly once")
    if ("canonical F718/D1106 ruling" not in caption
            or "rather than a value derived from measurement artifacts" not in caption):
        _reject("caption misstates F718/D1106 authority")
    if text.get("latency_note") != LATENCY_NOTE:
        _reject("latency independence boundary mismatch")
    forbidden = ("add_analysis_drawn", "legacy_three_percent_floor_drawn",
                 "noise_band_or_onset_drawn", "no_backoff_or_adaptive_baseline_drawn")
    if any(text.get(key) is not False for key in forbidden):
        _reject("forbidden analysis/baseline artist contract mismatch")
    if text.get("static_zero_is_no_backoff") is not False:
        _reject("static zero must not be called no-backoff")

    axis = provenance.get("axis_contract")
    if (not isinstance(axis, Mapping) or axis.get("artist_series_count") != 9
            or axis.get("abort_ci_artist") is not False
            or axis.get("layout") != _axis_contract()["layout"]
            or axis.get("x") != _axis_contract()["x"]
            or axis.get("y") != _axis_contract()["y"]
            or axis.get("bbox_overlap_policy")
            != "fail-before-save-including-tick-labels"):
        _reject("axis contract mismatch")
    data = provenance.get("data")
    if (not isinstance(data, list)
            or [row.get("workload") for row in data]
            != [spec["workload"] for spec in WORKLOAD_SPECS]):
        _reject("provenance workload order mismatch")
    chain_by_workload = {
        row["workload"]: row for row in _canonical_receipt_chain()["workloads"]
    }
    expected_artists = []
    for campaign, spec in zip(data, WORKLOAD_SPECS):
        workload = str(spec["workload"])
        if (campaign.get("campaign_id") != spec["campaign_id"]
                or campaign.get("job_id") != spec["job_id"]):
            _reject(f"campaign/job identity mismatch: {workload}")
        if campaign.get("claim_boundary") != CLAIM_BOUNDARY:
            _reject(f"campaign D1107 claim boundary mismatch: {workload}")
        expected_conditions = _expected_conditions(spec, chain_by_workload[workload])
        if campaign.get("conditions") != expected_conditions:
            _reject(f"measurement conditions exact-field mismatch: {workload}")
        raw = campaign.get("raw_points")
        included = campaign.get("included_points")
        excluded = campaign.get("excluded_points")
        if (not isinstance(raw, list) or not isinstance(included, list)
                or not isinstance(excluded, list)):
            _reject("raw/included/excluded point sets must be lists")
        if [row.get("backoff_us") for row in raw] != list(RAW_GRID):
            _reject("raw provenance grid mismatch")
        if [row.get("backoff_us") for row in included] != list(INCLUDED_GRID):
            _reject("included provenance grid mismatch")
        if included != [row for row in raw if row.get("included") is True]:
            _reject("included points do not preserve all raw values")
        if excluded != [row for row in raw if row.get("included") is False]:
            _reject("excluded points do not preserve all raw values")
        if len(excluded) != 1 or excluded[0].get("backoff_us") != 1000:
            _reject("1000us must be the sole excluded point")
        exclusion = excluded[0].get("exclusion")
        if exclusion != {
            "reason_code": "F718", "requested_backoff_us": 1000,
            "encoded_mode": 1, "encoded_amplitude_us": 0,
            "not_pooled_with_0us": True,
        }:
            _reject("F718 exclusion evidence mismatch")
        if excluded[0].get("encoding_authority") != F718_AUTHORITY:
            _reject("F718/D1106 canonical ruling authority mismatch")
        zero = included[0]
        if zero.get("backoff_us") != 0 or zero.get("included") is not True:
            _reject("static zero was not preserved")
        for point in raw:
            if (not isinstance(point.get("throughput_repetitions_tps"), list)
                    or len(point["throughput_repetitions_tps"]) != 5
                    or point.get("throughput_ci95_half_tps") is None
                    or point.get("abort_ci95_half") is not None
                    or any(key not in point for key in (
                        "throughput_dat_tps", "throughput_wal_mean_tps",
                        "abort_rate", "latency_ns", "cv"))):
                _reject("point measurement/CI provenance is incomplete")
            repetitions = point["throughput_repetitions_tps"]
            mean, half = _independent_t95(repetitions)
            median = statistics.median(float(value) for value in repetitions)
            if not _same_number(point.get("throughput_wal_mean_tps"), mean, 1e-6):
                _reject("stored WAL mean does not match repetitions")
            if not _same_number(point.get("throughput_ci95_half_tps"), half, 1e-6):
                _reject("stored t95 CI does not match repetitions")
            if not _same_number(point.get("throughput_dat_tps"), median, 1e-6):
                _reject("stored dat throughput is not the repetitions median")
            wal_metrics = point.get("wal_metrics")
            if (not isinstance(wal_metrics, Mapping)
                    or set(wal_metrics) != {"abort_rate", "latency_ns", "cv"}
                    or not _same_number(point.get("abort_rate"),
                                        wal_metrics.get("abort_rate"))
                    or not _same_number(point.get("latency_ns"),
                                        wal_metrics.get("latency_ns"), 1e-6)
                    or not _same_number(point.get("cv"), wal_metrics.get("cv"))):
                _reject("stored dat/WAL abort-latency-CV mapping mismatch")
            abort = point.get("abort_rate")
            latency = point.get("latency_ns")
            cv = point.get("cv")
            dat_tps = point.get("throughput_dat_tps")
            if (not _same_number(abort, abort) or not 0 <= float(abort) <= 1
                    or not _same_number(latency, latency) or float(latency) <= 0
                    or not _same_number(cv, cv) or float(cv) < 0
                    or not _same_number(dat_tps, dat_tps) or float(dat_tps) <= 0):
                _reject("stored point metric is outside its domain")
            reciprocal_threads = float(dat_tps) * float(latency) / 1e9
            if not math.isclose(
                    reciprocal_threads, 48.0, rel_tol=0.0, abs_tol=0.01):
                _reject("stored latency reciprocal contract mismatch")
            expected_authority = F718_AUTHORITY if point["backoff_us"] == 1000 else None
            if point.get("encoding_authority") != expected_authority:
                _reject("point exclusion authority mismatch")
        xs = [row["backoff_us"] for row in included]
        means = [row["throughput_wal_mean_tps"] / 1e6 for row in included]
        cis = [row["throughput_ci95_half_tps"] / 1e6 for row in included]
        aborts = [row["abort_rate"] for row in included]
        expected_artists.extend([
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
    if provenance.get("artist_series") != expected_artists:
        _reject("artist series differ from included measurements")


def _resolve_repo(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        _reject(f"repo path must be a non-empty string: {value!r}")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        _reject(f"repo path leaves repository: {value}")
    root_resolved = root.resolve()
    candidate = root_resolved / relative
    if not candidate.exists():
        _reject(f"repo artifact missing: {value}")
    resolved = candidate.resolve()
    if not _inside(root_resolved, resolved):
        _reject(f"repo path leaves repository: {value}")
    return resolved


def validate_repo_closure(provenance: Mapping, repo_root: Path) -> None:
    """Validate generator/dependency/output bytes without an external root."""
    validate_provenance_semantics(provenance)
    root = Path(repo_root)
    generator = provenance.get("generator")
    if not isinstance(generator, Mapping):
        _reject("generator closure is missing")
    if generator.get("path") != "tools/plotting/plot_b10_extended_backoff.py":
        _reject("generator path mismatch")
    generator_path = _resolve_repo(root, generator.get("path"))
    if generator.get("sha256") != _sha256(generator_path):
        _reject("generator SHA256 mismatch")
    dependencies = provenance.get("dependencies")
    if (not isinstance(dependencies, list) or len(dependencies) != 1
            or dependencies[0].get("role")
            != "admitted-wal-conditions-t95-ci-style"
            or dependencies[0].get("path") != "tools/plotting/plot_backoff.py"):
        _reject("plot_backoff dependency closure mismatch")
    dependency_path = _resolve_repo(root, dependencies[0].get("path"))
    if dependencies[0].get("sha256") != _sha256(dependency_path):
        _reject("dependency SHA256 mismatch")
    outputs = provenance.get("outputs")
    if (not isinstance(outputs, list) or len(outputs) != 2
            or [row.get("path") for row in outputs] != list(REAL_OUTPUT_PATHS)):
        _reject("outputs must be the exact fig2c PNG/PDF paths")
    for row in outputs:
        path = _resolve_repo(root, row.get("path"))
        if row.get("sha256") != _sha256(path):
            _reject(f"output SHA256 mismatch: {row.get('path')}")


def _parse_cli(argv: Sequence[str]) -> tuple[Path, Path] | None:
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        return None
    if len(argv) != 3:
        _reject("OUT_PREFIX and MEASUREMENT_ROOT are required")
    return Path(argv[1]), Path(argv[2])


def main(argv: Sequence[str]) -> int:
    try:
        parsed = _parse_cli(argv)
        if parsed is None:
            print(__doc__)
            return 0
        out_prefix, measurement_root = parsed
        campaigns, external_inputs, chain = load_measurements(measurement_root)
        figure, artists = make_figure(campaigns)
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        outputs = [Path(str(out_prefix) + ".png"), Path(str(out_prefix) + ".pdf")]
        # The renderer-backed check, including tick labels, has already run in
        # make_figure.  Repeat immediately before each save so later callers
        # cannot mutate the figure into an overlapping state.
        for output in outputs:
            _validate_text_bboxes(figure)
            figure.savefig(output, dpi=200, bbox_inches="tight")
        provenance = build_provenance(
            campaigns, external_inputs, chain, outputs, artists, measurement_root)
        provenance_path = Path(str(out_prefix) + ".provenance.json")
        provenance_path.write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"wrote {outputs[0]} / {outputs[1]} / {provenance_path}")
        return 0
    except (B10FigureError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    finally:
        if backoff.plt is not None:
            backoff.plt.close("all")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
