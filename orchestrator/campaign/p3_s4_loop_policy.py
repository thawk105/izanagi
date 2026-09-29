"""Policy campaign driver; see D2214, D2256, and the phase 3 policy runbook."""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass, replace
from dataclasses import fields, is_dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import axis_silo_function_policy as axis
from . import env_contract, ident, p3_s4_loop as L, site_policy, source_digest
from . import wal
from .artifact_admission import CampaignReadPurpose, require_admitted_campaign
from .auditor_gate import (AuditorGateFailure, apply_mandatory_deny_only_veto,
                           compute_diff_digest, parse_auditor_dict)
from .build_admission import (BuildAdmissionError, GeneratorId,
                              add_registered_coder_build_authority_argument,
                              build_run_context)
from .diff_quarantine import DiffQuarantineResult, DiffRejectSubtype
from .layout import exploration_campaign_layout
from .loop import run_campaign
from .model import CampaignConfig, Genome, STAGE_ABORT, STAGE_BENCH_DONE, STAGE_BUILD_START
from .pipeline import SEARCH_CONFIG_VERIFY_KEY, VERIFY_LEGACY_PLUS_PERFORMANCE, PerfConfig, variant_id
from .projection_guard import assert_closed_proposal_schema
from .silo_policy_compile import check_policy_body, find_compiler
from .silo_policy_ir import enumerate_recon, parse_policy_ir, render_policy
from ..verifier.core import result_to_dict_v3

ROOT = Path(__file__).resolve().parents[2]
PROJECTION_PATH = ROOT / 'output/env/pegasus/calibration/silo_function_policy_recon/projection.json'
CONTEXT_PATH = ROOT / 'src/coder-leakproof-context.md'
SPEC_PATH = Path(__file__).with_name('silo_function_policy_coder_spec.md')
HISTORY_NAME = 'policy_history.jsonl'
ENV_TAG = 'linux-baremetal'
DECLARED_USE_CLASS = 'exploration'
SOURCE_REL = axis.SOURCE_REL
BASE = {'BACK_OFF': 1, 'NO_WAIT_LOCKING_IN_VALIDATION': 1,
        'NO_WAIT_OF_TICTOC': 0, 'WAL': 0, axis.FLAG: 1}
# Fixed WAL abort reasons in loop.py, pipeline.py, and L.record_diff_reject,
# plus verifier verdicts.
REASON_CODES = frozenset({
    'identity-error', 'admission-error', 'build-source-state-error',
    'build-error', 'bench-binary-mismatch', 'trace-timeout',
    'trace-no-commit-witness', 'trace-witness-unsupported-workload',
    'trace-run-nonzero-exit', 'trace-empty', 'trace-no-abort-counts',
    'trace-batch-commits-unattributed', 'trace-parse-error',
    'verify-remote-unavailable', 'verify-probe-error',
    'verify-competing-tenant', 'bench-probe-error',
    'bench-competing-tenant', 'bench-unsettled',
    'bench-returncodes-round-unbound', 'bench-no-throughput',
    'bench-cv-undefined', 'screen-slower-than-floor', 'stale-baseline',
    'non-serializable', 'indeterminate', 'diff-quarantine',
})


def _reason_code(reason):
    if type(reason) is str:
        if reason in REASON_CODES:
            return reason
        if reason.startswith('eval-exception: '):
            return 'eval-exception'
    return 'other'


@dataclass(frozen=True)
class Proposal:
    implementation: str
    ir: dict | None
    justification: str


def _tagged_ir(value):
    if is_dataclass(value):
        return {'kind': type(value).__name__, **{
            field.name: _tagged_ir(getattr(value, field.name)) for field in fields(value)}}
    if isinstance(value, tuple):
        return [_tagged_ir(item) for item in value]
    return value


def initial_proposal(case_id):
    if case_id not in ('0000', '0001'):
        raise ValueError('unregistered initial point')
    ir = _tagged_ir(next(case.ir for case in enumerate_recon() if case.case_id == case_id))
    return Proposal(render_policy(parse_policy_ir(ir)), ir, '')


MACHINE_NAMES = {'random-ir': frozenset({'random-ir'}),
                 'evo-ir': frozenset({'evo-ir', 'evo-fallback-ir'})}


def load_machine_proposal(path, *, arm, series, form):
    if arm not in MACHINE_NAMES or form != 'ir':
        raise ValueError('machine proposal forbidden for this arm')
    with open(path, encoding='utf-8') as stream:
        document = json.load(stream, object_pairs_hook=_unique_pairs)
    if type(document) is not dict or set(document) != {'generator', 'ir'}:
        raise ValueError('invalid machine proposal')
    provenance = document['generator']
    if (type(provenance) is not dict or set(provenance) !=
            {'name', 'version', 'series', 'a', 'counter', 'preimage'}
            or provenance['name'] not in MACHINE_NAMES[arm]
            or type(provenance['version']) is not str
            or type(provenance['series']) is not int or provenance['series'] != series
            or type(provenance['a']) is not int or provenance['a'] < 1
            or type(provenance['counter']) is not int or not 0 <= provenance['counter'] < 1000
            or type(provenance['preimage']) is not str):
        raise ValueError('invalid generator provenance')
    prefix = {'random-ir': 'random', 'evo-ir': 'evo',
              'evo-fallback-ir': 'evo-fallback'}[provenance['name']]
    expected = f"{provenance['version']}|{prefix}|{series}|{provenance['a']}|{provenance['counter']}"
    if provenance['preimage'] != expected:
        raise ValueError('generator preimage mismatch')
    ir = document['ir']
    return Proposal(render_policy(parse_policy_ir(ir)), ir, '')


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate proposal key')
        result[key] = value
    return result


def load_proposal_file(path, *, form, preview=False):
    if form not in ('cpp', 'ir'):
        raise ValueError('unknown form')
    with open(path, encoding='utf-8') as stream:
        document = json.load(stream, object_pairs_hook=_unique_pairs)
    if preview:
        if type(document) is not dict or set(document) != {'coder'}:
            raise ValueError('preview requires only coder')
        coder_keys = {'axis', 'implementation' if form == 'cpp' else 'ir'}
        if type(document['coder']) is not dict or not coder_keys <= set(document['coder']) or set(document['coder']) - coder_keys - {'justification', 'confidence'}:
            raise ValueError('invalid preview coder')
    else:
        assert_closed_proposal_schema(document, require_auditor=True,
            require_coder_value=False, coder_contract='policy-' + form)
    coder = document['coder']
    if type(coder['axis']) is not str or coder['axis'] != axis.MARKER_ID:
        raise ValueError('policy axis mismatch')
    if type(coder.get('justification', '')) is not str:
        raise ValueError('invalid justification')
    if type(coder.get('confidence', 'medium')) is not str or coder.get('confidence', 'medium') not in ('high', 'medium', 'low'):
        raise ValueError('invalid confidence')
    if form == 'cpp':
        implementation, ir = coder['implementation'], None
        if type(implementation) is not str:
            raise ValueError('implementation must be string')
    else:
        ir = coder['ir']
        parsed = parse_policy_ir(ir)
        implementation = render_policy(parsed)
    auditor = None if preview else parse_auditor_dict(document['auditor'], max_violation_type=26)
    return Proposal(implementation, ir, coder.get('justification', '')), auditor


