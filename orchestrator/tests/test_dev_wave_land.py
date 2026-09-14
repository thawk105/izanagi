# -*- coding: utf-8 -*-
"""tools/dev_wave_land.py の linked-worktree / race / land 境界テスト。

pytest と ``python3 orchestrator/tests/test_dev_wave_land.py`` の両方で走る。
全 Git mutation は tempfile 配下の合成 repository に限定する。
"""
from __future__ import annotations

import contextlib
import dataclasses
import errno
import fcntl
import hashlib
import importlib.util
import io
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
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "tools" / "dev_wave_land.py"
SPEC = importlib.util.spec_from_file_location("dev_wave_land_under_test", HELPER_PATH)
assert SPEC and SPEC.loader
LAND = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LAND
SPEC.loader.exec_module(LAND)
REAL_GIT = "/usr/bin/git"
_EXPECTED_AUTHORITY_KINDS = {
    "tested-main": "dev-wave-acceptance-launcher",
    "tested-tip-bootstrap": "dev-wave-acceptance-launcher-bootstrap-tip",
}
_V5_BINDING_FIELDS = frozenset({
    "launcher_source_revision",
    "launcher_blob_sha",
    "launcher_executed_sha256",
    "waiter_executed_sha256",
    "runner_executed_sha256",
})
_V4_RECEIPT_FIELDS = frozenset({
    "schema_version",
    "authority_kind",
    "acceptance_wave",
    "lease_holder",
    "tested_main",
    "tested_tip",
    "argv",
    "resolved_runner_path",
    "child_rc",
    "pre_fingerprint",
    "post_fingerprint",
    "waiter_blob_sha",
    "env_projection",
    "effective_scheduler",
    "verdict",
    "log_sha256",
    "checker_rc",
    "checker_status",
    "checker_blob_sha",
    "checker_receipt_sha256",
    "red_nodeids",
    "flake_nodeids",
})


