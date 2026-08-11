"""T-810 slice 1 の単一 fail-closed validator。

この module は検査結果だけを返し、launch / approval capability を返さない。
DurableRootPolicy の注入は協調的 routing に限られ、能力遮断ではない。
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from orchestrator.campaign.durable_root import (
    ApprovedRoot,
    DurableRootError,
    DurableRootPolicy,
    resolve_policy_root,
)
from orchestrator.campaign.t810_preregistration import (
    VerifiedT810Preregistration,
)


PASS_RECEIPT_SCHEMA = "t810-validator-pass/v1"
MANIFEST_SCHEMA = "t810-frozen-manifest/v1"
LIMITATIONS = (
    "execution_mediation_incomplete: 未記録 exec の不存在はこの validator では証明できない",
    "durable_root_policy_is_cooperative_routing_not_capability_confinement",
    "d2_measurement_node_repository_absence_is_out_of_scope",
)
FORBIDDEN_REGION_CODES = frozenset({
    "FORBIDDEN_OUTPUT",
    "FORBIDDEN_ENV_CONTRACT",
    "FORBIDDEN_ENV_CONTRACT_ACTIVATIONS",
})


class T810ValidationError(ValueError):
    """入力または検査面を安全に解釈できない。"""


@dataclass(frozen=True)
class GitIdentity:
    repo_realpath: str
    git_dir_realpath: str
    common_dir_realpath: str


@dataclass(frozen=True)
class FileRecord:
    path: str
    kind: str
    mode: int
    size: int
    sha256: str | None
    mtime_ns: int
    dev: int
    inode: int
    ctime_ns: int
    link_target: str | None = None


@dataclass(frozen=True)
class TreeInventory:
    root: str
    status: str
    records: tuple[FileRecord, ...]


@dataclass(frozen=True)
class GitlinkRecord:
    path: str
    index_object_id: str
    submodule_head: str
    dirty: bool


@dataclass(frozen=True)
class RepositorySnapshot:
    identity: GitIdentity
    head: str
    index: str
    status: str
    refs: str
    packed_refs_sha256: str | None
    config_sha256: str | None
    files: tuple[FileRecord, ...]
    tracked_regular_sha256: tuple[tuple[str, str], ...]
    gitlinks: tuple[GitlinkRecord, ...]
    git_admin: TreeInventory


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str
    blocking: bool = True


@dataclass(frozen=True)
class ValidationBaseline:
    repository: RepositorySnapshot
    forbidden_regions: tuple[tuple[str, TreeInventory], ...]
    calibration: tuple[TreeInventory, ...]


@dataclass(frozen=True)
class Slice1ValidationResult:
    ok: bool
    terminal_state: str
    baseline_digest: str
    baseline: ValidationBaseline
    findings: tuple[Finding, ...]
    limitations: tuple[str, ...] = LIMITATIONS


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_regular_stable(path: Path, before: os.stat_result) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise T810ValidationError(f"scan race while opening {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after_fd = os.fstat(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise T810ValidationError(f"unreadable file during scan: {path}") from exc
    return b"".join(chunks), after_fd


def _stat_fingerprint(info: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


def _record(path: Path, relpath: str, info: os.stat_result) -> FileRecord:
    link_target: str | None = None
    digest: str | None = None
    if stat.S_ISREG(info.st_mode):
        raw, after_fd = _read_regular_stable(path, info)
        if _stat_fingerprint(after_fd) != _stat_fingerprint(info):
            raise T810ValidationError(f"file changed while being read: {path}")
        digest = _sha256_bytes(raw)
        kind = "regular"
    elif stat.S_ISDIR(info.st_mode):
        kind = "directory"
    elif stat.S_ISLNK(info.st_mode):
        try:
            link_target = os.readlink(path)
        except OSError as exc:
            raise T810ValidationError(f"unreadable symlink during scan: {path}") from exc
        digest = _sha256_bytes(os.fsencode(link_target))
        kind = "symlink"
    elif stat.S_ISSOCK(info.st_mode):
        kind = "socket"
    elif stat.S_ISFIFO(info.st_mode):
        kind = "fifo"
    elif stat.S_ISCHR(info.st_mode):
        kind = "character-device"
    elif stat.S_ISBLK(info.st_mode):
        kind = "block-device"
    else:
        kind = "unknown"
    try:
        after_path = path.lstat()
    except OSError as exc:
        raise T810ValidationError(f"entry disappeared during scan: {path}") from exc
    if _stat_fingerprint(after_path) != _stat_fingerprint(info):
        raise T810ValidationError(f"entry changed during scan: {path}")
    return FileRecord(
        path=relpath,
        kind=kind,
        mode=stat.S_IMODE(info.st_mode),
        size=info.st_size,
        sha256=digest,
        mtime_ns=info.st_mtime_ns,
        dev=info.st_dev,
        inode=info.st_ino,
        ctime_ns=info.st_ctime_ns,
        link_target=link_target,
    )


def _scan_once(root: Path, *, excluded: frozenset[Path] = frozenset()) -> tuple[FileRecord, ...]:
    records: list[FileRecord] = []

    def walk(directory: Path) -> None:
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: os.fsencode(item.name))
        except OSError as exc:
            raise T810ValidationError(f"unreadable directory during scan: {directory}") from exc
        for entry in entries:
            path = directory / entry.name
            if path in excluded:
                continue
            try:
                before = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise T810ValidationError(f"unreadable entry during scan: {path}") from exc
            relpath = path.relative_to(root).as_posix()
            records.append(_record(path, relpath, before))
            if stat.S_ISDIR(before.st_mode):
                walk(path)

    walk(root)
    return tuple(records)


def scan_tree(root: Path, *, excluded: Iterable[Path] = ()) -> TreeInventory:
    """gitignore を参照せず二重走査する。symlink directory は追わない。"""

    root = Path(root)
    try:
        root_info = root.lstat()
    except FileNotFoundError:
        return TreeInventory(root=str(root.absolute()), status="absent", records=())
    except OSError as exc:
        raise T810ValidationError(f"could not inspect inventory root: {root}") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise T810ValidationError(f"inventory root is not a real directory: {root}")
    absolute = root.absolute()
    excluded_set = frozenset(Path(item).absolute() for item in excluded)
    first = _scan_once(absolute, excluded=excluded_set)
    second = _scan_once(absolute, excluded=excluded_set)
    if first != second:
        raise T810ValidationError(f"filesystem changed between scans: {absolute}")
    return TreeInventory(root=str(absolute), status="present", records=first)


def _git(repo: Path, *args: str, allow_empty: bool = False) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 and not (allow_empty and proc.returncode == 1 and not proc.stdout):
        raise T810ValidationError(
            "git command failed: " + " ".join(args) + ": "
            + proc.stderr.decode("utf-8", "replace").strip()
        )
    return proc.stdout.decode("utf-8", "surrogateescape")


def resolve_git_identity(repo_root: Path) -> GitIdentity:
    repo_input = Path(repo_root)
    if not repo_input.is_absolute():
        raise T810ValidationError("repo_root must be absolute")
    try:
        if stat.S_ISLNK(repo_input.lstat().st_mode):
            raise T810ValidationError("repo_root must not be a symlink")
        repo_real = repo_input.resolve(strict=True)
    except OSError as exc:
        raise T810ValidationError("repo_root cannot be resolved") from exc
    if repo_input.absolute() != repo_real:
        raise T810ValidationError("repo_root must be its strict realpath")
    top = Path(_git(repo_real, "rev-parse", "--show-toplevel").strip()).resolve(strict=True)
    if top != repo_real:
        raise T810ValidationError("repo_root is not the git top-level")
    git_dir = Path(
        _git(repo_real, "rev-parse", "--path-format=absolute", "--git-dir").strip()
    ).resolve(strict=True)
    common_dir = Path(
        _git(repo_real, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    ).resolve(strict=True)
    return GitIdentity(str(repo_real), str(git_dir), str(common_dir))


def _optional_digest(path: Path) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise T810ValidationError(f"could not inspect git semantic file: {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise T810ValidationError(f"git semantic file is not regular: {path}")
    raw, after = _read_regular_stable(path, info)
    if _stat_fingerprint(info) != _stat_fingerprint(after):
        raise T810ValidationError(f"git semantic file changed: {path}")
    return _sha256_bytes(raw)


def inspect_repository(repo_root: Path, approved_identity: GitIdentity) -> RepositorySnapshot:
    identity = resolve_git_identity(repo_root)
    if identity != approved_identity:
        raise T810ValidationError("repo_root git identity does not match approved identity")
    repo = Path(identity.repo_realpath)
    nested = repo / ".claude" / "worktrees"
    try:
        nested.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise T810ValidationError("could not prove nested-worktree path absent") from exc
    else:
        raise T810ValidationError("dedicated checkout contains .claude/worktrees")

    head = _git(repo, "rev-parse", "HEAD").strip()
    index = _git(repo, "ls-files", "--stage", "-z")
    status_text = _git(
        repo, "status", "--porcelain=v2", "--branch", "--untracked-files=all"
    )
    refs = _git(repo, "show-ref", allow_empty=True)
    if not head or not index:
        raise T810ValidationError("repository HEAD and index must be non-empty")

    git_dir = Path(identity.git_dir_realpath)
    common_dir = Path(identity.common_dir_realpath)
    excluded: set[Path] = set()
    if git_dir.is_relative_to(repo):
        excluded.add(git_dir)
    files = scan_tree(repo, excluded=excluded).records
    file_map = {record.path: record for record in files}
    tracked: list[tuple[str, str]] = []
    gitlinks: list[GitlinkRecord] = []
    entries = [item for item in index.split("\0") if item]
    for item in entries:
        try:
            metadata, path = item.split("\t", 1)
            mode, object_id, stage = metadata.split(" ")
        except ValueError as exc:
            raise T810ValidationError("malformed git index record") from exc
        if stage != "0":
            raise T810ValidationError("unmerged index stage is forbidden")
        if mode == "160000":
            submodule = repo / path
            sub_head = _git(submodule, "rev-parse", "HEAD").strip()
            dirty = bool(_git(submodule, "status", "--porcelain=v2", "--untracked-files=all"))
            gitlinks.append(GitlinkRecord(path, object_id, sub_head, dirty))
            continue
        if mode in {"100644", "100755"}:
            record = file_map.get(path)
            if record is None or record.kind != "regular" or record.sha256 is None:
                raise T810ValidationError(f"tracked regular file missing or replaced: {path}")
            tracked.append((path, record.sha256))

    admin_excluded = {common_dir / "objects"}
    git_admin = scan_tree(git_dir, excluded=admin_excluded)
    return RepositorySnapshot(
        identity=identity,
        head=head,
        index=index,
        status=status_text,
        refs=refs,
        packed_refs_sha256=_optional_digest(common_dir / "packed-refs"),
        config_sha256=_optional_digest(common_dir / "config"),
        files=files,
        tracked_regular_sha256=tuple(tracked),
        gitlinks=tuple(gitlinks),
        git_admin=git_admin,
    )


def make_t810_durable_root(
    writable_root: Path, repo_root: Path, *, mountinfo_text: str | None = None
) -> ApprovedRoot:
    """d1 の協調的 routing policy を注入する。d2 の能力遮断ではない。"""

    writable_input = Path(writable_root)
    repo_input = Path(repo_root)
    if not writable_input.is_absolute() or not repo_input.is_absolute():
        raise T810ValidationError("writable_root and repo_root must be absolute")
    try:
        if stat.S_ISLNK(writable_input.lstat().st_mode) or stat.S_ISLNK(repo_input.lstat().st_mode):
            raise T810ValidationError("root paths must not be symlinks")
        writable = writable_input.resolve(strict=True)
        repo = repo_input.resolve(strict=True)
    except OSError as exc:
        raise T810ValidationError("root paths must be existing real directories") from exc
    if writable_input.absolute() != writable or repo_input.absolute() != repo:
        raise T810ValidationError("root paths must be their strict realpaths")
    if writable == repo or writable.is_relative_to(repo) or repo.is_relative_to(writable):
        raise T810ValidationError("writable root and repository overlap")
    policy = DurableRootPolicy(approved_roots=(writable,), forbidden_roots=(repo,))
    try:
        return resolve_policy_root(policy, str(writable), mountinfo_text=mountinfo_text)
    except DurableRootError as exc:
        raise T810ValidationError(str(exc)) from exc


def _calibration_inventories(repo: Path, writable: Path) -> tuple[TreeInventory, ...]:
    env_root = repo / "output" / "env"
    roots: list[Path] = []
    try:
        with os.scandir(env_root) as iterator:
            envs = sorted(iterator, key=lambda item: os.fsencode(item.name))
    except FileNotFoundError:
        envs = []
    except OSError as exc:
        raise T810ValidationError("cannot enumerate calibration namespaces") from exc
    for env in envs:
        try:
            env_info = env.stat(follow_symlinks=False)
        except OSError as exc:
            raise T810ValidationError("cannot inspect environment namespace") from exc
        if not stat.S_ISDIR(env_info.st_mode):
            continue
        calibration = Path(env.path) / "calibration"
        try:
            cal_info = calibration.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise T810ValidationError("cannot inspect calibration namespace") from exc
        if not stat.S_ISDIR(cal_info.st_mode) and not stat.S_ISLNK(cal_info.st_mode):
            raise T810ValidationError("calibration namespace is not a directory")
        real = calibration.resolve(strict=True)
        if not real.is_dir():
            raise T810ValidationError("calibration namespace alias target is not a directory")
        if writable == real or writable.is_relative_to(real) or real.is_relative_to(writable):
            raise T810ValidationError("writable root overlaps calibration namespace")
        roots.append(real)

    # 別名 symlink を列挙して realpath overlap を再確認する。alias の存在自体は拒否しない。
    repo_inventory = scan_tree(repo, excluded={Path(resolve_git_identity(repo).git_dir_realpath)})
    calibration_realpaths = tuple(roots)
    for record in repo_inventory.records:
        if record.kind != "symlink":
            continue
        alias = repo / record.path
        try:
            target = alias.resolve(strict=True)
        except OSError:
            continue
        if any(target == root or target.is_relative_to(root) for root in calibration_realpaths):
            if writable == target or writable.is_relative_to(target) or target.is_relative_to(writable):
                raise T810ValidationError(f"writable root overlaps calibration alias: {alias}")
    return tuple(scan_tree(root) for root in sorted(set(roots)))


def _parse_json_no_duplicates(raw: bytes, what: str) -> Mapping[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise T810ValidationError(f"duplicate JSON key in {what}: {key}")
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise T810ValidationError(f"invalid JSON in {what}") from exc
    if not isinstance(value, dict):
        raise T810ValidationError(f"{what} root must be an object")
    return value


def verify_frozen_manifest(
    manifest_path: Path, manifest_root: Path, *, expected_sha256: str
) -> TreeInventory:
    if (
        type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or any(ch not in "0123456789abcdef" for ch in expected_sha256)
    ):
        raise T810ValidationError("expected manifest sha256 is required")
    manifest = Path(manifest_path)
    root = Path(manifest_root)
    try:
        if stat.S_ISLNK(manifest.lstat().st_mode) or stat.S_ISLNK(root.lstat().st_mode):
            raise T810ValidationError("manifest and manifest root must not be symlinks")
        manifest_real = manifest.resolve(strict=True)
        root_real = root.resolve(strict=True)
        raw = manifest_real.read_bytes()
    except OSError as exc:
        raise T810ValidationError("manifest cannot be read") from exc
    if manifest.absolute() != manifest_real or root.absolute() != root_real:
        raise T810ValidationError("manifest paths must be their strict realpaths")
    if _sha256_bytes(raw) != expected_sha256:
        raise T810ValidationError("manifest digest mismatch")
    value = _parse_json_no_duplicates(raw, "manifest")
    if set(value) != {"schema_version", "members"} or value["schema_version"] != MANIFEST_SCHEMA:
        raise T810ValidationError("manifest schema mismatch")
    members = value["members"]
    if not isinstance(members, list) or not members:
        raise T810ValidationError("manifest members must be non-empty")
    expected: dict[str, tuple[int, str]] = {}
    for member in members:
        if not isinstance(member, dict) or set(member) != {"path", "size", "sha256"}:
            raise T810ValidationError("manifest member schema mismatch")
        rel = member["path"]
        if type(rel) is not str or not rel or "\\" in rel:
            raise T810ValidationError("invalid manifest member path")
        pure = PurePosixPath(rel)
        if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
            raise T810ValidationError("manifest member escapes root")
        if rel in expected:
            raise T810ValidationError("duplicate manifest member path")
        size, digest = member["size"], member["sha256"]
        if (
            type(size) is not int or size < 0 or not isinstance(digest, str)
            or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise T810ValidationError("invalid manifest size or digest")
        expected[rel] = (size, digest)
    inventory = scan_tree(root_real)
    actual_files = {record.path: record for record in inventory.records if record.kind != "directory"}
    allowed_extra: set[str] = set()
    if manifest_real.is_relative_to(root_real):
        allowed_extra.add(manifest_real.relative_to(root_real).as_posix())
    if set(actual_files) != set(expected) | allowed_extra:
        raise T810ValidationError("manifest root contains missing or unlisted files")
    for rel, (size, digest) in expected.items():
        record = actual_files[rel]
        if record.kind != "regular" or record.size != size or record.sha256 != digest:
            raise T810ValidationError(f"manifest member mismatch: {rel}")
    allowed_dirs = {str(parent) for rel in expected for parent in PurePosixPath(rel).parents if str(parent) != "."}
    if manifest_real.is_relative_to(root_real):
        manifest_rel = manifest_real.relative_to(root_real)
        allowed_dirs.update(
            str(parent) for parent in PurePosixPath(manifest_rel.as_posix()).parents
            if str(parent) != "."
        )
    actual_dirs = {record.path for record in inventory.records if record.kind == "directory"}
    if actual_dirs != allowed_dirs:
        raise T810ValidationError("manifest root contains an unlisted directory")
    return inventory


def canonical_benchmark_argv(
    preregistration: VerifiedT810Preregistration, executable_realpath: str
) -> tuple[str, ...]:
    measurement = preregistration.projection["measurement"]
    workload = measurement["workload"]
    return (
        executable_realpath,
        f"-ycsb_tuple_num={measurement['records']}",
        f"-ycsb_zipf_skew={workload['ycsb_zipf_skew']}",
        f"-ycsb_rratio={workload['ycsb_rratio']}",
        f"-ycsb_rmw={workload['ycsb_rmw']}",
        f"-thread_num={measurement['threads']}",
        f"-extime={measurement['repetition_duration_seconds']}",
        f"-clocks_per_us={measurement['clocks_per_us']}",
    )


def _receipt_evidence(
    value: Mapping[str, Any] | None, expected_slots: int
) -> tuple[bool, bool, frozenset[str], frozenset[str], tuple[Finding, ...], tuple[Mapping[str, Any], ...]]:
    findings: list[Finding] = []
    if not isinstance(value, Mapping):
        return False, False, frozenset(), frozenset(), (Finding("RECEIPT_INCOMPLETE", "receipt missing"),), ()
    coordinator = value.get("coordinator")
    slots = value.get("slots")
    if not isinstance(coordinator, Mapping) or not isinstance(slots, Sequence) or isinstance(slots, (str, bytes)):
        return False, False, frozenset(), frozenset(), (Finding("RECEIPT_INCOMPLETE", "coordinator or slots missing"),), ()
    events = coordinator.get("events")
    complete = coordinator.get("complete") is True and isinstance(events, Sequence) and not isinstance(events, (str, bytes))
    release_count = list(events).count("release") if complete else 0
    if release_count > 1:
        complete = False
    seen: set[str] = set()
    started: set[str] = set()
    completed: set[str] = set()
    normalized: list[Mapping[str, Any]] = []
    for slot in slots:
        if not isinstance(slot, Mapping):
            complete = False
            continue
        slot_id = slot.get("slot_id")
        slot_events = slot.get("events")
        if (
            type(slot_id) is not str
            or slot_id in seen
            or not isinstance(slot_events, Sequence)
            or isinstance(slot_events, (str, bytes))
            or slot.get("complete") is not True
        ):
            complete = False
            continue
        seen.add(slot_id)
        if list(slot_events).count("measurement_start") > 1:
            complete = False
        if "measurement_start" in slot_events:
            started.add(slot_id)
        if slot.get("completed") is True:
            completed.add(slot_id)
            if slot_id not in started:
                complete = False
        normalized.append(slot)
    expected_ids = {f"slot-{index:02d}" for index in range(expected_slots)}
    if seen != expected_ids or len(slots) != expected_slots:
        complete = False
    if not complete:
        findings.append(Finding("RECEIPT_INCOMPLETE", "coordinator/node receipt missing or contradictory"))
    return complete, release_count == 1, frozenset(started), frozenset(completed), tuple(findings), tuple(normalized)


def classify_terminal_state(
    receipt: Mapping[str, Any] | None,
    *,
    expected_slots: int,
    claimed_state: str,
    post_validation_passed: bool,
) -> str:
    complete, release, started, completed, _, _ = _receipt_evidence(receipt, expected_slots)
    if post_validation_passed and complete and claimed_state in {"valid", "terminal_reduced"}:
        expected_completed = expected_slots if claimed_state == "valid" else expected_slots - 1
        if release and len(completed) == expected_completed and started.issuperset(completed):
            return claimed_state
    if not complete:
        return "incomplete_after_start"
    if started:
        return "incomplete_after_start"
    if release:
        return "post_release_pre_measurement_invalid"
    return "pre_release_invalid"


def _verify_executable_and_argv(
    preregistration: VerifiedT810Preregistration,
    executable: Path,
    expected_executable_sha256: str,
    slots: Sequence[Mapping[str, Any]],
) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    try:
        info = executable.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise T810ValidationError("executable must be a non-symlink regular file")
        executable_real = executable.resolve(strict=True)
        if executable.absolute() != executable_real:
            raise T810ValidationError("executable path must be its strict realpath")
        raw, after = _read_regular_stable(executable, info)
        if _stat_fingerprint(info) != _stat_fingerprint(after):
            raise T810ValidationError("executable changed while hashing")
    except (OSError, T810ValidationError) as exc:
        return (Finding("EXECUTABLE_INVALID", str(exc)),)
    if _sha256_bytes(raw) != expected_executable_sha256:
        findings.append(Finding("EXECUTABLE_HASH_MISMATCH", str(executable_real)))
    expected_argv = canonical_benchmark_argv(preregistration, str(executable_real))
    rounds = int(preregistration.projection["design"]["selected"]["round_count"])
    total_records = 0
    for slot in slots:
        executions = slot.get("executions")
        if not isinstance(executions, Sequence) or isinstance(executions, (str, bytes)):
            findings.append(Finding("EXECUTION_RECEIPT_INVALID", str(slot.get("slot_id"))))
            continue
        if slot.get("completed") is True and len(executions) != rounds:
            findings.append(Finding("EXECUTION_CARDINALITY_MISMATCH", str(slot.get("slot_id"))))
        round_ids: set[int] = set()
        for execution in executions:
            total_records += 1
            if not isinstance(execution, Mapping):
                findings.append(Finding("EXECUTION_RECEIPT_INVALID", str(slot.get("slot_id"))))
                continue
            round_id = execution.get("round_id")
            if type(round_id) is not int or round_id < 1 or round_id > rounds or round_id in round_ids:
                findings.append(Finding("DUPLICATE_OR_INVALID_ROUND_ID", str(slot.get("slot_id"))))
            round_ids.add(round_id)
            if tuple(execution.get("argv", ())) != expected_argv:
                findings.append(Finding("BENCHMARK_ARGV_MISMATCH", str(slot.get("slot_id"))))
            if execution.get("executable_sha256") != expected_executable_sha256:
                findings.append(Finding("EXECUTABLE_RECEIPT_HASH_MISMATCH", str(slot.get("slot_id"))))
            if execution.get("executable_realpath") != str(executable_real):
                findings.append(Finding("EXECUTABLE_RECEIPT_PATH_MISMATCH", str(slot.get("slot_id"))))
    if total_records == 0:
        findings.append(Finding("EXECUTION_RECORDS_EMPTY", "record 0 is forbidden"))
    return tuple(findings)


def expected_attempt_layout(
    preregistration: VerifiedT810Preregistration,
    terminal_state: str,
    *,
    started_slots: frozenset[str],
) -> tuple[str, ...]:
    artifacts = preregistration.projection["artifacts"]
    matrix = artifacts["presence_matrix"].get(terminal_state)
    if matrix is None:
        raise T810ValidationError("unknown terminal state for artifact layout")
    count = int(preregistration.projection["design"]["selected"]["node_count"])
    paths = set(artifacts["root"]["always_files"])
    if matrix["estimate"] == "required":
        paths.add(artifacts["root"]["conditional_estimate_file"])
    for index in range(count):
        slot_id = artifacts["slots"]["id_format"] % index
        for name in artifacts["slots"]["always_files"]:
            paths.add(f"{slot_id}/{name}")
        paths.add(f"{slot_id}/{artifacts['slots']['conditional_node_receipt_file']}")
        if slot_id in started_slots:
            paths.add(f"{slot_id}/{artifacts['slots']['conditional_measurements_file']}")
    if not paths:
        raise T810ValidationError("attempt layout must be non-empty")
    return tuple(sorted(paths))


def _verify_attempt_layout(root: Path, expected: Sequence[str]) -> tuple[Finding, ...]:
    try:
        inventory = scan_tree(root)
    except T810ValidationError as exc:
        return (Finding("ATTEMPT_LAYOUT_UNREADABLE", str(exc)),)
    files = {record.path for record in inventory.records if record.kind != "directory"}
    dirs = {record.path for record in inventory.records if record.kind == "directory"}
    allowed_dirs = {str(parent) for rel in expected for parent in PurePosixPath(rel).parents if str(parent) != "."}
    if any(record.kind != "regular" for record in inventory.records if record.kind != "directory"):
        return (Finding("ATTEMPT_NON_REGULAR_MEMBER", str(root)),)
    if files != set(expected) or dirs != allowed_dirs:
        return (Finding("ATTEMPT_LAYOUT_MISMATCH", str(root)),)
    return ()


def _baseline_payload(baseline: ValidationBaseline) -> dict[str, Any]:
    return asdict(baseline)


def baseline_digest(baseline: ValidationBaseline) -> str:
    raw = json.dumps(_baseline_payload(baseline), sort_keys=True, separators=(",", ":")).encode()
    return _sha256_bytes(raw)


def baseline_to_dict(baseline: ValidationBaseline) -> dict[str, Any]:
    return _baseline_payload(baseline)


def _file_record_from_dict(value: Mapping[str, Any]) -> FileRecord:
    return FileRecord(**value)


def _inventory_from_dict(value: Mapping[str, Any]) -> TreeInventory:
    return TreeInventory(
        root=value["root"],
        status=value["status"],
        records=tuple(_file_record_from_dict(item) for item in value["records"]),
    )


def baseline_from_dict(value: Mapping[str, Any]) -> ValidationBaseline:
    """JSON baseline を exact dataclass へ戻す。不明・欠損 field は拒否する。"""

    try:
        if set(value) != {"repository", "forbidden_regions", "calibration"}:
            raise KeyError
        repo = value["repository"]
        if set(repo) != {
            "identity", "head", "index", "status", "refs", "packed_refs_sha256",
            "config_sha256", "files", "tracked_regular_sha256", "gitlinks", "git_admin",
        }:
            raise KeyError
        identity = GitIdentity(**repo["identity"])
        repository = RepositorySnapshot(
            identity=identity,
            head=repo["head"],
            index=repo["index"],
            status=repo["status"],
            refs=repo["refs"],
            packed_refs_sha256=repo["packed_refs_sha256"],
            config_sha256=repo["config_sha256"],
            files=tuple(_file_record_from_dict(item) for item in repo["files"]),
            tracked_regular_sha256=tuple(tuple(item) for item in repo["tracked_regular_sha256"]),
            gitlinks=tuple(GitlinkRecord(**item) for item in repo["gitlinks"]),
            git_admin=_inventory_from_dict(repo["git_admin"]),
        )
        forbidden = tuple(
            (item[0], _inventory_from_dict(item[1])) for item in value["forbidden_regions"]
        )
        calibration = tuple(_inventory_from_dict(item) for item in value["calibration"])
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise T810ValidationError("baseline schema is invalid") from exc
    baseline = ValidationBaseline(repository, forbidden, calibration)
    # 空 baseline を恒真比較に使わせない。
    if not baseline.repository.files or not baseline.repository.tracked_regular_sha256:
        raise T810ValidationError("baseline repository records must be non-empty")
    return baseline


def write_baseline_create_only(path: Path, baseline: ValidationBaseline, nonce: str) -> None:
    if not nonce:
        raise T810ValidationError("baseline nonce is required")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(baseline_to_dict(baseline), sort_keys=True, separators=(",", ":")) + "\n").encode()
    temp = target.parent / ("." + target.name + "." + nonce + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(temp, flags, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.link(temp, target, follow_symlinks=False)
    except OSError as exc:
        raise T810ValidationError("baseline already exists or cannot be atomically published") from exc
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def load_baseline(path: Path) -> ValidationBaseline:
    try:
        info = Path(path).lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise T810ValidationError("baseline must be a non-symlink regular file")
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise T810ValidationError("baseline cannot be read") from exc
    return baseline_from_dict(_parse_json_no_duplicates(raw, "baseline"))


def validate_t810(
    *,
    preregistration: VerifiedT810Preregistration,
    repo_root: Path,
    approved_git_identity: GitIdentity,
    writable_root: Path,
    manifest_path: Path,
    manifest_root: Path,
    expected_manifest_sha256: str,
    executable: Path,
    expected_executable_sha256: str,
    attempt_root: Path,
    attempt_receipt: Mapping[str, Any] | None,
    claimed_state: str,
    previous_baseline: ValidationBaseline | None = None,
    canonical_forbidden_roots: Mapping[str, Path] | None = None,
    mountinfo_text: str | None = None,
) -> Slice1ValidationResult:
    """pre/post 共通の検査関数。mode を受け取らず、常に全 5 検査を行う。"""

    if not isinstance(preregistration, VerifiedT810Preregistration):
        raise T810ValidationError("verified preregistration is required")
    if preregistration.run_authorized:
        raise T810ValidationError("dormant seal is not closed")
    findings: list[Finding] = []
    repo = Path(repo_root).resolve(strict=True)
    writable = make_t810_durable_root(writable_root, repo, mountinfo_text=mountinfo_text).path
    repository = inspect_repository(repo, approved_git_identity)
    verify_frozen_manifest(
        manifest_path, manifest_root, expected_sha256=expected_manifest_sha256
    )

    roots = canonical_forbidden_roots or {
        "FORBIDDEN_OUTPUT": repo / "output",
        "FORBIDDEN_ENV_CONTRACT": repo / "orchestrator" / "campaign" / "env_contract.py",
        "FORBIDDEN_ENV_CONTRACT_ACTIVATIONS": repo / "orchestrator" / "campaign" / "env_contract_activations",
    }
    if set(roots) != FORBIDDEN_REGION_CODES:
        raise T810ValidationError("canonical forbidden roots must contain the exact three regions")
    forbidden: list[tuple[str, TreeInventory]] = []
    for code, raw_root in roots.items():
        path = Path(raw_root).absolute()
        if path.is_file() and not path.is_symlink():
            parent_inventory = scan_tree(path.parent)
            records = tuple(record for record in parent_inventory.records if record.path == path.name)
            inventory = TreeInventory(str(path), "present", records)
        else:
            inventory = scan_tree(path)
        forbidden.append((code, inventory))
        try:
            outside = not path.resolve(strict=False).is_relative_to(repo)
        except OSError:
            outside = True
        if outside:
            findings.append(Finding(code + "_OUTSIDE_CHECKOUT", str(path), blocking=False))

    calibration = _calibration_inventories(repo, writable)
    complete, _, started, _, receipt_findings, slots = _receipt_evidence(
        attempt_receipt,
        int(preregistration.projection["design"]["selected"]["node_count"]),
    )
    del complete
    findings.extend(receipt_findings)
    findings.extend(
        _verify_executable_and_argv(
            preregistration, Path(executable), expected_executable_sha256, slots
        )
    )
    provisional_state = classify_terminal_state(
        attempt_receipt,
        expected_slots=int(preregistration.projection["design"]["selected"]["node_count"]),
        claimed_state=claimed_state,
        post_validation_passed=True,
    )
    try:
        layout = expected_attempt_layout(
            preregistration, provisional_state, started_slots=started
        )
        findings.extend(_verify_attempt_layout(Path(attempt_root), layout))
    except T810ValidationError as exc:
        findings.append(Finding("ATTEMPT_LAYOUT_INVALID", str(exc)))

    current = ValidationBaseline(repository, tuple(forbidden), calibration)
    if previous_baseline is not None:
        if repository != previous_baseline.repository:
            findings.append(Finding("REPOSITORY_CHURN", "repository snapshot differs from baseline"))
        previous_forbidden = dict(previous_baseline.forbidden_regions)
        for code, inventory in forbidden:
            if previous_forbidden.get(code) != inventory:
                outside = any(item.code == code + "_OUTSIDE_CHECKOUT" for item in findings)
                findings.append(Finding(code + "_CHURN", inventory.root, blocking=not outside))
        if calibration != previous_baseline.calibration:
            findings.append(Finding("CALIBRATION_NAMESPACE_CHURN", "calibration inventory changed"))

    blocking = any(finding.blocking for finding in findings)
    terminal_state = classify_terminal_state(
        attempt_receipt,
        expected_slots=int(preregistration.projection["design"]["selected"]["node_count"]),
        claimed_state=claimed_state,
        post_validation_passed=not blocking,
    )
    return Slice1ValidationResult(
        ok=not blocking,
        terminal_state=terminal_state,
        baseline_digest=baseline_digest(current),
        baseline=current,
        findings=tuple(findings),
    )


def write_pass_witness_create_only(
    path: Path,
    *,
    result: Slice1ValidationResult,
    attempt_nonce: str,
    invocation_nonce: str,
) -> tuple[int, int, bytes]:
    """同一 directory 内の hard-link publish で create-only + atomic に封印する。"""

    if not result.ok:
        raise T810ValidationError("cannot write a pass witness for a failed validation")
    if not attempt_nonce or not invocation_nonce:
        raise T810ValidationError("attempt and invocation nonce are required")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "attempt_nonce": attempt_nonce,
        "baseline_digest": result.baseline_digest,
        "invocation_nonce": invocation_nonce,
        "schema_version": PASS_RECEIPT_SCHEMA,
    }
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    temp = target.parent / ("." + target.name + "." + invocation_nonce + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(temp, flags, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.link(temp, target, follow_symlinks=False)
        directory_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        info = target.stat(follow_symlinks=False)
        return info.st_dev, info.st_ino, raw
    except OSError as exc:
        raise T810ValidationError("pass witness already exists or cannot be atomically published") from exc
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def consume_current_pass_witness(
    path: Path,
    *,
    process_returncode: int,
    invocation_nonce: str,
    created_identity: tuple[int, int, bytes],
) -> Mapping[str, Any]:
    if process_returncode != 0:
        raise T810ValidationError("current validator process did not return zero")
    dev, inode, expected_raw = created_identity
    try:
        info = Path(path).stat(follow_symlinks=False)
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise T810ValidationError("current pass witness is unreadable") from exc
    if (info.st_dev, info.st_ino) != (dev, inode) or raw != expected_raw:
        raise T810ValidationError("pass witness was not created by this invocation")
    value = _parse_json_no_duplicates(raw, "pass witness")
    if value.get("invocation_nonce") != invocation_nonce:
        raise T810ValidationError("pass witness invocation nonce mismatch")
    return value
