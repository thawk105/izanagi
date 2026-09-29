
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
import json
from types import SimpleNamespace

from tools.pegasus import silo_policy_contrast_launch as launch
from orchestrator.campaign.silo_policy_contrast import ContrastLedger, DEFAULT_BUDGETS


def _ledger(tmp_path):
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    item = ContrastLedger.create(tmp_path / 'ledger', {
        'version': 'silo-policy-contrast-test-2026-09-29', 'cohort': 'test',
        'arm': 'random-ir', 'series': 1, 'form': 'ir',
        'submit_checkout': str(checkout), 'checkout_head': 'abc',
        'pin': 'pin', 'budgets': DEFAULT_BUDGETS})
    item.append('series-start')
    return item


def test_submit_dry_run_env_and_hold_after(tmp_path, monkeypatch, capsys):
    item = _ledger(tmp_path)
    monkeypatch.setattr(launch, '_head', lambda checkout: 'abc')
    args = SimpleNamespace(ledger=str(item.root), evidence_root=str(tmp_path / 'evidence'),
        archive_root=str(tmp_path / 'archive'), walltime='00:45:00',
        after='123', hold=True, submit=False)
    launch.submit(args)
    result = json.loads(capsys.readouterr().out)
    argv = result['qsub_argv']
    assert argv[:4] == ['qsub', '-h', '--after', '123']
    assert 'IZANAGI_S4_POLICY_MODE=contrast' in argv[5]
    assert 'IZANAGI_S4_POLICY_UNIT_PATH=' in argv[5]
    assert 'IZANAGI_S4_POLICY_FORM=ir' in argv[5]
    assert 'IZANAGI_TRACE_ARCHIVE_ROOT=' in argv[5]
    assert Path(result['unit']['ledger_root']).is_absolute()
    assert not (tmp_path / 'evidence').exists()


def test_generate_reject_records_a(tmp_path, monkeypatch, capsys):
    item = _ledger(tmp_path)
    for slot, i in [('stock', 0), ('seed', 0), ('seed', 1)]:
        item.append('slot-start', logical_slot=f'{slot}-{i}', attempt=0)
        item.append('slot-result', logical_slot=f'{slot}-{i}', attempt=0, outcome='candidate-failure')
    calls = []
    def fake_driver(ledger, proposal, flag, out):
        calls.append(flag)
        if flag == '--preview-diff':
            launch._publish(out, {'passed': False})
        else:
            launch._publish(out, {'outcome': 'rejected'})
        return SimpleNamespace(returncode=1 if flag == '--preview-diff' else 0, stderr='')
    monkeypatch.setattr(launch, '_driver', fake_driver)
    launch.generate(SimpleNamespace(ledger=str(item.root)))
    assert calls == ['--preview-diff', '--record-reject']
    assert ContrastLedger(item.root).events[-1]['outcome'] == 'rejected'
    assert json.loads(capsys.readouterr().out)['a'] == 1


def test_submit_score_fixes_flat_endpoint_only_on_submit(tmp_path, monkeypatch, capsys):
    item = _ledger(tmp_path)
    for slot in ('stock-0', 'seed-0', 'seed-1'):
        item.append('slot-start', logical_slot=slot, attempt=0)
        item.append('slot-result', logical_slot=slot, attempt=0, outcome='certified',
                    quality='normal', fitness_tps=12, variant='seed-v', source_digest='seed-d')
    for a in range(1, 11):
        item.append('slot-start', logical_slot=f'eval-{a}', attempt=0)
        item.append('slot-result', logical_slot=f'eval-{a}', attempt=0,
                    outcome='candidate-failure')
    monkeypatch.setattr(launch, '_head', lambda checkout: 'abc')
    monkeypatch.setattr(launch, '_run', lambda argv, **kwargs:
                        SimpleNamespace(returncode=0, stdout='123\n', stderr=''))
    args = SimpleNamespace(ledger=str(item.root), evidence_root=str(tmp_path / 'evidence'),
        archive_root=str(tmp_path / 'archive'), walltime='00:25:00',
        after=None, hold=False, submit=False)
    launch.submit(args)
    capsys.readouterr()
    assert not any(e['kind'] == 'endpoint-fixed' for e in ContrastLedger(item.root).events)
    args.submit = True
    launch.submit(args)
    fixed = [e for e in ContrastLedger(item.root).events if e['kind'] == 'endpoint-fixed']
    assert len(fixed) == 1
    assert {key: fixed[0][key] for key in ('logical_slot', 'variant', 'source_digest', 'fitness_tps')} == {
        'logical_slot': 'seed-0', 'variant': 'seed-v', 'source_digest': 'seed-d', 'fitness_tps': 12}
    assert 'endpoint' not in fixed[0]


def test_generate_reject_preserves_preview_subtype(tmp_path, monkeypatch):
    item = _ledger(tmp_path)
    for slot in ('stock-0', 'seed-0', 'seed-1'):
        item.append('slot-start', logical_slot=slot, attempt=0)
        item.append('slot-result', logical_slot=slot, attempt=0, outcome='certified')
    def fake_driver(ledger, proposal, flag, out):
        launch._publish(out, {'passed': False, 'subtype': 'typed-ir', 'rule_id': 'rule-7'}
                        if flag == '--preview-diff' else {'outcome': 'rejected'})
        return SimpleNamespace(returncode=1 if flag == '--preview-diff' else 0, stderr='')
    monkeypatch.setattr(launch, '_driver', fake_driver)
    launch.generate(SimpleNamespace(ledger=str(item.root)))
    end = ContrastLedger(item.root).events[-1]
    assert (end['reject_subtype'], end['reject_rule_id']) == ('typed-ir', 'rule-7')


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
