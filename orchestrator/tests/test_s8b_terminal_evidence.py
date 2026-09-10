"""Contract and mutation tests for the pure terminal-evidence leaf."""
from __future__ import annotations
import ast
import copy
from dataclasses import dataclass, replace
from enum import IntEnum
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any
import pytest
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from orchestrator.campaign import attempt_registry_core as core
from orchestrator.campaign import s8b_attempt_profile as profile8b
from orchestrator.campaign import s8b_floor_stats as stats
from orchestrator.campaign import s8b_holdout_admission as admission
from orchestrator.campaign import s8b_holdout_freeze as holdout_freeze
from orchestrator.campaign import s8b_ratified_freeze as ratified
from orchestrator.campaign import s8b_terminal_evidence as evidence
H = {
    name: hashlib.sha256(name.encode('ascii')).hexdigest()
    for name in (
        'admission',
        'classification-event',
        'classification-receipt',
        'freeze',
        'manifest',
        'observation-event',
        'protocol',
        'schedule',
        'schedule-row',
    )
}

@dataclass
class _Binding:
    freeze_sha256: str = H['freeze']
    protocol_sha256: str = H['protocol']
    schedule_sha256: str = H['schedule']

@dataclass
class _Reservation:
    binding: object
    slot_id: tuple[str, str, int, int, int]
    protocol: dict[str, object]
    mode: str
    perf_preflight_receipt: object
    admission_claim_digest: str
    attempt_id: str
    campaign_run_id: str
    manifest_sha256: str
    run_relpath: str
    cell_id: str
    schedule_row_sha256: str
    records: int
    threads: int
    workload: dict[str, object]

@dataclass
class _Measurement:
    throughputs: list[float]

@dataclass
class _Opened:
    measurement: object | None
    failure: dict[str, object] | None
    probe_before: dict[str, object]
    probe_after: dict[str, object] | None
    launch_failures: tuple[object, ...]
    pre_observation_failure_reason: str | None
    external_evidence_sha256: str
    repetition_evidence: tuple[dict[str, object], ...]
    expected_use_perf: bool
    reps_expected: int

@dataclass
class _Terminal:
    raw_output_bytes: bytes
    terminal_status: str
    report_sha256: str
    observation_sha256: str | None
    primary_value: float | None
    finished_at: str
    campaign_record: dict[str, object]

@dataclass
class _Case:
    reservation: _Reservation
    opened: _Opened
    terminal: _Terminal

def _digest(value: object) -> str:
    return hashlib.sha256(core.canonical_json_bytes(value)).hexdigest()

def _probe(*, competing: bool=False) -> dict[str, object]:
    return {
        'rc': 0 if competing else 1,
        'stdout': '777 ycsb_other.exe\n' if competing else '',
        'stderr': '',
        'competing': competing,
    }

def _observation(
    index: int,
    throughput: float | None,
    *,
    returncode: int | None=0,
    execution_failure: bool=False,
) -> dict[str, object]:
    return {
        'rep_index': index,
        'returncode': returncode,
        'execution_failure': execution_failure,
        'counter_status': 'not_required',
        'missing_perf_events': [],
        'perf_raw': {event: None for event in stats.PERF_EVENTS},
        'throughput': throughput,
    }

def _base_reservation() -> _Reservation:
    workload = {'ycsb_rratio': '81', 'ycsb_zipf_skew': '0.9', 'ycsb_rmw': '0'}
    return _Reservation(
        binding=_Binding(),
        slot_id=('holdout-a', 'configuration-a', 7, 2, 0),
        protocol={'reps': 3, 'session_cv_max': '0.5'},
        mode='pilot',
        perf_preflight_receipt={'status': 'unavailable', 'available': False},
        admission_claim_digest=H['admission'],
        attempt_id='holdout-a::configuration-a::attempt-2',
        campaign_run_id='campaign-run-a',
        manifest_sha256=H['manifest'],
        run_relpath='runs/campaign-run-a',
        cell_id='holdout-a::configuration-a',
        schedule_row_sha256=H['schedule-row'],
        records=1000000,
        threads=48,
        workload=workload,
    )

def _record(
    reservation: _Reservation,
    *,
    before: dict[str, object],
    after: dict[str, object] | None,
    observations: list[dict[str, object]],
    throughputs: list[float],
    exec_failures: int,
    rep_integrity_failures: int | None,
    excluded_reason: str | None,
    exclusion_class: str | None,
    session_median: float | None,
    session_cv: float | None,
    valid: bool,
) -> dict[str, object]:
    return {
        'event': 'session',
        'kind': 'retry',
        'seq': 17,
        'round': 4,
        'retry_ordinal': reservation.slot_id[3],
        'attempt_id': reservation.attempt_id,
        'trigger': 'round-end',
        'cell_id': reservation.cell_id,
        'holdout_id': reservation.slot_id[0],
        'configuration_id': reservation.slot_id[1],
        'records': reservation.records,
        'threads': reservation.threads,
        'workload': copy.deepcopy(reservation.workload),
        'throughputs': list(throughputs),
        'reps_expected': 3,
        'exec_failures': exec_failures,
        'excluded_reason': excluded_reason,
        'retry': True,
        'rep_observations': copy.deepcopy(observations),
        'rep_integrity_failures': rep_integrity_failures,
        'exclusion_class': exclusion_class,
        'session_median': session_median,
        'valid': valid,
        'session_cv': session_cv,
        'duration_s': 1.25,
        'run_cmd': [
            'ycsb_test.exe',
            'ycsb_rratio=81',
            'ycsb_zipf_skew=0.9',
            'ycsb_rmw=0',
        ],
        'notes': ['sealed source note'],
        'probe_before': copy.deepcopy(before),
        'probe_after': copy.deepcopy(after),
        'binary_sha256_at_measure': hashlib.sha256(b'binary').hexdigest(),
    }

