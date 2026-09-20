# 生死 probe の逐語 (`probe_zombie_group.py`、job dir に置いた使い捨て driver、repo へは入れない)

実行: `python3 probe_zombie_group.py <wave worktree>` (login node、2026-09-20 07:19 JST)。結果は同 dir の `probe-result-login.jsonl`。
本 file は逐語の写しであり実行可能資材ではない (実装面は Codex author の契約、D95)。

```python
"""DW-G01 生死 probe: subreaper の下でゾンビが PGID に残るか、現行 _group_member_count が数えるか。

使い捨て。repo へは入れない。引数: <wave worktree 絶対 path>。
"""
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PR_SET_CHILD_SUBREAPER = 36
WORKTREE = Path(sys.argv[1])
sys.path.insert(0, os.fspath(WORKTREE))
sys.path.insert(0, os.fspath(WORKTREE / "tools"))
import codex_worker_launch as LAUNCHER  # noqa: E402
from tools.dev_waves import worker as WORKER  # noqa: E402

LEADER_CODE = r"""
import os, sys, time
from pathlib import Path
mode = sys.argv[1]
gc = os.fork()
if gc == 0:
    if mode == "running":
        import signal
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(30)
    os._exit(0)
Path(sys.argv[2]).write_text(str(gc))
if mode == "zombie":
    # 孫が Z になるまで待つが wait() はしない (回収不全を作る)
    while True:
        raw = Path(f"/proc/{gc}/stat").read_text()
        if raw[raw.rfind(")") + 2:].split()[0] == "Z":
            break
        time.sleep(0.005)
os._exit(0)
"""


def scan(pgid):
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            raw = Path(f"/proc/{name}/stat").read_text()
        except OSError:
            continue
        fields = raw[raw.rfind(")") + 2:].split()
        if int(fields[2]) == pgid:
            out.append((int(name), fields[0]))
    return sorted(out)


def run_case(mode, subreaper):
    libc = ctypes.CDLL(None, use_errno=True)
    if subreaper:
        assert libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) == 0, ctypes.get_errno()
    gc_path = Path(f"/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2620-zombie-residual/gc-{mode}-{subreaper}.pid")
    leader = subprocess.Popen(
        [sys.executable, "-c", LEADER_CODE, mode, os.fspath(gc_path)],
        start_new_session=True,
    )
    identity = WORKER.read_pid_identity(leader.pid)
    leader.wait()
    time.sleep(0.05)
    members = scan(leader.pid)
    reasons = []
    count = LAUNCHER._group_member_count(identity, on_unknown=reasons.append)
    residual, verified = LAUNCHER._normal_reap(leader, identity)
    gc = int(gc_path.read_text()) if gc_path.exists() else None
    result = {
        "mode": mode, "subreaper": subreaper, "leader": leader.pid, "grandchild": gc,
        "members_after_leader_wait": members, "group_member_count": count,
        "unknown": reasons, "normal_reap": [residual, verified],
        "worker_group_members": WORKER._group_members(leader.pid),
        "verified_group_exists": WORKER._verified_group_exists(identity),
    }
    # 後始末: 走っている孫は殺し、ゾンビは自分 (subreaper) が回収する
    if gc is not None:
        try:
            os.kill(gc, 9)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if pid == 0:
            time.sleep(0.01)
    result["members_after_cleanup"] = scan(leader.pid)
    if subreaper:
        libc.prctl(PR_SET_CHILD_SUBREAPER, 0, 0, 0, 0)
    return result


if __name__ == "__main__":
    for mode, sub in (("zombie", False), ("zombie", True), ("running", False)):
        print(json.dumps(run_case(mode, sub), default=str), flush=True)
```
