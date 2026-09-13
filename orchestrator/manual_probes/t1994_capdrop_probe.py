"""Disposable Linux x86_64 probe; namespace/capability changes stay in children."""
import ctypes as C
import errno, json, os, platform, sys, tempfile
from pathlib import Path

def main():
    checks, environment, temporary = {}, {}, None
    def check(name, action, expected=None, fatal=True):
        try:
            value = action(); row = {'result': expected is None and value is not False, 'errno': None}
        except Exception as exc:
            row = {'result': expected is not None and getattr(exc, 'errno', None) == expected, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
        checks[name] = row
        if fatal and not row['result']: raise RuntimeError(name)
    def syscall(fn, *args):
        result = fn(*args)
        if result == -1:
            code = C.get_errno(); raise OSError(code, os.strerror(code))
        return result
    def namespaces(flags):
        syscall(libc.unshare, flags)
        for name, data in [('setgroups', 'deny'), ('uid_map', f'{uid} {uid} 1'), ('gid_map', f'{gid} {gid} 1')]:
            Path('/proc/self/' + name).write_text(data + '\n')
    def drop():
        for cap in range(int(Path('/proc/sys/kernel/cap_last_cap').read_text()) + 1): syscall(libc.prctl, 24, cap, 0, 0, 0)
        syscall(libc.prctl, 47, 4, 0, 0, 0)  # PR_CAP_AMBIENT_CLEAR_ALL
        syscall(libc.capset, C.byref((C.c_uint32 * 2)(0x20080522, 0)), C.byref((C.c_uint32 * 6)()))
        syscall(libc.prctl, 38, 1, 0, 0, 0)  # PR_SET_NO_NEW_PRIVS
        status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines())
        return all(int(status[n], 16) == 0 for n in ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')) and int(status['NoNewPrivs']) == 1
    def filter_userns():
        class Filter(C.Structure): _fields_ = [('code', C.c_ushort), ('jt', C.c_ubyte), ('jf', C.c_ubyte), ('k', C.c_uint32)]
        class Program(C.Structure): _fields_ = [('len', C.c_ushort), ('filter', C.POINTER(Filter))]
        deny, allow = 0x50000 | errno.EPERM, 0x7fff0000
        # Validate arch; reject x32/setns; clone3 cannot inspect pointed-to flags.
        rows = [(0x20,0,0,4),(0x15,1,0,0xc000003e),(6,0,0,deny),(0x20,0,0,0),
                (0x45,0,1,0x40000000),(6,0,0,deny),(0x15,0,1,435),(6,0,0,0x50000 | errno.ENOSYS),
                (0x15,0,1,308),(6,0,0,deny),(0x15,2,0,272),(0x15,1,0,56),(6,0,0,allow),
                (0x20,0,0,16),(0x45,0,1,0x10000000),(6,0,0,deny),(6,0,0,allow)]
        program = Program(len(rows), (Filter * len(rows))(*(Filter(*r) for r in rows)))
        syscall(libc.syscall, C.c_long(317), C.c_uint(1), C.c_uint(0), C.byref(program))
    def liveness(grandchild=False):
        reader, writer = os.pipe(); pid = os.fork()
        if pid == 0:
            os.close(reader)
            try:
                if grandchild and not liveness(): os._exit(1)
                os.execve('/bin/true', ['/bin/true'], {})
            except BaseException as exc:
                os.write(writer, json.dumps({'errno': getattr(exc, 'errno', None), 'error': str(exc)}).encode()); os._exit(127)
        os.close(writer)
        with os.fdopen(reader) as stream: raw = stream.read()
        status = os.waitpid(pid, 0)[1]
        if raw:
            row = json.loads(raw); raise OSError(row['errno'], row['error'])
        return os.waitstatus_to_exitcode(status) == 0
    try:
        libc = C.CDLL(None, use_errno=True); libc.syscall.restype = C.c_long; libc.gnu_get_libc_version.restype = C.c_char_p
        uid, gid = os.getuid(), os.getgid()
        environment.update(kernel=platform.release(), hostname=platform.node(), uid=uid, glibc=libc.gnu_get_libc_version().decode())
        check('nonroot_x86_64', lambda: uid != 0 and gid != 0 and platform.machine() == 'x86_64')
        temporary = tempfile.TemporaryDirectory(prefix='t1994-capdrop-', dir='/tmp'); file = Path(temporary.name) / 'file'
        file.write_bytes(b'parent'); file.chmod(0o444)
        for state in ('a', 'b', 'c', 'd'):
            reader, writer = os.pipe(); pid = os.fork()
            if pid == 0:
                os.close(reader); checks = {}
                try:
                    check(state + '_namespace', lambda: namespaces(0x10000000 | 0x00020000))
                    check(state + '_private', lambda: syscall(libc.mount, None, b'/', None, C.c_ulong(16384 | 262144), None))
                    check(state + '_bind', lambda: syscall(libc.mount, os.fsencode(file), os.fsencode(file), None, C.c_ulong(4096), None))
                    check(state + '_mode', lambda: file.stat().st_mode & 0o777 == 0o444 and file.stat().st_uid == uid)
                    if state != 'a':
                        check(state + '_drop', drop)
                        check(state + '_after_drop_write', lambda: file.write_bytes(b'changed'), errno.EACCES, False)
                    if state == 'c': check('c_new_userns', lambda: namespaces(0x10000000))
                    if state == 'd':
                        check('d_seccomp', filter_userns)
                        check('d_new_userns', lambda: syscall(libc.unshare, 0x10000000), errno.EPERM, False)
                    check(state + '_write', lambda: file.write_bytes(b'changed'), None if state in ('a', 'c') else errno.EACCES, False)
                    if state == 'd':
                        check('d_fork_execve', liveness, fatal=False)
                        check('d_grandchild_execve', lambda: liveness(True), fatal=False)
                except Exception as exc: checks[state + '_error'] = {'result': False, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
                with os.fdopen(writer, 'w') as stream: json.dump(checks, stream)
                os._exit(0 if checks and all(c['result'] for c in checks.values()) else 1)
            os.close(writer)
            with os.fdopen(reader) as stream: raw = stream.read()
            _, status = os.waitpid(pid, 0)
            check(state + '_report', lambda: checks.update(json.loads(raw)), fatal=False)
            check(state + '_exit', lambda: os.waitstatus_to_exitcode(status) == 0, fatal=False)
        for state in ('a', 'b', 'c', 'd'):
            checks.setdefault(state + '_write', {'result': False, 'errno': None, 'error': 'not measured'})
    except Exception as exc: checks['error'] = {'result': False, 'errno': getattr(exc, 'errno', None), 'error': str(exc)}
    finally:
        if temporary is not None: check('cleanup', temporary.cleanup, fatal=False)
    overall = bool(checks) and all(c['result'] for c in checks.values())
    print(json.dumps({'overall': overall, 'checks': checks, 'environment': environment})); return 0 if overall else 1
if __name__ == '__main__': sys.exit(main())
