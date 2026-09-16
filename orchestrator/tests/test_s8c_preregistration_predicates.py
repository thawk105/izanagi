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
from orchestrator.campaign import s8c_schedule as S  # noqa: E402


CONTRACT_FILE = _ROOT / core.EVIDENCE_CONTRACT_PATH
_C06_CANDIDATE_PATHS = (
    core.EVIDENCE_CONTRACT_PATH,
    "orchestrator/campaign/s8c_budget.py",
    "orchestrator/campaign/s8b_ratified_freeze.py",
    "orchestrator/campaign/p3_autonomous_workload_trial.py",
)
_CurrentCommitSnapshot = tuple[
    Path,
    str,
    tuple[core.PredicateResult, ...],
    str,
    tuple[core.PredicateResult, ...],
]


def _c05_authority() -> dict[str, object]:
    return {
        "arms": ["on", "off", "swapped"],
        "designated_source_context": "axis:silo-backoff-trigger-gating/v1",
        "descriptor_bindings": {
            "H1": {"workload": "rr80", "ycsb_rratio": "80"},
            "H2": {"workload": "rr20", "ycsb_rratio": "20"},
        },
        "gating_spec": "five-bit-wire:v1",
        "holdout_bindings": {
            "H1": {"workload": "rr80", "ycsb_rratio": "80"},
            "H2": {"workload": "rr20", "ycsb_rratio": "20"},
        },
        "holdouts": ["H1", "H2"],
        "role_contracts": {
            "auditor": "auditor-contract:v1",
            "coder": "coder-contract:v1",
            "critic": "critic-contract:v1",
            "planner": "planner-contract:v1",
        },
        "role_files": {
            "auditor": "auditor.md",
            "coder": "coder.md",
            "critic": "critic.md",
            "planner": "planner.md",
        },
        "role_payload_allowlist": {
            "auditor": ["working_diff", "correctness_digest"],
            "coder": ["gating_spec", "baseline"],
            "critic": ["harness_result", "critic_digest"],
            "planner": ["current_perf", "whiteboard"],
        },
        "workloads": {
            "rr20": {"records": 100000, "threads": 4},
            "rr80": {"records": 100000, "threads": 4},
        },
        "attempt_policy": {"max_attempts": 1, "retry": False},
        "baseline": {"kind": "stock", "trace": False},
        "descriptor_binding": {
            "schema_version": "8b-v1",
            "descriptor_sha256": "descriptor-hash",
        },
        "gating_snapshot": {"schema_version": "gating-snapshot/v1", "wire": "10100"},
        "initial_role_metrics": {
            "abort_rate": None,
            "ipc": None,
            "latency_ns": None,
            "llc_miss_rate": None,
            "throughput_tps": None,
        },
        "leakproof_context": {
            "tools": ["declared-tool-set"],
            "projected_input_only": True,
        },
        "stop_policy": {
            "reasons": ["converged", "budget-iterations", "budget-walltime"],
        },
        "whiteboard": [{"status": "initial"}],
    }


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


def _require_unchanged_head(recorded: str, current: str) -> None:
    if recorded != current:
        raise AssertionError(
            "repository HEAD changed after shared evaluation: "
            f"recorded={recorded}, current={current}"
        )


def _snapshot_current_commit(
    tmp_path: Path,
) -> tuple[Path, str, str, tuple[core.PredicateResult, ...]]:
    """現 HEAD を一時 commit へ写す補助検査。

    snapshot と HEAD は同じ evaluator を使うため、resolver mutation の kill 根拠には
    数えない。ここで固定するのは commit-blob 投影の同値性だけである。
    """
    root = _init_repo(tmp_path, "current-snapshot")
    evaluated_head = _git(_ROOT, "rev-parse", "HEAD").decode("ascii").strip()
    evaluated_results = tuple(
        M.get_registry().evaluate_all(evaluated_head, repo_root=_ROOT)
    )
    paths = {
        reference.path
        for result in evaluated_results
        for reference in result.evidence
    }
    paths.add(core.EVIDENCE_CONTRACT_PATH)
    tracked = set(
        _git(_ROOT, "ls-tree", "-r", "--name-only", evaluated_head).decode().splitlines()
    )
    assert paths - tracked <= {core.EVIDENCE_CONTRACT_PATH}
    present = sorted(paths & tracked)
    if present:
        archive = _git(
            _ROOT, "archive", "--format=tar", evaluated_head, "--", *present
        )
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            for member in bundle.getmembers():
                if not member.isfile():
                    continue
                source = bundle.extractfile(member)
                assert source is not None
                _write(root, member.name, source.read())
    # HEAD がこの単位をまだ含まない段 5 でも、評価対象 commit には契約を含める。
    _write(root, core.EVIDENCE_CONTRACT_PATH, CONTRACT_FILE.read_bytes())
    return (
        root,
        _commit(root, "current evidence snapshot"),
        evaluated_head,
        evaluated_results,
    )


@pytest.fixture(scope="module")
def current_commit_snapshot(
    tmp_path_factory: pytest.TempPathFactory,
    real_repo_fixture_lock,
) -> _CurrentCommitSnapshot:
    """Read-only snapshot shared under parent SH for its full module lifetime."""
    with real_repo_fixture_lock("read", None):
        root, head, evaluated_head, evaluated_results = _snapshot_current_commit(
            tmp_path_factory.mktemp("current-commit")
        )
        results = tuple(M.get_registry().evaluate_all(head, repo_root=root))
        yield root, head, results, evaluated_head, evaluated_results


