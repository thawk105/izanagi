"""Disposable x86_64 Linux probe; isolation exists only in the forked child."""
import ctypes as C
import errno
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil
import sys
import tempfile
def digest(root):
    rows = [(str(p.relative_to(root)), p.stat().st_mode,
             p.read_bytes().hex() if p.is_file() else None)
            for p in [root, *sorted(root.rglob('*'))]]
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()

def main():
    checks, environment = {}, {}
    def check(name, action, expected=None, fatal=True):
        try:
            value = action()
            row = {'result': expected is None and value is not False, 'errno': None}
        except Exception as exc:
            row = {'result': expected is not None and getattr(exc, 'errno', None) == expected,
                   'errno': getattr(exc, 'errno', None), 'error': type(exc).__name__}
        checks[name] = row
        if fatal and not row['result']:
            raise RuntimeError(name)
    def syscall(fn, *args):
        if fn(*args) == -1:
            code = C.get_errno()
            raise OSError(code, os.strerror(code))
    def namespaces():
        return {n: os.readlink('/proc/self/ns/' + n) for n in ('user', 'mnt')}
    before, temporary = None, None
    try:
        environment.update(kernel=platform.uname().release, hostname=platform.node(), uid=os.getuid())
        for name in ('user/max_user_namespaces', 'kernel/unprivileged_userns_clone'):
            try:
                environment['/proc/sys/' + name] = {'value': Path('/proc/sys/' + name).read_text().strip(), 'errno': None}
            except OSError as exc:
                environment['/proc/sys/' + name] = {'value': None, 'errno': exc.errno}
        check('nonroot_x86_64', lambda: os.getuid() != 0 and platform.machine() == 'x86_64')
        temporary = tempfile.TemporaryDirectory(prefix='t1994-', dir='/tmp')
        src, dst = (Path(temporary.name) / n for n in ('source', 'snapshot'))
        src.mkdir(); dst.mkdir(); (src / 'nested').mkdir(mode=0o750)
        payload = b'T-1994 source\x00snapshot\n'
        (src / 'nested/file').write_bytes(payload)
        (src / 'nested/file').chmod(0o640)
        original = digest(src)
        before = namespaces()
        uid, gid = os.getuid(), os.getgid()
        reader, writer = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(reader)
            try:
                libc = C.CDLL(None, use_errno=True)
                libc.syscall.restype = C.c_long
                check('unshare', lambda: syscall(libc.unshare, 0x10000000 | 0x00020000))
                for name, data in [('setgroups', 'deny'), ('uid_map', f'{uid} {uid} 1'), ('gid_map', f'{gid} {gid} 1')]:
                    check(name, lambda: Path('/proc/self/' + name).write_text(data + '\n'))
                check('private', lambda: syscall(libc.mount, None, b'/', None, C.c_ulong(16384 | 262144), None))
                check('tmpfs', lambda: syscall(libc.mount, b'tmpfs', os.fsencode(dst), b'tmpfs', C.c_ulong(0), b'size=1m'))
                check('copy', lambda: shutil.copytree(src, dst, dirs_exist_ok=True))
                check('digest', lambda: digest(dst) == original)
                fd = os.open(dst, os.O_PATH | os.O_DIRECTORY)
                attr = (C.c_uint64 * 4)(1, 0, 0, 0)  # struct mount_attr: RDONLY
                check('seal', lambda: syscall(libc.syscall, C.c_long(442), C.c_int(fd), C.c_char_p(b''), C.c_uint(0x1000 | 0x8000), C.byref(attr), C.c_size_t(32)))
                os.close(fd)
                file = dst / 'nested/file'
                check('same_owner', lambda: file.stat().st_uid == os.getuid() == uid)
                check('chmod', lambda: os.chmod(file, 0o644), errno.EROFS, False)
                check('write', lambda: file.write_bytes(b'changed'), errno.EROFS, False)
                check('read', lambda: file.read_bytes() == payload, fatal=False)
            except Exception as exc:
                checks['child_error'] = {'result': False, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
            with os.fdopen(writer, 'w') as stream:
                json.dump(checks, stream)
            os._exit(0 if all(c['result'] for c in checks.values()) else 1)
        os.close(writer)
        with os.fdopen(reader) as stream:
            raw = stream.read()
        _, status = os.waitpid(pid, 0)
        checks.update(json.loads(raw))
        check('child_exit', lambda: os.waitstatus_to_exitcode(status) == 0, fatal=False)
    except Exception as exc:
        checks['error'] = {'result': False, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
    finally:
        if before is not None:
            for name in before:
                check('parent_' + name + '_unchanged', lambda: os.readlink('/proc/self/ns/' + name) == before[name], fatal=False)
        if temporary is not None:
            check('cleanup', temporary.cleanup, fatal=False)
    overall = bool(checks) and all(c['result'] for c in checks.values())
    print(json.dumps({'overall': overall, 'checks': checks, 'environment': environment}))
    return 0 if overall else 1
if __name__ == '__main__':
    sys.exit(main())
