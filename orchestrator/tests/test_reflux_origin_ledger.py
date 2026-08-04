# -*- coding: utf-8 -*-
"""T-244 origin-ledger prototype の独立 golden / FSM / crash / anchor tests。

pytest と素の ``python3 orchestrator/tests/test_reflux_origin_ledger.py`` の双方で走る。
production API の path を monkeypatch せず、private seam へ temp Git repository 全体だけを渡す。
"""
from __future__ import annotations

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
sys.path.insert(0, os.fspath(_ORCHESTRATOR))

from campaign import reflux_origin_ledger as ledger  # noqa: E402


FORMULA = "q-lower-bound/base+perRound*R+Emin/v1"
SCHEMA = "izanagi-trigger-gate-ir/v1"
AUTHORITY_PATH = Path("orchestrator/campaign/reflux_origin_authority_v1.json")
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
    batch_min: int = 2,
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
            "batch_cardinality_min": batch_min,
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
        b"izanagi-reflux-origin-manifest/v1\0" + _canonical(raw_manifest)
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
        "authority_schema": "izanagi-reflux-origin-authority/v1",
        "origins": entries,
    }) + b"\n"


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


def _batch_events(
    batch_id: str = "batch-0",
    iteration: int = 0,
    candidates: tuple[bytes, ...] = (b"10000", b"01000"),
    outcomes: tuple[str, ...] = ("accepted", "rejected"),
    constraints: tuple[str | None, ...] = (None, _h("d")),
) -> tuple[object, object, object]:
    def salts(_: str) -> tuple[str, ...]:
        return tuple(os.urandom(16).hex() for _ in candidates)
    candidate_salts = salts("candidate")
    outcome_salts = salts("outcome")
    result_salts = salts("result")
    constraint_salts = salts("constraint")
    results = tuple((_h("e"), _h("f"))[index] for index in range(len(candidates)))
    candidate_commitments = tuple(
        _salted(salt, value) for salt, value in zip(candidate_salts, candidates, strict=True)
    )
    outcome_commitments = tuple(
        _salted(salt, value.encode("ascii"))
        for salt, value in zip(outcome_salts, outcomes, strict=True)
    )
    result_commitments = tuple(
        _salted(salt, value.encode("ascii"))
        for salt, value in zip(result_salts, results, strict=True)
    )
    constraint_commitments = tuple(
        _salted(salt, b"" if value is None else value.encode("ascii"))
        for salt, value in zip(constraint_salts, constraints, strict=True)
    )
    return (
        ledger.BatchCommitted(batch_id, iteration, candidate_commitments),
        ledger.BatchResultsPrepared(
            batch_id,
            candidate_commitments,
            outcome_commitments,
            result_commitments,
            constraint_commitments,
        ),
        ledger.BatchSealed(
            batch_id,
            candidate_salts,
            candidates,
            outcome_salts,
            outcomes,
            result_salts,
            results,
            constraint_salts,
            constraints,
        ),
    )


