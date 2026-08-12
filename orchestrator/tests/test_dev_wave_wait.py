# -*- coding: utf-8 -*-
"""tools/dev_wave_wait.py の canonical waiter 契約テスト。"""
from __future__ import annotations

import errno
import hashlib
import importlib.util
import json
import os
import signal
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "dev_wave_wait.py"
_LEASE_HELPER = _ROOT / "tools" / "wave_land_window.py"
_SPEC = importlib.util.spec_from_file_location("dev_wave_wait_under_test", _TOOL)
assert _SPEC and _SPEC.loader
DW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = DW
_SPEC.loader.exec_module(DW)

_SHA_A = "a" * 40
_SHA_B = "b" * 40
_SHA_C = "c" * 40
_WAVE = "wave-test"
_REPO = Path("/repo")
_LEASE = Path("/lease")
_MESSAGE = Path("/message.txt")
_VALIDATED_MESSAGE = Path("/validated-message.txt")
_RECEIPT = Path("/receipts/acceptance.json")
_RECEIPT_TEMP = Path("/receipts/.dev-wave-acceptance-receipt-test.tmp")
_LOG = Path("/receipts/acceptance.log")
_CHECKER_RECEIPT = Path(
    "/receipts/acceptance.json.acceptance-red-check.json"
)
_COMMAND = ("harmless-command", "--flag")
_HOLDER = hashlib.sha256(_WAVE.encode("utf-8")).hexdigest()[:12]
_WAITER_BLOB = "d" * 40
_CHECKER_BLOB = "e" * 40
_RELEASE_JSON = json.dumps({"state": "released"})
_LEGACY_STATUS_ARGV = ("git", "status", "--porcelain", "--untracked-files=no")
_STATUS_ARGV = (
    "git", "status", "--porcelain", "--untracked-files=all",
    "--ignore-submodules=none",
)
_INDEX_FLAGS_ARGV = ("git", "ls-files", "-v", "-z")
_SUBMODULE_INDEX_FLAGS_ARGV = (
    "git", "submodule", "foreach", "--recursive", "--quiet",
    "git ls-files -v -z",
)
_DIFF_ARGV = ("git", "diff", "--binary", "--no-ext-diff", "HEAD", "--")
_SUBMODULE_STATUS_ARGV = ("git", "submodule", "status", "--recursive")
_SUBMODULE_READY_ARGV = _SUBMODULE_STATUS_ARGV


def _provenance_argv(
    repo: Path = _REPO,
    message: Path = _VALIDATED_MESSAGE,
) -> tuple[str, ...]:
    return (
        sys.executable,
        str(repo / "tools" / "check_ai_provenance.py"),
        "--message-file",
        str(message),
    )


def _stat_text(pid: int, start_time: int) -> str:
    fields = ["S", *("0" for _ in range(18)), str(start_time), "0"]
    return f"{pid} (worker name) " + " ".join(fields)


class _FakeEffects:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []
        self.run_queue: list[tuple[tuple[str, ...], bool, object]] = []
        self.kill_queue: list[object] = []
        self.is_file_queue: list[tuple[Path, object]] = []
        self.read_text_queue: list[tuple[Path, object]] = []
        self.monotonic_queue: list[float] = []
        self.env: dict[str, str] = {}
        self.temp_path = _VALIDATED_MESSAGE
        self.existing_paths: set[Path] = set()
        self.directories: set[Path] = {_RECEIPT.parent}
        self.symlinks: set[Path] = set()
        self.receipt_temp_result: object = _RECEIPT_TEMP
        self.rename_result: object = None
        self.receipt_content: bytes | None = None
        self.receipt_published = False
        self.last_claim_main_sha: str | None = None
        self.final_claim_age_seconds = 0
        self.logged_bytes = b""
        self.byte_files: dict[Path, bytes] = {}

    @property
    def effects(self) -> object:
        return DW._Effects(
            run=self.run,
            run_unbounded=self.run,
            sleep=self.sleep,
            kill=self.kill,
            is_file=self.is_file,
            read_text=self.read_text,
            getenv=self.getenv,
            monotonic=self.monotonic,
            write_temp=self.write_temp,
            unlink=self.unlink,
            path_exists=self.path_exists,
            is_dir=self.is_dir,
            resolve_path=self.resolve_path,
            write_receipt_temp=self.write_receipt_temp,
            rename=self.rename,
            run_logged=self.run_logged,
            read_bytes=self.read_bytes,
            is_symlink=self.is_symlink,
        )

    def expect_run(
        self,
        argv: tuple[str, ...],
        result: object = None,
        *,
        capture: bool = True,
        unchanged_postrun: bool = True,
    ) -> None:
        if result is None:
            result = DW._CommandResult(0)
        if len(argv) >= 5 and argv[2] == "claim" and argv[-2] == "--main-sha":
            self.last_claim_main_sha = argv[-1]
        self.run_queue.append((argv, capture, result))
        if (
            argv == _COMMAND
            and unchanged_postrun
            and not isinstance(result, BaseException)
        ):
            assert self.last_claim_main_sha is not None
            confirmed_main_sha = self.last_claim_main_sha
            postrun = [
                    (_STATUS_ARGV, True, DW._CommandResult(0, "")),
                    (_INDEX_FLAGS_ARGV, True, DW._CommandResult(0, "")),
                    (_SUBMODULE_INDEX_FLAGS_ARGV, True, DW._CommandResult(0, "")),
                    (
                        ("git", "rev-parse", "HEAD"),
                        True,
                        DW._CommandResult(0, _SHA_A + "\n"),
                    ),
                    (_DIFF_ARGV, True, DW._CommandResult(0, "")),
                    (_SUBMODULE_STATUS_ARGV, True, DW._CommandResult(0, "")),
            ]
            if result.returncode == 0:
                postrun.extend(
                    [
                    (
                        (
                            "git",
                            "rev-parse",
                            f"{_SHA_A}:tools/dev_wave_wait.py",
                        ),
                        True,
                        DW._CommandResult(0, _WAITER_BLOB + "\n"),
                    ),
                    (
                        ("git", "rev-parse", "main"),
                        True,
                        DW._CommandResult(0, confirmed_main_sha + "\n"),
                    ),
                    (
                        _helper("claim", confirmed_main_sha),
                        True,
                        DW._CommandResult(
                            0,
                            _held_self_payload(
                                main_sha=confirmed_main_sha,
                                age_seconds=self.final_claim_age_seconds,
                            ),
                        ),
                    ),
                    ]
                )
            self.run_queue.extend(postrun)

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        self.events.append(("run", actual, cwd, capture))
        assert self.run_queue, f"unexpected run: {actual}"
        expected, expected_capture, result = self.run_queue.pop(0)
        assert actual == expected
        assert capture is expected_capture
        if isinstance(result, BaseException):
            raise result
        return result

    def run_logged(self, argv: object, cwd: Path, log_file: Path) -> object:
        result = self.run(argv, cwd, False)
        self.byte_files[log_file] = self.logged_bytes
        self.existing_paths.add(log_file)
        return result

    def read_bytes(self, path: Path) -> bytes:
        assert path in self.byte_files, f"unexpected read_bytes: {path}"
        return self.byte_files[path]

    def sleep(self, seconds: float) -> None:
        self.events.append(("sleep", seconds))

    def kill(self, pid: int, signum: int) -> None:
        self.events.append(("kill", pid, signum))
        result = self.kill_queue.pop(0)
        if isinstance(result, BaseException):
            raise result

    def is_file(self, path: Path) -> bool:
        self.events.append(("is_file", path))
        assert self.is_file_queue, f"unexpected is_file: {path}"
        expected, result = self.is_file_queue.pop(0)
        assert path == expected
        if isinstance(result, BaseException):
            raise result
        return bool(result)

    def read_text(self, path: Path) -> str:
        self.events.append(("read_text", path))
        assert self.read_text_queue, f"unexpected read_text: {path}"
        expected, result = self.read_text_queue.pop(0)
        assert path == expected
        if isinstance(result, BaseException):
            raise result
        return str(result)

    def getenv(self, name: str) -> str | None:
        return self.env.get(name)

    def monotonic(self) -> float:
        self.events.append(("monotonic",))
        return self.monotonic_queue.pop(0) if self.monotonic_queue else 0.0

    def write_temp(self, content: bytes) -> Path:
        self.events.append(("write_temp", content))
        return self.temp_path

    def unlink(self, path: Path) -> None:
        self.events.append(("unlink", path))

    def path_exists(self, path: Path) -> bool:
        return path in self.existing_paths

    def is_dir(self, path: Path) -> bool:
        return path in self.directories

    def is_symlink(self, path: Path) -> bool:
        return path in self.symlinks

    def resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return Path(os.path.normpath(path))
        return Path(os.path.normpath(_REPO / path))

    def write_receipt_temp(self, final_path: Path, content: bytes) -> Path:
        self.events.append(("write_receipt_temp", final_path))
        self.receipt_content = content
        if isinstance(self.receipt_temp_result, BaseException):
            raise self.receipt_temp_result
        return self.receipt_temp_result

    def rename(self, source: Path, target: Path) -> None:
        self.events.append(("rename", source, target))
        if isinstance(self.rename_result, BaseException):
            raise self.rename_result
        self.receipt_published = True
        self.existing_paths.add(target)

    def assert_drained(
        self, expected_events: list[tuple[object, ...]] | None = None
    ) -> None:
        if expected_events is not None:
            assert self.events == expected_events
        assert self.run_queue == []
        assert self.kill_queue == []
        assert self.is_file_queue == []
        assert self.read_text_queue == []
        assert self.monotonic_queue == []


def _helper(
    action: str,
    sha: str | None = None,
    *,
    lease_dir: Path = _LEASE,
) -> tuple[str, ...]:
    argv = (
        sys.executable,
        str(_REPO / "tools" / "wave_land_window.py"),
        action,
        "--lease-dir",
        str(lease_dir),
        "--wave",
        _WAVE,
    )
    return argv + (("--main-sha", sha) if sha is not None else ())


def _preflight(fake: _FakeEffects) -> None:
    fake.expect_run(
        ("git", "rev-parse", "--is-inside-work-tree"),
        DW._CommandResult(0, "true\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "--show-toplevel"),
        DW._CommandResult(0, str(_REPO) + "\n"),
    )
    fake.expect_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        DW._CommandResult(0, f"feature-{_WAVE}\n"),
    )
    fake.expect_run(
        _STATUS_ARGV,
        DW._CommandResult(0, ""),
    )
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_READY_ARGV, DW._CommandResult(0, ""))


def _prerun_status(
    fake: _FakeEffects,
    *,
    stdout: str = "",
    returncode: int = 0,
) -> None:
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(returncode, stdout))
    if returncode == 0 and not stdout:
        _fingerprint(fake)


def _fingerprint(fake: _FakeEffects, head: str = _SHA_A) -> None:
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, head + "\n"))
    fake.expect_run(_DIFF_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_STATUS_ARGV, DW._CommandResult(0, ""))


def _postrun_integrity(fake: _FakeEffects, head: str = _SHA_A) -> None:
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    _fingerprint(fake, head)


def _provenance(fake: _FakeEffects, result: object = None) -> None:
    fake.expect_run(
        _provenance_argv(),
        DW._CommandResult(0) if result is None else result,
    )


_PREFLIGHT_EVENTS = [
    ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
    ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
    ("run", ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), _REPO, True),
    ("run", _STATUS_ARGV, _REPO, True),
    ("run", _INDEX_FLAGS_ARGV, _REPO, True),
    ("run", _SUBMODULE_INDEX_FLAGS_ARGV, _REPO, True),
    ("run", _SUBMODULE_READY_ARGV, _REPO, True),
]
_FINGERPRINT_EVENTS = [
    ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
    ("run", _DIFF_ARGV, _REPO, True),
    ("run", _SUBMODULE_STATUS_ARGV, _REPO, True),
]
_POSTRUN_INTEGRITY_EVENTS = [
    ("run", _STATUS_ARGV, _REPO, True),
    ("run", _INDEX_FLAGS_ARGV, _REPO, True),
    ("run", _SUBMODULE_INDEX_FLAGS_ARGV, _REPO, True),
    *_FINGERPRINT_EVENTS,
]


def _claim(fake: _FakeEffects, sha: str, payload: str) -> None:
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, sha + "\n"))
    fake.expect_run(_helper("claim", sha), DW._CommandResult(0, payload))


def _acquired_payload(*, main_sha: str = _SHA_A) -> str:
    return json.dumps(
        {
            "state": "acquired",
            "holder": _HOLDER,
            "holder_self": True,
            "main_sha": main_sha,
            "age_seconds": 0,
            "source": {"status": "ok", "reason": None},
        }
    )


def _acquired(fake: _FakeEffects, sha: str = _SHA_A) -> None:
    _claim(fake, sha, _acquired_payload(main_sha=sha))


def _held_self_payload(**overrides: object) -> str:
    payload: dict[str, object] = {
        "state": "held-self",
        "holder": _HOLDER,
        "holder_self": True,
        "main_sha": _SHA_A,
        "age_seconds": 0,
        "source": {"status": "ok", "reason": None},
    }
    payload.update(overrides)
    return json.dumps(payload)


