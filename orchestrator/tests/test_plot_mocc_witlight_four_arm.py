"""Real-grid, independent-oracle and two-layer closure checks for fig15."""
from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import traceback
from functools import lru_cache

import numpy as np
from matplotlib.text import Text

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from skiputil import Skip, skip
_spec = importlib.util.spec_from_file_location('mocc_figure_under_test', REPO/'tools/plotting/plot_mocc_witlight_four_arm.py')
PLOT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PLOT)
LANDED = 'docs/paper-story/figures/fig15_mocc_witlight_four_arm'
SUFFIXES = ('.png', '.pdf', '.provenance.json')
CP = ([0., 0.059629492286166874], [0.0004218744523420083, 0.08939905005748705])


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def _seal(external, *, preserve_inputs=False):
    hashes = {f'{b}/result.json': PLOT._sha256(external/f'{b}/result.json') for b in PLOT.BLOCKS}
    summary = PLOT._json(external/'summary.json')
    if not preserve_inputs:
        summary['inputs'] = [dict(path=f'{PLOT.EVIDENCE_ROOT}/{b}/result.json', sha256=hashes[f'{b}/result.json']) for b in PLOT.BLOCKS]
    _write(external/'summary.json', summary)
    hashes['summary.json'] = PLOT._sha256(external/'summary.json')
    return hashes


def _fixture(tmp_path):
    root, external = tmp_path/'repo', tmp_path/'external'
    caption = root/PLOT.CAPTION_SOURCE
    caption.parent.mkdir(parents=True)
    caption.write_text('Synthetic wording source, independent of measurement values.\n')
    for bi, block in enumerate(PLOT.BLOCKS):
        runs, bindings = [], {}
        for ai, arm in enumerate(PLOT.ARMS):
            definitions = ['-DCCBENCH_TRACE=1', f'-DCCBENCH_BACK_OFF={ai//2}']
            bindings[arm] = dict(witness=ai%2 == 0, pin=PLOT.PIN, configure_defines=definitions, configure_argv=['cmake']+definitions)
        for ri in range(15):
            start = (bi+ri)%4
            order = list(PLOT.ARMS[start:]+PLOT.ARMS[:start])
            for pos, arm in enumerate(order):
                ordinal = ri*4+pos+1
                ai = PLOT.ARMS.index(arm)
                g2 = (block, ordinal) in (('W1',18), ('W3',5))
                runs.append(dict(block_id=block, hostname=f'fixture-node-{bi}', arm=arm, ordinal=ordinal, round=ri+1, order=order,
                                 rc=0, witness=ai%2 == 0, pin=PLOT.PIN, commit_count=600001+bi*1103+ri*37+ai*101,
                                 verifier=dict(status='g2' if g2 else 'no-g2', rc=1 if g2 else 0), discriminator=dict(status='not-run')))
        _write(external/f'{block}/result.json', dict(schema_version='t2774-probe/v1', block_id=block, hostname=f'fixture-node-{bi}',
               status='completed', rounds=15, planned_runs=60, not_started=0, runs=runs,
               bindings=dict(arms=bindings, workload_argv=list(PLOT.WORKLOAD_ARGV))))
    arms = {}
    for ai, arm in enumerate(PLOT.ARMS):
        k = ai%2
        arms[arm] = dict(N=60, m=60, k=k, failure=0, indeterminate=0, decisive_m=60, k_over_m=k/60, cp95=CP[k],
                         discriminator_counts={s:60 if s=='not-run' else 0 for s in ('supported','contradicted','indeterminate','no-g2','input-rejected','not-run')},
                         identification=dict(g2_runs=k, identified_g2_runs=0, rate=0. if k else None))
    _write(external/'summary.json', dict(schema_version='t2774-summary/v1', arms=arms))
    return root, external, _seal(external)


def _data(tmp_path):
    root, external, pins = _fixture(tmp_path)
    return PLOT.load_evidence(root, external, expected_hashes=pins)


def _reject(call, phrase=None):
    try:
        call()
    except PLOT.FigureDataError as exc:
        if phrase is not None:
            assert phrase in str(exc), str(exc)
    else:
        raise AssertionError('invalid input accepted')


