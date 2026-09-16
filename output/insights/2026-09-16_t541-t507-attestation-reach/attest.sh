#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:05:00

set -eu
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t541-t507-attestation
exec python3.10 -B - <<'PY'
import dataclasses
import json
import os
from pathlib import Path
import socket
import subprocess

from orchestrator.campaign import env_attestation, env_contract
from orchestrator.qualification.t126_driver import _attest

repo_root = Path.cwd().resolve()
contract = env_contract.lookup("pegasus")
print(json.dumps({
    "repo_root": str(repo_root),
    "commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip(),
    "pbs_job_id": os.environ.get("PBS_JOBID"),
    "host": socket.gethostname(),
    "calibration_ref": dataclasses.asdict(contract.calibration_ref),
    "contract_sha256": contract.contract_sha256,
}, sort_keys=True), flush=True)
recorded_comparisons = []
real_compare_profiles = env_attestation.compare_profiles


def record_compare_profiles(expected, observed, *, now_fn):
    rows = real_compare_profiles(expected, observed, now_fn=now_fn)
    recorded_comparisons.extend(rows)
    return rows


env_attestation.compare_profiles = record_compare_profiles
try:
    payload = _attest(repo_root, contract)
except Exception:
    print(json.dumps({
        "non_pass_comparisons": [
            row for row in recorded_comparisons if row.get("verdict") != "pass"
        ],
    }, sort_keys=True, ensure_ascii=True), flush=True)
    # Re-raise to preserve the traceback on stderr and a nonzero job exit.
    raise
finally:
    env_attestation.compare_profiles = real_compare_profiles
print(json.dumps(payload, sort_keys=True, ensure_ascii=True), flush=True)
PY
