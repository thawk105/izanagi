#!/usr/bin/env python3
"""Pinned B-10 waiting grid: recorded family outcomes and paired-block intervals."""
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
import statistics
import sys
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from matplotlib.patches import Patch

SCHEMA = "izanagi-b10-waiting-grid-forest-figure-provenance/v1"
GENERATOR_PATH = "tools/plotting/plot_b10_waiting_grid_forest.py"
GENERATOR = Path(__file__).resolve()
REPO_ROOT = GENERATOR.parents[2]
PROVENANCE_JSON = "output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json"
REPORT_MD = str(Path(PROVENANCE_JSON).with_name("b10_backoff_shape_report_978195.nqsv-23409962b76b.md"))
PINNED_SHA256 = {
    PROVENANCE_JSON: "a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca",
    REPORT_MD: "e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768",
}
INPUT_KINDS = ("report_provenance", "report_markdown")
CAPTION_SOURCE = "docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md"
CAPTION_SCOPE = "source of wording of limitations and conditions; not the primary authority for measurement values or judgments"
EVIDENCE_ROOT = "/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape"
REPORT_NONCE = "23409962b76be959bb523a0cd5a31bc1"
REPORT_REQUEST = "978195.nqsv"
EXTERNAL_REL = {
    "report_receipt": f"submissions/{REPORT_NONCE}/submit-receipt.json",
    "report_job_result": f"submissions/{REPORT_NONCE}/job-attempts/{REPORT_REQUEST}/job-result.json",
}
EXTERNAL_SHA256 = {
    "report_receipt": "93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4",
    "report_job_result": "d5d4a0ee4c503c1b4b6a811f998949f7a76434a575c4ed8d0bfad849eafd082b",
}
# These fields are absent from the tracked report; pinned external bytes supply them.
REPORT_SUBMITTED_EPOCH = 1788581651
REPORT_COMPLETED_EPOCH = 1788582054
PROVENANCE_SCHEMA = "b10-backoff-shape-provenance/v2"
JUDGEMENT_SCHEMA = "b10-backoff-shape-judgement/v1"
RECEIPT_SCHEMA = "pegasus-b10-submit-receipt/v2"
JOB_RESULT_SCHEMA = "pegasus-b10-job-result/v1"
PREREG_COMMIT = "77b33e37d2d63b1f83d10652792c3c93eba9fe8f"
SOURCE_COMMIT = "2a338449bb2798b729c5bc2f9bfe76463a7fe347"
CCBENCH_PIN = "511c953"
SPEC_SHA256 = "9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2"
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
BLOCKS = ("block-1", "block-2", "block-3")
MEANS_US = (2, 5, 10, 25, 50, 100)
SHAPES = ("constant", "symmetric-modulo")
REFERENCE_SHAPE, CONTRAST_SHAPE = SHAPES
PAIRS_PER_FAMILY = 18
ENUMERATION = 2 ** 18
ALPHA = 0.05
EQUIVALENCE_MARGIN_PCT = 3.0
T975_DF2 = 4.302652729911275
DF = 2
REPS = 5
POINTS_PER_BLOCK = 15
RECORDS = 135
CELLS = 36
FAMILIES = 3
RELATIONS = ("inside-equivalence-range", "overlaps-equivalence-boundary", "outside-equivalence-range")


class FigureDataError(ValueError):
    """Invalid or incomplete evidence."""


class FigureLayoutError(FigureDataError):
    """Rendered text violates the layout contract."""


def _require(condition, message):
    if not condition:
        raise FigureDataError(message)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _number(value):
    _require(type(value) in (int, float) and math.isfinite(value), "finite number required")
    return value


def _string(value):
    _require(type(value) is str and bool(value.strip()), "nonempty string required")
    return value


def _digest(value):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "64 hex digest required")
    return value


def _close(left, right, tolerance=1e-12):
    return math.isclose(_number(left), _number(right), rel_tol=0, abs_tol=tolerance)


def _load_tracked(root, expected_hashes):
    hashes = PINNED_SHA256 if expected_hashes is None else expected_hashes
    _require(set(hashes) == set(PINNED_SHA256), 'input hash keys mismatch')
    tracked = []
    for path, kind in zip(PINNED_SHA256, INPUT_KINDS):
        digest = _sha256(root / path)
        _require(digest == hashes[path], f'SHA-256 mismatch: {path}')
        tracked.append(dict(kind=kind, path=path, sha256=digest))
    tracked.append(dict(kind='caption_source', path=CAPTION_SOURCE,
                        sha256=_sha256(root / CAPTION_SOURCE), authority_scope=CAPTION_SCOPE))
    return _json(root / PROVENANCE_JSON), (root / REPORT_MD).read_text(), tracked


