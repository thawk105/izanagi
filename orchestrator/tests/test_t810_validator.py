# -*- coding: utf-8 -*-
"""T-810 単一 validator の fail-closed 境界。"""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from orchestrator.campaign.t810_preregistration import (  # noqa: E402
    PREREG_PATH,
    T810NotAuthorizedError,
    VerifiedT810Preregistration,
    request_t810_launch,
)
from orchestrator.campaign.t810_validator import (  # noqa: E402
    MANIFEST_SCHEMA,
    T810ValidationError,
    canonical_benchmark_argv,
    classify_terminal_state,
    consume_current_pass_witness,
    inspect_repository,
    make_t810_durable_root,
    resolve_git_identity,
    scan_tree,
    validate_t810,
    verify_frozen_manifest,
    write_pass_witness_create_only,
)


def _run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        list(args), cwd=cwd, check=True, stdout=subprocess.PIPE, text=True
    ).stdout


def _git_repo(path: Path) -> Path:
    path.mkdir()
    _run("git", "init", "-q", cwd=path)
    _run("git", "config", "user.email", "validator@example.invalid", cwd=path)
    _run("git", "config", "user.name", "validator-test", cwd=path)
    (path / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _run("git", "add", "tracked.txt", cwd=path)
    _run("git", "commit", "-qm", "fixture", cwd=path)
    return path


def _preregistration() -> VerifiedT810Preregistration:
    # loader 自体の authority test ではないため、現行 artifact hash を fixture に複製しない。
    projection = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    return VerifiedT810Preregistration(
        sha256="validator-unit-projection", approval_id="validator-unit", projection=projection
    )


def _manifest(tmp_path: Path) -> tuple[Path, Path, Path, str, str]:
    root = tmp_path / "frozen"
    root.mkdir()
    executable = root / "CCBench-Silo"
    executable.write_bytes(b"fake executable\n")
    executable.chmod(0o755)
    executable_digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    value = {
        "schema_version": MANIFEST_SCHEMA,
        "members": [{
            "path": executable.name,
            "size": executable.stat().st_size,
            "sha256": executable_digest,
        }],
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return manifest, root, executable, hashlib.sha256(manifest.read_bytes()).hexdigest(), executable_digest


def _receipt(prereg: VerifiedT810Preregistration, executable: Path, digest: str, *,
             claimed: str = "valid", missing_slot: bool = False) -> dict:
    count = prereg.projection["design"]["selected"]["node_count"]
    rounds = prereg.projection["design"]["selected"]["round_count"]
    argv = list(canonical_benchmark_argv(prereg, str(executable.resolve())))
    slots = []
    for index in range(count - int(missing_slot)):
        completed = claimed == "valid" or (claimed == "terminal_reduced" and index < count - 1)
        slots.append({
            "slot_id": f"slot-{index:02d}",
            "complete": True,
            "completed": completed,
            "events": ["measurement_start"] if completed else [],
            "executions": [{
                "round_id": round_id,
                "argv": argv,
                "executable_realpath": str(executable.resolve()),
                "executable_sha256": digest,
            } for round_id in range(1, rounds + 1)] if completed else [],
        })
    return {"coordinator": {"complete": True, "events": ["release"]}, "slots": slots}


def _attempt_tree(root: Path, prereg: VerifiedT810Preregistration, *, reduced: bool = False) -> None:
    artifacts = prereg.projection["artifacts"]
    root.mkdir()
    root_files = list(artifacts["root"]["always_files"])
    root_files.append(artifacts["root"]["conditional_estimate_file"])
    for name in root_files:
        (root / name).write_text("fixture\n", encoding="utf-8")
    count = prereg.projection["design"]["selected"]["node_count"]
    for index in range(count):
        slot = root / f"slot-{index:02d}"
        slot.mkdir()
        for name in artifacts["slots"]["always_files"]:
            (slot / name).write_text("fixture\n", encoding="utf-8")
        (slot / artifacts["slots"]["conditional_node_receipt_file"]).write_text(
            "fixture\n", encoding="utf-8"
        )
        if not reduced or index < count - 1:
            (slot / artifacts["slots"]["conditional_measurements_file"]).write_text(
                "fixture\n", encoding="utf-8"
            )


def _mountinfo() -> str:
    return "1 0 0:1 / / rw - tmpfs synthetic rw\n"


def _positive(tmp_path: Path, *, claimed: str = "valid"):
    repo = _git_repo(tmp_path / "repo")
    writable = tmp_path / "writable"
    writable.mkdir()
    prereg = _preregistration()
    manifest, manifest_root, executable, manifest_digest, executable_digest = _manifest(tmp_path)
    attempt = tmp_path / "attempt"
    _attempt_tree(attempt, prereg, reduced=claimed == "terminal_reduced")
    receipt = _receipt(prereg, executable, executable_digest, claimed=claimed)
    result = validate_t810(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=resolve_git_identity(repo.resolve()),
        writable_root=writable.resolve(),
        manifest_path=manifest,
        manifest_root=manifest_root,
        expected_manifest_sha256=manifest_digest,
        executable=executable,
        expected_executable_sha256=executable_digest,
        attempt_root=attempt,
        attempt_receipt=receipt,
        claimed_state=claimed,
        mountinfo_text=_mountinfo(),
    )
    return result, repo, prereg, receipt, executable, executable_digest


def test_m16_quiet_checkout_and_canonical_attempt_pass(tmp_path: Path):
    result, _, prereg, _, _, _ = _positive(tmp_path)
    assert result.ok
    assert result.terminal_state == "valid"
    assert not hasattr(result, "launch")
    assert prereg.run_authorized is False
    assert any("未記録 exec" in item for item in result.limitations)
    assert any("cooperative" in item for item in result.limitations)
    assert any("d2_" in item for item in result.limitations)


def test_pre_and_post_cannot_select_validator_checks_by_mode():
    assert "mode" not in inspect.signature(validate_t810).parameters


def test_dormant_seal_has_no_positive_launch_path():
    prereg = _preregistration()
    with pytest.raises(T810NotAuthorizedError):
        request_t810_launch(prereg)


def test_terminal_reduced_requires_exactly_twelve_complete_slots(tmp_path: Path):
    result, _, prereg, receipt, _, _ = _positive(tmp_path, claimed="terminal_reduced")
    assert result.ok and result.terminal_state == "terminal_reduced"
    receipt["slots"][0]["completed"] = False
    receipt["slots"][0]["events"] = []
    receipt["slots"][0]["executions"] = []
    assert classify_terminal_state(
        receipt, expected_slots=13, claimed_state="terminal_reduced",
        post_validation_passed=True,
    ) == "incomplete_after_start"


def test_m1_m2_scan_walks_ignored_directory_to_nested_file(tmp_path: Path):
    root = tmp_path / "tree"
    (root / "ignored" / "deep").mkdir(parents=True)
    (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    hidden = root / "ignored" / "deep" / "must-be-seen.bin"
    hidden.write_bytes(b"seen")
    paths = {record.path for record in scan_tree(root).records}
    assert "ignored/deep/must-be-seen.bin" in paths


def test_mode_change_is_part_of_repository_snapshot(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    identity = resolve_git_identity(repo.resolve())
    before = inspect_repository(repo.resolve(), identity)
    (repo / "tracked.txt").chmod(0o755)
    after = inspect_repository(repo.resolve(), identity)
    assert before != after


def test_gitlink_records_head_and_dirty_state(tmp_path: Path):
    child = _git_repo(tmp_path / "child")
    parent = _git_repo(tmp_path / "parent")
    _run("git", "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), "dep", cwd=parent)
    _run("git", "commit", "-qam", "submodule", cwd=parent)
    clean = inspect_repository(parent.resolve(), resolve_git_identity(parent.resolve()))
    assert clean.gitlinks and not clean.gitlinks[0].dirty
    (parent / "dep" / "untracked").write_text("dirty\n", encoding="utf-8")
    dirty = inspect_repository(parent.resolve(), resolve_git_identity(parent.resolve()))
    assert dirty.gitlinks[0].dirty


def test_m9_measurement_start_overrides_claimed_pre_release(tmp_path: Path):
    prereg = _preregistration()
    _, _, executable, _, digest = _manifest(tmp_path)
    receipt = _receipt(prereg, executable, digest)
    assert classify_terminal_state(
        receipt, expected_slots=13, claimed_state="pre_release_invalid",
        post_validation_passed=False,
    ) == "incomplete_after_start"


def test_m10_missing_receipt_is_not_event_absence():
    assert classify_terminal_state(
        None, expected_slots=13, claimed_state="pre_release_invalid",
        post_validation_passed=False,
    ) == "incomplete_after_start"


def test_m11_repo_root_must_match_approved_git_identity(tmp_path: Path):
    approved = _git_repo(tmp_path / "approved")
    substituted = _git_repo(tmp_path / "substituted")
    with pytest.raises(T810ValidationError, match="approved identity"):
        inspect_repository(substituted.resolve(), resolve_git_identity(approved.resolve()))


def test_nested_worktree_container_is_rejected(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    (repo / ".claude" / "worktrees").mkdir(parents=True)
    with pytest.raises(T810ValidationError, match="contains .claude/worktrees"):
        inspect_repository(repo.resolve(), resolve_git_identity(repo.resolve()))


def test_m12_empty_manifest_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": MANIFEST_SCHEMA, "members": []}), encoding="utf-8")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises(T810ValidationError, match="non-empty"):
        verify_frozen_manifest(manifest, root, expected_sha256=digest)


def test_manifest_expected_digest_cannot_be_derived_from_file(tmp_path: Path):
    manifest, root, _, _, _ = _manifest(tmp_path)
    with pytest.raises(T810ValidationError, match="expected manifest"):
        verify_frozen_manifest(manifest, root, expected_sha256="")


def test_manifest_rejects_unlisted_nested_file_and_duplicate_member(tmp_path: Path):
    manifest, root, _, digest, _ = _manifest(tmp_path)
    (root / "ignored").mkdir()
    (root / "ignored" / "extra").write_bytes(b"extra")
    with pytest.raises(T810ValidationError, match="unlisted"):
        verify_frozen_manifest(manifest, root, expected_sha256=digest)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["members"].append(dict(value["members"][0]))
    manifest.write_text(json.dumps(value), encoding="utf-8")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises(T810ValidationError, match="duplicate"):
        verify_frozen_manifest(manifest, root, expected_sha256=digest)


def test_m14_activation_inventory_is_independent(tmp_path: Path):
    result, _, _, _, _, _ = _positive(tmp_path)
    assert {code for code, _ in result.baseline.forbidden_regions} == {
        "FORBIDDEN_OUTPUT", "FORBIDDEN_ENV_CONTRACT", "FORBIDDEN_ENV_CONTRACT_ACTIVATIONS"
    }


def test_m14_caller_cannot_omit_activation_inventory(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    writable = tmp_path / "writable"
    writable.mkdir()
    prereg = _preregistration()
    manifest, manifest_root, executable, manifest_digest, executable_digest = _manifest(tmp_path)
    attempt = tmp_path / "attempt"
    _attempt_tree(attempt, prereg)
    with pytest.raises(T810ValidationError, match="exact three"):
        validate_t810(
            preregistration=prereg, repo_root=repo.resolve(),
            approved_git_identity=resolve_git_identity(repo.resolve()), writable_root=writable.resolve(),
            manifest_path=manifest, manifest_root=manifest_root,
            expected_manifest_sha256=manifest_digest, executable=executable,
            expected_executable_sha256=executable_digest, attempt_root=attempt,
            attempt_receipt=_receipt(prereg, executable, executable_digest), claimed_state="valid",
            canonical_forbidden_roots={"FORBIDDEN_OUTPUT": repo / "output"},
            mountinfo_text=_mountinfo(),
        )


def test_calibration_overlap_and_symlink_alias_are_rejected(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    calibration = repo / "output" / "env" / "pegasus" / "calibration"
    calibration.mkdir(parents=True)
    with pytest.raises(T810ValidationError, match="overlap"):
        make_t810_durable_root(repo.parent.resolve(), repo.resolve(), mountinfo_text=_mountinfo())
    # Direct root helper also rejects a repository-external alias to calibration.
    alias = tmp_path / "calibration-alias"
    alias.symlink_to(calibration, target_is_directory=True)
    with pytest.raises(T810ValidationError, match="symlinks"):
        make_t810_durable_root(alias, repo.resolve(), mountinfo_text=_mountinfo())


def test_duplicate_round_id_and_zero_records_are_rejected(tmp_path: Path):
    result, repo, prereg, receipt, executable, digest = _positive(tmp_path)
    del result, repo
    receipt["slots"][0]["executions"][1]["round_id"] = 1
    # The focused helper is exercised through full validation in the positive fixture's shape.
    findings = __import__(
        "orchestrator.campaign.t810_validator", fromlist=["_verify_executable_and_argv"]
    )._verify_executable_and_argv(prereg, executable, digest, receipt["slots"])
    assert "DUPLICATE_OR_INVALID_ROUND_ID" in {finding.code for finding in findings}
    for slot in receipt["slots"]:
        slot["completed"] = False
        slot["executions"] = []
    findings = __import__(
        "orchestrator.campaign.t810_validator", fromlist=["_verify_executable_and_argv"]
    )._verify_executable_and_argv(prereg, executable, digest, receipt["slots"])
    assert "EXECUTION_RECORDS_EMPTY" in {finding.code for finding in findings}


def test_m15_pass_witness_is_create_only_and_current_process_bound(tmp_path: Path):
    result, _, _, _, _, _ = _positive(tmp_path)
    witness = tmp_path / "pass.json"
    created = write_pass_witness_create_only(
        witness, result=result, attempt_nonce="attempt-1", invocation_nonce="invocation-1"
    )
    value = consume_current_pass_witness(
        witness, process_returncode=0, invocation_nonce="invocation-1", created_identity=created
    )
    assert value["baseline_digest"] == result.baseline_digest
    with pytest.raises(T810ValidationError, match="already exists"):
        write_pass_witness_create_only(
            witness, result=result, attempt_nonce="attempt-1", invocation_nonce="invocation-2"
        )
    with pytest.raises(T810ValidationError, match="did not return zero"):
        consume_current_pass_witness(
            witness, process_returncode=2, invocation_nonce="invocation-1", created_identity=created
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
