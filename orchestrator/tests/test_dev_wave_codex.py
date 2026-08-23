# -*- coding: utf-8 -*-
"""tools/dev_wave_codex.py の dry-run argv 契約。"""
from __future__ import annotations

import hashlib
import json
import os
import stat
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
    sandbox: str | None = "read-only",
    prompt_text: str = "test prompt\n",
    extra: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    (root / "prompt.md").write_text(prompt_text, encoding="utf-8")
    (root / "artifacts").mkdir(exist_ok=True)
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
    ]
    if sandbox is not None:
        command.extend(("--sandbox", sandbox))
    command.append("--dry-run")
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


def _help_option_block(output: str, option: str) -> str:
    lines = output.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if line.startswith("  -") and option in line.split()
    ]
    assert len(starts) == 1, (option, starts)
    start = starts[0]
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("  -")
        ),
        len(lines),
    )
    return " ".join(" ".join(lines[start:end]).split())


def test_dry_run_stage_and_lane_matrix() -> None:
    cases = (
        ("plan", None, "max", "read-only"),
        ("consult", "sol", "max", "read-only"),
        ("consult", "luna", "max", "read-only"),
        ("author", None, None, "workspace-write"),
        ("review", None, None, "read-only"),
        ("fix", None, None, "workspace-write"),
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
                    sandbox=sandbox,
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
            if stage in ("review", "focus", "author", "fix"):
                assert "--reasoning" not in argv
            else:
                assert _option(argv, "--reasoning") == reasoning


def test_paths_and_job_id_are_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = _argv(
            _invoke(
                root,
                stage="consult",
                lane="luna",
                reasoning="max",
                extra=("--job-id", "wave-alpha-consult-luna"),
            )
        )
        second = _argv(
            _invoke(
                root,
                stage="consult",
                lane="luna",
                reasoning="max",
                extra=("--job-id", "wave-alpha-consult-luna"),
            )
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
        assert _option(defaults, "--wall-clock-admission-bound-s") == "3600"
        assert _option(defaults, "--max-model-calls") == "100"
        assert _option(defaults, "--max-cli-reported-tokens") == "1000000"
        assert "--max-attempts" not in defaults
        overridden = _argv(
            _invoke(
                root,
                stage="plan",
                reasoning="max",
                sandbox="workspace-write",
                extra=(
                    "--wall-clock-admission-bound-s",
                    "17",
                    "--max-model-calls",
                    "23",
                    "--max-cli-reported-tokens",
                    "29000",
                    "--job-id",
                    "explicit-job",
                ),
            )
        )
        assert _option(overridden, "--wall-clock-admission-bound-s") == "17"
        assert _option(overridden, "--max-model-calls") == "23"
        assert _option(overridden, "--max-cli-reported-tokens") == "29000"
        assert _option(overridden, "--sandbox") == "workspace-write"
        assert _option(overridden, "--job-id") == "explicit-job"
        assert _option(overridden, "--artifact-dir") == os.fspath(
            root / "artifacts" / "wave-alpha" / "explicit-job"
        )

        retried = _argv(
            _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=("--max-attempts", "2"),
            )
        )
        assert retried.count("--max-attempts") == 1
        assert _option(retried, "--max-attempts") == "2"


def test_evidence_grace_default_and_decimal_override_are_forwarded_once() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        defaults = _argv(_invoke(root, stage="plan", reasoning="max"))
        assert defaults.count("--evidence-grace-s") == 1
        assert _option(defaults, "--evidence-grace-s") == "90"

        overridden = _argv(
            _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=("--evidence-grace-s", "12.5"),
            )
        )
        assert overridden.count("--evidence-grace-s") == 1
        assert _option(overridden, "--evidence-grace-s") == "12.5"

        low_wall_clock = _argv(
            _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=("--wall-clock-admission-bound-s", "17"),
            )
        )
        assert low_wall_clock.count("--evidence-grace-s") == 1
        assert _option(low_wall_clock, "--evidence-grace-s") == "17"


