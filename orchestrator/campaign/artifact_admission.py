# -*- coding: utf-8 -*-
"""Admission-aware campaign artifact reader for the T-344 consumer boundary.

The overlay is a deny-only ledger.  It does not revise the verifier verdict that
was recorded at the time: ``verification_status`` and T-316
``admission_status`` are deliberately independent dimensions.

The positive-receipt rule is forward-only, but artifact bytes do not get to
declare themselves historical.  An unlisted receiptless artifact remains
readable only when its path, lock, and WAL exactly match the ledger's trusted
pre-policy Git snapshot.  This proves known history without performing the out-
of-scope repository-wide reclassification of all historical artifacts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from . import (
    campaign_lock,
    contract_loader_binding,
    ident,
    pipeline,
    wal,
)
from .build_admission import GeneratorId, build_run_context
from .layout import CampaignLayout
from .model import (
    COMMIT_CONTRACT_SHA256_KEY,
    Genome,
    STAGE_BUILD_START,
    STAGE_COMMIT,
)


LEDGER_SCHEMA = "legacy-campaign-admission-overlay/v1"
DECISION_SCHEMA = "campaign-artifact-admission-decision/v1"
VALIDATOR_IDENTITY = "orchestrator.campaign.artifact_admission"
LEDGER_PATH = Path(__file__).resolve().with_name("legacy_admission_overlay_v1.json")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SHA256_CHARS = frozenset("0123456789abcdef")
_LEDGER_KEYS = frozenset({
    "schema_version", "authority", "created_from_commit", "input_set_sha256",
    "generation_rule", "records",
})
_AUTHORITY_KEYS = frozenset({"kind", "ruling_id"})
_GENERATION_KEYS = frozenset({
    "scope", "input_projection", "verification_dimension", "admission_dimension",
    "membership_rule", "historicity_rule",
})
_INPUT_KEYS = (
    "path", "campaign_id", "campaign_lock_sha256", "wal_sha256",
    "build_start_count",
)
_RECORD_KEYS = frozenset((*_INPUT_KEYS, "verification_status", "admission_status"))
_TRIGGER_PROVENANCE_BASENAME = "p3_s8a_trigger_loop_provenance.json"


class ArtifactAdmissionError(RuntimeError):
    """Campaign bytes cannot support an admission-aware consumer decision."""


class OverlayLedgerError(ArtifactAdmissionError):
    """The deny-only overlay itself is malformed or inconsistent."""


class OverlayMutationError(ArtifactAdmissionError):
    """A known overlay identity no longer has the exact ruled bytes/topology."""


class CampaignNotAdmitted(ArtifactAdmissionError):
    """A valid decision explicitly excludes the campaign from admitted use."""


@dataclass(frozen=True, slots=True)
class ImmutableWalRecord:
    """Deep-immutable projection of one parser-validated WAL record."""

    variant: str
    stage: str
    env_tag: str
    ts: float
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class CampaignAdmissionDecision:
    classification: str
    admission_status: str
    verification_status: str
    campaign_id: str
    campaign_path: str
    campaign_lock_sha256: str
    wal_sha256: str
    policy_sha256: str | None
    attempt_receipt_sha256s: tuple[str, ...]
    overlay_ledger_sha256: str
    overlay_record_key: str | None
    validator_sha256: str

    @property
    def admitted(self) -> bool:
        return self.admission_status != "legacy-unclassified"

    def as_receipt(self) -> dict[str, Any]:
        """Return the detached exact decision receipt embedded by consumers."""
        return {
            "schema_version": DECISION_SCHEMA,
            "classification": self.classification,
            "admission_status": self.admission_status,
            "verification_status": self.verification_status,
            "campaign_id": self.campaign_id,
            "campaign_path": self.campaign_path,
            "campaign_lock_sha256": self.campaign_lock_sha256,
            "wal_sha256": self.wal_sha256,
            "policy_sha256": self.policy_sha256,
            "attempt_receipt_sha256s": list(self.attempt_receipt_sha256s),
            "validator": {
                "identity": VALIDATOR_IDENTITY,
                "sha256": self.validator_sha256,
            },
            "overlay": {
                "ledger_sha256": self.overlay_ledger_sha256,
                "record_key": self.overlay_record_key,
            },
        }


@dataclass(frozen=True, slots=True)
class AdmittedCampaign:
    """Immutable validated raw-WAL view; raw consumers accept only this type."""

    layout: CampaignLayout
    records: tuple[ImmutableWalRecord, ...]
    decision: CampaignAdmissionDecision

    def __post_init__(self) -> None:
        if (
            type(self.layout) is not CampaignLayout
            or type(self.decision) is not CampaignAdmissionDecision
            or type(self.records) is not tuple
            or not all(type(record) is ImmutableWalRecord for record in self.records)
        ):
            raise TypeError(
                "AdmittedCampaign requires the validator's immutable projection"
            )

    @property
    def root(self) -> str:
        return self.layout.root

    @property
    def wal_file(self) -> str:
        return self.layout.wal_file

    @property
    def lock_file(self) -> str:
        return self.layout.lock_file


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and set(value) <= _SHA256_CHARS
    )


def _is_object_id(value: object) -> bool:
    return (
        type(value) is str
        and len(value) in {40, 64}
        and set(value) <= _SHA256_CHARS
    )


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OverlayLedgerError("overlay value is not canonical JSON") from exc


def _deep_immutable(value: Any) -> Any:
    if type(value) is dict:
        return MappingProxyType({
            key: _deep_immutable(item) for key, item in value.items()
        })
    if type(value) is list:
        return tuple(_deep_immutable(item) for item in value)
    return value


def _immutable_records(records: tuple[Any, ...]) -> tuple[ImmutableWalRecord, ...]:
    return tuple(
        ImmutableWalRecord(
            variant=record.variant,
            stage=record.stage,
            env_tag=record.env_tag,
            ts=record.ts,
            payload=_deep_immutable(record.payload),
        )
        for record in records
    )


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _decode_json(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"), parse_constant=_reject_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ArtifactAdmissionError(f"{label} is not strict JSON") from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ArtifactAdmissionError(f"campaign artifact cannot be read: {path}") from exc
    return digest.hexdigest()


def _record_key(record: Mapping[str, Any]) -> str:
    return (
        f"{record['campaign_id']}|{record['campaign_lock_sha256']}|"
        f"{record['wal_sha256']}"
    )


def _load_ledger() -> tuple[dict[str, Any], str]:
    try:
        raw = LEDGER_PATH.read_bytes()
    except OSError as exc:
        raise OverlayLedgerError(f"overlay ledger cannot be read: {LEDGER_PATH}") from exc
    ledger_sha = hashlib.sha256(raw).hexdigest()
    value = _decode_json(raw, label="overlay ledger")
    if type(value) is not dict or set(value) != _LEDGER_KEYS:
        raise OverlayLedgerError("overlay ledger top-level exact keys differ")
    if value["schema_version"] != LEDGER_SCHEMA:
        raise OverlayLedgerError("overlay ledger schema differs")
    authority = value["authority"]
    if (
        type(authority) is not dict
        or set(authority) != _AUTHORITY_KEYS
        or authority != {
            "kind": "deny-only-admission-overlay",
            "ruling_id": "T-342+T-343+T-344/s4-ruling/1-C",
        }
    ):
        raise OverlayLedgerError("overlay authority differs from the stage-4 ruling")
    if not _is_object_id(value["created_from_commit"]):
        raise OverlayLedgerError("overlay created_from_commit is not an object ID")
    generation = value["generation_rule"]
    if (
        type(generation) is not dict
        or set(generation) != _GENERATION_KEYS
        or generation != {
            "scope": (
                "exactly the three receiptless loop campaigns named by the "
                "stage-4 ruling"
            ),
            "input_projection": list(_INPUT_KEYS),
            "verification_dimension": (
                "preserve the verifier verdict recorded at the time"
            ),
            "admission_dimension": (
                "deny admission-aware selection as legacy-unclassified"
            ),
            "membership_rule": "no inferred, prefix, or future campaign membership",
            "historicity_rule": (
                "unlisted receiptless artifacts require exact path, campaign.lock, "
                "and WAL bytes in created_from_commit"
            ),
        }
    ):
        raise OverlayLedgerError("overlay generation_rule exact keys differ")
    records = value["records"]
    if type(records) is not list or len(records) != 3:
        raise OverlayLedgerError("overlay membership must contain exactly three records")
    paths: set[str] = set()
    ids: set[str] = set()
    lock_shas: set[str] = set()
    wal_shas: set[str] = set()
    for record in records:
        if type(record) is not dict or set(record) != _RECORD_KEYS:
            raise OverlayLedgerError("overlay record exact keys differ")
        if (
            type(record["path"]) is not str
            or type(record["campaign_id"]) is not str
            or Path(record["path"]).name != record["campaign_id"]
            or not _is_sha256(record["campaign_lock_sha256"])
            or not _is_sha256(record["wal_sha256"])
            or type(record["build_start_count"]) is not int
            or record["build_start_count"] < 0
            or record["verification_status"] != "historically-certified"
            or record["admission_status"] != "legacy-unclassified"
        ):
            raise OverlayLedgerError("overlay record value contract differs")
        if (
            record["path"] in paths
            or record["campaign_id"] in ids
            or record["campaign_lock_sha256"] in lock_shas
            or record["wal_sha256"] in wal_shas
        ):
            raise OverlayLedgerError("overlay identity/hash membership is not unique")
        paths.add(record["path"])
        ids.add(record["campaign_id"])
        lock_shas.add(record["campaign_lock_sha256"])
        wal_shas.add(record["wal_sha256"])
    projection = [{key: record[key] for key in _INPUT_KEYS} for record in records]
    if (
        not _is_sha256(value["input_set_sha256"])
        or hashlib.sha256(_canonical_bytes(projection)).hexdigest()
        != value["input_set_sha256"]
    ):
        raise OverlayLedgerError("overlay input_set_sha256 differs from its records")
    return value, ledger_sha


def _layout(value: CampaignLayout | str | Path) -> CampaignLayout:
    if isinstance(value, CampaignLayout):
        return value
    if isinstance(value, (str, Path)):
        return CampaignLayout(root=str(Path(value)))
    raise TypeError("campaign must be CampaignLayout, str, or Path")


def _repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return None


def _current_policy():
    # Generator identity is deliberately absent from the policy preimage.  This
    # public factory is the U1 authority for reconstructing the current stable policy.
    return build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy


def _git_snapshot_sha256(commit: str, path: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "show", f"{commit}:{path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return hashlib.sha256(completed.stdout).hexdigest()


def _is_proven_pre_policy_artifact(
    *, relative: str | None, ledger: Mapping[str, Any],
    lock_sha: str, wal_sha: str,
) -> bool:
    if relative is None:
        return False
    commit = ledger["created_from_commit"]
    return (
        _git_snapshot_sha256(commit, f"{relative}/campaign.lock") == lock_sha
        and _git_snapshot_sha256(commit, f"{relative}/runs/wal.jsonl") == wal_sha
    )


def _is_legacy_trigger_lock(lock: object) -> bool:
    if type(lock) is not dict:
        return False
    search = lock.get("search_config")
    return type(search) is dict and search.get("axis") == wal.TRIGGER_AXIS


def _claims_certified_execution(
        records: tuple[Any, ...] | list[Any],
) -> bool:
    """Return whether WAL records claim a contract-bound certified execution."""
    return any(
        record.stage == STAGE_COMMIT
        and COMMIT_CONTRACT_SHA256_KEY in record.payload
        for record in records
    )


def _parse_canonical_genome(value: object) -> Genome:
    if type(value) is not str or "|" not in value:
        raise ArtifactAdmissionError(
            "post-policy build_start genome is not canonical"
        )
    protocol, body = value.split("|", 1)
    if not protocol:
        raise ArtifactAdmissionError(
            "post-policy build_start genome is not canonical"
        )
    flags: dict[str, int] = {}
    if body:
        for assignment in body.split(","):
            if "=" not in assignment:
                raise ArtifactAdmissionError(
                    "post-policy build_start genome is not canonical"
                )
            key, encoded = assignment.split("=", 1)
            if not key or key in flags:
                raise ArtifactAdmissionError(
                    "post-policy build_start genome is not canonical"
                )
            try:
                flags[key] = int(encoded)
            except ValueError as exc:
                raise ArtifactAdmissionError(
                    "post-policy build_start genome is not canonical"
                ) from exc
    try:
        genome = Genome(protocol=protocol, flags=flags)
    except (TypeError, ValueError) as exc:
        raise ArtifactAdmissionError(
            "post-policy build_start genome is not canonical"
        ) from exc
    if genome.canonical() != value:
        raise ArtifactAdmissionError(
            "post-policy build_start genome is not canonical"
        )
    return genome


def _validate_trigger_provenance(
        root: Path, *, lock: object, records: tuple[Any, ...] | list[Any],
) -> None:
    """Require each proposal provenance commitment to be copied from its WAL start."""
    if not wal.is_trigger_proposal_campaign_lock(lock):
        return
    path = root / "reports" / _TRIGGER_PROVENANCE_BASENAME
    if not path.is_file():
        raise ArtifactAdmissionError("trigger proposal provenance が存在しない")
    try:
        document = _decode_json(path.read_bytes(), label="trigger provenance")
    except OSError as exc:
        raise ArtifactAdmissionError("trigger proposal provenance を読めない") from exc
    entries = document.get("entries") if type(document) is dict else None
    if type(entries) is not dict:
        raise ArtifactAdmissionError("trigger proposal provenance entries が不正")

    starts: dict[str, tuple[str, str]] = {}
    for record in records:
        if record.stage != STAGE_BUILD_START:
            continue
        attempt_id = record.payload.get("build_attempt_id")
        commitment = record.payload.get(wal.TRIGGER_BINDING_COMMITMENT_KEY)
        if type(attempt_id) is not str or type(commitment) is not str:
            raise ArtifactAdmissionError(
                "trigger proposal WAL build_start attempt provenance が不正"
            )
        starts[attempt_id] = (record.variant, commitment)

    provenance_attempts: dict[str, tuple[str, str]] = {}
    for entry in entries.values():
        if type(entry) is not dict:
            raise ArtifactAdmissionError("trigger proposal provenance entry が不正")
        variant = entry.get("variant")
        if variant is None:
            continue
        attempt_id = entry.get("build_attempt_id")
        commitment = entry.get(wal.TRIGGER_BINDING_COMMITMENT_KEY)
        if (type(variant) is not str or type(attempt_id) is not str
                or type(commitment) is not str):
            raise ArtifactAdmissionError(
                "trigger proposal provenance attempt/commitment が不正"
            )
        pair = (variant, commitment)
        previous = provenance_attempts.setdefault(attempt_id, pair)
        if previous != pair:
            raise ArtifactAdmissionError(
                "trigger proposal provenance attempt の参照が競合"
            )
    if starts != provenance_attempts:
        raise ArtifactAdmissionError(
            "trigger proposal provenance attempt/commitment が WAL build_start と不一致"
        )


def _validate_trigger_proposal_campaign_id(
        *, decoded: campaign_lock.DecodedCampaignLock, campaign_id: str,
) -> None:
    """Retain the pre-existing trigger-proposal directory identity check.

    T-671 temporarily broadened this check to every v2 lock.  That unapproved
    broadening rejected valid non-trigger consumers which deliberately relocate
    an otherwise self-contained campaign view, so only the original trigger
    proposal axis remains subject to the directory-name binding.
    """
    if not decoded.is_v2:
        raise ArtifactAdmissionError("directory identity validation requires v2 lock")
    lock = decoded.identity
    if not wal.is_trigger_proposal_campaign_lock(lock):
        return
    identity_bytes = decoded.identity_preimage.encode("utf-8")
    search_tag = lock.get("search_tag")
    if type(search_tag) is not str or not search_tag:
        raise ArtifactAdmissionError("post-policy campaign.lock search_tag が不正")
    cfg_hash8 = hashlib.sha256(identity_bytes).hexdigest()[:8]
    suffix = f"-{search_tag}-{cfg_hash8}"
    slug = campaign_id[:-len(suffix)] if campaign_id.endswith(suffix) else ""
    expected = f"{slug}{suffix}" if slug else ""
    if expected != campaign_id:
        raise ArtifactAdmissionError(
            "post-policy campaign directory ID が inner identity preimage と不一致"
        )


def _decode_campaign_lock(
        lock_raw: bytes,
) -> campaign_lock.DecodedCampaignLock:
    try:
        return campaign_lock.decode_campaign_lock_bytes(lock_raw)
    except campaign_lock.CampaignLockCodecError as exc:
        raise ArtifactAdmissionError(
            f"campaign.lock codec validation failed: {exc}"
        ) from exc


def _verify_committed_loader_binding(
        decoded: campaign_lock.DecodedCampaignLock,
) -> None:
    authority = decoded.authority
    if authority is None:
        raise ArtifactAdmissionError("campaign-lock/v2 authority が存在しない")
    try:
        binding = contract_loader_binding.binding_from_authority(
            authority.contract_loader_commit,
            authority.contract_loader_blob_sha256s,
        )
        contract_loader_binding.verify_committed_contract_loader_binding(binding)
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise ArtifactAdmissionError(
            f"contract loader committed validation failed: {exc}"
        ) from exc


def _validate_recorded_activation(
        decoded: campaign_lock.DecodedCampaignLock,
) -> None:
    """Map the shared resume/admission tuple validator onto this error surface."""
    try:
        ident.verify_recorded_activation_tuple(decoded)
    except ident.IdentityMismatch as exc:
        raise ArtifactAdmissionError(str(exc)) from exc


def _inspect_campaign(
    campaign: CampaignLayout | str | Path,
) -> tuple[CampaignAdmissionDecision, tuple[Any, ...]]:
    layout = _layout(campaign)
    root = Path(layout.root).resolve()
    lock_path = root / "campaign.lock"
    wal_path = root / "runs" / "wal.jsonl"
    if not root.is_dir() or not lock_path.is_file() or not wal_path.is_file():
        raise ArtifactAdmissionError("campaign requires a directory, campaign.lock, and WAL")

    ledger, ledger_sha = _load_ledger()
    campaign_id = root.name
    relative = _repo_relative(root)
    try:
        lock_raw = lock_path.read_bytes()
    except OSError as exc:
        raise ArtifactAdmissionError(
            f"campaign artifact cannot be read: {lock_path}"
        ) from exc
    lock_sha = hashlib.sha256(lock_raw).hexdigest()
    wal_sha = _sha256_file(wal_path)
    validator_sha = _sha256_file(Path(__file__))
    identity_matches = [
        record for record in ledger["records"]
        if record["campaign_id"] == campaign_id
        or (relative is not None and record["path"] == relative)
    ]
    hash_matches = [
        record for record in ledger["records"]
        if record["campaign_lock_sha256"] == lock_sha
        or record["wal_sha256"] == wal_sha
    ]
    candidates = {
        _record_key(record): record
        for record in (*identity_matches, *hash_matches)
    }
    if candidates:
        if len(candidates) != 1:
            raise OverlayLedgerError("overlay identity lookup is ambiguous")
        record = next(iter(candidates.values()))
        # A ruled overlay member is identified by its exact bytes before any
        # semantic WAL parse.  A byte mutation may itself make the WAL malformed;
        # that must remain an overlay-tampering verdict rather than fall through
        # to the generic WAL parser/error surface.
        hashes_are_exact = (
            lock_sha == record["campaign_lock_sha256"]
            and wal_sha == record["wal_sha256"]
        )
        identity_is_exact = (
            relative == record["path"]
            and campaign_id == record["campaign_id"]
        )
        if not hashes_are_exact:
            raise OverlayMutationError(
                "known overlay campaign bytes/path/topology differ from the ruled record"
            )
        records, truncated = wal.read_records_checked(layout)
        build_start_count = sum(item.stage == STAGE_BUILD_START for item in records)
        if build_start_count != record["build_start_count"] or truncated:
            raise OverlayMutationError(
                "known overlay campaign bytes/path/topology differ from the ruled record"
            )
        # Exact ruled bytes remain denied after relocation.  Path/id are retained
        # in the receipt as ledger provenance, not trusted as the membership key.
        return CampaignAdmissionDecision(
            classification="overlay-denied",
            admission_status=record["admission_status"],
            verification_status=record["verification_status"],
            campaign_id=record["campaign_id"] if not identity_is_exact else campaign_id,
            campaign_path=record["path"],
            campaign_lock_sha256=lock_sha,
            wal_sha256=wal_sha,
            policy_sha256=None,
            attempt_receipt_sha256s=(),
            overlay_ledger_sha256=ledger_sha,
            overlay_record_key=_record_key(record),
            validator_sha256=validator_sha,
        ), tuple(records)

    decoded = _decode_campaign_lock(lock_raw)
    lock = decoded.identity
    search = lock["search_config"]
    if decoded.is_v2:
        _verify_committed_loader_binding(decoded)
        _validate_recorded_activation(decoded)
        if "build_admission" not in search:
            raise ArtifactAdmissionError(
                "campaign-lock/v2 identity lacks build_admission"
            )
        _validate_trigger_proposal_campaign_id(
            decoded=decoded, campaign_id=campaign_id,
        )

    records, truncated = wal.read_records_checked(layout)

    if (decoded.is_v1 and "build_admission" in search
            and _claims_certified_execution(records)):
        raise ArtifactAdmissionError(
            "campaign-lock/v1 with build_admission is a post-policy downgrade"
        )

    if decoded.is_v1 and "build_admission" not in search:
        if not _is_proven_pre_policy_artifact(
            relative=relative,
            ledger=ledger,
            lock_sha=lock_sha,
            wal_sha=wal_sha,
        ):
            raise ArtifactAdmissionError(
                "receiptless campaign historicity is not proven by the pre-policy snapshot"
            )
        if _sha256_file(lock_path) != lock_sha or _sha256_file(wal_path) != wal_sha:
            raise ArtifactAdmissionError(
                "campaign bytes changed during admission validation"
            )
        return CampaignAdmissionDecision(
            classification="historical-pre-admission-schema",
            admission_status=(
                "legacy-unclassified"
                if _is_legacy_trigger_lock(lock)
                else "historical-not-reclassified"
            ),
            verification_status="not-evaluated-by-overlay",
            campaign_id=campaign_id,
            campaign_path=relative or root.as_posix(),
            campaign_lock_sha256=lock_sha,
            wal_sha256=wal_sha,
            policy_sha256=None,
            attempt_receipt_sha256s=(),
            overlay_ledger_sha256=ledger_sha,
            overlay_record_key=None,
            validator_sha256=validator_sha,
        ), tuple(records)

    if truncated:
        raise ArtifactAdmissionError("post-policy campaign WAL has a truncated tail")
    policy = _current_policy()
    if search["build_admission"] != policy.as_preimage():
        raise ArtifactAdmissionError("post-policy campaign lock admission policy differs")
    try:
        wal._validate_attempt_topology(
            records, admission_policy=policy, campaign_lock=decoded,
        )
        if (wal.is_trigger_machine_campaign_lock(lock)
                and any(
                    type(record.payload.get("build_admission")) is dict
                    and record.payload["build_admission"].get("class")
                    == "coder-authored"
                    for record in records if record.stage == STAGE_BUILD_START
                )):
            raise wal.AttemptTopologyError(
                "trigger machine campaign の coder-authored receipt は binding が必要"
            )
        wal.validate_trigger_bindings(
            records, campaign_lock=lock, require_build_start=True,
        )
    except (wal.AttemptTopologyError, TypeError) as exc:
        raise ArtifactAdmissionError(
            f"post-policy campaign attempt admission is invalid: {exc}"
        ) from exc
    _validate_trigger_provenance(root, lock=lock, records=records)

    receipt_shas: list[str] = []
    lock_commit = lock.get("ccbench_commit")
    for record in records:
        if record.stage != STAGE_BUILD_START:
            continue
        receipt = record.payload.get("build_admission")
        if receipt is None:
            continue  # U2 permits a receiptless pre-build rejection only.
        source = receipt.get("source") if type(receipt) is dict else None
        genome = record.payload.get("genome")
        src_token = record.payload.get("src_token")
        if (
            type(source) is not dict
            or type(genome) is not str
            or source.get("genome_sha256")
            != hashlib.sha256(genome.encode("utf-8")).hexdigest()
            or source.get("src_token") != src_token
            or source.get("ccbench_commit") != lock_commit
        ):
            raise ArtifactAdmissionError(
                "post-policy build_start source evidence differs from WAL/lock identity"
            )
        genome_value = _parse_canonical_genome(genome)
        expected_variant = pipeline.variant_id(genome_value, src_token)
        if record.variant != expected_variant:
            raise ArtifactAdmissionError(
                "post-policy WAL variant differs from canonical genome/source identity"
            )
        receipt_shas.append(receipt["receipt_sha256"])

    # Re-reads are reject-only: parsing and the receipt remain bound to lock_raw.
    if _sha256_file(lock_path) != lock_sha or _sha256_file(wal_path) != wal_sha:
        raise ArtifactAdmissionError("campaign bytes changed during admission validation")
    return CampaignAdmissionDecision(
        classification="admitted-new-schema",
        admission_status="admitted",
        verification_status="not-evaluated-by-overlay",
        campaign_id=campaign_id,
        campaign_path=relative or root.as_posix(),
        campaign_lock_sha256=lock_sha,
        wal_sha256=wal_sha,
        policy_sha256=policy.sha256,
        attempt_receipt_sha256s=tuple(receipt_shas),
        overlay_ledger_sha256=ledger_sha,
        overlay_record_key=None,
        validator_sha256=validator_sha,
    ), tuple(records)


def classify_campaign(
    campaign: CampaignLayout | str | Path,
) -> CampaignAdmissionDecision:
    """Classify exact campaign bytes without admitting a denied overlay record."""
    decision, _records = _inspect_campaign(campaign)
    return decision


def require_admitted_campaign(
    campaign: CampaignLayout | str | Path,
) -> AdmittedCampaign:
    """Issue the sole raw-WAL consumer view after the shared validator succeeds."""
    decision, records = _inspect_campaign(campaign)
    if not decision.admitted:
        raise CampaignNotAdmitted(
            f"campaign is {decision.admission_status}: {decision.campaign_id}; "
            f"overlay={decision.overlay_ledger_sha256} "
            f"record={decision.overlay_record_key}"
        )
    return AdmittedCampaign(
        layout=_layout(campaign),
        records=_immutable_records(records),
        decision=decision,
    )
