# -*- coding: utf-8 -*-
"""tools/dev_wave_codex.py の dry-run argv 契約。"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_DISPATCHER = _ROOT / "tools" / "dev_wave_codex.py"


def _invoke(
    root: Path,
    *,
    stage: str,
    lane: str | None = None,
    reasoning: str | None = None,
    extra: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        os.fspath(_DISPATCHER),
        "--stage",
        stage,
        "--wave",
        "wave-alpha",
        "--prompt-file",
        os.fspath(root / "prompt.md"),
        "--artifact-root",
        os.fspath(root / "artifacts"),
        "-o",
        os.fspath(root / "answer.md"),
        "--repo-root",
        os.fspath(_ROOT),
        "--dry-run",
    ]
    if lane is not None:
        command.extend(("--lane", lane))
    if reasoning is not None:
        command.extend(("--reasoning", reasoning))
    command.extend(extra)
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _argv(result: subprocess.CompletedProcess[str]) -> list[str]:
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


def _option(argv: list[str], option: str) -> str:
    positions = [index for index, value in enumerate(argv) if value == option]
    assert len(positions) == 1, (option, positions)
    index = positions[0]
    assert index + 1 < len(argv)
    return argv[index + 1]


def test_dry_run_stage_and_lane_matrix() -> None:
    cases = (
        ("plan", None, "max", "read-only"),
        ("consult", "sol", "max", "read-only"),
        ("consult", "luna", "max", "read-only"),
        ("author", None, "high", "workspace-write"),
        ("review", None, None, "read-only"),
        ("fix", None, "high", "workspace-write"),
        ("focus", None, None, "read-only"),
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for stage, lane, reasoning, sandbox in cases:
            argv = _argv(
                _invoke(
                    root,
                    stage=stage,
                    lane=lane,
                    reasoning=reasoning,
                )
            )
            assert argv[:3] == [
                "python3",
                os.fspath(_ROOT / "tools" / "codex_worker_launch.py"),
                "run",
            ]
            assert _option(argv, "--stage") == stage
            assert _option(argv, "--sandbox") == sandbox
            assert "--model" not in argv
            if lane is None:
                assert "--lane" not in argv
            else:
                assert _option(argv, "--lane") == lane
            if stage in ("review", "focus"):
                assert "--reasoning" not in argv
            else:
                assert _option(argv, "--reasoning") == reasoning


def test_paths_and_job_id_are_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = _argv(
            _invoke(root, stage="consult", lane="luna", reasoning="max")
        )
        second = _argv(
            _invoke(root, stage="consult", lane="luna", reasoning="max")
        )
        assert first == second
        wave_root = root / "artifacts" / "wave-alpha"
        job_id = "wave-alpha-consult-luna"
        job_root = wave_root / job_id
        assert _option(first, "--job-id") == job_id
        assert _option(first, "--wave-id") == "wave-alpha"
        assert _option(first, "--artifact-dir") == os.fspath(job_root)
        assert _option(first, "--receipt") == os.fspath(job_root / "receipt.json")
        assert _option(first, "--manifest") == os.fspath(
            wave_root / "manifest.json"
        )
        base_commit = _option(first, "--base-commit")
        assert len(base_commit) == 40
        assert all(character in "0123456789abcdef" for character in base_commit)


def test_resource_defaults_and_overrides() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        defaults = _argv(_invoke(root, stage="plan", reasoning="max"))
        assert _option(defaults, "--max-wall-clock-s") == "3600"
        assert _option(defaults, "--max-model-calls") == "100"
        assert _option(defaults, "--max-cli-reported-tokens") == "1000000"
        overridden = _argv(
            _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=(
                    "--max-wall-clock-s",
                    "17",
                    "--max-model-calls",
                    "23",
                    "--max-cli-reported-tokens",
                    "29000",
                    "--sandbox",
                    "workspace-write",
                    "--job-id",
                    "explicit-job",
                ),
            )
        )
        assert _option(overridden, "--max-wall-clock-s") == "17"
        assert _option(overridden, "--max-model-calls") == "23"
        assert _option(overridden, "--max-cli-reported-tokens") == "29000"
        assert _option(overridden, "--sandbox") == "workspace-write"
        assert _option(overridden, "--job-id") == "explicit-job"
        assert _option(overridden, "--artifact-dir") == os.fspath(
            root / "artifacts" / "wave-alpha" / "explicit-job"
        )


def test_invalid_reasoning_for_bound_stages_is_rc2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for stage in ("review", "focus"):
            result = _invoke(root, stage=stage, reasoning="high")
            assert result.returncode == 2
            assert "--reasoning" in result.stderr


def test_lane_outside_consult_is_rc2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _invoke(
            Path(tmp), stage="plan", lane="sol", reasoning="max"
        )
        assert result.returncode == 2
        assert "--lane" in result.stderr


def test_consult_without_lane_is_rc2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _invoke(Path(tmp), stage="consult", reasoning="max")
        assert result.returncode == 2
        assert "--lane" in result.stderr


def test_unknown_stage_is_rc2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _invoke(Path(tmp), stage="unknown", reasoning="max")
        assert result.returncode == 2
        assert "invalid choice" in result.stderr


def test_relative_paths_are_rc2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        replacements = (
            ("--prompt-file", "prompt.md"),
            ("--artifact-root", "artifacts"),
            ("--output-file", "answer.md"),
            ("--repo-root", "repo"),
        )
        for option, relative in replacements:
            result = _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=(option, relative),
            )
            assert result.returncode == 2
            assert "absolute path" in result.stderr


def test_unbound_stage_requires_reasoning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _invoke(Path(tmp), stage="author")
        assert result.returncode == 2
        assert "--reasoning" in result.stderr


def test_help_marks_resource_defaults_non_authoritative() -> None:
    result = subprocess.run(
        [sys.executable, os.fspath(_DISPATCHER), "--help"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    phrase = "これは非権威の運用既定であり docs 権威ではない"
    normalized_help = " ".join(result.stdout.split())
    assert normalized_help.count(phrase) == 3


def _run() -> int:
    functions = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failed = 0
    for function in functions:
        try:
            function()
        except Exception as exc:  # noqa: BLE001 - plain runner reports failures.
            failed += 1
            print(f"FAIL {function.__name__}: {exc}", file=sys.stderr)
        else:
            print(f"PASS {function.__name__}")
    print(f"{len(functions) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
