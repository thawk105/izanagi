"""Pure contract checks for the interval GC compute driver."""
from __future__ import annotations

import json
import subprocess
from contextlib import contextmanager
from pathlib import Path
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

from orchestrator.campaign import vhash_interval_gc as d


def raises(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return
    raise AssertionError(f'expected {exc.__name__}')


def test_materializer_names_existing_driver_function():
    assert callable(d._build_variant)
    assert getattr(d, d._build_variant.__name__) is d._build_variant
    assert d.MATERIALIZER == f'{d._build_variant.__module__}.{d._build_variant.__qualname__}'


def test_condition_table_and_group_partition():
    assert len(d.CELLS) == 17
    names = [name for group in d.GROUPS.values() for name in group]
    assert len(d.GROUPS) >= 4 and len(names) == len(set(names))
    assert set(names) == set(d.CELLS)
    for rr in (50, 95):
        for kind in ('wait1', 'wait10', 'many', 'ronly'):
            for gc in (10, 100):
                assert f'rr{rr}-{kind}-gc{gc}' in d.CELLS
    assert d.CELLS['rr50-wait10-two-gc10']['long_threads'] == 2


def test_arm_macro_sets():
    expected = {
        'stock': {'CICADA_INTERVAL_LONGTX': 1},
        'min': {'CICADA_INTERVAL_LONGTX': 1, 'CICADA_INTERVAL_GC': 1},
        'gen': {'CICADA_INTERVAL_LONGTX': 1, 'CICADA_INTERVAL_GC': 1,
                'CICADA_INTERVAL_GC_GENERAL': 1},
    }
    assert set(d.MACRO_NAMES) == {'CICADA_INTERVAL_LONGTX', 'CICADA_INTERVAL_GC',
                                  'CICADA_INTERVAL_GC_GENERAL', 'CICADA_INTERVAL_COUNT'}
    for arm, perf in expected.items():
        assert d.arm_macros(arm, 'perf') == perf
        assert d.arm_macros(arm, 'trace') == perf
        assert d.arm_macros(arm, 'count') == {**perf, 'CICADA_INTERVAL_COUNT': 1}
        assert all(value == 1 for kind in ('perf', 'trace', 'count')
                   for value in d.arm_macros(arm, kind).values())


def test_order_rotation():
    assert [d.order_rotation(rep) for rep in range(3)] == [
        ('stock', 'min', 'gen'), ('min', 'gen', 'stock'), ('gen', 'stock', 'min')]
    plan = d.plan_runs('rr50_wait')
    cell = d.GROUPS['rr50_wait'][0]
    for rep in range(3):
        assert tuple(row['arm'] for row in plan if row['cell'] == cell and
                     row['build_kind'] == 'perf' and row['rep'] == rep) == d.order_rotation(rep)


def test_count_never_perf_eligible():
    assert d.perf_eligible('count') is False
    assert d.perf_eligible('perf') is True
    assert all(not d.perf_eligible(row['build_kind']) for row in d.plan_runs('rr50_wait')
               if row['build_kind'] == 'count')


def test_gate_receipt_missing_rejected():
    macros = d.arm_macros('min', 'count')
    receipts = [{'macro': name, 'admission': {'admitted': True}} for name in macros]
    d.assert_gate_receipts(macros, receipts)
    raises(RuntimeError, d.assert_gate_receipts, macros, receipts[:-1])
    bad = [dict(receipts[0], admission={'admitted': False}), *receipts[1:]]
    raises(RuntimeError, d.assert_gate_receipts, macros, bad)


def test_general_gate_requires_gc_companion():
    companion = SimpleNamespace(companion_defines=(('CICADA_INTERVAL_GC', '1'),))
    d.assert_gate_companion('CICADA_INTERVAL_GC_GENERAL', companion)
    for missing in ((), (('CICADA_INTERVAL_GC', '0'),)):
        raises(RuntimeError, d.assert_gate_companion, 'CICADA_INTERVAL_GC_GENERAL',
               SimpleNamespace(companion_defines=missing))


def test_competing_pid_rejected():
    original = d.competing_bench_pids
    try:
        d.competing_bench_pids = lambda: [123]
        raises(RuntimeError, d.assert_solo)
        d.competing_bench_pids = lambda: []
        assert d.assert_solo()['competing'] == []
    finally:
        d.competing_bench_pids = original


def test_compile_binding_positive_negative():
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp)
        path = build / 'compile_commands.json'
        for arm in d.ARMS:
            for kind in ('perf', 'count', 'trace'):
                expected = d.arm_macros(arm, kind)
                defs = {'TRACE': int(kind == 'trace'), 'ADD_ANALYSIS': 0, 'SINGLE_EXEC': 0,
                        **d.BASE, **expected}
                argv = ['c++', *(f'-D{k}={v}' for k, v in defs.items())]
                entries = [{'file': str(build / f'cc/cicada/{name}'),
                            'arguments': [*argv, '-o', f'CMakeFiles/ycsb_cicada.exe.dir/{name}.o']}
                           for name in ('transaction.cc', 'util.cc', 'ycsb_cicada.cc')]
                # A sibling target with different defines must not affect binding.
                entries.append({'file': entries[0]['file'], 'arguments': ['c++', '-DTRACE=1',
                               '-o', 'CMakeFiles/tpcc_cicada.exe.dir/transaction.cc.o']})
                path.write_text(json.dumps(entries))
                assert len(d.check_compile_commands(build, expected, int(kind == 'trace'))) == 3
                if kind in ('perf', 'count'):
                    diagnostic = json.loads(json.dumps(entries))
                    for entry in diagnostic[:3]:
                        entry['arguments'][1:1] = ['-g', '-fno-omit-frame-pointer',
                                                   '-UNDEBUG', '-O3', '-DNDEBUG', '-UNDEBUG']
                    path.write_text(json.dumps(diagnostic))
                    assert len(d.check_compile_commands(build, expected, 0, diag=True)) == 3
                    bad_order = json.loads(json.dumps(diagnostic))
                    bad_order[0]['arguments'].append('-DNDEBUG')
                    path.write_text(json.dumps(bad_order))
                    raises(RuntimeError, d.check_compile_commands, build, expected, 0,
                           diag=True)
                    diagnostic[0]['arguments'].remove('-g')
                    path.write_text(json.dumps(diagnostic))
                    raises(RuntimeError, d.check_compile_commands, build, expected, 0,
                           diag=True)
                    path.write_text(json.dumps(entries))
                for unexpected in ({'CICADA_INTERVAL_GC_GENERAL': 1},
                                   {'CICADA_INTERVAL_GC': 2}):
                    if any(key in expected for key in unexpected):
                        continue
                    bad = json.loads(json.dumps(entries))
                    key, value = next(iter(unexpected.items()))
                    bad[0]['arguments'].insert(1, f'-D{key}={value}')
                    path.write_text(json.dumps(bad))
                    raises(RuntimeError, d.check_compile_commands, build, expected,
                           int(kind == 'trace'))
                if 'CICADA_INTERVAL_GC' in expected:
                    bad = json.loads(json.dumps(entries))
                    for index, token in enumerate(bad[0]['arguments']):
                        if token == '-DCICADA_INTERVAL_GC=1':
                            bad[0]['arguments'][index] = '-DCICADA_INTERVAL_GC=2'
                            break
                    path.write_text(json.dumps(bad))
                    raises(RuntimeError, d.check_compile_commands, build, expected,
                           int(kind == 'trace'))
                if arm == 'gen':
                    bad = json.loads(json.dumps(entries))
                    bad[0]['arguments'].remove('-DCICADA_INTERVAL_GC_GENERAL=1')
                    path.write_text(json.dumps(bad))
                    raises(RuntimeError, d.check_compile_commands, build, expected,
                           int(kind == 'trace'))
        inert = {'TRACE': 0, 'ADD_ANALYSIS': 0, 'SINGLE_EXEC': 0, **d.BASE}
        argv = ['c++', *(f'-D{k}={v}' for k, v in inert.items())]
        entries = [{'file': str(build / f'cc/cicada/{name}'),
                    'arguments': [*argv, '-o', f'CMakeFiles/ycsb_cicada.exe.dir/{name}.o']}
                   for name in ('transaction.cc', 'util.cc', 'ycsb_cicada.cc')]
        path.write_text(json.dumps(entries))
        assert len(d.check_compile_commands(build, {}, 0)) == 3
        for macro in d.MACRO_NAMES:
            bad = json.loads(json.dumps(entries))
            bad[0]['arguments'].insert(1, f'-D{macro}=1')
            path.write_text(json.dumps(bad))
            raises(RuntimeError, d.check_compile_commands, build, {}, 0)


