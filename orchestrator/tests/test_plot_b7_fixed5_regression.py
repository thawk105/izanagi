"""B-7 fixed5 evidence, rendered figure, caption and landing contracts."""
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
    spec = importlib.util.spec_from_file_location("b7_fixed5_under_test", REPO / "tools/plotting/plot_b7_fixed5_regression.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLOT = _load_module()
RESULTS = REPO / PLOT.CAPTION_SOURCE
LANDED = "docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression"
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


def _seal(root, durable):
    p = PLOT
    _edit(root / p.MANIFEST_JSON, lambda m: m.update(files={path: _hash(durable / path) for path in p.RAW_REL.values()}))
    return {path: _hash(root / path) for path in p.PINNED_SHA256}


def _fixture(tmp_path):
    p = PLOT
    root, durable = tmp_path / "repo", tmp_path / "durable"
    policy = {"schema_version": p.POLICY_SCHEMA, "study": p.STUDY,
              "performance_common": {"threads": 48, "records": 1000000, "skew": "0.9", "rmw": "0", "max_ope": "10", "extime": 3, "reps": p.REPS, "ccbench_protocol": "silo"},
              "workloads": [], "cells": []}
    cert = {"schema_version": p.CERT_SCHEMA, "study": p.STUDY, "attempt_id": p.ATTEMPT_ID,
            "source_commit": "a"*40, "current_pin": "fixture-pin", "protocol_sha256": "b"*64,
            "status": "reject", "a4_noise_floor_status": "open", "request_ids": {}, "cells": [], "effects": {}}
    for wi, w in enumerate(p.WORKLOADS):
        policy["workloads"].append({"id": w, "adopted_backoff_us": p.ADOPTED_US})
        cert["request_ids"][w] = f"fixture-{wi}.nqsv"
        medians = []
        for ai, arm in enumerate(("stock", "fixed5")):
            cid = f"{w}-{arm}"
            role = "stock" if ai == 0 else "adopted"
            genome = dict(p.STOCK_GENOME if ai == 0 else p.ADOPTED_GENOME)
            token = "stock" if ai == 0 else "synthetic-source-bytes"
            perf, trace = hashlib.sha256((cid+'perf').encode()).hexdigest(), hashlib.sha256((cid+'trace').encode()).hexdigest()
            base = (wi+2)*1000000 + (0 if ai == 0 else (600000 if wi < 2 else -400000))
            samples = [float(base + delta) for delta in (-20000, -10000, 0, 10000, 60000)]
            medians.append(statistics.median(samples))
            cell = {"cell_id": cid, "workload": w, "role": role, "genome": genome,
                    "src_token": token, "source_binding_status": "bound", "perf_bin_sha256": perf, "trace_bin_sha256": trace,
                    "performance": {"status": "complete", "median_tps": medians[-1]},
                    "correctness": {"status": "certified", "disposition": "pass", "legacy": "pass", "performance": "pass",
                                    "legacy_repetitions_observed": 1, "performance_repetitions_observed": p.REPS}}
            cert["cells"].append(cell)
            policy["cells"].append({"id": cid, "workload": w, "role": role, "genome": genome})
            record = {"verdict": "serializable", "certified": True, "status": "pass", "integrity": "ok", "trace_enabled": True, "trace_binary_sha256": trace}
            raw = {"schema_version": p.RAW_SCHEMA, "attempt_id": p.ATTEMPT_ID, "cell_id": cid, "src_token": token, "genome": genome,
                   "performance": {"samples_tps": samples, "unstable": False, "trace_enabled": False, "status": "complete", "perf_bin_sha256": perf,
                                   "workload": {"threads": 48, "records": 1000000, "reps": p.REPS, "extime": 3,
                                                "workload": {"ycsb_rratio": str(p.RRATIOS[w]), "ycsb_rmw": "0", "ycsb_max_ope": "10", "ycsb_zipf_skew": "0.9"}}},
                   "build_evidence": {"performance_trace_disabled_build": True, "trace_bin_sha256": trace},
                   "correctness": {"legacy": [dict(record)], "performance": [dict(record) for _ in range(p.REPS)]}}
            _write(durable / p.RAW_REL[cid], raw)
        cert["effects"][w] = medians[1]/medians[0]-1
        _write(root / p.FLOOR_JSON[w], {"schema_version": p.FLOOR_SCHEMA,
            "genome": p.FLOOR_GENOME, "threads": 48, "records": 1000000,
            "workload": {"ycsb_rratio": str(p.RRATIOS[w]), "ycsb_zipf_skew": "0.9", "ycsb_rmw": "0"},
            "between_run": {"cv": .01, "sessions": 8, "reps_per_session": p.REPS, "high_variance": False}})
    _write(root / p.POLICY_PATH, policy)
    cert["policy_sha256"] = _hash(root / p.POLICY_PATH)
    _write(root / p.CERT_JSON, cert)
    _write(root / p.MANIFEST_JSON, {"schema_version": p.MANIFEST_SCHEMA, "study": p.STUDY,
            "attempt_id": p.ATTEMPT_ID, "protocol_sha256": cert["protocol_sha256"], "current_pin": cert["current_pin"], "files": {}})
    source = root / p.CAPTION_SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("Synthetic wording authority.\n")
    generator = root / p.GENERATOR_PATH
    generator.parent.mkdir(parents=True)
    generator.write_bytes(p.GENERATOR.read_bytes())
    return root, durable, _seal(root, durable)


def _data(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    return PLOT.load_evidence(root, durable, expected_hashes=hashes)


def _reject(call, phrase=None):
    try:
        call()
    except PLOT.FigureDataError as exc:
        if phrase is not None:
            assert phrase in str(exc), str(exc)
    else:
        raise AssertionError("invalid evidence was accepted")


def _reject_changed(tmp_path, change, phrase, *, path=None, raw=False):
    root, durable, _ = _fixture(tmp_path)
    path = path or (PLOT.RAW_REL['rr5-stock'] if raw else PLOT.CERT_JSON)
    _edit((durable if raw else root) / path, change)
    hashes = _seal(root, durable)
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), phrase)


