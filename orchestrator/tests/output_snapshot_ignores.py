# -*- coding: utf-8 -*-
"""実 repository の ``output/`` snapshot に共通する Git ignore 規則。"""
from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


_INDEX_BLOB_SHA256_CACHE: dict[tuple[bytes, str], str] = {}


@dataclass(frozen=True)
class GitIgnoredOutputAncestorDirectories:
    """Metadata を正規化する directory の規則由来集合。"""

    exact: frozenset[str]
    subtree_roots: frozenset[str]

    def contains(self, relative: str) -> bool:
        """``relative`` が exact ancestor または wildcard subtree 内かを返す。"""
        return relative in self.exact or any(
            not root
            or relative == root
            or relative.startswith(f"{root}/")
            for root in self.subtree_roots
        )


class GitIgnoredOutputPrefixes(tuple):
    """tracked 例外を保持しつつ従来の tuple 契約を保つ prefix 集合。"""

    git_visible_paths: frozenset[str]

    def __new__(
            cls,
            prefixes: tuple[str, ...],
            git_visible_paths: frozenset[str],
    ) -> GitIgnoredOutputPrefixes:
        instance = super().__new__(cls, prefixes)
        instance.git_visible_paths = git_visible_paths
        return instance


@dataclass(frozen=True)
class _GitOutputIndexSnapshot:
    blobs: dict[str, tuple[bytes, bytes, str]]
    fallback_reasons: tuple[str, ...]


def _git_failure(command: tuple[str, ...], completed) -> AssertionError:
    detail = completed.stderr
    if isinstance(detail, bytes):
        detail = detail.decode("utf-8", "replace")
    return AssertionError(
        f"{' '.join(command)} に失敗: {str(detail).strip() or completed.returncode}"
    )


def _run_git_bytes(
        repo_root: Path, command: tuple[str, ...],
        *, accepted_returncodes: frozenset[int] = frozenset({0}),
) -> subprocess.CompletedProcess:
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise AssertionError(
            f"{' '.join(command)} を実行できない: {exc}"
        ) from exc
    if completed.returncode not in accepted_returncodes:
        raise _git_failure(command, completed)
    return completed


def _one_git_path(command: tuple[str, ...], completed) -> Path:
    lines = completed.stdout.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise AssertionError(
            f"{' '.join(command)} が単一 path を返さない: {completed.stdout!r}"
        )
    return Path(os.fsdecode(lines[0])).expanduser()


def _nul_terminated_records(
        command: tuple[str, ...], stdout: bytes,
) -> tuple[bytes, ...]:
    if not stdout:
        return ()
    if not stdout.endswith(b"\0"):
        raise AssertionError(
            f"{' '.join(command)} が末尾 NUL のない出力を返した: {stdout!r}"
        )
    return tuple(stdout[:-1].split(b"\0"))


def _optional_rule_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return b""
    except OSError as exc:
        raise AssertionError(f"Git ignore 規則を読めない: {path}: {exc}") from exc


def _exclude_rule_sources(repo_root: Path) -> tuple[bytes, ...]:
    info_command = ("git", "rev-parse", "--git-path", "info/exclude")
    info_result = _run_git_bytes(repo_root, info_command)
    info_path = _one_git_path(info_command, info_result)
    if not info_path.is_absolute():
        info_path = repo_root / info_path

    config_command = ("git", "config", "--get", "core.excludesFile")
    config_result = _run_git_bytes(
        repo_root, config_command,
        accepted_returncodes=frozenset({0, 1}),
    )
    sources = [
        _optional_rule_bytes(repo_root / ".gitignore"),
        _optional_rule_bytes(info_path),
    ]
    if config_result.returncode == 0:
        config_path = _one_git_path(config_command, config_result)
        if not config_path.is_absolute():
            config_path = repo_root / config_path
        sources.append(_optional_rule_bytes(config_path))
    elif config_result.stdout:
        raise AssertionError(
            "git config --get core.excludesFile が rc=1 で stdout を返した: "
            f"{config_result.stdout!r}"
        )
    return tuple(sources)


