# -*- coding: utf-8 -*-
"""Temporary-repository integration coverage for the dev-wave supervisor."""
from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Iterator
from unittest import mock

import pytest

_BOOTSTRAP_REPO = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_REPO) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_REPO))

from orchestrator.tests.test_dev_waves_fake import write_fake_claude
from tools.dev_waves.checker import CheckSpec
from tools.dev_waves.daemon import (
    Supervisor,
    SupervisorConfig,
    SupervisorDependencies,
    SupervisorProfile,
)
from tools.dev_waves.git_state import resolve_repo_identity, snapshot_repo
from tools.dev_waves.ledger import STATUS_NAME, cache_transient_name
import tools.dev_waves.daemon as daemon_mod
from tools.dev_waves.protocol import exchange
from tools.dev_waves.schema import (
    PROTOCOL_VERSION,
    DevWavesError,
    ReasonCode,
    ResourceLimits,
    RunState,
    SubmitRequest,
    parse_response,
)
from tools.dev_waves.worker import kill_spawned_process, spawn_worker as real_spawn_worker


# ファイル丸ごとの 1 group ([T-120] が維持した xdist_group("dev-waves-integration")) は
# [T-132] (2026-07-27) で外し、テスト自身が長命なプロセス外資源 (socket・thread・Popen の子・
# 実 daemon プロセス) を作る node だけを xdist_group("dev-waves-runtime") に残した。対象を
# ここで手で列挙はしない — test_dev_waves_isolation_contract.py が同じ規則で AST から導出し、
# marker と突き合わせるので、付け忘れも付けすぎも同 test が赤くする。
#
# なぜ外したか: 全走 wall の下限を決めていたのはこの group の直列和 (68 秒) だった。A/B 交互
# 測定 (cygnus・worktree checkout・-n 32、順方向 3 往復 + 逆順 1 ブロック) は一貫して分割側が
# 速く、平均 73.4 -> 60.5 秒 (-17.6%)。[T-120] が「速くならない」と実測したのは -n 16 の条件で、
# 分割後の work をその並列度で割ると元の直列和と同程度になり差が埋もれていた。[T-120] の
# コメントは「下限は ungrouped の単一 node (46〜58 秒) なのでこの group (68〜70 秒) を割っても
# 頭打ち」とも書いていたが、68 > 58 で算数が合っていなかった。
#
# 代償: 分割すると各 node の temp git repo 構築がストレージ書き込みで競合し、このファイルの
# work は 68.0 -> 84.5 秒 (+24%、73/78 node が一様に増加) になる。利得は「分割後の work /
# 並列度 < 元の直列和」が成り立つ間だけなので、並列度が低い環境 (少コア機・PBS の小割当・CI)
# では消えるか逆転しうる。そこで回すときは wall を A/B 交互で測り直すこと。
#
# この直列 group が守らないもの: 時間境界に依存する node のフレーク ([T-136])。内部締切は
# _supervisor() / _request() 経由で 40/41 の node が持つため直列化では隔離できず、実際に
# group あり構成でも load 11 で赤が出ている。時間依存の解決は [T-136] の射程である。

_REPO = Path(__file__).resolve().parents[2]
_TERMINAL = {RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.INTERRUPTED}


def _run_command(
    argv: list[str], *, cwd: Path, env: dict[str, str] | None = None,
    allowed: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    if result.returncode not in allowed:
        raise AssertionError(
            f"command failed {result.returncode}: {argv!r}\n{result.stdout}\n{result.stderr}"
        )
    return result


def _git(cwd: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> str:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
    }
    return _run_command(["git", *args], cwd=cwd, env=environment, allowed=allowed).stdout.strip()


@contextlib.contextmanager
def _isolated_process_environment(root: Path, *, nested: bool = False) -> Iterator[None]:
    old = os.environ.copy()
    home = root / "test-home"
    config = root / "test-xdg-config"
    cache = root / "test-xdg-cache"
    for path in (home, config, cache):
        path.mkdir(mode=0o700, parents=True)
    global_config = root / "test-gitconfig"
    global_config.write_text("", encoding="utf-8")
    try:
        os.environ.clear()
        os.environ.update({
            "PATH": old.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C", "LANG": "C",
            "HOME": str(home), "XDG_CONFIG_HOME": str(config),
            "XDG_CACHE_HOME": str(cache), "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1",
        })
        if nested:
            os.environ["CLAUDECODE"] = "1"
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


@dataclass
class TemporaryRepo:
    root: Path
    main: Path
    remote: Path
    submodule_source: Path
    fake: Path
    fake_digest: str
    scenario_digest: str

    @property
    def runtime(self) -> Path:
        return self.main / "output" / "dev-wave-supervisor" / "runtime"


def _copy_task_run_surface(main: Path) -> None:
    (main / "tools").mkdir()
    shutil.copy2(_REPO / "tools" / "task_run.py", main / "tools" / "task_run.py")
    # [T-057] 並列 worker の .pyc 書き込みと競合しないよう `__pycache__` を除外する。
    shutil.copytree(_REPO / "tools" / "task_runs", main / "tools" / "task_runs",
                    ignore=shutil.ignore_patterns("__pycache__"))


def _temporary_repo(
    root: Path, waves: list[object], *, help_variant: str | None = None,
    handshake_variant: str | None = None,
) -> TemporaryRepo:
    main = root / "main"
    remote = root / "remote.git"
    submodule = root / "submodule-source"
    fake_dir = root / "fake"
    for repository in (main, submodule):
        repository.mkdir()
        _git(repository, "init", "-b", "main")
        _git(repository, "config", "user.name", "Dev Waves Test")
        _git(repository, "config", "user.email", "dev-waves@example.invalid")
    (submodule / "data.txt").write_text("submodule\n", encoding="utf-8")
    _git(submodule, "add", "data.txt")
    _git(submodule, "commit", "-m", "submodule base")

    _copy_task_run_surface(main)
    (main / "docs" / "handoff").mkdir(parents=True)
    (main / "docs" / "worklog.md").write_text(
        "# worklog\n\n## initial\n\n### 次の一手\n\n1. [T-076] bounded fake wave\n",
        encoding="utf-8",
    )
    (main / "docs" / "handoff" / "README.md").write_text("handoff\n", encoding="utf-8")
    (main / "tools" / "check_docs.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (main / "tools" / "check_ok.py").write_text(
        "from pathlib import Path\nimport time\n"
        "time.sleep(2 if Path('check.sleep').exists() else 0)\n"
        "raise SystemExit(1 if Path('check.fail').exists() else 0)\n",
        encoding="utf-8",
    )
    (main / "tools" / "check_fail.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    (main / "README.md").write_text("temporary dev waves repository\n", encoding="utf-8")
    (main / ".gitignore").write_text(
        "output/dev-wave-supervisor/runtime/\noutput/task-runs/\n__pycache__/\n",
        encoding="utf-8",
    )
    _git(main, "-c", "protocol.file.allow=always", "submodule", "add", str(submodule), "vendor/sub")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "initial repository")
    _git(root, "clone", "--bare", str(main), str(remote))
    _git(main, "remote", "add", "origin", str(remote))
    _git(main, "fetch", "origin", "main:refs/remotes/origin/main")
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o700)
    fake, digest = write_fake_claude(
        fake_dir, waves, help_variant=help_variant,
        handshake_variant=handshake_variant,
    )
    task_root = main / "output" / "task-runs"
    _run_command(
        [sys.executable, str(main / "tools" / "task_run.py"), "--root", str(task_root),
         "init-pilot", str(task_root)],
        cwd=main,
    )
    scenario_digest = hashlib.sha256((fake.parent / "scenario.json").read_bytes()).hexdigest()
    return TemporaryRepo(root, main, remote, submodule, fake, digest, scenario_digest)


