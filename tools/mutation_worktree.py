#!/usr/bin/env python3
"""固定 commit の使い捨て worktree 内で mutation harness を走らせる。

この wrapper が主張するのは、source/main 共有木の二つの観測点で status と
submodule-status の stdout bytes が不変であることだけである。物理ノード死、client
eviction、storage 障害後の物理永続性は主張しない。
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if os.fspath(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_REPO_ROOT))

from orchestrator.campaign import mutation_attempt_marker, site_policy  # noqa: E402


WRAPPER_RECEIPT_SCHEMA = "izanagi-mutation-worktree-wrapper/v1"
HARNESS_LEDGER_SCHEMA = "izanagi-dev-wave-mutation/v4"
MUTATION_SPEC_SCHEMA = "izanagi-dev-wave-mutation-spec/v1"
CONTAINER_NAME = ".izanagi-mutation-worktree"
CHECKOUT_NAME = "repo"
TERMINAL_MUTATION_STATUSES = frozenset(
    {"KILLED", "SURVIVED", "MISMATCH", "TIMEOUT"}
)
WRAPPER_FAILURE_RC = 125
_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_GIT_ENV_ALLOWLIST = frozenset({"GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"})
_STATUS_ARGS = (
    "status",
    "--porcelain=v1",
    "--untracked-files=all",
    "--ignore-submodules=none",
)


class MutationWorktreeError(RuntimeError):
    """wrapper の安全条件を証明できないときの fail-closed 停止。"""


class SignalAbort(BaseException):
    """受信 signal と child 終了値を上位の終了コード選択へ運ぶ。"""

    def __init__(self, signum: int, child_rc: int | None = None) -> None:
        self.signum = signum
        self.child_rc = child_rc
        super().__init__(f"signal {signum}")


class TeardownError(MutationWorktreeError):
    """teardown の部分成功を receipt state へ運ぶ。"""

    def __init__(self, message: str, *, evidence_relocated: bool) -> None:
        self.evidence_relocated = evidence_relocated
        super().__init__(message)


@dataclasses.dataclass(frozen=True)
class SharedObservation:
    """共有木の status/submodule-status stdout bytes 比較用 snapshot。"""

    roots: tuple[Path, ...]
    payloads: tuple[tuple[bytes, bytes], ...]


@dataclasses.dataclass(frozen=True)
class Preflight:
    """provision 前に固定した path と identity。"""

    source: Path
    commit: str
    scratch: Path
    container: Path
    checkout: Path
    spec: Path
    out: Path
    attempt: Path | None
    receipt: Path
    evidence: Path
    lock_path: Path
    registered_worktrees: tuple[Path, ...]
    shared_before: SharedObservation


@dataclasses.dataclass(frozen=True)
class AdminBinding:
    """生成 worktree とその単一 admin directory の相互束縛。"""

    common_dir: Path
    admin_dir: Path
    checkout_dotgit: Path
    backpointer: bytes


@dataclasses.dataclass
class RunState:
    """receipt と fail-closed 終了判定に必要な invocation state。"""

    preflight: Preflight | None = None
    admin: AdminBinding | None = None
    child_rc: int | None = None
    shared_snapshot_matches: bool | None = None
    evidence_relocated: bool = False
    evidence_rehydrated: bool = False
    terminal_ledger: bool = False
    teardown_attempted: bool = False
    teardown_completed: bool = False
    container_preserved: bool = False
    failure: str | None = None


@dataclasses.dataclass
class SignalState:
    """invocation 全域の signal と active child を保持する。"""

    signum: int | None = None
    process: subprocess.Popen[Any] | None = None


def _git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") or key in _GIT_ENV_ALLOWLIST
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(
    repo: Path, *args: str, text: bool = False
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        check=False,
        shell=False,
    )


def _git_checked(
    repo: Path, *args: str, label: str, text: bool = False
) -> subprocess.CompletedProcess[Any]:
    result = _git(repo, *args, text=text)
    if result.returncode != 0:
        stderr = result.stderr if text else result.stderr.decode("utf-8", "replace")
        raise MutationWorktreeError(
            f"{label} に失敗 (git rc={result.returncode}): {stderr.strip()}"
        )
    return result


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _absolute_output_path(path: Path) -> Path:
    if path.is_symlink():
        raise MutationWorktreeError("--out に symlink を指定してはならない")
    try:
        return path.resolve(strict=False)
    except OSError as exc:
        raise MutationWorktreeError(f"--out の絶対 path を解決できない: {exc}") from exc


def _lock_path_for_out(out: Path) -> Path:
    return Path(f"{out}.lock")


@contextlib.contextmanager
def _out_lock(out: Path) -> Iterator[Path]:
    """同じ絶対 --out の producer を scratch root に依らず一つにする。"""

    lock_path = _lock_path_for_out(out)
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_RDWR | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError as exc:
        raise MutationWorktreeError(f"wrapper lock を安全に開けない: {exc}") from exc
    stream = os.fdopen(descriptor, "a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise MutationWorktreeError(
                f"同じ --out の mutation wrapper が走行中: {out}"
            ) from exc
        yield lock_path
    finally:
        stream.close()


def _registered_worktrees(source: Path) -> tuple[Path, ...]:
    result = _git_checked(
        source,
        "worktree",
        "list",
        "--porcelain",
        label="registered worktree 一覧の取得",
    )
    roots: list[Path] = []
    for line in result.stdout.splitlines():
        if not line.startswith(b"worktree "):
            continue
        raw = os.fsdecode(line[len(b"worktree ") :])
        try:
            root = Path(raw).resolve(strict=False)
        except OSError as exc:
            raise MutationWorktreeError(
                f"registered worktree path を解決できない: {raw!r}: {exc}"
            ) from exc
        roots.append(root)
    if not roots or source not in roots:
        raise MutationWorktreeError("source を含む registered worktree 一覧を取得できない")
    return tuple(dict.fromkeys(roots))


def _resolve_source_and_commit(source_arg: Path, revision: str | None) -> tuple[Path, str]:
    try:
        source = source_arg.resolve(strict=True)
    except OSError as exc:
        raise MutationWorktreeError(f"--source-repo を解決できない: {exc}") from exc
    if not source.is_dir():
        raise MutationWorktreeError("--source-repo は directory でなければならない")
    inside = _git_checked(
        source, "rev-parse", "--is-inside-work-tree", label="source worktree 検査"
    )
    if inside.stdout.strip() != b"true":
        raise MutationWorktreeError("--source-repo は git worktree でなければならない")
    top = _git_checked(
        source, "rev-parse", "--show-toplevel", label="source root 検査", text=True
    )
    try:
        top_path = Path(top.stdout.strip()).resolve(strict=True)
    except OSError as exc:
        raise MutationWorktreeError(f"source root を解決できない: {exc}") from exc
    if top_path != source:
        raise MutationWorktreeError(
            "--source-repo は git worktree root そのものを指定する必要がある"
        )
    selected = "HEAD" if revision is None else revision
    commit_result = _git_checked(
        source,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{selected}^{{commit}}",
        label="commit 解決",
        text=True,
    )
    commit = commit_result.stdout.strip()
    if _SHA_RE.fullmatch(commit) is None:
        raise MutationWorktreeError("解決 commit が full lowercase object id でない")
    return source, commit


def _validate_scratch(path: Path, registered: Sequence[Path]) -> Path:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise MutationWorktreeError(f"--scratch-root を検査できない: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise MutationWorktreeError("--scratch-root は symlink であってはならない")
    try:
        scratch = path.resolve(strict=True)
    except OSError as exc:
        raise MutationWorktreeError(f"--scratch-root を解決できない: {exc}") from exc
    if not scratch.is_dir():
        raise MutationWorktreeError("--scratch-root は既存 directory でなければならない")
    if any(_path_within(scratch, root) for root in registered):
        raise MutationWorktreeError(
            "--scratch-root は全 registered worktree の外でなければならない"
        )
    if not os.access(scratch, os.W_OK | os.X_OK):
        raise MutationWorktreeError("--scratch-root に write/search 権限がない")
    return scratch


def _validate_artifact_locations(
    *,
    spec_arg: Path,
    out_arg: Path,
    registered: Sequence[Path],
    container: Path,
    attempt_arg: Path | None = None,
) -> tuple[Path, Path, Path | None, Path, Path, Path]:
    if spec_arg.is_symlink():
        raise MutationWorktreeError("--spec に symlink を指定してはならない")
    try:
        spec = spec_arg.resolve(strict=True)
    except OSError as exc:
        raise MutationWorktreeError(f"--spec を解決できない: {exc}") from exc
    if not spec.is_file():
        raise MutationWorktreeError("--spec は通常 file でなければならない")
    out = _absolute_output_path(out_arg)
    if attempt_arg is not None and attempt_arg.is_symlink():
        raise MutationWorktreeError("--attempt-out に symlink を指定してはならない")
    attempt = attempt_arg.resolve(strict=False) if attempt_arg is not None else None
    receipt = Path(f"{out}.wrapper-receipt.json")
    evidence = Path(f"{out}.dispatch-evidence")
    lock_path = _lock_path_for_out(out)
    candidates = [
        ("--spec", spec),
        ("--out", out),
        ("wrapper receipt", receipt),
        ("dispatch evidence", evidence),
        ("wrapper lock", lock_path),
    ]
    if attempt is not None:
        candidates.append(("--attempt-out", attempt))
    forbidden = (*registered, container)
    for label, candidate in candidates:
        if any(_path_within(candidate, root) for root in forbidden):
            raise MutationWorktreeError(
                f"{label} は registered/generated worktree の外でなければならない"
            )
    derived = {receipt, evidence, lock_path}
    explicit = {spec, out} | ({attempt} if attempt is not None else set())
    if len(explicit) != 2 + int(attempt is not None) or explicit & derived:
        raise MutationWorktreeError("spec/out/attempt と wrapper 派生 artifact が衝突する")
    return spec, out, attempt, receipt, evidence, lock_path


def _primary_and_source_roots(
    source: Path, registered: Sequence[Path]
) -> tuple[Path, ...]:
    common_result = _git_checked(
        source,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
        label="common git-dir 取得",
        text=True,
    )
    try:
        common = Path(common_result.stdout.strip()).resolve(strict=True)
    except OSError as exc:
        raise MutationWorktreeError(f"common git-dir を解決できない: {exc}") from exc
    primary = common.parent
    if primary not in registered:
        raise MutationWorktreeError("primary worktree を registered 一覧へ束縛できない")
    return tuple(dict.fromkeys((primary, source)))


def _observe_shared(roots: Sequence[Path]) -> SharedObservation:
    payloads: list[tuple[bytes, bytes]] = []
    for root in roots:
        status_result = _git_checked(root, *_STATUS_ARGS, label=f"{root} status snapshot")
        submodule_result = _git_checked(
            root,
            "submodule",
            "status",
            "--recursive",
            label=f"{root} submodule snapshot",
        )
        payloads.append((status_result.stdout, submodule_result.stdout))
    return SharedObservation(tuple(roots), tuple(payloads))


def _compare_shared_snapshots(before: SharedObservation) -> bool:
    return _observe_shared(before.roots).payloads == before.payloads


def _assert_shared_unchanged(before: SharedObservation) -> None:
    if not _compare_shared_snapshots(before):
        raise MutationWorktreeError("source/main 共有木の観測 bytes が変化した")


def _preflight(
    args: argparse.Namespace,
    *,
    source: Path,
    commit: str,
    out: Path,
    lock_path: Path,
) -> Preflight:
    registered = _registered_worktrees(source)
    scratch = _validate_scratch(args.scratch_root, registered)
    container = scratch / CONTAINER_NAME
    checkout = container / CHECKOUT_NAME
    spec, validated_out, attempt, receipt, evidence, derived_lock_path = (
        _validate_artifact_locations(
            spec_arg=args.spec,
            out_arg=args.out,
            attempt_arg=args.attempt_out,
            registered=registered,
            container=container,
        )
    )
    if validated_out != out:
        raise MutationWorktreeError("--out の lock identity と preflight identity が不一致")
    if derived_lock_path != lock_path:
        raise MutationWorktreeError("--out の派生 lock path が preflight と不一致")
    if args.runner_mode == "dispatch":
        if not args.resume and (evidence.exists() or evidence.is_symlink()):
            raise MutationWorktreeError(
                f"fresh dispatch の evidence 退避先が既に存在する: {evidence}"
            )
    roots = _primary_and_source_roots(source, registered)
    shared_before = _observe_shared(roots)
    return Preflight(
        source=source,
        commit=commit,
        scratch=scratch,
        container=container,
        checkout=checkout,
        spec=spec,
        out=out,
        attempt=attempt,
        receipt=receipt,
        evidence=evidence,
        lock_path=lock_path,
        registered_worktrees=registered,
        shared_before=shared_before,
    )


def _claim_fresh_container(preflight: Preflight) -> None:
    """fresh invocation の container を単一 atomic gate で所有する。"""

    try:
        preflight.container.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        print(
            f"既存 container は自動削除しません: {preflight.container}; "
            "保持中 run の evidence と scheduler 状態を確認し、resume または手動処置してください",
            file=sys.stderr,
            flush=True,
        )
        raise MutationWorktreeError(
            f"container が既に存在するため所有を拒否: {preflight.container}"
        ) from exc
    except OSError as exc:
        raise MutationWorktreeError(f"container を原子的に所有できない: {exc}") from exc


def _validate_resume_container(preflight: Preflight) -> AdminBinding:
    """保持済み container を commit/porcelain に再束縛してから再利用する。"""

    try:
        metadata = preflight.container.lstat()
    except OSError as exc:
        raise MutationWorktreeError(
            f"--resume の既存 container を検査できない: {exc}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise MutationWorktreeError("--resume container が symlink でない directory でない")
    binding = _admin_binding(preflight)
    _verify_provisioned(preflight)
    return binding


def _resume_container_exists(preflight: Preflight) -> bool:
    try:
        preflight.container.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise MutationWorktreeError(
            f"--resume の container existence を検査できない: {exc}"
        ) from exc
    return True


def _admin_binding(preflight: Preflight) -> AdminBinding:
    common_result = _git_checked(
        preflight.source,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
        label="common git-dir 取得",
        text=True,
    )
    admin_result = _git_checked(
        preflight.checkout,
        "rev-parse",
        "--absolute-git-dir",
        label="生成 worktree admin dir 取得",
        text=True,
    )
    try:
        common = Path(common_result.stdout.strip()).resolve(strict=True)
        admin = Path(admin_result.stdout.strip()).resolve(strict=True)
    except OSError as exc:
        raise MutationWorktreeError(f"admin/common dir を解決できない: {exc}") from exc
    expected_parent = common / "worktrees"
    if admin.parent != expected_parent or admin == expected_parent:
        raise MutationWorktreeError("生成 admin dir が <common>/worktrees の直接 child でない")
    checkout_dotgit = preflight.checkout / ".git"
    backpointer_path = admin / "gitdir"
    try:
        if backpointer_path.is_symlink() or not backpointer_path.is_file():
            raise MutationWorktreeError("生成 admin の gitdir が通常 file でない")
        backpointer = backpointer_path.read_bytes()
    except MutationWorktreeError:
        raise
    except OSError as exc:
        raise MutationWorktreeError(f"生成 admin の gitdir を読めない: {exc}") from exc
    expected = os.fsencode(checkout_dotgit) + b"\n"
    if backpointer != expected:
        raise MutationWorktreeError("生成 admin の gitdir が自 checkout を指していない")
    return AdminBinding(common, admin, checkout_dotgit, backpointer)


def _worktree_add(preflight: Preflight) -> AdminBinding:
    result = _git(
        preflight.source,
        "-c",
        "core.hooksPath=",
        "worktree",
        "add",
        "--detach",
        str(preflight.checkout),
        preflight.commit,
    )
    if result.returncode != 0:
        raise MutationWorktreeError(
            "git worktree add --detach に失敗: "
            + result.stderr.decode("utf-8", "replace").strip()
        )
    return _admin_binding(preflight)


def _verify_provisioned(preflight: Preflight) -> None:
    head = _git_checked(
        preflight.checkout,
        "rev-parse",
        "--verify",
        "HEAD",
        label="生成 HEAD 再検査",
        text=True,
    ).stdout.strip()
    if head != preflight.commit:
        raise MutationWorktreeError(
            f"生成 HEAD が要求 commit と不一致: expected={preflight.commit}, actual={head}"
        )
    status_result = _git_checked(
        preflight.checkout, *_STATUS_ARGS, label="生成 tree cleanliness 再検査"
    )
    if status_result.stdout:
        raise MutationWorktreeError("生成 worktree の porcelain が空でない")
    submodule = _git_checked(
        preflight.checkout,
        "submodule",
        "status",
        "--",
        "external/ccbench",
        label="生成 submodule 再検査",
    ).stdout
    gitlink = _git_checked(
        preflight.checkout,
        "ls-tree",
        "HEAD",
        "--",
        "external/ccbench",
        label="gitlink pin 取得",
        text=True,
    ).stdout.strip().split()
    marker = preflight.checkout / "external" / "ccbench" / ".git"
    if (
        not submodule.startswith(b" ")
        or len(submodule.split()) < 1
        or len(gitlink) < 3
        or submodule.split()[0].decode("ascii", "replace") != gitlink[2]
        or marker.is_symlink()
        or not marker.exists()
    ):
        raise MutationWorktreeError("external/ccbench が初期化済み gitlink pin と一致しない")


def _materialize_and_verify(preflight: Preflight) -> None:
    result = _git(
        preflight.checkout,
        "-c",
        "core.hooksPath=",
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "update",
        "--init",
        "--no-fetch",
        "--",
        "external/ccbench",
    )
    if result.returncode != 0:
        raise MutationWorktreeError(
            "submodule update --init --no-fetch に失敗: "
            + result.stderr.decode("utf-8", "replace").strip()
        )
    _verify_provisioned(preflight)


def _dispatch_root(preflight: Preflight) -> Path:
    return preflight.checkout / "output" / "pegasus-dispatch"


def _path_present_fail_closed(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _orphan_hold_present(preflight: Preflight) -> bool:
    """container 内 hold または外部 sidecar を保全側へ写像する。"""

    control_root = _dispatch_root(preflight)
    hold = control_root / "orphan-hold.json"
    sidecar = Path(f"{preflight.out}.orphan-stop.json")
    if _path_present_fail_closed(hold) or _path_present_fail_closed(sidecar):
        return True

    ledger = control_root / "orphan-holds"
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        return True
    try:
        descriptor = os.open(
            ledger,
            os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0),
        )
    except FileNotFoundError:
        return False
    except OSError:
        return True
    blocker = False
    try:
        with os.scandir(descriptor) as entries:
            blocker = any(entry.name.endswith(".json") for entry in entries)
    except OSError:
        blocker = True
    try:
        os.close(descriptor)
    except OSError:
        blocker = True
    return blocker


def _rehydrate_dispatch_evidence(preflight: Preflight) -> bool:
    source = preflight.evidence
    destination = _dispatch_root(preflight)
    source_exists = source.exists() or source.is_symlink()
    destination_exists = destination.exists() or destination.is_symlink()
    if source_exists and destination_exists:
        raise MutationWorktreeError("dispatch evidence が退避先と container の双方に存在する")
    if destination_exists:
        if destination.is_symlink() or not destination.is_dir():
            raise MutationWorktreeError("container 内 dispatch evidence が通常 directory でない")
        return False
    if source.is_symlink() or not source.is_dir():
        raise MutationWorktreeError("退避 dispatch evidence が通常 directory でない")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.rename(destination)
    except OSError as exc:
        raise MutationWorktreeError(f"dispatch evidence を再実体化できない: {exc}") from exc
    return True


def _stash_dispatch_evidence(preflight: Preflight, *, required: bool) -> bool:
    source = _dispatch_root(preflight)
    destination = preflight.evidence
    if not source.exists():
        if required:
            raise MutationWorktreeError("退避すべき dispatch evidence が生成されていない")
        return False
    if source.is_symlink() or not source.is_dir():
        raise MutationWorktreeError("生成 dispatch evidence が通常 directory でない")
    if destination.exists() or destination.is_symlink():
        raise MutationWorktreeError("dispatch evidence 退避先が既に存在する")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.rename(destination)
    except OSError as exc:
        raise MutationWorktreeError(f"dispatch evidence を rename 退避できない: {exc}") from exc
    return True


def _harness_argv(preflight: Preflight, args: argparse.Namespace) -> list[str]:
    argv = [
        sys.executable,
        str(preflight.checkout / "tools" / "mutation_harness.py"),
        "--repo",
        str(preflight.checkout),
        "--spec",
        str(preflight.spec),
        "--expected-spec-sha256",
        args.expected_spec_sha256,
        "--out",
        str(preflight.out),
        "--runner-mode",
        args.runner_mode,
    ]
    if args.resume:
        argv.append("--resume")
    if args.detached:
        argv.append("--detached")
    if args.plan_only:
        argv.append("--plan-only")
    if preflight.attempt is not None:
        argv.extend(
            [
                "--attempt-out",
                str(preflight.attempt),
                "--wrapper-attempt",
                str(args.wrapper_attempt),
            ]
        )
    argv.extend(["--", *args.command])
    return argv


def _child_env() -> dict[str, str]:
    env = _git_env()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _forward_signal(process: subprocess.Popen[Any], signum: int) -> None:
    try:
        if process.poll() is None:
            os.killpg(process.pid, signum)
    except OSError:
        pass


def _stop_after_signal(process: subprocess.Popen[Any]) -> int | None:
    try:
        return process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            return process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            return process.poll()


@contextlib.contextmanager
def _signal_scope() -> Iterator[SignalState]:
    """container 所有前から teardown 後まで signal を捕捉する。"""

    state = SignalState()
    old_handlers: dict[int, Any] = {}

    def handler(signum: int, _frame: Any) -> None:
        first = state.signum is None
        if first:
            state.signum = signum
        if state.process is not None:
            _forward_signal(state.process, signum)
            if first:
                raise SignalAbort(signum)

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, handler)
        yield state
    finally:
        for signum, old_handler in old_handlers.items():
            signal.signal(signum, old_handler)


def _raise_if_signaled(state: SignalState) -> None:
    if state.signum is not None:
        raise SignalAbort(state.signum)


def _run_harness(
    preflight: Preflight, args: argparse.Namespace, signal_state: SignalState
) -> int:
    try:
        process = subprocess.Popen(
            _harness_argv(preflight, args),
            cwd=preflight.container,
            env=_child_env(),
            stdin=subprocess.DEVNULL,
            stdout=None,
            stderr=None,
            start_new_session=True,
            shell=False,
        )
    except OSError as exc:
        raise MutationWorktreeError(f"mutation harness を起動できない: {exc}") from exc

    signal_state.process = process
    try:
        try:
            if signal_state.signum is not None:
                _forward_signal(process, signal_state.signum)
                raise SignalAbort(signal_state.signum)
            return int(process.wait())
        except SignalAbort as exc:
            exc.child_rc = _stop_after_signal(process)
            raise
    finally:
        signal_state.process = None


def _strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _ledger_is_terminal(preflight: Preflight, expected_spec_sha256: str) -> bool:
    out = preflight.out
    try:
        if out.is_symlink() or not out.is_file():
            return False
        ledger = json.loads(out.read_text(encoding="utf-8"))
        spec_bytes = preflight.spec.read_bytes()
        spec = json.loads(spec_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if hashlib.sha256(spec_bytes).hexdigest() != expected_spec_sha256:
        return False
    if not isinstance(spec, dict) or spec.get("schema") != MUTATION_SPEC_SCHEMA:
        return False
    spec_mutations = spec.get("mutations")
    if not isinstance(spec_mutations, list) or not spec_mutations:
        return False
    spec_ids = [
        mutation.get("id") if isinstance(mutation, dict) else None
        for mutation in spec_mutations
    ]
    if any(not isinstance(item, str) or not item for item in spec_ids):
        return False
    if len(set(spec_ids)) != len(spec_ids):
        return False
    if not isinstance(ledger, dict) or ledger.get("schema") != HARNESS_LEDGER_SCHEMA:
        return False
    if ledger.get("repo_head") != preflight.commit:
        return False
    if ledger.get("spec_sha256") != expected_spec_sha256:
        return False
    if not isinstance(ledger.get("summary"), dict):
        return False
    summary = ledger["summary"]
    mutations = ledger.get("mutations")
    baseline = ledger.get("baseline")
    if not isinstance(mutations, list) or not isinstance(baseline, dict):
        return False
    expected_count = len(spec_ids)
    integer_fields = {
        "registered",
        "recorded",
        "completed",
        "matching",
        "KILLED",
        "SURVIVED",
        "MISMATCH",
        "TIMEOUT",
        "PARSE_ERROR",
    }
    if set(summary) != integer_fields or any(
        not _strict_int(summary[field]) for field in integer_fields
    ):
        return False
    baseline_rc = baseline.get("rc")
    if (
        baseline.get("status") != "PASSED"
        or not _strict_int(baseline_rc)
        or baseline_rc != 0
    ):
        return False
    if baseline.get("failed_nodes") != []:
        return False
    if len(mutations) != expected_count:
        return False
    record_ids: list[str] = []
    status_counts = {status: 0 for status in TERMINAL_MUTATION_STATUSES}
    matching = 0
    for record in mutations:
        if not isinstance(record, dict):
            return False
        record_id = record.get("id")
        status_value = record.get("status")
        if not isinstance(record_id, str) or status_value not in status_counts:
            return False
        if not isinstance(record.get("matches_expectation"), bool):
            return False
        record_ids.append(record_id)
        status_counts[status_value] += 1
        matching += int(record["matches_expectation"])
    return (
        record_ids == spec_ids
        and summary["registered"] == expected_count
        and summary["recorded"] == expected_count
        and summary["completed"] == expected_count
        and summary["matching"] == matching
        and summary["PARSE_ERROR"] == 0
        and all(summary[status] == count for status, count in status_counts.items())
    )


def _validate_admin_for_delete(preflight: Preflight, binding: AdminBinding) -> None:
    if binding.admin_dir.parent != binding.common_dir / "worktrees":
        raise MutationWorktreeError("削除対象 admin dir が common/worktrees の直接 child でない")
    if binding.admin_dir.is_symlink() or not binding.admin_dir.is_dir():
        raise MutationWorktreeError("削除対象 admin dir が通常 directory でない")
    backpointer_path = binding.admin_dir / "gitdir"
    try:
        current = backpointer_path.read_bytes()
    except OSError as exc:
        raise MutationWorktreeError(f"削除前に admin gitdir を再読できない: {exc}") from exc
    if current != binding.backpointer or current != os.fsencode(binding.checkout_dotgit) + b"\n":
        raise MutationWorktreeError("削除前に admin gitdir の自 container 束縛が変化した")
    if not _path_within(preflight.checkout, preflight.container):
        raise MutationWorktreeError("checkout が所有 container の外へ逸脱した")


def _teardown(
    preflight: Preflight,
    binding: AdminBinding,
    *,
    runner_mode: str,
    evidence_required: bool,
) -> bool:
    """evidence → container → 自 admin の順だけで後始末する。"""

    relocated = False
    try:
        _validate_admin_for_delete(preflight, binding)
        if runner_mode == "dispatch":
            relocated = _stash_dispatch_evidence(preflight, required=evidence_required)
        shutil.rmtree(preflight.container)
    except OSError as exc:
        raise TeardownError(
            f"所有 container を再帰削除できない: {exc}",
            evidence_relocated=relocated,
        ) from exc
    except MutationWorktreeError as exc:
        raise TeardownError(str(exc), evidence_relocated=relocated) from exc
    if preflight.container.exists():
        raise TeardownError(
            "所有 container が再帰削除後も存在する",
            evidence_relocated=relocated,
        )
    try:
        shutil.rmtree(binding.admin_dir)
    except OSError as exc:
        raise TeardownError(
            f"自 admin dir を再帰削除できない: {exc}",
            evidence_relocated=relocated,
        ) from exc
    if binding.admin_dir.exists():
        raise TeardownError(
            "自 admin dir が削除後も存在する", evidence_relocated=relocated
        )
    return relocated


def _should_teardown(
    *,
    plan_only: bool,
    child_rc: int | None,
    terminal: bool,
    orphan_hold: bool,
) -> bool:
    return not orphan_hold and (plan_only or (child_rc in {0, 1} and terminal))


def _select_return_code(
    *, child_rc: int | None, signum: int | None, wrapper_failed: bool
) -> int:
    if wrapper_failed:
        return WRAPPER_FAILURE_RC
    if signum is not None:
        return 128 + signum
    return WRAPPER_FAILURE_RC if child_rc is None else child_rc


def _write_receipt(state: RunState) -> None:
    preflight = state.preflight
    if preflight is None:
        return
    try:
        wrapper = Path(__file__).resolve(strict=True)
        wrapper_sha256 = hashlib.sha256(wrapper.read_bytes()).hexdigest()
    except OSError as exc:
        raise MutationWorktreeError(f"wrapper identity を取得できない: {exc}") from exc
    document = {
        "schema": WRAPPER_RECEIPT_SCHEMA,
        "wrapper_sha256": wrapper_sha256,
        "resolved_commit": preflight.commit,
        "container_path": str(preflight.container),
        "scratch_root": str(preflight.scratch),
        "lock_path": str(preflight.lock_path),
        "child_rc": state.child_rc,
        "dispatch_evidence": {
            "original_path": str(_dispatch_root(preflight)),
            "relocated_path": str(preflight.evidence),
            "rehydrated": state.evidence_rehydrated,
            "relocated": state.evidence_relocated,
        },
        "shared_snapshot_matches": state.shared_snapshot_matches,
        "terminal_ledger": state.terminal_ledger,
        "teardown_attempted": state.teardown_attempted,
        "teardown_completed": state.teardown_completed,
        "container_preserved": state.container_preserved,
        "failure": state.failure,
    }
    try:
        preflight.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = preflight.receipt.with_name(f".{preflight.receipt.name}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, preflight.receipt)
    except OSError as exc:
        raise MutationWorktreeError(f"wrapper receipt を保存できない: {exc}") from exc


def _wrapper_resume_command(preflight: Preflight, args: argparse.Namespace) -> str:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--source-repo",
        str(preflight.source),
        "--commit",
        preflight.commit,
        "--scratch-root",
        str(preflight.scratch),
        "--spec",
        str(preflight.spec),
        "--expected-spec-sha256",
        args.expected_spec_sha256,
        "--out",
        str(preflight.out),
        "--runner-mode",
        args.runner_mode,
        "--resume",
    ]
    if args.detached:
        command.append("--detached")
    if args.plan_only:
        command.append("--plan-only")
    if preflight.attempt is not None:
        command.extend(
            [
                "--attempt-out",
                str(preflight.attempt),
                "--wrapper-attempt",
                str(args.wrapper_attempt + 1),
            ]
        )
    command.extend(["--", *args.command])
    return shlex.join(command)


def _print_preserved_resume(
    preflight: Preflight,
    args: argparse.Namespace,
    *,
    orphan_hold: bool = False,
) -> None:
    print(
        f"未完了 run の container を保持しました: {preflight.container}",
        file=sys.stderr,
        flush=True,
    )
    if orphan_hold:
        print(
            "復旧順序: qstat で対象の不在または終端を確認し、source を復元し、"
            "clean/HEAD を確認してから orphan hold と orphan-stop sidecar を"
            "手動削除してください。",
            file=sys.stderr,
            flush=True,
        )
        print(
            "次の --resume は orphan hold を解除した後にだけ有効です。",
            file=sys.stderr,
            flush=True,
        )
    print(
        "resume command: " + _wrapper_resume_command(preflight, args),
        file=sys.stderr,
        flush=True,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, default=Path.cwd())
    parser.add_argument("--commit")
    parser.add_argument("--scratch-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--expected-spec-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--attempt-out", type=Path)
    parser.add_argument("--wrapper-attempt", type=int)
    parser.add_argument("--runner-mode", required=True, choices=("local", "dispatch"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--detached", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def _refusing_local_site(runner_mode: str) -> str | None:
    if runner_mode != "local":
        return None
    site = site_policy.current_site(require_evidence=True)
    if site in {site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT}:
        return site
    return None


def main(argv: Sequence[str] | None = None) -> int:
    state = RunState()
    signum: int | None = None
    wrapper_failed = False
    args: argparse.Namespace | None = None
    try:
        args = _parser().parse_args(argv)
        if (args.attempt_out is None) is not (args.wrapper_attempt is None):
            raise MutationWorktreeError(
                "--attempt-out と --wrapper-attempt は同時指定が必要"
            )
        if args.wrapper_attempt is not None and args.wrapper_attempt < 1:
            raise MutationWorktreeError("--wrapper-attempt は 1 以上でなければならない")
        if args.attempt_out is not None and args.runner_mode == "local":
            try:
                from tools.pegasus import dispatch_compute

                mutation_attempt_marker.require_local_attempt_marker(
                    normalize_request_id=dispatch_compute._normalize_request_id,
                    is_regular_pbs_jobid=dispatch_compute._is_regular_pbs_jobid,
                )
            except mutation_attempt_marker.MutationAttemptMarkerError as exc:
                raise MutationWorktreeError(
                    f"local attempt authorization が不正です: {exc}"
                ) from exc
        command = list(args.command)
        if command and command[0] == "--":
            command.pop(0)
        if not command:
            raise MutationWorktreeError("runner argv を -- の後へ指定する必要がある")
        args.command = command
        if not args.plan_only and not args.detached:
            raise MutationWorktreeError("実走には --detached が必要")

        out = _absolute_output_path(args.out)
        with _signal_scope() as signal_state:
            try:
                _raise_if_signaled(signal_state)
                source, commit = _resolve_source_and_commit(
                    args.source_repo, args.commit
                )
                refusing_site = _refusing_local_site(args.runner_mode)
                if refusing_site is not None:
                    print(
                        "mutation worktree aborted: --runner-mode local は "
                        f"{refusing_site} で実行できない",
                        file=sys.stderr,
                        flush=True,
                    )
                    return 2
                expected_lock_path = _lock_path_for_out(out)
                state.preflight = _preflight(
                    args,
                    source=source,
                    commit=commit,
                    out=out,
                    lock_path=expected_lock_path,
                )
                preflight = state.preflight
                _raise_if_signaled(signal_state)
                with _out_lock(out) as lock_path:
                    try:
                        if lock_path != expected_lock_path:
                            raise MutationWorktreeError(
                                "取得 lock path が preflight identity と不一致"
                            )
                        _raise_if_signaled(signal_state)
                        if args.resume and _resume_container_exists(preflight):
                            state.admin = _validate_resume_container(preflight)
                        else:
                            _claim_fresh_container(preflight)
                            state.admin = _worktree_add(preflight)
                            _raise_if_signaled(signal_state)
                            _materialize_and_verify(preflight)
                        _raise_if_signaled(signal_state)
                        if args.runner_mode == "dispatch" and args.resume:
                            state.evidence_rehydrated = _rehydrate_dispatch_evidence(
                                preflight
                            )
                        _raise_if_signaled(signal_state)
                        state.child_rc = _run_harness(preflight, args, signal_state)
                        _raise_if_signaled(signal_state)
                        state.terminal_ledger = (
                            False
                            if args.plan_only
                            else _ledger_is_terminal(
                                preflight, args.expected_spec_sha256
                            )
                        )
                        terminal_failure = (
                            not args.plan_only
                            and state.child_rc in {0, 1}
                            and not state.terminal_ledger
                        )
                        if terminal_failure:
                            wrapper_failed = True
                            state.failure = (
                                "child は完走 rc を返したが terminal ledger を検証できない"
                            )
                        orphan_hold = (
                            args.runner_mode == "dispatch"
                            and _orphan_hold_present(preflight)
                        )
                        if orphan_hold:
                            wrapper_failed = True
                            state.failure = "orphan-hold"
                        if _should_teardown(
                            plan_only=args.plan_only,
                            child_rc=state.child_rc,
                            terminal=state.terminal_ledger,
                            orphan_hold=orphan_hold,
                        ):
                            state.teardown_attempted = True
                            state.evidence_relocated = _teardown(
                                preflight,
                                state.admin,
                                runner_mode=args.runner_mode,
                                evidence_required=(
                                    args.runner_mode == "dispatch"
                                    and (args.resume or not args.plan_only)
                                ),
                            )
                            state.teardown_completed = True
                            _raise_if_signaled(signal_state)
                        else:
                            state.container_preserved = True
                            if orphan_hold:
                                print(
                                    "mutation worktree aborted: orphan-hold; "
                                    f"container と source を保全しました: {preflight.container}",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            elif terminal_failure:
                                print(
                                    f"mutation worktree aborted: {state.failure}",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            _print_preserved_resume(
                                preflight, args, orphan_hold=orphan_hold
                            )
                    except SignalAbort as exc:
                        signum = exc.signum
                        if exc.child_rc is not None:
                            state.child_rc = exc.child_rc
                        state.container_preserved = (
                            state.preflight is not None
                            and state.preflight.container.exists()
                        )
                        if state.container_preserved and state.preflight is not None:
                            signal_orphan_hold = (
                                args.runner_mode == "dispatch"
                                and _orphan_hold_present(state.preflight)
                            )
                            _print_preserved_resume(
                                state.preflight,
                                args,
                                orphan_hold=signal_orphan_hold,
                            )
                    except Exception as exc:
                        wrapper_failed = True
                        if isinstance(exc, TeardownError):
                            state.evidence_relocated = exc.evidence_relocated
                        state.failure = str(exc)
                        fallback_orphan_hold = (
                            args.runner_mode == "dispatch"
                            and state.preflight is not None
                            and _orphan_hold_present(state.preflight)
                        )
                        if fallback_orphan_hold:
                            state.failure = "orphan-hold"
                        if (
                            args.plan_only
                            and state.preflight is not None
                            and state.admin is not None
                            and state.preflight.container.exists()
                            and not state.teardown_attempted
                            and not fallback_orphan_hold
                        ):
                            state.teardown_attempted = True
                            try:
                                state.evidence_relocated = _teardown(
                                    state.preflight,
                                    state.admin,
                                    runner_mode=args.runner_mode,
                                    evidence_required=state.evidence_rehydrated,
                                )
                                state.teardown_completed = True
                            except TeardownError as teardown_exc:
                                state.evidence_relocated = (
                                    state.evidence_relocated
                                    or teardown_exc.evidence_relocated
                                )
                                state.failure = (
                                    f"{state.failure}; plan-only teardown: {teardown_exc}"
                                )
                            except Exception as teardown_exc:
                                state.failure = (
                                    f"{state.failure}; plan-only teardown: {teardown_exc}"
                                )
                        state.container_preserved = (
                            state.preflight is not None
                            and state.preflight.container.exists()
                        )
                        print(
                            f"mutation worktree aborted: {exc}",
                            file=sys.stderr,
                            flush=True,
                        )
                        if state.container_preserved and state.preflight is not None:
                            _print_preserved_resume(
                                state.preflight,
                                args,
                                orphan_hold=fallback_orphan_hold,
                            )
                    finally:
                        if state.preflight is not None:
                            try:
                                _assert_shared_unchanged(
                                    state.preflight.shared_before
                                )
                                state.shared_snapshot_matches = True
                            except Exception as exc:
                                wrapper_failed = True
                                state.shared_snapshot_matches = False
                                message = f"共有木の事後検査に失敗: {exc}"
                                state.failure = (
                                    message
                                    if state.failure is None
                                    else f"{state.failure}; {message}"
                                )
                                print(
                                    f"mutation worktree aborted: {message}",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            try:
                                _write_receipt(state)
                            except Exception as exc:
                                wrapper_failed = True
                                state.failure = str(exc)
                                print(
                                    f"mutation worktree aborted: {exc}",
                                    file=sys.stderr,
                                    flush=True,
                                )
                signum = signal_state.signum if signum is None else signum
            except SignalAbort as exc:
                signum = exc.signum
    except SignalAbort as exc:
        signum = exc.signum
    except Exception as exc:
        wrapper_failed = True
        state.failure = str(exc)
        print(f"mutation worktree aborted: {exc}", file=sys.stderr, flush=True)
    return _select_return_code(
        child_rc=state.child_rc, signum=signum, wrapper_failed=wrapper_failed
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MutationWorktreeError as exc:
        print(f"mutation worktree aborted: {exc}", file=sys.stderr)
        raise SystemExit(WRAPPER_FAILURE_RC)