def _changed(tmp_path, relative, mutate, phrase, *, preserve_inputs=False):
    root, external, pins = _fixture(tmp_path)
    value = PLOT._json(external/relative)
    mutate(value)
    _write(external/relative, value)
    pins = _seal(external, preserve_inputs=preserve_inputs)
    _reject(lambda: PLOT.load_evidence(root, external, expected_hashes=pins), phrase)


def _provenance(root, external, pins):
    data = PLOT.load_evidence(root, external, expected_hashes=pins)
    outputs = [root/('fig15_fixture'+s) for s in SUFFIXES[:2]]
    for path in outputs:
        path.write_bytes(b'closure-only synthetic output bytes')
    argv = ['python3', PLOT.GENERATOR_PATH, '--repo-root', str(root), '--evidence-root', str(external), 'fig15_fixture']
    return PLOT.build_provenance(data, outputs, argv)


@lru_cache(maxsize=1)
def _rendered():
    # One actual production-shaped fixture Figure, shared read-only except restored mutations.
    with tempfile.TemporaryDirectory() as directory:
        data = _data(Path(directory))
    fig, axes = PLOT.make_figure(data)
    return data, fig, axes


def _visible(fig):
    return [t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]


def test_fixture_has_production_shape_and_rotation(tmp_path):
    root, external, pins = _fixture(tmp_path)
    blocks = [PLOT._json(external/f'{b}/result.json') for b in PLOT.BLOCKS]
    assert len(blocks) == 4 and all(len(b['runs']) == 60 for b in blocks)
    for bi, b in enumerate(blocks):
        assert b['rounds'] == 15
        for ri in range(15):
            order = list(PLOT.ARMS[(bi+ri)%4:]+PLOT.ARMS[:(bi+ri)%4])
            assert [r['arm'] for r in b['runs'][4*ri:4*ri+4]] == order
    data = PLOT.load_evidence(root, external, expected_hashes=pins)
    assert all(a['positions'] == {'1':15,'2':15,'3':15,'4':15} for a in data['arms'].values())
    assert [(r['block_id'],r['ordinal'],r['arm']) for b in blocks for r in b['runs'] if r['verifier']['status']=='g2'] == [('W1',18,'e9-witlight-nowit'),('W3',5,'e9-witlight-nowit-bo1')]
    assert not (external/'smoke').exists()


def test_statistics_recomputed_from_runs(tmp_path):
    data = _data(tmp_path)
    for ai, a in enumerate(data['arms'].values()):
        assert [a[k] for k in ('N','m','k','failure','indeterminate','decisive_m')] == [60,60,ai%2,0,0,60]
        total = sum(600001+b*1103+r*37+ai*101 for b in range(4) for r in range(15))
        assert a['commit_count_sum'] == total and a['commit_count_mean'] == total/60
        assert a['identification'] == dict(g2_runs=ai%2, identified_g2_runs=0, rate=0. if ai%2 else None)
    for bo in (0,1):
        a, b = [data['arms'][x] for x in PLOT.ARMS[2*bo:2*bo+2]]
        assert data['exposure_ratios'][bo]['ratio'] == a['commit_count_sum']/b['commit_count_sum']


def test_cp95_matches_reference_values_and_boundaries():
    for k in (0,1):
        assert np.allclose(PLOT._cp95(k,60), CP[k], rtol=0, atol=1e-14)
    assert np.allclose(PLOT._cp95(60,60), [0.9403705077138331,1.], rtol=0, atol=1e-14)
    assert np.allclose(PLOT._cp95(1,1), [.025,1.], rtol=0, atol=1e-14)
    for k in range(61):
        lo, hi = PLOT._cp95(k,60)
        assert 0 <= lo <= k/60 <= hi <= 1


def test_fisher_is_one_sided_on_lower():
    assert PLOT._fisher_less([[0,60],[1,59]]) == .5
    assert PLOT._fisher_less([[1,59],[0,60]]) == 1.
    assert math.isclose(PLOT._fisher_less([[0,3],[3,0]]), .05, abs_tol=1e-15)


