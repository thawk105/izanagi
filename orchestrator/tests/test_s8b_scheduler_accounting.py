# -*- coding: utf-8 -*-
"""Unit tests for the fail-closed scheduler accounting collector."""
from __future__ import annotations

import hashlib
import inspect
import json
import os
from pathlib import Path
import sys

import pytest

from orchestrator.campaign import attempt_registry_core
from orchestrator.campaign import create_only_store
from orchestrator.campaign import s8b_attempt_profile as profile8b
from orchestrator.campaign import s8b_scheduler_accounting as accounting


_COLLECTED_AT = "2026-08-26T12:34:56Z"


def _bound(
    request_id: str = "123456.nqsv", *, target: str = "a" * 64,
) -> accounting.BoundSchedulerRequest:
    return accounting._bound_scheduler_request_for_test(request_id, target)


def _qstat_bytes(
    request_id: str = "123456.nqsv",
    *,
    execution_host: str = "bnode003",
    exit_code: str = "1100",
    extra: str = "",
) -> bytes:
    return (
        f"Request ID: {request_id}\n"
        "    Batch Job Number = 0\n"
        f"    Execution Host = {execution_host}\n"
        f"    Exit Code = {exit_code}\n"
        f"{extra}"
    ).encode("utf-8")


def _write_raw(tmp_path: Path, data: bytes, *, name: str = "qstat.raw") -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _collect(
    tmp_path: Path,
    raw: Path,
    *,
    bound: accounting.BoundSchedulerRequest | None = None,
    literal: str = accounting.AUTHORITY_POLICY_SHA256,
) -> accounting.SchedulerAccountingReceipt:
    claims = tmp_path / "claims"
    claims.mkdir(exist_ok=True)
    return accounting.collect_scheduler_accounting(
        bound or _bound(),
        raw,
        accounting.scheduler_accounting_receipt_root(claims),
        authority_policy_sha256_literal=literal,
    )


def _assert_error(
    expected_type: type[BaseException], expected_code: str, call,
) -> BaseException:
    with pytest.raises(expected_type) as caught:
        call()
    assert type(caught.value) is expected_type
    assert getattr(caught.value, "code", None) == expected_code
    return caught.value


def test_policy_is_canonical_empty_and_pins_the_observed_value_range() -> None:
    assert accounting.FAILURE_REASONS == frozenset({
        "node_failure",
        "scheduler_external_interruption",
    })
    assert dict(accounting.OBSERVED_EXIT_CODE_COUNTS) == {
        "(none)": 263,
        "1100": 4,
        "F": 3,
        "9": 2,
        "A": 1,
    }
    assert dict(accounting.FAILURE_REASON_RULES) == {}
    policy = accounting.authority_policy_document()
    assert policy["failure_reason_rules"] == []
    assert policy["observed_exit_code_counts"] == [
        ["(none)", 263], ["1100", 4], ["F", 3], ["9", 2], ["A", 1],
    ]
    assert accounting.AUTHORITY_POLICY_BYTES == (
        attempt_registry_core.canonical_json_bytes(policy)
    )
    assert accounting.AUTHORITY_POLICY_SHA256 == hashlib.sha256(
        accounting.AUTHORITY_POLICY_BYTES
    ).hexdigest()
    accounting.assert_authority_policy_literal(
        accounting.AUTHORITY_POLICY_SHA256
    )


def test_mut_t1668_authority_literal_requires_independent_pin(
    tmp_path: Path,
) -> None:
    raw = _write_raw(tmp_path, _qstat_bytes())
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "authority-policy-literal-mismatch",
        lambda: _collect(tmp_path, raw, literal="f" * 64),
    )