def _checker_argv() -> tuple[str, ...]:
    return (
        sys.executable,
        str(_REPO / "tools" / "check_acceptance_reds.py"),
        "--log",
        str(_LOG),
        "--tested-main",
        _SHA_A,
        "--wave-tip",
        _SHA_A,
        "--receipt",
        str(_CHECKER_RECEIPT),
        "--probe-root",
        str(_LOG.parent),
    )


def _checker_receipt_bytes(
    fake: _FakeEffects,
    *,
    status: str,
    nodes: list[dict[str, object]],
    log_sha256: str | None = None,
) -> bytes:
    return (
        json.dumps(
            {
                "log_path": str(_LOG),
                "log_sha256": (
                    hashlib.sha256(fake.logged_bytes).hexdigest()
                    if log_sha256 is None
                    else log_sha256
                ),
                "nodes": nodes,
                "schema_version": "izanagi-acceptance-red-check/v1",
                "status": status,
                "submodules": [],
                "tested_main": _SHA_A,
                "wave_tip": _SHA_A,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("ascii")


def _queue_checker(
    fake: _FakeEffects,
    *,
    rc: int = 0,
    status: str = "non-attributable-only",
    nodes: list[dict[str, object]] | None = None,
    log_sha256: str | None = None,
) -> bytes:
    fake.expect_run(_checker_argv(), DW._CommandResult(rc), capture=False)
    raw = _checker_receipt_bytes(
        fake,
        status=status,
        nodes=(
            [{
                "classification": "non-attributable",
                "nodeid": "orchestrator/tests/test_known.py::test_known",
                "rerun_rc": 1,
            }]
            if nodes is None
            else nodes
        ),
        log_sha256=log_sha256,
    )
    fake.byte_files[_CHECKER_RECEIPT] = raw
    return raw


def _queue_non_attributable_receipt_tail(fake: _FakeEffects) -> None:
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/check_acceptance_reds.py"),
        DW._CommandResult(0, _CHECKER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _held_self_payload()),
    )


_SUCCESS_RECEIPT_EVENTS = [
    (
        "run",
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        _REPO,
        True,
    ),
    ("write_receipt_temp", _RECEIPT),
    ("run", ("git", "rev-parse", "main"), _REPO, True),
    ("run", _helper("claim", _SHA_A), _REPO, True),
    ("rename", _RECEIPT_TEMP, _RECEIPT),
]


def _lease_marker(tmp_path: Path) -> tuple[Path, Path, tuple[int, bytes]]:
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    lease_path = lease_dir / "acceptance.lease"
    lease_path.write_text(
        json.dumps(
            {
                "holder": _HOLDER,
                "main_sha": _SHA_A,
                "ttl": 2400,
            }
        )
        + "\n",
        encoding="ascii",
    )
    os.utime(lease_path, ns=(1_900_000_000_000_000_000,) * 2)
    before = (lease_path.stat().st_mtime_ns, lease_path.read_bytes())
    return lease_dir, lease_path, before


def _write_test_provenance_checker(repo: Path) -> None:
    checker = repo / "tools" / "check_ai_provenance.py"
    checker.write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        "parser=argparse.ArgumentParser()\n"
        "parser.add_argument('--message-file', type=Path, required=True)\n"
        "args=parser.parse_args()\n"
        "expected='AI-Agent: product=codex; model=gpt-5; reasoning=high; "
        "role=author'\n"
        "raise SystemExit(0 if expected in args.message_file.read_text() else 1)\n",
        encoding="utf-8",
    )


def _real_waiter_repo(
    tmp_path: Path,
    *,
    wave: str,
) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / f"repo-{wave}"
    lease = tmp_path / f"lease-{wave}"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    (tools / "run_tests.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    env = {
        **{
            key: value
            for key, value in os.environ.items()
            if key not in DW._GIT_ENV_KEYS
            and key not in {
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "IZANAGI_TASK_RUN_ID",
                "IZANAGI_TASK_RUNS_ROOT",
            }
        },
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=repo,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    git("init", "-b", "main")
    git("add", "tools")
    git("commit", "-m", "base")
    git("checkout", "-b", f"worktree-{wave}")
    return repo, lease, env


def _release(fake: _FakeEffects, result: object = None) -> None:
    fake.expect_run(
        _helper("release"),
        DW._CommandResult(0, _RELEASE_JSON) if result is None else result,
    )


def _abort_clean(fake: _FakeEffects, result: object = None) -> None:
    fake.expect_run(
        ("git", "merge", "--abort"),
        DW._CommandResult(0) if result is None else result,
    )
    fake.expect_run(
        ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
        DW._CommandResult(1),
    )
    fake.expect_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        DW._CommandResult(0, ""),
    )


_ABORT_CLEAN_EVENTS = [
    ("run", ("git", "merge", "--abort"), _REPO, True),
    (
        "run",
        ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
        _REPO,
        True,
    ),
    (
        "run",
        ("git", "status", "--porcelain", "--untracked-files=no"),
        _REPO,
        True,
    ),
]


def _run_acceptance(
    fake: _FakeEffects,
    *,
    message: Path | None = None,
    max_wait: int = 7200,
    owned_paths: tuple[Path, ...] = (),
    lease_dir: Path = _LEASE,
    lifecycle: object = None,
    receipt_file: Path = _RECEIPT,
    log_file: Path = _LOG,
) -> object:
    return DW.run_acceptance(
        wave=_WAVE,
        lease_dir=lease_dir,
        merge_message_file=message,
        poll_seconds=30,
        max_wait_seconds=max_wait,
        command=_COMMAND,
        repo=_REPO,
        effects=fake.effects,
        receipt_file=receipt_file,
        log_file=log_file,
        owned_paths=owned_paths,
        lifecycle=lifecycle,
    )


def _queue_clean_acceptance_prefix(
    fake: _FakeEffects,
    *,
    claim_payload: str | None = None,
) -> None:
    _preflight(fake)
    _claim(
        fake,
        _SHA_A,
        _acquired_payload() if claim_payload is None else claim_payload,
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake)


class _RoutingAcceptanceEffects(_FakeEffects):
    def __init__(
        self,
        *,
        branch: str = f"feature-{_WAVE}",
        behind: list[int] | None = None,
        message: str = "merge\nAI-Agent: codex\n",
        head_shas: list[str] | None = None,
        changed_paths: str = "",
        claim_payload: str | None = None,
        command_result: object = None,
        postclaim_rc: int = 0,
        merge_result: object = None,
        provenance_result: object = None,
        lease_dir: Path = _LEASE,
        remove_lease_on_release: bool = False,
    ) -> None:
        super().__init__()
        self.branch = branch
        self.behind = list([0] if behind is None else behind)
        self.message = message
        self.head_shas = list([] if head_shas is None else head_shas)
        self.last_head_sha = self.head_shas[-1] if self.head_shas else _SHA_A
        self.changed_paths = changed_paths
        self.claim_payload = (
            _acquired_payload() if claim_payload is None else claim_payload
        )
        self.command_result = (
            DW._CommandResult(0) if command_result is None else command_result
        )
        self.postclaim_rc = postclaim_rc
        self.merge_result = (
            DW._CommandResult(0) if merge_result is None else merge_result
        )
        self.provenance_result = (
            DW._CommandResult(0)
            if provenance_result is None
            else provenance_result
        )
        self.lease_dir = lease_dir
        self.remove_lease_on_release = remove_lease_on_release
        self.claims = 0
        self.releases = 0
        self.submissions = 0
        self.main_reads = 0

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        self.events.append(("run", actual, cwd, capture))
        if actual == ("git", "rev-parse", "--is-inside-work-tree"):
            return DW._CommandResult(0, "true\n")
        if actual == ("git", "rev-parse", "--show-toplevel"):
            return DW._CommandResult(0, str(_REPO) + "\n")
        if actual == ("git", "symbolic-ref", "--quiet", "--short", "HEAD"):
            return DW._CommandResult(0, self.branch + "\n")
        if actual in {
            _STATUS_ARGV,
            _LEGACY_STATUS_ARGV,
        }:
            return DW._CommandResult(0, "")
        if actual in {_INDEX_FLAGS_ARGV, _SUBMODULE_INDEX_FLAGS_ARGV}:
            return DW._CommandResult(0, "")
        if actual == ("git", "rev-parse", "main"):
            self.main_reads += 1
            if self.main_reads == 2 and self.postclaim_rc != 0:
                return DW._CommandResult(self.postclaim_rc)
            return DW._CommandResult(0, _SHA_A + "\n")
        if actual == _helper("claim", _SHA_A, lease_dir=self.lease_dir):
            self.claims += 1
            if self.claims == 1:
                return DW._CommandResult(0, self.claim_payload)
            return DW._CommandResult(
                0,
                _held_self_payload(main_sha=_SHA_A),
            )
        if actual == ("git", "rev-list", "--count", "HEAD..main"):
            assert self.behind
            return DW._CommandResult(0, f"{self.behind.pop(0)}\n")
        if actual == ("git", "diff", "--name-only", "HEAD...main"):
            return DW._CommandResult(0, self.changed_paths)
        if actual == ("git", "merge", "--no-ff", "--no-commit", "main"):
            return self.merge_result
        if actual == _provenance_argv():
            return self.provenance_result
        if actual in {
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        }:
            return DW._CommandResult(0)
        if actual == ("git", "rev-parse", "HEAD"):
            if self.head_shas:
                self.last_head_sha = self.head_shas.pop(0)
            return DW._CommandResult(0, self.last_head_sha + "\n")
        if actual == (
            "git",
            "rev-parse",
            f"{self.last_head_sha}:tools/dev_wave_wait.py",
        ):
            return DW._CommandResult(0, _WAITER_BLOB + "\n")
        if actual == _helper(
            "claim",
            self.last_head_sha,
            lease_dir=self.lease_dir,
        ):
            self.claims += 1
            return DW._CommandResult(
                0,
                _held_self_payload(main_sha=self.last_head_sha),
            )
        if actual in {_DIFF_ARGV, _SUBMODULE_STATUS_ARGV}:
            return DW._CommandResult(0, "")
        if actual[:4] == ("git", "log", "-1", "--format=%B"):
            return DW._CommandResult(0, self.message)
        if actual == _COMMAND:
            self.submissions += 1
            if isinstance(self.command_result, BaseException):
                raise self.command_result
            return self.command_result
        if (
            len(actual) >= 2
            and Path(actual[1]).name == "check_acceptance_reds.py"
        ):
            def option(name: str) -> str:
                return actual[actual.index(name) + 1]

            checker_receipt = Path(option("--receipt"))
            self.byte_files[checker_receipt] = (
                json.dumps(
                    {
                        "log_path": option("--log"),
                        "log_sha256": hashlib.sha256(self.logged_bytes).hexdigest(),
                        "nodes": [],
                        "schema_version": "izanagi-acceptance-red-check/v1",
                        "status": "green",
                        "submodules": [],
                        "tested_main": option("--tested-main"),
                        "wave_tip": option("--wave-tip"),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("ascii")
            return DW._CommandResult(0)
        if actual == _helper("release", lease_dir=self.lease_dir):
            self.releases += 1
            lease_path = self.lease_dir / "acceptance.lease"
            if self.remove_lease_on_release and lease_path.exists():
                lease_path.unlink()
            return DW._CommandResult(0, _RELEASE_JSON)
        if actual == ("git", "merge", "--abort"):
            return DW._CommandResult(0)
        if actual == ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"):
            return DW._CommandResult(1)
        raise AssertionError(f"unexpected run: {actual}")

    def is_file(self, path: Path) -> bool:
        self.events.append(("is_file", path))
        return True

    def read_text(self, path: Path) -> str:
        self.events.append(("read_text", path))
        return self.message


class _SubmoduleDirtyAcceptanceEffects(_RoutingAcceptanceEffects):
    def __init__(self, *, dirty_status_call: int) -> None:
        super().__init__(behind=[0, 0])
        self.dirty_status_call = dirty_status_call
        self.status_reads = 0

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        if actual in {_STATUS_ARGV, _LEGACY_STATUS_ARGV}:
            self.events.append(("run", actual, cwd, capture))
            self.status_reads += 1
            if (
                actual == _STATUS_ARGV
                and self.status_reads == self.dirty_status_call
            ):
                return DW._CommandResult(0, " m external/ccbench\n")
            return DW._CommandResult(0, "")
        return super().run(argv, cwd, capture)


def test_floor_job_staging_is_ignored_while_submissions_remain_tracked() -> None:
    lines = (_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    staging_pattern = "output/env/pegasus/floor/job-staging/"
    predecessor = "output/env/pegasus/silo_ladder_rung1/job-staging/"
    assert lines.count(staging_pattern) == 1
    assert lines.index(staging_pattern) == lines.index(predecessor) + 1
    assert [line for line in lines if "output/env/pegasus/floor/" in line] == [
        staging_pattern
    ]

    representative_relative = (
        staging_pattern + "0:873200.nqsv/hostname.stdout"
    )
    staging = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", representative_relative],
        cwd=_ROOT,
        check=False,
    )
    submissions = subprocess.run(
        [
            "git", "check-ignore", "--no-index", "-q", "--",
            "output/env/pegasus/floor/attempts/submissions/probe",
        ],
        cwd=_ROOT,
        check=False,
    )
    tracked_submissions = subprocess.run(
        [
            "git", "ls-files", "--",
            "output/env/pegasus/floor/attempts/submissions",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    tracked_staging = subprocess.run(
        ["git", "ls-files", "--", staging_pattern],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert staging.returncode == 0
    assert submissions.returncode == 1
    assert tracked_staging.returncode == 0
    assert tracked_staging.stdout == ""
    assert tracked_submissions.returncode == 0
    assert tracked_submissions.stdout


@pytest.mark.parametrize(
    ("prefix", "entry"),
    [("-", "external/uninitialized"), ("U", "external/conflicted")],
    ids=("uninitialized", "conflict"),
)
def test_submodule_not_ready_is_rejected_before_claim(
    prefix: str,
    entry: str,
) -> None:
    fake = _FakeEffects()
    fake.expect_run(
        ("git", "rev-parse", "--is-inside-work-tree"),
        DW._CommandResult(0, "true\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "--show-toplevel"),
        DW._CommandResult(0, str(_REPO) + "\n"),
    )
    fake.expect_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        DW._CommandResult(0, f"feature-{_WAVE}\n"),
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(
        _SUBMODULE_READY_ARGV,
        DW._CommandResult(0, f"{prefix}{_SHA_A} {entry}\n"),
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "preflight-submodule-ready")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_preflight_untracked_dirty_rejects_before_claim(tmp_path: Path) -> None:
    wave = "real-untracked"
    repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
    (repo / "untracked.py").write_text("foreign\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "dev_wave_wait.py"),
            "acceptance",
            "--wave",
            wave,
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(tmp_path / "untracked-receipt.json"),
            "--log-file",
            str(tmp_path / "untracked.log"),
            "--",
            "python3",
            "tools/run_tests.py",
        ],
        cwd=repo,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert "stage=preflight-clean rc=2" in completed.stderr
    assert not (lease / "acceptance.lease").exists()
    assert not (tmp_path / "untracked-receipt.json").exists()


def test_prerun_untracked_dirty_blocks_submission_and_releases() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_A + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake, stdout="?? untracked.py\n")
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    fake.assert_drained()


@pytest.mark.parametrize("tag", ["S", "h"], ids=("skip-worktree", "assume-unchanged"))
@pytest.mark.parametrize("source", ["root", "submodule"])
@pytest.mark.parametrize("phase", ["preflight", "postrun"])
def test_index_flags_fail_closed_before_claim_and_after_run(
    tag: str,
    source: str,
    phase: str,
) -> None:
    fake = _FakeEffects()
    flagged = f"{tag} hidden.py\0"
    if phase == "preflight":
        fake.expect_run(
            ("git", "rev-parse", "--is-inside-work-tree"),
            DW._CommandResult(0, "true\n"),
        )
        fake.expect_run(
            ("git", "rev-parse", "--show-toplevel"),
            DW._CommandResult(0, str(_REPO) + "\n"),
        )
        fake.expect_run(
            ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
            DW._CommandResult(0, f"feature-{_WAVE}\n"),
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(
            _INDEX_FLAGS_ARGV,
            DW._CommandResult(0, flagged if source == "root" else ""),
        )
        if source == "submodule":
            fake.expect_run(
                _SUBMODULE_INDEX_FLAGS_ARGV,
                DW._CommandResult(0, flagged),
            )
    else:
        _queue_clean_acceptance_prefix(fake)
        fake.expect_run(
            _COMMAND,
            DW._CommandResult(0),
            capture=False,
            unchanged_postrun=False,
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(
            _INDEX_FLAGS_ARGV,
            DW._CommandResult(0, flagged if source == "root" else ""),
        )
        if source == "submodule":
            fake.expect_run(
                _SUBMODULE_INDEX_FLAGS_ARGV,
                DW._CommandResult(0, flagged),
            )
        _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == f"{phase}-index-flags"
    if phase == "preflight":
        assert not any(
            event[0] == "run" and event[1] == _helper("claim", _SHA_A)
            for event in fake.events
        )
        assert not any(
            event[0] == "run" and event[1] == _COMMAND
            for event in fake.events
        )
    else:
        assert ("run", _COMMAND, _REPO, False) in fake.events
        assert ("run", _helper("release"), _REPO, True) in fake.events
    fake.assert_drained()


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        ("tracked", " M tracked.py\n"),
        ("untracked", "?? untracked.py\n"),
        ("submodule", " m external/ccbench\n"),
    ],
)
def test_postrun_dirty_fails_closed_and_releases(
    kind: str,
    status: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    del kind
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, status))
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-clean"
    child_index = fake.events.index(("run", _COMMAND, _REPO, False))
    assert child_index < fake.events.index(
        ("run", _STATUS_ARGV, _REPO, True),
        child_index + 1,
    )
    assert status.strip() in capsys.readouterr().err
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


def test_postrun_clean_head_change_fails_fingerprint_and_releases() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake, _SHA_B)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-fingerprint"
    fake.assert_drained()


@pytest.mark.parametrize("component", ["diff", "submodule-status"])
def test_postrun_fingerprint_binds_diff_and_submodule_status(
    component: str,
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(
        ("git", "rev-parse", "HEAD"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _DIFF_ARGV,
        DW._CommandResult(0, "binary patch\n" if component == "diff" else ""),
    )
    fake.expect_run(
        _SUBMODULE_STATUS_ARGV,
        DW._CommandResult(
            0,
            f" {_SHA_B} external/ccbench\n"
            if component == "submodule-status"
            else "",
        ),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-fingerprint"
    fake.assert_drained()


def test_fingerprint_length_framing_disambiguates_concatenated_inputs() -> None:
    first = _FakeEffects()
    first.expect_run(
        ("git", "rev-parse", "HEAD"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    first.expect_run(_DIFF_ARGV, DW._CommandResult(0, "bc"))
    first.expect_run(_SUBMODULE_STATUS_ARGV, DW._CommandResult(0, ""))
    second = _FakeEffects()
    second.expect_run(
        ("git", "rev-parse", "HEAD"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    second.expect_run(_DIFF_ARGV, DW._CommandResult(0, "c"))
    second.expect_run(_SUBMODULE_STATUS_ARGV, DW._CommandResult(0, ""))

    first_fingerprint = DW._tree_fingerprint(
        first.effects,
        _REPO,
        "fingerprint-test",
        "a",
    )
    second_fingerprint = DW._tree_fingerprint(
        second.effects,
        _REPO,
        "fingerprint-test",
        "ab",
    )

    assert first_fingerprint.digest != second_fingerprint.digest
    assert first_fingerprint.status_bytes == 1
    assert second_fingerprint.status_bytes == 2
    first.assert_drained()
    second.assert_drained()


@pytest.mark.parametrize("phase", ["prerun", "postrun"])
def test_fingerprint_git_command_failure_fails_closed_and_releases(
    phase: str,
) -> None:
    fake = _FakeEffects()
    if phase == "prerun":
        _preflight(fake)
        _acquired(fake)
        fake.expect_run(
            ("git", "rev-parse", "main"),
            DW._CommandResult(0, _SHA_A + "\n"),
        )
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(0, "0\n"),
        )
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(0, "0\n"),
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(9))
    else:
        _queue_clean_acceptance_prefix(fake)
        fake.expect_run(
            _COMMAND,
            DW._CommandResult(0),
            capture=False,
            unchanged_postrun=False,
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(9))
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == f"{phase}-fingerprint"
    assert outcome.source_rc == 9
    fake.assert_drained()


def test_nonzero_child_is_postchecked_before_propagation() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(23), capture=False)
    _queue_checker(fake, status="green", nodes=[])
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-red-check"
    child_index = fake.events.index(("run", _COMMAND, _REPO, False))
    release_index = fake.events.index(("run", _helper("release"), _REPO, True))
    assert ("run", _INDEX_FLAGS_ARGV, _REPO, True) in fake.events[child_index:release_index]
    fake.assert_drained()


def test_postrun_dirty_overrides_nonzero_child_rc() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(23),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, "?? child-output\n"))
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-clean"
    fake.assert_drained()


def test_held_self_postrun_dirty_retains_lease() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake, claim_payload=_held_self_payload())
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, " M tracked.py\n"))

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-clean"
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_unchanged_postrun_fingerprint_allows_success_and_retains_lease() -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_success_receipt_binds_tip_argv_rc_fingerprints_holder_and_waiter_blob(
) -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert lifecycle.receipt_published is True
    assert fake.receipt_published is True
    receipt = json.loads(fake.receipt_content)
    assert set(receipt) == {
        "schema_version", "authority_kind", "acceptance_wave", "lease_holder",
        "tested_main", "tested_tip", "argv", "resolved_runner_path", "child_rc",
        "pre_fingerprint", "post_fingerprint", "waiter_blob_sha",
        "env_projection", "verdict", "log_sha256", "checker_rc",
        "checker_status", "checker_blob_sha", "checker_receipt_sha256",
        "red_nodeids",
    }
    assert receipt["schema_version"] == "dev-wave-acceptance-receipt/v2"
    assert receipt["authority_kind"] == "dev-wave-wait-acceptance"
    assert receipt["acceptance_wave"] == _WAVE
    assert receipt["lease_holder"] == _HOLDER
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_A
    assert receipt["argv"] == list(_COMMAND)
    assert receipt["resolved_runner_path"] == "--flag"
    assert receipt["child_rc"] == 0
    assert receipt["pre_fingerprint"] == receipt["post_fingerprint"]
    assert receipt["pre_fingerprint"]["head_sha"] == _SHA_A
    assert receipt["waiter_blob_sha"] == _WAITER_BLOB
    assert receipt["verdict"] == "child-green"
    assert receipt["log_sha256"] == hashlib.sha256(b"").hexdigest()
    assert receipt["checker_rc"] is None
    assert receipt["checker_status"] is None
    assert receipt["checker_blob_sha"] is None
    assert receipt["checker_receipt_sha256"] is None
    assert receipt["red_nodeids"] == []
    assert receipt["env_projection"] == {
        "PYTEST_ADDOPTS": None,
        "PYTEST_PLUGINS": None,
        "IZANAGI_TASK_RUN_ID": None,
        "IZANAGI_TASK_RUNS_ROOT": None,
    }
    fake.assert_drained()


@pytest.mark.parametrize("child_rc", [1, 23], ids=("one", "audit-shaped"))
def test_failed_acceptance_never_publishes_receipt(child_rc: int) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(child_rc), capture=False)
    _queue_checker(fake, status="green", nodes=[])
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-red-check")
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


@pytest.mark.parametrize("checker_rc", [1, 2], ids=("attributable", "unknown"))
def test_failed_acceptance_rejects_nonzero_checker_rc(checker_rc: int) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
    _queue_checker(fake, rc=checker_rc)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(
        70,
        "acceptance-red-check",
        checker_rc,
    )
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


def test_non_attributable_only_publishes_receipt_with_real_child_rc() -> None:
    fake = _FakeEffects()
    fake.logged_bytes = b"synthetic failing pytest log\n"
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
    checker_raw = _queue_checker(fake)
    _queue_non_attributable_receipt_tail(fake)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome == DW._Outcome(0)
    receipt = json.loads(fake.receipt_content)
    assert receipt["verdict"] == "non-attributable-only"
    assert receipt["child_rc"] == 1
    assert receipt["checker_rc"] == 0
    assert receipt["checker_status"] == "non-attributable-only"
    assert receipt["checker_blob_sha"] == _CHECKER_BLOB
    assert receipt["checker_receipt_sha256"] == hashlib.sha256(
        checker_raw
    ).hexdigest()
    assert receipt["red_nodeids"] == [
        "orchestrator/tests/test_known.py::test_known"
    ]
    assert receipt["log_sha256"] == hashlib.sha256(fake.logged_bytes).hexdigest()
    fake.assert_drained()


def test_checker_receipt_log_hash_mismatch_is_rejected() -> None:
    fake = _FakeEffects()
    fake.logged_bytes = b"owned log bytes\n"
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
    _queue_checker(fake, log_sha256=hashlib.sha256(b"other log").hexdigest())
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-red-check")
    assert fake.receipt_content is None
    fake.assert_drained()


@pytest.mark.parametrize(
    "field",
    ("schema_version", "wave_tip", "tested_main", "classification"),
)
def test_checker_receipt_identity_and_nodes_are_bound(field: str) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
    checker_raw = _queue_checker(fake)
    payload = json.loads(checker_raw)
    if field == "schema_version":
        payload[field] = "izanagi-acceptance-red-check/v0"
    elif field in {"wave_tip", "tested_main"}:
        payload[field] = _SHA_B
    else:
        payload["nodes"][0][field] = "attributable"
    fake.byte_files[_CHECKER_RECEIPT] = (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-red-check")
    assert fake.receipt_content is None
    fake.assert_drained()


@pytest.mark.parametrize(
    "postcheck",
    ("postrun-clean", "postrun-index-flags", "postrun-fingerprint"),
)
def test_postrun_failure_prevents_red_checker(postcheck: str) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(1),
        capture=False,
        unchanged_postrun=False,
    )
    if postcheck == "postrun-clean":
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, " M changed.py\n"))
    elif postcheck == "postrun-index-flags":
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, "S hidden.py\0"))
    else:
        _postrun_integrity(fake, head=_SHA_B)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, postcheck)
    assert not any(event[0] == "run" and event[1] == _checker_argv()
                   for event in fake.events)
    fake.assert_drained()