def _git_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _git(repo: Path, *args: str, check: bool = True) -> str:
    env = _git_env()
    result = subprocess.run(
        [REAL_GIT, "-C", str(repo), *args],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if check:
        assert result.returncode == 0, (repo, args, result.stderr)
    return result.stdout.strip()


def _git_blob_sha256(repo: Path, revision: str, path: str) -> str:
    result = subprocess.run(
        [REAL_GIT, "-C", str(repo), "cat-file", "blob", f"{revision}:{path}"],
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, (repo, revision, path, result.stderr)
    return hashlib.sha256(result.stdout).hexdigest()


def _receipt_blob_sha256(repo: Path, revision: str, path: str) -> str:
    try:
        return _git_blob_sha256(repo, revision, path)
    except AssertionError:
        return "0" * 64


@contextlib.contextmanager
def _cwd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@contextlib.contextmanager
def _campaign_import_scope():
    """Campaign imports may edit sys.path; restore the complete list on exit."""
    saved_sys_path = sys.path[:]
    try:
        repo_path = str(ROOT)
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)
        yield
    finally:
        sys.path[:] = saved_sys_path


class _Repo:
    def __init__(self, *, waves: tuple[tuple[str, str], ...] = (("codex", "one"),)):
        self._tmp = tempfile.TemporaryDirectory(prefix="izanagi-land-test-")
        self.root = Path(self._tmp.name)
        self.main = self.root / "repo"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(self.main)],
            check=True,
            env={
                **{
                    key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")
                },
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_SYSTEM": os.devnull,
            },
        )
        _git(self.main, "config", "user.name", "Dev Wave Test")
        _git(self.main, "config", "user.email", "dev-wave@example.invalid")
        (self.main / "base.txt").write_text("base\n", encoding="utf-8")
        handoff = self.main / "docs" / "handoff"
        handoff.mkdir(parents=True)
        (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")
        spool = self.main / "docs" / "spool"
        spool.mkdir()
        (spool / "README.md").write_text("# spool\n", encoding="utf-8")
        (spool / "FOLDED.md").write_text("# receipts\n", encoding="utf-8")
        for ledger in LAND._FOLD_LEDGERS:
            directory = spool / ledger
            directory.mkdir()
            (directory / "README.md").write_text(f"# {ledger}\n", encoding="utf-8")
        tools = self.main / "tools"
        tools.mkdir()
        (tools / "check_docs.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        (tools / "check_ai_provenance.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        (tools / "dev_wave_wait.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        (tools / "check_acceptance_reds.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        (tools / "run_tests.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        (tools / "acceptance_launcher.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        _git(
            self.main,
            "add",
            "base.txt",
            "docs",
            "tools/check_docs.py",
            "tools/check_ai_provenance.py",
            "tools/dev_wave_wait.py",
            "tools/check_acceptance_reds.py",
            "tools/run_tests.py",
            "tools/acceptance_launcher.py",
        )
        _git(self.main, "commit", "-qm", "base")
        self.base = _git(self.main, "rev-parse", "HEAD")
        self.waves: dict[str, Path] = {}
        for family, name in waves:
            self.add_wave(family, name)

    def close(self) -> None:
        self._tmp.cleanup()

    def add_wave(self, family: str, name: str) -> Path:
        assert family in {"codex", "claude"}
        container = self.main / f".{family}" / "worktrees"
        container.mkdir(parents=True, exist_ok=True)
        path = container / name
        branch = f"wave/{family}-{name}"
        _git(self.main, "worktree", "add", "-q", "-b", branch, str(path), self.base)
        self.waves[name] = path
        return path

    def commit(self, wave: Path, filename: str, content: str) -> str:
        (wave / filename).write_text(content, encoding="utf-8")
        _git(wave, "add", filename)
        _git(wave, "commit", "-qm", f"add {filename}")
        return _git(wave, "rev-parse", "HEAD")

    def audited(self, base: str, tip: str, wave: Path) -> tuple[str, ...]:
        output = _git(wave, "rev-list", "--reverse", f"{base}..{tip}")
        return tuple(output.splitlines()) if output else ()

    def request(
        self,
        wave: Path,
        *,
        base: str | None = None,
        tip: str | None = None,
        audited: tuple[str, ...] | None = None,
        acceptance_wave: str = "test-wave",
        acceptance_receipt: Path | None = None,
        make_acceptance_receipt: bool = True,
        landing_tip: str | None = None,
        runner_digest_revision: str | None = None,
    ):
        tested_base = base or self.base
        tested_tip = tip or _git(wave, "rev-parse", "HEAD")
        commits = (
            audited
            if audited is not None
            else self.audited(tested_base, tested_tip, wave)
        )
        receipt_path = acceptance_receipt
        if receipt_path is None and make_acceptance_receipt:
            receipt_path = self._acceptance_receipt(
                wave,
                tested_base,
                tested_tip,
                acceptance_wave,
                runner_digest_revision=runner_digest_revision,
            )
        if receipt_path is None:
            receipt_path = self.root / "acceptance-receipt-not-created.json"
        return LAND.LandRequest(
            main_worktree=self.main,
            wave_worktree=wave,
            tested_main_sha=tested_base,
            tested_wave_tip_sha=tested_tip,
            audited_commits=commits,
            acceptance_wave=acceptance_wave,
            acceptance_receipt=receipt_path,
            landing_wave_tip_sha=landing_tip,
        )

    def _acceptance_receipt(
        self,
        wave: Path,
        tested_main: str,
        tested_tip: str,
        acceptance_wave: str,
        *,
        runner_digest_revision: str | None = None,
    ) -> Path:
        waiter_blob = _git(
            wave,
            "rev-parse",
            f"{tested_tip}:tools/dev_wave_wait.py",
            check=False,
        )
        if re.fullmatch(r"[0-9a-f]{40}", waiter_blob) is None:
            waiter_blob = "0" * 40
        launcher_blob = _git(
            wave,
            "rev-parse",
            f"{tested_main}:tools/acceptance_launcher.py",
            check=False,
        )
        launcher_source_revision = "tested-main"
        launcher_revision = tested_main
        if re.fullmatch(r"[0-9a-f]{40}", launcher_blob) is None:
            launcher_source_revision = "tested-tip-bootstrap"
            launcher_revision = tested_tip
            launcher_blob = _git(
                wave,
                "rev-parse",
                f"{tested_tip}:tools/acceptance_launcher.py",
            )
        fingerprint = {
            "digest": hashlib.sha256(tested_tip.encode("ascii")).hexdigest(),
            "head_sha": tested_tip,
            "status_bytes": 0,
            "diff_bytes": 0,
            "submodule_status_bytes": 0,
        }
        receipt = {
            "schema_version": LAND._ACCEPTANCE_RECEIPT_SCHEMA,
            "authority_kind": LAND._ACCEPTANCE_AUTHORITY_KINDS[
                launcher_source_revision
            ],
            "acceptance_wave": acceptance_wave,
            "lease_holder": hashlib.sha256(
                acceptance_wave.encode("utf-8")
            ).hexdigest()[:12],
            "tested_main": tested_main,
            "tested_tip": tested_tip,
            "argv": ["python3", "tools/run_tests.py"],
            "resolved_runner_path": "tools/run_tests.py",
            "child_rc": 0,
            "pre_fingerprint": fingerprint,
            "post_fingerprint": dict(fingerprint),
            "waiter_blob_sha": waiter_blob,
            "launcher_source_revision": launcher_source_revision,
            "launcher_blob_sha": launcher_blob,
            "launcher_executed_sha256": _git_blob_sha256(
                wave,
                launcher_revision,
                "tools/acceptance_launcher.py",
            ),
            "waiter_executed_sha256": _git_blob_sha256(
                wave,
                tested_tip,
                "tools/dev_wave_wait.py",
            ),
            "runner_executed_sha256": _receipt_blob_sha256(
                wave,
                runner_digest_revision or tested_main,
                "tools/run_tests.py",
            ),
            "env_projection": {
                "PYTEST_ADDOPTS": None,
                "PYTEST_PLUGINS": None,
                "IZANAGI_TASK_RUN_ID": None,
                "IZANAGI_TASK_RUNS_ROOT": None,
            },
            "effective_scheduler": "serial",
            "verdict": "child-green",
            "log_sha256": hashlib.sha256(b"").hexdigest(),
            "checker_rc": None,
            "checker_status": None,
            "checker_blob_sha": None,
            "checker_receipt_sha256": None,
            "red_nodeids": [],
            "flake_nodeids": [],
        }
        path = self.root / "acceptance-receipt.json"
        path.write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="ascii",
        )
        return path


@contextlib.contextmanager
def _repo(*, waves: tuple[tuple[str, str], ...] = (("codex", "one"),)):
    fixture = _Repo(waves=waves)
    try:
        yield fixture
    finally:
        fixture.close()


def _add_detached_worktree(repo: _Repo, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(repo.main, "worktree", "add", "--detach", str(path), repo.base)
    dotgit = (path / ".git").read_text(encoding="utf-8")
    assert dotgit.startswith("gitdir: ")
    admin = Path(dotgit.removeprefix("gitdir: ").strip())
    assert admin.is_absolute() and admin.is_dir()
    return admin


def _worktree_porcelain(repo: _Repo) -> bytes:
    result = LAND._git(repo.main, "worktree", "list", "--porcelain")
    assert result.returncode == 0, result.stderr
    return result.stdout


@contextlib.contextmanager
def _verified_repository(repo: _Repo, wave: Path):
    request = repo.request(wave, tip=_git(wave, "rev-parse", "HEAD"))
    with _cwd(wave):
        repository = LAND._verify_repository(request)
        try:
            yield repository
        finally:
            repository.close()


def _fake_gate_receipt(plan):
    raw_digests = tuple(
        (
            target.path,
            hashlib.sha256(target.after_bytes).hexdigest(),
        )
        for target in plan.targets
    )
    return LAND._FoldGateReceipt(
        plan,
        plan.transaction_id,
        "0" * 64,
        (),
        raw_digests,
        LAND._FOLD_GATE_OUTCOME,
        (),
    )


def _verify_fake_gate_receipt(_repo, receipt, plan):
    assert receipt.plan is plan
    assert receipt.transaction_id == plan.transaction_id
    assert receipt.target_raw_digests == tuple(
        (
            target.path,
            hashlib.sha256(target.after_bytes).hexdigest(),
        )
        for target in plan.targets
    )
    return LAND._FoldGateSelection("0" * 64, (), (), ())


def _durable_fake_gate_receipt(fold, plan):
    return fold.FoldGateReceipt(
        plan.transaction_id,
        "0" * 64,
        (),
        tuple(
            (
                target.path,
                hashlib.sha256(target.after_bytes).hexdigest(),
            )
            for target in plan.targets
        ),
        LAND._FOLD_GATE_OUTCOME,
        (),
    )


def _land_real_gate(request):
    with _cwd(request.wave_worktree):
        return LAND.land(request)


def _land(request):
    """既存 land tests は新 gate の private seam だけを固定して射程を保つ。"""

    with (
        _patched_land_attr(
            "_run_fold_gate",
            lambda _repository, plan, _tip: _fake_gate_receipt(plan),
        ),
        _patched_land_attr(
            "_fold_gate_receipt_from_plan",
            _fake_gate_receipt,
        ),
        _patched_land_attr(
            "_verify_fold_gate_receipt",
            _verify_fake_gate_receipt,
        ),
        _patched_land_attr(
            "_verify_folded_fragment_receipts",
            lambda _repo, _plan: None,
        ),
    ):
        return _land_real_gate(request)


class _FakeLandLockRuntime:
    def __init__(self) -> None:
        self.now_s = 0.0
        self.sleeps: list[float] = []
        self.delay_caps: list[float] = []
        self.on_sleep = None

    def now(self) -> float:
        return self.now_s

    def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.now_s += delay
        if self.on_sleep is not None:
            self.on_sleep(self)

    def jitter(self, delay_cap: float) -> float:
        self.delay_caps.append(delay_cap)
        return delay_cap

    @contextlib.contextmanager
    def patch(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(_patched_land_attr("_land_lock_now", self.now))
            stack.enter_context(_patched_land_attr("_land_lock_sleep", self.sleep))
            stack.enter_context(_patched_land_attr("_land_lock_jitter", self.jitter))
            yield self


@contextlib.contextmanager
def _held_land_lock(repo: _Repo):
    path = repo.main / ".git" / "dev-wave-land.lock"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield fd
    finally:
        os.close(fd)


def _land_cli_argv(request, *prefix: str) -> list[str]:
    argv = [
        *(prefix or (sys.executable, str(HELPER_PATH))),
        "--main-worktree", str(request.main_worktree),
        "--wave-worktree", str(request.wave_worktree),
        "--tested-main-sha", request.tested_main_sha,
        "--tested-wave-tip-sha", request.tested_wave_tip_sha,
        "--acceptance-wave", request.acceptance_wave,
        "--acceptance-receipt", str(request.acceptance_receipt),
    ]
    if request.landing_wave_tip_sha is not None:
        argv.extend(("--landing-wave-tip-sha", request.landing_wave_tip_sha))
    for commit in request.audited_commits:
        argv.extend(("--audited-commit", commit))
    return argv


@contextlib.contextmanager
def _lease_dir_environment(lease_dir: Path):
    name = "IZANAGI_WAVE_LEASE_DIR"
    previous = os.environ.get(name)
    os.environ[name] = str(lease_dir)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


@contextlib.contextmanager
def _patched_window_release(value):
    previous = LAND._wave_land_window.release
    LAND._wave_land_window.release = value
    try:
        yield
    finally:
        LAND._wave_land_window.release = previous


@contextlib.contextmanager
def _patched_window_renew(value):
    previous = LAND._wave_land_window.renew
    LAND._wave_land_window.renew = value
    try:
        yield
    finally:
        LAND._wave_land_window.renew = previous


class _FlushBuffer(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.was_flushed = False

    def flush(self) -> None:
        self.was_flushed = True
        super().flush()


def _invoke_land_main(
    request,
    lease_dir: Path,
    *,
    stdout: io.StringIO | None = None,
) -> tuple[int, dict[str, object], str, str]:
    output = stdout or _FlushBuffer()
    errors = io.StringIO()
    argv = _land_cli_argv(request)[2:]
    with (
        _cwd(request.wave_worktree),
        _lease_dir_environment(lease_dir),
        contextlib.redirect_stdout(output),
        contextlib.redirect_stderr(errors),
    ):
        rc = LAND.main(argv)
    return rc, json.loads(output.getvalue()), output.getvalue(), errors.getvalue()


def _claim_acceptance_lease(repo: _Repo, request) -> tuple[Path, Path]:
    lease_dir = repo.root / "lease"
    lease_dir.mkdir()
    result = LAND._wave_land_window.claim(
        lease_dir,
        request.acceptance_wave,
        request.tested_main_sha,
        LAND._wave_land_window._POLICY_TTL_SECONDS,
    )
    assert result["state"] == "acquired", result
    lease_path = lease_dir / "acceptance.lease"
    assert lease_path.is_file()
    return lease_dir, lease_path


def _receipt_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="ascii"))


def _write_receipt(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )


def _assert_v5_binding_baseline(
    request: object,
    payload: dict[str, object],
    *,
    launcher_matches_selected_revision: bool = True,
) -> None:
    assert LAND._ACCEPTANCE_RECEIPT_SCHEMA == "dev-wave-acceptance-receipt/v5"
    assert payload["schema_version"] == "dev-wave-acceptance-receipt/v5"
    assert LAND._ACCEPTANCE_RECEIPT_FIELDS == (
        _V4_RECEIPT_FIELDS | _V5_BINDING_FIELDS
    )
    assert set(payload) == LAND._ACCEPTANCE_RECEIPT_FIELDS
    source = payload["launcher_source_revision"]
    assert LAND._ACCEPTANCE_AUTHORITY_KINDS == _EXPECTED_AUTHORITY_KINDS
    assert source in _EXPECTED_AUTHORITY_KINDS
    assert payload["authority_kind"] == _EXPECTED_AUTHORITY_KINDS[source]
    launcher_revision = (
        request.tested_main_sha
        if source == "tested-main"
        else request.tested_wave_tip_sha
    )
    launcher_line = _git(
        request.wave_worktree,
        "ls-tree",
        launcher_revision,
        "--",
        "tools/acceptance_launcher.py",
    )
    launcher_fields = launcher_line.split()
    assert launcher_fields[:2] in (["100644", "blob"], ["100755", "blob"])
    launcher_blob = launcher_fields[2]
    assert _git(
        request.wave_worktree,
        "cat-file",
        "-t",
        launcher_blob,
    ) == "blob"
    if launcher_matches_selected_revision:
        assert payload["launcher_blob_sha"] == launcher_blob
        assert payload["launcher_executed_sha256"] == _git_blob_sha256(
            request.wave_worktree,
            launcher_revision,
            "tools/acceptance_launcher.py",
        )
    waiter_blob = _git(
        request.wave_worktree,
        "rev-parse",
        f"{request.tested_wave_tip_sha}:tools/dev_wave_wait.py",
    )
    assert payload["waiter_blob_sha"] == waiter_blob
    assert _git(
        request.wave_worktree,
        "cat-file",
        "-t",
        waiter_blob,
    ) == "blob"
    assert payload["waiter_executed_sha256"] == _git_blob_sha256(
        request.wave_worktree,
        request.tested_wave_tip_sha,
        "tools/dev_wave_wait.py",
    )
    runner_blob = _git(
        request.wave_worktree,
        "rev-parse",
        f"{request.tested_main_sha}:tools/run_tests.py",
    )
    assert _git(
        request.wave_worktree,
        "cat-file",
        "-t",
        runner_blob,
    ) == "blob"
    assert payload["runner_executed_sha256"] == _git_blob_sha256(
        request.wave_worktree,
        request.tested_main_sha,
        "tools/run_tests.py",
    )


def _change_one_hex_digit(value: object) -> str:
    assert isinstance(value, str) and re.fullmatch(r"[0-9a-f]+", value)
    replacement = "1" if value[0] == "0" else "0"
    return replacement + value[1:]


def _non_attributable_payload(
    request: object,
    *,
    child_rc: int = 1,
    red_nodeids: list[str] | None = None,
    flake_nodeids: list[str] | None = None,
) -> dict[str, object]:
    payload = _receipt_payload(request.acceptance_receipt)
    checker_blob = _git(
        request.wave_worktree,
        "rev-parse",
        f"{request.tested_wave_tip_sha}:tools/check_acceptance_reds.py",
    )
    payload.update({
        "verdict": "non-attributable-only",
        "child_rc": child_rc,
        "checker_rc": 0,
        "checker_status": "non-attributable-only",
        "checker_blob_sha": checker_blob,
        "checker_receipt_sha256": hashlib.sha256(
            b"synthetic checker receipt"
        ).hexdigest(),
        "red_nodeids": (
            ["orchestrator/tests/test_known.py::test_known"]
            if red_nodeids is None
            else red_nodeids
        ),
        "flake_nodeids": [] if flake_nodeids is None else flake_nodeids,
    })
    return payload


def _handoff_text(repo: _Repo, *, state: str = "作業中", base: str | None = None) -> str:
    return (
        "# foreign wave\n"
        "- 目的: parallel control plane\n"
        f"- 状態: {state}\n"
        "- 最終更新: 2000-01-01\n"
        f"- 基準コミット: {repo.base if base is None else base}\n"
        "\n"
        "## 完了した中間成果\n\nnone\n"
        "## 未完の作業と次の一手\n\ncontinue\n"
        "## 落とし穴・気づき\n\nnone\n"
    )


def _handoff(repo: _Repo, *, state: str = "作業中", name: str = "foreign.md") -> Path:
    path = repo.main / "docs" / "handoff" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_handoff_text(repo, state=state), encoding="utf-8")
    return path


def _snapshot(path: Path) -> tuple[bytes, tuple[int, int, int]]:
    metadata = path.lstat()
    return (
        path.read_bytes(),
        (metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)),
    )


def _artifact_snapshot(path: Path) -> tuple[object, tuple[object, ...]]:
    """型を問わず foreign artifact の中身と identity を採取する。

    ``_snapshot`` は regular file 専用なので、symlink / fifo / directory /
    読めない file でも「land が一切触っていない」ことを主張できる形へ広げる。
    """
    metadata = path.lstat()
    identity = (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_nlink,
        metadata.st_size,
    )
    if stat.S_ISLNK(metadata.st_mode):
        payload: object = os.readlink(path)
    elif stat.S_ISDIR(metadata.st_mode):
        payload = sorted(os.listdir(path))
    elif stat.S_ISREG(metadata.st_mode):
        try:
            payload = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            payload = f"unreadable:{exc.errno}"
    else:
        payload = None
    return payload, identity


# T-220 択 (a): docs/handoff/ 直下の型・名前・大きさ・link 数・encoding・schema は
# land の受理集合に入らない。旧実装が per-file の大域拒否を出していた 15 形を列挙する。
_FOREIGN_HANDOFF_KINDS = (
    "malformed",
    "symlink",
    "fifo",
    "directory",
    "non-md-suffix",
    "editor-swap",
    "editor-backup",
    "non-ascii-name",
    "oversize",
    "hard-link",
    "unreadable",
    "empty",
    "non-utf8",
    "unknown-state",
    "empty-base-commit",
)


def _make_foreign_handoff(repo: _Repo, kind: str) -> Path:
    """docs/handoff 直下に kind に対応する異形エントリを 1 つ作る。"""
    handoff = repo.main / "docs" / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    if kind == "malformed":
        path = handoff / "malformed.md"
        path.write_text("# missing schema\n", encoding="utf-8")
    elif kind == "symlink":
        path = handoff / "symlink.md"
        path.symlink_to(repo.main / "base.txt")
    elif kind == "fifo":
        path = handoff / "fifo.md"
        os.mkfifo(path)
    elif kind == "directory":
        path = handoff / "archive"
        path.mkdir()
        (path / "old.md").write_text(_handoff_text(repo), encoding="utf-8")
    elif kind == "non-md-suffix":
        path = handoff / "notes.txt"
        path.write_text("scratch notes\n", encoding="utf-8")
    elif kind == "editor-swap":
        path = handoff / ".foo.md.swp"
        path.write_bytes(b"b0VIM 8.0\x00\x00")
    elif kind == "editor-backup":
        path = handoff / "foo.md~"
        path.write_text(_handoff_text(repo), encoding="utf-8")
    elif kind == "non-ascii-name":
        path = handoff / "引き継ぎ.md"
        path.write_text(_handoff_text(repo), encoding="utf-8")
    elif kind == "oversize":
        path = handoff / "oversize.md"
        path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    elif kind == "hard-link":
        path = handoff / "linked.md"
        peer = repo.root / "handoff-hardlink-peer.md"
        peer.write_text(_handoff_text(repo), encoding="utf-8")
        os.link(peer, path)
    elif kind == "unreadable":
        path = handoff / "sealed.md"
        path.write_text(_handoff_text(repo), encoding="utf-8")
        path.chmod(0o000)
    elif kind == "empty":
        path = handoff / "empty.md"
        path.write_bytes(b"")
    elif kind == "non-utf8":
        path = handoff / "binary.md"
        path.write_bytes(b"# \xff\xfe not utf-8\n")
    elif kind == "unknown-state":
        path = handoff / "unknown-state.md"
        path.write_text(_handoff_text(repo, state="完了"), encoding="utf-8")
    elif kind == "empty-base-commit":
        # 旧 _validate_handoff_at:572 は "".split()[0] で IndexError を投げ、
        # rc 契約外の素の例外が land() を貫通していた形。
        path = handoff / "empty-base.md"
        path.write_text(_handoff_text(repo, base=""), encoding="utf-8")
    else:  # pragma: no cover - 列挙漏れの自己検査
        raise AssertionError(f"unknown foreign handoff kind: {kind}")
    return path


def _make_all_foreign_handoffs(repo: _Repo) -> dict[str, Path]:
    entries = {kind: _make_foreign_handoff(repo, kind) for kind in _FOREIGN_HANDOFF_KINDS}
    assert len(entries) == len(_FOREIGN_HANDOFF_KINDS) == 15
    assert len({path.name for path in entries.values()}) == 15
    return entries


_SYNTHETIC_ACCEPTANCE = r"""
import json
import os
import subprocess
import sys

git, tested_main, tested_tip, tested_tree = sys.argv[1:]

def run(*args):
    completed = subprocess.run(
        [git, "-C", os.getcwd(), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or f"git rc={completed.returncode}")
    return completed.stdout.strip()

observed_tip = run("rev-parse", "--verify", "HEAD")
observed_tree = run("rev-parse", "--verify", "HEAD^{tree}")
if observed_tip != tested_tip or observed_tree != tested_tree:
    raise SystemExit("acceptance HEAD/tree mismatch")
if subprocess.run(
    [git, "-C", os.getcwd(), "merge-base", "--is-ancestor",
     tested_main, tested_tip],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
).returncode != 0:
    raise SystemExit("tested main is not an ancestor of tested tip")
if run("status", "--porcelain=v1", "--ignore-submodules=none"):
    raise SystemExit("acceptance worktree is dirty")
for relative, expected in (
    ("winner.txt", "winner\n"),
    ("loser.txt", "loser\n"),
):
    with open(relative, encoding="utf-8") as stream:
        if stream.read() != expected:
            raise SystemExit(f"{relative} content mismatch")
print(json.dumps({
    "tested_main": tested_main,
    "tested_tip": observed_tip,
    "tested_tree": observed_tree,
}, sort_keys=True))
"""


def _run_synthetic_acceptance(
    wave: Path, *, tested_main: str, tested_tip: str, tested_tree: str
) -> dict[str, str]:
    """再同期 tip の内容・tree・cleanliness を実行して receipt を返す。"""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _SYNTHETIC_ACCEPTANCE,
            REAL_GIT,
            tested_main,
            tested_tip,
            tested_tree,
        ],
        cwd=wave,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert set(receipt) == {"tested_main", "tested_tip", "tested_tree"}
    return receipt


def test_basic_land_accepts_registered_claude_and_codex_children() -> None:
    """M10/M11: valid foreign handoff と両 container は正例である。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo, state="計測中")
        watched = {
            handoff: _snapshot(handoff),
            repo.waves["foreign"] / ".git": _snapshot(repo.waves["foreign"] / ".git"),
        }
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "author.txt").read_text() == "author\n"
        assert {path: _snapshot(path) for path in watched} == watched


def test_land_accepts_receipt_bound_to_wave_tip_and_emits_digest() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        raw = request.acceptance_receipt.read_bytes()

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_receipt_sha256 == hashlib.sha256(raw).hexdigest()
        assert result.acceptance_verdict == "child-green"
        assert result.acceptance_red_nodeids == ()
        assert result.acceptance_flake_nodeids == ()
        assert result.as_json()["acceptance_receipt_sha256"] == hashlib.sha256(
            raw
        ).hexdigest()
        assert result.as_json()["acceptance_verdict"] == "child-green"
        assert result.as_json()["acceptance_red_nodeids"] == []
        assert result.as_json()["acceptance_flake_nodeids"] == []
        assert _git(repo.main, "rev-parse", "HEAD") == tip


@pytest.mark.parametrize("scheduler", ["serial", "loadgroup"])
def test_land_accepts_effective_scheduler(scheduler: str) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        payload["effective_scheduler"] = scheduler
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result


def test_sharding_does_not_add_receipt_fields_or_expand_land_acceptance() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        payload["shard_count"] = 2
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"


def _assert_standard_v5_positive_control() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result


def _assert_tip_launcher_positive_control() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/acceptance_launcher.py",
            "raise SystemExit(9)\n",
        )
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result


def _assert_bootstrap_positive_control() -> None:
    with _repo(waves=()) as repo:
        _git(repo.main, "rm", "tools/acceptance_launcher.py")
        _git(repo.main, "commit", "-qm", "remove launcher")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        wave = repo.add_wave("codex", "one")
        tip = repo.commit(
            wave,
            "tools/acceptance_launcher.py",
            "raise SystemExit(0)\n",
        )
        result = _land(repo.request(wave, base=repo.base, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result


def test_m4_runner_executed_digest_mismatch_is_rejected() -> None:
    _assert_standard_v5_positive_control()
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        _assert_v5_binding_baseline(request, payload)
        payload["runner_executed_sha256"] = _change_one_hex_digit(
            payload["runner_executed_sha256"]
        )
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"
        assert result.retryable_same_request is False


def test_m5_waiter_executed_digest_mismatch_is_rejected() -> None:
    _assert_standard_v5_positive_control()
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        _assert_v5_binding_baseline(request, payload)
        payload["waiter_executed_sha256"] = _change_one_hex_digit(
            payload["waiter_executed_sha256"]
        )
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"
        assert result.retryable_same_request is False


def test_m6_trusted_launcher_digest_is_selected_from_tested_main() -> None:
    _assert_tip_launcher_positive_control()
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/acceptance_launcher.py",
            "raise SystemExit(6)\n",
        )
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        tip_launcher_blob = _git(
            wave,
            "rev-parse",
            f"{tip}:tools/acceptance_launcher.py",
        )
        assert tip_launcher_blob != payload["launcher_blob_sha"]
        payload["launcher_blob_sha"] = tip_launcher_blob
        payload["launcher_executed_sha256"] = _git_blob_sha256(
            wave,
            tip,
            "tools/acceptance_launcher.py",
        )
        assert _git(wave, "cat-file", "-t", tip_launcher_blob) == "blob"
        assert payload["launcher_blob_sha"] == tip_launcher_blob
        assert payload["launcher_executed_sha256"] == _git_blob_sha256(
            wave,
            tip,
            "tools/acceptance_launcher.py",
        )
        _assert_v5_binding_baseline(
            request,
            payload,
            launcher_matches_selected_revision=False,
        )
        assert payload["launcher_executed_sha256"] != _git_blob_sha256(
            wave,
            request.tested_main_sha,
            "tools/acceptance_launcher.py",
        )
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"
        assert result.retryable_same_request is False


def test_m7_bootstrap_is_rejected_when_tested_main_has_launcher() -> None:
    _assert_tip_launcher_positive_control()
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/acceptance_launcher.py",
            "raise SystemExit(7)\n",
        )
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        payload["launcher_source_revision"] = "tested-tip-bootstrap"
        payload["authority_kind"] = LAND._ACCEPTANCE_AUTHORITY_KINDS[
            "tested-tip-bootstrap"
        ]
        payload["launcher_blob_sha"] = _git(
            wave,
            "rev-parse",
            f"{tip}:tools/acceptance_launcher.py",
        )
        payload["launcher_executed_sha256"] = _git_blob_sha256(
            wave,
            tip,
            "tools/acceptance_launcher.py",
        )
        _assert_v5_binding_baseline(request, payload)
        assert _git(
            wave,
            "ls-tree",
            request.tested_main_sha,
            "--",
            "tools/acceptance_launcher.py",
        )
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"


def test_m10_bootstrap_rejects_locked_main_with_launcher() -> None:
    _assert_bootstrap_positive_control()
    with _repo() as repo:
        wave = repo.waves["one"]
        _git(repo.main, "rm", "tools/acceptance_launcher.py")
        _git(repo.main, "commit", "-qm", "remove launcher")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        (repo.main / "tools/acceptance_launcher.py").write_text(
            "raise SystemExit(0)\n", encoding="utf-8"
        )
        _git(repo.main, "add", "tools/acceptance_launcher.py")
        _git(repo.main, "commit", "-qm", "restore trusted launcher")
        _git(wave, "merge", "--ff-only", "main")
        tip = repo.commit(
            wave,
            "tools/acceptance_launcher.py",
            "raise SystemExit(10)\n",
        )
        request = repo.request(wave, base=repo.base, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        _assert_v5_binding_baseline(request, payload)
        assert payload["launcher_source_revision"] == "tested-tip-bootstrap"
        assert not _git(
            wave,
            "ls-tree",
            request.tested_main_sha,
            "--",
            "tools/acceptance_launcher.py",
        )
        assert _git(
            repo.main,
            "ls-tree",
            "HEAD",
            "--",
            "tools/acceptance_launcher.py",
        )
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"


def test_m11_otherwise_valid_complete_v4_receipt_is_rejected() -> None:
    _assert_standard_v5_positive_control()
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        _assert_v5_binding_baseline(request, payload)
        payload["schema_version"] = "dev-wave-acceptance-receipt/v4"
        payload["authority_kind"] = "dev-wave-wait-acceptance"
        for field in _V5_BINDING_FIELDS:
            del payload[field]
        assert set(payload) == _V4_RECEIPT_FIELDS
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, result
        assert result.reason == "acceptance-receipt-rejected"


_TAMPER_CASES = (
    "schema",
    "authority",
    "wave",
    "holder",
    "tested-main",
    "tip",
    "argv",
    "runner",
    "child-rc",
    "log-sha256",
    "verdict",
    "fingerprint-validity",
    "fingerprint-equality",
    "env-projection",
    "missing-scheduler",
    "unknown-scheduler",
    "non-string-scheduler",
    "waiter-blob",
    "duplicate-key",
    "unknown-field",
    "missing-flake-nodeids",
    "v3-schema",
)


@pytest.mark.parametrize("case", _TAMPER_CASES, ids=_TAMPER_CASES)
def test_land_rejects_tampered_acceptance_receipt(case: str) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        receipt = request.acceptance_receipt
        payload = _receipt_payload(receipt)
        if case == "schema":
            payload["schema_version"] = "dev-wave-acceptance-receipt/v2"
        elif case == "v3-schema":
            payload["schema_version"] = "dev-wave-acceptance-receipt/v3"
        elif case == "authority":
            payload["authority_kind"] = "direct-test-run"
        elif case == "tip":
            payload["tested_tip"] = repo.base
        elif case == "tested-main":
            payload["tested_main"] = tip
        elif case == "wave":
            payload["acceptance_wave"] = "other-wave"
        elif case == "holder":
            payload["lease_holder"] = "0" * 12
        elif case == "argv":
            payload["argv"] = ["python3", "-c", "pass"]
        elif case == "runner":
            payload["resolved_runner_path"] = "tools/other.py"
        elif case == "child-rc":
            payload["child_rc"] = 1
        elif case == "log-sha256":
            payload["log_sha256"] = "not-a-sha256"
        elif case == "verdict":
            payload["verdict"] = "green"
        elif case == "fingerprint-validity":
            payload["pre_fingerprint"]["digest"] = "not-a-sha256"
            payload["post_fingerprint"] = dict(payload["pre_fingerprint"])
        elif case == "fingerprint-equality":
            payload["post_fingerprint"]["digest"] = "f" * 64
        elif case == "env-projection":
            payload["env_projection"]["PYTEST_ADDOPTS"] = "-k nothing"
        elif case == "missing-scheduler":
            del payload["effective_scheduler"]
        elif case == "unknown-scheduler":
            payload["effective_scheduler"] = "unknown"
        elif case == "non-string-scheduler":
            payload["effective_scheduler"] = 1
        elif case == "waiter-blob":
            payload["waiter_blob_sha"] = "f" * 40
        elif case == "unknown-field":
            payload["extra"] = "rejected"
        elif case == "missing-flake-nodeids":
            del payload["flake_nodeids"]
        if case == "duplicate-key":
            raw = receipt.read_text(encoding="ascii")
            receipt.write_text(
                raw.replace("{", '{"schema_version":"duplicate",', 1),
                encoding="ascii",
            )
        else:
            _write_receipt(receipt, payload)
        before = _git(repo.main, "rev-parse", "HEAD")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, (case, result)
        assert result.reason == "acceptance-receipt-rejected", (case, result)
        assert _git(repo.main, "rev-parse", "HEAD") == before


test_land_rejects_tampered_acceptance_receipt._plain_cases = tuple(
    (case,) for case in _TAMPER_CASES
)


_VERDICT_INCONSISTENCY_CASES = (
    "green-child-rc",
    "green-checker-rc",
    "green-checker-status",
    "green-checker-blob",
    "green-checker-receipt",
    "green-red-nodeids",
    "green-flake-nodeids",
    "red-child-rc",
    "red-checker-rc-null",
    "red-checker-rc-nonzero",
    "red-checker-status-null",
    "red-checker-blob-null",
    "red-checker-blob-mismatch",
    "red-checker-receipt-null",
    "red-nodeids-empty",
    "red-nodeids-unsorted",
    "red-nodeids-non-string",
    "red-flake-nodeids-unsorted",
    "red-flake-nodeids-duplicate",
    "red-flake-nodeids-non-string",
    "red-nodeids-overlap-flake-nodeids",
)


@pytest.mark.parametrize(
    "case",
    _VERDICT_INCONSISTENCY_CASES,
    ids=_VERDICT_INCONSISTENCY_CASES,
)
def test_land_rejects_verdict_field_inconsistency(case: str) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _receipt_payload(request.acceptance_receipt)
        if case.startswith("red-"):
            payload = _non_attributable_payload(request)
        if case == "green-child-rc":
            payload["child_rc"] = 1
        elif case == "green-checker-rc":
            payload["checker_rc"] = 0
        elif case == "green-checker-status":
            payload["checker_status"] = "non-attributable-only"
        elif case == "green-checker-blob":
            payload["checker_blob_sha"] = "f" * 40
        elif case == "green-checker-receipt":
            payload["checker_receipt_sha256"] = "f" * 64
        elif case == "green-red-nodeids":
            payload["red_nodeids"] = ["test_x.py::test_x"]
        elif case == "green-flake-nodeids":
            payload["flake_nodeids"] = ["test_x.py::test_x"]
        elif case == "red-child-rc":
            payload["child_rc"] = 0
        elif case == "red-checker-rc-null":
            payload["checker_rc"] = None
        elif case == "red-checker-rc-nonzero":
            payload["checker_rc"] = 1
        elif case == "red-checker-status-null":
            payload["checker_status"] = None
        elif case == "red-checker-blob-null":
            payload["checker_blob_sha"] = None
        elif case == "red-checker-blob-mismatch":
            payload["checker_blob_sha"] = "f" * 40
        elif case == "red-checker-receipt-null":
            payload["checker_receipt_sha256"] = None
        elif case == "red-nodeids-empty":
            payload["red_nodeids"] = []
        elif case == "red-nodeids-unsorted":
            payload["red_nodeids"] = ["z.py::test_z", "a.py::test_a"]
        elif case == "red-nodeids-non-string":
            payload["red_nodeids"] = [1]
        elif case == "red-flake-nodeids-unsorted":
            payload["flake_nodeids"] = ["z.py::test_z", "a.py::test_a"]
        elif case == "red-flake-nodeids-duplicate":
            payload["flake_nodeids"] = ["a.py::test_a", "a.py::test_a"]
        elif case == "red-flake-nodeids-non-string":
            payload["flake_nodeids"] = [1]
        elif case == "red-nodeids-overlap-flake-nodeids":
            payload["flake_nodeids"] = list(payload["red_nodeids"])
        _write_receipt(request.acceptance_receipt, payload)
        before = _git(repo.main, "rev-parse", "HEAD")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT, (case, result)
        assert result.reason == "acceptance-receipt-rejected", (case, result)
        assert _git(repo.main, "rev-parse", "HEAD") == before


test_land_rejects_verdict_field_inconsistency._plain_cases = tuple(
    (case,) for case in _VERDICT_INCONSISTENCY_CASES
)


def test_land_accepts_non_attributable_receipt_and_emits_red_nodeids() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _non_attributable_payload(request, child_rc=1)
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_verdict == "non-attributable-only"
        assert result.acceptance_red_nodeids == (
            "orchestrator/tests/test_known.py::test_known",
        )
        assert result.as_json()["acceptance_red_nodeids"] == [
            "orchestrator/tests/test_known.py::test_known"
        ]
        assert result.acceptance_flake_nodeids == ()
        assert result.as_json()["acceptance_flake_nodeids"] == []


def test_land_accepts_flake_only_and_emits_flake_nodeids() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        flake = "orchestrator/tests/test_flake.py::test_flake"
        payload = _non_attributable_payload(
            request,
            red_nodeids=[],
            flake_nodeids=[flake],
        )
        _write_receipt(request.acceptance_receipt, payload)
        raw = request.acceptance_receipt.read_bytes()

        assert LAND._release_authority_digest(
            request.acceptance_receipt,
            request.acceptance_wave,
        ) == hashlib.sha256(raw).hexdigest()
        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_red_nodeids == ()
        assert result.acceptance_flake_nodeids == (flake,)
        assert result.as_json()["acceptance_red_nodeids"] == []
        assert result.as_json()["acceptance_flake_nodeids"] == [flake]


def test_land_accepts_mixed_red_and_flake_nodeids_without_merging_sets() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        red = "orchestrator/tests/test_known.py::test_known"
        flake = "orchestrator/tests/test_flake.py::test_flake"
        payload = _non_attributable_payload(
            request,
            red_nodeids=[red],
            flake_nodeids=[flake],
        )
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_red_nodeids == (red,)
        assert result.acceptance_flake_nodeids == (flake,)
        assert result.as_json()["acceptance_red_nodeids"] == [red]
        assert result.as_json()["acceptance_flake_nodeids"] == [flake]


def test_land_accepts_child_green_tip_runner_change_with_main_digest() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/run_tests.py",
            "raise SystemExit(7)\n",
        )
        assert _git(
            wave, "rev-parse", f"{repo.base}:tools/run_tests.py"
        ) != _git(wave, "rev-parse", f"{tip}:tools/run_tests.py")
        request = repo.request(
            wave,
            tip=tip,
            runner_digest_revision=repo.base,
        )
        payload = _receipt_payload(request.acceptance_receipt)
        assert payload["runner_executed_sha256"] == _git_blob_sha256(
            wave,
            repo.base,
            "tools/run_tests.py",
        )
        assert payload["runner_executed_sha256"] != _git_blob_sha256(
            wave,
            tip,
            "tools/run_tests.py",
        )
        lookups = []
        real_runner_tree_entry = LAND._runner_tree_entry

        def spy_runner_tree_entry(repository, revision):
            lookups.append(revision)
            return real_runner_tree_entry(repository, revision)

        with _patched_land_attr("_runner_tree_entry", spy_runner_tree_entry):
            result = _land(request)

        assert lookups == [tip, repo.base]
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_verdict == "child-green"
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_d987_rejects_final_runner_change_before_provenance_rc16() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_main = repo.base
        tip = repo.commit(wave, "wave.txt", "wave\n")
        assert tested_main != tip
        assert _git(
            wave, "rev-parse", f"{tested_main}:tools/run_tests.py"
        ) == _git(wave, "rev-parse", f"{tip}:tools/run_tests.py")
        request = repo.request(
            wave,
            base=tested_main,
            tip=tip,
            runner_digest_revision=tested_main,
        )
        locked_main = repo.commit(
            repo.main,
            "tools/run_tests.py",
            "raise SystemExit(9)\n",
        )
        assert locked_main != tested_main
        assert _git(
            repo.main,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            locked_main,
        ) == "tools/run_tests.py"
        assert _git(
            wave, "rev-parse", f"{locked_main}:tools/run_tests.py"
        ) != _git(wave, "rev-parse", f"{tested_main}:tools/run_tests.py")
        _git(wave, "merge", "--no-ff", "--no-edit", locked_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")
        request = dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        )
        lookups = []
        real_runner_tree_entry = LAND._runner_tree_entry

        def spy_runner_tree_entry(repository, revision):
            lookups.append(revision)
            return real_runner_tree_entry(repository, revision)

        provenance_calls = []

        def provenance_rc16(*args):
            provenance_calls.append(args)
            return subprocess.CompletedProcess([], 16, b"", b"")

        with (
            _patched_land_attr("_runner_tree_entry", spy_runner_tree_entry),
            _patched_land_attr("_run_provenance_checker", provenance_rc16),
        ):
            result = _land(request)

        assert lookups == [locked_main, tested_main]
        assert provenance_calls == []
        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == locked_main


def test_d987_post_provenance_recheck_rejects_after_second_preflight() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, incorporated, _merge_commits = _forward_merge_request(
            repo,
            wave,
            count=1,
        )
        main_before = _git(repo.main, "rev-parse", "HEAD")
        assert main_before == incorporated[-1]
        events = []
        d987_calls = 0
        real_preflight = LAND._locked_preflight
        real_provenance = LAND._audit_provenance_history
        real_d987 = LAND._verify_forward_main_runner_blob

        def spy_preflight(*args, **kwargs):
            events.append("preflight")
            return real_preflight(*args, **kwargs)

        def spy_provenance(*args, **kwargs):
            events.append("provenance")
            return real_provenance(*args, **kwargs)

        def reject_only_after_provenance(repository, tested_main, merges):
            nonlocal d987_calls
            d987_calls += 1
            events.append("d987")
            if d987_calls == 1:
                return real_d987(repository, tested_main, merges)
            raise LAND._acceptance_rejected()

        with (
            _patched_land_attr("_locked_preflight", spy_preflight),
            _patched_land_attr("_audit_provenance_history", spy_provenance),
            _patched_land_attr(
                "_verify_forward_main_runner_blob",
                reject_only_after_provenance,
            ),
        ):
            result = _land(request)

        assert events == [
            "preflight",
            "d987",
            "provenance",
            "preflight",
            "d987",
        ]
        assert d987_calls == 2
        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == "acceptance-receipt-rejected"
        assert result.incorporated_main_shas == incorporated
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == main_before


def test_land_rejects_tip_runner_digest_instead_of_tested_main_digest() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/run_tests.py",
            "raise SystemExit(7)\n",
        )
        request = repo.request(
            wave,
            tip=tip,
            runner_digest_revision=tip,
        )
        before = _git(repo.main, "rev-parse", "HEAD")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == before


def test_main_tip_runner_divergence_reaches_retryable_checker_lookup_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/run_tests.py",
            "raise SystemExit(7)\n",
        )
        assert _git(
            wave, "rev-parse", f"{repo.base}:tools/run_tests.py"
        ) != _git(wave, "rev-parse", f"{tip}:tools/run_tests.py")
        request = repo.request(wave, tip=tip)
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)
        real_git = LAND._git
        checker_lookups = []

        def fail_checker_lookup(repo_path: Path, *args: str, **kwargs):
            if (
                args[:1] == ("rev-parse",)
                and len(args) == 2
                and args[1].endswith(":tools/check_acceptance_reds.py")
            ):
                checker_lookups.append(args[1])
                return LAND._GitResult(
                    128,
                    b"",
                    b"synthetic checker lookup process failure",
                )
            return real_git(repo_path, *args, **kwargs)

        with _patched_land_attr("_git", fail_checker_lookup):
            result = _land(request)

        assert checker_lookups == [
            f"{repo.base}:tools/check_acceptance_reds.py",
            f"{tip}:tools/check_acceptance_reds.py",
        ]
        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            False,
            True,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_land_runner_path_absence_is_permanent_rejection() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        _git(repo.main, "rm", "tools/run_tests.py")
        _git(repo.main, "commit", "-qm", "remove runner")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", "main")
        tip = repo.commit(
            wave,
            "tools/run_tests.py",
            "raise SystemExit(0)\n",
        )
        request = repo.request(
            wave,
            base=repo.base,
            tip=tip,
            runner_digest_revision=tip,
        )
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_land_child_green_runner_path_absence_is_permanent_rejection() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        _git(repo.main, "rm", "tools/run_tests.py")
        _git(repo.main, "commit", "-qm", "remove runner")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", "main")
        tip = repo.commit(
            wave,
            "tools/run_tests.py",
            "raise SystemExit(0)\n",
        )
        request = repo.request(
            wave,
            base=repo.base,
            tip=tip,
            runner_digest_revision=tip,
        )

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


_RUNNER_ENTRY_SHAPE_CASES = (
    "main-blob-tip-tree",
    "main-tree-tip-blob",
    "main-blob-tip-missing",
)


@pytest.mark.parametrize(
    "case",
    _RUNNER_ENTRY_SHAPE_CASES,
    ids=_RUNNER_ENTRY_SHAPE_CASES,
)
def test_land_runner_entry_shape_is_permanent_rejection(case: str) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        if case == "main-tree-tip-blob":
            main_runner = repo.main / "tools/run_tests.py"
            main_runner.unlink()
            main_runner.mkdir()
            (main_runner / "entry").write_text("tree object\n", encoding="utf-8")
            _git(repo.main, "add", "-A", "tools/run_tests.py")
            _git(repo.main, "commit", "-qm", "replace main runner with tree")
            repo.base = _git(repo.main, "rev-parse", "HEAD")
            _git(wave, "merge", "--ff-only", "main")
            shutil.rmtree(wave / "tools/run_tests.py")
            (wave / "tools/run_tests.py").write_text(
                "raise SystemExit(0)\n",
                encoding="utf-8",
            )
            _git(wave, "add", "-A", "tools/run_tests.py")
            _git(wave, "commit", "-qm", "restore tip runner blob")
        elif case == "main-blob-tip-tree":
            tip_runner = wave / "tools/run_tests.py"
            tip_runner.unlink()
            tip_runner.mkdir()
            (tip_runner / "entry").write_text("tree object\n", encoding="utf-8")
            _git(wave, "add", "-A", "tools/run_tests.py")
            _git(wave, "commit", "-qm", "replace tip runner with tree")
        else:
            _git(wave, "rm", "tools/run_tests.py")
            _git(wave, "commit", "-qm", "remove tip runner")
        tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, base=repo.base, tip=tip)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


test_land_runner_entry_shape_is_permanent_rejection._plain_cases = tuple(
    (case,) for case in _RUNNER_ENTRY_SHAPE_CASES
)


def test_land_runner_lookup_process_failure_is_retryable() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)
        real_git = LAND._git

        def fail_runner_lookup(repo_path: Path, *args: str, **kwargs):
            if args[:3] == ("ls-tree", "-z", "--full-tree") and args[-2:] == (
                "--",
                "tools/run_tests.py",
            ):
                return LAND._GitResult(
                    128,
                    b"",
                    b"synthetic git process failure",
                )
            return real_git(repo_path, *args, **kwargs)

        with _patched_land_attr("_git", fail_runner_lookup):
            result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            False,
            True,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_land_child_green_runner_lookup_process_failure_is_retryable() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        real_git = LAND._git
        lookups = []

        def fail_tested_main_runner_lookup(
            repo_path: Path,
            *args: str,
            **kwargs,
        ):
            if args[:3] == ("ls-tree", "-z", "--full-tree") and args[-2:] == (
                "--",
                "tools/run_tests.py",
            ):
                lookups.append(args[3])
                if args[3] == request.tested_main_sha:
                    return LAND._GitResult(
                        128,
                        b"",
                        b"synthetic tested-main lookup failure",
                    )
            return real_git(repo_path, *args, **kwargs)

        with _patched_land_attr("_git", fail_tested_main_runner_lookup):
            result = _land(request)

        assert lookups == [tip, request.tested_main_sha]
        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            False,
            True,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_land_runner_gate_uses_tested_main_after_main_reaches_tip() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_main = repo.base
        tip = repo.commit(
            wave,
            "tools/run_tests.py",
            "raise SystemExit(7)\n",
        )
        request = repo.request(
            wave,
            base=tested_main,
            tip=tip,
            runner_digest_revision=tip,
        )
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)
        _git(repo.main, "merge", "--ff-only", tip)
        lookups = []
        real_runner_tree_entry = LAND._runner_tree_entry

        def spy_runner_tree_entry(repository, revision):
            lookups.append(revision)
            return real_runner_tree_entry(repository, revision)

        with _patched_land_attr("_runner_tree_entry", spy_runner_tree_entry):
            result = _land(request)

        assert lookups == [tip, tested_main]
        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_land_rejects_non_blob_runner_objects_even_when_trees_match() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / "tools" / "run_tests.py").unlink()
        (repo.main / "tools" / "run_tests.py").mkdir()
        (repo.main / "tools" / "run_tests.py" / "entry").write_text(
            "tree object\n",
            encoding="utf-8",
        )
        _git(repo.main, "add", "-A", "tools/run_tests.py")
        _git(repo.main, "commit", "-qm", "replace runner blob with tree")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", "main")
        tip = repo.commit(wave, "wave.txt", "wave\n")
        assert _git(
            wave, "rev-parse", f"{repo.base}:tools/run_tests.py"
        ) == _git(wave, "rev-parse", f"{tip}:tools/run_tests.py")
        request = repo.request(wave, base=repo.base, tip=tip)
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"


def test_land_accepts_different_commits_with_same_checker_blob() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        assert repo.base != tip
        assert _git(
            wave,
            "rev-parse",
            f"{repo.base}:tools/check_acceptance_reds.py",
        ) == _git(
            wave,
            "rev-parse",
            f"{tip}:tools/check_acceptance_reds.py",
        )
        assert _git(
            wave,
            "rev-parse",
            f"{repo.base}:tools/run_tests.py",
        ) == _git(
            wave,
            "rev-parse",
            f"{tip}:tools/run_tests.py",
        )
        request = repo.request(wave, tip=tip)
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_verdict == "non-attributable-only"


def test_land_rejects_checker_blob_divergence() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/check_acceptance_reds.py",
            "raise SystemExit(1)\n",
        )
        request = repo.request(wave, tip=tip)
        payload = _non_attributable_payload(request)
        _write_receipt(request.acceptance_receipt, payload)
        before = _git(repo.main, "rev-parse", "HEAD")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert _git(repo.main, "rev-parse", "HEAD") == before


@pytest.mark.parametrize(
    "child_rc",
    [0, 2, 13, 16, 23, -signal.SIGTERM],
    ids=("green", "pytest-usage", "deletion-gate", "dispatch", "audit", "signal"),
)
def test_land_rejects_non_attributable_receipt_with_non_pytest_failure_rc(
    child_rc: int,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        payload = _non_attributable_payload(request, child_rc=child_rc)
        _write_receipt(request.acceptance_receipt, payload)
        before = _git(repo.main, "rev-parse", "HEAD")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert _git(repo.main, "rev-parse", "HEAD") == before


def test_land_rejects_invalid_receipt_file_without_main_change() -> None:
    for case in ("missing", "symlink", "oversize"):
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            request = repo.request(wave, tip=tip)
            receipt = request.acceptance_receipt
            if case == "missing":
                receipt.unlink()
            elif case == "symlink":
                receipt.unlink()
                receipt.symlink_to(repo.root / "missing-target")
            else:
                receipt.write_bytes(
                    b"x" * (LAND._MAX_ACCEPTANCE_RECEIPT_BYTES + 1)
                )
            before = _git(repo.main, "rev-parse", "HEAD")

            result = _land(request)

            assert result.rc == LAND.RC_AUDIT, (case, result)
            assert result.reason == "acceptance-receipt-rejected", (case, result)
            assert _git(repo.main, "rev-parse", "HEAD") == before


def test_land_rejects_complete_orphan_temp_receipt_without_main_change() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        orphan = repo.root / ".dev-wave-acceptance-receipt-orphan.tmp"
        orphan.write_bytes(request.acceptance_receipt.read_bytes())
        request = dataclasses.replace(request, acceptance_receipt=orphan)
        before = _git(repo.main, "rev-parse", "HEAD")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert _git(repo.main, "rev-parse", "HEAD") == before


def test_already_landed_still_requires_acceptance_receipt() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        first = repo.request(wave, tip=tip)
        assert _land(first).rc == LAND.RC_OK
        missing = repo.root / "missing-receipt.json"
        second = dataclasses.replace(first, acceptance_receipt=missing)

        result = _land(second)

        assert result.rc == LAND.RC_AUDIT
        assert result.reason == "acceptance-receipt-rejected"
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_real_waiter_receipt_is_consumed_by_real_land_end_to_end() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        shutil.copy2(
            ROOT / "tools" / "acceptance_launcher.py",
            repo.main / "tools",
        )
        (repo.main / "tools" / "run_tests.py").write_text(
            "import hashlib\n"
            "import json\n"
            "import os\n"
            "from pathlib import Path\n"
            "\n"
            "binding_k = int(os.environ['IZANAGI_ACCEPTANCE_SHARDS'])\n"
            "binding_source = Path(__file__).read_bytes()\n"
            "binding_report = {\n"
            "    'schema_version': 'dev-wave-runner-binding-report/v1',\n"
            "    'tested_main': os.environ[\n"
            "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_TESTED_MAIN'\n"
            "    ],\n"
            "    'nonce': os.environ[\n"
            "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_NONCE'\n"
            "    ],\n"
            "    'runner_executed_sha256': hashlib.sha256(\n"
            "        binding_source\n"
            "    ).hexdigest(),\n"
            "    'shard_count': binding_k,\n"
            "    'shard_index': 0,\n"
            "}\n"
            "binding_line = (json.dumps(\n"
            "    binding_report,\n"
            "    ensure_ascii=True,\n"
            "    sort_keys=True,\n"
            "    separators=(',', ':'),\n"
            ") + '\\n').encode('ascii')\n"
            "os.write(\n"
            "    int(os.environ['IZANAGI_ACCEPTANCE_RUNNER_BINDING_FD']),\n"
            "    binding_line,\n"
            ")\n"
            "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
            "{\"effective_scheduler\":\"serial\"}')\n"
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        _git(
            repo.main,
            "add",
            "tools/acceptance_launcher.py",
            "tools/run_tests.py",
        )
        _git(repo.main, "commit", "-qm", "install real acceptance launcher")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", "main")
        shutil.copy2(ROOT / "tools" / "dev_wave_wait.py", wave / "tools")
        shutil.copy2(ROOT / "tools" / "wave_land_window.py", wave / "tools")
        _git(
            wave,
            "add",
            "tools/dev_wave_wait.py",
            "tools/wave_land_window.py",
        )
        _git(wave, "commit", "-qm", "install real acceptance waiter")
        tip = _git(wave, "rev-parse", "HEAD")
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        receipt_path = repo.root / "real-waiter-receipt.json"
        log_path = repo.root / "real-waiter.log"
        acceptance_wave = "codex-one"
        env = _git_env()
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        env.pop("IZANAGI_TASK_RUN_ID", None)
        env.pop("IZANAGI_TASK_RUNS_ROOT", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["IZANAGI_ACCEPTANCE_SHARDS"] = "1"

        waiter = subprocess.run(
            [
                sys.executable,
                str(wave / "tools" / "dev_wave_wait.py"),
                "acceptance",
                "--wave",
                acceptance_wave,
                "--lease-dir",
                str(lease_dir),
                "--receipt-file",
                str(receipt_path),
                "--log-file",
                str(log_path),
                "--",
                "python3",
                "tools/run_tests.py",
            ],
            cwd=wave,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert waiter.returncode == 0, waiter.stderr
        raw_receipt = receipt_path.read_bytes()
        request = repo.request(
            wave,
            tip=tip,
            acceptance_wave=acceptance_wave,
            acceptance_receipt=receipt_path,
        )

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_receipt_sha256 == hashlib.sha256(
            raw_receipt
        ).hexdigest()
        assert receipt_path.read_bytes() == raw_receipt
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_real_waiter_executes_main_when_tip_runner_differs_and_land_accepts() -> None:
    """Real waiter/launcher executes tested main, then real land consumes it."""
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / "tools" / "run_tests.py").write_text(
            "import hashlib\n"
            "import json\n"
            "import os\n"
            "import sys\n"
            "\n"
            "binding_k = int(os.environ['IZANAGI_ACCEPTANCE_SHARDS'])\n"
            "binding_source = sys._getframe(1).f_locals['source']\n"
            "binding_report = {\n"
            "    'schema_version': 'dev-wave-runner-binding-report/v1',\n"
            "    'tested_main': os.environ[\n"
            "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_TESTED_MAIN'\n"
            "    ],\n"
            "    'nonce': os.environ[\n"
            "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_NONCE'\n"
            "    ],\n"
            "    'runner_executed_sha256': hashlib.sha256(\n"
            "        binding_source\n"
            "    ).hexdigest(),\n"
            "    'shard_count': binding_k,\n"
            "    'shard_index': 0,\n"
            "}\n"
            "binding_line = (json.dumps(\n"
            "    binding_report,\n"
            "    ensure_ascii=True,\n"
            "    sort_keys=True,\n"
            "    separators=(',', ':'),\n"
            ") + '\\n').encode('ascii')\n"
            "os.write(\n"
            "    int(os.environ['IZANAGI_ACCEPTANCE_RUNNER_BINDING_FD']),\n"
            "    binding_line,\n"
            ")\n"
            "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
            "{\"effective_scheduler\":\"serial\"}')\n"
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        shutil.copy2(
            ROOT / "tools" / "acceptance_launcher.py",
            repo.main / "tools",
        )
        _git(
            repo.main,
            "add",
            "tools/run_tests.py",
            "tools/acceptance_launcher.py",
        )
        _git(repo.main, "commit", "-qm", "install synthetic green runner")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", "main")
        shutil.copy2(ROOT / "tools" / "dev_wave_wait.py", wave / "tools")
        shutil.copy2(ROOT / "tools" / "wave_land_window.py", wave / "tools")
        (wave / "tools" / "run_tests.py").write_text(
            "raise SystemExit(97)\n",
            encoding="utf-8",
        )
        _git(
            wave,
            "add",
            "tools/dev_wave_wait.py",
            "tools/wave_land_window.py",
            "tools/run_tests.py",
        )
        _git(
            wave,
            "commit",
            "-qm",
            "install waiter and divergent failing tip runner",
        )
        tip = _git(wave, "rev-parse", "HEAD")
        assert _git(
            wave,
            "rev-parse",
            f"{repo.base}:tools/run_tests.py",
        ) != _git(wave, "rev-parse", f"{tip}:tools/run_tests.py")
        lease_dir = repo.root / "lease-green-inherited"
        lease_dir.mkdir()
        receipt_path = repo.root / "real-green-inherited-receipt.json"
        log_path = repo.root / "real-green-inherited.log"
        acceptance_wave = "codex-one"
        env = _git_env()
        for name in (
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "IZANAGI_TASK_RUN_ID",
            "IZANAGI_TASK_RUNS_ROOT",
        ):
            env.pop(name, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["IZANAGI_ACCEPTANCE_SHARDS"] = "1"

        waiter = subprocess.run(
            [
                sys.executable,
                str(wave / "tools" / "dev_wave_wait.py"),
                "acceptance",
                "--wave",
                acceptance_wave,
                "--lease-dir",
                str(lease_dir),
                "--receipt-file",
                str(receipt_path),
                "--log-file",
                str(log_path),
                "--",
                "python3",
                "tools/run_tests.py",
            ],
            cwd=wave,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert waiter.returncode == 0, waiter.stdout + waiter.stderr
        raw_receipt = receipt_path.read_bytes()
        payload = json.loads(raw_receipt)
        assert payload["verdict"] == "child-green"
        assert payload["child_rc"] == 0
        assert payload["red_nodeids"] == []
        assert payload["flake_nodeids"] == []
        assert payload["runner_executed_sha256"] == _git_blob_sha256(
            wave,
            repo.base,
            "tools/run_tests.py",
        )
        assert payload["runner_executed_sha256"] != _git_blob_sha256(
            wave,
            tip,
            "tools/run_tests.py",
        )
        request = repo.request(
            wave,
            base=repo.base,
            tip=tip,
            acceptance_wave=acceptance_wave,
            acceptance_receipt=receipt_path,
        )
        _assert_v5_binding_baseline(request, payload)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_receipt_sha256 == hashlib.sha256(
            raw_receipt
        ).hexdigest()
        assert result.acceptance_verdict == "child-green"
        assert result.acceptance_red_nodeids == ()
        assert result.acceptance_flake_nodeids == ()
        assert _git(repo.main, "rev-parse", "HEAD") == tip


@pytest.mark.parametrize(
    "missing_option",
    ("--acceptance-receipt", "--acceptance-wave"),
    ids=("acceptance-receipt", "acceptance-wave"),
)
def test_land_cli_requires_acceptance_receipt(missing_option: str) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        argv = _land_cli_argv(request)
        missing_index = argv.index(missing_option)
        del argv[missing_index:missing_index + 2]

        completed = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        assert completed.returncode == 2
        assert missing_option in completed.stderr


def test_handoff_state_vocabulary_is_not_a_land_gate() -> None:
    """[意図した挙動変更] 状態語彙も stale date も land の gate ではない。

    旧 test は三状態だけを ``already-landed`` で確認していた。T-220 択 (a) 後は
    語彙外の値でも受理されるので期待値を反転し、さらに merge を伴う実 land
    (``landed``) で確認する。語彙の検出は check_docs の非阻害 warning へ降格した。
    """
    for state in ("作業中", "計測中", "中断", "完了", "", "arbitrary text"):
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            handoff = _handoff(repo, state=state)
            watched = _artifact_snapshot(handoff)
            result = _land(repo.request(wave, tip=tip))
            assert (result.rc, result.status) == (LAND.RC_OK, "landed"), (state, result)
            assert _git(repo.main, "rev-parse", "HEAD") == tip
            assert _artifact_snapshot(handoff) == watched, state


def test_colliding_untracked_rejected_without_main_or_foreign_artifact_change() -> None:
    """M4: land target と衝突する untracked は拒否し main を変更しない。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo)
        collision = repo.main / "author.txt"
        collision.write_text("foreign untracked\n", encoding="utf-8")
        watched = {
            handoff: _snapshot(handoff),
            repo.waves["foreign"] / ".git": _snapshot(repo.waves["foreign"] / ".git"),
            collision: _snapshot(collision),
        }
        before = _git(repo.main, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT and result.status == "rejected", result
        assert _git(repo.main, "rev-parse", "HEAD") == before
        assert {path: _snapshot(path) for path in watched} == watched


def test_noncolliding_foreign_session_untracked_does_not_block_land() -> None:
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        foreign = repo.main / "foreign-session.txt"
        foreign.write_text("foreign untracked\n", encoding="utf-8")
        watched = _snapshot(foreign)
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert _snapshot(foreign) == watched


def test_safe_child_name_rule_rejects_only_dangerous_names() -> None:
    for name in (b".", b"..", b"a/b", b"nul\x00child"):
        assert LAND._SAFE_CHILD_RE.fullmatch(name) is None, name
    for name in (b".izanagi-test-dispatch", b"ordinary-name"):
        assert LAND._SAFE_CHILD_RE.fullmatch(name) is not None, name


def test_tracked_and_staged_main_dirt_are_rejected() -> None:
    """N26/M3: 既存 dirty 防壁は worktree/index のどちらも拒否する。"""
    for staged in (False, True):
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            (repo.main / "base.txt").write_text("dirty\n", encoding="utf-8")
            if staged:
                _git(repo.main, "add", "base.txt")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_DIRT, (staged, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_foreign_handoff_of_any_shape_does_not_block_land() -> None:
    """[意図した挙動変更] どの形の foreign handoff も land 全体を止めない。

    旧 test (malformed / symlink / fifo) は per-file の大域拒否を固定していた。
    T-220 択 (a) 後は 15 形すべてが同時に存在しても ``landed`` であり、かつ
    land は foreign artifact の中身にも inode にも一切触れない。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        entries = _make_all_foreign_handoffs(repo)
        watched = {path: _artifact_snapshot(path) for path in entries.values()}
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "author.txt").read_text(encoding="utf-8") == "author\n"
        assert {
            path: _artifact_snapshot(path) for path in entries.values()
        } == watched


def test_foreign_handoff_of_any_shape_is_protected_from_target_collision() -> None:
    """N1/N2: 15 形すべてが incoming target との衝突では拒否され続ける。

    「大域拒否をやめたついでに protected からも落ちた」を赤にする。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        entries = _make_all_foreign_handoffs(repo)
        watched = {path: _artifact_snapshot(path) for path in entries.values()}
        for kind, path in entries.items():
            relative = path.relative_to(repo.main).as_posix()
            target = f"{relative}/incoming.md" if kind == "directory" else relative
            _git(wave, "reset", "-q", "--hard", repo.base)
            destination = wave / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("tracked replacement\n", encoding="utf-8")
            _git(wave, "add", "--", target)
            _git(wave, "commit", "-qm", f"add {kind} collision")
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_CONTROL_PLANE, (kind, result)
            assert (result.release_safe, result.retryable_same_request) == (True, False)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert {
            path: _artifact_snapshot(path) for path in entries.values()
        } == watched


def test_nested_untracked_under_foreign_handoff_directory() -> None:
    """N2: handoff 配下の nested untracked は大域拒否せず、衝突時だけ拒否する。

    衝突側の rc を判別するのは、776 の前方一致を素の ``in`` に戻すと
    同じ入力が 791 の RC_DIRT へ落ちて「拒否されたから緑」になるため。
    """
    for colliding in (False, True):
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            nested = repo.main / "docs" / "handoff" / "archive" / "a.md"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text("nested foreign note\n", encoding="utf-8")
            watched = _artifact_snapshot(nested)
            relative = "docs/handoff/archive/a.md" if colliding else "author.txt"
            destination = wave / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("incoming\n", encoding="utf-8")
            _git(wave, "add", "--", relative)
            _git(wave, "commit", "-qm", f"add {relative}")
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            if colliding:
                assert result.rc == LAND.RC_CONTROL_PLANE, result
                assert _git(repo.main, "rev-parse", "HEAD") == repo.base
            else:
                assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
                assert _git(repo.main, "rev-parse", "HEAD") == tip
            assert _artifact_snapshot(nested) == watched, colliding


def test_handoff_readme_remains_a_landable_target() -> None:
    """tracked な docs/handoff/README.md は foreign handoff があっても land できる。

    README skip を落とすと 9 commit の変更実績がある target が恒久的に
    着地不能になる。この回帰を赤にする test は従来 0 本だった。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        foreign = _handoff(repo)
        watched = _artifact_snapshot(foreign)
        payload = "# handoff\n\nupdated by the wave\n"
        readme = wave / "docs" / "handoff" / "README.md"
        readme.write_text(payload, encoding="utf-8")
        _git(wave, "add", "--", "docs/handoff/README.md")
        _git(wave, "commit", "-qm", "update handoff README")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "docs" / "handoff" / "README.md").read_text(
            encoding="utf-8"
        ) == payload
        assert _artifact_snapshot(foreign) == watched


def test_untracked_handoff_readme_colliding_with_target_is_rejected() -> None:
    """docs/handoff/ 面でも「incoming と衝突する未知 untracked」は拒否し続ける。

    README.md は名前集合から除かれる唯一の直下エントリなので、776 を無条件
    ``continue`` へ緩めた退行を判別できる唯一の入力でもある (rc=20 vs rc=24)。
    """
    with _repo() as repo:
        wave = repo.waves["one"]
        _handoff(repo)
        _git(wave, "rm", "-q", "docs/handoff/README.md")
        _git(wave, "commit", "-qm", "drop tracked handoff README")
        first_tip = _git(wave, "rev-parse", "HEAD")
        first = _land(repo.request(wave, tip=first_tip))
        assert (first.rc, first.status) == (LAND.RC_OK, "landed"), first
        assert not (repo.main / "docs" / "handoff" / "README.md").exists()

        untracked = repo.main / "docs" / "handoff" / "README.md"
        untracked.write_text("# foreign untracked readme\n", encoding="utf-8")
        watched = _artifact_snapshot(untracked)
        readme = wave / "docs" / "handoff" / "README.md"
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text("# reinstated by the wave\n", encoding="utf-8")
        _git(wave, "add", "--", "docs/handoff/README.md")
        _git(wave, "commit", "-qm", "reinstate handoff README")
        second_tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(
            wave,
            base=first_tip,
            tip=second_tip,
            audited=repo.audited(first_tip, second_tip, wave),
        ))
        assert result.rc == LAND.RC_DIRT, result
        assert _git(repo.main, "rev-parse", "HEAD") == first_tip
        assert _artifact_snapshot(untracked) == watched


def test_untracked_nested_repository_record_collides_with_target() -> None:
    """N10 (M4): nested repo は ``?? path/`` の 1 レコードで返る。

    ``-uall`` でも collapsed なので、末尾スラッシュを正規化しないと配下 target が
    衝突検査を素通りする。git がこの形で返すこと自体を positive control で固定する。
    """
    with _repo() as repo:
        wave = repo.waves["one"]
        nested = repo.main / "vendor" / "nested"
        nested.mkdir(parents=True)
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(nested)],
            check=True,
            env=_git_env(),
        )
        payload = nested / "payload.txt"
        payload.write_text("foreign nested repo\n", encoding="utf-8")
        raw = subprocess.run(
            [
                REAL_GIT, "-C", str(repo.main), "status", "--porcelain=v1", "-z",
                "--untracked-files=all", "--ignore-submodules=none",
            ],
            check=True,
            env=_git_env(),
            stdout=subprocess.PIPE,
        ).stdout
        assert b"?? vendor/nested/\x00" in raw, raw

        target = wave / "vendor" / "nested" / "payload.txt"
        target.parent.mkdir(parents=True)
        target.write_text("incoming\n", encoding="utf-8")
        _git(wave, "add", "--", "vendor/nested/payload.txt")
        _git(wave, "commit", "-qm", "add target under a nested repository")
        tip = _git(wave, "rev-parse", "HEAD")
        watched = _artifact_snapshot(payload)
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _artifact_snapshot(payload) == watched


def test_unregistered_alias_child_is_rejected() -> None:
    """M6: 正規 child の .git bytes を複製しても admin backpointer 不一致で拒否する。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        alias = repo.main / ".codex" / "worktrees" / "alias"
        alias.mkdir()
        (alias / ".git").write_bytes((wave / ".git").read_bytes())
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_ignored_registered_container_and_unrelated_cache_are_accepted() -> None:
    """collapsed ignored dir 内でも既存物の sibling target は受理する。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        exclude = repo.main / ".git" / "info" / "exclude"
        exclude.write_text(
            ".codex/worktrees/\n.claude/worktrees/\ncache/\n",
            encoding="utf-8",
        )
        cache = repo.main / "cache" / "pre-existing.bin"
        cache.parent.mkdir()
        cache.write_bytes(b"ignored cache\n")
        (wave / "cache").mkdir()
        (wave / "cache" / "new.txt").write_text(
            "tracked sibling\n", encoding="utf-8"
        )
        _git(wave, "add", "-f", "cache/new.txt")
        _git(wave, "commit", "-qm", "add tracked cache sibling")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        assert cache.read_bytes() == b"ignored cache\n"
        assert (repo.main / "cache" / "new.txt").read_text() == "tracked sibling\n"


def test_ignored_unregistered_container_child_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        alias = repo.main / ".codex" / "worktrees" / "alias"
        alias.mkdir()
        (alias / ".git").write_bytes((wave / ".git").read_bytes())
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_target_collision_with_existing_ignored_path_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            "cache/\n",
            encoding="utf-8",
        )
        collision = repo.main / "cache" / "collision.txt"
        collision.parent.mkdir()
        collision.write_text("foreign cache\n", encoding="utf-8")
        target = wave / "cache" / "collision.txt"
        target.parent.mkdir()
        target.write_text("wave target\n", encoding="utf-8")
        _git(wave, "add", "-f", "cache/collision.txt")
        _git(wave, "commit", "-qm", "add ignored collision")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT, result
        assert collision.read_text(encoding="utf-8") == "foreign cache\n"
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_target_collision_with_existing_ignored_ancestor_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            "cache\n",
            encoding="utf-8",
        )
        collision = repo.main / "cache"
        collision.write_text("foreign cache file\n", encoding="utf-8")
        target = wave / "cache" / "new.txt"
        target.parent.mkdir()
        target.write_text("wave target\n", encoding="utf-8")
        _git(wave, "add", "-f", "cache/new.txt")
        _git(wave, "commit", "-qm", "add target below ignored ancestor")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_DIRT, result
        assert collision.read_text(encoding="utf-8") == "foreign cache file\n"
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_target_collision_with_foreign_control_artifact_is_rejected() -> None:
    for kind in ("handoff", "worktree"):
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            if kind == "handoff":
                foreign = _handoff(repo)
                relative = "docs/handoff/foreign.md"
                target = wave / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("tracked replacement\n", encoding="utf-8")
            else:
                foreign = repo.waves["foreign"] / ".git"
                relative = ".claude/worktrees/foreign/payload.txt"
                target = wave / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("tracked collision\n", encoding="utf-8")
            watched = _snapshot(foreign)
            _git(wave, "add", relative)
            _git(wave, "commit", "-qm", f"add {kind} collision")
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_CONTROL_PLANE, (kind, result)
            assert _snapshot(foreign) == watched
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_unsafe_container_child_bytes_are_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        container = os.fsencode(repo.main / ".codex" / "worktrees")
        os.mkdir(container + b"/bad\nrecord")
        result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_shallow_graft_replace_filter_and_promisor_are_rejected() -> None:
    """M7 と filter 外部実行面を main mutation 前に拒否する。"""
    cases = (
        "shallow", "graft", "replace", "filter", "promisor",
        "included_filter", "worktree_filter",
    )
    for case in cases:
        with _repo() as repo:
            wave = repo.waves["one"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            common = repo.main / ".git"
            if case == "shallow":
                (common / "shallow").write_text(repo.base + "\n", encoding="ascii")
            elif case == "graft":
                (common / "info" / "grafts").write_text(
                    f"{tip} {repo.base}\n", encoding="ascii"
                )
            elif case == "replace":
                _git(repo.main, "replace", tip, repo.base)
            elif case == "filter":
                _git(repo.main, "config", "filter.evil.smudge", "touch escaped")
            elif case == "promisor":
                _git(repo.main, "config", "remote.origin.promisor", "true")
            elif case == "included_filter":
                (common / "land-include").write_text(
                    "[filter \"evil\"]\n\tsmudge = touch escaped\n",
                    encoding="utf-8",
                )
                _git(repo.main, "config", "--local", "include.path", "land-include")
            else:
                _git(repo.main, "config", "extensions.worktreeConfig", "true")
                _git(
                    repo.main, "config", "--worktree",
                    "filter.evil.process", "touch escaped",
                )
            result = _land(repo.request(wave, tip=tip))
            assert result.rc == LAND.RC_AUDIT, (case, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base
            assert not (repo.main / "escaped").exists()


def test_hooks_and_fsmonitor_are_disabled_for_land() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        hook_marker = repo.root / "hook-ran"
        fsmonitor_marker = repo.root / "fsmonitor-ran"
        hook = repo.main / ".git" / "hooks" / "post-merge"
        hook.write_text(
            f"#!/bin/sh\nprintf ran > {hook_marker}\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        fsmonitor = repo.root / "fsmonitor"
        fsmonitor.write_text(
            f"#!/bin/sh\nprintf ran > {fsmonitor_marker}\nexit 1\n",
            encoding="utf-8",
        )
        fsmonitor.chmod(0o755)
        _git(repo.main, "config", "core.fsmonitor", str(fsmonitor))
        _git(repo.main, "config", "merge.autoStash", "true")
        _git(repo.main, "config", "maintenance.auto", "true")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        assert not hook_marker.exists()
        assert not fsmonitor_marker.exists()


def test_gitlink_change_lands_but_cannot_report_success_before_d16_sync() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        old_submodule_tip = _git(submodule, "rev-parse", "HEAD")
        (submodule / "sub.txt").write_text("sub updated\n", encoding="utf-8")
        _git(submodule, "commit", "-qam", "submodule target")
        expected_submodule_tip = _git(submodule, "rev-parse", "HEAD")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "change gitlink")
        tip = _git(wave, "rev-parse", "HEAD")
        result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert "D16" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        request = repo.request(wave, tip=tip)

        uninitialized = _land(request)
        assert (
            uninitialized.rc,
            uninitialized.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), uninitialized

        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )
        main_submodule = repo.main / "vendor" / "submodule"
        assert _git(main_submodule, "rev-parse", "HEAD") == expected_submodule_tip
        _git(main_submodule, "checkout", "-q", old_submodule_tip)
        mismatched = _land(request)
        assert mismatched.rc != LAND.RC_OK, mismatched

        _git(main_submodule, "checkout", "-q", expected_submodule_tip)
        synchronized = _land(request)
        assert (
            synchronized.rc,
            synchronized.status,
        ) == (LAND.RC_OK, "already-landed"), synchronized


def test_deleted_gitlink_recovery_requires_worktree_and_nested_metadata_absent() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "add gitlink")
        tested_main = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tested_main)
        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )
        _git(wave, "rm", "-qf", "vendor/submodule")
        _git(wave, "commit", "-qm", "remove gitlink")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        audited = repo.audited(tested_main, tested_tip, wave)
        request = repo.request(
            wave,
            base=tested_main,
            tip=tested_tip,
            audited=audited,
        )

        landed = _land(request)
        assert (landed.rc, landed.status) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), landed
        assert _git(repo.main, "rev-parse", "HEAD") == tested_tip

        residual_worktree = repo.main / "vendor" / "submodule"
        residual_metadata = repo.main / ".git" / "modules" / "vendor" / "submodule"
        assert residual_worktree.exists()
        assert residual_metadata.exists()
        residual = _land(request)
        assert residual.rc != LAND.RC_OK, residual

        shutil.rmtree(residual_worktree)
        metadata_only = _land(request)
        assert metadata_only.rc != LAND.RC_OK, metadata_only

        shutil.rmtree(residual_metadata)
        synchronized = _land(request)
        assert (synchronized.rc, synchronized.status) == (
            LAND.RC_OK,
            "already-landed",
        ), synchronized
        assert request.tested_main_sha == tested_main
        assert request.tested_wave_tip_sha == tested_tip
        assert request.audited_commits == audited


def test_gitlink_to_normal_tree_recovery_preserves_target_entry() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "add gitlink")
        tested_main = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tested_main)
        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )

        _git(wave, "rm", "-qf", "vendor/submodule")
        replacement = wave / "vendor" / "submodule" / "replacement.txt"
        replacement.parent.mkdir(parents=True)
        replacement.write_text("normal tree\n", encoding="utf-8")
        _git(wave, "add", "vendor/submodule/replacement.txt")
        _git(wave, "commit", "-qm", "replace gitlink with normal tree")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        audited = repo.audited(tested_main, tested_tip, wave)
        request = repo.request(
            wave,
            base=tested_main,
            tip=tested_tip,
            audited=audited,
        )

        landed = _land(request)
        assert (landed.rc, landed.status) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), landed
        assert _git(repo.main, "rev-parse", "HEAD") == tested_tip

        main_replacement = repo.main / "vendor" / "submodule"
        residual_metadata = repo.main / ".git" / "modules" / "vendor" / "submodule"
        assert (main_replacement / "replacement.txt").read_text(
            encoding="utf-8"
        ) == "normal tree\n"
        assert (main_replacement / ".git").exists()
        assert residual_metadata.exists()
        residual_identity = _land(request)
        assert residual_identity.rc != LAND.RC_OK, residual_identity

        for child in main_replacement.iterdir():
            if child.name == "replacement.txt":
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()

        metadata_only = _land(request)
        assert metadata_only.rc != LAND.RC_OK, metadata_only

        shutil.rmtree(residual_metadata)
        synchronized = _land(request)
        assert (synchronized.rc, synchronized.status) == (
            LAND.RC_OK,
            "already-landed",
        ), synchronized
        assert (main_replacement / "replacement.txt").read_text(
            encoding="utf-8"
        ) == "normal tree\n"
        assert request.tested_main_sha == tested_main
        assert request.tested_wave_tip_sha == tested_tip
        assert request.audited_commits == audited


def test_gitlink_to_normal_blob_recovery_preserves_target_entry() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        submodule = repo.root / "submodule-source"
        subprocess.run(
            [REAL_GIT, "init", "-q", "-b", "main", str(submodule)],
            check=True,
        )
        _git(submodule, "config", "user.name", "Dev Wave Test")
        _git(submodule, "config", "user.email", "dev-wave@example.invalid")
        (submodule / "sub.txt").write_text("sub\n", encoding="utf-8")
        _git(submodule, "add", "sub.txt")
        _git(submodule, "commit", "-qm", "submodule base")
        _git(
            wave, "-c", "protocol.file.allow=always",
            "submodule", "add", "-q", str(submodule), "vendor/submodule",
        )
        _git(wave, "commit", "-qm", "add gitlink")
        tested_main = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tested_main)
        _git(
            repo.main, "-c", "protocol.file.allow=always",
            "submodule", "update", "--init", "--recursive",
        )

        _git(wave, "rm", "-qf", "vendor/submodule")
        replacement = wave / "vendor" / "submodule"
        replacement.write_text("normal blob\n", encoding="utf-8")
        _git(wave, "add", "vendor/submodule")
        _git(wave, "commit", "-qm", "replace gitlink with normal blob")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        audited = repo.audited(tested_main, tested_tip, wave)
        request = repo.request(
            wave,
            base=tested_main,
            tip=tested_tip,
            audited=audited,
        )

        landed = _land(request)
        assert (landed.rc, landed.status) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), landed
        assert _git(repo.main, "rev-parse", "HEAD") == tested_tip
        main_replacement = repo.main / "vendor" / "submodule"
        assert main_replacement.read_text(encoding="utf-8") == "normal blob\n"

        residual_metadata = repo.main / ".git" / "modules" / "vendor" / "submodule"
        assert residual_metadata.exists()
        metadata_only = _land(request)
        assert metadata_only.rc != LAND.RC_OK, metadata_only

        shutil.rmtree(residual_metadata)
        synchronized = _land(request)
        assert (synchronized.rc, synchronized.status) == (
            LAND.RC_OK,
            "already-landed",
        ), synchronized
        assert main_replacement.read_text(encoding="utf-8") == "normal blob\n"
        assert request.tested_main_sha == tested_main
        assert request.tested_wave_tip_sha == tested_tip
        assert request.audited_commits == audited


def test_audited_sequence_and_moved_wave_tip_are_exact() -> None:
    """M8 および audited A..T 列の省略を拒否する。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        first = repo.commit(wave, "one.txt", "one\n")
        tip = repo.commit(wave, "two.txt", "two\n")
        audited = repo.audited(repo.base, tip, wave)
        assert audited == (first, tip)
        omitted = _land(repo.request(wave, tip=tip, audited=(tip,)))
        assert omitted.rc == LAND.RC_AUDIT, omitted
        moved = repo.commit(wave, "three.txt", "three\n")
        result = _land(repo.request(wave, tip=tip, audited=audited))
        assert moved != tip
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_audited_sequence_reverse_order_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        repo.commit(wave, "one.txt", "one\n")
        tip = repo.commit(wave, "two.txt", "two\n")
        audited = repo.audited(repo.base, tip, wave)
        result = _land(repo.request(wave, tip=tip, audited=tuple(reversed(audited))))
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_audited_sequence_extra_commit_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "one.txt", "one\n")
        audited = repo.audited(repo.base, tip, wave)
        result = _land(
            repo.request(wave, tip=tip, audited=audited + (repo.base,))
        )
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_audited_sequence_same_length_wrong_commit_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        repo.commit(wave, "one.txt", "one\n")
        tip = repo.commit(wave, "two.txt", "two\n")
        audited = repo.audited(repo.base, tip, wave)
        wrong = (repo.base, audited[1])
        assert len(wrong) == len(audited) and wrong != audited
        result = _land(repo.request(wave, tip=tip, audited=wrong))
        assert result.rc == LAND.RC_AUDIT, result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_common_lock_timeout_does_not_start_provenance_checker() -> None:
    """M5/M9: timeout は checker より先に rc 11 で止まる。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        marker = repo.root / "provenance-checker-started"
        checker = (
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('started')\n"
        )
        repo.commit(wave, "tools/check_ai_provenance.py", checker)
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        with _held_land_lock(repo), runtime.patch():
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_LOCK_BUSY, "lock-busy"), result
        assert result.reason == (
            "another cooperative land operation holds the common lock "
            # A: 初回は従来どおり待機し尽くした拒否として区別する。
            "(wait budget exhausted after waiting; phase=initial, waited_s=180.000, "
            "window_elapsed_s=180.000, limit_s=180.000)"
        )
        assert sum(runtime.sleeps) == pytest.approx(LAND._LAND_LOCK_WAIT_SECONDS)
        assert not marker.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_common_lock_waits_then_lands_after_holder_releases() -> None:
    """M1: holder 解放後は同じ invocation が待機から land へ進む。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        with _held_land_lock(repo) as holder:
            runtime.on_sleep = lambda _runtime: fcntl.flock(holder, fcntl.LOCK_UN)
            with runtime.patch():
                result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert runtime.sleeps
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_land_lock_polling_stops_at_shared_deadline() -> None:
    """M2: 歴史的 nodeid を維持し、監査時間を待機予算から除く。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        deadlines: list[float] = []
        holder = -1
        real_audit = LAND._audit_provenance_history
        real_acquire = LAND._acquire_land_lock

        def audit_then_hold(repository):
            nonlocal holder
            receipt = real_audit(repository)
            holder = os.open(
                repo.main / ".git" / "dev-wave-land.lock",
                os.O_RDWR | os.O_NOFOLLOW,
            )
            fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
            runtime.now_s = 170.0
            return receipt

        def record_deadline(repository, lock, deadline):
            deadlines.append(deadline)
            return real_acquire(repository, lock, deadline)

        try:
            with (
                runtime.patch(),
                _patched_land_attr("_audit_provenance_history", audit_then_hold),
                _patched_land_attr("_acquire_land_lock", record_deadline),
            ):
                result = _land(repo.request(wave, tip=tip))
        finally:
            if holder >= 0:
                os.close(holder)

        assert (result.rc, result.status) == (LAND.RC_LOCK_BUSY, "lock-busy"), result
        assert result.reason == (
            "another cooperative land operation holds the common lock "
            # A: 監査 170 秒を差し引かず、残る 180 秒を競合待機に使う。
            "(wait budget exhausted after waiting; phase=post-provenance, waited_s=180.000, "
            # A: 監査 170 秒と競合待機 180 秒で壁時計は 350 秒。
            "window_elapsed_s=350.000, limit_s=180.000)"
        )
        # A: 監査完了時刻 170 秒から未消費の 180 秒を使う。
        assert deadlines == [180.0, 350.0]
        assert runtime.sleeps
        assert all(0.0 < delay <= LAND._LAND_LOCK_MAX_POLL_SECONDS for delay in runtime.sleeps)
        # A: 監査時間による減額がなくなり、180 秒待機する。
        assert sum(runtime.sleeps) == pytest.approx(180.0)
        # A: 監査 170 秒に待機 180 秒が加わる。
        assert runtime.now_s == pytest.approx(350.0)
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base



def _wait_budget_fold_tip(repo: _Repo, wave: Path) -> str:
    """実 spool planner / registry / gate / receipt を通す小さい canonical family。"""
    (repo.main / ".git/info/exclude").write_text(".codex/worktrees/\n")
    files = {
        "docs/worklog.md": (
            "# worklog\n\n## ローテーション\n\n---\n\n"
            "## 2026-08-02 (2) — current\n\n- current\n\n"
            "### 次の一手\n\n- [T-001] (1)\n"
        ),
        "docs/archive/worklog-phase3-0801-1.md": (
            "# archive\n\n## 2026-08-01 (1) — seed\n\n- seed\n\n"
            "### 次の一手\n\n- [T-001] seed task\n"
        ),
        "docs/archive/README.md": "# archive\n",
        "docs/decisions.md": "# decisions\n\n## D1. seed (2026-08-01)\n\n**決定:** seed\n",
        "docs/failures.md": "# failures\n\n## エントリ\n\n### F1. seed [手順漏れ]\n- 事象: seed\n",
        # 実 planner は見送り領域の始端と終端の見出しを各一つ要求する。
        "docs/phase3.md": "# phase3\n\n## 見送り台帳\n\n### 裁定・完了記録\n",
        "tools/check_docs.py": "WORKLOG_ROTATE_BYTES = 100000\n",
        "docs/spool/decisions/2026-08-03-test-wave-1.md": (
            "---\nschema: izanagi-spool-v1\nledger: decisions\n"
            "authored: 2026-08-03\nwave: test-wave\nseq: 1\n---\n"
            "## {{D:wait-budget}}. wait budget\n\n**決定:** keep cumulative waits.\n"
        ),
    }
    sources = [
        ROOT / "tools/spool_fold.py",
        ROOT / "orchestrator/tests/test_spool_fold.py",
        ROOT / "orchestrator/tests/fold_gate_nodes.py",
        ROOT / "orchestrator/tests/growth_test_holds.py",
        *sorted((ROOT / "tools/dev_waves").glob("*.py")),
    ]
    for source in sources:
        files[source.relative_to(ROOT).as_posix()] = source.read_text(encoding="utf-8")
    for relative, content in files.items():
        path = wave / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(wave, "add", "-A")
    _git(wave, "commit", "-qm", "wait budget real fold fixture")
    return _git(wave, "rev-parse", "HEAD")


def _exercise_cumulative_waits(*, fold: bool, initial: float, audit: float,
                               audit_wait: float, fold_wait: float = 0.0):
    """時計だけを進め、実 flock・監査・fold gate・再検証・着地を実行する。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = (_wait_budget_fold_tip(repo, wave) if fold
               else repo.commit(wave, "wave.txt", "wave\n"))
        runtime = _FakeLandLockRuntime()
        acquisitions = []
        stages = []
        real_acquire = LAND._acquire_land_lock
        real_audit = LAND._audit_provenance_history
        real_gate = LAND._run_fold_gate
        with _held_land_lock(repo) as holder:
            release_at = initial

            def sleep(delay):
                # Cap the fake scheduler tick at the exact holder release event.
                runtime.sleeps.append(delay)
                runtime.now_s += min(delay, max(0.0, release_at - runtime.now_s))
                if runtime.now_s >= release_at:
                    fcntl.flock(holder, fcntl.LOCK_UN)

            def hold_after(seconds, wait):
                nonlocal release_at
                runtime.now_s += seconds
                if wait:
                    fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
                release_at = runtime.now_s + wait

            def observed_audit(repository):
                receipt = real_audit(repository)
                stages.append("provenance")
                hold_after(audit, audit_wait)
                return receipt

            def observed_gate(repository, plan, landing_tip):
                assert plan.status != "noop"
                receipt = real_gate(repository, plan, landing_tip)
                assert receipt.outcome == LAND._FOLD_GATE_OUTCOME
                stages.append("fold-gate")
                hold_after(LAND._fold_gate_budgets().inner_seconds, fold_wait)
                return receipt

            def observed_acquire(repository, lock, deadline):
                if fold and len(acquisitions) == 2:
                    # 3 回目の実取得は、実 fold gate の成功後でなければならない。
                    assert stages == ["provenance", "fold-gate"]
                started = runtime.now_s
                acquired, waited = real_acquire(repository, lock, deadline)
                acquisitions.append((deadline - started, acquired, waited))
                return acquired, waited

            if not initial:
                fcntl.flock(holder, fcntl.LOCK_UN)
            with (
                runtime.patch(),
                _patched_land_attr("_land_lock_sleep", sleep),
                _patched_land_attr("_audit_provenance_history", observed_audit),
                _patched_land_attr("_run_fold_gate", observed_gate),
                _patched_land_attr("_acquire_land_lock", observed_acquire),
            ):
                result = _land_real_gate(repo.request(wave, tip=tip))
            head = _git(repo.main, "rev-parse", "HEAD")
            if result.rc == LAND.RC_OK:
                assert head == (result.fold_commit_sha if fold else tip)
            else:
                assert head == repo.base
        # The land finally path must have closed its lock descriptor.
        with _held_land_lock(repo):
            pass
        return result, acquisitions, stages


def test_cumulative_wait_budget_provenance_does_not_refill() -> None:
    """20 + 170: 残160なら拒否、180へ補充する変異なら取得できてしまう。"""
    result, acquisitions, stages = _exercise_cumulative_waits(
        fold=False, initial=20.0, audit=430.0, audit_wait=170.0,
    )
    assert (result.rc, result.status) == (LAND.RC_LOCK_BUSY, "lock-busy"), result
    assert "phase=post-provenance" in result.reason
    assert acquisitions == [(180.0, True, 20.0), (160.0, False, 160.0)]
    assert stages == ["provenance"]


def test_cumulative_wait_budget_fold_does_not_refill() -> None:
    """fold後にも独立に20 + 170の補充変異境界を踏む。"""
    result, acquisitions, stages = _exercise_cumulative_waits(
        fold=True, initial=20.0, audit=430.0, audit_wait=0.0, fold_wait=170.0,
    )
    assert stages == ["provenance", "fold-gate"], result
    assert len(acquisitions) == 3, (result, acquisitions)
    assert (result.rc, result.status) == (LAND.RC_LOCK_BUSY, "lock-busy"), result
    assert "phase=post-fold-gate" in result.reason
    assert acquisitions == [(180.0, True, 20.0), (160.0, True, 0.0), (160.0, False, 160.0)]
    assert stages == ["provenance", "fold-gate"]


@pytest.mark.parametrize("fold", [False, True], ids=["noop", "fold"])
def test_cumulative_wait_budget_long_audit_still_allows_contention(fold: bool) -> None:
    """430秒監査後の実競合に待てる正例で旧絶対deadline復活を殺す。"""
    result, acquisitions, stages = _exercise_cumulative_waits(
        fold=fold, initial=20.0, audit=430.0, audit_wait=30.0, fold_wait=40.0,
    )
    if fold:
        assert stages == ["provenance", "fold-gate"], result
        assert len(acquisitions) == 3, (result, acquisitions)
    assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
    expected = [(180.0, True, 20.0), (160.0, True, 30.0)]
    if fold:
        expected.append((130.0, True, 40.0))
    assert acquisitions == expected
    assert stages == (["provenance", "fold-gate"] if fold else ["provenance"])
    assert result.as_json()["waited_s"] == (90.0 if fold else 50.0)
    assert result.as_json()["window_elapsed_s"] == (
        430.0 + result.waited_s + (LAND._fold_gate_budgets().inner_seconds if fold else 0.0)
    )


def test_cumulative_wait_budget_observed_short_audit_case() -> None:
    """初回150秒・監査122秒の形でも、残30秒内の再取得を許す。"""
    result, acquisitions, _ = _exercise_cumulative_waits(
        fold=False, initial=150.0, audit=122.0, audit_wait=20.0,
    )
    assert result.rc == LAND.RC_OK, result
    assert acquisitions == [(180.0, True, 150.0), (30.0, True, 20.0)]


def test_cumulative_wait_budget_exhausted_before_attempt_reason() -> None:
    result, acquisitions, _ = _exercise_cumulative_waits(
        fold=False, initial=LAND._LAND_LOCK_WAIT_SECONDS, audit=430.0, audit_wait=20.0,
    )
    assert result.rc == LAND.RC_LOCK_BUSY, result
    assert acquisitions[-1] == (0.0, False, 0.0)
    assert "another cooperative land operation holds the common lock" in result.reason
    assert "wait budget already exhausted; tried once without waiting" in result.reason


def test_cumulative_wait_budget_empty_budget_free_lock_still_succeeds() -> None:
    result, acquisitions, _ = _exercise_cumulative_waits(
        fold=False, initial=LAND._LAND_LOCK_WAIT_SECONDS, audit=430.0, audit_wait=0.0,
    )
    assert result.rc == LAND.RC_OK, result
    assert acquisitions[-1] == (0.0, True, 0.0)


def test_cumulative_wait_budget_arithmetic_uses_production_timeouts() -> None:
    import ast
    import inspect
    import math

    function = ast.parse(inspect.getsource(LAND._run_provenance_checker))
    timeouts = [kw.value for node in ast.walk(function) if isinstance(node, ast.Call)
                for kw in node.keywords if kw.arg == "timeout"]
    assert len(timeouts) == 1 and isinstance(timeouts[0], ast.Constant)
    provenance = timeouts[0].value
    budgets = LAND._fold_gate_budgets()
    # 裁定の検査harness予算。production全体watchdogがあるという主張ではない。
    termination_margin, test_watchdog = 30.0, 1280.0
    components = (LAND._LAND_LOCK_WAIT_SECONDS, provenance, budgets.outer_seconds,
                  termination_margin, test_watchdog)
    assert all(math.isfinite(value) and value > 0 for value in components)
    assert budgets.inner_seconds + budgets.termination_grace_seconds < budgets.outer_seconds
    assert sum(components[:-1]) < test_watchdog


def test_cumulative_wait_budget_result_before_window_omits_timing() -> None:
    result = LAND.land(LAND.LandRequest(
        Path("/missing"), Path("/missing"), "bad", "bad", (),
        "test-wave", Path("/missing/receipt.json"),
    ))
    assert result.rc != LAND.RC_OK
    assert "waited_s" not in result.as_json()
    assert "window_elapsed_s" not in result.as_json()

def test_provenance_gate_accepts_tip_zero_and_lands() -> None:
    """正例: tracked tip checker の full audit が緑なら通常 land できる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_provenance_gate_rejects_tip_nonzero_before_ff() -> None:
    """M1/M2/M3/M8: wave 側の非 0 を新規 admit 前に拒否する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(
            wave,
            "tools/check_ai_provenance.py",
            "raise SystemExit(73)\n",
        )
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_PROVENANCE, "rejected"), result
        assert "rc=73" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_provenance_audit_runs_with_global_lock_released() -> None:
    """二相化: 新規 admit の checker 実行中は common lock を解放する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        marker = repo.root / "audit-obtained-lock"
        lock_path = repo.main / ".git" / "dev-wave-land.lock"
        checker = (
            "import fcntl, os\n"
            f"fd = os.open({str(lock_path)!r}, os.O_RDWR | os.O_CREAT, 0o600)\n"
            "try:\n"
            "    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
            f"    open({str(marker)!r}, 'wb').close()\n"
            "finally:\n"
            "    os.close(fd)\n"
        )
        tip = repo.commit(wave, "tools/check_ai_provenance.py", checker)
        result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert marker.is_file()


def test_post_provenance_reacquire_waits_with_same_deadline() -> None:
    """監査後の contender 解放を待ち、receipt と fingerprint を実検査する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        runtime = _FakeLandLockRuntime()
        deadlines: list[float] = []
        holder = -1
        real_audit = LAND._audit_provenance_history
        real_acquire = LAND._acquire_land_lock

        def audit_then_hold(repository):
            nonlocal holder
            receipt = real_audit(repository)
            holder = os.open(
                repo.main / ".git" / "dev-wave-land.lock",
                os.O_RDWR | os.O_NOFOLLOW,
            )
            fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
            runtime.now_s = 170.0
            return receipt

        def release_after_five_seconds(_runtime) -> None:
            if runtime.now_s >= 175.0:
                runtime.on_sleep = None
                fcntl.flock(holder, fcntl.LOCK_UN)

        def record_deadline(repository, lock, deadline):
            deadlines.append(deadline)
            return real_acquire(repository, lock, deadline)

        runtime.on_sleep = release_after_five_seconds
        try:
            with (
                runtime.patch(),
                _patched_land_attr("_audit_provenance_history", audit_then_hold),
                _patched_land_attr("_acquire_land_lock", record_deadline),
            ):
                result = _land(request)
        finally:
            if holder >= 0:
                os.close(holder)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        # A: 監査完了時刻 170 秒から未消費の 180 秒を使う。
        assert deadlines == [180.0, 350.0]
        assert sum(runtime.sleeps) >= 5.0
        assert runtime.now_s < 180.0
        assert result.acceptance_receipt_sha256 == hashlib.sha256(
            request.acceptance_receipt.read_bytes()
        ).hexdigest()
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_expired_shared_deadline_still_attempts_post_provenance_once() -> None:
    """歴史的 nodeid を保持。長い監査後も空いた lock は待たず取得する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        real_audit = LAND._audit_provenance_history

        def audit_then_expire(repository):
            receipt = real_audit(repository)
            runtime.now_s = LAND._LAND_LOCK_WAIT_SECONDS + 1.0
            return receipt

        with (
            runtime.patch(),
            _patched_land_attr("_audit_provenance_history", audit_then_expire),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert runtime.sleeps == []
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_acquired_lock_rejects_path_inode_replacement() -> None:
    """M3: 待機中に lock path が別 inode へ替われば rc 22。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        lock_path = repo.main / ".git" / "dev-wave-land.lock"
        replacement = repo.main / ".git" / "dev-wave-land.lock.new"
        with _held_land_lock(repo) as holder:
            def replace_lock(_runtime) -> None:
                runtime.on_sleep = None
                replacement.write_bytes(b"")
                replacement.chmod(0o600)
                os.replace(replacement, lock_path)
                fcntl.flock(holder, fcntl.LOCK_UN)

            runtime.on_sleep = replace_lock
            with runtime.patch():
                result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_IDENTITY, "rejected"), result
        assert "binding changed after acquisition" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_acquired_lock_rejects_path_rebinding_with_old_inode_preserved() -> None:
    """M3: 旧 inode の link を保った path 差し替えも rc 22。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        lock_path = repo.main / ".git" / "dev-wave-land.lock"
        preserved = repo.main / ".git" / "dev-wave-land.lock.before-rebind"
        with _held_land_lock(repo) as holder:
            def rebind_lock_path(_runtime) -> None:
                runtime.on_sleep = None
                os.rename(lock_path, preserved)
                lock_path.write_bytes(b"")
                lock_path.chmod(0o600)
                assert LAND._lock_metadata_is_safe(os.fstat(holder))
                assert LAND._lock_metadata_is_safe(
                    os.stat(lock_path, follow_symlinks=False)
                )
                fcntl.flock(holder, fcntl.LOCK_UN)

            runtime.on_sleep = rebind_lock_path
            with runtime.patch():
                result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_IDENTITY, "rejected"), result
        assert "binding changed after acquisition" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


@pytest.mark.parametrize("lock_rebinding", ["move-old-inode", "symlink-old-inode"])
def test_acquired_lock_rejects_common_git_dir_replacement(
    lock_rebinding: str,
) -> None:
    """M4: common dir 差し替えと旧 lock への symlink を rc 22 で拒否する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        common = repo.main / ".git"
        old_common = repo.root / "common-before-replacement"
        with _held_land_lock(repo) as holder:
            def replace_common(_runtime) -> None:
                runtime.on_sleep = None
                common.rename(old_common)
                shutil.copytree(old_common, common, symlinks=True)
                (common / "dev-wave-land.lock").unlink()
                if lock_rebinding == "move-old-inode":
                    os.replace(
                        old_common / "dev-wave-land.lock",
                        common / "dev-wave-land.lock",
                    )
                else:
                    os.symlink(
                        old_common / "dev-wave-land.lock",
                        common / "dev-wave-land.lock",
                    )
                fcntl.flock(holder, fcntl.LOCK_UN)

            runtime.on_sleep = replace_common
            with runtime.patch():
                result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_IDENTITY, "rejected"), result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


