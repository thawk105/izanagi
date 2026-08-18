# -*- coding: utf-8 -*-
"""s8c preregistration evidence predicate の fail-closed / 恒真化対策。"""
from __future__ import annotations

import ast
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_holdout_freeze  # noqa: E402
from orchestrator.campaign import s8c_generation_projection as projection  # noqa: E402
from orchestrator.campaign import s8c_preregistration as core  # noqa: E402
from orchestrator.campaign import s8c_preregistration_evidence as M  # noqa: E402


CONTRACT_FILE = _ROOT / core.EVIDENCE_CONTRACT_PATH


def _git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    ).stdout


def _write(root: Path, relative: str, raw: bytes | str) -> None:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw.encode("utf-8") if isinstance(raw, str) else raw)


def _init_repo(tmp_path: Path, name: str = "repo") -> Path:
    root = tmp_path / name
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    _write(root, core.EVIDENCE_CONTRACT_PATH, CONTRACT_FILE.read_bytes())
    return root


def _commit(root: Path, subject: str = "fixture") -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject)
    return _git(root, "rev-parse", "HEAD").decode("ascii").strip()


def _result(root: Path, commit: str, identifier: str) -> core.PredicateResult:
    results = M.get_registry().evaluate_all(commit, repo_root=root)
    return {item.id: item for item in results}[identifier]


def _snapshot_current_commit(tmp_path: Path) -> tuple[Path, str]:
    """現 HEAD を一時 commit へ写す補助検査。

    snapshot と HEAD は同じ evaluator を使うため、resolver mutation の kill 根拠には
    数えない。ここで固定するのは commit-blob 投影の同値性だけである。
    """
    root = _init_repo(tmp_path, "current-snapshot")
    paths = {
        reference.path
        for result in M.get_registry().evaluate_all("HEAD", repo_root=_ROOT)
        for reference in result.evidence
    }
    paths.add(core.EVIDENCE_CONTRACT_PATH)
    tracked = set(
        _git(_ROOT, "ls-tree", "-r", "--name-only", "HEAD").decode().splitlines()
    )
    assert paths - tracked <= {core.EVIDENCE_CONTRACT_PATH}
    present = sorted(paths & tracked)
    if present:
        archive = _git(_ROOT, "archive", "--format=tar", "HEAD", "--", *present)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            for member in bundle.getmembers():
                if not member.isfile():
                    continue
                source = bundle.extractfile(member)
                assert source is not None
                _write(root, member.name, source.read())
    # HEAD がこの単位をまだ含まない段 5 でも、評価対象 commit には契約を含める。
    _write(root, core.EVIDENCE_CONTRACT_PATH, CONTRACT_FILE.read_bytes())
    return root, _commit(root, "current evidence snapshot")


@pytest.fixture(scope="module")
def current_commit_snapshot(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, str]:
    """Read-only snapshot shared by all current-tree equivalence checks."""
    return _snapshot_current_commit(tmp_path_factory.mktemp("current-commit"))


