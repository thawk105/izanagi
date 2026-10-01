# 駆動 loop の逐語 (本走で使った版)

repo の外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/contrast_runner.py` の bytes を写したもの (Codex author、branch `t2867-run-fix2-x`)。
SHA-256: `d12eb6cd32bdb14a22abafb47d9ac112a5e2f3f588ff3d7dafd16b44f31b12f2`。実行は `python3 -B contrast_runner.py run --config <config.json>`。

```python
#!/usr/bin/env python3
"""Login-side scheduler for silo policy contrast series (Python 3.10)."""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

ARMS = {'llm-cpp', 'llm-ir', 'random-ir', 'evo-ir', 'reference'}
CONFIG_KEYS = {'schema', 'root', 'archive_root', 'cohort', 'version', 'pin', 'model',
               'settings', 'expected_head', 'checkouts', 'walltime_s', 'schedule',
               'max_active_series', 'max_llm_parents', 'poll_s'}
WALL_KEYS = {'job1', 'eval', 'score', 'reference'}
LAUNCH = 'tools/pegasus/silo_policy_contrast_launch.py'
PARENT = 'tools/pegasus/silo_policy_contrast_parent.py'
LEDGER = 'orchestrator/campaign/silo_policy_contrast.py'
REQUEST = re.compile(r'(\d+\.nqsv)')
QSTAT_ROW = re.compile(r'^\s*(\d+\.nqsv)\b')
STOP = False


def now():
    return datetime.now(timezone.utc).isoformat()


def positive_int(value):
    return type(value) is int and value > 0


def config_read(path):
    c = json.loads(Path(path).read_text())
    if not isinstance(c, dict) or set(c) != CONFIG_KEYS or c['schema'] != 't2867-contrast-runner-config/v1':
        raise ValueError('invalid config schema or keys')
    for key in ('root', 'archive_root', 'settings'):
        if not isinstance(c[key], str) or not Path(c[key]).is_absolute():
            raise ValueError(f'{key} must be an absolute path')
    for key in ('cohort', 'version', 'pin', 'model'):
        if not isinstance(c[key], str) or not c[key]:
            raise ValueError(f'{key} must be nonempty text')
    if not isinstance(c['expected_head'], str) or not re.fullmatch(r'[0-9a-fA-F]{40}', c['expected_head']):
        raise ValueError('expected_head must be 40 hex digits')
    if not Path(c['settings']).is_file():
        raise ValueError('settings file missing')
    if not isinstance(c['checkouts'], list) or not c['checkouts'] or len(set(c['checkouts'])) != len(c['checkouts']):
        raise ValueError('checkouts must be distinct and nonempty')
    for checkout in c['checkouts']:
        if not isinstance(checkout, str) or not Path(checkout).is_absolute() or not Path(checkout).is_dir():
            raise ValueError('checkout missing or not absolute')
        for args, expected in ((['rev-parse', 'HEAD'], c['expected_head']),
                               (['status', '--porcelain', '--untracked-files=no'], '')):
            result = subprocess.run(['git', '-C', checkout, *args], text=True, capture_output=True)
            if result.returncode or result.stdout.strip() != expected:
                raise ValueError(f'checkout HEAD or tracked status mismatch: {checkout}')
    if not isinstance(c['walltime_s'], dict) or set(c['walltime_s']) != WALL_KEYS or not all(positive_int(x) for x in c['walltime_s'].values()):
        raise ValueError('invalid walltime_s')
    if not isinstance(c['schedule'], list) or not c['schedule']:
        raise ValueError('empty schedule')
    seen = set()
    for item in c['schedule']:
        if not isinstance(item, dict) or set(item) != {'arm', 'series'} or item['arm'] not in ARMS or not positive_int(item['series']):
            raise ValueError('invalid schedule item')
        key = item['arm'], item['series']
        if key in seen:
            raise ValueError('duplicate schedule item')
        seen.add(key)
    for key in ('max_active_series', 'max_llm_parents', 'poll_s'):
        if not positive_int(c[key]):
            raise ValueError(f'invalid {key}')
    if any(key in os.environ for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN',
            'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX')):
        raise ValueError('metered provider environment present')
    return c


def atomic_json(path, value):
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix='.runner-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def append_json(path, value):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def parent_alive(pid):
    try:
        return alive(pid) and PARENT.encode() in Path(f'/proc/{pid}/cmdline').read_bytes()
    except OSError:
        return False


def tail(value):
    return value[-2048:] if isinstance(value, str) else ''


