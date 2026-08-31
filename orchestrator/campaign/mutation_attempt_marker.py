# -*- coding: utf-8 -*-
"""mutation task 内で鋳造する local attempt admission binding。"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from . import site_policy


MARKER_ENV = "IZANAGI_MUTATION_LOCAL_ATTEMPT_MARKER"
BINDING_SCHEMA = "izanagi-dev-wave-mutation-attempt-marker/v1"
COMPUTE_MARKER_NAME = "compute-visible.json"

_BINDING_FIELDS = frozenset(
    {
        "schema_version",
        "dispatch_root",
        "submission_dir",
        "pbs_jobid",
        "hostname",
        "request_sha256",
    }
)
_COMPUTE_MARKER_FIELDS = frozenset(
    {"schema_version", "pbs_jobid", "hostname"}
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class MutationAttemptMarkerError(RuntimeError):
    """local attempt marker の検証に失敗した。"""


def build_binding(
    *,
    dispatch_root: Path,
    submission_dir: Path,
    pbs_jobid: str,
    hostname: str,
    request_sha256: str,
    is_regular_pbs_jobid: Callable[[str], bool],
) -> dict[str, str]:
    """検査済み compute launcher が child へ渡す exact binding を作る。"""

    if not is_regular_pbs_jobid(pbs_jobid):
        raise MutationAttemptMarkerError("PBS job ID が不正です")
    if not isinstance(hostname, str) or not hostname:
        raise MutationAttemptMarkerError("hostname が空です")
    if _SHA256_RE.fullmatch(request_sha256) is None:
        raise MutationAttemptMarkerError("request SHA-256 が不正です")
    return {
        "schema_version": BINDING_SCHEMA,
        "dispatch_root": str(dispatch_root.resolve()),
        "submission_dir": str(submission_dir.resolve()),
        "pbs_jobid": pbs_jobid,
        "hostname": hostname,
        "request_sha256": request_sha256,
    }


def encode_binding(binding: Mapping[str, str]) -> str:
    """binding を環境変数用の canonical JSON にする。"""

    return json.dumps(
        dict(binding),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _require_exact_keys(
    value: dict[str, Any], expected: frozenset[str], label: str
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise MutationAttemptMarkerError(
            f"{label} の field 集合が不正です: missing={missing}, unknown={unknown}"
        )


def _read_regular_file(path: Path, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise MutationAttemptMarkerError(f"{label} の symlink 拒否を保証できません")
    try:
        descriptor = os.open(path, flags | nofollow)
    except OSError as exc:
        raise MutationAttemptMarkerError(
            f"{label} を安全に開けません: {exc}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise MutationAttemptMarkerError(f"{label} が通常 file ではありません")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(descriptor)
        stable = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        ) == (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
        )
        if total != before.st_size or not stable:
            raise MutationAttemptMarkerError(f"{label} が読取中に変化しました")
        return b"".join(chunks)
    except OSError as exc:
        raise MutationAttemptMarkerError(f"{label} を安全に読めません: {exc}") from exc
    finally:
        os.close(descriptor)


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    raw = _read_regular_file(path, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MutationAttemptMarkerError(
            f"{label} が正規 JSON ではありません"
        ) from exc
    if type(value) is not dict:
        raise MutationAttemptMarkerError(f"{label} root が object ではありません")
    return value


def _canonical_directory(value: Any, label: str) -> Path:
    if type(value) is not str or not value:
        raise MutationAttemptMarkerError(f"{label} が非空 string ではありません")
    path = Path(value)
    if not path.is_absolute():
        raise MutationAttemptMarkerError(f"{label} が絶対 path ではありません")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise MutationAttemptMarkerError(f"{label} を解決できません: {exc}") from exc
    if str(path) != str(resolved):
        raise MutationAttemptMarkerError(f"{label} が canonical path ではありません")
    if not resolved.is_dir():
        raise MutationAttemptMarkerError(f"{label} が directory ではありません")
    return resolved


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _first_label(hostname: str) -> str:
    normalized = hostname.lower().rstrip(".")
    return normalized.split(".", 1)[0] if normalized else ""


def require_local_attempt_marker(
    *,
    normalize_request_id: Callable[[str], str],
    is_regular_pbs_jobid: Callable[[str], bool],
) -> dict[str, Any]:
    """compute site と task 内 binding を検証し、検証した object 自体を返す。"""

    site = site_policy.current_site(require_evidence=True)
    if site != site_policy.PEGASUS_COMPUTE:
        raise MutationAttemptMarkerError(
            f"local attempt は Pegasus compute site でのみ許可されます: {site}"
        )

    encoded = os.environ.get(MARKER_ENV)
    if encoded is None:
        raise MutationAttemptMarkerError("mutation local attempt marker がありません")
    try:
        binding = json.loads(encoded)
    except json.JSONDecodeError as exc:
        raise MutationAttemptMarkerError(
            "mutation local attempt marker が正規 JSON ではありません"
        ) from exc
    if type(binding) is not dict:
        raise MutationAttemptMarkerError(
            "mutation local attempt marker root が object ではありません"
        )
    _require_exact_keys(binding, _BINDING_FIELDS, "mutation local attempt marker")
    if binding["schema_version"] != BINDING_SCHEMA:
        raise MutationAttemptMarkerError("mutation local attempt marker schema が不正です")
    for key in _BINDING_FIELDS - {"schema_version"}:
        if type(binding[key]) is not str or not binding[key]:
            raise MutationAttemptMarkerError(
                f"mutation local attempt marker.{key} が不正です"
            )
    if not is_regular_pbs_jobid(binding["pbs_jobid"]):
        raise MutationAttemptMarkerError(
            "mutation local attempt marker の PBS job ID が不正です"
        )
    if _SHA256_RE.fullmatch(binding["request_sha256"]) is None:
        raise MutationAttemptMarkerError(
            "mutation local attempt marker の request SHA-256 が不正です"
        )

    dispatch_root = _canonical_directory(binding["dispatch_root"], "dispatch root")
    submission_dir = _canonical_directory(binding["submission_dir"], "submission dir")
    if not _path_within(submission_dir, dispatch_root):
        raise MutationAttemptMarkerError("submission dir が canonical dispatch root の外です")

    request_path = submission_dir / "request.json"
    compute_marker_path = submission_dir / COMPUTE_MARKER_NAME
    request_bytes = _read_regular_file(request_path, "request.json")
    compute_marker = _read_json_object(compute_marker_path, COMPUTE_MARKER_NAME)
    _require_exact_keys(compute_marker, _COMPUTE_MARKER_FIELDS, COMPUTE_MARKER_NAME)
    if compute_marker["schema_version"] != "pegasus-compute-visible/v1":
        raise MutationAttemptMarkerError("compute-visible.json schema が不正です")
    if type(compute_marker["pbs_jobid"]) is not str or not is_regular_pbs_jobid(
        compute_marker["pbs_jobid"]
    ):
        raise MutationAttemptMarkerError("compute-visible.json の PBS job ID が不正です")
    if (
        type(compute_marker["hostname"]) is not str
        or not compute_marker["hostname"]
    ):
        raise MutationAttemptMarkerError("compute-visible.json の hostname が不正です")
    if normalize_request_id(binding["pbs_jobid"]) != normalize_request_id(
        compute_marker["pbs_jobid"]
    ):
        raise MutationAttemptMarkerError("PBS job ID が compute-visible.json と不一致です")
    if binding["hostname"] != compute_marker["hostname"]:
        raise MutationAttemptMarkerError("hostname が compute-visible.json と不一致です")
    try:
        current_hostname = socket.gethostname()
    except Exception as exc:
        raise MutationAttemptMarkerError("現在の hostname を取得できません") from exc
    if _first_label(binding["hostname"]) != _first_label(current_hostname):
        raise MutationAttemptMarkerError("hostname が現在の compute node と不一致です")
    if hashlib.sha256(request_bytes).hexdigest() != binding["request_sha256"]:
        raise MutationAttemptMarkerError("request.json SHA-256 が marker と不一致です")
    return binding