test_acquired_lock_rejects_common_git_dir_replacement._plain_cases = (
    ("move-old-inode",),
    ("symlink-old-inode",),
)


def test_post_provenance_reacquire_rejects_control_directory_replacement() -> None:
    """M7: 再取得待機中の byte-identical control inode 交換は rc 21。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        holder = -1
        real_audit = LAND._audit_provenance_history
        handoff = repo.main / "docs" / "handoff"
        old_handoff = repo.root / "handoff-before-replacement"

        def audit_then_hold(repository):
            nonlocal holder
            receipt = real_audit(repository)
            holder = os.open(
                repo.main / ".git" / "dev-wave-land.lock",
                os.O_RDWR | os.O_NOFOLLOW,
            )
            fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
            runtime.now_s = 170.0
            return receipt

        def replace_control(_runtime) -> None:
            runtime.on_sleep = None
            handoff.rename(old_handoff)
            shutil.copytree(old_handoff, handoff)
            fcntl.flock(holder, fcntl.LOCK_UN)

        runtime.on_sleep = replace_control
        try:
            with (
                runtime.patch(),
                _patched_land_attr("_audit_provenance_history", audit_then_hold),
            ):
                result = _land(repo.request(wave, tip=tip))
        finally:
            if holder >= 0:
                os.close(holder)

        assert (result.rc, result.status) == (
            LAND.RC_CONTROL_PLANE,
            "rejected",
        ), result
        assert result.reason == (
            "control-plane identity/binding changed during the provenance audit"
        )
        assert (result.release_safe, result.retryable_same_request) == (True, False)
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


@pytest.mark.parametrize(
    ("exit_kind", "expected_exception"),
    [
        ("timeout", None),
        ("runtime-error", RuntimeError),
        ("keyboard-interrupt", KeyboardInterrupt),
    ],
)
def test_land_lock_wait_closes_fd_on_non_success_exit(
    exit_kind: str,
    expected_exception: type[BaseException] | None,
) -> None:
    """M8: timeout・例外・割込みの全てで caller 所有 fd を閉じる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        runtime = _FakeLandLockRuntime()
        opened: list[int] = []
        real_open = LAND._open_lock

        def record_open(repository, lock) -> None:
            real_open(repository, lock)
            opened.append(lock.fd)

        if exit_kind == "runtime-error":
            def fail_jitter(_delay_cap: float) -> float:
                raise RuntimeError("synthetic jitter failure")
            runtime.jitter = fail_jitter
        elif exit_kind == "keyboard-interrupt":
            def interrupt_sleep(_delay: float) -> None:
                raise KeyboardInterrupt("synthetic interrupt")
            runtime.sleep = interrupt_sleep

        with _held_land_lock(repo), runtime.patch(), _patched_land_attr(
            "_open_lock", record_open
        ):
            if expected_exception is None:
                result = _land(repo.request(wave, tip=tip))
                assert result.rc == LAND.RC_LOCK_BUSY, result
            else:
                with pytest.raises(expected_exception):
                    _land(repo.request(wave, tip=tip))

        assert opened
        with pytest.raises(OSError) as closed:
            os.fstat(opened[-1])
        assert closed.value.errno == errno.EBADF


test_land_lock_wait_closes_fd_on_non_success_exit._plain_cases = (
    ("timeout", None),
    ("runtime-error", RuntimeError),
    ("keyboard-interrupt", KeyboardInterrupt),
)


@pytest.mark.parametrize(
    ("exit_kind", "expected_exception"),
    [
        ("reject", None),
        ("os-error", OSError),
        ("keyboard-interrupt", KeyboardInterrupt),
    ],
)
def test_land_lock_closes_fd_on_post_acquire_verification_exit(
    exit_kind: str,
    expected_exception: type[BaseException] | None,
) -> None:
    """M8: real flock 成功後の検証失敗でも caller 所有 fd を閉じる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        opened: list[int] = []
        verified: list[int] = []
        real_open = LAND._open_lock

        def record_open(repository, lock) -> None:
            real_open(repository, lock)
            opened.append(lock.fd)

        def fail_verification(_repository, lock) -> None:
            verified.append(lock.fd)
            contender = os.open(
                repo.main / ".git" / "dev-wave-land.lock",
                os.O_RDWR | os.O_NOFOLLOW,
            )
            try:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(contender)
            if exit_kind == "reject":
                raise LAND._Reject(LAND.RC_IDENTITY, "synthetic binding rejection")
            if exit_kind == "os-error":
                raise OSError(errno.EIO, "synthetic binding I/O failure")
            raise KeyboardInterrupt("synthetic post-acquire interrupt")

        with (
            _patched_land_attr("_open_lock", record_open),
            _patched_land_attr("_verify_land_lock_binding", fail_verification),
        ):
            if expected_exception is None:
                result = _land(repo.request(wave, tip=tip))
                assert (result.rc, result.status) == (
                    LAND.RC_IDENTITY,
                    "rejected",
                ), result
                assert result.reason == "synthetic binding rejection"
            else:
                with pytest.raises(expected_exception):
                    _land(repo.request(wave, tip=tip))

        assert verified == opened
        assert opened
        with pytest.raises(OSError) as closed:
            os.fstat(opened[-1])
        assert closed.value.errno == errno.EBADF


test_land_lock_closes_fd_on_post_acquire_verification_exit._plain_cases = (
    ("reject", None),
    ("os-error", OSError),
    ("keyboard-interrupt", KeyboardInterrupt),
)


def test_pre_provenance_release_does_not_close_reused_fd() -> None:
    """監査前の意図的解放後、再利用された同番号 fd を cleanup で閉じない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        opened: list[int] = []
        reused_fd = -1
        real_open = LAND._open_lock

        def record_open(repository, lock) -> None:
            real_open(repository, lock)
            opened.append(lock.fd)

        def reuse_released_fd_then_interrupt(_repository):
            nonlocal reused_fd
            assert opened
            with pytest.raises(OSError) as released:
                os.fstat(opened[-1])
            assert released.value.errno == errno.EBADF
            target_fd = opened[-1]
            candidate_fd = os.open(request.acceptance_receipt, os.O_RDONLY)
            if candidate_fd == target_fd:
                reused_fd = candidate_fd
            else:
                try:
                    os.dup2(candidate_fd, target_fd)
                finally:
                    os.close(candidate_fd)
                reused_fd = target_fd
            assert reused_fd == opened[-1]
            raise KeyboardInterrupt("synthetic audit interrupt after fd reuse")

        try:
            with (
                _patched_land_attr("_open_lock", record_open),
                _patched_land_attr(
                    "_audit_provenance_history",
                    reuse_released_fd_then_interrupt,
                ),
            ):
                with pytest.raises(KeyboardInterrupt):
                    _land(request)

            assert reused_fd >= 0
            os.fstat(reused_fd)
        finally:
            if reused_fd >= 0:
                os.close(reused_fd)

        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_waited_initial_lock_rechecks_main_and_reports_stale() -> None:
    """M6: 待機後も main の監査閉包外移動を同じ理由で拒否する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        marker = repo.root / "provenance-checker-started"
        checker = (
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('started')\n"
        )
        tested_main = repo.commit(wave, "tools/check_ai_provenance.py", checker)
        tip = repo.commit(wave, "wave.txt", "wave\n")
        tested_main_parent = _git(wave, "rev-parse", f"{tested_main}^")
        assert _git(
            wave,
            "merge-base",
            "--is-ancestor",
            tested_main_parent,
            tip,
        ) == ""
        _git(repo.main, "reset", "--hard", tested_main)
        runtime = _FakeLandLockRuntime()
        with _held_land_lock(repo) as holder:
            def move_main(_runtime) -> None:
                runtime.on_sleep = None
                _git(repo.main, "reset", "--hard", tested_main_parent)
                fcntl.flock(holder, fcntl.LOCK_UN)

            runtime.on_sleep = move_main
            with runtime.patch():
                result = _land(repo.request(wave, base=tested_main, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_STALE_MAIN, "stale-main"), result
        assert result.reason == "main moved outside the tested audited closure while locking"
        assert not marker.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == tested_main_parent
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_already_landed_does_not_run_failing_provenance_checker() -> None:
    """M8: 同じ request の二回目は checker を起動せず already-landed。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        first = _land(request)
        assert (first.rc, first.status) == (LAND.RC_OK, "landed"), first

        original_run = LAND.subprocess.run
        checker_calls = 0

        def fail_checker(argv, **kwargs):
            nonlocal checker_calls
            if isinstance(argv, list) and argv and argv[0] == LAND._GIT_EXE:
                return original_run(argv, **kwargs)
            if argv == [
                sys.executable,
                str(wave / "tools" / "check_ai_provenance.py"),
            ]:
                checker_calls += 1
                raise RuntimeError("checker must not run for already-landed")
            return original_run(argv, **kwargs)

        try:
            LAND.subprocess.run = fail_checker
            second = _land(request)
        finally:
            LAND.subprocess.run = original_run

        assert (second.rc, second.status) == (LAND.RC_OK, "already-landed"), second
        assert checker_calls == 0


