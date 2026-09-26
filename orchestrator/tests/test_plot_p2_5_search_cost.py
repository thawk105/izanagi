"""Figure 1b values, reconciliation, layout, and hash closure."""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.plotting import plot_p2_5_search_cost as fig1


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
    assert 'p=2.5×10⁻⁴' in prov['artist_series']['write-heavy']['annotations']
    assert '8/12 mis-converged' in prov['artist_series']['write-heavy']['annotations']


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


def test_landed_bundle():
    prefix = fig1.ROOT/'docs/paper-story/figures/fig1b_phase2_negative'
    provenance = prefix.with_suffix('.provenance.json')
    if not provenance.exists():
        pytest.skip('parent has not landed the bundle yet')
    prov = json.loads(provenance.read_text())
    assert fig1.validate_repo_closure(prov)
    readme = (prefix.parent/'README.md').read_text()
    assert prov['caption'] == fig1.caption()
    assert prov['caption'] in readme
