# probe の逐語

Codex author 作 (子 branch `author-t2273-probe-fix2` の終端 commit `7f38ac7fd`)。repo 外の job dir で実行し、repo には本逐語だけを置く。
R2'' はこの版で走った。R1 は `c7793e51f` 版 (run mode のみ)、R2 (X 無効) は `c962d9e92` 版、R2' は `22e361d9c` 版。plugin と analyzer は `c962d9e92` 以降同一 blob、runner だけが fix1 (staging を /scr へ・残骸掃除・quota 記録) と fix2 (/scr/<user> の作成) で変わった。

## tools/t2273_replica_runner.py

```python
"""Compute-only smoke then A or paired A2/staging/X; Python 3.10 standard library."""
import argparse
import errno
import getpass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import socket
import subprocess
import sys
import tempfile
import time
import threading
import re

sys.dont_write_bytecode = True
SPEC_ENV = 'IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1'
UNSET = ('PYTEST_ADDOPTS', 'PYTEST_XDIST_TESTRUNUID', 'IZANAGI_TASK_RUN_SIDECAR',
         'PYTHONPYCACHEPREFIX', 'IZANAGI_TEST_RUNNER_EXCLUSIONS_V1', 'PYTEST_PLUGINS',
         'PYTEST_DISABLE_PLUGIN_AUTOLOAD', 'IZANAGI_RUN_GROWTH_HELD_TESTS',
         'PYTEST_XDIST_WORKER', 'PYTEST_XDIST_WORKER_COUNT',
         'IZANAGI_ACCEPTANCE_SHARDS', SPEC_ENV, 'T2273_REPLICA_OUT', 'T2273_LOCAL_OUTPUT_SOURCE')
_ACTIVE = None


def dump(path, value):
    path = Path(path)
    pending = path.with_name(path.name + '.pending')
    pending.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n')
    pending.replace(path)


def command(argv, **kwargs):
    return subprocess.check_output(argv, text=True, timeout=30, **kwargs).strip()


def activity(tmp):
    user = getpass.getuser()
    processes = command(['ps', '-eo', 'user,pid,comm']).splitlines()[1:]
    system = {'root', 'daemon', 'bin', 'sys', 'sync', 'mail', 'nobody',
              'dbus', 'rpc', 'rpcuser', 'chrony', 'ntp', 'postfix', 'sshd', 'nscd'}
    rows = [line.split(None, 2) for line in processes]
    others = [r for r in rows if len(r) == 3 and r[0] not in system | {user}]
    stale = [r for r in rows if len(r) == 3 and r[0] == user and 'pytest' in r[2]]
    return {'epoch': time.time(), 'loadavg': list(os.getloadavg()),
            'others': len(others), 'stale_pytest': len(stale),
            'other_processes': others, 'stale_pytest_processes': stale,
            'system_users_excluded': sorted(system),
            'residues': sorted(str(p) for p in tmp.glob('izanagi-t080-e2e-session-*'))}


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def reap_group(process):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if not group_exists(process.pid):
            process.poll()
            return True
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return True
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            process.poll()
            if not group_exists(process.pid):
                return True
            time.sleep(.1)
    return not group_exists(process.pid)


def child(argv, env, repo, log):
    global _ACTIVE
    started = time.monotonic()
    with log.open('wb') as stream:
        _ACTIVE = subprocess.Popen(argv, cwd=repo, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        rc = _ACTIVE.wait()
        wall = time.monotonic() - started
        remaining = group_exists(_ACTIVE.pid)
        reaped = reap_group(_ACTIVE) if remaining else True
        if reaped:
            _ACTIVE = None
        if remaining:
            raise RuntimeError(f'child group remained after rc={rc}; reaped={reaped}')
    return rc, wall


def filesystem(tmp):
    """Record mount identity and statvfs without relocating temporary storage."""
    result = {'path': str(tmp), 'missing': []}
    try:
        vfs = os.statvfs(tmp)
        result['statvfs'] = {name: getattr(vfs, name) for name in
            ('f_bsize', 'f_frsize', 'f_blocks', 'f_bfree', 'f_bavail',
             'f_files', 'f_ffree', 'f_favail', 'f_flag', 'f_namemax')}
        device = os.stat(tmp).st_dev
        result['device'] = [os.major(device), os.minor(device)]
    except OSError as exc:
        result['missing'].append('statvfs/stat: ' + repr(exc))
    try:
        path = tmp.resolve()
        mounts = []
        for line in Path('/proc/mounts').read_text().splitlines():
            fields = [re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), field)
                      for field in line.split()]
            mount = Path(fields[1])
            if path == mount or mount in path.parents:
                mounts.append({'source': fields[0], 'mount_point': fields[1],
                               'filesystem': fields[2], 'options': fields[3]})
        result['mount'] = max(mounts, key=lambda m: len(m['mount_point'])) if mounts else None
        if not mounts:
            result['missing'].append('no matching /proc/mounts entry')
    except (OSError, ValueError, IndexError) as exc:
        result['missing'].append('mounts: ' + repr(exc))
    return result


def storage(tmp, staged_place):
    quota = {'attempts': [], 'missing': []}
    for flag in ('-s', '-v'):
        try:
            result = subprocess.run(['quota', flag], capture_output=True, text=True, timeout=10)
            quota['attempts'].append({'argv': ['quota', flag], 'rc': result.returncode,
                                      'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode == 0:
                break
        except (OSError, subprocess.TimeoutExpired) as exc:
            quota['attempts'].append({'argv': ['quota', flag], 'error': repr(exc)})
    else:
        quota['missing'].append('quota -s / -v unavailable or unsuccessful')
    return {'epoch': time.time(), 'quota': quota, 'TMPDIR': filesystem(tmp),
            'staged_place': filesystem(staged_place)}


def temp_inventory(tmp):
    """Only the named direct children; never traverse a pytest-root symlink."""
    paths = list(tmp.glob('izanagi-t080-e2e-*')) + list(tmp.glob('izanagi-task-run-*'))
    pytest_root = tmp / ('pytest-of-' + getpass.getuser())
    if pytest_root.exists() or pytest_root.is_symlink():
        info = pytest_root.lstat()
        if stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid():
            paths += list(pytest_root.glob('pytest-*'))
    result = {}
    for path in paths:
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        result[str(path)] = {'uid': info.st_uid, 'device': info.st_dev,
                             'inode': info.st_ino, 'mode': info.st_mode}
    return result


class JobTemps:
    """Attribute new paths only across this job's reaped child runs.

    The compute job's exclusive-node/quiet-child guards are prerequisites.
    Preserve every initial pathname, including a replaced inode at that name.
    """
    def __init__(self, tmp):
        self.tmp = tmp
        self.initial = temp_inventory(tmp)
        self.owned = {}

    def capture(self, before):
        for path, info in temp_inventory(self.tmp).items():
            if path not in self.initial and path not in before and info['uid'] == os.getuid():
                self.owned[path] = info

    def clean(self):
        result = {'deleted_count': 0, 'deleted_bytes': 0, 'deleted_allocated_bytes': 0,
                  'deleted': [], 'skipped': [],
                  'attribution': 'new during this job child; initial paths always protected'}
        current = temp_inventory(self.tmp)
        for name, identity in list(self.owned.items()):
            if name in self.initial or current.get(name) != identity:
                result['skipped'].append(name)
                continue
            path = Path(name)
            # Count without following links; refuse a tree with foreign-owned entries.
            entries = [path]
            if path.is_dir() and not path.is_symlink():
                def walk_error(exc):
                    raise exc
                for directory, dirs, files in os.walk(path, followlinks=False, onerror=walk_error):
                    entries.extend(Path(directory) / n for n in dirs + files)
            infos = [p.lstat() for p in entries]
            if any(s.st_uid != os.getuid() for s in infos):
                result['skipped'].append(name)
                continue
            size = sum(s.st_size for s in infos)
            allocated = sum(s.st_blocks * 512 for s in infos)
            if path.is_symlink() or not path.is_dir():
                path.unlink()
            else:
                shutil.rmtree(path)
            result['deleted'].append({'path': name, 'bytes': size, 'allocated_bytes': allocated})
            result['deleted_count'] += 1
            result['deleted_bytes'] += size
            result['deleted_allocated_bytes'] += allocated
            del self.owned[name]
        return result


def resource_sample(device):
    row = {'epoch': time.time(), 'mono': time.monotonic(), 'missing': [],
           'cpu': None, 'loadavg': None, 'lustre': {}, 'diskstats': None}
    try:
        fields = Path('/proc/stat').read_text().splitlines()[0].split()
        if fields[0] != 'cpu' or len(fields) < 9:
            raise ValueError('missing aggregate CPU fields')
        row['cpu'] = dict(zip(('user', 'nice', 'system', 'idle', 'iowait',
                              'irq', 'softirq', 'steal'), map(int, fields[1:9])))
    except (OSError, ValueError, IndexError) as exc:
        row['missing'].append('cpu: ' + repr(exc))
    try:
        fields = Path('/proc/loadavg').read_text().split()
        running, total = map(int, fields[3].split('/'))
        row['loadavg'] = {'load1': float(fields[0]), 'load5': float(fields[1]),
                          'load15': float(fields[2]), 'running': running,
                          'total': total, 'last_pid': int(fields[4])}
    except (OSError, ValueError, IndexError) as exc:
        row['missing'].append('loadavg: ' + repr(exc))
    for pattern in ('llite/*/stats', 'mdc/*/md_stats'):
        try:
            paths = sorted(Path('/proc/fs/lustre').glob(pattern))
            if not paths:
                row['missing'].append('lustre: no readable ' + pattern)
            for path in paths:
                try:
                    raw = path.read_text()
                    counters = {}
                    for line in raw.splitlines():
                        fields = line.split()
                        if len(fields) >= 3 and fields[2] == 'samples':
                            counters[fields[0]] = int(fields[1])
                    # Raw text retains all counters, units, min/max/sum and timestamps.
                    row['lustre'][str(path)] = {'raw': raw, 'counters': counters}
                except (OSError, ValueError) as exc:
                    row['missing'].append(str(path) + ': ' + repr(exc))
        except OSError as exc:
            row['missing'].append('lustre ' + pattern + ': ' + repr(exc))
    try:
        if device is None:
            raise ValueError('TMPDIR device unavailable')
        rows = [line for line in Path('/proc/diskstats').read_text().splitlines()
                if list(map(int, line.split()[:2])) == device]
        row['diskstats'] = rows
        if not rows:
            row['missing'].append('no diskstats block device for TMPDIR (e.g. tmpfs/Lustre)')
    except (OSError, ValueError) as exc:
        row['missing'].append('diskstats: ' + repr(exc))
    row['end_mono'] = time.monotonic()
    return row


class Sampler:
    def __init__(self, path, tmp):
        self.path = path
        self.device = filesystem(tmp).get('device')
        self.done = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def start(self):
        try:
            self.thread.start()
        except Exception as exc:
            self.failure(exc)

    def failure(self, exc):
        try:
            dump(self.path.with_name('sample-error.json'), {'missing': repr(exc)})
        except OSError:
            pass  # An unwritable output is detected as absent samples by analyzer.

    def loop(self):
        deadline = time.monotonic()
        while not self.done.is_set():
            try:
                try:
                    row = resource_sample(self.device)
                except Exception as exc:
                    row = {'epoch': time.time(), 'mono': time.monotonic(),
                           'missing': ['sample: ' + repr(exc)]}
                with self.path.open('a') as stream:
                    stream.write(json.dumps(row) + '\n')
            except Exception as exc:
                self.failure(exc)
            deadline += 1.0
            # If reading counters took >1 s, skip missed ticks, never busy-loop.
            now = time.monotonic()
            if deadline < now:
                deadline = now + 1.0
            self.done.wait(max(0.0, deadline - now))

    def stop(self):
        self.done.set()
        if self.thread.ident is not None:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                self.failure(RuntimeError('sampler read did not finish within 5 seconds'))


def git_env():
    # Same environment as the real _run_git_bytes; no source index refresh.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    return env


def snapshot(repo, tmp, staged_place=None):
    row = activity(tmp)
    if staged_place is not None:
        row['storage'] = storage(tmp, staged_place)
    row.update(HEAD=command(['git', '-C', str(repo), 'rev-parse', 'HEAD'], env=git_env()),
               git_status_line_count=len(command(['git', '-C', str(repo), 'status',
                                                  '--porcelain'], env=git_env()).splitlines()))
    return row


def stage_output(repo, tmp, record_path, *, test_tmp=None):
    """Independent clone; reject visible untracked input instead of silently omitting it."""
    global _ACTIVE
    repo, tmp = Path(repo).resolve(), Path(tmp).resolve()
    if tmp == repo or repo in tmp.parents:
        raise ValueError('staging TMPDIR must be outside real repo')
    started = time.monotonic()
    record = {'start_epoch': time.time(), 'commands': [], 'valid': False,
              'untracked_policy': 'reject: control must use committed input', 'file_count': None}
    record['storage_before'] = storage(test_tmp or tmp, tmp)
    record['placement'] = filesystem(tmp)
    staged_parent = None
    dump(record_path, record)

    def git(root, *args, allowed=(0,)):
        global _ACTIVE
        argv = ['git', '-C', str(root), *args]
        record['commands'].append(argv)
        _ACTIVE = subprocess.Popen(argv, env=git_env(), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = _ACTIVE.communicate(timeout=600)
            rc = _ACTIVE.returncode
            if rc not in allowed:
                raise RuntimeError(f'{argv!r}: rc={rc}: {stderr.decode(errors="replace")}')
            return stdout
        finally:
            if _ACTIVE is not None:
                reap_group(_ACTIVE)
                _ACTIVE = None

    def listing(root):
        tracked = git(root, 'ls-files', '-z', '-s', '--', 'output')
        others = git(root, 'ls-files', '-z', '--others', '--exclude-standard', '--', 'output')
        visible = set()
        for entry in tracked.split(b'\0'):
            if not entry:
                continue
            meta, relative = entry.decode('utf-8').split('\t', 1)
            if meta.split()[0] in ('100644', '100755'):
                visible.add(relative)
        # Reject every untracked output entry, including symlinks (conservative).
        if others:
            raise ValueError('untracked visible output entries present: ' + repr(others))
        return tracked, visible

    try:
        head = git(repo, 'rev-parse', 'HEAD').decode().strip()
        tracked, visible = listing(repo)
        record.update(HEAD=head, visible_path_count=len(visible),
                      visible_path_sha256=hashlib.sha256(json.dumps(sorted(visible),
                        ensure_ascii=True, separators=(',', ':')).encode()).hexdigest())
        staged_parent = Path(tempfile.mkdtemp(prefix='t2273-output-', dir=tmp))
        staged = staged_parent / 'repo'
        record['staged_root'] = str(staged)
        record['placement'] = filesystem(staged_parent)
        git(tmp, 'clone', '--no-local', '--no-checkout', str(repo), str(staged))
        git(staged, 'checkout', head, '--', 'output')
        # The real function disables global/system Git config. Preserve its local
        # ignore config, info/exclude, and every on-disk .gitignore under output.
        rules = [repo / '.gitignore']
        for directory, dirs, files in os.walk(repo / 'output', followlinks=False):
            if '.gitignore' in files:
                rules.append(Path(directory) / '.gitignore')
        hashes = {}
        for source in rules:
            if not source.exists():
                continue
            if source.is_symlink() or not source.is_file():
                raise ValueError('nonregular ignore rule: ' + str(source))
            relative = source.relative_to(repo)
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if source.read_bytes() != target.read_bytes():
                raise ValueError('ignore rule bytes differ: ' + str(relative))
            hashes[str(relative)] = hashlib.sha256(source.read_bytes()).hexdigest()
        exclude = Path(git(repo, 'rev-parse', '--git-path', 'info/exclude').decode().strip())
        if not exclude.is_absolute():
            exclude = repo / exclude
        target = staged / '.git/info/exclude'
        target.write_bytes(exclude.read_bytes() if exclude.exists() else b'')
        hashes['.git/info/exclude'] = hashlib.sha256(target.read_bytes()).hexdigest()
        for key in ('core.excludesfile', 'core.ignorecase'):
            value = git(repo, 'config', '--get', key, allowed=(0, 1)).decode().strip()
            if key == 'core.excludesfile' and value:
                # Relative/home-expanded local config is intentionally not guessed.
                raise ValueError('local core.excludesfile unsupported: ' + value)
            if value:
                git(staged, 'config', key, value)
            else:
                git(staged, 'config', '--unset-all', key, allowed=(0, 5))
            if git(staged, 'config', '--get', key, allowed=(0, 1)).decode().strip() != value:
                raise ValueError('local ignore config differs: ' + key)
        staged_tracked, staged_visible = listing(staged)
        if staged_tracked != tracked or staged_visible != visible:
            raise ValueError('staged Git-visible set/index differs')
        # Validate regular-file type and bytes, including paths excluded by copy.
        for relative in sorted(visible):
            source, target = repo / relative, staged / relative
            if source.is_symlink() or target.is_symlink() or not source.is_file() or not target.is_file():
                raise ValueError('nonregular visible file: ' + relative)
            if source.read_bytes() != target.read_bytes():
                raise ValueError('staged bytes differ: ' + relative)
        record.update(valid=True, file_count=len(visible), ignore_rule_sha256=hashes,
                      visible_set_equal=True, bytes_equal=True,
                      independent_git_admin=True)
        return staged
    except BaseException as exc:
        record['error'] = repr(exc)
        if staged_parent is not None:
            shutil.rmtree(staged_parent)
            record['staged_removed'] = True
        raise
    finally:
        record.update(end_epoch=time.time(), wall_s=time.monotonic() - started)
        record['storage_after'] = storage(test_tmp or tmp, tmp)
        dump(record_path, record)


def staged_replica(repo, tmp, out, replica, *, scratch=None):
    """The production X gate. scratch injection is for small local verification only."""
    scratch = Path(scratch) if scratch is not None else Path('/scr') / getpass.getuser()
    staged = None
    scratch_created = False
    scratch_identity = None
    try:
        resolved = scratch.resolve()
        if (not scratch.parent.is_dir() or not os.access(scratch.parent, os.W_OK | os.X_OK)
                or resolved == tmp.resolve() or tmp.resolve() in resolved.parents
                or resolved == Path('/tmp') or Path('/tmp') in resolved.parents):
            raise RuntimeError('X not run: writable node scratch outside TMPDIR required: ' + str(scratch))
        for place in (scratch.parent, scratch):
            mount = filesystem(place).get('mount')
            if (not mount or not mount['source'].startswith('/dev/')
                    or mount['filesystem'] not in ('xfs', 'ext4', 'ext3', 'ext2', 'btrfs')):
                raise RuntimeError('X not run: node-local scratch filesystem unconfirmed: ' + repr(mount))
        try:
            info = scratch.lstat()
        except FileNotFoundError:
            scratch.mkdir(mode=0o700, exist_ok=True)
            scratch_created = True
            info = scratch.lstat()
            scratch_identity = (info.st_dev, info.st_ino)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or not os.access(scratch, os.W_OK | os.X_OK)):
            raise RuntimeError('X not run: writable self-owned scratch directory required: ' + str(scratch))
        staged = stage_output(repo, scratch, out / 'staging.json', test_tmp=tmp)
        return replica('X', staged)
    except BaseException as exc:
        if not (out / 'staging.json').exists():
            dump(out / 'staging.json', {'valid': False, 'error': repr(exc),
                 'placement': filesystem(scratch), 'storage_before': storage(tmp, scratch),
                 'storage_after': storage(tmp, scratch)})
        dump(out / 'incomplete.json', {'reason': repr(exc), 'rc': 4})
        raise
    finally:
        record_path = out / 'staging.json'
        record = json.loads(record_path.read_text()) if record_path.exists() else {}
        record.update(scratch_user_dir=str(scratch), scratch_user_dir_created=scratch_created,
                      scratch_user_dir_removed=False)
        dump(record_path, record)
        if staged is not None:
            # Includes failed X and signal/deadline exceptions; never leave the clone behind.
            if _ACTIVE is not None and not reap_group(_ACTIVE):
                raise RuntimeError('cannot remove staged repo while child group remains')
            shutil.rmtree(staged.parent)
            record['staged_removed'] = True
            record['storage_after_cleanup'] = storage(tmp, scratch)
        if scratch_created:
            try:
                info = scratch.lstat()
                if (info.st_dev, info.st_ino) == scratch_identity and info.st_uid == os.getuid():
                    scratch.rmdir()  # Only an empty directory created by this job.
                    record['scratch_user_dir_removed'] = True
            except OSError as exc:
                if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT):
                    raise
                record['scratch_user_dir_cleanup_note'] = repr(exc)
        dump(record_path, record)


def run(args, out):
    repo, probe = Path(args.repo_root).resolve(), Path(args.probe_dir).resolve()
    if any(p == repo or repo in p.parents for p in (probe, out)):
        raise ValueError('probe and output must be outside the measurement checkout')
    if any(out.iterdir()):
        raise ValueError('out-root must be empty (one run only)')
    inherited_tmpdir = os.environ.get('TMPDIR')
    effective_tmpdir = inherited_tmpdir if inherited_tmpdir is not None else tempfile.gettempdir()
    tmp = Path(effective_tmpdir)
    if not tmp.is_absolute():
        tmp = repo / tmp
    scratch = Path('/scr') / getpass.getuser()
    temps = JobTemps(tmp) if args.mode == 'pair' else None
    env = os.environ.copy()
    removed = sorted(k for k in UNSET if k in env)
    for name in UNSET:
        env.pop(name, None)
    env.update(PYTHONDONTWRITEBYTECODE='1', IZANAGI_TASK_RUN_AUTO_RECORD='0',
               PYTHONPATH=str(probe) + os.pathsep + str(repo),
               TMPDIR=effective_tmpdir)
    if any(k in env for k in UNSET):
        raise RuntimeError('forbidden child environment survived sanitization')
    before = activity(tmp)
    if temps is not None:
        before['temp_inventory'] = temps.initial
        before['storage'] = storage(tmp, scratch)
    before.update(hostname=socket.gethostname(),
                  HEAD=command(['git', '-C', str(repo), 'rev-parse', 'HEAD']),
                  git_status_line_count=len(command(['git', '-C', str(repo), 'status',
                                                     '--porcelain'], env=git_env()).splitlines()),
                  python=sys.version, pytest=importlib.metadata.version('pytest'),
                  xdist=importlib.metadata.version('pytest-xdist'),
                  nproc=int(command(['nproc'])), TMPDIR=effective_tmpdir,
                  inherited_TMPDIR=inherited_tmpdir, tmp_filesystem=filesystem(tmp), removed_env=removed,
                  acceptance_shards_env='unset: compute has no outer shard dispatch; plugin spec selects 0/3')
    dump(out / 'env-before.json', before)
    if before['git_status_line_count']:
        dump(out / 'incomplete.json', {'reason': 'measurement checkout is not clean',
                                      'rc': 4, 'git_status_line_count': before['git_status_line_count']})
        return 4
    smoke = out / 'smoke'
    smoke.mkdir()
    smoke_before = snapshot(repo, tmp, scratch if temps else None)
    dump(smoke / 'env-before.json', smoke_before)
    if smoke_before['git_status_line_count'] or smoke_before['HEAD'] != before['HEAD'] or smoke_before['others'] or smoke_before['stale_pytest']:
        raise RuntimeError('smoke precondition failed: ' + repr(smoke_before))
    base = ['python3.10', str(repo / 'tools/run_tests.py')]
    plugins = ['-p', 'no:cacheprovider', '-p', 't2273_replica_plugin']
    argv = base + ['orchestrator/tests/test_s8b_oracle_driver.py', '-k',
                   'shared_base_builds_real_builder_once_across_processes',
                   '-n', '2', '--dist', 'loadgroup'] + plugins
    smoke_start = time.monotonic()
    smoke_record = {'executed': True, 'argv': argv, 'start_epoch': time.time(),
                    'rc': None, 'wall_s': None}
    dump(smoke / 'run.json', smoke_record)
    smoke_temps = temp_inventory(tmp) if temps else None
    try:
        rc, wall = child(argv, dict(env, T2273_REPLICA_OUT=str(smoke)), repo, smoke / 'pytest.log')
    except BaseException as exc:
        smoke_record.update(error=repr(exc), wall_s=time.monotonic() - smoke_start, end_epoch=time.time())
        dump(smoke / 'run.json', smoke_record)
        raise
    smoke_record.update(rc=rc, wall_s=wall, end_epoch=time.time())
    dump(smoke / 'run.json', smoke_record)
    if temps:
        temps.capture(smoke_temps)
    smoke_after = snapshot(repo, tmp, scratch if temps else None)
    dump(smoke / 'env-after.json', smoke_after)
    if smoke_after['git_status_line_count'] or smoke_after['HEAD'] != before['HEAD'] or smoke_after['others'] or smoke_after['stale_pytest']:
        raise RuntimeError('smoke postcondition failed: ' + repr(smoke_after))
    spans = [json.loads(line) for p in smoke.glob('spans-*.jsonl')
             for line in p.read_text().splitlines()]
    builds = sum(e['name'] == 'build' and e['ok'] for e in spans)
    smoke_record['build_spans'] = builds
    dump(smoke / 'run.json', smoke_record)
    if rc or builds < 1 or list(smoke.glob('record-error-*.json')):
        dump(out / 'incomplete.json', dict(smoke_record, reason='smoke failed',
             log_tail='\n'.join((smoke / 'pytest.log').read_text(errors='replace').splitlines()[-60:])))
        return 4
    # Repeat the clean-tree guard immediately before A.
    if command(['git', '-C', str(repo), 'status', '--porcelain'], env=git_env()):
        dump(out / 'incomplete.json', {'reason': 'measurement checkout dirty after smoke', 'rc': 4})
        return 4
    def replica(condition, staged=None):
        directory = out / condition
        directory.mkdir()
        place = staged if staged is not None else scratch
        guard = snapshot(repo, tmp, place if temps else None)
        dump(directory / 'env-before.json', guard)
        if guard['git_status_line_count'] or guard['HEAD'] != before['HEAD'] or guard['others'] or guard['stale_pytest']:
            raise RuntimeError(condition + ' precondition failed: ' + repr(guard))
        cleanup = temps.clean() if temps else None
        if temps:
            guard['temp_cleanup'] = cleanup
            dump(directory / 'env-before.json', guard)
        # The sole repository API required by the runner contract is invoked in a
        # separate interpreter. This file itself imports standard library only.
        code = ('from pathlib import Path; from tools import acceptance_shards; '
                'import sys; print(acceptance_shards.create_session(Path(sys.argv[1]), 3))')
        session_log = directory / 'create-session.log'
        session_rc, _ = child(['python3.10', '-c', code, str(repo)], env, repo, session_log)
        if session_rc:
            raise RuntimeError(f'create_session failed: rc={session_rc}')
        session = Path(session_log.read_text().strip())
        if not session.is_absolute() or not (session / 'shard-0').is_dir():
            raise RuntimeError('create_session returned no absolute session directory')
        record = {'condition': condition, 'job_tag': args.job_tag, 'HEAD': before['HEAD'],
                  'session_root': str(session), 'session_basename': session.name,
                  'smoke': smoke_record, 'rc': None, 'start_epoch': time.time()}
        dump(out / 'run.json', record)
        dump(directory / 'run.json', record)
        guard = snapshot(repo, tmp, place if temps else None)
        if temps:
            guard['temp_cleanup'] = cleanup
        dump(directory / 'env-before.json', guard)
        if guard['git_status_line_count'] or guard['HEAD'] != before['HEAD'] or guard['others'] or guard['stale_pytest']:
            raise RuntimeError(condition + ' immediate precondition failed: ' + repr(guard))
        argv = base + ['orchestrator/tests', '-n', '48', '--dist', 'loadgroup',
                       '--junitxml=' + str(session / 'shard-0/junit.xml'),
                       '-p', 'tools.acceptance_shards'] + plugins
        child_env = dict(env, T2273_REPLICA_OUT=str(directory))
        child_env[SPEC_ENV] = json.dumps({'session_root': str(session), 'shard_count': 3, 'shard_index': 0})
        if staged is not None:
            child_env['T2273_LOCAL_OUTPUT_SOURCE'] = str(staged)
        record['env'] = {k: child_env[k] for k in ('PYTHONDONTWRITEBYTECODE', 'IZANAGI_TASK_RUN_AUTO_RECORD', 'PYTHONPATH', 'TMPDIR', 'T2273_REPLICA_OUT', SPEC_ENV)}
        record['env']['T2273_LOCAL_OUTPUT_SOURCE'] = child_env.get('T2273_LOCAL_OUTPUT_SOURCE')
        record['argv'] = argv
        dump(directory / 'run.json', record)
        sampler = Sampler(directory / 'samples.jsonl', tmp)
        sampler.start()
        run_temps = temp_inventory(tmp) if temps else None
        try:
            rc, wall = child(argv, child_env, repo, directory / 'pytest.log')
        finally:
            sampler.stop()
            if temps and _ACTIVE is None:
                temps.capture(run_temps)
            if temps:
                after = snapshot(repo, tmp, place)
                dump(directory / 'env-after.json', after)
        record.update(rc=rc, wall_s=wall, end_epoch=time.time())
        if not temps:
            after = snapshot(repo, tmp)
        dump(directory / 'env-after.json', after)
        copied = directory / 'session'
        copied.mkdir()
        missing = []
        for name in ('report.json', 'junit.xml'):
            source = session / 'shard-0' / name
            if source.is_file():
                shutil.copy2(source, copied / name)
            else:
                missing.append(name)
        record['missing_artifacts'] = missing
        dump(directory / 'run.json', record)
        dump(out / 'run.json', record)
        if after['git_status_line_count'] or after['HEAD'] != before['HEAD'] or after['others'] or after['stale_pytest']:
            raise RuntimeError(condition + ' postcondition failed: ' + repr(after))
        if rc or missing:
            dump(out / 'incomplete.json', {'reason': condition + ' failed or artifacts missing',
                                          'rc': rc, 'missing': missing})
        return rc if rc else (4 if missing else 0)

    if args.mode == 'run':
        return replica('A')
    rc = replica('A2')
    if rc:
        return rc
    return staged_replica(repo, tmp, out, replica)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['run', 'pair'])
    for name in ('repo-root', 'probe-dir', 'out-root', 'job-tag'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if not socket.gethostname().startswith('bnode'):
        print('compute hostname prerequisite failed (requires bnode)', file=sys.stderr)
        return 3
    out = Path(args.out_root).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rc = 4

    def stop_job(signum, frame):
        signal.alarm(0)
        raise InterruptedError(f'job deadline or termination: signal={signum}')

    for sig in (signal.SIGTERM, signal.SIGALRM, signal.SIGINT):
        signal.signal(sig, stop_job)
    signal.alarm(2900)
    try:
        rc = run(args, out)
    except BaseException as exc:
        signal.alarm(0)
        rc = 124 if isinstance(exc, InterruptedError) else 4
        reaped = reap_group(_ACTIVE) if _ACTIVE is not None else True
        dump(out / 'incomplete.json', {'reason': repr(exc), 'rc': rc, 'group_reaped': reaped})
    finally:
        signal.alarm(0)
        (out / 'probe.done').write_text(f'rc={rc}\n')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
```