def test_receipt_publish_failure_is_fail_closed_and_releases() -> None:
    fake = _FakeEffects()
    fake.rename_result = OSError("rename failed")
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-receipt")
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    assert ("run", _helper("release"), _REPO, True) in fake.events
    fake.assert_drained()


def test_receipt_requires_sufficient_lease_ttl_and_releases() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(
            0,
            _held_self_payload(age_seconds=2101),
        ),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-receipt")
    assert fake.receipt_content is not None
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_receipt_reconfirms_same_lease_holder_before_publish() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, json.dumps({"state": "held"})),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-receipt")
    assert fake.receipt_content is not None
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_held_self_reacquired_before_receipt_is_released_once() -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(
        fake,
        claim_payload=_held_self_payload(),
    )
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _acquired_payload()),
    )
    _release(fake)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome == DW._Outcome(70, "acceptance-receipt")
    assert fake.events.count(("run", _helper("release"), _REPO, True)) == 1
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_signal_before_receipt_publish_leaves_no_final_and_releases() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._SignalReceived(signal.SIGTERM),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(143, "signal-15")
    assert fake.receipt_published is False
    assert _RECEIPT not in fake.existing_paths
    assert fake.events.index(("write_receipt_temp", _RECEIPT)) < max(
        index
        for index, event in enumerate(fake.events)
        if event == ("run", ("git", "rev-parse", "main"), _REPO, True)
    )
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_signal_after_receipt_publish_does_not_reverse_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    real_sigmask = DW.signal.pthread_sigmask

    def delayed_signal(how: int, signals: object):
        if how == signal.SIG_SETMASK:
            raise DW._SignalReceived(signal.SIGTERM)
        return real_sigmask(how, signals)

    monkeypatch.setattr(DW.signal, "pthread_sigmask", delayed_signal)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.receipt_published is True
    assert fake.receipt_published is True
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    fake.assert_drained()


