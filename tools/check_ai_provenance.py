#!/usr/bin/env python3
"""AI 作業 provenance の commit trailer を決定的に監査する。

既定では docs/ai-provenance.md の一意な追加 commit と、起動時に固定した HEAD へ到達する
その後の commit を検査する。
任意範囲は --range、commit 前の message は --message-file で検査できる。
hook には配線しない。Izanagi の hook 2 本限定を維持しつつ、欠落を明示的に監査するための
独立した lint である。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import re
import secrets
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_KNOWN_VIOLATION_REPO_ROOT = Path(__file__).resolve().parent.parent
_KNOWN_VIOLATION_RELATIVE_DIRECTORY = Path("tools/known_violations")
_KNOWN_VIOLATION_DIRECTORY = (
    _KNOWN_VIOLATION_REPO_ROOT / _KNOWN_VIOLATION_RELATIVE_DIRECTORY
)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.campaign import site_policy  # noqa: E402

POLICY_PATH = "docs/ai-provenance.md"
# tools/run_tests.py:110 の _PEGASUS_DISPATCH_RC と同値 (meta-test で照合する)。
PEGASUS_DISPATCH_RC = 16
_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV = (
    "IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE"
)
_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV = (
    "IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE"
)
_BOUNDED_SCOPE_UNIT_ENV = "IZANAGI_PROVENANCE_SCOPE_UNIT"
_BOUNDED_SCOPE_CAP_ENV = "IZANAGI_PROVENANCE_SCOPE_CAP"
_BOUNDED_SCOPE_UNIT_PREFIX = "izanagi-provenance-"
_CGROUP_ROOT = Path("/sys/fs/cgroup")
_PROC_SELF_CGROUP = Path("/proc/self/cgroup")
_SCOPE_POLL_SECONDS = 0.005
_SCOPE_ATTEST_SECONDS = 1.0
_SCOPE_DRAIN_SECONDS = 0.1
_HEADROOM_SHORT = "headroom_short"
# insight §11 で 32→48 は改善ゼロ。git subprocess の fork/exec が律速なので開けない。
AUDIT_WORKERS_CAP = 32
ROLES = ("author", "reviewer", "researcher", "manager", "integrator")
IDENT = r"[a-z0-9][a-z0-9._-]*"
RESERVED_PRODUCTS = {"none", "unknown", "not-exposed", "human"}
IMPLEMENTATION_POLICY_NEEDLE = (
    "実装面を変更する AI 関与 commit は Codex author を必須"
)
CO_AUTHORED_BY_POLICY_NEEDLE = (
    "Co-Authored-By 候補行はすべて最終 trailer block に置く"
)
IMPLEMENTATION_PREFIXES = (
    "orchestrator/", "tools/", "hooks/", ".github/", ".codex/", "external/",
)
IMPLEMENTATION_SUFFIXES = (
    ".py", ".sh", ".bash", ".c", ".cc", ".cpp", ".cxx",
    ".h", ".hh", ".hpp", ".hxx", ".cmake", ".patch", ".diff",
)
# pytest.ini は repo 直下にあり prefix/suffix のどちらにも当たらないが、受入全走の
# 収集集合を決める制御ファイルなので実装面として扱う (段 4 裁定 M8)。
IMPLEMENTATION_BASENAMES = {
    "CMakeLists.txt", "Makefile", "GNUmakefile", "pyproject.toml", "pytest.ini",
}
AGENT_VALUE = re.compile(
    rf"^product=(?P<product>{IDENT}); "
    rf"model=(?P<model>{IDENT}); "
    rf"reasoning=(?P<reasoning>{IDENT}); "
    rf"role=(?P<role>{'|'.join(ROLES)})"
    rf"(?:; scope=(?P<scope>{IDENT}))?$"
)
RAW_CO_AUTHORED_BY = re.compile(
    r"^[ \t]*Co-Authored-By[ \t]*:", re.IGNORECASE | re.MULTILINE
)
CORRECTION_KEY = "AI-Agent-Correction"
RAW_AI_AGENT_CORRECTION = re.compile(
    rf"^[ \t]*{re.escape(CORRECTION_KEY)}[ \t]*:"
    r"(?P<value>[^\r\n]*)\r?$",
    re.IGNORECASE | re.MULTILINE,
)
WAIVER_KEY = "AI-Agent-Waiver"
RAW_AI_AGENT_WAIVER = re.compile(
    rf"^[ \t]*{re.escape(WAIVER_KEY)}[ \t]*:"
    r"(?P<value>[^\r\n]*)\r?$",
    re.IGNORECASE | re.MULTILINE,
)
WAIVER_VALUE = re.compile(
    rf"^reason=(?P<reason>{IDENT}); "
    r"ratified=(?P<ratified>\d{4}-\d{2}-\d{2})$"
)
# docs/ai-provenance.md の逐語と一致させる (exactly-once メタテストで照合する)。
WAIVER_POLICY_LITERAL = "AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>"
TRAILER_PARSE_TEMP_ROOT: Path | None = None
_REPO_DISCOVERY_ENV = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_WORK_TREE",
}


def _repo_discovery_isolated_env() -> dict[str, str]:
    """ambient repository discovery override を除いた subprocess 環境。"""
    return {
        key: value for key, value in os.environ.items()
        if key not in _REPO_DISCOVERY_ENV
    }


@dataclass(frozen=True)
class ForwardCorrectionSpec:
    """一回限りの incident 固有 correction。一般 registry へ拡張しない。"""

    target: str

    @property
    def payload(self) -> str:
        return (
            f"target={self.target}; product=claude; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator"
        )


INCIDENT_6B64D21_FORWARD_CORRECTION = ForwardCorrectionSpec(
    target="6b64d21753d2cfc790f80caba29df7a40fef3072",
)


MISSING_AI_AGENT = "missing-ai-agent"
MISSING_CODEX_AUTHOR = "missing-codex-author"
MALFORMED_AI_AGENT = "malformed-ai-agent"
_LEDGER_FINDING_KINDS = frozenset({
    MISSING_AI_AGENT,
    MISSING_CODEX_AUTHOR,
    MALFORMED_AI_AGENT,
})
_NOTE_REQUIRED_FINDING_KINDS = frozenset({MALFORMED_AI_AGENT})
_ZERO_WIDTH_REGISTRY_CHARACTERS = frozenset("\u200b\u200c\u200d\ufeff")
_PROHIBITED_REGISTRY_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})
_DESCRIPTIVE_NOTE_CATEGORY_PREFIXES = frozenset({"L", "N", "P", "S"})
_NON_DESCRIPTIVE_NOTE_CHARACTERS = frozenset({
    "\u034f",  # COMBINING GRAPHEME JOINER
    "\u115f",  # HANGUL CHOSEONG FILLER
    "\u1160",  # HANGUL JUNGSEONG FILLER
    "\u17b4",  # KHMER VOWEL INHERENT AQ
    "\u17b5",  # KHMER VOWEL INHERENT AA
    "\u2065",  # reserved default-ignorable code point
    "\u3164",  # HANGUL FILLER
    "\ufe0f",  # VARIATION SELECTOR-16
    "\uffa0",  # HALFWIDTH HANGUL FILLER
})


@dataclass(frozen=True)
class KnownViolationSpec:
    """ユーザー裁定済みの既知 provenance 違反。

    expected_finding_value は malformed commit で観測した不正 trailer 値を
    逐語で持ち、それ以外の kind では空にする。
    """

    commit: str
    expected_finding_kind: str
    ruling: str
    note: str = ""
    expected_finding_value: str = ""


_KNOWN_VIOLATION_DATA_FIELDS = ("sha", "kind", "value", "ruling", "note")
_KNOWN_VIOLATION_DATA_PREFIX = "known provenance violation data"
_KNOWN_VIOLATION_FILENAME = re.compile(
    r"^(?P<sha>[0-9a-f]{40})--"
    rf"(?P<kind>{'|'.join(sorted(_LEDGER_FINDING_KINDS))})--"
    r"(?P<digest>[0-9a-f]{64})\.json$"
)

KNOWN_VIOLATION_BASELINE_RULING_COMMIT = (
    "5265fc6782fa5807aa742a198fa16d58006d17fb"
)
KNOWN_VIOLATION_BASELINE_KEYS: frozenset[tuple[str, str, str]] = frozenset({
    ("88f0f9f081f7c76c8ab5fc4a94e2640f70af129b", "missing-ai-agent", ""),
    ("85dacc27054db0bd3db55d73cab4f8ca3b4843e5", "missing-ai-agent", ""),
    ("6e69ca5c2bc2df403e1cda595aeffcba3a97c248", "missing-ai-agent", ""),
    ("16affe169185040b33f8c6cbdd452260bddc4089", "missing-ai-agent", ""),
    ("905c867a7b2342ff250a1bcf28a3ce74abdacc06", "missing-ai-agent", ""),
    ("b0a07672737cf03424ec1790cc25a06e4c85b737", "missing-codex-author", ""),
    ("3f2c43d7580b8c26724d90278589862057508965", "missing-ai-agent", ""),
    ("f277efd4461d361d5c9aa6db9a7e00b194b76083", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("74b501962092373ba2e8bbca1566d0732e0f16c6", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("7ec088163dee920f0b8e1e9783faa6e36b22b730", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("1d09940463ccacb0dbb0ab3e69ca0698a960fdf1", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("f1406c22abece76276b43dde897750a46aae877e", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("a567eb68d85d2ea4db6002c12a0ee59d2a5cd69f", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("ff264975a04aa19f36f861ca97efe9dc59c88659", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("2c1929533a6f641b513f4f7990fe06e6cdb383b1", "missing-codex-author", ""),
    ("9af3e7a0f1c82fb91f310b5c9d197ec4a45f1320", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("2b3d06cbe81b1ae2675c153bdf307d508fc35a20", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("30719e517dcee45c014cbf1052c6dc70a8fcf693", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("622bd786191d40bda388596fa2adbf119ee84c9a", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("c75fde903384b6eb9e4d45239b66008b7639cbf7", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("c55ace29e55bba948d7bdca89f6fc1fb1a5191da", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("edf74c94427686f2b91519ef10e94446d0fe89d5", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("7e3cc116f2466fb439ec2bddd38f35dab928c942", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("66769067ee57d78650b208b9a86438ff2f1bf73b", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("1f884f6f6042cd8b1ce3f16f0bc7db3d97b768aa", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("aaffa644a969f0a58969b2661318bda4c42ac767", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("6f5411ceb7cc5d872e3112fb6d04013367ac092e", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("797db5def66ef1d318d06c7aa189ea51a66c9312", "malformed-ai-agent", "product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator"),
    ("8ceebcdbe40fac27cb2a1fbd7a1b1e016894bd0e", "missing-codex-author", ""),
    ("a5b7045b129d062c4731acc7667262795abd3f67", "missing-codex-author", ""),
    ("333605d680ec15f3f74b00e9e2746ae317b85dc5", "missing-codex-author", ""),
    ("311d463f89d1d1708a309b86d5bf63f5b034f89d", "missing-codex-author", ""),
    ("5823caf328a5985476cd2f6f7aa0d13daa5b08f6", "missing-codex-author", ""),
    ("09ce607b779272fda5629a350676471a16bea9bb", "missing-ai-agent", ""),
    ("13101ab3ec09a54e1f30462d1c2b4621b121ba65", "missing-ai-agent", ""),
    ("8440a14850718e63d73dfc510aa66b853a526424", "missing-codex-author", ""),
    ("d87fd42c0335c1396c1f79557e45357e9bfc163f", "missing-ai-agent", ""),
    ("75d57796ea8c6af4f80f32031afc952cfef2903a", "missing-ai-agent", ""),
    ("216493593dbee40fbdac65207ca328bae5bc9f52", "missing-ai-agent", ""),
    ("e39a8d46567a02d231fce52abae5aee759634ff7", "missing-codex-author", ""),
    ("3eaf2038ec2ac3e7965c2a1eedcadb1ed1266626", "missing-codex-author", ""),
    ("387a1daab0d713cf86f19449e88559686f1eb575", "missing-codex-author", ""),
    ("649fe5a060a39de295f90d2002e8f97082729ea6", "malformed-ai-agent", "product=codex; model=gpt-5.6-luna; reasoning=unknown; role=fix"),
    ("649fe5a060a39de295f90d2002e8f97082729ea6", "missing-codex-author", ""),
    ("e86d363a876ab00e7e6b37dfdd94385e5ab03816", "missing-codex-author", ""),
    ("0c0f3e71b3208370be8d4e7e20a84a2152afe4b2", "missing-codex-author", ""),
    ("bf92f327cadfbe626e37cab73d55abe80d3994dd", "missing-codex-author", ""),
    ("b9c07cc22d483a9103dac208a83446872161ffad", "missing-codex-author", ""),
    ("25614f868c1a1b562a68072233fdf55b0be93cd1", "missing-codex-author", ""),
    ("94815c57976806da56a3f067ade91c0041b2e2d1", "missing-codex-author", ""),
    ("3a5e5feb5f5c65e5e91752f847c623ce37e9b14d", "missing-codex-author", ""),
})
_REGULAR_GIT_MODES = frozenset({b"100644", b"100755"})


@dataclass(frozen=True)
class _KnownViolationWorktreeFile:
    sha: str
    kind: str
    digest: str
    data: bytes
    executable: bool


class _DuplicateKnownViolationJSONKey(ValueError):
    pass


def _known_violation_data_error(detail: str) -> RuntimeError:
    return RuntimeError(f"{_KNOWN_VIOLATION_DATA_PREFIX} {detail}")


def _known_violation_git(
    repo_root: Path,
    *args: str,
    input_bytes: bytes | None = None,
) -> bytes:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            env=_repo_discovery_isolated_env(),
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise _known_violation_data_error(
            f"git unavailable: {type(exc).__name__}: {exc}"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip()).decode(
            "utf-8", errors="backslashreplace",
        )
        raise _known_violation_data_error(
            f"git {' '.join(args)} failed (rc={proc.returncode}): {detail}"
        )
    if not isinstance(proc.stdout, bytes):
        raise _known_violation_data_error(
            f"git {' '.join(args)} returned non-bytes stdout"
        )
    return proc.stdout


def _resolve_known_violation_head(repo_root: Path) -> str:
    raw = _known_violation_git(
        repo_root, "rev-parse", "--verify", "HEAD^{commit}",
    ).strip()
    try:
        head = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise _known_violation_data_error(
            f"HEAD is not an ASCII object id: {raw!r}"
        ) from exc
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) is None:
        raise _known_violation_data_error(
            f"HEAD resolved to invalid object id: {head!r}"
        )
    return head


def _registry_git_path(raw: bytes, *, source: str) -> str:
    try:
        path = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _known_violation_data_error(
            f"{source} has non-UTF-8 path: {raw!r}"
        ) from exc
    prefix = f"{_KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix()}/"
    if not path.startswith(prefix):
        raise _known_violation_data_error(
            f"{source} has path outside registry directory: {path!r}"
        )
    child = path[len(prefix):]
    if not child or "/" in child:
        raise _known_violation_data_error(
            f"{source} has nested path: {path!r}"
        )
    return child


def _read_known_violation_worktree(
    directory: Path,
) -> dict[str, _KnownViolationWorktreeFile]:
    path_label = _KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix()
    try:
        directory_lstat = os.lstat(directory)
    except OSError as exc:
        raise _known_violation_data_error(
            f"directory is unavailable: {path_label}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    if stat.S_ISLNK(directory_lstat.st_mode):
        raise _known_violation_data_error(
            f"directory is symlink: {path_label}"
        )
    if not stat.S_ISDIR(directory_lstat.st_mode):
        raise _known_violation_data_error(
            f"directory is not a directory: {path_label}"
        )
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        directory_fd = os.open(directory, directory_flags)
    except OSError as exc:
        raise _known_violation_data_error(
            f"directory cannot be opened safely: {path_label}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    members: dict[str, _KnownViolationWorktreeFile] = {}
    try:
        opened_directory = os.fstat(directory_fd)
        if (
            opened_directory.st_dev != directory_lstat.st_dev
            or opened_directory.st_ino != directory_lstat.st_ino
            or not stat.S_ISDIR(opened_directory.st_mode)
        ):
            raise _known_violation_data_error(
                f"directory changed while opening: {path_label}"
            )
        try:
            names = sorted(os.listdir(directory_fd))
        except OSError as exc:
            raise _known_violation_data_error(
                f"directory cannot be listed: {path_label}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        for name in names:
            relative_path = (
                _KNOWN_VIOLATION_RELATIVE_DIRECTORY / name
            ).as_posix()
            match = _KNOWN_VIOLATION_FILENAME.fullmatch(name)
            if match is None:
                raise _known_violation_data_error(
                    f"has invalid filename: {relative_path!r}"
                )
            try:
                member_lstat = os.stat(
                    name, dir_fd=directory_fd, follow_symlinks=False,
                )
            except OSError as exc:
                raise _known_violation_data_error(
                    f"member is unavailable: {relative_path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            if stat.S_ISLNK(member_lstat.st_mode):
                raise _known_violation_data_error(
                    f"is symlink: {relative_path}"
                )
            if not stat.S_ISREG(member_lstat.st_mode):
                raise _known_violation_data_error(
                    f"is not a regular file: {relative_path}"
                )
            flags = (
                os.O_RDONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_NONBLOCK", 0)
            )
            try:
                member_fd = os.open(name, flags, dir_fd=directory_fd)
            except OSError as exc:
                raise _known_violation_data_error(
                    f"cannot be opened safely: {relative_path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            try:
                opened_member = os.fstat(member_fd)
                if (
                    opened_member.st_dev != member_lstat.st_dev
                    or opened_member.st_ino != member_lstat.st_ino
                    or not stat.S_ISREG(opened_member.st_mode)
                ):
                    raise _known_violation_data_error(
                        f"changed while opening: {relative_path}"
                    )
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(member_fd, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                final_member = os.fstat(member_fd)
                initial_fingerprint = (
                    opened_member.st_dev,
                    opened_member.st_ino,
                    opened_member.st_size,
                    opened_member.st_mtime_ns,
                )
                final_fingerprint = (
                    final_member.st_dev,
                    final_member.st_ino,
                    final_member.st_size,
                    final_member.st_mtime_ns,
                )
                if initial_fingerprint != final_fingerprint:
                    raise _known_violation_data_error(
                        f"changed while reading: {relative_path}"
                    )
            except OSError as exc:
                raise _known_violation_data_error(
                    f"cannot be read safely: {relative_path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            finally:
                os.close(member_fd)
            members[name] = _KnownViolationWorktreeFile(
                sha=match.group("sha"),
                kind=match.group("kind"),
                digest=match.group("digest"),
                data=b"".join(chunks),
                executable=bool(final_member.st_mode & 0o111),
            )
        final_directory = os.fstat(directory_fd)
        if (
            final_directory.st_dev != opened_directory.st_dev
            or final_directory.st_ino != opened_directory.st_ino
        ):
            raise _known_violation_data_error(
                f"directory changed while reading: {path_label}"
            )
    finally:
        os.close(directory_fd)
    return members


def _known_violation_index(repo_root: Path) -> dict[str, bytes]:
    raw = _known_violation_git(
        repo_root, "ls-files", "--stage", "-v", "-z", "--",
        _KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix(),
    )
    entries: dict[str, bytes] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        if len(record) < 3 or record[1:2] != b" ":
            raise _known_violation_data_error(
                f"git ls-files returned unexpected record: {record!r}"
            )
        flag = record[:1]
        metadata, separator, raw_path = record[2:].partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3:
            raise _known_violation_data_error(
                f"git ls-files returned unexpected record: {record!r}"
            )
        mode, oid, stage = fields
        name = _registry_git_path(raw_path, source="git index")
        relative_path = (
            _KNOWN_VIOLATION_RELATIVE_DIRECTORY / name
        ).as_posix()
        if flag != b"H":
            reason = (
                "skip-worktree" if flag == b"S"
                else "assume-unchanged" if flag.islower()
                else f"unsafe index flag {flag!r}"
            )
            raise _known_violation_data_error(
                f"has {reason}: {relative_path}"
            )
        if (
            mode not in _REGULAR_GIT_MODES
            or stage != b"0"
            or re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None
        ):
            raise _known_violation_data_error(
                f"index entry is not a stage-0 regular file: {relative_path}"
            )
        if name in entries:
            raise _known_violation_data_error(
                f"git index has duplicate member: {relative_path}"
            )
        entries[name] = mode
    return entries


def _known_violation_ignored(repo_root: Path) -> set[str]:
    raw = _known_violation_git(
        repo_root,
        "ls-files", "--others", "--ignored", "--exclude-standard", "-z",
        "--", _KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix(),
    )
    return {
        _registry_git_path(record, source="git ignored set")
        for record in raw.split(b"\0")
        if record
    }


def _known_violation_head_entries(
    repo_root: Path, head: str,
) -> dict[str, tuple[bytes, bytes]]:
    raw = _known_violation_git(
        repo_root,
        "ls-tree", "-rz", "--full-tree", head, "--",
        _KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix(),
    )
    entries: dict[str, tuple[bytes, bytes]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3:
            raise _known_violation_data_error(
                f"git ls-tree returned unexpected record: {record!r}"
            )
        mode, object_type, oid = fields
        name = _registry_git_path(raw_path, source="HEAD tree")
        relative_path = (
            _KNOWN_VIOLATION_RELATIVE_DIRECTORY / name
        ).as_posix()
        if (
            mode not in _REGULAR_GIT_MODES
            or object_type != b"blob"
            or re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None
        ):
            raise _known_violation_data_error(
                f"HEAD entry is not a regular blob: {relative_path}"
            )
        if name in entries:
            raise _known_violation_data_error(
                f"HEAD tree has duplicate member: {relative_path}"
            )
        entries[name] = (mode, oid)
    return entries


def _known_violation_head_blobs(
    repo_root: Path, entries: dict[str, tuple[bytes, bytes]],
) -> dict[str, bytes]:
    ordered = sorted(entries)
    if not ordered:
        return {}
    request = b"".join(entries[name][1] + b"\n" for name in ordered)
    raw = _known_violation_git(
        repo_root, "cat-file", "--batch", input_bytes=request,
    )
    offset = 0
    blobs: dict[str, bytes] = {}
    for name in ordered:
        line_end = raw.find(b"\n", offset)
        if line_end < 0:
            raise _known_violation_data_error(
                "git cat-file --batch returned truncated header"
            )
        header = raw[offset:line_end]
        offset = line_end + 1
        fields = header.split()
        expected_oid = entries[name][1]
        if (
            len(fields) != 3
            or fields[0] != expected_oid
            or fields[1] != b"blob"
            or not fields[2].isascii()
            or not fields[2].isdigit()
        ):
            raise _known_violation_data_error(
                f"git cat-file --batch returned unexpected header: {header!r}"
            )
        size = int(fields[2], 10)
        end = offset + size
        if end >= len(raw) or raw[end:end + 1] != b"\n":
            raise _known_violation_data_error(
                f"git cat-file --batch returned truncated blob: {name}"
            )
        blobs[name] = raw[offset:end]
        offset = end + 1
    if offset != len(raw):
        raise _known_violation_data_error(
            "git cat-file --batch returned trailing bytes"
        )
    return blobs


def _decode_known_violation_object(
    relative_path: str, raw: bytes,
) -> dict[str, str]:
    def reject_duplicate(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise _DuplicateKnownViolationJSONKey(key)
            result[key] = value
        return result
    try:
        text = raw.decode("utf-8")
        obj = json.loads(text, object_pairs_hook=reject_duplicate)
    except _DuplicateKnownViolationJSONKey as exc:
        raise _known_violation_data_error(
            f"has duplicate key: {relative_path}: {exc.args[0]}"
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _known_violation_data_error(
            f"is not canonical UTF-8 JSON: {relative_path}"
        ) from exc
    if not isinstance(obj, dict):
        raise _known_violation_data_error(
            f"root is not an object: {relative_path}"
        )
    keys = set(obj)
    expected = set(_KNOWN_VIOLATION_DATA_FIELDS)
    unknown = sorted(keys - expected)
    missing = sorted(expected - keys)
    if unknown:
        raise _known_violation_data_error(
            f"has unknown keys: {relative_path}: {unknown!r}"
        )
    if missing:
        raise _known_violation_data_error(
            f"has missing keys: {relative_path}: {missing!r}"
        )
    for field in _KNOWN_VIOLATION_DATA_FIELDS:
        value = obj[field]
        if not isinstance(value, str):
            raise _known_violation_data_error(
                f"has invalid field type: {relative_path}: "
                f"field={field} type={type(value).__name__}"
            )
    canonical_obj = {
        field: obj[field] for field in _KNOWN_VIOLATION_DATA_FIELDS
    }
    canonical = (
        json.dumps(canonical_obj, ensure_ascii=False, indent=2, sort_keys=False)
        + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise _known_violation_data_error(
            f"is not canonical UTF-8 JSON: {relative_path}"
        )
    return canonical_obj


def _append_known_violation_spec(
    spec: KnownViolationSpec,
    registry: dict[str, list[KnownViolationSpec]],
) -> None:
    if not isinstance(spec, KnownViolationSpec):
        raise RuntimeError(
            "known provenance violation registry has invalid entry: "
            f"{spec!r}"
        )
    if not isinstance(spec.commit, str):
        raise RuntimeError(
            "known provenance violation registry has invalid SHA type: "
            f"{type(spec.commit).__name__}"
        )
    if re.fullmatch(r"[0-9a-f]{40}", spec.commit) is None:
        raise RuntimeError(
            "known provenance violation registry has invalid full SHA: "
            f"{spec.commit!r}"
        )
    if not isinstance(spec.expected_finding_kind, str):
        raise RuntimeError(
            "known provenance violation registry has invalid finding kind type: "
            f"{type(spec.expected_finding_kind).__name__}"
        )
    if spec.expected_finding_kind not in _LEDGER_FINDING_KINDS:
        raise RuntimeError(
            "known provenance violation registry has invalid finding kind: "
            f"{spec.expected_finding_kind!r}"
        )
    if not isinstance(spec.ruling, str) or not spec.ruling.strip():
        raise RuntimeError(
            "known provenance violation registry has empty ruling: "
            f"{spec.commit}"
        )
    if not isinstance(spec.note, str):
        raise RuntimeError(
            "known provenance violation registry has invalid note type: "
            f"{type(spec.note).__name__}"
        )
    if spec.note != "" and spec.note.splitlines() != [spec.note]:
        raise RuntimeError(
            "known provenance violation registry has line break in note: "
            f"{spec.commit}"
        )
    if not isinstance(spec.expected_finding_value, str):
        raise RuntimeError(
            "known provenance violation registry has invalid finding value type: "
            f"{type(spec.expected_finding_value).__name__}"
        )
    if spec.expected_finding_kind == MALFORMED_AI_AGENT and not spec.expected_finding_value:
        raise RuntimeError(
            "known provenance violation registry has empty required finding value: "
            f"{spec.commit}"
        )
    if spec.expected_finding_kind != MALFORMED_AI_AGENT and spec.expected_finding_value:
        raise RuntimeError(
            "known provenance violation registry has unexpected finding value: "
            f"{spec.commit}"
        )
    if spec.expected_finding_kind in _NOTE_REQUIRED_FINDING_KINDS and not spec.note.strip():
        raise RuntimeError(
            "known provenance violation registry has empty required note: "
            f"{spec.commit}"
        )
    if (
        spec.expected_finding_kind in _NOTE_REQUIRED_FINDING_KINDS
        and _contains_prohibited_registry_character(spec.note)
    ):
        raise RuntimeError(
            "known provenance violation registry has prohibited character in note: "
            f"{spec.commit}"
        )
    if (
        spec.expected_finding_kind in _NOTE_REQUIRED_FINDING_KINDS
        and not _contains_descriptive_note_character(spec.note)
    ):
        raise RuntimeError(
            "known provenance violation registry has non-descriptive required note: "
            f"{spec.commit}"
        )
    if _contains_prohibited_registry_character(spec.expected_finding_value):
        raise RuntimeError(
            "known provenance violation registry has prohibited character in "
            f"finding value: {spec.commit}"
        )
    prior_specs = registry.setdefault(spec.commit, [])
    if any(
        prior.expected_finding_kind == spec.expected_finding_kind
        and prior.expected_finding_value == spec.expected_finding_value
        for prior in prior_specs
    ):
        raise RuntimeError(
            "known provenance violation registry has duplicate SHA/finding: "
            f"{spec.commit} {spec.expected_finding_kind}"
        )
    prior_specs.append(spec)


@dataclass(frozen=True)
class _KnownViolationGroups:
    irreversible_history: frozenset[tuple[str, str, str]]
    post_baseline: frozenset[tuple[str, str, str]]


def _contains_prohibited_registry_character(value: str) -> bool:
    return any(
        char in _ZERO_WIDTH_REGISTRY_CHARACTERS
        or unicodedata.category(char) in _PROHIBITED_REGISTRY_CATEGORIES
        for char in value
    )


def _contains_descriptive_note_character(value: str) -> bool:
    return any(
        char not in _NON_DESCRIPTIVE_NOTE_CHARACTERS
        and unicodedata.category(char)[0] in _DESCRIPTIVE_NOTE_CATEGORY_PREFIXES
        for char in value
    )


def _known_violation_registry(
    repo_root: Path | None = None,
) -> dict[str, tuple[KnownViolationSpec, ...]]:
    """Commit 済み directory を history 監査時だけ検証し、full SHA map にする。

    filename の digest 成分は filename 据え置きの本文改変だけを防ぎ、裁定根拠の
    真正性は保証しない。真正性は check_known_violation_append_only_history()
    が担う。
    """
    if repo_root is None:
        root = _KNOWN_VIOLATION_REPO_ROOT
        directory = _KNOWN_VIOLATION_DIRECTORY
    else:
        root = Path(repo_root)
        directory = root / _KNOWN_VIOLATION_RELATIVE_DIRECTORY
    head = _resolve_known_violation_head(root)
    worktree = _read_known_violation_worktree(directory)
    index = _known_violation_index(root)
    ignored = _known_violation_ignored(root)
    worktree_names = set(worktree)
    index_names = set(index)
    unindexed = worktree_names - index_names
    ignored_unindexed = sorted(unindexed & ignored)
    if ignored_unindexed:
        name = ignored_unindexed[0]
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        raise _known_violation_data_error(f"is ignored: {path}")
    ordinary_untracked = sorted(unindexed - ignored)
    if ordinary_untracked:
        name = ordinary_untracked[0]
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        raise _known_violation_data_error(f"is untracked: {path}")
    missing_worktree = sorted(index_names - worktree_names)
    if missing_worktree:
        name = missing_worktree[0]
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        raise _known_violation_data_error(
            f"tracked member is missing from worktree: {path}"
        )
    head_entries = _known_violation_head_entries(root, head)
    head_names = set(head_entries)
    index_only = sorted(index_names - head_names)
    if index_only:
        name = index_only[0]
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        raise _known_violation_data_error(
            f"index-only member does not match HEAD: {path}"
        )
    head_only = sorted(head_names - index_names)
    if head_only:
        name = head_only[0]
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        raise _known_violation_data_error(
            f"HEAD member is missing from index: {path}"
        )
    for name in sorted(head_names):
        if index[name] != head_entries[name][0]:
            path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
            raise _known_violation_data_error(
                f"index mode does not match HEAD: {path}"
            )
    blobs = _known_violation_head_blobs(root, head_entries)
    for name in sorted(head_names):
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        file = worktree[name]
        head_mode = head_entries[name][0]
        if file.executable != (head_mode == b"100755"):
            raise _known_violation_data_error(
                f"worktree mode does not match HEAD: {path}"
            )
        if file.data != blobs[name]:
            raise _known_violation_data_error(
                f"does not match HEAD: {path}"
            )
    end_head = _resolve_known_violation_head(root)
    if end_head != head:
        raise _known_violation_data_error(
            f"HEAD changed while loading: start={head}, end={end_head}"
        )
    registry: dict[str, list[KnownViolationSpec]] = {}
    for name in sorted(worktree):
        path = (_KNOWN_VIOLATION_RELATIVE_DIRECTORY / name).as_posix()
        file = worktree[name]
        obj = _decode_known_violation_object(path, file.data)
        digest = hashlib.sha256(file.data).hexdigest()
        if (
            file.sha != obj["sha"]
            or file.kind != obj["kind"]
            or file.digest != digest
        ):
            raise _known_violation_data_error(
                f"filename/body mismatch: {path}"
            )
        _append_known_violation_spec(
            KnownViolationSpec(
                commit=obj["sha"],
                expected_finding_kind=obj["kind"],
                ruling=obj["ruling"],
                note=obj["note"],
                expected_finding_value=obj["value"],
            ),
            registry,
        )
    return {commit: tuple(specs) for commit, specs in registry.items()}


def _known_violation_append_only_git(
    repo_root: Path, *args: str,
) -> bytes:
    prefix = "known provenance violation append-only history check failed"
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            env=_repo_discovery_isolated_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(
            f"{prefix}: git unavailable: {type(exc).__name__}: {exc}"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip()).decode(
            "utf-8", errors="backslashreplace",
        )
        raise RuntimeError(
            f"{prefix}: git {' '.join(args)} failed "
            f"(rc={proc.returncode}): {detail}"
        )
    if not isinstance(proc.stdout, bytes):
        raise RuntimeError(
            f"{prefix}: git {' '.join(args)} returned non-bytes stdout"
        )
    return proc.stdout


def check_known_violation_append_only_history(repo_root: Path) -> None:
    """着地済み known-violation file の変更・削除・rename を拒否する。

    filename の digest 成分が防ぐのは filename 据え置きの本文改変だけであり、
    裁定根拠の真正性は保証しない。この append-only 履歴検査が、着地後の blob
    改変・削除・rename を履歴全体から拒否することで真正性を担う。

    production では引数なしの authoritative 全史監査だけが呼ぶ。合成 repo を
    監査する --range からは呼ばず、lazy 契約を持つ --message-file からも呼ばない。
    """
    root = Path(repo_root)
    prefix = "known provenance violation append-only history check failed"
    head = _known_violation_append_only_git(
        root, "rev-parse", "--verify", "HEAD^{commit}",
    ).strip()
    if re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", head) is None:
        raise RuntimeError(f"{prefix}: HEAD cannot be resolved")
    shallow = _known_violation_append_only_git(
        root, "rev-parse", "--is-shallow-repository",
    ).strip()
    if shallow != b"false":
        raise RuntimeError(
            f"{prefix}: authoritative history is unavailable "
            f"(is-shallow-repository={shallow!r})"
        )
    path_history = _known_violation_append_only_git(
        root, "log", "-1", "--format=%H", "--",
        _KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix(),
    ).strip()
    if re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", path_history) is None:
        raise RuntimeError(
            f"{prefix}: registry path has no authoritative history"
        )
    changed = _known_violation_append_only_git(
        root,
        "log", "--full-history", "-m", "--no-renames", "--diff-filter=MDT",
        "--format=%H", "--name-only", "--",
        _KNOWN_VIOLATION_RELATIVE_DIRECTORY.as_posix(),
    )
    end_head = _known_violation_append_only_git(
        root, "rev-parse", "--verify", "HEAD^{commit}",
    ).strip()
    if end_head != head:
        raise RuntimeError(
            f"{prefix}: HEAD changed while checking history: "
            f"start={head!r}, end={end_head!r}"
        )
    if changed == b"":
        return
    try:
        lines = changed.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            f"{prefix}: history contains a non-UTF-8 registry path"
        ) from exc
    current_commit: str | None = None
    violations: list[str] = []
    for line in lines:
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", line):
            current_commit = line
            continue
        if current_commit is None:
            raise RuntimeError(
                f"{prefix}: git log returned path without commit: {line!r}"
            )
        violations.append(f"commit={current_commit} path={line}")
    if not violations:
        raise RuntimeError(
            f"{prefix}: git log returned unparseable non-empty output"
        )
    raise RuntimeError(f"{prefix}: " + "; ".join(violations))


def _known_violation_key(spec: KnownViolationSpec) -> tuple[str, str, str]:
    return (
        spec.commit,
        spec.expected_finding_kind,
        spec.expected_finding_value,
    )


def _known_violation_groups(
    registry: dict[str, tuple[KnownViolationSpec, ...]],
) -> _KnownViolationGroups:
    """正規化済み台帳を凍結 baseline との純粋な集合演算で二分する。"""

    try:
        ledger_keys = frozenset(
            _known_violation_key(spec)
            for specs in registry.values()
            for spec in specs
        )
        irreversible_history = ledger_keys & KNOWN_VIOLATION_BASELINE_KEYS
        post_baseline = ledger_keys - KNOWN_VIOLATION_BASELINE_KEYS
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "known provenance violation group classification failed"
        ) from exc
    return _KnownViolationGroups(irreversible_history, post_baseline)


def _print_known_violation_groups(groups: _KnownViolationGroups) -> None:
    baseline = KNOWN_VIOLATION_BASELINE_RULING_COMMIT
    print(
        "check_ai_provenance: known-violations-irreversible-history="
        f"{len(groups.irreversible_history)} population=whole-ledger "
        "excluded=key-not-in-d742-baseline "
        f"baseline={baseline}"
    )
    print(
        "check_ai_provenance: known-violations-post-baseline="
        f"{len(groups.post_baseline)} population=whole-ledger "
        "excluded=key-in-d742-baseline "
        f"baseline={baseline}"
    )


def _known_violation_line(spec: KnownViolationSpec) -> str:
    line = (
        "check_ai_provenance: known-violation "
        f"sha={spec.commit} finding={spec.expected_finding_kind}"
    )
    if spec.note != "":
        line += f" note={spec.note}"
    return line


@dataclass(frozen=True)
class CorrectionAudit:
    raw_values: tuple[str, ...]
    parsed_values: tuple[str, ...]
    final_values: tuple[str, ...]
    final_ai_agent_values: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def candidate_count(self) -> int:
        return len(self.raw_values)

    @property
    def exact(self) -> bool:
        return self.candidate_count == 1 and not self.findings


@dataclass(frozen=True)
class WaiverAudit:
    """Codex author 契約の免除行。作法は CorrectionAudit を踏襲する。

    唯一の作法差: incident 固定値との逐語一致の代わりに WAIVER_VALUE 文法照合を
    置く (waiver は payload が可変で、固定値が存在しない)。
    """

    raw_values: tuple[str, ...]
    parsed_values: tuple[str, ...]
    final_values: tuple[str, ...]
    reason: str | None
    ratified: str | None
    findings: tuple[str, ...]

    @property
    def candidate_count(self) -> int:
        return len(self.raw_values)

    @property
    def exact(self) -> bool:
        return self.candidate_count == 1 and not self.findings


EMPTY_WAIVER = WaiverAudit((), (), (), None, None, ())


@dataclass(frozen=True)
class NormalFinding:
    text: str
    ledger_kind: str | None


@dataclass(frozen=True)
class _CommitMessage:
    subject: str
    message: str


@dataclass(frozen=True)
class CommitAudit:
    commit: str
    label: str
    normal_findings: tuple[NormalFinding, ...]
    correction: CorrectionAudit
    waiver: WaiverAudit = EMPTY_WAIVER
    waived_applied: bool = False


@dataclass(frozen=True)
class ForwardCorrected:
    target: str
    correction: str


@dataclass(frozen=True)
class ImplementationWaived:
    """実際に発火した免除 1 件。

    label は history 経路では commit SHA、message-file 経路では message file の
    path (commit 前で SHA が存在しない) を持つ。
    """

    label: str
    reason: str
    ratified: str


@dataclass(frozen=True)
class HistoryAudit:
    """History findings are new violations only; known entries are separate."""

    findings: list[str]
    corrected: list[ForwardCorrected]
    waived: list[ImplementationWaived]
    known_violations: tuple[KnownViolationSpec, ...] = ()


@dataclass(frozen=True)
class KnownViolationAudit:
    findings: tuple[str, ...]
    known_violations: tuple[KnownViolationSpec, ...]
    stale: tuple[KnownViolationSpec, ...]


def _git(*args: str, input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _batch_commit_messages(commits: list[str]) -> dict[str, _CommitMessage] | None:
    """Use the selected OIDs only; discard the entire batch on any failure.

    LF belongs in Git's output, before text-mode newline translation, just as
    in the two legacy show calls. None asks every worker to use those calls so
    speculative acquisition cannot change public errors or their input order.
    """
    requested = set(commits)
    if not all(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) for oid in requested):
        return None
    if not requested:
        return {}
    try:
        output = _git(
            "log", "--no-walk=unsorted", "--stdin", "-z",
            "--format=tformat:%H%x00%s%x0a%x00%B%x0a",
            input_text="\n".join(dict.fromkeys(commits)) + "\n",
        )
    except (RuntimeError, OSError, UnicodeError):
        return None
    if not output.endswith("\0"):
        return None
    fields = output[:-1].split("\0")
    if len(fields) != 3 * len(requested):
        return None
    messages: dict[str, _CommitMessage] = {}
    for offset in range(0, len(fields), 3):
        oid, subject, message = fields[offset:offset + 3]
        if (
            not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid)
            or oid not in requested
            or oid in messages
        ):
            return None
        messages[oid] = _CommitMessage(subject.strip(), message)
    if set(messages) != requested:
        return None
    return messages


def _canonical_trailer_env(parse_cwd: Path) -> dict[str, str]:
    """ambient config と repo discovery から隔離した trailer parser 環境。"""
    env = {
        key: value for key, value in _repo_discovery_isolated_env().items()
        if key != "GIT_CONFIG"
        and not key.startswith("GIT_CONFIG_")
    }
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CEILING_DIRECTORIES"] = str(parse_cwd)
    return env


def _isolated_parsed_trailers(
    message: str, *, no_divider: bool,
) -> dict[str, list[str]]:
    """隔離 parser の LF record を case-fold key ごとに返す。"""
    message_bytes = message.encode("utf-8")
    with tempfile.TemporaryDirectory(
        prefix="check-ai-provenance-",
        dir=TRAILER_PARSE_TEMP_ROOT,
    ) as private_dir:
        ceiling = Path(private_dir)
        parse_cwd = ceiling / "cwd"
        parse_cwd.mkdir()
        command = [
            "git", "-c", "trailer.separators=:",
            "interpret-trailers", "--parse",
        ]
        if no_divider:
            command.append("--no-divider")
        proc = subprocess.run(
            command,
            cwd=parse_cwd,
            env=_canonical_trailer_env(ceiling),
            input=message_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    if proc.returncode != 0:
        detail_bytes = proc.stderr.strip() or proc.stdout.strip()
        detail = detail_bytes.decode("utf-8", errors="backslashreplace")
        raise RuntimeError(f"git interpret-trailers failed: {detail}")
    if not isinstance(proc.stdout, bytes):
        raise RuntimeError("git interpret-trailers returned non-bytes stdout")

    records = proc.stdout.split(b"\n")
    if records and records[-1] == b"":
        records.pop()
    trailers: dict[str, list[str]] = {}
    for record in records:
        decoded = record.decode("utf-8")
        key, sep, value = decoded.partition(":")
        if not record or not sep or not key.strip(" \t"):
            raise RuntimeError(
                "git interpret-trailers returned unexpected LF record: "
                f"{record!r}"
            )
        trailers.setdefault(key.strip(" \t").casefold(), []).append(
            value.strip(" \t")
        )
    return trailers


def _parsed_trailers(message: str) -> dict[str, list[str]]:
    """CAB/correction 用の隔離 --no-divider canonical parse。"""
    return _isolated_parsed_trailers(message, no_divider=True)


def _parsed_final_trailers(message: str) -> dict[str, list[str]]:
    """correction と AI-Agent の final block を隔離 default parse で返す。"""
    return _isolated_parsed_trailers(message, no_divider=False)


def _ai_agent_values(message: str) -> list[str]:
    """従来の repo cwd・divider 既定 parser で AI-Agent 値だけを返す。"""
    parsed = _git("interpret-trailers", "--parse", input_text=message)
    values: list[str] = []
    for line in parsed.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "ai-agent":
            values.append(value.strip())
    return values


def _co_authored_by_findings(
    label: str, message: str,
) -> list[str]:
    raw_count = len(RAW_CO_AUTHORED_BY.findall(message))
    trailers = _parsed_trailers(message)
    parsed_count = len(trailers.get("co-authored-by", []))
    if raw_count == parsed_count:
        return []
    return [
        f"{label}: Co-Authored-By trailer 配置違反: "
        f"raw={raw_count}, parsed={parsed_count}"
    ]


def _correction_audit(label: str, message: str) -> CorrectionAudit:
    """raw 候補を隔離 canonical/final-block parse と突き合わせる。"""
    matches = tuple(RAW_AI_AGENT_CORRECTION.finditer(message))
    if not matches:
        return CorrectionAudit((), (), (), (), ())

    raw_values = tuple(match.group("value") for match in matches)
    key = CORRECTION_KEY.casefold()
    parsed_values = tuple(
        _parsed_trailers(message).get(key, [])
    )
    final_trailers = _parsed_final_trailers(message)
    final_values = tuple(final_trailers.get(key, []))
    final_ai_agent_values = tuple(final_trailers.get("ai-agent", []))
    payload = INCIDENT_6B64D21_FORWARD_CORRECTION.payload
    findings: list[str] = []
    if len(raw_values) != 1:
        findings.append(
            f"{label}: {CORRECTION_KEY} raw candidate cardinality 違反: "
            f"raw={len(raw_values)}（物理 exact 1 行が必要）"
        )
    if raw_values and any(value != f" {payload}" for value in raw_values):
        findings.append(
            f"{label}: {CORRECTION_KEY} raw value が incident 固定値と一致しない"
        )
    if len(parsed_values) != 1:
        findings.append(
            f"{label}: {CORRECTION_KEY} canonical multiplicity 違反: "
            f"raw={len(raw_values)}, canonical={len(parsed_values)}"
        )
    if parsed_values and any(value != payload for value in parsed_values):
        findings.append(
            f"{label}: {CORRECTION_KEY} canonical value が incident 固定値と一致しない"
        )
    if len(final_values) != 1 or not final_ai_agent_values:
        findings.append(
            f"{label}: {CORRECTION_KEY} final trailer block multiplicity 違反: "
            f"correction={len(final_values)}, ai-agent={len(final_ai_agent_values)}"
        )
    if final_values and any(value != payload for value in final_values):
        findings.append(
            f"{label}: {CORRECTION_KEY} final trailer block value が "
            "incident 固定値と一致しない"
        )
    return CorrectionAudit(
        raw_values,
        parsed_values,
        final_values,
        final_ai_agent_values,
        tuple(findings),
    )


def _waiver_audit(label: str, message: str) -> WaiverAudit:
    """raw 候補を隔離 canonical/final-block parse と突き合わせる (waiver 版)。"""
    matches = tuple(RAW_AI_AGENT_WAIVER.finditer(message))
    if not matches:
        return EMPTY_WAIVER

    raw_values = tuple(match.group("value") for match in matches)
    key = WAIVER_KEY.casefold()
    parsed_values = tuple(_parsed_trailers(message).get(key, []))
    final_trailers = _parsed_final_trailers(message)
    final_values = tuple(final_trailers.get(key, []))
    final_ai_agent_values = tuple(final_trailers.get("ai-agent", []))
    findings: list[str] = []
    if len(raw_values) != 1:
        findings.append(
            f"{label}: {WAIVER_KEY} raw candidate cardinality 違反: "
            f"raw={len(raw_values)}（物理 exact 1 行が必要）"
        )
    if any(
        not value.startswith(" ")
        or WAIVER_VALUE.fullmatch(value[1:]) is None
        for value in raw_values
    ):
        findings.append(
            f"{label}: {WAIVER_KEY} raw value が形式に一致しない — "
            "reason=<ident>; ratified=<YYYY-MM-DD> の順と許可値を確認する"
        )
    if len(parsed_values) != 1:
        findings.append(
            f"{label}: {WAIVER_KEY} canonical multiplicity 違反: "
            f"raw={len(raw_values)}, canonical={len(parsed_values)}"
        )
    if any(
        WAIVER_VALUE.fullmatch(value) is None for value in parsed_values
    ):
        findings.append(
            f"{label}: {WAIVER_KEY} canonical value が形式に一致しない"
        )
    if len(final_values) != 1:
        findings.append(
            f"{label}: {WAIVER_KEY} final trailer block multiplicity 違反: "
            f"waiver={len(final_values)}"
        )
    elif not any(
        (agent := AGENT_VALUE.fullmatch(value)) is not None
        and agent.group("role") == "author"
        for value in final_ai_agent_values
    ):
        findings.append(
            f"{label}: {WAIVER_KEY} と同じ最終 trailer block に "
            "role=author の AI-Agent がない"
        )
    reason: str | None = None
    ratified: str | None = None
    if len(parsed_values) == 1:
        match = WAIVER_VALUE.fullmatch(parsed_values[0])
        if match is not None:
            reason = match.group("reason")
            ratified = match.group("ratified")
    return WaiverAudit(
        raw_values,
        parsed_values,
        final_values,
        reason,
        ratified,
        tuple(findings),
    )


def validate_message(
    label: str, message: str, *, check_cab: bool = True,
    values: list[str] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    """(findings, scope_findings, cab_findings) を返す。

    scope_findings は「同じ role が複数行あるのに scope がない」違反。適用可否は呼び出し側
    (`_normal_commit_audit` の `applies_epoch`) が判定する — 非 authoritative の明示
    `--range` では scope 規則の子孫にのみ適用し、既定の authoritative 監査では scope 規則の
    祖先でない HEAD 到達 commit にも適用する。
    CAB policy 導入前の履歴では check_cab=False とし、canonical parser 自体を呼ばない。
    """
    if values is None:
        values = _ai_agent_values(message)
    cab_findings = (
        _co_authored_by_findings(label, message) if check_cab else []
    )
    if not values:
        return [f"{label}: AI-Agent trailer がない"], [], cab_findings

    if "none" in values:
        if values != ["none"]:
            return [
                f"{label}: AI-Agent: none は唯一の AI-Agent trailer でなければならない"
            ], [], cab_findings
        return [], [], cab_findings

    findings: list[str] = []
    seen: set[str] = set()
    by_role: dict[str, list[tuple[str, bool]]] = {}
    for value in values:
        if value in seen:
            findings.append(f"{label}: 同一 AI-Agent trailer の重複: {value}")
            continue
        seen.add(value)
        match = AGENT_VALUE.fullmatch(value)
        if not match:
            findings.append(
                f"{label}: AI-Agent の形式違反: {value!r} — "
                "product/model/reasoning/role (任意で scope) の順と許可値を確認する"
            )
            continue
        by_role.setdefault(match.group("role"), []).append(
            (value, match.group("scope") is not None)
        )
        if match.group("product") in RESERVED_PRODUCTS:
            findings.append(
                f"{label}: product={match.group('product')} は AI 製品識別子として使えない"
            )
        if match.group("model") == "none" or match.group("reasoning") == "none":
            findings.append(
                f"{label}: model/reasoning に none は使えない — "
                "not-exposed または unknown を使う"
            )

    scope_findings: list[str] = []
    for role, entries in by_role.items():
        if len(entries) < 2:
            continue
        for value, has_scope in entries:
            if not has_scope:
                scope_findings.append(
                    f"{label}: role={role} が複数行あるのに scope がない: {value}"
                )
    return findings, scope_findings, cab_findings


def _scope_policy_commit(head: str | None = None) -> str | None:
    """scope 規則を docs/ai-provenance.md へ導入した commit を内容検出する (SHA 非依存)。"""
    tip = head or "HEAD"
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", "scope=", tip,
        "--", POLICY_PATH,
    ).splitlines()
    return commits[0] if commits else None


def _implementation_policy_commit(head: str | None = None) -> str | None:
    """Codex author 契約を導入した commit を内容検出する。"""
    tip = head or "HEAD"
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", IMPLEMENTATION_POLICY_NEEDLE,
        tip, "--", POLICY_PATH,
    ).splitlines()
    return commits[0] if commits else None


def _has_co_authored_by_policy(commit: str) -> bool:
    """commit ancestry に CAB policy needle の変更があれば適用済みとみなす。"""
    commits = _git(
        "log", "--full-history", "--no-renames", "--format=%H",
        "-S", CO_AUTHORED_BY_POLICY_NEEDLE, commit, "--", POLICY_PATH,
    ).splitlines()
    return bool(commits)


def _is_descendant(ancestor: str, commit: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, commit],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    detail = proc.stderr.strip()
    raise RuntimeError(
        "git merge-base --is-ancestor "
        f"{ancestor} {commit} failed (rc={proc.returncode}): {detail}"
    )


def _is_implementation_path(path: str) -> bool:
    """Git 相対 path が実装面なら True。所在・拡張子の契約を一か所で判定する。"""
    normalized = path.removeprefix("./")
    basename = normalized.rsplit("/", 1)[-1]
    if basename in IMPLEMENTATION_BASENAMES:
        return True
    if normalized.endswith(IMPLEMENTATION_SUFFIXES):
        return True
    if normalized.startswith("patches/"):
        return False
    return (
        normalized.startswith(IMPLEMENTATION_PREFIXES)
        and not normalized.endswith((".md", ".rst"))
    )


def validate_implementation_author(
    label: str, message: str, paths: list[str], *, waived: bool = False,
    values: list[str] | None = None,
) -> tuple[list[str], bool]:
    """AI 関与の実装面 commit に Codex author がいることを検査する。

    (findings, waived_applied) を返す。waived_applied は「免除が実際に発火した」
    ときだけ True であり、waiver 行の付与数ではない (実装面 path なし・
    AI 非関与・codex author 済みの各早期 return では False のまま)。
    """
    implementation = sorted(path for path in paths if _is_implementation_path(path))
    if not implementation:
        return [], False
    if values is None:
        values = _ai_agent_values(message)
    if not values or values == ["none"]:
        return [], False
    for value in values:
        match = AGENT_VALUE.fullmatch(value)
        if (
            match is not None
            and match.group("product") == "codex"
            and match.group("role") == "author"
        ):
            return [], False
    if waived:
        return [], True
    sample = ", ".join(implementation[:3])
    if len(implementation) > 3:
        sample += f", ... ({len(implementation)} paths)"
    return [
        f"{label}: 実装面に Codex role=author がない — paths={sample}"
    ], False


def _nul_paths(raw: str) -> list[str]:
    return [path for path in raw.split("\0") if path]


def _commit_parents(commit: str) -> list[str]:
    return _git("show", "-s", "--format=%P", commit).split()


def _parse_path_batch(raw: str, requested: list[str]) -> dict[str, list[str]] | None:
    """Every OID-shaped token is a header, including paths after the last header."""
    if not raw.endswith("\0"):
        return None
    tokens = raw[:-1].split("\0")
    result: dict[str, list[str]] = {}
    headers: list[str] = []
    paths: list[str] | None = None
    for token in tokens:
        if not token:
            return None
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", token):
            headers.append(token)
            paths = []
            result[token] = paths
        elif paths is None:
            return None
        else:
            paths.append(token)
    if headers != requested or result.keys() != set(requested):
        return None
    return result


def _batch_nonmerge_paths(commits: list[str]) -> dict[str, list[str]] | None:
    requested = list(dict.fromkeys(commits))
    if not requested:
        return {}
    try:
        raw = _git(
            "diff-tree", "--stdin", "--root", "--no-renames", "-r",
            "--name-only", "-z", "--always",
            input_text="".join(f"{oid}\n" for oid in requested),
        )
        return _parse_path_batch(raw, requested)
    except (RuntimeError, OSError, UnicodeError, ValueError):
        return None


def _merge_path_batch_enabled() -> bool:
    try:
        statuses = [subprocess.run(
            ["git", "config", "--get", key], cwd=REPO, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).returncode for key in ("diff.ignoreSubmodules", "diff.relative")]
        return statuses == [1, 1]
    except (RuntimeError, OSError, UnicodeError, ValueError):
        return False


def _batch_merge_parent_paths(
    merges: list[str], parents_table: dict[str, tuple[str, ...]],
) -> dict[str, list[set[str]]] | None:
    requested = list(dict.fromkeys(merges))
    result: dict[str, list[set[str]]] = {oid: [] for oid in requested}
    for slot in range(max((len(parents_table[oid]) for oid in requested), default=0)):
        batch = [oid for oid in requested if slot < len(parents_table[oid])]
        try:
            raw = _git(
                "diff-tree", "--stdin", "--no-renames", "-r", "--name-only",
                "-z", "--diff-filter=ACMRDTUXB", "--always",
                input_text="".join(f"{oid} {parents_table[oid][slot]}\n" for oid in batch),
            )
            parsed = _parse_path_batch(raw, batch)
        except (RuntimeError, OSError, UnicodeError, ValueError):
            return None
        if parsed is None:
            return None
        for oid in batch:
            result[oid].append(set(parsed[oid]))
    return result


def _paths_changed_from(parent: str, commit: str) -> set[str]:
    raw = _git(
        "diff", "--no-renames", "--name-only",
        "--diff-filter=ACMRDTUXB", "-z", parent, commit, "--",
    )
    return set(_nul_paths(raw))


def _combined_diff_paths(commit: str, candidates: list[str]) -> list[str]:
    """candidates のうち、merge の combined diff が自明でない (patch 本体が空でない) ものだけ返す。

    patch 本体の空判定を使う。`--exit-code` は combined diff の自明性を反映しないため使わない
    (真の衝突解消 merge でも rc=0 を返すことを実測で確認済み)。
    raw bytes のまま判定し、UTF-8 decode を行わない — git の combined-diff compaction が
    マルチバイト文字や不正な UTF-8 バイト列の途中で出力を打ち切ることがあり、text mode では
    UnicodeDecodeError になるため。
    """
    retained: list[str] = []
    for path in candidates:
        result = subprocess.run(
            [
                "git", "--literal-pathspecs", "diff-tree", "--cc", "--no-renames",
                "--no-commit-id", "-p",
                commit, "--", path,
            ],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"git diff-tree --cc failed for {commit} -- {path}: "
                f"rc={result.returncode} {detail}"
            )
        if result.stdout != b"":
            retained.append(path)
    return retained


def _paths_changed_from_index(parent: str) -> set[str]:
    raw = _git(
        "diff", "--cached", "--no-renames", "--name-only",
        "--diff-filter=ACMRDTUXB", "-z", parent, "--",
    )
    return set(_nul_paths(raw))


def _intersection_path_set(path_sets: list[set[str]]) -> list[str]:
    if not path_sets:
        raise RuntimeError("combined path calculation requires at least one parent")
    return sorted(set.intersection(*path_sets))


def _commit_paths(
    commit: str, *, parents: tuple[str, ...] | None = None,
    parent_paths: list[set[str]] | None = None,
) -> list[str]:
    """non-merge は従来差分、merge は combined diff が自明でない候補 path だけを返す。"""
    if parents is None:
        parents = _commit_parents(commit)
    if len(parents) <= 1:
        raw = _git(
            "diff-tree", "--root", "--no-renames", "--no-commit-id",
            "--name-only", "-r", "-z", commit,
        )
        return _nul_paths(raw)
    if parent_paths is None:
        parent_paths = [_paths_changed_from(parent, commit) for parent in parents]
    candidates = _intersection_path_set(parent_paths)
    if not candidates:
        return []
    return _combined_diff_paths(commit, candidates)


def _staged_paths() -> list[str]:
    raw = _git(
        "diff", "--cached", "--no-renames", "--name-only",
        "--diff-filter=ACMRDTUXB", "-z",
    )
    return _nul_paths(raw)


def _merge_preflight_parents() -> list[str]:
    """MERGE_HEAD 不在は通常 preflight、存在時は prospective parents を返す。"""
    git_path = _git("rev-parse", "--git-path", "MERGE_HEAD").strip()
    if not git_path:
        raise RuntimeError("git rev-parse --git-path MERGE_HEAD returned empty path")
    merge_head_path = Path(git_path)
    if not merge_head_path.is_absolute():
        merge_head_path = REPO / merge_head_path
    try:
        raw = merge_head_path.read_text(encoding="ascii")
    except FileNotFoundError:
        return []
    merge_heads = raw.splitlines()
    if (
        not merge_heads
        or any(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None
               for oid in merge_heads)
        or len(set(merge_heads)) != len(merge_heads)
    ):
        raise RuntimeError("MERGE_HEAD is malformed")
    for oid in merge_heads:
        if not _commit_exists(oid):
            raise RuntimeError(f"MERGE_HEAD parent commit object is missing: {oid}")

    head = _git("rev-parse", "--verify", "HEAD^{commit}").strip()
    return [head, *merge_heads]


def _message_file_paths(merge_parents: list[str]) -> list[str]:
    if not merge_parents:
        return _staged_paths()
    return _intersection_path_set([
        _paths_changed_from_index(parent) for parent in merge_parents
    ])


def _policy_commit(head: str | None = None) -> str:
    tip = head or "HEAD"
    commits = _git(
        "log", "--full-history", "--no-renames", "--diff-filter=A",
        "--format=%H", tip, "--", POLICY_PATH,
    ).splitlines()
    if not commits:
        raise RuntimeError(
            f"{POLICY_PATH} の導入 commit が履歴にない。"
            "commit 前は --message-file で検査すること"
        )
    if len(commits) != 1:
        raise RuntimeError(
            f"{POLICY_PATH} の導入 commit が一意でない: "
            f"hits={len(commits)}"
        )
    return commits[0]


def _commit_range(
    rev_range: str | None, *, head: str | None = None,
) -> list[str]:
    if rev_range is None:
        if head is None:
            raise RuntimeError("authoritative history requires a pinned HEAD")
        policy = _policy_commit(head)
        commits = _git(
            "rev-list", "--reverse", f"{policy}..{head}"
        ).splitlines()
        return [policy, *commits]
    return _git("rev-list", "--reverse", rev_range).splitlines()


def _resolve_head() -> str:
    head = _git("rev-parse", "HEAD").strip()
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) is None:
        raise RuntimeError(f"git rev-parse HEAD returned invalid SHA: {head!r}")
    return head


def _assert_head_unchanged(start_head: str) -> None:
    end_head = _git("rev-parse", "HEAD").strip()
    if end_head != start_head:
        raise RuntimeError(
            "HEAD が監査中に変化した: "
            f"start={start_head}, end={end_head}"
        )


def _assert_authoritative_repository() -> None:
    shallow = _git("rev-parse", "--is-shallow-repository").strip()
    if shallow != "false":
        raise RuntimeError(
            "authoritative history is unavailable in a shallow repository"
        )

    grafts = Path(_git("rev-parse", "--git-path", "info/grafts").strip())
    if not grafts.is_absolute():
        grafts = REPO / grafts
    try:
        graft_bytes = grafts.read_bytes()
    except FileNotFoundError:
        graft_bytes = b""
    if graft_bytes.strip():
        raise RuntimeError(
            f"authoritative history is unavailable with grafts: {grafts}"
        )

    replacements = _git("replace", "--list").splitlines()
    if replacements:
        raise RuntimeError(
            "authoritative history is unavailable with git replace"
        )


def _read_message(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text()


def AUDIT_WORKERS() -> int:
    """履歴監査の既定並列度 (module 属性。テストは monkeypatch で差し替える)。

    site 由来にして計算ノードの割り当て資源を使い切る。available_cpus() は
    cgroup / affinity を尊重する。env による上書きは作らない (D103 却下項目)。
    """
    return max(1, min(site_policy.available_cpus(), AUDIT_WORKERS_CAP))


@dataclass(frozen=True)
class _Ancestry:
    """選択集合の祖先閉包を bitset で持ち、git subprocess を per-commit で焼かない。

    index は閉包全体 (選択集合の祖先すべて) を覆う。bits[i] は i 自身を含む祖先
    集合で、反射性は merge-base --is-ancestor A A (rc=0) と一致させるためにある。
    """

    index: dict[str, int]
    bits: tuple[int, ...]
    cab_policy_mask: int
    cab_policy_ancestor_mask: int = 0
    parents: dict[str, tuple[str, ...]] | None = None

    def is_descendant(self, ancestor: str, commit: str) -> bool:
        i = self.index.get(commit)
        j = self.index.get(ancestor)
        if i is None or j is None:
            return False
        return bool(self.bits[i] >> j & 1)

    def has_cab_policy(
        self,
        commit: str,
        *,
        authoritative: bool = False,
    ) -> bool:
        i = self.index.get(commit)
        # CAB seed が一度も導入されていない repo では、空集合に対する
        # 「どの seed の祖先でもない」は数式上真でも、規則自体を適用しない。
        if i is None or not self.cab_policy_mask:
            return False
        if self.bits[i] & self.cab_policy_mask:
            return True
        return authoritative and not bool(self.cab_policy_ancestor_mask & (1 << i))


def _build_ancestry(
    commits: list[str],
    *,
    authoritative: bool = False,
    head: str | None = None,
) -> _Ancestry:
    """rev-list 1 本 + pickaxe 1 本で per-commit の lineage 判定を畳む。

    --topo-order が必須 (既定の commit-date 順では逆順走査で親が未確定になりうる)。
    pickaxe は --full-history が履歴簡約を無効化し -S が親との diff で commit ごとに
    独立判定するため tip 非依存であり、ヒット集合は P ∩ ancestors(commit) になる。
    argv 前置 ("log", "--full-history", "--no-renames", "--format=%H") は
    既存 intercept テストの契約なので保存する。
    """
    if authoritative and head is None:
        raise RuntimeError("authoritative ancestry requires a pinned HEAD")

    raw = _git(
        "rev-list", "--topo-order", "--parents", "--stdin",
        input_text="".join(f"{commit}\n" for commit in commits),
    )
    rows = [line.split() for line in raw.splitlines()]
    index = {row[0]: n for n, row in enumerate(reversed(rows))}
    bits = [0] * len(rows)
    for row in reversed(rows):
        i = index[row[0]]
        acc = 1 << i
        for parent in row[1:]:
            j = index.get(parent)
            if j is not None:  # 閉包外は shallow / graft 境界だけ
                acc |= bits[j]
        bits[i] = acc
    tips = [head] if authoritative else commits
    policy_hits = _git(
        "log", "--full-history", "--no-renames", "--format=%H",
        "-S", CO_AUTHORED_BY_POLICY_NEEDLE, *tips, "--", POLICY_PATH,
    ).splitlines()
    mask = 0
    ancestor_mask = 0
    for sha in policy_hits:
        j = index.get(sha)
        if j is not None:
            mask |= 1 << j
            ancestor_mask |= bits[j]
    # This is an optional cache: malformed rows must not change the existing
    # ancestry calculation or its exceptions. Require a complete, ordered closure.
    parents = {row[0]: tuple(row[1:]) for row in rows}
    tokens = [token for row in rows for token in row]
    if (
        not raw.endswith("\n")
        or any(not line.strip() for line in raw.splitlines())
        or any(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", token) is None
               for token in tokens)
        or len({len(token) for token in tokens}) != 1
        or len(parents) != len(rows)
        or not set(commits).issubset(parents)
        or parents.keys() != index.keys()
        or any(parent not in index or index[parent] >= index[commit]
               for commit, row_parents in parents.items() for parent in row_parents)
    ):
        parents = None
    return _Ancestry(index, tuple(bits), mask, ancestor_mask, parents)


def _base_finding_ledger_kind(label: str, finding: str) -> str | None:
    if finding == f"{label}: AI-Agent trailer がない":
        return MISSING_AI_AGENT
    if finding.startswith(f"{label}: AI-Agent の形式違反: "):
        return MALFORMED_AI_AGENT
    return None


def _normal_commit_audit(
    commit: str,
    *,
    scope_epoch: str | None,
    implementation_epoch: str | None,
    ancestry: _Ancestry | None = None,
    commit_message: _CommitMessage | None = None,
    nonmerge_paths: dict[str, list[str]] | None = None,
    merge_parent_paths: dict[str, list[set[str]]] | None = None,
    authoritative: bool = False,
) -> CommitAudit:
    """ancestry=None は逐次 oracle 経路 (merge-base / per-commit pickaxe)。

    bitset 版と同じ判定を独立実装で持つため、等価性テストが自己参照にならない。
    """
    if ancestry is None and authoritative:
        raise RuntimeError(
            "authoritative normal audit requires an ancestry index"
        )

    if commit_message is None:
        subject = _git("show", "-s", "--format=%s", commit).strip()
        message = _git("show", "-s", "--format=%B", commit)
    else:
        subject = commit_message.subject
        message = commit_message.message
    label = f"{commit[:12]} {subject}"
    if ancestry is None:
        cab_policy_applies = _has_co_authored_by_policy(commit)

        def descends(ancestor: str) -> bool:
            return _is_descendant(ancestor, commit)
    else:
        cab_policy_applies = ancestry.has_cab_policy(
            commit, authoritative=authoritative,
        )

        def descends(ancestor: str) -> bool:
            return ancestry.is_descendant(ancestor, commit)

    shared_values = {} if ancestry is None else {"values": _ai_agent_values(message)}
    base, scoped, cab = validate_message(
        label, message, check_cab=cab_policy_applies, **shared_values,
    )
    findings = [
        NormalFinding(
            finding,
            _base_finding_ledger_kind(label, finding),
        )
        for finding in base
    ]

    def applies_epoch(epoch: str | None) -> bool:
        # 規則がこの履歴に存在しない epoch=None は、空虚な第2項を
        # 真として扱わず、常に非適用とする。
        if epoch is None:
            return False
        return descends(epoch) or (
            authoritative and not descends_from_commit(epoch)
        )

    def descends_from_commit(epoch: str) -> bool:
        if ancestry is None:
            return _is_descendant(commit, epoch)
        return ancestry.is_descendant(commit, epoch)

    if scoped and applies_epoch(scope_epoch):
        findings.extend(NormalFinding(finding, None) for finding in scoped)
    findings.extend(NormalFinding(finding, None) for finding in cab)
    waiver = EMPTY_WAIVER
    waived_applied = False
    if applies_epoch(implementation_epoch):
        waiver = _waiver_audit(label, message)
        findings.extend(
            NormalFinding(finding, None) for finding in waiver.findings
        )
        if ancestry is not None and authoritative:
            parents = ancestry.parents.get(commit) if ancestry.parents is not None else None
            paths = nonmerge_paths.get(commit) if nonmerge_paths is not None else None
            if paths is None:
                paths = _commit_paths(
                    commit, parents=parents,
                    parent_paths=(merge_parent_paths.get(commit)
                                  if merge_parent_paths is not None else None),
                )
        else:
            paths = _commit_paths(commit)
        implementation, waived_applied = validate_implementation_author(
            label, message, paths, waived=waiver.exact, **shared_values,
        )
        findings.extend(
            NormalFinding(finding, MISSING_CODEX_AUTHOR)
            for finding in implementation
        )
    return CommitAudit(
        commit=commit,
        label=label,
        normal_findings=tuple(findings),
        correction=_correction_audit(label, message),
        waiver=waiver,
        waived_applied=waived_applied,
    )


def _known_violation_audit(
    audits: list[CommitAudit],
    *,
    registry: dict[
        str, KnownViolationSpec | tuple[KnownViolationSpec, ...]
    ],
    suppressed_missing: tuple[str, str] | None,
    stale_eligible_commits: set[str],
    authoritative: bool = False,
) -> KnownViolationAudit:
    """correction / waiver 適用後の finding を固定台帳と照合する。"""

    findings: list[str] = []
    known_violations: list[KnownViolationSpec] = []
    specs_by_commit = {
        commit: (
            (value,)
            if isinstance(value, KnownViolationSpec)
            else value
        )
        for commit, value in registry.items()
    }
    expected_kind_counts = {
        spec: 0
        for commit, specs in specs_by_commit.items()
        if commit in stale_eligible_commits
        for spec in specs
    }
    consumed_registry_entries: set[KnownViolationSpec] = set()
    for audit in audits:
        for finding in audit.normal_findings:
            if suppressed_missing == (audit.commit, finding.text):
                continue
            for spec_for_commit in specs_by_commit.get(audit.commit, ()):
                if spec_for_commit in consumed_registry_entries:
                    continue
                if (
                    finding.ledger_kind == spec_for_commit.expected_finding_kind
                    and (
                        not spec_for_commit.expected_finding_value
                        or finding.text.startswith(
                            f"{audit.label}: AI-Agent の形式違反: "
                            f"{spec_for_commit.expected_finding_value!r} — "
                        )
                    )
                ):
                    if spec_for_commit in expected_kind_counts:
                        expected_kind_counts[spec_for_commit] += 1
                    known_violations.append(spec_for_commit)
                    consumed_registry_entries.add(spec_for_commit)
                    break
            else:
                findings.append(finding.text)
    stale = tuple(
        spec
        for commit in specs_by_commit
        for spec in specs_by_commit[commit]
        if spec in expected_kind_counts
        and expected_kind_counts[spec] == 0
    )
    return KnownViolationAudit(
        tuple(findings), tuple(known_violations), stale,
    )


def _ledger_policy_is_visible(
    spec: KnownViolationSpec,
    *,
    implementation_epoch: str | None,
    ancestry: _Ancestry,
    authoritative: bool = False,
) -> bool:
    """期待 finding の policy epoch を current HEAD から検証できるか。"""

    if spec.expected_finding_kind in {
        MISSING_AI_AGENT,
        MALFORMED_AI_AGENT,
    }:
        return True
    if spec.expected_finding_kind == MISSING_CODEX_AUTHOR:
        return (
            implementation_epoch is not None
            and (
                ancestry.is_descendant(implementation_epoch, spec.commit)
                or (
                    authoritative
                    and not ancestry.is_descendant(spec.commit, implementation_epoch)
                )
            )
        )
    raise RuntimeError(
        "known provenance violation registry has invalid finding kind: "
        f"{spec.expected_finding_kind!r}"
    )


_RECEIPT_SCHEMA = 1
_RECEIPT_DIRECTORY = "provenance-audit-receipts"
_RECEIPT_LIMIT = 64


def _receipt_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")).hexdigest()


def _system_attributes_path():
    """Resolve the attribute input, without attesting the Git executable."""
    result = subprocess.run(
        ["git", "var", "GIT_ATTR_SYSTEM"], cwd=REPO,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode == 0:
        return os.fsdecode(result.stdout).rstrip("\n")
    # Older Git lacks this var. Absolute compiled-in paths need no runtime
    # prefix expansion. Unknown/relocatable builds conservatively miss cache.
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("cannot resolve system attributes")
    paths = {os.fsdecode(item) for item in Path(executable).read_bytes().split(b"\0")
             if item.startswith(b"/") and item.endswith(b"/gitattributes")
             and b"\n" not in item}
    if len(paths) != 1:
        raise RuntimeError("cannot resolve system attributes")
    return paths.pop()


def _attribute_fingerprint(head):
    """Bind worktree/index and local/global/system attribute inputs, independent of tip.

    Untracked directories containing no tracked files are not enumerated for
    .gitattributes discovery.
    """
    attribute_paths = {b".gitattributes"}

    def add_ancestors(path):
        directory = path.rpartition(b"/")[0]
        while directory:
            attribute_paths.add(directory + b"/.gitattributes")
            directory = directory.rpartition(b"/")[0]

    def file_bytes(path):
        path = Path(path)
        if not path.is_absolute():
            path = REPO / path
        try:
            mode = stat.S_IFMT(path.lstat().st_mode)
        except FileNotFoundError:
            return {"kind": "absent"}
        except OSError as error:
            return {"kind": "unreadable", "errno": error.errno}
        source = {"kind": mode}
        try:
            if stat.S_ISLNK(mode):
                source["link"] = os.fsencode(os.readlink(path)).hex()
            elif stat.S_ISREG(mode):
                source["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            source["unreadable"] = error.errno
        return source

    info = _git("rev-parse", "--git-path", "info/attributes").rstrip("\n")
    configured = subprocess.run(
        ["git", "config", "--path", "--get", "-z", "core.attributesFile"],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if configured.returncode not in (0, 1):
        raise RuntimeError("cannot resolve core.attributesFile")
    if configured.returncode == 1:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        home = os.environ.get("HOME")
        default = (Path(xdg) / "git/attributes" if xdg else
                   Path(home) / ".config/git/attributes" if home else None)
        external = {"unset": True, "default":
                    {"unresolved": True} if default is None else file_bytes(default)}
    else:
        external = {"unset": False, "file":
                    file_bytes(os.fsdecode(configured.stdout[:-1]))}

    index = subprocess.run(
        ["git", "ls-files", "--stage", "-z"], cwd=REPO,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout
    indexed = []
    for entry in index.split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            add_ancestors(name)
            if name.rsplit(b"/", 1)[-1] == b".gitattributes":
                indexed.append([name.hex(), metadata.decode("ascii")])
                attribute_paths.add(name)
    # Probe only directories on index paths (plus the repository root). This includes
    # untracked attributes along those paths without walking ignored outputs or
    # submodule contents, and follows directory symlinks as Git does.
    working = [[name.hex(), file_bytes(os.fsdecode(name))]
               for name in sorted(attribute_paths)]
    return _receipt_digest({"info": file_bytes(info),
                            "configured": external, "index": sorted(indexed),
                            "working": working,
                            "system": file_bytes(_system_attributes_path())})


def _receipt_bindings(head, scope_epoch, implementation_epoch, ancestry):
    """Writer and reader share one OS user; receipts are no tamper barrier.
    Attribute, environment, registry, or checker changes require the full audit.
    Object storage and runtime versions are not attested.
    """
    common = Path(_git("rev-parse", "--git-common-dir").strip())
    if not common.is_absolute():
        common = REPO / common
    common = common.resolve()
    environment = {
        "checker": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "schema": _RECEIPT_SCHEMA,
        "config": _git("config", "--list"),
        "inherited": {key: value for key, value in os.environ.items()
                      if key.startswith(("GIT_", "LC_")) or key == "LANG"},
    }
    entries = _known_violation_head_entries(
        _KNOWN_VIOLATION_REPO_ROOT,
        _resolve_known_violation_head(_KNOWN_VIOLATION_REPO_ROOT),
    )
    manifest = [[name, mode.decode("ascii"), oid.decode("ascii")]
                for name, (mode, oid) in sorted(entries.items())]
    bindings = {
        "environment": environment,
        "repository": str(common),
        "object_format": _git("rev-parse", "--show-object-format").strip(),
        "policy": _policy_commit(head),
        "scope_epoch": scope_epoch,
        "implementation_epoch": implementation_epoch,
        "cab_hits": sorted(oid for oid, i in ancestry.index.items()
                           if ancestry.cab_policy_mask & (1 << i)),
        "registry_manifest": _receipt_digest(manifest),
        "attributes": _attribute_fingerprint(head),
    }
    return common / _RECEIPT_DIRECTORY / (
        _receipt_digest(environment)) / (head + ".json"), bindings


def _partition_receipts(path):
    return path.parent.glob("*.json")


def _prune_audit_receipts(path, head, ancestry):
    # 64 tips cover several generations of 20+ concurrent waves while bounding
    # lookup and storage per environment. Only regular receipt files are pruned.
    saved = []
    for candidate in _partition_receipts(path):
        try:
            info = candidate.lstat()
            if stat.S_ISREG(info.st_mode):
                receipt = _read_audit_receipt(candidate)
                tip = receipt.get("tip") if isinstance(receipt, dict) else None
                ancestor = (isinstance(tip, str)
                            and ancestry.is_descendant(tip, head))
                saved.append((ancestor, info.st_mtime_ns, candidate.name, candidate))
        except FileNotFoundError:
            continue
    for _, _, _, candidate in sorted(saved)[:-_RECEIPT_LIMIT]:
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def _read_audit_receipt(path: Path):
    """A cache miss has no diagnostic or authority; the full oracle decides."""
    try:
        directory = path.parent.lstat()
        if not stat.S_ISDIR(directory.st_mode) or stat.S_IMODE(directory.st_mode) != 0o700:
            return None
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
                return None
            return json.load(stream)
    except (OSError, ValueError, UnicodeError, RecursionError):
        return None


def _publish_audit_receipt(state: dict) -> None:
    """Writer and reader share one OS user; this is no tamper barrier.
    Attribute, environment, registry, or checker changes require the full audit.
    Only rc=0 publishes; failed persistence never reruns the audit.
    """
    if not state:
        return
    temporary = None
    try:
        path, receipt = state["path"], state["receipt"]
        _assert_head_unchanged(receipt["tip"])
        # Do not publish under bindings that changed during the audit.
        _, current = _receipt_bindings(
            receipt["tip"], receipt["bindings"]["scope_epoch"],
            receipt["bindings"]["implementation_epoch"], state["ancestry"],
        )
        if current != receipt["bindings"]:
            return
        path.parent.parent.mkdir(mode=0o700, exist_ok=True)
        path.parent.mkdir(mode=0o700, exist_ok=True)
        info = path.parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
            return
        fd, name = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(receipt, stream, sort_keys=True, ensure_ascii=True)
            stream.flush()
            os.fsync(stream.fileno())
        _assert_head_unchanged(receipt["tip"])
        os.replace(temporary, path)
        temporary = None
        _prune_audit_receipts(path, receipt["tip"], state["ancestry"])
    except (OSError, RuntimeError, ValueError, UnicodeError, subprocess.CalledProcessError):
        pass
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass


def _registry_specs(registry, selected):
    return tuple(spec for oid, value in registry.items() if oid in selected
                 for spec in ((value,) if isinstance(value, KnownViolationSpec) else value))


def _receipt_prefix(receipt, bindings, commits, head, ancestry, registry):
    """Validate every saved input and the complete successful prefix result."""
    try:
        if (not isinstance(receipt, dict)
                or set(receipt) != {"schema", "returncode", "bindings", "tip",
                                    "selection", "coverage", "candidate_count", "records"}
                or type(receipt["schema"]) is not int
                or receipt["schema"] != _RECEIPT_SCHEMA
                or type(receipt["returncode"]) is not int
                or receipt["returncode"] != 0
                or receipt["bindings"] != bindings):
            return None
        tip = receipt["tip"]
        if (not isinstance(tip, str)
                or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", tip) is None
                or _git("cat-file", "-t", tip).strip() != "commit"
                or not _is_descendant(tip, head)):
            return None
        prefix = [oid for oid in commits if ancestry.is_descendant(oid, tip)]
        if (not isinstance(receipt["selection"], dict)
                or type(receipt["selection"].get("count")) is not int
                or receipt["selection"] != {
                    "digest": _receipt_digest(sorted(prefix)), "count": len(prefix),
                }):
            return None
        delta = _git("rev-list", "--reverse", f"{tip}..{head}").splitlines()
        delta_set = set(delta)
        if delta_set != set(commits) - set(prefix) or len(delta) != len(delta_set):
            return None
        records = receipt["records"]
        if set(records) != {"findings", "corrected", "waived", "known_violations"} or records["findings"] != []:
            return None
        history = HistoryAudit(
            [], [ForwardCorrected(**record) for record in records["corrected"]],
            [ImplementationWaived(**record) for record in records["waived"]],
            tuple(KnownViolationSpec(**record) for record in records["known_violations"]),
        )
        # Round-trip rejects extra/missing fields; all public payloads are strings.
        if _receipt_digest(asdict(history)) != _receipt_digest(records):
            return None
        if any(not isinstance(value, str) for group in (
                history.corrected, history.waived, history.known_violations)
                for record in group for value in asdict(record).values()):
            return None
        eligible = _registry_specs(registry, set(prefix))
        keys = sorted([list(_known_violation_key(spec)) for spec in eligible])
        if (receipt["coverage"] != {"eligible": keys, "matched": keys}
                or set(history.known_violations) != set(eligible)
                or len(history.known_violations) != len(eligible)):
            return None
        count = receipt["candidate_count"]
        if type(count) is not int or count not in (0, 1) or count != len(history.corrected):
            return None
        if any(record.target not in prefix or record.correction not in prefix
               for record in history.corrected):
            return None
        if any(record.label not in prefix for record in history.waived):
            return None
        return prefix, [oid for oid in commits if oid in delta_set], history, count
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, UnicodeError):
        return None


def _audit_history(
    commits: list[str],
    *,
    authoritative: bool = False,
    head: str | None = None,
    receipt_state: dict | None = None,
) -> HistoryAudit:
    """selected revision set を順序非依存の membership/lineage 条件で監査する。"""
    if not commits and not authoritative:
        return HistoryAudit([], [], [])
    registry = _known_violation_registry()
    if authoritative:
        if head is None:
            raise RuntimeError("authoritative history requires a pinned HEAD")
        scope_epoch = _scope_policy_commit(head)
        implementation_epoch = _implementation_policy_commit(head)
    else:
        # Explicit --range の既存 monkeypatch seam は zero-arg 呼出しを契約と
        # する。None を明示的に渡すと preflight の回帰になるため分岐を保つ。
        scope_epoch = _scope_policy_commit()
        implementation_epoch = _implementation_policy_commit()
    ancestry = _build_ancestry(
        [head] if authoritative else commits,
        authoritative=authoritative,
        head=head,
    )
    if authoritative:
        _isolated_parsed_trailers("provenance parser canary\n\nAI-Agent: none\n", no_divider=True)
    path = bindings = reuse = None
    if authoritative and receipt_state is not None:
        receipt_state.clear()
        try:
            path, bindings = _receipt_bindings(head, scope_epoch, implementation_epoch, ancestry)
            # Rank using the existing HEAD closure, before prefix validation.
            selected_mask = 0
            for oid in commits:
                selected_mask |= 1 << ancestry.index[oid]
            candidates = []
            for candidate in sorted(_partition_receipts(path)):
                receipt = _read_audit_receipt(candidate)
                tip = receipt.get("tip") if isinstance(receipt, dict) else None
                if not isinstance(tip, str) or not ancestry.is_descendant(tip, head):
                    continue
                distance = (selected_mask & ~ancestry.bits[ancestry.index[tip]]).bit_count()
                candidates.append((distance, candidate.name, receipt))
            for _, _, receipt in sorted(candidates, key=lambda item: item[:2]):
                prefix = _receipt_prefix(
                    receipt, bindings, commits, head, ancestry, registry,
                )
                if prefix is not None:
                    reuse = prefix
                    break
        except (OSError, RuntimeError, ValueError, UnicodeError, subprocess.CalledProcessError):
            pass
    selected = commits if reuse is None else reuse[1]
    messages = _batch_commit_messages(selected) if ancestry is not None else None
    if reuse is not None:
        # A raw candidate anywhere in D requires the full set-wide correction oracle.
        try:
            if messages is None or any(RAW_AI_AGENT_CORRECTION.search(record.message)
                                       for record in messages.values()):
                reuse = None
        except (RuntimeError, UnicodeError):
            reuse = None
        if reuse is None:
            selected = commits
            messages = _batch_commit_messages(selected)

    nonmerge_paths = merge_parent_paths = None
    if authoritative and ancestry is not None and ancestry.parents is not None:
        parents_table = ancestry.parents
        requested = list(dict.fromkeys(selected))
        nonmerge_paths = _batch_nonmerge_paths([
            oid for oid in requested if oid in parents_table and len(parents_table[oid]) <= 1
        ])
        if _merge_path_batch_enabled():
            merge_parent_paths = _batch_merge_parent_paths(
                [oid for oid in requested if oid in parents_table and len(parents_table[oid]) > 1],
                parents_table,
            )

    def audit_one(commit: str) -> CommitAudit:
        return _normal_commit_audit(
            commit,
            scope_epoch=scope_epoch,
            implementation_epoch=implementation_epoch,
            ancestry=ancestry,
            commit_message=messages[commit] if messages is not None else None,
            nonmerge_paths=nonmerge_paths,
            merge_parent_paths=merge_parent_paths,
            authoritative=authoritative,
        )

    workers = max(1, min(AUDIT_WORKERS(), len(selected)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        audits = list(pool.map(audit_one, selected))
    history = _finish_history_audit(
        selected, audits, registry=registry, implementation_epoch=implementation_epoch,
        ancestry=ancestry, authoritative=authoritative,
    )
    candidate_count = sum(audit.correction.candidate_count for audit in audits)
    if reuse is not None:
        prefix, _, inherited, count = reuse
        order = {oid: i for i, oid in enumerate(commits)}
        history = HistoryAudit(
            history.findings, inherited.corrected + history.corrected,
            sorted(inherited.waived + history.waived, key=lambda record: order[record.label]),
            tuple(sorted(inherited.known_violations + history.known_violations,
                         key=lambda record: order[record.commit])),
        )
        candidate_count += count
    if receipt_state is not None and path is not None and bindings is not None and not history.findings:
        keys = sorted([list(_known_violation_key(spec))
                       for spec in _registry_specs(registry, set(commits))])
        receipt_state.update(path=path, ancestry=ancestry, receipt={
            "schema": _RECEIPT_SCHEMA, "returncode": 0, "bindings": bindings,
            "tip": head,
            "selection": {"digest": _receipt_digest(sorted(commits)), "count": len(commits)},
            "coverage": {"eligible": keys, "matched": keys},
            "candidate_count": candidate_count, "records": asdict(history),
        })
    return history


def _finish_history_audit(
    commits, audits, *, registry, implementation_epoch, ancestry, authoritative,
) -> HistoryAudit:
    by_commit = {audit.commit: audit for audit in audits}
    candidate_count = sum(
        audit.correction.candidate_count for audit in audits
    )
    candidate_audits = [
        audit for audit in audits if audit.correction.candidate_count
    ]
    correction_findings = [
        finding
        for audit in audits
        for finding in audit.correction.findings
    ]
    corrected: list[ForwardCorrected] = []
    suppressed_missing: tuple[str, str] | None = None
    spec = INCIDENT_6B64D21_FORWARD_CORRECTION

    if candidate_count and candidate_count != 1:
        correction_findings.append(
            "check_ai_provenance: AI-Agent-Correction は selected revision set 内 "
            f"exact 1 件でなければならない: candidates={candidate_count}"
        )
    elif candidate_count == 1:
        correction = candidate_audits[0]
        target = by_commit.get(spec.target)
        target_selected = target is not None
        strict_descendant = (
            target_selected
            and correction.commit != spec.target
            and _is_descendant(spec.target, correction.commit)
        )
        target_missing = (
            f"{target.label}: AI-Agent trailer がない"
            if target is not None
            else None
        )
        if not target_selected:
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction target が "
                "selected revision set にない"
            )
        elif not strict_descendant:
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction commit が "
                "target の strict descendant でない"
            )
        if (
            target is not None
            and target_missing not in {
                finding.text for finding in target.normal_findings
            }
        ):
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction target に "
                "AI-Agent trailer の実欠落がない"
            )

        carrier_ready = (
            correction.correction.exact
            and target_selected
            and strict_descendant
            and target is not None
            and target_missing in {
                finding.text for finding in target.normal_findings
            }
            and not correction.normal_findings
        )
        if (
            carrier_ready
            # waiver 行を持つ commit は前方訂正の担い手になれない。免除は
            # normal_findings を空にできるので、これが無いと waiver 1 行で
            # 「自身の通常 green」の連言が緩み受理集合が広がる。
            and not correction.waiver.exact
        ):
            suppressed_missing = (spec.target, target_missing)
            corrected.append(ForwardCorrected(spec.target, correction.commit))
        elif carrier_ready:
            # 規律 3: 失格を沈黙させない。この経路で出るのは target 側の
            # 「AI-Agent trailer がない」だけなので、理由が無いと運用者は
            # correction をもう 1 件足そうとして exact 1 件規則に当たる。
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction commit が "
                "AI-Agent-Waiver 行を持つため前方訂正の担い手になれない"
            )

    selected = set(commits)
    stale_eligible_commits = selected.intersection(registry)
    ledger_audit = _known_violation_audit(
        audits,
        registry=registry,
        suppressed_missing=suppressed_missing,
        stale_eligible_commits=stale_eligible_commits,
        authoritative=authoritative,
    )
    if ledger_audit.stale:
        details = ", ".join(
            f"sha={spec.commit} finding={spec.expected_finding_kind} "
            "reason="
            + (
                "expected-finding-missing checker-regression-suspected"
                if _ledger_policy_is_visible(
                    spec,
                    implementation_epoch=implementation_epoch,
                    ancestry=ancestry,
                    authoritative=authoritative,
                )
                else "policy-epoch-not-visible non-authoritative-invocation"
            )
            for spec in ledger_audit.stale
        )
        raise RuntimeError(f"known-violation-stale: {details}")
    findings = list(ledger_audit.findings)
    findings.extend(correction_findings)
    waived = [
        ImplementationWaived(audit.commit, audit.waiver.reason, audit.waiver.ratified)
        for audit in audits
        if audit.waived_applied
    ]
    return HistoryAudit(
        findings, corrected, waived, ledger_audit.known_violations,
    )


def _commit_exists(commit: str) -> bool:
    query = f"{commit}^{{commit}}"
    proc = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=REPO,
        input=f"{query}\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(
            "git cat-file --batch-check failed "
            f"(rc={proc.returncode}): {detail}"
        )
    record = proc.stdout.removesuffix("\n")
    if record == f"{query} missing":
        return False
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64}) commit", record):
        return True
    raise RuntimeError(
        "git cat-file --batch-check returned unexpected record: "
        f"{record!r}"
    )


def _message_file_correction_findings(
    label: str,
    correction: CorrectionAudit,
    merge_parents: list[str],
) -> list[str]:
    """prospective parent 集合だけを仮定する非権威な correction preflight。"""
    findings = list(correction.findings)
    if correction.candidate_count != 1:
        findings.append(
            f"{label}: AI-Agent-Correction は message-file 内 exact 1 件が必要: "
            f"candidates={correction.candidate_count}"
        )
        return findings

    spec = INCIDENT_6B64D21_FORWARD_CORRECTION
    if not _commit_exists(spec.target):
        findings.append(
            f"{label}: AI-Agent-Correction target commit object が存在しない"
        )
        return findings
    ancestry_tips = merge_parents or ["HEAD"]
    if not any(_is_descendant(spec.target, tip) for tip in ancestry_tips):
        findings.append(
            f"{label}: AI-Agent-Correction target が prospective parent "
            "ancestry にない"
        )

    target_message = _git("show", "-s", "--format=%B", spec.target)
    if _ai_agent_values(target_message):
        findings.append(
            f"{label}: AI-Agent-Correction target に AI-Agent trailer の実欠落がない"
        )

    existing_candidates = 0
    for commit in _git("rev-list", *ancestry_tips).splitlines():
        message = _git("show", "-s", "--format=%B", commit)
        existing_candidates += len(RAW_AI_AGENT_CORRECTION.findall(message))
    if existing_candidates:
        findings.append(
            f"{label}: prospective parent ancestry 全体に既存 "
            "AI-Agent-Correction candidate がある: "
            f"candidates={existing_candidates}"
        )
    return findings


def _dispatch_timeout_overrides(
    *, environ: Mapping[str, str]
) -> dict[str, float]:
    """D612 の opt-in dispatch timeout 上書きを純粋に解釈する。"""

    # tools/mutation_harness.py の同名実装と同値
    # (test_t2337_dispatch_timeout_overrides.py の meta-test で照合する)。
    overrides: dict[str, float] = {}
    for env_name, keyword in (
        (_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE_ENV, "queue_wait_timeout_s"),
        (_DISPATCH_OVERALL_GRACE_OVERRIDE_ENV, "overall_grace_s"),
    ):
        raw_value = environ.get(env_name)
        if not raw_value:
            continue
        value = float(raw_value)
        if (
            not math.isfinite(value)
            or value < 0
            or math.copysign(1.0, value) < 0
        ):
            raise ValueError(f"{env_name} は有限な非負数でなければなりません")
        overrides[keyword] = value
    return overrides


def _default_dispatch(argv: Sequence[str]) -> int:
    from tools.pegasus import dispatch_compute

    dispatch_kwargs = {
        "task": "provenance",
        "repo_root": REPO,
        **_dispatch_timeout_overrides(environ=os.environ),
    }
    return dispatch_compute.dispatch(argv, **dispatch_kwargs)


def _invoke_dispatch(dispatch_fn, argv: Sequence[str]) -> int:
    """dispatcher の想定外例外も top-level infra rc へ一義化する。"""
    selected = _default_dispatch if dispatch_fn is None else dispatch_fn
    try:
        return int(selected(argv))
    except (Exception, KeyboardInterrupt) as exc:
        print(
            f"Pegasus dispatcher を完了できませんでした: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return PEGASUS_DISPATCH_RC


@dataclass(frozen=True)
class _TreeFingerprint:
    digest: str
    summary: tuple[int, ...]


def _tree_and_submodules_fingerprint(repo: Path) -> _TreeFingerprint | None:
    """Hash worktree/index and recursive submodule state; fail closed."""

    repo_path = repo.resolve()
    commands = (
        (
            "status",
            [
                "git", "-C", str(repo_path), "status", "--porcelain=v1", "-z",
                "--untracked-files=all", "--ignore-submodules=none",
            ],
        ),
        (
            "diff",
            [
                "git", "-C", str(repo_path), "diff", "--binary",
                "--no-ext-diff", "HEAD", "--",
            ],
        ),
        (
            "submodule-heads",
            [
                "git", "-C", str(repo_path), "submodule", "status",
                "--recursive",
            ],
        ),
        (
            "submodule-status",
            [
                "git", "-C", str(repo_path), "submodule", "foreach",
                "--recursive", "--quiet",
                "git status --porcelain=v1 -z --untracked-files=all",
            ],
        ),
        (
            "submodule-diff",
            [
                "git", "-C", str(repo_path), "submodule", "foreach",
                "--recursive", "--quiet",
                "git diff --binary --no-ext-diff HEAD --",
            ],
        ),
    )
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    fingerprint = hashlib.sha256()
    summary: list[int] = []
    for label, command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                env=env,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not isinstance(result.stdout, bytes):
            return None
        label_bytes = label.encode("ascii")
        fingerprint.update(len(label_bytes).to_bytes(2, "big"))
        fingerprint.update(label_bytes)
        fingerprint.update(len(result.stdout).to_bytes(8, "big"))
        fingerprint.update(result.stdout)
        summary.append(len(result.stdout))
    return _TreeFingerprint(fingerprint.hexdigest(), tuple(summary))


def _cap_oom_fingerprint_refusal(
    before: _TreeFingerprint | None,
    after: _TreeFingerprint | None,
) -> int:
    if before is None or after is None:
        detail = (
            "local 試行前後の tree / submodule 指紋を安全に取得できませんでした"
            f"（before={'ok' if before is not None else 'failed'}、"
            f"after={'ok' if after is not None else 'failed'}）"
        )
    else:
        detail = (
            "local 試行の前後で tree / submodule 状態が変化しました"
            f"（digest {before.digest[:12]} -> {after.digest[:12]}、"
            f"各状態出力 bytes {before.summary} -> {after.summary}）"
        )
    print(
        "bounded scope が MemoryMax に達しましたが、"
        f"{detail}。自動 fallback せず停止します。git status と "
        "git submodule status --recursive で差分を確認してください。",
        file=sys.stderr,
        flush=True,
    )
    return PEGASUS_DISPATCH_RC


@dataclass(frozen=True)
class _ScopeResult:
    outcome: str
    child_rc: int | None = None


class _ScopeSamples:
    def __init__(self) -> None:
        self.ready = threading.Event()
        self.stop = threading.Event()
        self.attested = False
        self.cgroup: Path | None = None
        self.last_events: tuple[int, int] | None = None
        self.peak_current: int | None = None


@dataclass(frozen=True)
class _ScopeAccounting:
    module: object
    operation: str
    grant: object


_scope_accounting: ContextVar[_ScopeAccounting | None] = ContextVar(
    "provenance_scope_accounting", default=None,
)


def _load_login_headroom():
    """予算 leaf を遅延 import する。"""

    try:
        module = importlib.import_module("orchestrator.campaign.login_headroom")
    except Exception as exc:
        print(
            "login headroom admission を読み込めないため、"
            f"計算ノードへ dispatch します: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return None
    return module


def _evaluate_login_admission(admit_fn, *, min_bytes=None, operation=None):
    loaded = _load_login_headroom()
    if loaded is None:
        return (
            None,
            None,
            _HEADROOM_SHORT,
            "ログインノードの観測余裕=不明 bytes です。",
            None,
        )
    module = loaded
    try:
        if admit_fn is None:
            kwargs = {} if min_bytes is None else {"min_bytes": min_bytes}
            if operation is not None:
                kwargs["operation"] = operation
            decision = module.grant_budget(**kwargs)
        else:
            # 未 land テスト用の旧 admission seam。実運用は grant_budget だけを通る。
            decision = admit_fn(module.MAX_LOCAL_BUDGET_BYTES)
    except (Exception, KeyboardInterrupt) as exc:
        print(
            "login headroom admission を完了できないため、"
            f"計算ノードへ dispatch します: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return (
            module,
            None,
            _HEADROOM_SHORT,
            "ログインノードの観測余裕=不明 bytes です。",
            None,
        )

    if admit_fn is not None and isinstance(decision, tuple) and len(decision) == 2:
        admission, reason = decision
        budget = module.MAX_LOCAL_BUDGET_BYTES if admission is module.Admission.LOCAL else None
    elif isinstance(decision, tuple) and len(decision) == 3:
        admission, budget, reason = decision
    else:
        admission, budget, reason = None, None, "予算 API が不正な結果を返しました。"
    is_local = admission is module.Admission.LOCAL
    if is_local and (type(budget) is not int or budget <= 0):
        is_local = False
        budget = None
    return (
        module,
        budget,
        None if is_local else _HEADROOM_SHORT,
        reason if isinstance(reason, str) else "予算の理由を取得できませんでした。",
        decision,
    )


def _safe_bind_scope(grant, cgroup: Path | None) -> None:
    if grant is None or cgroup is None:
        return
    try:
        bind_scope = getattr(grant, "bind_scope", None)
        if callable(bind_scope):
            bind_scope(cgroup)
    except (Exception, KeyboardInterrupt):
        pass


def _safe_release_grant(grant) -> None:
    if grant is None:
        return
    try:
        release = getattr(grant, "release", None)
        if callable(release):
            release()
    except (Exception, KeyboardInterrupt):
        pass


def _safe_remember_peak(module, operation: str | None, peak: int | None) -> None:
    if module is None or operation is None or peak is None:
        return
    try:
        module.remember_peak(operation, peak)
    except (Exception, KeyboardInterrupt):
        pass


def _queue_dispatch_possible() -> tuple[bool, str]:
    """キュー観測不能は現行どおり dispatch 可へ倒す。"""

    try:
        module = importlib.import_module("orchestrator.campaign.queue_state")
        possible, reason = module.dispatch_possible()
        if type(possible) is not bool or not isinstance(reason, str):
            raise ValueError("invalid queue availability result")
        if not possible and ("ENA=" not in reason or "STS=" not in reason):
            raise ValueError("queue refusal lacks ENA/STS diagnostics")
        return possible, reason
    except (Exception, KeyboardInterrupt):
        return (
            True,
            "キューは ENA=不明、STS=不明です（観測不能のため可用扱い）。",
        )


def _print_granted_budget(cap: int, reason: str) -> None:
    print(
        f"bounded local に与えた予算: {cap} bytes。{reason}",
        file=sys.stderr,
        flush=True,
    )


def _no_execution_capacity(headroom_reason: str, queue_reason: str) -> int:
    print(
        "ログインの余裕もキューも無いため、いまは実行できません。"
        f"観測した余裕: {headroom_reason} {queue_reason}",
        file=sys.stderr,
        flush=True,
    )
    return PEGASUS_DISPATCH_RC


def _parse_unified_cgroup(text: str) -> str:
    matches = []
    for line in text.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[:2] == ["0", ""]:
            matches.append(parts[2])
    if len(matches) != 1:
        raise ValueError("unified cgroup entry is not unique")
    path = matches[0]
    components = path.removeprefix("/").split("/")
    if not path.startswith("/") or any(
        component in {"", ".", ".."} for component in components
    ):
        raise ValueError("unified cgroup path is not normalized")
    return path


def _scope_cgroup_path(proc_cgroup: Path, unit: str) -> Path | None:
    try:
        path = _parse_unified_cgroup(proc_cgroup.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    if Path(path).name != unit:
        return None
    return _CGROUP_ROOT / path.removeprefix("/")


def _scope_properties_are_enforced(cgroup: Path, cap: int) -> bool:
    try:
        memory_max = (cgroup / "memory.max").read_text(encoding="utf-8").strip()
        oom_group = (cgroup / "memory.oom.group").read_text(
            encoding="utf-8",
        ).strip()
    except (OSError, UnicodeError):
        return False
    accepted_memory_max = {str(cap)}
    if cap > 0:
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError):
            pass
        else:
            if type(page_size) is int and page_size > 0:
                accepted_memory_max.add(str(cap - cap % page_size))
    return memory_max in accepted_memory_max and oom_group == "1"


def _attest_scope_oom_group(cgroup: Path) -> bool:
    oom_group = cgroup / "memory.oom.group"
    try:
        oom_group.write_text("1\n", encoding="utf-8")
        attested = oom_group.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return False
    return attested == "1"


def _read_scope_events(cgroup: Path) -> tuple[int, int]:
    parsed = {}
    for line in (cgroup / "memory.events").read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2 or not fields[1].isascii() or not fields[1].isdecimal():
            raise ValueError("malformed memory.events")
        if fields[0] in parsed:
            raise ValueError("duplicate memory.events field")
        parsed[fields[0]] = int(fields[1], 10)
    return parsed["max"], parsed["oom"]


def _read_scope_current(cgroup: Path) -> int:
    raw = (cgroup / "memory.current").read_text(encoding="utf-8").strip()
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError("malformed memory.current")
    return int(raw, 10)


def _bounded_scope_membership() -> bool | None:
    unit = os.environ.get(_BOUNDED_SCOPE_UNIT_ENV)
    raw_cap = os.environ.get(_BOUNDED_SCOPE_CAP_ENV)
    if unit is None and raw_cap is None:
        return None
    if unit is None or raw_cap is None:
        return False
    if re.fullmatch(rf"{re.escape(_BOUNDED_SCOPE_UNIT_PREFIX)}[0-9]+-[0-9a-f]+\.scope", unit) is None:
        return False
    if not raw_cap.isascii() or not raw_cap.isdecimal():
        return False
    cap = int(raw_cap, 10)
    if cap <= 0:
        return False
    cgroup = _scope_cgroup_path(_PROC_SELF_CGROUP, unit)
    return (
        cgroup is not None
        and _attest_scope_oom_group(cgroup)
        and _scope_properties_are_enforced(cgroup, cap)
    )


def _new_scope_unit() -> str:
    return f"{_BOUNDED_SCOPE_UNIT_PREFIX}{os.getpid()}-{secrets.token_hex(8)}.scope"


def _scope_command(argv: Sequence[str], cap: int, unit: str) -> list[str]:
    return [
        "systemd-run", "--user", "--scope", "-q", f"--unit={unit}",
        "-p", "MemoryAccounting=yes",
        "-p", f"MemoryMax={cap}",
        "-p", "MemorySwapMax=0",
        "--", sys.executable, str(Path(__file__).resolve()), *argv,
    ]


def _sample_scope(process, unit: str, cap: int, samples: _ScopeSamples) -> None:
    """走行中だけ cgroup を読み、消滅前の最後の観測を保持する。"""

    deadline = time.monotonic() + _SCOPE_ATTEST_SECONDS
    cgroup = None
    try:
        while not samples.stop.is_set():
            cgroup = _scope_cgroup_path(
                Path("/proc") / str(process.pid) / "cgroup",
                unit,
            )
            if cgroup is not None:
                break
            if process.poll() is not None or time.monotonic() >= deadline:
                return
            time.sleep(_SCOPE_POLL_SECONDS)

        if cgroup is None or not _attest_scope_oom_group(cgroup):
            return
        if not _scope_properties_are_enforced(cgroup, cap):
            return
        samples.cgroup = cgroup
        samples.attested = True

        first_sample = True
        while not samples.stop.is_set():
            current = None
            events = None
            try:
                current = _read_scope_current(cgroup)
            except (OSError, UnicodeError, ValueError):
                pass
            try:
                events = _read_scope_events(cgroup)
            except (OSError, UnicodeError, ValueError, KeyError):
                pass

            if current is not None:
                samples.peak_current = max(
                    current,
                    samples.peak_current if samples.peak_current is not None else 0,
                )
            if events is not None:
                samples.last_events = events
            if first_sample:
                samples.ready.set()
                first_sample = False
            if current is None or events is None:
                return
            time.sleep(_SCOPE_POLL_SECONDS)
    finally:
        samples.ready.set()


def _start_scope_sampler(process, unit: str, cap: int):
    samples = _ScopeSamples()
    thread = threading.Thread(
        target=_sample_scope,
        args=(process, unit, cap, samples),
        name=f"{unit}-sampler",
        daemon=True,
    )
    thread.start()
    return samples, thread


def _stop_bounded_scope(process, unit: str) -> None:
    """attestation 失敗時に scope 全体の停止を試み、runner も回収する。"""

    try:
        subprocess.run(
            ["systemctl", "--user", "stop", unit],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass


def _run_bounded_scope(argv: Sequence[str], cap: int) -> _ScopeResult:
    unit = _new_scope_unit()
    child_env = os.environ.copy()
    child_env[_BOUNDED_SCOPE_UNIT_ENV] = unit
    child_env[_BOUNDED_SCOPE_CAP_ENV] = str(cap)
    try:
        process = subprocess.Popen(
            _scope_command(argv, cap, unit),
            cwd=REPO,
            env=child_env,
        )
    except (OSError, ValueError) as exc:
        print(
            f"bounded scope を起動できませんでした: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult("dispatch_infra")

    samples, sampler = _start_scope_sampler(process, unit, cap)
    samples.ready.wait(_SCOPE_ATTEST_SECONDS + _SCOPE_POLL_SECONDS)
    if not samples.attested:
        samples.stop.set()
        _stop_bounded_scope(process, unit)
        sampler.join(_SCOPE_DRAIN_SECONDS)
        print(
            "bounded scope の memory.max / memory.oom.group を走行中に"
            "attest できないため、scope を停止して dispatcher infrastructure "
            "failure とします。",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult("dispatch_infra")

    accounting = _scope_accounting.get()
    if accounting is not None:
        _safe_bind_scope(accounting.grant, samples.cgroup)

    try:
        rc = process.wait()
    except (OSError, ValueError) as exc:
        samples.stop.set()
        _stop_bounded_scope(process, unit)
        sampler.join(_SCOPE_DRAIN_SECONDS)
        print(
            f"bounded scope の終了を確認できませんでした: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult("dispatch_infra")

    final_events = None
    if _termination_signal(rc) is not None and samples.cgroup is not None:
        try:
            final_events = _read_scope_events(samples.cgroup)
        except (OSError, UnicodeError, ValueError, KeyError):
            pass

    # 正常終了では sampler 自身が cgroup の消滅を観測するまで待つ。ここで stop を
    # 立てると、最後の memory.events を読む直前に観測を打ち切り得る。
    sampler.join()
    if samples.peak_current is not None:
        print(
            f"bounded scope の観測ピーク: {samples.peak_current} bytes",
            file=sys.stderr,
            flush=True,
        )
    if samples.last_events is None:
        print(
            "bounded scope の memory.events を走行中に一度も読めないため、"
            "dispatcher infrastructure failure として停止します。",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult("dispatch_infra")
    if _termination_signal(rc) is not None:
        if final_events is None:
            print(
                "bounded scope は signal で終了しましたが、終了後の "
                "memory.events で cap 到達を証明できないため dispatcher "
                "infrastructure failure とします。",
                file=sys.stderr,
                flush=True,
            )
            return _ScopeResult("dispatch_infra")
        max_delta, oom_delta = final_events
        if max_delta > 0 and oom_delta > 0:
            if accounting is not None:
                _safe_remember_peak(
                    accounting.module,
                    accounting.operation,
                    max(cap, samples.peak_current or 0),
                )
            return _ScopeResult("cap_oom")
        print(
            "bounded scope は signal で終了しましたが、終了後の "
            "memory.events は cap 到達を示さないため dispatcher "
            "infrastructure failure とします。",
            file=sys.stderr,
            flush=True,
        )
        return _ScopeResult("dispatch_infra")
    if accounting is not None:
        _safe_remember_peak(
            accounting.module,
            accounting.operation,
            samples.peak_current,
        )
    return _ScopeResult("child_rc", int(rc))


def _termination_signal(returncode: int) -> int | None:
    signum = -returncode if returncode < 0 else returncode - 128
    if signum <= 0:
        return None
    try:
        return signum if signum in signal.valid_signals() else None
    except (AttributeError, OSError, ValueError):
        return signum if signum == signal.SIGKILL else None


def _launch_local_scope(
    argv: Sequence[str], cap: int, *, module=None, operation=None, grant=None,
):
    accounting = (
        _ScopeAccounting(module, operation, grant)
        if module is not None and operation is not None
        else None
    )
    token = _scope_accounting.set(accounting)
    try:
        return _run_bounded_scope(argv, cap)
    finally:
        _scope_accounting.reset(token)


def main(
    argv: Sequence[str] | None = None,
    *,
    site=None,
    dispatch_fn=None,
    admit_fn=None,
) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-dispatch",
        action="store_true",
        help=(
            "Pegasus LOGIN で headroom/queue 判定を行わず必ず"
            "計算ノードへ dispatch する"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--range", dest="rev_range", help="検査する git revision range")
    group.add_argument(
        "--message-file",
        help="commit 前の message ファイルを検査する。標準入力は -",
    )
    args = parser.parse_args(values)
    dispatch_values = [value for value in values if value != "--force-dispatch"]
    operation = "provenance-range" if args.rev_range is not None else "provenance"

    # site gate は parse_args の後に置き、通常の免除は args.message_file だけで
    # 判定する。明示された force_dispatch はその免除も上書きする。
    # raw token allowlist を移植すると --message-f のような接頭辞省略形が免除から
    # 外れ、commit 直前の preflight が queue 待ちに依存する。
    if args.message_file is None or args.force_dispatch:
        resolved_site = site_policy.current_site() if site is None else site
        if resolved_site not in {
            site_policy.OTHER,
            site_policy.PEGASUS_LOGIN,
            site_policy.PEGASUS_COMPUTE,
            site_policy.PEGASUS_SUSPECT,
        }:
            print(
                "実行 site を安全に分類できないため、provenance 履歴監査を拒否します。",
                file=sys.stderr,
                flush=True,
            )
            return PEGASUS_DISPATCH_RC
        bounded_membership = _bounded_scope_membership()
        if bounded_membership is False:
            print(
                "bounded scope marker と cgroup の memory.max / memory.oom.group が"
                "一致しないため、provenance 履歴監査を拒否します。",
                file=sys.stderr,
                flush=True,
            )
            return PEGASUS_DISPATCH_RC
        if resolved_site == site_policy.PEGASUS_SUSPECT:
            queue_hint = _queue_dispatch_possible()
            print(
                site_policy.heavy_work_refusal(
                    resolved_site, "provenance 履歴監査",
                    queue_hint=queue_hint,
                ),
                file=sys.stderr,
                flush=True,
            )
            return PEGASUS_DISPATCH_RC
        if site_policy.is_pegasus_login(resolved_site):
            if args.force_dispatch:
                return _invoke_dispatch(dispatch_fn, dispatch_values)
            if bounded_membership is None:
                module, cap, admission_outcome, headroom_reason, grant = (
                    _evaluate_login_admission(admit_fn, operation=operation)
                )
                queue_unavailable = False
                queue_reason = ""
                if admission_outcome == _HEADROOM_SHORT:
                    queue_possible, queue_reason = _queue_dispatch_possible()
                    if queue_possible:
                        _safe_release_grant(grant)
                        return _invoke_dispatch(dispatch_fn, dispatch_values)
                    queue_unavailable = True
                    if module is None:
                        return _no_execution_capacity(headroom_reason, queue_reason)
                    _safe_release_grant(grant)
                    module, cap, admission_outcome, headroom_reason, grant = (
                        _evaluate_login_admission(
                            admit_fn, min_bytes=0, operation=operation,
                        )
                    )
                    if admission_outcome == _HEADROOM_SHORT or cap is None:
                        _safe_release_grant(grant)
                        return _no_execution_capacity(headroom_reason, queue_reason)

                if cap is None:
                    _safe_release_grant(grant)
                    return PEGASUS_DISPATCH_RC
                _print_granted_budget(cap, headroom_reason)
                tree_before = _tree_and_submodules_fingerprint(REPO)
                try:
                    scope_result = _launch_local_scope(
                        values,
                        cap,
                        module=module,
                        operation=operation,
                        grant=grant,
                    )
                finally:
                    _safe_release_grant(grant)
                if scope_result.outcome == "child_rc":
                    if scope_result.child_rc is None:
                        return PEGASUS_DISPATCH_RC
                    return scope_result.child_rc
                if scope_result.outcome == "dispatch_infra":
                    return PEGASUS_DISPATCH_RC
                if scope_result.outcome == "cap_oom":
                    tree_after = _tree_and_submodules_fingerprint(REPO)
                    if (
                        tree_before is None
                        or tree_after is None
                        or tree_before != tree_after
                    ):
                        return _cap_oom_fingerprint_refusal(
                            tree_before,
                            tree_after,
                        )
                    if queue_unavailable:
                        return _no_execution_capacity(
                            headroom_reason,
                            queue_reason,
                        )
                    return _invoke_dispatch(dispatch_fn, dispatch_values)
                return PEGASUS_DISPATCH_RC

    try:
        corrected: list[ForwardCorrected] = []
        waived: list[ImplementationWaived] = []
        known_violations: tuple[KnownViolationSpec, ...] = ()
        known_violation_groups: _KnownViolationGroups | None = None
        correction_preflight = False
        merge_preflight = False
        if args.message_file is not None:
            message = _read_message(args.message_file)
            merge_parents = _merge_preflight_parents()
            merge_preflight = bool(merge_parents)
            base, scoped, cab = validate_message(
                args.message_file, message
            )
            waiver = _waiver_audit(args.message_file, message)
            implementation, waived_applied = validate_implementation_author(
                args.message_file, message, _message_file_paths(merge_parents),
                waived=waiver.exact,
            )
            findings = [
                *base, *scoped, *cab, *waiver.findings, *implementation,
            ]
            if waived_applied:
                waived.append(ImplementationWaived(
                    args.message_file, waiver.reason, waiver.ratified,
                ))
            correction = _correction_audit(args.message_file, message)
            if correction.candidate_count:
                findings.extend(_message_file_correction_findings(
                    args.message_file, correction, merge_parents,
                ))
                correction_preflight = not findings
            checked = 1
        else:
            authoritative = args.rev_range is None
            head = _resolve_head() if authoritative else None
            if authoritative:
                _assert_authoritative_repository()
                check_known_violation_append_only_history(
                    _KNOWN_VIOLATION_REPO_ROOT
                )
            commits = _commit_range(args.rev_range, head=head)
            receipt_state = {} if authoritative else None
            history = _audit_history(
                commits,
                authoritative=authoritative,
                head=head,
                receipt_state=receipt_state,
            )
            if authoritative:
                _assert_head_unchanged(head)
            findings = history.findings
            corrected = history.corrected
            waived = history.waived
            known_violations = history.known_violations
            known_violation_groups = _known_violation_groups(
                _known_violation_registry()
            )
            checked = len(commits)
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"check_ai_provenance: 実行不能: {exc}", file=sys.stderr)
        return 2

    # 免除は rc=1 でも沈黙させない (公開が唯一の抑止であるため)。
    for record in waived:
        print(
            "check_ai_provenance: implementation-author-waived "
            f"label={record.label} reason={record.reason} "
            f"ratified={record.ratified}"
        )
    if waived:
        print(
            "check_ai_provenance: implementation-author-waived="
            f"{len(waived)}"
        )

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        qualifier = "新規" if known_violations else ""
        print(
            f"check_ai_provenance: {checked} 件中 {len(findings)} "
            f"{qualifier}違反",
            file=sys.stderr,
        )
        for spec in known_violations:
            print(_known_violation_line(spec))
        if known_violations:
            print(
                "check_ai_provenance: known-violations="
                f"{len(known_violations)}"
            )
        if known_violation_groups is not None:
            _print_known_violation_groups(known_violation_groups)
        return 1

    for record in corrected:
        print(
            "check_ai_provenance: forward-corrected=1 "
            f"target={record.target} correction={record.correction}"
        )
    if correction_preflight:
        spec = INCIDENT_6B64D21_FORWARD_CORRECTION
        assumption = (
            "MERGE_HEAD の prospective merge"
            if merge_preflight
            else "current HEAD の通常子"
        )
        print(
            "check_ai_provenance: AI-Agent-Correction は preflight限定 "
            f"（{assumption}を仮定）。commit後 history監査が必須 "
            f"target={spec.target}"
        )
    for spec in known_violations:
        print(_known_violation_line(spec))
    if known_violations:
        print(
            "check_ai_provenance: known-violations="
            f"{len(known_violations)}"
        )
    if known_violation_groups is not None:
        _print_known_violation_groups(known_violation_groups)
    qualifier = "新規" if known_violations else ""
    print(f"check_ai_provenance: {checked} 件、{qualifier}違反なし")
    if args.message_file is None and receipt_state is not None:
        _publish_audit_receipt(receipt_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