def default_cfg(*, form, reflux=True, campaign_env=ENV_TAG, evaluation_purpose=None,
                contrast=None):
    if form not in ('cpp', 'ir'):
        raise ValueError('unknown form')
    if campaign_env not in (ENV_TAG, 'pegasus'):
        raise ValueError('unknown campaign environment')
    if evaluation_purpose not in (None, 'bootstrap', 'r2'):
        raise ValueError('unknown evaluation purpose')
    if contrast is not None:
        cohort, arm, series = contrast
        if (type(cohort) is not str or not cohort or arm not in
                (*MACHINE_NAMES, 'llm-cpp', 'llm-ir', 'reference')
                or type(series) is not int or series < 1
                or form != ('cpp' if arm in ('llm-cpp', 'reference') else 'ir')):
            raise ValueError('invalid contrast coordinates')
    cfg = CampaignConfig(
        spec_slug='p3-silo-policy-loop', search_tag='silo-policy-autonomous',
        spec_content='Silo function policy; D2214.', ccbench_commit=axis.PIN,
        search_config={'scale': 'silo', 'axis': axis.MARKER_ID, 'form': form,
                       'reflux': 'on' if reflux else 'off',
                       'perf': _perf_identity(default_perf()),
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_PERFORMANCE,
                       **({'evaluation_purpose': evaluation_purpose}
                          if evaluation_purpose is not None else {}),
                       **({'contrast_cohort': cohort, 'contrast_arm': arm,
                           'contrast_series': series,
                           'verify_performance_concurrent': True}
                          if contrast is not None else {})},
        trial='p3-silo-policy-loop')
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(cfg, context.policy)
    if campaign_env == 'pegasus':
        return L._campaign_cfg_for_site(cfg, site_policy.PEGASUS_COMPUTE,
                                        _contract=env_contract.lookup('pegasus'))
    return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))


def default_perf():
    return L.calibrated_perf('write-heavy')


def _perf_identity(perf):
    if type(perf) is not PerfConfig or type(perf.workload) is not dict:
        raise ValueError('invalid performance configuration')
    if any(type(getattr(perf, name)) is not int or getattr(perf, name) <= 0
           for name in ('records', 'threads', 'extime', 'reps')):
        raise ValueError('invalid performance scalar')
    if any(type(key) is not str or type(value) is not str
           for key, value in perf.workload.items()):
        raise ValueError('invalid performance workload')
    return {'records': perf.records, 'threads': perf.threads,
            'workload': {key: perf.workload[key] for key in sorted(perf.workload)},
            'extime': perf.extime, 'reps': perf.reps}


def _require_perf_identity(cfg, perf):
    if cfg.search_config.get('perf') != _perf_identity(perf):
        raise ValueError('performance configuration differs from campaign identity')


def _reject(subtype, rule_id):
    digest = {'rejection_type': 'diff-quarantine', 'subtype': subtype.value,
              'reason': subtype.value, 'diff_region': axis.SOURCE_REL,
              'template_diff_id': axis.MARKER_ID, 'evidence': rule_id,
              'rule_id': rule_id}
    return DiffQuarantineResult(passed=False, subtype=subtype,
        reason=subtype.value, digest=digest, violations=[digest])


def policy_gate(sub, implementation, auditor, *, compiler, scratch_dir, write,
                origin=None):
    """Use one gate for preview and run, with writes after all checks."""
    result, base, edited, working_diff = L.quarantine(
        sub, implementation, marker_id=axis.MARKER_ID,
        source_rel=axis.SOURCE_REL, write=False)
    if result.passed:
        grammar, compiled = check_policy_body(
            implementation, compiler=compiler, scratch_dir=scratch_dir)
        if not grammar.accepted:
            result = _reject(DiffRejectSubtype.POLICY_GRAMMAR,
                             grammar.rule_id or 'policy-grammar')
        elif compiled is None or not compiled.accepted:
            rule = ('compile-unavailable' if compiled is None or compiled.unavailable
                    else 'compile-timeout' if compiled.timed_out else 'compile-error')
            result = _reject(DiffRejectSubtype.POLICY_COMPILE, rule)
    if result.passed and auditor is not None:
        result = apply_mandatory_deny_only_veto(
            result, auditor, working_diff, diff_region=axis.SOURCE_REL,
            template_diff_id=axis.MARKER_ID, max_violation_type=26)
    if result.passed and write:
        if auditor is None and origin not in ('machine', 'initial'):
            raise AuditorGateFailure('auditor required for write')
        source = Path(sub) / axis.SOURCE_REL
        source.write_text(edited, encoding='utf-8')
        rebound = L.make_working_diff(base, source.read_text(encoding='utf-8'), axis.SOURCE_REL)
        if compute_diff_digest(rebound) != compute_diff_digest(working_diff):
            raise AuditorGateFailure('written policy digest mismatch')
    return result, working_diff


def _history_path(layout):
    return Path(layout.root) / HISTORY_NAME


def _campaign_layout(cfg):
    return exploration_campaign_layout(str(ident.campaign_id(cfg)))