def _relation(low, high):
    margin = EQUIVALENCE_MARGIN_PCT / 100
    if low >= -margin and high <= margin:
        return RELATIONS[0]
    if high < -margin or low > margin:
        return RELATIONS[2]
    return RELATIONS[1]


def _authority_data(root, expected_hashes=None):
    source, markdown, tracked = _load_tracked(root, expected_hashes)
    _require(source['schema_version'] == PROVENANCE_SCHEMA, 'provenance schema')
    _require(source['official_certification'] is False, 'official_certification must be false')
    _require(source['pin'] == CCBENCH_PIN, 'CCBench pin')
    submission = source['submission']
    for key, value in dict(request_id=REPORT_REQUEST, nonce=REPORT_NONCE, phase='report',
                           source_commit=SOURCE_COMMIT, prereg_commit=PREREG_COMMIT).items():
        _require(submission[key] == value, f'submission {key}')
    _require(submission['receipt_sha256'] == EXTERNAL_SHA256['report_receipt'], 'submission receipt_sha256')
    _digest(submission['job_script_sha256'])
    judgement = source['judgement']
    _require(judgement['schema_version'] == JUDGEMENT_SCHEMA, 'judgement schema')
    _require(judgement['alpha'] == ALPHA and judgement['spec_sha256'] == SPEC_SHA256, 'judgement constants')
    spec = source['preregistration']['spec']
    analysis = spec['analysis']
    _require(analysis['alpha'] == ALPHA and analysis['equivalence_margin_pct'] == EQUIVALENCE_MARGIN_PCT, 'spec constants')
    ci = analysis['confidence_interval']
    _require(ci['critical_value'] == T975_DF2 and ci['degrees_of_freedom'] == DF
             and ci['method'] == 'student-t-paired-block-mean', 'spec confidence interval')
    permutation = analysis['permutation']
    _require(permutation['enumeration'] == 'all-2^18' and permutation['pairs_per_family'] == PAIRS_PER_FAMILY
             and permutation['sided'] == 'two-sided', 'spec permutation')
    _require(analysis['holm_families'] == [dict(shape=CONTRAST_SHAPE, workload=w) for w in WORKLOADS], 'spec families')
    _require(spec['grid']['means_us'] == list(MEANS_US)
             and [s['name'] for s in spec['grid']['shapes']] == list(SHAPES), 'spec grid')
    minimum = _number(analysis['exposure']['minimum_calls_per_cell'])
    _require(minimum == 10000, 'spec exposure')
    records = source['records']
    _require(len(records) == RECORDS, 'record count')
    points = {'none': (None, None), 'adaptive': (None, None), 'zero-loop': (REFERENCE_SHAPE, 0)}
    points.update({f'{s}-mu{m}': (s, m) for s in SHAPES for m in MEANS_US})
    expected = {(w, b, p) for w in WORKLOADS for b in BLOCKS for p in points}
    indexed, registered = {}, {}
    for r in records:
        key = r['workload'], r['block_id'], r['point']
        _require(key in expected and key not in indexed, 'record grid identity')
        indexed[key] = r
        _require((r['shape'], r['mean_us']) == points[r['point']], 'record point identity')
        _require(r['correctness_certified'] is True and r['missing'] is False and r['unstable'] is False, 'record quality')
        _require(r['official_certification'] is False, 'record official_certification')
        samples = r['throughputs']
        _require(len(samples) == REPS and all(_number(v) > 0 for v in samples), 'record repetitions')
        _require(_number(r['median_tps']) > 0 and statistics.median(samples) == r['median_tps'], 'record median')
        if r['shape'] in SHAPES and r['mean_us'] in MEANS_US:
            _require(_number(r['backoff_call_count']) >= minimum, 'registered cell exposure')
            registered[r['workload'], r['block_id'], r['shape'], r['mean_us']] = r['median_tps']
    _require(set(indexed) == expected and len(registered) == 108, 'record grid completeness')
    differences = {w: [registered[w, b, CONTRAST_SHAPE, m] / registered[w, b, REFERENCE_SHAPE, m] - 1
                        for b in BLOCKS for m in MEANS_US] for w in WORKLOADS}
    rows = judgement['families']
    _require(len(rows) == FAMILIES, 'family count')
    _require({(f['workload'], f['shape']) for f in rows} == {(w, CONTRAST_SHAPE) for w in WORKLOADS}, 'family identities')
    families = []
    for w in WORKLOADS:
        f = copy.deepcopy(next(f for f in rows if f['workload'] == w))
        _require(f['pairs'] == PAIRS_PER_FAMILY and f['status'] == 'testable'
                 and f['reasons'] == [] and f['outcome'] == 'different', 'family outcome or pairs')
        _require(len(f['differences']) == PAIRS_PER_FAMILY and
                 all(_close(a, b) for a, b in zip(f['differences'], differences[w])), 'family differences order/value')
        raw = _number(f['raw_p'])
        _require(0 <= raw <= 1, 'raw p range')
        numerator = round(raw * ENUMERATION)
        _require(_close(raw * ENUMERATION, numerator, 1e-9), 'raw p denominator')
        _require(_number(f['holm_p']) <= ALPHA, 'Holm above alpha')
        total = sum(f['differences'])
        f.update(raw_p_numerator_2pow18=numerator, sum_of_differences=total,
                 direction='symmetric-modulo higher' if total > 0 else 'symmetric-modulo not higher')
        families.append(f)
    running = 0
    for i, f in enumerate(sorted(families, key=lambda f: f['raw_p'])):
        running = max(running, min(1, (FAMILIES-i) * f['raw_p']))
        _require(_close(f['holm_p'], running, 1e-15), 'Holm recalculation')
    rows = judgement['cell_effects']
    _require(len(rows) == CELLS, 'cell count')
    cell_keys = {(w, s, m) for w in WORKLOADS for s in SHAPES for m in MEANS_US}
    _require({(c['workload'], c['shape'], c['mean_us']) for c in rows} == cell_keys, 'cell identities')
    cells = []
    for w in WORKLOADS:
        for s in SHAPES:
            for i, m in enumerate(MEANS_US):
                c = copy.deepcopy(next(c for c in rows if (c['workload'], c['shape'], c['mean_us']) == (w, s, m)))
                _require(c['status'] == 'estimable' and c['equivalence_margin_pct'] == EQUIVALENCE_MARGIN_PCT, 'cell status/margin')
                if s == REFERENCE_SHAPE:
                    _require(c['effect'] == 0 and c['ci95_low'] == 0 and c['ci95_high'] == 0
                             and c['equivalence_relation'] == RELATIONS[0], 'constant cell zero reference')
                    block_values = [0.0] * len(BLOCKS)
                else:
                    block_values = [differences[w][b * len(MEANS_US) + i] for b in range(len(BLOCKS))]
                    mean = statistics.mean(block_values)
                    half = T975_DF2 * statistics.stdev(block_values) / math.sqrt(len(BLOCKS))
                    _require(_close(c['effect'], mean), 'cell effect recalculation')
                    _require(_close(c['ci95_low'], mean-half) and _close(c['ci95_high'], mean+half), 'cell interval recalculation')
                    _require(c['equivalence_relation'] == _relation(mean-half, mean+half), 'cell equivalence relation')
                c['block_effects'] = block_values
                cells.append(c)
    family_section = markdown.split('## Paired sign-flip permutation + Holm\n', 1)[1].split('\n## ', 1)[0]
    parsed = re.findall(r'^- (\S+) / symmetric-modulo: outcome=(\S+), pairs=(\d+), raw_p=(\S+), holm_p=(\S+)$', family_section, re.M)
    _require(len(parsed) == FAMILIES and {r[0] for r in parsed} == set(WORKLOADS), 'markdown family count')
    for w, outcome, pairs, raw, holm in parsed:
        f = next(f for f in families if f['workload'] == w)
        _require(outcome == f['outcome'] and int(pairs) == f['pairs']
                 and math.isclose(float(raw), f['raw_p'], rel_tol=1e-6)
                 and math.isclose(float(holm), f['holm_p'], rel_tol=1e-6), 'markdown Holm line')
    cell_section = markdown.split('## Cell effects and 95% paired-block intervals\n', 1)[1].split('\n## ', 1)[0]
    _require(len(re.findall(r'^- .* / .* / mu=.*', cell_section, re.M)) == CELLS, 'markdown cell count')
    summary = {name: sum(c['equivalence_relation'] == relation for c in cells)
               for name, relation in zip(('inside', 'overlaps', 'outside'), RELATIONS)}
    summary.update(indeterminate=0, estimable=len(cells))
    report = {k: submission[k] for k in ('request_id', 'nonce', 'phase', 'source_commit', 'prereg_commit', 'job_script_sha256')}
    report.update(submitted_epoch=REPORT_SUBMITTED_EPOCH, completed_epoch=REPORT_COMPLETED_EPOCH, driver_rc=0)
    return dict(repo_root=root, tracked_inputs=tracked,
                external_inputs=[dict(kind=k, path=p, sha256=EXTERNAL_SHA256[k]) for k, p in EXTERNAL_REL.items()],
                report=report, official_certification=False, ccbench_pin=source['pin'],
                analysis=dict(alpha=ALPHA, equivalence_margin_pct=EQUIVALENCE_MARGIN_PCT, critical_value=T975_DF2,
                              degrees_of_freedom=DF, pairs_per_family=PAIRS_PER_FAMILY, enumeration=ENUMERATION),
                families=families, cells=cells, summary=summary,
                crosschecks=dict(records=RECORDS, registered_records=len(registered), differences=True,
                                 intervals=True, holm=True, report_markdown=True),
                measurement_conditions=dict(environment='Pegasus compute nodes', threads=spec['execution']['threads'],
                                            protocol='silo', workloads=list(WORKLOADS), means_us=list(MEANS_US),
                                            reps=REPS, blocks=len(BLOCKS)))


