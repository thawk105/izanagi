"""Typed reflux-origin ledger client boundary tests."""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator.campaign import reflux_formal_consumer as formal
from orchestrator.campaign import reflux_origin_binding as binding
from orchestrator.campaign import reflux_origin_client as client_module
from orchestrator.campaign import reflux_origin_ledger as ledger
from orchestrator.tests import reflux_origin_fixture_builder as fixtures


_BANNED_PARAMETERS = {
    "store",
    "root",
    "path",
    "repository_root",
    "ledger_root",
}
_ARM_BINDING_DIGEST_SHA256 = "a" * 64


@dataclass(frozen=True)
class _Case:
    repo: Path
    capability: binding.OriginBindingCapability
    client: client_module.OriginLedgerClient


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        env=ledger._git_env(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _issued_capability(
    *, scope: str = "fixture"
) -> binding.OriginBindingCapability:
    record = fixtures.build_launch_admission_inputs(store_scope=scope)
    workload = record["authority_workload"]
    seal = object()
    capability = binding.OriginBindingCapability(
        authority_blob_sha256=record["authority_blob_sha256"],
        source_closure_sha256=record["source_closure_sha256"],
        origin_id=record["origin_id"],
        cell_key=record["cell_key"],
        authority_workload=binding.AuthorityWorkload(
            descriptor_sha256=workload["descriptor_sha256"],
            records=workload["records"],
            threads=workload["threads"],
        ),
        axis_semantics_sha256=record["axis_semantics_sha256"],
        verifier_policy_sha256=record["verifier_policy_sha256"],
        environment_contract_sha256=record["environment_contract_sha256"],
        campaign_id=record["campaign_id"],
        trial_workload=record["trial_workload"],
        measurement_head=record["measurement_head"],
        store_scope=scope,
        _seal=seal,
    )
    binding._ISSUED_CAPABILITY_FIELDS[seal] = binding._capability_fields(capability)
    return capability


@pytest.fixture
def case(tmp_path: Path) -> _Case:
    frozen = fixtures.build_fixture_repository(tmp_path / "frozen")
    repo = tmp_path / "fixture-repository"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Typed Client Test")
    _git(repo, "config", "user.email", "typed-client@example.invalid")
    authority = repo / ledger.AUTHORITY_RELATIVE_PATH
    authority.parent.mkdir(parents=True)
    shutil.copyfile(frozen.authority_manifest_path, authority)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture authority")
    capability = _issued_capability()
    fixture_client = client_module.OriginLedgerClient.for_fixture_repository(repo)
    return _Case(repo, capability, fixture_client)


def _decision(**changes: int) -> formal.AbortedOriginDecision:
    counters = {
        "batch_count": 0,
        "tombstone_count": 0,
        "sealed_queries": 0,
        "tombstoned_queries": 0,
        "forfeited_iterations": 0,
        "forfeited_queries": 0,
        **changes,
    }
    provisional = formal.AbortedOriginDecision(
        **counters, terminal_payload_sha256="0" * 64
    )
    return dataclasses.replace(
        provisional,
        terminal_payload_sha256=formal.aborted_origin_payload_sha256(provisional),
    )


def _p6_result(
    capability: binding.OriginBindingCapability,
    *,
    operation_id: str,
    input_state_commitment: str,
    decision: formal.AbortedOriginDecision,
) -> formal.P6Unavailable:
    evidence_sha256s = ("3" * 64,)
    evidence_root_sha256 = hashlib.sha256(
        json.dumps(
            list(evidence_sha256s),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    receipt = formal.FormalConsumerReceipt(
        operation_id=operation_id,
        authority_blob_sha256=capability.authority_blob_sha256,
        source_closure_sha256=capability.source_closure_sha256,
        run_plan_sha256="1" * 64,
        origin_id=capability.origin_id,
        input_state_commitment=input_state_commitment,
        origin_sealed_payload_sha256=decision.terminal_payload_sha256,
        evidence_sha256s=evidence_sha256s,
        evidence_root_sha256=evidence_root_sha256,
        enforcement_arm="fixture-arm",
        arm_binding_digest_sha256=_ARM_BINDING_DIGEST_SHA256,
        generator_closure={},
        reason_code=formal.FormalReasonCode.P6_UNAVAILABLE,
        _issuer=formal._RECEIPT_CONSTRUCTOR,
    )
    formal._ISSUED_RECEIPTS[receipt._seal] = formal.canonical_json_bytes(
        formal.formal_consumer_receipt_record(receipt)
    )
    projection = formal.OriginTerminalProjection(
        schema_version=formal.ORIGIN_TERMINAL_PROJECTION_SCHEMA_VERSION,
        reason_code=formal.FormalReasonCode.P6_UNAVAILABLE,
        formal_receipt_sha256=formal.formal_consumer_receipt_sha256(receipt),
        evidence_root_sha256=receipt.evidence_root_sha256,
        authority_blob_sha256=capability.authority_blob_sha256,
        origin_id=capability.origin_id,
        cell_key=capability.cell_key,
        terminal_payload_sha256=decision.terminal_payload_sha256,
        arm_binding_digest_sha256=_ARM_BINDING_DIGEST_SHA256,
    )
    return formal.P6Unavailable(
        formal.FormalReasonCode.P6_UNAVAILABLE,
        receipt,
        decision,
        projection,
    )


def test_read_reserve_commit_and_seal_reject_absent_capability(
    case: _Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    reached: list[str] = []

    def forbidden(label: str) -> None:
        reached.append(label)
        raise AssertionError("ledger operation reached without a capability")

    monkeypatch.setattr(ledger, "_FAULT_HOOK", forbidden)
    reservation = ledger.BatchReserved("batch-0", 0, 2, 0)
    calls = (
        lambda: case.client.read_origin(None),
        lambda: case.client.reserve_batch(
            None,
            operation_id="reserve-none",
            expected_state_commitment="0" * 64,
            reservation=reservation,
        ),
        lambda: case.client.commit_event(
            None,
            operation_id="commit-none",
            expected_state_commitment="0" * 64,
            event=reservation,
        ),
        lambda: case.client.commit_formal_result(
            None,
            operation_id="seal-none",
            expected_state_commitment="0" * 64,
            result=None,
        ),
    )
    for call in calls:
        with pytest.raises(client_module.OriginLedgerClientError, match="capability"):
            call()
    assert reached == []


def test_fixture_capability_without_client_never_resolves_production(
    case: _Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    reached = False

    def forbidden():
        nonlocal reached
        reached = True
        raise AssertionError("production store fallback was reached")

    monkeypatch.setattr(ledger, "_production_store", forbidden)
    with pytest.raises(
        client_module.OriginLedgerClientError, match="explicit fixture client"
    ):
        client_module.require_origin_ledger_client(case.capability)
    assert reached is False


def test_production_capability_rejects_fixture_client(
    case: _Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    production_capability = _issued_capability(scope="production")
    monkeypatch.setattr(
        binding,
        "assert_issued_origin_binding_capability",
        lambda value: value,
    )
    with pytest.raises(
        client_module.OriginLedgerClientError, match="production capability"
    ):
        client_module.require_origin_ledger_client(
            production_capability, case.client
        )


def test_fixture_capability_rejects_production_client(case: _Case) -> None:
    production_client = client_module.OriginLedgerClient.production()
    with pytest.raises(
        client_module.OriginLedgerClientError, match="fixture capability"
    ):
        client_module.require_origin_ledger_client(
            case.capability, production_client
        )


def test_store_scope_is_factory_derived_and_immutable(case: _Case) -> None:
    assert case.client.store_scope == "fixture"
    with pytest.raises(AttributeError, match="immutable"):
        case.client.store_scope = "production"
    with pytest.raises(AttributeError, match="immutable"):
        case.client._store = ledger._production_store()
    assert case.client.store_scope == "fixture"


def test_client_must_have_the_exact_module_type(case: _Case) -> None:
    class DerivedClient(client_module.OriginLedgerClient):
        pass

    forged = object.__new__(DerivedClient)
    with pytest.raises(client_module.OriginLedgerClientError, match="exact"):
        client_module.require_origin_ledger_client(case.capability, forged)


def test_mutated_derived_store_scope_is_rejected(case: _Case) -> None:
    derived = case.client._store
    object.__setattr__(derived, "fixture", False)
    try:
        with pytest.raises(
            client_module.OriginLedgerClientError, match="factory-issued store"
        ):
            case.client.read_origin(case.capability)
    finally:
        object.__setattr__(derived, "fixture", True)


def test_public_constructor_factories_and_methods_take_no_store_selector() -> None:
    public_calls = (
        client_module.OriginLedgerClient,
        client_module.OriginLedgerClient.production,
        client_module.OriginLedgerClient.for_fixture_repository,
        client_module.OriginLedgerClient.read_origin,
        client_module.OriginLedgerClient.reserve_batch,
        client_module.OriginLedgerClient.commit_event,
        client_module.OriginLedgerClient.read_sealed_batch,
        client_module.OriginLedgerClient.read_sealed_batches,
        client_module.OriginLedgerClient.commit_formal_result,
        client_module.require_origin_ledger_client,
    )
    for public_call in public_calls:
        assert not (
            _BANNED_PARAMETERS & set(inspect.signature(public_call).parameters)
        )
    with pytest.raises(TypeError, match="created by a factory"):
        client_module.OriginLedgerClient()


def test_raw_ledger_attributes_are_absent() -> None:
    for name in ("read_origin", "commit_event", "read_sealed_batch"):
        assert not hasattr(ledger, name)
        assert name not in ledger.__all__


def test_reserve_and_progress_commit_preserve_ledger_acceptance(case: _Case) -> None:
    initial = case.client.read_origin(case.capability)
    reserved = case.client.reserve_batch(
        case.capability,
        operation_id="typed-reserve",
        expected_state_commitment=initial.state_commitment,
        reservation=ledger.BatchReserved("batch-0", 0, 2, 0),
    )
    assert reserved.origin_id == case.capability.origin_id
    after_reserve = case.client.read_origin(case.capability)
    assert after_reserve.phase == "BATCH_RESERVED"
    abandoned = case.client.commit_event(
        case.capability,
        operation_id="typed-abandon",
        expected_state_commitment=after_reserve.state_commitment,
        event=ledger.BatchReservationAbandoned("batch-0"),
    )
    assert abandoned.origin_id == case.capability.origin_id
    assert case.client.read_origin(case.capability).phase == "IDLE"


def test_progress_api_rejects_raw_origin_seal(case: _Case) -> None:
    initial = case.client.read_origin(case.capability)
    raw_terminal = ledger.OriginSealed(
        aborted=True,
        constraint_class_sha256s=(),
        batch_count=0,
        tombstone_count=0,
        sealed_queries=0,
        tombstoned_queries=0,
        forfeited_iterations=0,
        forfeited_queries=0,
    )
    with pytest.raises(TypeError, match="non-terminal"):
        case.client.commit_event(
            case.capability,
            operation_id="raw-terminal",
            expected_state_commitment=initial.state_commitment,
            event=raw_terminal,
        )
    assert case.client.read_origin(case.capability).phase == "IDLE"


def test_p6_unavailable_can_only_commit_aborted_origin(
    case: _Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = case.client.read_origin(case.capability)
    decision = _decision()
    result = _p6_result(
        case.capability,
        operation_id="typed-terminal",
        input_state_commitment=snapshot.state_commitment,
        decision=decision,
    )
    observed: list[ledger.OriginSealed] = []

    def capture(*args, **kwargs):
        del args
        observed.append(kwargs["event"])
        return object()

    monkeypatch.setattr(ledger, "_commit_locked", capture)
    case.client.commit_formal_result(
        case.capability,
        operation_id="typed-terminal",
        expected_state_commitment=snapshot.state_commitment,
        result=result,
    )
    assert len(observed) == 1
    assert type(observed[0]) is ledger.OriginSealed
    assert observed[0].aborted is True
    assert observed[0].constraint_class_sha256s == ()


def test_receipt_rejects_wrong_input_state_commitment(case: _Case) -> None:
    snapshot = case.client.read_origin(case.capability)
    result = _p6_result(
        case.capability,
        operation_id="wrong-state",
        input_state_commitment=snapshot.state_commitment,
        decision=_decision(),
    )
    with pytest.raises(formal.FormalReceiptError) as raised:
        case.client.commit_formal_result(
            case.capability,
            operation_id="wrong-state",
            expected_state_commitment="f" * 64,
            result=result,
        )
    assert raised.value.reason_code is formal.FormalReceiptReason.STATE


def test_receipt_rejects_wrong_terminal_payload_digest(case: _Case) -> None:
    snapshot = case.client.read_origin(case.capability)
    result = _p6_result(
        case.capability,
        operation_id="wrong-payload",
        input_state_commitment=snapshot.state_commitment,
        decision=_decision(),
    )
    changed_decision = dataclasses.replace(result.decision, batch_count=1)
    changed = dataclasses.replace(result, decision=changed_decision)
    assert (
        changed.projection.terminal_payload_sha256
        == changed.decision.terminal_payload_sha256
    )
    assert (
        formal.aborted_origin_payload_sha256(changed.decision)
        != changed.decision.terminal_payload_sha256
    )
    with pytest.raises(formal.FormalReceiptError) as raised:
        case.client.commit_formal_result(
            case.capability,
            operation_id="wrong-payload",
            expected_state_commitment=snapshot.state_commitment,
            result=changed,
        )
    assert raised.value.reason_code is formal.FormalReceiptReason.PAYLOAD


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("formal_receipt_sha256", "0" * 64),
        ("evidence_root_sha256", "f" * 64),
    ],
)
def test_client_rederives_projection_evidence_references(
    case: _Case, field: str, value: str
) -> None:
    snapshot = case.client.read_origin(case.capability)
    result = _p6_result(
        case.capability,
        operation_id=f"wrong-projection-{field}",
        input_state_commitment=snapshot.state_commitment,
        decision=_decision(),
    )
    changed = dataclasses.replace(
        result,
        projection=dataclasses.replace(result.projection, **{field: value}),
    )
    with pytest.raises(
        client_module.OriginLedgerClientError, match="inspected evidence"
    ):
        case.client.commit_formal_result(
            case.capability,
            operation_id=result.receipt.operation_id,
            expected_state_commitment=snapshot.state_commitment,
            result=changed,
        )


def test_client_rederives_receipt_evidence_root_from_digest_list(
    case: _Case,
) -> None:
    snapshot = case.client.read_origin(case.capability)
    result = _p6_result(
        case.capability,
        operation_id="wrong-receipt-evidence-root",
        input_state_commitment=snapshot.state_commitment,
        decision=_decision(),
    )
    original = result.receipt
    receipt = formal.FormalConsumerReceipt(
        operation_id=original.operation_id,
        authority_blob_sha256=original.authority_blob_sha256,
        source_closure_sha256=original.source_closure_sha256,
        run_plan_sha256=original.run_plan_sha256,
        origin_id=original.origin_id,
        input_state_commitment=original.input_state_commitment,
        origin_sealed_payload_sha256=original.origin_sealed_payload_sha256,
        evidence_sha256s=original.evidence_sha256s,
        evidence_root_sha256="f" * 64,
        enforcement_arm=original.enforcement_arm,
        arm_binding_digest_sha256=original.arm_binding_digest_sha256,
        generator_closure=original.generator_closure,
        reason_code=original.reason_code,
        _issuer=formal._RECEIPT_CONSTRUCTOR,
    )
    formal._ISSUED_RECEIPTS[receipt._seal] = formal.canonical_json_bytes(
        formal.formal_consumer_receipt_record(receipt)
    )
    projection = dataclasses.replace(
        result.projection,
        formal_receipt_sha256=formal.formal_consumer_receipt_sha256(receipt),
        evidence_root_sha256=receipt.evidence_root_sha256,
    )
    changed = dataclasses.replace(result, receipt=receipt, projection=projection)
    with pytest.raises(
        client_module.OriginLedgerClientError, match="inspected evidence"
    ):
        case.client.commit_formal_result(
            case.capability,
            operation_id=receipt.operation_id,
            expected_state_commitment=snapshot.state_commitment,
            result=changed,
        )


def test_formal_receipt_exact_replay_matches_ledger_replay(case: _Case) -> None:
    snapshot = case.client.read_origin(case.capability)
    result = _p6_result(
        case.capability,
        operation_id="terminal-replay",
        input_state_commitment=snapshot.state_commitment,
        decision=_decision(),
    )
    first = case.client.commit_formal_result(
        case.capability,
        operation_id="terminal-replay",
        expected_state_commitment=snapshot.state_commitment,
        result=result,
    )
    second = case.client.commit_formal_result(
        case.capability,
        operation_id="terminal-replay",
        expected_state_commitment=snapshot.state_commitment,
        result=result,
    )
    assert first.replayed is False
    assert second.replayed is True
    assert first.event_sha256 == second.event_sha256


def test_each_call_rechecks_current_authority_blob(case: _Case) -> None:
    assert case.client.read_origin(case.capability).phase == "IDLE"
    authority = case.repo / ledger.AUTHORITY_RELATIVE_PATH
    authority.write_bytes(
        b'{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}\n'
    )
    _git(case.repo, "add", str(ledger.AUTHORITY_RELATIVE_PATH))
    _git(case.repo, "commit", "-qm", "replace authority")
    with pytest.raises(client_module.OriginLedgerClientError, match="authority blob"):
        case.client.read_origin(case.capability)


def test_each_call_rechecks_current_authority_cell(case: _Case) -> None:
    changed = dataclasses.replace(_issued_capability(), cell_key="f" * 64)
    binding._ISSUED_CAPABILITY_FIELDS[changed._seal] = binding._capability_fields(
        changed
    )
    with pytest.raises(client_module.OriginLedgerClientError, match="cell"):
        case.client.read_origin(changed)


def test_production_client_rejects_empty_current_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "empty-production-repository"
    copied_module = repo / "orchestrator/campaign/reflux_origin_ledger.py"
    copied_module.parent.mkdir(parents=True)
    shutil.copyfile(ledger.__file__, copied_module)
    authority = repo / ledger.AUTHORITY_RELATIVE_PATH
    authority.write_bytes(
        b'{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}\n'
    )
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Empty Production Test")
    _git(repo, "config", "user.email", "empty-production@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "empty production authority")
    ledger._fixture_store_for_test(repo)
    monkeypatch.setattr(ledger, "__file__", str(copied_module))
    monkeypatch.setattr(
        binding,
        "assert_issued_origin_binding_capability",
        lambda value: value,
    )
    production_capability = _issued_capability(scope="production")
    production_client = client_module.OriginLedgerClient.production()
    with pytest.raises(
        client_module.OriginLedgerClientError, match="no issuable origins"
    ):
        production_client.read_origin(production_capability)


def test_fixture_factory_cannot_target_production_repository() -> None:
    production_repository = Path(ledger.__file__).resolve().parents[2]
    with pytest.raises(
        client_module.OriginLedgerClientError, match="production repository"
    ):
        client_module.OriginLedgerClient.for_fixture_repository(
            production_repository, initialize=False
        )
