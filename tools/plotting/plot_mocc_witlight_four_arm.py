#!/usr/bin/env python3
"""Pinned, non-certifying MOCC witness observations: one forest and exposure columns."""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

SCHEMA = 'izanagi-mocc-witlight-four-arm-figure-provenance/v1'
GENERATOR_PATH = 'tools/plotting/plot_mocc_witlight_four_arm.py'
GENERATOR = Path(__file__).resolve()
REPO_ROOT = GENERATOR.parents[2]
EVIDENCE_ROOT = '/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W'
EXTERNAL_SHA256 = {
    'summary.json': 'b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698',
    'W1/result.json': 'ca8ab3ff579e3fb55b97447ebb7b647d34806a6fd452ad410051aca9e5bd4b50',
    'W2/result.json': '473063aa741cc4c349931d987c902facbc5dcf6499b3692ea2cad3a27ac1e584',
    'W3/result.json': 'f68876600f1cd5b7300b030fb3cfa75509cc7a687858d6f12985051ce46e3642',
    'W4/result.json': '197a2798de5ef53a7f6a32460f7ecfa5adbba8e853778b315d3b6e1839c36a6c',
}
CAPTION_SOURCE = 'docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md'
ARMS = ('e9-witlight-wit', 'e9-witlight-nowit', 'e9-witlight-wit-bo1', 'e9-witlight-nowit-bo1')
BLOCKS = ('W1', 'W2', 'W3', 'W4')
ROUNDS = 15
RUNS_PER_BLOCK = PLANNED_PER_ARM = 60
PIN = 'e9e477ca1b55348ab4530de0b1cf663ce4555290'
WORKLOAD_ARGV = ['-ycsb_tuple_num=10000', '-thread_num=48', '-ycsb_zipf_skew=0.9', '-ycsb_rratio=50', '-ycsb_rmw=0', '-ycsb_max_ope=10', '-extime=3']
DISC_STATUSES = ('supported', 'contradicted', 'indeterminate', 'no-g2', 'input-rejected', 'not-run')
FIXED_SENTENCES = (
    'Non-significance does not establish equivalence, and zero detections do not establish absence.',
    'Power 0.105 is a calculation under the design assumptions, not a measured quantity: independent Bernoulli trials, 60 runs per arm, off probability 0.0417, on probability 0, and a one-sided Fisher test at alpha 0.05.',
    'TRACE=1 commit counts are exposure, not performance.',
    'G2 signals do not identify a root cause or distinguish a real anomaly from a torn read.',
    'This is a non-certifying observation; individual verifier certified flags and observational_only=false do not certify this wave, MOCC, or the witness.',
    'The denominator includes only 4 blocks x 15 rounds x 4 arms; smoke runs are excluded.',
    'CP intervals and Fisher p values assume independent Bernoulli trials and do not model within-node dependence, rotation order, or temporal variation.',
)


class FigureDataError(ValueError):
    """Input or provenance does not satisfy this figure's contract."""


class FigureLayoutError(FigureDataError):
    """Renderer found overlapping or escaping text."""


def _require(condition, message):
    if not condition:
        raise FigureDataError(message)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _beta_quantile(q, a, b):
    lo, hi = 0., 1.
    n = a + b - 1
    for _ in range(70):
        x = (lo + hi) / 2
        cdf = math.fsum(math.comb(n, j) * x**j * (1-x)**(n-j) for j in range(a, n+1))
        if cdf < q:
            lo = x
        else:
            hi = x
    return (lo + hi) / 2


def _cp95(k, m):
    _require(type(k) is int and type(m) is int and 0 <= k <= m and m > 0, 'CP counts')
    return [0. if k == 0 else _beta_quantile(.025, k, m-k+1),
            1. if k == m else _beta_quantile(.975, k+1, m-k)]


