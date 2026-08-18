# -*- coding: utf-8 -*-
"""repo sibling に置く task-run generation manager。

この module は automatic recorder の所有者であり、generation 間の直列化と
series 全体の fail-closed 読み手を提供する。task.json/events.jsonl の schema は
ledger の task-run/v1 契約から増やさない。
"""
from __future__ import annotations

import errno
import fcntl
import os
import re
import stat
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Iterator

from . import ledger
from .ledger import (
    FINAL_MARKER_NAME,
    PilotClosedError,
    RootReport,
    _BANNED_OUTPUT_NAMESPACES,
)
from .schema import DamagedRunError, LedgerError, RUN_ID_RE, parse_timestamp


SERIES_LOCK_NAME = ".generation.lock"
TRANSPORT_DIR_NAME = "transport"
_SIDECAR_BASENAME = "pytest-stats.json"
_LEASE_OWNER_NAME = ".lease-owner"
GENERATION_PREFIX = "generation-"
_GENERATION_RE = re.compile(r"^generation-(?P<number>[0-9]{6})$")
_STAGING_RE = re.compile(r"^generation-(?P<number>[0-9]{6})\.staging$")
_QUARANTINE_RE = re.compile(r"^generation-[0-9]{6}\.staging\.damaged-[0-9]+$")
_SERIES_BASE_SUFFIX = "-task-runs"
_LEASE_MAX_AGE_S = 24 * 60 * 60
# One automatic start holds this lock across series validation, durable task
# publication, and sidecar creation.  That whole critical section is short in
# normal operation but is repeated serially by concurrent callers, so the
# series-specific bounded wait must cover the complete queue under load.
_LOCK_TIMEOUT_S = 30.0


class GenerationError(LedgerError):
    """generation/series の安全な操作を完遂できない。"""


class SeriesLockTimeout(GenerationError):
    """series lock の有界待ちが期限切れになった。"""


class SeriesInvalidError(GenerationError):
    """series lock/layout が fail-closed 検査に適合しない。"""


@dataclass(frozen=True)
class AutomaticRun:
    generation_root: Path
    task_run_id: str
    generation_name: str
    sidecar_path: Path | None


@dataclass(frozen=True)
class SeriesReport:
    """series 全体の読み取り結果。個別 root report の健全性を代弁しない。"""

    base: Path
    generations: tuple[Path, ...]
    root_reports: tuple[RootReport, ...]
    invalid_codes: tuple[str, ...] = ()
    quarantined: tuple[Path, ...] = ()
    diagnostics: tuple[str, ...] = ()

    @property
    def generation_roots(self) -> tuple[Path, ...]:
        return self.generations

    @property
    def published(self) -> tuple[Path, ...]:
        values: list[Path] = []
        for report in self.root_reports:
            values.extend(report.published)
        return tuple(values)

    @property
    def damaged(self) -> tuple[Path, ...]:
        values: list[Path] = []
        for report in self.root_reports:
            values.extend(item.path for item in report.damaged)
        return tuple(values)

    @property
    def incomplete(self) -> tuple[Path, ...]:
        values: list[Path] = []
        for report in self.root_reports:
            values.extend(report.incomplete)
        return tuple(values)

    @property
    def unknown(self) -> tuple[Path, ...]:
        values: list[Path] = []
        for report in self.root_reports:
            values.extend(report.unknown)
        return tuple(values)

    @property
    def is_valid(self) -> bool | None:
        if not self.generations:
            # Empty is not a healthy series.  It is an explicit, undecidable
            # state so callers cannot accidentally present it as validated.
            return None
        return not self.invalid_codes and all(report.is_valid for report in self.root_reports)

    @property
    def is_empty(self) -> bool:
        """generation が一つもなく、series 全体を判定できない状態。"""

        return not self.generations

    @property
    def published_run_count(self) -> int:
        return sum(report.published_run_count for report in self.root_reports)

    @property
    def max_task_runs(self) -> int:
        return max((report.max_task_runs for report in self.root_reports), default=10)

    def as_dict(self) -> dict[str, object]:
        """CLI 用の揮発しない projection。repo path は出力しない。"""

        return {
            "generations": [path.name for path in self.generations],
            "published": [path.name for path in self.published],
            "incomplete": [path.name for path in self.incomplete],
            "damaged": [path.name for path in self.damaged],
            "unknown": [path.name for path in self.unknown],
            "quarantined": [path.name for path in self.quarantined],
            "invalid_codes": list(self.invalid_codes),
            "diagnostics": list(self.diagnostics),
            "is_empty": self.is_empty,
            "published_run_count": self.published_run_count,
            "max_task_runs": self.max_task_runs,
            "cap_exceeded": self.published_run_count > self.max_task_runs,
            "cap_excess": max(0, self.published_run_count - self.max_task_runs),
            "is_valid": self.is_valid,
        }


@dataclass
class _SeriesLock:
    base: Path
    base_fd: int
    lock_fd: int
    base_identities: tuple[tuple[int, int], ...]


def _under(path: Path, parent: Path, *, strict: bool = False) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return strict or path != parent


def _safe_component(name: str, *, label: str) -> str:
    if (
        not isinstance(name, str)
        or name in {"", ".", ".."}
        or "\x00" in name
        or "/" in name
        or "\\" in name
    ):
        raise GenerationError(f"{label}: unsafe path component")
    return name


