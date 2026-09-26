"""Harness CLI admission and exact reference routing."""
import contextlib
import json

import pytest

from orchestrator.campaign import p3_s4_loop as L, ident, patchharness
from orchestrator.campaign.genome import Genome
from orchestrator.tests import test_p3_s4_loop as F


def args():
    result = F._b5_args()
    result[result.index('--b5-slot') + 1] = 't2849-harness-v1|fixture'
    return result


def reference(tmp_path, workload='read-heavy'):
    flags = {'BACK_OFF': 0, 'NO_WAIT_LOCKING_IN_VALIDATION': int(workload != 'read-heavy'),
             'NO_WAIT_OF_TICTOC': int(workload == 'read-heavy'), 'WAL': 0}
    path = tmp_path / 'reference.json'
    path.write_text(json.dumps({'protocol': 'silo', 'flags': flags}))
    return path, Genome('silo', flags)


@pytest.mark.parametrize('machine', [True, False])
def test_harness_machine_slot_accepted(tmp_path, monkeypatch, machine):
    _, _, _, sidecar, argv = F._b5_candidate_fixture(tmp_path, monkeypatch)
    argv[argv.index('--b5-slot') + 1] = 't2849-harness-v1|fixture'
    if not machine:
        argv.remove('--machine-generated-proposal')
        argv.append('--allow-coder-derived-build')
    monkeypatch.setattr(L, '_require_condition_gate', lambda *a, **k: None)
    observed = []
    contexts = []
    real_context = L.build_run_context

    def context(**kwargs):
        result = real_context(**kwargs)
        contexts.append((result, kwargs.get('coder_authority')))
        return result

    monkeypatch.setattr(L, 'build_run_context', context)

    class Boundary(Exception):
        pass

    def campaign(cfg, genomes, *a, **kw):
        observed.append(kw['build_context'])
        assert cfg.search_config['b5_slot'].startswith('t2849-harness-v1|')
        assert 'reference_genome' not in cfg.search_config
        raise Boundary

    monkeypatch.setattr(L, 'run_campaign', campaign)
    with pytest.raises(Boundary):
        L.main(argv)
    assert len(observed) == 1
    evaluation_authorities = [authority for ctx, authority in contexts if ctx is observed[0]]
    assert len(evaluation_authorities) == 1
    assert (evaluation_authorities[0] is None) == machine
    assert (sidecar / 'pipeline-submitted.json').exists()


@pytest.mark.parametrize('workload', ['read-heavy', 'balanced', 'write-heavy'])
def test_read_heavy_reference_exact_flags(tmp_path, monkeypatch, workload):
    _, sub, calls = F._stock_cli_fixture(tmp_path, monkeypatch)
    path, genome = reference(tmp_path, workload)
    events = []

    @contextlib.contextmanager
    def applied(*a):
        events.append('patch')
        yield
        events.append('revert')

    def gate(root, received, **kw):
        assert events == ['patch'] and root == str(sub)
        assert received == genome
        events.append('gate')

    monkeypatch.setattr(patchharness, 'applied', applied)
    monkeypatch.setattr(L, '_require_condition_gate', gate)
    assert L.main([*args(), '--stock-control', '--reference-genome', str(path)]) == 1
    assert events == ['patch', 'gate', 'revert']
    cfg, genomes, _, _, kwargs = calls[0]
    assert genomes == [genome]
    assert 'BACKOFF_FIXED' not in genomes[0].flags
    assert cfg.search_config['reference_genome'] == genome.canonical()
    assert kwargs['bench_max_rounds'] == 3


@pytest.mark.parametrize('mode', ['b5', 'no-slot', 'candidate', 'pair'])
def test_reference_rejected_outside_harness(tmp_path, monkeypatch, mode):
    F._stock_cli_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(L, '_require_condition_gate', lambda *a, **k: None)
    argv = args()
    if mode == 'b5':
        argv = F._b5_args()
    if mode == 'no-slot':
        argv = ['--isolate-worktree']
    if mode != 'candidate':
        argv += ['--stock-control']
    if mode in ('candidate', 'pair'):
        argv += ['--run-iteration', 'not-read.json']
    path, _ = reference(tmp_path)
    with pytest.raises(SystemExit) as exc:
        L.main([*argv, '--reference-genome', str(path)])
    assert exc.value.code == 2


@pytest.mark.parametrize('bad', ['bool', 'float', 'extra', 'missing', 'protocol', 'root', 'value'])
def test_reference_schema_exact(tmp_path, bad):
    path, _ = reference(tmp_path)
    doc = json.loads(path.read_text())
    if bad in ('bool', 'float', 'value'):
        doc['flags']['WAL'] = {'bool': False, 'float': 0.0, 'value': 2}[bad]
    elif bad == 'extra':
        doc['flags']['BACKOFF_FIXED'] = -1
    elif bad == 'missing':
        del doc['flags']['WAL']
    elif bad == 'protocol':
        doc['protocol'] = 'mocc'
    else:
        doc['extra'] = 1
    path.write_text(json.dumps(doc))
    with pytest.raises(SystemExit) as exc:
        L.main([*args(), '--stock-control', '--reference-genome', str(path)])
    assert exc.value.code == 2


