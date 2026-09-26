#!/usr/bin/env python3
"""Recreate Phase 2 search cost from frozen guided trials and historical P2-2 records."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.text import Text
from orchestrator.campaign import replay, search_baselines as sb, wal
from orchestrator.campaign.artifact_admission import CampaignReadPurpose
from orchestrator.campaign.genome import SILO_SPACE

TAGS = ('read-heavy', 'balanced', 'write-heavy')
GENERATOR = 'tools/plotting/plot_p2_5_search_cost.py'
GREEDY_KEYS = ('n', 'mean', 'median', 'min', 'max', 'iqr_lo', 'iqr_hi')


class FigureDataError(ValueError):
    """Figure input or proof chain failed."""


class FigureLayoutError(FigureDataError):
    """Text overlaps or escapes the figure."""


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _file(path):
    path = Path(path).resolve()
    try:
        name = str(path.relative_to(ROOT))
    except ValueError:
        name = str(path)
    return {'path': name, 'sha256': _sha256(path)}


def landscape_from_records(records):
    """Use only committed genomes and recorded certified flags; no new verdict."""
    genome_of, bench_of, cert_of, committed = {}, {}, {}, set()
    for r in records:
        if r.stage == 'build_start':
            genome_of[r.variant] = r.payload.get('genome', genome_of.get(r.variant, ''))
        elif r.stage == 'bench_done':
            bench_of[r.variant] = r.payload
        elif r.stage == 'verify_done':
            cert_of[r.variant] = bool(r.payload.get('certified'))
        elif r.stage == 'commit':
            committed.add(r.variant)
    land = {}
    for variant in committed:
        g, p = genome_of.get(variant), bench_of.get(variant)
        if not g or p is None:
            continue
        land[g] = replay.GenomeResult(
            genome=g, flags=replay.parse_flags(g), fitness_tps=p.get('median_tps'),
            tps=list(p.get('tps') or []),
            leading_indicators=dict(p.get('leading_indicators') or {}),
            certified=cert_of.get(variant, False), verification_evidence=None)
    if set(land) != {g.canonical() for g in SILO_SPACE.enumerate()}:
        raise FigureDataError('landscape space coverage mismatch')
    if not all(x.certified for x in land.values()):
        raise FigureDataError('landscape recorded certified mismatch')
    return land


def _equal(a, b):
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    return a == b


def _reconcile(tag, row, calc, summary):
    checked = []
    for key in ('k', 'n', 'tied_set', 'random_E', 'oracle_E', 'greedy_p_lt', 'guided_n'):
        if not _equal(calc[key], row[key]):
            raise FigureDataError(f'{tag}: {key} mismatch')
        checked.append(key)
    for group in ('greedy', 'guided'):
        for key in GREEDY_KEYS:
            if not _equal(calc[group][key], row[group][key]):
                raise FigureDataError(f'{tag}: {group}.{key} mismatch')
            checked.append(f'{group}.{key}')
    if calc['guided_n'] != len(row['guided_costs']):
        raise FigureDataError(f'{tag}: guided_n length mismatch')
    if row['informative']:
        frozen = summary['recalibration_2026_07_02']['results'][tag.replace('-', '_')]['guided_vs_greedy_A']
        if round(calc['A'], 4) != frozen:
            raise FigureDataError(f'{tag}: guided_vs_greedy_A mismatch')
        checked.append('guided_vs_greedy_A')
    if tag == 'write-heavy':
        frozen = summary['correction_2026_07_03']['value']['write_heavy_guided_vs_greedy_exact_p']
        if not math.isclose(calc['p'], frozen, rel_tol=1e-12):
            raise FigureDataError(f'{tag}: exact p mismatch')
        checked.append('write_heavy_guided_vs_greedy_exact_p')
    return checked


def load_data(summary_path=ROOT/'output/campaigns/p2-5-summary.json', output_root=ROOT/'output'):
    """Recompute all plotted values before any output is written."""
    try:
        summary = json.loads(Path(summary_path).read_text(encoding='utf-8'))
        rows = {r['workload']: r for r in summary['rows']}
        data = {'summary': _file(summary_path), 'workloads': {}}
        for tag in TAGS:
            row = rows[tag]
            view = replay.discover_p2_2_dir(
                tag, str(output_root), purpose=CampaignReadPurpose.HISTORICAL_RAW)
            for _, frame, _ in wal.iter_lines(view.wal_file):
                wal.parse_line(frame)
            land = landscape_from_records(view.records)
            tied = replay.winner_tied_set(land)
            n, k = len(land), len(tied)
            dist = sb.random_reach_distribution(n, k)
            costs = sb.greedy_reach(land, tied, 500, 0)
            guided_costs = row['guided_costs']
            greedy, guided = sb._summ(costs), sb._summ(guided_costs)
            greedy['n'], guided['n'] = len(costs), len(guided_costs)
            calc = {
                'n': n, 'k': k,
                'tied_set': sorted(replay.genome_label(land[x].flags) for x in tied),
                'random_E': sb.expectation(dist), 'oracle_E': sb.oracle_ceiling(n, k),
                'greedy': greedy, 'greedy_p_lt': sb.prob_superiority(costs, dist)['p_lt'],
                'greedy_counts': dict(sorted(Counter(costs).items())),
                'guided': guided, 'guided_n': len(guided_costs),
                'guided_costs': guided_costs, 'guided_failures': row['guided_failures'],
                'informative': row['informative'],
            }
            if row['informative']:
                calc['A'] = sb.prob_superiority_two_sample(guided_costs, costs)
            if tag == 'write-heavy':
                calc['p'] = sb.exact_perm_pvalue_A(guided_costs, costs, 'less')['p']
            calc['checked_keys'] = _reconcile(tag, row, calc, summary)
            epoch = view.campaign_verifier_epoch
            calc['campaign'] = {
                'id': Path(view.root).name, 'wal': _file(view.wal_file),
                'lock': _file(view.lock_file),
                'campaign_verifier_epoch': {
                    'campaign_verifier_epoch': epoch.campaign_verifier_epoch,
                    'state': epoch.state, 'reason_code': epoch.reason_code,
                    'identity_scope': epoch.identity_scope,
                    'excluded_scope': epoch.excluded_scope,
                    'verifier_assessment_basis': view.verifier_assessment_basis,
                },
                'measurement_conditions': {
                    'run_cmd': sorted({r.payload['run_cmd'] for r in view.records
                                       if isinstance(r.payload.get('run_cmd'), str)}),
                    'ccbench_commit': json.loads(Path(view.lock_file).read_text())['ccbench_commit'],
                },
            }
            data['workloads'][tag] = calc
        return data
    except FigureDataError:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise FigureDataError(f'invalid input: {exc}') from exc


def caption():
    return ('旧 linux-baremetal 環境の Phase 2 探索コスト。P2-2 の silo 8 構成について、'
            'LLM-guided は中立 critic の 30 試行（read-heavy 6、balanced 12、write-heavy 12）の凍結値を示す。'
            '原試行 WAL は削除済みである。未到達は事前登録どおり予算上限 8 として算入した。'
            'greedy は P2-2 WAL の決定論的再生 500 seed、random は解析期待値、oracle は初手ランダム制約下の天井。'
            'A = P(誘導<貪欲)+0.5·P(=)、p は厳密 permutation 検定（片側）。'
            'P2-2 campaign は verifier epoch E0 の記録をそのまま使用し、現行 verifier では再検証していない。'
            'read-heavy は k=4 で到達判定が情報を持たないため、A の注記を付けない。')


def _contains(outer, inner):
    return inner.x0 >= outer.x0-1 and inner.y0 >= outer.y0-1 and inner.x1 <= outer.x1+1 and inner.y1 <= outer.y1+1


def _intersection(a, b):
    return max(0, min(a.x1, b.x1)-max(a.x0, b.x0))*max(0, min(a.y1, b.y1)-max(a.y0, b.y0))


def check_figure_layout(fig, axes):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    if len(axes) != 3 or set(axes) != set(fig.axes):
        raise FigureLayoutError('production layout requires three axes')
    boxes = []
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not _contains(fig.bbox, box):
            raise FigureLayoutError(f'text leaves figure: {artist.get_text()!r}')
        if artist.get_gid() == 'direct-label' and (artist.axes is None or not _contains(artist.axes.bbox, box)):
            raise FigureLayoutError(f'text leaves axis: {artist.get_text()!r}')
        boxes.append((artist, box))
    for i, (a, box) in enumerate(boxes):
        for b, other in boxes[i+1:]:
            if _intersection(box, other) > 1:
                raise FigureLayoutError(f'text bbox overlap: {a.get_text()!r} / {b.get_text()!r}')
    for ax in axes:
        if not _contains(fig.bbox, ax.get_tightbbox(renderer)):
            raise FigureLayoutError('axis decoration leaves figure')


def make_figure(data):
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.8), sharey=True)
    fig.suptitle('Phase 2 negative result: LLM guidance does not beat a mechanical gradient — and is harmful under deceptive structure', fontsize=12)
    artists = {}
    for ax, tag in zip(axes, TAGS):
        d = data['workloads'][tag]
        costs, g = d['guided_costs'], d['greedy']
        xs = [(i-(len(costs)-1)/2)*.012 for i in range(len(costs))]
        dots = ax.scatter(xs, costs, s=32, color='#cd414c', edgecolor='white', linewidth=.4, zorder=4)
        median = ax.hlines(d['guided']['median'], -.25, .25, color='#c1121f', lw=3, zorder=5)
        whisker = ax.errorbar(1, g['mean'], yerr=[[g['mean']-g['iqr_lo']], [g['iqr_hi']-g['mean']]],
                              fmt='s', markersize=8, capsize=4, color='#4a4e69', lw=1.6, zorder=5)
        random = ax.axhline(d['random_E'], color='#9aa0a6', linestyle=':', lw=1.5)
        oracle = ax.axhline(d['oracle_E'], color='#2a9d8f', linestyle='--', lw=1.5)
        annotations = []
        if d['informative']:
            color = '#c1121f' if tag == 'write-heavy' else '#333333'
            note = ax.text(.98, .97, f"A={d['A']:.2f}", transform=ax.transAxes,
                           ha='right', va='top', color=color, fontsize=9)
            note.set_gid('direct-label'); annotations.append(note)
        if 'p' in d:
            note = ax.text(.98, .92, 'p=2.5×10⁻⁴', transform=ax.transAxes,
                           ha='right', va='top', color='#c1121f', fontsize=9)
            note.set_gid('direct-label'); annotations.append(note)
        if d['guided_failures']:
            note = ax.text(.32, 6.7, f"{d['guided_failures']}/{d['guided_n']} mis-converged",
                           ha='left', color='#c1121f', fontsize=8)
            note.set_gid('direct-label'); annotations.append(note)
        if tag == 'write-heavy':
            for label, y, color in (('random', d['random_E'], '#9aa0a6'), ('oracle', d['oracle_E'], '#2a9d8f')):
                note = ax.text(1.69, y+.04, label, color=color, fontsize=8, ha='right', va='bottom')
                note.set_gid('direct-label'); annotations.append(note)
        ax.set(title=tag, xlim=(-.6, 1.7), ylim=(.45, 8.55), xticks=(0, 1),
               xticklabels=('LLM-guided', 'greedy\n(no LLM)'), yticks=range(1, 9))
        artists[tag] = {
            'points': [list(map(float, xy)) for xy in dots.get_offsets()],
            'median_bar': float(median.get_segments()[0][0][1]),
            'greedy_square': float(whisker.lines[0].get_ydata()[0]),
            'greedy_whisker': [float(xy[1]) for xy in whisker.lines[2][0].get_segments()[0]],
            'random_line': float(random.get_ydata()[0]),
            'oracle_line': float(oracle.get_ydata()[0]),
            'annotations': [a.get_text() for a in annotations],
        }
    axes[0].set_ylabel('configs evaluated to reach best\n(lower = faster)')
    fig.subplots_adjust(left=.075, right=.98, bottom=.13, top=.78, wspace=.075)
    return fig, axes, artists


def validate_repo_closure(provenance, repo_root=ROOT):
    refs = [provenance['generator'], provenance['summary']]
    for d in provenance['workloads'].values():
        refs.extend((d['campaign']['wal'], d['campaign']['lock']))
    refs.extend(provenance['outputs'].values())
    for item in refs:
        path = Path(item['path'])
        if not path.is_absolute():
            path = Path(repo_root)/path
        if _sha256(path) != item['sha256']:
            raise FigureDataError(f"closure sha256 mismatch: {item['path']}")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out_prefix', type=Path)
    parser.add_argument('--summary', type=Path, default=ROOT/'output/campaigns/p2-5-summary.json')
    parser.add_argument('--output-root', type=Path, default=ROOT/'output')
    args = parser.parse_args(argv)
    data = load_data(args.summary, args.output_root)
    fig, axes, artists = make_figure(data)
    try:
        check_figure_layout(fig, axes)
        prefix = args.out_prefix
        prefix.parent.mkdir(parents=True, exist_ok=True)
        png, pdf = prefix.with_suffix('.png'), prefix.with_suffix('.pdf')
        fig.savefig(png, dpi=180)
        fig.savefig(pdf)
        provenance = {
            'schema': 'izanagi-p2-5-search-cost-figure-provenance/v1',
            'generator': _file(ROOT/GENERATOR), 'summary': data['summary'],
            'workloads': data['workloads'], 'artist_series': artists,
            'caption': caption(), 'outputs': {'png': _file(png), 'pdf': _file(pdf)},
            'argv': list(sys.argv[1:] if argv is None else argv),
            'generated_utc': datetime.now(timezone.utc).isoformat(),
            'versions': {'python': platform.python_version(), 'matplotlib': matplotlib.__version__, 'numpy': np.__version__},
        }
        prefix.with_suffix('.provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    finally:
        plt.close(fig)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except FigureDataError as exc:
        print(f'FigureDataError: {exc}', file=sys.stderr)
        sys.exit(1)
