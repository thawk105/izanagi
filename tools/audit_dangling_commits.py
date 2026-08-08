#!/usr/bin/env python3
"""要確認の到達不能変更を検出する。

到達不能 commit が変更した path のうち、main にも他の local branch tip にも
存在しないものだけを報告する。fold が消費する tree は既定で除外する。

exit code: 0 = repo 外の同一実体による抑止後に取り残しなし / 1 = 取り残しあり / 2 = 実行不能
"""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXCLUDED_PREFIXES = ("docs/spool/", "docs/archive/")
DEFAULT_REPO = Path(__file__).resolve().parents[1]
OFFREPO_ROOT_ENV = "IZANAGI_DEV_WAVE_JOBS_DIR"
MAX_BLOB_SIZE = 32 * 1024 * 1024
READ_CHUNK_SIZE = 1024 * 1024
_PATH_EXTENDING_BYTES = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_/"
)

Finding = tuple[str, str, list[str]]
Suppression = tuple[str, str, Path]
ExternalCopy = tuple[str, str, Path]
RootRejection = tuple[Path, str]
OversizeBlob = tuple[str, str, int]
LIMITATION_NOTICE = (
    "検出対象外: 既存ファイルへの変更・削除・同名別内容・gitlink 更新"
)


@dataclass(frozen=True)
class AuditReport:
    findings: list[Finding]
    suppressions: list[Suppression]
    unreferenced_copies: list[ExternalCopy]
    requested_roots: tuple[Path, ...]
    accepted_roots: tuple[Path, ...]
    rejected_roots: tuple[RootRejection, ...]
    scan_performed: bool
    blob_failures: int
    scan_failures: int
    oversize_blobs: tuple[OversizeBlob, ...]
    reference_failure: str | None


@dataclass(frozen=True)
class _BlobCandidate:
    commit: str
    path: str
    basename: str
    executable: bool
    content: bytes
    digest: bytes


@dataclass(frozen=True)
class _ExternalMatch:
    path: Path
    root: Path


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """対象 repo に対して読み取り専用の git command を実行する。"""
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    env.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """対象 repo に対して raw bytes を返す読み取り専用 git command を実行する。"""
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    env.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _checked_git(repo: Path, *args: str) -> str:
    completed = _git(repo, *args)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"git {' '.join(args)} に失敗した (rc={completed.returncode}): {detail}"
        )
    return completed.stdout


def unreachable_commits(repo: Path) -> list[str]:
    """reflog を到達性の根に含めず、到達不能 commit の object ID を返す。"""
    output = _checked_git(
        repo,
        "fsck",
        "--unreachable",
        "--no-reflogs",
        "--no-progress",
        "--connectivity-only",
    )
    commits: list[str] = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[:2] == ["unreachable", "commit"]:
            commits.append(fields[2])
    return sorted(set(commits))


def changed_files(repo: Path, commit: str) -> list[str]:
    """commit が各親に対して変更した path を返す (root/merge commit を含む)。"""
    parent_line = _checked_git(
        repo, "rev-list", "--parents", "-n", "1", commit
    ).split()
    if not parent_line:
        raise RuntimeError(f"commit の親を取得できません: {commit}")
    diff_mode = "-c" if len(parent_line) > 2 else "-m"
    output = _checked_git(
        repo,
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-only",
        "-r",
        diff_mode,
        "-z",
        commit,
    )
    return sorted({path for path in output.split("\0") if path})


def tree_paths(repo: Path, ref: str) -> set[str]:
    """ref の tree に存在する全 path を返す。"""
    output = _checked_git(repo, "ls-tree", "-r", "--name-only", "-z", ref)
    return {path for path in output.split("\0") if path}


def branch_tip_commits(repo: Path) -> list[str]:
    """local branch tips の commit object ID を返す。"""
    output = _checked_git(
        repo,
        "for-each-ref",
        "--format=%(objectname)",
        "refs/heads/",
    )
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def commit_subject(repo: Path, commit: str) -> str:
    return _checked_git(repo, "show", "-s", "--format=%s", commit).strip()


