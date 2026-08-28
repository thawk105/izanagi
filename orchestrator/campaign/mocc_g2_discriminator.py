#!/usr/bin/env python3
"""T-1943 fixed-cell MoCC payload-lineage discriminator.

This tool does not replace or extend the verifier.  It consumes one completed
verifier JSON document plus separately hashed standard-trace and payload-witness
manifests.  Its narrow conclusion only says whether the payload producer seen
by each reported G2 rw reason agrees with the producer implied by the standard
trace's reader version.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Iterable


SCHEMA_VERSION = "mocc-g2-payload-discriminator/v1"
TRACE_MANIFEST_SCHEMA = "mocc-g2-standard-trace-manifest/v1"
WITNESS_MANIFEST_SCHEMA = "mocc-g2-payload-witness-manifest/v1"
EXACT_WORKLOAD = {
    "extime_s": 3,
    "records": 10_000,
    "threads": 48,
    "ycsb_max_ope": 10,
    "ycsb_rmw": 0,
    "ycsb_rratio": 50,
    "zipf_skew": 0.9,
}
_HEX_40 = re.compile(r"[0-9a-f]{40}")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_KEY = re.compile(r"(?:[0-9a-f]{2})+")
_TRACE_NAME = re.compile(r"trace_(?:0|[1-9][0-9]*)[.]log")
_WITNESS_NAME = re.compile(r"witness_(?:0|[1-9][0-9]*)[.]log")
_WITNESS_HEADER = ("H", "IZANAGI_MOCC_G2_WATERMARK_V1", "1")
_TXID_MAX = (1 << 48) - 1


class DiscriminatorError(ValueError):
    """The input is not a completed, strictly bound discriminator input."""


def _exact_workload(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == set(EXACT_WORKLOAD)
        and all(
            type(value[key]) is type(expected) and value[key] == expected
            for key, expected in EXACT_WORKLOAD.items()
        )
    )


def _int(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise DiscriminatorError(f"{label} is not an integer >= {minimum}")
    return value


def _version(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        raise DiscriminatorError(f"{label} is not a two-integer version")
    return (_int(value[0], f"{label}[0]"), _int(value[1], f"{label}[1]"))


def _read_regular_bytes(path: Path, label: str) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise DiscriminatorError(f"{label} is unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise DiscriminatorError(f"{label} is not a regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read()
    finally:
        if fd >= 0:
            os.close(fd)


def _load_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiscriminatorError(f"{label} is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise DiscriminatorError(f"{label} is not a JSON object")
    return value


def _load_json(path: Path, label: str) -> tuple[dict[str, Any], str]:
    raw = _read_regular_bytes(path, label)
    return _load_json_bytes(raw, label), hashlib.sha256(raw).hexdigest()


def _validate_manifest(
    path: Path,
    *,
    schema: str,
    kind: str,
    name_pattern: re.Pattern[str],
) -> tuple[dict[str, Any], str, list[tuple[str, bytes]]]:
    manifest, manifest_sha = _load_json(path, f"{kind} manifest")
    expected_keys = {
        "artifact_kind",
        "binary_sha256",
        "files",
        "root_dir",
        "schema_version",
        "source_oid",
        "workload",
    }
    if set(manifest) != expected_keys:
        raise DiscriminatorError(f"{kind} manifest shape differs")
    if manifest["schema_version"] != schema:
        raise DiscriminatorError(f"{kind} manifest schema differs")
    if manifest["artifact_kind"] != kind:
        raise DiscriminatorError(f"{kind} manifest artifact kind differs")
    if not _exact_workload(manifest["workload"]):
        raise DiscriminatorError(f"{kind} manifest workload is outside T-1943")
    source_oid = manifest["source_oid"]
    binary_sha = manifest["binary_sha256"]
    if not isinstance(source_oid, str) or _HEX_40.fullmatch(source_oid) is None:
        raise DiscriminatorError(f"{kind} manifest source OID is invalid")
    if not isinstance(binary_sha, str) or _HEX_64.fullmatch(binary_sha) is None:
        raise DiscriminatorError(f"{kind} manifest binary digest is invalid")
    root_text = manifest["root_dir"]
    if not isinstance(root_text, str) or not os.path.isabs(root_text):
        raise DiscriminatorError(f"{kind} manifest root is not absolute")
    root = Path(root_text)
    try:
        root_info = root.stat(follow_symlinks=False)
    except OSError as exc:
        raise DiscriminatorError(f"{kind} manifest root is unavailable") from exc
    if not stat.S_ISDIR(root_info.st_mode) or root.is_symlink():
        raise DiscriminatorError(f"{kind} manifest root is not a real directory")

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise DiscriminatorError(f"{kind} manifest has no files")
    observed_names: set[str] = set()
    bound: list[tuple[str, bytes]] = []
    for index, entry in enumerate(files):
        if not isinstance(entry, dict) or set(entry) != {
            "name", "sha256", "size_bytes"
        }:
            raise DiscriminatorError(f"{kind} manifest file[{index}] shape differs")
        name = entry["name"]
        digest = entry["sha256"]
        size = entry["size_bytes"]
        if not isinstance(name, str) or name_pattern.fullmatch(name) is None:
            raise DiscriminatorError(f"{kind} manifest file name is invalid")
        thread_text = name.removeprefix(
            "trace_" if kind == "standard-trace" else "witness_"
        ).removesuffix(".log")
        if int(thread_text) >= EXACT_WORKLOAD["threads"]:
            raise DiscriminatorError(f"{kind} manifest thread id is outside workload")
        if name in observed_names:
            raise DiscriminatorError(f"{kind} manifest file name is duplicated")
        observed_names.add(name)
        if not isinstance(digest, str) or _HEX_64.fullmatch(digest) is None:
            raise DiscriminatorError(f"{kind} manifest file digest is invalid")
        _int(size, f"{kind} manifest file size")
        raw = _read_regular_bytes(root / name, f"{kind} file {name}")
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise DiscriminatorError(f"{kind} file {name} changed after manifest")
        bound.append((name, raw))
    actual_names: set[str] = set()
    for candidate in root.iterdir():
        try:
            candidate_info = candidate.stat(follow_symlinks=False)
        except OSError as exc:
            raise DiscriminatorError(f"{kind} root entry is unavailable") from exc
        if not stat.S_ISREG(candidate_info.st_mode):
            raise DiscriminatorError(f"{kind} root contains a non-regular entry")
        if name_pattern.fullmatch(candidate.name) is None:
            raise DiscriminatorError(f"{kind} root contains an unexpected file name")
        actual_names.add(candidate.name)
    if actual_names != observed_names:
        raise DiscriminatorError(f"{kind} manifest file set differs from root")
    return manifest, manifest_sha, bound


def _parse_uint(token: str, label: str) -> int:
    if not token.isascii() or not token.isdigit():
        raise DiscriminatorError(f"{label} is not an unsigned decimal integer")
    return int(token)


def _parse_txid(token: str, label: str) -> int:
    value = _parse_uint(token, label)
    if value > _TXID_MAX:
        raise DiscriminatorError(f"{label} exceeds the payload watermark range")
    return value


def _txid(value: Any, label: str) -> int:
    parsed = _int(value, label)
    if parsed > _TXID_MAX:
        raise DiscriminatorError(f"{label} exceeds the payload watermark range")
    return parsed


def _parse_key(token: str, label: str) -> str:
    if _KEY.fullmatch(token) is None:
        raise DiscriminatorError(f"{label} is not lowercase even-length hex")
    return token


def _ascii_lines(raw: bytes, label: str) -> Iterable[tuple[int, list[str]]]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise DiscriminatorError(f"{label} is not ASCII") from exc
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line or line != line.strip() or "\t" in line or "  " in line:
            raise DiscriminatorError(f"{label}:{line_number} has invalid framing")
        yield line_number, line.split(" ")


def _parse_standard_trace(
    files: list[tuple[str, bytes]],
) -> tuple[
    dict[int, tuple[int, int]],
    Counter[tuple[int, str, tuple[int, int]]],
    Counter[tuple[int, str, tuple[int, int]]],
    dict[tuple[str, tuple[int, int]], list[int]],
    list[str],
]:
    commits: dict[int, tuple[int, int]] = {}
    reads: Counter[tuple[int, str, tuple[int, int]]] = Counter()
    writes: Counter[tuple[int, str, tuple[int, int]]] = Counter()
    producers: dict[tuple[str, tuple[int, int]], list[int]] = defaultdict(list)
    blockers: list[str] = []
    for name, raw in files:
        file_thread = int(name.removeprefix("trace_").removesuffix(".log"))
        current: tuple[int, tuple[int, int], int, int] | None = None
        observed_reads = observed_writes = 0
        for line_number, tokens in _ascii_lines(raw, name):
            record = tokens[0]
            if record == "C" and len(tokens) == 7:
                if current is not None:
                    blockers.append("standard-trace-nested-frame")
                txid = _parse_txid(tokens[1], f"{name}:{line_number} txid")
                thread = _parse_uint(tokens[2], f"{name}:{line_number} thread")
                if thread != file_thread:
                    blockers.append("standard-trace-thread-identity-collision")
                version = (
                    _parse_uint(tokens[3], f"{name}:{line_number} epoch"),
                    _parse_uint(tokens[4], f"{name}:{line_number} tid"),
                )
                expected_reads = _parse_uint(
                    tokens[5], f"{name}:{line_number} read count"
                )
                expected_writes = _parse_uint(
                    tokens[6], f"{name}:{line_number} write count"
                )
                if txid in commits:
                    blockers.append("standard-trace-duplicate-txid")
                else:
                    commits[txid] = version
                current = (txid, version, expected_reads, expected_writes)
                observed_reads = observed_writes = 0
            elif record == "R" and len(tokens) == 5 and current is not None:
                txid = _parse_txid(tokens[1], f"{name}:{line_number} txid")
                if txid != current[0]:
                    blockers.append("standard-trace-frame-identity-collision")
                key = _parse_key(tokens[2], f"{name}:{line_number} key")
                version = (
                    _parse_uint(tokens[3], f"{name}:{line_number} epoch"),
                    _parse_uint(tokens[4], f"{name}:{line_number} tid"),
                )
                reads[(txid, key, version)] += 1
                observed_reads += 1
            elif record == "W" and len(tokens) == 6 and current is not None:
                txid = _parse_txid(tokens[1], f"{name}:{line_number} txid")
                if txid != current[0]:
                    blockers.append("standard-trace-frame-identity-collision")
                key = _parse_key(tokens[2], f"{name}:{line_number} key")
                if tokens[3] != "U":
                    blockers.append("standard-trace-non-update-write")
                version = (
                    _parse_uint(tokens[4], f"{name}:{line_number} epoch"),
                    _parse_uint(tokens[5], f"{name}:{line_number} tid"),
                )
                writes[(txid, key, version)] += 1
                producers[(key, version)].append(txid)
                if version != current[1]:
                    blockers.append("standard-trace-write-version-mismatch")
                observed_writes += 1
            elif record == "E" and len(tokens) == 2 and current is not None:
                txid = _parse_txid(tokens[1], f"{name}:{line_number} txid")
                if txid != current[0]:
                    blockers.append("standard-trace-frame-identity-collision")
                if (observed_reads, observed_writes) != (current[2], current[3]):
                    blockers.append("standard-trace-frame-count-mismatch")
                current = None
            else:
                raise DiscriminatorError(
                    f"{name}:{line_number} is outside the fixed standard trace grammar"
                )
        if current is not None:
            blockers.append("standard-trace-missing-end")
    if not commits:
        blockers.append("standard-trace-empty")
    if any(count != 1 for count in reads.values()):
        blockers.append("standard-trace-duplicate-read-identity")
    if any(count != 1 for count in writes.values()):
        blockers.append("standard-trace-duplicate-write-identity")
    if any(len(values) != 1 for values in producers.values()):
        blockers.append("standard-trace-producer-identity-collision")
    return commits, reads, writes, producers, blockers


def _parse_witness(
    files: list[tuple[str, bytes]],
) -> tuple[
    dict[tuple[int, str, tuple[int, int]], str],
    Counter[tuple[int, str, tuple[int, int]]],
    list[str],
]:
    lineage: dict[tuple[int, str, tuple[int, int]], str] = {}
    stores: Counter[tuple[int, str, tuple[int, int]]] = Counter()
    blockers: list[str] = []
    for name, raw in files:
        header_seen = False
        for line_number, tokens in _ascii_lines(raw, name):
            if tuple(tokens) == _WITNESS_HEADER and not header_seen:
                header_seen = True
                continue
            if not header_seen:
                raise DiscriminatorError(f"{name}:{line_number} precedes witness header")
            if tokens[0] == "L" and len(tokens) == 7:
                txid = _parse_txid(tokens[1], f"{name}:{line_number} txid")
                key = _parse_key(tokens[2], f"{name}:{line_number} key")
                version = (
                    _parse_uint(tokens[3], f"{name}:{line_number} epoch"),
                    _parse_uint(tokens[4], f"{name}:{line_number} tid"),
                )
                kind, producer = tokens[5], tokens[6]
                if (kind, producer) == ("G", "-"):
                    token = "genesis"
                elif kind == "T":
                    token = str(
                        _parse_txid(producer, f"{name}:{line_number} producer")
                    )
                else:
                    raise DiscriminatorError(f"{name}:{line_number} lineage token differs")
                identity = (txid, key, version)
                if identity in lineage:
                    blockers.append("witness-duplicate-lineage")
                else:
                    lineage[identity] = token
            elif tokens[0] == "S" and len(tokens) == 6:
                txid = _parse_txid(tokens[1], f"{name}:{line_number} txid")
                key = _parse_key(tokens[2], f"{name}:{line_number} key")
                version = (
                    _parse_uint(tokens[3], f"{name}:{line_number} epoch"),
                    _parse_uint(tokens[4], f"{name}:{line_number} tid"),
                )
                stored = _parse_txid(
                    tokens[5], f"{name}:{line_number} stored producer"
                )
                identity = (txid, key, version)
                stores[identity] += 1
                if stored != txid:
                    blockers.append("witness-post-store-token-mismatch")
            else:
                raise DiscriminatorError(
                    f"{name}:{line_number} is outside the payload witness grammar"
                )
        if not header_seen:
            blockers.append("witness-missing-header")
    if any(count != 1 for count in stores.values()):
        blockers.append("witness-duplicate-store")
    return lineage, stores, blockers


def _validate_verifier(
    verifier: dict[str, Any], trace_root: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if set(verifier) != {
        "certified_serializable",
        "indeterminate",
        "non_serializable",
        "results",
        "runs",
    }:
        raise DiscriminatorError("verifier aggregate shape differs")
    if (
        type(verifier["runs"]) is not int
        or verifier["runs"] != 1
        or not isinstance(verifier["results"], list)
    ):
        raise DiscriminatorError("verifier must contain exactly one run")
    if len(verifier["results"]) != 1:
        raise DiscriminatorError("verifier must contain exactly one result")
    for key in ("certified_serializable", "indeterminate", "non_serializable"):
        _int(verifier[key], f"verifier {key}")
    if sum(verifier[key] for key in (
        "certified_serializable", "indeterminate", "non_serializable"
    )) != 1:
        raise DiscriminatorError("verifier aggregate counters do not total one")
    result = verifier["results"][0]
    if not isinstance(result, dict):
        raise DiscriminatorError("verifier result is not an object")
    required = {
        "anomalies", "anomaly_count", "certified", "integrity",
        "serializable", "stats", "total_cycles", "trace_dir", "verdict",
    }
    if set(result) != required:
        raise DiscriminatorError("verifier result shape differs")
    if result["trace_dir"] != trace_root:
        raise DiscriminatorError("verifier trace_dir differs from trace manifest")
    anomalies = result["anomalies"]
    if not isinstance(anomalies, list):
        raise DiscriminatorError("verifier anomalies is not a list")
    if _int(result["anomaly_count"], "verifier anomaly_count") != len(anomalies):
        raise DiscriminatorError("verifier anomaly_count differs from anomalies")
    _int(result["total_cycles"], "verifier total_cycles")
    if result["verdict"] not in {
        "serializable", "indeterminate", "non-serializable"
    }:
        raise DiscriminatorError("verifier verdict differs")
    if type(result["certified"]) is not bool or type(result["serializable"]) is not bool:
        raise DiscriminatorError("verifier boolean fields differ")
    if not isinstance(result["integrity"], dict):
        raise DiscriminatorError("verifier integrity is not an object")
    if not isinstance(result["stats"], dict):
        raise DiscriminatorError("verifier stats is not an object")
    expected_aggregate = {
        "serializable": (1, 0, 0),
        "indeterminate": (0, 1, 0),
        "non-serializable": (0, 0, 1),
    }[result["verdict"]]
    actual_aggregate = (
        verifier["certified_serializable"],
        verifier["indeterminate"],
        verifier["non_serializable"],
    )
    if actual_aggregate != expected_aggregate:
        raise DiscriminatorError("verifier aggregate contradicts result verdict")
    expected_booleans = {
        "serializable": (True, True),
        "indeterminate": (False, False),
        "non-serializable": (False, False),
    }[result["verdict"]]
    if (result["certified"], result["serializable"]) != expected_booleans:
        raise DiscriminatorError("verifier booleans contradict result verdict")
    if result["verdict"] == "serializable" and (
        anomalies or result["total_cycles"] != 0
    ):
        raise DiscriminatorError("serializable verifier result contains cycles")
    if result["verdict"] == "non-serializable" and not anomalies:
        raise DiscriminatorError("non-serializable verifier result has no anomaly")
    return result, anomalies


def discriminate(
    trace_manifest_path: Path,
    witness_manifest_path: Path,
    verifier_path: Path,
) -> dict[str, Any]:
    trace_manifest, trace_manifest_sha, trace_files = _validate_manifest(
        trace_manifest_path,
        schema=TRACE_MANIFEST_SCHEMA,
        kind="standard-trace",
        name_pattern=_TRACE_NAME,
    )
    witness_manifest, witness_manifest_sha, witness_files = _validate_manifest(
        witness_manifest_path,
        schema=WITNESS_MANIFEST_SCHEMA,
        kind="payload-witness",
        name_pattern=_WITNESS_NAME,
    )
    for field in ("source_oid", "binary_sha256", "workload"):
        if trace_manifest[field] != witness_manifest[field]:
            raise DiscriminatorError(f"manifest {field} bindings differ")
    verifier, verifier_sha = _load_json(verifier_path, "verifier JSON")
    result, anomalies = _validate_verifier(verifier, trace_manifest["root_dir"])

    commits, reads, writes, producers, blockers = _parse_standard_trace(trace_files)
    lineage, stores, witness_blockers = _parse_witness(witness_files)
    blockers.extend(witness_blockers)

    if any(version == (1, 0) for _key, version in producers):
        blockers.append("standard-trace-implicit-genesis-producer-collision")

    if result["integrity"].get("clean") is not True:
        blockers.append("verifier-integrity-dirty")
    if result["verdict"] == "indeterminate":
        blockers.append("verifier-verdict-indeterminate")
    if result["total_cycles"] != len(anomalies):
        blockers.append("verifier-anomaly-list-truncated")
    if Counter(lineage.keys()) != reads:
        blockers.append("witness-lineage-missing-duplicate-or-orphan")
    if stores != writes:
        blockers.append("witness-store-missing-duplicate-or-orphan")

    committed_ids = set(commits)
    writer_keys = {(txid, key) for txid, key, _version_value in writes}
    for (_reader, key, _version_value), token in lineage.items():
        if token == "genesis":
            continue
        producer = int(token)
        if producer not in committed_ids or (producer, key) not in writer_keys:
            blockers.append("witness-producer-orphan")

    reason_identities: Counter[tuple[int, str, tuple[int, int]]] = Counter()
    comparison_inputs: list[
        tuple[int, str, tuple[int, int], str | None]
    ] = []
    for anomaly in anomalies:
        if not isinstance(anomaly, dict) or set(anomaly) != {
            "cycle", "edges", "length", "phenomenon"
        }:
            raise DiscriminatorError("verifier anomaly shape differs")
        if anomaly["phenomenon"] != "G2":
            blockers.append("verifier-non-g2-anomaly")
            continue
        cycle = anomaly["cycle"]
        edges = anomaly["edges"]
        if (
            not isinstance(cycle, list)
            or not isinstance(edges, list)
            or _int(anomaly["length"], "verifier anomaly length", minimum=2)
            != len(cycle)
            or len(edges) != len(cycle)
        ):
            raise DiscriminatorError("verifier G2 cycle shape differs")
        cycle_ids = [
            _txid(value, f"verifier anomaly cycle[{index}]")
            for index, value in enumerate(cycle)
        ]
        if len(set(cycle_ids)) != len(cycle_ids):
            blockers.append("verifier-cycle-identity-collision")
        if any(txid not in committed_ids for txid in cycle_ids):
            blockers.append("verifier-cycle-identity-orphan")
        for edge_index, edge in enumerate(edges):
            if not isinstance(edge, dict) or set(edge) != {
                "from", "reasons", "to", "types"
            }:
                raise DiscriminatorError("verifier edge shape differs")
            reader = _txid(edge["from"], "verifier edge.from")
            overwriter = _txid(edge["to"], "verifier edge.to")
            if reader not in committed_ids or overwriter not in committed_ids:
                blockers.append("verifier-edge-identity-orphan")
            if (
                reader != cycle_ids[edge_index]
                or overwriter != cycle_ids[(edge_index + 1) % len(cycle_ids)]
            ):
                blockers.append("verifier-cycle-edge-projection-mismatch")
            if edge["types"] != ["rw"]:
                blockers.append("verifier-g2-edge-outside-rw-only-shape")
            reasons = edge["reasons"]
            if not isinstance(reasons, list) or not reasons:
                raise DiscriminatorError("verifier edge reasons are absent")
            for reason in reasons:
                if not isinstance(reason, dict) or set(reason) != {
                    "key", "type", "u_ver", "v_ver"
                }:
                    raise DiscriminatorError("verifier rw reason shape differs")
                if reason["type"] != "rw":
                    blockers.append("verifier-g2-reason-outside-rw-shape")
                    continue
                key = _parse_key(reason["key"], "verifier rw reason key")
                read_version = _version(reason["u_ver"], "verifier rw reason u_ver")
                overwrite_version = _version(
                    reason["v_ver"], "verifier rw reason v_ver"
                )
                if producers.get((key, overwrite_version), []) != [overwriter]:
                    blockers.append("rw-reason-overwriter-projection-mismatch")
                identity = (reader, key, read_version)
                reason_identities[identity] += 1
                producer_ids = producers.get((key, read_version), [])
                if read_version == (1, 0):
                    expected = "genesis"
                elif len(producer_ids) == 1:
                    expected = str(producer_ids[0])
                else:
                    expected = None
                    blockers.append("reason-producer-missing-or-colliding")
                comparison_inputs.append((reader, key, read_version, expected))

    if any(count != 1 for count in reason_identities.values()):
        blockers.append("rw-reason-multiplicity-mismatch")
    for identity in reason_identities:
        if reads.get(identity, 0) != 1 or identity not in lineage:
            blockers.append("rw-reason-witness-cardinality-mismatch")

    blockers = sorted(set(blockers))
    comparisons: list[dict[str, Any]] = []
    if blockers:
        conclusion = "indeterminate"
    elif result["total_cycles"] == 0:
        conclusion = "no-g2"
    else:
        comparisons = [
            {
                "reader_txid": reader,
                "key": key,
                "reader_version": list(read_version),
                "expected_payload_producer": expected,
                "observed_payload_producer": lineage[(reader, key, read_version)],
            }
            for reader, key, read_version, expected in comparison_inputs
        ]
        if any(
            item["expected_payload_producer"]
            != item["observed_payload_producer"]
            for item in comparisons
        ):
            conclusion = "contradicted"
        else:
            conclusion = "supported"

    return {
        "schema_version": SCHEMA_VERSION,
        "conclusion": conclusion,
        "meaning": (
            "payload lineage supports the verifier reader-version projection"
            if conclusion == "supported"
            else "payload lineage contradicts the verifier reader-version projection"
            if conclusion == "contradicted"
            else "the completed verifier reported no G2 cycle"
            if conclusion == "no-g2"
            else "input integrity prevents payload-lineage comparison"
        ),
        "blockers": blockers,
        "comparisons": comparisons,
        "bindings": {
            "source_oid": trace_manifest["source_oid"],
            "binary_sha256": trace_manifest["binary_sha256"],
            "workload": dict(EXACT_WORKLOAD),
            "trace_manifest_sha256": trace_manifest_sha,
            "witness_manifest_sha256": witness_manifest_sha,
            "verifier_sha256": verifier_sha,
        },
        "limits": {
            "writer_version_verified": False,
            "write_store_order_verified_beyond_post_store_token": False,
            "commit_order_verified": False,
            "mocc_root_cause_verified": False,
            "serializable_elevation_allowed": False,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-manifest", required=True, type=Path)
    parser.add_argument("--witness-manifest", required=True, type=Path)
    parser.add_argument("--verifier", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = discriminate(
            args.trace_manifest, args.witness_manifest, args.verifier
        )
        output_bytes = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        fd = os.open(
            args.output,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
        with os.fdopen(fd, "wb") as handle:
            handle.write(output_bytes)
    except (DiscriminatorError, FileExistsError, OSError) as exc:
        print(f"mocc_g2_discriminator: {exc}", file=sys.stderr)
        return 2
    print(payload["conclusion"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
