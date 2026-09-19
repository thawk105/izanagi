"""One-shot two-node real flock probe; no campaign, binaries, or production timeout.

The parent supplies a fresh shared T2489_PROBE_OUT directory. Every published
JSON is create-only. Local monotonic deadlines bound this experiment only;
cross-node concurrency is established by messages, never clock comparisons.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time

from orchestrator.campaign import lock


ROOT = Path(os.environ["T2489_REPO_ROOT"]).resolve(strict=True)
OUT = Path(os.environ["T2489_PROBE_OUT"]).resolve(strict=True)
SCRIPT = ROOT / "t2489_lock_probe.py"
WAIT_S = 45  # Experimental message bound only; not a production budget.
CASES = (("candidate", "candidate"), ("default", "default"),
         ("candidate", "default"), ("default", "candidate"))


def publish(name, value):
    destination = OUT / (name + ".json")
    pending = OUT / (name + f".{os.getpid()}.pending")
    with pending.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(pending, destination)  # Atomic visibility and no overwrite.
    pending.unlink()
    fd = os.open(OUT, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def wait(name):
    deadline = time.monotonic() + WAIT_S
    while time.monotonic() < deadline:
        try:
            return json.loads((OUT / (name + ".json")).read_text())
        except FileNotFoundError:
            time.sleep(0.1)
    raise TimeoutError(f"incomplete probe: {name}")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def candidate_from_job():
    job = ROOT / "tools/pegasus/paper_story_a2_certification.sh"
    lines = job.read_text().splitlines()
    base = 'scratch_base=/scr/${USER}/paper-story-a2-certification'
    export = 'export IZANAGI_BENCH_LOCK="$scratch_base/bench.lock"'
    mkdir = 'mkdir -p "$scratch_base"'
    for line in (base, export, mkdir):
        if lines.count(line) != 1:
            raise RuntimeError(f"candidate job body missing exact line: {line}")
    if sum("IZANAGI_BENCH_LOCK" in line for line in lines) != 1:
        raise RuntimeError("ambiguous job body lock assignment")
    preflight = next(i for i, line in enumerate(lines)
                     if '"${POLICY_ARGS[@]}" compute-preflight' in line)
    workload = next(i for i, line in enumerate(lines)
                    if '"${POLICY_ARGS[@]}" run-workload' in line)
    if not (lines.index(base) < lines.index(mkdir) < lines.index(export)
            < preflight < workload):
        raise RuntimeError("candidate export is not before both driver calls")
    # Evaluate the validated assignment lines from the real job, not a separate
    # handwritten candidate path. Do not execute the job or its mkdir/staging.
    result = subprocess.run(
        ["bash", "-eu", "-c", base + "\n" + export
         + '\nprintf "%s" "$IZANAGI_BENCH_LOCK"'],
        check=True, capture_output=True, text=True)
    return result.stdout, {"job_sha256": digest(job),
                           "base_line": lines.index(base) + 1,
                           "export_line": lines.index(export) + 1,
                           "base_source": base, "export_source": export}


def snapshot(path):
    target = Path(path)
    stat = target.stat() if target.exists() else None
    return {
        "hostname": socket.gethostname(), "pid": os.getpid(),
        "cwd": str(Path.cwd()), "python": sys.executable,
        "python_version": sys.version, "path": str(target),
        "resolved_path": str(target.resolve()),
        "device": stat.st_dev if stat else None,
        "inode": stat.st_ino if stat else None,
        "environment": {key: os.environ.get(key) for key in (
            "PBS_JOBID", "PBS_NODEFILE", "PBS_O_WORKDIR", "USER", "HOME",
            "TMPDIR", "T2489_SCRATCH", "IZANAGI_BENCH_LOCK")},
        "home_realpath": str(Path.home().resolve()),
        "nodefile": Path(os.environ["PBS_NODEFILE"]).read_text(),
        "mountinfo": Path("/proc/self/mountinfo").read_text(),
        "code": {"probe_sha256": digest(SCRIPT),
                 "pbs_sha256": digest(ROOT / "t2489_lock_probe.pbs"),
                 "lock_sha256": digest(lock.__file__),
                 "head": subprocess.check_output(
                     ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()},
    }


def child(mode, name):
    path = lock.default_lock_path()
    try:
        with lock.bench_lock(path=None, blocking=False):
            publish(name, {"status": "acquired", **snapshot(path)})
            if mode == "hold":
                wait(name + "-release")
        if mode == "hold":
            publish(name + "-released", {"status": "released"})
        return 0
    except lock.BenchBusy:
        publish(name, {"status": "busy", **snapshot(path)})
        return 0  # An observation; the coordinator assigns its meaning.


def start(kind, mode, name, candidate):
    environment = dict(os.environ)
    environment.pop("IZANAGI_BENCH_LOCK", None)
    if kind == "candidate":
        environment["IZANAGI_BENCH_LOCK"] = candidate
    # Separate processes receive separate job-like scratch and TMPDIR, but
    # exactly the same real HOME. Never unlink either real lock file.
    scratch = Path(tempfile.mkdtemp(prefix="t2489-", dir=str(Path(candidate).parent)))
    (scratch / "tmp").mkdir()
    environment["T2489_SCRATCH"] = str(scratch)
    environment["TMPDIR"] = str(scratch / "tmp")
    return subprocess.Popen(
        ["python3.10", "-B", str(SCRIPT), "child", mode, name],
        cwd=ROOT, env=environment)


def attempt(kind, name, candidate):
    process = start(kind, "try", name, candidate)
    try:
        rc = process.wait(timeout=WAIT_S)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise
    if rc != 0:
        raise RuntimeError(f"child failed, not lock evidence: {name}, rc={rc}")
    return wait(name)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def coordinate(rank):
    candidate, source = candidate_from_job()
    require(re.fullmatch(r"bnode[0-9]+(?:\..*)?", socket.gethostname()),
            "probe must run on compute nodes")
    require(Path.cwd() == ROOT, "cwd differs from T2489_REPO_ROOT")
    Path(candidate).parent.mkdir(parents=True, exist_ok=True)
    publish(f"rank{rank}-environment", {**snapshot(candidate), **source})
    other = wait(f"rank{1-rank}-environment")
    own = wait(f"rank{rank}-environment")
    hosts = {own["hostname"], other["hostname"]}
    require(len(hosts) == 2, "two different compute nodes required")
    require(set(own["nodefile"].split()) == hosts
            == set(other["nodefile"].split()), "nodefile does not bind both hosts")
    require(own["home_realpath"] == other["home_realpath"]
            and own["environment"]["HOME"] == other["environment"]["HOME"]
            and own["environment"]["USER"] == other["environment"]["USER"],
            "default controls require identical real HOME and USER")
    require(own["path"] == other["path"] and own["code"] == other["code"]
            and own["job_sha256"] == other["job_sha256"],
            "nodes disagree on candidate path or executed code")
    require(own["environment"]["PBS_JOBID"].split(":", 1)[1]
            == other["environment"]["PBS_JOBID"].split(":", 1)[1],
            "ranks belong to different requests")
    # Serialize availability checks; neither check may itself cause BenchBusy.
    if rank == 1:
        wait("rank0-default-available")
    available = attempt("default", f"rank{rank}-default-check", candidate)
    require(available["status"] == "acquired",
            "inconclusive: default lock already held by another process")
    publish(f"rank{rank}-default-available", {"status": "available"})
    wait(f"rank{1-rank}-default-available")

    observations = []
    for holder_kind, challenger_kind in CASES:
        name = holder_kind + "-to-" + challenger_kind
        if rank == 1:
            held = wait(name + "-held")
            require(held["status"] == "acquired", "holder could not acquire")
            if holder_kind == challenger_kind:
                attempt(challenger_kind, name + "-remote", candidate)
            wait(name + "-held-released")
            continue
        holder = start(holder_kind, "hold", name + "-held", candidate)
        try:
            held = wait(name + "-held")
            require(held["status"] == "acquired",
                    "inconclusive: holder lock already busy")
            local = attempt(challenger_kind, name + "-local", candidate)
            remote = (wait(name + "-remote")
                      if holder_kind == challenger_kind else None)
            require(holder.poll() is None, "holder exited before challenge results")
        finally:
            publish(name + "-held-release", {"reason": "challenge results or error"})
            try:
                rc = holder.wait(timeout=WAIT_S)
            except subprocess.TimeoutExpired:
                holder.kill()
                holder.wait()
                raise
        require(rc == 0, "holder failed, not lock evidence")
        wait(name + "-held-released")
        after = attempt(holder_kind, name + "-after-release", candidate)
        require(after["status"] == "acquired", "lock unavailable after release")
        require((held["device"], held["inode"])
                == (after["device"], after["inode"]), "lock inode changed after release")
        require(held["pid"] != local["pid"]
                and held["environment"]["TMPDIR"] != local["environment"]["TMPDIR"]
                and held["environment"]["T2489_SCRATCH"]
                != local["environment"]["T2489_SCRATCH"],
                "same-node challenge did not use a separate process/scratch")
        if holder_kind == challenger_kind:
            require(local["status"] == "busy", "same-node exclusion failed")
            require((held["device"], held["inode"])
                    == (local["device"], local["inode"]), "same-node inode differs")
            expected = "acquired" if holder_kind == "candidate" else "busy"
            require(remote["status"] == expected, "cross-node control failed")
        # Mixed paths are observations for adoption, not pass/fail requirements.
        observations.append({"case": name, "local": local["status"],
                             "remote": remote["status"] if remote else None,
                             "after_release": after["status"]})
    publish(f"rank{rank}-done", {"status": "complete", "observations": observations})
    wait(f"rank{1-rank}-done")
    return 0


if __name__ == "__main__":
    label = "-".join(sys.argv[1:])
    try:
        if sys.argv[1] == "child":
            result = child(sys.argv[2], sys.argv[3])
        else:
            rank = int(sys.argv[1])
            require(rank in (0, 1), "only rank0/rank1 are valid")
            require(os.environ["PBS_JOBID"].startswith(f"{rank}:"), "rank mismatch")
            result = coordinate(rank)
    except Exception as exc:
        publish(label + "-failure", {"status": "incomplete-or-inconclusive",
                                     "error": repr(exc), "pid": os.getpid()})
        raise
    raise SystemExit(result)
