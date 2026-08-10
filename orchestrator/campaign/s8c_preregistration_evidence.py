# -*- coding: utf-8 -*-
"""Phase 3 段 8c の commit-blob 証拠 predicate registry。

判定対象は常に指定 commit ``C`` の tree である。worktree の Python module や
artifact を evidence として import / open しない。証拠定義も ``C`` の evidence
contract blob から strict に読み、未知 key・duplicate key・非有限数を拒否する。
"""
from __future__ import annotations

import ast
import enum
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from . import s8c_preregistration as core


CONTRACT_SCHEMA_VERSION = "s8c-preregistration-evidence-contract/v1"
_CONTRACT_KEYS = frozenset({"schema_version", "conditions"})
_CONDITION_KEYS = frozenset(
    {
        "condition_number",
        "required_evidence",
        "consumer_requirement",
        "negative_control_id",
        "machine_checkable",
        "static_only_note",
    }
)
_EVIDENCE_KEYS = frozenset(
    {"artifact_kind", "path", "field_paths", "reachable_from"}
)
_CONSUMER_KEYS = frozenset({"path", "entrypoints", "proof"})
_NEGATIVE_CONTROL_RE = re.compile(r"nc_c([0-9]{2})_[a-z0-9_]+\Z")


class EvidenceContractError(RuntimeError):
    """証拠契約を strict に解釈できない。``reason_code`` は閉じた値域。"""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        super().__init__(f"[{reason_code}] {detail}" if detail else reason_code)


class ReasonCode(str, enum.Enum):
    COMPLETION_PROOF_NOT_MACHINE_CHECKABLE = "completion-proof-not-machine-checkable"
    CONTRACT_MISSING = "evidence-contract-missing"
    CONTRACT_INVALID = "evidence-contract-invalid"
    BLOB_READ_ERROR = "commit-blob-read-error"
    PYTHON_PARSE_ERROR = "evidence-python-parse-error"
    EVALUATOR_INTERNAL_ERROR = "evaluator-internal-error"
    WORKLOAD_SUPERVISOR_ABSENT = "workload-supervisor-absent"
    WORKLOAD_PROJECTION_MISMATCH = "workload-projection-mismatch"
    WORKLOAD_CONSUMER_UNREACHABLE = "workload-consumer-unreachable"
    RATIFIED_GENERATION_REFERENCE_ABSENT = "ratified-generation-reference-absent"
    TRIAL_REGISTRY_CAPABILITY_ABSENT = "trial-registry-capability-absent"
    ARM_BINDING_DECLARED_ONLY = "arm-binding-declared-only"
    ARM_BINDING_PROOF_UNDEFINED = "arm-binding-proof-undefined"
    MANIFEST_REGISTRY_PROOF_UNDEFINED = "manifest-registry-proof-undefined"
    CRASH_POLICY_CELL_PARTIAL = "crash-policy-cell-partial"
    RESTART_GUARD_ABSENT = "restart-guard-absent"
    SCHEDULE_SCHEMA_ABSENT = "schedule-schema-absent"
    SCHEDULE_CONSUMER_UNDEFINED = "schedule-consumer-undefined"
    BUDGET_CONSUMER_UNDEFINED = "budget-consumer-contract-undefined"
    FLOOR_JUDGE_CONSUMER_UNDEFINED = "floor-judge-contract-undefined"
    PREREG_BINDING_CAPABILITY_ABSENT = "prereg-binding-capability-absent"
    PREREG_BINDING_PROOF_UNDEFINED = "prereg-binding-proof-undefined"
    LAYER3_PRODUCER_UNREACHABLE = "layer3-producer-unreachable"
    FORMAL_ACCEPTANCE_LAYER3_ABSENT = "formal-acceptance-layer3-consumer-absent"
    CROSS_BINDING_VERIFIER_INCOMPLETE = "cross-binding-verifier-incomplete"
    CROSS_BINDING_ACCEPTANCE_UNREACHABLE = "cross-binding-acceptance-unreachable"
    GENERATION_CAP_NOT_LIFTED = "generation-cap-not-lifted"
    GENERATION_ENTRYPOINT_BOUNDARY_INCOMPLETE = "generation-entrypoint-boundary-incomplete"
    CRITIC_FEEDBACK_CONSUMER_ABSENT = "critic-feedback-consumer-absent"
    SAMPLE_PLAN_ABSENT = "sample-plan-absent"
    SAMPLE_PLAN_INVALID = "sample-plan-invalid"
    CAP_LIFT_RECEIPT_ABSENT = "cap-lift-receipt-absent"
    CAP_LIFT_RECEIPT_INVALID = "cap-lift-receipt-invalid"
    GENERATION_ARTIFACT_BINDING_ABSENT = "generation-artifact-binding-absent"
    ENVIRONMENT_CONTRACT_CONSUMER_ABSENT = "environment-contract-consumer-absent"
    ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT = "allocation-enforcement-consumer-absent"


