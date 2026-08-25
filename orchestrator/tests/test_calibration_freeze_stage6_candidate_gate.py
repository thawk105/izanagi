# -*- coding: utf-8 -*-
"""段 6 候補提出の前提関門 adapter の終端・結線・caller inventory。"""
from __future__ import annotations

import ast
import sys
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.campaign import calibration_freeze_stage6_candidate_gate as gate
from orchestrator.tests import calibration_freeze_authority_contract as contract
from orchestrator.tests.repo_tree_util import list_tracked_and_untracked_files


_ADAPTER_PATH = "orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py"
_OBLIGATION_PREDICATE = "require_stage0_fixture_obligations_discharged"
_ADAPTER_PREDICATE = "require_stage6_candidate_submission_ready"
_TARGET_PREDICATES = frozenset({_OBLIGATION_PREDICATE, _ADAPTER_PREDICATE})
_EXPECTED_PREREQUISITE_CELLS = (
    "到達可能な段 6 production 経路が義務述語を通る",
    "`unmet`: production adapter 1 件・operational caller 0 件",
    "`orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py` の "
    "`require_stage6_candidate_submission_ready()`、"
    "`orchestrator/tests/calibration_freeze_authority_contract.py` の "
    "`require_stage0_fixture_obligations_discharged()`",
    "`checkout-pinned`; caller inventory の機械検査が adapter 1 件・"
    "operational caller 0 件を固定する",
    "adapter の呼び手と段 6 の候補提出経路が未実装。"
    "段 6 policy gate も `unresolved`",
    "`unassigned`",
)
_EXPECTED_DESIGN_10_2_FRAGMENT = (
    "段 6 の X 候補提出前には、前者ではなくこの義務解消述語の解消を要求する。\n"
    "この要求は `orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py` の\n"
    "`require_stage6_candidate_submission_ready()` が担い、同 adapter が義務解消述語を呼ぶ。\n"
    "段 6 の operational caller は義務解消述語を直接呼ばず、この adapter を呼ぶ。\n"
    "直接呼ぶと adapter の policy 終端を迂回する。\n"
    "production adapter 1 件・operational caller 0 件である。\n"
    "adapter が在ることは繰越義務の解消を意味しない。"
)
_EXPECTED_DESIGN_12_3_FRAGMENT = (
    "候補提出を実装する段 6 caller は\n"
    "`orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py` の\n"
    "`require_stage6_candidate_submission_ready()` を呼び、同 adapter が\n"
    "`require_stage0_fixture_obligations_discharged()` を通じて再び全件を要求する。\n"
    "段 6 の operational caller は義務解消述語を直接呼ばず、この adapter を呼ぶ。\n"
    "直接呼ぶと adapter の policy 終端を迂回する。\n"
    "production adapter 1 件・operational caller 0 件であり、候補入口そのものは未実装である。"
)


def _direct_import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        for imported in node.names:
            if imported.name in _TARGET_PREDICATES:
                aliases[imported.asname or imported.name] = imported.name
    return aliases


def _referenced_target(
    expression: ast.expr,
    aliases: Mapping[str, str],
) -> str | None:
    if isinstance(expression, ast.Attribute):
        return expression.attr if expression.attr in _TARGET_PREDICATES else None
    if isinstance(expression, ast.Name):
        resolved = aliases.get(expression.id, expression.id)
        return resolved if resolved in _TARGET_PREDICATES else None
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "getattr"
        and len(expression.args) >= 2
        and isinstance(expression.args[1], ast.Constant)
        and type(expression.args[1].value) is str
        and expression.args[1].value in _TARGET_PREDICATES
    ):
        return expression.args[1].value
    return None


def _target_aliases(tree: ast.AST) -> dict[str, str]:
    """直接 import と単純代入を target predicate まで固定点伝播する。"""

    aliases = _direct_import_aliases(tree)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            targets: tuple[ast.expr, ...]
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = (node.target,)
                value = node.value
            else:
                continue
            resolved = _referenced_target(value, aliases)
            if resolved is None:
                continue
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id not in aliases
                ):
                    aliases[target.id] = resolved
                    changed = True
    return aliases