def load_evidence(repo_root, evidence_root, *, expected_hashes=None):
    try:
        data = _authority_data(Path(repo_root).resolve(), expected_hashes)
        validate_external_sources(data, evidence_root)
        receipt, result = [_json(Path(evidence_root) / EXTERNAL_REL[k]) for k in EXTERNAL_REL]
        _require(receipt['schema_version'] == RECEIPT_SCHEMA and result['schema_version'] == JOB_RESULT_SCHEMA, 'external schema')
        _require(receipt['dry_run'] is False, 'receipt dry_run')
        for key in ('request_id', 'nonce', 'phase', 'source_commit', 'prereg_commit', 'job_script_sha256'):
            _require(receipt[key] == data['report'][key], f'receipt identity {key}')
        # The job-result schema has no prereg_commit, job_script_sha256 or dry_run.
        for key in ('request_id', 'nonce', 'phase', 'source_commit'):
            _require(result[key] == data['report'][key], f'job result identity {key}')
        _require(result['driver_rc'] == 0, 'job result driver_rc')
        _require(_number(result['completed_epoch']) > _number(receipt['submitted_epoch']), 'external chronology')
        _require(receipt['submitted_epoch'] == REPORT_SUBMITTED_EPOCH and result['completed_epoch'] == REPORT_COMPLETED_EPOCH, 'external pinned epochs')
        return data
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f'invalid evidence: {exc}') from exc


