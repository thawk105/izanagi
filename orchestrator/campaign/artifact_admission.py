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
import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence, final, overload

from . import (
    campaign_lock,
    contract_loader_binding,
    env_contract,
    ident,
    pipeline,
    wal,
)
from .build_admission import (
    BuildAdmissionError, BuildAdmissionPolicy, HistoricalBuildAdmissionPolicy,
    GeneratorId, build_run_context, decode_historical_build_admission_policy,
)
from .layout import CampaignLayout
from .model import (
    COMMIT_CONTRACT_SHA256_KEY,
    Genome,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
)
from ..verifier.commit_receipt import (
    CommitReceiptError,
    RECEIPT_PAYLOAD_KEY,
    validate_serialized_receipt,
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
_CAMPAIGN_VERIFIER_EPOCH_DOMAIN = b"campaign-verifier-epoch/v1"
_CERTIFIED_VIEW_TOKEN = object()
CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (curated exact 63 path; source-import 推移閉包ではない; "
    "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
    "2026-09-16 (a1b40608c) の実測では 162 module、うち収載 63)"
)
CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "同実測の発見集合の未収載 99 module、同発見集合に入らない module、"
    "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
    "package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、"
    "外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり "
    "(収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない"
)
PRE_T733_CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
    "enforcement source closure (exact 24 path; witness gate、S8C 判定器、"
    "receipt 発行・検証面を含む)"
)
PRE_T733_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
    "verifier package のうち orchestrator/verifier/__main__.py と "
    "orchestrator/verifier/cli.py、および package 外の orchestrator/verify.py の "
    "implementation bytes は束縛しない"
)


def _bind_replay_admission_capability_issuer():
    issuer_token = object()
    issued: dict[object, tuple[object, tuple, int]] = {}

    class _ReplayAdmissionCapability:
        __slots__ = ("_nonce",)

        def __init__(self, decision, records, token):
            if token is not issuer_token:
                raise TypeError("replay admission capability is admission-issued")
            nonce = object()
            issued[nonce] = (decision, records, os.getpid())
            self._nonce = nonce

        def _assert_source(self, view, record) -> None:
            try:
                decision, records, issuer_pid = issued[self._nonce]
            except (AttributeError, KeyError, TypeError) as exc:
                raise TypeError(
                    "replay admission capability lacks issuer authority"
                ) from exc
            if (type(self) is not _ReplayAdmissionCapability
                    or issuer_pid != os.getpid()
                    or view._replay_admission_capability is not self
                    or view.decision is not decision
                    or view.records is not records
                    or not any(record is row for row in records)
                    or record.stage != STAGE_COMMIT):
                raise TypeError(
                    "replay evidence requires the admission-issued source record"
                )

    def issue(decision, records):
        return _ReplayAdmissionCapability(decision, records, issuer_token)

    def assert_source(view, record) -> None:
        capability = view._replay_admission_capability
        if type(capability) is not _ReplayAdmissionCapability:
            raise TypeError(
                "certified view lacks exact replay admission authority"
            )
        capability._assert_source(view, record)

    return issue, assert_source


(
    _issue_replay_admission_capability,
    _assert_replay_admission_source,
) = _bind_replay_admission_capability_issuer()
del _bind_replay_admission_capability_issuer


class ArtifactAdmissionError(RuntimeError):
    """Campaign bytes cannot support an admission-aware consumer decision."""


class OverlayLedgerError(ArtifactAdmissionError):
    """The deny-only overlay itself is malformed or inconsistent."""


class OverlayMutationError(ArtifactAdmissionError):
    """A known overlay identity no longer has the exact ruled bytes/topology."""


class CampaignNotAdmitted(ArtifactAdmissionError):
    """A valid decision explicitly excludes the campaign from admitted use."""


class CampaignReadPurpose(str, Enum):
    """Campaign raw bytes を読む exact 2 値の目的。"""

    CERTIFIED_ACCEPTANCE = "CERTIFIED_ACCEPTANCE"
    HISTORICAL_RAW = "HISTORICAL_RAW"