def _finish_case(
    reservation: _Reservation,
    opened: _Opened,
    record: dict[str, object],
    *,
    status: str,
    primary: float | None,
) -> _Case:
    raw = profile8b.serialize_session_line(record)
    raw_digest = hashlib.sha256(raw).hexdigest()
    observation_digest = _digest(record['rep_observations']) if status == 'observed' else None
    terminal = _Terminal(
        raw_output_bytes=raw,
        terminal_status=status,
        report_sha256=raw_digest,
        observation_sha256=observation_digest,
        primary_value=primary,
        finished_at='2026-09-08T00:00:02+00:00',
        campaign_record=record,
    )
    return _Case(reservation=reservation, opened=opened, terminal=terminal)

def _case(kind: str='observed') -> _Case:
    reservation = _base_reservation()
    before = _probe()
    after: dict[str, object] | None = _probe()
    failure = None
    launch_failures: tuple[object, ...] = ()
    reason = None
    values = [100.0, 101.0, 102.0]
    observations = [_observation(index, value) for (index, value) in enumerate(values)]
    measurement: object | None = _Measurement(list(values))
    exec_failures = 0
    rep_integrity = 0
    assessment = stats.assess_session(values, reps=3, session_cv_max='0.5')
    excluded = None
    exclusion = None
    median = float(assessment.median)
    session_cv = assessment.cv
    valid = True
    status = 'observed'
    primary: float | None = median
    if kind == 'precompeting':
        before = _probe(competing=True)
        after = None
        observations = []
        measurement = None
        rep_integrity = None
        reason = 'competing_process'
        values = []
        excluded = 'competing_process'
        exclusion = 'competing_process'
        median = session_cv = None
        valid = False
        status = 'retryable-failure'
        primary = None
    elif kind == 'oserror':
        failure = {'stage': 'capture', 'exception_type': 'OSError', 'errno': 5, 'message': 'capture unavailable'}
        observations = []
        measurement = None
        exec_failures = 3
        rep_integrity = None
        reason = 'launch_failure'
        values = []
        excluded = 'launch_failure'
        exclusion = 'launch_failure'
        median = session_cv = None
        valid = False
        status = 'retryable-failure'
        primary = None
    elif kind == 'full-exec':
        observations = [
            _observation(
                index, None, returncode=None, execution_failure=True,
            )
            for index in range(3)
        ]
        measurement = _Measurement([])
        launch_failures = ({'exception_type': 'RuntimeError', 'errno': None, 'message': 'all repetitions failed'},)
        exec_failures = 3
        rep_integrity = 3
        reason = 'launch_failure'
        values = []
        excluded = 'launch_failure'
        exclusion = 'launch_failure'
        median = session_cv = None
        valid = False
        status = 'retryable-failure'
        primary = None
    elif kind != 'observed':
        raise AssertionError(f'unknown case: {kind}')
    opened = _Opened(
        measurement=measurement,
        failure=failure,
        probe_before=before,
        probe_after=after,
        launch_failures=launch_failures,
        pre_observation_failure_reason=reason,
        external_evidence_sha256=evidence._pre_output_evidence_sha256(
            probe_before=before,
            probe_after=after,
            launch_failures=tuple(
                dict(item) for item in launch_failures
            ),
            failure=failure,
        ),
        repetition_evidence=tuple(observations),
        expected_use_perf=False,
        reps_expected=3,
    )
    record = _record(
        reservation,
        before=before,
        after=after,
        observations=observations,
        throughputs=values,
        exec_failures=exec_failures,
        rep_integrity_failures=rep_integrity,
        excluded_reason=excluded,
        exclusion_class=exclusion,
        session_median=median,
        session_cv=session_cv,
        valid=valid,
    )
    return _finish_case(reservation, opened, record, status=status, primary=primary)

def _integrity_failure_case(kind: str) -> _Case:
    case = _case()
    observations = copy.deepcopy(list(case.opened.repetition_evidence))
    if kind == 'nonzero':
        observations[1]['returncode'] = 7
        measurement_values = [100.0, 101.0, 102.0]
        exec_failures = 0
    elif kind == 'execution':
        observations[1].update({
            'returncode': None,
            'execution_failure': True,
            'throughput': None,
        })
        measurement_values = [100.0, 102.0]
        exec_failures = 1
    else:
        raise AssertionError(f'unknown integrity case: {kind}')
    case.opened.repetition_evidence = tuple(observations)
    case.opened.measurement = _Measurement(measurement_values)
    record = copy.deepcopy(case.terminal.campaign_record)
    record.update({
        'rep_observations': observations,
        'throughputs': [100.0, 102.0],
        'exec_failures': exec_failures,
        'rep_integrity_failures': 1,
        'excluded_reason': 'nonfinite_or_partial_output',
        'exclusion_class': stats.REP_INTEGRITY_EXCLUSION_CLASS,
        'session_median': None,
        'session_cv': None,
        'valid': False,
    })
    return _finish_case(
        case.reservation, case.opened, record,
        status='retryable-failure', primary=None,
    )