def test_provenance_audit_detects_removed_ignored_collision() -> None:
    """監査中に ignored collision が消えたら fingerprint 不一致で rc=29。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        collision = repo.main / "collision.txt"
        (repo.main / ".git" / "info" / "exclude").write_text(
            "collision.txt\n",
            encoding="utf-8",
        )
        collision.write_text("existing ignored artifact\n", encoding="utf-8")
        checker = (
            "from pathlib import Path\n"
            f"Path({str(collision)!r}).unlink(missing_ok=True)\n"
        )
        repo.commit(wave, "tools/check_ai_provenance.py", checker)
        (wave / "collision.txt").write_text("incoming\n", encoding="utf-8")
        _git(wave, "add", "-f", "collision.txt")
        _git(wave, "commit", "-qm", "add collision.txt")
        tip = _git(wave, "rev-parse", "HEAD")

        assert _git(
            repo.main,
            "status", "--short", "--ignored=matching", "--", "collision.txt",
        ) == "!! collision.txt"
        assert _git(wave, "ls-files", "--error-unmatch", "collision.txt") == (
            "collision.txt"
        )

        result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_PROVENANCE,
            "rejected",
        ), result
        assert "collision paths changed" in result.reason
        assert not collision.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_provenance_audit_accepts_absent_ignored_collision() -> None:
    """正例: ignored target が元から無く監査後も無ければ land できる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        collision = repo.main / "collision.txt"
        (repo.main / ".git" / "info" / "exclude").write_text(
            "collision.txt\n",
            encoding="utf-8",
        )
        checker = (
            "from pathlib import Path\n"
            f"Path({str(collision)!r}).unlink(missing_ok=True)\n"
        )
        repo.commit(wave, "tools/check_ai_provenance.py", checker)
        (wave / "collision.txt").write_text("incoming\n", encoding="utf-8")
        _git(wave, "add", "-f", "collision.txt")
        _git(wave, "commit", "-qm", "add collision.txt")
        tip = _git(wave, "rev-parse", "HEAD")

        assert not collision.exists()
        assert _git(repo.main, "check-ignore", "collision.txt") == "collision.txt"
        assert _git(wave, "ls-files", "--error-unmatch", "collision.txt") == (
            "collision.txt"
        )

        result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert collision.read_text(encoding="utf-8") == "incoming\n"
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_provenance_audit_accepts_unrelated_worktree_appearing() -> None:
    """無関係な wave の起動は audit fingerprint の対象外。"""

    with _repo(waves=(("codex", "author"),)) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        real_audit = LAND._audit_provenance_history

        def audit_then_add(repository):
            receipt = real_audit(repository)
            repo.add_wave("claude", "foreign")
            return receipt

        with _patched_land_attr("_audit_provenance_history", audit_then_add):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert repo.waves["foreign"].is_dir()
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_provenance_audit_accepts_unrelated_worktree_disappearing() -> None:
    """無関係な wave の撤収は audit fingerprint の対象外。"""

    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        foreign = repo.waves["foreign"]
        tip = repo.commit(wave, "author.txt", "author\n")
        real_audit = LAND._audit_provenance_history

        def audit_then_remove(repository):
            receipt = real_audit(repository)
            _git(repo.main, "worktree", "remove", "--force", str(foreign))
            return receipt

        with _patched_land_attr("_audit_provenance_history", audit_then_remove):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert not foreign.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_provenance_audit_rejects_own_worktree_replacement() -> None:
    """自分の wave worktree の binding は audit 中も厳格に束縛する。"""

    with _repo(waves=(("codex", "author"),)) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        old_wave = repo.root / "author-before-replacement"
        real_audit = LAND._audit_provenance_history

        def audit_then_replace(repository):
            receipt = real_audit(repository)
            wave.rename(old_wave)
            shutil.copytree(old_wave, wave)
            return receipt

        with _patched_land_attr("_audit_provenance_history", audit_then_replace):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_CONTROL_PLANE,
            "rejected",
        ), result
        assert "control-plane identity/binding changed" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_provenance_audit_rejects_overlapping_worktree_appearing() -> None:
    """target と重なる新規 worktree は無関係 wave として除外しない。"""

    with _repo(waves=(("codex", "author"),)) as repo:
        wave = repo.waves["author"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".claude/worktrees/\n",
            encoding="utf-8",
        )
        relative = ".claude/worktrees/overlap/payload.txt"
        target = wave / relative
        target.parent.mkdir(parents=True)
        target.write_text("incoming\n", encoding="utf-8")
        _git(wave, "add", "-f", "--", relative)
        _git(wave, "commit", "-qm", "add target under future worktree")
        tip = _git(wave, "rev-parse", "HEAD")
        real_audit = LAND._audit_provenance_history

        def audit_then_add_overlap(repository):
            receipt = real_audit(repository)
            repo.add_wave("claude", "overlap")
            return receipt

        with _patched_land_attr(
            "_audit_provenance_history", audit_then_add_overlap
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_CONTROL_PLANE,
            "rejected",
        ), result
        assert "control-plane identity/binding changed" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


@pytest.mark.parametrize("moved_head", ("main", "wave"))
def test_provenance_audit_still_rejects_moved_land_heads(moved_head: str) -> None:
    """worktree membership を外しても main/wave head の束縛は緩めない。"""

    with _repo(waves=(("codex", "author"),)) as repo:
        wave = repo.waves["author"]
        tested_tip = repo.commit(wave, "author.txt", "author\n")
        moved_tip = repo.commit(wave, "next.txt", "next\n")
        _git(wave, "reset", "--hard", tested_tip)
        wave_ref = _git(wave, "symbolic-ref", "HEAD")
        real_audit = LAND._audit_provenance_history

        def audit_then_move_head(repository):
            receipt = real_audit(repository)
            ref = "refs/heads/main" if moved_head == "main" else wave_ref
            _git(repo.main, "update-ref", ref, moved_tip)
            return receipt

        with _patched_land_attr("_audit_provenance_history", audit_then_move_head):
            result = _land(repo.request(wave, tip=tested_tip))

        assert (result.rc, result.status) == (
            LAND.RC_PROVENANCE,
            "rejected",
        ), result
        assert "heads or collision paths changed" in result.reason


def test_provenance_audit_still_rejects_handoff_appearing() -> None:
    """worktree membership を外しても docs/handoff の名前集合は束縛する。"""

    with _repo(waves=(("codex", "author"),)) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        appearing = repo.main / "docs" / "handoff" / "appearing.md"
        real_audit = LAND._audit_provenance_history

        def audit_then_add_handoff(repository):
            receipt = real_audit(repository)
            appearing.write_text(_handoff_text(repo), encoding="utf-8")
            return receipt

        with _patched_land_attr("_audit_provenance_history", audit_then_add_handoff):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_CONTROL_PLANE,
            "rejected",
        ), result
        assert "control-plane identity/binding changed" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_provenance_receipt_rejects_each_bound_field() -> None:
    """M2/M4/M5: receipt の tip/blob/bytes/rc 四条件を独立に固定する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        request = repo.request(wave)
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            try:
                receipt = LAND._audit_provenance_history(repository)
                cases = (
                    LAND._ProvenanceReceipt(
                        "0" * len(receipt.tip_sha),
                        receipt.checker_blob_sha,
                        receipt.executed_bytes_sha,
                        0,
                    ),
                    LAND._ProvenanceReceipt(
                        receipt.tip_sha,
                        "0" * len(receipt.checker_blob_sha),
                        receipt.executed_bytes_sha,
                        0,
                    ),
                    LAND._ProvenanceReceipt(
                        receipt.tip_sha,
                        receipt.checker_blob_sha,
                        "0" * len(receipt.executed_bytes_sha),
                        0,
                    ),
                    LAND._ProvenanceReceipt(
                        receipt.tip_sha,
                        receipt.checker_blob_sha,
                        receipt.executed_bytes_sha,
                        1,
                    ),
                )
                for invalid in cases:
                    try:
                        LAND._verify_provenance_receipt(
                            repository,
                            invalid,
                            receipt.tip_sha,
                        )
                        assert False, f"invalid receipt accepted: {invalid}"
                    except LAND._Reject as exc:
                        assert exc.rc == LAND.RC_PROVENANCE
            finally:
                repository.close()


def test_provenance_audit_rejects_executed_bytes_mismatch() -> None:
    """M5: 束縛 FD の実行予定 bytes が commit blob と違えば rc=29。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        request = repo.request(wave)
        (wave / "tools" / "check_ai_provenance.py").write_text(
            "raise SystemExit(0)\n# dirty replacement\n",
            encoding="utf-8",
        )
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            try:
                try:
                    LAND._audit_provenance_history(repository)
                    assert False, "mismatched executed bytes were accepted"
                except LAND._Reject as exc:
                    assert exc.rc == LAND.RC_PROVENANCE
                    assert "bound bytes do not match" in exc.reason
            finally:
                repository.close()


def test_provenance_binding_close_is_idempotent_and_closes_both_fds() -> None:
    """最初の close 失敗でも二つ目を閉じ、全 field を -1 にする。"""

    checker_fd = os.open(os.devnull, os.O_RDONLY)
    tools_fd = os.open(os.devnull, os.O_RDONLY)
    binding = LAND._ProvenanceCheckerBinding(Path(os.devnull), tools_fd, checker_fd)
    original_close = LAND.os.close
    closed = []

    def fail_first(fd):
        closed.append(fd)
        if fd == checker_fd:
            raise OSError("synthetic first close failure")
        return original_close(fd)

    try:
        LAND.os.close = fail_first
        try:
            binding.close()
            assert False, "synthetic close failure was hidden"
        except OSError as exc:
            assert "synthetic first close failure" in str(exc)
    finally:
        LAND.os.close = original_close
        original_close(checker_fd)

    assert closed == [checker_fd, tools_fd]
    assert (binding.checker_fd, binding.tools_fd) == (-1, -1)
    try:
        os.fstat(tools_fd)
        assert False, "tools fd was left open"
    except OSError:
        pass
    binding.close()


def test_provenance_receipt_rejects_tip_that_moves_during_audit() -> None:
    """M4 integration: audit 中に tested tip から動いた HEAD は拒否する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        checker = (
            "import subprocess\n"
            "from pathlib import Path\n"
            "repo = Path(__file__).resolve().parent.parent\n"
            "raise SystemExit(subprocess.run(["
            f"{REAL_GIT!r}, '-C', str(repo), 'reset', '--hard', "
            "'refs/heads/provenance-next'], check=False).returncode)\n"
        )
        repo.commit(wave, "tools/check_ai_provenance.py", checker)
        tested_tip = repo.commit(wave, "wave.txt", "wave\n")
        moved_tip = repo.commit(wave, "next.txt", "next\n")
        _git(wave, "branch", "provenance-next", moved_tip)
        _git(wave, "reset", "--hard", tested_tip)
        request = repo.request(wave, tip=tested_tip)
        result = _land(request)
        assert (result.rc, result.status) == (LAND.RC_PROVENANCE, "rejected"), result
        assert "heads or collision paths changed" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_post_provenance_head_change_preserves_provenance_rejection_order() -> None:
    """R1: head 変化は全 preflight の再実行より先に rc 29 で拒否する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        checker = (
            "import subprocess\n"
            "from pathlib import Path\n"
            "repo = Path(__file__).resolve().parent.parent\n"
            "raise SystemExit(subprocess.run(["
            f"{REAL_GIT!r}, '-C', str(repo), 'reset', '--hard', "
            "'refs/heads/provenance-next'], check=False).returncode)\n"
        )
        repo.commit(wave, "tools/check_ai_provenance.py", checker)
        tested_tip = repo.commit(wave, "wave.txt", "wave\n")
        moved_tip = repo.commit(wave, "next.txt", "next\n")
        _git(wave, "branch", "provenance-next", moved_tip)
        _git(wave, "reset", "--hard", tested_tip)
        request = repo.request(wave, tip=tested_tip)
        real_locked_preflight = LAND._locked_preflight
        preflight_calls = 0

        def record_locked_preflight(*args, **kwargs):
            nonlocal preflight_calls
            preflight_calls += 1
            return real_locked_preflight(*args, **kwargs)

        with _patched_land_attr("_locked_preflight", record_locked_preflight):
            result = _land(request)

        assert preflight_calls == 1
        assert (result.rc, result.status) == (LAND.RC_PROVENANCE, "rejected")
        assert result.reason == (
            "main/wave heads or collision paths changed during "
            "the provenance audit"
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_provenance_subprocess_contract_and_exception_mapping() -> None:
    """M6/M7: argv/kwargs を固定し、起動・timeout・想定外例外を rc=29 化する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        request = repo.request(wave)
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            original_run = LAND.subprocess.run
            checker_path = wave / "tools" / "check_ai_provenance.py"
            expected_keys = {
                "cwd", "env", "stdin", "stdout", "stderr", "check",
                "shell", "close_fds", "timeout",
            }
            observed_calls = []

            def fake_run(argv, **kwargs):
                if isinstance(argv, list) and argv and argv[0] == LAND._GIT_EXE:
                    return original_run(argv, **kwargs)
                observed_calls.append((argv, kwargs))
                return subprocess.CompletedProcess(argv, 0, b"", b"")

            try:
                LAND.subprocess.run = fake_run
                receipt = LAND._audit_provenance_history(repository)
                assert receipt.returncode == 0
                assert len(observed_calls) == 1
                argv, kwargs = observed_calls[0]
                assert argv == [sys.executable, str(checker_path)]
                assert set(kwargs) == expected_keys
                assert kwargs["cwd"] == wave
                assert kwargs["env"] == {
                    **LAND._git_env(),
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
                assert kwargs["stdin"] is subprocess.DEVNULL
                assert kwargs["stdout"] is subprocess.PIPE
                assert kwargs["stderr"] is subprocess.PIPE
                assert kwargs["check"] is False
                assert kwargs["shell"] is False
                assert kwargs["close_fds"] is True
                assert kwargs["timeout"] == 480

                for failure in (
                    OSError("synthetic exec failure"),
                    subprocess.TimeoutExpired([sys.executable], 480),
                    RuntimeError("synthetic unexpected failure"),
                    SystemExit("synthetic system exit"),
                    GeneratorExit("synthetic generator exit"),
                ):
                    def failing_run(argv, _failure=failure, **kwargs):
                        if (
                            isinstance(argv, list)
                            and argv
                            and argv[0] == LAND._GIT_EXE
                        ):
                            return original_run(argv, **kwargs)
                        raise _failure

                    LAND.subprocess.run = failing_run
                    try:
                        LAND._audit_provenance_history(repository)
                        assert False, f"exception escaped mapping: {failure!r}"
                    except LAND._Reject as exc:
                        assert exc.rc == LAND.RC_PROVENANCE
            finally:
                LAND.subprocess.run = original_run
                repository.close()


def test_provenance_checker_missing_and_symlink_components_are_rejected_clean() -> None:
    """checker 欠落・leaf/ancestor symlink は clean commit tip でも rc=29。"""

    for kind in ("missing", "leaf-symlink", "ancestor-symlink"):
        with _repo() as repo:
            wave = repo.waves["one"]
            external = repo.root / f"external-{kind}"
            if kind == "missing":
                _git(wave, "rm", "tools/check_ai_provenance.py")
            elif kind == "leaf-symlink":
                external.write_text("raise SystemExit(0)\n", encoding="utf-8")
                _git(wave, "rm", "tools/check_ai_provenance.py")
                os.symlink(external, wave / "tools" / "check_ai_provenance.py")
                _git(wave, "add", "tools/check_ai_provenance.py")
            else:
                external.mkdir()
                (external / "check_ai_provenance.py").write_text(
                    "raise SystemExit(0)\n",
                    encoding="utf-8",
                )
                (external / "check_docs.py").write_text(
                    "raise SystemExit(0)\n",
                    encoding="utf-8",
                )
                _git(wave, "rm", "-r", "tools")
                os.symlink(external, wave / "tools", target_is_directory=True)
                _git(wave, "add", "tools")
            _git(wave, "commit", "-qm", f"make checker {kind}")
            assert _git(wave, "status", "--porcelain=v1") == ""
            tip = _git(wave, "rev-parse", "HEAD")
            result = _land(
                repo.request(wave, tip=tip, make_acceptance_receipt=False)
            )
            assert (result.rc, result.status) == (
                LAND.RC_PROVENANCE,
                "rejected",
            ), (kind, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base


_WRAPPER = """#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time

real = os.environ["DEV_WAVE_REAL_GIT"]
args = sys.argv[1:]
mode = os.environ.get("DEV_WAVE_WRAPPER_MODE", "")

if mode == "fail-exact":
    expected_repo = os.environ["DEV_WAVE_FAIL_REPO"]
    expected_subcommand = json.loads(os.environ["DEV_WAVE_FAIL_SUBCOMMAND"])
    try:
        repo_index = args.index("-C")
    except ValueError:
        repo_index = -1
    actual_subcommand = args[repo_index + 2:] if repo_index >= 0 else []
    if (
        repo_index >= 0
        and args[repo_index + 1:repo_index + 2] == [expected_repo]
        and actual_subcommand == expected_subcommand
    ):
        with open(os.environ["DEV_WAVE_FAIL_RECORD"], "w", encoding="utf-8") as stream:
            json.dump(actual_subcommand, stream)
        sys.stderr.write("synthetic exact git failure\\n")
        raise SystemExit(91)

def replace_target():
    marker = os.environ["DEV_WAVE_MARKER"]
    if os.path.exists(marker):
        return
    target = os.environ["DEV_WAVE_REPLACE_TARGET"]
    backup = os.environ["DEV_WAVE_REPLACE_BACKUP"]
    kind = os.environ["DEV_WAVE_REPLACE_KIND"]
    if kind == "file":
        with open(target, "rb") as stream:
            payload = stream.read()
        os.replace(target, backup)
        with open(target, "wb") as stream:
            stream.write(payload)
    else:
        with open(os.path.join(target, ".git"), "rb") as stream:
            payload = stream.read()
        os.replace(target, backup)
        os.mkdir(target)
        with open(os.path.join(target, ".git"), "wb") as stream:
            stream.write(payload)
    open(marker, "wb").close()

def once(marker_env):
    marker = os.environ[marker_env]
    if os.path.exists(marker):
        return False
    open(marker, "wb").close()
    return True

def edit_handoff_in_place():
    # production の handoff 更新 (Path.write_text) と同型に inode を保存して
    # bytes だけ書き換える。既存 replace_target は inode しか動かせない。
    if not once("DEV_WAVE_EDIT_MARKER"):
        return
    payload = os.environ["DEV_WAVE_EDIT_PAYLOAD"].encode("utf-8")
    fd = os.open(os.environ["DEV_WAVE_EDIT_TARGET"], os.O_WRONLY | os.O_TRUNC)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)

def create_handoff():
    if not once("DEV_WAVE_CREATE_MARKER"):
        return
    with open(os.environ["DEV_WAVE_CREATE_PATH"], "w", encoding="utf-8") as stream:
        stream.write(os.environ["DEV_WAVE_CREATE_PAYLOAD"])

def remove_handoff():
    # 他セッションが正常終了して handoff を回収する形。運用最頻の消失方向。
    if not once("DEV_WAVE_REMOVE_MARKER"):
        return
    os.unlink(os.environ["DEV_WAVE_REMOVE_PATH"])

def dirty_tracked():
    # merge 後に main の tracked file を書き換える。post-land の縮約検査
    # (_verify_main_no_tracked_dirt) だけがこの入力を見る。
    with open(os.environ["DEV_WAVE_DIRTY_PATH"], "w", encoding="utf-8") as stream:
        stream.write(os.environ["DEV_WAVE_DIRTY_PAYLOAD"])

def swap_directory():
    # 子エントリを名前ごと保存したまま dir 自身を差し替える。名前集合が
    # 変わらないので、dir identity を落とした実装だけがこれを見逃す。
    if not once("DEV_WAVE_SWAP_MARKER"):
        return
    target = os.environ["DEV_WAVE_SWAP_TARGET"]
    backup = os.environ["DEV_WAVE_SWAP_BACKUP"]
    names = sorted(os.listdir(target))
    os.rename(target, backup)
    os.mkdir(target)
    for name in names:
        os.link(os.path.join(backup, name), os.path.join(target, name))

if mode == "record":
    with open(os.environ["DEV_WAVE_RECORD"], "a", encoding="utf-8") as stream:
        stream.write(json.dumps(args) + "\\n")
if (
    mode == "hide-head"
    and os.path.exists(os.environ["DEV_WAVE_MARKER"])
    and "rev-parse" in args
    and "HEAD" in args
):
    raise SystemExit(92)
if mode == "replace-control" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    replace_target()
    raise SystemExit(completed.returncode)
if mode == "replace-after-collision" and "check-ignore" in args:
    completed = subprocess.run([real, *args], check=False)
    replace_target()
    raise SystemExit(completed.returncode)
if mode == "edit-handoff" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    edit_handoff_in_place()
    raise SystemExit(completed.returncode)
if mode == "create-handoff" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    create_handoff()
    raise SystemExit(completed.returncode)
if mode == "remove-handoff" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    remove_handoff()
    raise SystemExit(completed.returncode)
if mode == "swap-handoff-dir" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    swap_directory()
    raise SystemExit(completed.returncode)
if mode == "handoff-after-merge" and "status" in args:
    completed = subprocess.run([real, *args], check=False)
    if os.path.exists(os.environ["DEV_WAVE_MERGED"]):
        create_handoff()
        edit_handoff_in_place()
    raise SystemExit(completed.returncode)
if "merge" not in args:
    os.execv(real, [real, *args])
if mode == "audit-fds":
    targets = {}
    for name in os.listdir("/proc/self/fd"):
        try:
            targets[name] = os.readlink("/proc/self/fd/" + name)
        except OSError:
            pass
    with open(os.environ["DEV_WAVE_FD_RECORD"], "w", encoding="utf-8") as stream:
        json.dump(targets, stream)
if mode == "not-landed":
    raise SystemExit(91)
if mode == "partial":
    with open(os.environ["DEV_WAVE_PARTIAL_PATH"], "w", encoding="utf-8") as stream:
        stream.write("partial mutation\\n")
    raise SystemExit(91)
if mode in {"hold", "hold-dirty"}:
    dirty_path = os.environ.get("DEV_WAVE_DIRTY_PATH")
    if dirty_path:
        with open(dirty_path, "rb") as stream:
            original = stream.read()
        with open(dirty_path, "wb") as stream:
            stream.write(b"transient merge dirt\\n")
    open(os.environ["DEV_WAVE_READY"], "wb").close()
    while not os.path.exists(os.environ["DEV_WAVE_RELEASE"]):
        time.sleep(0.01)
    if dirty_path:
        with open(dirty_path, "wb") as stream:
            stream.write(original)
    os.execv(real, [real, *args])
completed = subprocess.run([real, *args], check=False)
if mode == "hide-head" and completed.returncode == 0:
    open(os.environ["DEV_WAVE_MARKER"], "wb").close()
if mode == "handoff-after-merge" and completed.returncode == 0:
    open(os.environ["DEV_WAVE_MERGED"], "wb").close()
if mode == "dirty-after-merge" and completed.returncode == 0:
    dirty_tracked()
if mode == "move-wave" and completed.returncode == 0:
    subprocess.run(
        [real, "-C", os.environ["DEV_WAVE_MOVE_REPO"], "update-ref",
         os.environ["DEV_WAVE_MOVE_REF"], os.environ["DEV_WAVE_MOVE_TO"]],
        check=True,
    )
raise SystemExit(completed.returncode)
"""


def _wrapper(root: Path) -> Path:
    path = root / "git-wrapper"
    path.write_text(_WRAPPER, encoding="utf-8")
    path.chmod(0o755)
    return path


@contextlib.contextmanager
def _patched_git(executable: Path, env: dict[str, str]):
    previous_git = LAND._GIT_EXE
    previous_env = {key: os.environ.get(key) for key in env}
    LAND._GIT_EXE = str(executable)
    os.environ.update(env)
    try:
        yield
    finally:
        LAND._GIT_EXE = previous_git
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextlib.contextmanager
def _patched_land_attr(name: str, value):
    previous = getattr(LAND, name)
    setattr(LAND, name, value)
    try:
        yield
    finally:
        setattr(LAND, name, previous)


def _fake_pending_fragment(
    repo: _Repo,
    wave: Path,
    *,
    wave_slug: str = "test-wave",
) -> tuple[str, Path, str]:
    relative = f"docs/spool/worklog/2000-01-01-{wave_slug}-1.md"
    path = wave / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "synthetic pending fragment\n"
    path.write_text(content, encoding="utf-8")
    _git(wave, "add", "--", relative)
    _git(wave, "commit", "-qm", "add synthetic pending fragment")
    return relative, path, content


@dataclasses.dataclass(frozen=True)
class _FakeFoldOrigin:
    kind: str
    base: str
    tested_tip: str
    wave_ref: str
    rollback_ref: str
    trusted_main_cutoff: str
    audited_digest: str


class _FakeFoldPlan:
    status = "planned"

    def __init__(
        self,
        gc_path: str,
        *,
        targets: tuple[object, ...] = (),
        fragments: tuple[object, ...] = (),
        origin: _FakeFoldOrigin | None = None,
        phase: str = "applied",
        transaction_id: str | None = None,
        rotation_path: str | None = None,
    ):
        self.gc_paths = (gc_path,)
        self.targets = targets
        self.fragments = fragments
        self.origin = origin
        self.phase = phase
        self.transaction_id = transaction_id or hashlib.sha256(
            (gc_path + "\0" + phase).encode("utf-8")
        ).hexdigest()
        self.rotation_path = rotation_path

    def with_phase(self, phase: str) -> "_FakeFoldPlan":
        return _FakeFoldPlan(
            self.gc_paths[0],
            targets=self.targets,
            fragments=self.fragments,
            origin=self.origin,
            phase=phase,
            transaction_id=self.transaction_id,
            rotation_path=self.rotation_path,
        )


class _FakeFoldFragment:
    def __init__(
        self,
        wave: str,
        *,
        path: str = "docs/spool/worklog/2000-01-01-test-wave-1.md",
        content_sha256: str = "0" * 64,
        authored: str = "2000-01-01",
        seq: int = 1,
    ):
        self.wave = wave
        self.path = path
        self.content_sha256 = content_sha256
        self.authored = authored
        self.seq = seq


class _FakeFoldTarget:
    def __init__(
        self,
        path: str,
        *,
        before_exists: bool = True,
        after_bytes: bytes = b"",
        before_bytes: bytes = b"",
    ):
        self.path = path
        self.before_exists = before_exists
        self.after_bytes = after_bytes
        self.after_sha256 = hashlib.sha256(self.after_bytes).hexdigest()
        self.before_sha256 = hashlib.sha256(before_bytes).hexdigest()


class _FakeFoldModule:
    FoldOrigin = _FakeFoldOrigin
    _CLOSURE_FIXED_PATHS = tuple(
        LAND._load_spool_fold()._CLOSURE_FIXED_PATHS
    )

    def __init__(self, plan, apply, *, active=False, fail_finalize=False):
        self._plan = plan
        self._apply = apply
        self._active = active
        self._fail_finalize = fail_finalize
        self.events: list[str] = []

    @staticmethod
    def audited_commit_digest(commits) -> str:
        return hashlib.sha256(
            b"".join(commit.encode("ascii") + b"\n" for commit in commits)
        ).hexdigest()

    def _bind_default_active_origin(self, repo: Path) -> None:
        if self._plan.origin is not None:
            return
        wave = Path.cwd()
        tested_tip = _git(wave, "rev-parse", "HEAD")
        wave_ref = _git(wave, "symbolic-ref", "HEAD")
        self._plan.origin = self.FoldOrigin(
            kind="land",
            base=tested_tip,
            tested_tip=tested_tip,
            wave_ref=wave_ref,
            rollback_ref=tested_tip,
            trusted_main_cutoff=tested_tip,
            audited_digest=self.audited_commit_digest(()),
        )

    def load_active_plan(self, repo: Path):
        assert repo.is_dir()
        if self._active:
            self._bind_default_active_origin(repo)
        return self._plan if self._active else None

    def validate_spool_tree(
        self,
        repo: Path,
        *,
        expected_transaction_id: str | None = None,
    ):
        assert repo.is_dir()
        assert expected_transaction_id == self._plan.transaction_id
        assert all((repo / target.path).is_file() for target in self._plan.targets)
        assert all(not (repo / relative).exists() for relative in self._plan.gc_paths)
        return []

    def _validate_closure(self, repo: Path, plan):
        assert repo.is_dir()
        assert plan is self._plan
        return {}, {}

    def plan_fold(self, repo: Path, *, fold_date: str, origin: _FakeFoldOrigin):
        assert repo.is_dir()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", fold_date)
        observed_tip = _git(repo, "rev-parse", "HEAD")
        observed_ref = _git(repo, "symbolic-ref", "HEAD")
        observed_audited = tuple(
            line for line in _git(
                repo,
                "rev-list",
                "--reverse",
                f"{origin.trusted_main_cutoff}..{observed_tip}",
            ).splitlines()
            if line
        )
        assert origin.tested_tip == observed_tip
        assert origin.wave_ref == observed_ref
        assert _git(repo, "cat-file", "-t", origin.base) == "commit"
        assert _git(repo, "cat-file", "-t", origin.rollback_ref) == "commit"
        assert _git(repo, "cat-file", "-t", origin.trusted_main_cutoff) == "commit"
        assert origin.audited_digest == self.audited_commit_digest(observed_audited)
        self._plan.origin = origin
        self.events.append("plan")
        return self._plan

    def _state_path(self, repo: Path) -> Path:
        return repo / ".git" / LAND._FOLD_STATE_NAME

    def apply_fold(self, repo: Path, plan, *, gate_receipt=None) -> None:
        assert plan is self._plan
        if getattr(plan.origin, "kind", None) == "land":
            assert gate_receipt is not None
        self.events.append("apply")
        self._apply(repo, plan)

    def _assert_fold_identity(self, repo: Path, plan, fold_commit: str) -> None:
        assert _git(repo, "rev-parse", "HEAD") == fold_commit
        assert _git(repo, "rev-parse", f"{fold_commit}^") == plan.origin.tested_tip
        assert _git(repo, "show", "-s", "--format=%an <%ae>", fold_commit) == (
            LAND.FOLD_AUTHOR_IDENTITY
        )
        assert _git(repo, "show", "-s", "--format=%B", fold_commit) == (
            LAND._FOLD_MESSAGE.rstrip("\n")
        )

    def verify_fold_commit_identity(self, repo: Path, plan, *, fold_commit: str) -> None:
        self.events.append("verify")
        self._assert_fold_identity(repo, plan, fold_commit)

    def mark_fold_committed(self, repo: Path, plan, *, fold_commit: str):
        self.events.append("mark")
        assert plan.phase == "applied"
        self._assert_fold_identity(repo, plan, fold_commit)
        self._plan = plan.with_phase("committed")
        return self._plan

    def finalize_fold(self, repo: Path, plan, *, fold_commit: str) -> None:
        self.events.append("finalize")
        assert plan.phase == "committed"
        self._assert_fold_identity(repo, plan, fold_commit)
        if self._fail_finalize:
            raise RuntimeError("synthetic finalize failure")


_ROLLBACK_TRANSACTION_ID = "a" * 64


@contextlib.contextmanager
def _rollback_fold_fixture():
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        index_tree = _git(repo.main, "write-tree")
        restore_path = repo.main / "docs/spool/rollback-path.txt"
        restore_path.write_bytes(b"rollback-before\n")
        restore_path.chmod(0o640)
        snapshots = LAND._snapshot_fold_paths(
            repo.main,
            (restore_path.relative_to(repo.main).as_posix(),),
        )
        _git(repo.main, "merge", "--ff-only", tip)

        fold = LAND._load_spool_fold()
        plan = _FakeFoldPlan(
            "docs/spool/worklog/synthetic.md",
            transaction_id=_ROLLBACK_TRANSACTION_ID,
        )
        state_path = fold._state_path(repo.main)
        state_bytes = (
            json.dumps(
                {"transaction_id": plan.transaction_id},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
        state_path.write_bytes(state_bytes)
        assert state_path.read_bytes() == state_bytes
        yield (
            repo,
            wave,
            tip,
            index_tree,
            restore_path,
            snapshots,
            fold,
            plan,
            state_path,
            state_bytes,
        )


def _call_rollback_fold(
    repo: _Repo,
    wave: Path,
    *,
    rollback_ref: str,
    expected_tip: str,
    index_tree: str,
    snapshots,
    state_path: Path,
    expected_transaction_id: str = _ROLLBACK_TRANSACTION_ID,
) -> list[str]:
    with _cwd(wave):
        repository = LAND._verify_repository(repo.request(wave, tip=expected_tip))
        try:
            return LAND._rollback_fold(
                repository,
                rollback_ref=rollback_ref,
                expected_tip=expected_tip,
                index_tree=index_tree,
                snapshots=snapshots,
                state_path=state_path,
                expected_transaction_id=expected_transaction_id,
            )
        finally:
            repository.close()


def _exact_git_failure(
    repo: _Repo,
    subcommand: list[str],
) -> tuple[Path, dict[str, str]]:
    record = repo.root / "exact-git-failure.json"
    return _wrapper(repo.root), {
        "DEV_WAVE_REAL_GIT": REAL_GIT,
        "DEV_WAVE_WRAPPER_MODE": "fail-exact",
        "DEV_WAVE_FAIL_REPO": str(repo.main),
        "DEV_WAVE_FAIL_SUBCOMMAND": json.dumps(subcommand),
        "DEV_WAVE_FAIL_RECORD": str(record),
    }


def _assert_exact_git_failure(record: Path, expected: list[str]) -> None:
    assert record.is_file(), f"wrapper did not observe exact subcommand: {expected!r}"
    assert json.loads(record.read_text(encoding="utf-8")) == expected


def _assert_valid_state_preserved(
    fold,
    repo: _Repo,
    plan,
    state_path: Path,
    state_bytes: bytes,
) -> None:
    assert state_path.read_bytes() == state_bytes
    assert json.loads(state_bytes)["transaction_id"] == plan.transaction_id


def _land_main_fold_for_resync(repo: _Repo, winner: Path) -> str:
    (repo.main / ".git" / "info" / "exclude").write_text(
        ".codex/worktrees/\n.claude/worktrees/\n",
        encoding="utf-8",
    )
    relative, _fragment, _content = _fake_pending_fragment(
        repo, winner, wave_slug="resync-main",
    )
    winner_tip = _git(winner, "rev-parse", "HEAD")

    def apply(repo_path: Path, _plan) -> None:
        (repo_path / relative).unlink()
        receipt = {
            "allocations": {},
            "authored": "2000-01-01",
            "content_sha256": hashlib.sha256(_content.encode("utf-8")).hexdigest(),
            "seq": 1,
            "wave": "resync-main",
        }
        folded = repo_path / "docs/spool/FOLDED.md"
        folded.write_text(
            folded.read_text(encoding="utf-8")
            + "- "
            + json.dumps(
                receipt,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    module = _FakeFoldModule(
        _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
        ),
        apply,
    )
    with (
        _patched_land_attr("_load_spool_fold", lambda: module),
        _patched_land_attr("_preflight_fold_message", lambda *_args: None),
    ):
        result = _land(repo.request(winner, tip=winner_tip))
    assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
    assert result.fold_commit_sha == result.main_after
    assert result.fold_commit_sha is not None
    assert LAND._load_spool_fold().validate_spool_layout(repo.main) == []
    return result.fold_commit_sha


def test_zero_fragment_preserves_land_result_and_commit_graph_bit_for_bit() -> None:
    """P03: fragment 0 件では既存 landed/already-landed を bit 単位で固定する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        tip = repo.commit(wave, "wave.txt", "wave\n")

        first_request = repo.request(wave, tip=tip)
        receipt_digest = hashlib.sha256(
            first_request.acceptance_receipt.read_bytes()
        ).hexdigest()
        first = _land(first_request)
        second = _land(repo.request(wave, tip=tip))

        assert first == LAND.LandResult(
            LAND.RC_OK,
            "landed",
            "main fast-forwarded to the tested wave tip",
            repo.base,
            tip,
            tip,
            acceptance_receipt_sha256=receipt_digest,
            acceptance_verdict="child-green",
            acceptance_red_nodeids=(),
            acceptance_flake_nodeids=(),
            tested_tip_sha=tip,
            landing_tip_sha=tip,
        )
        assert second == LAND.LandResult(
            LAND.RC_OK,
            "already-landed",
            "another lander reached the tested tip first",
            tip,
            tip,
            tip,
            acceptance_receipt_sha256=receipt_digest,
            acceptance_verdict="child-green",
            acceptance_red_nodeids=(),
            acceptance_flake_nodeids=(),
            tested_tip_sha=tip,
            landing_tip_sha=tip,
        )
        assert _git(repo.main, "rev-list", "--count", f"{repo.base}..HEAD") == "1"
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_zero_fragment_still_rejects_missing_spool_layout_before_ff() -> None:
    """F-5: pending 0 でも layout 防壁を削除した候補を no-op 扱いしない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        shutil.rmtree(wave / "docs" / "spool")
        _git(wave, "add", "-A", "docs/spool")
        _git(wave, "commit", "-qm", "remove spool layout")
        tip = _git(wave, "rev-parse", "HEAD")

        result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert "docs/spool" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_candidate_fold_plan_failure_happens_before_ff() -> None:
    """F-2: candidate tree の plan が赤なら main を 1 commit も進めない。"""

    class FailingPlanModule(_FakeFoldModule):
        def plan_fold(self, repo: Path, *, fold_date: str, origin):
            raise RuntimeError("synthetic plan failure")

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        module = FailingPlanModule(_FakeFoldPlan("docs/spool/worklog/missing.md"), lambda *_args: None)

        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert "synthetic plan failure" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_fold_is_called_under_land_lock_and_committed_with_message_file() -> None:
    """N23: lock 内 fold 呼出しを削除すると pending の GC/commit が消えて赤になる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        lock_observed = False

        def apply(repo_path: Path, _plan) -> None:
            nonlocal lock_observed
            contender = os.open(
                repo.main / ".git" / "dev-wave-land.lock",
                os.O_RDWR | os.O_NOFOLLOW,
            )
            try:
                try:
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    lock_observed = True
                else:
                    raise AssertionError("fold ran outside the cooperative land lock")
            finally:
                os.close(contender)
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text(folded.read_text(encoding="utf-8") + "- folded\n", encoding="utf-8")

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        wrapper = _wrapper(repo.root)
        record = repo.root / "fold-git-calls.jsonl"
        request = repo.request(wave, tip=tip)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
            _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "record",
                "DEV_WAVE_RECORD": str(record),
            }),
        ):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert lock_observed
        assert result.main_after != tip
        assert result.fold_commit_sha == result.main_after
        assert _git(repo.main, "rev-parse", f"{result.main_after}^") == tip
        assert not (repo.main / relative).exists()
        assert _git(repo.main, "status", "--porcelain=v1") == ""
        message = _git(repo.main, "show", "-s", "--format=%B", result.main_after)
        assert message == LAND._FOLD_MESSAGE.rstrip("\n")
        assert _git(repo.main, "show", "-s", "--format=%an <%ae>", result.main_after) == (
            LAND.FOLD_AUTHOR_IDENTITY
        )
        calls = [
            json.loads(line)
            for line in record.read_text(encoding="utf-8").splitlines()
        ]
        commit_calls = [args for args in calls if "commit" in args]
        assert len(commit_calls) == 1, calls
        commit_args = commit_calls[0]
        commit_index = commit_args.index("commit")
        assert commit_args[commit_index:commit_index + 3] == [
            "commit", "--no-gpg-sign", "-F",
        ]
        assert "-m" not in commit_args and "--no-edit" not in commit_args
        observed_origin = module._plan.origin
        assert observed_origin is not None
        independently_audited = repo.audited(repo.base, tip, wave)
        assert observed_origin == _FakeFoldOrigin(
            kind="land",
            base=repo.base,
            tested_tip=_git(wave, "rev-parse", "HEAD"),
            wave_ref=_git(wave, "symbolic-ref", "HEAD"),
            rollback_ref=repo.base,
            trusted_main_cutoff=repo.base,
            audited_digest=module.audited_commit_digest(independently_audited),
        )
        assert independently_audited == request.audited_commits
        assert module.events == ["plan", "apply", "mark", "finalize"]


