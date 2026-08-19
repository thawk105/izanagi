#!/usr/bin/env python3
"""Migrate selected tracked output files to deterministic gzip blobs.

The file list comes from ``HEAD`` rather than from a filesystem walk.  This is
intentional: the migration is for tracked bytes, and the HEAD blob is the
identity reference used by the compression self-check.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import gzip
import os
import posixpath
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence


class MigrationError(RuntimeError):
    """A repository or staging operation could not be completed safely."""


@dataclasses.dataclass(frozen=True)
class TreeEntry:
    mode: str
    git_type: str
    object_id: str
    size: int | None
    path: str


@dataclasses.dataclass(frozen=True)
class Candidate:
    entry: TreeEntry
    source: Path
    destination: Path
    mode: int


@dataclasses.dataclass(frozen=True)
class Plan:
    candidate: Candidate
    source_bytes: bytes
    compressed: bytes


@dataclasses.dataclass(frozen=True)
class Event:
    path: str
    key: str
    detail: str = ""


@dataclasses.dataclass
class Report:
    excluded: list[Event] = dataclasses.field(default_factory=list)
    skipped: list[Event] = dataclasses.field(default_factory=list)
    errors: list[str] = dataclasses.field(default_factory=list)
    plans: list[Plan] = dataclasses.field(default_factory=list)
    staged: list[str] = dataclasses.field(default_factory=list)

    def add_exclusion(self, path: str, key: str, detail: str = "") -> None:
        self.excluded.append(Event(path, key, detail))

    def add_skip(self, path: str, key: str, detail: str = "") -> None:
        self.skipped.append(Event(path, key, detail))

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    @staticmethod
    def _reason_counts(events: Iterable[Event]) -> str:
        counts = collections.Counter(event.key for event in events)
        if not counts:
            return "none"
        return ",".join(f"{key}={counts[key]}" for key in sorted(counts))

    @staticmethod
    def _event_line(prefix: str, event: Event) -> str:
        line = f"{prefix} {event.path} reason={event.key}"
        if event.detail:
            line += f" detail={event.detail}"
        return line

    def render(self, *, apply: bool) -> None:
        for event in self.excluded:
            print(self._event_line("EXCLUDE", event))
        for event in self.skipped:
            print(self._event_line("SKIP", event))
        for message in self.errors:
            print(f"ERROR {message}")
        for plan in self.plans:
            size = (
                plan.candidate.entry.size
                if plan.candidate.entry.size is not None
                else len(plan.source_bytes)
            )
            print(
                f"CANDIDATE path={plan.candidate.entry.path} size={size} "
                f"would-compress-to={len(plan.compressed)}"
            )
        if apply:
            for path in self.staged:
                print(f"STAGED {path}")

        source_bytes = sum(
            plan.candidate.entry.size
            if plan.candidate.entry.size is not None
            else len(plan.source_bytes)
            for plan in self.plans
        )
        compressed_bytes = sum(len(plan.compressed) for plan in self.plans)
        print(
            "SUMMARY "
            f"targets={len(self.plans)} "
            f"source-bytes={source_bytes} "
            f"compressed-bytes={compressed_bytes} "
            f"excluded={len(self.excluded)} "
            f"exclusion-reasons={self._reason_counts(self.excluded)} "
            f"skipped={len(self.skipped)} "
            f"skip-reasons={self._reason_counts(self.skipped)} "
            f"errors={len(self.errors)}"
        )


def compress_bytes(data: bytes) -> bytes:
    """Compress bytes as ``gzip -9 -n`` would, with a fixed mtime."""

    return gzip.compress(data, compresslevel=9, mtime=0)


def _repo_relative(value: str) -> str:
    """Normalize a repo-relative POSIX path and reject traversal."""

    if not value:
        raise argparse.ArgumentTypeError("空の repo-relative path は指定できません")
    if os.path.isabs(value):
        raise argparse.ArgumentTypeError("repo-relative path を指定してください")
    normalized = posixpath.normpath(value)
    if normalized in {".."} or normalized.startswith("../"):
        raise argparse.ArgumentTypeError("repo root の外側を指定できません")
    if normalized == ".":
        return ""
    return normalized


def _extension(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("空の suffix は指定できません")
    return value


def _nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("整数を指定してください") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("0 以上を指定してください")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "HEAD の tracked output を deterministic gzip に移行する。"
            " dry-run は作業木と index を変更しない。"
        )
    )
    parser.add_argument(
        "--root",
        action="append",
        required=True,
        type=_repo_relative,
        metavar="PATH",
        help="repo-root からの相対 path。複数指定可",
    )
    parser.add_argument(
        "--extension",
        action="append",
        required=True,
        type=_extension,
        metavar="SUFFIX",
        help="対象 suffix。複数指定可",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        type=_repo_relative,
        metavar="PATH",
        help="repo-relative path の exact 一致で除外。複数指定可",
    )
    parser.add_argument(
        "--min-bytes",
        required=True,
        type=_nonnegative_int,
        metavar="N",
        help="HEAD blob size が N より大きいものだけを対象にする",
    )
    parser.add_argument("--repo-root", type=Path, help="対象 Git repository の root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="計画を表示するだけ")
    mode.add_argument("--apply", action="store_true", help="gzip を作成し Git staging する")
    return parser


def _run_git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    """Run Git with an argv list; shell command strings are never used."""

    return subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_failure(result: subprocess.CompletedProcess[bytes], args: Sequence[str]) -> str:
    detail = result.stderr.decode("utf-8", errors="replace").strip()
    command = " ".join(["git", *args])
    if detail:
        return f"{command} failed rc={result.returncode}: {detail}"
    return f"{command} failed rc={result.returncode}"


def _resolve_repo_root(requested: Path | None) -> Path:
    start = (requested or Path.cwd()).expanduser().resolve()
    result = _run_git(start, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise MigrationError(_git_failure(result, ["rev-parse", "--show-toplevel"]))
    try:
        raw = result.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise MigrationError("git rev-parse の repository root が UTF-8 ではありません") from exc
    if not raw:
        raise MigrationError("git rev-parse が空の repository root を返しました")
    return Path(raw).resolve()


def _parse_ls_tree(output: bytes) -> list[TreeEntry]:
    entries: list[TreeEntry] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, git_type, object_id, raw_size = metadata.split(b" ", 3)
        except ValueError as exc:
            raise MigrationError(
                f"git ls-tree の record を parse できません: {record!r}"
            ) from exc
        if raw_size == b"-":
            size: int | None = None
        else:
            try:
                size = int(raw_size)
            except ValueError as exc:
                raise MigrationError(f"git ls-tree の size が不正です: {raw_size!r}") from exc
        try:
            decoded_mode = mode.decode("ascii", errors="strict")
            decoded_git_type = git_type.decode("ascii", errors="strict")
            decoded_object_id = object_id.decode("ascii", errors="strict")
        except UnicodeDecodeError as exc:
            raise MigrationError(
                f"git ls-tree の metadata が ASCII ではありません: {record!r}"
            ) from exc
        entries.append(
            TreeEntry(
                mode=decoded_mode,
                git_type=decoded_git_type,
                object_id=decoded_object_id,
                size=size,
                path=os.fsdecode(raw_path),
            )
        )
    return entries


def _under_root(path: str, root: str) -> bool:
    if not root:
        return True
    return path == root or path.startswith(root + "/")


def _collect_entries(repo: Path, roots: Sequence[str]) -> list[tuple[TreeEntry, str]]:
    """Run one NUL-delimited ls-tree query per root and deduplicate paths."""

    collected: list[tuple[TreeEntry, str]] = []
    seen: set[str] = set()
    for root in roots:
        pathspec = root or "."
        git_args = ["ls-tree", "-r", "-l", "-z", "HEAD", "--", pathspec]
        result = _run_git(repo, git_args)
        if result.returncode != 0:
            raise MigrationError(_git_failure(result, git_args))
        for entry in _parse_ls_tree(result.stdout):
            if entry.path in seen:
                continue
            seen.add(entry.path)
            collected.append((entry, root))
    return collected


def _mode_bits(mode: str) -> int:
    try:
        return int(mode, 8)
    except ValueError as exc:
        raise MigrationError(f"git mode が不正です: {mode!r}") from exc


def _working_path(repo: Path, relative_path: str) -> Path:
    return repo.joinpath(*relative_path.split("/"))


def _git_path_clean(repo: Path, relative_path: str) -> bool:
    for git_args in (
        ["diff", "--quiet", "--", relative_path],
        ["diff", "--cached", "--quiet", "--", relative_path],
    ):
        result = _run_git(repo, git_args)
        if result.returncode == 0:
            continue
        if result.returncode == 1:
            return False
        raise MigrationError(_git_failure(result, git_args))
    return True


def _cat_head_blob(repo: Path, relative_path: str) -> bytes:
    git_args = ["cat-file", "blob", f"HEAD:{relative_path}"]
    result = _run_git(repo, git_args)
    if result.returncode != 0:
        raise MigrationError(_git_failure(result, git_args))
    return result.stdout


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _find_parent_symlink(repo: Path, path: Path) -> Path | None:
    """Return the first symlink in repo -> path.parent, if any."""

    try:
        relative_parent = path.parent.relative_to(repo)
    except ValueError as exc:
        raise MigrationError(f"path is outside repository root: {path}") from exc

    current = repo
    if os.path.islink(os.fspath(current)):
        return current
    for component in relative_parent.parts:
        current /= component
        if os.path.islink(os.fspath(current)):
            return current
    return None


def _ensure_parent_chain_safe(repo: Path, candidate: Candidate) -> None:
    for path in (candidate.source, candidate.destination):
        symlink = _find_parent_symlink(repo, path)
        if symlink is not None:
            raise MigrationError(
                f"parent directory became symlink for {candidate.entry.path}: {symlink}"
            )


def _inspect_working_state(
    repo: Path, entry: TreeEntry, report: Report
) -> tuple[Candidate | None, bool]:
    """Return a safe source candidate and whether a fatal state was found."""
    source = _working_path(repo, entry.path)
    destination = Path(f"{source}.gz")

    for path in (source, destination):
        symlink = _find_parent_symlink(repo, path)
        if symlink is not None:
            report.add_exclusion(entry.path, "symlink", f"parent={symlink}")
            return None, False

    source_exists = _lexists(source)
    destination_exists = _lexists(destination)

    if source_exists and destination_exists:
        report.add_skip(entry.path, "source-and-gzip-both-exist")
        return None, True
    if not source_exists and destination_exists:
        report.add_skip(entry.path, "processed-existing-gzip")
        return None, False
    if not source_exists:
        report.add_skip(entry.path, "source-missing")
        return None, False

    # This explicit check is required even though the Git mode was parsed
    # above: the working tree can be replaced independently of HEAD.
    if os.path.islink(os.fspath(source)):
        report.add_exclusion(entry.path, "symlink", "working-tree")
        return None, False
    try:
        metadata = os.stat(source)
    except OSError as exc:
        report.add_skip(entry.path, "stat-failed", type(exc).__name__)
        return None, False
    if not stat.S_ISREG(metadata.st_mode):
        report.add_exclusion(entry.path, "non-regular", "working-tree")
        return None, False
    if metadata.st_nlink > 1:
        report.add_exclusion(entry.path, "hardlink", f"nlink={metadata.st_nlink}")
        return None, False
    if not _git_path_clean(repo, entry.path):
        report.add_skip(entry.path, "working-tree-or-index-dirty")
        return None, False

    return (
        Candidate(
            entry=entry,
            source=source,
            destination=destination,
            mode=stat.S_IMODE(metadata.st_mode),
        ),
        False,
    )


def _preflight_candidate(repo: Path, candidate: Candidate, report: Report) -> Plan | None:
    """Read HEAD/source bytes, compress, and verify one candidate."""

    entry = candidate.entry
    source = candidate.source

    try:
        head_bytes = _cat_head_blob(repo, entry.path)
    except MigrationError as exc:
        report.add_skip(entry.path, "head-blob-unavailable", str(exc))
        return None
    try:
        source_bytes = source.read_bytes()
    except OSError as exc:
        report.add_skip(entry.path, "source-read-failed", type(exc).__name__)
        return None
    if source_bytes != head_bytes:
        report.add_skip(entry.path, "working-tree-byte-mismatch")
        return None

    try:
        compressed = compress_bytes(source_bytes)
    except Exception as exc:  # a compression failure is a per-file skip
        report.add_skip(entry.path, "compression-failed", type(exc).__name__)
        return None
    try:
        restored = gzip.decompress(compressed)
    except Exception as exc:
        report.add_skip(entry.path, "verification-failed", type(exc).__name__)
        return None
    if restored != head_bytes:
        report.add_skip(entry.path, "verification-mismatch")
        return None

    return Plan(
        candidate=candidate,
        source_bytes=head_bytes,
        compressed=bytes(compressed),
    )


def _select_entry(
    entry: TreeEntry,
    root: str,
    extensions: Sequence[str],
    exclude_paths: set[str],
    min_bytes: int,
    report: Report,
) -> bool:
    """Apply the required root -> suffix -> exact path -> size filter order."""

    if not _under_root(entry.path, root):
        report.add_exclusion(entry.path, "outside-root")
        return False
    if not any(entry.path.endswith(extension) for extension in extensions):
        report.add_exclusion(entry.path, "extension-mismatch")
        return False
    if entry.path in exclude_paths:
        report.add_exclusion(entry.path, "excluded-path", "exact")
        return False
    if entry.size is None or entry.size <= min_bytes:
        report.add_exclusion(
            entry.path,
            "size-not-over-min",
            f"size={entry.size if entry.size is not None else 'unknown'} min={min_bytes}",
        )
        return False

    mode = _mode_bits(entry.mode)
    if entry.git_type != "blob":
        report.add_exclusion(entry.path, "non-regular", f"git-type={entry.git_type}")
        return False
    if stat.S_ISLNK(mode):
        report.add_exclusion(entry.path, "symlink", f"git-mode={entry.mode}")
        return False
    if not stat.S_ISREG(mode):
        report.add_exclusion(entry.path, "non-regular", f"git-mode={entry.mode}")
        return False
    return True


def _write_temp_gzip(directory: Path, compressed: bytes, mode: int) -> Path:
    fd, raw_name = tempfile.mkstemp(
        prefix=".migrate-output-gzip-",
        suffix=".tmp",
        dir=directory,
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(compressed)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
    except Exception:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return temporary


def _fsync_directory(directory: Path) -> None:
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _remove_if_ours(path: Path, expected: bytes | None = None) -> str | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        return f"could not inspect {path}: {type(exc).__name__}: {exc}"

    if stat.S_ISLNK(metadata.st_mode):
        return f"refused to remove symlink {path}"
    if not stat.S_ISREG(metadata.st_mode):
        return f"refused to remove non-regular path {path}"
    if expected is not None:
        try:
            current = path.read_bytes()
        except OSError as exc:
            return f"could not inspect {path}: {type(exc).__name__}: {exc}"
        if current != expected:
            return f"refused to remove changed path {path}"
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    except OSError as exc:
        return f"could not remove {path}: {type(exc).__name__}: {exc}"
    return None


def _revalidate_source(repo: Path, plan: Plan) -> None:
    candidate = plan.candidate
    _ensure_parent_chain_safe(repo, candidate)
    if not _lexists(candidate.source):
        raise MigrationError(f"pre-stage source disappeared for {candidate.entry.path}")
    if os.path.islink(os.fspath(candidate.source)):
        raise MigrationError(f"pre-stage source became symlink: {candidate.entry.path}")
    try:
        metadata = os.stat(candidate.source)
    except OSError as exc:
        raise MigrationError(f"pre-stage stat failed for {candidate.entry.path}: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink > 1:
        raise MigrationError(
            f"pre-stage source is not an independent regular file: {candidate.entry.path}"
        )
    if stat.S_IMODE(metadata.st_mode) != candidate.mode:
        raise MigrationError(f"pre-stage mode changed for {candidate.entry.path}")
    if not _git_path_clean(repo, candidate.entry.path):
        raise MigrationError(f"pre-stage Git state changed for {candidate.entry.path}")
    try:
        current = candidate.source.read_bytes()
    except OSError as exc:
        raise MigrationError(f"pre-stage read failed for {candidate.entry.path}: {exc}") from exc
    if current != plan.source_bytes:
        raise MigrationError(f"pre-stage bytes changed for {candidate.entry.path}")


def _revalidate_plan(repo: Path, plan: Plan) -> None:
    candidate = plan.candidate
    _ensure_parent_chain_safe(repo, candidate)
    if not _lexists(candidate.source) or _lexists(candidate.destination):
        raise MigrationError(f"pre-stage state changed for {candidate.entry.path}")
    _revalidate_source(repo, plan)


def _verify_destination_bytes(repo: Path, plan: Plan, *, phase: str) -> None:
    candidate = plan.candidate
    _ensure_parent_chain_safe(repo, candidate)
    destination = candidate.destination
    if not _lexists(destination):
        raise MigrationError(
            f"{phase} gzip destination disappeared for {candidate.entry.path}"
        )
    if os.path.islink(os.fspath(destination)):
        raise MigrationError(
            f"{phase} gzip destination became symlink: {candidate.entry.path}"
        )
    try:
        metadata = os.stat(destination)
    except OSError as exc:
        raise MigrationError(
            f"{phase} gzip destination stat failed for {candidate.entry.path}: {exc}"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink > 1:
        raise MigrationError(
            f"{phase} gzip destination is not an independent regular file: "
            f"{candidate.entry.path}"
        )
    try:
        actual = destination.read_bytes()
    except OSError as exc:
        raise MigrationError(
            f"{phase} gzip destination read failed for {candidate.entry.path}: {exc}"
        ) from exc
    if actual != plan.compressed:
        raise MigrationError(
            f"{phase} gzip destination bytes changed for {candidate.entry.path}"
        )


def _verify_staged_destination(repo: Path, plan: Plan) -> None:
    relative_destination = os.fspath(plan.candidate.destination.relative_to(repo))
    git_args = ["cat-file", "blob", f":{relative_destination}"]
    try:
        result = _run_git(repo, git_args)
    except Exception as exc:
        raise MigrationError(
            f"staged gzip verification failed for {plan.candidate.entry.path}: {exc}"
        ) from exc
    if result.returncode != 0:
        raise MigrationError(_git_failure(result, git_args))
    if result.stdout != plan.compressed:
        raise MigrationError(
            f"staged gzip bytes changed for {plan.candidate.entry.path}"
        )


def _link_temp_without_overwrite(
    temporary: Path, destination: Path, relative_path: str
) -> None:
    """Publish a complete gzip without allowing a concurrent overwrite.

    ``os.replace`` would clobber a destination created after a check.  A hard
    link is created atomically and refuses an existing destination; the temp
    name is unlinked by the caller after the final name is visible.
    """

    if _lexists(destination):
        raise MigrationError(f"gzip destination appeared: {relative_path}.gz")
    try:
        os.link(os.fspath(temporary), os.fspath(destination))
    except FileExistsError as exc:
        raise MigrationError(f"gzip destination appeared: {relative_path}.gz") from exc
    except OSError as exc:
        raise MigrationError(
            f"gzip destination install failed for {relative_path}.gz: {exc}"
        ) from exc


def _run_git_checked(repo: Path, git_args: Sequence[str]) -> None:
    result = _run_git(repo, git_args)
    if result.returncode != 0:
        raise MigrationError(_git_failure(result, git_args))


def _restore_after_stage_failure(
    repo: Path, plans: Sequence[Plan], *, reset_gzip: bool
) -> list[str]:
    """Restore explicit migration paths and return every rollback failure."""

    failures: list[str] = []
    source_paths = [plan.candidate.entry.path for plan in plans]
    gzip_paths = [os.fspath(plan.candidate.destination.relative_to(repo)) for plan in plans]

    def reset_paths(label: str, paths: Sequence[str]) -> None:
        if not paths:
            return
        git_args = ["reset", "--", *paths]
        try:
            result = _run_git(repo, git_args)
        except Exception as exc:
            failures.append(f"{label}: {type(exc).__name__}: {exc}")
            return
        if result.returncode != 0:
            failures.append(f"{label}: {_git_failure(result, git_args)}")

    reset_paths("source index reset failed", source_paths)
    if reset_gzip:
        reset_paths("gzip index reset failed", gzip_paths)

    for plan in plans:
        source = plan.candidate.source
        try:
            _ensure_parent_chain_safe(repo, plan.candidate)
            if os.path.islink(os.fspath(source)):
                raise MigrationError(f"source is symlink: {plan.candidate.entry.path}")
            if _lexists(source):
                metadata = os.stat(source)
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink > 1:
                    raise MigrationError(
                        f"source is not an independent regular file: "
                        f"{plan.candidate.entry.path}"
                    )
                if source.read_bytes() != plan.source_bytes:
                    raise MigrationError(
                        f"source changed during rollback: {plan.candidate.entry.path}"
                    )
            source.write_bytes(plan.source_bytes)
            os.chmod(source, plan.candidate.mode)
        except Exception as exc:
            failures.append(
                f"source restore failed for {plan.candidate.entry.path}: "
                f"{type(exc).__name__}: {exc}"
            )
    return failures


def _stage_plans(repo: Path, plans: Sequence[Plan]) -> None:
    """Create all final gzip files, then stage all deletions/additions in batches."""

    for plan in plans:
        _revalidate_plan(repo, plan)

    temporary_pairs: list[tuple[Path, Plan]] = []
    final_paths: list[tuple[Path, bytes]] = []
    git_rm_started = False
    git_add_started = False
    try:
        for plan in plans:
            _ensure_parent_chain_safe(repo, plan.candidate)
            temporary = _write_temp_gzip(
                plan.candidate.destination.parent,
                plan.compressed,
                plan.candidate.mode,
            )
            temporary_pairs.append((temporary, plan))

        # No source is removed until every gzip has been written.  Re-check all
        # sources after the last temporary file was created as a final TOCTOU
        # guard before any final destination is installed.
        for plan in plans:
            _revalidate_plan(repo, plan)

        for temporary, plan in temporary_pairs:
            _ensure_parent_chain_safe(repo, plan.candidate)
            _link_temp_without_overwrite(
                temporary,
                plan.candidate.destination,
                plan.candidate.entry.path,
            )
            final_paths.append((plan.candidate.destination, plan.compressed))
            temporary.unlink()
            _fsync_directory(plan.candidate.destination.parent)

        # Re-check the source after publishing the destinations and immediately
        # before deleting any source.  The destination checks below also make
        # sure a concurrent writer cannot cause unrelated bytes to be staged.
        for plan in plans:
            _revalidate_source(repo, plan)
            _verify_destination_bytes(repo, plan, phase="pre-stage")

        source_paths = [plan.candidate.entry.path for plan in plans]
        gzip_paths = [
            os.fspath(plan.candidate.destination.relative_to(repo)) for plan in plans
        ]
        git_rm_started = True
        _run_git_checked(repo, ["rm", "--", *source_paths])
        git_add_started = True
        _run_git_checked(repo, ["add", "--", *gzip_paths])
        for plan in plans:
            _verify_destination_bytes(repo, plan, phase="post-stage")
            _verify_staged_destination(repo, plan)
    except Exception as exc:
        rollback_failures: list[str] = []
        for temporary, _plan in temporary_pairs:
            failure = _remove_if_ours(temporary)
            if failure:
                rollback_failures.append(failure)
        if git_rm_started or git_add_started:
            try:
                rollback_failures.extend(
                    _restore_after_stage_failure(
                        repo,
                        plans,
                        reset_gzip=git_add_started,
                    )
                )
            except Exception as rollback_exc:
                rollback_failures.append(
                    "rollback procedure raised "
                    f"{type(rollback_exc).__name__}: {rollback_exc}"
                )
        for final_path, expected in final_paths:
            failure = _remove_if_ours(final_path, expected)
            if failure:
                rollback_failures.append(failure)
        if rollback_failures:
            detail = "; ".join(rollback_failures)
            raise MigrationError(
                f"staging failed: {type(exc).__name__}: {exc}; "
                f"rollback failed: {detail}"
            ) from exc
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    report = Report()
    try:
        repo = _resolve_repo_root(args.repo_root)
        entries = _collect_entries(repo, args.root)
        exclude_paths = set(args.exclude_path)

        candidates: list[tuple[TreeEntry, str]] = []
        for entry, root in entries:
            if _select_entry(
                entry,
                root,
                args.extension,
                exclude_paths,
                args.min_bytes,
                report,
            ):
                candidates.append((entry, root))

        inspected: list[Candidate] = []
        fatal_state = False
        for entry, _root in candidates:
            candidate, is_fatal = _inspect_working_state(repo, entry, report)
            fatal_state = fatal_state or is_fatal
            if candidate is not None:
                inspected.append(candidate)

        if fatal_state:
            report.add_error("source-and-gzip-both-exist: apply/dry-run stopped")
        else:
            for candidate in inspected:
                plan = _preflight_candidate(repo, candidate, report)
                if plan is not None:
                    report.plans.append(plan)

            if args.apply and report.plans:
                _stage_plans(repo, report.plans)
                report.staged.extend(
                    plan.candidate.entry.path for plan in report.plans
                )
    except MigrationError as exc:
        report.add_error(str(exc))
    except OSError as exc:
        report.add_error(f"OS error: {exc}")
    except Exception as exc:
        report.add_error(f"unexpected {type(exc).__name__}: {exc}")

    report.render(apply=args.apply)
    return 2 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
