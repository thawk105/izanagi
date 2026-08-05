#!/usr/bin/env python3
"""要確認の到達不能変更を検出する。

到達不能 commit が変更した path のうち、main にも他の local branch tip にも
存在しないものだけを報告する。fold が消費する tree は既定で除外する。

exit code: 0 = 取り残しなし / 1 = 取り残しあり / 2 = 実行不能
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_EXCLUDED_PREFIXES = ("docs/spool/", "docs/archive/")
DEFAULT_REPO = Path(__file__).resolve().parents[1]

Finding = tuple[str, str, list[str]]
LIMITATION_NOTICE = (
    "検出対象外: 既存ファイルへの変更・削除・同名別内容・gitlink 更新"
)


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
        "--include-fold-trees",
        action="store_true",
        help="docs/spool/ と docs/archive/ も判定対象に含める",
    )
    args = parser.parse_args(argv)

    excluded = () if args.include_fold_trees else DEFAULT_EXCLUDED_PREFIXES
    try:
        findings = audit(args.repo, args.ref, excluded)
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"audit_dangling_commits: 実行できません: {exc}", file=sys.stderr)
        return 2

    if not findings:
        print(f"audit_dangling_commits: 要確認 0 件 ({LIMITATION_NOTICE})")
        return 0

    print(f"audit_dangling_commits: 要確認の到達不能変更 {len(findings)} commit")
    for commit, subject, paths in findings:
        print(f"  commit {commit} ({subject})")
        for path in paths:
            print(f"    main・全 local branch tip に不在: {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