@pytest.mark.parametrize(
    "case",
    ["inside-repo", "existing", "missing-parent", "reserved-temp-name"],
)
def test_receipt_path_rejected_before_claim(case: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    if case == "inside-repo":
        receipt = _REPO / "receipt.json"
    elif case == "reserved-temp-name":
        receipt = _RECEIPT.parent / ".dev-wave-acceptance-receipt-final.json"
    else:
        receipt = _RECEIPT
    if case == "existing":
        fake.existing_paths.add(receipt)
    if case == "missing-parent":
        fake.directories.clear()

    outcome = _run_acceptance(fake, receipt_file=receipt)

    assert outcome == DW._Outcome(2, "acceptance-receipt-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_existing_log_path_is_rejected_before_claim() -> None:
    fake = _FakeEffects()
    fake.existing_paths.add(_LOG)
    _preflight(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-log-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    "case",
    ("existing-checker-receipt", "symlink-probe-root"),
)
def test_red_checker_paths_are_rejected_before_claim(case: str) -> None:
    fake = _FakeEffects()
    if case == "existing-checker-receipt":
        fake.existing_paths.add(_CHECKER_RECEIPT)
    else:
        fake.symlinks.add(_LOG.parent)
    _preflight(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-red-check-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("PYTEST_ADDOPTS", "-k nothing"),
        ("PYTEST_PLUGINS", "foreign_plugin"),
        ("IZANAGI_TASK_RUN_ID", "run-inside-repo"),
    ],
)
def test_acceptance_environment_rejected_before_claim(key: str, value: str) -> None:
    fake = _FakeEffects()
    fake.env[key] = value
    _preflight(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-env-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_real_pytest_addopts_is_rejected_before_claim(tmp_path: Path) -> None:
    wave = "real-env-closed"
    repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
    env["PYTEST_ADDOPTS"] = "-k nothing"
    receipt = tmp_path / "env-receipt.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "dev_wave_wait.py"),
            "acceptance",
            "--wave",
            wave,
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(receipt),
            "--log-file",
            str(tmp_path / "env.log"),
            "--",
            "python3",
            "tools/run_tests.py",
        ],
        cwd=repo,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert "stage=acceptance-env-preflight rc=2" in completed.stderr
    assert not (lease / "acceptance.lease").exists()
    assert not receipt.exists()


def test_pid_probe_calls_kill_zero_for_exact_pid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = 4321
    subprocesses: list[tuple[object, ...]] = []
    events: list[tuple[object, ...]] = []

    def run(argv: object, cwd: Path, capture: bool) -> object:
        subprocesses.append((tuple(argv), cwd, capture))
        return DW._CommandResult(1)

    def direct_run(argv: object, **kwargs: object) -> object:
        subprocesses.append((tuple(argv), kwargs))
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(DW.subprocess, "run", direct_run)

    def read_text(path: Path) -> str:
        events.append(("read_text", path))
        return _stat_text(pid, 9)

    def kill(actual_pid: int, signum: int) -> None:
        events.append(("kill", actual_pid, signum))
        raise ProcessLookupError(errno.ESRCH, "gone")

    def is_file(path: Path) -> bool:
        events.append(("is_file", path))
        return True

    effects = DW._Effects(
        run=run, run_unbounded=run, sleep=lambda seconds: events.append(("sleep", seconds)),
        kill=kill, is_file=is_file, read_text=read_text,
        getenv=lambda name: None, monotonic=lambda: events.append(("monotonic",)) or 0.0,
        write_temp=lambda content: _VALIDATED_MESSAGE, unlink=lambda path: None,
    )

    outcome = DW.wait_for_producer(
        done_file=Path("done"),
        artifact_file=Path("artifact"),
        pid=pid,
        max_wait_seconds=None,
        effects=effects,
    )

    assert outcome.rc == 0
    assert subprocesses == []
    assert events == [
        ("monotonic",),
        ("read_text", Path(f"/proc/{pid}/stat")),
        ("kill", pid, 0),
        ("is_file", Path("done")),
        ("is_file", Path("artifact")),
    ]


def test_producer_waits_while_pid_alive_then_completes_after_death() -> None:
    fake = _FakeEffects()
    pid = 42
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.extend(
        [(stat_path, _stat_text(pid, 11)), (stat_path, _stat_text(pid, 11))]
    )
    fake.kill_queue.extend([None, ProcessLookupError(errno.ESRCH, "gone")])
    fake.is_file_queue.extend([(Path("done"), True), (Path("artifact"), True)])

    outcome = DW.wait_for_producer(
        done_file=Path("done"),
        artifact_file=Path("artifact"),
        pid=pid,
        max_wait_seconds=None,
        effects=fake.effects,
    )

    assert outcome.rc == 0
    assert fake.events.count(("sleep", 5)) == 1
    fake.assert_drained()


@pytest.mark.parametrize("missing", ["done", "artifact"], ids=("done", "artifact"))
def test_producer_dead_without_required_file_fails_closed(missing: str) -> None:
    fake = _FakeEffects()
    pid = 55
    fake.read_text_queue.append((Path(f"/proc/{pid}/stat"), OSError("no proc")))
    fake.kill_queue.append(ProcessLookupError(errno.ESRCH, "gone"))
    for _ in range(7):
        fake.is_file_queue.append((Path("done"), missing != "done"))
        if missing != "done":
            fake.is_file_queue.append((Path("artifact"), False))

    outcome = DW.wait_for_producer(
        done_file=Path("done"),
        artifact_file=Path("artifact"),
        pid=pid,
        max_wait_seconds=None,
        effects=fake.effects,
    )

    assert outcome.rc == 70
    assert outcome.stage == "producer-files"
    file_events = [("is_file", Path("done"))]
    if missing == "artifact":
        file_events.append(("is_file", Path("artifact")))
    expected = [
        ("monotonic",),
        ("read_text", Path(f"/proc/{pid}/stat")),
        ("kill", pid, 0),
    ]
    for attempt in range(7):
        expected.extend(file_events)
        if attempt < 6:
            expected.append(("sleep", 5))
    fake.assert_drained(expected)


@pytest.mark.parametrize("source", ["direct", "pid-file"], ids=("direct", "pid-file"))
def test_producer_accepts_exactly_one_pid_source(source: str) -> None:
    fake = _FakeEffects()
    if source == "pid-file":
        fake.read_text_queue.append((Path("pid"), "123\n"))
    resolved = DW._resolve_pid(
        "123" if source == "direct" else None,
        Path("pid") if source == "pid-file" else None,
        fake.effects,
    )
    assert resolved == 123
    fake.assert_drained()


@pytest.mark.parametrize("source", ["neither", "both"], ids=("neither", "both"))
def test_producer_rejects_invalid_pid_source(source: str) -> None:
    fake = _FakeEffects()
    with pytest.raises(DW._StageFailure) as raised:
        DW._resolve_pid(
            "123" if source == "both" else None,
            Path("pid") if source == "both" else None,
            fake.effects,
        )
    assert raised.value.outcome.rc == 2
    fake.assert_drained([])


def test_producer_cli_surface_has_no_pattern_input(capsys: pytest.CaptureFixture[str]) -> None:
    parser = DW._producer_parser()
    expected_options = {
        "-h",
        "--help",
        "--done-file",
        "--artifact-file",
        "--pid",
        "--pid-file",
        "--max-wait-seconds",
    }
    actual_options = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    positional_actions = [action for action in parser._actions if not action.option_strings]
    assert actual_options == expected_options
    assert positional_actions == []

    base = ["producer", "--done-file", "d", "--artifact-file", "a", "--pid", "1"]
    for extra in (["--pattern", "X"], ["--match", "X"], ["unexpected"]):
        assert DW.main(base + extra) == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Traceback" not in captured.err


def test_producer_start_time_change_is_original_process_death() -> None:
    fake = _FakeEffects()
    pid = 99
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.extend(
        [(stat_path, _stat_text(pid, 1)), (stat_path, _stat_text(pid, 2))]
    )
    fake.kill_queue.append(None)
    fake.is_file_queue.extend([(Path("done"), True), (Path("artifact"), True)])
    outcome = DW.wait_for_producer(
        done_file=Path("done"), artifact_file=Path("artifact"), pid=pid,
        max_wait_seconds=None, effects=fake.effects,
    )
    assert outcome.rc == 0
    assert ("sleep", 5) not in fake.events
    fake.assert_drained()


def test_producer_zombie_is_dead_even_when_kill_zero_succeeds() -> None:
    fake = _FakeEffects()
    pid = 101
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.extend(
        [(stat_path, _stat_text(pid, 7)), (stat_path, _stat_text(pid, 7).replace(" S ", " Z ", 1))]
    )
    fake.kill_queue.append(None)
    fake.is_file_queue.extend([(Path("done"), True), (Path("artifact"), True)])

    outcome = DW.wait_for_producer(
        done_file=Path("done"), artifact_file=Path("artifact"), pid=pid,
        max_wait_seconds=None, effects=fake.effects,
    )

    assert outcome.rc == 0
    assert ("sleep", 5) not in fake.events
    fake.assert_drained()


def test_producer_file_visibility_grace_is_bounded() -> None:
    fake = _FakeEffects()
    pid = 100
    fake.read_text_queue.append((Path(f"/proc/{pid}/stat"), OSError("no proc")))
    fake.kill_queue.append(ProcessLookupError(errno.ESRCH, "gone"))
    fake.is_file_queue.extend(
        [
            (Path("done"), False),
            (Path("done"), True),
            (Path("artifact"), False),
            (Path("done"), True),
            (Path("artifact"), True),
        ]
    )
    outcome = DW.wait_for_producer(
        done_file=Path("done"), artifact_file=Path("artifact"), pid=pid,
        max_wait_seconds=None, effects=fake.effects,
    )
    assert outcome.rc == 0
    assert fake.events.count(("sleep", 5)) == 2
    fake.assert_drained()


@pytest.mark.parametrize(
    "state", ["held", "queued", "stale-held", "unavailable"],
    ids=("held", "queued", "stale-held", "unavailable"),
)
def test_acceptance_non_accepted_state_never_runs_command(state: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, json.dumps({"state": state}))
    if state in {"held", "queued"}:
        fake.monotonic_queue[:] = [0.0, 0.0]
    outcome = _run_acceptance(fake, max_wait=1)

    assert outcome.rc == 70
    expected = [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
    ]
    if state in {"held", "queued"}:
        expected.append(("monotonic",))
    assert fake.events == expected
    fake.assert_drained()


@pytest.mark.parametrize("age_seconds", [0, 7], ids=("zero-age", "observed-age"))
def test_acceptance_held_self_runs_command_without_polling(age_seconds: int) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(age_seconds=age_seconds),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_acceptance_real_acquired_payload_runs_command_and_releases_on_failure(
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_acquired_payload(),
        command_result=DW._CommandResult(23),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-red-check"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 1)
    assert fake.events.count(("sleep", 30)) == 0


def test_claim_once_real_acquired_payload_grants_acquired_ownership() -> None:
    fake = _FakeEffects()
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _acquired_payload()),
    )
    lifecycle = DW._AcceptanceLifecycle()

    claim = DW._claim_once(
        fake.effects,
        _REPO,
        _LEASE,
        _WAVE,
        _SHA_A,
        lifecycle,
    )

    assert claim == DW._ClaimContext("acquired", _HOLDER, _SHA_A, 0)
    assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED
    fake.assert_drained()


