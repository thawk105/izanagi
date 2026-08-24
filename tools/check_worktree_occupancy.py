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
_INVOKER_EXE_NAMES = _SHELL_EXE_NAMES | frozenset(
    {
        "timeout",
        "flock",
        "time",
        "strace",
        "nohup",
        "env",
        "stdbuf",
        "xargs",
        "setsid",
        "nice",
        "ionice",
    }
)
_CHECKER_PATH = Path(__file__).resolve()
_DELETED_CWD_SUFFIX = " (deleted)"


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
    zombie: int = 0
    cwd_deleted: int = 0


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


def _indexed_argv_path_tokens(
    argv: Sequence[str],
) -> tuple[tuple[int, str], ...]:
    candidates: list[tuple[int, str]] = []
    for index, token in enumerate(argv):
        if token:
            candidates.append((index, token))
        if "=" in token:
            rhs = token.split("=", 1)[1]
            if rhs:
                candidates.append((index, rhs))
    return tuple(candidates)


def _argv_matches_targets(
    argv: Sequence[str],
    *,
    process_cwds: tuple[Path, ...],
    targets: tuple[Path, ...],
) -> bool:
    for token in _argv_path_tokens(argv):
        path = Path(token)
        if path.is_absolute():
            bases = (Path("/"),)
        else:
            bases = process_cwds
        if not bases:
            continue
        if any(
            _path_matches_targets(path, base=base, targets=targets)
            for base in bases
        ):
            return True
    return False


