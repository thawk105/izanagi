"""Conjunct-level tests for ``OriginBindingCapability/v1`` issuance."""
from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator.campaign import ident
from orchestrator.campaign import p3_autonomous_workload_trial as producer
from orchestrator.campaign import reflux_origin_binding as B
from orchestrator.campaign import reflux_origin_ledger as ledger
from orchestrator.campaign import reflux_source_closure as closure_module
from orchestrator.campaign import trial_registry as registry
from orchestrator.campaign.model import CampaignConfig
from orchestrator.tests import reflux_origin_fixture_builder as F


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=registry._git_env(),
        check=False,
        capture_output=True,
        text=True,
    )


def _commit(repo: Path, message: str, *paths: Path) -> str:
    relative = [str(path.relative_to(repo)) for path in paths]
    added = _run(repo, "add", "--", *relative)
    assert added.returncode == 0, added.stderr
    committed = _run(repo, "commit", "-q", "-m", message)
    assert committed.returncode == 0, committed.stderr
    head = _run(repo, "rev-parse", "HEAD")
    assert head.returncode == 0, head.stderr
    return head.stdout.strip()


def _manifest_value(prereg_commit: str, selected_campaign_id: str) -> dict:
    rows = []
    for holdout in registry.HOLDOUTS:
        for arm in registry.ARMS:
            ordinal = len(rows)
            rows.append({
                "trial_id": f"origin-binding-{holdout.lower()}-{arm}",
                "arm": arm,
                "holdout": holdout,
                "campaign_id": (
                    selected_campaign_id
                    if ordinal == 0
                    else f"fixture-other-campaign-{ordinal}"
                ),
                "generations": 2,
                "n": 2,
            })
    return {
        "schema_version": registry.MANIFEST_SCHEMA_VERSION,
        "prereg_commit": prereg_commit,
        "trials": rows,
    }


def _registration_value(manifest: registry.TrialManifest) -> dict:
    return {
        "schema_version": registry.REGISTRATION_SCHEMA_VERSION,
        "manifest_sha256": manifest.sha256,
        "prereg_commit": manifest.prereg_commit,
        "trials": [
            {
                "trial_id": trial.trial_id,
                "arm": trial.arm,
                "holdout": trial.holdout,
                "campaign_id": trial.campaign_id,
                "generations": trial.generations,
                "n": trial.n,
            }
            for trial in manifest.trials
        ],
    }


def _effective_capability(
    manifest: registry.TrialManifest,
    monkeypatch: pytest.MonkeyPatch,
):
    module = registry.s8c_preregistration
    report = module.ActivationReport(
        commit=manifest.prereg_commit,
        condition_freeze_valid=True,
        freeze_generation=1,
        protected_sha256="1" * 64,
        freeze_reason_code="valid",
        decider_version=module.DECIDER_VERSION,
        decider_version_matches=True,
        decider_version_reason_code="decider-version-match",
        section5_findings=(),
        predicates=(),
        core_module_blob_sha256="2" * 64,
        evaluator_module_blob_sha256="3" * 64,
        projection_module_blob_sha256="4" * 64,
        effective=True,
    )
    capability = module._construct_effective(report)
    monkeypatch.setattr(
        module,
        "activation_report_at",
        lambda repo_root, commit: report,
    )
    return capability


