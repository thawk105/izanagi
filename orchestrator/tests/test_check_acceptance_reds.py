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
_WAITER = _ROOT / "tools" / "dev_wave_wait.py"
_SPEC = importlib.util.spec_from_file_location(
    "check_acceptance_reds_under_test", _CHECKER
)
assert _SPEC and _SPEC.loader
CAR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CAR)
_WAIT_SPEC = importlib.util.spec_from_file_location(
    "dev_wave_wait_for_acceptance_reds_test", _WAITER
)
assert _WAIT_SPEC and _WAIT_SPEC.loader
DW = importlib.util.module_from_spec(_WAIT_SPEC)
sys.modules[_WAIT_SPEC.name] = DW
_WAIT_SPEC.loader.exec_module(DW)

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
    (repo / ".gitignore").write_text(
        "__pycache__/\noutput/pegasus-dispatch/\n", encoding="utf-8"
    )
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
            "",
            "7 tests collected in 0.01s",
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


def _advance_wave_tip(repo: Path) -> str:
    _git(repo, "checkout", "-qb", "acceptance-wave")
    (repo / "tracked.txt").write_text("wave fixture\n", encoding="utf-8")
    return _commit_fixture(repo, "wave fixture")


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


def _fake_dispatch_result(
    worktree: Path,
    command: Sequence[str],
    *,
    returncode: int,
    authoritative_stdout: str,
    relay_stdout: str | None = None,
    receipt_root: Path | None = None,
    fallback: bool = False,
    mutate: Callable[[dict[str, object]], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    values = list(command)
    root = (
        worktree / "output" / "pegasus-dispatch"
        if receipt_root is None
        else receipt_root
    )
    root.mkdir(parents=True, exist_ok=True)
    nonce = "fixture-dispatch"
    submission_dir = root / nonce
    submission_dir.mkdir()
    scheduler_stdout = submission_dir / "dispatch.sh.ofixture"
    scheduler_stdout.write_text(authoritative_stdout, encoding="utf-8")
    pytest_args = [value for value in values[2:] if value != "--force-dispatch"]
    target_path, separator, target_suffix = pytest_args[-1].partition("::")
    expected_target = str((worktree / target_path).resolve(strict=False))
    pytest_args[-1] = expected_target + (
        separator + target_suffix if separator else ""
    )
    document: dict[str, object] = {
        "schema_version": "pegasus-dispatch-receipt/v2",
        "submission_dir": str(submission_dir),
        "request_id": "fixture.nqsv",
        "request": {"task": "tests", "args": pytest_args},
        "result": {"stage": "child", "child_rc": returncode},
        "outcome": {
            "kind": "child",
            "rc": returncode,
            "accounting_verified": True,
        },
        "scheduler_logs": {
            "accounting_present": True,
            "stdout": {
                "path": str(scheduler_stdout),
                "size": len(authoritative_stdout.encode("utf-8")),
                "omitted_bytes": 0,
                "tail": authoritative_stdout,
            },
        },
    }
    if mutate is not None:
        mutate(document)
    receipt = (
        root / f"receipt-fallback-{nonce}.json"
        if fallback
        else submission_dir / "receipt.json"
    )
    receipt.write_text(json.dumps(document), encoding="utf-8")
    relay = (
        f"[Pegasus dispatch] receipt を {receipt} へ保存しました "
        f"(child rc={returncode})\n"
    )
    if relay_stdout is not None:
        relay += relay_stdout
    return subprocess.CompletedProcess(values, returncode, relay, "")


def _unexpected_runner(_worktree: Path, nodeid: str) -> int:
    raise AssertionError(f"runner must not be reached: {nodeid}")


def _non_attributable_rerun(
    command: Sequence[str], nodeid: str = _NON_ATTRIBUTABLE,
) -> subprocess.CompletedProcess[str]:
    values = list(command)
    return subprocess.CompletedProcess(
        values, 1, _summary_log((("FAILED", nodeid),)), ""
    )


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
        _NON_ATTRIBUTABLE: [1],
        _ATTRIBUTABLE_A: [0, 1],
        _ATTRIBUTABLE_B: [0, 1],
    }

    def node_runner(_worktree: Path, nodeid: str) -> int:
        return outcomes[nodeid].pop(0)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=node_runner,
    ) == 1
    assert capsys.readouterr().out.splitlines() == [
        "status=attributable-red",
        f"attributable={_ATTRIBUTABLE_A}",
        f"attributable={_ATTRIBUTABLE_B}",
    ]