def test_predicate_registry_is_exactly_c01_through_c12(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    head = _commit(root)
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert tuple(item.id for item in results) == core.PREDICATE_IDS
    assert len(results) == 12
    assert all(item.reason_code in M.REASON_CODES for item in results)


def test_current_repository_snapshot_has_zero_satisfied_predicates(
    current_commit_snapshot: tuple[Path, str],
) -> None:
    root, head = current_commit_snapshot
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert sum(item.status is core.PredicateStatus.SATISFIED for item in results) == 0
    for item in results:
        assert item.evidence
        assert all(ref.path and len(ref.blob_sha256) == 64 for ref in item.evidence)


def test_current_repository_snapshot_exactly_matches_head(
    current_commit_snapshot: tuple[Path, str],
) -> None:
    root, head = current_commit_snapshot
    snapshot = tuple(M.get_registry().evaluate_all(head, repo_root=root))
    actual = tuple(M.get_registry().evaluate_all("HEAD", repo_root=_ROOT))
    assert snapshot == actual


def test_current_repository_gap_reason_snapshot_requires_cross_wave_review(
    current_commit_snapshot: tuple[Path, str],
) -> None:
    """個別 reason は gap ledger。他 wave の land 時は意図を再審査して更新する。

    [T-325] の land で trial_registry の capability probe 段階を通過した。
    """
    root, head = current_commit_snapshot
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert {
        item.id: (item.status, item.reason_code) for item in results
    } == {
        "C01": (core.PredicateStatus.UNSATISFIED, "ratified-generation-reference-absent"),
        "C02": (
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            "completion-proof-not-machine-checkable",
        ),
        "C03": (core.PredicateStatus.EVIDENCE_UNDEFINED, "manifest-registry-proof-undefined"),
        "C04": (core.PredicateStatus.UNSATISFIED, "crash-policy-cell-partial"),
        "C05": (core.PredicateStatus.EVIDENCE_UNDEFINED, "schedule-schema-absent"),
        "C06": (core.PredicateStatus.EVIDENCE_UNDEFINED, "budget-consumer-contract-undefined"),
        "C07": (core.PredicateStatus.EVIDENCE_UNDEFINED, "floor-judge-contract-undefined"),
        "C08": (core.PredicateStatus.EVIDENCE_UNDEFINED, "prereg-binding-proof-undefined"),
        "C09": (core.PredicateStatus.UNSATISFIED, "formal-acceptance-layer3-consumer-absent"),
        "C10": (core.PredicateStatus.UNSATISFIED, "cross-binding-verifier-incomplete"),
        "C11": (core.PredicateStatus.EVIDENCE_UNDEFINED, "completion-proof-not-machine-checkable"),
        "C12": (core.PredicateStatus.UNSATISFIED, "allocation-enforcement-consumer-absent"),
    }


def test_current_repository_c12_registry_reports_unwired_allocation_consumer(
    current_commit_snapshot: tuple[Path, str],
) -> None:
    # production が正しく配線されたら反転させる snapshot tripwire である。
    root, head = current_commit_snapshot
    results = M.get_registry().evaluate_all(head, repo_root=root)
    c12 = {item.id: item for item in results}["C12"]
    assert c12.status is core.PredicateStatus.UNSATISFIED
    assert c12.reason_code == "allocation-enforcement-consumer-absent"


def test_c02_missing_registry_preserves_capability_absent_reason(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        TOKEN_ONLY_C02_PRODUCER,
    )
    head = _commit(root, "C02 registry absent")

    result = _result(root, head, "C02")
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "trial-registry-capability-absent"


def test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer(
    current_commit_snapshot: tuple[Path, str],
) -> None:
    # production が正しく配線されたら反転させる snapshot tripwire である。
    root, head = current_commit_snapshot
    condition = M.load_contract_bytes(CONTRACT_FILE.read_bytes()).condition(12)
    paths = {
        item.artifact_kind: item.path for item in condition.required_evidence
    }
    supervisor_raw = core.read_blob_at(
        root, head, paths["workload_supervisor"]
    )
    allocation_raw = core.read_blob_at(
        root, head, paths["allocation_consumer"]
    )
    assert supervisor_raw is not None
    assert allocation_raw is not None

    supervisor = ast.parse(supervisor_raw)
    allocation = ast.parse(allocation_raw)
    assert {"read_binding", "check_reservation"} <= M._functions(allocation).keys()
    assert M._c12_allocation_binding_verdict(supervisor, allocation) == (
        core.PredicateStatus.UNSATISFIED,
        M.ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT,
    )


def test_evidence_undefined_is_never_satisfied() -> None:
    assert not M.is_satisfied(core.PredicateStatus.EVIDENCE_UNDEFINED)
    assert not M.is_satisfied(core.PredicateStatus.UNSATISFIED)
    assert not M.is_satisfied(core.PredicateStatus.ERROR)
    assert not M.is_satisfied(core.PredicateStatus.NOT_EVALUATED)
    assert M.is_satisfied(core.PredicateStatus.SATISFIED)


def test_missing_target_module_is_capability_probe_not_exception(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    head = _commit(root)
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "trial-registry-capability-absent"


def test_contract_semantic_hash_ignores_formatting_but_not_values() -> None:
    raw = CONTRACT_FILE.read_bytes()
    value = json.loads(raw)
    compact = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert M.semantic_contract_sha256(raw) == M.semantic_contract_sha256(compact)

    changed = json.loads(raw)
    changed["conditions"][0]["static_only_note"] += " Changed meaning."
    changed_raw = json.dumps(changed, ensure_ascii=False).encode("utf-8")
    assert M.semantic_contract_sha256(raw) != M.semantic_contract_sha256(changed_raw)


def test_contract_loader_rejects_unknown_and_duplicate_keys() -> None:
    raw = CONTRACT_FILE.read_bytes()
    value = json.loads(raw)
    value["unknown"] = True
    with pytest.raises(M.EvidenceContractError) as unknown:
        M.load_contract_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    assert unknown.value.reason_code == "contract-schema-keys"

    duplicate = raw.replace(
        b'{\n  "schema_version":',
        b'{\n  "schema_version":"duplicate",\n  "schema_version":',
        1,
    )
    with pytest.raises(M.EvidenceContractError) as repeated:
        M.load_contract_bytes(duplicate)
    assert repeated.value.reason_code == "contract-duplicate-key"


@pytest.mark.parametrize(
    ("owner", "control"),
    [
        pytest.param("required", "\r", id="required-cr"),
        pytest.param("required", "\n", id="required-lf"),
        pytest.param("required", "\x00", id="required-nul"),
        pytest.param("consumer", "\r", id="consumer-cr"),
        pytest.param("consumer", "\n", id="consumer-lf"),
        pytest.param("consumer", "\x00", id="consumer-nul"),
    ],
)
def test_contract_loader_rejects_embedded_path_control_chars(
    owner: str, control: str
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    candidate = f"dir/in{control}side.py"
    assert candidate == candidate.strip()
    if owner == "required":
        value["conditions"][0]["required_evidence"][0]["path"] = candidate
    else:
        value["conditions"][0]["consumer_requirement"]["path"] = candidate

    with pytest.raises(M.EvidenceContractError) as caught:
        M.load_contract_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    assert caught.value.reason_code == "contract-path-control-char"
    assert "\x00" not in str(caught.value)
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)


@pytest.mark.parametrize(
    "control",
    [
        pytest.param("\r", id="trailing-cr"),
        pytest.param("\n", id="trailing-lf"),
        pytest.param("\x00", id="trailing-nul"),
    ],
)
def test_contract_loader_reports_explicit_path_reason_for_trailing_controls(
    control: str,
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    current = value["conditions"][0]["required_evidence"][0]["path"]
    value["conditions"][0]["required_evidence"][0]["path"] = current + control

    with pytest.raises(M.EvidenceContractError) as caught:
        M.load_contract_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    assert caught.value.reason_code == "contract-path-control-char"
    assert "\x00" not in str(caught.value)
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)


def test_contract_loader_accepts_normal_relative_paths() -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    value["conditions"][0]["required_evidence"][0]["path"] = "nested/evidence.py"
    value["conditions"][0]["consumer_requirement"]["path"] = "nested/consumer.py"
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")

    contract = M.load_contract_bytes(raw)
    condition = contract.conditions[0]
    assert condition.required_evidence[0].path == "nested/evidence.py"
    assert condition.consumer_requirement.path == "nested/consumer.py"
    assert len(M.semantic_contract_sha256(raw)) == 64


def test_contract_loader_accepts_embedded_tab_path() -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    candidate = "nested/tab\tpath.py"
    value["conditions"][0]["required_evidence"][0]["path"] = candidate
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")

    contract = M.load_contract_bytes(raw)
    assert contract.conditions[0].required_evidence[0].path == candidate


def test_safe_path_rejects_membership_spoofing_str_subclass() -> None:
    class MembershipSpoofingPath(str):
        def __contains__(self, item: object) -> bool:
            return False

    candidate = MembershipSpoofingPath("nested/in\rside.py")
    with pytest.raises(M.EvidenceContractError) as caught:
        M._safe_path(candidate, where="spoofed.path")
    assert caught.value.reason_code == "contract-path-control-char"


def test_safe_path_returns_exact_str_for_accepted_str_subclass() -> None:
    class AcceptedPath(str):
        pass

    candidate = AcceptedPath("nested/accepted.py")
    result = M._safe_path(candidate, where="accepted.path")
    assert type(result) is str
    assert result == candidate


def test_registry_rejects_control_char_contract_before_evidence_ref_construction(
    tmp_path: Path,
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    candidate = "dir/in\nside.py"
    assert candidate == candidate.strip()
    value["conditions"][0]["required_evidence"][0]["path"] = candidate
    root = _init_repo(tmp_path)
    _write(
        root,
        core.EVIDENCE_CONTRACT_PATH,
        json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )
    head = _commit(root, "control character contract")

    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert len(results) == 12
    assert {item.status for item in results} == {core.PredicateStatus.ERROR}
    assert {item.reason_code for item in results} == {"evidence-contract-invalid"}
    assert {
        tuple(reference.path for reference in item.evidence) for item in results
    } == {(core.EVIDENCE_CONTRACT_PATH,)}


def test_contract_does_not_add_a_holdout_axis_conjunction() -> None:
    text = CONTRACT_FILE.read_text(encoding="utf-8")
    hits = s8b_holdout_freeze.holdout_conjunction_hits(
        {core.EVIDENCE_CONTRACT_PATH: text}
    )
    assert set(hits) == set(s8b_holdout_freeze.HOLDOUTS)
    assert all(paths == [] for paths in hits.values())


def test_contract_declares_exact_terminal_definition_path_universe() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    assert len(contract.evidence_paths) == 14
    assert {
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/execution_guard.py",
        "orchestrator/campaign/reservation.py",
        "orchestrator/campaign/s8b_ratified_freeze.py",
        "orchestrator/campaign/trial_registry.py",
        "orchestrator/campaign/autonomous_trial_completeness.py",
    } <= contract.evidence_paths


TOKEN_ONLY_C01 = """
from .s8b_ratified_freeze import load_ratified_freeze
def _campaign_for(*, holdout, ratified_sha256):
    return {"records": 1_000_000, "threads": 48}
def _perf_for(*, holdout, ratified_sha256):
    return {"records": 1_000_000, "threads": 48}
def _descriptor_for(*, holdout, ratified_sha256):
    return {"records": 1_000_000, "threads": 48}
def _run_workload():
    ratified = load_ratified_freeze()
    holdout = ratified.holdouts
    return (
        _campaign_for(holdout=holdout, ratified_sha256=ratified.sha256),
        _perf_for(holdout=holdout, ratified_sha256=ratified.sha256),
        _descriptor_for(holdout=holdout, ratified_sha256=ratified.sha256),
    )
def run_trial():
    return _run_workload()
def main():
    return run_trial()
"""

TOKEN_ONLY_C02_REGISTRY = """
def assert_issued_trial_binding(): pass
def resolve_arm_input(): pass
def assert_issued_resolved_arm_input(): pass
def validate_execution_input_descriptor(): pass
def assert_execution_digest_chain(): pass
def bind_trial_arm():
    assert_issued_trial_binding()
    resolve_arm_input()
def assert_issued_trial_arm_execution():
    assert_issued_trial_binding()
    assert_issued_resolved_arm_input()
def assert_rederived_trial_arm_execution():
    assert_issued_trial_arm_execution()
    bind_trial_arm()
def _expected_registered_arm_execution_record():
    resolve_arm_input()
    return {
        "input_schema_version": "v1",
        "content_digest_sha256": "a" * 64,
        "arm_binding_digest_sha256": "b" * 64,
    }
def assert_trial_registry_acceptance():
    arm_execution = {"arm_execution": _expected_registered_arm_execution_record()}
    validate_execution_input_descriptor()
    assert_execution_digest_chain()
    return arm_execution
"""

TOKEN_ONLY_C02_PRODUCER = """
def _invocation_namespace(*, arm, digest):
    return f"arm-{arm}.exec-{digest}"
def _invocation_id(*, arm, digest):
    return _invocation_namespace(arm=arm, digest=digest)
def _run_workload(*, arm, digest):
    return _invocation_namespace(arm=arm, digest=digest)
def run_trial(*, arm, digest):
    return _invocation_namespace(arm=arm, digest=digest)
"""

TOKEN_ONLY_C04 = """
from .trial_registry import forbid_trial_restart
def launch_cells(): pass
def mark_experiment_indeterminate(): pass
def run_trial():
    try:
        launch_cells()
    except Exception:
        mark_experiment_indeterminate()
        forbid_trial_restart()
def main():
    return run_trial()
"""

TOKEN_ONLY_C09_PRODUCER = """
from .autonomous_trial_completeness import assert_campaign_layer3_chain
def run_trial():
    assert_campaign_layer3_chain()
def main():
    return run_trial()
"""

TOKEN_ONLY_C09_REGISTRY = """
from .autonomous_trial_completeness import assert_campaign_layer3_chain
def assert_trial_registry_acceptance():
    policy = {"no-build": False, "certifying": False}
    assert_campaign_layer3_chain()
    return policy
"""

TOKEN_ONLY_C10 = """
def read_and_verify_bytes(): pass
def verify_s8c_cross_binding():
    fields = (
        "input_payload_sha256", "raw_response_path", "raw_response_sha256",
        "provider_payload_sha256", "provider_envelope_sha256", "proposal_path",
        "proposal_sha256", "build_records", "bench_records", "artifact_refs",
        "source_refs", "admission_decision",
    )
    read_and_verify_bytes()
    return fields
"""

TOKEN_ONLY_C10_REGISTRY = """
def verify_s8c_cross_binding(): pass
def assert_trial_registry_acceptance():
    return verify_s8c_cross_binding()
"""

TOKEN_ONLY_C11 = """
MAX_APPROVED_GENERATIONS = 2
def _validate_generation_budget(): pass
def apply_critic_feedback(): pass
def _run_workload():
    _validate_generation_budget()
    apply_critic_feedback()
def run_trial():
    _validate_generation_budget()
    return _run_workload()
def main():
    _validate_generation_budget()
    return run_trial()
"""

TOKEN_ONLY_C11_PROJECTION = """
_CRITIC_KEYS = frozenset()
_DIAGNOSTIC_METRICS = ()
def apply_critic_feedback(): pass
def _validate_critic_projection(): pass
def validate_planner_payload(): pass
"""

TOKEN_ONLY_C12 = """
from . import env_contract, execution_guard
environ = {}
def run_trial():
    contract = env_contract.lookup()
    execution_guard.attest_and_build_receipt(contract)
    binding = read_binding(environ)
    check_reservation(
        binding,
        required_s=1,
        safety_margin_s=0,
        environ=environ,
    )
    return binding
def main():
    return run_trial()
"""


def test_c12_allocation_binding_helper_rejects_check_without_read_binding() -> None:
    reservation = "orchestrator/campaign/reservation.py"
    baseline = TOKEN_ONLY_C12.encode("utf-8")
    read_binding_call = b"    binding = read_binding(environ)"
    assert baseline.count(read_binding_call) == 1
    without_read_binding = baseline.replace(
        read_binding_call,
        b"    binding = object()",
    )
    assert without_read_binding != baseline

    supervisor = ast.parse(without_read_binding)
    calls = M._reachable_calls(supervisor, "run_trial")
    assert "check_reservation" in calls
    assert "read_binding" not in calls
    allocation = ast.parse(_git(_ROOT, "show", f"HEAD:{reservation}"))
    assert M._c12_allocation_binding_verdict(supervisor, allocation) == (
        core.PredicateStatus.UNSATISFIED,
        M.ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT,
    )


def test_c12_allocation_binding_gate_precedes_environment_gate(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        "def run_trial(): return None\n",
    )
    reservation = "orchestrator/campaign/reservation.py"
    _write(root, reservation, _git(_ROOT, "show", f"HEAD:{reservation}"))
    head = _commit(root, "C12 allocation and environment consumers both absent")

    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "allocation-enforcement-consumer-absent"


def test_current_repository_c12_allocation_binding_helper_accepts_both_calls_overlay(
) -> None:
    condition = M.load_contract_bytes(CONTRACT_FILE.read_bytes()).condition(12)
    paths = {
        item.artifact_kind: item.path for item in condition.required_evidence
    }
    supervisor_raw = _git(
        _ROOT,
        "show",
        f"HEAD:{paths['workload_supervisor']}",
    )
    allocation_raw = _git(
        _ROOT,
        "show",
        f"HEAD:{paths['allocation_consumer']}",
    )
    anchor = b"""    if drive is _DRIVE_NOT_PROVIDED:
        drive = trigger.drive_iteration
    if preview is _PREVIEW_NOT_PROVIDED:
        preview = _preview
    _validate_generation_budget(generations)
"""
    injection = anchor + b"""    from .reservation import check_reservation, read_binding
    allocation_binding = read_binding(os.environ)
    check_reservation(
        allocation_binding,
        required_s=max_wall_s,
        safety_margin_s=0,
        environ=os.environ,
    )
"""
    assert supervisor_raw.count(anchor) == 1
    overlay_raw = supervisor_raw.replace(anchor, injection)
    assert overlay_raw != supervisor_raw

    baseline_calls = M._reachable_calls(ast.parse(supervisor_raw), "run_trial")
    assert {"read_binding", "check_reservation"}.isdisjoint(baseline_calls)
    overlay = ast.parse(overlay_raw)
    assert {"read_binding", "check_reservation"} <= M._reachable_calls(
        overlay,
        "run_trial",
    )
    allocation = ast.parse(allocation_raw)
    assert M._c12_allocation_binding_verdict(overlay, allocation) is None


def _negative_control_case(
    identifier: str,
) -> tuple[dict[str, bytes | str], str, bytes | str]:
    p3 = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    registry = "orchestrator/campaign/trial_registry.py"
    if identifier == "nc_c01_perf_scale_regression":
        sources = {
            p3: TOKEN_ONLY_C01,
            "orchestrator/campaign/s8b_ratified_freeze.py":
                "def load_ratified_freeze(): pass\n",
        }
        return sources, p3, TOKEN_ONLY_C01.replace(
            'def _perf_for(*, holdout, ratified_sha256):\n    return {"records": 1_000_000',
            'def _perf_for(*, holdout, ratified_sha256):\n    return {"records": 100_000',
        )
    if identifier == "nc_c02_proposal_path_arm_collision":
        sources = {
            registry: TOKEN_ONLY_C02_REGISTRY,
            p3: TOKEN_ONLY_C02_PRODUCER,
        }
        namespace_token = 'f"arm-{arm}.exec-{digest}"'
        collision_token = '"arm-shared.exec-shared"'
        assert TOKEN_ONLY_C02_PRODUCER.count(namespace_token) == 1
        mutated = TOKEN_ONLY_C02_PRODUCER.replace(
            namespace_token, collision_token, 1
        )
        assert mutated.count(collision_token) == 1
        return sources, p3, mutated
    if identifier == "nc_c04_partial_crash_survives":
        sources = {p3: TOKEN_ONLY_C04, registry: "def forbid_trial_restart(): pass\n"}
        return sources, p3, TOKEN_ONLY_C04.replace(
            "        mark_experiment_indeterminate()",
            "        keep_completed_cells_certifying()",
            1,
        )
    if identifier == "nc_c09_acceptance_skips_layer3":
        sources = {
            p3: TOKEN_ONLY_C09_PRODUCER,
            registry: TOKEN_ONLY_C09_REGISTRY,
            "orchestrator/campaign/autonomous_trial_completeness.py":
                "def assert_campaign_layer3_chain(): pass\n",
        }
        return sources, registry, TOKEN_ONLY_C09_REGISTRY.replace(
            "    assert_campaign_layer3_chain()\n", "", 1
        )
    if identifier == "nc_c10_raw_response_unbound":
        verifier = "orchestrator/campaign/autonomous_trial_completeness.py"
        sources = {verifier: TOKEN_ONLY_C10, registry: TOKEN_ONLY_C10_REGISTRY}
        return sources, verifier, TOKEN_ONLY_C10.replace(
            '"raw_response_sha256"', '"raw_response_digest"', 1
        )
    if identifier == "nc_c11_generation_cap_reverts_to_one":
        sources = {
            p3: TOKEN_ONLY_C11,
            "orchestrator/campaign/s8c_generation_projection.py":
                TOKEN_ONLY_C11_PROJECTION,
        }
        return sources, p3, TOKEN_ONLY_C11.replace("MAX_APPROVED_GENERATIONS = 2", "MAX_APPROVED_GENERATIONS = 1")
    if identifier == "nc_c12_reservation_check_bypassed":
        reservation = "orchestrator/campaign/reservation.py"
        baseline = TOKEN_ONLY_C12.encode("utf-8")
        reservation_check = b"""    check_reservation(
        binding,
        required_s=1,
        safety_margin_s=0,
        environ=environ,
    )"""
        bypass = b"    is_reservation_required(contract.isolation_policy)"
        assert baseline.count(reservation_check) == 1
        mutated = baseline.replace(reservation_check, bypass)
        assert mutated != baseline
        sources = {
            p3: TOKEN_ONLY_C12,
            "orchestrator/campaign/env_contract.py": "def lookup(): pass\n",
            "orchestrator/campaign/execution_guard.py":
                "def attest_and_build_receipt(): pass\n",
            reservation: _git(_ROOT, "show", f"HEAD:{reservation}"),
        }
        return sources, p3, mutated
    raise AssertionError(identifier)


NEGATIVE_CONTROL_CASES = {
    "nc_c01_perf_scale_regression": "C01",
    "nc_c02_proposal_path_arm_collision": "C02",
    "nc_c04_partial_crash_survives": "C04",
    "nc_c09_acceptance_skips_layer3": "C09",
    "nc_c10_raw_response_unbound": "C10",
    "nc_c11_generation_cap_reverts_to_one": "C11",
    "nc_c12_reservation_check_bypassed": "C12",
}


def test_c02_negative_control_collides_two_arms_by_one_namespace_token() -> None:
    _, mutated_path, mutated_source = _negative_control_case(
        "nc_c02_proposal_path_arm_collision"
    )
    assert mutated_path == "orchestrator/campaign/p3_autonomous_workload_trial.py"
    assert isinstance(mutated_source, str)
    baseline_scope: dict[str, object] = {}
    mutated_scope: dict[str, object] = {}
    exec(TOKEN_ONLY_C02_PRODUCER, baseline_scope)
    exec(mutated_source, mutated_scope)
    baseline_namespace = baseline_scope["_invocation_namespace"]
    mutated_namespace = mutated_scope["_invocation_namespace"]
    assert callable(baseline_namespace)
    assert callable(mutated_namespace)
    first = {"arm": "on", "digest": "a" * 64}
    second = {"arm": "off", "digest": "b" * 64}
    assert baseline_namespace(**first) != baseline_namespace(**second)
    assert mutated_namespace(**first) == mutated_namespace(**second)


def _terminal_result(
    tmp_path: Path, name: str, identifier: str, sources: dict[str, str]
) -> tuple[Path, str, core.PredicateResult]:
    root = _init_repo(tmp_path, name)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, name)
    result = _result(root, head, identifier)
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "completion-proof-not-machine-checkable"
    return root, head, result


def _c12_modules(supervisor: str) -> dict[str, str]:
    return {
        "orchestrator/campaign/p3_autonomous_workload_trial.py": supervisor,
        "orchestrator/campaign/env_contract.py": "def lookup(): pass\n",
        "orchestrator/campaign/execution_guard.py":
            "def attest_and_build_receipt(*args): pass\n",
        "orchestrator/campaign/reservation.py":
            "def read_binding(*args): return object()\n"
            "def check_reservation(*args, **kwargs): pass\n",
    }


@pytest.mark.parametrize(
    "imports_and_calls",
    [
        pytest.param(
            "from . import env_contract, execution_guard\n"
            "ENV = env_contract.lookup\nGUARD = execution_guard.attest_and_build_receipt\n",
            id="multi-name-from-package",
        ),
        pytest.param(
            "from .env_contract import lookup\n"
            "from .execution_guard import attest_and_build_receipt\n"
            "ENV = lookup\nGUARD = attest_and_build_receipt\n",
            id="from-symbol",
        ),
        pytest.param(
            "from .env_contract import lookup as ENV\n"
            "from .execution_guard import attest_and_build_receipt as GUARD\n",
            id="from-symbol-as",
        ),
        pytest.param(
            "import orchestrator.campaign.env_contract as e\n"
            "import orchestrator.campaign.execution_guard as g\n"
            "ENV = e.lookup\nGUARD = g.attest_and_build_receipt\n",
            id="absolute-import-as",
        ),
        pytest.param(
            "import orchestrator.campaign.env_contract\n"
            "import orchestrator.campaign.execution_guard\n"
            "ENV = orchestrator.campaign.env_contract.lookup\n"
            "GUARD = orchestrator.campaign.execution_guard.attest_and_build_receipt\n",
            id="absolute-import",
        ),
    ],
)
def test_cross_module_import_forms_resolve_exact_bound_target(
    tmp_path: Path, imports_and_calls: str
) -> None:
    supervisor = imports_and_calls + """
environ = {}
def run_trial():
    contract = ENV()
    GUARD(contract)
    binding = read_binding(environ)
    check_reservation(binding, required_s=1, safety_margin_s=0, environ=environ)
    return binding
def main(): return run_trial()
"""
    _, _, result = _terminal_result(
        tmp_path, "import-form", "C12", _c12_modules(supervisor)
    )
    paths = {reference.path for reference in result.evidence}
    assert {
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/execution_guard.py",
        "orchestrator/campaign/reservation.py",
    } <= paths


VALUE_FLOW_C12 = """
from . import env_contract, reservation, trigger
SENTINEL = object()
environ = {}
def relay(*, drive, contract, origin_runtime=None):
    drive(contract)
    return contract
def run_trial(drive=SENTINEL):
    if drive is SENTINEL:
        drive = trigger.drive_iteration
    contract = env_contract.lookup()
    binding = reservation.read_binding(environ)
    reservation.check_reservation(
        binding, required_s=1, safety_margin_s=0, environ=environ
    )
    return relay(drive=drive, contract=contract)
def main():
    return run_trial()
"""

VALUE_FLOW_TRIGGER = """
from . import execution_guard
def drive_iteration(contract):
    execution_guard.attest_and_build_receipt(contract)
"""


def _value_flow_sources(supervisor: str = VALUE_FLOW_C12) -> dict[str, str]:
    sources = _c12_modules(supervisor)
    sources["orchestrator/campaign/trigger.py"] = VALUE_FLOW_TRIGGER
    return sources


def test_local_single_assignment_and_keyword_value_flow_is_witness(
    tmp_path: Path,
) -> None:
    _terminal_result(tmp_path, "value-flow", "C12", _value_flow_sources())


DICT_CARRIER_C12 = VALUE_FLOW_C12.replace(
    "    return relay(drive=drive, contract=contract)",
    "    arguments = dict(drive=drive, contract=contract)\n"
    "    arguments[\"origin_runtime\"] = None\n"
    "    return relay(**arguments)",
)


def test_single_assignment_dict_carrier_with_unrelated_literal_update_is_witness(
    tmp_path: Path,
) -> None:
    _terminal_result(
        tmp_path, "dict-carrier", "C12", _value_flow_sources(DICT_CARRIER_C12)
    )


@pytest.mark.parametrize(
    ("name", "source"),
    [
        pytest.param(
            "target-key-subscript",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'arguments["drive"] = custom_drive',
            ).replace(
                "def run_trial(drive=SENTINEL):",
                "def custom_drive(*args): return None\n"
                "def run_trial(drive=SENTINEL):",
            ),
            id="target-key-subscript",
        ),
        pytest.param(
            "nonliteral-subscript",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'arguments[unknown_key] = None',
            ),
            id="nonliteral-subscript",
        ),
        pytest.param(
            "update",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'arguments.update({"drive": custom_drive})',
            ).replace(
                "def run_trial(drive=SENTINEL):",
                "def custom_drive(*args): return None\n"
                "def run_trial(drive=SENTINEL):",
            ),
            id="update",
        ),
        pytest.param(
            "pop",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'arguments.pop("drive")',
            ),
            id="pop",
        ),
        pytest.param(
            "delete",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'del arguments["drive"]',
            ),
            id="delete",
        ),
        pytest.param(
            "ior",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'arguments |= {"drive": custom_drive}',
            ).replace(
                "def run_trial(drive=SENTINEL):",
                "def custom_drive(*args): return None\n"
                "def run_trial(drive=SENTINEL):",
            ),
            id="ior",
        ),
        pytest.param(
            "literal-splat",
            VALUE_FLOW_C12.replace(
                "return relay(drive=drive, contract=contract)",
                'return relay(**{"drive": drive, "contract": contract})',
            ),
            id="literal-splat",
        ),
        pytest.param(
            "dict-positional-input",
            DICT_CARRIER_C12.replace(
                "dict(drive=drive, contract=contract)",
                'dict({"drive": drive}, contract=contract)',
            ),
            id="dict-positional-input",
        ),
        pytest.param(
            "dict-keyword-merge",
            DICT_CARRIER_C12.replace(
                "dict(drive=drive, contract=contract)",
                'dict(**{"drive": drive}, contract=contract)',
            ),
            id="dict-keyword-merge",
        ),
        pytest.param(
            "dict-literal-carrier",
            DICT_CARRIER_C12.replace(
                "dict(drive=drive, contract=contract)",
                '{"drive": drive, "contract": contract}',
            ),
            id="dict-literal-carrier",
        ),
        pytest.param(
            "expression-splat",
            DICT_CARRIER_C12.replace(
                "return relay(**arguments)", "return relay(**arguments.copy())"
            ),
            id="expression-splat",
        ),
        pytest.param(
            "carrier-rebound",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'arguments = dict(drive=custom_drive, contract=contract)',
            ).replace(
                "def run_trial(drive=SENTINEL):",
                "def custom_drive(*args): return None\n"
                "def run_trial(drive=SENTINEL):",
            ),
            id="carrier-rebound",
        ),
        pytest.param(
            "carrier-alias-mutation",
            DICT_CARRIER_C12.replace(
                'arguments["origin_runtime"] = None',
                'alias = arguments\n    alias["drive"] = custom_drive',
            ).replace(
                "def run_trial(drive=SENTINEL):",
                "def custom_drive(*args): return None\n"
                "def run_trial(drive=SENTINEL):",
            ),
            id="carrier-alias-mutation",
        ),
        pytest.param(
            "carrier-splatted-twice",
            DICT_CARRIER_C12.replace(
                "    return relay(**arguments)",
                "    relay(**arguments)\n    return relay(**arguments)",
            ),
            id="carrier-splatted-twice",
        ),
    ],
)
def test_unsafe_dict_carriers_block_the_target_parameter(
    tmp_path: Path, name: str, source: str
) -> None:
    root = _init_repo(tmp_path, name)
    for path, raw in _value_flow_sources(source).items():
        _write(root, path, raw)
    head = _commit(root, name)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "environment-contract-consumer-absent"


