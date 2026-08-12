"""Issuer-bound ``OriginBindingCapability/v1`` launch admission.

Capability issuance is prospective: it binds the authority, source closure,
registered trial, prepared campaign, and expected execution contracts.  It is
not permission to reserve ledger work until the physical-site client has also
checked the actual environment, WAL verifier configuration, and trigger
binding.

In particular, a ledger ``terminal_status == "certifiable"`` only describes
the ledger's formal terminal state.  It is distinct from launch-admission
``certifying``, which remains ``False`` here and is the authority for any later
certified-selection promotion.

The process-local seals are only a misuse guard.  At the final issuance
boundary every field in the sealed intermediate values is rederived from the
registry, raw authority bytes, raw source-closure bytes, and provisioning
receipt.  This is required because :func:`dataclasses.replace` preserves a
dataclass seal.
"""
from __future__ import annotations

import dataclasses
import hashlib
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

from . import ident, trial_registry
from .model import CampaignConfig
from .reflux_origin_artifacts import ArtifactError, strict_json_loads
from .reflux_origin_ledger import (
    _manifest_from_object,
    derive_cell_key,
    derive_origin_id,
)
from .reflux_source_closure import (
    ValidatedSourceClosure,
    assert_issued_validated_source_closure,
)
from .s8b_descriptor import canonical_descriptor_bytes


__all__ = [
    "AuthorityWorkload",
    "LaunchAdmissionRederivation",
    "OriginBindingCapability",
    "OriginBindingError",
    "PreparedOriginIdentity",
    "assert_issued_launch_admission_rederivation",
    "assert_issued_origin_binding_capability",
    "assert_issued_prepared_origin_identity",
    "assert_origin_binding_capability_record",
    "issue_origin_binding_capability",
    "origin_binding_capability_record",
    "prepare_origin_identity",
    "rederive_launch_admission",
]


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_OID_RE = re.compile(r"[0-9a-f]{40}\Z")
_LAUNCH_REDERIVATION_SEAL = object()
_PREPARED_ORIGIN_SEAL = object()
_ISSUED_CAPABILITY_FIELDS: dict[object, tuple[object, ...]] = {}
_WIRE_ISSUER_SEAL = "launch-admission-gate/v1"

_AUTHORITY_KEYS = frozenset({"authority_schema", "origins"})
_AUTHORITY_ENTRY_KEYS = frozenset({"cell_key", "manifest", "origin_id"})
_CLOSURE_KEYS = frozenset({
    "schema_version",
    "captured_commit_oid",
    "authority_series_id",
    "origin_id",
    "cell_key",
    "referents",
})
_REFERENT_KEYS = frozenset({
    "authority.workload.descriptor_sha256",
    "axis_semantics_sha256",
    "verifier_policy_sha256",
    "environment_contract_sha256",
})
_RECEIPT_KEYS = frozenset({
    "authority_blob_sha256", "source_closure_sha256", "origin_id", "cell_key",
})
_CAPABILITY_RECORD_KEYS = frozenset({
    "authority_blob_sha256",
    "source_closure_sha256",
    "origin_id",
    "cell_key",
    "authority_workload",
    "axis_semantics_sha256",
    "verifier_policy_sha256",
    "environment_contract_sha256",
    "campaign_id",
    "trial_workload",
    "measurement_head",
    "store_scope",
    "issuer_seal",
})
_WORKLOAD_KEYS = frozenset({"descriptor_sha256", "records", "threads"})


class OriginBindingError(ValueError):
    """The requested capability is not derivable without weakening a gate."""


def _reject(label: str, message: str) -> None:
    raise OriginBindingError(f"[{label}] {message}")


def _exact_mapping(value: object, keys: frozenset[str], *, label: str) -> Mapping:
    if type(value) is not dict or frozenset(value) != keys:
        _reject(label, "exact key set mismatch")
    return value


def _sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _reject(label, "expected lowercase SHA-256")
    return value


