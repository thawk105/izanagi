"""Figure 1b values, reconciliation, layout, and hash closure."""
from __future__ import annotations

import json
import inspect
import math
from pathlib import Path
import sys
import tempfile
import time
import traceback
from types import SimpleNamespace

import pytest

from tools.plotting import plot_p2_5_search_cost as fig1
from orchestrator.campaign import replay
from orchestrator.campaign.artifact_admission import CampaignReadPurpose


def test_real_data():
    data = fig1.load_data()
    rows = data['workloads']
    assert {t: rows[t]['k'] for t in fig1.TAGS} == {
        'read-heavy': 4, 'balanced': 1, 'write-heavy': 1}
    assert rows['write-heavy']['greedy_counts'] == {1: 62, 2: 66, 3: 67, 4: 35, 5: 31, 6: 182, 7: 57}
    assert round(rows['balanced']['A'], 4) == .5813
    assert round(rows['write-heavy']['A'], 4) == .2304
    assert math.isclose(rows['write-heavy']['p'], .0002521080185096, rel_tol=1e-12)
    assert all(rows[t]['campaign']['campaign_verifier_epoch']['campaign_verifier_epoch'] == 'E0'
               for t in fig1.TAGS)
    assert {t: rows[t]['campaign']['measurement_conditions']['read_ratio'] for t in fig1.TAGS} == {
        'read-heavy': '95', 'balanced': '50', 'write-heavy': '5'}


def test_p_format():
    assert fig1.format_p(.0002521080185096) == 'p=2.5×10⁻⁴'
    assert fig1.format_p(.00123) == 'p=1.2×10⁻³'


def test_measurement_conditions_consistency():
    view = replay.discover_p2_2_dir('balanced', str(fig1.ROOT/'output'),
                                    purpose=CampaignReadPurpose.HISTORICAL_RAW)
    records = list(view.records)
    expected = fig1._measurement_conditions(records, view.lock_file)
    assert expected['threads'] == '48' and expected['repetitions'] == 5
    bench = next(i for i, r in enumerate(records) if r.stage == 'bench_done')
    original = records[bench]
    for replacement in (
        SimpleNamespace(stage='bench_done', env_tag=original.env_tag,
                        payload={**original.payload, 'run_cmd': original.payload['run_cmd'].replace('-thread_num=48', '-thread_num=47')}),
        SimpleNamespace(stage='bench_done', env_tag='', payload=original.payload),
        SimpleNamespace(stage='bench_done', env_tag=original.env_tag,
                        payload={**original.payload, 'tps': original.payload['tps'][:-1]}),
    ):
        changed = records.copy()
        changed[bench] = replacement
        with pytest.raises(fig1.FigureDataError, match='measurement'):
            fig1._measurement_conditions(changed, view.lock_file)


def test_measurement_conditions_across_campaigns():
    rows = fig1.load_data()['workloads']
    changed = {tag: {**row, 'campaign': {**row['campaign'],
               'measurement_conditions': dict(row['campaign']['measurement_conditions'])}}
               for tag, row in rows.items()}
    conditions = changed['balanced']['campaign']['measurement_conditions']
    conditions['threads'] = str(int(conditions['threads']) + 1)
    with pytest.raises(fig1.FigureDataError, match='measurement conditions differ across campaigns'):
        fig1._common_measurement_conditions(changed)


@pytest.mark.parametrize('case', ('greedy', 'A', 'p', 'random'))
def test_reconciliation(tmp_path, case):
    summary = json.loads((fig1.ROOT/'output/campaigns/p2-5-summary.json').read_text())
    row = next(r for r in summary['rows'] if r['workload'] == 'write-heavy')
    if case == 'greedy':
        row['greedy']['mean'] += .1
    elif case == 'A':
        summary['recalibration_2026_07_02']['results']['write_heavy']['guided_vs_greedy_A'] += .1
    elif case == 'p':
        summary['correction_2026_07_03']['value']['write_heavy_guided_vs_greedy_exact_p'] += .1
    else:
        row['random_E'] += .1
    source = tmp_path/'summary.json'
    source.write_text(json.dumps(summary))
    prefix = tmp_path/'figure'
    with pytest.raises(fig1.FigureDataError, match='mismatch'):
        fig1.main([str(prefix), '--summary', str(source)])
    assert list(tmp_path.iterdir()) == [source]


def _records(certified=True, count=8):
    records = []
    for i, genome in enumerate(list(fig1.SILO_SPACE.enumerate())[:count]):
        variant = f'v{i}'
        for stage, payload in (
            ('build_start', {'genome': genome.canonical()}),
            ('bench_done', {'median_tps': 100+i, 'tps': [100+i]*5, 'leading_indicators': {}}),
            ('verify_done', {'certified': certified or i != 0}),
            ('commit', {}),
        ):
            records.append(SimpleNamespace(stage=stage, variant=variant, payload=payload))
    return records