def test_acceptance_legacy_self_held_fails_closed_without_polling() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(
        fake,
        _SHA_A,
        json.dumps(
            {
                "state": "held",
                "holder": _HOLDER,
                "holder_self": True,
                "age_seconds": 1,
                "source": {"status": "ok", "reason": None},
            }
        ),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "claim-self-unverified"
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    "overrides",
    [
        {"holder_self": False},
        {"age_seconds": "0"},
        {"source": {"status": "unavailable", "reason": "lease-unavailable"}},
        {"holder": "not-a-holder"},
        {"source": {"status": "ok", "reason": None, "extra": "rejected"}},
        {"source": {"status": "ok"}},
        {"age_seconds": True},
        {"holder": "ABCDEF012345"},
    ],
    ids=(
        "holder-false",
        "age-non-int",
        "source-unavailable",
        "holder-non-hex",
        "source-extra-key",
        "source-missing-key",
        "age-bool",
        "holder-uppercase-hex",
    ),
)
def test_acceptance_invalid_held_self_fails_closed(
    overrides: dict[str, object],
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, _held_self_payload(**overrides))

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "claim-self-unverified"
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_public_main_self_renew_failure_reports_reason_without_poll_or_release(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(
        fake,
        _SHA_A,
        json.dumps(
            {
                "state": "unavailable",
                "holder": _HOLDER,
                "holder_self": True,
                "main_sha": _SHA_A,
                "age_seconds": 17,
                "source": {
                    "status": "unavailable",
                    "reason": "self-renew-failed",
                },
            }
        ),
    )

    rc = DW.main(
        [
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--receipt-file",
            str(_RECEIPT),
            "--log-file",
            str(_LOG),
            "--",
            *_COMMAND,
        ],
        effects=fake.effects,
        repo=_REPO,
    )
    captured = capsys.readouterr()

    assert rc == 70
    assert captured.out == ""
    assert captured.err.splitlines().count(
        "acceptance: held-self lease retained; "
        "this invocation has no release authority"
    ) == 1
    assert captured.err.splitlines().count(
        "error: stage=claim-self-renew-failed rc=70"
    ) == 1
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_acceptance_ignores_acquired_outside_top_level_state() -> None:
    payload = json.dumps(
        {"state": "held", "diagnostic": "acquired", "nested": {"state": "acquired"}}
    )

    class RoutingEffects(_FakeEffects):
        def __init__(self) -> None:
            super().__init__()
            self.submissions = 0

        def run(self, argv: object, cwd: Path, capture: bool) -> object:
            actual = tuple(argv)
            self.events.append(("run", actual, cwd, capture))
            if actual == ("git", "rev-parse", "--is-inside-work-tree"):
                return DW._CommandResult(0, "true\n")
            if actual == ("git", "rev-parse", "--show-toplevel"):
                return DW._CommandResult(0, str(_REPO) + "\n")
            if actual == ("git", "symbolic-ref", "--quiet", "--short", "HEAD"):
                return DW._CommandResult(0, f"feature-{_WAVE}\n")
            if actual == _STATUS_ARGV:
                return DW._CommandResult(0, "")
            if actual in {_INDEX_FLAGS_ARGV, _SUBMODULE_INDEX_FLAGS_ARGV}:
                return DW._CommandResult(0, "")
            if actual == ("git", "rev-parse", "main"):
                return DW._CommandResult(0, _SHA_A + "\n")
            if actual == _helper("claim", _SHA_A):
                return DW._CommandResult(0, payload)
            if actual == ("git", "rev-list", "--count", "HEAD..main"):
                return DW._CommandResult(0, "0\n")
            if actual == _COMMAND:
                self.submissions += 1
                return DW._CommandResult(0)
            if actual == _helper("release"):
                return DW._CommandResult(0, _RELEASE_JSON)
            raise AssertionError(f"unexpected run: {actual}")

    fake = RoutingEffects()
    _run_acceptance(fake, max_wait=1)

    assert fake.submissions == 0


def test_claim_once_uses_only_exact_top_level_state() -> None:
    fake = _FakeEffects()
    payload = json.dumps(
        {"state": "held", "diagnostic": "acquired", "nested": {"state": "acquired"}}
    )
    fake.expect_run(_helper("claim", _SHA_A), DW._CommandResult(0, payload))

    claim = DW._claim_once(fake.effects, _REPO, _LEASE, _WAVE, _SHA_A)

    assert claim.state == "held"
    assert fake.events == [("run", _helper("claim", _SHA_A), _REPO, True)]
    fake.assert_drained()


@pytest.mark.parametrize(
    ("case", "payload"),
    [
        ("malformed", "{"),
        ("duplicate-state", '{"state":"acquired","state":"held"}'),
        ("unknown-state", '{"state":"free"}'),
        ("non-string-state", '{"state":7}'),
        ("array", '["acquired"]'),
        ("scalar", '"acquired"'),
    ],
    ids=(
        "malformed", "duplicate-state", "unknown-state", "non-string-state",
        "array", "scalar",
    ),
)
def test_acceptance_rejects_claim_json(case: str, payload: str) -> None:
    del case
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, payload)
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_held_and_queued_refresh_main_before_every_claim() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.monotonic_queue[:] = [0.0, 0.0, 30.0]
    _claim(fake, _SHA_A, '{"state":"held"}')
    _claim(fake, _SHA_B, '{"state":"queued"}')
    _claim(fake, _SHA_C, _acquired_payload(main_sha=_SHA_C))
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 0
    claim_shas = [
        event[1][-1]
        for event in fake.events
        if event[0] == "run" and len(event[1]) > 2 and event[1][2] == "claim"
    ]
    assert claim_shas == [_SHA_A, _SHA_B, _SHA_C, _SHA_C]
    assert fake.events.count(("sleep", 30)) == 2
    assert not any(event[0] == "run" and event[1] == _helper("release") for event in fake.events)
    fake.assert_drained()


def test_acquired_reloads_main_before_behind_check() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake, _SHA_A)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 0
    rev_parse_outputs = [
        event for event in fake.events
        if event[0] == "run" and event[1] == ("git", "rev-parse", "main")
    ]
    # postclaim、behind 検査、rename 直前の再確認で main を計 3 回読む。
    assert len(rev_parse_outputs) == 3
    fake.assert_drained()


def test_merge_required_without_message_file_releases_before_submission() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize(
    ("owned_path", "changed_path"),
    [
        (Path("./docs/x.md"), "docs/x.md"),
        (Path("docs"), "docs/sub/x.md"),
    ],
    ids=("normalized-exact", "directory-child"),
)
def test_owned_path_overlap_blocks_before_merge_and_releases(
    owned_path: Path,
    changed_path: str,
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "1\n"),
    )
    fake.expect_run(
        ("git", "diff", "--name-only", "HEAD...main"),
        DW._CommandResult(0, changed_path + "\n"),
    )
    _release(fake)

    outcome = _run_acceptance(
        fake,
        message=_MESSAGE,
        owned_paths=(owned_path,),
    )

    assert outcome.rc == 70
    assert outcome.stage == "owned-path-overlap"
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        (
            "run",
            ("git", "rev-list", "--count", "HEAD..main"),
            _REPO,
            True,
        ),
        (
            "run",
            ("git", "diff", "--name-only", "HEAD...main"),
            _REPO,
            True,
        ),
        ("run", _helper("release"), _REPO, True),
    ]
    assert not any(
        event[0] == "run" and event[1][:2] == ("git", "merge")
        for event in fake.events
    )
    assert not any(
        event[0] == "run" and event[1] == _COMMAND for event in fake.events
    )
    fake.assert_drained()