@dataclass(frozen=True, slots=True)
class CampaignVerifierEpoch:
    """記録された enforcement source closure の epoch 診断。

    保証する範囲とその除外範囲の正本は、それぞれ
    ``CAMPAIGN_VERIFIER_EPOCH_SCOPE`` と
    ``CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE`` である。
    """

    campaign_verifier_epoch: str
    state: str
    reason_code: str
    identity_scope: str = CAMPAIGN_VERIFIER_EPOCH_SCOPE
    excluded_scope: str = CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE

    def __post_init__(self) -> None:
        if self.identity_scope != CAMPAIGN_VERIFIER_EPOCH_SCOPE:
            raise TypeError("campaign verifier epoch identity scope が不正")
        if self.excluded_scope != CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE:
            raise TypeError("campaign verifier epoch excluded scope が不正")
        if self.state == "E0":
            valid = (
                self.campaign_verifier_epoch == "E0"
                and self.reason_code == "v1-authority-absent"
            )
        elif self.state == "E1":
            valid = (
                self.campaign_verifier_epoch.startswith("E1:")
                and _is_sha256(self.campaign_verifier_epoch[3:])
                and self.reason_code == "recorded-closure"
            )
        else:
            valid = (
                self.state == "E1-stale"
                and self.campaign_verifier_epoch.startswith("E1:")
                and _is_sha256(self.campaign_verifier_epoch[3:])
                and self.reason_code in {
                    "recorded-current-closure-mismatch",
                    "current-closure-unavailable",
                }
            )
        if not valid:
            raise TypeError("campaign verifier epoch diagnostic が不正")


@dataclass(frozen=True, slots=True)
class HistoricalCampaignVerifierEpoch(CampaignVerifierEpoch):
    """pre-T733 exact-24 grammar から再現した歴史閲覧専用 epoch。"""

    identity_scope: str = PRE_T733_CAMPAIGN_VERIFIER_EPOCH_SCOPE
    excluded_scope: str = PRE_T733_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE

    @property
    def current_verifier_conformance(self) -> str:
        return "unknown"

    def __post_init__(self) -> None:
        valid = (
            self.campaign_verifier_epoch.startswith("E1:")
            and _is_sha256(self.campaign_verifier_epoch[3:])
            and self.state == "E1"
            and self.reason_code == "recorded-closure"
            and self.identity_scope == PRE_T733_CAMPAIGN_VERIFIER_EPOCH_SCOPE
            and self.excluded_scope
            == PRE_T733_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE
        )
        if not valid:
            raise TypeError("historical campaign verifier epoch diagnostic が不正")


class CampaignVerifierEpochRejected(CampaignNotAdmitted):
    """Certified use cannot satisfy its recorded-epoch or closure prerequisites."""

    def __init__(self, epoch: CampaignVerifierEpoch):
        self.campaign_verifier_epoch = epoch.campaign_verifier_epoch
        self.epoch_state = epoch.state
        self.reason_code = epoch.reason_code
        self.identity_scope = epoch.identity_scope
        self.excluded_scope = epoch.excluded_scope
        super().__init__(
            "campaign verifier epoch rejected certified acceptance: "
            f"state={epoch.state} reason={epoch.reason_code} "
            f"epoch={epoch.campaign_verifier_epoch}; "
            f"scope={epoch.identity_scope}; excludes={epoch.excluded_scope}"
        )