def test_counter_lines_positive_negative():
    good = ('CICADA_INTERVAL_V1 {"schema":1,"prune_success":4}\n'
            'CICADA_IGC_LONGTX_V1 {"attempts":3,"commits":2,"aborts":1,'
            '"residence_cycles_sum":40,"residence_cycles_max":20}\n')
    assert d.parse_counters(good, 'count')[0]['prune_success'] == 4
    raises(ValueError, d.parse_counters, good + good, 'count')
    raises(ValueError, d.parse_counters, good, 'perf')
    raises(ValueError, d.parse_counters, good.replace('"attempts":3', '"attempts":-3'), 'count')


def test_smoke_candidate_delta():
    counters = {'min': {'threads': [{'prune_success': 2}, {'prune_success': 3}]},
                'gen': {'threads': [{'prune_success': 4}, {'prune_success': 5}]}}
    assert d.smoke_candidate_delta(counters)['beyond_minimum_candidate'] == 4
    raises(ValueError, d.smoke_candidate_delta,
           {'min': {'threads': [{}]}, 'gen': counters['gen']})


def test_overprune_parser_and_attribution():
    stderr = 'CICADA_OVERPRUNE_EVENT tx_wts=4 key=0a removed_wts=30\nCICADA_OVERPRUNE_FIRED n=1\n'
    diag = d.parse_overprune(stderr)
    assert diag['fired'] == 1 and diag['events'][0]['removed_wts'] == 30
    raises(ValueError, d.parse_overprune, stderr.replace('n=1', 'n=0'))
    record = {'anomalies': [{'edges': [{'from': 7, 'to': 8,
              'reasons': [{'key': '0a', 'u_ver': [1, 0]}]}]}]}
    assert d.attribute_overprune(record, diag, {7}, 20)
    assert not d.attribute_overprune(record, diag, {9}, 20)
    assert not d.attribute_overprune(record, diag, {7}, 40)


