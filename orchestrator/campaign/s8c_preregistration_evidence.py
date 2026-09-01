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
from dataclasses import dataclass, field
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
    REACHABILITY_LIMIT_EXCEEDED = "reachability-limit-exceeded"
    WORKLOAD_SUPERVISOR_ABSENT = "workload-supervisor-absent"
    WORKLOAD_PROJECTION_MISMATCH = "workload-projection-mismatch"
    WORKLOAD_CONSUMER_UNREACHABLE = "workload-consumer-unreachable"
    RATIFIED_GENERATION_REFERENCE_ABSENT = "ratified-generation-reference-absent"
    TRIAL_REGISTRY_CAPABILITY_ABSENT = "trial-registry-capability-absent"
    ARM_BINDING_DECLARED_ONLY = "arm-binding-declared-only"
    ARM_BINDING_PROOF_UNDEFINED = "arm-binding-proof-undefined"
    ARM_BINDING_CONSUMER_UNREACHABLE = "arm-binding-consumer-unreachable"
    MANIFEST_REGISTRY_PROOF_UNDEFINED = "manifest-registry-proof-undefined"
    CRASH_POLICY_CELL_PARTIAL = "crash-policy-cell-partial"
    RESTART_GUARD_ABSENT = "restart-guard-absent"
    SCHEDULE_SCHEMA_ABSENT = "schedule-schema-absent"
    SCHEDULE_CONSUMER_UNDEFINED = "schedule-consumer-undefined"
    SCHEDULE_CONSUMER_UNREACHABLE = "schedule-consumer-unreachable"
    BUDGET_CONSUMER_UNDEFINED = "budget-consumer-contract-undefined"
    FLOOR_JUDGE_CONSUMER_UNDEFINED = "floor-judge-contract-undefined"
    RESULT_JUDGE_CONSUMER_INCOMPLETE = "result-judge-consumer-incomplete"
    PREREG_BINDING_CAPABILITY_ABSENT = "prereg-binding-capability-absent"
    PREREG_BINDING_PROOF_UNDEFINED = "prereg-binding-proof-undefined"
    LAYER3_PRODUCER_UNREACHABLE = "layer3-producer-unreachable"
    FORMAL_ACCEPTANCE_LAYER3_ABSENT = "formal-acceptance-layer3-consumer-absent"
    CROSS_BINDING_VERIFIER_INCOMPLETE = "cross-binding-verifier-incomplete"
    CROSS_BINDING_ACCEPTANCE_UNREACHABLE = "cross-binding-acceptance-unreachable"
    CROSS_BINDING_READINESS_SATISFIED = "cross-binding-readiness-satisfied"
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

    @property
    def evidence_paths(self) -> frozenset[str]:
        """全条件が宣言する target definition の許可 path 集合。"""
        return frozenset(
            item.path
            for condition in self.conditions
            for item in condition.required_evidence
        )


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


def _live_called_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for current in _live_nodes(node):
        if not isinstance(current, ast.Call):
            continue
        function = current.func
        if isinstance(function, ast.Name):
            names.add(function.id)
        elif isinstance(function, ast.Attribute):
            names.add(function.attr)
    return names


def _returns_joined_string_using(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    required_names: set[str],
) -> bool:
    assignments: dict[str, list[tuple[int, int, ast.AST]]] = {}
    returns: list[ast.Return] = []
    for current in _live_nodes(node):
        if isinstance(current, ast.Assign):
            targets = [target.id for target in current.targets if isinstance(target, ast.Name)]
            for target in targets:
                assignments.setdefault(target, []).append(
                    (current.lineno, current.col_offset, current.value)
                )
        elif isinstance(current, ast.AnnAssign) and isinstance(current.target, ast.Name):
            if current.value is not None:
                assignments.setdefault(current.target.id, []).append(
                    (current.lineno, current.col_offset, current.value)
                )
        elif isinstance(current, ast.Return):
            returns.append(current)

    def joined_string_uses_required_names(value: ast.AST) -> bool:
        return isinstance(value, ast.JoinedStr) and required_names <= {
            child.id
            for child in ast.walk(value)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
        }

    for returned in returns:
        value = returned.value
        if value is not None and joined_string_uses_required_names(value):
            return True
        if not isinstance(value, ast.Name):
            continue
        preceding = [
            item
            for item in assignments.get(value.id, ())
            if (item[0], item[1]) < (returned.lineno, returned.col_offset)
        ]
        if preceding and joined_string_uses_required_names(
            max(preceding, key=lambda item: item[:2])[2]
        ):
            return True
    return False


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


_MAX_REACHABILITY_MODULES = 512
_MAX_REACHABILITY_DEPTH = 64
_MAX_REACHABILITY_STATES = 2048
_MAX_REACHABILITY_BYTES = 16 * 1024 * 1024
_PRODUCTION_PYTHON_ROOT = PurePosixPath("orchestrator/campaign")

_CallableTarget = tuple[str, str]


@dataclass(frozen=True)
class _ModuleBinding:
    path: str
    root_imports: tuple[str, ...] = ()


@dataclass(frozen=True)
class _CallableBinding:
    target: _CallableTarget


_Binding = _ModuleBinding | _CallableBinding


@dataclass(frozen=True)
class _ReachabilityLimits:
    modules: int = _MAX_REACHABILITY_MODULES
    depth: int = _MAX_REACHABILITY_DEPTH
    states: int = _MAX_REACHABILITY_STATES
    total_bytes: int = _MAX_REACHABILITY_BYTES


@dataclass(frozen=True)
class _Reachability:
    functions: frozenset[_CallableTarget]
    calls: frozenset[_CallableTarget]
    attributes: frozenset[str]
    modules: tuple[str, ...]


@dataclass(frozen=True)
class _CallState:
    target: _CallableTarget
    bindings: tuple[tuple[str, _CallableTarget], ...] = ()
    blocked: tuple[str, ...] = ()
    depth: int = 0

    def key(self) -> tuple[object, ...]:
        return (self.target, self.bindings, self.blocked)


@dataclass(frozen=True)
class _DictCarrier:
    keywords: tuple[tuple[str, _CallableTarget | None], ...]
    mutated_keys: frozenset[str]


def _production_python_path(path: str) -> bool:
    pure = PurePosixPath(path)
    try:
        pure.relative_to(_PRODUCTION_PYTHON_ROOT)
    except ValueError:
        return False
    return pure.suffix == ".py" and "tests" not in pure.parts


def _module_name(path: str) -> tuple[str, ...]:
    pure = PurePosixPath(path)
    parts = pure.parts[:-1] if pure.name == "__init__.py" else (*pure.parts[:-1], pure.stem)
    return tuple(parts)


def _package_name(path: str) -> tuple[str, ...]:
    module = _module_name(path)
    return module if PurePosixPath(path).name == "__init__.py" else module[:-1]


def _bound_names_in_target(target: ast.AST) -> set[str]:
    return {
        node.id
        for node in ast.walk(target)
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
    }


def _direct_bound_names(node: ast.AST) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, ast.Import):
        return {alias.asname or alias.name.split(".", 1)[0] for alias in node.names}
    if isinstance(node, ast.ImportFrom):
        return {alias.asname or alias.name for alias in node.names if alias.name != "*"}
    if isinstance(node, ast.Assign):
        return set().union(*(_bound_names_in_target(target) for target in node.targets))
    if isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        return _bound_names_in_target(node.target)
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return _bound_names_in_target(node.target)
    if isinstance(node, (ast.With, ast.AsyncWith)):
        return set().union(
            *(
                _bound_names_in_target(item.optional_vars)
                for item in node.items
                if item.optional_vars is not None
            ),
            set(),
        )
    if isinstance(node, ast.ExceptHandler) and node.name is not None:
        return {node.name}
    if isinstance(node, (ast.Global, ast.Nonlocal)):
        return set(node.names)
    if isinstance(node, ast.Delete):
        return set().union(*(_bound_names_in_target(target) for target in node.targets))
    return set()


def _statement_bound_names(node: ast.AST) -> set[str]:
    """``node`` の lexical scope に束縛を作る名前を保守的に返す。"""
    names: set[str] = set()

    def visit(current: ast.AST) -> None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(current.name)
            return
        elif isinstance(current, ast.Lambda):
            return
        names.update(_direct_bound_names(current))
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node)
    return names