def _profile(check_timeout: int = 15) -> SupervisorProfile:
    checks = (
        CheckSpec("docs", (sys.executable, "tools/check_docs.py"), check_timeout),
        CheckSpec("fixed", (sys.executable, "tools/check_ok.py"), check_timeout),
    )
    return SupervisorProfile(
        "default", "fake-model", "low", checks,
        max_waves=4, max_per_wave_timeout_s=10, max_total_timeout_s=30,
        max_per_wave_budget_usd=Decimal("1"), max_total_budget_usd=Decimal("3"),
        max_wave_output_bytes=512 * 1024, max_run_bytes=8 * 1024 * 1024,
        allowed_models=("fake-model",),
    )


def _supervisor(repo: TemporaryRepo, *, dependencies: SupervisorDependencies | None = None) -> Supervisor:
    return Supervisor(SupervisorConfig(
        str(repo.main), str(repo.fake), repo.fake_digest, _profile(), 15, 0.1,
        runtime_dir=str(repo.runtime), audit_max_bytes=64 * 1024,
    ), dependencies)


def _request(repo: TemporaryRepo, *, waves: int = 1, request_id: str | None = None,
             per_wave_timeout: int = 5, total_timeout: int | None = None,
             per_wave_budget: str = "1", total_budget: str | None = None,
             output_bytes: int = 256 * 1024,
             run_bytes: int = 8 * 1024 * 1024) -> SubmitRequest:
    identity = resolve_repo_identity(repo.main)
    return SubmitRequest(
        PROTOCOL_VERSION, "submit", identity.digest, waves, "default",
        request_id or str(uuid.uuid4()),
        ResourceLimits(
            per_wave_timeout, total_timeout or waves * per_wave_timeout,
            Decimal(per_wave_budget), Decimal(total_budget or str(waves)),
            output_bytes, run_bytes,
        ),
    )


def _wait_terminal(supervisor: Supervisor, run_id: str, timeout_s: float = 20.0):
    """Wait for a terminal state and for the run thread to release the run.

    Terminal state precedes quiescence: the run thread still joins its WAL
    writer, rewrites the status file and drops the run's descriptors after
    ``status`` first reports a terminal state.  Tests tear the temporary tree
    down as soon as this helper returns, so returning on the state alone races
    that tail — observed as ``OSError: Directory not empty`` in whichever node
    lost the race (5/48 in the standalone probe, 0/48 once joined).
    """
    deadline = time.monotonic() + timeout_s
    seen = []
    while time.monotonic() < deadline:
        status = supervisor.status(run_id)
        seen.append(status.state)
        if status.state in _TERMINAL:
            assert supervisor.wait_idle(timeout_s), (
                f"run thread still running after terminal state; states={seen[-10:]}"
            )
            return status, seen
        time.sleep(0.02)
    raise AssertionError(f"run did not terminate; states={seen[-10:]}")


def _wait_state(supervisor: Supervisor, run_id: str, state: RunState, wave: int) -> None:
    # xdist 高並列下では wave 1 (実 git 操作 + check) が 10 秒を超えうる。
    # 有界の決定的条件待ちであり、余裕を持たせても flaky にはならない。
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        status = supervisor.status(run_id)
        if status.state is state and status.wave_index == wave:
            return
        time.sleep(0.005)
    raise AssertionError((run_id, state, wave, supervisor.status(run_id)))


def _invocations(repo: TemporaryRepo) -> list[dict[str, object]]:
    path = repo.fake.parent / "invocations.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _start_real_daemon(
    repo: TemporaryRepo, request_waves: int, *, crash_after_accepted: bool = False,
) -> tuple[subprocess.Popen[str], str]:
    result_path = repo.root / "daemon-result"
    script = (
        "import os,pathlib,signal,sys,time,uuid\nfrom decimal import Decimal\n"
        "from tools.dev_waves.checker import CheckSpec\n"
        "from tools.dev_waves.daemon import Supervisor,SupervisorConfig,SupervisorDependencies,SupervisorProfile\n"
        "from tools.dev_waves.git_state import resolve_repo_identity\n"
        "from tools.dev_waves.schema import PROTOCOL_VERSION,ResourceLimits,SubmitRequest\n"
        "checks=(CheckSpec('docs',(sys.executable,'tools/check_docs.py'),15),"
        "CheckSpec('fixed',(sys.executable,'tools/check_ok.py'),15))\n"
        "p=SupervisorProfile('default','fake-model','low',checks,max_waves=4,"
        "max_per_wave_timeout_s=30,max_total_timeout_s=90,"
        "max_per_wave_budget_usd=Decimal('1'),max_total_budget_usd=Decimal('3'),"
        "max_wave_output_bytes=524288,max_run_bytes=8388608,allowed_models=('fake-model',))\n"
        "def crash(phase,_run,_wave):\n"
        "  if sys.argv[7]=='1' and phase=='after-accepted': os.kill(os.getpid(),signal.SIGKILL)\n"
        "s=Supervisor(SupervisorConfig(sys.argv[1],sys.argv[2],sys.argv[3],p,15,0.1,"
        "runtime_dir=sys.argv[4],audit_max_bytes=65536),"
        "SupervisorDependencies(crash_hook=crash))\n"
        "n=int(sys.argv[5]); identity=resolve_repo_identity(sys.argv[1]).digest\n"
        "q=SubmitRequest(PROTOCOL_VERSION,'submit',identity,n,'default',str(uuid.uuid4()),"
        "ResourceLimits(30,n*30,Decimal('1'),Decimal(str(n)),262144,8388608))\n"
        "r=s.submit(q); path=pathlib.Path(sys.argv[6]); path.write_text(r.run_id); "
        "open(path,'rb').close()\n"
        "while s._active is not None: time.sleep(.01)\n"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(_REPO)
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(repo.main), str(repo.fake),
         repo.fake_digest, str(repo.runtime), str(request_waves), str(result_path),
         "1" if crash_after_accepted else "0"],
        cwd=_REPO, env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None and not result_path.exists():
            raise AssertionError(process.stderr.read() if process.stderr else "daemon exited")
        if result_path.exists():
            # 書き手は open→write→close の途中でありうる。空内容は未完了として扱う。
            run_id = result_path.read_text(encoding="utf-8")
            if run_id:
                return process, run_id
        time.sleep(0.01)
    process.kill()
    process.wait()
    raise AssertionError("daemon run id did not appear")