class Runner:
    def __init__(self, config):
        self.c = config
        self.root = Path(config['root'])
        self.rs = self.root / 'runner-state'
        self.rs.mkdir(parents=True, exist_ok=True)
        self.state_path = self.rs / 'state.json'
        self.actions = self.rs / 'actions.jsonl'
        self.attentions = self.rs / 'attention.jsonl'
        self.done = self.rs / 'done.json'
        self.processes = {}
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())
            expected = [self.name(x) for x in config['schedule']]
            if len(expected) != len(set(expected)) or set(self.state['series']) != set(expected):
                raise ValueError('state schedule differs from config')
        else:
            self.state = {'series': {self.name(x): {'checkout': None, 'job': None,
                'parent': None, 'attention': None, 'end': None, 'intent': None,
                'job_missing': 0} for x in config['schedule']}}
        for name, item in self.state['series'].items():
            item.setdefault('intent', None)
            item.setdefault('job_missing', 0)
            if item['job']:
                item.setdefault('job_submitted', time.time())
            if item['parent']:
                item['parent'].setdefault('starting', False)
        self.persist()
        for name, item in self.state['series'].items():
            if not item['attention'] and item['parent'] and item['parent']['starting']:
                parent = item['parent']
                item['parent'] = None
                self.attention(name, 'parent-start-unknown', f"a={parent['a']}; log={parent['log']}")
            elif not item['attention'] and item['intent']:
                self.attention(name, 'intent-unknown', str(item['intent']))

    @staticmethod
    def name(item):
        return f"{item['arm']}-{item['series']}"

    def persist(self):
        atomic_json(self.state_path, self.state)

    def record(self, name, action, argv=None, rc=None, request_id=None, a=None,
               outcome=None, stdout='', stderr=''):
        append_json(self.actions, {'ts': now(), 'name': name, 'action': action,
            'argv': argv, 'rc': rc, 'request_id': request_id, 'a': a,
            'outcome': outcome, 'stdout_tail': tail(stdout), 'stderr_tail': tail(stderr)})

    def attention(self, name, kind, detail):
        self.state['series'][name]['attention'] = {'kind': kind, 'detail': detail}
        append_json(self.attentions, {'ts': now(), 'name': name, 'kind': kind, 'detail': detail})
        self.persist()

    def command(self, name, action, argv, checkout, timeout=None):
        try:
            result = subprocess.run(argv, cwd=checkout, text=True, capture_output=True, timeout=timeout)
            rc, stdout, stderr = result.returncode, result.stdout, result.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            rc, stdout, stderr = 2, '', str(exc)
        self.record(name, action, argv, rc,
                    request_id=(REQUEST.search(stdout).group(1) if action == 'submit' and REQUEST.search(stdout) else None),
                    stdout=stdout, stderr=stderr)
        return rc, stdout, stderr

    def qstat(self):
        rc, stdout, stderr = self.command('', 'qstat', ['qstat'], self.root)
        if rc or not any('RequestID' in line for line in stdout.splitlines()):
            return None
        return {match.group(1) for line in stdout.splitlines()
                if (match := QSTAT_ROW.match(line))}

    def ledger(self, checkout, path):
        spec = importlib.util.spec_from_file_location('contrast_ledger_readonly', Path(checkout) / LEDGER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, module.ContrastLedger(path)

    def ledger_path(self, name):
        return self.root / 'ledgers' / name

    def round(self):
        global STOP
        running = self.qstat()
        completed_parents = set()
        for name, item in self.state['series'].items():
            if item['job'] and running is not None:
                if item['job'] in running:
                    item['job_missing'] = 0
                    self.persist()
                else:
                    item['job_missing'] += 1
                    if (item['job_missing'] >= 2 and item.get('job_submitted')
                            and time.time() - item['job_submitted'] >= 120):
                        self.record(name, 'job-finished', request_id=item['job'])
                        item['job'] = None
                        item['job_missing'] = 0
                    self.persist()
            parent = item['parent']
            if parent:
                process = self.processes.get(name)
                rc = process.poll() if process else None
                if process and rc is None:
                    continue
                if not process and parent_alive(parent['pid']):
                    continue
                log = Path(parent['log']).read_text(errors='replace') if Path(parent['log']).exists() else ''
                outcome = log.strip().splitlines()[-1] if log.strip() and rc == 0 else None
                self.record(name, 'parent-finished', parent['argv'], rc, a=parent['a'],
                            outcome=outcome, stdout=log)
                item['parent'] = None
                completed_parents.add(name)
                self.processes.pop(name, None)
                self.persist()
                if rc is not None and rc != 0:
                    self.attention(name, 'parent-rc', f'rc={rc}; {tail(log)}')
        paused = (self.rs / 'pause').exists() or STOP
        waiting = deque()
        for entry in self.c['schedule']:
            name = self.name(entry)
            item = self.state['series'][name]
            if (name in completed_parents or not item['checkout'] or item['end']
                    or item['attention'] or item['job'] or item['parent']):
                continue
            checkout = item['checkout']
            ledger_path = self.ledger_path(name)
            argv = ['python3', '-B', LAUNCH, 'status', '--ledger', str(ledger_path)]
            rc, stdout, stderr = self.command(name, 'status', argv, checkout)
            if rc:
                self.attention(name, 'status-rc', f'rc={rc}; {tail(stderr)}')
                continue
            try:
                status = json.loads(stdout)
                module, ledger = self.ledger(checkout, ledger_path)
                ends = [e for e in ledger.events if e['kind'] == 'series-end']
                if ends:
                    item['end'] = ends[-1]['reason']
                    self.persist()
                    continue
                unit = status['next_unit']
                if unit is not None and unit['kind'] not in WALL_KEYS | {'dead-job'}:
                    raise ValueError('unknown next unit kind')
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                self.attention(name, 'status-data', str(exc))
                continue
            if unit and unit['kind'] == 'dead-job':
                self.attention(name, 'dead-job', 'launcher reported dead-job')
            elif paused:
                continue
            elif unit:
                kind = unit['kind']
                argv = ['python3', '-B', LAUNCH, 'submit', '--ledger', str(ledger_path),
                    '--evidence-root', str(self.root / 'evidence' / name),
                    '--archive-root', str(Path(self.c['archive_root']) / name),
                    '--walltime', str(self.c['walltime_s'][kind]), '--submit']
                item['intent'] = {'action': 'submit', 'ts': now()}
                self.persist()
                rc, out, err = self.command(name, 'submit', argv, checkout)
                found = REQUEST.search(out)
                if rc or not found:
                    item['intent'] = None
                    item['attention'] = {'kind': 'submit', 'detail': f'rc={rc}; {tail(out)} {tail(err)}'}
                    self.persist()
                    self.attention(name, 'submit', f'rc={rc}; {tail(out)} {tail(err)}')
                else:
                    item['job'] = found.group(1)
                    item['job_submitted'] = time.time()
                    item['job_missing'] = 0
                    item['intent'] = None
                    self.persist()
            elif entry['arm'] in ('random-ir', 'evo-ir'):
                argv = ['python3', '-B', LAUNCH, 'generate', '--ledger', str(ledger_path)]
                rc, out, err = self.command(name, 'generate', argv, checkout, timeout=900)
                if rc:
                    self.attention(name, 'generate-rc', f'rc={rc}; {tail(err)}')
            elif entry['arm'] in ('llm-cpp', 'llm-ir'):
                waiting.append(name)
            else:
                self.attention(name, 'reference-state', 'no next unit and no series-end')
        if not paused:
            slots = self.c['max_llm_parents'] - sum(bool(x['parent']) for x in self.state['series'].values())
            for name in list(waiting)[:max(0, slots)]:
                self.start_parent(name)
            self.open_series()
        items = list(self.state['series'].values())
        if (all(x['checkout'] and (x['end'] or x['attention']) for x in items)
                and not any(x['job'] or x['parent'] for x in items)):
            atomic_json(self.done, {'ts': now(), 'series': {name: {'end': x['end'],
                'attention': x['attention']} for name, x in self.state['series'].items()}})
            return True
        return False

    def start_parent(self, name):
        item = self.state['series'][name]
        checkout = item['checkout']
        ledger_path = self.ledger_path(name)
        try:
            module, ledger = self.ledger(checkout, ledger_path)
            a = module.open_opportunity(ledger)
            if a is None:
                a = module.next_opportunity(ledger)
        except (OSError, ValueError, KeyError) as exc:
            self.attention(name, 'ledger-read', str(exc))
            return
        directory = self.root / 'rounds' / name
        directory.mkdir(parents=True, exist_ok=True)
        n = 1
        while (directory / f'parent-a{a}-{n}.log').exists():
            n += 1
        log = directory / f'parent-a{a}-{n}.log'
        argv = ['python3', '-B', PARENT, '--ledger', str(ledger_path), '--a', str(a),
                '--out', str(directory / f'a{a}'), '--settings', self.c['settings'],
                '--model', self.c['model'], '--checkout', checkout]
        env = {k: v for k, v in os.environ.items() if not (k.startswith('CLAUDE') or
                k == 'AI_AGENT' or k.startswith('ANTHROPIC_'))}
        item['parent'] = {'pid': None, 'a': a, 'started': now(), 'starting': True,
                          'log': str(log), 'argv': argv}
        self.persist()
        try:
            with log.open('w') as stream:
                process = subprocess.Popen(argv, cwd=checkout, stdout=stream,
                    stderr=subprocess.STDOUT, start_new_session=True, env=env, text=True)
        except OSError as exc:
            item['parent'] = None
            self.persist()
            self.record(name, 'parent-start', argv, 2, a=a, stderr=str(exc))
            self.attention(name, 'parent-start', str(exc))
            return
        self.processes[name] = process
        item['parent']['pid'] = process.pid
        item['parent']['starting'] = False
        self.persist()
        self.record(name, 'parent-start', argv, 0, a=a, stdout=f'pid={process.pid}')

    def open_series(self):
        items = self.state['series']
        for entry in self.c['schedule']:
            name = self.name(entry)
            item = items[name]
            if item['attention'] and not item['checkout']:
                break  # Failed init blocks every later schedule item.
            if item['checkout']:
                continue
            active = sum(bool(x['checkout'] and not x['end'] and not x['attention']) for x in items.values())
            if active >= self.c['max_active_series']:
                break
            used = {x['checkout'] for x in items.values() if x['checkout'] and not x['end']}
            free = next((x for x in self.c['checkouts'] if x not in used), None)
            if free is None:
                break
            if STOP or (self.rs / 'pause').exists():
                break
            ledger = self.ledger_path(name)
            ledger.parent.mkdir(parents=True, exist_ok=True)
            argv = ['python3', '-B', LAUNCH, 'init', '--ledger', str(ledger),
                '--checkout', free, '--cohort', self.c['cohort'], '--arm', entry['arm'],
                '--version', self.c['version'], '--pin', self.c['pin'], '--series', str(entry['series'])]
            item['intent'] = {'action': 'init', 'ts': now()}
            self.persist()
            rc, out, err = self.command(name, 'init', argv, free)
            item['intent'] = None
            if rc:
                item['attention'] = {'kind': 'init-rc', 'detail': f'rc={rc}; {tail(err)}'}
                self.persist()
                self.attention(name, 'init-rc', f'rc={rc}; {tail(err)}')
                break
            item['checkout'] = free
            self.persist()


def status_command(config):
    path = Path(config['root']) / 'runner-state'
    state = json.loads((path / 'state.json').read_text()) if (path / 'state.json').exists() else {'series': {}}
    series = state['series']
    print(json.dumps({'state': state, 'attention_count': sum(bool(x['attention']) for x in series.values()),
        'end_count': sum(bool(x['end']) for x in series.values()),
        'running_jobs': {n: x['job'] for n, x in series.items() if x['job']},
        'running_parents': {n: x['parent'] for n, x in series.items() if x['parent']}},
        ensure_ascii=False, sort_keys=True))


def stop_handler(signum, frame):
    global STOP
    STOP = True


def run(config):
    global STOP
    STOP = False
    state_dir = Path(config['root']) / 'runner-state'
    state_dir.mkdir(parents=True, exist_ok=True)
    pidfile = state_dir / 'runner.pid'
    lock_fd = os.open(state_dir / 'runner.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('runner already running')
        pidfile.write_text(str(os.getpid()) + '\n')
        previous_term = signal.signal(signal.SIGTERM, stop_handler)
        previous_int = signal.signal(signal.SIGINT, stop_handler)
        try:
            runner = Runner(config)
            while not STOP:
                if runner.round():
                    return 0
                if STOP:
                    break
                time.sleep(config['poll_s'])
            runner.persist()
            return 0
        finally:
            signal.signal(signal.SIGTERM, previous_term)
            signal.signal(signal.SIGINT, previous_int)
            pidfile.unlink(missing_ok=True)
    finally:
        os.close(lock_fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('run', 'status'):
        commands.add_parser(command).add_argument('--config', required=True)
    args = parser.parse_args(argv)
    try:
        config = config_read(args.config) if args.command == 'run' else json.loads(Path(args.config).read_text())
        return run(config) if args.command == 'run' else status_command(config)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
```