def test_bound_request_cannot_be_constructed_from_a_raw_string(
    tmp_path: Path,
) -> None:
    assert accounting.BoundSchedulerRequest.__dataclass_params__.frozen is True
    assert accounting.SchedulerAccountingReceipt.__dataclass_params__.frozen is True
    parameters = inspect.signature(
        accounting.collect_scheduler_accounting
    ).parameters
    assert tuple(parameters) == (
        "bound_request",
        "saved_qstat_output",
        "receipt_root",
        "authority_policy_sha256_literal",
    )
    assert parameters["authority_policy_sha256_literal"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    with pytest.raises(TypeError):
        accounting.BoundSchedulerRequest("123456.nqsv")
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "bound-start-event-kind",
        lambda: accounting.bind_scheduler_request_from_start_event({
            "event": "terminal",
            "scheduler_request_id": "123456.nqsv",
            "event_sha256": "a" * 64,
        }),
    )
    synthetic = accounting.bind_scheduler_request_from_start_event({
        "event": "start",
        "scheduler_request_id": "123456.nqsv",
        "event_sha256": "a" * 64,
    })
    assert type(synthetic) is accounting.SchedulerAccountingReceiptIdentity
    assert not isinstance(synthetic, accounting.BoundSchedulerRequest)
    raw = _write_raw(tmp_path, _qstat_bytes())
    shared = tmp_path / "synthetic-claims"
    shared.mkdir()
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "bound-request-type",
        lambda: accounting.collect_scheduler_accounting(
            synthetic,  # type: ignore[arg-type]
            raw,
            accounting.scheduler_accounting_receipt_root(shared),
            authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
        ),
    )


def test_valid_bound_qstat_is_structurally_accepted_then_unclassifiable(
    tmp_path: Path,
) -> None:
    raw = _write_raw(tmp_path, _qstat_bytes(request_id="123456.nqsv."))
    claims = tmp_path / "claims"
    claims.mkdir()
    _assert_error(
        accounting.SchedulerAccountingUnclassifiable,
        "failure-reason-unclassifiable",
        lambda: accounting.collect_scheduler_accounting(
            _bound("0:123456.nqsv"),
            raw,
            accounting.scheduler_accounting_receipt_root(claims),
            authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
        ),
    )
    assert list(claims.iterdir()) == []


def test_registry_binding_is_honestly_inert_without_a_start_schema_field(
    tmp_path: Path,
) -> None:
    binding = profile8b.S8BAttemptBinding(
        freeze_sha256="1" * 64,
        protocol_sha256="2" * 64,
        schedule_sha256="3" * 64,
    )
    profile = profile8b.make_s8b_domain_profile(
        max_consumptions_per_budget_key=2,
        recovery_authority_id="test-recovery-authority",
        recovery_authority_policy_sha256="4" * 64,
    )
    slot = profile8b.S8BAttemptSlot(
        freeze_holdout_key="holdout-a",
        configuration_id="configuration-a",
        repetition=0,
        attempt_ordinal=0,
        schedule_row_sha256="5" * 64,
    )
    rows = attempt_registry_core.create_attempt_registry_genesis(
        profile=profile,
        slots=[slot],
        binding=binding,
    )
    rows = attempt_registry_core.reserve_attempt_slot(
        rows,
        profile=profile,
        freeze_id=binding.freeze_sha256,
        slot_id=profile.slot_codec.slot_id(slot),
        binding=binding,
        run_start_receipt_sha256="6" * 64,
        process_identity={
            "pid": 123,
            "starttime": "test-starttime",
            "execution_uuid": "test-execution",
        },
        started_at="2026-08-26T00:00:00+00:00",
    )
    registry_path = tmp_path / "registry.jsonl"
    registry_path.write_bytes(b"".join(
        attempt_registry_core.canonical_json_bytes(row) + b"\n"
        for row in rows
    ))

    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "bound-request-id-unavailable",
        lambda: accounting.bind_scheduler_request_from_registry_start(
            registry_path,
            profile=profile,
            binding=binding,
            slot_id=profile.slot_codec.slot_id(slot),
        ),
    )


def test_receipt_issuance_requires_typed_shared_root_capability(
    tmp_path: Path,
) -> None:
    shared = tmp_path / "shared-admission"
    shared.mkdir()
    capability = accounting.scheduler_accounting_receipt_root(shared)
    assert capability.path == shared
    expected = accounting.scheduler_accounting_receipt_claim_path(
        shared,
        _bound(),
        authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
    )
    assert expected == create_only_store.identity_claim_path(
        shared,
        namespace="scheduler-accounting",
        identity=(
            accounting.AUTHORITY_ID,
            accounting.AUTHORITY_POLICY_SHA256,
            "a" * 64,
        ),
    )

    raw = _write_raw(tmp_path, _qstat_bytes())
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "receipt-root-capability",
        lambda: accounting.collect_scheduler_accounting(
            _bound(),
            raw,
            shared,  # type: ignore[arg-type]
            authority_policy_sha256_literal=(
                accounting.AUTHORITY_POLICY_SHA256
            ),
        ),
    )


