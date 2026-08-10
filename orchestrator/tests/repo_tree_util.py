"""実 repo tree の tracked + untracked 不変性を検査する pytest 非依存 helper。"""
from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


class RepoTreeSnapshotError(RuntimeError):
    """git status snapshot 自体を取得できなかった。"""


class RepoTreeListError(RuntimeError):
    """tracked + untracked の path 一覧を取得できなかった。"""


def _repo_status(root: Path) -> bytes:
    try:
        return subprocess.run(
            ["git", "status", "--porcelain", "-z", "--untracked-files=all"],
            cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RepoTreeSnapshotError(f"git status snapshot を取得できない: {root}") from exc


def _decode_path(raw: bytes) -> str:
    return raw.decode("utf-8", "surrogateescape")


def _path_states(raw: bytes) -> dict[str, set[str]]:
    """porcelain -z を path -> status 集合へ変換する（rename/copy の二 path 対応）。"""
    states: dict[str, set[str]] = {}
    records = raw.split(b"\0")
    i = 0
    while i < len(records):
        record = records[i]
        if not record:
            i += 1
            continue
        if len(record) < 4 or record[2:3] != b" ":
            states.setdefault(_decode_path(record), set()).add("malformed")
            i += 1
            continue
        status = record[:2].decode("ascii", "replace")
        path = _decode_path(record[3:])
        states.setdefault(path, set()).add(status)
        if ("R" in status or "C" in status) and i + 1 < len(records):
            source = records[i + 1]
            if source:
                states.setdefault(_decode_path(source), set()).add(f"{status}:source")
                i += 1
        i += 1
    return states


def _unchanged_assertion(before: bytes, after: bytes) -> None:
    if before == after:
        return
    before_states = _path_states(before)
    after_states = _path_states(after)
    changed = sorted(
        path for path in set(before_states) | set(after_states)
        if before_states.get(path) != after_states.get(path)
    )
    if not changed:
        # status record 順だけが変わった場合も、関係 path を空メッセージにしない。
        changed = sorted(set(before_states) | set(after_states))
    raise AssertionError(
        "実 repo tree が変化した: "
        f"paths={changed!r} before={before!r} after={after!r}"
    )


def assert_repo_tree_unchanged(root: Path, action: Callable[[], T]) -> T:
    """action 前後の full porcelain bytes を比較し、変化 path 付きで失敗する。"""
    root = Path(root)
    before = _repo_status(root)
    try:
        result = action()
    except Exception:
        # action 自身の失敗時も、途中までの漏出を見逃さない。tree が同じなら原例外を保つ。
        after = _repo_status(root)
        _unchanged_assertion(before, after)
        raise
    after = _repo_status(root)
    _unchanged_assertion(before, after)
    return result


def list_tracked_and_untracked_files(root: Path) -> tuple[Path, ...]:
    """root の tracked + untracked（ignore 対象外）を相対 path で返す。

    呼出 process の cwd には依存せず、git 呼出しはこの関数内の 1 回だけである。
    """
    root = Path(root)
    try:
        raw = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RepoTreeListError(f"git ls-files を取得できない: {root}") from exc

    paths: list[Path] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        relative = Path(_decode_path(item))
        if relative.is_absolute() or ".." in relative.parts:
            raise RepoTreeListError(f"git ls-files が不正な相対 path を返した: {relative}")
        paths.append(relative)
    return tuple(paths)