def test_commit_mean_uses_all_runs_of_each_arm(tmp_path):
    root, external, pins = _fixture(tmp_path)
    blocks = [PLOT._json(external/f'{b}/result.json') for b in PLOT.BLOCKS]
    # Make the two G2 runs' contribution unmistakable; summary contains no commit mean.
    blocks[0]['runs'][17]['commit_count'] = 9999999
    blocks[2]['runs'][4]['commit_count'] = 8888888
    for block, b in zip(PLOT.BLOCKS, blocks):
        _write(external/f'{block}/result.json',b)
    pins = _seal(external)
    data = PLOT.load_evidence(root,external,expected_hashes=pins)
    for arm in PLOT.ARMS:
        values = [r['commit_count'] for b in blocks for r in b['runs'] if r['arm']==arm]
        assert len(values)==60
        assert data['arms'][arm]['commit_count_mean'] == sum(values)/60


def test_external_hash_drift_is_rejected(tmp_path):
    for i, rel in enumerate(PLOT.EXTERNAL_SHA256):
        root, external, pins = _fixture(tmp_path/str(i))
        path = external/rel
        path.write_bytes(path.read_bytes()+b' ')
        _reject(lambda: PLOT.load_evidence(root,external,expected_hashes=pins), 'SHA-256 mismatch')


def test_production_pins_match_results_document():
    section = (REPO/PLOT.CAPTION_SOURCE).read_text().split('### 5.1 ',1)[1].split('### 5.2 ',1)[0]
    for rel, pin in PLOT.EXTERNAL_SHA256.items():
        matches = re.findall(r'\| `arm-W/'+re.escape(rel)+r'` \| `([0-9a-f]{64})`', section)
        assert matches == [pin], rel


def test_summary_disagreement_is_rejected(tmp_path):
    mutations = {k: (lambda a,k=k: a.__setitem__(k,a[k]+1)) for k in ('N','m','k','failure','indeterminate','decisive_m','k_over_m')}
    mutations.update(cp95=lambda a:a.__setitem__('cp95',[0.,.2]), discriminator_counts=lambda a:a['discriminator_counts'].__setitem__('not-run',59), identification=lambda a:a['identification'].__setitem__('identified_g2_runs',1))
    for name, mutate in mutations.items():
        _changed(tmp_path/name,'summary.json',lambda s:mutate(s['arms'][PLOT.ARMS[0]]), 'summary')


def test_summary_inputs_are_exact(tmp_path):
    changes = [lambda s:s['inputs'].pop(), lambda s:s['inputs'].append(s['inputs'][0]),
               lambda s:s['inputs'].reverse(), lambda s:s['inputs'][0].__setitem__('path','elsewhere'),
               lambda s:s['inputs'][0].__setitem__('sha256','0'*64)]
    for i, change in enumerate(changes):
        _changed(tmp_path/str(i),'summary.json',change,'summary inputs exact',preserve_inputs=True)


def test_summary_inputs_reject_smoke_extra_entry(tmp_path):
    _changed(tmp_path,'summary.json',lambda s:s['inputs'].append(dict(path=PLOT.EVIDENCE_ROOT+'/smoke/result.json',sha256='0'*64)), 'summary inputs exact',preserve_inputs=True)


def test_smoke_or_duplicate_run_in_main_block_is_rejected(tmp_path):
    changes = [(lambda b:b.__setitem__('block_id','smoke'),'block ID'),
               (lambda b:b['runs'].append(b['runs'][0]),'runs count'),
               (lambda b:b['runs'][1].__setitem__('ordinal',1),'ordinal/round'),
               (lambda b:b['runs'][0].__setitem__('round',2),'ordinal/round')]
    for i,(change,phrase) in enumerate(changes):
        _changed(tmp_path/str(i),'W1/result.json',change,phrase)