def test_fold_lifecycle_orders_mark_postconditions_declared_and_finalize() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text("# receipts\n- ordered\n", encoding="utf-8")

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        events = module.events
        original_git = LAND._git
        original_main_dirt = LAND._verify_main_no_tracked_dirt
        original_declared = LAND.verify_declared_fold_commit

        def observed_git(repo_path: Path, *args: str, **kwargs):
            if args and args[0] == "commit":
                events.append("commit")
            return original_git(repo_path, *args, **kwargs)

        def observed_main_dirt(repository) -> None:
            original_main_dirt(repository)
            if _git(repository.main, "rev-parse", "HEAD") != tip:
                events.append("postcondition")

        def observed_declared(*args, **kwargs):
            if kwargs.get("fold_commit_sha") is not None:
                events.append("declared")
            return original_declared(*args, **kwargs)

        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
            _patched_land_attr("_git", observed_git),
            _patched_land_attr("_verify_main_no_tracked_dirt", observed_main_dirt),
            _patched_land_attr("verify_declared_fold_commit", observed_declared),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert events == [
            "plan",
            "apply",
            "commit",
            "mark",
            "postcondition",
            "declared",
            "finalize",
        ]


def test_finalize_failure_keeps_verified_fold_commit_and_never_rolls_back() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            (repo_path / "docs/spool/FOLDED.md").write_text(
                "# receipts\n- finalize-failure\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
            fail_finalize=True,
        )
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
            _patched_land_attr(
                "_rollback_fold",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("finalize failure must not roll back")
                ),
            ),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_FINALIZE_FAILED,
            "fold-finalize-failed",
        ), result
        assert (result.release_safe, result.retryable_same_request) == (False, True)
        assert "synthetic finalize failure" in result.reason
        assert result.main_after == _git(repo.main, "rev-parse", "HEAD")
        assert _git(repo.main, "rev-parse", f"{result.main_after}^") == tip
        assert module.events[-2:] == ["mark", "finalize"]


def test_generated_docs_declares_exact_active_transaction() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        plan = _FakeFoldPlan("docs/spool/worklog/synthetic.md")
        with _cwd(wave):
            repository = LAND._verify_repository(repo.request(wave))
        observed: list[list[str]] = []
        original_run = LAND.subprocess.run

        def capture(argv, **_kwargs):
            observed.append(argv)
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        try:
            LAND.subprocess.run = capture
            LAND._validate_generated_docs(repository, plan)
        finally:
            LAND.subprocess.run = original_run
            repository.close()

        assert observed == [[
            sys.executable,
            str(repo.main / "tools" / "check_docs.py"),
            "--expect-active-transaction",
            plan.transaction_id,
        ]]


def test_land_folds_rotation_inside_lock() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        rotate_limit = 900
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        historic_body = "- " + ("historic rotation bytes " * 90) + "\n"
        worklog = (
            "# worklog\n\n## ローテーション\n\n---\n\n"
            "## 2026-08-01 (1) — old entry large enough to rotate\n\n"
            f"{historic_body}\n### 次の一手\n\n- [T-001] historic task\n\n"
            "## 2026-08-02 (2) — current entry\n\n- current body\n\n"
            "### 次の一手\n\n- [T-001] current task\n"
        )
        canonical = {
            "docs/worklog.md": worklog,
            "docs/decisions.md": (
                "# decisions\n\n## D1. seed (2026-08-01)\n\n**決定:** seed\n"
            ),
            "docs/failures.md": (
                "# failures\n\n## エントリ\n\n### F1. seed [手順漏れ]\n"
                "- 事象: seed\n- 根本原因: seed\n- 恒久対応: seed\n- 再発検知: seed\n"
            ),
            "docs/phase3.md": (
                "# phase3\n\n## 見送り台帳\n\n### プロセス文書系\n\n"
                "- [T-050] 既存見送り — 理由: seed\n\n"
                "### 研究・計測系\n\n- [T-051] 既存見送り — 理由: seed\n\n"
                "### 裁定・完了記録\n\n- [T-052] 完了済み\n"
            ),
            "docs/archive/README.md": "# archive\n\n## 現在の収容物\n",
            "tools/check_docs.py": f"WORKLOG_ROTATE_BYTES = {rotate_limit}\n",
            "tools/spool_fold.py": (ROOT / "tools/spool_fold.py").read_text(
                encoding="utf-8"
            ),
        }
        for relative, content in canonical.items():
            path = wave / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        fragment_relative = "docs/spool/worklog/2026-08-03-test-wave-1.md"
        (wave / fragment_relative).write_text(
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: worklog\n"
            "authored: 2026-08-03\n"
            "wave: test-wave\n"
            "seq: 1\n"
            "title: rotation land\n"
            "---\n"
            "## 本文\n\n- folded under the land lock\n\n"
            "## 次の一手差分\n\n### carry\n\n- [T-001]\n",
            encoding="utf-8",
            newline="\n",
        )
        _git(wave, "add", "-A")
        _git(wave, "commit", "-qm", "add rotating fold fixture")
        tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, tip=tip)
        real_fold = LAND._load_spool_fold()

        class ObservedFold:
            def __init__(self):
                self.lock_observed = False
                self.rotation_path: str | None = None

            def __getattr__(self, name: str):
                return getattr(real_fold, name)

            def plan_fold(self, repo_path: Path, *, fold_date: str, origin):
                plan = real_fold.plan_fold(
                    repo_path,
                    fold_date=fold_date,
                    origin=origin,
                )
                assert plan.rotation_path is not None, plan
                self.rotation_path = plan.rotation_path
                return plan

            def apply_fold(self, repo_path: Path, plan, *, gate_receipt=None):
                contender = os.open(
                    repo.main / ".git" / "dev-wave-land.lock",
                    os.O_RDWR | os.O_NOFOLLOW,
                )
                try:
                    try:
                        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        self.lock_observed = True
                    else:
                        raise AssertionError("rotation fold ran outside the land lock")
                finally:
                    os.close(contender)
                return real_fold.apply_fold(
                    repo_path,
                    plan,
                    gate_receipt=gate_receipt,
                )

        observed = ObservedFold()
        with (
            _patched_land_attr("_load_spool_fold", lambda: observed),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert observed.lock_observed
        assert observed.rotation_path is not None
        assert (repo.main / observed.rotation_path).is_file()
        rotation_name = Path(observed.rotation_path).name
        archive_readme = (repo.main / "docs/archive/README.md").read_text(
            encoding="utf-8",
        )
        assert rotation_name in archive_readme
        assert (repo.main / "docs/worklog.md").stat().st_size <= rotate_limit
        assert result.fold_commit_sha == result.main_after
        declared = LAND.verify_declared_fold_commit(
            repo.main,
            fold_commit_sha=result.fold_commit_sha,
            landed_main_sha=result.main_after,
            landed_commits=request.audited_commits,
            wave_tip=tip,
        )
        assert declared.ok, declared


def test_land_folds_failure_supersede_inside_lock() -> None:
    """実 spool_fold の supersede 追記を cooperative land lock 内で適用する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        canonical = {
            "docs/worklog.md": (
                "# worklog\n\n## ローテーション\n\n---\n\n"
                "## 2026-08-01 (1) — seed\n\n- seed\n\n"
                "### 次の一手\n\n- [T-001] seed\n"
            ),
            "docs/decisions.md": (
                "# decisions\n\n## D1. seed (2026-08-01)\n\n**決定:** seed\n"
            ),
            "docs/failures.md": (
                "# failures\n\n## エントリ\n\n### F1. seed [手順漏れ]\n"
                "- 事象: seed\n- 根本原因: seed\n- 恒久対応: seed\n- 再発検知: seed\n"
            ),
            "docs/phase3.md": (
                "# phase3\n\n## 見送り台帳\n\n### プロセス文書系\n\n"
                "- [T-050] 既存見送り — 理由: seed\n\n"
                "### 研究・計測系\n\n- [T-051] 既存見送り — 理由: seed\n\n"
                "### 裁定・完了記録\n\n- [T-052] 完了済み\n"
            ),
            "docs/archive/README.md": "# archive\n\n## 現在の収容物\n",
            "tools/check_docs.py": "WORKLOG_ROTATE_BYTES = 100000\n",
            "tools/spool_fold.py": (ROOT / "tools/spool_fold.py").read_text(
                encoding="utf-8"
            ),
        }
        for relative, content in canonical.items():
            path = wave / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        fragment_relative = "docs/spool/failures/2026-08-10-test-wave-1.md"
        (wave / fragment_relative).write_text(
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: failures\n"
            "authored: 2026-08-10\n"
            "wave: test-wave\n"
            "seq: 1\n"
            "---\n"
            "## supersede 追記\n\n"
            "- F1 **supersede: 2026-08-10** — lock 内 fold。\n",
            encoding="utf-8",
            newline="\n",
        )
        _git(wave, "add", "-A")
        _git(wave, "commit", "-qm", "add failure supersede fold fixture")
        tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, tip=tip)
        real_fold = LAND._load_spool_fold()

        class ObservedFold:
            def __init__(self):
                self.lock_observed = False

            def __getattr__(self, name: str):
                return getattr(real_fold, name)

            def apply_fold(self, repo_path: Path, plan, *, gate_receipt=None):
                contender = os.open(
                    repo.main / ".git" / "dev-wave-land.lock",
                    os.O_RDWR | os.O_NOFOLLOW,
                )
                try:
                    try:
                        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        self.lock_observed = True
                    else:
                        raise AssertionError("failure supersede fold ran outside land lock")
                finally:
                    os.close(contender)
                return real_fold.apply_fold(
                    repo_path,
                    plan,
                    gate_receipt=gate_receipt,
                )

        observed = ObservedFold()
        with (
            _patched_land_attr("_load_spool_fold", lambda: observed),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert observed.lock_observed
        assert not (repo.main / fragment_relative).exists()
        assert (
            "- **supersede: 2026-08-10** — lock 内 fold。\n"
            in (repo.main / "docs/failures.md").read_text(encoding="utf-8")
        )
        assert result.fold_commit_sha == result.main_after


def test_p06_supervised_branch_slug_with_matching_fragments_can_fold() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n", encoding="utf-8",
        )
        run_id = "dw-" + "a" * 32
        _git(wave, "branch", "-m", f"dev-wave/{run_id}/w001")
        slug = f"dev-wave-{run_id}-w001"
        relative, _wave_fragment, _content = _fake_pending_fragment(
            repo, wave, wave_slug=slug,
        )
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text(
                folded.read_text(encoding="utf-8") + "- folded\n",
                encoding="utf-8",
            )

        plan = _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            fragments=(_FakeFoldFragment(slug),),
        )
        module = _FakeFoldModule(plan, apply)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.fold_commit_sha == result.main_after


def test_land_accepts_its_fold_commit_with_repository_commit_encoding() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n", encoding="utf-8",
        )
        _git(repo.main, "config", "i18n.commitEncoding", "ISO-8859-1")
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            folded = repo_path / "docs/spool/FOLDED.md"
            folded.write_text(
                folded.read_text(encoding="utf-8") + "- folded\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        commit_object = "\n" + _git(repo.main, "cat-file", "commit", result.main_after)
        assert "\nencoding ISO-8859-1\n" in commit_object


def test_n35_supervised_branch_rejects_fragment_from_another_slug_before_ff() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n", encoding="utf-8",
        )
        run_id = "dw-" + "a" * 32
        _git(wave, "branch", "-m", f"dev-wave/{run_id}/w001")
        slug = f"dev-wave-{run_id}-w001"
        relative, _wave_fragment, _content = _fake_pending_fragment(
            repo, wave, wave_slug=slug,
        )
        tip = _git(wave, "rev-parse", "HEAD")
        plan = _FakeFoldPlan(
            relative,
            fragments=(_FakeFoldFragment("dev-wave-dw-" + "b" * 32 + "-w001"),),
        )
        module = _FakeFoldModule(
            plan,
            lambda *_args: (_ for _ in ()).throw(AssertionError("apply must not run")),
        )
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_fold_failure_rolls_back_ff_and_never_returns_landed() -> None:
    """N24/F-2: fold 失敗は実装 commit を含めて ff 前へ戻す。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def fail_after_gc(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            raise RuntimeError("synthetic fold failure")

        module = _FakeFoldModule(_FakeFoldPlan(relative), fail_after_gc)
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed"), result
        assert "synthetic fold failure" in result.reason
        assert result.status not in {"landed", "already-landed"}
        assert result.main_after == repo.base
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert not (repo.main / relative).exists()
        assert _git(repo.main, "status", "--porcelain=v1") == ""
        assert _git(repo.main, "rev-list", "--count", f"{repo.base}..HEAD") == "0"


def test_pending_fragment_postcondition_failure_is_fold_failure() -> None:
    """N25: apply 後 pending=0 検査を削除すると残件ありで landed になって赤になる。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        module = _FakeFoldModule(_FakeFoldPlan(relative), lambda *_args: None)

        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed"), result
        assert "pending fragment postcondition failed" in result.reason
        assert result.main_after == repo.base
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert not (repo.main / relative).exists()
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_generated_canonical_validation_failure_rolls_back_ff() -> None:
    """F-3: apply 後の docs gate が赤なら fold commit も wave tip も残さない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()

        module = _FakeFoldModule(_FakeFoldPlan(relative), apply)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr(
                "_validate_generated_docs",
                lambda *_args: (_ for _ in ()).throw(RuntimeError("synthetic check_docs failure")),
            ),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed")
        assert "synthetic check_docs failure" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_rollback_fold_keeps_state_when_ref_cas_restore_fails() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            fold, plan, state_path, state_bytes,
        ) = fixture
        expected = ["update-ref", "refs/heads/main", repo.base, tip]
        assert repo.base != _git(repo.main, "rev-parse", "HEAD")
        wrapper, env = _exact_git_failure(repo, expected)
        with _patched_git(wrapper, env):
            failures = _call_rollback_fold(
                repo,
                wave,
                rollback_ref=repo.base,
                expected_tip=tip,
                index_tree=index_tree,
                snapshots=snapshots,
                state_path=state_path,
            )

        _assert_exact_git_failure(Path(env["DEV_WAVE_FAIL_RECORD"]), expected)
        assert failures == [
            "fold/main ref CAS rollback failed (synthetic exact git failure)"
        ]
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        _assert_valid_state_preserved(fold, repo, plan, state_path, state_bytes)


def test_rollback_fold_keeps_state_when_read_tree_restore_fails() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            fold, plan, state_path, state_bytes,
        ) = fixture
        expected = ["read-tree", "--reset", "-u", index_tree]
        wrapper, env = _exact_git_failure(repo, expected)
        with _patched_git(wrapper, env):
            failures = _call_rollback_fold(
                repo,
                wave,
                rollback_ref=repo.base,
                expected_tip=tip,
                index_tree=index_tree,
                snapshots=snapshots,
                state_path=state_path,
            )

        _assert_exact_git_failure(Path(env["DEV_WAVE_FAIL_RECORD"]), expected)
        assert failures == [
            "fold index/worktree rollback failed (synthetic exact git failure)"
        ]
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert (repo.main / "wave.txt").read_bytes() == b"wave\n"
        _assert_valid_state_preserved(fold, repo, plan, state_path, state_bytes)


def test_rollback_fold_keeps_state_when_path_restore_raises() -> None:
    """回帰 guard。現行実装でも例外は state block 前へ抜けるため修正検出力はない。"""

    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, restore_path, snapshots,
            fold, plan, state_path, state_bytes,
        ) = fixture
        restore_path.unlink()
        restore_path.symlink_to("FOLDED.md")

        failures = _call_rollback_fold(
            repo,
            wave,
            rollback_ref=repo.base,
            expected_tip=tip,
            index_tree=index_tree,
            snapshots=snapshots,
            state_path=state_path,
        )

        assert failures == [
            "fold rollback raised RuntimeError: rollback path is "
            "symlink/non-regular: docs/spool/rollback-path.txt"
        ]
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _git(repo.main, "write-tree") == index_tree
        assert restore_path.is_symlink()
        _assert_valid_state_preserved(fold, repo, plan, state_path, state_bytes)


def test_rollback_fold_removes_state_after_every_restore_point_succeeds() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, restore_path, snapshots,
            fold, _plan, state_path, _state_bytes,
        ) = fixture
        restore_path.write_bytes(b"rollback-after\n")
        restore_path.chmod(0o600)
        fsynced_directories: list[Path] = []
        original_fsync_directory = LAND._fsync_directory

        def observed_fsync_directory(path: Path) -> None:
            fsynced_directories.append(path)
            original_fsync_directory(path)

        with _patched_land_attr("_fsync_directory", observed_fsync_directory):
            failures = _call_rollback_fold(
                repo,
                wave,
                rollback_ref=repo.base,
                expected_tip=tip,
                index_tree=index_tree,
                snapshots=snapshots,
                state_path=state_path,
            )

        assert failures == []
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _git(repo.main, "write-tree") == index_tree
        assert not (repo.main / "wave.txt").exists()
        assert (repo.main / "base.txt").read_bytes() == b"base\n"
        assert restore_path.read_bytes() == b"rollback-before\n"
        assert stat.S_IMODE(restore_path.stat().st_mode) == 0o640
        assert not state_path.exists()
        assert not state_path.is_symlink()
        assert fsynced_directories == [state_path.parent]
        assert fold.load_active_plan(repo.main) is None


def test_rollback_fold_preserves_state_with_different_transaction_id() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            fold, plan, state_path, state_bytes,
        ) = fixture

        failures = _call_rollback_fold(
            repo,
            wave,
            rollback_ref=repo.base,
            expected_tip=tip,
            index_tree=index_tree,
            snapshots=snapshots,
            state_path=state_path,
            expected_transaction_id="b" * 64,
        )

        assert failures == [
            "fold transaction state transaction_id does not match "
            "the rollback plan; state preserved"
        ]
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        _assert_valid_state_preserved(fold, repo, plan, state_path, state_bytes)


def test_rollback_fold_reports_symlink_state_after_prior_failure() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            fold, _plan, state_path, state_bytes,
        ) = fixture
        payload_path = state_path.with_name(state_path.name + ".payload")
        state_path.replace(payload_path)
        state_path.symlink_to(payload_path.name)
        expected = ["update-ref", "refs/heads/main", repo.base, tip]
        wrapper, env = _exact_git_failure(repo, expected)
        with _patched_git(wrapper, env):
            failures = _call_rollback_fold(
                repo,
                wave,
                rollback_ref=repo.base,
                expected_tip=tip,
                index_tree=index_tree,
                snapshots=snapshots,
                state_path=state_path,
            )

        _assert_exact_git_failure(Path(env["DEV_WAVE_FAIL_RECORD"]), expected)
        assert failures == [
            "fold/main ref CAS rollback failed (synthetic exact git failure)",
            "fold transaction state is symlink/non-regular",
        ]
        assert state_path.is_symlink()
        assert state_path.read_bytes() == state_bytes
        assert payload_path.read_bytes() == state_bytes
        try:
            fold.load_active_plan(repo.main)
            assert False, "symlink state must remain rejected"
        except fold.TransactionError as exc:
            assert "regular file" in str(exc)


def test_rollback_fold_reports_directory_state_after_prior_failure() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            fold, _plan, state_path, state_bytes,
        ) = fixture
        state_path.unlink()
        state_path.mkdir()
        payload_path = state_path / "preserved-state.json"
        payload_path.write_bytes(state_bytes)
        expected = ["update-ref", "refs/heads/main", repo.base, tip]
        wrapper, env = _exact_git_failure(repo, expected)
        with _patched_git(wrapper, env):
            failures = _call_rollback_fold(
                repo,
                wave,
                rollback_ref=repo.base,
                expected_tip=tip,
                index_tree=index_tree,
                snapshots=snapshots,
                state_path=state_path,
            )

        _assert_exact_git_failure(Path(env["DEV_WAVE_FAIL_RECORD"]), expected)
        assert failures == [
            "fold/main ref CAS rollback failed (synthetic exact git failure)",
            "fold transaction state is symlink/non-regular",
        ]
        assert state_path.is_dir()
        assert payload_path.read_bytes() == state_bytes
        try:
            fold.load_active_plan(repo.main)
            assert False, "directory state must remain rejected"
        except fold.TransactionError as exc:
            assert "regular file" in str(exc)


def _fold_main_locked_with_failed_ref_rollback(
    repo: _Repo,
    wave: Path,
    tip: str,
    index_tree: str,
    snapshots,
    state_path: Path,
) -> LAND.LandResult:
    expected = ["update-ref", "refs/heads/main", repo.base, tip]
    wrapper, env = _exact_git_failure(repo, expected)
    module = _FakeFoldModule(
        _FakeFoldPlan(
            "docs/spool/worklog/synthetic.md",
            transaction_id=_ROLLBACK_TRANSACTION_ID,
        ),
        lambda *_args: (_ for _ in ()).throw(RuntimeError("synthetic apply failure")),
    )
    successful_land = LAND.LandResult(
        LAND.RC_OK,
        "landed",
        "synthetic successful fast-forward",
        repo.base,
        tip,
        tip,
    )
    with _cwd(wave):
        repository = LAND._verify_repository(repo.request(wave, tip=tip))
        try:
            with _patched_git(wrapper, env):
                result = LAND._fold_main_locked(
                    repository,
                    successful_land,
                    fold=module,
                    plan=module._plan,
                    trusted_main_cutoff_sha=repo.base,
                    tested_tip=tip,
                    landed_commits=(tip,),
                    wave_ref=_git(wave, "symbolic-ref", "HEAD"),
                    rollback_ref=repo.base,
                    snapshots=snapshots,
                    index_tree=index_tree,
                    state_path=state_path,
                )
        finally:
            repository.close()

    _assert_exact_git_failure(Path(env["DEV_WAVE_FAIL_RECORD"]), expected)
    return result


def test_fold_rollback_failure_reason_reports_preserved_state() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            fold, plan, state_path, state_bytes,
        ) = fixture
        result = _fold_main_locked_with_failed_ref_rollback(
            repo, wave, tip, index_tree, snapshots, state_path,
        )

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_ROLLBACK_FAILED,
            "fold-rollback-failed",
        )
        assert (result.release_safe, result.retryable_same_request) == (False, False)
        assert "rollback incomplete" in result.reason
        assert f"resume journal preserved at {state_path}" in result.reason
        _assert_valid_state_preserved(fold, repo, plan, state_path, state_bytes)


def test_fold_rollback_failure_reason_omits_non_regular_state_symlink() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            _fold, _plan, state_path, state_bytes,
        ) = fixture
        payload_path = state_path.with_name(state_path.name + ".payload")
        state_path.replace(payload_path)
        state_path.symlink_to(payload_path.name)

        result = _fold_main_locked_with_failed_ref_rollback(
            repo, wave, tip, index_tree, snapshots, state_path,
        )

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_ROLLBACK_FAILED,
            "fold-rollback-failed",
        )
        assert (
            "rollback incomplete: fold/main ref CAS rollback failed "
            "(synthetic exact git failure); "
            "fold transaction state is symlink/non-regular"
        ) in result.reason
        assert "resume journal preserved at" not in result.reason
        assert f"non-resumable transaction state remains at {state_path}" in result.reason
        assert state_path.is_symlink()
        assert payload_path.read_bytes() == state_bytes


def test_fold_rollback_failure_reason_omits_non_regular_state_directory() -> None:
    with _rollback_fold_fixture() as fixture:
        (
            repo, wave, tip, index_tree, _restore_path, snapshots,
            _fold, _plan, state_path, state_bytes,
        ) = fixture
        state_path.unlink()
        state_path.mkdir()
        payload_path = state_path / "preserved-state.json"
        payload_path.write_bytes(state_bytes)

        result = _fold_main_locked_with_failed_ref_rollback(
            repo, wave, tip, index_tree, snapshots, state_path,
        )

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_ROLLBACK_FAILED,
            "fold-rollback-failed",
        )
        assert (
            "rollback incomplete: fold/main ref CAS rollback failed "
            "(synthetic exact git failure); "
            "fold transaction state is symlink/non-regular"
        ) in result.reason
        assert "resume journal preserved at" not in result.reason
        assert f"non-resumable transaction state remains at {state_path}" in result.reason
        assert state_path.is_dir()
        assert payload_path.read_bytes() == state_bytes


def test_failed_cas_rollback_has_distinct_rc_and_status() -> None:
    """F-2: main を戻せない異常を通常の fold-failed と混同しない。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def fail_after_gc(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            raise RuntimeError("synthetic fold failure")

        module = _FakeFoldModule(_FakeFoldPlan(relative), fail_after_gc)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_rollback_fold", lambda *_args, **_kwargs: ["synthetic CAS refusal"]),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_ROLLBACK_FAILED,
            "fold-rollback-failed",
        )
        assert "rollback incomplete" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_active_transaction_resumes_before_main_dirty_gate() -> None:
    """F-6: complete shape の stored plan を通常 land から形 A として完遂する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "merge", "--ff-only", tip)
        receipt_rel = "docs/spool/FOLDED.md"
        (repo.main / receipt_rel).write_text("# receipts\n- resumed\n", encoding="utf-8")
        (repo.main / relative).unlink()

        def resume(repo_path: Path, _plan) -> None:
            (repo_path / receipt_rel).write_text("# receipts\n- resumed\n", encoding="utf-8")
            assert not (repo_path / relative).exists()

        plan = _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget(receipt_rel),),
        )
        module = _FakeFoldModule(plan, resume, active=True)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.main_after != tip
        assert _git(repo.main, "rev-parse", f"{result.main_after}^") == tip
        assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_shape_a_rollback_uses_stored_rollback_ref_tree() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, tip=tip)
        _git(repo.main, "merge", "--ff-only", tip)
        (repo.main / "docs/spool/FOLDED.md").write_text(
            "# receipts\n- shape-a-complete\n",
            encoding="utf-8",
        )
        (repo.main / relative).unlink()
        origin = _FakeFoldOrigin(
            kind="land",
            base=repo.base,
            tested_tip=tip,
            wave_ref=_git(wave, "symbolic-ref", "HEAD"),
            rollback_ref=repo.base,
            trusted_main_cutoff=repo.base,
            audited_digest=_FakeFoldModule.audited_commit_digest(
                repo.audited(repo.base, tip, wave)
            ),
        )
        plan = _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            origin=origin,
        )
        module = _FakeFoldModule(
            plan,
            lambda *_args: (_ for _ in ()).throw(
                RuntimeError("synthetic recovery apply failure")
            ),
            active=True,
        )
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_FOLD_FAILED, "fold-failed"), result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert _git(repo.main, "write-tree") == _git(repo.main, "rev-parse", f"{repo.base}^{{tree}}")
        assert not (repo.main / relative).exists()


def test_active_transaction_recovery_completes_with_provenance_red() -> None:
    """正例/M8: active recovery は checker 欠落・非0・timeout を起動しない。"""

    for mode in ("missing", "nonzero", "timeout"):
        with _repo() as repo:
            wave = repo.waves["one"]
            (repo.main / ".git" / "info" / "exclude").write_text(
                ".codex/worktrees/\n",
                encoding="utf-8",
            )
            if mode == "missing":
                _git(wave, "rm", "tools/check_ai_provenance.py")
                _git(wave, "commit", "-qm", "remove provenance checker")
            elif mode == "nonzero":
                repo.commit(
                    wave,
                    "tools/check_ai_provenance.py",
                    "raise SystemExit(73)\n",
                )
            else:
                repo.commit(
                    wave,
                    "tools/check_ai_provenance.py",
                    "import time\ntime.sleep(600)\n",
                )
            relative, _wave_fragment, _content = _fake_pending_fragment(repo, wave)
            tip = _git(wave, "rev-parse", "HEAD")
            _git(repo.main, "merge", "--ff-only", tip)
            receipt_rel = "docs/spool/FOLDED.md"
            (repo.main / receipt_rel).write_text(
                f"# receipts\n- resumed-{mode}-provenance\n", encoding="utf-8"
            )
            (repo.main / relative).unlink()

            def resume(repo_path: Path, _plan) -> None:
                (repo_path / receipt_rel).write_text(
                    f"# receipts\n- resumed-{mode}-provenance\n",
                    encoding="utf-8",
                )
                assert not (repo_path / relative).exists()

            plan = _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget(receipt_rel),),
            )
            module = _FakeFoldModule(plan, resume, active=True)
            original_run = LAND.subprocess.run

            def timeout_checker(argv, **kwargs):
                if isinstance(argv, list) and argv and argv[0] == LAND._GIT_EXE:
                    return original_run(argv, **kwargs)
                if argv == [
                    sys.executable,
                    str(wave / "tools" / "check_ai_provenance.py"),
                ]:
                    raise subprocess.TimeoutExpired(argv, 480)
                return original_run(argv, **kwargs)

            try:
                if mode == "timeout":
                    LAND.subprocess.run = timeout_checker
                with (
                    _patched_land_attr("_load_spool_fold", lambda: module),
                    _patched_land_attr(
                        "_preflight_fold_message", lambda *_args: None
                    ),
                ):
                    result = _land(repo.request(wave, tip=tip))
            finally:
                LAND.subprocess.run = original_run

            assert (result.rc, result.status) == (
                LAND.RC_OK,
                "landed",
            ), (mode, result)
            assert result.main_after != tip
            assert _git(repo.main, "rev-parse", f"{result.main_after}^") == tip
            assert _git(repo.main, "status", "--porcelain=v1") == ""


def test_shape_b_finalizes_without_reapply_recommit_or_provenance_audit() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            (repo_path / "docs/spool/FOLDED.md").write_text(
                "# receipts\n- shape-b\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        request = repo.request(wave, tip=tip)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            first = _land(request)
        assert (first.rc, first.status) == (LAND.RC_OK, "landed"), first
        fold_commit = first.main_after
        assert fold_commit is not None
        commit_count = _git(repo.main, "rev-list", "--count", f"{repo.base}..HEAD")

        module._plan = module._plan.with_phase("applied")
        module._active = True
        module._apply = lambda *_args: (_ for _ in ()).throw(
            AssertionError("shape B must not reapply")
        )
        module.events.clear()
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr(
                "_audit_provenance_history",
                lambda *_args: (_ for _ in ()).throw(
                    AssertionError("shape B must not run provenance audit")
                ),
            ),
        ):
            recovered = _land(request)

        assert (recovered.rc, recovered.status) == (LAND.RC_OK, "landed"), recovered
        assert recovered.main_after == fold_commit
        assert _git(repo.main, "rev-parse", "HEAD") == fold_commit
        assert _git(repo.main, "rev-list", "--count", f"{repo.base}..HEAD") == commit_count
        assert module.events == ["verify", "mark", "finalize"]


def test_shape_b_rejects_active_origin_from_different_existing_wave_ref() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        canonical = {
            "docs/worklog.md": (
                "# worklog\n\n## ローテーション\n\n---\n\n"
                "## 2026-08-01 (1) — seed\n\n- seed\n\n"
                "### 次の一手\n\n- [T-001] seed\n"
            ),
            "docs/decisions.md": (
                "# decisions\n\n## D1. seed (2026-08-01)\n\n**決定:** seed\n"
            ),
            "docs/failures.md": (
                "# failures\n\n## エントリ\n\n### F1. seed [手順漏れ]\n"
                "- 事象: seed\n- 根本原因: seed\n- 恒久対応: seed\n- 再発検知: seed\n"
            ),
            "docs/phase3.md": (
                "# phase3\n\n## 見送り台帳\n\n### プロセス文書系\n\n"
                "- [T-050] 既存見送り — 理由: seed\n\n"
                "### 研究・計測系\n\n- [T-051] 既存見送り — 理由: seed\n\n"
                "### 裁定・完了記録\n\n- [T-052] 完了済み\n"
            ),
            "docs/archive/README.md": "# archive\n\n## 現在の収容物\n",
            "tools/check_docs.py": "WORKLOG_ROTATE_BYTES = 100000\n",
            "tools/spool_fold.py": (ROOT / "tools/spool_fold.py").read_text(
                encoding="utf-8"
            ),
        }
        for relative, content in canonical.items():
            path = wave / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        fragment_relative = "docs/spool/worklog/2026-08-03-test-wave-1.md"
        (wave / fragment_relative).write_text(
            "---\n"
            "schema: izanagi-spool-v1\n"
            "ledger: worklog\n"
            "authored: 2026-08-03\n"
            "wave: test-wave\n"
            "seq: 1\n"
            "title: wave ref gate\n"
            "---\n"
            "## 本文\n\n- fold for wave ref gate\n\n"
            "## 次の一手差分\n\n### carry\n\n- [T-001]\n",
            encoding="utf-8",
            newline="\n",
        )
        _git(wave, "add", "-A")
        _git(wave, "commit", "-qm", "add wave ref recovery fixture")
        tip = _git(wave, "rev-parse", "HEAD")
        wave_ref = _git(wave, "symbolic-ref", "HEAD")
        audited = repo.audited(repo.base, tip, wave)
        fold = LAND._load_spool_fold()
        origin = fold.FoldOrigin(
            kind="land",
            base=repo.base,
            tested_tip=tip,
            wave_ref=wave_ref,
            rollback_ref=repo.base,
            trusted_main_cutoff=repo.base,
            audited_digest=fold.audited_commit_digest(audited),
        )
        plan = fold.plan_fold(wave, fold_date="2026-08-03", origin=origin)
        request = repo.request(wave, tip=tip)
        _git(repo.main, "merge", "--ff-only", tip)
        fold.apply_fold(
            repo.main,
            plan,
            gate_receipt=_durable_fake_gate_receipt(fold, plan),
        )
        _git(repo.main, "add", "-A")
        subprocess.run(
            [
                REAL_GIT, "-C", str(repo.main), "commit", "--no-gpg-sign",
                "--cleanup=verbatim", f"--author={LAND.FOLD_AUTHOR_IDENTITY}",
                "-F", "-",
            ],
            check=True,
            input=LAND._FOLD_MESSAGE.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        fold_commit = _git(repo.main, "rev-parse", "HEAD")

        other_ref = "refs/heads/wave/other-existing"
        _git(wave, "branch", other_ref.removeprefix("refs/heads/"), tip)
        assert _git(wave, "rev-parse", "--verify", other_ref) == tip
        assert other_ref != wave_ref
        stored_origin = dataclasses.replace(plan.origin, wave_ref=other_ref)
        transaction_id = fold._plan_transaction_id(
            plan.fold_date,
            stored_origin,
            plan.input_closure_sha256,
            plan.fragments,
            plan.gc_paths,
            plan.projected_worklog_bytes,
            plan.rotation_path,
            plan.targets,
        )
        stored_plan = dataclasses.replace(
            plan,
            origin=stored_origin,
            transaction_id=transaction_id,
        )
        state_path = fold._state_path(repo.main)
        fold._atomic_write(
            state_path,
            json.dumps(
                fold._plan_state(stored_plan),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8") + b"\n",
        )
        loaded = fold.load_active_plan(repo.main)
        assert loaded is not None
        assert loaded.transaction_id == transaction_id
        assert loaded.input_closure_sha256 == plan.input_closure_sha256
        assert loaded.targets == stored_plan.targets
        assert loaded.gc_paths == stored_plan.gc_paths
        fold.verify_fold_commit_identity(repo.main, loaded, fold_commit=fold_commit)

        with _patched_land_attr("_load_spool_fold", lambda: fold):
            recovered = _land(request)

        assert (recovered.rc, recovered.status) == (
            LAND.RC_FOLD_RECOVERY_FAILED,
            "fold-recovery-failed",
        ), recovered
        assert "origin wave_ref" in recovered.reason
        assert _git(repo.main, "rev-parse", "HEAD") == fold_commit
        assert fold.load_active_plan(repo.main).transaction_id == transaction_id


def test_shape_b_rejects_fold_commit_whose_parent_is_not_tested_tip() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            (repo_path / "docs/spool/FOLDED.md").write_text(
                "# receipts\n- parent-check\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        request = repo.request(wave, tip=tip)
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            first = _land(request)
        assert (first.rc, first.status) == (LAND.RC_OK, "landed"), first

        (repo.main / "unexpected.txt").write_text("wrong parent\n", encoding="utf-8")
        _git(repo.main, "add", "unexpected.txt")
        _git(repo.main, "commit", "-qm", "advance beyond fold commit")
        advanced = _git(repo.main, "rev-parse", "HEAD")
        module._plan = module._plan.with_phase("applied")
        module._active = True
        module.events.clear()
        with _patched_land_attr("_load_spool_fold", lambda: module):
            recovered = _land(request)

        assert (recovered.rc, recovered.status) == (
            LAND.RC_FOLD_RECOVERY_FAILED,
            "fold-recovery-failed",
        ), recovered
        assert _git(repo.main, "rev-parse", "HEAD") == advanced
        assert module.events == ["verify"]


def test_standalone_origin_state_is_not_auto_recovered() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        _git(repo.main, "merge", "--ff-only", tip)
        plan = _FakeFoldPlan(
            "docs/spool/worklog/synthetic.md",
            origin=_FakeFoldOrigin(
                kind="standalone",
                base=tip,
                tested_tip=tip,
                wave_ref="refs/heads/main",
                rollback_ref=tip,
                trusted_main_cutoff=tip,
                audited_digest=_FakeFoldModule.audited_commit_digest(()),
            ),
        )
        module = _FakeFoldModule(
            plan,
            lambda *_args: (_ for _ in ()).throw(
                AssertionError("standalone state must not be applied")
            ),
            active=True,
        )
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        state_path = module._state_path(repo.main).absolute()
        assert (result.rc, result.status) == (
            LAND.RC_FOLD_RECOVERY_FAILED,
            "fold-recovery-failed",
        ), result
        assert str(state_path) in result.reason
        assert "lock-aware finalize command は未実装" in result.reason
        assert module.events == []


def test_not_landed_is_distinct_from_postcondition_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "not-landed",
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_NOT_LANDED, "not-landed")
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_partial_merge_mutation_is_nonretryable_postcondition_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "partial",
            "DEV_WAVE_PARTIAL_PATH": str(repo.main / "base.txt"),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert (repo.main / "base.txt").read_text() == "partial mutation\n"


def test_unobservable_post_merge_head_is_nonretryable_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        marker = repo.root / "merged"
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "hide-head",
            "DEV_WAVE_MARKER": str(marker),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_control_plane_replacement_around_status_is_rejected() -> None:
    """[意図した挙動変更] 差し替えの拒否は worktree 面に残り、handoff 面では消える。

    ``file`` = foreign handoff を同 bytes・別 inode へ差し替える形。per-entry
    identity を捨てたので期待値を ``landed`` へ反転する (assert は削除せず反転)。
    ``directory`` = 登録済み foreign worktree の差し替えで、負例として不変。
    """
    expectations = {
        "file": (LAND.RC_OK, "landed"),
        "directory": (LAND.RC_CONTROL_PLANE, "rejected"),
    }
    for kind, expected in expectations.items():
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            tip = repo.commit(wave, "wave.txt", "wave\n")
            target = (
                _handoff(repo)
                if kind == "file"
                else repo.waves["foreign"]
            )
            wrapper = _wrapper(repo.root)
            marker = repo.root / f"replaced-{kind}"
            backup = repo.root / f"replacement-backup-{kind}"
            with _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "replace-control",
                "DEV_WAVE_MARKER": str(marker),
                "DEV_WAVE_REPLACE_TARGET": str(target),
                "DEV_WAVE_REPLACE_BACKUP": str(backup),
                "DEV_WAVE_REPLACE_KIND": kind,
            }):
                result = _land(repo.request(wave, tip=tip))
            assert (result.rc, result.status) == expected, (kind, result)
            assert marker.exists(), kind
            assert _git(repo.main, "rev-parse", "HEAD") == (
                tip if kind == "file" else repo.base
            ), kind