def _append_history(layout, iteration, proposal, out):
    digest = out.get('digest') or {}
    row = {'iteration': iteration, 'variant_id': out.get('variant'),
           'implementation': proposal.implementation, 'ir': proposal.ir,
           'outcome': out['outcome'], 'reject_subtype': digest.get('subtype'),
           'reject_rule_id': digest.get('rule_id'),
           'verifier_digest': out.get('verifier_digest'),
           'justification': proposal.justification,
           'measurement_campaign_id': out.get('measurement_campaign_id')}
    if 'logical_slot' in out:
        row['logical_slot'] = out['logical_slot']
    with _history_path(layout).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def _result_history(layout, result):
    """Project only typed evaluation and WAL fields into the next coder turn."""
    if result is None:
        return 'aborted', None
    records = [record for record in wal.read_records(layout)
               if record.variant == result.variant
               and record.payload.get('build_attempt_id') == result.build_attempt_id]
    aborts = [record for record in records if record.stage == STAGE_ABORT]
    terminal = aborts[-1].payload if aborts else {}
    reason = terminal.get('reason')
    if result.certified and not result.aborted:
        outcome = 'certified'
    elif type(reason) is str:
        outcome = _reason_code(reason)
    elif result.verdict in ('non-serializable', 'indeterminate'):
        outcome = result.verdict
    else:
        outcome = 'aborted'
    digest = {'verdict': result.verdict, 'certified': result.certified,
              'aborted': result.aborted}
    if type(reason) is str:
        digest['reason'] = _reason_code(reason)
    workload = terminal.get('workload')
    if type(workload) is dict and type(workload.get('tag')) is str:
        digest['workload_tag'] = workload['tag']
    verify = result.verify_result
    if verify is not None:
        structured = result_to_dict_v3(verify)
        digest['total_cycles'] = structured['total_cycles']
        anomalies = [{key: item[key] for key in ('phenomenon', 'cycle', 'edges')}
                     for item in structured['anomalies']]
        digest['witness_count'] = len(anomalies)
        digest['anomalies'] = sorted(anomalies, key=lambda item: json.dumps(
            item, sort_keys=True, ensure_ascii=False))[:8]
        integrity = structured['integrity']
        digest['integrity'] = {key: integrity[key] for key in (
            'clean', 'orphan_reads', 'version_dups', 'dup_txids',
            'genesis_commits', 'missing_txids', 'write_version_mismatch',
            'malformed_keys', 'framing_violations', 'lock_coverage_violations',
            'write_intent_violations', 'permutation_violations')}
        digest['integrity_reason_codes'] = [key for key, value in digest['integrity'].items()
                                            if key != 'clean' and value]
        if verify.integrity.existence_violation_details is not None:
            digest['integrity']['existence_violations'] = verify.integrity.existence_violations
            if verify.integrity.existence_violations:
                digest['integrity_reason_codes'].append('existence_violations')
        if (verify.integrity.expected_commits is not None
                and verify.integrity.observed_commits is not None
                and verify.integrity.expected_commits != verify.integrity.observed_commits):
            digest['integrity_reason_codes'].append('commit_witness_mismatch')
    return outcome, digest


def make_policy_coder_input(layout, *, baseline, critic_diagnosis=None):
    if type(baseline) is not dict or set(baseline) != {'throughput_tps', 'abort_rate_pct'} or any(type(v) not in (int, float) for v in baseline.values()):
        raise ValueError('invalid baseline')
    projection = json.loads(PROJECTION_PATH.read_text(encoding='utf-8'), object_pairs_hook=_unique_pairs)
    if type(projection) is not dict or set(projection) != {'binary', 'scope', 'excluded'} or type(projection['binary']) is not bool or type(projection['scope']) is not str:
        raise ValueError('invalid recon projection')
    history = []
    if _history_path(layout).exists():
        with _history_path(layout).open(encoding='utf-8') as stream:
            for line in stream:
                row = json.loads(line, object_pairs_hook=_unique_pairs)
                history.append({key: row[key] for key in (
                    'iteration', 'implementation', 'ir', 'outcome',
                    'reject_subtype', 'reject_rule_id', 'verifier_digest')})
    payload = {'leakproof_context': CONTEXT_PATH.read_text(encoding='utf-8'),
               'policy_spec': SPEC_PATH.read_text(encoding='utf-8'),
               'baseline': baseline,
               'recon_projection': {'binary': projection['binary'], 'scope': projection['scope']},
               'self_history': history}
    if critic_diagnosis is not None:
        keys = {'data_boundary', 'source_sha256', 'attribution', 'recommend', 'avoid', 'uncertainty'}
        if type(critic_diagnosis) is not dict or set(critic_diagnosis) != keys or any(type(v) is not str for v in critic_diagnosis.values()):
            raise ValueError('invalid critic diagnosis')
        payload['critic_diagnosis'] = critic_diagnosis
    return payload


def _measurement_contract(campaign_env):
    contract = L._admit_env_contract(L._current_site())
    if contract.env_tag != campaign_env:
        raise ValueError('campaign environment differs from measurement site')
    return contract


def _cfg_contract(cfg):
    return env_contract.lookup(cfg.search_config.get(L._CAMPAIGN_ENV_KEY, ENV_TAG))


def _measurement_options(*, build_context, contract, dependency_prefix='',
                         fetchcontent_options=None, authorization_session=None,
                         stock=False):
    options = {}
    if authorization_session is not None:
        options['authorization_session'] = authorization_session
    if contract.env_tag == 'pegasus':
        options['env_contract'] = contract
        if dependency_prefix:
            options['dependency_prefix'] = dependency_prefix
    if fetchcontent_options:
        options.update(fetchcontent_options)
        options['env_contract'] = contract
    if stock:
        options['capability_resolver'] = L._stock_capability_resolver(build_context)
    return options


def _stock_result(layout, summary):
    result = summary.results[0] if summary.results else None
    abort_rate = None
    stock_source = False
    if result is not None:
        records = [record for record in wal.read_records(layout)
                   if record.variant == result.variant
                   and record.payload.get('build_attempt_id') == result.build_attempt_id]
        stock_genome = Genome('silo', {key: value for key, value in BASE.items()
                                        if key != axis.FLAG})
        stock_source = (result.variant == variant_id(stock_genome)
                        and any(record.stage == STAGE_BUILD_START
                                and record.payload.get('src_token') == source_digest.STOCK
                                for record in records))
        benches = [record for record in records if record.stage == STAGE_BENCH_DONE]
        if benches:
            leading = benches[-1].payload.get('leading_indicators')
            if type(leading) is dict and type(leading.get('abort_rate')) in (int, float):
                abort_rate = leading['abort_rate'] * 100
    return {'outcome': (('certified-stock' if stock_source else 'non-stock-source')
                        if result.certified and not result.aborted else 'aborted')
                        if result else 'skipped',
            'variant': result.variant if result else None,
            'fitness_tps': result.fitness_tps if result else None,
            'abort_rate_pct': abort_rate,
            'verdict': result.verdict if result else None}


