"""Recorded flow: real-size fixture, fail-closed layout, independent hashes."""
from __future__ import annotations
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

os.environ['MPLBACKEND'] = 'Agg'
import pytest
from matplotlib.text import Text

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'tools/plotting/plot_k2_loop_flow.py'
FLOW = REPO / 'tools/plotting/k2_loop_flow_2026-09-20.json'
spec = importlib.util.spec_from_file_location('k2_flow_under_test', SCRIPT)
PLOT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PLOT)


# Independent transcription from the frozen note §§0.1, 2.2, 2.3;
# never derive this oracle from the input JSON or generator constants.
RECORDED_PATHS = (
    ('m1', 'measurement-reflux', 'round-1.evaluation', 'round-2.parent'),
    ('m2a', 'measurement-reflux', 'round-2.evaluation', 'after-round-2.parent'),
    ('m2b', 'measurement-reflux', 'round-2.evaluation', 'round-3.parent'),
    ('d1', 'diagnosis-reflux', 'round-2.critic', 'round-3.parent'),
    ('a1', 'absent', 'round-1.critic', 'round-2.parent'),
    ('a2', 'absent', 'round-2.critic', 'after-round-2.parent'),
    ('a3', 'absent', 'round-3.critic', None),
)


def _expected_arrows():
    return [dict(zip(('id', 'kind', 'from', 'to'), row), visible=True) for row in RECORDED_PATHS]


def _raw():
    return json.loads(FLOW.read_bytes())


def _load_bad(tmp_path, raw, reason=None, root=REPO):
    path = tmp_path / 'flow.json'
    path.write_text(json.dumps(raw), encoding='utf-8')
    with pytest.raises(PLOT.FigureDataError, match=reason):
        PLOT.load_flow(root, path)


def _root(tmp_path):
    raw = _raw()
    for relative in [str(FLOW.relative_to(REPO)), raw['caption_source'], *[r['definition_path'] for r in raw['roles']]]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    return tmp_path


@pytest.fixture(scope='module')
def production():
    data = PLOT.load_flow(REPO)
    fig, layout = PLOT.make_figure(data)
    yield data, fig, layout
    PLOT.plt.close(fig)


def test_t1_real_flow_at_production_size(production):
    data, fig, layout = production
    PLOT.check_figure_layout(fig, layout)
    assert tuple(fig.get_size_inches()) == (16, 11)
    assert fig.dpi == 200 and fig.axes == []
    d = data['flow']
    assert (len(d['lanes']),len(d['columns']),len(d['roles'])) == (6,4,3)
    assert len(d['arrows']) == 7
    assert tuple(tuple(a[k] for k in ('id','kind','from','to')) for a in d['arrows']) == RECORDED_PATHS
    assert [sum(a['kind']==k for a in d['arrows']) for k in ['measurement-reflux','diagnosis-reflux','absent']] == [3,1,3]
    texts = ' '.join(t.get_text().replace('\n',' ') for t in fig.findobj(Text))
    for col in d['columns']:
        for cell in col['cells'].values():
            if cell and 'instance' in cell:
                assert cell['instance'] in texts
        e = col['cells']['evaluation']
        if e:
            for job in [e['job'],*e['refused_jobs']]:
                assert 'job '+job in texts
    assert len([m for m in layout['markers'] if m[0].get_marker()=='p']) == 11


@pytest.mark.parametrize('index',[0,1,2])
def test_t2_tools_none_mismatch_is_rejected(tmp_path,index):
    raw=_raw()
    raw['roles'][index]['tools_none']=not raw['roles'][index]['tools_none']
    _load_bad(tmp_path,raw,'tools_none mismatch')


@pytest.mark.parametrize('case',['missing-line','missing-file','non-array','duplicate-line','changed-tools'])
def test_t2_role_frontmatter_binding(tmp_path,case):
    root=_root(tmp_path)
    path=root/_raw()['roles'][0]['definition_path']
    if case=='missing-file':
        path.unlink()
    else:
        replacement={'missing-line':'', 'non-array':'tools: null', 'duplicate-line':'tools: []\ntools: []', 'changed-tools':'tools: ["Read"]'}[case]
        path.write_text(path.read_text().replace('tools: []',replacement,1))
    with pytest.raises(PLOT.FigureDataError):
        PLOT.load_flow(root)