def _fisher_less(table):
    (a, b), (c, d) = table
    _require(all(type(v) is int and v >= 0 for v in (a, b, c, d)), 'Fisher counts')
    n, total, successes = a+b, a+b+c+d, a+c
    return math.fsum(math.comb(successes, x)*math.comb(total-successes, n-x)/math.comb(total, n)
                     for x in range(max(0, n-(total-successes)), min(a, successes)+1))


def _pins(expected_hashes):
    pins = EXTERNAL_SHA256 if expected_hashes is None else expected_hashes
    _require(set(pins) == set(EXTERNAL_SHA256), 'external input key set')
    _require(all(isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v) for v in pins.values()), 'external digest')
    return pins


def _source_inputs(pins):
    return [dict(path=f'{EVIDENCE_ROOT}/{b}/result.json', sha256=pins[f'{b}/result.json']) for b in BLOCKS]


def _external_inputs(pins):
    return [dict(path=p, kind='summary' if p == 'summary.json' else 'block_result', sha256=pins[p]) for p in EXTERNAL_SHA256]


def _load_external(evidence_root, expected_hashes=None):
    pins = _pins(expected_hashes)
    docs = {}
    for rel in EXTERNAL_SHA256:
        path = Path(evidence_root)/rel
        _require(_sha256(path) == pins[rel], f'external SHA-256 mismatch: {rel}')
        docs[rel] = _json(path)
    summary = docs['summary.json']
    _require(summary['schema_version'] == 't2774-summary/v1', 'summary schema')
    _require(summary['inputs'] == _source_inputs(pins), 'summary inputs exact mismatch')
    return summary, [docs[f'{b}/result.json'] for b in BLOCKS]


