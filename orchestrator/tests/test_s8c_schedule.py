from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from orchestrator.campaign import s8c_schedule as S


def _authority() -> dict[str, object]:
    return {
        "arms": ["on", "off", "swapped"],
        "designated_source_context": "axis:silo-backoff-trigger-gating/v1",
        "descriptor_bindings": {
            "H1": {"workload": "rr80", "ycsb_rratio": "80"},
            "H2": {"workload": "rr20", "ycsb_rratio": "20"},
        },
        "gating_spec": "five-bit-wire:v1",
        "holdout_bindings": {
            "H1": {"workload": "rr80", "ycsb_rratio": "80"},
            "H2": {"workload": "rr20", "ycsb_rratio": "20"},
        },
        "holdouts": ["H1", "H2"],
        "role_contracts": {
            "auditor": "auditor-contract:v1",
            "coder": "coder-contract:v1",
            "critic": "critic-contract:v1",
            "planner": "planner-contract:v1",
        },
        "role_files": {
            "auditor": "auditor.md",
            "coder": "coder.md",
            "critic": "critic.md",
            "planner": "planner.md",
        },
        "role_payload_allowlist": {
            "auditor": ["working_diff", "correctness_digest"],
            "coder": ["gating_spec", "baseline"],
            "critic": ["harness_result", "critic_digest"],
            "planner": ["current_perf", "whiteboard"],
        },
        "workloads": {
            "rr20": {"records": 100000, "threads": 4},
            "rr80": {"records": 100000, "threads": 4},
        },
        "attempt_policy": {"max_attempts": 1, "retry": False},
        "baseline": {"kind": "stock", "trace": False},
        "descriptor_binding": {
            "schema_version": "8b-v1",
            "descriptor_sha256": "descriptor-hash",
        },
        "gating_snapshot": {"schema_version": "gating-snapshot/v1", "wire": "10100"},
        "initial_role_metrics": {
            "abort_rate": None,
            "ipc": None,
            "latency_ns": None,
            "llc_miss_rate": None,
            "throughput_tps": None,
        },
        "leakproof_context": {
            "tools": ["declared-tool-set"],
            "projected_input_only": True,
        },
        "stop_policy": {
            "reasons": ["converged", "budget-iterations", "budget-walltime"],
        },
        "whiteboard": [{"status": "initial"}],
    }


def _decoded(artifact_bytes: bytes) -> dict[str, object]:
    value = json.loads(artifact_bytes)
    assert isinstance(value, dict)
    return value


def _order(artifact_bytes: bytes) -> tuple[tuple[str, str], ...]:
    value = _decoded(artifact_bytes)
    cells = value["cells"]
    assert isinstance(cells, list)
    return tuple((cell["holdout"], cell["arm"]) for cell in cells)


def _changed(value: object) -> object:
    if type(value) is str:
        return value + ":changed"
    if isinstance(value, dict):
        result = copy.deepcopy(value)
        result["__changed__"] = "authority-field"
        return result
    if isinstance(value, list):
        return [*value, "__changed__"]
    if isinstance(value, tuple):
        return (*value, "__changed__")
    raise AssertionError(f"fixture has unsupported value type: {type(value).__name__}")


def test_same_seed_and_authority_are_byte_exact() -> None:
    authority = _authority()
    S.validate_authority(authority)
    first = S.regenerate("seed-alpha", authority=authority)
    second = S.regenerate("seed-alpha", authority=authority)
    assert first == second
    S.verify_exact_schedule_bytes(first, master_seed="seed-alpha", authority=authority)
    verified = S.verify_schedule(first, master_seed="seed-alpha", authority=authority)
    assert verified.master_seed == "seed-alpha"


def test_seed_changes_and_fixes_the_cell_order() -> None:
    authority = _authority()
    alpha = S.regenerate("seed-alpha", authority=authority)
    beta = S.regenerate("seed-beta", authority=authority)
    assert _order(alpha) == (
        ("H2", "swapped"),
        ("H1", "swapped"),
        ("H1", "off"),
        ("H2", "on"),
        ("H1", "on"),
        ("H2", "off"),
    )
    assert _order(beta) == (
        ("H1", "swapped"),
        ("H2", "on"),
        ("H1", "on"),
        ("H2", "swapped"),
        ("H1", "off"),
        ("H2", "off"),
    )
    assert _order(alpha) != _order(beta)