@pytest.mark.parametrize('location', ['direction','magnitude','column-kind','arrow-kind','verdict','stop'])
def test_t3_invalid_enum_is_rejected(tmp_path,location):
    raw=_raw()
    cells=raw['columns'][0]['cells']
    target,key={'direction':(cells['planner'],'direction'), 'magnitude':(cells['planner'],'magnitude'),
                'column-kind':(raw['columns'][0],'kind'), 'arrow-kind':(raw['arrows'][0],'kind'),
                'verdict':(cells['evaluation'],'verdict'),'stop':(cells['evaluation'],'stop')}[location]
    target[key]='bogus'
    _load_bad(tmp_path,raw,'invalid enum')


@pytest.mark.parametrize('location',['top','role','lane','knowledge','column','cells','parent','planner','coder','proposal','evaluation','critic','arrow','stock','discipline'])
def test_t3_unknown_key_is_rejected(tmp_path,location):
    raw=_raw()
    cells=raw['columns'][0]['cells']
    target={'top':raw,'role':raw['roles'][0],'lane':raw['lanes'][0],'knowledge':raw['knowledge'],
            'column':raw['columns'][0],'cells':cells,**cells,'arrow':raw['arrows'][0],
            'stock':raw['stock_control'],'discipline':raw['discipline6']}[location]
    target['extra']='unexpected'
    _load_bad(tmp_path,raw,'key set')


@pytest.mark.parametrize('case',['missing-key','non-int','bool-value','low-value','high-value','value-mismatch',
    'evaluated','not-a-round-evaluation','arrow-from','arrow-to','anchor','absent-anchor',
    'diagnosis_fields','planner_keys','coder_keys','caption-source','percent','throughput','latency','assignment',
    'discipline6-form','discipline6-bool','schema','iso-date','reference-format','reference-duplicate',
    'reference-unused','roles-order','definition-path','lanes-order','columns-order','column-number',
    'certified','anomalies-none','job-duplicate','instance-duplicate','arrow-id-duplicate',
    'arrow-null','evaluated-null','not-a-round-kind','round-critic-null','round-date-null','diagnosis-column',
    'arrow-count-four'])
