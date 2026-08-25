# -*- coding: utf-8 -*-
"""resume の session-start gate と acceptance merge の時系列境界を検査する。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import textwrap

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_WAVE = "resume-acceptance-boundary"
_BRANCH = f"worktree-{_WAVE}"
_MESSAGE = (
    b"merge main after session-start gate\n\n"
    b"AI-Agent: product=codex; model=gpt-5; reasoning=high; role=author\n"
)
_ATTEMPT_PREFIX = "IZANAGI_ACCEPTANCE_ATTEMPT_V1 "


def _run_bounded(
    argv: list[str],
    *,
    repo: Path,
    env: dict[str, str],
    text: bool = True,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess:
    process = subprocess.Popen(
        argv,
        cwd=repo,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = process.communicate(timeout=2.0)
            except subprocess.TimeoutExpired as final_exc:
                raise AssertionError(
                    f"subprocess did not exit after SIGKILL: {argv!r}; "
                    f"stdout={final_exc.output!r}; stderr={final_exc.stderr!r}"
                ) from exc
        raise AssertionError(
            f"subprocess timed out: {argv!r}; stdout={stdout!r}; stderr={stderr!r}"
        ) from exc
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


def _git(
    repo: Path,
    env: dict[str, str],
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = _run_bounded(["git", *args], repo=repo, env=env)
    if check:
        assert completed.returncode == 0, (args, completed.stdout, completed.stderr)
    return completed


def _git_text(repo: Path, env: dict[str, str], *args: str) -> str:
    return _git(repo, env, *args).stdout.strip()


def _git_blob(repo: Path, env: dict[str, str], revision: str, path: str) -> bytes:
    completed = _run_bounded(
        ["git", "cat-file", "blob", f"{revision}:{path}"],
        repo=repo,
        env=env,
        text=False,
    )
    assert completed.returncode == 0, (path, completed.stderr)
    return completed.stdout


def _write_provenance_checker(repo: Path) -> None:
    (repo / "tools" / "check_ai_provenance.py").write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--message-file', type=Path)\n"
        "args = parser.parse_args()\n"
        "trailer = ('AI-Agent: product=codex; model=gpt-5; reasoning=high; '"
        "           'role=author')\n"
        "if args.message_file is not None and trailer not in "
        "args.message_file.read_text(encoding='utf-8'):\n"
        "    raise SystemExit(1)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )


def _write_runner(
    repo: Path,
    *,
    state_file: Path,
    phase_file: Path,
    counter_file: Path,
) -> None:
    source = f'''\
def main(argv):
    del argv
    import json
    from pathlib import Path
    import subprocess

    phase = Path({str(phase_file)!r})
    with phase.open("ab") as stream:
        stream.write(b"started\\n")
    counter = Path({str(counter_file)!r})
    with counter.open("ab") as stream:
        stream.write(b"run\\n")
    state = json.loads(Path({str(state_file)!r}).read_text(encoding="ascii"))
    repo = Path(state["repo"])
    if Path.cwd().resolve() != repo:
        raise SystemExit("child cwd mismatch")

    def run(*args, text=True):
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
            check=False,
        )

    behind = run("rev-list", "--count", "HEAD..main")
    if behind.returncode != 0 or behind.stdout.strip() != "0":
        raise SystemExit("child behind check failed")
    status = run(
        "status", "--porcelain", "--untracked-files=all",
        "--ignore-submodules=none",
    )
    if status.returncode != 0 or status.stdout != "":
        raise SystemExit("child clean check failed")
    merge_state = run("rev-parse", "-q", "--verify", "MERGE_HEAD")
    if merge_state.returncode != 1:
        raise SystemExit("child MERGE_HEAD check failed")
    commit = run("cat-file", "commit", "HEAD", text=False)
    if commit.returncode != 0:
        raise SystemExit("child commit read failed")
    header, separator, body = commit.stdout.partition(b"\\n\\n")
    if separator != b"\\n\\n":
        raise SystemExit("child commit framing failed")
    parents = [
        line.split(b" ", 1)[1].decode("ascii")
        for line in header.splitlines()
        if line.startswith(b"parent ")
    ]
    if parents != [state["wave_head"], state["main_tip"]]:
        raise SystemExit("child merge parents mismatch")
    if body != bytes.fromhex(state["message_hex"]):
        raise SystemExit("child commit message mismatch")
    with phase.open("ab") as stream:
        stream.write(b"verified\\n")
    print(
        'IZANAGI_EFFECTIVE_SCHEDULER_V1 '
        '{{"effective_scheduler":"serial"}}'
    )
    return 0
'''
    (repo / "tools" / "run_tests.py").write_text(
        textwrap.dedent(source), encoding="utf-8"
    )


def _tool_environment(repo: Path) -> dict[str, str]:
    git_path = shutil.which("git")
    python_path = shutil.which("python3")
    assert git_path is not None
    assert python_path is not None
    git_executable = Path(git_path).resolve()
    python_executable = Path(python_path).resolve()
    assert git_executable.is_file()
    assert python_executable.is_file()
    path_dirs = list(
        dict.fromkeys((str(git_executable.parent), str(python_executable.parent)))
    )
    env = {
        "PATH": os.pathsep.join(path_dirs),
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_AUTHOR_NAME": "Boundary Test",
        "GIT_AUTHOR_EMAIL": "boundary@example.invalid",
        "GIT_COMMITTER_NAME": "Boundary Test",
        "GIT_COMMITTER_EMAIL": "boundary@example.invalid",
    }
    assert "IZANAGI_WAVE_LEASE_DIR" not in env
    assert "PYTEST_ADDOPTS" not in env
    assert "PYTEST_PLUGINS" not in env
    resolved_git = shutil.which("git", path=env["PATH"])
    resolved_python = shutil.which("python3", path=env["PATH"])
    assert resolved_git is not None
    assert resolved_python is not None
    assert Path(resolved_git).samefile(git_executable)
    assert Path(resolved_python).samefile(python_executable)
    for executable in (git_executable, python_executable):
        verified = _run_bounded(
            [str(executable), "--version"], repo=repo, env=env, timeout=5.0
        )
        assert verified.returncode == 0, verified.stderr
    trusted_blob_git = Path("/usr/bin/git")
    assert trusted_blob_git.is_file(), "/usr/bin/git is required by dev_wave_wait.py"
    trusted_git_version = _run_bounded(
        [str(trusted_blob_git), "--version"],
        repo=repo,
        env=env,
        timeout=5.0,
    )
    assert trusted_git_version.returncode == 0, trusted_git_version.stderr
    return env


def test_resume_gate_then_postclaim_merge_runs_runner_once(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    assert list(lease_dir.iterdir()) == []
    env = _tool_environment(repo)

    tools = repo / "tools"
    tools.mkdir()
    for name in (
        "dev_wave_wait.py",
        "wave_land_window.py",
        "acceptance_launcher.py",
        "check_wave_startup.py",
    ):
        shutil.copy2(_ROOT / "tools" / name, tools / name)
    _write_provenance_checker(repo)
    state_file = tmp_path / "child-state.json"
    phase_file = tmp_path / "child-phase.txt"
    counter_file = tmp_path / "child-counter.txt"
    _write_runner(
        repo,
        state_file=state_file,
        phase_file=phase_file,
        counter_file=counter_file,
    )

    marker = repo / "external" / "ccbench" / "CMakeLists.txt"
    marker.parent.mkdir(parents=True)
    marker.write_text("# fixture\n", encoding="utf-8")
    handoff = repo / "docs" / "handoff"
    handoff.mkdir(parents=True)
    (handoff / "README.md").write_text("# handoff\n", encoding="utf-8")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")

    _git(repo, env, "init", "-q", "-b", "main", ".")
    for key, value in (
        ("user.name", "Boundary Test"),
        ("user.email", "boundary@example.invalid"),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", "/dev/null"),
        ("core.fsmonitor", "false"),
    ):
        _git(repo, env, "config", "--local", key, value)
    _git(repo, env, "add", ".")
    _git(repo, env, "commit", "-qm", "base")
    _git(repo, env, "checkout", "-qb", _BRANCH)
    (marker.parent / ".git").write_text("gitdir: fixture\n", encoding="utf-8")

    (repo / "wave-only.txt").write_text("wave\n", encoding="utf-8")
    _git(repo, env, "add", "wave-only.txt")
    _git(repo, env, "commit", "-qm", "wave ahead")
    assert _git_text(repo, env, "rev-list", "--count", "HEAD..main") == "0"
    assert _git_text(repo, env, "rev-list", "--count", "main..HEAD") == "1"
    assert _git_text(repo, env, "rev-parse", "HEAD") != _git_text(
        repo, env, "rev-parse", "main"
    )
    assert _git(repo, env, "status", "--porcelain").stdout == ""

    gate = _run_bounded(
        [
            "python3",
            "tools/check_wave_startup.py",
            "--repo",
            str(repo),
            "--mode",
            "resume",
        ],
        repo=repo,
        env=env,
    )
    assert gate.returncode == 0, gate.stderr
    assert gate.stderr == ""
    assert "OK:" in gate.stdout
    assert f"(resume; repo={repo.resolve()};" in gate.stdout
    assert "NG:" not in gate.stdout
    wave_head = _git_text(repo, env, "rev-parse", "HEAD")
    gate_main = _git_text(repo, env, "rev-parse", "main")

    _git(repo, env, "checkout", "-q", "main")
    (repo / "main-advance.txt").write_text("main advanced\n", encoding="utf-8")
    _git(repo, env, "add", "main-advance.txt")
    _git(repo, env, "commit", "-qm", "advance main")
    main_tip = _git_text(repo, env, "rev-parse", "main")
    _git(repo, env, "checkout", "-q", _BRANCH)

    assert _git_text(repo, env, "rev-list", "--count", "HEAD..main") == "1"
    assert _git_text(repo, env, "rev-list", "--count", "main..HEAD") == "1"
    assert _git_text(repo, env, "rev-parse", "HEAD") == wave_head
    assert _git_text(repo, env, "rev-parse", f"{main_tip}^") == gate_main
    assert _git_text(repo, env, "merge-base", wave_head, main_tip) == gate_main
    assert _git(repo, env, "status", "--porcelain").stdout == ""

    neutral_blobs: dict[str, bytes] = {}
    main_blobs: dict[str, bytes] = {}
    for path in (
        "tools/dev_wave_wait.py",
        "tools/acceptance_launcher.py",
        "tools/run_tests.py",
    ):
        wave_bytes = _git_blob(repo, env, wave_head, path)
        main_bytes = _git_blob(repo, env, main_tip, path)
        assert wave_bytes == main_bytes
        neutral_blobs[path] = wave_bytes
        main_blobs[path] = main_bytes
    changed = _git(repo, env, "diff", "--name-only", f"{wave_head}...{main_tip}")
    assert changed.stdout.splitlines() == ["main-advance.txt"]

    message_file = tmp_path / "merge-message.txt"
    message_file.write_bytes(_MESSAGE)
    receipt_file = tmp_path / "acceptance-receipt.json"
    log_file = tmp_path / "acceptance.log"
    for absent in (receipt_file, log_file, counter_file, phase_file):
        assert not absent.exists()
    state_file.write_text(
        json.dumps(
            {
                "repo": str(repo.resolve()),
                "wave_head": wave_head,
                "main_tip": main_tip,
                "message_hex": _MESSAGE.hex(),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        + "\n",
        encoding="ascii",
    )
    message_before = message_file.read_bytes()

    waiter = _run_bounded(
        [
            "python3",
            "tools/dev_wave_wait.py",
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(lease_dir),
            "--receipt-file",
            str(receipt_file),
            "--log-file",
            str(log_file),
            "--merge-message-file",
            str(message_file),
            "--max-wait-seconds",
            "60",
            "--",
            "python3",
            "tools/run_tests.py",
        ],
        repo=repo,
        env=env,
        timeout=45.0,
    )
    assert waiter.returncode == 0, (waiter.stdout, waiter.stderr)
    assert phase_file.read_bytes() == b"started\nverified\n"
    assert counter_file.read_bytes() == b"run\n"

    merge_head = _git_text(repo, env, "rev-parse", "HEAD")
    assert merge_head not in {wave_head, main_tip}
    commit = _run_bounded(
        ["git", "cat-file", "commit", merge_head],
        repo=repo,
        env=env,
        text=False,
    )
    assert commit.returncode == 0, commit.stderr
    header, separator, body = commit.stdout.partition(b"\n\n")
    assert separator == b"\n\n"
    parents = [
        line.split(b" ", 1)[1].decode("ascii")
        for line in header.splitlines()
        if line.startswith(b"parent ")
    ]
    assert len(parents) == 2
    assert parents[0] == wave_head
    assert parents[1] == main_tip
    assert body == _MESSAGE
    assert message_before == _MESSAGE
    assert message_file.read_bytes() == message_before
    assert _git_text(repo, env, "rev-list", "--count", "HEAD..main") == "0"
    assert _git(
        repo,
        env,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--ignore-submodules=none",
    ).stdout == ""
    merge_state = _git(
        repo, env, "rev-parse", "-q", "--verify", "MERGE_HEAD", check=False
    )
    assert merge_state.returncode == 1

    receipt = json.loads(receipt_file.read_text(encoding="ascii"))
    assert receipt["child_rc"] == 0
    assert receipt["verdict"] == "child-green"
    assert receipt["argv"] == ["python3", "tools/run_tests.py"]
    assert receipt["tested_main"] == main_tip
    assert receipt["tested_tip"] == merge_head
    assert receipt["launcher_source_revision"] == "tested-main"
    assert receipt["authority_kind"] == "dev-wave-acceptance-launcher"
    assert receipt["launcher_blob_sha"] == _git_text(
        repo, env, "rev-parse", f"{main_tip}:tools/acceptance_launcher.py"
    )
    assert receipt["waiter_executed_sha256"] == hashlib.sha256(
        neutral_blobs["tools/dev_wave_wait.py"]
    ).hexdigest()
    assert receipt["runner_executed_sha256"] == hashlib.sha256(
        neutral_blobs["tools/run_tests.py"]
    ).hexdigest()
    assert receipt["launcher_executed_sha256"] == hashlib.sha256(
        main_blobs["tools/acceptance_launcher.py"]
    ).hexdigest()

    journals = [
        json.loads(line.removeprefix(_ATTEMPT_PREFIX))
        for line in waiter.stderr.splitlines()
        if line.startswith(_ATTEMPT_PREFIX)
    ]
    assert len(journals) == 1
    journal = journals[0]
    assert journal["attempt"] == 1
    assert journal["classification"] == "child-green"
    assert journal["raw_child_rc"] == 0
    assert journal["normalized_child_rc"] == 0
    assert journal["retry"] is False


if __name__ == "__main__":
    os.environ.pop("PYTEST_ADDOPTS", None)
    os.environ.pop("PYTEST_PLUGINS", None)
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    raise SystemExit(pytest.main([__file__]))