def test_six_cells_are_a_schedule_index_bijection_and_full_cross_product() -> None:
    value = _decoded(S.regenerate("seed-alpha", authority=_authority()))
    cells = value["cells"]
    assert isinstance(cells, list)
    assert len(cells) == 6
    assert {cell["schedule_index"] for cell in cells} == set(range(6))
    assert {(cell["holdout"], cell["arm"]) for cell in cells} == {
        (holdout, arm) for holdout in S.HOLDOUTS for arm in S.ARMS
    }


def test_validate_authority_rejects_missing_extra_and_wrong_types() -> None:
    authority = _authority()
    missing = copy.deepcopy(authority)
    missing.pop(next(iter(S.SEARCH_SPACE_AUTHORITY_KEYS)))
    with pytest.raises(S.ScheduleError):
        S.validate_authority(missing)
    with pytest.raises(S.ScheduleError):
        S.search_space_digest(missing)
    with pytest.raises(S.ScheduleError):
        S.initial_state_digest(missing)

    extra = copy.deepcopy(authority)
    extra["unexpected"] = "not-authority"
    with pytest.raises(S.ScheduleError):
        S.validate_authority(extra)

    wrong_type = copy.deepcopy(authority)
    wrong_type["gating_spec"] = object()
    with pytest.raises(S.ScheduleError):
        S.validate_authority(wrong_type)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("workloads", {}),
        ("arms", []),
        ("gating_spec", ""),
    ),
)
def test_validate_authority_rejects_degenerate_top_level_values(
    field: str, replacement: object,
) -> None:
    authority = _authority()
    authority[field] = replacement
    with pytest.raises(S.ScheduleError):
        S.validate_authority(authority)


@pytest.mark.parametrize(
    "mutate",
    (
        lambda authority: authority["descriptor_bindings"].update(H1={}),
        lambda authority: authority["role_contracts"].update(auditor=""),
        lambda authority: authority["leakproof_context"].update(tools=[]),
    ),
)
def test_validate_authority_rejects_nested_degenerate_values(mutate) -> None:
    authority = _authority()
    mutate(authority)
    with pytest.raises(S.ScheduleError):
        S.validate_authority(authority)


def test_each_authority_field_changes_its_digest() -> None:
    authority = _authority()
    search_before = S.search_space_digest(authority)
    for key in S.SEARCH_SPACE_AUTHORITY_KEYS:
        changed = copy.deepcopy(authority)
        changed[key] = _changed(changed[key])
        assert S.search_space_digest(changed) != search_before, key

    initial_before = S.initial_state_digest(authority)
    for key in S.INITIAL_STATE_AUTHORITY_KEYS:
        changed = copy.deepcopy(authority)
        changed[key] = _changed(changed[key])
        assert S.initial_state_digest(changed) != initial_before, key


def test_exact_verifier_rejects_seed_extra_bytes_and_noncanonical_bytes() -> None:
    authority = _authority()
    artifact = S.regenerate("seed-alpha", authority=authority)
    S.verify_exact_schedule_bytes(artifact, master_seed="seed-alpha", authority=authority)

    with pytest.raises(S.ScheduleError):
        S.verify_exact_schedule_bytes(artifact, master_seed="seed-beta", authority=authority)
    with pytest.raises(S.ScheduleError):
        S.verify_exact_schedule_bytes(artifact + b"\n", master_seed="seed-alpha", authority=authority)
    noncanonical = artifact.replace(b"{", b"{ ", 1)
    with pytest.raises(S.ScheduleError):
        S.verify_exact_schedule_bytes(noncanonical, master_seed="seed-alpha", authority=authority)


def test_initial_state_bitflip_is_rejected_only_by_shared_verifier() -> None:
    authority = _authority()
    artifact = S.regenerate("seed-alpha", authority=authority)
    S.verify_exact_schedule_bytes(artifact, master_seed="seed-alpha", authority=authority)
    schedule = S.verify_schedule(artifact, master_seed="seed-alpha", authority=authority)
    expected_initial = schedule.cells[0].initial_state_sha256
    first_byte = bytes.fromhex(expected_initial[:2])[0] ^ 0x01
    flipped = f"{first_byte:02x}" + expected_initial[2:]
    assert int(expected_initial[:2], 16) ^ int(flipped[:2], 16) == 1
    assert expected_initial[2:] == flipped[2:]

    with pytest.raises(S.ScheduleError):
        S.verify_shared_search_space_and_initial_state(
            schedule,
            expected_search_space_sha256=S.search_space_digest(authority),
            expected_initial_state_sha256=flipped,
        )
    S.verify_exact_schedule_bytes(artifact, master_seed="seed-alpha", authority=authority)