def _seal(case: _Case | None=None) -> evidence.SealedTerminalEvidenceDraft:
    value = _case() if case is None else case
    return evidence.seal_terminal_evidence(value.reservation, value.opened, value.terminal)

def _draft_from_bytes(data: bytes) -> evidence.SealedTerminalEvidenceDraft:
    value = object.__new__(evidence.SealedTerminalEvidenceDraft)
    object.__setattr__(value, '_canonical_bytes', data)
    return value

def _promote(draft: evidence.SealedTerminalEvidenceDraft) -> evidence.ValidatedTerminalEvidence:
    document = copy.deepcopy(draft.document)
    document['attempt_binding'].update({
        'classification_receipt_sha256': H['classification-receipt'],
        'classification_event_sha256': H['classification-event'],
        'observation_event_sha256': H['observation-event'],
    })
    data = core.canonical_json_bytes(document)
    value = object.__new__(evidence.ValidatedTerminalEvidence)
    object.__setattr__(value, '_canonical_bytes', data)
    object.__setattr__(value, '_issuer_token', object())
    return value

def _healthy_assessment() -> stats.SessionAssessment:
    return stats.assess_session([100.0, 101.0, 102.0], reps=3, session_cv_max='0.5')

def _partial_assessment() -> stats.SessionAssessment:
    return stats.assess_session([100.0, 101.0], reps=3, session_cv_max='0.5')

def _performance_assessment() -> stats.SessionAssessment:
    return stats.assess_session([1.0, 100.0, 200.0], reps=3, session_cv_max='0.1')

def test_public_surface_signatures_and_dataclass_fields_are_exact() -> None:
    assert tuple(inspect.signature(evidence.derive_terminal_projection).parameters) == ('document',)
    assert tuple(inspect.signature(evidence.seal_terminal_evidence).parameters) == ('reservation', 'opened', 'terminal')
    assert tuple(inspect.signature(evidence.require_sealed_terminal_evidence).parameters) == ('value',)
    assert tuple(evidence.TerminalEvidenceProjection.__dataclass_fields__) == ('terminal_status', 'failure_reason', 'measurement_retry_reason', 'campaign_excluded_reason', 'primary_value', 'raw_output_sha256', 'report_sha256', 'observation_sha256', 'finished_at')

def test_production_imports_are_limited_to_the_two_contract_modules() -> None:
    path = _REPO_ROOT / 'orchestrator/campaign/s8b_terminal_evidence.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    relative = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            relative.append((node.module, tuple((alias.name for alias in node.names))))
    assert relative == [('attempt_registry_core', ('canonical_json_bytes',)), (None, ('s8b_floor_stats',))]

def test_outer_schema_and_draft_binding_are_exact() -> None:
    draft = _seal()
    document = draft.document
    assert set(document) == evidence._OUTER_KEYS
    assert len(document) == 30
    assert set(document['attempt_binding']) == evidence._DRAFT_ATTEMPT_BINDING_KEYS
    assert len(document['attempt_binding']) == 9
    assert evidence._PHASE_DIGEST_KEYS.isdisjoint(document['attempt_binding'])

def test_validated_binding_has_exact_twelve_keys_and_real_spelling() -> None:
    validated = _promote(_seal())
    checked = evidence.require_sealed_terminal_evidence(validated)
    binding = checked.document['attempt_binding']
    assert set(binding) == evidence._VALIDATED_ATTEMPT_BINDING_KEYS
    assert len(binding) == 12
    assert 'observation_event_sha256' in binding
    assert 'observation_start_event_sha256' not in binding

def test_campaign_trust_root_equals_ratified_exact_thirty_keys() -> None:
    assert evidence._CAMPAIGN_RECORD_KEYS == ratified._JOURNAL_KEYS['session']
    assert len(evidence._CAMPAIGN_RECORD_KEYS) == 30

def test_identity_four_groups_are_disjoint_and_exhaustive() -> None:
    groups = (evidence._AUTHORED_CAMPAIGN_IDENTITY_KEYS, evidence._UNAUTHORED_CAMPAIGN_IDENTITY_KEYS, evidence._CAMPAIGN_MEASUREMENT_KEYS, evidence._CAMPAIGN_DIGEST_ONLY_KEYS)
    for (index, group) in enumerate(groups):
        assert all((group.isdisjoint(other) for other in groups[index + 1:]))
    assert frozenset().union(*groups) == evidence._CAMPAIGN_RECORD_KEYS
    document = _seal().document
    assert set(document['campaign_record']) == evidence._CAMPAIGN_PLAINTEXT_KEYS
    assert evidence._UNAUTHORED_CAMPAIGN_IDENTITY_KEYS.isdisjoint(document['campaign_record'])