def test_t3_invalid_json_without_drawing(tmp_path,case):
    raw=_raw()
    c=raw['columns'][0]['cells']
    reason=None
    if case=='missing-key': del c['planner']['direction']
    elif case in ('non-int','bool-value','low-value','high-value'):
        c['coder']['value']={'non-int':20.0,'bool-value':True,'low-value':0,'high-value':1001}[case]
    elif case=='value-mismatch': c['proposal']['value']=21
    elif case=='evaluated': c['proposal']['evaluated']=False
    elif case=='not-a-round-evaluation': raw['columns'][2]['cells']['evaluation']=copy.deepcopy(c['evaluation'])
    elif case in ('arrow-from','arrow-to'): raw['arrows'][0][case[6:]]='missing.parent'
    elif case=='anchor': raw['knowledge']['source_anchor']='section 1.2'
    elif case=='absent-anchor': raw['knowledge']['source_anchor']='§999'
    elif case in ('diagnosis_fields','planner_keys','coder_keys'): raw[case]=raw[case][:-1]
    elif case=='caption-source': raw['caption_source']='wrong.md'
    elif case=='discipline6-form':
        c['planner']['discipline6']['form']='structured-field'; reason='discipline6 form mismatch'
    elif case=='discipline6-bool':
        c['coder']['discipline6']['instruction_like_detected']='false'; reason='bool required'
    elif case=='schema': raw['schema']='other'; reason='schema mismatch'
    elif case=='iso-date': raw['figure_created']='20/09/2026'; reason='ISO date required'
    elif case=='reference-format': raw['reference_ids'].append('bad_id'); reason='reference_ids format'
    elif case=='reference-duplicate': raw['reference_ids'].append('K2'); reason='duplicate reference_ids'
    elif case=='reference-unused': raw['reference_ids'].append('Z999'); reason='unused reference_ids'
    elif case=='roles-order': raw['roles'].reverse(); reason='role order/name mismatch'
    elif case=='definition-path': raw['roles'][0]['definition_path']='wrong.md'; reason='definition_path mismatch'
    elif case=='lanes-order': raw['lanes'][1],raw['lanes'][2]=raw['lanes'][2],raw['lanes'][1]; reason='lane order mismatch'
    elif case=='columns-order': raw['columns'].reverse(); reason='column order mismatch'
    elif case=='column-number': raw['columns'][0]['number']=True; reason='column number mismatch'
    elif case in ('certified','anomalies-none'):
        c['evaluation'][case.replace('-','_')]=False; reason='correctness flags must be true'
    elif case=='job-duplicate': c['evaluation']['refused_jobs']=[c['evaluation']['job']]; reason='duplicate job'
    elif case=='instance-duplicate': raw['columns'][1]['cells']['planner']['instance']=c['planner']['instance']; reason='duplicate instance'
    elif case=='arrow-id-duplicate': raw['arrows'][1]['id']=raw['arrows'][0]['id']; reason='duplicate arrow id'
    elif case=='arrow-null': raw['arrows'][0]['to']=None; reason='arrow to missing'
    elif case=='evaluated-null':
        raw['columns'][2]['cells']['proposal']['evaluated']=True
        reason='evaluated mismatch'
    elif case=='not-a-round-kind':
        raw['columns'][2]['kind']='round'; reason='evaluation kind mismatch'
    elif case=='round-critic-null': c['critic']=None; reason='evaluation kind mismatch'
    elif case=='round-date-null': raw['columns'][0]['date_evaluation']=None; reason='evaluation kind mismatch'
    elif case=='diagnosis-column': c['parent']['has_diagnosis']=True; reason='diagnosis column mismatch'
    elif case=='arrow-count-four':
        extra=copy.deepcopy(raw['arrows'][0]); extra['id']='extra'; raw['arrows'].append(extra)
        reason='arrow kind count must be between one and three'
    else: raw['knowledge']['label']={'percent':'38%','throughput':'10 tps','latency':'2 µs','assignment':'A=0.58'}[case]
    _load_bad(tmp_path,raw,reason)


@pytest.mark.parametrize('case',['duplicate','nan','infinity','negative-infinity'])
def test_t3_json_parser_rejects_noncanonical_values(tmp_path,case):
    text=FLOW.read_text()
    if case=='duplicate':
        text=text.replace('"schema":','"schema": "duplicate", "schema":',1)
    else:
        text=text.replace('"value": 20','"value": '+{'nan':'NaN','infinity':'Infinity','negative-infinity':'-Infinity'}[case],1)
    path=tmp_path/'flow.json'
    path.write_text(text)
    with pytest.raises(PLOT.FigureDataError,match='duplicate key|non-finite'):
        PLOT.load_flow(REPO,path)


@pytest.mark.parametrize('case', ['destination', 'missing', 'reordered'])
def test_t3_frozen_arrow_paths_are_required(tmp_path,case):
    raw=_raw()
    if case=='destination':
        raw['arrows'][0]['to']='round-3.parent'
    elif case=='missing':
        raw['arrows'].pop(0)
    else:
        raw['arrows'][0],raw['arrows'][1]=raw['arrows'][1],raw['arrows'][0]
    _load_bad(tmp_path,raw,'frozen arrow paths mismatch')


def test_t3_non_unique_anchor_is_rejected(tmp_path):
    root=_root(tmp_path)
    path=root/_raw()['caption_source']
    source=path.read_text()
    heading=next(line for line in source.splitlines() if line.startswith('### 1.2 '))
    path.write_text(source+'\n'+heading+'\n')
    with pytest.raises(PLOT.FigureDataError,match='exactly one line'):
        PLOT.load_flow(root)


@pytest.mark.parametrize('text',['38%','10 tps','2 µs','A=0.58','three runs','applied twice','３８％','١٢','K2suffix','job 1216.5','1216'])
def test_t4_free_text_rejects_quantities(text):
    with pytest.raises(PLOT.FigureDataError):
        PLOT.check_display_text(text,{'K2','planner-1'},{'1216'})


def test_t4_declared_identifiers_are_accepted():
    PLOT.check_display_text('K2 / planner-1; job 1216',{'K2','planner-1'},{'1216'})