## tools/t2273_replica_plugin.py

```python
"""Observations plus optional R2 control substitution, not an observational wrapper.

Only the real-repository output source is substituted; no selection or scheduling.
"""
import functools
import hashlib
import inspect
import json
import os
import resource
from pathlib import Path
import sys
import threading
import time

import pytest

_TARGET = 'orchestrator/tests/test_s8b_oracle_driver.py'
_REC = None


def cpu_usage():
    result = {}
    for label, who in (('self', resource.RUSAGE_SELF), ('children', resource.RUSAGE_CHILDREN)):
        usage = resource.getrusage(who)
        result[label] = {'utime': usage.ru_utime, 'stime': usage.ru_stime}
    return result


class Recorder:
    def __init__(self, out, worker):
        self.out, self.worker = Path(out), worker
        self.local = threading.local()
        self.counter = 0
        self.nodeid = ''
        self.test = None
        self.started = None
        self.installed = False
        self.undo = []
        self.errors = []

    def stack(self):
        if not hasattr(self.local, 'stack'):
            self.local.stack = []
        return self.local.stack

    def record_error(self, exc):
        self.errors.append(repr(exc))
        try:
            (self.out / f'record-error-{self.worker}-{os.getpid()}.json').write_text(
                json.dumps(self.errors) + '\n')
        except Exception:
            pass  # Never replace a production exception or write worker stderr.

    def begin(self, name, key=None, extra=None):
        stack = self.stack()
        parent = stack[-1] if stack else None
        self.counter += 1
        metadata = dict(parent['extra']) if parent else {}
        metadata.update(extra or {})
        metadata.update(nodeid=self.nodeid, span_id=f'{os.getpid()}:{self.counter}',
                        parent_span_id=parent['extra']['span_id'] if parent else None)
        return dict(worker=self.worker, pid=os.getpid(), name=name,
                    key=key if key is not None else (parent['key'] if parent else None),
                    begin_epoch=time.time(), begin_mono=time.monotonic(),
                    end_epoch=None, end_mono=None, ok=True, error=None, extra=metadata,
                    _cpu_begin=cpu_usage())

    def end(self, event, error=None):
        event.update(end_epoch=time.time(), end_mono=time.monotonic(),
                     ok=error is None, error=error)
        try:
            initial = event.pop('_cpu_begin')
            final = cpu_usage()
            event['extra']['cpu'] = {who: {field: final[who][field] - initial[who][field]
                for field in ('utime', 'stime')} for who in ('self', 'children')}
            # Resolve PID on each write: the real-builder smoke forks after install.
            with (self.out / f'spans-{self.worker}-{os.getpid()}.jsonl').open('a') as stream:
                stream.write(json.dumps(event, ensure_ascii=True) + '\n')
                stream.flush()
        except Exception as exc:
            self.record_error(exc)

    def invoke(self, original, name, args, kwargs, key=None, extra=None):
        event = None
        try:
            event = self.begin(name, key, extra)
            self.stack().append(event)
        except Exception as exc:
            self.record_error(exc)
        error = None
        try:
            result = original(*args, **kwargs)
            if event is not None and name == 'copy' and event['extra'].get('callable') == '_copy_git_visible_output':
                try:
                    event['extra']['visible_path_count'] = len(result)
                    event['extra']['visible_path_sha256'] = hashlib.sha256(
                        json.dumps(sorted(result), ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()
                except Exception as exc:
                    self.record_error(exc)
            return result
        except BaseException as exc:
            error = repr(exc)
            raise
        finally:
            if event is not None:
                self.stack().pop()
                self.end(event, error)

    def patch(self, owner, attr, classify):
        original = getattr(owner, attr, None)
        if not callable(original):
            self.record_error(RuntimeError('未計測: missing callable ' + attr))
            return

        @functools.wraps(original)
        def observed(*args, **kwargs):
            spec = None
            try:
                spec = classify(args, kwargs, sys._getframe(1).f_code)
            except Exception as exc:
                self.record_error(exc)
            if spec is None:
                return original(*args, **kwargs)
            name, key, extra = spec
            return self.invoke(original, name, args, kwargs, key, extra)
        self.undo.append((owner, attr, original))
        setattr(owner, attr, observed)


def install(rec, module):
    builder = getattr(module, '_build_t080_stub_free_e2e_repo', None)
    helper = getattr(module, '_t080_stub_free_e2e_repo', None)
    bases_class = getattr(module, '_T080SharedBases', None)
    if not all(callable(x) for x in (builder, helper, bases_class)):
        rec.record_error(RuntimeError('未計測: builder/helper/shared bases absent'))
        rec.installed = True
        return
    bases = module._T080_SHARED_BASES
    build_code, helper_code = builder.__code__, helper.__code__
    get_code = bases_class.get.__code__
    fields = ('r_trailer', 'extra_r_path', 'issue_receipt',
              'distinct_basis_blob', 'active_v2_base')

    def arguments(function, args, kwargs):
        bound = inspect.signature(function).bind(*args, **kwargs)
        bound.apply_defaults()
        return [bound.arguments[field] for field in fields]

    def get_spec(args, kwargs, caller):
        key = args[1] if len(args) > 1 else kwargs['key']
        return ('get', list(key), {'shared_session': args[0] is bases,
                                  'base_parent': str(args[0].parent),
                                  'shared_base_parent': str(args[0].parent)})

    rec.patch(bases_class, 'get', get_spec)
    rec.patch(module, '_t080_stub_free_e2e_repo', lambda a, k, c:
              ('helper', arguments(helper, a, k), {}))
    rec.patch(module, '_build_t080_stub_free_e2e_repo', lambda a, k, c:
              ('build', arguments(builder, a, k), {'base_parent': str(a[0] if a else k['tmp_path'])}))

    def direct(name):
        return lambda a, k, c: (name, None, {}) if c is build_code else None

    original_copy = module._copy_git_visible_output
    staged_value = os.environ.get('T2273_LOCAL_OUTPUT_SOURCE')
    staged = Path(staged_value).resolve() if staged_value else None
    real_root = Path(module.ROOT).resolve()

    @functools.wraps(original_copy)
    def controlled_copy(source_root, destination):
        substituted = staged is not None and Path(source_root).resolve() == real_root
        # Preserve A's observation scope; helper unit tests deliberately call
        # this function with missing files and expect its original exception.
        if not substituted and sys._getframe(1).f_code is not build_code:
            return original_copy(source_root, destination)
        extra = {'callable': '_copy_git_visible_output',
                 'substituted': substituted, 'source_root': str(source_root),
                 'real_root': str(real_root), 'staged_root': str(staged) if staged else None,
                 'intervention': 'control substitution, not an observational wrapper' if substituted else None}
        return rec.invoke(original_copy, 'copy',
                          (staged if substituted else source_root, destination), {}, extra=extra)

    rec.undo.append((module, '_copy_git_visible_output', original_copy))
    module._copy_git_visible_output = controlled_copy
    for attr in ('_copy_t080_migration_basis_file',):
        rec.patch(module, attr, lambda a, k, c, attr=attr:
                  ('copy', None, {'callable': attr}) if c is build_code else None)
    rec.patch(module, '_copy_t080_basis_file', lambda a, k, c:
              (('runtime' if Path(a[0]).name == 't080-current-runtime' else 'copy'), None, {})
              if c is build_code else None)

    def in_visible_copy():
        return any(e['name'] == 'copy' and
                   e['extra'].get('callable') == '_copy_git_visible_output'
                   for e in rec.stack())

    rec.patch(module, '_run_git_bytes', lambda a, k, c:
              ('copy.list', None, {'callable': '_run_git_bytes'}) if in_visible_copy() else None)

    def copytree_spec(a, k, c):
        # Recursive shutil.copytree calls are already included in the outer call.
        if any(e['name'] == 'copy.copytree' for e in rec.stack()):
            return None
        if in_visible_copy():
            return 'copy.copytree', None, {'callable': 'shutil.copytree'}
        if c in (build_code, helper_code):
            return ({build_code: 'copy', helper_code: 'base_copy'}[c], None,
                    {'callable': 'shutil.copytree'})
        return None

    rec.patch(module.shutil, 'copytree', copytree_spec)
    rec.patch(module, '_run_git', direct('git'))
    rec.patch(module.migration, 'inspect_receipt_history', direct('history'))
    rec.patch(module.subprocess, 'run', lambda a, k, c:
              ('issue', None, {}) if c is build_code and a and
              list(a[0][:4]) == [sys.executable, '-I', '-B', '-c'] else None)

    def key_lock(args, kwargs, caller):
        if caller is not get_code or len(args) < 2 or args[1] != module.fcntl.LOCK_EX:
            return None
        event = next((e for e in reversed(rec.stack()) if e['name'] == 'get'), None)
        if event is None:
            return None
        key = event['key']
        digest_key = key if len(key) == 5 and key[4] else key[:4]
        expected = Path(event['extra']['base_parent']) / (
            hashlib.sha256(json.dumps(digest_key).encode()).hexdigest() + '.lock')
        if Path(getattr(args[0], 'name', '')) == expected:
            return 'key_wait', key, {'lock_path': str(expected)}
        return None

    rec.patch(module.fcntl, 'flock', key_lock)
    rec.patch(module.migration, 'verify_receipt', lambda a, k, c:
              ('verify', None, {}) if rec.nodeid and
              not any(e['name'] == 'build' for e in rec.stack()) else None)
    rec.installed = True
    event = rec.begin('installed', extra={'module': module.__name__,
                      'targets': [attr for _, attr, _ in rec.undo]})
    rec.end(event)


def maybe_install():
    if not _REC or _REC.installed or _REC.worker == 'controller':
        return
    # pytest may use a package-qualified or importlib-mode name. Never import it.
    matches = {id(m): m for m in list(sys.modules.values()) if m is not None and
               str(getattr(m, '__file__', '')).replace('\\', '/').endswith('/' + _TARGET)}
    if len(matches) == 1:
        install(_REC, next(iter(matches.values())))
    elif len(matches) > 1:
        _REC.record_error(RuntimeError('ambiguous target module'))


def pytest_configure(config):
    global _REC
    _REC = None
    out = os.environ.get('T2273_REPLICA_OUT')
    if not out:
        return
    Path(out).mkdir(parents=True, exist_ok=True)
    _REC = Recorder(out, getattr(config, 'workerinput', {}).get('workerid', 'controller'))


def pytest_sessionstart(session):
    if _REC:
        _REC.started = time.time()


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    maybe_install()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    maybe_install()


def pytest_runtest_logstart(nodeid, location):
    if _REC and _REC.worker != 'controller':
        _REC.nodeid = nodeid
        _REC.test = _REC.begin('test', extra={'nodeid': nodeid})


def pytest_runtest_logfinish(nodeid, location):
    if _REC and _REC.worker != 'controller':
        if _REC.test is not None:
            _REC.end(_REC.test)
        _REC.test, _REC.nodeid = None, ''


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if not _REC:
        return
    event = _REC.begin('sessionfinish', extra={'exitstatus': int(exitstatus),
                       'installed': _REC.installed})
    _REC.end(event)
    for owner, attr, original in reversed(_REC.undo):
        setattr(owner, attr, original)
    if _REC.worker == 'controller':
        try:
            (_REC.out / 'controller.json').write_text(json.dumps({
                'session_start': _REC.started, 'session_finish': time.time(),
                'exitstatus': int(exitstatus), 'argv': list(sys.argv),
                'effective_scheduler': session.config.getoption('dist', default=None),
                'log_lines_source': 'pytest.log'}, indent=2) + '\n')
        except Exception as exc:
            _REC.record_error(exc)
```

