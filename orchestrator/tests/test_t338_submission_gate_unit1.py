"""T-338 unit 1: private submission-gate foundation tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from orchestrator.submission_gate import _binding, _event_chain, _git, _manifest
from orchestrator.preregistration.blobref import BlobRef


_GIT = "/usr/bin/git"


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "T-338 test",
            "GIT_AUTHOR_EMAIL": "t338@example.invalid",
            "GIT_COMMITTER_NAME": "T-338 test",
            "GIT_COMMITTER_EMAIL": "t338@example.invalid",
        }
    )
    return env


def _run(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        [_GIT, *arguments],
        cwd=root,
        env=_git_env(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _commit(root: Path, filename: str, content: str, message: str) -> str:
    (root / filename).write_text(content, encoding="utf-8")
    _run(root, "add", filename)
    _run(root, "commit", "-m", message)
    return _run(root, "rev-parse", "HEAD")


@pytest.fixture()
def git_fixture(tmp_path: Path) -> SimpleNamespace:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(
        [_GIT, "init", "-q"], cwd=root, env=_git_env(), check=True
    )
    branch = _run(root, "branch", "--show-current")
    root_commit = _commit(root, "root.txt", "root\n", "root")
    content_bytes = b"approved manifest\n"
    (root / "manifest.txt").write_bytes(content_bytes)
    (root / "other.txt").write_bytes(b"other\n")
    _run(root, "add", "manifest.txt", "other.txt")
    _run(root, "commit", "-m", "content")
    content_commit = _run(root, "rev-parse", "HEAD")

    _run(root, "checkout", "-q", "-b", "unmerged", content_commit)
    unmerged_effective = _commit(
        root, "unmerged.txt", "unmerged\n", "unmerged effective"
    )
    _run(root, "checkout", "-q", branch)
    effective_commit = _commit(
        root, "binding.txt", "effective\n", "effective"
    )

    _run(root, "checkout", "-q", "-b", "side", root_commit)
    side_commit = _commit(root, "side.txt", "side\n", "side")
    _run(root, "checkout", "-q", branch)
    merge_result = subprocess.run(
        [_GIT, "merge", "--no-ff", "-m", "merge side", "side"],
        cwd=root,
        env=_git_env(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    del merge_result
    merge_commit = _run(root, "rev-parse", "HEAD")
    head_commit = _commit(root, "measurement.txt", "head\n", "measurement")
    return SimpleNamespace(
        root=root,
        root_commit=root_commit,
        content_commit=content_commit,
        effective_commit=effective_commit,
        unmerged_effective=unmerged_effective,
        side_commit=side_commit,
        merge_commit=merge_commit,
        head_commit=head_commit,
        content_bytes=content_bytes,
    )


def _ref(path: str, commit: str, data: bytes) -> BlobRef:
    return BlobRef(path, commit, hashlib.sha256(data).hexdigest())


def _record(fixture: SimpleNamespace) -> _manifest.PreregistrationRecord:
    root = fixture.root_commit
    core = _ref("manifest.txt", fixture.content_commit, fixture.content_bytes)
    dummy = _ref("other.txt", fixture.content_commit, b"other\n")
    return _manifest.PreregistrationRecord(
        core=core,
        addendum_a=dummy,
        addendum_b=None,
        fold_commit=root,
        errata=(
            _manifest.ErratumRef(
                erratum_id="t139-core-s15-exactkey-v1",
                path=dummy.path,
                commit=dummy.commit,
                sha256=dummy.sha256,
                approval_fold_commit=root,
            ),
            _manifest.ErratumRef(
                erratum_id="t139-core-s7-stresscheck-v1",
                path=dummy.path,
                commit=dummy.commit,
                sha256=dummy.sha256,
                approval_fold_commit=root,
            ),
        ),
        approval_manifest=dummy,
        receipt_schema=dummy,
        composed_core_sha256=hashlib.sha256(b"composed").hexdigest(),
        prereg_commit=root,
    )


def _binding_for(
    fixture: SimpleNamespace,
    *,
    record: _manifest.PreregistrationRecord | None = None,
    measurement_head: str | None = None,
    effective_commit: str | None = None,
) -> _binding._PreregBinding:
    record = record or _record(fixture)
    return _binding._PreregBinding._issue(
        record=record,
        measurement_head=measurement_head or fixture.head_commit,
        prereg_commit=record.prereg_commit,
        prereg_content_commit=record.core.commit,
        prereg_effective_commit=effective_commit or fixture.effective_commit,
        root_identity=(fixture.root.stat().st_dev, fixture.root.stat().st_ino),
        token=_binding._CAPABILITY_TOKEN,
    )


def test_package_is_private_until_unit6() -> None:
    import orchestrator.submission_gate as package

    assert package.__all__ == ()
    for name in (
        "resolve_effective_preregistration",
        "PreregBinding",
        "submit_pilot",
        "verify_receipt",
        "verify_prereg_receipt",
    ):
        assert not hasattr(package, name)
    assert not hasattr(_binding, "PreregBinding")
    assert hasattr(_binding, "_PreregBinding")


def test_git_ancestor_and_exact_parent_positive(git_fixture: SimpleNamespace) -> None:
    _git.require_ancestor(
        git_fixture.root,
        ancestor=git_fixture.root_commit,
        descendant=git_fixture.head_commit,
    )
    _git.require_exact_parent(
        git_fixture.root,
        content_commit=git_fixture.content_commit,
        effective_commit=git_fixture.effective_commit,
    )


def test_git_ancestor_rejects_non_ancestor(git_fixture: SimpleNamespace) -> None:
    with pytest.raises(_git.GitSupportError):
        _git.require_ancestor(
            git_fixture.root,
            ancestor=git_fixture.side_commit,
            descendant=git_fixture.effective_commit,
        )
    with pytest.raises(_git.GitSupportError):
        _git.require_exact_parent(
            git_fixture.root,
            content_commit=git_fixture.side_commit,
            effective_commit=git_fixture.effective_commit,
        )


def test_exact_parent_rejects_root_and_merge(git_fixture: SimpleNamespace) -> None:
    with pytest.raises(_git.GitSupportError):
        _git.require_exact_parent(
            git_fixture.root,
            content_commit=git_fixture.root_commit,
            effective_commit=git_fixture.root_commit,
        )
    with pytest.raises(_git.GitSupportError):
        _git.require_exact_parent(
            git_fixture.root,
            content_commit=git_fixture.content_commit,
            effective_commit=git_fixture.merge_commit,
        )


@pytest.mark.parametrize(
    "value",
    ["HEAD", "a" * 39, "A" * 40, "a" * 41, "../" + "a" * 40],
)
def test_commit_arguments_are_full_lowercase_hex(
    git_fixture: SimpleNamespace, value: str
) -> None:
    with pytest.raises(_git.GitSupportError):
        _git.require_commit_object(git_fixture.root, value)


def test_fixed_executable_and_environment_are_scrubbed(
    git_fixture: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}

    def fake_run(argv, *, cwd, env, stdout, stderr, check, timeout):
        observed["argv"] = argv
        observed["cwd"] = cwd
        observed["env"] = dict(env)
        observed["timeout"] = timeout
        stdout.write(b"ok\n")
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setenv("PATH", str(git_fixture.root / "not-a-real-path"))
    monkeypatch.setenv("T338_UNTRUSTED_GIT_ENV", "must-not-cross")
    monkeypatch.setattr(_git.subprocess, "run", fake_run)
    result = _git._git(git_fixture.root, ["version"])

    assert result.stdout == b"ok\n"
    assert observed["argv"][0] == os.fspath(_git._GIT_EXECUTABLE)
    env = observed["env"]
    assert "PATH" not in env
    assert "T338_UNTRUSTED_GIT_ENV" not in env
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_NO_REPLACE_OBJECTS"] == "1"


def test_git_rejects_stderr_over_output_limit(
    git_fixture: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    def noisy_run(argv, *, cwd, env, stdout, stderr, check, timeout):
        stderr.write(b"e" * 17)
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setattr(_git.subprocess, "run", noisy_run)
    with pytest.raises(_git.GitSupportError, match="stderr"):
        _git._git(git_fixture.root, ["version"], max_output_bytes=16)


def test_safe_history_rejects_alternates_promisor_shallow_graft_and_replace(
    git_fixture: SimpleNamespace,
) -> None:
    root = git_fixture.root
    git_dir = Path(_run(root, "rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    objects = git_dir / "objects"

    marker = objects / "info" / "alternates"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("/outside\n", encoding="utf-8")
    with pytest.raises(_git.GitSupportError):
        _git.require_safe_history(root)
    marker.unlink()

    marker = objects / "pack" / "pack-test.promisor"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_bytes(b"")
    with pytest.raises(_git.GitSupportError):
        _git.require_safe_history(root)
    marker.unlink()

    shallow = git_dir / "shallow"
    shallow.write_text(git_fixture.root_commit + "\n", encoding="ascii")
    with pytest.raises(_git.GitSupportError):
        _git.require_safe_history(root)
    shallow.unlink()

    grafts = git_dir / "info" / "grafts"
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text("", encoding="ascii")
    with pytest.raises(_git.GitSupportError):
        _git.require_safe_history(root)
    grafts.unlink()

    replacement = git_dir / "refs" / "replace" / git_fixture.content_commit
    replacement.parent.mkdir(parents=True, exist_ok=True)
    _run(root, "update-ref", f"refs/replace/{git_fixture.content_commit}", git_fixture.root_commit)
    try:
        with pytest.raises(_git.GitSupportError):
            _git.require_safe_history(root)
    finally:
        _run(root, "update-ref", "-d", f"refs/replace/{git_fixture.content_commit}")
        if replacement.exists():
            replacement.unlink()


def test_safe_history_rejects_symlinked_objects_pack(
    git_fixture: SimpleNamespace, tmp_path: Path
) -> None:
    git_dir = Path(_run(git_fixture.root, "rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = git_fixture.root / git_dir
    pack_path = git_dir / "objects" / "pack"
    real_pack = git_dir / "objects" / "pack-real"
    outside = tmp_path / "external-pack"
    outside.mkdir()
    pack_path.mkdir(parents=True, exist_ok=True)
    pack_path.rename(real_pack)
    pack_path.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(_git.GitSupportError):
            _git.require_safe_history(git_fixture.root)
    finally:
        pack_path.unlink()
        real_pack.rename(pack_path)


def test_read_commit_blob_checks_tree_and_digest(git_fixture: SimpleNamespace) -> None:
    digest = hashlib.sha256(git_fixture.content_bytes).hexdigest()
    assert _git.read_commit_blob(
        git_fixture.root,
        commit=git_fixture.content_commit,
        path="manifest.txt",
        expected_sha256=digest,
    ) == git_fixture.content_bytes
    with pytest.raises(_git.GitSupportError):
        _git.read_commit_blob(
            git_fixture.root,
            commit=git_fixture.content_commit,
            path="missing.txt",
            expected_sha256=digest,
        )
    with pytest.raises(_git.GitSupportError):
        _git.read_commit_blob(
            git_fixture.root,
            commit=git_fixture.content_commit,
            path="../manifest.txt",
            expected_sha256=digest,
        )


def test_manifest_views_are_immutable_and_match_approval(
    git_fixture: SimpleNamespace,
) -> None:
    anchor = git_fixture.root_commit
    approval_ref = _ref("approval.txt", anchor, b"approval")
    core = _ref("manifest.txt", git_fixture.content_commit, git_fixture.content_bytes)
    addendum = _ref("addendum.txt", git_fixture.content_commit, b"addendum")
    erratum = _ref("erratum.txt", git_fixture.content_commit, b"erratum")
    erratum_two = _ref("erratum-two.txt", git_fixture.content_commit, b"erratum-two")
    schema = _ref("schema.json", git_fixture.content_commit, b"schema")
    derivation = _ref("derivation.txt", git_fixture.content_commit, b"derivation")
    record_items = _ref("record-items.txt", git_fixture.content_commit, b"record-items")
    approved = _manifest.ApprovedManifest(
        token=_manifest._MANIFEST_CAPABILITY_TOKEN,
        approval_ref=approval_ref,
        target_core=_ref("manifest.txt", anchor, git_fixture.content_bytes),
        approved_blobs={
            "addendum_a": addendum,
            "derivation_map": derivation,
            "erratum_t139_core_s15_exactkey_v1": erratum,
            "erratum_t139_core_s7_stresscheck_v1": erratum_two,
            "record_items": record_items,
            "receipt_schema": schema,
        },
        erratum_application_order=(
            "t139-core-s15-exactkey-v1",
            "t139-core-s7-stresscheck-v1",
        ),
        composed_sha256=hashlib.sha256(b"composed").hexdigest(),
        prereg_commit=anchor,
    )
    record = _manifest.PreregistrationRecord(
        core=core,
        addendum_a=addendum,
        addendum_b=None,
        fold_commit=anchor,
        errata=(
            _manifest.ErratumRef(
                erratum_id="t139-core-s15-exactkey-v1",
                path=erratum.path,
                commit=erratum.commit,
                sha256=erratum.sha256,
                approval_fold_commit=anchor,
            ),
            _manifest.ErratumRef(
                erratum_id="t139-core-s7-stresscheck-v1",
                path=erratum_two.path,
                commit=erratum_two.commit,
                sha256=erratum_two.sha256,
                approval_fold_commit=anchor,
            ),
        ),
        approval_manifest=approval_ref,
        receipt_schema=schema,
        composed_core_sha256=approved.composed_sha256,
        prereg_commit=anchor,
    )
    _manifest._require_manifest_matches_approval(record, approved)
    with pytest.raises(TypeError):
        approved.approved_blobs["new"] = core  # type: ignore[index]
    with pytest.raises(_manifest.ManifestError):
        _manifest._require_manifest_matches_approval(
            replace(record, prereg_commit=git_fixture.content_commit), approved
        )

    with pytest.raises(TypeError):
        _manifest.ApprovedManifest(
            approval_ref=approval_ref,
            target_core=_ref("manifest.txt", anchor, git_fixture.content_bytes),
            approved_blobs={
                "addendum_a": addendum,
                "derivation_map": derivation,
                "erratum_t139_core_s15_exactkey_v1": erratum,
                "erratum_t139_core_s7_stresscheck_v1": erratum_two,
                "record_items": record_items,
                "receipt_schema": schema,
            },
            erratum_application_order=(
                "t139-core-s15-exactkey-v1",
                "t139-core-s7-stresscheck-v1",
            ),
            composed_sha256=hashlib.sha256(b"composed").hexdigest(),
            prereg_commit=anchor,
        )


def test_binding_assert_intact_reads_addendum_blobs(
    git_fixture: SimpleNamespace,
) -> None:
    addendum_b = _ref("root.txt", git_fixture.content_commit, b"root\n")
    record = replace(_record(git_fixture), addendum_b=addendum_b)
    _binding_for(git_fixture, record=record).assert_intact(git_fixture.root)

    missing = replace(
        _record(git_fixture),
        addendum_a=_ref("missing.txt", git_fixture.content_commit, b"missing"),
    )
    with pytest.raises(_git.GitSupportError):
        _binding_for(git_fixture, record=missing).assert_intact(git_fixture.root)

    wrong_digest = replace(
        _record(git_fixture),
        addendum_a=_ref("other.txt", git_fixture.content_commit, b"wrong"),
    )
    with pytest.raises(_git.GitSupportError):
        _binding_for(git_fixture, record=wrong_digest).assert_intact(git_fixture.root)

    bad_b = replace(
        _record(git_fixture),
        addendum_b=_ref("missing-b.txt", git_fixture.content_commit, b"missing-b"),
    )
    with pytest.raises(_git.GitSupportError):
        _binding_for(git_fixture, record=bad_b).assert_intact(git_fixture.root)


def test_binding_assert_intact_checks_all_five_relations(
    git_fixture: SimpleNamespace,
) -> None:
    binding = _binding_for(git_fixture)
    binding.assert_intact(git_fixture.root)

    bad_anchor_record = replace(_record(git_fixture), prereg_commit=git_fixture.side_commit)
    with pytest.raises(_git.GitSupportError):
        _binding_for(git_fixture, record=bad_anchor_record).assert_intact(git_fixture.root)

    bad_digest = replace(
        _record(git_fixture),
        core=_ref("manifest.txt", git_fixture.content_commit, b"wrong"),
    )
    with pytest.raises(_git.GitSupportError):
        _binding_for(git_fixture, record=bad_digest).assert_intact(git_fixture.root)

    with pytest.raises(_git.GitSupportError):
        _binding_for(git_fixture, effective_commit=git_fixture.merge_commit).assert_intact(
            git_fixture.root
        )

    with pytest.raises(_git.GitSupportError):
        _binding_for(
            git_fixture, effective_commit=git_fixture.unmerged_effective
        ).assert_intact(git_fixture.root)

    with pytest.raises(_git.GitSupportError):
        _binding_for(
            git_fixture, measurement_head=git_fixture.effective_commit
        ).assert_intact(git_fixture.root)


def test_hash_chain_replays_and_rejects_gaps_previous_hash_and_duplicates() -> None:
    persisted: list[tuple[str, bytes]] = []

    def create_only(name: str, value: bytes) -> None:
        persisted.append((name, value))

    first = dict(
        _event_chain.append_event(
            [], event_type="created", payload={"value": 1}, create_only=create_only
        )
    )
    second = dict(
        _event_chain.append_event(
            [first], event_type="updated", payload={"value": 2}, create_only=create_only
        )
    )
    replayed = _event_chain.replay_event_chain([first, second])
    assert [event.event_index for event in replayed] == [0, 1]
    assert [name for name, _ in persisted] == ["0000.json", "0001.json"]

    with pytest.raises(_event_chain.EventChainError):
        _event_chain.replay_event_chain([second])
    wrong_previous = dict(second)
    wrong_previous["previous_event_sha256"] = "0" * 64
    with pytest.raises(_event_chain.EventChainError):
        _event_chain.replay_event_chain([first, wrong_previous])
    with pytest.raises(_event_chain.EventChainError):
        _event_chain.replay_event_chain([first, first])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
