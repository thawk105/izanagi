"""Tier0 gateway fixtures and opt-in compute-node tests of the actual insertion.

Live nodes require IZANAGI_B5_TIER0_TEST_RECEIPT and
IZANAGI_B5_TIER0_TEST_OUTPUT_ROOT in a scratch submit-tree with
the normal execution authorization. They build actual CCBench, never replace
buildcache, evidence/admission, run_once, parsers, sidecar writer or classifier.
"""
from __future__ import annotations

import ast
import contextlib
from dataclasses import replace
import hashlib
import inspect
import json
import os
import subprocess
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import b5_generator_contrast as B
from orchestrator.campaign import p3_s4_loop as L


GOOD = "abort_counts_:\t1\ncommit_counts_:\t7\nthroughput[tps]:\t7\n"


@pytest.fixture
def smoke_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("IZANAGI_BENCH_LOCK", str(tmp_path / "bench.lock"))
    monkeypatch.setenv("FLAGS_ycsb_rratio", "20")
    return SimpleNamespace(clocks_per_us=2100, numactl=())


def executable(tmp_path, *, output=GOOD, rc=0, delay=0, require_lock=False):
    binary = tmp_path / "perf-fixture"
    capture = tmp_path / "observed.json"
    binary.write_text(f"#!{sys.executable}\n" + textwrap.dedent(f"""
        import fcntl, json, os, pathlib, sys, time
        locked = False
        with open(os.environ['IZANAGI_BENCH_LOCK'], 'a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                locked = True
        pathlib.Path({str(capture)!r}).write_text(json.dumps({{
            'argv': sys.argv, 'locked': locked,
            'flags_env': sorted(k for k in os.environ if k.startswith('FLAGS_')),
            'log_exists': pathlib.Path('log').is_dir(), 'cwd': os.getcwd(),
        }}))
        if {require_lock!r} and not locked:
            sys.exit(47)
        time.sleep({delay!r})
        sys.stdout.write({output!r})
        sys.exit({rc!r})
    """))
    binary.chmod(0o755)
    return binary, capture


def test_smoke_exact_argv_and_parser(tmp_path, smoke_environment):
    binary, capture = executable(tmp_path)
    result = L._run_b5_tier0_smoke(str(binary), smoke_environment)
    observed = json.loads(capture.read_text())
    assert observed['argv'] == [str(binary), '--thread_num=4', '--ycsb_tuple_num=200',
                                '--extime=1', '--ycsb_rratio=50', '--ycsb_zipf_skew=0.9',
                                '--ycsb_rmw=true', '--ycsb_max_ope=5', '--clocks_per_us=2100']
    assert observed['flags_env'] == []
    assert observed['log_exists'] is True
    assert not Path(observed['cwd']).exists()
    assert (result['status'], result['reason'], result['error']) == ('passed', None, None)
    smoke = result['smoke']
    assert (smoke['commits'], smoke['aborts'], smoke['returncode'], smoke['throughput_positive']) == (7, 1, 0, True)
    assert smoke['timeout_s'] == 32
    assert set(smoke) == {'flags', 'timeout_s', 'returncode', 'wall_s', 'commits', 'aborts', 'throughput_positive'}


@pytest.mark.parametrize('output,rc', [
    pytest.param(GOOD, 7, id='nonzero'),
    pytest.param('', 0, id='empty'),
    pytest.param('abort_counts_:\t1\ncommit_counts_:\t0\nthroughput[tps]:\t7\n', 0, id='zero-commit'),
    pytest.param('abort_counts_:\t1\ncommit_counts_:\t7.0\nthroughput[tps]:\t7\n', 0, id='invalid-counter'),
    pytest.param('abort_counts_:\t1\ncommit_counts_:\t7\nthroughput[tps]:\t0\n', 0, id='zero-throughput'),
    pytest.param('abort_counts_:\t1\ncommit_counts_:\t7\nthroughput[tps]:\t1e999\n', 0, id='infinite-throughput'),
    pytest.param('abort_counts_:\t1\ncommit_counts_:\t7\nthroughput[tps]:\tnan\n', 0, id='nan-throughput'),
])
def test_smoke_rejects_nonzero_or_invalid_output(tmp_path, smoke_environment, output, rc):
    binary, _ = executable(tmp_path, output=output, rc=rc)
    result = L._run_b5_tier0_smoke(str(binary), smoke_environment)
    assert (result['status'], result['reason'], result['smoke']['returncode']) == ('rejected', 'smoke-failed', rc)