## tools/t2273_replica_analyze.py

```python
"""Single-run or A2/X paired observations, not medians; Python 3.10 stdlib."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

PARTS = ('copy', 'git', 'history', 'runtime', 'issue')
MAPPING = {
    'build': '実 builder 全体', 'copy': 'builder 直下の copy 配置 (runtime を除く)',
    'git': 'builder 直下の _run_git (copy/history/issue 内部を除く)',
    'history': 'builder 直下 inspect_receipt_history',
    'runtime': 'builder 直下の t080-current-runtime 配置',
    'issue': '発行 subprocess の起動/import/発行/検証/終了込み',
    'residual': 'build から copy/git/history/runtime/issue の排他区間を引いた残り',
    'key_wait': 'get 内の key lock LOCK_EX 呼び出し (取得即時の builder も含む)',
    'verify': 'test 実行中の実 verify_receipt 呼び出し (発行子内部は issue)',
    'base_copy': 'base→test: helper 直下 copytree',
    'copy.list': '可視 copy の内側の _run_git_bytes (git 可視列挙)',
    'copy.copytree': '可視 copy 内側および builder 直下の実 copytree',
    'copy.other': 'copy 複合区間のうち列挙と copytree を除いた区間',
    'slot_wait': '未計測: A 条件には slot 制限なし',
}


def read(path):
    return json.loads(path.read_text())


def canonical(node):
    return node[:node.rfind('@')] if node.rfind('@') > node.rfind(']') else node


def seconds(span):
    return span['end_mono'] - span['begin_mono']


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('nonfinite or nonnumeric time')
    return value


def validate(spans):
    ids = set()
    for span in spans:
        for clock in ('epoch', 'mono'):
            if finite(span['end_' + clock]) < finite(span['begin_' + clock]):
                raise ValueError('reversed span: end < begin')
        identity = span['extra']['span_id']
        if identity in ids:
            raise ValueError('duplicate span id: ' + identity)
        ids.add(identity)
        if span['key'] is not None and not isinstance(span['key'], list):
            raise ValueError('key must be observed JSON tuple/list')


    by_id = {s['extra']['span_id']: s for s in spans}
    for span in spans:
        parent_id = span['extra'].get('parent_span_id')
        if parent_id is None:
            continue
        if parent_id not in by_id:
            raise ValueError('missing parent span: ' + parent_id)
        parent = by_id[parent_id]
        for clock in ('mono', 'epoch'):
            if (span['begin_' + clock] < parent['begin_' + clock] - 1e-6 or
                    span['end_' + clock] > parent['end_' + clock] + 1e-6):
                raise ValueError('out-of-parent span: ' + span['extra']['span_id'])
        seen = {span['extra']['span_id']}
        cursor = parent_id
        while cursor is not None:
            if cursor in seen:
                raise ValueError('parent cycle')
            seen.add(cursor)
            cursor = by_id[cursor]['extra'].get('parent_span_id')
            if cursor is not None and cursor not in by_id:
                raise ValueError('missing ancestor span: ' + cursor)


def partition(build, children):
    children = [s for s in children if s['name'] in PARTS]
    ordered = sorted(children, key=lambda s: s['begin_mono'])
    previous = build['begin_mono']
    for s in ordered:
        if s['begin_mono'] < previous - 1e-9 or s['end_mono'] > build['end_mono'] + 1e-9:
            raise ValueError('overlapping or out-of-parent build component')
        previous = s['end_mono']
    result = {name: sum(seconds(s) for s in children if s['name'] == name) for name in PARTS}
    result['total'] = seconds(build)
    result['residual'] = result['total'] - sum(result[n] for n in PARTS)
    result['other'] = result['history'] + result['runtime'] + result['residual']
    return result


def junit(path, selected):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
    if len(suites) != 1:
        raise ValueError('expected one pytest JUnit testsuite')
    suite = suites[0]
    wall = finite(float(suite.attrib['time']))
    start = datetime.fromisoformat(suite.attrib['timestamp']).timestamp()
    addresses = {}
    for node in selected:
        address, bracket, parameter = node.partition('[')
        bits = address.split('::')
        classname = bits[0].removesuffix('.py').replace('/', '.')
        if len(bits) > 2:
            classname += '.' + '.'.join(bits[1:-1])
        identity = classname, bits[-1] + bracket + parameter
        if identity in addresses:
            raise ValueError('ambiguous selected JUnit identity')
        addresses[identity] = node
    items = []
    for case in suite.iter('testcase'):
        node = addresses[(case.attrib['classname'], canonical(case.attrib['name']))]
        props = {p.attrib['name']: p.attrib.get('value', '') for p in case.findall('./properties/property')}
        prefix = 'izanagi_acceptance_pairing_v1_'
        duration = finite(float(case.attrib['time']))
        if duration < 0:
            raise ValueError('negative JUnit duration')
        items.append({'nodeid': node, 'duration_s': duration,
                      'worker': props.get(prefix + 'worker'), 'rank': props.get(prefix + 'rank'),
                      'partner': props.get(prefix + 'partner'),
                      'outcome': next((n for n in ('failure', 'error', 'skipped') if case.find(n) is not None), 'passed')})
    if Counter(i['nodeid'] for i in items) != Counter(selected):
        raise ValueError('JUnit/selected multiset mismatch')
    return wall, start, items


def analyze(directory):
    missing = []
    result = {'note': '現行 tip の A 条件 1 走の観測。中央値ではない。',
              'missing': missing, 'component_mapping': MAPPING}
    spans = [json.loads(line) for p in sorted(directory.glob('spans-*.jsonl'))
             for line in p.read_text().splitlines()]
    validate(spans)
    if not spans:
        missing.append('未計測: spans')
    result['record_errors'] = {p.name: read(p) for p in directory.glob('record-error-*.json')}
    if result['record_errors']:
        missing.append('record-error files present')
    children = defaultdict(list)
    for s in spans:
        children[s['extra'].get('parent_span_id')].append(s)
    installed = [s for s in spans if s['name'] == 'installed']
    result['installations'] = installed
    if not installed:
        missing.append('未計測: wrapper installations')
    real = [s for s in spans if s['extra'].get('shared_session') is True]
    keys = sorted({json.dumps(s['key']) for s in real if s['key'] is not None})
    result['key_count'] = len(keys)
    if not keys:
        missing.append('未計測: shared-session keys')
    result['keys'] = []
    for encoded in keys:
        key = json.loads(encoded)
        events = [s for s in real if s['key'] == key]
        builds = [s for s in events if s['name'] == 'build']
        rows = []
        for b in builds:
            direct = children[b['extra']['span_id']]
            parts = partition(b, direct)
            parts['copy_breakdown'] = copy_breakdown(b, spans)
            names = Counter(s['name'] for s in direct)
            absent = [n for n in ('copy', 'git', 'history') if not names[n]]
            if len(key) == 5 and key[2]:
                absent += [n for n in ('issue', 'runtime') if not names[n]]
            for name in absent:
                parts[name] = None
                missing.append(f'未計測: key={encoded} {name}')
            if absent:
                parts['residual'] = parts['other'] = None
            rows.append({'worker': b['worker'], 'pid': b['pid'], 'nodeid': b['extra']['nodeid'],
                         'begin_epoch': b['begin_epoch'], 'end_epoch': b['end_epoch'],
                         'ok': b['ok'], 'seconds': parts})
        waits = []
        for w in (s for s in events if s['name'] == 'key_wait'):
            parent_children = children[w['extra']['parent_span_id']]
            waits.append({'worker': w['worker'], 'pid': w['pid'], 'seconds': seconds(w),
                          'nodeid': w['extra']['nodeid'],
                          'builder_request': any(s['name'] == 'build' for s in parent_children)})
        if not builds:
            missing.append('未計測: no build for key=' + encoded)
        if not waits:
            missing.append('未計測: no flock spans for key=' + encoded)
        if any(not b['ok'] for b in builds):
            missing.append('failed build for key=' + encoded)
        result['keys'].append({'key': key, 'builds': rows, 'flock_waits': waits,
                               'waiter_seconds': sum(w['seconds'] for w in waits if not w['builder_request'])})
    result['nonshared_builds'] = [s for s in spans if s['name'] == 'build' and
                                 not s['extra'].get('shared_session')]
    result['nonshared_builder_components'] = []
    for b in result['nonshared_builds']:
        parts = partition(b, children[b['extra']['span_id']])
        parts['copy_breakdown'] = copy_breakdown(b, spans)
        result['nonshared_builder_components'].append({'key': b['key'],
            'worker': b['worker'], 'nodeid': canonical(b['extra']['nodeid']),
            'ok': b['ok'], 'seconds': parts})
    result['span_exceptions'] = [s for s in spans if not s['ok']]
    consumers = defaultdict(lambda: {'verify_count': 0, 'verify_s': 0.0, 'copytree_count': 0, 'copytree_s': 0.0})
    for s in spans:
        if s['name'] not in ('verify', 'base_copy'):
            continue
        item = consumers[canonical(s['extra']['nodeid'])]
        prefix = 'verify' if s['name'] == 'verify' else 'copytree'
        item[prefix + '_count'] += 1
        item[prefix + '_s'] += seconds(s)
    result['consumers'] = dict(consumers)
    result['consumer_totals'] = {k: sum(v[k] for v in consumers.values()) for k in
                                 ('verify_count', 'verify_s', 'copytree_count', 'copytree_s')}
    for name in ('verify', 'base_copy'):
        if not any(s['name'] == name for s in spans):
            missing.append('未計測: no consumer ' + name + ' spans (zero calls or absent instrumentation)')
    report = read(directory / 'session/report.json')
    run = read(directory / 'run.json')
    controller = read(directory / 'controller.json')
    result.update(run=run, controller=controller)
    if (directory.parent / 'incomplete.json').exists():
        result['incomplete'] = read(directory.parent / 'incomplete.json')
        missing.append('runner incomplete.json present')
    if run.get('rc') != 0 or report.get('pytest_rc') != 0 or controller.get('exitstatus') != 0:
        missing.append('run/report/controller nonzero or missing rc')
    if Counter(report['selected']) != Counter(report['finished']):
        missing.append('selected/finished multiset mismatch')
    wall, start, items = junit(directory / 'session/junit.xml', report['selected'])
    tests = defaultdict(list)
    for s in spans:
        if s['name'] == 'test':
            tests[canonical(s['extra']['nodeid'])].append(s)
    if Counter({k: len(v) for k, v in tests.items()}) != Counter(report['selected']):
        missing.append('test spans/selected multiset mismatch')
    workers = defaultdict(list)
    for item in items:
        matches = tests.get(item['nodeid'], [])
        test = matches[0] if len(matches) == 1 else None
        if test:
            item.update(begin_epoch=test['begin_epoch'], end_epoch=test['end_epoch'],
                        test_span_s=seconds(test))
            if item['worker'] is not None and item['worker'] != test['worker']:
                missing.append('JUnit/span worker mismatch: ' + item['nodeid'])
        else:
            item.update(begin_epoch=None, end_epoch=None, test_span_s=None)
        if item['worker'] is None:
            missing.append('未計測: pairing worker: ' + item['nodeid'])
        if item['rank'] is None:
            missing.append('未計測: pairing rank: ' + item['nodeid'])
        workers[item['worker'] or 'unobserved'].append(item)
    occupancy = report['worker_occupancy']
    for w, entries in workers.items():
        entries.sort(key=lambda x: (x['begin_epoch'] is None, x['begin_epoch'] or 0, x['nodeid']))
        observed = occupancy.get(w)
        if not observed or observed['items'] != len(entries):
            missing.append('worker occupancy item mismatch: ' + w)
        elif abs(sum(i['duration_s'] for i in entries) - observed['duration_s']) > .002 * len(entries):
            missing.append('worker occupancy/JUnit duration mismatch: ' + w)
    maximum = max(occupancy, key=lambda w: occupancy[w]['duration_s']) if occupancy else None
    longest = max(items, key=lambda i: i['duration_s']) if items else None
    om = occupancy[maximum]['duration_s'] if maximum else None
    length = longest['duration_s'] if longest else None
    lw = longest['worker'] if longest else None
    ol = occupancy.get(lw, {}).get('duration_s')
    timeline = report.get('session_timeline', {})
    collection = timeline.get('collection_finished_epoch_s')
    if collection is None:
        missing.append('未計測: collection_finished_epoch_s')
    last = max((s['end_epoch'] for entries in tests.values() for s in entries), default=None)
    pre = collection - start if collection is not None else None
    post = start + wall - last if last is not None else None
    fixed = wall - om if om is not None else None
    result['shard'] = {'W': wall, 'W_start': start, 'W_end': start + wall, 'pre': pre,
        'O_max': om, 'O_max_worker': maximum, 'L': length, 'L_item': longest,
        'L_worker': lw, 'O_L': ol, 'O_max_minus_L': om - length if om is not None and length is not None else None,
        'P_L': ol - length if ol is not None and length is not None else None,
        'F': fixed, 'post': post,
        'F_residual': fixed - pre - post if all(v is not None for v in (fixed, pre, post)) else None,
        'worker_occupancy': occupancy, 'worker_timelines': dict(workers),
        'O_max_timeline': workers.get(maximum, []), 'L_timeline': workers.get(lw, []),
        'occupancy_definition': 'report setup/call/teardown duration sum; not elapsed worker wall',
        'test_bounds_definition': 'worker logstart/logfinish; outside protocol real-repo lock excluded',
        'junit_timestamp_timezone': 'ISO offset if present; otherwise analyzer local timezone'}
    # Keep the actual observed component timeline for the two critical workers.
    result['critical_worker_spans'] = {w: sorted([s for s in spans if s['worker'] == w and
        s['name'] not in ('test', 'installed', 'sessionfinish')], key=lambda s: s['begin_epoch'])
        for w in {maximum, lw} if w is not None}
    log = directory / 'pytest.log'
    result['scheduler_memo_lines'] = [line for line in log.read_text(errors='replace').splitlines()
        if 'IZANAGI_EFFECTIVE_SCHEDULER_V1' in line or 'IZANAGI_MEMO_PREWARM_V1' in line] if log.exists() else []
    enrich(result, spans, directory, start)
    result['complete_observation'] = not missing
    return result


def markdown(result):
    lines = [result['note'], '', '秒は worker 秒。未計測は null。', '',
             '## 共有 base', '', f"観測 key 数: {result.get('key_count', 0)}", '',
             '| key | builder worker | build | copy | git | issue | その他 |',
             '|---|---|---:|---:|---:|---:|---:|']
    for row in result.get('keys', []):
        for b in row['builds']:
            p = b['seconds']
            lines.append('| ' + ' | '.join([json.dumps(row['key']), b['worker']] +
                         [str(p[n]) for n in ('total', 'copy', 'git', 'issue', 'other')]) + ' |')
        lines += ['', 'flock: `' + json.dumps(row['flock_waits'], ensure_ascii=False) + '`', '']
    lines += ['## Consumer', '', '```json', json.dumps(result.get('consumers', {}), indent=2, ensure_ascii=False), '```']
    shard = result.get('shard', {})
    lines += ['', '## Shard', '', '```json', json.dumps({k: v for k, v in shard.items()
        if k not in ('worker_timelines', 'O_max_timeline', 'L_timeline')}, indent=2, ensure_ascii=False), '```']
    for worker, entries in shard.get('worker_timelines', {}).items():
        labels = (' O_max' if worker == shard.get('O_max_worker') else '') + (' L' if worker == shard.get('L_worker') else '')
        lines += ['', '## Timeline ' + worker + labels, '',
                  '| nodeid | rank | duration_s | start epoch | end epoch |', '|---|---:|---:|---:|---:|']
        for item in entries:
            lines.append('| ' + ' | '.join(str(item.get(k)).replace('|', '\\|') for k in
                ('nodeid', 'rank', 'duration_s', 'begin_epoch', 'end_epoch')) + ' |')
    for worker, entries in result.get('critical_worker_spans', {}).items():
        lines += ['', '## 成分 timeline ' + worker, '',
                  '| 成分 | nodeid | key | start epoch | end epoch | 秒 |', '|---|---|---|---:|---:|---:|']
        for s in entries:
            lines.append('| ' + ' | '.join(str(v).replace('|', '\\|') for v in
                (s['name'], s['extra']['nodeid'], json.dumps(s['key']),
                 s['begin_epoch'], s['end_epoch'], seconds(s))) + ' |')
    lines += ['', '## T-2786 成分対応', '', '| 成分 | 区間 |', '|---|---|']
    lines += ['| ' + k + ' | ' + v + ' |' for k, v in MAPPING.items()]
    lines += ['', '## 欠測・record-error', '', '```json', json.dumps({k: result.get(k) for k in
        ('missing', 'record_errors', 'span_exceptions', 'fatal_error', 'scheduler_memo_lines')}, indent=2, ensure_ascii=False), '```']
    lines += diagnostic_markdown(result)
    return '\n'.join(lines) + '\n'


