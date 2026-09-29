#!/usr/bin/env python3
"""Login-side ledger, proposal and PBS launcher for the silo contrast."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign.silo_policy_contrast import (ARMS, DEFAULT_BUDGETS,
    UNIT_SCHEMA, ContrastLedger, _publish, next_unit, select_endpoint, series_state)
from orchestrator.campaign.silo_policy_contrast_generators import random_ir, evolve_ir


def _run(argv, **kwargs):
    return subprocess.run(argv, text=True, capture_output=True, **kwargs)


def _head(checkout):
    result = _run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'])
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'cannot read checkout HEAD')
    return result.stdout.strip()


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def init(args):
    checkout = Path(args.checkout).resolve(strict=True)
    if args.arm not in ARMS:
        raise ValueError('unknown arm')
    if args.arm == 'reference' and not 1 <= args.series <= 3:
        raise ValueError('reference series must be batch 1..3')
    ledger = ContrastLedger.create(args.ledger, {
        'version': args.version, 'cohort': args.cohort, 'arm': args.arm,
        'series': args.series, 'form': ARMS[args.arm],
        'submit_checkout': str(checkout), 'checkout_head': _head(checkout),
        'pin': args.pin, 'budgets': DEFAULT_BUDGETS})
    ledger.append('series-start')
    print(ledger.root)


def _driver(ledger, proposal, flag, out):
    argv = [sys.executable, '-m', 'orchestrator.campaign.p3_s4_loop_policy',
            '--form', 'ir', '--campaign-env', 'pegasus',
            '--contrast-ledger', str(ledger.root), flag, str(proposal)]
    result = _run(argv, cwd=ledger.header['submit_checkout'])
    if result.stdout:
        _publish(out, json.loads(result.stdout))
    return result


def generate(args):
    ledger = ContrastLedger(args.ledger)
    arm = ledger.header['arm']
    if arm not in ('random-ir', 'evo-ir'):
        raise ValueError('generate requires a machine arm')
    state = series_state(ledger)
    if next_unit(ledger) is not None or state['unfinished_slots']:
        raise ValueError('outstanding unit')
    if state['A'] >= ledger.header['budgets']['A'] or state['B'] >= ledger.header['budgets']['B']:
        raise ValueError('series budget exhausted')
    a = state['A'] + 1
    if any(e['kind'] == 'opportunity-start' and e.get('a') == a for e in ledger.events):
        raise ValueError('opportunity already started')
    ledger.append('opportunity-start', a=a)
    version = ledger.header['version']
    if arm == 'random-ir':
        document, provenance = random_ir(version, ledger.header['series'], a)
    else:
        document, provenance = evolve_ir(version, ledger.header['series'], a,
                                         state['evolution_points'])
    if document is None:
        ledger.append('opportunity-end', a=a, outcome='empty', provenance=provenance)
        print(json.dumps({'a': a, 'outcome': 'empty'}))
        return
    proposal = ledger.root / f'proposal-{a:02d}.json'
    _publish(proposal, {'generator': provenance, 'ir': document})
    preview = ledger.root / f'preview-{a:02d}.json'
    result = _driver(ledger, proposal, '--preview-diff', preview)
    if result.returncode not in (0, 1):
        raise RuntimeError(f'driver preview failed: {result.stderr.strip()}')
    verdict = json.loads(preview.read_text())
    if verdict.get('passed') is True:
        outcome = 'proposed'
    else:
        rejected = ledger.root / f'rejected-{a:02d}.json'
        record = _driver(ledger, proposal, '--record-reject', rejected)
        if record.returncode:
            raise RuntimeError(f'driver reject record failed: {record.stderr.strip()}')
        outcome = 'rejected'
    ledger.append('opportunity-end', a=a, outcome=outcome,
                  proposal_path=str(proposal), proposal_sha256=_digest(proposal),
                  provenance=provenance)
    print(json.dumps({'a': a, 'outcome': outcome, 'proposal_path': str(proposal)}))


def _proposal_for(ledger, unit):
    if unit['kind'] != 'eval':
        return None
    matches = [e for e in ledger.events if e['kind'] == 'opportunity-end'
               and e.get('a') == unit['index'] and e.get('outcome') == 'proposed']
    if len(matches) != 1:
        raise ValueError('evaluation proposal missing')
    path = Path(matches[0]['proposal_path']).resolve(strict=True)
    if _digest(path) != unit['proposal_sha256']:
        raise ValueError('proposal digest changed')
    return str(path)


def _qsub_argv(ledger, unit_path, evidence, archive, walltime, after, hold):
    checkout = Path(ledger.header['submit_checkout'])
    head = _head(checkout)
    if head != ledger.header['checkout_head']:
        raise ValueError('submit checkout HEAD changed')
    env = {
        'IZANAGI_S4_REPO_ROOT': str(checkout),
        'IZANAGI_S4_EXPECTED_HEAD': head,
        'IZANAGI_S4_THIRDPARTY_SOURCE_ROOT': str(checkout / 'output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src'),
        'IZANAGI_S4_EVIDENCE_ROOT': str(evidence),
        'IZANAGI_S4_POLICY_MODE': 'contrast',
        'IZANAGI_S4_POLICY_FORM': ledger.header['form'],
        'IZANAGI_S4_POLICY_UNIT_PATH': str(unit_path),
        'IZANAGI_TRACE_ARCHIVE_ROOT': str(archive),
    }
    if any(',' in value or '\n' in value for value in env.values()):
        raise ValueError('PBS environment value contains delimiter')
    argv = ['qsub']
    if hold:
        argv.append('-h')
    if after:
        argv += ['--after', after]
    argv += ['-v', ','.join(f'{key}={value}' for key, value in env.items()),
             '-l', f'elapstim_req={walltime}', '-o', str(evidence / 'job.stdout'),
             '-e', str(evidence / 'job.stderr'),
             str(checkout / 'tools/pegasus/p3_s4_loop_pegasus.sh')]
    return argv


def submit(args):
    ledger = ContrastLedger(args.ledger)
    unit = next_unit(ledger)
    if unit is None:
        raise ValueError('no unit ready')
    if unit['kind'] == 'dead-job':
        raise ValueError('dead-job: unfinished slot; manual classification required')
    if unit['kind'] == 'score' and not any(e['kind'] == 'endpoint-fixed' for e in ledger.events):
        ledger.append('endpoint-fixed', endpoint=select_endpoint(ledger))
    proposal = _proposal_for(ledger, unit)
    unit_path = (ledger.root / 'units' / f"{unit['kind']}-{unit['index']}-a{unit['attempt']}.json").resolve()
    unit_path.parent.mkdir(exist_ok=True)
    payload = {'schema': UNIT_SCHEMA, 'ledger_root': str(ledger.root),
               'kind': unit['kind'], 'index': unit['index'], 'attempt': unit['attempt'],
               'proposal_path': proposal, 'proposal_sha256': unit['proposal_sha256']}
    if unit_path.exists():
        if json.loads(unit_path.read_text()) != payload:
            raise ValueError('existing unit differs')
    else:
        _publish(unit_path, payload)
    evidence = Path(args.evidence_root).resolve() / unit_path.stem
    archive = Path(args.archive_root).resolve() / unit_path.stem
    argv = _qsub_argv(ledger, unit_path, evidence, archive,
                       args.walltime, args.after, args.hold)
    print(json.dumps({'unit': payload, 'qsub_argv': argv}))
    if args.submit:
        if evidence.exists() or archive.exists():
            raise ValueError('evidence or archive already exists')
        evidence.mkdir(parents=True)
        archive.mkdir(parents=True)
        result = _run(argv, cwd=ledger.header['submit_checkout'])
        print(result.stdout, end='')
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or 'qsub failed')


def status(args):
    ledger = ContrastLedger(args.ledger)
    print(json.dumps({'header': ledger.header, 'state': series_state(ledger),
                      'next_unit': next_unit(ledger)}, default=str, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'generate', 'submit', 'status'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--ledger', required=True)
        if name == 'init':
            for key in ('checkout', 'cohort', 'arm', 'version', 'pin'):
                cmd.add_argument('--' + key, required=True)
            cmd.add_argument('--series', type=int, required=True)
        if name == 'submit':
            for key in ('evidence-root', 'archive-root', 'walltime'):
                cmd.add_argument('--' + key, required=True)
            cmd.add_argument('--after')
            cmd.add_argument('--hold', action='store_true')
            cmd.add_argument('--submit', action='store_true')
    args = parser.parse_args(argv)
    try:
        {'init': init, 'generate': generate, 'submit': submit, 'status': status}[args.command](args)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f'{exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