def test_smoke_parser_fallback(tmp_path, smoke_environment):
    binary, _ = executable(tmp_path, output='abort_counts_:\t1\ncommit_counts_:\t7\nactual_extime:\t1\n')
    result = L._run_b5_tier0_smoke(str(binary), smoke_environment)
    assert (result['status'], result['smoke']['throughput_positive']) == ('passed', True)


def test_smoke_timeout(tmp_path, monkeypatch, smoke_environment):
    assert L.B5_TIER0_CONTRACT['timeout_s'] == 32
    # Real subprocess timeout; omission makes the executable finish successfully.
    monkeypatch.setitem(L.B5_TIER0_CONTRACT, 'timeout_s', 0.05)
    binary, _ = executable(tmp_path, delay=0.5)
    result = L._run_b5_tier0_smoke(str(binary), smoke_environment)
    assert (result['status'], result['reason'], result['smoke']['returncode']) == ('rejected', 'smoke-timeout', None)
    assert result['smoke']['timeout_s'] == 0.05


def test_smoke_uses_bench_lock(tmp_path, smoke_environment):
    # The executable is a separate process using the real flock, not a lock spy.
    binary, capture = executable(tmp_path, require_lock=True)
    result = L._run_b5_tier0_smoke(str(binary), smoke_environment)
    assert result['status'] == 'passed'
    assert json.loads(capture.read_text())['locked'] is True


def _live_args(tmp_path, monkeypatch):
    receipt = os.environ.get('IZANAGI_B5_TIER0_TEST_RECEIPT')
    if not receipt:
        pytest.skip('parent compute-node check: set IZANAGI_B5_TIER0_TEST_RECEIPT in scratch submit-tree')
    assert Path(receipt).is_file()
    output_root = os.environ['IZANAGI_B5_TIER0_TEST_OUTPUT_ROOT']
    assert Path(output_root).is_absolute()
    # conftest deliberately clears the ordinary output-root environment.
    monkeypatch.setenv('IZANAGI_EXPLORATION_OUTPUT_ROOT', output_root)
    sidecar = tmp_path / 'sidecar'
    sidecar.mkdir()
    proposal = tmp_path / 'proposal.json'
    proposal.write_text(json.dumps(B.machine_proposal_document('random', 20, {'preimage': 'tier0-live-fixture'})))
    # A fresh physical identity, never an expected hash baked into the test.
    cohort = 'tier0-test-' + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:16]
    key = B.slot_key(cohort, 'random', 'write-heavy', 1, 'search', 1, 0)
    args = ['--run-iteration', str(proposal), '--machine-generated-proposal',
            '--isolate-worktree', '--fetchcontent-prebuild-receipt', receipt,
            '--calibrated-perf', '--perf-workload', 'write-heavy', '--verify-performance',
            '--b5-slot', key, '--b5-sidecar-dir', str(sidecar)]
    return args, sidecar


class _PipelineBoundary(Exception):
    pass


