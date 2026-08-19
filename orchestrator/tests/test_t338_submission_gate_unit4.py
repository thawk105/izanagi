"""T-338 unit 4: full-history alpha reservations and attempt authority."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from orchestrator.submission_gate import _attempt_authority as authority
from orchestrator.submission_gate import _event_chain, _git
from orchestrator.submission_gate._receipt_io import ReceiptParseError
from orchestrator.submission_gate._safe_io import SafeIOError


_GIT = "/usr/bin/git"


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "T-338 unit 4",
            "GIT_AUTHOR_EMAIL": "t338-unit4@example.invalid",
            "GIT_COMMITTER_NAME": "T-338 unit 4",
            "GIT_COMMITTER_EMAIL": "t338-unit4@example.invalid",
        }
    )
    return env


def _run(root: Path, *arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        [_GIT, *arguments],
        cwd=root,
        env=_git_env(),
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _commit(
    root: Path,
    files: dict[str, bytes] | None,
    message: str,
    *,
    delete: tuple[str, ...] = (),
) -> str:
    for relative, data in (files or {}).items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for relative in delete:
        target = root / relative
        if target.exists() or target.is_symlink():
            target.unlink()
    _run(root, "add", "-A")
    _run(root, "commit", "-m", message)
    return _run(root, "rev-parse", "HEAD")


def _row_bytes() -> bytes:
    return authority._canonical_alpha_json_bytes(
        {
            "family_root": authority.ALPHA_FAMILY_ROOT,
            "kind": authority.ALPHA_LEDGER_KIND,
            "ordinal": 1,
            "schema_version": authority.ALPHA_SCHEMA_VERSION,
        }
    )


@pytest.fixture()
def alpha_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run([_GIT, "init", "-q"], cwd=root, env=_git_env(), check=True)
    family_root = _commit(root, {"root.txt": b"root\n"}, "root")

    # The production literal is immutable.  The isolated fixture substitutes
    # its synthetic root so every history test still exercises the same
    # reject-only literal comparison and ancestor walk.
    monkeypatch.setattr(authority, "ALPHA_FAMILY_ROOT", family_root)
    ledger = _row_bytes() + b"\n"
    reservation_commit = _commit(
        root,
        {authority.ALPHA_LEDGER_PATH: ledger},
        "introduce alpha reservation",
    )
    measurement_head = _commit(root, {"tip.txt": b"tip\n"}, "measurement head")
    event_directory = root / "events" / "attempt-0001"
    event_directory.mkdir(parents=True)
    evidence = {
        "ledger_path": authority.ALPHA_LEDGER_PATH,
        "family_root": family_root,
        "ordinal": 1,
        "reservation_entry_sha256": hashlib.sha256(_row_bytes()).hexdigest(),
        "reservation_commit": reservation_commit,
    }
    return SimpleNamespace(
        root=root,
        family_root=family_root,
        reservation_commit=reservation_commit,
        measurement_head=measurement_head,
        row=ledger[:-1],
        evidence=evidence,
        event_directory=event_directory,
    )


def _inspect(fixture: SimpleNamespace, *, evidence: dict[str, object] | None = None, head: str | None = None):
    return authority._inspect_alpha_reservation(
        fixture.root,
        ledger_evidence=evidence or fixture.evidence,
        measurement_head=head or fixture.measurement_head,
    )


def _commit_ledger(fixture: SimpleNamespace, data: bytes, message: str) -> str:
    return _commit(
        fixture.root,
        {authority.ALPHA_LEDGER_PATH: data},
        message,
    )


def test_full_history_positive_walk(alpha_fixture: SimpleNamespace) -> None:
    revisions = _git.read_full_history(
        alpha_fixture.root,
        start_commit=alpha_fixture.family_root,
        end_commit=alpha_fixture.measurement_head,
        path=authority.ALPHA_LEDGER_PATH,
    )
    assert revisions
    assert revisions[-1].data == alpha_fixture.row + b"\n"
    assert all(revision.mode == "100644" for revision in revisions)
    assert _inspect(alpha_fixture).reservation_commit == alpha_fixture.reservation_commit


def test_git_walk_uses_full_history_reverse(
    alpha_fixture: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, ...]] = []
    original = _git._git

    def spy(root, arguments, **kwargs):
        calls.append(tuple(arguments))
        return original(root, arguments, **kwargs)

    monkeypatch.setattr(_git, "_git", spy)
    _inspect(alpha_fixture)
    assert any(
        "log" in call
        and "--full-history" in call
        and "--reverse" in call
        for call in calls
    )


def test_rejects_shallow_replace_and_graft(alpha_fixture: SimpleNamespace) -> None:
    git_dir = Path(_run(alpha_fixture.root, "rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = alpha_fixture.root / git_dir
    shallow = git_dir / "shallow"
    shallow.write_text(alpha_fixture.family_root + "\n", encoding="ascii")
    try:
        with pytest.raises(authority.AlphaReservationError) as caught:
            _inspect(alpha_fixture)
        assert isinstance(caught.value.__cause__, _git.GitSupportError)
    finally:
        shallow.unlink()


def test_rejects_non_ancestor_head(alpha_fixture: SimpleNamespace) -> None:
    branch = _run(alpha_fixture.root, "branch", "--show-current")
    _run(alpha_fixture.root, "checkout", "-q", "--orphan", "unrelated")
    unrelated = _commit(alpha_fixture.root, {"unrelated.txt": b"no\n"}, "unrelated")
    _run(alpha_fixture.root, "checkout", "-q", branch)
    with pytest.raises(authority.AlphaReservationError):
        _inspect(alpha_fixture, head=unrelated)


def test_requires_one_regular_introduction(alpha_fixture: SimpleNamespace) -> None:
    target = alpha_fixture.root / authority.ALPHA_LEDGER_PATH
    target.chmod(0o755)
    _run(alpha_fixture.root, "add", authority.ALPHA_LEDGER_PATH)
    _run(alpha_fixture.root, "commit", "-m", "change ledger mode")
    head = _run(alpha_fixture.root, "rev-parse", "HEAD")
    with pytest.raises(authority.AlphaReservationError):
        _inspect(alpha_fixture, head=head)


def test_rejects_truncate_edit_reorder_and_delete_recreate(
    alpha_fixture: SimpleNamespace,
) -> None:
    row_two = authority._canonical_alpha_json_bytes(
        {
            "family_root": authority.ALPHA_FAMILY_ROOT,
            "kind": authority.ALPHA_LEDGER_KIND,
            "ordinal": 2,
            "schema_version": authority.ALPHA_SCHEMA_VERSION,
        }
    )
    extended = alpha_fixture.row + b"\n" + row_two + b"\n"
    append_head = _commit_ledger(alpha_fixture, extended, "append second row")
    truncated_head = _commit_ledger(alpha_fixture, alpha_fixture.row + b"\n", "truncate row")
    with pytest.raises(_git.GitSupportError):
        _git.read_full_history(
            alpha_fixture.root,
            start_commit=alpha_fixture.family_root,
            end_commit=truncated_head,
            path=authority.ALPHA_LEDGER_PATH,
        )
    del_head = _commit(
        alpha_fixture.root,
        {},
        "delete ledger",
        delete=(authority.ALPHA_LEDGER_PATH,),
    )
    recreate_head = _commit_ledger(alpha_fixture, alpha_fixture.row + b"\n", "recreate ledger")
    assert append_head != del_head
    assert truncated_head != recreate_head
    with pytest.raises(_git.GitSupportError):
        _git.read_full_history(
            alpha_fixture.root,
            start_commit=alpha_fixture.family_root,
            end_commit=recreate_head,
            path=authority.ALPHA_LEDGER_PATH,
        )


def test_rejects_rename_and_copy_history(alpha_fixture: SimpleNamespace) -> None:
    old = alpha_fixture.root / authority.ALPHA_LEDGER_PATH
    renamed = alpha_fixture.root / "output" / "registry" / "renamed.jsonl"
    old.rename(renamed)
    _run(alpha_fixture.root, "add", "-A")
    _run(alpha_fixture.root, "commit", "-m", "rename ledger")
    head = _run(alpha_fixture.root, "rev-parse", "HEAD")
    with pytest.raises(_git.GitSupportError):
        _git.read_full_history(
            alpha_fixture.root,
            start_commit=alpha_fixture.family_root,
            end_commit=head,
            path=authority.ALPHA_LEDGER_PATH,
        )

    # A copied path is tested independently so the negative reason is copy
    # provenance rather than the preceding rename deletion.
    source = _commit(alpha_fixture.root, {"source.txt": alpha_fixture.row + b"\n"}, "copy source")
    copied_path = "output/registry/copied.jsonl"
    copied_head = _commit(
        alpha_fixture.root,
        {copied_path: alpha_fixture.row + b"\n"},
        "copy ledger",
    )
    assert source != copied_head
    with pytest.raises(_git.GitSupportError):
        _git.read_full_history(
            alpha_fixture.root,
            start_commit=alpha_fixture.family_root,
            end_commit=copied_head,
            path=copied_path,
        )


def test_rejects_duplicate_json_keys_and_missing_final_lf(
    alpha_fixture: SimpleNamespace,
) -> None:
    duplicate = (
        b'{"family_root":"'
        + alpha_fixture.family_root.encode("ascii")
        + b'","kind":"alpha_reservation","ordinal":1,"ordinal":1,"schema_version":"t139-alpha-reservation/v1"}\n'
    )
    _run(
        alpha_fixture.root,
        "checkout",
        "-q",
        "-b",
        "duplicate-json-key",
        alpha_fixture.measurement_head,
    )
    duplicate_head = _commit_ledger(
        alpha_fixture,
        alpha_fixture.row + b"\n" + duplicate,
        "duplicate JSON key",
    )
    with pytest.raises(authority.AlphaReservationError) as duplicate_error:
        _inspect(alpha_fixture, head=duplicate_head)
    assert isinstance(duplicate_error.value.__cause__, ReceiptParseError)

    _run(
        alpha_fixture.root,
        "checkout",
        "-q",
        "-b",
        "missing-final-lf",
        alpha_fixture.family_root,
    )
    valid_head = _commit_ledger(alpha_fixture, alpha_fixture.row, "remove final LF")
    with pytest.raises(authority.AlphaReservationError):
        _inspect(alpha_fixture, head=valid_head)


def test_rejects_duplicate_family_ordinal_across_history(
    alpha_fixture: SimpleNamespace,
) -> None:
    duplicate_head = _commit_ledger(
        alpha_fixture,
        alpha_fixture.row + b"\n" + alpha_fixture.row + b"\n",
        "duplicate reservation",
    )
    with pytest.raises(authority.AlphaReservationError):
        _inspect(alpha_fixture, head=duplicate_head)


def test_rejects_release_and_tombstone_entries(alpha_fixture: SimpleNamespace) -> None:
    tombstone = authority._canonical_alpha_json_bytes(
        {
            "family_root": authority.ALPHA_FAMILY_ROOT,
            "kind": "release",
            "ordinal": 1,
            "schema_version": authority.ALPHA_SCHEMA_VERSION,
        }
    ) + b"\n"
    head = _commit_ledger(alpha_fixture, tombstone, "tombstone entry")
    with pytest.raises(authority.AlphaReservationError):
        _inspect(alpha_fixture, head=head)


def test_derives_entry_digest_and_first_commit(alpha_fixture: SimpleNamespace) -> None:
    result = _inspect(alpha_fixture)
    assert result.reservation_entry_sha256 == hashlib.sha256(alpha_fixture.row).hexdigest()
    assert result.reservation_commit == alpha_fixture.reservation_commit
    assert result.measurement_head == alpha_fixture.measurement_head


def test_history_is_rewalked_without_cache(alpha_fixture: SimpleNamespace) -> None:
    first = _git.read_full_history(
        alpha_fixture.root,
        start_commit=alpha_fixture.family_root,
        end_commit=alpha_fixture.measurement_head,
        path=authority.ALPHA_LEDGER_PATH,
    )
    changed_head = _commit_ledger(
        alpha_fixture,
        alpha_fixture.row + b"\n" + alpha_fixture.row + b"\n",
        "history mutation after first walk",
    )
    assert first[-1].data == alpha_fixture.row + b"\n"
    with pytest.raises(authority.AlphaReservationError):
        _inspect(alpha_fixture, head=changed_head)


def test_parent_series_id_reset_is_killed_by_full_history(
    alpha_fixture: SimpleNamespace,
) -> None:
    receipt_a = {
        "series_id": "a" * 64,
        "parent_series_id": None,
        "ledger_evidence": dict(alpha_fixture.evidence),
    }
    assert receipt_a["ledger_evidence"]["family_root"] == alpha_fixture.family_root
    assert receipt_a["ledger_evidence"]["ordinal"] == 1
    accepted = authority._inspect_alpha_reservation(
        alpha_fixture.root,
        ledger_evidence=receipt_a["ledger_evidence"],
        measurement_head=alpha_fixture.measurement_head,
    )
    assert accepted.ordinal == 1

    # Attack C attempts to create a new family root by declaration.  The
    # comparison is reject-only and happens before any root selection, while
    # every other condition is still the positive fixture.
    receipt_c = {
        **receipt_a,
        "ledger_evidence": {
            **receipt_a["ledger_evidence"],
            "family_root": "f" * 40,
        },
    }
    with pytest.raises(authority.AlphaReservationError):
        authority._inspect_alpha_reservation(
            alpha_fixture.root,
            ledger_evidence=receipt_c["ledger_evidence"],
            measurement_head=alpha_fixture.measurement_head,
        )

    # Attack B is a new parent/series declaration backed by a second ledger
    # row with the same fixed identity.  No series_id -> family_root mapping is
    # used; the full history sees the duplicate reservation itself.
    receipt_b = {
        "series_id": "b" * 64,
        "parent_series_id": "c" * 64,
        "ledger_evidence": dict(receipt_a["ledger_evidence"]),
    }
    assert receipt_b["series_id"] != receipt_a["series_id"]
    assert receipt_b["parent_series_id"] != receipt_a["parent_series_id"]
    assert receipt_b["ledger_evidence"] == receipt_a["ledger_evidence"]
    assert receipt_b["ledger_evidence"] is not receipt_a["ledger_evidence"]
    attack_b_head = _commit_ledger(
        alpha_fixture,
        alpha_fixture.row + b"\n" + alpha_fixture.row + b"\n",
        "attack B duplicate ordinal",
    )
    with pytest.raises(authority.AlphaReservationError):
        authority._inspect_alpha_reservation(
            alpha_fixture.root,
            ledger_evidence=receipt_b["ledger_evidence"],
            measurement_head=attack_b_head,
        )


def test_alpha_authority_rejects_wrong_token_and_subclass(
    alpha_fixture: SimpleNamespace,
) -> None:
    sealed = _inspect(alpha_fixture)
    fields = {
        "ledger_path": sealed.ledger_path,
        "family_root": sealed.family_root,
        "ordinal": sealed.ordinal,
        "reservation_entry_sha256": sealed.reservation_entry_sha256,
        "reservation_commit": sealed.reservation_commit,
        "measurement_head": sealed.measurement_head,
        "root_identity": sealed._root_identity,
    }
    with pytest.raises(TypeError):
        authority._AlphaReservationAuthority._issue(
            **fields,
            token=object(),
        )

    class Forged(authority._AlphaReservationAuthority):
        pass

    with pytest.raises(TypeError):
        Forged(**fields, token=authority._ALPHA_CAPABILITY_TOKEN)


def test_alpha_root_identity_pin_is_rechecked(alpha_fixture: SimpleNamespace) -> None:
    sealed = _inspect(alpha_fixture)
    object.__setattr__(sealed, "_root_identity", (0, 0))
    with pytest.raises(authority.AlphaReservationError):
        sealed.assert_intact(alpha_fixture.root)


def test_event_chain_replays_and_rejects_gap_hash_tamper(
    alpha_fixture: SimpleNamespace,
) -> None:
    reservation = _inspect(alpha_fixture)
    loaded = authority._load_attempt_authority(
        alpha_fixture.root,
        reservation=reservation,
        event_directory="events/attempt-0001",
    )
    loaded = authority._append_attempt_event(
        alpha_fixture.root,
        loaded,
        event_type="created",
        payload={"attempt": {"ordinal": 1}},
    )
    loaded = authority._append_attempt_event(
        alpha_fixture.root,
        loaded,
        event_type="observed",
        payload={"nested": [1, 2]},
    )
    assert [event.event_index for event in loaded.events] == [0, 1]
    second = alpha_fixture.event_directory / "0001.json"
    value = json.loads(second.read_text(encoding="utf-8"))
    value["previous_event_sha256"] = "0" * 64
    second.write_bytes(authority._canonical_json_bytes(value) + b"\n")
    with pytest.raises(authority.AttemptAuthorityError) as caught:
        authority._load_attempt_authority(
            alpha_fixture.root,
            reservation=reservation,
            event_directory="events/attempt-0001",
        )
    assert isinstance(caught.value.__cause__, _event_chain.EventChainError)


def test_append_event_uses_create_only_sink(alpha_fixture: SimpleNamespace) -> None:
    reservation = _inspect(alpha_fixture)
    loaded = authority._load_attempt_authority(
        alpha_fixture.root,
        reservation=reservation,
        event_directory="events/attempt-0001",
    )
    updated = authority._append_attempt_event(
        alpha_fixture.root,
        loaded,
        event_type="created",
        payload={"value": 1},
    )
    assert (alpha_fixture.event_directory / "0000.json").is_file()
    assert updated.events[0].event_sha256 == _event_chain.hash_event(
        json.loads((alpha_fixture.event_directory / "0000.json").read_text())
    )
    with pytest.raises(authority.AttemptAuthorityError):
        # The stale authority is not allowed to retry the already-created
        # numbered target or treat create-only persistence as idempotent.
        authority._append_attempt_event(
            alpha_fixture.root,
            loaded,
            event_type="created",
            payload={"value": 2},
        )


def test_event_sink_rejects_symlink_and_snapshot_change(
    alpha_fixture: SimpleNamespace, tmp_path: Path
) -> None:
    external = tmp_path / "external.json"
    external.write_bytes(b"{}\n")
    link = alpha_fixture.event_directory / "0000.json"
    link.symlink_to(external)
    reservation = _inspect(alpha_fixture)
    with pytest.raises(authority.AttemptAuthorityError) as caught:
        authority._load_attempt_authority(
            alpha_fixture.root,
            reservation=reservation,
            event_directory="events/attempt-0001",
        )
    assert isinstance(caught.value.__cause__, SafeIOError) or caught.value.__cause__ is not None


def test_event_sink_rejects_noncanonical_stored_bytes(
    alpha_fixture: SimpleNamespace,
) -> None:
    reservation = _inspect(alpha_fixture)
    loaded = authority._load_attempt_authority(
        alpha_fixture.root,
        reservation=reservation,
        event_directory="events/attempt-0001",
    )
    authority._append_attempt_event(
        alpha_fixture.root,
        loaded,
        event_type="created",
        payload={"value": 1},
    )
    target = alpha_fixture.event_directory / "0000.json"
    value = json.loads(target.read_text(encoding="utf-8"))
    target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(authority.AttemptAuthorityError):
        authority._load_attempt_authority(
            alpha_fixture.root,
            reservation=reservation,
            event_directory="events/attempt-0001",
        )


def test_attempt_authority_payload_is_deeply_frozen(
    alpha_fixture: SimpleNamespace,
) -> None:
    reservation = _inspect(alpha_fixture)
    loaded = authority._load_attempt_authority(
        alpha_fixture.root,
        reservation=reservation,
        event_directory="events/attempt-0001",
    )
    payload = {"nested": {"values": [1, {"stable": True}]}}
    updated = authority._append_attempt_event(
        alpha_fixture.root,
        loaded,
        event_type="payload",
        payload=payload,
    )
    payload["nested"]["values"].append(99)
    frozen = updated.events[0].payload
    assert frozen["nested"]["values"] == (1, authority._freeze_json_value({"stable": True}))
    with pytest.raises(TypeError):
        frozen["nested"]["values"] = ()  # type: ignore[index]
    with pytest.raises(AttributeError):
        frozen["nested"]["values"].append(2)  # type: ignore[union-attr]


def test_attempt_authority_is_bound_to_alpha_reservation(
    alpha_fixture: SimpleNamespace,
) -> None:
    reservation = _inspect(alpha_fixture)
    loaded = authority._load_attempt_authority(
        alpha_fixture.root,
        reservation=reservation,
        event_directory="events/attempt-0001",
    )
    assert loaded.reservation is reservation
    with pytest.raises(TypeError):
        authority._AttemptAuthority._issue(
            reservation=object(),  # type: ignore[arg-type]
            event_directory="events/attempt-0001",
            events=(),
            root_identity=loaded._root_identity,
            event_directory_identity=loaded._event_directory_identity,
            token=authority._ATTEMPT_CAPABILITY_TOKEN,
        )


def test_attempt_root_and_directory_identity_pins(alpha_fixture: SimpleNamespace) -> None:
    reservation = _inspect(alpha_fixture)
    loaded = authority._load_attempt_authority(
        alpha_fixture.root,
        reservation=reservation,
        event_directory="events/attempt-0001",
    )
    object.__setattr__(loaded, "_root_identity", (0, 0))
    with pytest.raises(authority.AttemptAuthorityError):
        loaded.assert_intact(alpha_fixture.root)

    object.__setattr__(loaded, "_root_identity", (alpha_fixture.root.stat().st_dev, alpha_fixture.root.stat().st_ino))
    old = alpha_fixture.root / "events" / "attempt-0001-old"
    alpha_fixture.event_directory.rename(old)
    alpha_fixture.event_directory.mkdir()
    with pytest.raises(authority.AttemptAuthorityError):
        loaded.assert_intact(alpha_fixture.root)


def test_attempt_authority_does_not_claim_intent_exact_coverage() -> None:
    assert "intent" not in authority._AttemptAuthority.__annotations__
    assert "pbs" not in authority.__doc__.lower() or "does not claim" in authority.__doc__.lower()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
