"""Policy driver schema, gate order, and coder input boundaries."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import p3_s4_loop_policy as P
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign.auditor_gate import AuditorGateFailure
from orchestrator.campaign.diff_quarantine import DiffRejectSubtype
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY, VERIFY_LEGACY_PLUS_PERFORMANCE
from orchestrator.campaign.silo_policy_compile import check_policy_body, find_compiler
from orchestrator.campaign.auditor_gate import AuditorVerdict, compute_diff_digest
from orchestrator.campaign.build_admission import BuildAdmissionError

BODY = (ROOT / 'orchestrator/campaign/silo_function_policy_hand/abort0.cpp').read_text()
GOOD = BODY.replace('return 0u;', 'return 1u;')


def _source(tmp_path):
    path = tmp_path / P.axis.SOURCE_REL
    path.parent.mkdir(parents=True)
    path.write_text('// EVOLVE-BLOCK-BEGIN silo-function-policy\n'
                    '#if SILO_POLICY_VARIANT\n' + BODY +
                    '#else\n#endif\n'
                    '// EVOLVE-BLOCK-END silo-function-policy\n')
    return path


def _proposal(tmp_path, *, form='cpp', change=None):
    coder = {'axis': P.axis.MARKER_ID, 'implementation': BODY}
    if form == 'ir':
        from dataclasses import fields, is_dataclass
        from orchestrator.campaign.silo_policy_ir import degenerate_policy
        def tagged(value):
            if is_dataclass(value):
                return {'kind': type(value).__name__, **{f.name: tagged(getattr(value, f.name)) for f in fields(value)}}
            if type(value) is tuple:
                return [tagged(x) for x in value]
            return value
        coder.pop('implementation')
        coder['ir'] = tagged(degenerate_policy())
    document = {'coder': coder, 'auditor': {'verdict': 'pass', 'diff_digest': 'a' * 64}}
    if change:
        change(document)
    path = tmp_path / 'proposal.json'
    path.write_text(json.dumps(document), encoding='utf-8')
    return path


def test_proposal_schema_both_forms_and_scalar_rejections(tmp_path):
    for form in ('cpp', 'ir'):
        path = _proposal(tmp_path, form=form)
        proposal, auditor = P.load_proposal_file(path, form=form)
        assert proposal.implementation and auditor.verdict == 'pass'
        for change in (
            lambda d: d.pop('coder'), lambda d: d.pop('auditor'),
            lambda d: d['coder'].pop('implementation' if form == 'cpp' else 'ir'),
            lambda d: d.update(planner={}), lambda d: d.update(value=1),
            lambda d: d.update(prior_critic_reverse=False),
            lambda d: d['coder'].update(extra=True),
            lambda d: d['coder'].update(axis='other'),
            lambda d: d['coder'].update(confidence=True),
            lambda d: d['auditor'].update(verdict='other'),
            lambda d: d['auditor'].update(diff_digest=''),
        ):
            path = _proposal(tmp_path, form=form, change=change)
            with pytest.raises((ValueError, KeyError)):
                P.load_proposal_file(path, form=form)
        with pytest.raises((ValueError, KeyError)):
            P.load_proposal_file(_proposal(tmp_path, form=form), form='ir' if form == 'cpp' else 'cpp')
    path.write_text('{"coder":{},"coder":{},"auditor":{}}', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate'):
        P.load_proposal_file(path, form='cpp')


def test_policy_loader_uses_26_ceiling(tmp_path):
    for kind in range(22, 27):
        path = _proposal(tmp_path, change=lambda d: d['auditor'].update(
            verdict='reject', violations=[{'type': kind}]))
        _proposal_value, auditor = P.load_proposal_file(path, form='cpp')
        assert auditor.violations == [{'type': kind}]
    path = _proposal(tmp_path, change=lambda d: d['auditor'].update(
        verdict='reject', violations=[{'type': 27}]))
    with pytest.raises(AuditorGateFailure):
        P.load_proposal_file(path, form='cpp')
    path.write_text('{"coder":{"axis":"silo-function-policy","axis":"silo-function-policy","implementation":"x"},"auditor":{"verdict":"pass","diff_digest":"x"}}', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate'):
        P.load_proposal_file(path, form='cpp')


def test_cfg_and_coder_input_projection(tmp_path, monkeypatch):
    for form in ('cpp', 'ir'):
        cfg = P.default_cfg(form=form)
        assert cfg.ccbench_commit == P.axis.PIN
        assert cfg.search_config['axis'] == P.axis.MARKER_ID
        assert cfg.search_config['form'] == form
        assert cfg.search_config[SEARCH_CONFIG_VERIFY_KEY] == VERIFY_LEGACY_PLUS_PERFORMANCE
    perf = P.default_perf()
    assert perf == L.calibrated_perf('write-heavy')
    layout = CampaignLayout(str(tmp_path))
    projection = tmp_path / 'projection.json'
    projection.write_text(json.dumps({'binary': False, 'scope': 'scope', 'excluded': ['private']}))
    monkeypatch.setattr(P, 'PROJECTION_PATH', projection)
    (tmp_path / P.HISTORY_NAME).write_text(json.dumps({
        'iteration': 1, 'implementation': BODY, 'ir': None,
        'outcome': 'rejected', 'reject_subtype': 'policy-grammar',
        'reject_rule_id': 'rule', 'verifier_digest': None,
        'justification': 'private'}) + '\n')
    payload = P.make_policy_coder_input(layout, baseline={'throughput_tps': 1, 'abort_rate_pct': 2})
    assert set(payload) == {'leakproof_context', 'policy_spec', 'baseline', 'recon_projection', 'self_history'}
    assert payload['recon_projection'] == {'binary': False, 'scope': 'scope'}
    assert 'justification' not in payload['self_history'][0]
    for bad in ({'binary': 0, 'scope': 'scope', 'excluded': []},
                {'binary': False, 'scope': 'scope', 'excluded': [], 'extra': 1}):
        projection.write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            P.make_policy_coder_input(layout, baseline={'throughput_tps': 1, 'abort_rate_pct': 2})


def test_real_grammar_reject_precedes_translation_unit(tmp_path):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('g++ unavailable')
    bad = GOOD.replace('return 1u;', 'uint32_t x = 1u; x++; return x;')
    grammar, compiled = check_policy_body(bad, compiler=compiler, scratch_dir=str(tmp_path))
    assert not grammar.accepted and compiled is None
    # Verify the fixture is otherwise accepted by the actual C++ compiler.
    from orchestrator.campaign.silo_policy_compile import compile_policy
    assert compile_policy(bad, compiler=compiler, scratch_dir=str(tmp_path)).accepted


def test_real_translation_unit_only_rejection(tmp_path):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('g++ unavailable')
    unused_local = GOOD.replace('return 1u;', 'uint32_t unused = 1u; return 1u;')
    grammar, compiled = check_policy_body(
        unused_local, compiler=compiler, scratch_dir=str(tmp_path))
    assert grammar.accepted
    assert compiled is not None and not compiled.accepted


def test_policy_gate_digest_and_no_write_on_reject(tmp_path):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('g++ unavailable')
    source = _source(tmp_path)
    original = source.read_bytes()
    bad = GOOD.replace('return 1u;', 'uint32_t x = 1u; x++; return x;')
    result, _diff = P.policy_gate(str(tmp_path), bad, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert not result.passed
    assert result.subtype is DiffRejectSubtype.POLICY_GRAMMAR
    assert source.read_bytes() == original
    unused_local = GOOD.replace('return 1u;', 'uint32_t unused = 1u; return 1u;')
    result, _diff = P.policy_gate(str(tmp_path), unused_local, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert not result.passed
    assert result.subtype is DiffRejectSubtype.POLICY_COMPILE
    assert source.read_bytes() == original
    result, diff = P.policy_gate(str(tmp_path), GOOD, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert result.passed
    mismatch = AuditorVerdict('pass', '0' * 64)
    with pytest.raises(AuditorGateFailure):
        P.policy_gate(str(tmp_path), GOOD, mismatch,
            compiler=compiler, scratch_dir=str(tmp_path), write=True)
    assert source.read_bytes() == original
    accepted = AuditorVerdict('pass', compute_diff_digest(diff))
    result, rebound = P.policy_gate(str(tmp_path), GOOD, accepted,
        compiler=compiler, scratch_dir=str(tmp_path), write=True)
    assert result.passed and compute_diff_digest(rebound) == accepted.diff_digest
    assert source.read_bytes() != original


def test_budget_stop_preserves_checkpoint_without_candidate_work(tmp_path):
    layout = CampaignLayout(str(tmp_path))
    layout.ensure()
    state = L.LoopState(iteration=L.MAX_ITER, start_wall=0)
    L.save_loop_state(layout, state)
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    out = P.drive_iteration(P.default_cfg(form='cpp'), P.default_perf(),
        P.Proposal(BODY, None, ''), AuditorVerdict('pass', 'a' * 64),
        str(tmp_path), False, compiler='unused', scratch_dir=str(tmp_path),
        build_context=context, layout=layout)
    assert out['outcome'] == 'stopped-before' and out['iteration'] == L.MAX_ITER
    assert L.load_loop_state(layout).iteration == L.MAX_ITER


def test_cli_requires_coder_build_opt_in_before_candidate_read(tmp_path):
    with pytest.raises(BuildAdmissionError):
        P.main(['--form', 'cpp', '--run-iteration', str(tmp_path / 'absent.json')])
