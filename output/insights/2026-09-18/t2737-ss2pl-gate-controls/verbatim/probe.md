# probe 本体の逐語 (`t2737_gate_probe.py`、Codex `role=author` が段 5 で作成し段 6 fix2 で warm-up の base dir 作成を追加。repo へは commit しない)

sha256 `6ffae7beaa263fca7b769a6ef90e5d0273241793451c57b917bd837bcd96a61f`、38,745 bytes。

```python
#!/usr/bin/env python3
"""T-2737 mechanism probe. Run with python3 -B and absolute paths.

Shadow TPCC results do not establish the production YCSB stock comparison.
No trials. Only login-precheck is allowed on a Pegasus login node.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from uuid import uuid4

ABORT = ('#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB\n'
         '// The workload owns the increment.\n#else\n'
         '  ++result_->local_abort_counts_;\n#endif\n')
MACROS = ('SS2PL_LOCK_IMPL', 'SS2PL_LOCK_KIND', 'SS2PL_DLR', 'SS2PL_WFG_DIAG')
AXES = ('impl', 'kind', 'dlr', 'wfg')
REGISTRIES = ('O', 'T+', 'T-')
REASONS = dict(O='owner-tu-unresolved', C='configure-failed',
               D='dependency-closure-drift', A='compile-command-drift',
               M='stock-inert-mismatch', B='preprocess-bytes-identical',
               E='requested-default-preprocess-different',
               I='stock-inert-preprocess-identical', P='preprocess-failed')


def registry_block():
    # The complete fixed four-entry block, not a line-number or permissive match.
    return ''.join(
        f'    "{macro}": DefineSpec(\n'
        '        ROUTE_CMAKE_CACHE, _SS2PL_OWNER, "ycsb_ss2pl.exe",\n'
        '        "patches/ss2pl-lock-protocol-study.patch",\n'
        + ('        (("SS2PL_LOCK_IMPL", "1"),),\n' if macro == 'SS2PL_LOCK_KIND' else '')
        + '    ),\n' for macro in MACROS).encode()


def shadow_bytes(repo_bytes, registry):
    block = registry_block()
    if registry not in REGISTRIES or repo_bytes.count(block) != 1:
        raise ValueError('unknown registry or canonical four-entry block changed')
    replacement = block
    if registry != 'O':
        replacement = replacement.replace(b'"ycsb_ss2pl.exe"', b'"tpcc_ss2pl.exe"')
    if registry == 'T-':
        replacement = replacement.replace(b'(("SS2PL_LOCK_IMPL", "1"),)', b'()')
    return repo_bytes.replace(block, replacement, 1)


def accept_shadow(repo_bytes, candidate, registry):
    if candidate != shadow_bytes(repo_bytes, registry):
        raise ValueError('shadow differs from the entire expected byte sequence')
    return True


def cells_and_order():
    cells, order = [], []
    def group(patch, registry, arm, codes, staging='warm', axes=AXES):
        for axis, code in zip(axes, codes):
            ident = '.'.join((patch, registry, arm, axis, staging))
            cells.append(dict(id=ident, patch=patch, registry=registry, arm=arm,
                              axis=axis, staging=staging,
                              expected_reason=REASONS[code],
                              expected_if_s_mismatch=REASONS['M'] if code == 'I' else None,
                              expected_meaning='meaning-witness-undeclared',
                              prediction_condition='S bytes restored; root-location-only also allowed'
                              if code == 'I' else None))
            order.append(ident)
    group('current', 'O', 'phase1', 'PPPP', 'pristine')
    group('revs', 'T-', 'S', 'PPPP', 'pristine')
    order.append('warm-up')
    group('current', 'O', 'phase1', 'DEAD')
    group('revs', 'T-', 'S', 'IIII')
    group('revs', 'T+', 'phase1', 'E', axes=('kind',))
    group('revs', 'T-', 'phase1', 'EBEE')
    group('abort-unconditional', 'T-', 'S', 'MMMM')
    order.extend(('plain-build.S', 'plain-build.phase1'))
    group('current', 'O', 'S', 'OCOO')
    group('current', 'T-', 'S', 'MMMM')
    group('revs', 'O', 'S', 'OCOO')
    group('revs', 'O', 'phase1', 'EEEE')
    group('revs', 'T+', 'S', 'ICII')
    return cells, order


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def file_info(path):
    return dict(path=str(path), realpath=str(path.resolve()), **digest(path.read_bytes()))


def config_info(staging):
    p = staging / 'masstree/config.h'
    return dict(path=str(p), realpath=str(p.resolve()), exists=p.exists(),
                **(digest(p.read_bytes()) if p.exists() else {}))


def write_result(path, document):
    data = json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid4().hex}.tmp')
    try:
        with temporary.open('x') as out:
            out.write(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def command(argv, *, cwd=None, timeout=300, stdout_path=None):
    start = time.monotonic()
    p = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True, timeout=timeout)
    result = dict(argv=[str(x) for x in argv], cwd=str(cwd) if cwd else None,
                  rc=p.returncode, seconds=time.monotonic()-start,
                  stderr=p.stderr.decode('utf-8', 'replace'))
    if stdout_path is None:
        result['stdout'] = p.stdout.decode('utf-8', 'replace')
    else:
        stdout_path.write_bytes(p.stdout)
        result['stdout_file'] = file_info(stdout_path)
    return result


def require_command(result):
    if result['rc']:
        raise RuntimeError(f"command rc={result['rc']}: {result['argv']}\n{result['stderr']}")
    return result


def discover_pbs_jobid(repo, hostname):
    if os.environ.get('PBS_JOBID'):
        return dict(candidate=os.environ['PBS_JOBID'], source='environment', confirmed=False)
    candidates = []
    for path in (repo / 'output/pegasus-dispatch').glob('*/compute-visible.json'):
        try:
            r = json.loads(path.read_text())
            if (r.get('schema_version') == 'pegasus-compute-visible/v1'
                    and r.get('hostname') == hostname and isinstance(r.get('pbs_jobid'), str)
                    and r['pbs_jobid']):
                candidates.append((path.stat().st_mtime_ns, str(path), r['pbs_jobid']))
        except (OSError, ValueError, AttributeError):
            continue
    if candidates:
        mtime, path, candidate = max(candidates)
        return dict(candidate=candidate, source=path, mtime_ns=mtime, confirmed=False)
    return dict(candidate='unknown', source='unknown', confirmed=False)


def parse_patch(data):
    files = {}
    name = None
    hunk = None
    for line in data.decode().splitlines(keepends=True):
        if line.startswith('diff --git '):
            m = re.fullmatch(r'diff --git a/(.+) b/(.+)\n', line)
            if not m or m[1] != m[2] or m[1] in files:
                raise ValueError('unsupported patch path')
            name = m[1]
            files[name] = []
            hunk = None
        elif line.startswith('@@ '):
            m = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if not m or name is None:
                raise ValueError('bad hunk')
            old_count = int(m[2]) if m[2] is not None else 1
            new_count = int(m[4]) if m[4] is not None else 1
            hunk = [int(m[1]), old_count, new_count, []]
            files[name].append(hunk)
        elif hunk is not None and line[:1] in (' ', '+', '-'):
            hunk[3].append(line)
        elif line.startswith('\\'):
            if hunk is None or not hunk[3] or line.rstrip() != '\\ No newline at end of file':
                raise ValueError('unsupported patch marker')
            hunk[3][-1] = hunk[3][-1].removesuffix('\n')
    return files


def patch_postimages(left, right):
    """Reconstruct both patches on the same symbolic unchanged base, without tmp."""
    a, b = parse_patch(left), parse_patch(right)
    if set(a) != set(b):
        raise ValueError('patch changed-path sets differ')
    results = [{}, {}]
    for name in a:
        length = max((start - 1 + count for start, count, _, _ in a[name] + b[name]), default=0)
        base = [f'@UNCHANGED:{i}\n' for i in range(max(length, 0))]
        seen = {}
        for start, count, new_count, lines in a[name] + b[name]:
            old = [x[1:] for x in lines if x[0] in ' -']
            new = [x[1:] for x in lines if x[0] in ' +']
            if len(old) != count or len(new) != new_count:
                raise ValueError('hunk count mismatch')
            for i, line in enumerate(old, start - 1):
                if i in seen and seen[i] != line:
                    raise ValueError('different original source')
                seen[i] = line
                base[i] = line
        for result, parsed in zip(results, (a, b)):
            out, cursor = [], 0
            for start, count, _, lines in parsed[name]:
                pos = start - 1 if count else start
                if pos < cursor:
                    raise ValueError('overlapping hunks')
                out.extend(base[cursor:pos])
                out.extend(x[1:] for x in lines if x[0] in ' +')
                cursor = pos + count
            out.extend(base[cursor:])
            result[name] = ''.join(out)
    return results


def validate_abort_patch_pair(left, right):
    a, b = patch_postimages(left, right)
    name = 'cc/ss2pl/transaction.cc'
    if a[name].count(ABORT) != 1:
        raise ValueError('expected exactly one restored abort block')
    a[name] = a[name].replace(ABORT, '')
    if a != b:
        raise ValueError('patch pair differs outside the abort block')
    return dict(accepted=True, only_difference=ABORT, files=len(a))


def write_exact(path, expected):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != expected:
            raise ValueError(f'existing shadow mismatch: {path}')
    else:
        with path.open('xb') as out:
            out.write(expected)


def create_shadows(args, driver, patches, receipt):
    import orchestrator.campaign as package
    canonical = driver.condition_meaning_gate
    def identities():
        return dict(canonical_id=id(sys.modules[canonical.__name__]),
                    canonical_file=canonical.__file__,
                    package_attribute_id=id(package.condition_meaning_gate),
                    package_id=id(package), package_file=package.__file__,
                    source_digest_id=id(canonical.source_digest),
                    source_digest_file=canonical.source_digest.__file__)
    before = identities()
    repo_bytes = Path(canonical.__file__).read_bytes()
    modules = {}
    for patch_id, patch_path in patches.items():
        for registry in REGISTRIES:
            root = args.shadow_root / patch_id / registry
            path = root / 'orchestrator/campaign/condition_meaning_gate.py'
            expected = shadow_bytes(repo_bytes, registry)
            write_exact(path, expected)
            accept_shadow(repo_bytes, path.read_bytes(), registry)
            dest_patch = root / 'patches/ss2pl-lock-protocol-study.patch'
            write_exact(dest_patch, patch_path.read_bytes())
            name = 'orchestrator.campaign._t2737_gate_' + hashlib.sha256(str(path).encode()).hexdigest()[:20]
            m = load_module(name, path)
            after = identities()
            if before != after or m.__package__ != 'orchestrator.campaign' or m.source_digest is not canonical.source_digest:
                raise ValueError('canonical module/package/source_digest identity changed')
            expected_paths = set(parse_patch(patch_path.read_bytes()))
            changed = {macro: sorted(m._patch_changed_paths(m.DEFINE_SPECS[macro])) for macro in MACROS}
            if any(set(paths) != expected_paths for paths in changed.values()):
                raise ValueError('shadow patch path resolution mismatch')
            receipt.append(dict(patch_id=patch_id, registry_id=registry,
                                gate=file_info(path), patch=file_info(dest_patch),
                                package=m.__package__, source_digest_file=m.source_digest.__file__,
                                module_name=name, module_id=id(m), before=before, after=after,
                                patch_changed_paths=changed,
                                diff=''.join(difflib.unified_diff(repo_bytes.decode().splitlines(True),
                                                                 expected.decode().splitlines(True)))))
            modules[patch_id, registry] = m
    return modules


def configure_args(args, driver, arm, staging):
    expected = driver._expected_cache(arm, backoff=1)
    return ('-DCMAKE_BUILD_TYPE=Release', '-DENABLE_SANITIZER=OFF',
            f'-DCMAKE_PREFIX_PATH={args.gflags_prefix};{args.glog_prefix}',
            f'-DFETCHCONTENT_SOURCE_DIR_MASSTREE={staging / "masstree"}',
            f'-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={staging / "mimalloc"}',
            f'-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={staging / "googletest"}',
            '-DFETCHCONTENT_FULLY_DISCONNECTED=ON',
            *(f'-D{k}={v}' for k, v in expected.items() if k not in driver.AXIS_CACHE_KEYS.values()))


def diagnostics(m, captured, request, path):
    """Repeat each side once in separate dirs; never replace the original verdict."""
    spec, value, default, companions = m._validate_define_request(request)
    inert = m._is_inert_value(spec, requested=value, default=default)
    rows = []
    for side, root, v in [('requested', captured.source_root, value),
                          ('control', captured.stock_root if inert else captured.source_root,
                           None if inert else default)]:
        argv = [str(Path(shutil.which('cmake')).resolve()), '-S', root, '-B', str(path / side),
                '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                f'-DCMAKE_CXX_COMPILER={Path(shutil.which("c++")).resolve()}',
                *captured.configure_args, *m._configure_defines(request, v, companions)]
        rows.append(dict(side=side, **command(argv, timeout=120)))
    return rows


def static_contracts(driver, clones):
    result = {}
    for name in ('revs', 'abort-unconditional'):
        result[name] = {}
        for key, fn in [('abort_ownership', driver.validate_abort_counter_ownership),
                        ('study_header_declarations', driver._study_lock_header_declarations)]:
            try:
                result[name][key] = dict(accepted=True, evidence=fn(clones[name]))
            except driver.ContractError as exc:
                result[name][key] = dict(accepted=False, error=str(exc), exception_type=type(exc).__name__)
    return result


def compare_s(args, driver, clones, staging, attempt, receipt):
    receipt.update(status='running', target='tpcc_ss2pl.exe')
    paths = []
    for name in ('stock', 'revs'):
        source = clones[name]
        build = attempt / ('cmp-build-' + name)
        argv = ['cmake', '-S', str(source), '-B', str(build),
                '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
                *configure_args(args, driver, 'S', staging)]
        config = command(argv, timeout=600)
        receipt[name] = dict(configure=config)
        require_command(config)
        entries = driver._target_compile_entries(build, 'tpcc_ss2pl.exe')
        entry, = [x for x in entries if driver._entry_source(x) == str(source / 'cc/ss2pl/transaction.cc')]
        definitions = driver._definitions(driver._entry_argv(entry))
        if 'SS2PL_WORKLOAD_YCSB' in definitions:
            raise ValueError('TPCC comparison unexpectedly has the YCSB workload define')
        if name == 'revs':
            receipt[name]['compile_definitions'] = driver._validate_compile_definitions(
                [entry], driver._expected_cache('S', backoff=1))
        pp = attempt / (name + '.transaction.ii')
        result = command(driver._preprocess_argv(entry), cwd=entry['directory'], timeout=120, stdout_path=pp)
        receipt[name].update(entry=entry, preprocess=result)
        require_command(result)
        paths.append(pp)
    a, b = (p.read_bytes() for p in paths)
    receipt['cmp'] = command(['cmp', str(paths[0]), str(paths[1])])
    receipt['byte_identical'] = a == b
    # Diagnostic only; gate receives the unmodified trees and bytes.
    def normalized(data, root):
        return data.decode('utf-8', 'replace').replace(str(root), '<SOURCE_ROOT>')
    aa = normalized(a, clones['stock']).splitlines(True)
    bb = normalized(b, clones['revs']).splitlines(True)
    delta = list(difflib.unified_diff(aa, bb, fromfile='stock', tofile='revs'))
    receipt['non_path_difference_lines'] = sum(x.startswith(('+', '-')) and not x.startswith(('+++', '---')) for x in delta)
    receipt['first_difference_20_lines'] = delta[:20]
    diffpath = attempt / 'stock-revs.non-path.diff'
    diffpath.write_text(''.join(delta))
    receipt['non_path_diff_file'] = file_info(diffpath)
    receipt['status'] = 'complete'


def plain_build(args, driver, clones, staging, attempt, arm, row):
    build = attempt / ('plain-' + arm)
    row.update(status='running', arm=arm, build_success=False,
               condition_admission='separate family receipts; not required by this diagnostic build')
    expected = driver._configure(clones['revs'], build, arm=arm, backoff=1,
                                 gflags_prefix=args.gflags_prefix, glog_prefix=args.glog_prefix,
                                 thirdparty_root=staging)
    run = command(['cmake', '--build', str(build), '--target', 'ycsb_ss2pl.exe',
                   '--parallel', str(args.jobs)], timeout=1800)
    row['build'] = run
    require_command(run)
    row['build_success'] = True
    entries = driver._target_compile_entries(build, 'ycsb_ss2pl.exe')
    row['compile_entries'] = entries
    row['compile_definitions'] = driver._validate_compile_definitions(entries, expected)
    row['warning_flags'] = [[x for x in driver._entry_argv(e) if x.startswith('-W')] for e in entries]
    if any('-Werror' not in flags for flags in row['warning_flags']):
        raise ValueError('plain build lacks -Werror')
    row['cache'] = driver._cmake_cache(build / 'CMakeCache.txt')
    binary = driver._find_binary(build, 'ycsb_ss2pl.exe')
    row['binary'] = file_info(binary)
    if arm == 'S':
        try:
            row['wfg_absence'] = dict(accepted=True, evidence=driver._wfg_absence_evidence(binary, entries))
        except driver.ContractError as exc:
            row['wfg_absence'] = dict(accepted=False, error=str(exc))
    row['status'] = 'complete'


def selftest(driver):
    results = []
    def check(name, fn):
        try:
            fn()
            results.append((name, True, ''))
        except Exception as exc:
            results.append((name, False, repr(exc)))
    def assert_true(value):
        if not value:
            raise AssertionError('assertion failed')
    def rejects(fn):
        try:
            fn()
        except (ValueError, driver.ContractError):
            return
        raise AssertionError('unexpected acceptance')
    synthetic = b'non-SS2PL-entry\n' + registry_block() + b'logic\n'
    for registry in REGISTRIES:
        check('shadow-accept-' + registry, lambda r=registry: assert_true(accept_shadow(synthetic, shadow_bytes(synthetic, r), r)))
    valid = shadow_bytes(synthetic, 'T-')
    mutations = {
        'inert_values': valid.replace(b'"tpcc_ss2pl.exe",', b'"tpcc_ss2pl.exe", inert_values=("1",),', 1),
        'owner_tus': valid.replace(b'_SS2PL_OWNER', b'_SILO_OWNER', 1),
        'expression': valid.replace(b'"tpcc_ss2pl.exe"', b'(print("bad") or "tpcc_ss2pl.exe")', 1),
        'non-SS2PL': valid.replace(b'non-SS2PL-entry', b'other-entry'),
        'logic': valid.replace(b'logic', b'logix'),
    }
    for name, value in mutations.items():
        check('shadow-reject-' + name, lambda v=value: rejects(lambda: accept_shadow(synthetic, v, 'T-')))
    cells, order = cells_and_order()
    check('cell-count-45-and-unique', lambda: assert_true(len(cells) == len({x['id'] for x in cells}) == 45))
    check('prediction-vocabulary', lambda: assert_true(all(x['expected_reason'] in REASONS.values() for x in cells)))
    check('execution-order', lambda: assert_true(order[8] == 'warm-up' and
          all(order.index(c['id']) < 8 for c in cells if c['staging'] == 'pristine') and
          order[17] == 'revs.T+.phase1.kind.warm' and order[26:28] == ['plain-build.S', 'plain-build.phase1']))
    def patch_for(text):
        name = 'cc/ss2pl/transaction.cc'
        return (f'diff --git a/{name} b/{name}\n' + ''.join(difflib.unified_diff(
            ['void TxExecutor::abort() {\n', '}\n'], text.splitlines(True), fromfile='a/'+name, tofile='b/'+name))).encode()
    # Include a shared edit so both variants have a transaction hunk.
    left = patch_for('void TxExecutor::abort() {\n'+ABORT+'  common();\n}\n')
    right = patch_for('void TxExecutor::abort() {\n  common();\n}\n')
    check('abort-pair-accept', lambda: validate_abort_patch_pair(left, right))
    check('abort-pair-reject-extra-change', lambda: rejects(lambda: validate_abort_patch_pair(left, right.replace(b'common()', b'other()'))))
    check('patch-no-final-newline', lambda: assert_true(parse_patch(
        b'diff --git a/a b/a\n--- a/a\n+++ b/a\n@@ -1 +1 @@\n-old\n'
        b'\\ No newline at end of file\n+new\n\\ No newline at end of file\n'
    )['a'][0][3] == ['-old', '+new']))
    # In-memory Path-shaped fixture calls the actual ownership validator (no tmp).
    class MemoryPath:
        transaction = 'void TxExecutor::abort() {\n#if 0\n++result_->local_abort_counts_;\n#endif\n}\n'
        def __init__(self, path=''):
            self.path = path
        def __truediv__(self, name):
            return MemoryPath(self.path + '/' + name)
        def resolve(self):
            return self
        def is_file(self):
            return True
        def is_symlink(self):
            return False
        def relative_to(self, root):
            return self.path
        def read_text(self, **kwargs):
            return self.transaction if self.path.endswith('transaction.cc') else '++r.local_abort_counts_;\n++r.local_abort_counts_;\n'
    def abort_negative():
        try:
            driver.validate_abort_counter_ownership(MemoryPath())
        except driver.ContractError as exc:
            assert_true('TxExecutor::abort increments=1, workload increments=2' in str(exc))
            return
        raise AssertionError('#if 0 increment not counted')
    check('abort-if0-token-scan', abort_negative)
    from orchestrator.campaign import buildcache
    def fetchcontent_missing():
        with tempfile.TemporaryDirectory(prefix='t2737-selftest-') as temporary:
            base = Path(temporary).resolve(strict=True) / 'fetchcontent'
            try:
                buildcache._canonical_fetchcontent_base(str(base))
            except buildcache.BuildCacheError as exc:
                assert_true('non-symlink directory' in str(exc))
                return
            raise AssertionError('missing fetchcontent directory accepted')
    def fetchcontent_created():
        with tempfile.TemporaryDirectory(prefix='t2737-selftest-') as temporary:
            base = Path(temporary) / 'fetchcontent'
            base.mkdir(exist_ok=True)
            base = base.resolve(strict=True)
            assert_true(buildcache._canonical_fetchcontent_base(str(base)) == str(base))
    check('fetchcontent-missing-rejected', fetchcontent_missing)
    check('fetchcontent-mkdir-resolve-accepted', fetchcontent_created)
    for name, ok, detail in results:
        print(f'{name}: {"PASS" if ok else "FAIL"} {detail}', flush=True)
    return 0 if all(x[1] for x in results) else 1


def run(args, driver):
    started = time.monotonic()
    hostname = socket.gethostname()
    login = args.cells == ['login-precheck']
    cells, order = cells_and_order()
    by_id = {c['id']: c for c in cells}
    selected = ['revs.T-.S.impl.warm'] if login else ([c['id'] for c in cells] if args.cells == ['recommended'] else args.cells)
    if len(selected) != len(set(selected)) or any(x not in by_id for x in selected):
        raise ValueError('unknown/duplicate cell IDs (use T- in argv)')
    document = dict(schema='t2737-gate-probe/v1', tempfile_gettempdir=tempfile.gettempdir(),
                    tmp_free_bytes=shutil.disk_usage(tempfile.gettempdir()).free,
                    tmp_free_inodes=os.statvfs(tempfile.gettempdir()).f_favail,
                    hostname=hostname, pbs_jobid=discover_pbs_jobid(args.repo_root, hostname),
                    tools={}, inputs={}, status='running', stage='inputs',
                    cells=[dict(by_id[x], status='not-run', not_run_reason='not-reached',
                                internal_exception=None, gate_red=None) for x in selected],
                    order=order, shadows=[], families=[],
                    builds={arm: dict(status='not-run', not_run_reason='not-selected' if login else 'not-reached')
                            for arm in ('S', 'phase1')},
                    warm_up=dict(status='not-run', not_run_reason='login-precheck' if login else 'not-reached'),
                    trial='not-run')
    patches = {'current': args.patch_current, 'revs': args.patch_redesigned,
               'abort-unconditional': args.patch_abort_unconditional}
    rows = {x['id']: x for x in document['cells']}
    records = {}
    rc = 0
    def save():
        document['elapsed_seconds'] = time.monotonic() - started
        write_result(args.output, document)
    try:
        for name in ('c++', 'cmake', 'cc'):
            executable = shutil.which(name)
            document['tools'][name] = dict(realpath=str(Path(executable).resolve()) if executable else None,
                                           version=command([name, '--version']))
        for name, path in {**patches, 'probe': Path(__file__),
                           'runner': Path(driver.__file__),
                           'gate': Path(driver.condition_meaning_gate.__file__)}.items():
            document['inputs'][name] = file_info(path)
        document['argv'] = sys.argv
        save()
        if not login and not hostname.split('.')[0].startswith('bnode'):
            raise ValueError('compute mode requires bnode; use --cells login-precheck on login')
        for path in (args.scratch_root, args.shadow_root, args.thirdparty_root):
            if 'wfg' in str(path.resolve()).lower():
                raise ValueError('scratch/shadow/staging ancestor contains wfg')
        document['required_commands'] = driver.validate_required_commands()
        document['canonical_submodule'] = driver.verify_canonical_submodule(args.repo_root)
        document['abort_patch_pair'] = validate_abort_patch_pair(patches['revs'].read_bytes(), patches['abort-unconditional'].read_bytes())
        attempt = args.scratch_root / ('attempt-' + uuid4().hex)
        attempt.mkdir(parents=True)
        document['attempt'] = str(attempt)
        document['scratch_free_bytes'] = shutil.disk_usage(attempt).free
        document['output_parent_free_bytes'] = shutil.disk_usage(args.output.parent).free
        staging = attempt / 'staging'
        original_config = config_info(args.thirdparty_root)
        document['staging_original'] = original_config
        document['staging_copy'] = command(['cp', '-a', str(args.thirdparty_root), str(staging)], timeout=600)
        require_command(document['staging_copy'])
        for dep in ('masstree', 'mimalloc', 'googletest'):
            (staging / dep).resolve(strict=True).relative_to(staging.resolve())
        document['staging_before'] = config_info(staging)
        document['staging_state'] = 'preexisting' if login else 'pristine'
        if not login and (original_config['exists'] or document['staging_before']['exists']):
            raise ValueError('compute experiment requires pristine masstree without config.h')
        document['stage'] = 'clone-apply'
        save()
        clones = {}
        for name in ('stock', *patches):
            clone = attempt / name
            driver.clone_network_free(args.repo_root / 'external/ccbench', clone)
            if name != 'stock':
                driver._apply_patch(clone, patches[name], reverse=False)
            clones[name] = clone
        document['clones'] = {k: str(v) for k, v in clones.items()}
        # Compare applied trees as well as symbolic patch postimages.
        differences = []
        for name in parse_patch(patches['revs'].read_bytes()):
            a, b = ((clones[p] / name).read_bytes() for p in ('revs', 'abort-unconditional'))
            if a != b:
                differences.append(name)
                if name != 'cc/ss2pl/transaction.cc' or a.replace(ABORT.encode(), b'') != b:
                    raise ValueError('applied trees differ outside abort block')
        if differences != ['cc/ss2pl/transaction.cc']:
            raise ValueError('missing applied abort difference')
        document['applied_pair_only_abort'] = differences
        modules = create_shadows(args, driver, patches, document['shadows'])
        save()
        if login:
            document['static_contracts'] = static_contracts(driver, clones)
            document['s_comparison'] = {}
            try:
                compare_s(args, driver, clones, staging, attempt, document['s_comparison'])
            except Exception:
                rc = 1
                document['s_comparison'].update(status='internal-exception', error=traceback.format_exc())
            save()
        for ident in order:
            if login and ident not in selected:
                continue
            if ident not in selected and ident not in ('warm-up', 'plain-build.S', 'plain-build.phase1'):
                continue
            if ident.startswith('plain-build.') and args.cells != ['recommended']:
                continue
            if ident == 'warm-up' and not any(by_id[x]['staging'] == 'warm' for x in selected):
                continue
            # 40-minute job: leave a minute to serialize receipts; actions already
            # in progress retain their explicit subprocess timeouts.
            if time.monotonic() - started >= 2340:
                if ident in rows:
                    rows[ident]['not_run_reason'] = 'budget'
                elif ident.startswith('plain-build.'):
                    document['builds'][ident.split('.')[1]]['not_run_reason'] = 'budget'
                elif ident == 'warm-up':
                    document['warm_up']['not_run_reason'] = 'budget'
                document['budget_exhausted'] = True
                save()
                continue
            document['stage'] = ident
            print(ident, flush=True)
            if ident == 'warm-up':
                from orchestrator.campaign import buildcache
                row = document['warm_up'] = dict(before=config_info(staging), status='running')
                start = time.monotonic()
                try:
                    base = attempt / 'fetchcontent'
                    base.mkdir(exist_ok=True)
                    base = base.resolve(strict=True)
                    row['fetchcontent_base_dir'] = str(base)
                    row['fetchcontent_base_checks'] = dict(
                        isdir=os.path.isdir(base), islink=os.path.islink(base),
                        realpath_equals_abspath=os.path.realpath(base) == os.path.abspath(base))
                    manifest = buildcache.observed_toolchain_manifest('cc', 'c++')
                    kwargs = dict(ccbench_dir=str(clones['revs']), fetchcontent_base_dir=str(base),
                                  expected_toolchain_manifest=manifest, configure_timeout_s=300, target_timeout_s=600,
                                  dependency_prefix=f'{args.gflags_prefix};{args.glog_prefix}',
                                  masstree_source_dir=str(staging / 'masstree'),
                                  mimalloc_source_dir=str(staging / 'mimalloc'),
                                  googletest_source_dir=str(staging / 'googletest'))
                    row['helper'] = 'buildcache.prepare_masstree_fetchcontent'
                    row['kwargs'] = kwargs
                    save()
                    prepared = buildcache.prepare_masstree_fetchcontent(**kwargs)
                    row.update(status='complete', configure_argv=list(prepared.configure_argv),
                               build_argv=list(prepared.build_argv), build_dir=prepared.build_dir)
                except Exception:
                    rc = 1
                    row.update(status='internal-exception', error=traceback.format_exc())
                finally:
                    row.update(after=config_info(staging), seconds=time.monotonic()-start)
                    save()
                continue
            if ident.startswith('plain-build.'):
                arm = ident.split('.')[1]
                row = document['builds'][arm] = {}
                start = time.monotonic()
                try:
                    plain_build(args, driver, clones, staging, attempt, arm, row)
                except Exception:
                    rc = 1
                    row.update(status='internal-exception', error=traceback.format_exc())
                finally:
                    row['seconds'] = time.monotonic()-start
                    save()
                continue
            row = rows[ident]
            start = time.monotonic()
            try:
                row.update(status='running', not_run_reason=None, staging_config=config_info(staging),
                           staging_state='preexisting' if login else row['staging'],
                           patch_sha256=document['inputs'][row['patch']]['sha256'])
                save()
                if row['staging'] == 'pristine' and row['staging_config']['exists']:
                    raise ValueError('pristine cell sees config.h')
                if row['staging'] == 'warm' and not row['staging_config']['exists']:
                    row['staging_state_warning'] = 'warm-up failed to provide config.h; prediction not applicable'
                m = modules[row['patch'], row['registry']]
                expected = driver._expected_cache(row['arm'], backoff=1)
                axis, macro, value, default = next(x for x in driver._condition_request_inputs(expected) if x[0] == row['axis'])
                args_for_gate = configure_args(args, driver, row['arm'], staging)
                row['configure_args'] = args_for_gate
                captured = m.capture_define_inputs(clones[row['patch']], stock_root=clones['stock'], configure_args=args_for_gate)
                request = m.make_define_request(driver_id=f'tools.pegasus.run_ss2pl_lock_study:{row["arm"]}',
                                               macro=macro, requested_value=value, default_value=default,
                                               stock_comparison=value == default)
                supply = m.evaluate_define_supply_effectuation(captured, request=request, cxx='c++', cmake='cmake')
                row['supply_canonical_json'] = supply.canonical_json()
                row['observed_reason'] = supply.reason_code
                meaning = m.evaluate_define_runtime_meaning(captured, request=request, declaration=None, cxx='c++')
                row['meaning_canonical_json'] = meaning.canonical_json()
                row['gate_red'] = supply.terminal_status == 'red'
                row['status'] = 'gate-result'
                key = (row['patch'], row['registry'], row['arm'], row['staging'])
                records.setdefault(key, {})[axis] = (supply, meaning)
                if len(records[key]) == 4:
                    pairs = [records[key][a] for a in AXES]
                    admission = m.require_condition_gate_family([x[0] for x in pairs], [x[1] for x in pairs], use_class='raw-measurement')
                    document['families'].append(dict(key=key, canonical_json=admission.canonical_json()))
                if supply.reason_code == 'configure-failed':
                    row['diagnostic_configure'] = diagnostics(m, captured, request, attempt / ('diagnostic-' + ident))
            except Exception:
                rc = 1
                row.update(status='internal-exception', internal_exception=traceback.format_exc())
            finally:
                row['seconds'] = time.monotonic()-start
                write_result(attempt / 'cells' / (ident + '.json'), row)
                save()
        document['static_contracts'] = static_contracts(driver, clones)
        document['staging_original_after'] = config_info(args.thirdparty_root)
        if document['staging_original_after'] != document['staging_original']:
            raise ValueError('original staging config changed')
        document['status'] = 'partial' if any(x['status'] == 'not-run' for x in rows.values()) else ('internal-exception' if rc else 'complete')
    except Exception:
        rc = 1
        document.update(status='internal-exception', exception=traceback.format_exc())
    finally:
        document['rc'] = rc
        save()
    print(json.dumps(dict(rc=rc, status=document['status'], output=str(args.output)), ensure_ascii=False), flush=True)
    return rc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    for name in ('patch-current', 'patch-redesigned', 'patch-abort-unconditional',
                 'shadow-root', 'scratch-root', 'gflags-prefix', 'glog-prefix',
                 'thirdparty-root', 'output'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--jobs', type=int, default=48)
    parser.add_argument('--cells', nargs='+', default=['recommended'])
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    for name, value in vars(args).items():
        if isinstance(value, Path) and not value.is_absolute():
            parser.error(f'--{name.replace("_", "-")} must be absolute')
    driver = load_module('_t2737_ss2pl_runner', args.repo_root / 'tools/pegasus/run_ss2pl_lock_study.py')
    if args.selftest:
        return selftest(driver)
    for name, value in vars(args).items():
        if value is None:
            parser.error(f'--{name.replace("_", "-")} required outside selftest')
    if not 1 <= args.jobs <= 48:
        parser.error('--jobs must be 1..48')
    return run(args, driver)


if __name__ == '__main__':
    raise SystemExit(main())
```