@dataclass(frozen=True)
class _Case:
    repo: Path
    manifest_path: Path
    registry_path: Path
    effective_preregistration: object
    trial_id: str
    workload: str
    launch: B.LaunchAdmissionRederivation
    prepared_campaign: producer.PreparedCampaignIdentity
    prepared_origin: B.PreparedOriginIdentity
    validated_closure: closure_module.ValidatedSourceClosure
    authority_bytes: bytes
    closure_bytes: bytes
    receipt: dict
    authority_manifest: dict

    def launch_kwargs(self) -> dict:
        return {
            "effective_preregistration": self.effective_preregistration,
            "manifest_path": self.manifest_path,
            "trial_id": self.trial_id,
            "workloads": [self.workload],
            "allow_unregistered_exploratory": False,
            "repository_root": self.repo,
            "registry_path": self.registry_path,
        }

    def issue(self, **overrides) -> B.OriginBindingCapability:
        values = {
            "launch_rederivation": self.launch,
            "prepared_campaign": self.prepared_campaign,
            "prepared_origin": self.prepared_origin,
            "validated_source_closure": self.validated_closure,
            "authority_blob_bytes": self.authority_bytes,
            "source_closure_bytes": self.closure_bytes,
            "provisioning_receipt": self.receipt,
            **self.launch_kwargs(),
            "trial_workload": self.workload,
            "expected_axis_semantics_sha256": self.authority_manifest[
                "axis_semantics_sha256"
            ],
            "expected_verifier_policy_sha256": self.authority_manifest[
                "verifier_policy_sha256"
            ],
            "expected_environment_contract_sha256": self.authority_manifest[
                "environment_contract_sha256"
            ],
            "store_scope": "fixture",
        }
        values.update(overrides)
        return B.issue_origin_binding_capability(**values)


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Case:
    frozen = F.build_fixture_repository(tmp_path / "frozen")
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _run(repo, "init", "-q").returncode == 0
    assert _run(repo, "config", "user.email", "fixture@example.invalid").returncode == 0
    assert _run(repo, "config", "user.name", "Fixture").returncode == 0

    first_holdout = registry.HOLDOUTS[0]
    workload = registry.HOLDOUT_BINDINGS[first_holdout]["workload"]
    descriptor = {
        "schema_version": "izanagi-workload-descriptor/v1",
        "records": 100003,
        "threads": 7,
        "workload": workload,
        "ycsb_rratio": 80,
    }
    descriptor_raw = _canonical(descriptor)
    descriptor_sha = _digest(descriptor_raw)
    authority_manifest = F.build_authority_manifest(
        workload={
            "descriptor_sha256": descriptor_sha,
            "records": descriptor["records"],
            "threads": descriptor["threads"],
        }
    )
    origin_id = _digest(
        b"izanagi-reflux-origin-manifest/v2\0" + _canonical(authority_manifest)
    )
    cell_key = _digest(
        b"izanagi-reflux-origin-cell/v1\0"
        + _canonical([
            authority_manifest["workload"]["descriptor_sha256"],
            authority_manifest["axis_semantics_sha256"],
            authority_manifest["verifier_policy_sha256"],
            authority_manifest["environment_contract_sha256"],
        ])
    )
    authority_bytes = _canonical({
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": [{
            "cell_key": cell_key,
            "manifest": authority_manifest,
            "origin_id": origin_id,
        }],
    }) + b"\n"

    pre_authority = repo / ledger.AUTHORITY_RELATIVE_PATH
    pre_authority.parent.mkdir(parents=True)
    pre_authority.write_bytes(_canonical({
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": [],
    }) + b"\n")
    artifacts = repo / "artifacts"
    artifacts.mkdir()
    descriptor_path = artifacts / "workload-descriptor.json"
    descriptor_path.write_bytes(descriptor_raw)
    artifact_paths = [descriptor_path]
    for name in (
        "axis-semantics.json",
        "verifier-policy.json",
        "environment-contract.json",
    ):
        destination = artifacts / name
        destination.write_bytes((frozen.root / "artifacts" / name).read_bytes())
        artifact_paths.append(destination)
    captured_commit = _commit(
        repo, "source referents", pre_authority, *artifact_paths
    )

    source_record = F.build_source_closure_record(**{
        "captured_commit_oid": captured_commit,
        "authority_series_id": authority_manifest["authority_series_id"],
        "origin_id": origin_id,
        "cell_key": cell_key,
        (
            "referents__authority.workload.descriptor_sha256"
            "__preimage_ref__sha256"
        ): descriptor_sha,
    })
    closure_bytes = _canonical(source_record)
    receipt = {
        "authority_blob_sha256": _digest(authority_bytes),
        "source_closure_sha256": _digest(closure_bytes),
        "origin_id": origin_id,
        "cell_key": cell_key,
    }
    monkeypatch.setattr(
        closure_module,
        "resolve_by_contract_sha256",
        lambda digest: object()
        if digest == authority_manifest["environment_contract_sha256"]
        else (_ for _ in ()).throw(ValueError("unknown fixture contract")),
    )
    validated_closure = closure_module.validate_source_closure(
        closure_bytes,
        repo_root=repo,
        authority_manifest=authority_manifest,
        report_cell={
            "descriptor": descriptor,
            "descriptor_binding": {"output_sha256": descriptor_sha},
        },
        candidate_authority_blob_sha256=_digest(authority_bytes),
        human_approval_receipt=receipt,
    )

    campaign = CampaignConfig(
        spec_slug="origin-binding-fixture",
        search_tag="registered",
        spec_content="fixture-only origin binding",
        ccbench_commit="2" * 40,
        search_config={
            "descriptor_sha256": descriptor_sha,
            "records": descriptor["records"],
            "threads": descriptor["threads"],
            "workload": workload,
        },
        trial="origin-binding-fixture",
    )
    build_context = producer.build_run_context(
        generator_id=producer.GeneratorId.S8A_TRIGGER_SWEEP,
    )
    campaign = ident.bind_admission_policy(campaign, build_context.policy)
    campaign_id = str(ident.campaign_id(campaign))
    manifest_path = repo / "trial-manifest.json"
    manifest_path.write_text(
        json.dumps(
            _manifest_value(captured_commit, campaign_id),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    _commit(repo, "trial manifest", manifest_path)
    registry_path = repo / "registry" / "registry.jsonl"
    loaded_manifest = registry.load_trial_manifest(manifest_path)
    slots = []
    for trial in loaded_manifest.trials:
        identity = {
            "trial_id": trial.trial_id,
            "arm": trial.arm,
            "holdout": trial.holdout,
            "campaign_id": trial.campaign_id,
            "prereg_generation": 13,
            "replicate_index": 0,
            "attempt_index": 0,
        }
        slots.append({
            "slot_id": f"{trial.trial_id}-r0-a0",
            **identity,
            "schedule_row_sha256": _digest(_canonical(identity)),
        })
    attempt_path = registry.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest_sha256=loaded_manifest.sha256,
        freeze_id=f"freeze-{loaded_manifest.sha256[:16]}",
        prereg_generation=13,
        slots=slots,
    )
    content_commit = _commit(repo, "attempt registry genesis", attempt_path)
    genesis = json.loads(attempt_path.read_bytes().splitlines()[0])
    binding_path = repo / registry.DEFAULT_EFFECTIVE_BINDING_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_bytes(_canonical({
        "schema_version": registry.EFFECTIVE_BINDING_SCHEMA_VERSION,
        "prereg_content_commit": content_commit,
        "manifest_path": manifest_path.relative_to(repo).as_posix(),
        "manifest_sha256": loaded_manifest.sha256,
        "freeze_id": genesis["freeze_id"],
        "attempt_registry_path": registry.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_initial_sha256": _digest(attempt_path.read_bytes()),
    }))
    effective_commit = _commit(repo, "effective binding", binding_path)
    registry.append_trial_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry_path,
        prereg_effective_commit=effective_commit,
    )
    registry.s8c_arm_inputs.generate_off_neutral_artifacts(repository_root=repo)
    _commit(
        repo,
        "trial registry and arm inputs",
        registry_path,
        repo / registry.s8c_arm_inputs.OFF_DESCRIPTOR_RELATIVE_PATH,
        repo / registry.s8c_arm_inputs.OFF_FREEZE_RELATIVE_PATH,
    )
    loaded_manifest = registry.load_trial_manifest(manifest_path)
    trial = loaded_manifest.trials[0]
    effective = _effective_capability(loaded_manifest, monkeypatch)
    admission = registry.admit_registered_launch(
        effective_preregistration=effective,
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[workload],
        repository_root=repo,
        registry_path=registry_path,
    )
    launch_kwargs = {
        "effective_preregistration": effective,
        "manifest_path": manifest_path,
        "trial_id": trial.trial_id,
        "workloads": [workload],
        "allow_unregistered_exploratory": False,
        "repository_root": repo,
        "registry_path": registry_path,
    }
    assert admission.binding is not None
    arm_execution = registry.bind_trial_arm(admission.binding, repository_root=repo)
    launch = B.rederive_launch_admission(
        admission, arm_execution=arm_execution, **launch_kwargs
    )
    entry = producer.resolve_workload_entry(workload)
    prepared_campaign = producer.PreparedCampaignIdentity(
        descriptor=descriptor,
        descriptor_record={"output_sha256": descriptor_sha},
        campaign=campaign,
        campaign_id=campaign_id,
        perf=producer._perf_for(entry),
    )
    prepared_origin = B.prepare_origin_identity(
        authority_blob_bytes=authority_bytes,
        source_closure_bytes=closure_bytes,
        provisioning_receipt=receipt,
        validated_source_closure=validated_closure,
    )
    return _Case(
        repo=repo,
        manifest_path=manifest_path,
        registry_path=registry_path,
        effective_preregistration=effective,
        trial_id=trial.trial_id,
        workload=workload,
        launch=launch,
        prepared_campaign=prepared_campaign,
        prepared_origin=prepared_origin,
        validated_closure=validated_closure,
        authority_bytes=authority_bytes,
        closure_bytes=closure_bytes,
        receipt=receipt,
        authority_manifest=authority_manifest,
    )