def _argv_invokes_checker_before_target(
    argv: Sequence[str],
    *,
    process_cwds: tuple[Path, ...],
    targets: tuple[Path, ...],
) -> bool:
    indexed_tokens = _indexed_argv_path_tokens(argv)
    checker_indices: list[int] = []
    for index, token in enumerate(argv):
        path = Path(token)
        if not path.is_absolute():
            continue
        if any(
            candidate == _CHECKER_PATH
            for candidate in _candidate_spellings(path, base=Path("/"))
        ):
            checker_indices.append(index)
    if not checker_indices:
        return False
    first_checker = min(checker_indices)
    for index, token in indexed_tokens:
        if index <= first_checker:
            continue
        path = Path(token)
        if path.is_absolute():
            bases = (Path("/"),)
        else:
            bases = process_cwds
        if any(
            _path_matches_targets(path, base=base, targets=targets)
            for base in bases
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


def _read_process_cwd(pid_dir: Path) -> str:
    return os.readlink(pid_dir / "cwd")


def _resolve_process_cwd(raw_cwd: Path) -> Path:
    return raw_cwd.resolve(strict=True)


def _deleted_cwd_spellings(
    raw_cwd: Path,
    *,
    readlink_text: str,
) -> tuple[Path, Path] | None:
    if not readlink_text.endswith(_DELETED_CWD_SUFFIX):
        return None
    raw_text = os.fspath(raw_cwd)
    return raw_cwd, Path(raw_text.removesuffix(_DELETED_CWD_SUFFIX))


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


def _read_parent_pid(pid_dir: Path) -> int:
    for line in (pid_dir / "status").read_text(encoding="utf-8").splitlines():
        if not line.startswith("PPid:"):
            continue
        fields = line.removeprefix("PPid:").split()
        if not fields:
            break
        parent_pid = int(fields[0])
        if parent_pid < 0:
            break
        return parent_pid
    raise ValueError("status PPid field is missing or invalid")


def _read_process_comm(pid_dir: Path) -> str:
    return (pid_dir / "comm").read_text(encoding="utf-8").rstrip("\n")


def _process_is_zombie(pid_dir: Path) -> bool:
    try:
        lines = (pid_dir / "status").read_text(encoding="utf-8").splitlines()
    except (OSError, RuntimeError, UnicodeError):
        return False
    for line in lines:
        if line.startswith("State:"):
            return line.removeprefix("State:").lstrip().startswith("Z")
    return False


def _ancestor_is_invoking_checker(
    pid_dir: Path,
    argv: Sequence[str],
    *,
    process_cwds: tuple[Path, ...],
    targets: tuple[Path, ...],
) -> bool:
    try:
        exe_name = (pid_dir / "exe").resolve(strict=True).name
    except (OSError, RuntimeError):
        return False
    return (
        exe_name in _INVOKER_EXE_NAMES
        and _argv_invokes_checker_before_target(
            argv,
            process_cwds=process_cwds,
            targets=targets,
        )
    )


def _ancestor_starttimes(
    proc_root: Path,
    *,
    self_pid: int,
    parent_pid: int,
) -> dict[int, str]:
    ancestors: dict[int, str] = {}
    seen = {self_pid}
    pid = parent_pid
    while pid > 0 and pid not in seen:
        seen.add(pid)
        pid_dir = proc_root / str(pid)
        try:
            start_before = _read_starttime(pid_dir)
            next_pid = _read_parent_pid(pid_dir)
            start_after = _read_starttime(pid_dir)
        except (OSError, RuntimeError, UnicodeError, ValueError):
            break
        if start_before != start_after:
            break
        ancestors[pid] = start_before
        pid = next_pid
    return ancestors


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


def _cwd_permission_diagnostics(
    pid: int,
    pid_dir: Path,
    *,
    current_uid: int,
) -> tuple[int, tuple[SameUidCwdUnreachable, ...]]:
    try:
        process_uid = _read_process_uid(pid_dir)
    except (OSError, RuntimeError, UnicodeError, ValueError):
        process_uid = None
    if process_uid is not None and process_uid != current_uid:
        return 1, ()
    try:
        comm: str | None = _read_process_comm(pid_dir)
    except (OSError, RuntimeError, UnicodeError):
        comm = None
    return 0, (SameUidCwdUnreachable(pid=pid, comm=comm),)


def _scan_pid(
    pid: int,
    pid_dir: Path,
    *,
    targets: tuple[Path, ...],
    self_pid: int,
    ancestor_starttimes: dict[int, str],
    current_uid: int,
) -> tuple[
    Occupant | None,
    tuple[ScanIssue, ...],
    int,
    tuple[SameUidCwdUnreachable, ...],
    int,
    int,
] | None:
    try:
        start_before = _read_starttime(pid_dir)
    except FileNotFoundError as exc:
        if _pid_disappeared(pid_dir):
            return None
        return None, (_issue(pid, "stat", exc),), 0, (), 0, 0
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        return None, (_issue(pid, "stat", exc),), 0, (), 0, 0

    sources: set[str] = set()
    issues: list[ScanIssue] = []
    process_cwds: tuple[Path, ...] = ()
    cwd_permission_unreachable = 0
    same_uid_cwd_unreachable: tuple[SameUidCwdUnreachable, ...] = ()
    zombie_unreachable = 0
    cwd_deleted_unreachable = 0

    try:
        readlink_text = _read_process_cwd(pid_dir)
    except PermissionError:
        (
            cwd_permission_unreachable,
            same_uid_cwd_unreachable,
        ) = _cwd_permission_diagnostics(pid, pid_dir, current_uid=current_uid)
    except FileNotFoundError as exc:
        if _pid_disappeared(pid_dir):
            return None
        if _process_is_zombie(pid_dir):
            zombie_unreachable = 1
        else:
            issues.append(_issue(pid, "cwd", exc))
    except (OSError, RuntimeError, UnicodeError) as exc:
        issues.append(_issue(pid, "cwd", exc))
    else:
        raw_cwd = _lexical_absolute(Path(readlink_text), base=pid_dir)
        process_cwds = (raw_cwd,)
        try:
            resolved_cwd = _resolve_process_cwd(raw_cwd)
        except PermissionError:
            (
                cwd_permission_unreachable,
                same_uid_cwd_unreachable,
            ) = _cwd_permission_diagnostics(pid, pid_dir, current_uid=current_uid)
        except FileNotFoundError as exc:
            if _pid_disappeared(pid_dir):
                return None
            deleted_spellings = _deleted_cwd_spellings(
                raw_cwd,
                readlink_text=readlink_text,
            )
            if deleted_spellings is None:
                issues.append(_issue(pid, "cwd", exc))
            else:
                process_cwds = deleted_spellings
                if any(
                    _is_within(spelling, target)
                    for spelling in deleted_spellings
                    for target in targets
                ):
                    sources.add("cwd")
                else:
                    cwd_deleted_unreachable = 1
        except (OSError, RuntimeError, UnicodeError) as exc:
            issues.append(_issue(pid, "cwd", exc))
        else:
            process_cwds = (resolved_cwd,)
            if any(_is_within(resolved_cwd, target) for target in targets):
                sources.add("cwd")

    if pid != self_pid and not zombie_unreachable:
        try:
            argv = _read_cmdline(pid_dir)
            ignore_cmdline = (
                ancestor_starttimes.get(pid) == start_before
                and _ancestor_is_invoking_checker(
                    pid_dir,
                    argv,
                    process_cwds=process_cwds,
                    targets=targets,
                )
            )
            if not ignore_cmdline and _argv_matches_targets(
                argv,
                process_cwds=process_cwds,
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
            zombie_unreachable,
            cwd_deleted_unreachable,
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        return (
            None,
            tuple(issues + [_issue(pid, "stat", exc)]),
            cwd_permission_unreachable,
            same_uid_cwd_unreachable,
            zombie_unreachable,
            cwd_deleted_unreachable,
        )

    if start_after != start_before:
        return (
            None,
            (ScanIssue(error="pid-reused", pid=pid, source="stat"),),
            cwd_permission_unreachable,
            same_uid_cwd_unreachable,
            zombie_unreachable,
            cwd_deleted_unreachable,
        )

    occupant = None
    if sources:
        occupant = Occupant(pid=pid, sources=tuple(sorted(sources)))
    return (
        occupant,
        tuple(issues),
        cwd_permission_unreachable,
        same_uid_cwd_unreachable,
        zombie_unreachable,
        cwd_deleted_unreachable,
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
            status="invalid-target",
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
    ancestor_starttimes = _ancestor_starttimes(
        proc_root,
        self_pid=actual_self_pid,
        parent_pid=actual_parent_pid,
    )
    current_uid = os.getuid()
    occupants: list[Occupant] = []
    issues: list[ScanIssue] = []
    cwd_permission_unreachable = 0
    zombie_unreachable = 0
    cwd_deleted_unreachable = 0
    same_uid_cwd_unreachable: list[SameUidCwdUnreachable] = []
    for pid, pid_dir in pid_dirs:
        result = _scan_pid(
            pid,
            pid_dir,
            targets=targets,
            self_pid=actual_self_pid,
            ancestor_starttimes=ancestor_starttimes,
            current_uid=current_uid,
        )
        if result is None:
            continue
        (
            occupant,
            pid_issues,
            pid_cwd_permission_unreachable,
            pid_same_uid_cwd_unreachable,
            pid_zombie_unreachable,
            pid_cwd_deleted_unreachable,
        ) = result
        if occupant is not None:
            occupants.append(occupant)
        issues.extend(pid_issues)
        cwd_permission_unreachable += pid_cwd_permission_unreachable
        zombie_unreachable += pid_zombie_unreachable
        cwd_deleted_unreachable += pid_cwd_deleted_unreachable
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
            zombie=zombie_unreachable,
            cwd_deleted=cwd_deleted_unreachable,
        ),
    )


def _report_payload(report: ScanReport) -> dict[str, object]:
    unreachable = {"cwd_permission": report.unreachable.cwd_permission}
    if report.unreachable.zombie:
        unreachable["zombie"] = report.unreachable.zombie
    if report.unreachable.cwd_deleted:
        unreachable["cwd_deleted"] = report.unreachable.cwd_deleted
    payload: dict[str, object] = {
        "issues": [asdict(issue) for issue in report.issues],
        "occupants": [asdict(occupant) for occupant in report.occupants],
        "scanned": report.scanned,
        "status": report.status,
        "unreachable": unreachable,
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
    if report.status == "invalid-target":
        print(
            "check_worktree_occupancy: status=invalid-target",
            file=sys.stderr,
        )
    return {
        "unoccupied": UNOCCUPIED_RC,
        "occupied": OCCUPIED_RC,
        "indeterminate": INDETERMINATE_RC,
        "invalid-target": INDETERMINATE_RC,
    }[report.status]


if __name__ == "__main__":
    sys.exit(main())
