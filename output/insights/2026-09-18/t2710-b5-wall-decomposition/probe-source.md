# probe の逐語 (Codex `role=author`、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2710-b5-wall-decomposition/probe/`、repo へは入れない)

3 file とも 2026-09-18 の段 5 author (`codex/s5-author.md`) が unit worktree `.codex/worktrees/t2710-unit-probe` の `probe-t2710/` に書き、親が実行前に job dir へ退避した。login selftest 45/45 PASS。計算ノードでは `python3.10 t2710_probe_runner.py run --repo-root <wave worktree> --probe-dir <job dir>/probe --out-root <job dir>/runs/<job> --conditions <list> --job-tag <job>` を `tools/pegasus/dispatch_compute.py --task generic` で投げた (launcher は `codex/launch-job.sh`)。

| file | bytes | sha256 |
|---|---|---|
| `t2710_probe_plugin.py` | 19683 | `a1b95dfcbc819513f136a3631b10907112295acab2283e5ae248b6d384d9a60e` |
| `t2710_probe_runner.py` | 25326 | `a49b61731b326885b5fe02fcd8751a229b158427fb1493878ba2641e0cfc6af5` |
| `t2710_probe_analyze.py` | 27183 | `622b38c2912ef2218408352b1b22521093da13f40001aa1628cc4c61e3179524` |

## t2710_probe_plugin.py