def _select_inventory_paths(paths: Iterable[Path]) -> frozenset[Path]:
    """tracked + untracked 列から production Python の走査母集合を選ぶ。"""

    return frozenset(
        path
        for path in paths
        if path.suffix == ".py"
        and path.parts[:2] != ("orchestrator", "tests")
    )


def _assert_exact_inventory_roots(
    enumerated_paths: Iterable[Path],
    selected_paths: Iterable[Path],
) -> None:
    """列挙された production Python と選択集合の top-level root を exact 比較する。"""

    expected = frozenset(
        path.parts[0]
        for path in enumerated_paths
        if path.parts
        and path.suffix == ".py"
        and path.parts[:2] != ("orchestrator", "tests")
    )
    observed = frozenset(
        path.parts[0]
        for path in selected_paths
        if path.parts
    )
    if observed != expected:
        raise AssertionError(
            "caller inventory top-level roots drifted: "
            f"expected={sorted(expected)!r} observed={sorted(observed)!r}"
        )


def _assert_exact_paths(
    expected: frozenset[str],
    observed: frozenset[str],
    *,
    label: str,
) -> None:
    """caller 集合の exact 比較を repository と負の対照で共有する。"""

    if observed != expected:
        raise AssertionError(
            f"{label} caller inventory drifted: "
            f"expected={sorted(expected)!r} observed={sorted(observed)!r}"
        )


def _caller_inventory(
    sources: Mapping[str, str],
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """2 関門の caller 集合と曖昧参照 module 集合を純粋に抽出する。

    NFKC 後に両 target のどちらも含まない source は AST parse を省くため、
    target と無関係な source の構文不正はこの inventory の検査対象外である。
    target を含む source は元 source を parse し、構文不正を fail-closed にする。

    module を跨ぐ alias の再 export は 1 file の AST では解決できない。
    """

    obligation_callers: set[str] = set()
    adapter_callers: set[str] = set()
    ambiguous_callers: set[str] = set()
    for module_path, source in sources.items():
        normalized_source = unicodedata.normalize("NFKC", source)
        if not any(
            predicate in normalized_source
            for predicate in _TARGET_PREDICATES
        ):
            continue
        tree = ast.parse(source, filename=module_path)
        aliases = _target_aliases(tree)
        resolved_callees = {
            id(node.func): target
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            if (target := _referenced_target(node.func, aliases)) is not None
        }
        called_names = frozenset(resolved_callees.values())
        syntactic_references = (
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Attribute)
                and node.attr in _TARGET_PREDICATES
            )
            or (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and _referenced_target(node, aliases) is not None
            )
            or (
                isinstance(node, ast.Call)
                and _referenced_target(node, aliases) is not None
            )
        )
        if any(
            id(reference) not in resolved_callees
            for reference in syntactic_references
        ):
            ambiguous_callers.add(module_path)
        if _OBLIGATION_PREDICATE in called_names:
            obligation_callers.add(module_path)
        if _ADAPTER_PREDICATE in called_names:
            adapter_callers.add(module_path)
    return (
        frozenset(obligation_callers),
        frozenset(adapter_callers),
        frozenset(ambiguous_callers),
    )


def test_real_repository_rejects_stage6_candidate_for_undischarged_fixture_obligations(
) -> None:
    """これは終端 oracle であり、呼出しの実在は証明しない。"""

    try:
        gate.require_stage6_candidate_submission_ready()
    except gate.Stage6CandidateSubmissionBlocked as exc:
        assert type(exc) is gate.Stage6FixtureObligationGateRejected
        assert exc.reason_code == "stage0-fixture-obligation-gate-rejected"
        assert type(exc.__cause__) is contract.ContractError
        message = str(exc)
        assert "raw_pending_count=5" in message
        for fixture_id in (
            "approved-freeze-reference",
            "bundle-identity-propagation",
            "candidate-type-preservation",
            "floor-seal-consistency",
            "post-cutoff-bundle-identity",
        ):
            assert fixture_id in message
        assert "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT" in message
    else:
        raise AssertionError("undischarged fixture obligations were accepted")


