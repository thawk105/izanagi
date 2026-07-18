# -*- coding: utf-8 -*-
"""永続出力 root policy と限定 write capability。

機械固有 path は shared code に固定せず、呼び手が ``Path`` tuple として注入する。
"""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Tuple


class DurableRootError(ValueError):
    """approved / forbidden root 契約の fail-closed 拒否。"""


@dataclass(frozen=True)
class DurableRootPolicy:
    """書込み可能 root と拒否 root の immutable policy 値。"""

    approved_roots: Tuple[Path, ...]
    forbidden_roots: Tuple[Path, ...]

    def __post_init__(self) -> None:
        if type(self.approved_roots) is not tuple or not self.approved_roots:
            raise DurableRootError("approved_roots は空でない tuple でなければならない")
        if type(self.forbidden_roots) is not tuple:
            raise DurableRootError("forbidden_roots は tuple でなければならない")
        for field, roots in (
            ("approved_roots", self.approved_roots),
            ("forbidden_roots", self.forbidden_roots),
        ):
            for index, root in enumerate(roots):
                if not isinstance(root, Path) or not root.is_absolute():
                    raise DurableRootError(f"{field}[{index}] は absolute Path でなければならない")
                if any(part == ".." for part in root.parts):
                    raise DurableRootError(f"{field}[{index}] は canonical path でなければならない")
            if len(set(roots)) != len(roots):
                raise DurableRootError(f"{field} に重複 root がある")


@dataclass(frozen=True)
class ApprovedRoot:
    """policy、realpath、mount ID の検査を通過した既存 directory。"""

    path: Path
    policy_root: Path
    st_dev: int
    st_ino: int

    def acquire_write_capability(self) -> "WriteCapability":
        """現在の identity を再確認して write capability を取得する。"""
        return WriteCapability.from_approved_root(self)

    def write_capability(self) -> "WriteCapability":
        """``acquire_write_capability`` の短い同義 API。"""
        return self.acquire_write_capability()


@dataclass(frozen=True, init=False)
class WriteCapability:
    """検査済み root 配下へ書く capability。

    root の FD は常時保持しない。``open_for_write`` は open 直前に root の
    ``st_dev/st_ino`` を再照合し leaf に ``O_NOFOLLOW`` を付けるが、その再照合と
    open の間にはなお小さな TOCTOU 窓が残る。これは FD 常時保持/openat 全面化を
    見送った現裁定の既知限界である。
    """

    root: Path
    st_dev: int
    st_ino: int

    def __init__(self, approved: ApprovedRoot) -> None:
        if not isinstance(approved, ApprovedRoot):
            raise DurableRootError("ApprovedRoot からのみ capability を取得できる")
        identity = _directory_identity(approved.path)
        if identity != (approved.st_dev, approved.st_ino):
            raise DurableRootError("ApprovedRoot の identity が capability 取得前に変化した")
        object.__setattr__(self, "root", approved.path)
        object.__setattr__(self, "st_dev", identity[0])
        object.__setattr__(self, "st_ino", identity[1])

    @classmethod
    def from_approved_root(cls, approved: ApprovedRoot) -> "WriteCapability":
        return cls(approved)

    def _verify_identity(self) -> None:
        if _directory_identity(self.root) != (self.st_dev, self.st_ino):
            raise DurableRootError("write capability の root identity が変化した")

    def open_for_write(self, relpath: str) -> BinaryIO:
        """root 内の相対 leaf を binary truncate-write で開く。"""
        if type(relpath) is not str or not relpath or "\x00" in relpath:
            raise DurableRootError("relpath は非空 str でなければならない")
        relative = Path(relpath)
        if relative.is_absolute() or relative == Path(".") or ".." in relative.parts:
            raise DurableRootError("relpath は root 内の相対 path でなければならない")
        try:
            parent = (self.root / relative.parent).resolve(strict=True)
        except OSError as exc:
            raise DurableRootError("relpath の親 directory を解決できない") from exc
        if not parent.is_relative_to(self.root) or not parent.is_dir():
            raise DurableRootError("relpath の親が capability root 外または directory でない")
        target = parent / relative.name
        nofollow = getattr(os, "O_NOFOLLOW", None)
        if nofollow is None:
            raise DurableRootError("O_NOFOLLOW が利用できない")

        # 裁定どおり open の直前に identity を再照合する。
        self._verify_identity()
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | nofollow
        try:
            fd = os.open(target, flags, 0o600)
        except OSError as exc:
            raise DurableRootError(f"write target を安全に open できない: {target}") from exc
        try:
            return os.fdopen(fd, "wb")
        except Exception:
            os.close(fd)
            raise


