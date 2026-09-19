# runner の逐語 — `verify_phase_runner.py` (Codex `role=author` 作、段 6 fix 1 は Codex `role=fix`、repo へは入れない)

- v1 (走行に使った版): 1301 行、sha256 `91bbf85d594085a4900bb2e9272bd455cef18e83c258ccfe5828594c0afd82a7` — 原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.v1-run.py`
- v2 (段 6 fix 1、最終集計に使った版): 1384 行、sha256 `c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5` — 原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.py`
- v1 → v2 の差分は `summarize` の ruling sha 検査に許可集合 (`--accept-ruling-sha`) と段別開示を足したもの (README §6.3、`s6-fix-1.md`)。走行経路 (calibrate / verify / reverify) は同一。

## v2 — verify_phase_runner.py

```python
#!/usr/bin/env python3.10
"""Disposable adopted-backoff verification runner. Configuration is argv-only.

The s4 ruling is authoritative. No performance claims are made from trace runs.
Process timing and build/dependency mechanics derive from verifier_cli_timing_probe.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import copy
import fcntl
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from uuid import uuid4

PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
SCHEMA = "verify-phase-adopted-backoff/v1"
CANDIDATES = {
    "fixed-5": {"BACKOFF_FIXED": 5, "expected": "678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12"},
    "fixed-10": {"BACKOFF_FIXED": 10, "expected": "16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d"},
}
WORKLOADS = {"write-heavy": "5", "balanced": "50", "read-heavy": "95"}
EXTIMES = (3, 6, 10)
STAGES = "setup hydrate build bench count preserve verify cleanup".split()
TIMING_KEYS = "t_popen_monotonic t_popen_returned_monotonic t_wait_monotonic wall_s communicate_window_s rusage rc started_epoch finished_epoch pid signal".split()
REQUIRED = "schema_version phase candidate workload extime job_index rep_id bench_attempt_id verify_attempt_id hostname started_at finished_at runner_sha256 ruling_sha256 bindings seed_mode seed seed_identity bench count verify execution_status failure_reason operational_outcome preservation job_accounting".split()

def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def timing_record():
    return {**dict.fromkeys(TIMING_KEYS), "timed_out": False}


def configure_argv(source, build, policy, toolchain, dependencies, candidate):
    return ["cmake", "-S", str(source), "-B", str(build),
            "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF", *defines(candidate),
            "-DCCBENCH_CCACHE=OFF", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
            "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=",
            f"-DCMAKE_PREFIX_PATH={dependencies['gflags']};{dependencies['glog']}",
            f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={dependencies['masstree']}",
            f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={dependencies['mimalloc']}",
            f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={dependencies['googletest']}",
            f"-DIZANAGI_GFLAGS_SRC_HEAD={policy['gflags_expected_head']}",
            f"-DIZANAGI_GLOG_SRC_HEAD={policy['glog_expected_head']}",
            f"-DCMAKE_C_COMPILER={toolchain['cc_path']}",
            f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}", "-DCMAKE_CXX_FLAGS="]


def timing_values(start, returned, end, epoch_start, epoch_end, status, usage):
    return dict(t_popen_monotonic=start, t_popen_returned_monotonic=returned,
                t_wait_monotonic=end, wall_s=end - start,
                communicate_window_s=end - returned, started_epoch=epoch_start,
                finished_epoch=epoch_end, rc=os.waitstatus_to_exitcode(status),
                rusage={k: getattr(usage, k) for k in ("ru_utime", "ru_stime", "ru_maxrss")})


def timed_process(argv, cwd, timeout, stdout, stderr, env=None, on_started=None):
    """wait4 is the sole reaper (no poll/wait/communicate consuming rusage).

    Watchdog kills only this child's new process group. Deadline includes Popen.
    Linux ru_maxrss is KiB. Output file opening is outside the measured interval.
    """
    record = timing_record()
    done = threading.Event()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        epoch_start = time.time()
        start = time.monotonic()
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err,
                                start_new_session=True)
        returned = time.monotonic()

        def watchdog():
            if not done.wait(max(0.0, timeout - (time.monotonic() - start))):
                record["timed_out"] = True
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        timer = threading.Thread(target=watchdog, daemon=True)
        timer.start()
        try:
            if on_started is not None:
                on_started(dict(t_popen_monotonic=start, t_popen_returned_monotonic=returned,
                                pid=proc.pid, started_epoch=epoch_start))
            _, status, usage = os.wait4(proc.pid, 0)
            end = time.monotonic()
            epoch_end = time.time()
            done.set()
            proc.returncode = os.waitstatus_to_exitcode(status)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, _ = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(status)
            raise
        finally:
            done.set()
            timer.join()
        record.update(timing_values(start, returned, end, epoch_start, epoch_end, status, usage))
        record.update(pid=proc.pid, signal=-proc.returncode if proc.returncode < 0 else None)
    return record


def count_c_lines(trace_dir):
    # Exactly the counting loop/text I/O of pipeline._run_trace.
    n = 0
    if os.path.isdir(trace_dir):
        for fn in os.listdir(trace_dir):
            if fn.startswith("trace_") and fn.endswith(".log"):
                with open(os.path.join(trace_dir, fn)) as f:
                    n += sum(1 for line in f if line.startswith("C "))
    return n


def helpers(repo):
    sys.path.insert(0, str(repo))
    names = {
        'driver': ('campaign.s3_mocc_lock_coverage', '_run_checked _load_policy _resolve_toolchain _prepare_dependencies'),
        'tenant': ('campaign.p2_2', '_assert_single_tenant'),
        'patch': ('campaign.patchharness', 'checkout applied assert_pinned_clean'),
        'digest': ('campaign.source_digest', 'resolve_evidence'),
        'pipeline': ('campaign.pipeline', '_parse_commit_witness _parse_abort_counts'),
        'parse': ('verifier.parse', '_effective_worker_count'),
        'calibration': ('campaign.s1_verify_extime_calibration', 'choose_extime'),
        'genome': ('campaign.genome', 'Genome'),
        'backoff': ('campaign.backoff_sweep', '_BASE'),
        'site': ('campaign.site_policy', 'current_site refuses_heavy_work is_pegasus_compute default_build_jobs'),
    }
    result = {}
    for alias, (module, attributes) in names.items():
        result[alias] = importlib.import_module('orchestrator.' + module)
        for attribute in attributes.split():
            getattr(result[alias], attribute)
    return result


def defines(candidate):
    return ['-DCCBENCH_TRACE=1', '-DCCBENCH_BACK_OFF=1',
            f'-DCCBENCH_BACKOFF_FIXED={CANDIDATES[candidate]["BACKOFF_FIXED"]}',
            '-DCCBENCH_BACKOFF_NOINLINE=0', '-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1',
            '-DCCBENCH_NO_WAIT_OF_TICTOC=0', '-DCCBENCH_WAL=0']


def bench_argv(binary, workload, extime):
    return [str(binary), '-ycsb_tuple_num=1000000', '-thread_num=48',
            '-ycsb_zipf_skew=0.9', f'-ycsb_rratio={WORKLOADS[workload]}',
            '-ycsb_rmw=0', '-ycsb_max_ope=10', f'-extime={extime}', '-clocks_per_us=2100']


def verifier_argv(trace, witness, source):
    if type(witness) is not int or witness < 0:
        raise ValueError('missing/invalid commit witness; cannot omit --expected-commits')
    return [os.path.realpath(sys.executable), '-B', '-m', 'orchestrator.verifier',
            str(trace), '--json', '--expected-commits', str(witness),
            '--protocol', 'silo', '--ccbench-root', str(source)]


def new_result(phase, candidate, workload, extime, job_index=0, rep_id=0, attempt=1):
    return dict(schema_version=SCHEMA, phase=phase, candidate=candidate, workload=workload,
                extime=extime, job_index=job_index, rep_id=rep_id, bench_attempt_id=attempt,
                verify_attempt_id=1, hostname=socket.gethostname(), started_at=now(),
                finished_at=None, runner_sha256=sha(__file__), ruling_sha256=None, bindings={},
                seed_mode='self-seeded', seed=None,
                seed_identity=dict(rep_id=rep_id, pid=None, started_epoch=None),
                bench={**timing_record(), **dict.fromkeys(
                    'argv cwd stdout_path stderr_path commit_witness batch_commit_witness abort_counts'.split()),
                    'completed': False},
                count=dict(wall_s=None, c_lines=None),
                verify={**timing_record(), **dict.fromkeys(
                    'argv cwd json_path stderr_path verdict certified anomaly_count total_cycles integrity'.split()),
                    'parse_ok': False, 'completed': False},
                execution_status='not_run', failure_reason=None, operational_outcome='not_run',
                preservation=dict(complete=False, wall_s=None, files=[], destination=None),
                job_accounting={}, stop_reason=None)


def project_verifier(rc, raw, timed_out=False):
    keys = 'verdict certified anomaly_count total_cycles integrity anomalies proof_surfaces stats'.split()
    result = {**dict.fromkeys(keys), 'parse_ok': False, 'completed': False,
              'operational_outcome': 'indeterminate'}
    try:
        payload = json.loads(raw)
        if payload['runs'] != 1 or len(payload['results']) != 1:
            raise ValueError('expected exactly one CLI result')
        v = payload['results'][0]
        if not isinstance(v, dict):
            raise ValueError('CLI result must be an object')
        for key in ('verdict', 'certified', 'anomaly_count', 'integrity'):
            if key not in v:
                raise ValueError('missing CLI field: ' + key)
        if (v['verdict'] not in ('serializable', 'non-serializable', 'indeterminate')
                or type(v['certified']) is not bool
                or type(v['anomaly_count']) is not int or v['anomaly_count'] < 0):
            raise ValueError('invalid CLI field type/value')
        result['parse_ok'] = True
        if not timed_out and rc in (0, 1, 3):
            result.update({key: v.get(key) for key in keys})
            result.update(completed=True, operational_outcome=(
                'cli-indeterminate' if rc == 3 else 'completed'))
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result['parse_error'] = str(exc)
    return result


def identity_matches(candidate, bindings):
    expected = CANDIDATES[candidate]['expected']
    return all(isinstance(bindings.get(stage), dict) and all(
        bindings[stage].get(key) == expected for key in ('src_token', 'source_bytes_sha256'))
        for stage in ('source_before', 'source_after'))


def anomaly(record):
    v = record['verify']
    return v['completed'] and (v['rc'] == 1 or v['verdict'] == 'non-serializable')


def eligible(record):
    v = record['verify']
    return (record['bench']['completed'] and v['completed'] and v['rc'] == 0
            and v['verdict'] == 'serializable' and v['certified'] is True
            and v['anomaly_count'] == 0 and isinstance(v['wall_s'], (int, float))
            and math.isfinite(v['wall_s']) and 0 <= v['wall_s'] <= 600)


def green(record):
    v = record['verify']
    return (record['bench']['completed'] and record['preservation']['complete']
            and v['completed'] and v['rc'] == 0 and v['verdict'] == 'serializable'
            and v['certified'] is True and v['anomaly_count'] == 0
            and identity_matches(record['candidate'], record['bindings']))


def stop_reason(record):
    if not record['bench']['completed']:
        return record['failure_reason'] or 'bench failed or not started'
    if not record['verify']['completed']:
        return record['failure_reason'] or 'verifier incomplete'
    if record['verify']['wall_s'] > 600:
        return 'verifier wall > 600 s'
    return None


def calibration_prefix(rows):
    prefix = []
    for e, row in zip(EXTIMES, rows):
        if row['extime'] != e or not row['bench']['completed'] or not row['verify']['completed']:
            break
        prefix.append(dict(extime=e, verifier_walltime_s=row['verify']['wall_s']))
        if row['verify']['wall_s'] > 600:
            break
    return prefix


def calibration_summary(rows, chooser):
    prefix = calibration_prefix(rows)
    chosen = None
    if prefix and prefix[0]['verifier_walltime_s'] <= 600:
        chosen = chooser(prefix, 600.0)
    elif prefix:
        # Still call the pure function; first-point over-limit raises CalibrationError.
        try:
            chooser(prefix, 600.0)
        except (ValueError, RuntimeError):
            pass
    es = [r['extime'] for r in rows if eligible(r)]
    if chosen not in es:
        chosen = max((e for e in es if chosen is not None and e <= chosen), default=None)
    return dict(rows=rows, eligible_set=es, chosen_max_eligible=chosen,
                chooser_prefix=prefix, anomaly_seen=any(anomaly(r) for r in rows),
                indeterminate_count=sum(is_indeterminate(r) for r in rows))


def is_indeterminate(record):
    return record['operational_outcome'] in ('indeterminate', 'cli-indeterminate')


def budget_estimate(rows, extime, fixed):
    selected = [r for r in rows if r['extime'] == extime and eligible(r)]
    if len(selected) != 3 or {r['workload'] for r in selected} != set(WORKLOADS):
        return None
    t = sum(8 * (r['bench']['wall_s'] + r['count']['wall_s'] + r['verify']['wall_s']) for r in selected)
    a = sum(8 * r['preservation']['wall_s'] for r in selected)
    return dict(T_s=t, A_s=a, F_s=6 * fixed, total_s=t + a + 6 * fixed)


def file_inventory(trace):
    files = []
    for path in sorted(trace.rglob('*')):
        if path.is_symlink():
            raise ValueError('unexpected trace symlink: ' + str(path))
        if path.is_file():
            with path.open('rb') as handle:
                lines = sum(1 for _ in handle)
            files.append(dict(name=path.relative_to(trace).as_posix(), sha256=sha(path),
                              bytes=path.stat().st_size, lines=lines))
    return files


def safe_child(root, name):
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()) or Path(name).is_absolute():
        raise ValueError('manifest path outside root')
    return path


def validate_file(path, digest, size):
    if path.stat().st_size != size or sha(path) != digest:
        raise ValueError('manifest sha256/bytes mismatch: ' + str(path))


def preserve(trace, output):
    start = time.monotonic()
    dest = output / 'trace'
    dest.mkdir()
    files = file_inventory(trace)
    zstd = shutil.which('zstd')
    for entry in files:
        source = safe_child(trace, entry['name'])
        name = entry['name'] + ('.zst' if zstd else '')
        target = safe_child(dest, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name('.' + target.name + '.' + uuid4().hex)
        try:
            if zstd:
                with temp.open('xb') as out:
                    p = subprocess.run([zstd, '-T0', '-3', '-c', str(source)], stdout=out,
                                       stderr=subprocess.PIPE, check=False)
                    if p.returncode:
                        raise RuntimeError('zstd compression failed: ' + p.stderr.decode(errors='replace'))
                    out.flush()
                    os.fsync(out.fileno())
            else:
                shutil.copyfile(source, temp)
                validate_file(temp, entry['sha256'], entry['bytes'])
                with temp.open('rb') as handle:
                    os.fsync(handle.fileno())
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        entry.update(codec='zstd' if zstd else 'none', stored_name=name,
                     preserved_path=str(target), stored_sha256=sha(target),
                     stored_bytes=target.stat().st_size,
                     compressed_sha256=sha(target) if zstd else None,
                     compressed_bytes=target.stat().st_size if zstd else None)
    result = dict(complete=True, destination=str(dest), files=files,
                  wall_s=time.monotonic() - start)
    write_json(output / 'preservation.json', result)
    return result


def restore(manifest, output, trace):
    if manifest.get('complete') is not True:
        raise ValueError('trace preservation incomplete')
    (trace / 'log').mkdir(parents=True)
    seen = set()
    for entry in manifest['files']:
        if entry['name'] in seen:
            raise ValueError('duplicate manifest file')
        seen.add(entry['name'])
        source = safe_child(output / 'trace', entry['stored_name'])
        validate_file(source, entry['stored_sha256'], entry['stored_bytes'])
        dest = safe_child(trace, entry['name'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        if entry['codec'] == 'zstd':
            zstd = shutil.which('zstd')
            if zstd is None:
                raise RuntimeError('zstd needed to restore this trace')
            with dest.open('xb') as handle:
                subprocess.run([zstd, '-d', '-c', str(source)], stdout=handle, check=True)
        elif entry['codec'] == 'none':
            shutil.copyfile(source, dest)
        else:
            raise ValueError('unknown trace codec')
        validate_file(dest, entry['sha256'], entry['bytes'])


class IdentityMismatch(RuntimeError):
    pass


@contextmanager
def stage(job, name):
    start = time.monotonic()
    try:
        yield
    finally:
        job['stage_wall_s'][name] += time.monotonic() - start


def evidence(h, source, genome, candidate, bindings, key):
    ev = h['digest'].resolve_evidence(genome, PIN, ccbench_dir=str(source), cxx='g++')
    fields = 'schema_version source_root ccbench_commit genome_sha256 src_token source_bytes_sha256 tracked_clean tracked_diff_sha256 tracked_paths'.split()
    bindings[key] = {k: getattr(ev, k) for k in fields}
    if any(bindings[key][k] != CANDIDATES[candidate]['expected']
           for k in ('src_token', 'source_bytes_sha256')):
        raise IdentityMismatch(f'{key}: source identity mismatch')


def prepare(args, h, scratch, job, stack, do_build=True):
    b = job['bindings']
    with stage(job, 'setup'):
        driver = h['driver']
        b.update(repo_head=driver._run_checked(['git', '-C', str(args.repo_root), 'rev-parse', 'HEAD']).stdout.strip(),
                 ccbench_pin=PIN, python_executable=os.path.realpath(sys.executable), python_version=sys.version,
                 patch_sha256=sha(args.repo_root / 'patches/silo-backoff-fixed.patch'),
                 verifier_module_sha256={p.name: sha(p) for p in sorted((args.repo_root / 'orchestrator/verifier').glob('*.py'))},
                 pipeline_module_sha256=sha(args.repo_root / 'orchestrator/campaign/pipeline.py'),
                 configure_defines=defines(args.candidate), numactl=[])
        policy_path = args.repo_root / 'tools/pegasus/mocc_trace_v1_policy.json'
        policy = driver._load_policy(policy_path)
        b['policy_sha256'] = sha(policy_path)
        toolchain = driver._resolve_toolchain(policy)
        b['toolchain'] = toolchain
        b['compiler'] = dict(realpath=os.path.realpath(shutil.which('g++')),
                             version=driver._run_checked([toolchain['cxx_path'], '--version']).stdout.splitlines()[0])
        if b['compiler']['realpath'] != os.path.realpath(toolchain['cxx_path']):
            raise RuntimeError('digest/build compiler mismatch')
        genome = h['genome'].Genome('silo', {**h['backoff']._BASE, 'BACK_OFF': 1,
                                           'BACKOFF_FIXED': CANDIDATES[args.candidate]['BACKOFF_FIXED']})
        b['genome'] = dict(protocol='silo', flags=dict(genome.flags), canonical=genome.canonical())
    if do_build:
        with stage(job, 'hydrate'):
            deps = driver._prepare_dependencies(args.repo_root, policy, args.third_party_cache, scratch, toolchain)
    with stage(job, 'setup'):
        source = Path(stack.enter_context(h['patch'].checkout(PIN, base_dir=str(args.repo_root / 'external/ccbench'))))
        h['patch'].assert_pinned_clean(str(source), PIN)
        stack.enter_context(h['patch'].applied(str(args.repo_root / 'patches/silo-backoff-fixed.patch'), PIN, str(source)))
        b.update(source_checkout=str(source), source_pinned_clean=True)
        evidence(h, source, genome, args.candidate, b, 'source_before')
    if do_build:
        with stage(job, 'build'):
            jobs = h['site'].default_build_jobs(job['site'])
            for name, target, timeout in [('warmup', 'masstree_build', 1200), ('build', 'ycsb_silo.exe', 900)]:
                argv = configure_argv(source, scratch / name, policy, toolchain, deps, args.candidate)
                b[name + '_configure_argv'] = argv
                driver._run_checked(argv)
                driver._run_checked(['cmake', '--build', str(scratch / name), '--target', target, '-j', str(jobs)], timeout=timeout)
            b['configure_argv'] = b['build_configure_argv']
            binary = scratch / 'build/cc/silo/ycsb_silo.exe'
            b.update(binary=str(binary), binary_sha256=sha(binary))
    with stage(job, 'setup'):
        evidence(h, source, genome, args.candidate, b, 'source_after')
    # Hydrate belongs to fixed setup cost; stage ledger entries remain disjoint.
    job['F_s'] = sum(job['stage_wall_s'][k] for k in ('setup', 'hydrate', 'build'))
    if job['F_s'] > 2400:
        raise RuntimeError('setup+build (including hydrate) exceeded 2400 s')
    return source


def run_verifier(args, h, record, trace, source, output, job, timeout):
    v = record['verify']
    v.update(argv=verifier_argv(trace, record['bench']['commit_witness'], source),
             cwd=str(args.repo_root), json_path=str(output / 'verifier.json'),
             stderr_path=str(output / 'verifier.stderr'))
    try:
        h['tenant']._assert_single_tenant()
    except Exception:
        record.update(execution_status='not_run', operational_outcome='not_run',
                      failure_reason='single-tenant check failed before verifier')
        raise

    def started(values):
        v.update(values)
        record.update(execution_status='verifier_running', operational_outcome='indeterminate')
        write_json(output / 'result.json', record)

    with stage(job, 'verify'):
        v.update(timed_process(v['argv'], args.repo_root, timeout, Path(v['json_path']), Path(v['stderr_path']),
                               on_started=started))
    v.update(project_verifier(v['rc'], Path(v['json_path']).read_text(errors='replace'), v['timed_out']))
    record['operational_outcome'] = v['operational_outcome']
    record['execution_status'] = 'completed' if v['completed'] else 'verifier_incomplete'
    if not v['completed']:
        record['failure_reason'] = ('verifier timeout' if v['timed_out'] else
                                    'killed_unknown' if v['signal'] else 'verifier rc/JSON failure')


def measure(args, h, scratch, source, job, output, extime, rep, attempt):
    free = shutil.disk_usage(scratch).free
    job.setdefault('scratch_checks', []).append(dict(rep_id=rep, extime=extime, free_bytes=free, utc=now()))
    if free < 25 * 1024**3 * extime / 3:
        raise RuntimeError('insufficient scratch space')
    h['tenant']._assert_single_tenant()
    output.mkdir(parents=True)
    r = new_result(args.command, args.candidate, args.workload, extime, getattr(args, 'job_index', 0), rep, attempt)
    r.update(ruling_sha256=job['ruling_sha256'], bindings=copy.deepcopy(job['bindings']), scratch_free_bytes=free)
    trace = scratch / ('trace-' + uuid4().hex)
    (trace / 'log').mkdir(parents=True)
    try:
        b = r['bench']
        b.update(argv=bench_argv(job['bindings']['binary'], args.workload, extime), cwd=str(trace),
                 stdout_path=str(output / 'bench.stdout'), stderr_path=str(output / 'bench.stderr'))
        r['execution_status'] = 'bench_running'
        write_json(output / 'result.json', r)
        with stage(job, 'bench'):
            b.update(timed_process(b['argv'], trace, 120, Path(b['stdout_path']), Path(b['stderr_path']),
                                   env=dict(os.environ, IZANAGI_TRACE_DIR=str(trace))))
        r['seed_identity'].update(pid=b['pid'], started_epoch=b['started_epoch'])
        b['completed'] = b['rc'] == 0 and not b['timed_out']
        raw = Path(b['stdout_path']).read_text(errors='replace')
        b['commit_witness'], b['batch_commit_witness'] = h['pipeline']._parse_commit_witness(raw)
        b['abort_counts'] = h['pipeline']._parse_abort_counts(raw)
        r['execution_status'] = 'bench_completed' if b['completed'] else 'bench_failed'
        write_json(output / 'result.json', r)
        with stage(job, 'count'):
            start = time.monotonic()
            r['count'] = dict(c_lines=count_c_lines(trace), wall_s=time.monotonic() - start)
        with stage(job, 'preserve'):
            r['preservation'] = preserve(trace, output)
        r['verifier_default_workers'] = h['parse']._effective_worker_count(len(list(trace.glob('trace_*.log'))), None)
        r['execution_status'] = 'preserved'
        write_json(output / 'result.json', r)
        if not b['completed']:
            r.update(execution_status='bench_failed', operational_outcome='bench_failed', failure_reason='bench timeout/rc failure')
        elif b['commit_witness'] is None:
            r.update(execution_status='witness_missing', operational_outcome='indeterminate', failure_reason='commit witness unavailable')
        else:
            run_verifier(args, h, r, trace, source, output, job, 3600 if args.command == 'calibrate' else 1800)
    except Exception as exc:
        r['failure_reason'] = f'{type(exc).__name__}: {exc}'
        if r['execution_status'] != 'not_run':
            r.update(execution_status='execution_failed', operational_outcome='indeterminate')
        raise
    finally:
        r['finished_at'] = now()
        r['eligible'] = eligible(r)
        r['stop_reason'] = stop_reason(r) if args.command == 'calibrate' else None
        r['T_s'] = (sum([r['bench']['wall_s'], r['count']['wall_s'], r['verify']['wall_s']])
                    if all(x is not None for x in (r['bench']['wall_s'], r['count']['wall_s'], r['verify']['wall_s'])) else None)
        r['A_s'] = r['preservation']['wall_s']
        write_json(output / 'result.json', r)
        if r['preservation']['complete']:
            with stage(job, 'cleanup'):
                shutil.rmtree(trace)
    return r


def read_json(path):
    return json.loads(path.read_text())


def check_binding(record, args):
    expected = dict(schema_version=SCHEMA, candidate=args.candidate, workload=args.workload,
                    extime=args.extime, job_index=args.job_index, ruling_sha256=sha(args.ruling))
    for key, value in expected.items():
        if record.get(key) != value:
            raise ValueError(f'resume binding mismatch: {key}')


def reserve_output(args):
    if args.command == 'reverify':
        original = read_json(args.rep_dir / 'result.json')
        if (original['phase'] != 'verify' or original['verify_attempt_id'] != 1
                or original['verify']['completed']
                or (original['verify']['rc'] is None and original['verify']['t_popen_monotonic'] is None)
                or original['operational_outcome'] != 'indeterminate'
                or not original['bench']['completed'] or not original['preservation']['complete']):
            raise ValueError('only operationally incomplete stage-B verifier can be retried')
        if original['ruling_sha256'] != sha(args.ruling):
            raise ValueError('ruling sha mismatch')
        if not identity_matches(original['candidate'], original['bindings']):
            raise ValueError('original identity mismatch')
        if list(args.rep_dir.glob('reverify-*')):
            raise ValueError('one verifier retry already reserved; no further retries')
        args.candidate, args.workload = original['candidate'], original['workload']
        args.extime, args.job_index = original['extime'], original['job_index']
        args.output_dir = args.rep_dir / 'reverify-2'
        args.output_dir.mkdir()
        return original
    if args.command == 'calibrate':
        args.output_dir.mkdir(parents=True)
    else:
        if args.rep_start != 1 + 4 * (args.job_index - 1):
            raise ValueError('job-index/rep-start mismatch')
        if args.output_dir.exists() and not args.resume:
            raise ValueError('existing output requires --resume; refusing duplicate reps')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        # Validate everything before skipping or launching any rep.
        for path in sorted(args.output_dir.glob('rep-*')):
            rep = int(path.name.removeprefix('rep-'))
            if rep not in range(args.rep_start, args.rep_start + args.reps):
                raise ValueError('existing rep outside job range')
            records = sorted(path.glob('attempt-*/result.json'))
            if not records:
                raise ValueError('existing unrecorded rep needs manual recovery; not overwritten')
            for record_path in records:
                r = read_json(record_path)
                check_binding(r, args)
                if r['rep_id'] != rep:
                    raise ValueError('rep path/identity mismatch')
            # Recovery decisions are made under the invocation lock in run_job.
    return None


def run_job(args):
    start = time.monotonic()
    original = reserve_output(args)
    output = args.output_dir
    lock = (output / '.runner.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise RuntimeError('another invocation owns this output directory')
    job_id = uuid4().hex
    job = dict(schema_version=SCHEMA, job_id=job_id, phase=args.command,
               candidate=args.candidate, workload=args.workload, extime=getattr(args, 'extime', None),
               job_index=getattr(args, 'job_index', 0), hostname=socket.gethostname(),
               started_at=now(), finished_at=None, t_start_monotonic=start,
               runner_sha256=sha(__file__), ruling_sha256=sha(args.ruling),
               stage_wall_s={k: 0.0 for k in STAGES}, bindings={}, F_s=None,
               execution_status='running', failure_reason=None, skipped_reps=[])
    # Invocation ledger is never replaced on --resume; job.json is the latest view.
    ledger = output / ('job-' + job_id + '.json')
    write_json(ledger, job)
    scratch = None
    h = None
    stack = ExitStack()
    rows, result_paths = [], []
    success = False
    try:
        with stage(job, 'setup'):
            h = helpers(args.repo_root)
            site = h['site'].current_site(require_evidence=True)
            job['site'] = site
            if h['site'].refuses_heavy_work(site) or not h['site'].is_pegasus_compute(site):
                raise RuntimeError('requires a Pegasus compute node: ' + site)
            if not args.scratch_root.is_relative_to(Path('/scr')):
                raise ValueError('--scratch-root must be under /scr')
            scratch = Path(tempfile.mkdtemp(prefix='verify-phase-', dir=args.scratch_root))
            os.environ['TMPDIR'] = str(scratch)
            os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
            tempfile.tempdir = str(scratch)
            # Helpers use sys.executable internally; bind it to the same real interpreter.
            sys.executable = os.path.realpath(sys.executable)
            job['scratch'] = str(scratch)
        source = prepare(args, h, scratch, job, stack, do_build=args.command != 'reverify')
        write_json(ledger, job)
        if args.command == 'reverify':
            r = copy.deepcopy(original)
            r.update(phase='reverify', verify_attempt_id=2, started_at=now(), finished_at=None,
                     hostname=socket.gethostname(), runner_sha256=sha(__file__),
                     original_result=str(args.rep_dir / 'result.json'),
                     original_result_sha256=sha(args.rep_dir / 'result.json'),
                     original_bindings=original['bindings'], bindings=copy.deepcopy(job['bindings']),
                     execution_status='restoring', operational_outcome='not_run', failure_reason=None)
            r['verify'] = new_result('reverify', args.candidate, args.workload, args.extime)['verify']
            # Build/binary provenance remains the provenance of the original bench.
            for key in ('binary', 'binary_sha256', 'configure_argv', 'build_configure_argv', 'warmup_configure_argv'):
                r['bindings'][key] = original['bindings'].get(key)
            path = output / 'result.json'
            result_paths.append(path)
            write_json(path, r)
            trace = scratch / 'restored'
            free = shutil.disk_usage(scratch).free
            job['scratch_checks'] = [dict(free_bytes=free, extime=args.extime, utc=now())]
            if free < 25 * 1024**3 * args.extime / 3:
                raise RuntimeError('insufficient scratch space for reverify')
            with stage(job, 'preserve'):
                restore(original['preservation'], args.rep_dir, trace)
            try:
                run_verifier(args, h, r, trace, source, output, job, 3600)
            except Exception as exc:
                r['failure_reason'] = str(exc)
                raise
            finally:
                r['finished_at'] = now()
                write_json(path, r)
            success = r['verify']['completed']
        elif args.command == 'calibrate':
            reason = None
            for e in args.extimes:
                dest = output / f'extime-{e}'
                if reason:
                    dest.mkdir()
                    r = new_result('calibrate', args.candidate, args.workload, e)
                    r.update(stop_reason=reason, failure_reason=reason, ruling_sha256=job['ruling_sha256'],
                             bindings=copy.deepcopy(job['bindings']), eligible=False, T_s=None, A_s=None)
                    write_json(dest / 'result.json', r)
                else:
                    r = measure(args, h, scratch, source, job, dest, e, 0, 1)
                    reason = stop_reason(r)
                rows.append(r)
                result_paths.append(dest / 'result.json')
                cal = calibration_summary(rows, h['calibration'].choose_extime)
                cal.update(schema_version=SCHEMA, candidate=args.candidate, workload=args.workload,
                           ruling_sha256=job['ruling_sha256'], F_s=job['F_s'])
                write_json(output / 'calib.json', cal)
            success = all(r['execution_status'] in ('completed', 'not_run') for r in rows)
        else:
            for rep in range(args.rep_start, args.rep_start + args.reps):
                rep_dir = output / f'rep-{rep}'
                attempt = 1
                if rep_dir.exists():
                    prior_paths = sorted(rep_dir.glob('attempt-*/result.json'))
                    previous = read_json(prior_paths[-1])
                    preserved_flag = prior_paths[-1].parent / 'preservation.json'
                    if not previous['preservation']['complete'] and preserved_flag.exists():
                        previous['preservation'] = read_json(preserved_flag)
                        write_json(prior_paths[-1], previous)
                    if not previous['preservation']['complete']:
                        # §4.3: unpreserved walltime-interrupted rep is unstarted.
                        # Keep all interrupted evidence; reuse its logical attempt id.
                        if previous['execution_status'] not in ('bench_running', 'bench_completed', 'preserved', 'not_run'):
                            raise ValueError('failed preservation needs repair before resume')
                        attempt = previous['bench_attempt_id']
                        prior_paths[-1].parent.rename(rep_dir / ('interrupted-' + uuid4().hex))
                    elif previous['execution_status'] == 'bench_failed' and previous['bench_attempt_id'] == 1:
                        attempt = 2
                    elif previous['bench']['completed'] and previous['verify']['rc'] is None:
                        # Preserved trace whose first verifier never started (e.g. tenant refusal).
                        # A started/killed verifier is an operational retry, not this path.
                        if previous['verify']['t_popen_monotonic'] is not None:
                            raise ValueError('started verifier needs reverify, not bench resume')
                        dest = prior_paths[-1].parent
                        if (dest / 'verifier.json').exists() or (dest / 'verifier.stderr').exists():
                            raise ValueError('verifier launch evidence requires operational recovery')
                        free = shutil.disk_usage(scratch).free
                        job.setdefault('scratch_checks', []).append(dict(rep_id=rep, extime=args.extime, free_bytes=free, utc=now()))
                        if free < 25 * 1024**3 * args.extime / 3:
                            raise RuntimeError('insufficient scratch space for preserved rep')
                        trace = scratch / ('resume-' + uuid4().hex)
                        with stage(job, 'preserve'):
                            restore(previous['preservation'], dest, trace)
                        result_paths.append(prior_paths[-1])
                        try:
                            run_verifier(args, h, previous, trace, source, dest, job, 1800)
                        finally:
                            previous['finished_at'] = now()
                            write_json(prior_paths[-1], previous)
                        with stage(job, 'cleanup'):
                            shutil.rmtree(trace)
                        rows.append(previous)
                        continue
                    else:
                        job['skipped_reps'].append(rep)
                        continue
                for a in range(attempt, 3):
                    dest = rep_dir / f'attempt-{a}'
                    r = measure(args, h, scratch, source, job, dest, args.extime, rep, a)
                    rows.append(r)
                    result_paths.append(dest / 'result.json')
                    if r['execution_status'] != 'bench_failed':
                        break
            final_records = [read_json(sorted(p.glob('attempt-*/result.json'))[-1])
                             for p in output.glob('rep-*')]
            success = len(final_records) == args.reps and all(r['execution_status'] == 'completed' for r in final_records)
            if any(r['execution_status'] == 'bench_failed' and r['bench_attempt_id'] == 2 for r in rows):
                success = False
        job['execution_status'] = 'completed' if success else 'incomplete'
    except Exception as exc:
        job.update(execution_status='identity-mismatch' if isinstance(exc, IdentityMismatch) else 'failed',
                   failure_reason=f'{type(exc).__name__}: {exc}')
        success = False
    finally:
        with stage(job, 'cleanup'):
            try:
                stack.close()  # source survives all verifier processes
            except Exception as exc:
                job['cleanup_error'] = str(exc)
                success = False
            if scratch is not None:
                try:
                    shutil.rmtree(scratch)
                except OSError as exc:
                    job['cleanup_error'] = str(exc)
                    success = False
        job.update(finished_at=now(), t_end_monotonic=time.monotonic())
        if job.get('cleanup_error'):
            job['execution_status'] = 'failed'
        job['job_wall_s'] = job['t_end_monotonic'] - start
        job['F_s'] = sum(job['stage_wall_s'][k] for k in ('setup', 'hydrate', 'build'))
        write_json(ledger, job)
        write_json(output / 'job.json', job)
        # Include records flushed before an exception as well as normally returned records.
        paths = set(result_paths) | {p for p in output.rglob('result.json')
                                    if read_json(p).get('job_accounting') == {}}
        for path in paths:
            r = read_json(path)
            r['job_accounting'] = dict(job_id=job_id, job_json=str(ledger),
                                       job_wall_s=job['job_wall_s'], stage_wall_s=job['stage_wall_s'])
            write_json(path, r)
        if args.command == 'calibrate':
            # Setup failure also gives explicit not_run rows for every planned extime.
            for e in args.extimes:
                path = output / f'extime-{e}/result.json'
                if not path.exists():
                    path.parent.mkdir(exist_ok=True)
                    r = new_result('calibrate', args.candidate, args.workload, e)
                    r.update(ruling_sha256=job['ruling_sha256'], bindings=job['bindings'],
                             stop_reason=job['failure_reason'], failure_reason=job['failure_reason'],
                             job_accounting=dict(job_id=job_id, job_json=str(ledger), job_wall_s=job['job_wall_s'],
                                                 stage_wall_s=job['stage_wall_s']),
                             execution_status=job['execution_status'] if job['execution_status'] == 'identity-mismatch' else 'not_run')
                    write_json(path, r)
            final_rows = [read_json(output / f'extime-{e}/result.json') for e in args.extimes]
            cal = (calibration_summary(final_rows, h['calibration'].choose_extime) if h else
                   dict(rows=final_rows, eligible_set=[], chosen_max_eligible=None,
                        chooser_prefix=[], anomaly_seen=False, indeterminate_count=0))
            cal.update(schema_version=SCHEMA, candidate=args.candidate, workload=args.workload,
                       ruling_sha256=job['ruling_sha256'], F_s=job['F_s'], job_wall_s=job['job_wall_s'])
            write_json(output / 'calib.json', cal)
        lock.close()
    print(f'{args.command}: {job["execution_status"]} output={output}')
    return 0 if success else 1


def decide(candidate, calibration, slots, structural_errors=(), accepted_ruling_sha=()):
    reasons = list(structural_errors)
    expected = {(w, i) for w in WORKLOADS for i in range(1, 9)}
    keys = [(r['workload'], r['rep_id']) for r in slots]
    if len(keys) != len(set(keys)):
        reasons.append('duplicate rep')
    if set(keys) != expected:
        reasons.append('missing/out-of-range rep')
    if any(r['candidate'] != candidate for r in calibration + slots):
        reasons.append('candidate mismatch')
    digests = {r['ruling_sha256'] for r in calibration + slots}
    if (not digests <= set(accepted_ruling_sha) if accepted_ruling_sha else len(digests) > 1):
        reasons.append('ruling sha mismatch')
    if len({r['extime'] for r in slots}) > 1:
        reasons.append('stage-B extime mismatch')
    if any(not identity_matches(candidate, r['bindings']) for r in slots):
        reasons.append('stage-B identity mismatch')
    judged = [r for r in calibration + slots if r['verify']['completed']]
    anomalies = [r for r in judged if anomaly(r)]
    # Explicit identity/duplicate mixing makes the aggregate unusable, even if red.
    # No stage B is expected after a calibration anomaly. Partial stage-B tables,
    # however, are missing-slot aggregates and must remain undetermined.
    mixing = [s for s in reasons if s != 'missing/out-of-range rep' or slots]
    if mixing:
        decision = 'undetermined'
    elif anomalies:
        decision = 'disqualified'
        reasons.append('anomaly in judgment set')
    elif not reasons and len(slots) == 24 and all(green(r) for r in slots):
        decision = 'pass'
    else:
        decision = 'undetermined'
        reasons.append('not all 24 slots satisfy pass conditions')
    return dict(decision=decision, reasons=reasons, judgment_set_count=len(judged),
                anomaly_verdict_count=len(anomalies))


def effective_attempt(rep_dir, errors):
    paths = sorted(rep_dir.glob('attempt-*/result.json'))
    records = [read_json(p) for p in paths]
    if not records:
        errors.append('missing attempt record: ' + str(rep_dir))
        return None, []
    if [r['bench_attempt_id'] for r in records] not in ([1], [1, 2]):
        errors.append('invalid bench attempt sequence: ' + str(rep_dir))
    if len(records) > 1 and records[0]['execution_status'] != 'bench_failed':
        errors.append('unauthorized bench retry: ' + str(rep_dir))
    current = records[-1]
    for old in records:
        if any(old[k] != current[k] for k in ('candidate', 'workload', 'extime', 'rep_id', 'job_index', 'ruling_sha256')):
            errors.append('bench-attempt identity mixing: ' + str(rep_dir))
    for path, r in zip(paths, records):
        r['_path'] = str(path)
        if path.parent.name != f'attempt-{r["bench_attempt_id"]}' or rep_dir.name != f'rep-{r["rep_id"]}':
            errors.append('attempt/rep path mismatch: ' + str(path))
        retries = sorted(path.parent.glob('reverify-*/result.json'))
        if len(retries) > 1:
            errors.append('multiple verifier retries: ' + str(path))
        for retry_path in retries:
            retry = read_json(retry_path)
            retry['_path'] = str(retry_path)
            if (r['verify']['completed'] or r['operational_outcome'] != 'indeterminate'
                    or retry['verify_attempt_id'] != 2 or not r['bench']['completed']
                    or not r['preservation']['complete']):
                errors.append('unauthorized verifier retry: ' + str(retry_path))
            for key in ('candidate', 'workload', 'extime', 'rep_id', 'bench_attempt_id', 'ruling_sha256'):
                if retry[key] != r[key]:
                    errors.append('reverify binding mismatch: ' + key)
            if (retry.get('original_result_sha256') != sha(path)
                    or retry['preservation'] != r['preservation'] or retry['bench'] != r['bench']):
                errors.append('reverify original trace binding mismatch')
            if r is records[-1]:
                current = retry
    return current, records


def round_seconds(value):
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, dict):
        return {k: round_seconds(v) for k, v in value.items()}
    if isinstance(value, list):
        return [round_seconds(v) for v in value]
    return value


def summarize(args):
    accepted = sorted(set(getattr(args, 'accept_ruling_sha', None) or []))
    policy = 'accepted-set' if accepted else 'single'
    calibrations = [read_json(p) for p in sorted(args.input.glob('calib/*/calib.json'))]
    jobs = [read_json(p) for p in sorted(args.input.rglob('job-*.json'))]
    fixed = max((j['F_s'] for j in jobs if j['phase'] == 'calibrate' and j['F_s'] is not None), default=None)
    result = dict(schema_version=SCHEMA, generated_at=now(), F_hat_s=fixed, candidates={},
                  ruling_sha_accepted=accepted, ruling_sha_policy=policy,
                  ruling_sha_by_phase={'calibrate': {}, 'verify': {}})
    for c in CANDIDATES:
        errors, rows, slots, all_attempts = [], [], [], []
        sha_retries = []
        cals = [x for x in calibrations if x['candidate'] == c]
        for cal in cals:
            rows.extend(cal['rows'])
        if len(cals) != 3 or {x['workload'] for x in cals} != set(WORKLOADS):
            errors.append('missing/duplicate workload calibration')
        if any(r['candidate'] != c or r['workload'] != cal['workload'] or r['ruling_sha256'] != cal['ruling_sha256']
               for cal in cals for r in cal['rows']):
            errors.append('calibration identity mixing')
        for cal in cals:
            if [r['extime'] for r in cal['rows']] != list(EXTIMES):
                errors.append('missing/duplicate calibration extime')
            stopped = False
            for r in cal['rows']:
                if stopped and r['bench']['completed']:
                    errors.append('calibration executed after stop')
                if r['bench']['completed'] and not identity_matches(c, r['bindings']):
                    errors.append('calibration source identity mismatch')
                stopped = stopped or stop_reason(r) is not None
        sets = {w: sorted({r['extime'] for r in rows if r['workload'] == w and eligible(r)}) for w in WORKLOADS}
        intersection = sorted(set.intersection(*(set(es) for es in sets.values())))
        estimates = {str(e): budget_estimate(rows, e, fixed) if fixed is not None else None for e in EXTIMES}
        chosen, history = None, []
        for e in reversed(intersection):
            cost = estimates[str(e)]
            history.append(dict(extime=e, estimate=cost))
            if cost is not None and cost['total_s'] <= 14400:
                chosen = e
                break
        for job_dir in sorted(args.input.glob('verify/*')):
            for rep_dir in sorted(job_dir.glob('rep-*')):
                paths = sorted(rep_dir.glob('attempt-*/result.json'))
                if not paths:
                    continue
                first = read_json(paths[0])
                if first['candidate'] != c:
                    continue
                r, attempts = effective_attempt(rep_dir, errors)
                all_attempts.extend(attempts)
                for attempt in attempts:
                    for path in sorted(Path(attempt['_path']).parent.glob('reverify-*/result.json')):
                        retry = read_json(path)
                        retry['_path'] = str(path)
                        sha_retries.append(retry)
                if r:
                    slots.append(r)
                    if r['extime'] != chosen:
                        errors.append('stage-B extime differs from budgeted calibration choice')
                    if r['job_index'] != (1 if r['rep_id'] <= 4 else 2):
                        errors.append('job-index/rep-id mismatch')
        for r in rows + slots + all_attempts:
            digest = r.get('ruling_sha256')
            if (r.get('schema_version') != SCHEMA or not isinstance(digest, str) or len(digest) != 64
                    or any(ch not in '0123456789abcdef' for ch in digest)):
                errors.append('invalid schema/ruling identity')
        candidate_jobs = [j for j in jobs if j['candidate'] == c]
        if len({j['job_id'] for j in candidate_jobs}) != len(candidate_jobs):
            errors.append('duplicate accounting job identity')
        if any(j.get('job_wall_s') is None for j in candidate_jobs):
            errors.append('incomplete job accounting; reconcile dispatch receipt')
        known_jobs = {j['job_id'] for j in candidate_jobs}
        if any(r.get('job_accounting', {}).get('job_id') not in known_jobs for r in slots):
            errors.append('missing stage-B accounting job')
        if chosen is None and not any(anomaly(r) for r in rows):
            errors.append('no eligible extime within budget')
        # Count each record once, including retries not selected as effective
        # slots. Reverify records belong to the stage-B (verify) phase here.
        sha_records = list({r.get('_path', id(r)): r
                            for r in rows + all_attempts + sha_retries + slots}.values())
        by_phase = {'calibrate': {}, 'verify': {}}
        for r in sha_records:
            phase = 'calibrate' if r['phase'] == 'calibrate' else 'verify'
            digest = r.get('ruling_sha256')
            counts = by_phase[phase]
            counts[digest] = counts.get(digest, 0) + 1
        if accepted and any(r.get('ruling_sha256') not in accepted for r in sha_records):
            if not any(r.get('ruling_sha256') not in accepted for r in rows + slots):
                errors.append('ruling sha mismatch')
        decision = decide(c, rows, slots, errors, accepted_ruling_sha=accepted)
        for phase, counts in by_phase.items():
            total = result['ruling_sha_by_phase'][phase]
            for digest, count in counts.items():
                total[digest] = total.get(digest, 0) + count
        unfinished = [dict(phase=r['phase'], workload=r['workload'], extime=r['extime'],
                           rep_id=r['rep_id'], operational_outcome=r['operational_outcome'],
                           preserved=r['preservation']['complete'], destination=r['preservation']['destination'],
                           result=r.get('_path')) for r in rows + all_attempts
                      if is_indeterminate(r)]
        # Include retry failures separately without erasing original failures.
        unfinished += [dict(phase=r['phase'], rep_id=r['rep_id'], workload=r['workload'],
                            destination=r['preservation']['destination'], result=r.get('_path'))
                       for r in slots if r['phase'] == 'reverify' and is_indeterminate(r)]
        consumed = {phase: sum(j.get('job_wall_s') or 0 for j in jobs if j['candidate'] == c and
                              (j['phase'] == 'calibrate' if phase == 'A' else j['phase'] in ('verify', 'reverify')))
                    for phase in ('A', 'B')}
        table = []
        for w in WORKLOADS:
            for rep in range(1, 9):
                found = [r for r in slots if (r['workload'], r['rep_id']) == (w, rep)]
                r = found[0] if len(found) == 1 else None
                table.append(dict(workload=w, rep_id=rep,
                                  **{k: r['verify'][k] if r else None for k in ('verdict', 'certified', 'anomaly_count')},
                                  operational_outcome=r['operational_outcome'] if r else 'missing-or-duplicate',
                                  bench_attempt=r['bench_attempt_id'] if r else None,
                                  verify_attempt=r['verify_attempt_id'] if r else None,
                                  result=r.get('_path') if r else None))
        result['candidates'][c] = dict(**decision, ruling_sha_accepted=accepted,
            ruling_sha_policy=policy, ruling_sha_by_phase=by_phase, calibration_table=[dict(
            candidate=c, workload=r['workload'], extime=r['extime'], eligible=eligible(r),
            verifier_wall_s=r['verify']['wall_s'], verdict=r['verify']['verdict'], stop_reason=r['stop_reason']) for r in rows],
            eligible_sets=sets, intersection=intersection, initial_extime=max(intersection, default=None),
            chosen_extime=chosen, budget_estimates=estimates, stepdown_history=history,
            stage_B_allowed=chosen is not None and not any(anomaly(r) for r in rows) and not errors,
            slots=table, indeterminate_count=len(unfinished), indeterminate=unfinished,
            operational_indeterminate_count=sum(r['operational_outcome'] == 'indeterminate' for r in rows + all_attempts),
            cli_indeterminate_count=sum(r['operational_outcome'] == 'cli-indeterminate' for r in rows + all_attempts),
            not_run_count=sum(r['execution_status'] == 'not_run' for r in rows),
            consumed_job_wall_s=consumed, total_job_wall_s=sum(consumed.values()),
            budget_constraint_satisfied=consumed['B'] <= 14400,
            accounting_basis='runner monotonic job wall; dispatch Elapse requires parent reconciliation')
    result = round_seconds(result)
    write_json(args.output, result)
    if args.markdown:
        args.markdown.write_text(render_markdown(result))
    print('summarize: ' + ', '.join(f'{c}={r["decision"]}' for c, r in result['candidates'].items()))
    return 0


def render_markdown(result):
    # Flatten every field so the human-readable report cannot omit accounting or failures.
    def leaves(value, prefix=''):
        if prefix.rsplit('.', 1)[-1] in ('ruling_sha_accepted', 'ruling_sha_by_phase', 'ruling_sha_policy'):
            yield '| ' + prefix + ' | ' + json.dumps(value, ensure_ascii=False) + ' |'
        elif isinstance(value, dict):
            for k, v in value.items():
                yield from leaves(v, prefix + '.' + k if prefix else k)
        elif isinstance(value, list) and value:
            for i, v in enumerate(value):
                yield from leaves(v, f'{prefix}[{i}]')
        else:
            text = f'{value:.3f}' if isinstance(value, float) else json.dumps(value, ensure_ascii=False)
            yield '| ' + prefix + ' | ' + text.replace('|', '&#124;').replace('\n', '<br>') + ' |'
    return '## 検証相集計\n\n| field | value |\n|---|---|\n' + '\n'.join(leaves(result)) + '\n'


def selftest():
    h = helpers(Path.cwd())
    checks = []

    def check(name, value):
        checks.append(bool(value))
        print(('ok ' if value else 'FAIL ') + name)

    def rejects(fn):
        try:
            fn()
        except (ValueError, RuntimeError):
            return True
        return False

    def good(w='write-heavy', rep=1, e=3, phase='verify'):
        r = new_result(phase, 'fixed-5', w, e, 1 if rep <= 4 else 2, rep)
        r['ruling_sha256'] = 'a' * 64
        ev = {k: CANDIDATES['fixed-5']['expected'] for k in ('src_token', 'source_bytes_sha256')}
        r['bindings'] = dict(source_before=ev.copy(), source_after=ev.copy())
        r['bench'].update(completed=True, wall_s=3.0, rc=0, commit_witness=7)
        r['count'].update(wall_s=2.0, c_lines=7)
        r['verify'].update(completed=True, parse_ok=True, rc=0, wall_s=100.0,
                           verdict='serializable', certified=True, anomaly_count=0)
        r['preservation'].update(complete=True, wall_s=4.0)
        r.update(execution_status='completed', operational_outcome='completed')
        return r

    r = good()
    r['verify']['wall_s'] = 600.0
    check('eligible boundary 600.0', eligible(r))
    r['verify']['wall_s'] = 600.001
    check('ineligible above 600', not eligible(r))
    r = good()
    r['verify']['completed'] = False
    check('incomplete ineligible', not eligible(r))
    r = good()
    r['verify'].update(rc=1, verdict='non-serializable', anomaly_count=1)
    check('anomaly ineligible', not eligible(r) and anomaly(r))
    check('anomaly under 600 does not add a calibration stop rule', stop_reason(r) is None)
    rows = [good(e=e, phase='calibrate') for e in EXTIMES]
    rows[1]['verify'].update(completed=False, wall_s=3600, timed_out=True)
    rows[1]['operational_outcome'] = 'indeterminate'
    calls = []

    def spy(prefix, limit):
        calls.append(prefix)
        return h['calibration'].choose_extime(prefix, limit)

    chosen = calibration_summary(rows, spy)
    check('chooser receives only completed prefix', calls == [[dict(extime=3, verifier_walltime_s=100.0)]]
          and chosen['chosen_max_eligible'] == 3)
    check('empty prefix null', calibration_summary([rows[1]], spy)['chosen_max_eligible'] is None)
    slots = [good(w, rep) for w in WORKLOADS for rep in range(1, 9)]
    check('24 green pass', decide('fixed-5', [], slots)['decision'] == 'pass')
    check('calibration anomaly disqualifies', decide('fixed-5', [r], slots)['decision'] == 'disqualified')
    check('calibration anomaly with no B disqualifies', decide('fixed-5', [r], [])['decision'] == 'disqualified')
    bad = copy.deepcopy(slots)
    bad[0]['verify']['completed'] = False
    bad[0]['operational_outcome'] = 'indeterminate'
    check('one incomplete slot undetermined', decide('fixed-5', [], bad)['decision'] == 'undetermined')
    check('duplicate rep undetermined', decide('fixed-5', [], slots + [slots[0]])['decision'] == 'undetermined')
    check('missing rep undetermined', decide('fixed-5', [], slots[:-1])['decision'] == 'undetermined')
    check('partial B with anomaly is incomplete aggregate', decide('fixed-5', [r], slots[:-1])['decision'] == 'undetermined')
    check('calibration indeterminate permits pass with disclosure',
          decide('fixed-5', [rows[1]], slots)['decision'] == 'pass' and is_indeterminate(rows[1]))
    bad = copy.deepcopy(slots)
    bad[0]['preservation']['complete'] = False
    check('unpreserved cannot pass', decide('fixed-5', [], bad)['decision'] == 'undetermined')
    bad = copy.deepcopy(slots)
    bad[0]['bindings']['source_before']['src_token'] = 'stock'
    check('identity mismatch cannot pass', decide('fixed-5', [], bad)['decision'] == 'undetermined')
    bad = copy.deepcopy(slots)
    bad[0]['verify'].update(certified=False, verdict='indeterminate', rc=3)
    check('CLI indeterminate cannot pass', decide('fixed-5', [], bad)['decision'] == 'undetermined')
    bad = copy.deepcopy(slots)
    bad[0]['ruling_sha256'] = 'b' * 64
    check('ruling mixing cannot pass', decide('fixed-5', [], bad)['decision'] == 'undetermined')
    check('bench argv', bench_argv('/bin', 'balanced', 6) == [
        '/bin', '-ycsb_tuple_num=1000000', '-thread_num=48', '-ycsb_zipf_skew=0.9',
        '-ycsb_rratio=50', '-ycsb_rmw=0', '-ycsb_max_ope=10', '-extime=6', '-clocks_per_us=2100'])
    check('verifier argv', verifier_argv('/trace', 7, '/source') == [
        os.path.realpath(sys.executable), '-B', '-m', 'orchestrator.verifier', '/trace', '--json',
        '--expected-commits', '7', '--protocol', 'silo', '--ccbench-root', '/source'])
    check('missing witness rejected', rejects(lambda: verifier_argv('/trace', None, '/source')))
    for c in CANDIDATES:
        configured = configure_argv('/source', '/build', dict(gflags_expected_head='gf', glog_expected_head='gl'),
                                    dict(cc_path='/gcc', cxx_path='/g++'),
                                    {k: '/' + k for k in ('gflags', 'glog', 'masstree', 'mimalloc', 'googletest')}, c)
        check('configure defines ' + c, len(defines(c)) == 7 and all(d in configured for d in defines(c))
              and f'-DCCBENCH_BACKOFF_FIXED={CANDIDATES[c]["BACKOFF_FIXED"]}' in configured)
    check('schema required keys', set(REQUIRED) <= good().keys()
          and set(TIMING_KEYS) <= good()['verify'].keys())
    with tempfile.TemporaryDirectory(prefix='verify-phase-selftest-', dir='/tmp') as tmp:
        td = Path(tmp)
        path = td / 'trace_0.log'
        path.write_text('C 1\nR 1\n')
        check('inventory and C counting', file_inventory(td)[0]['lines'] == 2 and count_c_lines(td) == 1)
        validate_file(path, sha(path), path.stat().st_size)
        check('manifest mismatch rejected', rejects(lambda: validate_file(path, '0' * 64, path.stat().st_size)))
        document = good()
        write_json(td / 'record.json', document)
        check('schema JSON roundtrip', read_json(td / 'record.json') == document)
    rows = [good(e=e, phase='calibrate') for e in EXTIMES]
    rows[1]['verify']['wall_s'] = 601.0
    check('stop above 600', stop_reason(rows[1]) == 'verifier wall > 600 s')
    check('over-limit prefix excludes later row', len(calibration_prefix(rows)) == 2)
    rows[0]['verify']['wall_s'] = 601.0
    check('no rounding up to 3', calibration_summary(rows[:1], spy)['chosen_max_eligible'] is None)
    costs = budget_estimate([good(w, phase='calibrate') for w in WORKLOADS], 3, 10)
    check('budget formula', costs == dict(T_s=2520.0, A_s=96.0, F_s=60, total_s=2676.0))
    payload = dict(runs=1, results=[dict(verdict='serializable', certified=True,
                                       anomaly_count=27, anomalies=[], integrity={'clean': True})])
    projected = project_verifier(0, json.dumps(payload))
    check('copy anomaly_count not list length', projected['anomaly_count'] == 27)
    for rc in (2, -9, 42):
        v = project_verifier(rc, json.dumps(payload))
        check(f'operational rc {rc} null verdict', v['verdict'] is None and not v['completed'])
    check('broken JSON null verdict', project_verifier(0, '{')['verdict'] is None)
    check('timeout null verdict', project_verifier(0, json.dumps(payload), True)['verdict'] is None)
    # Exercise the actual file collector, budget selection and retry binding, still
    # using only small synthetic JSON in /tmp (no bench/verifier/preservation calls).
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory(prefix='verify-summary-selftest-', dir='/tmp') as tmp:
        root = Path(tmp)
        for w in WORKLOADS:
            dest = root / 'calib' / ('fixed-5-' + w)
            dest.mkdir(parents=True)
            cs = [good(w, 0, 3, 'calibrate'), good(w, 0, 6, 'calibrate')]
            cs[1]['verify'].update(completed=False, rc=-9, timed_out=True, verdict=None,
                                   certified=None, anomaly_count=None, wall_s=3600.0)
            cs[1]['operational_outcome'] = 'indeterminate'
            cs[1]['stop_reason'] = 'verifier incomplete'
            skipped = new_result('calibrate', 'fixed-5', w, 10)
            skipped.update(ruling_sha256='a' * 64, stop_reason='verifier incomplete')
            cs.append(skipped)
            cal = calibration_summary(cs, h['calibration'].choose_extime)
            cal.update(candidate='fixed-5', workload=w, ruling_sha256='a' * 64)
            write_json(dest / 'calib.json', cal)
            write_json(dest / 'job-cal.json', dict(job_id=w, phase='calibrate', candidate='fixed-5', F_s=10.0, job_wall_s=50.0))
            for index in (1, 2):
                jobdir = root / 'verify' / f'fixed-5-{w}-{index}'
                jobdir.mkdir(parents=True)
                jid = f'{w}-{index}'
                write_json(jobdir / ('job-' + jid + '.json'), dict(
                    job_id=jid, phase='verify', candidate='fixed-5', F_s=10.0, job_wall_s=200.0))
                for rep in range(1 + 4 * (index - 1), 5 + 4 * (index - 1)):
                    dest = jobdir / f'rep-{rep}' / 'attempt-1'
                    dest.mkdir(parents=True)
                    sr = good(w, rep)
                    sr['job_accounting'] = dict(job_id=jid)
                    write_json(dest / 'result.json', sr)
        options = SimpleNamespace(input=root, output=root / 'summary.json', markdown=None)
        summarize(options)
        summary = read_json(options.output)['candidates']['fixed-5']
        check('collector pass with calibration indeterminate disclosed', summary['decision'] == 'pass'
              and summary['indeterminate_count'] == 3 and summary['chosen_extime'] == 3
              and summary['judgment_set_count'] == 27)
        check('collector accounting excludes duplicate latest view', summary['consumed_job_wall_s'] == {'A': 150.0, 'B': 1200.0})
        verify_paths = sorted(root.glob('verify/*/rep-*/attempt-*/result.json'))
        for vp in verify_paths:
            sr = read_json(vp)
            sr['ruling_sha256'] = 'b' * 64
            write_json(vp, sr)
        summarize(options)
        mixed = read_json(options.output)
        summary = mixed['candidates']['fixed-5']
        check('mixed calibration/verify SHA without acceptance rejected',
              summary['decision'] == 'undetermined' and 'ruling sha mismatch' in summary['reasons'])
        check('default SHA policy disclosed', all(
            item['ruling_sha_accepted'] == [] and item['ruling_sha_policy'] == 'single'
            for item in [mixed, *mixed['candidates'].values()]))
        options.accept_ruling_sha = ['b' * 64, 'a' * 64, 'b' * 64]
        options.markdown = root / 'summary.md'
        summarize(options)
        mixed = read_json(options.output)
        summary = mixed['candidates']['fixed-5']
        check('explicit accepted SHA set permits mixed phase pass', summary['decision'] == 'pass'
              and 'ruling sha mismatch' not in summary['reasons'])
        expected_counts = {'calibrate': {'a' * 64: 9}, 'verify': {'b' * 64: 24}}
        check('SHA phase counts count records once',
              mixed['ruling_sha_by_phase'] == summary['ruling_sha_by_phase'] == expected_counts
              and mixed['candidates']['fixed-10']['ruling_sha_by_phase'] == {'calibrate': {}, 'verify': {}})
        check('accepted SHA policy disclosed in JSON and Markdown', all(
            item['ruling_sha_accepted'] == ['a' * 64, 'b' * 64] and item['ruling_sha_policy'] == 'accepted-set'
            for item in [mixed, *mixed['candidates'].values()]) and all(
                '| ' + prefix + field + ' | ' in options.markdown.read_text()
                for prefix in ('', 'candidates.fixed-5.', 'candidates.fixed-10.')
                for field in ('ruling_sha_accepted', 'ruling_sha_by_phase', 'ruling_sha_policy')))
        options.accept_ruling_sha = ['a' * 64]
        summarize(options)
        summary = read_json(options.output)['candidates']['fixed-5']
        check('incomplete accepted SHA set rejected', summary['decision'] == 'undetermined'
              and 'ruling sha mismatch' in summary['reasons'])
        # Restore the original fixture before the existing retry checks.
        options.accept_ruling_sha = []
        options.markdown = None
        for vp in verify_paths:
            sr = read_json(vp)
            sr['ruling_sha256'] = 'a' * 64
            write_json(vp, sr)
        path = root / 'verify/fixed-5-write-heavy-1/rep-1/attempt-1/result.json'
        sr = read_json(path)
        sr['verify'].update(completed=False, rc=-9, timed_out=True, verdict=None, certified=None, anomaly_count=None)
        sr.update(execution_status='verifier_incomplete', operational_outcome='indeterminate')
        write_json(path, sr)
        retrydir = path.parent / 'reverify-2'
        retrydir.mkdir()
        retry = copy.deepcopy(sr)
        retry.update(phase='reverify', verify_attempt_id=2, original_result_sha256=sha(path),
                     execution_status='completed', operational_outcome='completed')
        retry['verify'] = good()['verify']
        write_json(retrydir / 'result.json', retry)
        summarize(options)
        summary = read_json(options.output)['candidates']['fixed-5']
        check('collector retry success preserves original incomplete count', summary['decision'] == 'pass'
              and summary['indeterminate_count'] == 4 and summary['slots'][0]['verify_attempt'] == 2)
        check('SHA phase counts include original and retry once',
              summary['ruling_sha_by_phase'] == {'calibrate': {'a' * 64: 9}, 'verify': {'a' * 64: 25}})
        retry['bench']['commit_witness'] = 999
        write_json(retrydir / 'result.json', retry)
        summarize(options)
        check('collector rejects different trace retry', read_json(options.output)['candidates']['fixed-5']['decision'] == 'undetermined')
    print(f'selftest: {"PASS" if all(checks) else "FAIL"} {sum(checks)}/{len(checks)} cases')
    return 0 if all(checks) else 1


def absolute(value):
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError('must be an absolute path')
    return path.resolve()


def ruling_sha(value):
    if len(value) != 64 or any(ch not in '0123456789abcdef' for ch in value):
        raise argparse.ArgumentTypeError('expected 64 lowercase hexadecimal characters')
    return value


def extimes(value):
    try:
        parsed = tuple(int(x) for x in value.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('expected 3,6,10') from exc
    if parsed != EXTIMES:
        raise argparse.ArgumentTypeError('ruling fixes extimes to 3,6,10')
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('selftest', help='lightweight synthetic checks; no compute processes')
    for command in ('calibrate', 'verify', 'reverify'):
        p = sub.add_parser(command)
        for name in ('repo-root', 'scratch-root', 'ruling'):
            p.add_argument('--' + name, type=absolute, required=True)
        if command == 'reverify':
            p.add_argument('--rep-dir', type=absolute, required=True)
            continue
        for name in ('third-party-cache', 'output-dir'):
            p.add_argument('--' + name, type=absolute, required=True)
        p.add_argument('--candidate', choices=CANDIDATES, required=True)
        p.add_argument('--workload', choices=WORKLOADS, required=True)
        if command == 'calibrate':
            p.add_argument('--extimes', type=extimes, default=EXTIMES)
        else:
            p.add_argument('--extime', type=int, choices=EXTIMES, required=True)
            p.add_argument('--reps', type=int, choices=(4,), default=4)
            p.add_argument('--rep-start', type=int, choices=(1, 5), required=True)
            p.add_argument('--job-index', type=int, choices=(1, 2), required=True)
            p.add_argument('--resume', action='store_true')
    p = sub.add_parser('summarize')
    p.add_argument('--input', type=absolute, required=True)
    p.add_argument('--output', type=absolute, required=True)
    p.add_argument('--markdown', type=absolute)
    p.add_argument('--accept-ruling-sha', type=ruling_sha, action='append', default=[],
                   metavar='sha256', help='accepted ruling SHA-256 (repeatable); default: single SHA')
    args = parser.parse_args()
    try:
        if args.command == 'selftest':
            return selftest()
        if args.command == 'summarize':
            return summarize(args)
        return run_job(args)
    except Exception as exc:
        print(f'{args.command}: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    raise SystemExit(main())
```