@contextmanager
def _moved_text(production, kind):
    data,fig,layout=production
    items={r['id']:r['texts'][0] for r in layout['items']}
    text=items['after-round-2.evaluation'] if kind=='arrow-crossing' else items['arrow-a3']
    old=(text.get_position(),layout['owners'][text])
    # Preserve every registered string; canvas ownership isolates geometry.
    layout['owners'][text]='canvas'
    if kind=='overlap':
        text.set_position(items['arrow-a2'].get_position())
    elif kind=='escape':
        text.set_position((1.2,1.2))
    else:
        arrow=next(a for a in layout['arrows'] if a['id']=='m1')['artist']
        text.set_position((arrow.get_xdata()[1]-.004,.520))
    try:
        assert PLOT._drawn_items(data,layout)==PLOT._display_items(data['flow'])
        yield data,fig,layout
    finally:
        text.set_position(old[0]); layout['owners'][text]=old[1]


@pytest.fixture
def collision(production):
    with _moved_text(production,'overlap') as result:
        yield result


def test_t5_overlap_is_a_layout_error(collision):
    _,fig,layout=collision
    with pytest.raises(PLOT.FigureLayoutError,match='text overlap'):
        PLOT.check_figure_layout(fig,layout)


def test_t5_escape_is_a_layout_error(production):
    with _moved_text(production,'escape') as (_,fig,layout):
        with pytest.raises(PLOT.FigureLayoutError,match='text escape'):
            PLOT.check_figure_layout(fig,layout)


def test_t5_arrow_crossing_text_is_a_layout_error(production):
    with _moved_text(production,'arrow-crossing') as (_,fig,layout):
        with pytest.raises(PLOT.FigureLayoutError,match='arrow crossing text'):
            PLOT.check_figure_layout(fig,layout)


@pytest.mark.parametrize('kind',['overlap','escape','arrow-crossing'])
def test_t6_publish_runs_layout_check(production,tmp_path,kind):
    with _moved_text(production,kind) as (data,fig,layout):
        reason={'overlap':'text overlap','escape':'text escape','arrow-crossing':'arrow crossing text'}[kind]
        with pytest.raises(PLOT.FigureLayoutError,match=reason):
            PLOT._publish_outputs(fig,layout,tmp_path/'new'/'fig12_collision',data,[])
    assert not list(tmp_path.iterdir())


def _cli(prefix):
    return subprocess.run([sys.executable,str(SCRIPT),'--repo-root',str(REPO),str(prefix)],
                          capture_output=True,text=True,
                          env={**os.environ,'MPLBACKEND':'Agg','PYTHONDONTWRITEBYTECODE':'1'})


@pytest.fixture(scope='module')
def bundle(tmp_path_factory):
    directory=tmp_path_factory.mktemp('k2-flow')
    prefix=directory/'fig12_test'
    result=_cli(prefix)
    assert result.returncode==0,result.stderr
    paths=[Path(str(prefix)+s) for s in ('.png','.pdf','.provenance.json')]
    return prefix,paths,json.loads(paths[-1].read_bytes())


def test_t7_cli_outputs_and_independent_hashes(bundle):
    prefix,paths,prov=bundle
    assert set(prefix.parent.iterdir())==set(paths)
    assert all(stat.S_IMODE(p.stat().st_mode)==0o644 for p in paths)
    assert paths[0].read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert paths[1].read_bytes().startswith(b'%PDF-')
    assert set(prov)==set('schema generated_utc figure_created caption_source inputs generator outputs drawn_items arrows roles caption argv versions'.split())
    assert prov['schema']=='izanagi-k2-loop-flow-figure-provenance/v1'
    assert [r['kind'] for r in prov['inputs']]==['flow','caption_source','role_definition','role_definition','role_definition']
    for row in prov['inputs']+[prov['generator']]+prov['outputs']:
        assert row['sha256']==hashlib.sha256((REPO/row['path']).read_bytes()).hexdigest()
    for role in prov['roles']:
        raw=(REPO/role['definition_path']).read_bytes()
        assert role['sha256']==hashlib.sha256(raw).hexdigest()
        tools=re.search(r'^tools: (.+)$',raw.decode().split('---')[1],re.M)[1]
        assert role['tools_none']==(json.loads(tools)==[])
    assert prov['arrows']==_expected_arrows()
    assert prov['argv']==['python3','tools/plotting/plot_k2_loop_flow.py','--repo-root',str(REPO),str(prefix)]
    assert set(prov['versions'])=={'matplotlib','numpy'}
    before=[p.read_bytes() for p in paths]
    again=_cli(prefix)
    assert again.returncode==2 and 'output already exists' in again.stderr
    assert before==[p.read_bytes() for p in paths]