def test_control_plane_replacement_after_collision_inspection_is_rejected() -> None:
    """[意図した挙動変更] land 直前 (:1343) の再観測も handoff の内容/inode を見ない。

    ``directory`` は負例として不変。``file`` は 764/766 と同じ理由で ``landed`` へ
    反転する — この 2 窓は同じ ``_ControlSnapshot`` 比較なので同時に閉じる。
    """
    expectations = {
        "file": (LAND.RC_OK, "landed"),
        "directory": (LAND.RC_CONTROL_PLANE, "rejected"),
    }
    for kind, expected in expectations.items():
        with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
            wave = repo.waves["author"]
            tip = repo.commit(wave, "base.txt", "wave replacement\n")
            target = (
                _handoff(repo)
                if kind == "file"
                else repo.waves["foreign"]
            )
            wrapper = _wrapper(repo.root)
            marker = repo.root / f"collision-replaced-{kind}"
            backup = repo.root / f"collision-replacement-backup-{kind}"
            with _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "replace-after-collision",
                "DEV_WAVE_MARKER": str(marker),
                "DEV_WAVE_REPLACE_TARGET": str(target),
                "DEV_WAVE_REPLACE_BACKUP": str(backup),
                "DEV_WAVE_REPLACE_KIND": kind,
            }):
                result = _land(repo.request(wave, tip=tip))
            assert (result.rc, result.status) == expected, (kind, result)
            assert marker.exists(), kind
            assert _git(repo.main, "rev-parse", "HEAD") == (
                tip if kind == "file" else repo.base
            ), kind


def test_foreign_handoff_edited_in_place_around_status_does_not_block_land() -> None:
    """P4 の正例: 他セッションが handoff を in-place 更新しても land は落ちない。

    運用ルール (節目ごと + 10 分おきに育てる) の書き込みは inode を保存して
    bytes を変える。identities へ内容 sha256 を戻すとこの test が赤になる。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo)
        inode_before = handoff.lstat().st_ino
        updated = _handoff_text(repo, state="中断") + "\n節目の追記\n"
        wrapper = _wrapper(repo.root)
        marker = repo.root / "handoff-edited"
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "edit-handoff",
            "DEV_WAVE_EDIT_MARKER": str(marker),
            "DEV_WAVE_EDIT_TARGET": str(handoff),
            "DEV_WAVE_EDIT_PAYLOAD": updated,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert marker.exists()
        assert handoff.lstat().st_ino == inode_before
        assert handoff.read_text(encoding="utf-8") == updated
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_foreign_handoff_appearing_mid_flight_is_still_rejected() -> None:
    """N3: status を跨いで新しい名前の handoff が現れたら拒否し続ける。"""
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        _handoff(repo)
        appearing = repo.main / "docs" / "handoff" / "appearing.md"
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "create-handoff",
            "DEV_WAVE_CREATE_MARKER": str(repo.root / "handoff-created"),
            "DEV_WAVE_CREATE_PATH": str(appearing),
            "DEV_WAVE_CREATE_PAYLOAD": _handoff_text(repo),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert appearing.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_foreign_handoff_disappearing_mid_flight_is_still_rejected() -> None:
    """N3 の消失方向: 他セッションが正常終了して handoff を回収しても拒否する。

    出現方向 (``create-handoff``) だけでは名前集合の片側しか押さえられない。
    他セッションの正常終了 (handoff の回収) は「名前集合が縮む」形であり、
    出現だけを拒否して消失を見逃す実装をここで赤にする。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        disappearing = _handoff(repo, name="disappearing.md")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "remove-handoff",
            "DEV_WAVE_REMOVE_MARKER": str(repo.root / "handoff-removed"),
            "DEV_WAVE_REMOVE_PATH": str(disappearing),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert not disappearing.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_handoff_directory_replacement_around_status_is_still_rejected() -> None:
    """N4: docs/handoff 自身の差し替えは拒否し続ける。

    子エントリを名前ごと保存して差し替えるので、名前集合は一致する。
    dir identity を落とした実装だけがこれを見逃す。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff_dir = repo.main / "docs" / "handoff"
        _handoff(repo)
        inode_before = handoff_dir.lstat().st_ino
        names_before = sorted(path.name for path in handoff_dir.iterdir())
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "swap-handoff-dir",
            "DEV_WAVE_SWAP_MARKER": str(repo.root / "handoff-dir-swapped"),
            "DEV_WAVE_SWAP_TARGET": str(handoff_dir),
            "DEV_WAVE_SWAP_BACKUP": str(repo.root / "handoff-dir-backup"),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert result.rc == LAND.RC_CONTROL_PLANE, result
        assert sorted(path.name for path in handoff_dir.iterdir()) == names_before
        assert handoff_dir.lstat().st_ino != inode_before
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_post_land_is_not_failed_by_foreign_handoff_activity() -> None:
    """P3: merge 後の foreign handoff 活動を自分の land の failure にしない。

    post-land で control-plane を再観測すると、他セッションの正常な handoff
    作成・更新が非再試行の RC_LANDED_POSTCONDITION_FAILED になる。
    """
    with _repo(waves=(("codex", "author"), ("claude", "foreign"))) as repo:
        wave = repo.waves["author"]
        tip = repo.commit(wave, "author.txt", "author\n")
        handoff = _handoff(repo)
        appearing = repo.main / "docs" / "handoff" / "post-land.md"
        updated = _handoff_text(repo, state="中断") + "\nland 後の追記\n"
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "handoff-after-merge",
            "DEV_WAVE_MERGED": str(repo.root / "merged"),
            "DEV_WAVE_CREATE_MARKER": str(repo.root / "post-land-created"),
            "DEV_WAVE_CREATE_PATH": str(appearing),
            "DEV_WAVE_CREATE_PAYLOAD": _handoff_text(repo),
            "DEV_WAVE_EDIT_MARKER": str(repo.root / "post-land-edited"),
            "DEV_WAVE_EDIT_TARGET": str(handoff),
            "DEV_WAVE_EDIT_PAYLOAD": updated,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert appearing.exists()
        assert handoff.read_text(encoding="utf-8") == updated
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_git_operation_surface_is_read_only_except_sha_ff_merge() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        record = repo.root / "git-calls.jsonl"
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "record",
            "DEV_WAVE_RECORD": str(record),
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (result.rc, result.status) == (0, "landed"), result
        calls = [
            json.loads(line)
            for line in record.read_text(encoding="utf-8").splitlines()
        ]
        merge_calls = [args for args in calls if "merge" in args]
        assert len(merge_calls) == 1, calls
        merge = merge_calls[0]
        index = merge.index("merge")
        assert merge[index:] == [
            "merge", "--ff-only", "--no-stat", "--no-progress", tip,
        ]
        forbidden = {
            "push", "fetch", "pull", "rebase", "reset", "checkout", "stash",
            "branch", "switch", "remote", "update-ref", "worktree",
        }
        for args in calls:
            assert forbidden.isdisjoint(args), args
            if "config" in args:
                assert "--get-regexp" in args and "--includes" in args, args
        assert not any(
            any("tools/check_acceptance_reds.py" in arg for arg in args)
            for args in calls
        ), calls


def test_merge_child_inherits_only_explicit_lock_not_other_parent_fd() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        wrapper = _wrapper(repo.root)
        fd_record = repo.root / "fd-record.json"
        sentinel_path = repo.root / "sentinel"
        sentinel_fd = os.open(sentinel_path, os.O_RDWR | os.O_CREAT, 0o600)
        os.set_inheritable(sentinel_fd, True)
        try:
            with _patched_git(wrapper, {
                "DEV_WAVE_REAL_GIT": REAL_GIT,
                "DEV_WAVE_WRAPPER_MODE": "audit-fds",
                "DEV_WAVE_FD_RECORD": str(fd_record),
            }):
                result = _land(repo.request(wave, tip=tip))
        finally:
            os.close(sentinel_fd)
        assert (result.rc, result.status) == (0, "landed"), result
        targets = json.loads(fd_record.read_text(encoding="utf-8"))
        inherited = set(targets.values())
        assert str(sentinel_path) not in inherited, targets
        lock_targets = [
            target for target in inherited
            if target.endswith("/dev-wave-land.lock")
        ]
        assert len(lock_targets) == 1, targets


def test_wave_move_after_merge_is_landed_postcondition_failed() -> None:
    """M9: main は T に達したが wave ref が動いた事実を retryable failureへ潰さない。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        tree = _git(wave, "rev-parse", f"{tip}^{{tree}}")
        moved = _git(wave, "commit-tree", tree, "-p", tip, "-m", "moved tip")
        wave_ref = _git(wave, "symbolic-ref", "HEAD")
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "move-wave",
            "DEV_WAVE_MOVE_REPO": str(wave),
            "DEV_WAVE_MOVE_REF": wave_ref,
            "DEV_WAVE_MOVE_TO": moved,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert _git(wave, "rev-parse", "HEAD") == moved


def test_tracked_dirt_appearing_after_successful_merge_is_postcondition_failed() -> None:
    """N6 の post-land 面: main が T に達した後の tracked dirt を成功に潰さない。

    ``_verify_main_no_tracked_dirt`` の**成功経路**を守る唯一の入力である。
    pre-land の ``_verify_main_clean`` は merge 前にしか走らず、
    ``_postcondition`` 成功枝の先行検査 (symbolic HEAD / ref sha / wave 三点)
    はいずれも main の worktree dirt を観測しない。つまりこの入力を拒否できる
    位置は ``_postcondition`` 成功枝の ``_verify_main_no_tracked_dirt``
    1 箇所しかない (DW-M01)。
    """
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        dirt = "merge 後に現れた tracked dirt\n"
        wrapper = _wrapper(repo.root)
        with _patched_git(wrapper, {
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "dirty-after-merge",
            "DEV_WAVE_DIRTY_PATH": str(repo.main / "base.txt"),
            "DEV_WAVE_DIRTY_PAYLOAD": dirt,
        }):
            result = _land(repo.request(wave, tip=tip))
        assert (
            result.rc,
            result.status,
        ) == (
            LAND.RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
        ), result
        # 成功枝 (main_after == tested tip) を通ったことを固定する。失敗枝の
        # _main_tracked_or_index_dirty との取り違えをここで排除する。
        assert (result.main_before, result.main_after) == (repo.base, tip), result
        assert result.reason == "main tracked/index/submodule dirt is forbidden", result
        assert _git(repo.main, "rev-parse", "HEAD") == tip
        assert (repo.main / "base.txt").read_text(encoding="utf-8") == dirt


def test_merge_child_inherits_lock_fd_if_helper_is_killed() -> None:
    """winner が transient dirt を持っていても loser は先に lock-busy。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        wrapper = _wrapper(repo.root)
        ready = repo.root / "ready"
        release = repo.root / "release"
        code = (
            "import importlib.util,sys;"
            f"p={str(HELPER_PATH)!r};"
            "s=importlib.util.spec_from_file_location('land_child',p);"
            "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;"
            "s.loader.exec_module(m);"
            f"m._GIT_EXE={str(wrapper)!r};"
            "raise SystemExit(m.main(sys.argv[1:]))"
        )
        argv = _land_cli_argv(request, sys.executable, "-c", code)
        env = dict(os.environ)
        env.update({
            "DEV_WAVE_REAL_GIT": REAL_GIT,
            "DEV_WAVE_WRAPPER_MODE": "hold-dirty",
            "DEV_WAVE_READY": str(ready),
            "DEV_WAVE_RELEASE": str(release),
            "DEV_WAVE_DIRTY_PATH": str(repo.main / "base.txt"),
        })
        process = subprocess.Popen(
            argv,
            cwd=wave,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert ready.exists(), "merge wrapper did not start"
            os.kill(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
            runtime = _FakeLandLockRuntime()
            with runtime.patch():
                result = _land(request)
            assert (result.rc, result.status) == (
                LAND.RC_LOCK_BUSY,
                "lock-busy",
            ), result
            assert runtime.now_s == pytest.approx(LAND._LAND_LOCK_WAIT_SECONDS)
        finally:
            release.touch()
        deadline = time.monotonic() + 5
        while _git(repo.main, "rev-parse", "HEAD") != tip and time.monotonic() < deadline:
            time.sleep(0.02)
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def _merge_without_commit(wave: Path, main_sha: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            REAL_GIT,
            "-C",
            str(wave),
            "merge",
            "--no-ff",
            "--no-commit",
            "--no-edit",
            main_sha,
        ],
        env=_git_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _forward_merge_request(
    repo: _Repo,
    wave: Path,
    *,
    count: int,
) -> tuple[object, tuple[str, ...], tuple[str, ...]]:
    tested_tip = repo.commit(wave, "wave.txt", "accepted wave\n")
    request = repo.request(wave, tip=tested_tip)
    incorporated: list[str] = []
    merge_commits: list[str] = []
    for index in range(1, count + 1):
        main_sha = repo.commit(
            repo.main,
            f"main-{index}.txt",
            f"main advance {index}\n",
        )
        incorporated.append(main_sha)
        _git(wave, "merge", "--no-ff", "--no-edit", main_sha)
        merge_commits.append(_git(wave, "rev-parse", "HEAD"))
    landing_tip = merge_commits[-1]
    return (
        dataclasses.replace(request, landing_wave_tip_sha=landing_tip),
        tuple(incorporated),
        tuple(merge_commits),
    )


@pytest.mark.parametrize("count", (1, 3), ids=("one", "multiple"))
def test_receipt_survives_clean_forward_main_merge_chain(count: int) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, incorporated, merge_commits = _forward_merge_request(
            repo,
            wave,
            count=count,
        )
        receipt_before = request.acceptance_receipt.read_bytes()
        parsed = LAND._parser().parse_args(_land_cli_argv(request)[2:])
        assert parsed.landing_wave_tip_sha == request.landing_wave_tip_sha
        d987_calls = []
        real_d987 = LAND._verify_forward_main_runner_blob

        def spy_d987(repository, tested_main, merges):
            d987_calls.append(
                (
                    tested_main,
                    tuple(merge.incorporated_main_sha for merge in merges),
                )
            )
            return real_d987(repository, tested_main, merges)

        with _patched_land_attr("_verify_forward_main_runner_blob", spy_d987):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert d987_calls == [
            (request.tested_main_sha, incorporated),
            (request.tested_main_sha, incorporated),
        ]
        assert result.tested_tip_sha == request.tested_wave_tip_sha
        assert result.landing_tip_sha == request.landing_wave_tip_sha
        assert result.incorporated_main_shas == incorporated
        assert result.wave_tip == request.landing_wave_tip_sha
        assert _git(repo.main, "rev-parse", "HEAD") == request.landing_wave_tip_sha
        assert request.acceptance_receipt.read_bytes() == receipt_before
        assert tuple(
            _git(wave, "show", "-s", "--format=%P", commit).split()[1]
            for commit in merge_commits
        ) == incorporated


def test_d987_two_stage_chain_rejects_change_only_in_last_main() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_main = repo.base
        tested_tip = repo.commit(wave, "wave.txt", "accepted wave\n")
        request = repo.request(wave, base=tested_main, tip=tested_tip)
        first_main = repo.commit(repo.main, "main-1.txt", "first main\n")
        _git(wave, "merge", "--no-ff", "--no-edit", first_main)
        first_merge = _git(wave, "rev-parse", "HEAD")
        second_main = repo.commit(
            repo.main,
            "tools/run_tests.py",
            "raise SystemExit(27)\n",
        )
        _git(wave, "merge", "--no-ff", "--no-edit", second_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert first_merge != landing_tip
        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == "acceptance-receipt-rejected"
        assert result.incorporated_main_shas == (first_main, second_main)
        assert (result.release_safe, result.retryable_same_request) == (
            True,
            False,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == second_main


def test_d987_two_stage_chain_accepts_final_net_runner_restore() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_main = repo.base
        tested_tip = repo.commit(wave, "wave.txt", "accepted wave\n")
        request = repo.request(wave, base=tested_main, tip=tested_tip)
        first_main = repo.commit(
            repo.main,
            "tools/run_tests.py",
            "raise SystemExit(31)\n",
        )
        _git(wave, "merge", "--no-ff", "--no-edit", first_main)
        _git(
            repo.main,
            "checkout",
            tested_main,
            "--",
            "tools/run_tests.py",
        )
        _git(repo.main, "commit", "-qm", "restore tested-main runner")
        second_main = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--no-ff", "--no-edit", second_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")
        assert _git(
            wave,
            "rev-parse",
            f"{first_main}:tools/run_tests.py",
        ) != _git(wave, "rev-parse", f"{tested_main}:tools/run_tests.py")
        assert _git(
            wave,
            "rev-parse",
            f"{second_main}:tools/run_tests.py",
        ) == _git(wave, "rev-parse", f"{tested_main}:tools/run_tests.py")

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.incorporated_main_shas == (first_main, second_main)
        assert result.acceptance_verdict == "child-green"
        assert _git(repo.main, "rev-parse", "HEAD") == landing_tip


def test_d987_runner_lookup_process_failure_is_retryable() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, incorporated, _merge_commits = _forward_merge_request(
            repo,
            wave,
            count=1,
        )
        real_git = LAND._git

        def fail_final_main_runner_lookup(
            repo_path: Path,
            *args: str,
            **kwargs,
        ):
            if (
                args[:3] == ("ls-tree", "-z", "--full-tree")
                and args[3] == incorporated[-1]
                and args[-2:] == ("--", "tools/run_tests.py")
            ):
                return LAND._GitResult(
                    128,
                    b"",
                    b"synthetic final-main runner lookup failure",
                )
            return real_git(repo_path, *args, **kwargs)

        with _patched_land_attr("_git", fail_final_main_runner_lookup):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == "acceptance-receipt-rejected"
        assert (result.release_safe, result.retryable_same_request) == (
            False,
            True,
        )
        assert _git(repo.main, "rev-parse", "HEAD") == incorporated[-1]


def test_first_forward_main_must_descend_from_tested_main_only_by_origin_gate() -> None:
    """B-057-7: B--A--T と B--S の差替えを起点 gate 固有で拒否する。"""

    with _repo(waves=(("codex", "one"), ("codex", "divergent"))) as repo:
        wave = repo.waves["one"]
        divergent = repo.waves["divergent"]
        tested_main = repo.commit(
            repo.main,
            "accepted-main.txt",
            "accepted main\n",
        )
        _git(wave, "merge", "--ff-only", tested_main)
        tested_tip = repo.commit(wave, "wave.txt", "accepted wave\n")
        request = repo.request(wave, base=tested_main, tip=tested_tip)

        incorporated_main = repo.commit(
            divergent,
            "divergent-main.txt",
            "untested divergent main\n",
        )
        _git(wave, "merge", "--no-ff", "--no-edit", incorporated_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")
        _git(repo.main, "reset", "--hard", incorporated_main)

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == (
            "first incorporated main is not a descendant of tested main"
        )


def test_same_file_disjoint_hunks_forward_merge_matches_default_git_replay() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / "overlap.txt").write_text(
            "main-slot\nshared\nwave-slot\n",
            encoding="utf-8",
        )
        _git(repo.main, "add", "overlap.txt")
        _git(repo.main, "commit", "-qm", "shared overlap base")
        tested_main = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", tested_main)
        (wave / "overlap.txt").write_text(
            "main-slot\nshared\nwave-changed\n",
            encoding="utf-8",
        )
        _git(wave, "commit", "-am", "wave changes later hunk", "-q")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, base=tested_main, tip=tested_tip)
        (repo.main / "overlap.txt").write_text(
            "main-changed\nshared\nwave-slot\n",
            encoding="utf-8",
        )
        _git(repo.main, "commit", "-am", "main changes earlier hunk", "-q")
        incorporated_main = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--no-ff", "--no-edit", incorporated_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")
        merge_base = _git(wave, "merge-base", tested_tip, incorporated_main)
        before_raw = _git(
            wave,
            "diff-tree",
            "-r",
            "--raw",
            "--full-index",
            "--no-abbrev",
            "--no-renames",
            f"{merge_base}^{{tree}}",
            f"{tested_tip}^{{tree}}",
        )
        after_raw = _git(
            wave,
            "diff-tree",
            "-r",
            "--raw",
            "--full-index",
            "--no-abbrev",
            "--no-renames",
            f"{incorporated_main}^{{tree}}",
            f"{landing_tip}^{{tree}}",
        )
        assert before_raw != after_raw

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.incorporated_main_shas == (incorporated_main,)
        assert (repo.main / "overlap.txt").read_text(encoding="utf-8") == (
            "main-changed\nshared\nwave-changed\n"
        )


def test_forward_merge_replay_isolated_mutations_use_default_strategy() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        calls: list[tuple[Path, tuple[str, ...]]] = []
        original = LAND._git

        def spy(path, *args, **kwargs):
            calls.append((Path(path), tuple(args)))
            return original(path, *args, **kwargs)

        with _patched_land_attr("_git", spy):
            result = _land(request)

        assert result.rc == LAND.RC_OK, result
        replay_merge_calls = [
            (path, args)
            for path, args in calls
            if path not in {repo.main, wave} and "merge" in args
        ]
        assert len(replay_merge_calls) == 1
        replay_path, replay_args = replay_merge_calls[0]
        assert repo.root not in (replay_path, *replay_path.parents)
        assert "-s" not in replay_args
        assert "user.name=Izanagi Merge Replay" in replay_args
        assert "user.email=merge-replay@izanagi.invalid" in replay_args
        source_mutations = {
            "init",
            "update-ref",
            "reset",
            "merge",
            "read-tree",
            "add",
            "commit",
        }
        assert all(
            not source_mutations.intersection(args)
            for path, args in calls
            if path == wave
        )


@pytest.mark.parametrize("driver_key", ("driver", "recursive"))
def test_forward_merge_replay_rejects_external_merge_driver_configuration(
    driver_key: str,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        _git(repo.main, "config", f"merge.synthetic.{driver_key}", "true")

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.status == "rejected"
        assert result.reason == "external merge driver configuration is unsupported"


def test_forward_merge_replay_rejects_wave_worktree_merge_driver_configuration(
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        _git(repo.main, "config", "extensions.worktreeConfig", "true")
        _git(
            wave,
            "config",
            "--worktree",
            "merge.synthetic.driver",
            "true",
        )

        result = _land(request)

        assert result.rc == LAND.RC_AUDIT
        assert result.status == "rejected"
        assert result.reason == "external merge driver configuration is unsupported"


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("core.attributesFile", "synthetic-attributes"),
        ("diff.algorithm", "patience"),
        ("diff.renameLimit", "1"),
        ("diff.renames", "false"),
        ("merge.autoStash", "true"),
        ("merge.directoryRenames", "true"),
        ("merge.renameLimit", "1"),
        ("merge.renames", "false"),
        ("merge.renormalize", "true"),
        ("merge.verifySignatures", "true"),
        ("branch.wave/codex-one.mergeOptions", "-Xours"),
    ),
)
def test_forward_merge_replay_rejects_each_merge_affecting_config_key_only_by_gate(
    key: str,
    value: str,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        _git(repo.main, "config", key, value)

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == (
            "merge-affecting configuration is unsupported: " + key.lower()
        )


@pytest.mark.parametrize("origin", ("main-local", "wave-worktree", "global"))
def test_forward_merge_config_gate_reads_every_git_config_origin(
    origin: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        if origin == "main-local":
            _git(repo.main, "config", "--local", "merge.renormalize", "true")
        elif origin == "wave-worktree":
            _git(repo.main, "config", "extensions.worktreeConfig", "true")
            _git(
                wave,
                "config",
                "--worktree",
                "merge.renormalize",
                "true",
            )
        else:
            xdg = repo.root / "xdg"
            config_dir = xdg / "git"
            config_dir.mkdir(parents=True)
            (config_dir / "config").write_text(
                "[merge]\n\trenormalize = true\n",
                encoding="utf-8",
            )
            monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == (
            "merge-affecting configuration is unsupported: merge.renormalize"
        )


def test_conflicting_forward_merge_is_rejected_by_replay_rc_gate() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / "conflict.txt").write_text("same\n", encoding="utf-8")
        _git(repo.main, "add", "conflict.txt")
        _git(repo.main, "commit", "-qm", "conflict base")
        tested_main = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", tested_main)
        (wave / "conflict.txt").write_text("wave\n", encoding="utf-8")
        _git(wave, "commit", "-am", "wave side", "-q")
        tested_tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, base=tested_main, tip=tested_tip)
        (repo.main / "conflict.txt").write_text("main\n", encoding="utf-8")
        _git(repo.main, "commit", "-am", "main side", "-q")
        incorporated_main = _git(repo.main, "rev-parse", "HEAD")

        conflict = _merge_without_commit(wave, incorporated_main)
        assert conflict.returncode != 0, conflict
        (wave / "conflict.txt").write_text("manual resolution\n", encoding="utf-8")
        _git(wave, "add", "conflict.txt")
        _git(wave, "commit", "-qm", "manual conflict resolution")
        landing_tip = _git(wave, "rev-parse", "HEAD")
        assert _git(wave, "show", "-s", "--format=%P", landing_tip).split() == [
            tested_tip,
            incorporated_main,
        ]

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert result.rc == LAND.RC_AUDIT
        assert result.status == "rejected"
        assert "forward main merge replay rejected a non-clean merge" in result.reason


@pytest.mark.parametrize(
    "tamper",
    ("text-byte", "binary-byte", "mode", "symlink", "gitlink"),
)
def test_forward_merge_tree_tampering_is_rejected_only_by_replay_tree_gate(
    tamper: str,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        path = wave / "tamper.bin"
        embedded: Path | None = None
        if tamper == "binary-byte":
            path.write_bytes(b"\x00accepted\n")
            _git(wave, "add", "tamper.bin")
            _git(wave, "commit", "-qm", "accepted binary")
            tested_tip = _git(wave, "rev-parse", "HEAD")
        elif tamper == "symlink":
            path.symlink_to("accepted-target")
            _git(wave, "add", "tamper.bin")
            _git(wave, "commit", "-qm", "accepted symlink")
            tested_tip = _git(wave, "rev-parse", "HEAD")
        elif tamper == "gitlink":
            embedded = path
            embedded.mkdir()
            _git(embedded, "init", "-q", "-b", "main")
            _git(embedded, "config", "user.name", "Gitlink Test")
            _git(embedded, "config", "user.email", "gitlink@example.invalid")
            (embedded / "tracked.txt").write_text("one\n", encoding="utf-8")
            _git(embedded, "add", "tracked.txt")
            _git(embedded, "commit", "-qm", "gitlink one")
            gitlink_before = _git(embedded, "rev-parse", "HEAD")
            _git(
                wave,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{gitlink_before},tamper.bin",
            )
            _git(wave, "commit", "-qm", "accepted gitlink")
            tested_tip = _git(wave, "rev-parse", "HEAD")
        else:
            tested_tip = repo.commit(wave, "tamper.bin", "accepted\n")
        request = repo.request(wave, tip=tested_tip)
        incorporated_main = repo.commit(repo.main, "main-new.txt", "main advance\n")
        clean = _merge_without_commit(wave, incorporated_main)
        assert clean.returncode == 0, clean
        assert _git(wave, "rev-parse", "HEAD") == tested_tip

        if tamper == "text-byte":
            path.write_text("accepted!\n", encoding="utf-8")
            _git(wave, "add", "tamper.bin")
        elif tamper == "binary-byte":
            path.write_bytes(b"\x00acceptEd\n")
            _git(wave, "add", "tamper.bin")
        elif tamper == "mode":
            path.chmod(0o755)
            _git(wave, "add", "tamper.bin")
        elif tamper == "symlink":
            path.unlink()
            path.symlink_to("accepted-target!")
            _git(wave, "add", "tamper.bin")
        else:
            assert embedded is not None
            (embedded / "tracked.txt").write_text("two\n", encoding="utf-8")
            _git(embedded, "commit", "-am", "gitlink two", "-q")
            gitlink_after = _git(embedded, "rev-parse", "HEAD")
            _git(
                wave,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{gitlink_after},tamper.bin",
            )
        _git(wave, "commit", "-qm", f"tamper merge tree: {tamper}")
        landing_tip = _git(wave, "rev-parse", "HEAD")
        assert _git(wave, "show", "-s", "--format=%P", landing_tip).split() == [
            tested_tip,
            incorporated_main,
        ]

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert result.rc == LAND.RC_AUDIT
        assert result.status == "rejected"
        assert "forward main merge replay tree mismatch" in result.reason


def test_non_merge_commit_after_tested_tip_is_rejected_by_topology_gate() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_tip = repo.commit(wave, "wave.txt", "accepted wave\n")
        request = repo.request(wave, tip=tested_tip)
        repo.commit(wave, "ordinary.txt", "not a main merge\n")
        incorporated_main = repo.commit(repo.main, "main-new.txt", "main advance\n")
        _git(wave, "merge", "--no-ff", "--no-edit", incorporated_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")

        result = _land(dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        ))

        assert result.rc == LAND.RC_AUDIT
        assert result.status == "rejected"
        assert "first-parent commit must have exactly two parents" in result.reason


def test_landing_tip_that_does_not_contain_locked_main_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        repo.commit(repo.main, "main-later.txt", "main moved again\n")

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_STALE_MAIN, "stale-main")
        assert result.reason == "landing tip does not contain locked main"


def test_locked_forward_main_ff_gate_has_no_competing_rejection_layer() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(repo, wave, count=1)
        locked_main = repo.commit(repo.main, "main-later.txt", "main moved again\n")
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            try:
                merges = LAND._forward_main_merge_topology(
                    repository,
                    request.tested_main_sha,
                    request.tested_wave_tip_sha,
                    request.landing_wave_tip_sha,
                )
                with pytest.raises(LAND._Reject) as raised:
                    LAND._verify_locked_forward_main(
                        repository,
                        locked_main,
                        request.landing_wave_tip_sha,
                        merges,
                    )
            finally:
                repository.close()
        assert raised.value.rc == LAND.RC_STALE_MAIN
        assert raised.value.reason == "landing tip does not contain locked main"


def test_forward_permission_requires_verified_nonempty_merge_closure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_tip = repo.commit(wave, "wave.txt", "accepted\n")
        request = repo.request(wave, tip=tested_tip)
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            try:
                assert not LAND._main_is_allowed(
                    repository,
                    repo.base,
                    repo.base,
                    tested_tip,
                    request.audited_commits,
                    landing_tip="1" * 40,
                    forward_main_merges=(),
                )
            finally:
                repository.close()


def test_forward_main_merge_chain_above_json_budget_cap_is_rejected() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, _, _ = _forward_merge_request(
            repo,
            wave,
            count=LAND._MAX_FORWARD_MAIN_MERGES + 1,
        )

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == (
            "forward main merge chain exceeds the accepted maximum "
            f"of {LAND._MAX_FORWARD_MAIN_MERGES}"
        )


def test_forward_main_merge_chain_at_json_budget_cap_is_accepted() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, incorporated, _ = _forward_merge_request(
            repo,
            wave,
            count=LAND._MAX_FORWARD_MAIN_MERGES,
        )
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            try:
                merges = LAND._forward_main_merge_topology(
                    repository,
                    request.tested_main_sha,
                    request.tested_wave_tip_sha,
                    request.landing_wave_tip_sha,
                )
            finally:
                repository.close()

        assert tuple(merge.incorporated_main_sha for merge in merges) == incorporated


def test_omitted_landing_tip_preserves_legacy_tested_tip_target() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_tip = repo.commit(wave, "legacy.txt", "legacy target\n")
        request = repo.request(wave, tip=tested_tip)
        assert request.landing_wave_tip_sha is None
        _git(repo.main, "config", "merge.synthetic.driver", "false")

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.tested_tip_sha == tested_tip
        assert result.landing_tip_sha == tested_tip
        assert result.incorporated_main_shas == ()


def test_forward_merge_already_landed_branches_before_normal_preland_gate() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        request, incorporated, _ = _forward_merge_request(repo, wave, count=1)
        first = _land(request)
        assert first.rc == LAND.RC_OK

        second = _land(request)

        assert (second.rc, second.status) == (LAND.RC_OK, "already-landed"), second
        assert second.incorporated_main_shas == incorporated
        assert second.main_after == request.landing_wave_tip_sha


def test_forward_merge_fold_recovery_uses_landing_tip_state_boundary() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        (repo.main / ".git" / "info" / "exclude").write_text(
            ".codex/worktrees/\n",
            encoding="utf-8",
        )
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tested_tip = _git(wave, "rev-parse", "HEAD")
        request = repo.request(wave, tip=tested_tip)
        incorporated_main = repo.commit(repo.main, "main-new.txt", "main advance\n")
        _git(wave, "merge", "--no-ff", "--no-edit", incorporated_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")
        request = dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        )

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            (repo_path / "docs/spool/FOLDED.md").write_text(
                "# receipts\n- forward-shape-b\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            ),
            apply,
        )
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            first = _land(request)
        assert (first.rc, first.status) == (LAND.RC_OK, "landed"), first
        fold_commit = first.main_after
        assert fold_commit is not None
        assert _git(repo.main, "rev-parse", f"{fold_commit}^") == landing_tip
        assert module._plan.origin.tested_tip == landing_tip
        assert module._plan.origin.trusted_main_cutoff == incorporated_main

        module._plan = module._plan.with_phase("applied")
        module._active = True
        module._apply = lambda *_args: (_ for _ in ()).throw(
            AssertionError("forward shape B must not reapply")
        )
        module.events.clear()
        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr(
                "_audit_provenance_history",
                lambda *_args: (_ for _ in ()).throw(
                    AssertionError("active forward fold must not rerun provenance")
                ),
            ),
        ):
            recovered = _land(request)

        assert (recovered.rc, recovered.status) == (LAND.RC_OK, "landed"), recovered
        assert recovered.main_after == fold_commit
        assert recovered.incorporated_main_shas == (incorporated_main,)
        assert module.events == ["verify", "mark", "finalize"]


def test_active_forward_fold_d987_rejection_retains_lease_and_main() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tested_main = repo.base
        tested_tip = repo.commit(wave, "wave.txt", "accepted wave\n")
        request = repo.request(wave, base=tested_main, tip=tested_tip)
        incorporated_main = repo.commit(
            repo.main,
            "tools/run_tests.py",
            "raise SystemExit(41)\n",
        )
        _git(wave, "merge", "--no-ff", "--no-edit", incorporated_main)
        landing_tip = _git(wave, "rev-parse", "HEAD")
        request = dataclasses.replace(
            request,
            landing_wave_tip_sha=landing_tip,
        )
        assert _git(
            wave,
            "rev-parse",
            f"{incorporated_main}:tools/run_tests.py",
        ) != _git(
            wave,
            "rev-parse",
            f"{tested_main}:tools/run_tests.py",
        )
        module = _FakeFoldModule(
            _FakeFoldPlan("docs/spool/worklog/synthetic-active.md"),
            lambda *_args: (_ for _ in ()).throw(
                AssertionError("D987 rejection must not resume the fold")
            ),
            active=True,
        )
        provenance_calls = []
        d987_calls = []
        main_before = _git(repo.main, "rev-parse", "HEAD")
        assert main_before == incorporated_main
        real_d987 = LAND._verify_forward_main_runner_blob

        def forbidden_provenance(*args):
            provenance_calls.append(args)
            raise AssertionError("active-fold D987 rejection must precede provenance")

        def spy_d987(repository, observed_tested_main, merges):
            d987_calls.append((
                observed_tested_main,
                tuple(merge.incorporated_main_sha for merge in merges),
            ))
            return real_d987(repository, observed_tested_main, merges)

        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_audit_provenance_history", forbidden_provenance),
            _patched_land_attr("_verify_forward_main_runner_blob", spy_d987),
        ):
            result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_AUDIT, "rejected")
        assert result.reason == "acceptance-receipt-rejected"
        assert result.incorporated_main_shas == (incorporated_main,)
        assert (result.release_safe, result.retryable_same_request) == (
            False,
            False,
        )
        assert provenance_calls == []
        assert d987_calls == [(tested_main, (incorporated_main,))]
        assert module.events == []
        assert _git(repo.main, "rev-parse", "HEAD") == main_before


def test_same_base_two_wave_winner_stale_resync_loser_land_e2e() -> None:
    """M1/M13: winner→stale loser→merge/reaccept→loser land の一続きの E2E。"""
    with _repo(waves=(("codex", "winner"), ("claude", "loser"))) as repo:
        winner = repo.waves["winner"]
        loser = repo.waves["loser"]
        winner_tip = repo.commit(winner, "winner.txt", "winner\n")
        loser_tip = repo.commit(loser, "loser.txt", "loser\n")
        handoff = _handoff(repo, state="中断")
        foreign = winner / ".git"
        watched_before = {handoff: _snapshot(handoff), foreign: _snapshot(foreign)}

        first = _land(repo.request(winner, tip=winner_tip))
        assert (first.rc, first.status) == (0, "landed"), first
        stale = _land(repo.request(loser, tip=loser_tip))
        assert (stale.rc, stale.status) == (LAND.RC_STALE_MAIN, "stale-main"), stale
        assert _git(repo.main, "rev-parse", "HEAD") == winner_tip

        _git(loser, "merge", "--no-edit", "main")
        resynced_tip = _git(loser, "rev-parse", "HEAD")
        resynced_tree = _git(loser, "rev-parse", f"{resynced_tip}^{{tree}}")
        acceptance = _run_synthetic_acceptance(
            loser,
            tested_main=winner_tip,
            tested_tip=resynced_tip,
            tested_tree=resynced_tree,
        )
        assert acceptance["tested_tree"] == resynced_tree
        audited = repo.audited(winner_tip, resynced_tip, loser)
        assert audited == tuple(
            _git(
                loser, "rev-list", "--reverse",
                f"{winner_tip}..{resynced_tip}",
            ).splitlines()
        )
        assert winner_tip not in audited
        assert loser_tip in audited and resynced_tip in audited
        second = _land(
            repo.request(
                loser,
                base=acceptance["tested_main"],
                tip=acceptance["tested_tip"],
                audited=audited,
            )
        )
        assert (second.rc, second.status) == (0, "landed"), second
        assert _git(repo.main, "rev-parse", "HEAD") == resynced_tip
        assert (repo.main / "winner.txt").read_text() == "winner\n"
        assert (repo.main / "loser.txt").read_text() == "loser\n"
        assert {path: _snapshot(path) for path in watched_before} == watched_before

        foreign_untracked = repo.main / "unknown-after.txt"
        foreign_untracked.write_text("foreign session\n", encoding="utf-8")
        foreign_untracked_before = _snapshot(foreign_untracked)
        already = _land(
            repo.request(
                loser,
                base=winner_tip,
                tip=resynced_tip,
                audited=audited,
            )
        )
        assert (already.rc, already.status) == (LAND.RC_OK, "already-landed"), already
        assert _git(repo.main, "rev-parse", "HEAD") == resynced_tip
        assert _snapshot(foreign_untracked) == foreign_untracked_before
        assert {path: _snapshot(path) for path in watched_before} == watched_before


def test_main_fold_resync_reaches_no_fold_and_declared_fold_consumers() -> None:
    """main-side fold を merge した wave が land の両 cutoff 配線を通る。"""

    for declared_fold in (False, True):
        with _repo(waves=(("codex", "winner"), ("claude", "loser"))) as repo:
            winner = repo.waves["winner"]
            loser = repo.waves["loser"]
            main_fold = _land_main_fold_for_resync(repo, winner)

            if declared_fold:
                relative, _fragment, _content = _fake_pending_fragment(
                    repo, loser, wave_slug="resync-loser",
                )
            else:
                repo.commit(loser, "loser.txt", "loser\n")
                relative = None
            _git(loser, "merge", "--no-edit", "main")
            resynced_tip = _git(loser, "rev-parse", "HEAD")
            audited = repo.audited(main_fold, resynced_tip, loser)
            assert main_fold not in audited
            assert audited[-1] == resynced_tip

            if relative is None:
                result = _land(
                    repo.request(
                        loser,
                        base=main_fold,
                        tip=resynced_tip,
                        audited=audited,
                    )
                )
            else:
                def apply(repo_path: Path, _plan) -> None:
                    (repo_path / relative).unlink()
                    folded = repo_path / "docs/spool/FOLDED.md"
                    folded.write_text(
                        folded.read_text(encoding="utf-8") + "- loser fold\n",
                        encoding="utf-8",
                    )

                module = _FakeFoldModule(
                    _FakeFoldPlan(
                        relative,
                        targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
                    ),
                    apply,
                )
                with (
                    _patched_land_attr("_load_spool_fold", lambda: module),
                    _patched_land_attr("_preflight_fold_message", lambda *_args: None),
                ):
                    result = _land(
                        repo.request(
                            loser,
                            base=main_fold,
                            tip=resynced_tip,
                            audited=audited,
                        )
                    )

            assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
            assert _git(repo.main, "merge-base", "--is-ancestor", main_fold, "HEAD") == ""


def test_cli_emits_json_and_uses_only_sha_target_ff() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        argv = _land_cli_argv(request)
        completed = subprocess.run(
            argv,
            cwd=wave,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["status"] == "landed"
        assert payload["main_after"] == tip
        assert _git(repo.main, "rev-parse", "HEAD") == tip


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_exploration_external_root_keeps_wave_clean() -> None:
    """F98 正例: fake evaluator の exploration campaign は wave 外だけを汚す。"""
    with _campaign_import_scope():
        from types import SimpleNamespace
        from orchestrator.campaign import env_contract, layout as layout_module, loop, pipeline, wal
        from orchestrator.campaign.build_admission import GeneratorId, build_run_context
        from orchestrator.campaign.model import (
            CampaignConfig, Genome, STAGE_ABORT, STAGE_BUILD_START,
        )
        from orchestrator.campaign.pipeline import EvalResult, PerfConfig

    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    sentinel = object()
    saved_env = os.environ.get(env_name, sentinel)
    saved_repo_output_root = layout_module.repo_output_root
    saved_evaluate = loop.evaluate
    saved_source_digest = loop.source_digest
    fake_variant = {}
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        with _repo() as repo:
            wave = repo.waves["one"]
            external = repo.root / "external-output"
            external.mkdir()
            os.environ[env_name] = str(external)
            layout_module.repo_output_root = lambda: str(wave / "output")
            loop.source_digest = SimpleNamespace(
                resolve_evidence=lambda *_args, **_kwargs: SimpleNamespace(
                    src_token="stock",
                ),
            )

            def fake_evaluate(
                genome, layout, env_tag, _commit, _perf, _clocks, **kwargs,
            ):
                variant = pipeline.variant_id(genome, kwargs["src_token"])
                attempt_id = "f98-valid-prebuild-abort"
                fake_variant["value"] = variant
                wal.log(
                    layout, variant, STAGE_BUILD_START, env_tag,
                    {
                        "genome": genome.canonical(),
                        "build_attempt_id": attempt_id,
                    },
                )
                wal.log(
                    layout, variant, STAGE_ABORT, env_tag,
                    {
                        "reason": "f98-fixture-prebuild-abort",
                        "build_attempt_id": attempt_id,
                    },
                )
                return EvalResult(
                    genome=genome, variant=variant, certified=False,
                    aborted=True,
                )

            loop.evaluate = fake_evaluate
            cfg = CampaignConfig(
                spec_slug="f98", search_tag="external",
                spec_content="f98 external-root acceptance",
                ccbench_commit="deadbeef",
            )
            context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
            authorization = env_contract.authorize("linux-baremetal")
            contract = authorization.contract
            summary = loop.run_campaign(
                cfg, [Genome("silo", {"BACK_OFF": 1})],
                PerfConfig(records=1, threads=1), contract.env_tag,
                contract.clocks_per_us, numactl=contract.numactl,
                do_bench=False, log=lambda *_args: None,
                authorization_contract=authorization,
                build_context=context, declared_use_class="exploration",
            )
            campaign_root = Path(summary.layout_root)
            assert campaign_root.is_relative_to(external)
            assert (external / "exploration" / "namespace.json").read_bytes() == (
                b'{"namespace":"exploration"}\n'
            )
            assert (campaign_root / "campaign.lock").is_file()
            assert (campaign_root / "runs" / "wal.jsonl").is_file()
            replayed = wal.replay(
                layout_module.ExplorationCampaignLayout(root=str(campaign_root)),
                admission_policy=context.policy,
            )
            assert replayed[fake_variant["value"]].aborted
            assert _git(wave, "status", "--porcelain=v1", "--untracked-files=all") == ""

            request = repo.request(wave)
            with _cwd(wave):
                repository = LAND._verify_repository(request)
                try:
                    LAND._verify_wave_clean(repository)
                finally:
                    repository.close()
    finally:
        loop.evaluate = saved_evaluate
        loop.source_digest = saved_source_digest
        layout_module.repo_output_root = saved_repo_output_root
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_exploration_default_root_stops_before_wave_dirt() -> None:
    """M6/F98 負例: wave-local default は ensure gate で作成前に拒否する。"""
    with _campaign_import_scope():
        from orchestrator.campaign import layout as layout_module

    env_name = layout_module._EXPLORATION_OUTPUT_ROOT_ENV
    sentinel = object()
    saved_env = os.environ.get(env_name, sentinel)
    saved_repo_output_root = layout_module.repo_output_root
    layout_module._reset_exploration_output_root_pin_for_tests()
    try:
        for family in ("codex", "claude"):
            with _repo(waves=((family, "one"),)) as repo:
                wave = repo.waves["one"]
                local_output = wave / "output"
                os.environ.pop(env_name, None)
                layout_module.repo_output_root = lambda: str(local_output)
                campaign = layout_module.exploration_campaign_layout("f98-default")
                assert campaign.root == str(
                    local_output / "exploration" / "campaigns" / "f98-default"
                )
                try:
                    campaign.ensure()
                    assert False, "wave-local exploration root を拒否すべき"
                except ValueError as exc:
                    message = str(exc)
                    assert "worktree container" in message
                    assert env_name in message
                    assert "絶対 path" in message
                    assert "job 専用" in message
                    assert "base は exploration/ 自体ではない" in message
                assert not local_output.exists()
                assert _git(
                    wave, "status", "--porcelain=v1", "--untracked-files=all",
                ) == ""
    finally:
        layout_module.repo_output_root = saved_repo_output_root
        layout_module._reset_exploration_output_root_pin_for_tests()
        if saved_env is sentinel:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = saved_env


def test_verify_wave_clean_rejects_plain_untracked_file_as_dirt() -> None:
    """RC_DIRT 対照は campaign tree に依存しない plain untracked file とする。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        (wave / "plain-untracked.txt").write_text("dirt\n", encoding="utf-8")
        with _cwd(wave):
            repository = LAND._verify_repository(repo.request(wave))
            try:
                try:
                    LAND._verify_wave_clean(repository)
                    assert False, "plain untracked file を RC_DIRT で拒否すべき"
                except LAND._Reject as exc:
                    assert exc.rc == LAND.RC_DIRT
                    assert exc.reason == "wave worktree must be completely clean"
            finally:
                repository.close()