## v1 → v2 の unified diff

```diff
--- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.v1-run.py	2026-09-20 00:51:18.000000000 +0900
+++ /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/probe/verify_phase_runner.py	2026-09-20 00:51:19.000000000 +0900
@@ -846,7 +846,7 @@
     return 0 if success else 1


-def decide(candidate, calibration, slots, structural_errors=()):
+def decide(candidate, calibration, slots, structural_errors=(), accepted_ruling_sha=()):
     reasons = list(structural_errors)
     expected = {(w, i) for w in WORKLOADS for i in range(1, 9)}
     keys = [(r['workload'], r['rep_id']) for r in slots]
@@ -856,7 +856,8 @@
         reasons.append('missing/out-of-range rep')
     if any(r['candidate'] != candidate for r in calibration + slots):
         reasons.append('candidate mismatch')
-    if len({r['ruling_sha256'] for r in calibration + slots}) > 1:
+    digests = {r['ruling_sha256'] for r in calibration + slots}
+    if (not digests <= set(accepted_ruling_sha) if accepted_ruling_sha else len(digests) > 1):
         reasons.append('ruling sha mismatch')
     if len({r['extime'] for r in slots}) > 1:
         reasons.append('stage-B extime mismatch')
@@ -932,12 +933,17 @@


 def summarize(args):
+    accepted = sorted(set(getattr(args, 'accept_ruling_sha', None) or []))
+    policy = 'accepted-set' if accepted else 'single'
     calibrations = [read_json(p) for p in sorted(args.input.glob('calib/*/calib.json'))]
     jobs = [read_json(p) for p in sorted(args.input.rglob('job-*.json'))]
     fixed = max((j['F_s'] for j in jobs if j['phase'] == 'calibrate' and j['F_s'] is not None), default=None)
-    result = dict(schema_version=SCHEMA, generated_at=now(), F_hat_s=fixed, candidates={})
+    result = dict(schema_version=SCHEMA, generated_at=now(), F_hat_s=fixed, candidates={},
+                  ruling_sha_accepted=accepted, ruling_sha_policy=policy,
+                  ruling_sha_by_phase={'calibrate': {}, 'verify': {}})
     for c in CANDIDATES:
         errors, rows, slots, all_attempts = [], [], [], []
+        sha_retries = []
         cals = [x for x in calibrations if x['candidate'] == c]
         for cal in cals:
             rows.extend(cal['rows'])
@@ -976,6 +982,11 @@
                     continue
                 r, attempts = effective_attempt(rep_dir, errors)
                 all_attempts.extend(attempts)
+                for attempt in attempts:
+                    for path in sorted(Path(attempt['_path']).parent.glob('reverify-*/result.json')):
+                        retry = read_json(path)
+                        retry['_path'] = str(path)
+                        sha_retries.append(retry)
                 if r:
                     slots.append(r)
                     if r['extime'] != chosen:
@@ -997,7 +1008,24 @@
             errors.append('missing stage-B accounting job')
         if chosen is None and not any(anomaly(r) for r in rows):
             errors.append('no eligible extime within budget')
-        decision = decide(c, rows, slots, errors)
+        # Count each record once, including retries not selected as effective
+        # slots. Reverify records belong to the stage-B (verify) phase here.
+        sha_records = list({r.get('_path', id(r)): r
+                            for r in rows + all_attempts + sha_retries + slots}.values())
+        by_phase = {'calibrate': {}, 'verify': {}}
+        for r in sha_records:
+            phase = 'calibrate' if r['phase'] == 'calibrate' else 'verify'
+            digest = r.get('ruling_sha256')
+            counts = by_phase[phase]
+            counts[digest] = counts.get(digest, 0) + 1
+        if accepted and any(r.get('ruling_sha256') not in accepted for r in sha_records):
+            if not any(r.get('ruling_sha256') not in accepted for r in rows + slots):
+                errors.append('ruling sha mismatch')
+        decision = decide(c, rows, slots, errors, accepted_ruling_sha=accepted)
+        for phase, counts in by_phase.items():
+            total = result['ruling_sha_by_phase'][phase]
+            for digest, count in counts.items():
+                total[digest] = total.get(digest, 0) + count
         unfinished = [dict(phase=r['phase'], workload=r['workload'], extime=r['extime'],
                            rep_id=r['rep_id'], operational_outcome=r['operational_outcome'],
                            preserved=r['preservation']['complete'], destination=r['preservation']['destination'],
@@ -1021,7 +1049,8 @@
                                   bench_attempt=r['bench_attempt_id'] if r else None,
                                   verify_attempt=r['verify_attempt_id'] if r else None,
                                   result=r.get('_path') if r else None))
-        result['candidates'][c] = dict(**decision, calibration_table=[dict(
+        result['candidates'][c] = dict(**decision, ruling_sha_accepted=accepted,
+            ruling_sha_policy=policy, ruling_sha_by_phase=by_phase, calibration_table=[dict(
             candidate=c, workload=r['workload'], extime=r['extime'], eligible=eligible(r),
             verifier_wall_s=r['verify']['wall_s'], verdict=r['verify']['verdict'], stop_reason=r['stop_reason']) for r in rows],
             eligible_sets=sets, intersection=intersection, initial_extime=max(intersection, default=None),
@@ -1045,7 +1074,9 @@
 def render_markdown(result):
     # Flatten every field so the human-readable report cannot omit accounting or failures.
     def leaves(value, prefix=''):
-        if isinstance(value, dict):
+        if prefix.rsplit('.', 1)[-1] in ('ruling_sha_accepted', 'ruling_sha_by_phase', 'ruling_sha_policy'):
+            yield '| ' + prefix + ' | ' + json.dumps(value, ensure_ascii=False) + ' |'
+        elif isinstance(value, dict):
             for k, v in value.items():
                 yield from leaves(v, prefix + '.' + k if prefix else k)
         elif isinstance(value, list) and value:
@@ -1216,6 +1247,48 @@
               and summary['indeterminate_count'] == 3 and summary['chosen_extime'] == 3
               and summary['judgment_set_count'] == 27)
         check('collector accounting excludes duplicate latest view', summary['consumed_job_wall_s'] == {'A': 150.0, 'B': 1200.0})
+        verify_paths = sorted(root.glob('verify/*/rep-*/attempt-*/result.json'))
+        for vp in verify_paths:
+            sr = read_json(vp)
+            sr['ruling_sha256'] = 'b' * 64
+            write_json(vp, sr)
+        summarize(options)
+        mixed = read_json(options.output)
+        summary = mixed['candidates']['fixed-5']
+        check('mixed calibration/verify SHA without acceptance rejected',
+              summary['decision'] == 'undetermined' and 'ruling sha mismatch' in summary['reasons'])
+        check('default SHA policy disclosed', all(
+            item['ruling_sha_accepted'] == [] and item['ruling_sha_policy'] == 'single'
+            for item in [mixed, *mixed['candidates'].values()]))
+        options.accept_ruling_sha = ['b' * 64, 'a' * 64, 'b' * 64]
+        options.markdown = root / 'summary.md'
+        summarize(options)
+        mixed = read_json(options.output)
+        summary = mixed['candidates']['fixed-5']
+        check('explicit accepted SHA set permits mixed phase pass', summary['decision'] == 'pass'
+              and 'ruling sha mismatch' not in summary['reasons'])
+        expected_counts = {'calibrate': {'a' * 64: 9}, 'verify': {'b' * 64: 24}}
+        check('SHA phase counts count records once',
+              mixed['ruling_sha_by_phase'] == summary['ruling_sha_by_phase'] == expected_counts
+              and mixed['candidates']['fixed-10']['ruling_sha_by_phase'] == {'calibrate': {}, 'verify': {}})
+        check('accepted SHA policy disclosed in JSON and Markdown', all(
+            item['ruling_sha_accepted'] == ['a' * 64, 'b' * 64] and item['ruling_sha_policy'] == 'accepted-set'
+            for item in [mixed, *mixed['candidates'].values()]) and all(
+                '| ' + prefix + field + ' | ' in options.markdown.read_text()
+                for prefix in ('', 'candidates.fixed-5.', 'candidates.fixed-10.')
+                for field in ('ruling_sha_accepted', 'ruling_sha_by_phase', 'ruling_sha_policy')))
+        options.accept_ruling_sha = ['a' * 64]
+        summarize(options)
+        summary = read_json(options.output)['candidates']['fixed-5']
+        check('incomplete accepted SHA set rejected', summary['decision'] == 'undetermined'
+              and 'ruling sha mismatch' in summary['reasons'])
+        # Restore the original fixture before the existing retry checks.
+        options.accept_ruling_sha = []
+        options.markdown = None
+        for vp in verify_paths:
+            sr = read_json(vp)
+            sr['ruling_sha256'] = 'a' * 64
+            write_json(vp, sr)
         path = root / 'verify/fixed-5-write-heavy-1/rep-1/attempt-1/result.json'
         sr = read_json(path)
         sr['verify'].update(completed=False, rc=-9, timed_out=True, verdict=None, certified=None, anomaly_count=None)
@@ -1232,6 +1305,8 @@
         summary = read_json(options.output)['candidates']['fixed-5']
         check('collector retry success preserves original incomplete count', summary['decision'] == 'pass'
               and summary['indeterminate_count'] == 4 and summary['slots'][0]['verify_attempt'] == 2)
+        check('SHA phase counts include original and retry once',
+              summary['ruling_sha_by_phase'] == {'calibrate': {'a' * 64: 9}, 'verify': {'a' * 64: 25}})
         retry['bench']['commit_witness'] = 999
         write_json(retrydir / 'result.json', retry)
         summarize(options)
@@ -1247,6 +1322,12 @@
     return path.resolve()


+def ruling_sha(value):
+    if len(value) != 64 or any(ch not in '0123456789abcdef' for ch in value):
+        raise argparse.ArgumentTypeError('expected 64 lowercase hexadecimal characters')
+    return value
+
+
 def extimes(value):
     try:
         parsed = tuple(int(x) for x in value.split(','))
@@ -1284,6 +1365,8 @@
     p.add_argument('--input', type=absolute, required=True)
     p.add_argument('--output', type=absolute, required=True)
     p.add_argument('--markdown', type=absolute)
+    p.add_argument('--accept-ruling-sha', type=ruling_sha, action='append', default=[],
+                   metavar='sha256', help='accepted ruling SHA-256 (repeatable); default: single SHA')
     args = parser.parse_args()
     try:
         if args.command == 'selftest':
```
