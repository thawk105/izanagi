#!/usr/bin/env python3
"""Render recorded paper-story statuses without recomputing judgments."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from matplotlib.transforms import Bbox
import numpy as np

GENERATOR = Path(__file__).resolve()
GENERATOR_PATH = "tools/plotting/plot_k2_loop_flow.py"
REPO_ROOT = GENERATOR.parents[2]
DEFAULT_FLOW = "tools/plotting/k2_loop_flow_2026-09-20.json"
SOURCE = "docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md"
LANES = "parent planner coder proposal evaluation critic".split()
COLUMNS = ["round-1", "round-2", "after-round-2", "round-3"]
ROLE_NAMES = ["planner-v4", "coder-v4-autonomous-k2", "critic"]
PLANNER_KEYS = "current_perf leading_indicators whiteboard knowledge_input".split()
CODER_KEYS = "baseline planner_direction whiteboard knowledge_input leakproof_context".split()
DIAGNOSIS_KEY = "k2_critic_diagnosis"
DIAGNOSIS_FIELDS = "attribution recommend avoid uncertainty data_boundary source_sha256".split()
class FigureDataError(ValueError):
    """Input violates the recorded-status schema."""


class FigureLayoutError(FigureDataError):
    """Rendered artists cannot be published safely."""


def _require(condition, message):
    if not condition:
        raise FigureDataError(message)


def _keys(value, expected):
    _require(type(value) is dict and set(value) == set(expected.split()), "key set mismatch")


def _string(value):
    _require(type(value) is str and bool(value.strip()), "nonempty string required")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise FigureDataError(f"non-finite JSON constant: {value}")


def check_display_text(value, declared_ids, job_ids=()):
    """A small lexical contract, not a natural-language quantity classifier."""
    value = unicodedata.normalize("NFKC", _string(value))
    for job in job_ids:
        value = re.sub(r'(?<!\w)job '+re.escape(job)+r'(?![\w.])', 'job identifier', value)
    words = ("tps μs us ms ns sec seconds percent zero one two three four five six "
             "seven eight nine ten eleven twelve twenty thirty hundred thousand million "
             "dozen once twice thrice").split()
    _require(not re.search(r"[=%]|\b(?:" + "|".join(words) + r")\b", value, re.I),
             "quantity in free text")
    for token in re.split(r"[\s;,/]+", value):
        _require(not any(c.isdigit() for c in token) or token in declared_ids,
                 f"undeclared numeric token: {token}")


def _anchor(anchor, source):
    _string(anchor)
    if match := re.fullmatch(r"§2\.2 巡 ([1-9][0-9]*)", anchor):
        pattern = rf"^#### 巡 {match[1]} "
    elif match := re.fullmatch(r"§([0-9]+)\.([0-9]+)", anchor):
        pattern = rf"^### {match[1]}\.{match[2]} "
    elif match := re.fullmatch(r"§([0-9]+)", anchor):
        pattern = rf"^## {match[1]}\. "
    else:
        raise FigureDataError(f"invalid anchor: {anchor}")
    _require(len(re.findall(pattern, source, re.M)) == 1,
             f"anchor must match exactly one line: {anchor}")


def _enum(value, choices):
    _require(type(value) is str and value in choices, f"invalid enum: {value}")


def _date(value):
    _require(type(value) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value), "ISO date required")
    datetime.date.fromisoformat(value)


def _bool(value):
    _require(type(value) is bool, "bool required")


def _tools_none(raw):
    lines = raw.decode('utf-8').splitlines()
    _require(lines and lines[0] == '---', 'missing role frontmatter')
    _require('---' in lines[1:], 'unclosed role frontmatter')
    front = lines[1:lines.index('---', 1)]
    matches = [line[6:].strip() for line in front if line.startswith('tools:')]
    _require(len(matches) == 1, 'exactly one tools: line required')
    values = json.loads(matches[0], parse_constant=_constant)
    _require(type(values) is list and all(type(v) is str and v for v in values), 'tools array required')
    return not values


def load_flow(repo_root=REPO_ROOT, flow=DEFAULT_FLOW):
    """Validate the transcription, retaining each input's single byte read."""
    try:
        root = Path(repo_root).resolve()
        path = (root / flow).resolve()
        raw = path.read_bytes()
        d = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        _keys(d, 'schema figure_created caption_source reference_ids roles lanes knowledge diagnosis_fields planner_keys coder_keys columns arrows stock_control discipline6')
        _require(d['schema'] == 'izanagi-k2-loop-flow/v1', 'schema mismatch')
        _date(d['figure_created'])
        _require(d['caption_source'] == SOURCE, 'caption_source path mismatch')
        source_raw = (root / SOURCE).read_bytes()
        source = source_raw.decode('utf-8')
        inputs = [('flow', os.path.relpath(path, root), raw), ('caption_source', SOURCE, source_raw)]
        refs = d['reference_ids']
        _require(type(refs) is list and all(type(x) is str and re.fullmatch(r'[A-Za-z]+[0-9]*-?[0-9]+[a-z]?', x) for x in refs), 'reference_ids format')
        _require(len(refs) == len(set(refs)), 'duplicate reference_ids')
        for field, expected in [('planner_keys', PLANNER_KEYS), ('coder_keys', CODER_KEYS), ('diagnosis_fields', DIAGNOSIS_FIELDS)]:
            _require(d[field] == expected, field+' mismatch')
        free, instances, jobs = [], set(), set()

        def descriptive(obj, keys):
            _keys(obj, keys)
            for field in ('label', 'sublabel', 'definition', 'discipline6', 'attribution', 'recommend'):
                if field in obj:
                    free.append(obj[field])
            if 'source_anchor' in obj:
                _anchor(obj['source_anchor'], source)

        _require(type(d['roles']) is list and len(d['roles']) == 3, 'three roles required')
        for r, ident, name in zip(d['roles'], ['planner', 'coder', 'critic'], ROLE_NAMES):
            descriptive(r, 'id name definition_path tools_none label sublabel source_anchor')
            _require(r['id'] == ident and r['name'] == name, 'role order/name mismatch')
            _require(r['definition_path'] == f'.claude/agents/{name}.md', 'definition_path mismatch')
            _bool(r['tools_none'])
            role_raw = (root / r['definition_path']).read_bytes()
            _require(r['tools_none'] == _tools_none(role_raw), 'tools_none mismatch')
            inputs.append(('role_definition', r['definition_path'], role_raw))
        _require(type(d['lanes']) is list and len(d['lanes']) == 6, 'six lanes required')
        for lane, ident in zip(d['lanes'], LANES):
            descriptive(lane, 'id label sublabel source_anchor')
            _require(lane['id'] == ident, 'lane order mismatch')
            for role in d['roles']:
                if role['id'] == ident:
                    _require(all(lane[k] == role[k] for k in ('label', 'sublabel')), 'role lane mismatch')
        for field in ('knowledge', 'stock_control'):
            descriptive(d[field], 'label sublabel source_anchor')
        descriptive(d['discipline6'], 'label definition')
        _require(type(d['columns']) is list and len(d['columns']) == 4, 'four columns required')
        for i, col in enumerate(d['columns']):
            descriptive(col, 'id kind label date_proposal date_evaluation source_anchor cells')
            _require(col['id'] == COLUMNS[i], 'column order mismatch')
            _enum(col['kind'], ('round', 'not-a-round'))
            _require((col['kind'] == 'not-a-round') == (i == 2), 'column kind mismatch')
            _date(col['date_proposal'])
            if col['date_evaluation'] is not None:
                _date(col['date_evaluation'])
            cells = col['cells']
            _keys(cells, ' '.join(LANES))
            descriptive(cells['parent'], 'sublabel has_diagnosis')
            _bool(cells['parent']['has_diagnosis'])
            _require(cells['parent']['has_diagnosis'] == (i == 3), 'diagnosis column mismatch')
            descriptive(cells['planner'], 'instance direction magnitude discipline6')
            _enum(cells['planner']['direction'], ('increase', 'decrease', 'explore_both'))
            _enum(cells['planner']['magnitude'], ('small', 'medium', 'large'))
            descriptive(cells['coder'], 'instance value discipline6')
            descriptive(cells['proposal'], 'instance value known_value evaluated sublabel')
            for role in ('coder', 'proposal'):
                value = cells[role]['value']
                _require(type(value) is int and 1 <= value <= 1000, 'value must be int in range')
            _require(cells['coder']['value'] == cells['proposal']['value'], 'coder/proposal value mismatch')
            for k in ('known_value', 'evaluated'):
                _bool(cells['proposal'][k])
            evaluated = cells['evaluation'] is not None
            _require(cells['proposal']['evaluated'] == evaluated, 'evaluated mismatch')
            _require(evaluated == (col['kind'] == 'round') and evaluated == (cells['critic'] is not None)
                     and evaluated == (col['date_evaluation'] is not None), 'evaluation kind mismatch')
            if evaluated:
                e = cells['evaluation']
                descriptive(e, 'job refused_jobs verdict certified anomalies_none stop sublabel')
                _enum(e['verdict'], ('serializable',))
                _enum(e['stop'], ('continue',))
                _require(e['certified'] is True and e['anomalies_none'] is True, 'correctness flags must be true')
                _require(type(e['refused_jobs']) is list, 'refused_jobs array required')
                for job in [e['job'], *e['refused_jobs']]:
                    _require(type(job) is str and re.fullmatch(r'[0-9]+', job), 'job digits required')
                    _require(job not in jobs, 'duplicate job')
                    jobs.add(job)
                descriptive(cells['critic'], 'instance attribution recommend discipline6')
            for role in ('planner', 'coder', 'proposal', 'critic'):
                if cells[role] is None:
                    continue
                instance = cells[role]['instance']
                _require(type(instance) is str and re.fullmatch(role+r'-[1-9][0-9]*', instance), 'invalid instance')
                _require(instance not in instances, 'duplicate instance')
                instances.add(instance)
        endpoints = {c+'.'+lane for c in COLUMNS for lane in LANES}
        _require(type(d['arrows']) is list and d['arrows'], 'arrows array required')
        ids = set()
        for a in d['arrows']:
            descriptive(a, 'id kind from to label')
            ident = _string(a['id'])
            _require(ident not in ids, 'duplicate arrow id')
            ids.add(ident)
            _enum(a['kind'], ('measurement-reflux', 'diagnosis-reflux', 'absent'))
            _require(type(a['from']) is str and a['from'] in endpoints, 'arrow from missing')
            _require((a['kind'] == 'absent' and a['to'] is None) or
                     (type(a['to']) is str and a['to'] in endpoints), 'arrow to missing')
        for value in free:
            check_display_text(value, set(refs) | instances, jobs)
        tokens = {t for value in free for t in re.split(r'[\s;,/]+', value)}
        _require(set(refs) <= tokens, 'unused reference_ids')
        return dict(flow=d, repo_root=root, input_bytes=inputs)
    except FigureDataError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        raise FigureDataError(f'malformed flow: {exc}') from exc