def test_broken_classification_positive_negative():
    stock = {'total_cycles': 0, 'verdict': 'indeterminate'}
    broken = {'verdict': 'non-serializable', 'total_cycles': 1,
              'attributed_edges': [{'edge': {'from': 7}}],
              'overprune': {'fired': 1}}
    assert d.classify_broken(broken, stock) == '期待した経路で検出'
    assert d.classify_broken({**broken, 'attributed_edges': []}, stock) != '期待した経路で検出'
    assert d.classify_broken(broken, {**stock, 'total_cycles': 1}) == '対照異常'


def test_aggregate_missing_cells_rejected():
    raises(ValueError, d.aggregate, [])
    records = []
    for cell in d.CELLS:
        for arm in d.ARMS:
            for rep in range(3):
                records.append({'valid': True, 'cell': cell, 'arm': arm,
                                'build_kind': 'perf', 'perf_eligible': True,
                                'rep': rep, 'throughput_tps': 100 + rep})
            records.append({'valid': True, 'cell': cell, 'arm': arm,
                            'build_kind': 'count', 'perf_eligible': False,
                            'interval_counter': {'schema': 1}})
    assert d.aggregate(records)['complete'] is True
    raises(ValueError, d.aggregate, [r for r in records if r['cell'] != next(iter(d.CELLS))])