def test_main_green_wave_red_is_attributable(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    log = _write_log(tmp_path, _summary_log((("FAILED", _ATTRIBUTABLE_A),)))
    receipt = tmp_path / "receipt.json"
    observed_tips: list[str] = []

    def node_runner(worktree: Path, _nodeid: str) -> int:
        tip = _git(worktree, "rev-parse", "HEAD").stdout.strip()
        observed_tips.append(tip)
        return 0 if tip == tested_main else 1

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            receipt,
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=node_runner,
    ) == 1
    assert observed_tips == [tested_main, wave_tip]
    raw = receipt.read_bytes()
    document = json.loads(raw)
    assert set(document) == {
        "collections", "log_path", "log_sha256", "nodes", "schema_version",
        "status", "submodules", "tested_main", "wave_tip",
    }
    assert document["nodes"] == [
        {
            "classification": "attributable",
            "main_rerun_rc": 0,
            "nodeid": _ATTRIBUTABLE_A,
            "rerun_rc": 0,
            "wave_rerun_rc": 1,
        }
    ]
    assert set(document["nodes"][0]) == {
        "classification", "main_rerun_rc", "nodeid", "rerun_rc",
        "wave_rerun_rc",
    }
    with pytest.raises(DW._StageFailure) as exc_info:
        DW._red_check_payload_nodeids(
            json.loads(raw),
            tested_main=tested_main,
            tested_tip=wave_tip,
            log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        )
    assert exc_info.value.outcome == DW._Outcome(70, "acceptance-red-check")


def test_main_green_wave_green_is_recorded_as_flake(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    receipt = tmp_path / "receipt.json"
    observed_tips: list[str] = []

    def node_runner(worktree: Path, _nodeid: str) -> int:
        observed_tips.append(_git(worktree, "rev-parse", "HEAD").stdout.strip())
        return 0

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            receipt,
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=node_runner,
    ) == 0
    assert capsys.readouterr().out.splitlines() == [
        "status=non-attributable-only"
    ]
    assert observed_tips == [tested_main, wave_tip]
    document = json.loads(receipt.read_text(encoding="utf-8"))
    raw = receipt.read_bytes()
    assert set(document) == {
        "collections", "log_path", "log_sha256", "nodes", "schema_version",
        "status", "submodules", "tested_main", "wave_tip",
    }
    assert document["status"] == "non-attributable-only"
    assert document["nodes"] == [
        {
            "classification": "flake",
            "main_rerun_rc": 0,
            "nodeid": _NON_ATTRIBUTABLE,
            "rerun_rc": 0,
            "wave_rerun_rc": 0,
        }
    ]
    assert set(document["nodes"][0]) == {
        "classification", "main_rerun_rc", "nodeid", "rerun_rc",
        "wave_rerun_rc",
    }
    assert DW._red_check_payload_nodeids(
        json.loads(raw),
        tested_main=tested_main,
        tested_tip=wave_tip,
        log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
    ) == ((), (_NON_ATTRIBUTABLE,))


def test_main_red_is_non_attributable_without_wave_rerun(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    receipt = tmp_path / "receipt.json"
    observed_tips: list[str] = []

    def node_runner(worktree: Path, _nodeid: str) -> int:
        observed_tips.append(_git(worktree, "rev-parse", "HEAD").stdout.strip())
        return 1

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            receipt,
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=node_runner,
    ) == 0
    assert observed_tips == [tested_main]
    raw = receipt.read_bytes()
    document = json.loads(raw)
    assert set(document) == {
        "collections", "log_path", "log_sha256", "nodes", "schema_version",
        "status", "submodules", "tested_main", "wave_tip",
    }
    assert document["nodes"] == [
        {
            "classification": "non-attributable",
            "nodeid": _NON_ATTRIBUTABLE,
            "rerun_rc": 1,
        }
    ]
    assert set(document["nodes"][0]) == {
        "classification", "nodeid", "rerun_rc",
    }
    assert DW._red_check_payload_nodeids(
        json.loads(raw),
        tested_main=tested_main,
        tested_tip=wave_tip,
        log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
    ) == ((_NON_ATTRIBUTABLE,), ())


