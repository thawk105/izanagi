#!/usr/bin/env python3
"""Recompute interval-GC figures and input-bound tables from the 40 raw parts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics

ARMS = ('stock', 'min', 'gen')
COLORS = {'stock': '#555555', 'min': '#087e8b', 'gen': '#ba5d26'}
SITES = (('long_ro', 0, 0), ('online_ro', 0, 1),
         ('long_update', 1, 0), ('online_update', 1, 1))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def area(a, b):
    return max(0, min(a.x1, b.x1)-max(a.x0, b.x0))*max(0, min(a.y1, b.y1)-max(a.y0, b.y0))


def contains(a, b):
    return b.x0 >= a.x0-1 and b.y0 >= a.y0-1 and b.x1 <= a.x1+1 and b.y1 <= a.y1+1


def check_figure_layout(fig, axes):
    """The preceding figure's renderer-backed fail-closed layout check."""
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for item in fig.findobj(Text):
        if not item.get_visible() or not item.get_text().strip():
            continue
        box = item.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not contains(fig.bbox, box):
            raise ValueError('text outside figure: ' + item.get_text())
        if item.axes is not None and any(
                other is not item.axes
                and area(item.axes.bbox, other.bbox) < .9 * item.axes.bbox.width * item.axes.bbox.height
                and area(box, other.bbox) > 1 for other in fig.axes):
            raise ValueError('text enters neighboring panel: ' + item.get_text())
        boxes.append((item, box))
    for i, (left, a) in enumerate(boxes):
        for right, b in boxes[i+1:]:
            if area(a, b) > 1:
                raise ValueError('text overlap: ' + left.get_text() + ' / ' + right.get_text())
    for ax in axes:
        if not contains(fig.bbox, ax.get_tightbbox(renderer)):
            raise ValueError('axis decoration outside figure')


def short(cell):
    return cell.replace('rr50-', '').replace('rr95-', '').replace('-gc', '/').replace('wait10-two', 'wait10×2')


def verification_text(verification):
    status = verification['status']
    positive = verification['positive_count']
    auxiliary = verification['auxiliary_detection_count']
    disqualified = len(verification['disqualified'])
    if status == 'passed':
        outcome = 'Normal arms passed; preregistered S8 positive met'
    elif status == 'normal_arms_passed_s8_positive_unmet':
        outcome = 'Normal arms passed; preregistered S8 positive unmet'
    elif status == 'failed':
        outcome = 'Verification failed'
    else:
        raise ValueError('unknown verification status: ' + str(status))
    return (f'{outcome} (positive {positive}, auxiliary detections {auxiliary}, '
            f'disqualified {disqualified}).')