def test_landscape():
    with pytest.raises(fig1.FigureDataError, match='certified'):
        fig1.landscape_from_records(_records(False))
    with pytest.raises(fig1.FigureDataError, match='coverage'):
        fig1.landscape_from_records(_records(count=7))
    assert len(fig1.landscape_from_records(_records())) == 8


def test_end_to_end(tmp_path):
    prefix = tmp_path/'fig1b'
    assert fig1.main([str(prefix)]) == 0
    paths = [prefix.with_suffix(s) for s in ('.png', '.pdf', '.provenance.json')]
    assert all(p.exists() and p.stat().st_size for p in paths)
    prov = json.loads(paths[-1].read_text())
    assert fig1.validate_repo_closure(prov)
    for tag, d in prov['workloads'].items():
        a = prov['artist_series'][tag]
        assert len(a['points']) == d['guided_n']
        assert [v[1] for v in a['points']] == d['guided_costs']
        assert a['median_bar'] == d['guided']['median']
        assert a['greedy_square'] == d['greedy']['mean']
        assert a['greedy_whisker'] == [d['greedy']['iqr_lo'], d['greedy']['iqr_hi']]
        assert a['random_line'] == d['random_E']
        assert a['oracle_line'] == d['oracle_E']
    assert prov['artist_series']['balanced']['annotations'] == ['A=0.58']
    assert 'A=0.23' in prov['artist_series']['write-heavy']['annotations']
    assert fig1.format_p(prov['workloads']['write-heavy']['p']) in prov['artist_series']['write-heavy']['annotations']
    assert '8/12 mis-converged' in prov['artist_series']['write-heavy']['annotations']
    assert '48 スレッド' in prov['caption']
    assert prov['caption'] == fig1.caption(prov)


def test_layout():
    import matplotlib.pyplot as plt
    figure, axes, _ = fig1.make_figure(fig1.load_data())
    try:
        fig1.check_figure_layout(figure, axes)
        existing = next(t for t in axes[2].texts if t.get_text() == 'A=0.23')
        axes[2].text(*existing.get_position(), 'overlap', transform=existing.get_transform(),
                     ha='right', va='top')
        with pytest.raises(fig1.FigureLayoutError, match='overlap'):
            fig1.check_figure_layout(figure, axes)
    finally:
        plt.close(figure)


def test_closure(tmp_path):
    prefix = tmp_path/'fig1b'
    assert fig1.main([str(prefix)]) == 0
    prov = json.loads(prefix.with_suffix('.provenance.json').read_text())
    png = prefix.with_suffix('.png')
    png.write_bytes(png.read_bytes()+b'x')
    with pytest.raises(fig1.FigureDataError, match='sha256 mismatch'):
        fig1.validate_repo_closure(prov)


def test_closure_generator_history(tmp_path):
    prefix = tmp_path/'fig1b'
    assert fig1.main([str(prefix)]) == 0
    prov = json.loads(prefix.with_suffix('.provenance.json').read_text())
    prov['generator']['sha256'] = '0'*64
    assert fig1.validate_repo_closure(prov)


def test_landed_bundle():
    prefix = fig1.ROOT/'docs/paper-story/figures/fig1b_phase2_negative'
    provenance = prefix.with_suffix('.provenance.json')
    if not provenance.exists():
        pytest.skip('parent has not landed the bundle yet')
    prov = json.loads(provenance.read_text())
    assert fig1.validate_repo_closure(prov)
    readme = (prefix.parent/'README.md').read_text()
    assert prov['caption'] in readme


def _run():
    started = time.monotonic()
    passed = failed = skipped = errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith('test_') and callable(value)]
    for test in tests:
        cases = ('greedy', 'A', 'p', 'random') if test.__name__ == 'test_reconciliation' else (None,)
        for case in cases:
            node = f"{Path(__file__).name}::{test.__name__}" + (f'[{case}]' if case else '')
            try:
                with tempfile.TemporaryDirectory(prefix='fig1-search-cost-test-') as directory:
                    params = inspect.signature(test).parameters
                    kwargs = {'tmp_path': Path(directory)} if 'tmp_path' in params else {}
                    if case is not None:
                        kwargs['case'] = case
                    test(**kwargs)
                print(f'PASS {node}')
                passed += 1
            except pytest.skip.Exception as exc:
                print(f'SKIP {node}: {exc}')
                skipped += 1
            except AssertionError as exc:
                print(f'FAIL {node}: {exc}')
                traceback.print_exc()
                failed += 1
            except Exception as exc:
                print(f'ERROR {node}: {type(exc).__name__}: {exc}')
                traceback.print_exc()
                errors += 1
    print(f'{passed} passed, {failed} failed, {skipped} skipped, {errors} errors')
    print(f'wall seconds: {time.monotonic()-started:.3f}')
    fig1.plt.close('all')
    return 1 if failed or errors else 0


if __name__ == '__main__':
    sys.exit(_run())