def test_reference_identity_and_absent_defaults(tmp_path, monkeypatch):
    _, _, calls = F._stock_cli_fixture(tmp_path, monkeypatch)
    # Each CLI config gets its own campaign.lock, just as in production.
    monkeypatch.setattr(L, 'exploration_campaign_layout',
                        lambda cid: F.CampaignLayout(str(tmp_path / cid)))
    monkeypatch.setattr(L, '_require_condition_gate', lambda *a, **k: None)
    received = []
    real = L._run_stock_control_resolved

    def stock(*a, **kw):
        received.append(kw)
        return real(*a, **kw)

    monkeypatch.setattr(L, '_run_stock_control_resolved', stock)
    assert L.main(['--stock-control', '--isolate-worktree']) == 1
    assert ident.canonical_preimage(calls[0][0]) == F._DEFAULT_PREIMAGE_BEFORE_PAIR
    assert 'reference_genome' not in received[0]
    assert calls[0][1] == [Genome('silo', {**L._BASE, 'BACK_OFF': 1, 'BACKOFF_FIXED': -1})]
    for workload in ('read-heavy', 'balanced'):
        path, _ = reference(tmp_path, workload)
        assert L.main([*args(), '--stock-control', '--reference-genome', str(path)]) == 1
    assert len({str(ident.campaign_id(call[0])) for call in calls}) == 3


def test_mocc_exact_genomes_and_default_silo_identity():
    assert L.default_cfg().search_config == L.default_cfg(protocol='silo').search_config
    assert L.backoff_genome('silo', -1) == Genome('silo', {**L._BASE, 'BACK_OFF': 1,
                                                         'BACKOFF_FIXED': -1})
    assert L.backoff_genome('silo', 20) == Genome('silo', {**L._BASE, 'BACK_OFF': 1,
                                                         'BACKOFF_FIXED': 20})
    for value in (-1, 20):
        assert L.backoff_genome('mocc', value) == Genome('mocc', {
            'BACK_OFF': 1, 'KEY_SORT': 0, 'TEMPERATURE_RESET_OPT': 1,
            'BACKOFF_FIXED': value})
    assert L.default_cfg(protocol='mocc').search_config['scale'] == 'mocc'
    assert L.default_cfg(protocol='mocc').search_config['protocol'] == 'mocc'


def test_condition_gate_requests_follow_genome_protocol(monkeypatch):
    class StopAfterRequest(Exception):
        pass

    observed = []
    monkeypatch.setattr(L.buildcache, 'compilers_for_current_site', lambda: ('cc', 'cxx'))
    monkeypatch.setattr(L.condition_meaning_gate, 'capture_define_inputs',
                        lambda *args, **kwargs: object())

    def observe_supply(captured, *, request, **kwargs):
        observed.append((request.owner_tu, request.target))
        raise StopAfterRequest

    monkeypatch.setattr(L.condition_meaning_gate,
                        'evaluate_define_supply_effectuation', observe_supply)
    for protocol, value, expected in (
        ('mocc', -1, ('cc/mocc/transaction.cc', 'ycsb_mocc.exe')),
        ('mocc', 5, ('cc/mocc/transaction.cc', 'ycsb_mocc.exe')),
        ('silo', 5, ('cc/silo/transaction.cc', 'ycsb_silo.exe')),
    ):
        with pytest.raises(StopAfterRequest):
            L._require_condition_gate('/source', L.backoff_genome(protocol, value),
                                      stock_root='/stock' if value == -1 else None)
        assert observed[-1] == expected


def test_mocc_slot_start_sidecar_genome(tmp_path, monkeypatch):
    _, _, _, sidecar, argv = F._b5_candidate_fixture(tmp_path, monkeypatch)
    argv[argv.index('--b5-slot') + 1] = 't2849-harness-v1|fixture'
    monkeypatch.setattr(L, '_require_condition_gate', lambda *a, **k: None)
    class Boundary(Exception):
        pass
    def campaign(cfg, genomes, *args, **kwargs):
        assert genomes[0] == L.backoff_genome('mocc', 20)
        assert json.loads((sidecar / 'slot-start.json').read_text())['genome'] == genomes[0].canonical()
        raise Boundary
    monkeypatch.setattr(L, 'run_campaign', campaign)
    with pytest.raises(Boundary):
        L.main([*argv, '--protocol', 'mocc'])


def test_mocc_reference_genome_rejected(tmp_path):
    path, _ = reference(tmp_path)
    with pytest.raises(SystemExit) as exc:
        L.main([*args(), '--stock-control', '--protocol', 'mocc', '--reference-genome', str(path)])
    assert exc.value.code == 2


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
