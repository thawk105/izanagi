#!/usr/bin/env python3
"""Cicada interval GC diagnostic and correctness campaign (compute node only)."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from statistics import median

from orchestrator.calibrator.benchparse import parse_bench_stdout
from orchestrator.calibrator.runner import competing_bench_pids
from . import condition_meaning_gate as condition, patchharness, pin
from . import s3_mocc_lock_coverage as compute
from .materializer_admission import non_admissible_materializer

ROOT = Path(__file__).resolve().parents[2]
DRIVER_ID = 'orchestrator.campaign.vhash_interval_gc'
MATERIALIZER = DRIVER_ID + '._build_variant'
PATCHES = ('patches/cicada-interval-gc-variant.patch', 'patches/cicada-interval-gc-longtx.patch')
TRACE_PATCH = 'patches/instr-cicada-trace.patch'
BROKEN_PATCH = 'patches/broken-cicada-interval-gc-overprune.patch'
ARMS = ('stock', 'min', 'gen')
BASE = {'BACK_OFF': 0, 'INLINE_VERSION_OPT': 1, 'INLINE_VERSION_PROMOTION': 0,
        'REUSE_VERSION': 1, 'WRITE_LATEST_ONLY': 0}
# Each named group occupies one node. The union is the complete S9 table.
GROUPS = {
    'rr50_wait': tuple(f'rr50-{kind}-gc{gc}' for kind in ('wait1', 'wait10') for gc in (10, 100)),
    'rr50_other': tuple(f'rr50-{kind}-gc{gc}' for kind in ('many', 'ronly') for gc in (10, 100)),
    'rr95': tuple(f'rr95-{kind}-gc{gc}' for kind in ('wait1', 'wait10', 'many', 'ronly') for gc in (10, 100)),
    'two_long': ('rr50-wait10-two-gc10',),
}
CELLS = {}
for rr in (50, 95):
    for kind in ('wait1', 'wait10', 'many', 'ronly'):
        for gc in (10, 100):
            CELLS[f'rr{rr}-{kind}-gc{gc}'] = dict(rratio=rr, kind=kind, gc_inter_us=gc,
                                                  long_threads=1, wait_us=1000 if kind == 'wait1' else 10000)
CELLS['rr50-wait10-two-gc10'] = dict(rratio=50, kind='wait10', gc_inter_us=10,
                                      long_threads=2, wait_us=10000)
VERIFY_CELLS = {
    'K': (50, False, 10, 'wait_after_reads', 0),
    'W': (0, True, 5, 'wait_after_reads', 0),
    'R': (90, False, 4, 'wait_after_reads', 0),
    'wait_after_reads': (50, False, 10, 'wait_after_reads', 1),
    'ronly_wait': (50, False, 10, 'ronly_wait', 1),
}
INTEGRITY_NUMERIC = ('orphan_reads', 'version_dups', 'dup_txids', 'genesis_commits',
                     'missing_txids', 'write_version_mismatch', 'malformed_keys',
                     'framing_violations', 'lock_coverage_violations',
                     'write_intent_violations', 'permutation_violations')
MACRO_NAMES = ('CICADA_INTERVAL_GC', 'CICADA_INTERVAL_GC_GENERAL',
               'CICADA_INTERVAL_COUNT', 'CICADA_INTERVAL_LONGTX')
FAILURE_LOG_DIR = ContextVar('vhash_igc_failure_log_dir', default=None)


class ResidualBenchmarkError(RuntimeError):
    """A timed-out command left a benchmark that could contaminate later runs."""


def kill_group_and_confirm(child, *, check_benchmark=True):
    """Kill a command's process group, reap its leader, and check for survivors."""
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()
    if check_benchmark:
        for _ in range(20):
            remaining = competing_bench_pids()
            if not remaining:
                return
            time.sleep(0.05)
        raise ResidualBenchmarkError(f'benchmark survived process-group kill: {remaining}')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return digest(Path(path).read_bytes())


def checked(argv, *, cwd=None, timeout=900, build_log=None):
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if build_log is not None:
            build_log.record(argv, exc.stdout or b'', exc.stderr or b'', None,
                             label='timeout')
        else:
            log_failed_command(argv, exc.stdout or b'', exc.stderr or b'', None)
        raise
    if build_log is not None:
        build_log.record(argv, result.stdout, result.stderr, result.returncode)
    if result.returncode:
        if build_log is None:
            log_failed_command(argv, result.stdout, result.stderr, result.returncode)
        raise RuntimeError(f'command failed {result.returncode}: {argv!r}; {result.stderr[-2000:]!r}')
    return result


def log_failed_command(argv, stdout, stderr, rc):
    directory = FAILURE_LOG_DIR.get()
    if directory is None:
        return None
    path = directory / f'failed-command-{len(list(directory.iterdir())) + 1:04d}.log'
    log = BuildLog(path)
    try:
        log.record(argv, stdout, stderr, rc, label='failed command')
    finally:
        log.close()
    return path


class BuildLog:
    """Create-only, complete command output for one attempted build."""

    def __init__(self, path):
        self.path = path
        self.handle = path.open('xb')
        self.rc = None

    def record(self, argv, stdout, stderr, rc, *, label='command'):
        if isinstance(stdout, str):
            stdout = stdout.encode()
        if isinstance(stderr, str):
            stderr = stderr.encode()
        if rc is not None and rc != 0:
            self.rc = rc
        self.handle.write((f'[{label}] argv={argv!r} rc={rc}\n'
                           f'[stdout bytes={len(stdout)}]\n').encode())
        self.handle.write(stdout)
        self.handle.write(f'\n[stderr bytes={len(stderr)}]\n'.encode())
        self.handle.write(stderr)
        self.handle.write(b'\n[end command]\n')
        self.handle.flush()

    def close(self):
        self.handle.close()


def attempt_build(manifest, out, name, source, build, deps, toolchain, arm, kind,
                  *, dependency=False, diag=False):
    log = BuildLog(out / 'build-logs' / (name + '.log'))
    try:
        binary, receipts = _build_variant(source, build, deps, toolchain, arm, kind,
                                          dependency=dependency, build_log=log, diag=diag)
        entry = {'ok': True, 'rc': 0, 'sha256': sha_file(binary),
                 'gate_receipts': receipts, 'perf_eligible': not diag and perf_eligible(kind)}
        return binary, receipts
    except Exception as exc:
        log.handle.write(f'\n[build error] {type(exc).__name__}: {exc}\n'.encode())
        entry = {'ok': False, 'rc': log.rc if log.rc is not None else 1,
                 'command_rc': log.rc,
                 'error': {'type': type(exc).__name__, 'message': str(exc)}}
        return None
    finally:
        log.close()
        entry['log'] = {'path': str(log.path), 'sha256': sha_file(log.path)}
        manifest['builds'][name] = entry


def run_measured(argv, *, cwd=None, env=None, timeout=180, before_timeout_kill=None):
    """wait4 captures this child, rather than a cumulative RUSAGE_CHILDREN high water mark."""
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        deadline = time.monotonic() + timeout
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                break
            if time.monotonic() >= deadline:
                try:
                    if before_timeout_kill is not None:
                        before_timeout_kill(child.pid)
                finally:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    os.wait4(child.pid, 0)
                    child.returncode = -signal.SIGKILL
                    for _ in range(20):
                        remaining = competing_bench_pids()
                        if not remaining:
                            break
                        time.sleep(0.05)
                    else:
                        raise ResidualBenchmarkError(
                            f'benchmark survived process-group kill: {remaining}')
                stdout.seek(0)
                stderr.seek(0)
                output, errors = stdout.read(), stderr.read()
                log_failed_command(argv, output, errors, None)
                raise subprocess.TimeoutExpired(argv, timeout, output=output, stderr=errors)
            time.sleep(0.01)
        stdout.seek(0)
        stderr.seek(0)
        return SimpleNamespace(returncode=child.returncode, stdout=stdout.read(),
                               stderr=stderr.read(), maxrss_kb=usage.ru_maxrss)


def arm_macros(arm, kind):
    if arm not in ARMS or kind not in ('perf', 'count', 'trace'):
        raise ValueError('invalid arm/build kind')
    result = {'CICADA_INTERVAL_LONGTX': 1}
    if arm != 'stock':
        result['CICADA_INTERVAL_GC'] = 1
    if arm == 'gen':
        result['CICADA_INTERVAL_GC_GENERAL'] = 1
    if kind == 'count':
        result['CICADA_INTERVAL_COUNT'] = 1
    return result