def _rule_candidates(
        repo_root: Path,
) -> tuple[dict[bytes, bool], frozenset[bytes]]:
    literal_candidates: dict[bytes, bool] = {}
    wildcard_subtree_roots: set[bytes] = set()
    for source in _exclude_rule_sources(repo_root):
        for raw_line in source.splitlines():
            rule = raw_line.rstrip(b" ")
            if not rule or rule.startswith((b"#", b"!")):
                continue
            if b"\\" in rule or b"**" in rule:
                continue
            if rule.startswith(b"/"):
                rule = rule[1:]
            wildcard_at = next(
                (index for index, byte in enumerate(rule) if byte in b"*?["),
                None,
            )
            static = rule if wildcard_at is None else rule[:wildcard_at]
            if not static.startswith(b"output/"):
                continue
            if wildcard_at is None:
                candidate = rule.rstrip(b"/")
                if candidate:
                    literal_candidates[candidate] = (
                        literal_candidates.get(candidate, False)
                        or rule.endswith(b"/")
                    )
                continue

            relative_static = static.removeprefix(b"output/")
            if relative_static.endswith(b"/"):
                subtree_root = relative_static.rstrip(b"/")
            else:
                subtree_root = relative_static.rpartition(b"/")[0]
            wildcard_subtree_roots.add(subtree_root)
    return literal_candidates, frozenset(wildcard_subtree_roots)


def _check_rule_candidates(
        repo_root: Path, candidates: dict[bytes, bool],
) -> frozenset[bytes]:
    if not candidates:
        return frozenset()
    query_to_candidate = {
        candidate + (b"/" if directory_rule else b""): candidate
        for candidate, directory_rule in candidates.items()
    }
    command = ("git", "check-ignore", "--no-index", "--stdin", "-z")
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            check=False,
            input=b"\0".join(sorted(query_to_candidate)) + b"\0",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise AssertionError(f"git check-ignore を実行できない: {exc}") from exc

    if completed.returncode == 0:
        if not completed.stdout or not completed.stdout.endswith(b"\0"):
            raise AssertionError(
                "git check-ignore が rc=0 で正しい NUL 出力を返さない: "
                f"{completed.stdout!r}"
            )
        fields = completed.stdout[:-1].split(b"\0")
        matched_queries = frozenset(fields)
        if b"" in matched_queries or not matched_queries.issubset(query_to_candidate):
            raise AssertionError(
                "git check-ignore が入力候補外の path を返した: "
                f"{sorted(matched_queries - set(query_to_candidate))!r}"
            )
    elif completed.returncode == 1:
        if completed.stdout:
            raise AssertionError(
                "git check-ignore が rc=1 で stdout を返した: "
                f"{completed.stdout!r}"
            )
        matched_queries = frozenset()
    else:
        raise _git_failure(command, completed)
    return frozenset(query_to_candidate[query] for query in matched_queries)


def _git_ignored_output_snapshot_rules(
        repo_root: Path,
) -> tuple[GitIgnoredOutputPrefixes, GitIgnoredOutputAncestorDirectories]:
    # process 内 memo は意図的に置かない。末尾の ``ls-files -o -i`` は
    # snapshot ごとの実在状態を観測する必要がある。prefix と ancestor の双方が必要な
    # caller はこの 1 回の評価を共有し、規則 source と index の照会だけを重複させない。
    candidates, wildcard_roots = _rule_candidates(repo_root)
    matched = _check_rule_candidates(repo_root, candidates)
    prefixes: set[str] = set()
    for raw_prefix in matched:
        if raw_prefix == b"output":
            raise AssertionError(
                "output/ 全体が Git ignore 対象のため snapshot 検査を実行できない"
            )
        if not raw_prefix.startswith(b"output/"):
            raise AssertionError(
                "規則由来の output/ 外 path が check-ignore に一致した: "
                f"{raw_prefix!r}"
            )
        prefixes.add(os.fsdecode(raw_prefix.removeprefix(b"output/")))

    tracked_paths: set[str] = set()
    if prefixes:
        tracked_command = (
            "git", "ls-files", "--cached", "-z", "--",
            *(f":(literal)output/{prefix}" for prefix in sorted(prefixes)),
        )
        tracked = _run_git_bytes(repo_root, tracked_command)
        for raw_line in _nul_terminated_records(tracked_command, tracked.stdout):
            if not raw_line:
                continue
            if not raw_line.startswith(b"output/"):
                raise AssertionError(
                    "git ls-files --cached が output/ 外の path を返した: "
                    f"{raw_line!r}"
                )
            tracked_paths.add(os.fsdecode(raw_line.removeprefix(b"output/")))

    command = (
        "git", "ls-files", "-o", "-i", "--exclude-standard", "--directory",
        "-z", "--", "output/",
    )
    completed = _run_git_bytes(repo_root, command)
    for raw_line in _nul_terminated_records(command, completed.stdout):
        if not raw_line:
            continue
        normalized = raw_line.rstrip(b"/")
        if normalized == b"output":
            raise AssertionError(
                "output/ 全体が Git ignore 対象のため snapshot 検査を実行できない"
            )
        if normalized.startswith(b"output/"):
            prefixes.add(os.fsdecode(normalized.removeprefix(b"output/")))
        else:
            raise AssertionError(
                f"git ls-files が output/ 外の path を返した: {raw_line!r}"
            )

    tracked_ancestors: set[str] = set()
    for tracked_path in tracked_paths:
        components = tracked_path.split("/")
        tracked_ancestors.update(
            "/".join(components[:end])
            for end in range(1, len(components))
        )

    exact_ancestors = {".", *tracked_ancestors}
    for raw_candidate in matched:
        if raw_candidate == b"output":
            continue
        prefix = os.fsdecode(raw_candidate.removeprefix(b"output/"))
        components = prefix.split("/")
        exact_ancestors.update(
            "/".join(components[:end])
            for end in range(1, len(components))
        )
    return (
        GitIgnoredOutputPrefixes(
            tuple(sorted(prefixes)),
            frozenset(tracked_paths | tracked_ancestors),
        ),
        GitIgnoredOutputAncestorDirectories(
            exact=frozenset(exact_ancestors),
            subtree_roots=frozenset(
                os.fsdecode(root) for root in wildcard_roots
            ),
        ),
    )