def test_arm_bindings_and_rotation_are_checked(tmp_path):
    changes = [(lambda b:b['runs'][0].__setitem__('witness',False),'run arm binding'),
               (lambda b:b['bindings']['arms'][PLOT.ARMS[0]].__setitem__('witness',False),'arm binding'),
               (lambda b:b['bindings']['arms'][PLOT.ARMS[0]].__setitem__('configure_defines',['-DCCBENCH_TRACE=1','-DCCBENCH_BACK_OFF=1']),'BACK_OFF'),
               (lambda b:b['runs'][0]['order'].reverse(),'rotation/order'),
               (lambda b:b['bindings']['workload_argv'].__setitem__(0,'-ycsb_tuple_num=9999'),'workload_argv')]
    for i,(change,phrase) in enumerate(changes):
        _changed(tmp_path/str(i),'W1/result.json',change,phrase)


def test_failure_or_indeterminate_is_rejected(tmp_path):
    changes = [lambda r:r.__setitem__('rc',1), lambda r:r['verifier'].__setitem__('status','indeterminate'),
               lambda r:r['verifier'].__setitem__('rc',1), lambda r:r['verifier'].__setitem__('status','unknown')]
    for i, change in enumerate(changes):
        _changed(tmp_path/str(i),'W1/result.json',lambda b:change(b['runs'][0]),'failure or indeterminate')


def test_rendered_artists_equal_provenance(tmp_path):
    data, fig, axes = _rendered()
    series = fig._mocc_artist_series
    root, external, pins = _fixture(tmp_path)
    paths = [root/('fig15_artist'+s) for s in SUFFIXES[:2]]
    for p in paths:
        p.write_bytes(b'artists test')
    prov = PLOT.build_provenance(data, paths, [], artist_series=series)
    assert prov['artist_series'] == series
    ax, = axes
    points = [a for a in ax.lines if a.get_gid()=='rate-point']
    intervals = [a for a in ax.lines if a.get_gid()=='cp-interval']
    assert len(points)==len(intervals)==4
    for row, point, interval in zip(series['rows'],points,intervals):
        assert list(point.get_xdata()) == [row['rate_pct']]
        assert list(point.get_ydata()) == [row['y']]
        assert list(interval.get_xdata()) == row['cp95_pct']
        assert list(interval.get_ydata()) == [row['y']]*2
    texts = [t.get_text() for t in fig.findobj(Text) if t.get_gid()=='numeric-column']
    assert texts == [r[k] for r in series['rows'] for k in ('k_over_m','rate','cp95','mean_commits')]


def test_real_figure_passes_layout_check():
    _, fig, axes = _rendered()
    assert len(fig.axes)==1 and axes.shape==(1,)
    PLOT.check_figure_layout(fig,axes)


def test_required_disclosures_are_rendered():
    _, fig, _ = _rendered()
    text = '\n'.join(_visible(fig))
    for literal in ('non-certifying','TRACE=1 build','exposure, not performance','on lower, unadjusted',
                    'BACK_OFF=0: one-sided Fisher (on lower, unadjusted) p = 0.500',
                    'BACK_OFF=1: one-sided Fisher (on lower, unadjusted) p = 0.500',
                    'not equivalence','power 0.105 is calculated under design assumptions','verifier detection; does not identify a root cause',
                    'on / BACK_OFF=0','off / BACK_OFF=0','on / BACK_OFF=1','off / BACK_OFF=1',
                    '[0%, 5.963%]','[0.042%, 8.940%]','0/60','1/60','mean commits per run'):
        assert literal in text, literal


def test_layout_rejects_overlap_wrong_axes_and_escape():
    _, fig, axes = _rendered()
    extra = fig.text(.065,.315,'overlap')
    try:
        _reject(lambda:PLOT.check_figure_layout(fig,axes),'overlap')
    finally:
        extra.remove()
    extra = fig.text(1.1,.5,'escape')
    try:
        _reject(lambda:PLOT.check_figure_layout(fig,axes),'leaves figure')
    finally:
        extra.remove()
    extra = fig.add_axes([.1,.1,.1,.1])
    try:
        _reject(lambda:PLOT.check_figure_layout(fig,axes),'exactly one')
    finally:
        extra.remove()