def test_fixture_scope_positive_binds_exact_fields(case: _Case) -> None:
    capability = case.issue()
    record = B.origin_binding_capability_record(capability)
    assert set(record) == {
        "authority_blob_sha256",
        "source_closure_sha256",
        "origin_id",
        "cell_key",
        "authority_workload",
        "axis_semantics_sha256",
        "verifier_policy_sha256",
        "environment_contract_sha256",
        "campaign_id",
        "trial_workload",
        "measurement_head",
        "store_scope",
        "issuer_seal",
    }
    assert set(record["authority_workload"]) == {
        "descriptor_sha256", "records", "threads",
    }
    assert record["store_scope"] == "fixture"
    assert capability.enforcement_arm == "on"
    assert capability.arm_binding_digest_sha256 == (
        case.launch.arm_execution.arm_binding_digest_sha256
    )
    assert case.launch.certifying is False
    assert not hasattr(capability, "certifying")
    B.assert_origin_binding_capability_record(record, capability)


def test_decision_1_rejects_admission_that_fails_fresh_registry_derivation(
    case: _Case,
) -> None:
    altered = dataclasses.replace(case.launch.admission, trial_id="altered-trial")
    with pytest.raises(B.OriginBindingError, match="launch-admission"):
        B.rederive_launch_admission(
            altered,
            arm_execution=case.launch.arm_execution,
            **case.launch_kwargs(),
        )