@dataclass(frozen=True)
class _MountEntry:
    mount_id: int
    mount_point: Path


_MOUNT_ESCAPE_RE = re.compile(r"\\([0-7]{3})")


def _unescape_mount_path(raw: str) -> str:
    return _MOUNT_ESCAPE_RE.sub(lambda match: chr(int(match.group(1), 8)), raw)


def _parse_mountinfo(text: str) -> tuple[_MountEntry, ...]:
    if type(text) is not str:
        raise DurableRootError("mountinfo_text は str でなければならない")
    entries = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        fields = line.split()
        try:
            separator = fields.index("-")
            if separator < 6:
                raise ValueError
            mount_id = int(fields[0], 10)
            mount_point = Path(_unescape_mount_path(fields[4]))
            if mount_id <= 0 or not mount_point.is_absolute():
                raise ValueError
        except (ValueError, IndexError) as exc:
            raise DurableRootError(f"mountinfo {line_number} 行目が不正") from exc
        entries.append(_MountEntry(mount_id=mount_id, mount_point=mount_point))
    if not entries:
        raise DurableRootError("mountinfo に mount entry がない")
    return tuple(entries)


def _mount_id_for(path: Path, entries: tuple[_MountEntry, ...]) -> int:
    candidates = [entry for entry in entries if path.is_relative_to(entry.mount_point)]
    if not candidates:
        raise DurableRootError(f"path を覆う mount entry がない: {path}")
    depth = max(len(entry.mount_point.parts) for entry in candidates)
    most_specific = [entry for entry in candidates if len(entry.mount_point.parts) == depth]
    ids = {entry.mount_id for entry in most_specific}
    if len(ids) != 1:
        raise DurableRootError(f"path の mount ID が一意に決まらない: {path}")
    return ids.pop()


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        info = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise DurableRootError(f"root identity を取得できない: {path}") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise DurableRootError(f"root は symlink でない directory でなければならない: {path}")
    return info.st_dev, info.st_ino


def _resolve_directory(path: Path, field: str, *, strict: bool) -> Path:
    try:
        resolved = path.resolve(strict=strict)
    except OSError as exc:
        raise DurableRootError(f"{field} の realpath を解決できない: {path}") from exc
    if strict and not resolved.is_dir():
        raise DurableRootError(f"{field} は既存 directory でなければならない: {resolved}")
    return resolved


def resolve_policy_root(
    policy: DurableRootPolicy,
    candidate: str,
    *,
    mountinfo_text: str | None = None,
) -> ApprovedRoot:
    """candidate を canonicalize し、root allowlist と mount 境界を検査する。"""
    if not isinstance(policy, DurableRootPolicy):
        raise DurableRootError("policy は DurableRootPolicy でなければならない")
    if type(candidate) is not str or not candidate:
        raise DurableRootError("candidate は非空 str でなければならない")
    candidate_path = _resolve_directory(Path(candidate), "candidate", strict=True)
    approved_roots = tuple(
        _resolve_directory(root, "approved_root", strict=True) for root in policy.approved_roots
    )
    matching = [root for root in approved_roots if candidate_path.is_relative_to(root)]
    if not matching:
        raise DurableRootError("candidate が approved root 配下でない")
    policy_root = max(matching, key=lambda root: len(root.parts))

    forbidden_roots = tuple(
        _resolve_directory(root, "forbidden_root", strict=False)
        for root in policy.forbidden_roots
    )
    if any(candidate_path.is_relative_to(root) for root in forbidden_roots):
        raise DurableRootError("candidate が forbidden root 配下")

    if mountinfo_text is None:
        try:
            with open("/proc/self/mountinfo", "r", encoding="utf-8") as stream:
                mountinfo_text = stream.read()
        except OSError as exc:
            raise DurableRootError("mountinfo を読み取れない") from exc
    entries = _parse_mountinfo(mountinfo_text)
    if _mount_id_for(policy_root, entries) != _mount_id_for(candidate_path, entries):
        raise DurableRootError("approved root から candidate まで mount ID を横断する")

    st_dev, st_ino = _directory_identity(candidate_path)
    return ApprovedRoot(
        path=candidate_path,
        policy_root=policy_root,
        st_dev=st_dev,
        st_ino=st_ino,
    )