@pytest.fixture(params=['legacy', 'v2'])
def insertion_case(tmp_path, monkeypatch, smoke_environment, request):
    """Prepare the CLI seam; keep insertion, gateway, writer and driver real."""
    from orchestrator.campaign import patchharness, p2_2
    from orchestrator.calibrator import runner

    layout = L.CampaignLayout(str(tmp_path / 'campaign'))
    sub = tmp_path / 'checkout'
    source = sub / L.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text('''#pragma once
// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
#if BACKOFF_FIXED >= 0
double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
''')
    sidecar = tmp_path / 'sidecar'
    sidecar.mkdir()
    proposal = tmp_path / 'proposal.json'
    proposal.write_text(json.dumps(B.machine_proposal_document(
        'random', 20, {'preimage': 'tier0-insertion-fixture'})))
    site = L.site_policy.OTHER if request.param == 'legacy' else L.site_policy.PEGASUS_COMPUTE
    # Both branches use an active contract for environment binding and smoke.
    # OTHER still selects legacy build: no env_contract enters campaign_options.
    contract = replace(L.env_contract.lookup(
        L._SITE_ENV_TAGS[L.site_policy.PEGASUS_COMPUTE]), numactl=())
    monkeypatch.setitem(L._SITE_ENV_TAGS, site, contract.env_tag)
    monkeypatch.setattr(L, '_repo_root', lambda: str(tmp_path))
    monkeypatch.setattr(L, '_current_site', lambda: site)
    monkeypatch.setattr(L, '_lookup', lambda _tag: contract)
    monkeypatch.setattr(L, 'exploration_campaign_layout', lambda _cid: layout)
    monkeypatch.setattr(p2_2, '_assert_single_tenant', lambda: None)
    monkeypatch.setattr(patchharness, 'assert_pinned_clean', lambda *_a: None)
    monkeypatch.setattr(patchharness, 'checkout', lambda *_a, **_k: contextlib.nullcontext(str(sub)))
    monkeypatch.setattr(patchharness, 'applied', lambda *_a: contextlib.nullcontext())
    monkeypatch.setattr(L, '_require_condition_gate', lambda *_a, **_k: None)
    # Identity recovery precedes Tier0 in both drive_iteration and
    # _run_one_iteration_resolved. Keep its HEAD-blob check outside this seam
    # so even a comment-only mutation of p3_s4_loop.py can reach the insertion.
    # campaign_id/canonical_preimage and sidecar payloads remain real: they
    # serialize cfg without capturing or verifying a contract-loader binding.
    monkeypatch.setattr(L.ident, 'ensure_resumable_attempts', lambda *_a, **_k: None)
    case = SimpleNamespace(
        layout=layout, sidecar=sidecar, builds=[], events=[], gateway=[], outcomes=[],
        build_error=None, preparation_error=None, preparations=0,
        api='build' if request.param == 'legacy' else 'build_v2',
    )
    binaries = {}
    captures = {}
    for trace in (False, True):
        directory = tmp_path / ('trace' if trace else 'perf')
        directory.mkdir()
        # The trace executable leaves its own capture and fails if launched.
        binaries[trace], captures[trace] = executable(
            directory, rc=91 if trace else 0, require_lock=True)
    case.binaries, case.captures = binaries, captures

    def prepare(*_a, **_k):
        case.preparations += 1
        if case.preparation_error is not None:
            raise case.preparation_error
        return SimpleNamespace(src_token='fixture-source'), object(), 'cc', 'c++'

    def build(api, *_a, trace, **_k):
        case.builds.append((api, trace))
        case.events.append('build')
        if case.build_error is not None:
            raise case.build_error
        binary = binaries[trace]
        return SimpleNamespace(binary=str(binary), trace=trace, cached=False,
                               bin_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())

    monkeypatch.setattr(L, '_b5_tier0_build_inputs', prepare)
    monkeypatch.setattr(L.buildcache, 'build', lambda *a, **k: build('build', *a, **k))
    monkeypatch.setattr(L.buildcache, 'build_v2', lambda *a, **k: build('build_v2', *a, **k))

    def campaign(*_a, **_k):
        case.events.append('campaign')
        assert (sidecar / 'pipeline-submitted.json').is_file()
        raise _PipelineBoundary

    monkeypatch.setattr(L, 'run_campaign', campaign)
    case.args = ['--run-iteration', str(proposal), '--machine-generated-proposal',
                 '--isolate-worktree', '--calibrated-perf', '--perf-workload', 'balanced',
                 '--verify-performance', '--b5-slot', 'b5-generator-contrast-v1|tier0-fixture',
                 '--b5-sidecar-dir', str(sidecar)]

    def observe(frame, event, arg):
        # Observe real code objects; do not substitute any mechanism under test.
        code = frame.f_code
        if code is L._run_b5_tier0_smoke.__code__ and event == 'call':
            case.events.append('smoke')
            assert not (sidecar / 'tier0.json').exists()
            assert not (sidecar / 'pipeline-submitted.json').exists()
        if code is runner.run_once.__code__ and event == 'call':
            case.gateway.append(frame.f_locals['binary'])
        if code is L._write_b5_sidecar.__code__:
            name = frame.f_locals['name']
            if name in {'tier0.json', 'pipeline-submitted.json'}:
                if event == 'call' and name == 'pipeline-submitted.json':
                    assert json.loads((sidecar / 'tier0.json').read_text())['status'] == 'passed'
                if event == 'return':
                    assert (sidecar / name).is_file()
                    case.events.append(name)
        if code is L.drive_iteration.__code__ and event == 'return' and arg is not None:
            case.outcomes.append(dict(arg))

    @contextlib.contextmanager
    def observing():
        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            yield
        finally:
            sys.setprofile(previous)

    case.observing = observing
    return case