@dataclass(frozen=True, slots=True)
class _RecordedCampaignVerifierEpoch:
    diagnostic: CampaignVerifierEpoch
    blob_sha256s: Mapping[str, str] | None

    def __post_init__(self) -> None:
        if type(self.diagnostic) not in {
            CampaignVerifierEpoch,
            HistoricalCampaignVerifierEpoch,
        }:
            raise TypeError("recorded verifier epoch diagnostic が不正")
        if self.diagnostic.state == "E0":
            if self.blob_sha256s is not None:
                raise TypeError("E0 verifier epoch に blob map は存在しない")
            return
        if type(self.blob_sha256s) is not MappingProxyType:
            raise TypeError("E1 verifier epoch blob map は immutable projection が必要")
        expected_paths = (
            campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
            if type(self.diagnostic) is HistoricalCampaignVerifierEpoch
            else campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        )
        if tuple(self.blob_sha256s) != expected_paths:
            raise TypeError("E1 verifier epoch blob map の exact path 順序が不正")


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
    """Immutable validated raw-WAL view shared by the two nominal view types."""

    layout: CampaignLayout
    records: tuple[ImmutableWalRecord, ...]
    decision: CampaignAdmissionDecision
    campaign_verifier_epoch: CampaignVerifierEpoch

    def __post_init__(self) -> None:
        if (
            type(self.layout) is not CampaignLayout
            or type(self.decision) is not CampaignAdmissionDecision
            or type(self.campaign_verifier_epoch) not in {
                CampaignVerifierEpoch,
                HistoricalCampaignVerifierEpoch,
            }
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


@final
@dataclass(frozen=True, slots=True, init=False)
class CertifiedCampaignView(AdmittedCampaign):
    """記録 commit に束縛した E1 と current closure 可用性を持つ専用 view。

    件数は共通 admission 入口が WAL snapshot から投影した値であり、各 commit が
    証拠検査を通ったことを独立に証明するものではない。
    この view 自体は commit の存在を保証しない。存在保証を与えるのは
    ``require_certified_commit_evidence`` だけである。
    """

    persisted_certified_commit_count: int = field(compare=True)

    _replay_admission_capability: object = field(
        repr=False,
        compare=False,
    )

    def __init__(
            self, *, layout: CampaignLayout,
            records: tuple[ImmutableWalRecord, ...],
            decision: CampaignAdmissionDecision,
            campaign_verifier_epoch: CampaignVerifierEpoch,
            persisted_certified_commit_count: int,
            _certification_token: object,
            _replay_admission_capability: object = None,
    ) -> None:
        if _certification_token is not _CERTIFIED_VIEW_TOKEN:
            raise TypeError(
                "CertifiedCampaignView は certified epoch gate だけが発行できる"
            )
        object.__setattr__(self, "layout", layout)
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(
            self, "campaign_verifier_epoch", campaign_verifier_epoch,
        )
        object.__setattr__(
            self,
            "persisted_certified_commit_count",
            persisted_certified_commit_count,
        )
        object.__setattr__(
            self,
            "_replay_admission_capability",
            _replay_admission_capability,
        )
        self.__post_init__()

    def __post_init__(self) -> None:
        AdmittedCampaign.__post_init__(self)
        if (type(self.campaign_verifier_epoch) is not CampaignVerifierEpoch
                or self.campaign_verifier_epoch.state != "E1"):
            raise TypeError("CertifiedCampaignView requires exact E1")
        count = self.persisted_certified_commit_count
        if type(count) is not int:
            raise TypeError(
                "persisted certified commit count requires exact int"
            )
        if count < 0:
            raise ValueError(
                "persisted certified commit count must be non-negative"
            )
        snapshot_commit_count = sum(
            record.stage == STAGE_COMMIT for record in self.records
        )
        if count != snapshot_commit_count:
            raise ValueError(
                "persisted certified commit count does not match WAL snapshot"
            )

    @property
    def read_purpose(self) -> CampaignReadPurpose:
        return CampaignReadPurpose.CERTIFIED_ACCEPTANCE


@final
@dataclass(frozen=True, slots=True)
class HistoricalCampaignView(AdmittedCampaign):
    """現在 bytes を参照せず、記録当時の判定だけを保持する historical view。"""

    def __post_init__(self) -> None:
        AdmittedCampaign.__post_init__(self)
        if self.campaign_verifier_epoch.state not in {"E0", "E1"}:
            raise TypeError("HistoricalCampaignView requires a recorded epoch")

    @property
    def read_purpose(self) -> CampaignReadPurpose:
        return CampaignReadPurpose.HISTORICAL_RAW

    @property
    def verifier_assessment_basis(self) -> str:
        return "recorded-at-original-verifier-epoch"

    @property
    def current_verifier_conformance(self) -> str:
        return "unknown"


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


def _thaw_receipt_json(value: Any) -> Any:
    """Copy parser or immutable-view JSON into exact dict/list containers."""
    if type(value) in {dict, MappingProxyType}:
        return {
            key: _thaw_receipt_json(item)
            for key, item in value.items()
        }
    if type(value) in {list, tuple}:
        return [_thaw_receipt_json(item) for item in value]
    return value


def require_persisted_certified_commit(
        records, commit_record, *, campaign_lock_sha256: str,
):
    """Require one persisted COMMIT to retain its certified WAL evidence."""
    if getattr(commit_record, "stage", None) != STAGE_COMMIT:
        raise TypeError("persisted certification requires a COMMIT record")
    commit_index = next(
        (index for index, record in enumerate(records)
         if record is commit_record),
        None,
    )
    if commit_index is None:
        raise TypeError("COMMIT record must belong to the supplied WAL records")
    attempt_id = commit_record.payload.get("build_attempt_id")
    if type(attempt_id) is not str or not attempt_id:
        raise ArtifactAdmissionError(
            "COMMIT build_attempt_id must be a non-empty exact str"
        )

    verifies = [
        record
        for record in records[:commit_index]
        if record.stage == STAGE_VERIFY_DONE
        and record.variant == commit_record.variant
        and record.payload.get("build_attempt_id") == attempt_id
    ]
    if not verifies:
        raise ArtifactAdmissionError(
            "persisted COMMIT has no preceding verify_done for its attempt"
        )

    wal_evidence: list[tuple[str, str, bool]] = []
    for verify in verifies:
        payload = verify.payload
        if payload.get("verdict") != "serializable":
            raise ArtifactAdmissionError(
                "persisted COMMIT verify verdict is not serializable"
            )
        if payload.get("certified") is not True:
            raise ArtifactAdmissionError(
                "persisted COMMIT verify evidence is not certified"
            )
        anomalies = payload.get("anomalies")
        if type(anomalies) is not int or anomalies != 0:
            raise ArtifactAdmissionError(
                "persisted COMMIT verify anomalies must be exact int zero"
            )
        workload = payload.get("workload")
        workload_tag = (
            workload.get("tag")
            if type(workload) in {dict, MappingProxyType}
            else None
        )
        if type(workload_tag) is not str or not workload_tag:
            raise ArtifactAdmissionError(
                "persisted COMMIT verify workload tag is invalid"
            )
        wal_evidence.append((workload_tag, "serializable", True))

    commit_payload = _thaw_receipt_json(commit_record.payload)
    serialized_receipt = commit_payload.pop(RECEIPT_PAYLOAD_KEY, None)
    try:
        validated_receipt = validate_serialized_receipt(
            serialized_receipt,
            sink_kind="campaign-wal",
            lock_identity_sha256=campaign_lock_sha256,
            variant=commit_record.variant,
            terminal_payload=commit_payload,
        )
    except CommitReceiptError as exc:
        raise ArtifactAdmissionError(
            "persisted COMMIT verification receipt is invalid"
        ) from exc
    if validated_receipt["operation_identity"] != attempt_id:
        raise ArtifactAdmissionError(
            "persisted COMMIT receipt operation does not match its attempt"
        )
    receipt_evidence = [
        (row["workload_tag"], row["verdict"], row["certified"])
        for row in validated_receipt["verifier_evidence"]
    ]
    if receipt_evidence != wal_evidence:
        raise ArtifactAdmissionError(
            "persisted COMMIT receipt evidence does not match WAL verifies"
        )
    return commit_record


def admit_persisted_certified_commits(
        records: Sequence[object], *, campaign_lock_sha256: str,
) -> int:
    """Validate every persisted COMMIT against the full WAL evidence set."""
    admitted_count = 0
    for record in records:
        if record.stage == STAGE_COMMIT:
            require_persisted_certified_commit(
                records,
                record,
                campaign_lock_sha256=campaign_lock_sha256,
            )
            admitted_count += 1
    return admitted_count


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
        *, decoded: (
            campaign_lock.DecodedCampaignLock
            | campaign_lock.DecodedHistoricalCampaignLock
        ), campaign_id: str,
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


def _decode_historical_campaign_lock(
        lock_raw: bytes,
) -> campaign_lock.DecodedHistoricalCampaignLock:
    try:
        return campaign_lock.decode_historical_campaign_lock_bytes(lock_raw)
    except campaign_lock.CampaignLockCodecError as exc:
        raise ArtifactAdmissionError(
            f"historical campaign.lock codec validation failed: {exc}"
        ) from exc


def _decode_campaign_lock_for_purpose(
        lock_raw: bytes, *, purpose: CampaignReadPurpose,
) -> (
    campaign_lock.DecodedCampaignLock
    | campaign_lock.DecodedHistoricalCampaignLock
):
    _validate_read_purpose(purpose)
    if purpose is CampaignReadPurpose.HISTORICAL_RAW:
        return _decode_historical_campaign_lock(lock_raw)
    return _decode_campaign_lock(lock_raw)


def _build_admission_policy_for_purpose(
        recorded: object, *, purpose: CampaignReadPurpose,
) -> BuildAdmissionPolicy | HistoricalBuildAdmissionPolicy:
    _validate_read_purpose(purpose)
    if purpose is CampaignReadPurpose.HISTORICAL_RAW:
        try:
            return decode_historical_build_admission_policy(recorded)
        except BuildAdmissionError as exc:
            raise ArtifactAdmissionError(str(exc)) from exc
    policy = _current_policy()
    if recorded != policy.as_preimage():
        raise ArtifactAdmissionError("post-policy campaign lock admission policy differs")
    return policy


def _verify_committed_loader_binding(
        decoded: (
            campaign_lock.DecodedCampaignLock
            | campaign_lock.DecodedHistoricalCampaignLock
        ),
) -> None:
    authority = decoded.authority
    if authority is None:
        raise ArtifactAdmissionError("campaign-lock/v2 authority が存在しない")
    try:
        if (type(decoded) is campaign_lock.DecodedHistoricalCampaignLock
                and authority.recorded_contract_loader_relative_paths
                == campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS):
            contract_loader_binding.verify_committed_contract_loader_blobs(
                authority.contract_loader_commit,
                authority.contract_loader_blob_sha256s,
                authority.recorded_contract_loader_relative_paths,
            )
            return
        binding = contract_loader_binding.binding_from_authority(
            authority.contract_loader_commit,
            authority.contract_loader_blob_sha256s,
        )
        contract_loader_binding.verify_committed_contract_loader_binding(binding)
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise ArtifactAdmissionError(
            f"contract loader committed validation failed: {exc}"
        ) from exc


def _recorded_campaign_verifier_epoch(
        decoded: (
            campaign_lock.DecodedCampaignLock
            | campaign_lock.DecodedHistoricalCampaignLock
        ),
) -> _RecordedCampaignVerifierEpoch:
    """記録値だけから enforcement closure epoch を導出する。

    現行 grammar の scope は ``CAMPAIGN_VERIFIER_EPOCH_*``、pre-T733
    exact-24 の scope は ``PRE_T733_CAMPAIGN_VERIFIER_EPOCH_*`` に固定する。
    v2 の記録 map は記録 commit に対して真正と検証してから表示 ID を作る。
    """
    authority = decoded.authority
    if authority is None:
        return _RecordedCampaignVerifierEpoch(
            diagnostic=CampaignVerifierEpoch(
                campaign_verifier_epoch="E0",
                state="E0",
                reason_code="v1-authority-absent",
            ),
            blob_sha256s=None,
        )
    _verify_committed_loader_binding(decoded)
    relative_paths = (
        authority.recorded_contract_loader_relative_paths
        if type(authority) is campaign_lock.HistoricalCampaignLockAuthority
        else campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )
    recorded_map = {
        relative: authority.contract_loader_blob_sha256s[relative]
        for relative in relative_paths
    }
    payload = _CAMPAIGN_VERIFIER_EPOCH_DOMAIN + b"".join(
        relative.encode("utf-8") + b"\0" + bytes.fromhex(recorded_map[relative])
        for relative in relative_paths
    )
    display = f"E1:{hashlib.sha256(payload).hexdigest()}"
    diagnostic: CampaignVerifierEpoch
    if relative_paths == campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS:
        diagnostic = HistoricalCampaignVerifierEpoch(
            campaign_verifier_epoch=display,
            state="E1",
            reason_code="recorded-closure",
        )
    else:
        diagnostic = CampaignVerifierEpoch(
            campaign_verifier_epoch=display,
            state="E1",
            reason_code="recorded-closure",
        )
    return _RecordedCampaignVerifierEpoch(
        diagnostic=diagnostic,
        blob_sha256s=MappingProxyType(recorded_map),
    )


def _validate_read_purpose(purpose: CampaignReadPurpose) -> None:
    if type(purpose) is not CampaignReadPurpose:
        raise TypeError(
            "purpose は exact CampaignReadPurpose.CERTIFIED_ACCEPTANCE "
            "または HISTORICAL_RAW が必要"
        )


def _stale_epoch(
        recorded: _RecordedCampaignVerifierEpoch, *, reason_code: str,
) -> CampaignVerifierEpoch:
    return CampaignVerifierEpoch(
        campaign_verifier_epoch=recorded.diagnostic.campaign_verifier_epoch,
        state="E1-stale",
        reason_code=reason_code,
    )


def _require_verifier_epoch_for_purpose(
        recorded: _RecordedCampaignVerifierEpoch,
        purpose: CampaignReadPurpose,
) -> CampaignVerifierEpoch:
    """中央の目的別 gate。history は current closure を一切参照しない。"""
    _validate_read_purpose(purpose)
    if purpose is CampaignReadPurpose.HISTORICAL_RAW:
        return recorded.diagnostic
    if type(recorded.diagnostic) is HistoricalCampaignVerifierEpoch:
        raise AssertionError("historical epoch cannot enter certified acceptance")
    if recorded.diagnostic.state == "E0":
        raise CampaignVerifierEpochRejected(recorded.diagnostic)
    try:
        # D1163 keeps only the availability prerequisite here.  A clean
        # committed current closure may differ from the recorded closure.
        contract_loader_binding.capture_contract_loader_binding()
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise CampaignVerifierEpochRejected(_stale_epoch(
            recorded, reason_code="current-closure-unavailable",
        )) from exc
    return recorded.diagnostic


def require_campaign_verifier_epoch(
        campaign: CampaignLayout | str | Path, *,
        purpose: CampaignReadPurpose,
) -> CampaignVerifierEpoch:
    """WAL を読まず campaign.lock だけで中央 epoch gate を適用する。

    certified は現行 scope だけ、historical exact-24 は当時の scope を返す。
    """
    _validate_read_purpose(purpose)
    layout = _layout(campaign)
    lock_path = Path(layout.lock_file)
    try:
        lock_raw = lock_path.read_bytes()
    except OSError as exc:
        raise ArtifactAdmissionError(
            f"campaign.lock cannot be read: {lock_path}"
        ) from exc
    recorded = _recorded_campaign_verifier_epoch(
        _decode_campaign_lock_for_purpose(lock_raw, purpose=purpose)
    )
    return _require_verifier_epoch_for_purpose(recorded, purpose)


def _validate_recorded_activation(
        decoded: (
            campaign_lock.DecodedCampaignLock
            | campaign_lock.DecodedHistoricalCampaignLock
        ),
) -> None:
    """Map the shared resume/admission tuple validator onto this error surface."""
    if type(decoded) is campaign_lock.DecodedCampaignLock:
        try:
            ident.verify_recorded_activation_tuple(decoded)
        except ident.IdentityMismatch as exc:
            raise ArtifactAdmissionError(str(exc)) from exc
        return
    authority = decoded.authority
    if authority is None or not decoded.is_v2:
        raise ArtifactAdmissionError(
            "activation tuple 検証には exact historical v2 campaign.lock が必要"
        )
    try:
        current = env_contract.verified_current_activation_state()
        if authority.activation_serial > current.activation_serial:
            raise env_contract.EnvContractError(
                "記録 activation serial が current chain head を越えている"
            )
        recorded = env_contract.verified_historical_activation_state(
            authority.activation_serial,
            authority.activation_state_sha256,
        )
        target_rows = tuple(
            row for row in recorded.active_contracts
            if row.contract_sha256 == authority.environment_contract_sha256
        )
        if len(target_rows) != 1:
            raise env_contract.EnvContractError(
                "記録 activation state が対象 environment contract H を active "
                "にしていない"
            )
    except env_contract.EnvContractError as exc:
        raise ArtifactAdmissionError(
            f"campaign-lock activation tuple is not authentic: {exc}"
        ) from exc


def _validate_historical_commit_contract_bindings(
        records: Sequence[Any],
        decoded: campaign_lock.DecodedHistoricalCampaignLock,
) -> None:
    authority = decoded.authority
    if authority is None:
        raise ArtifactAdmissionError("historical v2 authority が存在しない")
    try:
        resolved = env_contract.resolve_by_contract_sha256(
            authority.environment_contract_sha256
        )
    except env_contract.EnvContractError as exc:
        raise ArtifactAdmissionError(
            "historical campaign.lock の environment contract を ever-active "
            "契約へ解決できない"
        ) from exc
    for record in records:
        if record.stage != STAGE_COMMIT:
            continue
        actual = record.payload.get(COMMIT_CONTRACT_SHA256_KEY)
        if actual != authority.environment_contract_sha256:
            raise ArtifactAdmissionError(
                "historical commit contract_sha256 が campaign.lock と不一致"
            )
        if record.env_tag != resolved.contract.env_tag:
            raise ArtifactAdmissionError(
                "historical commit env_tag が environment contract と不一致"
            )


def _inspect_campaign(
    campaign: CampaignLayout | str | Path, *,
    purpose: CampaignReadPurpose,
) -> tuple[
    CampaignAdmissionDecision,
    tuple[Any, ...],
    _RecordedCampaignVerifierEpoch | None,
]:
    _validate_read_purpose(purpose)
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
        ), tuple(records), None

    decoded = _decode_campaign_lock_for_purpose(lock_raw, purpose=purpose)
    recorded_epoch = _recorded_campaign_verifier_epoch(decoded)
    lock = decoded.identity
    search = lock["search_config"]
    if decoded.is_v2:
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
        ), tuple(records), recorded_epoch

    if truncated:
        raise ArtifactAdmissionError("post-policy campaign WAL has a truncated tail")
    if decoded.is_v2:
        policy = _build_admission_policy_for_purpose(
            search["build_admission"], purpose=purpose,
        )
    else:
        policy = _current_policy()
        if search["build_admission"] != policy.as_preimage():
            raise ArtifactAdmissionError("post-policy campaign lock admission policy differs")
    historical_policy_version = (
        decoded.is_v2 and purpose is CampaignReadPurpose.HISTORICAL_RAW
        and policy.as_preimage() != _current_policy().as_preimage()
    )
    validate_topology = wal._validate_attempt_topology
    if decoded.is_v2 and purpose is CampaignReadPurpose.HISTORICAL_RAW:
        validate_topology = wal._validate_historical_attempt_topology
    try:
        validate_topology(
            records,
            admission_policy=policy,
            campaign_lock=(
                decoded.identity
                if type(decoded) is campaign_lock.DecodedHistoricalCampaignLock
                else decoded
            ),
        )
        if (type(decoded) is campaign_lock.DecodedHistoricalCampaignLock
                and decoded.is_v2):
            _validate_historical_commit_contract_bindings(records, decoded)
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
        classification=(
            "historical-policy-version" if historical_policy_version else "admitted-new-schema"
        ),
        admission_status=(
            "historical-not-reclassified" if historical_policy_version else "admitted"
        ),
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
    ), tuple(records), recorded_epoch


