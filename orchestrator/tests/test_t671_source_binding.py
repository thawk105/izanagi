# -*- coding: utf-8 -*-
"""[T-671] contract loader source binding の決定的な test-first 回帰。"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission, env_contract, ident
from orchestrator.campaign.build_admission import GeneratorId, build_run_context
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import CampaignConfig


_LOADER_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
)


def _git(repo: Path, *args: str) -> bytes:
    """Run Git fail-closed; an unavailable/broken Git is a test failure, not a skip."""
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("git executable is required for the source-binding fixture")
    try:
        completed = subprocess.run(
            [executable, "-C", str(repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.fail(f"git fixture command could not run: {exc}")
    if completed.returncode != 0:
        pytest.fail(
            "git fixture command failed: "
            f"args={args!r} rc={completed.returncode} "
            f"stderr={completed.stderr.decode('utf-8', errors='replace')!r}"
        )
    return completed.stdout


def _committed_loader_repo(
    tmp_path: Path, *, copy_current_loaders: bool = False,
) -> tuple[Path, str, dict[str, str]]:
    repo = tmp_path / "loader-repo"
    repo.mkdir()
    _git(repo, "init", "-q")

    for index, relative in enumerate(_LOADER_PATHS, start=1):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if copy_current_loaders:
            current = Path(__file__).resolve().parents[2] / relative
            path.write_bytes(current.read_bytes())
        else:
            path.write_bytes(f"loader fixture {index}".encode("ascii"))

    _git(repo, "add", "--", *_LOADER_PATHS)
    _git(
        repo,
        "-c", "user.email=t671-fixture@example.invalid",
        "-c", "user.name=T671 fixture",
        "commit", "-q", "-m", "commit loader fixture",
    )
    commit = _git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    blob_sha256s = {
        relative: hashlib.sha256(
            _git(repo, "cat-file", "blob", f"{commit}:{relative}")
        ).hexdigest()
        for relative in _LOADER_PATHS
    }
    return repo, commit, blob_sha256s


def _bound_config() -> tuple[CampaignConfig, object, object]:
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    authorization = env_contract.authorize("linux-baremetal")
    cfg = CampaignConfig(
        spec_slug="t671-source-binding",
        search_tag="fixture",
        spec_content="deterministic source-binding fixture",
        ccbench_commit="0" * 40,
        search_config={"records": 1, "threads": 1},
        trial="loader-binding",
    )
    cfg = ident.bind_admission_policy(cfg, context.policy)
    cfg = ident.bind_environment_contract(cfg, authorization.contract)
    return cfg, context.policy, authorization


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def test_loader_drift_rejected_before_campaign_lock_or_wal_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Import stays inside the node: before U1 exists, this node itself must be red
    # because the source-binding gate module is absent, never a collection error.
    from orchestrator.campaign import contract_loader_binding

    assert contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS == _LOADER_PATHS
    assert isinstance(contract_loader_binding._REPO_ROOT, Path)
    assert issubclass(contract_loader_binding.ContractLoaderBindingError, Exception)
    repo, _commit, _blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    drifted_loader = repo / _LOADER_PATHS[0]
    drifted_loader.write_bytes(drifted_loader.read_bytes() + b"\n")
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)

    cfg, policy, _authorization = _bound_config()
    layout = CampaignLayout(root=str(tmp_path / "campaign"))
    layout.ensure()
    lock_path = Path(layout.lock_file)
    wal_path = Path(layout.wal_file)
    assert not lock_path.exists()
    assert not wal_path.exists()

    try:
        with pytest.raises(ident.IdentityMismatch) as caught:
            ident.ensure_campaign_identity(
                cfg,
                layout,
                admission_policy=policy,
            )
        assert caught.value.reason == "contract-loader-drift"
        assert "contract-loader-drift" in str(caught.value)
    finally:
        assert not lock_path.exists(), "loader drift rejection wrote campaign.lock bytes"
        assert not wal_path.exists() or wal_path.read_bytes() == b"", (
            "loader drift rejection wrote WAL bytes"
        )


def test_admission_rejects_contract_loader_blob_mismatch_at_recorded_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Keep the future resolver seam import node-local for the same test-first red.
    from orchestrator.campaign import contract_loader_binding

    assert contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS == _LOADER_PATHS
    assert isinstance(contract_loader_binding._REPO_ROOT, Path)
    assert issubclass(contract_loader_binding.ContractLoaderBindingError, Exception)
    repo, commit, blob_sha256s = _committed_loader_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)

    _cfg, policy, authorization = _bound_config()
    identity = {
        "spec_content": "deterministic admission source-binding fixture",
        "ccbench_commit": "0" * 40,
        "search_tag": "fixture",
        "search_config": {
            "records": 1,
            "threads": 1,
            "build_admission": dict(policy.as_preimage()),
        },
        "trial": "recorded-commit",
    }
    identity_preimage = _canonical_json(identity)
    mismatched = dict(blob_sha256s)
    mismatch_path = _LOADER_PATHS[0]
    recorded_blob = _git(
        repo, "cat-file", "blob", f"{commit}:{mismatch_path}",
    )
    mismatched[mismatch_path] = hashlib.sha256(b"mismatch:" + recorded_blob).hexdigest()
    assert mismatched[mismatch_path] != blob_sha256s[mismatch_path]

    lock = {
        "schema_version": "campaign-lock/v2",
        "identity_preimage": identity_preimage,
        "authority": {
            "environment_contract_sha256": authorization.contract.contract_sha256,
            "activation_serial": authorization.activation_serial,
            "activation_state_sha256": authorization.activation_state_sha256,
            "contract_loader_commit": commit,
            "contract_loader_blob_sha256s": mismatched,
        },
    }
    cfg_hash8 = hashlib.sha256(identity_preimage.encode("utf-8")).hexdigest()[:8]
    campaign = tmp_path / f"t671-source-binding-fixture-{cfg_hash8}"
    layout = CampaignLayout(root=str(campaign)).ensure()
    lock_path = Path(layout.lock_file)
    wal_path = Path(layout.wal_file)
    lock_path.write_text(_canonical_json(lock), encoding="utf-8")
    wal_path.write_bytes(b"")
    before_lock = lock_path.read_bytes()
    before_wal = wal_path.read_bytes()

    try:
        with pytest.raises(artifact_admission.ArtifactAdmissionError) as caught:
            artifact_admission.classify_campaign(layout)
        message = str(caught.value)
        assert "contract-loader-blob-mismatch" in message
        assert "historicity" not in message.lower()
        assert "historical" not in message.lower()
    finally:
        assert lock_path.read_bytes() == before_lock
        assert wal_path.read_bytes() == before_wal


def _run() -> int:
    """Keep this pytest-fixture test file inside the plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