def test_evidence_grace_rejects_nonpositive_nonfinite_or_unsafe_values() -> None:
    help_result = subprocess.run(
        [sys.executable, os.fspath(_DISPATCHER), "--help"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "--evidence-grace-s" in _help_option_block(
        help_result.stdout, "--evidence-grace-s"
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        valid = _invoke(
            root,
            stage="plan",
            reasoning="max",
            extra=("--evidence-grace-s", "90"),
        )
        valid_argv = _argv(valid)
        assert valid_argv.count("--evidence-grace-s") == 1
        assert _option(valid_argv, "--evidence-grace-s") == "90"

        for value in (
            "0",
            "-1",
            "NaN",
            "Infinity",
            "1e-10000",
            "9.999999999999999999999999999999999999e-10",
            "1e10000",
        ):
            rejected = _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=("--evidence-grace-s", value),
            )
            assert rejected.returncode == 2, (value, rejected.stderr)
            assert "正の有限数で nanosecond へ安全に変換" in rejected.stderr

        for value in (
            "0.000000001",
            "0.000000001000000000000000000000000001",
            "12.3456789012345678901234567890123456789",
        ):
            accepted = _invoke(
                root,
                stage="plan",
                reasoning="max",
                extra=("--evidence-grace-s", value),
            )
            assert accepted.returncode == 0, (value, accepted.stderr)
            accepted_argv = _argv(accepted)
            assert _option(accepted_argv, "--evidence-grace-s") == value


def test_evidence_grace_must_not_exceed_max_wall_clock() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        valid = _invoke(
            root,
            stage="plan",
            reasoning="max",
            extra=(
                "--evidence-grace-s",
                "90",
                "--wall-clock-admission-bound-s",
                "3600",
            ),
        )
        valid_argv = _argv(valid)
        assert valid_argv.count("--evidence-grace-s") == 1
        assert _option(valid_argv, "--evidence-grace-s") == "90"

        rejected = _invoke(
            root,
            stage="plan",
            reasoning="max",
            extra=(
                "--evidence-grace-s",
                "90.5",
                "--wall-clock-admission-bound-s",
                "90",
            ),
        )
        assert rejected.returncode == 2
        assert (
            "--evidence-grace-s は --wall-clock-admission-bound-s 以下"
            in rejected.stderr
        )


def test_default_job_id_binds_full_prompt_sha256() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        prompt = "review lens A\n"
        argv = _argv(
            _invoke(root, stage="review", prompt_text=prompt)
        )
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        assert _option(argv, "--job-id") == f"wave-alpha-review-{digest}"


def test_sandbox_is_caller_required() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _invoke(
            Path(tmp), stage="plan", reasoning="max", sandbox=None
        )
        assert result.returncode == 2
        assert "--sandbox" in result.stderr


def test_dry_run_creates_generated_directories() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "artifacts").mkdir()
        result = _invoke(root, stage="review")
        assert result.returncode == 0, result.stderr
        argv = _argv(result)
        wave_artifact_root = root / "artifacts" / "wave-alpha"
        artifact_dir = Path(_option(argv, "--artifact-dir"))
        assert wave_artifact_root.is_dir()
        assert artifact_dir.is_dir()
        assert stat.S_IMODE(wave_artifact_root.stat().st_mode) == 0o700
        assert stat.S_IMODE(artifact_dir.stat().st_mode) == 0o700


def _prepare_fake_repo(root: Path) -> None:
    (root / "tools").mkdir(parents=True)
    (root / "tools/codex_worker_launch.py").write_text(
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def option(name):
    index = sys.argv.index(name)
    return sys.argv[index + 1]

entry = {
    "job_id": option("--job-id"),
    "repo_root": option("--repo-root"),
    "artifact_dir": option("--artifact-dir"),
    "receipt": option("--receipt"),
    "output": option("--output-file"),
}
manifest = Path(option("--manifest"))
entries = json.loads(manifest.read_text()) if manifest.exists() else []
entries.append(entry)
manifest.write_text(json.dumps(entries))
Path(entry["receipt"]).write_text(json.dumps(entry))
Path(entry["output"]).write_text(entry["job_id"] + "\\n")
""",
        encoding="utf-8",
    )
    subprocess.run(("git", "-C", os.fspath(root), "init", "-q"), check=True)
    subprocess.run(
        ("git", "-C", os.fspath(root), "config", "user.name", "dispatcher-test"),
        check=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            os.fspath(root),
            "config",
            "user.email",
            "dispatcher-test@example.invalid",
        ),
        check=True,
    )
    subprocess.run(("git", "-C", os.fspath(root), "add", "tools"), check=True)
    subprocess.run(
        ("git", "-C", os.fspath(root), "commit", "-qm", "fake launcher"),
        check=True,
    )


def _run_fake_dispatch(
    *,
    repo_root: Path,
    artifact_root: Path,
    prompt_file: Path,
    output_file: Path,
    stage: str,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        os.fspath(_DISPATCHER),
        "--stage",
        stage,
        "--wave",
        "wave-shared",
        "--prompt-file",
        os.fspath(prompt_file),
        "--artifact-root",
        os.fspath(artifact_root),
        "-o",
        os.fspath(output_file),
        "--repo-root",
        os.fspath(repo_root),
        "--sandbox",
        "read-only",
    ]
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_review_fix_jobs_create_private_paths_and_share_wave_manifest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        sibling = root / "sibling"
        repo.mkdir()
        _prepare_fake_repo(repo)
        subprocess.run(
            (
                "git",
                "-C",
                os.fspath(repo),
                "worktree",
                "add",
                "--detach",
                os.fspath(sibling),
                "HEAD",
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        artifact_root = root / "artifacts"
        output_root = root / "outputs"
        prompt_root = root / "prompts"
        artifact_root.mkdir()
        output_root.mkdir()
        prompt_root.mkdir()
        jobs = (
            ("review", repo, "review-a"),
            ("review", sibling, "review-b"),
            ("fix", repo, "fix-1"),
            ("fix", sibling, "fix-2"),
            ("fix", repo, "fix-3"),
        )
        outputs: list[Path] = []
        for stage, worktree, name in jobs:
            prompt = prompt_root / f"{name}.md"
            output = output_root / f"{name}.md"
            prompt.write_text(f"{name} prompt\n", encoding="utf-8")
            result = _run_fake_dispatch(
                repo_root=worktree,
                artifact_root=artifact_root,
                prompt_file=prompt,
                output_file=output,
                stage=stage,
            )
            assert result.returncode == 0, result.stderr
            outputs.append(output)

        wave_root = artifact_root / "wave-shared"
        entries = json.loads((wave_root / "manifest.json").read_text())
        assert len(entries) == 5
        assert len({entry["job_id"] for entry in entries}) == 5
        assert {entry["repo_root"] for entry in entries} == {
            os.fspath(repo),
            os.fspath(sibling),
        }
        assert len({entry["artifact_dir"] for entry in entries}) == 5
        assert len({entry["receipt"] for entry in entries}) == 5
        assert len({entry["output"] for entry in entries}) == 5
        assert all(output.is_file() for output in outputs)
        assert stat.S_IMODE(wave_root.stat().st_mode) == 0o700
        for entry in entries:
            artifact_dir = Path(entry["artifact_dir"])
            assert artifact_dir.is_dir()
            assert stat.S_IMODE(artifact_dir.stat().st_mode) == 0o700
            assert Path(entry["receipt"]).is_file()


def test_workspace_write_max_attempts_is_rejected_before_directory_creation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = _invoke(
            root,
            stage="author",
            sandbox="workspace-write",
            extra=("--max-attempts", "2"),
        )
        assert result.returncode == 2
        assert "read-only" in result.stderr
        assert not (root / "artifacts" / "wave-alpha").exists()


def test_invalid_reasoning_for_bound_stages_is_rc2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for stage in ("review", "focus", "author", "fix"):
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
        result = _invoke(Path(tmp), stage="plan")
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
    for option in (
        "--wall-clock-admission-bound-s",
        "--max-model-calls",
        "--max-cli-reported-tokens",
        "--evidence-grace-s",
    ):
        option_block = _help_option_block(result.stdout, option)
        assert option in option_block
        assert phrase in option_block
    evidence_block = _help_option_block(result.stdout, "--evidence-grace-s")
    assert "子の起動完了時を起点とする" in evidence_block
    assert "受理集合に影響する" in evidence_block
    assert "暫定運用値であり測定された最小値ではない" in evidence_block
    assert "90 秒を上限" in evidence_block
    assert "--wall-clock-admission-bound-s が 90 未満ならそれに切り下げる" in evidence_block


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