def test_owned_path_diff_nonzero_fails_closed_and_releases() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "1\n"),
    )
    fake.expect_run(
        ("git", "diff", "--name-only", "HEAD...main"),
        DW._CommandResult(9),
    )
    _release(fake)

    outcome = _run_acceptance(
        fake,
        message=_MESSAGE,
        owned_paths=(Path("docs/x.md"),),
    )

    assert outcome.rc == 70
    assert outcome.stage == "owned-path-diff"
    assert outcome.source_rc == 9
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        (
            "run",
            ("git", "rev-list", "--count", "HEAD..main"),
            _REPO,
            True,
        ),
        (
            "run",
            ("git", "diff", "--name-only", "HEAD...main"),
            _REPO,
            True,
        ),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_owned_path_prefix_is_not_overlap_and_reaches_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
        changed_paths="docs/xy.md\n",
    )

    outcome = _run_acceptance(
        fake,
        message=_MESSAGE,
        owned_paths=(Path("docs/x.md"),),
    )

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    selected_calls = [
        event[1]
        for event in fake.events
        if event[0] == "run"
        and event[1]
        in {
            ("git", "diff", "--name-only", "HEAD...main"),
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            _provenance_argv(),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
    ]
    assert selected_calls == [
        ("git", "diff", "--name-only", "HEAD...main"),
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        _provenance_argv(),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        _COMMAND,
    ]


def test_missing_owned_path_skips_diff_warns_and_reaches_submission(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    assert not any(
        event[0] == "run"
        and event[1] == ("git", "diff", "--name-only", "HEAD...main")
        for event in fake.events
    )
    selected_calls = [
        event[1]
        for event in fake.events
        if event[0] == "run"
        and event[1]
        in {
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            _provenance_argv(),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
    ]
    assert selected_calls == [
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        _provenance_argv(),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        _COMMAND,
    ]
    warning = (
        "acceptance: --owned-path 未指定のため所有実装面 overlap 判定を省略します"
    )
    assert capsys.readouterr().err.splitlines().count(warning) == 1


def test_missing_message_preflight_does_not_release_foreign_lease() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, False))

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 2
    assert outcome.stage == "merge-message-preflight"
    assert fake.events == [*_PREFLIGHT_EVENTS, ("is_file", _MESSAGE)]
    fake.assert_drained()


def test_merge_sequence_and_postcheck_are_exact(capsys: pytest.CaptureFixture[str]) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.monotonic_queue[:] = [0.0, 100.0]
    fake.final_claim_age_seconds = 30
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "2\n"))
    fake.is_file_queue.append((_MESSAGE, True))
    fake.read_text_queue.append((_MESSAGE, "merge\n\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    _provenance(fake)
    fake.expect_run(("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(0, "merge\n\nAI-Agent: codex\n"),
    )
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 0
    git_mutations = [
        event[1]
        for event in fake.events
        if event[0] == "run" and event[1][:2] in {("git", "merge"), ("git", "commit")}
    ]
    assert git_mutations == [
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
    ]
    assert all("--ff-only" not in argv and "--no-edit" not in argv for argv in git_mutations)
    assert not any(event[0] == "run" and event[1] == _helper("release") for event in fake.events)
    captured = capsys.readouterr()
    assert "lease is held" in captured.out
    assert "TTL remaining at most 2370 seconds" in captured.out
    assert "exclusivity is lost after expiry" in captured.out
    assert "no fencing token" in captured.out
    assert "until land termination" not in captured.out
    assert "timeout=none" in captured.err
    assert ("unlink", _VALIDATED_MESSAGE) in fake.events
    fake.assert_drained()


_STAGES = (
    "preclaim-rev-parse",
    "claim",
    "postclaim-rev-parse",
    "behind-count",
    "merge",
    "merge-message-provenance",
    "commit-dry-run",
    "commit",
    "commit-rev-parse",
    "commit-message-postcheck",
    "postcheck",
    "commit-head-postcheck",
    "prerun-clean",
)


@pytest.mark.parametrize("stage", _STAGES, ids=_STAGES)
def test_nonzero_stage_blocks_submission_and_releases(stage: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    if stage == "preclaim-rev-parse":
        fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(9))
    else:
        fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_A + "\n"))
        fake.expect_run(
            _helper("claim", _SHA_A),
            DW._CommandResult(9)
            if stage == "claim"
            else DW._CommandResult(0, _acquired_payload()),
        )
    if stage not in {"preclaim-rev-parse", "claim"}:
        fake.expect_run(
            ("git", "rev-parse", "main"),
            DW._CommandResult(9) if stage == "postclaim-rev-parse" else DW._CommandResult(0, _SHA_B + "\n"),
        )
    if stage not in {"preclaim-rev-parse", "claim", "postclaim-rev-parse"}:
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(9) if stage == "behind-count" else DW._CommandResult(0, "1\n"),
        )
    merge_stages = {
        "merge", "merge-message-provenance", "commit-dry-run", "commit",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }
    if stage in merge_stages:
        fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
        fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
        fake.expect_run(
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            DW._CommandResult(9) if stage == "merge" else DW._CommandResult(0),
        )
    if stage in {
        "merge-message-provenance", "commit-dry-run", "commit",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        _provenance(
            fake,
            DW._CommandResult(9)
            if stage == "merge-message-provenance"
            else DW._CommandResult(0),
        )
    if stage in {
        "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        fake.expect_run(
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            DW._CommandResult(9) if stage == "commit-dry-run" else DW._CommandResult(0),
        )
    if stage in {
        "commit", "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        fake.expect_run(
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            DW._CommandResult(9) if stage == "commit" else DW._CommandResult(0),
        )
    if stage in {
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        fake.expect_run(
            ("git", "rev-parse", "HEAD"),
            DW._CommandResult(9) if stage == "commit-rev-parse"
            else DW._CommandResult(0, _SHA_C + "\n"),
        )
    if stage in {
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        fake.expect_run(
            ("git", "log", "-1", "--format=%B", _SHA_C),
            DW._CommandResult(9) if stage == "commit-message-postcheck"
            else DW._CommandResult(0, "merge\nAI-Agent: codex\n"),
        )
    if stage in {"postcheck", "commit-head-postcheck", "prerun-clean"}:
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(9) if stage == "postcheck"
            else DW._CommandResult(0, "0\n"),
        )
    if stage in {"commit-head-postcheck", "prerun-clean"}:
        fake.expect_run(
            ("git", "rev-parse", "HEAD"),
            DW._CommandResult(9)
            if stage == "commit-head-postcheck"
            else DW._CommandResult(0, _SHA_C + "\n"),
        )
    if stage == "prerun-clean":
        _prerun_status(fake, returncode=9)
    if stage in {
        "merge", "merge-message-provenance", "commit-dry-run", "commit",
    }:
        _abort_clean(fake)
    if stage != "preclaim-rev-parse":
        _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE if stage in merge_stages else None)

    assert outcome.rc == 70
    assert outcome.stage == stage
    expected = [*_PREFLIGHT_EVENTS]
    if stage in merge_stages:
        expected.append(("is_file", _MESSAGE))
    expected.extend(
        [
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
        ]
    )
    if stage != "preclaim-rev-parse":
        expected.extend(
            [
                ("monotonic",),
                ("run", _helper("claim", _SHA_A), _REPO, True),
            ]
        )
    if stage not in {"preclaim-rev-parse", "claim"}:
        expected.append(("run", ("git", "rev-parse", "main"), _REPO, True))
    if stage not in {"preclaim-rev-parse", "claim", "postclaim-rev-parse"}:
        expected.append(
            ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True)
        )
    if stage in merge_stages:
        expected.extend(
            [
                ("is_file", _MESSAGE),
                ("read_text", _MESSAGE),
                ("write_temp", b"merge\nAI-Agent: codex\n"),
                ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
            ]
        )
    if stage in {
        "merge-message-provenance", "commit-dry-run", "commit",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        expected.append(("run", _provenance_argv(), _REPO, True))
    if stage in {
        "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        expected.append(
            ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)), _REPO, True)
        )
    if stage in {
        "commit", "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        expected.append(
            ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE)), _REPO, True)
        )
    if stage in {
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        expected.append(("run", ("git", "rev-parse", "HEAD"), _REPO, True))
    if stage in {
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        expected.append(
            ("run", ("git", "log", "-1", "--format=%B", _SHA_C), _REPO, True)
        )
    if stage in {"postcheck", "commit-head-postcheck", "prerun-clean"}:
        expected.append(
            ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True)
        )
    if stage in {"commit-head-postcheck", "prerun-clean"}:
        expected.append(("run", ("git", "rev-parse", "HEAD"), _REPO, True))
    if stage == "prerun-clean":
        expected.append(("run", _STATUS_ARGV, _REPO, True))
    if stage in merge_stages:
        expected.append(("unlink", _VALIDATED_MESSAGE))
    if stage in {
        "merge", "merge-message-provenance", "commit-dry-run", "commit",
    }:
        expected.extend(_ABORT_CLEAN_EVENTS)
    if stage != "preclaim-rev-parse":
        expected.append(("run", _helper("release"), _REPO, True))
    assert fake.events == expected
    fake.assert_drained()


def test_prerun_clean_allows_acceptance_submission_without_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            ("monotonic",),
            ("run", _helper("claim", _SHA_A), _REPO, True),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
            *_FINGERPRINT_EVENTS,
            ("run", _COMMAND, _REPO, False),
            *_POSTRUN_INTEGRITY_EVENTS,
            *_SUCCESS_RECEIPT_EVENTS,
        ]
    )
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_prerun_tracked_dirty_blocks_submission_and_releases(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake, stdout=" M tracked.py\n")
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    assert "tracked.py" in capsys.readouterr().err
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            ("monotonic",),
            ("run", _helper("claim", _SHA_A), _REPO, True),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
            ("run", _helper("release"), _REPO, True),
        ]
    )
    assert not any(
        event[0] == "run" and event[1] == _COMMAND for event in fake.events
    )


def test_prerun_submodule_dirty_blocks_submission_and_releases() -> None:
    fake = _SubmoduleDirtyAcceptanceEffects(dirty_status_call=2)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    assert fake.status_reads == 2
    assert fake.claims == 1
    assert fake.submissions == 0
    assert fake.releases == 1
    assert fake.behind == []
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            ("monotonic",),
            ("run", _helper("claim", _SHA_A), _REPO, True),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
            ("run", _helper("release"), _REPO, True),
        ]
    )


def test_postmerge_tracked_dirty_blocks_submission_and_releases() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "1\n"),
    )
    fake.is_file_queue.append((_MESSAGE, True))
    fake.read_text_queue.append(
        (_MESSAGE, "merge\n\nAI-Agent: product=codex; model=gpt-5; "
         "reasoning=high; role=author\n")
    )
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    _provenance(fake)
    fake.expect_run(
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE))
    )
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(
        ("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n")
    )
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(
            0,
            "merge\n\nAI-Agent: product=codex; model=gpt-5; "
            "reasoning=high; role=author\n",
        ),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n")
    )
    _prerun_status(fake, stdout=" M postmerge.py\n")
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    expected_message = (
        b"merge\n\nAI-Agent: product=codex; model=gpt-5; "
        b"reasoning=high; role=author\n"
    )
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
            ("is_file", _MESSAGE),
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            ("monotonic",),
            ("run", _helper("claim", _SHA_A), _REPO, True),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("is_file", _MESSAGE),
            ("read_text", _MESSAGE),
            ("write_temp", expected_message),
            (
                "run",
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                _REPO,
                True,
            ),
            ("run", _provenance_argv(), _REPO, True),
            (
                "run",
                ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
                _REPO,
                True,
            ),
            ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
            (
                "run",
                ("git", "log", "-1", "--format=%B", _SHA_C),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
            ("run", _STATUS_ARGV, _REPO, True),
            ("unlink", _VALIDATED_MESSAGE),
            ("run", _helper("release"), _REPO, True),
        ]
    )
    assert not any(
        event[0] == "run" and event[1] == _COMMAND for event in fake.events
    )


def test_held_self_prerun_dirty_blocks_without_releasing_lease() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, _held_self_payload())
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake, stdout=" M retained.py\n")

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            ("monotonic",),
            ("run", _helper("claim", _SHA_A), _REPO, True),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
        ]
    )
    assert not any(
        event[0] == "run" and event[1] in {_COMMAND, _helper("release")}
        for event in fake.events
    )


def test_malformed_ai_agent_message_fails_provenance_before_commit() -> None:
    message = "merge\n\nAI-Agent: codex\n"
    assert DW._message_has_ai_agent(message)
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        message=message,
        head_shas=[_SHA_C, _SHA_C],
        provenance_result=DW._CommandResult(9),
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge-message-provenance"
    assert outcome.source_rc == 9
    assert fake.claims == 1
    assert fake.submissions == 0
    assert fake.releases == 1
    assert (
        "run",
        ("git", "merge", "--abort"),
        _REPO,
        True,
    ) in fake.events
    assert not any(
        event[0] == "run"
        and event[1]
        in {
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
        for event in fake.events
    )
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
            ("is_file", _MESSAGE),
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            ("monotonic",),
            ("run", _helper("claim", _SHA_A), _REPO, True),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("is_file", _MESSAGE),
            ("read_text", _MESSAGE),
            ("write_temp", message.encode("utf-8")),
            (
                "run",
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                _REPO,
                True,
            ),
            ("run", _provenance_argv(), _REPO, True),
            ("unlink", _VALIDATED_MESSAGE),
            *_ABORT_CLEAN_EVENTS,
            ("run", _helper("release"), _REPO, True),
        ]
    )


def test_preflight_submodule_dirty_rejects_before_claim() -> None:
    fake = _SubmoduleDirtyAcceptanceEffects(dirty_status_call=1)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 2
    assert outcome.stage == "preflight-clean"
    assert outcome.source_rc is None
    assert fake.status_reads == 1
    assert fake.claims == 0
    assert fake.submissions == 0
    assert fake.releases == 0
    fake.assert_drained(
        [
            ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
            ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
            (
                "run",
                ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
        ]
    )


def test_merge_failure_aborts_before_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"), DW._CommandResult(1))
    _abort_clean(fake)
    _release(fake)
    outcome = _run_acceptance(fake, message=_MESSAGE)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("is_file", _MESSAGE),
        ("read_text", _MESSAGE),
        ("write_temp", b"merge\nAI-Agent: codex\n"),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
        ("unlink", _VALIDATED_MESSAGE),
        *_ABORT_CLEAN_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_held_self_merge_failure_aborts_without_releasing_lease() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1],
        claim_payload=_held_self_payload(),
        merge_result=DW._CommandResult(1),
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge"
    assert fake.releases == 0
    assert fake.submissions == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (
        "run",
        ("git", "merge", "--abort"),
        _REPO,
        True,
    ) in fake.events
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_held_self_acceptance_red_retains_real_lease_without_polling(
    tmp_path: Path,
) -> None:
    lease_dir, lease_path, before = _lease_marker(tmp_path)
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(),
        command_result=DW._CommandResult(23),
        lease_dir=lease_dir,
        remove_lease_on_release=True,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-red-check"
    assert fake.releases == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (lease_path.stat().st_mtime_ns, lease_path.read_bytes()) == before


def test_held_self_postclaim_failure_retains_real_lease_without_polling(
    tmp_path: Path,
) -> None:
    lease_dir, lease_path, before = _lease_marker(tmp_path)
    fake = _RoutingAcceptanceEffects(
        claim_payload=_held_self_payload(),
        postclaim_rc=9,
        lease_dir=lease_dir,
        remove_lease_on_release=True,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome.rc == 70
    assert outcome.stage == "postclaim-rev-parse"
    assert outcome.source_rc == 9
    assert fake.submissions == 0
    assert fake.releases == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (lease_path.stat().st_mtime_ns, lease_path.read_bytes()) == before


def test_held_self_signal_retains_real_lease_without_polling(tmp_path: Path) -> None:
    lease_dir, lease_path, before = _lease_marker(tmp_path)
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(),
        command_result=DW._SignalReceived(signal.SIGTERM),
        lease_dir=lease_dir,
        remove_lease_on_release=True,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome.rc == 143
    assert outcome.stage == "signal-15"
    assert fake.submissions == 1
    assert fake.releases == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (lease_path.stat().st_mtime_ns, lease_path.read_bytes()) == before


def test_acceptance_command_red_is_propagated_after_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(23), capture=False)
    _queue_checker(fake, status="green", nodes=[])
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        ("run", _checker_argv(), _REPO, False),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize("kind", ["subprocess-error", "keyboard-interrupt"])
def test_abnormal_path_without_ownership_does_not_release(kind: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    if kind == "subprocess-error":
        fake.expect_run(("git", "rev-parse", "main"), OSError("boom"))
    else:
        fake.monotonic_queue[:] = [0.0, 0.0]
        _claim(fake, _SHA_A, '{"state":"held"}')
        original_sleep = fake.sleep

        def interrupting_sleep(seconds: float) -> None:
            original_sleep(seconds)
            raise KeyboardInterrupt

        effects = fake.effects
        effects = DW._Effects(
            run=effects.run, run_unbounded=effects.run_unbounded,
            sleep=interrupting_sleep, kill=effects.kill,
            is_file=effects.is_file, read_text=effects.read_text,
            getenv=effects.getenv, monotonic=effects.monotonic,
            write_temp=effects.write_temp, unlink=effects.unlink,
            path_exists=effects.path_exists, is_dir=effects.is_dir,
            resolve_path=effects.resolve_path,
            write_receipt_temp=effects.write_receipt_temp,
            rename=effects.rename,
            run_logged=effects.run_logged,
            read_bytes=effects.read_bytes,
            is_symlink=effects.is_symlink,
        )
    if kind == "subprocess-error":
        outcome = _run_acceptance(fake)
    else:
        outcome = DW.run_acceptance(
            wave=_WAVE, lease_dir=_LEASE, merge_message_file=None,
            poll_seconds=30, max_wait_seconds=7200, command=_COMMAND,
            repo=_REPO, effects=effects, receipt_file=_RECEIPT,
            log_file=_LOG,
        )
    assert outcome.rc == (130 if kind == "keyboard-interrupt" else 70)
    expected = [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
    ]
    if kind == "keyboard-interrupt":
        expected.extend(
            [
                ("monotonic",),
                ("run", _helper("claim", _SHA_A), _REPO, True),
                ("monotonic",),
                ("sleep", 30),
            ]
        )
    assert fake.events == expected
    fake.assert_drained()


def test_release_failure_overrides_primary_result() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(5), capture=False)
    _release(fake, DW._CommandResult(0, '{"state":"unavailable"}'))
    outcome = _run_acceptance(fake)
    assert outcome.rc == 74
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize(
    "release_result",
    [DW._CommandResult(9, ""), DW._CommandResult(0, "not-json")],
    ids=("nonzero", "malformed-json"),
)
def test_release_subprocess_failures_are_cleanup_failures(release_result: object) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(5), capture=False)
    _release(fake, release_result)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 74
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_merge_abort_nonzero_is_cleanup_failure() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"), DW._CommandResult(1))
    _abort_clean(fake, DW._CommandResult(8))
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 74
    assert outcome.stage == "merge-abort"
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("is_file", _MESSAGE),
        ("read_text", _MESSAGE),
        ("write_temp", b"merge\nAI-Agent: codex\n"),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
        ("unlink", _VALIDATED_MESSAGE),
        *_ABORT_CLEAN_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize("dirty", ["merge-head", "tracked"], ids=("merge-head", "tracked"))
