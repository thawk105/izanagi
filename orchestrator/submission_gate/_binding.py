"""preregistration の構造的整合性を束ねる private capability。

本 module は構造的整合性 (Git祖先関係・blob digest・approval manifest一致) だけを
検査する。投入可否・raw correctness・anomaly判定は行わない (それらは単位3 semantic
validator・単位4 attempt authorityの責務)。受領証とbindingのsnapshot一致検査はwriter
入口 (単位5) の責務であり、本 module は PreregBinding を要求する writer を持たない。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Final

from ._git import (
    GitSupportError,
    _COMMIT_RE,
    read_commit_blob,
    require_ancestor,
    require_exact_parent,
    resolve_head,
    require_git_repository,
)
from ._manifest import (
    ApprovedManifest,
    ErratumRef,
    ManifestError,
    PreregistrationRecord,
    _load_approved_manifest,
    _require_manifest_matches_approval,
)
from orchestrator.preregistration.blobref import BlobRef


_CAPABILITY_TOKEN: Final = object()


def _commit(value: object, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise GitSupportError(f"{label} は 40 桁 lowercase hex でなければならない")
    return value


def _root_identity(root: Path) -> tuple[int, int]:
    try:
        stat_result = root.stat()
    except OSError as exc:
        raise GitSupportError("repository root identity を取得できない") from exc
    return stat_result.st_dev, stat_result.st_ino


def _record_from_refs(
    approved: ApprovedManifest,
    *,
    core_ref: BlobRef,
    addendum_a: BlobRef,
    addendum_b: BlobRef | None,
) -> PreregistrationRecord:
    errata: list[ErratumRef] = []
    roles = {
        "t139-core-s15-exactkey-v1": "erratum_t139_core_s15_exactkey_v1",
        "t139-core-s7-stresscheck-v1": "erratum_t139_core_s7_stresscheck_v1",
    }
    for erratum_id in approved.erratum_application_order:
        ref = approved.approved_blobs.get(roles.get(erratum_id, ""))
        if ref is None:
            raise ManifestError(f"承認済み erratum が存在しない: {erratum_id}")
        errata.append(
            ErratumRef(
                erratum_id=erratum_id,
                path=ref.path,
                commit=ref.commit,
                sha256=ref.sha256,
                approval_fold_commit=approved.approval_ref.commit,
            )
        )
    return PreregistrationRecord(
        core=core_ref,
        addendum_a=addendum_a,
        addendum_b=addendum_b,
        fold_commit=approved.approval_ref.commit,
        errata=tuple(errata),
        approval_manifest=approved.approval_ref,
        receipt_schema=approved.approved_blobs["receipt_schema"],
        composed_core_sha256=approved.composed_sha256,
        prereg_commit=approved.prereg_commit,
    )


@dataclass(frozen=True, slots=True, init=False)
class _PreregBinding:
    """Opaque root-bound reference capability; no admission decision is made here."""

    record: PreregistrationRecord
    measurement_head: str
    prereg_commit: str
    prereg_content_commit: str
    prereg_effective_commit: str
    _root_identity: tuple[int, int]
    _seal: object = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        record: PreregistrationRecord,
        measurement_head: str,
        prereg_commit: str,
        prereg_content_commit: str,
        prereg_effective_commit: str,
        root_identity: tuple[int, int],
        token: object,
    ) -> None:
        if type(self) is not _PreregBinding or token is not _CAPABILITY_TOKEN:
            raise TypeError("_PreregBinding は内部 token からのみ発行される")
        if type(record) is not PreregistrationRecord:
            raise TypeError("record が PreregistrationRecord でない")
        if type(root_identity) is not tuple or len(root_identity) != 2 or any(
            type(item) is not int or item < 0 for item in root_identity
        ):
            raise TypeError("root identity が不正である")
        for label, value in (
            ("measurement_head", measurement_head),
            ("prereg_commit", prereg_commit),
            ("prereg_content_commit", prereg_content_commit),
            ("prereg_effective_commit", prereg_effective_commit),
        ):
            _commit(value, label)
        if prereg_commit != record.prereg_commit:
            raise TypeError("binding anchor が record と一致しない")
        if prereg_content_commit != record.core.commit:
            raise TypeError("binding content commit が core と一致しない")
        object.__setattr__(self, "record", record)
        object.__setattr__(self, "measurement_head", measurement_head)
        object.__setattr__(self, "prereg_commit", prereg_commit)
        object.__setattr__(self, "prereg_content_commit", prereg_content_commit)
        object.__setattr__(self, "prereg_effective_commit", prereg_effective_commit)
        object.__setattr__(self, "_root_identity", root_identity)
        object.__setattr__(self, "_seal", token)

    @classmethod
    def _issue(
        cls,
        *,
        record: PreregistrationRecord,
        measurement_head: str,
        prereg_commit: str,
        prereg_content_commit: str,
        prereg_effective_commit: str,
        root_identity: tuple[int, int],
        token: object,
    ) -> _PreregBinding:
        return cls(
            record=record,
            measurement_head=measurement_head,
            prereg_commit=prereg_commit,
            prereg_content_commit=prereg_content_commit,
            prereg_effective_commit=prereg_effective_commit,
            root_identity=root_identity,
            token=token,
        )

    def assert_intact(self, repository_root: str | os.PathLike[str]) -> None:
        """構造的な binding invariants を現在の checkout に対して再検査する。"""

        if type(self) is not _PreregBinding or self._seal is not _CAPABILITY_TOKEN:
            raise GitSupportError("preregistration capability の seal が不正である")
        root = require_git_repository(repository_root)
        if _root_identity(root) != self._root_identity:
            raise GitSupportError("repository root identity が binding 発行時から変わった")
        _commit(self.measurement_head, "measurement_head")
        _commit(self.prereg_commit, "prereg_commit")
        _commit(self.prereg_content_commit, "prereg_content_commit")
        _commit(self.prereg_effective_commit, "prereg_effective_commit")
        if self.prereg_commit != self.record.prereg_commit:
            raise GitSupportError("binding anchor が record と一致しない")
        if self.prereg_content_commit != self.record.core.commit:
            raise GitSupportError("binding content commit が core と一致しない")

        require_ancestor(
            root,
            ancestor=self.prereg_commit,
            descendant=self.prereg_content_commit,
        )
        read_commit_blob(
            root,
            commit=self.prereg_content_commit,
            path=self.record.core.path,
            expected_sha256=self.record.core.sha256,
        )
        read_commit_blob(
            root,
            commit=self.prereg_content_commit,
            path=self.record.addendum_a.path,
            expected_sha256=self.record.addendum_a.sha256,
        )
        if self.record.addendum_b is not None:
            read_commit_blob(
                root,
                commit=self.prereg_content_commit,
                path=self.record.addendum_b.path,
                expected_sha256=self.record.addendum_b.sha256,
            )
        require_exact_parent(
            root,
            content_commit=self.prereg_content_commit,
            effective_commit=self.prereg_effective_commit,
        )
        require_ancestor(
            root,
            ancestor=self.prereg_effective_commit,
            descendant=self.measurement_head,
        )
        current_head = resolve_head(root)
        if current_head != self.measurement_head:
            raise GitSupportError("measurement_head が現在の checkout HEAD と一致しない")


def _resolve_effective_preregistration(
    repository_root: str | os.PathLike[str],
    *,
    core_ref: BlobRef,
    addendum_a: BlobRef,
    addendum_b: BlobRef | None,
    prereg_effective_commit: str | None = None,
) -> _PreregBinding:
    """承認 view と refs から opaque binding を発行する内部入口。

    ``measurement_head`` は引数で受け取らず、必ず ``repository_root`` の実 checkout
    から導出する。effective commit を省略した互換的な内部呼出しでは addendum A の
    commit を候補にするが、発行時の exact-parent 検査を通らなければ拒否する。
    """

    if type(core_ref) is not BlobRef or type(addendum_a) is not BlobRef:
        raise ManifestError("core_ref/addendum_a は BlobRef でなければならない")
    if addendum_b is not None and type(addendum_b) is not BlobRef:
        raise ManifestError("addendum_b は BlobRef または None でなければならない")
    root = require_git_repository(repository_root)
    approved = _load_approved_manifest(os.fspath(root))
    record = _record_from_refs(
        approved,
        core_ref=core_ref,
        addendum_a=addendum_a,
        addendum_b=addendum_b,
    )
    _require_manifest_matches_approval(record, approved)
    measurement_head = resolve_head(root)
    effective = addendum_a.commit if prereg_effective_commit is None else prereg_effective_commit
    _commit(effective, "prereg_effective_commit")
    binding = _PreregBinding._issue(
        record=record,
        measurement_head=measurement_head,
        prereg_commit=record.prereg_commit,
        prereg_content_commit=record.core.commit,
        prereg_effective_commit=effective,
        root_identity=_root_identity(root),
        token=_CAPABILITY_TOKEN,
    )
    binding.assert_intact(root)
    return binding