def test_mixed_non_attributable_and_flake_receipt_round_trips_to_waiter(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    red = "orchestrator/tests/test_example.py::test_non_attributable"
    flake = "orchestrator/tests/test_example.py::test_attributable_a"
    log = _write_log(
        tmp_path,
        _summary_log((("FAILED", red), ("ERROR", flake))),
    )
    receipt = tmp_path / "receipt.json"
    observed: list[tuple[str, str]] = []

    def node_runner(worktree: Path, nodeid: str) -> int:
        observed.append(
            (_git(worktree, "rev-parse", "HEAD").stdout.strip(), nodeid)
        )
        if nodeid == red:
            return 1
        if nodeid == flake:
            return 0
        raise AssertionError(f"unexpected nodeid: {nodeid}")

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            receipt,
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=node_runner,
    ) == 0
    assert observed.count((tested_main, red)) == 1
    assert observed.count((tested_main, flake)) == 1
    assert observed.count((wave_tip, flake)) == 1

    raw = receipt.read_bytes()
    assert DW._red_check_payload_nodeids(
        json.loads(raw),
        tested_main=tested_main,
        tested_tip=wave_tip,
        log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
    ) == (
        ("orchestrator/tests/test_example.py::test_non_attributable",),
        ("orchestrator/tests/test_example.py::test_attributable_a",),
    )


def test_wave_rerun_rc_outside_zero_or_one_fails_closed(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    outcomes = iter((0, 2))

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            tmp_path / "receipt.json",
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=lambda _worktree, _nodeid: next(outcomes),
    ) == 2
    assert not (tmp_path / "receipt.json").exists()


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


def test_wave_probe_head_change_after_node_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def move_wave_probe_head(worktree: Path, _nodeid: str) -> int:
        if _git(worktree, "rev-parse", "HEAD").stdout.strip() == tested_main:
            return 0
        _git(
            worktree,
            "-c",
            "user.name=Acceptance Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "move wave probe head",
        )
        return 1

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            tmp_path / "receipt.json",
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=move_wave_probe_head,
    ) == 2
    assert list(probe_root.iterdir()) == []


def test_wave_probe_fingerprint_change_after_node_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    wave_tip = _advance_wave_tip(repo)
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def contaminate_wave_probe(worktree: Path, _nodeid: str) -> int:
        if _git(worktree, "rev-parse", "HEAD").stdout.strip() == tested_main:
            return 0
        cache = worktree / "__pycache__"
        cache.mkdir()
        (cache / "marker.pyc").write_bytes(b"pollution")
        return 1

    assert CAR.main(
        _arguments(
            log,
            tested_main,
            tmp_path / "receipt.json",
            probe_root,
            wave_tip=wave_tip,
        ),
        repo_root=repo,
        node_runner=contaminate_wave_probe,
    ) == 2
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


def test_ignored_artifact_diagnostic_includes_path(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
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
    captured = capsys.readouterr()
    assert "probe worktree is not clean, including ignored files" in captured.err
    assert "__pycache__" in captured.err
    assert list(probe_root.iterdir()) == []


def test_ignored_artifact_diagnostic_includes_multiple_paths(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def contaminate(worktree: Path, _nodeid: str) -> int:
        first_cache = worktree / "__pycache__"
        first_cache.mkdir()
        (first_cache / "marker.pyc").write_bytes(b"pollution")
        second_cache = worktree / "orchestrator" / "campaign" / "__pycache__"
        second_cache.mkdir(parents=True)
        (second_cache / "marker.pyc").write_bytes(b"pollution")
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=contaminate,
    ) == 2
    captured = capsys.readouterr()
    assert "!! __pycache__/" in captured.err
    assert "!! orchestrator/campaign/__pycache__/" in captured.err
    assert list(probe_root.iterdir()) == []


@pytest.mark.parametrize("entry_count", [64, 65])
def test_ignored_artifact_diagnostic_record_limit(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
    entry_count: int,
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )

    def contaminate(worktree: Path, _nodeid: str) -> int:
        for index in range(entry_count):
            cache = worktree / f"dirty-{index:03d}" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "marker.pyc").write_bytes(b"pollution")
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=contaminate,
    ) == 2
    captured = capsys.readouterr()
    if entry_count == 64:
        assert "truncated" not in captured.err
    else:
        assert "showing 64 of 65 entries, truncated" in captured.err
    assert list(probe_root.iterdir()) == []


