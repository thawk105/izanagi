from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign import s8c_arm_inputs as A


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _committed_artifacts(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0
    assert _git(repo, "config", "user.email", "fixture@example.invalid").returncode == 0
    assert _git(repo, "config", "user.name", "Fixture").returncode == 0
    A.generate_off_neutral_artifacts(repository_root=repo)
    assert _git(repo, "add", "--", "output").returncode == 0
    committed = _git(repo, "commit", "-q", "-m", "arm inputs")
    assert committed.returncode == 0, committed.stderr
    head = _git(repo, "rev-parse", "HEAD")
    assert head.returncode == 0
    return repo, head.stdout.strip()


def _recommit(repo: Path) -> str:
    assert _git(repo, "add", "-A", "--", "output").returncode == 0
    committed = _git(repo, "commit", "-q", "-m", "tamper")
    assert committed.returncode == 0, committed.stderr
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_off_descriptor_bytes_and_digest_are_the_adjudicated_literal() -> None:
    descriptor = A.derive_off_neutral_descriptor()
    raw = A.canonical_execution_input_bytes(descriptor)
    assert len(raw) == 281
    assert not raw.endswith(b"\n")
    assert hashlib.sha256(raw).hexdigest() == (
        "8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89"
    )
    assert descriptor["source"] == "campaign_search_config_projection"
    assert descriptor["read_write"]["read_ratio_percent"] == 50


def test_neutral_derivation_fails_if_positive_control_authority_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(A.s8b_holdout_freeze, "_POSITIVE_RATIO", "51")
    with pytest.raises(A.ArmInputError, match="positive-control ratio"):
        A.derive_off_neutral_descriptor()


def test_generator_is_create_or_exact_verify_and_never_rewrites(tmp_path: Path) -> None:
    A.generate_off_neutral_artifacts(repository_root=tmp_path)
    descriptor = tmp_path / A.OFF_DESCRIPTOR_RELATIVE_PATH
    original = descriptor.read_bytes()
    A.generate_off_neutral_artifacts(repository_root=tmp_path)
    descriptor.write_bytes(original + b"\n")
    with pytest.raises(A.ArmInputError, match="existing artifact differs"):
        A.generate_off_neutral_artifacts(repository_root=tmp_path)
    assert descriptor.read_bytes() == original + b"\n"


def test_generator_rejects_symlinked_artifact_parent(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, tmp_path / "output")
    with pytest.raises(A.ArmInputError, match="artifact parent is not a directory"):
        A.generate_off_neutral_artifacts(repository_root=tmp_path)
    assert list(outside.iterdir()) == []


def test_verify_and_resolve_all_arms_with_two_layer_digests(tmp_path: Path) -> None:
    repo, commit = _committed_artifacts(tmp_path)
    verified = A.verify_off_neutral_artifacts(
        repository_root=repo, commit=commit,
    )
    assert verified.content_digest_sha256 == (
        "8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89"
    )
    resolved = {
        arm: A.resolve_arm_input(
            arm=arm, holdout="H1", repository_root=repo, commit=commit,
        )
        for arm in A.ARMS
    }
    assert len({item.content_digest_sha256 for item in resolved.values()}) == 3
    assert resolved["on"].selected_holdout == "rr80"
    assert resolved["off"].selected_holdout is None
    assert resolved["swapped"].selected_holdout == "rr20"
    for arm, item in resolved.items():
        expected = hashlib.sha256(
            b"izanagi-s8c-arm-binding/v1\0"
            + b"H1"
            + arm.encode("ascii")
            + item.content_digest_sha256.encode("ascii")
        ).hexdigest()
        assert item.arm_binding_digest_sha256 == expected
        assert A.assert_issued_resolved_arm_input(item) is item


def test_cross_holdout_derangement_may_share_content_digest(tmp_path: Path) -> None:
    repo, commit = _committed_artifacts(tmp_path)
    h1_on = A.resolve_arm_input(
        arm="on", holdout="H1", repository_root=repo, commit=commit,
    )
    h2_swapped = A.resolve_arm_input(
        arm="swapped", holdout="H2", repository_root=repo, commit=commit,
    )
    assert h1_on.content_digest_sha256 == h2_swapped.content_digest_sha256
    assert h1_on.arm_binding_digest_sha256 != h2_swapped.arm_binding_digest_sha256


def test_pairwise_collision_rejects_instead_of_falling_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _committed_artifacts(tmp_path)
    neutral = A.derive_off_neutral_descriptor()
    monkeypatch.setattr(
        A.s8b_descriptor, "descriptor_for_holdout", lambda _entry: neutral,
    )
    with pytest.raises(A.ArmInputError, match="pairwise distinct"):
        A.resolve_arm_input(
            arm="on", holdout="H1", repository_root=repo, commit=commit,
        )


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":"8b-v1","schema_version":"8b-v1"}',
        b"\xef\xbb\xbf{}",
        b'{"value":NaN}',
        b"{}\n",
        b" {}",
        b'{"unknown":1}',
        b"\xff",
    ],
    ids=["duplicate", "bom", "nonfinite", "trailing-lf", "whitespace", "unknown", "utf8"],
)
def test_verifier_rejects_noncanonical_or_unknown_descriptor_bytes(
    tmp_path: Path, raw: bytes,
) -> None:
    repo, _commit = _committed_artifacts(tmp_path)
    (repo / A.OFF_DESCRIPTOR_RELATIVE_PATH).write_bytes(raw)
    changed = _recommit(repo)
    with pytest.raises(A.ArmInputError, match=r"\[arm-input-artifact\]"):
        A.verify_off_neutral_artifacts(repository_root=repo, commit=changed)


def test_verifier_rejects_committed_symlink(tmp_path: Path) -> None:
    repo, _commit = _committed_artifacts(tmp_path)
    descriptor = repo / A.OFF_DESCRIPTOR_RELATIVE_PATH
    descriptor.unlink()
    os.symlink("freeze.v1.json", descriptor)
    changed = _recommit(repo)
    with pytest.raises(A.ArmInputError, match="not a regular committed file"):
        A.verify_off_neutral_artifacts(repository_root=repo, commit=changed)


def test_verifier_rejects_committed_directory_in_place_of_artifact(
    tmp_path: Path,
) -> None:
    repo, _commit = _committed_artifacts(tmp_path)
    freeze = repo / A.OFF_FREEZE_RELATIVE_PATH
    freeze.unlink()
    freeze.mkdir()
    (freeze / "child").write_text("not-an-artifact", encoding="utf-8")
    changed = _recommit(repo)
    with pytest.raises(
        A.ArmInputError,
        match="regular committed file|absent or ambiguous",
    ):
        A.verify_off_neutral_artifacts(repository_root=repo, commit=changed)


def test_leaf_module_does_not_import_runner_or_completeness() -> None:
    source = Path(A.__file__).read_text(encoding="utf-8")
    assert "p3_autonomous_workload_trial" not in source
    assert "autonomous_trial_completeness" not in source


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))
