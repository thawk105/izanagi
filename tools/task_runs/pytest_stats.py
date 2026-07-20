"""Privacy-preserving pytest session statistics sidecar.

The sidecar contains aggregate counts and a short digest of the collected node
ID set.  Node IDs themselves never leave this process.  All public helpers are
designed to be called from fail-open pytest hooks.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Iterable, Mapping


SIDECAR_ENV = "IZANAGI_TASK_RUN_SIDECAR"
_SIDECAR_KEYS = frozenset({
    "collected", "passed", "failed", "skipped", "collected_node_digest",
})
_MAX_SIDECAR_BYTES = 4096
_SIDECAR_BASENAME = "pytest-stats.json"
_REPO = Path(__file__).resolve().parents[2]
_collected_node_ids: set[str] = set()


def _is_worker(config: Any) -> bool:
    return hasattr(config, "workerinput")


def note_collection(session: Any) -> None:
    """Remember locally collected IDs; xdist workers deliberately do nothing."""

    if _is_worker(session.config):
        return
    _collected_node_ids.update(str(item.nodeid) for item in session.items)


def note_xdist_collection(node: Any, ids: Iterable[str]) -> None:
    """Remember controller-observed xdist collection without retaining it on disk."""

    config = getattr(node, "config", None)
    if config is not None and _is_worker(config):
        return
    _collected_node_ids.update(str(node_id) for node_id in ids)


def _node_digest(node_ids: Iterable[str]) -> str:
    canonical = b"\0".join(
        node_id.encode("utf-8", errors="strict") for node_id in sorted(set(node_ids))
    )
    return hashlib.sha256(canonical).hexdigest()[:12]


def _count_stats(session: Any) -> dict[str, int | str | None]:
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return {
            "collected": int(session.testscollected),
            "passed": None,
            "failed": None,
            "skipped": None,
            "collected_node_digest": None,
        }

    stats = reporter.stats
    node_ids = set(_collected_node_ids)
    if not node_ids:
        for reports in stats.values():
            for report in reports:
                node_id = getattr(report, "nodeid", None)
                if isinstance(node_id, str):
                    node_ids.add(node_id)
    collected = int(session.testscollected)
    digest = _node_digest(node_ids) if node_ids or collected == 0 else None
    return {
        "collected": collected,
        "passed": len(stats.get("passed", ())),
        # pytest reports call failures as ``failed`` and setup/teardown errors
        # as ``error``.  The v1 failed count intentionally includes both.
        "failed": len(stats.get("failed", ())) + len(stats.get("error", ())),
        "skipped": len(stats.get("skipped", ())),
        "collected_node_digest": digest,
    }


def _create_sidecar(path: Path, payload: Mapping[str, object]) -> None:
    if not path.is_absolute():
        raise ValueError("sidecar path must be absolute")
    if path.name != _SIDECAR_BASENAME:
        raise ValueError("sidecar basename is not wrapper-owned")
    parent = path.parent
    parent_info = parent.lstat()
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        raise ValueError("sidecar parent must be a real directory")
    if parent_info.st_uid != os.getuid() or stat.S_IMODE(parent_info.st_mode) != 0o700:
        raise ValueError("sidecar parent must be owned by this uid with mode 0700")
    resolved_parent = parent.resolve(strict=True)
    repo = _REPO.resolve(strict=True)
    if resolved_parent == repo or repo in resolved_parent.parents:
        raise ValueError("sidecar parent must be outside the repository")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise OSError("O_NOFOLLOW unavailable")
    raw = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")
    if len(raw) > _MAX_SIDECAR_BYTES:
        raise ValueError("sidecar exceeds size limit")
    directory_flags = os.O_RDONLY | nofollow | getattr(os, "O_DIRECTORY", 0)
    directory_fd = os.open(parent, directory_flags)
    try:
        opened_parent = os.fstat(directory_fd)
        if (opened_parent.st_dev, opened_parent.st_ino) != (parent_info.st_dev, parent_info.st_ino):
            raise OSError("sidecar parent changed during validation")
        fd = os.open(path.name, flags | nofollow, 0o600, dir_fd=directory_fd)
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(raw)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("sidecar write made no progress")
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        os.close(directory_fd)


def write_session_stats(session: Any) -> None:
    """Controller-only create of the sidecar named by ``SIDECAR_ENV``."""

    value = os.environ.get(SIDECAR_ENV)
    if not value or _is_worker(session.config):
        return
    try:
        _create_sidecar(Path(value), _count_stats(session))
    except ValueError:
        # A path outside the wrapper-owned capability shape is an explicit no-op.
        return


def read_sidecar(path: Path) -> tuple[dict[str, int | None], str | None] | None:
    """Strictly read a sidecar; return ``None`` for absence or any corruption."""

    try:
        path = Path(path)
        if not path.is_absolute():
            return None
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return None
        if info.st_size <= 0 or info.st_size > _MAX_SIDECAR_BYTES:
            return None
        raw = path.read_bytes()
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            return None
        value = json.loads(raw.decode("ascii"))
        if not isinstance(value, dict) or set(value) != _SIDECAR_KEYS:
            return None
        counts: dict[str, int | None] = {}
        for name in ("collected", "passed", "failed", "skipped"):
            item = value[name]
            if item is not None and (
                isinstance(item, bool) or not isinstance(item, int) or item < 0
            ):
                return None
            counts[name] = item
        digest = value["collected_node_digest"]
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != 12
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            return None
        return counts, digest
    except Exception:
        return None