def _commit_regular_blob(
    repo: Path,
    commit: str,
    path: str,
    cache: dict[bytes, tuple[bytes, bytes]],
) -> tuple[_BlobCandidate | None, bool, int | None]:
    """regular blob を取得し、(候補, 取得失敗, 超過 size) を返す。"""
    tree = _git_bytes(
        repo,
        "--literal-pathspecs",
        "ls-tree",
        "-z",
        "--full-tree",
        commit,
        "--",
        path,
    )
    if tree.returncode != 0:
        return None, True, None
    records = [record for record in tree.stdout.split(b"\0") if record]
    if not records:
        return None, False, None
    if len(records) != 1 or b"\t" not in records[0]:
        return None, True, None
    metadata, recorded_path = records[0].split(b"\t", 1)
    fields = metadata.split()
    if len(fields) != 3 or recorded_path != os.fsencode(path):
        return None, True, None
    mode, object_type, object_id = fields
    if mode not in {b"100644", b"100755"} or object_type != b"blob":
        return None, False, None
    if len(object_id) not in {40, 64} or any(
        byte not in b"0123456789abcdef" for byte in object_id
    ):
        return None, True, None
    object_id_text = object_id.decode("ascii")

    size_result = _git_bytes(repo, "cat-file", "-s", object_id_text)
    if size_result.returncode != 0:
        return None, True, None
    try:
        size = int(size_result.stdout.strip())
    except ValueError:
        return None, True, None
    if size > MAX_BLOB_SIZE:
        return None, False, size

    cached = cache.get(object_id)
    if cached is None:
        content_result = _git_bytes(repo, "cat-file", "blob", object_id_text)
        if content_result.returncode != 0 or len(content_result.stdout) != size:
            return None, True, None
        content = content_result.stdout
        cached = (content, hashlib.sha256(content).digest())
        cache[object_id] = cached
    content, digest = cached
    return (
        _BlobCandidate(
            commit=commit,
            path=path,
            basename=Path(path).name,
            executable=mode == b"100755",
            content=content,
            digest=digest,
        ),
        False,
        None,
    )


def _validate_offrepo_roots(
    repo: Path,
    roots: Sequence[Path | str],
) -> tuple[tuple[Path, ...], tuple[Path, ...], tuple[RootRejection, ...]]:
    """探索根を絶対 path 化し、worktree と重なる root を拒否する。"""
    if not roots:
        return (), (), ()
    worktree = Path(_checked_git(repo, "rev-parse", "--show-toplevel").strip()).resolve()
    requested: list[Path] = []
    accepted: list[Path] = []
    rejected: list[RootRejection] = []
    seen: set[Path] = set()
    for raw_root in roots:
        try:
            root = Path(raw_root).resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            fallback = Path(raw_root).absolute()
            rejected.append((fallback, f"絶対 path 化不能: {exc}"))
            if fallback not in seen:
                requested.append(fallback)
                seen.add(fallback)
            continue
        if root in seen:
            continue
        seen.add(root)
        requested.append(root)
        if root == Path(root.anchor):
            rejected.append((root, "filesystem root は探索範囲が広すぎる"))
        elif root == worktree:
            rejected.append((root, "対象 worktree と同一"))
        elif root.is_relative_to(worktree):
            rejected.append((root, "対象 worktree の子孫"))
        elif worktree.is_relative_to(root):
            rejected.append((root, "対象 worktree の祖先"))
        else:
            accepted.append(root)
    return tuple(requested), tuple(accepted), tuple(rejected)