def _figure_number(prefix):
    match = re.match(r'fig([0-9]+)_', Path(prefix).name)
    _require(match is not None, 'output prefix basename must start with fig<N>_')
    return match.group(1)


def _caption(data, prefix):
    families = '; '.join(
        f"{f['workload']}: {f['outcome']}, raw p = {f['raw_p_numerator_2pow18']}/2^18 = {f['raw_p']:.17g}, "
        f"Holm p = {f['holm_p']:.17g}, {f['pairs']} pairs, sum of paired effects {f['sum_of_differences']:+.17g} "
        f"({f['direction']})" for f in data['families'])
    overlaps = []
    for w in data['measurement_conditions']['workloads']:
        means = [str(c['mean_us']) for c in data['cells'] if c['workload'] == w and c['equivalence_relation'] == RELATIONS[1]]
        if means:
            overlaps.append(w + ' mu ' + ' and '.join(means))
    summary = data['summary']
    conditions, report = data['measurement_conditions'], data['report']
    return (f"Figure {_figure_number(prefix)}. B-10 waiting-shape grid, preregistered contrast constant vs symmetric-modulo. "
            f"{families}. Cell effects and 95% paired-block intervals: {summary['estimable']} estimable, "
            f"inside {summary['inside']}, overlaps {summary['overlaps']}, outside {summary['outside']}, "
            f"indeterminate {summary['indeterminate']}; {sum(c['effect'] < 0 for c in data['cells'])} negative point estimates "
            f"and {sum(c['ci95_low'] > 0 for c in data['cells'])} positive interval lower bounds. "
            f"Boundary overlaps: {', '.join(overlaps) or 'none'}. "
            "Constant cells are constructional references at zero with intervals [0, 0]; gray ticks show the three block-level paired effects. "
            f"Conditions: {conditions['environment']}, {conditions['threads']} threads, {conditions['protocol']}, "
            f"YCSB {' / '.join(conditions['workloads'])}, commanded mean wait mu "
            f"{', '.join(map(str, conditions['means_us']))} us, {conditions['reps']} reps x {conditions['blocks']} blocks, "
            f"CCBench pin {data['ccbench_pin']}, report request {report['request_id']}, "
            f"preregistration commit {report['prereg_commit'][:9]}, source commit {report['source_commit'][:9]}. "
            + ' '.join(CAPTION_LITERALS))


