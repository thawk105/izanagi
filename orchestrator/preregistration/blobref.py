"""Commit に固定した blob の参照束縛。

本 module は投入 gate (admission gate) ではない。
``resolve_effective_preregistration`` / ``PreregBinding`` / ``submit_pilot`` /
``verify_receipt`` は本 wave では実装しない。
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile


_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_GIT_ENV_ALLOW = frozenset(
    {
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SYSTEMROOT",
        "TMPDIR",
    }
)
_GIT_HARDEN = ("-c", "core.useReplaceRefs=false")
GIT_TIMEOUT_BASE_SECONDS = 5.0
GIT_TIMEOUT_BYTES_PER_SECOND = 1024 * 1024
GIT_TIMEOUT_CAP_SECONDS = 30.0
MAX_BLOB_BYTES = 16 * 1024 * 1024
MAX_GIT_METADATA_OUTPUT_BYTES = 1024 * 1024


class BlobRefError(Exception):
    """BlobRef の検査または解決に失敗した。"""


class InvalidBlobRefError(BlobRefError):
    """BlobRef の path または digest の形状が不正である。"""


class BlobResolutionError(BlobRefError):
    """固定 commit の blob を Git object database から解決できない。"""


class BlobDigestMismatchError(BlobRefError):
    """解決した blob の digest が固定値と一致しない。"""


def _validate_repo_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise InvalidBlobRefError("path は空でない repo 相対文字列でなければならない")
    if "\\" in value or "\n" in value or "\r" in value:
        raise InvalidBlobRefError("path は canonical な POSIX repo 相対 path でなければならない")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix():
        raise InvalidBlobRefError("path は canonical な POSIX repo 相対 path でなければならない")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise InvalidBlobRefError("path に空要素・'.'・'..' は使えない")
    normalized = str.__str__(value)
    if type(normalized) is not str:
        raise InvalidBlobRefError("path は組み込み str へ正規化できない")
    if type(value) is not str:
        return _validate_repo_relative_path(normalized)
    return normalized


def _require_hex(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        width = 40 if label == "commit" else 64
        raise InvalidBlobRefError(f"{label} は {width} 桁 lowercase hex でなければならない")
    normalized = str.__str__(value)
    if type(normalized) is not str or pattern.fullmatch(normalized) is None:
        width = 40 if label == "commit" else 64
        raise InvalidBlobRefError(f"{label} は {width} 桁 lowercase hex でなければならない")
    return normalized


@dataclass(frozen=True)
class BlobRef:
    """Git object database 内の blob を path・commit・SHA-256 で固定する。"""

    path: str
    commit: str
    sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _validate_repo_relative_path(self.path))
        object.__setattr__(
            self, "commit", _require_hex(self.commit, _COMMIT_RE, "commit")
        )
        object.__setattr__(
            self, "sha256", _require_hex(self.sha256, _SHA256_RE, "sha256")
        )


def read_pinned_blob(repository_root: str | os.PathLike[str], ref: BlobRef) -> bytes:
    """``ref`` が固定する commit の blob bytes を検証して返す。

    worktree 上の対象 path は開かない。固定 commit の literal pathspec から得た
    object ID を Git object database から読み、replace object も無効化する。
    """

    if not isinstance(ref, BlobRef):
        raise InvalidBlobRefError("ref は BlobRef でなければならない")
    path, commit, sha256 = ref.path, ref.commit, ref.sha256
    for field_name, value in (
        ("path", path),
        ("commit", commit),
        ("sha256", sha256),
    ):
        if type(value) is not str:
            raise InvalidBlobRefError(
                f"ref.{field_name} は組み込み str でなければならない"
            )
    ref = BlobRef(path=path, commit=commit, sha256=sha256)
    try:
        root = Path(repository_root).resolve(strict=True)
    except OSError as exc:
        raise BlobResolutionError("repository_root を解決できない") from exc
    if not root.is_dir():
        raise BlobResolutionError("repository_root が directory として存在しない")

    env = _git_env()
    _require_git_top_level(root, env)
    _require_safe_history(root, env)
    object_name = _require_commit_regular_blob(root, ref, env)
    size_result = _git(root, env, ["cat-file", "-s", object_name])
    if size_result.returncode != 0:
        raise BlobResolutionError("固定 blob の size を解決できない")
    size_text = size_result.stdout.strip()
    if not size_text.isdigit():
        raise BlobResolutionError("固定 blob の size が不正である")
    blob_size = int(size_text)
    if blob_size > MAX_BLOB_BYTES:
        raise BlobResolutionError("固定 blob が size 上限を超える")
    result = _git(
        root,
        env,
        ["cat-file", "blob", object_name],
        work_bytes=blob_size,
        max_output_bytes=MAX_BLOB_BYTES,
    )
    if result.returncode != 0:
        raise BlobResolutionError("commit または blob が存在せず固定参照を解決できない")
    if len(result.stdout) != blob_size:
        raise BlobResolutionError("固定 blob の宣言 size と読取 size が一致しない")

    actual_digest = hashlib.sha256(result.stdout).digest()
    if actual_digest != bytes.fromhex(ref.sha256):
        actual = actual_digest.hex()
        raise BlobDigestMismatchError(
            f"固定 blob の SHA-256 が不一致: expected={ref.sha256}, actual={actual}"
        )
    return result.stdout


def _git_env() -> dict[str, str]:
    """Git 制御変数を継承せず、最小限の process 環境を構成する。"""

    env = {key: value for key, value in os.environ.items() if key in _GIT_ENV_ALLOW}
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
    return env


def _git_timeout_seconds(work_bytes: int) -> float:
    return min(
        GIT_TIMEOUT_BASE_SECONDS + work_bytes / GIT_TIMEOUT_BYTES_PER_SECOND,
        GIT_TIMEOUT_CAP_SECONDS,
    )


def _git(
    root: Path,
    env: dict[str, str],
    arguments: list[str],
    *,
    work_bytes: int = 0,
    max_output_bytes: int = MAX_GIT_METADATA_OUTPUT_BYTES,
) -> subprocess.CompletedProcess[bytes]:
    try:
        with tempfile.TemporaryFile() as stdout:
            completed = subprocess.run(
                ["git", *_GIT_HARDEN, "--no-replace-objects", *arguments],
                cwd=root,
                env=env,
                stdout=stdout,
                stderr=subprocess.PIPE,
                check=False,
                timeout=_git_timeout_seconds(work_bytes),
            )
            output_size = stdout.tell()
            if output_size > max_output_bytes:
                raise BlobResolutionError("Git output が size 上限を超える")
            stdout.seek(0)
            return subprocess.CompletedProcess(
                completed.args,
                completed.returncode,
                stdout.read(),
                completed.stderr,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BlobResolutionError("固定 blob の Git 解決を実行できない") from exc


def _require_git_top_level(root: Path, env: dict[str, str]) -> None:
    result = _git(root, env, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise BlobResolutionError("repository_root が Git worktree でない")
    try:
        actual = Path(result.stdout.decode("utf-8", errors="strict").strip()).resolve(
            strict=True
        )
    except (OSError, UnicodeDecodeError) as exc:
        raise BlobResolutionError("Git top-level の解決結果が不正である") from exc
    if actual != root:
        raise BlobResolutionError("repository_root が Git top-level と一致しない")


def _require_safe_history(root: Path, env: dict[str, str]) -> None:
    shallow = _git(root, env, ["rev-parse", "--is-shallow-repository"])
    if shallow.returncode != 0 or shallow.stdout.strip() != b"false":
        raise BlobResolutionError("shallow repository は受理しない")

    replace_refs = _git(
        root, env, ["for-each-ref", "--format=%(refname)", "refs/replace/"]
    )
    if replace_refs.returncode != 0 or replace_refs.stdout.strip():
        raise BlobResolutionError("replace refs を持つ repository は受理しない")

    graft_result = _git(root, env, ["rev-parse", "--git-path", "info/grafts"])
    if graft_result.returncode != 0:
        raise BlobResolutionError("grafts path を解決できない")
    try:
        graft_path = Path(
            graft_result.stdout.decode("utf-8", errors="strict").strip()
        )
    except UnicodeDecodeError as exc:
        raise BlobResolutionError("grafts path の解決結果が不正である") from exc
    if not graft_path.is_absolute():
        graft_path = root / graft_path
    if graft_path.exists():
        raise BlobResolutionError("grafts を持つ repository は受理しない")


def _require_commit_regular_blob(
    root: Path, ref: BlobRef, env: dict[str, str]
) -> str:
    """Exact commit と、その tree の regular blob entry を検証して object ID を返す。"""

    object_type = _git(root, env, ["cat-file", "-t", ref.commit])
    if object_type.returncode != 0 or object_type.stdout != b"commit\n":
        raise BlobResolutionError("commit は exact commit object でなければならない")

    listing = _git(
        root,
        env,
        ["ls-tree", "-z", "--full-name", ref.commit, "--", ref.path],
    )
    if listing.returncode != 0:
        raise BlobResolutionError("commit の tree entry を解決できない")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if len(entries) != 1:
        raise BlobResolutionError("path は commit 内の一意な tree entry でなければならない")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        raise BlobResolutionError("tree entry の形式が不正である")
    mode, object_kind, object_id = fields
    if entry_path != os.fsencode(ref.path):
        raise BlobResolutionError("tree entry path が固定 path と一致しない")
    if object_kind != b"blob" or mode not in {b"100644", b"100755"}:
        raise BlobResolutionError("固定 path は regular blob entry でなければならない")
    try:
        return object_id.decode("ascii", errors="strict")
    except UnicodeDecodeError as exc:
        raise BlobResolutionError("blob object ID が ASCII でない") from exc