def _figure_number(prefix):
    match = re.match(r'^fig([0-9]+[a-z]*)_', Path(prefix).name)
    _require(match is not None, 'output prefix basename must start with fig<N><letters>_')
    return match[1] if match else Path(prefix).name


def _normalized(parts):
    return ' '.join(' '.join(parts).split())


def _display_items(d):
    """All displayed strings, including fixed explanatory text, from typed fields."""
    rows = []
    def add(ident, kind, *parts):
        rows.append(dict(id=ident, kind=kind, text=_normalized(parts)))
    add('title', 'title', 'K2 manual loop: data flow over three recorded rounds (schematic; no performance values)')
    add('subtitle', 'subtitle', Path(d['caption_source']).name, '|', d['figure_created'])
    add('knowledge', 'knowledge', d['knowledge']['label'], d['knowledge']['sublabel'])
    roles = {r['id']:r for r in d['roles']}
    for lane in d['lanes']:
        add('lane-'+lane['id'], 'lane', roles[lane['id']]['name'] if lane['id'] in roles else lane['label'], lane['sublabel'])
    for col in d['columns']:
        cid = col['id']
        add(cid, 'column', col['label'], 'proposal:', col['date_proposal'], 'evaluation:', col['date_evaluation'] or 'none')
        for lane, cell in col['cells'].items():
            parts = []
            if lane == 'parent':
                for role in ('planner','coder'):
                    parts += [role+':', ', '.join(d[role+'_keys'])]
                    if cell['has_diagnosis']:
                        parts += ['+ '+DIAGNOSIS_KEY]
                parts += [cell['sublabel']]
            elif cell is None:
                parts = ['not evaluated' if lane == 'evaluation' else 'no critic']
            elif lane == 'planner':
                parts = [cell['instance'], cell['direction']+' / '+cell['magnitude']]
            elif lane == 'coder':
                parts = [cell['instance'], f"value {cell['value']}"]
            elif lane == 'proposal':
                parts = [cell['instance'], f"value {cell['value']}", 'known value' if cell['known_value'] else 'outside the known set',
                         'evaluated' if cell['evaluated'] else 'not evaluated', cell['sublabel']]
            elif lane == 'evaluation':
                parts = ['job '+cell['job']]
                if cell['refused_jobs']:
                    parts += ['refused at preflight: '+', '.join('job '+j for j in cell['refused_jobs'])]
                parts += ['verdict '+cell['verdict']+'; certified; no anomaly; stop: '+cell['stop'], cell['sublabel']]
            else:
                parts = [cell['instance'], cell['attribution'], cell['recommend']]
            add(cid+'.'+lane, 'cell', *parts)
    for a in d['arrows']:
        extra = (DIAGNOSIS_KEY+': '+', '.join(d['diagnosis_fields'])) if a['kind']=='diagnosis-reflux' else ''
        add('arrow-'+a['id'], 'arrow', a['id']+':', a['from'], '→', a['to'] or 'no destination', a['label'], extra)
    add('stock_control', 'stock_control', d['stock_control']['label'], d['stock_control']['sublabel'])
    add('legend-arrows', 'legend', 'Solid: measurement reflux; dashed: diagnosis reflux; dotted with cross: absent path; thin: within-column flow; dashed box: not a round.')
    add('legend-r6', 'legend', 'R6: no instruction-like content (self-reported).', d['discipline6']['label']+':', d['discipline6']['definition'])
    add('footnote-source', 'footnote', 'Read from the frozen results note', Path(d['caption_source']).name+'; no performance values are drawn and the three runs are not compared.')
    add('footnote-certified', 'footnote', 'Certified means the trace-enabled verify run found the trace serializable with no anomaly; it is not a performance certification.')
    add('footnote-discipline', 'footnote', 'Discipline-six marks are role self-reports, not a mechanical gate; causal effects of knowledge or diagnosis are not claimed.')
    return rows