def test_ignored_artifact_diagnostic_byte_limit(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(
        tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),))
    )
    entry_count = 40
    assert entry_count < 64

    def contaminate(worktree: Path, _nodeid: str) -> int:
        for index in range(entry_count):
            directory = f"dirty-{index:02d}-" + ("x" * 190)
            cache = worktree / directory / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "marker.pyc").write_bytes(b"pollution")
        return 1

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=contaminate,
    ) == 2
    captured = capsys.readouterr()
    summary = next(
        line for line in captured.err.splitlines() if line.startswith("showing ")
    )
    fields = summary.split()
    shown = int(fields[1])
    assert fields == [
        "showing", str(shown), "of", str(entry_count), "entries,", "truncated"
    ]
    assert 0 < shown < 64
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


def test_wave_tip_is_required(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log(()))
    receipt = tmp_path / "receipt.json"
    arguments = _arguments(log, tested_main, receipt, probe_root)
    wave_tip_index = arguments.index("--wave-tip")
    del arguments[wave_tip_index : wave_tip_index + 2]

    assert CAR.main(
        arguments,
        repo_root=repo,
        node_runner=_unexpected_runner,
    ) == 2
    assert not receipt.exists()


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
            worktree = Path(kwargs["cwd"])
            if "--collect-only" in values:
                return _fake_dispatch_result(
                    worktree,
                    values,
                    returncode=0,
                    authoritative_stdout=(
                        _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
                    ),
                )
            return _fake_dispatch_result(
                worktree,
                values,
                returncode=1,
                authoritative_stdout=_summary_log(
                    (("FAILED", _NON_ATTRIBUTABLE),)
                ),
            )
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


