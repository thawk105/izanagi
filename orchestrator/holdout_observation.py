# -*- coding: utf-8 -*-
"""Freeze-derived holdout classification and observation capabilities.

This is a neutral, stdlib-only leaf.  The campaign layer remains responsible
for verifying freeze/protocol authority and durable attempt consumption before
creating the private receipt consumed by this module's private issuer path.

Python code with permission to import private names can construct or invoke
those private hooks; this module does not claim to prevent that.  The boundary
provided here is narrower: no supported public API can issue an observation
token without the campaign ledger's durable-consumption path.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import threading
from typing import Any

__all__ = (
    "HoldoutObservationAdmission",
    "HoldoutObservationError",
    "MinimalHoldoutSignature",
    "assert_holdout_observation_admitted",
    "assert_issued_holdout_observation",
    "classify_minimal_holdout_signature",
    "normalized_direct_gflags",
    "protected_signatures_from_verified_freeze",
)


class HoldoutObservationError(RuntimeError):
    """A holdout observation request is malformed or not admitted."""


@dataclass(frozen=True, slots=True)
class MinimalHoldoutSignature:
    """Names kept distinct even where the current freeze uses equal strings."""

    freeze_holdout_key: str
    freeze_candidate_id: str
    trial_workload_name: str
    ycsb_rratio: str


@dataclass(frozen=True, slots=True)
class HoldoutObservationAdmission:
    """Attempt-bound identity token; field equality never establishes issuance."""

    freeze_holdout_key: str
    freeze_candidate_id: str
    trial_workload_name: str
    ycsb_rratio: str
    attempt_id: str
    permitted_run_once_calls: int


@dataclass(frozen=True, slots=True)
class _DurableAttemptConsumptionReceipt:
    """Private handoff created only after Unit B's durable ticket consume."""

    attempt_id: str
    permitted_run_once_calls: int


@dataclass(frozen=True, slots=True)
class _IssuedAdmissionState:
    token: HoldoutObservationAdmission
    signature: MinimalHoldoutSignature
    remaining_run_once_calls: int


# This neutral table is deliberately freeze-shaped.  It is not production
# authority: every issuance also derives the set from the already-verified
# freeze document supplied by the campaign layer and requires exact equality.
_NEUTRAL_HOLDOUTS: Mapping[str, Mapping[str, Any]] = {
    "rr80": {
        "candidate_id": "H1",
        "ycsb": {"ycsb_rratio": "80"},
    },
    "rr20": {
        "candidate_id": "H2",
        "ycsb": {"ycsb_rratio": "20"},
    },
}

_INDIRECT_GFLAGS = frozenset({"flagfile", "fromenv", "tryfromenv"})
_UINT64_MAX = (1 << 64) - 1


def _require_nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise HoldoutObservationError(f"invalid verified freeze {field}")
    return value


def _derive_protected_signatures(
    verified_freeze_document: Mapping[str, object],
) -> frozenset[MinimalHoldoutSignature]:
    """Derive signatures solely from a verified freeze's ``holdouts`` map."""

    if not isinstance(verified_freeze_document, Mapping):
        raise HoldoutObservationError("verified freeze document must be a mapping")
    holdouts = verified_freeze_document.get("holdouts")
    if not isinstance(holdouts, Mapping) or not holdouts:
        raise HoldoutObservationError("verified freeze holdouts must be a nonempty mapping")

    signatures: set[MinimalHoldoutSignature] = set()
    ratios: set[str] = set()
    for raw_key, raw_entry in holdouts.items():
        freeze_holdout_key = _require_nonempty_string(raw_key, "holdout key")
        if not isinstance(raw_entry, Mapping):
            raise HoldoutObservationError(
                f"invalid verified freeze holdout entry: {freeze_holdout_key}"
            )
        freeze_candidate_id = _require_nonempty_string(
            raw_entry.get("candidate_id"),
            f"holdouts.{freeze_holdout_key}.candidate_id",
        )
        ycsb = raw_entry.get("ycsb")
        if not isinstance(ycsb, Mapping):
            raise HoldoutObservationError(
                f"invalid verified freeze holdouts.{freeze_holdout_key}.ycsb"
            )
        ratio = _require_nonempty_string(
            ycsb.get("ycsb_rratio"),
            f"holdouts.{freeze_holdout_key}.ycsb.ycsb_rratio",
        )
        if ratio in ratios:
            raise HoldoutObservationError(
                f"ambiguous verified freeze ycsb_rratio: {ratio}"
            )
        ratios.add(ratio)
        signatures.add(MinimalHoldoutSignature(
            freeze_holdout_key=freeze_holdout_key,
            freeze_candidate_id=freeze_candidate_id,
            trial_workload_name=freeze_holdout_key,
            ycsb_rratio=ratio,
        ))
    return frozenset(signatures)