def test_layout_failure_publishes_nothing(tmp_path):
    data, fig, axes = _rendered()
    prefix = tmp_path/'fig15_overlap'
    extra = fig.text(.065,.315,'overlap')
    try:
        _reject(lambda:PLOT._publish_outputs(fig,axes,prefix,data,[]),'overlap')
        assert not any(Path(str(prefix)+s).exists() for s in SUFFIXES)
    finally:
        extra.remove()


FORBIDDEN = ('equivalent','equivalence established','no difference','no effect','no witness effect',
             'absent with witness on','G2 cannot occur with witness on','throughput','performance improvement','faster','slower',
             'root cause identified','real anomaly confirmed','torn read confirmed','MOCC is certified','witness is certified','MOCC certified')


def _check_claims(caption, fig):
    text = '\n'.join([caption]+_visible(fig)).lower()
    for phrase in FORBIDDEN:
        assert phrase.lower() not in text, phrase


def test_caption_fixed_literals_and_forbidden_claims():
    data, fig, axes = _rendered()
    caption = PLOT._caption(data,'fig15_test')
    literals = (
        'Non-significance does not establish equivalence, and zero detections do not establish absence.',
        'Power 0.105 is a calculation under the design assumptions, not a measured quantity: independent Bernoulli trials, 60 runs per arm, off probability 0.0417, on probability 0, and a one-sided Fisher test at alpha 0.05.',
        'TRACE=1 commit counts are exposure, not performance.',
        'G2 signals do not identify a root cause or distinguish a real anomaly from a torn read.',
        'This is a non-certifying observation; individual verifier certified flags and observational_only=false do not certify this wave, MOCC, or the witness.',
        'The denominator includes only 4 blocks x 15 rounds x 4 arms; smoke runs are excluded.',
        'CP intervals and Fisher p values assume independent Bernoulli trials and do not model within-node dependence, rotation order, or temporal variation.',
        'Conditions: 48 threads, 10,000 records, Zipf 0.9, read ratio 50, rmw 0, max operations 10, 3 s, TRACE=1 build, pin e9e477ca + X/P + witlight patches, Pegasus compute nodes, 4 blocks W1–W4 x 15 rounds x 4 arms, smoke excluded.',
        'Primary comparison BACK_OFF=0: one-sided Fisher (on lower), unadjusted p = 0.500',
        'Secondary comparison BACK_OFF=1: one-sided Fisher (on lower), unadjusted p = 0.500',
        'W1 e9-witlight-nowit (1/15)', 'W3 e9-witlight-nowit-bo1 (1/15)',
        'fired zero times and made zero comparisons', 'not a comparison at equal commit exposure',
        'Values from earlier waves [T-1892], [T-2774], and [T-2779] are neither pooled nor compared here.',
    )
    for literal in literals:
        assert literal in caption, literal
    _check_claims(caption,fig)
    original = axes[0].get_title()
    axes[0].set_title(original+' equivalent')
    try:
        try:
            _check_claims(caption,fig)
        except AssertionError as exc:
            assert str(exc).partition('\n')[0]=='equivalent'
        else:
            raise AssertionError('visible forbidden claim escaped detection')
    finally:
        axes[0].set_title(original)


def test_caption_number_comes_from_prefix(tmp_path):
    data = _data(tmp_path)
    assert PLOT._caption(data,'fig15_test').startswith('Figure 15.')
    assert PLOT._caption(data,'fig237_test').startswith('Figure 237.')
    for prefix in ('figX_test','fig15b_test','figure15_test'):
        _reject(lambda:PLOT._caption(data,prefix),'prefix')


