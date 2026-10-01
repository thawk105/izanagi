"""Bounded model result admission and mutation witnesses M6--M10."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign.silo_lock_order_model_gate import (  # noqa: E402
    ModelRegistry, check_model_result,
)

DIGEST = 'sha256:' + 'a' * 64
OTHER = 'sha256:' + 'b' * 64


def _registry():
    return ModelRegistry(DIGEST, {'L1': {
        'expected_configurations': 3, 'witness_required': True}})


def _result():
    return {'schema': 'cc-model-result/1', 'axis': 'silo-lock-order-policy',
            'specification_digest': DIGEST, 'scenarios': [{
                'scenario_id': 'L1', 'complete': True, 'stop_reason': 'exhausted',
                'explored_configurations': 3, 'witness_reached': True,
                'counterexamples': []}]}


def _check(value, registry=None):
    return check_model_result(json.dumps(value).encode(), registry or _registry())


def _counterexample():
    return {'schema': 'cc-model-counterexample/1',
            'specification_digest': DIGEST, 'scenario_id': 'L1',
            'judgment_id': 'J1', 'steps': [{
                'number': 1, 'thread': 'T1', 'name': 'write', 'key': 'K1',
                'version_id': 'V1', 'observed_value': None}],
            'cycle_txns': ['T1', 'T2'], 'cycle_edges': [
                {'source': 'T1', 'target': 'T2', 'kind': 'rw', 'key': 'K1',
                 'from_version': 'V1', 'to_version': 'V2'},
                {'source': 'T2', 'target': 'T1', 'kind': 'rw', 'key': 'K1',
                 'from_version': 'V2', 'to_version': 'V1'}], 'rule_ids': ['R1']}


def test_m6_unregistered_registry_rejected():
    assert _check(_result(), ModelRegistry(None, None)).reject_code == 'model-unregistered'


def test_m7_result_digest_cannot_supply_expectation():
    value = _result()
    value['specification_digest'] = OTHER
    assert _check(value).reject_code == 'model-digest-mismatch'


def test_m8_complete_max_states_is_incomplete():
    value = _result()
    value['scenarios'][0]['stop_reason'] = 'max_states'
    assert _check(value).reject_code == 'model-incomplete'


def test_m9_required_scenario_missing():
    value = _result()
    value['scenarios'] = []
    assert _check(value).reject_code == 'model-scenario-missing'


def test_m10_counterexample_rejected():
    value = _result()
    value['scenarios'][0]['counterexamples'] = [_counterexample()]
    result = _check(value)
    assert result.reject_code == 'model-counterexample'
    assert len(result.counterexamples) == 1


def test_unregistered_scenario_exists_but_its_counterexample_rejects():
    value = _result()
    value['scenarios'].append({**value['scenarios'][0],
                               'scenario_id': 'EXTRA', 'counterexamples': []})
    assert _check(value).passed
    example = _counterexample()
    example['scenario_id'] = 'EXTRA'
    value['scenarios'][1]['counterexamples'] = [example]
    assert _check(value).reject_code == 'model-counterexample'


def test_matching_complete_model_passes():
    result = _check(_result())
    assert result.passed and result.reject_code is None and result.scenario_ids == ('L1',)


def test_missing_and_malformed_result_fail_closed():
    assert check_model_result(None, _registry()).reject_code == 'model-result-missing'
    for payload in (b'{"schema":1,"schema":2}',
                    b'{"x":NaN}', json.dumps({**_result(), 'extra': 1}).encode()):
        assert check_model_result(payload, _registry()).reject_code == 'model-result-invalid'


def test_coverage_witness_and_extra_scenarios():
    value = _result()
    value['scenarios'][0]['explored_configurations'] = 2
    assert _check(value).reject_code == 'model-coverage-mismatch'
    value['scenarios'][0]['explored_configurations'] = 3
    value['scenarios'][0]['witness_reached'] = False
    assert _check(value).reject_code == 'model-witness-missing'
    value['scenarios'][0]['witness_reached'] = True
    value['scenarios'].append({**value['scenarios'][0], 'scenario_id': 'EXTRA'})
    assert _check(value).passed and _check(value).scenario_ids == ('EXTRA', 'L1')


def test_duplicate_scenario_and_counterexample_identity_rejected():
    value = _result()
    value['scenarios'].append(dict(value['scenarios'][0]))
    assert _check(value).reject_code == 'model-result-invalid'
    value['scenarios'].pop()
    example = _counterexample()
    example['scenario_id'] = 'L2'
    value['scenarios'][0]['counterexamples'] = [example]
    assert _check(value).reject_code == 'model-result-invalid'


def test_bounded_result_and_counterexample_arrays():
    value = _result()
    value['scenarios'] = [{**value['scenarios'][0], 'scenario_id': f'E{i}'}
                          for i in range(4097)]
    assert _check(value).reject_code == 'model-result-invalid'
    value = _result()
    value['scenarios'][0]['counterexamples'] = [_counterexample() for _ in range(65)]
    assert _check(value).reject_code == 'model-result-invalid'


def test_counterexample_extra_field_and_scenario_field_rejected():
    value = _result()
    value['scenarios'][0]['counterexamples'] = [{**_counterexample(), 'note': 'free text'}]
    assert _check(value).reject_code == 'model-result-invalid'
    value = _result()
    value['scenarios'][0]['extra'] = 1
    assert _check(value).reject_code == 'model-result-invalid'


def _run():
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn(); print('PASS', name)
            except Exception as exc:
                failed += 1; print('FAIL', name, repr(exc))
    return int(failed != 0)


if __name__ == '__main__':
    sys.exit(_run())