def collect(aggregate, raw):
    from orchestrator.campaign.vhash_interval_gc import aggregate as aggregate_jobs
    recomputed = aggregate_jobs(raw, require_parts=True)
    if recomputed != aggregate:
        raise ValueError('aggregate does not match raw recomputation')
    by_key = {}
    hosts = {}
    for rec in raw:
        part = rec['part_id']
        hosts.setdefault(part, set()).add(rec['host'])
        if rec.get('build_kind') in ('perf', 'count') and rec.get('cell') in aggregate['cells']:
            key = (rec['cell'], rec['arm'], rec['build_kind'], rec['rep'])
            if key in by_key:
                raise ValueError('duplicate run ' + str(key))
            by_key[key] = rec
    tables = {}
    for cell, group in aggregate['cells'].items():
        tables[cell] = {}
        for arm in ARMS:
            reps = [by_key[(cell, arm, 'perf', i)]['throughput_tps'] for i in range(3)]
            count = by_key[(cell, arm, 'count', 0)]
            m = group['count'][arm]['interval']
            if m != count['interval_metrics']:
                raise ValueError('interval metric mismatch ' + cell + '/' + arm)
            installed = m['installed']
            if installed <= 0:
                raise ValueError('zero installed versions ' + cell + '/' + arm)
            clocks = count['longtx_counter']['clocks_per_us']
            duration = count['extime']
            threads = int(next(arg.split('=', 1)[1] for arg in count['argv'] if arg.startswith('-thread_num=')))
            lock_seconds = m['install_lock_wait_tsc'] / clocks / 1_000_000
            retention = {name: m[name] for name in ('chain_versions', 'chain_bytes', 'pruned_pending', 'pruned_pending_bytes', 'installed', 'installed_bytes', 'reuse_pool')}
            retention['per_install'] = {name: m[name] / installed for name in ('chain_versions', 'chain_bytes', 'pruned_pending', 'pruned_pending_bytes')}
            hops = {name: {'total': m['hops'][i][j], 'reads': None, 'mean_per_read': None} for name, i, j in SITES}
            tables[cell][arm] = {
                'throughput': {'rep_tps': reps, 'median_tps': statistics.median(reps),
                               'rep_min_tps': min(reps), 'rep_max_tps': max(reps)},
                'retention': retention,
                'hops': hops,
                'gc_cost': {'install_lock_wait_tsc': m['install_lock_wait_tsc'],
                            'install_lock_wait_seconds': lock_seconds,
                            'install_lock_wait_fraction': lock_seconds / (duration * threads),
                            'duration_seconds': duration, 'threads': threads,
                            **{name: m[name] for name in ('attempts', 'success', 'lock_fail', 'cas_fail')}},
                'boundary_samples': m['boundary_samples'], 'pruned': m['pruned'],
                'gc_status': m['gc_status'], 'debug_mode': m['debug_mode'],
            }
    for cell, arms in tables.items():
        stock = arms['stock']['throughput']
        for arm in ARMS:
            this = arms[arm]['throughput']
            this['ratio_to_stock_medians'] = this['median_tps'] / stock['median_tps']
            paired = [v/s for v, s in zip(this['rep_tps'], stock['rep_tps'])]
            this['paired_rep_ratios'] = paired
            this['paired_ratio_min'] = min(paired)
            this['paired_ratio_max'] = max(paired)
    ronly = {cell: {arm: {'boundary_samples': values['boundary_samples'], 'pruned': values['pruned']}
                    for arm, values in arms.items()} for cell, arms in tables.items() if '-ronly-' in cell}
    if any(v['boundary_samples'] or v['pruned'] for arms in ronly.values() for v in arms.values()):
        raise ValueError('read-only long transaction unexpectedly published boundary or pruned')
    mechanism_cost_only = {
        cell: {arm: {'throughput_ratio_to_stock': values['throughput']['ratio_to_stock_medians'],
                     'install_lock_wait_fraction': values['gc_cost']['install_lock_wait_fraction'],
                     'boundary_samples': values['boundary_samples'],
                     'pruned': values['pruned'],
                     'pruning_zero_confirmed': values['pruned'] == 0}
               for arm, values in arms.items()} for cell, arms in tables.items() if '-ronly-' in cell}
    verification_text(aggregate['verification'])
    return {'schema': 'vhash-interval-gc-figures/v1', 'cells': tables,
            'verification': aggregate['verification'], 'perf_status': aggregate['perf_status'],
            'long_read_only_zero_work': ronly, 'mechanism_cost_only_cells': mechanism_cost_only,
            'caveats': [
                'In long read-only transaction cells boundary publication and pruning are zero; throughput differences show install-path cost only.',
                'Between-arm retention and hop totals are confounded by different installed-version counts (write volume). '
                'The install count for each cell and arm is alongside the plotted values at cells[cell][arm].retention.installed.'
            ],
            'part_hosts': {part: sorted(values) for part, values in sorted(hosts.items())},
            'missing': {'mean_hops_per_read': 'read counts are not recorded by CICADA_INTERVAL_COUNT',
                        'other': []},
            'conversions': {'lock_wait_seconds': 'install_lock_wait_tsc / clocks_per_us / 1e6',
                            'lock_wait_fraction': 'lock_wait_seconds / (extime seconds × thread_num)',
                            'per_install': 'end-of-run count or bytes / installed versions',
                            'paired_rep_ratios': 'same rep index variant TPS / stock TPS'}}


def setup(title, caption, shape, verification, size=(23, 12)):
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(*shape, figsize=size)
    fig.subplots_adjust(left=.065, right=.985, top=.79, bottom=.20, hspace=.68, wspace=.17)
    fig.suptitle(title, y=.975, fontsize=16)
    fig.text(.5, .94, '48 threads · N=1M · Zipf 0.9 · 10 ops · 3 s; external GC 10/100 µs; unlink without reuse', ha='center', fontsize=10)
    status_line = verification_text(verification)
    fig.text(.5, .915, status_line + ' Performance: unverified diagnostic data (indeterminate ceiling).', ha='center', fontsize=10)
    fig.text(.5, .06, caption + '\nVerification: ' + status_line, ha='center', va='center', fontsize=9)
    return fig, axs


def xaxis(ax, cells, mark_ronly=False):
    ax.set_xticks(range(len(cells)), [short(c) + ('*' if mark_ronly and '-ronly-' in c else '') for c in cells], rotation=50, ha='right', fontsize=8)
    ax.grid(axis='y', alpha=.25)