@pytest.mark.parametrize(
    "exit_code", ["(none)", "1100", "F", "9", "A", "future-value"],
)
def test_no_observed_or_unknown_exit_code_is_accepted_as_a_reason(
    tmp_path: Path, exit_code: str,
) -> None:
    raw = _write_raw(tmp_path, _qstat_bytes(exit_code=exit_code))
    _assert_error(
        accounting.SchedulerAccountingUnclassifiable,
        "failure-reason-unclassifiable",
        lambda: _collect(tmp_path, raw),
    )
    assert list((tmp_path / "claims").iterdir()) == []


def test_mut_t1668_request_id_binding_rejects_a_different_job(
    tmp_path: Path,
) -> None:
    raw = _write_raw(tmp_path, _qstat_bytes(request_id="other-job.nqsv"))
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "request-id-mismatch",
        lambda: _collect(tmp_path, raw, bound=_bound("123456.nqsv")),
    )


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"Execution Host = bnode003\nExit Code = 1100\n", "request-id-count"),
        (
            _qstat_bytes() + b"Request ID: 123456.nqsv\n",
            "request-id-count",
        ),
        (
            b"Request ID: 123456.nqsv\nExit Code = 1100\n",
            "execution-host-count",
        ),
        (
            _qstat_bytes() + b"Execution Host = bnode004\n",
            "execution-host-count",
        ),
        (
            b"Request ID: 123456.nqsv\nExecution Host = bnode003\n",
            "exit-code-count",
        ),
        (_qstat_bytes() + b"Exit Code = F\n", "exit-code-count"),
    ],
)
def test_each_qstat_binding_field_has_an_exact_count(
    tmp_path: Path, data: bytes, code: str,
) -> None:
    raw = _write_raw(tmp_path, data)
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        code,
        lambda: _collect(tmp_path, raw),
    )


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (_qstat_bytes(request_id="r" * 257), "request-id-invalid"),
        (_qstat_bytes(execution_host="h" * 257), "execution-host-invalid"),
        (_qstat_bytes(exit_code="1" * 65), "exit-code-invalid"),
    ],
)
def test_qstat_scalar_bounds_have_distinct_codes(
    tmp_path: Path, data: bytes, code: str,
) -> None:
    raw = _write_raw(tmp_path, data)
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        code,
        lambda: _collect(tmp_path, raw),
    )


def test_saved_record_path_is_no_follow_regular_bounded_and_strict_utf8(
    tmp_path: Path,
) -> None:
    target = _write_raw(tmp_path, _qstat_bytes(), name="target.raw")
    symlink = tmp_path / "symlink.raw"
    os.symlink(target.name, symlink)
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "raw-path-no-follow",
        lambda: _collect(tmp_path, symlink),
    )
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "raw-path-not-regular",
        lambda: _collect(tmp_path, tmp_path),
    )

    invalid_utf8 = _write_raw(
        tmp_path, _qstat_bytes() + b"\xff", name="invalid-utf8.raw",
    )
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "raw-record-utf8",
        lambda: _collect(tmp_path, invalid_utf8),
    )

    oversized = _write_raw(
        tmp_path,
        b"x" * (accounting.RAW_SCHEDULER_ACCOUNTING_MAX_BYTES + 1),
        name="oversized.raw",
    )
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "raw-record-too-large",
        lambda: _collect(tmp_path, oversized),
    )


def test_complete_monotonic_scheduler_times_reach_only_unclassifiable(
    tmp_path: Path,
) -> None:
    times = (
        "Created Request Time: Wed Aug 26 12:00:00 2026\n"
        "Started Request Time: Wed Aug 26 12:00:01 2026\n"
        "Ended Request Time: Wed Aug 26 12:00:02 2026\n"
    )
    raw = _write_raw(tmp_path, _qstat_bytes(extra=times))
    _assert_error(
        accounting.SchedulerAccountingUnclassifiable,
        "failure-reason-unclassifiable",
        lambda: _collect(tmp_path, raw),
    )