@pytest.mark.parametrize(
    ("mutation", "source"),
    [
        pytest.param(
            "caller-override",
            VALUE_FLOW_C12.replace(
                "def main():\n    return run_trial()",
                "def custom_drive(): return None\ndef main():\n    return run_trial(drive=custom_drive)",
            ),
            id="caller-override",
        ),
        pytest.param(
            "caller-positional-override",
            VALUE_FLOW_C12.replace(
                "def main():\n    return run_trial()",
                "def custom_drive(*args): return None\n"
                "def main():\n    return run_trial(custom_drive)",
            ),
            id="caller-positional-override",
        ),
        pytest.param(
            "sentinel-resolution-removed",
            VALUE_FLOW_C12.replace("        drive = trigger.drive_iteration", "        pass"),
            id="sentinel-resolution-removed",
        ),
        pytest.param(
            "callable-default",
            VALUE_FLOW_C12.replace(
                "def run_trial(drive=SENTINEL):\n"
                "    if drive is SENTINEL:\n"
                "        drive = trigger.drive_iteration\n",
                "def run_trial(drive=trigger.drive_iteration):\n",
            ),
            id="callable-default-is-not-witness",
        ),
        pytest.param(
            "multiple-assignment",
            VALUE_FLOW_C12.replace(
                "        drive = trigger.drive_iteration",
                "        drive = trigger.drive_iteration\n"
                "    drive = trigger.drive_iteration",
            ),
            id="multiple-assignment",
        ),
        pytest.param(
            "positional-only-propagation",
            VALUE_FLOW_C12.replace(
                "return relay(drive=drive, contract=contract)",
                "return relay(drive, contract=contract)",
            ),
            id="positional-only-is-not-propagated",
        ),
        pytest.param(
            "star-args",
            VALUE_FLOW_C12.replace(
                "return relay(drive=drive, contract=contract)",
                "return relay(*unknown_args, drive=drive, contract=contract)",
            ),
            id="star-args-blocks-all-target-parameters",
        ),
        pytest.param(
            "conditional-local-assignment",
            VALUE_FLOW_C12.replace(
                "if drive is SENTINEL:\n        drive = trigger.drive_iteration",
                "if unknown_condition:\n        drive = trigger.drive_iteration",
            ),
            id="conditional-local-assignment",
        ),
        pytest.param(
            "use-before-assignment",
            VALUE_FLOW_C12.replace(
                "    return relay(drive=drive, contract=contract)",
                "    result = relay(drive=drive, contract=contract)\n"
                "    drive = trigger.drive_iteration\n"
                "    return result",
            ).replace(
                "    if drive is SENTINEL:\n"
                "        drive = trigger.drive_iteration\n",
                "",
            ).replace(
                "def run_trial(drive=SENTINEL):", "def run_trial():"
            ),
            id="use-before-assignment",
        ),
        pytest.param(
            "sentinel-assignment-in-else",
            VALUE_FLOW_C12.replace(
                "if drive is SENTINEL:\n        drive = trigger.drive_iteration",
                "if drive is SENTINEL:\n        pass\n"
                "    else:\n        drive = trigger.drive_iteration",
            ),
            id="sentinel-assignment-in-else",
        ),
        pytest.param(
            "sentinel-assignment-nested",
            VALUE_FLOW_C12.replace(
                "if drive is SENTINEL:\n        drive = trigger.drive_iteration",
                "if drive is SENTINEL:\n"
                "        if unknown_condition:\n"
                "            drive = trigger.drive_iteration",
            ),
            id="sentinel-assignment-nested",
        ),
    ],
)
def test_callable_value_flow_failures_stay_environment_absent(
    tmp_path: Path, mutation: str, source: str
) -> None:
    assert source != VALUE_FLOW_C12, mutation
    if mutation == "multiple-assignment":
        assert source.count("drive = trigger.drive_iteration") == 2
    root = _init_repo(tmp_path)
    for path, raw in _value_flow_sources(source).items():
        _write(root, path, raw)
    head = _commit(root)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "environment-contract-consumer-absent"