_NEUTRAL_PROTECTED_SIGNATURES = _derive_protected_signatures(
    {"holdouts": _NEUTRAL_HOLDOUTS}
)
_NEUTRAL_BY_RATIO = {
    signature.ycsb_rratio: signature
    for signature in _NEUTRAL_PROTECTED_SIGNATURES
}


def protected_signatures_from_verified_freeze(
    verified_freeze_document: Mapping[str, object],
) -> frozenset[MinimalHoldoutSignature]:
    """Return the production protected set from the fixed neutral table."""

    return _protected_signatures_from_verified_freeze_core(
        verified_freeze_document,
    )


def _protected_signatures_from_verified_freeze_core(
    verified_freeze_document: Mapping[str, object],
    *,
    _neutral_holdouts: Mapping[str, Mapping[str, object]] | None = None,
) -> frozenset[MinimalHoldoutSignature]:
    """Return the protected set, rejecting drift from the neutral known set.

    The caller must first establish that ``verified_freeze_document`` is the
    verified authority document.  This leaf validates the holdout projection
    and fails closed on additions, removals, or binding changes.
    """

    derived = _derive_protected_signatures(verified_freeze_document)
    if _neutral_holdouts is None:
        if derived != _NEUTRAL_PROTECTED_SIGNATURES:
            raise HoldoutObservationError(
                "verified freeze holdout signatures do not exactly match the neutral set"
            )
        return derived
    expected = _derive_protected_signatures({"holdouts": _neutral_holdouts})
    if derived != expected:
        raise HoldoutObservationError(
            "verified freeze holdout signatures do not exactly match the neutral set"
        )
    return derived


def normalized_direct_gflags(gflags: Sequence[str]) -> dict[str, str]:
    """Normalize direct gflags with last-wins semantics.

    Both one- and two-dash forms are accepted.  Inputs that can cause gflags
    to obtain values indirectly are rejected before classification.
    """

    effective: dict[str, str] = {}
    for raw in gflags:
        if type(raw) is not str:
            raise HoldoutObservationError("gflags must contain exact strings only")
        if not raw.startswith("-") or raw == "-":
            continue
        body = raw[2:] if raw.startswith("--") else raw[1:]
        name, separator, value = body.partition("=")
        if name in _INDIRECT_GFLAGS:
            raise HoldoutObservationError(f"indirect gflags input is forbidden: {name}")
        if separator and name:
            effective[name] = value
    ratio = effective.get("ycsb_rratio")
    if ratio is not None:
        if (not ratio or not ratio.isascii() or not ratio.isdecimal()
                or (len(ratio) > 1 and ratio.startswith("0"))):
            raise HoldoutObservationError(
                "ycsb_rratio must be canonical unsigned decimal"
            )
        if int(ratio, 10) > _UINT64_MAX:
            raise HoldoutObservationError("ycsb_rratio exceeds uint64 range")
    return effective


def classify_minimal_holdout_signature(
    gflags: Sequence[str],
) -> MinimalHoldoutSignature | None:
    """Classify the effective direct read ratio against the protected set."""

    effective = normalized_direct_gflags(gflags)
    return _NEUTRAL_BY_RATIO.get(effective.get("ycsb_rratio"))