def _restart_recovery_probe(repo: TemporaryRepo, resume_run_id: str = "-") -> str:
    script = (
        "import sys,uuid\nfrom decimal import Decimal\n"
        "from tools.dev_waves.checker import CheckSpec\n"
        "from tools.dev_waves.daemon import Supervisor,SupervisorConfig,SupervisorProfile\n"
        "from tools.dev_waves.git_state import resolve_repo_identity\n"
        "from tools.dev_waves.schema import *\n"
        "c=(CheckSpec('docs',(sys.executable,'tools/check_docs.py'),15),"
        "CheckSpec('fixed',(sys.executable,'tools/check_ok.py'),15))\n"
        "p=SupervisorProfile('default','fake-model','low',c,max_waves=4,"
        "max_per_wave_timeout_s=30,max_total_timeout_s=90,"
        "max_per_wave_budget_usd=Decimal('1'),max_total_budget_usd=Decimal('3'),"
        "max_wave_output_bytes=524288,max_run_bytes=8388608,allowed_models=('fake-model',))\n"
        "s=Supervisor(SupervisorConfig(sys.argv[1],sys.argv[2],sys.argv[3],p,15,.1,"
        "runtime_dir=sys.argv[4],audit_max_bytes=65536))\n"
        "q=SubmitRequest(PROTOCOL_VERSION,'submit',resolve_repo_identity(sys.argv[1]).digest,"
        "1,'default',str(uuid.uuid4()),ResourceLimits(5,5,Decimal('1'),Decimal('1'),262144,8388608))\n"
        "if sys.argv[5]!='-':\n"
        " r=s.resume(sys.argv[5]); print(r.state.value+'|'+(r.reason.value if r.reason else '-'))\n"
        "else:\n"
        " try: s.submit(q)\n"
        " except DevWavesError as e: print(e.code.value)\n"
        " else: print('accepted')\n"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(_REPO)
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo.main), str(repo.fake),
         repo.fake_digest, str(repo.runtime), resume_run_id], cwd=_REPO, env=environment,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_one_wave_success_accepts_exact_fake_receipt_and_landing() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            before = _git(repo.main, "rev-parse", "HEAD")
            submitted = supervisor.submit(_request(repo))
            status, seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.COMPLETED
            assert status.reason is ReasonCode.MAX_WAVES_REACHED
            after = _git(repo.main, "rev-parse", "HEAD")
            assert after != before
            assert _git(repo.main, "merge-base", "--is-ancestor", before, after, allowed=(0, 1)) == ""
            run = repo.runtime / submitted.run_id
            receipt = json.loads((run / "waves" / "001" / "receipt.json").read_text())
            assert receipt["landed_main_sha"] == after
            assert receipt["selected_task_ids"] == ["T-076"]
            assert "IGNORE STRUCTURED_OUTPUT" not in (run / "events.jsonl").read_text()
            assert (run / "worktrees" / "w001").is_dir()
            events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
            assert any(event["state"] == "wave-accepted" for event in events)


def _assert_manifest_namespace_tamper_fails(field: str, value: object) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])

            def tampering_spawn(spec_path, **kwargs):
                spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
                manifest_path = Path(spec["wave_manifest_path"])
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest[field] = value
                manifest_path.write_text(
                    json.dumps(manifest, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8",
                )
                return real_spawn_worker(spec_path, **kwargs)

            supervisor = _supervisor(repo, dependencies=SupervisorDependencies(
                spawn_worker_fn=tampering_spawn,
            ))
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.FAILED
            assert status.reason is ReasonCode.NONZERO_EXIT
            assert not _invocations(repo)
            stderr = (
                repo.runtime / submitted.run_id / "waves" / "001" / "stderr.log"
            ).read_text(encoding="utf-8")
            assert "namespace mismatch" in stderr


def test_fake_manifest_run_id_is_bound_to_path_namespace() -> None:
    _assert_manifest_namespace_tamper_fails("supervisor_run_id", "dw-tampered")


def test_fake_manifest_wave_index_is_bound_to_wNNN_namespace() -> None:
    _assert_manifest_namespace_tamper_fails("wave_index", 2)


def test_three_wave_success_uses_distinct_pid_start_and_session_markers_without_transcript_carryover() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success", "success", "success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo, waves=3, total_timeout=15, total_budget="3"))
            status, _seen = _wait_terminal(supervisor, submitted.run_id, 30)
            assert status.state is RunState.COMPLETED
            records = _invocations(repo)
            assert len(records) == 3
            identities = {(item["pid"], item["start_ticks"]) for item in records}
            sessions = {item["session_marker"] for item in records}
            prompts = {item["prompt_sha256"] for item in records}
            assert len(identities) == len(sessions) == len(prompts) == 3
            assert [item["wave_index"] for item in records] == [1, 2, 3]


@pytest.mark.parametrize(
    "scenario,reason",
    [
        ("nonzero", ReasonCode.NONZERO_EXIT),
        ("sleep_timeout", ReasonCode.TIMEOUT),
        ("grandchild_residual", ReasonCode.NONZERO_EXIT),
        ("log_cap", ReasonCode.LOG_LIMIT),
    ],
)
def test_child_failure_injection_stops_before_next_wave(scenario: str, reason: ReasonCode) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        options: dict[str, object] = {"scenario": scenario}
        if scenario == "sleep_timeout":
            options["sleep_s"] = 2
        if scenario == "log_cap":
            options["bytes"] = 300000
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [options, "success"])
            supervisor = _supervisor(repo)
            request = _request(repo, waves=2, per_wave_timeout=1, total_timeout=2,
                               total_budget="2", output_bytes=128 * 1024)
            submitted = supervisor.submit(request)
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.FAILED
            assert status.reason is reason
            assert len(_invocations(repo)) == 1


def test_cancel_running_child_persists_signal_prepare_then_observe() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{"scenario": "sleep_timeout", "sleep_s": 60}])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo, per_wave_timeout=10))
            _wait_state(supervisor, submitted.run_id, RunState.CHILD_RUNNING, 1)
            supervisor.cancel(
                submitted.run_id, "22222222-2222-4222-8222-222222222222",
            )
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.INTERRUPTED
            events = [json.loads(line) for line in (
                repo.runtime / submitted.run_id / "events.jsonl"
            ).read_text().splitlines()]
            signal_events = [
                item["event"] for item in events
                if item.get("operation_id") == "w001-cancel"
            ]
            assert signal_events == ["side_effect_prepared", "side_effect_observed"]


def test_shutdown_running_child_uses_same_prepared_signal_path() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{"scenario": "sleep_timeout", "sleep_s": 60}])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo, per_wave_timeout=10))
            _wait_state(supervisor, submitted.run_id, RunState.CHILD_RUNNING, 1)
            supervisor.shutdown()
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.INTERRUPTED
            events = [json.loads(line) for line in (
                repo.runtime / submitted.run_id / "events.jsonl"
            ).read_text().splitlines()]
            observed = [
                item["data"]["observed"]["status"] for item in events
                if item.get("operation_id") == "w001-cancel" and
                item["event"] == "side_effect_observed"
            ]
            assert observed == ["signalled"]


def test_fake_handshake_failure_persists_exact_terminal_reason() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(
                root, ["success"], handshake_variant="wrong-nonce",
            )
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.FAKE_HANDSHAKE_FAILED
            exit_record = json.loads((
                repo.runtime / submitted.run_id / "waves" / "001" / "worker-exit.json"
            ).read_text())
            assert exit_record["reason"] == ReasonCode.FAKE_HANDSHAKE_FAILED.value
            assert not _invocations(repo)