def _provenance(data, tmp_path):
    outputs = [tmp_path / f"fig10_test{s}" for s in SUFFIXES[:2]]
    for path in outputs:
        path.write_bytes(b"synthetic output bytes")
    return PLOT.build_provenance(data, outputs, ["python3", PLOT.GENERATOR_PATH])


def test_fixture_has_production_shape_and_recomputes_statistics(tmp_path):
    data = _data(tmp_path)
    assert len(data['cells']) == 6 and len(data['external_inputs']) == 6
    for c in data['cells']:
        assert len(c['samples_tps']) == 5
        assert c['median_tps'] == statistics.median(c['samples_tps'])
        assert c['mean_tps'] == statistics.fmean(c['samples_tps']) != c['median_tps']
        assert c['stdev_tps'] == statistics.stdev(c['samples_tps'])
        assert c['ci95_half_tps'] == 2.7764451051977987*c['stdev_tps']/math.sqrt(5)
        assert c['correctness'] == {'status': 'certified', 'legacy_records': 1, 'performance_records': 5, 'verdicts_all_serializable': True}
    for i, w in enumerate(PLOT.WORKLOADS):
        assert data['effects'][w] == data['cells'][2*i+1]['median_tps']/data['cells'][2*i]['median_tps']-1
        expected = 'regression' if data['effects'][w] < -data['floors'][w]['cv'] else 'no-regression'
        assert data['judgments'][w]['recorded'] == expected == PLOT.RECORDED_JUDGMENT[w]