def order_rotation(rep):
    return ARMS[rep % 3:] + ARMS[:rep % 3]


def perf_eligible(kind):
    return kind == 'perf'


def plan_runs(group, no_gen_perf=False, smoke=False):
    names = ('rr50-wait1-gc10',) if smoke else GROUPS[group]
    result = []
    for name in names:
        for rep in range(1 if smoke else 3):
            for index, arm in enumerate(order_rotation(rep)):
                if arm == 'gen' and no_gen_perf:
                    continue
                result.append(dict(group=group, cell=name, arm=arm, rep=rep,
                                   order_index=index, build_kind='perf',
                                   extime=1 if smoke else 3))
        for index, arm in enumerate(ARMS):
            result.append(dict(group=group, cell=name, arm=arm, rep=0,
                               order_index=index, build_kind='count',
                               extime=1 if smoke else 3))
    return result


def assert_gate_receipts(macros, receipts):
    if set(macros) != {r.get('macro') for r in receipts} or len(receipts) != len(macros):
        raise RuntimeError('condition gate receipt missing')
    if any(r.get('admission', {}).get('admitted') is not True for r in receipts):
        raise RuntimeError('condition gate rejected')


def assert_gate_companion(macro, request):
    if (macro == 'CICADA_INTERVAL_GC_GENERAL' and
            ('CICADA_INTERVAL_GC', '1') not in request.companion_defines):
        raise RuntimeError('GC_GENERAL gate requires CICADA_INTERVAL_GC=1 companion')


def assert_solo():
    pids = competing_bench_pids()
    if pids:
        raise RuntimeError(f'competing benchmark processes: {pids}')
    return {'argv': ['pgrep', '-af', r'ycsb_.*\.exe'], 'competing': pids, 'at': now()}


def compile_entry(build, filename, target='ycsb_cicada.exe'):
    entries = json.loads((Path(build) / 'compile_commands.json').read_text())
    found = []
    for entry in entries:
        if Path(entry.get('file', '')).name != filename:
            continue
        argv = entry.get('arguments') or shlex.split(entry['command'])
        surface = ' '.join([*argv, entry.get('output', '')])
        if f'CMakeFiles/{target}.dir/' in surface:
            found.append(entry)
    if len(found) != 1:
        raise RuntimeError(f'{filename}: expected one {target} compile entry, found {len(found)}')
    return found[0]


def check_compile_commands(build, expected, trace, *, diag=False):
    # Include transaction.cc (macro owner), util.cc (shared definitions), and workload TU.
    checked_names = []
    for name in ('transaction.cc', 'util.cc', 'ycsb_cicada.cc'):
        entry = compile_entry(build, name)
        argv = entry.get('arguments') or shlex.split(entry['command'])
        defs = {}
        for token in argv:
            if token.startswith('-D') and '=' in token:
                key, value = token[2:].split('=', 1)
                defs[key] = value
        wanted = {'TRACE': str(trace), 'ADD_ANALYSIS': '0', 'SINGLE_EXEC': '0',
                  **{k: str(v) for k, v in BASE.items()},
                  **{k: str(v) for k, v in expected.items()}}
        for key, value in wanted.items():
            if defs.get(key) != value:
                raise RuntimeError(f'{name}: {key}={defs.get(key)!r}, expected {value}')
        for key in MACRO_NAMES:
            if key not in expected and key in defs:
                raise RuntimeError(f'{name}: unexpected {key}')
        if diag:
            if not all(flag in argv for flag in ('-g', '-fno-omit-frame-pointer', '-UNDEBUG')):
                raise RuntimeError(f'{name}: missing diagnostic compile flags')
            # CMake places CMAKE_CXX_FLAGS_RELEASE after CMAKE_CXX_FLAGS.
            if '-DNDEBUG' not in argv or max(i for i, flag in enumerate(argv) if flag == '-UNDEBUG') < max(
                    i for i, flag in enumerate(argv) if flag == '-DNDEBUG'):
                raise RuntimeError(f'{name}: NDEBUG remains enabled in diagnostic build')
        checked_names.append(name)
    return checked_names


@contextmanager
def capture_gate_commands(build_log):
    if build_log is None:
        yield
        return
    original = condition.subprocess.run

    def recorded(argv, *args, **kwargs):
        try:
            result = original(argv, *args, **kwargs)
        except subprocess.TimeoutExpired as exc:
            build_log.record(argv, exc.stdout or b'', exc.stderr or b'', None,
                             label='gate timeout')
            raise
        build_log.record(argv, result.stdout or b'', result.stderr or b'',
                         result.returncode, label='gate')
        return result

    condition.subprocess.run = recorded
    try:
        yield
    finally:
        condition.subprocess.run = original


def gate(source, macros, args, cxx, *, build_log=None):
    receipts = []
    with capture_gate_commands(build_log):
        for macro, value in macros.items():
            captured = condition.capture_define_inputs(source, configure_args=tuple(args))
            request = condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                                    requested_value=value, default_value=0)
            assert_gate_companion(macro, request)
            with condition._configured_define_compile_commands(captured, request=request,
                     cxx=cxx, cmake='cmake') as commands:
                supply = condition.evaluate_define_supply_effectuation(captured, request=request,
                         cxx=cxx, cmake='cmake', configured_commands=commands)
                meaning = condition.evaluate_define_runtime_meaning(captured, request=request,
                         declaration=condition.declare_define_runtime_meaning(request),
                         cxx=cxx, cmake='cmake', configured_commands=commands)
            admission = condition.require_condition_gate_family([supply], [meaning],
                                                                  use_class='raw-measurement')
            receipts.append({'macro': macro, 'value': value,
                             'supply': json.loads(supply.canonical_json()),
                             'meaning': json.loads(meaning.canonical_json()),
                             'admission': json.loads(admission.canonical_json())})
    assert_gate_receipts(macros, receipts)
    return receipts


def configure_args(deps, toolchain, trace):
    args = [a for a in compute._common_configure_args(trace=trace, toolchain=toolchain,
             dependencies=deps) if a not in compute.STOCK_G.cmake_defines()]
    names = {'BACK_OFF': 'CCBENCH_BACK_OFF', 'INLINE_VERSION_OPT': 'CCBENCH_INLINE_VERSION_OPT_CICADA',
             'INLINE_VERSION_PROMOTION': 'CCBENCH_INLINE_VERSION_PROMOTION',
             'REUSE_VERSION': 'CCBENCH_REUSE_VERSION',
             'WRITE_LATEST_ONLY': 'CCBENCH_WRITE_LATEST_ONLY'}
    return [a for a in args if not a.startswith('-DCMAKE_CXX_FLAGS=')] + [
        *(f'-D{names[k]}={v}' for k, v in BASE.items()),
        '-DCCBENCH_ADD_ANALYSIS=0', '-DCCBENCH_SINGLE_EXEC=0',
        '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']


def _build_variant(source, build, deps, toolchain, arm, kind, *, dependency=False,
                   build_log=None, diag=False):
    non_admissible_materializer(MATERIALIZER)
    trace = int(kind == 'trace')
    args = configure_args(deps, toolchain, trace)
    macros = {} if dependency else arm_macros(arm, kind)
    receipts = [] if dependency else gate(source, macros, args, toolchain['cxx_path'],
                                          build_log=build_log)
    flags = [*(f'-D{k}={v}' for k, v in macros.items())]
    if diag:
        flags.extend(('-g', '-fno-omit-frame-pointer', '-UNDEBUG'))
        # Release adds -DNDEBUG after CMAKE_CXX_FLAGS; override its suffix so
        # assertions remain enabled while retaining the Release optimization.
        args.append('-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -UNDEBUG')
    if flags:
        args.append('-DCMAKE_CXX_FLAGS=' + ' '.join(flags))
    checked(['cmake', '-S', str(source), '-B', str(build),
             '-DCMAKE_CXX_COMPILER=' + toolchain['cxx_path'], *args], timeout=600,
            build_log=build_log)
    checked(['cmake', '--build', str(build), '--target', 'ycsb_cicada.exe', '-j', '48'],
            build_log=build_log)
    binary = build / 'cc/cicada/ycsb_cicada.exe'
    if not binary.is_file():
        raise RuntimeError(f'missing binary {binary}')
    check_compile_commands(build, macros, trace, diag=diag)
    return binary, receipts


def preprocess(entry):
    argv = list(entry.get('arguments') or shlex.split(entry['command']))
    clean = []
    skip = False
    for arg in argv:
        if skip:
            skip = False
            continue
        if arg in ('-o', '-c'):
            skip = arg == '-o'
            continue
        clean.append(arg)
    output = checked([*clean, '-E'], cwd=Path(entry['directory']), timeout=180).stdout
    lines = (line for line in output.splitlines()
             if line.strip() and not line.lstrip().startswith(b'#'))
    return b'\n'.join(lines)