def _token(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        _reject(label, "expected non-empty string")
    return value


def _positive_int(value: object, *, label: str) -> int:
    if type(value) is not int or value < 1:
        _reject(label, "expected positive integer")
    return value


@dataclasses.dataclass(frozen=True, slots=True)
class AuthorityWorkload:
    descriptor_sha256: str
    records: int
    threads: int


@dataclasses.dataclass(frozen=True, slots=True)
class LaunchAdmissionRederivation:
    """Registry-rederived admission snapshot; its seal is not final authority."""

    admission: trial_registry.TrialLaunchAdmission
    mode: str
    certifying: bool
    reason_code: str
    trial_id: str
    workloads: tuple[str, ...]
    binding: trial_registry.TrialBinding | None
    activation_report_digest_sha256: str | None
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class PreparedOriginIdentity:
    """Identity projected from raw authority, closure, and approval receipt."""

    authority_blob_sha256: str
    source_closure_sha256: str
    origin_id: str
    cell_key: str
    authority_workload: AuthorityWorkload
    axis_semantics_sha256: str
    verifier_policy_sha256: str
    environment_contract_sha256: str
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class OriginBindingCapability:
    """Exact prospective launch-to-origin binding; never a certifying grant."""

    authority_blob_sha256: str
    source_closure_sha256: str
    origin_id: str
    cell_key: str
    authority_workload: AuthorityWorkload
    axis_semantics_sha256: str
    verifier_policy_sha256: str
    environment_contract_sha256: str
    campaign_id: str
    trial_workload: str
    measurement_head: str
    store_scope: Literal["production", "fixture"]
    _seal: object = dataclasses.field(repr=False, compare=False)


def _capability_fields(value: OriginBindingCapability) -> tuple[object, ...]:
    return tuple(
        getattr(value, field.name)
        for field in dataclasses.fields(OriginBindingCapability)
        if field.name != "_seal"
    )


def rederive_launch_admission(
    admission: trial_registry.TrialLaunchAdmission,
    *,
    effective_preregistration,
    manifest_path: Path | None,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    repository_root: Path,
    registry_path: Path,
) -> LaunchAdmissionRederivation:
    """Run both public registry assertions and seal their complete projection."""

    try:
        trial_registry.assert_issued_trial_launch_admission(admission)
        trial_registry.assert_rederived_launch_admission(
            admission,
            effective_preregistration=effective_preregistration,
            manifest_path=manifest_path,
            trial_id=trial_id,
            workloads=workloads,
            allow_unregistered_exploratory=allow_unregistered_exploratory,
            repository_root=repository_root,
            registry_path=registry_path,
        )
    except trial_registry.TrialRegistryError as exc:
        raise OriginBindingError(f"[launch-admission] {exc}") from exc
    return LaunchAdmissionRederivation(
        admission=admission,
        mode=admission.mode,
        certifying=admission.certifying,
        reason_code=admission.reason_code,
        trial_id=admission.trial_id,
        workloads=tuple(admission.workloads),
        binding=admission.binding,
        activation_report_digest_sha256=admission.activation_report_digest_sha256,
        _seal=_LAUNCH_REDERIVATION_SEAL,
    )


def assert_issued_launch_admission_rederivation(
    value: object,
) -> LaunchAdmissionRederivation:
    if (
        type(value) is not LaunchAdmissionRederivation
        or value._seal is not _LAUNCH_REDERIVATION_SEAL
    ):
        _reject("issued-launch", "rederivation was not issued by this module")
    admission = value.admission
    if type(admission) is not trial_registry.TrialLaunchAdmission:
        _reject("issued-launch", "admission type changed")
    expected = (
        admission.mode,
        admission.certifying,
        admission.reason_code,
        admission.trial_id,
        tuple(admission.workloads),
        admission.binding,
        admission.activation_report_digest_sha256,
    )
    supplied = (
        value.mode,
        value.certifying,
        value.reason_code,
        value.trial_id,
        value.workloads,
        value.binding,
        value.activation_report_digest_sha256,
    )
    if supplied != expected:
        _reject("issued-launch", "sealed projection fields changed")
    return value


def _parse_authority(raw: bytes):
    if type(raw) is not bytes or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        _reject("authority", "authority bytes require exactly one trailing LF")
    try:
        document = strict_json_loads(raw[:-1])
    except ArtifactError as exc:
        raise OriginBindingError("[authority] non-canonical authority bytes") from exc
    authority = _exact_mapping(document, _AUTHORITY_KEYS, label="authority")
    if authority["authority_schema"] != "izanagi-reflux-origin-authority/v2":
        _reject("authority", "unsupported authority schema")
    origins = authority["origins"]
    if type(origins) is not list or len(origins) != 1:
        _reject("authority", "capability preparation requires exactly one origin")
    entry = _exact_mapping(origins[0], _AUTHORITY_ENTRY_KEYS, label="authority-entry")
    try:
        manifest = _manifest_from_object(entry["manifest"])
    except Exception as exc:
        raise OriginBindingError("[authority] invalid authority manifest") from exc
    origin_id = derive_origin_id(manifest)
    cell_key = derive_cell_key(manifest)
    if entry["origin_id"] != origin_id or entry["cell_key"] != cell_key:
        _reject("authority", "entry identity differs from manifest derivation")
    return manifest, origin_id, cell_key


def _parse_closure(raw: bytes) -> Mapping:
    if type(raw) is not bytes:
        _reject("source-closure", "source closure must be immutable bytes")
    try:
        document = strict_json_loads(raw)
    except ArtifactError as exc:
        raise OriginBindingError("[source-closure] non-canonical closure bytes") from exc
    closure = _exact_mapping(document, _CLOSURE_KEYS, label="source-closure")
    if closure["schema_version"] != "source-closure/v1":
        _reject("source-closure", "unsupported schema")
    referents = _exact_mapping(
        closure["referents"], _REFERENT_KEYS, label="source-closure-referents"
    )
    return closure


def _referent_digest(closure: Mapping, name: str) -> str:
    item = closure["referents"].get(name)
    if type(item) is not dict:
        _reject("source-closure-referents", f"invalid referent {name}")
    reference = item.get("preimage_ref")
    if type(reference) is not dict:
        _reject("source-closure-referents", f"missing preimage for {name}")
    return _sha256(reference.get("sha256"), label="source-closure-referents")


def prepare_origin_identity(
    *,
    authority_blob_bytes: bytes,
    source_closure_bytes: bytes,
    provisioning_receipt: Mapping[str, object],
    validated_source_closure: ValidatedSourceClosure,
) -> PreparedOriginIdentity:
    """Derive every origin field from the three primary provisioning records."""

    try:
        closure_capability = assert_issued_validated_source_closure(
            validated_source_closure
        )
    except Exception as exc:
        raise OriginBindingError(f"[validated-source-closure] {exc}") from exc
    manifest, origin_id, cell_key = _parse_authority(authority_blob_bytes)
    closure = _parse_closure(source_closure_bytes)
    authority_sha = hashlib.sha256(authority_blob_bytes).hexdigest()
    closure_sha = hashlib.sha256(source_closure_bytes).hexdigest()
    receipt = _exact_mapping(
        provisioning_receipt, _RECEIPT_KEYS, label="provisioning-receipt"
    )
    expected_receipt = {
        "authority_blob_sha256": authority_sha,
        "source_closure_sha256": closure_sha,
        "origin_id": origin_id,
        "cell_key": cell_key,
    }
    if receipt != expected_receipt:
        _reject("provisioning-receipt", "receipt differs from primary bytes")
    expected_referents = {
        "authority.workload.descriptor_sha256": manifest.workload[
            "descriptor_sha256"
        ],
        "axis_semantics_sha256": manifest.axis_semantics_sha256,
        "verifier_policy_sha256": manifest.verifier_policy_sha256,
        "environment_contract_sha256": manifest.environment_contract_sha256,
    }
    actual_referents = {
        name: _referent_digest(closure, name) for name in _REFERENT_KEYS
    }
    if actual_referents != expected_referents:
        _reject("source-closure-referents", "closure differs from authority manifest")
    if (
        closure["authority_series_id"] != manifest.authority_series_id
        or closure["origin_id"] != origin_id
        or closure["cell_key"] != cell_key
    ):
        _reject("source-closure", "closure identity differs from authority")
    if (
        closure_capability.source_closure_sha256 != closure_sha
        or closure_capability.authority_series_id != manifest.authority_series_id
        or closure_capability.origin_id != origin_id
        or closure_capability.cell_key != cell_key
        or dict(closure_capability.referent_sha256s) != actual_referents
    ):
        _reject("validated-source-closure", "issued fields differ from primary bytes")
    workload = AuthorityWorkload(
        descriptor_sha256=_sha256(
            manifest.workload["descriptor_sha256"], label="authority-workload"
        ),
        records=_positive_int(manifest.workload["records"], label="authority-workload"),
        threads=_positive_int(manifest.workload["threads"], label="authority-workload"),
    )
    return PreparedOriginIdentity(
        authority_blob_sha256=authority_sha,
        source_closure_sha256=closure_sha,
        origin_id=origin_id,
        cell_key=cell_key,
        authority_workload=workload,
        axis_semantics_sha256=manifest.axis_semantics_sha256,
        verifier_policy_sha256=manifest.verifier_policy_sha256,
        environment_contract_sha256=manifest.environment_contract_sha256,
        _seal=_PREPARED_ORIGIN_SEAL,
    )


def assert_issued_prepared_origin_identity(value: object) -> PreparedOriginIdentity:
    if (
        type(value) is not PreparedOriginIdentity
        or value._seal is not _PREPARED_ORIGIN_SEAL
    ):
        _reject("issued-origin", "origin identity was not issued by this module")
    _validate_origin_fields(value)
    return value


def _validate_origin_fields(value: PreparedOriginIdentity | OriginBindingCapability) -> None:
    for label, digest in (
        ("authority-blob", value.authority_blob_sha256),
        ("source-closure", value.source_closure_sha256),
        ("origin-id", value.origin_id),
        ("cell-key", value.cell_key),
        ("axis-semantics", value.axis_semantics_sha256),
        ("verifier-policy", value.verifier_policy_sha256),
        ("environment-contract", value.environment_contract_sha256),
    ):
        _sha256(digest, label=label)
    if type(value.authority_workload) is not AuthorityWorkload:
        _reject("authority-workload", "expected exact AuthorityWorkload")
    _sha256(
        value.authority_workload.descriptor_sha256, label="authority-workload"
    )
    _positive_int(value.authority_workload.records, label="authority-workload")
    _positive_int(value.authority_workload.threads, label="authority-workload")


def _prepared_descriptor(prepared_campaign) -> tuple[str, int, int]:
    from .p3_autonomous_workload_trial import PreparedCampaignIdentity

    if type(prepared_campaign) is not PreparedCampaignIdentity:
        _reject("prepared-campaign", "expected exact PreparedCampaignIdentity")
    if type(prepared_campaign.campaign) is not CampaignConfig:
        _reject("prepared-campaign", "campaign config type changed")
    if prepared_campaign.campaign_id != str(ident.campaign_id(prepared_campaign.campaign)):
        _reject("prepared-campaign", "campaign_id differs from campaign derivation")
    if type(prepared_campaign.descriptor) is not dict:
        _reject("prepared-descriptor", "descriptor must be an exact mapping")
    descriptor = prepared_campaign.descriptor
    digest = hashlib.sha256(canonical_descriptor_bytes(descriptor)).hexdigest()
    record = prepared_campaign.descriptor_record
    if type(record) is not dict or record.get("output_sha256") != digest:
        _reject("prepared-descriptor", "descriptor record digest mismatch")
    search_config = prepared_campaign.campaign.search_config
    if type(search_config) is not dict or search_config.get("descriptor_sha256") != digest:
        _reject("prepared-descriptor", "search config digest mismatch")
    if descriptor.get("schema_version") == "8b-v1":
        scale = descriptor.get("scale")
        if type(scale) is not dict:
            _reject("prepared-descriptor", "8b scale is absent")
        records, threads = scale.get("records"), scale.get("threads")
    elif descriptor.get("schema_version") == "izanagi-workload-descriptor/v1":
        records, threads = descriptor.get("records"), descriptor.get("threads")
    else:
        _reject("prepared-descriptor", "unsupported descriptor schema")
    return (
        digest,
        _positive_int(records, label="prepared-descriptor"),
        _positive_int(threads, label="prepared-descriptor"),
    )


def _assert_prepared_campaign_type(prepared_campaign) -> None:
    from .p3_autonomous_workload_trial import PreparedCampaignIdentity

    if type(prepared_campaign) is not PreparedCampaignIdentity:
        _reject("prepared-campaign", "expected exact PreparedCampaignIdentity")
    if type(prepared_campaign.campaign) is not CampaignConfig:
        _reject("prepared-campaign", "campaign config type changed")


def issue_origin_binding_capability(
    *,
    launch_rederivation: LaunchAdmissionRederivation,
    prepared_campaign,
    prepared_origin: PreparedOriginIdentity,
    validated_source_closure: ValidatedSourceClosure,
    authority_blob_bytes: bytes,
    source_closure_bytes: bytes,
    provisioning_receipt: Mapping[str, object],
    effective_preregistration,
    manifest_path: Path | None,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    repository_root: Path,
    registry_path: Path,
    trial_workload: str,
    expected_axis_semantics_sha256: str,
    expected_verifier_policy_sha256: str,
    expected_environment_contract_sha256: str,
    store_scope: Literal["production", "fixture"],
) -> OriginBindingCapability:
    """Apply the seven issuance decisions as one fail-closed judgment."""

    supplied_launch = assert_issued_launch_admission_rederivation(
        launch_rederivation
    )
    fresh_launch = rederive_launch_admission(
        supplied_launch.admission,
        effective_preregistration=effective_preregistration,
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=workloads,
        allow_unregistered_exploratory=allow_unregistered_exploratory,
        repository_root=repository_root,
        registry_path=registry_path,
    )
    for field in dataclasses.fields(LaunchAdmissionRederivation):
        if field.name == "_seal":
            continue
        if getattr(supplied_launch, field.name) != getattr(fresh_launch, field.name):
            _reject("launch-rederivation", f"field changed: {field.name}")

    if supplied_launch.mode != "registered-effective":
        _reject("launch-mode", "only registered-effective admission can issue")
    binding = supplied_launch.binding
    if binding is None:
        _reject("launch-binding", "registered admission has no binding")
    try:
        trial_registry.assert_issued_trial_binding(binding)
    except Exception as exc:
        raise OriginBindingError(f"[launch-binding] {exc}") from exc

    workload = _token(trial_workload, label="trial-workload")
    _assert_prepared_campaign_type(prepared_campaign)
    if prepared_campaign.campaign_id != binding.campaign_id:
        _reject("campaign-binding", "prepared and registry campaign IDs differ")
    if binding.workload != workload:
        _reject("campaign-binding", "registry and requested workloads differ")
    search_workload = prepared_campaign.campaign.search_config.get("workload")
    if search_workload is not None and search_workload != workload:
        _reject("campaign-binding", "campaign search workload differs")

    descriptor_sha, records, threads = _prepared_descriptor(prepared_campaign)
    expected_workload = AuthorityWorkload(descriptor_sha, records, threads)

    supplied_origin = assert_issued_prepared_origin_identity(prepared_origin)
    if expected_workload != supplied_origin.authority_workload:
        _reject("authority-workload", "prepared descriptor or scale differs")
    fresh_origin = prepare_origin_identity(
        authority_blob_bytes=authority_blob_bytes,
        source_closure_bytes=source_closure_bytes,
        provisioning_receipt=provisioning_receipt,
        validated_source_closure=validated_source_closure,
    )
    for field in dataclasses.fields(PreparedOriginIdentity):
        if field.name == "_seal":
            continue
        if getattr(supplied_origin, field.name) != getattr(fresh_origin, field.name):
            _reject("origin-rederivation", f"field changed: {field.name}")
    expected_bindings = (
        _sha256(expected_axis_semantics_sha256, label="expected-axis"),
        _sha256(expected_verifier_policy_sha256, label="expected-verifier"),
        _sha256(expected_environment_contract_sha256, label="expected-environment"),
    )
    actual_bindings = (
        fresh_origin.axis_semantics_sha256,
        fresh_origin.verifier_policy_sha256,
        fresh_origin.environment_contract_sha256,
    )
    if expected_bindings != actual_bindings:
        _reject("expected-binding", "axis, verifier, or environment differs")
    if supplied_launch.certifying is not False:
        _reject("certifying", "origin binding cannot make a launch certifying")
    if type(store_scope) is not str or store_scope not in {"production", "fixture"}:
        _reject("store-scope", "expected production or fixture")
    if store_scope == "production":
        _reject("production-authority", "production authority has no issuable origins")
    if type(binding.measurement_head) is not str or _OID_RE.fullmatch(
        binding.measurement_head
    ) is None:
        _reject("measurement-head", "binding measurement head is not a full OID")

    issuer_seal = object()
    capability = OriginBindingCapability(
        authority_blob_sha256=fresh_origin.authority_blob_sha256,
        source_closure_sha256=fresh_origin.source_closure_sha256,
        origin_id=fresh_origin.origin_id,
        cell_key=fresh_origin.cell_key,
        authority_workload=fresh_origin.authority_workload,
        axis_semantics_sha256=fresh_origin.axis_semantics_sha256,
        verifier_policy_sha256=fresh_origin.verifier_policy_sha256,
        environment_contract_sha256=fresh_origin.environment_contract_sha256,
        campaign_id=binding.campaign_id,
        trial_workload=workload,
        measurement_head=binding.measurement_head,
        store_scope="fixture",
        _seal=issuer_seal,
    )
    _ISSUED_CAPABILITY_FIELDS[issuer_seal] = _capability_fields(capability)
    return assert_issued_origin_binding_capability(capability)


def assert_issued_origin_binding_capability(value: object) -> OriginBindingCapability:
    if type(value) is not OriginBindingCapability:
        _reject("issued-capability", "capability was not issued by this module")
    try:
        issued_fields = _ISSUED_CAPABILITY_FIELDS.get(value._seal)
    except TypeError:
        issued_fields = None
    if issued_fields is None or issued_fields != _capability_fields(value):
        _reject("issued-capability", "capability fields differ from issuer snapshot")
    _validate_origin_fields(value)
    _token(value.campaign_id, label="campaign-id")
    _token(value.trial_workload, label="trial-workload")
    if type(value.measurement_head) is not str or _OID_RE.fullmatch(
        value.measurement_head
    ) is None:
        _reject("measurement-head", "expected full lowercase commit OID")
    if value.store_scope != "fixture":
        _reject("store-scope", "only fixture capabilities are currently issuable")
    return value


def origin_binding_capability_record(
    capability: OriginBindingCapability,
) -> dict[str, object]:
    """Return the exact wire projection; its issuer string is not authority."""

    value = assert_issued_origin_binding_capability(capability)
    return {
        "authority_blob_sha256": value.authority_blob_sha256,
        "source_closure_sha256": value.source_closure_sha256,
        "origin_id": value.origin_id,
        "cell_key": value.cell_key,
        "authority_workload": {
            "descriptor_sha256": value.authority_workload.descriptor_sha256,
            "records": value.authority_workload.records,
            "threads": value.authority_workload.threads,
        },
        "axis_semantics_sha256": value.axis_semantics_sha256,
        "verifier_policy_sha256": value.verifier_policy_sha256,
        "environment_contract_sha256": value.environment_contract_sha256,
        "campaign_id": value.campaign_id,
        "trial_workload": value.trial_workload,
        "measurement_head": value.measurement_head,
        "store_scope": value.store_scope,
        "issuer_seal": _WIRE_ISSUER_SEAL,
    }


def assert_origin_binding_capability_record(
    record: object,
    capability: OriginBindingCapability,
) -> None:
    """Reject open, mistyped, or caller-authored projections of a capability."""

    supplied = _exact_mapping(
        record, _CAPABILITY_RECORD_KEYS, label="capability-record"
    )
    workload = _exact_mapping(
        supplied["authority_workload"], _WORKLOAD_KEYS, label="capability-workload"
    )
    _sha256(workload["descriptor_sha256"], label="capability-workload")
    _positive_int(workload["records"], label="capability-workload")
    _positive_int(workload["threads"], label="capability-workload")
    if supplied != origin_binding_capability_record(capability):
        _reject("capability-record", "record differs from issued capability")
