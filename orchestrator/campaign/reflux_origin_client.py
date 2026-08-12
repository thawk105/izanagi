"""Capability-bound access to the reflux origin ledger.

The public operations in this module never accept a raw ``origin_id`` or a
caller-selected ledger store.  Every operation requires an issuer-bound
``OriginBindingCapability`` and rechecks its authority blob, cell, manifest,
and store scope while holding the ledger lock.

Removing the raw public ledger API does not prevent a same-process caller
from invoking ``_production_store()`` or ``_fixture_store_for_test()``, then
``_locked()`` and ``_commit_locked()`` directly.  Underscore naming is not a
trust boundary.  Closing that route would change the ledger's acceptance set
and is outside this wave.  This wiring therefore holds only under the
operational assumption that callers do not invoke the ledger's private seams.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from . import reflux_origin_binding as binding
from . import reflux_origin_ledger as ledger
from .reflux_origin_artifacts import canonical_json_bytes


__all__ = [
    "OriginLedgerClient",
    "OriginLedgerClientError",
    "require_origin_ledger_client",
]


class OriginLedgerClientError(ValueError):
    """A client, capability, authority, or formal result did not match."""


_ISSUED_CLIENT_STORES: dict[
    object, tuple[ledger._Store, tuple[object, ...]]
] = {}
_PROGRESS_EVENT_TYPES = (
    ledger.BatchReserved,
    ledger.BatchReservationAbandoned,
    ledger.BatchCommitted,
    ledger.BatchResultsPrepared,
    ledger.BatchSealed,
)


def _reject(message: str) -> None:
    raise OriginLedgerClientError(message)


def _store_identity(derived: ledger._Store) -> tuple[object, ...]:
    return (
        derived.repo_root,
        derived.common_dir,
        derived.runtime_root,
        derived.authority_path,
        derived.committed_ref,
        derived.fixture,
    )


class OriginLedgerClient:
    """An immutable, module-issued handle to exactly one derived ledger store."""

    __slots__ = ("_store", "_seal")

    def __new__(cls):
        del cls
        raise TypeError("OriginLedgerClient values must be created by a factory")

    def __setattr__(self, name: str, value: object) -> None:
        del name, value
        raise AttributeError("OriginLedgerClient is immutable")

    @staticmethod
    def _issue(derived: ledger._Store) -> "OriginLedgerClient":
        if type(derived) is not ledger._Store:
            raise TypeError("derived ledger store has the wrong exact type")
        client = object.__new__(OriginLedgerClient)
        seal = object()
        object.__setattr__(client, "_store", derived)
        object.__setattr__(client, "_seal", seal)
        _ISSUED_CLIENT_STORES[seal] = (derived, _store_identity(derived))
        return client

    @staticmethod
    def production() -> "OriginLedgerClient":
        """Derive the fixed production store from the ledger module location."""

        return OriginLedgerClient._issue(ledger._production_store())

    @staticmethod
    def for_fixture_repository(
        fixture_repository: os.PathLike[str] | str,
        *,
        committed_ref: str = "HEAD",
        initialize: bool = True,
    ) -> "OriginLedgerClient":
        """Create an explicit client for one complete temporary Git repository."""

        fixture = Path(fixture_repository).resolve(strict=True)
        production_repository = Path(ledger.__file__).resolve(strict=True).parents[2]
        if fixture == production_repository:
            _reject("fixture factory cannot target the production repository")
        derived = ledger._fixture_store_for_test(
            fixture,
            committed_ref,
            initialize=initialize,
        )
        if type(derived) is not ledger._Store or derived.fixture is not True:
            _reject("fixture factory did not derive an exact fixture store")
        return OriginLedgerClient._issue(derived)

    @property
    def store_scope(self) -> Literal["production", "fixture"]:
        """Return the scope derived from the sealed store, never caller state."""

        derived = _assert_exact_client(self)
        return "fixture" if derived.fixture else "production"

    def read_origin(
        self,
        capability: binding.OriginBindingCapability,
    ) -> ledger.OriginSnapshot:
        value, derived = _prepare_call(self, capability)
        with ledger._locked(derived) as authority:
            _revalidate_current_authority(value, derived, authority)
            return ledger._read_origin_locked(derived, authority, value.origin_id)

    def reserve_batch(
        self,
        capability: binding.OriginBindingCapability,
        *,
        operation_id: str,
        expected_state_commitment: str,
        reservation: ledger.BatchReserved,
    ) -> ledger.EventReceipt:
        if type(reservation) is not ledger.BatchReserved:
            raise TypeError("reservation must be an exact BatchReserved")
        return _commit_progress(
            self,
            capability,
            operation_id=operation_id,
            expected_state_commitment=expected_state_commitment,
            event=reservation,
        )

    def commit_event(
        self,
        capability: binding.OriginBindingCapability,
        *,
        operation_id: str,
        expected_state_commitment: str,
        event: ledger.OriginEvent,
    ) -> ledger.EventReceipt:
        """Commit a non-terminal progress event; raw origin seals are rejected."""

        if type(event) not in _PROGRESS_EVENT_TYPES:
            raise TypeError("event must be an exact non-terminal ledger event")
        return _commit_progress(
            self,
            capability,
            operation_id=operation_id,
            expected_state_commitment=expected_state_commitment,
            event=event,
        )

    def read_sealed_batch(
        self,
        capability: binding.OriginBindingCapability,
        batch_id: str,
    ) -> ledger.SealedBatch:
        value, derived = _prepare_call(self, capability)
        with ledger._locked(derived) as authority:
            _revalidate_current_authority(value, derived, authority)
            return ledger._read_sealed_batch_locked(
                derived, authority, value.origin_id, batch_id
            )

    def read_sealed_batches(
        self,
        capability: binding.OriginBindingCapability,
    ) -> tuple[ledger.SealedBatch, ...]:
        value, derived = _prepare_call(self, capability)
        with ledger._locked(derived) as authority:
            _revalidate_current_authority(value, derived, authority)
            replay = ledger._replay(derived, authority)
            batches = replay.states[value.origin_id].sealed_batches
            return tuple(batches[key] for key in sorted(batches))

    def commit_formal_result(
        self,
        capability: binding.OriginBindingCapability,
        *,
        operation_id: str,
        expected_state_commitment: str,
        result: object,
    ) -> ledger.EventReceipt:
        """Map the closed formal result algebra to the sole aborted terminal event."""

        from . import reflux_formal_consumer as formal

        value, derived = _prepare_call(self, capability)
        if type(result) is formal.P6Unavailable:
            receipt = result.receipt
            supplied_decision = result.decision
        elif type(result) is formal.FormalContractRejected:
            receipt = None
            supplied_decision = result.decision
        else:
            raise TypeError("result must be an exact FormalConsumerResult")
        if type(supplied_decision) is not formal.AbortedOriginDecision:
            raise TypeError("formal result decision has the wrong exact type")
        if type(result.projection) is not formal.OriginTerminalProjection:
            raise TypeError("formal result projection has the wrong exact type")
        if (
            result.projection.authority_blob_sha256 != value.authority_blob_sha256
            or result.projection.origin_id != value.origin_id
            or result.projection.cell_key != value.cell_key
            or result.projection.terminal_payload_sha256
            != supplied_decision.terminal_payload_sha256
        ):
            _reject("formal result differs from the capability binding")
        if receipt is not None and (
            receipt.authority_blob_sha256 != value.authority_blob_sha256
            or receipt.source_closure_sha256 != value.source_closure_sha256
            or receipt.origin_id != value.origin_id
        ):
            _reject("formal receipt differs from the capability binding")
        if receipt is not None:
            formal_receipt_sha256 = formal.formal_consumer_receipt_sha256(receipt)
            evidence_root_sha256 = hashlib.sha256(
                canonical_json_bytes(list(receipt.evidence_sha256s))
            ).hexdigest()
            if (
                receipt.evidence_root_sha256 != evidence_root_sha256
                or result.projection.formal_receipt_sha256
                != formal_receipt_sha256
                or result.projection.evidence_root_sha256
                != evidence_root_sha256
            ):
                _reject("formal result projection differs from inspected evidence")
        with ledger._locked(derived) as authority:
            _revalidate_current_authority(value, derived, authority)
            decision = (
                supplied_decision
                if receipt is None
                else formal.consume_formal_consumer_receipt(
                    receipt,
                    operation_id=operation_id,
                    input_state_commitment=expected_state_commitment,
                    decision=supplied_decision,
                )
            )
            event = ledger.OriginSealed(
                aborted=True,
                constraint_class_sha256s=(),
                batch_count=decision.batch_count,
                tombstone_count=decision.tombstone_count,
                sealed_queries=decision.sealed_queries,
                tombstoned_queries=decision.tombstoned_queries,
                forfeited_iterations=decision.forfeited_iterations,
                forfeited_queries=decision.forfeited_queries,
            )
            return ledger._commit_locked(
                derived,
                authority,
                origin_id=value.origin_id,
                operation_id=operation_id,
                expected_state_commitment=expected_state_commitment,
                event=event,
            )


def _assert_exact_client(client: object) -> ledger._Store:
    if type(client) is not OriginLedgerClient:
        _reject("client must be the exact module-issued OriginLedgerClient")
    try:
        issued = _ISSUED_CLIENT_STORES.get(client._seal)
    except (AttributeError, TypeError):
        issued = None
    if (
        issued is None
        or issued[0] is not client._store
        or issued[1] != _store_identity(client._store)
    ):
        _reject("client store differs from its factory-issued store")
    derived = issued[0]
    if type(derived) is not ledger._Store:
        _reject("client store has the wrong exact type")
    return derived


def _issued_capability(
    capability: object,
) -> binding.OriginBindingCapability:
    if type(capability) is not binding.OriginBindingCapability:
        _reject("capability must be an exact OriginBindingCapability")
    try:
        return binding.assert_issued_origin_binding_capability(capability)
    except Exception as exc:
        raise OriginLedgerClientError(f"invalid issued capability: {exc}") from exc


def _scope_of(derived: ledger._Store) -> Literal["production", "fixture"]:
    return "fixture" if derived.fixture else "production"


def _require_scope(
    capability: binding.OriginBindingCapability,
    derived: ledger._Store,
) -> None:
    client_scope = _scope_of(derived)
    if capability.store_scope == "production" and client_scope != "production":
        _reject("production capability requires the production client")
    if capability.store_scope == "fixture" and client_scope != "fixture":
        _reject("fixture capability requires an explicit fixture client")
    if capability.store_scope not in {"production", "fixture"}:
        _reject("capability has an unsupported store scope")


def _prepare_call(
    client: object,
    capability: object,
) -> tuple[binding.OriginBindingCapability, ledger._Store]:
    derived = _assert_exact_client(client)
    value = _issued_capability(capability)
    _require_scope(value, derived)
    return value, derived


def _revalidate_current_authority(
    capability: binding.OriginBindingCapability,
    derived: ledger._Store,
    authority: ledger._Authority,
) -> None:
    _require_scope(capability, derived)
    if not derived.fixture and not authority.entries:
        _reject("the current production authority has no issuable origins")
    if authority.blob_sha256 != capability.authority_blob_sha256:
        _reject("current authority blob differs from the capability")
    entry = authority.entries.get(capability.origin_id)
    if entry is None:
        _reject("capability origin is absent from the current authority")
    if entry.cell_key != capability.cell_key:
        _reject("current authority cell differs from the capability")
    manifest = entry.manifest
    workload = manifest.workload
    expected_workload = capability.authority_workload
    if type(workload) not in (dict, MappingProxyType):
        _reject("current authority workload has an unexpected type")
    if (
        workload.get("descriptor_sha256") != expected_workload.descriptor_sha256
        or workload.get("records") != expected_workload.records
        or workload.get("threads") != expected_workload.threads
        or manifest.axis_semantics_sha256 != capability.axis_semantics_sha256
        or manifest.verifier_policy_sha256 != capability.verifier_policy_sha256
        or manifest.environment_contract_sha256
        != capability.environment_contract_sha256
    ):
        _reject("current authority manifest differs from the capability cell")


def _commit_progress(
    client: OriginLedgerClient,
    capability: binding.OriginBindingCapability,
    *,
    operation_id: str,
    expected_state_commitment: str,
    event: ledger.OriginEvent,
) -> ledger.EventReceipt:
    value, derived = _prepare_call(client, capability)
    with ledger._locked(derived) as authority:
        _revalidate_current_authority(value, derived, authority)
        return ledger._commit_locked(
            derived,
            authority,
            origin_id=value.origin_id,
            operation_id=operation_id,
            expected_state_commitment=expected_state_commitment,
            event=event,
        )


def require_origin_ledger_client(
    capability: binding.OriginBindingCapability,
    client: OriginLedgerClient | None = None,
) -> OriginLedgerClient:
    """Resolve production only after capability validation; fixture is explicit."""

    value = _issued_capability(capability)
    if client is None:
        if value.store_scope == "fixture":
            _reject("fixture capability requires an explicit fixture client")
        client = OriginLedgerClient.production()
    derived = _assert_exact_client(client)
    _require_scope(value, derived)
    return client
