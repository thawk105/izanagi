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
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    ApprovalReceipt,
    PREREG_PATH,
    T810NotAuthorizedError,
    VerifiedT810Preregistration,
    load_t810_preregistration,
    request_t810_launch,
)
from orchestrator.campaign.t810_validator import (  # noqa: E402
    BaselineEnvelope,
    MANIFEST_SCHEMA,
    T810ValidationError,
    canonical_benchmark_argv,
    classify_terminal_state,
    consume_current_pass_witness,
    git_identity_digest,
    inspect_repository,
    make_t810_durable_root,
    resolve_git_identity,
    scan_tree,
    validate_t810,
    verify_frozen_manifest,
    write_pass_witness_create_only,
)
from tools.pegasus.validate_t810 import main as validator_cli_main  # noqa: E402


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
    digest = hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()
    return load_t810_preregistration(
        PREREG_PATH,
        approval_receipt=ApprovalReceipt(
            artifact_sha256=digest,
            approval_id="validator-unit",
            schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
        ),
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
            "attempt_nonce": "attempt-1",
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
            "measurements_sha256": "0" * 64 if completed else None,
        })
    reached = [slot["slot_id"] for slot in slots]
    return {
        "attempt_nonce": "attempt-1",
        "coordinator_receipt_sha256": "0" * 64,
        "coordinator": {
            "attempt_nonce": "attempt-1",
            "complete": True,
            "estimate_sha256": None,
            "events": ["release"],
            "node_receipt_sha256": {slot_id: "0" * 64 for slot_id in reached},
            "reached_slots": reached,
        },
        "slots": slots,
    }


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _attempt_tree(
    root: Path,
    prereg: VerifiedT810Preregistration,
    executable: Path,
    executable_digest: str,
    *,
    state: str = "valid",
    attempt_nonce: str = "attempt-1",
) -> dict:
    artifacts = prereg.projection["artifacts"]
    root.mkdir()
    count = prereg.projection["design"]["selected"]["node_count"]
    rounds = prereg.projection["design"]["selected"]["round_count"]
    all_ids = [f"slot-{index:02d}" for index in range(count)]
    if state == "pre_release_invalid":
        reached = all_ids[:3]
    else:
        reached = all_ids
    if state == "valid":
        started = completed = set(all_ids)
    elif state == "terminal_reduced":
        started = completed = set(all_ids[:-1])
    elif state == "incomplete_after_start":
        started, completed = {all_ids[0]}, set()
    else:
        started = completed = set()
    release = state != "pre_release_invalid"
    argv = list(canonical_benchmark_argv(prereg, str(executable.resolve())))
    slots: list[dict] = []
    node_hashes: dict[str, str] = {}
    measurement_hashes: dict[str, str] = {}
    for slot_id in reached:
        slot = root / slot_id
        slot.mkdir()
        for name in artifacts["slots"]["always_files"]:
            (slot / name).write_text("fixture\n", encoding="utf-8")
        measurement_digest = None
        if slot_id in started:
            measurement_count = rounds if slot_id in completed else 1
            measurement_raw = b"".join(
                _json_bytes({"round_id": round_id, "throughput": 1000 + round_id})
                for round_id in range(1, measurement_count + 1)
            )
            (slot / artifacts["slots"]["conditional_measurements_file"]).write_bytes(
                measurement_raw
            )
            measurement_digest = hashlib.sha256(measurement_raw).hexdigest()
            measurement_hashes[slot_id] = measurement_digest
        is_completed = slot_id in completed
        value = {
            "attempt_nonce": attempt_nonce,
            "complete": True,
            "completed": is_completed,
            "events": ["measurement_start"] if slot_id in started else [],
            "executions": [{
                "argv": argv,
                "executable_realpath": str(executable.resolve()),
                "executable_sha256": executable_digest,
                "round_id": round_id,
            } for round_id in range(1, rounds + 1)] if is_completed else [],
            "measurements_sha256": measurement_digest,
            "slot_id": slot_id,
        }
        raw = _json_bytes(value)
        (slot / artifacts["slots"]["conditional_node_receipt_file"]).write_bytes(raw)
        node_hashes[slot_id] = hashlib.sha256(raw).hexdigest()
        slots.append(value)

    estimate_sha256 = None
    if state in {"valid", "terminal_reduced"}:
        estimate_raw = _json_bytes({
            "attempt_nonce": attempt_nonce,
            "input_measurements_sha256": measurement_hashes,
            "tau_hat": "0.001",
        })
        (root / artifacts["root"]["conditional_estimate_file"]).write_bytes(estimate_raw)
        estimate_sha256 = hashlib.sha256(estimate_raw).hexdigest()
    coordinator = {
        "attempt_nonce": attempt_nonce,
        "complete": True,
        "estimate_sha256": estimate_sha256,
        "events": ["release"] if release else [],
        "node_receipt_sha256": node_hashes,
        "reached_slots": reached,
    }
    coordinator_raw = _json_bytes(coordinator)
    for name in artifacts["root"]["always_files"]:
        if name == "coordinator-receipt.jsonl":
            (root / name).write_bytes(coordinator_raw)
        else:
            (root / name).write_text("fixture\n", encoding="utf-8")
    return {
        "attempt_nonce": attempt_nonce,
        "coordinator_receipt_sha256": hashlib.sha256(coordinator_raw).hexdigest(),
        "coordinator": coordinator,
        "slots": slots,
    }


