# -*- coding: utf-8 -*-
"""実 repository の ``output/`` snapshot に共通する Git ignore 規則。"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


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
        for raw_line in tracked.stdout.split(b"\0"):
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
    for raw_line in completed.stdout.split(b"\0"):
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
