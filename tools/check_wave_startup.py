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
_SUPPORTED_MODES = ("fresh", "resume", "midflight")
_READ_ONLY_GIT_SUBCOMMANDS = frozenset(
    {"ls-files", "rev-list", "rev-parse", "status", "symbolic-ref"}
)
_ALLOWED_GIT_ENV = frozenset({"GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"})


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class _RepositoryObservations:
    main_behind_count: str | None = None


def _git_env() -> dict[str, str]:
    """repository 選択用 GIT_* を除き、信頼済み設定だけを継承する。"""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") or key in _ALLOWED_GIT_ENV
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def _run_git(repo: Path, *args: str, strip_stdout: bool) -> GitResult:
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
    stdout = completed.stdout.strip() if strip_stdout else completed.stdout
    return GitResult(completed.returncode, stdout, completed.stderr.strip())


def _git(repo: Path, *args: str) -> GitResult:
    """許可した読み取り専用 git command だけを、optional lock 無しで実行する。"""
    return _run_git(repo, *args, strip_stdout=True)


def _git_raw(repo: Path, *args: str) -> GitResult:
    """NUL 区切りを壊さず、許可した読み取り専用 git command を実行する。"""
    return _run_git(repo, *args, strip_stdout=False)


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


def _check_no_grafts(repo: Path) -> list[str]:
    common_dir = _git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common_dir.returncode != 0:
        return [_git_failure("git common directory", common_dir)]
    if not common_dir.stdout:
        return ["git common directory が空: repository metadata を修復する"]
    common_dir_path = Path(common_dir.stdout)
    if not common_dir_path.is_absolute():
        return [
            f"git common directory が絶対 path でない ({common_dir.stdout}): "
            "repository metadata を修復する"
        ]
    grafts = common_dir_path / "info" / "grafts"
    try:
        grafts.lstat()
    except FileNotFoundError:
        return []
    except OSError as exc:
        return [
            f"legacy graft metadata を検査できない ({exc}): "
            "git metadata の path・権限を修復する"
        ]
    return [
        "legacy graft metadata exists (info/grafts): "
        "graft を除去し raw commit history を確認してから再実行する"
    ]


def _check_main_is_direct_ref(repo: Path) -> list[str]:
    symbolic_main = _git(repo, "symbolic-ref", "--quiet", _MAIN_REF)
    if symbolic_main.returncode == 0:
        return [
            f"local main is a symbolic ref ({_MAIN_REF}): direct ref に修復して再実行する"
        ]
    if symbolic_main.returncode != 1:
        return [_git_failure("local main symbolic-ref", symbolic_main)]
    return []


def _check_head_contains_main(repo: Path) -> list[str]:
    """raw commit graph で HEAD が direct local main を包含することを検査する。"""
    failures = _check_no_grafts(repo)

    result = _git(repo, "rev-list", "--count", f"HEAD..{_MAIN_REF}")
    if result.returncode != 0:
        failures.append(
            "HEAD/local main containment: git の読み取りに失敗 "
            f"({_one_line(result.stderr)}): HEAD と {_MAIN_REF} の実在・履歴を確認する"
        )
        return failures
    count = result.stdout
    if (
        not count
        or not count.isascii()
        or not count.isdecimal()
        or (count != "0" and count.startswith("0"))
    ):
        failures.append(
            "HEAD/local main containment: rev-list の出力が canonical な非負の "
            "ASCII 整数でない "
            f"({_one_line(count)}): git repository を確認する"
        )
    elif count != "0":
        failures.append(
            f"HEAD does not contain local main ({count} commit behind): "
            "session 開始時は local main を取り込み、clean tree にしてから "
            "--mode resume を再実行する; session 開始 gate が成功した後の受入前は "
            "gate を再実行せず tools/dev_wave_wait.py acceptance の "
            "post-claim merge に任せる; "
            "待ち手・launcher・runnerのbytesを変える前進は先に取り込む（F524）"
        )
    return failures