def _validate_blocks(blocks):
    _require(len(blocks) == 4, 'block count')
    for bi, block in enumerate(blocks):
        _require(block['schema_version'] == 't2774-probe/v1', 'block schema')
        _require(block['block_id'] == BLOCKS[bi], 'block ID')
        _require(block['status'] == 'completed' and block['rounds'] == ROUNDS
                 and block['planned_runs'] == RUNS_PER_BLOCK and block['not_started'] == 0, 'block completion')
        binding = block['bindings']
        _require(binding['workload_argv'] == blocks[0]['bindings']['workload_argv'] == WORKLOAD_ARGV, 'workload_argv')
        _require(set(binding['arms']) == set(ARMS), 'binding arm set')
        for ai, arm in enumerate(ARMS):
            spec = binding['arms'][arm]
            _require(spec['witness'] is (ai % 2 == 0) and spec['pin'] == PIN, 'arm binding witness/pin')
            for definitions in (spec['configure_defines'], spec['configure_argv']):
                _require([s for s in definitions if s.startswith('-DCCBENCH_BACK_OFF=')] == [f'-DCCBENCH_BACK_OFF={ai//2}'], 'arm binding BACK_OFF')
                _require([s for s in definitions if s.startswith('-DCCBENCH_TRACE=')] == ['-DCCBENCH_TRACE=1'], 'arm binding TRACE')
        _require(len(block['runs']) == RUNS_PER_BLOCK, 'runs count')
        for ri, run in enumerate(block['runs']):
            rotation = (bi + ri//4) % 4
            order = list(ARMS[rotation:] + ARMS[:rotation])
            _require(run['ordinal'] == ri+1 and run['round'] == ri//4+1, 'ordinal/round')
            _require(run['order'] == order and run['arm'] == order[ri % 4], 'arm rotation/order')
            _require(run['block_id'] == block['block_id'] and run['hostname'] == block['hostname'], 'run block/host')
            spec = binding['arms'][run['arm']]
            _require(run['witness'] is spec['witness'] and run['pin'] == spec['pin'], 'run arm binding')
            _require(run['rc'] == 0 and (run['verifier']['rc'], run['verifier']['status']) in ((0, 'no-g2'), (1, 'g2')), 'failure or indeterminate run')
            _require(type(run['commit_count']) is int and run['commit_count'] > 0, 'commit_count')
            _require(run['discriminator']['status'] == 'not-run', 'discriminator scope')
            _require(not (run['witness'] and run['verifier']['status'] == 'g2'), 'on G2 outside unreached discriminator scope')


def _project_runs(blocks):
    return [{k: copy.deepcopy(run[k]) for k in ('block_id', 'ordinal', 'round', 'order', 'arm', 'rc', 'commit_count', 'verifier', 'discriminator')}
            for block in blocks for run in block['runs']]


def _pct(value):
    return '0%' if value == 0 else f'{100*value:.3f}%'


def _format_arm(a):
    return dict(k_over_m=f"{a['k']}/{a['m']}", rate=_pct(a['k_over_m']),
                cp95=f"[{_pct(a['cp95'][0])}, {_pct(a['cp95'][1])}]", mean_commits=f"{a['commit_count_mean']:,.1f}")


def _comparisons(arms):
    comparisons, ratios = [], []
    for bo in (0, 1):
        on, off = [arms[a] for a in ARMS[2*bo:2*bo+2]]
        table = [[a['k'], a['m']-a['k']] for a in (on, off)]
        p = _fisher_less(table)
        comparisons.append(dict(back_off=bo, table=table, direction='on lower', adjustment='unadjusted', p=p, p_text=f'{p:.3f}'))
        ratio = on['commit_count_mean']/off['commit_count_mean']
        ratios.append(dict(back_off=bo, ratio=ratio, text=f'{ratio:.4f}'))
    return comparisons, ratios


def _derive_statistics(records):
    arms = {}
    for arm in ARMS:
        rows = [r for r in records if r['arm'] == arm]
        n = len(rows)
        _require(n == PLANNED_PER_ARM, 'arm N')
        k = sum(r['verifier']['status'] == 'g2' for r in rows)
        total = sum(r['commit_count'] for r in rows)
        counts = Counter(r['discriminator']['status'] for r in rows)
        a = dict(N=n, m=n, k=k, failure=0, indeterminate=0, decisive_m=n, k_over_m=k/n, cp95=_cp95(k, n),
                 discriminator_counts={s: counts[s] for s in DISC_STATUSES},
                 identification=dict(g2_runs=k, identified_g2_runs=0, rate=0. if k else None),
                 positions={str(i+1): sum(r['order'].index(arm) == i for r in rows) for i in range(4)},
                 commit_count_sum=total, commit_count_mean=total/n)
        a['formatted'] = _format_arm(a)
        arms[arm] = a
    comparisons, ratios = _comparisons(arms)
    return dict(arms=arms, comparisons=comparisons, exposure_ratios=ratios)


def _crosscheck_summary(derived, summary):
    _require(set(summary['arms']) == set(ARMS), 'summary arm set')
    for arm, a in derived['arms'].items():
        other = summary['arms'][arm]
        for key in ('N', 'm', 'k', 'failure', 'indeterminate', 'decisive_m', 'discriminator_counts', 'identification'):
            _require(a[key] == other[key], f'summary {arm} {key}')
        _require(math.isclose(a['k_over_m'], other['k_over_m'], rel_tol=0, abs_tol=1e-12), 'summary k_over_m')
        _require(len(other['cp95']) == 2 and all(math.isclose(x, y, rel_tol=0, abs_tol=1e-12) for x, y in zip(a['cp95'], other['cp95'])), 'summary cp95')


def _measurement_conditions(argv):
    _require(argv == WORKLOAD_ARGV, 'measurement workload_argv')
    values = dict(s.lstrip('-').split('=', 1) for s in argv)
    return dict(workload_argv=list(argv), threads=int(values['thread_num']), records=int(values['ycsb_tuple_num']),
                zipf=float(values['ycsb_zipf_skew']), read_ratio=int(values['ycsb_rratio']), rmw=int(values['ycsb_rmw']),
                max_operations=int(values['ycsb_max_ope']), seconds=int(values['extime']), trace=1, pin=PIN,
                patches='X/P + witlight patches', location='Pegasus compute nodes', blocks=list(BLOCKS), rounds=ROUNDS, smoke_excluded=True)


def _external_data(evidence_root, expected_hashes=None):
    summary, blocks = _load_external(evidence_root, expected_hashes)
    _validate_blocks(blocks)
    records = _project_runs(blocks)
    derived = _derive_statistics(records)
    _crosscheck_summary(derived, summary)
    return dict(**derived, external_inputs=_external_inputs(_pins(expected_hashes)), source_inputs=summary['inputs'],
                measurement_conditions=_measurement_conditions(blocks[0]['bindings']['workload_argv']),
                blocks=[dict(block=b['block_id'], hostname=b['hostname'], arms={a: dict(m=15, k=sum(r['arm'] == a and r['verifier']['status'] == 'g2' for r in b['runs'])) for a in ARMS}) for b in blocks])


def load_evidence(repo_root, evidence_root=EVIDENCE_ROOT, *, expected_hashes=None):
    try:
        root = Path(repo_root).resolve()
        return dict(repo_root=str(root), tracked_inputs=[dict(kind='caption_source', path=CAPTION_SOURCE, sha256=_sha256(root/CAPTION_SOURCE))],
                    **_external_data(evidence_root, expected_hashes))
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f'invalid evidence: {exc}') from exc


def _figure_number(prefix):
    match = re.match(r'fig([0-9]+)_', Path(prefix).name)
    _require(match is not None, 'prefix must start fig<N>_')
    return int(match.group(1))


def _caption(data, prefix):
    c = data['measurement_conditions']
    sentences = [f'Figure {_figure_number(prefix)}. Stock MOCC lightweight witness observations: G2 signal detection rates with two-sided 95% Clopper–Pearson (CP) intervals and descriptive mean commits per run.']
    for i, arm in enumerate(ARMS):
        f = data['arms'][arm]['formatted']
        sentences.append(f"{arm} ({'on' if i%2 == 0 else 'off'} / BACK_OFF={i//2}): {f['k_over_m']}, {f['rate']}, CP {f['cp95']}, mean commits per run {f['mean_commits']}.")
    for comp, ratio in zip(data['comparisons'], data['exposure_ratios']):
        sentences.append(f"{'Primary' if comp['back_off'] == 0 else 'Secondary'} comparison BACK_OFF={comp['back_off']}: one-sided Fisher (on lower), unadjusted p = {comp['p_text']}; on/off exposure ratio {ratio['text']}.")
    locations = [f"{b['block']} {a} ({v['k']}/{v['m']})" for b in data['blocks'] for a, v in b['arms'].items() if v['k']]
    sentences.append('G2 signal locations: ' + '; '.join(locations) + '.')
    sentences.extend(FIXED_SENTENCES)
    sentences.extend([
        'The discriminator was not reached: no on-arm G2 signals occurred, so it fired zero times and made zero comparisons.',
        f"Detection rates are per fixed-time {c['seconds']} s run, not a comparison at equal commit exposure.",
        'Values from earlier waves [T-1892], [T-2774], and [T-2779] are neither pooled nor compared here.',
        f"Conditions: {c['threads']} threads, {c['records']:,} records, Zipf {c['zipf']}, read ratio {c['read_ratio']}, rmw {c['rmw']}, max operations {c['max_operations']}, {c['seconds']} s, TRACE={c['trace']} build, pin {c['pin'][:8]} + {c['patches']}, {c['location']}, 4 blocks W1–W4 x {c['rounds']} rounds x 4 arms, smoke excluded.",
    ])
    return ' '.join(sentences)


def _artist_series(data):
    rows = []
    for i, arm in enumerate(ARMS):
        a = data['arms'][arm]
        rows.append(dict(arm=arm, label=f"{'on' if i%2 == 0 else 'off'} / BACK_OFF={i//2}", y=3-i,
                         rate_pct=100*a['k_over_m'], cp95_pct=[100*v for v in a['cp95']], **a['formatted']))
    notes = ['non-certifying; TRACE=1 build', 'Commits: exposure, not performance']
    notes += [f"BACK_OFF={c['back_off']}: one-sided Fisher (on lower, unadjusted) p = {c['p_text']}" for c in data['comparisons']]
    notes += ['Not significant is not equivalence; power 0.105 is calculated under design assumptions.',
              'G2 signal: verifier detection; does not identify a root cause.']
    return dict(rows=rows, headers=['k/m', 'Rate', 'CP 95%', 'mean commits per run'],
                exposure_notes=[f"BACK_OFF={r['back_off']}: on/off exposure ratio {r['text']}" for r in data['exposure_ratios']], notes=notes)


def make_figure(data):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'pdf.fonttype': 42})
    fig, ax = plt.subplots(figsize=(14, 6.4))
    fig.subplots_adjust(left=.17, right=.48, bottom=.47, top=.83)
    series = _artist_series(data)
    ax.set(xlim=(-.45, 10), ylim=(-.6, 3.8), xlabel='G2 signal detection rate (%)')
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.set_yticks([r['y'] for r in series['rows']], [r['label'] for r in series['rows']])
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', alpha=.2)
    fig.suptitle('Stock MOCC lightweight witness: G2 signal detection', y=.96, fontsize=14)
    columns = [.53, .60, .69, .85]
    for x, header in zip(columns, series['headers']):
        fig.text(x, .85, header, ha='center', fontsize=10)
    for row in series['rows']:
        ax.plot(row['cp95_pct'], [row['y']]*2, color='#24618a', linewidth=2, gid='cp-interval')
        ax.plot([row['rate_pct']], [row['y']], 'o', color='#172b4d', markersize=6, gid='rate-point')
        y = fig.transFigure.inverted().transform(ax.transData.transform((0, row['y'])))[1]
        for x, key in zip(columns, ('k_over_m', 'rate', 'cp95', 'mean_commits')):
            fig.text(x, y, row[key], ha='center', va='center', gid='numeric-column')
    for i, text in enumerate(series['exposure_notes']):
        fig.text(.53, .415-i*.038, text, fontsize=10)
    for i, text in enumerate(series['notes']):
        fig.text(.065, .315-i*.044, text, fontsize=10)
    # This exact object supplied every numeric artist and direct text above.
    fig._mocc_artist_series = copy.deepcopy(series)
    return fig, np.asarray([ax])