@pytest.mark.parametrize("scenario", [
    "malformed_json", "truncated", "multiple", "trailing_bytes", "oversize",
    "delayed_partial", "wrong_type",
])
def test_malformed_child_output_is_output_invalid(scenario: str) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        options: dict[str, object] = {"scenario": scenario}
        if scenario == "oversize":
            options["bytes"] = 300000
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [options])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo, output_bytes=256 * 1024))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            if scenario == "delayed_partial":
                # Worker parses only the complete bounded file after child exit;
                # chunk timing within the deadline is intentionally immaterial.
                assert status.state is RunState.COMPLETED
            else:
                expected = ReasonCode.LOG_LIMIT if scenario == "oversize" else ReasonCode.OUTPUT_INVALID
                assert status.reason is expected


@pytest.mark.parametrize("scenario", ["wrong_run", "wrong_wave", "wrong_base"])
def test_valid_receipt_with_wrong_binding_is_receipt_invalid(scenario: str) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [scenario])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.RECEIPT_INVALID


@pytest.mark.parametrize(
    "scenario,reason",
    [
        ("same_main", ReasonCode.MAIN_UNCHANGED),
        ("dirty_main", ReasonCode.MAIN_DIRTY),
        ("diverged_main", ReasonCode.MAIN_NOT_FF),
        ("commit_mismatch", ReasonCode.COMMIT_MISMATCH),
        ("commit_reordered", ReasonCode.COMMIT_MISMATCH),
        ("extra_commit", ReasonCode.COMMIT_MISMATCH),
        ("external_main_advance", ReasonCode.COMMIT_MISMATCH),
        ("task_run_incomplete", ReasonCode.TASK_RUN_INCOMPLETE),
        ("worklog_conservation_broken", ReasonCode.WORKLOG_INVALID),
        ("handoff_leaked", ReasonCode.HANDOFF_LEAKED),
        ("submodule_dirty", ReasonCode.SUBMODULE_DIRTY),
        ("push_attempt", ReasonCode.REMOTE_REF_CHANGED),
        ("provenance_failed", ReasonCode.TRUST_ROOT_CHANGED),
        ("check_failed", ReasonCode.CHECK_FAILED),
    ],
)
def test_independent_gate_failure_stops_next_wave(scenario: str, reason: ReasonCode) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [scenario, "success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo, waves=2, total_timeout=10, total_budget="2"))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is reason
            assert len(_invocations(repo)) == 1


def test_same_request_id_and_digest_returns_same_run_after_disconnect_and_restart() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            request = _request(repo, request_id="11111111-1111-4111-8111-111111111111")
            first = supervisor.submit(request)
            _wait_terminal(supervisor, first.run_id)
            restarted = _supervisor(repo)
            second = restarted.submit(request)
            assert second.run_id == first.run_id
            conflict = _request(repo, waves=2, request_id=request.client_request_id,
                                total_timeout=10, total_budget="2")
            with pytest.raises(Exception) as captured:
                restarted.submit(conflict)
            assert getattr(captured.value, "code", None) is ReasonCode.REQUEST_CONFLICT


def test_second_distinct_submit_is_busy_while_run_active() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{"scenario": "sleep_timeout", "sleep_s": 2}])
            supervisor = _supervisor(repo)
            first = supervisor.submit(_request(repo, per_wave_timeout=1))
            try:
                supervisor.submit(_request(repo))
            except DevWavesError as exc:
                assert exc.code is ReasonCode.DAEMON_BUSY
            else:
                raise AssertionError("second distinct submit entered an active run")
            _wait_terminal(supervisor, first.run_id)


def test_active_check_failure_occurs_only_after_passive_gates() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            checks = (
                CheckSpec("docs", (sys.executable, "tools/check_docs.py"), 15),
                CheckSpec("injected", (sys.executable, "tools/check_fail.py"), 15),
            )
            profile = SupervisorProfile(
                "default", "fake-model", "low", checks,
                max_waves=1, max_per_wave_timeout_s=10, max_total_timeout_s=10,
                max_per_wave_budget_usd=Decimal("1"), max_total_budget_usd=Decimal("1"),
                max_wave_output_bytes=512 * 1024, max_run_bytes=8 * 1024 * 1024,
                allowed_models=("fake-model",),
            )
            supervisor = Supervisor(SupervisorConfig(
                str(repo.main), str(repo.fake), repo.fake_digest, profile, 15, 0.1,
                runtime_dir=str(repo.runtime),
            ))
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.CHECK_FAILED
            checks_record = json.loads((
                repo.runtime / submitted.run_id / "waves" / "001" / "checks.json"
            ).read_text())
            assert checks_record["active_checks_started"] is True


