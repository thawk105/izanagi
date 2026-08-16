# -*- coding: utf-8 -*-
"""s8c preregistration evidence predicate の fail-closed / 恒真化対策。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR.parent))

from orchestrator.campaign import s8b_holdout_freeze  # noqa: E402
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
    """現 HEAD の evidence blobs と、この単位の契約を使い捨て commit へ写す。"""
    root = _init_repo(tmp_path, "current-snapshot")
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    paths = {
        item.path
        for condition in contract.conditions
        for item in condition.required_evidence
    }
    for path in sorted(paths):
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{path}"],
            cwd=_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).returncode == 0
        if exists:
            _write(root, path, _git(_ROOT, "show", f"HEAD:{path}"))
    # HEAD がこの単位をまだ含まない段 5 でも、評価対象 commit には契約を含める。
    _write(root, core.EVIDENCE_CONTRACT_PATH, CONTRACT_FILE.read_bytes())
    return root, _commit(root, "current evidence snapshot")


def test_predicate_registry_is_exactly_c01_through_c12(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    head = _commit(root)
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert tuple(item.id for item in results) == core.PREDICATE_IDS
    assert len(results) == 12
    assert all(item.reason_code in M.REASON_CODES for item in results)


def test_current_repository_snapshot_has_zero_satisfied_predicates(tmp_path: Path) -> None:
    root, head = _snapshot_current_commit(tmp_path)
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert sum(item.status is core.PredicateStatus.SATISFIED for item in results) == 0
    for item in results:
        assert item.evidence
        assert all(ref.path and len(ref.blob_sha256) == 64 for ref in item.evidence)


def test_current_repository_gap_reason_snapshot_requires_cross_wave_review(
    tmp_path: Path,
) -> None:
    """個別 reason は gap ledger。他 wave の land 時は意図を再審査して更新する。

    [T-325] の land で trial_registry の capability probe 段階を通過した。
    """
    root, head = _snapshot_current_commit(tmp_path)
    results = M.get_registry().evaluate_all(head, repo_root=root)
    assert {
        item.id: (item.status, item.reason_code) for item in results
    } == {
        "C01": (core.PredicateStatus.UNSATISFIED, "workload-projection-mismatch"),
        "C02": (core.PredicateStatus.EVIDENCE_UNDEFINED, "arm-binding-declared-only"),
        "C03": (core.PredicateStatus.EVIDENCE_UNDEFINED, "manifest-registry-proof-undefined"),
        "C04": (core.PredicateStatus.UNSATISFIED, "crash-policy-cell-partial"),
        "C05": (core.PredicateStatus.EVIDENCE_UNDEFINED, "schedule-schema-absent"),
        "C06": (core.PredicateStatus.EVIDENCE_UNDEFINED, "budget-consumer-contract-undefined"),
        "C07": (core.PredicateStatus.EVIDENCE_UNDEFINED, "floor-judge-contract-undefined"),
        "C08": (core.PredicateStatus.EVIDENCE_UNDEFINED, "prereg-binding-proof-undefined"),
        "C09": (core.PredicateStatus.UNSATISFIED, "formal-acceptance-layer3-consumer-absent"),
        "C10": (core.PredicateStatus.UNSATISFIED, "cross-binding-verifier-incomplete"),
        "C11": (core.PredicateStatus.EVIDENCE_UNDEFINED, "completion-proof-not-machine-checkable"),
        "C12": (core.PredicateStatus.UNSATISFIED, "environment-contract-consumer-absent"),
    }


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


TOKEN_ONLY_C01 = """
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

TOKEN_ONLY_C04 = """
def launch_cells(): pass
def mark_experiment_indeterminate(): pass
def forbid_trial_restart(): pass
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
def assert_campaign_layer3_chain(): pass
def run_trial():
    assert_campaign_layer3_chain()
def main():
    return run_trial()
"""