def _mountinfo() -> str:
    return "1 0 0:1 / / rw - tmpfs synthetic rw\n"


def _positive(
    tmp_path: Path,
    *,
    claimed: str = "valid",
    env_alias: bool = False,
    output_alias: bool = False,
    mountinfo_text: str | None = None,
):
    repo = _git_repo(tmp_path / "repo")
    writable = tmp_path / "writable"
    writable.mkdir()
    if output_alias:
        external_output = tmp_path / "external-output"
        external_output.mkdir()
        (repo / "output").symlink_to(external_output, target_is_directory=True)
    if env_alias:
        external_env = tmp_path / "external-env"
        (external_env / "calibration").mkdir(parents=True)
        (repo / "output" / "env").mkdir(parents=True)
        (repo / "output" / "env" / "pegasus").symlink_to(
            external_env, target_is_directory=True
        )
    prereg = _preregistration()
    manifest, manifest_root, executable, manifest_digest, executable_digest = _manifest(tmp_path)
    attempt = writable / "attempt"
    receipt = _attempt_tree(
        attempt, prereg, executable, executable_digest, state=claimed
    )
    identity = resolve_git_identity(repo.resolve())
    result = validate_t810(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=identity,
        approved_git_identity_sha256=git_identity_digest(identity),
        writable_root=writable.resolve(),
        manifest_path=manifest,
        manifest_root=manifest_root,
        expected_manifest_sha256=manifest_digest,
        executable=executable,
        expected_executable_sha256=executable_digest,
        attempt_root=attempt,
        attempt_receipt=receipt,
        attempt_nonce="attempt-1",
        pre_invocation_nonce="invocation-1",
        claimed_state=claimed,
        mountinfo_text=_mountinfo() if mountinfo_text is None else mountinfo_text,
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
    assert "canonical_forbidden_roots" not in inspect.signature(validate_t810).parameters


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


def test_m1_inspect_repository_itself_records_ignored_untracked_file(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    (repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    hidden = repo / "ignored" / "deep" / "must-be-seen.bin"
    hidden.parent.mkdir(parents=True)
    hidden.write_bytes(b"seen-through-inspect-repository")
    identity = resolve_git_identity(repo.resolve())
    snapshot = inspect_repository(repo.resolve(), identity)
    assert "ignored/deep/must-be-seen.bin" in {item.path for item in snapshot.files}


def test_mode_change_is_part_of_repository_snapshot(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    identity = resolve_git_identity(repo.resolve())
    before = inspect_repository(repo.resolve(), identity)
    (repo / "tracked.txt").chmod(0o755)
    after = inspect_repository(repo.resolve(), identity)
    assert before != after


def test_scan_root_identity_and_external_hardlink_nlink_are_sealed(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    member = root / "member"
    member.write_bytes(b"stable bytes")
    before = scan_tree(root)
    assert before.root_record is not None
    assert before.root_record.dev == root.stat().st_dev
    external_link = tmp_path / "external-link"
    external_link.hardlink_to(member)
    after = scan_tree(root)
    assert before != after
    assert after.records[0].nlink == before.records[0].nlink + 1


def test_git_environment_is_sanitized_and_alternates_is_not_excluded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = _git_repo(tmp_path / "repo")
    decoy = _git_repo(tmp_path / "decoy")
    identity = resolve_git_identity(repo.resolve())
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(decoy / ".git" / "index"))
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "1")
    before = inspect_repository(repo.resolve(), identity)
    assert inspect_repository(repo.resolve(), identity) == before
    alternates = repo / ".git" / "objects" / "info" / "alternates"
    alternates.parent.mkdir(parents=True, exist_ok=True)
    alternates.write_text(str(decoy / ".git" / "objects") + "\n", encoding="utf-8")
    after = inspect_repository(repo.resolve(), identity)
    assert before != after
    assert any(item.path.endswith("objects/info/alternates") for item in after.git_common.records)


def test_linked_worktree_scans_entire_common_directory(tmp_path: Path):
    primary = _git_repo(tmp_path / "primary")
    linked = tmp_path / "linked"
    _run("git", "worktree", "add", "-q", str(linked), cwd=primary)
    identity = resolve_git_identity(linked.resolve())
    before = inspect_repository(linked.resolve(), identity)
    common_marker = Path(identity.common_dir_realpath) / "validator-common-marker"
    common_marker.write_text("changed common-dir semantics\n", encoding="utf-8")
    after = inspect_repository(linked.resolve(), identity)
    assert before != after
    assert any(item.path == "validator-common-marker" for item in after.git_common.records)


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


def test_claimed_state_is_only_an_equality_check_not_a_classifier(tmp_path: Path):
    prereg = _preregistration()
    _, _, executable, _, digest = _manifest(tmp_path)
    receipt = _receipt(prereg, executable, digest, claimed="valid")
    assert classify_terminal_state(
        receipt,
        expected_slots=13,
        claimed_state="terminal_reduced",
        post_validation_passed=True,
    ) == "valid"


def test_m10_missing_receipt_is_not_event_absence():
    assert classify_terminal_state(
        None, expected_slots=13, claimed_state="pre_release_invalid",
        post_validation_passed=False,
    ) == "incomplete_after_start"
    assert classify_terminal_state(
        {"coordinator": {}, "slots": []},
        expected_slots=13,
        claimed_state="pre_release_invalid",
        post_validation_passed=False,
    ) == "incomplete_after_start"


def test_m12_zero_reached_slots_cannot_vacuously_classify_valid(tmp_path: Path):
    prereg = _preregistration()
    _, _, executable, _, digest = _manifest(tmp_path)
    receipt = _receipt(prereg, executable, digest)
    receipt["coordinator"]["reached_slots"] = []
    receipt["coordinator"]["node_receipt_sha256"] = {}
    receipt["slots"] = []
    assert classify_terminal_state(
        receipt,
        expected_slots=13,
        claimed_state="valid",
        post_validation_passed=True,
    ) == "incomplete_after_start"


def test_m11_repo_root_must_match_approved_git_identity(tmp_path: Path):
    approved = _git_repo(tmp_path / "approved")
    substituted = _git_repo(tmp_path / "substituted")
    with pytest.raises(T810ValidationError, match="approved identity"):
        inspect_repository(substituted.resolve(), resolve_git_identity(approved.resolve()))


def test_authority_digest_and_attempt_writable_capability_are_required(tmp_path: Path):
    _, repo, prereg, receipt, executable, executable_digest = _positive(tmp_path)
    identity = resolve_git_identity(repo.resolve())
    manifest = tmp_path / "manifest.json"
    common = dict(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=identity,
        writable_root=(tmp_path / "writable").resolve(),
        manifest_path=manifest,
        manifest_root=tmp_path / "frozen",
        expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        executable=executable,
        expected_executable_sha256=executable_digest,
        attempt_receipt=receipt,
        attempt_nonce="attempt-1",
        pre_invocation_nonce="invocation-1",
        claimed_state="valid",
        mountinfo_text=_mountinfo(),
    )
    with pytest.raises(T810ValidationError, match="approval authority"):
        validate_t810(
            **common,
            approved_git_identity_sha256="0" * 64,
            attempt_root=tmp_path / "writable" / "attempt",
        )
    repo_alias = tmp_path / "repo-alias"
    repo_alias.symlink_to(repo, target_is_directory=True)
    with pytest.raises(T810ValidationError, match="symlinks"):
        validate_t810(
            **{**common, "repo_root": repo_alias},
            approved_git_identity_sha256=git_identity_digest(identity),
            attempt_root=tmp_path / "writable" / "attempt",
        )
    outside = tmp_path / "outside-attempt"
    (tmp_path / "writable" / "attempt").rename(outside)
    with pytest.raises(T810ValidationError, match="strict descendant"):
        validate_t810(
            **common,
            approved_git_identity_sha256=git_identity_digest(identity),
            attempt_root=outside,
        )


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


def test_m14_real_activation_path_churn_is_blocking(tmp_path: Path):
    before, repo, prereg, receipt, executable, executable_digest = _positive(tmp_path)
    activation = repo / "orchestrator" / "campaign" / "env_contract_activations"
    activation.mkdir(parents=True)
    (activation / "00000001.json").write_text("{}\n", encoding="utf-8")
    identity = resolve_git_identity(repo.resolve())
    manifest = tmp_path / "manifest.json"
    previous = BaselineEnvelope(
        before.baseline, before.baseline_digest, before.lineage, "0" * 64
    )
    after = validate_t810(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=identity,
        approved_git_identity_sha256=git_identity_digest(identity),
        writable_root=(tmp_path / "writable").resolve(),
        manifest_path=manifest,
        manifest_root=tmp_path / "frozen",
        expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        executable=executable,
        expected_executable_sha256=executable_digest,
        attempt_root=tmp_path / "writable" / "attempt",
        attempt_receipt=receipt,
        attempt_nonce="attempt-1",
        pre_invocation_nonce="invocation-1",
        claimed_state="valid",
        previous_baseline=previous,
        mountinfo_text=_mountinfo(),
    )
    assert not after.ok
    assert "FORBIDDEN_ENV_CONTRACT_ACTIVATIONS_CHURN" in {
        finding.code for finding in after.findings
    }


def test_canonical_output_symlink_target_churn_is_blocking(tmp_path: Path):
    before, repo, prereg, receipt, executable, executable_digest = _positive(
        tmp_path, output_alias=True
    )
    (tmp_path / "external-output" / "late-artifact").write_bytes(b"forbidden churn")
    identity = resolve_git_identity(repo.resolve())
    manifest = tmp_path / "manifest.json"
    after = validate_t810(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=identity,
        approved_git_identity_sha256=git_identity_digest(identity),
        writable_root=(tmp_path / "writable").resolve(),
        manifest_path=manifest,
        manifest_root=tmp_path / "frozen",
        expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        executable=executable,
        expected_executable_sha256=executable_digest,
        attempt_root=tmp_path / "writable" / "attempt",
        attempt_receipt=receipt,
        attempt_nonce="attempt-1",
        pre_invocation_nonce="invocation-1",
        claimed_state="valid",
        previous_baseline=BaselineEnvelope(
            before.baseline, before.baseline_digest, before.lineage, "0" * 64
        ),
        mountinfo_text=_mountinfo(),
    )
    assert not after.ok
    assert "FORBIDDEN_OUTPUT_CHURN" in {finding.code for finding in after.findings}


def test_final_rescan_detects_churn_after_the_first_double_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _, repo, prereg, receipt, executable, executable_digest = _positive(tmp_path)
    identity = resolve_git_identity(repo.resolve())
    module = __import__(
        "orchestrator.campaign.t810_validator", fromlist=["inspect_repository"]
    )
    original = module.inspect_repository
    calls = 0

    def racing_inspect(repo_root: Path, approved_identity):
        nonlocal calls
        calls += 1
        if calls == 2:
            (repo / "late-ignored.bin").write_bytes(b"late churn")
        return original(repo_root, approved_identity)

    monkeypatch.setattr(module, "inspect_repository", racing_inspect)
    manifest = tmp_path / "manifest.json"
    result = validate_t810(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=identity,
        approved_git_identity_sha256=git_identity_digest(identity),
        writable_root=(tmp_path / "writable").resolve(),
        manifest_path=manifest,
        manifest_root=tmp_path / "frozen",
        expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        executable=executable,
        expected_executable_sha256=executable_digest,
        attempt_root=tmp_path / "writable" / "attempt",
        attempt_receipt=receipt,
        attempt_nonce="attempt-1",
        pre_invocation_nonce="invocation-1",
        claimed_state="valid",
        mountinfo_text=_mountinfo(),
    )
    assert not result.ok
    assert "FINAL_SNAPSHOT_CHURN" in {finding.code for finding in result.findings}


def test_m14_caller_cannot_omit_activation_inventory(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    writable = tmp_path / "writable"
    writable.mkdir()
    prereg = _preregistration()
    manifest, manifest_root, executable, manifest_digest, executable_digest = _manifest(tmp_path)
    attempt = writable / "attempt"
    receipt = _attempt_tree(attempt, prereg, executable, executable_digest)
    identity = resolve_git_identity(repo.resolve())
    with pytest.raises(T810ValidationError, match="exact three"):
        validate_t810(
            preregistration=prereg, repo_root=repo.resolve(),
            approved_git_identity=identity,
            approved_git_identity_sha256=git_identity_digest(identity),
            writable_root=writable.resolve(),
            manifest_path=manifest, manifest_root=manifest_root,
            expected_manifest_sha256=manifest_digest, executable=executable,
            expected_executable_sha256=executable_digest, attempt_root=attempt,
            attempt_receipt=receipt, attempt_nonce="attempt-1",
            pre_invocation_nonce="invocation-1", claimed_state="valid",
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

    # output/env/<env> 自体が symlink でも calibration を列挙から落とさない。
    external_env = tmp_path / "external-env"
    external_calibration = external_env / "calibration"
    external_calibration.mkdir(parents=True)
    env_root = repo / "output" / "env"
    env_root.mkdir(parents=True, exist_ok=True)
    (env_root / "aliased").symlink_to(external_env, target_is_directory=True)
    module = __import__(
        "orchestrator.campaign.t810_validator", fromlist=["_calibration_inventories"]
    )
    with pytest.raises(T810ValidationError, match="overlaps calibration"):
        module._calibration_inventories(repo.resolve(), external_calibration.resolve())


@pytest.mark.parametrize(
    "state",
    [
        "pre_release_invalid",
        "post_release_pre_measurement_invalid",
        "incomplete_after_start",
        "terminal_reduced",
        "valid",
    ],
)
def test_m16_all_frozen_terminal_topologies_are_not_over_rejected(
    tmp_path: Path, state: str
):
    result, _, _, _, _, _ = _positive(tmp_path, claimed=state)
    assert result.ok
    assert result.terminal_state == state


def test_m16_non_overlapping_environment_symlink_alias_is_inventoried_and_passes(
    tmp_path: Path,
):
    result, _, _, _, _, _ = _positive(tmp_path, env_alias=True)
    assert result.ok
    assert result.baseline.calibration


def test_m16_non_overlapping_separate_mount_topology_passes(tmp_path: Path):
    writable = (tmp_path / "writable").absolute()
    mountinfo = (
        "1 0 0:1 / / rw - tmpfs synthetic rw\n"
        f"2 1 0:2 / {writable} rw - tmpfs writable rw\n"
    )
    result, _, _, _, _, _ = _positive(tmp_path, mountinfo_text=mountinfo)
    assert result.ok


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


def test_non_completed_slot_execution_and_receipt_file_substitution_are_rejected(
    tmp_path: Path,
):
    result, repo, prereg, receipt, executable, digest = _positive(
        tmp_path, claimed="terminal_reduced"
    )
    assert result.ok
    dropped = receipt["slots"][-1]
    dropped["executions"] = [{
        "argv": list(canonical_benchmark_argv(prereg, str(executable.resolve()))),
        "executable_realpath": str(executable.resolve()),
        "executable_sha256": digest,
        "round_id": 1,
    }]
    findings = __import__(
        "orchestrator.campaign.t810_validator", fromlist=["_verify_executable_and_argv"]
    )._verify_executable_and_argv(prereg, executable, digest, receipt["slots"])
    assert "NON_COMPLETED_SLOT_HAS_EXECUTIONS" in {finding.code for finding in findings}

    receipt_path = (
        tmp_path / "writable" / "attempt" / "slot-12" / "node-receipt.jsonl"
    )
    dropped_raw = _json_bytes(dropped)
    receipt_path.write_bytes(dropped_raw)
    receipt["coordinator"]["node_receipt_sha256"]["slot-12"] = hashlib.sha256(
        dropped_raw
    ).hexdigest()
    coordinator_raw = _json_bytes(receipt["coordinator"])
    (tmp_path / "writable" / "attempt" / "coordinator-receipt.jsonl").write_bytes(
        coordinator_raw
    )
    receipt["coordinator_receipt_sha256"] = hashlib.sha256(coordinator_raw).hexdigest()
    identity = resolve_git_identity(repo.resolve())
    manifest = tmp_path / "manifest.json"
    common = dict(
        preregistration=prereg,
        repo_root=repo.resolve(),
        approved_git_identity=identity,
        approved_git_identity_sha256=git_identity_digest(identity),
        writable_root=(tmp_path / "writable").resolve(),
        manifest_path=manifest,
        manifest_root=tmp_path / "frozen",
        expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        executable=executable,
        expected_executable_sha256=digest,
        attempt_root=tmp_path / "writable" / "attempt",
        attempt_receipt=receipt,
        attempt_nonce="attempt-1",
        pre_invocation_nonce="invocation-1",
        claimed_state="terminal_reduced",
        mountinfo_text=_mountinfo(),
    )
    forged = validate_t810(**common)
    assert not forged.ok
    assert "NON_COMPLETED_SLOT_HAS_EXECUTIONS" in {
        finding.code for finding in forged.findings
    }

    receipt_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(T810ValidationError, match="node receipt chain"):
        validate_t810(**common)


def test_estimate_input_set_is_bound_to_actual_measurement_hashes(tmp_path: Path):
    _, repo, prereg, receipt, executable, digest = _positive(tmp_path)
    estimate_path = tmp_path / "writable" / "attempt" / "estimate.json"
    estimate = json.loads(estimate_path.read_text(encoding="utf-8"))
    del estimate["input_measurements_sha256"]["slot-00"]
    estimate_raw = _json_bytes(estimate)
    estimate_path.write_bytes(estimate_raw)
    receipt["coordinator"]["estimate_sha256"] = hashlib.sha256(estimate_raw).hexdigest()
    coordinator_raw = _json_bytes(receipt["coordinator"])
    (tmp_path / "writable" / "attempt" / "coordinator-receipt.jsonl").write_bytes(
        coordinator_raw
    )
    receipt["coordinator_receipt_sha256"] = hashlib.sha256(coordinator_raw).hexdigest()
    identity = resolve_git_identity(repo.resolve())
    manifest = tmp_path / "manifest.json"
    with pytest.raises(T810ValidationError, match="estimate input"):
        validate_t810(
            preregistration=prereg,
            repo_root=repo.resolve(),
            approved_git_identity=identity,
            approved_git_identity_sha256=git_identity_digest(identity),
            writable_root=(tmp_path / "writable").resolve(),
            manifest_path=manifest,
            manifest_root=tmp_path / "frozen",
            expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            executable=executable,
            expected_executable_sha256=digest,
            attempt_root=tmp_path / "writable" / "attempt",
            attempt_receipt=receipt,
            attempt_nonce="attempt-1",
            pre_invocation_nonce="invocation-1",
            claimed_state="valid",
            mountinfo_text=_mountinfo(),
        )


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


def test_m15_cli_existing_witness_fast_path_cannot_return_zero(tmp_path: Path):
    repo = _git_repo(tmp_path / "repo")
    writable = tmp_path / "writable"
    proofs = writable / "proofs"
    proofs.mkdir(parents=True)
    prereg = _preregistration()
    manifest, manifest_root, executable, manifest_digest, executable_digest = _manifest(tmp_path)
    attempt = writable / "attempt"
    receipt = _attempt_tree(attempt, prereg, executable, executable_digest)
    receipt_path = tmp_path / "attempt-receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")

    identity = resolve_git_identity(repo.resolve())
    identity_path = tmp_path / "git-identity.json"
    identity_path.write_text(json.dumps(identity.__dict__, sort_keys=True), encoding="utf-8")
    artifact_sha256 = hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps({
        "approval_id": "validator-cli-test",
        "artifact_sha256": artifact_sha256,
        "git_identity_sha256": git_identity_digest(identity),
        "schema_version": APPROVAL_RECEIPT_SCHEMA_VERSION,
    }, sort_keys=True), encoding="utf-8")
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps({
        "attempt_receipt": str(receipt_path.resolve()),
        "attempt_root": str(attempt.resolve()),
        "claimed_state": "valid",
        "executable": str(executable.resolve()),
        "expected_executable_sha256": executable_digest,
        "expected_manifest_sha256": manifest_digest,
        "manifest_path": str(manifest.resolve()),
        "manifest_root": str(manifest_root.resolve()),
        "preregistration": str(PREREG_PATH.resolve()),
        "repo_root": str(repo.resolve()),
        "writable_root": str(writable.resolve()),
    }, sort_keys=True), encoding="utf-8")
    baseline = proofs / "baseline.json"
    witness = proofs / "pre-pass.json"
    argv = [
        "pre",
        "--request", str(request_path),
        "--approval-receipt", str(approval_path),
        "--approved-git-identity", str(identity_path),
        "--baseline", str(baseline),
        "--pass-witness", str(witness),
        "--attempt-nonce", "attempt-1",
    ]
    assert validator_cli_main(argv) == 0
    assert witness.exists()
    successful_post_witness = proofs / "successful-post-pass.json"
    successful_post_argv = [
        "post",
        "--request", str(request_path),
        "--approval-receipt", str(approval_path),
        "--approved-git-identity", str(identity_path),
        "--baseline", str(baseline),
        "--pre-pass-witness", str(witness),
        "--pass-witness", str(successful_post_witness),
        "--attempt-nonce", "attempt-1",
    ]
    assert validator_cli_main(successful_post_argv) == 0
    assert validator_cli_main(argv) == 2

    # pre witness finalize が失敗して baseline だけ残っても post lineage には使えない。
    failed_baseline = proofs / "failed-baseline.json"
    stale_witness = proofs / "stale-pre-pass.json"
    stale_witness.write_text("{}\n", encoding="utf-8")
    failed_pre_argv = list(argv)
    failed_pre_argv[failed_pre_argv.index(str(baseline))] = str(failed_baseline)
    failed_pre_argv[failed_pre_argv.index(str(witness))] = str(stale_witness)
    assert validator_cli_main(failed_pre_argv) == 2
    assert failed_baseline.exists()
    post_witness = proofs / "post-pass.json"
    post_argv = [
        "post",
        "--request", str(request_path),
        "--approval-receipt", str(approval_path),
        "--approved-git-identity", str(identity_path),
        "--baseline", str(failed_baseline),
        "--pre-pass-witness", str(stale_witness),
        "--pass-witness", str(post_witness),
        "--attempt-nonce", "attempt-1",
    ]
    assert validator_cli_main(post_argv) == 2
    assert not post_witness.exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