def make_figure(data):
    """A fixed grid with dedicated routing gutters and label tracks; never shrink."""
    d = data['flow']
    fig = plt.figure(figsize=(16, 11), dpi=200)
    layout = dict(regions={}, owners={}, siblings={}, items=[], markers=[], arrows=[])
    renderer = fig.canvas.get_renderer()
    rows = {r['id']:r for r in _display_items(d)}

    def region(key, bounds, parent='figure', dashed=False, color=None):
        layout['regions'][key] = Bbox.from_bounds(*bounds)
        layout['siblings'].setdefault(parent, []).append(key)
        if color:
            fig.add_artist(Rectangle(bounds[:2], *bounds[2:], transform=fig.transFigure,
                                    facecolor=color, edgecolor='#aaaaaa', linewidth=.5,
                                    linestyle='--' if dashed else '-'))

    def label(key, bounds, size=7.5, pad=.004, parent='figure', dashed=False, color=None):
        region(key, bounds, parent, dashed, color)
        x,y,w,h = bounds
        prop = FontProperties(family='DejaVu Sans', size=size)
        line, lines = '', []
        for word in rows[key]['text'].split():
            candidate = (line+' '+word).strip()
            if line and renderer.get_text_width_height_descent(candidate, prop, False)[0] > (w-2*pad)*fig.bbox.width:
                lines.append(line)
                line = word
            else:
                line = candidate
        artist = fig.text(x+pad, y+h-pad, '\n'.join(lines+[line]), va='top',
                          fontproperties=prop, linespacing=1.08)
        layout['owners'][artist] = key
        layout['items'].append(dict(id=key, kind=rows[key]['kind'], texts=[artist]))
        return artist

    def arrow(ident, kind, points):
        style = {'flow':('-',.7,'#777777'), 'measurement-reflux':('-',1.3,'#28628a'),
                 'diagnosis-reflux':('--',1.3,'#804b8c'), 'absent':(':',1,'#999999')}[kind]
        xs,ys = zip(*points)
        artist = Line2D(xs,ys, transform=fig.transFigure, linestyle=style[0], linewidth=style[1], color=style[2])
        fig.add_artist(artist)
        # Arrowheads/crosses are markers, so they too participate in the text check.
        dx,dy = np.subtract(points[-1], points[-2])
        shape = 'x' if kind=='absent' else ('>' if dx>0 else '<') if abs(dx)>abs(dy) else ('^' if dy>0 else 'v')
        head = Line2D([xs[-1]], [ys[-1]], transform=fig.transFigure, linestyle='none',
                      marker=shape, markersize=3, color=style[2])
        fig.add_artist(head)
        layout['markers'].append((head, 'canvas', False))
        layout['arrows'].append(dict(id=ident, kind=kind, artist=artist))

    layout['regions']['canvas'] = Bbox.from_bounds(0,0,1,1)
    label('title', (.02,.957,.96,.033), 13)
    label('subtitle', (.02,.936,.96,.02), 8)
    label('knowledge', (.02,.895,.96,.038), 8, color='#e7f0e7')
    # Extra width for the unevaluated column keeps the typed keys readable.
    xs = [.195,.395,.595,.795]
    width = .172
    spans = [( .666,.159),(.614,.043),(.568,.037),(.472,.087),(.367,.096),(.282,.076)]
    for lane,(y,h) in zip(d['lanes'],spans):
        label('lane-'+lane['id'], (.02,y,.166,h), 7.5, color='#f2f2f2')
    for ci,col in enumerate(d['columns']):
        x = xs[ci]
        pale = col['kind']=='not-a-round'
        label(col['id'], (x,.839,width,.049), 8, dashed=pale, color='#f6f6f6' if pale else '#e3edf5')
        for li,(lane,(y,h)) in enumerate(zip(LANES,spans)):
            key = col['id']+'.'+lane
            bounds = (x,y,width,h)
            if ci == 3 and lane == 'evaluation':
                bounds = (x,y+.032,width,h-.032)
            label(key, bounds, 7.5, dashed=pale, color='#fafafa' if pale else '#ffffff')
            cell = col['cells'][lane]
            if lane in ('planner','coder','critic') and cell is not None:
                marker = Line2D([x+width-.008],[y+.009],transform=fig.transFigure,
                                marker='p',markersize=4,linestyle='none',color='#476b55')
                fig.add_artist(marker)
                layout['markers'].append((marker,key,False))
            if li and not (pale and li>=4):
                prev_y = spans[li-1][0]
                arrow('flow-'+key,'flow',[(x+width/2,prev_y-.0015),(x+width/2,y+h+.0015)])
        arrow('knowledge-'+col['id'],'flow',[(x-.012,.895),(x-.012,.827),
              (x+width/2,.827),(x+width/2,.826)])
    # Cross-column paths turn upward through blank gutters. The label bank
    # below the grid keeps the long typed diagnosis fields off the arrow lines.
    for ai,a in enumerate(d['arrows']):
        key='arrow-'+a['id']
        top=.274-ai*.022
        if a['kind']=='diagnosis-reflux':
            label(key,(.025,top-.019,.945,.019),6.6,pad=.001)
        else:
            label(key,(.025,top-.018,.945,.018),7,pad=.001)
        source=layout['regions'][a['from']]
        start=(source.x1,source.y0+.007)
        gutter=source.x1+.004+ai*.0007
        track=.830+ai*.001
        if a['to'] is not None:
            dest=layout['regions'][a['to']]
            left=dest.x0-.005-ai*.0007
            points=[start,(gutter,start[1]),(gutter,track),(left,track),(left,dest.y1-.002-ai*.004),(dest.x0-.001,dest.y1-.002-ai*.004)]
        else:
            points=[start,(gutter,start[1]),(gutter,track)]
        arrow(a['id'],a['kind'],points)
    label('stock_control',(.795,.367,.172,.03),7,pad=.002,dashed=True,color='#fff7eb')
    # The stock box occupies the reserved lower part of the evaluation lane.
    label('legend-arrows',(.02,.101,.96,.019),7,pad=.001)
    label('legend-r6',(.02,.067,.96,.033),7,pad=.001)
    for key,y in [('footnote-source',.046),('footnote-certified',.028),('footnote-discipline',.010)]:
        label(key,(.02,y,.96,.017),7,pad=.001)
    # Canonical order is independent of the order artists were constructed.
    layout['items'].sort(key=lambda r:list(rows).index(r['id']))
    return fig, layout


