"""Policy campaign driver; see D2214 and docs/phase3-silo-policy-runbook.md."""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import tempfile
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import axis_silo_function_policy as axis
from . import env_contract, ident, p3_s4_loop as L
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
from .model import CampaignConfig, Genome, STAGE_ABORT
from .pipeline import SEARCH_CONFIG_VERIFY_KEY, VERIFY_LEGACY_PLUS_PERFORMANCE, PerfConfig
from .projection_guard import assert_closed_proposal_schema
from .silo_policy_compile import check_policy_body, find_compiler
from .silo_policy_ir import parse_policy_ir, render_policy
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


def default_cfg(*, form, reflux=True):
    if form not in ('cpp', 'ir'):
        raise ValueError('unknown form')
    cfg = CampaignConfig(
        spec_slug='p3-silo-policy-loop', search_tag='silo-policy-autonomous',
        spec_content='Silo function policy; D2214.', ccbench_commit=axis.PIN,
        search_config={'scale': 'silo', 'axis': axis.MARKER_ID, 'form': form,
                       'reflux': 'on' if reflux else 'off',
                       'perf': _perf_identity(default_perf()),
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_PERFORMANCE},
        trial='p3-silo-policy-loop')
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    return ident.bind_environment_contract(
        ident.bind_admission_policy(cfg, context.policy), env_contract.lookup(ENV_TAG))


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


def policy_gate(sub, implementation, auditor, *, compiler, scratch_dir, write):
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
        if auditor is None:
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
           'justification': proposal.justification}
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


def run_one_iteration(cfg, perf, proposal, auditor, sub, do_build, *,
                      layout, compiler, scratch_dir, build_context,
                      cache_root='', log=print):
    _require_perf_identity(cfg, perf)
    if cfg.search_config.get('form') != ('ir' if proposal.ir is not None else 'cpp'):
        raise ValueError('policy form mismatch')
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
    genome = Genome('silo', dict(BASE))
    layout.ensure()
    if do_build:
        ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)
    from .patchharness import applied
    with applied(str(ROOT / 'patches' / axis.TEMPLATE_PATCH), axis.PIN, sub):
        result, _diff = policy_gate(sub, proposal.implementation, auditor,
            compiler=compiler, scratch_dir=scratch_dir, write=do_build)
        if not result.passed:
            if not do_build:
                return {'outcome': 'rejected', 'variant': None, 'digest': result.digest}
            variant = L.record_diff_reject(layout, genome, proposal.implementation,
                                           result, env_tag=ENV_TAG)
            return {'outcome': 'rejected', 'variant': variant, 'digest': result.digest}
        if not do_build:
            return {'outcome': 'dry-pass', 'variant': None}
        summary = run_campaign(cfg, [genome], perf, ENV_TAG, 1800,
            numactl=['numactl', '--interleave=all'], log=log,
            ccbench_dir=sub, cache_root=cache_root,
            authorization_contract=env_contract.authorize(ENV_TAG),
            build_context=build_context, declared_use_class=DECLARED_USE_CLASS)
    result = summary.results[0] if summary.results else None
    outcome, verifier_digest = _result_history(layout, result)
    return {'outcome': outcome,
            'variant': result.variant if result else None,
            'verdict': result.verdict if result else None,
            'verifier_digest': verifier_digest}


def drive_iteration(cfg, perf, proposal, auditor, sub, do_build, *,
                    compiler, scratch_dir, build_context, layout=None,
                    cache_root='', log=print):
    _require_perf_identity(cfg, perf)
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
    if layout is None:
        layout = _campaign_layout(cfg)
    layout.ensure()
    state = L.load_loop_state(layout) or L.LoopState(start_wall=time.time())
    state.whiteboard.clear()
    state.reverse_recommendations = 0
    stop = L.check_stop(state)
    if stop.stop:
        L.save_loop_state(layout, state)
        return {'outcome': 'stopped-before', 'variant': None,
                'stop_reason': stop.reason, 'iteration': state.iteration, 'ran': False}
    state.iteration += 1
    try:
        out = run_one_iteration(cfg, perf, proposal, auditor, sub, do_build,
            layout=layout, compiler=compiler, scratch_dir=scratch_dir,
            cache_root=cache_root, build_context=build_context, log=log)
    finally:
        L.save_loop_state(layout, state)
    if do_build:
        _append_history(layout, state.iteration, proposal, out)
        view = require_admitted_campaign(layout.root,
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
    cfg = ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
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
                                   proposal.implementation, result, env_tag=ENV_TAG)
    state.iteration += 1
    L.save_loop_state(layout, state)
    out = {'outcome': 'rejected', 'variant': variant, 'digest': result.digest}
    _append_history(layout, state.iteration, proposal, out)
    stop = L.check_stop(state)
    out.update({'stop_reason': stop.reason, 'iteration': state.iteration, 'ran': True})
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description='Silo function-policy campaign')
    parser.add_argument('--form', choices=('cpp', 'ir'), required=True)
    parser.add_argument('--preview-diff', metavar='PROPOSAL.json')
    parser.add_argument('--record-reject', metavar='CODER.json')
    parser.add_argument('--run-iteration', metavar='PROPOSAL.json')
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
                             args.run_iteration, args.emit_coder_input)) != 1:
        parser.error('select one action')
    if args.critic_output and not args.emit_coder_input:
        parser.error('--critic-output requires --emit-coder-input')
    cfg = default_cfg(form=args.form)
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
    if args.run_iteration and not args.no_build and args.coder_build_authority is None:
        raise BuildAdmissionError('明示 opt-in --allow-coder-derived-build is required')
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=None if args.no_build or args.preview_diff or args.record_reject
        else args.coder_build_authority)
    proposal, auditor = load_proposal_file(
        args.preview_diff or args.record_reject or args.run_iteration,
        form=args.form, preview=bool(args.preview_diff or args.record_reject))
    compiler = find_compiler()
    if compiler is None:
        raise RuntimeError('policy compiler unavailable')
    from . import patchharness
    fixed_sub = str(ROOT / 'external/ccbench')
    patchharness.assert_pinned_clean(fixed_sub, axis.PIN)
    if args.run_iteration and not args.no_build:
        from .p2_2 import _assert_single_tenant
        _assert_single_tenant()
    isolated = not args.no_isolate_worktree
    checkout = (patchharness.checkout(axis.PIN, base_dir=fixed_sub) if isolated
                else contextlib.nullcontext(fixed_sub))
    with checkout as sub:
        scratch = tempfile.gettempdir()
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
            out = drive_record_reject(cfg, default_perf(), proposal, sub,
                compiler=compiler, scratch_dir=scratch, layout=layout,
                build_context=context)
            print(json.dumps(out, ensure_ascii=False))
            return 0
        out = drive_iteration(cfg, default_perf(), proposal, auditor, sub,
            not args.no_build, compiler=compiler, scratch_dir=scratch,
            layout=layout, cache_root=str(Path(fixed_sub) / 'build-variants') if isolated else '',
            build_context=context)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