def test_smoke_attempts_every_build_and_preserves_complete_failure_log():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'scratch').mkdir()
        (root / 'output').mkdir()
        source = root / 'source'
        source.mkdir()
        attempted = []
        diagnostic_specs = []

        @contextmanager
        def checkout(_pin):
            yield source

        def fake_build(_source, build, _deps, _toolchain, arm, kind,
                       *, dependency=False, build_log=None, diag=False):
            name = build.name
            attempted.append(name)
            if name == 'min-perf':
                stdout = b'begin-' + b'A' * 3000 + b'-end'
                stderr = b'error-' + b'B' * 3000 + b'-end'
                with patch.object(d.subprocess, 'run', return_value=subprocess.CompletedProcess(
                        ['fake-compiler', name], 2, stdout, stderr)):
                    d.checked(['fake-compiler', name], build_log=build_log)
            binary = build / 'cc/cicada/ycsb_cicada.exe'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'binary')
            return binary, [{'macro': key, 'admission': {'admitted': True}}
                            for key in ({} if dependency else d.arm_macros(arm, kind))]

        def fake_run(_binary, spec, _receipts, _hashes, _raw_dir):
            return {**spec, 'interval_counter': {'prune_success': 1}, 'valid': True}

        args = SimpleNamespace(command='smoke', group=None, job=None,
                               output=root / 'output', scratch_root=root / 'scratch',
                               third_party_cache=root, no_gen_perf=False,
                               with_trace_builds=True, diag_builds=True,
                               diag_run_timeout=60, diag_gdb_timeout=120)
        with patch.object(d.socket, 'gethostname', return_value='compute'), \
             patch.object(d, 'assert_solo'), \
             patch.object(d.compute, '_load_policy', return_value={}), \
             patch.object(d.compute, '_resolve_toolchain', return_value={}), \
             patch.object(d.compute, '_prepare_dependencies', return_value={}), \
             patch.object(d.patchharness, 'checkout', checkout), \
             patch.object(d, '_build_variant', fake_build), \
             patch.object(d, 'inert_receipt', return_value={'matched': True}), \
             patch.object(d, 'apply_patches'), \
             patch.object(d, 'sha_file', side_effect=lambda path: d.digest(Path(path).read_bytes())
                          if Path(path).exists() else 'missing-test-patch'), \
             patch.object(d, 'run_binary', fake_run), \
             patch.object(d, 'run_diagnostic', side_effect=lambda _binary, spec, *_args,
                          **_kwargs: (diagnostic_specs.append(dict(spec)) or
                                      {'abnormal': False, 'perf_eligible': False})):
            raises(RuntimeError, d.run_job, args)
        assert attempted == ['dependency', 'stock-perf', 'min-perf', 'gen-perf',
                             'stock-count', 'min-count', 'gen-count',
                             'stock-perf-diag', 'min-perf-diag', 'gen-perf-diag',
                             'stock-count-diag', 'min-count-diag', 'gen-count-diag',
                             'stock-trace', 'min-trace', 'gen-trace', 'broken-trace']
        out = next((root / 'output').iterdir())
        manifest = json.loads((out / 'manifest.json').read_text())
        assert manifest['status'] == 'failed'
        assert set(manifest['builds']) == set(attempted)
        assert set(manifest['diagnostics']) == {
            f'{arm}-{kind}-diag{suffix}' for arm in d.ARMS
            for kind in ('perf', 'count') for suffix in ('', '-rr95-ronly-gc10')}
        assert {(s['cell'], s['arm'], s['build_kind'], s['extime']) for s in diagnostic_specs} == {
            (cell, arm, kind, 3) for cell in ('rr50-wait1-gc10', 'rr95-ronly-gc10')
            for arm in d.ARMS for kind in ('perf', 'count')}
        assert len(diagnostic_specs) == 12
        assert all(not manifest['diagnostics'][name]['perf_eligible']
                   for name in manifest['diagnostics'])
        assert all(not manifest['builds'][name]['perf_eligible'] for name in attempted
                   if name.endswith('-diag'))
        assert len(manifest['records']) == 5
        failed = manifest['builds']['min-perf']
        assert failed['ok'] is False and failed['rc'] == 2
        log = Path(failed['log']['path'])
        assert b'begin-' + b'A' * 3000 + b'-end' in log.read_bytes()
        assert b'error-' + b'B' * 3000 + b'-end' in log.read_bytes()
        assert d.sha_file(log) == failed['log']['sha256']
        assert all(manifest['builds'][name]['ok'] for name in attempted if name != 'min-perf')