def _segment_intersects_box(start, end, box):
    """Closed segment/rectangle intersection by slab clipping (including tangency)."""
    low, high = 0., 1.
    for a,b,minimum,maximum in zip(start,end,(box.x0,box.y0),(box.x1,box.y1)):
        delta=b-a
        if delta == 0:
            if not minimum <= a <= maximum:
                return False
        else:
            near,far=sorted(((minimum-a)/delta,(maximum-a)/delta))
            low,high=max(low,near),min(high,far)
            if low>high:
                return False
    return True


def _intersection(left, right):
    return max(0, min(left.x1, right.x1)-max(left.x0, right.x0)) * max(0, min(left.y1, right.y1)-max(left.y0, right.y0))


def _contains(outer, inner):
    return inner.x0 >= outer.x0-1 and inner.y0 >= outer.y0-1 and inner.x1 <= outer.x1+1 and inner.y1 <= outer.y1+1


def check_figure_layout(fig, layout):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    regions = {key: box.transformed(fig.transFigure) for key, box in layout["regions"].items()}

    def positive(box):
        if not np.isfinite(box.extents).all() or box.width <= 0 or box.height <= 0:
            raise FigureLayoutError("nonpositive or nonfinite bbox")

    boxes = []
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        positive(box)
        owner = layout["owners"].get(artist)
        if owner not in regions:
            raise FigureLayoutError("unregistered text")
        if not _contains(fig.bbox, box) or not _contains(regions[owner], box):
            raise FigureLayoutError(f"text escape: {artist.get_text()!r}")
        boxes.append((artist, box))
    for (left, box), (right, other) in itertools.combinations(boxes, 2):
        if _intersection(box, other) > 1:
            raise FigureLayoutError(f"text overlap: {left.get_text()!r} / {right.get_text()!r}")
    for parent, keys in layout["siblings"].items():
        for key in keys:
            positive(regions[key])
            if not _contains(regions.get(parent, fig.bbox), regions[key]):
                raise FigureLayoutError(f"region escape: {key}")
        for left, right in itertools.combinations(keys, 2):
            if _intersection(regions[left], regions[right]) > 1:
                raise FigureLayoutError(f"sibling overlap: {left} / {right}")
    for artist, owner, neutral in layout["markers"]:
        box = artist.get_window_extent(renderer)
        if not neutral:
            positive(box)
        elif not np.isfinite(box.extents).all() or box.width <= 0:
            raise FigureLayoutError("invalid neutral line")
        box = box.padded(fig.dpi/72)
        if not _contains(regions[owner], box):
            raise FigureLayoutError("marker escape")
        if any(_intersection(box, other) > 1 for _, other in boxes):
            raise FigureLayoutError("marker/text overlap")
    for left, right in itertools.combinations(layout['markers'], 2):
        if _intersection(left[0].get_window_extent(renderer), right[0].get_window_extent(renderer)) > 1:
            raise FigureLayoutError('marker overlap')
    for arrow in layout['arrows']:
        artist = arrow['artist']
        points = artist.get_transform().transform(artist.get_xydata())
        if not np.isfinite(points).all():
            raise FigureLayoutError('nonfinite arrow')
        for start,end in zip(points,points[1:]):
            for text,box in boxes:
                if _segment_intersects_box(start,end,box):
                    raise FigureLayoutError(f"arrow crossing text: {arrow['id']} / {text.get_text()!r}")


