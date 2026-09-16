# -*- coding: utf-8 -*-
"""Independent sentinels for the T-344 deny-only campaign overlay."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission as A
from orchestrator.campaign import (
    campaign_lock,
    contract_loader_binding,
    env_contract,
    ident,
    trigger_gate_binding,
    wal,
)
from orchestrator.campaign.build_admission import (
    GeneratorId,
    add_coder_build_authority_argument,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import (
    COMMIT_CONTRACT_SHA256_KEY,
    CampaignConfig,
    Genome,
)
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, SourceEvidence
from orchestrator.tests.campaign_lock_test_support import build_v2_campaign_lock
from orchestrator.tests import commit_receipt_support as receipt_support


ROOT = Path(__file__).resolve().parents[2]
CERTIFIED = A.CampaignReadPurpose.CERTIFIED_ACCEPTANCE
HISTORICAL = A.CampaignReadPurpose.HISTORICAL_RAW
_EXPECTED_PRE_T733_CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
)
_EXPECTED_E1_CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
    "orchestrator/campaign/verify_fanout_worker.py",
)
_FIXED_SYNTHETIC_E1_EPOCH = (
    "E1:73f334f62ec13c394aae3d4787b80117562187984b6e0e372f2c0f7058b8ced2"
)
_FIXED_ORDERED_CLOSURE_PATHS_SHA256 = (
    "2247e5312a327caca9d0d4be081457eaf196513764010f64ccad1561409399ec"
)
_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)
LEDGER_RAW_SHA256 = "f08ed2d0b265710286752cad74c12d1136ea0af7684e810b00e10867a71cef93"
EXPECTED_RECORDS = (
    (
        "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387",
        "p3-s4-loop-s4-autonomous-0b53a387",
        "0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9",
        "2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611",
        3,
    ),
    (
        "output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d",
        "p3-s5-sort-loop-s5-sort-autonomous-3be89e0d",
        "3be89e0ddad8e8b2b37d35168c49affe7889ea580831973dc0d6d9706aaa4f97",
        "b901f23a502e4d3843454de807ca01666c145ee7d9d424a957bb366ef3e793a5",
        1,
    ),
    (
        "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5",
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5",
        "3f72ecd58a6df4018d136bcbb8abb276114ba8d302c64aaf792c473ae4b1de0c",
        "a539648d29afce9be036eba519b53f21fd1f8e1fb7bfe24549f4ec3ceac31ea3",
        2,
    ),
)
KNOWN_HISTORICAL = (
    "output/campaigns/p2-2-silo-balanced-enumerate-f1588056",
    "f15880560640c76223fb7c20ed4f8b1e6d4596ae80c94bdbc55c95d5201a180f",
    "d6e98161d8cc3a011688316c3a180a532c0374c87fbbcc30934106f51f95f34c",
)
LEGACY_TRIGGER_CAMPAIGNS = (
    (
        "output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2",
        "b8f4a4e25158d0d9e6a5839da9a837d3d41af3af198e9da25ef76ae3b6557b88",
        "3e447c7dd44d6daf35105e0db0acfc02afc20c295016a60e763f3f3f5d0eca41",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8",
        "c2d838b89009ed499ac6e1f19990ad5653c0dde337859a012d934675bdd9b688",
        "d5ec15db79957e44f7d10a5adbcc7d069db2f587f170fd83ae0dfcfe56df428d",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7",
        "654d5cd73c0418e5cc6ce8924854528d35921d2ab7e850c7c2f1ea69eeeb3c41",
        "6c519d85c5704dcdf040a37e01eba6d86f0f4a4b535561880d6af6f905590f4c",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c",
        "8a237e8c48a3ed154840a167d8a6e43d843ebe1849bbadda885d8cb06a7b87f1",
        "aa04b36a3a48d006664589a5bc71242ebbd5c7ea9ea3c46ac171266f1516847e",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8",
        "a81ec3d876775cdee547c558d77fb4bc19515b89f76849acdd38f3d91bdd6be4",
        "d218f4e47685b6c3bb25e47119aa3ef509022d2dbf29e2a4acd2e294b0924bbd",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb",
        "dcd2bbfbd08942af7e2d49fd5c510ec657e89a630b2917ab55ed54d20619a55c",
        "194746d89f1c92ef72e24daf83620ff179c386819b86b91be8159740f01c9225",
    ),
)
ADMITTED_HISTORICAL_CAMPAIGNS = (
    "output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50",
    "output/campaigns/backoff-repro-silo-write-heavy-repro-181607af",
    "output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e",
    "output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9",
    "output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90",
    "output/campaigns/backoff-sweep-silo-read-heavy-sweep-8ff95955",
    "output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7",
    "output/campaigns/p2-2-silo-balanced-enumerate-f1588056",
    "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad",
    "output/campaigns/p2-2-silo-write-heavy-enumerate-8967bed6",
    "output/campaigns/p3-kickoff-coder-wiring-cba40400",
    "output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4",
    "output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e",
    "output/campaigns/p3-s6-sort-sweep-balanced-sweep-dd25aa8c",
    "output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef",
    "output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-d4552403",
    "output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2",
    "output/campaigns/s1-direct-block2-direct-comparison-9645b16a",
    "output/campaigns/s1-direct-develop-direct-comparison-7bccdf1a",
    "output/campaigns/s1-direct-develop-direct-comparison-d0f495bf",
    "output/campaigns/s1-direct-floor-direct-comparison-b82b9229",
)
EXPECTED_CAMPAIGN_CLASSIFICATIONS = {
    "backoff-repro-silo-balanced-repro-87dbbf50":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "backoff-repro-silo-write-heavy-repro-181607af":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "backoff-sweep-silo-balanced-sweep-484c663e":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "backoff-sweep-silo-read-heavy-sweep-610004b9":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "backoff-sweep-silo-read-heavy-sweep-6f169f90":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "backoff-sweep-silo-read-heavy-sweep-8ff95955":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "backoff-sweep-silo-write-heavy-sweep-493813a7":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p2-2-silo-balanced-enumerate-f1588056":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p2-2-silo-read-heavy-enumerate-5ffcabad":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p2-2-silo-write-heavy-enumerate-8967bed6":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-kickoff-coder-wiring-cba40400":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-s4-loop-s4-autonomous-0b53a387":
        ("overlay-denied", "legacy-unclassified"),
    "p3-s4-red-s4-red-consumer-9a1897c4":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-s5-sort-loop-s5-sort-autonomous-3be89e0d":
        ("overlay-denied", "legacy-unclassified"),
    "p3-s6-sort-sweep-balanced-sweep-1b39095e":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-s6-sort-sweep-balanced-sweep-dd25aa8c":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-s6-sort-sweep-write-heavy-sweep-0484feef":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-s6-sort-sweep-write-heavy-sweep-d4552403":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5":
        ("overlay-denied", "legacy-unclassified"),
    "p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2":
        ("historical-pre-admission-schema", "legacy-unclassified"),
    "p3-s8a-trigger-sweep-balanced-sweep-c2d838b8":
        ("historical-pre-admission-schema", "legacy-unclassified"),
    "p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7":
        ("historical-pre-admission-schema", "legacy-unclassified"),
    "p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c":
        ("historical-pre-admission-schema", "legacy-unclassified"),
    "p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8":
        ("historical-pre-admission-schema", "legacy-unclassified"),
    "p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb":
        ("historical-pre-admission-schema", "legacy-unclassified"),
    "s1-direct-block1-direct-comparison-74ff9ba2":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "s1-direct-block2-direct-comparison-9645b16a":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "s1-direct-develop-direct-comparison-7bccdf1a":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "s1-direct-develop-direct-comparison-d0f495bf":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
    "s1-direct-floor-direct-comparison-b82b9229":
        ("historical-pre-admission-schema", "historical-not-reclassified"),
}
EXPECTED_EVIDENCE_CAMPAIGN_LOCKS = frozenset({
    "output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/"
    "campaign-layout/campaigns/"
    "p3-t178-ycsb-a-workload-conditioned-autonomous-0a11751c/campaign.lock",
    "output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/"
    "campaign-layout/campaigns/"
    "p3-t178-ycsb-a-workload-conditioned-autonomous-9785aec6/campaign.lock",
})



# Independent declaration copied from 2a9ba783f^; never derive from production.
_EXPECTED_T733_EXACT62_CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
)

# Known answers computed once from the Git declaration above and the committed
# fixture bytes "epoch closure fixture {index}\n" (one-based declaration index).
# Epoch: SHA256(domain + sum(path UTF-8 + NUL + SHA256(fixture bytes))).
# Path hash: SHA256(sum(path UTF-8 + NUL)), in declaration order.
# Keep these literals fixed even if both production and expected tuples change.
_FIXED_T733_EXACT62_EPOCH = "E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9"
_FIXED_T733_EXACT62_PATH_SHA256 = "b274387d0be033a98e86d54e5225667221bde79776832e73fb3d07cebfc6067a"

def _canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _write_campaign(root: Path, lock: dict | str, records: list[dict]) -> Path:
    (root / "runs").mkdir(parents=True)
    lock_text = lock if type(lock) is str else _canonical_json(lock)
    (root / "campaign.lock").write_text(lock_text, encoding="utf-8")
    (root / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    return root


def _record(
        stage: str, payload: dict, *, ts: float,
        variant: str = "6a803ba39f7b", env_tag: str = "test",
) -> dict:
    return {
        "variant": variant, "stage": stage, "env_tag": env_tag, "ts": ts,
        "payload": payload,
    }


def _campaign_id_for_lock(lock: dict | str, *, slug: str = "campaign") -> str:
    if type(lock) is str:
        decoded = campaign_lock.decode_campaign_lock(lock)
        identity = decoded.identity
        identity_preimage = decoded.identity_preimage
    else:
        identity = lock
        identity_preimage = _canonical_json(lock)
    digest = hashlib.sha256(identity_preimage.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{identity['search_tag']}-{digest}"


def _rename_for_lock(campaign: Path) -> Path:
    lock = (campaign / "campaign.lock").read_text()
    expected = campaign.parent / _campaign_id_for_lock(lock)
    if expected != campaign:
        campaign.rename(expected)
    return expected


def _rewrite_v2_identity(lock_path: Path, mutate) -> None:
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    assert decoded.is_v2 and decoded.authority is not None
    identity = json.loads(decoded.identity_preimage)
    mutate(identity)
    lock_path.write_text(
        campaign_lock.encode_campaign_lock_v2(
            _canonical_json(identity), decoded.authority,
        ),
        encoding="utf-8",
    )


def _rewrite_v2_authority(lock_path: Path, **changes: object) -> None:
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    assert decoded.is_v2 and decoded.authority is not None
    authority = decoded.authority.as_dict()
    authority.update(changes)
    lock_path.write_text(
        campaign_lock.encode_campaign_lock_v2(
            decoded.identity_preimage,
            campaign_lock.CampaignLockAuthority(**authority),
        ),
        encoding="utf-8",
    )


def _rewrite_wal(campaign: Path, mutate) -> None:
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    mutate(records)
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _replace_receipted_commit(
        campaign: Path, mutate, *, operation_identity: str = "attempt-1",
        receipt_tags=("legacy",),
) -> None:
    """Reissue one fixture COMMIT after mutating its terminal preimage."""
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    commit = next(record for record in records if record["stage"] == "commit")
    records.remove(commit)
    terminal_payload = dict(commit["payload"])
    terminal_payload.pop("commit_verification_receipt")
    mutate(records, terminal_payload)
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    receipt_support.log_receipted_commit(
        CampaignLayout(root=str(campaign)), commit["variant"], commit["env_tag"],
        terminal_payload, operation_identity=operation_identity,
        tags=receipt_tags, ts=commit["ts"],
    )


def _fixture_git(repo: Path, *args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail(
            "artifact-admission Git infrastructure failure: git executable is unavailable"
        )
    git_env = {
        key: os.environ[key]
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    git_env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    try:
        completed = subprocess.run(
            [
                executable,
                "-c", "core.autocrlf=false",
                "-c", "core.fileMode=false",
                "-C", str(repo),
                *args,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=git_env,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "artifact-admission Git infrastructure failure: command timed out: "
            f"args={args!r}: {exc}"
        )
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.fail(
            "artifact-admission Git infrastructure failure: command could not run: "
            f"args={args!r}: {exc}"
        )
    if completed.returncode != 0:
        pytest.fail(
            "artifact-admission Git infrastructure failure: command returned nonzero: "
            f"args={args!r} rc={completed.returncode} "
            f"stderr={completed.stderr.decode('utf-8', errors='replace')!r}"
        )
    return completed.stdout


def _committed_closure_repo(tmp_path: Path) -> Path:
    """現行 checkout の hash を使わない exact 63-path E1 fixture。"""
    repo = tmp_path / "closure-repo"
    repo.mkdir()
    _fixture_git(repo, "init", "-q")
    for index, relative in enumerate(
        _EXPECTED_E1_CLOSURE_PATHS, start=1,
    ):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"epoch closure fixture {index}\n".encode("ascii"))
    _fixture_git(
        repo, "add", "--", *_EXPECTED_E1_CLOSURE_PATHS,
    )
    _fixture_git(
        repo,
        "-c", "user.email=epoch-fixture@example.invalid",
        "-c", "user.name=epoch fixture",
        "commit", "-q", "-m", "record closure A",
    )
    return repo


def _expected_fixture_epoch() -> str:
    payload = b"campaign-verifier-epoch/v1" + b"".join(
        relative.encode("utf-8")
        + b"\0"
        + hashlib.sha256(
            f"epoch closure fixture {index}\n".encode("ascii")
        ).digest()
        for index, relative in enumerate(
            _EXPECTED_E1_CLOSURE_PATHS, start=1,
        )
    )
    return f"E1:{hashlib.sha256(payload).hexdigest()}"


def _expected_pre_t733_fixture_epoch() -> str:
    payload = b"campaign-verifier-epoch/v1" + b"".join(
        relative.encode("utf-8")
        + b"\0"
        + hashlib.sha256(
            (
                "epoch closure fixture "
                f"{_EXPECTED_E1_CLOSURE_PATHS.index(relative) + 1}\n"
            ).encode("ascii")
        ).digest()
        for relative in _EXPECTED_PRE_T733_CLOSURE_PATHS
    )
    return f"E1:{hashlib.sha256(payload).hexdigest()}"


def _rewrite_as_pre_t733_lock(campaign: Path) -> bytes:
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(
        lock_path.read_text(encoding="utf-8")
    )
    assert decoded.is_v2 and decoded.authority is not None
    authority = decoded.authority.as_dict()
    blobs = authority["contract_loader_blob_sha256s"]
    authority["contract_loader_blob_sha256s"] = {
        relative: blobs[relative]
        for relative in campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
    }
    lock_text = _canonical_json({
        "schema_version": decoded.schema_version,
        "identity_preimage": decoded.identity_preimage,
        "authority": authority,
    })
    lock_path.write_text(lock_text, encoding="utf-8")
    return lock_text.encode("utf-8")


def _ordered_fixture_path_list_sha256() -> str:
    payload = b"".join(
        relative.encode("utf-8") + b"\0"
        for relative in _EXPECTED_E1_CLOSURE_PATHS
    )
    return hashlib.sha256(payload).hexdigest()


def _new_schema_campaign(
        tmp_path: Path, *, omit_receipt: bool = False,
        coder_authored: bool = False,
) -> Path:
    if coder_authored:
        parser = argparse.ArgumentParser(add_help=False)
        add_coder_build_authority_argument(parser)
        authority = parser.parse_args(
            ["--allow-coder-derived-build"]
        ).coder_build_authority
        context = build_run_context(
            generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
            coder_authority=authority,
        )
    else:
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    genome_value = Genome("silo", {"BACK_OFF": 0})
    genome = genome_value.canonical()
    src_token = "b" * 64 if coder_authored else "stock"
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(tmp_path.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.encode()).hexdigest(),
        src_token=src_token,
        source_bytes_sha256="a" * 64,
        tracked_clean=not coder_authored,
        tracked_diff_sha256=("c" * 64 if coder_authored
                             else EMPTY_TRACKED_DIFF_SHA256),
        tracked_paths=(("cc/silo/transaction.cc",) if coder_authored else ()),
    )
    admission = derive_build_admission(context, evidence)
    receipt = admission.as_wal_receipt()
    attempt_id = "attempt-1"
    start = {
        "build_attempt_id": attempt_id,
        "genome": genome,
        "src_token": src_token,
    }
    if not omit_receipt:
        start.update({
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        })
    lock = {
        "ccbench_commit": CURRENT_PIN,
        "search_config": {
            "records": 1,
            "threads": 1,
            "build_admission": dict(context.policy.as_preimage()),
        },
        "search_tag": "test",
        "spec_content": "test",
        "trial": "test",
    }
    authorization = env_contract.authorize("linux-baremetal")
    lock_text = build_v2_campaign_lock(
        _canonical_json(lock), authorization=authorization,
    )
    decoded = campaign_lock.decode_campaign_lock(lock_text)
    assert decoded.authority is not None
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    }
    # v2 envelope 剥離攻撃を忠実に再現できるよう、COMMIT は authority と同じ契約 hash を持つ。
    commit = {
        **terminal,
        COMMIT_CONTRACT_SHA256_KEY:
            decoded.authority.environment_contract_sha256,
    }
    variant = A.pipeline.variant_id(genome_value, src_token)
    env_tag = authorization.contract.env_tag
    records = [
        _record("build_start", start, ts=1.0, variant=variant, env_tag=env_tag),
        _record("build_done", terminal, ts=2.0, variant=variant, env_tag=env_tag),
        _record("verify_done", {
            "build_attempt_id": attempt_id,
            "verdict": "serializable",
            "certified": True,
            "anomalies": 0,
            "workload": {"tag": "legacy"},
        }, ts=3.0, variant=variant, env_tag=env_tag),
    ]
    campaign = _write_campaign(
        tmp_path / _campaign_id_for_lock(lock_text), lock_text, records,
    )
    receipt_support.log_receipted_commit(
        CampaignLayout(root=str(campaign)), variant, env_tag, commit,
        operation_identity=attempt_id, tags=("legacy",), ts=4.0,
    )
    return campaign


def _classify_as_trigger(
        campaign: Path, *, marker: bool, proposal: bool, binding: bool,
        axis: str = wal.TRIGGER_AXIS,
) -> Path:
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    assert decoded.is_v2 and decoded.authority is not None
    lock = dict(decoded.identity)
    lock["search_config"] = dict(lock["search_config"])
    search = lock["search_config"]
    search["axis"] = axis
    if proposal:
        search["reflux"] = "on"
    else:
        search.update({
            "generator": "reason-subset-v1",
            "space": "reason-subsets(effective)+identall+stock",
        })
    if marker:
        search[wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY] = trigger_gate_binding.SCHEMA_VERSION
    lock_path.write_text(campaign_lock.encode_campaign_lock_v2(
        _canonical_json(lock), decoded.authority,
    ), encoding="utf-8")
    if not binding:
        return _rename_for_lock(campaign)

    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    start = next(record for record in records if record["stage"] == "build_start")
    source = start["payload"]["build_admission"]["source"]
    value = trigger_gate_binding.TriggerGateBinding(
        mask=9,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(9),
        nonce="9" * 64,
        source=trigger_gate_binding.SourceBinding(
            src_token=source["src_token"],
            source_bytes_sha256=source["source_bytes_sha256"],
        ),
    )
    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY] = \
        trigger_gate_binding.commitment(value)
    raw = _record(trigger_gate_binding.WAL_RECORD_STAGE, {
        "build_attempt_id": start["payload"]["build_attempt_id"],
        wal.TRIGGER_BINDING_PAYLOAD_KEY: trigger_gate_binding.to_record(value),
    }, ts=start["ts"] - 0.5, env_tag=start["env_tag"])
    raw["variant"] = start["variant"]
    records.insert(records.index(start), raw)
    wal_path.write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    reports = campaign / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "p3_s8a_trigger_loop_provenance.json").write_text(json.dumps({
        "entries": {
            "1": {
                "build_attempt_id": start["payload"]["build_attempt_id"],
                "variant": start["variant"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY:
                    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
            },
        },
    }), encoding="utf-8")
    return _rename_for_lock(campaign)


def test_recovered_attempt_then_retry_is_admitted_without_read_mutation(tmp_path):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    original = wal.read_records(layout)
    start = original[0]
    (campaign / "runs/wal.jsonl").write_text(
        json.dumps({
            "variant": start.variant,
            "stage": start.stage,
            "env_tag": start.env_tag,
            "ts": start.ts,
            "payload": start.payload,
        }, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    crash_prefix = (campaign / "runs/wal.jsonl").read_bytes()
    policy = build_run_context(
        generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
    ).policy
    recovered = wal.recover_interrupted_attempts(
        layout, admission_policy=policy,
    )
    assert len(recovered) == 1
    retry_payload = dict(start.payload)
    retry_payload["build_attempt_id"] = "attempt-2"
    terminal_payload = {
        "build_attempt_id": "attempt-2",
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
    }
    wal.log(layout, start.variant, "build_start", start.env_tag, retry_payload)
    wal.log(layout, start.variant, "build_done", start.env_tag, terminal_payload)
    decoded = campaign_lock.decode_campaign_lock(Path(layout.lock_file).read_text())
    assert decoded.authority is not None
    receipt_support.log_receipted_commit(
        layout, start.variant, start.env_tag, {
        **terminal_payload,
        COMMIT_CONTRACT_SHA256_KEY:
            decoded.authority.environment_contract_sha256,
        }, operation_identity="attempt-2",
    )
    before_admission = (campaign / "runs/wal.jsonl").read_bytes()

    admitted = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert admitted.decision.admitted
    assert before_admission.startswith(crash_prefix)
    assert (campaign / "runs/wal.jsonl").read_bytes() == before_admission


@pytest.mark.parametrize("extra_key,extra_value", [
    ("build_admission", {"forged": "body"}),
    ("fitness_tps", 999999999),
    ("verify", {"verdict": "forged"}),
], ids=["build-admission", "fitness-tps", "verify"])
def test_recovery_abort_extra_keys_are_rejected_by_replay_and_admission(
        tmp_path, extra_key, extra_value):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    payload = {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": start.payload["build_attempt_id"],
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
        extra_key: extra_value,
    }
    records = [
        _record("build_start", start.payload, ts=1.0, variant=start.variant),
        _record("abort", payload, ts=2.0, variant=start.variant),
    ]
    (campaign / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    with pytest.raises(wal.AttemptTopologyError, match="exact key"):
        wal.replay(layout, admission_policy=policy)
    with pytest.raises(A.ArtifactAdmissionError, match="exact key"):
        A.require_admitted_campaign(campaign, purpose=HISTORICAL)


@pytest.mark.parametrize("schema_key,schema_value", [
    ("build_attempt_id", "orphan-attempt"),
    ("build_admission", {"schema": "marker-only"}),
    ("build_admission_receipt_sha256", "a" * 64),
    (wal.TRIGGER_BINDING_COMMITMENT_KEY, "b" * 64),
], ids=[
    "build-attempt-id", "build-admission", "receipt-sha256",
    "trigger-commitment",
])
def test_each_attempt_schema_key_independently_enables_strict_recovery_validation(
        tmp_path, schema_key, schema_value):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    malformed = _record(
        "build_done", {schema_key: schema_value}, ts=1.0,
        variant="schema-marker-v",
    )
    wal_path = campaign / "runs/wal.jsonl"
    wal_path.write_text(
        json.dumps(malformed, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    before = wal_path.read_bytes()
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    with pytest.raises(wal.InterruptedAttemptRecoveryError) as excinfo:
        wal.recover_interrupted_attempts(layout, admission_policy=policy)
    assert excinfo.value.condition == "existing-topology-violation"
    assert wal_path.read_bytes() == before


def _append_committed_retry(layout, start, attempt_id: str) -> None:
    retry_start = dict(start.payload)
    retry_start["build_attempt_id"] = attempt_id
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
    }
    wal.log(layout, start.variant, "build_start", start.env_tag, retry_start)
    wal.log(layout, start.variant, "build_done", start.env_tag, terminal)
    decoded = campaign_lock.decode_campaign_lock(Path(layout.lock_file).read_text())
    assert decoded.authority is not None
    receipt_support.log_receipted_commit(
        layout, start.variant, start.env_tag, {
        **terminal,
        COMMIT_CONTRACT_SHA256_KEY:
            decoded.authority.environment_contract_sha256,
        }, operation_identity=attempt_id,
    )


def test_historical_signal_does_not_overreject_later_start_only_recovery(tmp_path):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    first_terminal = {
        "build_attempt_id": "historical-attempt",
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
    }
    first_start = dict(start.payload)
    first_start["build_attempt_id"] = "historical-attempt"
    active_start = dict(start.payload)
    active_start["build_attempt_id"] = "active-attempt"
    records = [
        _record("build_start", first_start, ts=1.0, variant=start.variant),
        _record("build_done", first_terminal, ts=2.0, variant=start.variant),
        _record("verify_done", {"verdict": "red"}, ts=3.0, variant=start.variant),
        _record("abort", {**first_terminal, "reason": "verify-failed"},
                ts=4.0, variant=start.variant),
        _record("build_start", active_start, ts=5.0, variant=start.variant),
    ]
    (campaign / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    recovered = wal.recover_interrupted_attempts(layout, admission_policy=policy)
    assert len(recovered) == 1
    assert recovered[0].payload["build_attempt_id"] == "active-attempt"
    _append_committed_retry(layout, start, "retry-attempt")
    before_admission = (campaign / "runs/wal.jsonl").read_bytes()
    assert A.require_admitted_campaign(
        campaign, purpose=HISTORICAL,
    ).decision.admitted
    assert (campaign / "runs/wal.jsonl").read_bytes() == before_admission


def test_other_variant_recovery_limit_does_not_overreject_first_recovery(tmp_path):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    records = []
    for index in range(wal.INCOMPLETE_ATTEMPT_RECOVERY_LIMIT):
        attempt_id = f"variant-a-attempt-{index}"
        records.extend([
            _record("build_start", {"build_attempt_id": attempt_id},
                    ts=float(index * 2 + 1), variant="variant-a"),
            _record("abort", {
                "reason": "recovery-abort-incomplete-attempt",
                "build_attempt_id": attempt_id,
            }, ts=float(index * 2 + 2), variant="variant-a"),
        ])
    active_start = dict(start.payload)
    active_start["build_attempt_id"] = "variant-b-active"
    records.append(_record(
        "build_start", active_start, ts=10.0, variant=start.variant,
    ))
    (campaign / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    recovered = wal.recover_interrupted_attempts(layout, admission_policy=policy)
    assert len(recovered) == 1
    assert recovered[0].variant == start.variant
    assert recovered[0].payload["build_attempt_id"] == "variant-b-active"
    _append_committed_retry(layout, start, "variant-b-retry")
    before_admission = (campaign / "runs/wal.jsonl").read_bytes()
    assert A.require_admitted_campaign(
        campaign, purpose=HISTORICAL,
    ).decision.admitted
    assert (campaign / "runs/wal.jsonl").read_bytes() == before_admission


def test_overlay_raw_sha_and_exact_membership_are_independently_pinned() -> None:
    raw = A.LEDGER_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == LEDGER_RAW_SHA256
    ledger = json.loads(raw)
    assert len(ledger["records"]) == 3
    actual = tuple(
        (
            record["path"], record["campaign_id"],
            record["campaign_lock_sha256"], record["wal_sha256"],
            record["build_start_count"],
        )
        for record in ledger["records"]
    )
    assert actual == EXPECTED_RECORDS


def test_trusted_snapshot_campaign_corpus_is_fully_enumerated() -> None:
    ledger = json.loads(A.LEDGER_PATH.read_bytes())
    completed = subprocess.run(
        [
            "git", "-C", str(ROOT), "ls-tree", "-r", "--name-only",
            ledger["created_from_commit"], "--", "output/campaigns",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    actual = {
        path.removesuffix("/campaign.lock")
        for path in completed.stdout.splitlines()
        if path.endswith("/campaign.lock")
    }
    overlay = {path for path, *_rest in EXPECTED_RECORDS}
    legacy_trigger = {path for path, _lock_sha, _wal_sha in LEGACY_TRIGGER_CAMPAIGNS}
    admitted_historical = set(ADMITTED_HISTORICAL_CAMPAIGNS)

    assert actual == overlay | legacy_trigger | admitted_historical


def test_existing_campaign_tracked_bytes_match_git_head() -> None:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("git is required to prove output/campaigns tracked bytes")
    try:
        completed = subprocess.run(
            [
                executable, "-C", str(ROOT), "diff", "--quiet", "HEAD", "--",
                "output/campaigns",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.fail(f"git diff for output/campaigns could not run: {exc}")
    assert completed.returncode == 0, (
        "tracked output/campaigns bytes differ from git HEAD: "
        f"rc={completed.returncode} "
        f"stderr={completed.stderr.decode('utf-8', errors='replace')!r}"
    )


def test_existing_campaign_lock_corpus_is_exactly_32_v1_locks() -> None:
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "output").glob("**/campaign.lock")
    }
    expected_paths = {
        f"output/campaigns/{name}/campaign.lock"
        for name in EXPECTED_CAMPAIGN_CLASSIFICATIONS
    } | set(EXPECTED_EVIDENCE_CAMPAIGN_LOCKS)
    assert len(actual_paths) == 32
    assert actual_paths == expected_paths

    schema_versions = {
        relative: campaign_lock.decode_campaign_lock(
            (ROOT / relative).read_text(encoding="utf-8")
        ).schema_version
        for relative in sorted(actual_paths)
    }
    assert set(schema_versions.values()) == {"campaign-lock/v1"}


def test_existing_campaign_classification_exact_mapping() -> None:
    actual = {
        campaign.name: (
            decision.classification,
            decision.admission_status,
        )
        for campaign in sorted((ROOT / "output/campaigns").iterdir())
        if campaign.is_dir()
        for decision in (A.classify_campaign(campaign),)
    }
    assert actual == EXPECTED_CAMPAIGN_CLASSIFICATIONS


@pytest.mark.parametrize(
    "campaign_path",
    sorted(
        lock_path.removesuffix("/campaign.lock")
        for lock_path in EXPECTED_EVIDENCE_CAMPAIGN_LOCKS
    ),
    ids=lambda campaign_path: Path(campaign_path).name,
)
def test_existing_evidence_campaign_classification_exact_rejection(
    campaign_path: str,
) -> None:
    with pytest.raises(A.ArtifactAdmissionError) as exc_info:
        A.classify_campaign(ROOT / campaign_path)
    assert type(exc_info.value) is A.ArtifactAdmissionError
    assert str(exc_info.value) == (
        "campaign requires a directory, campaign.lock, and WAL"
    )


@pytest.mark.parametrize(
    ("lock", "expected"),
    [
        pytest.param(
            {
                "search_config": {
                    "axis": wal.TRIGGER_AXIS,
                    "generator": "reason-subset-v1",
                    "space": "reason-subsets(effective)+identall+stock",
                },
            },
            True,
            id="trigger-machine-shape",
        ),
        pytest.param(
            {"search_config": {"axis": wal.TRIGGER_AXIS, "reflux": "on"}},
            True,
            id="trigger-proposal-shape",
        ),
        pytest.param(
            {"search_config": {"axis": wal.TRIGGER_AXIS, "unknown": "shape"}},
            True,
            id="trigger-unknown-shape",
        ),
        pytest.param(
            {"search_config": {"axis": "silo-writeset-sort"}},
            False,
            id="non-trigger-axis",
        ),
        pytest.param(
            {"search_config": []}, False, id="search-config-not-dict",
        ),
        pytest.param({}, False, id="search-config-absent"),
        pytest.param([], False, id="lock-not-dict"),
    ],
)
def test_is_legacy_trigger_lock_truth_table(lock: object, expected: bool) -> None:
    assert A._is_legacy_trigger_lock(lock) is expected


def test_three_legacy_campaigns_are_denied() -> None:
    for path, campaign_id, lock_sha, wal_sha, count in EXPECTED_RECORDS:
        campaign = ROOT / path
        decision = A.classify_campaign(campaign)
        assert decision.classification == "overlay-denied"
        assert decision.admission_status == "legacy-unclassified"
        assert decision.verification_status == "historically-certified"
        assert decision.campaign_id == campaign_id
        assert decision.campaign_lock_sha256 == lock_sha
        assert decision.wal_sha256 == wal_sha
        assert decision.overlay_ledger_sha256 == LEDGER_RAW_SHA256
        assert count == sum(
            '"stage":"build_start"' in line
            for line in (campaign / "runs/wal.jsonl").read_text().splitlines()
        )
        with pytest.raises(
            A.CampaignNotAdmitted, match="legacy-unclassified",
        ) as excinfo:
            A.require_admitted_campaign(campaign, purpose=CERTIFIED)
        assert type(excinfo.value) is A.CampaignNotAdmitted


@pytest.mark.parametrize(
    ("path", "lock_sha", "wal_sha"),
    LEGACY_TRIGGER_CAMPAIGNS,
    ids=[Path(path).name for path, _lock_sha, _wal_sha in LEGACY_TRIGGER_CAMPAIGNS],
)
def test_legacy_trigger_campaigns_are_not_admitted(
    path: str, lock_sha: str, wal_sha: str,
) -> None:
    campaign = ROOT / path
    assert (
        hashlib.sha256((campaign / "campaign.lock").read_bytes()).hexdigest()
        == lock_sha
    )
    assert (
        hashlib.sha256((campaign / "runs/wal.jsonl").read_bytes()).hexdigest()
        == wal_sha
    )

    decision = A.classify_campaign(campaign)
    assert decision.classification == "historical-pre-admission-schema"
    assert decision.admission_status == "legacy-unclassified"
    with pytest.raises(
        A.CampaignNotAdmitted, match="legacy-unclassified",
    ) as excinfo:
        A.require_admitted_campaign(campaign, purpose=CERTIFIED)
    assert type(excinfo.value) is A.CampaignNotAdmitted


@pytest.mark.parametrize(
    "path",
    ADMITTED_HISTORICAL_CAMPAIGNS,
    ids=[Path(path).name for path in ADMITTED_HISTORICAL_CAMPAIGNS],
)
def test_nontrigger_historical_campaigns_remain_admitted(path: str) -> None:
    admitted = A.require_admitted_campaign(ROOT / path, purpose=HISTORICAL)
    assert admitted.decision.classification == "historical-pre-admission-schema"
    assert admitted.decision.admission_status == "historical-not-reclassified"


def test_real_e0_is_rejected_only_by_certified_epoch_gate() -> None:
    campaign = (
        ROOT
        / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
    )
    decision = A.classify_campaign(campaign)
    assert decision.admitted
    assert decision.classification == "historical-pre-admission-schema"

    with pytest.raises(A.CampaignVerifierEpochRejected) as excinfo:
        A.require_admitted_campaign(campaign, purpose=CERTIFIED)
    assert excinfo.value.campaign_verifier_epoch == "E0"
    assert excinfo.value.epoch_state == "E0"
    assert excinfo.value.reason_code == "v1-authority-absent"
    assert excinfo.value.identity_scope == (
        "enforcement source closure (curated exact 62 path; 2026-09-01 の静的 import "
        "発見集合 131 module のうち、既存 24、明示 import 先 36、実行時 package 初期化 "
        "2 を収載; source-import 推移閉包ではない)"
    )
    assert excinfo.value.excluded_scope == (
        "同発見集合の未収載 69 module、orchestrator/verifier/__main__.py、"
        "orchestrator/verifier/cli.py、package 外の orchestrator/verify.py、および "
        "data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 "
        "import を含む非 import 委譲は本 map の外であり、完全性を主張しない"
    )


def test_real_e0_historical_raw_succeeds_with_recorded_epoch() -> None:
    campaign = (
        ROOT
        / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
    )
    view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert type(view) is A.HistoricalCampaignView
    assert view.campaign_verifier_epoch.campaign_verifier_epoch == "E0"
    assert view.campaign_verifier_epoch.state == "E0"
    assert view.read_purpose is HISTORICAL


@pytest.mark.parametrize("schema", ["historical", "post-policy"])
def test_lock_read_snapshot_is_rechecked_against_terminal_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, schema: str,
) -> None:
    if schema == "historical":
        campaign = _write_campaign(
            tmp_path / "historical",
            {
                "ccbench_commit": "historical",
                "search_config": {"records": 1, "threads": 1},
                "search_tag": "test", "spec_content": "test", "trial": "test",
            },
            [_record("build_start", {"genome": "g", "src_token": "old"}, ts=1.0)],
        )
        monkeypatch.setattr(
            A, "_is_proven_pre_policy_artifact", lambda **_kwargs: True,
        )
    else:
        campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    original_read_bytes = Path.read_bytes
    replacement_raw = original_read_bytes(lock_path) + b"\n"
    replaced = False

    def read_then_replace(path: Path) -> bytes:
        nonlocal replaced
        raw = original_read_bytes(path)
        if path == lock_path and not replaced:
            lock_path.write_bytes(replacement_raw)
            replaced = True
        return raw

    monkeypatch.setattr(Path, "read_bytes", read_then_replace)

    with pytest.raises(A.ArtifactAdmissionError, match="bytes changed"):
        A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert replaced
    assert original_read_bytes(lock_path) == replacement_raw


def test_overlay_named_campaign_with_changed_hash_is_tampering_not_fallthrough(
    tmp_path: Path,
) -> None:
    source = ROOT / EXPECTED_RECORDS[2][0]
    copied = tmp_path / EXPECTED_RECORDS[2][1]
    (copied / "runs").mkdir(parents=True)
    (copied / "campaign.lock").write_bytes((source / "campaign.lock").read_bytes())
    (copied / "runs/wal.jsonl").write_bytes(
        (source / "runs/wal.jsonl").read_bytes() + b"\n"
    )
    with pytest.raises(A.OverlayMutationError, match="known overlay campaign"):
        A.classify_campaign(copied)


def test_overlay_exact_bytes_remain_denied_after_relocation(tmp_path: Path) -> None:
    source = ROOT / EXPECTED_RECORDS[0][0]
    copied = tmp_path / "renamed-campaign"
    (copied / "runs").mkdir(parents=True)
    (copied / "campaign.lock").write_bytes((source / "campaign.lock").read_bytes())
    (copied / "runs/wal.jsonl").write_bytes(
        (source / "runs/wal.jsonl").read_bytes()
    )

    decision = A.classify_campaign(copied)
    assert decision.classification == "overlay-denied"
    assert decision.overlay_record_key is not None
    with pytest.raises(A.CampaignNotAdmitted, match="legacy-unclassified"):
        A.require_admitted_campaign(copied, purpose=CERTIFIED)


@pytest.mark.parametrize("mutated_file", ["campaign.lock", "runs/wal.jsonl"])
def test_overlay_invariant_tuple_partial_match_is_tampering(
    tmp_path: Path, mutated_file: str,
) -> None:
    source = ROOT / EXPECTED_RECORDS[1][0]
    copied = tmp_path / "relocated-and-mutated"
    (copied / "runs").mkdir(parents=True)
    (copied / "campaign.lock").write_bytes((source / "campaign.lock").read_bytes())
    (copied / "runs/wal.jsonl").write_bytes(
        (source / "runs/wal.jsonl").read_bytes()
    )
    target = copied / mutated_file
    target.write_bytes(target.read_bytes() + b"\n")

    with pytest.raises(A.OverlayMutationError, match="known overlay campaign"):
        A.classify_campaign(copied)


def test_unlisted_post_policy_campaign_requires_exact_attempt_receipt(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    admitted = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert admitted.decision.classification == "admitted-new-schema"
    assert len(admitted.decision.attempt_receipt_sha256s) == 1


def test_valid_v2_campaign_is_admitted(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    decoded = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text()
    )
    assert decoded.is_v2
    assert decoded.authority is not None
    assert len(decoded.authority.contract_loader_blob_sha256s) == 63
    assert A.classify_campaign(campaign).admission_status == "admitted"


def test_certified_acceptance_admits_exact_e1_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert len(_EXPECTED_E1_CLOSURE_PATHS) == 63
    assert _expected_fixture_epoch() == _FIXED_SYNTHETIC_E1_EPOCH
    assert (
        _ordered_fixture_path_list_sha256()
        == _FIXED_ORDERED_CLOSURE_PATHS_SHA256
    )
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")

    view = A.require_admitted_campaign(campaign, purpose=CERTIFIED)

    assert type(view) is A.CertifiedCampaignView
    assert view.campaign_verifier_epoch.state == "E1"
    assert (
        view.campaign_verifier_epoch.campaign_verifier_epoch
        == _FIXED_SYNTHETIC_E1_EPOCH
    )
    assert view.read_purpose is CERTIFIED
    assert not hasattr(view, "verifier_assessment_basis")
    assert view.persisted_certified_commit_count == 1
    assert A.require_certified_campaign_view(view) is view


@pytest.mark.parametrize(
    "mutation",
    (
        "anomalies-positive",
        "receipt-terminal-mismatch",
        "receipt-operation-mismatch",
        "receipt-evidence-mismatch",
        "verify-attempt-mismatch",
    ),
    ids=(
        "anomalies-positive",
        "receipt-terminal-mismatch",
        "receipt-operation-mismatch",
        "receipt-evidence-mismatch",
        "verify-attempt-mismatch",
    ),
)
def test_persisted_commit_gate_rejects(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")

    if mutation == "anomalies-positive":
        _rewrite_wal(campaign, lambda records: next(
            record for record in records if record["stage"] == "verify_done"
        )["payload"].update({"anomalies": 1}))
    elif mutation == "receipt-terminal-mismatch":
        _rewrite_wal(campaign, lambda records: next(
            record for record in records if record["stage"] == "commit"
        )["payload"].update({"fitness_tps": 1.0}))
    elif mutation == "receipt-operation-mismatch":
        _replace_receipted_commit(
            campaign, lambda _records, _payload: None,
            operation_identity="other-attempt",
        )
    elif mutation == "receipt-evidence-mismatch":
        def change_wal_evidence(records, terminal_payload) -> None:
            verify = next(
                record for record in records
                if record["stage"] == "verify_done"
            )
            verify["payload"]["workload"]["tag"] = "s2"
            terminal_payload["verify_configs"] = ["s2"]

        _replace_receipted_commit(
            campaign, change_wal_evidence, receipt_tags=("legacy",),
        )
    else:
        layout = CampaignLayout(root=str(campaign))
        records = [
            json.loads(line)
            for line in Path(layout.wal_file).read_text().splitlines()
        ]
        commit = next(record for record in records if record["stage"] == "commit")
        records.remove(commit)
        start = next(record for record in records if record["stage"] == "build_start")
        attempt_a = start["payload"]["build_attempt_id"]
        receipt_sha = start["payload"]["build_admission_receipt_sha256"]
        records.append(_record(
            "abort", {
                "reason": "build-error",
                "build_attempt_id": attempt_a,
                "build_admission_receipt_sha256": receipt_sha,
            }, ts=4.0, variant=start["variant"], env_tag=start["env_tag"],
        ))
        Path(layout.wal_file).write_text(
            "".join(
                json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records
            ),
            encoding="utf-8",
        )
        attempt_b = "attempt-2"
        retry_start = dict(start["payload"])
        retry_start["build_attempt_id"] = attempt_b
        terminal = {
            "build_attempt_id": attempt_b,
            "build_admission_receipt_sha256": receipt_sha,
            COMMIT_CONTRACT_SHA256_KEY:
                commit["payload"][COMMIT_CONTRACT_SHA256_KEY],
        }
        wal.log(
            layout, start["variant"], "build_start", start["env_tag"],
            retry_start, ts=5.0,
        )
        wal.log(
            layout, start["variant"], "build_done", start["env_tag"],
            {key: terminal[key] for key in (
                "build_attempt_id", "build_admission_receipt_sha256",
            )}, ts=6.0,
        )
        receipt_support.log_receipted_commit(
            layout, start["variant"], start["env_tag"], terminal,
            operation_identity=attempt_b, tags=("legacy",), ts=7.0,
        )

    with pytest.raises(A.ArtifactAdmissionError):
        A.require_admitted_campaign(campaign, purpose=CERTIFIED)


@pytest.mark.parametrize(
    "case",
    (
        "aborted-red-attempt-coexists",
        "no-commit-campaign",
        "nonzero-aborts",
    ),
    ids=(
        "aborted-red-attempt-coexists",
        "no-commit-campaign",
        "nonzero-aborts",
    ),
)
def test_persisted_commit_gate_accepts(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    layout = CampaignLayout(root=str(campaign))
    records = wal.read_records(layout)
    start = next(record for record in records if record.stage == "build_start")
    receipt_sha = start.payload["build_admission_receipt_sha256"]

    if case == "aborted-red-attempt-coexists":
        attempt_id = "red-attempt"
        retry_start = dict(start.payload)
        retry_start["build_attempt_id"] = attempt_id
        terminal = {
            "build_attempt_id": attempt_id,
            "build_admission_receipt_sha256": receipt_sha,
        }
        wal.log(
            layout, start.variant, "build_start", start.env_tag,
            retry_start, ts=5.0,
        )
        wal.log(
            layout, start.variant, "build_done", start.env_tag,
            terminal, ts=6.0,
        )
        wal.log(
            layout, start.variant, "verify_done", start.env_tag, {
                "build_attempt_id": attempt_id,
                "verdict": "non-serializable",
                "certified": False,
                "anomalies": 1,
                "workload": {"tag": "legacy"},
            }, ts=7.0,
        )
        wal.log(
            layout, start.variant, "abort", start.env_tag, {
                **terminal,
                "reason": "verifier-red",
            }, ts=8.0,
        )
    elif case == "no-commit-campaign":
        def replace_commit(records_json) -> None:
            commit = next(
                record for record in records_json
                if record["stage"] == "commit"
            )
            commit["stage"] = "abort"
            commit["payload"] = {
                "reason": "build-error",
                "build_attempt_id": start.payload["build_attempt_id"],
                "build_admission_receipt_sha256": receipt_sha,
            }

        _rewrite_wal(campaign, replace_commit)
    else:
        _rewrite_wal(campaign, lambda records_json: next(
            record for record in records_json
            if record["stage"] == "verify_done"
        )["payload"].update({"aborts": 17}))

    view = A.require_admitted_campaign(campaign, purpose=CERTIFIED)
    assert type(view) is A.CertifiedCampaignView
    expected_count = sum(
        record.stage == "commit" for record in wal.read_records(layout)
    )
    assert view.persisted_certified_commit_count == expected_count
    if case == "no-commit-campaign":
        assert view.persisted_certified_commit_count == 0


@pytest.mark.parametrize(
    "mutation",
    ("second-commit-invalid", "both-commits-valid"),
)
def test_certified_view_checks_every_commit(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    layout = CampaignLayout(root=str(campaign))
    records = wal.read_records(layout)
    start = next(record for record in records if record.stage == "build_start")
    first_commit = next(record for record in records if record.stage == "commit")
    attempt_id = "attempt-2"
    receipt_sha = start.payload["build_admission_receipt_sha256"]
    retry_start = dict(start.payload)
    retry_start["build_attempt_id"] = attempt_id
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt_sha,
    }
    wal.log(
        layout, start.variant, "build_start", start.env_tag,
        retry_start, ts=5.0,
    )
    wal.log(
        layout, start.variant, "build_done", start.env_tag,
        terminal, ts=6.0,
    )
    wal.log(
        layout, start.variant, "verify_done", start.env_tag, {
            "build_attempt_id": attempt_id,
            "verdict": "serializable",
            "certified": True,
            "anomalies": (
                1 if mutation == "second-commit-invalid" else 0
            ),
            "workload": {"tag": "legacy"},
        }, ts=7.0,
    )
    receipt_support.log_receipted_commit(
        layout, start.variant, start.env_tag, {
            **terminal,
            COMMIT_CONTRACT_SHA256_KEY:
                first_commit.payload[COMMIT_CONTRACT_SHA256_KEY],
        }, operation_identity=attempt_id, tags=("legacy",), ts=8.0,
    )

    if mutation == "second-commit-invalid":
        with pytest.raises(A.ArtifactAdmissionError, match="anomalies"):
            A.require_admitted_campaign(campaign, purpose=CERTIFIED)
    else:
        view = A.require_admitted_campaign(campaign, purpose=CERTIFIED)
        assert view.persisted_certified_commit_count == 2


@pytest.mark.parametrize("mutation", ("incomplete-receipt",))
def test_historical_raw_unaffected(
        tmp_path: Path, mutation: str,
) -> None:
    assert mutation == "incomplete-receipt"
    campaign = _new_schema_campaign(tmp_path)
    _rewrite_wal(campaign, lambda records: next(
        record for record in records if record["stage"] == "commit"
    )["payload"]["commit_verification_receipt"].pop("receipt_id"))

    view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert type(view) is A.HistoricalCampaignView


def test_persisted_commit_helper_accepts_immutable_view(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    commit = next(record for record in view.records if record.stage == "commit")

    assert A.require_persisted_certified_commit(
        view.records,
        commit,
        campaign_lock_sha256=view.decision.campaign_lock_sha256,
    ) is commit


def test_persisted_commit_missing_attempt_is_artifact_admission_error(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    records = wal.read_records(layout)
    commit = next(record for record in records if record.stage == "commit")
    commit.payload.pop("build_attempt_id")
    lock_sha256 = hashlib.sha256(
        Path(layout.lock_file).read_bytes()
    ).hexdigest()

    with pytest.raises(
        A.ArtifactAdmissionError,
        match="build_attempt_id must be a non-empty exact str",
    ):
        A.require_persisted_certified_commit(
            records,
            commit,
            campaign_lock_sha256=lock_sha256,
        )


def test_certified_acceptance_rejects_e1_stale_exact_map_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    pipeline_path = repo / "orchestrator/campaign/pipeline.py"
    pipeline_path.write_bytes(pipeline_path.read_bytes() + b"changed in B\n")
    _fixture_git(repo, "add", "--", "orchestrator/campaign/pipeline.py")
    _fixture_git(
        repo,
        "-c", "user.email=epoch-fixture@example.invalid",
        "-c", "user.name=epoch fixture",
        "commit", "-q", "-m", "record closure B",
    )

    view = A.require_admitted_campaign(campaign, purpose=CERTIFIED)

    assert type(view) is A.CertifiedCampaignView
    assert view.read_purpose is CERTIFIED
    assert view.campaign_verifier_epoch.state == "E1"
    assert view.campaign_verifier_epoch.reason_code == "recorded-closure"
    assert (
        view.campaign_verifier_epoch.campaign_verifier_epoch
        == _expected_fixture_epoch()
    )


@pytest.mark.parametrize(
    "verifier_path",
    (
        "orchestrator/verifier/core.py",
        "orchestrator/verifier/dsg.py",
        "orchestrator/verifier/model.py",
        "orchestrator/verifier/parse.py",
        "orchestrator/verifier/__init__.py",
        "orchestrator/verifier/report.py",
        "orchestrator/verifier/commit_receipt.py",
    ),
    ids=lambda path: Path(path).name,
)
def test_certified_acceptance_rejects_each_verifier_drift_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verifier_path: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    lock_path = campaign / "campaign.lock"
    wal_path = campaign / "runs/wal.jsonl"
    before_lock = lock_path.read_bytes()
    before_wal = wal_path.read_bytes()
    historical = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    expected_epoch = (
        historical.campaign_verifier_epoch.campaign_verifier_epoch
    )
    verifier = repo / verifier_path

    try:
        verifier.write_bytes(verifier.read_bytes() + b"uncommitted verifier drift\n")
        with pytest.raises(A.CampaignVerifierEpochRejected) as uncommitted:
            A.require_admitted_campaign(campaign, purpose=CERTIFIED)
        assert uncommitted.value.epoch_state == "E1-stale"
        assert uncommitted.value.reason_code == "current-closure-unavailable"
        assert uncommitted.value.campaign_verifier_epoch == expected_epoch

        _fixture_git(repo, "add", "--", verifier_path)
        _fixture_git(
            repo,
            "-c", "user.email=epoch-fixture@example.invalid",
            "-c", "user.name=epoch fixture",
            "commit", "-q", "-m", "record verifier drift",
        )
        committed = A.require_admitted_campaign(campaign, purpose=CERTIFIED)
        assert type(committed) is A.CertifiedCampaignView
        assert committed.read_purpose is CERTIFIED
        assert committed.campaign_verifier_epoch.state == "E1"
        assert committed.campaign_verifier_epoch.reason_code == "recorded-closure"
        assert (
            committed.campaign_verifier_epoch.campaign_verifier_epoch
            == expected_epoch
        )
    finally:
        assert lock_path.read_bytes() == before_lock
        assert wal_path.read_bytes() == before_wal


def test_certified_acceptance_distinguishes_current_closure_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")

    def unavailable() -> contract_loader_binding.ContractLoaderBinding:
        raise contract_loader_binding.ContractLoaderBindingError("unavailable")

    monkeypatch.setattr(
        contract_loader_binding, "capture_contract_loader_binding", unavailable,
    )
    with pytest.raises(A.CampaignVerifierEpochRejected) as excinfo:
        A.require_admitted_campaign(campaign, purpose=CERTIFIED)
    assert excinfo.value.epoch_state == "E1-stale"
    assert excinfo.value.reason_code == "current-closure-unavailable"


def test_historical_raw_with_dirty_current_closure_preserves_recorded_view_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    live_path = repo / "orchestrator/campaign/artifact_admission.py"
    live_path.write_bytes(live_path.read_bytes() + b"dirty live bytes\n")

    view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)

    assert type(view) is A.HistoricalCampaignView
    assert view.read_purpose is HISTORICAL
    assert view.campaign_verifier_epoch.state == "E1"
    assert view.campaign_verifier_epoch.reason_code == "recorded-closure"
    assert (
        view.campaign_verifier_epoch.campaign_verifier_epoch
        == _expected_fixture_epoch()
    )


def test_historical_view_reports_unknown_current_verifier_conformance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    live_path = repo / "orchestrator/campaign/artifact_admission.py"
    live_path.write_bytes(live_path.read_bytes() + b"dirty live bytes\n")

    view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)

    assert view.current_verifier_conformance == "unknown"


def test_p3_pre_t733_exact_24_is_readable_only_as_recorded_historical_epoch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    lock_raw = _rewrite_as_pre_t733_lock(campaign)

    view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)

    assert type(view) is A.HistoricalCampaignView
    assert type(view.campaign_verifier_epoch) is A.HistoricalCampaignVerifierEpoch
    assert campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_PRE_T733_CLOSURE_PATHS
    )
    assert view.campaign_verifier_epoch.state == "E1"
    assert view.campaign_verifier_epoch.reason_code == "recorded-closure"
    assert (
        view.campaign_verifier_epoch.campaign_verifier_epoch
        == _expected_pre_t733_fixture_epoch()
    )
    assert view.campaign_verifier_epoch.identity_scope == (
        "enforcement source closure (exact 24 path; witness gate、S8C 判定器、"
        "receipt 発行・検証面を含む)"
    )
    assert view.campaign_verifier_epoch.excluded_scope == (
        "verifier package のうち orchestrator/verifier/__main__.py と "
        "orchestrator/verifier/cli.py、および package 外の "
        "orchestrator/verify.py の implementation bytes は束縛しない"
    )
    assert view.campaign_verifier_epoch.identity_scope != (
        A.CAMPAIGN_VERIFIER_EPOCH_SCOPE
    )
    assert view.campaign_verifier_epoch.current_verifier_conformance == "unknown"
    assert view.current_verifier_conformance == "unknown"
    assert (campaign / "campaign.lock").read_bytes() == lock_raw


def test_p4_same_pre_t733_exact_24_bytes_are_rejected_for_certified_use(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    lock_raw = _rewrite_as_pre_t733_lock(campaign)
    historical = A.require_admitted_campaign(campaign, purpose=HISTORICAL)

    with pytest.raises(
        A.ArtifactAdmissionError, match="codec validation failed",
    ):
        A.require_admitted_campaign(campaign, purpose=CERTIFIED)
    with pytest.raises(
        A.ArtifactAdmissionError, match="codec validation failed",
    ):
        A.classify_campaign(campaign)

    assert type(historical) is A.HistoricalCampaignView
    assert (campaign / "campaign.lock").read_bytes() == lock_raw


@pytest.mark.parametrize(
    "mutation",
    ["subset", "superset", "same-count-replacement", "order"],
)
def test_unknown_pre_t733_grammar_is_rejected_for_both_read_purposes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    _rewrite_as_pre_t733_lock(campaign)
    lock_path = campaign / "campaign.lock"
    value = json.loads(lock_path.read_text(encoding="utf-8"))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    if mutation in {"subset", "same-count-replacement"}:
        blobs.pop(campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS[-1])
    if mutation in {"superset", "same-count-replacement"}:
        extra = "orchestrator/campaign/verify_fanout_worker.py"
        assert extra in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        assert extra not in campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
        blobs[extra] = "f" * 64
    if mutation == "order":
        paths = tuple(blobs)
        value["authority"]["contract_loader_blob_sha256s"] = {
            path: blobs[path]
            for path in (paths[1], paths[0], *paths[2:])
        }
        lock_text = json.dumps(
            value, sort_keys=False, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )
    else:
        lock_text = _canonical_json(value)
    lock_path.write_text(lock_text, encoding="utf-8")
    lock_raw = lock_path.read_bytes()

    for purpose in (HISTORICAL, CERTIFIED):
        with pytest.raises(A.ArtifactAdmissionError, match="codec validation failed"):
            A.require_admitted_campaign(campaign, purpose=purpose)

    assert lock_path.read_bytes() == lock_raw


def test_pre_t733_historical_decode_rejects_recorded_commit_blob_mismatch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    _rewrite_as_pre_t733_lock(campaign)
    lock_path = campaign / "campaign.lock"
    value = json.loads(lock_path.read_text(encoding="utf-8"))
    first = campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS[0]
    recorded = value["authority"]["contract_loader_blob_sha256s"][first]
    value["authority"]["contract_loader_blob_sha256s"][first] = (
        ("0" if recorded[0] != "0" else "1") + recorded[1:]
    )
    lock_path.write_text(_canonical_json(value), encoding="utf-8")

    with pytest.raises(
        A.ArtifactAdmissionError, match="contract-loader-blob-mismatch",
    ):
        A.require_admitted_campaign(campaign, purpose=HISTORICAL)


def test_certified_acceptance_rejects_dirty_current_closure_with_exact_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    live_path = repo / "orchestrator/campaign/artifact_admission.py"
    live_path.write_bytes(live_path.read_bytes() + b"dirty live bytes\n")

    with pytest.raises(A.CampaignVerifierEpochRejected) as excinfo:
        A.require_admitted_campaign(campaign, purpose=CERTIFIED)

    assert type(excinfo.value) is A.CampaignVerifierEpochRejected
    assert excinfo.value.epoch_state == "E1-stale"
    assert excinfo.value.reason_code == "current-closure-unavailable"


def test_legacy_recorded_current_closure_mismatch_diagnostic_remains_readable(
) -> None:
    epoch = A.CampaignVerifierEpoch(
        campaign_verifier_epoch=f"E1:{'a' * 64}",
        state="E1-stale",
        reason_code="recorded-current-closure-mismatch",
    )

    assert epoch.state == "E1-stale"
    assert epoch.reason_code == "recorded-current-closure-mismatch"


def test_historical_epoch_display_is_independent_of_live_closure_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    before = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    live_path = repo / "orchestrator/campaign/loop.py"
    live_path.write_bytes(live_path.read_bytes() + b"dirty live bytes\n")

    after = A.require_admitted_campaign(campaign, purpose=HISTORICAL)

    assert type(before) is A.HistoricalCampaignView
    assert type(after) is A.HistoricalCampaignView
    assert (
        before.campaign_verifier_epoch.campaign_verifier_epoch
        == after.campaign_verifier_epoch.campaign_verifier_epoch
        == _expected_fixture_epoch()
    )
    assert before.campaign_verifier_epoch == after.campaign_verifier_epoch
    assert (
        before.verifier_assessment_basis
        == after.verifier_assessment_basis
        == "recorded-at-original-verifier-epoch"
    )
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        before.verifier_assessment_basis = "current-verifier-revalidated"


def _private_zero_commit_certified_view(
    tmp_path: Path, *, count: object = None,
) -> A.CertifiedCampaignView:
    records = ()
    projected_count = (
        sum(record.stage == A.STAGE_COMMIT for record in records)
        if count is None
        else count
    )
    decision = A.CampaignAdmissionDecision(
        classification="test",
        admission_status="admitted",
        verification_status="certified",
        campaign_id="private-zero-commit",
        campaign_path=str(tmp_path),
        campaign_lock_sha256="a" * 64,
        wal_sha256="b" * 64,
        policy_sha256=None,
        attempt_receipt_sha256s=(),
        overlay_ledger_sha256="c" * 64,
        overlay_record_key=None,
        validator_sha256="d" * 64,
    )
    epoch = A.CampaignVerifierEpoch(
        campaign_verifier_epoch="E1:" + "e" * 64,
        state="E1",
        reason_code="recorded-closure",
    )
    return A.CertifiedCampaignView(
        layout=CampaignLayout(root=str(tmp_path)),
        records=records,
        decision=decision,
        campaign_verifier_epoch=epoch,
        persisted_certified_commit_count=projected_count,
        _certification_token=A._CERTIFIED_VIEW_TOKEN,
    )


def test_certified_commit_evidence_rejects_no_commit_campaign(
    tmp_path: Path,
) -> None:
    view = _private_zero_commit_certified_view(tmp_path)

    with pytest.raises(
        A.ArtifactAdmissionError,
        match="at least one persisted COMMIT",
    ):
        A.require_certified_commit_evidence(view)


def test_certified_view_rejects_non_exact_commit_count(tmp_path: Path) -> None:
    class IntSubclass(int):
        pass

    with pytest.raises(TypeError, match="exact int"):
        _private_zero_commit_certified_view(tmp_path, count=IntSubclass(0))


def test_certified_view_rejects_bool_commit_count(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="exact int"):
        _private_zero_commit_certified_view(tmp_path, count=False)


def test_certified_view_rejects_negative_commit_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        _private_zero_commit_certified_view(tmp_path, count=-1)


def test_certified_view_rejects_commit_count_snapshot_mismatch(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="does not match WAL snapshot"):
        _private_zero_commit_certified_view(tmp_path, count=1)


def test_historical_view_cannot_cross_certified_type_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    historical = A.require_admitted_campaign(campaign, purpose=HISTORICAL)

    assert type(historical) is A.HistoricalCampaignView
    assert not isinstance(historical, A.CertifiedCampaignView)
    with pytest.raises(TypeError, match="exact CertifiedCampaignView"):
        A.require_certified_campaign_view(historical)
    with pytest.raises(TypeError, match="gate だけが発行"):
        A.CertifiedCampaignView(
            layout=historical.layout,
            records=historical.records,
            decision=historical.decision,
            campaign_verifier_epoch=historical.campaign_verifier_epoch,
            persisted_certified_commit_count=sum(
                record.stage == A.STAGE_COMMIT
                for record in historical.records
            ),
            _certification_token=object(),
        )


def test_lock_only_epoch_api_does_not_read_wal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    (campaign / "runs/wal.jsonl").write_bytes(b"not-json\n")

    epoch = A.require_campaign_verifier_epoch(
        campaign, purpose=CERTIFIED,
    )

    assert epoch.state == "E1"
    assert epoch.campaign_verifier_epoch == _expected_fixture_epoch()


def test_noncertifying_lock_is_rejected_by_lock_only_certified_gate_before_wal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = {
        "spec_content": "A-1 fixture",
        "ccbench_commit": "a" * 40,
        "search_tag": "paired",
        "search_config": {
            "build_admission": {"schema": "fixture"},
            "schema": "paper-story-a1-paired-campaign/v1",
            "study_id": "paper-story-a1-20260826-sized-v1",
            "formal": False,
            "promotion_prohibited": True,
            "pairing_design": "arm-grouped-positional-v1",
            "workload": {"name": "write-heavy"},
        },
        "trial": "paper-story-a1-20260826-sized-v1",
    }
    common = {
        "mode": "registered-formal-non-certifying",
        "certifying": False,
        "study_id": "paper-story-a1-20260826-sized-v1",
        "policy_sha256": "1" * 64,
        "preregistration_sha256": "2" * 64,
        "source_commit": "3" * 40,
        "source_binding_sha256": "4" * 64,
        "environment_contract_sha256": "5" * 64,
        "intent_sha256": "6" * 64,
        "campaign_ids": ["campaign-a", "campaign-b", "campaign-c"],
    }
    campaign = tmp_path / "campaign-a"
    (campaign / "runs").mkdir(parents=True)
    (campaign / "campaign.lock").write_text(
        campaign_lock.encode_non_certifying_campaign_lock(
            _canonical_json(identity),
            common_record=common,
            workload_binding={
                "workload": "write-heavy",
                "campaign_id": "campaign-a",
                "ordinal": 0,
            },
        ),
        encoding="utf-8",
    )
    (campaign / "runs/wal.jsonl").write_bytes(b"must-not-be-read")
    original = Path.read_bytes

    def refuse_wal_read(path: Path) -> bytes:
        if path == campaign / "runs/wal.jsonl":
            pytest.fail("lock-only certified gate read the WAL")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", refuse_wal_read)
    with pytest.raises(A.ArtifactAdmissionError):
        A.require_campaign_verifier_epoch(campaign, purpose=CERTIFIED)

    layout = CampaignLayout(root=str(campaign))
    monkeypatch.setattr(
        wal,
        "read_records",
        lambda _layout: pytest.fail("generic replay read non-certifying WAL"),
    )
    with pytest.raises(wal.AttemptTopologyError):
        wal.replay(layout)


def test_read_purpose_is_mandatory_and_exact() -> None:
    campaign = (
        ROOT
        / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
    )
    with pytest.raises(TypeError):
        A.require_admitted_campaign(campaign)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="exact CampaignReadPurpose"):
        A.require_admitted_campaign(
            campaign, purpose="HISTORICAL_RAW",  # type: ignore[arg-type]
        )


def test_v2_committed_admission_ignores_dirty_live_loader_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "loader-repo"
    repo.mkdir()
    _fixture_git(repo, "init", "-q")
    for index, relative in enumerate(
        campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS, start=1,
    ):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"admission loader fixture {index}".encode("ascii"))
    _fixture_git(
        repo, "add", "--", *campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
    )
    _fixture_git(
        repo,
        "-c", "user.email=admission-fixture@example.invalid",
        "-c", "user.name=admission fixture",
        "commit", "-q", "-m", "commit loader fixture",
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    decoded = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text(encoding="utf-8")
    )
    assert decoded.authority is not None

    dirty_path = "orchestrator/campaign/loop.py"
    assert dirty_path in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    dirty_file = repo / dirty_path
    recorded_blob = _fixture_git(
        repo, "cat-file", "blob",
        f"{decoded.authority.contract_loader_commit}:{dirty_path}",
    )
    recorded_digest = hashlib.sha256(recorded_blob).hexdigest()
    assert (
        decoded.authority.contract_loader_blob_sha256s[dirty_path]
        == recorded_digest
    )
    dirty_file.write_bytes(dirty_file.read_bytes() + b"\nuncommitted edit\n")
    assert hashlib.sha256(dirty_file.read_bytes()).hexdigest() != recorded_digest

    assert A.classify_campaign(campaign).admission_status == "admitted"


def test_v2_admission_rejects_commit_contract_hash_missing(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)

    def remove_hash(records: list[dict]) -> None:
        commit = next(record for record in records if record["stage"] == "commit")
        commit["payload"].pop(COMMIT_CONTRACT_SHA256_KEY)

    _rewrite_wal(campaign, remove_hash)
    with pytest.raises(A.ArtifactAdmissionError, match="contract_sha256.*exact"):
        A.classify_campaign(campaign)


def test_v2_admission_rejects_commit_contract_hash_mismatch(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)

    def replace_hash(records: list[dict]) -> None:
        commit = next(record for record in records if record["stage"] == "commit")
        actual = commit["payload"][COMMIT_CONTRACT_SHA256_KEY]
        commit["payload"][COMMIT_CONTRACT_SHA256_KEY] = (
            "0" * 64 if actual != "0" * 64 else "1" * 64
        )

    _rewrite_wal(campaign, replace_hash)
    with pytest.raises(A.ArtifactAdmissionError, match="campaign.lock と不一致"):
        A.classify_campaign(campaign)


def test_v2_admission_rejects_commit_environment_tag_mismatch(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)

    def replace_env_tag(records: list[dict]) -> None:
        commit = next(record for record in records if record["stage"] == "commit")
        commit["env_tag"] = f"{commit['env_tag']}-foreign"

    _rewrite_wal(campaign, replace_env_tag)
    with pytest.raises(A.ArtifactAdmissionError, match="env_tag.*不一致"):
        A.classify_campaign(campaign)


def test_v2_loader_mismatch_rejection_preserves_lock_wal_and_report_bytes(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    assert decoded.authority is not None
    digests = dict(decoded.authority.contract_loader_blob_sha256s)
    first_path = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS[0]
    digests[first_path] = "0" * 64 if digests[first_path] != "0" * 64 else "1" * 64
    _rewrite_v2_authority(
        lock_path, contract_loader_blob_sha256s=digests,
    )
    wal_path = campaign / "runs/wal.jsonl"
    report_path = campaign / "reports" / "sentinel.json"
    report_path.parent.mkdir()
    report_path.write_bytes(b'{"sentinel":"unchanged"}\n')
    before = {
        lock_path: lock_path.read_bytes(),
        wal_path: wal_path.read_bytes(),
        report_path: report_path.read_bytes(),
    }

    with pytest.raises(A.ArtifactAdmissionError, match="contract-loader-blob-mismatch"):
        A.classify_campaign(campaign)

    assert {path: path.read_bytes() for path in before} == before


def test_v2_outer_envelope_stripped_to_v1_post_policy_is_rejected(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    lock_path.write_text(decoded.identity_preimage, encoding="utf-8")

    with pytest.raises(A.ArtifactAdmissionError, match="post-policy downgrade"):
        A.classify_campaign(campaign)


def test_guided_equivalent_v1_non_certified_lane_is_admitted(
    tmp_path: Path,
) -> None:
    """Guided 相当の非 certified lane を過剰拒否せず受理する正例。

    封筒と COMMIT hash を同時に削った artifact はこの経路では区別できない
    （既知の限界。脅威モデルは bytes 書き換えを含まない）。
    """
    campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    lock_path.write_text(decoded.identity_preimage, encoding="utf-8")
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    for record in records:
        if record["stage"] == "commit":
            record["payload"].pop(COMMIT_CONTRACT_SHA256_KEY)
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    decision = A.classify_campaign(campaign)
    assert decision.classification == "admitted-new-schema"
    assert decision.admission_status == "admitted"


def test_v2_outer_and_build_admission_stripped_cannot_claim_history(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    identity = json.loads(decoded.identity_preimage)
    identity["search_config"].pop("build_admission")
    lock_path.write_text(_canonical_json(identity), encoding="utf-8")

    with pytest.raises(A.ArtifactAdmissionError, match="historicity"):
        A.classify_campaign(campaign)


def test_v2_loader_validation_rejects_git_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    monkeypatch.setattr(
        contract_loader_binding,
        "_GIT_EXECUTABLE",
        tmp_path / "missing-fixed-git",
    )

    with pytest.raises(A.ArtifactAdmissionError, match="git executable"):
        A.classify_campaign(campaign)


def test_v2_loader_validation_rejects_valid_second_git_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path / "campaign")
    second = tmp_path / "second-repository"
    second.mkdir()
    _fixture_git(second, "init", "-q")
    marker = second / "marker"
    marker.write_text("valid second repository", encoding="utf-8")
    _fixture_git(second, "add", "marker")
    _fixture_git(
        second,
        "-c", "user.email=artifact-fixture@example.invalid",
        "-c", "user.name=artifact fixture",
        "commit", "-q", "-m", "valid second repository",
    )
    real_run_git = contract_loader_binding._run_git
    calls: list[tuple[str, ...]] = []

    def redirected_git_view(root: Path, *args: str, **kwargs: object) -> bytes:
        calls.append(args)
        if args == ("rev-parse", "--show-toplevel"):
            return f"{second.resolve()}\n".encode()
        return real_run_git(root, *args, **kwargs)

    monkeypatch.setattr(
        contract_loader_binding, "_run_git", redirected_git_view,
    )

    with pytest.raises(A.ArtifactAdmissionError, match="Git top-level"):
        A.classify_campaign(campaign)
    assert calls == [("rev-parse", "--show-toplevel")]


def test_v2_loader_validation_rejects_ambient_git_repository_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "foreign.git"))

    with pytest.raises(A.ArtifactAdmissionError, match="ambient Git"):
        A.classify_campaign(campaign)


def test_v2_loader_validation_rejects_git_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path)

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=10)

    monkeypatch.setattr(contract_loader_binding.subprocess, "run", timeout)
    with pytest.raises(A.ArtifactAdmissionError, match="git-timeout"):
        A.classify_campaign(campaign)


def test_v2_loader_validation_rejects_missing_commit(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    _rewrite_v2_authority(
        campaign / "campaign.lock", contract_loader_commit="f" * 40,
    )

    with pytest.raises(A.ArtifactAdmissionError, match="git command"):
        A.classify_campaign(campaign)


def test_v2_loader_validation_rejects_missing_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    real_run_git = contract_loader_binding._run_git
    missing = "orchestrator/campaign/env_contract_activation.py"
    assert missing in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    decoded = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text()
    )
    assert decoded.authority is not None
    commit = decoded.authority.contract_loader_commit
    calls: list[tuple[str, ...]] = []

    def missing_blob(root: Path, *args: str, **kwargs: object) -> bytes:
        calls.append(args)
        output = real_run_git(root, *args, **kwargs)
        if args[:4] == ("ls-tree", "-r", "-z", commit):
            raw_missing = os.fsencode(missing)
            entries = output.split(b"\0")
            output = b"\0".join(
                entry for entry in entries
                if entry.partition(b"\t")[2] != raw_missing
            )
        return output

    monkeypatch.setattr(contract_loader_binding, "_run_git", missing_blob)

    with pytest.raises(A.ArtifactAdmissionError, match="git command") as caught:
        A.classify_campaign(campaign)
    assert missing in str(caught.value)
    assert [
        args for args in calls
        if args[:4] == ("ls-tree", "-r", "-z", commit)
    ] == [(
        "ls-tree", "-r", "-z", commit, "--",
        *(f":(literal){relative}"
          for relative in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS),
    )]


def test_contract_loader_rejects_leaf_symlink(tmp_path: Path) -> None:
    root = tmp_path / "root"
    relative = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS[0]
    leaf = root / relative
    leaf.parent.mkdir(parents=True)
    target = root / "loader-target.py"
    target.write_bytes(b"loader")
    leaf.symlink_to(target)

    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
        match="symlink/non-regular",
    ):
        contract_loader_binding._read_regular_file_no_follow(root, relative)


def test_contract_loader_rejects_parent_directory_symlink(tmp_path: Path) -> None:
    root = tmp_path / "root"
    real_parent = root / "real-campaign"
    real_parent.mkdir(parents=True)
    (real_parent / "env_contract.py").write_bytes(b"loader")
    orchestrator_dir = root / "orchestrator"
    orchestrator_dir.mkdir()
    (orchestrator_dir / "campaign").symlink_to(real_parent, target_is_directory=True)
    relative = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS[0]

    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
        match="open-error",
    ):
        contract_loader_binding._read_regular_file_no_follow(root, relative)


def test_contract_loader_rejects_file_swap_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    relative = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS[0]
    loader = root / relative
    loader.parent.mkdir(parents=True)
    loader.write_bytes(b"before")
    real_read = contract_loader_binding.os.read
    swapped = False

    def read_then_swap(fd: int, size: int) -> bytes:
        nonlocal swapped
        chunk = real_read(fd, size)
        if chunk and not swapped:
            swapped = True
            loader.write_bytes(b"after-different-size")
        return chunk

    monkeypatch.setattr(contract_loader_binding.os, "read", read_then_swap)
    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
        match="path-race",
    ):
        contract_loader_binding._read_regular_file_no_follow(root, relative)


def test_contract_loader_path_closure_uses_codec_single_source() -> None:
    assert (
        contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS
        is campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )
    assert set(contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS) == set(
        campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )


def test_v2_loader_validation_rejects_broken_symlink_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path / "campaign")
    broken = tmp_path / "loader-repo-link"
    broken.symlink_to(tmp_path / "does-not-exist", target_is_directory=True)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", broken)

    with pytest.raises(A.ArtifactAdmissionError, match="root"):
        A.classify_campaign(campaign)


def test_v2_loader_validation_rejects_root_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign = _new_schema_campaign(tmp_path / "campaign")
    outside = tmp_path.parent
    assert outside.resolve() != ROOT.resolve()
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", outside)

    with pytest.raises(A.ArtifactAdmissionError, match="git command"):
        A.classify_campaign(campaign)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"activation_serial": 999999}, id="missing-serial"),
        pytest.param(
            {"activation_state_sha256": "f" * 64}, id="missing-state",
        ),
    ],
)
def test_v2_activation_tuple_must_name_real_active_record(
    tmp_path: Path, changes: dict[str, object],
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    _rewrite_v2_authority(campaign / "campaign.lock", **changes)

    with pytest.raises(A.ArtifactAdmissionError, match="activation tuple"):
        A.classify_campaign(campaign)


def test_v2_resume_authenticates_activation_tuple_before_wal_repair(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    decoded = campaign_lock.decode_campaign_lock(lock_path.read_text())
    identity = decoded.identity
    authorization = env_contract.authorize("linux-baremetal")
    cfg = CampaignConfig(
        spec_slug="campaign",
        search_tag=identity["search_tag"],
        spec_content=identity["spec_content"],
        ccbench_commit=identity["ccbench_commit"],
        search_config=dict(identity["search_config"]),
        trial=identity["trial"],
        bound_environment_contract=authorization.contract,
    )
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    _rewrite_v2_authority(lock_path, activation_state_sha256="f" * 64)
    wal_path = campaign / "runs/wal.jsonl"
    with wal_path.open("ab") as stream:
        stream.write(b'{"torn":')
    before = wal_path.read_bytes()

    with pytest.raises(ident.IdentityMismatch) as rejected:
        ident.ensure_resumable_wal(
            cfg,
            CampaignLayout(root=str(campaign)),
            admission_policy=context.policy,
        )

    assert rejected.value.reason == "activation-tuple-invalid"
    assert wal_path.read_bytes() == before


def test_post_policy_trigger_proposal_requires_marker_and_complete_binding(tmp_path: Path) -> None:
    canonical = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "canonical"),
        marker=True, proposal=True, binding=True,
    )
    assert A.classify_campaign(canonical).classification == "admitted-new-schema"

    marker_without_binding = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "missing-binding"),
        marker=True, proposal=True, binding=False,
    )
    with pytest.raises(A.ArtifactAdmissionError, match="一対一"):
        A.classify_campaign(marker_without_binding)

    proposal_without_marker = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "missing-marker"),
        marker=False, proposal=True, binding=False,
    )
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(proposal_without_marker)


def test_post_policy_trigger_machine_sweep_does_not_require_binding(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=False, proposal=False, binding=False,
    )
    decision = A.classify_campaign(campaign)
    assert decision.classification == "admitted-new-schema"
    assert decision.admission_status == "admitted"


def test_nontrigger_post_policy_v2_allows_relocated_directory(
    tmp_path: Path,
) -> None:
    """全 v2 照合は親の独自追加で正当な relocation consumer を拒否したため撤回した。"""
    campaign = _new_schema_campaign(tmp_path)
    assert A.classify_campaign(campaign).classification == "admitted-new-schema"
    arbitrary_layout = campaign.parent / "formal-shaped"
    campaign.rename(arbitrary_layout)

    decision = A.classify_campaign(arbitrary_layout)
    assert decision.classification == "admitted-new-schema"
    assert decision.admission_status == "admitted"


def test_post_policy_campaign_directory_id_must_match_lock_preimage(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    renamed = campaign.parent / "campaign-test-deadbeef"
    campaign.rename(renamed)
    with pytest.raises(A.ArtifactAdmissionError, match="directory ID"):
        A.classify_campaign(renamed)


def test_post_policy_trigger_proposal_requires_canonical_lock_bytes(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    lock_path = campaign / "campaign.lock"
    lock_path.write_text(json.dumps(json.loads(lock_path.read_text())), encoding="utf-8")

    with pytest.raises(A.ArtifactAdmissionError, match="canonical"):
        A.classify_campaign(campaign)


def test_proposal_cannot_be_rewritten_as_machine_sweep_with_coder_receipt(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path, coder_authored=True),
        marker=True, proposal=True, binding=True,
    )
    lock_path = campaign / "campaign.lock"

    def rewrite_as_machine(lock: dict) -> None:
        search = lock["search_config"]
        search.pop(wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY)
        search.pop("reflux")
        search.update({
            "generator": "reason-subset-v1",
            "space": "reason-subsets(effective)+identall+stock",
        })
    _rewrite_v2_identity(lock_path, rewrite_as_machine)

    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    records = [
        record for record in records
        if record["stage"] != trigger_gate_binding.WAL_RECORD_STAGE
    ]
    start = next(record for record in records if record["stage"] == "build_start")
    assert start["payload"]["build_admission"]["class"] == "coder-authored"
    start["payload"].pop(wal.TRIGGER_BINDING_COMMITMENT_KEY)
    wal_path.write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    provenance_path = campaign / "reports/p3_s8a_trigger_loop_provenance.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["entries"]["1"].pop(wal.TRIGGER_BINDING_COMMITMENT_KEY)
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    campaign = _rename_for_lock(campaign)

    with pytest.raises(A.ArtifactAdmissionError, match="coder-authored receipt"):
        A.classify_campaign(campaign)


def test_post_policy_trigger_binding_tamper_is_rejected_by_shared_validator(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    raw = next(record for record in records
               if record["stage"] == trigger_gate_binding.WAL_RECORD_STAGE)
    raw["payload"][wal.TRIGGER_BINDING_PAYLOAD_KEY]["mask"] = 10
    wal_path.write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    with pytest.raises(A.ArtifactAdmissionError, match="binding record"):
        A.classify_campaign(campaign)


def test_post_policy_trigger_provenance_must_copy_wal_commitment(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    path = campaign / "reports/p3_s8a_trigger_loop_provenance.json"
    provenance = json.loads(path.read_text())
    provenance["entries"]["1"][wal.TRIGGER_BINDING_COMMITMENT_KEY] = "0" * 64
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(A.ArtifactAdmissionError, match="WAL build_start と不一致"):
        A.classify_campaign(campaign)


def test_trigger_provenance_requires_each_abort_retry_attempt(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    raw = next(record for record in records
               if record["stage"] == trigger_gate_binding.WAL_RECORD_STAGE)
    start = next(record for record in records if record["stage"] == "build_start")
    receipt_sha = start["payload"]["build_admission_receipt_sha256"]
    first_attempt = start["payload"]["build_attempt_id"]
    second_attempt = "attempt-2"
    raw_retry = json.loads(json.dumps(raw))
    raw_retry["ts"] = 3.0
    raw_retry["payload"]["build_attempt_id"] = second_attempt
    start_retry = json.loads(json.dumps(start))
    start_retry["ts"] = 4.0
    start_retry["payload"]["build_attempt_id"] = second_attempt
    abort_first = _record(
        "abort", {
            "build_attempt_id": first_attempt,
            "build_admission_receipt_sha256": receipt_sha,
            "reason": "build-error",
        }, ts=2.0, variant=start["variant"],
    )
    abort_retry = _record(
        "abort", {
            "build_attempt_id": second_attempt,
            "build_admission_receipt_sha256": receipt_sha,
            "reason": "build-error",
        }, ts=5.0, variant=start["variant"],
    )
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in [raw, start, abort_first, raw_retry, start_retry, abort_retry]
        ),
        encoding="utf-8",
    )

    path = campaign / "reports/p3_s8a_trigger_loop_provenance.json"
    provenance = json.loads(path.read_text())
    provenance["entries"]["2"] = {
        "build_attempt_id": second_attempt,
        "variant": start["variant"],
        wal.TRIGGER_BINDING_COMMITMENT_KEY:
            start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
    }
    path.write_text(json.dumps(provenance), encoding="utf-8")
    assert A.classify_campaign(campaign).classification == "admitted-new-schema"

    del provenance["entries"]["2"]
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(A.ArtifactAdmissionError, match="attempt/commitment"):
        A.classify_campaign(campaign)


def test_trigger_binding_marker_on_nontrigger_axis_is_mixed_and_rejected(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=False, binding=False,
        axis="silo-writeset-sort",
    )
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(campaign)


def test_post_policy_trigger_unknown_marker_or_unclassified_shape_is_rejected(
    tmp_path: Path,
) -> None:
    unknown_marker = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "unknown-marker"),
        marker=True, proposal=True, binding=False,
    )
    lock_path = unknown_marker / "campaign.lock"
    _rewrite_v2_identity(
        lock_path,
        lambda lock: lock["search_config"].__setitem__(
            wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY, "unknown/v9",
        ),
    )
    unknown_marker = _rename_for_lock(unknown_marker)
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(unknown_marker)

    unknown_shape = _new_schema_campaign(tmp_path / "unknown-shape")
    lock_path = unknown_shape / "campaign.lock"
    _rewrite_v2_identity(
        lock_path,
        lambda lock: lock["search_config"].__setitem__("axis", wal.TRIGGER_AXIS),
    )
    unknown_shape = _rename_for_lock(unknown_shape)
    with pytest.raises(A.ArtifactAdmissionError, match="classification is unknown|分類が unknown"):
        A.classify_campaign(unknown_shape)


def test_post_policy_variant_is_rederived_from_genome_and_source(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    for record in records:
        record["variant"] = "ffffffffffff"
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    with pytest.raises(A.ArtifactAdmissionError, match="variant differs"):
        A.require_admitted_campaign(campaign, purpose=HISTORICAL)


def test_post_policy_variant_without_build_start_remains_admissible(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    records.insert(2, {
        "variant": "ffffffffffff",
        "stage": "verify_done",
        "env_tag": "test",
        "ts": 2.5,
        "payload": {"certified": True},
    })
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    admitted = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert admitted.decision.classification == "admitted-new-schema"
    assert any(
        record.variant == "ffffffffffff" and record.stage == "verify_done"
        for record in admitted.records
    )


def test_admitted_view_is_deeply_immutable(tmp_path: Path) -> None:
    admitted = A.require_admitted_campaign(
        _new_schema_campaign(tmp_path), purpose=HISTORICAL,
    )
    start = admitted.records[0]
    with pytest.raises(FrozenInstanceError):
        start.stage = "commit"
    with pytest.raises(TypeError):
        start.payload["genome"] = "silo|BACK_OFF=1"
    with pytest.raises(TypeError):
        start.payload["build_admission"]["source"]["src_token"] = "mutated"


def test_unlisted_post_policy_receiptless_terminal_is_denied(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path, omit_receipt=True)
    with pytest.raises(A.ArtifactAdmissionError, match="attempt admission is invalid"):
        A.require_admitted_campaign(campaign, purpose=HISTORICAL)


def test_unlisted_receiptless_campaign_cannot_self_declare_history(tmp_path: Path) -> None:
    campaign = _write_campaign(
        tmp_path / "historical",
        {
            "ccbench_commit": "historical",
            "search_config": {"records": 1, "threads": 1},
            "search_tag": "test", "spec_content": "test", "trial": "test",
        },
        [_record("build_start", {"genome": "g", "src_token": "old"}, ts=1.0)],
    )
    with pytest.raises(A.ArtifactAdmissionError, match="historicity is not proven"):
        A.require_admitted_campaign(campaign, purpose=HISTORICAL)


def test_exact_pre_policy_git_snapshot_artifact_remains_readable() -> None:
    path, lock_sha, wal_sha = KNOWN_HISTORICAL
    campaign = ROOT / path
    assert hashlib.sha256((campaign / "campaign.lock").read_bytes()).hexdigest() == lock_sha
    assert hashlib.sha256((campaign / "runs/wal.jsonl").read_bytes()).hexdigest() == wal_sha
    admitted = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
    assert admitted.decision.classification == "historical-pre-admission-schema"
    assert admitted.decision.admission_status == "historical-not-reclassified"


def _rewrite_as_t733_exact62_lock(campaign: Path) -> bytes:
    lock_path = campaign / "campaign.lock"
    value = json.loads(lock_path.read_text(encoding="utf-8"))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    value["authority"]["contract_loader_blob_sha256s"] = {
        path: blobs[path] for path in _EXPECTED_T733_EXACT62_CLOSURE_PATHS
    }
    raw = _canonical_json(value).encode("utf-8")
    lock_path.write_bytes(raw)
    return raw


def test_t733_exact62_is_readable_only_as_recorded_historical_epoch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    lock_raw = _rewrite_as_t733_exact62_lock(campaign)
    wal_raw = (campaign / "runs/wal.jsonl").read_bytes()
    assert campaign_lock.T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_T733_EXACT62_CLOSURE_PATHS
    )
    assert hashlib.sha256(b"".join(
        path.encode("utf-8") + b"\0"
        for path in campaign_lock.T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS
    )).hexdigest() == _FIXED_T733_EXACT62_PATH_SHA256
    for dirty in (False, True):
        if dirty:
            live = repo / "orchestrator/campaign/artifact_admission.py"
            live.write_bytes(live.read_bytes() + b"uncommitted live closure drift\n")
        view = A.require_admitted_campaign(campaign, purpose=HISTORICAL)
        epoch = A.require_campaign_verifier_epoch(campaign, purpose=HISTORICAL)
        assert type(view) is A.HistoricalCampaignView
        assert view.read_purpose is HISTORICAL
        assert view.campaign_verifier_epoch == epoch
        assert type(epoch) is A.HistoricalCampaignVerifierEpoch
        assert epoch.state == "E1"
        assert epoch.reason_code == "recorded-closure"
        assert epoch.campaign_verifier_epoch == _FIXED_T733_EXACT62_EPOCH
        assert epoch.identity_scope == (
            "enforcement source closure (curated exact 62 path; 2026-09-01 の静的 import "
            "発見集合 131 module のうち、既存 24、明示 import 先 36、実行時 package 初期化 "
            "2 を収載; source-import 推移閉包ではない)"
        )
        assert epoch.excluded_scope == (
            "同発見集合の未収載 69 module、orchestrator/verifier/__main__.py、"
            "orchestrator/verifier/cli.py、package 外の orchestrator/verify.py、および "
            "data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 "
            "import を含む非 import 委譲は本 map の外であり、完全性を主張しない"
        )
        assert epoch.current_verifier_conformance == "unknown"
        assert view.current_verifier_conformance == "unknown"
        assert (campaign / "campaign.lock").read_bytes() == lock_raw
        assert (campaign / "runs/wal.jsonl").read_bytes() == wal_raw


def test_t733_exact62_is_rejected_for_certified_use(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    lock_raw = _rewrite_as_t733_exact62_lock(campaign)
    for api in (A.require_admitted_campaign, A.require_campaign_verifier_epoch):
        with pytest.raises(A.ArtifactAdmissionError, match="codec validation failed"):
            api(campaign, purpose=CERTIFIED)
    with pytest.raises(A.ArtifactAdmissionError, match="codec validation failed"):
        A.classify_campaign(campaign)
    assert (campaign / "campaign.lock").read_bytes() == lock_raw


@pytest.mark.parametrize(
    "mutation", ["subset", "superset", "same-count-replacement", "order"],
)
def test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    _rewrite_as_t733_exact62_lock(campaign)
    lock_path = campaign / "campaign.lock"
    value = json.loads(lock_path.read_text(encoding="utf-8"))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    if mutation in {"subset", "same-count-replacement"}:
        blobs.pop(_EXPECTED_T733_EXACT62_CLOSURE_PATHS[-1])
    if mutation in {"superset", "same-count-replacement"}:
        extra = "orchestrator/campaign/unknown_t2483.py"
        assert extra not in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        blobs[extra] = "f" * 64
    if mutation == "order":
        paths = tuple(blobs)
        value["authority"]["contract_loader_blob_sha256s"] = {
            p: blobs[p] for p in (paths[1], paths[0], *paths[2:])
        }
        text = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    else:
        text = _canonical_json(value)
    lock_path.write_text(text, encoding="utf-8")
    for purpose in (HISTORICAL, CERTIFIED):
        for api in (A.require_admitted_campaign, A.require_campaign_verifier_epoch):
            with pytest.raises(A.ArtifactAdmissionError, match="codec validation failed"):
                api(campaign, purpose=purpose)
    assert lock_path.read_bytes() == text.encode("utf-8")


@pytest.mark.parametrize("relative", _EXPECTED_T733_EXACT62_CLOSURE_PATHS)
def test_t733_exact62_rejects_each_recorded_commit_blob_mismatch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str,
) -> None:
    repo = _committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    campaign = _new_schema_campaign(tmp_path / "campaign")
    _rewrite_as_t733_exact62_lock(campaign)
    lock_path = campaign / "campaign.lock"
    value = json.loads(lock_path.read_text(encoding="utf-8"))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    recorded = blobs[relative]
    blobs[relative] = ("0" if recorded[0] != "0" else "1") + recorded[1:]
    lock_path.write_text(_canonical_json(value), encoding="utf-8")
    for api in (A.require_admitted_campaign, A.require_campaign_verifier_epoch):
        with pytest.raises(
            A.ArtifactAdmissionError, match="contract-loader-blob-mismatch",
        ) as rejected:
            api(campaign, purpose=HISTORICAL)
        assert relative in str(rejected.value)


def test_t733_exact62_epoch_requires_matching_scope_and_paths() -> None:
    from dataclasses import replace
    from types import MappingProxyType

    epoch = A.HistoricalCampaignVerifierEpoch(
        campaign_verifier_epoch=_FIXED_T733_EXACT62_EPOCH,
        state="E1", reason_code="recorded-closure",
        identity_scope=A.T733_EXACT62_CAMPAIGN_VERIFIER_EPOCH_SCOPE,
        excluded_scope=A.T733_EXACT62_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,
    )
    blobs62 = MappingProxyType({
        p: hashlib.sha256(f"epoch closure fixture {i}\n".encode("ascii")).hexdigest()
        for i, p in enumerate(_EXPECTED_T733_EXACT62_CLOSURE_PATHS, start=1)
    })
    A._RecordedCampaignVerifierEpoch(diagnostic=epoch, blob_sha256s=blobs62)
    for changes in (
        {"identity_scope": A.PRE_T733_CAMPAIGN_VERIFIER_EPOCH_SCOPE},
        {"excluded_scope": A.PRE_T733_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE},
        {"identity_scope": "unknown scope"},
        {"excluded_scope": "unknown exclusions"},
    ):
        with pytest.raises(TypeError, match="diagnostic"):
            replace(epoch, **changes)
    epoch24 = replace(
        epoch, identity_scope=A.PRE_T733_CAMPAIGN_VERIFIER_EPOCH_SCOPE,
        excluded_scope=A.PRE_T733_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,
    )
    blobs24 = MappingProxyType({p: blobs62[p] for p in _EXPECTED_PRE_T733_CLOSURE_PATHS})
    paths = _EXPECTED_T733_EXACT62_CLOSURE_PATHS
    reordered = MappingProxyType({
        p: blobs62[p] for p in (paths[1], paths[0], *paths[2:])
    })
    for diagnostic, blobs in ((epoch24, blobs62), (epoch, blobs24), (epoch, reordered)):
        with pytest.raises(TypeError, match="exact path 順序"):
            A._RecordedCampaignVerifierEpoch(diagnostic=diagnostic, blob_sha256s=blobs)


def _run() -> int:
    """pytest fixtures/parametrize を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