@pytest.mark.parametrize("absence", ["missing-definition", "unimported-same-name"])
def test_c12_allocation_target_requires_exact_imported_definition(
    tmp_path: Path, absence: str
) -> None:
    sources = _c12_modules(TOKEN_ONLY_C12)
    root, _, _ = _terminal_result(tmp_path, "exact-target", "C12", sources)
    reservation = "orchestrator/campaign/reservation.py"
    if absence == "missing-definition":
        _write(root, reservation, "def read_binding(*args): return object()\n")
    else:
        _write(root, reservation, "def read_binding(*args): return object()\n")
        _write(
            root,
            "orchestrator/campaign/unimported_decoy.py",
            "def check_reservation(*args, **kwargs): pass\n",
        )
    head = _commit(root, absence)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "allocation-enforcement-consumer-absent"


@pytest.mark.parametrize(
    ("absence", "supervisor"),
    [
        pytest.param(
            "read-binding-call-edge",
            TOKEN_ONLY_C12.replace(
                "    binding = read_binding(environ)",
                "    binding = object()",
            ),
            id="read-binding-call-edge",
        ),
        pytest.param(
            "check-reservation-call-edge",
            TOKEN_ONLY_C12.replace(
                "    check_reservation(\n"
                "        binding,\n"
                "        required_s=1,\n"
                "        safety_margin_s=0,\n"
                "        environ=environ,\n"
                "    )",
                "    is_reservation_required(binding)",
            ),
            id="check-reservation-call-edge",
        ),
        pytest.param(
            "unreachable-check-reservation",
            TOKEN_ONLY_C12.replace(
                "    check_reservation(\n"
                "        binding,\n"
                "        required_s=1,\n"
                "        safety_margin_s=0,\n"
                "        environ=environ,\n"
                "    )",
                "    return binding\n"
                "def never_called():\n"
                "    check_reservation(\n"
                "        None, required_s=1, safety_margin_s=0, environ=environ\n"
                "    )",
            ),
            id="unreachable-check-reservation",
        ),
    ],
)
def test_c12_allocation_absence_shapes_are_independent_from_definition(
    tmp_path: Path, absence: str, supervisor: str
) -> None:
    removed = {
        "read-binding-call-edge": "    binding = read_binding(environ)",
        "check-reservation-call-edge": "    check_reservation(\n",
        "unreachable-check-reservation": "    check_reservation(\n",
    }[absence]
    assert TOKEN_ONLY_C12.count(removed) == 1
    assert supervisor != TOKEN_ONLY_C12, absence
    sources = _c12_modules(TOKEN_ONLY_C12)
    root, _, _ = _terminal_result(tmp_path, "allocation-baseline", "C12", sources)
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        supervisor,
    )
    head = _commit(root, absence)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "allocation-enforcement-consumer-absent"