def _check_main_divergence_measurable(
    repo: Path,
) -> tuple[list[str], str | None]:
    """raw commit graph 上の main 乖離を canonical な件数として測定する。"""
    result = _git(repo, "rev-list", "--count", f"HEAD..{_MAIN_REF}")
    if result.returncode != 0:
        return (
            [
                "HEAD/local main divergence measurement: git の読み取りに失敗 "
                f"({_one_line(result.stderr)}): HEAD と {_MAIN_REF} の実在・履歴を確認する"
            ],
            None,
        )
    count = result.stdout
    if (
        not count
        or not count.isascii()
        or not count.isdecimal()
        or (count != "0" and count.startswith("0"))
    ):
        return (
            [
                "HEAD/local main divergence measurement: rev-list の出力が canonical な"
                "非負の ASCII 整数でない "
                f"({_one_line(count)}): git repository を確認する"
            ],
            None,
        )
    return [], count


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
        "検査対象の worktree root で python3 tools/dev_wave_submodule_init.py "
        "--worktree <path> を実行し再検査する"
    ]


def _check_worktree_handoff(repo: Path) -> list[str]:
    """main との内容一致は check_repository の先行 clean-tree gate と連言で保証する。

    clean/smudge filter や EOL 変換がある path では raw bytes の一致までは含意しない。
    """
    tracked = _git_raw(
        repo,
        "ls-files",
        "-v",
        "--stage",
        "-z",
        "--",
        _HANDOFF_DIR.as_posix(),
    )
    if tracked.returncode != 0:
        return [_git_failure("worktree handoff index", tracked)]
    if tracked.stdout and not tracked.stdout.endswith("\0"):
        return [
            "worktree handoff index: git ls-files -v --stage -z の出力が "
            "NUL 終端でない: repository を確認する"
        ]

    direct_records: dict[str, tuple[str, str, str, str] | None] = {}
    records = tracked.stdout[:-1].split("\0") if tracked.stdout else []
    for record in records:
        index_metadata, separator, relative_path = record.partition("\t")
        fields = index_metadata.split()
        if not separator or len(fields) != 4 or not relative_path:
            return [
                "worktree handoff index: git ls-files -v --stage -z の record を"
                "解釈できない: repository を確認する"
            ]
        tag, mode, object_id, stage = fields
        index_path = Path(relative_path)
        if relative_path != _HANDOFF_DIR.as_posix() and index_path.parent != _HANDOFF_DIR:
            continue
        if relative_path in direct_records:
            direct_records[relative_path] = None
        else:
            direct_records[relative_path] = (tag, mode, object_id, stage)

    root_record = _HANDOFF_DIR.as_posix() in direct_records
    index_failures: list[str] = []
    accepted_names: set[str] = set()
    for relative_path, metadata in direct_records.items():
        if metadata is None:
            index_failures.append(
                "worktree handoff index contains duplicate path "
                f"({relative_path}): 重複 record を解消する"
            )
            continue
        if relative_path == _HANDOFF_DIR.as_posix():
            continue
        tag, mode, object_id, stage = metadata
        record_failures: list[str] = []
        if tag != "H":
            record_failures.append(
                "worktree handoff index tag is not H "
                f"({relative_path}: {tag}): assume-unchanged / skip-worktree 等の flag を解除する"
            )
        if stage != "0":
            record_failures.append(
                "worktree handoff index stage is not 0 "
                f"({relative_path}: {stage}): 未 merge の index record を解消する"
            )
        if mode not in {"100644", "100755"}:
            record_failures.append(
                "worktree handoff index mode is not 100644/100755 "
                f"({relative_path}: {mode}): regular file mode に修復する"
            )
        if record_failures:
            index_failures.extend(record_failures)
            continue
        main_entry = _git(
            repo,
            "rev-parse",
            "--verify",
            f"{_MAIN_REF}:{relative_path}",
        )
        if main_entry.returncode != 0:
            index_failures.append(
                "worktree handoff index entry is absent from main "
                f"({relative_path}): main に land してから再検査する"
            )
        elif main_entry.stdout != object_id:
            index_failures.append(
                "worktree handoff index OID differs from main "
                f"({relative_path}): index を main と同じ内容へ戻す"
            )
        else:
            accepted_names.add(Path(relative_path).name)

    root_record_failure = (
        f"worktree handoff index contains {_HANDOFF_DIR} itself: "
        "gitlink 等の root entry を除去する"
    )

    handoff = repo / _HANDOFF_DIR
    try:
        metadata = handoff.lstat()
    except FileNotFoundError:
        if root_record:
            index_failures.append(root_record_failure)
        return index_failures
    except OSError as exc:
        filesystem_failure = (
            f"{_HANDOFF_DIR} を検査できない ({exc}): handoff path を修復する"
        )
        if root_record:
            index_failures.append(root_record_failure)
        return [filesystem_failure, *index_failures]
    if stat.S_ISLNK(metadata.st_mode):
        filesystem_failure = f"{_HANDOFF_DIR} is a symlink: worktree 内の symlink を除去する"
        if root_record:
            index_failures.append(root_record_failure)
        return [filesystem_failure, *index_failures]
    if not stat.S_ISDIR(metadata.st_mode):
        filesystem_failure = (
            f"{_HANDOFF_DIR} is not a directory: worktree 内の handoff path を修復する"
        )
        if root_record:
            index_failures.append(root_record_failure)
        return [filesystem_failure, *index_failures]
    if root_record:
        index_failures.append(root_record_failure)
    if index_failures:
        return index_failures
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
        if not stat.S_ISREG(entry_metadata.st_mode) or path.name not in accepted_names:
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
    failures, _observations = _collect_repository_checks(
        repo,
        mode=mode,
        forbid_worktree_handoff=forbid_worktree_handoff,
        external_handoff=external_handoff,
    )
    return failures


