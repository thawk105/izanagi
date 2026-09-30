"""Closed lock order intake and witness history projection."""
import json
import contextlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import p3_s4_loop_lock_order as D  # noqa: E402
from orchestrator.campaign import patchharness  # noqa: E402
from orchestrator.campaign.silo_lock_order_model_gate import (  # noqa: E402
    ModelDecision, ModelRegistry, check_model_result,
)
from tools.cc_model_checker.schema import validate_counterexample  # noqa: E402
from orchestrator.codex_roles.policy import ROLE_FORBIDDEN_KEY_TOKENS, _contains_token, _normalise_key  # noqa: E402

DIGEST = 'sha256:' + 'a' * 64


def _model():
    result = {'schema': 'cc-model-result/1', 'axis': 'silo-lock-order-policy',
              'specification_digest': DIGEST, 'scenarios': [{
                  'scenario_id': 'L1', 'complete': True, 'stop_reason': 'exhausted',
                  'explored_configurations': 1, 'witness_reached': True,
                  'counterexamples': []}]}
    registry = ModelRegistry(DIGEST, {'L1': {
        'expected_configurations': 1, 'witness_required': True}})
    return check_model_result(json.dumps(result).encode(), registry)


def _verify(required=True):
    return {'verdict': 'serializable', 'certified': True,
            'gate_witness': {'meaning_version': 2, 'required': required,
                             'counts': {key: 0 for key in D._COUNTS},
                             'occurrence': {}, 'D5': 'pass'}}


def _proposal():
    return D.LockOrderProposal('return true;', None, 'initial')


def test_m12_required_false_cannot_certify():
    row = D.history_row_from_verification(_verify(False), iteration=1,
        proposal=_proposal(), model=_model())
    assert row['outcome'] == 'rejected'
    assert row['reject_code'] == 'gate-witness-not-required'


def test_required_version_d5_and_certified_all_needed():
    good = D.history_row_from_verification(_verify(), iteration=1,
        proposal=_proposal(), model=_model())
    assert good['outcome'] == 'certified' and good['reject_code'] is None
    for field, value, code in (
            ('meaning_version', 1, 'gate-witness-version'),
            ('D5', 'fail', 'gate-d5-not-pass')):
        data = _verify()
        data['gate_witness'][field] = value
        assert D.history_row_from_verification(data, iteration=1,
            proposal=_proposal(), model=_model())['reject_code'] == code
    data = _verify()
    data['certified'] = False
    assert D.history_row_from_verification(data, iteration=1,
        proposal=_proposal(), model=_model())['reject_code'] == 'verifier-not-certified'


def test_gate_violation_projection_is_closed_and_counted():
    data = _verify()
    data['gate_witness']['counts']['D2b_ii'] = 3
    row = D.history_row_from_verification(data, iteration=1,
        proposal=_proposal(), model=_model())
    digest = row['verifier_digest']
    assert set(digest) == D._VERIFIER_KEYS
    assert set(digest['gate_counts']) == set(D._COUNTS)
    assert digest['gate_counts']['D2b_ii'] == 3
    assert digest['D5'] == 'pass'


def test_m11_counterexample_projection_has_exact_keys():
    example = {'schema': 'cc-model-counterexample/1',
               'specification_digest': DIGEST, 'scenario_id': 'L1',
               'judgment_id': 'J1', 'steps': [{
                   'number': 1, 'thread': 'T1', 'name': 'read', 'key': 'K1',
                   'version_id': 'V1', 'observed_value': None}],
               'cycle_txns': None, 'cycle_edges': None, 'rule_ids': ['R1']}
    validated = validate_counterexample(example)
    model = ModelDecision(False, 'model-counterexample', DIGEST, ('L1',),
                          (validated,))
    row = D.history_row_from_verification(_verify(), iteration=1,
        proposal=_proposal(), model=model)
    assert set(row) == D.HISTORY_KEYS
    assert row['counterexamples'] == [{
        'scenario_id': 'L1', 'judgment_id': 'J1', 'rule_ids': ['R1']}]
    assert set(row['counterexamples'][0]) == {'scenario_id', 'judgment_id', 'rule_ids'}


def test_history_keys_avoid_role_forbidden_tokens():
    for key in D.HISTORY_KEYS | D._VERIFIER_KEYS:
        normalized = _normalise_key(key)
        for role, tokens in ROLE_FORBIDDEN_KEY_TOKENS.items():
            assert not any(_contains_token(normalized, token) for token in tokens), (role, key)


