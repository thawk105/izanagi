"""Pure construction and validation of sealed 8b terminal evidence.

This module intentionally has no registry, launcher, campaign, admission, or
filesystem dependency.  It turns the three launcher carriers into canonical
bytes and derives the terminal row projection from those bytes.  The adapter
is responsible for adding the three durable phase digests and for issuing a
``ValidatedTerminalEvidence`` instance.

The E1 precedence follows the campaign's session classification, but its
accepted exception-name domain is the launcher's wider captured domain.  In
particular, accepting an ``OSError`` terminal does not claim that the campaign
would have emitted a corresponding session row; the campaign does not catch
that exception at the same surface.

``exec_failures`` is bound only by equality with the 30-key campaign record.
This evidence does not claim that it proves the execution outcome of each
individual repetition.  Structured per-repetition execution failures remain
outside this leaf's scope.
"""
from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any
from .attempt_registry_core import canonical_json_bytes
from . import s8b_floor_stats
__all__ = [
    'SealedTerminalEvidenceDraft',
    'TerminalEvidenceError',
    'TerminalEvidenceProjection',
    'ValidatedTerminalEvidence',
    'derive_terminal_projection',
    'require_sealed_terminal_evidence',
    'seal_terminal_evidence',
]
_SCHEMA_VERSION = 's8b-floor-terminal-evidence/v2'
_SHA256_LENGTH = 64
_E2_ENVIRONMENT = 'measurement_environment_conflict'
_E2_UNAVAILABLE = 'measurement_execution_unavailable'
_E2_INCOMPLETE = 'measurement_sample_incomplete'
_E2_DISPERSION = 'measurement_dispersion_exceeded'
_E2_REASONS = frozenset({
    _E2_ENVIRONMENT,
    _E2_UNAVAILABLE,
    _E2_INCOMPLETE,
    _E2_DISPERSION,
})
_CAMPAIGN_COMPETING = 'competing_process'
_CAMPAIGN_LAUNCH = 'launch_failure'
_CAMPAIGN_PARTIAL = 'nonfinite_or_partial_output'
_CAMPAIGN_PERFORMANCE = 'performance_anomaly'
_CAMPAIGN_REASONS = frozenset({
    _CAMPAIGN_COMPETING,
    _CAMPAIGN_LAUNCH,
    _CAMPAIGN_PARTIAL,
    _CAMPAIGN_PERFORMANCE,
})
_LAUNCHER_CAPTURED_EXCEPTION_NAMES = frozenset({
    'RuntimeError',
    'subprocess.TimeoutExpired',
    'OSError',
})
_PROBE_KEYS = frozenset({'rc', 'stdout', 'stderr', 'competing'})
_PROBE_SUMMARY_KEYS = frozenset({
    'competing',
    'rc_is_zero',
    'stdout_is_empty',
    'stderr_is_empty',
})
_FAILURE_KEYS = frozenset({'stage', 'exception_type', 'errno', 'message'})
_FAILURE_SUMMARY_KEYS = frozenset({'stage', 'exception_type', 'errno'})
_LAUNCH_FAILURE_KEYS = frozenset({'exception_type', 'errno', 'message'})
_PRE_OUTPUT_EVIDENCE_SCHEMA = 's8b-floor-pre-output-evidence/v2'
_PRE_OUTPUT_EVIDENCE_KEYS = frozenset({
    'schema_version',
    'probe_before',
    'probe_after',
    'launch_failures',
    'capture_failure',
})
_DRAFT_ATTEMPT_BINDING_KEYS = frozenset({
    'admission_claim_digest',
    'attempt_id',
    'campaign_run_id',
    'freeze_sha256',
    'manifest_sha256',
    'protocol_sha256',
    'run_relpath',
    'schedule_row_sha256',
    'schedule_sha256',
})
_PHASE_DIGEST_KEYS = frozenset({
    'classification_receipt_sha256',
    'classification_event_sha256',
    'observation_event_sha256',
})
_VALIDATED_ATTEMPT_BINDING_KEYS = _DRAFT_ATTEMPT_BINDING_KEYS | _PHASE_DIGEST_KEYS
_CAMPAIGN_RECORD_KEYS = frozenset({
    'attempt_id',
    'binary_sha256_at_measure',
    'cell_id',
    'configuration_id',
    'duration_s',
    'event',
    'excluded_reason',
    'exclusion_class',
    'exec_failures',
    'holdout_id',
    'kind',
    'notes',
    'probe_after',
    'probe_before',
    'records',
    'rep_integrity_failures',
    'rep_observations',
    'reps_expected',
    'retry',
    'retry_ordinal',
    'round',
    'run_cmd',
    'seq',
    'session_cv',
    'session_median',
    'threads',
    'throughputs',
    'trigger',
    'valid',
    'workload',
})
_AUTHORED_CAMPAIGN_IDENTITY_KEYS = frozenset({
    'attempt_id',
    'cell_id',
    'configuration_id',
    'holdout_id',
    'records',
    'retry_ordinal',
    'threads',
})
_UNAUTHORED_CAMPAIGN_IDENTITY_KEYS = frozenset({
    'event',
    'kind',
    'seq',
    'round',
    'trigger',
    'retry',
})
_CAMPAIGN_MEASUREMENT_KEYS = frozenset({
    'binary_sha256_at_measure',
    'duration_s',
    'excluded_reason',
    'exclusion_class',
    'exec_failures',
    'rep_integrity_failures',
    'reps_expected',
    'session_cv',
    'session_median',
    'throughputs',
    'valid',
})
_CAMPAIGN_PLAINTEXT_KEYS = _AUTHORED_CAMPAIGN_IDENTITY_KEYS | _CAMPAIGN_MEASUREMENT_KEYS
_CAMPAIGN_DIGEST_ONLY_KEYS = frozenset({
    'notes',
    'probe_after',
    'probe_before',
    'rep_observations',
    'run_cmd',
    'workload',
})
assert (
    _CAMPAIGN_PLAINTEXT_KEYS
    | _UNAUTHORED_CAMPAIGN_IDENTITY_KEYS
    | _CAMPAIGN_DIGEST_ONLY_KEYS
) == _CAMPAIGN_RECORD_KEYS
_OUTER_KEYS = frozenset({
    'attempt_binding',
    'campaign_record',
    'campaign_record_sha256',
    'exec_failures',
    'expected_use_perf',
    'failure',
    'failure_message_sha256',
    'finished_at',
    'launch_failures_count',
    'launch_failures_sha256',
    'mode',
    'nonfinite_count',
    'notes_sha256',
    'observation_sha256',
    'perf_preflight_receipt_sha256',
    'probe_after',
    'probe_after_sha256',
    'probe_before',
    'probe_before_sha256',
    'raw_output_sha256',
    'rep_integrity_failures',
    'rep_observations_sha256',
    'report_sha256',
    'reps_expected',
    'run_cmd_sha256',
    'schema_version',
    'session_cv_max',
    'throughputs',
    'unauthored_identity_sha256',
    'workload_sha256',
})

class TerminalEvidenceError(ValueError):
    """The terminal evidence contract rejected a value."""

def _fail(detail: str) -> None:
    raise TerminalEvidenceError(f'[s8b-terminal-evidence] {detail}')

def _canonical(value: object, *, label: str) -> bytes:
    try:
        return canonical_json_bytes(value)
    except Exception as exc:
        raise TerminalEvidenceError(f'[s8b-terminal-evidence] {label} is not canonical JSON data') from exc

def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def _digest_value(value: object, *, label: str) -> str:
    return _sha256_bytes(_canonical(value, label=label))