def test_cli_outputs_and_provenance_closure(tmp_path):
    root, external, pins = _fixture(tmp_path)
    prefix = root/'fig15_cli'
    assert PLOT.main(['--repo-root',str(root),'--evidence-root',str(external),str(prefix)],expected_hashes=pins)==0
    assert all(Path(str(prefix)+s).is_file() for s in SUFFIXES)
    prov = PLOT._json(Path(str(prefix)+SUFFIXES[2]))
    PLOT.validate_repo_closure(prov,root,expected_hashes=pins)
    PLOT.validate_external_sources(prov,external,expected_hashes=pins)
    assert prov['reproduction']['argv']==['python3',PLOT.GENERATOR_PATH,'--repo-root',str(root),'--evidence-root',str(external),'fig15_cli']
    for key in ('schema','tracked_inputs','external_inputs','source_inputs','measurement_conditions','arms','blocks','comparisons','exposure_ratios','artist_series','caption','outputs','reproduction'):
        changed = copy.deepcopy(prov)
        changed[key] = 'drift'
        _reject(lambda:PLOT.validate_repo_closure(changed,root,expected_hashes=pins))
    for key in ('arms','blocks','measurement_conditions','comparisons','exposure_ratios'):
        changed=copy.deepcopy(prov)
        changed[key]='drift'
        _reject(lambda:PLOT.validate_external_sources(changed,external,expected_hashes=pins))
    Path(str(prefix)+'.png').write_bytes(b'drift')
    _reject(lambda:PLOT.validate_repo_closure(prov,root,expected_hashes=pins),'output closure')


def test_cli_default_reads_flat_verbatim_fixture(tmp_path):
    root, external, pins = _fixture(tmp_path)
    verbatim = root/PLOT.VERBATIM_PATH
    verbatim.mkdir(parents=True)
    for rel, name in PLOT.VERBATIM_FILES.items():
        shutil.copyfile(external/rel, verbatim/name)
    prefix = root/'fig15_flat'
    assert PLOT.main(['--repo-root', str(root), str(prefix)], expected_hashes=pins) == 0
    assert all(Path(str(prefix)+suffix).is_file() for suffix in SUFFIXES)
    prov = PLOT._json(Path(str(prefix)+SUFFIXES[2]))
    assert prov['reproduction']['argv'][5] == str(verbatim.resolve())
    PLOT.validate_external_sources(prov, verbatim.resolve(), expected_hashes=pins)


def test_external_sources_and_repo_closure_have_separate_roots(tmp_path):
    root, external, pins = _fixture(tmp_path)
    prov = _provenance(root,external,pins)
    PLOT.validate_external_sources(prov,external,expected_hashes=pins)
    (external/'W1/result.json').unlink()
    PLOT.validate_repo_closure(prov,root,expected_hashes=pins)
    _reject(lambda:PLOT.validate_external_sources(prov,external,expected_hashes=pins),'external sources')
    for key in ('tracked_inputs','external_inputs'):
        changed=copy.deepcopy(prov)
        changed[key].pop()
        _reject(lambda:PLOT.validate_repo_closure(changed,root,expected_hashes=pins),key)
    (root/PLOT.CAPTION_SOURCE).write_text('Changed wording')
    _reject(lambda:PLOT.validate_repo_closure(prov,root,expected_hashes=pins),'tracked_inputs')


def test_relocated_evidence_keeps_original_input_paths(tmp_path):
    root, external, pins = _fixture(tmp_path)
    moved = tmp_path/'moved'
    shutil.move(external,moved)
    data = PLOT.load_evidence(root,moved,expected_hashes=pins)
    assert [r['path'] for r in data['source_inputs']]==[f'{PLOT.EVIDENCE_ROOT}/{b}/result.json' for b in PLOT.BLOCKS]


def _landed(root):
    paths = [root/(LANDED+s) for s in SUFFIXES]
    assert all(p.is_file() for p in paths), 'fig15 integration bundle is incomplete'
    prov = PLOT._json(paths[2])
    assert [r['path'] for r in prov['outputs']]==[LANDED+s for s in SUFFIXES[:2]], 'landed output paths mismatch'
    return paths, prov


def test_landed_fig15_repo_closure_and_caption_when_present():
    paths, prov = _landed(REPO)
    PLOT.validate_repo_closure(prov,REPO)
    readme = (paths[0].parent/'README.md').read_text()
    section = readme.split(f'# `{Path(LANDED).name}` — ',1)[1].split('\n# ',1)[0]
    assert prov['caption'] in section
    hashes = section.split('## 着地 bytes の SHA-256\n',1)[1].split('\n## ',1)[0]
    for path in paths:
        rows = re.findall(rf'^- `{re.escape(path.name)}` SHA-256: `([0-9a-f]{{64}})`$',hashes,re.M)
        assert rows == [PLOT._sha256(path)]


