# -*- coding: utf-8 -*-
"""Evidence-derived admission metadata for campaign builds.

The sealed runtime values and exact canonical receipts in this module prevent accidental class
selection and make provenance structurally checkable.  They do **not** authenticate an issuer:
trusted orchestrator code in the same Python process can call the private factories, register an
``argparse`` action of its own, or mutate process memory.  This is misuse prevention and
provenance structuring, not a security boundary against an in-process caller.

The following boundaries are deliberately still open and receive no security credit here:
in-process issuers, shell materializers, the ABA/mixed-snapshot window between evidence capture
and compilation, and transitive provenance through older artifacts.  In particular, a receipt
proves canonical structure and internal consistency, not that a human or generator really acted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .pin import CURRENT_PIN
from . import source_digest
from .model import Genome
from .source_digest import (
    SOURCE_EVIDENCE_SCHEMA,
    SOURCE_EVIDENCE_SCHEMA_V2,
    STOCK,
    SourceEvidence,
    TriggerGateSourceError,
    inspect_trigger_gate_source,
)
from .trigger_gate_language import TRIGGER_GATE_LANGUAGE


ADMISSION_SCHEMA = "build-admission/v1"
ADMISSION_SCHEMA_V2 = "build-admission/v2"
POLICY_SCHEMA = "build-admission-policy/v1"
GENERATOR_RECEIPT_SCHEMA = "generator-receipt/v1"
REVIEW_RECEIPT_SCHEMA = "source-review/v1"
TRIGGER_GATE_RECEIPT_SCHEMA = "trigger-gate-receipt/v1"
_AUTHORITY_KIND = "cli-opt-in"
_SEAL = object()
_ISSUED_AUTHORITY_NONCES: set[str] = set()
_CLAIMED_AUTHORITY_NONCES: set[str] = set()


class BuildAdmissionError(RuntimeError):
    """Source evidence did not support exactly one admitted build class."""


class TriggerGateAdmissionError(BuildAdmissionError):
    """Closed trigger-gate admission rejection with no untrusted source detail."""


class BuildProvenance(str, Enum):
    """Classes derived by :func:`derive_build_admission`, never selected by callers."""

    STOCK_BASELINE = "stock-baseline"
    CODER_AUTHORED = "coder-authored"
    MACHINE_GENERATED = "machine-generated"
    HUMAN_REVIEWED = "human-reviewed"

    # Source-compatible names for code migrating from T-316.  Construction remains sealed, so
    # these aliases do not retain the old caller-declaration acceptance path.
    STOCK_OR_PINNED = STOCK_BASELINE
    CODER_DERIVED = CODER_AUTHORED
    MACHINE_SWEEP = MACHINE_GENERATED


class GeneratorId(str, Enum):
    """Closed registry of production source generators."""

    BACKOFF_OVERTHROTTLE = "backoff-overthrottle"
    BACKOFF_PROFILE = "backoff-profile"
    BACKOFF_REPRO = "backoff-repro"
    BACKOFF_SWEEP = "backoff-sweep"
    S1_EXTIME_CALIBRATION = "s1-extime-calibration"
    S6_SORT_SWEEP = "s6-sort-sweep"
    S8A_TRIGGER_SWEEP = "s8a-trigger-sweep"


class ReviewId(str, Enum):
    """Closed registry of source-bound human-review checkpoints."""

    S1_KNOWN_AXES = "s1-known-axes"
    S8B_FLOOR = "s8b-floor"
    S8B_ORACLE = "s8b-oracle"


def _canonical_json(value: Mapping[str, object]) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("receipt は canonical JSON に変換可能である必要がある") from exc


def _sha256_map(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _require_exact_keys(value: object, expected: frozenset[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        got = sorted(repr(key) for key in value) if isinstance(value, Mapping) else type(value).__name__
        raise BuildAdmissionError(f"{label} の key 集合が不正: expected={sorted(expected)} got={got}")
    if any(type(key) is not str for key in value):
        raise BuildAdmissionError(f"{label} の key は exact str が必要")
    return value


def _source_map(source: SourceEvidence) -> dict[str, object]:
    if type(source) is not SourceEvidence:
        raise BuildAdmissionError("source は resolve_evidence() 由来の exact SourceEvidence が必要")
    try:
        return source.as_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("SourceEvidence の canonical body が不正") from exc


@dataclass(frozen=True, slots=True, init=False)
class CoderBuildAuthority:
    """Opaque, process-local token issued only by the private argparse action."""

    _nonce: str

    def __init__(self, nonce: str, *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("CoderBuildAuthority は parser action だけが発行できる")
        object.__setattr__(self, "_nonce", nonce)


@dataclass(frozen=True, slots=True, init=False)
class BuildAdmissionPolicy:
    """Stable, nonce-free admission policy identity."""

    _preimage_json: str
    sha256: str

    def __init__(self, preimage: Mapping[str, object], *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("BuildAdmissionPolicy は build_run_context() が発行する")
        rendered = _canonical_json(preimage)
        object.__setattr__(self, "_preimage_json", rendered)
        object.__setattr__(self, "sha256", hashlib.sha256(rendered.encode("utf-8")).hexdigest())

    def as_preimage(self) -> Mapping[str, object]:
        return json.loads(self._preimage_json)


@dataclass(frozen=True, slots=True, init=False)
class BuildRunContext:
    """One process-local run context for generator and optional CLI authority receipts."""

    _policy: BuildAdmissionPolicy
    _generator_id: GeneratorId
    _context_nonce: str
    _authority_nonce: str | None

    def __init__(
        self,
        policy: BuildAdmissionPolicy,
        generator_id: GeneratorId,
        context_nonce: str,
        authority_nonce: str | None,
        *,
        _seal: object = None,
    ) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("BuildRunContext は build_run_context() が発行する")
        object.__setattr__(self, "_policy", policy)
        object.__setattr__(self, "_generator_id", generator_id)
        object.__setattr__(self, "_context_nonce", context_nonce)
        object.__setattr__(self, "_authority_nonce", authority_nonce)

    @property
    def policy(self) -> BuildAdmissionPolicy:
        return self._policy

    @property
    def generator_id(self) -> GeneratorId:
        return self._generator_id


@dataclass(frozen=True, slots=True, init=False)
class GeneratorReceipt:
    """Runtime generator receipt with a full canonical persistent body."""

    _body_json: str
    _context_nonce: str

    def __init__(self, body: Mapping[str, object], context_nonce: str, *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("GeneratorReceipt は attest_generator_output() が発行する")
        object.__setattr__(self, "_body_json", _canonical_json(body))
        object.__setattr__(self, "_context_nonce", context_nonce)

    def as_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


@dataclass(frozen=True, slots=True, init=False)
class ReviewReceipt:
    """Validated source-bound review receipt; authenticity is outside this process boundary."""

    _body_json: str

    def __init__(self, body: Mapping[str, object], *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("ReviewReceipt は verify_review_receipt() が発行する")
        object.__setattr__(self, "_body_json", _canonical_json(body))

    def as_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


@dataclass(frozen=True, slots=True, init=False)
class TriggerGateReceipt:
    """Process-sealed identity binding for one actual rendered trigger hole."""

    _body_json: str
    _runtime_seal: object

    def __init__(self, body: Mapping[str, object], *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError(
                "TriggerGateReceipt は issue_trigger_gate_receipt() だけが発行できる"
            )
        object.__setattr__(self, "_body_json", _canonical_json(body))
        object.__setattr__(self, "_runtime_seal", _SEAL)

    @property
    def receipt_sha256(self) -> str:
        return str(json.loads(self._body_json)["receipt_sha256"])

    def as_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


@dataclass(frozen=True, slots=True, init=False)
class BuildAdmission:
    """Sealed admission whose persistent projection contains every receipt body."""

    _provenance: BuildProvenance
    _body_json: str

    def __init__(
        self,
        provenance: BuildProvenance,
        body: Mapping[str, object],
        *,
        _seal: object = None,
    ) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("BuildAdmission は derive_build_admission() だけが発行する")
        object.__setattr__(self, "_provenance", provenance)
        object.__setattr__(self, "_body_json", _canonical_json(body))

    @property
    def provenance(self) -> BuildProvenance:
        return self._provenance

    @property
    def provenance_class(self) -> BuildProvenance:
        """Compatibility spelling for callers migrating from T-316."""

        return self._provenance

    @property
    def receipt_sha256(self) -> str:
        return str(json.loads(self._body_json)["receipt_sha256"])

    def as_cache_identity(self) -> Mapping[str, object]:
        return json.loads(self._body_json)

    def as_wal_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


class _CoderAuthorityAction(argparse.Action):
    """Private action: the only supported issuer of a coder authority token."""

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        nonce = secrets.token_hex(32)
        _ISSUED_AUTHORITY_NONCES.add(nonce)
        setattr(namespace, self.dest, CoderBuildAuthority(nonce, _seal=_SEAL))


def add_coder_build_authority_argument(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "coder_build_authority",
) -> None:
    """Add ``--allow-coder-derived-build`` with an opaque process-local value."""

    if type(parser) is not argparse.ArgumentParser:
        raise TypeError("parser は argparse.ArgumentParser の exact instance が必要")
    parser.add_argument(
        "--allow-coder-derived-build",
        dest=dest,
        action=_CoderAuthorityAction,
        nargs=0,
        default=None,
        help="permit coder-derived source builds for this invocation",
    )


def _new_policy() -> BuildAdmissionPolicy:
    preimage: dict[str, object] = {
        "schema": POLICY_SCHEMA,
        "repo_stock_pin": CURRENT_PIN,
        "coder_authority": _AUTHORITY_KIND,
        "generator_registry": sorted(member.value for member in GeneratorId),
        "review_registry": sorted(member.value for member in ReviewId),
    }
    return BuildAdmissionPolicy(preimage, _seal=_SEAL)


def build_run_context(
    *,
    generator_id: GeneratorId,
    coder_authority: CoderBuildAuthority | None = None,
) -> BuildRunContext:
    """Create one run context, consuming an optional parser-issued authority exactly once."""

    if type(generator_id) is not GeneratorId:
        raise BuildAdmissionError("generator_id は registered GeneratorId の exact member が必要")
    authority_nonce = None
    if coder_authority is not None:
        if type(coder_authority) is not CoderBuildAuthority:
            raise BuildAdmissionError("coder_authority は parser 発行 token の exact type が必要")
        authority_nonce = coder_authority._nonce
        if authority_nonce not in _ISSUED_AUTHORITY_NONCES:
            raise BuildAdmissionError("coder_authority はこの process の parser が発行していない")
        if authority_nonce in _CLAIMED_AUTHORITY_NONCES:
            raise BuildAdmissionError("coder_authority は別 run context で既に使用済み")
        _CLAIMED_AUTHORITY_NONCES.add(authority_nonce)
    return BuildRunContext(
        _new_policy(), generator_id, secrets.token_hex(32), authority_nonce, _seal=_SEAL
    )


def attest_generator_output(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_input_sha256: str,
) -> GeneratorReceipt:
    """Bind the context's registered generator and input digest to exact source evidence."""

    if type(context) is not BuildRunContext:
        raise BuildAdmissionError("context は build_run_context() 由来の exact value が必要")
    source_body = _source_map(source)
    if not _is_sha256(generator_input_sha256):
        raise BuildAdmissionError("generator_input_sha256 は lowercase SHA-256 が必要")
    body: dict[str, object] = {
        "schema": GENERATOR_RECEIPT_SCHEMA,
        "generator_id": context.generator_id.value,
        "source": source_body,
        "generator_input_sha256": generator_input_sha256,
    }
    body["receipt_sha256"] = _sha256_map(body)
    return GeneratorReceipt(body, context._context_nonce, _seal=_SEAL)


