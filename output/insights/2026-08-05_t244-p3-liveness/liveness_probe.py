#!/usr/bin/env python3
"""Fixture-only T-244 P3 probe; placeholder budget; accepted is ledger vocabulary, not an execution result."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RECEIPT = Path(__file__).resolve().with_name("receipt")
sys.path.insert(0, os.fspath(ROOT / "orchestrator"))
from campaign import auditor_gate, reflux_ir, reflux_origin_ledger as ledger  # noqa: E402

CHECKS = ("C-a", "C-b", "C-c1", "C-c2", "C-d", "C-e")
SEMANTICS = "ledger-vocabulary-only; not an execution result"
SCOPE = {"fixture_only": True, "placeholder_manifest": True, "production_evidence": False, "p3_evidence": False}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()


def fixture_manifest() -> dict[str, object]:
    h = lambda char: char * 64
    floor = {"formula_id": "q-lower-bound/base+perRound*R+Emin/v1",
             "base_queries": 0, "queries_per_round": 2, "rounds": 1, "evidence_min": 0}
    return {
        "authority_series_id": "t244-p3-liveness-placeholder",
        "spec_content_sha256": h("1"), "ccbench_commit_oid": "2" * 40, "axis_semantics_sha256": h("3"),
        "workload": {"descriptor_sha256": h("4"), "records": 1, "threads": 1},
        "verifier_policy_sha256": h("5"), "environment_contract_sha256": h("6"), "role_bundle_sha256": h("8"),
        "recipient_projection_schema_sha256": h("9"),
        "candidate_ir": {"schema_ref": "izanagi-trigger-gate-ir/v1", "canonical_emitter_sha256": h("7")},
        "budget_policy": {"imax": 2, "qmax": 4, "kmax": 0, "batch_cardinality_min": 2,
                          "query_floor_constraints": [floor]},
        "stock_certification_ref": {"path": "placeholder/stock.json", "sha256": h("a")},
        "structural_zero_evidence_ref": {"path": "placeholder/zero.json", "sha256": h("b")},
    }


def member_bytes(wire: bytes, ordinal: int) -> bytes:
    body = {"candidate_wire_b64": base64.b64encode(wire).decode("ascii"), "query_ordinal": ordinal,
            "replicate_ordinal": ordinal}
    return b"izanagi-reflux-origin-batch-member/v1\0" + canonical(body)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=repo, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=30)


def commit(store: object, origin: str, operation: str, base: str, event: object) -> ledger.EventReceipt:
    with ledger._locked(store) as authority:
        fields = {"origin_id": origin, "operation_id": operation, "expected_state_commitment": base, "event": event}
        return ledger._commit_locked(store, authority, **fields)


def load_preview(path: Path, wire: str) -> str:
    with path.open("rb") as source:
        raw = source.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("preview exceeds 1048576 bytes")
    preview = json.loads(raw.decode())
    evidence, working_diff = preview.get("diff_digest"), preview.get("working_diff")
    if type(preview) is not dict or preview.get("passed") is not True:
        raise ValueError("preview is not a passed object")
    if type(evidence) is not str or re.fullmatch(r"[0-9a-f]{64}", evidence) is None:
        raise ValueError("diff_digest is not 64 lowercase hex")
    if type(working_diff) is not str or auditor_gate.compute_diff_digest(working_diff) != evidence:
        raise ValueError("working_diff does not match diff_digest")
    predicate = reflux_ir.emit_predicate(reflux_ir.parse_wire(wire))
    if predicate not in working_diff:
        raise ValueError("wire predicate is absent from working_diff")
    return evidence


def run_probe(wire_text: str, evidence: str) -> tuple[dict[str, bool], dict[str, object]]:
    wire = wire_text.encode("ascii")
    salts: list[str] = []
    while len(salts) < 6:
        salt = secrets.token_hex(16)
        if salt != "0" * 32 and salt not in salts:
            salts.append(salt)
    salted = lambda salt, value: hashlib.sha256(bytes.fromhex(salt) + value).hexdigest()
    candidate_salts, result_salts, constraint_salts = salts[:2], salts[2:4], salts[4:]
    candidates = tuple(salted(candidate_salts[i], member_bytes(wire, i)) for i in range(2))
    result_preimage = b"izanagi-reflux-origin-result-evidence/v1\0" + canonical({
        "evidence_sha256": evidence, "outcome": "accepted"})
    results = tuple(salted(result_salts[i], result_preimage) for i in range(2))
    constraints = tuple(salted(constraint_salts[i], b"") for i in range(2))
    events = (
        ledger.BatchCommitted("liveness-positive", 0, tuple(ledger.CommittedBatchMember(i, candidates[i])
                                                            for i in range(2))),
        ledger.BatchResultsPrepared("liveness-positive", tuple(ledger.PreparedBatchMember(
            i, candidates[i], results[i], constraints[i]) for i in range(2))),
        ledger.BatchSealed("liveness-positive", tuple(ledger.OpenedBatchMember(
            i, i, candidate_salts[i], wire, result_salts[i], "accepted",
            ledger.EvidenceDigest(evidence), constraint_salts[i], None) for i in range(2))),
    )
    manifest = fixture_manifest()
    origin = hashlib.sha256(b"izanagi-reflux-origin-manifest/v2\0" + canonical(manifest)).hexdigest()
    cell_fields = [manifest["workload"]["descriptor_sha256"], manifest["axis_semantics_sha256"],
                   manifest["verifier_policy_sha256"], manifest["environment_contract_sha256"]]
    cell = hashlib.sha256(b"izanagi-reflux-origin-cell/v1\0" + canonical(cell_fields)).hexdigest()
    authority = canonical({"authority_schema": "izanagi-reflux-origin-authority/v2",
                           "origins": [{"cell_key": cell, "manifest": manifest, "origin_id": origin}]}) + b"\n"
    temp_base = Path(tempfile.gettempdir()).resolve()
    if temp_base == ROOT or ROOT in temp_base.parents:
        raise ValueError("temporary root is inside the source repository")
    with tempfile.TemporaryDirectory(prefix="t244-p3-liveness-", dir=temp_base) as temporary:
        repo = Path(temporary).resolve()
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Liveness Probe")
        git(repo, "config", "user.email", "probe@example.invalid")
        authority_path = repo / "orchestrator/campaign/reflux_origin_authority_v2.json"
        authority_path.parent.mkdir(parents=True)
        authority_path.write_bytes(authority)
        git(repo, "add", authority_path.relative_to(repo).as_posix())
        git(repo, "commit", "-qm", "fixture authority")
        store = ledger._fixture_store_for_test(repo, "HEAD")
        with ledger._locked(store) as loaded:
            before = ledger._read_origin_locked(store, loaded, origin)
        receipts, base = [], before.state_commitment
        for index, event in enumerate(events):
            item = commit(store, origin, f"liveness-positive-{index}", base, event)
            receipts.append(item)
            base = item.current_state_commitment
        with ledger._locked(store) as loaded:
            after = ledger._read_origin_locked(store, loaded, origin)
            opened = ledger._read_sealed_batch_locked(store, loaded, origin, "liveness-positive")
        duplicate = ledger.BatchCommitted("liveness-negative-duplicate", 1, (
            ledger.CommittedBatchMember(2, candidates[0]),
            ledger.CommittedBatchMember(3, candidates[0])))
        duplicate_reason = None
        try:
            commit(store, origin, "liveness-negative-duplicate", base, duplicate)
        except ledger.RefluxOriginLedgerError as exc:
            duplicate_reason = str(exc)
        with ledger._locked(store) as loaded:
            after_negative = ledger._read_origin_locked(store, loaded, origin)
    members = opened.members
    unchanged = (after_negative.queries_used, after_negative.iterations_used) == (after.queries_used, after.iterations_used)
    checks = {
        "C-a": len(receipts) == 3 and all(re.fullmatch(r"[0-9a-f]{64}", x.event_sha256) for x in receipts),
        "C-b": len(members) == 2 and tuple(x.replicate_ordinal for x in members) == (0, 1),
        "C-c1": all(x.candidate_bytes == wire for x in members) and reflux_ir.encode_wire(reflux_ir.parse_wire(wire_text)) == wire_text,
        "C-c2": all(x.evidence_digest and x.evidence_digest.sha256 == evidence for x in members),
        "C-d": duplicate_reason == "invalid batch candidate commitments" and unchanged,
        "C-e": (before.queries_used, after.queries_used, before.iterations_used, after.iterations_used) == (0, 2, 0, 1),
    }
    details = {
        "wire": wire_text,
        "events": {type(event).__name__: {"event_sha256": item.event_sha256, "event_index": item.event_index}
                   for event, item in zip(events, receipts, strict=True)},
        "counters": {
            "queries_used": {"before": before.queries_used, "after": after.queries_used},
            "iterations_used": {"before": before.iterations_used, "after": after.iterations_used},
        },
        "sealed_members": [{"candidate_bytes": member.candidate_bytes.decode("ascii"),
                            "evidence_digest": ({"sha256": member.evidence_digest.sha256}
                                                if member.evidence_digest else None),
                            "replicate_ordinal": member.replicate_ordinal} for member in members],
        "distinct_candidate_count": len({member.candidate_bytes for member in members}),
        "member_row_count": len(members),
        "negative_control": {
            "rejection_reason": duplicate_reason, "counters_unchanged": unchanged,
            "queries_used": {"before": after.queries_used, "after": after_negative.queries_used},
            "iterations_used": {"before": after.iterations_used, "after": after_negative.iterations_used},
        },
    }
    return checks, details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wire", required=True)
    parser.add_argument("--preview-json", type=Path, required=True)
    parser.add_argument("--keep", type=Path)
    args = parser.parse_args()
    statuses = {name: "NOT_RUN" for name in CHECKS}
    details: dict[str, object] = {}
    stage, reason = "receipt_output", "not run"
    try:
        if args.keep is not None and Path(os.path.abspath(args.keep)) != RECEIPT:
            raise ValueError(f"--keep must be exactly {RECEIPT}")
        stage = "preview"
        evidence = load_preview(args.preview_json, args.wire)
        stage = "fixture_ledger"
        checks, details = run_probe(args.wire, evidence)
        statuses = {name: "PASS" if checks[name] else "FAIL" for name in CHECKS}
        failed = [name for name in CHECKS if statuses[name] == "FAIL"]
        stage, reason = ("verification", ", ".join(failed)) if failed else ("complete", "none")
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
    receipt = {"schema": "izanagi-t244-p3-liveness-receipt/v1", **SCOPE, **details, "outcome": "accepted",
               "outcome_semantics": SEMANTICS, "check_statuses": statuses, "stage": stage, "reason": reason}
    if args.keep is not None and Path(os.path.abspath(args.keep)) == RECEIPT:
        try:
            descriptor = os.open(RECEIPT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(receipt, output, sort_keys=True, indent=2)
                output.write("\n")
        except Exception as exc:
            stage, reason = "receipt_output", f"{type(exc).__name__}: {exc}"
    print("scope: fixture-only; placeholder manifest; non-production; not P3 evidence")
    print(f'outcome="accepted" semantics: {SEMANTICS}')
    print(f"stage: {stage}")
    print(f"reason: {reason}")
    for name in CHECKS:
        print(f"{name}\t{statuses[name]}")
    return 0 if stage == "complete" and all(x == "PASS" for x in statuses.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