def test_t7_caption_source_hash_is_independent(bundle):
    prov=bundle[2]
    source=_raw()['caption_source']
    assert prov['caption_source']=={'path':source,'sha256':hashlib.sha256((REPO/source).read_bytes()).hexdigest()}


def test_t7_drawn_items_match_flow(production,bundle):
    data,_,layout=production
    raw=_raw()
    items={r['id']:r['text'] for r in bundle[2]['drawn_items']}
    expected_ids={'title','subtitle','knowledge','stock_control','legend-arrows','legend-r6',
                  'footnote-source','footnote-certified','footnote-discipline'}
    for lane in raw['lanes']:
        ident='lane-'+lane['id']
        expected_ids.add(ident)
        roles={r['id']:r for r in raw['roles']}
        source=roles.get(lane['id'],lane)
        assert items[ident]==' '.join([source.get('name',source['label']),source['sublabel']])
    for key in ('knowledge','stock_control'):
        assert items[key]==' '.join([raw[key]['label'],raw[key]['sublabel']])
    for a in raw['arrows']:
        ident='arrow-'+a['id']
        expected_ids.add(ident)
        expected=' '.join([a['id']+':',a['from'],'→',a['to'] or 'no destination',a['label']])
        if a['kind']=='diagnosis-reflux':
            expected+=' k2_critic_diagnosis: '+', '.join(raw['diagnosis_fields'])
        assert items[ident]==expected
    for col in raw['columns']:
        expected_ids.add(col['id'])
        heading=f"Round {col['number']}" if col['kind']=='round' else f"After round {col['number']} (not a round)"
        evaluation='evaluation '+col['date_evaluation']+' (job log)' if col['date_evaluation'] else 'evaluation: none'
        assert items[col['id']]==' '.join([heading,'proposal',col['date_proposal'],'(per round records) ·',evaluation])
        for lane,c in col['cells'].items():
            expected_ids.add(col['id']+'.'+lane)
            text=items[col['id']+'.'+lane]
            boundary='' if not c or lane not in ('planner','coder','critic') else (' instruction-like content: detected (self-report)' if c['discipline6']['instruction_like_detected'] else ' instruction-like content: none detected (self-report)')
            if c is None: assert text==('not evaluated' if lane=='evaluation' else 'no critic')
            elif lane=='planner': assert text==f"{c['instance']} {c['direction']} / {c['magnitude']}"+boundary
            elif lane=='coder': assert text==f"{c['instance']} synthesizes one backoff literal"+boundary
            elif lane=='parent':
                keys=[]
                for role in ('planner','coder'):
                    keys += [role+':',', '.join(raw[role+'_keys'])]
                    if c['has_diagnosis']: keys += ['+ k2_critic_diagnosis']
                assert text==' '.join(keys+[c['sublabel']])
            elif lane=='proposal':
                assert text==' '.join([c['instance'],f"backoff literal {c['value']}",'in the run-card known set' if c['known_value'] else 'outside the run-card known set','evaluated' if c['evaluated'] else 'not evaluated',c['sublabel']])
            elif lane=='critic': assert text==' '.join([c['instance'],c['attribution'],c['recommend']])+boundary
            else:
                parts=['job '+c['job']]
                if c['refused_jobs']: parts+=['refused at preflight: '+', '.join('job '+j for j in c['refused_jobs'])]
                parts+=['verdict serializable; certified; no anomaly; stop: continue',c['sublabel']]
                assert text==' '.join(parts)
    assert set(items)==expected_ids
    assert len(items)==len(bundle[2]['drawn_items'])
    assert items['title']=='K2 manual loop: data flow over three recorded rounds (schematic; no performance values)'
    basename=Path(raw['caption_source']).name
    assert items['subtitle']=='Source: frozen results note '+basename+' (SHA-256 in provenance); figure created '+raw['figure_created']
    assert items['legend-arrows']=='Solid: measurement reflux; dashed: diagnosis reflux; dotted with cross: absent path; thin: within-column flow; dashed box: not a round.'
    assert items['legend-r6']=='R6: self-reported; shield: none detected; red X: detected. '+raw['discipline6']['label']+': '+raw['discipline6']['definition']+'; coder: structured field data_boundary_report.instruction_like_content_detected: false in all four coder outputs; no role reported detection'
    assert items['footnote-source']=='Read from the frozen results note '+basename+'; no performance values are drawn and the three runs are not compared.'
    assert items['footnote-certified']=='Certified means the trace-enabled verify run found the trace serializable with no anomaly; it is not a performance certification.'
    assert items['footnote-discipline']=='Discipline-six marks are role self-reports, not a mechanical gate; causal effects of knowledge or diagnosis are not claimed.'
    changed=copy.deepcopy(data)
    changed['flow']['columns'][0]['cells']['parent']['sublabel']='changed after rendering'
    with pytest.raises(PLOT.FigureDataError,match='drawn_items disagree'):
        PLOT.build_provenance(changed,layout,[],[])