def test_failed_nonbuild_command_keeps_complete_output():
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        token = d.FAILURE_LOG_DIR.set(directory)
        try:
            stdout = b'first-' + b'X' * 3000 + b'-last'
            stderr = b'first-' + b'Y' * 3000 + b'-last'
            completed = subprocess.CompletedProcess(['fake-command'], 7, stdout, stderr)
            with patch.object(d.subprocess, 'run', return_value=completed):
                raises(RuntimeError, d.checked, ['fake-command'])
        finally:
            d.FAILURE_LOG_DIR.reset(token)
        log = next(directory.glob('failed-command-*.log')).read_bytes()
        assert stdout in log and stderr in log
        assert b'rc=7' in log


def test_diagnostic_signal_reruns_gdb_once_and_logs_output():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / 'logs').mkdir()
        spec = {'arm': 'gen', 'build_kind': 'perf', 'cell': 'rr50-wait1-gc10', 'extime': 1}
        receipts = [{'macro': key, 'admission': {'admitted': True}}
                    for key in d.arm_macros('gen', 'perf')]
        calls = []

        def fake_gdb(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, b'full backtrace\n', b'')

        with patch.object(d, 'assert_solo'), \
             patch.object(d, 'bench_argv', return_value=['/fake/ycsb', '-extime=1']), \
             patch.object(d.shutil, 'which', return_value='/usr/bin/gdb'), \
             patch.object(d, 'run_measured', return_value=SimpleNamespace(
                 returncode=-6, stdout=b'flags\n',
                 stderr=b'assertion failed: pinned version\nvariant=general\n')), \
             patch.object(d.subprocess, 'run', side_effect=fake_gdb):
            result = d.run_diagnostic(Path('/fake/ycsb'), spec, receipts, out)
        assert result['abnormal'] and result['perf_eligible'] is False
        assert len(calls) == 1
        assert calls[0] == ['/usr/bin/gdb', '-batch', '-ex', 'run',
                            '-ex', 'thread apply all bt 20', '--args',
                            '/fake/ycsb', '-extime=1']
        log = Path(result['log']['path']).read_bytes()
        assert b'assertion failed: pinned version\nvariant=general\n' in log
        assert log.index(b'assertion failed') < log.index(b'full backtrace')
        assert result['returncode'] == -6


def test_diagnostic_build_keeps_gate_and_adds_compile_flags():
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp)
        binary = build / 'cc/cicada/ycsb_cicada.exe'
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b'binary')
        commands = []
        gates = []
        checks = []

        def fake_gate(_source, macros, args, _cxx, **kwargs):
            gates.append((macros, list(args)))
            return [{'macro': key, 'admission': {'admitted': True}} for key in macros]

        with patch.object(d, 'non_admissible_materializer'), \
             patch.object(d, 'configure_args', return_value=['-DCMAKE_BUILD_TYPE=Release']), \
             patch.object(d, 'gate', side_effect=fake_gate), \
             patch.object(d, 'checked', side_effect=lambda argv, **kwargs: commands.append(argv)), \
             patch.object(d, 'check_compile_commands', side_effect=lambda *a, **kw: checks.append(kw)):
            d._build_variant(build, build, {}, {'cxx_path': '/usr/bin/c++'},
                             'gen', 'count', diag=True)
        assert gates[0][0] == d.arm_macros('gen', 'count')
        assert gates[0][1] == ['-DCMAKE_BUILD_TYPE=Release']
        flags = next(value for value in commands[0] if value.startswith('-DCMAKE_CXX_FLAGS='))
        assert '-g -fno-omit-frame-pointer -UNDEBUG' in flags
        release = next(value for value in commands[0]
                       if value.startswith('-DCMAKE_CXX_FLAGS_RELEASE='))
        assert release.endswith('-O3 -DNDEBUG -UNDEBUG')
        assert all(f'-D{key}={value}' in flags for key, value in gates[0][0].items())
        assert checks == [{'diag': True}]

        commands.clear()
        with patch.object(d, 'non_admissible_materializer'), \
             patch.object(d, 'configure_args', return_value=['-DCMAKE_BUILD_TYPE=Release']), \
             patch.object(d, 'gate', side_effect=fake_gate), \
             patch.object(d, 'checked', side_effect=lambda argv, **kwargs: commands.append(argv)), \
             patch.object(d, 'check_compile_commands'):
            d._build_variant(build, build, {}, {'cxx_path': '/usr/bin/c++'},
                             'gen', 'perf')
        assert all('-UNDEBUG' not in arg for arg in commands[0])