# Priority resolves nested intervals, including nested verifier calls. Every
# elementary segment contributes to exactly one category, never both parent/child.
CATEGORIES = ('flock_wait', 'build.copy.list', 'build.copy.copytree',
              'build.copy.other', 'build.git', 'build.issue', 'build.other',
              'base_copy', 'verify')


def exclusive_segments(begin, end, labeled):
    clipped = [(max(begin, a), min(end, b), label, priority)
               for a, b, label, priority in labeled if min(end, b) > max(begin, a)]
    edges = sorted({begin, end} | {v for a, b, _, _ in clipped for v in (a, b)})
    result = defaultdict(float)
    for a, b in zip(edges, edges[1:]):
        active = [(priority, label) for lo, hi, label, priority in clipped if lo < b and hi > a]
        if active:
            result[max(active)[1]] += b - a
    return dict(result)


def ancestor(span, by_id, name):
    cursor = span['extra'].get('parent_span_id')
    while cursor:
        parent = by_id[cursor]
        if parent['name'] == name:
            return parent
        cursor = parent['extra'].get('parent_span_id')
    return None


def copy_breakdown(build, spans):
    by_id = {s['extra']['span_id']: s for s in spans}
    labeled = []
    for s in spans:
        if ancestor(s, by_id, 'build') is not build:
            continue
        if s['name'] == 'copy':
            labeled.append((s['begin_mono'], s['end_mono'], 'copy.other', 1))
        kind = copy_kind(s)
        if kind:
            labeled.append((s['begin_mono'], s['end_mono'], kind, 2))
    parts = dict.fromkeys(('copy.list', 'copy.copytree', 'copy.other'), 0.0)
    parts.update(exclusive_segments(build['begin_mono'], build['end_mono'], labeled))
    return parts


