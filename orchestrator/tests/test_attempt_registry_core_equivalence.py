"""Differential proof that the 8c facade preserves its frozen state machine."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign import attempt_registry_core as core
from orchestrator.campaign import trial_registry as R


_ZERO = "0" * 64
_CONTENT = "1" * 40
_EFFECTIVE = "2" * 40
_RUN_START = "3" * 64
_POLICY = "4" * 64
_EXTERNAL = "5" * 64
_RAW = "6" * 64
_REPORT = "7" * 64
_PROCESS = {
    "pid": 101,
    "starttime": "reference-start",
    "execution_uuid": "reference-execution",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _legacy_event(
    value: dict[str, object], *, index: int, previous: str,
) -> dict[str, object]:
    row = {**value, "event_index": index, "previous_event_sha256": previous}
    row["event_sha256"] = hashlib.sha256(_canonical(row)).hexdigest()
    return row


def _legacy_capability_digest(
    *, freeze_id: str, slot: dict[str, object], binding: tuple[str, str],
) -> str:
    return hashlib.sha256(_canonical({
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "trial_id": slot["trial_id"],
        "arm": slot["arm"],
        "holdout": slot["holdout"],
        "campaign_id": slot["campaign_id"],
        "replicate_index": slot["replicate_index"],
        "attempt_index": slot["attempt_index"],
        "schedule_row_sha256": slot["schedule_row_sha256"],
        "prereg_content_commit": binding[0],
        "prereg_effective_commit": binding[1],
    })).hexdigest()


def _slot(*, attempt_index: int = 0) -> dict[str, object]:
    identity = {
        "trial_id": "reference-trial",
        "arm": "on",
        "holdout": "H1",
        "campaign_id": "reference-campaign",
        "replicate_index": 0,
        "attempt_index": attempt_index,
    }
    return {
        "slot_id": f"reference-trial-r0-a{attempt_index}",
        **identity,
        "schedule_row_sha256": hashlib.sha256(_canonical(identity)).hexdigest(),
    }


def _legacy_reference(
    *, manifest_path: str, manifest_sha256: str, freeze_id: str,
    slot: dict[str, object], binding: tuple[str, str],
) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
    genesis = _legacy_event({
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "freeze",
        "freeze_id": freeze_id,
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha256,
        "root_path": R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "retryable_failure_reasons": sorted(R.ATTEMPT_RETRYABLE_FAILURE_REASONS),
        "slots": [slot],
    }, index=0, previous=_ZERO)
    start = _legacy_event({
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "start",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "prereg_content_commit": binding[0],
        "prereg_effective_commit": binding[1],
        "run_start_receipt_sha256": _RUN_START,
        "process_identity": _PROCESS,
        "schedule_row_sha256": slot["schedule_row_sha256"],
        "started_at": "2026-08-23T00:00:00+00:00",
    }, index=1, previous=genesis["event_sha256"])
    seal = _legacy_event({
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "pre-observation-seal",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "start_event_sha256": start["event_sha256"],
        "run_start_receipt_sha256": _RUN_START,
        "process_identity": _PROCESS,
        "schedule_row_sha256": slot["schedule_row_sha256"],
    }, index=2, previous=start["event_sha256"])
    capability_digest = _legacy_capability_digest(
        freeze_id=freeze_id, slot=slot, binding=binding,
    )
    receipt = {
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "classification-receipt",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "capability_digest_sha256": capability_digest,
        "authority_id": "reference-authority",
        "authority_policy_sha256": _POLICY,
        "external_evidence_sha256": _EXTERNAL,
        "classified_at": "2026-08-23T00:00:01+00:00",
        "pre_observation_failure_reason": "wall-timeout",
        "pre_observation_seal_sha256": seal["event_sha256"],
    }
    receipt_sha256 = hashlib.sha256(_canonical(receipt) + b"\n").hexdigest()
    classification = _legacy_event({
        **receipt,
        "event": "classification",
        "prereg_content_commit": binding[0],
        "prereg_effective_commit": binding[1],
        "classification_receipt_sha256": receipt_sha256,
    }, index=3, previous=seal["event_sha256"])
    terminal = _legacy_event({
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "terminal",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "prereg_content_commit": binding[0],
        "prereg_effective_commit": binding[1],
        "classification_receipt_sha256": receipt_sha256,
        "terminal_status": "retryable-failure",
        "raw_output_sha256": _RAW,
        "report_sha256": _REPORT,
        "observation_sha256": None,
        "primary_value": None,
        # Frozen 8c deliberately accepts a terminal reason that differs from
        # the classification reason, while preserving the exact echo.
        "failure_reason": "preempted",
        "pre_observation_failure_reason_echo": "wall-timeout",
        "observation_start_event_sha256": None,
        "finished_at": "2026-08-23T00:00:02+00:00",
        "schedule_row_sha256": slot["schedule_row_sha256"],
        "process_identity": _PROCESS,
    }, index=4, previous=classification["event_sha256"])
    return (genesis, start, seal, classification, terminal), receipt


def _core_reference(
    *, manifest_sha256: str, freeze_id: str, slot: dict[str, object],
    binding: tuple[str, str],
) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
    rows = core.create_attempt_registry_genesis(
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id=freeze_id,
        manifest_path=Path("manifest.json"),
        manifest_sha256=manifest_sha256,
        slots=[slot],
    )
    rows = core.reserve_attempt_slot(
        rows,
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-23T00:00:00+00:00",
    )
    capability_digest = _legacy_capability_digest(
        freeze_id=freeze_id, slot=slot, binding=binding,
    )
    rows, receipt = core.classify_attempt(
        rows,
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        capability_digest_sha256=capability_digest,
        pre_observation_failure_reason="wall-timeout",
        authority_id="reference-authority",
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=_EXTERNAL,
        classified_at="2026-08-23T00:00:01+00:00",
    )
    rows = core.record_attempt_terminal(
        rows,
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        binding=binding,
        terminal_status="retryable-failure",
        raw_output_sha256=_RAW,
        report_sha256=_REPORT,
        observation_sha256=None,
        primary_value=None,
        finished_at="2026-08-23T00:00:02+00:00",
        failure_reason="preempted",
    )
    return rows, receipt


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _commit(repo: Path, message: str, *paths: Path) -> str:
    _git(repo, "add", "--", *(str(path.relative_to(repo)) for path in paths))
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _facade_reference(
    tmp_path: Path, *, manifest_sha256: str, freeze_id: str,
    slot: dict[str, object],
) -> tuple[tuple[dict[str, object], ...], bytes]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "attempt-core@example.invalid")
    _git(repo, "config", "user.name", "Attempt Core Test")
    manifest = repo / "manifest.json"
    manifest.write_bytes(b"{}\n")
    _commit(repo, "manifest", manifest)
    registry = R.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest,
        manifest_sha256=manifest_sha256,
        freeze_id=freeze_id,
        slots=[slot],
    )
    content = _commit(repo, "attempt genesis", registry)
    marker = repo / "effective.txt"
    marker.write_text("effective\n", encoding="utf-8")
    effective = _commit(repo, "effective", marker)
    capability = R.reserve_attempt_slot(
        repository_root=repo,
        freeze_id=freeze_id,
        slot_id=str(slot["slot_id"]),
        prereg_content_commit=content,
        prereg_effective_commit=effective,
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-23T00:00:00+00:00",
    )
    receipt = R.classify_attempt(
        capability,
        pre_observation_failure_reason="wall-timeout",
        authority_id="reference-authority",
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=_EXTERNAL,
        classified_at="2026-08-23T00:00:01+00:00",
    )
    R.record_attempt_terminal(
        capability,
        terminal_status="retryable-failure",
        raw_output_sha256=_RAW,
        report_sha256=_REPORT,
        observation_sha256=None,
        primary_value=None,
        finished_at="2026-08-23T00:00:02+00:00",
        failure_reason="preempted",
    )
    receipt_bytes = _canonical(receipt) + b"\n"
    stored_receipt = (
        repo / R._S8C_ATTEMPT_PROFILE.layout.classification_receipt_dir
        / f"{hashlib.sha256(receipt_bytes).hexdigest()}.json"
    ).read_bytes()
    rows = tuple(
        json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines()
    )
    return rows, stored_receipt


def _row_bytes(rows: tuple[dict[str, object], ...]) -> bytes:
    return b"".join(_canonical(row) + b"\n" for row in rows)


def test_reference_core_and_facade_event_and_receipt_bytes_are_identical(
    tmp_path: Path,
) -> None:
    manifest_sha256 = hashlib.sha256(b"{}\n").hexdigest()
    freeze_id = "reference-freeze"
    slot = _slot()
    facade_rows, facade_receipt = _facade_reference(
        tmp_path,
        manifest_sha256=manifest_sha256,
        freeze_id=freeze_id,
        slot=slot,
    )
    binding = (
        facade_rows[1]["prereg_content_commit"],
        facade_rows[1]["prereg_effective_commit"],
    )
    legacy_rows, legacy_receipt = _legacy_reference(
        manifest_path="manifest.json",
        manifest_sha256=manifest_sha256,
        freeze_id=freeze_id,
        slot=slot,
        binding=binding,
    )
    core_rows, core_receipt = _core_reference(
        manifest_sha256=manifest_sha256,
        freeze_id=freeze_id,
        slot=slot,
        binding=binding,
    )
    assert _row_bytes(legacy_rows) == _row_bytes(core_rows) == _row_bytes(facade_rows)
    assert (
        _canonical(legacy_receipt) + b"\n"
        == _canonical(core_receipt) + b"\n"
        == facade_receipt
    )


def test_unknown_event_rejection_reason_is_identical() -> None:
    manifest_sha256 = hashlib.sha256(b"{}\n").hexdigest()
    rows = core.create_attempt_registry_genesis(
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id="reference-freeze",
        manifest_path=Path("manifest.json"),
        manifest_sha256=manifest_sha256,
        slots=[_slot()],
    )
    unknown = _legacy_event({
        "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "recovery",
        "freeze_id": "reference-freeze",
        "slot_id": "reference-trial-r0-a0",
    }, index=1, previous=rows[0]["event_sha256"])
    payload = _row_bytes(tuple(rows) + (unknown,))
    expected = "[attempt-registry-schema] attempt registry line 2.event is unknown"
    with pytest.raises(core.AttemptRegistryCoreError) as core_error:
        core.load_attempt_registry(payload, profile=R._S8C_ATTEMPT_PROFILE)
    with pytest.raises(R.TrialRegistryError) as facade_error:
        R._load_attempt_registry_bytes(payload)
    assert str(core_error.value) == expected == str(facade_error.value)


def test_skipped_slot_rejection_reason_is_identical(tmp_path: Path) -> None:
    manifest_sha256 = hashlib.sha256(b"{}\n").hexdigest()
    freeze_id = "reference-freeze"
    slots = [_slot(attempt_index=0), _slot(attempt_index=1)]
    rows = core.create_attempt_registry_genesis(
        profile=R._S8C_ATTEMPT_PROFILE,
        freeze_id=freeze_id,
        manifest_path=Path("manifest.json"),
        manifest_sha256=manifest_sha256,
        slots=slots,
    )
    expected = (
        "[attempt-slot-order] only the next slot after a completed "
        "retryable failure may start"
    )
    with pytest.raises(core.AttemptRegistryCoreError) as core_error:
        core.reserve_attempt_slot(
            rows,
            profile=R._S8C_ATTEMPT_PROFILE,
            freeze_id=freeze_id,
            slot_id=slots[1]["slot_id"],
            binding=(_CONTENT, _EFFECTIVE),
            run_start_receipt_sha256=_RUN_START,
            process_identity=_PROCESS,
            started_at="2026-08-23T00:00:00+00:00",
        )
    assert str(core_error.value) == expected

    repo = tmp_path / "skip-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "attempt-core@example.invalid")
    _git(repo, "config", "user.name", "Attempt Core Test")
    manifest = repo / "manifest.json"
    manifest.write_bytes(b"{}\n")
    _commit(repo, "manifest", manifest)
    registry = R.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest,
        manifest_sha256=manifest_sha256,
        freeze_id=freeze_id,
        slots=slots,
    )
    content = _commit(repo, "attempt genesis", registry)
    marker = repo / "effective.txt"
    marker.write_text("effective\n", encoding="utf-8")
    effective = _commit(repo, "effective", marker)
    with pytest.raises(R.TrialRegistryError) as facade_error:
        R.reserve_attempt_slot(
            repository_root=repo,
            freeze_id=freeze_id,
            slot_id=str(slots[1]["slot_id"]),
            prereg_content_commit=content,
            prereg_effective_commit=effective,
            run_start_receipt_sha256=_RUN_START,
            process_identity=_PROCESS,
            started_at="2026-08-23T00:00:00+00:00",
        )
    assert str(facade_error.value) == expected


def test_six_facades_are_unrebound_real_functions() -> None:
    source = Path(R.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        "create_attempt_registry_genesis",
        "load_attempt_registry",
        "reserve_attempt_slot",
        "classify_attempt",
        "begin_attempt_observation",
        "record_attempt_terminal",
    }
    definitions = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    rebound = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    assert names <= definitions
    assert names.isdisjoint(rebound)


def test_core_source_has_no_8c_domain_literals() -> None:
    source = Path(core.__file__).read_text(encoding="utf-8")
    for literal in (
        "trial_id",
        "ARMS",
        "HOLDOUTS",
        "prereg_commit",
        "output/s8c-",
    ):
        assert literal not in source


if __name__ == "__main__":
    def _plain_runner_main() -> int:
        return int(pytest.main(["-q", str(Path(__file__).resolve())]))

    raise SystemExit(_plain_runner_main())