def test_intake_rejects_duplicate_and_extra_keys():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'proposal.json'
        path.write_text('{"coder":{},"coder":{},"auditor":{}}')
        try:
            D.load_lock_order_proposal(path)
        except ValueError:
            pass
        else:
            raise AssertionError('duplicate key passed')
        path.write_text(json.dumps({'coder': {'axis': 'silo-lock-order-policy',
            'implementation': 'return true;', 'extra': 1}, 'auditor': {}}))
        try:
            D.load_lock_order_proposal(path)
        except ValueError:
            pass
        else:
            raise AssertionError('extra key passed')


def test_named_control_reads_initial_source():
    proposal = D.load_lock_order_proposal(None, named_control='version_desc')
    assert proposal.origin == 'initial'
    assert proposal.implementation == (ROOT / D.axis.HAND_POLICY_DIR /
        D.axis.HAND_POLICIES['version_desc']).read_text()


def _iteration_patches(tmp, *, registered=True, campaign=None):
    stack = contextlib.ExitStack()
    stack.enter_context(patch.object(patchharness, 'applied',
                                     lambda *_a, **_k: contextlib.nullcontext()))
    stack.enter_context(patch.object(D, 'order_gate',
                                     lambda *_a, **_k: (SimpleNamespace(passed=True), 'diff')))
    stack.enter_context(patch.object(D.P, '_require_perf_identity', lambda *_a: None))
    stack.enter_context(patch.object(D.P, '_measurement_options', lambda **_k: {}))
    stack.enter_context(patch.object(D.env_contract, 'authorize', lambda *_a: object()))
    stack.enter_context(patch.object(D.ident, 'campaign_id', lambda *_a: 'fixture-campaign'))
    stack.enter_context(patch.object(D.axis, 'MODEL_SPECIFICATION_DIGEST',
                                     DIGEST if registered else None))
    stack.enter_context(patch.object(D.axis, 'MODEL_SCENARIOS',
                                     {'L1': {'expected_configurations': 1,
                                             'witness_required': True}} if registered else None))
    if campaign is not None:
        stack.enter_context(patch.object(D, 'run_campaign', campaign))
    layout = SimpleNamespace(root=tmp, ensure=lambda: None)
    contract = SimpleNamespace(env_tag='linux-baremetal', clocks_per_us=1,
                               numactl=())
    return stack, layout, contract


def _model_bytes():
    return json.dumps({'schema': 'cc-model-result/1',
                       'axis': 'silo-lock-order-policy',
                       'specification_digest': DIGEST,
                       'scenarios': [{'scenario_id': 'L1', 'complete': True,
                                      'stop_reason': 'exhausted',
                                      'explored_configurations': 1,
                                      'witness_reached': True,
                                      'counterexamples': []}]}).encode()


def test_missing_model_rejects_before_build_and_records_history():
    with tempfile.TemporaryDirectory() as tmp:
        def forbidden(*_a, **_k):
            raise AssertionError('build reached')
        stack, layout, contract = _iteration_patches(tmp, registered=True,
                                                       campaign=forbidden)
        with stack:
            row = D.run_one_iteration(object(), object(), _proposal(), tmp,
                None, layout=layout, iteration=1, compiler='c++',
                scratch_dir=tmp, build_context=object(), contract=contract)
        assert row['reject_code'] == 'model-result-missing'
        assert json.loads((Path(tmp) / D.HISTORY_NAME).read_text()) == row


def test_run_campaign_spy_requires_gate_witness_and_skips_terminal_variant():
    with tempfile.TemporaryDirectory() as tmp:
        calls = []
        def campaign(*args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(results=[], skipped=1, identity_skipped=0,
                                   skipped_variants=['v1'])
        stack, layout, contract = _iteration_patches(tmp, campaign=campaign)
        with stack:
            row = D.run_one_iteration(object(), object(), _proposal(), tmp,
                _model_bytes(), layout=layout, iteration=1, compiler='c++',
                scratch_dir=tmp, build_context=object(), contract=contract)
        assert len(calls) == 1
        assert calls[0][1]['require_gate_witness'] is True
        assert calls[0][1]['declared_use_class'] == 'exploration'
        assert row['outcome'] == 'skipped' and row['reject_code'] == 'campaign-skipped'
        assert row['variant_id'] == 'v1'
        assert json.loads((Path(tmp) / D.HISTORY_NAME).read_text()) == row


def test_coder_input_rejects_free_text_history():
    with tempfile.TemporaryDirectory() as tmp:
        row = D.history_row_from_verification(_verify(), iteration=1,
            proposal=_proposal(), model=_model())
        row['counterexamples'] = [{'scenario_id': 'L1',
                                   'judgment_id': 'free text with spaces',
                                   'rule_ids': []}]
        (Path(tmp) / D.HISTORY_NAME).write_text(json.dumps(row) + '\n')
        try:
            D.make_lock_order_coder_input(SimpleNamespace(root=tmp))
        except ValueError:
            pass
        else:
            raise AssertionError('free text passed')


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