def test_discharged_fixture_obligations_reach_unresolved_stage6_policy_terminal(
) -> None:
    """これは終端 oracle であり、呼出しの実在は証明しない。"""

    summary = {"raw_pending_count": 0, "deferred_gate_ids": ()}

    def discharged_summary(*_args: object, **_kwargs: object) -> dict[str, object]:
        return summary

    original = contract.validate_repository
    blocked: gate.Stage6CandidateSubmissionBlocked | None = None
    try:
        contract.validate_repository = discharged_summary
        try:
            gate.require_stage6_candidate_submission_ready()
        except gate.Stage6CandidateSubmissionBlocked as exc:
            blocked = exc
        else:
            raise AssertionError("the unresolved stage 6 policy returned normally")
    finally:
        contract.validate_repository = original

    assert blocked is not None
    assert type(blocked) is gate.Stage6PolicyUnresolvedAfterFixtureObligations
    assert blocked.reason_code == (
        "stage0-fixture-obligations-passed-stage6-policy-unresolved"
    )
    assert "CFAB-STAGE6-POLICY-PREDICATE" in str(blocked)
    assert "unresolved" in str(blocked)
    assert blocked.__cause__ is None
    assert (
        gate.Stage6PolicyUnresolvedAfterFixtureObligations
        is not gate.Stage6FixtureObligationGateRejected
    )
    assert (
        gate.Stage6PolicyUnresolvedAfterFixtureObligations.reason_code
        != gate.Stage6FixtureObligationGateRejected.reason_code
    )


def test_stage6_candidate_gate_executes_obligation_predicate_with_forwarded_paths(
) -> None:
    fixture_root = object()
    design_doc = object()
    default_fixture_root = object()
    default_design_doc = object()
    calls: list[tuple[object, object]] = []

    def obligation_spy(
        *,
        fixture_root: object = default_fixture_root,
        design_doc: object = default_design_doc,
    ) -> dict[str, object]:
        calls.append((fixture_root, design_doc))
        return {}

    original = contract.require_stage0_fixture_obligations_discharged
    blocked: gate.Stage6CandidateSubmissionBlocked | None = None
    try:
        contract.require_stage0_fixture_obligations_discharged = obligation_spy
        try:
            gate.require_stage6_candidate_submission_ready(
                fixture_root=fixture_root,
                design_doc=design_doc,
            )
        except gate.Stage6CandidateSubmissionBlocked as exc:
            blocked = exc
        else:
            raise AssertionError("the stage 6 candidate gate returned normally")
    finally:
        contract.require_stage0_fixture_obligations_discharged = original

    assert len(calls) == 1
    assert calls[0][0] is fixture_root
    assert calls[0][1] is design_doc
    assert type(blocked) is gate.Stage6PolicyUnresolvedAfterFixtureObligations


def test_stage6_candidate_gate_propagates_non_contract_exception() -> None:
    class SentinelError(RuntimeError):
        pass

    sentinel = SentinelError("throwing-spy sentinel")
    fixture_root = object()
    design_doc = object()
    default_fixture_root = object()
    default_design_doc = object()

    def throwing_spy(
        *,
        fixture_root: object = default_fixture_root,
        design_doc: object = default_design_doc,
    ) -> None:
        raise sentinel

    original = contract.require_stage0_fixture_obligations_discharged
    observed: BaseException | None = None
    try:
        contract.require_stage0_fixture_obligations_discharged = throwing_spy
        try:
            gate.require_stage6_candidate_submission_ready(
                fixture_root=fixture_root,
                design_doc=design_doc,
            )
        except BaseException as exc:
            observed = exc
        else:
            raise AssertionError("the throwing spy exception was swallowed")
    finally:
        contract.require_stage0_fixture_obligations_discharged = original

    assert observed is sentinel
    assert type(observed) is SentinelError
    assert not isinstance(observed, contract.ContractError)