```python
"""Opt-in pytest observer; never imports the held test module."""
import atexit
import collections
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import threading
import time

import pytest

TEST_FILE = 'orchestrator/tests/test_s8b_oracle_driver.py'
SINGLE = 'test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5'
PARAMS = ('known-artifact-known_axes.artifact_bytes',
          'holdout-artifact-holdout.artifact_bytes',
          'ccbench-current-known_axes.ccbench_current',
          'unknownness-layer2-holdout.unknownness_layer2')
M = tuple(TEST_FILE + '::' + name for name in (
    'test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5',
    *(SINGLE + '[' + p + ']' for p in PARAMS),
    'test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5',
    *('test_t080_full_valid_history_defects_have_one_baseline_reason_f28[' + p + ']'
      for p in ('bad-trailer-receipt.user_commit_trailer',
                'extra-r-path-receipt.introduction_diff',
                'modify-revert-receipt.history_mutated')),
    'test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28',
    'test_never_issued_generator_tamper_reaches_public_driver_gate_g7'))
C_NODE = TEST_FILE + '::' + SINGLE + '[' + PARAMS[2] + ']'
FIELDS = set('run_id condition nodeid worker pid phase event span_id parent_span_id '
             't_start t_end monotonic_start monotonic_end call_index outcome extra'.split())


def canonical(nodeid):
    return nodeid[:nodeid.rfind('@')] if nodeid.rfind('@') > nodeid.rfind(']') else nodeid


def scope(nodeid):
    return nodeid.rsplit('@', 1)[1] if nodeid.rfind('@') > nodeid.rfind(']') else nodeid


def digest(ids):
    return hashlib.sha256(json.dumps(list(ids), ensure_ascii=True,
                                    separators=(',', ':')).encode()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n')


def units_for(items, cost_fn, scope_fn=scope, initial=96):
    units = {}
    for item in items:
        key = scope_fn(item.nodeid)
        units.setdefault(key, {'scope': key, 'items': [], 'index': len(units)})['items'].append(item)
    known_costs = []
    for u in units.values():
        costs = [cost_fn(i) for i in u['items']]
        known = all(x is not None and math.isfinite(x) for x in costs)
        total = sum(costs) if known else None
        u['cost'] = total if total is not None and math.isfinite(total) else None
        if u['cost'] is not None:
            known_costs.append(u['cost'])
    known_costs.sort(reverse=True)
    unknown = known_costs[min(initial, len(known_costs)) - 1] if known_costs else None
    for u in units.values():
        u['known'] = u['cost'] is not None
        if not u['known']:
            u['cost'] = unknown
    return list(units.values())


def reorder_b(units):
    qa = sorted(units, key=lambda u: -len(u['items']))
    if len(qa) < 96 or any(u['cost'] is None for u in qa):
        raise pytest.UsageError('t2710 B infeasible: fewer than 96 units or unavailable costs')
    ranked = sorted(range(48, len(qa)), key=lambda i: (qa[i]['cost'], i))[:48]
    chosen = set(ranked)
    qb = qa[:48] + [qa[i] for i in ranked] + [u for i, u in enumerate(qa) if i >= 48 and i not in chosen]
    if [u['scope'] for u in sorted(qb, key=lambda u: -len(u['items']))] != [u['scope'] for u in qb]:
        raise pytest.UsageError('t2710 B infeasible: cardinality sort changes intended queue')
    return qa, qb


def deselect_c(items, config):
    removed = [i for i in items if canonical(i.nodeid) == C_NODE]
    if len(removed) != 1:
        raise pytest.UsageError('t2710 C requires exactly one target')
    items[:] = [i for i in items if i is not removed[0]]
    config.hook.pytest_deselected(items=removed)
    return removed[0].nodeid


def unit_payload(units):
    return [{'scope': u['scope'], 'cost': u['cost'], 'nodes': len(u['items']),
             'nodeids': [i.nodeid for i in u['items']]} for u in units]


def initial_pairs(units, workers):
    """loadscope initial assign + reschedule (pending item count <= 2)."""
    queue = sorted(units, key=lambda u: -len(u['items']))
    first = queue[:workers]
    cursor = len(first)
    result = {}
    for unit in first:
        second = None
        if len(unit['items']) <= 2 and cursor < len(queue):
            second = unit_payload([queue[cursor]])[0]
            cursor += 1
        result[unit['scope']] = second
    return result


def aggregate_reports(reports):
    workers = {}
    for r in reports:
        w = workers.setdefault(r['worker'], {'duration': 0.0, 'nodes': {}})
        w['duration'] += r['duration']
        n = w['nodes'].setdefault(r['nodeid'], {'nodeid': r['nodeid'], 'duration': 0.0,
                                               'start': r['start'], 'phases': {}})
        n['duration'] += r['duration']
        n['start'] = min(n['start'], r['start'])
        n['phases'][r['when']] = r['duration']
    for w in workers.values():
        w['items'] = sorted(w.pop('nodes').values(), key=lambda n: n['start'])
        w['count'] = len(w['items'])
    return workers


class Recorder:
    def __init__(self, out, condition, run_id, worker):
        self.out, self.condition, self.run_id, self.worker = Path(out), condition, run_id, worker
        self.pid = os.getpid()
        self.path = self.out / f'spans-{worker}-{self.pid}.jsonl'
        self.nodeid, self.phase = '', 'session'
        self.events, self.errors = [], []
        self.local = threading.local()
        self.counter = 0
        self.error_count = 0
        self.indices = collections.Counter()
        self.passages = collections.Counter()
        self.undo = []
        self.report_seconds = 0.0
        self.reports, self.collections = [], {}
        self.session_start = None

    def stack(self):
        if not hasattr(self.local, 'stack'):
            self.local.stack = []
        return self.local.stack

    def begin(self, event, extra=None):
        self.counter += 1
        self.indices[event] += 1
        stack = self.stack()
        e = dict(run_id=self.run_id, condition=self.condition, nodeid=self.nodeid,
                 worker=self.worker, pid=self.pid, phase=self.phase, event=event,
                 span_id=f'{self.pid}:{self.counter}', parent_span_id=stack[-1]['span_id'] if stack else None,
                 t_start=time.time(), t_end=None, monotonic_start=time.monotonic(),
                 monotonic_end=None, call_index=self.indices[event], outcome='ok', extra=extra or {})
        stack.append(e)
        return e

    def append(self, e):
        self.events.append(e)

    def record_error(self, exc):
        now, mono = time.time(), time.monotonic()
        self.error_count += 1
        e = dict(run_id=self.run_id, condition=self.condition, nodeid=self.nodeid,
                 worker=self.worker, pid=self.pid, phase=self.phase, event='record-error',
                 span_id=f'{self.pid}:error:{self.error_count}', parent_span_id=None,
                 t_start=now, t_end=now, monotonic_start=mono, monotonic_end=mono,
                 call_index=0, outcome='record-error', extra={'error': repr(exc)})
        self.errors.append(e)

    def end(self, e, outcome='ok'):
        e.update(t_end=time.time(), monotonic_end=time.monotonic(), outcome=outcome)
        stack = self.stack()
        if stack and stack[-1] is e:
            stack.pop()
        try:
            self.append(e)
        except Exception as exc:
            self.record_error(exc)

    def instant(self, event, extra):
        self.end(self.begin(event, extra))

    def wrap(self, original, event, predicate=None, metadata=None):
        @functools.wraps(original)
        def observed(*args, **kwargs):
            e = None
            try:
                self.passages[event] += 1
                if predicate is None or predicate(args, kwargs):
                    e = self.begin(event, metadata(args, kwargs) if metadata else {})
            except Exception as exc:
                self.record_error(exc)
            outcome = 'ok'
            try:
                return original(*args, **kwargs)
            except BaseException:
                outcome = 'exception'
                raise
            finally:
                if e is not None:
                    try:
                        self.end(e, outcome)
                    except Exception as exc:
                        self.record_error(exc)
        return observed

    def patch(self, owner, name, event, **kwargs):
        original = getattr(owner, name)
        setattr(owner, name, self.wrap(original, event, **kwargs))
        self.undo.append((owner, name, original))

    def restore(self):
        for owner, name, original in reversed(self.undo):
            setattr(owner, name, original)
        self.undo.clear()

    def flush(self, overhead=False):
        batch, self.events = self.events + self.errors, []
        self.errors = []
        started = time.monotonic()
        try:
            raw = ''.join(json.dumps(e, ensure_ascii=True) + '\n' for e in batch).encode()
            with self.path.open('ab') as f:
                f.write(raw)
            elapsed = time.monotonic() - started
            if overhead:
                self.instant('overhead', {'wrapper_passages': dict(self.passages),
                    'passages': sum(self.passages.values()), 'recorded': len(batch),
                    'bytes': len(raw), 'write_seconds': elapsed,
                    'excludes_own_overhead_line': True})
                self.flush()
        except Exception as exc:
            self.record_error(exc)
            try:
                write_json(self.out / f'record-error-{self.worker}-{self.pid}.json', self.errors)
            except Exception:
                print('T2710 record-error: ' + repr(exc), file=sys.stderr)


def install(rec, item):
    module = item.module
    if Path(module.__file__).resolve() != (Path.cwd() / TEST_FILE).resolve():
        raise pytest.UsageError('t2710 module file mismatch')
    rec.nodeid, rec.phase = canonical(item.nodeid), 'setup'
    rec.indices.clear()
    rec.passages.clear()
    rec.patch(module, '_build_t080_stub_free_e2e_repo', 'build',
              metadata=lambda a, k: {'base_parent': str(a[0]), 'kwargs': k})
    rec.patch(module._T080SharedBases, 'get', 'get',
              metadata=lambda a, k: {'key': a[1], 'base_path': str(a[0].parent)})
    rec.patch(module, '_t080_stub_free_e2e_repo', 'helper',
              metadata=lambda a, k: {'tmp_path': str(a[0]), 'key': [k.get('r_trailer', 'AI-Agent: none'),
                  k.get('extra_r_path', False), k.get('issue_receipt', True), k.get('distinct_basis_blob', False)]})
    copied = set()
    def top_copy(a, k):
        stack = rec.stack()
        if not stack or stack[-1]['event'] != 'helper' or stack[-1]['span_id'] in copied:
            return False
        caller = sys._getframe(2)
        if caller.f_code.co_name != '_t080_stub_free_e2e_repo':
            return False
        copied.add(stack[-1]['span_id'])
        return True
    rec.patch(module.shutil, 'copytree', 'copytree_top', predicate=top_copy,
              metadata=lambda a, k: {'source': str(a[0]), 'destination': str(a[1])})
    rec.patch(module.fcntl, 'flock', 'flock_ex', predicate=lambda a, k:
              any(e['event'] == 'get' for e in rec.stack()) and
              bool(a[1] & module.fcntl.LOCK_EX) and not bool(a[1] & module.fcntl.LOCK_NB))
    rec.patch(module.migration, 'verify_receipt', 'verify',
              metadata=lambda a, k: {'root': str(k.get('root', a[0] if a else ''))})
    if not getattr(module, '_t2710_close_observer', False):
        original = module._T080SharedBases.close
        def close_observed(obj, *a, **k):
            old_node, old_phase = rec.nodeid, rec.phase
            rec.nodeid, rec.phase = '', 'session'
            try:
                return rec.wrap(original, 'close', metadata=lambda a, k:
                                {'base_path': str(a[0].parent)})(obj, *a, **k)
            finally:
                rec.flush()
                rec.nodeid, rec.phase = old_node, old_phase
        module._T080SharedBases.close = close_observed
        module._t2710_close_observer = True
        bases = module._T080_SHARED_BASES
        if bases is not None:
            # Import captured a bound method. Class replacement alone misses it.
            # Rebind exactly once; this moves this callback later in registration
            # order (earlier at exit). Never call close early or twice.
            atexit.unregister(original.__get__(bases, type(bases)))
            atexit.register(bases.close)
        rec.instant('installation', {'module': str(module.__file__),
                    'atexit_callback_rebound': bases is not None})


_REC = None


def pytest_configure(config):
    global _REC
    _REC = None
    names = ('T2710_PROBE_CONDITION', 'T2710_PROBE_OUT', 'T2710_PROBE_RUN_ID')
    values = [os.environ.get(n) for n in names]
    if not any(v is not None for v in values):
        return
    condition, out, run_id = values
    if condition not in ('S1', 'S', 'A', 'B', 'C') or not out or run_id is None:
        raise pytest.UsageError('t2710 incomplete probe environment')
    if not Path(out).is_absolute() or not Path(out).is_dir():
        raise pytest.UsageError('t2710 output must be an existing absolute directory')
    _REC = Recorder(out, condition, run_id, os.environ.get('PYTEST_XDIST_WORKER', 'controller'))
    _REC.plugins = sorted(str(n) for n, p in config.pluginmanager.list_name_plugin() if p is not None)


def pytest_sessionstart(session):
    if _REC:
        _REC.session_start = time.time()
        if _REC.worker != 'controller':
            _REC.instant('session', {'hook': 'sessionstart', 'plugins': _REC.plugins})
            _REC.flush()


@pytest.hookimpl(tryfirst=True)
def pytest_collection_finish(session):
    r = _REC
    if not r or r.worker == 'controller':
        return
    r.instant('session', {'hook': 'collection_finish'})
    config, items = session.config, session.items
    if r.condition in ('A', 'B', 'C') and not hasattr(config, '_izanagi_acceptance_shard_state'):
        r.instant('collection-error', {'reason': 'production selection missing'})
        r.flush()
        raise pytest.UsageError('t2710 production shard state missing')
    conftests = [p for p in config.pluginmanager.get_plugins()
                 if hasattr(p, '_acceptance_duration_for_item') and
                 Path(getattr(p, '__file__', '')).resolve() == (Path.cwd() / 'orchestrator/tests/conftest.py').resolve()]
    if len(conftests) != 1:
        raise pytest.UsageError('t2710 conftest not found uniquely')
    cf = conftests[0]
    ledger = getattr(config, cf._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR)
    units = units_for(items, lambda i: cf._acceptance_duration_for_item(i, ledger),
                      cf._acceptance_loadgroup_scope, cf._ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS)
    if r.condition == 'B':
        try:
            qa, units = reorder_b(units)
        except pytest.UsageError:
            r.instant('B-infeasible', {'cardinality': dict(collections.Counter(len(u['items']) for u in units))})
            r.flush()
            raise
        items[:] = [i for u in units for i in u['items']]
        write_json(r.out / f'b-intended-{r.worker}.json', {'sha256': digest(i.nodeid for i in items),
            'count': len(items), 'units': unit_payload(units[:120]), 'qa': unit_payload(qa[:120])})
    removed = deselect_c(items, config) if r.condition == 'C' else None
    if removed:
        # These are diagnostic costs for C's execution collection, never a
        # second sort or a change to production's allocated selected set.
        units = units_for(items, lambda i: cf._acceptance_duration_for_item(i, ledger),
                          cf._acceptance_loadgroup_scope, cf._ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS)
    r.instant('collection', {'units': unit_payload(units[:100]), 'unit_count': len(units),
        'unit_costs': {u['scope']: u['cost'] for u in units},
        'initial_pairs': initial_pairs(units, {'S1': 1, 'S': 11}.get(r.condition, 48)),
        'deselected': removed, 'executed_selected': [i.nodeid for i in items],
        'allocated_selected': getattr(config, '_izanagi_acceptance_shard_state', {}).get('selected'),
        'cardinality': dict(collections.Counter(len(u['items']) for u in units))})
    r.flush()


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node, ids):
    r = _REC
    if not r or r.worker != 'controller':
        return
    worker = node.gateway.id
    entry = {'received_at': time.time(), 'ids_first_200': list(ids[:200]),
             'sha256': digest(ids), 'count': len(ids)}
    if r.condition == 'B':
        try:
            intended = json.loads((r.out / f'b-intended-{worker}.json').read_text())
            entry['intended_matches'] = entry['sha256'] == intended['sha256'] and len(ids) == intended['count']
            entry['intended_units'] = intended['units']
        except Exception as exc:
            entry.update(intended_matches=False, error=repr(exc))
    r.collections[worker] = entry


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if _REC and _REC.worker != 'controller' and canonical(item.nodeid) in M:
        install(_REC, item)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    r = _REC
    e = None
    if r and r.worker != 'controller' and canonical(item.nodeid) in M:
        r.phase = 'call'
        e = r.begin('call')
    outcome = yield
    if e is not None:
        r.end(e, 'exception' if outcome.excinfo else 'ok')


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    if _REC and _REC.worker != 'controller':
        _REC.phase = 'teardown'


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    try:
        yield
    finally:
        if _REC and _REC.worker != 'controller' and canonical(item.nodeid) in M:
            _REC.restore()
            _REC.flush(overhead=True)
            _REC.nodeid, _REC.phase = '', 'session'


def pytest_runtest_logreport(report):
    r = _REC
    if r and r.worker == 'controller':
        start = time.monotonic()
        r.reports.append({'nodeid': report.nodeid, 'worker': getattr(report, 'worker_id', 'serial'),
            'when': report.when, 'start': report.start, 'stop': report.stop,
            'duration': report.duration, 'outcome': report.outcome})
        r.report_seconds += time.monotonic() - start


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    r = _REC
    if not r:
        return
    if r.worker != 'controller':
        r.instant('session', {'hook': 'sessionfinish', 'exitstatus': int(exitstatus)})
        r.flush()
    else:
        workers = aggregate_reports(r.reports)
        busy = max(workers, key=lambda w: workers[w]['duration'], default=None)
        longest = max((dict(n, worker=w) for w, d in workers.items() for n in d['items']),
                      key=lambda n: n['duration'], default=None)
        write_json(r.out / 'controller.json', {'reports': r.reports, 'workers': workers,
            'most_busy_worker': busy, 'longest_node': longest, 'collections': r.collections,
            'session_start': r.session_start, 'session_finish': time.time(),
            'exitstatus': int(exitstatus), 'plugins': r.plugins,
            'overhead': {'report_count': len(r.reports), 'report_seconds': r.report_seconds}})

```