def test_diagnostic_missing_gdb_records_and_continues():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / 'logs').mkdir()
        spec = {'arm': 'stock', 'build_kind': 'count', 'cell': 'rr50-wait1-gc10', 'extime': 1}
        receipts = [{'macro': key, 'admission': {'admitted': True}}
                    for key in d.arm_macros('stock', 'count')]
        with patch.object(d, 'assert_solo'), \
             patch.object(d, 'bench_argv', return_value=['/fake/ycsb']), \
             patch.object(d.shutil, 'which', return_value=None), \
             patch.object(d, 'run_measured', return_value=SimpleNamespace(
                 returncode=-9, stdout=b'', stderr=b'')), \
             patch.object(d.subprocess, 'run', side_effect=AssertionError('gdb launched')):
            result = d.run_diagnostic(Path('/fake/ycsb'), spec, receipts, out)
        assert b'gdb unavailable' in Path(result['log']['path']).read_bytes()


def test_diagnostic_timeout_attaches_before_kill_and_reruns():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        (out / 'logs').mkdir()
        spec = {'arm': 'min', 'build_kind': 'perf', 'cell': 'rr50-wait1-gc10', 'extime': 1}
        receipts = [{'macro': key, 'admission': {'admitted': True}}
                    for key in d.arm_macros('min', 'perf')]
        calls = []

        def fake_run(argv, *, before_timeout_kill, **kwargs):
            before_timeout_kill(1234)
            raise subprocess.TimeoutExpired(argv, kwargs['timeout'])

        def fake_gdb(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, b'backtrace\n', b'')

        with patch.object(d, 'assert_solo'), \
             patch.object(d, 'bench_argv', return_value=['/fake/ycsb']), \
             patch.object(d.shutil, 'which', return_value='/usr/bin/gdb'), \
             patch.object(d, 'run_measured', side_effect=fake_run), \
             patch.object(d.subprocess, 'run', side_effect=fake_gdb):
            result = d.run_diagnostic(Path('/fake/ycsb'), spec, receipts, out,
                                      run_timeout=2, gdb_timeout=3)
        assert result['timeout'] and len(calls) == 2
        assert calls[0] == ['/usr/bin/gdb', '-batch', '-p', '1234',
                            '-ex', 'thread apply all bt 20']
        assert calls[1][2:4] == ['-ex', 'run']
        assert b'backtrace' in Path(result['log']['path']).read_bytes()


def test_measured_timeout_calls_attach_before_kill():
    events = []

    def fake_wait4(pid, options):
        events.append(('wait4', options))
        return (0, 0, None) if options == d.os.WNOHANG else (pid, 0, None)

    with patch.object(d.subprocess, 'Popen', return_value=SimpleNamespace(pid=1234)), \
         patch.object(d.os, 'wait4', side_effect=fake_wait4), \
         patch.object(d.os, 'kill', side_effect=lambda pid, sig: events.append(('kill', pid))), \
         patch.object(d.time, 'monotonic', side_effect=[0, 2]):
        raises(subprocess.TimeoutExpired, d.run_measured, ['/fake/ycsb'], timeout=1,
               before_timeout_kill=lambda pid: events.append(('attach', pid)))
    assert events == [('wait4', d.os.WNOHANG), ('attach', 1234),
                      ('kill', 1234), ('wait4', 0)]


def _run():
    tests = [(name, value) for name, value in sorted(globals().items())
             if name.startswith('test_') and callable(value)]
    failures = 0
    for name, test in tests:
        try:
            test()
            print('PASS', name)
        except Exception as exc:
            failures += 1
            print('FAIL', name, type(exc).__name__, exc)
            traceback.print_exc()
    print(f'{len(tests) - failures} passed, {failures} failed')
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(_run())
