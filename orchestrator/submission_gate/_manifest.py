"""承認済み preregistration manifest の immutable view。

ここで扱う値は approval payload と受領証の shape を固定するための view であり、
投入可否や raw correctness を判定する admission API ではない。anchor commit は
payload から供給され、manifest blob 自身が自分の commit を申告して決めることはない。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import Final

from orchestrator.preregistration.approval_payload import (
    APPROVED_BLOB_ROLES,
    APPROVED_ERRATUM_ORDER,
    D282_DECISIONS_REF,
    load_approval_payload,
)
from orchestrator.preregistration.blobref import BlobRef, InvalidBlobRefError


_COMMIT_RE: Final = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_ERRATUM_ID_RE: Final = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_ERRATUM_ROLE: Final = {
    "t139-core-s15-exactkey-v1": "erratum_t139_core_s15_exactkey_v1",
    "t139-core-s7-stresscheck-v1": "erratum_t139_core_s7_stresscheck_v1",
}
_MANIFEST_CAPABILITY_TOKEN: Final = object()


class ManifestError(ValueError):
    """manifest または approval view の構造が不正である。"""


def _commit(value: object, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise ManifestError(f"{label} は 40 桁 lowercase hex でなければならない")
    return value


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ManifestError(f"{label} は 64 桁 lowercase hex でなければならない")
    return value


def _blob_ref(value: object, label: str) -> BlobRef:
    if not isinstance(value, BlobRef) or type(value) is not BlobRef:
        raise ManifestError(f"{label} は BlobRef でなければならない")
    return value


def _same_blob(left: BlobRef, right: BlobRef, *, include_commit: bool = False) -> bool:
    if include_commit:
        return left == right
    return left.path == right.path and left.sha256 == right.sha256


@dataclass(frozen=True, slots=True)
class ErratumRef:
    """承認順序へ束縛された erratum の三つ組。"""

    erratum_id: str
    path: str
    commit: str
    sha256: str
    approval_fold_commit: str

    def __post_init__(self) -> None:
        if (
            type(self.erratum_id) is not str
            or _ERRATUM_ID_RE.fullmatch(self.erratum_id) is None
        ):
            raise ManifestError("erratum_id の形式が不正である")
        try:
            ref = BlobRef(path=self.path, commit=self.commit, sha256=self.sha256)
        except InvalidBlobRefError as exc:
            raise ManifestError("erratum の blob ref が不正である") from exc
        object.__setattr__(self, "path", ref.path)
        object.__setattr__(self, "commit", ref.commit)
        object.__setattr__(self, "sha256", ref.sha256)
        object.__setattr__(
            self,
            "approval_fold_commit",
            _commit(self.approval_fold_commit, "approval_fold_commit"),
        )


@dataclass(frozen=True, slots=True)
class PreregistrationRecord:
    """受領証の preregistration object を不変値として表す。"""

    core: BlobRef
    addendum_a: BlobRef
    addendum_b: BlobRef | None
    fold_commit: str
    errata: tuple[ErratumRef, ...]
    approval_manifest: BlobRef
    receipt_schema: BlobRef
    composed_core_sha256: str
    prereg_commit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "core", _blob_ref(self.core, "core"))
        object.__setattr__(self, "addendum_a", _blob_ref(self.addendum_a, "addendum_a"))
        if self.addendum_b is not None:
            object.__setattr__(self, "addendum_b", _blob_ref(self.addendum_b, "addendum_b"))
        object.__setattr__(self, "fold_commit", _commit(self.fold_commit, "fold_commit"))
        if (
            type(self.errata) is not tuple
            or not self.errata
            or not all(type(item) is ErratumRef for item in self.errata)
        ):
            raise ManifestError(
                "errata は 1 件以上の ErratumRef の tuple でなければならない"
            )
        ids = tuple(item.erratum_id for item in self.errata)
        if len(set(ids)) != len(ids):
            raise ManifestError("errata の erratum_id が重複している")
        object.__setattr__(
            self,
            "approval_manifest",
            _blob_ref(self.approval_manifest, "approval_manifest"),
        )
        object.__setattr__(self, "receipt_schema", _blob_ref(self.receipt_schema, "receipt_schema"))
        object.__setattr__(
            self,
            "composed_core_sha256",
            _sha256(self.composed_core_sha256, "composed_core_sha256"),
        )
        object.__setattr__(self, "prereg_commit", _commit(self.prereg_commit, "prereg_commit"))


@dataclass(frozen=True, slots=True, init=False)
class ApprovedManifest:
    """D282 approval payload に束縛された opaque capability。"""

    approval_ref: BlobRef
    target_core: BlobRef
    approved_blobs: Mapping[str, BlobRef]
    erratum_application_order: tuple[str, ...]
    composed_sha256: str
    prereg_commit: str | None = None
    _seal: object = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        token: object,
        approval_ref: BlobRef,
        target_core: BlobRef,
        approved_blobs: Mapping[str, BlobRef],
        erratum_application_order: tuple[str, ...],
        composed_sha256: str,
        prereg_commit: str | None = None,
    ) -> None:
        if type(self) is not ApprovedManifest or token is not _MANIFEST_CAPABILITY_TOKEN:
            raise TypeError("ApprovedManifest は内部 token からのみ発行される")
        object.__setattr__(self, "approval_ref", approval_ref)
        object.__setattr__(self, "target_core", target_core)
        object.__setattr__(self, "approved_blobs", approved_blobs)
        object.__setattr__(self, "erratum_application_order", erratum_application_order)
        object.__setattr__(self, "composed_sha256", composed_sha256)
        object.__setattr__(self, "prereg_commit", prereg_commit)
        object.__setattr__(self, "_seal", token)
        self.__post_init__()

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_ref", _blob_ref(self.approval_ref, "approval_ref"))
        object.__setattr__(self, "target_core", _blob_ref(self.target_core, "target_core"))
        if not isinstance(self.approved_blobs, Mapping):
            raise ManifestError("approved_blobs は Mapping でなければならない")
        copied = dict(self.approved_blobs)
        if set(copied) != APPROVED_BLOB_ROLES:
            raise ManifestError("approved_blobs の role 集合が承認値と一致しない")
        if any(type(key) is not str or type(value) is not BlobRef for key, value in copied.items()):
            raise ManifestError("approved_blobs の role/ref が不正である")
        object.__setattr__(self, "approved_blobs", MappingProxyType(copied))
        if type(self.erratum_application_order) is not tuple or any(
            type(item) is not str or not item for item in self.erratum_application_order
        ):
            raise ManifestError("erratum_application_order が不正である")
        if len(set(self.erratum_application_order)) != len(self.erratum_application_order):
            raise ManifestError("erratum_application_order が重複している")
        if self.erratum_application_order != APPROVED_ERRATUM_ORDER:
            raise ManifestError("erratum_application_order が承認順序と一致しない")
        object.__setattr__(
            self,
            "composed_sha256",
            _sha256(self.composed_sha256, "composed_sha256"),
        )
        anchor = self.approval_ref.commit if self.prereg_commit is None else self.prereg_commit
        object.__setattr__(self, "prereg_commit", _commit(anchor, "prereg_commit"))


def _is_sealed_approved_manifest(value: object) -> bool:
    return (
        type(value) is ApprovedManifest
        and getattr(value, "_seal", None) is _MANIFEST_CAPABILITY_TOKEN
    )


def _load_approved_manifest(repository_root: str) -> ApprovedManifest:
    """固定した approval payload から承認済み view を構築する。

    approval payload を含む固定 approval ref の commit が anchor である。作業木の
    manifest が自分の commit を自己申告する経路はここにはない。将来の payload が
    明示的な anchor field を持つ場合は、その approval 値を優先する。
    """

    payload = load_approval_payload(repository_root)
    explicit_anchor = getattr(payload, "prereg_commit", D282_DECISIONS_REF.commit)
    return ApprovedManifest(
        token=_MANIFEST_CAPABILITY_TOKEN,
        approval_ref=D282_DECISIONS_REF,
        target_core=payload.target_core,
        approved_blobs=payload.approved_blobs,
        erratum_application_order=payload.erratum_application_order,
        composed_sha256=payload.composed_sha256,
        prereg_commit=explicit_anchor,
    )


def _parse_blob_ref(value: object, label: str) -> BlobRef:
    if isinstance(value, BlobRef):
        return _blob_ref(value, label)
    if not isinstance(value, Mapping) or set(value) != {"path", "commit", "sha256"}:
        raise ManifestError(f"{label} の三つ組が不正である")
    try:
        return BlobRef(path=value["path"], commit=value["commit"], sha256=value["sha256"])
    except (InvalidBlobRefError, KeyError, TypeError, ValueError) as exc:
        raise ManifestError(f"{label} の三つ組が不正である") from exc


def _parse_erratum(value: object, index: int) -> ErratumRef:
    label = f"errata[{index}]"
    if not isinstance(value, Mapping) or set(value) != {
        "erratum_id", "path", "commit", "sha256", "approval_fold_commit"
    }:
        raise ManifestError(f"{label} の key 集合が不正である")
    try:
        return ErratumRef(
            erratum_id=value["erratum_id"],
            path=value["path"],
            commit=value["commit"],
            sha256=value["sha256"],
            approval_fold_commit=value["approval_fold_commit"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ManifestError(f"{label} が不正である") from exc


def _parse_preregistration_record(
    value: Mapping[str, object],
) -> PreregistrationRecord:
    """受領証の preregistration object を exact-key で不変 record にする。"""

    expected = {
        "core",
        "addendum_a",
        "addendum_b",
        "fold_commit",
        "errata",
        "approval_manifest",
        "receipt_schema",
        "composed_core_sha256",
        "prereg_commit",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        actual = sorted(value) if isinstance(value, Mapping) else type(value).__name__
        raise ManifestError(f"preregistration key 集合が不正である: {actual!r}")
    errata_value = value["errata"]
    if not isinstance(errata_value, (list, tuple)):
        raise ManifestError("errata は sequence でなければならない")
    return PreregistrationRecord(
        core=_parse_blob_ref(value["core"], "core"),
        addendum_a=_parse_blob_ref(value["addendum_a"], "addendum_a"),
        addendum_b=(
            None
            if value["addendum_b"] is None
            else _parse_blob_ref(value["addendum_b"], "addendum_b")
        ),
        fold_commit=value["fold_commit"],
        errata=tuple(_parse_erratum(item, index) for index, item in enumerate(errata_value)),
        approval_manifest=_parse_blob_ref(value["approval_manifest"], "approval_manifest"),
        receipt_schema=_parse_blob_ref(value["receipt_schema"], "receipt_schema"),
        composed_core_sha256=value["composed_core_sha256"],
        prereg_commit=value["prereg_commit"],
    )


def _require_manifest_matches_approval(
    record: PreregistrationRecord,
    approved: ApprovedManifest,
) -> None:
    """record が固定 approval view の閉集合と一致することを検査する。"""

    if type(record) is not PreregistrationRecord or not _is_sealed_approved_manifest(approved):
        raise ManifestError("manifest view の型が不正である")
    if record.prereg_commit != approved.prereg_commit:
        raise ManifestError("prereg_commit が approval anchor と一致しない")
    if not _same_blob(record.approval_manifest, approved.approval_ref, include_commit=True):
        raise ManifestError("approval_manifest が approval payload と一致しない")
    if not _same_blob(record.core, approved.target_core):
        raise ManifestError("core の path/digest が承認済み target_core と一致しない")
    if "addendum_a" not in approved.approved_blobs:
        raise ManifestError("承認済み addendum_a が存在しない")
    if not _same_blob(record.addendum_a, approved.approved_blobs["addendum_a"]):
        raise ManifestError("addendum_a の path/digest が承認値と一致しない")
    if "addendum_b" in approved.approved_blobs:
        if record.addendum_b is None or not _same_blob(
            record.addendum_b, approved.approved_blobs["addendum_b"]
        ):
            raise ManifestError("addendum_b が承認値と一致しない")
    elif record.addendum_b is not None:
        raise ManifestError("未承認の addendum_b がある")
    if "receipt_schema" not in approved.approved_blobs or not _same_blob(
        record.receipt_schema, approved.approved_blobs["receipt_schema"]
    ):
        raise ManifestError("receipt_schema が承認値と一致しない")
    if record.composed_core_sha256 != approved.composed_sha256:
        raise ManifestError("composed_core_sha256 が承認値と一致しない")
    if record.fold_commit != approved.approval_ref.commit:
        raise ManifestError("fold_commit が approval fold commit と一致しない")

    if tuple(item.erratum_id for item in record.errata) != approved.erratum_application_order:
        raise ManifestError("errata の承認順序が一致しない")
    for item in record.errata:
        role = _ERRATUM_ROLE.get(item.erratum_id)
        if role is None or role not in approved.approved_blobs:
            raise ManifestError(f"erratum の承認 role が存在しない: {item.erratum_id}")
        expected = approved.approved_blobs[role]
        if not _same_blob(
            BlobRef(path=item.path, commit=item.commit, sha256=item.sha256), expected
        ) or item.approval_fold_commit != approved.approval_ref.commit:
            raise ManifestError(f"erratum が承認値と一致しない: {item.erratum_id}")