def test_all_source_digests_are_rederived() -> None:
    case = _case()
    document = _seal(case).document
    record = case.terminal.campaign_record
    assert document['campaign_record_sha256'] == _digest(record)
    assert document['workload_sha256'] == _digest(record['workload'])
    assert document['run_cmd_sha256'] == _digest(record['run_cmd'])
    assert document['notes_sha256'] == _digest(record['notes'])
    assert document['rep_observations_sha256'] == _digest(record['rep_observations'])
    assert document['probe_before_sha256'] == _digest(record['probe_before'])
    assert document['probe_after_sha256'] == _digest(record['probe_after'])
    assert document['failure_message_sha256'] == _digest(None)
    assert document['launch_failures_sha256'] == _digest([])
    assert document['perf_preflight_receipt_sha256'] == _digest(case.reservation.perf_preflight_receipt)
    raw_digest = hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()
    assert document['raw_output_sha256'] == raw_digest
    assert document['report_sha256'] == raw_digest
    assert document['observation_sha256'] == _digest(record['rep_observations'])
    unauthored = {name: record[name] for name in evidence._UNAUTHORED_CAMPAIGN_IDENTITY_KEYS}
    assert document['unauthored_identity_sha256'] == _digest(unauthored)

def test_raw_output_relation_uses_the_existing_session_serializer() -> None:
    case = _case()
    assert case.terminal.raw_output_bytes == profile8b.serialize_session_line(case.terminal.campaign_record)
    assert _seal(case).projection.raw_output_sha256 == hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()

def test_projection_is_rebuilt_from_canonical_bytes() -> None:
    draft = _seal()
    first = draft.projection
    second = draft.projection
    assert first == second
    assert first is not second
    assert first == evidence.TerminalEvidenceProjection(terminal_status='observed', failure_reason=None, measurement_retry_reason=None, campaign_excluded_reason=None, primary_value=101.0, raw_output_sha256=draft.document['raw_output_sha256'], report_sha256=draft.document['report_sha256'], observation_sha256=draft.document['observation_sha256'], finished_at='2026-09-08T00:00:02+00:00')

def test_document_is_a_fresh_detached_tree_on_every_access() -> None:
    draft = _seal()
    first = draft.document
    first['campaign_record']['attempt_id'] = 'forged'
    first['throughputs'].append(999.0)
    second = draft.document
    assert second['campaign_record']['attempt_id'] != 'forged'
    assert second['throughputs'] == [100.0, 101.0, 102.0]

def test_holdout_safe_positive_and_plaintext_negative_are_paired() -> None:
    draft = _seal()
    admission.assert_holdout_safe_bytes('terminal-evidence.json', draft.canonical_bytes)
    document = copy.deepcopy(draft.document)
    holdout = holdout_freeze.HOLDOUTS['rr80']['ycsb']
    run_cmd = ['ycsb_test.exe'] + [
        holdout_freeze.concrete_axis_encodings(axis, holdout[key])[0]
        for (axis, key) in (
            ('rratio', holdout_freeze.RRATIO_KEY),
            ('skew', holdout_freeze.SKEW_KEY),
            ('rmw', holdout_freeze.RMW_KEY),
        )
    ]
    mutations = ({'workload': holdout}, {'run_cmd': run_cmd})
    for mutation in mutations:
        contaminated = {**document, **mutation}
        with pytest.raises(admission.HoldoutAdmissionError, match='contamination'):
            admission.assert_holdout_safe_bytes('terminal-evidence.json', core.canonical_json_bytes(contaminated))

@pytest.mark.parametrize(('case_kind', 'status', 'failure_reason', 'retry_reason', 'campaign_reason'), [('observed', 'observed', None, None, None), ('precompeting', 'retryable-failure', 'competing_process', 'measurement_environment_conflict', 'competing_process'), ('oserror', 'retryable-failure', 'launch_failure', 'measurement_execution_unavailable', 'launch_failure'), ('full-exec', 'retryable-failure', 'launch_failure', 'measurement_execution_unavailable', 'launch_failure')])
def test_end_to_end_e1_representative_cases(case_kind: str, status: str, failure_reason: str | None, retry_reason: str | None, campaign_reason: str | None) -> None:
    projection = _seal(_case(case_kind)).projection
    assert projection.terminal_status == status
    assert projection.failure_reason == failure_reason
    assert projection.measurement_retry_reason == retry_reason
    assert projection.campaign_excluded_reason == campaign_reason
    assert projection.terminal_status not in {'terminal-failure', 'not-consumed'}

@pytest.mark.parametrize(('before', 'after', 'failure', 'exec_count', 'rep_integrity', 'assessment', 'expected'), [({'competing': True}, None, {'stage': 'capture'}, 3, None, _healthy_assessment(), ('measurement_environment_conflict', 'competing_process', 'retryable-failure', None)), ({'competing': False}, {'competing': False}, {'stage': 'open'}, 3, None, _partial_assessment(), ('measurement_execution_unavailable', 'launch_failure', 'retryable-failure', None)), ({'competing': False}, {'competing': False}, None, 1, 0, _healthy_assessment(), ('measurement_execution_unavailable', 'launch_failure', 'retryable-failure', None)), ({'competing': False}, {'competing': False}, None, 0, 1, _partial_assessment(), ('measurement_sample_incomplete', 'nonfinite_or_partial_output', 'retryable-failure', None)), ({'competing': False}, {'competing': False}, None, 0, 0, _partial_assessment(), ('measurement_sample_incomplete', 'nonfinite_or_partial_output', 'retryable-failure', None)), ({'competing': False}, {'competing': False}, None, 0, 0, _performance_assessment(), ('measurement_dispersion_exceeded', 'performance_anomaly', 'retryable-failure', None)), ({'competing': False}, {'competing': False}, None, 0, 0, _healthy_assessment(), (None, None, 'observed', 101.0))])
def test_e1_all_ordered_branches_are_directly_observable(before: dict[str, bool], after: dict[str, bool] | None, failure: dict[str, object] | None, exec_count: int, rep_integrity: int | None, assessment: stats.SessionAssessment, expected: tuple[object, ...]) -> None:
    assert evidence._derive_e1(probe_before=before, probe_after=after, failure=failure, exec_failures=exec_count, reps_expected=3, rep_integrity_failures=rep_integrity, assessment=assessment) == expected

