# -*- coding: utf-8 -*-
"""T-244 origin-ledger prototype の独立 golden / FSM / crash / anchor tests。

pytest と素の ``python3 orchestrator/tests/test_reflux_origin_ledger.py`` の双方で走る。
production API の path を monkeypatch せず、private seam へ temp Git repository 全体だけを渡す。
"""
from __future__ import annotations

import base64
import dataclasses
import errno
import fcntl
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
sys.path.insert(0, os.fspath(_ORCHESTRATOR.parent))

from orchestrator.campaign import reflux_origin_ledger as ledger  # noqa: E402


FORMULA = "q-lower-bound/base+perRound*R+Emin/v1"
SCHEMA = "izanagi-trigger-gate-ir/v1"
AUTHORITY_PATH = Path("orchestrator/campaign/reflux_origin_authority_v2.json")
SUBPROCESS_TIMEOUT = 120


class Raises:
    def __init__(self, contains: str | None = None):
        self.contains = contains
        self.value: BaseException | None = None

    def __enter__(self) -> "Raises":
        return self

    def __exit__(self, kind, value, traceback) -> bool:
        assert kind is not None, "expected RefluxOriginLedgerError"
        assert issubclass(kind, ledger.RefluxOriginLedgerError), kind
        self.value = value
        if self.contains is not None:
            assert self.contains in str(value), str(value)
        return True


def _h(char: str) -> str:
    return char * 64


def _manifest_object(
    *,
    series: str = "series-a",
    descriptor: str = _h("4"),
    axis: str = _h("5"),
    verifier: str = _h("6"),
    environment: str = _h("7"),
    imax: int = 4,
    qmax: int = 8,
    kmax: int = 3,
    member_row_min: int = 2,
    candidate_min: int = 1,
    floor_base: int = 0,
    floor_per_round: int = 2,
    floor_rounds: int = 1,
    floor_evidence: int = 0,
    schema: str = SCHEMA,
) -> dict[str, object]:
    return {
        "authority_series_id": series,
        "spec_content_sha256": _h("1"),
        "ccbench_commit_oid": "2" * 40,
        "axis_semantics_sha256": axis,
        "workload": {
            "descriptor_sha256": descriptor,
            "records": 100003,
            "threads": 7,
        },
        "verifier_policy_sha256": verifier,
        "environment_contract_sha256": environment,
        "candidate_ir": {
            "schema_ref": schema,
            "canonical_emitter_sha256": _h("8"),
        },
        "role_bundle_sha256": _h("9"),
        "recipient_projection_schema_sha256": _h("a"),
        "budget_policy": {
            "imax": imax,
            "qmax": qmax,
            "kmax": kmax,
            "batch_member_row_count_min": member_row_min,
            "batch_distinct_candidate_count_min": candidate_min,
            "query_floor_constraints": [{
                "formula_id": FORMULA,
                "base_queries": floor_base,
                "queries_per_round": floor_per_round,
                "rounds": floor_rounds,
                "evidence_min": floor_evidence,
            }],
        },
        "stock_certification_ref": {"path": "evidence/stock.json", "sha256": _h("b")},
        "structural_zero_evidence_ref": {"path": "evidence/zero.json", "sha256": _h("c")},
    }


def _manifest(raw: dict[str, object] | None = None) -> ledger.AuthorityManifest:
    return ledger._manifest_from_object(raw or _manifest_object())


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _independent_origin(raw_manifest: dict[str, object]) -> str:
    return hashlib.sha256(
        b"izanagi-reflux-origin-manifest/v2\0" + _canonical(raw_manifest)
    ).hexdigest()


def _independent_cell(raw_manifest: dict[str, object]) -> str:
    cell = [
        raw_manifest["workload"]["descriptor_sha256"],
        raw_manifest["axis_semantics_sha256"],
        raw_manifest["verifier_policy_sha256"],
        raw_manifest["environment_contract_sha256"],
    ]
    return hashlib.sha256(b"izanagi-reflux-origin-cell/v1\0" + _canonical(cell)).hexdigest()


def _authority_bytes(manifests: list[dict[str, object]]) -> bytes:
    entries = [{
        "cell_key": _independent_cell(item),
        "manifest": item,
        "origin_id": _independent_origin(item),
    } for item in manifests]
    entries.sort(key=lambda item: item["origin_id"])
    return _canonical({
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": entries,
    }) + b"\n"


def _independent_event_frame(
    event_type: str,
    payload: dict[str, object],
    *,
    operation_id: str = "x" * 128,
    event_index: int = (1 << 63) - 1,
    previous_event_sha256: str = "e" * 64,
) -> bytes:
    core = {
        "schema_version": "izanagi-reflux-origin-event/v2",
        "event_index": event_index,
        "previous_event_sha256": previous_event_sha256,
        "origin_id": "f" * 64,
        "operation_id": operation_id,
        "event_type": event_type,
        "payload": payload,
    }
    record = dict(core)
    record["event_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    return _canonical(record) + b"\n"


def _independent_head_frame(
    record_type: str,
    payload: dict[str, object],
    *,
    record_index: int = (1 << 63) - 1,
    previous_record_sha256: str = "e" * 64,
) -> bytes:
    core = {
        "schema_version": "izanagi-reflux-origin-runtime-head/v2",
        "record_index": record_index,
        "previous_record_sha256": previous_record_sha256,
        "record_type": record_type,
        "payload": payload,
    }
    record = dict(core)
    record["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    return _canonical(record) + b"\n"


def _independent_worst_case_batch_frames(
    member_row_count: int,
    *,
    tombstoned: bool = False,
) -> tuple[bytes, bytes, bytes, bytes]:
    maximum_integer = (1 << 63) - 1
    hashes = tuple(
        f"{index + 1:064x}" for index in range(member_row_count)
    )
    reserved = _independent_event_frame("batch-reserved", {
        "batch_id": "x" * 128,
        "member_row_count": member_row_count,
        "iteration_index": maximum_integer,
        "query_ordinal_start": maximum_integer,
    })
    committed = _independent_event_frame("batch-committed", {
        "batch_id": "x" * 128,
        "member_row_count": member_row_count,
        "iteration_index": maximum_integer,
        "members": [
            {"candidate_commitment": digest, "query_ordinal": maximum_integer}
            for digest in hashes
        ],
    })
    prepared = _independent_event_frame("batch-results-prepared", {
        "batch_id": "x" * 128,
        "members": [
            {
                "candidate_commitment": digest,
                "constraint_commitment": digest,
                "query_ordinal": maximum_integer,
                "result_evidence_commitment": digest,
            }
            for digest in hashes
        ],
    })
    members = []
    for index, digest in enumerate(hashes):
        salt_base = index * 3 + 1
        candidate = f"{index % 32:05b}".encode("ascii")
        members.append({
            "candidate_salt": f"{salt_base:032x}"[-32:],
            "candidate_wire_b64": base64.b64encode(candidate).decode("ascii"),
            "constraint_salt": f"{salt_base + 2:032x}"[-32:],
            "constraint_sha256": None if tombstoned else digest,
            "evidence_sha256": None if tombstoned else digest,
            "outcome": "tombstoned" if tombstoned else "rejected",
            "query_ordinal": maximum_integer,
            "replicate_ordinal": maximum_integer,
            "result_evidence_salt": f"{salt_base + 1:032x}"[-32:],
        })
    sealed = _independent_event_frame("batch-sealed", {
        "batch_id": "x" * 128,
        "member_row_count": member_row_count,
        "distinct_candidate_count": min(member_row_count, 32),
        "sealed_distinct_candidate_count": (
            0 if tombstoned else min(member_row_count, 32)
        ),
        "members": members,
    })
    return reserved, committed, prepared, sealed


def _independent_worst_case_abandoned_frames(
    member_row_count: int,
) -> tuple[bytes, bytes]:
    maximum_integer = (1 << 63) - 1
    reserved = _independent_event_frame("batch-reserved", {
        "batch_id": "x" * 128,
        "member_row_count": member_row_count,
        "iteration_index": maximum_integer,
        "query_ordinal_start": maximum_integer,
    })
    abandoned = _independent_event_frame("batch-reservation-abandoned", {
        "batch_id": "x" * 128,
    })
    return reserved, abandoned


def _independent_origin_ledger_upper_bytes(
    *,
    batches: int,
    members: int,
    kmax: int,
) -> int:
    maximum_integer = (1 << 63) - 1
    genesis = _independent_event_frame(
        "origin-opened",
        {"authority_blob_sha256": "a" * 64, "cell_key": "b" * 64},
        operation_id="origin-opened:" + "f" * 64,
        event_index=0,
        previous_event_sha256="0" * 64,
    )
    class_frame = _independent_event_frame("origin-sealed", {
        "batch_count": maximum_integer,
        "constraint_class_sha256s": [
            f"{index + 1:064x}" for index in range(kmax)
        ],
        "seal_kind": "certifiable",
        "sealed_queries": maximum_integer,
        "tombstone_count": maximum_integer,
        "tombstoned_queries": maximum_integer,
        "forfeited_iterations": maximum_integer,
        "forfeited_queries": maximum_integer,
    })
    branch_bytes = []
    for tombstoned in (False, True):
        one = sum(map(len, _independent_worst_case_batch_frames(
            1, tombstoned=tombstoned
        )))
        two = sum(map(len, _independent_worst_case_batch_frames(
            2, tombstoned=tombstoned
        )))
        increment = two - one
        # Hand-derived conservative reserve: reserve/commit/seal member rows
        # expand to four digits, and both distinct counts expand to two.
        branch_bytes.append(
            batches * one + (members - batches) * increment + batches * 11
        )
    return len(genesis) + max(branch_bytes) + len(class_frame)


def _independent_shared_head_bytes(batch_counts: tuple[int, ...]) -> int:
    maximum_integer = (1 << 63) - 1
    genesis = _independent_head_frame(
        "runtime-opened",
        {
            "authority_blob_sha256": "a" * 64,
            "origin_heads": [
                {
                    "event_index": 0,
                    "event_sha256": "b" * 64,
                    "origin_id": f"{index + 1:064x}",
                }
                for index in range(len(batch_counts))
            ],
        },
        record_index=0,
        previous_record_sha256="0" * 64,
    )
    prepared = _independent_head_frame("head-prepared", {
        "base_state_commitment": "a" * 64,
        "next_event_binding_sha256": "d" * 64,
        "old_event_byte_length": 64 << 20,
        "old_event_index": maximum_integer,
        "old_event_sha256": "c" * 64,
        "operation_id": "x" * 128,
        "origin_id": "f" * 64,
        "prospective_public_state_sha256": "e" * 64,
        "request_sha256": "b" * 64,
    })
    committed = _independent_head_frame("head-committed", {
        "event_index": maximum_integer,
        "event_sha256": "b" * 64,
        "operation_id": "x" * 128,
        "origin_id": "f" * 64,
        "prepared_record_sha256": "a" * 64,
    })
    pair_bytes = len(prepared) + len(committed)
    return len(genesis) + sum(
        (batch_count * 4 + 1) * pair_bytes for batch_count in batch_counts
    )


def _git_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "LC_ALL", "TZ")
        if key in os.environ
    }
    env.update({
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
    })
    if extra:
        env.update(extra)
    return env


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=repo,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return result.stdout


def _repo(tmp_path: Path, manifests: list[dict[str, object]] | None = None) -> tuple[Path, list[str]]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Origin Test")
    _git(repo, "config", "user.email", "origin@example.invalid")
    manifests = manifests or [_manifest_object()]
    path = repo / AUTHORITY_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(_authority_bytes(manifests))
    _git(repo, "add", AUTHORITY_PATH.as_posix())
    _git(repo, "commit", "-qm", "fixture authority")
    return repo, [_independent_origin(item) for item in manifests]


def _store(repo: Path, *, initialize: bool = True) -> object:
    return ledger._fixture_store_for_test(repo, "HEAD", initialize=initialize)


def _snapshot(store: object, origin_id: str) -> ledger.OriginSnapshot:
    with ledger._locked(store) as authority:
        return ledger._read_origin_locked(store, authority, origin_id)


def _commit(
    store: object,
    origin_id: str,
    operation: str,
    base: str,
    event: object,
) -> ledger.EventReceipt:
    with ledger._locked(store) as authority:
        return ledger._commit_locked(
            store,
            authority,
            origin_id=origin_id,
            operation_id=operation,
            expected_state_commitment=base,
            event=event,
        )


def _salted(salt: str, value: bytes) -> str:
    return hashlib.sha256(bytes.fromhex(salt) + value).hexdigest()


def _member_bytes(candidate: bytes, query: int, replicate: int) -> bytes:
    return b"izanagi-reflux-origin-batch-member/v1\0" + _canonical({
        "candidate_wire_b64": base64.b64encode(candidate).decode("ascii"),
        "query_ordinal": query,
        "replicate_ordinal": replicate,
    })


def _result_bytes(outcome: str, evidence: str | None) -> bytes:
    return b"izanagi-reflux-origin-result-evidence/v1\0" + _canonical({
        "evidence_sha256": evidence,
        "outcome": outcome,
    })


def _batch_events(
    batch_id: str = "batch-0",
    iteration: int = 0,
    candidates: tuple[bytes, ...] = (b"10000", b"01000"),
    outcomes: tuple[str, ...] = ("accepted", "rejected"),
    constraints: tuple[str | None, ...] = (None, _h("d")),
    query_start: int = 0,
    prior_replicates: dict[bytes, int] | None = None,
) -> tuple[object, object, object]:
    def salts(_: str) -> tuple[str, ...]:
        return tuple(os.urandom(16).hex() for _ in candidates)
    candidate_salts = salts("candidate")
    result_salts = salts("result")
    constraint_salts = salts("constraint")
    evidence = tuple(
        None if outcome == "tombstoned" else (_h("e"), _h("f"))[index % 2]
        for index, outcome in enumerate(outcomes)
    )
    counts = dict(prior_replicates or {})
    replicates = []
    for candidate in candidates:
        replicates.append(counts.get(candidate, 0))
        counts[candidate] = counts.get(candidate, 0) + 1
    candidate_commitments = tuple(
        _salted(salt, _member_bytes(value, query_start + index, replicates[index]))
        for index, (salt, value) in enumerate(
            zip(candidate_salts, candidates, strict=True)
        )
    )
    result_commitments = tuple(
        _salted(salt, _result_bytes(outcome, digest))
        for salt, outcome, digest in zip(result_salts, outcomes, evidence, strict=True)
    )
    constraint_commitments = tuple(
        _salted(salt, b"" if value is None else value.encode("ascii"))
        for salt, value in zip(constraint_salts, constraints, strict=True)
    )
    return (
        ledger.BatchCommitted(batch_id, iteration, tuple(
            ledger.CommittedBatchMember(query_start + index, commitment)
            for index, commitment in enumerate(candidate_commitments)
        )),
        ledger.BatchResultsPrepared(
            batch_id,
            tuple(
                ledger.PreparedBatchMember(
                    query_start + index,
                    candidate_commitments[index],
                    result_commitments[index],
                    constraint_commitments[index],
                )
                for index in range(len(candidates))
            ),
        ),
        ledger.BatchSealed(
            batch_id,
            tuple(
                ledger.OpenedBatchMember(
                    query_ordinal=query_start + index,
                    replicate_ordinal=replicates[index],
                    candidate_salt=candidate_salts[index],
                    candidate_bytes=candidates[index],
                    result_evidence_salt=result_salts[index],
                    outcome=outcomes[index],
                    evidence_digest=None if evidence[index] is None else ledger.EvidenceDigest(evidence[index]),
                    constraint_salt=constraint_salts[index],
                    constraint_sha256=constraints[index],
                )
                for index in range(len(candidates))
            ),
        ),
    )


def _reservation_event(
    batch_id: str = "batch-0",
    iteration: int = 0,
    member_row_count: int = 2,
    query_start: int = 0,
) -> ledger.BatchReserved:
    return ledger.BatchReserved(
        batch_id, iteration, member_row_count, query_start
    )


def _reservation_for(event: ledger.BatchCommitted) -> ledger.BatchReserved:
    assert event.members, "a committed batch must have at least one member"
    return _reservation_event(
        event.batch_id,
        event.iteration_index,
        len(event.members),
        event.members[0].query_ordinal,
    )


def _commit_sequence(store: object, origin: str, events: tuple[object, ...], prefix: str) -> list[ledger.EventReceipt]:
    receipts = []
    base = _snapshot(store, origin).state_commitment
    for index, event in enumerate(events):
        receipt = _commit(store, origin, f"{prefix}-{index}", base, event)
        receipts.append(receipt)
        base = receipt.current_state_commitment
    return receipts


def _commit_batch_sequence(
    store: object,
    origin: str,
    events: tuple[object, ...],
    prefix: str,
) -> list[ledger.EventReceipt]:
    assert events and type(events[0]) is ledger.BatchCommitted
    return _commit_sequence(
        store,
        origin,
        (_reservation_for(events[0]), *events),
        prefix,
    )


def _files(store: object, origin: str) -> tuple[bytes, bytes]:
    return store.head_path.read_bytes(), store.origin_path(origin).read_bytes()


