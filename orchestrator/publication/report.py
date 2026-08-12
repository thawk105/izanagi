"""D291 blob role の deny-only JSON report。"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .approval_d291 import (
    D291_FOLD_COMMIT,
    _D291RoleResolution,
    resolve_d291_approvals,
)


class D291ReportError(Exception):
    """HEAD decision scan または report 構築に失敗した。"""


@dataclass(frozen=True, slots=True)
class _SupersessionScan:
    """HEAD 上で D291 より後ろにある canonical supersession の走査結果。"""

    status: Literal["none_found", "possible_supersession"]
    decision_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ApprovalReport:
    """JSON 化前の deny-only D291 report。"""

    roles: tuple[tuple[str, _D291RoleResolution], ...]
    supersession_scan: _SupersessionScan


_DECISION_HEADING_RE = re.compile(r"^## (D([0-9]+))\.")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _outside_fences(lines: list[str]) -> tuple[bool, ...]:
    visible: list[bool] = []
    fence_character: str | None = None
    fence_width = 0
    for line in lines:
        if fence_character is not None:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_width},}}[ \t]*",
                line,
            )
            visible.append(False)
            if closing is not None:
                fence_character = None
                fence_width = 0
            continue
        opening = _FENCE_OPEN_RE.fullmatch(line)
        if opening is not None:
            marker, info = opening.groups()
            if marker[0] == "`" and "`" in info:
                visible.append(True)
                continue
            fence_character = marker[0]
            fence_width = len(marker)
            visible.append(False)
            continue
        visible.append(True)
    return tuple(visible)


def _scan_d291_supersession(decisions_blob: bytes) -> _SupersessionScan:
    """後続 decision にある D291 参照を fail-closed に列挙する。

    自然言語から supersession と単なる参照を完全には区別できないため、後続 decision
    section に ``D291`` が一度でも現れたら、現在も承認済みとは断言しない。
    """

    if not isinstance(decisions_blob, bytes):
        raise TypeError("decisions_blob は bytes でなければならない")
    try:
        lines = decisions_blob.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as exc:
        raise D291ReportError("HEAD docs/decisions.md が UTF-8 でない") from exc
    visible = _outside_fences(lines)
    headings: list[tuple[int, str, int]] = []
    for index, line in enumerate(lines):
        if not visible[index]:
            continue
        match = _DECISION_HEADING_RE.match(line)
        if match is not None:
            headings.append((index, match.group(1), int(match.group(2))))
    d291 = [item for item in headings if item[2] == 291]
    if len(d291) != 1:
        raise D291ReportError("HEAD に D291 heading が一意に存在しない")
    d291_start = d291[0][0]
    found: list[str] = []
    for position, (start, decision_id, _number) in enumerate(headings):
        if start <= d291_start:
            continue
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        section = "\n".join(lines[start:end])
        if "D291" in section:
            found.append(decision_id)
    return _SupersessionScan(
        status="possible_supersession" if found else "none_found",
        decision_ids=tuple(found),
    )


def _read_head_decisions(repository_root: str | os.PathLike[str]) -> bytes:
    try:
        root = Path(repository_root).resolve(strict=True)
    except OSError as exc:
        raise D291ReportError("repository_root を解決できない") from exc
    if not root.is_dir():
        raise D291ReportError("repository_root が directory でない")
    env = {
        key: value
        for key, value in os.environ.items()
        if key in {"LANG", "LC_ALL", "LC_CTYPE", "PATH", "SYSTEMROOT", "TMPDIR"}
    }
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    try:
        top = subprocess.run(
            [
                "git",
                "-c",
                "core.useReplaceRefs=false",
                "--no-replace-objects",
                "rev-parse",
                "--show-toplevel",
            ],
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )
        if top.returncode != 0:
            raise D291ReportError("repository_root が Git worktree でない")
        actual_root = Path(top.stdout.decode("utf-8", errors="strict").strip()).resolve(
            strict=True
        )
        if actual_root != root:
            raise D291ReportError("repository_root が Git top-level と一致しない")
        result = subprocess.run(
            [
                "git",
                "-c",
                "core.useReplaceRefs=false",
                "--no-replace-objects",
                "show",
                "HEAD:docs/decisions.md",
            ],
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise D291ReportError("HEAD docs/decisions.md の Git 解決に失敗した") from exc
    if result.returncode != 0:
        raise D291ReportError("HEAD に docs/decisions.md が存在しない")
    return result.stdout


def _build_approval_report(
    repository_root: str | os.PathLike[str],
) -> _ApprovalReport:
    """固定 F_p の role 状態と HEAD supersession scan を内部で結合する。"""

    resolutions = resolve_d291_approvals(repository_root)
    scan = _scan_d291_supersession(_read_head_decisions(repository_root))
    return _ApprovalReport(roles=tuple(resolutions.items()), supersession_scan=scan)


def _approval_report_to_dict(report: _ApprovalReport) -> dict[str, object]:
    """内部で構築済みの D291 report を決定的 JSON 用 dict へ写す。"""

    role_names = tuple(role for role, _ in report.roles)
    if role_names != ("publication_core", "source_addendum_b"):
        raise D291ReportError("report role 列が D291 の exact 2 roles と一致しない")
    superseded = report.supersession_scan.status != "none_found"
    roles: dict[str, object] = {}
    for role, resolution in report.roles:
        roles[role] = {
            "approval_status": (
                "not_asserted_after_supersession"
                if superseded
                else resolution.approval_status
            ),
            "d291_recorded_fact": "blob_role_approved_at_d291",
            "path": resolution.ref.path,
            "commit": resolution.ref.commit,
            "sha256": resolution.ref.sha256,
            "approval_authority": "canonical_decision_D291",
            "document_envelope_authority": resolution.document_envelope_authority,
            "submission_authority": "not_granted",
        }
    return {
        "decision": "D291",
        "trust_root_commit": D291_FOLD_COMMIT,
        "roles": roles,
        "authority_binding": {
            "canonical_source": "D291",
            "document_envelope_authority": "none",
            "document_bytes_rewritten": "no",
        },
        "supersession_scan": {
            "status": report.supersession_scan.status,
            "decision_ids": list(report.supersession_scan.decision_ids),
        },
        "submission_authority": "not_granted",
        "pilot_submission": "forbidden",
        "main_submission": "forbidden",
    }


def build_approval_report(
    repository_root: str | os.PathLike[str],
) -> dict[str, object]:
    """実 ``F_p`` と HEAD bytes から deny-only report dict を構築する。"""

    return _approval_report_to_dict(_build_approval_report(repository_root))


def approval_report_to_dict(
    repository_root: str | os.PathLike[str],
) -> dict[str, object]:
    """実 ``F_p`` と HEAD bytes から決定的 report dict を構築する。

    caller 作成の report object は受け取らず、公開経路では authority を注入できない。
    """

    return build_approval_report(repository_root)


def main(argv: Sequence[str] | None = None) -> int:
    """D291 deny-only report を stdout に決定的 JSON として出す。"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository_root", nargs="?", default=".")
    arguments = parser.parse_args(argv)
    report = approval_report_to_dict(arguments.repository_root)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
