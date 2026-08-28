# -*- coding: utf-8 -*-
"""One-rep balanced diagnostic for Silo adaptive requested backoff microseconds."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import (  # noqa: E402
    artifact_admission,
    buildcache,
    campaign_lock as campaign_lock_codec,
    p2_2,
    patchharness,
    pin,
    pipeline,
    screening_driver,
    source_digest,
    wal,
)
from .backoff_extended_sweep import (  # noqa: E402
    TEMPLATE_PATCH,
    WORKLOAD_BY_TAG,
    _assert_backoff_fixed_materialized,
    _repo_root,
    _resolve_ccbench_dir,
    genomes,
)
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    resolve_current_build_admission_policy,
    resolve_immediate_predecessor_build_admission_policy,
)
from .layout import CampaignLayout  # noqa: E402
from .lock import bench_lock  # noqa: E402
from .model import Genome  # noqa: E402


WORKLOAD = "balanced"
EXTIME = 3
REPS = 1
DEFAULT_BUILD_TIMEOUT_SECONDS = 1800
DEFAULT_RECORD_TIMEOUT_SECONDS = 300
PATCH_REL = "patches/silo-backoff-requested-us.patch"
DIAGNOSTIC_FLAG = "BACKOFF_REQUESTED_US"
DIAGNOSTIC_USE_CLASS = "diagnostic"
PREFIX = "IZANAGI_BACKOFF_REQUESTED_US_V1"
REP_SCHEMA = "b10-backoff-requested-us-rep/v1"
MANIFEST_SCHEMA = "b10-backoff-requested-us-manifest/v1"
SOURCE_MEASUREMENT = "instrumented_requested_us"
D1106_STATES = (0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
EXPECTED_FIXED_GRID = (
    0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 100,
    150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000,
)
FIELD_NAMES = (
    "call_count",
    "requested_us_sum",
    *(f"state_{state}_call_count" for state in D1106_STATES),
    "unknown_state_call_count",
    "counter_overflowed",
)
USAGE_ELIGIBILITY_KEYS = (
    "headline_tps",
    "formal_b10",
    "floor",
    "fitness",
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
UINT64_MAX = (1 << 64) - 1


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


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_regular_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"required regular file is unreadable: {path}") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError(f"required regular file is not regular: {path}")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        os.close(descriptor)


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_read_regular_bytes(path))


def _decode_json_object(raw: bytes, label: object) -> dict:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON: {label}") from exc
    if type(value) is not dict:
        raise RuntimeError(f"JSON object required: {label}")
    return value


def _read_json_object(path: Path) -> tuple[dict, bytes]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"required regular JSON is missing: {path}")
    raw = _read_regular_bytes(path)
    return _decode_json_object(raw, path), raw


def _write_create_only(path: Path, value: object) -> None:
    payload = _canonical_json_bytes(value)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        written = os.write(descriptor, payload)
        if written != len(payload):
            raise OSError(f"short create-only write: {written}/{len(payload)}")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_create_only_at(directory_fd: int, name: str, value: object) -> None:
    if Path(name).name != name or name in {".", ".."}:
        raise RuntimeError(f"unsafe diagnostic artifact name: {name!r}")
    payload = _canonical_json_bytes(value)
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError(f"short create-only write: {offset}/{len(payload)}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _materialize_artifact_snapshot(
        destination: Path, snapshots: Mapping[str, bytes],
) -> None:
    for relative, raw in sorted(snapshots.items()):
        candidate = destination / relative
        candidate.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = (
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(candidate, flags, 0o600)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:
                    raise OSError("snapshot materialization made no progress")
                offset += written
        finally:
            os.close(descriptor)


def _parse_genome(canonical: object) -> tuple[str, dict[str, int]]:
    if type(canonical) is not str:
        raise RuntimeError("reference genome is not an exact string")
    try:
        protocol, body = canonical.split("|", 1)
        flags = {
            key: int(value)
            for key, value in (item.split("=", 1) for item in body.split(","))
        }
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid reference genome: {canonical!r}") from exc
    if not protocol or not flags:
        raise RuntimeError(f"invalid reference genome: {canonical!r}")
    return protocol, flags


def _path_has_symlink(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return True
    return False


def _snapshot_completion_artifacts(
        reference_root: Path, completion: Mapping[str, object],
) -> tuple[dict[str, str], dict[str, bytes]]:
    artifacts = completion.get("artifacts")
    if type(artifacts) is not dict or not artifacts:
        raise RuntimeError("reference completion artifact map is missing")
    checked: dict[str, str] = {}
    snapshots: dict[str, bytes] = {}
    for relative, expected in sorted(artifacts.items()):
        if (
            type(relative) is not str
            or type(expected) is not str
            or _SHA256_RE.fullmatch(expected) is None
        ):
            raise RuntimeError("reference completion artifact entry is malformed")
        candidate_rel = Path(relative)
        if candidate_rel.is_absolute() or ".." in candidate_rel.parts:
            raise RuntimeError(f"unsafe reference artifact path: {relative!r}")
        candidate = reference_root / candidate_rel
        if _path_has_symlink(reference_root, candidate) or not candidate.is_file():
            raise RuntimeError(f"reference artifact SHA mismatch: {relative}")
        raw = _read_regular_bytes(candidate)
        if _sha256_bytes(raw) != expected:
            raise RuntimeError(f"reference artifact SHA mismatch: {relative}")
        checked[relative] = expected
        snapshots[relative] = raw
    return checked, snapshots


def _verify_completion_artifacts(
        reference_root: Path, completion: Mapping[str, object]) -> dict[str, str]:
    checked, _snapshots = _snapshot_completion_artifacts(reference_root, completion)
    return checked


def _load_wal_snapshot(raw: bytes) -> tuple[list[dict], list]:
    if not raw or not raw.endswith(b"\n"):
        raise RuntimeError("reference WAL is empty or has a partial trailing record")
    raw_records = []
    records = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        try:
            record = wal.parse_line(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, wal.WalLineError) as exc:
            raise RuntimeError(f"reference WAL parse error at line {line_number}") from exc
        records.append(record)
        raw_records.append({
            "variant": record.variant,
            "stage": record.stage,
            "env_tag": record.env_tag,
            "ts": record.ts,
            "payload": record.payload,
        })
    return raw_records, records


def _record_sha256(record: Mapping[str, object]) -> str:
    return _sha256_bytes(_canonical_json_bytes(dict(record)))


def _runtime_invocation(
        run_cmd: object, *, expected_numactl: object,
) -> tuple[str, dict[str, str]]:
    if type(run_cmd) is not str or not run_cmd:
        raise RuntimeError("reference run command is missing")
    tokens = shlex.split(run_cmd)
    binaries = [index for index, token in enumerate(tokens) if token.endswith("/ycsb_silo.exe")]
    if len(binaries) != 1:
        raise RuntimeError("reference run command has no unique ycsb_silo binary")
    if (
        type(expected_numactl) is not list
        or any(type(token) is not str for token in expected_numactl)
        or tokens[:binaries[0]] != expected_numactl
    ):
        raise RuntimeError("reference run command numactl prefix mismatch")
    result: dict[str, str] = {}
    for token in tokens[binaries[0] + 1:]:
        if not token.startswith("-") or "=" not in token:
            raise RuntimeError(f"unexpected reference runtime token: {token!r}")
        key, value = token[1:].split("=", 1)
        if not key or key in result:
            raise RuntimeError(f"duplicate reference runtime flag: {key!r}")
        result[key] = value
    expected = {
        "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us",
        *WORKLOAD_BY_TAG[WORKLOAD],
    }
    if set(result) != expected:
        raise RuntimeError(
            f"reference runtime flags mismatch: missing={sorted(expected - set(result))!r}, "
            f"extra={sorted(set(result) - expected)!r}"
        )
    return tokens[binaries[0]], result


def _runtime_flags(
        run_cmd: object, *, expected_numactl: object) -> dict[str, str]:
    _binary, flags = _runtime_invocation(
        run_cmd, expected_numactl=expected_numactl,
    )
    return flags


def _command_tokens(value: object, label: str) -> list[str]:
    if type(value) is str:
        try:
            tokens = shlex.split(value)
        except ValueError as exc:
            raise RuntimeError(f"reference {label} is malformed") from exc
    elif type(value) is list and all(type(token) is str for token in value):
        tokens = list(value)
    else:
        raise RuntimeError(f"reference {label} is missing")
    if not tokens:
        raise RuntimeError(f"reference {label} is empty")
    return tokens


def _option_path(tokens: Sequence[str], option: str, label: str) -> str:
    values = []
    for index, token in enumerate(tokens):
        if token == option:
            if index + 1 >= len(tokens):
                raise RuntimeError(f"reference {label} has an incomplete {option}")
            values.append(tokens[index + 1])
        elif token.startswith(option) and token != option:
            values.append(token[len(option):].removeprefix("="))
    if len(values) != 1 or not values[0]:
        raise RuntimeError(f"reference {label} has no unique {option} path")
    if not os.path.isabs(values[0]):
        raise RuntimeError(f"reference {label} {option} path is not absolute")
    return os.path.normpath(values[0])


def _require_reference_binary_binding(
        done_payload: object, run_binary: str,
) -> dict[str, object]:
    """Bind the bench executable to its attempt-local build receipt and SHA."""
    if type(done_payload) is not dict:
        raise RuntimeError("reference build_done payload is malformed")
    expected_sha256 = done_payload.get("perf_bin_sha256")
    display_hash = done_payload.get("perf_bin")
    if (
        type(expected_sha256) is not str
        or _SHA256_RE.fullmatch(expected_sha256) is None
        or type(display_hash) is not str
        or display_hash != expected_sha256[:16]
    ):
        raise RuntimeError("reference perf binary SHA receipt is inconsistent")
    if type(run_binary) is not str or not os.path.isabs(run_binary):
        raise RuntimeError("reference bench binary path must be absolute")
    normalized_run = os.path.normpath(run_binary)
    build_tokens = _command_tokens(done_payload.get("perf_build_cmd"), "perf build command")
    configure_tokens = _command_tokens(
        done_payload.get("perf_configure_cmd"), "perf configure command",
    )
    build_dir = _option_path(build_tokens, "-" * 2 + "build", "perf build command")
    configure_dir = _option_path(configure_tokens, "-B", "perf configure command")
    if build_dir != configure_dir:
        raise RuntimeError("reference perf build/configure cache identity mismatch")
    receipt_binary = os.path.join(build_dir, "cc", "silo", "ycsb_silo.exe")
    if normalized_run != receipt_binary:
        raise RuntimeError("reference bench binary differs from perf build receipt")

    if os.path.lexists(normalized_run):
        actual_sha256 = _sha256_file(Path(normalized_run))
        if actual_sha256 != expected_sha256:
            raise RuntimeError("reference bench binary SHA differs from build_done")
        method = "live-binary-sha256"
    else:
        # Frozen B-10 roots may outlive their scratch build cache.  In that case
        # do not claim a rehash: retain only the exact configure/build cache path
        # receipt that mechanically names the bench executable for this attempt.
        method = "attempt-build-cache-receipt"
    return {
        "run_binary": normalized_run,
        "perf_build_directory": build_dir,
        "binding_method": method,
        "sha256": expected_sha256,
        "live_binary_rehashed": method == "live-binary-sha256",
    }


def _unique_stage(records: Sequence[Mapping[str, object]], stage: str) -> Mapping[str, object]:
    selected = [record for record in records if record.get("stage") == stage]
    if len(selected) != 1:
        raise RuntimeError(f"reference adaptive variant requires one {stage}: {len(selected)}")
    return selected[0]


def _grid_projection(committed_genomes: Sequence[str]) -> dict[str, object]:
    observed_fixed_grid = []
    for canonical in committed_genomes:
        protocol, flags = _parse_genome(canonical)
        if (
            protocol == "silo"
            and flags.get("BACK_OFF") == 1
            and flags.get("BACKOFF_FIXED", -1) >= 0
        ):
            observed_fixed_grid.append(flags["BACKOFF_FIXED"])
    observed_fixed_grid.sort()
    if observed_fixed_grid != list(EXPECTED_FIXED_GRID):
        raise RuntimeError("reference observed fixed grid does not match D1106 campaign")
    requested_intersection = sorted(set(observed_fixed_grid) & set(D1106_STATES))
    admitted_intersection = [state for state in requested_intersection if state != 1000]
    if requested_intersection != list(D1106_STATES) or admitted_intersection != list(
            D1106_STATES[:-1]):
        raise RuntimeError("reference requested/admitted intersections violate F718")
    return {
        "expected_d1106_grid": list(EXPECTED_FIXED_GRID),
        "observed_fixed_grid": observed_fixed_grid,
        "requested_grid_intersection": requested_intersection,
        "admitted_realized_intersection": admitted_intersection,
        "admitted_realized_exclusion": "1000us excluded by F718 encoding collision",
    }


def _reference_records(
        campaign_root: Path, lock: Mapping[str, object], decoded_lock,
        records: list,
) -> list:
    """Validate a frozen campaign against current or the exact T-1941 predecessor policy."""
    layout = CampaignLayout(root=str(campaign_root))
    artifact_admission.require_campaign_verifier_epoch(
        layout,
        purpose=artifact_admission.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    current_policy = resolve_current_build_admission_policy()
    try:
        decision = artifact_admission.classify_campaign(layout)
    except artifact_admission.ArtifactAdmissionError as exc:
        if str(exc) != "post-policy campaign lock admission policy differs":
            raise RuntimeError("reference campaign admission failed") from exc
        policy = resolve_immediate_predecessor_build_admission_policy(
            added_generator_id=GeneratorId.BACKOFF_REQUESTED_US,
        )
        search = decoded_lock.identity.get("search_config")
        if (
            type(search) is not dict
            or search.get("build_admission") != policy.as_preimage()
        ):
            raise RuntimeError(
                "reference campaign is not the exact pre-T-1941 admission policy"
            ) from exc
    else:
        if not decision.admitted:
            raise RuntimeError("reference campaign is not admitted")
        policy = current_policy

    if not records:
        raise RuntimeError("reference WAL is empty")
    try:
        wal._validate_attempt_topology(  # frozen read-only historical validation
            records,
            admission_policy=policy,
            campaign_lock=decoded_lock,
        )
        wal.validate_trigger_bindings(
            records, campaign_lock=lock, require_build_start=True,
        )
    except (TypeError, wal.AttemptTopologyError) as exc:
        raise RuntimeError("reference attempt admission is invalid") from exc
    if wal.is_trigger_machine_campaign_lock(lock):
        raise RuntimeError("trigger campaign cannot serve as a D1106 reference")

    lock_commit = decoded_lock.identity.get("ccbench_commit")
    for record in records:
        if record.stage != "build_start":
            continue
        receipt = record.payload.get("build_admission")
        if receipt is None:
            continue
        source = receipt.get("source") if type(receipt) is dict else None
        canonical = record.payload.get("genome")
        src_token = record.payload.get("src_token")
        if (
            type(source) is not dict
            or type(canonical) is not str
            or type(src_token) is not str
            or source.get("genome_sha256")
            != _sha256_bytes(canonical.encode("utf-8"))
            or source.get("src_token") != src_token
            or source.get("ccbench_commit") != lock_commit
        ):
            raise RuntimeError("reference build source differs from WAL/lock identity")
        protocol, flags = _parse_genome(canonical)
        if record.variant != pipeline.variant_id(Genome(protocol, flags), src_token):
            raise RuntimeError("reference variant differs from genome/source identity")
    return records


def load_reference_binding(reference_root: str) -> dict[str, object]:
    """Validate and project one exact certified balanced D1106 reference root."""
    root = Path(reference_root).resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("reference root must be a real directory")
    completion_path = root / "completion.json"
    completion, completion_raw = _read_json_object(completion_path)
    if (
        completion.get("schema_version") != "b10-backoff-grid-job-complete/v1"
        or completion.get("status") != "complete"
        or completion.get("workload") != WORKLOAD
        or type(completion.get("campaign_id")) is not str
    ):
        raise RuntimeError("reference completion identity is not certified balanced D1106")
    artifact_sha256, artifact_snapshots = _snapshot_completion_artifacts(
        root, completion,
    )

    campaign_id = completion["campaign_id"]
    if Path(campaign_id).name != campaign_id or campaign_id in {".", ".."}:
        raise RuntimeError("reference campaign id is not a safe path component")
    campaign_root = root / "campaigns" / campaign_id
    if _path_has_symlink(root, campaign_root) or not campaign_root.is_dir():
        raise RuntimeError("reference campaign directory is missing or symlinked")

    lock_rel = f"campaigns/{campaign_id}/campaign.lock"
    wal_rel = f"campaigns/{campaign_id}/runs/wal.jsonl"
    if lock_rel not in artifact_sha256 or wal_rel not in artifact_sha256:
        raise RuntimeError("reference completion omits campaign lock or WAL")
    lock_path = root / lock_rel
    wal_path = root / wal_rel
    lock_raw = artifact_snapshots[lock_rel]
    campaign_lock_value = _decode_json_object(lock_raw, lock_path)
    try:
        decoded_lock = campaign_lock_codec.decode_campaign_lock_bytes(lock_raw)
    except (UnicodeDecodeError, campaign_lock_codec.CampaignLockCodecError) as exc:
        raise RuntimeError("reference campaign lock is invalid") from exc
    if not decoded_lock.is_v2:
        raise RuntimeError("reference campaign lock schema mismatch")
    identity_preimage = decoded_lock.identity_preimage
    identity = decoded_lock.identity
    search = identity.get("search_config")
    if (
        type(search) is not dict
        or search.get("workload") != WORKLOAD
        or search.get("ycsb") != dict(WORKLOAD_BY_TAG[WORKLOAD])
        or search.get("records") != p2_2.RECORDS
        or search.get("threads") != p2_2.THREADS
        or search.get("sweep_us") != list(EXPECTED_FIXED_GRID)
        or identity.get("ccbench_commit") != pin.CURRENT_PIN
    ):
        raise RuntimeError("reference campaign lock workload/runtime/grid mismatch")

    raw_records, wal_records = _load_wal_snapshot(artifact_snapshots[wal_rel])
    with tempfile.TemporaryDirectory(prefix="izanagi_t1941_reference_snapshot_") as temporary:
        snapshot_root = Path(temporary)
        _materialize_artifact_snapshot(snapshot_root, artifact_snapshots)
        records = _reference_records(
            snapshot_root / "campaigns" / campaign_id,
            campaign_lock_value,
            decoded_lock,
            wal_records,
        )
    states = wal.replay_admitted_records(records)
    committed: dict[str, tuple[str, object]] = {}
    for variant, state in states.items():
        if not state.committed:
            continue
        start = state.committed_build_start
        verifies = state.committed_verify
        if start is None or not verifies or not all(
                record.payload.get("certified") is True for record in verifies):
            raise RuntimeError(f"reference variant is not attempt-bound certified: {variant}")
        canonical = start.payload.get("genome")
        _protocol, parsed = _parse_genome(canonical)
        if DIAGNOSTIC_FLAG in parsed:
            raise RuntimeError("reference genome unexpectedly contains the diagnostic flag")
        if canonical in committed:
            raise RuntimeError(f"duplicate committed reference genome: {canonical}")
        committed[canonical] = (variant, state)
    expected_genomes = {genome.canonical() for genome in genomes(WORKLOAD)}
    if set(committed) != expected_genomes:
        raise RuntimeError(
            f"reference committed genome set mismatch: "
            f"missing={sorted(expected_genomes - set(committed))!r}, "
            f"extra={sorted(set(committed) - expected_genomes)!r}"
        )

    adaptive = [
        genome for genome in genomes(WORKLOAD)
        if genome.flags.get("BACK_OFF") == 1
        and genome.flags.get("BACKOFF_FIXED") == -1
    ]
    if len(adaptive) != 1:
        raise RuntimeError("balanced reference does not define one adaptive point")
    reference_genome = adaptive[0]
    variant, _state = committed[reference_genome.canonical()]
    variant_records = [record for record in raw_records if record.get("variant") == variant]
    start = _unique_stage(variant_records, "build_start")
    done = _unique_stage(variant_records, "build_done")
    verify = _unique_stage(variant_records, "verify_done")
    bench = _unique_stage(variant_records, "bench_done")
    commit = _unique_stage(variant_records, "commit")
    attempt_id = start.get("payload", {}).get("build_attempt_id")
    if type(attempt_id) is not str or not attempt_id:
        raise RuntimeError("reference adaptive attempt identity is missing")
    for record in (done, verify, bench, commit):
        if record.get("payload", {}).get("build_attempt_id") != attempt_id:
            raise RuntimeError("reference adaptive records are not attempt-bound")
    if verify.get("payload", {}).get("certified") is not True:
        raise RuntimeError("reference adaptive verify is not certified")
    commit_receipt = commit.get("payload", {}).get("commit_verification_receipt")
    if (
        type(commit_receipt) is not dict
        or commit_receipt.get("operation_identity") != attempt_id
        or commit_receipt.get("variant") != variant
        or type(commit_receipt.get("receipt_id")) is not str
    ):
        raise RuntimeError("reference adaptive commit verification identity mismatch")
    reference_binary_sha256 = done.get("payload", {}).get("perf_bin_sha256")
    if type(reference_binary_sha256) is not str or _SHA256_RE.fullmatch(
            reference_binary_sha256) is None:
        raise RuntimeError("reference adaptive binary SHA is invalid")

    runtime_manifest_rel = [
        relative for relative in artifact_sha256
        if relative.endswith("/b10-backoff-overthrottle-balanced.manifest.json")
    ]
    if len(runtime_manifest_rel) != 1:
        raise RuntimeError("reference runtime manifest is not unique")
    runtime_manifest = _decode_json_object(
        artifact_snapshots[runtime_manifest_rel[0]],
        root / runtime_manifest_rel[0],
    )
    runtime_contract = runtime_manifest.get("runtime_contract")
    if (
        runtime_manifest.get("campaign_id") != campaign_id
        or runtime_manifest.get("workload") != WORKLOAD
        or runtime_manifest.get("workload_coordinates") != dict(WORKLOAD_BY_TAG[WORKLOAD])
        or type(runtime_contract) is not dict
    ):
        raise RuntimeError("reference runtime manifest binding mismatch")
    run_binary, runtime_flags = _runtime_invocation(
        bench.get("payload", {}).get("run_cmd"),
        expected_numactl=runtime_contract.get("numactl"),
    )
    reference_binary_binding = _require_reference_binary_binding(
        done.get("payload"), run_binary,
    )
    if (
        runtime_flags["thread_num"] != str(runtime_contract.get("threads"))
        or runtime_flags["ycsb_tuple_num"] != str(runtime_contract.get("records"))
        or runtime_flags["clocks_per_us"] != str(runtime_contract.get("clocks_per_us"))
        or runtime_flags["extime"] != str(EXTIME)
        or any(runtime_flags[key] != value for key, value in WORKLOAD_BY_TAG[WORKLOAD].items())
        or commit.get("payload", {}).get("contract_sha256")
        != runtime_contract.get("contract_sha256")
    ):
        raise RuntimeError("reference adaptive full runtime flags mismatch")

    grid_projection = _grid_projection(tuple(committed))
    if (
        _sha256_file(completion_path) != _sha256_bytes(completion_raw)
        or _verify_completion_artifacts(root, completion) != artifact_sha256
    ):
        raise RuntimeError("reference artifact set changed during binding validation")

    return {
        "reference_root": str(root),
        "completion_sha256": _sha256_bytes(completion_raw),
        "artifact_sha256": artifact_sha256,
        "campaign_id": campaign_id,
        "campaign_identity_sha256": _sha256_bytes(identity_preimage.encode("utf-8")),
        "campaign_lock_sha256": artifact_sha256[lock_rel],
        "wal_sha256": artifact_sha256[wal_rel],
        "runtime_manifest_sha256": artifact_sha256[runtime_manifest_rel[0]],
        "reference_variant_id": variant,
        "reference_genome": reference_genome.canonical(),
        "reference_diagnostic_flag": {
            "present_in_genome": False,
            "effective_value": 0,
        },
        "build_attempt_id": attempt_id,
        "verify_record_sha256": _record_sha256(verify),
        "commit_verification_receipt_id": commit_receipt["receipt_id"],
        "reference_binary_sha256": reference_binary_sha256,
        "reference_binary_binding": reference_binary_binding,
        "reference_source_evidence": start["payload"]["build_admission"]["source"],
        "workload_coordinates": dict(WORKLOAD_BY_TAG[WORKLOAD]),
        "runtime_flags": runtime_flags,
        "runtime_contract": runtime_contract,
        **grid_projection,
    }


def _require_uint64_fields(parsed: Mapping[str, int]) -> None:
    for field in FIELD_NAMES:
        value = parsed.get(field)
        if type(value) is not int or not 0 <= value <= UINT64_MAX:
            raise RuntimeError(f"diagnostic field is outside uint64: {field}")


def parse_diagnostic_stdout(stdout: str) -> dict[str, int | bool]:
    """Parse exactly one diagnostic prefix line without touching normal metrics."""
    if type(stdout) is not str:
        raise RuntimeError("diagnostic stdout must be an exact string")
    lines = [line for line in stdout.splitlines() if line.startswith(PREFIX)]
    if len(lines) != 1:
        raise RuntimeError(f"diagnostic prefix line count mismatch: {len(lines)}")
    tokens = lines[0].split()
    if tokens[:1] != [PREFIX]:
        raise RuntimeError("diagnostic prefix token mismatch")
    parsed: dict[str, int] = {}
    for token in tokens[1:]:
        if token.count("=") != 1:
            raise RuntimeError(f"malformed diagnostic field: {token!r}")
        key, raw = token.split("=", 1)
        if key in parsed:
            raise RuntimeError(f"duplicate diagnostic field: {key}")
        if not raw.isascii() or not raw.isdecimal():
            raise RuntimeError(f"non-integer diagnostic field: {key}")
        parsed[key] = int(raw)
    if set(parsed) != set(FIELD_NAMES):
        raise RuntimeError(
            f"diagnostic field set mismatch: missing={sorted(set(FIELD_NAMES) - set(parsed))!r}, "
            f"extra={sorted(set(parsed) - set(FIELD_NAMES))!r}"
        )
    _require_uint64_fields(parsed)
    if parsed["counter_overflowed"] not in {0, 1}:
        raise RuntimeError("counter_overflowed must be 0 or 1")
    if parsed["unknown_state_call_count"] != 0:
        raise RuntimeError("unknown requested-us state observed")
    if parsed["counter_overflowed"] != 0:
        raise RuntimeError("requested-us counter overflow observed")
    bucket_sum = sum(parsed[f"state_{state}_call_count"] for state in D1106_STATES)
    weighted_sum = sum(
        state * parsed[f"state_{state}_call_count"] for state in D1106_STATES
    )
    if parsed["call_count"] <= 0 or parsed["call_count"] != bucket_sum:
        raise RuntimeError("requested-us call/bucket invariant failed")
    if parsed["requested_us_sum"] != weighted_sum:
        raise RuntimeError("requested-us weighted-sum invariant failed")
    result: dict[str, int | bool] = dict(parsed)
    result["counter_overflowed"] = False
    return result


def usage_eligibility() -> dict[str, bool]:
    return {key: False for key in USAGE_ELIGIBILITY_KEYS}


def validate_usage_eligibility(value: object) -> None:
    if type(value) is not dict or set(value) != set(USAGE_ELIGIBILITY_KEYS):
        raise RuntimeError("diagnostic usage eligibility key set mismatch")
    if any(item is not False for item in value.values()):
        raise RuntimeError("diagnostic value is ineligible for all four performance uses")


def _value(value: int | bool) -> dict[str, object]:
    return {
        "value": value,
        "source_measurement": SOURCE_MEASUREMENT,
        "certified": False,
        "diagnostic_only": True,
    }


def _flags(workload: Mapping[str, str], contract) -> list[str]:
    return [
        f"-thread_num={p2_2.THREADS}",
        f"-ycsb_tuple_num={p2_2.RECORDS}",
        f"-extime={EXTIME}",
        f"-clocks_per_us={contract.clocks_per_us}",
        *[f"-{key}={value}" for key, value in workload.items()],
    ]


def _flag_mapping(flags: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in flags:
        if not token.startswith("-") or token.count("=") != 1:
            raise RuntimeError(f"invalid diagnostic runtime flag: {token!r}")
        key, value = token[1:].split("=", 1)
        if key in result:
            raise RuntimeError(f"duplicate diagnostic runtime flag: {key}")
        result[key] = value
    return result


def _require_runtime_match(binding: Mapping[str, object], contract, toolchain: object) -> list[str]:
    flags = _flags(WORKLOAD_BY_TAG[WORKLOAD], contract)
    reference_contract = binding["runtime_contract"]
    if (
        type(reference_contract) is not dict
        or contract.env_tag != reference_contract.get("env_tag")
        or contract.contract_sha256 != reference_contract.get("contract_sha256")
        or contract.clocks_per_us != reference_contract.get("clocks_per_us")
        or list(contract.numactl) != reference_contract.get("numactl")
        or toolchain != reference_contract.get("toolchain_manifest")
        or _flag_mapping(flags) != binding.get("runtime_flags")
    ):
        raise RuntimeError("diagnostic runtime/toolchain differs from certified reference")
    return flags


def _require_fixed_source_match(
        reference_receipt: object, fixed_evidence: source_digest.SourceEvidence,
) -> None:
    try:
        reference = source_digest.SourceEvidence.from_receipt(reference_receipt)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("certified reference source evidence is invalid") from exc
    if type(fixed_evidence) is not source_digest.SourceEvidence:
        raise RuntimeError("fixed-only source evidence is not exact SourceEvidence")
    reference_body = reference.as_receipt()
    fixed_body = fixed_evidence.as_receipt()
    # Frozen and diagnostic runs necessarily use different checkout roots.  All
    # content, commit, genome, token, diff, and tracked-path fields remain exact.
    reference_body.pop("source_root")
    fixed_body.pop("source_root")
    if fixed_body != reference_body:
        raise RuntimeError("fixed-only source differs from certified reference")


def _run_rep(
        binary: str, flags: list[str], numactl: list[str], *, timeout_s: int,
) -> str:
    """Return raw stdout; do not pass it through the normal metric parser."""
    with bench_lock():
        p2_2._assert_single_tenant()
        completed = subprocess.run(
            [*numactl, binary, *flags],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"diagnostic binary failed with rc={completed.returncode}")
    return completed.stdout


class _OutputBoundary:
    def __init__(
            self, reference: Path, diagnostic: Path, parent: Path,
            parent_fd: int,
    ) -> None:
        self.reference = reference
        self.diagnostic = diagnostic
        self.parent = parent
        self.parent_fd = parent_fd
        info = os.fstat(parent_fd)
        self.parent_identity = (info.st_dev, info.st_ino)

    def close(self) -> None:
        if self.parent_fd >= 0:
            descriptor, self.parent_fd = self.parent_fd, -1
            os.close(descriptor)

    def __del__(self) -> None:  # pragma: no cover - error-path descriptor safety net
        try:
            self.close()
        except OSError:
            pass

    def _require_parent_unchanged(self) -> None:
        try:
            info = os.stat(self.parent, follow_symlinks=False)
        except OSError as exc:
            raise RuntimeError("diagnostic output parent changed before publish") from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or (info.st_dev, info.st_ino) != self.parent_identity
        ):
            raise RuntimeError("diagnostic output parent changed before publish")

    def publish(self, rep: object, manifest: object) -> None:
        self._require_parent_unchanged()
        os.mkdir(self.diagnostic.name, 0o700, dir_fd=self.parent_fd)
        flags = (
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        )
        root_fd = os.open(self.diagnostic.name, flags, dir_fd=self.parent_fd)
        try:
            if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
                raise RuntimeError("diagnostic output root is not a real directory")
            _write_create_only_at(root_fd, "rep-000.json", rep)
            _write_create_only_at(root_fd, "manifest.json", manifest)
            os.fsync(root_fd)
        finally:
            os.close(root_fd)
        self._require_parent_unchanged()
        os.fsync(self.parent_fd)


def _assert_output_boundary(reference_root: str, diagnostic_root: str) -> tuple[Path, Path]:
    reference = Path(reference_root).resolve(strict=True)
    diagnostic = Path(diagnostic_root).resolve(strict=False)
    if diagnostic.exists():
        raise FileExistsError(f"diagnostic root already exists: {diagnostic}")
    try:
        diagnostic.relative_to(reference)
    except ValueError:
        pass
    else:
        raise RuntimeError("diagnostic root must not be inside the reference root")
    try:
        reference.relative_to(diagnostic)
    except ValueError:
        pass
    else:
        raise RuntimeError("reference root must not be inside the diagnostic root")
    if not diagnostic.parent.is_dir() or diagnostic.parent.is_symlink():
        raise RuntimeError("diagnostic root parent must be an existing real directory")
    return reference, diagnostic


def _open_output_boundary(reference_root: str, diagnostic_root: str) -> _OutputBoundary:
    reference, diagnostic = _assert_output_boundary(reference_root, diagnostic_root)
    lexical = Path(os.path.abspath(diagnostic_root))
    if lexical.name in {"", ".", ".."} or lexical != diagnostic:
        raise RuntimeError("diagnostic root must have one stable real parent")
    flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        parent_fd = os.open(lexical.parent, flags)
    except OSError as exc:
        raise RuntimeError("diagnostic root parent cannot be opened safely") from exc
    try:
        info = os.fstat(parent_fd)
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("diagnostic root parent is not a real directory")
        return _OutputBoundary(reference, diagnostic, lexical.parent, parent_fd)
    except BaseException:
        os.close(parent_fd)
        raise


def measure(
        *, reference_root: str, diagnostic_root: str, cache_root: str,
        ccbench_dir: Optional[str] = None, log=print,
        binding_loader=load_reference_binding, run_rep=_run_rep,
        build_timeout_s: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
        record_timeout_s: int = DEFAULT_RECORD_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Build and run the one balanced adaptive diagnostic rep."""
    output_boundary = _open_output_boundary(
        reference_root, diagnostic_root,
    )
    reference_path = output_boundary.reference
    diagnostic_path = output_boundary.diagnostic
    for label, value in (
        ("build_timeout_s", build_timeout_s),
        ("record_timeout_s", record_timeout_s),
    ):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{label} must be a positive exact integer")
    binding = binding_loader(str(reference_path))
    if binding.get("reference_root") != str(reference_path):
        raise RuntimeError("reference binding root mismatch")
    base_ccbench_dir = _resolve_ccbench_dir(ccbench_dir)
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
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    toolchain_manifest = buildcache.observed_toolchain_manifest(resolved_cc, resolved_cxx)
    flags = _require_runtime_match(binding, contract, toolchain_manifest)

    protocol, reference_flags = _parse_genome(binding["reference_genome"])
    if protocol != "silo" or DIAGNOSTIC_FLAG in reference_flags:
        raise RuntimeError("diagnostic reference genome is not stock-flag Silo adaptive")
    fixed_genome = Genome(protocol, reference_flags)
    diagnostic_genome = Genome(
        protocol,
        {**reference_flags, DIAGNOSTIC_FLAG: 1},
    )
    fixed_patch = Path(_repo_root()) / TEMPLATE_PATCH
    diagnostic_patch = Path(_repo_root()) / PATCH_REL
    fixed_patch_sha256 = _sha256_file(fixed_patch)
    diagnostic_patch_sha256 = _sha256_file(diagnostic_patch)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_REQUESTED_US)
    with patchharness.checkout(
            pin.CURRENT_PIN, base_dir=base_ccbench_dir,
    ) as isolated_ccbench:
        fixed_files = patchharness.patch_files(
            str(fixed_patch), isolated_ccbench,
        )
        diagnostic_files = patchharness.patch_files(
            str(diagnostic_patch), isolated_ccbench,
        )
        touched_files = sorted(set(fixed_files) | set(diagnostic_files))
        try:
            patchharness.apply_patch(str(fixed_patch), isolated_ccbench)
            _assert_backoff_fixed_materialized(isolated_ccbench)
            fixed_evidence = source_digest.resolve_evidence(
                fixed_genome,
                pin.CURRENT_PIN,
                ccbench_dir=isolated_ccbench,
                cxx=resolved_cxx,
            )
            _require_fixed_source_match(
                binding.get("reference_source_evidence"), fixed_evidence,
            )

            patchharness.apply_patch(str(diagnostic_patch), isolated_ccbench)
            _assert_backoff_fixed_materialized(isolated_ccbench)
            evidence = source_digest.resolve_evidence(
                diagnostic_genome,
                pin.CURRENT_PIN,
                ccbench_dir=isolated_ccbench,
                cxx=resolved_cxx,
            )
            generator_input = {
                "schema": "backoff-requested-us-generator-input/v1",
                "fixed_patch_sha256": fixed_patch_sha256,
                "diagnostic_patch_sha256": diagnostic_patch_sha256,
                "genome": diagnostic_genome.canonical(),
            }
            generator_receipt = attest_generator_output(
                build_context,
                evidence,
                generator_input_sha256=_sha256_bytes(
                    _canonical_json_bytes(generator_input)
                ),
            )
            admission = derive_build_admission(
                build_context,
                evidence,
                generator_receipt=generator_receipt,
            )
            built = buildcache.build_v2(
                diagnostic_genome,
                contract=contract,
                ccbench_commit=pin.CURRENT_PIN,
                trace=False,
                src_token=evidence.src_token,
                cc=resolved_cc,
                cxx=resolved_cxx,
                cache_root=cache_root,
                ccbench_dir=isolated_ccbench,
                admission=admission,
                build_context=build_context,
                source_evidence=evidence,
                expected_toolchain_manifest=toolchain_manifest,
                declared_use_class=DIAGNOSTIC_USE_CLASS,
                timeout_s=build_timeout_s,
            )
            stdout = run_rep(
                built.binary, flags, list(contract.numactl),
                timeout_s=record_timeout_s,
            )
            counters = parse_diagnostic_stdout(stdout)
        finally:
            patchharness.revert_worktree(isolated_ccbench, touched_files)

    completion, completion_raw = _read_json_object(reference_path / "completion.json")
    if (
        _sha256_bytes(completion_raw) != binding["completion_sha256"]
        or _verify_completion_artifacts(reference_path, completion)
        != binding["artifact_sha256"]
    ):
        raise RuntimeError("reference artifact set changed during diagnostic measurement")

    values = {field: _value(counters[field]) for field in FIELD_NAMES}
    rep = {
        "schema_version": REP_SCHEMA,
        "workload": WORKLOAD,
        "rep": 0,
        "reference_campaign_id": binding["campaign_id"],
        "reference_variant_id": binding["reference_variant_id"],
        "reference_genome": binding["reference_genome"],
        "diagnostic_genome": diagnostic_genome.canonical(),
        "certified": False,
        "diagnostic_only": True,
        "values": values,
    }
    eligibility = usage_eligibility()
    validate_usage_eligibility(eligibility)
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "complete",
        "workload": WORKLOAD,
        "workload_coordinates": binding["workload_coordinates"],
        "record_count": REPS,
        "record_file": "rep-000.json",
        "records_sha256": _sha256_bytes(_canonical_json_bytes(rep)),
        "certified": False,
        "diagnostic_only": True,
        "usage_eligibility": eligibility,
        "reference": binding,
        "runtime_contract": {
            "env_tag": contract.env_tag,
            "contract_sha256": contract.contract_sha256,
            "clocks_per_us": contract.clocks_per_us,
            "numactl": list(contract.numactl),
            "records": p2_2.RECORDS,
            "threads": p2_2.THREADS,
            "extime": EXTIME,
            "flags": _flag_mapping(flags),
            "ccbench_commit": pin.CURRENT_PIN,
            "toolchain_manifest": toolchain_manifest,
            "execution_receipt": execution_receipt,
            "calibration": {
                "schema_version": verified_for_manifest.schema_version,
                "sha256": verified_for_manifest.sha256,
                "attestation_profile_sha256": (
                    verified_for_manifest.attestation_profile_sha256
                ),
            },
        },
        "diagnostic_build": {
            "declared_use_class": DIAGNOSTIC_USE_CLASS,
            "trace_flag": 0,
            "diagnostic_flag": 1,
            "fixed_patch_sha256": fixed_patch_sha256,
            "diagnostic_patch_sha256": diagnostic_patch_sha256,
            "source_evidence": evidence.as_receipt(),
            "binary_sha256": built.bin_sha256,
        },
    }
    try:
        output_boundary.publish(rep, manifest)
    finally:
        output_boundary.close()
    log(f"[{WORKLOAD}] requested-us diagnostic rep=0 manifest={diagnostic_path / 'manifest.json'}")
    return {"rep": rep, "manifest": manifest, "root": str(diagnostic_path)}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--diagnostic-root", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--ccbench-dir")
    parser.add_argument(
        "-" * 2 + "build-timeout-seconds", type=int,
        default=DEFAULT_BUILD_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--record-timeout-seconds", type=int,
        default=DEFAULT_RECORD_TIMEOUT_SECONDS,
    )
    args = parser.parse_args(argv)
    result = measure(
        reference_root=args.reference_root,
        diagnostic_root=args.diagnostic_root,
        cache_root=args.cache_root,
        ccbench_dir=args.ccbench_dir,
        build_timeout_s=args.build_timeout_seconds,
        record_timeout_s=args.record_timeout_seconds,
    )
    print(f"balanced: 1 diagnostic rep, root={result['root']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