def copy_kind(span):
    if span['name'] in ('copy.list', 'copy.copytree'):
        return span['name']
    if span['name'] == 'copy' and span['extra'].get('callable') == 'shutil.copytree':
        return 'copy.copytree'
    return None


def concurrency(spans, start):
    events = defaultdict(Counter)
    for s in spans:
        name = 'build' if s['name'] == 'build' else copy_kind(s)
        if name is None:
            continue
        events[s['begin_epoch']][name] += 1
        events[s['end_epoch']][name] -= 1
    counts = Counter({name: 0 for name in ('build', 'copy.list', 'copy.copytree')})
    rows = []
    for epoch, changes in sorted(events.items()):
        counts.update(changes)
        rows.append({'t_s': epoch - start, **dict(counts)})
    return rows


def same_key(left, right):
    # The real get() accepts legacy four-field keys, whose fifth field is False.
    def identity(key):
        return key[:4] if key is not None and len(key) == 5 and not key[4] else key
    return left is not None and right is not None and identity(left) == identity(right)


def item_decomposition(item, spans, by_id, builds, start):
    begin, end = item['begin_epoch'], item['end_epoch']
    row = {k: item[k] for k in ('nodeid', 'rank', 'worker', 'duration_s')}
    row.update(start_s=begin - start if begin is not None else None,
               end_s=end - start if end is not None else None,
               keys=[], flock_dependencies=[])
    if begin is None or end is None:
        row['seconds'] = None
        return row
    events = [s for s in spans if s['worker'] == item['worker'] and
              canonical(s['extra']['nodeid']) == item['nodeid'] and
              s['begin_epoch'] >= begin - 1e-6 and s['end_epoch'] <= end + 1e-6]
    labeled = []
    for s in events:
        if s['key'] is not None and s['key'] not in row['keys']:
            row['keys'].append(s['key'])
        name = s['name']
        build = s if name == 'build' else ancestor(s, by_id, 'build')
        category = None
        priority = 0
        if build:
            category, priority = 'build.other', 10
            if name == 'copy':
                category, priority = 'build.copy.other', 20
            kind = copy_kind(s)
            if kind:
                category, priority = 'build.' + kind, 30
            elif name in ('git', 'issue'):
                category, priority = 'build.' + name, 20
        elif name == 'key_wait':
            category, priority = 'flock_wait', 40
            matches = []
            for b in builds:
                if (not same_key(b['key'], s['key']) or
                        b['extra'].get('shared_session') != s['extra'].get('shared_session') or
                        b['extra'].get('shared_base_parent') != s['extra'].get('shared_base_parent')):
                    continue
                overlap = max(0.0, min(b['end_epoch'], s['end_epoch']) -
                              max(b['begin_epoch'], s['begin_epoch']))
                if overlap:
                    matches.append({'builder_span_id': b['extra']['span_id'],
                                    'worker': b['worker'], 'key': b['key'],
                                    'start_s': b['begin_epoch'] - start,
                                    'end_s': b['end_epoch'] - start, 'overlap_s': overlap})
            overlap = exclusive_segments(s['begin_epoch'], s['end_epoch'],
                [(b['start_s'] + start, b['end_s'] + start, 'matched', 1) for b in matches])
            row['flock_dependencies'].append({'wait_span_id': s['extra']['span_id'],
                'key': s['key'], 'wait_s': seconds(s), 'builders': matches,
                'unmatched_s': max(0.0, s['end_epoch'] - s['begin_epoch'] - overlap.get('matched', 0.0))})
        elif name in ('base_copy', 'verify'):
            category, priority = name, 5
        if category:
            labeled.append((s['begin_epoch'], s['end_epoch'], category, priority))
    parts = dict.fromkeys(CATEGORIES, 0.0)
    parts.update(exclusive_segments(begin, end, labeled))
    parts['remaining'] = item['duration_s'] - sum(parts.values())
    row['seconds'] = parts
    row['junit_minus_test_span_s'] = item['duration_s'] - item['test_span_s']
    return row