def test_insertion_build_smoke_sidecar_submission_order(insertion_case):
    c = insertion_case
    with c.observing(), pytest.raises(_PipelineBoundary):
        L.main(c.args)
    assert c.events == ['build', 'smoke', 'tier0.json', 'pipeline-submitted.json', 'campaign']
    assert c.preparations == 1
    assert c.builds == [(c.api, False)]
    assert c.gateway == [str(c.binaries[False])]
    assert json.loads(c.captures[False].read_text())['argv'][0] == str(c.binaries[False])
    assert json.loads(c.captures[False].read_text())['locked'] is True
    assert not c.captures[True].exists()
    tier0 = json.loads((c.sidecar / 'tier0.json').read_text())
    assert (tier0['status'], tier0['reason']) == ('passed', None)
    assert tier0['build'] == dict(
        trace=False, binary=str(c.binaries[False]), cached=False,
        bin_sha256=hashlib.sha256(c.binaries[False].read_bytes()).hexdigest())


@pytest.mark.parametrize('failure', ['smoke', 'runtime', 'subprocess'])
def test_insertion_rejection_rc3_no_submission_wal_or_digest(insertion_case, failure):
    c = insertion_case
    if failure == 'smoke':
        executable(c.binaries[False].parent, rc=7, require_lock=True)
    else:
        kind = RuntimeError if failure == 'runtime' else subprocess.SubprocessError
        c.build_error = kind('fixture build failure')
    with c.observing():
        assert L.main(c.args) == 3
    assert c.builds == [(c.api, False)]
    assert c.preparations == 1
    assert c.events == (['build', 'smoke', 'tier0.json'] if failure == 'smoke'
                        else ['build', 'tier0.json'])
    assert len(c.outcomes) == 1
    assert c.outcomes[0]['outcome'] == 'rejected-tier0'
    assert c.outcomes[0]['critic_digest_generated'] is False
    tier0 = json.loads((c.sidecar / 'tier0.json').read_text())
    assert tier0['status'] == 'rejected'
    assert tier0['reason'] == ('smoke-failed' if failure == 'smoke' else 'build-error')
    if failure == 'smoke':
        assert tier0['smoke']['returncode'] == 7
        assert c.gateway == [str(c.binaries[False])]
        assert c.captures[False].is_file()
    else:
        assert tier0['build'] is None and tier0['smoke'] is None
        assert tier0['error'] == f'{type(c.build_error).__name__}: {c.build_error}'
        assert c.gateway == [] and not c.captures[False].exists()
    assert not c.captures[True].exists()
    assert not (c.sidecar / 'pipeline-submitted.json').exists()
    assert not Path(c.layout.root, 's4_loop_digest.txt').exists()
    assert not Path(c.layout.root, 'runs/wal.jsonl').exists()
    state = L.load_loop_state(c.layout)
    assert state.iteration == 1 and state.whiteboard == []


@pytest.mark.parametrize('boundary,kind', [
    pytest.param('build', OSError, id='build-io'),
    pytest.param('preparation', OSError, id='preparation-io'),
    pytest.param('preparation', RuntimeError, id='preparation-runtime'),
    pytest.param('preparation', subprocess.SubprocessError, id='preparation-subprocess'),
])
def test_insertion_preparation_and_build_errors_propagate(insertion_case, boundary, kind):
    c = insertion_case
    error = kind('fixture boundary failure')
    setattr(c, 'build_error' if boundary == 'build' else 'preparation_error', error)
    with c.observing(), pytest.raises(kind) as caught:
        L.main(c.args)
    assert caught.value is error
    assert c.preparations == 1
    assert c.builds == ([(c.api, False)] if boundary == 'build' else [])
    assert c.events == (['build'] if boundary == 'build' else [])
    assert c.gateway == [] and c.outcomes == []
    assert (c.sidecar / 'slot-start.json').is_file()
    assert not (c.sidecar / 'tier0.json').exists()
    assert not (c.sidecar / 'pipeline-submitted.json').exists()
    assert not Path(c.layout.root, 's4_loop_digest.txt').exists()
    assert not Path(c.layout.root, 'runs/wal.jsonl').exists()