def test_truncated_relay_uses_complete_dispatch_receipt(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            worktree = Path(kwargs["cwd"])
            if "--collect-only" in values:
                return _fake_dispatch_result(
                    worktree,
                    values,
                    returncode=0,
                    authoritative_stdout=(
                        _NON_ATTRIBUTABLE
                        + "\norchestrator/tests/test_example.py::test_other"
                        + "\n\n2 tests collected in 0.01s\n"
                    ),
                    relay_stdout=(
                        "| orchestrator/tests/test_example.py::test_other\n"
                        "| \n| 2 tests collected in 0.01s\n"
                    ),
                )
            return _fake_dispatch_result(
                worktree,
                values,
                returncode=1,
                authoritative_stdout=_summary_log(
                    (("FAILED", _NON_ATTRIBUTABLE),)
                ),
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    assert list(probe_root.iterdir()) == []


def test_truncated_relay_without_receipt_fails_closed_before_rerun(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    rerun_reached = False

    def command_runner(command: Sequence[str], **kwargs):
        nonlocal rerun_reached
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    "[Pegasus dispatch] request fixture child stdout begin "
                    "(size=100 bytes, omitted_bytes=50)\n"
                    f"| {_NON_ATTRIBUTABLE}\n| 1 test collected in 0.01s\n",
                    "",
                )
            rerun_reached = True
            return _non_attributable_rerun(values)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2
    assert not rerun_reached


def test_dispatch_receipt_outside_probe_root_fails_closed_before_rerun(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    rerun_reached = False

    def command_runner(command: Sequence[str], **kwargs):
        nonlocal rerun_reached
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                worktree = Path(kwargs["cwd"])
                (worktree / "output" / "pegasus-dispatch").mkdir(
                    parents=True, exist_ok=True
                )
                return _fake_dispatch_result(
                    worktree,
                    values,
                    returncode=0,
                    authoritative_stdout=(
                        _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
                    ),
                    receipt_root=tmp_path / "foreign-dispatch",
                )
            rerun_reached = True
            return _non_attributable_rerun(values)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2
    assert not rerun_reached


def test_dispatch_collection_receipt_requires_bound_request_args(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def mutate(document: dict[str, object]) -> None:
        request = document["request"]
        assert isinstance(request, dict)
        request["args"] = ["-q", "/foreign/test.py"]

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" not in values:
                return _non_attributable_rerun(values)
            return _fake_dispatch_result(
                Path(kwargs["cwd"]),
                values,
                returncode=0,
                authoritative_stdout=(
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
                ),
                mutate=mutate,
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


@pytest.mark.parametrize("invalid_field", ["schema", "child_rc", "accounting"])
def test_dispatch_collection_receipt_requires_v2_child_outcome(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    invalid_field: str,
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def mutate(document: dict[str, object]) -> None:
        if invalid_field == "schema":
            document["schema_version"] = "pegasus-dispatch-receipt/v1"
        elif invalid_field == "child_rc":
            result = document["result"]
            assert isinstance(result, dict)
            result["child_rc"] = 1
        else:
            outcome = document["outcome"]
            assert isinstance(outcome, dict)
            outcome["accounting_verified"] = False

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" not in values:
                return _non_attributable_rerun(values)
            return _fake_dispatch_result(
                Path(kwargs["cwd"]),
                values,
                returncode=0,
                authoritative_stdout=(
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
                ),
                mutate=mutate,
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def mutate(document: dict[str, object]) -> None:
        logs = document["scheduler_logs"]
        assert isinstance(logs, dict)
        stdout = logs["stdout"]
        assert isinstance(stdout, dict)
        stdout["omitted_bytes"] = 1

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" not in values:
                return _non_attributable_rerun(values)
            return _fake_dispatch_result(
                Path(kwargs["cwd"]),
                values,
                returncode=0,
                authoritative_stdout=(
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
                ),
                mutate=mutate,
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_dispatch_receipt_size_mismatch_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def mutate(document: dict[str, object]) -> None:
        logs = document["scheduler_logs"]
        assert isinstance(logs, dict)
        stdout = logs["stdout"]
        assert isinstance(stdout, dict)
        stdout["size"] = int(stdout["size"]) + 1

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" not in values:
                return _non_attributable_rerun(values)
            return _fake_dispatch_result(
                Path(kwargs["cwd"]),
                values,
                returncode=0,
                authoritative_stdout=(
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
                ),
                mutate=mutate,
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_dispatch_receipt_replacement_character_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" not in values:
                return _non_attributable_rerun(values)
            return _fake_dispatch_result(
                Path(kwargs["cwd"]),
                values,
                returncode=0,
                authoritative_stdout=(
                    _NON_ATTRIBUTABLE
                    + "\n\ufffd\n\n1 test collected in 0.01s\n"
                ),
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_collection_footer_count_mismatch_fails_closed_before_rerun(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    rerun_reached = False

    def command_runner(command: Sequence[str], **kwargs):
        nonlocal rerun_reached
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n2 tests collected in 0.01s\n",
                    "",
                )
            rerun_reached = True
            return _non_attributable_rerun(values)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2
    assert not rerun_reached


def test_collection_footer_missing_fails_closed_on_production_path(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    rerun_reached = False

    def command_runner(command: Sequence[str], **kwargs):
        nonlocal rerun_reached
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(values, 0, _NON_ATTRIBUTABLE + "\n", "")
            rerun_reached = True
            return _non_attributable_rerun(values)
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2
    assert not rerun_reached


def test_single_test_collection_footer_is_accepted(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
                )
            return subprocess.CompletedProcess(
                values, 1, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)), ""
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0


def test_injected_rerun_output_is_not_replayed_to_checker_streams(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    fake_rerun_log = _summary_log((("FAILED", _NON_ATTRIBUTABLE),))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
                )
            return subprocess.CompletedProcess(
                values, 1, fake_rerun_log, fake_rerun_log
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["status=non-attributable-only"]
    assert captured.err == ""
    for stream in (captured.out, captured.err):
        assert "short test summary info" not in stream
        assert f"FAILED {_NON_ATTRIBUTABLE}" not in stream


def test_deselected_collection_footer_uses_selected_count(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE
                    + "\n\n1/3 tests collected (2 deselected) in 0.01s\n",
                    "",
                )
            return subprocess.CompletedProcess(
                values, 1, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)), ""
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0


@pytest.mark.parametrize(
    "footer",
    [
        "no tests collected in 0.01s",
        "no tests collected (3 deselected) in 0.01s",
        "0/3 tests collected (3 deselected) in 0.01s",
    ],
)
def test_zero_or_all_deselected_collection_fails_closed(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    footer: str,
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            assert "--collect-only" in values
            return subprocess.CompletedProcess(values, 0, footer + "\n", "")
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_rerun_rc_one_without_matching_outcome_fails_closed(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
                )
            return subprocess.CompletedProcess(
                values,
                1,
                _summary_log(
                    (("FAILED", "orchestrator/tests/test_example.py::test_other"),)
                ),
                "",
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_dispatch_commands_use_dispatch_aware_timeout(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    dispatch_timeouts: list[float] = []
    git_timeouts: list[float] = []

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            dispatch_timeouts.append(kwargs["timeout"])
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
                )
            return subprocess.CompletedProcess(
                values, 1, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)), ""
            )
        git_timeouts.append(kwargs["timeout"])
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    assert dispatch_timeouts == [5100.0, 5100.0]
    assert git_timeouts and set(git_timeouts) == {120.0}


def test_collection_environment_neutralizes_pytest_addopts(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    monkeypatch.setenv("PYTEST_ADDOPTS", "--deselect=target")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", "explicit-user-command")
    monkeypatch.setenv("IZANAGI_T080_E2E", "1")
    monkeypatch.setenv("IZANAGI_TEST_NPROC", "7")
    monkeypatch.setenv("IZANAGI_TEST_TRIGGER", "review-fix")
    observed_environments: list[dict[str, str]] = []

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            observed_environments.append(kwargs["env"])
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
                )
            return subprocess.CompletedProcess(
                values, 1, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)), ""
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    assert len(observed_environments) == 2
    for environment in observed_environments:
        assert environment["PYTEST_ADDOPTS"] == ""
        assert "PYTEST_PLUGINS" not in environment
        assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" not in environment
        assert "IZANAGI_RUN_GROWTH_HELD_TESTS" not in environment
        assert "IZANAGI_T080_E2E" not in environment
        assert environment["IZANAGI_TEST_NPROC"] == "7"
        assert environment["IZANAGI_TEST_TRIGGER"] == "review-fix"


def test_checker_receipt_records_collection_provenance(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    collection_stdout = _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n"
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))
    receipt = tmp_path / "checker-receipt.json"

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return _fake_dispatch_result(
                    Path(kwargs["cwd"]),
                    values,
                    returncode=0,
                    authoritative_stdout=collection_stdout,
                )
            return subprocess.CompletedProcess(
                values, 1, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)), ""
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, receipt, probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    collection = json.loads(receipt.read_text(encoding="utf-8"))["collections"][0]
    assert collection["path"] == "orchestrator/tests/test_example.py"
    assert collection["source"] == "dispatch-receipt"
    assert "receipt_path" not in collection
    assert collection["deleted_receipt_path"].endswith(
        "/fixture-dispatch/receipt.json"
    )
    assert collection["submission_nonce"] == "fixture-dispatch"
    assert collection["request_id"] == "fixture.nqsv"
    assert collection["stdout_sha256"] == hashlib.sha256(
        collection_stdout.encode("utf-8")
    ).hexdigest()


def test_default_dispatched_rerun_removes_verified_dispatch_artifacts(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                return subprocess.CompletedProcess(
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
                )
            return _fake_dispatch_result(
                Path(kwargs["cwd"]),
                values,
                returncode=1,
                authoritative_stdout=_summary_log(
                    (("FAILED", _NON_ATTRIBUTABLE),)
                ),
                fallback=True,
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0


def test_dispatch_cleanup_refuses_nonempty_exact_root(tmp_path: Path) -> None:
    worktree = tmp_path / "probe"
    worktree.mkdir()
    command = [
        sys.executable,
        str(worktree / "tools" / "run_tests.py"),
        "-p",
        "no:cacheprovider",
        "--force-dispatch",
        _NON_ATTRIBUTABLE,
    ]
    result = _fake_dispatch_result(
        worktree,
        command,
        returncode=1,
        authoritative_stdout=_summary_log((("FAILED", _NON_ATTRIBUTABLE),)),
        fallback=True,
    )
    dispatch_root = worktree / "output" / "pegasus-dispatch"
    marker = dispatch_root / "unowned-marker"
    marker.write_text("must remain\n", encoding="utf-8")
    expected_args = [
        "-p",
        "no:cacheprovider",
        str(
            (
                worktree / "orchestrator" / "tests" / "test_example.py"
            ).resolve(strict=False)
        )
        + "::test_non_attributable",
    ]

    with pytest.raises(CAR.InvalidInput, match="dispatch artifact cleanup failed"):
        CAR._authoritative_command_stdout(
            result,
            worktree=worktree,
            expected_args=expected_args,
        )

    assert marker.read_text(encoding="utf-8") == "must remain\n"
    assert not (dispatch_root / "fixture-dispatch").exists()
    assert not (dispatch_root / "receipt-fallback-fixture-dispatch.json").exists()


def test_dispatch_cleanup_preserves_everything_when_orphan_hold_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "probe" / "output" / "pegasus-dispatch"
    submission = root / "nonce"
    submission.mkdir(parents=True)
    receipt = submission / "receipt.json"
    receipt.write_text("{}\n", encoding="utf-8")
    hold = root / "orphan-hold.json"
    hold.write_text("{}\n", encoding="utf-8")
    artifacts = CAR._DispatchArtifacts(root, receipt, submission, None, "nonce")
    rmtree_calls: list[Path] = []
    rmdir_calls: list[Path] = []

    monkeypatch.setattr(
        CAR.shutil,
        "rmtree",
        lambda path: rmtree_calls.append(Path(path)),
    )
    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda path: rmdir_calls.append(Path(path)),
    )

    with pytest.raises(CAR.InvalidInput, match="orphan-hold"):
        CAR._cleanup_dispatch_artifacts(artifacts)

    assert rmtree_calls == []
    assert rmdir_calls == []
    assert receipt.is_file()
    assert hold.is_file()


def test_dispatch_cleanup_lstat_error_preserves_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "probe" / "output" / "pegasus-dispatch"
    submission = root / "nonce"
    submission.mkdir(parents=True)
    receipt = submission / "receipt.json"
    receipt.write_text("{}\n", encoding="utf-8")
    hold = root / "orphan-hold.json"
    artifacts = CAR._DispatchArtifacts(root, receipt, submission, None, "nonce")
    real_lstat = os.lstat
    rmtree_calls: list[Path] = []
    rmdir_calls: list[Path] = []

    def indeterminate(path, *args, **kwargs):
        if Path(path) == hold:
            raise OSError("injected lstat failure")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(CAR.os, "lstat", indeterminate)
    monkeypatch.setattr(
        CAR.shutil,
        "rmtree",
        lambda path: rmtree_calls.append(Path(path)),
    )
    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda path: rmdir_calls.append(Path(path)),
    )

    with pytest.raises(CAR.InvalidInput, match="orphan-hold"):
        CAR._cleanup_dispatch_artifacts(artifacts)

    assert rmtree_calls == []
    assert rmdir_calls == []
    assert receipt.is_file()
    assert submission.is_dir()


def test_dispatch_cleanup_without_hold_keeps_existing_positive_behavior(
    tmp_path: Path,
) -> None:
    root = tmp_path / "probe" / "output" / "pegasus-dispatch"
    submission = root / "nonce"
    submission.mkdir(parents=True)
    receipt = submission / "receipt.json"
    receipt.write_text("{}\n", encoding="utf-8")
    artifacts = CAR._DispatchArtifacts(root, receipt, submission, None, "nonce")

    CAR._cleanup_dispatch_artifacts(artifacts)

    assert not root.exists()


def test_probe_cleanup_runs_no_command_or_rmdir_when_orphan_hold_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    parent = tmp_path / "probe-parent"
    worktree = parent / "probe"
    hold = worktree / "output" / "pegasus-dispatch" / "orphan-hold.json"
    hold.parent.mkdir(parents=True)
    hold.write_text("{}\n", encoding="utf-8")
    commands: list[list[str]] = []
    rmdir_calls: list[Path] = []

    def command_runner(command: Sequence[str], **_kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        Path,
        "rmdir",
        lambda path: rmdir_calls.append(Path(path)),
    )

    with pytest.raises(CAR.InvalidInput, match="orphan-hold"):
        CAR._cleanup_probe(
            repo,
            parent,
            worktree,
            added=True,
            command_runner=command_runner,
        )

    assert commands == []
    assert rmdir_calls == []
    assert hold.is_file()


@pytest.mark.parametrize(
    "collection_stdout",
    [
        (
            _NON_ATTRIBUTABLE
            + "\n"
            + _NON_ATTRIBUTABLE
            + "\n\n2 tests collected in 0.01s\n"
        ),
        (
            _NON_ATTRIBUTABLE
            + "\n\n1 test collected in 0.01s\n"
            + "1 test collected in 0.02s\n"
        ),
        _NON_ATTRIBUTABLE + "\n\n1 tests collected in 0.01s\n",
        _NON_ATTRIBUTABLE + "\n\n1/4 tests collected (2 deselected) in 0.01s\n",
    ],
)
def test_collection_duplicate_or_invalid_footer_fails_closed(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    collection_stdout: str,
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            assert "--collect-only" in values
            return subprocess.CompletedProcess(values, 0, collection_stdout, "")
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 2


def test_each_logged_path_has_an_independent_complete_collection_gate(
    tmp_path: Path, committed_repo: tuple[Path, str, Path]
) -> None:
    repo, tested_main, probe_root = committed_repo
    second = "orchestrator/tests/test_second.py::test_red"
    log = _write_log(
        tmp_path,
        _summary_log(
            (("FAILED", _NON_ATTRIBUTABLE), ("ERROR", second))
        ),
    )
    collected_targets: list[str] = []

    def command_runner(command: Sequence[str], **kwargs):
        values = list(command)
        if len(values) >= 2 and Path(values[1]).name == "run_tests.py":
            if "--collect-only" in values:
                target = values[-1]
                collected_targets.append(target)
                selected = _NON_ATTRIBUTABLE if target.endswith("test_example.py") else second
                return subprocess.CompletedProcess(
                    values, 0, selected + "\n\n1 test collected in 0.01s\n", ""
                )
            selector = values[-1]
            return subprocess.CompletedProcess(
                values, 1, _summary_log((("FAILED", selector),)), ""
            )
        return subprocess.run(values, **kwargs)

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        command_runner=command_runner,
    ) == 0
    assert collected_targets == [
        "orchestrator/tests/test_example.py",
        "orchestrator/tests/test_second.py",
    ]


def test_injected_collection_failure_cannot_reach_rerun_or_status(
    tmp_path: Path,
    committed_repo: tuple[Path, str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, tested_main, probe_root = committed_repo
    log = _write_log(tmp_path, _summary_log((("FAILED", _NON_ATTRIBUTABLE),)))

    def fail_collection(_worktree: Path, _path_text: str) -> tuple[str, ...]:
        raise CAR.InvalidInput("injected incomplete collection")

    assert CAR.main(
        _arguments(log, tested_main, tmp_path / "receipt.json", probe_root),
        repo_root=repo,
        node_runner=_unexpected_runner,
        collection_runner=fail_collection,
    ) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "status=invalid-input" in captured.err
    assert not (tmp_path / "receipt.json").exists()


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
                    values,
                    0,
                    _NON_ATTRIBUTABLE + "\n\n1 test collected in 0.01s\n",
                    "",
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