def test_artist_series_equal_provenance_cells_and_rendered_artists(tmp_path):
    data = _data(tmp_path)
    fig, axes = PLOT.make_figure(data)
    try:
        prov = _provenance(data, tmp_path)
        assert fig._b7_artist_series == prov['artist_series']
        for i, w in enumerate(PLOT.WORKLOADS):
            ax = axes[i]
            for x, c in enumerate(data['cells'][2*i:2*i+2]):
                points, = [s for s in ax.collections if s.get_gid() == c['cell_id']+'-samples']
                assert list(points.get_offsets()[:, 1]) == [v/1e6 for v in c['samples_tps']]
                assert list(points.get_offsets()[:, 0]) == [x+j for j in (-.12, -.06, 0, .06, .12)]
                median, = [s for s in ax.collections if s.get_gid() == c['cell_id']+'-median']
                assert list(median.get_segments()[0][:, 1]) == [c['median_tps']/1e6]*2
                means = ax.containers[x]
                assert list(means.lines[0].get_ydata()) == [c['mean_tps']/1e6]
                segment = means.lines[2][0].get_segments()[0]
                assert all(math.isclose(a, b) for a, b in zip(segment[:, 1], [(c['mean_tps']-c['ci95_half_tps'])/1e6, (c['mean_tps']+c['ci95_half_tps'])/1e6]))
                rows = [r for r in prov['artist_series'] if r.get('cell_id') == c['cell_id']]
                assert {r['kind'] for r in rows} == {'sample-points', 'median', 'mean-ci95'}
                assert next(r['values'] for r in rows if r['kind'] == 'sample-points') == c['samples_tps']
            baseline, = [s for s in ax.lines if s.get_gid() == 'stock-median']
            assert list(baseline.get_ydata()) == [data['cells'][2*i]['median_tps']/1e6]*2
            lines = {s.get_gid(): s for s in axes[3].lines}
            assert list(lines[w+'-effect'].get_ydata()) == [100*data['effects'][w]]
            assert list(lines[w+'-floor'].get_ydata()) == [-100*data['floors'][w]['cv']]*2
            assert lines[w+'-effect'].get_markerfacecolor() == ('#2166ac' if w == 'rr95' else 'white')
    finally:
        PLOT.plt.close(fig)


def test_real_figure_passes_layout_check(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        assert len(axes) == 4 and len(fig.axes) == 4
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
    prefix = tmp_path / 'fig10_overlap'
    try:
        fig.text(.5, .5, 'overlap alpha')
        fig.text(.5, .5, 'overlap beta')
        _reject(lambda: PLOT._publish_outputs(fig, axes, prefix, data, []), 'overlap')
        assert not list(tmp_path.glob('*fig10_overlap*'))
    finally:
        PLOT.plt.close(fig)


def test_caption_contains_fixed_literals(tmp_path):
    caption = PLOT._caption(_data(tmp_path), 'fig10_test')
    literals = [
        'This is B-7 material, not a B-7 satisfaction decision (D2044 item 3).',
        'The rule fixed before the results were seen classifies a workload as regression when effect < -floor (strict), floor being the D1639 between-run noise floor (coefficient of variation of the stock genome across 8 sessions of 5 repetitions, measured earlier under the same settings).',
        'No regression is neither superiority nor proof of no difference; the floor is not the standard error of the effect, and no significance decision is made.',
        "The outer status is the protocol's conjunction over the three workloads and follows from the negative read-heavy effect; it is not a research verdict.",
        'This figure reports a single attempt of five samples per cell; it does not promote the certification and does not speak to repeated attempts.',
        'Correctness comes from separate trace-enabled verify runs under the recorded check configuration, not the performance configuration: all 6 cells are recorded as certified with serializable verdicts (1 legacy and 5 performance records each); certified means serializability of the observed traces under that check configuration and nothing beyond, and this is not a performance certification.',
        'Mean confidence intervals describe samples; they are not confidence intervals for effects, medians, or the floor judgment.',
        'Top-row y axes are workload-local and must not be compared across panels.',
        'Existing materials with other adopted values are neither pooled nor compared.',
    ]
    for literal in literals:
        assert literal in caption, literal
    assert 'outer status reject; a4_noise_floor_status open' in caption
    assert 'Result of that rule: write-heavy no regression, balanced no regression, read-heavy regression (below -floor).' in caption
    for i in range(3):
        assert f'request fixture-{i}.nqsv' in caption
    data = _data(tmp_path / 'second')
    data['judgments']['rr5']['recorded'] = 'regression'
    assert 'Result of that rule: write-heavy regression (below -floor)' in PLOT._caption(data, 'fig10_test')


def test_caption_avoids_forbidden_claims(tmp_path):
    caption = PLOT._caption(_data(tmp_path), 'fig10_test')
    assert not re.search(r'\b(significant|superior|improvement|anomaly)\b', caption, re.I)
    for phrase in ('satisfies B-7', 'B-7 is met', 'performance certified'):
        assert phrase.lower() not in caption.lower()
    assert 'promot' not in caption.replace('does not promote', '')


def test_caption_figure_number_comes_from_prefix(tmp_path):
    data = _data(tmp_path)
    assert PLOT._caption(data, 'fig10_test').startswith('Figure 10.')
    assert PLOT._caption(data, 'fig27_test').startswith('Figure 27.')
    _reject(lambda: PLOT._caption(data, 'figX_test'))


def _reject_hash_drift(tmp_path, path):
    root, durable, hashes = _fixture(tmp_path)
    target = root / path
    target.write_bytes(target.read_bytes()+b'\n')
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'SHA-256 mismatch')


