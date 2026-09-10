# P2 derivation probe (逐語)

```python
#!/usr/bin/env python3
"""P2: payload を変えない導出値が、renew 前後と再取得前後で区別を作るかを測る。

C4 (payload bytes hash)、C5 (holder+main hash)、C14 (dev/ino + birth time)、
および B2 が足した A2 (wave 単位) / A3 (main 単位) / A4 (lease dir 単位) を同じ走で測る。
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe")
JOB = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-probe")
SCRATCH = JOB / "scratch"
HELPER = REPO / "tools" / "wave_land_window.py"
WAVE = "probe-wave-A"
SHA = "a" * 40


def run(directory, action):
    argv = [
        sys.executable, str(HELPER), action,
        "--lease-dir", str(directory), "--wave", WAVE,
    ]
    if action == "claim":
        argv += ["--main-sha", SHA]
    done = subprocess.run(
        argv, cwd=REPO, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    return done.returncode, done.stdout.strip()


def snapshot(directory, label):
    path = directory / "acceptance.lease"
    raw = path.read_bytes()
    data = json.loads(raw)
    st = path.stat()
    dst = directory.stat()
    return {
        "label": label,
        # C4: 現行 payload bytes の hash
        "c4_payload_sha256": hashlib.sha256(raw).hexdigest(),
        # C5: holder + main_sha からの導出
        "c5_holder_main_sha256": hashlib.sha256(
            (data["holder"] + "\0" + data["main_sha"]).encode("ascii")
        ).hexdigest(),
        # C14: lease file の dev/ino と birth time
        "c14_dev": st.st_dev,
        "c14_ino": st.st_ino,
        "c14_birthtime": getattr(st, "st_birthtime", None),
        "mtime_ns": st.st_mtime_ns,
        "ctime_ns": st.st_ctime_ns,
        # A2: wave 単位
        "a2_wave_sha256": hashlib.sha256(
            b"wave-generation\0" + WAVE.encode("utf-8")
        ).hexdigest(),
        # A3: main 単位
        "a3_main_sha256": hashlib.sha256(
            b"main-generation\0" + data["main_sha"].encode("ascii")
        ).hexdigest(),
        # A4: lease directory 単位
        "a4_dir_dev": dst.st_dev,
        "a4_dir_ino": dst.st_ino,
    }


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="p2-identity-", dir=SCRATCH))
    shots = []
    run(directory, "claim")
    shots.append(snapshot(directory, "acquired-1"))
    time.sleep(1.1)
    run(directory, "claim")  # 同一 holder の claim は renew になる
    shots.append(snapshot(directory, "renewed-same-acquisition"))
    run(directory, "release")
    time.sleep(1.1)
    run(directory, "claim")
    shots.append(snapshot(directory, "acquired-2"))
    for shot in shots:
        print(json.dumps(shot, sort_keys=True))

    keys = [
        "c4_payload_sha256", "c5_holder_main_sha256",
        "c14_ino", "c14_birthtime", "mtime_ns",
        "a2_wave_sha256", "a3_main_sha256", "a4_dir_ino",
    ]
    comparisons = []
    for key in keys:
        comparisons.append({
            "field": key,
            "stable_across_renew": shots[0][key] == shots[1][key],
            "changed_across_reacquire": shots[0][key] != shots[2][key],
            "v1": shots[0][key], "v2": shots[1][key], "v3": shots[2][key],
        })
    print(json.dumps({"comparisons": comparisons}, sort_keys=True))


if __name__ == "__main__":
    main()
```
