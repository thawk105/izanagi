#!/usr/bin/env python3
"""dev-wave worktree の開始条件を変更なしで検査する。

この checker は観測専用であり、init / fetch / checkout などの修復操作は行わない。
qsub の有効性や投入先の計算資源は検査範囲外である。
"""
from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

_SUBMODULE_MARKER = Path("external/ccbench/CMakeLists.txt")
_SUBMODULE_GIT = Path("external/ccbench/.git")
_HANDOFF_DIR = Path("docs/handoff")
_MAIN_REF = "refs/heads/main"
_READ_ONLY_GIT_SUBCOMMANDS = frozenset(
    {"rev-list", "rev-parse", "status", "symbolic-ref"}
)
_ALLOWED_GIT_ENV = frozenset({"GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"})


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


def _git_env() -> dict[str, str]:
    """repository 選択用 GIT_* を除き、信頼済み設定だけを継承する。"""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") or key in _ALLOWED_GIT_ENV
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(repo: Path, *args: str) -> GitResult:
    """許可した読み取り専用 git command だけを、optional lock 無しで実行する。"""
    if not args or args[0] not in _READ_ONLY_GIT_SUBCOMMANDS:
        raise ValueError(f"mutating or unknown git subcommand is forbidden: {args!r}")
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(repo), *args],
            env=_git_env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except UnicodeDecodeError as exc:
        return GitResult(
            127,
            "",
            (
                f"git output is not UTF-8 ({exc}); "
                "git の出力・file 名を UTF-8 に是正する"
            ),
        )
    except OSError as exc:
        return GitResult(127, "", str(exc))
    return GitResult(completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def _one_line(text: str) -> str:
    return " ".join(text.split()) or "詳細なし"


def _git_failure(label: str, result: GitResult) -> str:
    return f"{label}: git の読み取りに失敗 ({_one_line(result.stderr)}); repository を確認する"


def _check_head_matches_main(repo: Path) -> list[str]:
    head = _git(repo, "rev-parse", "--verify", "HEAD")
    main = _git(repo, "rev-parse", "--verify", "refs/heads/main")
    failures: list[str] = []
    if head.returncode != 0:
        failures.append(_git_failure("HEAD", head))
    if main.returncode != 0:
        failures.append(_git_failure("local main", main))
    if not failures and head.stdout != main.stdout:
        failures.append(
            "HEAD != local main: local main と同じ commit から fresh worktree を作り直す"
        )
    return failures


def _check_fresh_branch(repo: Path) -> list[str]:
    branch = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch.returncode == 1:
        return ["detached HEAD: main 以外の作業 branch を checkout する"]
    if branch.returncode != 0:
        return [_git_failure("current branch", branch)]
    if branch.stdout == "main":
        return ["branch is main: main 以外の作業 branch を checkout する"]
    return []


def _git_path(repo: Path, name: str) -> tuple[Path | None, str | None]:
    result = _git(repo, "rev-parse", "--path-format=absolute", "--git-path", name)
    if result.returncode != 0:
        return None, _git_failure(f"git state {name}", result)
    return Path(result.stdout), None


def _check_no_operation_in_progress(repo: Path) -> list[str]:
    failures: list[str] = []
    active: list[str] = []
    for name in ("rebase-merge", "rebase-apply", "MERGE_HEAD"):
        path, error = _git_path(repo, name)
        if error:
            failures.append(error)
        elif path is not None and path.exists():
            active.append(name)
    if active:
        failures.append(
            f"rebase/merge in progress ({', '.join(active)}): 操作を完了または中止してから再実行する"
        )
    return failures


def _check_clean_tree(repo: Path) -> list[str]:
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        return [_git_failure("clean tree", status)]
    if status.stdout:
        return ["working tree is not clean: 変更を commit または退避してから再実行する"]
    return []


def _check_submodule_marker(repo: Path) -> list[str]:
    marker = repo / _SUBMODULE_MARKER
    git_entry = repo / _SUBMODULE_GIT
    try:
        marker_metadata = marker.lstat()
    except OSError:
        marker_metadata = None
    try:
        git_metadata = git_entry.lstat()
    except OSError:
        git_metadata = None
    if (
        marker_metadata is not None
        and stat.S_ISREG(marker_metadata.st_mode)
        and git_metadata is not None
        and not stat.S_ISLNK(git_metadata.st_mode)
    ):
        return []
    return [
        "submodule is not initialized "
        f"({_SUBMODULE_MARKER} must be a non-symlink regular file and "
        f"{_SUBMODULE_GIT} must exist without being a symlink): "
        "親セッションで submodule を初期化する"
    ]


def _check_worktree_handoff(repo: Path) -> list[str]:
    handoff = repo / _HANDOFF_DIR
    try:
        metadata = handoff.lstat()
    except FileNotFoundError:
        return []
    except OSError as exc:
        return [f"{_HANDOFF_DIR} を検査できない ({exc}): handoff path を修復する"]
    if stat.S_ISLNK(metadata.st_mode):
        return [f"{_HANDOFF_DIR} is a symlink: worktree 内の symlink を除去する"]
    if not stat.S_ISDIR(metadata.st_mode):
        return [f"{_HANDOFF_DIR} is not a directory: worktree 内の handoff path を修復する"]
    leftovers: list[str] = []
    try:
        entries = list(handoff.iterdir())
    except OSError as exc:
        return [f"{_HANDOFF_DIR} を列挙できない ({exc}): handoff path を修復する"]
    for path in entries:
        try:
            entry_metadata = path.lstat()
        except OSError:
            leftovers.append(path.name)
            continue
        if path.name != "README.md" or not stat.S_ISREG(entry_metadata.st_mode):
            leftovers.append(path.name)
    leftovers.sort()
    if not leftovers:
        return []
    return [
        "worktree-local handoff remains "
        f"({', '.join(leftovers)}): 外部 handoff を正本にして worktree 内の残置を除く"
    ]


def _check_external_handoff_file(repo: Path, handoff: Path) -> list[str]:
    try:
        metadata = handoff.lstat()
    except OSError as exc:
        return [
            f"external handoff が実在しない ({handoff}: {exc}): "
            "repo 外に regular file を作成して指定する"
        ]
    if not stat.S_ISREG(metadata.st_mode):
        return [
            f"external handoff is not a non-symlink regular file ({handoff}): "
            "repo 外の regular file を指定する"
        ]
    try:
        resolved = handoff.resolve(strict=True)
    except OSError as exc:
        return [
            f"external handoff を解決できない ({handoff}: {exc}): "
            "repo 外の regular file を指定する"
        ]
    try:
        resolved.relative_to(repo)
    except ValueError:
        return []
    return [
        f"external handoff is inside repository ({resolved}): "
        "repo 外の regular file を指定する"
    ]


def describe_main_divergence(repo: Path) -> str:
    """HEAD が local main から何 commit 遅れているかを 1 行で述べる。

    これは可視化であり gate ではない。worktree の `docs/` は基準 commit の凍結写しなので、
    遅れている間に他 session が land した裁定を見落とす (F67)。乖離が無い場合も必ず述べ、
    取得できない場合もその旨を述べる — 出ないことがあると、読み手が「乖離が無い」のか
    「表示が壊れている」のかを区別できず、恒真な保証になる。

    失敗しても呼び手の受理集合は変えない (fail-open)。ここで停止させると、並行 session が
    land するたびに無関係な理由で wave の起動が止まる。
    """
    result = _git(repo, "rev-list", "--count", f"HEAD..{_MAIN_REF}")
    if result.returncode != 0:
        return (
            f"local main との乖離を取得できない ({_one_line(result.stderr)}): "
            "可視化のみ省略し検査は続行する"
        )
    try:
        behind = int(result.stdout)
    except ValueError:
        return (
            "local main との乖離を解釈できない "
            f"(rev-list の出力: {_one_line(result.stdout)}): "
            "可視化のみ省略し検査は続行する"
        )
    if behind == 0:
        return f"local main との乖離なし (0 commit; HEAD は {_MAIN_REF} を含む)"
    return (
        f"HEAD は local main より {behind} commit 遅れている: "
        "worklog・裁定・docs は local main 側を正本として読む (worktree の docs は凍結写し)"
    )


def check_repository(
    repo: Path,
    *,
    mode: str = "fresh",
    forbid_worktree_handoff: bool = False,
    external_handoff: Path | None = None,
) -> list[str]:
    """全適用項目を検査し、是正案付きの failure を集約する。"""
    repo = repo.resolve()
    failures: list[str] = []
    if mode == "fresh":
        failures.extend(_check_head_matches_main(repo))
        failures.extend(_check_fresh_branch(repo))
    failures.extend(_check_no_operation_in_progress(repo))
    if mode == "fresh":
        failures.extend(_check_clean_tree(repo))
    failures.extend(_check_submodule_marker(repo))
    if forbid_worktree_handoff or external_handoff is not None:
        failures.extend(_check_worktree_handoff(repo))
    if external_handoff is not None:
        failures.extend(_check_external_handoff_file(repo, external_handoff))
    return failures


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "dev-wave worktree の開始条件を passive に検査する。"
            "qsub の有効性・投入先資源は scope 外。"
        )
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="検査する repository root (既定: current working directory)",
    )
    parser.add_argument(
        "--mode",
        choices=("fresh", "resume"),
        default="fresh",
        help="fresh は全開始条件、resume は進行状態・submodule・handoff だけを検査",
    )
    parser.add_argument(
        "--forbid-worktree-handoff",
        action="store_true",
        help="docs/handoff に README.md 以外の worktree-local handoff が無いことも検査",
    )
    parser.add_argument(
        "--external-handoff",
        type=Path,
        metavar="PATH",
        help="repo 外にある実在 regular file の external handoff も検査",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    # 可視化は検査結果に依らず必ず先に出す (rc には一切影響させない)。
    # flush は stdout が pipe のとき NG 行 (stderr) との前後関係を保つため。
    print(f"INFO: {describe_main_divergence(args.repo)}", flush=True)
    failures = check_repository(
        args.repo,
        mode=args.mode,
        forbid_worktree_handoff=args.forbid_worktree_handoff,
        external_handoff=args.external_handoff,
    )
    if failures:
        for failure in failures:
            print(f"NG: {failure}", file=sys.stderr)
        return 1
    print(f"OK: wave startup checks passed ({args.mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
