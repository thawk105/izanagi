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


def _live_nodes(node: ast.AST) -> list[ast.AST]:
    """Function body nodes excluding nested scopes and constant-false branches."""
    values: list[ast.AST] = []

    def visit(current: ast.AST, *, root: bool = False) -> None:
        if root and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            values.append(current)
            for child in current.body:
                visit(child)
            return
        if not root and isinstance(
            current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        values.append(current)
        if isinstance(current, ast.If):
            false_branch = (
                isinstance(current.test, ast.Constant)
                and (current.test.value is False or current.test.value == 0)
            )
            branches = current.orelse if false_branch else (*current.body, *current.orelse)
            visit(current.test)
            for child in branches:
                visit(child)
            return
        for child in ast.iter_child_nodes(current):
            visit(child)

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
        parameters = set(_function_parameters(node))
        callable_defaults = _callable_defaults(node)
        unsafe_bindings: set[str] = set()
        for current in _scope_nodes(node):
            if isinstance(current, (ast.Assign, ast.AnnAssign)):
                continue
            unsafe_bindings.update(_direct_bound_names(current))
        for name in unsafe_bindings:
            local.pop(name, None)
            availability.pop(name, None)
        shadowed = (
            parameters
            | set(assignments)
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


def _evaluate_c12(probe: _ConditionProbe) -> core.PredicateResult:
    workload_path = probe.requirement("workload_supervisor").path
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    functions = _functions(tree)
    if functions.get("run_trial") is None or functions.get("main") is None:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    graph = _ReachabilityExplorer(probe).walk((workload_path, "main"))
    if (workload_path, "run_trial") not in graph.functions:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.ENVIRONMENT_CONTRACT_CONSUMER_ABSENT)
    environment = probe.python_kind("environment_contract")
    guard = probe.python_kind("execution_guard")
    allocation = probe.python_kind("allocation_consumer")
    environment_target = (probe.requirement("environment_contract").path, "lookup")
    guard_target = (
        probe.requirement("execution_guard").path,
        "attest_and_build_receipt",
    )
    allocation_target = (
        probe.requirement("allocation_consumer").path,
        "single_process_required",
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
    if (
        allocation is None
        or "single_process_required" not in _functions(allocation)
        or not _declared_call(probe, graph, allocation_target)
        or not {"single_process", "allow_resume"} <= graph.attributes
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
MACHINE_CHECKABLE_CONDITION_IDS: frozenset[str] = frozenset(
    f"C{number:02d}" for number in _MACHINE_EVALUATORS
)
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
                        raise EvidenceContractError(
                            "contract-machine-evaluator", condition.identifier
                        )
                    result = evaluator(probe)
                else:
                    result = _evaluate_undefined(probe)
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