def _drawn_items(data, layout):
    actual = [dict(id=r['id'],kind=r['kind'],text=_normalized([t.get_text() for t in r['texts'] if t.get_visible()])) for r in layout['items']]
    _require(actual == _display_items(data['flow']), 'drawn_items disagree with flow')
    return actual


def _caption(data, number):
    d=data['flow']
    return CAPTION.format(number=number, basename=Path(d['caption_source']).name,
                          planner_keys=', '.join(d['planner_keys']), coder_keys=', '.join(d['coder_keys']),
                          diagnosis_key=DIAGNOSIS_KEY, diagnosis_fields=', '.join(d['diagnosis_fields']))


def build_provenance(data, layout, outputs, argv, *, hash_paths=None, figure_number='12'):
    hashes = outputs if hash_paths is None else hash_paths
    inputs = [dict(kind=kind,path=path,sha256=hashlib.sha256(raw).hexdigest()) for kind,path,raw in data['input_bytes']]
    by_path = {r['path']:r['sha256'] for r in inputs}
    return dict(schema='izanagi-k2-loop-flow-figure-provenance/v1',
                generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                figure_created=data['flow']['figure_created'],
                caption_source=dict(path=SOURCE,sha256=by_path[SOURCE]), inputs=inputs,
                generator=dict(path=GENERATOR_PATH,sha256=hashlib.sha256(GENERATOR.read_bytes()).hexdigest()),
                outputs=[dict(path=os.path.relpath(p,data['repo_root']),sha256=hashlib.sha256(Path(h).read_bytes()).hexdigest()) for p,h in zip(outputs,hashes)],
                drawn_items=_drawn_items(data,layout), arrows=data['flow']['arrows'],
                roles=[dict(name=r['name'],definition_path=r['definition_path'],tools_none=r['tools_none'],sha256=by_path[r['definition_path']]) for r in data['flow']['roles']],
                caption=_caption(data,figure_number),argv=list(argv),versions=dict(matplotlib=matplotlib.__version__,numpy=np.__version__))