def run_stock_control(cfg, perf, sub, *, layout, cache_root='',
                      build_context, contract, dependency_prefix='',
                      fetchcontent_options=None, authorization_session=None,
                      log=print):
    """Evaluate the original stock source; see D2256 and the runbook."""
    genome = Genome('silo', {key: value for key, value in BASE.items()
                             if key != axis.FLAG})
    layout.ensure()
    ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)
    options = _measurement_options(build_context=build_context, contract=contract,
        dependency_prefix=dependency_prefix,
        fetchcontent_options=fetchcontent_options,
        authorization_session=authorization_session, stock=True)
    summary = run_campaign(cfg, [genome], perf, contract.env_tag,
        contract.clocks_per_us, numactl=list(contract.numactl), log=log,
        ccbench_dir=sub, cache_root=cache_root,
        authorization_contract=env_contract.authorize(contract.env_tag),
        build_context=build_context, declared_use_class=DECLARED_USE_CLASS,
        **options)
    return _stock_result(layout, summary)


def run_one_iteration(cfg, perf, proposal, auditor, sub, do_build, *,
                      layout, compiler, scratch_dir, build_context,
                      cache_root='', contract=None, dependency_prefix='',
                      fetchcontent_options=None, authorization_session=None,
                      log=print, origin=None):
    _require_perf_identity(cfg, perf)
    if cfg.search_config.get('form') != ('ir' if proposal.ir is not None else 'cpp'):
        raise ValueError('policy form mismatch')
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    if contract is None:
        contract = _cfg_contract(cfg)
    cfg = ident.bind_environment_contract(cfg, contract)
    genome = Genome('silo', dict(BASE))
    layout.ensure()
    if do_build:
        ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)
    from .patchharness import applied
    with applied(str(ROOT / 'patches' / axis.TEMPLATE_PATCH), axis.PIN, sub):
        result, _diff = policy_gate(sub, proposal.implementation, auditor,
            compiler=compiler, scratch_dir=scratch_dir, write=do_build,
            origin=origin)
        if not result.passed:
            if not do_build:
                return {'outcome': 'rejected', 'variant': None, 'digest': result.digest}
            variant = L.record_diff_reject(layout, genome, proposal.implementation,
                                           result, env_tag=contract.env_tag)
            return {'outcome': 'rejected', 'variant': variant, 'digest': result.digest}
        if not do_build:
            return {'outcome': 'dry-pass', 'variant': None}
        options = _measurement_options(build_context=build_context,
            contract=contract, dependency_prefix=dependency_prefix,
            fetchcontent_options=fetchcontent_options,
            authorization_session=authorization_session)
        summary = run_campaign(cfg, [genome], perf, contract.env_tag,
            contract.clocks_per_us, numactl=list(contract.numactl), log=log,
            ccbench_dir=sub, cache_root=cache_root,
            authorization_contract=env_contract.authorize(contract.env_tag),
            build_context=build_context, declared_use_class=DECLARED_USE_CLASS,
            **options)
    result = summary.results[0] if summary.results else None
    outcome, verifier_digest = _result_history(layout, result)
    return {'outcome': outcome,
            'variant': result.variant if result else None,
            'verdict': result.verdict if result else None,
            'verifier_digest': verifier_digest}


def drive_iteration(cfg, perf, proposal, auditor, sub, do_build, *,
                    compiler, scratch_dir, build_context, layout=None,
                    cache_root='', contract=None, dependency_prefix='',
                    fetchcontent_options=None, authorization_session=None,
                    state=None, measurement_cfg=None, measurement_layout=None,
                    log=print):
    _require_perf_identity(cfg, perf)
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, contract or _cfg_contract(cfg))
    if layout is None:
        layout = _campaign_layout(cfg)
    layout.ensure()
    if state is None:
        state = L.load_loop_state(layout) or L.LoopState(start_wall=time.time())
    state.whiteboard.clear()
    state.reverse_recommendations = 0
    stop = L.check_stop(state)
    if stop.stop:
        L.save_loop_state(layout, state)
        return {'outcome': 'stopped-before', 'variant': None,
                'stop_reason': stop.reason, 'iteration': state.iteration, 'ran': False}
    state.iteration += 1
    L.save_loop_state(layout, state)
    evaluation_cfg = measurement_cfg if measurement_cfg is not None else cfg
    evaluation_layout = measurement_layout if measurement_layout is not None else layout
    measurement_campaign_id = (str(ident.campaign_id(evaluation_cfg))
                               if measurement_cfg is not None else None)
    try:
        out = run_one_iteration(evaluation_cfg, perf, proposal, auditor, sub, do_build,
            layout=evaluation_layout, compiler=compiler, scratch_dir=scratch_dir,
            cache_root=cache_root, build_context=build_context,
            contract=contract, dependency_prefix=dependency_prefix,
            fetchcontent_options=fetchcontent_options,
            authorization_session=authorization_session, log=log)
    except Exception:
        if do_build:
            _append_history(layout, state.iteration, proposal,
                            {'outcome': 'eval-exception',
                             'measurement_campaign_id': measurement_campaign_id})
        raise
    finally:
        L.save_loop_state(layout, state)
    if do_build:
        _append_history(layout, state.iteration, proposal,
                        {**out, 'measurement_campaign_id': measurement_campaign_id})
        view = require_admitted_campaign(evaluation_layout.root,
            purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE)
        digest = L.make_critic_digest(view, tag='p3-silo-policy',
            reflux=cfg.search_config.get('reflux') == 'on',
            identity_projection=L.make_critic_identity_projection(view))
        (Path(layout.root) / 'silo_policy_loop_digest.txt').write_text(digest, encoding='utf-8')
    stop = L.check_stop(state)
    out.update({'stop_reason': stop.reason, 'iteration': state.iteration, 'ran': True})
    return out


def drive_record_reject(cfg, perf, proposal, sub, *, compiler, scratch_dir,
                        build_context, layout=None):
    """Record a failed preview without building or accepting a passing candidate."""
    _require_perf_identity(cfg, perf)
    if cfg.search_config.get('form') != ('ir' if proposal.ir is not None else 'cpp'):
        raise ValueError('policy form mismatch')
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, _cfg_contract(cfg))
    if layout is None:
        layout = _campaign_layout(cfg)
    state = L.load_loop_state(layout) or L.LoopState(start_wall=time.time())
    state.whiteboard.clear()
    state.reverse_recommendations = 0
    stop = L.check_stop(state)
    if stop.stop:
        L.save_loop_state(layout, state)
        return {'outcome': 'stopped-before', 'variant': None,
                'stop_reason': stop.reason, 'iteration': state.iteration, 'ran': False}
    from .patchharness import applied
    with applied(str(ROOT / 'patches' / axis.TEMPLATE_PATCH), axis.PIN, sub):
        result, _diff = policy_gate(sub, proposal.implementation, None,
            compiler=compiler, scratch_dir=scratch_dir, write=False)
    return _record_rejected_gate(cfg, proposal, result, layout, state, build_context)