def git_ignored_output_snapshot_rules(
        repo_root: Path,
) -> tuple[GitIgnoredOutputPrefixes, GitIgnoredOutputAncestorDirectories]:
    """1 回の snapshot に必要な prefix、ancestor、tracked 例外を返す。"""
    return _git_ignored_output_snapshot_rules(repo_root)


def git_ignored_output_prefixes(repo_root: Path) -> GitIgnoredOutputPrefixes:
    """Git が ignore する ``output/`` 配下の path を相対 prefix で返す。

    非実在の literal 候補は repository root の ``.gitignore``、
    ``git rev-parse --git-path info/exclude`` の返す file、および
    ``git config --get core.excludesFile`` の設定 file の規則 bytes だけから作る。
    wildcard 規則は有限展開できないため、従来どおり実在後に ``git ls-files``
    側で得られるものだけが prefix になる。
    """
    prefixes, _ancestors = _git_ignored_output_snapshot_rules(repo_root)
    return prefixes


def git_ignored_output_ancestor_directories(
        repo_root: Path,
) -> GitIgnoredOutputAncestorDirectories:
    """規則由来 ignored prefix の祖先 directory 集合を返す。

    ``exact`` は literal prefix の厳密な祖先と、ignore 規則配下にある tracked
    path の祖先を含み、root ``.`` は常に含む。
    ``subtree_roots`` は wildcard より前の静的 directory であり、その directory と
    配下の全 directory を祖先扱いする。untracked tree の実在には依存しない。
    """
    _prefixes, ancestors = _git_ignored_output_snapshot_rules(repo_root)
    return ancestors


def _walk_output_entries(output: Path) -> list[tuple[str, str, str]]:
    """``rglob`` と同じ entry 集合を symlink 非追跡で列挙する。"""
    entries = []
    stack = [os.fspath(output)]
    base = os.fspath(output)
    while stack:
        current = stack.pop()
        with os.scandir(current) as iterator:
            items = list(iterator)
        for entry in items:
            relative = os.path.relpath(entry.path, base).replace(os.sep, "/")
            if entry.is_symlink():
                entries.append(("symlink", relative, entry.path))
            elif entry.is_dir(follow_symlinks=False):
                entries.append(("dir", relative, entry.path))
                stack.append(entry.path)
            elif entry.is_file(follow_symlinks=False):
                entries.append(("file", relative, entry.path))
    return entries


def _sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _git_worktree_output_prefix(
        repo_root: Path, output: Path,
) -> tuple[Path, str] | None:
    """``output`` が属する worktree root と repo-relative prefix を返す。"""
    command = ("git", "rev-parse", "--show-toplevel")
    completed = _run_git_bytes(
        repo_root, command, accepted_returncodes=frozenset({0, 128}),
    )
    if completed.returncode == 128:
        return None
    worktree_root = _one_git_path(command, completed).resolve(strict=False)
    try:
        relative = output.resolve(strict=False).relative_to(worktree_root)
    except (OSError, RuntimeError, ValueError):
        return None
    return worktree_root, relative.as_posix()


def _output_relative_path(repo_relative: str, output_prefix: str) -> str | None:
    if output_prefix in ("", "."):
        return repo_relative
    if repo_relative == output_prefix:
        return ""
    prefix = f"{output_prefix}/"
    if repo_relative.startswith(prefix):
        return repo_relative[len(prefix):]
    return None


