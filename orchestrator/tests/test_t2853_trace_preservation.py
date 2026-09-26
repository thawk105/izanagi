"""Real local repetition cleanup and zstd archival IO."""
import builtins
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import replace

import pytest

from orchestrator.campaign import pipeline as P
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.tests import test_campaign as F

_REAL_MKDTEMP = P.tempfile.mkdtemp


@pytest.fixture(autouse=True)
def authority():
    F._refresh_certified_writer_authority()


@pytest.fixture
def archive(tmp_path, monkeypatch):
    root = tmp_path / 'archive'
    monkeypatch.setenv('IZANAGI_TRACE_ARCHIVE_ROOT', str(root))
    return root


def evaluate(tmp_path, monkeypatch, **kwargs):
    source_root = kwargs.pop('source_root', None)
    if source_root is None:
        source_root = git_source(tmp_path / 'ccbench')
    directories = []
    real = _REAL_MKDTEMP

    def mkdir(*a, **kw):
        if kw.get('prefix', '').startswith('izanagi_eval_trace_'):
            kw['dir'] = str(tmp_path)
            directory = real(*a, **kw)
            directories.append(Path(directory))
            return directory
        return real(*a, **kw)

    monkeypatch.setattr(P.tempfile, 'mkdtemp', mkdir)
    layout = CampaignLayout(str(tmp_path / 'campaign'))
    original_evidence = F._source_evidence
    with monkeypatch.context() as patch:
        patch.setattr(F, '_source_evidence', lambda *a, **kw: replace(
            original_evidence(*a, **kw), source_root=str(source_root)))
        result, calls = F._eval(layout, **kwargs)
    return result, calls, directories


def git_source(root):
    root.mkdir()
    env = P._sanitized_git_env()
    subprocess.run(['git', '-C', str(root), 'init', '-q'], check=True, env=env)
    tracked = root / 'tracked.txt'
    tracked.write_text('before\n')
    subprocess.run(['git', '-C', str(root), 'add', 'tracked.txt'], check=True, env=env)
    subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test',
                    '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'base'],
                   check=True, env=env)
    tracked.write_text('after\n')
    return root


def serial_trace():
    return Path(F._HERE, 'fixtures/g1_serial/trace_0.log').read_text()


def test_inventory_records_r1_inputs(tmp_path, monkeypatch, archive):
    source = git_source(tmp_path / 'source')
    result, calls, dirs = evaluate(tmp_path, monkeypatch, source_root=source,
                                   trace_content=serial_trace(), ncommit=2)
    assert result.certified and calls
    path, = archive.rglob('inventory.json')
    data = json.loads(path.read_text())
    repo_root = Path(P.__file__).resolve().parents[2]
    git_env = P._sanitized_git_env()
    git = lambda root, *args: subprocess.check_output(
        ['git', '-C', str(root), *args], env=git_env)
    patch = git(source, 'diff', '--binary', 'HEAD', '--')
    assert git(source, 'rev-parse', 'HEAD') != git(repo_root, 'rev-parse', 'HEAD')
    expected_argv = [os.path.realpath(sys.executable), '-B', '-m',
                     'orchestrator.verifier', str(dirs[0]), '--json',
                     '--expected-commits', '2', '--protocol', 'silo',
                     '--ccbench-root', str(source)]
    assert data['verifier_invocation'] == 'in-process'
    assert data['verifier_argv'] == expected_argv
    assert data['repo_head'] == git(repo_root, 'rev-parse', 'HEAD').decode().strip()
    assert data['ccbench_pin'] == 'deadbeef'
    recovered = subprocess.check_output(
        ['zstd', '-d', '-c', str(path.parent / data['patch_path'])])
    assert (recovered, data['patch_sha256'], data['patch_bytes'], data['patch_path']) == (
        patch, hashlib.sha256(patch).hexdigest(), len(patch), 'patch/ccbench.diff.zst')
    assert data['tracked_diff_sha256'] == hashlib.sha256(b'').hexdigest()
    assert data['verifier_module_sha256'] == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((repo_root / 'orchestrator/verifier').glob('*.py'))}


def test_r1_argv_null_without_witness(tmp_path, monkeypatch, archive):
    result, calls, dirs = evaluate(tmp_path, monkeypatch, trace_content='', ncommit=0)
    path, = archive.rglob('inventory.json')
    data = json.loads(path.read_text())
    assert data['verifier_argv'] is None
    assert (data['repo_head'] is not None and data['ccbench_pin'] == 'deadbeef'
            and data['patch_path'] == 'patch/ccbench.diff.zst'
            and data['tracked_diff_sha256'] is not None
            and data['verifier_module_sha256'])