_GENERATOR_KEYS = frozenset({
    "schema", "generator_id", "source", "generator_input_sha256", "receipt_sha256",
})
_REVIEW_KEYS = frozenset({
    "schema", "review_id", "source", "input_sha256", "receipt_sha256",
})
_TRIGGER_GATE_RECEIPT_KEYS = frozenset({
    "schema", "trigger_gate_language", "implementation_sha256", "source",
    "receipt_sha256",
})
_ADMISSION_KEYS_V1 = frozenset({
    "schema", "class", "policy_sha256", "source", "generator_id", "review_id",
    "input_sha256", "generator_receipt", "review_receipt", "authority_kind",
    "receipt_sha256",
})
_ADMISSION_KEYS_V2 = _ADMISSION_KEYS_V1 | frozenset({"trigger_gate_receipt"})


def _validate_trigger_gate_receipt_body(
    value: object,
    *,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]:
    body = _require_exact_keys(
        value, _TRIGGER_GATE_RECEIPT_KEYS, "trigger gate receipt"
    )
    if (body["schema"] != TRIGGER_GATE_RECEIPT_SCHEMA
            or body["trigger_gate_language"] != TRIGGER_GATE_LANGUAGE):
        raise BuildAdmissionError("trigger gate receipt schema/language が不一致")
    try:
        source = SourceEvidence.from_receipt(body["source"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("trigger gate receipt source evidence が不正") from exc
    if source.schema_version != SOURCE_EVIDENCE_SCHEMA_V2:
        raise BuildAdmissionError("trigger gate receipt は SourceEvidence v2 が必要")
    if (body["implementation_sha256"]
            != source.trigger_gate_implementation_sha256):
        raise BuildAdmissionError("trigger gate receipt implementation digest が不一致")
    if expected_source is not None and body["source"] != _source_map(expected_source):
        raise BuildAdmissionError("trigger gate receipt source evidence/root が不一致")
    if not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("trigger gate receipt outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("trigger gate receipt outer SHA が canonical body と不一致")
    return body


def issue_trigger_gate_receipt(
    source: SourceEvidence,
    *,
    genome: Genome,
    cxx: str = "g++-13",
) -> TriggerGateReceipt:
    """Re-resolve all source evidence before sealing one trigger identity receipt."""

    source_body = _source_map(source)
    if source.schema_version != SOURCE_EVIDENCE_SCHEMA_V2:
        raise TriggerGateAdmissionError(
            "trigger gate receipt 発行には SourceEvidence v2 が必要"
        )
    if type(genome) is not Genome:
        raise TriggerGateAdmissionError("trigger gate receipt 発行には exact Genome が必要")
    try:
        fresh = source_digest.resolve_evidence(
            genome,
            source.ccbench_commit,
            ccbench_dir=source.source_root,
            cxx=cxx,
        )
    except (RuntimeError, TriggerGateSourceError) as exc:
        raise TriggerGateAdmissionError("trigger gate actual source を受理できない") from exc
    if fresh != source:
        raise TriggerGateAdmissionError(
            "trigger gate current SourceEvidence が発行入力と不一致"
        )
    try:
        inspected = inspect_trigger_gate_source(source.source_root, required=True)
    except TriggerGateSourceError as exc:
        raise TriggerGateAdmissionError("trigger gate actual source を受理できない") from exc
    if inspected is None:
        raise TriggerGateAdmissionError("trigger gate actual source を受理できない")
    _implementation, implementation_sha256 = inspected
    if (source.trigger_gate_language != TRIGGER_GATE_LANGUAGE
            or source.trigger_gate_implementation_sha256 != implementation_sha256):
        raise TriggerGateAdmissionError(
            "trigger gate actual source と SourceEvidence が不一致"
        )
    body: dict[str, object] = {
        "schema": TRIGGER_GATE_RECEIPT_SCHEMA,
        "trigger_gate_language": TRIGGER_GATE_LANGUAGE,
        "implementation_sha256": implementation_sha256,
        "source": source_body,
    }
    body["receipt_sha256"] = _sha256_map(body)
    return TriggerGateReceipt(body, _seal=_SEAL)


def validate_trigger_gate_receipt(
    value: object,
    *,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]:
    """Validate a persistent trigger receipt body without granting runtime issuance."""

    checked = _validate_trigger_gate_receipt_body(
        value, expected_source=expected_source
    )
    return json.loads(_canonical_json(checked))


def require_trigger_gate_receipt(
    value: object,
    *,
    expected_source: SourceEvidence,
) -> TriggerGateReceipt:
    """Require exact runtime type/seal and exact SourceEvidence binding."""

    if type(value) is not TriggerGateReceipt:
        raise BuildAdmissionError(
            "trigger_gate_receipt は issue_trigger_gate_receipt() 由来の exact value が必要"
        )
    if getattr(value, "_runtime_seal", None) is not _SEAL:
        raise BuildAdmissionError("TriggerGateReceipt runtime seal が不正")
    try:
        body = value.as_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("TriggerGateReceipt sealed body が不正") from exc
    _validate_trigger_gate_receipt_body(body, expected_source=expected_source)
    return value


def _validate_generator_body(value: object, source_body: Mapping[str, object]) -> Mapping[str, object]:
    body = _require_exact_keys(value, _GENERATOR_KEYS, "generator receipt")
    if body["schema"] != GENERATOR_RECEIPT_SCHEMA:
        raise BuildAdmissionError("generator receipt schema が不一致")
    try:
        GeneratorId(body["generator_id"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("generator receipt の generator_id が未登録") from exc
    if body["source"] != source_body:
        raise BuildAdmissionError("generator receipt は対象 source evidence に束縛されていない")
    if not _is_sha256(body["generator_input_sha256"]):
        raise BuildAdmissionError("generator receipt の input digest が不正")
    if not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("generator receipt の outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("generator receipt の outer SHA が canonical body と不一致")
    return body


def verify_review_receipt(
    review_id: ReviewId,
    source: SourceEvidence,
    *,
    receipt: Mapping[str, object],
) -> ReviewReceipt:
    """Validate an exact, source-bound review body and return its sealed runtime projection.

    This checks structure and equality only.  It does not authenticate the human reviewer.
    """

    if type(review_id) is not ReviewId:
        raise BuildAdmissionError("review_id は registered ReviewId の exact member が必要")
    source_body = _source_map(source)
    body = _require_exact_keys(receipt, _REVIEW_KEYS, "review receipt")
    if body["schema"] != REVIEW_RECEIPT_SCHEMA or body["review_id"] != review_id.value:
        raise BuildAdmissionError("review receipt の schema/review_id が不一致")
    if body["source"] != source_body:
        raise BuildAdmissionError("review receipt は対象 source evidence に束縛されていない")
    if not _is_sha256(body["input_sha256"]) or not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("review receipt の input/outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("review receipt の outer SHA が canonical body と不一致")
    return ReviewReceipt(body, _seal=_SEAL)


def _validated_review_body(value: ReviewReceipt, source_body: Mapping[str, object]) -> Mapping[str, object]:
    if type(value) is not ReviewReceipt:
        raise BuildAdmissionError("review_receipt は verify_review_receipt() 由来の exact value が必要")
    try:
        body = value.as_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("review receipt の sealed body が不正") from exc
    checked = _require_exact_keys(body, _REVIEW_KEYS, "review receipt")
    try:
        review_id = ReviewId(checked["review_id"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("review receipt の review_id が未登録") from exc
    # Re-run the persistent validator instead of trusting the runtime seal alone.
    verified = verify_review_receipt(review_id, _source_from_body_proxy(source_body), receipt=checked)
    return verified.as_receipt()


def _source_from_body_proxy(source_body: Mapping[str, object]) -> SourceEvidence:
    """Rehydrate an already validated source body for internal receipt revalidation."""

    return SourceEvidence.from_receipt(source_body)


def derive_build_admission(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_receipt: GeneratorReceipt | None = None,
    review_receipt: ReviewReceipt | None = None,
    trigger_gate_receipt: TriggerGateReceipt | None = None,
) -> BuildAdmission:
    """Derive one class in the ruled order; reject missing or ambiguous evidence."""

    if type(context) is not BuildRunContext:
        raise BuildAdmissionError("context は build_run_context() 由来の exact value が必要")
    source_body = _source_map(source)
    trigger_gate_body = None
    if source.schema_version == SOURCE_EVIDENCE_SCHEMA_V2:
        trigger_gate_receipt = require_trigger_gate_receipt(
            trigger_gate_receipt,
            expected_source=source,
        )
        trigger_gate_body = trigger_gate_receipt.as_receipt()
    elif source.schema_version == SOURCE_EVIDENCE_SCHEMA:
        if trigger_gate_receipt is not None:
            raise BuildAdmissionError("SourceEvidence v1 へ trigger gate receipt は提示できない")
    else:
        raise BuildAdmissionError("SourceEvidence schema が admission 非対応")
    if generator_receipt is not None and review_receipt is not None:
        raise BuildAdmissionError("generator と review receipt の同時提示は曖昧なので拒否")

    generator_body = review_body = None
    generator_id = review_id = input_sha256 = authority_kind = None
    if source.src_token == STOCK and source.tracked_clean is True \
            and source.ccbench_commit == CURRENT_PIN:
        provenance = BuildProvenance.STOCK_BASELINE
    elif review_receipt is not None:
        review_body = _validated_review_body(review_receipt, source_body)
        review_id = review_body["review_id"]
        input_sha256 = review_body["input_sha256"]
        provenance = BuildProvenance.HUMAN_REVIEWED
    elif generator_receipt is not None:
        if type(generator_receipt) is not GeneratorReceipt:
            raise BuildAdmissionError(
                "generator_receipt は attest_generator_output() 由来の exact value が必要"
            )
        if generator_receipt._context_nonce != context._context_nonce:
            raise BuildAdmissionError("generator receipt は別 run context 由来")
        generator_body = _validate_generator_body(generator_receipt.as_receipt(), source_body)
        if generator_body["generator_id"] != context.generator_id.value:
            raise BuildAdmissionError("generator receipt の id が run context と不一致")
        generator_id = generator_body["generator_id"]
        input_sha256 = generator_body["generator_input_sha256"]
        provenance = BuildProvenance.MACHINE_GENERATED
    elif context._authority_nonce is not None:
        if context._authority_nonce not in _CLAIMED_AUTHORITY_NONCES:
            raise BuildAdmissionError("coder authority は同一 run context で有効でない")
        authority_kind = _AUTHORITY_KIND
        provenance = BuildProvenance.CODER_AUTHORED
    else:
        raise BuildAdmissionError("source evidence は stock/review/generator/coder のどれも支持しない")

    body: dict[str, object] = {
        "schema": (
            ADMISSION_SCHEMA_V2
            if source.schema_version == SOURCE_EVIDENCE_SCHEMA_V2
            else ADMISSION_SCHEMA
        ),
        "class": provenance.value,
        "policy_sha256": context.policy.sha256,
        "source": source_body,
        "generator_id": generator_id,
        "review_id": review_id,
        "input_sha256": input_sha256,
        "generator_receipt": generator_body,
        "review_receipt": review_body,
        "authority_kind": authority_kind,
    }
    if trigger_gate_body is not None:
        body["trigger_gate_receipt"] = trigger_gate_body
    body["receipt_sha256"] = _sha256_map(body)
    return BuildAdmission(provenance, body, _seal=_SEAL)


def _validate_admission_body(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence | None,
) -> Mapping[str, object]:
    if type(expected_policy) is not BuildAdmissionPolicy:
        raise BuildAdmissionError("expected_policy は BuildRunContext.policy の exact value が必要")
    if not isinstance(value, Mapping):
        raise BuildAdmissionError("build admission receipt は object が必要")
    schema = value.get("schema")
    keys = _ADMISSION_KEYS_V2 if schema == ADMISSION_SCHEMA_V2 else _ADMISSION_KEYS_V1
    body = _require_exact_keys(value, keys, "build admission receipt")
    if schema not in {ADMISSION_SCHEMA, ADMISSION_SCHEMA_V2} \
            or body["policy_sha256"] != expected_policy.sha256:
        raise BuildAdmissionError("build admission receipt の schema/policy が不一致")
    source_body = body["source"]
    try:
        source = SourceEvidence.from_receipt(source_body)
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("build admission receipt の source evidence が不正") from exc
    if expected_source is not None and source_body != _source_map(expected_source):
        raise BuildAdmissionError("build admission receipt の source evidence/root が不一致")
    if schema == ADMISSION_SCHEMA_V2:
        if source.schema_version != SOURCE_EVIDENCE_SCHEMA_V2:
            raise BuildAdmissionError("build admission v2 は SourceEvidence v2 が必要")
        _validate_trigger_gate_receipt_body(
            body["trigger_gate_receipt"], expected_source=source
        )
    elif source.schema_version != SOURCE_EVIDENCE_SCHEMA:
        raise BuildAdmissionError("build admission v1 は SourceEvidence v1 が必要")
    try:
        provenance = BuildProvenance(body["class"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("build admission receipt の class が不正") from exc
    if not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("build admission receipt の outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("build admission receipt の outer SHA が canonical body と不一致")

    if provenance is BuildProvenance.STOCK_BASELINE:
        if not (source.src_token == STOCK and source.tracked_clean is True
                and source.ccbench_commit == CURRENT_PIN):
            raise BuildAdmissionError("stock class を repo pin/clean/source evidence が支持しない")
        expected_null = ("generator_id", "review_id", "input_sha256",
                         "generator_receipt", "review_receipt", "authority_kind")
        if any(body[key] is not None for key in expected_null):
            raise BuildAdmissionError("stock class に他 class の evidence が混在")
    elif provenance is BuildProvenance.HUMAN_REVIEWED:
        checked = _require_exact_keys(body["review_receipt"], _REVIEW_KEYS, "review receipt")
        try:
            review_id = ReviewId(checked["review_id"])
        except (TypeError, ValueError) as exc:
            raise BuildAdmissionError("review receipt の review_id が未登録") from exc
        verify_review_receipt(review_id, source, receipt=checked)
        if (body["review_id"] != review_id.value or body["input_sha256"] != checked["input_sha256"]
                or body["generator_id"] is not None or body["generator_receipt"] is not None
                or body["authority_kind"] is not None):
            raise BuildAdmissionError("human-reviewed class の canonical body が不整合")
    elif provenance is BuildProvenance.MACHINE_GENERATED:
        checked = _validate_generator_body(body["generator_receipt"], source_body)
        if (body["generator_id"] != checked["generator_id"]
                or body["input_sha256"] != checked["generator_input_sha256"]
                or body["review_id"] is not None or body["review_receipt"] is not None
                or body["authority_kind"] is not None):
            raise BuildAdmissionError("machine-generated class の canonical body が不整合")
    else:
        if body["authority_kind"] != _AUTHORITY_KIND:
            raise BuildAdmissionError("coder-authored class は CLI authority kind が必要")
        expected_null = ("generator_id", "review_id", "input_sha256",
                         "generator_receipt", "review_receipt")
        if any(body[key] is not None for key in expected_null):
            raise BuildAdmissionError("coder-authored class に他 class の evidence が混在")
    return body


def require_build_admission(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence,
) -> BuildAdmission:
    """Revalidate a sealed runtime admission against the current policy and source/root."""

    if type(value) is not BuildAdmission:
        raise BuildAdmissionError("admission は derive_build_admission() 由来の exact value が必要")
    try:
        body = value.as_wal_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("BuildAdmission の sealed body が不正") from exc
    checked = _validate_admission_body(
        body, expected_policy=expected_policy, expected_source=expected_source
    )
    if value.provenance.value != checked["class"]:
        raise BuildAdmissionError("runtime provenance と canonical receipt class が不一致")
    return value


def validate_build_admission_receipt(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]:
    """Validate a persistent exact-key receipt and return a detached canonical mapping."""

    checked = _validate_admission_body(
        value, expected_policy=expected_policy, expected_source=expected_source
    )
    return json.loads(_canonical_json(checked))


def legacy_trigger_admission_projection(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
) -> tuple[Mapping[str, object], SourceEvidence]:
    """Derive the historical v1 cache lookup body without issuing a runtime admission."""

    checked = _validate_admission_body(
        value, expected_policy=expected_policy, expected_source=None
    )
    if checked["schema"] != ADMISSION_SCHEMA_V2:
        raise BuildAdmissionError("legacy trigger projection は build admission v2 が必要")
    source_v2 = SourceEvidence.from_receipt(checked["source"])
    source_body = dict(source_v2.as_receipt())
    source_body["schema"] = SOURCE_EVIDENCE_SCHEMA
    source_body.pop("trigger_gate_language", None)
    source_body.pop("trigger_gate_implementation_sha256", None)
    source_v1 = SourceEvidence.from_receipt(source_body)

    projected = dict(checked)
    projected["schema"] = ADMISSION_SCHEMA
    projected["source"] = source_body
    projected.pop("trigger_gate_receipt", None)
    if type(projected.get("generator_receipt")) is dict:
        nested = dict(projected["generator_receipt"])
        nested["source"] = source_body
        nested.pop("receipt_sha256", None)
        nested["receipt_sha256"] = _sha256_map(nested)
        projected["generator_receipt"] = nested
    if type(projected.get("review_receipt")) is dict:
        nested = dict(projected["review_receipt"])
        nested["source"] = source_body
        nested.pop("receipt_sha256", None)
        nested["receipt_sha256"] = _sha256_map(nested)
        projected["review_receipt"] = nested
    projected.pop("receipt_sha256", None)
    projected["receipt_sha256"] = _sha256_map(projected)
    validated = _validate_admission_body(
        projected,
        expected_policy=expected_policy,
        expected_source=source_v1,
    )
    return json.loads(_canonical_json(validated)), source_v1
