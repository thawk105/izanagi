"""Policy driver schema, gate order, and coder input boundaries."""
import json
import contextlib
from dataclasses import replace
from pathlib import Path
import os
import subprocess
import sys
import time

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
from orchestrator.campaign.model import Genome, WalRecord, STAGE_ABORT
from orchestrator.campaign.model import STAGE_BENCH_DONE, STAGE_BUILD_START
from orchestrator.campaign.pipeline import EvalResult, variant_id
from orchestrator.verifier.model import Anomaly, Integrity, VerifyResult

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


def test_preview_accepts_only_closed_coder(tmp_path):
    for form in ('cpp', 'ir'):
        path = _proposal(tmp_path, form=form, change=lambda d: d.pop('auditor'))
        proposal, auditor = P.load_proposal_file(path, form=form, preview=True)
        assert proposal.implementation and auditor is None
        for change in (lambda d: d.update(auditor={}),
                       lambda d: d.update(extra=1),
                       lambda d: d['coder'].update(extra=1)):
            path = _proposal(tmp_path, form=form, change=lambda d: (d.pop('auditor'), change(d)))
            with pytest.raises(ValueError):
                P.load_proposal_file(path, form=form, preview=True)
    path.write_text('{"coder":{"axis":"x","axis":"x"}}')
    with pytest.raises(ValueError, match='duplicate'):
        P.load_proposal_file(path, form='cpp', preview=True)


