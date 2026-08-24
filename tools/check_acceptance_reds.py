#!/usr/bin/env python3
"""受入 log の赤を tested main との全走差分で判定する。"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, NamedTuple, Sequence


_SCHEMA_VERSION = "izanagi-acceptance-red-check/v1"
_MAX_LOG_BYTES = 64 * 1024 * 1024
_MAX_DISPATCH_RECEIPT_BYTES = 8 * 1024 * 1024
_MAX_PROBE_DIAGNOSTIC_ENTRIES = 64
_MAX_PROBE_DIAGNOSTIC_BYTES = 8192
# dispatch_compute may spend 900s queued, then reset its deadline to
# 3600s RUN time + 300s grace, followed by 60s of accounting.  Keep this
# outer timeout above that 4860s authority so dispatch reports its own timeout.
_DISPATCH_TIMEOUT_SECONDS = 5100.0
_WORKTREE_RETRY_DELAY_SECONDS = 1.0
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
_DISPATCH_CONTROL_PREFIX = "[Pegasus dispatch] "
_EFFECTIVE_SCHEDULER_PREFIX = "IZANAGI_EFFECTIVE_SCHEDULER_V1 "
_EFFECTIVE_SCHEDULERS = frozenset({"loadgroup", "serial", "unknown"})
_DISPATCH_RECEIPT_LINE = re.compile(
    r"^\[Pegasus dispatch\] receipt を (?P<path>/[^\r\n]*) "
    r"へ保存しました \(child rc=(?P<rc>[0-9]+)\)$"
)
_DISPATCH_RECEIPT_SCHEMA = "pegasus-dispatch-receipt/v2"
_DISPATCH_NONCE = re.compile(r"[A-Za-z0-9._-]+")
_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_COLLECTION_FOOTER = re.compile(
    r"(?:(?P<single>1) test collected|"
    r"(?P<plural>(?:[2-9]|[1-9][0-9]+)) tests collected|"
    r"(?P<selected>[0-9]+)/(?P<total>[0-9]+) tests collected "
    r"\((?P<deselected>[0-9]+) deselected\)|"
    r"no tests collected(?: \((?P<none_deselected>[0-9]+) deselected\))?) "
    rf"in (?P<duration>{_DURATION.pattern})"
)
_PYTEST_SELECTION_ENV = frozenset({
    "PYTEST_ADDOPTS",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    "PYTEST_PLUGINS",
    "IZANAGI_RUN_GROWTH_HELD_TESTS",
    # 履歴側 tested_main の旧 opt-in へ ambient 値を漏らさない。
    "IZANAGI_T080_E2E",
})

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class _PytestRunResult(NamedTuple):
    returncode: int
    references: tuple[str, ...]


FullRunner = Callable[[Path], _PytestRunResult]
NodeRunner = Callable[[Path, Sequence[str]], _PytestRunResult]
SubmoduleReceipt = tuple[Mapping[str, str], ...]
Sleeper = Callable[[float], None]


class _CollectionEvidence(NamedTuple):
    path: str
    source: str
    deleted_receipt_path: str | None
    submission_nonce: str | None
    request_id: str | None
    stdout_sha256: str | None


class _CollectionResult(NamedTuple):
    nodeids: tuple[str, ...]
    evidence: _CollectionEvidence


CollectionRunner = Callable[[Path], Sequence[str] | _CollectionResult]


class _MainProbeResult(NamedTuple):
    references: tuple[str, ...]
    collection: _CollectionResult


class _DispatchArtifacts(NamedTuple):
    root: Path
    receipt_path: Path
    submission_dir: Path
    fallback_receipt: Path | None
    nonce: str
    control_root: Path


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


def _has_control_character(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def _read_regular_file(path: Path, *, limit: int, label: str) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise InvalidInput(f"O_NOFOLLOW is unavailable for {label}")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise InvalidInput(f"cannot open {label}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise InvalidInput(f"{label} is not a regular file")
        if before.st_size > limit:
            raise InvalidInput(f"{label} exceeds its size cap")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if len(raw) > limit:
            raise InvalidInput(f"{label} exceeds its read cap")
        if identity_before != identity_after or len(raw) != before.st_size:
            raise InvalidInput(f"{label} changed while it was read")
        return raw
    except OSError as exc:
        raise InvalidInput(f"cannot read {label}: {exc}") from exc
    finally:
        try:
            os.close(descriptor)
        except OSError as exc:
            raise InvalidInput(f"cannot close {label}: {exc}") from exc


def _path_is_nfc_without_controls(path: Path) -> bool:
    value = str(path)
    return unicodedata.normalize("NFC", value) == value and not _has_control_character(
        value
    )


def _assert_no_symlink_components(root: Path, path: Path, *, label: str) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise InvalidInput(f"{label} is outside the dispatch root") from exc
    current = root
    if current.is_symlink():
        raise InvalidInput("dispatch root is a symlink")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise InvalidInput(f"{label} traverses a symlink")


def _dispatch_receipt_path(
    stdout: str, returncode: int,
) -> Path | None:
    matches = [
        match
        for line in stdout.splitlines()
        if (match := _DISPATCH_RECEIPT_LINE.fullmatch(line)) is not None
    ]
    has_dispatch_control = any(
        line.startswith(_DISPATCH_CONTROL_PREFIX) for line in stdout.splitlines()
    )
    if not matches:
        if has_dispatch_control:
            raise InvalidInput(
                "dispatch output has no unique non-relay receipt announcement"
            )
        return None
    if len(matches) != 1:
        raise InvalidInput("dispatch receipt announcement is non-unique")
    match = matches[0]
    if int(match.group("rc"), 10) != returncode:
        raise InvalidInput("dispatch receipt announcement child rc mismatch")
    value = match.group("path")
    path = Path(value)
    if not path.is_absolute() or not _path_is_nfc_without_controls(path):
        raise InvalidInput("dispatch receipt path is not an absolute safe NFC path")
    return path


def _dispatch_artifacts(receipt_path: Path, worktree: Path) -> _DispatchArtifacts:
    root_path = worktree / "output" / "pegasus-dispatch"
    try:
        root = root_path.resolve(strict=True)
        worktree_resolved = worktree.resolve(strict=True)
    except OSError as exc:
        raise InvalidInput(f"dispatch receipt root cannot be resolved: {exc}") from exc
    try:
        receipt_resolved = receipt_path.resolve(strict=True)
    except OSError as exc:
        raise InvalidInput(f"dispatch receipt cannot be resolved: {exc}") from exc

    fallback_receipt: Path | None = None
    preferred_shape = (
        receipt_path.parent.parent == root and receipt_path.name == "receipt.json"
    )
    fallback_shape = (
        receipt_path.parent == root
        and receipt_path.name.startswith("receipt-fallback-")
        and receipt_path.name.endswith(".json")
    )
    if receipt_path.name == "receipt.json":
        nonce = receipt_path.parent.name
        submission_dir = receipt_path.parent
    elif (
        receipt_path.name.startswith("receipt-fallback-")
        and receipt_path.name.endswith(".json")
    ):
        nonce = receipt_path.name[len("receipt-fallback-"):-len(".json")]
        submission_dir = root / nonce
        fallback_receipt = receipt_path
    else:
        nonce = receipt_path.parent.name
        submission_dir = receipt_path.parent

    location_valid = False
    try:
        _assert_no_symlink_components(root, receipt_path, label="dispatch receipt")
        _assert_no_symlink_components(root, submission_dir, label="dispatch submission")
        submission_resolved = submission_dir.resolve(strict=True)
    except (InvalidInput, OSError):
        pass
    else:
        location_valid = (
            root.is_dir()
            and root == worktree_resolved / "output" / "pegasus-dispatch"
            and receipt_resolved == receipt_path
            and (preferred_shape or fallback_shape)
            and submission_dir.is_dir()
            and submission_resolved == submission_dir
        )
    if not location_valid:
        raise InvalidInput("dispatch receipt has an invalid location")
    if _DISPATCH_NONCE.fullmatch(nonce) is None or nonce in {".", ".."}:
        raise InvalidInput("dispatch receipt nonce directory is invalid")
    return _DispatchArtifacts(
        root=root,
        receipt_path=receipt_path,
        submission_dir=submission_dir,
        fallback_receipt=fallback_receipt,
        nonce=nonce,
        control_root=worktree_resolved / "output" / "pegasus-dispatch",
    )


def _required_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidInput(f"dispatch receipt {label} is not an object")
    return value


def _read_dispatch_receipt(
    artifacts: _DispatchArtifacts,
    *,
    expected_args: Sequence[str],
    returncode: int,
) -> tuple[str, _CollectionEvidence]:
    raw = _read_regular_file(
        artifacts.receipt_path,
        limit=_MAX_DISPATCH_RECEIPT_BYTES,
        label="dispatch receipt",
    )
    try:
        document = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidInput(f"dispatch receipt is not canonical UTF-8 JSON: {exc}") from exc
    receipt = _required_mapping(document, "root")
    if receipt.get("schema_version") != _DISPATCH_RECEIPT_SCHEMA:
        raise InvalidInput("dispatch receipt schema_version is not v2")
    if receipt.get("submission_dir") != str(artifacts.submission_dir):
        raise InvalidInput("dispatch receipt submission_dir mismatch")

    request = _required_mapping(receipt.get("request"), "request")
    if request.get("task") != "tests" or request.get("args") != list(expected_args):
        raise InvalidInput("dispatch receipt request task/args mismatch")
    request_id = receipt.get("request_id")
    if type(request_id) is not str or _REQUEST_ID.fullmatch(request_id) is None:
        raise InvalidInput("dispatch receipt request_id is invalid")

    result = _required_mapping(receipt.get("result"), "result")
    child_rc = result.get("child_rc")
    if (
        result.get("stage") != "child"
        or type(child_rc) is not int
        or child_rc != returncode
    ):
        raise InvalidInput("dispatch receipt child result mismatch")
    outcome = _required_mapping(receipt.get("outcome"), "outcome")
    outcome_rc = outcome.get("rc")
    if (
        outcome.get("kind") != "child"
        or type(outcome_rc) is not int
        or outcome_rc != returncode
        or outcome.get("accounting_verified") is not True
    ):
        raise InvalidInput("dispatch receipt child outcome is not verified")

    scheduler_logs = _required_mapping(
        receipt.get("scheduler_logs"), "scheduler_logs"
    )
    if scheduler_logs.get("accounting_present") is not True:
        raise InvalidInput("dispatch receipt scheduler accounting is missing")
    stdout_record = _required_mapping(
        scheduler_logs.get("stdout"), "scheduler_logs.stdout"
    )
    stdout_path_value = stdout_record.get("path")
    if type(stdout_path_value) is not str:
        raise InvalidInput("dispatch receipt scheduler stdout path is invalid")
    stdout_path = Path(stdout_path_value)
    if not stdout_path.is_absolute() or not _path_is_nfc_without_controls(stdout_path):
        raise InvalidInput("dispatch receipt scheduler stdout path is unsafe")
    try:
        stdout_resolved = stdout_path.resolve(strict=True)
    except OSError as exc:
        raise InvalidInput(f"dispatch scheduler stdout cannot be resolved: {exc}") from exc
    _assert_no_symlink_components(
        artifacts.submission_dir, stdout_path, label="dispatch scheduler stdout"
    )
    if stdout_resolved != stdout_path or not stdout_path.is_file():
        raise InvalidInput("dispatch scheduler stdout is not a canonical regular file")

    size = stdout_record.get("size")
    omitted_bytes = stdout_record.get("omitted_bytes")
    tail = stdout_record.get("tail")
    if type(size) is not int or size < 0:
        raise InvalidInput("dispatch receipt scheduler stdout size is invalid")
    if type(omitted_bytes) is not int or omitted_bytes < 0:
        raise InvalidInput("dispatch receipt scheduler stdout omitted_bytes is invalid")
    if type(tail) is not str:
        raise InvalidInput("dispatch receipt scheduler stdout tail is invalid")
    if "\ufffd" in tail:
        raise InvalidInput("dispatch receipt scheduler stdout contains decode replacement")
    if omitted_bytes != 0:
        raise InvalidInput("dispatch receipt scheduler stdout is truncated")
    if size != len(tail.encode("utf-8")):
        raise InvalidInput("dispatch receipt scheduler stdout size mismatch")
    return tail, _CollectionEvidence(
        path="",
        source="dispatch-receipt",
        deleted_receipt_path=str(artifacts.receipt_path),
        submission_nonce=artifacts.nonce,
        request_id=request_id,
        stdout_sha256=hashlib.sha256(tail.encode("utf-8")).hexdigest(),
    )


def _orphan_hold_present(dispatch_root: Path) -> bool:
    """aggregate/request ledger の存在・判定不能を blocker にする。"""

    hold = dispatch_root / "orphan-hold.json"
    try:
        os.lstat(hold)
    except FileNotFoundError:
        pass
    except OSError:
        return True
    else:
        return True

    ledger = dispatch_root / "orphan-holds"
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


def _cleanup_dispatch_artifacts(artifacts: _DispatchArtifacts) -> None:
    if _orphan_hold_present(artifacts.control_root):
        raise InvalidInput(
            "orphan-hold: dispatch artifacts are preserved; "
            f"control={artifacts.control_root}; "
            "hold=orphan-hold.json|orphan-holds/*.json"
        )
    failures: list[str] = []
    try:
        shutil.rmtree(artifacts.submission_dir)
    except OSError as exc:
        failures.append(f"nonce directory removal failed: {exc}")
    if artifacts.fallback_receipt is not None:
        try:
            artifacts.fallback_receipt.unlink()
        except OSError as exc:
            failures.append(f"fallback receipt removal failed: {exc}")
    try:
        artifacts.root.rmdir()
    except OSError as exc:
        failures.append(f"dispatch root removal failed: {exc}")
    if artifacts.submission_dir.exists() or artifacts.submission_dir.is_symlink():
        failures.append("nonce directory remains")
    if artifacts.fallback_receipt is not None and (
        artifacts.fallback_receipt.exists() or artifacts.fallback_receipt.is_symlink()
    ):
        failures.append("fallback receipt remains")
    if artifacts.root.exists() or artifacts.root.is_symlink():
        failures.append("dispatch root remains")
    if failures:
        raise InvalidInput("dispatch artifact cleanup failed: " + "; ".join(failures))


def _authoritative_command_stdout(
    result: subprocess.CompletedProcess[str],
    *,
    worktree: Path,
    expected_args: Sequence[str],
) -> tuple[str, _CollectionEvidence]:
    relay_stdout = result.stdout or ""
    receipt_path = _dispatch_receipt_path(relay_stdout, int(result.returncode))
    if receipt_path is None:
        if "\ufffd" in relay_stdout:
            raise InvalidInput("local pytest stdout contains decode replacement")
        return relay_stdout, _CollectionEvidence(
            path="",
            source="local",
            deleted_receipt_path=None,
            submission_nonce=None,
            request_id=None,
            stdout_sha256=hashlib.sha256(relay_stdout.encode("utf-8")).hexdigest(),
        )
    artifacts = _dispatch_artifacts(receipt_path, worktree)
    try:
        return _read_dispatch_receipt(
            artifacts,
            expected_args=expected_args,
            returncode=int(result.returncode),
        )
    finally:
        _cleanup_dispatch_artifacts(artifacts)


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


def _no_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput("duplicate JSON key in pytest collection metadata")
        result[key] = value
    return result


def _is_collection_metadata(line: str) -> bool:
    """pytest の collection 出力に付く正規化済み診断 marker を検証する。"""

    if not line.startswith(_EFFECTIVE_SCHEDULER_PREFIX):
        return False
    payload_text = line[len(_EFFECTIVE_SCHEDULER_PREFIX):]
    try:
        payload = json.loads(
            payload_text,
            object_pairs_hook=_no_duplicate_json_keys,
        )
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError) as exc:
        raise InvalidInput("pytest collection scheduler marker is invalid") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"effective_scheduler"}
        or not isinstance(payload["effective_scheduler"], str)
        or payload["effective_scheduler"] not in _EFFECTIVE_SCHEDULERS
    ):
        raise InvalidInput("pytest collection scheduler marker is invalid")
    return True


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
    environment_removals: Sequence[str] = (),
) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment["GIT_TERMINAL_PROMPT"] = "0"
    for key in environment_removals:
        environment.pop(key, None)
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


def _pytest_environment() -> tuple[Mapping[str, str], tuple[str, ...]]:
    return (
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_ADDOPTS": "",
        },
        tuple(sorted(_PYTEST_SELECTION_ENV - {"PYTEST_ADDOPTS"})),
    )


def _absolute_pytest_target(worktree: Path, target: str) -> str:
    path_text, separator, suffix = target.partition("::")
    try:
        absolute_path = (worktree / path_text).resolve(strict=False)
    except OSError as exc:
        raise InvalidInput(f"pytest target cannot be normalized: {exc}") from exc
    return str(absolute_path) + (separator + suffix if separator else "")


def _expected_dispatch_args(
    worktree: Path,
    pytest_args: Sequence[str],
    *,
    target_indices: Sequence[int] | None = None,
) -> list[str]:
    if not pytest_args:
        raise InvalidInput("pytest dispatch argv has no target")
    expected = list(pytest_args)
    indices = (
        (len(pytest_args) - 1,)
        if target_indices is None
        else tuple(target_indices)
    )
    for index in indices:
        if index < 0 or index >= len(pytest_args):
            raise InvalidInput("pytest dispatch target index is out of range")
        expected[index] = _absolute_pytest_target(worktree, pytest_args[index])
    return expected


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
) -> tuple[str, str]:
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
    return hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(), result.stdout


def _probe_dirty_diagnostic(porcelain_text: str) -> str:
    records = porcelain_text.split("\n")
    while records and records[-1] == "":
        records.pop()
    total = len(records)
    shown: list[str] = []
    shown_bytes = 0
    for record in records:
        if len(shown) >= _MAX_PROBE_DIAGNOSTIC_ENTRIES:
            break
        record_bytes = len(record.encode("utf-8")) + 1
        if shown_bytes + record_bytes > _MAX_PROBE_DIAGNOSTIC_BYTES:
            break
        shown.append(record)
        shown_bytes += record_bytes

    truncated = len(shown) < total
    if shown:
        detail = "\n".join(shown)
    else:
        detail = "(no complete status records fit within the diagnostic limit)"
    if truncated:
        summary = f"showing {len(shown)} of {total} entries, truncated"
    else:
        summary = f"showing {len(shown)} of {total} entries"
    return (
        "probe worktree is not clean, including ignored files; "
        "porcelain status entries:\n"
        f"{detail}\n"
        f"{summary}\n"
        "(submodule entries show only the parent-repo summary line, not files "
        "inside the submodule)"
    )


def _assert_probe_identity(
    worktree: Path,
    expected_tip: str,
    *,
    tip_label: str = "--tested-main",
    command_runner: CommandRunner,
) -> None:
    head = _git(worktree, ["rev-parse", "HEAD"], command_runner=command_runner)
    if head.returncode != 0 or head.stdout.strip() != expected_tip:
        raise InvalidInput(f"probe worktree HEAD does not equal {tip_label}")
    fingerprint, porcelain_text = _probe_fingerprint(
        worktree, command_runner=command_runner
    )
    if fingerprint != hashlib.sha256(b"").hexdigest():
        raise InvalidInput(_probe_dirty_diagnostic(porcelain_text))


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


def _worktree_add(
    repo: Path,
    worktree: Path,
    tip: str,
    *,
    command_runner: CommandRunner,
    sleeper: Sleeper = time.sleep,
) -> subprocess.CompletedProcess[str]:
    """一過性の worktree add rc=128 だけを一度再試行する。"""

    command = ["worktree", "add", "--detach", str(worktree), tip]
    added = _git(repo, command, command_runner=command_runner)
    if added.returncode != 128:
        return added
    if worktree.exists() or worktree.is_symlink():
        raise InvalidInput(
            "git worktree add rc=128 left a worktree path residue; refusing retry"
        )
    if os.path.realpath(worktree) in _registered_worktrees(
        repo, command_runner=command_runner
    ):
        raise InvalidInput(
            "git worktree add rc=128 left a registered worktree residue; refusing retry"
        )
    sleeper(_WORKTREE_RETRY_DELAY_SECONDS)
    return _git(repo, command, command_runner=command_runner)


def _worktree_remove(
    repo: Path,
    worktree: Path,
    *,
    command_runner: CommandRunner,
    sleeper: Sleeper = time.sleep,
    deferred_signals: list[int] | None = None,
) -> subprocess.CompletedProcess[str]:
    """一過性の worktree remove rc=128 だけを一度再試行する。"""

    command = ["worktree", "remove", "--force", str(worktree)]
    removed = _git(repo, command, command_runner=command_runner)
    if removed.returncode != 128:
        return removed
    dispatch_root = worktree / "output" / "pegasus-dispatch"
    if _orphan_hold_present(dispatch_root):
        raise InvalidInput(
            "orphan-hold: refusing worktree remove retry; "
            f"control={dispatch_root}; "
            "hold=orphan-hold.json|orphan-holds/*.json"
        )
    path_present = worktree.exists() or worktree.is_symlink()
    registered = _registered_worktrees(repo, command_runner=command_runner)
    if not path_present and os.path.realpath(worktree) not in registered:
        raise InvalidInput(
            "git worktree remove rc=128 left no removable worktree residue"
        )
    try:
        sleeper(_WORKTREE_RETRY_DELAY_SECONDS)
    except _TerminationSignal as exc:
        if deferred_signals is None:
            raise
        if not deferred_signals:
            deferred_signals.append(exc.signum)
    if _orphan_hold_present(dispatch_root):
        raise InvalidInput(
            "orphan-hold: refusing worktree remove retry; "
            f"control={dispatch_root}; "
            "hold=orphan-hold.json|orphan-holds/*.json"
        )
    return _git(repo, command, command_runner=command_runner)


def _cleanup_probe(
    repo: Path,
    parent: Path,
    worktree: Path,
    *,
    added: bool,
    command_runner: CommandRunner,
    sleeper: Sleeper = time.sleep,
    deferred_signals: list[int] | None = None,
) -> None:
    dispatch_root = worktree / "output" / "pegasus-dispatch"
    if _orphan_hold_present(dispatch_root):
        raise InvalidInput(
            "orphan-hold: probe worktree is preserved; "
            f"control={dispatch_root}; "
            "hold=orphan-hold.json|orphan-holds/*.json"
        )
    failures: list[str] = []
    if added or worktree.exists():
        try:
            removed = _worktree_remove(
                repo,
                worktree,
                command_runner=command_runner,
                sleeper=sleeper,
                deferred_signals=deferred_signals,
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


def _complete_collected_nodeids(
    stdout: str, path_text: str | None = None,
) -> tuple[str, ...]:
    lines = [
        _ANSI_ESCAPE.sub("", _payload_line(line)).strip()
        for line in stdout.splitlines()
    ]
    footer_candidates = [
        line
        for line in lines
        if re.match(r"^(?:no|[0-9]+(?:/[0-9]+)?) tests? collected\b", line)
    ]
    if len(footer_candidates) != 1:
        raise InvalidInput("pytest collection footer is missing or non-unique")
    footer = _COLLECTION_FOOTER.fullmatch(footer_candidates[0])
    if footer is None:
        raise InvalidInput("pytest collection footer has an unknown format")
    if footer.group("single") is not None:
        selected = 1
    elif footer.group("plural") is not None:
        selected = int(footer.group("plural"), 10)
    elif footer.group("selected") is not None:
        selected = int(footer.group("selected"), 10)
        total = int(footer.group("total"), 10)
        deselected = int(footer.group("deselected"), 10)
        if selected + deselected != total:
            raise InvalidInput("pytest collection footer deselection arithmetic mismatch")
    else:
        selected = 0
    if selected == 0:
        raise InvalidInput("pytest collection selected zero tests")

    body_lines = []
    metadata_count = 0
    for line in lines:
        if line == footer_candidates[0]:
            continue
        if _is_collection_metadata(line):
            metadata_count += 1
            continue
        body_lines.append(line)
    if metadata_count > 1:
        raise InvalidInput("pytest collection scheduler marker is non-unique")
    if path_text is None:
        nodeids = []
        for line in body_lines:
            if not line:
                continue
            _outcome_reference(line)
            nodeids.append(line)
    else:
        nodeids = [
            line
            for line in body_lines
            if line == path_text or line.startswith(f"{path_text}::")
        ]
    if len(nodeids) != len(set(nodeids)):
        raise InvalidInput("pytest collect-only returned duplicate nodeids")
    if len(nodeids) != selected:
        raise InvalidInput(
            "collection footer count mismatch: "
            f"selected={selected} nodeids={len(nodeids)} path={path_text!r}"
        )
    return tuple(sorted(nodeids))


def _pytest_run_result(
    result: subprocess.CompletedProcess[str],
    *,
    worktree: Path,
    expected_args: Sequence[str],
    label: str,
) -> _PytestRunResult:
    authoritative_stdout, _evidence = _authoritative_command_stdout(
        result,
        worktree=worktree,
        expected_args=expected_args,
    )
    if result.returncode not in {0, 1}:
        raise InvalidInput(
            f"{label} did not produce pytest rc 0 or 1: rc={result.returncode}"
        )
    references = parse_pytest_log(authoritative_stdout.encode("utf-8"))
    if (result.returncode == 0) != (not references):
        raise InvalidInput(
            f"{label} rc and FAILED/ERROR outcomes are inconsistent: "
            f"rc={result.returncode} references={references!r}"
        )
    return _PytestRunResult(int(result.returncode), tuple(references))


def _default_full_runner(
    worktree: Path,
    *,
    command_runner: CommandRunner,
) -> _PytestRunResult:
    pytest_args = ["-p", "no:cacheprovider"]
    command = [
        sys.executable,
        str(worktree / "tools" / "run_tests.py"),
        "--force-dispatch",
        *pytest_args,
    ]
    environment_overrides, environment_removals = _pytest_environment()
    result = _completed(
        command_runner,
        command,
        cwd=worktree,
        capture_output=True,
        timeout=_DISPATCH_TIMEOUT_SECONDS,
        environment_overrides=environment_overrides,
        environment_removals=environment_removals,
    )
    return _pytest_run_result(
        result,
        worktree=worktree,
        expected_args=_expected_dispatch_args(
            worktree, pytest_args, target_indices=()
        ),
        label="main full run",
    )


def _default_node_runner(
    worktree: Path,
    nodeids: Sequence[str],
    *,
    command_runner: CommandRunner,
) -> _PytestRunResult:
    if not nodeids:
        raise InvalidInput("batch rerun received no nodeids")
    pytest_args = [
        "-p",
        "no:cacheprovider",
        *nodeids,
    ]
    command = [
        sys.executable,
        str(worktree / "tools" / "run_tests.py"),
        "--force-dispatch",
        *pytest_args,
    ]
    environment_overrides, environment_removals = _pytest_environment()
    result = _completed(
        command_runner,
        command,
        cwd=worktree,
        capture_output=True,
        timeout=_DISPATCH_TIMEOUT_SECONDS,
        environment_overrides=environment_overrides,
        environment_removals=environment_removals,
    )
    return _pytest_run_result(
        result,
        worktree=worktree,
        expected_args=_expected_dispatch_args(
            worktree,
            pytest_args,
            target_indices=range(2, len(pytest_args)),
        ),
        label="wave batch rerun",
    )


def _default_collection_runner(
    worktree: Path,
    *,
    command_runner: CommandRunner,
) -> _CollectionResult:
    pytest_args = [
        "-p",
        "no:cacheprovider",
        "--collect-only",
        "-q",
    ]
    command = [
        sys.executable,
        str(worktree / "tools" / "run_tests.py"),
        "--force-dispatch",
        *pytest_args,
    ]
    environment_overrides, environment_removals = _pytest_environment()
    result = _completed(
        command_runner,
        command,
        cwd=worktree,
        timeout=_DISPATCH_TIMEOUT_SECONDS,
        environment_overrides=environment_overrides,
        environment_removals=environment_removals,
    )
    authoritative_stdout, evidence = _authoritative_command_stdout(
        result,
        worktree=worktree,
        expected_args=_expected_dispatch_args(
            worktree, pytest_args, target_indices=()
        ),
    )
    if result.returncode != 0:
        raise InvalidInput(f"pytest collect-only failed: rc={result.returncode}")
    nodeids = _complete_collected_nodeids(authoritative_stdout)
    return _CollectionResult(
        nodeids=nodeids,
        evidence=_CollectionEvidence(
            path="",
            source=evidence.source,
            deleted_receipt_path=evidence.deleted_receipt_path,
            submission_nonce=evidence.submission_nonce,
            request_id=evidence.request_id,
            stdout_sha256=evidence.stdout_sha256,
        ),
    )


def _collection_result_from_output(
    collection_output: Sequence[str] | _CollectionResult,
) -> _CollectionResult:
    if isinstance(collection_output, _CollectionResult):
        return collection_output
    return _CollectionResult(
        nodeids=tuple(collection_output),
        evidence=_CollectionEvidence(
            path="",
            source="injected-runner",
            deleted_receipt_path=None,
            submission_nonce=None,
            request_id=None,
            stdout_sha256=None,
        ),
    )


@contextlib.contextmanager
def _defer_cleanup_signals(deferred: list[int]) -> Any:
    """cleanup 中の signal を記録し、破壊的操作の途中では再送しない。"""

    signals = tuple(
        candidate
        for candidate in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
        if candidate is not None
    )
    previous: dict[signal.Signals, Any] = {}

    def defer(signum: int, _frame: Any) -> None:
        if not deferred:
            deferred.append(signum)

    try:
        for candidate in signals:
            previous[candidate] = signal.getsignal(candidate)
            signal.signal(candidate, defer)
        yield
    finally:
        for candidate, handler in previous.items():
            signal.signal(candidate, handler)


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


def _coerce_run_result(value: Any, *, label: str) -> _PytestRunResult:
    if isinstance(value, _PytestRunResult):
        result = value
    elif (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and len(value) == 2
    ):
        result = _PytestRunResult(value[0], tuple(value[1]))
    else:
        raise InvalidInput(f"{label} returned an invalid result")
    if type(result.returncode) is not int or result.returncode not in {0, 1}:
        raise InvalidInput(
            f"{label} did not produce pytest rc 0 or 1: "
            f"rc={result.returncode!r}"
        )
    if isinstance(result.references, (str, bytes, bytearray)):
        raise InvalidInput(f"{label} returned invalid pytest references")
    references = tuple(result.references)
    if any(type(reference) is not str for reference in references):
        raise InvalidInput(f"{label} returned a non-string pytest reference")
    if (result.returncode == 0) != (not references):
        raise InvalidInput(
            f"{label} rc and FAILED/ERROR outcomes are inconsistent: "
            f"rc={result.returncode} references={references!r}"
        )
    return _PytestRunResult(result.returncode, references)


def _validate_collection_result(
    collection: _CollectionResult,
) -> _CollectionResult:
    nodeids = tuple(collection.nodeids)
    if not nodeids:
        raise InvalidInput("pytest collect-only returned no nodeids")
    if any(type(nodeid) is not str for nodeid in nodeids):
        raise InvalidInput("pytest collect-only returned a non-string nodeid")
    if len(nodeids) != len(set(nodeids)):
        raise InvalidInput("pytest collect-only returned duplicate nodeids")
    for nodeid in nodeids:
        _outcome_reference(nodeid)
    return _CollectionResult(tuple(sorted(nodeids)), collection.evidence)


def _run_probe_worktree(
    repo: Path,
    probe_root: Path,
    tip: str,
    *,
    tip_label: str,
    operation: Callable[[Path], Any],
    command_runner: CommandRunner,
    sleeper: Sleeper = time.sleep,
) -> tuple[Any, SubmoduleReceipt]:
    parent = Path(
        tempfile.mkdtemp(prefix="izanagi-acceptance-reds-", dir=probe_root)
    )
    worktree = parent / "worktree"
    added = False
    pending: BaseException | None = None
    result: Any = None
    submodules: SubmoduleReceipt = ()
    try:
        add = _worktree_add(
            repo,
            worktree,
            tip,
            command_runner=command_runner,
            sleeper=sleeper,
        )
        if add.returncode != 0:
            raise InvalidInput(f"git worktree add failed with rc={add.returncode}")
        added = True
        submodules = _initialize_submodules_cache_only(
            worktree, command_runner=command_runner
        )
        _assert_probe_identity(
            worktree,
            tip,
            tip_label=tip_label,
            command_runner=command_runner,
        )
        result = operation(worktree)
    except BaseException as exc:
        pending = exc
    deferred_signals: list[int] = []
    try:
        with _defer_cleanup_signals(deferred_signals):
            _cleanup_probe(
                repo,
                parent,
                worktree,
                added=added,
                command_runner=command_runner,
                sleeper=sleeper,
                deferred_signals=deferred_signals,
            )
    except _TerminationSignal:
        raise
    except BaseException as exc:
        raise InvalidInput(
            f"probe worktree cleanup did not complete: {exc}"
        ) from pending
    if deferred_signals and pending is None:
        pending = _TerminationSignal(deferred_signals[0])
    if pending is not None:
        if isinstance(pending, (KeyboardInterrupt, SystemExit, _TerminationSignal)):
            raise pending
        if isinstance(pending, InvalidInput):
            raise pending
        raise InvalidInput(
            f"probe operation failed: {type(pending).__name__}: {pending}"
        ) from pending
    if result is None:
        raise InvalidInput("probe operation returned no result")
    return result, submodules


def _run_with_fingerprint(
    worktree: Path,
    tip: str,
    *,
    tip_label: str,
    operation: Callable[[], Any],
    command_runner: CommandRunner,
    description: str,
) -> Any:
    _assert_probe_identity(
        worktree,
        tip,
        tip_label=tip_label,
        command_runner=command_runner,
    )
    before_fingerprint, _ = _probe_fingerprint(
        worktree, command_runner=command_runner
    )
    result = operation()
    _assert_probe_identity(
        worktree,
        tip,
        tip_label=tip_label,
        command_runner=command_runner,
    )
    after_fingerprint, _ = _probe_fingerprint(
        worktree, command_runner=command_runner
    )
    if before_fingerprint != after_fingerprint:
        raise InvalidInput(f"probe worktree fingerprint changed during {description}")
    return result


def _run_main_probe(
    repo: Path,
    probe_root: Path,
    tested_main: str,
    *,
    full_runner: FullRunner,
    collection_runner: CollectionRunner,
    command_runner: CommandRunner,
    sleeper: Sleeper,
) -> tuple[_MainProbeResult, SubmoduleReceipt]:
    def operation(worktree: Path) -> _MainProbeResult:
        full = _run_with_fingerprint(
            worktree,
            tested_main,
            tip_label="--tested-main",
            operation=lambda: _coerce_run_result(
                full_runner(worktree), label="main full run"
            ),
            command_runner=command_runner,
            description="main full run",
        )
        collection = _run_with_fingerprint(
            worktree,
            tested_main,
            tip_label="--tested-main",
            operation=lambda: _validate_collection_result(
                _collection_result_from_output(collection_runner(worktree))
            ),
            command_runner=command_runner,
            description="main collect-only run",
        )
        return _MainProbeResult(full.references, collection)

    return _run_probe_worktree(
        repo,
        probe_root,
        tested_main,
        tip_label="--tested-main",
        operation=operation,
        command_runner=command_runner,
        sleeper=sleeper,
    )


def _resolve_red_references(
    main_references: Sequence[str],
    tip_references: Sequence[str],
    collected_nodeids: Sequence[str],
) -> tuple[dict[str, str], dict[str, str]]:
    main_by_nodeid: dict[str, str] = {}
    for reference in main_references:
        _outcome_reference(reference)
        try:
            selector, nodeid = _selector_from_collection(
                reference, collected_nodeids
            )
        except InvalidInput as exc:
            raise InvalidInput(
                f"main red reference cannot be resolved by collection: {reference!r}"
            ) from exc
        if nodeid in main_by_nodeid:
            raise InvalidInput(
                f"main red references resolve to duplicate nodeid: {nodeid!r}"
            )
        main_by_nodeid[nodeid] = selector

    tip_by_nodeid: dict[str, str] = {}
    for reference in tip_references:
        _outcome_reference(reference)
        try:
            selector, nodeid = _selector_from_collection(
                reference, collected_nodeids
            )
        except InvalidInput:
            # A test added only by the wave is absent from the tested-main
            # collection.  Keep its original reference for the wave batch.
            selector, nodeid = reference, reference
        if nodeid in tip_by_nodeid:
            raise InvalidInput(
                f"tip red references resolve to duplicate nodeid: {nodeid!r}"
            )
        tip_by_nodeid[nodeid] = selector
    return main_by_nodeid, tip_by_nodeid


def _batch_rerun_rcs(
    result: _PytestRunResult,
    nodeid_selectors: Mapping[str, str],
) -> dict[str, int]:
    selectors = tuple(nodeid_selectors.values())
    if len(selectors) != len(set(selectors)):
        raise InvalidInput("wave batch contains duplicate pytest selectors")
    failed_selectors: set[str] = set()
    for reference in result.references:
        _outcome_reference(reference)
        try:
            selector, _nodeid = _selector_from_collection(reference, selectors)
        except InvalidInput as exc:
            raise InvalidInput(
                f"wave batch red reference is outside the selected D set: "
                f"{reference!r}"
            ) from exc
        if selector in failed_selectors:
            raise InvalidInput(
                f"wave batch red reference resolves to a duplicate selector: "
                f"{selector!r}"
            )
        failed_selectors.add(selector)
    return {
        nodeid: 1 if selector in failed_selectors else 0
        for nodeid, selector in nodeid_selectors.items()
    }


def _run_wave_batch(
    repo: Path,
    probe_root: Path,
    wave_tip: str,
    nodeid_selectors: Mapping[str, str],
    *,
    node_runner: NodeRunner,
    command_runner: CommandRunner,
    sleeper: Sleeper,
) -> dict[str, int]:
    selectors = tuple(nodeid_selectors.values())
    if not selectors:
        raise InvalidInput("wave batch rerun received no D nodeids")

    def operation(worktree: Path) -> dict[str, int]:
        return _run_with_fingerprint(
            worktree,
            wave_tip,
            tip_label="--wave-tip",
            operation=lambda: _batch_rerun_rcs(
                _coerce_run_result(
                    node_runner(worktree, selectors),
                    label="wave batch rerun",
                ),
                nodeid_selectors,
            ),
            command_runner=command_runner,
            description="wave batch rerun",
        )

    result, _submodules = _run_probe_worktree(
        repo,
        probe_root,
        wave_tip,
        tip_label="--wave-tip",
        operation=operation,
        command_runner=command_runner,
        sleeper=sleeper,
    )
    return result


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
    full_runner: FullRunner | None = None,
    node_runner: NodeRunner | None = None,
    collection_runner: CollectionRunner | None = None,
    command_runner: CommandRunner = subprocess.run,
    sleeper: Sleeper = time.sleep,
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
    tip_references = parse_pytest_log(raw)
    wave_rerun_rcs: dict[str, int] = {}
    attributable: list[str] = []
    flakes: list[str] = []
    nodeids: tuple[str, ...] = tuple(tip_references)
    main_by_nodeid: dict[str, str] = {}
    submodules: SubmoduleReceipt = ()
    collections: tuple[_CollectionEvidence, ...] = ()
    if tip_references:
        selected_full_runner = (
            (lambda worktree: _default_full_runner(
                worktree, command_runner=command_runner
            ))
            if full_runner is None
            else full_runner
        )
        selected_node_runner = (
            (lambda worktree, selected: _default_node_runner(
                worktree, selected, command_runner=command_runner
            ))
            if node_runner is None
            else node_runner
        )
        selected_collection_runner = (
            (lambda worktree: _default_collection_runner(
                worktree, command_runner=command_runner
            ))
            if collection_runner is None
            else collection_runner
        )
        main_probe, submodules = _run_main_probe(
            repo,
            probe,
            tested_main,
            full_runner=selected_full_runner,
            collection_runner=selected_collection_runner,
            command_runner=command_runner,
            sleeper=sleeper,
        )
        main_by_nodeid, tip_by_nodeid = _resolve_red_references(
            main_probe.references,
            tip_references,
            main_probe.collection.nodeids,
        )
        nodeids = tuple(sorted(tip_by_nodeid))
        difference = {
            nodeid: tip_by_nodeid[nodeid]
            for nodeid in nodeids
            if nodeid not in main_by_nodeid
        }
        if difference:
            _assert_wave_identity(repo, wave_tip, command_runner=command_runner)
            wave_rerun_rcs = _run_wave_batch(
                repo,
                probe,
                wave_tip,
                difference,
                node_runner=selected_node_runner,
                command_runner=command_runner,
                sleeper=sleeper,
            )
            for nodeid in sorted(difference):
                if wave_rerun_rcs[nodeid] == 1:
                    attributable.append(nodeid)
                else:
                    flakes.append(nodeid)
        collections = (main_probe.collection.evidence,)
    _resolve_tested_main(repo, tested_main, command_runner=command_runner)
    _assert_wave_identity(repo, wave_tip, command_runner=command_runner)
    if not nodeids:
        rc, status = 0, "green"
    elif attributable:
        rc, status = 1, "attributable-red"
    else:
        rc, status = 0, "non-attributable-only"
    nodes = []
    for nodeid in sorted(nodeids):
        if nodeid in main_by_nodeid:
            nodes.append(
                {
                    "classification": "non-attributable",
                    "nodeid": nodeid,
                    "rerun_rc": 1,
                }
            )
            continue
        wave_rc = wave_rerun_rcs[nodeid]
        nodes.append(
            {
                "classification": "flake" if nodeid in flakes else "attributable",
                "main_rerun_rc": 0,
                "nodeid": nodeid,
                "rerun_rc": 0,
                "wave_rerun_rc": wave_rc,
            }
        )
    _write_receipt(
        receipt_path,
        {
            "collections": [
                {
                    "path": item.path,
                    "deleted_receipt_path": item.deleted_receipt_path,
                    "request_id": item.request_id,
                    "source": item.source,
                    "stdout_sha256": item.stdout_sha256,
                    "submission_nonce": item.submission_nonce,
                }
                for item in collections
            ],
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
        description=(
            "受入 log の赤を tested main の全走との差分で分類し、"
            "差分だけを wave tip で batch 再走して帰属を判定する。"
        )
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
    full_runner: FullRunner | None = None,
    node_runner: NodeRunner | None = None,
    collection_runner: CollectionRunner | None = None,
    command_runner: CommandRunner = subprocess.run,
    sleeper: Sleeper = time.sleep,
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
                full_runner=full_runner,
                node_runner=node_runner,
                collection_runner=collection_runner,
                command_runner=command_runner,
                sleeper=sleeper,
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
