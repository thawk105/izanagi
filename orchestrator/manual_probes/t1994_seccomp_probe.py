"""Disposable Linux x86_64 seccomp probe; only fork children install filters."""
import ctypes as C
import errno, json, mmap, os, platform, signal, sys, tempfile
from pathlib import Path
L = C.CDLL(None, use_errno=True)
L.syscall.restype = L.ptrace.restype = C.c_long
MASK, EPERM, ENOSYS = 0x10020000, 0x50001, 0x50026
def call(n, *args):
    r = L.syscall(C.c_long(n), *args)
    if r == -1: raise OSError(C.get_errno(), os.strerror(C.get_errno()))
    return r
def install():
    class Ins(C.Structure): _fields_ = [('code', C.c_ushort), ('jt', C.c_ubyte), ('jf', C.c_ubyte), ('k', C.c_uint)]
    class Prog(C.Structure): _fields_ = [('len', C.c_ushort), ('filter', C.POINTER(Ins))]
    b = [(0x20,0,0,4),(0x15,1,0,0xc000003e),(6,0,0,EPERM),(0x20,0,0,0),(0x45,0,1,0x40000000),(6,0,0,EPERM)]
    for nr, verdict in [(435,ENOSYS),(308,EPERM),(165,EPERM),(166,EPERM),(442,EPERM),(429,EPERM)]:
        b += [(0x15,0,1,nr),(6,0,0,verdict)]
    for nr in (56,272): b += [(0x15,0,3,nr),(0x20,0,0,16),(0x45,0,1,MASK),(6,0,0,EPERM),(0x20,0,0,0)]
    b += [(6,0,0,0x7fff0000)]; a = (Ins * len(b))(*(Ins(*i) for i in b)); p = Prog(len(b), a)
    call(157,38,1,0,0,0); call(157,22,2,C.byref(p),0,0)
def reap(pid):
    if pid == 0: os._exit(0)
    return os.waitstatus_to_exitcode(os.waitpid(pid,0)[1]) == 0
def clone(flags): return reap(call(56,C.c_ulong(flags | signal.SIGCHLD),0,0,0,0))
def execute():
    pid = os.fork()
    if pid == 0: os.execve('/bin/true',['true'],{})
    return reap(pid)
def grandchildren():
    pid = os.fork()
    if pid == 0: os.execve(sys.executable,[sys.executable,'-I','-B','-c',"import os; p=os.fork(); os.execve('/bin/true',['true'],{}) if p==0 else os._exit(os.waitstatus_to_exitcode(os.waitpid(p,0)[1]))"],{})
    return reap(pid)
def compat():
    with mmap.mmap(-1,4096,prot=7) as mem:
        mem.write(bytes.fromhex('b814000000cd804898c3'))  # i386 getpid; sign-extend errno
        r = C.CFUNCTYPE(C.c_long)(C.addressof(C.c_char.from_buffer(mem)))()
        if r < 0: raise OSError(-r,os.strerror(-r))
        return r > 0
def control(dst):
    uid,gid = os.getuid(),os.getgid(); call(272,MASK)
    for name,data in [('setgroups','deny'),('uid_map',f'{uid} {uid} 1'),('gid_map',f'{gid} {gid} 1')]: Path('/proc/self/'+name).write_text(data+'\n')
    call(165,None,b'/',None,C.c_ulong(16384|262144),None)
    call(165,b'tmpfs',os.fsencode(dst),b'tmpfs',0,b'size=1m')
    try: return (Path(dst)/'marker').write_bytes(b'writable') == 8
    finally: call(166,os.fsencode(dst),0)