def _scope_nodes(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    """関数自身の lexical scope。dead branch は曖昧 binding 検査へ含める。"""
    values: list[ast.AST] = []

    def visit(current: ast.AST, *, root: bool = False) -> None:
        if not root and isinstance(
            current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            values.append(current)
            return
        values.append(current)
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node, root=True)
    return values


def _function_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    args = node.args
    return tuple(
        item.arg
        for item in (*args.posonlyargs, *args.args, *args.kwonlyargs)
    ) + (() if args.vararg is None else (args.vararg.arg,)) + (
        () if args.kwarg is None else (args.kwarg.arg,)
    )


def _literal_truth(node: ast.AST) -> bool | None:
    """Return literal truthiness, or ``None`` for every non-literal expression."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "bool"
        and len(node.args) == 1
        and not node.keywords
    ):
        nested = _literal_truth(node.args[0])
        return nested
    if not isinstance(node, (ast.Constant, ast.Tuple, ast.List, ast.Set, ast.Dict)):
        return None
    try:
        return bool(ast.literal_eval(node))
    except (ValueError, TypeError, SyntaxError):
        return None


def _live_nodes(node: ast.AST) -> list[ast.AST]:
    """Function body nodes excluding nested scopes and provably dead statements."""
    values: list[ast.AST] = []

    def visit_block(statements: Sequence[ast.stmt]) -> None:
        for statement in statements:
            visit(statement)
            if isinstance(statement, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                break
            if (
                isinstance(statement, ast.If)
                and _literal_truth(statement.test) is True
                and any(isinstance(child, ast.Return) for child in statement.body)
            ):
                break

    def visit(current: ast.AST, *, root: bool = False) -> None:
        if root and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            values.append(current)
            visit_block(current.body)
            return
        if not root and isinstance(
            current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        values.append(current)
        if isinstance(current, ast.If):
            visit(current.test)
            truth = _literal_truth(current.test)
            if truth is True:
                visit_block(current.body)
            elif truth is False:
                visit_block(current.orelse)
            else:
                visit_block(current.body)
                visit_block(current.orelse)
            return
        if isinstance(current, ast.While):
            visit(current.test)
            if _literal_truth(current.test) is False:
                visit_block(current.orelse)
            else:
                visit_block(current.body)
                visit_block(current.orelse)
            return
        for _, child in ast.iter_fields(current):
            if isinstance(child, ast.AST):
                visit(child)
            elif isinstance(child, list):
                if all(isinstance(item, ast.stmt) for item in child):
                    visit_block(child)
                else:
                    for item in child:
                        if isinstance(item, ast.AST):
                            visit(item)

    visit(node, root=True)
    return values


def _callable_defaults(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names whose defaults are callable expressions; these are never witnesses."""
    positional = (*node.args.posonlyargs, *node.args.args)
    defaults = (None,) * (len(positional) - len(node.args.defaults)) + tuple(node.args.defaults)
    pairs = list(zip((item.arg for item in positional), defaults))
    pairs.extend(zip((item.arg for item in node.args.kwonlyargs), node.args.kw_defaults))
    return {
        name
        for name, default in pairs
        if isinstance(default, (ast.Attribute, ast.Lambda, ast.Call))
    }


def _read_blob_at_resolved(repo_root: Path, commit: str, path: str) -> bytes | None:
    """一度安全検証済みの exact commit から blob を読む。"""
    if "\x00" in path or "\r" in path or "\n" in path:
        raise core.PreregistrationError("path-control-char")
    spec = f"{commit}:{path}"
    header = core._git_text(
        repo_root,
        ["cat-file", "--batch-check"],
        stdin=f"{spec}\n".encode(),
    )
    tokens = header.split()
    if tokens and tokens[-1] == "missing":
        return None
    if (
        len(tokens) < 2
        or core._OBJECT_ID_RE.fullmatch(tokens[0]) is None
        or tokens[1] != "blob"
    ):
        raise core.PreregistrationError("path-not-blob", f"{spec}: {header!r}")
    if len(tokens) < 3 or not tokens[2].isdigit():
        raise core.PreregistrationError("cat-file-header", header)
    if int(tokens[2]) > core.MAX_BLOB_BYTES:
        raise core.PreregistrationError("blob-byte-limit", path)
    return core._git(repo_root, ["cat-file", "blob", tokens[0]])


@dataclass
class _ConditionProbe:
    repo_root: Path
    commit: str
    contract: ConditionContract
    contract_ref: core.EvidenceRef
    refs: dict[str, core.EvidenceRef]
    cache: dict[str, bytes | None]
    python_cache: dict[str, ast.Module | None] = field(default_factory=dict)
    declared_paths: frozenset[str] = frozenset()
    function_cache: dict[
        str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]
    ] = field(default_factory=dict)
    binding_cache: dict[
        str, tuple[dict[str, _Binding], tuple[str, ...]]
    ] = field(default_factory=dict)
    binding_dependencies_seen: set[str] = field(default_factory=set)
    graph_cache: dict[
        tuple[_CallableTarget, _ReachabilityLimits], _Reachability
    ] = field(default_factory=dict)
    reachability_modules: set[str] = field(default_factory=set)
    reachability_bytes: int = 0
    reachability_elapsed_s: float = 0.0

    def requirement(self, kind: str) -> RequiredEvidence:
        matches = [item for item in self.contract.required_evidence if item.artifact_kind == kind]
        if len(matches) != 1:
            raise EvidenceContractError("contract-artifact-kind", f"{self.contract.identifier}:{kind}")
        return matches[0]

    def read_kind(self, kind: str) -> bytes | None:
        return self.read_path(self.requirement(kind).path)

    def read_path(self, path: str) -> bytes | None:
        if path not in self.cache:
            raw = _read_blob_at_resolved(self.repo_root, self.commit, path)
            self.cache[path] = raw
        raw = self.cache[path]
        if raw is not None:
            self.refs[path] = core.EvidenceRef(path, core._sha256(raw))
        return raw

    def python_kind(self, kind: str) -> ast.Module | None:
        return self.python_path(self.requirement(kind).path)

    def python_path(
        self, path: str, *, limits: _ReachabilityLimits | None = None
    ) -> ast.Module | None:
        if path in self.python_cache:
            cached = self.python_cache[path]
            raw = self.cache.get(path)
            if raw is not None:
                self.refs[path] = core.EvidenceRef(path, core._sha256(raw))
            if (
                limits is not None
                and cached is not None
                and raw is not None
                and path not in self.reachability_modules
            ):
                if len(self.reachability_modules) + 1 > limits.modules:
                    raise EvidenceContractError(
                        ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value,
                        f"module>{limits.modules}",
                    )
                if self.reachability_bytes + len(raw) > limits.total_bytes:
                    raise EvidenceContractError(
                        ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value,
                        f"bytes>{limits.total_bytes}",
                    )
                self.reachability_modules.add(path)
                self.reachability_bytes += len(raw)
            return cached
        raw = self.read_path(path)
        if raw is None:
            self.python_cache[path] = None
            return None
        if limits is not None:
            if len(self.reachability_modules) + 1 > limits.modules:
                raise EvidenceContractError(
                    ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value,
                    f"module>{limits.modules}",
                )
            if self.reachability_bytes + len(raw) > limits.total_bytes:
                raise EvidenceContractError(
                    ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value,
                    f"bytes>{limits.total_bytes}",
                )
            self.reachability_modules.add(path)
            self.reachability_bytes += len(raw)
        try:
            tree = ast.parse(raw.decode("utf-8", "strict"), filename=path)
        except (UnicodeError, SyntaxError) as exc:
            raise EvidenceContractError("evidence-python-parse-error", str(exc)) from exc
        self.python_cache[path] = tree
        return tree

    def evidence(self) -> tuple[core.EvidenceRef, ...]:
        values = {self.contract_ref.path: self.contract_ref, **self.refs}
        return tuple(values[path] for path in sorted(values))