def plot_throughput(summary):
    import numpy as np
    cells = summary['cells']
    fig, axs = setup('(a) Throughput and stock-relative throughput',
        'Performance: 3 rotated reps per arm and cell; point = median TPS, whisker = rep min–max. Ratio = median variant / median stock; ratio whiskers = paired rep range.\n'
        'Stock is the dashed 1× line. * ronly: pruning 0; differences show install-path cost only. rr50 / rr95 are separate rows; wait10×2 has two long threads. Missing perf cells: none.', (2, 2), summary['verification'])
    for row, rr in enumerate(('rr50', 'rr95')):
        keys = [c for c in cells if c.startswith(rr)]
        x = np.arange(len(keys))
        left, right = axs[row]
        for arm, offset in (('stock', -.22), ('min', 0), ('gen', .22)):
            values = [cells[c][arm]['throughput'] for c in keys]
            y = np.array([v['median_tps']/1e6 for v in values])
            lo = np.array([v['rep_min_tps']/1e6 for v in values])
            hi = np.array([v['rep_max_tps']/1e6 for v in values])
            left.errorbar(x+offset, y, yerr=[y-lo, hi-y], fmt='o', color=COLORS[arm], capsize=2, label=arm)
            if arm != 'stock':
                ratio = np.array([v['ratio_to_stock_medians'] for v in values])
                rlo = np.array([v['paired_ratio_min'] for v in values])
                rhi = np.array([v['paired_ratio_max'] for v in values])
                # Paired range may not enclose a ratio of medians; draw its interval directly.
                right.vlines(x+offset, rlo, rhi, color=COLORS[arm], alpha=.7)
                right.plot(x+offset, ratio, 'o', color=COLORS[arm], label=arm)
        right.axhline(1, ls='--', lw=1, color=COLORS['stock'])
        left.set_title(rr + ' · throughput'); right.set_title(rr + ' · relative to stock')
        left.set_ylabel('million tx/s'); right.set_ylabel('ratio')
        xaxis(left, keys, mark_ronly=True); xaxis(right, keys, mark_ronly=True)
    fig.legend(handles=axs[0, 0].get_legend_handles_labels()[0], labels=['stock', 'minimum', 'general'], loc='upper center', bbox_to_anchor=(.5, .895), ncol=3)
    return fig, list(axs.flat)


def plot_retention(summary):
    import numpy as np
    cells = summary['cells']; keys = list(cells)
    fig, axs = setup('(b) End-of-run versions and retained bytes',
        'Stack = chain-resident + unlinked but unreused. Top: millions of versions / MiB; bottom: versions or bytes per installed version.\n'
        'Per-install = final count or bytes / that arm’s install count. Arm differences are confounded by install counts (write volume); each cell/arm count is alongside values at summary cells[cell][arm].retention.installed. Count build 1 rep; missing: none.', (2, 2), summary['verification'], (25, 13))
    for col, (on, off, scale, ylabel) in enumerate((('chain_versions', 'pruned_pending', 1e6, 'million versions'),
                                                     ('chain_bytes', 'pruned_pending_bytes', 2**20, 'MiB'))):
        for row, normalized in enumerate((False, True)):
            ax = axs[row, col]
            x = np.arange(len(keys))
            for j, arm in enumerate(ARMS):
                ret = [cells[c][arm]['retention'] for c in keys]
                base = np.array([v['per_install'][on] if normalized else v[on]/scale for v in ret])
                extra = np.array([v['per_install'][off] if normalized else v[off]/scale for v in ret])
                ax.bar(x+(j-1)*.25, base, width=.24, color=COLORS[arm], alpha=.9)
                ax.bar(x+(j-1)*.25, extra, bottom=base, width=.24, color=COLORS[arm], alpha=.38, hatch='//')
            ax.set_title(('per install · ' if normalized else 'end count · ') + ('versions' if col == 0 else 'bytes'))
            ax.set_ylabel(('versions/install' if col == 0 else 'bytes/install') if normalized else ylabel)
            xaxis(ax, keys)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=COLORS[a], label=a) for a in ARMS] +
               [Patch(facecolor='#999999', alpha=.9, label='chain'), Patch(facecolor='#999999', alpha=.38, hatch='//', label='unlinked / unreused')],
               loc='upper center', bbox_to_anchor=(.5, .895), ncol=5)
    return fig, list(axs.flat)