def test_t7_caption_verbatim_and_limits(bundle):
    caption=bundle[2]['caption']
    assert caption.startswith('Figure 12. Data flow of the K2 manual synthesis loop over three recorded rounds, read from the frozen results note '+Path(_raw()['caption_source']).name+'.')
    clauses=[
        'This is a schematic of recorded data flow; no performance values are drawn and the three runs are not compared.',
        'Certified means only that the trace-enabled verify run found the observed trace serializable with no anomaly; it is not a performance certification and not a choice among candidates.',
        'The planner and coder role definitions declare no tools (structural blockade); critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation.',
        'Discipline-six marks are role self-reports that external inputs contained no instruction-like strings; none is reported in the recorded rounds. Their form differs by role and they are not a mechanical gate.',
        'No causal effect of the knowledge source or of the diagnosis on the proposed values is claimed: each condition was launched once, without a control.',
        'The same-job stock control was not achieved and awaits a ruling; proposal values are backoff literals, not results.',
        "Role launch times, inline delivery, proposal dates, and the fine ordering of steps rest on each round's records; saved prompts and inputs are not proof of delivery.",
        'This figure does not judge whether B-6 is met; the tool-less declaration concerns tool access only, and leak control is not complete.']
    for clause in clauses: assert clause in caption
    for word in ['improvement','better','faster','converge','optimal','performance certified','causal effect of the diagnosis was','%',' tps']:
        assert word not in caption
    for key in ('planner_keys','coder_keys','diagnosis_fields'):
        assert ', '.join(_raw()[key]) in caption


def test_t7_arrows_bind_artists_and_caption(production,bundle):
    data,fig,layout=production
    raw=_raw()
    expected=_expected_arrows()
    assert tuple(tuple(a[k] for k in ('id','kind','from','to')) for a in raw['arrows']) == RECORDED_PATHS
    drawn=[a for a in layout['arrows'] if a['kind']!='flow']
    assert len(drawn)==len(expected)
    for a,row in zip(drawn,expected):
        assert {k:a[k] for k in ('id','kind','from','to')}=={k:row[k] for k in ('id','kind','from','to')}
        assert a['artist'].get_visible() and a['artist'] in fig.artists
        assert a['head'].get_visible() and a['head'] in fig.artists
        source=layout['regions'][row['from']]
        assert tuple(a['artist'].get_xydata()[0])==(source.x1,source.y0+.007)
        end=a['artist'].get_xydata()[-1]
        if row['to'] is None:
            assert tuple(end)==(source.x1+.02,source.y0+.007)
            assert a['head'].get_marker()=='x'
        else:
            dest=layout['regions'][row['to']]
            assert end[0]==dest.x0-.001 and dest.y0 < end[1] < dest.y1
    assert bundle[2]['arrows']==expected
    caption=bundle[2]['caption']
    assert ('Measurement reflux occurred twice between the recorded rounds '
            '(the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round), '
            'and diagnosis reflux occurred once (the second critic into the third-round inputs as the typed key k2_critic_diagnosis '
            'with fields attribution, recommend, avoid, uncertainty, data_boundary, source_sha256, identical for planner and coder). '
            'Three measurement arrows are drawn because the second evaluation feeds both the unevaluated proposal and the third-round proposal; '
            'three dotted arrows mark absent paths.') in caption
    artist=drawn[0]['artist']
    artist.set_visible(False)
    try:
        with pytest.raises(PLOT.FigureDataError,match='drawn arrows disagree'):
            PLOT.build_provenance(data,layout,[],[])
    finally: artist.set_visible(True)
    index=layout['arrows'].index(drawn[0])
    removed=layout['arrows'].pop(index)
    try:
        with pytest.raises(PLOT.FigureDataError,match='drawn arrows disagree'):
            PLOT.build_provenance(data,layout,[],[])
    finally: layout['arrows'].insert(index,removed)


