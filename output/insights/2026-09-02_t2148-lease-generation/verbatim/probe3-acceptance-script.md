# P3 acceptance probe (逐語)

```python
#!/usr/bin/env python3
"""P3: production 入口の acceptance を、世代 field を足した lease に対して実走する。

B8 (helper の観測から acceptance 全体へ一般化してよいか) を閉じる。
本番の lease dir は使わない。使い捨て dir を --lease-dir で明示する。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-probe")
JOB = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2148-lease-generation-probe")
SCRATCH = JOB / "scratch"
WAVE = "dev-wave-t2148-lease-generation-probe"


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="p3-acceptance-", dir=SCRATCH))
    lease = directory / "acceptance.lease"
    receipt = directory / "receipt.json"
    log = directory / "acceptance.log"

    main_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True,
        text=True, stdout=subprocess.PIPE,
    ).stdout.strip()

    subprocess.run([
        sys.executable, str(REPO / "tools/wave_land_window.py"), "claim",
        "--lease-dir", str(directory), "--wave", WAVE, "--main-sha", main_sha,
    ], cwd=REPO, check=True, stdout=subprocess.PIPE)

    value = json.loads(lease.read_text(encoding="ascii"))
    value["lease_generation"] = "0" * 64
    lease.write_text(json.dumps(value) + "\n", encoding="ascii")
    before = (lease.read_bytes(), lease.stat().st_mtime_ns)

    done = subprocess.run([
        sys.executable, str(REPO / "tools/dev_wave_wait.py"), "acceptance",
        "--wave", WAVE,
        "--lease-dir", str(directory),
        "--receipt-file", str(receipt),
        "--log-file", str(log),
        "--max-wait-seconds", "1200",
        "--", sys.executable, "-c", "raise SystemExit(0)",
    ], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
       check=False)

    after = (lease.read_bytes(), lease.stat().st_mtime_ns)
    print(json.dumps({
        "rc": done.returncode,
        "receipt_exists": receipt.exists(),
        "log_exists": log.exists(),
        "lease_unchanged": before == after,
        "dir_entries": sorted(str(p.name) for p in directory.iterdir()),
    }, sort_keys=True))
    print("----- stdout -----")
    print(done.stdout)
    print("----- stderr -----")
    print(done.stderr)


if __name__ == "__main__":
    main()
```