## t2710_probe_runner.py

```python
"""Sequential compute runner and lightweight, session-free selftest."""
import argparse
import collections
import fcntl
import getpass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace as NS

# Keep the three-source probe directory free of generated bytecode in selftest.
sys.dont_write_bytecode = True


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def listing(path):
    try:
        return sorted(str(p) for p in Path(path).iterdir())
    except OSError as exc:
        return {'error': repr(exc)}


def residues():
    tmp = Path(tempfile.gettempdir())
    shared = sorted(str(p) for p in tmp.glob('izanagi-t080-e2e-session-*'))
    pytest_dirs = {str(p): listing(p) for p in sorted(tmp.glob('pytest-of-*'))}
    return {'shared_bases': shared, 'pytest_dirs': pytest_dirs}


def filesystem(path):
    path = str(Path(path).resolve())
    matches = []
    for line in Path('/proc/mounts').read_text().splitlines():
        fields = line.split()
        mount = fields[1].replace('\\040', ' ').replace('\\011', '\t').replace('\\134', '\\')
        if path == mount or path.startswith(mount.rstrip('/') + '/'):
            matches.append((len(mount), mount, fields[2]))
    mount = max(matches) if matches else (0, None, None)
    st = os.statvfs(path)
    return {'mount': mount[1], 'fstype': mount[2], 'free_bytes': st.f_bavail * st.f_frsize,
            'total_bytes': st.f_blocks * st.f_frsize, 'free_inodes': st.f_favail}


def environment(repo, probe):
    keys = ('TMPDIR', 'TMP', 'TEMP', 'PATH', 'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE',
            'PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD',
            'PBS_JOBID', 'LANG', 'LC_ALL', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
            'IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1')
    return {'tempdir': tempfile.gettempdir(), 'filesystem': filesystem(tempfile.gettempdir()),
            'pytest_user_contents': listing(Path(tempfile.gettempdir()) / ('pytest-of-' + getpass.getuser())),
            **residues(), 'hostname': socket.gethostname(), 'PBS_JOBID': os.environ.get('PBS_JOBID'),
            'env': {k: os.environ.get(k) for k in keys},
            'interpreter': sys.executable, 'python_version': sys.version,
            'pytest_version': importlib.metadata.version('pytest'),
            'xdist_version': importlib.metadata.version('pytest-xdist'),
            'git_head': command('git', 'rev-parse', 'HEAD'),
            'git_status_line_count': len(command('git', 'status', '--porcelain').splitlines()),
            'ledger_sha256': sha(repo / 'orchestrator/tests/acceptance_duration_ledger.json'),
            'probe_sha256': {p.name: sha(p) for p in sorted(probe.glob('t2710_probe_*.py'))}}


def lock_checks(paths):
    results = []
    for parent in paths:
        path = Path(parent) / 'workers.lock'
        try:
            with path.open('r+b') as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    results.append({'path': str(path), 'status': '残存 worker の疑い'})
                else:
                    fcntl.flock(f, fcntl.LOCK_UN)
                    results.append({'path': str(path), 'status': 'unlocked'})
        except OSError as exc:
            results.append({'path': str(path), 'status': 'unavailable', 'error': repr(exc)})
    return results


def microbench(out):
    start = time.monotonic()
    for _ in range(100000):
        time.monotonic()
    clock = time.monotonic() - start
    events = []
    start = time.monotonic()
    for i in range(100000):
        events.append({'event': 'sample', 'index': i, 'duration': 0.1})
    append = time.monotonic() - start
    start = time.monotonic()
    with tempfile.TemporaryFile(mode='w+', dir=out) as f:
        for e in events[:1000]:
            f.write(json.dumps(e, ensure_ascii=True) + '\n')
        f.flush()
    write = time.monotonic() - start
    dump(out / 'microbench.json', {'monotonic_100000': clock, 'dict_append_100000': append,
        'json_write_1000': write, 'clock_unit': clock / 100000,
        'record_unit': append / 100000, 'json_line_unit': write / 1000,
        'note': 'Clock/dict costs are proxies, not an upper bound on predicate or I/O interference.'})


def run(args):
    if not args.require_hostname_prefix or not socket.gethostname().startswith(args.require_hostname_prefix):
        print('hostname does not match required prefix: ' + args.require_hostname_prefix, file=sys.stderr)
        return 2
    repo, probe, out = (Path(p).resolve() for p in (args.repo_root, args.probe_dir, args.out_root))
    conditions = args.conditions.split(',')
    if any(c not in ('S1', 'S', 'A', 'B', 'C') for c in conditions):
        raise ValueError('unknown condition')
    os.chdir(repo)
    sys.path.insert(0, str(probe))
    sys.path.insert(0, str(repo))
    from t2710_probe_plugin import M, C_NODE
    from tools import acceptance_shards
    out.mkdir(parents=True, exist_ok=True)
    microbench(out)
    failed = False
    job_tag = args.job_tag or out.name
    for ordinal, condition in enumerate(conditions, 1):
        directory = out / f'{ordinal:02d}-{condition}'
        directory.mkdir()  # Refuse accidental reuse of an existing run.
        session = None
        before = None
        record = {'condition': condition, 'ordinal': ordinal, 'job_tag': job_tag,
                  'run_id': f'{job_tag}-{ordinal:02d}-{condition}', 'rc': None,
                  'hostname': socket.gethostname(), 'errors': []}
        started = time.monotonic()
        try:
            before = environment(repo, probe)
            dump(directory / 'env-before.json', before)
            env = os.environ.copy()
            env['PYTHONPATH'] = str(probe) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
            env.update(T2710_PROBE_CONDITION=condition, T2710_PROBE_OUT=str(directory),
                       T2710_PROBE_RUN_ID=record['run_id'])
            if condition in ('S1', 'S'):
                targets, n = ([C_NODE], 1) if condition == 'S1' else (list(M), 11)
                junit = directory / 'junit.xml'
                plugins = ['-p', 'no:cacheprovider', '-p', 't2710_probe_plugin']
                if env.get(acceptance_shards.PLUGIN_SPEC_ENV):
                    raise RuntimeError('S1/S inherited a production shard spec; refusing mixed condition')
            else:
                session = acceptance_shards.create_session(repo, 3)
                record['acceptance_session_original'] = str(session)
                env[acceptance_shards.PLUGIN_SPEC_ENV] = json.dumps(
                    {'session_root': str(session), 'shard_count': 3, 'shard_index': 0},
                    separators=(',', ':'), sort_keys=True)
                targets, n = ['orchestrator/tests'], 48
                junit = session / 'shard-0/junit.xml'
                plugins = ['-p', 'tools.acceptance_shards', '-p', 'no:cacheprovider', '-p', 't2710_probe_plugin']
            argv = ['python3.10', '-m', 'pytest', *targets, '-n', str(n), '--dist', 'loadgroup',
                    '--junitxml=' + str(junit), *plugins]
            record.update(argv=argv, child_interpreter=shutil.which('python3.10'),
                child_env={k: v for k, v in env.items() if k.startswith(('T2710_', 'PYTEST_', 'IZANAGI_')) or
                           k in ('PYTHONPATH', 'TMPDIR', 'TEMP', 'TMP')}, start_epoch=time.time())
            dump(directory / 'run.json', record)
            started = time.monotonic()
            with (directory / 'pytest.log').open('wb') as log:
                record['rc'] = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
            record['outer_wall'] = time.monotonic() - started
            record['stop_epoch'] = time.time()
        except Exception as exc:
            record['errors'].append(repr(exc))
            record['rc'] = record['rc'] if record['rc'] is not None else 2
        finally:
            record.setdefault('outer_wall', time.monotonic() - started)
            if session is not None:
                try:
                    shutil.move(str(session), str(directory / 'acceptance-session'))
                    record['acceptance_session_moved'] = str(directory / 'acceptance-session')
                except Exception as exc:
                    record['errors'].append('session move failed: ' + repr(exc))
            try:
                after = residues()
                old = before or {'shared_bases': [], 'pytest_dirs': {}}
                after['new_shared_bases'] = sorted(set(after['shared_bases']) - set(old['shared_bases']))
                after['new_pytest_entries'] = {p: sorted(set(v) - set(old['pytest_dirs'].get(p, [])))
                    for p, v in after['pytest_dirs'].items() if isinstance(v, list)}
                after['locks'] = lock_checks(after['shared_bases'])
                dump(directory / 'env-after.json', after)
            except Exception as exc:
                record['errors'].append('after snapshot failed: ' + repr(exc))
            dump(directory / 'run.json', record)
        failed |= record['rc'] != 0 or bool(record['errors'])
        print(record['run_id'], 'rc=', record['rc'], flush=True)
    return 1 if failed else 0


def selftest(args):
    sys.path.insert(0, str(Path(args.probe_dir).resolve()))
    import t2710_probe_plugin as p
    import t2710_probe_analyze as a
    checks = []
    def check(name, ok):
        checks.append((name, bool(ok)))
    with tempfile.TemporaryDirectory(prefix='t2710-selftest-') as tmp:
        r = p.Recorder(tmp, 'S1', 'synthetic', 'gw0')
        marker, arg = object(), object()
        calls = []
        def original(*args, **kwargs):
            calls.append((args, kwargs))
            return marker
        wrapped = r.wrap(original, 'helper')
        check('return identity and exactly one call', wrapped(arg, key=arg) is marker and len(calls) == 1)
        check('argument identity', calls[0][0][0] is arg and calls[0][1]['key'] is arg)
        failure = RuntimeError('synthetic original')
        def raises():
            raise failure
        try:
            r.wrap(raises, 'verify')()
        except RuntimeError as exc:
            check('exception object', exc is failure)
        saved = r.append
        def broken(e):
            raise OSError('synthetic recording failure')
        r.append = broken
        check('record failure preserves return', r.wrap(original, 'verify')() is marker)
        try:
            r.wrap(raises, 'verify')()
        except RuntimeError as exc:
            check('record failure preserves exception', exc is failure)
        check('record-error separate sink', len(r.errors) == 2 and r.errors[0]['outcome'] == 'record-error')
        r.append = saved
        parent = r.begin('call')
        r.wrap(original, 'verify')()
        r.end(parent)
        check('nested parent', r.events[-2]['parent_span_id'] == parent['span_id'])
        owner = NS(fn=original)
        r.patch(owner, 'fn', 'helper')
        r.restore()
        check('restoration identity', owner.fn is original)
        r.flush(overhead=True)
        events = [json.loads(line) for line in r.path.read_text().splitlines()]
        check('JSONL required fields', all(p.FIELDS <= set(e) and isinstance(e['extra'], dict) for e in events))
        check('JSONL monotonic and epoch bounds', all(e['t_start'] <= e['t_end'] and
              e['monotonic_start'] <= e['monotonic_end'] for e in events))
        ids = {e['span_id'] for e in events}
        check('span correspondence', all(e['parent_span_id'] is None or e['parent_span_id'] in ids for e in events))
        items = [NS(nodeid=f'test::g{g}-{i}@group{g}', cost=500.0) for g in range(4) for i in range(3)]
        items += [NS(nodeid=f'test::s{i}', cost=None if i % 17 == 0 else float(300-i)) for i in range(200)]
        units = p.units_for(items, lambda i: i.cost)
        qa, qb = p.reorder_b(units)
        flat = [i for u in qb for i in u['items']]
        check('B identity multiset', collections.Counter(map(id, flat)) == collections.Counter(map(id, items)))
        check('B unit internal order', all([i for i in items if p.scope(i.nodeid) == u['scope']] == u['items'] for u in qb))
        check('B top 48', qb[:48] == qa[:48])
        chosen = sorted(range(48, len(qa)), key=lambda i: (qa[i]['cost'], i))[:48]
        check('B minimum 48', qb[48:96] == [qa[i] for i in chosen])
        check('B rest stable', qb[96:] == [u for i, u in enumerate(qa) if i >= 48 and i not in chosen])
        check('B cardinality stable', sorted(qb, key=lambda u: -len(u['items'])) == qb)
        initial = p.initial_pairs(qb, 48)
        check('initial pending >2 gets no second', all(initial[u['scope']] is None for u in qb[:4]))
        check('initial singleton second skips large groups', initial[qb[4]['scope']]['scope'] == qb[48]['scope'])
        known = sorted([u['cost'] for u in units if u['known']], reverse=True)
        check('B unknown 96th cost', all(u['cost'] == known[95] for u in units if not u['known']))
        bad = [NS(nodeid=f'test::{g}-{i}@g{g}', cost=1000.0) for g in range(60) for i in range(3)]
        bad += [NS(nodeid=f'test::single{i}', cost=1.0) for i in range(100)]
        try:
            p.reorder_b(p.units_for(bad, lambda i: i.cost))
        except p.pytest.UsageError as exc:
            check('B infeasible fail closed', str(exc).startswith('t2710 B infeasible:'))
        else:
            check('B infeasible fail closed', False)
        selected = [p.C_NODE, p.M[0]]
        config = NS(_izanagi_acceptance_shard_state={'selected': selected},
                    hook=NS(pytest_deselected=lambda **kw: calls.append(kw)))
        keep = NS(nodeid=p.C_NODE + 'extra')
        target = NS(nodeid=p.C_NODE + '@group')
        citems = [keep, target, NS(nodeid=p.M[0])]
        p.deselect_c(citems, config)
        check('C exact only and selected unchanged', len(citems) == 2 and citems[0] is keep and
              config._izanagi_acceptance_shard_state['selected'] is selected and len(selected) == 2)
        check('C notification', calls[-1]['items'] == [target])
        check('M exact membership', len(p.M) == 11 and p.canonical(p.C_NODE + '@x') in p.M and p.C_NODE + 'x' not in p.M)
        reports = []
        for node, worker, base, durations in [('n1', 'gw0', 10, (1, 6, 1)), ('n2', 'gw0', 20, (0, 2, 0)),
                                               ('n3', 'gw1', 10, (0, 7, 0))]:
            start = base
            for when, duration in zip(('setup', 'call', 'teardown'), durations):
                reports.append(dict(nodeid=node, worker=worker, when=when, duration=duration,
                                    start=start, stop=start+duration, outcome='passed'))
                start += duration
        workers = p.aggregate_reports(reports)
        controller = dict(reports=reports, workers=workers, session_start=0, session_finish=30,
                          collections={}, overhead={'report_count': 9, 'report_seconds': 0})
        dump(Path(tmp) / 'controller.json', controller)
        (Path(tmp) / 'junit.xml').write_text('<testsuites><testsuite time="30"><testcase classname="n" name="1" time="8"/>'
            '<testcase classname="n" name="2" time="2"/><testcase classname="n" name="3" time="7"/></testsuite></testsuites>')
        metrics = a.shard_metrics(controller, Path(tmp) / 'junit.xml', 'A')
        check('phase sum/controller', sum(w['duration'] for w in workers.values()) == 17)
        check('W O F L P D', [metrics[k] for k in ('W', 'O', 'F', 'L', 'P', 'D')] == [30, 10, 20, 8, 2, 17])
        check('mean load', metrics['mean_load'] == 17/48)
        check('per metric median', a.summarize_values([3, 1, 8]) == {'values': [3, 1, 8], 'median': 3, 'n': 3})
        check('model formula', a.wall_model(8, 480, 20) == 30)
        history = a.history_compare([dict(W=2, O=2, F=2, L=2)],
                                    [dict(W=x, O=x, F=x, L=x) for x in (1, 2, 3)])
        check('history I percentile median ratio', history['I'] and history['metrics']['W']['percentiles'] == [0.5]
              and history['metrics']['W']['median_ratio'] == 1)
        check('interval union excludes nested', a.union_length([(0, 5), (1, 3), (4, 7)]) == 7)
        synthetic = [dict(event='helper', span_id='h', parent_span_id=None, monotonic_start=0, monotonic_end=10),
                     dict(event='get', span_id='g', parent_span_id='h', monotonic_start=1, monotonic_end=6),
                     dict(event='build', span_id='b', parent_span_id='g', monotonic_start=3, monotonic_end=5),
                     dict(event='flock_ex', span_id='f', parent_span_id='g', monotonic_start=1, monotonic_end=3)]
        check('tree residual', a.residual(synthetic, 'get', {'flock_ex', 'build'}) == 1)
        def span(event, sid, parent, lo, hi, index=1):
            return dict(event=event, span_id=sid, parent_span_id=parent, monotonic_start=lo,
                        monotonic_end=hi, nodeid=p.C_NODE, phase='call', call_index=index)
        spans = [span('call', 'c', None, 0, 30), span('helper', 'h', 'c', 0, 10)]
        spans += [span('verify', f'v{i}', 'c', lo, lo+2, i) for i, lo in enumerate((10, 12, 18, 20, 22), 1)]
        reduced = [p.TEST_FILE + '::' + p.SINGLE + '[' + param + ']' for param in (p.PARAMS[0], p.PARAMS[1], p.PARAMS[3])]
        model_input = dict(W=60, O=40, F=20, L=32, D=58,
            allnodes=[dict(nodeid=n, duration=d) for n, d in zip([p.C_NODE, 'other', *reduced], [32, 20, 1, 2, 3])])
        model = a.models(model_input, [dict(nodeid=p.C_NODE, setup=1, call=30, teardown=1, helper=10)], spans)
        check('split duplicated helper and 2+3 verification', [model[k] for k in
              ('d_positive', 'd_defect', 'L_split', 'D_split', 'split_model')] == [16, 28, 28, 70, 48])
        check('baseline residual and reduction model', [model[k] for k in
              ('A_model', 'A_residual', 'D_reduce', 'L_reduce', 'reduce_model')] == [52, 8, 52, 32, 52])
        fixture = Path(tmp) / '01-S1'
        fixture.mkdir()
        fixture_reports = [dict(nodeid=p.C_NODE, worker='gw0', when=w, start=t, stop=t+d, duration=d,
                                outcome='passed') for w, t, d in [('setup', 10, 1), ('call', 11, 30), ('teardown', 41, 1)]]
        fixture_controller = dict(reports=fixture_reports, workers=p.aggregate_reports(fixture_reports),
                                  session_start=0, session_finish=52, collections={}, exitstatus=0)
        dump(fixture / 'controller.json', fixture_controller)
        dump(fixture / 'run.json', dict(condition='S1', run_id='synthetic-S1', ordinal=1,
                                       hostname='synthetic', rc=0, outer_wall=54))
        (fixture / 'junit.xml').write_text('<testsuites><testsuite time="52"><testcase '
            'classname="orchestrator.tests.test_s8b_oracle_driver" name="' + p.C_NODE.split('::')[1] +
            '" time="32"/></testsuite></testsuites>')
        fixture_events = []
        for e in spans:
            e = dict(e, run_id='synthetic-S1', condition='S1', worker='gw0', pid=1,
                     t_start=e['monotonic_start']+11, t_end=e['monotonic_end']+11, outcome='ok', extra={})
            if e['event'] == 'helper':
                e['extra'] = {'key': ['AI-Agent: none', False, True, False]}
            fixture_events.append(e)
        fixture_events.append(dict(fixture_events[0], event='collection', nodeid='', span_id='collection',
            parent_span_id=None, extra={'executed_selected': [p.C_NODE], 'units': []}))
        (fixture / 'spans-gw0-1.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in fixture_events))
        analyzed = a.analyze_run(fixture)
        check('synthetic run artifacts integrate', not analyzed['excluded'] and
              [analyzed[k] for k in ('W', 'O', 'F', 'L', 'P', 'D')] == [52, 32, 20, 32, 0, 32])
        check('synthetic longest node worker and three layers', analyzed['longest_on_busy'] is True and
              [analyzed['fixed_layers'][k] for k in ('session_to_first_test', 'execution_interval', 'last_test_to_sessionfinish',
               'outer_minus_junit')] == [10, 32, 10, 2])
        summaries, pairs = a.summaries([analyzed])
        check('synthetic node verify summary', summaries['S1']['nodes'][p.C_NODE]['verify_5']['median'] == 2)
        # Exercise real installation on a synthetic module object. No held
        # module import, real filesystem copy, flock or pytest session occurs.
        installed = p.Recorder(tmp, 'S', 'installation', 'gw1')
        copy_calls, flock_calls = [], []
        fake_shutil = NS()
        def copytree(src, dst, **kwargs):
            copy_calls.append((src, dst, kwargs))
            if src == 'base':
                fake_shutil.copytree('recursive', dst)
            return marker
        fake_shutil.copytree = copytree
        fake_fcntl = NS(LOCK_EX=2, LOCK_NB=4, LOCK_SH=1, LOCK_UN=8,
                       flock=lambda *a: flock_calls.append(a))
        fake_migration = NS(verify_receipt=original)
        module = NS(__file__=str(Path.cwd() / p.TEST_FILE), shutil=fake_shutil,
                    fcntl=fake_fcntl, migration=fake_migration, _T080_SHARED_BASES=None)
        def build(path, **kwargs):
            fake_shutil.copytree('builder', 'destination')
            return marker
        class Bases:
            parent = Path(tmp)
            def get(self, key):
                fake_fcntl.flock(7, fake_fcntl.LOCK_EX)
                fake_fcntl.flock(7, fake_fcntl.LOCK_SH)
                fake_fcntl.flock(7, fake_fcntl.LOCK_EX | fake_fcntl.LOCK_NB)
                fake_fcntl.flock(7, fake_fcntl.LOCK_UN)
                module._build_t080_stub_free_e2e_repo(self.parent)
                return marker
            def close(self):
                return marker
        bases = Bases()
        original_get = Bases.get
        def _t080_stub_free_e2e_repo(tmp_path, **kwargs):
            bases.get(('key',))
            fake_shutil.copytree('base', 'destination', symlinks=True)
            return marker
        module._T080SharedBases = Bases
        module._build_t080_stub_free_e2e_repo = build
        module._t080_stub_free_e2e_repo = _t080_stub_free_e2e_repo
        item = NS(nodeid=p.C_NODE, module=module)
        p.install(installed, item)
        check('installed helper identity', module._t080_stub_free_e2e_repo(Path(tmp)) is marker)
        ev = installed.events
        copy_events = [e for e in ev if e['event'] == 'copytree_top']
        flock_events = [e for e in ev if e['event'] == 'flock_ex']
        check('copy direct only; recursion and build pass through', len(copy_events) == 1 and
              installed.passages['copytree_top'] == 3 and len(copy_calls) == 3)
        check('flock only blocking EX; one delegation each', len(flock_events) == 1 and
              installed.passages['flock_ex'] == 4 and len(flock_calls) == 4)
        byid = {e['span_id']: e for e in ev}
        check('installed helper/get/build span tree', byid[copy_events[0]['parent_span_id']]['event'] == 'helper' and
              byid[flock_events[0]['parent_span_id']]['event'] == 'get')
        p._REC = installed
        protocol = p.pytest_runtest_protocol(item, None)
        next(protocol)
        try:
            protocol.throw(RuntimeError('synthetic setup failure'))
        except RuntimeError:
            pass
        check('setup failure protocol restores originals', module._t080_stub_free_e2e_repo is _t080_stub_free_e2e_repo and
              Bases.get is original_get and fake_shutil.copytree is copytree and fake_migration.verify_receipt is original)
        check('close delegates identity', bases.close() is marker)
        close_events = [json.loads(line) for line in installed.path.read_text().splitlines()]
        check('close recorded in session', any(e['event'] == 'close' and e['phase'] == 'session' for e in close_events))
        p._REC = None
        check('held module never imported', not any(n.endswith('test_s8b_oracle_driver') for n in sys.modules))
    for name, ok in checks:
        print(('PASS ' if ok else 'FAIL ') + name)
    print(f'{sum(ok for _, ok in checks)}/{len(checks)} passed')
    return 0 if all(ok for _, ok in checks) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    run_parser = sub.add_parser('run')
    for key in ('repo-root', 'probe-dir', 'out-root', 'conditions'):
        run_parser.add_argument('--' + key, required=True)
    run_parser.add_argument('--job-tag')
    run_parser.add_argument('--require-hostname-prefix', default='bnode')
    test_parser = sub.add_parser('selftest')
    test_parser.add_argument('--probe-dir', required=True)
    args = parser.parse_args()
    return selftest(args) if args.mode == 'selftest' else run(args)


if __name__ == '__main__':
    raise SystemExit(main())

```