def test_policy_gate_veto_checks_types_22_through_26(tmp_path):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('g++ unavailable')
    source = _source(tmp_path)
    original = source.read_bytes()
    preview, diff = P.policy_gate(str(tmp_path), GOOD, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert preview.passed
    for kind in range(22, 27):
        verdict = AuditorVerdict('reject', compute_diff_digest(diff),
            violations=[{'type': kind}], max_violation_type=26)
        result, _ = P.policy_gate(str(tmp_path), GOOD, verdict,
            compiler=compiler, scratch_dir=str(tmp_path), write=True)
        assert not result.passed
        assert result.digest['subtype'] == 'auditor-violation'
        assert source.read_bytes() == original


def test_cfg_and_coder_input_projection(tmp_path, monkeypatch):
    for form in ('cpp', 'ir'):
        cfg = P.default_cfg(form=form)
        assert cfg.ccbench_commit == P.axis.PIN
        assert cfg.search_config['axis'] == P.axis.MARKER_ID
        assert cfg.search_config['form'] == form
        assert cfg.search_config[SEARCH_CONFIG_VERIFY_KEY] == VERIFY_LEGACY_PLUS_PERFORMANCE
    perf = P.default_perf()
    assert perf == L.calibrated_perf('write-heavy')
    assert cfg.search_config['perf'] == P._perf_identity(perf)
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
    assert set(payload['self_history'][0]) == {
        'iteration', 'implementation', 'ir', 'outcome', 'reject_subtype',
        'reject_rule_id', 'verifier_digest'}
    for bad in ({'binary': 0, 'scope': 'scope', 'excluded': []},
                {'binary': False, 'scope': 'scope', 'excluded': [], 'extra': 1}):
        projection.write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            P.make_policy_coder_input(layout, baseline={'throughput_tps': 1, 'abort_rate_pct': 2})


def test_perf_identity_rejects_changed_runtime_before_layout(tmp_path):
    cfg = P.default_cfg(form='cpp')
    perf = P.default_perf()
    changed = replace(perf, threads=perf.threads + 1)
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    with pytest.raises(ValueError, match='performance configuration'):
        P.drive_iteration(cfg, changed, P.Proposal(BODY, None, ''), None,
            str(tmp_path), False, compiler='unused', scratch_dir=str(tmp_path),
            build_context=context, layout=CampaignLayout(str(tmp_path / 'campaign')))
    assert not (tmp_path / 'campaign').exists()


def test_dry_pass_returns_without_history_or_admitted_view(tmp_path, monkeypatch):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('g++ unavailable')
    _source(tmp_path)
    from orchestrator.campaign import patchharness
    monkeypatch.setattr(patchharness, 'applied',
                        lambda *_a, **_k: contextlib.nullcontext())
    layout = CampaignLayout(str(tmp_path / 'campaign'))
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    out = P.drive_iteration(P.default_cfg(form='cpp'), P.default_perf(),
        P.Proposal(GOOD, None, ''), None, str(tmp_path), False,
        compiler=compiler, scratch_dir=str(tmp_path), build_context=context,
        layout=layout)
    assert out['outcome'] == 'dry-pass' and out['ran']
    assert not (Path(layout.root) / P.HISTORY_NAME).exists()
    assert not Path(layout.wal_file).exists()
    assert not (Path(layout.root) / 'silo_policy_loop_digest.txt').exists()
    bad = GOOD.replace('return 1u;', 'uint32_t x = 1u; x++; return x;')
    rejected = P.drive_iteration(P.default_cfg(form='cpp'), P.default_perf(),
        P.Proposal(bad, None, ''), None, str(tmp_path), False,
        compiler=compiler, scratch_dir=str(tmp_path), build_context=context,
        layout=layout)
    assert rejected['outcome'] == 'rejected'
    assert not Path(layout.wal_file).exists()
    assert not (Path(layout.root) / P.HISTORY_NAME).exists()


def test_critic_output_only_with_emit_and_six_field_projection(tmp_path, capsys):
    critic = tmp_path / 'critic.txt'
    critic.write_text('## attribution\nA\n## recommend\nB\n## avoid\nC\n## uncertainty\nD\n')
    with pytest.raises(SystemExit) as rejected:
        P.main(['--form', 'cpp', '--preview-diff', str(tmp_path / 'absent'),
                '--critic-output', str(critic)])
    assert rejected.value.code == 2
    assert P.main(['--form', 'cpp', '--emit-coder-input',
                   '--baseline-throughput-tps', '1', '--baseline-abort-rate-pct', '2',
                   '--critic-output', str(critic)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['critic_diagnosis'] == L.k2_critic_diagnosis_from_bytes(critic.read_bytes())


def test_history_projects_wal_reason_workload_and_integrity_without_notes(tmp_path, monkeypatch):
    layout = CampaignLayout(str(tmp_path))
    verify = VerifyResult('', True, integrity=Integrity(lock_coverage_violations=1),
                          n_txns=1)
    result = EvalResult(Genome('silo', dict(P.BASE)), 'variant', False, True,
                        verdict='indeterminate', notes=['untrusted free text'],
                        build_attempt_id='attempt', verify_result=verify)
    records = [WalRecord('variant', STAGE_ABORT, P.ENV_TAG, 0,
                         {'build_attempt_id': 'attempt', 'reason': 'indeterminate',
                          'workload': {'tag': 'performance'}})]
    monkeypatch.setattr(P.wal, 'read_records', lambda _layout: records)
    outcome, digest = P._result_history(layout, result)
    assert outcome == 'indeterminate'
    assert digest['workload_tag'] == 'performance'
    assert digest['integrity_reason_codes'] == ['lock_coverage_violations']
    assert 'untrusted free text' not in json.dumps(digest)
    records[0].payload['reason'] = 'trace-timeout'
    assert P._result_history(layout, result)[0] == 'trace-timeout'
    records[0].payload['reason'] = 'build-error'
    assert P._result_history(layout, result)[0] == 'build-error'


def test_exception_reason_is_closed_before_coder_input(tmp_path, monkeypatch):
    layout = CampaignLayout(str(tmp_path))
    result = EvalResult(Genome('silo', dict(P.BASE)), 'variant', False, True,
                        build_attempt_id='attempt')
    private = 'eval-exception: ValueError: arbitrary private exception text'
    monkeypatch.setattr(P.wal, 'read_records', lambda _layout: [
        WalRecord('variant', STAGE_ABORT, P.ENV_TAG, 0,
                  {'build_attempt_id': 'attempt', 'reason': private})])
    outcome, digest = P._result_history(layout, result)
    assert outcome == digest['reason'] == 'eval-exception'
    assert P._reason_code('unrecognized private reason') == 'other'
    assert P._reason_code('build-error: private suffix') == 'other'
    P._append_history(layout, 1, P.Proposal(BODY, None, ''),
                      {'outcome': outcome, 'verifier_digest': digest})
    projection = tmp_path / 'projection.json'
    projection.write_text(json.dumps({'binary': False, 'scope': 'scope', 'excluded': []}))
    monkeypatch.setattr(P, 'PROJECTION_PATH', projection)
    payload = P.make_policy_coder_input(layout,
        baseline={'throughput_tps': 1, 'abort_rate_pct': 2})
    assert private not in json.dumps(payload)
    assert payload['self_history'][0]['outcome'] == 'eval-exception'


def test_anomaly_digest_has_stable_first_eight_and_witness_count(tmp_path, monkeypatch):
    layout = CampaignLayout(str(tmp_path))
    anomalies = [Anomaly([i, i], 'G2', []) for i in range(11, 0, -1)]
    verify = VerifyResult('', False, anomalies=anomalies, total_cycles=39124)
    result = EvalResult(Genome('silo', dict(P.BASE)), 'variant', False, True,
                        build_attempt_id='attempt', verify_result=verify)
    monkeypatch.setattr(P.wal, 'read_records', lambda _layout: [])
    _outcome, digest = P._result_history(layout, result)
    assert digest['witness_count'] == 11
    assert digest['total_cycles'] == 39124
    assert len(digest['anomalies']) == 8
    assert all(set(item) == {'phenomenon', 'cycle', 'edges'} for item in digest['anomalies'])
    verify.anomalies.reverse()
    assert P._result_history(layout, result)[1]['anomalies'] == digest['anomalies']


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


def test_record_reject_records_only_real_gate_failure(tmp_path):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('g++ unavailable')
    source = _source(tmp_path)
    original = source.read_bytes()
    layout = CampaignLayout(str(tmp_path / 'campaign'))
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    cfg = P.default_cfg(form='cpp')
    cfg = P.ident.bind_admission_policy(cfg, context.policy)
    cfg = P.ident.bind_environment_contract(cfg, P.env_contract.lookup(P.ENV_TAG))
    state = L.LoopState(start_wall=time.time())
    passing, _ = P.policy_gate(str(tmp_path), GOOD, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert passing.passed
    with pytest.raises(ValueError, match='requires a rejected candidate'):
        P._record_rejected_gate(cfg, P.Proposal(GOOD, None, ''), passing,
                                layout, state, context)
    assert not Path(layout.root).exists()
    bad = GOOD.replace('return 1u;', 'uint32_t x = 1u; x++; return x;')
    rejected, _ = P.policy_gate(str(tmp_path), bad, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert not rejected.passed and rejected.digest['rule_id']
    out = P._record_rejected_gate(cfg, P.Proposal(bad, None, ''), rejected,
                                   layout, state, context)
    assert out['outcome'] == 'rejected' and out['iteration'] == 1
    assert source.read_bytes() == original
    assert L.load_loop_state(layout).iteration == 1
    assert 'diff-quarantine' in Path(layout.wal_file).read_text()
    row = json.loads((Path(layout.root) / P.HISTORY_NAME).read_text())
    assert row['outcome'] == 'rejected'
    assert row['reject_subtype'] == rejected.digest['subtype']
    assert row['reject_rule_id'] == rejected.digest['rule_id']


def test_record_reject_honors_budget_before_gate(tmp_path):
    layout = CampaignLayout(str(tmp_path / 'campaign'))
    layout.ensure()
    L.save_loop_state(layout, L.LoopState(iteration=L.MAX_ITER, start_wall=time.time()))
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    out = P.drive_record_reject(P.default_cfg(form='cpp'), P.default_perf(),
        P.Proposal(BODY, None, ''), str(tmp_path / 'absent'),
        compiler='unused', scratch_dir=str(tmp_path), build_context=context,
        layout=layout)
    assert out['outcome'] == 'stopped-before' and out['iteration'] == L.MAX_ITER
    assert not Path(layout.wal_file).exists()
    assert not (Path(layout.root) / P.HISTORY_NAME).exists()


def test_cli_requires_coder_build_opt_in_before_candidate_read(tmp_path):
    with pytest.raises(BuildAdmissionError):
        P.main(['--form', 'cpp', '--run-iteration', str(tmp_path / 'absent.json')])


def test_record_reject_cli_uses_coder_only_input_without_build_opt_in(tmp_path):
    with pytest.raises(FileNotFoundError):
        P.main(['--form', 'cpp', '--record-reject', str(tmp_path / 'absent.json')])
    path = _proposal(tmp_path, change=lambda d: d.pop('auditor'))
    proposal, auditor = P.load_proposal_file(path, form='cpp', preview=True)
    assert proposal.implementation == BODY and auditor is None
    path = _proposal(tmp_path)
    with pytest.raises(ValueError, match='only coder'):
        P.load_proposal_file(path, form='cpp', preview=True)


def test_campaign_environment_and_purpose_identity(monkeypatch):
    from orchestrator.campaign import site_policy
    baseline = P.default_cfg(form='cpp')
    pegasus = P.default_cfg(form='cpp', campaign_env='pegasus')
    bound = L._campaign_cfg_for_site(
        replace(baseline, bound_environment_contract=None),
        site_policy.PEGASUS_COMPUTE, _contract=P.env_contract.lookup('pegasus'))
    assert P.ident.campaign_id(pegasus) == P.ident.campaign_id(bound)
    assert len({str(P.ident.campaign_id(cfg)) for cfg in (
        baseline, pegasus,
        P.default_cfg(form='cpp', campaign_env='pegasus', evaluation_purpose='bootstrap'),
        P.default_cfg(form='cpp', campaign_env='pegasus', evaluation_purpose='r2'))}) == 4
    assert 'evaluation_purpose' not in baseline.search_config
    with pytest.raises(ValueError):
        P.default_cfg(form='cpp', evaluation_purpose='other')


def test_stock_genome_and_same_attempt_baseline(tmp_path, monkeypatch):
    layout = CampaignLayout(str(tmp_path))
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    result = EvalResult(Genome('silo', {}), 'variant', False, True,
                        fitness_tps=123, build_attempt_id='selected')
    records = [WalRecord('variant', STAGE_BENCH_DONE, P.ENV_TAG, i,
                {'build_attempt_id': attempt,
                 'leading_indicators': {'abort_rate': rate}})
               for i, (attempt, rate) in enumerate((('selected', .12), ('other', .89)))]
    monkeypatch.setattr(P.wal, 'read_records', lambda _layout: records)
    seen = []
    monkeypatch.setattr(P.ident, 'ensure_resumable_attempts', lambda *_a, **_k: None)
    def capture(_cfg, genomes, _perf, _env_tag, _clocks, **kwargs):
        seen.extend(genomes)
        assert kwargs['build_context'] is context
        assert 'capability_resolver' in kwargs
        return type('Summary', (), {'results': [result]})()
    monkeypatch.setattr(P, 'run_campaign', capture)
    out = P.run_stock_control(P.default_cfg(form='cpp'), P.default_perf(),
        str(tmp_path), layout=layout, build_context=context,
        contract=P.env_contract.lookup(P.ENV_TAG))
    assert seen[0].flags == {k: v for k, v in P.BASE.items() if k != P.axis.FLAG}
    assert out['abort_rate_pct'] == 12
    assert out['fitness_tps'] == 123


def test_stock_result_requires_stock_source_in_selected_attempt(tmp_path, monkeypatch):
    from orchestrator.campaign import source_digest
    layout = CampaignLayout(str(tmp_path))
    stock_genome = Genome('silo', {k: v for k, v in P.BASE.items() if k != P.axis.FLAG})
    stock_variant = variant_id(stock_genome)
    result = EvalResult(stock_genome, stock_variant, True, False,
                        fitness_tps=123, build_attempt_id='selected')
    summary = type('Summary', (), {'results': [result]})()
    records = [
        WalRecord(stock_variant, STAGE_BUILD_START, P.ENV_TAG, 0,
                  {'build_attempt_id': 'other', 'src_token': source_digest.STOCK}),
        WalRecord(stock_variant, STAGE_BUILD_START, P.ENV_TAG, 1,
                  {'build_attempt_id': 'selected', 'src_token': 'DIFFERENT'}),
        WalRecord(stock_variant, STAGE_BENCH_DONE, P.ENV_TAG, 2,
                  {'build_attempt_id': 'selected',
                   'leading_indicators': {'abort_rate': .12}}),
    ]
    monkeypatch.setattr(P.wal, 'read_records', lambda _layout: records)
    assert P._stock_result(layout, summary)['outcome'] == 'non-stock-source'
    records[1].payload['src_token'] = source_digest.STOCK
    assert P._stock_result(layout, summary)['outcome'] == 'certified-stock'
    result.variant = 'different-variant'
    assert P._stock_result(layout, summary)['outcome'] == 'non-stock-source'


def test_original_stock_source_is_classified_by_source_digest():
    from orchestrator.campaign import source_digest
    sub = ROOT / 'external/ccbench'
    compiler = find_compiler()
    if compiler is None or not (sub / '.git').exists():
        pytest.skip('CCBench submodule or compiler unavailable')
    genome = Genome('silo', {k: v for k, v in P.BASE.items() if k != P.axis.FLAG})
    assert source_digest.resolve(genome, P.axis.PIN,
                                 ccbench_dir=str(sub), cxx=compiler) == source_digest.STOCK


def test_measurement_rejects_mismatched_site_before_campaign(monkeypatch):
    monkeypatch.setattr(L, '_current_site', lambda: P.site_policy.OTHER)
    with pytest.raises(ValueError, match='environment differs'):
        P._measurement_contract('pegasus')


def _prepare_stock_cli(tmp_path, monkeypatch):
    from orchestrator.campaign import patchharness, p2_2
    monkeypatch.setattr(P, 'ROOT', tmp_path)
    monkeypatch.setattr(patchharness, 'assert_pinned_clean', lambda *_a: None)
    monkeypatch.setattr(p2_2, '_assert_single_tenant', lambda: None)
    monkeypatch.setattr(L, '_current_site', lambda: P.site_policy.OTHER)
    monkeypatch.setattr(P, 'exploration_campaign_layout',
                        lambda *_a: CampaignLayout(str(tmp_path / 'campaign')))


def test_stock_baseline_failure_returns_one_with_json(tmp_path, monkeypatch, capsys):
    _prepare_stock_cli(tmp_path, monkeypatch)
    monkeypatch.setattr(P, 'run_stock_control',
                        lambda *_a, **_k: {'outcome': 'aborted'})
    assert P.main(['--form', 'cpp', '--no-isolate-worktree', '--stock-baseline']) == 1
    assert json.loads(capsys.readouterr().out) == {'outcome': 'aborted'}


def test_stock_cli_preserves_environment_prefix_and_stderr_log(tmp_path, monkeypatch, capsys):
    _prepare_stock_cli(tmp_path, monkeypatch)
    monkeypatch.setenv('CMAKE_PREFIX_PATH', '/a:/b')
    monkeypatch.setattr(P.ident, 'ensure_resumable_attempts', lambda *_a, **_k: None)
    seen = []
    def capture(*_a, **kwargs):
        seen.append(kwargs)
        kwargs['log']('measurement marker')
        return type('Summary', (), {'results': []})()
    monkeypatch.setattr(P, 'run_campaign', capture)
    assert P.main(['--form', 'cpp', '--no-isolate-worktree', '--stock-baseline']) == 1
    assert len(seen) == 1 and 'dependency_prefix' not in seen[0]
    captured = capsys.readouterr()
    assert captured.err == 'measurement marker\n'
    assert json.loads(captured.out) == {'outcome': 'skipped', 'variant': None,
        'fitness_tps': None, 'abort_rate_pct': None, 'verdict': None}


def test_drive_exception_records_history(tmp_path, monkeypatch):
    layout = CampaignLayout(str(tmp_path))
    context = P.build_run_context(generator_id=P.GeneratorId.BACKOFF_SWEEP)
    def fail(*_a, **_k):
        raise RuntimeError('evaluation failed')
    monkeypatch.setattr(P, 'run_one_iteration', fail)
    with pytest.raises(RuntimeError, match='evaluation failed'):
        P.drive_iteration(P.default_cfg(form='cpp'), P.default_perf(),
            P.Proposal(BODY, None, ''), None, str(tmp_path), True,
            compiler='unused', scratch_dir=str(tmp_path), build_context=context,
            layout=layout)
    rows = [json.loads(line) for line in (tmp_path / P.HISTORY_NAME).read_text().splitlines()]
    assert len(rows) == 1 and rows[0]['outcome'] == 'eval-exception'
    assert set(rows[0]) == {'iteration', 'variant_id', 'implementation', 'ir',
                            'outcome', 'reject_subtype', 'reject_rule_id',
                            'verifier_digest', 'justification',
                            'measurement_campaign_id'}


def test_replay_uses_real_auditor_gate_without_loop_state(tmp_path, monkeypatch, capsys):
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('policy compiler unavailable')
    from orchestrator.campaign import patchharness, p2_2
    source = _source(tmp_path / 'external/ccbench')
    sub = tmp_path / 'external/ccbench'
    preview, diff = P.policy_gate(str(sub), GOOD, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert preview.passed
    monkeypatch.setattr(P, 'ROOT', tmp_path)
    monkeypatch.setattr(patchharness, 'assert_pinned_clean', lambda *_a: None)
    monkeypatch.setattr(patchharness, 'applied',
                        lambda *_a, **_k: contextlib.nullcontext())
    monkeypatch.setattr(p2_2, '_assert_single_tenant', lambda: None)
    monkeypatch.setattr(L, '_current_site', lambda: P.site_policy.OTHER)
    layout = CampaignLayout(str(tmp_path / 'campaign'))
    monkeypatch.setattr(P, 'exploration_campaign_layout', lambda *_a: layout)
    calls = []
    def capture(*_a, **_k):
        calls.append(1)
        return type('Summary', (), {'results': []})()
    monkeypatch.setattr(P, 'run_campaign', capture)
    bad = _proposal(tmp_path, change=lambda d: d['coder'].update(implementation=GOOD))
    with pytest.raises(AuditorGateFailure):
        P.main(['--form', 'cpp', '--allow-coder-derived-build',
                '--no-isolate-worktree', '--replay-proposal', str(bad)])
    assert calls == [] and not (tmp_path / 'campaign/loop_state.json').exists()
    good = _proposal(tmp_path, change=lambda d: (
        d['coder'].update(implementation=GOOD),
        d['auditor'].update(diff_digest=compute_diff_digest(diff))))
    assert P.main(['--form', 'cpp', '--allow-coder-derived-build',
                   '--no-isolate-worktree', '--replay-proposal', str(good)]) == 0
    assert len(calls) == 1
    assert not (tmp_path / 'campaign/loop_state.json').exists()
    assert not (tmp_path / 'campaign/policy_history.jsonl').exists()
    assert json.loads(capsys.readouterr().out)['outcome'] == 'aborted'


def test_pair_orders_candidate_then_stock_in_one_session(tmp_path, monkeypatch, capsys):
    if find_compiler() is None:
        pytest.skip('policy compiler unavailable')
    from orchestrator.campaign import patchharness, p2_2
    monkeypatch.setattr(P, 'ROOT', tmp_path)
    monkeypatch.setattr(patchharness, 'assert_pinned_clean', lambda *_a: None)
    monkeypatch.setattr(p2_2, '_assert_single_tenant', lambda: None)
    monkeypatch.setattr(L, '_current_site', lambda: P.site_policy.OTHER)
    monkeypatch.setattr(P, 'exploration_campaign_layout',
                        lambda campaign_id: CampaignLayout(str(tmp_path / campaign_id)))
    seen = []
    def candidate(*_a, **kwargs):
        seen.append(('candidate', kwargs['authorization_session'],
                     kwargs['build_context'], kwargs['measurement_cfg'],
                     kwargs['measurement_layout'], kwargs['layout'], kwargs['state']))
        return {'outcome': 'certified'}
    def stock(*_a, **kwargs):
        seen.append(('stock', kwargs['authorization_session'],
                     kwargs['build_context'], _a[0], kwargs['layout'],
                     None, None))
        return {'outcome': 'certified-stock'}
    monkeypatch.setattr(P, 'drive_iteration', candidate)
    monkeypatch.setattr(P, 'run_stock_control', stock)
    proposal = _proposal(tmp_path)
    assert P.main(['--form', 'cpp', '--allow-coder-derived-build',
        '--no-isolate-worktree', '--run-iteration', str(proposal),
        '--stock-control']) == 0
    assert [item[0] for item in seen] == ['candidate', 'stock']
    assert seen[0][1] is seen[1][1]
    series = P.default_cfg(form='cpp')
    measurement = replace(series, search_config={
        **series.search_config, 'policy_iteration': 1})
    measurement_id = str(P.ident.campaign_id(measurement))
    assert seen[0][3] == seen[1][3] == measurement
    assert seen[0][4].root == seen[1][4].root == str(tmp_path / measurement_id)
    assert seen[0][5].root == str(tmp_path / str(P.ident.campaign_id(series)))
    assert seen[0][6] is not None and seen[0][6].iteration == 0
    assert seen[0][2]._coder_entrypoint_site == 'orchestrator.campaign.p3_s4_loop_policy.main'
    assert seen[1][2]._coder_entrypoint_site is None
    assert json.loads(capsys.readouterr().out) == {
        'candidate': {'outcome': 'certified',
                      'measurement_campaign_id': measurement_id},
        'stock': {'outcome': 'certified-stock'}}
    seen.clear()
    def failed_candidate(*_a, **kwargs):
        seen.append(('candidate', kwargs['authorization_session'],
                     kwargs['build_context']))
        raise RuntimeError('candidate failed')
    monkeypatch.setattr(P, 'drive_iteration', failed_candidate)
    with pytest.raises(RuntimeError, match='candidate failed'):
        P.main(['--form', 'cpp', '--allow-coder-derived-build',
            '--no-isolate-worktree', '--run-iteration', str(proposal),
            '--stock-control'])
    assert [item[0] for item in seen] == ['candidate', 'stock']
    assert seen[0][1] is seen[1][1]


def test_pair_without_candidate_attempt_skips_stock(tmp_path, monkeypatch, capsys):
    if find_compiler() is None:
        pytest.skip('policy compiler unavailable')
    _prepare_stock_cli(tmp_path, monkeypatch)
    candidate = {'outcome': 'stopped-before', 'variant': None, 'ran': False}
    monkeypatch.setattr(P, 'drive_iteration', lambda *_a, **_k: candidate)
    def unexpected_stock(*_a, **_k):
        pytest.fail('stock must not run without a candidate attempt')
    monkeypatch.setattr(P, 'run_stock_control', unexpected_stock)
    proposal = _proposal(tmp_path)
    assert P.main(['--form', 'cpp', '--allow-coder-derived-build',
        '--no-isolate-worktree', '--run-iteration', str(proposal),
        '--stock-control']) == 1
    assert json.loads(capsys.readouterr().out) == {
        'outcome': 'stopped-before', 'variant': None, 'ran': False}


def test_pair_stock_failure_returns_one_after_candidate(tmp_path, monkeypatch, capsys):
    if find_compiler() is None:
        pytest.skip('policy compiler unavailable')
    _prepare_stock_cli(tmp_path, monkeypatch)
    monkeypatch.setattr(P, 'drive_iteration',
                        lambda *_a, **_k: {'outcome': 'rejected', 'ran': True})
    monkeypatch.setattr(P, 'run_stock_control',
                        lambda *_a, **_k: {'outcome': 'non-stock-source'})
    proposal = _proposal(tmp_path)
    assert P.main(['--form', 'cpp', '--allow-coder-derived-build',
        '--no-isolate-worktree', '--run-iteration', str(proposal),
        '--stock-control']) == 1
    assert json.loads(capsys.readouterr().out) == {
        'candidate': {'outcome': 'rejected', 'ran': True,
                      'measurement_campaign_id': str(P.ident.campaign_id(
                          replace(P.default_cfg(form='cpp'), search_config={
                              **P.default_cfg(form='cpp').search_config,
                              'policy_iteration': 1})))},
        'stock': {'outcome': 'non-stock-source'}}


def _policy_pair_child(base, proposal, crash=False):
    """Run the real Pegasus authorization and WAL from a short lived process."""
    import statistics
    from types import SimpleNamespace
    from orchestrator.campaign import (env_attestation as ea, execution_guard,
        layout as layout_module, loop, p2_2, patchharness, pipeline,
        site_policy, source_digest)
    from orchestrator.tests import test_campaign as fixtures

    base = Path(base)
    roots = [base / 'candidate', base / 'stock']
    for root in roots:
        _source(root)
        fixtures._install_complete_silo_proof_source(str(root))
    patches = pytest.MonkeyPatch()
    try:
        patches.setenv('IZANAGI_EXPLORATION_OUTPUT_ROOT', str(base / 'output'))
        patches.setattr(layout_module, 'default_durable_root_policy',
            lambda: fixtures._single_process_test_policy(base / 'output'))
        patches.setattr(site_policy, 'socket',
            SimpleNamespace(gethostname=lambda: 'bnode001'))
        patches.setattr(site_policy, '_has_nqsv', lambda: True)
        contract = P.env_contract.lookup('pegasus')
        verified = ea.load_verified_calibration(contract, loop._repo_root())
        raw = ea.profile_to_dict(verified.attestation_profile)
        del raw['effective_clock']['tolerance_pct']
        samples = raw['effective_clock']['samples_mhz']
        raw['effective_clock']['samples_mhz'] = [
            float(statistics.median(samples))] * len(samples)
        observed = ea.normalize_observed_profile(raw)
        attest = execution_guard.attest_and_build_receipt
        patches.setattr(execution_guard, 'attest_and_build_receipt',
            lambda contract, calibration: attest(
                contract, calibration, probe_fn=lambda: observed))
        patches.setattr(P, 'ROOT', base)
        patches.setattr(p2_2, '_assert_single_tenant', lambda: None)
        patches.setattr(patchharness, 'assert_pinned_clean', lambda *_a: None)
        patches.setattr(patchharness, 'applied',
            lambda *_a, **_k: contextlib.nullcontext())
        patches.setattr(loop, '_perform_perf_preflight', lambda *_a, **_k: (None, True))
        def evidence(genome, pin, *, ccbench_dir='', **_kwargs):
            token = source_digest.STOCK if Path(ccbench_dir) == roots[1] else 'd' * 64
            return fixtures._source_evidence(genome, pin, src_token=token,
                                            source_root=ccbench_dir)
        patches.setattr(loop.source_digest, 'resolve_evidence', evidence)

        @contextlib.contextmanager
        def checkout(pin, *, base_dir):
            arm = checkout.arm
            checkout.arm += 1
            assert arm in (0, 1) and pin == P.axis.PIN
            assert base_dir == str(base / 'external/ccbench')
            with fixtures._mock_pipeline(
                trace_content=(ROOT / 'orchestrator/tests/fixtures/g1_serial/trace_0.log').read_text(),
                ncommit=2), patches.context() as local:
                local.setattr(pipeline.source_digest, 'resolve_evidence', evidence)
                build = pipeline.buildcache.build_v2
                def observed_build(genome, *, build_context, **kwargs):
                    assert (build_context._authority_nonce is None) == (arm == 1)
                    assert kwargs['ccbench_dir'] == str(roots[arm])
                    if crash and arm == 0:
                        os._exit(37)
                    local.setattr(fixtures, '_BUILD_CONTEXT', build_context)
                    return build(genome, build_context=build_context, **kwargs)
                local.setattr(pipeline.buildcache, 'build_v2', observed_build)
                yield str(roots[arm])
        checkout.arm = 0
        patches.setattr(patchharness, 'checkout', checkout)
        return P.main(['--form', 'cpp', '--campaign-env', 'pegasus',
            '--allow-coder-derived-build', '--run-iteration', str(proposal),
            '--stock-control'])
    finally:
        patches.undo()


def _policy_pair_case(tmp_path, valid_reservation_environment):
    output = tmp_path / 'output'
    (output / 'env/pegasus/claims').mkdir(parents=True)
    preview_root = tmp_path / 'preview'
    _source(preview_root)
    compiler = find_compiler()
    if compiler is None:
        pytest.skip('policy compiler unavailable')
    gate, diff = P.policy_gate(str(preview_root), GOOD, None,
        compiler=compiler, scratch_dir=str(tmp_path), write=False)
    assert gate.passed
    proposal = _proposal(tmp_path, change=lambda d: (
        d['coder'].update(implementation=GOOD),
        d['auditor'].update(diff_digest=compute_diff_digest(diff))))
    harness = tmp_path / 'pair_child.py'
    harness.write_text(
        'import sys\n'
        'from orchestrator.tests.test_p3_s4_loop_policy import _policy_pair_child\n'
        'sys.exit(_policy_pair_child(sys.argv[1], sys.argv[2], sys.argv[3] == "crash"))\n',
        encoding='utf-8')
    env = {**os.environ, **valid_reservation_environment}
    env['PYTHONPATH'] = os.pathsep.join((
        str(ROOT), str(ROOT / 'orchestrator/tests'), env.get('PYTHONPATH', '')))
    def run(*, crash=False):
        return subprocess.run([sys.executable, str(harness), str(tmp_path),
            str(proposal), 'crash' if crash else 'run'], cwd=ROOT, env=env,
            text=True, capture_output=True, timeout=30)
    series = P.default_cfg(form='cpp', campaign_env='pegasus')
    # The subprocess uses a disposable exploration root; derive paths from IDs.
    series_root = output / 'exploration/campaigns' / str(P.ident.campaign_id(series))
    def measurement(number):
        cfg = replace(series, search_config={
            **series.search_config, 'policy_iteration': number})
        return cfg, output / 'exploration/campaigns' / str(P.ident.campaign_id(cfg))
    return run, output, series_root, measurement


def _pair_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def test_pair_pegasus_two_processes_use_distinct_claims_and_measurement_wal(
        tmp_path, valid_reservation_environment):
    from orchestrator.campaign import wal
    from orchestrator.campaign.artifact_admission import (
        CampaignReadPurpose, require_admitted_campaign)
    run, output, series_root, measurement = _policy_pair_case(
        tmp_path, valid_reservation_environment)
    first = run()
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)['stock']['outcome'] == 'certified-stock'
    assert json.loads((series_root / 'loop_state.json').read_text())['iteration'] == 1
    assert len(_pair_rows(series_root / P.HISTORY_NAME)) == 1
    second = run()
    assert second.returncode == 0, second.stderr
    claims = list((output / 'env/pegasus/claims').glob('*.claim'))
    assert len(claims) == 2 and len({claim.name for claim in claims}) == 2
    assert {claim.stem for claim in claims} == {
        str(P.ident.campaign_id(measurement(number)[0])) for number in (1, 2)}
    rows = _pair_rows(series_root / P.HISTORY_NAME)
    assert [row['iteration'] for row in rows] == [1, 2]
    assert json.loads((series_root / 'loop_state.json').read_text())['iteration'] == 2
    for number, process in ((1, first), (2, second)):
        cfg, root = measurement(number)
        payload = json.loads(process.stdout)
        assert payload['stock']['outcome'] == 'certified-stock'
        assert payload['candidate']['measurement_campaign_id'] == str(P.ident.campaign_id(cfg))
        assert rows[number - 1]['measurement_campaign_id'] == str(P.ident.campaign_id(cfg))
        records = wal.read_records(CampaignLayout(str(root)))
        assert {payload['candidate']['variant'], payload['stock']['variant']} <= {
            record.variant for record in records}
        assert len({record.variant for record in records if record.stage == STAGE_BUILD_START}) == 2
    _cfg, second_root = measurement(2)
    view = require_admitted_campaign(str(second_root),
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE)
    completed_digest = L.make_critic_digest(view, tag='p3-silo-policy', reflux=True,
        identity_projection=L.make_critic_identity_projection(view))
    digest = (series_root / 'silo_policy_loop_digest.txt').read_text()
    second_records = wal.read_records(CampaignLayout(str(second_root)))
    second_payload = json.loads(second.stdout)
    second_variant = second_payload['candidate']['variant']
    stock_variant = second_payload['stock']['variant']
    candidate_start = next(record for record in second_records
        if record.stage == STAGE_BUILD_START and record.variant == second_variant)
    stock_start = next(record for record in second_records
        if record.stage == STAGE_BUILD_START and record.variant == stock_variant)
    candidate_evidence = candidate_start.payload['genome'].split('|', 1)[1]
    stock_evidence = stock_start.payload['genome'].split('|', 1)[1]
    assert candidate_evidence != stock_evidence
    assert candidate_evidence in digest
    assert stock_evidence in completed_digest
    assert stock_evidence not in digest


def test_pair_pegasus_crash_consumes_iteration_before_measurement(
        tmp_path, valid_reservation_environment):
    from orchestrator.campaign import wal
    run, output, series_root, measurement = _policy_pair_case(
        tmp_path, valid_reservation_environment)
    crashed = run(crash=True)
    assert crashed.returncode == 37
    assert len(list((output / 'env/pegasus/claims').glob('*.claim'))) == 1
    assert json.loads((series_root / 'loop_state.json').read_text())['iteration'] == 1
    assert not (series_root / P.HISTORY_NAME).exists()
    next_run = run()
    assert next_run.returncode == 0, next_run.stderr
    claims = list((output / 'env/pegasus/claims').glob('*.claim'))
    assert len(claims) == 2
    payload = json.loads(next_run.stdout)
    assert payload['candidate']['outcome'] == 'certified'
    assert payload['stock']['outcome'] == 'certified-stock'
    cfg, root = measurement(2)
    assert str(P.ident.campaign_id(cfg)) in {claim.stem for claim in claims}
    assert payload['candidate']['measurement_campaign_id'] == str(P.ident.campaign_id(cfg))
    assert len({record.variant for record in wal.read_records(CampaignLayout(str(root)))
                if record.stage == STAGE_BUILD_START}) == 2
    assert json.loads((series_root / 'loop_state.json').read_text())['iteration'] == 2
    rows = _pair_rows(series_root / P.HISTORY_NAME)
    assert len(rows) == 1 and rows[0]['iteration'] == 2


def test_pair_pegasus_reused_identity_keeps_one_shot_claim(
        tmp_path, valid_reservation_environment):
    from orchestrator.campaign import wal
    run, output, series_root, measurement = _policy_pair_case(
        tmp_path, valid_reservation_environment)
    first = run()
    assert first.returncode == 0, first.stderr
    cfg, root = measurement(1)
    layout = CampaignLayout(str(root))
    before = wal.read_records(layout)
    state_path = series_root / 'loop_state.json'
    state = json.loads(state_path.read_text())
    state['iteration'] = 0
    state_path.write_text(json.dumps(state), encoding='utf-8')
    duplicate = run()
    assert duplicate.returncode != 0 and 'ClaimError' in duplicate.stderr
    assert wal.read_records(layout) == before
    claims = list((output / 'env/pegasus/claims').glob('*.claim'))
    assert len(claims) == 1 and claims[0].stem == str(P.ident.campaign_id(cfg))