def _intersection(left, right):
    return max(0, min(left.x1, right.x1) - max(left.x0, right.x0)) * max(0, min(left.y1, right.y1) - max(left.y0, right.y0))


def _contains(outer, inner):
    return inner.x0 >= outer.x0 - 1 and inner.y0 >= outer.y0 - 1 and inner.x1 <= outer.x1 + 1 and inner.y1 <= outer.y1 + 1


def check_figure_layout(fig, axes):
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    plot_axes = list(np.asarray(axes).flat)
    if len(plot_axes) != 1 or set(plot_axes) != set(fig.axes):
        raise FigureLayoutError("production layout must contain exactly one axis")
    boxes = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not _contains(fig.bbox, box):
            raise FigureLayoutError(f"text leaves figure: {text.get_text()!r}")
        if text.get_gid() == "direct-label" and (text.axes is None or not _contains(text.axes.bbox, box)):
            raise FigureLayoutError("annotation leaves owner axis")
        if text.axes is not None:
            for other in fig.axes:
                if other is not text.axes and _intersection(box, other.bbox) > 1:
                    raise FigureLayoutError("text enters neighboring panel")
        boxes.append((text, box))
    for index, (left, box) in enumerate(boxes):
        for right, other in boxes[index + 1:]:
            if _intersection(box, other) > 1:
                raise FigureLayoutError(f"text bbox overlap: {left.get_text()!r} / {right.get_text()!r}")
    for axis in fig.axes:
        if not _contains(fig.bbox, axis.get_tightbbox(renderer)):
            raise FigureLayoutError("axis decoration leaves figure")


