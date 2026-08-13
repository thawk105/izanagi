# -*- coding: utf-8 -*-
"""tools/dev_wave_land.py の linked-worktree / race / land 境界テスト。

pytest と ``python3 orchestrator/tests/test_dev_wave_land.py`` の両方で走る。
全 Git mutation は tempfile 配下の合成 repository に限定する。
"""
from __future__ import annotations

import contextlib
import dataclasses
import fcntl
import hashlib
import importlib.util
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
    ):
        tested_base = base or self.base
        tested_tip = tip or _git(wave, "rev-parse", "HEAD")
        commits = (
            audited
            if audited is not None
            else self.audited(tested_base, tested_tip, wave)
        )
        receipt_path = acceptance_receipt or self._acceptance_receipt(
            wave,
            tested_base,
            tested_tip,
            acceptance_wave,
        )
        return LAND.LandRequest(
            main_worktree=self.main,
            wave_worktree=wave,
            tested_main_sha=tested_base,
            tested_wave_tip_sha=tested_tip,
            audited_commits=commits,
            acceptance_wave=acceptance_wave,
            acceptance_receipt=receipt_path,
        )

    def _acceptance_receipt(
        self,
        wave: Path,
        tested_main: str,
        tested_tip: str,
        acceptance_wave: str,
    ) -> Path:
        waiter_blob = _git(
            wave,
            "rev-parse",
            f"{tested_tip}:tools/dev_wave_wait.py",
            check=False,
        )
        if re.fullmatch(r"[0-9a-f]{40}", waiter_blob) is None:
            waiter_blob = "0" * 40
        fingerprint = {
            "digest": hashlib.sha256(tested_tip.encode("ascii")).hexdigest(),
            "head_sha": tested_tip,
            "status_bytes": 0,
            "diff_bytes": 0,
            "submodule_status_bytes": 0,
        }
        receipt = {
            "schema_version": LAND._ACCEPTANCE_RECEIPT_SCHEMA,
            "authority_kind": LAND._ACCEPTANCE_AUTHORITY_KIND,
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


def _land(request):
    with _cwd(request.wave_worktree):
        return LAND.land(request)


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
    for commit in request.audited_commits:
        argv.extend(("--audited-commit", commit))
    return argv


def _receipt_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="ascii"))


def _write_receipt(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )


def _non_attributable_payload(
    request: object,
    *,
    child_rc: int = 1,
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
        "red_nodeids": ["orchestrator/tests/test_known.py::test_known"],
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
        assert result.as_json()["acceptance_receipt_sha256"] == hashlib.sha256(
            raw
        ).hexdigest()
        assert result.as_json()["acceptance_verdict"] == "child-green"
        assert result.as_json()["acceptance_red_nodeids"] == []
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
        shutil.copy2(ROOT / "tools" / "dev_wave_wait.py", wave / "tools")
        shutil.copy2(ROOT / "tools" / "wave_land_window.py", wave / "tools")
        (wave / "tools" / "run_tests.py").write_text(
            "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
            "{\"effective_scheduler\":\"serial\"}')\n"
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        _git(
            wave,
            "add",
            "tools/dev_wave_wait.py",
            "tools/wave_land_window.py",
            "tools/run_tests.py",
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


def test_real_non_attributable_waiter_receipt_passes_real_land_end_to_end() -> None:
    with _repo() as repo:
        wave = repo.waves["one"]
        known_red = "orchestrator/tests/test_known.py::test_known"
        (repo.main / "tools" / "run_tests.py").write_text(
            "import sys\n"
            f"node={known_red!r}\n"
            "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
            "{\"effective_scheduler\":\"serial\"}')\n"
            "if '--collect-only' in sys.argv:\n"
            "    print(node)\n"
            "    print('1 test collected in 0.01s')\n"
            "    raise SystemExit(0)\n"
            "if node in sys.argv:\n"
            "    print('=== short test summary info ===')\n"
            "    print('FAILED ' + node + ' - synthetic known red')\n"
            "    print('=== 1 failed in 0.01s ===')\n"
            "    raise SystemExit(1)\n"
            "print('=== short test summary info ===')\n"
            "print('FAILED ' + node + ' - synthetic known red')\n"
            "print('=== 1 failed in 0.01s ===')\n"
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )
        _git(repo.main, "add", "tools/run_tests.py")
        _git(repo.main, "commit", "-qm", "install synthetic known red")
        repo.base = _git(repo.main, "rev-parse", "HEAD")
        _git(wave, "merge", "--ff-only", "main")
        shutil.copy2(ROOT / "tools" / "dev_wave_wait.py", wave / "tools")
        shutil.copy2(ROOT / "tools" / "wave_land_window.py", wave / "tools")
        shutil.copy2(ROOT / "tools" / "check_acceptance_reds.py", wave / "tools")
        _git(
            wave,
            "add",
            "tools/dev_wave_wait.py",
            "tools/wave_land_window.py",
            "tools/check_acceptance_reds.py",
        )
        _git(wave, "commit", "-qm", "install real acceptance integrity tools")
        tip = _git(wave, "rev-parse", "HEAD")
        lease_dir = repo.root / "lease-red"
        lease_dir.mkdir()
        receipt_path = repo.root / "real-red-receipt.json"
        log_path = repo.root / "real-red.log"
        acceptance_wave = "codex-one"
        env = _git_env()
        for name in (
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "IZANAGI_TASK_RUN_ID",
            "IZANAGI_TASK_RUNS_ROOT",
        ):
            env.pop(name, None)

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
        assert payload["verdict"] == "non-attributable-only"
        assert payload["child_rc"] == 1
        assert payload["red_nodeids"] == [known_red]
        request = repo.request(
            wave,
            base=repo.base,
            tip=tip,
            acceptance_wave=acceptance_wave,
            acceptance_receipt=receipt_path,
        )

        result = _land(request)

        assert (result.rc, result.status) == (LAND.RC_OK, "landed"), result
        assert result.acceptance_receipt_sha256 == hashlib.sha256(
            raw_receipt
        ).hexdigest()
        assert result.acceptance_verdict == "non-attributable-only"
        assert result.acceptance_red_nodeids == (known_red,)
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


def test_nonblocking_common_lock_reports_lock_busy() -> None:
    """M9: lock-busy は checker を起動せず 2 秒未満で返す。"""
    with _repo() as repo:
        wave = repo.waves["one"]
        marker = repo.root / "provenance-checker-started"
        checker = (
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('started')\n"
        )
        repo.commit(wave, "tools/check_ai_provenance.py", checker)
        tip = repo.commit(wave, "wave.txt", "wave\n")
        lock_path = repo.main / ".git" / "dev-wave-land.lock"
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            started = time.monotonic()
            result = _land(repo.request(wave, tip=tip))
            elapsed = time.monotonic() - started
        finally:
            os.close(lock_fd)
        assert (result.rc, result.status) == (LAND.RC_LOCK_BUSY, "lock-busy"), result
        assert elapsed < 2.0
        assert not marker.exists()
        assert _git(repo.main, "rev-parse", "HEAD") == repo.base


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
            result = _land(repo.request(wave, tip=tip))
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
    ):
        self.gc_paths = (gc_path,)
        self.targets = targets
        self.fragments = fragments
        self.origin = origin
        self.phase = phase
        self.transaction_id = transaction_id or hashlib.sha256(
            (gc_path + "\0" + phase).encode("utf-8")
        ).hexdigest()

    def with_phase(self, phase: str) -> "_FakeFoldPlan":
        return _FakeFoldPlan(
            self.gc_paths[0],
            targets=self.targets,
            fragments=self.fragments,
            origin=self.origin,
            phase=phase,
            transaction_id=self.transaction_id,
        )


class _FakeFoldFragment:
    def __init__(self, wave: str):
        self.wave = wave


class _FakeFoldTarget:
    def __init__(self, path: str, *, before_exists: bool = True):
        self.path = path
        self.before_exists = before_exists


class _FakeFoldModule:
    FoldOrigin = _FakeFoldOrigin

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

    def apply_fold(self, repo: Path, plan) -> None:
        assert plan is self._plan
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

            def apply_fold(self, repo_path: Path, plan):
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
                return real_fold.apply_fold(repo_path, plan)

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

            def apply_fold(self, repo_path: Path, plan):
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
                return real_fold.apply_fold(repo_path, plan)

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
        fold.apply_fold(repo.main, plan)
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
            result = _land(request)
            assert (result.rc, result.status) == (
                LAND.RC_LOCK_BUSY,
                "lock-busy",
            ), result
        finally:
            release.touch()
        deadline = time.monotonic() + 5
        while _git(repo.main, "rev-parse", "HEAD") != tip and time.monotonic() < deadline:
            time.sleep(0.02)
        assert _git(repo.main, "rev-parse", "HEAD") == tip


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
                build_context=context, campaign_namespace="exploration",
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
