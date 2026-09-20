"""B-10 waiting-grid evidence, rendered figure, caption and landing contracts."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import statistics
import sys
import tempfile
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from skiputil import Skip, skip


def _load_module():
    spec = importlib.util.spec_from_file_location("b10_waiting_grid_forest_under_test", REPO / "tools/plotting/plot_b10_waiting_grid_forest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLOT = _load_module()
RESULTS = REPO / PLOT.CAPTION_SOURCE
LANDED = "docs/paper-story/figures/fig13_b10_waiting_grid_forest"
SUFFIXES = (".png", ".pdf", ".provenance.json")


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _edit(path, change):
    record = json.loads(path.read_text())
    change(record)
    _write(path, record)


RECEIPT_BYTES = b'{"dry_run":false,"job_script_path":"tools/pegasus/b10_backoff_shape_campaign.sh","job_script_sha256":"6f633ad08579d020190bf76263c006774a2d548a48ccd3f99106f090df628f6b","nonce":"23409962b76be959bb523a0cd5a31bc1","phase":"report","prereg_commit":"77b33e37d2d63b1f83d10652792c3c93eba9fe8f","request":{"elapstim_req_s":86400,"nodes":1,"project":"SFC","queue":"gen_S"},"request_id":"978195.nqsv","schema_version":"pegasus-b10-submit-receipt/v2","source_commit":"2a338449bb2798b729c5bc2f9bfe76463a7fe347","submitted_epoch":1788581651,"workload":null}\n'
RESULT_BYTES = b'{"completed_epoch":1788582054,"driver_rc":0,"nonce":"23409962b76be959bb523a0cd5a31bc1","pbs_jobid":"0:978195.nqsv","phase":"report","request_id":"978195.nqsv","scheduler_elapse_limit_s":86400,"scheduler_remaining_elapse_at_start_s":86396,"schema_version":"pegasus-b10-job-result/v1","source_commit":"2a338449bb2798b729c5bc2f9bfe76463a7fe347","submission_receipt":"/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962b76be959bb523a0cd5a31bc1/submit-receipt.json","workload":null}\n'

def _reject(call, phrase=None):
    try:
        call()
    except PLOT.FigureDataError as exc:
        if phrase is not None:
            assert phrase in str(exc), str(exc)
    else:
        raise AssertionError("invalid evidence was accepted")

def _markdown(document):
    j = document['judgement']
    lines = ['## Paired sign-flip permutation + Holm', '']
    for f in j['families']:
        lines.append(f"- {f['workload']} / symmetric-modulo: outcome={f['outcome']}, pairs={f['pairs']}, raw_p={f['raw_p']:.8g}, holm_p={f['holm_p']:.8g}")
    lines.extend(['', '## Cell effects and 95% paired-block intervals', ''])
    for c in j['cell_effects']:
        lines.append(f"- {c['workload']} / {c['shape']} / mu={c['mean_us']}: effect={c['effect']}, CI=[{c['ci95_low']}, {c['ci95_high']}], status={c['status']}, equivalence={c['equivalence_relation']}")
    return '\n'.join(lines) + '\n'


def _seal(root):
    return {p: _hash(root/p) for p in PLOT.PINNED_SHA256}


def _fixture(tmp_path):
    p = PLOT
    root, durable = tmp_path/'repo', tmp_path/'durable'
    receipt = json.loads(RECEIPT_BYTES)
    submission = {k: receipt[k] for k in ('request_id', 'nonce', 'phase', 'source_commit', 'prereg_commit', 'job_script_sha256')}
    submission['receipt_sha256'] = hashlib.sha256(RECEIPT_BYTES).hexdigest()
    spec = dict(analysis=dict(alpha=.05, equivalence_margin_pct=3.,
        confidence_interval=dict(critical_value=4.302652729911275, degrees_of_freedom=2, method='student-t-paired-block-mean'),
        permutation=dict(enumeration='all-2^18', pairs_per_family=18, sided='two-sided'),
        holm_families=[dict(workload=w, shape='symmetric-modulo') for w in p.WORKLOADS],
        exposure=dict(minimum_calls_per_cell=10000)),
        grid=dict(means_us=[2, 5, 10, 25, 50, 100], shapes=[dict(name=s) for s in p.SHAPES]), execution=dict(threads=48))
    records, medians = [], {}
    for wi, w in enumerate(p.WORKLOADS):
        for bi, b in enumerate(p.BLOCKS):
            points = [('none', None, None), ('adaptive', None, None), ('zero-loop', 'constant', 0)]
            points += [(f'{s}-mu{m}', s, m) for s in p.SHAPES for m in p.MEANS_US]
            for point, shape, mean in points:
                base = 1000000. + wi*100000 + bi*1000
                if shape == 'symmetric-modulo':
                    effect = (-.012, .012, .024)[bi] if mean == 2 else (-.01 if mean == 5 else .008 + mean*.00001 + bi*.0001)
                    base *= 1+effect
                samples = [base-2, base-1, base, base+1, base+2]
                records.append(dict(workload=w, block_id=b, point=point, shape=shape, mean_us=mean,
                    median_tps=statistics.median(samples), throughputs=samples, backoff_call_count=10000,
                    correctness_certified=True, missing=False, unstable=False, official_certification=False))
                medians[w, b, shape, mean] = statistics.median(samples)
    families, cells = [], []
    for wi, w in enumerate(p.WORKLOADS):
        diffs = [medians[w,b,'symmetric-modulo',m]/medians[w,b,'constant',m]-1 for b in p.BLOCKS for m in p.MEANS_US]
        families.append(dict(workload=w, shape='symmetric-modulo', pairs=18, differences=diffs,
            raw_p=(6000, 80, 4)[wi]/262144, status='testable', reasons=[], outcome='different'))
        for shape in p.SHAPES:
            for i, m in enumerate(p.MEANS_US):
                values = [0.]*3 if shape == 'constant' else [diffs[b*6+i] for b in range(3)]
                mean = statistics.mean(values)
                half = 4.302652729911275*statistics.stdev(values)/math.sqrt(3)
                low, high = mean-half, mean+half
                relation = 'inside-equivalence-range' if low >= -.03 and high <= .03 else ('outside-equivalence-range' if high < -.03 or low > .03 else 'overlaps-equivalence-boundary')
                cells.append(dict(workload=w, shape=shape, mean_us=m, effect=mean, ci95_low=low, ci95_high=high,
                    equivalence_margin_pct=3., equivalence_relation=relation, status='estimable'))
    running = 0
    for i, f in enumerate(sorted(families, key=lambda f: f['raw_p'])):
        running = max(running, min(1., (3-i)*f['raw_p']))
        f['holm_p'] = running
    doc = dict(schema_version='b10-backoff-shape-provenance/v2', official_certification=False, pin='511c953',
        submission=submission, preregistration=dict(spec=spec), records=records,
        judgement=dict(schema_version='b10-backoff-shape-judgement/v1', alpha=.05,
            spec_sha256='9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2', families=families, cell_effects=cells))
    _write(root/p.PROVENANCE_JSON, doc)
    (root/p.REPORT_MD).write_text(_markdown(doc))
    (root/p.CAPTION_SOURCE).parent.mkdir(parents=True)
    (root/p.CAPTION_SOURCE).write_text('Fixture limitations and conditions.\n')
    for kind, content in zip(p.EXTERNAL_REL, (RECEIPT_BYTES, RESULT_BYTES)):
        path = durable/p.EXTERNAL_REL[kind]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    generator = root/p.GENERATOR_PATH
    generator.parent.mkdir(parents=True)
    generator.write_bytes(p.GENERATOR.read_bytes())
    return root, durable, _seal(root)


def _data(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    return PLOT.load_evidence(root, durable, expected_hashes=hashes)


def _reject_changed(tmp_path, change, phrase, *, sync_markdown=False):
    root, durable, _ = _fixture(tmp_path)
    _edit(root/PLOT.PROVENANCE_JSON, change)
    if sync_markdown:
        (root/PLOT.REPORT_MD).write_text(_markdown(json.loads((root/PLOT.PROVENANCE_JSON).read_text())))
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=_seal(root)), phrase)


def _provenance(data, tmp_path):
    outputs = [tmp_path/('fig13_fixture'+s) for s in SUFFIXES[:2]]
    for path in outputs:
        path.write_bytes(b'fixture output bytes')
    import os
    argv = ['python3', PLOT.GENERATOR_PATH, '--repo-root', str(data['repo_root']), '--evidence-root', str(tmp_path/'durable'), os.path.relpath(outputs[0].with_suffix(''), data['repo_root'])]
    return PLOT.build_provenance(data, outputs, argv)


def test_fixture_has_production_shape_and_recomputes_statistics(tmp_path):
    data = _data(tmp_path)
    assert len(data['cells']) == 36 and len(data['families']) == 3
    assert data['crosschecks']['records'] == 135 and data['crosschecks']['registered_records'] == 108
    assert any(c['effect'] < 0 for c in data['cells'])
    assert any(c['ci95_low'] > 0 for c in data['cells'])
    assert data['summary']['overlaps'] > 0
    for c in data['cells']:
        assert math.isclose(c['effect'], statistics.mean(c['block_effects']), abs_tol=1e-12)
        half = 4.302652729911275*statistics.stdev(c['block_effects'])/math.sqrt(3)
        assert math.isclose(c['ci95_low'], c['effect']-half, abs_tol=1e-12)
        assert math.isclose(c['ci95_high'], c['effect']+half, abs_tol=1e-12)


def test_artist_series_equal_provenance_cells_and_rendered_artists(tmp_path):
    data = _data(tmp_path)
    fig, axes = PLOT.make_figure(data)
    try:
        prov = _provenance(data, tmp_path)
        assert prov['artist_series'] == fig._b10_artist_series
        artists = {a.get_gid(): a for a in fig.findobj() if a.get_gid()}
        for i, (c, row) in enumerate(zip(prov['cells'], prov['artist_series'])):
            assert row['x'] == 100*c['effect'] and row['low'] == 100*c['ci95_low'] and row['high'] == 100*c['ci95_high']
            point = artists[f'cell-{i}']
            assert list(point.get_xdata()) == [row['x']]
            assert list(point.get_ydata()) == [row['y']]
            assert point.get_marker() == row['marker']
            if c['shape'] == 'symmetric-modulo':
                assert list(artists[f'blocks-{i}'].get_xdata()) == row['block_x']
                assert artists[f'blocks-{i}'].get_zorder() < point.get_zorder()
                assert artists[f'interval-{i}'].get_segments()[0].tolist() == [[row['low'], row['y']], [row['high'], row['y']]]
            else:
                assert point.get_markerfacecolor() == 'white'
        assert len({ax.get_xlim() for ax in axes}) == 1
        assert all(ax.yaxis_inverted() for ax in axes)
    finally:
        PLOT.plt.close(fig)


def test_layout_rejects_wrong_axes_count(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        _reject(lambda: PLOT.check_figure_layout(fig, axes[:2]), 'three axes')
    finally:
        PLOT.plt.close(fig)


def test_real_figure_passes_layout_check(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        assert len(axes) == 3 and len(fig.axes) == 3
        PLOT.check_figure_layout(fig, axes)
    finally:
        PLOT.plt.close(fig)


def test_bbox_overlap_is_a_failure(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        PLOT.check_figure_layout(fig, axes)
        fig.text(.5, .5, 'overlap alpha')
        fig.text(.5, .5, 'overlap beta')
        _reject(lambda: PLOT.check_figure_layout(fig, axes), 'overlap')
    finally:
        PLOT.plt.close(fig)


def test_layout_failure_publishes_nothing(tmp_path):
    data = _data(tmp_path)
    fig, axes = PLOT.make_figure(data)
    prefix = tmp_path / 'fig13_overlap'
    try:
        fig.text(.5, .5, 'overlap alpha')
        fig.text(.5, .5, 'overlap beta')
        _reject(lambda: PLOT._publish_outputs(fig, axes, prefix, data, []), 'overlap')
        assert not list(tmp_path.glob('*fig13_overlap*'))
    finally:
        PLOT.plt.close(fig)




def test_caption_contains_fixed_literals(tmp_path):
    caption = PLOT._caption(_data(tmp_path), "fig13_test")
    for literal in ["Each family's outcome is the preregistered procedure's classification and is not a research verdict.", 'Intervals lying inside the +/-3.0% margin are reported as the position of the interval and are not a finding of equivalence; no equivalence test was performed.', 'Per-cell intervals are descriptive and no per-cell significance decision is made; the only tests are the three family-level permutation tests with Holm adjustment.', 'The static right-tail cohorts (separate preregistration, grid and driver) are neither pooled nor compared with this grid.', 'official_certification is false; these performance values are not a basis for adopting a variant.', 'Direction and effect sizes are stated for this one contrast only; nothing is claimed about waiting-shape effects in general, about binary, about a dose response of dispersion, or about a general separation of waiting shape from waiting amount.', 'Correctness is recorded from separate trace-enabled runs (135 of 135 cells certified) and is not a performance certification.', 'The three workloads ran as separate jobs on different days and driver versions; absolute throughput is not compared across workloads, and no mechanism is claimed for the direction.']:
        assert literal in caption, literal
def test_caption_figure_number_comes_from_prefix(tmp_path):
    data = _data(tmp_path)
    assert PLOT._caption(data, 'fig13_test').startswith('Figure 13.')
    assert PLOT._caption(data, 'fig27_test').startswith('Figure 27.')
    _reject(lambda: PLOT._caption(data, 'figX_test'))



def test_caption_avoids_forbidden_claims(tmp_path):
    caption = PLOT._caption(_data(tmp_path), 'fig13_test').lower()
    for phrase in ('equivalent', 'superior', 'desynchroniz', 'performance certified', 'significantly', 'no difference', 'mechanism explains', 'reproduc'):
        assert phrase not in caption


def _reject_hash_drift(tmp_path, relative, external=False):
    root, durable, hashes = _fixture(tmp_path)
    path = (durable if external else root)/relative
    path.write_bytes(path.read_bytes()+b' ')
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'SHA-256')


def test_provenance_json_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.PROVENANCE_JSON)


def test_report_markdown_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.REPORT_MD)


def test_receipt_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.EXTERNAL_REL['report_receipt'], True)


def test_job_result_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.EXTERNAL_REL['report_job_result'], True)


def test_receipt_sha_not_matching_submission_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['submission'].update(receipt_sha256='0'*64), 'submission receipt_sha256')


def _external_semantic_reject(tmp_path, kind, change, phrase):
    # Rebind synthetic bytes, leaving all validators real. This isolates content
    # validation from the separately tested production-byte pin.
    root, durable, _ = _fixture(tmp_path)
    _edit(durable/PLOT.EXTERNAL_REL[kind], change)
    previous = PLOT.EXTERNAL_SHA256
    try:
        PLOT.EXTERNAL_SHA256 = {**previous, kind: _hash(durable/PLOT.EXTERNAL_REL[kind])}
        if kind == 'report_receipt':
            _edit(root/PLOT.PROVENANCE_JSON, lambda d: d['submission'].update(receipt_sha256=PLOT.EXTERNAL_SHA256[kind]))
        _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=_seal(root)), phrase)
    finally:
        PLOT.EXTERNAL_SHA256 = previous


def test_receipt_identity_mismatch_is_rejected(tmp_path):
    _external_semantic_reject(tmp_path, 'report_receipt', lambda d: d.update(nonce='other'), 'receipt identity nonce')


def test_job_result_driver_rc_nonzero_is_rejected(tmp_path):
    _external_semantic_reject(tmp_path, 'report_job_result', lambda d: d.update(driver_rc=1), 'driver_rc')


def test_family_count_mismatch_is_rejected(tmp_path):
    # A duplicate preserves the identity set: only the cardinality check rejects it.
    _reject_changed(tmp_path, lambda d: d['judgement']['families'].append(copy.deepcopy(d['judgement']['families'][0])), 'family count')


def test_family_outcome_or_pairs_mismatch_is_rejected(tmp_path):
    for key, value in [('pairs', 17), ('outcome', 'not-detected')]:
        _reject_changed(tmp_path/key, lambda d: d['judgement']['families'][0].update({key: value}), 'family outcome or pairs', sync_markdown=True)


def test_differences_order_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['judgement']['families'][0]['differences'].reverse(), 'differences')


def test_differences_value_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['judgement']['families'][0]['differences'].__setitem__(0, .99), 'differences')


def test_raw_p_not_dyadic_is_rejected(tmp_path):
    def change(d):
        f = d['judgement']['families'][0]
        f.update(raw_p=.023123456, holm_p=.023123456)
    _reject_changed(tmp_path, change, 'denominator', sync_markdown=True)


def test_holm_p_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['judgement']['families'][0].update(holm_p=.03), 'Holm recalculation', sync_markdown=True)


def test_holm_p_above_alpha_is_rejected(tmp_path):
    def change(d):
        d['judgement']['families'][0].update(raw_p=.125, holm_p=.125)
    _reject_changed(tmp_path, change, 'above alpha', sync_markdown=True)


def test_cell_count_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['judgement']['cell_effects'].pop(), 'cell count')


def test_cell_effect_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['judgement']['cell_effects'][6].update(effect=.9), 'cell effect')


def test_cell_interval_mismatch_is_rejected(tmp_path):
    for key in ('ci95_low', 'ci95_high'):
        _reject_changed(tmp_path/key, lambda d: d['judgement']['cell_effects'][6].update({key: .9}), 'cell interval')


def test_equivalence_relation_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['judgement']['cell_effects'][6].update(equivalence_relation='inside-equivalence-range'), 'equivalence relation')


def test_constant_cell_nonzero_is_rejected(tmp_path):
    for key in ('effect', 'ci95_low', 'ci95_high'):
        _reject_changed(tmp_path/key, lambda d: d['judgement']['cell_effects'][0].update({key: .001}), 'constant cell')


def test_uncertified_or_missing_or_unstable_record_is_rejected(tmp_path):
    for key, value in [('correctness_certified', False), ('missing', True), ('unstable', True)]:
        _reject_changed(tmp_path/key, lambda d: d['records'][0].update({key: value}), 'record quality')


def test_official_certification_true_is_rejected(tmp_path):
    _reject_changed(tmp_path/'top', lambda d: d.update(official_certification=True), 'official_certification')
    _reject_changed(tmp_path/'record', lambda d: d['records'][0].update(official_certification=True), 'official_certification')


def test_record_count_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['records'].pop(), 'record count')


def test_median_not_matching_throughputs_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda d: d['records'][0].update(median_tps=1), 'record median')


def test_underexposed_registered_cell_is_rejected(tmp_path):
    # The positive fixture sits exactly on 10000, distinguishing >= from >.
    _data(tmp_path/'boundary')
    _reject_changed(tmp_path/'below', lambda d: d['records'][3].update(backoff_call_count=9999), 'exposure')


def test_report_markdown_holm_line_mismatch_is_rejected(tmp_path):
    root, durable, _ = _fixture(tmp_path)
    path = root/PLOT.REPORT_MD
    path.write_text(path.read_text().replace('pairs=18', 'pairs=17', 1))
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=_seal(root)), 'markdown Holm')


def test_caption_source_missing_is_rejected(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    (root/PLOT.CAPTION_SOURCE).unlink()
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'invalid evidence')


def test_spec_constants_mismatch_is_rejected(tmp_path):
    changes = [lambda s: s['analysis'].update(alpha=.1), lambda s: s['analysis'].update(equivalence_margin_pct=4),
        lambda s: s['analysis']['confidence_interval'].update(critical_value=1.96),
        lambda s: s['analysis']['permutation'].update(pairs_per_family=12),
        lambda s: s['grid'].update(means_us=[2, 5]), lambda s: s['analysis']['holm_families'].pop()]
    for i, change in enumerate(changes):
        _reject_changed(tmp_path/str(i), lambda d: change(d['preregistration']['spec']), 'spec')

def test_provenance_binds_caption_source(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prov = _provenance(PLOT.load_evidence(root, durable, expected_hashes=hashes), tmp_path)
    row, = [r for r in prov['tracked_inputs'] if r['kind'] == 'caption_source']
    assert row == dict(kind='caption_source', path=PLOT.CAPTION_SOURCE, sha256=_hash(root/PLOT.CAPTION_SOURCE), authority_scope=PLOT.CAPTION_SCOPE)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    (root/PLOT.CAPTION_SOURCE).write_text('Changed wording.\n')
    _reject(lambda: PLOT.validate_repo_closure(prov, root, expected_hashes=hashes), 'tracked_inputs')


def test_pinned_hashes_are_used_when_no_override(tmp_path):
    root, durable, _ = _fixture(tmp_path)
    _reject(lambda: PLOT.load_evidence(root, durable), 'SHA-256 mismatch')
    PLOT._authority_data(REPO)  # Also kills a mutation of the production pin itself.


def test_generator_comment_change_preserves_provenance_closure(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prov = _provenance(PLOT.load_evidence(root, durable, expected_hashes=hashes), tmp_path)
    generator = root/PLOT.GENERATOR_PATH
    assert prov['generator']['sha256'] == _hash(generator)
    generator.write_bytes(generator.read_bytes()+b'\n# Comment only.\n')
    prov['generator']['sha256'] = _hash(generator)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)


def test_external_sources_and_repo_closure_have_separate_roots(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prov = _provenance(PLOT.load_evidence(root, durable, expected_hashes=hashes), tmp_path)
    PLOT.validate_external_sources(prov, durable)
    (durable/PLOT.EXTERNAL_REL['report_receipt']).unlink()
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    _reject(lambda: PLOT.validate_external_sources(prov, durable), 'external sources')
    for field in ('external_inputs', 'tracked_inputs'):
        changed = copy.deepcopy(prov)
        changed[field].pop()
        _reject(lambda: PLOT.validate_repo_closure(changed, root, expected_hashes=hashes), field)


def _assert_landed_output_paths(prov):
    assert [r['path'] for r in prov['outputs']] == [LANDED+s for s in SUFFIXES[:2]], 'landed output paths mismatch'


def test_landed_output_paths_reject_same_basename_in_other_directory(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    data = PLOT.load_evidence(root, durable, expected_hashes=hashes)
    outputs = [root/(LANDED+s) for s in SUFFIXES[:2]]
    outputs[0].parent.mkdir(parents=True)
    for path in outputs:
        path.write_bytes(b'synthetic landed bytes')
    argv = ['python3', PLOT.GENERATOR_PATH, '--repo-root', str(root), '--evidence-root', str(durable), LANDED]
    prov = PLOT.build_provenance(data, outputs, argv)
    _assert_landed_output_paths(prov)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    other = root/'other'
    other.mkdir()
    for path in outputs:
        (other/path.name).write_bytes(path.read_bytes())
    for row in prov['outputs']:
        row['path'] = 'other/'+Path(row['path']).name
    argv[-1] = 'other/'+Path(LANDED).name
    prov['reproduction']['argv'] = argv
    import shlex
    prov['reproduction']['command'] = shlex.join(argv)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    try:
        _assert_landed_output_paths(prov)
    except AssertionError as exc:
        assert 'landed output paths' in str(exc)
    else:
        raise AssertionError('alternate directory accepted as landing')


def test_pins_match_results_document():
    text = RESULTS.read_text()
    section = text.split('### 4.1', 1)[1].split('### 4.2', 1)[0]
    for path, digest in PLOT.PINNED_SHA256.items():
        rows = re.findall(r'\| `'+re.escape(path)+r'` \| `([0-9a-f]{64})` \|', section)
        assert rows == [digest]
        assert _hash(REPO/path) == digest
    for digest in PLOT.EXTERNAL_SHA256.values():
        assert digest in text.split('### 4.2', 1)[1]


def test_document_values_match_report_json():
    text = RESULTS.read_text()
    judgement = json.loads((REPO/PLOT.PROVENANCE_JSON).read_text())['judgement']
    section = text.split('### 2.2 ', 1)[1].split('### 2.3 ', 1)[0]
    rows = re.findall(r'^\| (\S+) / symmetric-modulo \| `testable` \| \*\*`different`\*\* \| (\d+) \| (\S+) \(= (\d+) / 2\^18\) \| (\S+) \|$', section, re.M)
    assert len(rows) == 3
    for w, pairs, raw, numerator, holm in rows:
        f = next(f for f in judgement['families'] if f['workload'] == w)
        assert int(pairs) == f['pairs'] and float(raw) == f['raw_p'] and float(holm) == f['holm_p']
        assert int(numerator)/262144 == f['raw_p']
    section = text.split('### 2.4 ', 1)[1].split('### 2.5 ', 1)[0]
    rows = re.findall(r'^\| (\S+) \| (\d+) \| (\S+) \| (\S+) \| (\S+) \| `([^`]+)` \| `estimable` \|$', section, re.M)
    assert len(rows) == 18
    for w, mean, effect, low, high, relation in rows:
        c = next(c for c in judgement['cell_effects'] if (c['workload'], c['shape'], c['mean_us']) == (w, 'symmetric-modulo', int(mean)))
        assert (float(effect), float(low), float(high), relation) == (c['effect'], c['ci95_low'], c['ci95_high'], c['equivalence_relation'])


def test_real_evidence_loads_when_root_present():
    if not Path(PLOT.EVIDENCE_ROOT).exists():
        skip('external evidence root absent')
    data = PLOT.load_evidence(REPO, PLOT.EVIDENCE_ROOT)
    assert data['summary'] == dict(inside=32, overlaps=4, outside=0, indeterminate=0, estimable=36)
    assert [f['raw_p_numerator_2pow18'] for f in data['families']] == [6702, 70, 2]
    fig, axes = PLOT.make_figure(data)
    try:
        PLOT.check_figure_layout(fig, axes)
    finally:
        PLOT.plt.close(fig)


def test_cli_writes_three_outputs_and_provenance_closure(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prefix = root/'fig13_fixture'
    assert PLOT.main(['--repo-root', str(root), '--evidence-root', str(durable), str(prefix)], expected_hashes=hashes) == 0
    paths = [Path(f'{prefix}{s}') for s in SUFFIXES]
    assert all(p.is_file() for p in paths)
    prov = json.loads(paths[2].read_text())
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    PLOT.validate_external_sources(prov, durable)
    for key in ('artist_series', 'cells', 'caption', 'summary', 'report', 'analysis', 'reproduction'):
        changed = copy.deepcopy(prov)
        changed[key] = 'drift'
        _reject(lambda: PLOT.validate_repo_closure(changed, root, expected_hashes=hashes))
    changed = copy.deepcopy(prov)
    changed['unknown'] = True
    _reject(lambda: PLOT.validate_repo_closure(changed, root, expected_hashes=hashes), 'key set')
    paths[0].write_bytes(paths[0].read_bytes()+b'drift')
    _reject(lambda: PLOT.validate_repo_closure(prov, root, expected_hashes=hashes), 'output closure')


def test_cli_rejects_prefix_without_fig_number(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    for name in ('figX_invalid', 'fig_invalid', 'fi13_invalid'):
        prefix = tmp_path/name
        assert PLOT.main(['--repo-root', str(root), '--evidence-root', str(durable), str(prefix)], expected_hashes=hashes) == 2
        assert not list(tmp_path.glob(name+'*'))


def test_landed_fig13_repo_closure_and_caption_when_present():
    prefix = REPO/LANDED
    paths = [Path(f'{prefix}{s}') for s in SUFFIXES]
    assert all(p.is_file() for p in paths), 'fig13 integration bundle is incomplete'
    prov = json.loads(paths[2].read_text())
    _assert_landed_output_paths(prov)
    PLOT.validate_repo_closure(prov, REPO)
    row, = [r for r in prov['tracked_inputs'] if r['kind'] == 'caption_source']
    assert row['sha256'] == _hash(REPO/PLOT.CAPTION_SOURCE)
    readme = (prefix.parent/'README.md').read_text()
    assert prov['caption'] in readme
    section = readme.split(f'# `{prefix.name}` — ', 1)[1].split('\n# ', 1)[0]
    hashes = section.split('## 着地 bytes の SHA-256\n', 1)[1].split('\n## ', 1)[0]
    for path in paths:
        rows = re.findall(rf'^- `{re.escape(path.name)}` SHA-256: `([0-9a-f]{{64}})`$', hashes, re.M)
        assert len(rows) == 1 and rows[0] == _hash(path), f'README hash mismatch: {path.name}'
def _reject_missing_landed_bundle(root, present_suffixes):
    global REPO
    prefix = root/LANDED
    prefix.parent.mkdir(parents=True)
    (prefix.parent/'README.md').write_text('Figure 13 landing regression.\n')
    for suffix in present_suffixes:
        Path(f'{prefix}{suffix}').write_bytes(b'presence only; reject missing files first')
    original = REPO
    try:
        REPO = root
        try:
            test_landed_fig13_repo_closure_and_caption_when_present()
        except AssertionError as exc:
            assert str(exc).startswith('fig13 integration bundle is incomplete'), str(exc)
        except BaseException as exc:
            pytest = sys.modules.get('pytest')
            if isinstance(exc, Skip) or (pytest is not None and isinstance(exc, pytest.skip.Exception)):
                raise AssertionError('missing fig13 bundle was skipped instead of rejected') from exc
            raise
        else:
            raise AssertionError('missing fig13 bundle was accepted')
    finally:
        REPO = original


def test_landed_fig13_rejects_all_missing_outputs(tmp_path):
    _reject_missing_landed_bundle(tmp_path/'repo', ())


def test_landed_fig13_rejects_partial_missing_outputs(tmp_path):
    for mask in range(1, 7):
        _reject_missing_landed_bundle(tmp_path/f'repo-{mask}', [s for i, s in enumerate(SUFFIXES) if mask & (1 << i)])


def _run():
    passed = failed = skipped = errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith('test_') and callable(value)]
    for test in tests:
        node = f'{Path(__file__).name}::{test.__name__}'
        try:
            with tempfile.TemporaryDirectory(prefix='b10-waiting-grid-test-') as directory:
                kwargs = {'tmp_path': Path(directory)} if 'tmp_path' in inspect.signature(test).parameters else {}
                test(**kwargs)
            print(f'PASS {node}')
            passed += 1
        except Skip as exc:
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
    return 1 if failed or errors else 0


if __name__ == '__main__':
    sys.exit(_run())