class _ReachabilityExplorer:
    """Bounded, deterministic resolver over committed production Python blobs."""

    def __init__(
        self, probe: _ConditionProbe, limits: _ReachabilityLimits | None = None
    ) -> None:
        self.probe = probe
        self.limits = limits or _ReachabilityLimits()
        self._bindings = probe.binding_cache
        self._binding_in_progress: set[str] = set()

    def _tree(self, path: str) -> ast.Module | None:
        if not _production_python_path(path):
            return None
        return self.probe.python_path(path, limits=self.limits)

    def _functions(
        self, path: str
    ) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
        cached = self.probe.function_cache.get(path)
        if cached is not None:
            self._tree(path)
            return cached
        tree = self._tree(path)
        if tree is None:
            return {}
        candidates: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        rebound: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                candidates.setdefault(node.name, []).append(node)
            else:
                rebound.update(_statement_bound_names(node))
        functions = {
            name: rows[0]
            for name, rows in candidates.items()
            if len(rows) == 1 and name not in rebound
        }
        self.probe.function_cache[path] = functions
        return functions

    def _module_path(self, parts: tuple[str, ...]) -> str | None:
        if not parts or any(not part.isidentifier() for part in parts):
            return None
        candidates = (
            "/".join(parts) + ".py",
            "/".join(parts) + "/__init__.py",
        )
        existing = [path for path in candidates if self._tree(path) is not None]
        return existing[0] if len(existing) == 1 else None

    def _import_parts(self, path: str, node: ast.ImportFrom) -> tuple[str, ...] | None:
        if node.level:
            package = _package_name(path)
            if node.level > len(package) + 1:
                return None
            prefix = package[: len(package) - node.level + 1]
        else:
            prefix = ()
        suffix = () if node.module is None else tuple(node.module.split("."))
        parts = (*prefix, *suffix)
        return parts if all(part.isidentifier() for part in parts) else None

    def _initializer_shadows(self, package: tuple[str, ...], name: str) -> bool:
        init_path = "/".join(package) + "/__init__.py"
        tree = self._tree(init_path)
        if tree is None:
            return False
        return any(name in _statement_bound_names(node) for node in tree.body)

    def _resolve_from_module(self, path: str, name: str) -> _Binding | None:
        functions = self._functions(path)
        if name in functions:
            return _CallableBinding((path, name))
        return None

    def _bindings_for(self, path: str) -> dict[str, _Binding]:
        cached = self._bindings.get(path)
        if cached is not None:
            bindings, dependencies = cached
            if path not in self.probe.binding_dependencies_seen:
                for dependency in dependencies:
                    self._tree(dependency)
                self.probe.binding_dependencies_seen.add(path)
            return bindings
        if path in self._binding_in_progress:
            return {}
        self._binding_in_progress.add(path)
        modules_before = set(self.probe.reachability_modules)
        tree = self._tree(path)
        bindings: dict[str, _Binding] = {}
        counts: dict[str, int] = {}
        bound_rows: dict[str, list[ast.stmt]] = {}
        if tree is not None:
            for node in tree.body:
                for name in _statement_bound_names(node):
                    counts[name] = counts.get(name, 0) + 1
                    bound_rows.setdefault(name, []).append(node)

            def unambiguous_import(local: str, node: ast.stmt) -> bool:
                if counts.get(local) == 1:
                    return True
                if not isinstance(node, ast.Import):
                    return False
                rows = bound_rows.get(local, [])
                return bool(rows) and all(
                    isinstance(row, ast.Import)
                    and any(
                        alias.asname is None
                        and alias.name.split(".", 1)[0] == local
                        for alias in row.names
                    )
                    for row in rows
                )

            for node in tree.body:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        parts = tuple(alias.name.split("."))
                        module_path = self._module_path(parts)
                        if module_path is None:
                            continue
                        local = alias.asname or parts[0]
                        if not unambiguous_import(local, node):
                            continue
                        if alias.asname is None:
                            previous = bindings.get(local)
                            imported = {module_path}
                            if isinstance(previous, _ModuleBinding):
                                imported.update(previous.root_imports or (previous.path,))
                            bindings[local] = _ModuleBinding(
                                module_path, tuple(sorted(imported))
                            )
                        else:
                            bindings[local] = _ModuleBinding(module_path)
                elif isinstance(node, ast.ImportFrom):
                    base = self._import_parts(path, node)
                    if base is None:
                        continue
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        local = alias.asname or alias.name
                        if not unambiguous_import(local, node):
                            continue
                        if node.module is None:
                            if self._initializer_shadows(base, alias.name):
                                continue
                            module_path = self._module_path((*base, alias.name))
                            if module_path is not None:
                                bindings[local] = _ModuleBinding(module_path)
                        else:
                            module_path = self._module_path(base)
                            if module_path is None:
                                continue
                            binding = self._resolve_from_module(module_path, alias.name)
                            if binding is not None:
                                bindings[local] = binding
            # Resolve exact, single module-level callable aliases after imports.
            for node in tree.body:
                target: ast.Name | None = None
                value: ast.AST | None = None
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    target, value = node.targets[0], node.value
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    target, value = node.target, node.value
                if target is None or value is None or counts.get(target.id) != 1:
                    continue
                resolved = self._resolve_expr(path, value, {}, set(), bindings=bindings)
                if resolved is not None:
                    bindings[target.id] = _CallableBinding(resolved)
        self._binding_in_progress.remove(path)
        dependencies = tuple(
            sorted(self.probe.reachability_modules - modules_before)
        )
        self._bindings[path] = (bindings, dependencies)
        self.probe.binding_dependencies_seen.add(path)
        return bindings

    def _resolve_expr(
        self,
        path: str,
        expr: ast.AST,
        local: Mapping[str, _CallableTarget],
        shadowed: set[str],
        *,
        bindings: Mapping[str, _Binding] | None = None,
    ) -> _CallableTarget | None:
        module_bindings = self._bindings_for(path) if bindings is None else bindings
        if isinstance(expr, ast.Name):
            if expr.id in local:
                return local[expr.id]
            if expr.id in shadowed:
                return None
            binding = module_bindings.get(expr.id)
            if isinstance(binding, _CallableBinding):
                return binding.target
            if expr.id in self._functions(path):
                return (path, expr.id)
            return None
        if isinstance(expr, ast.Attribute):
            chain: list[str] = []
            current: ast.AST = expr
            while isinstance(current, ast.Attribute):
                chain.append(current.attr)
                current = current.value
            if not isinstance(current, ast.Name) or current.id in shadowed:
                return None
            chain.reverse()
            binding = module_bindings.get(current.id)
            if not isinstance(binding, _ModuleBinding) or not chain:
                return None
            module_path = binding.path
            if len(chain) > 1:
                bound_parts = _module_name(module_path)
                if binding.root_imports:
                    requested = (current.id, *chain[:-1])
                    matches = [
                        candidate
                        for candidate in binding.root_imports
                        if _module_name(candidate) == requested
                    ]
                    if len(matches) != 1:
                        return None
                    module_path = matches[0]
                elif tuple(chain[:-1]) != bound_parts[1:]:
                    module_parts = (*bound_parts, *chain[:-1])
                    resolved_path = self._module_path(module_parts)
                    if resolved_path is None:
                        return None
                    module_path = resolved_path
            return (
                (module_path, chain[-1])
                if chain[-1] in self._functions(module_path)
                else None
            )
        return None

    @staticmethod
    def _assignment_rows(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> dict[str, list[tuple[ast.AST, ast.AST | None]]]:
        rows: dict[str, list[tuple[ast.AST, ast.AST | None]]] = {}
        for current in _live_nodes(node):
            if isinstance(current, ast.Assign):
                for target in current.targets:
                    if isinstance(target, ast.Name):
                        rows.setdefault(target.id, []).append((current.value, current))
            elif isinstance(current, ast.AnnAssign) and isinstance(current.target, ast.Name):
                rows.setdefault(current.target.id, []).append((current.value, current))
        return rows

    @staticmethod
    def _sentinel_assignment(
        node: ast.FunctionDef | ast.AsyncFunctionDef, name: str, assignment: ast.AST
    ) -> tuple[int, int] | None:
        # The only admitted conditional assignment is ``if p is SENTINEL: p = f``
        # for an omitted parameter whose default is a non-callable Name sentinel.
        positional = (*node.args.posonlyargs, *node.args.args)
        defaults = (None,) * (len(positional) - len(node.args.defaults)) + tuple(node.args.defaults)
        default_map = dict(zip((item.arg for item in positional), defaults))
        default_map.update(
            zip((item.arg for item in node.args.kwonlyargs), node.args.kw_defaults)
        )
        default = default_map.get(name)
        if not isinstance(default, ast.Name):
            return None
        for current in node.body:
            if not isinstance(current, ast.If):
                continue
            test = current.test
            if not (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == name
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Is)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Name)
                and test.comparators[0].id == default.id
            ):
                continue
            if current.orelse or len(current.body) != 1 or current.body[0] is not assignment:
                continue
            if not (
                isinstance(assignment, ast.Assign)
                and len(assignment.targets) == 1
                and isinstance(assignment.targets[0], ast.Name)
                and assignment.targets[0].id == name
            ):
                continue
            return (
                getattr(current, "end_lineno", current.lineno),
                getattr(current, "end_col_offset", current.col_offset),
            )
        return None

    @staticmethod
    def _position(node: ast.AST) -> tuple[int, int]:
        return (getattr(node, "lineno", -1), getattr(node, "col_offset", -1))

    @staticmethod
    def _same_block_precedes(
        root: ast.FunctionDef | ast.AsyncFunctionDef,
        assignment: ast.stmt,
        use: ast.AST,
    ) -> bool:
        """同じ statement list 内の先行文だけを無条件の支配とみなす。"""

        def locate(owner: ast.AST, target: ast.AST) -> tuple[int, str, int] | None:
            for field_name, value in ast.iter_fields(owner):
                if not isinstance(value, list):
                    continue
                statement_rows = [item for item in value if isinstance(item, ast.stmt)]
                if len(statement_rows) != len(value):
                    for item in value:
                        if isinstance(item, ast.AST):
                            found = locate(item, target)
                            if found is not None:
                                return found
                    continue
                for index, statement in enumerate(statement_rows):
                    found = locate(statement, target)
                    if found is not None:
                        return found
                    if statement is target or any(
                        candidate is target for candidate in ast.walk(statement)
                    ):
                        return (id(owner), field_name, index)
            return None

        assigned_at = locate(root, assignment)
        used_at = locate(root, use)
        return (
            assigned_at is not None
            and used_at is not None
            and assigned_at[:2] == used_at[:2]
            and assigned_at[2] < used_at[2]
        )

    @staticmethod
    def _available_local(
        local: Mapping[str, _CallableTarget],
        availability: Mapping[str, tuple[int, int]],
        current: ast.AST,
    ) -> dict[str, _CallableTarget]:
        position = _ReachabilityExplorer._position(current)
        return {
            name: target
            for name, target in local.items()
            if availability.get(name, (-1, -1)) < position
        }

    def _local_bindings(
        self,
        path: str,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        incoming: Mapping[str, _CallableTarget],
        blocked: set[str],
    ) -> tuple[
        dict[str, _CallableTarget],
        set[str],
        dict[str, tuple[int, int]],
    ]:
        local = dict(incoming)
        availability = {name: (-1, -1) for name in incoming}
        assignments = self._assignment_rows(node)
        scope = _scope_nodes(node)
        assignment_names = {
            target.id
            for current in scope
            for target in (
                current.targets
                if isinstance(current, ast.Assign)
                else (current.target,) if isinstance(current, ast.AnnAssign) else ()
            )
            if isinstance(target, ast.Name)
        }
        parameters = set(_function_parameters(node))
        callable_defaults = _callable_defaults(node)
        unsafe_bindings: set[str] = set()
        for current in scope:
            if isinstance(current, (ast.Assign, ast.AnnAssign)):
                continue
            unsafe_bindings.update(_direct_bound_names(current))
        for name in unsafe_bindings:
            local.pop(name, None)
            availability.pop(name, None)
        shadowed = (
            parameters
            | assignment_names
            | callable_defaults
            | blocked
            | unsafe_bindings
        )
        ordered = sorted(
            assignments.items(),
            key=lambda item: min(self._position(row[1]) for row in item[1]),
        )
        for name, rows in ordered:
            if len(rows) != 1 or name in callable_defaults:
                local.pop(name, None)
                availability.pop(name, None)
                continue
            value, assignment = rows[0]
            available_after: tuple[int, int] | None
            if name in parameters:
                if name in incoming or name in blocked:
                    continue
                available_after = self._sentinel_assignment(node, name, assignment)
                if available_after is None:
                    continue
            elif assignment not in node.body:
                # Conditional/loop/exception assignments are not a witness.
                continue
            else:
                available_after = (
                    getattr(assignment, "end_lineno", assignment.lineno),
                    getattr(assignment, "end_col_offset", assignment.col_offset),
                )
            visible = self._available_local(local, availability, assignment)
            resolved = self._resolve_expr(path, value, visible, shadowed - {name})
            if resolved is not None:
                local[name] = resolved
                availability[name] = available_after
        return local, shadowed, availability

    def _dict_keywords(
        self,
        path: str,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        local: Mapping[str, _CallableTarget],
        shadowed: set[str],
        availability: Mapping[str, tuple[int, int]],
    ) -> dict[str, _DictCarrier]:
        result: dict[str, _DictCarrier] = {}
        scope = _scope_nodes(node)
        candidates: list[tuple[str, ast.Assign]] = []
        for current in scope:
            if not (
                isinstance(current, ast.Assign)
                and len(current.targets) == 1
                and isinstance(current.targets[0], ast.Name)
            ):
                continue
            candidates.append((current.targets[0].id, current))
        for name, assignment in candidates:
            binding_count = sum(
                name in _direct_bound_names(current) for current in scope
            )
            if binding_count != 1:
                continue
            value = assignment.value
            if not (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "dict"
                and not value.args
                and all(keyword.arg is not None for keyword in value.keywords)
            ):
                continue
            splats = [
                (current, keyword)
                for current in scope
                if isinstance(current, ast.Call)
                for keyword in current.keywords
                if keyword.arg is None
                and isinstance(keyword.value, ast.Name)
                and keyword.value.id == name
            ]
            if len(splats) != 1 or not self._same_block_precedes(
                node, assignment, splats[0][0]
            ):
                continue
            mutated_keys: set[str] = set()
            invalid = False
            allowed_loads = {id(splats[0][1].value)}
            for current in scope:
                if isinstance(current, ast.Call) and isinstance(current.func, ast.Attribute):
                    if isinstance(current.func.value, ast.Name) and current.func.value.id == name:
                        invalid = True
                targets: Sequence[ast.AST] = ()
                if isinstance(current, ast.Assign):
                    targets = current.targets
                elif isinstance(current, (ast.AnnAssign, ast.AugAssign)):
                    targets = (current.target,)
                elif isinstance(current, ast.Delete):
                    targets = tuple(current.targets)
                for target in targets:
                    if not (
                        isinstance(target, ast.Subscript)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == name
                    ):
                        continue
                    allowed_loads.add(id(target.value))
                    if not isinstance(current, ast.Assign):
                        invalid = True
                        continue
                    key = target.slice
                    if not (
                        isinstance(key, ast.Constant)
                        and type(key.value) is str
                    ):
                        invalid = True
                        continue
                    mutated_keys.add(key.value)
            if any(
                isinstance(current, ast.Name)
                and isinstance(current.ctx, ast.Load)
                and current.id == name
                and id(current) not in allowed_loads
                for current in scope
            ):
                invalid = True
            if invalid:
                continue
            visible = self._available_local(local, availability, assignment)
            keywords = {
                keyword.arg: self._resolve_expr(path, keyword.value, visible, shadowed)
                for keyword in value.keywords
                if keyword.arg is not None
            }
            result[name] = _DictCarrier(
                tuple(sorted(keywords.items())), frozenset(mutated_keys)
            )
        return result

    def walk(self, start: _CallableTarget) -> _Reachability:
        cache_key = (start, self.limits)
        cached_graph = self.probe.graph_cache.get(cache_key)
        if cached_graph is not None:
            for path in cached_graph.modules:
                self._tree(path)
            return cached_graph
        pending = [_CallState(start)]
        visited: set[tuple[object, ...]] = set()
        functions: set[_CallableTarget] = set()
        calls: set[_CallableTarget] = set()
        attributes: set[str] = set()
        while pending:
            pending.sort(key=lambda item: (item.depth, item.target, item.bindings, item.blocked))
            state = pending.pop(0)
            if state.depth > self.limits.depth:
                raise EvidenceContractError(
                    ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value,
                    f"depth>{self.limits.depth}",
                )
            key = state.key()
            if key in visited:
                continue
            if len(visited) + 1 > self.limits.states:
                raise EvidenceContractError(
                    ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value,
                    f"states>{self.limits.states}",
                )
            visited.add(key)
            path, name = state.target
            function = self._functions(path).get(name)
            if function is None:
                continue
            functions.add(state.target)
            incoming = dict(state.bindings)
            blocked = set(state.blocked)
            local, shadowed, availability = self._local_bindings(
                path, function, incoming, blocked
            )
            dicts = self._dict_keywords(
                path, function, local, shadowed, availability
            )
            live = _live_nodes(function)
            attributes.update(
                current.attr for current in live if isinstance(current, ast.Attribute)
            )
            successors: list[_CallState] = []
            for current in live:
                if not isinstance(current, ast.Call):
                    continue
                visible = self._available_local(local, availability, current)
                target = self._resolve_expr(path, current.func, visible, shadowed)
                if target is None:
                    continue
                calls.add(target)
                target_function = self._functions(target[0]).get(target[1])
                if target_function is None:
                    continue
                target_params = set(_function_parameters(target_function))
                positional_params = tuple(
                    item.arg
                    for item in (
                        *target_function.args.posonlyargs,
                        *target_function.args.args,
                    )
                )
                propagated: dict[str, _CallableTarget] = {}
                target_blocked: set[str] = set()
                hard_blocked: set[str] = set()
                for index, argument in enumerate(current.args):
                    if isinstance(argument, ast.Starred):
                        hard_blocked.update(target_params)
                    elif index < len(positional_params):
                        hard_blocked.add(positional_params[index])
                for keyword in current.keywords:
                    if keyword.arg is None:
                        if isinstance(keyword.value, ast.Name):
                            carrier = dicts.get(keyword.value.id)
                            if carrier is None:
                                hard_blocked.update(target_params)
                                continue
                            values = dict(carrier.keywords)
                            for arg in target_params:
                                if arg in carrier.mutated_keys:
                                    hard_blocked.add(arg)
                                    continue
                                if arg not in values:
                                    continue
                                value = values[arg]
                                if arg not in target_params:
                                    continue
                                if value is None:
                                    target_blocked.add(arg)
                                else:
                                    if arg in propagated or arg in target_blocked:
                                        hard_blocked.add(arg)
                                    propagated[arg] = value
                        else:
                            hard_blocked.update(target_params)
                        continue
                    if keyword.arg not in target_params:
                        continue
                    if keyword.arg in propagated or keyword.arg in target_blocked:
                        hard_blocked.add(keyword.arg)
                    value = self._resolve_expr(path, keyword.value, visible, shadowed)
                    if value is None:
                        target_blocked.add(keyword.arg)
                    else:
                        propagated[keyword.arg] = value
                target_blocked.update(hard_blocked)
                for name in hard_blocked:
                    propagated.pop(name, None)
                successors.append(
                    _CallState(
                        target,
                        tuple(sorted(propagated.items())),
                        tuple(sorted(target_blocked)),
                        state.depth + 1,
                    )
                )
            pending.extend(successors)
        graph = _Reachability(
            frozenset(functions),
            frozenset(calls),
            frozenset(attributes),
            tuple(sorted(self.probe.reachability_modules)),
        )
        self.probe.graph_cache[cache_key] = graph
        return graph


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