def test_certification_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.CERT_JSON)


def test_manifest_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.MANIFEST_JSON)


def test_floor_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.FLOOR_JSON['rr5'])


def test_policy_hash_drift_is_rejected(tmp_path):
    _reject_hash_drift(tmp_path, PLOT.POLICY_PATH)


def test_policy_sha_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda c: c.update(policy_sha256='f'*64), 'policy SHA-256 mismatch')


def test_raw_sha_mismatch_is_rejected(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    path = durable / PLOT.RAW_REL['rr5-stock']
    path.write_bytes(path.read_bytes()+b'\n')
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'raw SHA-256 mismatch')


def test_raw_missing_is_rejected(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    (durable / PLOT.RAW_REL['rr5-stock']).unlink()
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'raw missing')


def test_sample_count_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r['performance']['samples_tps'].pop(), 'sample count', raw=True)


def test_median_mismatch_is_rejected(tmp_path):
    # Scale both arms together: the ratio still matches if median checks are removed.
    root, durable, _ = _fixture(tmp_path)
    for arm in ('stock', 'fixed5'):
        _edit(durable/PLOT.RAW_REL['rr5-'+arm], lambda r: r['performance'].update(
            samples_tps=[v*2 for v in r['performance']['samples_tps']]))
    hashes = _seal(root, durable)
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'median mismatch')


def test_effect_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda c: c['effects'].update(rr5=.4), 'effect mismatch')


def test_judgment_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda f: f['between_run'].update(cv=.2), 'judgment mismatch', path=PLOT.FLOOR_JSON['rr95'])


def test_uncertified_cell_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda c: c['cells'][0]['correctness'].update(status='rejected'), 'uncertified cell')


def test_raw_verdict_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r['correctness']['performance'][0].update(verdict='unknown'), 'raw verdict', raw=True)


def test_trace_enabled_samples_are_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r['performance'].update(trace_enabled=True), 'trace-enabled performance', raw=True)


def test_unstable_samples_are_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r['performance'].update(unstable=True), 'unstable samples', raw=True)


def test_adopted_stock_token_is_rejected(tmp_path):
    root, durable, _ = _fixture(tmp_path)
    def change(c):
        for row in c['cells']:
            if row['role'] == 'adopted':
                row['src_token'] = 'stock'
    _edit(root/PLOT.CERT_JSON, change)
    for w in PLOT.WORKLOADS:
        _edit(durable/PLOT.RAW_REL[w+'-fixed5'], lambda r: r.update(src_token='stock'))
    hashes = _seal(root, durable)
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes), 'adopted stock token')


def test_source_binding_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda c: c['cells'][0].update(source_binding_status='unbound'), 'source binding')


def test_caption_source_missing_is_rejected(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    (root/PLOT.CAPTION_SOURCE).unlink()
    _reject(lambda: PLOT.load_evidence(root, durable, expected_hashes=hashes))


def test_cell_order_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda c: c['cells'].reverse(), 'cell order')


def test_floor_genome_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda f: f.update(genome='different-genome'), 'floor genome mismatch', path=PLOT.FLOOR_JSON['rr5'])