@pytest.mark.parametrize(
    ("times", "code"),
    [
        (
            "Created Request Time: Wed Aug 26 12:00:00 2026\n",
            "time-field-partial",
        ),
        (
            "Created Request Time: Wed Aug 26 12:00:00 2026\n"
            "Created Request Time: Wed Aug 26 12:00:00 2026\n"
            "Started Request Time: Wed Aug 26 12:00:01 2026\n"
            "Ended Request Time: Wed Aug 26 12:00:02 2026\n",
            "time-field-count",
        ),
        (
            "Created Request Time: Wed Aug 26 12:00:02 2026\n"
            "Started Request Time: Wed Aug 26 12:00:01 2026\n"
            "Ended Request Time: Wed Aug 26 12:00:03 2026\n",
            "time-field-order",
        ),
        (
            "Created Request Time: Tue Aug 26 12:00:00 2026\n"
            "Started Request Time: Wed Aug 26 12:00:01 2026\n"
            "Ended Request Time: Wed Aug 26 12:00:02 2026\n",
            "time-field-weekday",
        ),
        (
            "Created Request Time: not-a-time\n"
            "Started Request Time: Wed Aug 26 12:00:01 2026\n"
            "Ended Request Time: Wed Aug 26 12:00:02 2026\n",
            "time-field-format",
        ),
    ],
)
def test_scheduler_time_consistency_gates_have_distinct_codes(
    tmp_path: Path, times: str, code: str,
) -> None:
    raw = _write_raw(tmp_path, _qstat_bytes(extra=times))
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        code,
        lambda: _collect(tmp_path, raw),
    )


def test_mut_t1668_receipt_identity_includes_target_start_event_hash(
    tmp_path: Path,
) -> None:
    first = accounting.scheduler_accounting_receipt_claim_path(
        tmp_path,
        _bound(target="a" * 64),
        authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
    )
    second = accounting.scheduler_accounting_receipt_claim_path(
        tmp_path,
        _bound(target="b" * 64),
        authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
    )
    assert first != second
    assert create_only_store.identity_claim_path(
        tmp_path,
        namespace="scheduler-accounting",
        identity=(
            accounting.AUTHORITY_ID,
            accounting.AUTHORITY_POLICY_SHA256,
            "a" * 64,
        ),
    ) == first


def test_create_only_store_returns_existing_bytes_without_overwrite(
    tmp_path: Path,
) -> None:
    path = create_only_store.identity_claim_path(
        tmp_path,
        namespace="test-claim",
        identity=("authority", "policy", "target"),
    )
    first = create_only_store.claim_bytes(path, b"first\n", max_bytes=100)
    second = create_only_store.claim_bytes(path, b"second\n", max_bytes=100)
    assert first.created is True
    assert first.data == b"first\n"
    assert second.created is False
    assert second.data == b"first\n"
    assert path.read_bytes() == b"first\n"


def test_create_only_store_rejects_a_symlink_claim(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"payload")
    claim = tmp_path / "claim.json"
    os.symlink(target.name, claim)
    with pytest.raises(create_only_store.CreateOnlyStoreError) as caught:
        create_only_store.read_claim_bytes(claim, max_bytes=100)
    assert type(caught.value) is create_only_store.CreateOnlyStoreError
    assert caught.value.code == "claim-no-follow"


def test_receipt_assembly_has_the_exact_core_keys_and_canonical_newline() -> None:
    raw_sha256 = hashlib.sha256(b"raw").hexdigest()
    data = accounting._assemble_receipt(
        bound_request=_bound(),
        raw_sha256=raw_sha256,
        failure_reason="node_failure",
        collected_at=_COLLECTED_AT,
    )
    document = json.loads(data)
    assert frozenset(document) == (
        attempt_registry_core._SCHEDULER_ACCOUNTING_RECEIPT_KEYS
    )
    assert data == attempt_registry_core.canonical_json_bytes(document) + b"\n"
    assert document["raw_scheduler_accounting_record_sha256"] == raw_sha256


def test_existing_receipt_validation_preserves_original_bytes_and_time() -> None:
    bound = _bound()
    raw_sha256 = hashlib.sha256(b"raw").hexdigest()
    data = accounting._assemble_receipt(
        bound_request=bound,
        raw_sha256=raw_sha256,
        failure_reason="node_failure",
        collected_at="2026-08-26T01:02:03Z",
    )
    result = accounting._validated_existing_receipt(
        data,
        bound_request=bound,
        raw_sha256=raw_sha256,
        expected_failure_reason="node_failure",
    )
    assert result.canonical_bytes is data
    assert json.loads(result.canonical_bytes)["collected_at"] == (
        "2026-08-26T01:02:03Z"
    )
    assert result.sha256 == hashlib.sha256(data).hexdigest()