def test_decision_2_rejects_exploratory_production_capability(case: _Case) -> None:
    trial_id = "fresh-origin-exploratory"
    admission = registry.admit_unregistered_exploratory(
        trial_id=trial_id,
        workloads=["ycsb-a"],
        allow_unregistered_exploratory=True,
        repository_root=case.repo,
        registry_path=case.registry_path,
    )
    launch = B.rederive_launch_admission(
        admission,
        effective_preregistration=None,
        manifest_path=None,
        trial_id=trial_id,
        workloads=["ycsb-a"],
        allow_unregistered_exploratory=True,
        repository_root=case.repo,
        registry_path=case.registry_path,
    )
    with pytest.raises(B.OriginBindingError, match="launch-mode"):
        case.issue(
            launch_rederivation=launch,
            effective_preregistration=None,
            manifest_path=None,
            trial_id=trial_id,
            workloads=["ycsb-a"],
            allow_unregistered_exploratory=True,
            store_scope="production",
        )


def test_decision_2_rejects_unissued_trial_binding(case: _Case) -> None:
    issued = case.launch.binding
    assert issued is not None
    forged = registry.TrialBinding(
        **{
            field.name: getattr(issued, field.name)
            for field in dataclasses.fields(issued)
            if field.name != "_seal"
        },
        _seal=object(),
    )
    admission = dataclasses.replace(case.launch.admission, binding=forged)
    with pytest.raises(B.OriginBindingError, match="launch-binding") as caught:
        B.rederive_launch_admission(
            admission,
            arm_execution=case.launch.arm_execution,
            **case.launch_kwargs(),
        )
    assert isinstance(caught.value.__cause__, registry.TrialRegistryError)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ("campaign", "campaign-binding"),
        ("workload", "campaign-binding"),
    ],
)
def test_decision_3_rejects_campaign_or_workload_mismatch(
    case: _Case,
    override: str,
    message: str,
) -> None:
    if override == "campaign":
        prepared = dataclasses.replace(
            case.prepared_campaign, campaign_id="different-campaign"
        )
        kwargs = {"prepared_campaign": prepared}
    else:
        kwargs = {"trial_workload": "different-workload"}
    with pytest.raises(B.OriginBindingError, match=message):
        case.issue(**kwargs)