def _assert_flock_state(path: Path, *, blocked: bool) -> None:
    fd = os.open(path, os.O_RDWR | getattr(os, "O_CLOEXEC", 0))
    acquired = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError as exc:
            assert exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK)
            assert blocked, "flock unexpectedly blocked after the holder released"
        else:
            assert not blocked, "flock unexpectedly succeeded while the holder was active"
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_v01_literal_manifest_event_state_and_receipt_goldens() -> None:
    """V1 / M-N1: production helper から期待値を作らない literal golden。"""
    assert ledger.MANIFEST_SCHEMA_ID == "izanagi-reflux-origin-manifest/v2"
    assert ledger.AUTHORITY_SCHEMA_ID == "izanagi-reflux-origin-authority/v2"
    assert ledger.AUTHORITY_RELATIVE_PATH.endswith("reflux_origin_authority_v2.json")
    assert {"BatchReserved", "BatchReservationAbandoned"} <= set(ledger.__all__)
    raw = _manifest_object()
    literal = (
        b'{"authority_series_id":"series-a","axis_semantics_sha256":"5555555555555555555555555555555555555555555555555555555555555555",'
        b'"budget_policy":{"batch_distinct_candidate_count_min":1,"batch_member_row_count_min":2,"imax":4,"kmax":3,"qmax":8,"query_floor_constraints":['
        b'{"base_queries":0,"evidence_min":0,"formula_id":"q-lower-bound/base+perRound*R+Emin/v1","queries_per_round":2,"rounds":1}]},'
        b'"candidate_ir":{"canonical_emitter_sha256":"8888888888888888888888888888888888888888888888888888888888888888","schema_ref":"izanagi-trigger-gate-ir/v1"},'
        b'"ccbench_commit_oid":"2222222222222222222222222222222222222222","environment_contract_sha256":"7777777777777777777777777777777777777777777777777777777777777777",'
        b'"recipient_projection_schema_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","role_bundle_sha256":"9999999999999999999999999999999999999999999999999999999999999999",'
        b'"spec_content_sha256":"1111111111111111111111111111111111111111111111111111111111111111","stock_certification_ref":{"path":"evidence/stock.json","sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},'
        b'"structural_zero_evidence_ref":{"path":"evidence/zero.json","sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"},'
        b'"verifier_policy_sha256":"6666666666666666666666666666666666666666666666666666666666666666","workload":{"descriptor_sha256":"4444444444444444444444444444444444444444444444444444444444444444","records":100003,"threads":7}}'
    )
    assert _canonical(raw) == literal
    assert ledger.canonical_manifest_bytes(_manifest(raw)) == literal
    # SHA-256 standard literal keeps the digest oracle independent from this module.
    assert ledger._sha256(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    event = ledger._event_record(
        origin_id=_h("1"), operation_id="op-golden", event_index=7,
        previous_event_sha256=_h("2"), event_type="batch-sealed",
        payload={
            "batch_id": "batch-golden",
            "distinct_candidate_count": 1,
            "member_row_count": 1,
            "sealed_distinct_candidate_count": 0,
            "members": [{
            "candidate_salt": "1" * 32,
            "candidate_wire_b64": "MTAwMDA=",
            "constraint_salt": "2" * 32,
            "constraint_sha256": None,
            "evidence_sha256": None,
            "outcome": "tombstoned",
            "query_ordinal": 7,
            "replicate_ordinal": 3,
            "result_evidence_salt": "3" * 32,
            }],
        },
    )
    literal_event_frame = (
        b'{"event_index":7,"event_sha256":"0924fe76119fcc5dffd0c0e5efa37ab25b51c6ee9a1ae1a432a1bf16deea9a05",'
        b'"event_type":"batch-sealed","operation_id":"op-golden","origin_id":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"payload":{"batch_id":"batch-golden","distinct_candidate_count":1,"member_row_count":1,"members":[{"candidate_salt":"11111111111111111111111111111111","candidate_wire_b64":"MTAwMDA=",'
        b'"constraint_salt":"22222222222222222222222222222222","constraint_sha256":null,"evidence_sha256":null,"outcome":"tombstoned",'
        b'"query_ordinal":7,"replicate_ordinal":3,"result_evidence_salt":"33333333333333333333333333333333"}],"sealed_distinct_candidate_count":0},'
        b'"previous_event_sha256":"2222222222222222222222222222222222222222222222222222222222222222",'
        b'"schema_version":"izanagi-reflux-origin-event/v2"}\n'
    )
    literal_event_core = literal_event_frame.replace(
        b',"event_sha256":"0924fe76119fcc5dffd0c0e5efa37ab25b51c6ee9a1ae1a432a1bf16deea9a05"',
        b"",
        1,
    )[:-1]
    assert hashlib.sha256(literal_event_core).hexdigest() == (
        "0924fe76119fcc5dffd0c0e5efa37ab25b51c6ee9a1ae1a432a1bf16deea9a05"
    )
    assert _canonical(event) + b"\n" == literal_event_frame
    reservation = ledger._event_record(
        origin_id=_h("1"), operation_id="reserve-golden", event_index=8,
        previous_event_sha256=_h("2"), event_type="batch-reserved",
        payload={
            "batch_id": "batch-golden",
            "iteration_index": 7,
            "member_row_count": 2,
            "query_ordinal_start": 14,
        },
    )
    literal_reservation_frame = (
        b'{"event_index":8,"event_sha256":"dfb3039e4d42e4b94c77096777cf59045a51a9b76c2920d406748cb599b9ce77",'
        b'"event_type":"batch-reserved","operation_id":"reserve-golden","origin_id":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"payload":{"batch_id":"batch-golden","iteration_index":7,"member_row_count":2,"query_ordinal_start":14},'
        b'"previous_event_sha256":"2222222222222222222222222222222222222222222222222222222222222222",'
        b'"schema_version":"izanagi-reflux-origin-event/v2"}\n'
    )
    reservation_core = literal_reservation_frame.replace(
        b',"event_sha256":"dfb3039e4d42e4b94c77096777cf59045a51a9b76c2920d406748cb599b9ce77"',
        b"",
        1,
    )[:-1]
    assert hashlib.sha256(reservation_core).hexdigest() == (
        "dfb3039e4d42e4b94c77096777cf59045a51a9b76c2920d406748cb599b9ce77"
    )
    assert _canonical(reservation) + b"\n" == literal_reservation_frame
    abandoned = ledger._event_record(
        origin_id=_h("1"), operation_id="abandon-golden", event_index=9,
        previous_event_sha256=_h("3"),
        event_type="batch-reservation-abandoned",
        payload={"batch_id": "batch-golden"},
    )
    literal_abandoned_frame = (
        b'{"event_index":9,"event_sha256":"3d6bd2067e166da750177ebda1f92abd0f3c37677d3a3303233143ebaf5b6c2b",'
        b'"event_type":"batch-reservation-abandoned","operation_id":"abandon-golden",'
        b'"origin_id":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"payload":{"batch_id":"batch-golden"},'
        b'"previous_event_sha256":"3333333333333333333333333333333333333333333333333333333333333333",'
        b'"schema_version":"izanagi-reflux-origin-event/v2"}\n'
    )
    abandoned_core = literal_abandoned_frame.replace(
        b',"event_sha256":"3d6bd2067e166da750177ebda1f92abd0f3c37677d3a3303233143ebaf5b6c2b"',
        b"",
        1,
    )[:-1]
    assert hashlib.sha256(abandoned_core).hexdigest() == (
        "3d6bd2067e166da750177ebda1f92abd0f3c37677d3a3303233143ebaf5b6c2b"
    )
    assert _canonical(abandoned) + b"\n" == literal_abandoned_frame
    head_record = ledger._head_record(
        record_index=3,
        previous_record_sha256=_h("f"),
        record_type="head-committed",
        payload={
            "prepared_record_sha256": _h("e"),
            "origin_id": _h("1"),
            "operation_id": "op-golden",
            "event_index": 7,
            "event_sha256": _h("2"),
        },
    )
    literal_head_frame = (
        b'{"payload":{"event_index":7,"event_sha256":"2222222222222222222222222222222222222222222222222222222222222222",'
        b'"operation_id":"op-golden","origin_id":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"prepared_record_sha256":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"},'
        b'"previous_record_sha256":"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff","record_index":3,'
        b'"record_sha256":"1a769b02032b499194eef7d41045d8b9efa9c9742c37a981ec0632c309e858cb",'
        b'"record_type":"head-committed","schema_version":"izanagi-reflux-origin-runtime-head/v2"}\n'
    )
    literal_head_core = literal_head_frame.replace(
        b',"record_sha256":"1a769b02032b499194eef7d41045d8b9efa9c9742c37a981ec0632c309e858cb"',
        b"",
        1,
    )[:-1]
    assert hashlib.sha256(literal_head_core).hexdigest() == (
        "1a769b02032b499194eef7d41045d8b9efa9c9742c37a981ec0632c309e858cb"
    )
    assert _canonical(head_record) + b"\n" == literal_head_frame
    state = ledger._SemanticState()
    head = {
        "record_index": 0,
        "record_sha256": _h("5"),
    }
    observed_state = ledger._state_commitment(
        authority_sha=_h("6"), head_record=head, head_byte_length=211,
        head_tail=b"partial", transaction_phase="clean",
        prepared_record_sha256=None, prepared_request_sha256=None,
        committed_heads={}, origin_states={},
    )
    state_preimage = {
        "authority_blob_sha256": _h("6"),
        "runtime_head_record_index": 0,
        "runtime_head_record_sha256": _h("5"),
        "head_file_byte_length": 211,
        "head_partial_tail_sha256": hashlib.sha256(b"partial").hexdigest(),
        "transaction_phase": "clean",
        "prepared_record_sha256": None,
        "prepared_request_sha256": None,
        "origins": [],
    }
    assert observed_state == hashlib.sha256(
        b"izanagi-reflux-origin-state/v2\0" + _canonical(state_preimage)
    ).hexdigest()
    member_preimage = (
        b'izanagi-reflux-origin-batch-member/v1\x00'
        b'{"candidate_wire_b64":"MTAwMDA=","query_ordinal":7,"replicate_ordinal":3}'
    )
    assert ledger._member_preimage(b"10000", 7, 3) == member_preimage
    assert hashlib.sha256(bytes.fromhex("1" * 32) + member_preimage).hexdigest() == (
        "d78528f3300907292606b2c929da1e17637707af4dbdb80a511b711465ae7a39"
    )
    result_preimage = (
        b'izanagi-reflux-origin-result-evidence/v1\x00'
        b'{"evidence_sha256":null,"outcome":"tombstoned"}'
    )
    assert ledger._result_evidence_preimage("tombstoned", None) == result_preimage
    assert hashlib.sha256(bytes.fromhex("3" * 32) + result_preimage).hexdigest() == (
        "145a9fb91d76254d933846f06a9dd3e53c80e95eaf34e15fe2faff8e7d7cf846"
    )
    assert state.phase == "EMPTY"
    receipt = ledger.EventReceipt(_h("1"), "op-golden", 7, _h("2"), _h("3"), _h("4"), False)
    assert dataclasses.asdict(receipt) == {
        "origin_id": _h("1"), "operation_id": "op-golden", "event_index": 7,
        "event_sha256": _h("2"), "resulting_state_commitment": _h("3"),
        "current_state_commitment": _h("4"), "replayed": False,
    }


def test_v02_exact_six_phase_seven_event_transition_matrix_and_no_legacy_tombstone() -> None:
    """V2: reservation を含む 6 相 x 7 入力の受理集合を全数固定する。"""
    assert "BatchTombstoned" not in ledger.__all__
    assert not hasattr(ledger, "BatchTombstoned")
    assert frozenset(ledger.OriginEvent.__args__) == frozenset((
        ledger.BatchReserved,
        ledger.BatchReservationAbandoned,
        ledger.BatchCommitted,
        ledger.BatchResultsPrepared,
        ledger.BatchSealed,
        ledger.OriginSealed,
    ))
    with Raises("unknown event type"):
        ledger._event_from_payload(
            "batch-tombstoned", {"batch_id": "legacy-batch"}
    )
    manifest = _manifest()
    committed, prepared, sealed = _batch_events()
    reserved = _reservation_for(committed)
    abandoned = ledger.BatchReservationAbandoned(reserved.batch_id)
    origin_seal = ledger.OriginSealed(True, (), 0, 0, 0, 0, 0, 0)
    genesis = None
    events = (
        genesis,
        reserved,
        abandoned,
        committed,
        prepared,
        sealed,
        origin_seal,
    )
    allowed = {
        ("EMPTY", type(None)): "IDLE",
        ("IDLE", ledger.BatchReserved): "BATCH_RESERVED",
        ("IDLE", ledger.OriginSealed): "ORIGIN_SEALED",
        ("BATCH_RESERVED", ledger.BatchCommitted): "BATCH_COMMITTED",
        ("BATCH_RESERVED", ledger.BatchReservationAbandoned): "IDLE",
        ("BATCH_COMMITTED", ledger.BatchResultsPrepared): "RESULTS_PREPARED",
        ("RESULTS_PREPARED", ledger.BatchSealed): "IDLE",
    }
    builders: dict[str, Callable[[], ledger._SemanticState]] = {}
    def at_empty(): return ledger._SemanticState()
    def at_idle():
        state = at_empty(); ledger._apply_event(state, None, manifest=manifest, origin_id=_h("1")); return state
    def at_reserved():
        state = at_idle(); ledger._apply_event(state, reserved, manifest=manifest, origin_id=_h("1")); return state
    def at_committed():
        state = at_reserved(); ledger._apply_event(state, committed, manifest=manifest, origin_id=_h("1")); return state
    def at_prepared():
        state = at_committed(); ledger._apply_event(state, prepared, manifest=manifest, origin_id=_h("1")); return state
    def at_terminal():
        state = at_idle(); ledger._apply_event(state, origin_seal, manifest=manifest, origin_id=_h("1")); return state
    builders.update(
        EMPTY=at_empty,
        IDLE=at_idle,
        BATCH_RESERVED=at_reserved,
        BATCH_COMMITTED=at_committed,
        RESULTS_PREPARED=at_prepared,
        ORIGIN_SEALED=at_terminal,
    )
    accepted = rejected = 0
    for phase, builder in builders.items():
        for event in events:
            key = (phase, type(event))
            state = builder()
            if key in allowed:
                ledger._apply_event(state, event, manifest=manifest, origin_id=_h("1"))
                assert state.phase == allowed[key]
                accepted += 1
            else:
                with Raises():
                    ledger._apply_event(state, event, manifest=manifest, origin_id=_h("1"))
                rejected += 1
    assert len(builders) * len(events) == 42
    assert len(allowed) == accepted == 7
    assert rejected == 35


def test_v03_manifest_identity_and_cell_equivalence_positive_negative() -> None:
    """V3 / M-N1/M-N2: 全 field origin 感度、4 組 cell 正負例、caller override 不在。"""
    base = _manifest_object()
    base_origin = ledger.derive_origin_id(_manifest(base))
    mutations = [
        ("authority_series_id", "series-b"),
        ("spec_content_sha256", _h("d")),
        ("ccbench_commit_oid", "3" * 40),
        ("axis_semantics_sha256", _h("d")),
        ("verifier_policy_sha256", _h("d")),
        ("environment_contract_sha256", _h("d")),
        ("role_bundle_sha256", _h("d")),
        ("recipient_projection_schema_sha256", _h("d")),
    ]
    for key, value in mutations:
        changed = json.loads(json.dumps(base)); changed[key] = value
        assert ledger.derive_origin_id(_manifest(changed)) != base_origin
    nested = []
    for path, value in (
        (("workload", "descriptor_sha256"), _h("d")),
        (("workload", "records"), 100019),
        (("workload", "threads"), 11),
        (("candidate_ir", "canonical_emitter_sha256"), _h("d")),
        (("budget_policy", "imax"), 5),
        (("budget_policy", "qmax"), 9),
        (("budget_policy", "kmax"), 4),
        (("stock_certification_ref", "path"), "evidence/stock-b.json"),
        (("stock_certification_ref", "sha256"), _h("d")),
        (("structural_zero_evidence_ref", "path"), "evidence/zero-b.json"),
        (("structural_zero_evidence_ref", "sha256"), _h("d")),
    ):
        changed = json.loads(json.dumps(base))
        changed[path[0]][path[1]] = value
        nested.append(changed)
    floor_change = json.loads(json.dumps(base))
    floor_change["budget_policy"]["query_floor_constraints"][0]["evidence_min"] = 1
    nested.append(floor_change)
    batch_change = json.loads(json.dumps(base))
    batch_change["budget_policy"]["batch_member_row_count_min"] = 3
    batch_change["budget_policy"]["query_floor_constraints"][0]["queries_per_round"] = 3
    nested.append(batch_change)
    for changed in nested:
        assert ledger.derive_origin_id(_manifest(changed)) != base_origin
    assert base_origin == _independent_origin(base)
    same_cell = json.loads(json.dumps(base)); same_cell["authority_series_id"] = "series-b"
    assert ledger.derive_cell_key(_manifest(same_cell)) == ledger.derive_cell_key(_manifest(base))
    different_cell = json.loads(json.dumps(base)); different_cell["verifier_policy_sha256"] = _h("d")
    assert ledger.derive_cell_key(_manifest(different_cell)) != ledger.derive_cell_key(_manifest(base))
    for container, key in (
        ("workload", "descriptor_sha256"),
        (None, "axis_semantics_sha256"),
        (None, "verifier_policy_sha256"),
        (None, "environment_contract_sha256"),
    ):
        changed = json.loads(json.dumps(base))
        if container is None:
            changed[key] = _h("d")
        else:
            changed[container][key] = _h("d")
        assert ledger.derive_cell_key(_manifest(changed)) != ledger.derive_cell_key(_manifest(base))
        ledger._authority_from_bytes(_authority_bytes([base, changed]))
    with Raises("duplicate authority cell"):
        ledger._authority_from_bytes(_authority_bytes([base, same_cell]))
    ledger._authority_from_bytes(_authority_bytes([base, different_cell]))
    assert "origin_id" not in inspect.signature(ledger.derive_origin_id).parameters


def test_v04_global_flock_race_reentry_and_public_signature(tmp_path: Path) -> None:
    """V4 / M-A2/M-N3: deterministic latch で同一 base の writer を競合。"""
    repo, origins = _repo(tmp_path)
    store = _store(repo)
    origin = origins[0]
    base = _snapshot(store, origin).state_commitment
    event = _reservation_event()
    barrier = threading.Barrier(3)
    outcomes: list[str] = []
    first_at_base = threading.Event()
    release_base = threading.Event()
    latch_guard = threading.Lock()
    latch_calls = 0
    def latch(label: str) -> None:
        nonlocal latch_calls
        if label != "commit:base-read":
            return
        with latch_guard:
            latch_calls += 1
            call = latch_calls
        if call == 1:
            first_at_base.set()
            assert release_base.wait(timeout=10)
    def writer(name: str) -> None:
        barrier.wait()
        try:
            _commit(store, origin, name, base, event)
            outcomes.append("committed")
        except ledger.RefluxOriginLedgerError:
            outcomes.append("rejected")
    threads = [threading.Thread(target=writer, args=(f"race-{index}",)) for index in range(2)]
    ledger._FAULT_HOOK = latch
    try:
        for thread in threads: thread.start()
        barrier.wait()
        assert first_at_base.wait(timeout=10)
        _assert_flock_state(store.lock_path, blocked=True)
        release_base.set()
    finally:
        release_base.set()
        for thread in threads: thread.join(timeout=10)
        ledger._FAULT_HOOK = None
    assert not any(thread.is_alive() for thread in threads)
    _assert_flock_state(store.lock_path, blocked=False)
    assert latch_calls == 2
    assert sorted(outcomes) == ["committed", "rejected"]
    with ledger._locked(store):
        with Raises("reentry"):
            with ledger._locked(store):
                pass
    for function in (ledger.read_origin, ledger.commit_event, ledger.read_sealed_batch):
        parameters = inspect.signature(function).parameters
        assert not ({"root", "path", "store", "repository_root", "ledger_root"} & set(parameters))
    first = _manifest_object(series="series-a", descriptor=_h("4"))
    second = _manifest_object(series="series-b", descriptor=_h("d"))
    two_repo, two_origins = _repo(tmp_path / "two-cells", [first, second])
    two_store = _store(two_repo)
    shared_base = _snapshot(two_store, two_origins[0]).state_commitment
    two_barrier = threading.Barrier(3)
    cross_results: list[str] = []
    def cross_writer(index: int) -> None:
        two_barrier.wait()
        try:
            _commit(two_store, two_origins[index], f"cross-{index}", shared_base,
                    _reservation_event(f"cross-{index}"))
            cross_results.append("committed")
        except ledger.RefluxOriginLedgerError:
            cross_results.append("rejected")
    cross_threads = [threading.Thread(target=cross_writer, args=(index,)) for index in range(2)]
    for thread in cross_threads: thread.start()
    two_barrier.wait()
    for thread in cross_threads: thread.join(timeout=10)
    assert not any(thread.is_alive() for thread in cross_threads)
    assert sorted(cross_results) == ["committed", "rejected"]
    linked = tmp_path / "linked-worktree"
    _git(two_repo, "worktree", "add", "--detach", os.fspath(linked), "HEAD")
    linked_store = ledger._fixture_store_for_test(linked, "HEAD")
    assert linked_store.runtime_root == two_store.runtime_root

    process_manifests = [
        _manifest_object(series="process-a", descriptor=_h("4")),
        _manifest_object(series="process-b", descriptor=_h("d")),
    ]
    process_repo, process_origins = _repo(tmp_path / "process-flock", process_manifests)
    process_store = _store(process_repo)
    process_origin_a, process_origin_b = sorted(process_origins)
    process_base = _snapshot(process_store, process_origin_a).state_commitment
    marker_a = tmp_path / "process-a.ready"
    marker_b = tmp_path / "process-b.ready"
    process_event = _reservation_event("process-batch")
    def process_script(
        origin: str,
        operation: str,
        marker: Path,
        wait_for_release: bool,
        probe: bool,
    ) -> str:
        return f"""
import errno,fcntl,os,sys
from pathlib import Path
sys.path.insert(0,{os.fspath(_ORCHESTRATOR.parent)!r})
from orchestrator.campaign import reflux_origin_ledger as l
s=l._store_for_repo(Path({os.fspath(process_repo)!r}),committed_ref='HEAD',fixture=True)
e=l.BatchReserved(
    {process_event.batch_id!r},
    {process_event.iteration_index!r},
    {process_event.member_row_count!r},
    {process_event.query_ordinal_start!r},
)
if {probe!r}:
    probe_fd=os.open(s.lock_path,os.O_RDWR)
    try:
        try:
            fcntl.flock(probe_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            assert exc.errno in (errno.EAGAIN,errno.EWOULDBLOCK)
            probe_state='blocked'
        else:
            fcntl.flock(probe_fd,fcntl.LOCK_UN)
            probe_state='available'
    finally:
        os.close(probe_fd)
    sys.stdout.write('PROBE '+probe_state+'\\n')
    sys.stdout.flush()
def hook(label):
    if label=='commit:base-read':
        Path({os.fspath(marker)!r}).write_text('ready',encoding='ascii')
        sys.stdout.write('READY\\n')
        sys.stdout.flush()
        if {wait_for_release!r}:
            os.read(0,1)
l._FAULT_HOOK=hook
try:
    with l._locked(s) as a:
        l._commit_locked(s,a,origin_id={origin!r},operation_id={operation!r},expected_state_commitment={process_base!r},event=e)
except l.RefluxOriginLedgerError:
    sys.exit(19)
"""
    import select
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    process_results: dict[str, tuple[int | None, bytes, bytes]] = {}
    observed_stdout: dict[subprocess.Popen[bytes], bytearray] = {}
    cleanup_failures: list[tuple[str, BaseException]] = []
    process_failure: BaseException | None = None
    process_deadline = time.monotonic() + SUBPROCESS_TIMEOUT
    first_ready = ""
    probe_state = ""
    second_ready = ""
    def read_process_line(process: subprocess.Popen[bytes]) -> str:
        assert process.stdout is not None
        stdout = observed_stdout.setdefault(process, bytearray())
        line = bytearray()
        while True:
            remaining = process_deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, SUBPROCESS_TIMEOUT)
            readable, _, _ = select.select(
                (process.stdout.fileno(),), (), (), remaining
            )
            if not readable:
                raise subprocess.TimeoutExpired(process.args, SUBPROCESS_TIMEOUT)
            try:
                byte = os.read(process.stdout.fileno(), 1)
            except InterruptedError:
                continue
            if not byte:
                raise AssertionError(f"unexpected process stdout EOF: {bytes(line)!r}")
            stdout.extend(byte)
            if byte == b"\n":
                return line.decode("ascii")
            line.extend(byte)
    def release_process(process: subprocess.Popen[bytes]) -> None:
        if process.stdin is None:
            return
        stdin = process.stdin
        process.stdin = None
        try:
            stdin.write(b"R")
            stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                stdin.close()
            except (BrokenPipeError, OSError):
                pass
    try:
        first_process = subprocess.Popen(
            [sys.executable, "-c", process_script(
                process_origin_a, "process-a", marker_a, True, False
            )],
            cwd=process_repo,
            env=_git_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        processes.append(("first", first_process))
        first_ready = read_process_line(first_process)
        assert first_ready == "READY"
        second_process = subprocess.Popen(
            [sys.executable, "-c", process_script(
                process_origin_b, "process-b", marker_b, True, True
            )],
            cwd=process_repo,
            env=_git_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        processes.append(("second", second_process))
        probe_line = read_process_line(second_process)
        assert probe_line in ("PROBE blocked", "PROBE available"), probe_line
        probe_state = probe_line.removeprefix("PROBE ")
        release_process(first_process)
        second_ready = read_process_line(second_process)
        assert second_ready == "READY"
        release_process(second_process)
        for _, process in processes:
            remaining = process_deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, SUBPROCESS_TIMEOUT)
            process.wait(timeout=remaining)
    except BaseException as exc:
        process_failure = exc
    finally:
        for _, process in processes:
            release_process(process)
        for name, process in processes:
            if process.poll() is None:
                try:
                    process.kill()
                except OSError as exc:
                    cleanup_failures.append((name, exc))
        for name, process in processes:
            try:
                stdout_tail, stderr = process.communicate(timeout=SUBPROCESS_TIMEOUT)
            except BaseException as exc:
                cleanup_failures.append((name, exc))
            else:
                stdout = bytes(observed_stdout.get(process, b"")) + stdout_tail
                process_results[name] = (process.returncode, stdout, stderr)
    if process_failure is None:
        try:
            assert not cleanup_failures, cleanup_failures
            first_rc, first_stdout, first_stderr = process_results["first"]
            second_rc, second_stdout, second_stderr = process_results["second"]
            assert probe_state == "blocked"
            assert first_ready == "READY"
            assert second_ready == "READY"
            assert first_rc == 0, (first_stdout, first_stderr)
            assert second_rc == 19, (second_stdout, second_stderr)
            assert marker_a.exists()
            assert marker_b.exists()
            _assert_flock_state(process_store.lock_path, blocked=False)
            assert _snapshot(process_store, process_origin_a).iterations_used == 1
        except BaseException as exc:
            process_failure = exc
    if process_failure is not None:
        child_diagnostics = {
            name: {
                "rc": process.returncode,
                "stdout": process_results.get(name, (None, None, None))[1],
                "stderr": process_results.get(name, (None, None, None))[2],
            }
            for name, process in processes
        }
        raise AssertionError(
            f"process-flock failure: {process_failure!r}; "
            f"children={child_diagnostics!r}; cleanup={cleanup_failures!r}"
        ) from process_failure


def test_v05_prepared_changes_commitment_and_only_exact_request_resumes(tmp_path: Path) -> None:
    """V5 / M-A5/M-N6: durable prepare 中は別 operation を write 無し拒否。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    event = _batch_events()[0]
    reservation = _commit(
        store,
        origin,
        "prepare-reserve",
        _snapshot(store, origin).state_commitment,
        _reservation_for(event),
    )
    base = reservation.current_state_commitment
    before = _files(store, origin)
    def crash(label: str) -> None:
        if label == "head-prepared:fsynced":
            raise RuntimeError("prepared crash latch")
    ledger._FAULT_HOOK = crash
    try:
        try:
            _commit(store, origin, "prepare-a", base, event)
            assert False, "fault latch should interrupt after prepared fsync"
        except RuntimeError as exc:
            assert str(exc) == "prepared crash latch"
    finally:
        ledger._FAULT_HOOK = None
    prepared_snapshot = _snapshot(store, origin)
    assert prepared_snapshot.state_commitment != base
    assert prepared_snapshot.phase == "BATCH_RESERVED"
    prepared_bytes = _files(store, origin)
    try:
        _commit(store, origin, "prepare-b", prepared_snapshot.state_commitment, event)
        operation_b_accepted = True
    except ledger.RefluxOriginLedgerError:
        operation_b_accepted = False
    assert not operation_b_accepted
    assert _files(store, origin) == prepared_bytes
    altered = dataclasses.replace(
        event, members=tuple(reversed(event.members))
    )
    try:
        _commit(store, origin, "prepare-a", base, altered)
        altered_request_accepted = True
    except ledger.RefluxOriginLedgerError:
        altered_request_accepted = False
    assert not altered_request_accepted
    assert _files(store, origin) == prepared_bytes
    receipt = _commit(store, origin, "prepare-a", base, event)
    assert not receipt.replayed
    assert receipt.current_state_commitment != prepared_snapshot.state_commitment
    assert _files(store, origin) != before


def test_v06_historic_replay_and_committed_operation_identity(tmp_path: Path) -> None:
    """V6 / M-A1/M-N17: exact replay は historic/current を分離し bytes 不変。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    first, _, _ = _batch_events()
    reserved = _reservation_for(first)
    base_a = _snapshot(store, origin).state_commitment
    with ledger._locked(store) as authority:
        assert f"origin-opened:{origin}" in ledger._replay(store, authority).operation_ids
    receipt_a = _commit(store, origin, "operation-a", base_a, reserved)
    receipt_b = _commit(
        store, origin, "operation-b", receipt_a.current_state_commitment, first
    )
    before = _files(store, origin)
    committed_replay = _commit(
        store,
        origin,
        "operation-b",
        receipt_a.current_state_commitment,
        first,
    )
    assert committed_replay.replayed
    assert committed_replay.resulting_state_commitment == (
        receipt_b.resulting_state_commitment
    )
    assert committed_replay.current_state_commitment == (
        receipt_b.current_state_commitment
    )
    assert _files(store, origin) == before
    committed_identity = {
        member.candidate_commitment for member in first.members
    }
    replacement_commitment = next(
        _h(char) for char in "abcdef" if _h(char) not in committed_identity
    )
    altered_committed = dataclasses.replace(
        first,
        members=(
            dataclasses.replace(
                first.members[0], candidate_commitment=replacement_commitment
            ),
            *first.members[1:],
        ),
    )
    with Raises("reuse mismatch"):
        _commit(
            store,
            origin,
            "operation-b",
            receipt_a.current_state_commitment,
            altered_committed,
        )
    assert _files(store, origin) == before
    replay = _commit(store, origin, "operation-a", base_a, reserved)
    assert replay.replayed
    assert replay.resulting_state_commitment == receipt_a.resulting_state_commitment
    assert replay.current_state_commitment == receipt_b.current_state_commitment
    assert replay.resulting_state_commitment != replay.current_state_commitment
    assert _files(store, origin) == before
    with Raises("reuse mismatch"):
        _commit(store, origin, "operation-a", receipt_a.current_state_commitment, reserved)
    altered = dataclasses.replace(
        reserved, member_row_count=reserved.member_row_count + 1
    )
    with Raises("reuse mismatch"):
        _commit(store, origin, "operation-a", base_a, altered)
    with Raises("reserved"):
        _commit(store, origin, f"origin-opened:{origin}", receipt_b.current_state_commitment, altered)
    first_manifest = _manifest_object(series="cross-a", descriptor=_h("4"))
    second_manifest = _manifest_object(series="cross-b", descriptor=_h("d"))
    cross_repo, cross_origins = _repo(tmp_path / "cross-origin-op", [first_manifest, second_manifest])
    cross_store = _store(cross_repo)
    origin_a, origin_b = sorted(cross_origins)
    cross_event = _reservation_event("cross-op-batch")
    cross_base = _snapshot(cross_store, origin_a).state_commitment
    cross_receipt = _commit(cross_store, origin_a, "cross-origin-operation", cross_base, cross_event)
    with Raises("reuse mismatch"):
        _commit(
            cross_store,
            origin_b,
            "cross-origin-operation",
            cross_receipt.current_state_commitment,
            cross_event,
        )


def test_v07_batch_prefix_member_row_distinctness_and_single_inflight(tmp_path: Path) -> None:
    """V7 / M-N4: scalar count でなく event prefix が第二 in-flight を拒否。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    first = _reservation_event()
    base = _snapshot(store, origin).state_commitment
    receipt = _commit(store, origin, "batch-first", base, first)
    second = _reservation_event("batch-1", 1, 2, 2)
    with Raises("current phase"):
        _commit(store, origin, "batch-second", receipt.current_state_commitment, second)
    invalid_one = _reservation_event("one", member_row_count=1)
    fresh_repo, (fresh_origin,) = _repo(tmp_path / "fresh")
    fresh = _store(fresh_repo)
    fresh_base = _snapshot(fresh, fresh_origin).state_commitment
    with Raises("batch minimum"):
        _commit(fresh, fresh_origin, "one", fresh_base, invalid_one)
    duplicate = ledger.BatchCommitted("duplicate", 0, (
        ledger.CommittedBatchMember(0, _h("1")),
        ledger.CommittedBatchMember(1, _h("1")),
    ))
    duplicate_reservation = _commit(
        fresh,
        fresh_origin,
        "duplicate-reserve",
        fresh_base,
        _reservation_for(duplicate),
    )
    with Raises("candidate commitments"):
        _commit(
            fresh,
            fresh_origin,
            "duplicate",
            duplicate_reservation.current_state_commitment,
            duplicate,
        )
    with Raises("batch member row minimum"):
        _manifest(_manifest_object(member_row_min=1))


def test_v08_tombstone_no_refund_member_row_accounting_and_no_provider(tmp_path: Path) -> None:
    """V8 / M-N7: Q は member row 件、tombstone 後も I/Q は返却しない。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    tombstoned = _batch_events(
        outcomes=("tombstoned", "tombstoned"), constraints=(None, None)
    )
    receipts = _commit_batch_sequence(store, origin, tombstoned, "tomb")
    snap = _snapshot(store, origin)
    assert snap.iterations_used == 1
    assert snap.queries_used == 2
    assert snap.sealed_queries == 0
    assert snap.tombstoned_queries == 2
    assert (snap.forfeited_iterations, snap.forfeited_queries) == (0, 0)
    assert snap.tombstone_count == 1
    assert receipts[-1].current_state_commitment == snap.state_commitment
    source = Path(ledger.__file__).read_text(encoding="utf-8")
    assert "provider" not in {name for name in ledger.__dict__ if not name.startswith("__")}
    assert "qualification" not in source


def _crash_script(
    repo: Path,
    origin: str,
    base: str,
    point: str,
    reserved: ledger.BatchReserved,
) -> str:
    return f"""
import os,sys
sys.path.insert(0,{os.fspath(_ORCHESTRATOR.parent)!r})
from orchestrator.campaign import reflux_origin_ledger as l
s=l._fixture_store_for_test({os.fspath(repo)!r},'HEAD',initialize=False)
e=l.BatchReserved(
    {reserved.batch_id!r},
    {reserved.iteration_index!r},
    {reserved.member_row_count!r},
    {reserved.query_ordinal_start!r},
)
def hook(label):
    if label=={point!r}: os._exit(73)
l._FAULT_HOOK=hook
with l._locked(s) as a:
    l._commit_locked(s,a,origin_id={origin!r},operation_id='process-crash',expected_state_commitment={base!r},event=e)
"""


def test_v09_process_crash_boundaries_reopen_exactly_once(tmp_path: Path) -> None:
    """V9 / M-A5/M-N11/M-N16: process exit で kernel lock 解放、exact retry のみ継続。"""
    for index, point in enumerate((
        "head-prepared:fsynced", "origin-event:fsynced", "head-committed:fsynced"
    )):
        case = tmp_path / f"case-{index}"
        case.mkdir()
        repo, (origin,) = _repo(case)
        store = _store(repo)
        base = _snapshot(store, origin).state_commitment
        reserved = _reservation_event()
        completed = subprocess.run(
            [sys.executable, "-c", _crash_script(repo, origin, base, point, reserved)],
            cwd=repo,
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=SUBPROCESS_TIMEOUT,
        )
        assert completed.returncode == 73, (point, completed.stderr)
        crashed_snapshot = _snapshot(store, origin)
        if point != "head-committed:fsynced":
            assert crashed_snapshot.phase == "IDLE"
            assert crashed_snapshot.iterations_used == 0
            assert crashed_snapshot.queries_used == 0
        else:
            assert crashed_snapshot.phase == "BATCH_RESERVED"
            assert crashed_snapshot.iterations_used == 1
            assert crashed_snapshot.queries_used == 2
            assert (
                crashed_snapshot.reserved_batch_id,
                crashed_snapshot.reserved_iteration_index,
                crashed_snapshot.reserved_member_row_count,
                crashed_snapshot.reserved_query_ordinal_start,
            ) == ("batch-0", 0, 2, 0)
        with Raises():
            _commit(
                store,
                origin,
                "other-operation",
                _snapshot(store, origin).state_commitment,
                _reservation_event("other-batch"),
            )
        receipt = _commit(store, origin, "process-crash", base, reserved)
        assert receipt.event_index == 1
        with ledger._locked(store) as authority:
            replay = ledger._replay(store, authority)
        assert replay.committed_heads[origin][0] == 1
        assert len(replay.operations) == 1


def test_v10_short_write_fsync_fault_and_inode_recheck(tmp_path: Path) -> None:
    """V10: short write loop、fsync fault、flock 後 inode 一致検査。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    base = _snapshot(store, origin).state_commitment
    real_write = ledger.os.write
    write_calls = []
    def short_write(fd: int, raw: object) -> int:
        limited = raw[:max(1, len(raw) // 3)]
        count = real_write(fd, limited)
        write_calls.append(count)
        return count
    ledger.os.write = short_write
    try:
        receipt = _commit(store, origin, "short-write", base, _reservation_event())
    finally:
        ledger.os.write = real_write
    assert receipt.event_index == 1
    assert len(write_calls) > 3
    head_inode = store.head_path.stat().st_ino
    event_inode = store.origin_path(origin).stat().st_ino
    assert head_inode != event_inode
    lock_inode = store.lock_path.stat().st_ino
    with ledger._locked(store):
        assert store.lock_path.stat().st_ino == lock_inode
    inode_repo, (inode_origin,) = _repo(tmp_path / "inode-replace")
    inode_store = _store(inode_repo)
    replacement_locked = threading.Event()
    entered_after_retry = threading.Event()
    replacement_fd = -1
    replaced = False
    stale_lock = inode_store.lock_path.with_name("authority.lock.stale")
    def replace_inode(label: str) -> None:
        nonlocal replacement_fd, replaced
        if label != "lock:flocked" or replaced:
            return
        replaced = True
        inode_store.lock_path.rename(stale_lock)
        replacement_fd = os.open(inode_store.lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        fcntl.flock(replacement_fd, fcntl.LOCK_EX)
        replacement_locked.set()
    def acquire_after_replacement() -> None:
        with ledger._locked(inode_store):
            entered_after_retry.set()
    ledger._FAULT_HOOK = replace_inode
    inode_thread = threading.Thread(target=acquire_after_replacement)
    try:
        inode_thread.start()
        assert replacement_locked.wait(timeout=10)
        assert stale_lock.stat().st_ino != inode_store.lock_path.stat().st_ino
        _assert_flock_state(inode_store.lock_path, blocked=True)
        fcntl.flock(replacement_fd, fcntl.LOCK_UN)
        os.close(replacement_fd)
        replacement_fd = -1
    finally:
        ledger._FAULT_HOOK = None
        if replacement_fd >= 0:
            fcntl.flock(replacement_fd, fcntl.LOCK_UN)
            os.close(replacement_fd)
        inode_thread.join(timeout=10)
    assert not inode_thread.is_alive()
    assert entered_after_retry.is_set()
    _assert_flock_state(inode_store.lock_path, blocked=False)
    assert _snapshot(inode_store, inode_origin).origin_id == inode_origin
    fault_repo, (fault_origin,) = _repo(tmp_path / "fsync")
    fault_store = _store(fault_repo)
    fault_base = _snapshot(fault_store, fault_origin).state_commitment
    real_fsync = ledger.os.fsync
    failed = False
    def fail_once(fd: int) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("injected fsync fault")
        real_fsync(fd)
    ledger.os.fsync = fail_once
    try:
        with Raises("fsync failed"):
            _commit(fault_store, fault_origin, "fsync-fault", fault_base, _reservation_event())
    finally:
        ledger.os.fsync = real_fsync
    with Raises("poisoned"):
        _commit(fault_store, fault_origin, "fsync-fault", fault_base, _reservation_event())
    retry_repo, (fault_origin,) = _repo(tmp_path / "fsync-retry")
    fault_store = _store(retry_repo)
    fault_base = _snapshot(fault_store, fault_origin).state_commitment
    retry = _commit(fault_store, fault_origin, "fsync-fault", fault_base, _reservation_event())
    assert retry.event_index == 1
    for index, target in enumerate(("origin-event:written", "head-committed:written")):
        case = tmp_path / f"fsync-{index}"
        case.mkdir()
        case_repo, (case_origin,) = _repo(case)
        case_store = _store(case_repo)
        case_base = _snapshot(case_store, case_origin).state_commitment
        armed = failed_target = False
        real_fsync = ledger.os.fsync
        def arm(label: str) -> None:
            nonlocal armed
            if label == target:
                armed = True
        def fail_target(fd: int) -> None:
            nonlocal failed_target
            if armed and not failed_target:
                failed_target = True
                raise OSError("injected targeted fsync fault")
            real_fsync(fd)
        ledger._FAULT_HOOK = arm
        ledger.os.fsync = fail_target
        try:
            with Raises("fsync failed"):
                _commit(case_store, case_origin, f"fsync-target-{index}", case_base, _reservation_event())
        finally:
            ledger.os.fsync = real_fsync
            ledger._FAULT_HOOK = None
        assert failed_target
        with Raises("poisoned"):
            _snapshot(case_store, case_origin)


def test_v11_authorized_partial_tail_offsets_and_unrelated_tail_rejected(tmp_path: Path) -> None:
    """V11 / M-A4/M-N11r: 検証済み prefix へ修復し receipt は増やさない。"""
    for index, cut in enumerate((1, 17, 83)):
        case = tmp_path / f"offset-{index}"
        case.mkdir()
        repo, (origin,) = _repo(case)
        store = _store(repo)
        base = _snapshot(store, origin).state_commitment
        event = _reservation_event()
        def crash(label: str) -> None:
            if label == "head-prepared:fsynced":
                raise RuntimeError("stop")
        ledger._FAULT_HOOK = crash
        try:
            try:
                _commit(store, origin, "partial-op", base, event)
            except RuntimeError:
                pass
        finally:
            ledger._FAULT_HOOK = None
        with ledger._locked(store) as authority:
            replay = ledger._replay(store, authority)
            _, _, _, frame, _ = ledger._build_event_for_current_head(
                replay=replay, origin_id=origin, operation_id="partial-op", event=event
            )
        with store.origin_path(origin).open("ab") as stream:
            stream.write(frame[:min(cut, len(frame) - 1)])
            stream.flush(); os.fsync(stream.fileno())
        receipt = _commit(store, origin, "partial-op", base, event)
        assert receipt.event_index == 1
        with ledger._locked(store) as authority:
            replay = ledger._replay(store, authority)
        assert len(replay.operations) == 1
        assert len(replay.head_data.records) == 3
    bad_case = tmp_path / "bad"
    bad_case.mkdir()
    repo, (origin,) = _repo(bad_case)
    store = _store(repo)
    with store.head_path.open("ab") as stream:
        stream.write(b"\xff")
        stream.flush(); os.fsync(stream.fileno())
    with Raises("non-ASCII"):
        _snapshot(store, origin)
    unrelated_case = tmp_path / "unrelated-head"
    unrelated_case.mkdir()
    repo, (origin,) = _repo(unrelated_case)
    store = _store(repo)
    clean_base = _snapshot(store, origin).state_commitment
    unrelated_event = _reservation_event()
    with store.head_path.open("ab") as stream:
        stream.write(b'{"unrelated":')
        stream.flush(); os.fsync(stream.fileno())
    reopened_store = _store(repo)
    observed = _snapshot(reopened_store, origin).state_commitment
    assert observed == clean_base
    assert reopened_store.head_path.read_bytes().endswith(b"\n")
    repaired_unrelated = _commit(
        reopened_store, origin, "unrelated-tail", clean_base, unrelated_event
    )
    assert repaired_unrelated.event_index == 1
    head_case = tmp_path / "head-partial"
    head_case.mkdir()
    repo, (origin,) = _repo(head_case)
    store = _store(repo)
    base = _snapshot(store, origin).state_commitment
    head_partial_event = _reservation_event()
    real_write_all = ledger._write_all
    def partial_prepare(fd: int, raw: bytes) -> None:
        os.write(fd, raw[:37])
        raise OSError("injected partial prepare")
    ledger._write_all = partial_prepare
    try:
        with Raises("fsync failed"):
            _commit(store, origin, "head-partial", base, head_partial_event)
    finally:
        ledger._write_all = real_write_all
    reopened_store = _store(repo)
    observed = _snapshot(reopened_store, origin).state_commitment
    assert observed == base
    assert reopened_store.head_path.read_bytes().endswith(b"\n")
    repaired = _commit(reopened_store, origin, "head-partial", base, head_partial_event)
    assert repaired.event_index == 1
    exact_replay = _commit(reopened_store, origin, "head-partial", base, head_partial_event)
    assert exact_replay.replayed
    assert exact_replay.resulting_state_commitment == repaired.resulting_state_commitment
    missing_committed_case = tmp_path / "missing-committed-event"
    missing_committed_case.mkdir()
    repo, (origin,) = _repo(missing_committed_case)
    store = _store(repo)
    with ledger._locked(store) as authority:
        fresh_replay = ledger._replay(store, authority)
        with Raises("points outside"):
            ledger._replay_state_prefix(
                authority=authority,
                parsed_events=fresh_replay.parsed_events,
                committed_heads={origin: (1, _h("f"))},
            )
    _commit(
        store,
        origin,
        "committed-before-delete",
        _snapshot(store, origin).state_commitment,
        _reservation_event(),
    )
    event_frames = store.origin_path(origin).read_bytes().splitlines(keepends=True)
    assert len(event_frames) == 2
    store.origin_path(origin).write_bytes(event_frames[0])
    with Raises("points outside"):
        _snapshot(store, origin)
    zero_case = tmp_path / "zero-ledger"
    zero_case.mkdir()
    repo, (origin,) = _repo(zero_case)
    store = _store(repo)
    store.origin_path(origin).write_bytes(b"")
    with Raises("zero-byte"):
        _snapshot(store, origin)
    corrupt_case = tmp_path / "corrupt-prefix"
    corrupt_case.mkdir()
    repo, (origin,) = _repo(corrupt_case)
    store = _store(repo)
    records = [json.loads(line) for line in store.head_path.read_bytes().splitlines()]
    records[0]["record_sha256"] = _h("f")
    store.head_path.write_bytes(_canonical(records[0]) + b"\n{" )
    with Raises("digest mismatch"):
        _commit(store, origin, "corrupt-prefix", _h("1"), _reservation_event())


def test_v12_git_anchor_symbolic_head_env_scrub_and_authority_version(tmp_path: Path) -> None:
    """V12 / M-N9/M-N18: HEAD を一度 OID 化、working tree tamper と version mismatch を拒否。"""
    repo, (origin,) = _repo(tmp_path)
    malicious = tmp_path / "malicious.git"
    malicious.mkdir()
    old_git_dir = os.environ.get("GIT_DIR")
    os.environ["GIT_DIR"] = os.fspath(malicious)
    try:
        store = ledger._fixture_store_for_test(repo, "HEAD")
        assert _snapshot(store, origin).origin_id == origin
    finally:
        if old_git_dir is None:
            os.environ.pop("GIT_DIR", None)
        else:
            os.environ["GIT_DIR"] = old_git_dir
    authority_path = repo / AUTHORITY_PATH
    committed = authority_path.read_bytes()
    authority_path.write_bytes(committed.replace(b"series-a", b"series-z"))
    with Raises("differs from committed"):
        _snapshot(store, origin)
    authority_path.write_bytes(committed)
    with Raises("Git observation failed"):
        ledger._fixture_store_for_test(repo, "HEAD~1", initialize=False)
    head_doc = [json.loads(line) for line in store.head_path.read_text().splitlines()]
    head_doc[0]["payload"]["authority_blob_sha256"] = _h("f")
    core = {key: value for key, value in head_doc[0].items() if key != "record_sha256"}
    head_doc[0]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    store.head_path.write_bytes(b"".join(_canonical(item) + b"\n" for item in head_doc))
    with Raises("authority version mismatch"):
        _snapshot(store, origin)


def test_v12_production_path_in_subprocess_temp_repository(tmp_path: Path) -> None:
    """Δ13 production route: copied module resolves symbolic HEAD inside the temp repo."""
    source_root = Path(ledger.__file__).resolve().parents[2]
    repo = tmp_path / "production-repo"
    repo.mkdir()
    for relative in (
        "orchestrator/campaign/__init__.py",
        "orchestrator/campaign/reflux_origin_ledger.py",
        "orchestrator/campaign/reflux_ir.py",
        "orchestrator/campaign/axis_trigger_gating.py",
        "orchestrator/campaign/pin.py",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / relative, target)
    raw = _manifest_object()
    authority_path = repo / AUTHORITY_PATH
    authority_path.write_bytes(_authority_bytes([raw]))
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Origin Test")
    _git(repo, "config", "user.email", "origin@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "production fixture")
    origin = _independent_origin(raw)
    script = f"""
import sys
sys.path.insert(0,{os.fspath(repo)!r})
from orchestrator.campaign import reflux_origin_ledger as l
l._fixture_store_for_test({os.fspath(repo)!r},'HEAD')
def forbidden_hook(label):
    raise RuntimeError('fixture hook reached production path')
l._FAULT_HOOK=forbidden_hook
s=l.read_origin({origin!r})
assert s.origin_id=={origin!r}
print(s.phase)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=repo, env=_git_env(),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    assert completed.stdout == b"IDLE\n"


def test_v13_global_chain_interleave_delete_reorder_and_cross_binding(tmp_path: Path) -> None:
    """V13 / M-A6: global previous digest と prepared/event/commit の対応を固定。"""
    first = _manifest_object(series="series-a", descriptor=_h("4"))
    second = _manifest_object(series="series-b", descriptor=_h("d"))
    repo, origins = _repo(tmp_path, [first, second])
    store = _store(repo)
    origin_a, origin_b = sorted(origins)
    base = _snapshot(store, origin_a).state_commitment
    events_a = _batch_events("a")
    events_b = _batch_events("b")
    receipt_a = _commit(
        store, origin_a, "interleave-a", base, _reservation_for(events_a[0])
    )
    receipt_b = _commit(
        store,
        origin_b,
        "interleave-b",
        receipt_a.current_state_commitment,
        _reservation_for(events_b[0]),
    )
    _commit(store, origin_a, "interleave-a2", receipt_b.current_state_commitment,
            events_a[0])
    original = store.head_path.read_bytes()
    lines = original.splitlines(keepends=True)
    assert len(lines) == 7
    store.head_path.write_bytes(b"".join(lines[:3] + lines[5:]))
    with Raises():
        _snapshot(store, origin_a)
    store.head_path.write_bytes(original)
    records = [json.loads(line) for line in original.splitlines()]
    records[4]["payload"]["prepared_record_sha256"] = records[1]["record_sha256"]
    core = {key: value for key, value in records[4].items() if key != "record_sha256"}
    records[4]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    records[5]["previous_record_sha256"] = records[4]["record_sha256"]
    core = {key: value for key, value in records[5].items() if key != "record_sha256"}
    records[5]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    records[6]["previous_record_sha256"] = records[5]["record_sha256"]
    records[6]["payload"]["prepared_record_sha256"] = records[5]["record_sha256"]
    core = {key: value for key, value in records[6].items() if key != "record_sha256"}
    records[6]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    store.head_path.write_bytes(b"".join(_canonical(item) + b"\n" for item in records))
    with Raises():
        _snapshot(store, origin_a)
    records = [json.loads(line) for line in original.splitlines()]
    # Rewrite B and the final A transaction into two internally consistent
    # per-origin chains.  Only the global previous-record rule should reject it.
    records[3]["previous_record_sha256"] = records[0]["record_sha256"]
    core = {key: value for key, value in records[3].items() if key != "record_sha256"}
    records[3]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    records[4]["previous_record_sha256"] = records[3]["record_sha256"]
    records[4]["payload"]["prepared_record_sha256"] = records[3]["record_sha256"]
    core = {key: value for key, value in records[4].items() if key != "record_sha256"}
    records[4]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    origin_event_records = {
        origin_a: [json.loads(line) for line in store.origin_path(origin_a).read_bytes().splitlines()],
        origin_b: [json.loads(line) for line in store.origin_path(origin_b).read_bytes().splitlines()],
    }
    semantic_by_origin = {}
    for item_origin, batch_id in ((origin_a, "a"), (origin_b, "b")):
        reserved_payload = origin_event_records[item_origin][1]["payload"]
        semantic_by_origin[item_origin] = {
            "phase": "BATCH_RESERVED",
            "iterations_used": 1,
            "queries_used": 2,
            "sealed_queries": 0,
            "tombstoned_queries": 0,
            "forfeited_iterations": 0,
            "forfeited_queries": 0,
            "sealed_member_row_count": 0,
            "origin_distinct_candidate_count": 0,
            "origin_sealed_distinct_candidate_count": 0,
            "batch_count": 0,
            "tombstone_count": 0,
            "open_batch": {
                "batch_id": batch_id,
                "iteration_index": reserved_payload["iteration_index"],
                "member_row_count": reserved_payload["member_row_count"],
                "query_ordinal_start": reserved_payload["query_ordinal_start"],
                "members": None,
            },
            "sealed_batch_ids": [],
            "seen_batch_ids": [batch_id],
            "rejected_constraints": [],
            "seen_salts": [],
            "terminal_status": None,
            "constraint_class": [],
        }
    global_base_preimage = {
        "authority_blob_sha256": hashlib.sha256(_authority_bytes([first, second])).hexdigest(),
        "runtime_head_record_index": records[4]["record_index"],
        "runtime_head_record_sha256": records[4]["record_sha256"],
        "head_file_byte_length": sum(len(_canonical(item)) + 1 for item in records[:5]),
        "head_partial_tail_sha256": None,
        "transaction_phase": "clean",
        "prepared_record_sha256": None,
        "prepared_request_sha256": None,
        "origins": [[
            item_origin,
            1,
            origin_event_records[item_origin][1]["event_sha256"],
            hashlib.sha256(_canonical(semantic_by_origin[item_origin])).hexdigest(),
        ] for item_origin in sorted((origin_a, origin_b))],
    }
    rewritten_base = hashlib.sha256(
        b"izanagi-reflux-origin-state/v2\0" + _canonical(global_base_preimage)
    ).hexdigest()
    a2_event = origin_event_records[origin_a][2]
    rewritten_request = hashlib.sha256(_canonical({
        "base_state_commitment": rewritten_base,
        "origin_id": origin_a,
        "operation_id": "interleave-a2",
        "event_type": a2_event["event_type"],
        "payload": a2_event["payload"],
    })).hexdigest()
    records[5]["previous_record_sha256"] = records[2]["record_sha256"]
    records[5]["payload"]["base_state_commitment"] = rewritten_base
    records[5]["payload"]["request_sha256"] = rewritten_request
    core = {key: value for key, value in records[5].items() if key != "record_sha256"}
    records[5]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    records[6]["previous_record_sha256"] = records[5]["record_sha256"]
    records[6]["payload"]["prepared_record_sha256"] = records[5]["record_sha256"]
    core = {key: value for key, value in records[6].items() if key != "record_sha256"}
    records[6]["record_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    store.head_path.write_bytes(b"".join(_canonical(item) + b"\n" for item in records))
    with Raises("runtime head chain mismatch"):
        _snapshot(store, origin_a)


def test_v14_i_q_k_sealed_evidence_row_proxy_floor_not_physical_query_and_aborted_seal(
    tmp_path: Path,
) -> None:
    """V14 / M-A3/M-N8/M-N13: I/Q/K と floor を独立値で境界検査。"""
    invalid = _manifest_object(floor_per_round=0)
    with Raises():
        _manifest(invalid)
    empty_floors = _manifest_object()
    empty_floors["budget_policy"]["query_floor_constraints"] = []
    with Raises("non-empty"):
        _manifest(empty_floors)
    invalid = _manifest_object(schema="unknown-ir/v9")
    with Raises("unknown candidate IR"):
        _manifest(invalid)
    first_only = _manifest_object()
    first_only["budget_policy"]["query_floor_constraints"].append({
        "formula_id": FORMULA,
        "base_queries": 8,
        "queries_per_round": 1,
        "rounds": 1,
        "evidence_min": 0,
    })
    with Raises("outside authority budget"):
        _manifest(first_only)
    with Raises("partitioned"):
        _manifest(_manifest_object(
            imax=1,
            qmax=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
            floor_per_round=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
        ))
    with Raises("batch minimum exceeds codec feasibility"):
        _manifest(_manifest_object(
            imax=2,
            qmax=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
            member_row_min=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
            floor_per_round=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
        ))
    with Raises("partitioned"):
        _manifest(_manifest_object(
            imax=1, qmax=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1
        ))
    with Raises("Kmax exceeds codec feasibility"):
        _manifest(_manifest_object(kmax=ledger._MAX_CLASS_CARDINALITY + 1))
    partitioned = _manifest_object(
        imax=2,
        qmax=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
        member_row_min=2,
        floor_per_round=ledger._MAX_BATCH_MEMBER_ROW_COUNT + 1,
    )
    _manifest(partitioned)
    raw = _manifest_object(imax=1, qmax=4, kmax=0)
    repo, (origin,) = _repo(tmp_path, [raw])
    store = _store(repo)
    committed, prepared, sealed = _batch_events(outcomes=("accepted", "accepted"), constraints=(None, None))
    receipts = _commit_batch_sequence(
        store, origin, (committed, prepared, sealed), "limits"
    )
    cert = ledger.OriginSealed(False, (), 1, 0, 2, 0, 0, 0)
    _commit(store, origin, "certifiable", receipts[-1].current_state_commitment, cert)
    over_repo, (over_origin,) = _repo(tmp_path / "over", [raw])
    over = _store(over_repo)
    full_tombstone = _batch_events(
        outcomes=("tombstoned", "tombstoned"), constraints=(None, None)
    )
    tomb_receipts = _commit_batch_sequence(
        over, over_origin, full_tombstone, "first"
    )
    with Raises("Imax"):
        _commit(over, over_origin, "second", tomb_receipts[-1].current_state_commitment,
                _reservation_event("batch-1", iteration=1, query_start=2))
    qraw = _manifest_object(imax=2, qmax=2)
    qrepo, (qorigin,) = _repo(tmp_path / "q-over", [qraw])
    qstore = _store(qrepo)
    qtomb = _commit_batch_sequence(qstore, qorigin, full_tombstone, "q")[-1]
    with Raises("Qmax"):
        _commit(qstore, qorigin, "q-second", qtomb.current_state_commitment,
                _reservation_event("batch-1", iteration=1, query_start=2))
    low = _manifest_object(imax=2, qmax=4, floor_per_round=4)
    low_repo, (low_origin,) = _repo(tmp_path / "low", [low])
    low_store = _store(low_repo)
    tomb_receipts = _commit_batch_sequence(
        low_store, low_origin, full_tombstone, "low"
    )
    second_tomb = _commit_batch_sequence(
        low_store,
        low_origin,
        _batch_events(
            "batch-1", iteration=1, query_start=2,
            prior_replicates={b"10000": 1, b"01000": 1},
            outcomes=("tombstoned", "tombstoned"), constraints=(None, None),
        ),
        "low-second",
    )
    tombstoned_floor = _snapshot(low_store, low_origin)
    assert tombstoned_floor.sealed_queries == 0
    assert tombstoned_floor.tombstoned_queries == 4
    with Raises("floor"):
        _commit(low_store, low_origin, "early-cert", second_tomb[-1].current_state_commitment,
                ledger.OriginSealed(False, (), 2, 2, 0, 4, 0, 0))
    _commit(low_store, low_origin, "abort", second_tomb[-1].current_state_commitment,
            ledger.OriginSealed(True, (), 2, 2, 0, 4, 0, 0))
    kraw = _manifest_object(imax=1, qmax=2, kmax=0)
    krepo, (korigin,) = _repo(tmp_path / "k-over", [kraw])
    kstore = _store(krepo)
    kreceipts = _commit_batch_sequence(kstore, korigin, _batch_events(), "k")
    with Raises("Kmax"):
        _commit(kstore, korigin, "k-seal", kreceipts[-1].current_state_commitment,
                ledger.OriginSealed(False, (_h("d"),), 1, 0, 2, 0, 0, 0))


def test_v15_strict_authority_event_json_paths_types_and_limits(tmp_path: Path) -> None:
    """V15 / M-N12: extra/missing/duplicate key、bool、path、symlink、size を拒否。"""
    production_authority = (
        Path(ledger.__file__).with_name("reflux_origin_authority_v2.json").read_bytes()
    )
    parsed_production = ledger._authority_from_bytes(production_authority)
    assert dict(parsed_production.entries) == {}
    assert json.loads(production_authority)["authority_schema"] == (
        "izanagi-reflux-origin-authority/v2"
    )
    raw = _manifest_object()
    legacy_budget = json.loads(json.dumps(raw))
    legacy_policy = legacy_budget["budget_policy"]
    legacy_cardinality = legacy_policy.pop("batch_member_row_count_min")
    legacy_policy.pop("batch_distinct_candidate_count_min")
    legacy_policy["batch_cardinality_min"] = legacy_cardinality
    with Raises("keys"):
        _manifest(legacy_budget)
    malformed = json.loads(json.dumps(raw)); malformed["extra"] = 1
    with Raises("keys"):
        _manifest(malformed)
    malformed = json.loads(json.dumps(raw)); malformed["budget_policy"]["imax"] = True
    with Raises("Imax"):
        _manifest(malformed)
    malformed = json.loads(json.dumps(raw)); malformed["stock_certification_ref"]["path"] = "../stock"
    with Raises("path"):
        _manifest(malformed)
    malformed = json.loads(json.dumps(raw)); malformed["stock_certification_ref"]["path"] = "/absolute/stock"
    with Raises("path"):
        _manifest(malformed)
    malformed = json.loads(json.dumps(raw)); malformed.pop("role_bundle_sha256")
    with Raises("keys"):
        _manifest(malformed)
    malformed = json.loads(json.dumps(raw)); malformed["ccbench_commit_oid"] = "2" * 39
    with Raises("CCBench commit OID"):
        _manifest(malformed)
    duplicate = b'{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[],"origins":[]}\n'
    with Raises("duplicate"):
        ledger._authority_from_bytes(duplicate)
    missing_authority = _canonical({"authority_schema": ledger.AUTHORITY_SCHEMA_ID}) + b"\n"
    with Raises("keys"):
        ledger._authority_from_bytes(missing_authority)
    with Raises("oversize authority"):
        ledger._authority_from_bytes(b"x" * ((8 << 20) + 1))
    reserved_type, reserved_payload = ledger._event_payload(_reservation_event())
    assert reserved_type == "batch-reserved"
    malformed_reservations = [{**reserved_payload, "extra": 1}]
    malformed_reservations.extend(
        {
            key: value
            for key, value in reserved_payload.items()
            if key != missing
        }
        for missing in reserved_payload
    )
    malformed_reservations.extend(
        {**reserved_payload, key: True} for key in reserved_payload
    )
    for altered in malformed_reservations:
        with Raises():
            ledger._event_from_payload(reserved_type, altered)
    committed_type, committed_payload = ledger._event_payload(
        _batch_events()[0]
    )
    for event_type, payload in (
        (reserved_type, reserved_payload),
        (committed_type, committed_payload),
    ):
        legacy_payload = {
            key: value
            for key, value in payload.items()
            if key != "member_row_count"
        }
        legacy_payload["cardinality"] = payload["member_row_count"]
        with Raises("keys"):
            ledger._event_from_payload(event_type, legacy_payload)
    assert {
        field.name for field in dataclasses.fields(ledger.BatchSealed)
    } == {"batch_id", "members"}
    sealed_event = _batch_events(
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )[2]
    sealed_type, sealed_payload = ledger._event_payload(sealed_event)
    assert sealed_type == "batch-sealed"
    assert sealed_payload["member_row_count"] == 2
    assert sealed_payload["distinct_candidate_count"] == 1
    assert sealed_payload["sealed_distinct_candidate_count"] == 1
    assert ledger._event_from_payload(sealed_type, sealed_payload) == sealed_event
    for field, reason in (
        ("member_row_count", "member row count mismatch"),
        ("distinct_candidate_count", "distinct candidate count mismatch"),
        (
            "sealed_distinct_candidate_count",
            "executed distinct candidate count mismatch",
        ),
    ):
        with Raises(reason):
            ledger._event_from_payload(
                sealed_type,
                {**sealed_payload, field: int(sealed_payload[field]) + 1},
            )
        with Raises("keys"):
            ledger._event_from_payload(
                sealed_type,
                {
                    key: value
                    for key, value in sealed_payload.items()
                    if key != field
                },
            )
    legacy_sealed_payload = {
        key: value
        for key, value in sealed_payload.items()
        if key not in {
            "member_row_count",
            "distinct_candidate_count",
            "sealed_distinct_candidate_count",
        }
    }
    with Raises("keys"):
        ledger._event_from_payload(sealed_type, legacy_sealed_payload)
    abandoned_type, abandoned_payload = ledger._event_payload(
        ledger.BatchReservationAbandoned("batch-0")
    )
    assert abandoned_type == "batch-reservation-abandoned"
    for altered in (
        {**abandoned_payload, "extra": 1},
        {},
        {"batch_id": True},
    ):
        with Raises():
            ledger._event_from_payload(abandoned_type, altered)
    origin_seal = ledger.OriginSealed(
        False, (_h("d"),), 3, 1, 4, 2, 5, 7
    )
    origin_type, origin_payload = ledger._event_payload(origin_seal)
    assert origin_type == "origin-sealed"
    assert set(origin_payload) == {
        "seal_kind",
        "constraint_class_sha256s",
        "batch_count",
        "tombstone_count",
        "sealed_queries",
        "tombstoned_queries",
        "forfeited_iterations",
        "forfeited_queries",
    }
    assert ledger._event_from_payload(origin_type, origin_payload) == origin_seal
    old_six_field = {
        key: value
        for key, value in origin_payload.items()
        if key not in {"forfeited_iterations", "forfeited_queries"}
    }
    with Raises("keys"):
        ledger._event_from_payload(origin_type, old_six_field)
    for field in ("forfeited_iterations", "forfeited_queries"):
        with Raises("keys"):
            ledger._event_from_payload(
                origin_type,
                {key: value for key, value in origin_payload.items() if key != field},
            )
        with Raises(field.replace("_", " ")):
            ledger._event_from_payload(
                origin_type,
                {**origin_payload, field: True},
            )
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    real_lock = store.lock_path
    replacement = real_lock.with_name("replacement.lock")
    real_lock.rename(replacement)
    real_lock.symlink_to(replacement.name)
    with Raises("authority lock"):
        _snapshot(store, origin)
    for name, transform in (
        ("event-extra", lambda raw_event: _canonical({**json.loads(raw_event), "extra": 1}) + b"\n"),
        ("event-missing", lambda raw_event: _canonical({
            key: value for key, value in json.loads(raw_event).items() if key != "event_type"
        }) + b"\n"),
        ("event-duplicate", lambda raw_event: b'{"event_index":0,' + raw_event[1:]),
        ("event-noncanonical", lambda raw_event: b"{ " + raw_event[1:]),
        ("event-no-lf", lambda raw_event: raw_event.rstrip(b"\n")),
    ):
        case = tmp_path / name
        case.mkdir()
        case_repo, (case_origin,) = _repo(case)
        case_store = _store(case_repo)
        original_event = case_store.origin_path(case_origin).read_bytes()
        case_store.origin_path(case_origin).write_bytes(transform(original_event))
        with Raises():
            _snapshot(case_store, case_origin)
    ancestor_case = tmp_path / "runtime-ancestor"
    ancestor_case.mkdir()
    ancestor_repo, (ancestor_origin,) = _repo(ancestor_case)
    ancestor_store = _store(ancestor_repo)
    real_runtime = ancestor_store.runtime_root.with_name("v2-real")
    ancestor_store.runtime_root.rename(real_runtime)
    ancestor_store.runtime_root.symlink_to(real_runtime.name)
    with Raises("real directory"):
        _snapshot(ancestor_store, ancestor_origin)
    authority_ancestor_case = tmp_path / "authority-ancestor"
    authority_ancestor_case.mkdir()
    authority_repo, (authority_origin,) = _repo(authority_ancestor_case)
    authority_store = _store(authority_repo)
    orchestrator_path = authority_repo / "orchestrator"
    real_orchestrator = authority_repo / "orchestrator-real"
    orchestrator_path.rename(real_orchestrator)
    orchestrator_path.symlink_to(real_orchestrator.name)
    with Raises("ancestor"):
        _snapshot(authority_store, authority_origin)
    authority_final_case = tmp_path / "authority-final-symlink"
    authority_final_case.mkdir()
    authority_final_repo, (authority_final_origin,) = _repo(authority_final_case)
    authority_final_store = _store(authority_final_repo)
    authority_final_path = authority_final_store.authority_path
    authority_real_path = authority_final_path.with_name("authority-real.json")
    authority_final_path.rename(authority_real_path)
    authority_final_path.symlink_to(authority_real_path.name)
    with Raises("cannot open authority"):
        _snapshot(authority_final_store, authority_final_origin)
    event_final_case = tmp_path / "event-final-symlink"
    event_final_case.mkdir()
    event_final_repo, (event_final_origin,) = _repo(event_final_case)
    event_final_store = _store(event_final_repo)
    event_final_path = event_final_store.origin_path(event_final_origin)
    event_real_path = event_final_path.with_name("events-real.jsonl")
    event_final_path.rename(event_real_path)
    event_final_path.symlink_to(event_real_path.name)
    with Raises("cannot open origin ledger"):
        _snapshot(event_final_store, event_final_origin)
    nonregular_case = tmp_path / "nonregular"
    nonregular_case.mkdir()
    nonregular_repo, (nonregular_origin,) = _repo(nonregular_case)
    nonregular_store = _store(nonregular_repo)
    nonregular_store.head_path.unlink()
    nonregular_store.head_path.mkdir()
    with Raises("size or type"):
        _snapshot(nonregular_store, nonregular_origin)
    fifo_repo, (fifo_origin,) = _repo(tmp_path / "fifo")
    fifo_store = _store(fifo_repo)
    fifo_store.head_path.unlink()
    os.mkfifo(fifo_store.head_path, 0o600)
    fifo_script = f"""
import os,sys
from pathlib import Path
sys.path.insert(0,{os.fspath(_ORCHESTRATOR.parent)!r})
from orchestrator.campaign import reflux_origin_ledger as l
try:
    s=l._fixture_store_for_test(Path({os.fspath(fifo_repo)!r}),'HEAD',initialize=False)
    with l._locked(s) as a:
        l._read_origin_locked(s,a,{fifo_origin!r})
except l.RefluxOriginLedgerError:
    sys.exit(0)
sys.exit(1)
"""
    fifo_result = subprocess.run(
        [sys.executable, "-c", fifo_script],
        cwd=fifo_repo,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
    )
    assert fifo_result.returncode == 0, fifo_result.stderr.decode("utf-8", errors="replace")
    oversize_repo, (oversize_origin,) = _repo(tmp_path / "oversize")
    oversize_store = _store(oversize_repo)
    with oversize_store.head_path.open("ab") as stream:
        stream.write(b"x" * ((1 << 20) + 1))
        stream.flush(); os.fsync(stream.fileno())
    with Raises("oversize partial"):
        _snapshot(oversize_store, oversize_origin)
    full_record_repo, (full_record_origin,) = _repo(tmp_path / "oversize-full")
    full_record_store = _store(full_record_repo)
    with full_record_store.head_path.open("ab") as stream:
        stream.write(b'"' + b"x" * (1 << 20) + b'"\n')
        stream.flush(); os.fsync(stream.fileno())
    with Raises("record framing"):
        _snapshot(full_record_store, full_record_origin)


def test_v16_commit_reveal_privacy_order_exact_class_and_positive_cycle(tmp_path: Path) -> None:
    """V16 / M-N5/M-N10/M-N14/M-N15: full positive cycle と reveal/exact-set 負例。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    committed, prepared, sealed = _batch_events()
    reservation = _commit(
        store,
        origin,
        "positive-0",
        _snapshot(store, origin).state_commitment,
        _reservation_for(committed),
    )
    first = _commit(
        store, origin, "positive-1", reservation.current_state_commitment, committed
    )
    second = _commit(
        store, origin, "positive-2", first.current_state_commitment, prepared
    )
    prepared_snapshot = _snapshot(store, origin)
    assert prepared_snapshot.phase == "RESULTS_PREPARED"
    assert prepared_snapshot.origin_distinct_candidate_count == 0
    assert not hasattr(prepared_snapshot, "outcomes")
    assert not hasattr(second, "outcomes")
    visible = repr(dataclasses.asdict(prepared_snapshot)) + repr(dataclasses.asdict(second))
    possible_plaintexts = []
    for mask in range(32):
        possible_plaintexts.append(tuple(
            "rejected" if mask & (1 << bit) else "accepted" for bit in range(5)
        ))
    assert len(set(possible_plaintexts)) == 32
    assert all(repr(assignment) not in visible for assignment in possible_plaintexts)
    assert "accepted" not in visible and "rejected" not in visible
    assert "evidence_digest" not in visible and "constraint_sha256" not in visible
    with Raises("not sealed"):
        with ledger._locked(store) as authority:
            ledger._read_sealed_batch_locked(store, authority, origin, "batch-0")
    wrong = dataclasses.replace(
        sealed,
        members=(
            dataclasses.replace(
                sealed.members[0], candidate_salt="f" * 32
            ),
            sealed.members[1],
        ),
    )
    with Raises("opening mismatch"):
        _commit(store, origin, "wrong-open", second.current_state_commitment, wrong)
    third = _commit(store, origin, "positive-3", second.current_state_commitment, sealed)
    assert _snapshot(store, origin).origin_distinct_candidate_count == 2
    with ledger._locked(store) as authority:
        revealed = ledger._read_sealed_batch_locked(store, authority, origin, "batch-0")
    assert tuple(member.outcome for member in revealed.members) == ("accepted", "rejected")
    partial = ledger.OriginSealed(False, (), 1, 0, 2, 0, 0, 0)
    with Raises("exact rejected set"):
        _commit(store, origin, "partial-class", third.current_state_commitment, partial)
    final = _commit(store, origin, "positive-4", third.current_state_commitment,
                    ledger.OriginSealed(False, (_h("d"),), 1, 0, 2, 0, 0, 0))
    assert _snapshot(store, origin).terminal_status == "certifiable"
    assert final.event_index == 5
    order_repo, (order_origin,) = _repo(tmp_path / "result-order")
    order_store = _store(order_repo)
    ordered = _batch_events(outcomes=("accepted", "accepted"), constraints=(None, None))
    order_reserved = _commit(
        order_store,
        order_origin,
        "order-0",
        _snapshot(order_store, order_origin).state_commitment,
        _reservation_for(ordered[0]),
    )
    order_first = _commit(
        order_store,
        order_origin,
        "order-1",
        order_reserved.current_state_commitment,
        ordered[0],
    )
    misordered_prepared = dataclasses.replace(
        ordered[1], members=tuple(reversed(ordered[1].members))
    )
    with Raises("do not match"):
        _commit(
            order_store,
            order_origin,
            "misordered-prepared",
            order_first.current_state_commitment,
            misordered_prepared,
        )
    order_second = _commit(
        order_store,
        order_origin,
        "order-2",
        order_first.current_state_commitment,
        ordered[1],
    )
    reveal = ordered[2]
    misordered = dataclasses.replace(reveal, members=(
        dataclasses.replace(
            reveal.members[0],
            result_evidence_salt=reveal.members[1].result_evidence_salt,
            evidence_digest=reveal.members[1].evidence_digest,
        ),
        dataclasses.replace(
            reveal.members[1],
            result_evidence_salt=reveal.members[0].result_evidence_salt,
            evidence_digest=reveal.members[0].evidence_digest,
        ),
    ))
    with Raises("opening mismatch"):
        _commit(order_store, order_origin, "misordered-result",
                order_second.current_state_commitment, misordered)


def test_v16_salt_contract_and_observer_reconstructs_preseal_bytes(tmp_path: Path) -> None:
    """RA-4/5, RB-15, M-N6: pre-seal frame oracle and origin-wide fresh salts."""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    committed, prepared, sealed = _batch_events()
    receipts = _commit_batch_sequence(
        store, origin, (committed, prepared), "privacy"
    )
    clean_base = receipts[-1].current_state_commitment
    head_before, origin_before = _files(store, origin)
    def crash(label: str) -> None:
        if label == "head-prepared:fsynced":
            raise RuntimeError("observe pre-seal")
    ledger._FAULT_HOOK = crash
    try:
        try:
            _commit(store, origin, "privacy-seal", clean_base, sealed)
            assert False, "pre-seal latch did not fire"
        except RuntimeError as exc:
            assert str(exc) == "observe pre-seal"
    finally:
        ledger._FAULT_HOOK = None
    head_after, origin_after = _files(store, origin)
    assert origin_after == origin_before

    prior_head = [json.loads(line) for line in head_before.splitlines()]
    prior_events = [json.loads(line) for line in origin_before.splitlines()]
    prepared_payload = {
        "batch_id": prepared.batch_id,
        "members": [{
            "candidate_commitment": member.candidate_commitment,
            "constraint_commitment": member.constraint_commitment,
            "query_ordinal": member.query_ordinal,
            "result_evidence_commitment": member.result_evidence_commitment,
        } for member in prepared.members],
    }
    assert prior_events[-1]["payload"] == prepared_payload
    observer_projection = {
        "batch_id": "batch-0",
        "members": prepared_payload["members"],
    }
    request_sha = hashlib.sha256(_canonical({
        "base_state_commitment": clean_base,
        "origin_id": origin,
        "operation_id": "privacy-seal",
        "event_type": "batch-sealed",
        "payload": observer_projection,
    })).hexdigest()
    binding_sha = hashlib.sha256(_canonical({
        "schema_version": "izanagi-reflux-origin-event/v2",
        "event_index": 4,
        "previous_event_sha256": prior_events[-1]["event_sha256"],
        "origin_id": origin,
        "operation_id": "privacy-seal",
        "event_type": "batch-sealed",
        "payload": observer_projection,
    })).hexdigest()
    prospective_public = {
        "phase": "IDLE",
        "iterations_used": 1,
        "queries_used": 2,
        "forfeited_iterations": 0,
        "forfeited_queries": 0,
        "batch_count": 1,
        "open_batch": None,
        "sealed_batch_ids": ["batch-0"],
        "seen_batch_ids": ["batch-0"],
        "terminal_status": None,
    }
    prospective_sha = hashlib.sha256(_canonical(prospective_public)).hexdigest()
    prepared_head_payload = {
        "base_state_commitment": clean_base,
        "request_sha256": request_sha,
        "origin_id": origin,
        "operation_id": "privacy-seal",
        "old_event_index": 3,
        "old_event_sha256": prior_events[-1]["event_sha256"],
        "old_event_byte_length": len(origin_before),
        "next_event_binding_sha256": binding_sha,
        "prospective_public_state_sha256": prospective_sha,
    }
    prepared_core = {
        "schema_version": "izanagi-reflux-origin-runtime-head/v2",
        "record_index": len(prior_head),
        "previous_record_sha256": prior_head[-1]["record_sha256"],
        "record_type": "head-prepared",
        "payload": prepared_head_payload,
    }
    expected_record = dict(prepared_core)
    expected_record["record_sha256"] = hashlib.sha256(_canonical(prepared_core)).hexdigest()
    expected_frame = _canonical(expected_record) + b"\n"
    assert head_after == head_before + expected_frame

    committed_semantic = {
        "phase": "RESULTS_PREPARED",
        "iterations_used": 1,
        "queries_used": 2,
        "sealed_queries": 0,
        "tombstoned_queries": 0,
        "forfeited_iterations": 0,
        "forfeited_queries": 0,
        "sealed_member_row_count": 0,
        "origin_distinct_candidate_count": 0,
        "origin_sealed_distinct_candidate_count": 0,
        "batch_count": 1,
        "tombstone_count": 0,
        "open_batch": {
            "batch_id": "batch-0",
            "iteration_index": 0,
            "member_row_count": 2,
            "query_ordinal_start": 0,
            "members": prepared_payload["members"],
        },
        "sealed_batch_ids": [],
        "seen_batch_ids": ["batch-0"],
        "rejected_constraints": [],
        "seen_salts": [],
        "terminal_status": None,
        "constraint_class": [],
    }
    state_preimage = {
        "authority_blob_sha256": hashlib.sha256(_authority_bytes([_manifest_object()])).hexdigest(),
        "runtime_head_record_index": expected_record["record_index"],
        "runtime_head_record_sha256": expected_record["record_sha256"],
        "head_file_byte_length": len(head_after),
        "head_partial_tail_sha256": None,
        "transaction_phase": "prepared",
        "prepared_record_sha256": expected_record["record_sha256"],
        "prepared_request_sha256": request_sha,
        "origins": [[
            origin,
            3,
            prior_events[-1]["event_sha256"],
            hashlib.sha256(_canonical(committed_semantic)).hexdigest(),
        ]],
    }
    independent_commitment = hashlib.sha256(
        b"izanagi-reflux-origin-state/v2\0" + _canonical(state_preimage)
    ).hexdigest()
    prepared_snapshot = _snapshot(store, origin)
    assert prepared_snapshot.state_commitment == independent_commitment
    without_prepared = dict(state_preimage)
    without_prepared.update({
        "transaction_phase": "clean",
        "prepared_record_sha256": None,
        "prepared_request_sha256": None,
    })
    assert independent_commitment != hashlib.sha256(
        b"izanagi-reflux-origin-state/v2\0" + _canonical(without_prepared)
    ).hexdigest()
    sealed_receipt = _commit(store, origin, "privacy-seal", clean_base, sealed)
    assert sealed_receipt.event_index == 4

    salt_repo, (salt_origin,) = _repo(tmp_path / "salt-contract")
    salt_store = _store(salt_repo)
    salt_base = _snapshot(salt_store, salt_origin).state_commitment
    salt_committed, salt_prepared, salt_sealed = _batch_events("salt-a")
    salt_receipts = _commit_batch_sequence(
        salt_store, salt_origin, (salt_committed, salt_prepared), "salt-a"
    )
    all_salts = tuple(
        salt
        for member in salt_sealed.members
        for salt in (
            member.candidate_salt,
            member.result_evidence_salt,
            member.constraint_salt,
        )
    )
    assert len(all_salts) == len(set(all_salts))
    with Raises("all-zero"):
        _commit(
            salt_store,
            salt_origin,
            "zero-salt",
            salt_receipts[-1].current_state_commitment,
            dataclasses.replace(salt_sealed, members=(
                dataclasses.replace(salt_sealed.members[0], candidate_salt="00" * 16),
                salt_sealed.members[1],
            )),
        )
    with Raises("invalid candidate salt"):
        _commit(
            salt_store,
            salt_origin,
            "short-salt",
            salt_receipts[-1].current_state_commitment,
            dataclasses.replace(salt_sealed, members=(
                dataclasses.replace(salt_sealed.members[0], candidate_salt="11" * 15),
                salt_sealed.members[1],
            )),
        )
    with Raises("reused"):
        _commit(
            salt_store,
            salt_origin,
            "duplicate-salt",
            salt_receipts[-1].current_state_commitment,
            dataclasses.replace(salt_sealed, members=(
                dataclasses.replace(
                    salt_sealed.members[0],
                    constraint_salt=salt_sealed.members[0].candidate_salt,
                ),
                salt_sealed.members[1],
            )),
        )
    first_seal = _commit(
        salt_store,
        salt_origin,
        "salt-a-seal",
        salt_receipts[-1].current_state_commitment,
        salt_sealed,
    )
    second_events = _batch_events(
        "salt-b", iteration=1, query_start=2,
        prior_replicates={b"10000": 1, b"01000": 1},
    )
    second_receipts = _commit_batch_sequence(
        salt_store, salt_origin, second_events[:2], "salt-b"
    )
    assert second_receipts[0].resulting_state_commitment != first_seal.resulting_state_commitment
    with Raises("reused"):
        _commit(
            salt_store,
            salt_origin,
            "cross-batch-salt",
            second_receipts[-1].current_state_commitment,
            dataclasses.replace(second_events[2], members=(
                dataclasses.replace(
                    second_events[2].members[0],
                    candidate_salt=salt_sealed.members[0].candidate_salt,
                ),
                second_events[2].members[1],
            )),
        )


def test_v17_member_identity_replicates_and_sealed_evidence_row_proxy_not_physical_query(
    tmp_path: Path,
) -> None:
    """W2: wire/q/r preimage, origin-wide replicate, and row-count accounting."""
    literal = (
        b'izanagi-reflux-origin-batch-member/v1\x00'
        b'{"candidate_wire_b64":"MTAwMDA=","query_ordinal":0,"replicate_ordinal":0}'
    )
    assert _member_bytes(b"10000", 0, 0) == literal
    assert ledger._member_preimage(b"10000", 0, 0) == literal
    variants = {
        ledger._member_preimage(b"01000", 0, 0),
        ledger._member_preimage(b"10000", 1, 0),
        ledger._member_preimage(b"10000", 0, 1),
    }
    assert literal not in variants and len(variants) == 3
    salt = "1" * 32
    assert len({_salted(salt, item) for item in {*variants, literal}}) == 4

    repo, (origin,) = _repo(tmp_path / "positive")
    store = _store(repo)
    first = _batch_events(
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )
    first_receipts = _commit_batch_sequence(store, origin, first, "repeat-a")
    second = _batch_events(
        "batch-1",
        iteration=1,
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
        query_start=2,
        prior_replicates={b"10000": 2},
    )
    _commit_batch_sequence(store, origin, second, "repeat-b")
    snap = _snapshot(store, origin)
    assert snap.queries_used == 4
    assert snap.sealed_queries == 4
    assert snap.origin_distinct_candidate_count == 1
    with ledger._locked(store) as authority:
        first_opened = ledger._read_sealed_batch_locked(
            store, authority, origin, "batch-0"
        )
        second_opened = ledger._read_sealed_batch_locked(
            store, authority, origin, "batch-1"
        )
    for opened in (first_opened, second_opened):
        assert opened.member_row_count == 2
        assert opened.distinct_candidate_count == 1
        assert opened.sealed_distinct_candidate_count == 1
    assert tuple(member.replicate_ordinal for member in second_opened.members) == (2, 3)
    sealed_payloads = [
        json.loads(frame)["payload"]
        for frame in store.origin_path(origin).read_bytes().splitlines()
        if json.loads(frame)["event_type"] == "batch-sealed"
    ]
    assert len(sealed_payloads) == 2
    assert all(
        payload["member_row_count"] == 2
        and payload["distinct_candidate_count"] == 1
        and payload["sealed_distinct_candidate_count"] == 1
        for payload in sealed_payloads
    )
    reset = _batch_events(
        "batch-2",
        iteration=2,
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
        query_start=4,
    )
    reset_ready = _commit_batch_sequence(
        store, origin, reset[:2], "repeat-reset"
    )[-1]
    with Raises("replicate ordinal"):
        _commit(
            store,
            origin,
            "repeat-reset-seal",
            reset_ready.current_state_commitment,
            reset[2],
        )

    for name, mutate in (
        ("gap", lambda event: dataclasses.replace(
            event,
            members=(
                event.members[0],
                dataclasses.replace(event.members[1], query_ordinal=2),
            ),
        )),
        ("duplicate-query", lambda event: dataclasses.replace(
            event,
            members=(
                event.members[0],
                dataclasses.replace(event.members[1], query_ordinal=0),
            ),
        )),
        ("duplicate-commitment", lambda event: dataclasses.replace(
            event,
            members=(
                event.members[0],
                dataclasses.replace(
                    event.members[1],
                    candidate_commitment=event.members[0].candidate_commitment,
                ),
            ),
        )),
    ):
        case_repo, (case_origin,) = _repo(tmp_path / name)
        case_store = _store(case_repo)
        event = mutate(_batch_events()[0])
        reserved = _commit(
            case_store,
            case_origin,
            f"{name}-reserve",
            _snapshot(case_store, case_origin).state_commitment,
            _reservation_for(event),
        )
        with Raises():
            _commit(
                case_store,
                case_origin,
                name,
                reserved.current_state_commitment,
                event,
            )

    replicate_repo, (replicate_origin,) = _repo(tmp_path / "bad-replicate")
    replicate_store = _store(replicate_repo)
    events = _batch_events()
    ready = _commit_batch_sequence(
        replicate_store, replicate_origin, events[:2], "rep"
    )[-1]
    bad_replicate = dataclasses.replace(events[2], members=(
        dataclasses.replace(events[2].members[0], replicate_ordinal=1),
        events[2].members[1],
    ))
    with Raises("replicate ordinal"):
        _commit(
            replicate_store,
            replicate_origin,
            "bad-replicate-open",
            ready.current_state_commitment,
            bad_replicate,
        )

    for name, outcomes in (
        ("bad-wire-sealed", ("accepted", "accepted")),
        ("bad-wire-tombstoned", ("tombstoned", "tombstoned")),
    ):
        bad_repo, (bad_origin,) = _repo(tmp_path / name)
        bad_store = _store(bad_repo)
        bad = _batch_events(
            candidates=(b"1000", b"01000"),
            outcomes=outcomes,
            constraints=(None, None),
        )
        ready = _commit_batch_sequence(bad_store, bad_origin, bad[:2], name)[-1]
        with Raises("candidate IR wire"):
            _commit(
                bad_store,
                bad_origin,
                f"{name}-seal",
                ready.current_state_commitment,
                bad[2],
            )


def test_v18_evidence_outcome_contract_and_fixed_member_tombstones(
    tmp_path: Path,
) -> None:
    """W3/W4: closed matrix at codec+reducer and fixed suffix tombstones."""
    valid = _batch_events()
    _, sealed_payload = ledger._event_payload(valid[2])
    for altered_member in (
        {**sealed_payload["members"][0], "extra": 1},
        {
            key: value
            for key, value in sealed_payload["members"][0].items()
            if key != "candidate_salt"
        },
        {**sealed_payload["members"][0], "query_ordinal": True},
        {**sealed_payload["members"][0], "replicate_ordinal": -1},
        {**sealed_payload["members"][0], "evidence_sha256": "F" * 64},
    ):
        with Raises():
            ledger._event_from_payload(
                "batch-sealed",
                {
                    **sealed_payload,
                    "members": [altered_member, sealed_payload["members"][1]],
                },
            )
    manifest = _manifest()
    def prepared_state(events: tuple[object, object, object]) -> ledger._SemanticState:
        state = ledger._SemanticState()
        ledger._apply_event(state, None, manifest=manifest, origin_id=_h("1"))
        ledger._apply_event(
            state, _reservation_for(events[0]), manifest=manifest, origin_id=_h("1")
        )
        ledger._apply_event(state, events[0], manifest=manifest, origin_id=_h("1"))
        ledger._apply_event(state, events[1], manifest=manifest, origin_id=_h("1"))
        return state

    def events_for_cell(
        outcome: str,
        evidence_sha256: str | None,
        constraint_sha256: str | None,
    ) -> tuple[object, object, object]:
        opened = dataclasses.replace(
            valid[2].members[1],
            outcome=outcome,
            evidence_digest=(
                None
                if evidence_sha256 is None
                else ledger.EvidenceDigest(evidence_sha256)
            ),
            constraint_sha256=constraint_sha256,
        )
        prepared = dataclasses.replace(
            valid[1].members[1],
            result_evidence_commitment=_salted(
                opened.result_evidence_salt,
                _result_bytes(outcome, evidence_sha256),
            ),
            constraint_commitment=_salted(
                opened.constraint_salt,
                b"" if constraint_sha256 is None else constraint_sha256.encode("ascii"),
            ),
        )
        return (
            valid[0],
            dataclasses.replace(
                valid[1], members=(valid[1].members[0], prepared)
            ),
            dataclasses.replace(
                valid[2], members=(valid[2].members[0], opened)
            ),
        )

    # Complete 3 outcomes x evidence-present/missing x constraint-present/missing
    # contract.  The same table drives encode/decode and the reducer directly.
    matrix = (
        ("accepted-evidence-no-constraint", "accepted", _h("f"), None, True),
        ("accepted-evidence-constraint", "accepted", _h("f"), _h("d"), False),
        ("accepted-no-evidence-no-constraint", "accepted", None, None, False),
        ("accepted-no-evidence-constraint", "accepted", None, _h("d"), False),
        ("rejected-evidence-constraint", "rejected", _h("f"), _h("d"), True),
        ("rejected-evidence-no-constraint", "rejected", _h("f"), None, False),
        ("rejected-no-evidence-constraint", "rejected", None, _h("d"), False),
        ("rejected-no-evidence-no-constraint", "rejected", None, None, False),
        ("tombstoned-no-evidence-no-constraint", "tombstoned", None, None, True),
        ("tombstoned-no-evidence-constraint", "tombstoned", None, _h("d"), False),
        ("tombstoned-evidence-no-constraint", "tombstoned", _h("f"), None, False),
        ("tombstoned-evidence-constraint", "tombstoned", _h("f"), _h("d"), False),
    )
    assert len(matrix) == 12
    assert sum(1 for *_, legal in matrix if legal) == 3
    for label, outcome, evidence_sha, constraint_sha, legal in matrix:
        events = events_for_cell(outcome, evidence_sha, constraint_sha)
        raw_member = {
            **sealed_payload["members"][1],
            "outcome": outcome,
            "evidence_sha256": evidence_sha,
            "constraint_sha256": constraint_sha,
        }
        raw_members = [sealed_payload["members"][0], raw_member]
        raw_payload = {
            **{
                key: value
                for key, value in sealed_payload.items()
                if key not in {
                    "member_row_count",
                    "distinct_candidate_count",
                    "sealed_distinct_candidate_count",
                }
            },
            "member_row_count": len(raw_members),
            "distinct_candidate_count": len({
                member["candidate_wire_b64"] for member in raw_members
            }),
            "sealed_distinct_candidate_count": len({
                member["candidate_wire_b64"]
                for member in raw_members
                if member["outcome"] != "tombstoned"
            }),
            "members": raw_members,
        }
        if legal:
            event_type, payload = ledger._event_payload(events[2])
            assert ledger._event_from_payload(event_type, payload) == events[2], label
            assert ledger._event_from_payload("batch-sealed", raw_payload) == events[2], label
            state = prepared_state(events)
            ledger._apply_event(
                state, events[2], manifest=manifest, origin_id=_h("1")
            )
            assert state.phase == "IDLE", label
        else:
            with Raises():
                ledger._event_payload(events[2])
            with Raises():
                ledger._event_from_payload("batch-sealed", raw_payload)
            state = prepared_state(events)
            with Raises():
                ledger._apply_event(
                    state, events[2], manifest=manifest, origin_id=_h("1")
                )

    unknown = events_for_cell("unknown", _h("f"), None)
    unknown_payload = {
        **sealed_payload,
        "members": [
            sealed_payload["members"][0],
            {
                **sealed_payload["members"][1],
                "outcome": "unknown",
                "constraint_sha256": None,
            },
        ],
    }
    with Raises("invalid sealed outcome"):
        ledger._event_payload(unknown[2])
    with Raises("invalid sealed outcome"):
        ledger._event_from_payload("batch-sealed", unknown_payload)
    with Raises("invalid sealed outcome"):
        ledger._apply_event(
            prepared_state(unknown), unknown[2], manifest=manifest, origin_id=_h("1")
        )

    state = prepared_state(valid)
    with Raises("partial"):
        ledger._apply_event(
            state,
            dataclasses.replace(valid[2], members=valid[2].members[:1]),
            manifest=manifest,
            origin_id=_h("1"),
        )

    repo, (origin,) = _repo(tmp_path / "tamper")
    store = _store(repo)
    ready = _commit_batch_sequence(store, origin, valid[:2], "tamper")[-1]
    evidence_tamper = dataclasses.replace(valid[2], members=(
        dataclasses.replace(
            valid[2].members[0], evidence_digest=ledger.EvidenceDigest(_h("a"))
        ),
        valid[2].members[1],
    ))
    with Raises("opening mismatch"):
        _commit(store, origin, "evidence-tamper", ready.current_state_commitment, evidence_tamper)
    outcome_tamper = dataclasses.replace(valid[2], members=(
        dataclasses.replace(
            valid[2].members[0],
            outcome="rejected",
            constraint_sha256=_h("a"),
        ),
        valid[2].members[1],
    ))
    with Raises("opening mismatch"):
        _commit(store, origin, "outcome-tamper", ready.current_state_commitment, outcome_tamper)

    partial_repo, (partial_origin,) = _repo(tmp_path / "partial")
    partial_store = _store(partial_repo)
    partial = _batch_events(
        outcomes=("accepted", "tombstoned"), constraints=(None, None)
    )
    _commit_batch_sequence(partial_store, partial_origin, partial, "partial")
    partial_snap = _snapshot(partial_store, partial_origin)
    assert (partial_snap.queries_used, partial_snap.sealed_queries, partial_snap.tombstoned_queries) == (2, 1, 1)
    assert partial_snap.tombstone_count == 1
    with ledger._locked(partial_store) as authority:
        rows = ledger._read_sealed_batch_locked(
            partial_store, authority, partial_origin, "batch-0"
        ).members
    assert len(rows) == len(partial[0].members) == len(partial[1].members) == len(partial[2].members)
    assert tuple(member.outcome for member in rows) == ("accepted", "tombstoned")

    hole = _batch_events(
        outcomes=("tombstoned", "accepted"), constraints=(None, None)
    )
    state = prepared_state(hole)
    with Raises("terminal suffix"):
        ledger._apply_event(
            state, hole[2], manifest=manifest, origin_id=_h("1")
        )


def test_v19_authority_policy_and_sealed_evidence_row_proxy_partition_not_physical_query(
    tmp_path: Path,
) -> None:
    """W5: event policy injection fails; authority and exact counters govern."""
    policy_events = (_reservation_event(), _batch_events()[0])
    assert tuple(ledger._event_payload(event)[0] for event in policy_events) == (
        "batch-reserved",
        "batch-committed",
    )
    for event in policy_events:
        event_type, payload = ledger._event_payload(event)
        for key in ("qmax", "floor", "policy"):
            with Raises("keys"):
                ledger._event_from_payload(event_type, {**payload, key: 1})

    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    events = _batch_events()
    receipts = _commit_batch_sequence(store, origin, events, "policy")
    with Raises("counters mismatch"):
        _commit(
            store,
            origin,
            "wrong-origin-counters",
            receipts[-1].current_state_commitment,
            ledger.OriginSealed(False, (_h("d"),), 1, 0, 1, 1, 0, 0),
        )
    assert dataclasses.fields(ledger.EvidenceDigest)[0].name == "sha256"
    assert len(dataclasses.fields(ledger.EvidenceDigest)) == 1
    assert not hasattr(ledger.EvidenceDigest, "path")


def test_v20_preseal_projection_hides_execution_counters_and_replicates() -> None:
    """Δ2/Δ3: prepared bytes reveal neither replicate structure nor prefix length."""
    assert "replicate_ordinal" not in {
        field.name for field in dataclasses.fields(ledger.CommittedBatchMember)
    }
    assert "replicate_ordinal" not in {
        field.name for field in dataclasses.fields(ledger.PreparedBatchMember)
    }
    accepted = _batch_events(
        outcomes=("accepted", "accepted"), constraints=(None, None)
    )
    partial = _batch_events(
        outcomes=("accepted", "tombstoned"), constraints=(None, None)
    )
    for event in (accepted[0], partial[0]):
        event_type, payload = ledger._event_payload(event)
        assert event_type == "batch-committed"
        assert "replicate_ordinal" not in repr(payload)
        assert "member_sequence_commitment" not in payload
    for event in (accepted[1], partial[1]):
        _, payload = ledger._event_payload(event)
        assert "replicate_ordinal" not in repr(payload)

    manifest = _manifest()
    def state_after(events: tuple[object, object, object]) -> ledger._SemanticState:
        state = ledger._SemanticState()
        for event in (None, _reservation_for(events[0]), *events):
            ledger._apply_event(state, event, manifest=manifest, origin_id=_h("1"))
        return state
    accepted_state = state_after(accepted)
    partial_state = state_after(partial)
    assert accepted_state.sealed_queries == 2
    assert partial_state.sealed_queries == 1
    assert partial_state.tombstoned_queries == 1
    assert ledger._preseal_semantic_sha(accepted_state) == ledger._preseal_semantic_sha(partial_state)

    repeated = _batch_events(
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )
    distinct = _batch_events(
        candidates=(b"10000", b"01000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )
    repeated_state = state_after(repeated)
    distinct_state = state_after(distinct)
    assert repeated_state.sealed_member_row_count == 2
    assert distinct_state.sealed_member_row_count == 2
    assert repeated_state.origin_distinct_candidate_count == 1
    assert distinct_state.origin_distinct_candidate_count == 2
    assert repeated_state.origin_sealed_distinct_candidate_count == 1
    assert distinct_state.origin_sealed_distinct_candidate_count == 2
    assert ledger._semantic_sha(repeated_state) != ledger._semantic_sha(distinct_state)
    assert ledger._preseal_semantic_sha(repeated_state) == (
        ledger._preseal_semantic_sha(distinct_state)
    )

    prepared_state = ledger._SemanticState()
    for event in (
        None,
        _reservation_for(accepted[0]),
        accepted[0],
        accepted[1],
    ):
        ledger._apply_event(
            prepared_state, event, manifest=manifest, origin_id=_h("1")
        )
    _, accepted_payload = ledger._event_payload(accepted[2])
    _, partial_payload = ledger._event_payload(partial[2])
    accepted_projection = ledger._prepared_payload_projection(
        "batch-sealed", accepted_payload, state=prepared_state
    )
    partial_projection = ledger._prepared_payload_projection(
        "batch-sealed", partial_payload, state=prepared_state
    )
    assert accepted_projection == partial_projection
    projection_text = repr(accepted_projection)
    assert "replicate_ordinal" not in projection_text
    assert "sealed_queries" not in projection_text
    assert "tombstoned_queries" not in projection_text
    empty_state = ledger._SemanticState()
    forfeited_iteration_state = dataclasses.replace(
        empty_state, forfeited_iterations=1
    )
    forfeited_query_state = dataclasses.replace(empty_state, forfeited_queries=2)
    assert ledger._preseal_semantic_sha(empty_state) != ledger._preseal_semantic_sha(
        forfeited_iteration_state
    )
    assert ledger._preseal_semantic_sha(empty_state) != ledger._preseal_semantic_sha(
        forfeited_query_state
    )


def test_v21_exact_salt_width_and_independent_codec_partition_oracle() -> None:
    """Δ6/Δ7/Δ8: literal salt width and independent max/max+1 v2 frames."""
    assert ledger._salt("1" * 32, label="salt") == "1" * 32
    for invalid in (
        "1" * 31,
        "1" * 33,
        "1" * 34,
        "g" * 32,
        "0" * 32,
    ):
        with Raises():
            ledger._salt(invalid, label="salt")

    maximum_integer = (1 << 63) - 1
    maximum_record_bytes = 1 << 20
    def independent_rejected_seal_frame(member_row_count: int) -> bytes:
        members = []
        for index in range(member_row_count):
            candidate = f"{index % 32:05b}".encode("ascii")
            members.append({
                "candidate_salt": "1" * 32,
                "candidate_wire_b64": base64.b64encode(candidate).decode("ascii"),
                "constraint_salt": "1" * 32,
                "constraint_sha256": _h("f"),
                "evidence_sha256": _h("f"),
                "outcome": "rejected",
                "query_ordinal": maximum_integer,
                "replicate_ordinal": maximum_integer,
                "result_evidence_salt": "1" * 32,
            })
        core = {
            "schema_version": "izanagi-reflux-origin-event/v2",
            "event_index": maximum_integer,
            "previous_event_sha256": _h("e"),
            "origin_id": _h("f"),
            "operation_id": "x" * 128,
            "event_type": "batch-sealed",
            "payload": {
                "batch_id": "x" * 128,
                "distinct_candidate_count": min(member_row_count, 32),
                "member_row_count": member_row_count,
                "sealed_distinct_candidate_count": min(member_row_count, 32),
                "members": members,
            },
        }
        record = dict(core)
        record["event_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
        return _canonical(record) + b"\n"
    maximum = independent_rejected_seal_frame(2248)
    overflow = independent_rejected_seal_frame(2249)
    assert len(maximum) == 1_048_337 <= maximum_record_bytes
    assert len(overflow) == 1_048_803 > maximum_record_bytes
    assert ledger._MAX_BATCH_MEMBER_ROW_COUNT == 2248
    _manifest(_manifest_object(
        imax=2,
        qmax=2249,
        floor_per_round=2249,
    ))
    with Raises("partitioned"):
        _manifest(_manifest_object(
            imax=1,
            qmax=2249,
            floor_per_round=2249,
        ))


def test_v22_authority_floor_requires_an_existing_batch_partition() -> None:
    """F1/M-18a/M-19: the maximum floor has a constructible batch count."""
    assert 1124 + 1125 == 2249
    _manifest(_manifest_object(
        imax=2,
        qmax=2249,
        member_row_min=1124,
        floor_per_round=2249,
    ))
    with Raises("floor cannot be partitioned"):
        _manifest(_manifest_object(
            imax=2,
            qmax=2249,
            member_row_min=2248,
            floor_per_round=2249,
        ))


def test_v23_two_origin_shared_runtime_head_aggregate_max_and_max_plus_one() -> None:
    """F2/M-20: per-origin feasibility cannot hide shared-head overflow."""
    maximum_ledger_bytes = 64 << 20
    maximum = _independent_shared_head_bytes((4636, 4637))
    overflow = _independent_shared_head_bytes((4636, 4638))
    assert maximum == 67_103_806 <= maximum_ledger_bytes
    assert overflow == 67_111_042 > maximum_ledger_bytes

    first = _manifest_object(
        descriptor=_h("3"), imax=4636, qmax=9_272
    )
    second_at_maximum = _manifest_object(
        descriptor=_h("4"), imax=4637, qmax=9_274
    )
    second_overflow = _manifest_object(
        descriptor=_h("4"), imax=4638, qmax=9_276
    )
    ledger._authority_from_bytes(_authority_bytes([first, second_at_maximum]))
    with Raises("shared runtime head"):
        ledger._authority_from_bytes(_authority_bytes([first, second_overflow]))


def test_v24_origin_ledger_total_decimal_count_max_and_max_plus_one() -> None:
    """F3/M-18c/M-21: decimal-width-aware independent ledger-total oracle."""
    exact_digit_boundaries = {10: 12_056, 100: 93_869, 1000: 911_972}
    conservative_bounds = {10: 12_062, 100: 93_872, 1000: 911_972}
    for member_row_count, exact_bytes in exact_digit_boundaries.items():
        assert sum(map(len, _independent_worst_case_batch_frames(
            member_row_count
        ))) == exact_bytes
        assert ledger._affine_batch_bytes(
            batches=1, members=member_row_count, tombstoned=False
        ) == conservative_bounds[member_row_count]
    for member_row_count in (1, 2, 2248):
        abandoned = sum(map(len, _independent_worst_case_abandoned_frames(
            member_row_count
        )))
        normal = sum(map(len, _independent_worst_case_batch_frames(
            member_row_count
        )))
        tombstoned = sum(map(len, _independent_worst_case_batch_frames(
            member_row_count, tombstoned=True
        )))
        assert abandoned < normal
        assert abandoned < tombstoned

    maximum_ledger_bytes = 64 << 20
    maximum = _independent_origin_ledger_upper_bytes(
        batches=33, members=73_717, kmax=4
    )
    overflow = _independent_origin_ledger_upper_bytes(
        batches=33, members=73_718, kmax=4
    )
    assert maximum == 67_108_536 <= maximum_ledger_bytes
    assert overflow == 67_109_445 > maximum_ledger_bytes

    _manifest(_manifest_object(imax=33, qmax=73_717, kmax=4))
    with Raises("authority budget exceeds ledger codec feasibility"):
        _manifest(_manifest_object(imax=33, qmax=73_718, kmax=4))


def test_v25_public_commit_enforces_2248_member_row_codec_limit(
    tmp_path: Path,
) -> None:
    """F4/M-18b: the public commit path accepts 2248 and rejects 2249."""
    raw = _manifest_object(imax=2, qmax=2249)

    def committed(member_row_count: int) -> ledger.BatchCommitted:
        return ledger.BatchCommitted(
            "member-row-boundary",
            0,
            tuple(
                ledger.CommittedBatchMember(index, f"{index + 1:064x}")
                for index in range(member_row_count)
            ),
        )

    accepted_repo, (accepted_origin,) = _repo(tmp_path / "accepted", [raw])
    accepted_store = _store(accepted_repo)
    accepted_reservation = _commit(
        accepted_store,
        accepted_origin,
        "reserve-2248",
        _snapshot(accepted_store, accepted_origin).state_commitment,
        _reservation_event("member-row-boundary", member_row_count=2248),
    )
    accepted = _commit(
        accepted_store,
        accepted_origin,
        "commit-2248",
        accepted_reservation.current_state_commitment,
        committed(2248),
    )
    assert accepted.event_index == 2
    assert _snapshot(accepted_store, accepted_origin).queries_used == 2248

    rejected_repo, (rejected_origin,) = _repo(tmp_path / "rejected", [raw])
    rejected_store = _store(rejected_repo)
    with Raises("batch member row count exceeds codec feasibility"):
        _commit(
            rejected_store,
            rejected_origin,
            "reserve-2249",
            _snapshot(rejected_store, rejected_origin).state_commitment,
            _reservation_event("member-row-boundary", member_row_count=2249),
        )


def test_v26_reservation_is_required_before_commit_and_binds_commit_identity(
    tmp_path: Path,
) -> None:
    """Direct commit と reservation binding 4 軸を単一理由で拒否する。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    committed = _batch_events()[0]
    initial = _snapshot(store, origin)
    with Raises("current phase"):
        _commit(
            store,
            origin,
            "direct-commit",
            initial.state_commitment,
            committed,
        )
    assert _snapshot(store, origin) == initial

    reserved = _commit(
        store,
        origin,
        "reserve",
        initial.state_commitment,
        _reservation_for(committed),
    )
    pending = _snapshot(store, origin)
    assert pending.phase == "BATCH_RESERVED"
    assert (pending.iterations_used, pending.queries_used) == (1, 2)
    assert (
        pending.reserved_batch_id,
        pending.reserved_iteration_index,
        pending.reserved_member_row_count,
        pending.reserved_query_ordinal_start,
    ) == ("batch-0", 0, 2, 0)

    wrong_batch = dataclasses.replace(committed, batch_id="batch-other")
    wrong_iteration = dataclasses.replace(committed, iteration_index=1)
    existing_commitments = {
        member.candidate_commitment for member in committed.members
    }
    extra_commitment = next(
        _h(char) for char in "abcdef" if _h(char) not in existing_commitments
    )
    wrong_member_row_count = dataclasses.replace(
        committed,
        members=(
            *committed.members,
            ledger.CommittedBatchMember(2, extra_commitment),
        ),
    )
    wrong_query_base = dataclasses.replace(
        committed,
        members=tuple(
            dataclasses.replace(member, query_ordinal=member.query_ordinal + 1)
            for member in committed.members
        ),
    )
    for operation, event, reason in (
        ("wrong-batch", wrong_batch, "does not match"),
        ("wrong-iteration", wrong_iteration, "does not match"),
        ("wrong-member-row-count", wrong_member_row_count, "does not match"),
        ("wrong-query-base", wrong_query_base, "query ordinals"),
    ):
        with Raises(reason):
            _commit(
                store,
                origin,
                operation,
                reserved.current_state_commitment,
                event,
            )
        assert _snapshot(store, origin) == pending

    accepted = _commit(
        store,
        origin,
        "matching-commit",
        reserved.current_state_commitment,
        committed,
    )
    assert accepted.event_index == 2
    assert _snapshot(store, origin).phase == "BATCH_COMMITTED"


def test_v27_abandoned_reservation_forfeits_budget_and_allows_abort_seal(
    tmp_path: Path,
) -> None:
    """Abandon は I/Q を返さず sealed/tombstoned と分離して終端できる。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    reserved = _commit(
        store,
        origin,
        "reserve",
        _snapshot(store, origin).state_commitment,
        _reservation_event(),
    )
    abandoned = _commit(
        store,
        origin,
        "abandon",
        reserved.current_state_commitment,
        ledger.BatchReservationAbandoned("batch-0"),
    )
    snap = _snapshot(store, origin)
    assert snap.phase == "IDLE"
    assert (snap.iterations_used, snap.queries_used) == (1, 2)
    assert (snap.forfeited_iterations, snap.forfeited_queries) == (1, 2)
    assert (snap.sealed_queries, snap.tombstoned_queries) == (0, 0)
    assert snap.tombstone_count == 0
    assert (
        snap.reserved_batch_id,
        snap.reserved_iteration_index,
        snap.reserved_member_row_count,
        snap.reserved_query_ordinal_start,
    ) == (None, None, None, None)
    for operation, event, reason in (
        ("reused-batch", _reservation_event("batch-0", 1, 2, 2), "reused"),
        (
            "reused-iteration",
            _reservation_event("batch-1", 0, 2, 2),
            "iteration index",
        ),
        (
            "reused-query",
            _reservation_event("batch-1", 1, 2, 0),
            "query ordinal start",
        ),
    ):
        with Raises(reason):
            _commit(
                store,
                origin,
                operation,
                abandoned.current_state_commitment,
                event,
            )
        assert _snapshot(store, origin) == snap
    terminal = _commit(
        store,
        origin,
        "abort-seal",
        abandoned.current_state_commitment,
        ledger.OriginSealed(True, (), 0, 0, 0, 0, 1, 2),
    )
    assert terminal.event_index == 3
    assert _snapshot(store, origin).terminal_status == "aborted"


def test_v28_reserved_origin_cannot_seal_or_skip_commit(tmp_path: Path) -> None:
    """BATCH_RESERVED では matching commit / abandon 以外を受理しない。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    committed, prepared, sealed = _batch_events()
    reserved = _commit(
        store,
        origin,
        "reserve",
        _snapshot(store, origin).state_commitment,
        _reservation_for(committed),
    )
    pending = _snapshot(store, origin)
    for operation, event, reason in (
        (
            "seal-while-reserved",
            ledger.OriginSealed(True, (), 0, 0, 0, 0, 0, 0),
            "current phase",
        ),
        ("prepare-before-commit", prepared, "current phase"),
        (
            "batch-seal-before-commit",
            sealed,
            "batch seal projection requires prepared results",
        ),
    ):
        with Raises(reason):
            _commit(
                store,
                origin,
                operation,
                reserved.current_state_commitment,
                event,
            )
        assert _snapshot(store, origin) == pending

    # 公開経路では projection 層が先に拒否するため、FSM 相 guard の帰属は
    # _apply_event の直接呼出しで別に固定する。
    semantic_state = ledger._SemanticState()
    manifest = _manifest()
    ledger._apply_event(
        semantic_state,
        None,
        manifest=manifest,
        origin_id=origin,
    )
    ledger._apply_event(
        semantic_state,
        _reservation_for(committed),
        manifest=manifest,
        origin_id=origin,
    )
    assert semantic_state.phase == "BATCH_RESERVED"
    semantic_before = ledger._semantic_object(semantic_state)
    with Raises("current phase"):
        ledger._apply_event(
            semantic_state,
            sealed,
            manifest=manifest,
            origin_id=origin,
        )
    assert ledger._semantic_object(semantic_state) == semantic_before

    committed_receipt = _commit(
        store,
        origin,
        "commit",
        reserved.current_state_commitment,
        committed,
    )
    with Raises("current phase"):
        _commit(
            store,
            origin,
            "abandon-after-commit",
            committed_receipt.current_state_commitment,
            ledger.BatchReservationAbandoned("batch-0"),
        )


def _recovery_script(
    repo: Path,
    origin: str,
    *,
    action: str,
    expected_event_index: int = 2,
) -> str:
    assert action in {"commit", "abandon"}
    raw_action_source = (
        """\
members=tuple(
    l.CommittedBatchMember(snap.reserved_query_ordinal_start+index,f'{index+1:064x}')
    for index in range(snap.reserved_member_row_count)
)
event=l.BatchCommitted(
    snap.reserved_batch_id,
    snap.reserved_iteration_index,
    members,
)
"""
        if action == "commit"
        else "event=l.BatchReservationAbandoned(snap.reserved_batch_id)"
    )
    action_source = "\n".join(
        "    " + line for line in raw_action_source.splitlines()
    )
    return f"""
import os,sys
sys.path.insert(0,{os.fspath(_ORCHESTRATOR.parent)!r})
from orchestrator.campaign import reflux_origin_ledger as l
s=l._fixture_store_for_test({os.fspath(repo)!r},'HEAD',initialize=False)
with l._locked(s) as authority:
    snap=l._read_origin_locked(s,authority,{origin!r})
    assert snap.phase=='BATCH_RESERVED'
    assert snap.reserved_batch_id is not None
    assert snap.reserved_iteration_index is not None
    assert snap.reserved_member_row_count is not None
    assert snap.reserved_query_ordinal_start is not None
{action_source}
    receipt=l._commit_locked(
        s,
        authority,
        origin_id={origin!r},
        operation_id='recovery-{action}',
        expected_state_commitment=snap.state_commitment,
        event=event,
    )
assert receipt.event_index=={expected_event_index}
"""


def test_v29_committed_reservation_replays_and_new_process_commits_from_binding(
    tmp_path: Path,
) -> None:
    """Durable reservation を二重課金せず、新 process が4 bindingで commitする。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    base = _snapshot(store, origin).state_commitment
    reserved_event = _reservation_event()
    reserved = _commit(store, origin, "durable-reserve", base, reserved_event)
    replayed = _commit(store, origin, "durable-reserve", base, reserved_event)
    assert replayed.replayed
    assert replayed.resulting_state_commitment == reserved.resulting_state_commitment
    pending = _snapshot(store, origin)
    assert (pending.iterations_used, pending.queries_used) == (1, 2)
    assert (pending.forfeited_iterations, pending.forfeited_queries) == (0, 0)
    recovery_source = _recovery_script(repo, origin, action="commit")
    assert "batch-0" not in recovery_source
    completed = subprocess.run(
        [sys.executable, "-c", recovery_source],
        cwd=repo,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
    )
    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", errors="replace"
    )
    recovered = _snapshot(_store(repo, initialize=False), origin)
    assert recovered.phase == "BATCH_COMMITTED"
    assert (recovered.iterations_used, recovered.queries_used) == (1, 2)
    assert (recovered.forfeited_iterations, recovered.forfeited_queries) == (0, 0)


def test_v30_forfeited_queries_do_not_satisfy_certifiable_floor(
    tmp_path: Path,
) -> None:
    """forfeited member rows は certifiable floor へ算入しない。"""
    raw = _manifest_object(imax=1, qmax=2, floor_per_round=2)
    repo, (origin,) = _repo(tmp_path, [raw])
    store = _store(repo)
    receipts = _commit_sequence(
        store,
        origin,
        (_reservation_event(), ledger.BatchReservationAbandoned("batch-0")),
        "forfeit-floor",
    )
    with Raises("floor"):
        _commit(
            store,
            origin,
            "certifiable",
            receipts[-1].current_state_commitment,
            ledger.OriginSealed(False, (), 0, 0, 0, 0, 1, 2),
        )
    aborted = _commit(
        store,
        origin,
        "aborted",
        receipts[-1].current_state_commitment,
        ledger.OriginSealed(True, (), 0, 0, 0, 0, 1, 2),
    )
    assert aborted.event_index == 3


def test_v31_abandon_batch_binding_rejects_wrong_then_accepts_matching(
    tmp_path: Path,
) -> None:
    """Abandon の batch ID 不一致だけを拒否し、正しい再試行を受理する。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    reserved = _commit(
        store,
        origin,
        "reserve-b0",
        _snapshot(store, origin).state_commitment,
        _reservation_event("b0"),
    )
    with Raises("does not match"):
        _commit(
            store,
            origin,
            "abandon-b1",
            reserved.current_state_commitment,
            ledger.BatchReservationAbandoned("b1"),
        )
    pending = _snapshot(store, origin)
    assert pending.phase == "BATCH_RESERVED"
    accepted = _commit(
        store,
        origin,
        "abandon-b0",
        reserved.current_state_commitment,
        ledger.BatchReservationAbandoned("b0"),
    )
    assert accepted.event_index == 2
    assert _snapshot(store, origin).phase == "IDLE"


def test_v32_origin_seal_rejects_each_forfeited_counter_mismatch_alone(
    tmp_path: Path,
) -> None:
    """既存 counter を正しく保ち、新 forfeit counter だけを個別に誤らせる。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    receipts = _commit_sequence(
        store,
        origin,
        (_reservation_event(), ledger.BatchReservationAbandoned("batch-0")),
        "forfeit-counter",
    )
    base = receipts[-1].current_state_commitment
    for operation, event in (
        (
            "wrong-forfeited-iterations",
            ledger.OriginSealed(True, (), 0, 0, 0, 0, 0, 2),
        ),
        (
            "wrong-forfeited-queries",
            ledger.OriginSealed(True, (), 0, 0, 0, 0, 1, 1),
        ),
    ):
        with Raises("counters mismatch"):
            _commit(store, origin, operation, base, event)
    accepted = _commit(
        store,
        origin,
        "matching-forfeited-counters",
        base,
        ledger.OriginSealed(True, (), 0, 0, 0, 0, 1, 2),
    )
    assert accepted.event_index == 3


def test_v33_new_process_abandons_from_public_reservation_binding(
    tmp_path: Path,
) -> None:
    """非最小 member row count の累積 abandon を新 process 復旧で固定する。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    first_reserved = _commit(
        store,
        origin,
        "reserve-two",
        _snapshot(store, origin).state_commitment,
        _reservation_event(),
    )
    first_abandoned = _commit(
        store,
        origin,
        "abandon-two",
        first_reserved.current_state_commitment,
        ledger.BatchReservationAbandoned("batch-0"),
    )
    second_reserved = _commit(
        store,
        origin,
        "reserve-three",
        first_abandoned.current_state_commitment,
        _reservation_event(
            "batch-1", iteration=1, member_row_count=3, query_start=2
        ),
    )
    pending = _snapshot(store, origin)
    assert pending.state_commitment == second_reserved.current_state_commitment
    assert (
        pending.reserved_batch_id,
        pending.reserved_iteration_index,
        pending.reserved_member_row_count,
        pending.reserved_query_ordinal_start,
    ) == ("batch-1", 1, 3, 2)
    assert (pending.iterations_used, pending.queries_used) == (2, 5)
    assert (pending.forfeited_iterations, pending.forfeited_queries) == (1, 2)
    recovery_source = _recovery_script(
        repo,
        origin,
        action="abandon",
        expected_event_index=4,
    )
    assert "batch-1" not in recovery_source
    completed = subprocess.run(
        [sys.executable, "-c", recovery_source],
        cwd=repo,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=SUBPROCESS_TIMEOUT,
    )
    assert completed.returncode == 0, completed.stderr.decode(
        "utf-8", errors="replace"
    )
    recovered = _snapshot(_store(repo, initialize=False), origin)
    assert recovered.phase == "IDLE"
    assert (recovered.iterations_used, recovered.queries_used) == (2, 5)
    assert (recovered.forfeited_iterations, recovered.forfeited_queries) == (2, 5)
    assert (recovered.sealed_queries, recovered.tombstoned_queries) == (0, 0)


def test_v34_abandon_then_completed_batch_can_certifiably_seal(
    tmp_path: Path,
) -> None:
    """Forfeit があっても別 batch の sealed floor が certifiable seal を許す。"""
    raw = _manifest_object(imax=2, qmax=4, floor_per_round=2)
    repo, (origin,) = _repo(tmp_path, [raw])
    store = _store(repo)
    abandoned = _commit_sequence(
        store,
        origin,
        (_reservation_event(), ledger.BatchReservationAbandoned("batch-0")),
        "forfeit-first",
    )[-1]
    completed_events = _batch_events("batch-1", iteration=1, query_start=2)
    completed = _commit_batch_sequence(
        store,
        origin,
        completed_events,
        "complete-second",
    )[-1]
    before_seal = _snapshot(store, origin)
    assert abandoned.event_index == 2
    assert completed.event_index == 6
    assert before_seal.phase == "IDLE"
    assert (before_seal.iterations_used, before_seal.queries_used) == (2, 4)
    assert (
        before_seal.forfeited_iterations,
        before_seal.forfeited_queries,
    ) == (1, 2)
    assert (before_seal.sealed_queries, before_seal.tombstoned_queries) == (2, 0)
    terminal = _commit(
        store,
        origin,
        "certifiable-after-forfeit",
        completed.current_state_commitment,
        ledger.OriginSealed(False, (_h("d"),), 1, 0, 2, 0, 1, 2),
    )
    assert terminal.event_index == 7
    assert _snapshot(store, origin).terminal_status == "certifiable"


def test_v35_origin_seal_prepared_hashes_use_independent_counter_projection() -> None:
    """OriginSealed の request/binding が各 forfeit counter を独立に束縛する。"""
    base_state = _h("1")
    origin = _h("2")
    operation = "origin-seal-oracle"
    previous_event = _h("3")
    record = {
        "schema_version": "izanagi-reflux-origin-event/v2",
        "event_index": 17,
        "previous_event_sha256": previous_event,
        "origin_id": origin,
        "operation_id": operation,
    }
    payload = {
        "seal_kind": "aborted",
        "constraint_class_sha256s": [],
        "batch_count": 2,
        "tombstone_count": 1,
        "sealed_queries": 3,
        "tombstoned_queries": 1,
        "forfeited_iterations": 4,
        "forfeited_queries": 9,
    }
    state = ledger._SemanticState(phase="IDLE")

    def independent_digests(raw: dict[str, object]) -> tuple[str, str]:
        projection = {
            "seal_kind": raw["seal_kind"],
            "batch_count": raw["batch_count"],
            "tombstone_count": raw["tombstone_count"],
            "sealed_queries": raw["sealed_queries"],
            "tombstoned_queries": raw["tombstoned_queries"],
            "forfeited_iterations": raw["forfeited_iterations"],
            "forfeited_queries": raw["forfeited_queries"],
        }
        request = hashlib.sha256(_canonical({
            "base_state_commitment": base_state,
            "origin_id": origin,
            "operation_id": operation,
            "event_type": "origin-sealed",
            "payload": projection,
        })).hexdigest()
        binding = hashlib.sha256(_canonical({
            **record,
            "event_type": "origin-sealed",
            "payload": projection,
        })).hexdigest()
        return request, binding

    def production_digests(raw: dict[str, object]) -> tuple[str, str]:
        return (
            ledger._request_sha256(
                base_state_commitment=base_state,
                origin_id=origin,
                operation_id=operation,
                event_type="origin-sealed",
                payload=raw,
                state=state,
            ),
            ledger._prepared_event_binding_sha256(
                record=record,
                event_type="origin-sealed",
                payload=raw,
                state=state,
            ),
        )

    baseline = independent_digests(payload)
    assert production_digests(payload) == baseline
    for field in ("forfeited_iterations", "forfeited_queries"):
        altered = {**payload, field: int(payload[field]) + 1}
        expected = independent_digests(altered)
        assert expected[0] != baseline[0]
        assert expected[1] != baseline[1]
        assert production_digests(altered) == expected


def test_d96_default_explicit_positive_aggregate_and_aborted_boundaries(
    tmp_path: Path,
) -> None:
    """既定1の維持と明示2の per-batch certifiable gate を対で固定する。"""
    repeated = _batch_events(
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )

    default_repo, (default_origin,) = _repo(tmp_path / "default")
    default_store = _store(default_repo)
    default_receipts = _commit_batch_sequence(
        default_store, default_origin, repeated, "default-repeat"
    )
    default_terminal = _commit(
        default_store,
        default_origin,
        "default-certifiable",
        default_receipts[-1].current_state_commitment,
        ledger.OriginSealed(False, (), 1, 0, 2, 0, 0, 0),
    )
    assert default_terminal.event_index == 5

    explicit = _manifest_object(candidate_min=2)
    explicit_repo, (explicit_origin,) = _repo(
        tmp_path / "explicit", [explicit]
    )
    explicit_store = _store(explicit_repo)
    explicit_receipts = _commit_batch_sequence(
        explicit_store, explicit_origin, repeated, "explicit-repeat"
    )
    explicit_snapshot = _snapshot(explicit_store, explicit_origin)
    assert explicit_snapshot.origin_distinct_candidate_count == 1
    with ledger._locked(explicit_store) as authority:
        explicit_batch = ledger._read_sealed_batch_locked(
            explicit_store, authority, explicit_origin, "batch-0"
        )
    assert (
        explicit_batch.member_row_count,
        explicit_batch.distinct_candidate_count,
        explicit_batch.sealed_distinct_candidate_count,
    ) == (2, 1, 1)
    with Raises("distinct candidate count is below minimum"):
        _commit(
            explicit_store,
            explicit_origin,
            "explicit-certifiable",
            explicit_receipts[-1].current_state_commitment,
            ledger.OriginSealed(False, (), 1, 0, 2, 0, 0, 0),
        )

    positive_repo, (positive_origin,) = _repo(
        tmp_path / "positive", [explicit]
    )
    positive_store = _store(positive_repo)
    distinct = _batch_events(
        candidates=(b"10000", b"01000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )
    positive_receipts = _commit_batch_sequence(
        positive_store, positive_origin, distinct, "explicit-distinct"
    )
    _commit(
        positive_store,
        positive_origin,
        "positive-certifiable",
        positive_receipts[-1].current_state_commitment,
        ledger.OriginSealed(False, (), 1, 0, 2, 0, 0, 0),
    )

    aggregate_raw = _manifest_object(
        imax=2, qmax=4, candidate_min=2
    )
    aggregate_repo, (aggregate_origin,) = _repo(
        tmp_path / "aggregate", [aggregate_raw]
    )
    aggregate_store = _store(aggregate_repo)
    first = _batch_events(
        candidates=(b"10000", b"10000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )
    _commit_batch_sequence(
        aggregate_store, aggregate_origin, first, "aggregate-a"
    )
    second = _batch_events(
        "batch-1",
        iteration=1,
        candidates=(b"01000", b"01000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
        query_start=2,
    )
    aggregate_receipts = _commit_batch_sequence(
        aggregate_store, aggregate_origin, second, "aggregate-b"
    )
    assert _snapshot(
        aggregate_store, aggregate_origin
    ).origin_distinct_candidate_count == 2
    with Raises("distinct candidate count is below minimum"):
        _commit(
            aggregate_store,
            aggregate_origin,
            "aggregate-certifiable",
            aggregate_receipts[-1].current_state_commitment,
            ledger.OriginSealed(False, (), 2, 0, 4, 0, 0, 0),
        )

    aborted_repo, (aborted_origin,) = _repo(
        tmp_path / "aborted", [explicit]
    )
    aborted_store = _store(aborted_repo)
    aborted_receipts = _commit_batch_sequence(
        aborted_store, aborted_origin, repeated, "aborted-repeat"
    )
    aborted_terminal = _commit(
        aborted_store,
        aborted_origin,
        "aborted-terminal",
        aborted_receipts[-1].current_state_commitment,
        ledger.OriginSealed(True, (), 1, 0, 2, 0, 0, 0),
    )
    assert aborted_terminal.event_index == 5


def test_all_tombstone_batch_is_outside_candidate_minimum_gate(
    tmp_path: Path,
) -> None:
    """実行候補0の batch は gate 外、実行済み batch は通常どおり gate する。"""
    tombstoned = _batch_events(
        candidates=(b"10000", b"01000"),
        outcomes=("tombstoned", "tombstoned"),
        constraints=(None, None),
    )

    def prepare(
        path: Path,
        *,
        candidate_min: int,
        executed_candidates: tuple[bytes, bytes],
    ) -> tuple[object, str, ledger.EventReceipt]:
        raw = _manifest_object(imax=2, qmax=4, candidate_min=candidate_min)
        repo, (origin,) = _repo(path, [raw])
        store = _store(repo)
        _commit_batch_sequence(store, origin, tombstoned, "tombstone-batch")
        executed = _batch_events(
            "batch-1",
            iteration=1,
            candidates=executed_candidates,
            outcomes=("accepted", "accepted"),
            constraints=(None, None),
            query_start=2,
        )
        receipt = _commit_batch_sequence(
            store, origin, executed, "executed-batch"
        )[-1]
        return store, origin, receipt

    default_store, default_origin, default_receipt = prepare(
        tmp_path / "default",
        candidate_min=1,
        executed_candidates=(b"00100", b"00010"),
    )
    _commit(
        default_store,
        default_origin,
        "default-certifiable",
        default_receipt.current_state_commitment,
        ledger.OriginSealed(False, (), 2, 1, 2, 2, 0, 0),
    )

    passing_store, passing_origin, passing_receipt = prepare(
        tmp_path / "explicit-pass",
        candidate_min=2,
        executed_candidates=(b"00100", b"00010"),
    )
    _commit(
        passing_store,
        passing_origin,
        "explicit-pass-certifiable",
        passing_receipt.current_state_commitment,
        ledger.OriginSealed(False, (), 2, 1, 2, 2, 0, 0),
    )

    failing_store, failing_origin, failing_receipt = prepare(
        tmp_path / "explicit-fail",
        candidate_min=2,
        executed_candidates=(b"00100", b"00100"),
    )
    with Raises("distinct candidate count is below minimum"):
        _commit(
            failing_store,
            failing_origin,
            "explicit-fail-certifiable",
            failing_receipt.current_state_commitment,
            ledger.OriginSealed(False, (), 2, 1, 2, 2, 0, 0),
        )


def test_t1_tombstone_counts_gate_only_executed_candidates(
    tmp_path: Path,
) -> None:
    """A,A,B(tombstoned) は凍結2・実行1として gate する。"""
    events = _batch_events(
        candidates=(b"10000", b"10000", b"01000"),
        outcomes=("accepted", "accepted", "tombstoned"),
        constraints=(None, None, None),
    )
    sealed_type, sealed_payload = ledger._event_payload(events[2])
    assert sealed_type == "batch-sealed"
    assert sealed_payload["member_row_count"] == 3
    assert sealed_payload["distinct_candidate_count"] == 2
    assert sealed_payload["sealed_distinct_candidate_count"] == 1

    high = _manifest_object(
        imax=1, qmax=3, member_row_min=2, candidate_min=2
    )
    high_repo, (high_origin,) = _repo(tmp_path / "high", [high])
    high_store = _store(high_repo)
    high_receipts = _commit_batch_sequence(
        high_store, high_origin, events, "t1-high"
    )
    high_snapshot = _snapshot(high_store, high_origin)
    with ledger._locked(high_store) as authority:
        batch = ledger._read_sealed_batch_locked(
            high_store, authority, high_origin, "batch-0"
        )
        semantic = ledger._semantic_object(
            ledger._replay(high_store, authority).states[high_origin]
        )
    assert (
        batch.member_row_count,
        batch.distinct_candidate_count,
        batch.sealed_distinct_candidate_count,
    ) == (3, 2, 1)
    assert high_snapshot.origin_distinct_candidate_count == 2
    assert (
        semantic["sealed_member_row_count"],
        semantic["origin_distinct_candidate_count"],
        semantic["origin_sealed_distinct_candidate_count"],
    ) == (3, 2, 1)
    with Raises("distinct candidate count is below minimum"):
        _commit(
            high_store,
            high_origin,
            "t1-high-certifiable",
            high_receipts[-1].current_state_commitment,
            ledger.OriginSealed(False, (), 1, 1, 2, 1, 0, 0),
        )

    low = _manifest_object(
        imax=1, qmax=3, member_row_min=2, candidate_min=1
    )
    low_repo, (low_origin,) = _repo(tmp_path / "low", [low])
    low_store = _store(low_repo)
    low_receipts = _commit_batch_sequence(
        low_store, low_origin, events, "t1-low"
    )
    accepted = _commit(
        low_store,
        low_origin,
        "t1-low-certifiable",
        low_receipts[-1].current_state_commitment,
        ledger.OriginSealed(False, (), 1, 1, 2, 1, 0, 0),
    )
    assert accepted.event_index == 5


def test_t3_certifiable_gate_checks_every_batch_not_only_edges(
    tmp_path: Path,
) -> None:
    """good(A,B)→bad(C,C)→good(B,D) の中央だけで拒否する。"""
    raw = _manifest_object(imax=3, qmax=6, candidate_min=2)
    repo, (origin,) = _repo(tmp_path, [raw])
    store = _store(repo)
    good_first = _batch_events(
        "batch-0",
        candidates=(b"10000", b"01000"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
    )
    _commit_batch_sequence(store, origin, good_first, "t3-first")
    bad_middle = _batch_events(
        "batch-1",
        iteration=1,
        candidates=(b"00100", b"00100"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
        query_start=2,
    )
    _commit_batch_sequence(store, origin, bad_middle, "t3-middle")
    good_last = _batch_events(
        "batch-2",
        iteration=2,
        candidates=(b"01000", b"00010"),
        outcomes=("accepted", "accepted"),
        constraints=(None, None),
        query_start=4,
        prior_replicates={b"01000": 1},
    )
    final_receipts = _commit_batch_sequence(
        store, origin, good_last, "t3-last"
    )
    with ledger._locked(store) as authority:
        batches = tuple(
            ledger._read_sealed_batch_locked(store, authority, origin, batch_id)
            for batch_id in ("batch-0", "batch-1", "batch-2")
        )
    assert tuple(
        batch.sealed_distinct_candidate_count for batch in batches
    ) == (2, 1, 2)
    with Raises("distinct candidate count is below minimum"):
        _commit(
            store,
            origin,
            "t3-certifiable",
            final_receipts[-1].current_state_commitment,
            ledger.OriginSealed(False, (), 3, 0, 6, 0, 0, 0),
        )


def test_t4_candidate_minimum_member_row_feasibility_boundary() -> None:
    """candidate minimum は member row minimum 以下だけを受理する。"""
    equal = _manifest_object(member_row_min=2, candidate_min=2)
    policy = _manifest(equal).budget_policy
    assert policy.batch_member_row_count_min == 2
    assert policy.batch_distinct_candidate_count_min == 2
    with Raises("exceeds member row minimum"):
        _manifest(_manifest_object(member_row_min=2, candidate_min=3))


def _run() -> int:
    functions = [value for name, value in sorted(globals().items())
                 if name.startswith("test_") and callable(value)]
    passed = failed = 0
    for function in functions:
        temporary: tempfile.TemporaryDirectory[str] | None = None
        try:
            parameters = inspect.signature(function).parameters
            kwargs = {}
            if "tmp_path" in parameters:
                temporary = tempfile.TemporaryDirectory(prefix="reflux-origin-test-")
                kwargs["tmp_path"] = Path(temporary.name)
            function(**kwargs)
            print(f"PASS {function.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {function.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
        finally:
            if temporary is not None:
                temporary.cleanup()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