REASON_CODES = frozenset(item.value for item in ReasonCode)


@dataclass(frozen=True)
class RequiredEvidence:
    artifact_kind: str
    path: str
    field_paths: tuple[str, ...]
    reachable_from: tuple[str, ...]


@dataclass(frozen=True)
class ConsumerRequirement:
    path: str
    entrypoints: tuple[str, ...]
    proof: str


@dataclass(frozen=True)
class ConditionContract:
    condition_number: int
    required_evidence: tuple[RequiredEvidence, ...]
    consumer_requirement: ConsumerRequirement
    negative_control_id: str
    machine_checkable: bool
    static_only_note: str

    @property
    def identifier(self) -> str:
        return f"C{self.condition_number:02d}"


@dataclass(frozen=True)
class EvidenceContract:
    schema_version: str
    conditions: tuple[ConditionContract, ...]

    def condition(self, number: int) -> ConditionContract:
        return self.conditions[number - 1]


def _reject_constant(token: str) -> None:
    raise EvidenceContractError("contract-nonfinite-number", token)


def _unique_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceContractError("contract-duplicate-key", key)
        result[key] = value
    return result


def _strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise EvidenceContractError("contract-bad-utf8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise EvidenceContractError("contract-bad-json", str(exc)) from exc


def _exact_keys(value: object, keys: frozenset[str], *, where: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceContractError("contract-not-object", where)
    if frozenset(value) != keys:
        delta = sorted(frozenset(value) ^ keys)
        raise EvidenceContractError("contract-schema-keys", f"{where}: {delta!r}")
    return value


def _nonempty_string(value: object, *, where: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise EvidenceContractError("contract-string", where)
    return value


def _string_tuple(value: object, *, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise EvidenceContractError("contract-string-list", where)
    values = tuple(_nonempty_string(item, where=where) for item in value)
    if len(set(values)) != len(values):
        raise EvidenceContractError("contract-list-duplicate", where)
    return values


def _safe_path(value: object, *, where: str) -> str:
    if isinstance(value, str):
        text = "".join((value,))
        if "\x00" in text or "\r" in text or "\n" in text:
            raise EvidenceContractError("contract-path-control-char", repr(where))
    else:
        text = _nonempty_string(value, where=where)
    path = _nonempty_string(text, where=where)
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or path != pure.as_posix():
        raise EvidenceContractError("contract-path", where)
    return path


def load_contract_bytes(raw: bytes) -> EvidenceContract:
    """strict JSON と exact v1 schema を検査して型付き契約を返す。"""
    top = _exact_keys(_strict_json(raw), _CONTRACT_KEYS, where="contract")
    if top["schema_version"] != CONTRACT_SCHEMA_VERSION:
        raise EvidenceContractError("contract-schema-version")
    rows = top["conditions"]
    if not isinstance(rows, list) or len(rows) != 12:
        raise EvidenceContractError("contract-condition-count")
    conditions: list[ConditionContract] = []
    for expected, raw_row in enumerate(rows, 1):
        row = _exact_keys(raw_row, _CONDITION_KEYS, where=f"conditions[{expected - 1}]")
        number = row["condition_number"]
        if isinstance(number, bool) or not isinstance(number, int) or number != expected:
            raise EvidenceContractError("contract-condition-number", repr(number))
        raw_evidence = row["required_evidence"]
        if not isinstance(raw_evidence, list) or not raw_evidence:
            raise EvidenceContractError("contract-required-evidence", f"C{number:02d}")
        evidence: list[RequiredEvidence] = []
        kinds: set[str] = set()
        for index, raw_item in enumerate(raw_evidence):
            item = _exact_keys(
                raw_item,
                _EVIDENCE_KEYS,
                where=f"C{number:02d}.required_evidence[{index}]",
            )
            kind = _nonempty_string(item["artifact_kind"], where="artifact_kind")
            if kind in kinds:
                raise EvidenceContractError("contract-artifact-kind-duplicate", kind)
            kinds.add(kind)
            evidence.append(
                RequiredEvidence(
                    artifact_kind=kind,
                    path=_safe_path(item["path"], where=f"C{number:02d}.{kind}.path"),
                    field_paths=_string_tuple(
                        item["field_paths"], where=f"C{number:02d}.{kind}.field_paths"
                    ),
                    reachable_from=_string_tuple(
                        item["reachable_from"],
                        where=f"C{number:02d}.{kind}.reachable_from",
                    ),
                )
            )
        raw_consumer = _exact_keys(
            row["consumer_requirement"],
            _CONSUMER_KEYS,
            where=f"C{number:02d}.consumer_requirement",
        )
        negative = _nonempty_string(row["negative_control_id"], where="negative_control_id")
        match = _NEGATIVE_CONTROL_RE.fullmatch(negative)
        if match is None or int(match.group(1)) != number:
            raise EvidenceContractError("contract-negative-control-id", negative)
        machine = row["machine_checkable"]
        if type(machine) is not bool:
            raise EvidenceContractError("contract-machine-checkable", f"C{number:02d}")
        conditions.append(
            ConditionContract(
                condition_number=number,
                required_evidence=tuple(evidence),
                consumer_requirement=ConsumerRequirement(
                    path=_safe_path(raw_consumer["path"], where="consumer.path"),
                    entrypoints=_string_tuple(
                        raw_consumer["entrypoints"], where="consumer.entrypoints"
                    ),
                    proof=_nonempty_string(raw_consumer["proof"], where="consumer.proof"),
                ),
                negative_control_id=negative,
                machine_checkable=machine,
                static_only_note=_nonempty_string(
                    row["static_only_note"], where="static_only_note"
                ),
            )
        )
    return EvidenceContract(CONTRACT_SCHEMA_VERSION, tuple(conditions))


def semantic_contract_sha256(raw: bytes) -> str:
    """schema 検証後の JSON 意味 hash。空白や key 順には依存しない。"""
    load_contract_bytes(raw)
    return core.evidence_contract_sha256(raw)


def is_satisfied(status: core.PredicateStatus) -> bool:
    """真として扱う status は exact ``SATISFIED`` だけ。"""
    return status is core.PredicateStatus.SATISFIED


def _functions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        function = child.func
        if isinstance(function, ast.Name):
            names.add(function.id)
        elif isinstance(function, ast.Attribute):
            names.add(function.attr)
    return names


def _attributes(node: ast.AST) -> set[str]:
    return {child.attr for child in ast.walk(node) if isinstance(child, ast.Attribute)}


def _strings(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _integers(node: ast.AST) -> set[int]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, int)
        and not isinstance(child.value, bool)
    }


def _assigned_integer(tree: ast.Module, name: str) -> int | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            if isinstance(node.value, ast.Constant) and type(node.value.value) is int:
                return node.value.value
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and isinstance(node.value, ast.Constant)
            and type(node.value.value) is int
        ):
            return node.value.value
    return None


def _reachable_functions(tree: ast.Module, start: str) -> set[str]:
    functions = _functions(tree)
    reached: set[str] = set()
    pending = [start]
    while pending:
        name = pending.pop()
        if name in reached or name not in functions:
            continue
        reached.add(name)
        pending.extend(_called_names(functions[name]) & functions.keys())
    return reached


def _reachable_calls(tree: ast.Module, start: str) -> set[str]:
    functions = _functions(tree)
    return set().union(
        *(_called_names(functions[name]) for name in _reachable_functions(tree, start))
    ) if start in functions else set()


@dataclass
class _ConditionProbe:
    repo_root: Path
    commit: str
    contract: ConditionContract
    contract_ref: core.EvidenceRef
    refs: dict[str, core.EvidenceRef]
    cache: dict[str, bytes | None]

    def requirement(self, kind: str) -> RequiredEvidence:
        matches = [item for item in self.contract.required_evidence if item.artifact_kind == kind]
        if len(matches) != 1:
            raise EvidenceContractError("contract-artifact-kind", f"{self.contract.identifier}:{kind}")
        return matches[0]

    def read_kind(self, kind: str) -> bytes | None:
        path = self.requirement(kind).path
        if path not in self.cache:
            raw = core.read_blob_at(self.repo_root, self.commit, path, required=False)
            self.cache[path] = raw
            if raw is not None:
                self.refs[path] = core.EvidenceRef(path, core._sha256(raw))
        return self.cache[path]

    def python_kind(self, kind: str) -> ast.Module | None:
        raw = self.read_kind(kind)
        if raw is None:
            return None
        try:
            return ast.parse(raw.decode("utf-8", "strict"), filename=self.requirement(kind).path)
        except (UnicodeError, SyntaxError) as exc:
            raise EvidenceContractError("evidence-python-parse-error", str(exc)) from exc

    def evidence(self) -> tuple[core.EvidenceRef, ...]:
        values = {self.contract_ref.path: self.contract_ref, **self.refs}
        return tuple(values[path] for path in sorted(values))


def _result(
    probe: _ConditionProbe,
    status: core.PredicateStatus,
    reason: ReasonCode,
) -> core.PredicateResult:
    return core.PredicateResult(
        probe.contract.identifier,
        status,
        reason.value,
        probe.evidence(),
    )


def _evaluate_c01(probe: _ConditionProbe) -> core.PredicateResult:
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    functions = _functions(tree)
    sinks = ("_campaign_for", "_perf_for", "_descriptor_for")
    if any(name not in functions for name in sinks):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.WORKLOAD_CONSUMER_UNREACHABLE)
    if any(not {1_000_000, 48} <= _integers(functions[name]) for name in sinks):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.WORKLOAD_PROJECTION_MISMATCH)
    reached = _reachable_functions(tree, "run_trial")
    if not set(sinks) <= reached or "run_trial" not in _reachable_functions(tree, "main"):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.WORKLOAD_CONSUMER_UNREACHABLE)
    ratified = probe.python_kind("ratified_generation_reference")
    calls = _reachable_calls(tree, "run_trial")
    attributes = set().union(*(_attributes(functions[name]) for name in reached))
    if (
        ratified is None
        or "load_ratified_freeze" not in _functions(ratified)
        or "load_ratified_freeze" not in calls
        or not {"sha256", "holdouts"} <= attributes
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.RATIFIED_GENERATION_REFERENCE_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c04(probe: _ConditionProbe) -> core.PredicateResult:
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    calls = _reachable_calls(tree, "run_trial")
    if not {"mark_experiment_indeterminate", "forbid_trial_restart"} <= calls:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRASH_POLICY_CELL_PARTIAL)
    registry = probe.python_kind("trial_registry")
    if registry is None or "forbid_trial_restart" not in _functions(registry):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.RESTART_GUARD_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c09(probe: _ConditionProbe) -> core.PredicateResult:
    producer = probe.python_kind("layer3_producer")
    if producer is None or "assert_campaign_layer3_chain" not in _reachable_calls(producer, "run_trial"):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.LAYER3_PRODUCER_UNREACHABLE)
    registry = probe.python_kind("trial_registry")
    functions = _functions(registry) if registry is not None else {}
    accept = functions.get("accept_trial")
    if accept is None or "assert_campaign_layer3_chain" not in _called_names(accept):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.FORMAL_ACCEPTANCE_LAYER3_ABSENT)
    strings = _strings(accept)
    if not {"no-build", "certifying"} <= strings:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.FORMAL_ACCEPTANCE_LAYER3_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


