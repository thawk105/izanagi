from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator.publication import ledger as L


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LEDGER_RELATIVE_PATH = Path("output/registry/t139-publication-reservations.jsonl")
PRIMARY_FAMILY_ROOT = "dce4ae4fed6f4fb33747165c5b92c16d01822850"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "T793 Test")
    _git(repo, "config", "user.email", "t793@example.invalid")
    seed = repo / "seed.txt"
    seed.write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _ledger_path(repo: Path) -> Path:
    path = repo / LEDGER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _entry(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "family_root": L.PUBLICATION_FAMILY_ROOT,
        "kind": L.PUBLICATION_LEDGER_KIND,
        "ordinal": 1,
        "schema_version": L.PUBLICATION_LEDGER_SCHEMA_VERSION,
    }
    value.update(changes)
    return value


def _canonical_line(value: dict[str, object]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _read(repo: Path) -> L.PublicationLedger:
    return L._read_publication_ledger_from_repository(repo)


def test_p4_present_zero_entry_canonical_ledger_is_accepted() -> None:
    result = L.read_publication_ledger()
    path = L.canonical_publication_ledger_path()
    assert path == REPOSITORY_ROOT / LEDGER_RELATIVE_PATH
    assert path.is_file()
    assert path.read_bytes() == b""
    assert result.entries == ()


def test_publication_identity_literals_and_schema_are_exact() -> None:
    assert L.PUBLICATION_FAMILY_ROOT == "88d68f9127b31df5aafc3d59607896626a1652e8"
    assert L.PUBLICATION_LEDGER_KIND == "individual_publication"
    assert (
        L.PUBLICATION_LEDGER_SCHEMA_VERSION
        == "t139-publication-reservation/v1"
    )


def test_one_canonical_publication_entry_is_structurally_readable(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _ledger_path(repo).write_bytes(_canonical_line(_entry()))
    result = _read(repo)
    assert result.entries == (
        L.PublicationReservation(
            family_root="88d68f9127b31df5aafc3d59607896626a1652e8",
            kind="individual_publication",
            ordinal=1,
            schema_version="t139-publication-reservation/v1",
        ),
    )


def test_canonical_path_and_public_readers_take_no_caller_input(tmp_path: Path) -> None:
    assert inspect.signature(L.canonical_publication_ledger_path).parameters == {}
    assert inspect.signature(L.read_publication_ledger).parameters == {}
    assert L.canonical_publication_ledger_path() == (
        REPOSITORY_ROOT / LEDGER_RELATIVE_PATH
    )
    with pytest.raises(TypeError):
        L.read_publication_ledger(tmp_path)  # type: ignore[call-arg]


def test_environment_cannot_redirect_the_canonical_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoy = "/tmp/caller-selected-publication-ledger.jsonl"
    for name in (
        "IZANAGI_PUBLICATION_LEDGER_PATH",
        "PUBLICATION_LEDGER_PATH",
        "T139_PUBLICATION_LEDGER_PATH",
    ):
        monkeypatch.setenv(name, decoy)
    assert L.canonical_publication_ledger_path() == (
        REPOSITORY_ROOT / LEDGER_RELATIVE_PATH
    )
    assert L.read_publication_ledger().entries == ()


def test_reservation_writer_and_success_admission_apis_do_not_exist() -> None:
    forbidden = {
        "reserve_next_publication",
        "append_publication_reservation",
        "is_submission_allowed",
        "ready_for_main",
        "admitted",
        "can_submit",
    }
    assert forbidden.isdisjoint(vars(L))


def test_missing_canonical_ledger_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    with pytest.raises(L.PublicationLedgerError, match=r"\[ledger-read\].*absent"):
        _read(repo)


def test_kind_outside_closed_publication_set_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _ledger_path(repo).write_bytes(_canonical_line(_entry(kind="exploratory")))
    with pytest.raises(L.PublicationLedgerError, match=r"\[ledger-kind\]"):
        _read(repo)


def test_nonliteral_publication_family_root_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _ledger_path(repo).write_bytes(_canonical_line(_entry(family_root="0" * 40)))
    with pytest.raises(L.PublicationLedgerError, match=r"\[family-root\]"):
        _read(repo)


def test_primary_entry_space_is_rejected_before_publication_identity(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    primary = _entry(
        family_root=PRIMARY_FAMILY_ROOT,
        kind="alpha_reservation",
        schema_version="t139-alpha-reservation/v1",
    )
    _ledger_path(repo).write_bytes(_canonical_line(primary))
    with pytest.raises(L.PublicationLedgerError, match=r"\[entry-space\]"):
        _read(repo)


def test_duplicate_root_kind_ordinal_identity_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    line = _canonical_line(_entry())
    _ledger_path(repo).write_bytes(line + line)
    with pytest.raises(L.PublicationLedgerError, match=r"\[entry-duplicate\]"):
        _read(repo)


@pytest.mark.parametrize(
    "payload, gate",
    (
        (
            (
                b'{"schema_version":"t139-publication-reservation/v1",'
                b'"ordinal":1,"kind":"individual_publication",'
                b'"family_root":"88d68f9127b31df5aafc3d59607896626a1652e8"}\n'
            ),
            "ledger-canonical",
        ),
        (
            (
                b'{"family_root": "88d68f9127b31df5aafc3d59607896626a1652e8",'
                b'"kind":"individual_publication","ordinal":1,'
                b'"schema_version":"t139-publication-reservation/v1"}\n'
            ),
            "ledger-canonical",
        ),
        (_canonical_line(_entry()) + b"\n", "ledger-framing"),
        (
            (
                b'{"family_root":"88d68f9127b31df5aafc3d59607896626a1652e8",'
                b'"family_root":"88d68f9127b31df5aafc3d59607896626a1652e8",'
                b'"kind":"individual_publication","ordinal":1,'
                b'"schema_version":"t139-publication-reservation/v1"}\n'
            ),
            "json",
        ),
    ),
    ids=("key-order", "whitespace", "blank-line", "duplicate-key"),
)
def test_noncanonical_jsonl_is_rejected(
    tmp_path: Path,
    payload: bytes,
    gate: str,
) -> None:
    repo = _init_repo(tmp_path)
    _ledger_path(repo).write_bytes(payload)
    with pytest.raises(L.PublicationLedgerError, match=rf"\[{gate}\]"):
        _read(repo)


@pytest.mark.parametrize(
    "changes",
    (
        {"schema_version": "t139-alpha-reservation/v1"},
        {"ordinal": 0},
        {"ordinal": True},
    ),
    ids=("foreign-schema", "zero-ordinal", "boolean-ordinal"),
)
def test_entry_schema_is_publication_specific_and_ordinal_is_positive_int(
    tmp_path: Path,
    changes: dict[str, object],
) -> None:
    repo = _init_repo(tmp_path)
    _ledger_path(repo).write_bytes(_canonical_line(_entry(**changes)))
    with pytest.raises(L.PublicationLedgerError, match=r"\[entry-schema\]"):
        _read(repo)


def test_entry_key_set_is_exact(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    value = _entry()
    value["unexpected"] = "closed-set violation"
    _ledger_path(repo).write_bytes(_canonical_line(value))
    with pytest.raises(L.PublicationLedgerError, match=r"\[entry-schema\].*unknown"):
        _read(repo)


def test_unchanged_ledger_bytes_across_merge_history_are_accepted(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    root_commit = _git(repo, "rev-parse", "HEAD")
    main_branch = _git(repo, "branch", "--show-current")

    path = _ledger_path(repo)
    path.write_bytes(b"")
    _git(repo, "add", LEDGER_RELATIVE_PATH.as_posix())
    _git(repo, "commit", "-q", "-m", "add empty publication ledger")
    ledger_commit = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "-q", "-b", "without-ledger", root_commit)
    side = repo / "side.txt"
    side.write_text("side\n", encoding="utf-8")
    _git(repo, "add", side.name)
    _git(repo, "commit", "-q", "-m", "commit without publication ledger")

    _git(repo, "checkout", "-q", main_branch)
    _git(repo, "merge", "--no-ff", "-q", "without-ledger", "-m", "merge side")
    merge_commit = _git(repo, "rev-parse", "HEAD")
    history = _git(
        repo,
        "log",
        "--format=%H",
        "--reverse",
        "--full-history",
        "HEAD",
        "--",
        LEDGER_RELATIVE_PATH.as_posix(),
    ).splitlines()

    assert history == [ledger_commit, merge_commit]
    assert [
        _git(
            repo,
            "cat-file",
            "blob",
            f"{commit}:{LEDGER_RELATIVE_PATH.as_posix()}",
        )
        for commit in history
    ] == ["", ""]
    assert _read(repo).entries == ()


@pytest.mark.parametrize(
    "replacement",
    (b"", _canonical_line(_entry(ordinal=2))),
    ids=("truncate", "rewrite"),
)
def test_committed_non_prefix_ledger_history_is_rejected(
    tmp_path: Path,
    replacement: bytes,
) -> None:
    repo = _init_repo(tmp_path)
    path = _ledger_path(repo)
    path.write_bytes(_canonical_line(_entry()))
    _git(repo, "add", LEDGER_RELATIVE_PATH.as_posix())
    _git(repo, "commit", "-q", "-m", "add publication reservation")

    path.write_bytes(replacement)
    _git(repo, "add", LEDGER_RELATIVE_PATH.as_posix())
    _git(repo, "commit", "-q", "-m", "replace publication ledger")

    with pytest.raises(
        L.PublicationLedgerError,
        match=r"\[ledger-history\].*prefix extension",
    ):
        _read(repo)


def test_committed_delete_and_recreate_is_rejected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    path = _ledger_path(repo)
    path.write_bytes(b"")
    _git(repo, "add", LEDGER_RELATIVE_PATH.as_posix())
    _git(repo, "commit", "-q", "-m", "add empty publication ledger")

    path.unlink()
    _git(repo, "add", "-A", LEDGER_RELATIVE_PATH.as_posix())
    _git(repo, "commit", "-q", "-m", "delete publication ledger")

    path.write_bytes(b"")
    _git(repo, "add", LEDGER_RELATIVE_PATH.as_posix())
    _git(repo, "commit", "-q", "-m", "recreate publication ledger")

    with pytest.raises(
        L.PublicationLedgerError,
        match=r"\[ledger-history\].*deleted in committed history",
    ):
        _read(repo)


def _run() -> int:
    """Keep this new test file covered by the repository plain-runner contract."""

    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