def _copy_bytes(value: bytes) -> bytes:
    """Return equal bytes without exposing the stored bytes object itself."""
    return bytes(bytearray(value))

def _canonical_copy(value: object, *, label: str) -> Any:
    """Detach a JSON value through its canonical bytes."""
    data = _canonical(value, label=label)
    return json.loads(data.decode('utf-8'))

def _exact_mapping(value: object, *, keys: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f'{label} is not an object')
    result = dict(value)
    if frozenset(result) != keys:
        _fail(f'{label} exact keys differ')
    if any((type(key) is not str for key in result)):
        _fail(f'{label} contains a non-string key')
    return result

def _text(value: object, *, label: str) -> str:
    if type(value) is not str or not value:
        _fail(f'{label} is not non-empty exact text')
    return value

def _nullable_text(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label=label)

def _sha256(value: object, *, label: str) -> str:
    value = _text(value, label=label)
    if len(value) != _SHA256_LENGTH:
        _fail(f'{label} is not a SHA-256 digest')
    try:
        int(value, 16)
    except ValueError:
        _fail(f'{label} is not a SHA-256 digest')
    if value != value.lower():
        _fail(f'{label} is not lowercase SHA-256')
    return value

def _nullable_sha256(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _sha256(value, label=label)

def _nonnegative_int(value: object, *, label: str) -> int:
    if type(value) is not int or value < 0:
        _fail(f'{label} is not a nonnegative exact integer')
    return value

def _positive_int(value: object, *, label: str) -> int:
    value = _nonnegative_int(value, label=label)
    if value == 0:
        _fail(f'{label} is not positive')
    return value

def _exact_bool(value: object, *, label: str) -> bool:
    if type(value) is not bool:
        _fail(f'{label} is not an exact boolean')
    return value

def _finite_float(value: object, *, label: str, nonnegative: bool=False) -> float:
    if type(value) is not float or not math.isfinite(value):
        _fail(f'{label} is not a finite exact float')
    if nonnegative and value < 0.0:
        _fail(f'{label} is negative')
    return value

def _nullable_finite_float(value: object, *, label: str) -> float | None:
    if value is None:
        return None
    return _finite_float(value, label=label)

def _member(value: object, name: str, *, label: str) -> object:
    try:
        return getattr(value, name)
    except AttributeError as exc:
        raise TerminalEvidenceError(f'[s8b-terminal-evidence] {label} has no {name}') from exc

def _probe(value: object, *, label: str) -> dict[str, object]:
    probe = _exact_mapping(value, keys=_PROBE_KEYS, label=label)
    if type(probe['rc']) is not int:
        _fail(f'{label}.rc is not an exact integer')
    if type(probe['stdout']) is not str or type(probe['stderr']) is not str:
        _fail(f'{label} output is not exact text')
    _exact_bool(probe['competing'], label=f'{label}.competing')
    _canonical(probe, label=label)
    return probe

def _probe_summary(value: Mapping[str, object]) -> dict[str, bool]:
    return {'competing': value['competing'] is True, 'rc_is_zero': value['rc'] == 0, 'stdout_is_empty': value['stdout'] == '', 'stderr_is_empty': value['stderr'] == ''}

def _checked_probe_summary(value: object, *, label: str) -> dict[str, bool]:
    summary = _exact_mapping(value, keys=_PROBE_SUMMARY_KEYS, label=label)
    for key in _PROBE_SUMMARY_KEYS:
        _exact_bool(summary[key], label=f'{label}.{key}')
    return summary

def _failure(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    failure = _exact_mapping(value, keys=_FAILURE_KEYS, label='failure')
    stage = _text(failure['stage'], label='failure.stage')
    if stage not in {'capture', 'open'}:
        _fail('failure.stage is outside the launcher stages')
    exception_type = _text(failure['exception_type'], label='failure.exception_type')
    if exception_type not in _LAUNCHER_CAPTURED_EXCEPTION_NAMES:
        _fail('failure.exception_type is outside the launcher captured set')
    error_number = failure['errno']
    if error_number is not None and type(error_number) is not int:
        _fail('failure.errno is not an exact integer or null')
    if type(failure['message']) is not str:
        _fail('failure.message is not exact text')
    _canonical(failure, label='failure')
    return failure

def _failure_summary(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    return {'stage': value['stage'], 'exception_type': value['exception_type'], 'errno': value['errno']}

def _checked_failure_summary(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    summary = _exact_mapping(value, keys=_FAILURE_SUMMARY_KEYS, label='failure')
    expanded = {**summary, 'message': ''}
    return _failure(expanded) and summary

def _launch_failure(value: object, *, position: int) -> dict[str, object]:
    label = f'launch_failures[{position}]'
    if isinstance(value, Mapping):
        failure = _exact_mapping(value, keys=_LAUNCH_FAILURE_KEYS, label=label)
    else:
        try:
            failure = {'exception_type': value.exception_type, 'errno': value.errno, 'message': value.message}
        except AttributeError as exc:
            raise TerminalEvidenceError(f'[s8b-terminal-evidence] {label} has an invalid shape') from exc
    _text(failure['exception_type'], label=f'{label}.exception_type')
    error_number = failure['errno']
    if error_number is not None and type(error_number) is not int:
        _fail(f'{label}.errno is not an exact integer or null')
    if type(failure['message']) is not str:
        _fail(f'{label}.message is not exact text')
    _canonical(failure, label=label)
    return failure

def _launch_failures(value: object) -> list[dict[str, object]]:
    if type(value) is not tuple:
        _fail('opened.launch_failures is not an exact tuple')
    return [_launch_failure(item, position=position) for (position, item) in enumerate(value)]

def _serialize_session_line(record: Mapping[str, Any]) -> bytes:
    try:
        return (json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise TerminalEvidenceError('[s8b-terminal-evidence] campaign_record is not serializable') from exc

def _strict_json_document(data: object) -> dict[str, Any]:
    if type(data) is not bytes:
        _fail('canonical bytes have an invalid type')

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for (key, value) in pairs:
            if key in result:
                _fail(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    try:
        decoded = data.decode('utf-8')
        value = json.loads(decoded, object_pairs_hook=pairs_hook, parse_constant=lambda token: _fail(f'nonfinite JSON token: {token}'))
    except TerminalEvidenceError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TerminalEvidenceError('[s8b-terminal-evidence] canonical bytes are not strict JSON') from exc
    if type(value) is not dict:
        _fail('terminal evidence is not an exact object')
    if _canonical(value, label='terminal evidence') != data:
        _fail('terminal evidence bytes are not canonical')
    return value

@dataclass(frozen=True, slots=True, init=False)
class _ReservationSourceSnapshot:
    """Private canonical reservation facts captured before launch effects."""
    _canonical_bytes: bytes = field(repr=False)
    _launcher_origin_capability: object | None = field(
        repr=False, compare=False,
    )

@dataclass(frozen=True, slots=True, init=False)
class _OpenedSourceSnapshot:
    """Private canonical opened facts never exposed to the terminal builder."""
    _reservation: _ReservationSourceSnapshot = field(repr=False)
    _canonical_bytes: bytes = field(repr=False)

@dataclass(frozen=True, slots=True, init=False)
class _TerminalSourceSnapshot:
    """One canonical read of the terminal builder's returned facts."""
    _canonical_bytes: bytes = field(repr=False)
    _campaign_record_bytes: bytes = field(repr=False)
    _raw_output_bytes: bytes = field(repr=False)

def _snapshot_reservation_source(
    reservation: object,
    *,
    launcher_origin_capability: object | None = None,
) -> _ReservationSourceSnapshot:
    """Read every reservation fact used by the sealer exactly once."""
    protocol_value = _member(reservation, 'protocol', label='reservation')
    if not isinstance(protocol_value, Mapping):
        _fail('reservation.protocol is not an object')
    protocol_snapshot = _canonical_copy(
        dict(protocol_value), label='reservation.protocol')
    receipt_value = _member(
        reservation, 'perf_preflight_receipt', label='reservation')
    receipt_snapshot = _nullable_mapping_snapshot(
        receipt_value, label='reservation.perf_preflight_receipt')
    workload_value = _member(reservation, 'workload', label='reservation')
    if not isinstance(workload_value, Mapping):
        _fail('reservation.workload is not an object')
    workload_snapshot = _canonical_copy(
        dict(workload_value), label='reservation.workload')
    slot_id = _member(reservation, 'slot_id', label='reservation')
    if type(slot_id) is not tuple or len(slot_id) not in {4, 5}:
        _fail('reservation.slot_id is not an exact slot identity')
    source = {
        'attempt_binding': _source_attempt_binding(reservation),
        'slot_id': list(slot_id),
        'protocol': protocol_snapshot,
        'mode': _member(reservation, 'mode', label='reservation'),
        'perf_preflight_receipt': receipt_snapshot,
        'attempt_id': _member(reservation, 'attempt_id', label='reservation'),
        'cell_id': _member(reservation, 'cell_id', label='reservation'),
        'records': _member(reservation, 'records', label='reservation'),
        'threads': _member(reservation, 'threads', label='reservation'),
        'workload': workload_snapshot,
    }
    canonical = _canonical(source, label='reservation source')
    snapshot = object.__new__(_ReservationSourceSnapshot)
    object.__setattr__(snapshot, '_canonical_bytes', canonical)
    object.__setattr__(
        snapshot, '_launcher_origin_capability', launcher_origin_capability,
    )
    return snapshot

def _nullable_mapping_snapshot(
    value: object, *, label: str,
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        _fail(f'{label} is not an object or null')
    result = _canonical_copy(dict(value), label=label)
    assert type(result) is dict
    return result

def _reservation_source_document(
    snapshot: _ReservationSourceSnapshot,
) -> dict[str, Any]:
    if type(snapshot) is not _ReservationSourceSnapshot:
        _fail('reservation source snapshot type differs')
    return _strict_json_document(snapshot._canonical_bytes)

def _pre_output_evidence_bytes(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    launch_failures: Sequence[Mapping[str, object]],
    failure: Mapping[str, object] | None,
) -> bytes:
    before = _probe(probe_before, label='pre-output probe_before')
    after = None if probe_after is None else _probe(
        probe_after, label='pre-output probe_after')
    failures = [
        _launch_failure(item, position=position)
        for (position, item) in enumerate(launch_failures)
    ]
    checked_failure = _failure(failure)
    payload = {
        'schema_version': _PRE_OUTPUT_EVIDENCE_SCHEMA,
        'probe_before': before,
        'probe_after': after,
        'launch_failures': failures,
        'capture_failure': (
            checked_failure
            if checked_failure is not None
            and checked_failure['stage'] == 'capture'
            else None
        ),
    }
    return _canonical(payload, label='pre-output evidence')

def _pre_output_evidence_sha256(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    launch_failures: Sequence[Mapping[str, object]],
    failure: Mapping[str, object] | None,
) -> str:
    return _sha256_bytes(_pre_output_evidence_bytes(
        probe_before=probe_before,
        probe_after=probe_after,
        launch_failures=launch_failures,
        failure=failure,
    ))

def _pre_output_evidence_document(data: bytes) -> dict[str, Any]:
    document = _strict_json_document(data)
    source = _exact_mapping(
        document,
        keys=_PRE_OUTPUT_EVIDENCE_KEYS,
        label='pre-output evidence',
    )
    if source['schema_version'] != _PRE_OUTPUT_EVIDENCE_SCHEMA:
        _fail('pre-output evidence schema_version differs')
    source['probe_before'] = _probe(
        source['probe_before'], label='pre-output probe_before')
    after = source['probe_after']
    source['probe_after'] = None if after is None else _probe(
        after, label='pre-output probe_after')
    failures = source['launch_failures']
    if type(failures) is not list:
        _fail('pre-output launch_failures is not an exact list')
    source['launch_failures'] = [
        _launch_failure(item, position=position)
        for (position, item) in enumerate(failures)
    ]
    capture_failure = _failure(source['capture_failure'])
    if capture_failure is not None and capture_failure['stage'] != 'capture':
        _fail('pre-output capture_failure stage differs')
    source['capture_failure'] = capture_failure
    return source

def _assert_external_evidence_matches_terminal(
    data: bytes,
    *,
    expected_digest: str,
    terminal_document: Mapping[str, Any],
) -> None:
    """Bind durable pre-output bytes to one canonical terminal document."""
    digest = _sha256(expected_digest, label='external_evidence_sha256')
    if _sha256_bytes(data) != digest:
        _fail('external evidence bytes digest differs')
    source = _pre_output_evidence_document(data)
    checked, _assessment = _validated_document(terminal_document)
    comparisons = {
        'probe_before_sha256': _digest_value(
            source['probe_before'], label='external probe_before'),
        'probe_after_sha256': (
            None
            if source['probe_after'] is None
            else _digest_value(
                source['probe_after'], label='external probe_after')
        ),
        'launch_failures_sha256': _digest_value(
            source['launch_failures'], label='external launch_failures'),
    }
    for name, derived in comparisons.items():
        if checked[name] != derived:
            _fail(f'external evidence differs from terminal: {name}')
    capture_failure = source['capture_failure']
    terminal_failure = checked['failure']
    if capture_failure is not None:
        if terminal_failure != _failure_summary(capture_failure):
            _fail('external capture failure differs from terminal summary')
        if checked['failure_message_sha256'] != _digest_value(
            capture_failure['message'], label='external failure message',
        ):
            _fail('external evidence differs from terminal: failure_message_sha256')
    elif terminal_failure is not None and terminal_failure['stage'] == 'capture':
        _fail('terminal capture failure is absent from external evidence')
    elif terminal_failure is None and checked['failure_message_sha256'] != (
        _digest_value(None, label='external null failure message')
    ):
        _fail('external evidence differs from terminal: failure_message_sha256')

def _snapshot_opened_source(
    reservation: _ReservationSourceSnapshot,
    opened: object,
) -> _OpenedSourceSnapshot:
    """Freeze all mutable launcher-owned evidence before builder effects."""
    if type(reservation) is not _ReservationSourceSnapshot:
        _fail('reservation source snapshot type differs')
    before = _probe(
        _member(opened, 'probe_before', label='opened'),
        label='probe_before',
    )
    after_value = _member(opened, 'probe_after', label='opened')
    after = None if after_value is None else _probe(
        after_value, label='probe_after')
    failure = _failure(_member(opened, 'failure', label='opened'))
    launch_failures = _launch_failures(
        _member(opened, 'launch_failures', label='opened'))
    observations_value = _member(
        opened, 'repetition_evidence', label='opened')
    if type(observations_value) is not tuple:
        _fail('opened.repetition_evidence is not an exact tuple')
    source_observations = [
        dict(item) if isinstance(item, Mapping) else item
        for item in observations_value
    ]
    source_reps_expected = _positive_int(
        _member(opened, 'reps_expected', label='opened'),
        label='opened.reps_expected',
    )
    source_expected_use_perf = _exact_bool(
        _member(opened, 'expected_use_perf', label='opened'),
        label='opened.expected_use_perf',
    )
    (
        source_errors,
        source_rep_integrity_failures,
        source_exec_failures,
        source_qualified_throughputs,
    ) = s8b_floor_stats._derive_rep_integrity(
        source_observations,
        reps=source_reps_expected,
        expected_use_perf=source_expected_use_perf,
    )
    if failure is None and before['competing'] is False and source_errors:
        _fail(f'opened repetition evidence is invalid: {source_errors[0]}')
    observations = _canonical_copy(
        source_observations, label='opened.repetition_evidence')
    if type(observations) is not list:
        _fail('opened repetition snapshot is not an exact list')
    measurement = _member(opened, 'measurement', label='opened')
    measurement_throughputs: list[object] | None = None
    if measurement is not None:
        try:
            measurement_throughputs = list(measurement.throughputs)
        except (AttributeError, TypeError) as exc:
            raise TerminalEvidenceError(
                '[s8b-terminal-evidence] opened measurement has no '
                'throughput sequence'
            ) from exc
    external_evidence_bytes = _pre_output_evidence_bytes(
        probe_before=before,
        probe_after=after,
        launch_failures=launch_failures,
        failure=failure,
    )
    computed_external = _sha256_bytes(external_evidence_bytes)
    supplied_external = _sha256(
        _member(opened, 'external_evidence_sha256', label='opened'),
        label='opened.external_evidence_sha256',
    )
    if supplied_external != computed_external:
        _fail('opened external evidence digest differs from source facts')
    source = {
        'measurement_throughputs': measurement_throughputs,
        'failure': failure,
        'probe_before': before,
        'probe_after': after,
        'launch_failures': launch_failures,
        'pre_observation_failure_reason': _member(
            opened, 'pre_observation_failure_reason', label='opened'),
        'external_evidence_sha256': computed_external,
        'repetition_evidence': observations,
        'source_rep_integrity_failures': source_rep_integrity_failures,
        'source_exec_failures': source_exec_failures,
        'source_qualified_throughputs': list(source_qualified_throughputs),
        'expected_use_perf': source_expected_use_perf,
        'reps_expected': source_reps_expected,
    }
    canonical = _canonical(source, label='opened source')
    snapshot = object.__new__(_OpenedSourceSnapshot)
    object.__setattr__(snapshot, '_reservation', reservation)
    object.__setattr__(snapshot, '_canonical_bytes', canonical)
    return snapshot

def _opened_source_document(snapshot: _OpenedSourceSnapshot) -> dict[str, Any]:
    if type(snapshot) is not _OpenedSourceSnapshot:
        _fail('opened source snapshot type differs')
    return _strict_json_document(snapshot._canonical_bytes)

def _snapshot_terminal_source(terminal: object) -> _TerminalSourceSnapshot:
    """Strictly snapshot a builder result, including one campaign-record read."""
    record = _source_campaign_record(
        _member(terminal, 'campaign_record', label='terminal'))
    _campaign_plaintext({
        name: record[name] for name in _CAMPAIGN_PLAINTEXT_KEYS
    })
    record_bytes = _canonical(record, label='campaign_record source')
    raw_output = _member(terminal, 'raw_output_bytes', label='terminal')
    if type(raw_output) is not bytes or not raw_output:
        _fail('terminal.raw_output_bytes is not non-empty exact bytes')
    source = {
        'terminal_status': _member(
            terminal, 'terminal_status', label='terminal'),
        'report_sha256': _member(
            terminal, 'report_sha256', label='terminal'),
        'observation_sha256': _member(
            terminal, 'observation_sha256', label='terminal'),
        'primary_value': _member(
            terminal, 'primary_value', label='terminal'),
        'finished_at': _member(terminal, 'finished_at', label='terminal'),
    }
    snapshot = object.__new__(_TerminalSourceSnapshot)
    object.__setattr__(
        snapshot, '_canonical_bytes', _canonical(source, label='terminal source'))
    object.__setattr__(snapshot, '_campaign_record_bytes', record_bytes)
    object.__setattr__(snapshot, '_raw_output_bytes', _copy_bytes(raw_output))
    return snapshot

def _terminal_source_document(
    snapshot: _TerminalSourceSnapshot,
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    if type(snapshot) is not _TerminalSourceSnapshot:
        _fail('terminal source snapshot type differs')
    return (
        _strict_json_document(snapshot._canonical_bytes),
        _strict_json_document(snapshot._campaign_record_bytes),
        _copy_bytes(snapshot._raw_output_bytes),
    )

def _attempt_binding(value: object, *, expected_keys: frozenset[str] | None=None) -> dict[str, object]:
    if not isinstance(value, Mapping):
        _fail('attempt_binding is not an object')
    keys = frozenset(value)
    allowed = {_DRAFT_ATTEMPT_BINDING_KEYS, _VALIDATED_ATTEMPT_BINDING_KEYS}
    if expected_keys is not None:
        allowed = {expected_keys}
    if keys not in allowed:
        _fail('attempt_binding exact keys differ')
    binding = dict(value)
    digest_keys = {'admission_claim_digest', 'freeze_sha256', 'manifest_sha256', 'protocol_sha256', 'schedule_row_sha256', 'schedule_sha256'} | _PHASE_DIGEST_KEYS
    for key in digest_keys & keys:
        _sha256(binding[key], label=f'attempt_binding.{key}')
    for key in {'attempt_id', 'campaign_run_id', 'run_relpath'}:
        _text(binding[key], label=f'attempt_binding.{key}')
    return binding

def _campaign_plaintext(value: object) -> dict[str, object]:
    record = _exact_mapping(value, keys=_CAMPAIGN_PLAINTEXT_KEYS, label='campaign_record')
    _text(record['attempt_id'], label='campaign_record.attempt_id')
    _text(record['cell_id'], label='campaign_record.cell_id')
    _text(record['configuration_id'], label='campaign_record.configuration_id')
    _text(record['holdout_id'], label='campaign_record.holdout_id')
    _positive_int(record['records'], label='campaign_record.records')
    retry_ordinal = record['retry_ordinal']
    if retry_ordinal is not None:
        _nonnegative_int(
            retry_ordinal, label='campaign_record.retry_ordinal')
    _positive_int(record['threads'], label='campaign_record.threads')
    _sha256(record['binary_sha256_at_measure'], label='campaign_record.binary_sha256_at_measure')
    _finite_float(record['duration_s'], label='campaign_record.duration_s', nonnegative=True)
    reason = _nullable_text(record['excluded_reason'], label='campaign_record.excluded_reason')
    if reason not in _CAMPAIGN_REASONS | {None}:
        _fail('campaign_record.excluded_reason is outside the closed vocabulary')
    exclusion = _nullable_text(record['exclusion_class'], label='campaign_record.exclusion_class')
    if exclusion not in _CAMPAIGN_REASONS | {None, s8b_floor_stats.REP_INTEGRITY_EXCLUSION_CLASS}:
        _fail('campaign_record.exclusion_class is outside the closed vocabulary')
    _nonnegative_int(record['exec_failures'], label='campaign_record.exec_failures')
    rep_integrity = record['rep_integrity_failures']
    if rep_integrity is not None:
        _nonnegative_int(rep_integrity, label='campaign_record.rep_integrity_failures')
    _positive_int(record['reps_expected'], label='campaign_record.reps_expected')
    session_cv = record['session_cv']
    if session_cv is not None:
        _finite_float(session_cv, label='campaign_record.session_cv')
    _nullable_finite_float(record['session_median'], label='campaign_record.session_median')
    _exact_bool(record['valid'], label='campaign_record.valid')
    throughputs = record['throughputs']
    if type(throughputs) is not list:
        _fail('campaign_record.throughputs is not an exact list')
    for (position, item) in enumerate(throughputs):
        _finite_float(item, label=f'campaign_record.throughputs[{position}]')
    return record

def _finite_throughputs(value: object) -> tuple[float, ...]:
    if type(value) is not list:
        _fail('throughputs is not an exact list')
    result = []
    for (position, item) in enumerate(value):
        result.append(_finite_float(item, label=f'throughputs[{position}]'))
    return tuple(result)

def _assess_finite_throughputs(throughputs: Sequence[float], *, reps_expected: int, session_cv_max: str) -> s8b_floor_stats.SessionAssessment:
    """Assess finite values against the original, unshortened rep count."""
    try:
        return s8b_floor_stats.assess_session(throughputs, reps=reps_expected, session_cv_max=session_cv_max)
    except s8b_floor_stats.FloorStatsError as exc:
        raise TerminalEvidenceError(f'[s8b-terminal-evidence] session assessment failed: {exc}') from exc

def _derive_classification_echo(*, probe_before: Mapping[str, bool], probe_after: Mapping[str, bool] | None, failure: Mapping[str, object] | None, launch_failures_count: int) -> str | None:
    if probe_before['competing'] or (probe_after is not None and probe_after['competing']):
        return _CAMPAIGN_COMPETING
    if launch_failures_count > 0 or (failure is not None and failure['stage'] == 'capture'):
        return _CAMPAIGN_LAUNCH
    return None

def _derive_e1(*, probe_before: Mapping[str, bool], probe_after: Mapping[str, bool] | None, failure: Mapping[str, object] | None, exec_failures: int, reps_expected: int, rep_integrity_failures: int | None, assessment: s8b_floor_stats.SessionAssessment) -> tuple[str | None, str | None, str, float | None]:
    """Run the six ordered E1 branches without an observed fallback table."""
    if probe_before['competing'] or (probe_after is not None and probe_after['competing']):
        retry_reason = _E2_ENVIRONMENT
        campaign_reason = _CAMPAIGN_COMPETING
    elif failure is not None or exec_failures >= reps_expected:
        retry_reason = _E2_UNAVAILABLE
        campaign_reason = _CAMPAIGN_LAUNCH
    elif 0 < exec_failures < reps_expected and assessment.required_reason is None:
        retry_reason = _E2_UNAVAILABLE
        campaign_reason = _CAMPAIGN_LAUNCH
    elif rep_integrity_failures is not None and rep_integrity_failures > 0 and (assessment.required_reason == _CAMPAIGN_PARTIAL):
        retry_reason = _E2_INCOMPLETE
        campaign_reason = _CAMPAIGN_PARTIAL
    elif assessment.required_reason == _CAMPAIGN_PARTIAL:
        retry_reason = _E2_INCOMPLETE
        campaign_reason = _CAMPAIGN_PARTIAL
    elif assessment.required_reason == _CAMPAIGN_PERFORMANCE:
        retry_reason = _E2_DISPERSION
        campaign_reason = _CAMPAIGN_PERFORMANCE
    else:
        retry_reason = None
        campaign_reason = None
    if retry_reason is None:
        terminal_status = 'observed'
        primary_value = None if assessment.median is None else float(assessment.median)
    else:
        terminal_status = 'retryable-failure'
        primary_value = None
    return (retry_reason, campaign_reason, terminal_status, primary_value)

def _assert_mutual_consistency(*, probe_before: Mapping[str, bool], probe_after: Mapping[str, bool] | None, failure: Mapping[str, object] | None, launch_failures_count: int, throughputs: Sequence[float], nonfinite_count: int, exec_failures: int, reps_expected: int, rep_integrity_failures: int | None, rep_observations_sha256: str, sink_length: int | None=None, measurement_present: bool | None=None) -> None:
    empty_observations_sha256 = _digest_value([], label='empty observations')
    skipped_signature = failure is None and launch_failures_count == 0 and (len(throughputs) == 0) and (nonfinite_count == 0) and (rep_observations_sha256 == empty_observations_sha256) and (rep_integrity_failures is None) and (exec_failures == 0)
    no_after = probe_after is None
    before_competing = probe_before['competing']
    if not no_after == before_competing == skipped_signature:
        _fail('probe skip equivalence is inconsistent')
    opened = failure is None and probe_after is not None
    if opened:
        if sink_length is not None and sink_length != reps_expected:
            _fail('opened repetition sink length differs from reps_expected')
        if rep_integrity_failures is None:
            _fail('opened evidence has null rep_integrity_failures')
        if exec_failures > rep_integrity_failures:
            _fail('execution-failure repetitions exceed integrity failures')
        other_integrity_failures = rep_integrity_failures - exec_failures
        classified_repetitions = (
            len(throughputs)
            + nonfinite_count
            + exec_failures
            + other_integrity_failures
        )
        if classified_repetitions != reps_expected:
            _fail(
                'finite/nonfinite/execution-failure/other-integrity '
                'repetition sum differs from reps_expected'
            )
    if failure is not None:
        if failure['stage'] == 'capture' and launch_failures_count != 0:
            _fail('capture failure has nonzero launch_failures_count')
        if throughputs or nonfinite_count != 0:
            _fail('failure evidence contains measurement values')
        if exec_failures != reps_expected:
            _fail('failure evidence is not an unavailable projection')
        if rep_integrity_failures is not None:
            _fail('failure evidence has rep_integrity_failures')
        if rep_observations_sha256 != empty_observations_sha256:
            _fail('failure evidence contains repetition observations')
        if measurement_present is True:
            _fail('failure evidence contains an opened measurement')
    if launch_failures_count > 0 and exec_failures == 0:
        _fail('launch failures contradict zero exec_failures')

@dataclass(frozen=True, slots=True)
class TerminalEvidenceProjection:
    terminal_status: str
    failure_reason: str | None
    measurement_retry_reason: str | None
    campaign_excluded_reason: str | None
    primary_value: float | None
    raw_output_sha256: str
    report_sha256: str
    observation_sha256: str | None
    finished_at: str

@dataclass(frozen=True, slots=True, init=False)
class SealedTerminalEvidenceDraft:
    """Canonical draft whose attempt binding has exactly nine keys."""
    _canonical_bytes: bytes = field(repr=False)
    _external_evidence_sha256: str = field(repr=False, compare=False)
    _launcher_origin_capability: object | None = field(
        repr=False, compare=False,
    )

    @property
    def canonical_bytes(self) -> bytes:
        return _copy_bytes(self._canonical_bytes)

    @property
    def document(self) -> Mapping[str, Any]:
        document = _strict_json_document(self._canonical_bytes)
        _validated_document(document, expected_binding_keys=_DRAFT_ATTEMPT_BINDING_KEYS)
        return document

    @property
    def projection(self) -> TerminalEvidenceProjection:
        return derive_terminal_projection(self.document)

@dataclass(frozen=True, slots=True, init=False)
class ValidatedTerminalEvidence:
    """Adapter-issued canonical evidence with the exact 12-key binding."""
    _canonical_bytes: bytes = field(repr=False)
    _issuer_token: object = field(repr=False, compare=False)

    @property
    def canonical_bytes(self) -> bytes:
        return _copy_bytes(self._canonical_bytes)

    @property
    def document(self) -> Mapping[str, Any]:
        document = _strict_json_document(self._canonical_bytes)
        _validated_document(document, expected_binding_keys=_VALIDATED_ATTEMPT_BINDING_KEYS)
        return document

    @property
    def projection(self) -> TerminalEvidenceProjection:
        return derive_terminal_projection(self.document)

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self._canonical_bytes)

def _validated_document(value: object, *, expected_binding_keys: frozenset[str] | None=None) -> tuple[dict[str, Any], s8b_floor_stats.SessionAssessment]:
    document = _exact_mapping(value, keys=_OUTER_KEYS, label='terminal evidence')
    if document['schema_version'] != _SCHEMA_VERSION:
        _fail('schema_version differs')
    _attempt_binding(document['attempt_binding'], expected_keys=expected_binding_keys)
    mode = _text(document['mode'], label='mode')
    if mode not in {'pilot', 'official'}:
        _fail('mode is outside the closed vocabulary')
    _exact_bool(document['expected_use_perf'], label='expected_use_perf')
    _text(document['finished_at'], label='finished_at')
    session_cv_max = _text(document['session_cv_max'], label='session_cv_max')
    reps_expected = _positive_int(document['reps_expected'], label='reps_expected')
    throughputs = _finite_throughputs(document['throughputs'])
    nonfinite_count = _nonnegative_int(document['nonfinite_count'], label='nonfinite_count')
    exec_failures = _nonnegative_int(document['exec_failures'], label='exec_failures')
    rep_integrity = document['rep_integrity_failures']
    if rep_integrity is not None:
        rep_integrity = _nonnegative_int(rep_integrity, label='rep_integrity_failures')
    launch_count = _nonnegative_int(document['launch_failures_count'], label='launch_failures_count')
    failure = _checked_failure_summary(document['failure'])
    before = _checked_probe_summary(document['probe_before'], label='probe_before')
    after_value = document['probe_after']
    after = None if after_value is None else _checked_probe_summary(after_value, label='probe_after')
    campaign = _campaign_plaintext(document['campaign_record'])
    digest_fields = {'campaign_record_sha256', 'failure_message_sha256', 'launch_failures_sha256', 'notes_sha256', 'perf_preflight_receipt_sha256', 'probe_before_sha256', 'raw_output_sha256', 'rep_observations_sha256', 'report_sha256', 'run_cmd_sha256', 'unauthored_identity_sha256', 'workload_sha256'}
    for name in digest_fields:
        _sha256(document[name], label=name)
    _nullable_sha256(document['probe_after_sha256'], label='probe_after_sha256')
    _nullable_sha256(document['observation_sha256'], label='observation_sha256')
    if (after is None) != (document['probe_after_sha256'] is None):
        _fail('probe_after summary/digest nullability differs')
    if (failure is None) != (document['failure_message_sha256'] == _digest_value(None, label='null failure message')):
        _fail('failure summary/message digest nullability differs')
    if campaign['throughputs'] != list(throughputs):
        _fail('campaign_record.throughputs differs from finite throughputs')
    comparisons = {'reps_expected': reps_expected, 'exec_failures': exec_failures, 'rep_integrity_failures': rep_integrity}
    for (name, expected) in comparisons.items():
        if campaign[name] != expected:
            _fail(f'campaign_record.{name} differs from evidence')
    _assert_mutual_consistency(probe_before=before, probe_after=after, failure=failure, launch_failures_count=launch_count, throughputs=throughputs, nonfinite_count=nonfinite_count, exec_failures=exec_failures, reps_expected=reps_expected, rep_integrity_failures=rep_integrity, rep_observations_sha256=document['rep_observations_sha256'])
    assessment = _assess_finite_throughputs(throughputs, reps_expected=reps_expected, session_cv_max=session_cv_max)
    (retry_reason, campaign_reason, status, primary) = _derive_e1(probe_before=before, probe_after=after, failure=failure, exec_failures=exec_failures, reps_expected=reps_expected, rep_integrity_failures=rep_integrity, assessment=assessment)
    if campaign['excluded_reason'] != campaign_reason:
        _fail('campaign_record.excluded_reason differs from E1')
    expected_cv = assessment.cv
    if campaign['session_cv'] != expected_cv:
        _fail('campaign_record.session_cv differs from assessment')
    expected_median = primary if status == 'observed' else None
    if campaign['session_median'] != expected_median:
        _fail('campaign_record.session_median differs from assessment')
    if campaign['valid'] is not (status == 'observed'):
        _fail('campaign_record.valid differs from E1')
    expected_exclusion = campaign_reason if campaign_reason in {_CAMPAIGN_COMPETING, _CAMPAIGN_LAUNCH} else s8b_floor_stats.REP_INTEGRITY_EXCLUSION_CLASS if rep_integrity is not None and rep_integrity > 0 else campaign_reason
    if campaign['exclusion_class'] != expected_exclusion:
        _fail('campaign_record.exclusion_class differs from E1')
    if document['report_sha256'] != document['raw_output_sha256']:
        _fail('report_sha256 differs from raw_output_sha256')
    expected_observation = document['rep_observations_sha256'] if status == 'observed' else None
    if document['observation_sha256'] != expected_observation:
        _fail('observation_sha256 differs from E1')
    if retry_reason not in _E2_REASONS | {None}:
        _fail('internal E1 reason is outside the closed vocabulary')
    return (document, assessment)

def derive_terminal_projection(document: Mapping[str, Any]) -> TerminalEvidenceProjection:
    """Re-derive the row projection from a draft or validated document."""
    (checked, assessment) = _validated_document(document)
    before = checked['probe_before']
    after = checked['probe_after']
    failure = checked['failure']
    (retry_reason, campaign_reason, status, primary) = _derive_e1(probe_before=before, probe_after=after, failure=failure, exec_failures=checked['exec_failures'], reps_expected=checked['reps_expected'], rep_integrity_failures=checked['rep_integrity_failures'], assessment=assessment)
    failure_reason = _derive_classification_echo(probe_before=before, probe_after=after, failure=failure, launch_failures_count=checked['launch_failures_count'])
    return TerminalEvidenceProjection(terminal_status=status, failure_reason=failure_reason, measurement_retry_reason=retry_reason, campaign_excluded_reason=campaign_reason, primary_value=primary, raw_output_sha256=checked['raw_output_sha256'], report_sha256=checked['report_sha256'], observation_sha256=checked['observation_sha256'], finished_at=checked['finished_at'])

def _source_campaign_record(value: object) -> dict[str, Any]:
    return _exact_mapping(
        value, keys=_CAMPAIGN_RECORD_KEYS, label='campaign_record source')

def _source_throughputs(opened: object, *, reps_expected: int, expected_use_perf: bool, failure: Mapping[str, object] | None, pre_probe_competing: bool) -> tuple[list[dict[str, object]], tuple[float, ...], int, int | None, int, bool]:
    observations_value = _member(opened, 'repetition_evidence', label='opened')
    if type(observations_value) is not tuple:
        _fail('opened.repetition_evidence is not an exact tuple')
    observations = [dict(item) if isinstance(item, Mapping) else item for item in observations_value]
    measurement = _member(opened, 'measurement', label='opened')
    if failure is not None or pre_probe_competing:
        if measurement is not None or observations:
            _fail('unopened evidence contains measurement data')
        return ([], (), 0, None, 0, False)
    if measurement is None:
        _fail('opened evidence has no measurement')
    try:
        source_throughputs = list(measurement.throughputs)
    except (AttributeError, TypeError) as exc:
        raise TerminalEvidenceError('[s8b-terminal-evidence] opened measurement has no throughput sequence') from exc
    raw_observed = [item.get('throughput') for item in observations if isinstance(item, Mapping) and item.get('throughput') is not None]
    if source_throughputs != raw_observed:
        _fail('measurement throughputs differ from the private repetition sink')
    (errors, integrity_failures, exec_failures, qualified) = \
        s8b_floor_stats._derive_rep_integrity(
            observations, reps=reps_expected,
            expected_use_perf=expected_use_perf,
        )
    if errors:
        _fail(f'opened repetition evidence is invalid: {errors[0]}')
    finite: list[float] = []
    nonfinite_count = 0
    for (position, value) in enumerate(qualified):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _fail(f'qualified throughput {position} is not numeric')
        if math.isfinite(value):
            finite.append(float(value))
        else:
            nonfinite_count += 1
    return (
        observations, tuple(finite), nonfinite_count,
        integrity_failures, exec_failures, True,
    )

def _source_throughputs_from_snapshot(
    opened: Mapping[str, Any],
    *,
    reps_expected: int,
    expected_use_perf: bool,
    failure: Mapping[str, object] | None,
    pre_probe_competing: bool,
) -> tuple[list[dict[str, object]], tuple[float, ...], int, int | None, int, bool]:
    observations = opened['repetition_evidence']
    if type(observations) is not list:
        _fail('opened repetition snapshot is not an exact list')
    measurement_throughputs = opened['measurement_throughputs']
    if failure is not None or pre_probe_competing:
        if measurement_throughputs is not None or observations:
            _fail('unopened evidence contains measurement data')
        return ([], (), 0, None, 0, False)
    if type(measurement_throughputs) is not list:
        _fail('opened evidence has no measurement')
    raw_observed = [
        item.get('throughput')
        for item in observations
        if isinstance(item, Mapping) and item.get('throughput') is not None
    ]
    if measurement_throughputs != raw_observed:
        _fail('measurement throughputs differ from the private repetition sink')
    integrity_failures = _nonnegative_int(
        opened['source_rep_integrity_failures'],
        label='opened.source_rep_integrity_failures',
    )
    exec_failures = _nonnegative_int(
        opened['source_exec_failures'],
        label='opened.source_exec_failures',
    )
    qualified = opened['source_qualified_throughputs']
    if type(qualified) is not list:
        _fail('opened source_qualified_throughputs is not an exact list')
    finite: list[float] = []
    nonfinite_count = 0
    for (position, value) in enumerate(qualified):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _fail(f'qualified throughput {position} is not numeric')
        if math.isfinite(value):
            finite.append(float(value))
        else:
            nonfinite_count += 1
    return (
        observations,
        tuple(finite),
        nonfinite_count,
        integrity_failures,
        exec_failures,
        True,
    )

def _source_attempt_binding(reservation: object) -> dict[str, object]:
    binding = _member(reservation, 'binding', label='reservation')
    result = {
        'admission_claim_digest': _member(
            reservation, 'admission_claim_digest', label='reservation'),
        'attempt_id': _member(reservation, 'attempt_id', label='reservation'),
        'campaign_run_id': _member(
            reservation, 'campaign_run_id', label='reservation'),
        'freeze_sha256': _member(binding, 'freeze_sha256', label='binding'),
        'manifest_sha256': _member(
            reservation, 'manifest_sha256', label='reservation'),
        'protocol_sha256': _member(binding, 'protocol_sha256', label='binding'),
        'run_relpath': _member(reservation, 'run_relpath', label='reservation'),
        'schedule_row_sha256': _member(
            reservation, 'schedule_row_sha256', label='reservation'),
        'schedule_sha256': _member(binding, 'schedule_sha256', label='binding'),
    }
    return _attempt_binding(result, expected_keys=_DRAFT_ATTEMPT_BINDING_KEYS)

def _assert_authoritative_identity(
    reservation: Mapping[str, Any], record: Mapping[str, Any],
) -> None:
    slot_id = reservation['slot_id']
    if type(slot_id) is not list or len(slot_id) != 5:
        _fail('reservation.slot_id is not an exact v2 slot identity')
    measurement_ordinal = _nonnegative_int(
        slot_id[3], label='reservation.slot_id[3]')
    expected = {
        'attempt_id': reservation['attempt_id'],
        'cell_id': reservation['cell_id'],
        'configuration_id': slot_id[1],
        'holdout_id': slot_id[0],
        'records': reservation['records'],
        'retry_ordinal': (
            None if measurement_ordinal == 0 else measurement_ordinal),
        'threads': reservation['threads'],
    }
    for (name, value) in expected.items():
        if record[name] != value:
            _fail(f'campaign_record.{name} differs from durable identity')
    workload = reservation['workload']
    if _canonical(record['workload'], label='campaign workload') != _canonical(workload, label='durable workload'):
        _fail('campaign_record.workload differs from durable identity')

def seal_terminal_evidence(reservation: object, opened: object, terminal: object) -> SealedTerminalEvidenceDraft:
    """Seal private snapshots into a nine-binding-key canonical draft.

    The three-argument public surface remains available for direct leaf use.
    The certified launcher passes private source snapshots in ``opened`` and
    ``terminal`` so this function never rereads caller-owned reservation data
    after the terminal builder has run.
    """
    if type(opened) is _OpenedSourceSnapshot:
        opened_snapshot = opened
        if type(terminal) is not _TerminalSourceSnapshot:
            _fail('terminal source snapshot type differs')
        terminal_snapshot = terminal
    else:
        reservation_snapshot = _snapshot_reservation_source(reservation)
        opened_snapshot = _snapshot_opened_source(
            reservation_snapshot, opened)
        terminal_snapshot = _snapshot_terminal_source(terminal)
    reservation_source = _reservation_source_document(
        opened_snapshot._reservation)
    opened_source = _opened_source_document(opened_snapshot)
    terminal_source, record, raw_output = _terminal_source_document(
        terminal_snapshot)
    protocol = reservation_source['protocol']
    reps_expected = _positive_int(protocol.get('reps'), label='protocol.reps')
    session_cv_max = _text(protocol.get('session_cv_max'), label='protocol.session_cv_max')
    opened_reps = _positive_int(
        opened_source['reps_expected'], label='opened.reps_expected')
    if opened_reps != reps_expected:
        _fail('opened.reps_expected differs from protocol.reps')
    expected_use_perf = _exact_bool(
        opened_source['expected_use_perf'], label='opened.expected_use_perf')
    mode = _text(reservation_source['mode'], label='mode')
    if mode not in {'pilot', 'official'}:
        _fail('reservation.mode is outside the closed vocabulary')
    before_raw = _probe(opened_source['probe_before'], label='probe_before')
    after_value = opened_source['probe_after']
    after_raw = None if after_value is None else _probe(after_value, label='probe_after')
    failure = _failure(opened_source['failure'])
    launch_failures = [
        _launch_failure(item, position=position)
        for (position, item) in enumerate(opened_source['launch_failures'])
    ]
    (
        observations,
        throughputs,
        nonfinite_count,
        rep_integrity,
        derived_exec_failures,
        measurement_present,
    ) = _source_throughputs_from_snapshot(
        opened_source,
        reps_expected=reps_expected,
        expected_use_perf=expected_use_perf,
        failure=failure,
        pre_probe_competing=before_raw['competing'] is True,
    )
    _assert_authoritative_identity(reservation_source, record)
    serialized = _serialize_session_line(record)
    if raw_output != serialized:
        _fail('raw output differs from serialize_session_line(campaign_record)')
    exec_failures = _nonnegative_int(record['exec_failures'], label='campaign_record.exec_failures')
    record_plaintext = {name: record[name] for name in _CAMPAIGN_PLAINTEXT_KEYS}
    record_plaintext['throughputs'] = list(throughputs)
    checked_plaintext = _campaign_plaintext(record_plaintext)
    if record['throughputs'] != list(throughputs):
        _fail('campaign_record.throughputs differs from qualified finite values')
    if record['reps_expected'] != reps_expected:
        _fail('campaign_record.reps_expected differs from protocol')
    if record['rep_integrity_failures'] != rep_integrity:
        _fail('campaign_record.rep_integrity_failures differs from private sink')
    if measurement_present and exec_failures != derived_exec_failures:
        _fail('campaign_record.exec_failures differs from private sink')
    before_summary = _probe_summary(before_raw)
    after_summary = None if after_raw is None else _probe_summary(after_raw)
    rep_observations_sha256 = _digest_value(observations, label='rep observations')
    _assert_mutual_consistency(probe_before=before_summary, probe_after=after_summary, failure=_failure_summary(failure), launch_failures_count=len(launch_failures), throughputs=throughputs, nonfinite_count=nonfinite_count, exec_failures=exec_failures, reps_expected=reps_expected, rep_integrity_failures=rep_integrity, rep_observations_sha256=rep_observations_sha256, sink_length=len(observations), measurement_present=measurement_present)
    raw_output_sha256 = _sha256_bytes(raw_output)
    assessment = _assess_finite_throughputs(throughputs, reps_expected=reps_expected, session_cv_max=session_cv_max)
    (retry_reason, campaign_reason, status, primary) = _derive_e1(probe_before=before_summary, probe_after=after_summary, failure=_failure_summary(failure), exec_failures=exec_failures, reps_expected=reps_expected, rep_integrity_failures=rep_integrity, assessment=assessment)
    expected_echo = _derive_classification_echo(probe_before=before_summary, probe_after=after_summary, failure=_failure_summary(failure), launch_failures_count=len(launch_failures))
    if opened_source['pre_observation_failure_reason'] != expected_echo:
        _fail('pre-observation failure reason differs from launcher facts')
    terminal_status = terminal_source['terminal_status']
    if terminal_status != status:
        _fail('terminal.terminal_status differs from E1')
    terminal_primary = terminal_source['primary_value']
    if terminal_primary != primary or (terminal_primary is not None and type(terminal_primary) is not float):
        _fail('terminal.primary_value differs from E1')
    report_sha256 = terminal_source['report_sha256']
    if report_sha256 != raw_output_sha256:
        _fail('terminal.report_sha256 differs from raw output digest')
    observation_sha256 = rep_observations_sha256 if status == 'observed' else None
    if terminal_source['observation_sha256'] != observation_sha256:
        _fail('terminal.observation_sha256 differs from E1')
    finished_at = _text(terminal_source['finished_at'], label='finished_at')
    if checked_plaintext['excluded_reason'] != campaign_reason:
        _fail('campaign_record.excluded_reason differs from E1')
    expected_cv = assessment.cv
    if checked_plaintext['session_cv'] != expected_cv:
        _fail('campaign_record.session_cv differs from assessment')
    expected_median = primary if status == 'observed' else None
    if checked_plaintext['session_median'] != expected_median:
        _fail('campaign_record.session_median differs from assessment')
    if checked_plaintext['valid'] is not (status == 'observed'):
        _fail('campaign_record.valid differs from E1')
    expected_exclusion = campaign_reason if campaign_reason in {_CAMPAIGN_COMPETING, _CAMPAIGN_LAUNCH} else s8b_floor_stats.REP_INTEGRITY_EXCLUSION_CLASS if rep_integrity is not None and rep_integrity > 0 else campaign_reason
    if checked_plaintext['exclusion_class'] != expected_exclusion:
        _fail('campaign_record.exclusion_class differs from E1')
    campaign_probe_before_sha256 = _digest_value(record['probe_before'], label='campaign probe_before')
    probe_before_sha256 = _digest_value(before_raw, label='opened probe_before')
    if campaign_probe_before_sha256 != probe_before_sha256:
        _fail('campaign_record.probe_before differs from opened probe')
    campaign_probe_after_sha256 = None if record['probe_after'] is None else _digest_value(record['probe_after'], label='campaign probe_after')
    probe_after_sha256 = None if after_raw is None else _digest_value(after_raw, label='opened probe_after')
    if campaign_probe_after_sha256 != probe_after_sha256:
        _fail('campaign_record.probe_after differs from opened probe')
    if _digest_value(record['rep_observations'], label='campaign observations') != rep_observations_sha256:
        _fail('campaign_record.rep_observations differs from private sink')
    perf_receipt = reservation_source['perf_preflight_receipt']
    document = {
        'schema_version': _SCHEMA_VERSION,
        'attempt_binding': reservation_source['attempt_binding'],
        'mode': mode,
        'expected_use_perf': expected_use_perf,
        'finished_at': finished_at,
        'session_cv_max': session_cv_max,
        'reps_expected': reps_expected,
        'throughputs': list(throughputs),
        'nonfinite_count': nonfinite_count,
        'exec_failures': exec_failures,
        'rep_integrity_failures': rep_integrity,
        'launch_failures_count': len(launch_failures),
        'failure': _failure_summary(failure),
        'probe_before': before_summary,
        'probe_after': after_summary,
        'campaign_record': checked_plaintext,
        'campaign_record_sha256': _sha256_bytes(
            terminal_snapshot._campaign_record_bytes),
        'workload_sha256': _digest_value(record['workload'], label='workload'),
        'run_cmd_sha256': _digest_value(record['run_cmd'], label='run command'),
        'notes_sha256': _digest_value(record['notes'], label='notes'),
        'rep_observations_sha256': rep_observations_sha256,
        'probe_before_sha256': probe_before_sha256,
        'probe_after_sha256': probe_after_sha256,
        'failure_message_sha256': _digest_value(
            None if failure is None else failure['message'],
            label='failure message'),
        'launch_failures_sha256': _digest_value(
            launch_failures, label='launch failures'),
        'perf_preflight_receipt_sha256': _digest_value(
            perf_receipt, label='perf preflight receipt'),
        'raw_output_sha256': raw_output_sha256,
        'report_sha256': raw_output_sha256,
        'observation_sha256': observation_sha256,
        'unauthored_identity_sha256': _digest_value(
            {
                name: record[name]
                for name in _UNAUTHORED_CAMPAIGN_IDENTITY_KEYS
            },
            label='unauthored campaign identity'),
    }
    canonical = _canonical(document, label='terminal evidence')
    parsed = _strict_json_document(canonical)
    _validated_document(parsed, expected_binding_keys=_DRAFT_ATTEMPT_BINDING_KEYS)
    draft = object.__new__(SealedTerminalEvidenceDraft)
    object.__setattr__(draft, '_canonical_bytes', canonical)
    object.__setattr__(
        draft,
        '_external_evidence_sha256',
        opened_source['external_evidence_sha256'],
    )
    object.__setattr__(
        draft,
        '_launcher_origin_capability',
        opened_snapshot._reservation._launcher_origin_capability,
    )
    return draft

def require_sealed_terminal_evidence(value: object) -> ValidatedTerminalEvidence:
    """Require an already adapter-issued validated capability.

    This is deliberately not a draft promotion API.  It performs an exact-type
    check and reconstructs all derived state from the capability's canonical
    bytes on every call.
    """
    if type(value) is not ValidatedTerminalEvidence:
        _fail('validated terminal evidence has an invalid exact type')
    if type(value._issuer_token) is not object:
        _fail('validated terminal evidence has an invalid issuer token')
    data = value._canonical_bytes
    document = _strict_json_document(data)
    _validated_document(document, expected_binding_keys=_VALIDATED_ATTEMPT_BINDING_KEYS)
    return value