_C10_FIELDS = frozenset(
    {
        "input_payload_sha256",
        "raw_response_path",
        "raw_response_sha256",
        "provider_payload_sha256",
        "provider_envelope_sha256",
        "proposal_path",
        "proposal_sha256",
        "build_records",
        "bench_records",
        "artifact_refs",
        "source_refs",
        "admission_decision",
    }
)


def _evaluate_c10(probe: _ConditionProbe) -> core.PredicateResult:
    verifier = probe.python_kind("cross_binding_verifier")
    functions = _functions(verifier) if verifier is not None else {}
    verify = functions.get("verify_s8c_cross_binding")
    if (
        verify is None
        or not _C10_FIELDS <= _strings(verify)
        or "read_and_verify_bytes" not in _called_names(verify)
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE)
    registry = probe.python_kind("trial_registry")
    accept = _functions(registry).get("accept_trial") if registry is not None else None
    if accept is None or "verify_s8c_cross_binding" not in _called_names(accept):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CROSS_BINDING_ACCEPTANCE_UNREACHABLE)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _artifact_object(probe: _ConditionProbe, kind: str) -> Mapping[str, Any] | None:
    raw = probe.read_kind(kind)
    if raw is None:
        return None
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError, EvidenceContractError) as exc:
        raise EvidenceContractError("artifact-json-invalid", kind) from exc
    return value if isinstance(value, dict) else {}