@pytest.mark.usefixtures('_detect_site_under_test')
def test_live_insertion_build_smoke_sidecar_submission_order(tmp_path, monkeypatch):
    """M1/M2/M3: observe actual calls and BuildResult, stop at pipeline entry.

    Profiling only observes arguments/results; no dependency is replaced. Full
    verify/bench and perf-cache-hit validation belong to the parent's live slot.
    """
    args, sidecar = _live_args(tmp_path, monkeypatch)
    events, builds = [], []
    code = L._run_one_iteration_resolved.__code__

    def observe(frame, event, arg):
        parent = frame.f_back
        if parent is None or parent.f_code is not code:
            return
        name = frame.f_code.co_name
        if event == 'return' and name in {'build', 'build_v2'}:
            assert arg is not None
            builds.append(arg)
            events.append('build')
        if event == 'call' and name == '_run_b5_tier0_smoke':
            assert len(builds) == 1 and builds[0].trace is False
            assert frame.f_locals['binary'] == builds[0].binary
            assert not (sidecar / 'pipeline-submitted.json').exists()
            events.append('smoke')
        if event == 'call' and name == '_write_b5_sidecar':
            name = frame.f_locals['name']
            if name == 'tier0.json':
                assert not (sidecar / 'pipeline-submitted.json').exists()
                assert frame.f_locals['payload']['status'] == 'passed'
            if name == 'pipeline-submitted.json':
                assert json.loads((sidecar / 'tier0.json').read_text())['status'] == 'passed'
            events.append(name)
        if event == 'call' and name == 'run_campaign':
            assert events == ['build', 'smoke', 'tier0.json', 'pipeline-submitted.json']
            assert frame.f_locals['bench_max_rounds'] == 3
            raise _PipelineBoundary

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        with pytest.raises(_PipelineBoundary):
            L.main(args)
    finally:
        sys.setprofile(previous)
    assert events == ['build', 'smoke', 'tier0.json', 'pipeline-submitted.json']
    doc = json.loads((sidecar / 'tier0.json').read_text())
    assert doc['contract'] == L.B5_TIER0_CONTRACT
    assert doc['build'] == dict(trace=False, binary=builds[0].binary,
                                bin_sha256=builds[0].bin_sha256, cached=builds[0].cached)


@pytest.mark.usefixtures('_detect_site_under_test')
def test_live_rejection_rc3_no_submission_wal_or_digest(tmp_path, monkeypatch):
    """M9/M10: actual CLI/build/gateway rejection reaches the early-return set."""
    args, sidecar = _live_args(tmp_path, monkeypatch)
    # A real zero-deadline gateway failure; no fake result or exception.
    monkeypatch.setitem(L.B5_TIER0_CONTRACT, 'timeout_s', 0)
    assert L.main(args) == 3
    start = json.loads((sidecar / 'slot-start.json').read_text())
    tier0 = json.loads((sidecar / 'tier0.json').read_text())
    assert (tier0['status'], tier0['reason']) == ('rejected', 'smoke-timeout')
    assert not (sidecar / 'pipeline-submitted.json').exists()
    root = Path(start['campaign_root'])
    assert not (root / 's4_loop_digest.txt').exists()
    assert not (root / 'runs/wal.jsonl').exists()
    state = L.load_loop_state(L.CampaignLayout(str(root)))
    assert state.iteration == 1 and state.whiteboard == []