def _identity_capability_functions():
    # Keep the strong-reference registry in a closure: importing a private
    # module name cannot expose a seal or mutable registry that forges identity.
    issued: dict[int, _IssuedAdmissionState] = {}
    receipts: dict[int, _DurableAttemptConsumptionReceipt] = {}
    lock = threading.RLock()

    def new_receipt(
        *, attempt_id: str, permitted_run_once_calls: int,
    ) -> _DurableAttemptConsumptionReceipt:
        """Register Unit B's private post-durable-consumption handoff.

        This private Python hook is a supported-layer boundary, not a sandbox:
        code allowed to import private names can call it without doing I/O.
        """
        if type(attempt_id) is not str or not attempt_id:
            raise HoldoutObservationError("attempt_id must be a nonempty exact str")
        if (type(permitted_run_once_calls) is not int
                or permitted_run_once_calls <= 0):
            raise HoldoutObservationError(
                "permitted_run_once_calls must be a positive exact int"
            )
        receipt = _DurableAttemptConsumptionReceipt(
            attempt_id=attempt_id,
            permitted_run_once_calls=permitted_run_once_calls,
        )
        with lock:
            receipts[id(receipt)] = receipt
        return receipt

    def issue_from_receipt(
        *,
        receipt: _DurableAttemptConsumptionReceipt,
        verified_freeze_document: Mapping[str, object],
        freeze_holdout_key: str,
        _neutral_holdouts: Mapping[str, Mapping[str, object]] | None = None,
    ) -> HoldoutObservationAdmission:
        """Consume one private receipt and issue its attempt-bound token."""
        signatures = _protected_signatures_from_verified_freeze_core(
            verified_freeze_document,
            _neutral_holdouts=_neutral_holdouts,
        )
        matches = [
            signature for signature in signatures
            if signature.freeze_holdout_key == freeze_holdout_key
        ]
        if len(matches) != 1:
            raise HoldoutObservationError(
                f"verified freeze holdout key is not protected: {freeze_holdout_key}"
            )
        with lock:
            registered_receipt = receipts.pop(id(receipt), None)
            if registered_receipt is None or registered_receipt is not receipt:
                raise HoldoutObservationError(
                    "durable attempt consumption receipt was not issued or was reused"
                )
            signature = matches[0]
            token = HoldoutObservationAdmission(
                freeze_holdout_key=signature.freeze_holdout_key,
                freeze_candidate_id=signature.freeze_candidate_id,
                trial_workload_name=signature.trial_workload_name,
                ycsb_rratio=signature.ycsb_rratio,
                attempt_id=receipt.attempt_id,
                permitted_run_once_calls=receipt.permitted_run_once_calls,
            )
            issued[id(token)] = _IssuedAdmissionState(
                token=token,
                signature=signature,
                remaining_run_once_calls=receipt.permitted_run_once_calls,
            )
        return token

    def assert_issued(
        admission: object,
        *,
        expected_signature: MinimalHoldoutSignature | None = None,
    ) -> None:
        with lock:
            state = issued.get(id(admission))
        if state is None or state.token is not admission:
            raise HoldoutObservationError("holdout observation admission was not issued")
        if expected_signature is not None and state.signature != expected_signature:
            raise HoldoutObservationError(
                "holdout observation admission does not match the protected signature"
            )

    def consume_run_once(
        admission: object,
        *,
        effective_ycsb_rratio: str | None,
    ) -> None:
        with lock:
            state = issued.get(id(admission))
            if state is None or state.token is not admission:
                raise HoldoutObservationError(
                    "holdout observation admission was not issued"
                )
            if state.signature.ycsb_rratio != effective_ycsb_rratio:
                raise HoldoutObservationError(
                    "holdout observation admission does not match the protected signature"
                )
            if state.remaining_run_once_calls <= 0:
                raise HoldoutObservationError(
                    "holdout observation admission run_once allowance exhausted"
                )
            issued[id(admission)] = _IssuedAdmissionState(
                token=state.token,
                signature=state.signature,
                remaining_run_once_calls=state.remaining_run_once_calls - 1,
            )

    return new_receipt, issue_from_receipt, assert_issued, consume_run_once


(
    _new_durable_attempt_consumption_receipt,
    _issue_holdout_observation_admission_from_receipt,
    assert_issued_holdout_observation,
    _consume_holdout_observation_run_once,
) = _identity_capability_functions()
del _identity_capability_functions


def assert_holdout_observation_admitted(
    *,
    gflags: Sequence[str],
    admission: HoldoutObservationAdmission | None,
) -> None:
    """Apply the subprocess gateway gate for the effective direct flags.

    Tokenless calls use the fixed production table.  An issued token carries
    the exact verified signature used by its private campaign reservation, so
    the subprocess edge compares the executed ratio with that same signature.
    """

    effective = normalized_direct_gflags(gflags)
    ratio = effective.get("ycsb_rratio")
    if admission is None:
        signature = _NEUTRAL_BY_RATIO.get(ratio)
        if signature is not None:
            raise HoldoutObservationError(
                "holdout observation admission required for "
                f"ycsb_rratio={signature.ycsb_rratio}"
            )
        return
    _consume_holdout_observation_run_once(
        admission,
        effective_ycsb_rratio=ratio,
    )
