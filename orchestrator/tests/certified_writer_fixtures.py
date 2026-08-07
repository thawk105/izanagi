"""Hermetic valid evidence fixtures for certified-writer admission tests."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from qualification import contract


REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AdmissionFixture:
    repo_root: Path
    receipts: dict[str, Path]
    environments: dict[str, dict[str, str]]
    shared_floor_walltime_s: int
    t126_walltime_s: int


def _git(repo: Path, *args: str) -> str:
    git_env = os.environ.copy()
    git_env.update({
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
    })
    completed = subprocess.run(
        ["git", "-c", "core.hooksPath=", "-c", "commit.gpgSign=false",
         "-C", str(repo), *args],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=git_env,
    )
    return completed.stdout.strip()


def _write_json(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(
            value, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("ascii") + b"\n"
    )
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _captures() -> dict[str, dict[str, object]]:
    return {
        name: {"rc": 0, "stdout_raw": f"{name} ok\n", "stderr_raw": ""}
        for name in ("qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota")
    }


def _ledger_event(
        index: int, previous: str, series_id: str, event_type: str,
        payload: dict[str, object],
) -> dict[str, object]:
    unhashed = {
        "schema_version": "t126-series-attempt-ledger-event/v1",
        "qualification_lineage": "t126-only",
        "event_index": index,
        "previous_event_sha256": previous,
        "qualification_series_id": series_id,
        "event_type": event_type,
        "payload": payload,
    }
    return {
        **unhashed,
        "event_sha256": hashlib.sha256(
            contract.canonical_json_bytes(unhashed)
        ).hexdigest(),
    }


def build_admission_fixture(
        directory: Path, *, shared_floor_walltime_s: int = 35999,
) -> AdmissionFixture:
    """Create valid floor and T126 receipts over one local Git repository."""
    repo = directory / "certified-writer-repo"
    repo.mkdir(parents=True)

    copied = (
        "tools/pegasus/floor_campaign.sh",
        "tools/pegasus/t126_qualification.sh",
        "tools/pegasus/collect_t126_qualification.py",
        "orchestrator/qualification/t126_control_v1.json",
        contract.RESERVATION_POLICY_RELATIVE_PATH,
    )
    for relative in copied:
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)

    shared_policy = json.loads(
        (REPO / "tools/pegasus/policy.json").read_text(encoding="utf-8")
    )
    shared_policy["floor_walltime_s"] = shared_floor_walltime_s
    _write_json(repo / "tools/pegasus/policy.json", shared_policy)
    floor_protocol = repo / "output/s8b-freeze/floor_protocol.json"
    floor_protocol.parent.mkdir(parents=True)
    shutil.copy2(REPO / "output/s8b-freeze/floor_protocol.json", floor_protocol)

    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "add", ".")
    gitlink = "1" * 40
    _git(
        repo, "update-index", "--add", "--cacheinfo",
        f"160000,{gitlink},external/ccbench",
    )
    _git(repo, "commit", "-qm", "certified writer fixture")
    source_commit = _git(repo, "rev-parse", "HEAD")
    source_tree = _git(repo, "rev-parse", "HEAD^{tree}")

    floor_nonce = "a" * 32
    floor_job = "floor.123"
    floor_receipt = _write_json(
        repo / "output/env/pegasus/floor/submissions/floor-receipt.json",
        {
            "schema_version": "pegasus-floor-submit-receipt/v1",
            "source_commit": source_commit,
            "job_script_path": "tools/pegasus/floor_campaign.sh",
            "job_script_sha256": _sha256(
                repo / "tools/pegasus/floor_campaign.sh"
            ),
            "job_id": floor_job,
            "nonce": floor_nonce,
            "submitted_at": 1,
            "request": {
                "project": shared_policy["project"],
                "queue": shared_policy["queue"],
                "nodes": shared_policy["nodes"],
                "elapstim_req_s": shared_floor_walltime_s,
            },
            "preflight": _captures(),
            "dry_run": False,
        },
    )

    reservation = json.loads(
        (repo / contract.RESERVATION_POLICY_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    t126_walltime_s = reservation["t126_qualification_walltime_s"]
    protocol_path = repo / "orchestrator/qualification/t126_control_v1.json"
    job_path = repo / "tools/pegasus/t126_qualification.sh"
    collector_path = repo / "tools/pegasus/collect_t126_qualification.py"
    protocol = contract.load_protocol_bytes(protocol_path.read_bytes())
    series_id = "2" * 64
    nonce = "b" * 32
    job_id = "t126.456"
    intent_sha = "3" * 64
    invocation_path = _write_json(
        repo / "output/env/pegasus/qualification/t126/submissions/fixture/"
        "qsub-invocation.json",
        {
            "nonce": nonce,
            "retry_index": 0,
            "submission_intent_sha256": intent_sha,
        },
    )
    invocation_sha = _sha256(invocation_path)
    binding_path = _write_json(
        invocation_path.parent / "qsub-binding.json",
        {
            "schema_version": "t126-qsub-binding/v2",
            "job_id": job_id,
            "nonce": nonce,
            "submission_intent_sha256": intent_sha,
            "qsub_invocation_sha256": invocation_sha,
            "retry_index": 0,
            "qsub_returncode": 0,
            "qsub_stdout_raw": f"Request {job_id} submitted.\n",
        },
    )
    binding_sha = _sha256(binding_path)
    attempt_id = contract.attempt_identity({
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": series_id,
        "pbs_job_id": job_id,
        "nonce": nonce,
        "retry_index": 0,
        "submission_intent_sha256": intent_sha,
    })

    initial = _ledger_event(
        0, "0" * 64, series_id, "initial_intent",
        {
            "nonce": nonce,
            "retry_index": 0,
            "submission_intent_sha256": intent_sha,
        },
    )
    submitted = _ledger_event(
        1, initial["event_sha256"], series_id, "initial_submitted",
        {
            "nonce": nonce,
            "retry_index": 0,
            "job_id": job_id,
            "qualification_attempt_id": attempt_id,
            "qsub_invocation_sha256": invocation_sha,
            "submission_evidence_sha256": binding_sha,
        },
    )
    ledger = (
        repo / "output/env/pegasus/qualification/t126/series"
        / series_id / "attempt-ledger"
    )
    _write_json(ledger / "0000.json", initial)
    _write_json(ledger / "0001.json", submitted)

    t126_receipt = _write_json(
        invocation_path.parent / "submit-receipt.json",
        {
            "schema_version": "t126-qualification-submit-receipt/v1",
            "qualification_lineage": "t126-only",
            "authority": "evidence-only/no-promotion",
            "hold_enforced": False,
            "job_id": job_id,
            "qualification_series_id": series_id,
            "qualification_attempt_id": attempt_id,
            "nonce": nonce,
            "source_commit": source_commit,
            "source_tree": source_tree,
            "ccbench_gitlink": gitlink,
            "job_script_sha256": _sha256(job_path),
            "collector_sha256": _sha256(collector_path),
            "protocol_sha256": _sha256(protocol_path),
            "request": {
                "project": shared_policy["project"],
                "queue": shared_policy["queue"],
                "nodes": shared_policy["nodes"],
                "elapstim_req_s": t126_walltime_s,
            },
            "preflight": _captures(),
            "retry_index": 0,
            "retry_from_attempt_id": None,
            "retry_from_series_id": None,
            "retry_receipt_sha256": None,
            "submission_intent_sha256": intent_sha,
            "qsub_invocation_sha256": invocation_sha,
            "qsub_binding_sha256": binding_sha,
            "dry_run": False,
            "submitted_epoch": 1,
        },
    )
    assert protocol["environment"]["env_tag"] == "pegasus"
    return AdmissionFixture(
        repo_root=repo,
        receipts={"floor": floor_receipt, "t126": t126_receipt},
        environments={
            "floor": {
                "IZANAGI_SUBMISSION_NONCE": floor_nonce,
                "PBS_JOBID": floor_job,
            },
            "t126": {
                "IZANAGI_SUBMISSION_NONCE": nonce,
                "PBS_JOBID": job_id,
            },
        },
        shared_floor_walltime_s=shared_floor_walltime_s,
        t126_walltime_s=t126_walltime_s,
    )


def build_source_drift_fixture(directory: Path) -> tuple[Path, Path, str]:
    """Commit adapter A, then fail-open one imported domain module in B."""
    repo = directory / "source-drift-repo"
    shutil.copytree(
        REPO / "orchestrator", repo / "orchestrator",
        ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc"),
    )
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "source-bound adapter A")
    source_commit = _git(repo, "rev-parse", "HEAD")
    admission = repo / "orchestrator/campaign/certified_writer_admission.py"
    with admission.open("a", encoding="utf-8") as stream:
        stream.write(
            "\n\ndef admit(*_args, **_kwargs):\n"
            "    return None  # fixture fail-open B\n"
        )
    receipt = _write_json(
        directory / "source-drift-receipt.json",
        {"source_commit": source_commit},
    )
    helper_source = _git(
        repo, "show",
        f"{source_commit}:orchestrator/campaign/certified_writer_preflight.py",
    )
    return repo, receipt, helper_source