def test_land_result_release_contract_defaults_fail_closed_and_is_in_json() -> None:
    result = LAND.LandResult(999, "synthetic", "unknown return site")

    assert (result.release_safe, result.retryable_same_request) == (False, False)
    assert dataclasses.replace(
        result,
        release_safe=True,
        retryable_same_request=True,
    ) == result
    payload = result.as_json()
    assert payload["acceptance_flake_nodeids"] is None
    assert payload["tested_tip_sha"] is None
    assert payload["landing_tip_sha"] is None
    assert payload["incorporated_main_shas"] == []
    assert payload["release_safe"] is False
    assert payload["retryable_same_request"] is False
    assert "lease_release" not in payload


def test_main_releases_owned_lease_after_success_and_preserves_core_result() -> None:
    """P1 / M0: 実 land 成功は stdout 確定後に owned lease を解放する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)

        rc, payload, raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_OK
        assert payload["status"] == "landed"
        assert payload["main_after"] == tip
        assert payload["release_safe"] is True
        assert payload["retryable_same_request"] is False
        assert "lease_release" not in payload
        assert raw.endswith("\n")
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=released reason=none\n"
        )
        assert not lease_path.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == tip


def test_main_requires_release_safe_and_not_retryable_same_request() -> None:
    """M2: 2 bool が同時に True なら release_safe 単独では解放しない。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        calls: list[object] = []
        result = LAND.LandResult(
            LAND.RC_LOCK_BUSY,
            "synthetic",
            "both predicates true",
            release_safe=True,
            retryable_same_request=True,
        )

        def forbidden_release(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("retryable result must retain the lease")

        with (
            _patched_land_attr("land", lambda _request: result),
            _patched_window_release(forbidden_release),
        ):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_LOCK_BUSY
        assert calls == []
        assert payload["release_safe"] is True
        assert payload["retryable_same_request"] is True
        assert errors == (
            "lease_renew state=free reason=none\n"
            "lease_release state=retained reason=land-result-not-release-safe\n"
        )


def test_main_unexpected_exception_or_interrupt_never_releases() -> None:
    """M3: mutation outcome 不明の例外・中断は JSON 化も release もしない。"""

    for failure in (RuntimeError("synthetic"), KeyboardInterrupt()):
        with _repo() as repo:
            request = repo.request(repo.waves["one"])
            lease_dir = repo.root / "lease"
            lease_dir.mkdir()
            output = io.StringIO()
            errors = io.StringIO()
            calls: list[object] = []
            renew_calls: list[object] = []

            def fail_land(_request, failure=failure):
                raise failure

            def forbidden_release(*args, **kwargs):
                calls.append((args, kwargs))
                raise AssertionError("unexpected failures must not release")

            def observed_renew(lease_path, wave):
                renew_calls.append((lease_path, wave))
                return {
                    "state": "free",
                    "source": {"status": "ok", "reason": None},
                }

            try:
                with (
                    _patched_land_attr("land", fail_land),
                    _patched_window_release(forbidden_release),
                    _patched_window_renew(observed_renew),
                    _cwd(request.wave_worktree),
                    _lease_dir_environment(lease_dir),
                    contextlib.redirect_stdout(output),
                    contextlib.redirect_stderr(errors),
                ):
                    LAND.main(_land_cli_argv(request)[2:])
                assert False, "land failure must propagate"
            except BaseException as exc:
                assert exc is failure
            assert calls == []
            assert renew_calls == [(lease_dir, request.acceptance_wave)]
            assert output.getvalue() == ""
            assert errors.getvalue() == ""


def test_provenance_checker_violation_rc_is_release_safe_and_releases() -> None:
    """M8: checker の違反 rc=1 は rc=29 の release-safe 側。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)

        def rejected_checker(_checker, _repository, _env):
            return subprocess.CompletedProcess([], 1, b"", b"")

        with _patched_land_attr("_run_provenance_checker", rejected_checker):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_PROVENANCE
        assert payload["status"] == "rejected"
        assert payload["release_safe"] is True
        assert payload["retryable_same_request"] is False
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=released reason=none\n"
        )
        assert not lease_path.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def _assert_non_authoritative_provenance_rc_retains(returncode: int) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()

        def incomplete_checker(_checker, _repository, _env):
            return subprocess.CompletedProcess([], returncode, b"", b"")

        with _patched_land_attr("_run_provenance_checker", incomplete_checker):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_PROVENANCE
        assert payload["status"] == "rejected"
        assert payload["release_safe"] is False
        assert payload["retryable_same_request"] is True
        assert "did not complete authoritatively" in payload["reason"]
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=retained reason=land-result-not-release-safe\n"
        )
        assert lease_path.read_bytes() == before
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_provenance_checker_infrastructure_rc_is_retryable_and_retains() -> None:
    """F1: checker の infrastructure rc=16 は違反ではなく保持する。"""

    _assert_non_authoritative_provenance_rc_retains(16)


def test_provenance_checker_signal_returncode_is_retryable_and_retains() -> None:
    """F1: signal 終了の負 returncode は違反ではなく保持する。"""

    for returncode in (-9, -15):
        _assert_non_authoritative_provenance_rc_retains(returncode)


def test_provenance_checker_timeout_is_retryable_and_retains() -> None:
    """M7: timeout を決定的 checker 非 0 と同一視せず lease を保持する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()

        def timed_out_checker(_checker, _repository, _env):
            raise subprocess.TimeoutExpired(["provenance-checker"], 480)

        with _patched_land_attr("_run_provenance_checker", timed_out_checker):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_PROVENANCE
        assert payload["status"] == "rejected"
        assert payload["release_safe"] is False
        assert payload["retryable_same_request"] is True
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=retained reason=land-result-not-release-safe\n"
        )
        assert lease_path.read_bytes() == before
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_internal_fold_planning_interrupt_is_never_release_safe() -> None:
    """M3: land 内部 catch の KeyboardInterrupt は lease を解放しない。"""

    class InterruptedPlanModule(_FakeFoldModule):
        def plan_fold(self, repo: Path, *, fold_date: str, origin):
            raise KeyboardInterrupt("synthetic internal interrupt")

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()
        module = InterruptedPlanModule(
            _FakeFoldPlan("docs/spool/worklog/missing.md"),
            lambda *_args: None,
        )

        with _patched_land_attr("_load_spool_fold", lambda: module):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_FOLD_FAILED
        assert payload["status"] == "fold-failed"
        assert payload["release_safe"] is False
        assert payload["retryable_same_request"] is True
        assert "KeyboardInterrupt" in payload["reason"]
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=retained reason=land-result-not-release-safe\n"
        )
        assert lease_path.read_bytes() == before
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_successful_fold_rollback_remains_held_fail_closed() -> None:
    """F3: ref だけの再検証では不十分なので rollback 成功後も保持する。"""

    with _rollback_fold_fixture() as fixture:
        (
            repo,
            wave,
            tip,
            index_tree,
            _restore_path,
            snapshots,
            _fold,
            plan,
            state_path,
            _state_bytes,
        ) = fixture
        module = _FakeFoldModule(
            plan,
            lambda *_args: (_ for _ in ()).throw(
                RuntimeError("synthetic apply failure")
            ),
        )
        successful_land = LAND.LandResult(
            LAND.RC_OK,
            "landed",
            "synthetic successful fast-forward",
            repo.base,
            tip,
            tip,
        )
        with _cwd(wave):
            repository = LAND._verify_repository(repo.request(wave, tip=tip))
            try:
                result = LAND._fold_main_locked(
                    repository,
                    successful_land,
                    fold=module,
                    plan=plan,
                    trusted_main_cutoff_sha=repo.base,
                    tested_tip=tip,
                    landed_commits=(tip,),
                    wave_ref=_git(wave, "symbolic-ref", "HEAD"),
                    rollback_ref=repo.base,
                    snapshots=snapshots,
                    index_tree=index_tree,
                    state_path=state_path,
                )
            finally:
                repository.close()

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_FAILED,
            "fold-failed",
        )
        assert (result.release_safe, result.retryable_same_request) == (False, False)
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_receipt_read_io_failure_is_retryable_and_retains() -> None:
    """F4: receipt open/read/stat の一時 I/O failure は同一 request で再試行する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()

        def fail_regular_read(*_args, **_kwargs):
            raise OSError("synthetic receipt read failure")

        with _patched_land_attr("_read_regular_at", fail_regular_read):
            try:
                LAND._read_acceptance_receipt(request.acceptance_receipt)
                assert False, "receipt I/O failure was accepted"
            except LAND._Reject as exc:
                assert exc.retryable_same_request is True

        transient = LAND._acceptance_rejected(retryable_same_request=True)

        def fail_receipt(_path):
            raise transient

        with _patched_land_attr("_read_acceptance_receipt", fail_receipt):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_AUDIT
        assert payload["release_safe"] is False
        assert payload["retryable_same_request"] is True
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=retained reason=land-result-not-release-safe\n"
        )
        assert lease_path.read_bytes() == before


def test_locked_status_git_io_failure_is_retryable_and_retains() -> None:
    """F4: locked preflight の status 実行失敗は structural dirt と分離する。"""

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        request = repo.request(wave, tip=tip)
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()
        real_git = LAND._git

        def fail_main_status(repo_path: Path, *args: str, **kwargs):
            if repo_path == repo.main and args[:2] == (
                "status",
                "--porcelain=v1",
            ):
                return LAND._GitResult(128, b"", b"synthetic status I/O failure")
            return real_git(repo_path, *args, **kwargs)

        with _patched_land_attr("_git", fail_main_status):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_DIRT
        assert payload["release_safe"] is True
        assert payload["retryable_same_request"] is True
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=retained reason=land-result-not-release-safe\n"
        )
        assert lease_path.read_bytes() == before
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_main_binds_release_to_wave_main_and_flushed_core_json() -> None:
    """M9/M13/M15: slug・tested_main・stdout flush・core field を同時に固定。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        output = _FlushBuffer()
        digest = hashlib.sha256(request.acceptance_receipt.read_bytes()).hexdigest()
        result = LAND.LandResult(
            LAND.RC_OK,
            "already-landed",
            "synthetic quiescent result",
            main_before=request.tested_main_sha,
            main_after=request.tested_wave_tip_sha,
            wave_tip=request.tested_wave_tip_sha,
            acceptance_receipt_sha256=digest,
            release_safe=True,
        )

        def observed_release(lease_path, wave, expected_main_sha=None):
            assert output.was_flushed is True
            printed = json.loads(output.getvalue())
            assert printed["release_safe"] is True
            assert printed["retryable_same_request"] is False
            assert "lease_release" not in printed
            assert lease_path == lease_dir
            assert wave == request.acceptance_wave
            assert expected_main_sha == request.tested_main_sha
            return {
                "state": "released",
                "source": {"status": "ok", "reason": None},
            }

        with (
            _patched_land_attr("land", lambda _request: result),
            _patched_window_release(observed_release),
        ):
            rc, payload, _raw, errors = _invoke_land_main(
                request,
                lease_dir,
                stdout=output,
            )

        assert rc == LAND.RC_OK
        assert payload["release_safe"] is True
        assert payload["retryable_same_request"] is False
        assert errors == (
            "lease_renew state=free reason=none\n"
            "lease_release state=released reason=none\n"
        )


def test_main_empty_lease_dir_reports_required_for_renew_and_release() -> None:
    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        result = LAND.LandResult(
            LAND.RC_OK,
            "already-landed",
            "synthetic empty lease directory result",
            release_safe=True,
        )
        output = _FlushBuffer()
        errors = io.StringIO()
        renew_calls: list[object] = []

        def forbidden_renew(*args, **kwargs):
            renew_calls.append((args, kwargs))
            raise AssertionError("empty lease directory must not call renew")

        previous = os.environ.get("IZANAGI_WAVE_LEASE_DIR")
        os.environ["IZANAGI_WAVE_LEASE_DIR"] = ""
        try:
            with (
                _patched_land_attr("land", lambda _request: result),
                _patched_window_renew(forbidden_renew),
                _cwd(request.wave_worktree),
                contextlib.redirect_stdout(output),
                contextlib.redirect_stderr(errors),
            ):
                rc = LAND.main(_land_cli_argv(request)[2:])
        finally:
            if previous is None:
                os.environ.pop("IZANAGI_WAVE_LEASE_DIR", None)
            else:
                os.environ["IZANAGI_WAVE_LEASE_DIR"] = previous

        assert rc == LAND.RC_OK
        assert json.loads(output.getvalue()) == result.as_json()
        assert renew_calls == []
        assert errors.getvalue().splitlines() == [
            "lease_renew state=unavailable reason=lease-dir-required",
            "lease_release state=unavailable reason=lease-dir-required",
        ]


def test_main_renew_exception_does_not_change_land_result() -> None:
    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        result = LAND.LandResult(
            LAND.RC_LOCK_BUSY,
            "synthetic",
            "renew failure must not alter land result",
            release_safe=False,
            retryable_same_request=True,
        )
        land_calls: list[object] = []

        def observed_land(land_request):
            land_calls.append(land_request)
            return result

        def failed_renew(*_args, **_kwargs):
            raise RuntimeError("synthetic renew failure")

        with (
            _patched_land_attr("land", observed_land),
            _patched_window_renew(failed_renew),
        ):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_LOCK_BUSY
        assert payload == result.as_json()
        assert land_calls == [request]
        assert errors.splitlines() == [
            "lease_renew state=unavailable reason=renew-internal-error",
            "lease_release state=retained reason=land-result-not-release-safe",
        ]