## t2710_probe_analyze.py

```python
"""Analyze diagnostic replicas, never promote them to acceptance evidence."""
import argparse
import collections
import json
import math
from pathlib import Path
import re
import statistics
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
from t2710_probe_plugin import M, C_NODE, PARAMS, SINGLE, TEST_FILE, FIELDS
from t2710_probe_plugin import canonical, scope, aggregate_reports, write_json


def read_json(path):
    return json.loads(Path(path).read_text())


def union_length(intervals):
    end, total = None, 0.0
    for lo, hi in sorted(intervals):
        if hi < lo:
            raise ValueError('reversed interval')
        total += hi - lo if end is None or lo >= end else max(0, hi - end)
        end = hi if end is None else max(end, hi)
    return total


def interval(e):
    return e['monotonic_start'], e['monotonic_end']


def elapsed(events, event):
    return union_length([interval(e) for e in events if e['event'] == event])


def descendants(events, parent, names):
    byid = {e['span_id']: e for e in events}
    found = []
    for e in events:
        if e['event'] not in names:
            continue
        ancestor = e.get('parent_span_id')
        seen = set()
        while ancestor is not None and ancestor not in seen:
            if ancestor == parent['span_id']:
                found.append(e)
                break
            seen.add(ancestor)
            ancestor = byid.get(ancestor, {}).get('parent_span_id')
    return found


def residual(events, parent_event, children):
    result = 0.0
    for parent in events:
        if parent['event'] == parent_event:
            lo, hi = interval(parent)
            occupied = [(max(lo, e['monotonic_start']), min(hi, e['monotonic_end']))
                        for e in descendants(events, parent, children)]
            occupied = [(a, b) for a, b in occupied if b >= a]
            result += hi - lo - union_length(occupied)
    return result


def summarize_values(values):
    return {'values': values, 'median': statistics.median(values) if values else None, 'n': len(values)}


def wall_model(longest, total, fixed):
    return max(longest, total / 48) + fixed


def junit_data(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else list(root.findall('testsuite'))
    if len(suites) != 1:
        raise ValueError('expected one pytest JUnit testsuite')
    cases = []
    for c in suites[0].iter('testcase'):
        nodeid = c.attrib.get('classname', '').replace('.', '/') + '.py::' + c.attrib['name']
        cases.append({'nodeid': nodeid, 'name': c.attrib['name'], 'time': float(c.attrib.get('time', 0)),
                      'failed': c.find('failure') is not None or c.find('error') is not None,
                      'skipped': c.find('skipped') is not None})
    return float(suites[0].attrib['time']), cases


def shard_metrics(controller, junit, condition, production=None):
    workers = aggregate_reports(controller['reports'])
    if workers != controller['workers']:
        raise ValueError('controller phase aggregation mismatch')
    busy = max(workers, key=lambda w: workers[w]['duration'])
    W, cases = junit_data(junit)
    longest_case = max(cases, key=lambda n: n['time'])
    L, O = longest_case['time'], workers[busy]['duration']
    D = sum(w['duration'] for w in workers.values())
    allnodes = [dict(n, worker=w) for w, data in workers.items() for n in data['items']]
    matches = [n for n in allnodes if canonical(n['nodeid']) == longest_case['nodeid']]
    # Names uniquely identify these function tests; fallback supports synthetic JUnit.
    if not matches:
        matches = [n for n in allnodes if canonical(n['nodeid']).split('::')[-1] == longest_case['name']]
    longest_worker = matches[0]['worker'] if len(matches) == 1 else None
    r = dict(W=W, O=O, F=W-O, L=L, P=O-L, D=D,
             mean_load=D / {'S1': 1, 'S': 11}.get(condition, 48),
             longest_node=longest_case['nodeid'], longest_worker=longest_worker,
             longest_on_busy=longest_worker == busy if longest_worker else None,
             busy_worker=busy, busy_items=workers[busy]['items'], busy_count=workers[busy]['count'],
             workers=workers, allnodes=allnodes, cases=cases)
    if production:
        prod_o = max((v['duration_s'] for k, v in production['worker_occupancy'].items()
                      if k != 'unobserved'), default=0.0)
        r.update(O_production=prod_o, O_difference=O-prod_o,
                 production_unobserved=production['worker_occupancy'].get('unobserved'))
    return r


def node_metrics(nodeid, reports, events):
    reports = [r for r in reports if canonical(r['nodeid']) == nodeid]
    events = [e for e in events if canonical(e['nodeid']) == nodeid]
    phases = {when: sum(r['duration'] for r in reports if r['when'] == when)
              for when in ('setup', 'call', 'teardown')}
    helper = [e for e in events if e['event'] == 'helper']
    verify = sorted([e for e in events if e['event'] == 'verify'], key=lambda e: e['call_index'])
    # Restrict the call subtraction to descendants of the observed call; setup
    # helpers/verifiers are reported but must not be subtracted from call.
    call_children = [e for c in events if c['event'] == 'call'
                     for e in descendants(events, c, {'helper', 'verify'})]
    row = dict(nodeid=nodeid, worker=reports[0]['worker'] if reports else None,
               base_key=helper[0]['extra'].get('key') if helper else None,
               status='observed' if reports else 'not executed', **phases)
    row.update({name: elapsed(events, name) for name in ('helper', 'get', 'flock_ex', 'build', 'copytree_top')})
    row.update(get_other=residual(events, 'get', {'flock_ex', 'build'}),
               helper_other=residual(events, 'helper', {'get', 'copytree_top'}),
               call_other=phases['call'] - union_length([interval(e) for e in call_children]),
               verify=[e['monotonic_end']-e['monotonic_start'] for e in verify],
               helper_count=len(helper), verify_count=len(verify))
    row.update({f'verify_{i+1}': v for i, v in enumerate(row['verify'])})
    return row


def models(metrics, nodes, events):
    durations = {canonical(n['nodeid']): n['duration'] for n in metrics['allnodes']}
    F, D = metrics['F'], metrics['D']
    baseline = wall_model(metrics['L'], D, F)
    result = {'A_model': baseline, 'A_residual': metrics['W']-baseline,
              'assumptions': 'Fixed durations and F_A; lower-bound model, not implementation effect. '
              'Independent split loses same-root positive-to-mutation continuity; duplicated observed helper/setup/teardown. '
              'Build executed once in reality; both waits may recur. Session cleanup change is unmodeled.'}
    removed = {TEST_FILE + '::' + SINGLE + '[' + p + ']' for p in (PARAMS[0], PARAMS[1], PARAMS[3])}
    remaining = [v for k, v in durations.items() if k not in removed]
    if remaining and removed <= durations.keys():
        lr, dr = max(remaining), D-sum(durations[n] for n in removed)
        result.update(L_reduce=lr, D_reduce=dr, reduce_model=wall_model(lr, dr, F))
        result['reduce_gain_model'] = baseline-result['reduce_model']
    node = next((n for n in nodes if n['nodeid'] == C_NODE), None)
    ev = [e for e in events if canonical(e['nodeid']) == C_NODE and e['phase'] == 'call']
    calls = [e for e in ev if e['event'] == 'call']
    helper = [e for e in ev if e['event'] == 'helper']
    verifies = sorted([e for e in ev if e['event'] == 'verify' and e.get('parent_span_id') in
                       {c['span_id'] for c in calls}], key=lambda e: e['call_index'])
    if node and C_NODE in durations and len(verifies) == 5 and len(calls) == 1 and len(helper) == 1:
        # Cut immediately after V2. Uninstrumented work before/after that cut
        # stays on its respective side; mutation cannot be independently timed.
        call_lo, call_hi = interval(calls[0])
        cut = verifies[1]['monotonic_end']
        occupied = [interval(e) for e in helper + verifies]
        other_p = cut-call_lo-union_length([(max(call_lo, x), min(cut, y)) for x, y in occupied if x < cut and y > call_lo])
        other_d = call_hi-cut-union_length([(max(cut, x), min(call_hi, y)) for x, y in occupied if x < call_hi and y > cut])
        common = node['setup'] + node['helper'] + node['teardown']
        vs = [e['monotonic_end']-e['monotonic_start'] for e in verifies]
        # Pytest call duration minus our call-hook interval is an unseparated
        # hook-boundary residual, charged once to defect rather than discarded.
        boundary = node['call']-(call_hi-call_lo)
        positive = common + sum(vs[:2]) + other_p
        defect = common + sum(vs[2:]) + other_d + boundary
        ls = max([positive, defect] + [v for k, v in durations.items() if k != C_NODE])
        ds = D-durations[C_NODE]+positive+defect
        result.update(d_positive=positive, d_defect=defect, positive_other=other_p,
                      mutation_plus_defect_other=other_d, call_boundary_other=boundary,
                      L_split=ls, D_split=ds, split_model=wall_model(ls, ds, F))
        result['split_gain_model'] = baseline-result['split_model']
    else:
        result['split_unavailable'] = 'requires exactly five direct call verifiers, one helper and one call span'
    return result


def history_rows(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 8 and re.fullmatch(r'\d\d-\d\d \d\d:\d\d', cells[0]):
            rows.append(dict(zip(('W', 'O', 'F', 'L'), map(float, cells[2:6]))))
    if not rows:
        raise ValueError('history table not found')
    return rows


def history_compare(runs, history):
    result = {'I': bool(runs), 'n_history': len(history), 'n_A': len(runs), 'metrics': {},
              'note': 'Descriptive inclusion, not equivalence; history rounded to 0.1 seconds.'}
    for key in ('W', 'O', 'F', 'L'):
        hs, values = [r[key] for r in history], [r[key] for r in runs]
        inside = [min(hs) <= value <= max(hs) for value in values]
        result['I'] &= all(inside)
        result['metrics'][key] = {'inside': inside, 'range': [min(hs), max(hs)],
            'percentiles': [(sum(h < v for h in hs) + 0.5*sum(h == v for h in hs))/len(hs) for v in values],
            'percentiles_percent': [100*(sum(h < v for h in hs) + 0.5*sum(h == v for h in hs))/len(hs) for v in values],
            'median_ratio': statistics.median(values)/statistics.median(hs) if values else None}
    return result


def distribution(controller, metrics, events):
    worker = metrics['longest_worker']
    items = metrics['workers'].get(worker, {}).get('items', [])
    costs = {}
    initial = {}
    for e in events:
        if e['event'] == 'collection':
            costs.update({u['scope']: u['cost'] for u in e['extra']['units']})
            costs.update(e['extra'].get('unit_costs', {}))
            initial.update(e['extra'].get('initial_pairs', {}))
    for entry in controller['collections'].values():
        costs.update({u['scope']: u['cost'] for u in entry.get('intended_units', [])})
    units = {}
    for n in items:
        key = scope(n['nodeid'])
        u = units.setdefault(key, {'scope': key, 'cost': costs.get(key), 'items': [], 'duration': 0.0})
        u['items'].append(n['nodeid'])
        u['duration'] += n['duration']
    seq = list(units.values())
    predicted_second = initial.get(seq[0]['scope']) if seq else None
    return {'worker': worker, 'units': seq, 'second': seq[1] if len(seq) > 1 else None,
            'initial_second_predicted': predicted_second,
            'initial_second_observed_matches': (seq[1]['scope'] == predicted_second['scope'])
                if predicted_second and len(seq) > 1 else None,
            'third_or_later': len(seq) > 2,
            'collection_matches': {w: c.get('intended_matches') for w, c in controller['collections'].items()},
            'initial_second_inference': 'Prediction uses scheduler pending <=2 rule; execution sequence is observed, enqueue timestamps are not.'}


def analyze_run(path):
    run = read_json(path / 'run.json')
    row = {'path': str(path), 'run': run.get('run_id', path.name), 'condition': run['condition'],
           'job': run.get('job_tag', path.parent.name), 'ordinal': run['ordinal'],
           'host': run['hostname'], 'outer_wall': run.get('outer_wall'), 'rc': run.get('rc'),
           'excluded': list(run.get('errors', []))}
    if run.get('rc') != 0:
        row['excluded'].append('rc != 0')
    try:
        controller = read_json(path / 'controller.json')
        if controller.get('exitstatus', 0) != 0:
            row['excluded'].append('controller exitstatus != 0')
        junit = path / 'junit.xml'
        production = None
        if run['condition'] in ('A', 'B', 'C'):
            junit = path / 'acceptance-session/shard-0/junit.xml'
            production = read_json(path / 'acceptance-session/shard-0/report.json')
        events = [json.loads(line) for file in sorted(path.glob('spans-*.jsonl'))
                  for line in file.read_text().splitlines() if line]
        if not events:
            row['excluded'].append('no worker events')
        if list(path.glob('record-error-*.json')) or any(e.get('outcome') == 'record-error' for e in events):
            row['excluded'].append('record-error')
        ids = {e['span_id'] for e in events}
        for e in events:
            if not FIELDS <= e.keys() or not isinstance(e['extra'], dict):
                raise ValueError('invalid span schema')
            if any(not math.isfinite(e[k]) for k in ('t_start', 't_end', 'monotonic_start', 'monotonic_end')):
                raise ValueError('nonfinite span time')
            if e['t_end'] < e['t_start'] or e['monotonic_end'] < e['monotonic_start']:
                raise ValueError('reversed span')
            if e['parent_span_id'] is not None and e['parent_span_id'] not in ids:
                raise ValueError('orphan span')
        metrics = shard_metrics(controller, junit, run['condition'], production)
        row.update({k: v for k, v in metrics.items() if k not in ('allnodes', 'cases', 'workers')})
        collected = [e['extra']['executed_selected'] for e in events if e['event'] == 'collection']
        finished = {canonical(r['nodeid']) for r in controller['reports'] if r['when'] == 'teardown'}
        expected = {canonical(n) for n in collected[0]} if collected else set()
        if not expected or any({canonical(n) for n in ids} != expected for ids in collected) or finished != expected:
            row['excluded'].append('incomplete or inconsistent execution collection')
        if len(metrics['cases']) != len(finished):
            row['excluded'].append('JUnit testcase count differs from finished nodes')
        if production:
            allocated = set(production['selected'])
            prod_finished = set(production['finished'])
            expected_allocated = expected | ({C_NODE} if run['condition'] == 'C' else set())
            if allocated != expected_allocated or prod_finished != finished:
                row['excluded'].append('production selected/finished differs from diagnostic condition')
            if production.get('pytest_rc') != 0:
                row['excluded'].append('production report rc != 0')
        failed = {canonical(r['nodeid']) for r in controller['reports'] if r['outcome'] == 'failed'}
        skipped = {canonical(r['nodeid']) for r in controller['reports'] if r['outcome'] == 'skipped'}
        row['terminal'] = {'selected': len(production['selected']) if production else len(expected),
            'executed_selected': len(expected), 'finished': len(finished), 'failed': len(failed),
            'skipped': len(skipped), 'rc': run.get('rc')}
        if failed:
            row['excluded'].append('failed phase')
        row['nodes'] = [node_metrics(n, controller['reports'], events) for n in M]
        missing_helpers = [n['nodeid'] for n in row['nodes'] if n['nodeid'] in expected and not n['helper_count']]
        if missing_helpers:
            row['excluded'].append('missing M helper instrumentation: ' + ', '.join(missing_helpers))
        row['distribution'] = distribution(controller, metrics, events)
        if run['condition'] == 'B' and (not controller['collections'] or
                not all(c.get('intended_matches') is True for c in controller['collections'].values())):
            row['excluded'].append('B received collection mismatch')
        reports = controller['reports']
        first, last = min(r['start'] for r in reports), max(r['stop'] for r in reports)
        row['fixed_layers'] = {'session_to_first_test': first-controller['session_start'],
            'execution_interval': last-first, 'last_test_to_sessionfinish': controller['session_finish']-last,
            'outer_minus_junit': row['outer_wall']-row['W'],
            'execution_minus_occupancy': last-first-row['O'],
            'close_spans': [e for e in events if e['event'] == 'close'],
            'worker_session_events': [e for e in events if e['event'] == 'session'],
            'unseparated': 'worker start/collection/prewarm; shutdown/JUnit; post-session cleanup'}
        bench_path = path.parent / 'microbench.json'
        if bench_path.exists():
            bench = read_json(bench_path)
            overhead = collections.defaultdict(float)
            for e in events:
                if e['event'] == 'overhead':
                    x = e['extra']
                    overhead[e['worker']] += x['passages']*bench['clock_unit'] + x['recorded']*bench['record_unit'] + x['write_seconds']
            row['overhead'] = {'worker_H_proxy': dict(overhead),
                'busy_worker_H_proxy': overhead[metrics['busy_worker']],
                'controller_report_seconds': controller['overhead']['report_seconds'],
                'controller_H_proxy': controller['overhead']['report_count']*bench['record_unit'],
                'note': 'Sensitivity proxy, excludes unmeasured predicate and indirect I/O cost; no proven upper bound.'}
        if run['condition'] == 'A':
            row['models'] = models(metrics, row['nodes'], events)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        row['excluded'].append(repr(exc))
    return row


def summaries(rows):
    valid = [r for r in rows if not r['excluded']]
    result = {}
    keys = ('W', 'O', 'F', 'L', 'P', 'D', 'mean_load', 'outer_wall')
    for condition in ('S1', 'S', 'A', 'B', 'C'):
        group = [r for r in valid if r['condition'] == condition]
        result[condition] = {key: summarize_values([r[key] for r in group]) for key in keys}
        result[condition]['replication_complete'] = len(group) == 3
        result[condition]['nodes'] = {}
        for nodeid in M:
            observed = [x for r in group for x in r.get('nodes', [])
                        if x['nodeid'] == nodeid and x['status'] == 'observed']
            node_keys = ['setup', 'call', 'teardown', 'helper', 'get', 'flock_ex', 'build',
                         'get_other', 'copytree_top', 'helper_other', 'call_other']
            node_keys += [f'verify_{i+1}' for i in range(max((x['verify_count'] for x in observed), default=0))]
            result[condition]['nodes'][nodeid] = {k: summarize_values([x[k] for x in observed if k in x]) for k in node_keys}
        result[condition]['fixed_layers'] = {k: summarize_values([r['fixed_layers'][k] for r in group]) for k in
            ('session_to_first_test', 'execution_interval', 'last_test_to_sessionfinish', 'outer_minus_junit', 'execution_minus_occupancy')}
        model_keys = sorted({k for r in group for k, v in r.get('models', {}).items() if isinstance(v, (int, float))})
        result[condition]['models'] = {k: summarize_values([r['models'][k] for r in group if k in r.get('models', {})]) for k in model_keys}
    pairs = {}
    for condition in ('B', 'C'):
        values = []
        for job in sorted({r['job'] for r in valid}):
            aa = [r for r in valid if r['job'] == job and r['condition'] == 'A']
            xx = [r for r in valid if r['job'] == job and r['condition'] == condition]
            if len(aa) == len(xx) == 1:
                a, x = aa[0], xx[0]
                delta = a['W']-x['W']
                pair = {'job': job, 'A_minus_' + condition: delta, 'rate': delta/a['W'], 'rate_percent': 100*delta/a['W'],
                    'busy_worker_changed': a['busy_worker'] != x['busy_worker'],
                    'worker_label_note': 'gw labels are local to each run; label change alone is not a bottleneck shift',
                    'longest_node_changed': a['longest_node'] != x['longest_node'],
                    'A_second': a['distribution']['second'], 'X_second': x['distribution']['second']}
                if condition == 'B':
                    pair['pair_model_using_observed_B_occupancy_and_F_A'] = x['O'] + a['F']
                    pair['pair_model_note'] = 'Includes all B workers and later units; uses B durations, not a fixed-A counterfactual.'
                values.append(pair)
        ds = [v['A_minus_' + condition] for v in values]
        ma, mx = result['A']['W']['median'], result[condition]['W']['median']
        pairs[condition] = {'pairs': values, **summarize_values(ds),
            'difference_of_medians': ma-mx if ma is not None and mx is not None else None,
            'interpretation': '方向が一致した観測差（有意差判定ではない）' if len(ds) == 3 and all(d > 0 for d in ds)
                              else '採用効果は未確立',
            'scope': 'replica; C is diagnostic, not an upper bound; single-run 10% rule is not a median rule'}
    return result, pairs


def display(value):
    if value is None:
        return '—'
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f'{value:.1f}'
    if isinstance(value, (dict, list)):
        return json.dumps(round_numbers(value), ensure_ascii=False).replace('|', '\\|')
    return str(value).replace('|', '\\|').replace('\n', ' ')


def round_numbers(obj):
    if isinstance(obj, float):
        return round(obj, 1)
    if isinstance(obj, dict):
        return {k: round_numbers(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_numbers(v) for v in obj]
    return obj


def table(columns, rows):
    return ['| ' + ' | '.join(columns) + ' |', '|' + '|'.join('---' for _ in columns) + '|'] + [
        '| ' + ' | '.join(display(row.get(k)) for k in columns) + ' |' for row in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', required=True)
    parser.add_argument('--history', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    paths = sorted({p.parent.resolve() for root in args.runs for p in Path(root).rglob('run.json')})
    rows = [analyze_run(path) for path in paths]
    summary, pairs = summaries(rows)
    history = history_compare([r for r in rows if not r['excluded'] and r['condition'] == 'A'], history_rows(args.history))
    result = {'runs': rows, 'conditions': summary, 'paired_differences': pairs, 'history': history,
              'scope': 'replica shard-0 の同一 tip 反復。受入証跡ではない。model は下限参考値。'}
    lines = ['## 対象と定義', '', result['scope'], '',
             f'走数 {len(rows)}、採用 {sum(not r["excluded"] for r in rows)}。中央値は各走を分解した後、指標別に計算。', '',
             'W=JUnit testsuite、L=JUnit testcase 最大、O=phase 合算最大、F=W−O、P=O−L、D=全 phase 合算。', '',
             '## shard 表', '']
    columns = ['condition', 'run', 'host', 'ordinal', 'W', 'O', 'O_production', 'O_difference', 'F', 'L',
               'longest_node', 'P', 'longest_on_busy', 'D', 'mean_load', 'busy_worker', 'busy_count', 'terminal', 'outer_wall', 'status']
    lines += table(columns, [dict(r, status='除外 (' + '; '.join(r['excluded']) + ')' if r['excluded'] else '採用') for r in rows])
    for r in rows:
        lines += ['', '## ' + r['run'], '']
        if r['excluded']:
            lines += ['除外 (' + '; '.join(r['excluded']) + ')']
            continue
        lines += ['最忙 worker の item 列（start 順）', '']
        lines += table(['nodeid', 'duration', 'start'], r['busy_items'])
        lines += ['', 'M node 成分（実行していない node は not executed）', '']
        columns = ['nodeid', 'worker', 'status', 'base_key', 'setup', 'call', 'teardown', 'helper', 'get', 'flock_ex',
                   'build', 'get_other', 'copytree_top', 'verify', 'helper_other', 'call_other', 'helper_count', 'verify_count']
        lines += table(columns, r.get('nodes', []))
        for label, key in [('配布確認', 'distribution'), ('固定費 3 層・close（未分離項を含む）', 'fixed_layers'),
                           ('観測 overhead 感度', 'overhead'), ('model', 'models')]:
            if key in r:
                lines += ['', label, ''] + table(['metric', 'value'], [{'metric': k, 'value': v} for k, v in r[key].items()])
    lines += ['', '## 条件別中央値と全走の値', '']
    for condition, metrics in summary.items():
        lines += [condition, ''] + table(['metric', 'values', 'median', 'n'],
            [dict(metric=k, **v) for k, v in metrics.items() if isinstance(v, dict) and 'values' in v]) + ['']
        lines += ['M 成分の中央値と全値（各 node/指標を個別集計）', '']
        lines += table(['nodeid', 'metric', 'values', 'median', 'n'],
            [dict(nodeid=n, metric=k, **v) for n, mm in metrics['nodes'].items() for k, v in mm.items()])
        lines += [''] + table(['metric', 'values', 'median', 'n'], [dict(metric=k, **v) for k, v in metrics['models'].items()]) + ['']
        lines += table(['metric', 'values', 'median', 'n'], [dict(metric=k, **v) for k, v in metrics['fixed_layers'].items()]) + ['']
    lines += ['## job 内の対差', '']
    for condition, values in pairs.items():
        lines += ['A−' + condition, ''] + table(['metric', 'value'], [{'metric': k, 'value': v} for k, v in values.items()]) + ['']
    lines += ['## 歴史照合', ''] + table(['metric', 'value'], [{'metric': k, 'value': v} for k, v in history.items()])
    lines += ['', '## 総括', '', '失敗・未完走・記録失敗は除外。3/3 の同符号は有意差ではない。'
              '分割は連続検査、縮約は 3 欠陥型の検出を失う案。実装効果・他 shard への利益は未測定。']
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'analysis.json', result)
    (out / 'analysis.md').write_text('\n'.join(lines) + '\n')
    print(f'{len(rows)} runs; {sum(not r["excluded"] for r in rows)} included; {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

```
