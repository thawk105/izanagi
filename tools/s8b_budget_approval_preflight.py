#!/usr/bin/env python3
"""S8B budget approval の非権威な骨組み作成と read-only 検証を行う。"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.campaign import s8b_holdout_freeze as _freeze  # noqa: E402


class PreflightError(RuntimeError):
    """Preflight が安全に完了できないときの利用者向けエラー。"""


def _absolute_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("絶対 path を指定すること")
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    skeleton = commands.add_parser(
        "skeleton",
        help="承認ではない骨組みを repo 外へ create-only で書く",
    )
    skeleton.add_argument(
        "--out", required=True, type=_absolute_path, metavar="ABSOLUTE_PATH",
    )

    verify = commands.add_parser(
        "verify",
        help="人間が作成した candidate を read-only で検証する",
    )
    verify.add_argument("--candidate", required=True, type=Path, metavar="PATH")
    return parser


def _normalized_absolute(path: Path) -> Path:
    return Path(os.path.normpath(os.fspath(path)))


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _open_parent_nofollow(path: Path) -> int:
    """絶対 path の parent を symlink component を辿らず directory fd で開く。"""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise PreflightError("O_NOFOLLOW が利用できない")
    flags = (
        os.O_RDONLY | os.O_DIRECTORY | nofollow | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(os.sep, flags)
    try:
        for component in path.parent.parts[1:]:
            if not component:
                continue
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _same_regular_leaf(parent_fd: int, name: str, identity: os.stat_result) -> bool:
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(current.st_mode)
        and (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino)
    )


def _write_create_only_outside_repo(path: Path, raw: bytes) -> None:
    normalized = _normalized_absolute(path)
    repo_root = _REPO_ROOT.resolve()
    if _is_within(normalized, repo_root):
        raise PreflightError("--out は repository の外を指定すること")
    if normalized.name in {"", os.curdir, os.pardir}:
        raise PreflightError("--out の leaf が不正")

    parent_fd = -1
    descriptor = -1
    created_identity: os.stat_result | None = None
    try:
        parent_fd = _open_parent_nofollow(normalized)
        flags = (
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(normalized.name, flags, 0o600, dir_fd=parent_fd)
        created_identity = os.fstat(descriptor)
        if not stat.S_ISREG(created_identity.st_mode):
            raise PreflightError("--out を regular file として作れない")
        offset = 0
        while offset < len(raw):
            try:
                written = os.write(descriptor, raw[offset:])
            except InterruptedError:
                continue
            if written <= 0:
                raise PreflightError("skeleton の書き込みが進捗しない")
            offset += written
        os.fsync(descriptor)
        if not _same_regular_leaf(parent_fd, normalized.name, created_identity):
            raise PreflightError("--out leaf が作成中に置換された")
        os.close(descriptor)
        descriptor = -1
        os.fsync(parent_fd)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
            descriptor = -1
        if (
            parent_fd >= 0
            and created_identity is not None
            and _same_regular_leaf(parent_fd, normalized.name, created_identity)
        ):
            try:
                os.unlink(normalized.name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            except OSError:
                pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if parent_fd >= 0:
            os.close(parent_fd)


def _skeleton_bytes() -> bytes:
    document = {
        "required_fields": sorted(_freeze.BUDGET_APPROVAL_KEYS - {"scope"}),
        "scope": _freeze.BUDGET_APPROVAL_SCOPE,
        "status": "draft-not-an-approval",
    }
    return _freeze._canonical_bytes(document)


def _active_v1_holdout_ids() -> tuple[str, ...]:
    raw = _freeze._capture_regular_nofollow(
        _REPO_ROOT / _freeze.FREEZE_REL, label="active v1 freeze",
    )
    if (
        hashlib.sha256(raw).hexdigest()
        != _freeze.t080_freeze_migration.HOLDOUT_RAW_SHA256
    ):
        raise _freeze.FreezeError("active v1 freeze が T-080 固定 hash と不一致")
    document = _freeze._strict_load_object_bytes(raw, "active v1 freeze")
    if set(document) != _freeze.TOP_LEVEL_KEYS:
        raise _freeze.FreezeError("active v1 freeze の top-level schema が不一致")
    holdouts = document.get("holdouts")
    if not isinstance(holdouts, Mapping) or set(holdouts) != set(_freeze.HOLDOUTS):
        raise _freeze.FreezeError("active v1 freeze の holdout 集合が不一致")
    return tuple(sorted(holdouts))


def _verify_candidate(path: Path) -> str:
    raw = _freeze._capture_regular_nofollow(path, label="budget approval candidate")
    approval = _freeze._strict_load_object_bytes(raw, "budget approval candidate")
    if frozenset(approval) != _freeze.BUDGET_APPROVAL_KEYS:
        raise _freeze.FreezeError("budget approval の key 集合が不一致")
    if _freeze._canonical_bytes(approval) != raw:
        raise _freeze.FreezeError("budget approval raw bytes が canonical JSON でない")
    if approval.get("scope") != _freeze.BUDGET_APPROVAL_SCOPE:
        raise _freeze.FreezeError("budget approval.scope が固定値と不一致")
    approver = approval.get("approver")
    if not isinstance(approver, str) or not approver.strip():
        raise _freeze.FreezeError("budget approval.approver が空")
    approved_at = approval.get("approved_at")
    if not isinstance(approved_at, str):
        raise _freeze.FreezeError("budget approval.approved_at が UTC timestamp でない")
    try:
        parsed = dt.datetime.strptime(approved_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise _freeze.FreezeError(
            "budget approval.approved_at が UTC timestamp でない"
        ) from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != approved_at:
        raise _freeze.FreezeError(
            "budget approval.approved_at が canonical UTC timestamp でない"
        )
    _freeze._validate_budget(
        approval.get("budget"),
        holdout_ids=_active_v1_holdout_ids(),
        label="budget approval.budget",
    )
    return hashlib.sha256(raw).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "skeleton":
            _write_create_only_outside_repo(args.out, _skeleton_bytes())
            print(f"created non-approval skeleton: {_normalized_absolute(args.out)}")
            return 0

        raw_sha256 = _verify_candidate(args.candidate)
        print(f"raw_sha256={raw_sha256}")
        print(f'BUDGET_APPROVAL_SHA256: Optional[str] = "{raw_sha256}"')
        return 0
    except (_freeze.FreezeError, PreflightError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