def _declared_call(
    probe: _ConditionProbe, graph: _Reachability, target: _CallableTarget
) -> bool:
    return target[0] in probe.declared_paths and target in graph.calls


def _attribute_names(node: ast.AST) -> set[str]:
    return {
        current.attr
        for current in ast.walk(node)
        if isinstance(current, ast.Attribute)
    }


def _top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
    return names


def _call_target_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _calls_named(node: ast.AST, name: str) -> tuple[ast.Call, ...]:
    candidates = (
        _live_nodes(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        else list(ast.walk(node))
    )
    return tuple(
        current
        for current in candidates
        if isinstance(current, ast.Call) and _call_target_name(current) == name
    )


def _keyword_value(call: ast.Call, name: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _positional_or_keyword_value(
    call: ast.Call, *, index: int, name: str
) -> ast.AST | None:
    keyword_value = _keyword_value(call, name)
    if keyword_value is not None:
        return keyword_value
    return call.args[index] if len(call.args) > index else None


def _is_name(node: ast.AST | None, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _has_attribute(node: ast.AST | None, name: str) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == name


def _has_live_assignment(
    node: ast.FunctionDef | ast.AsyncFunctionDef, name: str
) -> bool:
    for current in _live_nodes(node):
        targets: tuple[ast.AST, ...]
        if isinstance(current, ast.Assign):
            targets = tuple(current.targets)
        elif isinstance(current, (ast.AnnAssign, ast.AugAssign)):
            targets = (current.target,)
        else:
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name for target in targets
        ):
            return True
    return False


def _contains_legacy_return(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Reject a legacy acceptance branch that returns before strict checks."""
    for current in _live_nodes(node):
        if not isinstance(current, ast.If):
            continue
        names = {
            child.id
            for child in ast.walk(current.test)
            if isinstance(child, ast.Name)
        }
        names.update(
            child.attr
            for child in ast.walk(current.test)
            if isinstance(child, ast.Attribute)
        )
        if any("legacy" in name.casefold() for name in names) and any(
            isinstance(child, ast.Return)
            for statement in current.body
            for child in ast.walk(statement)
        ):
            return True
    return False


def _acceptance_function(
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> tuple[str, ast.FunctionDef | ast.AsyncFunctionDef] | None:
    for name in ("assert_trial_registry_acceptance", "accept_trial"):
        function = functions.get(name)
        if function is not None:
            return name, function
    return None


def _evaluate_c03(probe: _ConditionProbe) -> core.PredicateResult:
    """Inspect the C03 static shape without making it SATISFIED."""
    registry_path = probe.requirement("trial_registry").path
    registry = probe.python_kind("trial_registry")
    if registry is None:
        return _result(
            probe,
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            ReasonCode.TRIAL_REGISTRY_CAPABILITY_ABSENT,
        )

    functions = _functions(registry)
    required = {
        "load_trial_manifest",
        "load_effective_binding_at_commit",
        "validate_preregistration_binding",
        "_find_registration_for_manifest",
        "_assert_manifest_registry_trial_set",
        "_assert_runtime_report_trial_set",
        "_assert_runtime_report_cells",
        "load_attempt_registry",
        "reserve_attempt_slot",
        "create_attempt_registry_genesis",
        "classify_attempt",
        "begin_attempt_observation",
        "record_attempt_terminal",
    }
    acceptance = _acceptance_function(functions)
    if acceptance is None or not required <= functions.keys():
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    acceptance_name, acceptance_node = acceptance

    canonical = functions["_trial_canonical_tuple"] if "_trial_canonical_tuple" in functions else None
    if canonical is None or not {
        "trial_id", "arm", "holdout", "campaign_id", "generations"
    } <= {
        current.attr
        for current in _live_nodes(canonical)
        if isinstance(current, ast.Attribute)
    }:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    compare = functions["_assert_manifest_registry_trial_set"]
    if (
        len(_calls_named(compare, "_trial_canonical_tuple")) < 2
        or not {"set", "len"} <= _live_called_names(compare)
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    runtime_cells = functions["_assert_runtime_report_cells"]
    if not {
        "cells", "workload", "workload_flags", "ycsb_rratio", "campaign_id"
    } <= {
        child.value
        for child in _live_nodes(runtime_cells)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    } or "get" not in _live_called_names(runtime_cells):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    if _contains_legacy_return(acceptance_node):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )

    registry_graph = _ReachabilityExplorer(probe).walk(
        (registry_path, acceptance_name)
    )
    required_acceptance_targets = {
        "load_trial_manifest",
        "load_effective_binding_at_commit",
        "validate_preregistration_binding",
        "_find_registration_for_manifest",
        "_assert_manifest_registry_trial_set",
        "_assert_runtime_report_trial_set",
        "_assert_runtime_report_cells",
        "load_attempt_registry",
    }
    if not all(
        _declared_call(probe, registry_graph, (registry_path, name))
        for name in required_acceptance_targets
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )

    producer_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    producer = probe.python_path(producer_path)
    if producer is None or "run_trial" not in _functions(producer):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    if "_reserve_registered_attempt_slot" not in _reachable_calls(
        producer, "run_trial"
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    producer_graph = _ReachabilityExplorer(probe).walk((producer_path, "run_trial"))
    required_producer_targets = {
        "reserve_attempt_slot",
        "classify_attempt",
        "begin_attempt_observation",
        "record_attempt_terminal",
    }
    if not all(
        (registry_path, name) in producer_graph.calls
        for name in required_producer_targets
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )

    if not {
        "MANIFEST_SCHEMA_VERSION",
        "REGISTRATION_SCHEMA_VERSION",
        "DEFAULT_ATTEMPT_REGISTRY_PATH",
        "ATTEMPT_REGISTRY_SCHEMA_VERSION",
        "ATTEMPT_STATUSES",
        "ATTEMPT_RETRYABLE_FAILURE_REASONS",
    } <= _top_level_names(registry):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    fields = _attribute_names(registry) | _strings(registry)
    if not {
        "manifest_sha256",
        "prereg_content_commit",
        "prereg_effective_commit",
        "trials",
        "cells",
    } <= fields:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
        )
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.MANIFEST_REGISTRY_PROOF_UNDEFINED,
    )


def _evaluate_c08(probe: _ConditionProbe) -> core.PredicateResult:
    """Inspect P/C/H binding flow on both admission and acceptance paths."""
    registry_path = probe.requirement("trial_registry").path
    registry = probe.python_kind("trial_registry")
    if registry is None:
        return _result(
            probe,
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            ReasonCode.PREREG_BINDING_CAPABILITY_ABSENT,
        )

    functions = _functions(registry)
    required = {
        "assert_effective_commit_exact_parent",
        "load_effective_binding_at_commit",
        "validate_preregistration_binding",
        "_blob_at_commit",
        "_assert_ancestor",
        "admit_registered_launch",
        "load_launch_binding",
        "_derive_launch_binding",
        "assert_trial_registry_acceptance",
    }
    if not required <= functions.keys():
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )

    validator = functions["validate_preregistration_binding"]
    if _has_live_assignment(validator, "effective_commit"):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )
    exact_parent_calls = _calls_named(
        validator, "assert_effective_commit_exact_parent"
    )
    if len(exact_parent_calls) != 1:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )
    exact_parent = exact_parent_calls[0]
    if not (
        _is_name(_keyword_value(exact_parent, "effective_commit"), "effective_commit")
        and _has_attribute(
            _keyword_value(exact_parent, "content_commit"),
            "prereg_content_commit",
        )
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )

    binding_calls = _calls_named(validator, "load_effective_binding_at_commit")
    if not any(
        _is_name(
            _positional_or_keyword_value(call, index=1, name="effective_commit"),
            "effective_commit",
        )
        for call in binding_calls
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )
    blob_loader = functions["load_effective_binding_at_commit"]
    if not any(
        _is_name(_keyword_value(call, "commit_id"), "effective_commit")
        for call in _calls_named(blob_loader, "_blob_at_commit")
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )
    if not any(
        _is_name(_keyword_value(call, "ancestor"), "effective_commit")
        and _is_name(_keyword_value(call, "descendant"), "measurement_commit")
        for call in _calls_named(validator, "_assert_ancestor")
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
        )

    admission_graph = _ReachabilityExplorer(probe).walk(
        (registry_path, "admit_registered_launch")
    )
    acceptance_graph = _ReachabilityExplorer(probe).walk(
        (registry_path, "assert_trial_registry_acceptance")
    )
    for graph in (admission_graph, acceptance_graph):
        if not all(
            _declared_call(probe, graph, (registry_path, name))
            for name in (
                "validate_preregistration_binding",
                "assert_effective_commit_exact_parent",
                "load_effective_binding_at_commit",
                "_blob_at_commit",
                "_assert_ancestor",
            )
        ):
            return _result(
                probe,
                core.PredicateStatus.UNSATISFIED,
                ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
            )

    for graph in (admission_graph, acceptance_graph):
        for path, name in graph.functions:
            if path != registry_path:
                continue
            function = functions.get(name)
            if function is None:
                continue
            for call in _calls_named(function, "validate_preregistration_binding"):
                value = _keyword_value(call, "effective_commit")
                if value is None or any(
                    _has_attribute(value, attribute)
                    for attribute in ("prereg_commit", "prereg_content_commit")
                ):
                    return _result(
                        probe,
                        core.PredicateStatus.UNSATISFIED,
                        ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
                    )
                if not (
                    _is_name(value, "effective_commit")
                    or _has_attribute(value, "prereg_effective_commit")
                ):
                    return _result(
                        probe,
                        core.PredicateStatus.UNSATISFIED,
                        ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
                    )

    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.PREREG_BINDING_PROOF_UNDEFINED,
    )


def _evaluate_c01(probe: _ConditionProbe) -> core.PredicateResult:
    workload_path = probe.requirement("workload_supervisor").path
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    functions = _functions(tree)
    sinks = ("_campaign_for", "_perf_for", "_descriptor_for")
    if any(name not in functions for name in sinks):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.WORKLOAD_CONSUMER_UNREACHABLE)
    if any(not {1_000_000, 48} <= _integers(functions[name]) for name in sinks):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.WORKLOAD_PROJECTION_MISMATCH)
    graph = _ReachabilityExplorer(probe).walk((workload_path, "main"))
    if not {(workload_path, name) for name in sinks} <= graph.functions or (
        workload_path, "run_trial"
    ) not in graph.functions:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.WORKLOAD_CONSUMER_UNREACHABLE)
    ratified = probe.python_kind("ratified_generation_reference")
    ratified_path = probe.requirement("ratified_generation_reference").path
    if (
        ratified is None
        or "load_ratified_freeze" not in _functions(ratified)
        or not _declared_call(
            probe, graph, (ratified_path, "load_ratified_freeze")
        )
        or not {"sha256", "holdouts"} <= graph.attributes
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.RATIFIED_GENERATION_REFERENCE_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c02(probe: _ConditionProbe) -> core.PredicateResult:
    registry = probe.python_kind("trial_registry")
    if registry is None:
        return _result(
            probe,
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            ReasonCode.TRIAL_REGISTRY_CAPABILITY_ABSENT,
        )
    functions = _functions(registry)
    required_calls = {
        "bind_trial_arm": {"assert_issued_trial_binding", "resolve_arm_input"},
        "assert_issued_trial_arm_execution": {
            "assert_issued_trial_binding",
            "assert_issued_resolved_arm_input",
        },
        "assert_rederived_trial_arm_execution": {
            "assert_issued_trial_arm_execution",
            "bind_trial_arm",
        },
        "_expected_registered_arm_execution_record": {"resolve_arm_input"},
        "assert_trial_registry_acceptance": {
            "_expected_registered_arm_execution_record",
            "validate_execution_input_descriptor",
            "assert_execution_digest_chain",
        },
    }
    for name, expected in required_calls.items():
        function = functions.get(name)
        if function is None:
            return _result(
                probe,
                core.PredicateStatus.UNSATISFIED,
                ReasonCode.ARM_BINDING_CONSUMER_UNREACHABLE,
            )
        if not expected <= _live_called_names(function):
            return _result(
                probe,
                core.PredicateStatus.UNSATISFIED,
                ReasonCode.ARM_BINDING_CONSUMER_UNREACHABLE,
            )

    binding_fields = {
        current.value
        for current in _live_nodes(functions["_expected_registered_arm_execution_record"])
        if isinstance(current, ast.Constant) and isinstance(current.value, str)
    }
    acceptance_fields = {
        current.value
        for current in _live_nodes(functions["assert_trial_registry_acceptance"])
        if isinstance(current, ast.Constant) and isinstance(current.value, str)
    }
    if not {
        "input_schema_version",
        "content_digest_sha256",
        "arm_binding_digest_sha256",
    } <= binding_fields or "arm_execution" not in acceptance_fields:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.ARM_BINDING_CONSUMER_UNREACHABLE,
        )

    producer = probe.python_kind("proposal_namespace_producer")
    producer_functions = _functions(producer) if producer is not None else {}
    namespace = producer_functions.get("_invocation_namespace")
    producer_consumers = ("_invocation_id", "_run_workload", "run_trial")
    namespace_binds_arm_and_digest = (
        namespace is not None
        and _returns_joined_string_using(namespace, {"arm", "digest"})
    )
    consumers_use_namespace = all(
        name in producer_functions
        and "_invocation_namespace" in _live_called_names(producer_functions[name])
        for name in producer_consumers
    )
    if not namespace_binds_arm_and_digest or not consumers_use_namespace:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.ARM_BINDING_CONSUMER_UNREACHABLE,
        )
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c04(probe: _ConditionProbe) -> core.PredicateResult:
    workload_path = probe.requirement("workload_supervisor").path
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    graph = _ReachabilityExplorer(probe).walk((workload_path, "main"))
    if (workload_path, "run_trial") not in graph.functions:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRASH_POLICY_CELL_PARTIAL)
    registry_path = probe.requirement("trial_registry").path
    if not all(
        _declared_call(probe, graph, target)
        for target in (
            (workload_path, "mark_experiment_indeterminate"),
            (registry_path, "forbid_trial_restart"),
        )
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRASH_POLICY_CELL_PARTIAL)
    registry = probe.python_kind("trial_registry")
    if registry is None or "forbid_trial_restart" not in _functions(registry):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.RESTART_GUARD_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c05(probe: _ConditionProbe) -> core.PredicateResult:
    if probe.read_kind("schedule_artifact") is None:
        return _result(
            probe,
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            ReasonCode.SCHEDULE_SCHEMA_ABSENT,
        )

    consumer = probe.python_kind("schedule_consumer")
    if consumer is None:
        return _result(
            probe,
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            ReasonCode.SCHEDULE_CONSUMER_UNDEFINED,
        )

    functions = _functions(consumer)
    required_functions = {
        "validate_authority",
        "search_space_digest",
        "initial_state_digest",
        "regenerate",
        "load_schedule",
        "verify_exact_schedule_bytes",
        "verify_shared_search_space_and_initial_state",
        "verify_schedule",
        "consume_schedule",
    }
    if not required_functions <= functions.keys():
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.SCHEDULE_CONSUMER_UNDEFINED,
        )

    required_calls = {
        "verify_schedule": {
            "verify_exact_schedule_bytes",
            "verify_shared_search_space_and_initial_state",
            "validate_authority",
        },
        "consume_schedule": {"verify_schedule"},
        "verify_exact_schedule_bytes": {"regenerate"},
    }
    for name, expected in required_calls.items():
        if not expected <= _live_called_names(functions[name]):
            return _result(
                probe,
                core.PredicateStatus.UNSATISFIED,
                ReasonCode.SCHEDULE_CONSUMER_UNREACHABLE,
            )

    field_literals = {
        current.value
        for name in required_functions
        for current in _live_nodes(functions[name])
        if isinstance(current, ast.Constant) and isinstance(current.value, str)
    }
    if not {
        "schema_version",
        "master_seed",
        "cells",
        "schedule_index",
        "arm",
        "holdout",
        "search_space_sha256",
        "initial_state_sha256",
    } <= field_literals:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.SCHEDULE_CONSUMER_UNDEFINED,
        )

    workload_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    try:
        workload = probe.python_kind("workload_supervisor")
    except EvidenceContractError as exc:
        if exc.reason_code != "contract-artifact-kind":
            raise
        # C05 declares the two reachable evidence edges, not a third artifact
        # kind.  Resolve the named production supervisor path directly for
        # the reachability part of this static check.
        workload = probe.python_path(workload_path)
    if workload is None or "run_trial" not in _functions(workload):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.SCHEDULE_CONSUMER_UNREACHABLE,
        )

    graph = _ReachabilityExplorer(probe).walk((workload_path, "run_trial"))
    consumer_path = probe.requirement("schedule_consumer").path
    required_targets = {
        (consumer_path, "verify_schedule"),
        (consumer_path, "consume_schedule"),
        (consumer_path, "load_schedule"),
    }
    if not required_targets <= graph.calls:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.SCHEDULE_CONSUMER_UNREACHABLE,
        )

    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _evaluate_c09(probe: _ConditionProbe) -> core.PredicateResult:
    producer_path = probe.requirement("layer3_producer").path
    producer = probe.python_kind("layer3_producer")
    graph = (
        None
        if producer is None
        else _ReachabilityExplorer(probe).walk((producer_path, "main"))
    )
    if graph is None or not any(
        path in probe.declared_paths and name == "assert_campaign_layer3_chain"
        for path, name in graph.calls
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.LAYER3_PRODUCER_UNREACHABLE)
    registry = probe.python_kind("trial_registry")
    functions = _functions(registry) if registry is not None else {}
    accept = functions.get("assert_trial_registry_acceptance")
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


_C10_CROSS_BINDING_FIELD_BINDINGS = (
    ("input_payload_sha256", "role_event.input_payload_sha256"),
    ("raw_response_path", "role_event.raw_response_path"),
    ("raw_response_sha256", "role_event.raw_response_sha256"),
    ("provider_payload_sha256", "provider.payload_sha256"),
    ("provider_envelope_sha256", "provider.envelope_sha256"),
    ("proposal_path", "proposal.path"),
    ("proposal_sha256", "proposal.sha256"),
    ("proposal_build_source_bindings", "proposal.build_source_bindings"),
    ("build_records", "campaign_wal.build_records"),
    ("bench_records", "campaign_wal.bench_records"),
    ("artifact_refs", "layer3.artifact_refs"),
    ("source_refs", "layer3.source_refs"),
    ("admission_decision", "layer3.admission_decision"),
)
_C10_FIELDS = frozenset(
    literal for literal, _ in _C10_CROSS_BINDING_FIELD_BINDINGS
)
_C10_EXPECTED_FIELD_PATHS = frozenset(
    path for _, path in _C10_CROSS_BINDING_FIELD_BINDINGS
)


def _c10_field_paths_verdict(probe: _ConditionProbe) -> bool:
    return (
        frozenset(
            probe.requirement("cross_binding_verifier").field_paths
        )
        == _C10_EXPECTED_FIELD_PATHS
    )


def _c10_single_function(
    tree: ast.Module,
    name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    return matches[0] if len(matches) == 1 else None


def _c10_reader_is_not_noop(
    reader: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    statements = list(reader.body)
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and type(statements[0].value.value) is str
    ):
        statements.pop(0)
    return bool(statements) and not all(
        isinstance(statement, ast.Pass)
        or (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and statement.value.value is Ellipsis
        )
        for statement in statements
    )


def _c10_block_must_raise(statements: Sequence[ast.stmt]) -> bool:
    for statement in statements:
        if isinstance(statement, ast.Raise):
            return True
        if isinstance(statement, ast.If):
            if (
                statement.orelse
                and _c10_block_must_raise(statement.body)
                and _c10_block_must_raise(statement.orelse)
            ):
                return True
        if isinstance(statement, (ast.Return, ast.Break, ast.Continue)):
            return False
    return False


def _c10_contextlib_suppress_aliases(
    tree: ast.Module,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[frozenset[str], frozenset[str]]:
    """Return unambiguous module and callable aliases for contextlib.suppress."""

    def import_kind(node: ast.AST, name: str) -> str | None:
        if isinstance(node, ast.Import):
            if any(
                alias.name == "contextlib"
                and (alias.asname or alias.name) == name
                for alias in node.names
            ):
                return "module"
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module == "contextlib"
            and any(
                alias.name == "suppress"
                and (alias.asname or alias.name) == name
                for alias in node.names
            )
        ):
            return "callable"
        return None

    def exact_aliases(
        rows_by_name: Mapping[str, Sequence[ast.AST]],
    ) -> tuple[set[str], set[str]]:
        modules: set[str] = set()
        callables: set[str] = set()
        for name, rows in rows_by_name.items():
            kinds = {import_kind(row, name) for row in rows}
            if kinds == {"module"}:
                modules.add(name)
            elif kinds == {"callable"}:
                callables.add(name)
        return modules, callables

    module_rows: dict[str, list[ast.AST]] = {}
    for statement in tree.body:
        for name in _statement_bound_names(statement):
            module_rows.setdefault(name, []).append(statement)
    module_aliases, callable_aliases = exact_aliases(module_rows)

    live_ids = {id(node) for node in _live_nodes(function)}
    local_rows: dict[str, list[ast.AST]] = {
        name: [] for name in _function_parameters(function)
    }
    for node in _scope_nodes(function)[1:]:
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            continue
        for name in _direct_bound_names(node):
            local_rows.setdefault(name, []).append(node)
    module_aliases.difference_update(local_rows)
    callable_aliases.difference_update(local_rows)
    live_local_rows = {
        name: rows
        for name, rows in local_rows.items()
        if rows and all(id(row) in live_ids for row in rows)
    }
    local_modules, local_callables = exact_aliases(live_local_rows)
    module_aliases.update(local_modules)
    callable_aliases.update(local_callables)
    return frozenset(module_aliases), frozenset(callable_aliases)


def _c10_is_suppress_context(
    expression: ast.AST,
    *,
    module_aliases: frozenset[str],
    callable_aliases: frozenset[str],
) -> bool:
    if not isinstance(expression, ast.Call):
        return False
    target = expression.func
    if isinstance(target, ast.Name):
        return target.id in callable_aliases
    return (
        isinstance(target, ast.Attribute)
        and target.attr == "suppress"
        and isinstance(target.value, ast.Name)
        and target.value.id in module_aliases
    )


def _c10_call_is_not_catch_and_continue(
    tree: ast.Module,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
) -> bool:
    parents = _c07_parent_map(function)
    module_aliases, callable_aliases = _c10_contextlib_suppress_aliases(
        tree, function
    )
    current: ast.AST = call
    while id(current) in parents:
        parent = parents[id(current)]
        if isinstance(parent, ast.Try) and any(
            call is candidate
            for statement in parent.body
            for candidate in ast.walk(statement)
        ):
            if any(
                not _c10_block_must_raise(handler.body)
                for handler in parent.handlers
            ):
                return False
        if isinstance(parent, (ast.With, ast.AsyncWith)) and any(
            call is candidate
            for statement in parent.body
            for candidate in ast.walk(statement)
        ):
            if any(
                _c10_is_suppress_context(
                    item.context_expr,
                    module_aliases=module_aliases,
                    callable_aliases=callable_aliases,
                )
                for item in parent.items
            ):
                return False
        current = parent
    return True


def _evaluate_c10(probe: _ConditionProbe) -> core.PredicateResult:
    verifier = probe.python_kind("cross_binding_verifier")
    if verifier is None:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE,
        )
    verifier_path = probe.requirement("cross_binding_verifier").path
    verify = _c10_single_function(verifier, "verify_s8c_cross_binding")
    if verify is None:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE,
        )
    if not _c10_field_paths_verdict(probe):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE,
        )
    reader = _c10_single_function(verifier, "read_and_verify_bytes")
    live_strings = {
        node.value
        for node in _live_nodes(verify)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    reader_calls = _calls_named(verify, "read_and_verify_bytes")
    verifier_graph = _ReachabilityExplorer(probe).walk(
        (verifier_path, "verify_s8c_cross_binding")
    )
    if (
        reader is None
        or not _c10_reader_is_not_noop(reader)
        or not _C10_FIELDS <= live_strings
        or not reader_calls
        or verifier_graph is None
        or not _declared_call(
            probe,
            verifier_graph,
            (verifier_path, "read_and_verify_bytes"),
        )
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE,
        )
    registry = probe.python_kind("trial_registry")
    registry_path = probe.requirement("trial_registry").path
    accept = (
        _functions(registry).get("assert_trial_registry_acceptance")
        if registry is not None
        else None
    )
    acceptance_calls = (
        () if accept is None else _calls_named(accept, "verify_s8c_cross_binding")
    )
    acceptance_graph = (
        None
        if accept is None
        else _ReachabilityExplorer(probe).walk(
            (registry_path, "assert_trial_registry_acceptance")
        )
    )
    if (
        accept is None
        or not acceptance_calls
        or acceptance_graph is None
        or not _declared_call(
            probe,
            acceptance_graph,
            (verifier_path, "verify_s8c_cross_binding"),
        )
        or not all(
            _c10_call_is_not_catch_and_continue(registry, accept, call)
            for call in acceptance_calls
        )
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.CROSS_BINDING_ACCEPTANCE_UNREACHABLE,
        )
    return _result(
        probe,
        core.PredicateStatus.SATISFIED,
        ReasonCode.CROSS_BINDING_READINESS_SATISFIED,
    )


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
    projection = probe.python_kind("generation_projection")
    if projection is None:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRITIC_FEEDBACK_CONSUMER_ABSENT)
    projection_functions = _functions(projection)
    projection_assignments = {
        target.id
        for node in projection.body
        for target in (
            node.targets
            if isinstance(node, ast.Assign)
            else (node.target,) if isinstance(node, ast.AnnAssign) else ()
        )
        if isinstance(target, ast.Name)
    }
    if (
        not {"_CRITIC_KEYS", "_DIAGNOSTIC_METRICS"} <= projection_assignments
        or not {
            "apply_critic_feedback",
            "_validate_critic_projection",
            "validate_planner_payload",
        } <= projection_functions.keys()
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRITIC_FEEDBACK_CONSUMER_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _c12_allocation_binding_verdict(
    probe: _ConditionProbe,
    workload_path: str,
    workload_supervisor: ast.Module,
    allocation_consumer: ast.Module | None,
) -> tuple[core.PredicateStatus, ReasonCode] | None:
    required_functions = {"read_binding", "check_reservation"}
    if (
        allocation_consumer is None
        or not required_functions <= _functions(allocation_consumer).keys()
        or "run_trial" not in _functions(workload_supervisor)
    ):
        return (
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT,
        )

    graph = _ReachabilityExplorer(probe).walk((workload_path, "run_trial"))
    allocation_path = probe.requirement("allocation_consumer").path
    if not all(
        _declared_call(probe, graph, (allocation_path, name))
        for name in required_functions
    ):
        return (
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT,
        )
    return None


def _evaluate_c12(probe: _ConditionProbe) -> core.PredicateResult:
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    workload_path = probe.requirement("workload_supervisor").path
    allocation = probe.python_kind("allocation_consumer")
    allocation_verdict = _c12_allocation_binding_verdict(
        probe,
        workload_path,
        tree,
        allocation,
    )
    if allocation_verdict is not None:
        status, reason = allocation_verdict
        return _result(probe, status, reason)
    functions = _functions(tree)
    if functions.get("run_trial") is None or functions.get("main") is None:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    graph = _ReachabilityExplorer(probe).walk((workload_path, "main"))
    if (workload_path, "run_trial") not in graph.functions:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    environment = probe.python_kind("environment_contract")
    guard = probe.python_kind("execution_guard")
    environment_target = (probe.requirement("environment_contract").path, "lookup")
    guard_target = (
        probe.requirement("execution_guard").path,
        "attest_and_build_receipt",
    )
    if (
        environment is None
        or guard is None
        or "lookup" not in _functions(environment)
        or "attest_and_build_receipt" not in _functions(guard)
        or not all(
            _declared_call(probe, graph, target)
            for target in (environment_target, guard_target)
        )
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


def _c07_string_sequence(value: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(value, (ast.Tuple, ast.List, ast.Set)):
        return None
    result: list[str] = []
    for item in value.elts:
        if not isinstance(item, ast.Constant) or type(item.value) is not str:
            return None
        result.append(item.value)
    return tuple(result)


def _c07_assignment_names(node: ast.stmt) -> set[str]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = (node.target,)
    else:
        return set()
    return {
        target.id
        for target in targets
        if isinstance(target, ast.Name)
    }


def _c07_name_loads(node: ast.AST) -> set[str]:
    return {
        current.id
        for current in ast.walk(node)
        if isinstance(current, ast.Name) and isinstance(current.ctx, ast.Load)
    }


def _c07_contains_dict_key(node: ast.AST, key: str) -> bool:
    return any(
        isinstance(current, ast.Dict)
        and any(
            isinstance(item, ast.Constant) and item.value == key
            for item in current.keys
        )
        for current in ast.walk(node)
    )


def _c07_returns_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(current, ast.Return) and current.value is not None
        for current in _live_nodes(node)
    )


def _c07_call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _c07_call_value_is_consumed(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
) -> bool:
    """Return whether a call result reaches a non-dead consumer in ``function``."""
    return _c07_call_has_reachable_use(function, call)


def _c07_parent_map(function: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(function):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def _c07_assignment_targets(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = (node.target,)
    else:
        return ()
    return tuple(
        name
        for target in targets
        for name in sorted(_bound_names_in_target(target))
    )


def _c07_is_assignment_value(parent: ast.AST, child: ast.AST) -> bool:
    if isinstance(parent, (ast.Assign, ast.AnnAssign)):
        value = parent.value
        return value is not None and any(current is child for current in ast.walk(value))
    return False


def _c07_is_call_argument(parent: ast.Call, child: ast.AST) -> bool:
    return any(current is child for current in (*parent.args, *(item.value for item in parent.keywords)))


def _c07_assignment_defines(node: ast.AST, name: str) -> bool:
    return name in _c07_assignment_targets(node)


def _c07_is_latest_definition(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    assignment: ast.AST,
    load: ast.Name,
) -> bool:
    load_position = (
        getattr(load, "lineno", -1),
        getattr(load, "col_offset", -1),
    )
    definitions = [
        current
        for current in _live_nodes(function)
        if isinstance(current, (ast.Assign, ast.AnnAssign))
        and _c07_assignment_defines(current, name)
        and (
            getattr(current, "lineno", -1),
            getattr(current, "col_offset", -1),
        ) < load_position
    ]
    if not definitions:
        return False
    latest = max(
        definitions,
        key=lambda current: (
            getattr(current, "lineno", -1),
            getattr(current, "col_offset", -1),
        ),
    )
    return latest is assignment


def _c07_load_reaches_sink(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    load: ast.Name,
    parents: Mapping[int, ast.AST],
    seen: set[tuple[str, int]],
    *,
    allow_return: bool = True,
) -> bool:
    current: ast.AST = load
    while id(current) in parents:
        parent = parents[id(current)]
        if isinstance(parent, (ast.Assign, ast.AnnAssign)) and _c07_is_assignment_value(parent, current):
            return any(
                _c07_name_reaches_sink(
                    function,
                    name,
                    parent,
                    parents,
                    seen,
                    allow_return=allow_return,
                )
                for name in _c07_assignment_targets(parent)
            )
        if isinstance(parent, ast.NamedExpr) and parent.value is current:
            if isinstance(parent.target, ast.Name):
                return _c07_name_reaches_sink(
                    function,
                    parent.target.id,
                    parent,
                    parents,
                    seen,
                    allow_return=allow_return,
                )
        if isinstance(parent, ast.Call):
            if _c07_is_call_argument(parent, current):
                return True
            if parent.func is current:
                return True
        if isinstance(parent, ast.Return):
            return allow_return
        if isinstance(parent, (ast.If, ast.While, ast.Assert, ast.Raise, ast.For, ast.AsyncFor)):
            return True
        if isinstance(parent, ast.Expr):
            return False
        current = parent
    return False


def _c07_name_reaches_sink(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    assignment: ast.AST,
    parents: Mapping[int, ast.AST],
    seen: set[tuple[str, int]],
    *,
    allow_return: bool = True,
) -> bool:
    marker = (name, id(assignment))
    if marker in seen:
        return False
    seen.add(marker)
    assignment_line = getattr(assignment, "lineno", -1)
    for current in _live_nodes(function):
        if not isinstance(current, ast.Name) or current.id != name:
            continue
        if not isinstance(current.ctx, ast.Load) or getattr(current, "lineno", -1) <= assignment_line:
            continue
        if not _c07_is_latest_definition(function, name, assignment, current):
            continue
        if _c07_load_reaches_sink(
            function,
            current,
            parents,
            seen,
            allow_return=allow_return,
        ):
            return True
    return False


def _c07_expression_reaches_check(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    expression: ast.AST,
    parents: Mapping[int, ast.AST],
    seen: set[tuple[str, int]],
    *,
    allow_return: bool = True,
) -> bool:
    """Trace a value to a comparison, condition, return, or call argument."""
    current = expression
    while id(current) in parents:
        parent = parents[id(current)]
        if isinstance(parent, (ast.Assign, ast.AnnAssign)) and _c07_is_assignment_value(parent, current):
            return any(
                _c07_name_reaches_sink(
                    function,
                    name,
                    parent,
                    parents,
                    seen,
                    allow_return=allow_return,
                )
                for name in _c07_assignment_targets(parent)
            )
        if isinstance(parent, ast.NamedExpr) and parent.value is current:
            if isinstance(parent.target, ast.Name):
                return _c07_name_reaches_sink(
                    function,
                    parent.target.id,
                    parent,
                    parents,
                    seen,
                    allow_return=allow_return,
                )
        if isinstance(parent, ast.Call):
            if _c07_is_call_argument(parent, current):
                return True
            if parent.func is current:
                return True
        if isinstance(parent, ast.Compare):
            return True
        if isinstance(parent, ast.Return):
            return allow_return
        if isinstance(parent, (ast.If, ast.While, ast.Assert, ast.Raise, ast.For, ast.AsyncFor)):
            return True
        if isinstance(parent, ast.Expr):
            return False
        current = parent
    return False


def _c07_call_has_reachable_use(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
) -> bool:
    parents = _c07_parent_map(function)
    return _c07_expression_reaches_check(function, call, parents, set())


def _c07_live_calls(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ast.Call, ...]:
    live = {id(node) for node in _live_nodes(function)}
    return tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and id(node) in live
    )


def _c07_reachable_functions(
    tree: ast.Module,
    start: str,
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    functions = _functions(tree)
    reached: set[str] = set()
    pending = [start]
    while pending:
        name = pending.pop()
        if name in reached or name not in functions:
            continue
        reached.add(name)
        pending.extend(_live_called_names(functions[name]) & functions.keys())
    return {
        name: functions[name]
        for name in reached
        if name in functions
    }


_C07_FLOOR_FIELDS = frozenset(
    {"path", "sha256", "env_tag", "measurement_head"}
)
_C07_FLOOR_ARTIFACTS = frozenset({"floor_protocol", "floor_source"})
_C07_FLOOR_FIELD_ALIASES = {"frozen_at_head": "measurement_head"}


def _c07_string_call_key(node: ast.Call) -> str | None:
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    if type(node.args[0].value) is not str:
        return None
    if isinstance(node.func, ast.Attribute) and node.func.attr in {"get", "pop"}:
        return node.args[0].value
    if isinstance(node.func, ast.Name) and node.func.id in {"_first", "get_field"}:
        return node.args[0].value
    return None


def _c07_field_key(node: ast.AST) -> str | None:
    if isinstance(node, ast.Subscript):
        slice_node = node.slice
        if isinstance(slice_node, ast.Constant) and type(slice_node.value) is str:
            return slice_node.value
    if isinstance(node, ast.Call):
        return _c07_string_call_key(node)
    return None


def _c07_live_constant_uses(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    values: frozenset[str],
) -> set[str]:
    parents = _c07_parent_map(function)
    used: set[str] = set()
    for node in _live_nodes(function):
        if not isinstance(node, ast.Constant) or type(node.value) is not str:
            continue
        if node.value not in values:
            continue
        if _c07_expression_reaches_check(
            function, node, parents, set(), allow_return=False
        ):
            used.add(node.value)
    return used


def _c07_floor_field_uses(
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> set[str]:
    used: set[str] = set()
    for function in functions.values():
        parents = _c07_parent_map(function)
        for node in _live_nodes(function):
            field = _c07_field_key(node)
            field = _C07_FLOOR_FIELD_ALIASES.get(field, field)
            if field in _C07_FLOOR_FIELDS and _c07_expression_reaches_check(
                function, node, parents, set(), allow_return=False
            ):
                used.add(field)
    return used


def _c07_receipt_parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    arguments = (
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    )
    if function.args.vararg is not None:
        arguments += (function.args.vararg,)
    if function.args.kwarg is not None:
        arguments += (function.args.kwarg,)
    return {
        argument.arg
        for argument in arguments
        if any(token in argument.arg.lower() for token in ("receipt", "evidence", "floor"))
    }


def _evaluate_c07(probe: _ConditionProbe) -> core.PredicateResult:
    """静的な C07 構造検査を行う。

    動的 dispatch、実行時の例外経路、実 bytes と結果値の対応は静的に完全証明できないため、
    構造と到達使用を検査しても証拠 undefined に留める。
    """
    requirement = probe.contract.consumer_requirement
    expected_entrypoints = (
        "verify_floor_bytes",
        "judge",
        "publish_result_table",
    )
    entrypoints = tuple(requirement.entrypoints)
    result_requirement = probe.requirement("result_judge")
    declared_chain = " -> ".join(expected_entrypoints)
    if (
        entrypoints != expected_entrypoints
        or not any(
            declared_chain in reachable
            for reachable in result_requirement.reachable_from
        )
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )
    result_path = result_requirement.path
    if result_path != requirement.path:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )
    tree = probe.python_path(result_path)
    if tree is None:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )
    functions = _functions(tree)
    public_functions = {name for name in functions if not name.startswith("_")}
    if public_functions != set(entrypoints) or any(
        name not in functions for name in entrypoints
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )
    declared_names = []
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in statement.targets
        ):
            continue
        sequence = _c07_string_sequence(statement.value)
        if sequence is not None:
            declared_names.extend(sequence)
    if tuple(declared_names) != expected_entrypoints:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )

    verify = functions.get("verify_floor_bytes")
    judge = functions.get("judge")
    publish = functions.get("publish_result_table")
    if verify is None or judge is None or publish is None:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )
    if not all(_c07_returns_value(function) for function in (verify, judge, publish)):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )
    verify_reachable = _c07_reachable_functions(tree, "verify_floor_bytes")
    floor_fields = _c07_floor_field_uses(verify_reachable)
    floor_artifacts = set().union(
        *(
            _c07_live_constant_uses(function, _C07_FLOOR_ARTIFACTS)
            for function in verify_reachable.values()
        )
    )
    if floor_fields != set(_C07_FLOOR_FIELDS) or floor_artifacts != set(_C07_FLOOR_ARTIFACTS):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )

    expected_condition_ids = {
        "on_off_prediction_difference",
        "swapped_follow_through",
        "paired_repeat_contrast",
    }
    judge_loads = _c07_name_loads(judge)
    condition_candidates: list[tuple[str, tuple[str, ...]]] = []
    for statement in tree.body:
        names = _c07_assignment_names(statement)
        if not any("condition" in name.lower() for name in names):
            continue
        value = (
            statement.value
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            else None
        )
        if value is None:
            continue
        sequence = _c07_string_sequence(value)
        if sequence is not None and names & judge_loads:
            condition_candidates.extend(
                (name, sequence)
                for name in names & judge_loads
            )
    conditions_assignment = any(
        isinstance(current, (ast.Assign, ast.AnnAssign))
        and "conditions" in _c07_assignment_names(current)
        and _c07_contains_dict_key(current, "condition")
        and _c07_name_reaches_sink(
            judge,
            "conditions",
            current,
            _c07_parent_map(judge),
            set(),
        )
        for current in _live_nodes(judge)
    ) or any(
        isinstance(current, (ast.Assign, ast.AnnAssign))
        and "conditions" in _c07_assignment_names(current)
        and any(isinstance(child, ast.Dict) for child in ast.walk(current.value))
        and _c07_name_reaches_sink(
            judge,
            "conditions",
            current,
            _c07_parent_map(judge),
            set(),
        )
        for current in _live_nodes(judge)
        if isinstance(current, (ast.Assign, ast.AnnAssign))
        and getattr(current, "value", None) is not None
    )
    if (
        len(condition_candidates) != 1
        or len(condition_candidates[0][1]) != 3
        or len(set(condition_candidates[0][1])) != 3
        or set(condition_candidates[0][1]) != expected_condition_ids
        or not conditions_assignment
        or condition_candidates[0][0] not in judge_loads
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )

    publish_reachable = _c07_reachable_functions(tree, "publish_result_table")
    publish_nodes = tuple(
        node
        for function in publish_reachable.values()
        for node in _live_nodes(function)
    )
    table_markers = {"descriptive_only", "official_status", "selection_evaluation"}
    table_candidates: list[tuple[str, tuple[str, ...]]] = []
    publish_loads = _c07_name_loads(publish)
    for statement in tree.body:
        names = _c07_assignment_names(statement)
        if not any("table" in name.lower() for name in names):
            continue
        value = (
            statement.value
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            else None
        )
        if value is None:
            continue
        sequence = _c07_string_sequence(value)
        if sequence is not None and names & publish_loads:
            table_candidates.extend(
                (name, sequence)
                for name in names & publish_loads
            )
    has_cells_structure = any(
        isinstance(node, ast.Dict)
        and any(
            isinstance(key, ast.Constant) and key.value == "cells"
            for key in node.keys
        )
        for node in publish_nodes
    )
    cell_validator_names = {
        name
        for name, function in functions.items()
        if "cell" in name.lower()
        and any(token in name.lower() for token in ("validat", "exact", "check"))
        and _c07_returns_value(function)
    }
    cell_calls = tuple(
        (function, call)
        for function in publish_reachable.values()
        for call in _c07_live_calls(function)
        if _c07_call_name(call) in cell_validator_names
    )
    if (
        len(table_candidates) != 1
        or len(table_candidates[0][1]) != 3
        or len(set(table_candidates[0][1])) != 3
        or set(table_candidates[0][1]) != table_markers
        or not has_cells_structure
        or not cell_calls
        or any(
            not _c07_call_value_is_consumed(function, call)
            for function, call in cell_calls
        )
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )

    receipt_parameters = _c07_receipt_parameters(publish)
    publish_loads = _c07_name_loads(publish)
    if not receipt_parameters or not receipt_parameters & publish_loads:
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )

    validation_names = {
        name
        for name, function in functions.items()
        if name not in cell_validator_names
        and (
            "validat" in name.lower()
            or name.lower().startswith(("verify", "check"))
        )
        and _c07_returns_value(function)
    }
    validation_calls = tuple(
        (function, call)
        for entrypoint in entrypoints
        for function in _c07_reachable_functions(tree, entrypoint).values()
        for call in _c07_live_calls(function)
        if _c07_call_name(call) in validation_names
    )
    if (
        not validation_calls
        or any(
            not _c07_call_value_is_consumed(function, call)
            for function, call in validation_calls
        )
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RESULT_JUDGE_CONSUMER_INCOMPLETE,
        )

    ratified_path = probe.requirement("ratified_generation_reference").path
    ratified = probe.python_path(ratified_path)
    if ratified is None or "load_ratified_freeze" not in _functions(ratified):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RATIFIED_GENERATION_REFERENCE_ABSENT,
        )
    loader_calls = tuple(
        (function, call)
        for function in verify_reachable.values()
        for call in _c07_live_calls(function)
        if _c07_call_name(call) == "load_ratified_freeze"
    )
    if not loader_calls or any(
        not _c07_call_has_reachable_use(function, call)
        for function, call in loader_calls
    ):
        return _result(
            probe,
            core.PredicateStatus.UNSATISFIED,
            ReasonCode.RATIFIED_GENERATION_REFERENCE_ABSENT,
        )
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


SATISFIABLE_CONDITION_IDS: frozenset[str] = frozenset({"C10"})


def _evaluate_undefined(probe: _ConditionProbe) -> core.PredicateResult:
    number = probe.contract.condition_number
    if number == 3:
        return _evaluate_c03(probe)
    if number == 8:
        return _evaluate_c08(probe)
    if number in _MACHINE_EVALUATORS:
        for item in probe.contract.required_evidence:
            probe.read_kind(item.artifact_kind)
        reason = ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE
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
            resolved = core.resolve_commit(root, commit)
            contract_raw = _read_blob_at_resolved(
                root, resolved, core.EVIDENCE_CONTRACT_PATH
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
        raw_cache: dict[str, bytes | None] = {
            core.EVIDENCE_CONTRACT_PATH: contract_raw
        }
        python_cache: dict[str, ast.Module | None] = {}
        function_cache: dict[
            str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]
        ] = {}
        binding_cache: dict[
            str, tuple[dict[str, _Binding], tuple[str, ...]]
        ] = {}
        graph_cache: dict[
            tuple[_CallableTarget, _ReachabilityLimits], _Reachability
        ] = {}
        results: list[core.PredicateResult] = []
        for condition in contract.conditions:
            probe = _ConditionProbe(
                root,
                resolved,
                condition,
                contract_ref,
                {},
                raw_cache,
                python_cache,
                declared_paths=contract.evidence_paths,
                function_cache=function_cache,
                binding_cache=binding_cache,
                graph_cache=graph_cache,
            )
            try:
                if condition.machine_checkable:
                    evaluator = _MACHINE_EVALUATORS.get(condition.condition_number)
                    if evaluator is None:
                        if condition.condition_number in {3, 8}:
                            # Historical contracts may have marked these static
                            # predicates as machine-checkable.  They must fail
                            # closed explicitly while the current contract stays
                            # non-machine and the evaluator map stays unchanged.
                            result = _result(
                                probe,
                                core.PredicateStatus.ERROR,
                                ReasonCode.BLOB_READ_ERROR,
                            )
                        else:
                            raise EvidenceContractError(
                                "contract-machine-evaluator", condition.identifier
                            )
                    else:
                        result = evaluator(probe)
                else:
                    result = _evaluate_undefined(probe)
                if (
                    is_satisfied(result.status)
                    and condition.identifier not in SATISFIABLE_CONDITION_IDS
                ):
                    result = _result(
                        probe,
                        core.PredicateStatus.ERROR,
                        ReasonCode.EVALUATOR_INTERNAL_ERROR,
                    )
            except (core.PreregistrationError, EvidenceContractError) as exc:
                error_reason = getattr(exc, "reason_code", "")
                if error_reason == "evidence-python-parse-error":
                    reason = ReasonCode.PYTHON_PARSE_ERROR
                elif error_reason == ReasonCode.REACHABILITY_LIMIT_EXCEEDED.value:
                    reason = ReasonCode.REACHABILITY_LIMIT_EXCEEDED
                else:
                    reason = ReasonCode.BLOB_READ_ERROR
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


# C06 の静的 evaluator は、契約の machine_checkable 宣言に対応して production registry へ登録する。
from types import MappingProxyType as _MappingProxyType  # noqa: E402

_C06_EXPECTED_FIELD_PATHS = frozenset(
    {
        "ledger.manifest_sha256",
        "ledger.freeze_sha256",
        "ledger.schedule_sha256",
        "ledger.ratified_generation_sha256",
        "reservation.cells[*].reserved_bench_s",
        "settlement.cells[*].actual_bench_s",
    }
)
_C06_EXPECTED_CELL_ROWS = frozenset(
    {
        ("H1", "on"),
        ("H1", "off"),
        ("H1", "swapped"),
        ("H2", "on"),
        ("H2", "off"),
        ("H2", "swapped"),
    }
)
_C06_EXPECTED_REACHABLE_FROM = (
    (
        "budget_consumer",
        "run_trial -> reserve_all_cells -> bench launch",
    ),
    (
        "budget_consumer",
        "bench terminal -> settle -> symmetric_indeterminate",
    ),
    (
        "ratified_generation_reference",
        "run_trial -> load_ratified_freeze -> reserve_all_cells",
    ),
)


def _c06_reachable_from_verdict(probe: _ConditionProbe) -> bool:
    # 契約記述と evaluator 期待値の整合 (drift) だけを確認し、
    # 実コード上の呼び出し順序やデータフローは検証しない。
    return all(
        chain in probe.requirement(kind).reachable_from
        for kind, chain in _C06_EXPECTED_REACHABLE_FROM
    )


def _c06_annotation_names(node: ast.AST) -> frozenset[str]:
    return frozenset(
        current.id
        for current in ast.walk(node)
        if isinstance(current, ast.Name)
    ) | frozenset(
        current.attr
        for current in ast.walk(node)
        if isinstance(current, ast.Attribute)
    )


def _c06_dataclass_fields(
    tree: ast.Module,
    name: str,
) -> tuple[dict[str, ast.AST], bool]:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    ]
    if len(matches) != 1:
        return {}, False
    node = matches[0]
    dataclass_decorator = False
    frozen = False
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if (
            isinstance(target, ast.Name) and target.id == "dataclass"
        ) or (
            isinstance(target, ast.Attribute) and target.attr == "dataclass"
        ):
            dataclass_decorator = True
            if isinstance(decorator, ast.Call):
                frozen = any(
                    keyword.arg == "frozen"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in decorator.keywords
                )
    fields = {
        statement.target.id: statement.annotation
        for statement in node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    }
    return fields, dataclass_decorator and frozen


def _c06_expected_rows(tree: ast.Module) -> frozenset[tuple[str, str]]:
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else (statement.target,)
        )
        if not any(
            isinstance(target, ast.Name) and target.id == "_EXPECTED_CELL_ROWS"
            for target in targets
        ):
            continue
        value = statement.value
        if not isinstance(value, ast.Tuple):
            return frozenset()
        rows: set[tuple[str, str]] = set()
        for row in value.elts:
            if not isinstance(row, ast.Tuple) or len(row.elts) != 2:
                return frozenset()
            if not all(
                isinstance(item, ast.Constant) and type(item.value) is str
                for item in row.elts
            ):
                return frozenset()
            rows.add((row.elts[0].value, row.elts[1].value))
        return frozenset(rows)
    return frozenset()


def _c06_has_attribute_chain(tree: ast.Module, chain: tuple[str, ...]) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        parts: list[str] = [node.attr]
        current = node.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        if tuple(reversed(parts)) == chain:
            return True
    return False


def _c06_field_path_verdict(tree: ast.Module) -> bool:
    """C06 の field path を実 dataclass と instance access から検査する。"""
    fields: dict[str, dict[str, ast.AST]] = {}
    for name in (
        "BudgetLimits",
        "ReservationCell",
        "Reservation",
        "SettlementCell",
        "Settlement",
        "Ledger",
    ):
        current, valid = _c06_dataclass_fields(tree, name)
        if not valid:
            return False
        fields[name] = current
    required_fields = {
        "BudgetLimits": {"total_bench_s", "per_arm_bench_s", "per_holdout_bench_s"},
        "ReservationCell": {"cell_id", "holdout", "arm", "reserved_bench_s"},
        "Reservation": {"cells", "budget_bench_s", "total_reserved_bench_s", "state"},
        "SettlementCell": {"cell_id", "actual_bench_s"},
        "Settlement": {"cells", "total_actual_bench_s"},
        "Ledger": {
            "manifest_sha256",
            "freeze_sha256",
            "schedule_sha256",
            "ratified_generation_sha256",
            "reservation",
            "settlement",
            "cell_ids",
        },
    }
    if any(
        not required_fields[name] <= set(class_fields)
        for name, class_fields in fields.items()
    ):
        return False
    if not {"tuple", "frozenset"} <= {
        current.func.id
        for current in ast.walk(tree)
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Name)
    }:
        return False
    constructor_names = {
        current.func.id
        for current in ast.walk(tree)
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Name)
    }
    if not {
        "BudgetLimits",
        "ReservationCell",
        "Reservation",
        "SettlementCell",
        "Settlement",
        "Ledger",
    } <= constructor_names:
        return False
    annotation_names = {
        name: _c06_annotation_names(annotation)
        for class_name, class_fields in fields.items()
        for name, annotation in class_fields.items()
    }
    if "tuple" not in annotation_names["cells"]:
        return False
    if "frozenset" not in annotation_names["cell_ids"]:
        return False
    if _c06_expected_rows(tree) != _C06_EXPECTED_CELL_ROWS:
        return False
    required_strings = {
        "total_bench_s",
        "per_arm_bench_s",
        "per_holdout_bench_s",
        "total_reserved_bench_s",
        "reserved_bench_s",
        "actual_bench_s",
        "insufficient",
    }
    strings = _strings(tree)
    if not required_strings <= strings:
        return False
    comparisons = {
        type(current.ops[0])
        for current in ast.walk(tree)
        if isinstance(current, ast.Compare) and current.ops
    }
    if ast.LtE not in comparisons:
        return False
    if not any(
        isinstance(current, ast.Attribute) and current.attr == "O_EXCL"
        for current in ast.walk(tree)
    ):
        return False
    for chain in (
        ("ledger", "manifest_sha256"),
        ("ledger", "freeze_sha256"),
        ("ledger", "schedule_sha256"),
        ("ledger", "ratified_generation_sha256"),
        ("ledger", "reservation", "cells"),
        ("ledger", "settlement", "cells"),
    ):
        if not _c06_has_attribute_chain(tree, chain):
            return False
    if any(
        isinstance(current, ast.Call)
        and isinstance(current.func, ast.Name)
        and current.func.id == "setattr"
        for current in ast.walk(tree)
    ):
        return False
    return True


def _c06_unsatisfied(probe: _ConditionProbe) -> core.PredicateResult:
    return _result(
        probe,
        core.PredicateStatus.UNSATISFIED,
        ReasonCode.BUDGET_CONSUMER_UNDEFINED,
    )


def _evaluate_c06(probe: _ConditionProbe) -> core.PredicateResult:
    """C06 の machine evaluator。充足を返さず、完了証明は常に未定義にする。"""
    budget = probe.python_kind("budget_consumer")
    if budget is None:
        return _result(
            probe,
            core.PredicateStatus.EVIDENCE_UNDEFINED,
            ReasonCode.BUDGET_CONSUMER_UNDEFINED,
        )
    requirement = probe.requirement("budget_consumer")
    if frozenset(requirement.field_paths) != _C06_EXPECTED_FIELD_PATHS:
        return _c06_unsatisfied(probe)
    if not _c06_reachable_from_verdict(probe):
        return _c06_unsatisfied(probe)
    if not _c06_field_path_verdict(budget):
        return _c06_unsatisfied(probe)
    functions = _functions(budget)
    if not {
        "reserve_all_cells",
        "settle",
        "symmetric_indeterminate",
    } <= functions.keys():
        return _c06_unsatisfied(probe)
    if not {
        "_ledger_lock",
        "_check_limit_state",
    } <= functions.keys():
        return _c06_unsatisfied(probe)
    required_calls = {
        "reserve_all_cells": {
            "_ledger_lock",
            "_check_limit_state",
        },
        "settle": {"_ledger_lock"},
    }
    for name, expected in required_calls.items():
        if not expected <= _live_called_names(functions[name]):
            return _c06_unsatisfied(probe)
    reference_requirement = probe.requirement(
        "ratified_generation_reference"
    )
    reference = probe.python_kind("ratified_generation_reference")
    if (
        reference is None
        or "load_ratified_freeze" not in _functions(reference)
        or "sha256" not in _strings(reference)
    ):
        return _c06_unsatisfied(probe)
    supervisor_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    supervisor = probe.python_path(supervisor_path)
    if supervisor is None or "run_trial" not in _functions(supervisor):
        return _c06_unsatisfied(probe)

    graph = _ReachabilityExplorer(probe).walk(
        (supervisor_path, "run_trial")
    )
    required_targets = {
        (reference_requirement.path, "load_ratified_freeze"),
        (requirement.path, "reserve_all_cells"),
        (requirement.path, "settle"),
        (requirement.path, "symmetric_indeterminate"),
    }
    if not all(
        _declared_call(probe, graph, target)
        for target in required_targets
    ):
        return _c06_unsatisfied(probe)
    if not any(
        isinstance(current, ast.Attribute) and current.attr == "sha256"
        for current in ast.walk(supervisor)
    ):
        return _c06_unsatisfied(probe)
    # static_only_note の通り、実時間の値は readiness の充足条件にしない。
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )


_MACHINE_EVALUATORS = {
    1: _evaluate_c01,
    2: _evaluate_c02,
    4: _evaluate_c04,
    5: _evaluate_c05,
    6: _evaluate_c06,
    7: _evaluate_c07,
    9: _evaluate_c09,
    10: _evaluate_c10,
    11: _evaluate_c11,
    12: _evaluate_c12,
}
MACHINE_CHECKABLE_CONDITION_IDS: frozenset[str] = frozenset(
    f"C{number:02d}" for number in _MACHINE_EVALUATORS
)
_STAGED_EVALUATORS = _MappingProxyType({})
