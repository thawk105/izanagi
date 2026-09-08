# -*- coding: utf-8 -*-
"""[T-671] contract loader source binding の決定的な test-first 回帰。"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission, env_contract, ident
from orchestrator.campaign.build_admission import GeneratorId, build_run_context
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import CampaignConfig


_PRE_WAVE_ENFORCEMENT_SOURCE_PATHS = (
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
)
_PRE_T733_ENFORCEMENT_SOURCE_PATHS = (
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
_T733_ENFORCEMENT_SOURCE_PATH_SUFFIX = (
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
_EXPECTED_ENFORCEMENT_SOURCE_PATHS = (
    *_PRE_T733_ENFORCEMENT_SOURCE_PATHS,
    *_T733_ENFORCEMENT_SOURCE_PATH_SUFFIX,
)
_PRE_T1287_ENFORCEMENT_SOURCE_PATHS = _PRE_T733_ENFORCEMENT_SOURCE_PATHS[:14]
_S8C_DECIDER_PATHS = _PRE_T733_ENFORCEMENT_SOURCE_PATHS[14:17]
_SOURCE_BINDING_IMPLEMENTATION_PATHS = _PRE_T733_ENFORCEMENT_SOURCE_PATHS[17:19]
_RECEIPT_IMPLEMENTATION_PATHS = _PRE_T733_ENFORCEMENT_SOURCE_PATHS[19:24]
_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)


def _git(repo: Path, *args: str) -> bytes:
    """Run Git fail-closed; an unavailable/broken Git is a test failure, not a skip."""
    executable = shutil.which("git")
    if executable is None:
        pytest.fail(
            "source-binding Git infrastructure failure: git executable is unavailable"
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
            "source-binding Git infrastructure failure: command timed out: "
            f"args={args!r}: {exc}"
        )
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.fail(
            "source-binding Git infrastructure failure: command could not run: "
            f"args={args!r}: {exc}"
        )
    if completed.returncode != 0:
        pytest.fail(
            "source-binding Git infrastructure failure: command returned nonzero: "
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


def test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths() -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding
    from orchestrator.campaign import s8c_preregistration

    assert campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
    assert len(_PRE_T733_ENFORCEMENT_SOURCE_PATHS) == 24
    assert len(_T733_ENFORCEMENT_SOURCE_PATH_SUFFIX) == 39
    assert len(_EXPECTED_ENFORCEMENT_SOURCE_PATHS) == 63
    assert (
        contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS
        is campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )
    assert _S8C_DECIDER_PATHS == (
        s8c_preregistration.CORE_MODULE_PATH,
        s8c_preregistration.EVALUATOR_MODULE_PATH,
        s8c_preregistration.PROJECTION_MODULE_PATH,
    )
    assert _SOURCE_BINDING_IMPLEMENTATION_PATHS == (
        "orchestrator/campaign/campaign_lock.py",
        "orchestrator/campaign/contract_loader_binding.py",
    )
    assert _RECEIPT_IMPLEMENTATION_PATHS == (
        "orchestrator/campaign/guided.py",
        "orchestrator/campaign/replay.py",
        "orchestrator/qualification/artifacts.py",
        "orchestrator/qualification/t126_driver.py",
        "orchestrator/verifier/commit_receipt.py",
    )


@pytest.mark.parametrize(
    ("mutated_path", "old_bytes", "new_bytes"),
    (
        (
            "orchestrator/verifier/__init__.py",
            b"    verify_trace_dir_with_capability,",
            b"    verify_trace_dir_with_capability as unchecked_verify_trace_dir_with_capability,",
        ),
        (
            "orchestrator/verifier/report.py",
            b'"certified": res.certified,',
            b'"certified": True,',
        ),
    ),
    ids=("verifier-init-dispatch", "verifier-report-payload"),
)
def test_pre_wave_exact_twelve_misses_but_exact_fourteen_rejects_new_enforcement_face(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutated_path: str,
    old_bytes: bytes,
    new_bytes: bytes,
) -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding

    production_paths = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    assert contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS is production_paths
    assert production_paths[:12] == _PRE_WAVE_ENFORCEMENT_SOURCE_PATHS
    assert mutated_path in production_paths
    repo, _commit, _blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    clean_binding = contract_loader_binding.capture_contract_loader_binding()
    contract_loader_binding.verify_live_contract_loader_binding(clean_binding)

    target = repo / mutated_path
    original = target.read_bytes()
    assert original.count(old_bytes) == 1
    assert original.count(new_bytes) == 0
    mutated = original.replace(old_bytes, new_bytes)
    assert mutated != original
    target.write_bytes(mutated)

    monkeypatch.setattr(
        contract_loader_binding,
        "CONTRACT_LOADER_RELATIVE_PATHS",
        _PRE_WAVE_ENFORCEMENT_SOURCE_PATHS,
    )
    pre_wave_binding = contract_loader_binding.capture_contract_loader_binding()
    assert tuple(pre_wave_binding.contract_loader_blob_sha256s) == (
        _PRE_WAVE_ENFORCEMENT_SOURCE_PATHS
    )
    contract_loader_binding.verify_live_contract_loader_binding(pre_wave_binding)

    monkeypatch.setattr(
        contract_loader_binding,
        "CONTRACT_LOADER_RELATIVE_PATHS",
        production_paths,
    )
    assert contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS is production_paths
    assert (
        contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS
        == campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )

    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
    ) as capture_error:
        contract_loader_binding.capture_contract_loader_binding()
    assert "contract-loader-drift" in str(capture_error.value)
    assert mutated_path in str(capture_error.value)

    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
    ) as live_error:
        contract_loader_binding.verify_live_contract_loader_binding(clean_binding)
    assert "contract-loader-drift" in str(live_error.value)
    assert mutated_path in str(live_error.value)


def _assert_pre_t1287_exact_fourteen_misses_new_face(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutated_path: str,
) -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding

    production_paths = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    assert production_paths[:14] == _PRE_T1287_ENFORCEMENT_SOURCE_PATHS
    assert mutated_path in production_paths[14:]
    repo, _commit, _blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    clean_binding = contract_loader_binding.capture_contract_loader_binding()
    contract_loader_binding.verify_live_contract_loader_binding(clean_binding)

    target = repo / mutated_path
    target.write_bytes(target.read_bytes() + b"\n# isolated enforcement mutation\n")

    monkeypatch.setattr(
        contract_loader_binding,
        "CONTRACT_LOADER_RELATIVE_PATHS",
        _PRE_T1287_ENFORCEMENT_SOURCE_PATHS,
    )
    pre_t1287_binding = contract_loader_binding.capture_contract_loader_binding()
    contract_loader_binding.verify_live_contract_loader_binding(pre_t1287_binding)

    monkeypatch.setattr(
        contract_loader_binding,
        "CONTRACT_LOADER_RELATIVE_PATHS",
        production_paths,
    )
    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
        match="contract-loader-drift",
    ) as caught:
        contract_loader_binding.capture_contract_loader_binding()
    assert mutated_path in str(caught.value)


@pytest.mark.parametrize(
    "mutated_path",
    _S8C_DECIDER_PATHS,
    ids=lambda path: f"s8c-{Path(path).name}",
)
def test_pre_t1287_exact_fourteen_misses_but_exact_twenty_four_rejects_s8c_face(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutated_path: str,
) -> None:
    _assert_pre_t1287_exact_fourteen_misses_new_face(
        tmp_path, monkeypatch, mutated_path,
    )


@pytest.mark.parametrize(
    "mutated_path",
    _RECEIPT_IMPLEMENTATION_PATHS,
    ids=lambda path: f"receipt-{Path(path).name}",
)
def test_pre_t1287_exact_fourteen_misses_but_exact_twenty_four_rejects_receipt_face(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutated_path: str,
) -> None:
    _assert_pre_t1287_exact_fourteen_misses_new_face(
        tmp_path, monkeypatch, mutated_path,
    )


def test_exact_twenty_four_clean_closure_capture_and_live_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding

    repo, commit, _blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    binding = contract_loader_binding.capture_contract_loader_binding()
    contract_loader_binding.verify_live_contract_loader_binding(binding)

    assert campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS == (
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
    assert (
        contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS
        is campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    )
    assert tuple(binding.contract_loader_blob_sha256s) == (
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
    assert set(binding.contract_loader_blob_sha256s) == set(
        _EXPECTED_ENFORCEMENT_SOURCE_PATHS
    )
    for relative in _EXPECTED_ENFORCEMENT_SOURCE_PATHS:
        committed_blob = _git(
            repo, "cat-file", "blob", f"{commit}:{relative}",
        )
        assert (
            hashlib.sha256(committed_blob).hexdigest()
            == binding.contract_loader_blob_sha256s[relative]
        )


def test_contract_loader_binding_ignores_fake_git_at_front_of_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import contract_loader_binding

    repo, _commit, _blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    target = repo / contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS[0]
    target.write_bytes(target.read_bytes() + b"\n# forged live closure\n")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    marker = tmp_path / "fake-git-ran"
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        f"touch {marker}\n"
        "exit 0\n",
        encoding="ascii",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv(
        "PATH", os.fspath(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)

    with pytest.raises(
        contract_loader_binding.ContractLoaderBindingError,
        match="contract-loader-drift",
    ):
        contract_loader_binding.capture_contract_loader_binding()
    assert not marker.exists()


def test_new_certified_lock_accepts_unratified_closure_and_records_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import campaign_lock, contract_loader_binding

    repo, commit, blob_sha256s = _committed_loader_repo(
        tmp_path, copy_current_loaders=True,
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    cfg, policy, _authorization = _bound_config()
    layout = CampaignLayout(root=str(tmp_path / "unratified-campaign")).ensure()

    assert ident.ensure_campaign_identity(
        cfg, layout, admission_policy=policy,
    ) is True
    decoded = campaign_lock.decode_campaign_lock(Path(layout.lock_file).read_text())
    assert decoded.authority is not None
    assert decoded.authority.contract_loader_commit == commit
    assert decoded.authority.contract_loader_blob_sha256s == blob_sha256s


def test_verifier_package_module_census_requires_ruling_for_new_modules() -> None:
    """新 module を閉包へ入れるか除外するかは、赤をユーザー裁定へ返す。"""
    verifier_dir = Path(__file__).resolve().parents[1] / "verifier"
    closure_members = frozenset({
        "__init__.py",
        "core.py",
        "commit_receipt.py",
        "dsg.py",
        "model.py",
        "parse.py",
        "report.py",
    })
    intentional_exclusions = frozenset({"__main__.py", "cli.py"})
    actual = frozenset(
        path.name
        for path in verifier_dir.iterdir()
        if path.is_file() and path.suffix == ".py"
    )

    assert len(closure_members) == 7
    assert len(intentional_exclusions) == 2
    assert closure_members.isdisjoint(intentional_exclusions)
    assert actual == closure_members | intentional_exclusions


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
        ("artifact_admission.py", "_verify_committed_loader_binding",
         "verify_committed_contract_loader_blobs"): 1,
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