@pytest.mark.parametrize(
    ("identifier", "mutation", "expected"),
    [
        pytest.param("C01", "ratified = load_ratified_freeze()", "ratified-generation-reference-absent", id="C01"),
        pytest.param("C02", "assert_execution_digest_chain()", "arm-binding-consumer-unreachable", id="C02"),
        pytest.param("C04", "mark_experiment_indeterminate()", "crash-policy-cell-partial", id="C04"),
        pytest.param("C09", "assert_campaign_layer3_chain()", "layer3-producer-unreachable", id="C09"),
        pytest.param("C12", "execution_guard.attest_and_build_receipt(contract)", "environment-contract-consumer-absent", id="C12"),
    ],
)
@pytest.mark.parametrize("absence", ["not-called", "constant-false", "nested"])
def test_reachable_consumers_reject_absence_shapes_with_single_reason(
    tmp_path: Path,
    identifier: str,
    mutation: str,
    expected: str,
    absence: str,
) -> None:
    control_id = next(key for key, value in NEGATIVE_CONTROL_CASES.items() if value == identifier)
    sources, _, _ = _negative_control_case(control_id)
    _terminal_result(tmp_path, "baseline", identifier, sources)
    owner = next(path for path, source in sources.items() if mutation in source)
    source = sources[owner]
    old_line = next(line for line in source.splitlines() if line.strip() == mutation)
    indent = old_line[: len(old_line) - len(old_line.lstrip())]
    if absence == "not-called":
        replacement = indent + "pass"
    elif absence == "constant-false":
        replacement = indent + "if False:\n" + indent + "    " + mutation
    else:
        replacement = indent + "def never_called():\n" + indent + "    " + mutation
    _write(tmp_path / "baseline", owner, source.replace(old_line, replacement, 1))
    head = _commit(tmp_path / "baseline", absence)
    result = _result(tmp_path / "baseline", head, identifier)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == expected


def test_c02_namespace_fstring_must_flow_to_return_value(tmp_path: Path) -> None:
    sources, _, _ = _negative_control_case(
        "nc_c02_proposal_path_arm_collision"
    )
    root, _, _ = _terminal_result(tmp_path, "baseline", "C02", sources)
    old = '    return f"arm-{arm}.exec-{digest}"'
    replacement = (
        '    f"arm-{arm}.exec-{digest}"\n'
        '    return "arm-shared.exec-shared"'
    )
    assert TOKEN_ONLY_C02_PRODUCER.count(old) == 1
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        TOKEN_ONLY_C02_PRODUCER.replace(old, replacement, 1),
    )
    head = _commit(root, "namespace f-string is unused")

    result = _result(root, head, "C02")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "arm-binding-consumer-unreachable"


def test_c02_call_after_literal_true_return_is_dead(tmp_path: Path) -> None:
    sources, _, _ = _negative_control_case(
        "nc_c02_proposal_path_arm_collision"
    )
    root, _, _ = _terminal_result(tmp_path, "baseline", "C02", sources)
    old = (
        "def bind_trial_arm():\n"
        "    assert_issued_trial_binding()\n"
        "    resolve_arm_input()\n"
    )
    replacement = (
        "def bind_trial_arm():\n"
        "    assert_issued_trial_binding()\n"
        "    if True:\n"
        "        return None\n"
        "    resolve_arm_input()\n"
    )
    assert TOKEN_ONLY_C02_REGISTRY.count(old) == 1
    _write(
        root,
        "orchestrator/campaign/trial_registry.py",
        TOKEN_ONLY_C02_REGISTRY.replace(old, replacement, 1),
    )
    head = _commit(root, "C02 call follows literal true return")

    result = _result(root, head, "C02")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "arm-binding-consumer-unreachable"


@pytest.mark.parametrize(
    ("dead_shape", "replacement"),
    [
        pytest.param(
            "if-true-else",
            "    if True:\n"
            "        pass\n"
            "    else:\n"
            "        assert_campaign_layer3_chain()\n",
            id="if-true-else",
        ),
        pytest.param(
            "while-false-body",
            "    while False:\n"
            "        assert_campaign_layer3_chain()\n",
            id="while-false-body",
        ),
        pytest.param(
            "after-return",
            "    return None\n"
            "    assert_campaign_layer3_chain()\n",
            id="after-return",
        ),
    ],
)
def test_c09_provably_dead_calls_are_not_reachability_witnesses(
    tmp_path: Path, dead_shape: str, replacement: str
) -> None:
    sources, _, _ = _negative_control_case("nc_c09_acceptance_skips_layer3")
    root, _, _ = _terminal_result(tmp_path, "dead-call-baseline", "C09", sources)
    producer_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    target = "    assert_campaign_layer3_chain()\n"
    producer = sources[producer_path]
    assert isinstance(producer, str)
    assert producer.count(target) == 1
    mutated = producer.replace(target, replacement, 1)
    assert mutated != producer, dead_shape
    _write(root, producer_path, mutated)
    head = _commit(root, dead_shape)
    result = _result(root, head, "C09")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "layer3-producer-unreachable"