def _artist_series(data):
    return [dict(workload=c['workload'], shape=c['shape'], mean_us=c['mean_us'],
                 x=100*c['effect'], low=100*c['ci95_low'], high=100*c['ci95_high'],
                 y=list(MEANS_US).index(c['mean_us']),
                 block_x=[100*v for v in c['block_effects']],
                 marker='o' if c['shape'] == REFERENCE_SHAPE or c['equivalence_relation'] != RELATIONS[1] else 's')
            for c in data['cells']]


def make_figure(data):
    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 8, 'axes.labelsize': 9, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.subplots_adjust(left=.055, right=.985, top=.73, bottom=.28, wspace=.22)
    series = _artist_series(data)
    limit = 1.12 * max(EQUIVALENCE_MARGIN_PCT, *(abs(s[k]) for s in series for k in ('low', 'high')))
    for ax, family in zip(axes, data['families']):
        ax.axvspan(-EQUIVALENCE_MARGIN_PCT, EQUIVALENCE_MARGIN_PCT, color='#d9ead3', zorder=0)
        ax.axvline(0, color='#666666', linewidth=.8, zorder=1)
        for index, row in enumerate(series):
            if row['workload'] != family['workload']:
                continue
            if row['shape'] == REFERENCE_SHAPE:
                point, = ax.plot([row['x']], [row['y']], 'o', color='#244c70', markerfacecolor='white', markersize=6, zorder=5)
            else:
                ticks, = ax.plot(row['block_x'], [row['y']]*3, '|', color='#777777', markersize=7, zorder=2)
                ticks.set_gid(f'blocks-{index}')
                bars = ax.errorbar([row['x']], [row['y']],
                                   xerr=[[row['x']-row['low']], [row['high']-row['x']]],
                                   fmt=row['marker'], color='#244c70', capsize=3, markersize=5, zorder=3)
                point = bars.lines[0]
                bars.lines[2][0].set_gid(f'interval-{index}')
            point.set_gid(f'cell-{index}')
        ax.set_xlim(-limit, limit)
        ax.set_xticks([v for v in ax.get_xticks() if -limit <= v <= limit])
        ax.set_ylim(-.6, 5.6)
        ax.set_yticks(range(6), [str(m) for m in MEANS_US])
        ax.invert_yaxis()
        ax.set_ylabel('Commanded mean wait (µs)')
        ax.set_xlabel('Paired relative effect (%)')
        ax.set_title(f"{family['workload']}: symmetric-modulo vs constant — {family['outcome']}\n"
                     f"Holm p = {family['holm_p']:.4g} (raw p = {family['raw_p_numerator_2pow18']}/2^18 = {family['raw_p']:.3g})\n"
                     f"{family['pairs']} pairs, sum of paired effects {family['sum_of_differences']:+.4f}", pad=12)
    fig.suptitle(f"B-10 waiting-shape grid, report {data['report']['request_id']}\n"
                 "Preregistered contrast constant vs symmetric-modulo (3 families x 18 pairs, 36 cell effects)", y=.965, fontsize=12)
    handles = [Line2D([], [], marker='o', color='#244c70', label='Cell effect + 95% interval'),
               Line2D([], [], marker='s', color='#244c70', linestyle='none', label='Overlaps boundary'),
               Line2D([], [], marker='o', color='#244c70', markerfacecolor='white', linestyle='none', label='Constant reference'),
               Line2D([], [], marker='|', color='#777777', linestyle='none', label='Block-level paired effects'),
               Patch(facecolor='#d9ead3', label='+/-3.0% margin')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .135), ncol=5, frameon=False)
    cond = data['measurement_conditions']
    fig.text(.5, .09, f"{cond['environment']}; {cond['threads']} threads; {cond['protocol']}; YCSB write-heavy / balanced / read-heavy; "
             f"{cond['reps']} reps x {cond['blocks']} blocks; CCBench {data['ccbench_pin']}; official_certification: false", ha='center', fontsize=9)
    fig.text(.5, .045, 'Intervals inside the band are not equivalence; no per-cell significance is decided.', ha='center', fontsize=9)
    fig._b10_artist_series = series
    return fig, axes