def test_nonfinite_normalization_counts_and_removes_values() -> None:
    opened = _case().opened
    values = [100.0, float('nan'), 102.0]
    opened.measurement = _Measurement(list(values))
    opened.repetition_evidence = tuple((_observation(index, value) for (index, value) in enumerate(values)))
    (observations, finite, count, failures, exec_failures, present) = evidence._source_throughputs(opened, reps_expected=3, expected_use_perf=False, failure=None, pre_probe_competing=False)
    assert len(observations) == 3
    assert finite == (100.0, 102.0)
    assert count == 1
    assert failures == 0
    assert exec_failures == 0
    assert present is True
    assessment = evidence._assess_finite_throughputs(finite, reps_expected=3, session_cv_max='0.5')
    assert assessment.required_reason == 'nonfinite_or_partial_output'

def test_rep_integrity_is_rederived_from_private_sink() -> None:
    opened = _case('full-exec').opened
    (_observations, finite, count, failures, exec_failures, present) = evidence._source_throughputs(opened, reps_expected=3, expected_use_perf=False, failure=None, pre_probe_competing=False)
    assert finite == ()
    assert count == 0
    assert failures == 3
    assert exec_failures == 3
    assert present is True

def test_nonzero_rc_integrity_failure_reaches_sealed_terminal() -> None:
    """B1: non-execution integrity failure is its own repetition class."""
    document = _seal(_integrity_failure_case('nonzero')).document
    assert document['throughputs'] == [100.0, 102.0]
    assert document['exec_failures'] == 0
    assert document['rep_integrity_failures'] == 1
    assert document['campaign_record']['excluded_reason'] == \
        'nonfinite_or_partial_output'

def test_execution_failure_without_throughput_is_a_valid_sealed_input() -> None:
    """B2 positive: runner-caught exception has no throughput and remains sealable."""
    document = _seal(_integrity_failure_case('execution')).document
    assert document['throughputs'] == [100.0, 102.0]
    assert document['exec_failures'] == 1
    assert document['rep_integrity_failures'] == 1

def test_execution_failure_with_success_throughput_is_rejected_by_signature() -> None:
    case = _case()
    case.opened.repetition_evidence[1]['execution_failure'] = True
    with pytest.raises(
        evidence.TerminalEvidenceError,
        match='execution_failure=True なのに throughput が非 null',
    ):
        _seal(case)

def test_terminal_rejects_exec_count_mismatch_against_private_sink() -> None:
    case = _integrity_failure_case('execution')
    case.terminal.campaign_record['exec_failures'] = 0
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(
        case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(
        case.terminal.raw_output_bytes).hexdigest()
    with pytest.raises(
        evidence.TerminalEvidenceError,
        match='campaign_record.exec_failures differs from private sink',
    ):
        _seal(case)

def test_mutation_l01_outer_extra_key_has_one_exact_schema_gate() -> None:
    document = copy.deepcopy(_seal().document)
    document['extra'] = None
    with pytest.raises(evidence.TerminalEvidenceError, match='terminal evidence exact keys'):
        evidence.derive_terminal_projection(document)

def test_mutation_l02_draft_binding_extra_key_has_one_exact_gate() -> None:
    document = copy.deepcopy(_seal().document)
    document['attempt_binding']['extra'] = None
    data = core.canonical_json_bytes(document)
    with pytest.raises(evidence.TerminalEvidenceError, match='attempt_binding exact keys'):
        _draft_from_bytes(data).document

def test_mutation_l03_validated_old_observation_spelling_has_one_gate() -> None:
    validated = _promote(_seal())
    document = copy.deepcopy(validated.document)
    value = document['attempt_binding'].pop('observation_event_sha256')
    document['attempt_binding']['observation_start_event_sha256'] = value
    forged = object.__new__(evidence.ValidatedTerminalEvidence)
    object.__setattr__(forged, '_canonical_bytes', core.canonical_json_bytes(document))
    object.__setattr__(forged, '_issuer_token', object())
    with pytest.raises(evidence.TerminalEvidenceError, match='attempt_binding exact keys'):
        evidence.require_sealed_terminal_evidence(forged)

@pytest.mark.parametrize('mutate', [lambda data, _document: data + b'\n', lambda _data, document: json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(', ', ':'), allow_nan=False).encode('utf-8')])
def test_mutations_l04_l05_noncanonical_bytes_have_only_canonical_gate(mutate) -> None:
    draft = _seal()
    data = mutate(draft.canonical_bytes, draft.document)
    with pytest.raises(evidence.TerminalEvidenceError, match='bytes are not canonical'):
        _draft_from_bytes(data).document

