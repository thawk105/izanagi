"""Decision fragment が ``approved_blobs:`` で承認する blob の marker gate。

この guard が拒否できるのは、``approved_blobs:`` 形式で path / commit /
sha256 の三つ組を宣言する fragment だけである。承認を散文だけで述べる
fragment は検査 target が空集合になり、この guard を素通りする。
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable

from orchestrator.preregistration.blobref import BlobRef, BlobRefError, read_pinned_blob


__all__ = (
    "ApprovalGuardError",
    "MalformedApprovedBlobRefError",
    "UNRESOLVED_APPROVAL_MARKERS",
    "UNRESOLVED_APPROVED_BLOB_REF_DIAGNOSTIC_CODE",
    "UnresolvedApprovalMarkerError",
    "require_resolved_approval_markers",
)


UNRESOLVED_APPROVAL_MARKERS = (
    b"__UNRESOLVED_APPROVAL_FOLD_COMMIT__",
    b"__UNRESOLVED__",
)
UNRESOLVED_APPROVED_BLOB_REF_DIAGNOSTIC_CODE = "unresolved-approved-blob-ref"

_APPROVED_BLOBS_HEADING_RE = re.compile(rb"^approved_blobs:[ \t]*$")
_ROLE_RE = re.compile(rb"^  (?P<role>[a-z][a-z0-9_]*):?[ \t]*$")
_FIELD_RE = re.compile(
    rb"^    (?P<field>path|commit|sha256)[ \t]*=[ \t]*(?P<value>\S+)[ \t]*$"
)
_LOGGER = logging.getLogger(__name__)


class ApprovalGuardError(Exception):
    """承認宣言または unresolved marker 検査に失敗した。"""

    code = "approval-guard-error"


class MalformedApprovedBlobRefError(ApprovalGuardError):
    """``approved_blobs:`` 内の role 宣言が壊れているか曖昧である。"""

    code = "malformed-approved-blob-ref"

    def __init__(self, role: str | None, line: int, reason: str) -> None:
        self.role = role
        self.line = line
        target = "approved_blobs" if role is None else f"approved_blobs.{role}"
        super().__init__(f"{target} の宣言が不正 (line {line}): {reason}")


class UnresolvedApprovalMarkerError(ApprovalGuardError):
    """承認対象として pin された blob が未確定 marker を含む。"""

    code = "unresolved-approval-marker"

    def __init__(self, role: str, marker: bytes) -> None:
        self.role = role
        self.marker = marker
        super().__init__(
            f"approved_blobs.{role} が未確定 marker {marker.decode('ascii')} を含む"
        )


def _approved_blob_refs(payload: bytes) -> tuple[tuple[str, BlobRef], ...]:
    lines = payload.splitlines()
    refs: list[tuple[str, BlobRef]] = []
    index = 0
    while index < len(lines):
        if _APPROVED_BLOBS_HEADING_RE.fullmatch(lines[index]) is None:
            index += 1
            continue
        index += 1
        role: str | None = None
        role_line = index + 1
        fields: dict[str, str] = {}
        seen_roles: set[str] = set()

        def finish_role() -> None:
            nonlocal role, role_line, fields
            if role is not None:
                required = {"path", "commit", "sha256"}
                if set(fields) != required:
                    missing = ", ".join(sorted(required - set(fields)))
                    raise MalformedApprovedBlobRefError(
                        role,
                        role_line,
                        f"path / commit / sha256 の三つ組が不足: {missing}",
                    )
                try:
                    ref = BlobRef(
                        path=fields["path"],
                        commit=fields["commit"],
                        sha256=fields["sha256"],
                    )
                except BlobRefError as exc:
                    raise MalformedApprovedBlobRefError(
                        role,
                        role_line,
                        f"三つ組の形が不正: {exc}",
                    ) from exc
                refs.append((role, ref))
            role = None
            fields = {}

        while index < len(lines):
            line = lines[index]
            if line and line[:1] not in {b" ", b"\t"}:
                break
            if not line.strip():
                index += 1
                continue
            role_match = _ROLE_RE.fullmatch(line)
            if role_match is not None:
                finish_role()
                role = role_match.group("role").decode("ascii")
                role_line = index + 1
                if role in seen_roles:
                    raise MalformedApprovedBlobRefError(
                        role,
                        role_line,
                        "同じ role が重複",
                    )
                seen_roles.add(role)
                index += 1
                continue
            field_match = _FIELD_RE.fullmatch(line)
            if field_match is not None:
                if role is None:
                    raise MalformedApprovedBlobRefError(
                        None,
                        index + 1,
                        "role より前に field がある",
                    )
                field = field_match.group("field").decode("ascii")
                if field in fields:
                    raise MalformedApprovedBlobRefError(
                        role,
                        index + 1,
                        f"field {field!r} が重複",
                    )
                try:
                    fields[field] = field_match.group("value").decode(
                        "utf-8", errors="strict"
                    )
                except UnicodeDecodeError as exc:
                    raise MalformedApprovedBlobRefError(
                        role,
                        index + 1,
                        f"field {field!r} が UTF-8 でない",
                    ) from exc
                index += 1
                continue
            raise MalformedApprovedBlobRefError(
                role,
                index + 1,
                "role または path / commit / sha256 field として解釈できない",
            )
        finish_role()
    return tuple(refs)


def require_resolved_approval_markers(
    repository_root: str | os.PathLike[str],
    decision_payloads: Iterable[bytes],
) -> None:
    """承認 payload が pin する blob に exact unresolved marker が無いことを課す。

    一般の「未確定」「未凍結」「draft」等は検査しない。成功値は返さず、構文が
    壊れた role または exact marker の検出時に例外で fold を止める。形が正しい
    pin の解決失敗は marker gate の拒否理由にせず、専用 code の logger 診断だけを
    残す。この保証は ``approved_blobs:`` の三つ組だけが対象で、散文だけの承認は
    対象が空になる。
    """

    for payload in decision_payloads:
        if not isinstance(payload, bytes):
            raise TypeError("decision_payloads の各要素は bytes でなければならない")
        for role, ref in _approved_blob_refs(payload):
            try:
                blob = read_pinned_blob(repository_root, ref)
            except BlobRefError as exc:
                _LOGGER.warning(
                    "[%s] approved_blobs.%s の固定 blob を解決できない: %s",
                    UNRESOLVED_APPROVED_BLOB_REF_DIAGNOSTIC_CODE,
                    role,
                    exc,
                )
                continue
            for marker in UNRESOLVED_APPROVAL_MARKERS:
                if marker in blob:
                    raise UnresolvedApprovalMarkerError(role, marker)