def test_decision_4_rejects_descriptor_canonical_digest_mismatch(case: _Case) -> None:
    descriptor = dict(case.prepared_campaign.descriptor)
    descriptor["records"] += 1
    prepared = dataclasses.replace(case.prepared_campaign, descriptor=descriptor)
    with pytest.raises(B.OriginBindingError, match="prepared-descriptor"):
        case.issue(prepared_campaign=prepared)


@pytest.mark.parametrize("field", ["records", "threads"])
def test_decision_4_rejects_authority_scale_mismatch(
    case: _Case,
    field: str,
) -> None:
    workload = dataclasses.replace(
        case.prepared_origin.authority_workload,
        **{field: getattr(case.prepared_origin.authority_workload, field) + 1},
    )
    altered = dataclasses.replace(case.prepared_origin, authority_workload=workload)
    with pytest.raises(B.OriginBindingError, match="authority-workload"):
        case.issue(prepared_origin=altered)


def test_decision_4_search_config_digest_is_not_independently_reachable(
    case: _Case,
) -> None:
    config = dataclasses.replace(
        case.prepared_campaign.campaign,
        search_config={
            **case.prepared_campaign.campaign.search_config,
            "descriptor_sha256": "f" * 64,
        },
    )
    prepared = dataclasses.replace(case.prepared_campaign, campaign=config)
    # campaign_id includes search_config, so decision 3 necessarily rejects first.
    with pytest.raises(B.OriginBindingError, match="prepared-campaign"):
        case.issue(prepared_campaign=prepared)


def test_decision_5_rederives_dataclasses_replace_origin_fields(case: _Case) -> None:
    altered = dataclasses.replace(case.prepared_origin, origin_id="e" * 64)
    assert altered._seal is case.prepared_origin._seal
    with pytest.raises(B.OriginBindingError, match="origin-rederivation"):
        case.issue(prepared_origin=altered)


def test_decision_5_rederives_dataclasses_replace_launch_fields(case: _Case) -> None:
    altered = dataclasses.replace(case.launch, reason_code="caller-selected")
    assert altered._seal is case.launch._seal
    with pytest.raises(B.OriginBindingError, match="issued-launch"):
        case.issue(launch_rederivation=altered)


def test_registered_origin_binding_requires_issued_arm_execution(case: _Case) -> None:
    altered = dataclasses.replace(case.launch, arm_execution=None)
    with pytest.raises(B.OriginBindingError, match="arm-execution"):
        case.issue(launch_rederivation=altered)


def test_final_capability_rejects_dataclasses_replace(case: _Case) -> None:
    capability = case.issue()
    altered = dataclasses.replace(capability, campaign_id="caller-selected")
    assert altered._seal is capability._seal
    with pytest.raises(B.OriginBindingError, match="issuer snapshot"):
        B.assert_issued_origin_binding_capability(altered)