def inert_receipt(source, build, logs_dir):
    names = ('transaction.cc', 'util.cc', 'ycsb_cicada.cc')
    targets = ('ycsb_cicada.exe', 'tpcc_cicada.exe', 'bomb_cicada.exe', 'sbomb_cicada.exe')
    entries = [(target, name, compile_entry(build, name, target)) for target in targets
               for name in (*names[:2], target.split('_')[0] + '_cicada.cc')]
    before = {f'{t}/{n}': preprocess(e) for t, n, e in entries}
    applied = []
    try:
        for patch in PATCHES:
            checked(['git', '-C', str(source), 'apply', '--check', str(ROOT / patch)])
            checked(['git', '-C', str(source), 'apply', str(ROOT / patch)])
            applied.append(patch)
        after = {f'{t}/{n}': preprocess(e) for t, n, e in entries}
    finally:
        for patch in reversed(applied):
            checked(['git', '-C', str(source), 'apply', '-R', str(ROOT / patch)])
    receipt = {'before': {key: digest(data) for key, data in before.items()},
               'after': {key: digest(data) for key, data in after.items()},
               'matched': before == after,
               'normalization': 'omit preprocessor markers and whitespace-only lines',
               'units': {}}
    for target, name, _ in entries:
        key = f'{target}/{name}'
        matched = before[key] == after[key]
        unit = {'matched': matched}
        if not matched:
            diff = difflib.diff_bytes(
                difflib.unified_diff,
                [line + b'\n' for line in before[key].splitlines()],
                [line + b'\n' for line in after[key].splitlines()],
                fromfile=f'pin/{key}'.encode(), tofile=f'variant/{key}'.encode())
            first = []
            total = 0
            for line in diff:
                total += 1
                if total <= 400:
                    first.append(line)
            if total > 400:
                first.append(f'... diff truncated after 400 of {total} lines\n'.encode())
            path = logs_dir / f'inert-{target}-{name}.diff'
            data = b''.join(first)
            with path.open('xb') as handle:
                handle.write(data)
            unit['diff'] = {'path': str(path), 'sha256': digest(data),
                            'lines': total, 'shown_lines': min(total, 400)}
        receipt['units'][key] = unit
    return receipt


def parse_json_line(stdout, prefix, required):
    lines = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise ValueError(f'{prefix.strip()}: expected one line, got {len(lines)}')
    value = json.loads(lines[0])
    if not isinstance(value, dict) or not required <= value.keys():
        raise ValueError(f'{prefix.strip()}: invalid JSON schema')
    return value


def parse_counters(stdout, kind):
    longtx = parse_json_line(stdout, 'CICADA_IGC_LONGTX_V1 ',
                             {'schema', 'attempts', 'commits', 'aborts', 'residence_cycles_sum',
                              'residence_cycles_max', 'clocks_per_us'})
    if any(type(longtx[k]) is not int or longtx[k] < 0 for k in
           ('attempts', 'commits', 'aborts', 'residence_cycles_sum', 'residence_cycles_max',
            'clocks_per_us')) or longtx['schema'] != 1 or longtx['clocks_per_us'] == 0:
        raise ValueError('invalid longtx counters')
    interval = None
    if kind == 'count':
        interval = parse_json_line(stdout, 'CICADA_INTERVAL_V1 ',
                                   {'schema', 'debug_mode', 'chain_versions', 'chain_bytes',
                                    'reuse_pool', 'threads'})
        if interval['schema'] != 1 or interval.get('debug_mode') not in (-1, 1):
            raise ValueError('invalid interval count mode')
        interval_metrics(interval)
    elif 'CICADA_INTERVAL_V1 ' in stdout:
        raise ValueError('counter in perf/trace build')
    return interval, longtx


def counter_total(counter, name):
    if not isinstance(counter, dict):
        raise ValueError('invalid interval counter')
    threads = counter.get('threads')
    if threads is not None:
        if not isinstance(threads, list) or any(not isinstance(t, dict) for t in threads):
            raise ValueError('invalid interval thread counters')
        values = [t[name] for t in threads if name in t]
        if len(values) != len(threads):
            raise ValueError(f'missing interval counter {name}')
        if any(type(item) is not int or item < 0 for item in values):
            raise ValueError(f'invalid interval counter {name}')
        value = sum(values)
    else:
        value = counter.get(name)
    if type(value) is not int or value < 0:
        raise ValueError(f'invalid interval counter {name}')
    return value


def interval_metrics(counter):
    """Summarize the count line without conflating stock's absent GC with zero work."""
    if not isinstance(counter, dict) or not isinstance(counter.get('threads'), list) or not counter['threads']:
        raise ValueError('missing interval threads')
    mode = counter.get('debug_mode')
    if mode not in (-1, 1) or type(mode) is not int:
        raise ValueError('invalid interval mode')
    fields = ('chain_versions', 'chain_bytes', 'pruned_pending', 'pruned_pending_bytes',
              'reuse_pool', 'retired_versions', 'retired_bytes')
    gc_top_fields = {'pruned_pending', 'pruned_pending_bytes', 'retired_versions', 'retired_bytes'}
    result = {}
    missing = []
    for name in fields:
        value = counter.get(name)
        if value is None and mode == -1 and name in gc_top_fields:
            value = 0
            missing.append(name)
        if type(value) is not int or value < 0:
            raise ValueError(f'invalid interval counter {name}')
        result[name] = value
    result['missing_fields'] = missing
    result['debug_mode'] = mode
    result['gc_status'] = 'absent' if mode == -1 else 'measured'
    thread_fields = ('installed', 'installed_bytes', 'stock_removed', 'stock_removed_bytes',
                     'retention_unknown', 'write_hops', 'boundary_samples', 'boundary_age_sum')
    gc_fields = ('attempts', 'success', 'cas_fail', 'lock_fail', 'pruned', 'pruned_bytes',
                 'reuse', 'reuse_bytes', 'retired_current', 'retired_bytes',
                 'install_lock_spins', 'install_lock_wait_tsc')
    for name in thread_fields:
        result[name] = counter_total(counter, name)
    for name in gc_fields:
        key = 'thread_retired_bytes' if name == 'retired_bytes' else name
        result[key] = (0 if mode == -1 else counter_total(counter, name))
    result['gc_fields_status'] = 'not_applicable' if mode == -1 else 'measured'
    for name in ('prune_age_log2', 'stock_age_log2', 'retire_age_log2'):
        rows = [thread.get(name) for thread in counter['threads']]
        if mode == -1 and name != 'stock_age_log2':
            for i, row in enumerate(rows):
                if row is None:
                    rows[i] = [0] * 64
                    missing.append(f'threads[{i}].{name}')
        if any(not isinstance(row, list) or len(row) != 64 or
               any(type(value) is not int or value < 0 for value in row) for row in rows):
            raise ValueError(f'invalid interval bucket {name}')
        result[name] = [sum(row[i] for row in rows) for i in range(64)]
    hops = [thread.get('hops') for thread in counter['threads']]
    if any(not isinstance(row, list) or len(row) != 2 or
           any(not isinstance(pair, list) or len(pair) != 2 or
               any(type(value) is not int or value < 0 for value in pair) for pair in row)
           for row in hops):
        raise ValueError('invalid interval hops')
    result['hops'] = [[sum(row[i][j] for row in hops) for j in range(2)] for i in range(2)]
    modes = []
    for thread in counter['threads']:
        row = thread.get('debug_modes')
        if not isinstance(row, list) or len(row) != 4 or any(
                not isinstance(entry, dict) or entry.get('mode') != i or
                any(type(entry.get(name)) is not int or entry[name] < 0 for name in
                    ('calls', 'intervals', 'versions')) for i, entry in enumerate(row)):
            raise ValueError('invalid interval debug modes')
        modes.append(row)
    result['debug_modes'] = [
        {'mode': i, **{name: sum(row[i][name] for row in modes) for name in
                       ('calls', 'intervals', 'versions')}} for i in range(4)]
    return result


def smoke_candidate_delta(counters):
    minimum = counter_total(counters['min'], 'success')
    general = counter_total(counters['gen'], 'success')
    return {'minimum_prune_success': minimum, 'general_prune_success': general,
            'beyond_minimum_candidate': max(0, general - minimum)}