def test_mutation_l06_nonfinite_plaintext_has_only_finite_gate() -> None:
    document = copy.deepcopy(_seal().document)
    document['throughputs'][1] = float('nan')
    with pytest.raises(evidence.TerminalEvidenceError, match='finite exact float'):
        evidence.derive_terminal_projection(document)

def test_mutation_l07_missing_nonfinite_count_has_only_sum_gate() -> None:
    with pytest.raises(evidence.TerminalEvidenceError, match='repetition sum'):
        evidence._assert_mutual_consistency(probe_before={'competing': False}, probe_after={'competing': False}, failure=None, launch_failures_count=0, throughputs=(100.0, 102.0), nonfinite_count=0, exec_failures=0, reps_expected=3, rep_integrity_failures=0, rep_observations_sha256='a' * 64, sink_length=3, measurement_present=True)

def test_mutation_l08_competing_precedes_failure() -> None:
    actual = evidence._derive_e1(probe_before={'competing': True}, probe_after=None, failure={'stage': 'capture'}, exec_failures=3, reps_expected=3, rep_integrity_failures=None, assessment=_partial_assessment())
    assert actual[:2] == ('measurement_environment_conflict', 'competing_process')

def test_mutation_l09_failure_branch_is_directly_observed() -> None:
    actual = evidence._derive_e1(probe_before={'competing': False}, probe_after={'competing': False}, failure={'stage': 'open'}, exec_failures=0, reps_expected=3, rep_integrity_failures=None, assessment=_healthy_assessment())
    assert actual[0] == 'measurement_execution_unavailable'

def test_mutation_l10_rep_integrity_partial_is_not_dispersion() -> None:
    actual = evidence._derive_e1(probe_before={'competing': False}, probe_after={'competing': False}, failure=None, exec_failures=0, reps_expected=3, rep_integrity_failures=1, assessment=_partial_assessment())
    assert actual[0] == 'measurement_sample_incomplete'

def test_mutation_l11_assessment_keeps_original_rep_count() -> None:
    finite = (100.0, 102.0)
    required = evidence._assess_finite_throughputs(finite, reps_expected=3, session_cv_max='0.5')
    shortened = stats.assess_session(finite, reps=2, session_cv_max='0.5')
    assert required.required_reason == 'nonfinite_or_partial_output'
    assert shortened.required_reason is None

def test_mutation_l12_primary_must_be_assessment_median() -> None:
    case = _case()
    case.terminal.primary_value = 100.0
    with pytest.raises(evidence.TerminalEvidenceError, match='primary_value'):
        _seal(case)

@pytest.mark.parametrize(
    'exception_name',
    ['RuntimeError', 'subprocess.TimeoutExpired', 'OSError'],
)
def test_mutation_l13_launcher_captured_set_is_exact(
    exception_name: str,
) -> None:
    case = _case('oserror')
    assert case.opened.failure is not None
    case.opened.failure['exception_type'] = exception_name
    case.opened.external_evidence_sha256 = (
        evidence._pre_output_evidence_sha256(
            probe_before=case.opened.probe_before,
            probe_after=case.opened.probe_after,
            launch_failures=(),
            failure=case.opened.failure,
        )
    )
    projection = _seal(case).projection
    assert projection.measurement_retry_reason == 'measurement_execution_unavailable'
    assert _seal(case).document['failure_message_sha256'] == _digest(
        case.opened.failure['message'])

def test_mutation_l14_unknown_exception_name_is_rejected() -> None:
    case = _case('oserror')
    assert case.opened.failure is not None
    case.opened.failure['exception_type'] = 'ValueError'
    with pytest.raises(evidence.TerminalEvidenceError, match='captured set'):
        _seal(case)

def test_mutation_l15_require_uses_exact_type_not_isinstance() -> None:
    validated = _promote(_seal())

    class _Subclass(evidence.ValidatedTerminalEvidence):
        pass
    forged = object.__new__(_Subclass)
    object.__setattr__(forged, '_canonical_bytes', validated.canonical_bytes)
    object.__setattr__(forged, '_issuer_token', object())
    with pytest.raises(evidence.TerminalEvidenceError, match='invalid exact type'):
        evidence.require_sealed_terminal_evidence(forged)

def test_mutation_l16_probe_equivalence_checks_both_directions() -> None:
    with pytest.raises(evidence.TerminalEvidenceError, match='skip equivalence'):
        evidence._assert_mutual_consistency(probe_before={'competing': False}, probe_after=None, failure=None, launch_failures_count=0, throughputs=(), nonfinite_count=0, exec_failures=0, reps_expected=3, rep_integrity_failures=None, rep_observations_sha256=_digest([]))

def test_mutation_l17_report_digest_is_rederived_from_raw_bytes() -> None:
    case = _case()
    case.terminal.report_sha256 = 'f' * 64
    with pytest.raises(evidence.TerminalEvidenceError, match='report_sha256'):
        _seal(case)

def test_mutation_l18_canonical_bytes_never_returns_internal_reference() -> None:
    draft = _seal()
    first = draft.canonical_bytes
    second = draft.canonical_bytes
    assert first == second
    assert first is not second
    validated = _promote(draft)
    first_validated = validated.canonical_bytes
    second_validated = validated.canonical_bytes
    assert first_validated == second_validated
    assert first_validated is not second_validated