def _root_attributes_enable_checkout_conversion(
        worktree_root: Path, blob_sha: bytes | None,
) -> bool:
    if blob_sha is None:
        return False
    command = ("git", "cat-file", "blob", blob_sha.decode("ascii"))
    completed = _run_git_bytes(worktree_root, command)
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(b"#"):
            continue
        fields = line.split()
        for token in fields[1:]:
            if (
                    token == b"text"
                    or token.startswith(b"text=")
                    or token.startswith(b"eol=")
                    or token == b"ident"
                    or token.startswith(b"working-tree-encoding=")
                    or token.startswith(b"filter=")
            ):
                return True
    return False


def _core_autocrlf_enables_checkout_conversion(worktree_root: Path) -> bool:
    command = ("git", "config", "--get", "core.autocrlf")
    completed = _run_git_bytes(
        worktree_root, command, accepted_returncodes=frozenset({0, 1}),
    )
    if completed.returncode == 1:
        if completed.stdout:
            raise AssertionError(
                "git config --get core.autocrlf が rc=1 で stdout を返した: "
                f"{completed.stdout!r}"
            )
        return False
    return completed.stdout.strip().lower() != b"false"


def _index_blobs_for_output(
        worktree_root: Path, output_prefix: str,
) -> _GitOutputIndexSnapshot:
    output_pathspec = (
        "." if output_prefix in ("", ".")
        else f":(literal){output_prefix}"
    )
    command = (
        "git", "ls-files", "-s", "-v", "-z", "--",
        ":(literal).gitattributes", output_pathspec,
    )
    completed = _run_git_bytes(worktree_root, command)
    blobs: dict[str, tuple[bytes, bytes, str]] = {}
    fallback_reasons: list[str] = []
    root_attributes_blob: bytes | None = None
    for record in _nul_terminated_records(command, completed.stdout):
        if not record:
            continue
        if len(record) < 3 or record[1:2] != b" ":
            raise AssertionError(
                f"git ls-files -s -v が不正な flag を返した: {record!r}"
            )
        flag = record[:1]
        metadata, separator, raw_path = record[2:].partition(b"\t")
        fields = metadata.split(b" ")
        if not separator or not raw_path or len(fields) != 3:
            raise AssertionError(
                f"git ls-files -s -v が不正な entry を返した: {record!r}"
            )
        mode, blob_sha, stage = fields
        repo_relative = os.fsdecode(raw_path)
        relative = _output_relative_path(repo_relative, output_prefix)
        if repo_relative == ".gitattributes":
            if stage == b"0":
                root_attributes_blob = blob_sha
        if relative is None:
            if repo_relative == ".gitattributes":
                continue
            raise AssertionError(
                "git ls-files -s -v が対象外の path を返した: "
                f"{raw_path!r}"
            )
        if flag == b"S":
            fallback_reasons.append("skip-worktree")
        elif b"a" <= flag <= b"z":
            fallback_reasons.append("assume-unchanged")
        if (
                relative == ".gitattributes"
                or relative.endswith("/.gitattributes")
        ):
            fallback_reasons.append("subtree-gitattributes")
        if stage == b"0":
            blobs[relative] = (mode, blob_sha, repo_relative)

    if _core_autocrlf_enables_checkout_conversion(worktree_root):
        fallback_reasons.append("core.autocrlf")
    if _root_attributes_enable_checkout_conversion(
            worktree_root, root_attributes_blob,
    ):
        fallback_reasons.append("root-gitattributes-conversion")
    return _GitOutputIndexSnapshot(
        blobs=blobs,
        fallback_reasons=tuple(dict.fromkeys(fallback_reasons)),
    )


def _status_paths_for_output(
        worktree_root: Path, output_prefix: str,
) -> frozenset[str]:
    command = (
        "git", "status", "--porcelain=v1", "-uall", "-z", "--",
        f":(literal){output_prefix}",
    )
    completed = _run_git_bytes(worktree_root, command)
    records = _nul_terminated_records(command, completed.stdout)
    changed: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            raise AssertionError(
                "git status --porcelain が途中に空 entry を返した"
            )
        if len(record) < 4 or record[2:3] != b" ":
            raise AssertionError(
                f"git status --porcelain が不正な entry を返した: {record!r}"
            )
        status_code = record[:2]
        raw_paths = [record[3:]]
        if b"R" in status_code or b"C" in status_code:
            if index >= len(records) or not records[index]:
                raise AssertionError(
                    "git status --porcelain の rename/copy 元 path がない"
                )
            raw_paths.append(records[index])
            index += 1
        for raw_path in raw_paths:
            relative = _output_relative_path(
                os.fsdecode(raw_path), output_prefix,
            )
            if relative is not None:
                changed.add(relative)
    return frozenset(changed)