def parse_overprune(stderr):
    events, fired = [], []
    for line in stderr.splitlines():
        if line.startswith('CICADA_OVERPRUNE_EVENT '):
            pairs = dict(re.findall(r'([a-z_]+)=([^ ]+)', line))
            if not {'key', 'removed_wts'} <= pairs.keys():
                raise ValueError('malformed overprune event')
            events.append({'key': pairs['key'], 'removed_wts': int(pairs['removed_wts'], 0),
                           'tx_wts': int(pairs.get('tx_wts', '0'), 0)})
        elif line.startswith('CICADA_OVERPRUNE_FIRED '):
            match = re.fullmatch(r'CICADA_OVERPRUNE_FIRED n=(\d+)', line)
            if not match:
                raise ValueError('malformed overprune fired')
            fired.append(int(match[1]))
    if len(fired) != 1 or fired[0] != len(events):
        raise ValueError('overprune count mismatch')
    return {'events': events, 'fired': fired[0]}


def version_wts(version, initial_wts):
    if version == [1, 0]:
        return initial_wts
    if not isinstance(version, list) or len(version) != 2 or any(type(x) is not int for x in version):
        raise ValueError('malformed witness version')
    return (version[0] << 32) | version[1]


def attribute_overprune(verifier_result, diagnostics, long_txids, initial_wts):
    matches = []
    for anomaly in verifier_result.get('anomalies', []):
        for edge in anomaly.get('edges', []):
            if edge.get('from') not in long_txids and edge.get('to') not in long_txids:
                continue
            for reason in edge.get('reasons', []):
                for event in diagnostics['events']:
                    if str(reason.get('key')) != event['key']:
                        continue
                    read_version = reason.get('u_ver') if edge.get('from') in long_txids else reason.get('v_ver')
                    if read_version is None:
                        continue
                    if version_wts(read_version, initial_wts) < event['removed_wts']:
                        matches.append({'edge': edge, 'event': event})
    return matches


def aggregate(records, *, no_gen_perf=False, require_parts=False):
    if require_parts:
        found = {r.get('part_id') for r in records}
        expected = set(plan_parts())
        if found != expected:
            raise ValueError(f'missing planned parts: {sorted(expected - found)}; '
                             f'unexpected parts: {sorted(found - expected, key=str)}')
        for part in expected:
            planned = part_specs(part)
            actual = [r for r in records if r.get('part_id') == part]
            if plan_parts()[part]['command'] == 'run-part':
                key = lambda r: (r.get('cell'), r.get('arm'), r.get('rep'),
                                 r.get('build_kind'))
            else:
                key = lambda r: (r.get('cell'), r.get('thread'), r.get('arm'))
            if len(actual) != len(planned) or {key(r) for r in actual} != {key(r) for r in planned}:
                raise ValueError(f'incomplete or duplicate part records: {part}')
    verification = aggregate_verification(records) if require_parts else None
    if verification and verification['status'] == 'failed':
        raise ValueError('correctness verification failed: ' +
                         json.dumps(verification, ensure_ascii=False, sort_keys=True))
    planned = set(CELLS)
    cells = {}
    for record in records:
        if not record.get('valid') or record.get('cell') not in planned:
            continue
        key = record['cell']
        cell = cells.setdefault(key, {'perf': {arm: {} for arm in ARMS},
                                      'count': {arm: None for arm in ARMS}})
        arm = record['arm']
        if record['build_kind'] == 'perf' and record.get('perf_eligible') is True:
            if record['rep'] in cell['perf'][arm]:
                raise ValueError('duplicate perf rep')
            cell['perf'][arm][record['rep']] = record['throughput_tps']
        elif record['build_kind'] == 'count' and record.get('perf_eligible') is False:
            if cell['count'][arm] is not None:
                raise ValueError('duplicate count record')
            cell['count'][arm] = {'interval': interval_metrics(record['interval_counter']),
                                  'longtx': record.get('longtx_counter')}
    if set(cells) != planned:
        raise ValueError(f'missing planned cells: {sorted(planned - set(cells))}')
    result = {}
    for key, cell in cells.items():
        medians = {}
        for arm in ARMS:
            required = set() if no_gen_perf and arm == 'gen' else {0, 1, 2}
            if set(cell['perf'][arm]) != required:
                raise ValueError(f'missing perf rep {key}/{arm}')
            medians[arm] = median(cell['perf'][arm].values()) if required else None
            if cell['count'][arm] is None:
                raise ValueError(f'missing count {key}/{arm}')
        result[key] = {'perf_median_tps': medians, 'count': cell['count']}
    return {'schema': 'vhash-interval-gc-aggregate/v1', 'cells': result,
            'verification': verification, 'status': verification['status'] if verification else None,
            'complete': True,
            'perf_status': '未検証の診断値'}


def bench_argv(binary, cell, extime, thread=None, count=False):
    if cell in CELLS:
        c = CELLS[cell]
        rr, rmw, ops, kind = c['rratio'], False, 10, c['kind']
        threads, tuples, long_threads, wait, gc = 48, 1000000, c['long_threads'], c['wait_us'], c['gc_inter_us']
        kind = {'wait1': 'wait_after_reads', 'wait10': 'wait_after_reads',
                'many': 'many_ops', 'ronly': 'ronly_wait'}[kind]
    else:
        rr, rmw, ops, kind, long_threads = VERIFY_CELLS[cell]
        threads, tuples, wait, gc = thread, 200, 1000, 10
    return [str(binary), f'-thread_num={threads}', f'-ycsb_tuple_num={tuples}',
            '-ycsb_zipf_skew=0.9', f'-ycsb_rratio={rr}', f'-ycsb_rmw={str(rmw).lower()}',
            f'-ycsb_max_ope={ops}', f'-extime={extime}', '-clocks_per_us=2100',
            f'-gc_inter_us={gc}', '-group_commit=0',
            f'--cicada_igc_long_threads={long_threads}', f'--cicada_igc_long_kind={kind}',
            '--cicada_igc_long_ops=1000', '--cicada_igc_long_rratio=90',
            f'--cicada_igc_long_wait_us={wait}', '--cicada_igc_wait_reads=10',
            *([f'--cicada_igc_count_long_threads={long_threads}'] if count else [])]


def run_binary(binary, spec, receipts, hashes, raw_dir):
    assert_gate_receipts(arm_macros(spec['arm'], spec['build_kind']), receipts)
    probe = assert_solo()
    argv = bench_argv(binary, spec['cell'], spec['extime'], count=spec['build_kind'] == 'count')
    started = now()
    completed = run_measured(argv)
    stem = f"{spec['cell']}-{spec['arm']}-{spec['build_kind']}-r{spec['rep']}"
    stdout_path, stderr_path = raw_dir / (stem + '.stdout'), raw_dir / (stem + '.stderr')
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    if completed.returncode:
        log_failed_command(argv, completed.stdout, completed.stderr, completed.returncode)
        raise RuntimeError(f'benchmark rc={completed.returncode}: {stderr_path}')
    out = completed.stdout.decode('utf-8', 'replace')
    interval, longtx = parse_counters(out, spec['build_kind'])
    throughput = parse_bench_stdout(out).get('throughput[tps]')
    commit = re.findall(r'^commit_counts_:\s*(\d+)\s*$', out, re.M)
    abort = re.findall(r'^abort_counts_:\s*(\d+)\s*$', out, re.M)
    if throughput is None or not re.fullmatch(r'\d+(?:\.\d+)?', throughput):
        raise ValueError('missing throughput[tps]')
    if len(commit) != 1 or len(abort) != 1:
        raise ValueError('missing commit or abort counts')
    commits, aborts = int(commit[0]), int(abort[0])
    return {**spec, 'valid': True, 'returncode': completed.returncode,
            'host': socket.gethostname(), 'started_utc': started,
            'perf_eligible': perf_eligible(spec['build_kind']),
            'verification_status': '未検証の診断値', 'throughput_tps': float(throughput),
            'abort_rate': aborts / (commits + aborts) if commits + aborts else None,
            'commit_count': commits,
            'maxrss_kb': completed.maxrss_kb,
            'argv': argv, 'binary_sha256': sha_file(binary), 'patch_sha256': hashes,
            'gate_receipts': receipts, 'gate_receipt_present': bool(receipts),
            'competing_probe': probe,
            'stdout': {'path': str(stdout_path), 'sha256': digest(completed.stdout)},
            'stderr': {'path': str(stderr_path), 'sha256': digest(completed.stderr)},
            'interval_counter': interval, 'interval_metrics': interval_metrics(interval) if interval else None,
            'longtx_counter': longtx}


