# 駆動 loop の自己試験の逐語

repo の外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/runner/test_contrast_runner.py` の bytes を写したもの (Codex author、branch `t2867-run-fix2-x`)。
SHA-256: `39cce9428dd7beb9a6e6e08d2eb882efbea9f6c2284769e2e734ef5b62d94492`。計算ノードで 13/13 OK (request 37799)。

```python
#!/usr/bin/env python3
"""Small process-level tests for the contrast scheduler."""
import importlib.util
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
spec = importlib.util.spec_from_file_location('runner', HERE / 'contrast_runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

LAUNCHER = '''import json, pathlib, subprocess, sys
p = pathlib.Path(sys.argv[sys.argv.index('--ledger')+1]); cmd=sys.argv[1]
name=p.name; control=p.parents[1]/'control.json'
c=json.loads(control.read_text()); mode=c.get(name, 'unit')
with (p.parents[1]/'calls').open('a') as f: f.write(name+' '+cmd+'\\n')
if cmd=='init':
 p.mkdir(parents=True); (p/'events').mkdir()
 arm=sys.argv[sys.argv.index('--arm')+1]
 (p/'header.json').write_text(json.dumps({'schema':'silo-policy-contrast-ledger/v1','arm':arm,'form':'cpp' if arm in ('llm-cpp','reference') else 'ir'}))
 (p/'events'/'000001-series-start.json').write_text(json.dumps({'event_seq':1,'kind':'series-start'}))
elif cmd=='status':
 if mode=='bad': sys.exit(2)
 if mode=='end':
  path=p/'events'/'000002-series-end.json'
  if not path.exists(): path.write_text(json.dumps({'event_seq':2,'kind':'series-end','reason':'b-complete'}))
 print(json.dumps({'next_unit': {'kind':'dead-job'} if mode=='dead' else {'kind':'job1'} if mode=='unit' else None}))
elif cmd=='submit':
 if mode=='submit-fail': sys.exit(2)
 print(subprocess.check_output(['qsub'],text=True).strip())
elif cmd=='generate':
 if mode=='generate-fail': sys.exit(2)
'''
PARENT = '''import os, sys, time
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--ledger')+1]); root=p.parents[1]
(root/'parent-env').write_text(' '.join(k for k in os.environ if k.startswith('CLAUDE') or k.startswith('ANTHROPIC_') or k=='AI_AGENT'))
time.sleep(0.5)
print('empty')
'''


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'work'
        self.root.mkdir()
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self._script('qsub', '#!/bin/sh\necho 101.nqsv\n')
        self._script('qstat', '#!/bin/sh\ncat "$RUNNER_QSTAT"\n')
        self.qstat = self.base / 'qstat.txt'
        self.qstat.write_text('RequestID User\n101.nqsv user\n')
        self.env = patch.dict(os.environ, {'PATH': str(self.bin)+os.pathsep+os.environ['PATH'],
            'RUNNER_QSTAT': str(self.qstat)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.checkout = self.base / 'checkout'
        (self.checkout / 'tools/pegasus').mkdir(parents=True)
        (self.checkout / 'orchestrator/campaign').mkdir(parents=True)
        (self.checkout / runner.LAUNCH).write_text(LAUNCHER)
        (self.checkout / runner.PARENT).write_text(PARENT)
        shutil.copy(REPO / runner.LEDGER, self.checkout / runner.LEDGER)
        subprocess.run(['git', 'init', '-q', str(self.checkout)], check=True)
        subprocess.run(['git', '-C', str(self.checkout), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.checkout), '-c', 'user.name=Test',
            '-c', 'user.email=test@example.com', 'commit', '-qm', 'fake'], check=True)
        self.head = subprocess.check_output(['git', '-C', str(self.checkout), 'rev-parse', 'HEAD'], text=True).strip()
        self.settings = self.base / 'settings.json'
        self.settings.write_text('{}')
        self.control = self.root / 'control.json'
        self.control.write_text('{}')

    def _script(self, name, body):
        path = self.bin / name
        path.write_text(body)
        path.chmod(0o755)

    def config(self, schedule, **overrides):
        c = {'schema': 't2867-contrast-runner-config/v1', 'root': str(self.root),
            'archive_root': str(self.base / 'archive'), 'cohort': 'test', 'version': 'test',
            'pin': '6810666', 'model': 'test-model', 'settings': str(self.settings),
            'expected_head': self.head, 'checkouts': [str(self.checkout)],
            'walltime_s': {'job1': 1800, 'eval': 900, 'score': 2700, 'reference': 3600},
            'schedule': [{'arm': a, 'series': s} for a, s in schedule],
            'max_active_series': 1, 'max_llm_parents': 1, 'poll_s': 1}
        c.update(overrides)
        return c

    def test_startup_validation_and_order_limit(self):
        c = self.config([('reference', 1), ('llm-cpp', 1)])
        r = runner.Runner(runner.config_read(self._config_file(c)))
        r.round()
        self.assertEqual([(n, x['checkout'] is not None) for n, x in r.state['series'].items()],
                         [('reference-1', True), ('llm-cpp-1', False)])
        self.assertEqual((self.root/'calls').read_text().splitlines(), ['reference-1 init'])
        c['schedule'].append({'arm': 'reference', 'series': 1})
        with self.assertRaises(ValueError): runner.config_read(self._config_file(c))

    def _config_file(self, c):
        path = self.base / 'config.json'
        path.write_text(json.dumps(c))
        return path

    def test_job_not_repeated_on_qstat_failure_or_restart(self):
        r = runner.Runner(self.config([('reference', 1)]))
        r.round(); r.round()
        self.assertEqual(r.state['series']['reference-1']['job'], '101.nqsv')
        self.qstat.write_text('broken\n')
        r.round()
        restarted = runner.Runner(self.config([('reference', 1)]))
        restarted.round()
        calls = (self.root/'calls').read_text().splitlines()
        self.assertEqual(calls.count('reference-1 submit'), 1)
        self.assertEqual(restarted.state['series']['reference-1']['job'], '101.nqsv')

    def test_restart_accepts_unsorted_schedule_and_rejects_different_series(self):
        c = self.config([('reference', 1), ('evo-ir', 1)],
                        checkouts=[str(self.checkout), str(self._second_checkout())],
                        max_active_series=2)
        runner.Runner(c)
        state = json.loads((self.root / 'runner-state/state.json').read_text())
        self.assertEqual(list(state['series']), ['evo-ir-1', 'reference-1'])

        restarted = runner.Runner(c)
        restarted.round()
        self.assertEqual((self.root / 'calls').read_text().splitlines(),
                         ['reference-1 init', 'evo-ir-1 init'])

        different = self.config([('reference', 1), ('random-ir', 1)])
        with self.assertRaisesRegex(ValueError, 'state schedule differs from config'):
            runner.Runner(different)

    def test_dead_job_and_rc_attention_then_done(self):
        r = runner.Runner(self.config([('reference', 1), ('random-ir', 1)],
            checkouts=[str(self.checkout), str(self._second_checkout())], max_active_series=2))
        self.control.write_text(json.dumps({'reference-1':'dead', 'random-ir-1':'end'}))
        r.round(); r.round()
        self.assertEqual(r.state['series']['reference-1']['attention']['kind'], 'dead-job')
        self.assertIsNotNone(r.state['series']['random-ir-1']['checkout'])
        self.assertTrue(r.round())
        self.assertTrue((self.root/'runner-state/done.json').exists())
        self.assertEqual(r.state['series']['random-ir-1']['end'], 'b-complete')

    def test_status_rc_attention_does_not_block_other_series(self):
        r = runner.Runner(self.config([('reference', 1), ('random-ir', 1)],
            checkouts=[str(self.checkout), str(self._second_checkout())], max_active_series=2))
        self.control.write_text(json.dumps({'reference-1':'bad', 'random-ir-1':'end'}))
        r.round()
        self.assertTrue(r.round())
        self.assertEqual(r.state['series']['reference-1']['attention']['kind'], 'status-rc')
        self.assertEqual(r.state['series']['random-ir-1']['end'], 'b-complete')

    def test_init_failure_keeps_schedule_order(self):
        # Force the first init to fail before any later schedule item is opened.
        launch = self.checkout / runner.LAUNCH
        launch.write_text('import sys\nsys.exit(2)\n')
        r = runner.Runner(self.config([('reference', 1), ('random-ir', 1)]))
        r.round(); r.round()
        self.assertEqual(r.state['series']['reference-1']['attention']['kind'], 'init-rc')
        self.assertIsNone(r.state['series']['random-ir-1']['checkout'])
        self.assertFalse((self.root/'ledgers/random-ir-1').exists())

    def test_pause_stops_new_actions(self):
        r = runner.Runner(self.config([('reference', 1)]))
        (self.root/'runner-state/pause').touch()
        r.round()
        self.assertFalse((self.root/'calls').exists())
        (self.root/'runner-state/pause').unlink()
        r.round()
        (self.root/'runner-state/pause').touch()
        r.round()
        self.assertEqual((self.root/'calls').read_text().splitlines(), ['reference-1 init', 'reference-1 status'])

    def test_parent_limit_and_clean_environment(self):
        c = self.config([('llm-cpp', 1), ('llm-ir', 1)],
                        checkouts=[str(self.checkout), str(self._second_checkout())],
                        max_active_series=2, max_llm_parents=1)
        r = runner.Runner(c)
        self.control.write_text(json.dumps({'llm-cpp-1':'waiting', 'llm-ir-1':'waiting'}))
        r.round()
        with patch.dict(os.environ, {'CLAUDE_SESSION_ID':'secret', 'ANTHROPIC_FOO':'secret',
                                      'AI_AGENT':'secret'}):
            r.round()
        self.assertEqual(sum(bool(x['parent']) for x in r.state['series'].values()), 1)
        first = r.state['series']['llm-cpp-1']['parent']
        self.assertEqual(first['a'], 1)
        restarted = runner.Runner(c)
        restarted.round()
        self.assertEqual(restarted.state['series']['llm-cpp-1']['parent']['pid'], first['pid'])
        self.assertEqual(sum(bool(x['parent']) for x in restarted.state['series'].values()), 1)
        r.processes['llm-cpp-1'].wait(timeout=3)
        self.assertEqual((self.root/'parent-env').read_text(), '')

    def test_lock_rejects_second_runner_and_accepts_stale_pid(self):
        c = self.config([('reference', 1)])
        state_dir = self.root / 'runner-state'
        state_dir.mkdir()
        (state_dir / 'runner.pid').write_text('99999999\n')
        lock = (state_dir / 'runner.lock').open('w')
        self.addCleanup(lock.close)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with self.assertRaisesRegex(ValueError, 'runner already running'):
            runner.run(c)
        self.assertFalse((self.root / 'calls').exists())
        fcntl.flock(lock, fcntl.LOCK_UN)
        with patch.object(runner.Runner, 'round', return_value=True):
            self.assertEqual(runner.run(c), 0)
        self.assertFalse((state_dir / 'runner.pid').exists())

    def test_starting_parent_restart_requires_attention(self):
        c = self.config([('llm-cpp', 1)])
        r = runner.Runner(c)
        item = r.state['series']['llm-cpp-1']
        item['checkout'] = str(self.checkout)
        item['parent'] = {'pid': None, 'a': 1, 'starting': True,
            'started': runner.now(), 'log': str(self.root / 'parent.log'), 'argv': []}
        r.persist()
        restarted = runner.Runner(c)
        self.assertEqual(restarted.state['series']['llm-cpp-1']['attention']['kind'],
                         'parent-start-unknown')
        restarted.round()
        self.assertFalse((self.root / 'calls').exists())
        item['parent']['starting'] = False
        item['parent']['pid'] = os.getpid()
        item['attention'] = None
        r.persist()
        accepted = runner.Runner(c)
        self.assertIsNone(accepted.state['series']['llm-cpp-1']['attention'])

    def test_leftover_init_or_submit_intent_requires_attention(self):
        for action in ('init', 'submit'):
            with self.subTest(action=action):
                c = self.config([('reference', 1)])
                r = runner.Runner(c)
                item = r.state['series']['reference-1']
                item['checkout'] = str(self.checkout) if action == 'submit' else None
                item['intent'] = {'action': action, 'ts': runner.now()}
                r.persist()
                restarted = runner.Runner(c)
                self.assertEqual(restarted.state['series']['reference-1']['attention']['kind'],
                                 'intent-unknown')
                restarted.round()
                self.assertFalse((self.root / 'calls').exists())
                item['intent'] = None
                item['attention'] = None
                r.persist()
                accepted = runner.Runner(c)
                self.assertIsNone(accepted.state['series']['reference-1']['attention'])

    def test_job_missing_needs_two_successes_and_120_seconds(self):
        c = self.config([('reference', 1)])
        r = runner.Runner(c)
        r.round(); r.round()
        item = r.state['series']['reference-1']
        submitted = item['job_submitted']
        self.qstat.write_text('RequestID User\n')
        with patch.object(runner.time, 'time', return_value=submitted + 119):
            r.round(); r.round()
        self.assertEqual(item['job'], '101.nqsv')
        self.assertEqual((self.root / 'calls').read_text().splitlines().count('reference-1 submit'), 1)
        self.qstat.write_text('RequestID User\n101.nqsv user\n')
        r.round()
        self.assertEqual(item['job_missing'], 0)
        self.qstat.write_text('RequestID User\n')
        (self.root / 'runner-state/pause').touch()
        with patch.object(runner.time, 'time', return_value=submitted + 121):
            r.round()
            self.assertEqual(item['job'], '101.nqsv')
            r.round()
        self.assertIsNone(item['job'])

    def test_stop_during_open_series_prevents_next_init(self):
        c = self.config([('reference', 1), ('random-ir', 1)],
                        checkouts=[str(self.checkout), str(self._second_checkout())],
                        max_active_series=2)
        r = runner.Runner(c)
        original = r.command
        def stop_after_first_init(name, action, argv, checkout, timeout=None):
            result = original(name, action, argv, checkout, timeout)
            if action == 'init':
                runner.STOP = True
            return result
        try:
            with patch.object(r, 'command', side_effect=stop_after_first_init):
                r.round()
        finally:
            runner.STOP = False
        self.assertEqual((self.root / 'calls').read_text().splitlines(), ['reference-1 init'])
        self.assertIsNone(r.state['series']['random-ir-1']['checkout'])
        r.round()
        self.assertIsNotNone(r.state['series']['random-ir-1']['checkout'])

    def _second_checkout(self):
        other = self.base/'checkout2'
        subprocess.run(['git', 'clone', '-q', str(self.checkout), str(other)], check=True)
        return other


if __name__ == '__main__':
    unittest.main()
```