def test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs(
) -> None:
    enumerated_paths = list_tracked_and_untracked_files(ROOT)
    candidate_paths = _select_inventory_paths(enumerated_paths)
    assert candidate_paths, "caller inventory の production Python 母集合が空"
    _assert_exact_inventory_roots(enumerated_paths, candidate_paths)
    sources = {
        path.as_posix(): (ROOT / path).read_text(encoding="utf-8")
        for path in candidate_paths
    }

    obligation_callers, adapter_callers, ambiguous_callers = _caller_inventory(
        sources
    )
    _assert_exact_paths(
        frozenset({_ADAPTER_PATH}),
        obligation_callers,
        label="obligation predicate",
    )
    _assert_exact_paths(
        frozenset(),
        adapter_callers,
        label="stage 6 adapter",
    )
    _assert_exact_paths(
        frozenset(),
        ambiguous_callers,
        label="ambiguous target reference",
    )

    prerequisite = ROOT / "docs" / "env-contract-activation-prerequisites.md"
    rows = [
        line
        for line in prerequisite.read_text(encoding="utf-8").splitlines()
        if line.startswith(
            "| 到達可能な段 6 production 経路が義務述語を通る |"
        )
    ]
    assert len(rows) == 1
    row_parts = rows[0].split("|")
    assert row_parts[0] == "" and row_parts[-1] == ""
    cells = tuple(part.strip() for part in row_parts[1:-1])
    assert len(cells) == 6
    assert cells == _EXPECTED_PREREQUISITE_CELLS

    design_text = contract.DESIGN_DOC.read_text(encoding="utf-8")
    assert design_text.count(_EXPECTED_DESIGN_10_2_FRAGMENT) == 1
    assert design_text.count(_EXPECTED_DESIGN_12_3_FRAGMENT) == 1


def test_stage6_candidate_gate_inventory_path_selection_is_exact() -> None:
    synthetic_paths = (
        Path("orchestrator/campaign/adapter.py"),
        Path("orchestrator/campaign/notes.txt"),
        Path("orchestrator/tests/test_adapter.py"),
        Path("tools/submit.py"),
        Path("another_package/worker.py"),
    )
    selected_paths = _select_inventory_paths(synthetic_paths)
    assert selected_paths == frozenset(
        {
            Path("orchestrator/campaign/adapter.py"),
            Path("tools/submit.py"),
            Path("another_package/worker.py"),
        }
    )
    _assert_exact_inventory_roots(synthetic_paths, selected_paths)

    shrunken_paths = frozenset(
        {
            Path("orchestrator/campaign/adapter.py"),
            Path("tools/submit.py"),
        }
    )
    try:
        _assert_exact_inventory_roots(synthetic_paths, shrunken_paths)
    except AssertionError as exc:
        assert "top-level roots drifted" in str(exc)
    else:
        raise AssertionError("inventory root comparison accepted a shrunken set")


