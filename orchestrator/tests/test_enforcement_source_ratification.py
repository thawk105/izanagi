# -*- coding: utf-8 -*-
"""[T-1287] read-only enforcement-source closure ratification tests."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from orchestrator.campaign import campaign_lock
from orchestrator.campaign import enforcement_source_ratification as R


_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)


def _git(repo: Path, *args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("ratification test requires git")
    env = {
        key: os.environ[key]
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    completed = subprocess.run(
        [executable, "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
        timeout=30,
    )
    if completed.returncode != 0:
        pytest.fail(
            f"ratification test git failed: args={args!r} "
            f"stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "ratification-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    marker = repo / "marker"
    marker.write_text("ratification fixture\n", encoding="ascii")
    _git(repo, "add", "--", "marker")
    _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit", "-q", "-m", "initialize ratification fixture",
    )
    return repo


def _closure_map(seed: str) -> dict[str, str]:
    return {
        relative: hashlib.sha256(f"{seed}:{relative}".encode("ascii")).hexdigest()
        for relative in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    }


def _row(digest: str) -> bytes:
    return (
        json.dumps(
            {"schema_version": 1, "closure_digest_sha256": digest},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        + b"\n"
    )


def _commit_ledger(repo: Path, rows: list[str], message: str) -> None:
    ledger = repo / R.RATIFICATION_LEDGER_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_bytes(b"".join(_row(digest) for digest in rows))
    _git(repo, "add", "--", R.RATIFICATION_LEDGER_RELATIVE_PATH)
    _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit", "-q", "-m", message,
    )


def _commit_raw_ledger(repo: Path, raw: bytes, message: str) -> None:
    ledger = repo / R.RATIFICATION_LEDGER_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_bytes(raw)
    _git(repo, "add", "--", R.RATIFICATION_LEDGER_RELATIVE_PATH)
    _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit", "-q", "-m", message,
    )


def test_closure_digest_is_canonical_map_hash_without_commit_identity() -> None:
    blob_map = _closure_map("same-bytes")
    reversed_map = dict(reversed(tuple(blob_map.items())))

    expected = hashlib.sha256(json.dumps(
        blob_map,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")).hexdigest()

    assert R.closure_digest_sha256(blob_map) == expected
    assert R.closure_digest_sha256(reversed_map) == expected


@pytest.mark.parametrize(
    ("raw", "message"),
    (
        (
            b'{"closure_digest_sha256":"' + b"0" * 64
            + b'", "schema_version":1}\n',
            "not canonical JSON",
        ),
        (
            b'{"closure_digest_sha256":"' + b"0" * 64
            + b'","extra":false,"schema_version":1}\n',
            "non-exact schema",
        ),
        (
            b'{"closure_digest_sha256":"' + b"0" * 64
            + b'","schema_version":1}',
            "not newline terminated",
        ),
    ),
    ids=("whitespace", "extra-key", "missing-newline"),
)
def test_ratification_ledger_requires_strict_canonical_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: bytes, message: str,
) -> None:
    repo = _repo(tmp_path)
    _commit_raw_ledger(repo, raw, "record malformed ratification row")
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(R.EnforcementSourceRatificationError, match=message):
        R.require_ratified_closure(_closure_map("not-present"))


def test_unratified_closure_digest_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="enforcement-source-closure-unratified",
    ):
        R.require_ratified_closure(_closure_map("unratified"))


def test_fake_git_at_front_of_path_cannot_forge_ratification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    marker = tmp_path / "fake-git-ran"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        f"touch {marker}\n"
        "exit 0\n",
        encoding="ascii",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv(
        "PATH", os.fspath(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="enforcement-source-closure-unratified",
    ):
        R.require_ratified_closure(_closure_map("forged-by-path"))
    assert not marker.exists()


def test_ratified_closure_digest_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    blob_map = _closure_map("ratified")
    digest = R.closure_digest_sha256(blob_map)
    _commit_ledger(repo, [digest], "record one ratification")
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R.require_ratified_closure(blob_map) == digest


def test_ratified_digest_rejects_a_different_actual_path_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    ratified = _closure_map("ratified")
    _commit_ledger(
        repo,
        [R.closure_digest_sha256(ratified)],
        "record one ratification",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="enforcement-source-closure-unratified",
    ):
        R.require_ratified_closure(_closure_map("different-actual-map"))


def test_committed_ratification_row_deletion_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    blob_map = _closure_map("ratified")
    digest = R.closure_digest_sha256(blob_map)
    _commit_ledger(repo, [digest], "record one ratification")
    ledger = repo / R.RATIFICATION_LEDGER_RELATIVE_PATH
    ledger.unlink()
    _git(repo, "add", "-u", "--", R.RATIFICATION_LEDGER_RELATIVE_PATH)
    _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit", "-q", "-m", "delete ratification ledger",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="deleted in committed history",
    ):
        R.require_ratified_closure(blob_map)


def test_committed_ratification_row_replacement_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    first = R.closure_digest_sha256(_closure_map("first"))
    replacement = R.closure_digest_sha256(_closure_map("replacement"))
    _commit_ledger(repo, [first], "record first ratification")
    _commit_ledger(repo, [replacement], "replace ratification row")
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="not a strict prefix extension",
    ):
        R.require_ratified_closure(_closure_map("replacement"))


def test_committed_ratification_row_reordering_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    first = R.closure_digest_sha256(_closure_map("first"))
    second = R.closure_digest_sha256(_closure_map("second"))
    _commit_ledger(repo, [first], "record first ratification")
    _commit_ledger(repo, [first, second], "record second ratification")
    _commit_ledger(repo, [second, first], "reorder ratification rows")
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="not a strict prefix extension",
    ):
        R.require_ratified_closure(_closure_map("first"))


def test_committed_multirow_addition_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    first = R.closure_digest_sha256(_closure_map("first"))
    second = R.closure_digest_sha256(_closure_map("second"))
    third = R.closure_digest_sha256(_closure_map("third"))
    _commit_ledger(repo, [first], "record first ratification")
    _commit_ledger(
        repo,
        [first, second, third],
        "append two ratification rows without an intervening review",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="added more than one row",
    ):
        R.require_ratified_closure(_closure_map("third"))