def test_c09_unknown_branch_remains_a_potential_reachability_witness(
    tmp_path: Path,
) -> None:
    sources, _, _ = _negative_control_case("nc_c09_acceptance_skips_layer3")
    producer_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    target = "    assert_campaign_layer3_chain()\n"
    producer = sources[producer_path]
    assert isinstance(producer, str)
    assert producer.count(target) == 1
    replacement = (
        "    if unknown_condition:\n"
        "        pass\n"
        "    else:\n"
        "        assert_campaign_layer3_chain()\n"
    )
    mutated = producer.replace(target, replacement, 1)
    assert mutated != producer
    sources[producer_path] = mutated
    _terminal_result(tmp_path, "unknown-call-branch", "C09", sources)


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        pytest.param("C01", "workload-consumer-unreachable", id="C01"),
        pytest.param("C04", "crash-policy-cell-partial", id="C04"),
        pytest.param("C09", "layer3-producer-unreachable", id="C09"),
        pytest.param("C12", "environment-contract-consumer-absent", id="C12"),
    ],
)
def test_production_entrypoint_cut_is_rejected_for_all_reachability_conditions(
    tmp_path: Path, identifier: str, expected: str
) -> None:
    control_id = next(
        key for key, value in NEGATIVE_CONTROL_CASES.items() if value == identifier
    )
    sources, _, _ = _negative_control_case(control_id)
    root, _, _ = _terminal_result(tmp_path, "entrypoint-baseline", identifier, sources)
    owner = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    _write(
        root,
        owner,
        sources[owner].replace(
            "def main():\n    return run_trial()",
            "def main():\n    return None",
        ),
    )
    head = _commit(root, "entrypoint cut")
    result = _result(root, head, identifier)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == expected


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        pytest.param("C01", "ratified-generation-reference-absent", id="C01"),
        pytest.param("C04", "crash-policy-cell-partial", id="C04"),
        pytest.param("C09", "layer3-producer-unreachable", id="C09"),
        pytest.param("C12", "environment-contract-consumer-absent", id="C12"),
    ],
)
def test_test_only_target_is_rejected_for_all_reachability_conditions(
    tmp_path: Path, identifier: str, expected: str
) -> None:
    control_id = next(
        key for key, value in NEGATIVE_CONTROL_CASES.items() if value == identifier
    )
    sources, _, _ = _negative_control_case(control_id)
    owner = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    source = sources[owner]
    if identifier == "C01":
        source = source.replace(
            "from .s8b_ratified_freeze import load_ratified_freeze",
            "from orchestrator.tests.fake_target import load_ratified_freeze",
        )
        decoy = "def load_ratified_freeze(): pass\n"
    elif identifier == "C04":
        source = source.replace(
            "from .trial_registry import forbid_trial_restart",
            "from orchestrator.tests.fake_target import forbid_trial_restart",
        )
        decoy = "def forbid_trial_restart(): pass\n"
    elif identifier == "C09":
        source = source.replace(
            "from .autonomous_trial_completeness import assert_campaign_layer3_chain",
            "from orchestrator.tests.fake_target import assert_campaign_layer3_chain",
        )
        decoy = "def assert_campaign_layer3_chain(): pass\n"
    else:
        source = source.replace(
            "from . import env_contract, execution_guard",
            "from . import env_contract\n"
            "from orchestrator.tests import fake_target as execution_guard",
        )
        decoy = "def attest_and_build_receipt(*args): pass\n"
    sources[owner] = source
    sources["orchestrator/tests/fake_target.py"] = decoy
    root = _init_repo(tmp_path, f"{identifier}-test-only")
    for path, raw in sources.items():
        _write(root, path, raw)
    head = _commit(root, "test-only target")
    result = _result(root, head, identifier)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == expected


@pytest.mark.parametrize(
    ("identifier", "target_call", "decoy", "expected"),
    [
        pytest.param(
            "C01", "ratified = load_ratified_freeze()",
            "def load_ratified_freeze(): pass\n",
            "ratified-generation-reference-absent", id="C01",
        ),
        pytest.param(
            "C04", "forbid_trial_restart()", "def forbid_trial_restart(): pass\n",
            "crash-policy-cell-partial", id="C04",
        ),
        pytest.param(
            "C09", "assert_campaign_layer3_chain()",
            "def assert_campaign_layer3_chain(): pass\n",
            "layer3-producer-unreachable", id="C09",
        ),
        pytest.param(
            "C12", "execution_guard.attest_and_build_receipt(contract)",
            "def attest_and_build_receipt(*args): pass\n",
            "environment-contract-consumer-absent", id="C12",
        ),
    ],
)
def test_unimported_same_name_decoy_is_rejected_for_all_reachability_conditions(
    tmp_path: Path,
    identifier: str,
    target_call: str,
    decoy: str,
    expected: str,
) -> None:
    control_id = next(
        key for key, value in NEGATIVE_CONTROL_CASES.items() if value == identifier
    )
    sources, _, _ = _negative_control_case(control_id)
    root, _, _ = _terminal_result(tmp_path, "decoy-baseline", identifier, sources)
    owner = next(path for path, source in sources.items() if target_call in source)
    _write(root, owner, sources[owner].replace(target_call, "pass", 1))
    _write(root, "orchestrator/campaign/unimported_decoy.py", decoy)
    head = _commit(root, "unimported same-name decoy")
    result = _result(root, head, identifier)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == expected


ABSENCE_MATRIX_EXCLUSIONS = {
    "caller-override": {
        "C01": "callable parameter relay が契約経路に無い",
        "C04": "callable parameter relay が契約経路に無い",
        "C09": "callable parameter relay が契約経路に無い",
    },
    "package-module-shadow": {
        "C01": "from submodule import symbol で package 属性を参照しない",
        "C04": "from submodule import symbol で package 属性を参照しない",
        "C09": "from submodule import symbol で package 属性を参照しない",
    },
}


def test_absence_matrix_exclusions_are_explicit_and_limited() -> None:
    assert set(ABSENCE_MATRIX_EXCLUSIONS) == {
        "caller-override", "package-module-shadow"
    }
    assert all(
        set(rows) == {"C01", "C04", "C09"}
        and all(reason for reason in rows.values())
        for rows in ABSENCE_MATRIX_EXCLUSIONS.values()
    )


@pytest.mark.parametrize(
    ("name", "supervisor", "extra"),
    [
        pytest.param(
            "entrypoint-cut",
            TOKEN_ONLY_C12.replace("def main():\n    return run_trial()", "def main():\n    return None"),
            {},
            id="production-entrypoint-cut",
        ),
        pytest.param(
            "package-shadow",
            TOKEN_ONLY_C12,
            {"orchestrator/campaign/__init__.py": "env_contract = None\n"},
            id="package-shadow",
        ),
        pytest.param(
            "package-shadow-if-true",
            TOKEN_ONLY_C12,
            {
                "orchestrator/campaign/__init__.py":
                    "if True:\n    env_contract = None\n"
            },
            id="package-shadow-if-true",
        ),
        pytest.param(
            "module-rebind",
            TOKEN_ONLY_C12.replace(
                "environ = {}", "env_contract = None\nenviron = {}"
            ),
            {},
            id="module-rebind",
        ),
        pytest.param(
            "local-shadow",
            TOKEN_ONLY_C12.replace(
                "def run_trial():", "def run_trial(env_contract=None):"
            ).replace("return run_trial()", "return run_trial(env_contract=None)"),
            {},
            id="local-shadow",
        ),
        pytest.param(
            "test-only",
            TOKEN_ONLY_C12.replace(
                "from . import env_contract, execution_guard",
                "from . import env_contract\n"
                "from orchestrator.tests import fake_guard as execution_guard",
            ),
            {"orchestrator/tests/fake_guard.py": "def attest_and_build_receipt(*args): pass\n"},
            id="test-only-module",
        ),
    ],
)
def test_c12_rejects_shadow_entrypoint_and_test_only_paths(
    tmp_path: Path, name: str, supervisor: str, extra: dict[str, str]
) -> None:
    sources = _c12_modules(supervisor)
    sources.update(extra)
    root = _init_repo(tmp_path)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, name)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "environment-contract-consumer-absent"
    if name.startswith("package-shadow"):
        assert "orchestrator/campaign/__init__.py" in {
            reference.path for reference in result.evidence
        }


@pytest.mark.parametrize(
    ("name", "binding", "extra"),
    [
        pytest.param(
            "local-import",
            "    from . import decoy as env_contract\n",
            {"orchestrator/campaign/decoy.py": "def lookup(): pass\n"},
            id="local-import",
        ),
        pytest.param(
            "for-target",
            "    for env_contract in ():\n        pass\n",
            {},
            id="for-target",
        ),
        pytest.param(
            "with-target",
            "    with unknown_manager as env_contract:\n        pass\n",
            {},
            id="with-target",
        ),
        pytest.param(
            "except-target",
            "    try:\n        pass\n"
            "    except Exception as env_contract:\n        pass\n",
            {},
            id="except-target",
        ),
        pytest.param(
            "walrus-target",
            "    if (env_contract := None) is not None:\n        pass\n",
            {},
            id="walrus-target",
        ),
        pytest.param(
            "global-declaration",
            "    global env_contract\n",
            {},
            id="global-declaration",
        ),
        pytest.param(
            "nonlocal-declaration",
            "    nonlocal env_contract\n",
            {},
            id="nonlocal-declaration",
        ),
    ],
)
def test_c12_rejects_conservative_local_binding_forms(
    tmp_path: Path, name: str, binding: str, extra: dict[str, str]
) -> None:
    supervisor = TOKEN_ONLY_C12.replace(
        "def run_trial():\n", "def run_trial():\n" + binding
    )
    sources = _c12_modules(supervisor)
    sources.update(extra)
    root = _init_repo(tmp_path, name)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, name)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "environment-contract-consumer-absent"