def sample_rates(samples):
    """Rates use consecutive observations; resets and unavailable counters are missing."""
    rows = []
    previous = None
    for sample in sorted(samples, key=lambda s: s['mono']):
        finite(sample['mono']); finite(sample['epoch'])
        row = {'epoch': sample['epoch'], 'cpu_usage': None, 'iowait': None,
               'run_queue': (sample.get('loadavg') or {}).get('running'), 'lustre_ops_s': {}}
        if previous is not None:
            dt = sample['mono'] - previous['mono']
            if dt <= 0:
                raise ValueError('duplicate/reversed resource sample time')
            before, after = previous.get('cpu'), sample.get('cpu')
            if before and after and before.keys() == after.keys():
                delta = {k: after[k] - before[k] for k in after}
                total = sum(delta.values())
                if min(delta.values()) >= 0 and total > 0:
                    row['cpu_usage'] = 1 - delta['idle'] / total
                    row['iowait'] = delta['iowait'] / total
            for path, entry in sample.get('lustre', {}).items():
                old = previous.get('lustre', {}).get(path, {}).get('counters', {})
                for op, value in entry.get('counters', {}).items():
                    if op in old and value >= old[op]:
                        # Keep client paths separate: llite and mdc count different layers.
                        row['lustre_ops_s'][path + ':' + op] = (value - old[op]) / dt
        rows.append(row)
        previous = sample
    return rows


