"""Immutable per-series ledger and scheduling state for the silo contrast."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

LEDGER_SCHEMA = 'silo-policy-contrast-ledger/v1'
UNIT_SCHEMA = 'silo-policy-contrast-unit/v1'
EVENT_KINDS = frozenset(('series-start', 'slot-start', 'slot-result',
    'opportunity-start', 'opportunity-end', 'critic-result', 'endpoint-fixed', 'series-end'))
END_REASONS = frozenset(('b-complete', 'a-exhausted', 'machine-retry-exhausted',
    'stock-unestablished', 'model-mismatch', 'unclassified-missing', 'dead-job'))
ARMS = {'llm-cpp': 'cpp', 'llm-ir': 'ir', 'random-ir': 'ir',
        'evo-ir': 'ir', 'reference': 'cpp'}
DEFAULT_BUDGETS = {'B': 10, 'A': 30, 'k': 2, 'n_eval': 5,
                   'machine_retries': 2, 'role_retries': 2}


def _publish(path, document):
    path = Path(path)
    data = (json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()
    fd, name = tempfile.mkstemp(prefix='.contrast-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(name).unlink(missing_ok=True)


class ContrastLedger:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.header = json.loads((self.root / 'header.json').read_text())
        if self.header.get('schema') != LEDGER_SCHEMA:
            raise ValueError('unknown ledger schema')
        if self.header.get('form') != ARMS.get(self.header.get('arm')):
            raise ValueError('arm/form mismatch')
        self.events = []
        for seq, path in enumerate(sorted((self.root / 'events').glob('*.json')), 1):
            event = json.loads(path.read_text())
            if (event.get('event_seq') != seq or event.get('kind') not in EVENT_KINDS
                    or path.name != f"{seq:06d}-{event['kind']}.json"):
                raise ValueError('invalid ledger event sequence')
            self.events.append(event)

    @classmethod
    def create(cls, root, header):
        root = Path(root)
        document = {**header, 'schema': LEDGER_SCHEMA}
        if document.get('form') != ARMS.get(document.get('arm')):
            raise ValueError('arm/form mismatch')
        if document.get('budgets') != DEFAULT_BUDGETS:
            raise ValueError('budget mismatch')
        root.mkdir(parents=True, exist_ok=False)
        (root / 'events').mkdir()
        _publish(root / 'header.json', document)
        return cls(root)

    def append(self, kind, **values):
        if kind not in EVENT_KINDS:
            raise ValueError('unknown event kind')
        if self.events and self.events[-1]['kind'] == 'series-end':
            raise ValueError('series already ended')
        if kind == 'series-end' and values.get('reason') not in END_REASONS:
            raise ValueError('unknown series end reason')
        if kind == 'opportunity-end' and values.get('outcome') not in (
                'proposed', 'rejected', 'empty', 'outage', 'role-failure'):
            raise ValueError('unknown opportunity outcome')
        event = json.loads(json.dumps({**values, 'kind': kind,
            'event_seq': len(self.events) + 1,
            'ts_utc': datetime.now(timezone.utc).isoformat()}))
        _publish(self.root / 'events' / f"{event['event_seq']:06d}-{kind}.json", event)
        self.events.append(event)
        return event


def _ledger(ledger):
    return ledger if isinstance(ledger, ContrastLedger) else ContrastLedger(ledger)


def _slot_key(event):
    return event.get('logical_slot'), event.get('attempt', 0)


def series_state(ledger):
    ledger = _ledger(ledger)
    events = ledger.events
    starts = [e for e in events if e['kind'] == 'slot-start']
    results = [e for e in events if e['kind'] == 'slot-result']
    result_keys = {_slot_key(e) for e in results}
    unfinished = [e for e in starts if _slot_key(e) not in result_keys]
    a_used = sum(e['kind'] == 'opportunity-end' and e.get('outcome') in
                 ('proposed', 'rejected', 'empty') for e in events)
    b_used = len({e['logical_slot'] for e in starts if
                  e.get('logical_slot', '').startswith('eval-') and e.get('attempt', 0) == 0})
    eligible = []
    for event in results:
        slot = event.get('logical_slot', '')
        if (event.get('outcome') == 'certified' and event.get('quality') == 'normal'
                and not event.get('anomalies')
                and event.get('fitness_tps') is not None
                and (slot.startswith('seed-') or slot.startswith('eval-'))):
            eligible.append({'fitness_tps': event['fitness_tps'],
                           'ir': event.get('ir'), 'implementation': event.get('implementation'),
                           'logical_slot': slot,
                           'variant': event.get('variant'), 'source_digest': event.get('source_digest')})
    def order(point):
        slot = point['logical_slot']
        prefix, _, number = slot.rpartition('-')
        return (0 if prefix == 'seed' else 1, int(number))
    points = [{**point, 'slot_order': i} for i, point in enumerate(sorted(eligible, key=order))]
    endpoint = min(points, key=lambda p: (-p['fitness_tps'], p['slot_order'])) if points else None
    return {'A': a_used, 'B': b_used, 'a_used': a_used, 'b_used': b_used,
            'unfinished_slots': unfinished, 'endpoint_candidate': endpoint,
            'evolution_points': [{k: p[k] for k in ('slot_order', 'fitness_tps', 'ir')}
                                 for p in points if p['ir'] is not None],
            'points': points}


def select_endpoint(ledger):
    return series_state(ledger)['endpoint_candidate']


def _unit(kind, index, attempt, slots, proposal_sha256=None):
    return {'kind': kind, 'index': index, 'attempt': attempt,
            'proposal_sha256': proposal_sha256,
            'slots': [{'slot': slot, 'index': i, 'attempt': attempt} for slot, i in slots]}


def next_unit(ledger):
    ledger = _ledger(ledger)
    state = series_state(ledger)
    events = ledger.events
    if any(e['kind'] == 'series-end' for e in events):
        return None
    if state['unfinished_slots']:
        return {'kind': 'dead-job', 'index': None, 'attempt': None,
                'proposal_sha256': None, 'slots': state['unfinished_slots']}
    results = [e for e in events if e['kind'] == 'slot-result']
    by_slot = {}
    for event in results:
        by_slot.setdefault(event.get('logical_slot'), []).append(event)
    for slot, attempts in by_slot.items():
        last = max(attempts, key=lambda e: e.get('attempt', 0))
        if last.get('outcome') == 'machine-failure':
            attempt = last.get('attempt', 0) + 1
            if attempt > ledger.header['budgets']['machine_retries']:
                return None
            prefix, _, number = slot.rpartition('-')
            if prefix in ('stock', 'seed', 'eval', 'score', 'ref-stock', 'ref-fixed10'):
                kind = ('job1' if prefix in ('stock', 'seed') else
                        'reference' if prefix.startswith('ref-') else prefix)
                proposal_sha256 = last.get('proposal_sha256')
                if kind == 'eval' and proposal_sha256 is None:
                    proposal_sha256 = next((e.get('proposal_sha256') for e in events
                        if e['kind'] == 'opportunity-end' and e.get('a') == int(number)
                        and e.get('outcome') == 'proposed'), None)
                return _unit(kind, int(number), attempt, [(prefix, int(number))],
                             proposal_sha256)
    arm = ledger.header['arm']
    if arm == 'reference':
        slots = [('ref-stock', i) for i in range(5)] + [('ref-fixed10', i) for i in range(5)]
        remaining = [(slot, i) for slot, i in slots if f'{slot}-{i}' not in by_slot]
        return _unit('reference', 1, 0, remaining) if remaining else None
    job1 = [('stock', 0), ('seed', 0), ('seed', 1)]
    remaining = [(slot, i) for slot, i in job1 if f'{slot}-{i}' not in by_slot]
    if remaining:
        return _unit('job1', 1, 0, remaining)
    ends = [e for e in events if e['kind'] == 'opportunity-end']
    for event in ends:
        if event.get('outcome') == 'proposed' and f"eval-{event['a']}" not in by_slot:
            return _unit('eval', event['a'], 0, [('eval', event['a'])], event.get('proposal_sha256'))
    if state['B'] >= ledger.header['budgets']['B'] or state['A'] >= ledger.header['budgets']['A']:
        if state['endpoint_candidate'] is None:
            return None
        remaining = [('score', i) for i in range(ledger.header['budgets']['n_eval'])
                     if f'score-{i}' not in by_slot]
        return _unit('score', 1, 0, remaining) if remaining else None
    # An open opportunity, outage or role failure resumes at the same a.
    return None