def test_r1_input_failure_retains_original(tmp_path, monkeypatch, archive, capsys):
    source = tmp_path / 'not-a-git-repo'
    source.mkdir()
    (tmp_path / 'baseline').mkdir()
    (tmp_path / 'archived').mkdir()
    monkeypatch.delenv('IZANAGI_TRACE_ARCHIVE_ROOT')
    baseline, _, _ = evaluate(tmp_path / 'baseline', monkeypatch,
                              source_root=source, trace_content=serial_trace(), ncommit=2)
    monkeypatch.setenv('IZANAGI_TRACE_ARCHIVE_ROOT', str(archive))
    try:
        result, calls, dirs = evaluate(tmp_path / 'archived', monkeypatch,
                                       source_root=source, trace_content=serial_trace(), ncommit=2)
    except Exception:
        result, calls, dirs = None, [], []
    assert result is not None and (result.certified, result.verdict) == (
        baseline.certified, baseline.verdict)
    path, = archive.rglob('inventory.json')
    data = json.loads(path.read_text())
    assert data['status'] == 'failed'
    assert dirs and (dirs[0] / 'trace_0.log').exists()


def test_archive_before_cleanup(tmp_path, monkeypatch, archive):
    trace = serial_trace()
    result, calls, dirs = evaluate(tmp_path, monkeypatch, trace_content=trace, ncommit=2)
    assert result.certified and calls
    assert dirs and all(not d.exists() for d in dirs)
    inventories = list(archive.rglob('inventory.json'))
    assert len(inventories) == len(dirs)
    for path in inventories:
        data = json.loads(path.read_text())
        assert data['status'] == 'complete'
        assert data['genome'] == 'silo|BACK_OFF=1'
        assert data['workload_flags'] and data['trace_binary_sha256']
        row, = data['files']
        assert row['sha256'] == hashlib.sha256(trace.encode()).hexdigest()
        recovered = subprocess.check_output(['zstd', '-d', '-c', str(path.parent / row['archive_path'])])
        assert recovered == trace.encode()
        assert row['compressed_bytes'] == (path.parent / row['archive_path']).stat().st_size


@pytest.mark.parametrize('content,ncommit', [('anomaly', 2), ('parse-error', 1)])
def test_anomaly_verdict_and_no_bench_unchanged(tmp_path, monkeypatch, archive, content, ncommit):
    trace = (Path(F._HERE, 'fixtures/r1_write_skew/trace_0.log').read_text()
             if content == 'anomaly' else 'not a trace\n')
    result, calls, dirs = evaluate(tmp_path, monkeypatch, trace_content=trace, ncommit=ncommit)
    assert not result.certified and result.aborted and not calls
    assert list(archive.rglob('inventory.json'))
    assert all(not d.exists() for d in dirs)


@pytest.mark.parametrize('failure', ['spawn', 'nonzero', 'inventory', 'relative'])
def test_failure_retains_original(tmp_path, monkeypatch, archive, capsys, failure):
    if failure in ('spawn', 'nonzero'):
        def fail(*a, **kw):
            if failure == 'spawn':
                raise FileNotFoundError('zstd missing')
            raise subprocess.CalledProcessError(1, ['zstd', '-T0', '-3'])
        monkeypatch.setattr(P, '_compress_trace_archive', fail)
    elif failure == 'inventory':
        real = builtins.open
        def fail(path, *a, **kw):
            if os.fspath(path).endswith('inventory.json'):
                raise OSError('inventory unwritable')
            return real(path, *a, **kw)
        monkeypatch.setattr(builtins, 'open', fail)
    else:
        monkeypatch.setenv('IZANAGI_TRACE_ARCHIVE_ROOT', 'relative')
    result, calls, dirs = evaluate(tmp_path, monkeypatch, trace_content=serial_trace(), ncommit=2)
    assert result.certified and calls
    assert dirs and all((d / 'trace_0.log').exists() for d in dirs)
    err = capsys.readouterr().err
    assert 'trace preservation failed' in err and str(dirs[0]) in err
    assert all(json.loads(p.read_text())['status'] != 'complete'
               for p in archive.rglob('inventory.json'))