def test_merge_abort_requires_clean_repository_postcondition(dirty: str) -> None:
    fake = _FakeEffects()
    fake.expect_run(("git", "merge", "--abort"))
    fake.expect_run(
        ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
        DW._CommandResult(0, _SHA_A + "\n")
        if dirty == "merge-head" else DW._CommandResult(1),
    )
    fake.expect_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        DW._CommandResult(0, " M tracked.py\n" if dirty == "tracked" else ""),
    )

    outcome = DW._abort_pending_merge(fake.effects, _REPO)

    assert outcome.rc == 74
    assert outcome.stage == (
        "merge-abort-state" if dirty == "merge-head" else "merge-abort-clean"
    )
    fake.assert_drained(_ABORT_CLEAN_EVENTS)


def test_default_run_sanitizes_git_and_bounds_only_stages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert {
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_NOSYSTEM",
    } <= DW._GIT_ENV_KEYS
    popen_calls: list[tuple[list[str], dict[str, object]]] = []
    run_calls: list[tuple[list[str], dict[str, object]]] = []
    group_kills: list[tuple[int, int]] = []

    class Process:
        def __init__(self, argv: list[str], *, times_out: bool = False) -> None:
            self.argv = argv
            self.pid = 4321
            self.returncode = 0
            self.times_out = times_out
            self.communicate_calls: list[object] = []

        def communicate(self, timeout: object = None) -> tuple[str, str]:
            self.communicate_calls.append(timeout)
            if self.times_out and len(self.communicate_calls) == 1:
                raise subprocess.TimeoutExpired(self.argv, timeout)
            self.returncode = -signal.SIGKILL if self.times_out else 0
            return "", ""

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: object = None) -> int:
            del timeout
            return self.returncode

    processes: list[Process] = []

    def recording_popen(argv: list[str], **kwargs: object) -> Process:
        popen_calls.append((argv, kwargs))
        process = Process(argv, times_out=len(popen_calls) == 3)
        processes.append(process)
        return process

    def recording_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        run_calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "", "")

    for key in DW._GIT_ENV_KEYS:
        monkeypatch.setenv(key, f"bad-{key}")
    monkeypatch.setattr(DW.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(DW.subprocess, "run", recording_run)
    monkeypatch.setattr(
        DW.os, "killpg", lambda pid, signum: group_kills.append((pid, signum))
    )

    DW._default_run(("git", "status"), _REPO, True)
    DW._default_run(_helper("release"), _REPO, True)
    DW._default_run_unbounded(("git", "status"), _REPO, False)
    with pytest.raises(subprocess.TimeoutExpired):
        DW._default_run(("git", "merge", "main"), _REPO, True)

    git_kwargs = popen_calls[0][1]
    assert git_kwargs["start_new_session"] is True
    assert all(key not in git_kwargs["env"] for key in DW._GIT_ENV_KEYS)
    assert popen_calls[1][1]["start_new_session"] is True
    assert len(run_calls) == 1
    assert "start_new_session" not in run_calls[0][1]
    assert all(key not in run_calls[0][1]["env"] for key in DW._GIT_ENV_KEYS)
    assert len(popen_calls) == 3
    assert processes[2].communicate_calls == [300, 5]
    assert group_kills == [(4321, signal.SIGKILL)]


def test_provenance_checker_is_sanitized_bounded_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    popen_calls: list[tuple[list[str], dict[str, object]]] = []
    group_kills: list[tuple[int, int]] = []

    class Process:
        pid = 5432
        returncode = 0

        def __init__(self) -> None:
            self.communicate_calls: list[object] = []

        def communicate(self, timeout: object = None) -> tuple[str, str]:
            self.communicate_calls.append(timeout)
            if len(self.communicate_calls) == 1:
                raise subprocess.TimeoutExpired(_provenance_argv(), timeout)
            self.returncode = -signal.SIGKILL
            return "", ""

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: object = None) -> int:
            del timeout
            return self.returncode

    process = Process()

    def recording_popen(argv: list[str], **kwargs: object) -> Process:
        popen_calls.append((argv, kwargs))
        return process

    for key in DW._GIT_ENV_KEYS:
        monkeypatch.setenv(key, f"bad-{key}")
    monkeypatch.setattr(DW.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(
        DW.os, "killpg", lambda pid, signum: group_kills.append((pid, signum))
    )

    with pytest.raises(DW._StageFailure) as exc_info:
        DW._run_capture(
            DW._default_effects(),
            _provenance_argv(),
            _REPO,
            "merge-message-provenance",
        )

    assert exc_info.value.outcome.rc == 70
    assert exc_info.value.outcome.stage == "merge-message-provenance"
    assert exc_info.value.outcome.source_rc is None
    assert len(popen_calls) == 1
    checker_argv, checker_kwargs = popen_calls[0]
    assert checker_argv == list(_provenance_argv())
    assert checker_kwargs["start_new_session"] is True
    assert all(key not in checker_kwargs["env"] for key in DW._GIT_ENV_KEYS)
    assert process.communicate_calls == [300, 5]
    assert group_kills == [(5432, signal.SIGKILL)]


@pytest.mark.parametrize(
    "case", ["missing-delimiter", "empty-command", "poll-29", "poll-121", "default-30"],
)
def test_acceptance_cli_contract(case: str) -> None:
    base = [
        "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
        "--receipt-file", str(_RECEIPT),
        "--log-file", str(_LOG),
    ]
    if case == "missing-delimiter":
        argv = base + ["harmless"]
    elif case == "empty-command":
        argv = base + ["--"]
    elif case == "poll-29":
        argv = base + ["--poll-seconds", "29", "--", "harmless"]
    elif case == "poll-121":
        argv = base + ["--poll-seconds", "121", "--", "harmless"]
    else:
        command, args, child = DW._parse_cli(base + ["--", "harmless"])
        assert command == "acceptance"
        assert args.poll_seconds == 30
        assert args.max_wait_seconds == 7200
        assert args.owned_path == []
        assert child == ["harmless"]
        return
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli(argv)
    assert raised.value.outcome.rc == 2


def test_acceptance_owned_path_is_repeatable() -> None:
    command, args, child = DW._parse_cli(
        [
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--receipt-file",
            str(_RECEIPT),
            "--log-file",
            str(_LOG),
            "--owned-path",
            "./docs/x.md",
            "--owned-path",
            "tools",
            "--",
            "harmless",
        ]
    )

    assert command == "acceptance"
    assert args.owned_path == [Path("docs/x.md"), Path("tools")]
    assert child == ["harmless"]


def test_acceptance_cli_requires_receipt_file() -> None:
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli([
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--log-file",
            str(_LOG),
            "--",
            "harmless",
        ])
    assert raised.value.outcome == DW._Outcome(2, "cli-usage")


def test_acceptance_cli_requires_log_file() -> None:
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli([
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--receipt-file",
            str(_RECEIPT),
            "--",
            "harmless",
        ])
    assert raised.value.outcome == DW._Outcome(2, "cli-usage")


@pytest.mark.parametrize(
    ("top_level", "branch", "status", "failed_stage"),
    [
        ("/other", f"feature-{_WAVE}", "", "preflight-toplevel"),
        (str(_REPO), "wrong-branch", "", "preflight-branch"),
        (str(_REPO), f"feature-{_WAVE}", " M tracked.py\n", "preflight-clean"),
    ],
)
def test_identity_preflight_rejects_before_claim(
    top_level: str, branch: str, status: str, failed_stage: str,
) -> None:
    fake = _FakeEffects()
    fake.expect_run(("git", "rev-parse", "--is-inside-work-tree"), DW._CommandResult(0, "true\n"))
    fake.expect_run(("git", "rev-parse", "--show-toplevel"), DW._CommandResult(0, top_level + "\n"))
    if failed_stage != "preflight-toplevel":
        fake.expect_run(("git", "symbolic-ref", "--quiet", "--short", "HEAD"), DW._CommandResult(0, branch + "\n"))
    if failed_stage == "preflight-clean":
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, status))
    outcome = _run_acceptance(fake)
    assert outcome.rc == 2
    assert outcome.stage == failed_stage
    expected = [
        ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
        ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
    ]
    if failed_stage != "preflight-toplevel":
        expected.append(
            ("run", ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), _REPO, True)
        )
    if failed_stage == "preflight-clean":
        expected.append(
            ("run", _STATUS_ARGV, _REPO, True)
        )
    assert fake.events == expected
    fake.assert_drained()


def test_wrong_branch_fixture_reaches_submission_only_if_branch_gate_is_removed() -> None:
    fake = _RoutingAcceptanceEffects(branch="wrong-branch", behind=[0])

    outcome = _run_acceptance(fake)

    assert outcome.rc == 2
    assert outcome.stage == "preflight-branch"
    assert (fake.claims, fake.submissions, fake.releases) == (0, 0, 0)


def test_positive_postmerge_behind_count_blocks_only_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 1],
        head_shas=[_SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "postcheck"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)


def test_created_commit_identity_change_blocks_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_B],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "commit-head-postcheck"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)


def test_merge_message_requires_nonempty_ai_agent_trailer() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        message="merge without trailer\n",
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge-message"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)


def test_committed_message_without_ai_agent_never_runs_acceptance() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    _provenance(fake)
    fake.expect_run(("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(0, "merge without trailer\n"),
    )
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "commit-message-postcheck"
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("is_file", _MESSAGE),
        ("read_text", _MESSAGE),
        ("write_temp", b"merge\nAI-Agent: codex\n"),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
        ("run", _provenance_argv(), _REPO, True),
        ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)), _REPO, True),
        ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE)), _REPO, True),
        ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
        ("run", ("git", "log", "-1", "--format=%B", _SHA_C), _REPO, True),
        ("unlink", _VALIDATED_MESSAGE),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_signal_path_releases_and_normalizes_rc() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_A + "\n"))
    fake.expect_run(_helper("claim", _SHA_A), DW._SignalReceived(15))
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 143
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize(
    ("ownership", "release_count"),
    [
        (DW._LeaseOwnership.ACQUIRED, 1),
        (DW._LeaseOwnership.HELD_SELF, 0),
    ],
    ids=("acquired", "held-self"),
)
def test_cleanup_consumes_ownership_before_release_and_is_idempotent(
    ownership: DW._LeaseOwnership,
    release_count: int,
) -> None:
    fake = _FakeEffects()
    if release_count:
        _release(fake)
    lifecycle = DW._AcceptanceLifecycle(ownership=ownership)

    first = DW._cleanup_lifecycle(lifecycle, fake.effects, _REPO, _LEASE, _WAVE)
    second = DW._cleanup_lifecycle(lifecycle, fake.effects, _REPO, _LEASE, _WAVE)

    assert first is None
    assert second is None
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    assert sum(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    ) == release_count
    fake.assert_drained(
        [("run", _helper("release"), _REPO, True)] if release_count else []
    )


def test_signal_after_core_success_uses_restored_real_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    restored_handler_calls: list[int] = []
    restore_calls = 0
    real_restore = DW._restore_signal_handlers

    def inject_signal_then_restore(previous: dict[int, object]) -> None:
        nonlocal restore_calls
        restore_calls += 1
        if restore_calls == 1:
            os.kill(os.getpid(), signal.SIGTERM)
        real_restore(previous)

    monkeypatch.setattr(DW, "_restore_signal_handlers", inject_signal_then_restore)
    original = signal.getsignal(signal.SIGTERM)
    signal.signal(
        signal.SIGTERM,
        lambda signum, frame: restored_handler_calls.append(signum),
    )
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--receipt-file", str(_RECEIPT),
                "--log-file", str(_LOG),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)

    assert rc == 0
    assert restore_calls == 2
    assert restored_handler_calls == [signal.SIGTERM]
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        *_SUCCESS_RECEIPT_EVENTS,
    ]
    fake.assert_drained()


