# -*- coding: utf-8 -*-
"""Create-only grammar reinspection ledgers for historical trigger records.

The ledger is deliberately separate from the campaign WAL.  It never upgrades an old record to
a standard attempt and never stores the inspected implementation or a source location.
"""
from __future__ import annotations

import hashlib
import json
import os
from enum import Enum
from typing import Iterable, Mapping

from .model import Genome
from .source_digest import (
    SOURCE_EVIDENCE_SCHEMA_V2,
    TriggerGateSourceError,
    resolve_evidence,
)
from .trigger_gate_language import check_trigger_gate_implementation


REINSPECTION_LEDGER_SCHEMA = "trigger-gate-reinspection/v2"


class ReinspectionError(RuntimeError):
    """A reinspection ledger is unavailable, non-canonical, or already exists."""


class ReinspectionVerdict(str, Enum):
    PASSED = "passed"
    REJECTED = "rejected"
    SOURCE_UNAVAILABLE = "source-unavailable"


def _canonical_bytes(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        )
    except (TypeError, ValueError) as exc:
        raise ReinspectionError("reinspection input を canonical JSON 化できない") from exc
    return rendered.encode("ascii")


def canonical_record_sha256(record: Mapping[str, object]) -> str:
    """Return the full canonical hash used as the only old-record identifier."""

    if not isinstance(record, Mapping):
        raise ReinspectionError("old record は mapping が必要")
    return hashlib.sha256(_canonical_bytes(record)).hexdigest()


def _implementation_values(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "implementation" and type(item) is str:
                found.add(item)
            else:
                found.update(_implementation_values(item))
    elif type(value) is list:
        for item in value:
            found.update(_implementation_values(item))
    return found


def _record_identity(record: Mapping[str, object]) -> tuple[Genome, str] | None:
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return None
    canonical = payload.get("genome")
    src_token = payload.get("src_token")
    if type(canonical) is not str or type(src_token) is not str or "|" not in canonical:
        return None
    protocol, encoded_flags = canonical.split("|", 1)
    flags: dict[str, int] = {}
    try:
        if encoded_flags:
            for assignment in encoded_flags.split(","):
                key, raw = assignment.split("=", 1)
                if not key or key in flags:
                    return None
                flags[key] = int(raw)
        genome = Genome(protocol, flags)
    except (TypeError, ValueError):
        return None
    if genome.canonical() != canonical:
        return None
    return genome, src_token


def reinspect_record(
    record: Mapping[str, object],
    *,
    source_root: str | None = None,
    ccbench_commit: str | None = None,
) -> ReinspectionVerdict:
    """Check record-bound source identity or its embedded verbatim provenance."""

    canonical_record_sha256(record)
    if source_root is not None:
        identity = _record_identity(record)
        if (
            type(source_root) is not str
            or not source_root
            or type(ccbench_commit) is not str
            or not ccbench_commit
            or identity is None
        ):
            return ReinspectionVerdict.SOURCE_UNAVAILABLE
        genome, recorded_src_token = identity
        try:
            evidence = resolve_evidence(
                genome, ccbench_commit, ccbench_dir=source_root,
            )
        except TriggerGateSourceError as exc:
            return (
                ReinspectionVerdict.REJECTED
                if exc.reason_code is not None
                else ReinspectionVerdict.SOURCE_UNAVAILABLE
            )
        except RuntimeError:
            return ReinspectionVerdict.SOURCE_UNAVAILABLE
        if (
            evidence.schema_version != SOURCE_EVIDENCE_SCHEMA_V2
            or evidence.src_token != recorded_src_token
        ):
            return ReinspectionVerdict.REJECTED
        return ReinspectionVerdict.PASSED

    implementations = _implementation_values(record)
    if len(implementations) != 1:
        return ReinspectionVerdict.SOURCE_UNAVAILABLE
    implementation = next(iter(implementations))

    result = check_trigger_gate_implementation(implementation)
    return (
        ReinspectionVerdict.PASSED
        if result.passed
        else ReinspectionVerdict.REJECTED
    )


def _validate_ledger(value: object, *, campaign_id: str | None = None) -> dict[str, object]:
    if type(value) is not dict or set(value) != {
        "schema", "campaign_id", "ccbench_commit", "entries", "evidence",
        "ledger_sha256",
    }:
        raise ReinspectionError("reinspection ledger exact key 集合が不正")
    if value["schema"] != REINSPECTION_LEDGER_SCHEMA:
        raise ReinspectionError("reinspection ledger schema が不正")
    if type(value["campaign_id"]) is not str or not value["campaign_id"]:
        raise ReinspectionError("reinspection ledger campaign_id が不正")
    if campaign_id is not None and value["campaign_id"] != campaign_id:
        raise ReinspectionError("reinspection ledger campaign_id が要求と不一致")
    if value["ccbench_commit"] is not None and (
        type(value["ccbench_commit"]) is not str or not value["ccbench_commit"]
    ):
        raise ReinspectionError("reinspection ledger ccbench_commit が不正")
    entries = value["entries"]
    if type(entries) is not dict:
        raise ReinspectionError("reinspection ledger entries が object でない")
    allowed = {member.value for member in ReinspectionVerdict}
    for digest, verdict in entries.items():
        if (type(digest) is not str or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)):
            raise ReinspectionError("reinspection ledger entry が不正")
        if type(verdict) is not str or verdict not in allowed:
            raise ReinspectionError("reinspection ledger verdict が不正")
    evidence = value["evidence"]
    if type(evidence) is not dict or set(evidence) != set(entries):
        raise ReinspectionError("reinspection ledger evidence 集合が不正")
    for entry in evidence.values():
        if type(entry) is not dict or set(entry) != {"kind", "source_root"}:
            raise ReinspectionError("reinspection ledger evidence shape が不正")
        if entry["kind"] not in {"record-provenance", "record-source"}:
            raise ReinspectionError("reinspection ledger evidence kind が不正")
        if entry["kind"] == "record-source":
            if type(entry["source_root"]) is not str or not entry["source_root"]:
                raise ReinspectionError("reinspection ledger source root が不正")
        elif entry["source_root"] is not None:
            raise ReinspectionError("record provenance entry に source root が混在")
    outer = value["ledger_sha256"]
    if (type(outer) is not str or len(outer) != 64
            or any(ch not in "0123456789abcdef" for ch in outer)):
        raise ReinspectionError("reinspection ledger sha256 が不正")
    unsigned = dict(value)
    unsigned.pop("ledger_sha256")
    if hashlib.sha256(_canonical_bytes(unsigned)).hexdigest() != outer:
        raise ReinspectionError("reinspection ledger canonical sha256 が不一致")
    return json.loads(_canonical_bytes(value).decode("ascii"))