def _compare_regular_candidate(
    path: Path,
    initial_stat: os.stat_result,
    candidate: _BlobCandidate,
) -> tuple[bool, bool]:
    """外部 regular file を全体保持せず hash 後に chunk 単位で比較する。"""
    if not stat.S_ISREG(initial_stat.st_mode):
        return False, False
    if initial_stat.st_size != len(candidate.content):
        return False, False
    if bool(initial_stat.st_mode & stat.S_IXUSR) != candidate.executable:
        return False, False
    nofollow = getattr(os, "O_NOFOLLOW", None)
    cloexec = getattr(os, "O_CLOEXEC", None)
    if nofollow is None or cloexec is None:
        return False, True

    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | cloexec | nofollow)
        opened_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_dev != initial_stat.st_dev
            or opened_stat.st_ino != initial_stat.st_ino
            or opened_stat.st_size != len(candidate.content)
            or bool(opened_stat.st_mode & stat.S_IXUSR) != candidate.executable
        ):
            return False, True

        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, READ_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
        if total != len(candidate.content):
            return False, True
        if digest.digest() != candidate.digest:
            return False, False

        os.lseek(descriptor, 0, os.SEEK_SET)
        offset = 0
        while offset < len(candidate.content):
            chunk = os.read(
                descriptor,
                min(READ_CHUNK_SIZE, len(candidate.content) - offset),
            )
            if not chunk or chunk != candidate.content[offset : offset + len(chunk)]:
                return False, True
            offset += len(chunk)
        if os.read(descriptor, 1):
            return False, True
        final_stat = os.fstat(descriptor)
        if (
            final_stat.st_size,
            final_stat.st_mtime_ns,
            final_stat.st_ctime_ns,
            final_stat.st_ino,
            final_stat.st_mode,
        ) != (
            opened_stat.st_size,
            opened_stat.st_mtime_ns,
            opened_stat.st_ctime_ns,
            opened_stat.st_ino,
            opened_stat.st_mode,
        ):
            return False, True
        return True, False
    except OSError:
        return False, True
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _find_offrepo_matches(
    roots: Sequence[Path],
    candidates: Sequence[_BlobCandidate],
) -> tuple[dict[tuple[str, str], list[_ExternalMatch]], int, bool]:
    """各 root を一度だけ走査し、条件 1〜4 を満たす実体を列挙する。"""
    if not candidates:
        return {}, 0, False
    by_basename: dict[str, dict[int, list[_BlobCandidate]]] = {}
    for candidate in candidates:
        by_basename.setdefault(candidate.basename, {}).setdefault(
            len(candidate.content), []
        ).append(candidate)

    matches: dict[tuple[str, str], list[_ExternalMatch]] = {}
    failures = 0
    for root in sorted(roots):
        try:
            root_stat = root.lstat()
        except OSError:
            failures += 1
            continue
        permission_bits = stat.S_IMODE(root_stat.st_mode)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or permission_bits & 0o444 == 0
            or permission_bits & 0o111 == 0
        ):
            failures += 1
            continue

        def record_walk_error(_error: OSError) -> None:
            nonlocal failures
            failures += 1

        for directory, dirnames, filenames in os.walk(
            root,
            topdown=True,
            onerror=record_walk_error,
            followlinks=False,
        ):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                size_index = by_basename.get(filename)
                if size_index is None:
                    continue
                path = Path(directory) / filename
                try:
                    candidate_stat = path.lstat()
                except OSError:
                    failures += 1
                    continue
                if not stat.S_ISREG(candidate_stat.st_mode):
                    continue
                same_size = size_index.get(candidate_stat.st_size, ())
                for candidate in same_size:
                    identical, failed = _compare_regular_candidate(
                        path, candidate_stat, candidate
                    )
                    if failed:
                        failures += 1
                    if identical:
                        key = (candidate.commit, candidate.path)
                        match = _ExternalMatch(path=path.absolute(), root=root)
                        if match not in matches.setdefault(key, []):
                            matches[key].append(match)
    for found in matches.values():
        found.sort(key=lambda item: (str(item.path), str(item.root)))
    return matches, failures, True


def _reference_patterns(match: _ExternalMatch) -> tuple[str, ...]:
    patterns = [str(match.path)]
    ancestor = match.path.parent
    while ancestor != match.root:
        patterns.append(str(ancestor))
        if ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent
    return tuple(patterns)


def _has_bounded_path_reference(content: bytes, pattern: bytes) -> bool:
    """pattern が前後の path 境界を満たす出現を 1 つでも持つか返す。"""
    if not pattern:
        return False
    start = 0
    while True:
        index = content.find(pattern, start)
        if index < 0:
            return False
        end = index + len(pattern)
        left_extends = index > 0 and content[index - 1] in _PATH_EXTENDING_BYTES
        right_extends = (
            end < len(content) and content[end] in _PATH_EXTENDING_BYTES
        )
        if not left_extends and not right_extends:
            return True
        start = index + 1