@pytest.mark.parametrize('mutation', [{'probe_after': None}, {'rep_integrity_failures': None}, {'exec_failures': 1}])
def test_opened_mutual_consistency_rejects_each_independent_break(mutation) -> None:
    document = copy.deepcopy(_seal().document)
    document.update(mutation)
    if 'rep_integrity_failures' in mutation:
        document['campaign_record']['rep_integrity_failures'] = None
    if 'exec_failures' in mutation:
        document['campaign_record']['exec_failures'] = 1
    with pytest.raises(evidence.TerminalEvidenceError):
        evidence.derive_terminal_projection(document)

def test_opened_sink_length_is_checked_directly() -> None:
    with pytest.raises(evidence.TerminalEvidenceError, match='sink length'):
        evidence._assert_mutual_consistency(probe_before={'competing': False}, probe_after={'competing': False}, failure=None, launch_failures_count=0, throughputs=(100.0, 101.0, 102.0), nonfinite_count=0, exec_failures=0, reps_expected=3, rep_integrity_failures=0, rep_observations_sha256='a' * 64, sink_length=2, measurement_present=True)

def test_failure_requires_unavailable_projection() -> None:
    case = _case('oserror')
    case.terminal.campaign_record['exec_failures'] = 2
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()
    with pytest.raises(evidence.TerminalEvidenceError, match='unavailable projection'):
        _seal(case)

def test_launch_failure_count_contradicts_zero_exec_failures() -> None:
    with pytest.raises(evidence.TerminalEvidenceError, match='contradict'):
        evidence._assert_mutual_consistency(probe_before={'competing': False}, probe_after={'competing': False}, failure=None, launch_failures_count=1, throughputs=(100.0, 101.0, 102.0), nonfinite_count=0, exec_failures=0, reps_expected=3, rep_integrity_failures=0, rep_observations_sha256='a' * 64, sink_length=3, measurement_present=True)

def test_capture_failure_requires_zero_launch_failure_count_pair() -> None:
    positive = _case('oserror')
    assert _seal(positive).document['launch_failures_count'] == 0

    negative = _case('oserror')
    contradictory = {
        'exception_type': 'OSError',
        'errno': 5,
        'message': 'contradictory launch failure',
    }
    negative.opened.launch_failures = (contradictory,)
    negative.opened.external_evidence_sha256 = (
        evidence._pre_output_evidence_sha256(
            probe_before=negative.opened.probe_before,
            probe_after=negative.opened.probe_after,
            launch_failures=(contradictory,),
            failure=negative.opened.failure,
        )
    )
    with pytest.raises(
        evidence.TerminalEvidenceError,
        match='capture failure has nonzero launch_failures_count',
    ):
        _seal(negative)

def test_opened_external_digest_is_rechecked_against_each_source() -> None:
    case = _case()
    case.opened.probe_before['stderr'] = 'builder-forged'
    with pytest.raises(
        evidence.TerminalEvidenceError,
        match='external evidence digest differs from source facts',
    ):
        _seal(case)


@pytest.mark.parametrize(
    ('field', 'replacement'),
    (
        ('rep_index', type('RepIndexSubclass', (int,), {})(0)),
        ('returncode', IntEnum('ReturnCode', {'ZERO': 0}).ZERO),
    ),
)
def test_rep_source_exact_integer_types_are_checked_before_canonical_copy(
    field: str,
    replacement: object,
) -> None:
    case = _case()
    case.opened.repetition_evidence[0][field] = replacement
    with pytest.raises(evidence.TerminalEvidenceError):
        _seal(case)


@pytest.mark.parametrize(
    ('field', 'replacement', 'message'),
    (
        ('records', type('RecordCountSubclass', (int,), {})(1000000), 'records'),
        ('retry_ordinal', IntEnum('RetryOrdinal', {'TWO': 2}).TWO, 'retry_ordinal'),
        ('attempt_id', type('AttemptIdSubclass', (str,), {})('holdout-a::configuration-a::attempt-2'), 'attempt_id'),
    ),
)
def test_campaign_source_exact_types_are_checked_before_canonical_copy(
    field: str,
    replacement: object,
    message: str,
) -> None:
    case = _case()
    case.terminal.campaign_record[field] = replacement
    with pytest.raises(evidence.TerminalEvidenceError, match=message):
        _seal(case)


