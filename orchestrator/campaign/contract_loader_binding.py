# -*- coding: utf-8 -*-
"""歴史名 ``contract_loader_*`` が表す exact 85 path closure の binding。"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Iterator, Mapping

from .campaign_lock import CONTRACT_LOADER_RELATIVE_PATHS

_REPO_ROOT = Path(__file__).resolve().parents[2]
GIT_TIMEOUT_SECONDS = 10
_GIT_EXECUTABLE = Path("/usr/bin/git")
_GIT_HARDEN = (
    "--no-pager",
    "-c",
    "core.useReplaceRefs=false",
    "-c",
    "core.commitGraph=false",
    "-c",
    "core.fsmonitor=false",
)

_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)
_FORBIDDEN_AMBIENT_GIT_ENV = frozenset({
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES",
})

_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_HEX40_BYTES_RE = re.compile(rb"[0-9a-f]{40}\Z")


class ContractLoaderBindingError(Exception):
    """loader binding を完全には取得・検証できなかった。"""


@dataclass(frozen=True)
class ContractLoaderBinding:
    """記録 commit と enforcement source closure 85 path の SHA-256。

    ``contract_loader_*`` 識別子は歴史的名称であり、値は loader 2 path では
    なく enforcement source closure 85 path を表す。
    """

    contract_loader_commit: str
    contract_loader_blob_sha256s: Mapping[str, str]

    def __post_init__(self) -> None:
        _validate_commit(self.contract_loader_commit)
        checked = _validate_blob_sha256s(self.contract_loader_blob_sha256s)
        object.__setattr__(self, "contract_loader_blob_sha256s", checked)


def _validate_commit(value: object) -> str:
    if type(value) is not str or _HEX40_RE.fullmatch(value) is None:
        raise ContractLoaderBindingError(
            "contract-loader-invalid-binding: commit は 40 桁 lowercase hex が必要"
        )
    return value


def _validate_blob_sha256s(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != set(CONTRACT_LOADER_RELATIVE_PATHS):
        raise ContractLoaderBindingError(
            "contract-loader-invalid-binding: blob map の exact key 集合が不正"
        )
    checked: dict[str, str] = {}
    for relative in CONTRACT_LOADER_RELATIVE_PATHS:
        digest = value[relative]
        if type(digest) is not str or _HEX64_RE.fullmatch(digest) is None:
            raise ContractLoaderBindingError(
                "contract-loader-invalid-binding: blob SHA-256 が不正: "
                f"{relative}"
            )
        checked[relative] = digest
    return checked


def _validated_root() -> Path:
    if not isinstance(_REPO_ROOT, Path):
        raise ContractLoaderBindingError(
            "contract-loader-root-error: _REPO_ROOT は pathlib.Path が必要"
        )
    try:
        root = _REPO_ROOT.resolve(strict=True)
        info = os.stat(root, follow_symlinks=False)
    except (OSError, RuntimeError) as exc:
        raise ContractLoaderBindingError(
            f"contract-loader-root-error: repository root を解決できない: {exc}"
        ) from exc
    if not stat.S_ISDIR(info.st_mode):
        raise ContractLoaderBindingError(
            "contract-loader-root-error: repository root が directory でない"
        )
    raw_toplevel = _run_git(root, "rev-parse", "--show-toplevel")
    try:
        toplevel = raw_toplevel.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractLoaderBindingError(
            "contract-loader-root-error: Git top-level が UTF-8 でない"
        ) from exc
    if not toplevel.endswith("\n") or "\n" in toplevel[:-1]:
        raise ContractLoaderBindingError(
            "contract-loader-root-error: Git top-level 出力が一意でない"
        )
    toplevel = toplevel[:-1]
    if toplevel != str(root):
        raise ContractLoaderBindingError(
            "contract-loader-root-error: Git top-level が expected checkout root "
            f"と不一致: actual={toplevel!r} expected={str(root)!r}"
        )
    return root


def _relative_parts(relative: str) -> tuple[str, ...]:
    if type(relative) is not str:
        raise ContractLoaderBindingError(
            "contract-loader-path-error: loader path は exact str が必要"
        )
    pure = PurePosixPath(relative)
    if (pure.is_absolute() or not pure.parts
            or any(part in {"", ".", ".."} for part in pure.parts)
            or pure.as_posix() != relative):
        raise ContractLoaderBindingError(
            f"contract-loader-path-escape: loader path が不正: {relative!r}"
        )
    return pure.parts


def _stat_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _read_regular_file_no_follow(root: Path, relative: str) -> bytes:
    """root-relative path を component ごと no-follow で開き、race を拒否する。"""
    parts = _relative_parts(relative)
    candidate = root.joinpath(*parts)
    try:
        resolved_before = candidate.resolve(strict=True)
        resolved_before.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ContractLoaderBindingError(
            f"contract-loader-path-escape: root 外または解決不能: {relative}"
        ) from exc

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    cloexec = getattr(os, "O_CLOEXEC", None)
    if nofollow is None or directory is None or cloexec is None:
        raise ContractLoaderBindingError(
            "contract-loader-open-error: no-follow open flags が利用できない"
        )

    opened_dirs: list[int] = []
    file_fd: int | None = None
    try:
        current_fd = os.open(root, os.O_RDONLY | directory | cloexec | nofollow)
        opened_dirs.append(current_fd)
        for part in parts[:-1]:
            current_fd = os.open(
                part,
                os.O_RDONLY | directory | cloexec | nofollow,
                dir_fd=current_fd,
            )
            opened_dirs.append(current_fd)

        before_path = os.stat(
            parts[-1], dir_fd=current_fd, follow_symlinks=False,
        )
        if not stat.S_ISREG(before_path.st_mode):
            raise ContractLoaderBindingError(
                f"contract-loader-file-type: symlink/non-regular loader: {relative}"
            )
        file_fd = os.open(
            parts[-1], os.O_RDONLY | cloexec | nofollow, dir_fd=current_fd,
        )
        before_fd = os.fstat(file_fd)
        if (not stat.S_ISREG(before_fd.st_mode)
                or (before_fd.st_dev, before_fd.st_ino)
                != (before_path.st_dev, before_path.st_ino)):
            raise ContractLoaderBindingError(
                f"contract-loader-path-race: open 前に path/inode が変化: {relative}"
            )

        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)

        after_fd = os.fstat(file_fd)
        after_path = os.stat(
            parts[-1], dir_fd=current_fd, follow_symlinks=False,
        )
        try:
            resolved_after = candidate.resolve(strict=True)
            resolved_after.relative_to(root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ContractLoaderBindingError(
                f"contract-loader-path-race: read 後に path が escape: {relative}"
            ) from exc
        identities = (
            _stat_identity(before_path),
            _stat_identity(before_fd),
            _stat_identity(after_fd),
            _stat_identity(after_path),
        )
        if len(set(identities)) != 1 or resolved_after != resolved_before:
            raise ContractLoaderBindingError(
                f"contract-loader-path-race: read 前後で path/inode が変化: {relative}"
            )
        return b"".join(chunks)
    except ContractLoaderBindingError:
        raise
    except OSError as exc:
        raise ContractLoaderBindingError(
            f"contract-loader-open-error: loader を安全に読めない: {relative}: {exc}"
        ) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for fd in reversed(opened_dirs):
            os.close(fd)


def _run_git(
    root: Path,
    *args: str,
    input_bytes: bytes | None = None,
    timeout_seconds: int = GIT_TIMEOUT_SECONDS,
) -> bytes:
    if not _GIT_EXECUTABLE.is_absolute():
        raise ContractLoaderBindingError(
            "contract-loader-git-error: git executable が絶対 path でない"
        )
    try:
        present = _GIT_EXECUTABLE.is_file()
    except OSError as exc:
        raise ContractLoaderBindingError(
            "contract-loader-git-error: git executable を解決できない"
        ) from exc
    if not present:
        raise ContractLoaderBindingError(
            "contract-loader-git-error: git executable が見つからない"
        )
    executable = os.fspath(_GIT_EXECUTABLE)
    contaminated = sorted(
        key for key in _FORBIDDEN_AMBIENT_GIT_ENV if key in os.environ
    )
    if contaminated:
        raise ContractLoaderBindingError(
            "contract-loader-git-environment: ambient Git repository/object "
            f"override を拒否: {contaminated!r}"
        )
    git_env = {
        key: os.environ[key]
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    git_env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    try:
        completed = subprocess.run(
            [
                executable,
                *_GIT_HARDEN,
                "--no-replace-objects",
                "-C", str(root),
                *args,
            ],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=git_env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise ContractLoaderBindingError(
            f"contract-loader-git-timeout: git が {timeout_seconds} 秒で完了しない"
        ) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise ContractLoaderBindingError(
            f"contract-loader-git-error: git を実行できない: {exc}"
        ) from exc
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ContractLoaderBindingError(
            "contract-loader-git-error: git command が失敗: "
            f"args={args!r} rc={completed.returncode} stderr={stderr!r}"
        )
    return completed.stdout


def _head_commit(root: Path) -> str:
    raw = _run_git(root, "rev-parse", "--verify", "HEAD^{commit}")
    try:
        commit = raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ContractLoaderBindingError(
            "contract-loader-git-error: commit id が ASCII でない"
        ) from exc
    return _validate_commit(commit)


def _require_commit(root: Path, commit: str) -> None:
    actual = _run_git(root, "rev-parse", "--verify", f"{commit}^{{commit}}")
    try:
        resolved = actual.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ContractLoaderBindingError(
            "contract-loader-git-error: verified commit id が ASCII でない"
        ) from exc
    if resolved != commit:
        raise ContractLoaderBindingError(
            "contract-loader-git-error: 記録 commit を exact に解決できない"
        )


def _iter_blobs(
    root: Path,
    commit: str,
    relative_paths: tuple[str, ...],
) -> Iterator[tuple[str, bytes]]:
    """commit の blob 群を path 順・重複込みで batch 取得する。"""
    relatives = tuple(relative_paths)
    encoded_by_relative: dict[str, bytes] = {}
    for relative in relatives:
        _relative_parts(relative)
        encoded = os.fsencode(relative)
        if b"\0" in encoded:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command に NUL path を渡せない: "
                f"{relative!r}"
            )
        encoded_by_relative[relative] = encoded

    if not relatives:
        return

    unique_paths = tuple(dict.fromkeys(relatives))
    expected_by_raw_path: dict[bytes, str] = {}
    for relative in unique_paths:
        raw_path = encoded_by_relative[relative]
        previous = expected_by_raw_path.get(raw_path)
        if previous is not None and previous != relative:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の path encoding が衝突: "
                f"{relative!r}"
            )
        expected_by_raw_path[raw_path] = relative

    ls_tree = _run_git(
        root,
        "ls-tree",
        "-r",
        "-z",
        commit,
        "--",
        *(f":(literal){relative}" for relative in unique_paths),
        timeout_seconds=GIT_TIMEOUT_SECONDS * len(unique_paths),
    )
    entries = ls_tree.split(b"\0")
    if not entries or entries[-1] != b"":
        raise ContractLoaderBindingError(
            "contract-loader-git-error: git command の ls-tree 出力が "
            "NUL 終端でない"
        )
    entries.pop()

    oid_by_relative: dict[str, bytes] = {}
    for entry in entries:
        metadata, separator, raw_path = entry.partition(b"\t")
        fields = metadata.split(b" ")
        if separator != b"\t" or len(fields) != 3 or not raw_path:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree entry が不正"
            )
        _mode, object_type, oid = fields
        if not _mode:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree entry が不正"
            )
        relative = expected_by_raw_path.get(raw_path)
        if relative is None:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree に期待外 path: "
                f"{os.fsdecode(raw_path)!r}"
            )
        if relative in oid_by_relative:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree に重複 path: "
                f"{relative}"
            )
        if object_type != b"blob":
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree object が "
                f"blob でない: {relative}"
            )
        if _HEX40_BYTES_RE.fullmatch(oid) is None:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree oid が不正: "
                f"{relative}"
            )
        oid_by_relative[relative] = oid

    for relative in unique_paths:
        if relative not in oid_by_relative:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の ls-tree に path が不在: "
                f"{relative}"
            )

    queries = tuple(
        (relative, oid_by_relative[relative]) for relative in relatives
    )
    batch_input = b"".join(oid + b"\n" for _relative, oid in queries)
    batch_output = _run_git(
        root,
        "cat-file",
        "--batch",
        input_bytes=batch_input,
        timeout_seconds=GIT_TIMEOUT_SECONDS * len(queries),
    )

    offset = 0
    parsed: list[tuple[str, bytes]] = []
    for relative, expected_oid in queries:
        header_end = batch_output.find(b"\n", offset)
        if header_end < 0:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch header が途中 EOF: "
                f"{relative}"
            )
        header = batch_output[offset:header_end]
        fields = header.split(b" ")
        if len(fields) != 3:
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch status/header が不正: "
                f"{relative}"
            )
        oid, object_type, raw_size = fields
        if (_HEX40_BYTES_RE.fullmatch(oid) is None
                or oid != expected_oid):
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch oid が期待値と不一致: "
                f"{relative}"
            )
        if object_type != b"blob":
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch object が blob でない: "
                f"{relative}"
            )
        if not raw_size or not raw_size.isdigit():
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch size が不正: "
                f"{relative}"
            )
        size = int(raw_size)
        body_start = header_end + 1
        body_end = body_start + size
        if body_end >= len(batch_output):
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch body が途中 EOF: "
                f"{relative}"
            )
        if batch_output[body_end:body_end + 1] != b"\n":
            raise ContractLoaderBindingError(
                "contract-loader-git-error: git command の batch record LF が不正: "
                f"{relative}"
            )
        parsed.append((relative, batch_output[body_start:body_end]))
        offset = body_end + 1

    if offset != len(batch_output):
        raise ContractLoaderBindingError(
            "contract-loader-git-error: git command の batch 出力に余剰 bytes"
        )

    yield from parsed


def _blob(root: Path, commit: str, relative: str) -> bytes:
    blobs = tuple(_iter_blobs(root, commit, (relative,)))
    return blobs[0][1]


def capture_contract_loader_binding() -> ContractLoaderBinding:
    """current HEAD blob と live closure bytes が一致する binding を取得する。"""
    root = _validated_root()
    commit = _head_commit(root)
    digests: dict[str, str] = {}
    for relative, blob in _iter_blobs(
        root, commit, CONTRACT_LOADER_RELATIVE_PATHS,
    ):
        disk = _read_regular_file_no_follow(root, relative)
        if disk != blob:
            raise ContractLoaderBindingError(
                f"contract-loader-drift: disk bytes が HEAD blob と不一致: {relative}"
            )
        digests[relative] = hashlib.sha256(blob).hexdigest()
    return ContractLoaderBinding(commit, digests)


def verify_live_contract_loader_binding(binding: ContractLoaderBinding) -> None:
    """記録 commit blob・記録 digest・現在の closure bytes を exact 照合する。"""
    if type(binding) is not ContractLoaderBinding:
        raise ContractLoaderBindingError(
            "contract-loader-invalid-binding: exact ContractLoaderBinding が必要"
        )
    root = _validated_root()
    _require_commit(root, binding.contract_loader_commit)
    for relative, blob in _iter_blobs(
        root, binding.contract_loader_commit, CONTRACT_LOADER_RELATIVE_PATHS,
    ):
        actual_digest = hashlib.sha256(blob).hexdigest()
        if actual_digest != binding.contract_loader_blob_sha256s[relative]:
            raise ContractLoaderBindingError(
                f"contract-loader-blob-mismatch: 記録 digest と commit blob が不一致: {relative}"
            )
        disk = _read_regular_file_no_follow(root, relative)
        if disk != blob:
            raise ContractLoaderBindingError(
                f"contract-loader-drift: disk bytes が記録 commit blob と不一致: {relative}"
            )


def verify_committed_contract_loader_binding(
        binding: ContractLoaderBinding,
) -> None:
    """working tree を読まず、記録 commit blob と記録 digest だけを照合する。"""
    if type(binding) is not ContractLoaderBinding:
        raise ContractLoaderBindingError(
            "contract-loader-invalid-binding: exact ContractLoaderBinding が必要"
        )
    root = _validated_root()
    _require_commit(root, binding.contract_loader_commit)
    for relative, blob in _iter_blobs(
        root, binding.contract_loader_commit, CONTRACT_LOADER_RELATIVE_PATHS,
    ):
        if hashlib.sha256(blob).hexdigest() != binding.contract_loader_blob_sha256s[relative]:
            raise ContractLoaderBindingError(
                f"contract-loader-blob-mismatch: 記録 digest と commit blob が不一致: {relative}"
            )


def verify_committed_contract_loader_blobs(
        contract_loader_commit: str,
        contract_loader_blob_sha256s: Mapping[str, str],
        relative_paths: tuple[str, ...],
) -> None:
    """明示された ordered path 全体の記録 commit blob を digest 照合する。"""
    root = _validated_root()
    _require_commit(root, contract_loader_commit)
    for relative, blob in _iter_blobs(
        root, contract_loader_commit, relative_paths,
    ):
        if (
            hashlib.sha256(blob).hexdigest()
            != contract_loader_blob_sha256s[relative]
        ):
            raise ContractLoaderBindingError(
                f"contract-loader-blob-mismatch: 記録 digest と commit blob が不一致: {relative}"
            )


def binding_from_authority(
        contract_loader_commit: str,
        contract_loader_blob_sha256s: Mapping[str, str],
) -> ContractLoaderBinding:
    """codec が検証した v2 authority を binding value へ写す。"""
    return ContractLoaderBinding(
        contract_loader_commit=contract_loader_commit,
        contract_loader_blob_sha256s=dict(contract_loader_blob_sha256s),
    )