def run_diagnostic(binary, spec, receipts, out, *, run_timeout=60, gdb_timeout=120):
    """Run a non-measurement build and retain debugger output on abnormal exit."""
    assert_gate_receipts(arm_macros(spec['arm'], spec['build_kind']), receipts)
    assert_solo()
    argv = bench_argv(binary, spec['cell'], spec['extime'],
                      count=spec['build_kind'] == 'count')
    if spec.get('debug_mode') is not None:
        if spec['arm'] == 'stock' or spec['debug_mode'] not in range(4):
            raise ValueError('debug mode requires min/gen and a value from 0 to 3')
        argv.append(f"--cicada_igc_debug_mode={spec['debug_mode']}")
    name = f"{spec['arm']}-{spec['build_kind']}-diag"
    debugger = shutil.which('gdb')
    attach = []

    def debugger_call(command, *, attach=False):
        if debugger is None:
            return (command, b'', b'gdb unavailable\n', None, 'unavailable')
        try:
            child = subprocess.Popen(command, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, start_new_session=True)
            try:
                stdout, stderr = child.communicate(timeout=gdb_timeout)
                return (command, stdout, stderr, child.returncode, 'gdb')
            except subprocess.TimeoutExpired:
                try:
                    kill_group_and_confirm(child, check_benchmark=not attach)
                except ResidualBenchmarkError as exc:
                    log_failed_command(command, b'', str(exc).encode(), None)
                    raise
                stdout, stderr = child.communicate()
                return (command, stdout, stderr, None, 'gdb timeout')
        except OSError as exc:
            return (command, b'', str(exc).encode(), None, 'gdb error')

    def before_kill(pid):
        attach.append(debugger_call([debugger or 'gdb', '-batch', '-p', str(pid),
                                     '-ex', 'thread apply all bt 20'], attach=True))

    timed_out = False
    try:
        completed = run_measured(argv, timeout=run_timeout,
                                 before_timeout_kill=before_kill)
        rc = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out, rc = True, None
        timed_out_stdout, timed_out_stderr = exc.stdout or b'', exc.stderr or b''
    abnormal = timed_out or rc != 0
    stdout = timed_out_stdout if timed_out else completed.stdout
    stderr = timed_out_stderr if timed_out else completed.stderr
    result = {'build': name, 'perf_eligible': False, 'argv': argv,
              'returncode': rc, 'signal': -rc if rc is not None and rc < 0 else None,
              'timeout': timed_out, 'abnormal': abnormal,
              'stdout': stdout.decode('utf-8', 'replace'),
              'stderr': stderr.decode('utf-8', 'replace'),
              'count_lines': [line for line in stdout.decode('utf-8', 'replace').splitlines()
                              if line.startswith(('CICADA_INTERVAL_V1 ',
                                                  'CICADA_IGC_LONGTX_V1 '))]}
    suffix = '' if spec['cell'] == 'rr50-wait1-gc10' else f"-{spec['cell']}"
    if spec.get('debug_mode') is not None:
        suffix += f"-mode{spec['debug_mode']}"
    log = BuildLog(out / 'logs' / f'diag-{name}{suffix}.log')
    try:
        log.record(argv, stdout, stderr, rc,
                   label='diagnostic run timeout' if timed_out else 'diagnostic run')
        if abnormal:
            for command, stdout, stderr, code, label in attach:
                log.record(command, stdout, stderr, code, label='attach ' + label)
            command = [debugger or 'gdb', '-batch', '-ex', 'run',
                       '-ex', 'thread apply all bt 20', '--args', *argv]
            rerun_command, stdout, stderr, code, label = debugger_call(command)
            log.record(rerun_command, stdout, stderr, code, label='rerun ' + label)
    finally:
        log.close()
    result['log'] = {'path': str(log.path), 'sha256': sha_file(log.path)}
    return result


def parse_debug_modes(value):
    try:
        modes = tuple(int(part) for part in value.split(','))
    except ValueError as exc:
        raise ValueError('debug modes must be comma-separated integers from 0 to 3') from exc
    if not modes or len(set(modes)) != len(modes) or any(mode not in range(4) for mode in modes):
        raise ValueError('debug modes must be unique integers from 0 to 3')
    return modes


def trace_counts(trace_dir):
    counts = {tag: 0 for tag in 'CRWE'}
    for path in sorted(trace_dir.glob('trace_*.log')):
        for line in path.read_text(errors='replace').splitlines():
            parts = line.split()
            if parts and parts[0] in counts:
                counts[parts[0]] += 1
    return counts


def verify_binary(binary, source, spec, receipts, hashes, raw_dir):
    macros = arm_macros('min' if spec['arm'] == 'broken' else spec['arm'], 'trace')
    assert_gate_receipts(macros, receipts)
    probe = assert_solo()
    trace_dir = raw_dir / (spec['name'] + '.trace')
    trace_dir.mkdir(exist_ok=False)
    argv = bench_argv(binary, spec['cell'], 1, thread=spec['thread'])
    completed = run_measured(argv, cwd=trace_dir,
                             env=dict(os.environ, IZANAGI_TRACE_DIR=str(trace_dir)))
    out, err = completed.stdout.decode('utf-8', 'replace'), completed.stderr.decode('utf-8', 'replace')
    stdout_path, stderr_path = raw_dir / (spec['name'] + '.stdout'), raw_dir / (spec['name'] + '.stderr')
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    if completed.returncode:
        log_failed_command(argv, completed.stdout, completed.stderr, completed.returncode)
        raise RuntimeError(f'verify benchmark rc={completed.returncode}: {stderr_path}')
    commit = re.findall(r'^commit_counts_:\s*(\d+)\s*$', out, re.M)
    mismatch = re.findall(r'^CICADA_TRACE_READ_WTS_MISMATCH n=(\d+)$', err, re.M)
    initial = re.findall(r'^CICADA_TRACE_INITIAL_WTS=(\d+)$', err, re.M)
    if len(commit) != 1 or len(mismatch) != 1 or len(initial) != 1:
        raise ValueError('missing trace counters')
    counts = trace_counts(trace_dir)
    if counts['C'] != int(commit[0]):
        raise ValueError('C rows differ from commit count')
    verifier_argv = [sys.executable, '-m', 'verifier', str(trace_dir), '--json', '--quiet',
                     '--protocol', 'cicada', '--ccbench-root', str(source),
                     '--expected-commits', commit[0]]
    try:
        verification = subprocess.run(verifier_argv, cwd=ROOT / 'orchestrator',
                                      capture_output=True, timeout=900)
    except subprocess.TimeoutExpired as exc:
        log_failed_command(verifier_argv, exc.stdout or b'', exc.stderr or b'', None)
        raise
    if verification.returncode not in (0, 1, 3):
        log_failed_command(verifier_argv, verification.stdout, verification.stderr,
                           verification.returncode)
        raise RuntimeError(f'verifier rc={verification.returncode}: {verification.stderr[-500:]!r}')
    result = json.loads(verification.stdout)['results'][0]
    integrity = result.get('integrity') or {}
    if any(integrity.get(key) != 0 for key in INTEGRITY_NUMERIC):
        raise ValueError('integrity numeric error')
    if int(mismatch[0]):
        raise ValueError('CICADA_TRACE_READ_WTS_MISMATCH')
    if result.get('certified') is True:
        raise ValueError('Cicada proof limit exceeded')
    verifier_path = raw_dir / (spec['name'] + '.verifier.json')
    verifier_path.write_bytes(verification.stdout)
    record = {**spec, 'host': socket.gethostname(), 'argv': argv,
              'binary_sha256': sha_file(binary), 'patch_sha256': hashes,
              'gate_receipts': receipts, 'competing_probe': probe,
              'trace_counts': counts, 'commit_count': int(commit[0]),
              'read_wts_mismatch': int(mismatch[0]), 'initial_wts': int(initial[0]),
              'integrity': {key: integrity[key] for key in INTEGRITY_NUMERIC},
              'verdict': result.get('verdict'), 'total_cycles': result.get('total_cycles'),
              'certification_limit': 'indeterminate', 'verifier_result': result,
              'verifier_argv': verifier_argv,
              'verifier_json': {'path': str(verifier_path), 'sha256': digest(verification.stdout)},
              'stdout': {'path': str(stdout_path), 'sha256': digest(completed.stdout)},
              'stderr': {'path': str(stderr_path), 'sha256': digest(completed.stderr)}}
    if spec['arm'] == 'broken':
        record['overprune'] = parse_overprune(err)
        # The long thread id is the final worker; trace txids encode worker id.
        long_id = spec['thread'] - 1
        long_txids = {int(parts[1]) for path in trace_dir.glob('trace_*.log')
                      for line in path.read_text(errors='replace').splitlines()
                      if (parts := line.split()) and parts[0] == 'C'
                      and path.name == f'trace_{long_id}.log'}
        record['attributed_edges'] = attribute_overprune(result, record['overprune'],
                                                          long_txids, int(initial[0]))
    return record