def test_planned_terminal_binds_none_retry_ordinal() -> None:
    case = _case()
    case.reservation.slot_id = (*case.reservation.slot_id[:3], 0, 0)
    case.terminal.campaign_record.update({
        'kind': 'planned',
        'retry': False,
        'retry_ordinal': None,
        'trigger': None,
    })
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(
        case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(
        case.terminal.raw_output_bytes).hexdigest()

    draft = _seal(case)

    assert draft.document['campaign_record']['retry_ordinal'] is None


def test_planned_terminal_rejects_nonnull_retry_ordinal() -> None:
    case = _case()
    case.reservation.slot_id = (*case.reservation.slot_id[:3], 0, 0)
    case.terminal.campaign_record.update({
        'kind': 'planned',
        'retry': False,
        'retry_ordinal': 1,
        'trigger': None,
    })
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(
        case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(
        case.terminal.raw_output_bytes).hexdigest()

    with pytest.raises(
        evidence.TerminalEvidenceError,
        match='campaign_record.retry_ordinal differs from durable identity',
    ):
        _seal(case)


def test_campaign_retry_binds_measurement_ordinal_not_recovery_ordinal() -> None:
    case = _case()
    assert case.reservation.slot_id[3] == 2
    assert case.reservation.slot_id[4] == 0
    assert _seal(case).document['campaign_record']['retry_ordinal'] == 2

    case.terminal.campaign_record['retry_ordinal'] = (
        case.reservation.slot_id[4])
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(
        case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(
        case.terminal.raw_output_bytes).hexdigest()
    with pytest.raises(
        evidence.TerminalEvidenceError,
        match='campaign_record.retry_ordinal differs from durable identity',
    ):
        _seal(case)


def test_campaign_excluded_reason_must_equal_rederived_word() -> None:
    case = _case()
    case.terminal.campaign_record['excluded_reason'] = 'performance_anomaly'
    case.terminal.campaign_record['exclusion_class'] = 'performance_anomaly'
    case.terminal.campaign_record['valid'] = False
    case.terminal.campaign_record['session_median'] = None
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()
    with pytest.raises(evidence.TerminalEvidenceError, match='excluded_reason'):
        _seal(case)

@pytest.mark.parametrize(('field', 'replacement', 'message'), [('attempt_id', 'other-attempt', 'attempt_id'), ('cell_id', 'other-cell', 'cell_id'), ('configuration_id', 'other-config', 'configuration_id'), ('holdout_id', 'other-holdout', 'holdout_id'), ('records', 9, 'records'), ('retry_ordinal', 1, 'retry_ordinal'), ('threads', 9, 'threads')])
def test_authoritative_campaign_identity_is_rechecked(field: str, replacement: object, message: str) -> None:
    case = _case()
    case.terminal.campaign_record[field] = replacement
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()
    with pytest.raises(evidence.TerminalEvidenceError, match=message):
        _seal(case)

def test_workload_authority_is_rechecked_without_plaintext_disclosure() -> None:
    case = _case()
    case.terminal.campaign_record['workload'] = {**case.reservation.workload, 'ycsb_rratio': '20'}
    case.terminal.raw_output_bytes = profile8b.serialize_session_line(case.terminal.campaign_record)
    case.terminal.report_sha256 = hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()
    with pytest.raises(evidence.TerminalEvidenceError, match='workload'):
        _seal(case)
    clean_document = _seal().document
    assert 'workload' not in clean_document['campaign_record']
    assert 'workload_sha256' in clean_document

def test_campaign_probe_and_observations_are_digest_bound() -> None:
    for field in ('probe_before', 'probe_after', 'rep_observations'):
        case = _case()
        if field == 'rep_observations':
            case.terminal.campaign_record[field][0]['throughput'] = 99.0
        else:
            case.terminal.campaign_record[field]['stdout'] = 'changed'
        case.terminal.raw_output_bytes = profile8b.serialize_session_line(case.terminal.campaign_record)
        case.terminal.report_sha256 = hashlib.sha256(case.terminal.raw_output_bytes).hexdigest()
        with pytest.raises(evidence.TerminalEvidenceError, match=field):
            _seal(case)

def test_constructor_and_dataclasses_replace_attacks_are_closed() -> None:
    with pytest.raises(TypeError):
        evidence.SealedTerminalEvidenceDraft(b'{}')
    with pytest.raises(TypeError):
        evidence.ValidatedTerminalEvidence(b'{}', object())
    draft = _seal()
    validated = _promote(draft)
    with pytest.raises((TypeError, ValueError)):
        replace(draft, _canonical_bytes=b'{}')
    with pytest.raises((TypeError, ValueError)):
        replace(validated, _canonical_bytes=b'{}')

def test_require_never_promotes_a_draft() -> None:
    with pytest.raises(evidence.TerminalEvidenceError, match='invalid exact type'):
        evidence.require_sealed_terminal_evidence(_seal())

def test_validated_sha256_and_canonical_bytes_are_recomputed() -> None:
    validated = _promote(_seal())
    checked = evidence.require_sealed_terminal_evidence(validated)
    assert checked is validated
    assert validated.sha256 == hashlib.sha256(validated.canonical_bytes).hexdigest()
    assert validated.canonical_bytes == core.canonical_json_bytes(validated.document)

def test_duplicate_key_and_non_object_json_are_rejected_directly() -> None:
    duplicated = b'{"schema_version":1,"schema_version":2}'
    with pytest.raises(evidence.TerminalEvidenceError, match='duplicate JSON key'):
        _draft_from_bytes(duplicated).document
    with pytest.raises(evidence.TerminalEvidenceError, match='exact object'):
        _draft_from_bytes(b'[]').document

def test_canonical_bytes_reject_lf_and_spacing_without_other_validation() -> None:
    draft = _seal()
    assert not draft.canonical_bytes.endswith(b'\n')
    assert draft.canonical_bytes == core.canonical_json_bytes(draft.document)
if __name__ == '__main__':
    raise SystemExit(pytest.main(['-q', str(Path(__file__).resolve())]))