def build_provenance(data, outputs, argv, *, hash_paths=None, generated_utc=None, artist_series=None):
    hashes = outputs if hash_paths is None else hash_paths
    _require(len(outputs) == len(hashes) == 2, "two figure outputs required")
    return {
        **{key: copy.deepcopy(value) for key, value in data.items() if key not in ("repo_root", "tracked_inputs")},
        "tracked_inputs": copy.deepcopy(data["tracked_inputs"]),
        "schema": SCHEMA,
        "generated_utc": generated_utc or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": {"path": GENERATOR_PATH, "sha256": _sha256(GENERATOR)},
        "outputs": [{"path": os.path.relpath(Path(p).resolve(), data["repo_root"]), "sha256": _sha256(h)}
                    for p, h in zip(outputs, hashes)],
        "artist_series": copy.deepcopy(_artist_series(data) if artist_series is None else artist_series),
        "caption": _caption(data, Path(outputs[0]).with_suffix("")),
        "reproduction": {"cwd": "repository-root", "argv": list(argv), "command": shlex.join(argv)},
    }


def _validate_projection(p):
    _require(set(p['arms']) == set(ARMS), 'arms key set')
    _require([b['block'] for b in p['blocks']] == list(BLOCKS), 'blocks identities')
    for b in p['blocks']:
        _require(set(b['arms']) == set(ARMS) and isinstance(b['hostname'], str) and b['hostname'], 'blocks shape')
        for a in b['arms'].values():
            _require(a['m'] == 15 and type(a['k']) is int and 0 <= a['k'] <= 15, 'block counts')
    for i, arm in enumerate(ARMS):
        a = p['arms'][arm]
        _require(a['N'] == a['m'] == a['decisive_m'] == 60 and a['failure'] == a['indeterminate'] == 0, 'arms denominator')
        _require(a['k'] == sum(b['arms'][arm]['k'] for b in p['blocks']), 'arms block counts')
        _require(i%2 == 1 or a['k'] == 0, 'on G2 scope')
        _require(a['k_over_m'] == a['k']/a['m'] and a['cp95'] == _cp95(a['k'], a['m']), 'arms rates/CP')
        _require(type(a['commit_count_sum']) is int and a['commit_count_sum'] > 0
                 and a['commit_count_mean'] == a['commit_count_sum']/a['N'], 'arms commit mean')
        _require(a['positions'] == {str(i): 15 for i in range(1,5)}, 'arms positions')
        _require(a['discriminator_counts'] == {s: 60 if s == 'not-run' else 0 for s in DISC_STATUSES}, 'arms discriminator')
        _require(a['identification'] == dict(g2_runs=a['k'], identified_g2_runs=0, rate=0. if a['k'] else None), 'arms identification')
        _require(a['formatted'] == _format_arm(a), 'arms formatted')
    comparisons, ratios = _comparisons(p['arms'])
    _require(p['comparisons'] == comparisons, 'comparisons closure')
    _require(p['exposure_ratios'] == ratios, 'exposure_ratios closure')
    _require(p['measurement_conditions'] == _measurement_conditions(p['measurement_conditions']['workload_argv']), 'measurement_conditions closure')