def test_preservation_error_does_not_replace_result(tmp_path, monkeypatch, archive):
    def fail(*a, **kw):
        raise OSError('zstd spawn failed')
    monkeypatch.setattr(P, '_compress_trace_archive', fail)
    result, calls, dirs = evaluate(tmp_path, monkeypatch, trace_content=serial_trace(), ncommit=2)
    assert result.certified and calls and all(d.exists() for d in dirs)


@pytest.mark.parametrize('failure', ['spawn', 'inventory'])
def test_preservation_error_does_not_replace_exception(tmp_path, monkeypatch, archive, failure):
    original = RuntimeError('original verification error')
    def verify(*a, **kw):
        raise original
    real_open = builtins.open
    def fail_open(path, *a, **kw):
        if os.fspath(path).endswith('inventory.json'):
            raise OSError('inventory error')
        return real_open(path, *a, **kw)
    def fail_spawn(*a, **kw):
        raise OSError('spawn error')
    monkeypatch.setattr(P, 'verify_trace_dir_with_capability', verify)
    if failure == 'spawn':
        monkeypatch.setattr(P, '_compress_trace_archive', fail_spawn)
    else:
        monkeypatch.setattr(builtins, 'open', fail_open)
    with pytest.raises(RuntimeError) as exc:
        evaluate(tmp_path, monkeypatch, trace_content=serial_trace(), ncommit=2)
    assert exc.value is original
    assert list(tmp_path.glob('izanagi_eval_trace_*/trace_0.log'))


def test_unset_env_unchanged(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv('IZANAGI_TRACE_ARCHIVE_ROOT', raising=False)
    source = git_source(tmp_path / 'source')
    subprocess_calls = []
    r1_reads = []
    writes = []
    real_open, real_makedirs = builtins.open, os.makedirs
    real_run, real_read_bytes = subprocess.run, Path.read_bytes
    def run(*a, **kw):
        subprocess_calls.append(a)
        raise AssertionError('unexpected subprocess')
    def opened(path, mode='r', *a, **kw):
        if any(m in mode for m in 'wax'):
            writes.append(os.fspath(path))
        return real_open(path, mode, *a, **kw)
    def makedirs(path, *a, **kw):
        writes.append(os.fspath(path))
        return real_makedirs(path, *a, **kw)
    def tracked_run(args, *a, **kw):
        if args and args[0] == 'git':
            subprocess_calls.append(args)
        return real_run(args, *a, **kw)
    def tracked_read_bytes(path):
        if path.parent.name == 'verifier' and path.suffix == '.py':
            r1_reads.append(str(path))
        return real_read_bytes(path)
    monkeypatch.setattr(P, '_compress_trace_archive', run)
    monkeypatch.setattr(subprocess, 'run', tracked_run)
    monkeypatch.setattr(Path, 'read_bytes', tracked_read_bytes)
    monkeypatch.setattr(builtins, 'open', opened)
    monkeypatch.setattr(os, 'makedirs', makedirs)
    result, calls, dirs = evaluate(tmp_path, monkeypatch, source_root=source)
    assert result.certified and calls and dirs
    assert not subprocess_calls
    assert not r1_reads
    assert all(not d.exists() for d in dirs)
    assert not any('archive' in p or 'inventory.json' in p or '.zst' in p for p in writes)
    assert 'preservation' not in capsys.readouterr().err


def test_multiple_archives_and_streaming_counts(tmp_path, archive):
    from orchestrator.campaign.genome import Genome
    for rep in range(2):
        source = tmp_path / f'rep-{rep}'
        source.mkdir()
        payloads = {'empty': b'', 'tail': b'a\nb', 'newline': b'a\n', 'large': b'x' * (1024 * 1024 + 1)}
        for name, data in payloads.items():
            (source / name).write_bytes(data)
        P._preserve_trace_directory(str(source), str(archive), campaign_id='campaign', variant='v',
            build_attempt_id='attempt', tag='legacy', workload_flags={'thread': 2},
            genome=Genome('silo', {'BACK_OFF': 1}), trace_binary_sha256='a' * 64)
        path = archive / 'campaign/v/attempt/legacy' / source.name / 'inventory.json'
        rows = json.loads(path.read_text())['files']
        assert {r['path']: r['lines'] for r in rows} == {'empty': 0, 'tail': 2, 'newline': 1, 'large': 1}
        for row in rows:
            assert row['bytes'] == len(payloads[row['path']])
            assert row['sha256'] == hashlib.sha256(payloads[row['path']]).hexdigest()
    assert len(list(archive.rglob('inventory.json'))) == 2


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