def _landed_reference_matches(
    repo: Path,
    main_ref: str,
    matches: dict[tuple[str, str], list[_ExternalMatch]],
) -> tuple[dict[tuple[str, str], list[Path]], str | None]:
    """bytes 一致候補をまとめた一度の git grep で landed 参照を確認する。"""
    pattern_owners: dict[str, list[tuple[tuple[str, str], Path]]] = {}
    for key, external_matches in matches.items():
        for match in external_matches:
            for pattern in _reference_patterns(match):
                owner = (key, match.path)
                if owner not in pattern_owners.setdefault(pattern, []):
                    pattern_owners[pattern].append(owner)
    if not pattern_owners:
        return {}, None

    arguments = ["grep", "-F", "-l", "-z"]
    for pattern in sorted(pattern_owners):
        arguments.extend(("-e", pattern))
    arguments.extend((main_ref, "--"))
    grep_result = _git_bytes(repo, *arguments)
    if grep_result.returncode == 1:
        return {}, None
    if grep_result.returncode != 0:
        detail = (grep_result.stderr or grep_result.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        return {}, f"git grep rc={grep_result.returncode}: {detail}"

    prefix = os.fsencode(main_ref) + b":"
    contents: list[bytes] = []
    for record in grep_result.stdout.split(b"\0"):
        if not record:
            continue
        if not record.startswith(prefix):
            return {}, "git grep の path 出力を解釈できない"
        tree_path = os.fsdecode(record[len(prefix) :])
        show_result = _git_bytes(repo, "show", f"{main_ref}:{tree_path}")
        if show_result.returncode != 0:
            detail = (show_result.stderr or show_result.stdout).decode(
                "utf-8", errors="replace"
            ).strip()
            return {}, f"landed file の参照確認不能: {detail}"
        contents.append(show_result.stdout)

    referenced: dict[tuple[str, str], list[Path]] = {}
    for pattern, owners in pattern_owners.items():
        encoded = os.fsencode(pattern)
        if not any(
            _has_bounded_path_reference(content, encoded) for content in contents
        ):
            continue
        for key, external_path in owners:
            paths = referenced.setdefault(key, [])
            if external_path not in paths:
                paths.append(external_path)
    for paths in referenced.values():
        paths.sort(key=str)
    return referenced, None


def audit(
    repo: Path | str,
    main_ref: str = "main",
    excluded_prefixes: tuple[str, ...] = DEFAULT_EXCLUDED_PREFIXES,
) -> list[Finding]:
    """3 条件をすべて満たす commit と、その失われた path を返す。"""
    root = Path(repo).resolve()
    main_commit = _checked_git(
        root, "rev-parse", "--verify", f"{main_ref}^{{commit}}"
    )
    main_commit = main_commit.strip()
    main_paths = tree_paths(root, main_commit)

    other_tip_paths: set[str] = set()
    for tip in branch_tip_commits(root):
        if tip != main_commit:
            other_tip_paths.update(tree_paths(root, tip))

    findings: list[Finding] = []
    for commit in unreachable_commits(root):
        lost_paths: list[str] = []
        for path in changed_files(root, commit):
            if any(path.startswith(prefix) for prefix in excluded_prefixes):
                continue
            if path in main_paths:
                continue
            if path in other_tip_paths:
                continue
            lost_paths.append(path)
        if lost_paths:
            findings.append((commit, commit_subject(root, commit), lost_paths))
    return findings


def audit_with_offrepo(
    repo: Path | str,
    main_ref: str = "main",
    excluded_prefixes: tuple[str, ...] = DEFAULT_EXCLUDED_PREFIXES,
    *,
    offrepo_roots: Sequence[Path | str] = (),
) -> AuditReport:
    """既存 findings に repo 外の同一実体による抑止を後段適用する。"""
    root = Path(repo).resolve()
    original_findings = audit(repo, main_ref, excluded_prefixes)
    requested, accepted, rejected = _validate_offrepo_roots(root, offrepo_roots)
    if not requested or not accepted:
        return AuditReport(
            findings=original_findings,
            suppressions=[],
            unreferenced_copies=[],
            requested_roots=requested,
            accepted_roots=accepted,
            rejected_roots=rejected,
            scan_performed=False,
            blob_failures=0,
            scan_failures=0,
            oversize_blobs=(),
            reference_failure=None,
        )

    candidates: list[_BlobCandidate] = []
    blob_failures = 0
    oversize: list[OversizeBlob] = []
    blob_cache: dict[bytes, tuple[bytes, bytes]] = {}
    for commit, _subject, paths in original_findings:
        for path in paths:
            candidate, failed, oversize_bytes = _commit_regular_blob(
                root, commit, path, blob_cache
            )
            if failed:
                blob_failures += 1
            elif oversize_bytes is not None:
                oversize.append((commit, path, oversize_bytes))
            elif candidate is not None:
                candidates.append(candidate)

    matches, scan_failures, scan_performed = _find_offrepo_matches(
        accepted, candidates
    )
    referenced, reference_failure = _landed_reference_matches(
        root, main_ref, matches
    )

    suppressions: list[Suppression] = []
    unreferenced: list[ExternalCopy] = []
    remaining: list[Finding] = []
    for commit, subject, paths in original_findings:
        remaining_paths: list[str] = []
        for path in paths:
            key = (commit, path)
            referenced_paths = referenced.get(key, ()) if reference_failure is None else ()
            if referenced_paths:
                suppressions.append((commit, path, referenced_paths[0]))
                continue
            remaining_paths.append(path)
            if reference_failure is None and matches.get(key):
                unreferenced.append((commit, path, matches[key][0].path))
        if remaining_paths:
            remaining.append((commit, subject, remaining_paths))

    return AuditReport(
        findings=remaining,
        suppressions=suppressions,
        unreferenced_copies=unreferenced,
        requested_roots=requested,
        accepted_roots=accepted,
        rejected_roots=rejected,
        scan_performed=scan_performed,
        blob_failures=blob_failures,
        scan_failures=scan_failures,
        oversize_blobs=tuple(oversize),
        reference_failure=reference_failure,
    )


def _print_offrepo_report(report: AuditReport) -> None:
    if not report.requested_roots:
        print("audit_dangling_commits: repo 外の同一実体の探索を未実施")
        print(f"  --offrepo-root / {OFFREPO_ROOT_ENV} が未指定")
    else:
        print(
            "audit_dangling_commits: repo 外の同一実体の探索根 "
            f"{len(report.requested_roots)} 件"
        )
        for root in report.accepted_roots:
            print(f"  探索根: {root}")
        for root, reason in report.rejected_roots:
            print(f"  探索根を拒否 (抑止せず): {root} ({reason})")
        if report.accepted_roots and not report.scan_performed:
            print("  照合可能な候補 basename 0 件のため走査省略")
    for commit, path, size in report.oversize_blobs:
        print(
            f"  oversize (抑止せず): commit {commit}: {path} "
            f"({size} bytes; 上限 {MAX_BLOB_SIZE} bytes)"
        )
    if report.blob_failures:
        print(f"  blob 確認不能 {report.blob_failures} 件 (抑止せず)")
    if report.scan_failures:
        print(f"  repo 外候補の確認不能 {report.scan_failures} 件 (抑止せず)")
    if report.reference_failure is not None:
        print(f"  landed 参照確認不能 (抑止せず): {report.reference_failure}")

    print(
        "audit_dangling_commits: repo 外の同一実体で抑止 "
        f"{len(report.suppressions)} (commit, path) 対"
    )
    for commit, path, external_copy_path in report.suppressions:
        print(f"  commit {commit}: {path}")
        print(f"    repo 外の同一実体: {external_copy_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="要確認の到達不能変更を検出する",
        epilog=LIMITATION_NOTICE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_REPO,
        help=f"対象 repo (既定: {DEFAULT_REPO})",
    )
    parser.add_argument("--ref", default="main", help="取り込み先 ref (既定: main)")
    parser.add_argument(
        "--offrepo-root",
        type=Path,
        action="append",
        default=None,
        metavar="PATH",
        help=(
            "repo 外の同一実体の探索根。複数指定可。指定時は "
            f"{OFFREPO_ROOT_ENV} を完全に上書きする"
        ),
    )
    parser.add_argument(
        "--include-fold-trees",
        action="store_true",
        help="docs/spool/ と docs/archive/ も判定対象に含める",
    )
    args = parser.parse_args(argv)

    excluded = () if args.include_fold_trees else DEFAULT_EXCLUDED_PREFIXES
    if args.offrepo_root is not None:
        roots: Sequence[Path | str] = tuple(args.offrepo_root)
    else:
        environment_root = os.environ.get(OFFREPO_ROOT_ENV, "")
        roots = (environment_root,) if environment_root else ()
    try:
        report = audit_with_offrepo(
            args.repo,
            args.ref,
            excluded,
            offrepo_roots=roots,
        )
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"audit_dangling_commits: 実行できません: {exc}", file=sys.stderr)
        return 2

    _print_offrepo_report(report)
    if not report.findings:
        print(f"audit_dangling_commits: 要確認 0 件 ({LIMITATION_NOTICE})")
        return 0

    notes = {
        (commit, path): external_copy_path
        for commit, path, external_copy_path in report.unreferenced_copies
    }
    print(
        "audit_dangling_commits: 要確認の到達不能変更 "
        f"{len(report.findings)} commit"
    )
    for commit, subject, paths in report.findings:
        print(f"  commit {commit} ({subject})")
        for path in paths:
            external_copy_path = notes.get((commit, path))
            note = ""
            if external_copy_path is not None:
                note = (
                    " — repo 外に同一 bytes の実体あり "
                    f"(landed 参照なし): {external_copy_path}"
                )
            print(f"    main・全 local branch tip に不在: {path}{note}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
