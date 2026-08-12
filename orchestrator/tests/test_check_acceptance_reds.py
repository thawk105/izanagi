# -*- coding: utf-8 -*-
"""受入赤の実測帰属 checker の fail-closed 契約。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_CHECKER = _ROOT / "tools" / "check_acceptance_reds.py"
_SPEC = importlib.util.spec_from_file_location(
    "check_acceptance_reds_under_test", _CHECKER
)
assert _SPEC and _SPEC.loader
CAR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CAR)

_NON_ATTRIBUTABLE = "orchestrator/tests/test_example.py::test_non_attributable"
_ATTRIBUTABLE_A = "orchestrator/tests/test_example.py::test_attributable_a"
_ATTRIBUTABLE_B = "orchestrator/tests/test_example.py::test_attributable_b"


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def committed_repo(tmp_path: Path) -> tuple[Path, str, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    tools = repo / "tools"
    tools.mkdir()
    collected = "\n".join(
        (
            _NON_ATTRIBUTABLE,
            "orchestrator/tests/test_example.py::test_non_attributable_two",
            _ATTRIBUTABLE_A,
            _ATTRIBUTABLE_B,
            "orchestrator/tests/test_example.py::test_target",
            "orchestrator/tests/test_example.py::test_target@literal",
            "orchestrator/tests/test_example.py::test_target - literal",
        )
    )
    (tools / "run_tests.py").write_text(
        "import sys\n"
        f"COLLECTED = {collected!r}\n"
        "if '--collect-only' in sys.argv:\n"
        "    print(COLLECTED)\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(99)\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".gitignore", "tracked.txt", "tools/run_tests.py")
    _git(
        repo,
        "-c",
        "user.name=Acceptance Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    _git(repo, "branch", "-M", "main")
    tested_main = _git(repo, "rev-parse", "HEAD").stdout.strip()
    probe_root = tmp_path / "probes"
    probe_root.mkdir()
    return repo, tested_main, probe_root


def _commit_fixture(repo: Path, message: str) -> str:
    _git(
        repo,
        "-c",
        "user.name=Acceptance Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qam",
        message,
    )
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _add_initialized_submodule(repo: Path, tmp_path: Path) -> tuple[str, str, Path]:
    path_text = "external/dependency"
    source = tmp_path / "dependency-source"
    source.mkdir()
    _git(source, "init", "-q")
    (source / "dependency.txt").write_text("cached dependency\n", encoding="utf-8")
    _git(source, "add", "dependency.txt")
    _git(
        source,
        "-c",
        "user.name=Acceptance Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "dependency fixture",
    )
    _git(
        repo,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-q",
        str(source),
        path_text,
    )
    tested_main = _commit_fixture(repo, "add initialized dependency")
    common_dir = Path(
        _git(
            repo, "rev-parse", "--path-format=absolute", "--git-common-dir"
        ).stdout.strip()
    )
    return tested_main, path_text, common_dir / "modules" / path_text


def _add_uninitialized_submodule(repo: Path) -> tuple[str, str]:
    path_text = "external/uninitialized"
    object_id = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / ".gitmodules").write_text(
        '[submodule "external/uninitialized"]\n'
        "\tpath = external/uninitialized\n"
        "\turl = https://example.invalid/uninitialized.git\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".gitmodules")
    _git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{object_id},{path_text}",
    )
    return _commit_fixture(repo, "add uninitialized dependency"), path_text


def _summary_log(
    outcomes: Sequence[tuple[str, str]],
    *,
    terminal: str | None = None,
    dispatch_prefix: bool = False,
) -> str:
    failed = sum(outcome == "FAILED" for outcome, _ in outcomes)
    errors = sum(outcome == "ERROR" for outcome, _ in outcomes)
    counts: list[str] = []
    if failed:
        counts.append(f"{failed} failed")
    if errors:
        counts.append(f"{errors} {'error' if errors == 1 else 'errors'}")
    if not counts:
        counts.extend(("1 passed", "1 skipped"))
    final = terminal if terminal is not None else ", ".join(counts) + " in 0.01s"
    lines = ["================ short test summary info ================"]
    lines.extend(f"{outcome} {nodeid} - fixture detail" for outcome, nodeid in outcomes)
    if not outcomes:
        lines.append("SKIPPED orchestrator/tests/test_example.py::test_skip - fixture")
    lines.append(f"================ {final} ================")
    if dispatch_prefix:
        lines = [f"| {line}" for line in lines]
        lines.insert(0, "[Pegasus dispatch] request fixture child stdout begin")
        lines.append("[Pegasus dispatch] request fixture child stdout end")
    return "\n".join(lines) + "\n"


def _write_log(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "acceptance.log"
    path.write_text(text, encoding="utf-8")
    return path


def _arguments(
    log: Path,
    tested_main: str,
    receipt: Path,
    probe_root: Path,
    *,
    wave_tip: str | None = None,
) -> list[str]:
    return [
        "--log",
        str(log),
        "--tested-main",
        tested_main,
        "--wave-tip",
        tested_main if wave_tip is None else wave_tip,
        "--receipt",
        str(receipt),
        "--probe-root",
        str(probe_root),
    ]


def _unexpected_runner(_worktree: Path, nodeid: str) -> int:
    raise AssertionError(f"runner must not be reached: {nodeid}")


def test_green_log_returns_zero(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log(()))
    receipt = tmp_path / "green-receipt.json"
    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 0
    assert capsys.readouterr().out.splitlines() == ["status=green"]
    assert json.loads(receipt.read_text(encoding="utf-8"))["nodes"] == []


def test_truncated_log_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path,
        "================ short test summary info ================\n"
        f"FAILED {_NON_ATTRIBUTABLE} - fixture detail\n",
    )
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
    ) == 2


def test_missing_short_summary_with_green_counts_returns_zero(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, "================ 1 passed in 0.01s ================\n")
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
    ) == 0


def test_missing_short_summary_and_terminal_counts_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, "ordinary pytest output without a summary\n")
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_missing_short_summary_with_red_counts_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, "================ 1 failed in 0.01s ================\n")
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_count_mismatch_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path,
        _summary_log(
            (("FAILED", _NON_ATTRIBUTABLE),), terminal="2 failed in 0.01s"
        ),
    )
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
    ) == 2


def test_duplicate_nodeid_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path,
        _summary_log(
            (
                ("FAILED", _NON_ATTRIBUTABLE),
                ("FAILED", _NON_ATTRIBUTABLE),
            )
        ),
    )
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
    ) == 2


def test_two_summary_blocks_fail_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log(()) + _summary_log(()))
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


@pytest.mark.parametrize("position", ["before", "after"])
def test_red_outcome_outside_summary_block_fails_closed(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    position: str,
) -> None:
    repo, tested_main, probe_root = committed_repo
    red = f"FAILED {_NON_ATTRIBUTABLE} - outside block\n"
    green = _summary_log(())
    log = _write_log(tmp_path, red + green if position == "before" else green + red)
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_red_outcome_without_summary_block_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path,
        f"FAILED {_NON_ATTRIBUTABLE} - outside block\n"
        "================ 1 passed in 0.01s ================\n",
    )
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_dispatch_prefix_is_exactly_supported(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((), dispatch_prefix=True))
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 0


def test_all_non_attributable_reds_return_zero(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    second = "orchestrator/tests/test_example.py::test_non_attributable_two"
    log = _write_log(
        tmp_path,
        _summary_log(
            (("FAILED", second), ("ERROR", _NON_ATTRIBUTABLE))
        ),
    )
    receipt = tmp_path / "receipt.json"
    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
    ) == 0
    assert capsys.readouterr().out.splitlines() == [
        "status=non-attributable-only"
    ]
    document = json.loads(receipt.read_text(encoding="utf-8"))
    assert {node["classification"] for node in document["nodes"]} == {
        "non-attributable"
    }


def test_attributable_red_stops_even_beside_non_attributable(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path,
        _summary_log(
            (
                ("FAILED", _ATTRIBUTABLE_B),
                ("FAILED", _NON_ATTRIBUTABLE),
                ("ERROR", _ATTRIBUTABLE_A),
            )
        ),
    )
    outcomes = {
        _NON_ATTRIBUTABLE: 1,
        _ATTRIBUTABLE_A: 0,
        _ATTRIBUTABLE_B: 0,
    }
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, nodeid: outcomes[nodeid],
    ) == 1
    assert capsys.readouterr().out.splitlines() == [
        "status=attributable-red",
        f"attributable={_ATTRIBUTABLE_A}",
        f"attributable={_ATTRIBUTABLE_B}",
    ]


def test_probe_worktree_head_mismatch_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    probe_head_calls = 0

    def wrong_probe_head(command: Sequence[str], **kwargs):
        nonlocal probe_head_calls
        if list(command)[-2:] == ["rev-parse", "HEAD"] and Path(command[2]) != repo:
            probe_head_calls += 1
        if probe_head_calls == 1 and list(command)[-2:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "0" * 40 + "\n", "")
        return subprocess.run(command, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
        command_runner=wrong_probe_head,
    ) == 2
    assert list(probe_root.iterdir()) == []


def test_probe_worktree_head_change_after_node_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    """M8: 初期検査は通し、node 後の HEAD 再検証だけで変更を拒否する。"""

    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    reached = False

    def move_probe_head(worktree: Path, _nodeid: str) -> int:
        nonlocal reached
        reached = True
        _git(
            worktree,
            "-c",
            "user.name=Acceptance Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "move probe head",
        )
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=move_probe_head,
    ) == 2
    assert reached
    assert list(probe_root.iterdir()) == []


def test_each_node_uses_a_fresh_probe_worktree(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    second = "orchestrator/tests/test_example.py::test_non_attributable_two"
    log = _write_log(
        tmp_path,
        _summary_log((("FAILED", _NON_ATTRIBUTABLE), ("FAILED", second))),
    )
    observed: list[Path] = []

    def record_worktree(worktree: Path, _nodeid: str) -> int:
        observed.append(worktree)
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=record_worktree,
    ) == 0
    assert len(observed) == 2
    assert len({str(path) for path in observed}) == 2
    assert list(probe_root.iterdir()) == []


def test_cache_only_submodule_initialization_failure_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, _old_main, probe_root = committed_repo
    tested_main, path_text, _module_dir = _add_initialized_submodule(repo, tmp_path)
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    observed_environment: dict[str, str] = {}

    def fail_submodule_update(command: Sequence[str], **kwargs):
        values = list(command)
        if values[-6:] == [
            "submodule", "update", "--init", "--no-fetch", "--", path_text,
        ]:
            observed_environment.update(kwargs["env"])
            return subprocess.CompletedProcess(values, 1, "", "cache miss")
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
        command_runner=fail_submodule_update,
    ) == 2
    assert observed_environment["GIT_ALLOW_PROTOCOL"] == "file"
    assert list(probe_root.iterdir()) == []


def test_initialized_submodule_uses_local_module_dir_and_file_protocol(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, _old_main, probe_root = committed_repo
    tested_main, path_text, module_dir = _add_initialized_submodule(repo, tmp_path)
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    receipt = tmp_path / "receipt.json"
    observed_config: list[list[str]] = []
    observed_update_environment: dict[str, str] = {}

    def observe_submodule_commands(command: Sequence[str], **kwargs):
        values = list(command)
        if values[-3:] == ["config", f"submodule.{path_text}.url", str(module_dir)]:
            observed_config.append(values)
        if values[-6:] == [
            "submodule", "update", "--init", "--no-fetch", "--", path_text,
        ]:
            observed_update_environment.update(kwargs["env"])
        return subprocess.run(values, **kwargs)

    def assert_initialized(worktree: Path, _nodeid: str) -> int:
        assert (worktree / path_text / "dependency.txt").read_text(
            encoding="utf-8"
        ) == "cached dependency\n"
        assert _git(
            worktree, "config", "--get", f"submodule.{path_text}.url"
        ).stdout.strip() == str(module_dir)
        return 1

    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        node_runner=assert_initialized,
        command_runner=observe_submodule_commands,
    ) == 0
    assert len(observed_config) == 1
    assert observed_update_environment["GIT_ALLOW_PROTOCOL"] == "file"
    assert json.loads(receipt.read_text(encoding="utf-8"))["submodules"] == [
        {
            "path": path_text,
            "reference_module_dir": str(module_dir),
            "status": "initialized",
        }
    ]


def test_reference_uninitialized_submodule_is_not_initialized_and_is_receipted(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, _old_main, probe_root = committed_repo
    tested_main, path_text = _add_uninitialized_submodule(repo)
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    receipt = tmp_path / "receipt.json"
    submodule_updates: list[list[str]] = []

    def observe_commands(command: Sequence[str], **kwargs):
        values = list(command)
        if "submodule" in values and "update" in values:
            submodule_updates.append(values)
        return subprocess.run(values, **kwargs)

    def assert_uninitialized(worktree: Path, _nodeid: str) -> int:
        assert not (worktree / path_text / ".git").exists()
        return 1

    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        node_runner=assert_uninitialized,
        command_runner=observe_commands,
    ) == 0
    assert submodule_updates == []
    assert json.loads(receipt.read_text(encoding="utf-8"))["submodules"] == [
        {"path": path_text, "status": "reference-uninitialized"}
    ]


def test_submodule_url_rewrite_failure_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, _old_main, probe_root = committed_repo
    tested_main, path_text, module_dir = _add_initialized_submodule(repo, tmp_path)
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    update_reached = False

    def fail_url_rewrite(command: Sequence[str], **kwargs):
        nonlocal update_reached
        values = list(command)
        if values[-3:] == ["config", f"submodule.{path_text}.url", str(module_dir)]:
            return subprocess.CompletedProcess(values, 1, "", "config rejected")
        if "submodule" in values and "update" in values:
            update_reached = True
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
        command_runner=fail_url_rewrite,
    ) == 2
    assert not update_reached
    assert list(probe_root.iterdir()) == []


def test_ignored_artifact_from_node_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def contaminate(worktree: Path, _nodeid: str) -> int:
        cache = worktree / "__pycache__"
        cache.mkdir()
        (cache / "marker.pyc").write_bytes(b"pollution")
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=contaminate,
    ) == 2
    assert list(probe_root.iterdir()) == []


@pytest.mark.skipif(not hasattr(signal, "SIGTERM"), reason="SIGTERM unavailable")
def test_sigterm_cleans_active_probe_before_nonzero_exit(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def terminate(_worktree: Path, _nodeid: str) -> int:
        os.kill(os.getpid(), signal.SIGTERM)
        raise AssertionError("signal handler must interrupt the runner")

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=terminate,
    ) == 2
    assert list(probe_root.iterdir()) == []
    assert str(probe_root) not in _git(repo, "worktree", "list", "--porcelain").stdout


def test_probe_root_inside_repo_is_rejected(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, _probe_root = committed_repo
    inside = repo / "probes"
    inside.mkdir()
    log = _write_log(tmp_path, _summary_log(()))
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", inside),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_tested_main_must_equal_main_ref_head(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    (repo / "tracked.txt").write_text("new main\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(
        repo,
        "-c",
        "user.name=Acceptance Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "advance main",
    )
    wave_tip = _git(repo, "rev-parse", "HEAD").stdout.strip()
    log = _write_log(tmp_path, _summary_log(()))
    assert CAR.main(
        _arguments(
            log,
            tested_main,
            tmp_path / "receipt.json",
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_wave_tip_must_equal_repo_head(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log(()))
    assert CAR.main(
        _arguments(
            log,
            tested_main,
            tmp_path / "receipt.json",
            probe_root,
            wave_tip="0" * 40,
        ),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_dirty_wave_worktree_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    log = _write_log(tmp_path, _summary_log(()))
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2


def test_probe_worktree_is_removed_on_failure(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def fail_runner(_worktree: Path, _nodeid: str) -> int:
        raise RuntimeError("injected runner failure")

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=fail_runner,
    ) == 2
    assert list(probe_root.iterdir()) == []
    assert str(probe_root) not in _git(repo, "worktree", "list", "--porcelain").stdout


def test_probe_cleanup_failure_returns_invalid_input(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def failed_remove_after_real_cleanup(command: Sequence[str], **kwargs):
        values = list(command)
        if values[-3:-1] == ["remove", "--force"]:
            completed = subprocess.run(values, **kwargs)
            assert completed.returncode == 0
            return subprocess.CompletedProcess(values, 1, completed.stdout, completed.stderr)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
        command_runner=failed_remove_after_real_cleanup,
    ) == 2
    assert list(probe_root.iterdir()) == []
    assert str(probe_root) not in _git(repo, "worktree", "list", "--porcelain").stdout


def test_receipt_binds_log_hash_and_tested_main(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    receipt = tmp_path / "receipt.json"
    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: 1,
    ) == 0
    document = json.loads(receipt.read_text(encoding="utf-8"))
    assert document["log_path"] == str(log)
    assert document["log_sha256"] == hashlib.sha256(log.read_bytes()).hexdigest()
    assert document["tested_main"] == tested_main
    assert document["wave_tip"] == tested_main
    assert document["nodes"] == [
        {
            "classification": "non-attributable",
            "nodeid": _NON_ATTRIBUTABLE,
            "rerun_rc": 1,
        }
    ]
    canonical = (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    assert receipt.read_bytes() == canonical


def test_default_seam_forces_dispatch_for_collection_and_rerun(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    observed: list[list[str]] = []

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            observed.append(values)
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values, 0, _NON_ATTRIBUTABLE + "\n", ""
                )
            return subprocess.CompletedProcess(values, 1, None, None)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    assert len(observed) == 2
    collection, rerun = observed
    assert collection[0] == sys.executable
    assert collection[1] == rerun[1]
    assert Path(collection[1]).parts[-2:] == ("tools", "run_tests.py")
    assert collection[2:] == [
        "--force-dispatch",
        "-p",
        "no:cacheprovider",
        "--collect-only",
        "-q",
        "orchestrator/tests/test_example.py",
    ]
    assert rerun[2:] == [
        "--force-dispatch",
        "-p",
        "no:cacheprovider",
        _NON_ATTRIBUTABLE,
    ]


def test_xdist_group_suffix_is_removed_only_from_rerun_selector(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    logged_nodeid = _NON_ATTRIBUTABLE + "@real-repo"
    log = _write_log(tmp_path, _summary_log((("FAILED", logged_nodeid),)))
    receipt = tmp_path / "receipt.json"
    observed: list[str] = []

    def node_runner(_worktree: Path, selector: str) -> int:
        observed.append(selector)
        return 1

    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        node_runner=node_runner,
    ) == 0
    assert observed == [_NON_ATTRIBUTABLE]
    assert json.loads(receipt.read_text(encoding="utf-8"))["nodes"][0][
        "nodeid"
    ] == logged_nodeid


@pytest.mark.parametrize(
    "literal_nodeid",
    [
        "orchestrator/tests/test_example.py::test_target@literal",
        "orchestrator/tests/test_example.py::test_target - literal",
    ],
)
def test_collection_preserves_literal_nodeid_suffixes(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    literal_nodeid: str,
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", literal_nodeid),)))
    observed: list[str] = []

    def node_runner(_worktree: Path, selector: str) -> int:
        observed.append(selector)
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=node_runner,
    ) == 0
    assert observed == [literal_nodeid]


def test_uncollected_logged_nodeid_fails_closed_without_rerun(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    unknown = "orchestrator/tests/test_example.py::test_not_collected"
    log = _write_log(tmp_path, _summary_log((("FAILED", unknown),)))
    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2
    assert list(probe_root.iterdir()) == []


def test_default_runner_infrastructure_rc_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values, 0, _NON_ATTRIBUTABLE + "\n", ""
                )
            return subprocess.CompletedProcess(values, 16, None, None)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2
    assert list(probe_root.iterdir()) == []


def test_unexpected_internal_error_never_uses_attributable_rc(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log(()))

    def broken_command_runner(_command: Sequence[str], **_kwargs):
        raise ValueError("injected unexpected failure")

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=broken_command_runner,
    ) == 2


@pytest.mark.parametrize("argv", [[], ["--help"]])
def test_incomplete_or_help_cli_never_returns_zero(argv: list[str]) -> None:
    assert CAR.main(argv) == 2


def _run() -> int:
    """新規 test file を repository の plain-runner 契約へ載せる。"""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