def classify_broken(broken, stock):
    if stock['total_cycles'] != 0 or stock['verdict'] != 'indeterminate':
        return '対照異常'
    if broken['overprune']['fired'] == 0:
        return '発火 0'
    if (broken['verdict'] == 'non-serializable' and broken['total_cycles'] > 0
            and broken.get('attributed_edges')
            and all(broken.get('integrity', {}).get(key) == 0 for key in INTEGRITY_NUMERIC)
            and broken.get('trace_counts', {}).get('C') == broken.get('commit_count')):
        return '期待した経路で検出'
    return '未検出または帰属不能'


def aggregate_verification(records):
    """Summarize every correctness cell and enforce the S8 positive control."""
    verify = [r for r in records if r.get('arm') in (*ARMS, 'broken')
              and 'thread' in r]
    by_cell = {(r['cell'], r['thread'], r['arm']): r for r in verify}
    controls = []
    broken_rows = []
    for cell, thread in sorted({(r['cell'], r['thread']) for r in verify}):
        stock = by_cell[cell, thread, 'stock']
        for arm in ARMS:
            record = by_cell[cell, thread, arm]
            reasons = []
            if record.get('total_cycles') != 0:
                reasons.append('cycles')
            if any(record.get('integrity', {}).get(key) != 0 for key in INTEGRITY_NUMERIC):
                reasons.append('integrity')
            if record.get('trace_counts', {}).get('C') != record.get('commit_count'):
                reasons.append('commit_rows')
            if record.get('verdict') != 'indeterminate':
                reasons.append('verdict')
            if record.get('read_wts_mismatch') != 0:
                reasons.append('read_wts_mismatch')
            controls.append({'cell': cell, 'thread': thread, 'arm': arm,
                             'cycles': record.get('total_cycles'),
                             'integrity': record.get('integrity'),
                             'disqualified': bool(reasons), 'reasons': reasons})
        broken = by_cell[cell, thread, 'broken']
        classification = classify_broken(broken, stock)
        broken_rows.append({'cell': cell, 'thread': thread,
                            'classification': classification,
                            'cycles': broken.get('total_cycles'),
                            'fired': broken.get('overprune', {}).get('fired', 0),
                            'attributed_witnesses': len(broken.get('attributed_edges', [])),
                            'integrity': broken.get('integrity'),
                            'commit_rows_match': broken.get('trace_counts', {}).get('C') ==
                                                 broken.get('commit_count')})
    detected = [r for r in broken_rows if r['classification'] == '期待した経路で検出']
    positives = [r for r in detected if r['cell'] == 'ronly_wait']
    auxiliary = [{**r, 'attribution_basis':
                  ('長い tx の無い cell で末尾 worker を代役にした事前登録外の帰属'
                   if r['cell'] in ('K', 'W', 'R') and r['attributed_witnesses'] else
                   '帰属 0 の事前登録外の巡回検出' if not r['attributed_witnesses'] else
                   '事前登録外の cell での帰属')}
                 for r in broken_rows if r['cell'] != 'ronly_wait'
                 and r['cycles'] is not None and r['cycles'] > 0
                 and by_cell[r['cell'], r['thread'], 'broken'].get('verdict') == 'non-serializable']
    disqualified = [r for r in controls if r['disqualified']]
    status = ('failed' if disqualified or not (positives or auxiliary) else
              'passed' if positives else 'normal_arms_passed_s8_positive_unmet')
    return {'status': status, 'positive_count': len(positives),
            'auxiliary_detection_count': len(auxiliary),
            'positive': positives, 'auxiliary_detections': auxiliary,
            'disqualified': disqualified,
            'controls': controls, 'broken': broken_rows}


