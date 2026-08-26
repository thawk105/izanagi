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


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode(
        "ascii"
    ).strip()


def _ledger_digest(seed: str) -> str:
    return hashlib.sha256(f"ratification-ledger:{seed}".encode("ascii")).hexdigest()


def _commit_tree_with_raw_ledger(
    repo: Path,
    raw: bytes | None,
    parents: tuple[str, ...],
    message: str,
) -> str:
    if parents:
        _git(repo, "reset", "-q", "--hard", parents[0])
    ledger = repo / R.RATIFICATION_LEDGER_RELATIVE_PATH
    if ledger.is_symlink() or ledger.exists():
        ledger.unlink()
    _git(
        repo,
        "rm", "-q", "--cached", "--ignore-unmatch", "--",
        R.RATIFICATION_LEDGER_RELATIVE_PATH,
    )
    if raw is not None:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_bytes(raw)
        _git(repo, "add", "--", R.RATIFICATION_LEDGER_RELATIVE_PATH)
    tree = _git(repo, "write-tree").decode("ascii").strip()
    args = [
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit-tree", tree,
    ]
    for parent in parents:
        args.extend(("-p", parent))
    args.extend(("-m", message))
    commit = _git(repo, *args).decode("ascii").strip()
    _git(repo, "reset", "-q", "--hard", commit)
    return commit


def _commit_tree_with_rows(
    repo: Path,
    rows: list[str] | None,
    parents: tuple[str, ...],
    message: str,
) -> str:
    raw = None if rows is None else b"".join(_row(digest) for digest in rows)
    return _commit_tree_with_raw_ledger(repo, raw, parents, message)


def _commit_tree_with_symlink_ledger(
    repo: Path, digest: str, parent: str,
) -> str:
    _git(repo, "reset", "-q", "--hard", parent)
    ledger = repo / R.RATIFICATION_LEDGER_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    if ledger.is_symlink() or ledger.exists():
        ledger.unlink()
    ledger.symlink_to(_row(digest).decode("ascii"))
    _git(repo, "add", "--", R.RATIFICATION_LEDGER_RELATIVE_PATH)
    tree = _git(repo, "write-tree").decode("ascii").strip()
    commit = _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit-tree", tree, "-p", parent, "-m", "introduce symlink ledger",
    ).decode("ascii").strip()
    _git(repo, "reset", "-q", "--hard", commit)
    return commit


def _commit_tree_with_gitlink_ledger(repo: Path, parent: str) -> str:
    _git(repo, "reset", "-q", "--hard", parent)
    ledger = repo / R.RATIFICATION_LEDGER_RELATIVE_PATH
    if ledger.is_symlink() or ledger.exists():
        ledger.unlink()
    _git(
        repo,
        "update-index", "--add", "--cacheinfo", "160000", parent,
        R.RATIFICATION_LEDGER_RELATIVE_PATH,
    )
    tree = _git(repo, "write-tree").decode("ascii").strip()
    commit = _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit-tree", tree, "-p", parent, "-m", "introduce gitlink ledger",
    ).decode("ascii").strip()
    _git(repo, "update-ref", "HEAD", commit)
    return commit


def _git_path(repo: Path, relative: str) -> Path:
    raw = _git(repo, "rev-parse", "--git-path", relative).decode("utf-8").strip()
    path = Path(raw)
    return path if path.is_absolute() else repo / path


def _unparented_commit(repo: Path, message: str) -> str:
    tree = _git(repo, "write-tree").decode("ascii").strip()
    return _git(
        repo,
        "-c", "user.email=t1287-fixture@example.invalid",
        "-c", "user.name=T1287 fixture",
        "commit-tree", tree, "-m", message,
    ).decode("ascii").strip()


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