def _record_rejected_gate(cfg, proposal, result, layout, state, build_context):
    """Persist only a rejected result from the shared preview gate."""
    if result.passed:
        raise ValueError('record-reject requires a rejected candidate')
    layout.ensure()
    ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)
    variant = L.record_diff_reject(layout, Genome('silo', dict(BASE)),
                                   proposal.implementation, result,
                                   env_tag=_cfg_contract(cfg).env_tag)
    state.iteration += 1
    L.save_loop_state(layout, state)
    out = {'outcome': 'rejected', 'variant': variant, 'digest': result.digest}
    _append_history(layout, state.iteration, proposal, out)
    stop = L.check_stop(state)
    out.update({'stop_reason': stop.reason, 'iteration': state.iteration, 'ran': True})
    return out


CONTRAST_SLOTS = frozenset(('stock', 'seed', 'eval', 'score',
                            'ref-stock', 'ref-fixed10'))


class ContrastUnitMismatch(ValueError):
    """The submitted unit does not match the next ledger unit."""


def contrast_cfg(header, *, campaign_env, slot=None, index=None, attempt=0):
    form, arm = header['form'], header['arm']
    cfg = default_cfg(form=form, campaign_env=campaign_env,
        contrast=(header['cohort'], arm, header['series']))
    if slot is None:
        return cfg
    if slot not in CONTRAST_SLOTS or type(index) is not int or index < 0 or type(attempt) is not int or attempt < 0:
        raise ValueError('invalid contrast slot')
    return replace(cfg, search_config={**cfg.search_config,
        'contrast_slot': f'{slot}-{index}-a{attempt}'})


def _contrast_header(ledger_root, form, campaign_env):
    from .silo_policy_contrast import ContrastLedger
    root = Path(ledger_root)
    if not root.is_absolute():
        raise ValueError('contrast ledger root must be absolute')
    ledger = ContrastLedger(root)
    if ledger.header['form'] != form:
        raise ValueError('contrast form differs from ledger')
    return ledger, contrast_cfg(ledger.header, campaign_env=campaign_env)


def drive_contrast_record_reject(cfg, perf, proposal, sub, *, a, compiler,
                                 scratch_dir, build_context, layout=None):
    """Record a rejected opportunity without consulting the legacy loop state."""
    _require_perf_identity(cfg, perf)
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, _cfg_contract(cfg))
    layout = layout or _campaign_layout(cfg)
    from .patchharness import applied
    with applied(str(ROOT / 'patches' / axis.TEMPLATE_PATCH), axis.PIN, sub):
        result, _ = policy_gate(sub, proposal.implementation, None,
            compiler=compiler, scratch_dir=scratch_dir, write=False)
    if result.passed:
        raise ValueError('record-reject requires a rejected candidate')
    layout.ensure()
    ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)
    variant = L.record_diff_reject(layout, Genome('silo', dict(BASE)),
        proposal.implementation, result, env_tag=_cfg_contract(cfg).env_tag)
    out = {'outcome': 'rejected', 'variant': variant, 'digest': result.digest}
    _append_history(layout, a, proposal, out)
    return out


def _slot_observation(layout, variant, perf, out, logical_slot, attempt):
    from .b5_generator_contrast import (MACHINE_FAILURE_ABORT_REASONS,
                                         classify_session, wal_timing)
    records = [record for record in wal.read_records(layout)
               if record.variant == variant] if variant else []
    start = next((r for r in records if r.stage == STAGE_BUILD_START), None)
    if start is not None:
        records = [r for r in records if r.payload.get('build_attempt_id') ==
                   start.payload.get('build_attempt_id')]
    abort = next((r for r in reversed(records) if r.stage == STAGE_ABORT), None)
    benches = [r for r in records if r.stage == STAGE_BENCH_DONE]
    reason = abort.payload.get('reason') if abort else None
    anomalies = sum(r.payload.get('anomalies', 0) for r in records
                    if r.stage == 'verify_done')
    quality = classify_session(benches[-1].payload, perf.reps) if benches else None
    if anomalies or (type(reason) is str and 'anomaly' in reason):
        outcome, failure = 'anomaly', 'candidate'
    elif reason in MACHINE_FAILURE_ABORT_REASONS:
        outcome, failure = 'machine-failure', 'machine-failure'
    elif out.get('outcome') in ('certified', 'certified-stock'):
        outcome, failure = ('certified', None) if quality == 'normal' else ('quality-missing', 'quality')
    elif abort is not None:
        outcome, failure = 'candidate-failure', 'candidate'
    else:
        outcome, failure = 'unclassified-missing', 'unclassified'
    wal_path = Path(layout.wal_file)
    return {'logical_slot': logical_slot, 'attempt': attempt,
        'campaign_id': Path(layout.root).name, 'campaign_root': str(Path(layout.root).resolve()),
        'variant': variant, 'source_digest': start.payload.get('src_token') if start else None,
        'outcome': outcome, 'failure_class': failure, 'quality': quality,
        'fitness_tps': out.get('fitness_tps') or (benches[-1].payload.get('median_tps') if benches else None),
        'abort_rate_pct': (out.get('abort_rate_pct') if out.get('abort_rate_pct') is not None
                           else benches[-1].payload.get('leading_indicators', {}).get('abort_rate', 0) * 100
                           if benches else None), 'anomalies': anomalies,
        'wal_sha256': hashlib.sha256(wal_path.read_bytes()).hexdigest() if wal_path.exists() else None,
        'timing': wal_timing(records, perf.reps), 'critic_digest': None}


