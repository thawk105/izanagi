# -*- coding: utf-8 -*-
"""[T-671] contract loader source binding の決定的な test-first 回帰。"""
from __future__ import annotations

import ast
from collections import Counter
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


_EXPECTED_ENFORCEMENT_SOURCE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
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

    for index, relative in enumerate(
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS, start=1,
    ):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if copy_current_loaders:
            current = Path(__file__).resolve().parents[2] / relative
            path.write_bytes(current.read_bytes())
        else:
            path.write_bytes(f"loader fixture {index}".encode("ascii"))

    _git(repo, "add", "--", *_EXPECTED_ENFORCEMENT_SOURCE_PATHS)
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
        for relative in _EXPECTED_ENFORCEMENT_SOURCE_PATHS
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


def test_enforcement_source_closure_is_the_independent_exact_eight_paths() -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding

    assert campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
    assert (
        contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS
        is campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )


@pytest.mark.parametrize(
    "drift_path", _EXPECTED_ENFORCEMENT_SOURCE_PATHS,
    ids=lambda path: Path(path).name,
)
def test_loader_drift_rejected_before_campaign_lock_or_wal_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift_path: str,
) -> None:
    # Import stays inside the node: before U1 exists, this node itself must be red
    # because the source-binding gate module is absent, never a collection error.
    from orchestrator.campaign import contract_loader_binding

    assert contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
    assert isinstance(contract_loader_binding._REPO_ROOT, Path)
    assert issubclass(contract_loader_binding.ContractLoaderBindingError, Exception)
    repo, _commit, _blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    drifted_loader = repo / drift_path
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
        assert drift_path in str(caught.value)
    finally:
        assert not lock_path.exists(), "loader drift rejection wrote campaign.lock bytes"
        assert not wal_path.exists() or wal_path.read_bytes() == b"", (
            "loader drift rejection wrote WAL bytes"
        )


@pytest.mark.parametrize(
    "drift_path", _EXPECTED_ENFORCEMENT_SOURCE_PATHS,
    ids=lambda path: Path(path).name,
)
def test_live_verification_rejects_each_dirty_enforcement_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift_path: str,
) -> None:
    from orchestrator.campaign import contract_loader_binding

    repo, _commit, _blob_sha256s = _committed_loader_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    binding = contract_loader_binding.capture_contract_loader_binding()
    assert set(binding.contract_loader_blob_sha256s) == set(
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )

    drifted = repo / drift_path
    drifted.write_bytes(drifted.read_bytes() + b"\nuncommitted edit\n")

    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
    ) as caught:
        contract_loader_binding.verify_live_contract_loader_binding(binding)
    message = str(caught.value)
    assert "contract-loader-drift" in message
    assert drift_path in message


@pytest.mark.parametrize(
    "mismatch_path", _EXPECTED_ENFORCEMENT_SOURCE_PATHS,
    ids=lambda path: Path(path).name,
)
def test_admission_rejects_contract_loader_blob_mismatch_at_recorded_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mismatch_path: str,
) -> None:
    # Keep the future resolver seam import node-local for the same test-first red.
    from orchestrator.campaign import contract_loader_binding

    assert contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
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
        assert mismatch_path in message
        assert "historicity" not in message.lower()
        assert "historical" not in message.lower()
    finally:
        assert lock_path.read_bytes() == before_lock
        assert wal_path.read_bytes() == before_wal


def test_live_verification_uses_recorded_commit_when_head_has_advanced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import contract_loader_binding

    repo, recorded_commit, _blob_sha256s = _committed_loader_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    binding = contract_loader_binding.capture_contract_loader_binding()
    changed_path = _EXPECTED_ENFORCEMENT_SOURCE_PATHS[0]
    changed = repo / changed_path
    changed.write_bytes(changed.read_bytes() + b"\nhead advanced\n")
    _git(repo, "add", "--", changed_path)
    _git(
        repo,
        "-c", "user.email=t671-fixture@example.invalid",
        "-c", "user.name=T671 fixture",
        "commit", "-q", "-m", "advance fixture head",
    )
    current_head = _git(
        repo, "rev-parse", "--verify", "HEAD^{commit}",
    ).decode().strip()
    assert current_head != recorded_commit
    changed.write_bytes(
        _git(repo, "cat-file", "blob", f"{recorded_commit}:{changed_path}")
    )

    contract_loader_binding.verify_live_contract_loader_binding(binding)


@pytest.mark.parametrize(
    "dirty_path", _EXPECTED_ENFORCEMENT_SOURCE_PATHS,
    ids=lambda path: Path(path).name,
)
def test_shared_v2_fixture_default_uses_recorded_blobs_when_disk_is_dirty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dirty_path: str,
) -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding
    from orchestrator.tests.campaign_lock_test_support import (
        build_v2_campaign_lock,
    )

    repo, recorded_commit, _blob_sha256s = _committed_loader_repo(tmp_path)
    dirty_file = repo / dirty_path
    dirty_file.write_bytes(dirty_file.read_bytes() + b"\nuncommitted edit\n")
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    identity_preimage = _canonical_json({
        "spec_content": "dirty shared fixture",
        "ccbench_commit": "0" * 40,
        "search_tag": "fixture",
        "search_config": {},
        "trial": None,
    })

    decoded = campaign_lock.decode_campaign_lock(
        build_v2_campaign_lock(identity_preimage)
    )

    assert decoded.authority is not None
    assert decoded.authority.contract_loader_commit == recorded_commit
    recorded_blob = _git(
        repo, "cat-file", "blob", f"{recorded_commit}:{dirty_path}",
    )
    recorded_digest = hashlib.sha256(recorded_blob).hexdigest()
    assert (
        decoded.authority.contract_loader_blob_sha256s[dirty_path]
        == recorded_digest
    )
    assert recorded_digest != hashlib.sha256(dirty_file.read_bytes()).hexdigest()


def test_production_contract_loader_binding_call_sites_are_exact() -> None:
    campaign_dir = Path(__file__).resolve().parents[1] / "campaign"
    expected = Counter({
        ("ident.py", "_capture_current_loader_binding",
         "capture_contract_loader_binding"): 1,
        ("ident.py", "_capture_current_loader_binding",
         "verify_live_contract_loader_binding"): 1,
        ("ident.py", "_binding_from_lock", "binding_from_authority"): 1,
        ("ident.py", "verify_against_lock",
         "verify_live_contract_loader_binding"): 1,
        ("artifact_admission.py", "_verify_committed_loader_binding",
         "binding_from_authority"): 1,
        ("artifact_admission.py", "_verify_committed_loader_binding",
         "verify_committed_contract_loader_binding"): 1,
        ("artifact_admission.py", "_require_verifier_epoch_for_purpose",
         "capture_contract_loader_binding"): 1,
    })
    actual: Counter[tuple[str, str, str]] = Counter()

    for name in ("ident.py", "artifact_admission.py"):
        tree = ast.parse((campaign_dir / name).read_text(encoding="utf-8"))
        for function in (
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            for call in (
                node for node in ast.walk(function) if isinstance(node, ast.Call)
            ):
                func = call.func
                if (isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "contract_loader_binding"):
                    actual[(name, function.name, func.attr)] += 1

    assert actual == expected


def _run() -> int:
    """Keep this pytest-fixture test file inside the plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