def test_pre_ledger_branch_merge_with_unchanged_ledger_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    root = _head(repo)
    side = _commit_tree_with_rows(repo, None, (root,), "pre-ledger side work")
    digest = _ledger_digest("base")
    introduced = _commit_tree_with_rows(
        repo, [digest], (root,), "introduce ledger",
    )
    _commit_tree_with_rows(
        repo, [digest], (introduced, side), "merge pre-ledger side",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({digest})


def test_concurrent_branch_appends_are_accepted_after_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    base, left_digest, right_digest = (
        _ledger_digest(seed) for seed in ("base", "left", "right")
    )
    introduced = _commit_tree_with_rows(
        repo, [base], (_head(repo),), "introduce ledger",
    )
    left = _commit_tree_with_rows(
        repo, [base, left_digest], (introduced,), "left appends",
    )
    right = _commit_tree_with_rows(
        repo, [base, right_digest], (introduced,), "right appends",
    )
    _commit_tree_with_rows(
        repo,
        [base, left_digest, right_digest],
        (left, right),
        "merge concurrent appends",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({
        base, left_digest, right_digest,
    })


def test_single_parent_middle_insertion_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    first, middle, last = (
        _ledger_digest(seed) for seed in ("first", "middle", "last")
    )
    introduced = _commit_tree_with_rows(
        repo, [first], (_head(repo),), "introduce ledger",
    )
    picked = _commit_tree_with_rows(
        repo, [first, last], (introduced,), "append future last row",
    )
    _commit_tree_with_rows(
        repo, [first, middle, last], (picked,), "rebase inserts middle row",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({
        first, middle, last,
    })


def test_opposite_branch_orders_are_accepted_after_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    first, second, third = (
        _ledger_digest(seed) for seed in ("first", "second", "third")
    )
    introduced = _commit_tree_with_rows(
        repo, [first], (_head(repo),), "introduce ledger",
    )
    left_first = _commit_tree_with_rows(
        repo, [first, second], (introduced,), "left appends second",
    )
    left = _commit_tree_with_rows(
        repo, [first, second, third], (left_first,), "left appends third",
    )
    right_first = _commit_tree_with_rows(
        repo, [first, third], (introduced,), "right appends third",
    )
    right = _commit_tree_with_rows(
        repo, [first, third, second], (right_first,), "right appends second",
    )
    _commit_tree_with_rows(
        repo, [first, second, third], (left, right), "merge opposite orders",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({
        first, second, third,
    })


def test_octopus_branch_appends_are_accepted_after_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    base = _ledger_digest("base")
    additions = [_ledger_digest(seed) for seed in ("one", "two", "three")]
    introduced = _commit_tree_with_rows(
        repo, [base], (_head(repo),), "introduce ledger",
    )
    branches = tuple(
        _commit_tree_with_rows(
            repo, [base, digest], (introduced,), f"branch appends {index}",
        )
        for index, digest in enumerate(additions, start=1)
    )
    _commit_tree_with_rows(
        repo, [base, *additions], branches, "octopus merge",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({base, *additions})


def test_repeated_pre_ledger_branch_merges_are_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    root = _head(repo)
    side_one = _commit_tree_with_rows(repo, None, (root,), "old side one")
    side_two = _commit_tree_with_rows(
        repo, None, (side_one,), "old side two",
    )
    digest = _ledger_digest("base")
    introduced = _commit_tree_with_rows(
        repo, [digest], (root,), "introduce ledger",
    )
    merged_once = _commit_tree_with_rows(
        repo, [digest], (introduced, side_one), "first old-side merge",
    )
    _commit_tree_with_rows(
        repo, [digest], (merged_once, side_two), "second old-side merge",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({digest})


def test_two_independent_ledger_introductions_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    root = _head(repo)
    first = _ledger_digest("first")
    second = _ledger_digest("second")
    first_intro = _commit_tree_with_rows(
        repo, [first], (root,), "first introduction",
    )
    second_intro = _commit_tree_with_rows(
        repo, [second], (root,), "second introduction",
    )
    _commit_tree_with_rows(
        repo, [first, second], (first_intro, second_intro),
        "merge independent introductions",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="has more than one ledger introduction",
    ):
        R._committed_ratification_digests()


def test_merge_omitting_one_parent_row_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    base, left_digest, right_digest = (
        _ledger_digest(seed) for seed in ("base", "left", "right")
    )
    introduced = _commit_tree_with_rows(
        repo, [base], (_head(repo),), "introduce ledger",
    )
    left = _commit_tree_with_rows(
        repo, [base, left_digest], (introduced,), "left appends",
    )
    right = _commit_tree_with_rows(
        repo, [base, right_digest], (introduced,), "right appends",
    )
    _commit_tree_with_rows(
        repo, [base, left_digest], (left, right), "merge drops right row",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="not a strict prefix extension",
    ):
        R._committed_ratification_digests()


def test_merge_substituting_an_unknown_row_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    base, left_digest, right_digest, unknown = (
        _ledger_digest(seed)
        for seed in ("base", "left", "right", "unknown")
    )
    introduced = _commit_tree_with_rows(
        repo, [base], (_head(repo),), "introduce ledger",
    )
    left = _commit_tree_with_rows(
        repo, [base, left_digest], (introduced,), "left appends",
    )
    right = _commit_tree_with_rows(
        repo, [base, right_digest], (introduced,), "right appends",
    )
    _commit_tree_with_rows(
        repo, [base, left_digest, unknown], (left, right),
        "merge substitutes an unknown row",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="not a strict prefix extension",
    ):
        R._committed_ratification_digests()


def test_merge_adding_two_new_rows_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    base, left_digest, right_digest, extra_one, extra_two = (
        _ledger_digest(seed)
        for seed in ("base", "left", "right", "extra-one", "extra-two")
    )
    introduced = _commit_tree_with_rows(
        repo, [base], (_head(repo),), "introduce ledger",
    )
    left = _commit_tree_with_rows(
        repo, [base, left_digest], (introduced,), "left appends",
    )
    right = _commit_tree_with_rows(
        repo, [base, right_digest], (introduced,), "right appends",
    )
    _commit_tree_with_rows(
        repo,
        [base, left_digest, right_digest, extra_one, extra_two],
        (left, right),
        "merge appends two rows",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="added more than one row",
    ):
        R._committed_ratification_digests()


def test_invalid_middle_history_transition_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    first, replacement, final = (
        _ledger_digest(seed) for seed in ("first", "replacement", "final")
    )
    introduced = _commit_tree_with_rows(
        repo, [first], (_head(repo),), "introduce ledger",
    )
    invalid = _commit_tree_with_rows(
        repo, [replacement], (introduced,), "replace row in middle history",
    )
    _commit_tree_with_rows(
        repo, [replacement, final], (invalid,), "normal append at head",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="not a strict prefix extension",
    ):
        R._committed_ratification_digests()


def test_crlf_ratification_ledger_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    digest = _ledger_digest("crlf")
    raw = _row(digest).replace(b"\n", b"\r\n")
    _commit_tree_with_raw_ledger(
        repo, raw, (_head(repo),), "introduce CRLF ledger",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="not canonical JSON",
    ):
        R._committed_ratification_digests()


def test_non_regular_ledger_entries_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    for kind in ("symlink", "gitlink"):
        case_root = tmp_path / kind
        case_root.mkdir()
        repo = _repo(case_root)
        parent = _head(repo)
        if kind == "symlink":
            _commit_tree_with_symlink_ledger(
                repo, _ledger_digest("symlink"), parent,
            )
        else:
            _commit_tree_with_gitlink_ledger(repo, parent)
        monkeypatch.setattr(R, "_REPO_ROOT", repo)

        with pytest.raises(
            R.EnforcementSourceRatificationError,
            match="not a blob in committed history",
        ):
            R._committed_ratification_digests()


def test_shallow_repository_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = _repo(source_root)
    digest = _ledger_digest("shallow")
    _commit_tree_with_rows(
        source, [digest], (_head(source),), "introduce ledger",
    )
    clone_root = tmp_path / "clone-root"
    clone_root.mkdir()
    _git(
        clone_root,
        "clone", "-q", "--depth=1", source.as_uri(), "shallow",
    )
    shallow = clone_root / "shallow"
    monkeypatch.setattr(R, "_REPO_ROOT", shallow)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="requires a non-shallow repository",
    ):
        R._committed_ratification_digests()


def test_effective_graft_file_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    digest = _ledger_digest("graft")
    _commit_tree_with_rows(repo, [digest], (_head(repo),), "introduce ledger")
    grafts = _git_path(repo, "info/grafts")
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_bytes((_head(repo) + "\n").encode("ascii"))
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationError,
        match="cannot use Git grafts",
    ):
        R._committed_ratification_digests()


def test_empty_graft_and_unrelated_replace_ref_are_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    digest = _ledger_digest("base")
    _commit_tree_with_rows(repo, [digest], (_head(repo),), "introduce ledger")
    grafts = _git_path(repo, "info/grafts")
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_bytes(b"")
    original = _unparented_commit(repo, "unreachable original")
    replacement = _unparented_commit(repo, "unreachable replacement")
    _git(repo, "update-ref", f"refs/replace/{original}", replacement)
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    assert R._committed_ratification_digests() == frozenset({digest})


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