def classify_campaign(
    campaign: CampaignLayout | str | Path,
) -> CampaignAdmissionDecision:
    """Classify exact campaign bytes without admitting a denied overlay record."""
    decision, _records, _epoch = _inspect_campaign(
        campaign, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    return decision


@overload
def require_admitted_campaign(
    campaign: CampaignLayout | str | Path, *,
    purpose: Literal[CampaignReadPurpose.CERTIFIED_ACCEPTANCE],
) -> CertifiedCampaignView: ...


@overload
def require_admitted_campaign(
    campaign: CampaignLayout | str | Path, *,
    purpose: Literal[CampaignReadPurpose.HISTORICAL_RAW],
) -> HistoricalCampaignView: ...


def _require_admitted_campaign(
    campaign: CampaignLayout | str | Path, *,
    purpose: CampaignReadPurpose,
    _replay_capability_issuer,
) -> CertifiedCampaignView | HistoricalCampaignView:
    """既存 admission 後に目的別 epoch gate を適用して非互換 view を返す。"""
    _validate_read_purpose(purpose)
    decision, records, recorded_epoch = _inspect_campaign(
        campaign, purpose=purpose,
    )
    if not decision.admitted:
        raise CampaignNotAdmitted(
            f"campaign is {decision.admission_status}: {decision.campaign_id}; "
            f"overlay={decision.overlay_ledger_sha256} "
            f"record={decision.overlay_record_key}"
        )
    if recorded_epoch is None:
        raise AssertionError("admitted campaign requires a recorded epoch")
    epoch = _require_verifier_epoch_for_purpose(recorded_epoch, purpose)
    if purpose is CampaignReadPurpose.CERTIFIED_ACCEPTANCE:
        persisted_certified_commit_count = admit_persisted_certified_commits(
            records,
            campaign_lock_sha256=decision.campaign_lock_sha256,
        )
    view_fields = {
        "layout": _layout(campaign),
        "records": _immutable_records(records),
        "decision": decision,
        "campaign_verifier_epoch": epoch,
    }
    if purpose is CampaignReadPurpose.CERTIFIED_ACCEPTANCE:
        replay_capability = _replay_capability_issuer(
            decision,
            view_fields["records"],
        )
        return CertifiedCampaignView(
            **view_fields, _certification_token=_CERTIFIED_VIEW_TOKEN,
            persisted_certified_commit_count=(
                persisted_certified_commit_count
            ),
            _replay_admission_capability=replay_capability,
        )
    return HistoricalCampaignView(**view_fields)


def _bind_require_admitted_campaign(replay_capability_issuer):
    def require_admitted_campaign(
        campaign: CampaignLayout | str | Path, *,
        purpose: CampaignReadPurpose,
    ) -> CertifiedCampaignView | HistoricalCampaignView:
        return _require_admitted_campaign(
            campaign,
            purpose=purpose,
            _replay_capability_issuer=replay_capability_issuer,
        )

    return require_admitted_campaign


require_admitted_campaign = _bind_require_admitted_campaign(
    _issue_replay_admission_capability,
)
del _bind_require_admitted_campaign
del _issue_replay_admission_capability


def require_certified_campaign_view(
        view: object,
) -> CertifiedCampaignView:
    """History 型を certified consumer 境界へ渡すことを exact 型で拒否する。"""
    if type(view) is not CertifiedCampaignView:
        raise TypeError("certified consumer requires exact CertifiedCampaignView")
    return view


def require_certified_commit_evidence(
        view: object,
) -> CertifiedCampaignView:
    """共通入口が投影した COMMIT 件数を exact view 上で非ゼロ要求する。

    件数は存在保証にだけ使い、各 commit が証拠検査を通ったことの独立した
    証拠とは扱わない。
    """
    certified_view = require_certified_campaign_view(view)
    if certified_view.persisted_certified_commit_count == 0:
        raise ArtifactAdmissionError(
            "certified commit evidence requires at least one persisted COMMIT"
        )
    return certified_view