def _path_is_changed(relative: str, changed: frozenset[str]) -> bool:
    candidate = relative
    while candidate:
        if candidate in changed:
            return True
        candidate, _separator, _name = candidate.rpartition("/")
    return "" in changed


def git_indexed_output_snapshot(
        output: Path,
        repo_root: Path,
        *,
        walk_entries: Callable[[Path], list[tuple[str, str, str]]] | None = None,
        digest_file: Callable[[str], str] | None = None,
) -> tuple[tuple[object, ...], ...]:
    """Git-visible tree を index blob cache 付きで内容 snapshot にする。

    ``output`` が ``repo_root`` の worktree 外なら、従来どおり全 regular file を
    読む。worktree 内でも directory と symlink は毎回実 tree から列挙する。
    """
    if not output.exists():
        return ()
    walker = _walk_output_entries if walk_entries is None else walk_entries
    digester = _sha256_file if digest_file is None else digest_file
    ignored_prefixes, _ignored_ancestors = git_ignored_output_snapshot_rules(
        repo_root,
    )
    entries = [
        entry for entry in walker(output)
        if not is_git_ignored_output_path(entry[1], ignored_prefixes)
    ]

    context = _git_worktree_output_prefix(repo_root, output)
    tracked: dict[str, tuple[bytes, bytes, str]] = {}
    changed: frozenset[str] = frozenset()
    fallback_reasons: tuple[str, ...] = ()
    if context is not None:
        worktree_root, output_prefix = context
        index_snapshot = _index_blobs_for_output(worktree_root, output_prefix)
        tracked = index_snapshot.blobs
        fallback_reasons = index_snapshot.fallback_reasons
        changed = _status_paths_for_output(worktree_root, output_prefix)

    digest_by_relative = {}
    for kind, relative, absolute in entries:
        if kind != "file":
            continue
        index_entry = tracked.get(relative)
        cacheable = (
            not fallback_reasons
            and index_entry is not None
            and index_entry[0] in (b"100644", b"100755")
            and not _path_is_changed(relative, changed)
        )
        if not cacheable:
            digest_by_relative[relative] = digester(absolute)
            continue
        blob_sha = index_entry[1]
        repo_relative = index_entry[2]
        cache_key = (blob_sha, repo_relative)
        digest = _INDEX_BLOB_SHA256_CACHE.get(cache_key)
        if digest is None:
            digest = digester(absolute)
            _INDEX_BLOB_SHA256_CACHE[cache_key] = digest
        digest_by_relative[relative] = digest

    snapshot = []
    for kind, relative, absolute in entries:
        if kind == "symlink":
            snapshot.append((
                "symlink", relative, Path(absolute).readlink().as_posix(),
            ))
        elif kind == "file":
            snapshot.append(("file", relative, digest_by_relative[relative]))
        else:
            snapshot.append(("dir", relative))
    snapshot.sort(key=lambda row: row[1])
    return tuple(snapshot)


def git_visible_output_metadata_snapshot(
        root: Path, repo_root: Path,
) -> tuple[tuple[object, ...], ...]:
    """Git-visible entry の現行 metadata tuple を共有実装で返す。"""
    ignored_prefixes, ignored_ancestors = git_ignored_output_snapshot_rules(
        repo_root,
    )
    entries = [
        root,
        *(
            path for path in root.rglob("*")
            if not is_git_ignored_output_path(
                path.relative_to(root).as_posix(), ignored_prefixes,
            )
        ),
    ]
    snapshot = []
    for path in sorted(entries):
        relative = path.relative_to(root).as_posix() if path != root else "."
        info = path.lstat()
        normalize = (
            stat.S_ISDIR(info.st_mode)
            and ignored_ancestors.contains(relative)
        )
        snapshot.append((
            relative,
            info.st_mode,
            None if normalize else info.st_size,
            None if normalize else info.st_mtime_ns,
            None if normalize else info.st_ctime_ns,
        ))
    return tuple(snapshot)


def is_git_ignored_output_path(
        relative: str,
        ignored_prefixes: tuple[str, ...],
) -> bool:
    """相対 path 自身またはその祖先 directory が ignore 対象かを返す。"""
    if isinstance(ignored_prefixes, GitIgnoredOutputPrefixes):
        if relative in ignored_prefixes.git_visible_paths:
            return False
    return any(
        relative == prefix
        or relative.startswith(f"{prefix}/")
        for prefix in ignored_prefixes
    )