def _evaluate_c11(probe: _ConditionProbe) -> core.PredicateResult:
    tree = probe.python_kind("generation_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    cap = _assigned_integer(tree, "MAX_APPROVED_GENERATIONS")
    if cap is None or cap < 2:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.GENERATION_CAP_NOT_LIFTED)
    functions = _functions(tree)
    boundaries = ("main", "run_trial", "_run_workload")
    if any(
        name not in functions or "_validate_generation_budget" not in _called_names(functions[name])
        for name in boundaries
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.GENERATION_ENTRYPOINT_BOUNDARY_INCOMPLETE)
    workload = functions["_run_workload"]
    if "apply_critic_feedback" not in _called_names(workload):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRITIC_FEEDBACK_CONSUMER_ABSENT)
    sample = _artifact_object(probe, "sample_plan")
    if sample is None:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.SAMPLE_PLAN_ABSENT)
    if not (
        sample.get("schema_version") == "s8c-sample-plan/v1"
        and type(sample.get("minimum_generations")) is int
        and sample["minimum_generations"] >= 2
        and sample.get("critic_feedback_required") is True
        and type(sample.get("sample_count")) is int
        and sample["sample_count"] > 0
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.SAMPLE_PLAN_INVALID)
    lift = _artifact_object(probe, "cap_lift")
    if lift is None:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CAP_LIFT_RECEIPT_ABSENT)
    if not (
        lift.get("schema_version") == "s8c-generation-cap-lift/v1"
        and type(lift.get("minimum_generations")) is int
        and lift["minimum_generations"] >= 2
        and lift.get("entrypoints") == ["main", "run_trial", "_run_workload"]
        and isinstance(lift.get("ruling_reference"), str)
        and lift["ruling_reference"]
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CAP_LIFT_RECEIPT_INVALID)
    if not {"sample_plan_sha256", "cap_lift_sha256"} <= _strings(workload):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.GENERATION_ARTIFACT_BINDING_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c12(probe: _ConditionProbe) -> core.PredicateResult:
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    functions = _functions(tree)
    run_trial = functions.get("run_trial")
    if run_trial is None:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    calls = _reachable_calls(tree, "run_trial")
    attributes = set().union(*(_attributes(functions[name]) for name in _reachable_functions(tree, "run_trial")))
    environment = probe.python_kind("environment_contract")
    guard = probe.python_kind("execution_guard")
    allocation = probe.python_kind("allocation_consumer")
    if (
        environment is None
        or guard is None
        or "lookup" not in _functions(environment)
        or "attest_and_build_receipt" not in _functions(guard)
        or not {"lookup", "attest_and_build_receipt"} <= calls
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    if (
        allocation is None
        or "single_process_required" not in _functions(allocation)
        or "single_process_required" not in calls
        or not {"single_process", "allow_resume"} <= attributes
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


_MACHINE_EVALUATORS = {
    1: _evaluate_c01,
    4: _evaluate_c04,
    9: _evaluate_c09,
    10: _evaluate_c10,
    11: _evaluate_c11,
    12: _evaluate_c12,
}
SATISFIABLE_CONDITION_IDS: frozenset[str] = frozenset()


def _evaluate_undefined(probe: _ConditionProbe) -> core.PredicateResult:
    number = probe.contract.condition_number
    if number in _MACHINE_EVALUATORS:
        for item in probe.contract.required_evidence:
            probe.read_kind(item.artifact_kind)
        reason = ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE
    elif number == 2:
        raw = probe.read_kind("trial_registry")
        if raw is None:
            reason = ReasonCode.TRIAL_REGISTRY_CAPABILITY_ABSENT
        elif b"declared-only" in raw:
            reason = ReasonCode.ARM_BINDING_DECLARED_ONLY
        else:
            reason = ReasonCode.ARM_BINDING_PROOF_UNDEFINED
    elif number == 3:
        raw = probe.read_kind("trial_registry")
        reason = (
            ReasonCode.TRIAL_REGISTRY_CAPABILITY_ABSENT
            if raw is None
            else ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED
        )
    elif number == 5:
        artifact = probe.read_kind("schedule_artifact")
        consumer = probe.read_kind("schedule_consumer")
        reason = (
            ReasonCode.SCHEDULE_SCHEMA_ABSENT
            if artifact is None
            else ReasonCode.SCHEDULE_CONSUMER_UNDEFINED
        )
        del consumer
    elif number == 6:
        probe.read_kind("budget_consumer")
        reason = ReasonCode.BUDGET_CONSUMER_UNDEFINED
    elif number == 7:
        probe.read_kind("result_judge")
        reason = ReasonCode.FLOOR_JUDGE_CONSUMER_UNDEFINED
    elif number == 8:
        raw = probe.read_kind("trial_registry")
        reason = (
            ReasonCode.PREREG_BINDING_CAPABILITY_ABSENT
            if raw is None
            else ReasonCode.PREREG_BINDING_PROOF_UNDEFINED
        )
    else:  # schema validation makes this unreachable unless code/contract drift.
        raise EvidenceContractError("contract-machine-evaluator", probe.contract.identifier)
    return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, reason)


class PredicateRegistry:
    """単位 A の ``PredicateRegistry`` protocol を満たす closed registry。"""

    def evaluate_all(
        self, commit: str, *, repo_root: Path
    ) -> Sequence[core.PredicateResult]:
        root = Path(repo_root).resolve()
        try:
            contract_raw = core.read_blob_at(
                root, commit, core.EVIDENCE_CONTRACT_PATH, required=False
            )
        except core.PreregistrationError:
            return self._uniform(core.PredicateStatus.ERROR, ReasonCode.BLOB_READ_ERROR)
        if contract_raw is None:
            return self._uniform(core.PredicateStatus.ERROR, ReasonCode.CONTRACT_MISSING)
        contract_ref = core.EvidenceRef(
            core.EVIDENCE_CONTRACT_PATH, core._sha256(contract_raw)
        )
        try:
            contract = load_contract_bytes(contract_raw)
        except EvidenceContractError:
            return self._uniform(
                core.PredicateStatus.ERROR,
                ReasonCode.CONTRACT_INVALID,
                evidence=[contract_ref],
            )
        results: list[core.PredicateResult] = []
        for condition in contract.conditions:
            probe = _ConditionProbe(root, commit, condition, contract_ref, {}, {})
            try:
                if condition.machine_checkable:
                    evaluator = _MACHINE_EVALUATORS.get(condition.condition_number)
                    if evaluator is None:
                        raise EvidenceContractError(
                            "contract-machine-evaluator", condition.identifier
                        )
                    result = evaluator(probe)
                else:
                    result = _evaluate_undefined(probe)
            except (core.PreregistrationError, EvidenceContractError) as exc:
                reason = (
                    ReasonCode.PYTHON_PARSE_ERROR
                    if getattr(exc, "reason_code", "") == "evidence-python-parse-error"
                    else ReasonCode.BLOB_READ_ERROR
                )
                result = _result(probe, core.PredicateStatus.ERROR, reason)
            except Exception:  # fail-closed。自由文を reason_code にしない。
                result = _result(
                    probe,
                    core.PredicateStatus.ERROR,
                    ReasonCode.EVALUATOR_INTERNAL_ERROR,
                )
            results.append(result)
        return tuple(results)

    @staticmethod
    def _uniform(
        status: core.PredicateStatus,
        reason: ReasonCode,
        *,
        evidence: Sequence[core.EvidenceRef] | None = None,
    ) -> tuple[core.PredicateResult, ...]:
        refs = () if evidence is None else tuple(evidence)
        return tuple(
            core.PredicateResult(identifier, status, reason.value, refs)
            for identifier in core.PREDICATE_IDS
        )


_REGISTRY = PredicateRegistry()


def get_registry() -> PredicateRegistry:
    return _REGISTRY


def evaluate_all(
    commit: str, *, repo_root: Path
) -> Sequence[core.PredicateResult]:
    """module 自身も registry として使える protocol adapter。"""
    return _REGISTRY.evaluate_all(commit, repo_root=repo_root)