def test_landed_fig15_rejects_missing_or_partial_bundle(tmp_path):
    global REPO
    original = REPO
    try:
        for i, present in enumerate([()] + [tuple(s for s in SUFFIXES if s != missing) for missing in SUFFIXES]):
            REPO = tmp_path/str(i)
            for s in present:
                path = REPO/(LANDED+s)
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'presence only')
            try:
                test_landed_fig15_repo_closure_and_caption_when_present()
            except AssertionError as exc:
                assert str(exc).partition('\n')[0]=='fig15 integration bundle is incomplete'
            else:
                raise AssertionError('incomplete bundle accepted')
    finally:
        REPO=original


def test_real_evidence_matches_results_document_when_root_present():
    data = PLOT.load_evidence(REPO)
    doc = (REPO/PLOT.CAPTION_SOURCE).read_text().replace('`','').replace('**','')
    section = doc.split('### 2.2 ',1)[1].split('### 2.3 ',1)[0]
    for arm in PLOT.ARMS:
        row, = [line.split('|') for line in section.splitlines() if line.startswith('| '+arm+' (')]
        cells = [s.strip() for s in row]
        f = data['arms'][arm]['formatted']
        assert cells[2:5] == [f['k_over_m'],f['rate'],f['cp95']]
        assert cells[6] == f['mean_commits']
    section = doc.split('### 2.3 ',1)[1].split('### 2.4 ',1)[0]
    for bo, c in enumerate(data['comparisons']):
        row, = [line.split('|') for line in section.splitlines() if line.startswith('| '+('主' if bo==0 else '副')+'比較 BACK_OFF=')]
        assert row[2].strip()==str(c['table']) and row[3].strip()==c['p_text']
    section = doc.split('### 2.6 ',1)[1].split('### 2.7 ',1)[0]
    for bo, r in enumerate(data['exposure_ratios']):
        row, = [line.split('|') for line in section.splitlines() if line.startswith(f'| BACK_OFF={bo} |')]
        assert row[4].strip().split(' ')[0]==r['text']
        assert [s.strip() for s in row[2:4]]==[data['arms'][a]['formatted']['mean_commits'] for a in PLOT.ARMS[2*bo:2*bo+2]]
    fig, axes = PLOT.make_figure(data)
    try:
        # Independent literals from the results document, section 2.6.
        visible = _visible(fig)
        for literal in ('BACK_OFF=0: on/off exposure ratio 0.8636',
                        'BACK_OFF=1: on/off exposure ratio 0.8450'):
            assert literal in visible, literal
        PLOT.check_figure_layout(fig,axes)
        _check_claims(PLOT._caption(data,'fig15_real'),fig)
    finally:
        PLOT.plt.close(fig)


def test_landed_fig15_external_closure_when_root_present():
    _, prov = _landed(REPO)
    PLOT.validate_external_sources(prov,(REPO/PLOT.VERBATIM_PATH).resolve())


def _run():
    started = time.monotonic()
    passed = failed = skipped = errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        node = f"{Path(__file__).name}::{test.__name__}"
        try:
            with tempfile.TemporaryDirectory(prefix="mocc-four-arm-test-") as directory:
                kwargs = {"tmp_path": Path(directory)} if "tmp_path" in inspect.signature(test).parameters else {}
                test(**kwargs)
            print(f"PASS {node}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {node}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {node}: {exc}")
            traceback.print_exc()
            failed += 1
        except Exception as exc:
            print(f"ERROR {node}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            errors += 1
    print(f"{passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
    print(f"wall seconds: {time.monotonic()-started:.3f}")
    PLOT.plt.close("all")
    _rendered.cache_clear()
    return 1 if failed or errors else 0


if __name__ == "__main__":
    sys.exit(_run())
