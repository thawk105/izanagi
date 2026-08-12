#!/usr/bin/env python3
"""受入 log の赤が tested main にも存在するかを単独再走で判定する。"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence


_SCHEMA_VERSION = "izanagi-acceptance-red-check/v1"
_MAX_LOG_BYTES = 64 * 1024 * 1024
_SUMMARY_HEADER = re.compile(r"^={3,} short test summary info ={3,}$")
_SUMMARY_LINE = re.compile(r"^={3,} (?P<body>.+) ={3,}$")
_OUTCOME_LINE = re.compile(
    r"^(?P<outcome>FAILED|ERROR|PASSED|SKIPPED|XFAIL|XPASS) (?P<body>.+)$"
)
_COUNT_ITEM = re.compile(r"(?P<count>[0-9]+) (?P<kind>[A-Za-z][A-Za-z-]*)")
_DURATION = re.compile(r"[0-9]+(?:\.[0-9]+)?s(?: \([^()]+\))?")
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_SHA1 = re.compile(r"[0-9a-f]{40}")
_DISPATCH_LINE_PREFIX = "| "

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
NodeRunner = Callable[[Path, str], int]
CollectionRunner = Callable[[Path, str], Sequence[str]]
SubmoduleReceipt = tuple[Mapping[str, str], ...]


class InvalidInput(RuntimeError):
    """入力、probe、または cleanup を安全に検証できない。"""


class _TerminationSignal(BaseException):
    """catchable な終了 signal を cleanup 経路へ運ぶ。"""

    def __init__(self, signum: int) -> None:
        super().__init__(f"received signal {signum}")
        self.signum = signum


def _payload_line(line: str) -> str:
    """Pegasus relay が明示する exact ``| `` prefix だけを一度除く。"""

    if line.startswith(_DISPATCH_LINE_PREFIX):
        return line[len(_DISPATCH_LINE_PREFIX):]
    return line


def _terminal_counts(line: str) -> Mapping[str, int] | None:
    match = _SUMMARY_LINE.fullmatch(line)
    if match is None:
        return None
    body = match.group("body")
    if " in " not in body:
        return None
    count_text, duration = body.rsplit(" in ", 1)
    if _DURATION.fullmatch(duration) is None:
        return None

    counts: dict[str, int] = {}
    for item in count_text.split(", "):
        count_match = _COUNT_ITEM.fullmatch(item)
        if count_match is None:
            return None
        kind = count_match.group("kind")
        if kind in {"error", "errors"}:
            kind = "errors"
        if kind in counts:
            raise InvalidInput(f"duplicate terminal summary category: {kind}")
        counts[kind] = int(count_match.group("count"), 10)
    return counts


def _outcome_reference(body: str) -> str:
    """summary body を未推測のまま保持し、collection 対象 path だけ検証する。"""

    reference = body.strip()
    if not reference or unicodedata.normalize("NFC", reference) != reference:
        raise InvalidInput("pytest outcome reference is empty or not NFC")
    if any(unicodedata.category(character) == "Cc" for character in reference):
        raise InvalidInput(
            f"pytest outcome reference contains a control character: {reference!r}"
        )
    path_text = reference.split("::", 1)[0]
    path = PurePosixPath(path_text)
    if (
        not path_text
        or path.is_absolute()
        or path_text.startswith("-")
        or "\\" in path_text
        or ".." in path.parts
    ):
        raise InvalidInput(f"pytest nodeid is not repo-relative: {reference!r}")
    return reference


def _selector_from_collection(
    reference: str, collected_nodeids: Sequence[str],
) -> tuple[str, str]:
    """collection の最長 exact match だけを selector として採用する。"""

    matches: list[tuple[int, str, str]] = []
    for collected in set(collected_nodeids):
        suffix = reference[len(collected):] if reference.startswith(collected) else None
        if suffix is None:
            continue
        logged_nodeid = collected
        if suffix == "" or suffix.startswith(" - "):
            pass
        elif suffix.startswith("@"):
            group, separator, _detail = suffix[1:].partition(" - ")
            if (
                not group
                or "@" in group
                or any(character.isspace() for character in group)
                or any(unicodedata.category(character) == "Cc" for character in group)
            ):
                continue
            logged_nodeid = f"{collected}@{group}"
            if separator == "" and suffix != f"@{group}":
                continue
        else:
            continue
        matches.append((len(collected), collected, logged_nodeid))
    if not matches:
        raise InvalidInput(
            f"logged pytest nodeid has no exact collected selector: {reference!r}"
        )
    longest = max(length for length, _selector, _logged in matches)
    exact = {
        (selector, logged)
        for length, selector, logged in matches
        if length == longest
    }
    if len(exact) != 1:
        raise InvalidInput(
            f"logged pytest nodeid does not select exactly one collected item: {reference!r}"
        )
    return next(iter(exact))


def _validate_terminal_counts(
    candidates: Sequence[Mapping[str, int]], failed: int, errors: int,
) -> None:
    """集計行の存在・一意性・赤件数を同じ fail-closed 層で検証する。"""

    if len(candidates) != 1:
        raise InvalidInput(
            "pytest terminal summary line is missing or non-unique"
        )
    counts = candidates[0]
    if counts.get("failed", 0) != failed or counts.get("errors", 0) != errors:
        raise InvalidInput(
            "pytest terminal counts do not match FAILED/ERROR entries"
        )


def parse_pytest_log(raw: bytes) -> tuple[str, ...]:
    """pytest log を厳密に読み、赤 outcome の未推測 reference を返す。"""

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidInput(f"acceptance log is not UTF-8: {exc}") from exc
    lines = [
        _ANSI_ESCAPE.sub("", _payload_line(line)) for line in text.splitlines()
    ]
    headers = [index for index, line in enumerate(lines) if _SUMMARY_HEADER.fullmatch(line)]
    if len(headers) > 1:
        raise InvalidInput("pytest short test summary info block is non-unique")
    terminals = [
        (index, counts)
        for index, line in enumerate(lines)
        if (counts := _terminal_counts(line)) is not None
    ]
    if len(terminals) != 1:
        raise InvalidInput("pytest terminal summary line is missing or non-unique")
    terminal_index, terminal_counts = terminals[0]

    red_outcomes: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        outcome_match = _OUTCOME_LINE.fullmatch(line.lstrip())
        if outcome_match is None:
            continue
        outcome = outcome_match.group("outcome")
        if outcome not in {"FAILED", "ERROR"}:
            continue
        red_outcomes.append(
            (index, outcome, _outcome_reference(outcome_match.group("body")))
        )

    if not headers:
        _validate_terminal_counts((terminal_counts,), 0, 0)
        if red_outcomes:
            raise InvalidInput(
                "pytest red outcome exists without a short summary block"
            )
        return ()

    header_index = headers[0]
    if terminal_index <= header_index:
        raise InvalidInput("pytest terminal summary precedes the short summary block")
    outside = [
        reference
        for index, _outcome, reference in red_outcomes
        if index <= header_index or index >= terminal_index
    ]
    if outside:
        raise InvalidInput("pytest red outcome exists outside the short summary block")
    failed = sum(outcome == "FAILED" for _, outcome, _ in red_outcomes)
    errors = sum(outcome == "ERROR" for _, outcome, _ in red_outcomes)
    _validate_terminal_counts((terminal_counts,), failed, errors)
    red_nodes = [reference for _, _outcome, reference in red_outcomes]
    if len(red_nodes) != len(set(red_nodes)):
        raise InvalidInput("pytest FAILED/ERROR nodeids contain duplicates")
    return tuple(red_nodes)


def _read_log(path: Path) -> tuple[bytes, str]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise InvalidInput("O_NOFOLLOW is unavailable")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise InvalidInput(f"cannot open acceptance log: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise InvalidInput("acceptance log is not a regular file")
        if before.st_size > _MAX_LOG_BYTES:
            raise InvalidInput("acceptance log exceeds the 64 MiB size cap")
        chunks: list[bytes] = []
        remaining = _MAX_LOG_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if len(raw) > _MAX_LOG_BYTES:
            raise InvalidInput("acceptance log exceeds the 64 MiB read cap")
        if identity_before != identity_after or len(raw) != before.st_size:
            raise InvalidInput("acceptance log changed while it was read")
    except OSError as exc:
        raise InvalidInput(f"cannot read acceptance log: {exc}") from exc
    finally:
        try:
            os.close(descriptor)
        except OSError as exc:
            raise InvalidInput(f"cannot close acceptance log: {exc}") from exc
    return raw, hashlib.sha256(raw).hexdigest()


def _completed(
    command_runner: CommandRunner,
    command: Sequence[str],
    *,
    cwd: Path,
    capture_output: bool = True,
    timeout: float | None = 120.0,
    environment_overrides: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment["GIT_TERMINAL_PROMPT"] = "0"
    if environment_overrides:
        environment.update(environment_overrides)
    try:
        return command_runner(
            list(command),
            cwd=str(cwd),
            capture_output=capture_output,
            text=True,
            check=False,
            timeout=timeout,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise InvalidInput(f"command could not be completed: {type(exc).__name__}: {exc}") from exc


def _git(
    repo: Path,
    arguments: Sequence[str],
    *,
    command_runner: CommandRunner,
    environment_overrides: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return _completed(
        command_runner,
        ["git", "-C", str(repo), *arguments],
        cwd=repo,
        environment_overrides=environment_overrides,
    )


def _resolve_tested_main(
    repo: Path, tested_main: str, *, command_runner: CommandRunner,
) -> str:
    if _SHA1.fullmatch(tested_main) is None:
        raise InvalidInput("--tested-main must be a full lowercase SHA-1")
    result = _git(
        repo,
        ["rev-parse", "--verify", f"{tested_main}^{{commit}}"],
        command_runner=command_runner,
    )
    if result.returncode != 0 or result.stdout.strip() != tested_main:
        raise InvalidInput("--tested-main is not the exact local commit requested")
    main = _git(
        repo,
        ["rev-parse", "--verify", "refs/heads/main^{commit}"],
        command_runner=command_runner,
    )
    if main.returncode != 0 or main.stdout.strip() != tested_main:
        raise InvalidInput("--tested-main does not equal refs/heads/main HEAD")
    return tested_main


def _assert_wave_identity(
    repo: Path, wave_tip: str, *, command_runner: CommandRunner,
) -> None:
    if _SHA1.fullmatch(wave_tip) is None:
        raise InvalidInput("--wave-tip must be a full lowercase SHA-1")
    resolved = _git(
        repo,
        ["rev-parse", "--verify", f"{wave_tip}^{{commit}}"],
        command_runner=command_runner,
    )
    head = _git(repo, ["rev-parse", "HEAD"], command_runner=command_runner)
    if (
        resolved.returncode != 0
        or resolved.stdout.strip() != wave_tip
        or head.returncode != 0
        or head.stdout.strip() != wave_tip
    ):
        raise InvalidInput("repo HEAD does not equal --wave-tip")
    status_result = _git(
        repo,
        ["status", "--porcelain=v1", "--untracked-files=all"],
        command_runner=command_runner,
    )
    if status_result.returncode != 0 or status_result.stdout:
        raise InvalidInput("wave working tree is not clean")


def _probe_fingerprint(
    worktree: Path, *, command_runner: CommandRunner,
) -> str:
    result = _git(
        worktree,
        [
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored=matching",
            "--ignore-submodules=none",
        ],
        command_runner=command_runner,
    )
    if result.returncode != 0:
        raise InvalidInput("cannot fingerprint probe worktree")
    return hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()


def _assert_probe_identity(
    worktree: Path, tested_main: str, *, command_runner: CommandRunner,
) -> None:
    head = _git(worktree, ["rev-parse", "HEAD"], command_runner=command_runner)
    if head.returncode != 0 or head.stdout.strip() != tested_main:
        raise InvalidInput("probe worktree HEAD does not equal --tested-main")
    fingerprint = _probe_fingerprint(worktree, command_runner=command_runner)
    if fingerprint != hashlib.sha256(b"").hexdigest():
        raise InvalidInput("probe worktree is not clean, including ignored files")


def _registered_worktrees(
    repo: Path, *, command_runner: CommandRunner,
) -> set[str]:
    result = _git(repo, ["worktree", "list", "--porcelain"], command_runner=command_runner)
    if result.returncode != 0:
        raise InvalidInput("cannot verify the worktree registry after cleanup")
    return {
        os.path.realpath(line[len("worktree "):])
        for line in result.stdout.splitlines()
        if line.startswith("worktree ")
    }


def _cleanup_probe(
    repo: Path,
    parent: Path,
    worktree: Path,
    *,
    added: bool,
    command_runner: CommandRunner,
) -> None:
    failures: list[str] = []
    if added or worktree.exists():
        try:
            removed = _git(
                repo,
                ["worktree", "remove", "--force", str(worktree)],
                command_runner=command_runner,
            )
        except InvalidInput as exc:
            failures.append(f"worktree remove failed: {exc}")
        else:
            if removed.returncode != 0:
                failures.append(f"worktree remove rc={removed.returncode}")
    try:
        pruned = _git(repo, ["worktree", "prune"], command_runner=command_runner)
    except InvalidInput as exc:
        failures.append(f"worktree prune failed: {exc}")
    else:
        if pruned.returncode != 0:
            failures.append(f"worktree prune rc={pruned.returncode}")
    try:
        if os.path.realpath(worktree) in _registered_worktrees(
            repo, command_runner=command_runner
        ):
            failures.append("worktree remains registered")
    except InvalidInput as exc:
        failures.append(str(exc))
    if worktree.exists():
        failures.append("worktree directory remains")
    try:
        parent.rmdir()
    except OSError as exc:
        failures.append(f"probe parent removal failed: {exc}")
    if failures:
        raise InvalidInput("probe cleanup failed: " + "; ".join(failures))


def _default_node_runner(
    worktree: Path,
    nodeid: str,
    *,
    command_runner: CommandRunner,
) -> int:
    command = [
        sys.executable,
        str(worktree / "tools" / "run_tests.py"),
        "-p",
        "no:cacheprovider",
        nodeid,
    ]
    result = _completed(
        command_runner,
        command,
        cwd=worktree,
        capture_output=False,
        timeout=None,
        environment_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
    )
    return int(result.returncode)


def _default_collection_runner(
    worktree: Path,
    path_text: str,
    *,
    command_runner: CommandRunner,
) -> tuple[str, ...]:
    command = [
        sys.executable,
        str(worktree / "tools" / "run_tests.py"),
        "-p",
        "no:cacheprovider",
        "--collect-only",
        "-q",
        path_text,
    ]
    result = _completed(
        command_runner,
        command,
        cwd=worktree,
        environment_overrides={"PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode != 0:
        raise InvalidInput(
            f"pytest collect-only failed for logged path: {path_text!r} rc={result.returncode}"
        )
    nodeids = {
        line
        for raw_line in result.stdout.splitlines()
        if (
            (line := _payload_line(raw_line).strip()) == path_text
            or line.startswith(f"{path_text}::")
        )
    }
    if not nodeids:
        raise InvalidInput(
            f"pytest collect-only returned no machine-matchable nodeids: {path_text!r}"
        )
    return tuple(sorted(nodeids))


def _initialize_submodules_cache_only(
    worktree: Path, *, command_runner: CommandRunner,
) -> SubmoduleReceipt:
    indexed = _git(
        worktree,
        ["ls-files", "--stage", "-z"],
        command_runner=command_runner,
    )
    if indexed.returncode != 0:
        raise InvalidInput("cannot enumerate indexed submodules")

    indexed_paths: list[str] = []
    for record in indexed.stdout.split("\0"):
        if not record:
            continue
        metadata, separator, path_text = record.partition("\t")
        fields = metadata.split(" ")
        if separator != "\t" or len(fields) != 3:
            raise InvalidInput("git ls-files --stage returned malformed output")
        mode, _object_id, stage = fields
        if mode != "160000":
            continue
        path = PurePosixPath(path_text)
        if (
            not path_text
            or path.is_absolute()
            or str(path) != path_text
            or ".." in path.parts
            or unicodedata.normalize("NFC", path_text) != path_text
            or any(unicodedata.category(character) == "Cc" for character in path_text)
            or stage != "0"
        ):
            raise InvalidInput(f"indexed submodule path is invalid: {path_text!r}")
        indexed_paths.append(path_text)
    if len(indexed_paths) != len(set(indexed_paths)):
        raise InvalidInput("indexed submodule paths contain duplicates")

    configured_paths: list[str] = []
    gitmodules = worktree / ".gitmodules"
    if gitmodules.is_symlink() or (gitmodules.exists() and not gitmodules.is_file()):
        raise InvalidInput(".gitmodules is not a regular file")
    if gitmodules.is_file():
        configured = _git(
            worktree,
            [
                "config",
                "-z",
                "--file",
                ".gitmodules",
                "--get-regexp",
                r"^submodule\..*\.path$",
            ],
            command_runner=command_runner,
        )
        if configured.returncode not in {0, 1}:
            raise InvalidInput("cannot enumerate configured submodule paths")
        for record in configured.stdout.split("\0"):
            if not record:
                continue
            _key, separator, path_text = record.partition("\n")
            if separator != "\n":
                raise InvalidInput("git config returned malformed submodule path output")
            path = PurePosixPath(path_text)
            if (
                not path_text
                or path.is_absolute()
                or str(path) != path_text
                or ".." in path.parts
                or unicodedata.normalize("NFC", path_text) != path_text
                or any(unicodedata.category(character) == "Cc" for character in path_text)
            ):
                raise InvalidInput(f"configured submodule path is invalid: {path_text!r}")
            configured_paths.append(path_text)
    if len(configured_paths) != len(set(configured_paths)):
        raise InvalidInput("configured submodule paths contain duplicates")

    indexed_path_set = set(indexed_paths)
    paths = indexed_path_set | set(configured_paths)

    common_result = _git(
        worktree,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        command_runner=command_runner,
    )
    common_text = common_result.stdout.rstrip("\n")
    if (
        common_result.returncode != 0
        or not common_text
        or "\n" in common_text
        or unicodedata.normalize("NFC", common_text) != common_text
    ):
        raise InvalidInput("cannot resolve the absolute git common directory")
    common_dir = Path(common_text)
    if not common_dir.is_absolute() or not common_dir.is_dir():
        raise InvalidInput("git common directory is not an absolute directory")

    receipt: list[Mapping[str, str]] = []
    for path_text in sorted(paths):
        if path_text not in indexed_path_set:
            receipt.append(
                {"path": path_text, "status": "reference-uninitialized"}
            )
            continue
        module_dir = common_dir.joinpath("modules", *PurePosixPath(path_text).parts)
        if not module_dir.exists():
            if module_dir.is_symlink():
                raise InvalidInput(
                    f"reference submodule cache is a broken symlink: {path_text!r}"
                )
            receipt.append(
                {"path": path_text, "status": "reference-uninitialized"}
            )
            continue
        if not module_dir.is_dir():
            raise InvalidInput(
                f"reference submodule cache is not a directory: {path_text!r}"
            )
        configured = _git(
            worktree,
            ["config", f"submodule.{path_text}.url", str(module_dir)],
            command_runner=command_runner,
        )
        if configured.returncode != 0:
            raise InvalidInput(
                f"cache-only submodule URL rewrite failed with rc={configured.returncode}: "
                f"{path_text!r}"
            )
        updated = _git(
            worktree,
            ["submodule", "update", "--init", "--no-fetch", "--", path_text],
            command_runner=command_runner,
            environment_overrides={"GIT_ALLOW_PROTOCOL": "file"},
        )
        if updated.returncode != 0:
            raise InvalidInput(
                "cache-only submodule initialization failed with "
                f"rc={updated.returncode}: {path_text!r}"
            )
        receipt.append(
            {
                "path": path_text,
                "reference_module_dir": str(module_dir),
                "status": "initialized",
            }
        )
    return tuple(receipt)


def _probe_nodes(
    repo: Path,
    probe_root: Path,
    tested_main: str,
    nodeids: Sequence[str],
    *,
    node_runner: NodeRunner | None,
    collection_runner: CollectionRunner | None,
    command_runner: CommandRunner,
) -> tuple[dict[str, int], tuple[str, ...], tuple[str, ...], SubmoduleReceipt]:
    rerun_rcs: dict[str, int] = {}
    attributable: list[str] = []
    selected_runner: NodeRunner
    if node_runner is None:
        selected_runner = lambda path, node: _default_node_runner(
            path, node, command_runner=command_runner
        )
    else:
        selected_runner = node_runner
    if collection_runner is None:
        selected_collection_runner = lambda path, target: _default_collection_runner(
            path, target, command_runner=command_runner
        )
    else:
        selected_collection_runner = collection_runner
    logged_nodeids: list[str] = []
    submodule_receipt: SubmoduleReceipt | None = None
    for reference in sorted(nodeids):
        parent = Path(
            tempfile.mkdtemp(prefix="izanagi-acceptance-reds-", dir=probe_root)
        )
        worktree = parent / "worktree"
        added = False
        pending: BaseException | None = None
        try:
            add = _git(
                repo,
                ["worktree", "add", "--detach", str(worktree), tested_main],
                command_runner=command_runner,
            )
            if add.returncode != 0:
                raise InvalidInput(f"git worktree add failed with rc={add.returncode}")
            added = True
            current_submodules = _initialize_submodules_cache_only(
                worktree, command_runner=command_runner
            )
            if submodule_receipt is None:
                submodule_receipt = current_submodules
            elif current_submodules != submodule_receipt:
                raise InvalidInput(
                    "reference submodule initialization state changed between probes"
                )
            _assert_probe_identity(
                worktree, tested_main, command_runner=command_runner
            )
            path_text = reference.split("::", 1)[0]
            collected = selected_collection_runner(worktree, path_text)
            selector, logged_nodeid = _selector_from_collection(reference, collected)
            if logged_nodeid in rerun_rcs:
                raise InvalidInput(
                    f"pytest FAILED/ERROR nodeids contain duplicates: {logged_nodeid!r}"
                )
            _assert_probe_identity(
                worktree, tested_main, command_runner=command_runner
            )
            before_fingerprint = _probe_fingerprint(
                worktree, command_runner=command_runner
            )
            rerun_rc = selected_runner(worktree, selector)
            if type(rerun_rc) is not int or rerun_rc not in {0, 1}:
                raise InvalidInput(
                    "single-node rerun did not produce pytest rc 0 or 1: "
                    f"{logged_nodeid!r} rc={rerun_rc!r}"
                )
            rerun_rcs[logged_nodeid] = rerun_rc
            if rerun_rc == 0:
                attributable.append(logged_nodeid)
            _assert_probe_identity(
                worktree, tested_main, command_runner=command_runner
            )
            after_fingerprint = _probe_fingerprint(
                worktree, command_runner=command_runner
            )
            if before_fingerprint != after_fingerprint:
                raise InvalidInput("probe worktree fingerprint changed during rerun")
            logged_nodeids.append(logged_nodeid)
        except BaseException as exc:
            pending = exc
        try:
            _cleanup_probe(
                repo,
                parent,
                worktree,
                added=added,
                command_runner=command_runner,
            )
        except BaseException as exc:
            raise InvalidInput(
                f"probe worktree cleanup did not complete: {exc}"
            ) from pending
        if pending is not None:
            if isinstance(
                pending, (KeyboardInterrupt, SystemExit, _TerminationSignal)
            ):
                raise pending
            if isinstance(pending, InvalidInput):
                raise pending
            raise InvalidInput(
                f"single-node rerun failed: {type(pending).__name__}: {pending}"
            ) from pending
    return (
        rerun_rcs,
        tuple(sorted(attributable)),
        tuple(sorted(logged_nodeids)),
        submodule_receipt or (),
    )


def _canonical_json(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_receipt(path: Path, document: Mapping[str, Any]) -> None:
    raw = _canonical_json(document)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise InvalidInput("O_NOFOLLOW is unavailable for receipt creation")
    flags |= nofollow
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(path, flags, 0o600)
        created = True
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short receipt write")
            view = view[written:]
        os.fsync(descriptor)
    except BaseException as exc:
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        if isinstance(exc, (KeyboardInterrupt, SystemExit, _TerminationSignal)):
            raise
        if isinstance(exc, OSError):
            raise InvalidInput(f"cannot create receipt: {exc}") from exc
        raise
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError as exc:
                if created:
                    try:
                        path.unlink()
                    except OSError:
                        pass
                raise InvalidInput(f"cannot close receipt: {exc}") from exc


def _absolute_path(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or unicodedata.normalize("NFC", value) != value:
        raise InvalidInput(f"{label} must be an absolute NFC path")
    return path


def _validate_paths(
    log: str,
    receipt: str,
    probe_root: str,
    repo_root: Path,
) -> tuple[Path, Path, Path, Path]:
    try:
        repo = repo_root.resolve(strict=True)
    except OSError as exc:
        raise InvalidInput(f"repo root cannot be resolved: {exc}") from exc
    log_path = _absolute_path(log, "--log")
    receipt_path = _absolute_path(receipt, "--receipt")
    probe_path = _absolute_path(probe_root, "--probe-root")
    try:
        probe = probe_path.resolve(strict=True)
    except OSError as exc:
        raise InvalidInput(f"--probe-root cannot be resolved: {exc}") from exc
    if not probe.is_dir() or probe.is_symlink():
        raise InvalidInput("--probe-root must be a real directory")
    if probe == repo or repo in probe.parents:
        raise InvalidInput("--probe-root must be outside the repository")
    try:
        receipt_parent = receipt_path.parent.resolve(strict=True)
    except OSError as exc:
        raise InvalidInput(f"--receipt parent cannot be resolved: {exc}") from exc
    if not receipt_parent.is_dir() or receipt_path.exists() or receipt_path.is_symlink():
        raise InvalidInput("--receipt must name a new file in an existing directory")
    return log_path, receipt_path, probe, repo


def check_acceptance_reds(
    *,
    log: str,
    tested_main: str,
    wave_tip: str,
    receipt: str,
    probe_root: str,
    repo_root: Path,
    node_runner: NodeRunner | None = None,
    collection_runner: CollectionRunner | None = None,
    command_runner: CommandRunner = subprocess.run,
) -> tuple[int, str, tuple[str, ...]]:
    log_path, receipt_path, probe, repo = _validate_paths(
        log, receipt, probe_root, repo_root
    )
    tested_main = _resolve_tested_main(repo, tested_main, command_runner=command_runner)
    _assert_wave_identity(repo, wave_tip, command_runner=command_runner)
    registered = _registered_worktrees(repo, command_runner=command_runner)
    if any(
        probe == Path(worktree) or Path(worktree) in probe.parents
        for worktree in registered
    ):
        raise InvalidInput("--probe-root must be outside every registered worktree")
    raw, log_sha256 = _read_log(log_path)
    references = parse_pytest_log(raw)
    rerun_rcs: dict[str, int] = {}
    attributable: tuple[str, ...] = ()
    nodeids: tuple[str, ...] = ()
    submodules: SubmoduleReceipt = ()
    if references:
        rerun_rcs, attributable, nodeids, submodules = _probe_nodes(
            repo,
            probe,
            tested_main,
            references,
            node_runner=node_runner,
            collection_runner=collection_runner,
            command_runner=command_runner,
        )
    _resolve_tested_main(repo, tested_main, command_runner=command_runner)
    _assert_wave_identity(repo, wave_tip, command_runner=command_runner)
    if not nodeids:
        rc, status = 0, "green"
    elif attributable:
        rc, status = 1, "attributable-red"
    else:
        rc, status = 0, "non-attributable-only"
    nodes = [
        {
            "classification": (
                "attributable" if rerun_rcs[nodeid] == 0 else "non-attributable"
            ),
            "nodeid": nodeid,
            "rerun_rc": rerun_rcs[nodeid],
        }
        for nodeid in sorted(nodeids)
    ]
    _write_receipt(
        receipt_path,
        {
            "log_path": str(log_path),
            "log_sha256": log_sha256,
            "nodes": nodes,
            "schema_version": _SCHEMA_VERSION,
            "status": status,
            "submodules": list(submodules),
            "tested_main": tested_main,
            "wave_tip": wave_tip,
        },
    )
    return rc, status, attributable


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="受入 log の赤を tested main で単独再走し、差分への帰属を判定する。"
    )
    parser.add_argument("--log", required=True)
    parser.add_argument("--tested-main", required=True)
    parser.add_argument("--wave-tip", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--probe-root", required=True)
    return parser


@contextlib.contextmanager
def _termination_signal_handlers():
    signals = tuple(
        candidate
        for candidate in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
        if candidate is not None
    )
    previous: dict[signal.Signals, Any] = {}

    def terminate(signum: int, _frame: Any) -> None:
        raise _TerminationSignal(signum)

    try:
        for candidate in signals:
            previous[candidate] = signal.getsignal(candidate)
            signal.signal(candidate, terminate)
        yield
    finally:
        for candidate, handler in previous.items():
            signal.signal(candidate, handler)


def main(
    argv: Sequence[str] | None = None,
    *,
    repo_root: Path | None = None,
    node_runner: NodeRunner | None = None,
    collection_runner: CollectionRunner | None = None,
    command_runner: CommandRunner = subprocess.run,
) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        return 2
    root = Path(__file__).resolve().parents[1] if repo_root is None else repo_root
    try:
        with _termination_signal_handlers():
            rc, status, attributable = check_acceptance_reds(
                log=args.log,
                tested_main=args.tested_main,
                wave_tip=args.wave_tip,
                receipt=args.receipt,
                probe_root=args.probe_root,
                repo_root=root,
                node_runner=node_runner,
                collection_runner=collection_runner,
                command_runner=command_runner,
            )
    except _TerminationSignal as exc:
        print("status=invalid-input", file=sys.stderr)
        print(f"reason=terminated by signal {exc.signum} after cleanup", file=sys.stderr)
        return 2
    except InvalidInput as exc:
        print("status=invalid-input", file=sys.stderr)
        print(f"reason={exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print("status=invalid-input", file=sys.stderr)
        print(
            f"reason=internal checker failure: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    print(f"status={status}")
    for nodeid in attributable:
        print(f"attributable={nodeid}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
