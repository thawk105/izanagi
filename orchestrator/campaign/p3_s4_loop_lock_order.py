"""Thin Silo lock order campaign driver with model and witness admission."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import tempfile

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = 'orchestrator.campaign'

from . import p3_s4_loop_policy as P
from . import axis_silo_lock_order as axis
from . import env_contract, ident, p3_s4_loop as L, site_policy, wal
from .auditor_gate import parse_auditor_dict
from .build_admission import (BuildAdmissionError, GeneratorId,
                              add_registered_coder_build_authority_argument,
                              build_run_context)
from .layout import exploration_campaign_layout
from .loop import run_campaign
from .model import CampaignConfig, Genome, STAGE_VERIFY_DONE
from .pipeline import SEARCH_CONFIG_VERIFY_KEY, VERIFY_LEGACY_PLUS_PERFORMANCE
from .silo_lock_order_gate import order_gate
from .silo_lock_order_compile import find_compiler
from .silo_lock_order_model_gate import ModelDecision, ModelRegistry, check_model_result
from ..verifier.report import result_to_dict

ROOT = Path(__file__).resolve().parents[2]
HISTORY_NAME = 'lock_order_history.jsonl'
DECLARED_USE_CLASS = 'exploration'
BASE = {'BACK_OFF': 1, 'NO_WAIT_LOCKING_IN_VALIDATION': 1,
        'NO_WAIT_OF_TICTOC': 0, 'WAL': 0, axis.FLAG: 1}
_COUNTS = ('unreachable', 'D1a', 'D1b1', 'D1b2', 'D1c', 'D2a', 'D2b_i', 'D2b_ii')
HISTORY_KEYS = frozenset({
    'schema', 'iteration', 'axis', 'proposal_digest', 'variant_id', 'outcome',
    'reject_code', 'model_specification_digest', 'model_evidence_kind',
    'model_scenario_ids', 'counterexamples', 'verifier_digest',
    'measurement_campaign_id',
})
_VERIFIER_KEYS = frozenset({'verdict', 'certified', 'gate_counts', 'D5'})
_EVIDENCE_KINDS = frozenset({'registered', 'fixture', 'unregistered'})
_ATOMIC = re.compile(r'[A-Za-z0-9_.:-]{1,128}\Z')
_REJECT_CODES = frozenset({
    'order-gate-rejected', 'gate-witness-missing', 'gate-witness-not-required',
    'gate-witness-version', 'gate-witness-invalid', 'gate-d5-not-pass',
    'verifier-not-certified', 'verifier-result-missing', 'campaign-not-certified',
    'campaign-skipped', 'campaign-result-missing',
}) | frozenset({
    'model-unregistered', 'model-result-missing', 'model-result-invalid',
    'model-digest-mismatch', 'model-scenario-missing', 'model-incomplete',
    'model-coverage-mismatch', 'model-witness-missing', 'model-counterexample',
})


@dataclass(frozen=True)
class LockOrderProposal:
    implementation: str
    auditor: object | None
    origin: str | None


def load_lock_order_proposal(path, *, named_control=None):
    """Read a closed proposal, or the named hand control as origin=initial."""
    if named_control is not None:
        if named_control not in axis.HAND_POLICIES:
            raise ValueError('unknown named control')
        body = (ROOT / axis.HAND_POLICY_DIR / axis.HAND_POLICIES[named_control]).read_text(
            encoding='utf-8')
        return LockOrderProposal(body, None, 'initial')
    if path is None:
        raise ValueError('proposal path required')
    with open(path, encoding='utf-8') as stream:
        document = json.load(stream, object_pairs_hook=P._unique_pairs,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON')))
    if type(document) is not dict or set(document) != {'coder', 'auditor'}:
        raise ValueError('invalid proposal envelope')
    coder = document['coder']
    if (type(coder) is not dict or not {'axis', 'implementation'} <= set(coder)
            or set(coder) - {'axis', 'implementation', 'justification', 'confidence'}
            or coder['axis'] != axis.MARKER_ID
            or type(coder['implementation']) is not str
            or type(coder.get('justification', '')) is not str
            or coder.get('confidence', 'medium') not in ('high', 'medium', 'low')):
        raise ValueError('invalid coder proposal')
    auditor = parse_auditor_dict(document['auditor'], max_violation_type=30)
    return LockOrderProposal(coder['implementation'], auditor, None)


def production_registry():
    return ModelRegistry(axis.MODEL_SPECIFICATION_DIGEST,
                         axis.MODEL_SCENARIOS, axis.MODEL_VOCABULARY)


def default_cfg(*, campaign_env=P.ENV_TAG):
    if campaign_env not in (P.ENV_TAG, 'pegasus'):
        raise ValueError('unknown campaign environment')
    cfg = CampaignConfig(
        spec_slug='p3-silo-lock-order-loop', search_tag='silo-lock-order-model-gated',
        spec_content='Silo lock order policy; model and gate witness required.',
        ccbench_commit=axis.PIN,
        search_config={'scale': 'silo', 'axis': axis.MARKER_ID,
                       'perf': P._perf_identity(P.default_perf()),
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_PERFORMANCE},
        trial='p3-silo-lock-order-loop')
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(cfg, context.policy)
    if campaign_env == 'pegasus':
        return L._campaign_cfg_for_site(cfg, site_policy.PEGASUS_COMPUTE,
                                        _contract=env_contract.lookup('pegasus'))
    return ident.bind_environment_contract(cfg, env_contract.lookup(P.ENV_TAG))


def _counterexample_projection(model: ModelDecision):
    # Values are validated Counterexample objects; project only bounded atomic fields.
    return [{'scenario_id': item.scenario_id, 'judgment_id': item.judgment_id,
             'rule_ids': list(item.rule_ids[:8])}
            for item in model.counterexamples[:2]]


def _row(iteration, proposal, model, *, outcome, reject_code=None,
         variant_id=None, verifier_digest=None, measurement_campaign_id=None,
         model_evidence_kind='unregistered'):
    if model_evidence_kind not in _EVIDENCE_KINDS:
        raise ValueError('invalid model evidence kind')
    row = {
        'schema': 'silo-lock-order-history/1', 'iteration': iteration,
        'axis': axis.MARKER_ID,
        'proposal_digest': 'sha256:' + sha256(proposal.implementation.encode()).hexdigest(),
        'variant_id': variant_id, 'outcome': outcome, 'reject_code': reject_code,
        'model_specification_digest': model.specification_digest,
        'model_evidence_kind': model_evidence_kind,
        'model_scenario_ids': list(model.scenario_ids),
        'counterexamples': _counterexample_projection(model),
        'verifier_digest': verifier_digest,
        'measurement_campaign_id': measurement_campaign_id,
    }
    assert set(row) == HISTORY_KEYS
    return row


def history_row_from_verification(verification, *, iteration, proposal, model,
                                  variant_id=None, measurement_campaign_id=None,
                                  model_evidence_kind=None):
    """Project one result; the standalone route labels registered fixtures as fixture."""
    if model_evidence_kind is None:
        model_evidence_kind = ('unregistered' if model.reject_code == 'model-unregistered'
                               else 'fixture')
    data = result_to_dict(verification) if not isinstance(verification, dict) else verification
    if type(data) is not dict:
        raise ValueError('invalid verification')
    gate = data.get('gate_witness')
    counts = gate.get('counts') if type(gate) is dict else None
    closed_counts = (type(counts) is dict and set(_COUNTS) <= set(counts)
                     and all(type(counts[key]) is int and counts[key] >= 0 for key in _COUNTS))
    digest = {'verdict': data.get('verdict') if data.get('verdict') in
              ('serializable', 'indeterminate', 'non-serializable') else 'indeterminate',
              'certified': data.get('certified') is True,
              'gate_counts': {key: counts[key] for key in _COUNTS} if closed_counts else None,
              'D5': gate.get('D5') if type(gate) is dict and gate.get('D5') in
              ('pass', 'fail', 'unavailable', 'not-required') else 'unavailable'}
    assert set(digest) == _VERIFIER_KEYS
    if not model.passed:
        code = model.reject_code or 'model-result-invalid'
    elif gate is None or type(gate) is not dict:
        code = 'gate-witness-missing'
    elif gate.get('required') is not True:
        code = 'gate-witness-not-required'
    elif type(gate.get('meaning_version')) is not int or gate['meaning_version'] < 2:
        code = 'gate-witness-version'
    elif not closed_counts:
        code = 'gate-witness-invalid'
    elif gate.get('D5') != 'pass':
        code = 'gate-d5-not-pass'
    elif data.get('certified') is not True:
        code = 'verifier-not-certified'
    else:
        code = None
    return _row(iteration, proposal, model,
                outcome='certified' if code is None else 'rejected', reject_code=code,
                variant_id=variant_id, verifier_digest=digest,
                measurement_campaign_id=measurement_campaign_id,
                model_evidence_kind=model_evidence_kind)


def history_row_from_attempt(layout, *, attempt_id, variant_id, iteration,
                             proposal, model, measurement_campaign_id,
                             result_certified):
    """Check every verify_done record for one variant and build attempt."""
    base = dict(iteration=iteration, proposal=proposal, model=model,
                variant_id=variant_id, measurement_campaign_id=measurement_campaign_id,
                model_evidence_kind='registered')
    try:
        records = [record for record in wal.read_records(layout)
                   if record.variant == variant_id and record.stage == STAGE_VERIFY_DONE
                   and record.payload.get('build_attempt_id') == attempt_id]
    except (OSError, ValueError, UnicodeError):
        records = []
    if not records:
        return _row(**base, outcome='rejected', reject_code='verifier-result-missing')
    projected = [history_row_from_verification({
        'verdict': record.payload.get('verdict'),
        'certified': record.payload.get('certified'),
        'gate_witness': record.payload.get('gate_witness'),
    }, **base) for record in records]
    row = projected[0]
    # Sum the eight validated counters across all repetitions.
    digests = [item['verifier_digest'] for item in projected]
    if all(digest['gate_counts'] is not None for digest in digests):
        row['verifier_digest']['gate_counts'] = {
            key: sum(digest['gate_counts'][key] for digest in digests)
            for key in _COUNTS}
    else:
        row['verifier_digest']['gate_counts'] = None
    if any(digest['D5'] != 'pass' for digest in digests):
        row['verifier_digest']['D5'] = next(
            digest['D5'] for digest in digests if digest['D5'] != 'pass')
    failure = next((item['reject_code'] for item in projected
                    if item['reject_code'] is not None), None)
    if failure is None and result_certified is not True:
        failure = 'campaign-not-certified'
    row['outcome'] = 'certified' if failure is None else 'rejected'
    row['reject_code'] = failure
    row['verifier_digest']['certified'] = failure is None
    return row


def _append_history(layout, row):
    if set(row) != HISTORY_KEYS:
        raise ValueError('history row is not closed')
    layout.ensure()
    with (Path(layout.root) / HISTORY_NAME).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')


def _closed_history_row(row):
    if type(row) is not dict or set(row) != HISTORY_KEYS:
        return False
    if (row['schema'] != 'silo-lock-order-history/1' or row['axis'] != axis.MARKER_ID
            or type(row['iteration']) is not int or row['iteration'] < 0
            or type(row['proposal_digest']) is not str
            or not re.fullmatch(r'sha256:[0-9a-f]{64}', row['proposal_digest'])
            or row['outcome'] not in ('certified', 'rejected', 'skipped', 'dry-pass')
            or row['reject_code'] is not None and
            (type(row['reject_code']) is not str or row['reject_code'] not in _REJECT_CODES)
            or row['model_evidence_kind'] not in _EVIDENCE_KINDS
            or row['model_specification_digest'] is not None and
            (type(row['model_specification_digest']) is not str or not re.fullmatch(
                r'sha256:[0-9a-fA-F]{64}', row['model_specification_digest']))):
        return False
    for key in ('variant_id', 'measurement_campaign_id'):
        value = row[key]
        if value is not None and (type(value) is not str or not _ATOMIC.fullmatch(value)):
            return False
    ids = row['model_scenario_ids']
    if type(ids) is not list or len(ids) > 4096 or any(
            type(value) is not str or not _ATOMIC.fullmatch(value) for value in ids):
        return False
    examples = row['counterexamples']
    if type(examples) is not list or len(examples) > 2:
        return False
    for item in examples:
        if type(item) is not dict or set(item) != {'scenario_id', 'judgment_id', 'rule_ids'}:
            return False
        if any(type(item[key]) is not str or not _ATOMIC.fullmatch(item[key])
               for key in ('scenario_id', 'judgment_id')):
            return False
        rules = item['rule_ids']
        if type(rules) is not list or len(rules) > 8 or any(
                type(rule) is not str or not _ATOMIC.fullmatch(rule) for rule in rules):
            return False
    digest = row['verifier_digest']
    if digest is None:
        return True
    if (type(digest) is not dict or set(digest) != _VERIFIER_KEYS
            or digest['verdict'] not in ('serializable', 'indeterminate', 'non-serializable')
            or type(digest['certified']) is not bool
            or digest['D5'] not in ('pass', 'fail', 'unavailable', 'not-required')):
        return False
    counts = digest['gate_counts']
    return counts is None or (type(counts) is dict and set(counts) == set(_COUNTS)
        and all(type(counts[key]) is int and counts[key] >= 0 for key in _COUNTS))


def make_lock_order_coder_input(layout):
    history = []
    path = Path(layout.root) / HISTORY_NAME
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line, object_pairs_hook=P._unique_pairs)
            if not _closed_history_row(row):
                raise ValueError('invalid history row')
            history.append(row)
    return {'axis': axis.MARKER_ID,
            'policy_spec': {'api_header': axis.API_HEADER, 'source': axis.SOURCE_REL},
            'self_history': history}


def run_one_iteration(cfg, perf, proposal, sub, model_result_bytes, *, layout,
                      iteration, compiler, scratch_dir, build_context,
                      do_build=True, cache_root='', contract=None,
                      fetchcontent_options=None, log=print):
    """Use only the production registry; no fixture override reaches this path."""
    P._require_perf_identity(cfg, perf)
    contract = contract or P._cfg_contract(cfg)
    model = None
    from .patchharness import applied
    with applied(str(ROOT / 'patches' / axis.TEMPLATE_PATCH), axis.PIN, sub):
        preview, _ = order_gate(sub, proposal.implementation, proposal.auditor,
                                compiler=compiler, scratch_dir=scratch_dir, write=False,
                                origin=proposal.origin)
        if not preview.passed:
            model = check_model_result(None, production_registry())
            row = _row(iteration, proposal, model, outcome='rejected',
                       reject_code='order-gate-rejected',
                       model_evidence_kind='unregistered' if
                       model.reject_code == 'model-unregistered' else 'registered')
        else:
            model = check_model_result(model_result_bytes, production_registry())
            evidence_kind = ('unregistered' if model.reject_code == 'model-unregistered'
                             else 'registered')
            if not model.passed:
                row = _row(iteration, proposal, model, outcome='rejected',
                           reject_code=model.reject_code, model_evidence_kind=evidence_kind)
            elif not do_build:
                row = _row(iteration, proposal, model, outcome='dry-pass',
                           model_evidence_kind=evidence_kind)
            else:
                written, _ = order_gate(sub, proposal.implementation, proposal.auditor,
                                    compiler=compiler, scratch_dir=scratch_dir,
                                    write=True, origin=proposal.origin)
                if not written.passed:
                    row = _row(iteration, proposal, model, outcome='rejected',
                           reject_code='order-gate-rejected', model_evidence_kind=evidence_kind)
                else:
                    genome = Genome('silo', dict(BASE))
                    options = P._measurement_options(build_context=build_context,
                    contract=contract, fetchcontent_options=fetchcontent_options)
                    summary = run_campaign(cfg, [genome], perf, contract.env_tag,
                    contract.clocks_per_us, numactl=list(contract.numactl), log=log,
                    ccbench_dir=sub, cache_root=cache_root,
                    authorization_contract=env_contract.authorize(contract.env_tag),
                    build_context=build_context, declared_use_class=DECLARED_USE_CLASS,
                    require_gate_witness=True, **options)
                    campaign_id = str(ident.campaign_id(cfg))
                    if summary.skipped or getattr(summary, 'identity_skipped', 0):
                        row = _row(iteration, proposal, model, outcome='skipped',
                                   reject_code='campaign-skipped',
                                   variant_id=summary.skipped_variants[0]
                                   if summary.skipped_variants else None,
                                   measurement_campaign_id=campaign_id,
                                   model_evidence_kind=evidence_kind)
                    elif summary.results:
                        result = summary.results[0]
                        row = history_row_from_attempt(layout,
                            attempt_id=result.build_attempt_id,
                            variant_id=result.variant, iteration=iteration,
                            proposal=proposal, model=model,
                            measurement_campaign_id=campaign_id,
                            result_certified=result.certified is True and not result.aborted)
                    else:
                        row = _row(iteration, proposal, model, outcome='rejected',
                                   reject_code='campaign-result-missing',
                                   measurement_campaign_id=campaign_id,
                                   model_evidence_kind=evidence_kind)
    if do_build or row['outcome'] == 'rejected':
        _append_history(layout, row)
    return row


def main(argv=None):
    parser = argparse.ArgumentParser(description='Silo lock order campaign')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--run-iteration', metavar='PROPOSAL.json')
    action.add_argument('--initial-control', choices=tuple(axis.HAND_POLICIES))
    action.add_argument('--emit-coder-input', action='store_true')
    parser.add_argument('--model-result', metavar='RESULT.json')
    parser.add_argument('--campaign-env', choices=(P.ENV_TAG, 'pegasus'), default=P.ENV_TAG)
    parser.add_argument('--fetchcontent-prebuild-receipt', metavar='PATH')
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('--no-isolate-worktree', action='store_true')
    add_registered_coder_build_authority_argument(
        parser, coder_entrypoint_site='orchestrator.campaign.p3_s4_loop_lock_order.main')
    args = parser.parse_args(argv)
    cfg = default_cfg(campaign_env=args.campaign_env)
    layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))
    if args.emit_coder_input:
        print(json.dumps(make_lock_order_coder_input(layout), ensure_ascii=False))
        return 0
    if not args.no_build and args.coder_build_authority is None:
        raise BuildAdmissionError('明示 opt-in --allow-coder-derived-build is required')
    proposal = load_lock_order_proposal(args.run_iteration,
                                         named_control=args.initial_control)
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=args.coder_build_authority if not args.no_build else None)
    model_bytes = Path(args.model_result).read_bytes() if args.model_result else None
    compiler = find_compiler()
    if compiler is None:
        raise RuntimeError('policy compiler unavailable')
    from . import patchharness
    fixed_sub = str(ROOT / 'external/ccbench')
    patchharness.assert_pinned_clean(fixed_sub, axis.PIN)
    checkout = (patchharness.checkout(axis.PIN, base_dir=fixed_sub)
                if not args.no_isolate_worktree else P.contextlib.nullcontext(fixed_sub))
    with checkout as sub:
        row = run_one_iteration(cfg, P.default_perf(), proposal, sub, model_bytes,
            layout=layout, iteration=1, compiler=compiler,
            scratch_dir=tempfile.gettempdir(), build_context=context,
            do_build=not args.no_build, cache_root=str(Path(fixed_sub) / 'build-variants'),
            contract=P._measurement_contract(args.campaign_env) if not args.no_build else None)
    print(json.dumps(row, sort_keys=True, ensure_ascii=False))
    return 0 if row['outcome'] in ('certified', 'dry-pass') else 1


if __name__ == '__main__':
    raise SystemExit(main())
