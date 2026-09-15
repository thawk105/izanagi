"""Disposable Linux x86_64 probe: private ancestors, shared writable branches."""
import ctypes as C
import errno, hashlib, json, os, platform, shutil, socket, subprocess, sys, tempfile
from pathlib import Path
def digest(root):
    rows = [(str(p.relative_to(root)), p.stat().st_mode, p.read_bytes().hex() if p.is_file() else None) for p in [root, *sorted(root.rglob('*'))]]
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()

def main():
    checks, environment, temporary, before = {}, {}, None, None
    def check(name, action, expected=None, fatal=True):
        try:
            value = action(); row = {'result': expected is None and value is not False, 'errno': None}
        except Exception as exc:
            row = {'result': expected is not None and getattr(exc, 'errno', None) == expected, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
        checks[name] = row
        if fatal and not row['result']: raise RuntimeError(name)
    def syscall(fn, *args):
        if fn(*args) == -1:
            code = C.get_errno(); raise OSError(code, os.strerror(code))
    def run(args):
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=90)
        if p.returncode: raise RuntimeError(f'{args!r}: exit={p.returncode}: {p.stdout}')
        return p.stdout
    def namespaces(): return {n: os.readlink('/proc/self/ns/' + n) for n in ('user', 'mnt')}
    def project(path, tag):
        path.mkdir(parents=True, exist_ok=True)
        (path / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.10)\nproject(probe C)\nadd_executable(probe main.c)\n')
        (path / 'main.c').write_text('#include <stdio.h>\nint main(void){puts("' + tag + '");return 0;}\n')
    try:
        environment.update(kernel=platform.release(), hostname=platform.node(), uid=os.getuid(), TMPDIR=os.environ.get('TMPDIR'), tempfile_root=tempfile.gettempdir())
        for name, choices in [('cmake', ('cmake',)), ('cc', ('cc', 'gcc', 'clang'))]:
            path = next((shutil.which(n) for n in choices if shutil.which(n)), None)
            environment[name] = {'path': os.path.realpath(path) if path else None, 'version': None}
            check('find_' + name, lambda: path is not None)
            environment[name]['version'] = run([path, '--version']).splitlines()[0]
        check('nonroot_x86_64', lambda: os.getuid() != 0 and platform.machine() == 'x86_64')
        temporary = tempfile.TemporaryDirectory(prefix='t1994-rootview-'); root = Path(temporary.name)
        src, base, cache = root / 'ancestor/source', root / 'base', root / 'cache'
        project(src, 'A'); base.mkdir(); cache.mkdir(); (base / 'masstree-src').mkdir(); (base / 'masstree-src/file').write_text('dependency')
        original = digest(src); source_mode = src.stat().st_mode & 0o777; payload = {p.name: p.read_bytes() for p in src.iterdir()}; checks['source_A'] = {'result': True, 'errno': None, 'digest': original}
        before = namespaces(); uid, gid = os.getuid(), os.getgid(); parent, child = socket.socketpair(); parent.settimeout(240); child.settimeout(240)
        pid = os.fork()
        if pid == 0:
            parent.close(); stream = child.makefile('rw'); mounts = []; fds = []
            try:
                libc = C.CDLL(None, use_errno=True); libc.syscall.restype = C.c_long
                check('unshare', lambda: syscall(libc.unshare, 0x10000000 | 0x00020000))
                for name, data in [('setgroups', 'deny'), ('uid_map', f'{uid} {uid} 1'), ('gid_map', f'{gid} {gid} 1')]: check(name, lambda: Path('/proc/self/' + name).write_text(data + '\n'))
                check('private', lambda: syscall(libc.mount, None, b'/', None, C.c_ulong(16384 | 262144), None))
                fds = [os.open(p, os.O_PATH | os.O_DIRECTORY) for p in (base, cache)]
                def mount(target, source=b'tmpfs', kind=b'tmpfs', flags=0):
                    syscall(libc.mount, source, os.fsencode(target), kind, C.c_ulong(flags), b'size=4m' if kind else None); mounts.append(target)
                check('root_view_tmpfs', lambda: mount(root)); src.mkdir(parents=True); base.mkdir(); cache.mkdir()
                for p, fd in zip((base, cache), fds): check('share_' + p.name, lambda: mount(p, os.fsencode(f'/proc/self/fd/{fd}'), None, 4096 | 16384))
                check('source_tmpfs', lambda: mount(src)); src.chmod(source_mode)
                for name, data in payload.items(): (src / name).write_bytes(data)
                attr = (C.c_uint64 * 4)(1, 0, 0, 0)
                check('seal', lambda: syscall(libc.syscall, C.c_long(442), C.c_int(-100), C.c_char_p(os.fsencode(src)), C.c_uint(0x8000), C.byref(attr), C.c_size_t(32)))
                check('sealed_digest', lambda: digest(src) == original); stream.write('READY\n'); stream.flush()
                check('GO', lambda: stream.readline().strip() == 'GO'); staging = cache / 'staging'
                check('late_staging_marker', lambda: (staging / 'marker').read_text() == 'parent')
                check('parent_mutated', lambda: stream.readline().strip() == 'MUTATED')
                check('dependency_chmod_shared', lambda: (base / 'masstree-src/file').stat().st_mode & 0o777 == 0o444)
                check('dependency_write', lambda: (base / 'masstree-src/file').write_text('changed'), errno.EACCES, False)
                check('configure', lambda: run([environment['cmake']['path'], '-G', 'Unix Makefiles', '-S', str(src), '-B', str(staging), '-DCMAKE_C_COMPILER=' + environment['cc']['path']]))
                check('build', lambda: run([environment['cmake']['path'], '--build', str(staging)]))
                checks['artifact_inodes'] = {'result': True, 'errno': None, 'files': {str(p.relative_to(staging)): [p.stat().st_dev, p.stat().st_ino] for p in [staging / 'CMakeCache.txt', staging / 'probe', *staging.rglob('*.d')]}}
                check('binary_A', lambda: run([str(staging / 'probe')]).strip() == 'A'); (staging / 'child-marker').write_text('child')
                check('chmod', lambda: (src / 'main.c').chmod(0o600), errno.EROFS, False)
                check('write', lambda: (src / 'main.c').write_text('B'), errno.EROFS, False)
                check('read_A', lambda: digest(src) == original, fatal=False); check('base_writable', lambda: (base / 'new-entry').write_text('child'))
            except Exception as exc: checks['child_error'] = {'result': False, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
            finally:
                for fd in fds: os.close(fd)
                for p in reversed(mounts): check('unmount_' + str(p.relative_to(root)), lambda: syscall(libc.umount2, os.fsencode(p), 0), fatal=False)
            stream.write(json.dumps(checks) + '\n'); stream.flush(); os._exit(0 if all(c['result'] for c in checks.values()) else 1)
        child.close(); stream = parent.makefile('rw')
        try:
            raw = stream.readline()
            if raw.strip() == 'READY':
                checks['READY'] = {'result': True, 'errno': None}; staging = cache / 'staging'
                check('late_staging_create', lambda: staging.mkdir()); (staging / 'marker').write_text('parent'); (base / 'masstree-src/file').chmod(0o444)
                stream.write('GO\n'); stream.flush()
                check('rename_source', lambda: src.rename(src.with_name('source-old'))); project(src, 'B')
                check('rename_ancestor', lambda: src.parent.rename(root / 'ancestor-old')); project(src, 'B'); stream.write('MUTATED\n'); stream.flush(); raw = stream.readline()
            checks.update(json.loads(raw))
        finally:
            stream.close(); parent.close(); _, status = os.waitpid(pid, 0)
            check('child_exit', lambda: os.waitstatus_to_exitcode(status) == 0, fatal=False)
        for name in ('marker', 'child-marker', 'CMakeCache.txt', 'probe'): check('parent_reads_' + name, lambda: bool((cache / 'staging' / name).read_bytes()), fatal=False)
        check('parent_depfiles', lambda: any(p.read_bytes() for p in (cache / 'staging').rglob('*.d')), fatal=False); check('parent_same_inodes', lambda: all([ (cache / 'staging' / n).stat().st_dev, (cache / 'staging' / n).stat().st_ino] == v for n, v in checks['artifact_inodes']['files'].items()), fatal=False)
        check('base_shared', lambda: (base / 'new-entry').read_text() == 'child', fatal=False)
    except Exception as exc: checks['error'] = {'result': False, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
    finally:
        if before is not None: check('parent_namespaces_unchanged', lambda: namespaces() == before, fatal=False)
        if temporary is not None: check('cleanup', temporary.cleanup, fatal=False)
    overall = bool(checks) and all(c['result'] for c in checks.values())
    print(json.dumps({'overall': overall, 'checks': checks, 'environment': environment})); return 0 if overall else 1
if __name__ == '__main__': sys.exit(main())
