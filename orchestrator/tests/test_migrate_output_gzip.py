"""Tests for ``tools/migrate_output_gzip.py`` using disposable Git repositories."""
from __future__ import annotations

import gzip
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "tools" / "migrate_output_gzip.py"
_SPEC = importlib.util.spec_from_file_location("migrate_output_gzip_under_test", _SCRIPT)
assert _SPEC and _SPEC.loader
MIGRATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MIGRATOR
_SPEC.loader.exec_module(MIGRATOR)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def _new_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "migration-test")
    _git(repo, "config", "user.email", "migration-test@example.invalid")
    return repo


def _commit_all(repo: Path, message: str = "fixture") -> None:
    _git(repo, "add", "--all")
    _git(repo, "commit", "-q", "-m", message)


def _write(repo: Path, relative: str, payload: bytes) -> Path:
    path = repo.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _status(repo: Path) -> str:
    return _git(repo, "status", "--porcelain").stdout


def _invoke(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--repo-root", str(repo), *arguments],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _common_args(*, mode: str = "--dry-run", min_bytes: int = 0) -> list[str]:
    return [
        "--root",
        "output",
        "--extension",
        ".json",
        "--min-bytes",
        str(min_bytes),
        mode,
    ]


def test_dry_run_is_read_only_and_applies_suffix_and_strict_size_filter(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    threshold = 4096
    _write(repo, "output/at.json", b"a" * threshold)
    _write(repo, "output/over.json", b"b" * (threshold + 1))
    _write(repo, "output/over.txt", b"c" * (threshold + 1))
    _commit_all(repo)
    before = _status(repo)

    result = _invoke(
        repo,
        "--root",
        "output",
        "--extension",
        ".json",
        "--min-bytes",
        str(threshold),
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert _status(repo) == before == ""
    assert "CANDIDATE path=output/over.json size=4097" in result.stdout
    assert "output/at.json size=4096" not in result.stdout
    assert "CANDIDATE path=output/over.txt" not in result.stdout
    assert "SUMMARY targets=1 source-bytes=4097" in result.stdout
    assert "compressed-bytes=" in result.stdout


def test_exclude_path_is_exact_and_does_not_exclude_same_basename(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    payload = b"fixture payload\n" * 400
    n1 = _write(
        repo,
        "output/insights/2026-07-10_s8a-n1-provenance.json",
        payload,
    )
    receipt = _write(
        repo,
        "output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json",
        payload,
    )
    retained = _write(
        repo,
        "output/insights/other/receipt-schema-v1.json",
        payload,
    )
    _commit_all(repo)

    result = _invoke(
        repo,
        "--root",
        "output/insights",
        "--extension",
        ".json",
        "--exclude-path",
        "output/insights/2026-07-10_s8a-n1-provenance.json",
        "--exclude-path",
        "output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json",
        "--min-bytes",
        "0",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert f"CANDIDATE path={retained.relative_to(repo).as_posix()}" in result.stdout
    assert f"CANDIDATE path={n1.relative_to(repo).as_posix()}" not in result.stdout
    assert f"CANDIDATE path={receipt.relative_to(repo).as_posix()}" not in result.stdout
    assert (
        "EXCLUDE output/insights/2026-07-10_s8a-n1-provenance.json "
        "reason=excluded-path detail=exact"
    ) in result.stdout
    assert (
        "EXCLUDE output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json "
        "reason=excluded-path detail=exact"
    ) in result.stdout
    assert "SUMMARY targets=1" in result.stdout


def test_apply_round_trip_is_byte_exact_and_stages_delete_and_add(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    original = (b"binary\x00payload\xff\n" * 700) + b"tail"
    source = _write(repo, "output/roundtrip.json", original)
    _commit_all(repo)

    result = _invoke(repo, *_common_args(mode="--apply"))

    assert result.returncode == 0, result.stderr
    destination = Path(f"{source}.gz")
    assert not source.exists()
    assert destination.exists()
    assert gzip.decompress(destination.read_bytes()) == original
    staged = _git(repo, "diff", "--cached", "--no-renames", "--name-status").stdout
    assert "D\toutput/roundtrip.json\n" in staged
    assert "A\toutput/roundtrip.json.gz\n" in staged
    assert "STAGED output/roundtrip.json" in result.stdout
    assert "SUMMARY targets=1" in result.stdout


def test_verification_mismatch_skips_without_touching_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _new_repo(tmp_path)
    original = b"the HEAD bytes must remain the identity\n" * 200
    source = _write(repo, "output/mismatch.json", original)
    _commit_all(repo)
    before_status = _status(repo)
    real_compress = MIGRATOR.compress_bytes

    def corrupt_compress(data: bytes) -> bytes:
        assert data == original
        return real_compress(b"intentionally different\n")

    monkeypatch.setattr(MIGRATOR, "compress_bytes", corrupt_compress)
    rc = MIGRATOR.main(
        [
            "--repo-root",
            str(repo),
            "--root",
            "output",
            "--extension",
            ".json",
            "--min-bytes",
            "0",
            "--apply",
        ]
    )

    assert rc == 0
    assert source.exists()
    assert source.read_bytes() == original
    assert not Path(f"{source}.gz").exists()
    assert _status(repo) == before_status == ""


def test_rerun_skips_source_missing_with_existing_gzip(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    source = _write(repo, "output/repeat.json", b"repeat me\n" * 500)
    _commit_all(repo)
    first = _invoke(repo, *_common_args(mode="--apply"))
    assert first.returncode == 0, first.stderr
    staged_before = _git(repo, "diff", "--cached", "--no-renames", "--name-status").stdout

    second = _invoke(repo, *_common_args(mode="--apply"))

    assert second.returncode == 0, second.stderr
    assert "SKIP output/repeat.json reason=processed-existing-gzip" in second.stdout
    assert "SUMMARY targets=0" in second.stdout
    assert _git(repo, "diff", "--cached", "--no-renames", "--name-status").stdout == staged_before
    assert not source.exists()
    assert Path(f"{source}.gz").exists()


def test_both_source_and_gzip_present_is_fatal_without_changes(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    source = _write(repo, "output/conflict.json", b"source\n" * 500)
    other = _write(repo, "output/other.json", b"other source\n" * 500)
    _commit_all(repo)
    destination = Path(f"{source}.gz")
    destination.write_bytes(b"pre-existing gzip placeholder")
    original_source = source.read_bytes()
    original_gzip = destination.read_bytes()

    result = _invoke(repo, *_common_args(mode="--apply"))

    assert result.returncode != 0
    assert "source-and-gzip-both-exist" in result.stdout
    assert "apply/dry-run stopped" in result.stdout
    assert source.read_bytes() == original_source
    assert destination.read_bytes() == original_gzip
    assert other.exists()
    assert not Path(f"{other}.gz").exists()
    assert "D\toutput/conflict.json" not in _git(
        repo, "diff", "--cached", "--no-renames", "--name-status"
    ).stdout


def test_symlink_and_hardlink_are_excluded_with_reasons(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    link_target = _write(repo, "link-target.bin", b"symlink target\n" * 300)
    symlink = repo / "output" / "symlink" / "link.json"
    symlink.parent.mkdir(parents=True)
    symlink.symlink_to(Path("../../link-target.bin"))

    hardlink_target = _write(repo, "hardlink-target.bin", b"hardlink target\n" * 300)
    hardlink = repo / "output" / "hardlink" / "alias.json"
    hardlink.parent.mkdir(parents=True)
    os.link(hardlink_target, hardlink)
    _commit_all(repo)

    result = _invoke(repo, *_common_args())

    assert result.returncode == 0, result.stderr
    assert "EXCLUDE output/symlink/link.json reason=symlink" in result.stdout
    assert "EXCLUDE output/hardlink/alias.json reason=hardlink" in result.stdout
    assert "SUMMARY targets=0" in result.stdout
    assert _status(repo) == ""


def test_parent_directory_symlink_is_excluded_before_any_write(
    tmp_path: Path,
) -> None:
    repo = _new_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    payload = b"parent symlink payload\n" * 300
    source = _write(repo, "output/nested/file.json", payload)
    _commit_all(repo)

    source.unlink()
    source.parent.rmdir()
    outside_file = outside / "file.json"
    outside_file.write_bytes(payload)
    source.parent.symlink_to(outside, target_is_directory=True)

    result = _invoke(repo, *_common_args())

    assert result.returncode == 0, result.stderr
    assert "EXCLUDE output/nested/file.json reason=symlink detail=parent=" in result.stdout
    assert "CANDIDATE path=output/nested/file.json" not in result.stdout
    assert not Path(f"{outside_file}.gz").exists()


def test_destination_bytes_are_checked_after_git_add(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _new_repo(tmp_path)
    original = b"destination bytes must remain deterministic\n" * 300
    source = _write(repo, "output/post-add.json", original)
    _commit_all(repo)
    destination = Path(f"{source}.gz")
    real_run_git_checked = MIGRATOR._run_git_checked

    def tamper_before_add(repo_arg: Path, git_args: list[str]) -> None:
        if git_args[:2] == ["add", "--"]:
            destination.write_bytes(b"tampered after install")
        real_run_git_checked(repo_arg, git_args)

    monkeypatch.setattr(MIGRATOR, "_run_git_checked", tamper_before_add)
    rc = MIGRATOR.main(
        [
            "--repo-root",
            str(repo),
            "--root",
            "output",
            "--extension",
            ".json",
            "--min-bytes",
            "0",
            "--apply",
        ]
    )

    output = capsys.readouterr().out
    assert rc != 0
    assert "post-stage gzip destination bytes changed" in output
    assert source.exists()
    assert source.read_bytes() == original
    assert destination.read_bytes() == b"tampered after install"
    assert "rollback failed" in output


def test_git_rm_failure_after_partial_unlink_restores_all_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _new_repo(tmp_path)
    first_bytes = b"first source\n" * 400
    second_bytes = b"second source\n" * 400
    first = _write(repo, "output/a.json", first_bytes)
    second = _write(repo, "output/b.json", second_bytes)
    _commit_all(repo)
    real_run_git_checked = MIGRATOR._run_git_checked

    def fail_after_partial_rm(repo_arg: Path, git_args: list[str]) -> None:
        if git_args[:2] == ["rm", "--"]:
            first.unlink()
            raise MIGRATOR.MigrationError("injected git rm failure")
        real_run_git_checked(repo_arg, git_args)

    monkeypatch.setattr(MIGRATOR, "_run_git_checked", fail_after_partial_rm)
    rc = MIGRATOR.main(
        [
            "--repo-root",
            str(repo),
            "--root",
            "output",
            "--extension",
            ".json",
            "--min-bytes",
            "0",
            "--apply",
        ]
    )

    output = capsys.readouterr().out
    assert rc != 0
    assert "injected git rm failure" in output
    assert first.read_bytes() == first_bytes
    assert second.read_bytes() == second_bytes
    assert not Path(f"{first}.gz").exists()
    assert not Path(f"{second}.gz").exists()
    assert _status(repo) == ""


def test_rollback_failure_is_reported_with_the_original_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _new_repo(tmp_path)
    source = _write(repo, "output/rollback.json", b"rollback source\n" * 400)
    _commit_all(repo)
    real_run_git = MIGRATOR._run_git

    def fail_git(repo_arg: Path, git_args: list[str]) -> subprocess.CompletedProcess[bytes]:
        if git_args[:2] == ["rm", "--"]:
            source.unlink()
            return subprocess.CompletedProcess(
                ["git", *git_args], 1, stdout=b"", stderr=b"primary failure"
            )
        if git_args[:2] == ["reset", "--"]:
            return subprocess.CompletedProcess(
                ["git", *git_args], 1, stdout=b"", stderr=b"rollback failure"
            )
        return real_run_git(repo_arg, git_args)

    monkeypatch.setattr(MIGRATOR, "_run_git", fail_git)
    rc = MIGRATOR.main(
        [
            "--repo-root",
            str(repo),
            "--root",
            "output",
            "--extension",
            ".json",
            "--min-bytes",
            "0",
            "--apply",
        ]
    )

    output = capsys.readouterr().out
    assert rc != 0
    assert "primary failure" in output
    assert "rollback failed" in output
    assert "rollback failure" in output


def test_unexpected_decode_exception_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _new_repo(tmp_path)

    def fail_resolve(_requested: Path | None) -> Path:
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid root")

    monkeypatch.setattr(MIGRATOR, "_resolve_repo_root", fail_resolve)
    rc = MIGRATOR.main(
        [
            "--repo-root",
            str(repo),
            "--root",
            "output",
            "--extension",
            ".json",
            "--min-bytes",
            "0",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert rc != 0
    assert "ERROR unexpected UnicodeDecodeError" in output
    assert "SUMMARY targets=0" in output