def test_existing_identity_is_returned_before_collected_at_is_recomputed() -> None:
    source = inspect.getsource(accounting.collect_scheduler_accounting)
    existing_branch = source.index("if existing is not None:")
    collected_at_check = source.index("_collected_at_now()")
    assert existing_branch < collected_at_check
    branch = source[existing_branch:collected_at_check]
    assert "return _validated_existing_receipt(" in branch


def test_public_collector_create_exact_retry_and_raw_collision_with_test_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        accounting,
        "FAILURE_REASON_RULES",
        {"1100": "node_failure"},
    )
    monkeypatch.setattr(
        accounting, "_collected_at_now", lambda: "2026-08-26T01:02:03Z",
    )
    raw = _write_raw(tmp_path, _qstat_bytes(), name="first.raw")
    shared = tmp_path / "shared-admission"
    shared.mkdir()
    root = accounting.scheduler_accounting_receipt_root(shared)
    bound = _bound()

    first = accounting.collect_scheduler_accounting(
        bound,
        raw,
        root,
        authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
    )
    claim_path = accounting.scheduler_accounting_receipt_claim_path(
        shared,
        bound,
        authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
    )
    assert claim_path.read_bytes() == first.canonical_bytes
    assert json.loads(first.canonical_bytes)["collected_at"] == (
        "2026-08-26T01:02:03Z"
    )

    monkeypatch.setattr(
        accounting, "_collected_at_now", lambda: "2099-01-01T00:00:00Z",
    )
    exact_retry = accounting.collect_scheduler_accounting(
        bound,
        raw,
        root,
        authority_policy_sha256_literal=accounting.AUTHORITY_POLICY_SHA256,
    )
    assert exact_retry.canonical_bytes == first.canonical_bytes
    assert exact_retry.sha256 == first.sha256

    different_raw = _write_raw(
        tmp_path,
        _qstat_bytes(execution_host="bnode004"),
        name="different.raw",
    )
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "existing-receipt-raw-digest",
        lambda: accounting.collect_scheduler_accounting(
            bound,
            different_raw,
            root,
            authority_policy_sha256_literal=(
                accounting.AUTHORITY_POLICY_SHA256
            ),
        ),
    )
    assert claim_path.read_bytes() == first.canonical_bytes


def test_existing_receipt_rejects_nonexact_keys_with_its_own_code() -> None:
    bound = _bound()
    raw_sha256 = hashlib.sha256(b"raw").hexdigest()
    data = accounting._assemble_receipt(
        bound_request=bound,
        raw_sha256=raw_sha256,
        failure_reason="node_failure",
        collected_at=_COLLECTED_AT,
    )
    document = json.loads(data)
    document["unknown"] = "field"
    tampered = attempt_registry_core.canonical_json_bytes(document) + b"\n"
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "existing-receipt-keys",
        lambda: accounting._validated_existing_receipt(
            tampered,
            bound_request=bound,
            raw_sha256=raw_sha256,
            expected_failure_reason="node_failure",
        ),
    )


def test_existing_receipt_rejects_invalid_collected_at_with_its_own_code() -> None:
    bound = _bound()
    raw_sha256 = hashlib.sha256(b"raw").hexdigest()
    data = accounting._assemble_receipt(
        bound_request=bound,
        raw_sha256=raw_sha256,
        failure_reason="node_failure",
        collected_at=_COLLECTED_AT,
    )
    document = json.loads(data)
    document["collected_at"] = "not-a-time"
    data = attempt_registry_core.canonical_json_bytes(document) + b"\n"
    _assert_error(
        accounting.SchedulerAccountingCollectorError,
        "existing-receipt-collected-at",
        lambda: accounting._validated_existing_receipt(
            data,
            bound_request=bound,
            raw_sha256=raw_sha256,
            expected_failure_reason="node_failure",
        ),
    )


def test_collector_has_no_subprocess_or_forbidden_adapter_imports() -> None:
    source = inspect.getsource(accounting)
    assert "import subprocess" not in source
    assert "subprocess." not in source
    assert "s8b_holdout_admission" not in source
    assert "s8b_attempt_registry" not in source


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