def run(action, filtered, expected=0, trace=False):
    rd,wr = os.pipe(); pid = os.fork()
    if pid == 0:
        os.close(rd); ready = False
        try:
            if trace: call(101,0,0,0,0); os.kill(os.getpid(),signal.SIGSTOP)
            if filtered: install()
            ready = True; value = action(); row = dict(result=expected in (0,None) and value is not False,errno=None)
        except BaseException as exc: row = dict(result=ready and (expected is None or getattr(exc,'errno',None)==expected),errno=getattr(exc,'errno',None),error=str(exc))
        row['filter_installed'] = filtered and ready
        with os.fdopen(wr,'w') as stream: json.dump(row,stream)
        os._exit(0)
    try:
        os.close(wr); events = []; status = os.waitpid(pid,0)[1] if trace else None; entering = True
        while trace and os.WIFSTOPPED(status):
            if os.WSTOPSIG(status) == signal.SIGSTOP: call(101,0x4200,pid,0,1)  # TRACESYSGOOD
            elif os.WSTOPSIG(status) == (signal.SIGTRAP|128):
                regs = (C.c_ulonglong*27)(); call(101,12,pid,0,C.byref(regs))
                if regs[15] in (56,435): events.append([int(regs[15]),'enter' if entering else C.c_longlong(regs[10]).value])
                entering = not entering
            call(101,24,pid,0,0); status = os.waitpid(pid,0)[1]
    except BaseException:
        os.kill(pid,signal.SIGKILL); os.waitpid(pid,0); os.close(rd)
        raise
    with os.fdopen(rd) as stream: raw = stream.read()
    if status is None: status = os.waitpid(pid,0)[1]
    row = json.loads(raw) if raw else dict(result=False,errno=None,error='child produced no JSON')
    row['exit'] = os.waitstatus_to_exitcode(status); row['result'] &= row['exit']==0
    if trace:
        fallback = any(events[i]==[435,-errno.ENOSYS] and events[i+1]==[56,'enter'] and events[i+2][0]==56 and isinstance(events[i+2][1],int) and events[i+2][1]>0 for i in range(len(events)-2))
        row.update(syscalls=events,clone3_attempted=[435,'enter'] in events,clone3_fallback=fallback)
        if filtered and row['clone3_attempted']: row['result'] &= fallback
    return row
def main():
    checks,environment = {},dict(kernel=platform.release(),hostname=platform.node(),uid=os.getuid(),glibc=platform.libc_ver())
    try:
        L.gnu_get_libc_version.restype = C.c_char_p; environment['glibc'] = L.gnu_get_libc_version().decode()
        for name in ('kernel/unprivileged_userns_clone','user/max_user_namespaces'):
            try: environment['/proc/sys/'+name] = dict(value=Path('/proc/sys/'+name).read_text().strip(),errno=None)
            except OSError as exc: environment['/proc/sys/'+name] = dict(value=None,errno=exc.errno)
        if platform.machine()!='x86_64': raise RuntimeError('requires x86_64')
        with tempfile.TemporaryDirectory(prefix='t1994-seccomp-',dir='/tmp') as dst:
            checks['outside.control_writable_mount'] = run(lambda:control(dst),False)
            checks['inside.control_writable_mount'] = run(lambda:control(dst),True,errno.EPERM)
        attacks = {**{f'{name}_{flag:x}':(lambda n=n,f=flag: clone(f) if n==56 else call(n,f)) for name,n in [('clone',56),('unshare',272)] for flag in (0x10000000,0x20000,MASK)},'clone3':lambda:reap(call(435,C.byref((C.c_uint64*11)(MASK,0,0,0,signal.SIGCHLD)),88)),'setns':lambda:call(308,-1,0),'mount':lambda:call(165,b'tmpfs',b'',b'tmpfs',0,None),'umount2':lambda:call(166,b'',0),'mount_setattr':lambda:call(442,-1,b'',0,C.byref((C.c_uint64*4)()),32),'move_mount':lambda:call(429,-1,b'',-1,b'',0),'x32':lambda:call(0x40000027),'i386':compat}
        positives = dict(fork=lambda:reap(os.fork()),clone=lambda:clone(0),execve=execute,grandchildren=grandchildren,glibc_spawn=lambda:reap(os.posix_spawn('/bin/true',['true'],{})))
        for name,action in {**attacks,**positives}.items():
            for filtered in (False,True): checks[('inside.' if filtered else 'outside.')+name] = run(action,filtered,(errno.ENOSYS if name=='clone3' else errno.EPERM) if filtered and name in attacks else (None if name in attacks else 0),name=='glibc_spawn')
    except BaseException as exc: checks['error'] = dict(result=False,errno=getattr(exc,'errno',None),error=str(exc))
    overall = bool(checks) and all(c['result'] for c in checks.values()); print(json.dumps(dict(overall=overall,checks=checks,environment=environment))); return 0 if overall else 1
if __name__ == '__main__': sys.exit(main())
