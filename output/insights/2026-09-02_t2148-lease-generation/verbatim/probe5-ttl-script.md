# P5 TTL probe (逐語)

```python
#!/usr/bin/env python3
"""P5: 世代 field 入り lease の TTL 前後 3 分岐と、renew による停止の延伸を測る。

B9 (「2400 秒間固まる」は不正確) を閉じる。
"""
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
GEN = "0" * 64
SHA = "a" * 40


def invoke(directory, action, wave):
    argv = [sys.executable, str(HELPER), action,
            "--lease-dir", str(directory), "--wave", wave]
    if action == "claim":
        argv += ["--main-sha", SHA]
    if action == "status":
        argv += ["--json"]
    done = subprocess.run(argv, cwd=REPO, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False)
    try:
        value = json.loads(done.stdout)
    except ValueError:
        value = {"_stdout": done.stdout, "_stderr": done.stderr}
    source = value.get("source")
    return {
        "action": action, "wave": wave, "rc": done.returncode,
        "state": value.get("state"),
        "reason": source.get("reason") if isinstance(source, dict) else None,
    }


def poison(directory):
    path = directory / "acceptance.lease"
    data = json.loads(path.read_text(encoding="ascii"))
    data["lease_generation"] = GEN
    path.write_text(json.dumps(data) + "\n", encoding="ascii")


def age(directory, seconds):
    path = directory / "acceptance.lease"
    stamp = time.time() - seconds
    os.utime(path, (stamp, stamp))


def refresh(directory):
    """新しい実装が renew した状況を模す (mtime だけを現在へ戻す)。"""
    path = directory / "acceptance.lease"
    now = time.time()
    os.utime(path, (now, now))


def scenario(label, ages, refresh_after_age=False):
    directory = Path(tempfile.mkdtemp(prefix=f"p5-{label}-", dir=SCRATCH))
    invoke(directory, "claim", "probe-wave-A")
    poison(directory)
    age(directory, ages)
    if refresh_after_age:
        refresh(directory)
    rows = [
        invoke(directory, "status", "probe-wave-A"),
        invoke(directory, "release", "probe-wave-A"),
        invoke(directory, "claim", "probe-wave-B"),
    ]
    for row in rows:
        row["scenario"] = label
        row["aged_seconds"] = ages
        row["refreshed"] = refresh_after_age
        print(json.dumps(row, sort_keys=True))


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    scenario("fresh-0", 0)
    scenario("just-under-ttl-2399", 2399)
    scenario("just-over-ttl-2401", 2401)
    scenario("over-ttl-then-renewed", 2401, refresh_after_age=True)


if __name__ == "__main__":
    main()
```