def test_c09_test_only_layer3_target_is_not_production_witness(
    tmp_path: Path,
) -> None:
    sources, _, _ = _negative_control_case("nc_c09_acceptance_skips_layer3")
    root, _, _ = _terminal_result(tmp_path, "c09-production", "C09", sources)
    producer_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    _write(
        root,
        producer_path,
        sources[producer_path].replace(
            "from .autonomous_trial_completeness import assert_campaign_layer3_chain",
            "from orchestrator.tests.fake_layer3 import assert_campaign_layer3_chain",
        ),
    )
    _write(
        root,
        "orchestrator/tests/fake_layer3.py",
        "def assert_campaign_layer3_chain(): pass\n",
    )
    head = _commit(root, "test-only layer3")
    result = _result(root, head, "C09")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "layer3-producer-unreachable"


def test_c09_same_name_target_in_undeclared_production_path_is_not_witness(
    tmp_path: Path,
) -> None:
    sources, _, _ = _negative_control_case("nc_c09_acceptance_skips_layer3")
    root, _, _ = _terminal_result(tmp_path, "c09-declared-owner", "C09", sources)
    producer_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    _write(
        root,
        producer_path,
        sources[producer_path].replace(
            "from .autonomous_trial_completeness import assert_campaign_layer3_chain",
            "from .production_decoy import assert_campaign_layer3_chain",
        ),
    )
    _write(
        root,
        "orchestrator/campaign/production_decoy.py",
        "def assert_campaign_layer3_chain(): pass\n",
    )
    head = _commit(root, "undeclared production decoy")
    result = _result(root, head, "C09")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "layer3-producer-unreachable"


def _walk_sources(
    tmp_path: Path,
    name: str,
    sources: dict[str, str],
    limits: M._ReachabilityLimits,
) -> M._Reachability:
    root = _init_repo(tmp_path, name)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, name)
    raw = core.read_blob_at(root, head, core.EVIDENCE_CONTRACT_PATH, required=True)
    contract = M.load_contract_bytes(raw).condition(12)
    probe = M._ConditionProbe(
        root,
        head,
        contract,
        core.EvidenceRef(core.EVIDENCE_CONTRACT_PATH, core._sha256(raw)),
        {},
        {},
    )
    return M._ReachabilityExplorer(probe, limits).walk(
        ("orchestrator/campaign/m0.py", "f0")
    )


def _chain_sources(length: int, *, padding: str = "") -> dict[str, str]:
    sources: dict[str, str] = {}
    for index in range(length):
        path = f"orchestrator/campaign/m{index}.py"
        if index + 1 == length:
            sources[path] = f"def f{index}(): pass\n{padding}"
        else:
            sources[path] = (
                f"from .m{index + 1} import f{index + 1}\n"
                f"def f{index}(): return f{index + 1}()\n"
            )
    return sources


def test_production_default_module_limit_accepts_sixty_five_modules(
    tmp_path: Path,
) -> None:
    assert M._MAX_REACHABILITY_MODULES == 512
    graph = _walk_sources(
        tmp_path,
        "production-default-65-modules",
        _chain_sources(65),
        M._ReachabilityLimits(),
    )
    assert len(graph.functions) == 65
    assert len(graph.modules) == 65


@pytest.mark.parametrize(
    ("dimension", "limits"),
    [
        pytest.param("modules", M._ReachabilityLimits(modules=2), id="modules"),
        pytest.param("depth", M._ReachabilityLimits(depth=1), id="depth"),
        pytest.param("states", M._ReachabilityLimits(states=2), id="states"),
    ],
)
def test_reachability_limits_accept_boundary_and_reject_boundary_plus_one(
    tmp_path: Path, dimension: str, limits: M._ReachabilityLimits
) -> None:
    graph = _walk_sources(tmp_path, f"{dimension}-exact", _chain_sources(2), limits)
    assert len(graph.functions) == 2
    with pytest.raises(M.EvidenceContractError) as caught:
        _walk_sources(tmp_path, f"{dimension}-plus-one", _chain_sources(3), limits)
    assert caught.value.reason_code == "reachability-limit-exceeded"


def test_reachability_byte_limit_accepts_boundary_and_rejects_next_byte(
    tmp_path: Path,
) -> None:
    sources = _chain_sources(2)
    exact = sum(len(source.encode("utf-8")) for source in sources.values())
    graph = _walk_sources(
        tmp_path,
        "bytes-exact",
        sources,
        M._ReachabilityLimits(total_bytes=exact),
    )
    assert len(graph.functions) == 2
    with pytest.raises(M.EvidenceContractError) as caught:
        _walk_sources(
            tmp_path,
            "bytes-plus-one",
            _chain_sources(2, padding="#"),
            M._ReachabilityLimits(total_bytes=exact),
        )
    assert caught.value.reason_code == "reachability-limit-exceeded"


def test_cross_module_cycle_terminates_on_canonical_callable_state(
    tmp_path: Path,
) -> None:
    graph = _walk_sources(
        tmp_path,
        "cycle",
        {
            "orchestrator/campaign/m0.py":
                "from .m1 import f1\ndef f0(): return f1()\n",
            "orchestrator/campaign/m1.py":
                "from .m0 import f0\ndef f1(): return f0()\n",
        },
        M._ReachabilityLimits(),
    )
    assert graph.functions == frozenset(
        {
            ("orchestrator/campaign/m0.py", "f0"),
            ("orchestrator/campaign/m1.py", "f1"),
        }
    )


def test_registry_preserves_reachability_limit_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sources, _, _ = _negative_control_case("nc_c04_partial_crash_survives")
    root = _init_repo(tmp_path)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root)

    def fail_limit(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise M.EvidenceContractError("reachability-limit-exceeded")

    monkeypatch.setattr(M._ReachabilityExplorer, "walk", fail_limit)
    result = _result(root, head, "C04")
    assert result.status is core.PredicateStatus.ERROR
    assert result.reason_code == "reachability-limit-exceeded"


def test_evaluate_all_shares_blob_ast_binding_and_root_graph_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _init_repo(tmp_path)
    for path, source in _c12_modules(TOKEN_ONLY_C12).items():
        _write(root, path, source)
    head = _commit(root, "shared evaluation caches")
    read_counts: dict[str, int] = {}
    resolve_calls = 0
    graph_cache_hits: list[bool] = []
    cache_identities: list[tuple[int, int, int, int, int]] = []
    original_read = M._read_blob_at_resolved
    original_resolve = core.resolve_commit
    original_walk = M._ReachabilityExplorer.walk

    def counted_resolve(repo_root: Path, commit: str = "HEAD") -> str:
        nonlocal resolve_calls
        resolve_calls += 1
        return original_resolve(repo_root, commit)

    def counted_read(repo_root: Path, commit: str, path: str) -> bytes | None:
        read_counts[path] = read_counts.get(path, 0) + 1
        return original_read(repo_root, commit, path)

    def counted_walk(
        explorer: M._ReachabilityExplorer, start: M._CallableTarget
    ) -> M._Reachability:
        cache_identities.append(
            (
                id(explorer.probe.cache),
                id(explorer.probe.python_cache),
                id(explorer.probe.function_cache),
                id(explorer.probe.binding_cache),
                id(explorer.probe.graph_cache),
            )
        )
        graph_cache_hits.append(
            (start, explorer.limits) in explorer.probe.graph_cache
        )
        return original_walk(explorer, start)

    monkeypatch.setattr(M, "_read_blob_at_resolved", counted_read)
    monkeypatch.setattr(core, "resolve_commit", counted_resolve)
    monkeypatch.setattr(M._ReachabilityExplorer, "walk", counted_walk)
    results = M.evaluate_all(head, repo_root=root)
    assert len(results) == 12
    assert read_counts
    assert resolve_calls == 1
    assert max(read_counts.values()) == 1
    assert graph_cache_hits == [False, True, True]
    assert len(set(cache_identities)) == 1


def test_report_projection_is_hash_seed_deterministic(tmp_path: Path) -> None:
    root, head, _ = _terminal_result(
        tmp_path, "hash-seed", "C12", _value_flow_sources()
    )
    script = (
        "import json,sys; from pathlib import Path; "
        "from orchestrator.campaign import s8c_preregistration_evidence as M; "
        "rows=M.evaluate_all(sys.argv[2],repo_root=Path(sys.argv[1])); "
        "print(json.dumps([(x.id,x.status.value,x.reason_code,"
        "[(r.path,r.blob_sha256) for r in x.evidence]) for x in rows],"
        "sort_keys=True,separators=(',',':')))"
    )
    outputs = []
    for seed in ("1", "987654"):
        environment = dict(os.environ)
        environment["PYTHONHASHSEED"] = seed
        outputs.append(
            subprocess.run(
                [sys.executable, "-c", script, str(root), head],
                cwd=_ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=30,
            ).stdout
        )
    assert outputs[0] == outputs[1]


def test_satisfiable_predicate_requires_negative_control() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    rows = {condition.identifier: condition for condition in contract.conditions}
    machine_checkable = {
        identifier for identifier, row in rows.items() if row.machine_checkable
    }
    assert machine_checkable == M.MACHINE_CHECKABLE_CONDITION_IDS
    assert machine_checkable == {
        "C01", "C02", "C04", "C09", "C10", "C11", "C12"
    }
    assert M.SATISFIABLE_CONDITION_IDS == frozenset()
    assert M.SATISFIABLE_CONDITION_IDS <= M.MACHINE_CHECKABLE_CONDITION_IDS
    exercised = 0
    for identifier in machine_checkable:
        exercised += 1
        row = rows[identifier]
        assert row.negative_control_id in NEGATIVE_CONTROL_CASES
        assert NEGATIVE_CONTROL_CASES[row.negative_control_id] == identifier
    assert exercised == 7
    assert set(NEGATIVE_CONTROL_CASES) == {
        rows[identifier].negative_control_id for identifier in machine_checkable
    }


@pytest.mark.parametrize(
    ("negative_control_id", "identifier"),
    tuple(NEGATIVE_CONTROL_CASES.items()),
)
def test_noop_and_token_only_fixtures_never_satisfy(
    tmp_path: Path, negative_control_id: str, identifier: str
) -> None:
    root = _init_repo(tmp_path)
    sources, mutated_path, mutated_source = _negative_control_case(negative_control_id)
    for path, source in sources.items():
        _write(root, path, source)
    token_only = _commit(root, f"token only {identifier}")
    token_result = _result(root, token_only, identifier)
    assert token_result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert token_result.reason_code == "completion-proof-not-machine-checkable"

    _write(root, mutated_path, mutated_source)
    mutated = _commit(root, f"mutated token only {negative_control_id}")
    mutated_result = _result(root, mutated, identifier)
    expected_reasons = {
        "C01": "workload-projection-mismatch",
        "C02": "arm-binding-consumer-unreachable",
        "C04": "crash-policy-cell-partial",
        "C09": "formal-acceptance-layer3-consumer-absent",
        "C10": "cross-binding-verifier-incomplete",
        "C11": "generation-cap-not-lifted",
        "C12": "allocation-enforcement-consumer-absent",
    }
    assert mutated_result.status is core.PredicateStatus.UNSATISFIED
    assert mutated_result.reason_code == expected_reasons[identifier]


def test_runtime_satisfiable_allowlist_rejects_unlisted_evaluator_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _init_repo(tmp_path)
    sources, _, _ = _negative_control_case(
        "nc_c02_proposal_path_arm_collision"
    )
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, "spuriously satisfied C02 evaluator")

    def spuriously_satisfied(probe: M._ConditionProbe) -> core.PredicateResult:
        return M._result(
            probe,
            core.PredicateStatus.SATISFIED,
            M.ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
        )

    monkeypatch.setitem(M._MACHINE_EVALUATORS, 2, spuriously_satisfied)
    result = _result(root, head, "C02")
    assert result.status is core.PredicateStatus.ERROR
    assert result.reason_code == "evaluator-internal-error"


