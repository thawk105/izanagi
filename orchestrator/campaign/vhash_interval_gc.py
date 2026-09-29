#!/usr/bin/env python3
"""Cicada interval GC diagnostic and correctness campaign (compute node only)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
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
MATERIALIZER = DRIVER_ID + '.build_variant'
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


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return digest(Path(path).read_bytes())


def checked(argv, *, cwd=None, timeout=900):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'command failed {result.returncode}: {argv!r}; {result.stderr[-2000:]!r}')
    return result


def run_measured(argv, *, cwd=None, env=None, timeout=180):
    """wait4 captures this child, rather than a cumulative RUSAGE_CHILDREN high water mark."""
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
        deadline = time.monotonic() + timeout
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                break
            if time.monotonic() >= deadline:
                child.kill()
                os.wait4(child.pid, 0)
                raise subprocess.TimeoutExpired(argv, timeout)
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


def check_compile_commands(build, expected, trace):
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
        checked_names.append(name)
    return checked_names


def gate(source, macros, args, cxx):
    receipts = []
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


def build_variant(source, build, deps, toolchain, arm, kind, *, dependency=False):
    non_admissible_materializer(MATERIALIZER)
    trace = int(kind == 'trace')
    args = configure_args(deps, toolchain, trace)
    macros = {} if dependency else arm_macros(arm, kind)
    receipts = [] if dependency else gate(source, macros, args, toolchain['cxx_path'])
    if macros:
        args.append('-DCMAKE_CXX_FLAGS=' + ' '.join(f'-D{k}={v}' for k, v in macros.items()))
    checked(['cmake', '-S', str(source), '-B', str(build),
             '-DCMAKE_CXX_COMPILER=' + toolchain['cxx_path'], *args], timeout=600)
    checked(['cmake', '--build', str(build), '--target', 'ycsb_cicada.exe', '-j', '48'])
    binary = build / 'cc/cicada/ycsb_cicada.exe'
    if not binary.is_file():
        raise RuntimeError(f'missing binary {binary}')
    check_compile_commands(build, macros, trace)
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
    return digest(b'\n'.join(line for line in output.splitlines()
                             if line.strip() and not line.lstrip().startswith(b'#')))


def inert_receipt(source, build):
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
    receipt = {'before': before, 'after': after, 'matched': before == after,
               'normalization': 'omit preprocessor markers and whitespace-only lines'}
    if not receipt['matched']:
        raise RuntimeError('inert preprocessing mismatch')
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
                             {'attempts', 'commits', 'aborts', 'residence_cycles_sum', 'residence_cycles_max'})
    if any(type(longtx[k]) is not int or longtx[k] < 0 for k in
           ('attempts', 'commits', 'aborts', 'residence_cycles_sum', 'residence_cycles_max')):
        raise ValueError('invalid longtx counters')
    interval = None
    if kind == 'count':
        interval = parse_json_line(stdout, 'CICADA_INTERVAL_V1 ', {'schema'})
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
        value = sum(values)
    else:
        value = counter.get(name)
    if type(value) is not int or value < 0:
        raise ValueError(f'invalid interval counter {name}')
    return value


def smoke_candidate_delta(counters):
    minimum = counter_total(counters['min'], 'prune_success')
    general = counter_total(counters['gen'], 'prune_success')
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


def aggregate(records, *, no_gen_perf=False):
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
            cell['count'][arm] = record['interval_counter']
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
            'complete': True, 'perf_status': '未検証の診断値'}


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
            'interval_counter': interval, 'longtx_counter': longtx}


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
    verification = subprocess.run(verifier_argv, cwd=ROOT / 'orchestrator',
                                  capture_output=True, timeout=900)
    if verification.returncode not in (0, 1, 3):
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
    if (broken['verdict'] == 'non-serializable' and broken['total_cycles'] > 0
            and broken.get('attributed_edges') and broken['overprune']['fired'] > 0):
        return '期待した経路で検出'
    return '未検出または帰属不能'


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
                dependency, _ = build_variant(source, scratch / 'dependency', deps, toolchain,
                                              'stock', 'perf', dependency=True)
                manifest['builds']['dependency'] = {'sha256': sha_file(dependency)}
                if args.command == 'smoke':
                    manifest['inert'] = inert_receipt(source, scratch / 'dependency')
                names = ([TRACE_PATCH, *PATCHES] if args.command == 'verify' else list(PATCHES))
                apply_patches(source, names)
                for name in names:
                    manifest['patches'][name] = sha_file(ROOT / name)
                binaries = {}
                kinds = ('trace',) if args.command == 'verify' else ('perf', 'count')
                for kind in kinds:
                    for arm in ARMS:
                        binary, receipts = build_variant(source, scratch / f'{arm}-{kind}',
                                                         deps, toolchain, arm, kind)
                        binaries[arm, kind] = binary, receipts
                        manifest['builds'][f'{arm}-{kind}'] = {
                            'sha256': sha_file(binary), 'gate_receipts': receipts}
                if args.command == 'verify':
                    apply_patches(source, [BROKEN_PATCH])
                    manifest['patches'][BROKEN_PATCH] = sha_file(ROOT / BROKEN_PATCH)
                    binary, receipts = build_variant(source, scratch / 'broken-trace',
                                                     deps, toolchain, 'min', 'trace')
                    binaries['broken', 'trace'] = binary, receipts
                    manifest['builds']['broken-trace'] = {
                        'sha256': sha_file(binary), 'gate_receipts': receipts}
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
                    for spec in plan_runs(args.group or 'rr50_wait', args.no_gen_perf,
                                          smoke=args.command == 'smoke'):
                        binary, receipts = binaries[spec['arm'], spec['build_kind']]
                        records.append(run_binary(binary, spec, receipts,
                                                  manifest['patches'], raw_dir))
                    if args.command == 'smoke':
                        manifest['smoke_counters'] = {r['arm']: r['interval_counter'] for r in records
                                                      if r['build_kind'] == 'count'}
                        manifest['smoke_candidates'] = smoke_candidate_delta(
                            manifest['smoke_counters'])
                manifest['records'] = records
                append_x(out / 'raw.jsonl', records)
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
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('smoke', 'run', 'verify', 'aggregate'))
    parser.add_argument('--group', choices=GROUPS)
    parser.add_argument('--job')
    parser.add_argument('--no-gen-perf', action='store_true')
    parser.add_argument('--third-party-cache', type=Path)
    parser.add_argument('--scratch-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--raw', type=Path, action='append')
    args = parser.parse_args(argv)
    if args.command == 'aggregate':
        if not args.raw or args.output is None:
            parser.error('aggregate requires --raw and --output')
        if not args.output.is_absolute() or args.output.resolve() == ROOT or ROOT in args.output.resolve().parents:
            parser.error('aggregate --output must be absolute and outside the repository')
        records = [json.loads(line) for path in args.raw for line in path.read_text().splitlines()]
        write_x(args.output / 'aggregate.json', aggregate(records, no_gen_perf=args.no_gen_perf))
        return 0
    if args.command == 'run' and not args.group:
        parser.error('run requires --group')
    if args.no_gen_perf and args.command not in ('run', 'aggregate'):
        parser.error('--no-gen-perf applies to run and aggregate only')
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