def test_verify_schedule_rejects_external_initial_digest_bitflip() -> None:
    authority = _authority()
    artifact = S.regenerate("seed-alpha", authority=authority)
    expected_initial = S.initial_state_digest(authority)
    first_byte = bytes.fromhex(expected_initial[:2])[0] ^ 0x01
    flipped = f"{first_byte:02x}" + expected_initial[2:]
    assert int(expected_initial[:2], 16) ^ int(flipped[:2], 16) == 1
    assert expected_initial[2:] == flipped[2:]

    with pytest.raises(S.ScheduleError):
        S.verify_schedule(
            artifact,
            master_seed="seed-alpha",
            authority=authority,
            expected_initial_state_sha256=flipped,
        )
    assert S.verify_schedule(
        artifact,
        master_seed="seed-alpha",
        authority=authority,
    ).master_seed == "seed-alpha"


def _direct_schedule(
    *, cell_count: int = 6, duplicate_ordinal: bool = False,
) -> S.Schedule:
    search_digest = "a" * 64
    initial_digest = "b" * 64
    cells = []
    pairs = [
        (holdout, arm)
        for holdout in S.HOLDOUTS
        for arm in S.ARMS
    ][:cell_count]
    for ordinal, (holdout, arm) in enumerate(pairs):
        if duplicate_ordinal and ordinal == len(pairs) - 1:
            ordinal = 0
        cells.append(
            S.ScheduleCell(
                cell_ordinal=ordinal,
                holdout=holdout,
                arm=arm,
                search_space_sha256=search_digest,
                initial_state_sha256=initial_digest,
            )
        )
    return S.Schedule(
        schema_version=S.SCHEDULE_SCHEMA_VERSION,
        generator_version=S.GENERATOR_VERSION,
        master_seed="direct-shared-fixture",
        cells=tuple(cells),
    )


def test_shared_verifier_rejects_direct_schedule_with_five_cells() -> None:
    with pytest.raises(S.ScheduleError):
        S.verify_shared_search_space_and_initial_state(
            _direct_schedule(cell_count=5),
            expected_search_space_sha256="a" * 64,
            expected_initial_state_sha256="b" * 64,
        )


def test_shared_verifier_rejects_direct_schedule_with_duplicate_ordinals() -> None:
    with pytest.raises(S.ScheduleError):
        S.verify_shared_search_space_and_initial_state(
            _direct_schedule(duplicate_ordinal=True),
            expected_search_space_sha256="a" * 64,
            expected_initial_state_sha256="b" * 64,
        )


def test_shared_verifier_accepts_directly_constructed_valid_schedule() -> None:
    S.verify_shared_search_space_and_initial_state(
        _direct_schedule(),
        expected_search_space_sha256="a" * 64,
        expected_initial_state_sha256="b" * 64,
    )


def test_consume_rejects_seed_mismatch_and_accepts_matching_seed() -> None:
    """A seed that does not match the artifact makes consume fail.
    A matching seed returns the cell for the requested ordinal.
    """
    authority = _authority()
    artifact = S.regenerate("seed-alpha", authority=authority)

    with pytest.raises(S.ScheduleError):
        S.consume_schedule(
            artifact,
            master_seed="seed-beta",
            authority=authority,
            schedule_index=0,
        )

    cell = S.consume_schedule(
        artifact,
        master_seed="seed-alpha",
        authority=authority,
        schedule_index=0,
    )
    assert isinstance(cell, S.ScheduleCell)
    assert cell.cell_ordinal == 0


def test_consume_rejects_bad_indices_and_returns_the_verified_cell(tmp_path: Path) -> None:
    authority = _authority()
    artifact = S.regenerate("seed-alpha", authority=authority)
    path = tmp_path / "schedule.v1.json"
    path.write_bytes(artifact)
    assert S.load_schedule(path) == artifact

    cell = S.consume_schedule(
        artifact,
        master_seed="seed-alpha",
        authority=authority,
        schedule_index=0,
    )
    verified = S.verify_schedule(artifact, master_seed="seed-alpha", authority=authority)
    expected = next(item for item in verified.cells if item.cell_ordinal == 0)
    assert isinstance(cell, S.ScheduleCell)
    assert cell == expected

    for invalid in (-1, 6, True, 1.0, "0", None):
        with pytest.raises(S.ScheduleError):
            S.consume_schedule(
                artifact,
                master_seed="seed-alpha",
                authority=authority,
                schedule_index=invalid,
            )


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))
