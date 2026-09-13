"""One-shot compute qualification, outside pytest's testpaths.

Run via tools/pegasus/dispatch_compute.py --task generic -- python3 -m
orchestrator.manual_probes.t1994_readonly_snapshot_qualification.

This measures source substitution during build, not poisoned cache reuse.
The production capability is a trusted-producer value, not kernel attestation
or a signature. Hostile Python process-memory mutation is outside its boundary.
clone3 ENOSYS fallback was observed on glibc 2.35, not arbitrary libcs.
No replacement session, context, or capability is defined here. Observers call
the real session.run; buildcache retains its real parent-side checks and publish.
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes as C
import dataclasses
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / 'output/insights/2026-09-14/t1994-readonly-snapshot/qualification'
LIMITS = [
    'Only source substitution during build is measured; poisoned cache reuse is open.',
    'Capabilities are trusted-producer values, not kernel attestation or signatures.',
    'Hostile Python process-memory mutation is outside the trust boundary.',
    'clone3 ENOSYS fallback evidence covers only the observed libc and commands.',
    'Only one freeze entry each for stock_common and sort_best is qualified.',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def namespaces():
    return {n: os.readlink('/proc/self/ns/' + n) for n in ('user', 'mnt')}


def error(exc):
    return {'result': False, 'errno': getattr(exc, 'errno', None),
            'error': f'{type(exc).__name__}: {exc}'}


def require(checks, name, value, **facts):
    checks[name] = {'result': bool(value), 'errno': None, **facts}
    if not value:
        raise RuntimeError(name)


def fd_inventory(root):
    """Count the actual copy domain through directory fds, excluding .git.

    Destination inodes include the root and each name separately. Regular-file
    bytes are rounded per file using the observed page size. Symlink payloads
    are separate; actual tmpfs allocation is measured with statvfs, not guessed
    from these counts. Content digests normalize only permission write bits.
    """
    page = os.sysconf('SC_PAGESIZE')
    counts = dict(files=0, directories=1, symlinks=0, apparent_bytes=0,
                  symlink_bytes=0, page_rounded_file_bytes=0, page_size=page)
    rows = []

    def visit(fd, prefix):
        for name in sorted(os.listdir(fd), key=os.fsencode):
            if name == '.git':
                continue
            rel = prefix + name
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            mode = stat.S_IMODE(info.st_mode) & ~0o222
            if stat.S_ISDIR(info.st_mode):
                counts['directories'] += 1
                rows.append([rel, 'd', mode])
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    opened = os.fstat(child)
                    if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        raise RuntimeError('directory changed while opening ' + rel)
                    visit(child, rel + '/')
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    opened = os.fstat(child)
                    if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        raise RuntimeError('file changed while opening ' + rel)
                    digest, size = hashlib.sha256(), 0
                    while block := os.read(child, 1024 * 1024):
                        digest.update(block)
                        size += len(block)
                    after = os.fstat(child)
                    if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
                            after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                        raise RuntimeError('file changed while reading ' + rel)
                finally:
                    os.close(child)
                counts['files'] += 1
                counts['apparent_bytes'] += size
                counts['page_rounded_file_bytes'] += ((size + page - 1) // page) * page
                rows.append([rel, 'f', mode, size, digest.hexdigest()])
            elif stat.S_ISLNK(info.st_mode):
                target = os.readlink(name, dir_fd=fd)
                counts['symlinks'] += 1
                counts['symlink_bytes'] += len(os.fsencode(target))
                rows.append([rel, 'l', target])
            else:
                raise RuntimeError('unsupported copy node: ' + rel)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        visit(fd, '')
    finally:
        os.close(fd)
    counts['nodes'] = counts['files'] + counts['directories'] + counts['symlinks']
    counts['required_inodes'] = counts['nodes']
    counts['copy_domain_sha256'] = canonical_sha(rows)
    counts['excluded_names'] = ['.git']
    return counts


def libc():
    lib = C.CDLL(None, use_errno=True)
    lib.syscall.restype = C.c_long
    return lib


def checked(value):
    if value == -1:
        code = C.get_errno()
        raise OSError(code, os.strerror(code))
    return value


def identity_map(uid, gid):
    for name, data in [('setgroups', 'deny'), ('uid_map', f'{uid} {uid} 1'),
                       ('gid_map', f'{gid} {gid} 1')]:
        Path('/proc/self/' + name).write_text(data + '\n')


def write_errno(path):
    try:
        fd = os.open(path, os.O_WRONLY)
        try:
            os.write(fd, b'X')
        finally:
            os.close(fd)
        return 0
    except OSError as exc:
        return exc.errno


def fork_report(action):
    """Drain before waitpid; no pipe-capacity deadlock or guessed timeout."""
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            result = action()
        except BaseException as exc:
            result = error(exc)
        with os.fdopen(write_fd, 'w') as stream:
            json.dump(result, stream)
        os._exit(0)
    os.close(write_fd)
    try:
        with os.fdopen(read_fd) as stream:
            raw = stream.read()
    finally:
        _, status = os.waitpid(pid, 0)
    return {'pid': pid, 'exit': os.waitstatus_to_exitcode(status),
            'observation': json.loads(raw) if raw else {'error': 'empty child report'}}


def nested_attack(kind, shared):
    """Identical attack code inside the real filter and in its control.

    After namespace creation, map the original identity and write the shared
    0444 file. Raw clone is fork-like (no CLONE_VM, null stack), x86_64 only.
    The clone child must itself succeed and is synchronously reaped.
    """
    lib, uid, gid = libc(), os.getuid(), os.getgid()
    flags = 0x10000000  # CLONE_NEWUSER
    if kind == 'unshare':
        value = lib.unshare(flags)
    elif kind == 'clone':
        value = lib.syscall(C.c_long(56), C.c_ulong(flags | signal.SIGCHLD),
                            C.c_void_p(0), C.c_void_p(0), C.c_void_p(0), C.c_ulong(0))
    elif kind == 'clone3':
        args = (C.c_uint64 * 11)()
        args[0], args[4] = flags, signal.SIGCHLD
        value = lib.syscall(C.c_long(435), C.byref(args), C.c_size_t(C.sizeof(args)))
    else:
        raise ValueError(kind)
    if value == -1:
        return {'errno': C.get_errno(), 'namespace_created': False}
    if kind != 'unshare' and value > 0:
        _, status = os.waitpid(value, 0)
        return {'errno': 0, 'namespace_created': True,
                'nested_child_exit': os.waitstatus_to_exitcode(status)}
    try:
        identity_map(uid, gid)
        code = write_errno(shared)
        result = {'errno': 0, 'namespace_created': True, 'shared_write_errno': code}
    except BaseException:
        if kind != 'unshare':
            os._exit(1)
        raise
    if kind != 'unshare':
        os._exit(0 if code == 0 else 1)
    return result


def drop_capabilities():
    lib = libc()
    for cap in range(int(Path('/proc/sys/kernel/cap_last_cap').read_text()) + 1):
        checked(lib.prctl(24, cap, 0, 0, 0))  # PR_CAPBSET_DROP
    header, data = (C.c_uint32 * 2)(0x20080522, 0), (C.c_uint32 * 6)()
    checked(lib.capset(C.byref(header), C.byref(data)))
    checked(lib.prctl(38, 1, 0, 0, 0))  # PR_SET_NO_NEW_PRIVS


def control(shared):
    uid, gid = os.getuid(), os.getgid()
    checked(libc().unshare(0x10000000 | 0x00020000))
    identity_map(uid, gid)
    before = write_errno(shared)
    drop_capabilities()
    after = write_errno(shared)
    attacks = {name: fork_report(lambda name=name: nested_attack(name, shared))
               for name in ('unshare', 'clone', 'clone3')}
    return {'before_drop_write_errno': before, 'after_drop_write_errno': after,
            'attacks_without_filter': attacks}


def sealed_observation(root, shared):
    root = Path(root)
    inventory = fd_inventory(root)
    target = root / 'CMakeLists.txt'
    original = target.read_bytes()
    try:
        target.chmod(0o600)
        chmod_errno = 0
    except OSError as exc:
        chmod_errno = exc.errno
    code = write_errno(target)
    vfs = os.statvfs(root)
    mountinfo = Path('/proc/self/mountinfo').read_text()
    escaped = str(root).replace('\\', '\\134').replace(' ', '\\040').replace('\t', '\\011')
    mounts = [line for line in mountinfo.splitlines() if line.split()[4] == escaped]
    return {'inventory': inventory, 'mountinfo': mountinfo, 'source_mounts': mounts,
            'chmod_errno': chmod_errno, 'write_errno': code,
            'read_unchanged': target.read_bytes() == original,
            'git_absent': not os.path.lexists(root / '.git'),
            'tmpfs': {'fragment_size': vfs.f_frsize,
                      'used_bytes': (vfs.f_blocks - vfs.f_bfree) * vfs.f_frsize,
                      'used_inodes': vfs.f_files - vfs.f_ffree},
            'status': Path('/proc/self/status').read_text(),
            'shared_write_errno': write_errno(shared),
            'attacks_with_filter': {name: fork_report(lambda name=name: nested_attack(name, shared))
                                    for name in ('unshare', 'clone', 'clone3')},
            'namespaces': namespaces()}


def child_command(action, *args):
    return [sys.executable, str(Path(__file__).resolve()), '--internal', action, *map(str, args)]


def proc_descendants():
    seen = set()

    def visit(pid):
        result = []
        try:
            tasks = list(Path(f'/proc/{pid}/task').iterdir())
        except FileNotFoundError:
            return result
        for task in tasks:
            try:
                children = (task / 'children').read_text().split()
            except FileNotFoundError:
                continue
            for child in map(int, children):
                if child not in seen:
                    seen.add(child)
                    result.append(child)
                    result.extend(visit(child))
        return result
    return visit(os.getpid())


def ccache_diagnostic(build_dir, execute):
    """Observation failures are data, never an independent qualification gate."""
    result = {'launcher': None, 'cache_dir': None, 'temporary_dir': None,
              'log_file': None, 'status': 'unobserved'}
    try:
        entries = {}
        for line in (Path(build_dir) / 'CMakeCache.txt').read_text().splitlines():
            if '=' in line and ':' in line.split('=', 1)[0] and not line.startswith('//'):
                key, value = line.split('=', 1)
                entries[key.split(':', 1)[0]] = value
        result['cmake_entries'] = {k: v for k, v in entries.items()
                                   if 'LAUNCHER' in k or 'CCACHE' in k.upper()}
        lines = []
        for path in Path(build_dir).rglob('build.make'):
            lines.extend(line for line in path.read_text(errors='replace').splitlines()
                         if 'ccache' in line and line.startswith('\t'))
        for path in Path(build_dir).rglob('*.ninja'):
            lines.extend(line for line in path.read_text(errors='replace').splitlines()
                         if 'ccache' in line and 'command =' in line)
        result['generated_recipe_lines'] = lines
        launcher = entries.get('CMAKE_CXX_COMPILER_LAUNCHER')
        if not launcher and lines:
            import shlex
            launcher = next((t for t in shlex.split(lines[0]) if Path(t).name == 'ccache'), None)
        result['launcher'] = launcher or 'unused'
        if not launcher or 'ccache' not in launcher:
            result['status'] = 'unused'
            return result
        # Keep a failed optional query from becoming a failed session command.
        completed = execute(child_command('ccache', *launcher.split(';')))
        diagnostic = json.loads(completed.stdout)
        if diagnostic.get('error'):
            result.update(status='unobservable', error=diagnostic['error'])
            return result
        raw = diagnostic['stdout']
        if isinstance(raw, bytes):
            raw = raw.decode(errors='replace')
        result.update(show_config_returncode=diagnostic['returncode'], show_config_raw=raw)
        if diagnostic['returncode']:
            result['status'] = 'unobservable'
            return result
        for line in raw.splitlines():
            for name in ('cache_dir', 'temporary_dir', 'log_file'):
                if name + ' = ' in line:
                    result[name] = line.split(name + ' = ', 1)[1] or 'unset'
        result['status'] = 'observed'
    except Exception as exc:
        result.update(status='unobservable', error=str(exc))
    return result


def query_ccache(argv):
    """Return diagnostic failures as JSON; the optional helper itself exits zero."""
    try:
        completed = subprocess.run([*argv, '--show-config'], capture_output=True,
                                   text=True, timeout=None)
        return {'returncode': completed.returncode, 'stdout': completed.stdout,
                'stderr': completed.stderr, 'argv': [*argv, '--show-config']}
    except Exception as exc:
        return {'error': str(exc)}


def prepare_dependencies(base, pin, toolchain, run, source_dirs):
    """Execute buildcache's CMake preparation argv without its mandatory caps.

    The real floor verifier/materializer creates canonical oracle material.
    No D1755 validation, protection, or post-oracle build step is substituted.
    """
    from orchestrator.campaign import buildcache as bc, patchharness, s8b_floor_campaign as floor
    with patchharness.checkout(pin, base_dir=str(ROOT / 'external/ccbench')) as source:
        directory = base / 'izanagi-masstree-prebuild'
        configure = [toolchain['cmake']['realpath'], '-S', source, '-B', str(directory),
                     '-DCMAKE_BUILD_TYPE=Release', '-DENABLE_SANITIZER=OFF',
                     '-DCMAKE_C_COMPILER=' + toolchain['cc']['realpath'],
                     '-DCMAKE_CXX_COMPILER=' + toolchain['cxx']['realpath'],
                     '-DFETCHCONTENT_BASE_DIR=' + str(base)]
        configure += bc._fetchcontent_source_defines(source_dirs)
        run(configure)
        run([toolchain['cmake']['realpath'], '--build', str(directory), '--target',
             'masstree_build', '-j', str(bc._resolve_build_jobs(None, None))])
    binding = floor._verify_floor_oracle_dependency_source(
        base, repo_root=ROOT, expected_head=floor._masstree_policy_pin(ROOT),
        expected_toolchain_manifest_sha256=floor._floor_toolchain_manifest_sha256(toolchain))
    return floor._materialize_floor_oracle_dependency(binding, lease_parent=base)


def qualify(args, report, log):
    # S1 is absent in the author checkout. Import failure must not become a green skip.
    from orchestrator.campaign.s8b_expected_materialization import (
        sealed_build_session, SealedBuildSession, SealedSnapshotProtectionKind,
    )
    from orchestrator.campaign import (
        buildcache as bc, env_contract, s8b_expected_materialization as em,
        s8b_floor_campaign as floor, s8b_materialization as mat,
        s1_direct_comparison as direct, source_digest, sort_swo_dependency_material,
    )
    from orchestrator.campaign.build_admission import (
        build_run_context, GeneratorId, ReviewId, derive_build_admission,
    )
    checks = report['checks']
    require(checks, 'real_session_api', callable(sealed_build_session))
    require(checks, 'compute_node', bc._resolve_site(None) == bc.site_policy.PEGASUS_COMPUTE)
    require(checks, 'nonroot_x86_64', os.getuid() != 0 and platform.machine() == 'x86_64')
    checked(libc().prctl(36, 1, 0, 0, 0))  # collect orphan descendants as well
    report['commands'] = []

    def run(argv):
        record = {'argv': list(map(str, argv)), 'timeout_s': None}
        report['commands'].append(record)
        began = time.monotonic()
        completed = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, timeout=None)
        record.update(returncode=completed.returncode, elapsed_s=time.monotonic() - began)
        log.write(json.dumps(record) + '\n' + completed.stdout + '\n')
        log.flush()
        if completed.returncode:
            raise RuntimeError(f'command failed: {record}')
        return completed

    cc, cxx = bc.compilers_for_current_site()
    toolchain = bc.observed_toolchain_manifest(args.cc or cc, args.cxx or cxx)
    cc, cxx = bc.toolchain_compilers_from_manifest(toolchain)
    report['toolchain'] = toolchain
    pin = run(['git', '-C', str(ROOT / 'external/ccbench'), 'rev-parse',
               (args.pin or 'HEAD') + '^{commit}']).stdout.strip()
    report['ccbench_pin'] = pin
    freeze = json.loads(args.freeze.read_text())
    report['declarations'] = {'freeze': str(args.freeze),
                              'freeze_sha256': sha(args.freeze.read_bytes()), 'holdout': args.holdout}
    contract = env_contract.lookup(args.env_tag)
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    report['contract_sha256'] = contract.contract_sha256
    # No custom environment variable is required by generic dispatch.
    with tempfile.TemporaryDirectory(prefix='t1994-qualification-', dir='/tmp') as temporary:
        scratch = Path(temporary)
        base = scratch / 'base'
        base.mkdir()
        source_dirs = {}
        if args.dependency_sources is not None:
            pins = floor._floor_third_party_policy_pins(ROOT)
            for name in ('masstree', 'mimalloc', 'googletest'):
                source, target = args.dependency_sources / (name + '-src'), base / (name + '-src')
                run(['git', 'clone', '--no-hardlinks', '--no-checkout', str(source), str(target)])
                run(['git', '-C', str(target), 'checkout', '--detach', pins[name]])
                source_dirs[name] = str(target)
        shared = scratch / 'shared-0444'
        shared.write_bytes(b'A')
        shared.chmod(0o444)
        control_row = fork_report(lambda: control(shared))
        report['control'] = control_row
        obs = control_row['observation']
        require(checks, 'capability_control', control_row['exit'] == 0
                and obs.get('before_drop_write_errno') == 0
                and obs.get('after_drop_write_errno') == errno.EACCES, observation=obs)
        for name in ('unshare', 'clone', 'clone3'):
            attack = obs['attacks_without_filter'][name]
            detail = attack['observation']
            require(checks, 'unfiltered_' + name, attack['exit'] == 0
                    and detail.get('namespace_created') is True and detail.get('errno') == 0
                    and detail.get('nested_child_exit', 0) == 0
                    and detail.get('shared_write_errno', 0) == 0, observation=attack)
        material = None
        try:
            binding, material = prepare_dependencies(base, pin, toolchain, run, source_dirs)
            report['dependency'] = binding.private_dict()
            report['builds'] = {}
            for configuration, attack_mode in [('stock_common', 'aba'), ('sort_best', 'none'),
                                                ('stock_common', 'persistent')]:
                label = configuration + ':' + attack_mode
                row = {'configuration': configuration, 'attack': attack_mode,
                       'session_commands': [], 'ccache': {'status': 'unobserved'}}
                report['builds'][label] = row
                try:
                    build_case(configuration, attack_mode, label, row, checks, args,
                               freeze, pin, toolchain, cc, cxx, context, contract,
                               base, source_dirs, shared, binding, scratch, log,
                               bc, em, mat, floor, direct, source_digest,
                               SealedBuildSession, SealedSnapshotProtectionKind,
                               derive_build_admission, ReviewId)
                except Exception as exc:
                    checks[label] = error(exc)
                    row['error'] = traceback.format_exc()
        finally:
            if material is not None:
                sort_swo_dependency_material.cleanup_canonical_dependency(material)


def build_case(configuration, attack_mode, label, row, checks, args, freeze, pin,
               toolchain, cc, cxx, context, contract, base, source_dirs, shared,
               binding, scratch, log, bc, em, mat, floor, direct, source_digest,
               session_type, protection_kind, derive_build_admission, review_id):
    entry = mat.binding_entry(freeze, args.holdout, configuration)
    descriptor = em.expected_materialization_descriptor(
        ccbench_commit=pin, configuration=configuration, declaration=entry)
    row['descriptor_sha256'] = descriptor.declaration_sha256
    row['descriptor'] = {'configuration': configuration, 'ccbench_commit': pin,
                         'declaration': dict(entry), 'template_patch_path': descriptor.template_patch_path}
    cache = scratch / ('cache-' + configuration + '-' + attack_mode)
    cache.mkdir()
    options = {'oracle_dependency_root': binding.oracle_root,
               'oracle_compiler': toolchain['cxx']['realpath']} \
        if configuration == 'sort_best' else {}
    with direct.prepare_cell({'configuration': configuration, 'variant': dict(entry)},
                             pin, cxx=cxx, **options) as prepared:
        root = Path(prepared.ccbench_dir)
        inventory = fd_inventory(root)
        row['copy_target'] = inventory
        extra = {'sort_oracle_contract_id': prepared.sort_oracle_contract_id} \
            if prepared.sort_oracle_contract_id is not None else {}
        evidence = source_digest.resolve_evidence(
            prepared.genome, pin, ccbench_dir=str(root), cxx=cxx, **extra)
        review = mat.reviewed_source_capability(
            review_id=review_id.S8B_FLOOR, source=evidence, input_sha256=descriptor.declaration_sha256)
        admission = derive_build_admission(context, evidence, review_receipt=review)
        build_options = dict(extra, fetchcontent_base_dir=str(base))
        build_options.update({name + '_source_dir': value for name, value in source_dirs.items()})
        if configuration == 'sort_best':
            row['oracle_attempt'] = prepared.oracle_attempt
            build_options.update(
                fetchcontent_dependency_receipt=binding.cache_receipt(),
                fetchcontent_archive_sha256=binding.archive_sha256,
                post_oracle_dependency_binding=floor._post_oracle_dependency_binding(
                    prepared.oracle_attempt, binding),
                current_compiler_input_masstree_root=str(binding.source_root))
            row['post_oracle_binding'] = build_options['post_oracle_dependency_binding']
        original_run = session_type.run
        mutated = build_finished = sealed_seen = False
        old_parent = root.parent.with_name(root.parent.name + '-original-A')
        renamed_source = root.with_name(root.name + '-original-A')
        parent_checks = []
        parent_namespaces = namespaces()

        def restore():
            nonlocal mutated
            if mutated:
                if root.parent.exists():
                    shutil.rmtree(root.parent)
                old_parent.rename(root.parent)
                renamed_source.rename(root)
                mutated = False

        def mutate():
            nonlocal mutated
            root.rename(renamed_source)
            try:
                root.parent.rename(old_parent)
            except BaseException:
                renamed_source.rename(root)
                raise
            mutated = True
            root.parent.mkdir()
            shutil.copytree(old_parent / renamed_source.name, root, symlinks=True)
            poisoned = []
            for path in root.rglob('*'):
                if path.suffix in ('.cc', '.cpp', '.c', '.h', '.hpp') and path.is_file() and not path.is_symlink():
                    path.chmod(0o600)
                    path.write_bytes(b'#error T1994_ORIGINAL_TREE_B\n')
                    poisoned.append(str(path.relative_to(root)))
            row['rename_attack'] = {'source_renamed': True, 'ancestor_renamed': True,
                                    'poisoned_paths': poisoned, 'parent_B_inventory': fd_inventory(root)}
            require(checks, label + ':B_differs', bool(poisoned)
                    and fd_inventory(root)['copy_domain_sha256'] != inventory['copy_domain_sha256'])

        def observed_run(session, argv, *, cwd, env, timeout_s):
            nonlocal sealed_seen, build_finished

            def execute(command):
                record = {'argv': list(map(str, command)), 'cwd': str(cwd), 'timeout_s': None,
                          'ccache_environment': {k: v for k, v in (env or {}).items() if k.startswith('CCACHE_')}}
                row['session_commands'].append(record)
                started = time.monotonic()
                try:
                    completed = original_run(session, command, cwd=cwd, env=env, timeout_s=None)
                except Exception as exc:
                    record.update(error(exc))
                    raise
                record.update(returncode=completed.returncode, elapsed_s=time.monotonic() - started)
                log.write(json.dumps(record) + '\n')
                for key in ('stdout', 'stderr'):
                    output = getattr(completed, key, '') or ''
                    log.write((output.decode(errors='replace') if isinstance(output, bytes) else output) + '\n')
                log.flush()
                return completed

            if not sealed_seen:
                observed = execute(child_command('sealed', root, shared))
                observation = json.loads(observed.stdout)
                row['seal'] = observation
                require(checks, label + ':seal', observed.returncode == 0
                        and observation['chmod_errno'] == errno.EROFS and observation['write_errno'] == errno.EROFS
                        and observation['read_unchanged'] and observation['git_absent']
                        and observation['inventory'] == inventory and observation['source_mounts']
                        and all('ro' in line.split()[5].split(',') and ' - tmpfs ' in line
                                for line in observation['source_mounts']))
                require(checks, label + ':capdrop', observation['shared_write_errno'] == errno.EACCES)
                status = dict(line.split(':', 1) for line in observation['status'].splitlines() if ':' in line)
                require(checks, label + ':capability_sets_empty',
                        all(int(status[name].strip(), 16) == 0 for name in
                            ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb'))
                        and status['NoNewPrivs'].strip() == '1')
                for name, expected in [('unshare', errno.EPERM), ('clone', errno.EPERM), ('clone3', errno.ENOSYS)]:
                    attack = observation['attacks_with_filter'][name]
                    require(checks, label + ':filtered_' + name,
                            attack['exit'] == 0 and attack['observation'].get('errno') == expected,
                            observation=attack)
                sealed_seen = True
            is_build = '--build' in argv
            if is_build and attack_mode != 'none' and not mutated:
                mutate()
            completed = execute(argv)
            if is_build:
                build_finished = completed.returncode == 0
                copied = execute(child_command('inventory', root))
                observed_inventory = json.loads(copied.stdout)
                row['compiler_read_view_after_build'] = observed_inventory
                require(checks, label + ':compiler_A', build_finished
                        and copied.returncode == 0 and observed_inventory == inventory)
                if attack_mode == 'aba':
                    restore()
            if '-B' in argv:
                row['ccache'] = ccache_diagnostic(argv[list(argv).index('-B') + 1], execute)
            return completed

        def observe_guard(name, original):
            def call(*positional, **keywords):
                record = {'guard': name, 'pid': os.getpid(), 'namespaces': namespaces(), 'source_is_B': mutated}
                parent_checks.append(record)
                try:
                    result = original(*positional, **keywords)
                except Exception as exc:
                    record.update(rejected=True, error=str(exc))
                    raise
                record['rejected'] = False
                return result
            return call

        result = caught = None
        try:
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(session_type, 'run', observed_run))
                for owner, name in [(bc, '_assert_source_snapshot_sha256'), (bc, '_recheck_source_evidence'),
                                    (bc, '_collect_compiler_inputs'), (em, '_assert_root_identity'),
                                    (bc, '_assert_fetchcontent_fully_disconnected_effective'),
                                    (bc, '_assert_post_oracle_dependency_material'),
                                    (bc, '_masstree_source_root_from_cmake_cache')]:
                    stack.enter_context(patch.object(owner, name, observe_guard(name, getattr(owner, name))))
                result = bc.build_v2(
                    prepared.genome, admission=admission, build_context=context,
                    source_evidence=evidence, expected_materialization_descriptor=descriptor,
                    contract=contract, ccbench_commit=pin, trace=False, src_token=evidence.src_token,
                    cc=cc, cxx=cxx, cache_root=str(cache), ccbench_dir=str(root),
                    expected_toolchain_manifest=toolchain, timeout_s=None, **build_options)
        except Exception as exc:
            caught = exc
            row['build_exception'] = error(exc)
        finally:
            row['parent_checks'] = parent_checks
            row['cache_completion_files_before_restore'] = [str(p.relative_to(cache)) for p in cache.rglob('completion.json')]
            row['cache_binaries_before_restore'] = [str(p.relative_to(cache)) for p in cache.rglob('ycsb_*.exe')]
            try:
                row['parent_inventory_at_return'] = fd_inventory(root)
            finally:
                restore()
        require(checks, label + ':session_used', sealed_seen and build_finished)
        if attack_mode == 'persistent':
            rejected = [r for r in parent_checks if r.get('rejected') and r['source_is_B']]
            require(checks, label + ':parent_rejected_B', caught is not None and bool(rejected)
                    and all(r['pid'] == os.getpid() for r in rejected)
                    and all(r['namespaces'] == parent_namespaces for r in rejected)
                    and row['parent_inventory_at_return']['copy_domain_sha256'] != inventory['copy_domain_sha256'],
                    rejection=str(caught))
            require(checks, label + ':no_publish', result is None
                    and not row['cache_completion_files_before_restore'] and not row['cache_binaries_before_restore'])
        else:
            if caught is not None:
                raise caught
            require(checks, label + ':real_build', result is not None and not result.cached
                    and result.source_protection.kind is protection_kind.SEALED_BUILD)
            row['provenance'] = {
                'configure_argv': result.configure_argv, 'build_argv': result.build_argv,
                'binary_sha256': result.bin_sha256,
                'compiler_input_manifest_sha256': result.compiler_input_manifest_sha256,
                'source_snapshot_sha256': result.source_snapshot_sha256,
                'expected_materialization_sha256': result.expected_materialization_sha256,
                'source_protection': dataclasses.asdict(result.source_protection),
                'toolchain_manifest': result.toolchain_manifest}
            require(checks, label + ':binary_digest', sha(Path(result.binary).read_bytes()) == result.bin_sha256)
            require(checks, label + ':manifest_digest',
                    bc.s8b_compiler_input.manifest_sha256(result.compiler_input_manifest)
                    == result.compiler_input_manifest_sha256)
            require(checks, label + ':source_unchanged', fd_inventory(root) == inventory)
            if configuration == 'sort_best':
                guards = {r['guard'] for r in parent_checks if r.get('rejected') is False}
                require(checks, label + ':D1755_checks_executed', {
                    '_assert_fetchcontent_fully_disconnected_effective',
                    '_assert_post_oracle_dependency_material',
                    '_masstree_source_root_from_cmake_cache'} <= guards)
        checks[label] = {'result': True, 'errno': None}


def parser():
    result = argparse.ArgumentParser(description=__doc__, add_help=False)
    result.add_argument('--freeze', type=Path, default=ROOT / 'output/s8b-freeze/holdout_freeze.json')
    result.add_argument('--holdout', default='rr80')
    result.add_argument('--pin', help='CCBench commit; default: local CCBench HEAD')
    result.add_argument('--cc')
    result.add_argument('--cxx')
    result.add_argument('--env-tag', default='pegasus')
    result.add_argument('--dependency-sources', type=Path,
                        help='Optional pristine masstree-src/mimalloc-src/googletest-src parent; cloned before use')
    result.add_argument('--internal', choices=['sealed', 'inventory', 'ccache'], help=argparse.SUPPRESS)
    result.add_argument('internal_paths', nargs='*', help=argparse.SUPPRESS)
    return result


def json_default(value):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if hasattr(value, 'value'):
        return value.value
    return str(value)


def main(argv=None):
    report = {'overall': False, 'checks': {},
              'environment': {'hostname': platform.node(), 'kernel': platform.release(),
                              'libc': platform.libc_ver(), 'uid': os.getuid(),
                              'argv': [sys.executable, *sys.argv]},
              'time_budget': {'timeout_s': None, 'population': None, 'observed_max_s': None,
                              'multiplier': None, 'same_regime': None,
                              'reason': 'No qualified duration population exists for this regime. '
                                        'Driver/session/CMake calls have no timeout. '
                                        'Existing oracle semantic limits are recorded separately.'},
              'limitations': LIMITS}
    before = output = saved_stdout = saved_stderr = log = None
    try:
        args = parser().parse_args(argv)
        if args.internal:
            try:
                if args.internal == 'sealed':
                    value = sealed_observation(*args.internal_paths)
                elif args.internal == 'ccache':
                    value = query_ccache(args.internal_paths)
                else:
                    value = fd_inventory(*args.internal_paths)
                print(json.dumps(value))
                return 0
            except BaseException as exc:
                print(json.dumps(error(exc)))
                return 1
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix='run-', dir=ARTIFACTS))
        report['artifacts'] = {'json': str(output / 'qualification.json'), 'raw_log': str(output / 'raw.log')}
        log = (output / 'raw.log').open('w')
        sys.stdout.flush()
        saved_stdout = os.dup(1)
        saved_stderr = os.dup(2)
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)
        report['environment']['exec_argv'] = [os.fsdecode(v) for v in
            Path('/proc/self/cmdline').read_bytes().rstrip(b'\0').split(b'\0')]
        before = namespaces()
        report['environment']['parent_namespaces_before'] = before
        from orchestrator.campaign import sort_swo_oracle as oracle
        report['oracle_existing_limits'] = {
            'source': str(Path(oracle.__file__).resolve()), 'source_sha256': sha(Path(oracle.__file__).read_bytes()),
            'compile_s': oracle._COMPILE_TIMEOUT_S, 'run_s': oracle._RUN_TIMEOUT_S,
            'tool_identity_s': oracle._TOOL_IDENTITY_TIMEOUT_S,
            'scope': 'Existing SWO oracle contract only, not qualification build time budgets.'}
        qualify(args, report, log)
    except BaseException as exc:
        report['checks']['error'] = error(exc)
        report['traceback'] = traceback.format_exc()
    finally:
        if before is not None:
            try:
                after = namespaces()
                report['environment']['parent_namespaces_after'] = after
                report['checks']['parent_namespaces_unchanged'] = {'result': before == after, 'errno': None}
                remaining = proc_descendants()
                report['checks']['descendants_finished'] = {'result': not remaining, 'errno': None, 'remaining_pids': remaining}
                for pid in reversed(remaining):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                reaped = []
                while True:
                    try:
                        pid, status = os.waitpid(-1, 0)
                    except ChildProcessError:
                        break
                    reaped.append([pid, os.waitstatus_to_exitcode(status)])
                report['cleanup_reaped'] = reaped
            except Exception as exc:
                report['checks']['descendant_cleanup'] = error(exc)
        if saved_stdout is not None:
            sys.stdout.flush()
            os.dup2(saved_stdout, 1)
            os.close(saved_stdout)
        if saved_stderr is not None:
            sys.stderr.flush()
            os.dup2(saved_stderr, 2)
            os.close(saved_stderr)
        if log is not None:
            log.close()
    report['overall'] = bool(report['checks']) and all(c['result'] for c in report['checks'].values())
    report['summary_tail'] = {'overall': report['overall'],
                              'failed': [k for k, v in report['checks'].items() if not v['result']],
                              'requested_coverage': ['stock_common', 'sort_best'],
                              'completed_cases': [k for k in report.get('builds', {}) if report['checks'].get(k, {}).get('result')],
                              'copy_targets': {k: v.get('copy_target') for k, v in report.get('builds', {}).items()},
                              'ccache_diagnostic_only': True}
    try:
        if output is not None:
            (output / 'qualification.json').write_text(json.dumps(report, default=json_default, indent=2) + '\n')
    except Exception as exc:
        report['checks']['artifact_write'] = error(exc)
        report['overall'] = False
        report['summary_tail'].update(overall=False, artifact_error=str(exc))
    print(json.dumps(report, default=json_default))
    return 0 if report['overall'] else 1


if __name__ == '__main__':
    sys.exit(main())