@pytest.mark.parametrize(
    "check_name,reason",
    [("provenance", ReasonCode.PROVENANCE_FAILED),
     ("codex-agents", ReasonCode.CODE_DIRTY)],
)
def test_dedicated_provenance_and_code_dirty_reasons_are_wired(
    check_name: str, reason: ReasonCode,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            checks = (
                CheckSpec("docs", (sys.executable, "tools/check_docs.py"), 15),
                CheckSpec(check_name, (sys.executable, "tools/check_fail.py"), 15),
            )
            base = _profile()
            profile = SupervisorProfile(
                "default", "fake-model", "low", checks,
                max_waves=base.max_waves,
                max_per_wave_timeout_s=base.max_per_wave_timeout_s,
                max_total_timeout_s=base.max_total_timeout_s,
                max_per_wave_budget_usd=base.max_per_wave_budget_usd,
                max_total_budget_usd=base.max_total_budget_usd,
                max_wave_output_bytes=base.max_wave_output_bytes,
                max_run_bytes=base.max_run_bytes,
                allowed_models=base.allowed_models,
            )
            supervisor = Supervisor(SupervisorConfig(
                str(repo.main), str(repo.fake), repo.fake_digest, profile, 15, 0.1,
                runtime_dir=str(repo.runtime),
            ))
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is reason


@pytest.mark.parametrize(
    "phase,expected_invocations",
    [
        ("before-child", 0), ("running", None), ("after-exit", 1),
        ("after-land", 1), ("after-decision", 1),
    ],
)
def test_resume_never_duplicates_child_or_land(
    phase: str, expected_invocations: int | None,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            fired: list[str] = []

            def crash_hook(observed: str, _run_id: str | None, _wave: int | None) -> None:
                if observed == phase and not fired:
                    fired.append(observed)
                    raise RuntimeError("trusted crash injection")

            supervisor = _supervisor(
                repo, dependencies=SupervisorDependencies(crash_hook=crash_hook),
            )
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert fired == [phase]
            assert status.reason is ReasonCode.RUNTIME_IO_FAILURE
            before_resume = len(_invocations(repo))
            inactive_deadline = time.monotonic() + 2
            while supervisor._active is not None and time.monotonic() < inactive_deadline:
                time.sleep(0.01)
            resumed = supervisor.resume(submitted.run_id)
            assert resumed.state is RunState.FAILED
            assert len(_invocations(repo)) == before_resume
            if expected_invocations is None:
                assert before_resume in (0, 1)
            else:
                assert before_resume == expected_invocations


@pytest.mark.xdist_group("dev-waves-runtime")
@pytest.mark.parametrize(
    "waves,request_waves,target_state,target_wave",
    [
        ([{"scenario": "sleep_timeout", "sleep_s": 60}], 1,
         RunState.CHILD_RUNNING, 1),
        (["check_sleep"], 1, RunState.VERIFYING, 1),
        (["success", {"scenario": "sleep_timeout", "sleep_s": 60}], 2,
         RunState.CHILD_RUNNING, 2),
    ],
)
def test_real_daemon_sigkill_restart_closes_recovery_gate_at_three_points(
    waves: list[object], request_waves: int,
    target_state: RunState, target_wave: int,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, waves)
            daemon, run_id = _start_real_daemon(repo, request_waves)
            try:
                observer = _supervisor(repo)
                _wait_state(observer, run_id, target_state, target_wave)
                before = len(_invocations(repo))
                os.kill(daemon.pid, signal.SIGKILL)
                assert daemon.wait(timeout=5) == -signal.SIGKILL
                assert _restart_recovery_probe(repo) == ReasonCode.AMBIGUOUS_RECOVERY.value
                time.sleep(0.5)
                assert len(_invocations(repo)) == before
            finally:
                if daemon.poll() is None:
                    daemon.kill(); daemon.wait()


@pytest.mark.xdist_group("dev-waves-runtime")
def test_real_daemon_sigkill_after_accepted_reconciles_without_child_rerun() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            daemon, run_id = _start_real_daemon(
                repo, 1, crash_after_accepted=True,
            )
            assert daemon.wait(timeout=20) == -signal.SIGKILL
            assert _restart_recovery_probe(repo, run_id) == (
                "completed|max-waves-reached"
            )
            assert len(_invocations(repo)) == 1


@pytest.mark.xdist_group("dev-waves-runtime")
@pytest.mark.parametrize("dirty_kind", ["main", "submodule"])
def test_accepted_reconciliation_rejects_dirty_repo_without_child_rerun(
    dirty_kind: str,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            daemon, run_id = _start_real_daemon(
                repo, 1, crash_after_accepted=True,
            )
            assert daemon.wait(timeout=20) == -signal.SIGKILL
            target = (
                repo.main / "recovery-dirty.txt" if dirty_kind == "main"
                else repo.main / "vendor" / "sub" / "data.txt"
            )
            target.write_text("dirty\n", encoding="utf-8")
            assert _restart_recovery_probe(repo, run_id) == (
                "failed|ambiguous-recovery"
            )
            assert len(_invocations(repo)) == 1


@pytest.mark.xdist_group("dev-waves-runtime")
@pytest.mark.parametrize("mismatch", ["identity", "branch"])
def test_accepted_reconciliation_rebinds_repo_identity_and_main_branch(
    mismatch: str,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            daemon, run_id = _start_real_daemon(
                repo, 1, crash_after_accepted=True,
            )
            assert daemon.wait(timeout=20) == -signal.SIGKILL
            supervisor = _supervisor(repo)
            if mismatch == "identity":
                patcher = mock.patch(
                    "tools.dev_waves.daemon.resolve_repo_identity",
                    return_value=mock.Mock(
                        digest="0" * 64, main_worktree=str(repo.main),
                    ),
                )
            else:
                patcher = mock.patch(
                    "tools.dev_waves.daemon.snapshot_repo",
                    return_value=replace(snapshot_repo(repo.main), branch="other"),
                )
            with patcher:
                resumed = supervisor.resume(run_id)
            assert (resumed.state, resumed.reason) == (
                RunState.FAILED, ReasonCode.AMBIGUOUS_RECOVERY,
            )
            assert len(_invocations(repo)) == 1


def test_invalid_request_audit_has_capacity_and_creates_no_run() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            before = {path.name for path in repo.runtime.iterdir()}
            response = parse_response(supervisor.dispatch(b'{"action":"submit"}'))
            after = {path.name for path in repo.runtime.iterdir()}
            assert not response.ok and response.reason is ReasonCode.INVALID_ARGS
            assert after - before == {"invalid-requests.jsonl"}
            line = (repo.runtime / "invalid-requests.jsonl").read_text().splitlines()[0]
            record = json.loads(line)
            assert set(record) == {
                "schema_version", "created_utc", "sha256", "reason", "detail",
            }


def _sandbox_permits_short_alias_bind(directory: Path) -> bool:
    """この sandbox が本番と同じ手順の AF_UNIX bind を許すかだけを独立に確かめる。

    capability probe が検査対象の `bind_repo_socket()` 自身を呼ぶと、108 byte 回避
    (`protocol.socket_path_alias`) の退行を「sandbox が許さない」と区別できず、
    SKIPPED + rc=0 の恒真ゲートになる ([T-138])。ここは本番実装を通さず、本番と
    同じ basename と同じ syscall 列 (socket → bind → chmod → stat → listen) を生の
    socket で踏む。名前も syscall も減らさないのは、pathname policy や listen 禁止の
    ような capability 差を本番の退行と誤認しないため — 短縮すると probe が通って
    本番だけ落ちる断面が残る。socket そのものを作れない sandbox も capability 不足で
    あって退行ではないので、例外を漏らさず False にする。

    本番 bind の前に呼ぶ前提で、作った socket file は必ず消す。消せなければ本番が
    `socket-path-exists` で偽赤になるため、その失敗は隠さず送出する。
    """
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        alias = f"/proc/self/fd/{fd}/.s"
        if not os.path.isdir(f"/proc/self/fd/{fd}") or len(os.fsencode(alias)) >= 108:
            return False
        probe = None
        created = False
        try:
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            probe.bind(alias)
            created = True
            os.chmod(".s", 0o600, dir_fd=fd, follow_symlinks=False)
            os.stat(".s", dir_fd=fd, follow_symlinks=False)
            probe.listen(1)
            return True
        except OSError:
            return False
        finally:
            if probe is not None:
                with contextlib.suppress(OSError):
                    probe.close()
            if created:
                os.unlink(".s", dir_fd=fd)
    finally:
        os.close(fd)


class _PermissiveAliasSocket:
    """capability が十分な環境を模す socket。bind は alias の実体を置くだけ。

    probe の True 側を環境に依らず固定するために使う。AF_UNIX の実挙動の検査ではない
    (それは長 path の node が担う)。
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def bind(self, alias: str) -> None:
        (self._directory / ".s").touch()

    def listen(self, backlog: int) -> None:
        pass

    def close(self) -> None:
        pass


@pytest.mark.xdist_group("dev-waves-runtime")
def test_short_alias_bind_probe_separates_capability_loss_from_regression() -> None:
    """probe の両方向を capability 非依存に固定する。

    False 側だけを固定すると、probe が常時 False へ退行したときに probe を使う node が
    そろって SKIP + rc=0 になり、[T-138] の恒真ゲートが形を変えて戻る (probe 自身を壊す
    変異ではこの性質を確かめられない)。True 側も固定して「capability があるのに False」を
    赤にする。False 側は、AF_UNIX を禁じた sandbox で受入が赤になる = 承認外の受理集合
    縮小を防ぐために要る。
    """
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for failure in (PermissionError(errno.EPERM, "seccomp"),
                        OSError(errno.EACCES, "policy")):
            with mock.patch("socket.socket", side_effect=failure):
                assert _sandbox_permits_short_alias_bind(directory) is False
        for method in ("bind", "listen"):
            with mock.patch.object(socket.socket, method,
                                   side_effect=PermissionError(errno.EPERM, "policy")):
                assert _sandbox_permits_short_alias_bind(directory) is False
        with mock.patch("socket.socket",
                        return_value=_PermissiveAliasSocket(directory)):
            assert _sandbox_permits_short_alias_bind(directory) is True
        assert not list(directory.iterdir()), "probe が socket file を残した"


@pytest.mark.xdist_group("dev-waves-runtime")
def test_socket_roundtrip_works_beyond_108_byte_repository_path() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / ("long-component-" * 8)
        root.mkdir(parents=True)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            assert len(os.fsencode(str(repo.runtime / ".s"))) >= 108
            # probe より前に Supervisor を作る — runtime dir を作るのはこの構築である。
            supervisor = _supervisor(repo)
            if not _sandbox_permits_short_alias_bind(repo.runtime):
                pytest.skip("sandbox does not permit AF_UNIX bind through /proc/self/fd")
            serve_failures: list[BaseException] = []

            def _serve() -> None:
                # serve_forever の例外を主スレッドへ回収する。thread 内で死なせると
                # pytest は warning しか出さず、bind の退行が緑で通る ([T-137])。
                try:
                    supervisor.serve_forever()
                except BaseException as exc:
                    serve_failures.append(exc)

            # 偽緑だった原因は daemon 属性ではなく生存 assertion の欠如だった ([T-137])。
            # 停止の退行は下の join + is_alive が赤にする。daemon=True は維持する —
            # 非 daemon thread は select が timeout なしに退行した場合など lease 検査へ
            # 戻らない経路で interpreter 終了を永久に阻止し、受入全走が「赤」でなく
            # 「終わらない」になる。可用性を落とさずに退行を赤にできる方を採る。
            thread = threading.Thread(target=_serve, daemon=True)
            thread.start()
            deadline = time.monotonic() + 5
            while not (repo.runtime / ".s").exists() and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.01)
            if serve_failures:
                raise AssertionError(
                    f"serve_forever が socket を開けずに落ちた: {serve_failures[0]!r}",
                ) from serve_failures[0]
            assert (repo.runtime / ".s").exists()
            raw = exchange(repo.runtime, _request(repo), timeout_s=5)
            response = parse_response(raw)
            assert response.ok and response.run_id is not None
            status, _seen = _wait_terminal(supervisor, response.run_id)
            assert status.state is RunState.COMPLETED
            supervisor.shutdown()
            # 30 秒は同ファイルの他 node (wait_idle 系) と揃えた値。5 秒だと共有ノードの
            # 高負荷で serve thread が deschedule されただけで停止契約の退行と誤判定する。
            thread.join(30)
            assert not thread.is_alive(), "shutdown() が serve ループを止めていない"
            assert not serve_failures, serve_failures


def test_linked_worktree_repo_root_resolves_common_identity_and_runtime_main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            linked = root / "linked"
            _git(repo.main, "worktree", "add", "-b", "linked-test", str(linked), "HEAD")
            main_identity = resolve_repo_identity(repo.main)
            linked_identity = resolve_repo_identity(linked)
            assert linked_identity.digest == main_identity.digest
            assert linked_identity.common_dir == main_identity.common_dir
            linked_supervisor = Supervisor(SupervisorConfig(
                str(linked), str(repo.fake), repo.fake_digest, _profile(), 15, 0.1,
            ))
            assert linked_supervisor.layout.root == repo.runtime


def test_nested_environment_rejects_serve_and_resume_but_client_can_connect() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            with _isolated_process_environment(root / "nested", nested=True):
                with pytest.raises(Exception) as captured:
                    supervisor.serve_forever()
                assert getattr(captured.value, "code", None) is ReasonCode.NESTED_LAUNCH_ENVIRONMENT


def test_settings_strict_parse_and_required_hook_wiring_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            settings = root / "settings.json"
            settings.write_text('{"hooks":{}}', encoding="utf-8")
            base = _profile()
            profile = SupervisorProfile(
                "default", "fake-model", "low", base.check_specs,
                settings_path=str(settings), required_hooks=(("Bash", "deny-push"),),
                max_waves=base.max_waves,
                max_per_wave_timeout_s=base.max_per_wave_timeout_s,
                max_total_timeout_s=base.max_total_timeout_s,
                max_per_wave_budget_usd=base.max_per_wave_budget_usd,
                max_total_budget_usd=base.max_total_budget_usd,
                max_wave_output_bytes=base.max_wave_output_bytes,
                max_run_bytes=base.max_run_bytes,
                allowed_models=base.allowed_models,
            )
            supervisor = Supervisor(SupervisorConfig(
                str(repo.main), str(repo.fake), repo.fake_digest, profile, 15, 0.1,
                runtime_dir=str(repo.runtime),
            ))
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.SETTINGS_INVALID
            assert not _invocations(repo)
            try:
                SupervisorProfile(
                    "default", "opus", "low", base.check_specs,
                    max_waves=base.max_waves,
                    max_per_wave_timeout_s=base.max_per_wave_timeout_s,
                    max_total_timeout_s=base.max_total_timeout_s,
                    max_per_wave_budget_usd=base.max_per_wave_budget_usd,
                    max_total_budget_usd=base.max_total_budget_usd,
                    max_wave_output_bytes=base.max_wave_output_bytes,
                    max_run_bytes=base.max_run_bytes,
                    allowed_models=("fake-model",),
                )
            except ValueError:
                pass
            else:
                raise AssertionError("model aliases were accepted as complete slugs")


def test_budget_accumulates_across_waves_and_deadline_boundary_is_clipped() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [
                {"scenario": "success", "cost": 0.6},
                {"scenario": "success", "cost": 0.6},
            ])
            supervisor = _supervisor(repo)
            request = _request(repo, waves=2, total_timeout=10,
                               per_wave_budget="1", total_budget="1")
            submitted = supervisor.submit(request)
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.BUDGET_INVALID
            invocations = _invocations(repo)
            assert len(invocations) == 2
            first_budget = next(
                token for token in invocations[0]["argv"]
                if token.startswith("--max-budget-usd=")
            )
            second_budget = next(
                token for token in invocations[1]["argv"]
                if token.startswith("--max-budget-usd=")
            )
            assert first_budget == "--max-budget-usd=1"
            assert second_budget == "--max-budget-usd=0.4"
            events = [json.loads(line) for line in (
                repo.runtime / submitted.run_id / "events.jsonl"
            ).read_text().splitlines()]
            assert sum(event["state"] == "wave-accepted" for event in events) == 1


def test_max_run_bytes_counts_wal_and_all_artifacts_but_excludes_git_worktree() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            invalid = _request(repo, output_bytes=32 * 1024, run_bytes=96 * 1024 - 1)
            with pytest.raises(DevWavesError) as captured:
                supervisor.submit(invalid)
            assert captured.value.code is ReasonCode.BUDGET_INVALID
            assert not any(path.name.startswith("dw-") for path in repo.runtime.iterdir())

            cap = 512 * 1024
            submitted = supervisor.submit(_request(
                repo, output_bytes=64 * 1024, run_bytes=cap,
            ))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.COMPLETED
            run = repo.runtime / submitted.run_id
            measured = supervisor._run_artifact_bytes(submitted.run_id)
            assert measured <= cap
            worktree = run / "worktrees" / "w001"
            assert worktree.is_dir()
            (worktree / "excluded-large.bin").write_bytes(b"x" * (cap + 1))
            assert supervisor._run_artifact_bytes(submitted.run_id) == measured


@contextlib.contextmanager
def _vanishing_entry(run: Path, name: str, size: int) -> Iterator[None]:
    """Make ``name`` exist when ``os.walk`` lists it and be gone at ``lstat``.

    This is the real failure shape: the ledger thread renames its rewrite
    scratch away between the supervisor's listing of a directory and the stat
    of each entry in it.
    """
    victim = run / name
    victim.write_bytes(b"x" * size)
    real_walk = os.walk

    def vanishing_walk(top, *args, **kwargs):
        for directory, names, files in real_walk(top, *args, **kwargs):
            if Path(directory) == run and victim.name in files:
                victim.unlink()
            yield directory, names, files

    with mock.patch.object(daemon_mod.os, "walk", vanishing_walk):
        yield


@pytest.mark.xdist_group("dev-waves-runtime")
def test_vanished_rewrite_scratch_is_skipped_but_lost_artifact_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(
                repo, output_bytes=64 * 1024, run_bytes=512 * 1024,
            ))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.COMPLETED
            run = repo.runtime / submitted.run_id
            measured = supervisor._run_artifact_bytes(submitted.run_id)

            # The ledger's own scratch owes no bytes once it has been renamed.
            scratch = cache_transient_name(STATUS_NAME)
            with _vanishing_entry(run, scratch, 4096):
                assert supervisor._run_artifact_bytes(submitted.run_id) == measured
            assert not (run / scratch).exists()

            # Anything else is create-only: losing it is a typed failure, not a
            # bare FileNotFoundError escaping the measurement.  The last name
            # wears the scratch suffix over a base that is never rewritten, so
            # a recognizer that matched on shape alone would wrongly skip it.
            for name in (STATUS_NAME, "events.jsonl", "durable-artifact.json",
                         f"events.jsonl.tmp.{os.getpid()}.1"):
                with _vanishing_entry(run, name, 4096):
                    with pytest.raises(DevWavesError) as captured:
                        supervisor._run_artifact_bytes(submitted.run_id)
                assert captured.value.code is ReasonCode.RUNTIME_IO_FAILURE
                assert captured.value.detail["kind"] == "vanished-artifact"


@pytest.mark.xdist_group("dev-waves-runtime")
def test_capacity_gate_stays_closed_when_an_artifact_vanishes_mid_measure() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(
                repo, output_bytes=64 * 1024, run_bytes=512 * 1024,
            ))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.COMPLETED
            run = repo.runtime / submitted.run_id
            with _vanishing_entry(run, "durable-artifact.json", 4096):
                with pytest.raises(DevWavesError) as captured:
                    supervisor._enforce_run_capacity(submitted.run_id, 512 * 1024)
            assert captured.value.code is ReasonCode.RUNTIME_IO_FAILURE


def test_artifact_aggregate_cap_stops_before_next_wave_side_effect() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{
                "scenario": "artifact_cap", "artifact_bytes": 70000,
            }])
            supervisor = _supervisor(repo)
            cap = 128 * 1024
            submitted = supervisor.submit(_request(
                repo, output_bytes=32 * 1024, run_bytes=cap,
            ))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert (status.state, status.reason) == (
                RunState.FAILED, ReasonCode.BUDGET_INVALID,
            )
            run = repo.runtime / submitted.run_id
            assert supervisor._run_artifact_bytes(submitted.run_id) > cap
            assert not (run / "waves" / "001" / "checks.json").exists()
            events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
            assert not any(item["state"] == RunState.CHILD_EXITED.value for item in events)


def test_expired_deadline_prevents_next_real_artifact_side_effect() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            entries = []
            supervisor = _supervisor(repo, dependencies=SupervisorDependencies(
                side_effect_hook=entries.append,
            ))
            run_id = "dw-deadline-counter"
            run = supervisor.layout.run_dir(run_id)
            run.mkdir()
            supervisor._active = mock.Mock(
                cancel=threading.Event(), cancel_reason=ReasonCode.SIGNAL_RECEIVED,
            )
            deadline = mock.Mock()
            deadline.remaining_ns.side_effect = [1, 0]
            first = run / "first.json"
            second = run / "second.json"
            supervisor._create_wave_json(deadline, run_id, 1024, first, {"n": 1})
            with pytest.raises(DevWavesError) as captured:
                supervisor._create_wave_json(deadline, run_id, 1024, second, {"n": 2})
            assert captured.value.code is ReasonCode.TIMEOUT
            assert first.exists() and not second.exists()
            assert entries == ["artifact-write"]
            supervisor._active = None


@pytest.mark.parametrize(
    "scenario,waves,terminal,reason",
    [
        ("success", 1, RunState.COMPLETED, ReasonCode.MAX_WAVES_REACHED),
        ("no_actionable_task", 2, RunState.COMPLETED, ReasonCode.NO_ACTIONABLE_TASK),
        ("user_ruling_required", 2, RunState.BLOCKED, ReasonCode.USER_RULING_REQUIRED),
        ("blocked", 2, RunState.BLOCKED, ReasonCode.CHECK_FAILED),
        ("failed", 2, RunState.FAILED, ReasonCode.NONZERO_EXIT),
    ],
)
def test_each_outcome_has_one_terminal_mapping_and_never_starts_next_child(
    scenario: str, waves: int, terminal: RunState, reason: ReasonCode,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [scenario, "success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(
                repo, waves=waves, total_timeout=waves * 5,
                total_budget=str(waves),
            ))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert (status.state, status.reason) == (terminal, reason)
            assert len(_invocations(repo)) == 1


def test_blocked_receipt_with_main_move_is_failed_not_blocked() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["blocked_main_moved"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.FAILED
            assert status.reason is ReasonCode.MAIN_MOVED


def test_spawn_identity_read_failure_kills_and_reaps_exact_popen() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{"scenario": "sleep_timeout", "sleep_s": 60}])
            spawned = []

            def capture_spawn(*args, **kwargs):
                process = real_spawn_worker(*args, **kwargs)
                spawned.append(process)
                return process

            supervisor = _supervisor(repo, dependencies=SupervisorDependencies(
                spawn_worker_fn=capture_spawn,
            ))
            with mock.patch(
                "tools.dev_waves.daemon.read_pid_identity", side_effect=OSError("injected"),
            ):
                submitted = supervisor.submit(_request(repo))
                status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.FAILED
            assert status.reason is ReasonCode.SPAWN_FAILED
            assert len(spawned) == 1 and spawned[0].poll() is not None


def test_cancel_identity_mismatch_records_ambiguous_not_signalled() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{"scenario": "sleep_timeout", "sleep_s": 60}])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo, per_wave_timeout=10))
            _wait_state(supervisor, submitted.run_id, RunState.CHILD_RUNNING, 1)
            with mock.patch(
                "tools.dev_waves.daemon.terminate_verified_group", return_value=False,
            ):
                supervisor.cancel(submitted.run_id)
            status = supervisor.status(submitted.run_id)
            assert (status.state, status.reason) == (
                RunState.FAILED, ReasonCode.AMBIGUOUS_RECOVERY,
            )
            events = [json.loads(line) for line in (
                repo.runtime / submitted.run_id / "events.jsonl"
            ).read_text().splitlines()]
            observations = [
                item["data"]["observed"]["status"] for item in events
                if item.get("operation_id") == "w001-cancel" and
                item["event"] == "side_effect_observed"
            ]
            assert observations == ["ambiguous"]
            with supervisor._lock:
                process = supervisor._active.worker if supervisor._active else None
            if process is not None:
                kill_spawned_process(process)
            deadline = time.monotonic() + 5
            while supervisor._active is not None and time.monotonic() < deadline:
                time.sleep(0.01)
            assert supervisor._active is None
            # The run thread clears ``_active`` from inside its own finally and
            # only then releases the run, so this alone is not quiescence.
            assert supervisor.wait_idle(30)


def test_wal_partial_tail_validate_is_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            _wait_terminal(supervisor, submitted.run_id)
            wal = repo.runtime / submitted.run_id / "events.jsonl"
            with wal.open("ab") as stream:
                stream.write(b'{"schema_version":1')
                stream.flush(); os.fsync(stream.fileno())
            with pytest.raises(Exception):
                supervisor.validate(submitted.run_id)


@pytest.mark.parametrize("mode,expected_spawns", [("before-spawn", 0), ("after-spawn", 1)])
def test_supervisor_wal_fsync_failure_orders_real_worker_spawn_side_effect(
    mode: str, expected_spawns: int,
) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, [{"scenario": "sleep_timeout", "sleep_s": 2}])
            fsync_calls = 0
            spawns = 0
            armed = False
            failed = False

            def injected_fsync(fd: int) -> None:
                nonlocal fsync_calls, failed
                try:
                    target = os.readlink(f"/proc/self/fd/{fd}")
                except OSError:
                    target = ""
                if not target.endswith("/events.jsonl"):
                    os.fsync(fd)
                    return
                fsync_calls += 1
                should_fail = (
                    mode == "before-spawn" and fsync_calls == 7 or
                    mode == "after-spawn" and armed and not failed
                )
                if should_fail:
                    failed = True
                    raise OSError(errno.EIO, "injected WAL fsync")
                os.fsync(fd)

            from tools.dev_waves.worker import spawn_worker as real_spawn_worker

            def counted_spawn(*args, **kwargs):
                nonlocal spawns, armed
                spawns += 1
                process = real_spawn_worker(*args, **kwargs)
                armed = True
                return process

            supervisor = _supervisor(repo, dependencies=SupervisorDependencies(
                spawn_worker_fn=counted_spawn, ledger_fsync=injected_fsync,
            ))
            submitted = supervisor.submit(_request(repo, per_wave_timeout=5))
            deadline = time.monotonic() + 5
            status = supervisor.status(submitted.run_id)
            while status.reason is not ReasonCode.POISONED and time.monotonic() < deadline:
                time.sleep(0.01)
                status = supervisor.status(submitted.run_id)
            assert status.reason is ReasonCode.POISONED, (
                status, fsync_calls, spawns, failed,
                (repo.runtime / submitted.run_id / "emergency-stop.json").exists(),
            )
            assert spawns == expected_spawns
            inactive_deadline = time.monotonic() + 5
            while supervisor._active is not None and time.monotonic() < inactive_deadline:
                time.sleep(0.01)
            assert supervisor._active is None
            # See ``_wait_terminal``: quiescence is a separate observation.
            assert supervisor.wait_idle(30)
            with pytest.raises(DevWavesError) as same_instance:
                supervisor.submit(_request(repo))
            assert same_instance.value.code is ReasonCode.AMBIGUOUS_RECOVERY
            restarted = _supervisor(repo)
            with pytest.raises(DevWavesError) as captured:
                restarted.submit(_request(repo))
            assert captured.value.code is ReasonCode.AMBIGUOUS_RECOVERY


def test_supervisor_command_audit_contains_no_cleanup_land_or_push_api() -> None:
    source = (_REPO / "tools" / "dev_waves" / "daemon.py").read_text(encoding="utf-8")
    forbidden = (
        "worktree remove", "branch -D", "branch --delete", "submodule deinit",
        "git push", "git rebase", "git merge",
    )
    assert not any(token in source for token in forbidden)


def test_auto_unavailable_or_permission_abort_never_rebuilds_dangerous_argv() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["permission_abort"], help_variant="auto-unavailable")
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.FLAG_UNAVAILABLE
            assert not _invocations(repo)
        with _isolated_process_environment(root / "permission-case"):
            repo = _temporary_repo(root / "permission-case", ["permission_abort"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.reason is ReasonCode.PERMISSION_ABORT
            argv = _invocations(repo)[0]["argv"]
            assert "--permission-mode=auto" in argv
            assert not any("dangerously" in token or "bypass" in token or "dontAsk" in token
                           for token in argv)


@pytest.mark.xdist_group("dev-waves-runtime")
def test_wait_idle_is_bound_to_the_run_thread_and_reports_timeout_without_raising() -> None:
    """静止の観測は run スレッドの生死に束縛される (``_active`` の消滅ではない)。

    ``_active`` は run スレッドが自分の finally の中で消すので、それが None に
    なった時点ではまだ run の資源 (WAL writer・status の scratch・fd と lock) が
    握られている。``wait_idle`` はスレッドそのものを待つ。
    """
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            # run を 1 つも起こしていない supervisor は既に静止している。
            assert supervisor.wait_idle(0) is True

            started = threading.Event()
            release = threading.Event()

            def _body() -> None:
                started.set()
                release.wait(30)

            thread = threading.Thread(target=_body, name="dev-waves-probe", daemon=False)
            supervisor._last_run_thread = thread
            thread.start()
            try:
                assert started.wait(5)
                # 走っている限り False を返す。例外にはしない (timeout の意味は呼び手が決める)。
                assert supervisor.wait_idle(0.05) is False
            finally:
                release.set()
                thread.join(30)
            assert supervisor.wait_idle(5) is True


def test_terminal_state_precedes_quiescence_and_wait_idle_leaves_no_run_thread() -> None:
    """terminal 観測の後も残っていた run/WAL スレッドが、静止待ちの後には居ない。

    この 2 本のスレッド (``dev-waves-<run_id>`` と ``dev-waves-wal-<run_id>``) が
    terminal 観測直後に生き残ることが、temp tree を消す側から見た
    ``OSError: Directory not empty`` の実体だった。
    """
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with _isolated_process_environment(root):
            repo = _temporary_repo(root, ["success"])
            supervisor = _supervisor(repo)
            submitted = supervisor.submit(_request(repo))
            # 静止待ちの配線そのものを撃つ: submit が run スレッドを記録しなければ
            # wait_idle は無条件に True を返し、下の lingering 検査は競合次第でしか
            # 落ちなくなる (偽 SURVIVED になる変異を決定的に赤くする)。
            assert supervisor._last_run_thread is not None
            status, _seen = _wait_terminal(supervisor, submitted.run_id)
            assert status.state is RunState.COMPLETED
            lingering = [
                thread.name for thread in threading.enumerate()
                if thread.name in (
                    f"dev-waves-{submitted.run_id}",
                    f"dev-waves-wal-{submitted.run_id}",
                )
            ]
            assert lingering == [], lingering


def _run() -> int:
    # Parametrized failure and crash matrices must retain their pytest fixture
    # semantics; invoking pytest here gives the plain runner the identical node
    # set rather than a reduced smoke subset.
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