def _collect_repository_checks(
    repo: Path,
    *,
    mode: str = "fresh",
    forbid_worktree_handoff: bool = False,
    external_handoff: Path | None = None,
) -> tuple[list[str], _RepositoryObservations]:
    """検査 failure と、同じ検査で得た観測値を集約する。"""
    repo = repo.resolve()
    if mode not in _SUPPORTED_MODES:
        return (
            [
                f"unsupported startup mode {mode!r}: "
                "fresh / resume / midflight のいずれかを明示する"
            ],
            _RepositoryObservations(),
        )
    if mode == "midflight" and (
        forbid_worktree_handoff or external_handoff is not None
    ):
        return (
            [
                "midflight mode does not accept --forbid-worktree-handoff / "
                "--external-handoff; 開始 gate には fresh / resume を使う"
            ],
            _RepositoryObservations(),
        )

    failures: list[str] = []
    if mode == "fresh":
        failures.extend(_check_head_matches_main(repo))
        failures.extend(_check_main_is_direct_ref(repo))
        failures.extend(_check_fresh_branch(repo))
        failures.extend(_check_no_operation_in_progress(repo))
        failures.extend(_check_clean_tree(repo))
        failures.extend(_check_submodule_marker(repo))
        if forbid_worktree_handoff or external_handoff is not None:
            failures.extend(_check_worktree_handoff(repo))
        if external_handoff is not None:
            failures.extend(_check_external_handoff_file(repo, external_handoff))
        return failures, _RepositoryObservations()

    if mode == "resume":
        failures.extend(_check_head_contains_main(repo))
        failures.extend(_check_main_is_direct_ref(repo))
        failures.extend(_check_fresh_branch(repo))
        failures.extend(_check_no_operation_in_progress(repo))
        failures.extend(_check_clean_tree(repo))
        failures.extend(_check_submodule_marker(repo))
        if forbid_worktree_handoff or external_handoff is not None:
            failures.extend(_check_worktree_handoff(repo))
        if external_handoff is not None:
            failures.extend(_check_external_handoff_file(repo, external_handoff))
        return failures, _RepositoryObservations()

    failures.extend(_check_no_grafts(repo))
    measurement_failures, main_behind_count = _check_main_divergence_measurable(repo)
    failures.extend(measurement_failures)
    failures.extend(_check_main_is_direct_ref(repo))
    failures.extend(_check_fresh_branch(repo))
    failures.extend(_check_no_operation_in_progress(repo))
    failures.extend(_check_submodule_marker(repo))
    return failures, _RepositoryObservations(main_behind_count=main_behind_count)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "dev-wave worktree の開始条件を passive に検査する。"
            "解決後の repo path を使う。qsub の有効性・投入先資源は scope 外。"
            "wave identity・branch 所有・--repo の同一性は認証しない。"
        )
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="検査する repository root (既定: current working directory を実行時に解決)",
    )
    parser.add_argument(
        "--mode",
        choices=_SUPPORTED_MODES,
        default="fresh",
        help=(
            "fresh は HEAD==main、resume は HEAD が direct main を包含することを要求し、"
            "その他の開始条件は共通。midflight は段 5 実装子 dispatch 直前専用で、"
            "開始 gate (fresh / resume) の代用ではない。HEAD/main 関係・clean tree・"
            "handoff を検査せず、main 乖離量は関門でない"
        ),
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
    parser = _parser()
    args = parser.parse_args(argv)
    if args.mode == "midflight" and (
        args.forbid_worktree_handoff or args.external_handoff is not None
    ):
        parser.error(
            "--mode midflight does not accept --forbid-worktree-handoff / "
            "--external-handoff"
        )
    repo = args.repo.resolve()
    # 可視化は検査結果に依らず必ず先に出す (rc には一切影響させない)。
    # flush は stdout が pipe のとき NG 行 (stderr) との前後関係を保つため。
    try:
        divergence = describe_main_divergence(repo)
    except Exception as exc:
        divergence = (
            f"local main との乖離を取得できない ({_one_line(str(exc))}): "
            "可視化のみ省略し検査は続行する"
        )
    print(f"INFO: {divergence}", flush=True)
    failures, observations = _collect_repository_checks(
        repo,
        mode=args.mode,
        forbid_worktree_handoff=args.forbid_worktree_handoff,
        external_handoff=args.external_handoff,
    )
    if args.mode == "midflight":
        print(
            "NOTE: midflight は段 5 実装子 dispatch 直前専用で、"
            "開始 gate (fresh / resume) の代用ではない; "
            "HEAD/main 関係・clean tree・handoff を検査しない",
            flush=True,
        )
        if observations.main_behind_count is not None:
            print(
                "NOTE: local main より "
                f"{observations.main_behind_count} commit 遅れている "
                "(gate の実測値; これは関門ではない)",
                flush=True,
            )
        clean_tree_failures = _check_clean_tree(repo)
        if not clean_tree_failures:
            print(
                "NOTE: working tree is clean "
                "(midflight は clean tree を検査しない)",
                flush=True,
            )
        elif clean_tree_failures == [
            "working tree is not clean: 変更を commit または退避してから再実行する"
        ]:
            print(
                "NOTE: working tree is not clean "
                "(midflight は clean tree を検査しない)",
                flush=True,
            )
        else:
            print(
                "NOTE: working tree cleanliness could not be observed "
                "(midflight は clean tree を検査しない; これは関門ではない)",
                flush=True,
            )
    if failures:
        for failure in failures:
            print(f"NG: {failure}", file=sys.stderr)
        return 1
    print(
        "OK: wave startup checks passed "
        f"({args.mode}; repo={repo}; "
        "wave identity・branch 所有・--repo の同一性は認証しない)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