def write_x(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def append_x(path, records):
    with path.open('x', encoding='utf-8') as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')


def apply_patches(source, names):
    for name in names:
        checked(['git', '-C', str(source), 'apply', '--check', str(ROOT / name)])
        checked(['git', '-C', str(source), 'apply', str(ROOT / name)])


def plan_parts():
    """Stable 34 measurement and six correctness jobs."""
    parts = {}
    for cell in CELLS:
        for kind in ('perf', 'count'):
            part = f'run-{cell}-{kind}'
            parts[part] = {'command': 'run-part', 'cell': cell, 'kind': kind,
                           'estimated_run_seconds': 27 if kind == 'perf' else 9,
                           'runs': 9 if kind == 'perf' else 3}
    for cell in VERIFY_CELLS:
        if cell == 'ronly_wait':
            for thread in (4, 8):
                parts[f'verify-{cell}-t{thread}'] = {'command': 'verify-part',
                                                     'cell': cell, 'thread': thread, 'runs': 4}
        else:
            parts[f'verify-{cell}'] = {'command': 'verify-part', 'cell': cell, 'runs': 8}
    return parts


def part_specs(part):
    plan = plan_parts()[part]
    if plan['command'] == 'run-part':
        cell, kind = plan['cell'], plan['kind']
        group = next(name for name, cells in GROUPS.items() if cell in cells)
        reps = range(3) if kind == 'perf' else range(1)
        return [dict(group=group, cell=cell, arm=arm, rep=rep,
                     order_index=index, build_kind=kind, extime=3)
                for rep in reps
                for index, arm in enumerate(order_rotation(rep) if kind == 'perf' else ARMS)]
    cell = plan['cell']
    arms = (*ARMS, 'broken')
    return [dict(cell=cell, thread=thread, arm=arm,
                 name=f'{cell}-t{thread}-{arm}')
            for thread in ((plan['thread'],) if 'thread' in plan else (4, 8)) for arm in arms]


def bundle_binary(directory, manifest, arm, kind):
    name = f'{arm}-{kind}'
    entry = manifest['builds'][name]
    expected = arm_macros('min' if arm == 'broken' else arm, kind)
    if (entry.get('macros') != expected or entry.get('compile_commands_checked') is not True
            or not entry.get('ok')):
        raise ValueError(f'invalid build manifest: {name}')
    assert_gate_receipts(expected, entry['gate_receipts'])
    binary = directory / 'binaries' / name
    if not binary.is_file() or sha_file(binary) != entry['sha256']:
        raise ValueError(f'binary sha256 mismatch: {name}')
    return binary, entry['gate_receipts']


def load_bundle(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest.get('schema') != 'vhash-interval-gc-binaries/v1' or manifest.get('status') != 'completed':
        raise ValueError('incomplete binary manifest')
    if manifest.get('pin') != pin.CURRENT_PIN or not manifest.get('inert', {}).get('matched'):
        raise ValueError('binary bundle pin or inert mismatch')
    for name in (*PATCHES, TRACE_PATCH, BROKEN_PATCH):
        if manifest.get('patches', {}).get(name) != sha_file(ROOT / name):
            raise ValueError(f'patch sha256 mismatch: {name}')
    for kind in ('perf', 'count', 'trace'):
        for arm in ARMS:
            bundle_binary(directory, manifest, arm, kind)
    bundle_binary(directory, manifest, 'broken', 'trace')
    return manifest


def build_bundle(args):
    host = socket.gethostname()
    if re.fullmatch(r'pegasus0\d+', host):
        raise RuntimeError('build requires a compute node')
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output
    for name in ('raw', 'build-logs', 'logs', 'binaries'):
        (out / name).mkdir()
    manifest = {'schema': 'vhash-interval-gc-binaries/v1', 'status': 'started',
                'pin': pin.CURRENT_PIN, 'host': host, 'started_utc': now(),
                'patches': {}, 'builds': {}}
    token = FAILURE_LOG_DIR.set(out / 'logs')
    try:
        assert_solo()
        policy = compute._load_policy(ROOT / 'tools/pegasus/mocc_trace_v1_policy.json')
        toolchain = compute._resolve_toolchain(policy)
        with tempfile.TemporaryDirectory(prefix='vhash-igc-', dir=args.scratch_root) as tmp:
            scratch = Path(tmp)
            deps = compute._prepare_dependencies(ROOT, policy, args.third_party_cache,
                                                  scratch, toolchain)
            with patchharness.checkout(pin.CURRENT_PIN) as source:
                source = Path(source)
                def one(name, tree, arm, kind, *, dependency=False):
                    result = attempt_build(manifest, out, name, tree, scratch / name,
                                           deps, toolchain, arm, kind, dependency=dependency)
                    if result is None:
                        raise RuntimeError(f'build failed: {name}')
                    binary, _ = result
                    entry = manifest['builds'][name]
                    entry['macros'] = {} if dependency else arm_macros(arm, kind)
                    entry['compile_commands_checked'] = True
                    entry['compile_commands_sha256'] = sha_file(
                        scratch / name / 'compile_commands.json')
                    if not dependency:
                        target = out / 'binaries' / name
                        with target.open('xb') as handle:
                            handle.write(binary.read_bytes())
                        target.chmod(stat.S_IMODE(binary.stat().st_mode))
                        entry['sha256'] = sha_file(target)
                    return result
                one('dependency', source, 'stock', 'perf', dependency=True)
                manifest['inert'] = inert_receipt(source, scratch / 'dependency', out / 'logs')
                if not manifest['inert']['matched']:
                    raise RuntimeError('inert preprocessing mismatch')
                apply_patches(source, PATCHES)
                for kind in ('perf', 'count'):
                    for arm in ARMS:
                        one(f'{arm}-{kind}', source, arm, kind)
            with patchharness.checkout(pin.CURRENT_PIN) as trace_source:
                trace_source = Path(trace_source)
                apply_patches(trace_source, [TRACE_PATCH, *PATCHES])
                for arm in ARMS:
                    one(f'{arm}-trace', trace_source, arm, 'trace')
                apply_patches(trace_source, [BROKEN_PATCH])
                one('broken-trace', trace_source, 'min', 'trace')
        for name in (*PATCHES, TRACE_PATCH, BROKEN_PATCH):
            manifest['patches'][name] = sha_file(ROOT / name)
        manifest['status'] = 'completed'
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        raise
    finally:
        manifest['ended_utc'] = now()
        write_x(out / 'manifest.json', manifest)
        FAILURE_LOG_DIR.reset(token)


def execute_part(args):
    plan = plan_parts()[args.part]
    if plan['command'] != args.command:
        raise ValueError('part and command differ')
    if re.fullmatch(r'pegasus0\d+', socket.gethostname()):
        raise RuntimeError('measurement requires a compute node')
    bundle = load_bundle(args.binaries)
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output
    (out / 'raw').mkdir()
    (out / 'logs').mkdir()
    token = FAILURE_LOG_DIR.set(out / 'logs')
    records = []
    job = {'schema': 'vhash-interval-gc-part/v1', 'part_id': args.part,
           'binary_manifest_sha256': sha_file(args.binaries / 'manifest.json'),
           'started_utc': now(), 'status': 'started'}
    try:
        for spec in part_specs(args.part):
            kind = spec.get('build_kind', 'trace')
            binary, receipts = bundle_binary(args.binaries, bundle, spec['arm'], kind)
            if not os.access(binary, os.X_OK):
                raise PermissionError(f'bundled binary is not executable: {binary}')
            if args.command == 'run-part':
                record = run_binary(binary, spec, receipts, bundle['patches'], out / 'raw')
            else:
                record = verify_binary(binary, ROOT / 'external/ccbench', spec, receipts,
                                       bundle['patches'], out / 'raw')
                if spec['arm'] in ARMS and (record['total_cycles'] != 0 or
                                           record['verdict'] != 'indeterminate'):
                    raise RuntimeError('interval GC correctness control failed')
                if spec['arm'] == 'broken':
                    stock = next(r for r in records if r['cell'] == spec['cell'] and
                                 r['thread'] == spec['thread'] and
                                 r['arm'] == 'stock')
                    record['classification'] = classify_broken(record, stock)
            record['part_id'] = args.part
            records.append(record)
        append_x(out / 'raw.jsonl', records)
        job['status'] = 'completed'
    except Exception as exc:
        job['status'] = 'failed'
        job['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        raise
    finally:
        job['ended_utc'] = now()
        job['records'] = len(records)
        write_x(out / 'manifest.json', job)
        FAILURE_LOG_DIR.reset(token)


def run_job(args):
    host = socket.gethostname()
    if re.fullmatch(r'pegasus0\d+', host):
        raise RuntimeError('build and measurement require a compute node')
    assert_solo()
    started = now()
    out = args.output / f'{args.command}-{args.group or args.job or "all"}-{started.replace(":", "-")}'
    out.mkdir(parents=True, exist_ok=False)
    raw_dir = out / 'raw'
    raw_dir.mkdir()
    (out / 'build-logs').mkdir()
    logs_dir = out / 'logs'
    logs_dir.mkdir()
    log_token = FAILURE_LOG_DIR.set(logs_dir)
    manifest = {'schema': 'vhash-interval-gc-job/v1', 'command': args.command,
                'group': args.group, 'job': args.job, 'host': host, 'started_utc': started,
                'pin': pin.CURRENT_PIN, 'patches': {}, 'builds': {}, 'records': [],
                'status': 'started', 'verification_status': '実装済み・未実走'}
    try:
        policy = compute._load_policy(ROOT / 'tools/pegasus/mocc_trace_v1_policy.json')
        toolchain = compute._resolve_toolchain(policy)
        with tempfile.TemporaryDirectory(prefix='vhash-igc-', dir=args.scratch_root) as tmp:
            scratch = Path(tmp)
            deps = compute._prepare_dependencies(ROOT, policy, args.third_party_cache,
                                                  scratch, toolchain)
            with patchharness.checkout(pin.CURRENT_PIN) as checkout:
                source = Path(checkout)
                failures = []

                def build_one(name, tree, arm, kind, *, dependency=False, diag=False):
                    result = attempt_build(manifest, out, name, tree, scratch / name,
                                           deps, toolchain, arm, kind,
                                           dependency=dependency, diag=diag)
                    if result is None:
                        failures.append(name)
                        if args.command != 'smoke':
                            raise RuntimeError(f'build failed: {name}; '
                                               f'{manifest["builds"][name]["log"]["path"]}')
                    return result

                dependency = build_one('dependency', source, 'stock', 'perf',
                                       dependency=True)
                if args.command == 'smoke' and dependency is not None:
                    try:
                        manifest['inert'] = inert_receipt(source, scratch / 'dependency', logs_dir)
                        if not manifest['inert']['matched']:
                            manifest['inert']['error'] = 'inert preprocessing mismatch'
                            failures.append('inert')
                    except Exception as exc:
                        manifest['inert'] = {'matched': False, 'error': str(exc)}
                        failures.append('inert')
                names = ([TRACE_PATCH, *PATCHES] if args.command == 'verify' else list(PATCHES))
                apply_patches(source, names)
                for name in names:
                    manifest['patches'][name] = sha_file(ROOT / name)
                binaries = {}
                kinds = ('trace',) if args.command == 'verify' else ('perf', 'count')
                for kind in kinds:
                    for arm in ARMS:
                        result = build_one(f'{arm}-{kind}', source, arm, kind)
                        if result is not None:
                            binaries[arm, kind] = result
                diagnostics = {}
                if args.command == 'smoke' and getattr(args, 'diag_builds', False):
                    for kind in ('perf', 'count'):
                        for arm in ARMS:
                            name = f'{arm}-{kind}-diag'
                            result = build_one(name, source, arm, kind, diag=True)
                            if result is not None:
                                diagnostics[arm, kind] = result
                if args.command == 'verify':
                    apply_patches(source, [BROKEN_PATCH])
                    manifest['patches'][BROKEN_PATCH] = sha_file(ROOT / BROKEN_PATCH)
                    binaries['broken', 'trace'] = build_one('broken-trace', source, 'min', 'trace')
                elif args.command == 'smoke' and args.with_trace_builds:
                    with patchharness.checkout(pin.CURRENT_PIN) as trace_checkout:
                        trace_source = Path(trace_checkout)
                        apply_patches(trace_source, [TRACE_PATCH, *PATCHES])
                        manifest['patches'][TRACE_PATCH] = sha_file(ROOT / TRACE_PATCH)
                        for arm in ARMS:
                            build_one(f'{arm}-trace', trace_source, arm, 'trace')
                        apply_patches(trace_source, [BROKEN_PATCH])
                        manifest['patches'][BROKEN_PATCH] = sha_file(ROOT / BROKEN_PATCH)
                        build_one('broken-trace', trace_source, 'min', 'trace')
                records = []
                if args.command == 'verify':
                    for cell in VERIFY_CELLS:
                        for thread in (4, 8):
                            for arm in (*ARMS, 'broken'):
                                spec = {'cell': cell, 'thread': thread, 'arm': arm,
                                        'name': f'{cell}-t{thread}-{arm}'}
                                binary, receipts = binaries[arm, 'trace']
                                records.append(verify_binary(binary, source, spec, receipts,
                                                             manifest['patches'], raw_dir))
                    for record in records:
                        if record['arm'] == 'broken':
                            stock = next(r for r in records if r['cell'] == record['cell'] and
                                         r['thread'] == record['thread'] and r['arm'] == 'stock')
                            record['classification'] = classify_broken(record, stock)
                    normal = [r for r in records if r['arm'] in ARMS]
                    if any(r['total_cycles'] != 0 or r['verdict'] != 'indeterminate'
                           for r in normal):
                        raise RuntimeError('interval GC correctness control failed')
                    if not any(r['cell'] == 'ronly_wait' and
                               r['classification'] == '期待した経路で検出'
                               for r in records if r['arm'] == 'broken'):
                        raise RuntimeError('overprune positive control not attributed')
                else:
                    if args.command == 'smoke' and diagnostics:
                        manifest['diagnostics'] = {}
                        diagnostic_cells = ('rr50-wait1-gc10', 'rr95-ronly-gc10')
                        for cell in diagnostic_cells:
                            for spec in plan_runs('rr50_wait', smoke=True):
                                spec = {**spec, 'cell': cell, 'extime': 3}
                                built = diagnostics.get((spec['arm'], spec['build_kind']))
                                if built is None:
                                    continue
                                name = f"{spec['arm']}-{spec['build_kind']}-diag"
                                modes = (None,)
                                if cell == 'rr50-wait1-gc10' and spec['arm'] != 'stock':
                                    modes = getattr(args, 'debug_modes', ()) or (None,)
                                for mode in modes:
                                    mode_spec = {**spec, 'debug_mode': mode} if mode is not None else spec
                                    key = name if cell == diagnostic_cells[0] else f'{name}-{cell}'
                                    if mode is not None:
                                        key += f'-mode{mode}'
                                    try:
                                        manifest['diagnostics'][key] = run_diagnostic(
                                            built[0], mode_spec, built[1], out,
                                            run_timeout=args.diag_run_timeout,
                                            gdb_timeout=args.diag_gdb_timeout)
                                        if manifest['diagnostics'][key]['abnormal']:
                                            failures.append(key + '-run')
                                    except ResidualBenchmarkError as exc:
                                        manifest['diagnostics'][key] = {'error': str(exc),
                                                                        'perf_eligible': False}
                                        raise
                                    except Exception as exc:
                                        failures.append(key + '-run')
                                        manifest['diagnostics'][key] = {'error': str(exc),
                                                                        'perf_eligible': False}
                    for spec in plan_runs(args.group or 'rr50_wait', args.no_gen_perf,
                                          smoke=args.command == 'smoke'):
                        built = binaries.get((spec['arm'], spec['build_kind']))
                        if built is None:
                            continue
                        binary, receipts = built
                        if args.command == 'smoke':
                            try:
                                records.append(run_binary(binary, spec, receipts,
                                                          manifest['patches'], raw_dir))
                            except ResidualBenchmarkError:
                                raise
                            except Exception as exc:
                                name = f'{spec["arm"]}-{spec["build_kind"]}-run'
                                failures.append(name)
                                manifest.setdefault('run_failures', {})[name] = str(exc)
                        else:
                            records.append(run_binary(binary, spec, receipts,
                                                      manifest['patches'], raw_dir))
                    if args.command == 'smoke':
                        manifest['smoke_counters'] = {r['arm']: r['interval_counter'] for r in records
                                                      if r['build_kind'] == 'count'}
                        if {'min', 'gen'} <= manifest['smoke_counters'].keys():
                            manifest['smoke_candidates'] = smoke_candidate_delta(
                                manifest['smoke_counters'])
                manifest['records'] = records
                append_x(out / 'raw.jsonl', records)
                if failures:
                    raise RuntimeError(f'builds failed: {", ".join(failures)}')
                manifest['status'] = 'completed'
                manifest['verification_status'] = ('indeterminate' if args.command == 'verify'
                                                   else '未検証の診断値')
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        raise
    finally:
        manifest['ended_utc'] = now()
        write_x(out / 'manifest.json', manifest)
        FAILURE_LOG_DIR.reset(log_token)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('smoke', 'run', 'verify', 'build',
                                            'plan-jobs', 'run-part', 'verify-part', 'aggregate'))
    parser.add_argument('--group', choices=GROUPS)
    parser.add_argument('--job')
    parser.add_argument('--no-gen-perf', action='store_true')
    parser.add_argument('--with-trace-builds', action='store_true')
    parser.add_argument('--diag-builds', action='store_true')
    parser.add_argument('--debug-modes', type=parse_debug_modes, default=())
    parser.add_argument('--diag-run-timeout', type=float, default=60)
    parser.add_argument('--diag-gdb-timeout', type=float, default=120)
    parser.add_argument('--third-party-cache', type=Path)
    parser.add_argument('--scratch-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--raw', type=Path, nargs='+', action='extend')
    parser.add_argument('--part')
    parser.add_argument('--binaries', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'plan-jobs':
        for part, plan in plan_parts().items():
            command = plan['command']
            print(json.dumps({'part_id': part, **plan,
                              'argv': ['python3', '-m', DRIVER_ID, command, '--part', part,
                                       '--binaries', '<shared-dir>', '--output', '<part-dir>'],
                              'estimated_load_seconds': f'{plan["runs"]} × DB load (node dependent)',
                              'estimated_total_seconds':
                              f'{plan.get("estimated_run_seconds", plan["runs"])} + '
                              f'{plan["runs"]} × DB load + verifier overhead'}, sort_keys=True))
        return 0
    if args.command == 'aggregate':
        if not args.raw or args.output is None:
            parser.error('aggregate requires --raw and --output')
        if not args.output.is_absolute() or args.output.resolve() == ROOT or ROOT in args.output.resolve().parents:
            parser.error('aggregate --output must be absolute and outside the repository')
        records = [json.loads(line) for path in args.raw for line in path.read_text().splitlines()]
        write_x(args.output / 'aggregate.json', aggregate(records, no_gen_perf=args.no_gen_perf,
                                                         require_parts=True))
        return 0
    if args.command in ('run-part', 'verify-part'):
        if args.part not in plan_parts() or args.binaries is None or args.output is None:
            parser.error('part commands require valid --part, --binaries and --output')
        if not args.binaries.is_absolute() or not args.output.is_absolute():
            parser.error('part paths must be absolute')
        if ROOT in args.output.resolve().parents or args.output.resolve() == ROOT:
            parser.error('part output must be outside the repository')
        execute_part(args)
        return 0
    if args.command == 'build':
        if any(value is None or not value.is_absolute() for value in
               (args.third_party_cache, args.scratch_root, args.output)):
            parser.error('build requires absolute cache, scratch and output paths')
        if any(path == ROOT or ROOT in path.parents for path in
               (args.scratch_root.resolve(), args.output.resolve())):
            parser.error('build paths must be outside the repository')
        build_bundle(args)
        return 0
    if args.command == 'run' and not args.group:
        parser.error('run requires --group')
    if args.no_gen_perf and args.command not in ('run', 'aggregate'):
        parser.error('--no-gen-perf applies to run and aggregate only')
    if args.with_trace_builds and args.command != 'smoke':
        parser.error('--with-trace-builds applies to smoke only')
    if args.diag_builds and args.command != 'smoke':
        parser.error('--diag-builds applies to smoke only')
    if args.debug_modes and not (args.command == 'smoke' and args.diag_builds):
        parser.error('--debug-modes requires smoke --diag-builds')
    if args.diag_run_timeout <= 0 or args.diag_gdb_timeout <= 0:
        parser.error('diagnostic timeouts must be positive')
    if args.command == 'verify' and not args.job:
        parser.error('verify requires --job')
    if args.job and not re.fullmatch(r'[A-Za-z0-9_-]+', args.job):
        parser.error('--job must be a simple name')
    if any(value is None or not value.is_absolute() for value in
           (args.third_party_cache, args.scratch_root, args.output)):
        parser.error('build commands require absolute --third-party-cache, --scratch-root, --output')
    if any(path == ROOT or ROOT in path.parents for path in
           (args.scratch_root.resolve(), args.output.resolve())):
        parser.error('--scratch-root and --output must be outside the repository')
    print(run_job(args))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