CAPTION_LITERALS = ("Each family's outcome is the preregistered procedure's classification and is not a research verdict.", 'Intervals lying inside the +/-3.0% margin are reported as the position of the interval and are not a finding of equivalence; no equivalence test was performed.', 'Per-cell intervals are descriptive and no per-cell significance decision is made; the only tests are the three family-level permutation tests with Holm adjustment.', 'The static right-tail cohorts (separate preregistration, grid and driver) are neither pooled nor compared with this grid.', 'official_certification is false; these performance values are not a basis for adopting a variant.', 'Direction and effect sizes are stated for this one contrast only; nothing is claimed about waiting-shape effects in general, about binary, about a dose response of dispersion, or about a general separation of waiting shape from waiting amount.', 'Correctness is recorded from separate trace-enabled runs (135 of 135 cells certified) and is not a performance certification.', 'The three workloads ran as separate jobs on different days and driver versions; absolute throughput is not compared across workloads, and no mechanism is claimed for the direction.')


def _intersection(left, right):
    return max(0, min(left.x1, right.x1) - max(left.x0, right.x0)) * max(0, min(left.y1, right.y1) - max(left.y0, right.y0))


def _contains(outer, inner):
    return inner.x0 >= outer.x0 - 1 and inner.y0 >= outer.y0 - 1 and inner.x1 <= outer.x1 + 1 and inner.y1 <= outer.y1 + 1


def check_figure_layout(fig, axes):
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    plot_axes = list(np.asarray(axes).flat)
    if len(plot_axes) != 3 or set(plot_axes) != set(fig.axes):
        raise FigureLayoutError("production layout must contain exactly three axes")
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


def validate_repo_closure(provenance, repo_root, *, expected_hashes=None):
    """Rebuild every projection using only tracked inputs and external byte pins."""
    try:
        root = Path(repo_root).resolve()
        data = _authority_data(root, expected_hashes)
        outputs = provenance['outputs']
        _require(len(outputs) == 2 and [Path(r['path']).suffix for r in outputs] == ['.png', '.pdf'], 'output paths mismatch')
        prefix = Path(outputs[0]['path']).with_suffix('')
        _require(Path(outputs[1]['path']).with_suffix('') == prefix, 'output prefix mismatch')
        for row in outputs:
            _require(_sha256(root / row['path']) == row['sha256'], 'output closure mismatch')
        argv = provenance['reproduction']['argv']
        _require(len(argv) == 7 and argv[:3] == ['python3', GENERATOR_PATH, '--repo-root']
                 and argv[4] == '--evidence-root', 'reproduction argv mismatch')
        _require(Path(argv[3]).is_absolute() and Path(argv[5]).is_absolute(), 'reproduction roots')
        _require(argv[6] == str(prefix), 'reproduction output prefix')
        _digest(provenance['generator']['sha256'])
        # A source comment is not an input-data change; retain the generation-time hash.
        # Do not read the live generator (or the evidence root) during repo closure.
        expected = {
            **{k: copy.deepcopy(v) for k, v in data.items() if k != 'repo_root'},
            'schema': SCHEMA,
            'generated_utc': provenance['generated_utc'],
            'generator': dict(path=GENERATOR_PATH, sha256=provenance['generator']['sha256']),
            'outputs': [dict(path=r['path'], sha256=_sha256(root/r['path'])) for r in outputs],
            'artist_series': _artist_series(data),
            'caption': _caption(data, prefix),
            'reproduction': dict(cwd='repository-root', argv=argv, command=shlex.join(argv)),
        }
        _require(set(provenance) == set(expected), 'provenance key set mismatch')
        for key in expected:
            _require(provenance[key] == expected[key], f'{key} closure mismatch')
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f'invalid repo closure: {exc}') from exc


def validate_external_sources(provenance, evidence_root):
    try:
        rows = provenance['external_inputs']
        _require(rows == [dict(kind=k, path=p, sha256=EXTERNAL_SHA256[k]) for k, p in EXTERNAL_REL.items()], 'external input set mismatch')
        for row in rows:
            _require(_sha256(Path(evidence_root) / row['path']) == row['sha256'], 'external SHA-256 mismatch')
    except (OSError, KeyError, TypeError, ValueError) as exc:
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
                                      artist_series=fig._b10_artist_series)
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
