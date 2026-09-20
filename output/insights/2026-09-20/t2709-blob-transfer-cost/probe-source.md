# probe 本体の逐語 (tools/t2709_blob_transfer_probe.py、repo へは残さない)

- 作成: Codex `role=author` (段 5、959 行)。段 6 fix なし。親は編集していない。
- 保全先: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2709-blob-transfer-cost/probe/tools/t2709_blob_transfer_probe.py`
- sha256: `0e6759231b0e92d082196872288b978ea01ff153cecd77ad701d0de945fcef18` (959 行)。本走 (request 11899.nqsv) と login の selftest / hold-session-only はこの bytes で走った。
- 起動形: `python3 -B <絶対 path> --source-root <wave worktree> --work-parent /tmp --out <job dir>/run1/result.json --rounds 5 --transfer-trials 3 --require-local-fs` (計算ノード generic dispatch、cwd = source-root)。

```python
"""Disposable T-2709 probe. Never commit; measure only on compute nodes.

選定・移送・不足 object の生成・index の検証と保存に必要な処理を timed 外へ移して、自己完結経路の総費用と記述してはならない。production の status 引数・環境・変更検出を弱めてはならない。失格・timeout・欠測を黙って除外または再試行し、成功分だけで事前登録判定を満たしたと報告してはならない。main 初回を cold と断定し、per-base の差を受入 wall の改善へ読み替えてはならない。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter_ns

TIMEOUT = 1200.0
STATUS = ('-c', 'core.useReplaceRefs=false', '-c', 'core.fsmonitor=false',
          '-c', 'core.untrackedCache=false', 'status', '--porcelain=v1', '-z',
          '--untracked-files=all', '--ignore-submodules=none')
MESSAGE = ('-m', 'T080 migration basis', '-m', 'AI-Agent: none')
LIMITATIONS = [
    '初回移送・main 初回とも cold 未保証。per-base 差は受入 wall の改善ではない。',
    'C2 は参照 index を無料で使う下限模型で production 設計ではない。',
    'C2 は複製済み worktree を変更せず空 stat を通常設定で検証する経路の参考費用。',
    'checkout-index 経路は未測定。copy 後 status は副次量。',
    '失格・timeout・欠測を保持し、主判定の成功 round 数を明示する。',
    'selftest は仕様 v2 に従い submodule なし。submodule 検査は本走のみ。',
]


def now():
    return datetime.now(timezone.utc).isoformat()


def seconds(start):
    return (perf_counter_ns() - start) / 1e9


def git_env(commit=False):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    if commit:
        for role in ('AUTHOR', 'COMMITTER'):
            for key, value in [('NAME', 'T080 E2E Human'),
                               ('EMAIL', 't080-e2e@example.invalid'),
                               ('DATE', '2026-09-20T00:00:00+0900')]:
                env['GIT_' + role + '_' + key] = value
    return env


def require(condition, failures, check, **details):
    if not condition:
        failures.append({'check': check, **details})
    return bool(condition)


def git(root, *args, data=None, records=None, label=None):
    argv = ['git', *map(str, args)]
    record = {'argv': argv, 'cwd': str(root), 'rc': None, 'stderr': ''}
    if records is not None:
        records.append(record)
    env = git_env('commit' in args or 'commit-tree' in args)
    start = perf_counter_ns()
    try:
        result = subprocess.run(argv, cwd=root, input=data, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env,
                                timeout=TIMEOUT, check=False)
        elapsed = seconds(start)
        record.update(rc=result.returncode, stderr=result.stderr[:4096].decode('utf-8', 'replace'),
                      stdout_hex=result.stdout.hex(), elapsed_s=elapsed)
        return result
    except subprocess.TimeoutExpired as exc:
        record.update(timeout=True, elapsed_s=seconds(start),
                      stderr=(exc.stderr or b'')[:4096].decode('utf-8', 'replace'))
        raise
    finally:
        record.setdefault('elapsed_s', seconds(start))
        if label:
            record['label'] = label


def checked_git(root, *args, data=None, records=None, label=None):
    result = git(root, *args, data=data, records=records, label=label)
    if result.returncode:
        raise RuntimeError(f'git {args}: rc={result.returncode}: {result.stderr[:4096]!r}')
    return result.stdout


def status_prod(root, records=None):
    return checked_git(root, *STATUS, records=records)


def save(output, destination):
    output['ok'] = not output['failures']
    destination.write_text(json.dumps(output, ensure_ascii=True, indent=2) + '\n')


def fstype(path):
    best = None
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left, right = line.split(' - ', 1)
        mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), left.split()[4])
        if path.is_relative_to(Path(mount)) and (best is None or len(mount) > best[0]):
            best = (len(mount), right.split()[0])
    if best is None:
        raise ValueError('no mountinfo entry for work-root')
    return best[1]


def hold_session(source, work, output):
    """Import only inside a normally enforcing collection session; execute no tests."""
    import pytest
    module_name = 'orchestrator.tests.test_s8b_oracle_driver'
    module_path = source / 'orchestrator/tests/test_s8b_oracle_driver.py'
    argv = [str(module_path), '--collect-only', '-q', '-p', 'no:cacheprovider',
            '-k', 't2709_no_such_node_zzz']
    record = {'argv': argv, 'rc': None}
    output['hold_session'] = record

    class LoadBuilder:
        def pytest_sessionstart(self, session):
            import importlib
            importlib.import_module(module_name)

    start = perf_counter_ns()
    try:
        record['rc'] = int(pytest.main(argv, plugins=[LoadBuilder()]))
    except Exception as exc:
        output['failures'].append({'check': 'hold session exception', 'message': str(exc)})
    finally:
        record['elapsed_s'] = seconds(start)
        record['temp_environment'] = {k: os.environ.get(k) for k in ('TMPDIR', 'TEMP', 'TMP')}
        record['git_environment_keys'] = sorted(k for k in os.environ if k.startswith('GIT_'))
        record['environment_preserved'] = (
            all(v == str(work / 'tmp') for v in record['temp_environment'].values())
            and not record['git_environment_keys'])
        require(record['environment_preserved'], output['failures'], 'hold environment changed')
    require(record['rc'] in (0, 5), output['failures'], 'hold session rc', rc=record['rc'])
    builder = sys.modules.get(module_name)
    module_file = getattr(builder, '__file__', None)
    record['module_loaded'] = builder is not None
    record['module_file'] = str(Path(module_file).resolve()) if module_file else None
    require(record['module_loaded'], output['failures'], 'hold module missing')
    require(record['module_file'] == str(module_path.resolve()), output['failures'],
            'hold module source mismatch')
    return None if output['failures'] else builder


def build_once(builder, work, output):
    """Fork the imported builder with a hard 1800s process-tree deadline."""
    context = multiprocessing.get_context('fork')
    reader, writer = context.Pipe(duplex=False)

    def child():
        os.setsid()
        reader.close()
        original_run = subprocess.run

        def bounded_run(*args, **kwargs):
            kwargs['timeout'] = min(kwargs.get('timeout') or TIMEOUT, TIMEOUT)
            argv = args[0] if args else kwargs.get('args', [])
            if isinstance(argv, (list, tuple)) and argv and argv[0] == 'git':
                kwargs['env'] = git_env('commit' in argv or 'commit-tree' in argv)
            return original_run(*args, **kwargs)

        subprocess.run = bounded_run
        try:
            (work / 'base').mkdir()
            root, _, _ = builder._build_t080_stub_free_e2e_repo(work / 'base', issue_receipt=False)
            writer.send({'root': str(root)})
        except BaseException as exc:
            writer.send({'error': type(exc).__name__, 'message': str(exc)})
        finally:
            writer.close()

    process = context.Process(target=child)
    start = perf_counter_ns()
    process.start()
    writer.close()
    try:
        if not reader.poll(1800):
            raise subprocess.TimeoutExpired('builder', 1800)
        result = reader.recv()
        process.join(timeout=5)
        if process.is_alive():
            raise subprocess.TimeoutExpired('builder exit', 1800)
        if 'error' in result:
            raise RuntimeError('builder: ' + repr(result))
        if process.exitcode:
            raise RuntimeError(f'builder exit {process.exitcode}')
        return Path(result['root'])
    finally:
        output['build_s'] = seconds(start)
        if process.is_alive():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                process.kill()
            process.join(timeout=5)
        reader.close()


def parse_index(raw):
    entries = []
    for item in raw.split(b'\0'):
        if item:
            meta, path = item.split(b'\t', 1)
            mode, oid, stage = meta.decode().split()
            if stage != '0':
                raise ValueError('unmerged index')
            entries.append((mode, oid, stage, os.fsdecode(path)))
    return entries


def lines(values):
    values = list(values)
    if any('\n' in value or '\r' in value for value in values):
        raise ValueError('newline path cannot use --stdin-paths')
    if any(value.startswith('"') for value in values):
        raise ValueError('quoted path unsupported by this disposable probe')
    return b''.join(os.fsencode(value) + b'\n' for value in values)


def batch_present(source, oids, records=None):
    oids = sorted(set(oids))
    raw = checked_git(source, 'cat-file', '--batch-check', data=lines(oids), records=records)
    present, missing = [], []
    for line in raw.decode().splitlines():
        fields = line.split()
        (missing if fields[-1] == 'missing' else present).append(fields[0])
    if len(present) + len(missing) != len(oids):
        raise ValueError('incomplete batch-check output')
    return present, missing


def reachable(root, commit, records=None):
    return {line.split()[0].decode() for line in checked_git(
        root, 'rev-list', '--objects', 'HEAD', records=records).splitlines()} - {commit}


def count_objects(root, records=None):
    raw = checked_git(root, 'count-objects', '-v', records=records).decode()
    counts = {}
    for line in raw.splitlines():
        key, value = line.split(': ', 1)
        if key == 'alternate':
            counts.setdefault('alternates', []).append(value)
        else:
            counts[key] = int(value)
    return counts


def reference(root, source, work, basis, paths, commits, output):
    records = []
    raw = checked_git(root, 'ls-files', '-s', '-z', records=records)
    entries = parse_index(raw)
    commit = checked_git(root, 'rev-parse', 'HEAD', records=records).decode().strip()
    blobs = sorted({oid for mode, oid, _, _ in entries if mode in ('100644', '100755', '120000')})
    present, missing = batch_present(source, blobs, records)
    regular = [p for m, _, _, p in entries if m in ('100644', '100755')]
    missing_set = set(missing)
    missing_entries = [(p, oid) for m, oid, _, p in entries if oid in missing_set]
    ref = dict(tree=checked_git(root, 'rev-parse', 'HEAD^{tree}', records=records).decode().strip(),
               commit=commit, raw=raw, entries=entries, blobs=blobs, present=present,
               missing=missing_entries, paths=regular, basis=basis, in_repo_sources=sorted(paths),
               recorded_commits=sorted(commits), reachable=reachable(root, commit, records),
               config=(root / '.git/config').read_bytes())
    output['reference'] = dict(tree=ref['tree'], builder_commit=commit, index_entries=len(entries),
        regular=len(regular), symlink=sum(m == '120000' for m, _, _, _ in entries),
        gitlink=sum(m == '160000' for m, _, _, _ in entries),
        bytes=sum((root / p).stat().st_size for p in regular), ref_blobs=len(blobs),
        present=len(present), missing=len(missing), missing_paths=missing_entries,
        in_repo_sources=len(paths), real_basis=basis, recorded_commits=len(commits),
        ref_reachable=len(ref['reachable']), count_objects=count_objects(root, records), records=records)
    os.rename(root / '.git', work / 'git-ref')
    if (work / 'git-ref/modules').exists():
        os.rename(work / 'git-ref/modules', work / 'modules-keep')
    return ref


def reset(root, work, ref, records):
    modules = root / '.git/modules'
    if modules.exists():
        os.rename(modules, work / 'modules-keep')
    if (root / '.git').exists():
        shutil.rmtree(root / '.git')
    checked_git(root, 'init', '-q', records=records)
    (root / '.git/config').write_bytes(ref['config'])
    if (work / 'modules-keep').exists():
        os.rename(work / 'modules-keep', modules)
    if checked_git(root, 'config', '--int', '--get', 'gc.auto', records=records).strip() != b'0':
        raise ValueError('gc.auto must be 0')
    # Required config check is setup; no status/refresh precedes the first step.


def transfer(source, root, oids, pack_args, row):
    payload = lines(sorted(set(oids)))
    commands = [(['git', 'pack-objects', '--stdout', *pack_args, '--delta-base-offset'], source),
                (['git', 'index-pack', '--stdin', '-v'], root)]
    records = [{'argv': argv, 'cwd': str(cwd), 'rc': None, 'stderr': ''} for argv, cwd in commands]
    row['pipe'] = records
    row['transfer_oid_count'] = len(set(oids))
    children = []
    env = git_env()
    # File-backed stdin/stderr/stdout prevent pipe deadlocks and unbounded memory.
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as err1, \
            tempfile.TemporaryFile() as err2, tempfile.TemporaryFile() as out:
        inp.write(payload)
        inp.seek(0)
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = perf_counter_ns()
        try:
            producer = subprocess.Popen(commands[0][0], cwd=source, stdin=inp,
                                        stdout=subprocess.PIPE, stderr=err1, env=env)
            children.append(producer)
            consumer = subprocess.Popen(commands[1][0], cwd=root, stdin=producer.stdout,
                                        stdout=out, stderr=err2, env=env)
            children.append(consumer)
            producer.stdout.close()
            for proc in children:
                proc.wait(timeout=max(0.001, TIMEOUT - seconds(start)))
        except subprocess.TimeoutExpired:
            row['timeout'] = True
            raise
        finally:
            for proc in children:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=TIMEOUT)
            row['transfer_s'] = seconds(start)
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            row['cpu_s'] = {'utime': after.ru_utime - before.ru_utime,
                            'stime': after.ru_stime - before.ru_stime}
            for index, handle in enumerate((err1, err2)):
                handle.seek(0)
                records[index].update(stderr=handle.read(4096).decode('utf-8', 'replace'),
                                      elapsed_s=row['transfer_s'],
                                      rc=children[index].returncode if index < len(children) else None)
            out.seek(0)
            row['pipe_stdout_hex'] = out.read().hex()
            row['pack_bytes'] = sum(p.stat().st_size for p in (root / '.git/objects/pack').glob('*.pack'))
    if any(record['rc'] != 0 for record in records):
        raise RuntimeError('transfer pipe nonzero rc')


def select(source, ref, row):
    start = perf_counter_ns()
    records = row.setdefault('selection_records', [])
    try:
        raw = checked_git(source, 'ls-files', '-s', '-z', '--', 'orchestrator', 'output', records=records)
        candidates = {p: (m, oid) for m, oid, _, p in parse_index(raw)}
        if ref['in_repo_sources']:
            raw = checked_git(source, 'ls-tree', '-r', '-z', ref['basis'], '--',
                              *ref['in_repo_sources'], records=records)
            for entry in raw.split(b'\0'):
                if entry:
                    meta, path = entry.split(b'\t', 1)
                    mode, kind, oid = meta.decode().split()
                    if kind == 'blob':
                        candidates[os.fsdecode(path)] = (mode, oid)
        # Only known copied regular paths enter C1; no reference OIDs are consulted.
        chosen = {candidates[p][1] for p in ref['paths'] if p in candidates}
        present, missing = batch_present(source, chosen, records)
        row['selection'] = {'no_candidate_paths': sum(p not in candidates for p in ref['paths']),
                            'missing': len(missing), 'transfer_oids': len(present)}
        return present
    finally:
        row['select_s'] = seconds(start)


def step(root, row, label, *args, data=None):
    records = row.setdefault('records', [])
    try:
        return checked_git(root, *args, data=data, records=records, label=label)
    finally:
        row[label + '_s'] = records[-1]['elapsed_s']


def run_variant(root, source, ref, pack_args, row, stat_probe=None):
    variant = row['variant']
    start = perf_counter_ns()
    included = []
    try:
        if variant == 'C1':
            oids = select(source, ref, row)
            included.append('select')
            transfer(source, root, oids, pack_args, row)
            included.append('transfer')
        elif variant == 'C2':
            transfer(source, root, ref['present'], pack_args, row)
            included.append('transfer')
            included.append('generate')
            if ref['missing']:
                generated = step(root, row, 'generate', 'hash-object', '-w', '--stdin-paths',
                                 data=lines(p for p, _ in ref['missing'])).decode().splitlines()
                if generated != [oid for _, oid in ref['missing']]:
                    raise ValueError('generated-oid-mismatch')
            else:
                row['generate_s'] = 0.0
            step(root, row, 'index_info', 'update-index', '-z', '--index-info', data=ref['raw'])
            included.append('index_info')
            if stat_probe:
                stat_probe('index-info')
            tree = step(root, row, 'write_tree', 'write-tree').decode().strip()
            included.append('write_tree')
            commit = step(root, row, 'commit_tree', 'commit-tree', tree, *MESSAGE).decode().strip()
            included.append('commit_tree')
            step(root, row, 'update_ref', 'update-ref', 'HEAD', commit)
            included.append('update_ref')
            if stat_probe:
                stat_probe('before-refresh')
            step(root, row, 'refresh', 'update-index', '--refresh')
            included.append('refresh')
            if stat_probe:
                stat_probe('after-refresh')
        if variant in ('A', 'C1'):
            step(root, row, 'add', 'add', '-A')
            included.append('add')
            step(root, row, 'commit', 'commit', '-q', *MESSAGE)
            included.append('commit')
        row['status1_hex'] = step(root, row, 'status1', *STATUS).hex()
        included.append('status1')
        row['primary_outer_s'] = seconds(start)
        row['total_s'] = sum(row[key + '_s'] for key in included)
        row['python_and_preparation_s'] = row['primary_outer_s'] - row['total_s']
        row['status2_hex'] = step(root, row, 'status2', *STATUS).hex()
    finally:
        row['variant_outer_s'] = seconds(start)
        row['total_components'] = included
        row.setdefault('total_s', None)


def check_trial(root, ref, row, anchor):
    records = row.setdefault('check_records', [])
    checks = row.setdefault('checks', {})
    row['tree'] = checked_git(root, 'rev-parse', 'HEAD^{tree}', records=records).decode().strip()
    row['commit'] = checked_git(root, 'rev-parse', 'HEAD', records=records).decode().strip()
    checks['i'] = row['tree'] == ref['tree']
    checks['ii'] = anchor is None or row['commit'] == anchor
    checks['iii'] = row.get('status1_hex') == ''
    checks['iv'] = reachable(root, row['commit'], records) == ref['reachable']
    checks['v'] = git(root, 'fsck', '--connectivity-only', records=records).returncode == 0
    try:
        (root / '.git/objects/info/alternates').lstat()
        checks['vi'] = False
    except FileNotFoundError:
        checks['vi'] = True
    if row['variant'] in ('C1', 'C2'):
        objects = []
        valid = True
        indexes = sorted((root / '.git/objects/pack').glob('*.idx'))
        for idx in indexes:
            result = git(root, 'verify-pack', '-v', str(idx), records=records)
            valid = valid and result.returncode == 0
            for line in result.stdout.decode().splitlines():
                fields = line.split()
                if fields and re.fullmatch(r'[0-9a-f]{40,64}', fields[0]):
                    objects.append(fields[1])
        checks['vii'] = bool(indexes) and valid and all(t == 'blob' for t in objects) and len(objects) == row['transfer_oid_count']
        row['pack_object_types'] = objects
    else:
        checks['vii'] = True
    checks['viii'] = True
    for oid in ref['recorded_commits']:
        result = git(root, 'cat-file', '-e', oid, records=records)
        if result.returncode == 0:
            checks['viii'] = False
    row['count_objects'] = count_objects(root, records)
    files = [Path(directory) / name for directory, _, names in os.walk(root / '.git/objects') for name in names]
    row['objects'] = {'bytes': sum(p.stat().st_size for p in files), 'files': len(files)}
    row.setdefault('pack_bytes', sum(p.stat().st_size for p in (root / '.git/objects/pack').glob('*.pack')))
    row['fail_reasons'].extend('check-' + key for key, value in checks.items() if not value)
    row['failed'] = bool(row['fail_reasons'])


def copy_timed(source, target):
    start = perf_counter_ns()
    shutil.copytree(source, target, symlinks=True)
    return seconds(start)


def mutations(root, paths, row, submodule=True):
    checks = {}
    records = row.setdefault('records', [])
    path = root / paths[0]
    original = path.read_bytes()
    mode = path.stat().st_mode
    expected = b' M ' + os.fsencode(paths[0]) + b'\0'
    try:
        path.write_bytes(original + b'!')
        checks['content_dirty'] = expected in status_prod(root, records)
    finally:
        path.write_bytes(original)
    checks['content_restored'] = status_prod(root, records) == b''
    try:
        path.chmod(mode ^ 0o111)
        checks['mode_dirty'] = expected in status_prod(root, records)
    finally:
        path.chmod(mode)
    checks['mode_restored'] = status_prod(root, records) == b''
    if submodule:
        sub = root / 'external/ccbench'
        entries = parse_index(checked_git(sub, 'ls-files', '-s', '-z', records=records))
        relative = next(p for m, _, _, p in entries if m in ('100644', '100755'))
        path = sub / relative
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'!')
            checks['submodule_dirty'] = b' M external/ccbench\0' in status_prod(root, records)
        finally:
            path.write_bytes(original)
        checks['submodule_restored'] = status_prod(root, records) == b''
    row['mutation_checks'] = checks
    return all(checks.values())


def variant_checks(root, work, ref, submodule=True):
    row = {'failed': False, 'fail_reasons': [], 'records': []}
    hidden = work / 'git-ref-hidden'
    copy = work / 'fixture-copy'
    try:
        os.rename(work / 'git-ref', hidden)
        try:
            row['copy_fixture_s'] = copy_timed(root, copy)
            for i in (1, 2):
                row[f'copy_status{i}_hex'] = step(copy, row, f'copy_status{i}', *STATUS).hex()
            _, missing = batch_present(copy, ref['blobs'], row['records'])
            row['copy_missing_blobs'] = missing
            row['ix'] = not missing and all(row[f'copy_status{i}_hex'] == '' for i in (1, 2))
        finally:
            if copy.exists():
                shutil.rmtree(copy)
            os.rename(hidden, work / 'git-ref')
        row['x'] = mutations(root, ref['paths'], row, submodule)
        row['fail_reasons'] = [key for key in ('ix', 'x') if not row[key]]
    except Exception as exc:
        row['fail_reasons'].append('timeout' if isinstance(exc, subprocess.TimeoutExpired) else str(exc))
    row['failed'] = bool(row['fail_reasons'])
    return row


def fail_exception(row, exc):
    row['failed'] = True
    row.setdefault('fail_reasons', []).append('timeout' if isinstance(exc, subprocess.TimeoutExpired)
                                            else type(exc).__name__ + ': ' + str(exc))


def finish_row(output, row, category, destination):
    if row['failed']:
        output['failures'].append({'check': category, 'round': row.get('round'),
                                   'variant': row.get('variant'), 'reasons': row['fail_reasons']})
    save(output, destination)


def pretrials(args, root, source, work, ref, output):
    output['transfer_pretrials'] = []
    configs = [[], ['--window=0', '--depth=0']]
    for index, config in enumerate([[]] + configs * args.transfer_trials):
        row = {'pack_args': config, 'failed': False, 'fail_reasons': [], 'setup_records': []}
        if index == 0:
            row['cold_guaranteed'] = False
            output['initial_transfer'] = row
        else:
            output['transfer_pretrials'].append(row)
        try:
            reset(root, work, ref, row['setup_records'])
            transfer(source, root, ref['present'], config, row)
        except Exception as exc:
            fail_exception(row, exc)
        finish_row(output, row, 'transfer pretrial', args.out)
    medians = []
    for config in configs:
        rows = [r for r in output['transfer_pretrials'] if r['pack_args'] == config]
        values = [r['transfer_s'] for r in rows if not r['failed']]
        medians.append(statistics.median(values) if values else None)
    complete = all(not r['failed'] for r in output['transfer_pretrials'])
    # Incomplete comparisons cannot justify selecting the fastest survivors.
    chosen = configs[1] if complete and medians[1] < medians[0] else configs[0]
    output['chosen_pack_args'] = chosen
    output['pack_choice'] = {'default_median_s': medians[0], 'w0_median_s': medians[1],
                             'complete': complete, 'reason': 'median, tie default' if complete else 'incomplete: default fallback; failed probe'}
    return chosen


def summarize(output, rounds):
    trials = output['trials']
    result = {'variants': {}, 'd_r': [], 'rule_version':
              'median(d)<=-1.0 and count(d<0)>=4: 改善候補; median(d)>=1.0 and count(d>0)>=4: 悪化観測; else 未確定; n<5: threshold=n-1',
              'requested_rounds': rounds, 'failed_trials': sum(r['failed'] for r in trials)}
    for variant in ('A', 'C1', 'C2'):
        values = [r['total_s'] for r in trials if r['variant'] == variant and not r['failed']]
        result['variants'][variant] = {'n': len(values), 'median': statistics.median(values) if values else None,
                                      'min': min(values) if values else None, 'max': max(values) if values else None}
    for r in range(1, rounds + 1):
        pair = {t['variant']: t for t in trials if t['round'] == r and t['variant'] in ('A', 'C1')}
        valid = len(pair) == 2 and not any(t['failed'] for t in pair.values())
        result['d_r'].append({'round': r, 'd_s': pair['C1']['total_s'] - pair['A']['total_s'] if valid else None})
    values = [r['d_s'] for r in result['d_r'] if r['d_s'] is not None]
    n = len(values)
    median = statistics.median(values) if values else None
    threshold = n - 1 if n < 5 else 4
    verdict = '未確定'
    if n and median <= -1 and sum(d < 0 for d in values) >= threshold:
        verdict = '改善候補'
    elif n and median >= 1 and sum(d > 0 for d in values) >= threshold:
        verdict = '悪化観測'
    result.update(successful_rounds=n, median_d_s=median, sign_threshold=threshold,
                  negative=sum(d < 0 for d in values), positive=sum(d > 0 for d in values),
                  verdict=verdict, failures_total=len(output['failures']),
                  incomplete=n != rounds, first_main_C1_slower=bool(result['d_r'] and
                      result['d_r'][0]['d_s'] is not None and result['d_r'][0]['d_s'] > 0))
    output['summary'] = result


def measure(args, source, work, output):
    builder = hold_session(source, work, output)
    if builder is None:
        return
    if builder.ROOT.resolve() != source:
        raise ValueError('builder ROOT mismatch')
    root = build_once(builder, work, output)
    known = json.loads((source / builder.migration.KNOWN_AXES_REL).read_text())
    receipt = json.loads((source / builder.migration.RECEIPT_REL).read_text())
    paths, commits = set(), set()

    def collect(value, receipt_mode=False):
        if isinstance(value, dict):
            if not receipt_mode and isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
                if not value['path'].startswith('external/ccbench/'):
                    paths.add(value['path'])
            for child in value.values():
                collect(child, receipt_mode)
        elif isinstance(value, list):
            for child in value:
                collect(child, receipt_mode)
        elif receipt_mode and isinstance(value, str) and re.fullmatch('[0-9a-fA-F]{40}', value):
            commits.add(value.lower())

    collect(known)
    collect(receipt, True)
    ref = reference(root, source, work, receipt['migration_basis_commit'], paths, commits, output)
    output['fixture_root'] = str(root)
    chosen = pretrials(args, root, source, work, ref, output)
    output.update(trials=[], hash_pass=[], variant_checks={})
    anchor = None
    for round_number in range(1, args.rounds + 1):
        hashing = {'round': round_number, 'records': [], 'failed': False, 'fail_reasons': []}
        output['hash_pass'].append(hashing)
        try:
            if any('\n' in p or '\r' in p for p in ref['paths']):
                hashing['skipped'] = 'newline in path'
            else:
                step(root, hashing, 'hash_pass', 'hash-object', '--stdin-paths', data=lines(ref['paths']))
        except Exception as exc:
            fail_exception(hashing, exc)
        finish_row(output, hashing, 'hash_pass', args.out)
        order = ['A', 'C1', 'C2']
        shift = (round_number - 1) % 3
        order = order[shift:] + order[:shift]
        for position, variant in enumerate(order, 1):
            row = {'round': round_number, 'position': position, 'variant': variant,
                   'failed': False, 'fail_reasons': [], 'checks': {}, 'setup_records': []}
            output['trials'].append(row)
            try:
                reset(root, work, ref, row['setup_records'])
                run_variant(root, source, ref, chosen, row)
                check_trial(root, ref, row, anchor)
                target = work / f'gitcopy-{len(output["trials"])}'
                try:
                    row['gitcopy_s'] = copy_timed(root / '.git', target)
                finally:
                    if target.exists():
                        shutil.rmtree(target)
                if not row['failed']:
                    if variant not in output['variant_checks']:
                        output['variant_checks'][variant] = variant_checks(root, work, ref)
                    vc = output['variant_checks'][variant]
                    if vc['failed']:
                        row['fail_reasons'].append('variant checks: ' + repr(vc['fail_reasons']))
                        row['failed'] = True
                    elif anchor is None:
                        anchor = row['commit']
            except Exception as exc:
                fail_exception(row, exc)
            finish_row(output, row, 'main trial', args.out)
            summarize(output, args.rounds)
            save(output, args.out)


def selftest(args, work, output):
    test = {'checks': {}, 'trials': [], 'negative_trials': [], 'records': []}
    output['selftest'] = test
    base = work / 'selftest'
    base.mkdir()
    source = base / 'source'
    source.mkdir()
    records = test['records']

    def check(name, condition, **details):
        test['checks'][name] = require(condition, output['failures'], 'selftest ' + name, **details)

    def init(root):
        checked_git(root, 'init', '-q', records=records)
        checked_git(root, 'config', 'gc.auto', '0', records=records)
        checked_git(root, 'config', 'user.name', 'T080 E2E Human', records=records)
        checked_git(root, 'config', 'user.email', 't080-e2e@example.invalid', records=records)

    init(source)
    (source / 'orchestrator').mkdir()
    contents = {'.gitignore': 'ignored\n', 'ignored': 'tracked but ignored\n',
                'basis': 'old basis\n', 'target': 'target', 'one': 'one\n', 'two': 'two\n'}
    for path, content in contents.items():
        (source / 'orchestrator' / path).write_text(content)
    (source / 'orchestrator/link').symlink_to('target')
    checked_git(source, 'add', '-A', records=records)
    checked_git(source, 'add', '-f', '--', 'orchestrator/ignored', records=records)
    checked_git(source, 'commit', '-q', *MESSAGE, records=records)
    basis = checked_git(source, 'rev-parse', 'HEAD', records=records).decode().strip()
    (source / 'orchestrator/basis').write_text('new basis\n')
    checked_git(source, 'add', '-A', records=records)
    checked_git(source, 'commit', '-q', *MESSAGE, records=records)
    source_head = checked_git(source, 'rev-parse', 'HEAD', records=records).decode().strip()
    source_entries = parse_index(checked_git(source, 'ls-files', '-s', '-z', records=records))
    check('source_fixture_shape', sum(m in ('100644', '100755') for m, _, _, _ in source_entries) == 6
          and sum(m == '120000' for m, _, _, _ in source_entries) == 1
          and any(p == 'orchestrator/ignored' for _, _, _, p in source_entries))
    root = base / 'fixture'
    shutil.copytree(source, root, symlinks=True, ignore=shutil.ignore_patterns('.git'))
    (root / 'orchestrator/basis').write_text('old basis\n')
    (root / 'orchestrator/one').write_text('fixture-only bytes\n')
    init(root)
    checked_git(root, 'add', '-A', records=records)
    checked_git(root, 'commit', '-q', *MESSAGE, records=records)
    ref = reference(root, source, work, basis, {'orchestrator/basis'}, {source_head}, output)
    check('one_missing_blob', len(ref['missing']) == 1 and ref['missing'][0][0] == 'orchestrator/one')
    # The ignored source entry is intentionally absent from the fresh A reference.
    check('ignored_not_in_reference', 'orchestrator/ignored' not in ref['paths'])
    stat = {}
    test['stat'] = stat

    def debug_values():
        raw = checked_git(root, 'ls-files', '--debug', records=records).decode()
        values = [(int(a), int(b)) for a, b in re.findall(r'(?:ctime|mtime): (\d+):(\d+)', raw)]
        sizes = [int(v) for v in re.findall(r'size: (\d+)', raw)]
        return raw, values, sizes

    def stat_probe(stage):
        index = root / '.git/index'
        if stage == 'index-info':
            raw, times, sizes = debug_values()
            stat['index_info_debug'] = raw
            check('empty_stat', len(times) == 2 * len(ref['entries']) and len(sizes) == len(ref['entries'])
                  and all(a == b == 0 for a, b in times) and all(v == 0 for v in sizes))
        elif stage == 'before-refresh':
            before = index.read_bytes()
            stat['before_refresh_sha256'] = hashlib.sha256(before).hexdigest()
            statuses, unchanged = [], []
            for _ in range(2):
                statuses.append(status_prod(root, records).hex())
                unchanged.append(index.read_bytes() == before)
            stat['status_hex'] = statuses
            stat['status_index_unchanged'] = unchanged
            check('optional_status_does_not_write_index', all(unchanged) and statuses == ['', ''])
        else:
            raw, times, sizes = debug_values()
            stat['refreshed_debug'] = raw
            stat['after_refresh_sha256'] = hashlib.sha256(index.read_bytes()).hexdigest()
            check('refresh_saves_stat', len(times) == 2 * len(ref['entries'])
                  and all(a > 0 for a, _ in times) and len(sizes) == len(ref['entries'])
                  and all(v > 0 for v in sizes)
                  and stat['before_refresh_sha256'] != stat['after_refresh_sha256'])

    anchor = None
    for variant in ('A', 'C1', 'C2'):
        row = {'variant': variant, 'failed': False, 'fail_reasons': [], 'setup_records': []}
        test['trials'].append(row)
        try:
            reset(root, work, ref, row['setup_records'])
            run_variant(root, source, ref, [], row, stat_probe if variant == 'C2' else None)
            check_trial(root, ref, row, anchor)
            if anchor is None and not row['failed']:
                anchor = row['commit']
            vc = variant_checks(root, work, ref, submodule=False)
            row['variant_checks'] = vc
            check(variant + '_independence_and_mutations', not vc['failed'])
        except Exception as exc:
            fail_exception(row, exc)
        check(variant + '_invariants', not row['failed'], reasons=row['fail_reasons'])
        save(output, args.out)
    good = [r for r in test['trials'] if not r['failed']]
    check('three_way_tree_commit', len(good) == 3 and len({r['tree'] for r in good}) == 1
          and len({r['commit'] for r in good}) == 1)
    by_variant = {r['variant']: r for r in good}
    if 'A' in by_variant and 'C1' in by_variant:
        # Unique reachable non-blobs are exactly trees plus the fixture commit.
        kinds = checked_git(root, 'cat-file', '--batch-check',
                            data=lines(ref['reachable']), records=records).decode().splitlines()
        overhead = 1 + sum(line.split()[1] == 'tree' for line in kinds)
        a_count = by_variant['A']['count_objects']['count']
        c_count = by_variant['C1']['count_objects']['count']
        test['loose_counts'] = {'A': a_count, 'C1': c_count, 'tree_commit_count': overhead}
        check('packed_add_avoids_loose', c_count <= 1 + overhead)
        check('unpacked_add_control', a_count == len(ref['blobs']) + overhead and a_count > c_count)
    else:
        check('packed_add_avoids_loose', False)
        check('unpacked_add_control', False)

    for label, expected in [('alternates', 'vi'), ('wrong-tree', 'i'),
                            ('mixed-pack', 'vii'), ('recorded-commit', 'viii')]:
        row = {'variant': 'C2', 'case': label, 'failed': False, 'fail_reasons': [], 'setup_records': []}
        test['negative_trials'].append(row)
        altered = dict(ref)
        alternate = root / '.git/objects/info/alternates'
        path = root / 'orchestrator/one'
        original = path.read_bytes()
        try:
            reset(root, work, ref, row['setup_records'])
            run_variant(root, source, ref, [], row)
            if label == 'alternates':
                alternate.write_text(str(source / '.git/objects') + '\n')
            elif label == 'wrong-tree':
                path.write_bytes(original + b'!')
                checked_git(root, 'add', '-A', records=records)
                checked_git(root, 'commit', '-q', *MESSAGE, records=records)
            elif label == 'mixed-pack':
                extra = {}
                transfer(source, root, [source_head], [], extra)
                row['negative_transfer'] = extra
                row['transfer_oid_count'] += 1
            else:
                altered['recorded_commits'] = [checked_git(root, 'rev-parse', 'HEAD', records=records).decode().strip()]
            check_trial(root, altered, row, anchor)
            check('reject_' + label, row['failed'] and row['checks'].get(expected) is False)
        except Exception as exc:
            fail_exception(row, exc)
            check('reject_' + label, False, error=str(exc))
        finally:
            if alternate.exists():
                alternate.unlink()
            path.write_bytes(original)
        save(output, args.out)
    test['fstype'] = fstype(work)
    check('mountinfo', bool(test['fstype']))


def main():
    global TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--work-parent', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=5)
    parser.add_argument('--transfer-trials', type=int, default=3)
    parser.add_argument('--subprocess-timeout', type=float, default=1200)
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--require-local-fs', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--selftest', action='store_true')
    mode.add_argument('--hold-session-only', action='store_true')
    args = parser.parse_args()
    output = {'started_at': now(), 'failures': [], 'limitations': LIMITATIONS,
              'parameters': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              'environment': {'hostname': socket.gethostname(), 'python': sys.version,
                              'cpu_count': os.cpu_count(),
                              'affinity_count': len(os.sched_getaffinity(0)),
                              'loadavg_start': os.getloadavg(),
                              'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'build_s': None, 'hold_session': None}
    destination = None
    work = None
    try:
        if not all(p.is_absolute() for p in (args.source_root, args.work_parent, args.out)):
            raise ValueError('all paths must be absolute')
        source = args.source_root.resolve()
        parent = args.work_parent.resolve()
        candidate = args.out.resolve()
        if Path.cwd().resolve() != source:
            raise ValueError('cwd must equal source-root')
        if parent.is_relative_to(source) or candidate.is_relative_to(source):
            raise ValueError('work-parent/out must be outside source-root')
        if candidate == parent or source.is_relative_to(candidate):
            raise ValueError('out must not contain source-root or equal work-parent')
        if not parent.is_dir() or not candidate.parent.is_dir():
            raise ValueError('work-parent and out parent must already exist')
        destination = candidate
        args.out = destination
        if args.rounds < 1 or args.transfer_trials < 1 or not (0 < args.subprocess_timeout < float('inf')):
            raise ValueError('rounds/trials/timeout must be positive and finite')
        TIMEOUT = args.subprocess_timeout
        for key in list(os.environ):
            if key.startswith('GIT_') or key == 'PYTEST_XDIST_TESTRUNUID':
                del os.environ[key]
        if os.environ.get('IZANAGI_RUN_GROWTH_HELD_TESTS'):
            raise ValueError('growth-held override must be absent')
        work = Path(tempfile.mkdtemp(prefix='t2709-', dir=parent)).resolve()
        if work.is_relative_to(source) or source.is_relative_to(work):
            raise ValueError('work-root overlaps source-root')
        temp = work / 'tmp'
        temp.mkdir()
        for key in ('TMPDIR', 'TEMP', 'TMP'):
            os.environ[key] = str(temp)
        tempfile.tempdir = str(temp)
        sys.path.insert(0, str(source))
        sys.dont_write_bytecode = True
        env = output['environment']
        env.update(work_root=str(work), fstype=fstype(work),
                   temp_environment={k: os.environ[k] for k in ('TMPDIR', 'TEMP', 'TMP')})
        if args.require_local_fs and env['fstype'] in ('tmpfs', 'lustre', 'nfs', 'nfs4'):
            raise ValueError('require-local-fs refused fstype=' + env['fstype'])
        if not (args.selftest or args.hold_session_only) and socket.gethostname().startswith('pegasus0'):
            raise ValueError('measure forbidden on Pegasus login node')
        records = output.setdefault('environment_records', [])
        env['git_version'] = checked_git(source, '--version', records=records).decode().strip()
        env['source_head'] = checked_git(source, 'rev-parse', 'HEAD', records=records).decode().strip()
        env['source_common_dir'] = checked_git(source, 'rev-parse', '--git-common-dir', records=records).decode().strip()
        env['source_count_objects'] = count_objects(source, records)
        save(output, destination)
        if args.selftest:
            selftest(args, work, output)
        elif args.hold_session_only:
            hold_session(source, work, output)
        else:
            measure(args, source, work, output)
    except Exception as exc:
        output['failures'].append({'check': 'probe exception', 'type': type(exc).__name__,
                                   'reason': 'timeout' if isinstance(exc, subprocess.TimeoutExpired) else str(exc)})
    finally:
        if work is not None and not args.keep_work:
            try:
                shutil.rmtree(work)
                output['work_removed'] = True
            except Exception as exc:
                output['failures'].append({'check': 'cleanup', 'message': str(exc)})
        output['finished_at'] = now()
        output['environment']['loadavg_end'] = os.getloadavg()
        output['ok'] = not output['failures']
        try:
            if destination is None:
                raise ValueError('unsafe output path; emitting JSON to stdout')
            save(output, destination)
        except Exception as exc:
            output['failures'].append({'check': 'write JSON', 'message': str(exc)})
            output['ok'] = False
            print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0 if output['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
```