def validate_repo_closure(provenance, repo_root, *, expected_hashes=None):
    """Check saved statistics' self-consistency; never open external evidence."""
    try:
        p, root = provenance, Path(repo_root).resolve()
        keys = {'schema', 'generated_utc', 'generator', 'tracked_inputs', 'external_inputs', 'source_inputs',
                'measurement_conditions', 'arms', 'blocks', 'comparisons', 'exposure_ratios', 'artist_series', 'caption', 'outputs', 'reproduction'}
        _require(set(p) == keys and p['schema'] == SCHEMA, 'provenance schema/key set')
        pins = _pins(expected_hashes)
        _require(p['external_inputs'] == _external_inputs(pins), 'external_inputs closure')
        _require(p['source_inputs'] == _source_inputs(pins), 'source_inputs closure')
        _require(p['tracked_inputs'] == [dict(kind='caption_source', path=CAPTION_SOURCE, sha256=_sha256(root/CAPTION_SOURCE))], 'tracked_inputs closure')
        _require(p['generator']['path'] == GENERATOR_PATH and re.fullmatch('[0-9a-f]{64}', p['generator']['sha256']), 'generator metadata')
        outputs = p['outputs']
        _require(len(outputs) == 2 and [Path(r['path']).suffix for r in outputs] == ['.png', '.pdf'], 'output paths')
        prefix = Path(outputs[0]['path']).with_suffix('')
        _require(Path(outputs[1]['path']).with_suffix('') == prefix, 'output prefix')
        for row in outputs:
            _require(_sha256(root/row['path']) == row['sha256'], 'output closure')
        _validate_projection(p)
        _require(p['artist_series'] == _artist_series(p), 'artist_series closure')
        _require(p['caption'] == _caption(p, prefix), 'caption closure')
        argv = p['reproduction']['argv']
        _require(len(argv) == 7 and argv[:3] == ['python3', GENERATOR_PATH, '--repo-root'] and argv[4] == '--evidence-root'
                 and Path(argv[3]).is_absolute() and Path(argv[5]).is_absolute() and argv[6] == str(prefix), 'reproduction argv')
        _require(p['reproduction'] == dict(cwd='repository-root', argv=argv, command=shlex.join(argv)), 'reproduction closure')
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f'invalid repo closure: {exc}') from exc