def measure_slot(header, slot, index, attempt, *, proposal, auditor, sub,
                 compiler, scratch_dir, build_context, stock_context,
                 contract, cache_root='', fetchcontent_options=None,
                 authorization_session=None, log=print, origin=None):
    """Evaluate one physical slot in its own campaign identity."""
    cfg = contrast_cfg(header, campaign_env=contract.env_tag, slot=slot,
                       index=index, attempt=attempt)
    layout = _campaign_layout(cfg)
    perf = default_perf()
    if slot in ('stock', 'ref-stock'):
        out = run_stock_control(cfg, perf, sub, layout=layout, cache_root=cache_root,
            build_context=stock_context, contract=contract,
            fetchcontent_options=fetchcontent_options,
            authorization_session=authorization_session, log=log)
    elif slot == 'ref-fixed10':
        from .patchharness import applied
        genome = Genome('silo', {**{k: v for k, v in BASE.items() if k != axis.FLAG},
                                  'BACKOFF_FIXED': 10})
        with applied(str(ROOT / 'patches/silo-backoff-fixed.patch'), axis.PIN, sub):
            # The existing meaning gate checks the requested define before the build.
            L._require_condition_gate(sub, genome)
            layout.ensure()
            ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)
            options = _measurement_options(build_context=build_context, contract=contract,
                fetchcontent_options=fetchcontent_options,
                authorization_session=authorization_session)
            summary = run_campaign(cfg, [genome], perf, contract.env_tag,
                contract.clocks_per_us, numactl=list(contract.numactl), log=log,
                ccbench_dir=sub, cache_root=cache_root,
                authorization_contract=env_contract.authorize(contract.env_tag),
                build_context=build_context, declared_use_class=DECLARED_USE_CLASS,
                **options)
        result = summary.results[0] if summary.results else None
        out = {'outcome': 'certified' if result and result.certified and not result.aborted else 'aborted',
               'variant': result.variant if result else None,
               'fitness_tps': result.fitness_tps if result else None}
    else:
        if proposal is None:
            raise ValueError('candidate slot needs a proposal')
        origin = origin or ('initial' if slot == 'seed' else 'machine'
                            if header['arm'] in MACHINE_NAMES else None)
        out = run_one_iteration(cfg, perf, proposal, auditor, sub, True,
            layout=layout, compiler=compiler, scratch_dir=scratch_dir,
            build_context=build_context, cache_root=cache_root, contract=contract,
            fetchcontent_options=fetchcontent_options,
            authorization_session=authorization_session, log=log, origin=origin)
    logical_slot = f'{slot}-{index}'
    row = _slot_observation(layout, out.get('variant'), perf, out,
                            logical_slot, attempt)
    if slot == 'eval':
        view = require_admitted_campaign(layout.root,
            purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE)
        row['critic_digest'] = L.make_critic_digest(view, tag='p3-silo-policy',
            reflux=cfg.search_config.get('reflux') == 'on',
            identity_projection=L.make_critic_identity_projection(view))
    return row


def _contrast_unit(ledger, unit_path, ledger_root):
    from .silo_policy_contrast import UNIT_SCHEMA, next_unit
    path = Path(unit_path)
    unit = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_pairs)
    if (type(unit) is not dict or set(unit) != {'schema', 'ledger_root', 'kind',
            'index', 'attempt', 'proposal_path', 'proposal_sha256'}
            or unit['schema'] != UNIT_SCHEMA
            or type(unit['index']) is not int or type(unit['attempt']) is not int
            or type(unit['kind']) is not str
            or type(unit['ledger_root']) is not str
            or not Path(unit['ledger_root']).is_absolute()
            or Path(unit['ledger_root']) != Path(ledger_root).resolve()):
        raise ContrastUnitMismatch('unit schema or ledger mismatch')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                   text=True).strip()
    if (Path(ledger.header['submit_checkout']).resolve() != ROOT.resolve()
            or ledger.header['checkout_head'] != head):
        raise ContrastUnitMismatch('submit checkout or HEAD mismatch')
    expected = next_unit(ledger)
    if (expected is None or expected['kind'] == 'dead-job'
            or any(unit[key] != expected[key] for key in ('kind', 'index', 'attempt', 'proposal_sha256'))):
        raise ContrastUnitMismatch('unit is not next in ledger')
    proposal_path = unit['proposal_path']
    if proposal_path is not None:
        if type(proposal_path) is not str or not Path(proposal_path).is_absolute():
            raise ContrastUnitMismatch('proposal path must be absolute')
        actual = hashlib.sha256(Path(proposal_path).read_bytes()).hexdigest()
        if actual != unit['proposal_sha256']:
            raise ContrastUnitMismatch('proposal digest mismatch')
    elif unit['proposal_sha256'] is not None:
        raise ContrastUnitMismatch('proposal digest without path')
    open_slots = [e for e in ledger.events if e['kind'] == 'slot-start']
    closed_slots = [e for e in ledger.events if e['kind'] == 'slot-result']
    if len(open_slots) != len(closed_slots):
        raise ContrastUnitMismatch('unfinished slot attempt')
    return unit, expected