TOKEN_ONLY_C09_REGISTRY = """
def assert_campaign_layer3_chain(): pass
def accept_trial():
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
def accept_trial():
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
class Policy:
    single_process = True
    allow_resume = False
class Contract:
    isolation_policy = Policy()
def lookup(): return Contract()
def attest_and_build_receipt(*args): return object()
def single_process_required(*args): return True
def run_trial():
    contract = lookup()
    attest_and_build_receipt(contract)
    if not single_process_required(contract.isolation_policy):
        raise RuntimeError
    if contract.isolation_policy.allow_resume:
        raise RuntimeError
    return contract.isolation_policy.single_process
def main():
    return run_trial()
"""


def _negative_control_case(identifier: str) -> tuple[dict[str, str], str, str]:
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
    if identifier == "nc_c04_partial_crash_survives":
        sources = {p3: TOKEN_ONLY_C04, registry: "def forbid_trial_restart(): pass\n"}
        return sources, p3, TOKEN_ONLY_C04.replace(
            "        mark_experiment_indeterminate()",
            "        keep_completed_cells_certifying()",
            1,
        )
    if identifier == "nc_c09_acceptance_skips_layer3":
        sources = {p3: TOKEN_ONLY_C09_PRODUCER, registry: TOKEN_ONLY_C09_REGISTRY}
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
    if identifier == "nc_c12_resume_or_multi_process_allowed":
        sources = {
            p3: TOKEN_ONLY_C12,
            "orchestrator/campaign/env_contract.py": "def lookup(): pass\n",
            "orchestrator/campaign/execution_guard.py":
                "def attest_and_build_receipt(): pass\n",
            "orchestrator/campaign/reservation.py":
                "def single_process_required(): pass\n",
        }
        return sources, p3, TOKEN_ONLY_C12.replace(
            "single_process_required(contract.isolation_policy)",
            "multi_process_allowed(contract.isolation_policy)",
            1,
        )
    raise AssertionError(identifier)


NEGATIVE_CONTROL_CASES = {
    "nc_c01_perf_scale_regression": "C01",
    "nc_c04_partial_crash_survives": "C04",
    "nc_c09_acceptance_skips_layer3": "C09",
    "nc_c10_raw_response_unbound": "C10",
    "nc_c11_generation_cap_reverts_to_one": "C11",
    "nc_c12_resume_or_multi_process_allowed": "C12",
}


def test_satisfiable_predicate_requires_negative_control() -> None:
    contract = M.load_contract_bytes(CONTRACT_FILE.read_bytes())
    rows = {condition.identifier: condition for condition in contract.conditions}
    machine_checkable = {
        identifier for identifier, row in rows.items() if row.machine_checkable
    }
    assert machine_checkable == M.MACHINE_CHECKABLE_CONDITION_IDS
    assert machine_checkable == {"C01", "C04", "C09", "C10", "C11", "C12"}
    assert M.SATISFIABLE_CONDITION_IDS == frozenset()
    assert M.SATISFIABLE_CONDITION_IDS <= M.MACHINE_CHECKABLE_CONDITION_IDS
    exercised = 0
    for identifier in machine_checkable:
        exercised += 1
        row = rows[identifier]
        assert row.negative_control_id in NEGATIVE_CONTROL_CASES
        assert NEGATIVE_CONTROL_CASES[row.negative_control_id] == identifier
    assert exercised == 6
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
        "C04": "crash-policy-cell-partial",
        "C09": "formal-acceptance-layer3-consumer-absent",
        "C10": "cross-binding-verifier-incomplete",
        "C11": "generation-cap-not-lifted",
        "C12": "allocation-enforcement-consumer-absent",
    }
    assert mutated_result.status is core.PredicateStatus.UNSATISFIED
    assert mutated_result.reason_code == expected_reasons[identifier]


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
    head = _commit(root, "mismatched evaluator")
    report = core.activation_report_at(root, head)
    assert {item.status for item in report.predicates} == {core.PredicateStatus.ERROR}
    assert {item.reason_code for item in report.predicates} == {"evaluator-blob-mismatch"}


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
    value["conditions"][1]["machine_checkable"] = True
    root = _init_repo(tmp_path)
    _write(
        root,
        core.EVIDENCE_CONTRACT_PATH,
        json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )
    head = _commit(root, "C02 falsely marked machine checkable")

    result = _result(root, head, "C02")
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