def test_stage6_candidate_gate_caller_inventory_detects_additional_callers(
) -> None:
    baseline_sources = {
        _ADAPTER_PATH: (
            "contract.require_stage0_fixture_obligations_discharged()\n"
        ),
    }
    obligation_callers, adapter_callers, ambiguous_callers = _caller_inventory(
        baseline_sources
    )
    expected_obligation_callers = frozenset({_ADAPTER_PATH})
    expected_adapter_callers = frozenset()
    _assert_exact_paths(
        expected_obligation_callers,
        obligation_callers,
        label="baseline obligation predicate",
    )
    _assert_exact_paths(
        expected_adapter_callers,
        adapter_callers,
        label="baseline stage 6 adapter",
    )
    _assert_exact_paths(
        frozenset(),
        ambiguous_callers,
        label="baseline ambiguous target reference",
    )

    additional_path = "orchestrator/campaign/synthetic_stage6_submitter.py"
    sources_with_additional_caller = dict(baseline_sources)
    sources_with_additional_caller[additional_path] = (
        "contract.require_stage0_fixture_obligations_discharged()\n"
        "candidate_gate.require_stage6_candidate_submission_ready()\n"
    )
    obligation_callers, adapter_callers, ambiguous_callers = (
        _caller_inventory(sources_with_additional_caller)
    )
    assert obligation_callers == frozenset({_ADAPTER_PATH, additional_path})
    assert adapter_callers == frozenset({additional_path})
    assert ambiguous_callers == frozenset()
    for label, expected, observed in (
        (
            "additional obligation predicate",
            expected_obligation_callers,
            obligation_callers,
        ),
        (
            "additional stage 6 adapter",
            expected_adapter_callers,
            adapter_callers,
        ),
    ):
        try:
            _assert_exact_paths(expected, observed, label=label)
        except AssertionError as exc:
            assert "caller inventory drifted" in str(exc)
        else:
            raise AssertionError(
                f"baseline exact comparison accepted {label} caller"
            )

    indirect_controls = {
        "alias.py": (
            "ready = gate.require_stage6_candidate_submission_ready\n"
            "ready()\n"
        ),
        "getattr.py": (
            "getattr(gate, "
            "'require_stage6_candidate_submission_ready')()\n"
        ),
        "nfkc.py": (
            "contract.ｒｅｑｕｉｒｅ_stage0_fixture_obligations_discharged()\n"
        ),
        "mapping.py": (
            "{'submit': gate.require_stage6_candidate_submission_ready}"
            "['submit']()\n"
        ),
        "partial.py": (
            "partial(gate.require_stage6_candidate_submission_ready)()\n"
        ),
    }
    obligation_callers, adapter_callers, ambiguous_callers = _caller_inventory(
        indirect_controls
    )
    assert obligation_callers == frozenset({"nfkc.py"})
    assert adapter_callers == frozenset({"alias.py", "getattr.py"})
    assert ambiguous_callers == frozenset(
        {"alias.py", "mapping.py", "partial.py"}
    )

    non_reference_controls = {
        "docstring.py": (
            "'''require_stage6_candidate_submission_ready'''\n"
        ),
        "comment.py": (
            "# require_stage0_fixture_obligations_discharged\n"
        ),
        "plain_string.py": (
            "label = 'require_stage6_candidate_submission_ready'\n"
        ),
    }
    assert _caller_inventory(non_reference_controls) == (
        frozenset(),
        frozenset(),
        frozenset(),
    )


_EXPECTED_TEST_NAMES = frozenset(
    {
        "test_real_repository_rejects_stage6_candidate_for_undischarged_fixture_obligations",
        "test_discharged_fixture_obligations_reach_unresolved_stage6_policy_terminal",
        "test_stage6_candidate_gate_executes_obligation_predicate_with_forwarded_paths",
        "test_stage6_candidate_gate_propagates_non_contract_exception",
        "test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs",
        "test_stage6_candidate_gate_inventory_path_selection_is_exact",
        "test_stage6_candidate_gate_caller_inventory_detects_additional_callers",
    }
)


def _run() -> int:
    discovered = {
        name: value
        for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    }
    discovered_names = frozenset(discovered)
    if not discovered_names:
        print("FAIL no test functions discovered")
        return 1
    if discovered_names != _EXPECTED_TEST_NAMES:
        print(
            "FAIL test function inventory drifted: "
            f"expected={sorted(_EXPECTED_TEST_NAMES)!r} "
            f"observed={sorted(discovered_names)!r}"
        )
        return 1

    passed = failed = 0
    for name in sorted(_EXPECTED_TEST_NAMES):
        try:
            discovered[name]()
            print(f"PASS {name}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