def create_reinspection_ledger(
    path: str,
    *,
    campaign_id: str,
    records: Iterable[Mapping[str, object]],
    record_source_roots: Mapping[str, str] | None = None,
    ccbench_commit: str | None = None,
) -> dict[str, object]:
    """Inspect records and atomically claim one create-only campaign ledger path."""

    if type(campaign_id) is not str or not campaign_id:
        raise ReinspectionError("campaign_id は非空 exact str が必要")
    if record_source_roots is not None and not isinstance(record_source_roots, Mapping):
        raise ReinspectionError("record_source_roots は record hash mapping が必要")
    entries: dict[str, str] = {}
    evidence: dict[str, dict[str, object]] = {}
    for record in records:
        digest = canonical_record_sha256(record)
        source_root = (
            record_source_roots.get(digest) if record_source_roots is not None else None
        )
        verdict = reinspect_record(
            record, source_root=source_root, ccbench_commit=ccbench_commit,
        ).value
        proof = {
            "kind": (
                "record-source" if source_root is not None else "record-provenance"
            ),
            "source_root": source_root,
        }
        previous = entries.get(digest)
        if previous is not None and (
            previous != verdict or evidence[digest] != proof
        ):
            raise ReinspectionError("同じ old record hash の verdict が競合")
        entries[digest] = verdict
        evidence[digest] = proof
    body: dict[str, object] = {
        "schema": REINSPECTION_LEDGER_SCHEMA,
        "campaign_id": campaign_id,
        "ccbench_commit": ccbench_commit,
        "entries": {key: entries[key] for key in sorted(entries)},
        "evidence": {key: evidence[key] for key in sorted(evidence)},
    }
    body["ledger_sha256"] = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    payload = _canonical_bytes(body) + b"\n"
    try:
        with open(path, "xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.path.dirname(os.path.abspath(path))
        directory_fd = os.open(
            directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except FileExistsError as exc:
        raise ReinspectionError("reinspection ledger は create-only で既に存在する") from exc
    except OSError as exc:
        raise ReinspectionError("reinspection ledger を永続化できない") from exc
    return _validate_ledger(body, campaign_id=campaign_id)


def load_reinspection_ledger(
    path: str,
    *,
    campaign_id: str | None = None,
) -> dict[str, object]:
    """Read and verify a detached ledger for artifact-admission consumers."""

    try:
        with open(path, "rb") as handle:
            raw = handle.read()
        value = json.loads(raw.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReinspectionError("reinspection ledger を厳密に読めない") from exc
    if raw != _canonical_bytes(value) + b"\n":
        raise ReinspectionError("reinspection ledger bytes が canonical でない")
    return _validate_ledger(value, campaign_id=campaign_id)


def lookup_reinspection_verdict(
    ledger: Mapping[str, object],
    old_record_sha256: str,
) -> ReinspectionVerdict | None:
    """Return one verified verdict; absence stays absence and grants no admission."""

    checked = _validate_ledger(dict(ledger))
    value = checked["entries"].get(old_record_sha256)  # type: ignore[union-attr]
    return ReinspectionVerdict(value) if value is not None else None


def revalidate_reinspection_ledger(
    ledger: Mapping[str, object],
    records: Iterable[Mapping[str, object]],
    *,
    ccbench_commit: str | None,
) -> tuple[str, ...]:
    """Reinspect every referenced record at the consumer boundary."""

    checked = _validate_ledger(dict(ledger))
    if checked["ccbench_commit"] != ccbench_commit:
        raise ReinspectionError("reinspection ledger commit binding が不一致")
    entries = checked["entries"]
    evidence = checked["evidence"]
    digests: list[str] = []
    for record in records:
        digest = canonical_record_sha256(record)
        verdict = entries.get(digest)
        proof = evidence.get(digest)
        if type(verdict) is not str or not isinstance(proof, dict):
            raise ReinspectionError("reinspection ledger に record verdict がない")
        actual = reinspect_record(
            record,
            source_root=proof["source_root"],
            ccbench_commit=ccbench_commit,
        )
        if actual is not ReinspectionVerdict.PASSED or verdict != actual.value:
            raise ReinspectionError("reinspection record の consumer 再検査が不合格")
        digests.append(digest)
    if set(entries) != set(digests):
        raise ReinspectionError("reinspection ledger record 集合が campaign と不一致")
    return tuple(digests)