def cpu_class(ratio):
    if ratio is None:
        return '未計測'
    if ratio >= .8:
        return 'CPU 実行が支配'
    if ratio <= .3:
        return '待ち (IO・metadata・run queue) が支配'
    return '混在'


def resource_table(spans, by_id, rates, start):
    rows = []
    for s in spans:
        build = ancestor(s, by_id, 'build')
        name = copy_kind(s) or s['name']
        if build is None or name not in ('copy.list', 'copy.copytree', 'git', 'issue'):
            continue
        selected = [r for r in rates if s['begin_epoch'] <= r['epoch'] <= s['end_epoch']]
        averages, counts = {}, {}
        for field in ('cpu_usage', 'iowait', 'run_queue'):
            values = [r[field] for r in selected if r[field] is not None]
            counts[field] = len(values)
            averages[field] = sum(values) / len(values) if values else None
        ops = sorted({op for r in selected for op in r['lustre_ops_s']})
        averages['lustre_ops_s'] = {}
        counts['lustre_ops_s'] = {}
        for op in ops:
            values = [r['lustre_ops_s'][op] for r in selected if op in r['lustre_ops_s']]
            averages['lustre_ops_s'][op] = sum(values) / len(values)
            counts['lustre_ops_s'][op] = len(values)
        wall = seconds(s)
        cpu = s['extra'].get('cpu', {})
        own = sum(cpu['self'].values()) / wall if wall > 0 and 'self' in cpu else None
        both = own + sum(cpu['children'].values()) / wall if own is not None and 'children' in cpu else None
        rows.append({'span_id': s['extra']['span_id'], 'builder_span_id': build['extra']['span_id'],
                     'worker': s['worker'], 'key': s['key'], 'component': name,
                     'start_s': s['begin_epoch'] - start, 'end_s': s['end_epoch'] - start,
                     'wall_s': wall, 'cpu': cpu or None, 'self_cpu_wall': own,
                     'self_children_cpu_wall': both, 'self_class': cpu_class(own),
                     'self_children_class': cpu_class(both), 'sample_count': len(selected),
                     'available_counts': counts, 'sample_mean': averages})
    return rows


def enrich(result, spans, directory, start):
    missing = result['missing']
    by_id = {s['extra']['span_id']: s for s in spans}
    builds = [s for s in spans if s['name'] == 'build']
    result['concurrency_timeline'] = concurrency(spans, start)
    result['critical_worker_decomposition'] = {}
    shard = result['shard']
    for w in dict.fromkeys((shard['O_max_worker'], shard['L_worker'])):
        if w is None:
            continue
        rows = [item_decomposition(i, spans, by_id, builds, start)
                for i in shard['worker_timelines'].get(w, [])]
        totals = {k: sum(r['seconds'][k] for r in rows if r['seconds'] is not None)
                  for k in (*CATEGORIES, 'remaining')}
        for row in rows:
            if row['seconds'] is None:
                missing.append('unobserved critical item: ' + row['nodeid'])
            elif row['seconds']['remaining'] < -.002:
                missing.append('negative JUnit residual: ' + row['nodeid'])
        result['critical_worker_decomposition'][w] = {'items': rows, 'totals_s': totals,
            'largest_component': max(totals, key=totals.get) if rows else None}
    sample_path = directory / 'samples.jsonl'
    samples = [json.loads(line) for line in sample_path.read_text().splitlines()] if sample_path.exists() else []
    if not samples:
        missing.append('未計測: resource samples')
    result['resource_sampling'] = {'count': len(samples),
        'complete': bool(samples) and not any(s.get('missing') for s in samples) and
                    not (directory / 'sample-error.json').exists(),
        'missing': [{'epoch': s['epoch'], 'missing': s['missing']} for s in samples if s.get('missing')],
        'error': read(directory / 'sample-error.json') if (directory / 'sample-error.json').exists() else None}
    if not result['resource_sampling']['complete']:
        missing.append('未計測: resource counters or sampler errors (see resource_sampling)')
    result['builder_resources'] = resource_table(spans, by_id, sample_rates(samples), start)
    if any('cpu' not in s['extra'] for s in spans):
        missing.append('未計測: span CPU')
    visible = [s for s in spans if s['name'] == 'copy' and
               s['extra'].get('callable') == '_copy_git_visible_output']
    if builds and not visible:
        missing.append('未計測: visible copy spans')
    for s in visible:
        children = [c for c in spans if c['extra'].get('parent_span_id') == s['extra']['span_id']]
        for name in ('copy.list', 'copy.copytree'):
            if s['ok'] and not any(c['name'] == name for c in children):
                missing.append('未計測: ' + name + ' for ' + s['extra']['span_id'])
        if s['ok'] and s['extra'].get('visible_path_count') is None:
            missing.append('未計測: visible_path_count for ' + s['extra']['span_id'])
    result['visible_copies'] = [{'span_id': s['extra']['span_id'], 'key': s['key'],
        'worker': s['worker'], 'visible_path_count': s['extra'].get('visible_path_count'),
        'visible_path_sha256': s['extra'].get('visible_path_sha256'),
        'substituted': s['extra'].get('substituted'),
        'source_root': s['extra'].get('source_root'),
        'real_root': s['extra'].get('real_root'),
        'staged_root': s['extra'].get('staged_root'),
        'builder_span_id': (ancestor(s, by_id, 'build') or {}).get('extra', {}).get('span_id')}
        for s in visible]
    result['diagnostic_notes'] = [
        '1 走の観測であり中央値ではない。原因の断定はしない。',
        '時系列は JUnit timestamp 基準秒、イベント境界の直後の同時本数。全 observed builder を含む。',
        'copy.copytree は可視 copy の子 span と builder 直下 copytree を含む。再帰 copytree は外側だけ。',
        'copy.list は _run_git_bytes の時間。Python 側の集合処理等は copy その他。',
        'item 分解は span epoch 境界の排他和。残りは JUnit time との差で、丸めと計器 overhead も含む。',
        'flock は実 LOCK_EX 時間。依存 builder との重複と未対応時間を併記し、待ち全体を構築と同一視しない。',
        'RUSAGE_CHILDREN は終了・回収済み子 process の CPU。self/children とも process 単位で、並行 thread の CPU も含む。',
        '資源標本は node/client 全体であり当該 span 専用ではない。Lustre は client path/層を合算しない。',
        '平均は区間内に終点のある 1 Hz 標本の算術平均。counter 率は直前標本との差で区間外を含みうる。',
        '短区間に標本がなければ null。CPU 使用率は 1-idle 比で iowait を含む。counter reset は欠測。',
    ]


def diagnostic_markdown(result):
    lines = ['', '## 診断注記', ''] + result.get('diagnostic_notes', [])
    lines += ['', '## 同時本数 (JUnit 基準秒)', '',
              '| t_s | builder | copy.list | copy.copytree |', '|---:|---:|---:|---:|']
    for r in result.get('concurrency_timeline', []):
        lines.append('| ' + ' | '.join(str(r[k]) for k in ('t_s', 'build', 'copy.list', 'copy.copytree')) + ' |')
    for w, data in result.get('critical_worker_decomposition', {}).items():
        fields = ('nodeid', 'rank', 'start_s', 'end_s', 'keys')
        lines += ['', '## 排他分解 ' + w, '',
                  '| ' + ' | '.join((*fields, *CATEGORIES, 'remaining')) + ' |',
                  '| ' + ' | '.join('---' for _ in range(len(fields) + len(CATEGORIES) + 1)) + ' |']
        for r in data['items']:
            values = [r[k] for k in fields] + [(r['seconds'] or {}).get(k) for k in (*CATEGORIES, 'remaining')]
            lines.append('| ' + ' | '.join(str(v).replace('|', '\\|') for v in values) + ' |')
        lines += ['', '```json', json.dumps(data, indent=2, ensure_ascii=False), '```']
    lines += ['', '## Builder 資源標本・CPU 比', '',
              '| span | component | wall | CPU使用率 | iowait | run queue | self/wall | self+children/wall | self区分 | self+children区分 | Lustre op/s |',
              '|---|---|---:|---:|---:|---:|---:|---:|---|---|---|']
    for r in result.get('builder_resources', []):
        avg = r['sample_mean']
        values = [r['span_id'], r['component'], r['wall_s'], avg['cpu_usage'], avg['iowait'],
                  avg['run_queue'], r['self_cpu_wall'], r['self_children_cpu_wall'],
                  r['self_class'], r['self_children_class'], json.dumps(avg['lustre_ops_s'])]
        lines.append('| ' + ' | '.join(str(v).replace('|', '\\|') for v in values) + ' |')
    lines += ['', '資源欠測: `' + json.dumps(result.get('resource_sampling'), ensure_ascii=False) + '`',
              '', '可視 path 件数: `' + json.dumps(result.get('visible_copies'), ensure_ascii=False) + '`']
    return lines


def difference(a, x):
    return {'A2': a, 'X': x, 'A2_minus_X': a - x if a is not None and x is not None else None}