def run_contrast_unit(unit_path, *, form, contract, fetchcontent_options,
                      context, stock_context, sub, cache_root, compiler,
                      scratch_dir, log):
    from .silo_policy_contrast import ContrastLedger
    raw = json.loads(Path(unit_path).read_text(encoding='utf-8'),
                     object_pairs_hook=_unique_pairs)
    ledger = ContrastLedger(raw['ledger_root'])
    if ledger.header['form'] != form:
        raise ContrastUnitMismatch('form differs from ledger')
    unit, expected = _contrast_unit(ledger, unit_path, raw['ledger_root'])
    proposal = auditor = None
    if unit['proposal_path'] is not None:
        if ledger.header['arm'] in MACHINE_NAMES:
            proposal = load_machine_proposal(unit['proposal_path'],
                arm=ledger.header['arm'], series=ledger.header['series'], form=form)
        else:
            proposal, auditor = load_proposal_file(unit['proposal_path'], form=form)
    if unit['kind'] == 'score':
        fixed = next((e for e in reversed(ledger.events)
                      if e['kind'] == 'endpoint-fixed'), None)
        if fixed is None:
            raise ContrastUnitMismatch('score endpoint has not been fixed')
        origin_slot = fixed.get('logical_slot') or fixed.get('slot')
        if type(origin_slot) is not str:
            raise ContrastUnitMismatch('fixed endpoint slot is missing')
        source = next((e for e in ledger.events if e['kind'] == 'slot-result'
                       and e.get('logical_slot') == origin_slot), None)
        if source is None or type(source.get('implementation')) is not str:
            raise ValueError('fixed endpoint source is unavailable')
        proposal = Proposal(source['implementation'], source.get('ir'), '')
        auditor = None
        if origin_slot.startswith('eval-') and ledger.header['arm'] not in MACHINE_NAMES:
            a = int(origin_slot.split('-')[1])
            opportunity = next((e for e in ledger.events
                if e['kind'] == 'opportunity-end' and e.get('a') == a
                and e.get('outcome') == 'proposed'), None)
            if opportunity is None:
                raise ValueError('endpoint auditor provenance missing')
            original, auditor = load_proposal_file(opportunity['proposal_path'], form=form)
            if original.implementation != proposal.implementation:
                raise ValueError('endpoint source differs from proposal')
    results = []
    from . import loop
    with loop.authorization_session() as session:
        for spec in expected['slots']:
            slot, index, attempt = spec['slot'], spec['index'], spec['attempt']
            if slot == 'seed':
                selected = initial_proposal('0000' if index == 0 else '0001')
                if form == 'cpp':
                    selected = Proposal(selected.implementation, None, '')
                selected_auditor = None
            else:
                selected, selected_auditor = proposal, auditor
            ledger.append('slot-start', logical_slot=f'{slot}-{index}',
                          attempt=attempt, unit_kind=unit['kind'],
                          unit_index=unit['index'])
            result = measure_slot(ledger.header, slot, index, attempt,
                proposal=selected, auditor=selected_auditor, sub=sub,
                compiler=compiler, scratch_dir=scratch_dir,
                build_context=context, stock_context=stock_context,
                contract=contract, cache_root=cache_root,
                fetchcontent_options=fetchcontent_options,
                authorization_session=session, log=log,
                origin=('initial' if unit['kind'] == 'score' and origin_slot.startswith('seed-') else None))
            if selected is not None:
                result['ir'] = selected.ir
                result['implementation'] = selected.implementation
            ledger.append('slot-result', **result)
            results.append(result)
    series_layout = _campaign_layout(contrast_cfg(ledger.header,
                                                   campaign_env=contract.env_tag))
    series_layout.ensure()
    if unit['kind'] == 'job1':
        for ordinal, result in enumerate(results):
            if result['logical_slot'].startswith('seed-'):
                case = initial_proposal('0000' if ordinal == 1 else '0001')
                if form == 'cpp':
                    case = Proposal(case.implementation, None, '')
                _append_history(series_layout, ordinal - 3, case, {
                    'outcome': result['outcome'], 'variant': result['variant'],
                    'logical_slot': result['logical_slot'],
                    'measurement_campaign_id': result['campaign_id']})
    elif unit['kind'] == 'eval' and results:
        _append_history(series_layout, unit['index'], proposal, {
            'outcome': results[0]['outcome'], 'variant': results[0]['variant'],
            'logical_slot': results[0]['logical_slot'],
            'measurement_campaign_id': results[0]['campaign_id']})
    return {'kind': unit['kind'], 'index': unit['index'], 'slots': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Silo function-policy campaign')
    parser.add_argument('--form', choices=('cpp', 'ir'), required=True)
    parser.add_argument('--preview-diff', metavar='PROPOSAL.json')
    parser.add_argument('--record-reject', metavar='CODER.json')
    parser.add_argument('--contrast-ledger', metavar='ROOT')
    parser.add_argument('--contrast-run-unit', metavar='UNIT.json')
    parser.add_argument('--run-iteration', metavar='PROPOSAL.json')
    parser.add_argument('--replay-proposal', metavar='PROPOSAL.json')
    parser.add_argument('--stock-baseline', action='store_true')
    parser.add_argument('--stock-control', action='store_true')
    parser.add_argument('--campaign-env', choices=(ENV_TAG, 'pegasus'), default=ENV_TAG)
    parser.add_argument('--fetchcontent-prebuild-receipt', metavar='PATH')
    parser.add_argument('--emit-coder-input', action='store_true')
    parser.add_argument('--critic-output', metavar='CRITIC.txt')
    parser.add_argument('--baseline-throughput-tps', type=float)
    parser.add_argument('--baseline-abort-rate-pct', type=float)
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('--no-isolate-worktree', action='store_true')
    add_registered_coder_build_authority_argument(
        parser, coder_entrypoint_site='orchestrator.campaign.p3_s4_loop_policy.main')
    args = parser.parse_args(argv)
    if sum(bool(x) for x in (args.preview_diff, args.record_reject,
                             args.run_iteration, args.replay_proposal,
                             args.stock_baseline, args.emit_coder_input,
                             args.contrast_run_unit)) != 1:
        parser.error('select one action')
    if args.contrast_ledger and not (args.preview_diff or args.record_reject or args.emit_coder_input):
        parser.error('--contrast-ledger requires a login action')
    if args.contrast_run_unit and (args.no_build or args.campaign_env != 'pegasus'):
        parser.error('--contrast-run-unit requires pegasus and a build')
    if args.stock_control and not args.run_iteration:
        parser.error('--stock-control requires --run-iteration')
    if args.stock_control and args.no_build:
        parser.error('--stock-control requires a build')
    if args.critic_output and not args.emit_coder_input:
        parser.error('--critic-output requires --emit-coder-input')
    measuring = (args.stock_baseline or args.replay_proposal or args.contrast_run_unit
                 or (args.run_iteration and not args.no_build))
    if args.fetchcontent_prebuild_receipt and (not measuring or args.no_build):
        parser.error('--fetchcontent-prebuild-receipt requires a measuring action')
    if args.stock_baseline and args.no_build:
        parser.error('--stock-baseline requires a build')
    if args.replay_proposal and args.no_build:
        parser.error('--replay-proposal requires a build')
    if (args.run_iteration or args.replay_proposal or args.contrast_run_unit) and not args.no_build and args.coder_build_authority is None:
        raise BuildAdmissionError('明示 opt-in --allow-coder-derived-build is required')
    contract = _measurement_contract(args.campaign_env) if measuring else None
    fetchcontent_options = None
    if args.fetchcontent_prebuild_receipt:
        (fetchcontent_base_dir, masstree_source_dir, mimalloc_source_dir,
         googletest_source_dir, fetchcontent_dependency_receipt) = (
            L._load_masstree_prebuild_receipt(args.fetchcontent_prebuild_receipt))
        fetchcontent_options = {
            'fetchcontent_base_dir': fetchcontent_base_dir,
            'masstree_source_dir': masstree_source_dir,
            'mimalloc_source_dir': mimalloc_source_dir,
            'googletest_source_dir': googletest_source_dir,
            'fetchcontent_dependency_receipt': fetchcontent_dependency_receipt}
    purpose = 'bootstrap' if args.stock_baseline else 'r2' if args.replay_proposal else None
    ledger = None
    if args.contrast_ledger:
        ledger, cfg = _contrast_header(args.contrast_ledger, args.form,
                                       args.campaign_env)
    else:
        cfg = default_cfg(form=args.form, campaign_env=args.campaign_env,
                          evaluation_purpose=purpose)
    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    if args.emit_coder_input:
        if args.baseline_throughput_tps is None or args.baseline_abort_rate_pct is None:
            parser.error('baseline scalars required')
        diagnosis = (L.k2_critic_diagnosis_from_bytes(Path(args.critic_output).read_bytes())
                     if args.critic_output else None)
        print(json.dumps(make_policy_coder_input(layout, baseline={
            'throughput_tps': args.baseline_throughput_tps,
            'abort_rate_pct': args.baseline_abort_rate_pct},
            critic_diagnosis=diagnosis), ensure_ascii=False))
        return 0
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=(args.coder_build_authority
                         if args.run_iteration or args.replay_proposal or args.contrast_run_unit else None)
                         if not args.no_build else None)
    stock_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    proposal = auditor = None
    if not args.stock_baseline and not args.contrast_run_unit:
        proposal_path = args.preview_diff or args.record_reject or args.run_iteration or args.replay_proposal
        if ledger is not None and ledger.header['arm'] in MACHINE_NAMES:
            proposal = load_machine_proposal(proposal_path,
                arm=ledger.header['arm'], series=ledger.header['series'], form=args.form)
        else:
            proposal, auditor = load_proposal_file(proposal_path,
                form=args.form, preview=bool(args.preview_diff or args.record_reject))
    compiler = find_compiler() if not args.stock_baseline else None
    if not args.stock_baseline and compiler is None:
        raise RuntimeError('policy compiler unavailable')
    from . import patchharness
    fixed_sub = str(ROOT / 'external/ccbench')
    patchharness.assert_pinned_clean(fixed_sub, axis.PIN)
    if measuring:
        from .p2_2 import _assert_single_tenant
        _assert_single_tenant()
    isolated = not args.no_isolate_worktree
    checkout = (patchharness.checkout(axis.PIN, base_dir=fixed_sub) if isolated
                else contextlib.nullcontext(fixed_sub))
    with checkout as sub:
        scratch = tempfile.gettempdir()
        cache_root = str(Path(fixed_sub) / 'build-variants') if isolated else ''
        measurement_log = lambda *parts: print(*parts, file=sys.stderr)
        if args.stock_baseline:
            out = run_stock_control(cfg, default_perf(), sub, layout=layout,
                cache_root=cache_root, build_context=stock_context,
                contract=contract, fetchcontent_options=fetchcontent_options,
                log=measurement_log)
            print(json.dumps(out, ensure_ascii=False))
            return 0 if out['outcome'] == 'certified-stock' else 1
        if args.preview_diff:
            from .patchharness import applied
            with applied(str(ROOT / 'patches' / axis.TEMPLATE_PATCH), axis.PIN, sub):
                result, diff = policy_gate(sub, proposal.implementation, None,
                    compiler=compiler, scratch_dir=scratch, write=False)
            print(json.dumps({'passed': result.passed, 'working_diff': diff,
                'diff_digest': compute_diff_digest(diff),
                'subtype': result.digest.get('subtype') if result.digest else None,
                'rule_id': result.digest.get('rule_id') if result.digest else None},
                ensure_ascii=False))
            return 0 if result.passed else 1
        if args.record_reject:
            if ledger is not None:
                from .silo_policy_contrast import next_unit
                pending = next_unit(ledger)
                a = pending['index'] if pending and pending['kind'] == 'eval' else 1 + sum(
                    e['kind'] == 'opportunity-end' and e.get('outcome') != 'outage'
                    for e in ledger.events)
                out = drive_contrast_record_reject(cfg, default_perf(), proposal, sub,
                    a=a, compiler=compiler, scratch_dir=scratch, layout=layout,
                    build_context=context)
            else:
                out = drive_record_reject(cfg, default_perf(), proposal, sub,
                    compiler=compiler, scratch_dir=scratch, layout=layout,
                    build_context=context)
            print(json.dumps(out, ensure_ascii=False))
            return 0
        if args.contrast_run_unit:
            try:
                out = run_contrast_unit(args.contrast_run_unit, form=args.form,
                    contract=contract, fetchcontent_options=fetchcontent_options,
                    context=context, stock_context=stock_context, sub=sub,
                    cache_root=cache_root, compiler=compiler, scratch_dir=scratch,
                    log=measurement_log)
            except ContrastUnitMismatch as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(json.dumps(out, ensure_ascii=False))
            return 0
        if args.replay_proposal:
            out = run_one_iteration(cfg, default_perf(), proposal, auditor, sub, True,
                layout=layout, compiler=compiler, scratch_dir=scratch,
                cache_root=cache_root, build_context=context, contract=contract,
                fetchcontent_options=fetchcontent_options, log=measurement_log)
        elif args.stock_control:
            from . import loop
            state = L.load_loop_state(layout) or L.LoopState(start_wall=time.time())
            iteration = state.iteration + 1
            measurement_cfg = replace(cfg, search_config={
                **cfg.search_config, 'policy_iteration': iteration})
            measurement_layout = _campaign_layout(measurement_cfg)
            candidate_error = None
            with loop.authorization_session() as session:
                try:
                    candidate = drive_iteration(cfg, default_perf(), proposal, auditor, sub,
                        True, compiler=compiler, scratch_dir=scratch, layout=layout,
                        state=state, measurement_cfg=measurement_cfg,
                        measurement_layout=measurement_layout,
                        cache_root=cache_root, build_context=context, contract=contract,
                        fetchcontent_options=fetchcontent_options,
                        authorization_session=session, log=measurement_log)
                except Exception as exc:
                    candidate_error = exc
                if candidate_error is None and candidate.get('ran') is False:
                    print(json.dumps(candidate, ensure_ascii=False))
                    return 1
                try:
                    stock = run_stock_control(measurement_cfg, default_perf(), sub,
                        layout=measurement_layout,
                        cache_root=cache_root, build_context=stock_context,
                        contract=contract,
                        fetchcontent_options=fetchcontent_options,
                        authorization_session=session, log=measurement_log)
                except Exception:
                    if candidate_error is None:
                        raise
            if candidate_error is not None:
                raise candidate_error.with_traceback(candidate_error.__traceback__)
            candidate['measurement_campaign_id'] = str(ident.campaign_id(measurement_cfg))
            out = {'candidate': candidate, 'stock': stock}
            result_code = 0 if stock['outcome'] == 'certified-stock' else 1
        else:
            out = drive_iteration(cfg, default_perf(), proposal, auditor, sub,
                not args.no_build, compiler=compiler, scratch_dir=scratch,
                layout=layout, cache_root=cache_root, build_context=context,
                contract=contract, fetchcontent_options=fetchcontent_options,
                log=measurement_log)
    print(json.dumps(out, ensure_ascii=False))
    return result_code if args.stock_control else 0


if __name__ == '__main__':
    raise SystemExit(main())