def test_public_main_failure_restores_handler_without_release() -> None:
    fake = _FakeEffects()
    fake.expect_run(
        ("git", "rev-parse", "--is-inside-work-tree"),
        DW._CommandResult(0, "true\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "--show-toplevel"),
        DW._CommandResult(0, str(_REPO) + "\n"),
    )
    fake.expect_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        DW._CommandResult(0, "wrong-branch\n"),
    )
    restored_handler_calls: list[int] = []
    original = signal.getsignal(signal.SIGTERM)
    signal.signal(
        signal.SIGTERM,
        lambda signum, frame: restored_handler_calls.append(signum),
    )
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--receipt-file", str(_RECEIPT),
                "--log-file", str(_LOG),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)

    assert rc == 2
    assert restored_handler_calls == [signal.SIGTERM]
    fake.assert_drained(
        [
            ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
            ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
            (
                "run",
                ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
                _REPO,
                True,
            ),
        ]
    )


def test_second_signal_is_deferred_until_cleanup_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    _release(fake)
    previous_mask = {signal.SIGUSR1}

    def signal_mask(how: int, signals: object) -> set[signal.Signals]:
        if how == signal.SIG_BLOCK:
            fake.events.append(("mask", how, tuple(signals)))
            return previous_mask
        fake.events.append(("mask", how, signals))
        raise DW._SignalReceived(signal.SIGINT)

    monkeypatch.setattr(DW.signal, "pthread_sigmask", signal_mask)

    outcome = DW._cleanup_after_claim(
        fake.effects,
        _REPO,
        _LEASE,
        _WAVE,
        merge_pending=False,
        release_lease=True,
    )

    assert outcome is None
    assert fake.events == [
        ("mask", signal.SIG_BLOCK, DW._HANDLED_SIGNALS),
        ("run", _helper("release"), _REPO, True),
        ("mask", signal.SIG_SETMASK, previous_mask),
    ]
    fake.assert_drained()


def test_real_git_dirty_after_claim_blocks_acceptance_command(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-dirty"
    lease = tmp_path / "lease-dirty"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    real_helper = tools / "wave_land_window_real.py"
    shutil.copy2(_LEASE_HELPER, real_helper)
    helper = tools / "wave_land_window.py"
    helper.write_text(
        "import subprocess,sys\n"
        "from pathlib import Path\n"
        "real=Path(__file__).with_name('wave_land_window_real.py')\n"
        "result=subprocess.run([sys.executable,str(real),*sys.argv[1:]],"
        "capture_output=True,text=True)\n"
        "if len(sys.argv)>1 and sys.argv[1]=='claim' and result.returncode==0:\n"
        "    (Path(__file__).resolve().parents[1]/'tracked.txt').write_text("
        "'dirty after claim\\n',encoding='utf-8')\n"
        "sys.stdout.write(result.stdout)\n"
        "sys.stderr.write(result.stderr)\n"
        "raise SystemExit(result.returncode)\n",
        encoding="utf-8",
    )
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/wave_land_window_real.py",
    )
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-dirty-real")
    sentinel = "REAL-DIRTY-COMMAND-SENTINEL"

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "dirty-real",
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(tmp_path / "dirty-receipt.json"),
            "--log-file",
            str(tmp_path / "dirty.log"),
            "--",
            sys.executable,
            "-c",
            f"print({sentinel!r})",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )

    assert result.returncode == 70
    assert "error: stage=prerun-clean rc=70" in result.stderr
    assert "tracked.txt" in result.stderr
    assert sentinel not in result.stdout
    assert not (lease / "acceptance.lease").exists()


def test_real_git_production_provenance_rejects_malformed_merge_message(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-production-provenance"
    lease = tmp_path / "lease-production-provenance"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    shutil.copy2(_ROOT / "tools" / "check_ai_provenance.py", tools)
    campaign = repo / "orchestrator" / "campaign"
    campaign.mkdir(parents=True)
    shutil.copy2(_ROOT / "orchestrator" / "campaign" / "__init__.py", campaign)
    shutil.copy2(_ROOT / "orchestrator" / "campaign" / "site_policy.py", campaign)
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt", "tools", "orchestrator")
    git("commit", "-m", "base")
    base_sha = git("rev-parse", "HEAD").stdout.strip()
    git("checkout", "-b", "worktree-production-provenance")
    git("checkout", "main")
    tracked.write_text("main advanced\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", "advance main")
    git("checkout", "worktree-production-provenance")
    message = tmp_path / "malformed-merge-message.txt"
    message.write_text("merge main\n\nAI-Agent: codex\n", encoding="utf-8")
    sentinel = "PRODUCTION-PROVENANCE-COMMAND-SENTINEL"

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "production-provenance",
            "--lease-dir",
            str(lease),
            "--merge-message-file",
            str(message),
            "--receipt-file",
            str(tmp_path / "provenance-receipt.json"),
            "--log-file",
            str(tmp_path / "provenance.log"),
            "--",
            sys.executable,
            "-c",
            f"print({sentinel!r})",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )

    assert result.returncode == 70
    assert "error: stage=merge-message-provenance rc=70 source_rc=1" in result.stderr
    assert sentinel not in result.stdout
    assert git("rev-parse", "HEAD").stdout.strip() == base_sha
    assert git("rev-list", "--count", "HEAD..main").stdout.strip() == "1"
    assert git(
        "status", "--porcelain", "--untracked-files=no",
        "--ignore-submodules=none",
    ).stdout == ""
    merge_head = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )
    assert merge_head.returncode == 1
    assert not (lease / "acceptance.lease").exists()


def test_default_wiring_with_real_git_and_lease_helper(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    lease = tmp_path / "lease"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    _write_test_provenance_checker(repo)

    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/dev_wave_wait.py",
        "tools/check_ai_provenance.py",
    )
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-integration")
    git("checkout", "main")
    tracked.write_text("main advanced\n", encoding="utf-8")
    git("add", "tracked.txt", "tools/wave_land_window.py")
    git("commit", "-m", "advance main")
    git("checkout", "worktree-integration")
    message = tmp_path / "merge-message.txt"
    message.write_text(
        "merge main\n\nAI-Agent: product=codex; model=gpt-5; "
        "reasoning=high; role=author\n",
        encoding="utf-8",
    )

    child = (
        "import pathlib,sys; "
        "expected=pathlib.Path(sys.argv[1]); "
        "assert pathlib.Path.cwd()==expected; "
        "print('CHILD-STDOUT-SENTINEL'); "
        "print('CHILD-STDERR-SENTINEL', file=sys.stderr)"
    )
    waiter_env = {**git_env, "IZANAGI_WAVE_LEASE_DIR": str(lease)}

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "integration",
            "--merge-message-file",
            str(message),
            "--receipt-file",
            str(tmp_path / "integration-receipt.json"),
            "--log-file",
            str(tmp_path / "integration.log"),
            "--",
            sys.executable,
            "-c",
            child,
            str(repo.resolve()),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=waiter_env,
    )

    assert result.returncode == 0, result.stderr
    assert "lease is held" in result.stdout
    captured_log = (tmp_path / "integration.log").read_text(encoding="utf-8")
    assert "CHILD-STDOUT-SENTINEL" in captured_log
    assert "CHILD-STDERR-SENTINEL" in captured_log
    assert "CHILD-STDOUT-SENTINEL" not in result.stdout
    assert "CHILD-STDERR-SENTINEL" not in result.stderr
    integration_receipt = json.loads(
        (tmp_path / "integration-receipt.json").read_text(encoding="ascii")
    )
    assert integration_receipt["log_sha256"] == hashlib.sha256(
        (tmp_path / "integration.log").read_bytes()
    ).hexdigest()
    assert "AI-Agent: product=codex" in git(
        "log", "-1", "--format=%B", "HEAD"
    ).stdout
    assert git("rev-list", "--count", "HEAD..main").stdout.strip() == "0"
    assert (lease / "acceptance.lease").is_file()
    released = subprocess.run(
        [
            sys.executable,
            str(tools / "wave_land_window.py"),
            "release",
            "--lease-dir",
            str(lease),
            "--wave",
            "integration",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert released.returncode == 0
    assert json.loads(released.stdout)["state"] == "released"


def test_default_wiring_second_acceptance_reuses_self_held_lease(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    lease_dir = tmp_path / "lease"
    repo.mkdir()
    lease_dir.mkdir()
    (repo / "tools").mkdir()
    helper = repo / "tools" / "wave_land_window.py"
    shutil.copy2(_LEASE_HELPER, helper)
    shutil.copy2(_TOOL, repo / "tools" / "dev_wave_wait.py")
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            env=git_env,
        ).stdout.strip()

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt", "tools/wave_land_window.py", "tools/dev_wave_wait.py")
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-deadlock")
    main_sha = git("rev-parse", "main")
    claim = subprocess.run(
        [
            sys.executable,
            str(helper),
            "claim",
            "--lease-dir",
            str(lease_dir),
            "--wave",
            "deadlock",
            "--main-sha",
            main_sha,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )
    assert claim.returncode == 0, claim.stderr
    assert json.loads(claim.stdout)["state"] == "acquired"
    lease_path = lease_dir / "acceptance.lease"
    before_payload = lease_path.read_bytes()
    before_mtime = lease_path.stat().st_mtime_ns - 10_000_000_000
    os.utime(lease_path, ns=(before_mtime, before_mtime))

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "deadlock",
            "--lease-dir",
            str(lease_dir),
            "--max-wait-seconds",
            "1",
            "--receipt-file",
            str(tmp_path / "second-receipt.json"),
            "--log-file",
            str(tmp_path / "second.log"),
            "--",
            sys.executable,
            "-c",
            "print('SECOND-ACCEPTANCE-SENTINEL')",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )

    assert result.returncode == 0, result.stderr
    assert "SECOND-ACCEPTANCE-SENTINEL" in (
        tmp_path / "second.log"
    ).read_text(encoding="utf-8")
    assert "SECOND-ACCEPTANCE-SENTINEL" not in result.stdout
    assert "claim-timeout" not in result.stderr
    assert lease_path.read_bytes() == before_payload
    assert lease_path.stat().st_mtime_ns > before_mtime


def test_public_main_real_signal_releases_lease(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    lease = tmp_path / "lease"
    repo.mkdir()
    lease.mkdir()
    (repo / "tools").mkdir()
    shutil.copy2(_LEASE_HELPER, repo / "tools" / "wave_land_window.py")
    shutil.copy2(_TOOL, repo / "tools" / "dev_wave_wait.py")
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt", "tools/wave_land_window.py", "tools/dev_wave_wait.py")
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-signal")
    signal_child = (
        "import os,signal; "
        "os.kill(os.getppid(), signal.SIGTERM)"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "signal",
            "--receipt-file",
            str(tmp_path / "signal-receipt.json"),
            "--log-file",
            str(tmp_path / "signal.log"),
            "--",
            sys.executable,
            "-c",
            signal_child,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={**git_env, "IZANAGI_WAVE_LEASE_DIR": str(lease)},
    )

    assert result.returncode == 143, result.stderr
    assert not (lease / "acceptance.lease").exists()


def test_public_main_real_signal_after_success_uses_restored_handler(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-success"
    lease = tmp_path / "lease-success"
    repo.mkdir()
    lease.mkdir()
    (repo / "tools").mkdir()
    shutil.copy2(_LEASE_HELPER, repo / "tools" / "wave_land_window.py")
    shutil.copy2(_TOOL, repo / "tools" / "dev_wave_wait.py")
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt", "tools/wave_land_window.py", "tools/dev_wave_wait.py")
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-signal-success")
    runner = tmp_path / "success-boundary.py"
    runner.write_text(
        "import importlib.util, os, signal, sys\n"
        "from pathlib import Path\n"
        "spec=importlib.util.spec_from_file_location('waiter', sys.argv[1])\n"
        "module=importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name]=module\n"
        "spec.loader.exec_module(module)\n"
        "received=[]\n"
        "signal.signal(signal.SIGTERM, lambda n, f: received.append(n))\n"
        "rc=module.main(['acceptance','--wave','signal-success',"
        "'--receipt-file',sys.argv[3],'--log-file',sys.argv[4],'--',"
        "sys.executable,'-c','raise SystemExit(0)'], repo=Path(sys.argv[2]))\n"
        "os.kill(os.getpid(), signal.SIGTERM)\n"
        "print(f'RESTORED={received} RC={rc}')\n"
        "raise SystemExit(rc)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(runner),
            str(_TOOL),
            str(repo),
            str(tmp_path / "signal-success-receipt.json"),
            str(tmp_path / "signal-success.log"),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={**git_env, "IZANAGI_WAVE_LEASE_DIR": str(lease)},
    )

    assert result.returncode == 0, result.stderr
    assert f"RESTORED=[{signal.SIGTERM}] RC=0" in result.stdout
    assert (lease / "acceptance.lease").is_file()
