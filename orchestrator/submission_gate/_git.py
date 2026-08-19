"""固定した Git 実行面と commit/blob の構造検査。

この module は既存の preregistration helper を import せず、その Git の衛生化境界を
独立に実装する。Git の設定・履歴の外部入力を受理集合へ
黙って混ぜないため、実行可能ファイル、環境、履歴の形をすべてここで閉じる。
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
from typing import Final


_COMMIT_RE: Final = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}\Z")

# PATH、global/system config、replace object、lazy fetch などを Git の入力から
# 外す。LANG 系と一時ディレクトリだけは Git の通常のプロセス契約として残す。
_GIT_ENV_ALLOW: Final = frozenset(
    {"LANG", "LC_ALL", "LC_CTYPE", "SYSTEMROOT", "TMPDIR"}
)
_GIT_EXECUTABLE: Final = Path("/usr/bin/git")
_GIT_HARDEN: Final = (
    "--no-pager",
    "-c",
    "core.useReplaceRefs=false",
    "-c",
    "core.commitGraph=false",
    "-c",
    "core.fsmonitor=false",
)
GIT_TIMEOUT_BASE_SECONDS: Final = 5.0
GIT_TIMEOUT_BYTES_PER_SECOND: Final = 1024 * 1024
GIT_TIMEOUT_CAP_SECONDS: Final = 30.0
MAX_BLOB_BYTES: Final = 16 * 1024 * 1024
MAX_GIT_METADATA_OUTPUT_BYTES: Final = 1024 * 1024


class GitSupportError(RuntimeError):
    """固定 Git で repository/history/blob を検査できない。"""


def _repository_root(repository_root: str | os.PathLike[str]) -> Path:
    try:
        root = Path(repository_root).resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as exc:
        raise GitSupportError("repository_root を解決できない") from exc
    if not root.is_dir():
        raise GitSupportError("repository_root が directory として存在しない")
    return root


def _git_env() -> dict[str, str]:
    """Git が参照する環境を最小集合へ scrub する。"""

    env = {key: value for key, value in os.environ.items() if key in _GIT_ENV_ALLOW}
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return env


def _git_timeout_seconds(work_bytes: int) -> float:
    if type(work_bytes) is not int or work_bytes < 0:
        raise GitSupportError("Git work_bytes が不正である")
    return min(
        GIT_TIMEOUT_BASE_SECONDS + work_bytes / GIT_TIMEOUT_BYTES_PER_SECOND,
        GIT_TIMEOUT_CAP_SECONDS,
    )


def _resolve_git_executable() -> str:
    """PATH 探索をせず、固定した絶対 path の Git だけを返す。"""

    if not _GIT_EXECUTABLE.is_absolute():
        raise GitSupportError("git executable を絶対 path として解決できない")
    try:
        if not _GIT_EXECUTABLE.is_file():
            raise GitSupportError("git executable が regular file でない")
    except OSError as exc:
        raise GitSupportError("git executable を解決できない") from exc
    return os.fspath(_GIT_EXECUTABLE)


def _git(
    root: Path,
    arguments: list[str] | tuple[str, ...],
    *,
    work_bytes: int = 0,
    max_output_bytes: int = MAX_GIT_METADATA_OUTPUT_BYTES,
) -> subprocess.CompletedProcess[bytes]:
    """固定 executable・scrub 済み環境で Git を実行する。"""

    executable = _resolve_git_executable()
    if type(max_output_bytes) is not int or max_output_bytes < 0:
        raise GitSupportError("Git output 上限が不正である")
    try:
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            completed = subprocess.run(
                [executable, *_GIT_HARDEN, "--no-replace-objects", *arguments],
                cwd=root,
                env=_git_env(),
                stdout=stdout,
                stderr=stderr,
                check=False,
                timeout=_git_timeout_seconds(work_bytes),
            )
            stdout_size = stdout.tell()
            stderr_size = stderr.tell()
            if stdout_size > max_output_bytes:
                raise GitSupportError("Git output が size 上限を超える")
            if stderr_size > max_output_bytes:
                raise GitSupportError("Git stderr output が size 上限を超える")
            stdout.seek(0)
            stderr.seek(0)
            return subprocess.CompletedProcess(
                completed.args,
                completed.returncode,
                stdout.read(),
                stderr.read(),
            )
    except GitSupportError:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitSupportError("固定 blob の Git 解決を実行できない") from exc


def require_git_repository(
    repository_root: str | os.PathLike[str],
) -> Path:
    """実際の Git worktree root を検証して返す。"""

    root = _repository_root(repository_root)
    result = _git(root, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise GitSupportError("repository_root が Git worktree でない")
    try:
        text = result.stdout.decode("utf-8", errors="strict")
        actual = Path(text.rstrip("\n")).resolve(strict=True)
    except (OSError, UnicodeDecodeError, RuntimeError) as exc:
        raise GitSupportError("Git top-level の解決結果が不正である") from exc
    if not text.endswith("\n") or "\n" in text[:-1] or "\x00" in text:
        raise GitSupportError("Git top-level の解決結果が不正である")
    if actual != root:
        raise GitSupportError("repository_root が Git top-level と一致しない")
    return root


def _require_no_alternates_or_promisor(root: Path) -> None:
    """外部 object store、partial clone、promisor を拒否する。"""

    objects_result = _git(root, ["rev-parse", "--git-path", "objects"])
    if objects_result.returncode != 0:
        raise GitSupportError("Git objects path を解決できない")
    try:
        objects_text = objects_result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GitSupportError("Git objects path の解決結果が不正である") from exc
    if (
        not objects_text.endswith("\n")
        or not objects_text[:-1]
        or "\n" in objects_text[:-1]
        or "\x00" in objects_text
    ):
        raise GitSupportError("Git objects path の解決結果が不正である")
    objects_path = Path(objects_text[:-1])
    if not objects_path.is_absolute():
        objects_path = root / objects_path
    try:
        objects_path.lstat()
    except OSError as exc:
        raise GitSupportError("Git objects directory の状態を検査できない") from exc
    if not objects_path.is_dir() or objects_path.is_symlink():
        raise GitSupportError("Git objects directory が安全でない")

    for marker in (
        objects_path / "info" / "alternates",
        objects_path / "info" / "http-alternates",
    ):
        try:
            marker.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise GitSupportError("alternates の状態を検査できない") from exc
        else:
            raise GitSupportError("alternates を持つ repository は受理しない")

    pack_path = objects_path / "pack"
    try:
        pack_stat = pack_path.lstat()
    except FileNotFoundError:
        has_promisor_marker = False
    except OSError as exc:
        raise GitSupportError("Git pack directory の状態を検査できない") from exc
    else:
        if stat.S_ISLNK(pack_stat.st_mode) or not stat.S_ISDIR(pack_stat.st_mode):
            raise GitSupportError("Git pack directory が安全でない")
        try:
            with os.scandir(pack_path) as entries:
                has_promisor_marker = any(
                    entry.name.endswith(".promisor") for entry in entries
                )
        except OSError as exc:
            raise GitSupportError("promisor object の状態を検査できない") from exc
    if has_promisor_marker:
        raise GitSupportError("promisor object を持つ repository は受理しない")

    partial_clone = _git(
        root, ["config", "--includes", "--get-all", "extensions.partialClone"]
    )
    if partial_clone.returncode == 0:
        raise GitSupportError("partial clone repository は受理しない")
    if partial_clone.returncode != 1:
        raise GitSupportError("partial clone 設定を検査できない")

    promisors = _git(
        root,
        [
            "config",
            "-z",
            "--includes",
            "--type=bool",
            "--get-regexp",
            r"^remote\..*\.promisor$",
        ],
    )
    if promisors.returncode == 1:
        return
    if promisors.returncode != 0:
        raise GitSupportError("promisor remote 設定を検査できない")
    records = promisors.stdout.split(b"\0")
    if records[-1:] != [b""]:
        raise GitSupportError("promisor remote 設定の解決結果が不正である")
    records.pop()
    if not records or any(not record for record in records):
        raise GitSupportError("promisor remote 設定の解決結果が不正である")
    for record in records:
        fields = record.split(b"\n")
        if (
            len(fields) != 2
            or not fields[0]
            or fields[1] not in {b"true", b"false"}
        ):
            raise GitSupportError("promisor remote 設定の解決結果が不正である")
        if fields[1] == b"true":
            raise GitSupportError("promisor remote を持つ repository は受理しない")


def require_safe_history(repository_root: Path) -> None:
    """shallow/graft/replace/alternates/promisor のない履歴だけを受理する。"""

    root = require_git_repository(repository_root)
    _require_no_alternates_or_promisor(root)

    shallow = _git(root, ["rev-parse", "--is-shallow-repository"])
    if shallow.returncode != 0 or shallow.stdout != b"false\n":
        raise GitSupportError("shallow repository は受理しない")

    replace_refs = _git(
        root, ["for-each-ref", "--format=%(refname)", "refs/replace/"]
    )
    if replace_refs.returncode != 0 or replace_refs.stdout.strip():
        raise GitSupportError("replace refs を持つ repository は受理しない")

    graft_result = _git(root, ["rev-parse", "--git-path", "info/grafts"])
    if graft_result.returncode != 0:
        raise GitSupportError("grafts path を解決できない")
    try:
        graft_text = graft_result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GitSupportError("grafts path の解決結果が不正である") from exc
    if (
        not graft_text.endswith("\n")
        or not graft_text[:-1]
        or "\n" in graft_text[:-1]
        or "\x00" in graft_text
    ):
        raise GitSupportError("grafts path の解決結果が不正である")
    graft_path = Path(graft_text[:-1])
    if not graft_path.is_absolute():
        graft_path = root / graft_path
    try:
        graft_path.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise GitSupportError("grafts の状態を検査できない") from exc
    else:
        raise GitSupportError("grafts を持つ repository は受理しない")


def _require_commit_id(value: object, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise GitSupportError(f"{label} は 40 桁 lowercase hex でなければならない")
    return value


def _require_sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise GitSupportError(f"{label} は 64 桁 lowercase hex でなければならない")
    return value


def resolve_head(repository_root: Path) -> str:
    """安全な実 checkout の ``HEAD`` を full commit ID として導出する。"""

    root = require_git_repository(repository_root)
    require_safe_history(root)
    result = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    if result.returncode != 0:
        raise GitSupportError("HEAD を commit として解決できない")
    try:
        commit = result.stdout.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GitSupportError("HEAD の解決結果が ASCII でない") from exc
    if not commit.endswith("\n") or "\n" in commit[:-1]:
        raise GitSupportError("HEAD の解決結果が不正である")
    return _require_commit_id(commit[:-1], "HEAD")


def require_commit_object(repository_root: Path, commit: str) -> None:
    """full SHA-1 が replace/peel ではない exact commit object であることを検査する。"""

    commit = _require_commit_id(commit, "commit")
    root = require_git_repository(repository_root)
    require_safe_history(root)
    object_type = _git(root, ["cat-file", "-t", commit])
    if object_type.returncode != 0 or object_type.stdout != b"commit\n":
        raise GitSupportError("commit は exact commit object でなければならない")
    result = _git(root, ["rev-parse", "--verify", f"{commit}^{{commit}}"])
    if result.returncode != 0:
        raise GitSupportError("commit object を解決できない")
    try:
        resolved = result.stdout.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GitSupportError("commit 解決結果が ASCII でない") from exc
    if resolved != f"{commit}\n":
        raise GitSupportError("commit 解決で object identity が変わった")


def require_ancestor(
    repository_root: Path,
    *,
    ancestor: str,
    descendant: str,
) -> None:
    """``ancestor`` が ``descendant`` の祖先であることを検査する。"""

    ancestor = _require_commit_id(ancestor, "ancestor")
    descendant = _require_commit_id(descendant, "descendant")
    root = require_git_repository(repository_root)
    require_safe_history(root)
    require_commit_object(root, ancestor)
    require_commit_object(root, descendant)
    result = _git(root, ["merge-base", "--is-ancestor", ancestor, descendant])
    if result.returncode == 0:
        return
    if result.returncode == 1:
        raise GitSupportError("commit が祖先関係にない")
    raise GitSupportError(
        f"merge-base --is-ancestor が非 0 で終了した: rc={result.returncode}"
    )


def _validate_repo_relative_path(path_value: object) -> str:
    if type(path_value) is not str or not path_value or "\x00" in path_value:
        raise GitSupportError("path は空でない repo 相対文字列でなければならない")
    if any(char in path_value for char in ("\\", "\n", "\r", "\t")):
        raise GitSupportError("path は canonical な POSIX repo 相対 path でなければならない")
    path = PurePosixPath(path_value)
    if path.is_absolute() or path_value != path.as_posix():
        raise GitSupportError("path は canonical な POSIX repo 相対 path でなければならない")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise GitSupportError("path に空要素・'.'・'..' は使えない")
    return path_value


def require_exact_parent(
    repository_root: Path,
    *,
    content_commit: str,
    effective_commit: str,
) -> None:
    """effective commit の親集合が exact ``{content_commit}`` であることを検査する。"""

    content_commit = _require_commit_id(content_commit, "content_commit")
    effective_commit = _require_commit_id(effective_commit, "effective_commit")
    root = require_git_repository(repository_root)
    require_safe_history(root)
    require_commit_object(root, content_commit)
    require_commit_object(root, effective_commit)
    result = _git(root, ["rev-list", "--parents", "-n", "1", effective_commit])
    if result.returncode != 0:
        raise GitSupportError("effective commit の rev-list が非 0 で終了した")
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        raise GitSupportError("effective commit の親情報が一意でない")
    try:
        fields = lines[0].decode("ascii").split()
    except UnicodeDecodeError as exc:
        raise GitSupportError("effective commit の親情報が ASCII でない") from exc
    if not fields or fields[0] != effective_commit:
        raise GitSupportError("effective commit の親情報が object identity と不一致")
    parents = tuple(fields[1:])
    if any(_COMMIT_RE.fullmatch(parent) is None for parent in parents):
        raise GitSupportError("effective commit の親 ID が不正である")
    if set(parents) != {content_commit} or len(parents) != 1:
        if not parents:
            raise GitSupportError("effective commit は root commit である")
        if len(parents) > 1:
            raise GitSupportError("effective commit は merge commit である")
        raise GitSupportError("effective commit の sole parent が content commit でない")


def _require_commit_regular_blob(root: Path, *, commit: str, path: str) -> str:
    object_type = _git(root, ["cat-file", "-t", commit])
    if object_type.returncode != 0 or object_type.stdout != b"commit\n":
        raise GitSupportError("commit は exact commit object でなければならない")
    listing = _git(root, ["ls-tree", "-z", "--full-name", commit, "--", path])
    if listing.returncode != 0:
        raise GitSupportError("commit の tree entry を解決できない")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if len(entries) != 1:
        raise GitSupportError("path は commit 内の一意な tree entry でなければならない")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        raise GitSupportError("tree entry の形式が不正である")
    mode, object_kind, object_id = fields
    if entry_path != os.fsencode(path):
        raise GitSupportError("tree entry path が固定 path と一致しない")
    if object_kind != b"blob" or mode not in {b"100644", b"100755"}:
        raise GitSupportError("固定 path は regular blob entry でなければならない")
    try:
        object_name = object_id.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GitSupportError("blob object ID が ASCII でない") from exc
    if _COMMIT_RE.fullmatch(object_name) is None:
        raise GitSupportError("blob object ID が 40 桁 lowercase hex でない")
    return object_name


def read_commit_blob(
    repository_root: Path,
    *,
    commit: str,
    path: str,
    expected_sha256: str,
    max_bytes: int = MAX_BLOB_BYTES,
) -> bytes:
    """commit tree の regular blob を literal path・size・SHA-256 で読む。"""

    commit = _require_commit_id(commit, "commit")
    path = _validate_repo_relative_path(path)
    expected_sha256 = _require_sha256(expected_sha256, "expected_sha256")
    if type(max_bytes) is not int or max_bytes < 0:
        raise GitSupportError("blob size 上限が不正である")
    root = require_git_repository(repository_root)
    require_safe_history(root)
    require_commit_object(root, commit)
    object_name = _require_commit_regular_blob(root, commit=commit, path=path)
    size_result = _git(root, ["cat-file", "-s", object_name])
    if size_result.returncode != 0 or not re.fullmatch(rb"[0-9]+\n", size_result.stdout):
        raise GitSupportError("固定 blob の size を解決できない")
    blob_size = int(size_result.stdout[:-1])
    if blob_size > max_bytes:
        raise GitSupportError("固定 blob が size 上限を超える")
    result = _git(
        root,
        ["cat-file", "blob", object_name],
        work_bytes=blob_size,
        max_output_bytes=max_bytes,
    )
    if result.returncode != 0:
        raise GitSupportError("commit または blob が存在せず固定参照を解決できない")
    if len(result.stdout) != blob_size:
        raise GitSupportError("固定 blob の宣言 size と読取 size が一致しない")
    actual = hashlib.sha256(result.stdout).hexdigest()
    if actual != expected_sha256:
        raise GitSupportError(
            f"固定 blob の SHA-256 が不一致: expected={expected_sha256}, actual={actual}"
        )
    return result.stdout