def _nofollow() -> int:
    value = getattr(os, "O_NOFOLLOW", None)
    if value is None:
        raise GenerationError("O_NOFOLLOW が利用できないため fail-closed")
    return value


def _open_dir_at(parent_fd: int, name: str, *, label: str) -> int:
    name = _safe_component(name, label=label)
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise GenerationError(f"{label} を安全に開けない") from exc
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise GenerationError(f"{label}: directory でない")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _check_banned_components(path: Path) -> None:
    parts = path.parts
    for index, part in enumerate(parts[:-1]):
        if part == "output" and parts[index + 1] in _BANNED_OUTPUT_NAMESPACES:
            raise GenerationError("証拠 namespace 配下に series base を置けない")


def _open_directory_chain(
    path: Path,
    *,
    create_final: bool,
    _return_identities: bool = False,
) -> int | tuple[int, tuple[tuple[int, int], ...]]:
    """absolute path を root fd から一 component ずつ openat/mkdirat する。"""

    path = Path(path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = Path(os.path.normpath(os.fspath(path)))
    if path == Path(path.anchor):
        raise GenerationError("series base が filesystem root そのもの")
    _check_banned_components(path)
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        current_fd = os.open(path.anchor or os.sep, flags)
    except OSError as exc:
        raise GenerationError("filesystem root を安全に開けない") from exc
    try:
        root_info = os.fstat(current_fd)
    except OSError as exc:
        os.close(current_fd)
        raise GenerationError("filesystem root の identity を検査できない") from exc
    if not stat.S_ISDIR(root_info.st_mode):
        os.close(current_fd)
        raise GenerationError("filesystem root が directory でない")
    identities: list[tuple[int, int]] = [(root_info.st_dev, root_info.st_ino)]
    parts = path.parts[1:]
    try:
        for index, component in enumerate(parts):
            final = index == len(parts) - 1
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except FileNotFoundError as exc:
                if not (create_final and final):
                    raise GenerationError("series base の component が存在しない") from exc
                try:
                    os.mkdir(component, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                except OSError as mkdir_exc:
                    raise GenerationError("series base を mkdirat できない") from mkdir_exc
                try:
                    os.fsync(current_fd)
                except OSError as fsync_exc:
                    raise GenerationError("series base parent を fsync できない") from fsync_exc
                try:
                    next_fd = os.open(component, flags, dir_fd=current_fd)
                except OSError as open_exc:
                    raise GenerationError("mkdirat 後の series base を開けない") from open_exc
            except OSError as exc:
                raise GenerationError("series base component を O_NOFOLLOW で開けない") from exc
            try:
                next_info = os.fstat(next_fd)
                if not stat.S_ISDIR(next_info.st_mode):
                    raise GenerationError("series base component が directory でない")
                identities.append((next_info.st_dev, next_info.st_ino))
            except BaseException:
                os.close(next_fd)
                raise
            os.close(current_fd)
            current_fd = next_fd
        if _return_identities:
            return current_fd, tuple(identities)
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def _validate_repo_base_binding(repo_root: Path, base: Path) -> None:
    repo = Path(repo_root).resolve(strict=True)
    if not repo.is_dir():
        raise GenerationError("repo_root は directory でなければならない")
    candidate = Path(base)
    try:
        resolved_base = candidate.resolve(strict=False)
    except OSError as exc:
        raise GenerationError("series base の realpath を解決できない") from exc
    # derived sibling は repo と同一でも、repo の下でも、repo を含む親でもない。
    if resolved_base == repo or _under(resolved_base, repo) or _under(repo, resolved_base):
        raise GenerationError("series base が repo namespace と重なる")


def series_base_for_repo(repo_root: Path) -> Path:
    """git-common-dir の realpath の親から repo sibling base を導出する。"""

    repo = Path(repo_root).resolve(strict=True)
    if not repo.is_dir():
        raise GenerationError("repo_root は directory でなければならない")
    repo_binding = ledger._open_directory_binding(repo, label="repo root")
    common_binding = None
    try:
        ledger._verify_directory_binding(repo_binding, label="repo root")
        toplevel = Path(
            ledger._git_output(
                repo,
                "rev-parse",
                "--show-toplevel",
                _binding=repo_binding,
            ),
        ).resolve(strict=True)
        if toplevel != repo:
            raise GenerationError("repo_root が git toplevel と一致しない")
        common_raw = ledger._git_output(
            repo,
            "rev-parse",
            "--git-common-dir",
            _binding=repo_binding,
        )
        common = Path(common_raw)
        if not common.is_absolute():
            common = repo / common
        common = common.resolve(strict=True)
        if not common.is_dir():
            raise GenerationError("git-common-dir が directory でない")
        common_binding = ledger._open_directory_binding(common, label="git-common-dir")
        ledger._verify_directory_binding(common_binding, label="git-common-dir")
        common_repo = common.parent.resolve(strict=True)
        if not common_repo.name or common_repo.name in {".", ".."}:
            raise GenerationError("common repo name が空")
        base = common_repo.parent / f"{common_repo.name}{_SERIES_BASE_SUFFIX}"
        _validate_repo_base_binding(repo, base)
        _check_banned_components(base)
        ledger._verify_directory_binding(repo_binding, label="repo root")
        ledger._verify_directory_binding(common_binding, label="git-common-dir")
        return base
    finally:
        ledger._close_directory_binding(common_binding)
        ledger._close_directory_binding(repo_binding)


# Names used by tests and downstream code should have one canonical derivation.
default_series_base = series_base_for_repo


def _open_series_base(base: Path, *, create: bool) -> int:
    return _open_directory_chain(base, create_final=create)


def _open_lock(base_fd: int, *, create: bool) -> int:
    flags = os.O_RDWR | _nofollow()
    if create:
        flags |= os.O_CREAT
    try:
        fd = os.open(SERIES_LOCK_NAME, flags, 0o600, dir_fd=base_fd)
    except OSError as exc:
        raise SeriesInvalidError("series lock file を安全に開けない") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
            raise SeriesInvalidError("series lock は owner-only regular file が必要")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _acquire_series_lock(lock_fd: int, *, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EACCES):
                raise GenerationError("series lock 取得に失敗") from exc
            if time.monotonic() >= deadline:
                raise SeriesLockTimeout("series lock timeout") from exc
            time.sleep(0.01)


@contextmanager
def _hold_series_lock(
    base: Path,
    *,
    create: bool,
    timeout_s: float | None = None,
) -> Iterator[_SeriesLock]:
    base = Path(base)
    effective_timeout = _LOCK_TIMEOUT_S if timeout_s is None else timeout_s
    opened = _open_directory_chain(base, create_final=create, _return_identities=True)
    base_fd, base_identities = opened
    lock_fd: int | None = None
    acquired = False
    try:
        base_binding = ledger._DirectoryBinding(
            path=Path(base), fd=base_fd, identities=base_identities,
        )
        ledger._verify_directory_binding(base_binding, label="series base")
        lock_fd = _open_lock(base_fd, create=create)
        _acquire_series_lock(lock_fd, timeout_s=effective_timeout)
        acquired = True
        ledger._verify_directory_binding(base_binding, label="series base")
        yield _SeriesLock(
            base=base,
            base_fd=base_fd,
            lock_fd=lock_fd,
            base_identities=base_identities,
        )
    finally:
        if lock_fd is not None:
            try:
                if acquired:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        os.close(base_fd)


def _hold_repo_series_lock(
    repo_root: Path,
    *,
    create: bool,
    timeout_s: float | None = None,
) -> Iterator[_SeriesLock]:
    return _hold_series_lock(series_base_for_repo(repo_root), create=create, timeout_s=timeout_s)


def _verify_series_lock_base(lock: _SeriesLock) -> None:
    binding = ledger._DirectoryBinding(
        path=lock.base,
        fd=lock.base_fd,
        identities=lock.base_identities,
    )
    ledger._verify_directory_binding(binding, label="series base")


def _entry_exists(base_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=base_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise GenerationError("series entry を検査できない") from exc
    return True


def _fsync_dir(fd: int, *, label: str) -> None:
    try:
        os.fsync(fd)
    except OSError as exc:
        raise GenerationError(f"{label} を fsync できない") from exc


def _quarantine_staging(base_fd: int, name: str) -> Path:
    stamp = time.time_ns()
    for attempt in range(32):
        target = f"{name}.damaged-{stamp + attempt}"
        try:
            os.rename(name, target, src_dir_fd=base_fd, dst_dir_fd=base_fd)
        except FileExistsError:
            continue
        except OSError as exc:
            raise GenerationError("damaged staging を quarantine できない") from exc
        _fsync_dir(base_fd, label="series base")
        return Path(target)
    raise GenerationError("damaged staging quarantine 名を予約できない")


def _recover_staging(lock: _SeriesLock, name: str) -> tuple[str, Path | None]:
    match = _STAGING_RE.fullmatch(name)
    if match is None:
        return "not-staging", None
    number = int(match.group("number"))
    final_name = f"{GENERATION_PREFIX}{number:06d}"
    stage_path = lock.base / name
    stage_fd: int | None = None
    valid = False
    try:
        stage_fd = _open_dir_at(lock.base_fd, name, label=name)
        with ledger._locked_root_snapshot(stage_path, root_fd=stage_fd) as (report, _runs):
            valid = not report.damaged and not report.unknown and not report.incomplete
    except Exception:
        valid = False
    finally:
        if stage_fd is not None:
            os.close(stage_fd)
    if valid and not _entry_exists(lock.base_fd, final_name):
        try:
            os.rename(name, final_name, src_dir_fd=lock.base_fd, dst_dir_fd=lock.base_fd)
            _fsync_dir(lock.base_fd, label="series base")
        except OSError as exc:
            raise GenerationError("valid staging を generation へ publish できない") from exc
        return "recovered", lock.base / final_name
    quarantine = _quarantine_staging(lock.base_fd, name)
    return "damaged", quarantine


def _create_generation_locked(lock: _SeriesLock, *, number: int) -> Path:
    if number < 1 or number > 999999:
        raise GenerationError("generation number が範囲外")
    final_name = f"{GENERATION_PREFIX}{number:06d}"
    staging_name = f"{final_name}.staging"
    if _entry_exists(lock.base_fd, final_name) or _entry_exists(lock.base_fd, staging_name):
        raise GenerationError("generation reservation が既に存在する")
    try:
        os.mkdir(staging_name, 0o700, dir_fd=lock.base_fd)
    except OSError as exc:
        raise GenerationError("generation staging を排他予約できない") from exc
    stage_fd: int | None = None
    try:
        # RENAME_NOREPLACE は使わず、mkdir reservation と series lock の組で
        # destination の不存在を保持してから rename する。
        # stage_fd を先に open し、pilot の create もこの fd に anchored
        # する。base directory の rename/swap が起きても別 namespace へ
        # 書き込まない。
        stage_fd = _open_dir_at(lock.base_fd, staging_name, label=staging_name)
        try:
            ledger.init_pilot(
                lock.base / staging_name,
                bounded_wait=True,
                lock_timeout_s=_LOCK_TIMEOUT_S,
                _root_fd=stage_fd,
            )
            ledger._pilot_from_root_fd(stage_fd)
            _fsync_dir(stage_fd, label="staging generation")
        finally:
            os.close(stage_fd)
            stage_fd = None
        _fsync_dir(lock.base_fd, label="series base")
        if _entry_exists(lock.base_fd, final_name):
            raise GenerationError("generation destination が publish 前に存在した")
        try:
            os.rename(staging_name, final_name, src_dir_fd=lock.base_fd, dst_dir_fd=lock.base_fd)
        except OSError as exc:
            raise GenerationError("generation staging の rename に失敗") from exc
        _fsync_dir(lock.base_fd, label="series base")
        return lock.base / final_name
    except BaseException:
        # staging は削除しない。次回起動時に pilot bytes を検証して recovery/quarantine する。
        if stage_fd is not None:
            os.close(stage_fd)
        raise


def _known_task_run_ids(lock: _SeriesLock) -> set[str]:
    known: set[str] = set()
    try:
        names = os.listdir(lock.base_fd)
    except OSError:
        return known
    for name in names:
        if _GENERATION_RE.fullmatch(name) is None:
            continue
        try:
            generation_fd = _open_dir_at(lock.base_fd, name, label=name)
        except GenerationError:
            continue
        try:
            for child in os.listdir(generation_fd):
                if RUN_ID_RE.fullmatch(child) is not None:
                    known.add(child)
        except OSError:
            continue
        finally:
            os.close(generation_fd)
    return known


def _lease_owner_alive(lease_fd: int) -> bool | None:
    try:
        raw = ledger._read_file_at(lease_fd, _LEASE_OWNER_NAME, limit=64, label=_LEASE_OWNER_NAME)
        owner = raw.decode("ascii").strip()
        if owner == "closed":
            return False
        pid = int(owner)
        if pid <= 0:
            return False
    except (LedgerError, UnicodeError, ValueError):
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def _cleanup_orphan_leases(lock: _SeriesLock) -> tuple[str, ...]:
    """Remove abandoned transport leases without making validation fail-open."""

    try:
        transport_fd = _open_dir_at(lock.base_fd, TRANSPORT_DIR_NAME, label=TRANSPORT_DIR_NAME)
    except GenerationError:
        if _entry_exists(lock.base_fd, TRANSPORT_DIR_NAME):
            return ("recording-unavailable:lease-cleanup",)
        return ()
    diagnostics: list[str] = []
    changed = False
    known = _known_task_run_ids(lock)
    try:
        try:
            names = sorted(os.listdir(transport_fd))
        except OSError:
            return ("recording-unavailable:lease-cleanup",)
        for name in names:
            try:
                info = os.stat(name, dir_fd=transport_fd, follow_symlinks=False)
            except OSError:
                diagnostics.append("recording-unavailable:lease-cleanup")
                continue
            if not stat.S_ISDIR(info.st_mode):
                diagnostics.append("recording-unavailable:lease-cleanup")
                continue
            old = max(0.0, time.time() - info.st_mtime) > _LEASE_MAX_AGE_S
            lease_fd: int | None = None
            try:
                lease_fd = _open_dir_at(transport_fd, name, label="sidecar lease directory")
                lease_identity = os.fstat(lease_fd)
                children = os.listdir(lease_fd)
                owner_alive = _lease_owner_alive(lease_fd)
                if name in known and not old and owner_alive is not False:
                    continue
                for child in children:
                    if child in {_SIDECAR_BASENAME, _LEASE_OWNER_NAME}:
                        os.unlink(child, dir_fd=lease_fd)
                    else:
                        raise GenerationError("孤立 lease に未知の file がある")
                _fsync_dir(lease_fd, label="sidecar lease directory")
                current = os.stat(name, dir_fd=transport_fd, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (lease_identity.st_dev, lease_identity.st_ino):
                    raise GenerationError("sidecar lease directory の identity が変化した")
                os.rmdir(name, dir_fd=transport_fd)
                changed = True
            except Exception:
                diagnostics.append("recording-unavailable:lease-cleanup")
            finally:
                if lease_fd is not None:
                    os.close(lease_fd)
        if changed:
            try:
                _fsync_dir(transport_fd, label="transport")
            except Exception:
                diagnostics.append("recording-unavailable:lease-cleanup")
    finally:
        os.close(transport_fd)
    return tuple(dict.fromkeys(diagnostics))


def _validate_generation_entries(
    lock: _SeriesLock,
    *,
    recover_staging: bool = False,
) -> SeriesReport:
    _verify_series_lock_base(lock)
    diagnostics = _cleanup_orphan_leases(lock)
    try:
        names = sorted(os.listdir(lock.base_fd))
    except OSError as exc:
        raise GenerationError("series entry を列挙できない") from exc

    invalid: list[str] = []
    quarantined: list[Path] = []
    staging = [name for name in names if _STAGING_RE.fullmatch(name)]
    if staging and not recover_staging:
        invalid.append("staging-pending")
    elif recover_staging:
        for name in staging:
            status, path = _recover_staging(lock, name)
            if status == "damaged":
                invalid.append("staging-damaged")
                if path is not None:
                    quarantined.append(path)

    try:
        names = sorted(os.listdir(lock.base_fd))
    except OSError as exc:
        raise GenerationError("staging recovery 後の series entry を列挙できない") from exc

    generation_numbers: list[int] = []
    generation_names: dict[int, str] = {}
    unknown_names: list[str] = []
    for name in names:
        if name == SERIES_LOCK_NAME:
            continue
        if name == TRANSPORT_DIR_NAME:
            try:
                fd = _open_dir_at(lock.base_fd, name, label=name)
            except GenerationError:
                invalid.append("transport-invalid")
            else:
                os.close(fd)
            continue
        if _QUARANTINE_RE.fullmatch(name):
            invalid.append("staging-damaged")
            quarantined.append(lock.base / name)
            continue
        if _STAGING_RE.fullmatch(name):
            invalid.append("staging-pending")
            continue
        generation_match = _GENERATION_RE.fullmatch(name)
        if generation_match is not None:
            number = int(generation_match.group("number"))
            generation_numbers.append(number)
            generation_names[number] = name
            continue
        unknown_names.append(name)
    if unknown_names:
        invalid.append("unknown-series-entry")

    generation_numbers.sort()
    if generation_numbers and generation_numbers != list(range(1, generation_numbers[-1] + 1)):
        invalid.append("generation-gap")

    generations: list[Path] = []
    root_reports: list[RootReport] = []
    for number in generation_numbers:
        name = generation_names[number]
        path = lock.base / name
        try:
            fd = _open_dir_at(lock.base_fd, name, label=name)
        except GenerationError:
            invalid.append("generation-invalid")
            continue
        generations.append(path)
        try:
            with ledger._locked_root_snapshot(path, root_fd=fd) as (report, _runs):
                pass
        except Exception:
            invalid.append("generation-invalid")
            continue
        finally:
            os.close(fd)
        root_reports.append(report)
        if report.damaged or report.unknown or report.incomplete or not report.is_valid:
            invalid.append("generation-invalid")

    return SeriesReport(
        base=lock.base,
        generations=tuple(generations),
        root_reports=tuple(root_reports),
        invalid_codes=tuple(dict.fromkeys(invalid)),
        quarantined=tuple(dict.fromkeys(quarantined)),
        diagnostics=diagnostics,
    )


def _single_root_report(root: Path) -> SeriesReport:
    try:
        report = ledger.validate_root(root)
    except Exception:
        return SeriesReport(
            base=Path(root).resolve(strict=False),
            generations=(Path(root).resolve(strict=False),),
            root_reports=(),
            invalid_codes=("generation-invalid",),
        )
    invalid = () if report.is_valid and not report.incomplete and not report.damaged and not report.unknown else ("generation-invalid",)
    resolved = Path(root).resolve(strict=False)
    return SeriesReport(
        base=resolved.parent,
        generations=(resolved,),
        root_reports=(report,),
        invalid_codes=invalid,
    )


def _looks_like_generation_root(path: Path) -> bool:
    try:
        resolved = Path(path).resolve(strict=False)
        return resolved.is_dir() and (resolved / "pilot.json").is_file()
    except OSError:
        return False


def validate_series(
    repo_root: Path,
    *,
    _held_lock: _SeriesLock | None = None,
    _recover_staging: bool = False,
) -> SeriesReport:
    """series 全体を読む唯一の fail-closed reader。

    automatic と CLI の series 健全性保証はこの入口だけが提供する。
    個別 generation の root report は、その generation の状態を示すだけで
    series 全体の健全性を代弁しない。generation が 0 件なら ``is_empty`` が
    true で、``is_valid`` は判定不能 (``None``) になる。
    """

    candidate = Path(repo_root)
    if _held_lock is not None:
        return _validate_generation_entries(_held_lock, recover_staging=_recover_staging)
    managed_base = _managed_series_base(candidate)
    if managed_base is not None:
        base = managed_base
        if not base.exists():
            return SeriesReport(base=base, generations=(), root_reports=(), invalid_codes=("series-missing",))
        try:
            with _hold_series_lock(base, create=False) as lock:
                return _validate_generation_entries(lock, recover_staging=_recover_staging)
        except GenerationError:
            return SeriesReport(base=base, generations=(), root_reports=(), invalid_codes=("series-lock-invalid",))
    if _looks_like_generation_root(candidate):
        return _single_root_report(candidate)

    if candidate.name.endswith(_SERIES_BASE_SUFFIX):
        base = candidate.resolve(strict=False)
    else:
        base = series_base_for_repo(candidate)
    if not base.exists():
        return SeriesReport(base=base, generations=(), root_reports=(), invalid_codes=("series-missing",))
    try:
        with _hold_series_lock(base, create=False) as lock:
            return _validate_generation_entries(lock, recover_staging=_recover_staging)
    except GenerationError:
        return SeriesReport(base=base, generations=(), root_reports=(), invalid_codes=("series-lock-invalid",))


def _latest_generation(report: SeriesReport) -> Path | None:
    return report.generations[-1] if report.generations else None


def _root_diagnostics_are_nonblocking(report: SeriesReport) -> bool:
    """damaged/unknown run の診断だけなら automatic write を継続する。"""

    if report.invalid_codes != ("generation-invalid",) or not report.root_reports:
        return False
    saw_invalid_root = False
    for root_report in report.root_reports:
        if root_report.is_valid:
            continue
        saw_invalid_root = True
        if root_report.incomplete or root_report.cap_exceeded:
            return False
        if not root_report.damaged and not root_report.unknown:
            return False
    return saw_invalid_root


def _closure_reason(
    generation_root: Path,
    root_report: RootReport,
    *,
    root_fd: int | None = None,
) -> str | None:
    own_root_fd = root_fd is None
    active_root_fd = ledger._open_directory(generation_root) if own_root_fd else root_fd
    try:
        try:
            os.stat(FINAL_MARKER_NAME, dir_fd=active_root_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            ledger._validate_final_marker_fd(active_root_fd)
            return "final"
        pilot = ledger._pilot_from_root_fd(active_root_fd)
    finally:
        if own_root_fd:
            os.close(active_root_fd)
    if root_report.published_run_count >= int(pilot["max_task_runs"]):
        return "max-task-runs"
    now = ledger._utc_now()
    started = parse_timestamp(pilot["pilot_started_at"], label="pilot_started_at")
    if now >= started + timedelta(days=int(pilot["max_days"])):
        return "max-days"
    return None


def _open_transport(lock: _SeriesLock) -> int:
    try:
        fd = _open_dir_at(lock.base_fd, TRANSPORT_DIR_NAME, label=TRANSPORT_DIR_NAME)
    except GenerationError as exc:
        if not _entry_exists(lock.base_fd, TRANSPORT_DIR_NAME):
            try:
                os.mkdir(TRANSPORT_DIR_NAME, 0o700, dir_fd=lock.base_fd)
            except OSError as mkdir_exc:
                raise GenerationError("transport directory を作成できない") from mkdir_exc
            _fsync_dir(lock.base_fd, label="series base")
            fd = _open_dir_at(lock.base_fd, TRANSPORT_DIR_NAME, label=TRANSPORT_DIR_NAME)
        else:
            raise exc
    return fd


def _create_sidecar(lock: _SeriesLock, task_run_id: str) -> Path:
    transport_fd = _open_transport(lock)
    name = task_run_id
    lease_fd: int | None = None
    completed = False
    created = False
    try:
        try:
            os.mkdir(name, 0o700, dir_fd=transport_fd)
        except OSError as exc:
            raise GenerationError("sidecar lease directory を作成できない") from exc
        created = True
        lease_fd = _open_dir_at(transport_fd, name, label="sidecar lease directory")
        try:
            ledger._create_file_at(
                lease_fd,
                _LEASE_OWNER_NAME,
                f"{os.getpid()}\n".encode("ascii"),
                label=_LEASE_OWNER_NAME,
            )
            try:
                os.fchmod(lease_fd, 0o700)
            except OSError as exc:
                raise GenerationError("sidecar lease directory の mode を設定できない") from exc
            _fsync_dir(lease_fd, label="sidecar lease directory")
        finally:
            os.close(lease_fd)
            lease_fd = None
        _fsync_dir(transport_fd, label="transport")
        completed = True
    except BaseException:
        # A signal or a failed fsync before the lease is handed to the caller
        # must not strand the newly-created directory.
        try:
            if lease_fd is not None:
                os.close(lease_fd)
                lease_fd = None
            if created:
                try:
                    os.unlink(
                        f"{name}/{_LEASE_OWNER_NAME}",
                        dir_fd=transport_fd,
                    )
                except FileNotFoundError:
                    pass
                os.rmdir(name, dir_fd=transport_fd)
                _fsync_dir(transport_fd, label="transport")
        except Exception:
            pass
        raise
    finally:
        if lease_fd is not None:
            os.close(lease_fd)
        os.close(transport_fd)
    if not completed:
        raise GenerationError("sidecar lease を完了できない")
    return lock.base / TRANSPORT_DIR_NAME / name / _SIDECAR_BASENAME


def _mark_sidecar_closed(path: Path) -> None:
    path = Path(path)
    if (
        not path.is_absolute()
        or path.name != _SIDECAR_BASENAME
        or path.parent.name in {"", ".", ".."}
        or path.parent.parent.name != TRANSPORT_DIR_NAME
        or any(part in {".", ".."} for part in path.parts)
    ):
        raise GenerationError("sidecar path binding が不正")
    transport_binding = ledger._open_directory_binding(path.parent.parent, label="transport")
    lease_fd: int | None = None
    owner_fd: int | None = None
    try:
        ledger._verify_directory_binding(transport_binding, label="transport")
        lease_fd = _open_dir_at(
            transport_binding.fd,
            path.parent.name,
            label="sidecar lease directory",
        )
        owner_fd = ledger._open_regular_at(
            lease_fd,
            _LEASE_OWNER_NAME,
            os.O_WRONLY | os.O_TRUNC,
            label=_LEASE_OWNER_NAME,
        )
        ledger._write_all(owner_fd, b"closed\n")
        os.fsync(owner_fd)
        os.fsync(lease_fd)
    finally:
        if owner_fd is not None:
            os.close(owner_fd)
        if lease_fd is not None:
            os.close(lease_fd)
        ledger._close_directory_binding(transport_binding)


def _remove_sidecar(path: Path) -> None:
    path = Path(path)
    if (
        not path.is_absolute()
        or path.name != _SIDECAR_BASENAME
        or path.parent.name in {"", ".", ".."}
        or path.parent.parent.name != TRANSPORT_DIR_NAME
        or any(part in {".", ".."} for part in path.parts)
    ):
        raise GenerationError("sidecar path binding が不正")
    transport_binding = ledger._open_directory_binding(path.parent.parent, label="transport")
    transport_fd = transport_binding.fd
    lease_fd: int | None = None
    lease_identity: tuple[int, int] | None = None
    try:
        ledger._verify_directory_binding(transport_binding, label="transport")
        lease_fd = _open_dir_at(
            transport_fd,
            path.parent.name,
            label="sidecar lease directory",
        )
        lease_info = os.fstat(lease_fd)
        lease_identity = lease_info.st_dev, lease_info.st_ino
        try:
            for child in (_SIDECAR_BASENAME, _LEASE_OWNER_NAME):
                try:
                    os.unlink(child, dir_fd=lease_fd)
                except FileNotFoundError:
                    pass
            _fsync_dir(lease_fd, label="sidecar lease directory")
        except OSError as exc:
            raise GenerationError("sidecar file を cleanup できない") from exc
        finally:
            os.close(lease_fd)
            lease_fd = None
        current = os.stat(path.parent.name, dir_fd=transport_fd, follow_symlinks=False)
        if lease_identity != (current.st_dev, current.st_ino):
            raise GenerationError("sidecar lease directory の identity が変化した")
        try:
            os.rmdir(path.parent.name, dir_fd=transport_fd)
        except OSError as exc:
            raise GenerationError("sidecar lease directory を cleanup できない") from exc
        _fsync_dir(transport_fd, label="transport")
    finally:
        if lease_fd is not None:
            os.close(lease_fd)
        ledger._close_directory_binding(transport_binding)


def _diagnostic_for(exc: Exception) -> str:
    if isinstance(exc, SeriesLockTimeout):
        return "recording-unavailable:series-lock-timeout"
    if isinstance(exc, SeriesInvalidError):
        return "recording-unavailable:series-invalid"
    if isinstance(exc, (GenerationError, DamagedRunError)):
        if "lock timeout" in str(exc):
            return "recording-unavailable:series-lock-timeout"
        return "recording-unavailable:filesystem"
    if isinstance(exc, LedgerError):
        if "root lock timeout" in str(exc):
            return "recording-unavailable:series-lock-timeout"
        return "recording-unavailable:filesystem"
    return "recording-unavailable:filesystem"


def _cap_reached_by_invalid_runs(report: SeriesReport) -> bool:
    """Allow incomplete runs to reach their cap diagnostic, not a bypass."""

    if report.published_run_count < report.max_task_runs:
        return False
    if report.invalid_codes != ("generation-invalid",):
        return False
    return any(root_report.incomplete for root_report in report.root_reports)


def _ensure_generation_selfcheck(generation_root: Path, generation_fd: int) -> str | None:
    status = ledger._generation_selfcheck_status_fd(generation_fd)
    if status == "ok":
        return None
    if status == "failed":
        return "recording-unavailable:filesystem"
    diagnostic: str | None = None
    try:
        ledger.selfcheck(generation_root)
        status = "ok"
    except Exception:
        status = "failed"
        diagnostic = "recording-unavailable:filesystem"
    try:
        ledger._write_generation_selfcheck_status_fd(generation_fd, status)
    except Exception:
        diagnostic = "recording-unavailable:filesystem"
    return diagnostic


def _merge_diagnostic(*values: str | None) -> str | None:
    for value in values:
        if value is not None:
            return value
    return None


def start_automatic_test_run(repo_root: Path) -> tuple[AutomaticRun | None, str | None]:
    """automatic recorder の開始。閉鎖世代からの rollover は行わない。"""

    try:
        with _hold_repo_series_lock(repo_root, create=True) as lock:
            report = validate_series(repo_root, _held_lock=lock, _recover_staging=True)
            diagnostic = report.diagnostics[0] if report.diagnostics else None
            nonblocking = _root_diagnostics_are_nonblocking(report)
            if report.is_empty and report.invalid_codes:
                return None, "recording-unavailable:series-invalid"
            if report.is_valid is False and _cap_reached_by_invalid_runs(report):
                return None, "pilot-closed:max-task-runs"
            if report.is_valid is False and not nonblocking:
                return None, "recording-unavailable:series-invalid"
            generation_root = _latest_generation(report)
            if generation_root is None:
                generation_root = _create_generation_locked(lock, number=1)
                report = validate_series(repo_root, _held_lock=lock, _recover_staging=True)
                diagnostic = _merge_diagnostic(
                    diagnostic,
                    report.diagnostics[0] if report.diagnostics else None,
                )
                if report.is_valid is not True:
                    return None, "recording-unavailable:series-invalid"
                generation_root = _latest_generation(report)
            if generation_root is None:
                return None, "recording-unavailable:series-invalid"
            latest_report = report.root_reports[-1]
            generation_fd = _open_dir_at(lock.base_fd, generation_root.name, label=generation_root.name)
            try:
                reason = _closure_reason(generation_root, latest_report, root_fd=generation_fd)
                if report.is_valid is False and reason == "final":
                    return None, "recording-unavailable:series-invalid"
                if reason is not None:
                    return None, f"pilot-closed:{reason}"
                diagnostic = _merge_diagnostic(
                    diagnostic,
                    _ensure_generation_selfcheck(generation_root, generation_fd),
                )
                # この production path が repo_root binding 付き start_run の唯一の caller。
                task_run_id = ledger.start_run(
                    generation_root,
                    slug="pytest-run",
                    objective="automatic test observation",
                    task_class=2,
                    task_kind="other",
                    repo_root=repo_root,
                    bounded_wait=True,
                    lock_timeout_s=_LOCK_TIMEOUT_S,
                    _root_fd=generation_fd,
                )
            finally:
                os.close(generation_fd)
            sidecar: Path | None = None
            try:
                try:
                    sidecar = _create_sidecar(lock, task_run_id)
                except Exception:
                    diagnostic = _merge_diagnostic(diagnostic, "recording-unavailable:sidecar")
                return (
                    AutomaticRun(
                        generation_root=generation_root,
                        task_run_id=task_run_id,
                        generation_name=generation_root.name,
                        sidecar_path=sidecar,
                    ),
                    diagnostic,
                )
            except BaseException:
                if sidecar is not None:
                    try:
                        _mark_sidecar_closed(sidecar)
                    except Exception:
                        pass
                    try:
                        _remove_sidecar(sidecar)
                    except Exception:
                        pass
                raise
    except PilotClosedError as exc:
        return None, f"pilot-closed:{exc.reason.replace('_', '-')}"
    except Exception as exc:
        return None, _diagnostic_for(exc)


def finish_automatic_test_run(run: AutomaticRun, outcome: str) -> str | None:
    """automatic task_end と sidecar cleanup。通常例外だけ固定診断へ変換する。"""

    failure: Exception | None = None
    try:
        ledger.finish_run(run.generation_root, run.task_run_id, outcome)
    except Exception as exc:
        failure = exc
    finally:
        if run.sidecar_path is not None:
            try:
                _mark_sidecar_closed(run.sidecar_path)
            except Exception as exc:
                if failure is None:
                    failure = exc
            try:
                _remove_sidecar(run.sidecar_path)
            except Exception as exc:
                if failure is None:
                    failure = exc
    return "recording-unavailable:finish" if failure is not None else None


def _managed_series_base(root: Path) -> Path | None:
    try:
        resolved = Path(root).resolve(strict=False)
    except OSError:
        return None
    for ancestor in (resolved, *resolved.parents):
        if _GENERATION_RE.fullmatch(ancestor.name) is None:
            continue
        base = ancestor.parent
        if not base.name.endswith(_SERIES_BASE_SUFFIX):
            continue
        try:
            base_info = os.stat(base, follow_symlinks=False)
            generation_info = os.stat(ancestor, follow_symlinks=False)
            lock_info = os.stat(base / SERIES_LOCK_NAME, follow_symlinks=False)
            pilot_info = os.stat(ancestor / "pilot.json", follow_symlinks=False)
        except OSError:
            continue
        if (
            stat.S_ISDIR(base_info.st_mode)
            and stat.S_ISDIR(generation_info.st_mode)
            and stat.S_ISREG(lock_info.st_mode)
            and stat.S_ISREG(pilot_info.st_mode)
            and (resolved == ancestor or _under(resolved, ancestor))
        ):
            # The structural pattern and durable series markers, rather than
            # the current existence of the repo, are the managed boundary.
            return base
    return None


def is_managed_generation_root(root: Path) -> bool:
    """CLI の write 入口から managed generation を realpath で拒否する。"""

    return _managed_series_base(root) is not None


def open_next_generation(repo_root: Path) -> Path:
    """明示 CLI handler 専用の次世代作成 API。automatic path からは呼ばない。"""

    with _hold_repo_series_lock(repo_root, create=True) as lock:
        report = validate_series(repo_root, _held_lock=lock, _recover_staging=True)
        if report.is_valid is False or (report.is_empty and report.invalid_codes):
            raise GenerationError("series が invalid のため次世代を開けない")
        latest = _latest_generation(report)
        if latest is not None:
            generation_fd = _open_dir_at(lock.base_fd, latest.name, label=latest.name)
            try:
                reason = _closure_reason(latest, report.root_reports[-1], root_fd=generation_fd)
            finally:
                os.close(generation_fd)
            if reason is None:
                raise GenerationError("active generation はまだ closed でない")
        next_number = len(report.generations) + 1
        return _create_generation_locked(lock, number=next_number)


__all__ = [
    "AutomaticRun",
    "GenerationError",
    "SeriesLockTimeout",
    "SeriesReport",
    "default_series_base",
    "finish_automatic_test_run",
    "is_managed_generation_root",
    "open_next_generation",
    "series_base_for_repo",
    "start_automatic_test_run",
    "validate_series",
]