def test_predicate_registry_is_exactly_c01_through_c12(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    head = _commit(root)
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert tuple(item.id for item in results) == core.PREDICATE_IDS
    assert len(results) == 12
    assert all(item.reason_code in M.REASON_CODES for item in results)


def test_require_unchanged_head_accepts_matching_oids() -> None:
    oid = "a" * 40
    _require_unchanged_head(oid, oid)


def test_require_unchanged_head_rejects_mismatched_oids() -> None:
    with pytest.raises(AssertionError, match="repository HEAD changed"):
        _require_unchanged_head("a" * 40, "b" * 40)


@pytest.mark.xdist_group("s8c-predicate-snapshot")
def test_current_repository_snapshot_has_zero_satisfied_predicates(
    current_commit_snapshot: _CurrentCommitSnapshot,
) -> None:
    _, _, results, evaluated_head, actual = current_commit_snapshot
    satisfied = {
        item.id
        for item in results
        if item.status is core.PredicateStatus.SATISFIED
    }
    actual_by_id = {item.id: item for item in actual}
    assert satisfied == {"C10"}
    assert actual_by_id["C10"].status is core.PredicateStatus.SATISFIED
    assert actual_by_id["C10"].reason_code == "cross-binding-readiness-satisfied"
    assert core.activation_report_at(_ROOT, evaluated_head).effective is False
    for item in results:
        assert item.evidence
        assert all(ref.path and len(ref.blob_sha256) == 64 for ref in item.evidence)


@pytest.mark.xdist_group("s8c-predicate-snapshot")
def test_current_repository_snapshot_exactly_matches_head(
    current_commit_snapshot: _CurrentCommitSnapshot,
) -> None:
    _, _, snapshot, evaluated_head, actual = current_commit_snapshot
    current_head = _git(_ROOT, "rev-parse", "HEAD").decode("ascii").strip()
    _require_unchanged_head(evaluated_head, current_head)
    assert snapshot == actual
    verifier_source = _git(
        _ROOT,
        "show",
        f"{evaluated_head}:orchestrator/campaign/autonomous_trial_completeness.py",
    ).decode("utf-8")
    verifier_module = ast.parse(verifier_source)
    verifier = next(
        node
        for node in verifier_module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "verify_s8c_cross_binding"
    )
    assert "proposal_build_source_bindings" in {
        node.value
        for node in ast.walk(verifier)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    c10 = next(item for item in actual if item.id == "C10")
    assert c10.status is core.PredicateStatus.SATISFIED
    assert c10.reason_code == "cross-binding-readiness-satisfied"


@pytest.mark.xdist_group("s8c-predicate-snapshot")
def test_current_repository_gap_reason_snapshot_requires_cross_wave_review(
    current_commit_snapshot: _CurrentCommitSnapshot,
) -> None:
    """個別 reason は gap ledger。他 wave の land 時は意図を再審査して更新する。

    [T-325] の land で trial_registry の capability probe 段階を通過した。

    退役した `test_current_repository_c12_registry_reports_unwired_allocation_consumer` が
    表していた C12 registry の allocation consumer 未配線という主張と、
    `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer` が
    表していた C12 allocation binding helper の consumer 未配線という主張も発見用に残す。
    この記述は検査ではなく、安全性や退役可否の根拠にはしない。
    """
    _, _, results, _, _ = current_commit_snapshot
    snapshot_by_id = {
        item.id: (item.status, item.reason_code) for item in results
    }
    assert snapshot_by_id["C12"][0] is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert snapshot_by_id == {
        "C01": (
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            "completion-proof-not-machine-checkable",
        ),
        "C02": (
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            "completion-proof-not-machine-checkable",
        ),
        "C03": (core.PredicateStatus.UNSATISFIED, "manifest-registry-proof-undefined"),
        "C04": (
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            "completion-proof-not-machine-checkable",
        ),
        "C05": (core.PredicateStatus.EVIDENCE_UNDEFINED, "schedule-schema-absent"),
        "C06": (core.PredicateStatus.EVIDENCE_UNDEFINED, "completion-proof-not-machine-checkable"),
        "C07": (core.PredicateStatus.EVIDENCE_UNDEFINED, "completion-proof-not-machine-checkable"),
        "C08": (core.PredicateStatus.EVIDENCE_UNDEFINED, "prereg-binding-proof-undefined"),
        "C09": (
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            "completion-proof-not-machine-checkable",
        ),
        "C10": (
            core.PredicateStatus.SATISFIED,
            "cross-binding-readiness-satisfied",
        ),
        "C11": (core.PredicateStatus.EVIDENCE_UNDEFINED, "completion-proof-not-machine-checkable"),
        "C12": (
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            "completion-proof-not-machine-checkable",
        ),
    }


@pytest.mark.xdist_group("s8c-predicate-snapshot")
def test_current_repository_c04_rejects_missing_started_trial_preflight(
    tmp_path: Path,
    current_commit_snapshot: _CurrentCommitSnapshot,
) -> None:
    root, head, _, evaluated_head, _ = current_commit_snapshot
    current_head = _git(_ROOT, "rev-parse", "HEAD").decode("ascii").strip()
    _require_unchanged_head(evaluated_head, current_head)

    baseline = _result(root, head, "C04")
    assert baseline.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert baseline.reason_code == "completion-proof-not-machine-checkable"

    workload_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    registry_path = "orchestrator/campaign/trial_registry.py"
    workload_source = (root / workload_path).read_bytes()
    registry_source = (root / registry_path).read_bytes()
    started_trial_call = b"""    trial_registry.reject_started_trial(
        trial_id=trial_id,
        repository_root=ROOT,
        lifecycle_path=ROOT / trial_registry.DEFAULT_LIFECYCLE_PATH,
    )
"""
    assert workload_source.count(b"trial_registry.reject_started_trial(") == 1
    assert workload_source.count(started_trial_call) == 1

    mutated_workload = workload_source.replace(started_trial_call, b"", 1)
    mark_call = b"            mark_experiment_indeterminate(\n"
    forbid_call = b"trial_registry.forbid_trial_restart("
    assert mutated_workload.count(b"trial_registry.reject_started_trial(") == 0
    assert workload_source.count(mark_call) >= 1
    assert mutated_workload.count(mark_call) == workload_source.count(mark_call)
    assert workload_source.count(forbid_call) == 1
    assert mutated_workload.count(forbid_call) == 1
    assert registry_source.count(b"def reject_started_trial(") == 1
    assert registry_source.count(b"def forbid_trial_restart(") == 1

    mutated_root = _init_repo(tmp_path, "current-snapshot-c04-mutation")
    tracked_paths = (
        _git(root, "ls-tree", "-r", "--name-only", head).decode().splitlines()
    )
    for path in tracked_paths:
        _write(mutated_root, path, (root / path).read_bytes())
    _write(mutated_root, workload_path, mutated_workload)
    mutated_head = _commit(mutated_root, "C04 reject-started preflight removed")
    result = _result(mutated_root, mutated_head, "C04")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "crash-policy-cell-partial"


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

TOKEN_ONLY_C03_REGISTRY = """
MANIFEST_SCHEMA_VERSION = "manifest.v1"
REGISTRATION_SCHEMA_VERSION = "registration.v1"
DEFAULT_ATTEMPT_REGISTRY_PATH = "attempt-registry.jsonl"
ATTEMPT_REGISTRY_SCHEMA_VERSION = "attempt-registry.v1"
ATTEMPT_STATUSES = ("observed", "retryable-failure", "terminal-failure", "not-consumed")
ATTEMPT_RETRYABLE_FAILURE_REASONS = ("provider-transient",)
def load_trial_manifest(path):
    return path
def load_effective_binding_at_commit(repository_root, effective_commit, manifest_path):
    return (repository_root, effective_commit, manifest_path)
def validate_preregistration_binding(repository_root, *, manifest_path, effective_commit, measurement_commit):
    return load_effective_binding_at_commit(
        repository_root, effective_commit, manifest_path
    )
def _trial_canonical_tuple(trial):
    return (
        trial.trial_id,
        trial.arm,
        trial.holdout,
        trial.campaign_id,
        trial.generations,
    )
def _assert_manifest_registry_trial_set(manifest, registration):
    expected = tuple(_trial_canonical_tuple(item) for item in manifest.trials)
    actual = tuple(_trial_canonical_tuple(item) for item in registration.trials)
    if len(actual) != len(expected) or set(actual) != set(expected):
        raise ValueError("manifest registry set mismatch")
def _assert_runtime_report_trial_set(loaded, manifest):
    ids = [item.report.get("trial_id") for item in loaded]
    return set(ids) == {trial.trial_id for trial in manifest.trials}
def _assert_runtime_report_cells(report, *, trial):
    cells = report.get("cells")
    if not isinstance(cells, list) or len(cells) > 1:
        raise ValueError("runtime cells mismatch")
    if cells:
        cell = cells[0]
        flags = cell.get("workload_flags")
        if (
            cell.get("workload") != "workload"
            or not isinstance(flags, dict)
            or flags.get("ycsb_rratio") != "50"
            or cell.get("campaign_id") != trial.campaign_id
        ):
            raise ValueError("runtime cell projection mismatch")
    return cells
def _find_registration_for_manifest(registrations, manifest, *, effective_commit=None):
    registration = registrations[0]
    _assert_manifest_registry_trial_set(manifest, registration)
    return registration
def load_attempt_registry(*args, **kwargs):
    return ()
def assert_attempt_registry_acceptance(*, report, trial):
    rows = load_attempt_registry()
    return rows
def assert_trial_registry_acceptance(*, manifest_path, registration, loaded, report):
    manifest = load_trial_manifest(manifest_path)
    binding = validate_preregistration_binding(
        None,
        manifest_path=manifest_path,
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=registration.measurement_head,
    )
    selected = _find_registration_for_manifest(
        [registration], manifest, effective_commit=registration.prereg_effective_commit
    )
    _assert_runtime_report_trial_set(loaded, manifest)
    _assert_runtime_report_cells(report, trial=manifest.trials[0])
    assert_attempt_registry_acceptance(report=report, trial=manifest.trials[0])
    return {
        "manifest_sha256": selected.manifest_sha256,
        "prereg_content_commit": selected.prereg_content_commit,
        "prereg_effective_commit": selected.prereg_effective_commit,
        "trials": manifest.trials,
        "cells": report.get("cells"),
        "binding": binding,
    }
def create_attempt_registry_genesis(*args, **kwargs):
    pass
def reserve_attempt_slot(*args, **kwargs):
    pass
def classify_attempt(*args, **kwargs):
    pass
def begin_attempt_observation(*args, **kwargs):
    pass
def record_attempt_terminal(*args, **kwargs):
    pass
"""

TOKEN_ONLY_C03_PRODUCER = """
from . import trial_registry
def _reserve_registered_attempt_slot():
    return trial_registry.reserve_attempt_slot()
def _record_attempt_terminal_for_run():
    trial_registry.classify_attempt()
    trial_registry.begin_attempt_observation()
    trial_registry.record_attempt_terminal()
def read_observation():
    return "observation"
def run_trial():
    slot = _reserve_registered_attempt_slot()
    _record_attempt_terminal_for_run()
    value = read_observation()
    return slot, value
"""

TOKEN_ONLY_C08_REGISTRY = """
def _blob_at_commit(repository_root, *, commit_id, relative_path):
    return (repository_root, commit_id, relative_path)
def _assert_ancestor(repository_root, *, ancestor, descendant, gate, message):
    return (repository_root, ancestor, descendant, gate, message)
def assert_effective_commit_exact_parent(repository_root, *, content_commit, effective_commit):
    return (repository_root, content_commit, effective_commit)
def load_effective_binding_at_commit(repository_root, effective_commit, manifest_path, manifest=None):
    binding_blob = _blob_at_commit(
        repository_root,
        commit_id=effective_commit,
        relative_path="output/s8c-preregistration/prereg-effective-binding.v1.json",
    )
    return binding_blob
def validate_preregistration_binding(
    repository_root, *, manifest_path, effective_commit, measurement_commit
):
    binding = load_effective_binding_at_commit(
        repository_root, effective_commit, manifest_path
    )
    _assert_ancestor(
        repository_root,
        ancestor=manifest.prereg_commit,
        descendant=binding.prereg_content_commit,
        gate="ancestry",
        message="manifest ancestry",
    )
    assert_effective_commit_exact_parent(
        repository_root,
        content_commit=binding.prereg_content_commit,
        effective_commit=effective_commit,
    )
    _assert_ancestor(
        repository_root,
        ancestor=effective_commit,
        descendant=measurement_commit,
        gate="ancestry",
        message="measurement ancestry",
    )
    return binding
def _derive_launch_binding(*, manifest_path, registration, measurement_head):
    return validate_preregistration_binding(
        None,
        manifest_path=manifest_path,
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=measurement_head,
    )
def load_launch_binding(*, manifest_path, registration, measurement_head):
    return _derive_launch_binding(
        manifest_path=manifest_path,
        registration=registration,
        measurement_head=measurement_head,
    )
def admit_registered_launch(*, manifest_path, registration, measurement_head):
    return load_launch_binding(
        manifest_path=manifest_path,
        registration=registration,
        measurement_head=measurement_head,
    )
def _expected_registered_launch_admission_record(*, manifest_path, registration, measurement_head):
    return validate_preregistration_binding(
        None,
        manifest_path=manifest_path,
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=measurement_head,
    )
def assert_trial_registry_acceptance(*, manifest_path, registration, measurement_head):
    return validate_preregistration_binding(
        None,
        manifest_path=manifest_path,
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=measurement_head,
    )
"""

TOKEN_ONLY_C04 = """
from .trial_registry import forbid_trial_restart
from .trial_registry import reject_started_trial
def launch_cells(): pass
def mark_experiment_indeterminate(): pass
def run_trial():
    reject_started_trial()
    try:
        launch_cells()
    except Exception:
        mark_experiment_indeterminate()
        forbid_trial_restart()
def main():
    return run_trial()
"""

TOKEN_ONLY_C05_SCHEDULE = """
def validate_authority(authority):
    return (
        "schema_version",
        "master_seed",
        "cells",
        "schedule_index",
        "arm",
        "holdout",
        "search_space_sha256",
        "initial_state_sha256",
    )

def search_space_digest(authority):
    return "search_space_sha256"

def initial_state_digest(authority):
    return "initial_state_sha256"

def regenerate(master_seed, *, authority):
    return master_seed, authority

def load_schedule(path):
    return path

def verify_exact_schedule_bytes(artifact_bytes, *, master_seed, authority):
    regenerate(master_seed, authority=authority)
    return artifact_bytes

def verify_shared_search_space_and_initial_state(
    schedule, *, expected_search_space_sha256, expected_initial_state_sha256
):
    return schedule, expected_search_space_sha256, expected_initial_state_sha256

def verify_schedule(artifact_bytes, *, master_seed, authority):
    validate_authority(authority)
    verify_exact_schedule_bytes(
        artifact_bytes, master_seed=master_seed, authority=authority
    )
    verify_shared_search_space_and_initial_state(
        artifact_bytes,
        expected_search_space_sha256=search_space_digest(authority),
        expected_initial_state_sha256=initial_state_digest(authority),
    )
    return artifact_bytes

def consume_schedule(
    artifact_bytes, *, master_seed, authority, schedule_index
):
    verify_schedule(
        artifact_bytes, master_seed=master_seed, authority=authority
    )
    return schedule_index
"""

TOKEN_ONLY_C05_SUPERVISOR = """
from .s8c_schedule import consume_schedule, load_schedule

def run_trial():
    artifact = load_schedule("output/s8c-preregistration/schedule.v1.json")
    return consume_schedule(
        artifact,
        master_seed="fixture-seed",
        authority={},
        schedule_index=0,
    )

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
        "proposal_sha256", "proposal_build_source_bindings", "build_records",
        "bench_records", "artifact_refs", "source_refs", "admission_decision",
    )
    read_and_verify_bytes()
    return fields
"""

TOKEN_ONLY_C10_REGISTRY = """
def verify_s8c_cross_binding(): pass
def assert_trial_registry_acceptance():
    return verify_s8c_cross_binding()
"""

C10_SATISFIED_VERIFIER = """
import hashlib
from pathlib import Path

def read_and_verify_bytes(path, *, expected_sha256):
    raw = Path(path).read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("digest mismatch")
    return raw

def verify_s8c_cross_binding(event):
    fields = (
        "input_payload_sha256", "provider_payload_sha256",
        "provider_envelope_sha256", "proposal_path", "proposal_sha256",
        "build_records", "bench_records", "artifact_refs", "source_refs",
        "proposal_build_source_bindings",
        "admission_decision",
    )
    raw = read_and_verify_bytes(
        event.get("raw_response_path"),
        expected_sha256=event.get("raw_response_sha256"),
    )
    return fields, raw
"""

C10_SATISFIED_REGISTRY = """
from .autonomous_trial_completeness import verify_s8c_cross_binding

def assert_trial_registry_acceptance(event):
    try:
        receipt = verify_s8c_cross_binding(event)
    except ValueError as exc:
        raise RuntimeError("cross binding failed") from exc
    return {"cross_binding_receipt_sha256": receipt}
"""

ACTIVE_VALUE_CHECK_C10 = """
import hashlib
from pathlib import Path

def read_and_verify_bytes(path, *, expected_sha256):
    raw = Path(path).read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("digest mismatch")
    return raw

def _never():
    return False

def verify_s8c_cross_binding(actual, expected):
    fields = (
        "input_payload_sha256", "raw_response_path", "raw_response_sha256",
        "provider_payload_sha256", "provider_envelope_sha256", "proposal_path",
        "proposal_sha256", "proposal_build_source_bindings", "build_records",
        "bench_records", "artifact_refs", "source_refs", "admission_decision",
    )
    read_and_verify_bytes(
        actual["raw_response_path"],
        expected_sha256=actual["raw_response_sha256"],
    )
    actual_value = actual["proposal_build_source_bindings"]
    expected_value = expected["proposal_build_source_bindings"]
    if actual_value != expected_value:
        raise ValueError("proposal_build_source_bindings differs")
    return fields
"""

NEUTERED_VALUE_CHECK_C10 = ACTIVE_VALUE_CHECK_C10.replace(
    "    if actual_value != expected_value:\n",
    "    if _never() and actual_value != expected_value:\n",
)
assert NEUTERED_VALUE_CHECK_C10 != ACTIVE_VALUE_CHECK_C10

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
from .reservation import read_binding, check_reservation
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

TOKEN_ONLY_C07 = """
__all__ = ("verify_floor_bytes", "judge", "publish_result_table")
_CONDITION_IDS = (
    "on_off_prediction_difference",
    "swapped_follow_through",
    "paired_repeat_contrast",
)
_TABLE_NAMES = ("descriptive_only", "official_status", "selection_evaluation")
_FLOOR_ARTIFACT_KINDS = ("floor_protocol", "floor_source")

def _validate_floor_reference(path, sha256, env_tag, measurement_head, ratified):
    return path, sha256, env_tag, measurement_head, ratified

def _validate_contrast_params(params):
    return params

def _validate_complete_block(manifest, params):
    return manifest, params

def _validate_exact_cell_set(generated, expected):
    return tuple(generated) if set(generated) == set(expected) else None

def _validate_verified_floor(receipt):
    return receipt

def _table_bytes(name, cells):
    return {"table": name, "result_table": {"cells": cells}}

def verify_floor_bytes(floor_refs):
    ratified = load_ratified_freeze()
    if not ratified["sha256"]:
        raise ValueError("missing ratified digest")
    if tuple(_FLOOR_ARTIFACT_KINDS) != ("floor_protocol", "floor_source"):
        raise ValueError("wrong floor artifacts")
    floor_protocol = floor_refs[0]
    floor_source = floor_refs[1]
    path = floor_protocol["path"]
    sha256 = floor_protocol["sha256"]
    source_path = floor_source["path"]
    source_sha256 = floor_source["sha256"]
    env_tag = ratified["env_tag"]
    measurement_head = ratified["frozen_at_head"]
    validated = _validate_floor_reference(
        path, sha256, env_tag, measurement_head, ratified
    )
    source_validated = _validate_floor_reference(
        source_path, source_sha256, env_tag, measurement_head, ratified
    )
    if not validated or not source_validated:
        raise ValueError("invalid floor reference")
    return (validated, source_validated)

def judge(params, manifest=None):
    validated = _validate_contrast_params(params)
    complete = _validate_complete_block(manifest, params)
    if not validated or not complete:
        raise ValueError("invalid params")
    conditions = {
        _CONDITION_IDS[0]: "UNSATISFIED",
        _CONDITION_IDS[1]: "UNSATISFIED",
        _CONDITION_IDS[2]: "UNSATISFIED",
    }
    return conditions

def publish_result_table(result, predeclared_cells, verified_floor):
    checked_floor = _validate_verified_floor(verified_floor)
    if not checked_floor:
        raise ValueError("floor receipt required")
    cells = result["result_table"]["cells"]
    descriptive = _validate_exact_cell_set(cells, predeclared_cells)
    if descriptive is None:
        raise ValueError("cell set mismatch")
    return {
        name: _table_bytes(name, descriptive)
        for name in _TABLE_NAMES
    }
"""

TOKEN_ONLY_C07_RATIFIED = """
def load_ratified_freeze():
    return {
        "sha256": "a" * 64,
        "env_tag": "fixture-env",
        "frozen_at_head": "b" * 40,
    }
"""

TOKEN_ONLY_C07_DECLARED_PATH_DECOY = """
__all__ = ("verify_floor_bytes", "judge", "publish_result_table")
def verify_floor_bytes(*args, **kwargs):
    return None
def judge(*args, **kwargs):
    return None
def publish_result_table(*args, **kwargs):
    return None
"""


def test_c12_allocation_binding_helper_rejects_check_without_read_binding(
    tmp_path: Path,
) -> None:
    read_binding_call = "    binding = read_binding(environ)"
    without_read_binding = TOKEN_ONLY_C12.replace(
        read_binding_call,
        "    binding = object()",
    )
    assert without_read_binding != TOKEN_ONLY_C12

    root = _init_repo(tmp_path)
    for path, source in _c12_modules(without_read_binding).items():
        _write(root, path, source)
    head = _commit(root, "C12 read_binding call edge removed")
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "allocation-enforcement-consumer-absent"


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
    if identifier == "nc_c03_manifest_cell_removed":
        sources = {
            registry: TOKEN_ONLY_C03_REGISTRY,
            p3: TOKEN_ONLY_C03_PRODUCER,
        }
        anchor = "    expected = tuple(_trial_canonical_tuple(item) for item in manifest.trials)\n"
        replacement = "    expected = tuple()\n"
        assert TOKEN_ONLY_C03_REGISTRY.count(anchor) == 1
        mutated = TOKEN_ONLY_C03_REGISTRY.replace(anchor, replacement, 1)
        assert mutated.count(replacement) == 1
        return sources, registry, mutated
    if identifier == "nc_c08_parent_commit_substitution":
        sources = {registry: TOKEN_ONLY_C08_REGISTRY}
        anchor = "        ancestor=effective_commit,\n"
        replacement = "        ancestor=registration.prereg_content_commit,\n"
        assert TOKEN_ONLY_C08_REGISTRY.count(anchor) == 1
        mutated = TOKEN_ONLY_C08_REGISTRY.replace(anchor, replacement, 1)
        assert mutated.count(replacement) == 1
        return sources, registry, mutated
    if identifier == "nc_c04_partial_crash_survives":
        sources = {
            p3: TOKEN_ONLY_C04,
            registry: (
                "def forbid_trial_restart(): pass\n"
                "def reject_started_trial(): pass\n"
            ),
        }
        return sources, p3, TOKEN_ONLY_C04.replace(
            "        mark_experiment_indeterminate()",
            "        keep_completed_cells_certifying()",
            1,
        )
    if identifier == "nc_c05_initial_state_hash_bitflip":
        consumer = "orchestrator/campaign/s8c_schedule.py"
        artifact = "output/s8c-preregistration/schedule.v1.json"
        sources = {
            p3: TOKEN_ONLY_C05_SUPERVISOR,
            consumer: TOKEN_ONLY_C05_SCHEDULE,
            artifact: S.regenerate("fixture-seed", authority=_c05_authority()),
        }
        consume_call = """    return consume_schedule(
        artifact,
        master_seed="fixture-seed",
        authority={},
        schedule_index=0,
    )"""
        assert TOKEN_ONLY_C05_SUPERVISOR.count(consume_call) == 1
        mutated = TOKEN_ONLY_C05_SUPERVISOR.replace(
            consume_call,
            "    return artifact",
            1,
        )
        assert mutated != TOKEN_ONLY_C05_SUPERVISOR
        assert mutated.count(consume_call) == 0
        return sources, p3, mutated
    if identifier == "nc_c06_one_arm_reservation_removed":
        path = "orchestrator/campaign/s8c_budget.py"
        marker = '    ("H2", "swapped"),\n'
        assert TOKEN_ONLY_C06_BUDGET.count(marker) == 1
        mutated = TOKEN_ONLY_C06_BUDGET.replace(marker, "", 1)
        return (
            {
                path: TOKEN_ONLY_C06_BUDGET,
                "orchestrator/campaign/s8b_ratified_freeze.py": TOKEN_ONLY_C06_RATIFIED,
                "orchestrator/campaign/p3_autonomous_workload_trial.py": TOKEN_ONLY_C06_SUPERVISOR,
            },
            path,
            mutated,
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
        sources = {
            verifier: C10_SATISFIED_VERIFIER,
            registry: C10_SATISFIED_REGISTRY,
        }
        return sources, verifier, C10_SATISFIED_VERIFIER.replace(
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
    if identifier == "nc_c07_floor_or_result_cell_removed":
        result_judge = "orchestrator/campaign/s8c_result_judge.py"
        ratified = "orchestrator/campaign/s8b_ratified_freeze.py"
        floor_field = '    measurement_head = ratified["frozen_at_head"]\n'
        assert TOKEN_ONLY_C07.count(floor_field) == 1
        mutated = TOKEN_ONLY_C07.replace(floor_field, "", 1)
        assert mutated != TOKEN_ONLY_C07
        sources = {
            result_judge: TOKEN_ONLY_C07,
            ratified: TOKEN_ONLY_C07_RATIFIED,
        }
        return sources, result_judge, mutated
    raise AssertionError(identifier)


NEGATIVE_CONTROL_CASES = {
    "nc_c01_perf_scale_regression": "C01",
    "nc_c02_proposal_path_arm_collision": "C02",
    "nc_c04_partial_crash_survives": "C04",
    "nc_c05_initial_state_hash_bitflip": "C05",
    "nc_c06_one_arm_reservation_removed": "C06",
    "nc_c07_floor_or_result_cell_removed": "C07",
    "nc_c09_acceptance_skips_layer3": "C09",
    "nc_c10_raw_response_unbound": "C10",
    "nc_c11_generation_cap_reverts_to_one": "C11",
    "nc_c12_reservation_check_bypassed": "C12",
}


STATIC_NEGATIVE_CONTROL_CASES = {
    "nc_c03_manifest_cell_removed": "C03",
    "nc_c08_parent_commit_substitution": "C08",
}


NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES = {
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
    tmp_path: Path,
    name: str,
    identifier: str,
    sources: dict[str, str],
    *,
    expected_reason: str = "completion-proof-not-machine-checkable",
) -> tuple[Path, str, core.PredicateResult]:
    root = _init_repo(tmp_path, name)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, name)
    result = _result(root, head, identifier)
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == expected_reason
    return root, head, result


def _c07_probe(
    tmp_path: Path,
    name: str,
    *,
    result_source: str = TOKEN_ONLY_C07,
    ratified_source: str | None = TOKEN_ONLY_C07_RATIFIED,
    extra_sources: dict[str, str] | None = None,
) -> M._ConditionProbe:
    root = _init_repo(tmp_path, name)
    _write(root, "orchestrator/campaign/s8c_result_judge.py", result_source)
    if ratified_source is not None:
        _write(
            root,
            "orchestrator/campaign/s8b_ratified_freeze.py",
            ratified_source,
        )
    for path, source in (extra_sources or {}).items():
        _write(root, path, source)
    head = _commit(root, name)
    contract_raw = core.read_blob_at(
        root, head, core.EVIDENCE_CONTRACT_PATH, required=True
    )
    contract = M.load_contract_bytes(contract_raw).condition(7)
    return M._ConditionProbe(
        root,
        head,
        contract,
        core.EvidenceRef(core.EVIDENCE_CONTRACT_PATH, core._sha256(contract_raw)),
        {},
        {},
        declared_paths=M.load_contract_bytes(contract_raw).evidence_paths,
    )


def test_c07_token_only_direct_evaluation_is_terminal_undefined(
    tmp_path: Path,
) -> None:
    probe = _c07_probe(tmp_path, "c07-token-only")
    result = M._evaluate_c07(probe)
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "completion-proof-not-machine-checkable"


def test_c07_negative_control_removes_one_floor_field_only(
    tmp_path: Path,
) -> None:
    baseline = M._evaluate_c07(_c07_probe(tmp_path, "c07-negative-baseline"))
    assert baseline.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert baseline.reason_code == "completion-proof-not-machine-checkable"

    sources, mutated_path, mutated_source = _negative_control_case(
        "nc_c07_floor_or_result_cell_removed"
    )
    assert set(sources) == {
        "orchestrator/campaign/s8c_result_judge.py",
        "orchestrator/campaign/s8b_ratified_freeze.py",
    }
    assert mutated_path == "orchestrator/campaign/s8c_result_judge.py"
    assert isinstance(mutated_source, str)
    result = M._evaluate_c07(
        _c07_probe(
            tmp_path,
            "c07-negative-floor-field",
            result_source=mutated_source,
        )
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "result-judge-consumer-incomplete"


def test_c07_missing_ratified_loader_has_dedicated_reason(
    tmp_path: Path,
) -> None:
    result = M._evaluate_c07(
        _c07_probe(tmp_path, "c07-ratified-loader-missing", ratified_source=None)
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "ratified-generation-reference-absent"


def test_c07_removed_ratified_loader_call_is_not_a_consumer(
    tmp_path: Path,
) -> None:
    loader_call = "    ratified = load_ratified_freeze()\n"
    without_loader_call = TOKEN_ONLY_C07.replace(
        loader_call,
        "    ratified = {\"sha256\": \"a\" * 64, \"env_tag\": \"fixture-env\", \"frozen_at_head\": \"b\" * 40}\n",
        1,
    )
    assert without_loader_call != TOKEN_ONLY_C07
    result = M._evaluate_c07(
        _c07_probe(
            tmp_path,
            "c07-ratified-loader-call-removed",
            result_source=without_loader_call,
        )
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "ratified-generation-reference-absent"


def test_c07_contract_path_rejects_same_name_decoy_module(
    tmp_path: Path,
) -> None:
    decoy_path = "orchestrator/campaign/s8b_verdict.py"
    probe = _c07_probe(
        tmp_path,
        "c07-decoy-module",
        result_source="# contract path intentionally has no consumer\n",
        extra_sources={decoy_path: TOKEN_ONLY_C07},
    )
    result = M._evaluate_c07(probe)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "result-judge-consumer-incomplete"
    assert decoy_path not in probe.cache


def test_c07_declared_contract_path_decoy_is_not_a_consumer(
    tmp_path: Path,
) -> None:
    result = M._evaluate_c07(
        _c07_probe(
            tmp_path,
            "c07-declared-path-decoy",
            result_source=TOKEN_ONLY_C07_DECLARED_PATH_DECOY,
        )
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "result-judge-consumer-incomplete"


def test_c07_discarded_validator_return_is_incomplete(
    tmp_path: Path,
) -> None:
    call = (
        "    validated = _validate_floor_reference(\n"
        "        path, sha256, env_tag, measurement_head, ratified\n"
        "    )\n"
    )
    discarded = TOKEN_ONLY_C07.replace(
        call,
        "    _validate_floor_reference(\n"
        "        path, sha256, env_tag, measurement_head, ratified\n"
        "    )\n",
        1,
    )
    assert discarded != TOKEN_ONLY_C07
    result = M._evaluate_c07(
        _c07_probe(tmp_path, "c07-discarded-validator", result_source=discarded)
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "result-judge-consumer-incomplete"


def test_c07_dead_validator_assignment_is_not_a_consumer(
    tmp_path: Path,
) -> None:
    call = (
        "    validated = _validate_floor_reference(\n"
        "        path, sha256, env_tag, measurement_head, ratified\n"
        "    )\n"
    )
    dead_assignment = TOKEN_ONLY_C07.replace(
        "    validated = _validate_floor_reference(\n",
        "    discarded_validation = _validate_floor_reference(\n",
        1,
    )
    assert call in TOKEN_ONLY_C07
    assert dead_assignment != TOKEN_ONLY_C07
    result = M._evaluate_c07(
        _c07_probe(
            tmp_path,
            "c07-dead-validator-assignment",
            result_source=dead_assignment,
        )
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "result-judge-consumer-incomplete"


def test_c07_literal_floor_fields_without_verification_are_incomplete(
    tmp_path: Path,
) -> None:
    literal_floor = TOKEN_ONLY_C07
    replacements = {
        '    path = floor_protocol["path"]\n': '    path = "literal-path"\n',
        '    sha256 = floor_protocol["sha256"]\n': '    sha256 = "literal-sha"\n',
        '    source_path = floor_source["path"]\n': '    source_path = "literal-source-path"\n',
        '    source_sha256 = floor_source["sha256"]\n': '    source_sha256 = "literal-source-sha"\n',
        '    env_tag = ratified["env_tag"]\n': '    env_tag = "literal-env"\n',
        '    measurement_head = ratified["frozen_at_head"]\n': '    measurement_head = "literal-head"\n',
    }
    for original, replacement in replacements.items():
        assert literal_floor.count(original) == 1
        literal_floor = literal_floor.replace(original, replacement, 1)
    result = M._evaluate_c07(
        _c07_probe(
            tmp_path,
            "c07-literal-floor-fields",
            result_source=literal_floor,
        )
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "result-judge-consumer-incomplete"


def test_c07_is_registered_and_added_to_negative_controls() -> None:
    assert 7 in M._MACHINE_EVALUATORS
    assert "nc_c07_floor_or_result_cell_removed" in NEGATIVE_CONTROL_CASES


def test_c07_real_result_judge_blob_is_static_only(
    tmp_path: Path,
) -> None:
    result_judge = (
        _ROOT / "orchestrator/campaign/s8c_result_judge.py"
    ).read_text(encoding="utf-8")
    result = M._evaluate_c07(
        _c07_probe(
            tmp_path,
            "c07-real-result-judge",
            result_source=result_judge,
        )
    )
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "completion-proof-not-machine-checkable"


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
    supervisor = (
        imports_and_calls
        + "from .reservation import read_binding, check_reservation\n"
        + """
environ = {}
def run_trial():
    contract = ENV()
    GUARD(contract)
    binding = read_binding(environ)
    check_reservation(binding, required_s=1, safety_margin_s=0, environ=environ)
    return binding
def main(): return run_trial()
"""
    )
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


def _assert_c12_allocation_consumer_absent(
    tmp_path: Path,
    name: str,
    supervisor: str,
    extra_sources: dict[str, str] | None = None,
) -> None:
    sources = _c12_modules(supervisor)
    sources.update(extra_sources or {})
    root = _init_repo(tmp_path)
    for path, source in sources.items():
        _write(root, path, source)
    head = _commit(root, name)
    result = _result(root, head, "C12")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "allocation-enforcement-consumer-absent"


def test_c12_allocation_rejects_import_alias_consumer(tmp_path: Path) -> None:
    supervisor = TOKEN_ONLY_C12.replace(
        "from .reservation import read_binding, check_reservation\n",
        "from .unrelated_decoy import foo as read_binding, bar as check_reservation\n",
    )
    _assert_c12_allocation_consumer_absent(
        tmp_path,
        "C12 import alias allocation decoy",
        supervisor,
        {
            "orchestrator/campaign/unrelated_decoy.py": (
                "def foo(*args): return object()\n"
                "def bar(*args, **kwargs): pass\n"
            ),
        },
    )


def test_c12_allocation_rejects_local_decoy_consumer(tmp_path: Path) -> None:
    supervisor = TOKEN_ONLY_C12.replace(
        "environ = {}",
        "def read_binding(*args):\n"
        "    return object()\n"
        "def check_reservation(*args, **kwargs):\n"
        "    pass\n"
        "environ = {}",
    )
    _assert_c12_allocation_consumer_absent(
        tmp_path,
        "C12 local allocation decoy",
        supervisor,
    )


def test_c12_allocation_rejects_dead_code_after_return(tmp_path: Path) -> None:
    check_and_return = """    check_reservation(
        binding,
        required_s=1,
        safety_margin_s=0,
        environ=environ,
    )
    return binding
"""
    dead_after_return = TOKEN_ONLY_C12.replace(
        check_and_return,
        """    return binding
    check_reservation(
        binding,
        required_s=1,
        safety_margin_s=0,
        environ=environ,
    )
""",
    )
    assert dead_after_return != TOKEN_ONLY_C12
    _assert_c12_allocation_consumer_absent(
        tmp_path,
        "C12 dead allocation check after return",
        dead_after_return,
    )


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


def test_c09_provably_dead_acceptance_call_is_not_a_formal_witness(
    tmp_path: Path,
) -> None:
    sources, registry_path, _ = _negative_control_case(
        "nc_c09_acceptance_skips_layer3"
    )
    layer3_path = "orchestrator/campaign/autonomous_trial_completeness.py"
    sources[layer3_path] = _git(
        _ROOT, "show", f"HEAD:{layer3_path}"
    ).decode("utf-8")
    root, _, positive = _terminal_result(
        tmp_path, "live-acceptance-call", "C09", sources
    )
    assert positive.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert positive.reason_code == "completion-proof-not-machine-checkable"

    assert registry_path == "orchestrator/campaign/trial_registry.py"
    target = "    assert_campaign_layer3_chain()\n"
    registry = sources[registry_path]
    assert isinstance(registry, str)
    assert registry.count(target) == 1
    replacement = "    if False:\n        assert_campaign_layer3_chain()\n"
    mutated = registry.replace(target, replacement, 1)
    assert mutated != registry
    _write(root, registry_path, mutated)
    head = _commit(root, "dead acceptance call")

    negative = _result(root, head, "C09")
    assert negative.status is core.PredicateStatus.UNSATISFIED
    assert negative.reason_code == "formal-acceptance-layer3-consumer-absent"


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
    assert graph_cache_hits == [False, True, False, True]
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
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
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
        "C01", "C02", "C04", "C05", "C06", "C07", "C09", "C10", "C11", "C12"
    }
    assert M.SATISFIABLE_CONDITION_IDS == frozenset({"C10"})
    assert M.SATISFIABLE_CONDITION_IDS <= M.MACHINE_CHECKABLE_CONDITION_IDS
    exercised = 0
    for identifier in machine_checkable:
        exercised += 1
        row = rows[identifier]
        assert row.negative_control_id in NEGATIVE_CONTROL_CASES
        assert NEGATIVE_CONTROL_CASES[row.negative_control_id] == identifier
    assert exercised == 10
    assert set(NEGATIVE_CONTROL_CASES) == {
        rows[identifier].negative_control_id for identifier in machine_checkable
    }


def test_static_negative_controls_equal_non_machine_contract_controls() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    expected = {
        condition.negative_control_id: f"C{condition.condition_number:02d}"
        for condition in contract.conditions
        if not condition.machine_checkable and condition.condition_number in (3, 8)
    }
    assert expected == {
        "nc_c03_manifest_cell_removed": "C03",
        "nc_c08_parent_commit_substitution": "C08",
    }
    assert STATIC_NEGATIVE_CONTROL_CASES == expected
    assert set(STATIC_NEGATIVE_CONTROL_CASES).isdisjoint(NEGATIVE_CONTROL_CASES)


def test_static_negative_control_binds_c03_to_its_contract_case() -> None:
    assert STATIC_NEGATIVE_CONTROL_CASES["nc_c03_manifest_cell_removed"] == "C03"


def test_static_negative_control_binds_c08_to_its_contract_case() -> None:
    assert STATIC_NEGATIVE_CONTROL_CASES["nc_c08_parent_commit_substitution"] == "C08"


@pytest.mark.parametrize(
    "mutation",
    (
        "unexpected-extra-field-path",
        "binding-pair-removed",
        "verifier-literal-removed",
    ),
)
def test_c10_load_bearing_check_requires_live_literals_not_semantic_guards_or_value_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    """literal な常偽枝は除外するが、意味的に常偽の guard と値束縛は証明しない。"""
    assert len(M._C10_CROSS_BINDING_FIELD_BINDINGS) == 13
    assert len(M._C10_FIELDS) == 13
    assert len(M._C10_EXPECTED_FIELD_PATHS) == 13
    root = _init_repo(tmp_path)
    verifier_path = "orchestrator/campaign/autonomous_trial_completeness.py"
    registry_path = "orchestrator/campaign/trial_registry.py"
    _write(root, verifier_path, C10_SATISFIED_VERIFIER)
    _write(root, registry_path, C10_SATISFIED_REGISTRY)
    baseline_head = _commit(root, "C10 production-equivalent 13 of 13")
    baseline = _result(root, baseline_head, "C10")
    assert baseline.status is core.PredicateStatus.SATISFIED
    assert baseline.reason_code == "cross-binding-readiness-satisfied"

    if mutation == "unexpected-extra-field-path":
        contract = json.loads(CONTRACT_FILE.read_bytes())
        requirement = next(
            item
            for item in contract["conditions"][9]["required_evidence"]
            if item["artifact_kind"] == "cross_binding_verifier"
        )
        assert len(requirement["field_paths"]) == 13
        requirement["field_paths"].append("proposal.unimplemented_field")
        assert len(requirement["field_paths"]) == 14
        _write(
            root,
            core.EVIDENCE_CONTRACT_PATH,
            json.dumps(contract, ensure_ascii=False).encode("utf-8"),
        )
        mutated_head = _commit(root, "C10 unexpected fourteenth field path")
    elif mutation == "binding-pair-removed":
        bindings = tuple(
            binding
            for binding in M._C10_CROSS_BINDING_FIELD_BINDINGS
            if binding[0] != "proposal_build_source_bindings"
        )
        assert len(bindings) == 12
        monkeypatch.setattr(M, "_C10_CROSS_BINDING_FIELD_BINDINGS", bindings)
        monkeypatch.setattr(
            M, "_C10_FIELDS", frozenset(literal for literal, _ in bindings)
        )
        monkeypatch.setattr(
            M, "_C10_EXPECTED_FIELD_PATHS", frozenset(path for _, path in bindings)
        )
        mutated_head = baseline_head
    else:
        assert mutation == "verifier-literal-removed"
        _write(
            root,
            verifier_path,
            C10_SATISFIED_VERIFIER.replace(
                '        "proposal_build_source_bindings",\n', "", 1
            ),
        )
        mutated_head = _commit(root, "C10 verifier literal removed")

    mutated = _result(root, mutated_head, "C10")
    assert mutated.status is core.PredicateStatus.UNSATISFIED
    assert mutated.reason_code == "cross-binding-verifier-incomplete"


def test_c10_gate_survives_semantically_false_guard_and_unbound_proposal_value(
    tmp_path: Path,
) -> None:
    """live literal 検査は literal な常偽枝を落とすが、値照合の恒真化は拒否できない。

    定数でない述語による意味的な常偽 guard と値束縛は、producer 側の functional test の責務である。
    """
    raw_response = tmp_path / "raw-response.bin"
    raw_response_bytes = b"fixture raw response"
    raw_response.write_bytes(raw_response_bytes)
    actual = {
        "proposal_build_source_bindings": ["actual"],
        "raw_response_path": str(raw_response),
        "raw_response_sha256": core._sha256(raw_response_bytes),
    }
    expected = {"proposal_build_source_bindings": ["expected"]}
    active_namespace: dict[str, object] = {}
    exec(ACTIVE_VALUE_CHECK_C10, active_namespace)
    active_verify = active_namespace["verify_s8c_cross_binding"]
    assert callable(active_verify)
    with pytest.raises(ValueError, match="proposal_build_source_bindings differs"):
        active_verify(actual, expected)
    neutered_namespace: dict[str, object] = {}
    exec(NEUTERED_VALUE_CHECK_C10, neutered_namespace)
    neutered_verify = neutered_namespace["verify_s8c_cross_binding"]
    assert callable(neutered_verify)
    neutered_fields = neutered_verify(actual, expected)
    assert "proposal_build_source_bindings" in neutered_fields

    results: dict[str, core.PredicateResult] = {}
    for name, source in (
        ("active-value-check", ACTIVE_VALUE_CHECK_C10),
        ("neutered-value-check", NEUTERED_VALUE_CHECK_C10),
    ):
        root = _init_repo(tmp_path, name)
        _write(
            root,
            "orchestrator/campaign/autonomous_trial_completeness.py",
            source,
        )
        _write(
            root,
            "orchestrator/campaign/trial_registry.py",
            C10_SATISFIED_REGISTRY,
        )
        head = _commit(root, f"C10 {name}")
        results[name] = _result(root, head, "C10")

    assert results["active-value-check"].status is core.PredicateStatus.SATISFIED
    assert results["active-value-check"].reason_code == (
        "cross-binding-readiness-satisfied"
    )
    assert results["neutered-value-check"].status is core.PredicateStatus.SATISFIED
    assert results["neutered-value-check"].reason_code == (
        "cross-binding-readiness-satisfied"
    )


@pytest.mark.parametrize(
    ("negative_control_id", "identifier"),
    tuple(
        (negative_control_id, identifier)
        for negative_control_id, identifier in NEGATIVE_CONTROL_CASES.items()
        if identifier != "C10"
    ),
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
        "C05": "schedule-consumer-unreachable",
        "C06": "budget-consumer-contract-undefined",
        "C07": "result-judge-consumer-incomplete",
        "C09": "formal-acceptance-layer3-consumer-absent",
        "C10": "cross-binding-verifier-incomplete",
        "C11": "generation-cap-not-lifted",
        "C12": "allocation-enforcement-consumer-absent",
    }
    assert mutated_result.status is core.PredicateStatus.UNSATISFIED
    assert mutated_result.reason_code == expected_reasons[identifier]


def test_c04_rejects_missing_started_trial_preflight(tmp_path: Path) -> None:
    sources, _, _ = _negative_control_case("nc_c04_partial_crash_survives")
    p3 = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    registry = "orchestrator/campaign/trial_registry.py"
    source = sources[p3]
    registry_source = sources[registry]
    assert isinstance(source, str)
    assert isinstance(registry_source, str)
    root, _, _ = _terminal_result(
        tmp_path,
        "c04-reject-started-baseline",
        "C04",
        {p3: source, registry: registry_source},
    )
    preflight_call = "    reject_started_trial()\n"
    assert source.count(preflight_call) == 1

    mutated_source = source.replace(preflight_call, "", 1)
    assert mutated_source.count(preflight_call) == 0
    assert (
        mutated_source.count("from .trial_registry import reject_started_trial\n")
        == 1
    )
    assert mutated_source.count("        mark_experiment_indeterminate()\n") == 1
    assert mutated_source.count("        forbid_trial_restart()\n") == 1
    assert registry_source.count("def forbid_trial_restart()") == 1
    assert registry_source.count("def reject_started_trial()") == 1

    _write(root, p3, mutated_source)
    head = _commit(root, "C04 reject-started preflight removed")
    result = _result(root, head, "C04")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "crash-policy-cell-partial"


def test_c10_token_only_fixture_never_satisfies(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    verifier = "orchestrator/campaign/autonomous_trial_completeness.py"
    registry = "orchestrator/campaign/trial_registry.py"
    _write(root, verifier, TOKEN_ONLY_C10)
    _write(root, registry, TOKEN_ONLY_C10_REGISTRY)
    head = _commit(root, "C10 token-only no-op reader")

    result = _result(root, head, "C10")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "cross-binding-verifier-incomplete"


def test_c10_registered_negative_control_pairs_with_satisfied_fixture(
    tmp_path: Path,
) -> None:
    control_id = "nc_c10_raw_response_unbound"
    assert NEGATIVE_CONTROL_CASES[control_id] == "C10"
    sources, mutated_path, mutated_source = _negative_control_case(control_id)
    root = _init_repo(tmp_path)
    for path, source in sources.items():
        _write(root, path, source)
    baseline = _commit(root, "C10 substantive readiness fixture")
    baseline_result = _result(root, baseline, "C10")
    assert baseline_result.status is core.PredicateStatus.SATISFIED
    assert baseline_result.reason_code == "cross-binding-readiness-satisfied"

    _write(root, mutated_path, mutated_source)
    mutated = _commit(root, "C10 raw response digest unbound")
    mutated_result = _result(root, mutated, "C10")
    assert mutated_result.status is core.PredicateStatus.UNSATISFIED
    assert mutated_result.reason_code == "cross-binding-verifier-incomplete"


_C10_READER_CALL = """    raw = read_and_verify_bytes(
        event.get("raw_response_path"),
        expected_sha256=event.get("raw_response_sha256"),
    )
"""


C10_SINGLE_REASON_READER_VERIFIER = C10_SATISFIED_VERIFIER.replace(
    "def verify_s8c_cross_binding(event):\n",
    """class NamedReaderDecoy:
    @staticmethod
    def read_and_verify_bytes(event):
        return b"decoy"

named_reader_decoy = NamedReaderDecoy()

def verify_s8c_cross_binding(event):
""",
    1,
).replace(
    '        "admission_decision",\n',
    '        "admission_decision", "raw_response_path", "raw_response_sha256",\n',
    1,
).replace(
    _C10_READER_CALL,
    """    raw = named_reader_decoy.read_and_verify_bytes(event)
    if False:
        raw = read_and_verify_bytes(
            event.get("raw_response_path"),
            expected_sha256=event.get("raw_response_sha256"),
        )
""",
    1,
)

C10_SINGLE_REASON_ACCEPTANCE_REGISTRY = """
from .autonomous_trial_completeness import verify_s8c_cross_binding

class NamedVerifierDecoy:
    @staticmethod
    def verify_s8c_cross_binding(event):
        return {"decoy": True}

named_verifier_decoy = NamedVerifierDecoy()

def assert_trial_registry_acceptance(event):
    receipt = named_verifier_decoy.verify_s8c_cross_binding(event)
    if False:
        receipt = verify_s8c_cross_binding(event)
    return {"cross_binding_receipt_sha256": receipt}
"""

C10_SUPPRESSED_REGISTRY = """
from contextlib import suppress as ignore_verifier_failure
from .autonomous_trial_completeness import verify_s8c_cross_binding

def assert_trial_registry_acceptance(event):
    with ignore_verifier_failure(Exception):
        receipt = verify_s8c_cross_binding(event)
    return {"cross_binding_receipt_sha256": receipt}
"""

C10_GENERAL_WITH_REGISTRY = """
from contextlib import nullcontext as acceptance_scope
from .autonomous_trial_completeness import verify_s8c_cross_binding

def assert_trial_registry_acceptance(event):
    with acceptance_scope():
        receipt = verify_s8c_cross_binding(event)
    return {"cross_binding_receipt_sha256": receipt}
"""


@pytest.mark.parametrize(
    ("mutated_path", "mutated_source", "expected_reason"),
    (
        pytest.param(
            "orchestrator/campaign/autonomous_trial_completeness.py",
            C10_SATISFIED_VERIFIER.replace(
                _C10_READER_CALL,
                """    if False:
        raw = read_and_verify_bytes(
            event.get("raw_response_path"),
            expected_sha256=event.get("raw_response_sha256"),
        )
""",
                1,
            ),
            "cross-binding-verifier-incomplete",
            id="N2-reader-literal-dead-branch",
        ),
        pytest.param(
            "orchestrator/campaign/autonomous_trial_completeness.py",
            C10_SATISFIED_VERIFIER.replace(
                "def verify_s8c_cross_binding(event):\n",
                """def harmless_reader(*args, **kwargs):
    return b""

read_and_verify_bytes = harmless_reader

def verify_s8c_cross_binding(event):
""",
                1,
            ),
            "cross-binding-verifier-incomplete",
            id="N3-reader-alias-decoy",
        ),
        pytest.param(
            "orchestrator/campaign/autonomous_trial_completeness.py",
            TOKEN_ONLY_C10,
            "cross-binding-verifier-incomplete",
            id="N4-reader-no-op",
        ),
        pytest.param(
            "orchestrator/campaign/autonomous_trial_completeness.py",
            C10_SINGLE_REASON_READER_VERIFIER,
            "cross-binding-verifier-incomplete",
            id="N2-single-reader-live-exact-call",
        ),
        pytest.param(
            "orchestrator/campaign/trial_registry.py",
            C10_SATISFIED_REGISTRY.replace(
                "        receipt = verify_s8c_cross_binding(event)\n",
                """        if False:
            receipt = verify_s8c_cross_binding(event)
""",
                1,
            ),
            "cross-binding-acceptance-unreachable",
            id="N5-acceptance-literal-dead-branch",
        ),
        pytest.param(
            "orchestrator/campaign/trial_registry.py",
            C10_SATISFIED_REGISTRY.replace(
                "def assert_trial_registry_acceptance(event):\n",
                """def harmless_verifier(event):
    return {}

verify_s8c_cross_binding = harmless_verifier

def assert_trial_registry_acceptance(event):
""",
                1,
            ),
            "cross-binding-acceptance-unreachable",
            id="N6-acceptance-alias-decoy",
        ),
        pytest.param(
            "orchestrator/campaign/trial_registry.py",
            C10_SATISFIED_REGISTRY.replace(
                '        raise RuntimeError("cross binding failed") from exc\n',
                "        pass\n",
                1,
            ),
            "cross-binding-acceptance-unreachable",
            id="N7-acceptance-catch-and-continue",
        ),
        pytest.param(
            "orchestrator/campaign/trial_registry.py",
            C10_SINGLE_REASON_ACCEPTANCE_REGISTRY,
            "cross-binding-acceptance-unreachable",
            id="N5-single-acceptance-live-exact-call",
        ),
        pytest.param(
            "orchestrator/campaign/trial_registry.py",
            C10_SUPPRESSED_REGISTRY,
            "cross-binding-acceptance-unreachable",
            id="N8-acceptance-suppress-context-manager",
        ),
    ),
)
def test_c10_readiness_rejects_registered_spoof_classes(
    tmp_path: Path,
    mutated_path: str,
    mutated_source: str,
    expected_reason: str,
) -> None:
    verifier = "orchestrator/campaign/autonomous_trial_completeness.py"
    registry = "orchestrator/campaign/trial_registry.py"
    root = _init_repo(tmp_path)
    _write(root, verifier, C10_SATISFIED_VERIFIER)
    _write(root, registry, C10_SATISFIED_REGISTRY)
    baseline = _commit(root, "C10 readiness baseline")
    baseline_result = _result(root, baseline, "C10")
    assert baseline_result.status is core.PredicateStatus.SATISFIED
    assert baseline_result.reason_code == "cross-binding-readiness-satisfied"

    _write(root, mutated_path, mutated_source)
    mutated = _commit(root, "C10 spoof mutation")
    mutated_result = _result(root, mutated, "C10")
    assert mutated_result.status is core.PredicateStatus.UNSATISFIED
    assert mutated_result.reason_code == expected_reason


def _c10_probe(
    tmp_path: Path,
    name: str,
    *,
    verifier_source: str = C10_SATISFIED_VERIFIER,
    registry_source: str = C10_SATISFIED_REGISTRY,
) -> M._ConditionProbe:
    root = _init_repo(tmp_path, name)
    _write(
        root,
        "orchestrator/campaign/autonomous_trial_completeness.py",
        verifier_source,
    )
    _write(root, "orchestrator/campaign/trial_registry.py", registry_source)
    head = _commit(root, name)
    contract_raw = core.read_blob_at(
        root, head, core.EVIDENCE_CONTRACT_PATH, required=True
    )
    contract = M.load_contract_bytes(contract_raw)
    return M._ConditionProbe(
        root,
        head,
        contract.condition(10),
        core.EvidenceRef(
            core.EVIDENCE_CONTRACT_PATH,
            core._sha256(contract_raw),
        ),
        {},
        {},
        declared_paths=contract.evidence_paths,
    )


def _c10_readiness_checks(probe: M._ConditionProbe) -> dict[str, bool]:
    verifier = probe.python_kind("cross_binding_verifier")
    assert verifier is not None
    verifier_path = probe.requirement("cross_binding_verifier").path
    verify = M._c10_single_function(verifier, "verify_s8c_cross_binding")
    reader = M._c10_single_function(verifier, "read_and_verify_bytes")
    assert verify is not None
    assert reader is not None
    live_strings = {
        node.value
        for node in M._live_nodes(verify)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    reader_calls = M._calls_named(verify, "read_and_verify_bytes")
    verifier_graph = M._ReachabilityExplorer(probe).walk(
        (verifier_path, "verify_s8c_cross_binding")
    )

    registry = probe.python_kind("trial_registry")
    assert registry is not None
    registry_path = probe.requirement("trial_registry").path
    accept = M._functions(registry).get("assert_trial_registry_acceptance")
    assert accept is not None
    acceptance_calls = M._calls_named(accept, "verify_s8c_cross_binding")
    acceptance_graph = M._ReachabilityExplorer(probe).walk(
        (registry_path, "assert_trial_registry_acceptance")
    )
    return {
        "verifier-single-definition": verify is not None,
        "reader-single-definition": reader is not None,
        "reader-not-noop": M._c10_reader_is_not_noop(reader),
        "fields-live": M._C10_FIELDS <= live_strings,
        "reader-named-live-call": bool(reader_calls),
        "reader-exact-live-call": M._declared_call(
            probe,
            verifier_graph,
            (verifier_path, "read_and_verify_bytes"),
        ),
        "acceptance-definition": accept is not None,
        "acceptance-named-live-call": bool(acceptance_calls),
        "acceptance-exact-live-call": M._declared_call(
            probe,
            acceptance_graph,
            (verifier_path, "verify_s8c_cross_binding"),
        ),
        "acceptance-not-catch-and-continue": all(
            M._c10_call_is_not_catch_and_continue(registry, accept, call)
            for call in acceptance_calls
        ),
    }


@pytest.mark.parametrize(
    ("name", "verifier_source", "registry_source", "sole_failed_check", "reason"),
    (
        pytest.param(
            "c10-reader-live-exact-only",
            C10_SINGLE_REASON_READER_VERIFIER,
            C10_SATISFIED_REGISTRY,
            "reader-exact-live-call",
            "cross-binding-verifier-incomplete",
            id="N2-single-reader-live-exact-call",
        ),
        pytest.param(
            "c10-acceptance-live-exact-only",
            C10_SATISFIED_VERIFIER,
            C10_SINGLE_REASON_ACCEPTANCE_REGISTRY,
            "acceptance-exact-live-call",
            "cross-binding-acceptance-unreachable",
            id="N5-single-acceptance-live-exact-call",
        ),
    ),
)
def test_c10_single_reason_fixtures_fail_only_the_intended_check(
    tmp_path: Path,
    name: str,
    verifier_source: str,
    registry_source: str,
    sole_failed_check: str,
    reason: str,
) -> None:
    probe = _c10_probe(
        tmp_path,
        name,
        verifier_source=verifier_source,
        registry_source=registry_source,
    )
    checks = _c10_readiness_checks(probe)
    assert {check for check, passed in checks.items() if not passed} == {
        sole_failed_check
    }
    result = M._evaluate_c10(probe)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == reason


@pytest.mark.parametrize(
    ("import_line", "context_expression"),
    (
        pytest.param(
            "import contextlib",
            "contextlib.suppress",
            id="contextlib-suppress",
        ),
        pytest.param(
            "import contextlib as error_handling",
            "error_handling.suppress",
            id="contextlib-module-alias",
        ),
        pytest.param(
            "from contextlib import suppress",
            "suppress",
            id="suppress-direct-import",
        ),
        pytest.param(
            "from contextlib import suppress as ignore_failure",
            "ignore_failure",
            id="suppress-import-alias",
        ),
    ),
)
def test_c10_suppress_context_manager_spellings_are_rejected(
    tmp_path: Path,
    import_line: str,
    context_expression: str,
) -> None:
    registry_source = f"""
{import_line}
from .autonomous_trial_completeness import verify_s8c_cross_binding

def assert_trial_registry_acceptance(event):
    with {context_expression}(Exception):
        receipt = verify_s8c_cross_binding(event)
    return {{"cross_binding_receipt_sha256": receipt}}
"""
    probe = _c10_probe(
        tmp_path,
        f"c10-suppress-{context_expression}",
        registry_source=registry_source,
    )
    result = M._evaluate_c10(probe)
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "cross-binding-acceptance-unreachable"


def test_c10_general_with_context_manager_remains_satisfied(tmp_path: Path) -> None:
    probe = _c10_probe(
        tmp_path,
        "c10-general-with",
        registry_source=C10_GENERAL_WITH_REGISTRY,
    )
    result = M._evaluate_c10(probe)
    assert result.status is core.PredicateStatus.SATISFIED
    assert result.reason_code == "cross-binding-readiness-satisfied"


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


def test_non_machine_c03_satisfied_is_rejected_by_runtime_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _init_repo(tmp_path)
    head = _commit(root, "spuriously satisfied non-machine C03")

    def spuriously_satisfied(probe: M._ConditionProbe) -> core.PredicateResult:
        return M._result(
            probe,
            core.PredicateStatus.SATISFIED,
            M.ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )

    monkeypatch.setattr(M, "_evaluate_c03", spuriously_satisfied)
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.ERROR
    assert result.reason_code == "evaluator-internal-error"


def test_non_machine_c08_satisfied_is_rejected_by_runtime_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _init_repo(tmp_path)
    head = _commit(root, "spuriously satisfied non-machine C08")

    def spuriously_satisfied(probe: M._ConditionProbe) -> core.PredicateResult:
        return M._result(
            probe,
            core.PredicateStatus.SATISFIED,
            M.ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )

    monkeypatch.setattr(M, "_evaluate_c08", spuriously_satisfied)
    result = _result(root, head, "C08")
    assert result.status is core.PredicateStatus.ERROR
    assert result.reason_code == "evaluator-internal-error"


def test_c03_negative_control_rejects_manifest_cell_check_removal(
    tmp_path: Path,
) -> None:
    sources, mutated_path, mutated_source = _negative_control_case(
        "nc_c03_manifest_cell_removed"
    )
    root = _init_repo(tmp_path)
    for path, source in sources.items():
        _write(root, path, source)
    token_only = _commit(root, "token only C03")
    token_result = _result(root, token_only, "C03")
    assert token_result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert token_result.reason_code == "manifest-registry-proof-undefined"

    _write(root, mutated_path, mutated_source)
    mutated = _commit(root, "mutated token only nc_c03_manifest_cell_removed")
    result = _result(root, mutated, "C03")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "manifest-registry-proof-undefined"


def test_c08_negative_control_rejects_parent_commit_substitution(
    tmp_path: Path,
) -> None:
    sources, mutated_path, mutated_source = _negative_control_case(
        "nc_c08_parent_commit_substitution"
    )
    root = _init_repo(tmp_path)
    for path, source in sources.items():
        _write(root, path, source)
    token_only = _commit(root, "token only C08")
    token_result = _result(root, token_only, "C08")
    assert token_result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert token_result.reason_code == "prereg-binding-proof-undefined"

    _write(root, mutated_path, mutated_source)
    mutated = _commit(root, "mutated token only nc_c08_parent_commit_substitution")
    result = _result(root, mutated, "C08")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "prereg-binding-proof-undefined"


def test_c03_negative_control_rejects_deterministic_false_strict_branch(
    tmp_path: Path,
) -> None:
    sources = {
        "orchestrator/campaign/trial_registry.py": TOKEN_ONLY_C03_REGISTRY,
        "orchestrator/campaign/p3_autonomous_workload_trial.py": TOKEN_ONLY_C03_PRODUCER,
    }
    root, _head, _baseline = _terminal_result(
        tmp_path,
        "c03-deterministic-false-baseline",
        "C03",
        sources,
        expected_reason="manifest-registry-proof-undefined",
    )
    anchor = """def _assert_manifest_registry_trial_set(manifest, registration):
    expected = tuple(_trial_canonical_tuple(item) for item in manifest.trials)
    actual = tuple(_trial_canonical_tuple(item) for item in registration.trials)
    if len(actual) != len(expected) or set(actual) != set(expected):
        raise ValueError("manifest registry set mismatch")
"""
    replacement = """def _assert_manifest_registry_trial_set(manifest, registration):
    if bool(0):
        expected = tuple(_trial_canonical_tuple(item) for item in manifest.trials)
        actual = tuple(_trial_canonical_tuple(item) for item in registration.trials)
        if len(actual) != len(expected) or set(actual) != set(expected):
            raise ValueError("manifest registry set mismatch")
"""
    assert TOKEN_ONLY_C03_REGISTRY.count(anchor) == 1
    _write(
        root,
        "orchestrator/campaign/trial_registry.py",
        TOKEN_ONLY_C03_REGISTRY.replace(anchor, replacement, 1),
    )
    head = _commit(root, "C03 deterministic false strict branch")
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "manifest-registry-proof-undefined"


def test_c03_producer_reachability_requires_classification_and_terminal(
    tmp_path: Path,
) -> None:
    sources = {
        "orchestrator/campaign/trial_registry.py": TOKEN_ONLY_C03_REGISTRY,
        "orchestrator/campaign/p3_autonomous_workload_trial.py": TOKEN_ONLY_C03_PRODUCER,
    }
    root, _head, _baseline = _terminal_result(
        tmp_path,
        "c03-producer-reachability-baseline",
        "C03",
        sources,
        expected_reason="manifest-registry-proof-undefined",
    )
    anchor = """def _record_attempt_terminal_for_run():
    trial_registry.classify_attempt()
    trial_registry.begin_attempt_observation()
    trial_registry.record_attempt_terminal()
"""
    replacement = """def _record_attempt_terminal_for_run():
    pass
"""
    assert TOKEN_ONLY_C03_PRODUCER.count(anchor) == 1
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        TOKEN_ONLY_C03_PRODUCER.replace(anchor, replacement, 1),
    )
    head = _commit(root, "C03 producer classification terminal bypass")
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "manifest-registry-proof-undefined"


def test_c08_negative_control_rejects_deterministic_false_binding_branch(
    tmp_path: Path,
) -> None:
    sources = {"orchestrator/campaign/trial_registry.py": TOKEN_ONLY_C08_REGISTRY}
    root, _head, _baseline = _terminal_result(
        tmp_path,
        "c08-deterministic-false-baseline",
        "C08",
        sources,
        expected_reason="prereg-binding-proof-undefined",
    )
    anchor = """    assert_effective_commit_exact_parent(
        repository_root,
        content_commit=binding.prereg_content_commit,
        effective_commit=effective_commit,
    )
"""
    replacement = """    if bool(0):
        assert_effective_commit_exact_parent(
            repository_root,
            content_commit=binding.prereg_content_commit,
            effective_commit=effective_commit,
        )
"""
    assert TOKEN_ONLY_C08_REGISTRY.count(anchor) == 1
    _write(
        root,
        "orchestrator/campaign/trial_registry.py",
        TOKEN_ONLY_C08_REGISTRY.replace(anchor, replacement, 1),
    )
    head = _commit(root, "C08 deterministic false binding branch")
    result = _result(root, head, "C08")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "prereg-binding-proof-undefined"


def test_c03_acceptance_legacy_bypass_is_unsatisfied(tmp_path: Path) -> None:
    sources = {
        "orchestrator/campaign/trial_registry.py": TOKEN_ONLY_C03_REGISTRY,
        "orchestrator/campaign/p3_autonomous_workload_trial.py": TOKEN_ONLY_C03_PRODUCER,
    }
    root, _, _ = _terminal_result(
        tmp_path,
        "c03-legacy-baseline",
        "C03",
        sources,
        expected_reason="manifest-registry-proof-undefined",
    )
    anchor = "def assert_trial_registry_acceptance(*, manifest_path, registration, loaded, report):\n"
    assert TOKEN_ONLY_C03_REGISTRY.count(anchor) == 1
    mutated_source = TOKEN_ONLY_C03_REGISTRY.replace(
        anchor,
        anchor + "    if legacy_mode:\n        return old_acceptance()\n",
        1,
    )
    _write(root, "orchestrator/campaign/trial_registry.py", mutated_source)
    head = _commit(root, "C03 legacy acceptance bypass")
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "manifest-registry-proof-undefined"


def test_c03_acceptance_requires_independent_runtime_cell_route(
    tmp_path: Path,
) -> None:
    sources = {
        "orchestrator/campaign/trial_registry.py": TOKEN_ONLY_C03_REGISTRY,
        "orchestrator/campaign/p3_autonomous_workload_trial.py": TOKEN_ONLY_C03_PRODUCER,
    }
    root, _, _ = _terminal_result(
        tmp_path,
        "c03-cell-route-baseline",
        "C03",
        sources,
        expected_reason="manifest-registry-proof-undefined",
    )
    anchor = "    _assert_runtime_report_cells(report, trial=manifest.trials[0])\n"
    assert TOKEN_ONLY_C03_REGISTRY.count(anchor) == 1
    mutated_source = TOKEN_ONLY_C03_REGISTRY.replace(anchor, "", 1)
    _write(root, "orchestrator/campaign/trial_registry.py", mutated_source)
    head = _commit(root, "C03 runtime cell route removed")
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "manifest-registry-proof-undefined"


def test_c03_noop_helpers_do_not_prove_manifest_registry(tmp_path: Path) -> None:
    names = (
        "load_trial_manifest",
        "load_effective_binding_at_commit",
        "validate_preregistration_binding",
        "_find_registration_for_manifest",
        "_assert_manifest_registry_trial_set",
        "_assert_runtime_report_trial_set",
        "_assert_runtime_report_cells",
        "load_attempt_registry",
        "reserve_attempt_slot",
        "assert_trial_registry_acceptance",
        "begin_attempt_observation",
    )
    noop = "\n".join(
        f"def {name}(*args, **kwargs): pass" for name in names
    ) + "\n"
    root = _init_repo(tmp_path)
    _write(root, "orchestrator/campaign/trial_registry.py", noop)
    _write(
        root,
        "orchestrator/campaign/p3_autonomous_workload_trial.py",
        TOKEN_ONLY_C03_PRODUCER,
    )
    head = _commit(root, "C03 noop helpers")
    result = _result(root, head, "C03")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "manifest-registry-proof-undefined"


def test_c08_noop_helpers_do_not_prove_prereg_binding(tmp_path: Path) -> None:
    names = (
        "_blob_at_commit",
        "_assert_ancestor",
        "assert_effective_commit_exact_parent",
        "load_effective_binding_at_commit",
        "validate_preregistration_binding",
        "_derive_launch_binding",
        "load_launch_binding",
        "admit_registered_launch",
        "assert_trial_registry_acceptance",
    )
    noop = "\n".join(
        f"def {name}(*args, **kwargs): pass" for name in names
    ) + "\n"
    root = _init_repo(tmp_path)
    _write(root, "orchestrator/campaign/trial_registry.py", noop)
    head = _commit(root, "C08 noop helpers")
    result = _result(root, head, "C08")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "prereg-binding-proof-undefined"


def test_c03_dispatch_trace_never_calls_machine_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def traced(probe: M._ConditionProbe) -> core.PredicateResult:
        calls.append(probe.contract.identifier)
        return M._result(
            probe,
            core.PredicateStatus.SATISFIED,
            M.ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
        )

    monkeypatch.setitem(M._MACHINE_EVALUATORS, 3, traced)
    root = _init_repo(tmp_path)
    head = _commit(root, "C03 dispatch trace")
    result = _result(root, head, "C03")
    assert calls == []
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "trial-registry-capability-absent"


def test_c08_dispatch_trace_never_calls_machine_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def traced(probe: M._ConditionProbe) -> core.PredicateResult:
        calls.append(probe.contract.identifier)
        return M._result(
            probe,
            core.PredicateStatus.SATISFIED,
            M.ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
        )

    monkeypatch.setitem(M._MACHINE_EVALUATORS, 8, traced)
    root = _init_repo(tmp_path)
    head = _commit(root, "C08 dispatch trace")
    result = _result(root, head, "C08")
    assert calls == []
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "prereg-binding-capability-absent"


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


def test_historical_c08_machine_checkable_contract_fails_closed(
    tmp_path: Path,
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    value["conditions"][7]["machine_checkable"] = True
    root = _init_repo(tmp_path)
    _write(
        root,
        core.EVIDENCE_CONTRACT_PATH,
        json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )
    head = _commit(root, "C08 falsely marked machine checkable")

    result = _result(root, head, "C08")
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


def _current_head_c05_probe() -> M._ConditionProbe:
    contract_raw = CONTRACT_FILE.read_bytes()
    contract = M.load_contract_bytes(contract_raw)
    condition = contract.condition(5)
    paths = {
        item.artifact_kind: item.path for item in condition.required_evidence
    }
    artifact_path = paths["schedule_artifact"]
    consumer_path = paths["schedule_consumer"]
    workload_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    artifact = S.regenerate("c05-direct-probe", authority=_c05_authority())
    consumer_raw = (_ROOT / consumer_path).read_bytes()
    workload_raw = _git(_ROOT, "show", f"HEAD:{workload_path}")
    return M._ConditionProbe(
        _ROOT,
        "HEAD",
        condition,
        core.EvidenceRef(
            core.EVIDENCE_CONTRACT_PATH,
            core._sha256(contract_raw),
        ),
        {},
        {
            artifact_path: artifact,
            consumer_path: consumer_raw,
            workload_path: workload_raw,
        },
        python_cache={
            consumer_path: ast.parse(
                consumer_raw.decode("utf-8"), filename=consumer_path
            ),
            workload_path: ast.parse(
                workload_raw.decode("utf-8"), filename=workload_path
            ),
        },
        declared_paths=contract.evidence_paths,
    )


def test_c05_direct_evaluator_reports_current_head_unreachable() -> None:
    result = M._evaluate_c05(_current_head_c05_probe())
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "schedule-consumer-unreachable"


def test_c05_evaluator_reports_undefined_when_consumer_commit_module_is_absent(
    tmp_path: Path,
) -> None:
    contract_raw = CONTRACT_FILE.read_bytes()
    contract = M.load_contract_bytes(contract_raw)
    condition = contract.condition(5)
    paths = {
        item.artifact_kind: item.path
        for item in condition.required_evidence
    }
    artifact_path = paths["schedule_artifact"]
    consumer_path = paths["schedule_consumer"]
    artifact = S.regenerate("c05-consumer-absent", authority=_c05_authority())
    root = _init_repo(tmp_path, "c05-consumer-absent")
    _write(root, artifact_path, artifact)
    commit = _commit(root, "C05 artifact without consumer module")
    probe = M._ConditionProbe(
        root,
        commit,
        condition,
        core.EvidenceRef(
            core.EVIDENCE_CONTRACT_PATH,
            core._sha256(contract_raw),
        ),
        {},
        {
            artifact_path: artifact,
            consumer_path: None,
        },
        declared_paths=contract.evidence_paths,
    )

    result = M._evaluate_c05(probe)
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "schedule-consumer-undefined"


@pytest.mark.parametrize(
    ("negative_control_id", "identifier"),
    [("nc_c05_initial_state_hash_bitflip", "C05")],
)
def test_c05_initial_state_hash_bitflip_is_single_shared_layer_failure(
    negative_control_id: str, identifier: str
) -> None:
    assert negative_control_id == "nc_c05_initial_state_hash_bitflip"
    assert identifier == "C05"
    authority = _c05_authority()
    master_seed = "c05-negative-control"
    baseline = S.regenerate(master_seed, authority=authority)
    schedule = S.verify_schedule(
        baseline,
        master_seed=master_seed,
        authority=authority,
    )
    expected_search = S.search_space_digest(authority)
    expected_initial = S.initial_state_digest(authority)
    assert all(cell.search_space_sha256 == expected_search for cell in schedule.cells)
    assert all(cell.initial_state_sha256 == expected_initial for cell in schedule.cells)

    flipped_bytes = bytearray.fromhex(expected_initial)
    flipped_bytes[0] ^= 0x01
    flipped_initial = bytes(flipped_bytes).hex()
    assert (
        int(expected_initial, 16) ^ int(flipped_initial, 16)
    ).bit_count() == 1
    assert expected_initial[2:] == flipped_initial[2:]

    with pytest.raises(S.ScheduleError):
        S.verify_shared_search_space_and_initial_state(
            schedule,
            expected_search_space_sha256=expected_search,
            expected_initial_state_sha256=flipped_initial,
        )
    S.verify_exact_schedule_bytes(
        baseline,
        master_seed=master_seed,
        authority=authority,
    )


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


TOKEN_ONLY_C06_BUDGET = """
import os
from dataclasses import dataclass
from typing import Literal, Mapping

@dataclass(frozen=True, slots=True)
class BudgetLimits:
    total_bench_s: float
    per_arm_bench_s: Mapping[str, float]
    per_holdout_bench_s: Mapping[str, float]

@dataclass(frozen=True, slots=True)
class ReservationCell:
    cell_id: str
    holdout: str
    arm: str
    reserved_bench_s: float

@dataclass(frozen=True, slots=True)
class Reservation:
    cells: tuple[ReservationCell, ...]
    budget_bench_s: float
    total_reserved_bench_s: float
    state: Literal["held", "insufficient"]

@dataclass(frozen=True, slots=True)
class SettlementCell:
    cell_id: str
    actual_bench_s: float

@dataclass(frozen=True, slots=True)
class Settlement:
    cells: tuple[SettlementCell, ...]
    total_actual_bench_s: float

@dataclass(frozen=True, slots=True)
class Ledger:
    manifest_sha256: str
    freeze_sha256: str
    schedule_sha256: str
    ratified_generation_sha256: str
    reservation: Reservation
    settlement: Settlement
    cell_ids: frozenset[str]

_EXPECTED_CELL_ROWS = (
    ("H1", "on"),
    ("H1", "off"),
    ("H1", "swapped"),
    ("H2", "on"),
    ("H2", "off"),
    ("H2", "swapped"),
)

def _ledger_lock():
    return os.O_CREAT | os.O_EXCL

def _check_limit_state(cells, limits):
    total_reserved_bench_s = sum(cell.reserved_bench_s for cell in cells)
    total_ok = total_reserved_bench_s <= limits.total_bench_s
    arm_ok = all(value <= limits.per_arm_bench_s[arm] for arm, value in {})
    holdout_ok = all(value <= limits.per_holdout_bench_s[holdout] for holdout, value in {})
    return total_ok and arm_ok and holdout_ok

def _make_limits():
    return BudgetLimits(1.0, {}, {})

def _make_cells():
    return (
        ReservationCell("cell", "H1", "on", 0.0),
        SettlementCell("cell", 0.0),
    )

def reserve_all_cells(ledger_path, *, manifest_sha256, freeze_sha256,
                      schedule_sha256, ratified_generation_sha256,
                      cells, limits):
    _ledger_lock()
    cells = tuple(cells)
    state = "held" if _check_limit_state(cells, limits) else "insufficient"
    reservation = Reservation(cells, limits.total_bench_s,
                              sum(cell.reserved_bench_s for cell in cells), state)
    settlement = Settlement(tuple(), 0.0)
    return Ledger(manifest_sha256, freeze_sha256, schedule_sha256,
                  ratified_generation_sha256, reservation, settlement,
                  frozenset(cell.cell_id for cell in cells))

def settle(ledger_path, *, cell_id, actual_bench_s):
    _ledger_lock()
    if actual_bench_s <= 1.0:
        return ledger_path
    raise RuntimeError("actual_bench_s")

def symmetric_indeterminate(ledger, *, launched_cell_ids=()):
    if ledger.reservation.state == "insufficient":
        return frozenset(ledger.cell_ids) - frozenset(launched_cell_ids)
    return frozenset()

def _document(ledger, limits):
    return {
        "schema_version": "s8c-budget-ledger/v1",
        "manifest_sha256": ledger.manifest_sha256,
        "freeze_sha256": ledger.freeze_sha256,
        "schedule_sha256": ledger.schedule_sha256,
        "ratified_generation_sha256": ledger.ratified_generation_sha256,
        "reservation": {
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "holdout": cell.holdout,
                    "arm": cell.arm,
                    "reserved_bench_s": cell.reserved_bench_s,
                }
                for cell in ledger.reservation.cells
            ],
            "budget_bench_s": ledger.reservation.budget_bench_s,
            "total_reserved_bench_s": ledger.reservation.total_reserved_bench_s,
            "state": ledger.reservation.state,
            "limits": {
                "total_bench_s": limits.total_bench_s,
                "per_arm_bench_s": dict(limits.per_arm_bench_s),
                "per_holdout_bench_s": dict(limits.per_holdout_bench_s),
            },
        },
        "settlement": {
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "actual_bench_s": cell.actual_bench_s,
                }
                for cell in ledger.settlement.cells
            ],
            "total_actual_bench_s": ledger.settlement.total_actual_bench_s,
        },
        "cell_ids": sorted(ledger.cell_ids),
    }
"""

TOKEN_ONLY_C06_BUDGET_MISSING_LIMIT_CHECK = TOKEN_ONLY_C06_BUDGET.replace(
    'state = "held" if _check_limit_state(cells, limits) else "insufficient"',
    'state = "held"',
)

TOKEN_ONLY_C06_RATIFIED = """
class Ratified:
    sha256 = "a" * 64
    sha256_field = "sha256"
def load_ratified_freeze():
    return Ratified()
"""

TOKEN_ONLY_C06_SUPERVISOR = """
from .s8b_ratified_freeze import load_ratified_freeze
from .s8c_budget import reserve_all_cells, settle, symmetric_indeterminate
def _budget():
    ratified = load_ratified_freeze()
    generation_sha256 = ratified.sha256
    ledger = reserve_all_cells(None, manifest_sha256="a", freeze_sha256="b",
                               schedule_sha256="c", ratified_generation_sha256=generation_sha256,
                               cells=(), limits=None)
    settle(None, cell_id="cell", actual_bench_s=0.0)
    return symmetric_indeterminate(ledger)
def run_trial():
    return _budget()
"""

TOKEN_ONLY_C06_SUPERVISOR_NO_RUN_TRIAL = TOKEN_ONLY_C06_SUPERVISOR.replace(
    "def run_trial():",
    "def not_run_trial():",
)

TOKEN_ONLY_C06_SUPERVISOR_NAME_ONLY_DECOY = """
class DecoyRatified:
    sha256 = "decoy"

def load_ratified_freeze():
    return DecoyRatified()

def reserve_all_cells(*args, **kwargs):
    return object()

def settle(*args, **kwargs):
    return None

def symmetric_indeterminate(ledger):
    return frozenset()

def _budget():
    ratified = load_ratified_freeze()
    generation_sha256 = ratified.sha256
    ledger = reserve_all_cells(
        None,
        manifest_sha256="a",
        freeze_sha256="b",
        schedule_sha256="c",
        ratified_generation_sha256=generation_sha256,
        cells=(),
        limits=None,
    )
    settle(None, cell_id="cell", actual_bench_s=0.0)
    return symmetric_indeterminate(ledger)

def run_trial():
    return _budget()
"""


def _c06_contract_with_machine_flag() -> bytes:
    value = json.loads(CONTRACT_FILE.read_bytes())
    value["conditions"][5]["machine_checkable"] = True
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _c06_contract_with_broken_reachable_from() -> bytes:
    value = json.loads(CONTRACT_FILE.read_bytes())
    value["conditions"][5]["machine_checkable"] = True
    budget_consumer = next(
        item
        for item in value["conditions"][5]["required_evidence"]
        if item["artifact_kind"] == "budget_consumer"
    )
    budget_consumer["reachable_from"].remove(
        "bench terminal -> settle -> symmetric_indeterminate"
    )
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _machine_c06_result(
    tmp_path: Path,
    name: str,
    *,
    budget_source: str,
    supervisor_source: str | None = TOKEN_ONLY_C06_SUPERVISOR,
    contract_source: bytes | None = None,
) -> tuple[Path, str, core.PredicateResult]:
    root = _init_repo(tmp_path, name)
    _write(
        root,
        core.EVIDENCE_CONTRACT_PATH,
        _c06_contract_with_machine_flag()
        if contract_source is None
        else contract_source,
    )
    _write(root, "orchestrator/campaign/s8c_budget.py", budget_source)
    _write(root, "orchestrator/campaign/s8b_ratified_freeze.py", TOKEN_ONLY_C06_RATIFIED)
    if supervisor_source is not None:
        _write(
            root,
            "orchestrator/campaign/p3_autonomous_workload_trial.py",
            supervisor_source,
        )
    head = _commit(root, name)
    return root, head, _result(root, head, "C06")


def test_current_contract_promotes_c06_to_machine_registry() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    assert contract.condition(6).machine_checkable is True
    assert 6 in M._MACHINE_EVALUATORS
    assert set(M._STAGED_EVALUATORS) == set()
    assert len(M.MACHINE_CHECKABLE_CONDITION_IDS) == 10


def test_c06_machine_fixture_is_not_a_contract_promotion(
    tmp_path: Path,
) -> None:
    """これは mutation fixture であり凍結された契約ではない。"""
    root, head, result = _machine_c06_result(
        tmp_path,
        "machine-c06",
        budget_source=TOKEN_ONLY_C06_BUDGET,
    )
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "completion-proof-not-machine-checkable"
    report = core.activation_report_at(root, head)
    assert report.effective is False


def test_c06_machine_negative_control_removes_one_arm_reservation(
    tmp_path: Path,
) -> None:
    control_id = "nc_c06_one_arm_reservation_removed"
    assert NEGATIVE_CONTROL_CASES[control_id] == "C06"
    sources, mutated_path, mutated_source = _negative_control_case(control_id)
    root = _init_repo(tmp_path, "machine-c06-negative")
    _write(root, core.EVIDENCE_CONTRACT_PATH, _c06_contract_with_machine_flag())
    for path, source in sources.items():
        _write(root, path, source)
    baseline = _commit(root, "machine C06 baseline")
    baseline_result = _result(root, baseline, "C06")
    assert baseline_result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    _write(root, mutated_path, mutated_source)
    mutated = _commit(root, "machine C06 one arm removed")
    mutated_result = _result(root, mutated, "C06")
    assert mutated_result.status is core.PredicateStatus.UNSATISFIED


@pytest.mark.parametrize(
    ("name", "supervisor_source"),
    [
        ("machine-c06-supervisor-absent", None),
        (
            "machine-c06-run-trial-absent",
            TOKEN_ONLY_C06_SUPERVISOR_NO_RUN_TRIAL,
        ),
    ],
)
def test_c06_missing_supervisor_or_run_trial_is_unsatisfied(
    tmp_path: Path,
    name: str,
    supervisor_source: str | None,
) -> None:
    _, _, result = _machine_c06_result(
        tmp_path,
        name,
        budget_source=TOKEN_ONLY_C06_BUDGET,
        supervisor_source=supervisor_source,
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "budget-consumer-contract-undefined"


def test_c06_rejects_name_only_supervisor_decoy(
    tmp_path: Path,
) -> None:
    _, _, result = _machine_c06_result(
        tmp_path,
        "machine-c06-name-only-decoy",
        budget_source=TOKEN_ONLY_C06_BUDGET,
        supervisor_source=TOKEN_ONLY_C06_SUPERVISOR_NAME_ONLY_DECOY,
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "budget-consumer-contract-undefined"


def test_c06_rejects_budget_without_limit_check(
    tmp_path: Path,
) -> None:
    _, _, result = _machine_c06_result(
        tmp_path,
        "machine-c06-missing-limit-check",
        budget_source=TOKEN_ONLY_C06_BUDGET_MISSING_LIMIT_CHECK,
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "budget-consumer-contract-undefined"


def test_c06_rejects_broken_reachable_from_contract(
    tmp_path: Path,
) -> None:
    _, _, result = _machine_c06_result(
        tmp_path,
        "machine-c06-broken-reachable-from",
        budget_source=TOKEN_ONLY_C06_BUDGET,
        contract_source=_c06_contract_with_broken_reachable_from(),
    )
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "budget-consumer-contract-undefined"


@pytest.mark.parametrize(
    "source",
    [
        "def reserve_all_cells():\n    return {'ledger.manifest_sha256': 'x'}\n",
        "class Ledger:\n    manifest_sha256: str\n",
        TOKEN_ONLY_C06_BUDGET + "\ndef dynamic(ledger, name, value):\n    setattr(ledger, name, value)\n",
    ],
    ids=("dict-literal-only", "annotation-only", "dynamic-field-generation"),
)
def test_c06_field_path_checker_rejects_non_closed_shapes(source: str) -> None:
    assert M._c06_field_path_verdict(ast.parse(source)) is False


def _candidate_commit_with_worktree(tmp_path: Path) -> str:
    index = tmp_path / "candidate.index"
    env = os.environ.copy()
    env.update(
        {
            "GIT_INDEX_FILE": str(index),
            "GIT_AUTHOR_NAME": "s8c candidate fixture",
            "GIT_AUTHOR_EMAIL": "s8c-candidate@example.invalid",
            "GIT_COMMITTER_NAME": "s8c candidate fixture",
            "GIT_COMMITTER_EMAIL": "s8c-candidate@example.invalid",
        }
    )

    def run(args: list[str], *, input_bytes: bytes | None = None) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=_ROOT,
            env=env,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=20,
        )
        return result.stdout.decode("utf-8").strip()

    run(["read-tree", "HEAD"])
    run(["add", "-A", "--", *_C06_CANDIDATE_PATHS])
    tree = run(["write-tree"])
    return run(
        ["commit-tree", tree, "-p", "HEAD"],
        input_bytes=b"s8c budget candidate\n",
    )


@pytest.fixture
def repository_candidate_commit(
    tmp_path_factory: pytest.TempPathFactory,
    real_repo_fixture_lock,
) -> str:
    """候補生成を parent EX、consumer 実行を parent SH で覆う。"""
    with real_repo_fixture_lock("write", None):
        candidate = _candidate_commit_with_worktree(
            tmp_path_factory.mktemp("c06-candidate")
        )
    with real_repo_fixture_lock("read", None):
        yield candidate


def _direct_c06_result(root: Path, commit: str) -> core.PredicateResult:
    raw = CONTRACT_FILE.read_bytes()
    contract = M.load_contract_bytes(raw)
    probe = M._ConditionProbe(
        root,
        commit,
        contract.condition(6),
        core.EvidenceRef(core.EVIDENCE_CONTRACT_PATH, core._sha256(raw)),
        {},
        {core.EVIDENCE_CONTRACT_PATH: raw},
        declared_paths=contract.evidence_paths,
    )
    return M._evaluate_c06(probe)


def test_repository_candidate_uses_real_s8c_budget_module(
    repository_candidate_commit: str,
) -> None:
    result = _direct_c06_result(_ROOT, repository_candidate_commit)
    assert result.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert result.reason_code == "completion-proof-not-machine-checkable"
