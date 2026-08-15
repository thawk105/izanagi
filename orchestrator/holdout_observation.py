# -*- coding: utf-8 -*-
"""Freeze-derived holdout classification and observation capabilities.

This is a neutral, stdlib-only leaf.  The campaign layer remains responsible
for verifying freeze/protocol authority and durable attempt consumption before
calling the issuer hook in this module.
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
    "issue_holdout_observation_admission",
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
    """Opaque-by-identity token; field equality never establishes issuance."""

    freeze_holdout_key: str
    freeze_candidate_id: str
    trial_workload_name: str
    ycsb_rratio: str


@dataclass(frozen=True, slots=True)
class _IssuedAdmissionState:
    token: HoldoutObservationAdmission
    signature: MinimalHoldoutSignature


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
    """Return the protected set, rejecting drift from the neutral known set.

    The caller must first establish that ``verified_freeze_document`` is the
    verified authority document.  This leaf validates the holdout projection
    and fails closed on additions, removals, or binding changes.
    """

    derived = _derive_protected_signatures(verified_freeze_document)
    if derived != _NEUTRAL_PROTECTED_SIGNATURES:
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
        if not isinstance(raw, str):
            raise HoldoutObservationError("gflags must contain strings only")
        if not raw.startswith("-") or raw == "-":
            continue
        body = raw[2:] if raw.startswith("--") else raw[1:]
        name, separator, value = body.partition("=")
        if name in _INDIRECT_GFLAGS:
            raise HoldoutObservationError(f"indirect gflags input is forbidden: {name}")
        if separator and name:
            effective[name] = value
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
    lock = threading.RLock()

    def issue(
        *,
        verified_freeze_document: Mapping[str, object],
        freeze_holdout_key: str,
    ) -> HoldoutObservationAdmission:
        signatures = protected_signatures_from_verified_freeze(
            verified_freeze_document
        )
        matches = [
            signature for signature in signatures
            if signature.freeze_holdout_key == freeze_holdout_key
        ]
        if len(matches) != 1:
            raise HoldoutObservationError(
                f"verified freeze holdout key is not protected: {freeze_holdout_key}"
            )
        signature = matches[0]
        token = HoldoutObservationAdmission(
            freeze_holdout_key=signature.freeze_holdout_key,
            freeze_candidate_id=signature.freeze_candidate_id,
            trial_workload_name=signature.trial_workload_name,
            ycsb_rratio=signature.ycsb_rratio,
        )
        state = _IssuedAdmissionState(token=token, signature=signature)
        with lock:
            issued[id(token)] = state
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

    return issue, assert_issued


(
    issue_holdout_observation_admission,
    assert_issued_holdout_observation,
) = _identity_capability_functions()
del _identity_capability_functions


def assert_holdout_observation_admitted(
    *,
    gflags: Sequence[str],
    admission: HoldoutObservationAdmission | None,
) -> None:
    """Apply the subprocess gateway gate for the effective direct flags."""

    signature = classify_minimal_holdout_signature(gflags)
    if signature is None:
        if admission is not None:
            assert_issued_holdout_observation(admission)
            raise HoldoutObservationError(
                "holdout observation admission supplied for an unprotected ratio"
            )
        return
    if admission is None:
        raise HoldoutObservationError(
            f"holdout observation admission required for ycsb_rratio={signature.ycsb_rratio}"
        )
    assert_issued_holdout_observation(
        admission,
        expected_signature=signature,
    )