def test_provenance_binds_caption_source(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    data = PLOT.load_evidence(root, durable, expected_hashes=hashes)
    prov = _provenance(data, tmp_path)
    assert [r for r in prov['tracked_inputs'] if r['kind'] == 'caption_source'] == [
        {'kind': 'caption_source', 'path': PLOT.CAPTION_SOURCE, 'sha256': _hash(root/PLOT.CAPTION_SOURCE),
         'authority_scope': 'wording of limitations and conditions only; not measurement values, effects, or the floor judgment'}]
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    (root/PLOT.CAPTION_SOURCE).write_text('Changed wording.\n')
    _reject(lambda: PLOT.validate_repo_closure(prov, root, expected_hashes=hashes), 'tracked_inputs')


def test_pinned_hashes_are_used_when_no_override(tmp_path):
    root, durable, _ = _fixture(tmp_path)
    _reject(lambda: PLOT.load_evidence(root, durable), 'SHA-256 mismatch')


def test_generator_comment_change_preserves_provenance_closure(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prov = _provenance(PLOT.load_evidence(root, durable, expected_hashes=hashes), tmp_path)
    generator = root/PLOT.GENERATOR_PATH
    assert prov['generator']['sha256'] == _hash(generator)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    generator.write_bytes(generator.read_bytes()+b'\n# Comment only.\n')
    assert prov['generator']['sha256'] != _hash(generator)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)


def test_external_sources_and_repo_closure_have_separate_roots(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prov = _provenance(PLOT.load_evidence(root, durable, expected_hashes=hashes), tmp_path)
    PLOT.validate_external_sources(prov, durable)
    (durable/PLOT.RAW_REL['rr5-stock']).unlink()
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
    prov = PLOT.build_provenance(data, outputs, [])
    _assert_landed_output_paths(prov)
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    other = root/'other'
    other.mkdir()
    for row, path in zip(prov['outputs'], outputs):
        alternate = other/path.name
        alternate.write_bytes(path.read_bytes())
        row['path'] = alternate.relative_to(root).as_posix()
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    try:
        _assert_landed_output_paths(prov)
    except AssertionError as exc:
        assert str(exc).startswith('landed output paths mismatch')
    else:
        raise AssertionError('alternate directory accepted as landing')


def _document_values():
    text = RESULTS.read_text()
    floor_section = text.split('### 1.4', 1)[1].split('## 2.', 1)[0]
    floors = {w: float(re.search(rf'{w} `([0-9.]+)`', floor_section).group(1)) for w in PLOT.WORKLOADS}
    table = text.split('### 2.1', 1)[1].split('### 2.2', 1)[0]
    effects, judgments = {}, {}
    for w in PLOT.WORKLOADS:
        line, = [line for line in table.splitlines() if line.startswith(f'| {w} (')]
        cols = [c.strip() for c in line.split('|')[1:-1]]
        effects[w] = float(re.fullmatch(r'`([^`]+)`', cols[3]).group(1))
        judgments[w] = {'**退行なし**': 'no-regression', '**退行 (床値超)**': 'regression'}[cols[6]]
    samples, medians = {}, {}
    table = text.split('### 2.2', 1)[1].split('### 2.3', 1)[0]
    for cid in PLOT.RAW_REL:
        line, = [line for line in table.splitlines() if line.startswith(f'| `{cid}` |')]
        cols = [c.strip() for c in line.split('|')[1:-1]]
        samples[cid] = [float(v) for v in cols[1].split(',')]
        medians[cid] = float(cols[2].replace(',', ''))
    return floors, effects, judgments, samples, medians


def test_pins_floors_effects_and_judgments_match_results_document():
    p = PLOT
    table = RESULTS.read_text().split('### 5.1', 1)[1].split('### 5.2', 1)[0]
    for path in (p.CERT_JSON, p.MANIFEST_JSON):
        line, = [line for line in table.splitlines() if line.startswith(f'| `{Path(path).name}` |')]
        assert re.findall(r'`([0-9a-f]{64})`', line) == [p.PINNED_SHA256[path]]
        assert _hash(REPO/path) == p.PINNED_SHA256[path]
    floors, effects, judgments, _, _ = _document_values()
    cert = json.loads((REPO/p.CERT_JSON).read_text())
    assert cert['effects'] == effects
    assert p.RECORDED_JUDGMENT == judgments
    for w in p.WORKLOADS:
        assert json.loads((REPO/p.FLOOR_JSON[w]).read_text())['between_run']['cv'] == floors[w]


def test_real_evidence_matches_results_document():
    durable = Path(PLOT.DEFAULT_MEASUREMENT_ROOT)
    if not durable.exists():
        skip('durable measurement root unavailable')
    data = PLOT.load_evidence(REPO, durable)
    floors, effects, judgments, samples, medians = _document_values()
    assert data['effects'] == effects
    for w in PLOT.WORKLOADS:
        assert data['floors'][w]['cv'] == floors[w]
        assert data['judgments'][w]['recorded'] == judgments[w]
    for c in data['cells']:
        assert c['samples_tps'] == samples[c['cell_id']]
        assert c['median_tps'] == medians[c['cell_id']]


def test_cli_writes_three_outputs_and_provenance_closure(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prefix = root/'fig10_fixture'
    assert PLOT.main(['--repo-root', str(root), '--measurement-root', str(durable), str(prefix)], expected_hashes=hashes) == 0
    paths = [Path(f'{prefix}{s}') for s in SUFFIXES]
    assert all(p.is_file() for p in paths)
    prov = json.loads(paths[2].read_text())
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    PLOT.validate_external_sources(prov, durable)
    assert prov['reproduction']['argv'] == ['python3', PLOT.GENERATOR_PATH, '--repo-root', str(root), '--measurement-root', str(durable), prefix.name]
    for key, change, phrase in (
        ('artist_series', lambda v: v[0].update(x=99), 'artist'),
        ('cells', lambda v: v[0].update(mean_tps=1), 'cells'),
        ('caption', None, 'caption'),
    ):
        changed = copy.deepcopy(prov)
        if change is None:
            changed[key] += ' drift'
        else:
            change(changed[key])
        _reject(lambda: PLOT.validate_repo_closure(changed, root, expected_hashes=hashes), phrase)
    paths[0].write_bytes(paths[0].read_bytes()+b'drift')
    _reject(lambda: PLOT.validate_repo_closure(prov, root, expected_hashes=hashes), 'output closure')


def test_cli_rejects_prefix_without_fig_number(tmp_path):
    root, durable, hashes = _fixture(tmp_path)
    prefix = tmp_path/'figX_invalid'
    assert PLOT.main(['--repo-root', str(root), '--measurement-root', str(durable), str(prefix)], expected_hashes=hashes) == 2
    assert not list(tmp_path.glob('figX_invalid*'))


def test_landed_fig10_repo_closure_and_caption_when_present():
    prefix = REPO/LANDED
    paths = [Path(f'{prefix}{s}') for s in SUFFIXES]
    assert all(p.is_file() for p in paths), 'fig10 integration bundle is incomplete'
    prov = json.loads(paths[2].read_text())
    _assert_landed_output_paths(prov)
    PLOT.validate_repo_closure(prov, REPO)
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
    (prefix.parent/'README.md').write_text('Figure 10 landing regression.\n')
    for suffix in present_suffixes:
        Path(f'{prefix}{suffix}').write_bytes(b'presence only; reject missing files first')
    original = REPO
    try:
        REPO = root
        try:
            test_landed_fig10_repo_closure_and_caption_when_present()
        except AssertionError as exc:
            assert str(exc).startswith('fig10 integration bundle is incomplete'), str(exc)
        except BaseException as exc:
            pytest = sys.modules.get('pytest')
            if isinstance(exc, Skip) or (pytest is not None and isinstance(exc, pytest.skip.Exception)):
                raise AssertionError('missing fig10 bundle was skipped instead of rejected') from exc
            raise
        else:
            raise AssertionError('missing fig10 bundle was accepted')
    finally:
        REPO = original


def test_landed_fig10_rejects_all_missing_outputs(tmp_path):
    _reject_missing_landed_bundle(tmp_path/'repo', ())


def test_landed_fig10_rejects_partial_missing_outputs(tmp_path):
    for mask in range(1, 7):
        _reject_missing_landed_bundle(tmp_path/f'repo-{mask}', [s for i, s in enumerate(SUFFIXES) if mask & (1 << i)])


def _run():
    passed = failed = skipped = errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith('test_') and callable(value)]
    for test in tests:
        node = f'{Path(__file__).name}::{test.__name__}'
        try:
            with tempfile.TemporaryDirectory(prefix='b7-fixed5-test-') as directory:
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
