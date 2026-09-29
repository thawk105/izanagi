from orchestrator.campaign.silo_policy_contrast import (
    ContrastLedger, DEFAULT_BUDGETS, close_series_if_done, next_opportunity,
    next_unit, open_opportunity, select_endpoint, series_state)


def ledger(tmp_path, arm='random-ir'):
    item = ContrastLedger.create(tmp_path / 'series', {
        'version': 'silo-policy-contrast-test-2026-09-29', 'cohort': 'test',
        'arm': arm, 'series': 1, 'form': 'cpp' if arm in ('llm-cpp', 'reference') else 'ir',
        'submit_checkout': str(tmp_path), 'checkout_head': 'abc', 'pin': 'pin',
        'budgets': DEFAULT_BUDGETS})
    item.append('series-start')
    return item


def finish_job1(item):
    for slot, index in [('stock', 0), ('seed', 0), ('seed', 1)]:
        logical = f'{slot}-{index}'
        item.append('slot-start', logical_slot=logical, attempt=0, unit_kind='job1', unit_index=1)
        item.append('slot-result', logical_slot=logical, attempt=0,
                    outcome='certified', quality='normal', fitness_tps=10 + index,
                    ir={'kind': 'PolicyIR'} if slot == 'seed' else None)


def test_a_b_outage_and_retry(tmp_path):
    item = ledger(tmp_path)
    assert [x['slot'] for x in next_unit(item)['slots']] == ['stock', 'seed', 'seed']
    finish_job1(item)
    item.append('opportunity-start', a=1)
    item.append('opportunity-end', a=1, outcome='outage')
    assert series_state(item)['A'] == 0
    item.append('opportunity-end', a=1, outcome='proposed', proposal_sha256='digest')
    assert next_unit(item)['proposal_sha256'] == 'digest'
    item.append('slot-start', logical_slot='eval-1', attempt=0, unit_kind='eval', unit_index=1)
    assert series_state(item)['B'] == 1
    assert next_unit(item)['kind'] == 'dead-job'
    item.append('slot-result', logical_slot='eval-1', attempt=0, outcome='machine-failure')
    assert next_unit(item)['attempt'] == 1
    assert series_state(item)['A'] == 1


def test_endpoint_earliest_tie_and_create_only(tmp_path):
    item = ledger(tmp_path)
    finish_job1(item)
    endpoint = select_endpoint(item)
    assert endpoint['logical_slot'] == 'seed-1'
    item.append('opportunity-end', a=1, outcome='proposed', proposal_sha256='x')
    item.append('slot-start', logical_slot='eval-1', attempt=0, unit_kind='eval', unit_index=1)
    item.append('slot-result', logical_slot='eval-1', attempt=0, outcome='certified',
                quality='normal', fitness_tps=11, ir={'kind': 'PolicyIR'})
    assert select_endpoint(item)['logical_slot'] == 'seed-1'
    assert [p['slot_order'] for p in series_state(item)['evolution_points']] == [0, 1, 2]
    assert ContrastLedger(item.root).events == item.events


def test_close_series_after_score_and_reference_once(tmp_path):
    item = ledger(tmp_path)
    finish_job1(item)
    for a in range(1, 11):
        item.append('slot-start', logical_slot=f'eval-{a}', attempt=0)
        item.append('slot-result', logical_slot=f'eval-{a}', attempt=0,
                    outcome='candidate-failure')
    for i in range(5):
        item.append('slot-start', logical_slot=f'score-{i}', attempt=0)
        item.append('slot-result', logical_slot=f'score-{i}', attempt=0, outcome='certified')
    assert close_series_if_done(item) == 'b-complete'
    assert close_series_if_done(item) is None
    assert next_unit(item) is None
    reference = ledger(tmp_path / 'reference', arm='reference')
    for kind in ('ref-stock', 'ref-fixed10'):
        for i in range(5):
            reference.append('slot-start', logical_slot=f'{kind}-{i}', attempt=0)
            reference.append('slot-result', logical_slot=f'{kind}-{i}', attempt=0,
                             outcome='certified')
    assert close_series_if_done(reference) == 'b-complete'
    retry = ledger(tmp_path / 'retry')
    retry.append('slot-start', logical_slot='stock-0', attempt=0)
    retry.append('slot-result', logical_slot='stock-0', attempt=0, outcome='machine-failure')
    assert close_series_if_done(retry) is None
    for attempt in (1, 2):
        retry.append('slot-start', logical_slot='stock-0', attempt=attempt)
        retry.append('slot-result', logical_slot='stock-0', attempt=attempt,
                     outcome='machine-failure')
    assert close_series_if_done(retry) == 'machine-retry-exhausted'


def test_stock_unestablished_closes_after_job1(tmp_path):
    item = ledger(tmp_path)
    for slot in ('stock-0', 'seed-0', 'seed-1'):
        item.append('slot-start', logical_slot=slot, attempt=0)
        item.append('slot-result', logical_slot=slot, attempt=0,
                    outcome='candidate-failure' if slot == 'stock-0' else 'certified')
    assert close_series_if_done(item) == 'stock-unestablished'
    assert next_unit(item) is None


def test_open_and_next_opportunity_after_outage(tmp_path):
    item = ledger(tmp_path)
    assert open_opportunity(item) is None
    assert next_opportunity(item) == 1
    item.append('opportunity-start', a=1)
    item.append('opportunity-end', a=1, outcome='outage')
    assert open_opportunity(item) == 1
    assert next_opportunity(item) == 1
    item.append('opportunity-end', a=1, outcome='rejected')
    assert open_opportunity(item) is None
    assert next_opportunity(item) == 2