def plot_hops(summary):
    import numpy as np
    cells = summary['cells']; keys = list(cells)
    fig, axs = setup('(c) Version-search hops by read site (count totals)',
        'Each counter increments once per skipped version in a read traversal. Panels split long thread / online and read-only / update.\n'
        'Count build lacks reads by site, so mean hops/read is unavailable; raw totals use symlog. Arm differences are confounded by install counts (write volume); each cell/arm count accompanies values at summary cells[cell][arm].retention.installed. Missing: per-read denominator.', (2, 2), summary['verification'], (25, 13))
    for ax, (site, _, _) in zip(axs.flat, SITES):
        x = np.arange(len(keys))
        for j, arm in enumerate(ARMS):
            ax.bar(x+(j-1)*.25, [cells[c][arm]['hops'][site]['total'] for c in keys], width=.24, color=COLORS[arm], label=arm)
        ax.set_yscale('symlog', linthresh=1)
        ax.set_title(site.replace('_', ' / ')); ax.set_ylabel('total skipped-version hops')
        xaxis(ax, keys)
    fig.legend(handles=axs[0, 0].get_legend_handles_labels()[0], labels=['stock', 'minimum', 'general'], loc='upper center', bbox_to_anchor=(.5, .895), ncol=3)
    return fig, list(axs.flat)


def plot_cost(summary):
    import numpy as np
    cells = summary['cells']
    fig, axs = setup('(d) Interval GC cost in count runs',
        'Install lock fraction = rdtscp wait cycles / clocks_per_us / 1e6 / (3 s × 48 threads), summed over threads.\n'
        'Pruning: circle = attempts, square = success, triangle = lock failure; solid = minimum, dashed = general. Stock is not applicable (0 for reference). Count build 1 rep; missing cells: none.', (2, 2), summary['verification'])
    for row, rr in enumerate(('rr50', 'rr95')):
        keys = [c for c in cells if c.startswith(rr)]
        x = np.arange(len(keys)); a, b = axs[row]
        for j, arm in enumerate(ARMS):
            a.bar(x+(j-1)*.25, [100*cells[c][arm]['gc_cost']['install_lock_wait_fraction'] for c in keys], width=.24, color=COLORS[arm], label=arm)
        for arm, ls in (('min', '-'), ('gen', '--')):
            for metric, marker in (('attempts', 'o'), ('success', 's'), ('lock_fail', '^')):
                b.plot(x, [cells[c][arm]['gc_cost'][metric] for c in keys], marker=marker, ls=ls, color=COLORS[arm], ms=3, label=arm+' '+metric)
        a.set_title(rr + ' · install lock wait'); b.set_title(rr + ' · pruning counters')
        a.set_ylabel('thread-time share (%)'); b.set_ylabel('count')
        xaxis(a, keys); xaxis(b, keys)
    fig.legend(handles=axs[0, 0].get_legend_handles_labels()[0], labels=['stock', 'minimum', 'general'], loc='upper center', bbox_to_anchor=(.5, .895), ncol=3)
    return fig, list(axs.flat)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--aggregate', type=Path, required=True)
    p.add_argument('--raw', type=Path, nargs='+', required=True)
    p.add_argument('--output-prefix', type=Path, required=True)
    p.add_argument('--summary', type=Path, required=True)
    args = p.parse_args(argv)
    if len(args.raw) != 40 or len({str(p.resolve()) for p in args.raw}) != 40:
        raise ValueError('require exactly 40 distinct raw parts')
    aggregate = json.loads(args.aggregate.read_text())
    raw = [json.loads(line) for path in args.raw for line in path.read_text().splitlines() if line.strip()]
    summary = collect(aggregate, raw)
    inputs = {str(path.resolve()): sha256(path) for path in (args.aggregate, *args.raw)}
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'pdf.fonttype': 42})
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    figures = {}
    for label, fn in (('a-throughput', plot_throughput), ('b-retention', plot_retention),
                      ('c-hops', plot_hops), ('d-gc-cost', plot_cost)):
        fig, axes = fn(summary)
        check_figure_layout(fig, axes)
        out = args.output_prefix.with_name(args.output_prefix.name + '-' + label)
        fig.savefig(out.with_suffix('.png'), dpi=180)
        fig.savefig(out.with_suffix('.pdf'))
        provenance = {'campaign_id': 'vhash-interval-gc-2026-09-29', 'figure': label,
                      'inputs': inputs, 'conditions': {'threads': 48, 'records': 1_000_000,
                      'zipf': .9, 'operations': 10, 'duration_seconds': 3,
                      'read_ratios': [50, 95], 'gc_interval_us': [10, 100],
                      'variant': 'unlink without reuse (debug_mode=1)'},
                      'conversions': summary['conversions'], 'major_values': summary['cells'],
                      'missing': summary['missing'], 'verification': summary['verification']['status'],
                      'performance_status': summary['perf_status']}
        out.with_suffix('.provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n')
        figures[label] = str(out)
        plt.close(fig)
    summary['figure_prefixes'] = figures
    summary['inputs'] = inputs
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print('layout checks passed for 4 figures; aggregate recomputation matched; 40 raw parts')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