@pytest.mark.parametrize('boundary', ['_b5_tier0_build_inputs', 'build_v2'])
@pytest.mark.usefixtures('_detect_site_under_test')
def test_live_preparation_and_build_io_errors_propagate(tmp_path, monkeypatch, boundary):
    """M11: real file-open failure injected at a named call in the insertion.

    The profile callback raises FileNotFoundError from a missing fixture file;
    it does not substitute a build, admission or helper implementation/result.
    The build case specifically crosses the build exception handler, so widening
    that handler to Exception turns this into rc 3 and fails raises().
    """
    args, sidecar = _live_args(tmp_path, monkeypatch)
    reached = []
    missing = tmp_path / 'absent-io-input'
    def inject(frame, event, arg):
        if (event == 'call' and frame.f_code.co_name == boundary
                and frame.f_back is not None
                and frame.f_back.f_code is L._run_one_iteration_resolved.__code__):
            reached.append(boundary)
            missing.read_bytes()
    previous = sys.getprofile()
    try:
        sys.setprofile(inject)
        with pytest.raises(FileNotFoundError):
            L.main(args)
    finally:
        sys.setprofile(previous)
    assert reached == [boundary]
    assert not (sidecar / 'tier0.json').exists()
    assert not (sidecar / 'pipeline-submitted.json').exists()
    observed = B.classify_slot(sidecar, None, 5, B._genome(20))
    assert (observed['outcome'], observed['submitted']) == ('unclassified-missing', False)


@pytest.mark.usefixtures('_detect_site_under_test')
def test_live_pipeline_reuses_perf_cache_and_keeps_verify(tmp_path, monkeypatch):
    """Parent's full one-slot liveness probe, including real verify and bench."""
    args, sidecar = _live_args(tmp_path, monkeypatch)
    assert L.main(args) == 0
    tier0 = json.loads((sidecar / 'tier0.json').read_text())
    start = json.loads((sidecar / 'slot-start.json').read_text())
    assert tier0['status'] == 'passed'
    layout = L.CampaignLayout(start['campaign_root'])
    records = L.wal.read_records(layout)
    built = [r.payload for r in records if r.stage == 'build_done']
    assert len(built) == 1
    assert built[0]['perf_cached'] is True
    assert built[0]['perf_bin_sha256'] == tier0['build']['bin_sha256']
    assert [r.payload['workload']['tag'] for r in records if r.stage == 'verify_done'] == [
        'legacy', 'performance', 'performance', 'performance', 'performance', 'performance']
    assert [r.stage for r in records[-2:]] == ['bench_done', 'commit']
    observed = B.classify_slot(sidecar, None, 5, B._genome(20))
    assert (observed['outcome'], observed['submitted'], observed['tier0']['status']) == (
        'certified', True, 'passed')


def test_build_exception_boundary_and_preparation_order():
    """Static companion to live build tests: constrain the actual insertion try."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(L._run_one_iteration_resolved)))
    tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)
             and any(isinstance(c, ast.Call) and ast.unparse(c.func) == 'buildcache.build_v2'
                     for stmt in n.body for c in ast.walk(stmt))]
    assert len(tries) == 1
    block = tries[0]
    assert [ast.unparse(h.type) for h in block.handlers] == ['(RuntimeError, subprocess.SubprocessError)']
    preparation = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and ast.unparse(n.func) == '_b5_tier0_build_inputs']
    assert len(preparation) == 1 and preparation[0].lineno < block.lineno
    assert not any(isinstance(n, ast.Call) and ast.unparse(n.func) == '_b5_tier0_build_inputs'
                   for n in ast.walk(block))


def test_non_b5_stock_and_dry_run_do_not_reach_tier0():
    tree = ast.parse(textwrap.dedent(inspect.getsource(L._run_one_iteration_resolved)))
    tier0 = [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test) == 'b5_mode'
             and any(isinstance(c, ast.Call) and ast.unparse(c.func) == '_run_b5_tier0_smoke'
                     for c in ast.walk(n))]
    assert len(tier0) == 1
    dry = next(n for n in tree.body[0].body if isinstance(n, ast.If) and ast.unparse(n.test) == 'not do_build')
    assert isinstance(dry.body[-1], ast.Return) and dry.end_lineno < tier0[0].lineno
    stock = ast.parse(textwrap.dedent(inspect.getsource(L._run_stock_control_resolved)))
    assert [c for c in ast.walk(stock) if isinstance(c, ast.Call)
            and ast.unparse(c.func) in {'_run_b5_tier0_smoke', '_b5_tier0_build_inputs'}] == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
