# P1 placement probe (逐語)

repo 外 (`dev-wave-jobs/dev-wave-t2148-lease-generation-probe/artifacts/probe1_placement.py`) で
実行した使い捨て probe の逐語。実装面を repo へ入れないため `.md` へ貼る。

```python
#!/usr/bin/env python3
"""P1: lease directory への世代の置き方ごとに、現行 consumer の読解を測る。

repo 外の使い捨て probe。repo へは入れない。production 入口
(tools/wave_land_window.py の CLI) と、CLI が持たない renew だけ module import で叩く。
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
SHA_A = "a" * 40
SHA_B = "b" * 40

sys.path.insert(0, str(REPO))
from tools import wave_land_window as WLW  # noqa: E402


def invoke(args):
    done = subprocess.run(
        [sys.executable, str(HELPER), *args],
        cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    try:
        value = json.loads(done.stdout)
    except ValueError:
        value = {"_stdout": done.stdout, "_stderr": done.stderr}
    return done.returncode, value


def payload_extra(field, value, stale=False):
    def mutate(directory):
        path = directory / "acceptance.lease"
        data = json.loads(path.read_text(encoding="ascii"))
        data[field] = value
        path.write_text(json.dumps(data) + "\n", encoding="ascii")
        if stale:
            stamp = time.time() - 2401
            os.utime(path, (stamp, stamp))
    return mutate


def sidecar(name, value):
    def mutate(directory):
        (directory / name).write_text(str(value) + "\n", encoding="ascii")
    return mutate


def replace_name(directory):
    (directory / "acceptance.lease").rename(directory / f"acceptance.{GEN}.lease")


def hardlink_companion(directory):
    os.link(directory / "acceptance.lease", directory / f"acceptance.{GEN}.lease")


def replace_directory(directory):
    target = directory / f"generation.{GEN}"
    target.mkdir()
    (directory / "acceptance.lease").rename(target / "acceptance.lease")


def companion_directory(directory):
    (directory / f"generation.{GEN}").mkdir()


def set_xattr(directory):
    os.setxattr(
        directory / "acceptance.lease",
        b"user.izanagi_lease_generation",
        GEN.encode("ascii"),
    )


def external_ledger(directory):
    directory.with_name(directory.name + ".ledger").write_text(
        GEN + "\n", encoding="ascii"
    )


def stale_only(directory):
    path = directory / "acceptance.lease"
    stamp = time.time() - 2401
    os.utime(path, (stamp, stamp))


SCENARIOS = {
    "baseline": lambda d: None,
    "baseline-stale-2401": stale_only,
    "payload-lease_generation": payload_extra("lease_generation", GEN),
    "payload-time": payload_extra("lease_generation", 1_700_000_000_000_000_000),
    "payload-counter": payload_extra("lease_generation", 1),
    "payload-stale-2401": payload_extra("lease_generation", GEN, stale=True),
    "sidecar-random": sidecar("acceptance.generation", GEN),
    "sidecar-counter": sidecar("acceptance.counter", 1),
    "sidecar-authority": sidecar("authority.generation", GEN),
    "filename-replacement": replace_name,
    "filename-hardlink-companion": hardlink_companion,
    "directory-replacement": replace_directory,
    "directory-companion": companion_directory,
    "xattr": set_xattr,
    "external-ledger": external_ledger,
}


def read_back(directory):
    """B7: 台帳 sibling と xattr を読み戻し、entry を全列挙する。"""
    entries = sorted(
        str(p.relative_to(directory)) for p in directory.rglob("*")
    )
    ledger = directory.with_name(directory.name + ".ledger")
    xattr_value = None
    lease = directory / "acceptance.lease"
    if lease.exists():
        try:
            xattr_value = os.getxattr(
                lease, b"user.izanagi_lease_generation"
            ).decode("ascii")
        except OSError as exc:
            xattr_value = f"<{type(exc).__name__}:{exc.errno}>"
    return {
        "entries_after": entries,
        "ledger_exists": ledger.exists(),
        "ledger_content": ledger.read_text(encoding="ascii").strip()
        if ledger.exists() else None,
        "xattr_after": xattr_value,
    }


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for label, mutate in SCENARIOS.items():
        for action in ("claim", "release", "status", "renew"):
            directory = Path(tempfile.mkdtemp(
                prefix=f"p1-{label}-{action}-", dir=SCRATCH
            ))
            invoke([
                "claim", "--lease-dir", str(directory),
                "--wave", "probe-wave-A", "--main-sha", SHA_A,
            ])
            record = {"scenario": label, "action": action}
            try:
                mutate(directory)
            except OSError as exc:
                record["unsupported"] = f"{type(exc).__name__}:{exc.errno}"
                print(json.dumps(record, sort_keys=True))
                continue
            if action == "claim":
                rc, result = invoke([
                    "claim", "--lease-dir", str(directory),
                    "--wave", "probe-wave-B", "--main-sha", SHA_B,
                ])
            elif action == "release":
                rc, result = invoke([
                    "release", "--lease-dir", str(directory),
                    "--wave", "probe-wave-A",
                ])
            elif action == "status":
                rc, result = invoke([
                    "status", "--lease-dir", str(directory),
                    "--wave", "probe-wave-A", "--json",
                ])
            else:
                # renew は CLI subcommand を持たないので module API を直接叩く。
                rc = 0
                try:
                    result = WLW.renew(directory, "probe-wave-A")
                except Exception as exc:  # noqa: BLE001
                    rc = -1
                    result = {"_exception": type(exc).__name__}
            record["rc"] = rc
            record["state"] = result.get("state")
            source = result.get("source")
            record["reason"] = (
                source.get("reason") if isinstance(source, dict) else None
            )
            record["holder"] = result.get("holder")
            record.update(read_back(directory))
            print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
```