def _commit_sequence(store: object, origin: str, events: tuple[object, ...], prefix: str) -> list[ledger.EventReceipt]:
    receipts = []
    base = _snapshot(store, origin).state_commitment
    for index, event in enumerate(events):
        receipt = _commit(store, origin, f"{prefix}-{index}", base, event)
        receipts.append(receipt)
        base = receipt.current_state_commitment
    return receipts


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
    raw = _manifest_object()
    literal = (
        b'{"authority_series_id":"series-a","axis_semantics_sha256":"5555555555555555555555555555555555555555555555555555555555555555",'
        b'"budget_policy":{"batch_cardinality_min":2,"imax":4,"kmax":3,"qmax":8,"query_floor_constraints":['
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
        previous_event_sha256=_h("2"), event_type="batch-tombstoned",
        payload={"batch_id": "batch-golden"},
    )
    literal_event_frame = (
        b'{"event_index":7,"event_sha256":"db34b64a65089c313c94f0a222134751898a1cf9a2286df0ff66e202971d02cc",'
        b'"event_type":"batch-tombstoned","operation_id":"op-golden","origin_id":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"payload":{"batch_id":"batch-golden"},"previous_event_sha256":"2222222222222222222222222222222222222222222222222222222222222222",'
        b'"schema_version":"izanagi-reflux-origin-event/v1"}\n'
    )
    literal_event_core = literal_event_frame.replace(
        b',"event_sha256":"db34b64a65089c313c94f0a222134751898a1cf9a2286df0ff66e202971d02cc"',
        b"",
        1,
    )[:-1]
    assert hashlib.sha256(literal_event_core).hexdigest() == (
        "db34b64a65089c313c94f0a222134751898a1cf9a2286df0ff66e202971d02cc"
    )
    assert _canonical(event) + b"\n" == literal_event_frame
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
        b'"record_sha256":"c0586d5c91199880d714ea7f3fc4c25206ceba4ccaac2bd2a91b53f3f91014e5",'
        b'"record_type":"head-committed","schema_version":"izanagi-reflux-origin-runtime-head/v1"}\n'
    )
    literal_head_core = literal_head_frame.replace(
        b',"record_sha256":"c0586d5c91199880d714ea7f3fc4c25206ceba4ccaac2bd2a91b53f3f91014e5"',
        b"",
        1,
    )[:-1]
    assert hashlib.sha256(literal_head_core).hexdigest() == (
        "c0586d5c91199880d714ea7f3fc4c25206ceba4ccaac2bd2a91b53f3f91014e5"
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
        b"izanagi-reflux-origin-state/v1\0" + _canonical(state_preimage)
    ).hexdigest()
    assert state.phase == "EMPTY"
    receipt = ledger.EventReceipt(_h("1"), "op-golden", 7, _h("2"), _h("3"), _h("4"), False)
    assert dataclasses.asdict(receipt) == {
        "origin_id": _h("1"), "operation_id": "op-golden", "event_index": 7,
        "event_sha256": _h("2"), "resulting_state_commitment": _h("3"),
        "current_state_commitment": _h("4"), "replayed": False,
    }