def _destinations(prefix):
    paths = [Path(f"{prefix}{suffix}") for suffix in (".png", ".pdf", ".provenance.json")]
    _require(not any(os.path.lexists(p) for p in paths), "output already exists")
    return paths


def _publish_outputs(fig, layout, prefix, data, argv):
    prefix = Path(prefix)
    number = _figure_number(prefix)
    destinations = _destinations(prefix)
    check_figure_layout(fig, layout)
    _drawn_items(data, layout)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    temporary, published = [], []
    try:
        for suffix in (".png", ".pdf", ".provenance.json"):
            fd, name = tempfile.mkstemp(prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent)
            os.close(fd)
            temporary.append(Path(name))
        for path, fmt in zip(temporary[:2], ("png", "pdf")):
            fig.savefig(path, format=fmt, dpi=200)
        provenance = build_provenance(data, layout, destinations[:2], argv,
                                      hash_paths=temporary[:2], figure_number=number)
        temporary[2].write_text(json.dumps(provenance, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        for source, destination in zip(temporary, destinations):
            source.chmod(0o644)
            # Atomic no-clobber publication, including a concurrent creator.
            os.link(source, destination)
            published.append(destination)
        return destinations
    except BaseException:
        for path in published:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--flow", type=Path, default=Path(DEFAULT_FLOW))
    parser.add_argument("out_prefix", type=Path)
    args = parser.parse_args(argv)
    figure = None
    try:
        _figure_number(args.out_prefix)
        _destinations(args.out_prefix)
        data = load_flow(args.repo_root, args.flow)
        figure, layout = make_figure(data)
        recorded_argv = ["python3", GENERATOR_PATH, *(sys.argv[1:] if argv is None else map(str, argv))]
        _publish_outputs(figure, layout, args.out_prefix.resolve(), data, recorded_argv)
    except Exception as exc:
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {args.out_prefix}.png / .pdf / .provenance.json")
    return 0
# A fixed structural caption; not subject to the JSON free-text contract.
CAPTION = ('Figure {number}. Data flow of the K2 manual synthesis loop over three recorded rounds, read from the frozen results note {basename}. '
'In each round the parent session projects typed JSON inputs (planner: {planner_keys}; coder: {coder_keys}) to planner-v4 and coder-v4-autonomous-k2; '
 'the proposal is one backoff literal evaluated by one Pegasus compute-node job with separate trace-enabled verify and trace-disabled bench builds and a campaign WAL terminal record; critic reads the digest and the WAL. '
'Measurement reflux occurred twice (the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round) and diagnosis reflux once (the second critic into the third-round inputs as the typed key {diagnosis_key} with fields {diagnosis_fields}, identical for planner and coder). '
'The unevaluated proposal, generated without a diagnosis key, re-proposed a known value. '
'The planner and coder role definitions declare no tools (structural blockade); critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation. '
'Certified means only that the trace-enabled verify run found the observed trace serializable with no anomaly; it is not a performance certification and not a choice among candidates. '
'Discipline-six marks are role self-reports that external inputs contained no instruction-like strings; their form differs by role and they are not a mechanical gate. '
'No causal effect of the knowledge source or of the diagnosis on the proposed values is claimed: each condition was launched once, without a control. '
'The same-job stock control was not achieved and awaits a ruling; proposal values are backoff literals, not results. '
'This is a schematic of recorded data flow; no performance values are drawn and the three runs are not compared.')

if __name__ == '__main__':
    raise SystemExit(main())
