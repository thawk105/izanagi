from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from orchestrator.preregistration.blobref import (
    BlobDigestMismatchError,
    BlobRef,
    InvalidBlobRefError,
    read_pinned_blob,
)


class _EqualitySpoofingStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    def __str__(self) -> str:
        return "attacker-controlled __str__ result"

    __hash__ = str.__hash__


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


@pytest.fixture
def git_blob_fixture(tmp_path: Path) -> tuple[Path, bytes, str]:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "T139 BlobRef test")
    _git(root, "config", "user.email", "t139-blobref@example.invalid")
    blob = b"approved positive blob\n"
    (root / "regular.txt").write_bytes(blob)
    _git(root, "add", "regular.txt")
    _git(root, "commit", "-q", "-m", "fixture")
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    return root, blob, commit


def test_sha256_subclass_cannot_bypass_digest_mismatch(git_blob_fixture):
    root, _blob, commit = git_blob_fixture
    spoofed_sha256 = _EqualitySpoofingStr("0" * 64)
    ref = BlobRef("regular.txt", commit, spoofed_sha256)

    assert type(ref.sha256) is str
    assert ref.sha256 == "0" * 64
    with pytest.raises(BlobDigestMismatchError):
        read_pinned_blob(root, ref)


def test_commit_subclass_is_stored_as_exact_builtin_str(git_blob_fixture):
    root, blob, commit = git_blob_fixture
    ref = BlobRef(
        "regular.txt",
        _EqualitySpoofingStr(commit),
        hashlib.sha256(blob).hexdigest(),
    )

    assert type(ref.commit) is str
    assert ref.commit == commit
    assert read_pinned_blob(root, ref) == blob


def test_path_subclass_is_normalized_and_cannot_hide_noncanonical_path(
    git_blob_fixture,
):
    root, blob, commit = git_blob_fixture
    ref = BlobRef(
        _EqualitySpoofingStr("regular.txt"),
        commit,
        hashlib.sha256(blob).hexdigest(),
    )

    assert type(ref.path) is str
    assert ref.path == "regular.txt"
    assert read_pinned_blob(root, ref) == blob
    with pytest.raises(InvalidBlobRefError):
        BlobRef(
            _EqualitySpoofingStr("directory//regular.txt"),
            commit,
            hashlib.sha256(blob).hexdigest(),
        )


def test_post_init_sha256_subclass_reinjection_is_rejected(git_blob_fixture):
    root, blob, commit = git_blob_fixture
    ref = BlobRef("regular.txt", commit, hashlib.sha256(blob).hexdigest())
    object.__setattr__(
        ref, "sha256", _EqualitySpoofingStr(hashlib.sha256(blob).hexdigest())
    )

    with pytest.raises(InvalidBlobRefError, match=r"ref\.sha256"):
        read_pinned_blob(root, ref)


def test_post_init_commit_subclass_reinjection_is_rejected(git_blob_fixture):
    root, blob, commit = git_blob_fixture
    ref = BlobRef("regular.txt", commit, hashlib.sha256(blob).hexdigest())
    object.__setattr__(ref, "commit", _EqualitySpoofingStr(commit))

    with pytest.raises(InvalidBlobRefError, match=r"ref\.commit"):
        read_pinned_blob(root, ref)


def test_post_init_path_subclass_reinjection_is_rejected(git_blob_fixture):
    root, blob, commit = git_blob_fixture
    ref = BlobRef("regular.txt", commit, hashlib.sha256(blob).hexdigest())
    object.__setattr__(ref, "path", _EqualitySpoofingStr("regular.txt"))

    with pytest.raises(InvalidBlobRefError, match=r"ref\.path"):
        read_pinned_blob(root, ref)


def test_plain_str_positive_reference_remains_accepted(git_blob_fixture):
    root, blob, commit = git_blob_fixture
    ref = BlobRef(
        "regular.txt",
        commit,
        hashlib.sha256(blob).hexdigest(),
    )

    assert type(ref.path) is str
    assert type(ref.commit) is str
    assert type(ref.sha256) is str
    assert read_pinned_blob(os.fspath(root), ref) == blob


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