def test_decision_5_rejects_changed_provisioning_receipt(case: _Case) -> None:
    receipt = dict(case.receipt)
    receipt["authority_blob_sha256"] = "f" * 64
    with pytest.raises(B.OriginBindingError, match="provisioning-receipt"):
        case.issue(provisioning_receipt=receipt)


def test_decision_5_rechecks_validated_source_closure_fields(case: _Case) -> None:
    altered = copy.copy(case.validated_closure)
    object.__setattr__(altered, "origin_id", "e" * 64)
    assert altered._seal is case.validated_closure._seal
    with pytest.raises(B.OriginBindingError, match="validated-source-closure"):
        case.issue(validated_source_closure=altered)


@pytest.mark.parametrize(
    "argument",
    [
        "expected_axis_semantics_sha256",
        "expected_verifier_policy_sha256",
        "expected_environment_contract_sha256",
    ],
)
def test_decision_6_rejects_each_expected_binding(case: _Case, argument: str) -> None:
    with pytest.raises(B.OriginBindingError, match="expected-binding"):
        case.issue(**{argument: "f" * 64})


def test_decision_7_true_is_rejected_upstream_and_has_no_issuance_path(
    case: _Case,
) -> None:
    altered_admission = dataclasses.replace(case.launch.admission, certifying=True)
    with pytest.raises(B.OriginBindingError, match="launch-admission"):
        B.rederive_launch_admission(
            altered_admission,
            arm_execution=case.launch.arm_execution,
            **case.launch_kwargs(),
        )

    source_path = Path(B.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    true_writes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            true_writes.extend(
                keyword
                for keyword in node.keywords
                if keyword.arg == "certifying"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            )
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if isinstance(value, ast.Constant) and value.value is True:
                true_writes.extend(
                    target
                    for target in targets
                    if (
                        isinstance(target, ast.Name) and target.id == "certifying"
                    ) or (
                        isinstance(target, ast.Attribute)
                        and target.attr == "certifying"
                    )
                )
    assert true_writes == []


def test_production_capability_is_unconditionally_rejected(case: _Case) -> None:
    with pytest.raises(B.OriginBindingError, match="production-authority"):
        case.issue(store_scope="production")


def test_dataclass_and_wire_fields_are_exact(case: _Case) -> None:
    assert {field.name for field in dataclasses.fields(B.OriginBindingCapability)} == {
        "authority_blob_sha256",
        "source_closure_sha256",
        "origin_id",
        "cell_key",
        "authority_workload",
        "axis_semantics_sha256",
        "verifier_policy_sha256",
        "environment_contract_sha256",
        "campaign_id",
        "trial_workload",
        "measurement_head",
        "store_scope",
        "_seal",
        "enforcement_arm",
        "arm_binding_digest_sha256",
    }
    assert {field.name for field in dataclasses.fields(B.AuthorityWorkload)} == {
        "descriptor_sha256", "records", "threads",
    }
    capability = case.issue()
    B.assert_origin_binding_capability_record(
        B.origin_binding_capability_record(capability), capability
    )


@pytest.mark.parametrize(
    "mutation",
    ["extra", "missing", "top-type", "nested-extra", "nested-missing", "nested-type"],
)
def test_capability_record_rejects_added_missing_and_mistyped_fields(
    case: _Case,
    mutation: str,
) -> None:
    capability = case.issue()
    record = copy.deepcopy(B.origin_binding_capability_record(capability))
    if mutation == "extra":
        record["extra"] = None
    elif mutation == "missing":
        del record["origin_id"]
    elif mutation == "top-type":
        record["issuer_seal"] = 1
    elif mutation == "nested-extra":
        record["authority_workload"]["extra"] = None
    elif mutation == "nested-missing":
        del record["authority_workload"]["threads"]
    else:
        record["authority_workload"]["records"] = True
    with pytest.raises(B.OriginBindingError):
        B.assert_origin_binding_capability_record(record, capability)


@pytest.mark.parametrize("scope", [None, 1, "unknown", True])
def test_store_scope_type_and_closed_values_are_rejected(case: _Case, scope) -> None:
    with pytest.raises(B.OriginBindingError, match="store-scope"):
        case.issue(store_scope=scope)