def pair_builders(result):
    rows = {}
    entries = list(result['keys'])
    nonshared = defaultdict(list)
    for b in result.get('nonshared_builder_components', []):
        if b['ok']:
            identity = json.dumps({'shared_session': False, 'key': b['key'], 'nodeid': b['nodeid']}, sort_keys=True)
            nonshared[identity].append(b)
    entries += [{'key': json.loads(identity), 'builds': builders} for identity, builders in nonshared.items()]
    for row in entries:
        key = json.dumps(row['key'], sort_keys=True)
        builders = row['builds']
        # Multiple builders are retained; never silently pick one for a key.
        rows[key] = {'workers': [b['worker'] for b in builders], 'count': len(builders)}
        for name in ('build', 'copy', 'copy.list', 'copy.copytree', 'git', 'issue'):
            values = [b['seconds']['copy_breakdown'].get(name) if name.startswith('copy.')
                      else b['seconds'].get('total' if name == 'build' else name) for b in builders]
            rows[key][name] = sum(values) if values and all(v is not None for v in values) else None
    return rows


def analyze_pair(directory):
    runs = {name: analyze(directory / name) for name in ('A2', 'X')}
    staging = read(directory / 'staging.json')
    a, x = runs['A2'], runs['X']
    checks = {}
    checks['runner_complete'] = not (directory / 'incomplete.json').exists()
    checks['staging'] = (staging.get('valid') is True and staging.get('visible_set_equal') is True
                         and staging.get('bytes_equal') is True)
    checks['rc'] = all(r['run'].get('rc') == 0 and r['controller'].get('exitstatus') == 0
                       and read(directory / name / 'session/report.json').get('pytest_rc') == 0
                       for name, r in runs.items())
    outcomes = {}
    for name, r in runs.items():
        outcomes[name] = Counter((i['nodeid'], i['outcome'])
            for entries in r['shard']['worker_timelines'].values() for i in entries)
    checks['outcomes_equal'] = bool(outcomes['A2']) and outcomes['A2'] == outcomes['X']
    checks['record_error_zero'] = all(not r['record_errors'] for r in runs.values())
    guards = {name: {phase: read(directory / name / ('env-' + phase + '.json'))
                     for phase in ('before', 'after')} for name in runs}
    checks['clean'] = all(g.get('git_status_line_count') == 0
                          for phases in guards.values() for g in phases.values())
    heads = [g.get('HEAD') for phases in guards.values() for g in phases.values()]
    heads += [r['run'].get('HEAD') for r in runs.values()] + [staging.get('HEAD')]
    checks['same_HEAD'] = bool(heads[0]) and all(h == heads[0] for h in heads)
    checks['others_zero'] = all(g.get('others') == 0 and g.get('stale_pytest') == 0
                                for phases in guards.values() for g in phases.values())
    checks['observations_present'] = all(not [m for m in r['missing']
        if not m.startswith(('未計測: resource samples', '未計測: resource counters'))]
        for r in runs.values())
    visible = {}
    valid_digests = True
    for name, r in runs.items():
        copies = r['visible_copies']
        spans = [json.loads(line) for path in (directory / name).glob('spans-*.jsonl')
                 for line in path.read_text().splitlines()]
        build_ids = {s['extra']['span_id'] for s in spans if s['name'] == 'build' and s['ok']}
        observed_ids = {c['builder_span_id'] for c in copies if c['builder_span_id'] is not None}
        if not build_ids or build_ids != observed_ids:
            valid_digests = False
        visible[name] = Counter()
        for c in copies:
            digest, count = c['visible_path_sha256'], c['visible_path_count']
            if (not isinstance(digest, str) or len(digest) != 64 or
                    any(ch not in '0123456789abcdef' for ch in digest) or
                    not isinstance(count, int) or isinstance(count, bool) or count < 0):
                valid_digests = False
            visible[name][(json.dumps(c['key']), count, digest)] += 1
        checks[name + '_source_control'] = bool(copies) and all(
            c['substituted'] is (name == 'X') and c['source_root'] is not None and
            c['real_root'] is not None and Path(c['source_root']).resolve() == Path(c['real_root']).resolve() and
            (name != 'X' or c['staged_root'] == staging.get('staged_root')) for c in copies)
    checks['visible_digest_equal_all_builders'] = valid_digests and visible['A2'] == visible['X']
    checks['visible_matches_staging'] = all(
        c['visible_path_count'] == staging.get('visible_path_count') and
        c['visible_path_sha256'] == staging.get('visible_path_sha256')
        for r in runs.values() for c in r['visible_copies'])
    # Verify that only session/output routing and the registered intervention differ.
    def normalized(r):
        argv = [arg for arg in r['run'].get('argv', []) if not arg.startswith('--junitxml=')]
        env = dict(r['run'].get('env', {}))
        for key in ('T2273_REPLICA_OUT', 'T2273_LOCAL_OUTPUT_SOURCE', 'IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1'):
            env.pop(key, None)
        return argv, env
    checks['argv_env_equal'] = bool(a['run'].get('argv')) and bool(a['run'].get('env')) and normalized(a) == normalized(x)
    checks['separate_sessions'] = (bool(a['run'].get('session_root')) and bool(x['run'].get('session_root'))
                                   and a['run']['session_root'] != x['run']['session_root'])
    for name, r in runs.items():
        env = r['run'].get('env', {})
        spec = json.loads(env.get('IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1', '{}'))
        session = r['run'].get('session_root')
        argv = r['run'].get('argv', [])
        checks[name + '_shard_spec'] = spec == {'session_root': session, 'shard_count': 3, 'shard_index': 0}
        checks[name + '_junit_route'] = [v for v in argv if v.startswith('--junitxml=')] == [
            '--junitxml=' + str(Path(session or '') / 'shard-0/junit.xml')]
        checks[name + '_intervention_env'] = env.get('T2273_LOCAL_OUTPUT_SOURCE') == (
            staging.get('staged_root') if name == 'X' else None)
    metrics = {name: difference(a['shard'][field], x['shard'][field])
               for name, field in (('W_0', 'W'), ('O_max', 'O_max'), ('L', 'L'), ('pre', 'pre'), ('post', 'post'))}
    workers = {name: {k: r['shard'][k] for k in ('O_max_worker', 'L_worker')} for name, r in runs.items()}
    builders = {name: pair_builders(r) for name, r in runs.items()}
    checks['builder_keys_equal'] = bool(builders['A2']) and builders['A2'].keys() == builders['X'].keys()
    comparisons = []
    for key in sorted(builders['A2'].keys() | builders['X'].keys()):
        left, right = builders['A2'].get(key, {}), builders['X'].get(key, {})
        comparisons.append({'key': json.loads(key), 'A2_workers': left.get('workers'),
            'X_workers': right.get('workers'), 'A2_count': left.get('count'), 'X_count': right.get('count'),
            'seconds': {part: difference(left.get(part), right.get(part))
                        for part in ('build', 'copy', 'copy.list', 'copy.copytree', 'git', 'issue')}})
    checks['one_builder_per_key'] = all(row['A2_count'] == row['X_count'] == 1 for row in comparisons)
    delta = metrics['W_0']['A2_minus_X']
    ratio = delta / metrics['W_0']['A2'] if metrics['W_0']['A2'] > 0 else None
    staging_wall = finite(staging['wall_s'])
    checks['staging_time'] = staging_wall >= 0
    valid = all(checks.values())
    copy_shorter = bool(comparisons) and all(row['seconds']['copy']['A2_minus_X'] is not None and
                                           row['seconds']['copy']['A2_minus_X'] > 0 for row in comparisons)
    classification = ('10 % 以上の短縮' if ratio >= .1 else
                      '10 % 以上の増加' if ratio <= -.1 else '10 % 未満: 変化なし') if ratio is not None else '未計測'
    maximum = x['shard']['O_max_worker']
    critical = {name: r['critical_worker_decomposition'] for name, r in runs.items()}
    result = {'note': 'A2 → staging → X の1対。D357の1走比較、有意差判定ではない。Xは後走のwarmを受ける。',
        'validity': {'valid': valid, 'checks': checks, 'failed': [k for k, v in checks.items() if not v]},
        'metrics_s': metrics, 'workers': workers, 'builders': comparisons,
        'critical_worker_decomposition': critical,
        'X_maximum_worker': maximum,
        'X_largest_component': critical['X'].get(maximum, {}).get('largest_component'),
        'staging': staging, 'staging_wall_s': staging_wall,
        'delta_W_0_s': delta, 'delta_W_0_fraction': ratio,
        'delta_W_0_minus_staging_s': delta - staging_wall if delta is not None else None,
        'D357_classification': classification if valid else 'X 無効 (参考値: ' + classification + ')',
        'builder_copy_shorter_all': copy_shorter,
        'recommendation': ('複製元の局所化を次の一手として提示' if ratio is not None and ratio >= .1 and copy_shorter else
                           '効果を確認できなかった。issue は効果未測の候補') if valid else 'X 無効: 効果判定を行わない',
        'span_exceptions': {name: r['span_exceptions'] for name, r in runs.items()},
        'resource_sampling': {name: r['resource_sampling'] for name, r in runs.items()},
        'visible_copies': {name: r['visible_copies'] for name, r in runs.items()},
        'outcomes': {name: [{'nodeid': node, 'outcome': outcome, 'count': count}
                            for (node, outcome), count in sorted(values.items())] for name, values in outcomes.items()},
        'builder_scope': 'All successful shared/nonshared builders; expected failed calls remain in span_exceptions and outcome comparison.',
        'guards': guards, 'missing': {name: r['missing'] for name, r in runs.items()},
        'complete_observation': valid and all(r['complete_observation'] for r in runs.values())}
    return result


def pair_markdown(result):
    lines = [result['note'], '', '差は A2 − X、秒。worker は各走の観測値。', '']
    for key in ('validity', 'metrics_s', 'workers', 'builders', 'critical_worker_decomposition',
                'X_maximum_worker', 'X_largest_component', 'staging_wall_s', 'delta_W_0_s',
                'delta_W_0_fraction', 'delta_W_0_minus_staging_s', 'D357_classification',
                'builder_copy_shorter_all', 'recommendation', 'staging', 'resource_sampling',
                'visible_copies', 'outcomes', 'guards', 'builder_scope', 'span_exceptions', 'missing', 'fatal_error'):
        if key in result:
            lines += ['## ' + key, '', '```json', json.dumps(result[key], indent=2, ensure_ascii=False), '```', '']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--run-dir')
    source.add_argument('--pair-dir')
    parser.add_argument('--markdown', required=True)
    parser.add_argument('--json', required=True)
    args = parser.parse_args()
    try:
        result = analyze_pair(Path(args.pair_dir)) if args.pair_dir else analyze(Path(args.run_dir))
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        result = {'note': 'A 条件 1 走の観測。中央値ではない。',
                  'complete_observation': False, 'fatal_error': str(exc)}
    Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    Path(args.markdown).write_text(pair_markdown(result) if args.pair_dir else markdown(result))
    rc = 0 if result['complete_observation'] else 1
    print(json.dumps({'rc': rc, 'key_count': result.get('key_count'),
                      'missing': result.get('missing'), 'fatal_error': result.get('fatal_error')}, ensure_ascii=False))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
```