def test_evidence_reads_commit_blob_not_dirty_worktree(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    sources, mutated_path, mutated_source = _negative_control_case(
        "nc_c01_perf_scale_regression"
    )
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, "token-only C01")
    before = _result(root, head, "C01")
    assert before.status is core.PredicateStatus.EVIDENCE_UNDEFINED

    _write(root, mutated_path, mutated_source)
    after = _result(root, head, "C01")
    assert after == before


def test_live_evaluator_bytes_must_match_commit_blob(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, core.CORE_MODULE_PATH, Path(core.__file__).read_bytes())
    _write(root, core.EVALUATOR_MODULE_PATH, b"# bytes different from imported evaluator\n")
    _write(root, core.PROJECTION_MODULE_PATH, Path(projection.__file__).read_bytes())
    head = _commit(root, "mismatched evaluator")
    report = core.activation_report_at(root, head)
    assert {item.status for item in report.predicates} == {core.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {"evaluator-blob-mismatch"}


def test_evaluator_identity_precedes_projection_identity(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, core.CORE_MODULE_PATH, Path(core.__file__).read_bytes())
    head = _commit(root, "missing evaluator and projection")
    report = core.activation_report_at(root, head)
    assert {item.status for item in report.predicates} == {
        core.PredicateStatus.EVIDENCE_UNDEFINED
    }
    assert {item.reason_code for item in report.predicates} == {
        "evaluator-module-absent-at-commit"
    }


def test_live_core_bytes_must_match_commit_blob(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(root, core.CORE_MODULE_PATH, b"# bytes different from running core\n")
    _write(root, core.EVALUATOR_MODULE_PATH, Path(M.__file__).read_bytes())
    head = _commit(root, "mismatched core")
    report = core.activation_report_at(root, head)
    assert {item.status for item in report.predicates} == {core.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {"core-blob-mismatch"}


def test_c11_prohibition_ruling_blob_alone_is_not_compliance(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        TOKEN_ONLY_C11.replace("MAX_APPROVED_GENERATIONS = 2", "MAX_APPROVED_GENERATIONS = 1"),
    )
    _write(
        root,
        "docs/archive/ruling-fixture.md",
        "T-324: generation budget one のまま正式系列を実走してはならない。\n",
    )
    head = _commit(root, "prohibition ruling only")
    result = _result(root, head, "C11")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "generation-cap-not-lifted"


def test_machine_checkable_condition_without_evaluator_is_error(tmp_path: Path) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    value["conditions"][2]["machine_checkable"] = True
    root = _init_repo(tmp_path)
    _write(
        root,
        core.EVIDENCE_CONTRACT_PATH,
        json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )
    head = _commit(root, "C03 falsely marked machine checkable")

    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.ERROR
    assert result.reason_code == "commit-blob-read-error"


def test_legacy_contract_routes_machine_evaluators_to_undefined(
    tmp_path: Path,
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    for row in value["conditions"]:
        if f"C{row['condition_number']:02d}" in M.MACHINE_CHECKABLE_CONDITION_IDS:
            row["machine_checkable"] = False
    root = _init_repo(tmp_path)
    _write(
        root,
        core.EVIDENCE_CONTRACT_PATH,
        json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )
    head = _commit(root, "legacy all-static contract")

    results = {item.id: item for item in M.get_registry().evaluate_all(head, repo_root=root)}
    for identifier in M.MACHINE_CHECKABLE_CONDITION_IDS:
        assert results[identifier].status is core.PredicateStatus.EVIDENCE_UNDEFINED
        assert results[identifier].reason_code == "completion-proof-not-machine-checkable"


@pytest.mark.parametrize(
    ("mutation", "projection"),
    [
        pytest.param("missing", None, id="missing-blob"),
        pytest.param(
            "broken-identifier",
            TOKEN_ONLY_C11_PROJECTION.replace(
                "def _validate_critic_projection(): pass",
                "def validate_critic_projection(): pass",
            ),
            id="broken-identifier",
        ),
    ],
)
def test_c11_generation_projection_is_required_before_terminal_undefined(
    tmp_path: Path, mutation: str, projection: str | None
) -> None:
    root = _init_repo(tmp_path)
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        TOKEN_ONLY_C11,
    )
    projection_path = "orchestrator/campaign/s8c_generation_projection.py"
    _write(root, projection_path, TOKEN_ONLY_C11_PROJECTION)
    baseline = _commit(root, "valid C11 projection shape")
    baseline_result = _result(root, baseline, "C11")
    assert baseline_result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert baseline_result.reason_code == "completion-proof-not-machine-checkable"

    if projection is None:
        (root / projection_path).unlink()
    else:
        _write(root, projection_path, projection)
    mutated = _commit(root, f"{mutation} C11 projection")
    result = _result(root, mutated, "C11")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "critic-feedback-consumer-absent"


def test_c03_c08_contract_uses_two_stage_binding_without_self_reference() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    for number in (3, 8):
        condition = contract.condition(number)
        serialized = json.dumps(
            json.loads(CONTRACT_FILE.read_bytes())["conditions"][number - 1],
            ensure_ascii=False,
        )
        assert "prereg_commit" not in serialized
        manifest = next(
            item for item in condition.required_evidence
            if item.artifact_kind == "trial_manifest"
        )
        assert set(manifest.field_paths).isdisjoint(
            {"prereg_content_commit", "prereg_effective_commit", "manifest_sha256"}
        )
        binding = next(
            item for item in condition.required_evidence
            if item.artifact_kind == "prereg_effective_binding"
        )
        assert set(binding.field_paths) == {
            "prereg_content_commit", "manifest_path", "manifest_sha256"
        }

    c08_proof = contract.condition(8).consumer_requirement.proof
    assert "effective commit C to have the exact parent set {P}" in c08_proof
    assert "prove ancestry from C to the measurement HEAD" in c08_proof
    assert c08_proof.count("ancestry") == 1


def test_machine_checkable_contract_and_evaluator_registry_are_bijective() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    contract_ids = {
        condition.identifier
        for condition in contract.conditions
        if condition.machine_checkable
    }
    evaluator_ids = frozenset(
        f"C{number:02d}" for number in M._MACHINE_EVALUATORS
    )
    assert contract_ids == evaluator_ids == M.MACHINE_CHECKABLE_CONDITION_IDS