def validate_external_sources(provenance, evidence_root, *, expected_hashes=None):
    """Recompute statistics, formatting and conditions from the five originals."""
    try:
        data = _external_data(evidence_root, expected_hashes)
        for key, value in data.items():
            _require(provenance[key] == value, f'external {key} closure')
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f'invalid external sources: {exc}') from exc


def _publish_outputs(fig, axes, prefix, data, argv):
    _figure_number(prefix)
    check_figure_layout(fig, axes)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    destinations = [Path(f"{prefix}{suffix}") for suffix in (".png", ".pdf", ".provenance.json")]
    temporary, published = [], []
    try:
        for suffix in (".png", ".pdf", ".provenance.json"):
            fd, name = tempfile.mkstemp(prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent)
            os.close(fd)
            temporary.append(Path(name))
        for path, fmt in zip(temporary[:2], ("png", "pdf")):
            fig.savefig(path, format=fmt, dpi=200)
        provenance = build_provenance(data, destinations[:2], argv, hash_paths=temporary[:2],
                                      artist_series=fig._mocc_artist_series)
        temporary[2].write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        previous = {p: p.read_bytes() if p.exists() else None for p in destinations}
        try:
            for source, destination in zip(temporary, destinations):
                os.replace(source, destination)
                published.append(destination)
        except OSError:
            for path in published:
                if previous[path] is None:
                    path.unlink()
                else:
                    path.write_bytes(previous[path])
            raise
        return destinations
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def main(argv=None, *, expected_hashes=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--evidence-root", type=Path, default=Path(EVIDENCE_ROOT))
    parser.add_argument("out_prefix", type=Path)
    args = parser.parse_args(argv)
    root, prefix = args.repo_root.resolve(), args.out_prefix.resolve()
    figure = None
    try:
        _figure_number(prefix)
        data = load_evidence(root, args.evidence_root.resolve(), expected_hashes=expected_hashes)
        figure, axes = make_figure(data)
        expanded = ["python3", GENERATOR_PATH, "--repo-root", str(root), "--evidence-root", str(args.evidence_root.resolve()), os.path.relpath(prefix, root)]
        _publish_outputs(figure, axes, prefix, data, expanded)
    except Exception as exc:
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {prefix}.png / .pdf / .provenance.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
