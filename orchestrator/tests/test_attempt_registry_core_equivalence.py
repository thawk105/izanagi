"""Differential proof that the 8c facade preserves its frozen state machine."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import re
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign import attempt_registry_core as core
from orchestrator.campaign import trial_registry as R


_ZERO = "0" * 64
_SCHEMA_VERSION = "p3-8c-attempt-registry/v2"
_RETRYABLE_REASONS = (
    "launcher-failure", "node-failure", "preempted", "wall-timeout",
)
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
_SLOT_KEYS = frozenset({
    "slot_id", "trial_id", "arm", "holdout", "campaign_id",
    "replicate_index", "attempt_index", "schedule_row_sha256",
})


class _LegacyBuilderError(RuntimeError):
    """Independent model of the pre-extraction builder rejection surface."""


def _legacy_fail(gate: str, message: str) -> None:
    raise _LegacyBuilderError(f"[{gate}] {message}")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _legacy_canonical(value: object) -> bytes:
    try:
        return _canonical(value)
    except (TypeError, ValueError) as exc:
        raise _LegacyBuilderError(
            f"[json] value is not canonical JSON: {exc}"
        ) from exc


def _legacy_event(
    value: dict[str, object], *, index: int, previous: str,
) -> dict[str, object]:
    row = {**value, "event_index": index, "previous_event_sha256": previous}
    row["event_sha256"] = hashlib.sha256(_legacy_canonical(row)).hexdigest()
    return row


def _legacy_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        _legacy_fail(
            "attempt-registry-schema",
            f"{label} is not a bounded non-empty string",
        )
    return value


def _legacy_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _legacy_fail(
            "attempt-registry-schema", f"{label} is not a SHA-256 digest",
        )
    return value


def _legacy_parse_slot(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        _legacy_fail("attempt-registry-schema", f"{label} is not an object")
    actual = frozenset(value)
    if actual != _SLOT_KEYS:
        _legacy_fail(
            "schema",
            f"{label} key set differs: missing={sorted(_SLOT_KEYS - actual)}, "
            f"unknown={sorted(actual - _SLOT_KEYS)}",
        )
    _legacy_text(value.get("slot_id"), label=f"{label}.slot_id")
    trial_id = value.get("trial_id")
    if (
        not isinstance(trial_id, str)
        or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", trial_id) is None
    ):
        _legacy_fail(
            "attempt-registry-schema", f"{label}.trial_id is invalid",
        )
    if value.get("arm") not in ("on", "off", "swapped"):
        _legacy_fail(
            "attempt-registry-schema", f"{label}.arm is outside the closed set",
        )
    if value.get("holdout") not in ("H1", "H2"):
        _legacy_fail(
            "attempt-registry-schema", f"{label}.holdout is outside the closed set",
        )
    _legacy_text(value.get("campaign_id"), label=f"{label}.campaign_id")
    for field in ("replicate_index", "attempt_index"):
        raw = value.get(field)
        if type(raw) is not int or raw < 0:
            _legacy_fail(
                "attempt-registry-schema", f"{label}.{field} is invalid",
            )
    _legacy_digest(
        value.get("schedule_row_sha256"),
        label=f"{label}.schedule_row_sha256",
    )
    return dict(value)


def _legacy_build_genesis_for_rejection(
    slots: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    """Reimplement 5a4cbfa8:2701-2716 without production helpers."""
    value = _legacy_event({
        "schema_version": _SCHEMA_VERSION,
        "event": "freeze",
        "freeze_id": "reference-freeze",
        "manifest_path": "manifest.json",
        "manifest_sha256": hashlib.sha256(b"{}\n").hexdigest(),
        "root_path": "output/s8c-preregistration/attempt-registry.jsonl",
        "retryable_failure_reasons": list(_RETRYABLE_REASONS),
        "slots": [dict(slot) for slot in slots],
    }, index=0, previous=_ZERO)
    parsed_slots = [
        _legacy_parse_slot(
            slot, label=f"attempt registry genesis.slots[{index}]",
        )
        for index, slot in enumerate(value["slots"])
    ]
    return ({**value, "slots": parsed_slots},)


def _legacy_capability_digest(
    *, freeze_id: str, slot: dict[str, object], binding: tuple[str, str],
) -> str:
    return hashlib.sha256(_canonical({
        "schema_version": _SCHEMA_VERSION,
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
        "schema_version": _SCHEMA_VERSION,
        "event": "freeze",
        "freeze_id": freeze_id,
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha256,
        "root_path": "output/s8c-preregistration/attempt-registry.jsonl",
        "retryable_failure_reasons": list(_RETRYABLE_REASONS),
        "slots": [slot],
    }, index=0, previous=_ZERO)
    start = _legacy_event({
        "schema_version": _SCHEMA_VERSION,
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
        "schema_version": _SCHEMA_VERSION,
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
        "schema_version": _SCHEMA_VERSION,
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
        "schema_version": _SCHEMA_VERSION,
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
        repo / "output/s8c-trial-registry/classification-receipts"
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
        "schema_version": _SCHEMA_VERSION,
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


@pytest.mark.parametrize(
    "case",
    (
        "non-json-value",
        "wrong-field-type",
        "missing-key",
        "extra-key",
        "out-of-range-value",
    ),
)
def test_genesis_builder_rejection_matches_pre_extraction_order(
    tmp_path: Path, case: str,
) -> None:
    slot = _slot()
    if case == "non-json-value":
        slot["arm"] = object()
    elif case == "wrong-field-type":
        slot["replicate_index"] = "zero"
    elif case == "missing-key":
        del slot["arm"]
    elif case == "extra-key":
        slot["unexpected"] = "field"
    elif case == "out-of-range-value":
        slot["arm"] = "forbidden-arm"
    else:  # pragma: no cover - closed parametrization
        raise AssertionError(case)

    with pytest.raises(_LegacyBuilderError) as legacy_error:
        _legacy_build_genesis_for_rejection([slot])

    manifest_sha256 = hashlib.sha256(b"{}\n").hexdigest()
    with pytest.raises(
        (core.AttemptRegistryCoreError, R.TrialRegistryError)
    ) as core_error:
        core.create_attempt_registry_genesis(
            profile=R._S8C_ATTEMPT_PROFILE,
            freeze_id="reference-freeze",
            manifest_path=Path("manifest.json"),
            manifest_sha256=manifest_sha256,
            slots=[slot],
        )

    repo = tmp_path / "builder-rejection-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    manifest = repo / "manifest.json"
    manifest.write_bytes(b"{}\n")
    with pytest.raises(R.TrialRegistryError) as facade_error:
        R.create_attempt_registry_genesis(
            repository_root=repo,
            manifest_path=manifest,
            manifest_sha256=manifest_sha256,
            freeze_id="reference-freeze",
            slots=[slot],
        )

    expected = str(legacy_error.value)
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


def test_frozen_paths_and_public_signatures_are_literal_pinned() -> None:
    assert R.DEFAULT_ATTEMPT_REGISTRY_PATH == Path(
        "output/s8c-preregistration/attempt-registry.jsonl"
    )
    assert (
        R._S8C_ATTEMPT_PROFILE.layout.classification_receipt_dir.as_posix()
        == "output/s8c-trial-registry/classification-receipts"
    )
    actual = {
        name: str(inspect.signature(getattr(R, name)))
        for name in (
            "create_attempt_registry_genesis",
            "load_attempt_registry",
            "reserve_attempt_slot",
            "classify_attempt",
            "begin_attempt_observation",
            "record_attempt_terminal",
        )
    }
    assert actual == {
        "create_attempt_registry_genesis": (
            "(*, repository_root: 'Path', manifest_path: 'Path', "
            "manifest_sha256: 'str', freeze_id: 'str', "
            "slots: 'Sequence[Mapping[str, Any]]', "
            "retryable_failure_reasons: 'Sequence[str]' = "
            "('launcher-failure', 'node-failure', 'preempted', 'wall-timeout'), "
            "registry_path: 'Path' = "
            "PosixPath('output/s8c-preregistration/attempt-registry.jsonl')) "
            "-> 'Path'"
        ),
        "load_attempt_registry": (
            "(repository_root: 'Path', *, registry_path: 'Path' = "
            "PosixPath('output/s8c-preregistration/attempt-registry.jsonl'), "
            "prereg_content_commit: 'str | None' = None, "
            "prereg_effective_commit: 'str | None' = None, "
            "freeze_id: 'str | None' = None, manifest_path: 'Path | None' = "
            "None, manifest_sha256: 'str | None' = None) -> "
            "'tuple[dict[str, Any], ...]'"
        ),
        "reserve_attempt_slot": (
            "(*, repository_root: 'Path', freeze_id: 'str', slot_id: 'str', "
            "prereg_content_commit: 'str', prereg_effective_commit: 'str', "
            "run_start_receipt_sha256: 'str', process_identity: "
            "'Mapping[str, Any]', started_at: 'str', registry_path: 'Path' = "
            "PosixPath('output/s8c-preregistration/attempt-registry.jsonl')) "
            "-> 'AttemptSlotCapability'"
        ),
        "classify_attempt": (
            "(capability: 'AttemptSlotCapability', *, "
            "pre_observation_failure_reason: 'str | None', authority_id: 'str', "
            "authority_policy_sha256: 'str', external_evidence_sha256: 'str', "
            "classified_at: 'str') -> 'dict[str, Any]'"
        ),
        "begin_attempt_observation": (
            "(capability: 'AttemptSlotCapability') -> 'dict[str, Any]'"
        ),
        "record_attempt_terminal": (
            "(capability: 'AttemptSlotCapability', *, terminal_status: 'str', "
            "raw_output_sha256: 'str', report_sha256: 'str | None', "
            "observation_sha256: 'str | None', primary_value: 'Any', "
            "finished_at: 'str', failure_reason: 'str | None' = None) -> 'None'"
        ),
    }


def test_facade_namespace_keeps_core_helpers_private() -> None:
    assert "PurePosixPath" not in vars(R)
    assert "attempt_core" not in vars(R)


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