def test_v02_exact_five_phase_six_event_transition_matrix() -> None:
    """V2: allowed branches と全 phase/event pair の reject を別々に固定。"""
    manifest = _manifest()
    committed, prepared, sealed = _batch_events()
    tombstone = ledger.BatchTombstoned("batch-0")
    origin_seal = ledger.OriginSealed(True, (), 0, 0)
    genesis = None
    events = (genesis, committed, prepared, sealed, tombstone, origin_seal)
    allowed = {
        ("EMPTY", type(None)),
        ("IDLE", ledger.BatchCommitted),
        ("IDLE", ledger.OriginSealed),
        ("BATCH_COMMITTED", ledger.BatchResultsPrepared),
        ("BATCH_COMMITTED", ledger.BatchTombstoned),
        ("RESULTS_PREPARED", ledger.BatchSealed),
    }
    builders: dict[str, Callable[[], ledger._SemanticState]] = {}
    def at_empty(): return ledger._SemanticState()
    def at_idle():
        state = at_empty(); ledger._apply_event(state, None, manifest=manifest, origin_id=_h("1")); return state
    def at_committed():
        state = at_idle(); ledger._apply_event(state, committed, manifest=manifest, origin_id=_h("1")); return state
    def at_prepared():
        state = at_committed(); ledger._apply_event(state, prepared, manifest=manifest, origin_id=_h("1")); return state
    def at_terminal():
        state = at_idle(); ledger._apply_event(state, origin_seal, manifest=manifest, origin_id=_h("1")); return state
    builders.update(EMPTY=at_empty, IDLE=at_idle, BATCH_COMMITTED=at_committed,
                    RESULTS_PREPARED=at_prepared, ORIGIN_SEALED=at_terminal)
    for phase, builder in builders.items():
        for event in events:
            key = (phase, type(event))
            state = builder()
            if key in allowed:
                ledger._apply_event(state, event, manifest=manifest, origin_id=_h("1"))
            else:
                with Raises():
                    ledger._apply_event(state, event, manifest=manifest, origin_id=_h("1"))


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
    batch_change["budget_policy"]["batch_cardinality_min"] = 3
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
    event = _batch_events()[0]
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
                    _batch_events(f"cross-{index}")[0])
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
    probe_b = tmp_path / "process-b.probe"
    release = tmp_path / "process.release"
    process_event = _batch_events("process-batch")[0]
    def process_script(
        origin: str,
        operation: str,
        marker: Path,
        wait_for_release: bool,
        probe: Path | None,
    ) -> str:
        return f"""
import errno,fcntl,os,sys,time
from pathlib import Path
sys.path.insert(0,{os.fspath(_ORCHESTRATOR)!r})
from campaign import reflux_origin_ledger as l
s=l._store_for_repo(Path({os.fspath(process_repo)!r}),committed_ref='HEAD',fixture=True)
e=l.BatchCommitted('process-batch',0,{process_event.candidate_commitments!r})
probe={None if probe is None else os.fspath(probe)!r}
if probe is not None:
    probe_fd=os.open(s.lock_path,os.O_RDWR)
    try:
        try:
            fcntl.flock(probe_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            assert exc.errno in (errno.EAGAIN,errno.EWOULDBLOCK)
            Path(probe).write_text('blocked',encoding='ascii')
        else:
            fcntl.flock(probe_fd,fcntl.LOCK_UN)
            Path(probe).write_text('available',encoding='ascii')
    finally:
        os.close(probe_fd)
def hook(label):
    if label=='commit:base-read':
        Path({os.fspath(marker)!r}).write_text('ready',encoding='ascii')
        if {wait_for_release!r}:
            deadline=time.monotonic()+30
            while not Path({os.fspath(release)!r}).exists():
                if time.monotonic()>deadline: raise RuntimeError('release timeout')
                time.sleep(0.01)
l._FAULT_HOOK=hook
try:
    with l._locked(s) as a:
        l._commit_locked(s,a,origin_id={origin!r},operation_id={operation!r},expected_state_commitment={process_base!r},event=e)
except l.RefluxOriginLedgerError:
    sys.exit(19)
"""
    first_process = subprocess.Popen(
        [sys.executable, "-c", process_script(
            process_origin_a, "process-a", marker_a, True, None
        )],
        cwd=process_repo,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 10
    while not marker_a.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not marker_a.exists():
        release.write_text("release", encoding="ascii")
        first_process.kill()
        first_process.communicate(timeout=SUBPROCESS_TIMEOUT)
    assert marker_a.exists()
    second_process = subprocess.Popen(
        [sys.executable, "-c", process_script(
            process_origin_b, "process-b", marker_b, True, probe_b
        )],
        cwd=process_repo,
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 10
    while not probe_b.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not probe_b.exists():
        release.write_text("release", encoding="ascii")
        first_process.kill()
        second_process.kill()
        first_process.communicate(timeout=SUBPROCESS_TIMEOUT)
        second_process.communicate(timeout=SUBPROCESS_TIMEOUT)
    assert probe_b.exists()
    probe_state = probe_b.read_text(encoding="ascii")
    if probe_state == "available":
        deadline = time.monotonic() + 10
        while not marker_b.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker_b.exists(), "per-origin path did not reach the shared base gate"
    release.write_text("release", encoding="ascii")
    try:
        first_stdout, first_stderr = first_process.communicate(timeout=SUBPROCESS_TIMEOUT)
        second_stdout, second_stderr = second_process.communicate(timeout=SUBPROCESS_TIMEOUT)
    except subprocess.TimeoutExpired:
        first_process.kill()
        second_process.kill()
        first_process.communicate()
        second_process.communicate()
        raise
    assert probe_state == "blocked"
    assert first_process.returncode == 0, (first_stdout, first_stderr)
    assert second_process.returncode == 19, (second_stdout, second_stderr)
    assert marker_b.exists()
    _assert_flock_state(process_store.lock_path, blocked=False)
    assert _snapshot(process_store, process_origin_a).iterations_used == 1


def test_v05_prepared_changes_commitment_and_only_exact_request_resumes(tmp_path: Path) -> None:
    """V5 / M-A5/M-N6: durable prepare 中は別 operation を write 無し拒否。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    base = _snapshot(store, origin).state_commitment
    event = _batch_events()[0]
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
    assert prepared_snapshot.phase == "IDLE"  # committed-index visibility, not physical extra state
    prepared_bytes = _files(store, origin)
    try:
        _commit(store, origin, "prepare-b", prepared_snapshot.state_commitment, event)
        operation_b_accepted = True
    except ledger.RefluxOriginLedgerError:
        operation_b_accepted = False
    assert not operation_b_accepted
    assert _files(store, origin) == prepared_bytes
    altered = dataclasses.replace(
        event, candidate_commitments=tuple(reversed(event.candidate_commitments))
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
    first, prepared, _ = _batch_events()
    base_a = _snapshot(store, origin).state_commitment
    with ledger._locked(store) as authority:
        assert f"origin-opened:{origin}" in ledger._replay(store, authority).operation_ids
    receipt_a = _commit(store, origin, "operation-a", base_a, first)
    receipt_b = _commit(
        store, origin, "operation-b", receipt_a.current_state_commitment, prepared
    )
    before = _files(store, origin)
    replay = _commit(store, origin, "operation-a", base_a, first)
    assert replay.replayed
    assert replay.resulting_state_commitment == receipt_a.resulting_state_commitment
    assert replay.current_state_commitment == receipt_b.current_state_commitment
    assert replay.resulting_state_commitment != replay.current_state_commitment
    assert _files(store, origin) == before
    with Raises("reuse mismatch"):
        _commit(store, origin, "operation-a", receipt_a.current_state_commitment, first)
    altered = ledger.BatchCommitted(first.batch_id, first.iteration_index, tuple(reversed(first.candidate_commitments)))
    with Raises("reuse mismatch"):
        _commit(store, origin, "operation-a", base_a, altered)
    with Raises("reserved"):
        _commit(store, origin, f"origin-opened:{origin}", receipt_b.current_state_commitment, altered)
    first_manifest = _manifest_object(series="cross-a", descriptor=_h("4"))
    second_manifest = _manifest_object(series="cross-b", descriptor=_h("d"))
    cross_repo, cross_origins = _repo(tmp_path / "cross-origin-op", [first_manifest, second_manifest])
    cross_store = _store(cross_repo)
    origin_a, origin_b = sorted(cross_origins)
    cross_event = _batch_events("cross-op-batch")[0]
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


def test_v07_batch_prefix_cardinality_distinctness_and_single_inflight(tmp_path: Path) -> None:
    """V7 / M-N4: scalar count でなく event prefix が第二 in-flight を拒否。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    first = _batch_events()[0]
    base = _snapshot(store, origin).state_commitment
    receipt = _commit(store, origin, "batch-first", base, first)
    second = ledger.BatchCommitted("batch-1", 1, (_h("1"), _h("2")))
    with Raises("current phase"):
        _commit(store, origin, "batch-second", receipt.current_state_commitment, second)
    invalid_one = ledger.BatchCommitted("one", 0, (_h("1"),))
    fresh_repo, (fresh_origin,) = _repo(tmp_path / "fresh")
    fresh = _store(fresh_repo)
    fresh_base = _snapshot(fresh, fresh_origin).state_commitment
    with Raises("candidate commitments"):
        _commit(fresh, fresh_origin, "one", fresh_base, invalid_one)
    duplicate = ledger.BatchCommitted("duplicate", 0, (_h("1"), _h("1")))
    with Raises("candidate commitments"):
        _commit(fresh, fresh_origin, "duplicate", fresh_base, duplicate)
    with Raises("batch minimum"):
        _manifest(_manifest_object(batch_min=1))


def test_v08_tombstone_no_refund_cardinality_accounting_and_no_provider(tmp_path: Path) -> None:
    """V8 / M-N7: Q は cardinality 件、tombstone 後も I/Q は返却しない。"""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    committed = _batch_events()[0]
    receipts = _commit_sequence(
        store, origin, (committed, ledger.BatchTombstoned("batch-0")), "tomb"
    )
    snap = _snapshot(store, origin)
    assert snap.iterations_used == 1
    assert snap.queries_used == 2
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
    committed: object,
) -> str:
    return f"""
import os,sys
sys.path.insert(0,{os.fspath(_ORCHESTRATOR)!r})
from campaign import reflux_origin_ledger as l
s=l._fixture_store_for_test({os.fspath(repo)!r},'HEAD',initialize=False)
e=l.BatchCommitted('batch-0',0,{committed.candidate_commitments!r})
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
        committed = _batch_events()[0]
        completed = subprocess.run(
            [sys.executable, "-c", _crash_script(repo, origin, base, point, committed)],
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
        with Raises():
            _commit(store, origin, "other-operation", _snapshot(store, origin).state_commitment, _batch_events()[0])
        receipt = _commit(store, origin, "process-crash", base, committed)
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
        receipt = _commit(store, origin, "short-write", base, _batch_events()[0])
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
            _commit(fault_store, fault_origin, "fsync-fault", fault_base, _batch_events()[0])
    finally:
        ledger.os.fsync = real_fsync
    with Raises("poisoned"):
        _commit(fault_store, fault_origin, "fsync-fault", fault_base, _batch_events()[0])
    retry_repo, (fault_origin,) = _repo(tmp_path / "fsync-retry")
    fault_store = _store(retry_repo)
    fault_base = _snapshot(fault_store, fault_origin).state_commitment
    retry = _commit(fault_store, fault_origin, "fsync-fault", fault_base, _batch_events()[0])
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
                _commit(case_store, case_origin, f"fsync-target-{index}", case_base, _batch_events()[0])
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
        event = _batch_events()[0]
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
    unrelated_event = _batch_events()[0]
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
    head_partial_event = _batch_events()[0]
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
        _batch_events()[0],
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
        _commit(store, origin, "corrupt-prefix", _h("1"), _batch_events()[0])


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
sys.path.insert(0,{os.fspath(repo / 'orchestrator')!r})
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
    receipt_a = _commit(store, origin_a, "interleave-a", base, events_a[0])
    receipt_b = _commit(store, origin_b, "interleave-b", receipt_a.current_state_commitment, events_b[0])
    _commit(store, origin_a, "interleave-a2", receipt_b.current_state_commitment,
            events_a[1])
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
        committed_payload = origin_event_records[item_origin][1]["payload"]
        semantic_by_origin[item_origin] = {
            "phase": "BATCH_COMMITTED",
            "iterations_used": 1,
            "queries_used": 2,
            "sealed_queries": 0,
            "batch_count": 1,
            "tombstone_count": 0,
            "open_batch": {
                "batch_id": batch_id,
                "candidate_commitments": committed_payload["candidate_commitments"],
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
        b"izanagi-reflux-origin-state/v1\0" + _canonical(global_base_preimage)
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


def test_v14_independent_i_q_k_floor_boundaries_and_aborted_seal(tmp_path: Path) -> None:
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
    with Raises("query floor exceeds codec feasibility"):
        _manifest(_manifest_object(
            imax=1,
            qmax=ledger._MAX_BATCH_CARDINALITY + 1,
            floor_per_round=ledger._MAX_BATCH_CARDINALITY + 1,
        ))
    with Raises("batch minimum exceeds codec feasibility"):
        _manifest(_manifest_object(
            imax=2,
            qmax=ledger._MAX_BATCH_CARDINALITY + 1,
            batch_min=ledger._MAX_BATCH_CARDINALITY + 1,
            floor_per_round=ledger._MAX_BATCH_CARDINALITY + 1,
        ))
    with Raises("Qmax exceeds codec feasibility"):
        _manifest(_manifest_object(imax=1, qmax=ledger._MAX_BATCH_CARDINALITY + 1))
    with Raises("Kmax exceeds codec feasibility"):
        _manifest(_manifest_object(kmax=ledger._MAX_CLASS_CARDINALITY + 1))
    exact_boundary = _manifest_object(
        imax=1,
        qmax=3912,
        batch_min=3912,
        floor_per_round=3912,
    )
    with Raises("batch minimum exceeds codec feasibility"):
        _manifest(exact_boundary)
    raw = _manifest_object(imax=1, qmax=4, kmax=0)
    repo, (origin,) = _repo(tmp_path, [raw])
    store = _store(repo)
    committed, prepared, sealed = _batch_events(outcomes=("accepted", "accepted"), constraints=(None, None))
    receipts = _commit_sequence(store, origin, (committed, prepared, sealed), "limits")
    cert = ledger.OriginSealed(False, (), 1, 0)
    _commit(store, origin, "certifiable", receipts[-1].current_state_commitment, cert)
    over_repo, (over_origin,) = _repo(tmp_path / "over", [raw])
    over = _store(over_repo)
    first_receipt = _commit(over, over_origin, "first", _snapshot(over, over_origin).state_commitment, committed)
    tomb_receipt = _commit(over, over_origin, "first-tomb", first_receipt.current_state_commitment,
                           ledger.BatchTombstoned("batch-0"))
    with Raises("Imax"):
        _commit(over, over_origin, "second", tomb_receipt.current_state_commitment,
                ledger.BatchCommitted("batch-1", 1, (_h("1"), _h("2"))))
    qraw = _manifest_object(imax=2, qmax=2)
    qrepo, (qorigin,) = _repo(tmp_path / "q-over", [qraw])
    qstore = _store(qrepo)
    qfirst = _commit(qstore, qorigin, "q-first", _snapshot(qstore, qorigin).state_commitment, committed)
    qtomb = _commit(qstore, qorigin, "q-tomb", qfirst.current_state_commitment,
                    ledger.BatchTombstoned("batch-0"))
    with Raises("Qmax"):
        _commit(qstore, qorigin, "q-second", qtomb.current_state_commitment,
                ledger.BatchCommitted("batch-1", 1, (_h("1"), _h("2"))))
    low = _manifest_object(imax=2, qmax=4, floor_per_round=4)
    low_repo, (low_origin,) = _repo(tmp_path / "low", [low])
    low_store = _store(low_repo)
    tomb_receipts = _commit_sequence(
        low_store, low_origin,
        (_batch_events()[0], ledger.BatchTombstoned("batch-0")), "low"
    )
    second_tomb = _commit_sequence(
        low_store,
        low_origin,
        (_batch_events("batch-1", iteration=1)[0], ledger.BatchTombstoned("batch-1")),
        "low-second",
    )
    with Raises("floor"):
        _commit(low_store, low_origin, "early-cert", second_tomb[-1].current_state_commitment,
                ledger.OriginSealed(False, (), 2, 2))
    _commit(low_store, low_origin, "abort", second_tomb[-1].current_state_commitment,
            ledger.OriginSealed(True, (), 2, 2))
    kraw = _manifest_object(imax=1, qmax=2, kmax=0)
    krepo, (korigin,) = _repo(tmp_path / "k-over", [kraw])
    kstore = _store(krepo)
    kreceipts = _commit_sequence(kstore, korigin, _batch_events(), "k")
    with Raises("Kmax"):
        _commit(kstore, korigin, "k-seal", kreceipts[-1].current_state_commitment,
                ledger.OriginSealed(False, (_h("d"),), 1, 0))


def test_v15_strict_authority_event_json_paths_types_and_limits(tmp_path: Path) -> None:
    """V15 / M-N12: extra/missing/duplicate key、bool、path、symlink、size を拒否。"""
    raw = _manifest_object()
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
    duplicate = b'{"authority_schema":"izanagi-reflux-origin-authority/v1","origins":[],"origins":[]}\n'
    with Raises("duplicate"):
        ledger._authority_from_bytes(duplicate)
    missing_authority = _canonical({"authority_schema": ledger.AUTHORITY_SCHEMA_ID}) + b"\n"
    with Raises("keys"):
        ledger._authority_from_bytes(missing_authority)
    with Raises("oversize authority"):
        ledger._authority_from_bytes(b"x" * ((8 << 20) + 1))
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
    real_runtime = ancestor_store.runtime_root.with_name("v1-real")
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
sys.path.insert(0,{os.fspath(_ORCHESTRATOR)!r})
from campaign import reflux_origin_ledger as l
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
    first = _commit(store, origin, "positive-0", _snapshot(store, origin).state_commitment, committed)
    second = _commit(store, origin, "positive-1", first.current_state_commitment, prepared)
    prepared_snapshot = _snapshot(store, origin)
    assert prepared_snapshot.phase == "RESULTS_PREPARED"
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
    assert "result_sha256s" not in visible and "constraint_sha256s" not in visible
    with Raises("not sealed"):
        with ledger._locked(store) as authority:
            ledger._read_sealed_batch_locked(store, authority, origin, "batch-0")
    wrong = dataclasses.replace(sealed, candidate_salts=tuple(reversed(sealed.candidate_salts)))
    with Raises("opening mismatch"):
        _commit(store, origin, "wrong-open", second.current_state_commitment, wrong)
    third = _commit(store, origin, "positive-2", second.current_state_commitment, sealed)
    with ledger._locked(store) as authority:
        revealed = ledger._read_sealed_batch_locked(store, authority, origin, "batch-0")
    assert revealed.outcomes == ("accepted", "rejected")
    partial = ledger.OriginSealed(False, (), 1, 0)
    with Raises("exact rejected set"):
        _commit(store, origin, "partial-class", third.current_state_commitment, partial)
    final = _commit(store, origin, "positive-3", third.current_state_commitment,
                    ledger.OriginSealed(False, (_h("d"),), 1, 0))
    assert _snapshot(store, origin).terminal_status == "certifiable"
    assert final.event_index == 4
    order_repo, (order_origin,) = _repo(tmp_path / "result-order")
    order_store = _store(order_repo)
    ordered = _batch_events(outcomes=("accepted", "accepted"), constraints=(None, None))
    order_first = _commit(
        order_store,
        order_origin,
        "order-0",
        _snapshot(order_store, order_origin).state_commitment,
        ordered[0],
    )
    misordered_prepared = dataclasses.replace(
        ordered[1], candidate_commitments=tuple(reversed(ordered[1].candidate_commitments))
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
        "order-1",
        order_first.current_state_commitment,
        ordered[1],
    )
    reveal = ordered[2]
    misordered = dataclasses.replace(
        reveal,
        result_salts=tuple(reversed(reveal.result_salts)),
        result_sha256s=tuple(reversed(reveal.result_sha256s)),
    )
    with Raises("opening mismatch"):
        _commit(order_store, order_origin, "misordered-result",
                order_second.current_state_commitment, misordered)


def test_v16_salt_contract_and_observer_reconstructs_preseal_bytes(tmp_path: Path) -> None:
    """RA-4/5, RB-15, M-N6: pre-seal frame oracle and origin-wide fresh salts."""
    repo, (origin,) = _repo(tmp_path)
    store = _store(repo)
    committed, prepared, sealed = _batch_events()
    receipts = _commit_sequence(store, origin, (committed, prepared), "privacy")
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
    prepared_payload = prior_events[-1]["payload"]
    observer_projection = {
        "batch_id": "batch-0",
        "candidate_commitments": prepared_payload["candidate_commitments"],
        "outcome_commitments": prepared_payload["outcome_commitments"],
        "result_commitments": prepared_payload["result_commitments"],
        "constraint_commitments": prepared_payload["constraint_commitments"],
    }
    request_sha = hashlib.sha256(_canonical({
        "base_state_commitment": clean_base,
        "origin_id": origin,
        "operation_id": "privacy-seal",
        "event_type": "batch-sealed",
        "payload": observer_projection,
    })).hexdigest()
    binding_sha = hashlib.sha256(_canonical({
        "schema_version": "izanagi-reflux-origin-event/v1",
        "event_index": 3,
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
        "sealed_queries": 2,
        "batch_count": 1,
        "tombstone_count": 0,
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
        "old_event_index": 2,
        "old_event_sha256": prior_events[-1]["event_sha256"],
        "old_event_byte_length": len(origin_before),
        "next_event_binding_sha256": binding_sha,
        "prospective_public_state_sha256": prospective_sha,
    }
    prepared_core = {
        "schema_version": "izanagi-reflux-origin-runtime-head/v1",
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
        "batch_count": 1,
        "tombstone_count": 0,
        "open_batch": {
            "batch_id": "batch-0",
            "candidate_commitments": prepared_payload["candidate_commitments"],
            "outcome_commitments": prepared_payload["outcome_commitments"],
            "result_commitments": prepared_payload["result_commitments"],
            "constraint_commitments": prepared_payload["constraint_commitments"],
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
            2,
            prior_events[-1]["event_sha256"],
            hashlib.sha256(_canonical(committed_semantic)).hexdigest(),
        ]],
    }
    independent_commitment = hashlib.sha256(
        b"izanagi-reflux-origin-state/v1\0" + _canonical(state_preimage)
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
        b"izanagi-reflux-origin-state/v1\0" + _canonical(without_prepared)
    ).hexdigest()
    sealed_receipt = _commit(store, origin, "privacy-seal", clean_base, sealed)
    assert sealed_receipt.event_index == 3

    salt_repo, (salt_origin,) = _repo(tmp_path / "salt-contract")
    salt_store = _store(salt_repo)
    salt_base = _snapshot(salt_store, salt_origin).state_commitment
    salt_committed, salt_prepared, salt_sealed = _batch_events("salt-a")
    salt_receipts = _commit_sequence(
        salt_store, salt_origin, (salt_committed, salt_prepared), "salt-a"
    )
    all_salts = (
        *salt_sealed.candidate_salts,
        *salt_sealed.outcome_salts,
        *salt_sealed.result_salts,
        *salt_sealed.constraint_salts,
    )
    assert len(all_salts) == len(set(all_salts))
    with Raises("all-zero"):
        _commit(
            salt_store,
            salt_origin,
            "zero-salt",
            salt_receipts[-1].current_state_commitment,
            dataclasses.replace(
                salt_sealed,
                candidate_salts=("00" * 16, *salt_sealed.candidate_salts[1:]),
            ),
        )
    with Raises("invalid candidate salt"):
        _commit(
            salt_store,
            salt_origin,
            "short-salt",
            salt_receipts[-1].current_state_commitment,
            dataclasses.replace(
                salt_sealed,
                candidate_salts=("11" * 15, *salt_sealed.candidate_salts[1:]),
            ),
        )
    with Raises("reused"):
        _commit(
            salt_store,
            salt_origin,
            "duplicate-salt",
            salt_receipts[-1].current_state_commitment,
            dataclasses.replace(
                salt_sealed,
                constraint_salts=(salt_sealed.candidate_salts[0], *salt_sealed.constraint_salts[1:]),
            ),
        )
    first_seal = _commit(
        salt_store,
        salt_origin,
        "salt-a-seal",
        salt_receipts[-1].current_state_commitment,
        salt_sealed,
    )
    second_events = _batch_events("salt-b", iteration=1)
    second_receipts = _commit_sequence(
        salt_store, salt_origin, second_events[:2], "salt-b"
    )
    assert second_receipts[0].resulting_state_commitment != first_seal.resulting_state_commitment
    with Raises("reused"):
        _commit(
            salt_store,
            salt_origin,
            "cross-batch-salt",
            second_receipts[-1].current_state_commitment,
            dataclasses.replace(
                second_events[2],
                candidate_salts=(salt_sealed.candidate_salts[0], *second_events[2].candidate_salts[1:]),
            ),
        )


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
