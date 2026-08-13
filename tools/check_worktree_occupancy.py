#!/usr/bin/env python3
"""worktree への cwd / argv 参照による占有を検出する。

rc=0 は cwd / argv 参照による占有を inspect できた範囲で検出しなかったことだけを
表す。cmdline は列挙した PID 全体を走査するが、cwd は inspect できる PID に限られ、
他ユーザーおよび non-dumpable process の cwd は観測できない。同じ uid または uid
判定不能の観測不能 process は pid と comm を残る盲点として列挙するため、worker で
ありうる process が一つでもあれば削除してはならない。PID 走査後に始まる process、
別 PID namespace、FD 経由の参照も観測できないため、削除の必要条件であって十分条件
ではない。恒久解は lease であり、本 wave の scope 外である。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


UNOCCUPIED_RC = 0
OCCUPIED_RC = 1
INDETERMINATE_RC = 2
_SHELL_EXE_NAMES = frozenset({"bash", "sh", "dash", "zsh", "ksh"})
_CHECKER_PATH = Path(__file__).resolve()


@dataclass(frozen=True)
class Occupant:
    pid: int
    sources: tuple[str, ...]


@dataclass(frozen=True)
class ScanIssue:
    error: str
    pid: int | None
    source: str


@dataclass(frozen=True)
class Unreachable:
    cwd_permission: int


@dataclass(frozen=True)
class SameUidCwdUnreachable:
    pid: int
    comm: str | None


@dataclass(frozen=True)
class ScanReport:
    worktree: Path
    status: str
    occupants: tuple[Occupant, ...]
    issues: tuple[ScanIssue, ...]
    scanned: int
    same_uid_cwd_unreachable: tuple[SameUidCwdUnreachable, ...]
    unreachable: Unreachable


def _lexical_absolute(path: Path, *, base: Path | None = None) -> Path:
    if path.is_absolute():
        return Path(os.path.abspath(os.fspath(path)))
    anchor = Path.cwd() if base is None else base
    return Path(os.path.abspath(os.fspath(anchor / path)))


def _is_within(candidate: Path, target: Path) -> bool:
    if candidate == target:
        return True
    try:
        candidate.relative_to(target)
    except ValueError:
        return False
    return True


def _candidate_spellings(path: Path, *, base: Path) -> tuple[Path, ...]:
    lexical = _lexical_absolute(path, base=base)
    try:
        real = lexical.resolve(strict=False)
    except (OSError, RuntimeError):
        return (lexical,)
    if real == lexical:
        return (lexical,)
    return (lexical, real)


def _path_matches_targets(
    path: Path,
    *,
    base: Path,
    targets: tuple[Path, ...],
) -> bool:
    return any(
        _is_within(candidate, target)
        for candidate in _candidate_spellings(path, base=base)
        for target in targets
    )


def _argv_path_tokens(argv: Sequence[str]) -> tuple[str, ...]:
    candidates: list[str] = []
    for token in argv:
        if token:
            candidates.append(token)
        if "=" in token:
            rhs = token.split("=", 1)[1]
            if rhs:
                candidates.append(rhs)
    return tuple(candidates)


def _argv_matches_targets(
    argv: Sequence[str],
    *,
    process_cwd: Path | None,
    targets: tuple[Path, ...],
) -> bool:
    for token in _argv_path_tokens(argv):
        path = Path(token)
        if not path.is_absolute() and process_cwd is None:
            continue
        base = process_cwd if process_cwd is not None else Path("/")
        if _path_matches_targets(path, base=base, targets=targets):
            return True
    return False


def _argv_mentions_checker(
    argv: Sequence[str],
    *,
    process_cwd: Path | None,
) -> bool:
    checker_targets = (_CHECKER_PATH,)
    for token in _argv_path_tokens(argv):
        path = Path(token)
        if not path.is_absolute() and process_cwd is None:
            continue
        base = process_cwd if process_cwd is not None else Path("/")
        if any(
            candidate == checker
            for candidate in _candidate_spellings(path, base=base)
            for checker in checker_targets
        ):
            return True
    return False


def _read_starttime(pid_dir: Path) -> str:
    text = (pid_dir / "stat").read_text(encoding="utf-8")
    close_paren = text.rfind(")")
    if close_paren < 0:
        raise ValueError("stat comm terminator is missing")
    fields_after_comm = text[close_paren + 1 :].split()
    if len(fields_after_comm) <= 19:
        raise ValueError("stat starttime field is missing")
    return fields_after_comm[19]


def _read_process_cwd(pid_dir: Path) -> Path:
    cwd_link = pid_dir / "cwd"
    raw = Path(os.readlink(cwd_link))
    if not raw.is_absolute():
        raw = cwd_link.parent / raw
    return raw.resolve(strict=True)


def _read_cmdline(pid_dir: Path) -> tuple[str, ...]:
    raw = (pid_dir / "cmdline").read_bytes()
    return tuple(os.fsdecode(token) for token in raw.split(b"\0") if token)


def _read_process_uid(pid_dir: Path) -> int:
    for line in (pid_dir / "status").read_text(encoding="utf-8").splitlines():
        if not line.startswith("Uid:"):
            continue
        fields = line.removeprefix("Uid:").split()
        if not fields:
            break
        return int(fields[0])
    raise ValueError("status Uid field is missing")


def _read_process_comm(pid_dir: Path) -> str:
    return (pid_dir / "comm").read_text(encoding="utf-8").rstrip("\n")


def _parent_is_invoking_shell(
    pid_dir: Path,
    argv: Sequence[str],
    *,
    process_cwd: Path | None,
) -> bool:
    try:
        exe_name = (pid_dir / "exe").resolve(strict=True).name
    except (OSError, RuntimeError):
        return False
    return (
        exe_name in _SHELL_EXE_NAMES
        and _argv_mentions_checker(argv, process_cwd=process_cwd)
    )


def _issue(pid: int | None, source: str, exc: BaseException) -> ScanIssue:
    if isinstance(exc, PermissionError):
        error = "permission"
    elif isinstance(exc, FileNotFoundError):
        error = "missing"
    elif isinstance(exc, (ValueError, UnicodeError)):
        error = "invalid"
    else:
        error = "os-error"
    return ScanIssue(error=error, pid=pid, source=source)


def _pid_disappeared(pid_dir: Path) -> bool:
    try:
        return not pid_dir.exists()
    except OSError:
        return False


def _scan_pid(
    pid: int,
    pid_dir: Path,
    *,
    targets: tuple[Path, ...],
    self_pid: int,
    parent_pid: int,
    current_uid: int,
) -> tuple[
    Occupant | None,
    tuple[ScanIssue, ...],
    int,
    tuple[SameUidCwdUnreachable, ...],
] | None:
    try:
        start_before = _read_starttime(pid_dir)
    except FileNotFoundError as exc:
        if _pid_disappeared(pid_dir):
            return None
        return None, (_issue(pid, "stat", exc),), 0, ()
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        return None, (_issue(pid, "stat", exc),), 0, ()

    sources: set[str] = set()
    issues: list[ScanIssue] = []
    process_cwd: Path | None = None
    cwd_permission_unreachable = 0
    same_uid_cwd_unreachable: tuple[SameUidCwdUnreachable, ...] = ()

    try:
        process_cwd = _read_process_cwd(pid_dir)
        if any(_is_within(process_cwd, target) for target in targets):
            sources.add("cwd")
    except PermissionError:
        try:
            process_uid = _read_process_uid(pid_dir)
        except (OSError, RuntimeError, UnicodeError, ValueError):
            process_uid = None
        if process_uid is None or process_uid == current_uid:
            try:
                comm: str | None = _read_process_comm(pid_dir)
            except (OSError, RuntimeError, UnicodeError):
                comm = None
            same_uid_cwd_unreachable = (
                SameUidCwdUnreachable(pid=pid, comm=comm),
            )
        else:
            cwd_permission_unreachable = 1
    except FileNotFoundError as exc:
        if _pid_disappeared(pid_dir):
            return None
        issues.append(_issue(pid, "cwd", exc))
    except (OSError, RuntimeError, UnicodeError) as exc:
        issues.append(_issue(pid, "cwd", exc))

    if pid != self_pid:
        try:
            argv = _read_cmdline(pid_dir)
            ignore_cmdline = (
                pid == parent_pid
                and _parent_is_invoking_shell(
                    pid_dir,
                    argv,
                    process_cwd=process_cwd,
                )
            )
            if not ignore_cmdline and _argv_matches_targets(
                argv,
                process_cwd=process_cwd,
                targets=targets,
            ):
                sources.add("cmdline")
        except FileNotFoundError as exc:
            if _pid_disappeared(pid_dir):
                return None
            issues.append(_issue(pid, "cmdline", exc))
        except (OSError, RuntimeError, UnicodeError) as exc:
            issues.append(_issue(pid, "cmdline", exc))

    try:
        start_after = _read_starttime(pid_dir)
    except FileNotFoundError as exc:
        if _pid_disappeared(pid_dir):
            return None
        return (
            None,
            tuple(issues + [_issue(pid, "stat", exc)]),
            cwd_permission_unreachable,
            same_uid_cwd_unreachable,
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        return (
            None,
            tuple(issues + [_issue(pid, "stat", exc)]),
            cwd_permission_unreachable,
            same_uid_cwd_unreachable,
        )

    if start_after != start_before:
        return None, (
            ScanIssue(error="pid-reused", pid=pid, source="stat"),
        ), cwd_permission_unreachable, same_uid_cwd_unreachable

    occupant = None
    if sources:
        occupant = Occupant(pid=pid, sources=tuple(sorted(sources)))
    return (
        occupant,
        tuple(issues),
        cwd_permission_unreachable,
        same_uid_cwd_unreachable,
    )


def scan_worktree_occupancy(
    worktree: Path,
    *,
    proc_root: Path = Path("/proc"),
    self_pid: int | None = None,
    parent_pid: int | None = None,
) -> ScanReport:
    """cwd / argv 占有を走査する。未検出は削除の必要条件であり十分条件ではない。"""

    lexical_target = _lexical_absolute(Path(worktree))
    try:
        real_target = lexical_target.resolve(strict=True)
        if not real_target.is_dir():
            raise NotADirectoryError(real_target)
    except (OSError, RuntimeError) as exc:
        return ScanReport(
            worktree=lexical_target,
            status="indeterminate",
            occupants=(),
            issues=(_issue(None, "worktree", exc),),
            scanned=0,
            same_uid_cwd_unreachable=(),
            unreachable=Unreachable(cwd_permission=0),
        )

    targets = tuple(dict.fromkeys((lexical_target, real_target)))
    try:
        if not proc_root.is_dir():
            raise NotADirectoryError(proc_root)
        pid_dirs = sorted(
            (
                (int(entry.name), entry)
                for entry in proc_root.iterdir()
                if entry.name.isdecimal()
            ),
            key=lambda item: item[0],
        )
    except (OSError, RuntimeError, ValueError) as exc:
        return ScanReport(
            worktree=real_target,
            status="indeterminate",
            occupants=(),
            issues=(_issue(None, "proc-root", exc),),
            scanned=0,
            same_uid_cwd_unreachable=(),
            unreachable=Unreachable(cwd_permission=0),
        )

    actual_self_pid = os.getpid() if self_pid is None else self_pid
    actual_parent_pid = os.getppid() if parent_pid is None else parent_pid
    current_uid = os.getuid()
    occupants: list[Occupant] = []
    issues: list[ScanIssue] = []
    cwd_permission_unreachable = 0
    same_uid_cwd_unreachable: list[SameUidCwdUnreachable] = []
    for pid, pid_dir in pid_dirs:
        result = _scan_pid(
            pid,
            pid_dir,
            targets=targets,
            self_pid=actual_self_pid,
            parent_pid=actual_parent_pid,
            current_uid=current_uid,
        )
        if result is None:
            continue
        (
            occupant,
            pid_issues,
            pid_cwd_permission_unreachable,
            pid_same_uid_cwd_unreachable,
        ) = result
        if occupant is not None:
            occupants.append(occupant)
        issues.extend(pid_issues)
        cwd_permission_unreachable += pid_cwd_permission_unreachable
        same_uid_cwd_unreachable.extend(pid_same_uid_cwd_unreachable)

    occupants.sort(key=lambda item: (item.pid, item.sources))
    issues.sort(key=lambda item: (item.pid is None, item.pid or -1, item.source, item.error))
    same_uid_cwd_unreachable.sort(key=lambda item: item.pid)
    if occupants:
        status = "occupied"
    elif issues:
        status = "indeterminate"
    else:
        status = "unoccupied"
    return ScanReport(
        worktree=real_target,
        status=status,
        occupants=tuple(occupants),
        issues=tuple(issues),
        scanned=len(pid_dirs),
        same_uid_cwd_unreachable=tuple(same_uid_cwd_unreachable),
        unreachable=Unreachable(
            cwd_permission=cwd_permission_unreachable,
        ),
    )


def _report_payload(report: ScanReport) -> dict[str, object]:
    payload: dict[str, object] = {
        "issues": [asdict(issue) for issue in report.issues],
        "occupants": [asdict(occupant) for occupant in report.occupants],
        "scanned": report.scanned,
        "status": report.status,
        "unreachable": asdict(report.unreachable),
        "worktree": str(report.worktree),
    }
    if report.same_uid_cwd_unreachable:
        payload["same_uid_cwd_unreachable"] = [
            asdict(process) for process in report.same_uid_cwd_unreachable
        ]
    return payload


def main(
    argv: Sequence[str] | None = None,
    *,
    proc_root: Path = Path("/proc"),
    self_pid: int | None = None,
    parent_pid: int | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "worktree への cwd / argv 参照による占有を検出する。rc0 は inspect できた"
            "範囲で占有を検出しなかったことだけを表す。cmdline は列挙した全 PID を走査"
            "するが、cwd は他ユーザーおよび non-dumpable process では観測できない。"
            "同じ uid または uid 判定不能の観測不能 process は pid と comm を残る"
            "盲点として列挙する。"
            "列挙中に worker でありうる process が一つでもあれば削除してはならない。"
            "走査後に始まる process、別 PID namespace、FD 参照も観測できないため、"
            "rc0 は削除の必要条件であって十分条件ではない。恒久解は lease であり、"
            "本 wave の scope 外である。"
        )
    )
    parser.add_argument("worktree", metavar="WORKTREE")
    args = parser.parse_args(argv)
    report = scan_worktree_occupancy(
        Path(args.worktree),
        proc_root=proc_root,
        self_pid=self_pid,
        parent_pid=parent_pid,
    )
    print(
        json.dumps(
            _report_payload(report),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return {
        "unoccupied": UNOCCUPIED_RC,
        "occupied": OCCUPIED_RC,
        "indeterminate": INDETERMINATE_RC,
    }[report.status]


if __name__ == "__main__":
    sys.exit(main())