@pytest.mark.parametrize('flipped_role', ['coder', 'planner', 'critic'])
def test_t7_discipline6_flip_changes_marker_and_items(production,tmp_path,flipped_role):
    original,_,original_layout=production
    raw=_raw()
    raw['columns'][0]['cells'][flipped_role]['discipline6']['instruction_like_detected']=True
    path=tmp_path/'flow.json'
    path.write_text(json.dumps(raw))
    changed=PLOT.load_flow(REPO,path)
    fig,layout=PLOT.make_figure(changed)
    try:
        PLOT.check_figure_layout(fig,layout)
        before={r['id']:r['text'] for r in PLOT._drawn_items(original,original_layout)}
        after={r['id']:r['text'] for r in PLOT._drawn_items(changed,layout)}
        key='round-1.'+flipped_role
        assert before[key].endswith('instruction-like content: none detected (self-report)')
        assert after[key]==before[key].replace('none detected (self-report)', 'detected (self-report)')
        coder_summary='true in at least one coder output' if flipped_role=='coder' else 'false in all four coder outputs'
        assert 'data_boundary_report.instruction_like_content_detected: '+coder_summary+';' in after['legend-r6']
        assert after['legend-r6'].endswith('at least one role reported detection')
        assert before['legend-r6'].endswith('no role reported detection')
        before_caption=PLOT.build_provenance(original,original_layout,[],[])['caption']
        after_caption=PLOT.build_provenance(changed,layout,[],[])['caption']
        assert 'none is reported in the recorded rounds.' in before_caption
        assert after_caption==before_caption.replace('none is reported in the recorded rounds.', 'at least one recorded output reports detection.')
        for col in raw['columns']:
            for role in ('planner','coder','critic'):
                cell=col['cells'][role]
                if cell is None: continue
                key=col['id']+'.'+role
                marker=next(m for m,owner in layout['markers'] if owner==key)
                expected={False:('p','#476b55'),True:('X','#b52222')}[cell['discipline6']['instruction_like_detected']]
                assert (marker.get_marker(),marker.get_color())==expected
                assert marker.get_markersize()==7
                assert marker.get_ydata()[0]==layout['regions'][key].y1-.009
    finally: PLOT.plt.close(fig)


def test_t8_cli_rejects_invalid_prefix(tmp_path):
    result=_cli(tmp_path/'bad_prefix')
    assert result.returncode==2 and 'output prefix' in result.stderr
    assert not list(tmp_path.iterdir())


def test_landed_fig12_bundle_when_present():
    prefix=REPO/'docs/paper-story/figures/fig12_k2_manual_loop_dataflow'
    paths=[Path(str(prefix)+s) for s in ('.png','.pdf','.provenance.json')]
    assert all(p.is_file() for p in paths), 'fig12 bundle not landed'
    prov=json.loads(paths[-1].read_bytes())
    assert prov['caption_source']['sha256']==hashlib.sha256((REPO/_raw()['caption_source']).read_bytes()).hexdigest()
    readme=(prefix.parent/'README.md').read_text()
    assert prov['caption'] in readme
    section=re.search(r'^# .*fig12[^\n]*\n(.*?)(?=^# |\Z)',readme,re.M|re.S)
    assert section, 'fig12 section missing'
    assert '着地 bytes の SHA-256' in section[0]
    for path in paths:
        assert f'- `{path.name}` SHA-256: `{hashlib.sha256(path.read_bytes()).hexdigest()}`' in section[0]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