def test_main_receipt_digest_change_blocks_release() -> None:
    """M12: land が digest を返さない経路は snapshot 後の receipt 差替えを拒否。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()
        calls: list[object] = []

        def land_after_replacement(_request):
            payload = _receipt_payload(request.acceptance_receipt)
            payload["log_sha256"] = "f" * 64
            _write_receipt(request.acceptance_receipt, payload)
            return LAND.LandResult(
                LAND.RC_PROVENANCE,
                "rejected",
                "synthetic pre-receipt result",
                release_safe=True,
            )

        def forbidden_release(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("changed receipt must not authorize release")

        with (
            _patched_land_attr("land", land_after_replacement),
            _patched_window_release(forbidden_release),
        ):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_PROVENANCE
        assert payload["release_safe"] is True
        assert calls == []
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=unavailable reason=receipt-digest-changed\n"
        )
        assert lease_path.read_bytes() == before


def test_main_verified_receipt_digest_mismatch_blocks_release() -> None:
    """M12: 完全検証 digest と事前 authority snapshot の不一致も拒否する。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir, lease_path = _claim_acceptance_lease(repo, request)
        before = lease_path.read_bytes()
        calls: list[object] = []
        result = LAND.LandResult(
            LAND.RC_OK,
            "already-landed",
            "synthetic verified result from different receipt bytes",
            main_before=request.tested_main_sha,
            main_after=request.tested_wave_tip_sha,
            wave_tip=request.tested_wave_tip_sha,
            acceptance_receipt_sha256="f" * 64,
            release_safe=True,
        )

        def forbidden_release(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("mismatched verified digest must not authorize release")

        with (
            _patched_land_attr("land", lambda _request: result),
            _patched_window_release(forbidden_release),
        ):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_OK
        assert payload["release_safe"] is True
        assert calls == []
        assert errors == (
            "lease_renew state=held-self reason=none\n"
            "lease_release state=unavailable reason=receipt-digest-mismatch\n"
        )
        assert lease_path.read_bytes() == before


def test_compact_core_json_preserves_legacy_64k_message_boundary() -> None:
    """flake field で21 bytes、今回の3 field で73 bytes、最大 nodeid が縮む。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        legacy_nodeid = "x" * 65002
        boundary_nodeid = "x" * 64981
        result = LAND.LandResult(
            LAND.RC_OK,
            "landed",
            "boundary",
            main_before="a" * 40,
            main_after="b" * 40,
            wave_tip="b" * 40,
            acceptance_receipt_sha256="c" * 64,
            acceptance_verdict="non-attributable-only",
            acceptance_red_nodeids=(boundary_nodeid,),
            acceptance_flake_nodeids=(),
        )
        payload = result.as_json()
        legacy_payload = dataclasses.replace(
            result,
            acceptance_red_nodeids=(legacy_nodeid,),
        ).as_json()
        legacy_without_flake_payload = {
            key: value
            for key, value in legacy_payload.items()
            if key != "acceptance_flake_nodeids"
        }
        pre_forward_fields_payload = {
            key: value
            for key, value in payload.items()
            if key not in {
                "tested_tip_sha",
                "landing_tip_sha",
                "incorporated_main_shas",
            }
        }
        legacy_without_flake_bytes = json.dumps(
            legacy_without_flake_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        pre_forward_fields_bytes = json.dumps(
            pre_forward_fields_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        legacy_bytes = json.dumps(
            legacy_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        compact_bytes = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        assert len(legacy_nodeid) - len(boundary_nodeid) == 21
        assert len(b',"acceptance_flake_nodeids":[]') == 30
        assert len(legacy_bytes) - len(legacy_without_flake_bytes) == 30
        assert len(legacy_bytes) - len(compact_bytes) == 21
        assert len(compact_bytes) - len(pre_forward_fields_bytes) == 73
        assert len(legacy_bytes) == 65556
        assert len(compact_bytes) == 65535
        assert len(legacy_bytes) + 1 > LAND._wave_land_window._MAX_LAND_JSON_BYTES
        assert len(compact_bytes) + 1 == LAND._wave_land_window._MAX_LAND_JSON_BYTES

        with _patched_land_attr("land", lambda _request: result):
            rc, emitted, raw, _errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_OK
        assert emitted == payload
        assert raw.encode("utf-8") == compact_bytes + b"\n"
        land_json = repo.root / "land-result-boundary.json"
        land_json.write_bytes(raw.encode("utf-8"))
        message = LAND._wave_land_window.message(
            request.acceptance_wave,
            land_json,
        )
        assert message.startswith("[dev-wave] landed main=" + "b" * 40)


def test_max_forward_main_merge_chain_fits_receipt_derived_64k_json_budget() -> None:
    """64 KiB 受領証の最大 nodeid と上限 chain が land JSON に同居できる。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        receipt = json.loads(request.acceptance_receipt.read_text(encoding="ascii"))
        receipt.update({
            "child_rc": 1,
            "verdict": "non-attributable-only",
            "checker_rc": 0,
            "checker_status": "non-attributable-only",
            "checker_blob_sha": "d" * 40,
            "checker_receipt_sha256": "e" * 64,
            "red_nodeids": [""],
        })
        receipt_bytes = json.dumps(
            receipt,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        max_nodeid_bytes = (
            LAND._MAX_ACCEPTANCE_RECEIPT_BYTES - len(receipt_bytes) - 1
        )
        max_nodeid = "x" * max_nodeid_bytes
        receipt["red_nodeids"] = [max_nodeid]
        receipt_bytes = json.dumps(
            receipt,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        assert len(receipt_bytes) + 1 == LAND._MAX_ACCEPTANCE_RECEIPT_BYTES

        sha = "f" * 40
        result = LAND.LandResult(
            LAND.RC_OK,
            "already-landed",
            "verified active fold commit finalized without reapplying or recommitting",
            main_before=sha,
            main_after=sha,
            wave_tip=sha,
            fold_commit_sha=sha,
            acceptance_receipt_sha256="a" * 64,
            acceptance_verdict="non-attributable-only",
            acceptance_red_nodeids=(max_nodeid,),
            acceptance_flake_nodeids=(),
            tested_tip_sha=sha,
            landing_tip_sha=sha,
            incorporated_main_shas=tuple(
                f"{index:040x}"
                for index in range(LAND._MAX_FORWARD_MAIN_MERGES)
            ),
            release_safe=True,
        )
        land_bytes = json.dumps(
            result.as_json(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        assert len(result.incorporated_main_shas) == LAND._MAX_FORWARD_MAIN_MERGES
        assert len(land_bytes) + 1 <= LAND._wave_land_window._MAX_LAND_JSON_BYTES


def test_release_failure_never_overwrites_land_result() -> None:
    """M14: release 例外は core JSON と元 rc を変更しない。"""

    with _repo() as repo:
        request = repo.request(repo.waves["one"])
        lease_dir = repo.root / "lease"
        lease_dir.mkdir()
        result = LAND.LandResult(
            LAND.RC_STALE_MAIN,
            "stale-main",
            "synthetic stale main",
            release_safe=True,
        )

        def failed_release(*_args, **_kwargs):
            raise OSError("synthetic release failure")

        with (
            _patched_land_attr("land", lambda _request: result),
            _patched_window_release(failed_release),
        ):
            rc, payload, _raw, errors = _invoke_land_main(request, lease_dir)

        assert rc == LAND.RC_STALE_MAIN
        assert payload["status"] == "stale-main"
        assert payload["release_safe"] is True
        assert errors == (
            "lease_renew state=free reason=none\n"
            "lease_release state=unavailable reason=release-internal-error\n"
        )


def _gate_plan(
    *,
    fragment_ledger: str,
    targets: tuple[_FakeFoldTarget, ...],
    transaction_id: str = "a" * 64,
) -> _FakeFoldPlan:
    fragment_path = (
        f"docs/spool/{fragment_ledger}/2000-01-01-test-wave-1.md"
    )
    fragment = _FakeFoldFragment(
        "test-wave",
        path=fragment_path,
        content_sha256=hashlib.sha256(b"fragment\n").hexdigest(),
    )
    return _FakeFoldPlan(
        fragment_path,
        targets=targets,
        fragments=(fragment,),
        transaction_id=transaction_id,
    )


def test_fold_gate_rejects_overlap_with_third_live_registered_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        third = repo.root / "third-live-worktree"
        _add_detached_worktree(repo, third)
        isolation = third / "fold-isolation"
        isolation.mkdir()

        def exact_temporary_directory(**kwargs):
            assert kwargs == {
                "prefix": "izanagi-fold-gate-",
                "dir": "/tmp",
            }
            return contextlib.nullcontext(str(isolation))

        with _verified_repository(repo, wave) as repository:
            registered = LAND._registered_worktree_paths(repository)
            assert {
                repo.main.resolve(strict=True),
                wave.resolve(strict=True),
                third.resolve(strict=True),
            } <= set(registered)
            monkeypatch.setattr(
                LAND.tempfile,
                "TemporaryDirectory",
                exact_temporary_directory,
            )
            with pytest.raises(
                LAND._FoldGateFailure,
                match=(
                    "fold gate isolation directory overlaps a registered "
                    "worktree"
                ),
            ):
                LAND._execute_fold_gate(
                    repository,
                    _FakeFoldPlan("docs/spool/worklog/synthetic.md"),
                    LAND._FoldGateSelection("1" * 64, (), (), ()),
                    _git(wave, "rev-parse", "HEAD"),
                    LAND._fold_gate_budgets(),
                )


def test_registered_worktree_paths_keep_absent_registration() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        missing = repo.root / "scratch" / "job-repo"
        _add_detached_worktree(repo, missing)
        shutil.rmtree(missing)
        raw = _worktree_porcelain(repo)
        record = next(
            item
            for item in raw.split(b"\n\n")
            if b"worktree " + os.fsencode(missing) in item.splitlines()
        )
        assert any(line.startswith(b"prunable ") for line in record.splitlines())

        with _verified_repository(repo, wave) as repository:
            registered = LAND._registered_worktree_paths(repository)

        assert repo.main.resolve(strict=True) in registered
        assert wave.resolve(strict=True) in registered
        assert missing.is_absolute() and not missing.exists()
        assert missing in registered


def test_registered_worktree_paths_keep_live_directory_with_missing_dotgit(
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        linked = repo.root / "dotgit-gone"
        _add_detached_worktree(repo, linked)
        (linked / ".git").unlink()
        raw = _worktree_porcelain(repo)
        record = next(
            item
            for item in raw.split(b"\n\n")
            if b"worktree " + os.fsencode(linked) in item.splitlines()
        )
        assert any(line.startswith(b"prunable ") for line in record.splitlines())

        with _verified_repository(repo, wave) as repository:
            registered = LAND._registered_worktree_paths(repository)

        assert linked.resolve(strict=True) in registered


def test_registered_worktree_paths_keep_live_newline_marker_registration(
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        linked = repo.root / "live\nprunable fake-marker"
        _add_detached_worktree(repo, linked)
        raw = _worktree_porcelain(repo)
        raw_prefix = os.fsencode(linked).split(b"\n", 1)[0]
        assert b"worktree " + raw_prefix + b"\nprunable fake-marker\n" in raw

        with _verified_repository(repo, wave) as repository:
            registered = LAND._registered_worktree_paths(repository)

        listed_path = Path(os.fsdecode(raw_prefix))
        assert linked.is_dir()
        assert listed_path in registered


@pytest.mark.parametrize(
    "failure_kind",
    ("permission", "unicode"),
)
def test_registered_worktree_paths_fail_closed_for_other_resolution_errors(
    failure_kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        raw = _worktree_porcelain(repo)
        main_raw = os.fsencode(repo.main)
        assert b"worktree " + main_raw in raw

        with _verified_repository(repo, wave) as repository:
            with monkeypatch.context() as patch:
                if failure_kind == "permission":
                    original_resolve = LAND.Path.resolve

                    def fail_resolve(path: Path, *, strict: bool = False):
                        if path == repo.main and strict:
                            raise PermissionError("synthetic permission denial")
                        return original_resolve(path, strict=strict)

                    patch.setattr(LAND.Path, "resolve", fail_resolve)
                else:
                    original_fsdecode = LAND.os.fsdecode

                    def fail_decode(value):
                        if value == main_raw:
                            raise UnicodeError("synthetic decode failure")
                        return original_fsdecode(value)

                    patch.setattr(LAND.os, "fsdecode", fail_decode)

                with pytest.raises(
                    LAND._FoldGateFailure,
                    match="registered worktree path cannot be resolved",
                ):
                    LAND._registered_worktree_paths(repository)


@pytest.mark.parametrize(
    "raw",
    (b"", b"prunable fake-marker\n\n"),
    ids=("empty", "marker-only"),
)
def test_registered_worktree_paths_reject_list_without_worktree_lines(
    raw: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        with _verified_repository(repo, wave) as repository:
            monkeypatch.setattr(
                LAND,
                "_git",
                lambda *_args: subprocess.CompletedProcess(
                    [REAL_GIT],
                    0,
                    raw,
                    b"",
                ),
            )
            with pytest.raises(
                LAND._FoldGateFailure,
                match="registered worktree list is empty",
            ):
                LAND._registered_worktree_paths(repository)


def test_registered_worktree_paths_do_not_prune_absent_registration() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        missing = repo.root / "scratch" / "job-repo"
        admin = _add_detached_worktree(repo, missing)
        shutil.rmtree(missing)
        assert admin.is_dir()

        with _verified_repository(repo, wave) as repository:
            registered = LAND._registered_worktree_paths(repository)

        raw_after = _worktree_porcelain(repo)
        assert missing in registered
        assert admin.is_dir()
        assert b"worktree " + os.fsencode(missing) + b"\n" in raw_after
        assert b"prunable " in next(
            item
            for item in raw_after.split(b"\n\n")
            if b"worktree " + os.fsencode(missing) in item.splitlines()
        )


def test_fold_gate_rejects_recreated_absent_registered_isolation_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        missing = repo.root / "izanagi-fold-gate-reserved"
        _add_detached_worktree(repo, missing)
        shutil.rmtree(missing)

        @contextlib.contextmanager
        def recreate_registered_path(**kwargs):
            assert kwargs == {
                "prefix": "izanagi-fold-gate-",
                "dir": "/tmp",
            }
            missing.mkdir()
            try:
                yield str(missing)
            finally:
                shutil.rmtree(missing)

        with _verified_repository(repo, wave) as repository:
            monkeypatch.setattr(
                LAND.tempfile,
                "TemporaryDirectory",
                recreate_registered_path,
            )
            with pytest.raises(
                LAND._FoldGateFailure,
                match=(
                    "fold gate isolation directory overlaps a registered "
                    "worktree"
                ),
            ):
                LAND._execute_fold_gate(
                    repository,
                    _FakeFoldPlan("docs/spool/worklog/synthetic.md"),
                    LAND._FoldGateSelection("1" * 64, (), (), ()),
                    _git(wave, "rev-parse", "HEAD"),
                    LAND._fold_gate_budgets(),
                )


def _absent_registration_fold_case(repo: _Repo, wave: Path):
    (repo.main / ".git" / "info" / "exclude").write_text(
        ".codex/worktrees/\n",
        encoding="utf-8",
    )
    relative, _fragment, content = _fake_pending_fragment(repo, wave)
    tip = _git(wave, "rev-parse", "HEAD")
    missing = repo.root / "scratch" / "job-repo"
    admin = _add_detached_worktree(repo, missing)
    shutil.rmtree(missing)
    folded_after = b"# receipts\n- missing-registration-land\n"

    def apply(repo_path: Path, _plan) -> None:
        (repo_path / relative).unlink()
        (repo_path / "docs/spool/FOLDED.md").write_bytes(folded_after)

    plan = _FakeFoldPlan(
        relative,
        targets=(
            _FakeFoldTarget(
                "docs/spool/FOLDED.md",
                after_bytes=folded_after,
            ),
        ),
        fragments=(
            _FakeFoldFragment(
                "test-wave",
                path=relative,
                content_sha256=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            ),
        ),
    )
    module = _FakeFoldModule(plan, apply)
    selection = LAND._FoldGateSelection("1" * 64, (), ("folded",), ())
    return tip, missing, admin, module, selection


@contextlib.contextmanager
def _real_fold_land_seams(module: _FakeFoldModule, selection):
    with (
        _patched_land_attr("_load_spool_fold", lambda: module),
        _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        _patched_land_attr("_select_fold_gate_nodes", lambda *_args: selection),
        _patched_land_attr(
            "_verify_folded_fragment_receipts",
            lambda *_args: None,
        ),
    ):
        yield


def test_land_succeeds_with_absent_registered_worktree() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip, missing, admin, module, selection = (
            _absent_registration_fold_case(repo, wave)
        )
        with _real_fold_land_seams(module, selection):
            result = _land_real_gate(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert admin.is_dir()
        assert b"worktree " + os.fsencode(missing) + b"\n" in (
            _worktree_porcelain(repo)
        )


def test_land_with_absent_registration_still_rejects_live_wave_dirt() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip, missing, _admin, module, selection = (
            _absent_registration_fold_case(repo, wave)
        )
        dirt = wave / "untracked-dirt.txt"
        dirt.write_text("dirt\n", encoding="utf-8")
        assert b"worktree " + os.fsencode(missing) + b"\n" in (
            _worktree_porcelain(repo)
        )
        with _real_fold_land_seams(module, selection):
            result = _land_real_gate(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_DIRT, "rejected"), result
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert dirt.read_text(encoding="utf-8") == "dirt\n"


def test_fold_gate_rc_status_and_budget_invariant_are_exact() -> None:
    result = LAND._fold_gate_failed_result(
        "synthetic gate failure",
        main_before="a" * 40,
        main_after="a" * 40,
        tested_tip="b" * 40,
    )
    assert (LAND.RC_FOLD_GATE, result.rc, result.status) == (
        31,
        31,
        "fold-gate-failed",
    )
    budgets = LAND._fold_gate_budgets()
    assert (
        budgets.inner_seconds + budgets.termination_grace_seconds
        < budgets.outer_seconds
    )
    with _patched_land_attr(
        "_FOLD_GATE_OUTER_TIMEOUT_SECONDS",
        budgets.inner_seconds + budgets.termination_grace_seconds,
    ):
        with pytest.raises(LAND._FoldGateFailure, match="time budget invariant"):
            LAND._fold_gate_budgets()


def test_fold_gate_expected_targets_are_independent_of_plan_targets() -> None:
    plan = _gate_plan(
        fragment_ledger="worklog",
        targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
    )
    assert LAND._expected_fold_target_paths(plan) == (
        "docs/spool/FOLDED.md",
        "docs/worklog.md",
    )
    with pytest.raises(
        LAND._FoldGateFailure,
        match="omits independently expected targets",
    ):
        LAND._select_fold_gate_nodes(ROOT, plan)


def test_fold_gate_selection_records_uncovered_family_without_rejecting() -> None:
    plan = _gate_plan(
        fragment_ledger="decisions",
        targets=(
            _FakeFoldTarget("docs/decisions.md"),
            _FakeFoldTarget("docs/spool/FOLDED.md"),
        ),
    )
    selection = LAND._select_fold_gate_nodes(ROOT, plan)
    assert selection.target_families == ("decisions", "folded")
    assert selection.uncovered_families == ("decisions",)
    assert selection.nodeids == (
        "test_spool_fold.py::"
        "test_n37_real_repo_canonical_family_requires_archive_active_history",
    )
    assert re.fullmatch(r"[0-9a-f]{64}", selection.registry_digest)


def test_fold_gate_capability_mismatch_is_fail_closed_and_not_user_injectable(
) -> None:
    class CapabilityRow:
        target_family = ("folded",)
        requires_git_history = True
        requires_submodules = False

    class CapabilityRegistry:
        FOLD_GATE_SELECTED_NODES = {
            "test_spool_fold.py::test_gate_node": CapabilityRow(),
        }
        FOLD_GATE_NODE_REGISTRY_SHA256 = "1" * 64

        @staticmethod
        def fold_gate_node_registry_sha256():
            return "1" * 64

    plan = _gate_plan(
        fragment_ledger="decisions",
        targets=(
            _FakeFoldTarget("docs/decisions.md"),
            _FakeFoldTarget("docs/spool/FOLDED.md"),
        ),
    )
    with _patched_land_attr(
        "_load_fold_gate_registry",
        lambda _repo: CapabilityRegistry,
    ):
        with pytest.raises(
            LAND._FoldGateFailure,
            match="capability mismatch",
        ):
            LAND._select_fold_gate_nodes(ROOT, plan)
    assert "executor" not in {
        field.name for field in dataclasses.fields(LAND.LandRequest)
    }
    assert "fold-gate-executor" not in {
        action.dest for action in LAND._parser()._actions
    }


def test_fold_gate_environment_removes_ambient_pytest_and_python_injection() -> None:
    names = tuple(LAND._FOLD_GATE_ENV_REMOVE)
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ[name] = "ambient-injection"
        env = LAND._fold_gate_environment()
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    assert all(name not in env for name in names)
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert "PYTHONNOUSERSITE" not in dict(LAND._FOLD_GATE_ENV_FORCE)
    assert "PYTHONNOUSERSITE" not in env
    assert "IZANAGI_RUN_GROWTH_HELD_TESTS" not in dict(
        LAND._FOLD_GATE_ENV_FORCE
    )


@pytest.mark.parametrize(
    "name",
    (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONOPTIMIZE",
    ),
)
def test_each_fold_gate_ambient_injection_is_removed_independently(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(name, "ambient-injection")

    env = LAND._fold_gate_environment()

    assert name not in env


def test_fold_gate_child_environment_removes_ambient_pythonnousersite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHONNOUSERSITE", "1")

    env = LAND._fold_gate_environment_with_tmp(tmp_path)

    assert "PYTHONNOUSERSITE" not in env


def test_fold_gate_junit_requires_execution_and_rejects_skip_failure_error(
) -> None:
    nodeid = "test_spool_fold.py::test_gate_node"
    cases = {
        "passed": "<testcase name='test_gate_node'/>",
        "skipped": (
            "<testcase name='test_gate_node'><skipped/></testcase>"
        ),
        "failed": (
            "<testcase name='test_gate_node'><failure/></testcase>"
        ),
        "error": "<testcase name='test_gate_node'><error/></testcase>",
        "empty": "",
    }
    with tempfile.TemporaryDirectory(prefix="fold-gate-junit-test-") as raw:
        path = Path(raw) / "junit.xml"
        for case, payload in cases.items():
            path.write_text(
                f"<testsuite>{payload}</testsuite>",
                encoding="utf-8",
            )
            if case == "passed":
                assert LAND._parse_fold_gate_junit(path, (nodeid,)) == (
                    LAND._FoldGateJUnitCounts(1, 1, 0, 0, 0)
                )
            else:
                with pytest.raises(LAND._FoldGateFailure):
                    LAND._parse_fold_gate_junit(path, (nodeid,))


def test_fold_gate_junit_rejects_zero_execution_as_the_only_failure(
    tmp_path: Path,
) -> None:
    path = tmp_path / "empty-junit.xml"
    path.write_text("<testsuite/>", encoding="utf-8")

    with pytest.raises(LAND._FoldGateFailure, match="JUnit rejected"):
        LAND._parse_fold_gate_junit(path, ())


def test_fold_gate_exports_full_tree_applies_raw_bytes_and_runs_one_pytest(
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        relative, _fragment_path, content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        plan = _gate_plan(
            fragment_ledger="worklog",
            targets=(
                _FakeFoldTarget(
                    "docs/spool/FOLDED.md",
                    after_bytes=b"# receipts\n- gate\n",
                ),
                _FakeFoldTarget(
                    "docs/worklog.md",
                    before_exists=False,
                    after_bytes=b"# projected worklog\n",
                ),
            ),
        )
        plan.gc_paths = (relative,)
        plan.fragments = (
            _FakeFoldFragment(
                "test-wave",
                path=relative,
                content_sha256=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            ),
        )
        selection = LAND._FoldGateSelection(
            "1" * 64,
            ("test_spool_fold.py::test_gate_node",),
            ("folded", "worklog"),
            (),
        )
        observed: dict[str, object] = {}

        def fake_pytest(
            argv,
            *,
            cwd,
            env,
            timeout,
            termination_grace,
        ):
            observed["argv"] = argv
            observed["env"] = env
            observed["timeout"] = timeout
            observed["termination_grace"] = termination_grace
            observed["base"] = (cwd / "base.txt").read_bytes()
            observed["folded"] = (
                cwd / "docs/spool/FOLDED.md"
            ).read_bytes()
            observed["worklog"] = (cwd / "docs/worklog.md").read_bytes()
            observed["gc_missing"] = not (cwd / relative).exists()
            observed["git_missing"] = not (cwd / ".git").exists()
            junit_arg = next(
                item for item in argv if item.startswith("--junitxml=")
            )
            Path(junit_arg.split("=", 1)[1]).write_text(
                "<testsuite><testcase name='test_gate_node'/></testsuite>",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        request = repo.request(wave, tip=tip)
        with _cwd(wave):
            repository = LAND._verify_repository(request)
            try:
                with _patched_land_attr("_run_fold_gate_pytest", fake_pytest):
                    counts = LAND._execute_fold_gate(
                        repository,
                        plan,
                        selection,
                        tip,
                        LAND._fold_gate_budgets(),
                    )
            finally:
                repository.close()

        assert counts == LAND._FoldGateJUnitCounts(1, 1, 0, 0, 0)
        assert observed["base"] == b"base\n"
        assert observed["folded"] == b"# receipts\n- gate\n"
        assert observed["worklog"] == b"# projected worklog\n"
        assert observed["gc_missing"] is True
        assert observed["git_missing"] is True
        assert observed["argv"][-1] == (
            "orchestrator/tests/test_spool_fold.py::test_gate_node"
        )
        assert observed["argv"].count("-m") == 1
        assert observed["argv"][1:5] == ["-m", "pytest", "-p", "junitxml"]


def test_fold_gate_missing_junit_reports_bounded_escaped_child_output() -> None:
    class Repository:
        wave = ROOT

    class Plan:
        targets = ()
        fragments = ()
        gc_paths = ()

    selection = LAND._FoldGateSelection(
        "1" * 64,
        ("test_spool_fold.py::test_gate_node",),
        ("folded",),
        (),
    )
    stdout = b"A" * 600 + b" stdout\x1b\n"
    stderr = b"B" * 600 + b" stderr\x00\r\n"

    def no_junit(argv, **_kwargs):
        return subprocess.CompletedProcess(argv, 4, stdout, stderr)

    with (
        _patched_land_attr("_registered_worktree_paths", lambda _repo: (ROOT,)),
        _patched_land_attr("_export_tracked_tree", lambda *_args: None),
        _patched_land_attr("_run_fold_gate_pytest", no_junit),
        pytest.raises(LAND._FoldGateInfrastructureFailure) as raised,
    ):
        LAND._execute_fold_gate(
            Repository(),
            Plan(),
            selection,
            "a" * 40,
            LAND._fold_gate_budgets(),
        )

    reason = str(raised.value)
    assert "JUnit cannot be parsed" in reason
    assert "pytest returncode=4" in reason
    assert "stdout_tail(omitted_bytes=" in reason
    assert "stderr_tail(omitted_bytes=" in reason
    assert r"\\x1b\\x0a" in reason
    assert r"\\x00\\x0d\\x0a" in reason
    assert "\x1b" not in reason
    assert "\x00" not in reason
    assert len(reason.encode("ascii")) < 1400


def test_fold_gate_real_argv_environment_create_junit_in_gitless_tree() -> None:
    class Repository:
        wave = ROOT

    class Plan:
        targets = ()
        fragments = ()
        gc_paths = ()

    nodeid = (
        "test_spool_fold.py::"
        "test_n37_real_repo_canonical_family_requires_archive_active_history"
    )
    selection = LAND._FoldGateSelection(
        "1" * 64,
        (nodeid,),
        ("folded",),
        (),
        ((nodeid, ("folded",)),),
    )
    tip = _git(ROOT, "rev-parse", "HEAD")
    child_env = LAND._fold_gate_environment_with_tmp(Path("/tmp/fold-gate-probe"))
    assert "PYTHONNOUSERSITE" not in child_env
    assert "PYTHONOPTIMIZE" not in child_env
    assert child_env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"

    with _patched_land_attr("_registered_worktree_paths", lambda _repo: (ROOT,)):
        counts = LAND._execute_fold_gate(
            Repository(),
            Plan(),
            selection,
            tip,
            LAND._fold_gate_budgets(),
        )

    assert counts == LAND._FoldGateJUnitCounts(1, 1, 0, 0, 0)


def test_fold_gate_receipt_binds_plan_identity_transaction_and_raw_bytes(
) -> None:
    plan = _gate_plan(
        fragment_ledger="decisions",
        targets=(
            _FakeFoldTarget("docs/decisions.md", after_bytes=b"decisions\n"),
            _FakeFoldTarget(
                "docs/spool/FOLDED.md",
                after_bytes=b"folded\n",
            ),
        ),
    )
    selection = LAND._select_fold_gate_nodes(ROOT, plan)
    receipt = LAND._FoldGateReceipt(
        plan,
        plan.transaction_id,
        selection.registry_digest,
        selection.nodeids,
        LAND._fold_gate_target_raw_digests(plan),
        LAND._FOLD_GATE_OUTCOME,
        selection.uncovered_families,
    )
    assert LAND._verify_fold_gate_receipt(ROOT, receipt, plan) == selection

    replacement = _gate_plan(
        fragment_ledger="decisions",
        targets=plan.targets,
        transaction_id=plan.transaction_id,
    )
    with pytest.raises(LAND._FoldGateFailure, match="object identity"):
        LAND._verify_fold_gate_receipt(ROOT, receipt, replacement)
    with pytest.raises(LAND._FoldGateFailure, match="transaction_id"):
        LAND._verify_fold_gate_receipt(
            ROOT,
            dataclasses.replace(receipt, transaction_id="b" * 64),
            plan,
        )
    plan.targets[0].after_bytes = b"tampered\n"
    with pytest.raises(LAND._FoldGateFailure, match="raw digest mismatch"):
        LAND._verify_fold_gate_receipt(ROOT, receipt, plan)


def test_fold_gate_receipt_rejects_forged_target_raw_digest_only() -> None:
    plan = _gate_plan(
        fragment_ledger="decisions",
        targets=(
            _FakeFoldTarget("docs/decisions.md", after_bytes=b"decisions\n"),
            _FakeFoldTarget(
                "docs/spool/FOLDED.md",
                after_bytes=b"folded\n",
            ),
        ),
    )
    selection = LAND._select_fold_gate_nodes(ROOT, plan)
    receipt = LAND._FoldGateReceipt(
        plan,
        plan.transaction_id,
        selection.registry_digest,
        selection.nodeids,
        LAND._fold_gate_target_raw_digests(plan),
        LAND._FOLD_GATE_OUTCOME,
        selection.uncovered_families,
    )
    forged = dataclasses.replace(
        receipt,
        target_raw_digests=(
            (receipt.target_raw_digests[0][0], "0" * 64),
            *receipt.target_raw_digests[1:],
        ),
    )
    assert LAND._fold_gate_target_raw_digests(plan) == (
        receipt.target_raw_digests
    )
    assert forged.plan is plan
    assert forged.transaction_id == plan.transaction_id
    assert forged.registry_digest == selection.registry_digest
    assert forged.nodeids == selection.nodeids
    assert forged.outcome == LAND._FOLD_GATE_OUTCOME
    assert forged.uncovered_families == selection.uncovered_families
    assert forged.target_raw_digests != receipt.target_raw_digests

    with pytest.raises(
        LAND._FoldGateFailure,
        match="receipt target raw digest mismatch",
    ):
        LAND._verify_fold_gate_receipt(ROOT, forged, plan)


def test_spool_state_v3_roundtrips_gate_receipt_and_rejects_old_schema(
) -> None:
    fold = LAND._load_spool_fold()
    origin = fold.FoldOrigin(
        "land",
        "a" * 40,
        "b" * 40,
        "refs/heads/wave/test",
        "a" * 40,
        "a" * 40,
        fold.audited_commit_digest(()),
    )
    target = fold.TargetChange(
        "docs/spool/FOLDED.md",
        hashlib.sha256(b"before\n").hexdigest(),
        hashlib.sha256(b"after\n").hexdigest(),
        True,
        b"after\n",
    )
    fragment = fold.FragmentReceipt(
        "docs/spool/decisions/2000-01-01-test-wave-1.md",
        "2000-01-01",
        "test-wave",
        1,
        hashlib.sha256(b"fragment\n").hexdigest(),
        (),
    )
    transaction_id = fold._plan_transaction_id(
        "2000-01-01",
        origin,
        "c" * 64,
        (fragment,),
        (fragment.path,),
        0,
        None,
        (target,),
    )
    gate_receipt = fold.FoldGateReceipt(
        transaction_id,
        "d" * 64,
        (),
        ((target.path, target.after_sha256),),
        LAND._FOLD_GATE_OUTCOME,
        ("decisions",),
    )
    plan = fold.FoldPlan(
        "planned",
        "2000-01-01",
        transaction_id,
        origin,
        "c" * 64,
        "applied",
        (),
        (target,),
        (fragment,),
        (fragment.path,),
        0,
        None,
        gate_receipt,
    )
    state = fold._plan_state(plan)
    assert state["version"] == 3
    assert fold._state_plan(state) == plan

    old_state = dict(state)
    old_state.pop("gate_receipt")
    old_state["version"] = 2
    with tempfile.TemporaryDirectory(prefix="fold-gate-old-state-") as raw:
        path = Path(raw) / "state.json"
        path.write_text(
            json.dumps(
                old_state,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        with pytest.raises(fold.FoldGateReceiptError):
            fold._load_state(path)


def test_missing_recovery_gate_receipt_returns_rc31_before_main_change() -> None:
    fold = LAND._load_spool_fold()

    class MissingReceiptModule(_FakeFoldModule):
        FoldGateReceiptError = fold.FoldGateReceiptError

        def load_active_plan(self, _repo):
            raise self.FoldGateReceiptError("synthetic missing receipt")

    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        module = MissingReceiptModule(
            _FakeFoldPlan("docs/spool/worklog/missing.md"),
            lambda *_args: None,
        )
        with _patched_land_attr("_load_spool_fold", lambda: module):
            result = _land(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_GATE,
            "fold-gate-failed",
        )
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


def test_fold_gate_failure_and_main_pending_race_both_stop_before_ff() -> None:
    for case in ("gate-red", "main-pending-race"):
        with _repo() as repo:
            wave = repo.waves["one"]
            relative, _fragment, _content = _fake_pending_fragment(repo, wave)
            tip = _git(wave, "rev-parse", "HEAD")
            plan = _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
                fragments=(_FakeFoldFragment("test-wave", path=relative),),
            )
            module = _FakeFoldModule(plan, lambda *_args: None)

            def gate_runner(_repository, gate_plan, _tip):
                if case == "gate-red":
                    raise LAND._FoldGateFailure("synthetic semantic red")
                extra = (
                    repo.main
                    / "docs/spool/decisions/2000-01-01-racing-wave-1.md"
                )
                extra.write_text("racing fragment\n", encoding="utf-8")
                return _fake_gate_receipt(gate_plan)

            with (
                _patched_land_attr("_load_spool_fold", lambda: module),
                _patched_land_attr("_run_fold_gate", gate_runner),
                _patched_land_attr(
                    "_verify_fold_gate_receipt",
                    _verify_fake_gate_receipt,
                ),
            ):
                result = _land_real_gate(repo.request(wave, tip=tip))

            assert (result.rc, result.status) == (
                LAND.RC_FOLD_GATE,
                "fold-gate-failed",
            ), (case, result)
            assert _git(repo.main, "rev-parse", "HEAD") == repo.base
            assert result.fold_commit_sha is None


def test_fold_gate_expected_targets_cover_all_ledgers_rotation_and_receipts(
    tmp_path: Path,
) -> None:
    cases = {
        "worklog": "docs/worklog.md",
        "decisions": "docs/decisions.md",
        "failures": "docs/failures.md",
    }
    for ledger, canonical in cases.items():
        plan = _gate_plan(
            fragment_ledger=ledger,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
        )
        assert canonical in LAND._expected_fold_target_paths(plan)
        with pytest.raises(
            LAND._FoldGateFailure,
            match="omits independently expected targets",
        ):
            LAND._select_fold_gate_nodes(ROOT, plan)

    phase3_repo = tmp_path / "phase3-selection-repo"
    registry_path = phase3_repo / "orchestrator/tests/fold_gate_nodes.py"
    registry_path.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "orchestrator/tests/fold_gate_nodes.py", registry_path)
    fragment_raw = "## 本文\n\n### 見送り\n".encode("utf-8")
    fragment_path = (
        phase3_repo
        / "docs/spool/worklog/2000-01-01-test-wave-1.md"
    )
    fragment_path.parent.mkdir(parents=True)
    fragment_path.write_bytes(fragment_raw)
    phase3_plan = _gate_plan(
        fragment_ledger="worklog",
        targets=(
            _FakeFoldTarget("docs/phase3.md"),
            _FakeFoldTarget("docs/spool/FOLDED.md"),
            _FakeFoldTarget("docs/worklog.md"),
        ),
    )
    phase3_plan.fragments[0].content_sha256 = hashlib.sha256(
        fragment_raw
    ).hexdigest()
    expected_targets = LAND._expected_fold_target_paths(
        phase3_plan,
        repo=phase3_repo,
    )
    assert expected_targets == (
        "docs/phase3.md",
        "docs/spool/FOLDED.md",
        "docs/worklog.md",
    )
    assert LAND._fold_gate_target_families(
        expected_targets,
        rotation_path=None,
    ) == ("folded", "phase3", "worklog")
    phase3_selection = LAND._select_fold_gate_nodes(
        phase3_repo,
        phase3_plan,
    )
    assert phase3_selection.nodeids == (
        "test_spool_fold.py::"
        "test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed",
        "test_spool_fold.py::"
        "test_n37_real_repo_canonical_family_requires_archive_active_history",
        "test_spool_fold.py::"
        "test_phase3_real_canonical_plan_accepts_unique_and_rejects_generated_duplicate_id",
    )
    assert phase3_selection.uncovered_families == ()

    rotation = "docs/archive/worklog-phase3-0101-1.md"
    rotation_plan = _gate_plan(
        fragment_ledger="worklog",
        targets=(
            _FakeFoldTarget("docs/spool/FOLDED.md"),
            _FakeFoldTarget("docs/worklog.md"),
        ),
    )
    rotation_plan.rotation_path = rotation
    assert {
        rotation,
        "docs/archive/README.md",
    } <= set(LAND._expected_fold_target_paths(rotation_plan))
    with pytest.raises(
        LAND._FoldGateFailure,
        match="omits independently expected targets",
    ):
        LAND._select_fold_gate_nodes(ROOT, rotation_plan)

    repo = tmp_path / "receipt-repo"
    folded_path = repo / "docs/spool/FOLDED.md"
    folded_path.parent.mkdir(parents=True)
    before = b"# receipts\n"
    folded_path.write_bytes(before)
    record = {
        "allocations": {},
        "authored": "2000-01-01",
        "base": "a" * 40,
        "content_sha256": hashlib.sha256(b"fragment\n").hexdigest(),
        "seq": 1,
        "tested_tip": "b" * 40,
        "wave": "test-wave",
        "wave_ref": "refs/heads/wave/test",
    }
    after = before + (
        "- "
        + json.dumps(record, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    receipt_plan = _gate_plan(
        fragment_ledger="decisions",
        targets=(
            _FakeFoldTarget(
                "docs/decisions.md",
                after_bytes=b"decision\n",
            ),
            _FakeFoldTarget(
                "docs/spool/FOLDED.md",
                before_bytes=before,
                after_bytes=after,
            ),
        ),
    )
    LAND._verify_folded_fragment_receipts(repo, receipt_plan)
    record["content_sha256"] = "0" * 64
    receipt_plan.targets[-1].after_bytes = before + (
        "- "
        + json.dumps(record, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    with pytest.raises(
        LAND._FoldGateFailure,
        match="path/content digests",
    ):
        LAND._verify_folded_fragment_receipts(repo, receipt_plan)


def test_ambient_pythonoptimize_cannot_hide_one_byte_positive_control(
    tmp_path: Path,
) -> None:
    from orchestrator.tests import test_fold_gate_nodes_contract as contract

    mutated_source = tmp_path / "mutated-source"
    contract._materialize_real_canonical_source(mutated_source)
    contract._mutate_latest_t139_bytes(mutated_source / "docs/worklog.md")
    run_path = tmp_path / "run"
    run_path.mkdir()
    previous = os.environ.get("PYTHONOPTIMIZE")
    os.environ["PYTHONOPTIMIZE"] = "1"
    try:
        env = LAND._fold_gate_environment()
    finally:
        if previous is None:
            os.environ.pop("PYTHONOPTIMIZE", None)
        else:
            os.environ["PYTHONOPTIMIZE"] = previous
    code = (
        "from pathlib import Path\n"
        "import sys\n"
        "from orchestrator.tests import test_spool_fold as tests\n"
        "tests.test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed(\n"
        "    Path(sys.argv[2]), _checkout=Path(sys.argv[1]))\n"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            code,
            str(mutated_source),
            str(run_path),
        ],
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert "PYTHONOPTIMIZE" not in env
    assert "PYTHONNOUSERSITE" not in env
    assert completed.returncode != 0, completed.stdout + completed.stderr


@pytest.mark.parametrize("junit_case", ("passed", "failed"))
def test_fold_gate_tmp_isolation_preserves_main_and_wave_status_bytes(
    junit_case: str,
) -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        relative, _fragment_path, content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        plan = _gate_plan(
            fragment_ledger="worklog",
            targets=(
                _FakeFoldTarget(
                    "docs/spool/FOLDED.md",
                    after_bytes=b"# receipts\n- gate\n",
                ),
                _FakeFoldTarget(
                    "docs/worklog.md",
                    before_exists=False,
                    after_bytes=b"# projected worklog\n",
                ),
            ),
        )
        plan.gc_paths = (relative,)
        plan.fragments = (
            _FakeFoldFragment(
                "test-wave",
                path=relative,
                content_sha256=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            ),
        )
        selection = LAND._FoldGateSelection(
            "1" * 64,
            ("test_spool_fold.py::test_gate_node",),
            ("folded", "worklog"),
            (),
            (("test_spool_fold.py::test_gate_node", ("folded", "worklog")),),
        )
        before = {
            path: _git(
                path,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            )
            for path in (repo.main, wave)
        }
        previous_tmpdir = os.environ.get("TMPDIR")
        os.environ["TMPDIR"] = str(repo.main)

        def fake_pytest(
            argv,
            *,
            cwd,
            env,
            timeout,
            termination_grace,
        ):
            assert Path(env["TMPDIR"]).parent == cwd
            assert env["TMPDIR"] == env["TMP"] == env["TEMP"]
            basetemp = next(
                item.split("=", 1)[1]
                for item in argv
                if item.startswith("--basetemp=")
            )
            assert basetemp == env["TMPDIR"]
            (Path(env["TMPDIR"]) / "probe").write_bytes(b"tmp\n")
            junit = next(
                Path(item.split("=", 1)[1])
                for item in argv
                if item.startswith("--junitxml=")
            )
            child = (
                "<testcase name='test_gate_node'/>"
                if junit_case == "passed"
                else (
                    "<testcase name='test_gate_node'><failure/>"
                    "</testcase>"
                )
            )
            junit.write_text(f"<testsuite>{child}</testsuite>")
            return subprocess.CompletedProcess(
                argv,
                0 if junit_case == "passed" else 1,
                b"",
                b"",
            )

        request = repo.request(wave, tip=tip)
        try:
            with _cwd(wave):
                repository = LAND._verify_repository(request)
                try:
                    with _patched_land_attr(
                        "_run_fold_gate_pytest", fake_pytest
                    ):
                        if junit_case == "passed":
                            LAND._execute_fold_gate(
                                repository,
                                plan,
                                selection,
                                tip,
                                LAND._fold_gate_budgets(),
                            )
                        else:
                            with pytest.raises(LAND._FoldGateFailure):
                                LAND._execute_fold_gate(
                                    repository,
                                    plan,
                                    selection,
                                    tip,
                                    LAND._fold_gate_budgets(),
                                )
                finally:
                    repository.close()
        finally:
            if previous_tmpdir is None:
                os.environ.pop("TMPDIR", None)
            else:
                os.environ["TMPDIR"] = previous_tmpdir
        after_status = {
            path: _git(
                path,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            )
            for path in (repo.main, wave)
        }
        assert after_status == before


def test_main_untracked_archive_closure_race_stops_before_ff() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")
        plan = _FakeFoldPlan(
            relative,
            targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
            fragments=(_FakeFoldFragment("test-wave", path=relative),),
        )
        module = _FakeFoldModule(plan, lambda *_args: None)
        extra = repo.main / "docs/archive/worklog-racing.md"

        def gate_runner(_repository, gate_plan, _tip):
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_text("untracked closure race\n", encoding="utf-8")
            return _fake_gate_receipt(gate_plan)

        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_run_fold_gate", gate_runner),
            _patched_land_attr(
                "_verify_fold_gate_receipt",
                _verify_fake_gate_receipt,
            ),
        ):
            result = _land_real_gate(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (
            LAND.RC_FOLD_GATE,
            "fold-gate-failed",
        )
        assert "surviving untracked fold closure" in result.reason
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base
        assert extra.is_file()


def test_fold_gate_structured_families_survive_finalize_failure() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        relative, _fragment, _content = _fake_pending_fragment(repo, wave)
        tip = _git(wave, "rev-parse", "HEAD")

        def apply(repo_path: Path, _plan) -> None:
            (repo_path / relative).unlink()
            (repo_path / "docs/spool/FOLDED.md").write_text(
                "# receipts\n- structured\n",
                encoding="utf-8",
            )

        module = _FakeFoldModule(
            _FakeFoldPlan(
                relative,
                targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
                fragments=(_FakeFoldFragment("test-wave", path=relative),),
            ),
            apply,
            fail_finalize=True,
        )

        def receipt(_repository, plan, _tip):
            return dataclasses.replace(
                _fake_gate_receipt(plan),
                uncovered_families=("decisions",),
            )

        with (
            _patched_land_attr("_load_spool_fold", lambda: module),
            _patched_land_attr("_run_fold_gate", receipt),
            _patched_land_attr(
                "_verify_fold_gate_receipt",
                _verify_fake_gate_receipt,
            ),
            _patched_land_attr("_preflight_fold_message", lambda *_args: None),
        ):
            result = _land_real_gate(repo.request(wave, tip=tip))

        assert result.status == "fold-finalize-failed"
        assert result.fold_gate_uncovered_families == ("decisions",)
        assert result.as_json()["fold_gate_uncovered_families"] == [
            "decisions"
        ]


def test_fold_gate_assertion_reports_exact_failed_families() -> None:
    path = Path(tempfile.mkdtemp(prefix="fold-gate-family-junit-")) / "junit.xml"
    try:
        path.write_text(
            "<testsuite><testcase name='test_a'><failure/></testcase>"
            "<testcase name='test_b'/></testsuite>",
            encoding="utf-8",
        )
        with pytest.raises(LAND._FoldGateFailure) as raised:
            LAND._parse_fold_gate_junit(
                path,
                (
                    "test_spool_fold.py::test_a",
                    "test_spool_fold.py::test_b",
                ),
                (
                    ("test_spool_fold.py::test_a", ("failures",)),
                    ("test_spool_fold.py::test_b", ("worklog",)),
                ),
            )
        assert raised.value.retryable_same_request is False
        assert raised.value.covered_and_failed_families == ("failures",)
    finally:
        shutil.rmtree(path.parent)


def test_fold_gate_infra_retains_lease_and_assertion_releases() -> None:
    for infra in (True, False):
        with _repo() as repo:
            wave = repo.waves["one"]
            relative, _fragment, _content = _fake_pending_fragment(repo, wave)
            tip = _git(wave, "rev-parse", "HEAD")
            request = repo.request(wave, tip=tip)
            lease_dir, lease_path = _claim_acceptance_lease(repo, request)
            lease_before = lease_path.read_bytes()
            module = _FakeFoldModule(
                _FakeFoldPlan(
                    relative,
                    targets=(_FakeFoldTarget("docs/spool/FOLDED.md"),),
                    fragments=(
                        _FakeFoldFragment("test-wave", path=relative),
                    ),
                ),
                lambda *_args: None,
            )

            def fail_gate(*_args):
                if infra:
                    raise LAND._FoldGateInfrastructureFailure(
                        "synthetic JUnit parse failure"
                    )
                raise LAND._FoldGateFailure(
                    "synthetic assertion failure",
                    covered_and_failed_families=("folded",),
                )

            with (
                _patched_land_attr("_load_spool_fold", lambda: module),
                _patched_land_attr("_run_fold_gate", fail_gate),
            ):
                rc, payload, _raw, errors = _invoke_land_main(
                    request,
                    lease_dir,
                )
            assert rc == LAND.RC_FOLD_GATE
            assert payload["status"] == "fold-gate-failed"
            if infra:
                assert payload["retryable_same_request"] is True
                assert payload["release_safe"] is False
                assert lease_path.read_bytes() == lease_before
                assert "lease_release state=retained" in errors
            else:
                assert payload["retryable_same_request"] is False
                assert payload["release_safe"] is True
                assert payload[
                    "fold_gate_covered_and_failed_families"
                ] == ["folded"]
                assert not lease_path.exists()
                assert "lease_release state=released" in errors


def test_fold_gate_inner_timeout_uses_termination_grace_and_reaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[object] = []

    class Process:
        returncode = -signal.SIGKILL

        def communicate(self, timeout=None):
            events.append(("communicate", timeout))
            if timeout in {2.0, 3.0}:
                raise subprocess.TimeoutExpired(["pytest"], timeout)
            return b"stdout", b"stderr"

        def terminate(self):
            events.append("terminate")

        def kill(self):
            events.append("kill")

    monkeypatch.setattr(LAND.subprocess, "Popen", lambda *_a, **_k: Process())
    with pytest.raises(subprocess.TimeoutExpired):
        LAND._run_fold_gate_pytest(
            ["pytest"],
            cwd=ROOT,
            env={},
            timeout=2.0,
            termination_grace=3.0,
        )
    assert events == [
        ("communicate", 2.0),
        "terminate",
        ("communicate", 3.0),
        "kill",
        ("communicate", None),
    ]


def test_fold_gate_outer_watchdog_fires_when_injected_clock_advances() -> None:
    values = iter((0.0, 1.0))

    def advancing_clock() -> float:
        return next(values, 1.0)

    started = time.monotonic()
    with _patched_land_attr("_fold_gate_now", advancing_clock):
        with pytest.raises(
            LAND._FoldGateInfrastructureFailure,
            match="outer watchdog fired",
        ):
            with LAND._FoldGateOuterWatchdog(0.05):
                time.sleep(1.0)
    assert time.monotonic() - started < 0.5


def test_fold_writer_and_isolation_materialization_preserve_mode_contract(
    tmp_path: Path,
) -> None:
    fold = LAND._load_spool_fold()
    writer_existing = tmp_path / "writer-existing.md"
    writer_existing.write_bytes(b"before\n")
    writer_existing.chmod(0o640)
    fold._atomic_write_canonical_target(writer_existing, b"after\n")
    assert stat.S_IMODE(writer_existing.stat().st_mode) == 0o644
    writer_new = tmp_path / "writer-new.md"
    fold._atomic_write_canonical_target(writer_new, b"new\n")
    assert stat.S_IMODE(writer_new.stat().st_mode) == 0o644

    tree = tmp_path / "tree"
    existing = tree / "docs/existing.md"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"before\n")
    existing.chmod(0o640)

    class Plan:
        targets = (
            _FakeFoldTarget("docs/existing.md", after_bytes=b"after\n"),
            _FakeFoldTarget("docs/new.md", after_bytes=b"new\n"),
        )
        fragments = ()
        gc_paths = ()

    LAND._materialize_fold_plan(tree, Plan())
    assert stat.S_IMODE(existing.stat().st_mode) == 0o644
    assert stat.S_IMODE((tree / "docs/new.md").stat().st_mode) == 0o644


def test_fresh_noop_never_starts_fold_gate() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        tip = repo.commit(wave, "wave.txt", "wave\n")
        with _patched_land_attr(
            "_run_fold_gate",
            lambda *_args: (_ for _ in ()).throw(
                AssertionError("fresh noop must not start fold gate")
            ),
        ):
            result = _land_real_gate(repo.request(wave, tip=tip))

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            plain_cases = getattr(test, "_plain_cases", None)
            if plain_cases is None:
                test()
            else:
                for case in plain_cases:
                    test(*case)
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
