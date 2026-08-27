"""Independent consumer for the frozen B-4 analysis prose and implementation.

The implementation modules own source literals and never obtain contract values
from the preregistration document.  This consumer independently extracts the
document contract, compares it with already imported implementation values,
checks selected source assignments and enum members with ``ast``, and exercises
the ledger-selection and artifact-to-verdict paths with discriminating inputs.

The AST check is deliberately limited.  It establishes that the named contract
assignments and enum values are direct constants, literal tuples, or
``Fraction(<int>, <int>)`` calls.  It cannot prove that no hidden constant or
alternate computation path exists.  The source-closure, semantic section hash,
and behavior probes are additional tripwires, not a proof of that stronger claim.

The exact raw bytes hash of the ratified section is an unconditional pin.  A
second hash over a strictly defined semantic normalization is retained only to
separate diagnostics; it never rescues a raw-byte mismatch.

This consumer also owns the only public source-closure receipt producer.  It
emits canonical consumer-result bytes only after the document, source-shape, and
live behavior checks succeed, then binds those bytes and their hash into the
receipt.  The production caller inventory for the public pure analysis function
is pinned separately; that limited AST inventory does not make direct calls
impossible.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from fractions import Fraction
import ast
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from . import p3_b4_analysis_contract as contract
from . import p3_b4_analysis_ledgers as ledgers
from . import p3_b4_analysis_path as analysis_path
from .p3_b4_analysis_adapter import B4ExecutionDisposition


B4_PREREGISTRATION_CONSUMER_SCHEMA_VERSION = (
    "p3-b4-preregistration-consumer/v1"
)
PREREGISTRATION_SECTION_5_1_1_SHA256 = (
    "0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30"
)
PREREGISTRATION_SECTION_5_1_1_SEMANTIC_SHA256 = (
    "5d0b189bd68391b4a6876bd24400230e7186f6bc1fe374ea298d44edebcfd1a7"
)

_ANALYSIS_INVALID_REASONS = (
    "block_count_mismatch",
    "duplicate_block_id",
    "unknown_block_id",
    "precursor_hash_mismatch",
    "reference_binding_mismatch",
    "reference_value_domain_error",
    "status_domain_error",
    "throughput_contract_error",
    "floor_domain_error",
    "violation_count_domain_error",
    "binding_domain_error",
    "field_missing_or_ill_typed",
)
_REGISTRY_VIOLATION_REASONS = (
    "arm_digest_contaminated_precursor",
    "assignment_schedule_violated",
    "arm_asymmetric_gate",
    "env_tag_mismatch",
    "manifest_mutated_after_freeze",
)
_BLOCK_STATUSES = ("certified", "rejected", "aborted", "missing")
_MISSING_DISPOSITIONS = (
    "duplicate",
    "dry-pass",
    "stopped-before",
    "crash",
    "terminal-record-absent",
)
_VERDICT_BRANCH_ORDER = (
    "analysis_invalid",
    "protocol_violation",
    "contamination",
    "treatment_shortage",
    "p_on",
    "p_off",
    "otherwise",
)
_DISPLAY_CLASSIFICATIONS = (
    "成立",
    "不成立",
    "判定不能",
    "protocol violation",
)
_CLOSURE_PATHS = (
    "orchestrator/campaign/p3_b4_analysis_contract.py",
    "orchestrator/campaign/p3_b4_analysis_adapter.py",
    "orchestrator/campaign/p3_b4_analysis_ledgers.py",
    "orchestrator/campaign/p3_b4_analysis_path.py",
    "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",
)


class B4PreregistrationContractError(ValueError):
    """The document, source closure, or live implementation failed closed."""


@dataclass(frozen=True, slots=True)
class ParsedPreregisteredAnalysisContract:
    """Exact literals and structural facts extracted from section 5.1.1."""

    schema_version: str
    section_sha256: str
    semantic_section_sha256: str
    analysis_invalid_reasons: tuple[str, ...]
    registry_violation_reasons: tuple[str, ...]
    block_statuses: tuple[str, ...]
    rank_tiers: tuple[tuple[str, ...], ...]
    block_scores: tuple[Fraction, Fraction, Fraction]
    a_min: Fraction
    a_min_is_verdict_threshold: bool
    expected_block_count: int
    test_unit: str
    assignment_probability: Fraction
    assignment_independent_per_block: bool
    assignment_fixed_before_run: bool
    sign_distribution: str
    sign_upper_and_lower_tails: bool
    sign_m_zero_p_values: tuple[Fraction, Fraction]
    one_sided_alpha: Fraction
    two_sided_alpha: Fraction
    verdict_branch_order: tuple[str, ...]
    display_classifications: tuple[str, ...]
    theta_interval_method: str
    theta_interval_level: Fraction
    theta_m_zero_interval: tuple[Fraction, Fraction]
    theta_m_zero_estimable: bool
    missing_dispositions: tuple[str, ...]


def _consumer_result_wire_value(value: object) -> object:
    if isinstance(value, Fraction):
        return {
            "numerator": value.numerator,
            "denominator": value.denominator,
        }
    if type(value) is tuple:
        return [_consumer_result_wire_value(item) for item in value]
    if value is None or type(value) in (bool, int, str):
        return value
    _fail("consumer result contains a non-canonical value")


def _canonical_consumer_result_bytes(
    parsed: ParsedPreregisteredAnalysisContract,
) -> bytes:
    payload = {
        "schema_version": (
            analysis_path.B4_PREREGISTRATION_CONSUMER_RESULT_SCHEMA_VERSION
        ),
        "contract": {
            field.name: _consumer_result_wire_value(getattr(parsed, field.name))
            for field in fields(parsed)
        },
    }
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )


@dataclass(frozen=True, slots=True)
class _Heading:
    level: int
    start: int
    end: int
    text: str


@dataclass(frozen=True, slots=True)
class _Section:
    raw_bytes: bytes
    h5_parts: tuple[bytes, ...]


def _fail(message: str) -> None:
    raise B4PreregistrationContractError(message)


def _remove_inline_markup(value: str, *, heading: bool = False) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"`+", "", value)
    value = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", value)
    value = re.sub(r"(?<!\w)__([^_\n]+)__(?!\w)", r"\1", value)
    value = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"\1", value)
    value = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", value)
    value = re.sub(r"~~([^~\n]+)~~", r"\1", value)
    if heading:
        value = value.replace("*", "").replace("_", "")
    return value


def _normalize_heading(value: str) -> str:
    return " ".join(_remove_inline_markup(value, heading=True).split()).casefold()


def _without_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                return "".join(visible), True
            cursor = end + 3
            in_comment = False
            continue
        start = line.find("<!--", cursor)
        if start < 0:
            visible.append(line[cursor:])
            break
        visible.append(line[cursor:start])
        cursor = start + 4
        in_comment = True
    return "".join(visible), in_comment


def _headings(document_bytes: bytes) -> tuple[_Heading, ...]:
    try:
        text = document_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise B4PreregistrationContractError(
            "preregistration document is not strict UTF-8"
        ) from error

    result: list[_Heading] = []
    byte_offset = 0
    in_comment = False
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        line_bytes = line.encode("utf-8")
        visible, in_comment = _without_html_comments(line, in_comment)
        candidate = visible.rstrip("\r\n")
        fence = re.match(r"^[ ]{0,3}(`{3,}|~{3,})(?:[^`]*)$", candidate)
        if fence_character is not None:
            stripped = candidate.lstrip(" ")
            if re.match(
                rf"^{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                stripped,
            ):
                fence_character = None
                fence_length = 0
            byte_offset += len(line_bytes)
            continue
        if fence is not None:
            marker = fence.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            byte_offset += len(line_bytes)
            continue
        heading = re.match(
            r"^[ ]{0,3}(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$",
            candidate,
        )
        if heading is not None:
            result.append(
                _Heading(
                    level=len(heading.group(1)),
                    start=byte_offset,
                    end=byte_offset + len(line_bytes),
                    text=_normalize_heading(heading.group(2)),
                )
            )
        byte_offset += len(line_bytes)
    return tuple(result)


def _matches_fingerprint(text: str, tokens: tuple[str, ...]) -> bool:
    return all(_normalize_heading(token) in text for token in tokens)


_H5_FINGERPRINTS = (
    ("赤 precursor", "母集合", "適格性述語", "順序", "選択関数"),
    ("最小重要効果", "pilot", "独立", "固定"),
    ("n", "検定単位"),
    ("primary outcome", "純関数"),
    ("実験 verdict", "全域関数", "7.1", "4 分類", "写す"),
    ("本節", "発効", "条件", "要求"),
)


def _locate_section(document_bytes: bytes) -> _Section:
    if type(document_bytes) is not bytes:
        _fail("preregistration document must be bytes")
    headings = _headings(document_bytes)
    h4_matches = tuple(
        heading
        for heading in headings
        if heading.level == 4
        and _matches_fingerprint(
            heading.text,
            ("5.1.1", "分析契約", "一括凍結"),
        )
    )
    if len(h4_matches) != 1:
        _fail("normalized section 5.1.1 H4 fingerprint is absent or duplicated")
    h4 = h4_matches[0]
    end = len(document_bytes)
    for heading in headings:
        if heading.start > h4.start and heading.level <= 4:
            end = heading.start
            break
    nested_h5 = tuple(
        heading
        for heading in headings
        if h4.start < heading.start < end and heading.level == 5
    )
    if len(nested_h5) != len(_H5_FINGERPRINTS):
        _fail("section 5.1.1 H5 set is missing, duplicated, or has an extra member")
    for heading, fingerprint in zip(nested_h5, _H5_FINGERPRINTS, strict=True):
        if not _matches_fingerprint(heading.text, fingerprint):
            _fail("section 5.1.1 H5 fingerprint order does not match the freeze")
    parts = tuple(
        document_bytes[
            heading.start : (
                nested_h5[index + 1].start
                if index + 1 < len(nested_h5)
                else end
            )
        ]
        for index, heading in enumerate(nested_h5)
    )
    section = document_bytes[h4.start:end]
    if not section or any(not part for part in parts):
        _fail("section 5.1.1 or a required subsection is empty")
    return _Section(raw_bytes=section, h5_parts=parts)


def _semantic_section_bytes(section_bytes: bytes) -> bytes:
    text = section_bytes.decode("utf-8", errors="strict")
    visible: list[str] = []
    in_comment = False
    for line in text.splitlines(keepends=True):
        without_comment, in_comment = _without_html_comments(line, in_comment)
        heading = re.match(r"^[ ]{0,3}(#{1,6})[ \t]+(.*)$", without_comment)
        if heading is not None:
            tail = re.sub(r"[ \t]+#+[ \t]*(?:\r?\n)?$", "", heading.group(2))
            visible.append(f" H{len(heading.group(1))} {tail} ")
        else:
            visible.append(without_comment)
    normalized = _remove_inline_markup("".join(visible))
    return (" ".join(normalized.split()) + "\n").encode("utf-8")


def _normalized_part(part: bytes) -> str:
    return " ".join(_remove_inline_markup(part.decode("utf-8")).split())


def _literal_count(text: str, literal: str) -> int:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(literal)}(?![A-Za-z0-9_])"
    return len(re.findall(pattern, text))


def _require_literal_once(text: str, literal: str, label: str) -> None:
    if _literal_count(text, literal) != 1:
        _fail(f"{label} literal is absent or duplicated: {literal}")


def _require_regex_once(text: str, pattern: str, label: str) -> re.Match[str]:
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        _fail(f"{label} contract is absent or duplicated")
    return matches[0]


def _ordered_markers(text: str, markers: tuple[str, ...], label: str) -> None:
    cursor = 0
    for marker in markers:
        position = text.find(marker, cursor)
        if position < 0:
            _fail(f"{label} marker is absent or out of order: {marker}")
        cursor = position + len(marker)


def extract_preregistered_analysis_contract(
    document_bytes: bytes,
) -> ParsedPreregisteredAnalysisContract:
    """Extract the normalized H4/H5 contract and enforce both section pins."""

    section = _locate_section(document_bytes)
    raw_sha256 = hashlib.sha256(section.raw_bytes).hexdigest()
    semantic_sha256 = hashlib.sha256(
        _semantic_section_bytes(section.raw_bytes)
    ).hexdigest()
    if raw_sha256 != PREREGISTRATION_SECTION_5_1_1_SHA256:
        _fail("section 5.1.1 exact raw sha256 pin mismatches")
    if semantic_sha256 != PREREGISTRATION_SECTION_5_1_1_SEMANTIC_SHA256:
        _fail("section 5.1.1 semantic sha256 diagnostic pin mismatches")

    population, minimum, sample, primary, verdict, activation = tuple(
        _normalized_part(part) for part in section.h5_parts
    )
    del activation

    for literal in _ANALYSIS_INVALID_REASONS:
        _require_literal_once(primary, literal, "analysis_invalid reason")
    for literal in _REGISTRY_VIOLATION_REASONS:
        _require_literal_once(primary, literal, "registry violation reason")

    status_match = _require_regex_once(
        primary,
        r"status の値域は (certified) / (rejected) / (aborted) / (missing) のちょうど 4 値",
        "block status",
    )
    statuses = tuple(status_match.groups())
    if statuses != _BLOCK_STATUSES:
        _fail("block status order differs from the freeze")
    _require_regex_once(
        primary,
        r"1\. certified 2\. rejected と aborted .*?3\. missing",
        "status rank",
    )
    _require_literal_once(primary, "この 2 つの間だけが常に tie", "middle tie")
    _require_literal_once(primary, "tie ではない", "missing non-tie")
    _require_regex_once(
        primary,
        r"block score X は、on が上位なら 1、tie なら 1/2、off が上位なら 0 とする",
        "block score",
    )

    _require_literal_once(minimum, "A_min = 0.60", "A_min")
    _require_literal_once(minimum, "判定の閾値にしない", "A_min threshold exclusion")
    _require_literal_once(sample, "n = 201", "block count")
    _require_literal_once(sample, "検定単位は block とする", "test unit")

    _require_literal_once(population, "確率 1/2 ずつ", "assignment probability")
    _require_literal_once(population, "block ごとに独立に", "assignment independence")
    _require_literal_once(population, "実走前に", "assignment pre-run freeze")

    _require_literal_once(primary, "Bin(m, 1/2)", "sign distribution")
    _require_regex_once(
        primary,
        r"p_on は Bin\(m, 1/2\) の上側 .*?p_off は下側",
        "sign tails",
    )
    _require_literal_once(primary, "m = 0 のときは p_on = p_off = 1", "m-zero p values")
    _require_literal_once(sample, "方向ごとに 0.025", "one-sided alpha")
    _require_literal_once(sample, "両方向あわせて 0.05", "two-sided alpha")

    _ordered_markers(
        verdict,
        (
            "1. 出力が analysis_invalid",
            "2. registry_violation_count",
            "3. いずれかの block で contaminated",
            "4. 両アームとも treatment_fired",
            "5. p_on",
            "6. p_off",
            "7. それ以外",
        ),
        "verdict branch",
    )
    for classification in _DISPLAY_CLASSIFICATIONS:
        if classification not in verdict:
            _fail(f"display classification is absent: {classification}")
    _require_regex_once(
        verdict,
        r"Clopper-Pearson の厳密両側 95% 区間",
        "theta interval",
    )
    _require_regex_once(
        verdict,
        r"m = 0 のときは区間を \[0, 1\] とし、theta は推定不能",
        "theta m-zero rule",
    )

    _ordered_markers(
        primary,
        ("duplicate", "dry-pass", "実行前の停止", "crash", "終端記録の不在", "missing"),
        "missing disposition",
    )

    return ParsedPreregisteredAnalysisContract(
        schema_version=B4_PREREGISTRATION_CONSUMER_SCHEMA_VERSION,
        section_sha256=raw_sha256,
        semantic_section_sha256=semantic_sha256,
        analysis_invalid_reasons=_ANALYSIS_INVALID_REASONS,
        registry_violation_reasons=_REGISTRY_VIOLATION_REASONS,
        block_statuses=statuses,
        rank_tiers=(("certified",), ("rejected", "aborted"), ("missing",)),
        block_scores=(Fraction(1), Fraction(1, 2), Fraction(0)),
        a_min=Fraction(3, 5),
        a_min_is_verdict_threshold=False,
        expected_block_count=201,
        test_unit="block",
        assignment_probability=Fraction(1, 2),
        assignment_independent_per_block=True,
        assignment_fixed_before_run=True,
        sign_distribution="Bin(m, 1/2)",
        sign_upper_and_lower_tails=True,
        sign_m_zero_p_values=(Fraction(1), Fraction(1)),
        one_sided_alpha=Fraction(1, 40),
        two_sided_alpha=Fraction(1, 20),
        verdict_branch_order=_VERDICT_BRANCH_ORDER,
        display_classifications=_DISPLAY_CLASSIFICATIONS,
        theta_interval_method="Clopper-Pearson exact two-sided",
        theta_interval_level=Fraction(95, 100),
        theta_m_zero_interval=(Fraction(0), Fraction(1)),
        theta_m_zero_estimable=False,
        missing_dispositions=_MISSING_DISPOSITIONS,
    )


def _parse_source(source_bytes: bytes, label: str) -> ast.Module:
    if type(source_bytes) is not bytes:
        _fail(f"{label} source must be bytes")
    try:
        text = source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise B4PreregistrationContractError(
            f"{label} source is not strict UTF-8"
        ) from error
    try:
        return ast.parse(text)
    except SyntaxError as error:
        raise B4PreregistrationContractError(
            f"{label} source is not valid Python"
        ) from error


def _direct_literal_value(node: ast.expr) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_direct_literal_value(item) for item in node.elts)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Fraction"
        and not node.keywords
        and len(node.args) in (1, 2)
        and all(
            isinstance(argument, ast.Constant)
            and type(argument.value) is int
            for argument in node.args
        )
    ):
        values = tuple(argument.value for argument in node.args)
        return Fraction(*values)
    _fail("contract value is derived rather than a permitted source literal")


def _module_assignments(tree: ast.Module) -> dict[str, ast.expr]:
    result: dict[str, ast.expr] = {}
    duplicates: set[str] = set()
    for statement in tree.body:
        name: str | None = None
        value: ast.expr | None = None
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            name = statement.targets[0].id
            value = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            name = statement.target.id
            value = statement.value
        if name is not None and value is not None:
            if name in result:
                duplicates.add(name)
            result[name] = value
    if duplicates:
        _fail("contract source contains duplicate module assignments")
    return result


def _enum_literals(tree: ast.Module, class_name: str) -> tuple[object, ...]:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    if len(matches) != 1:
        _fail(f"contract enum is absent or duplicated: {class_name}")
    members: list[object] = []
    for statement in matches[0].body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id.isupper()
        ):
            members.append(_direct_literal_value(statement.value))
    if not members:
        _fail(f"contract enum has no literal members: {class_name}")
    return tuple(members)


def _assert_contract_function_shapes(tree: ast.Module) -> None:
    evaluate = _function(tree, "evaluate_analysis", "contract")
    evaluate_ifs = [node for node in evaluate.body if isinstance(node, ast.If)]
    if (
        len(evaluate_ifs) != 1
        or "B4AnalysisInvalid" not in ast.unparse(evaluate_ifs[0].test)
    ):
        _fail("analysis_invalid is not the first public verdict branch")

    validated = _function(tree, "_evaluate_validated_analysis", "contract")
    chains = [node for node in validated.body if isinstance(node, ast.If)]
    if len(chains) != 1:
        _fail("validated verdict source does not have one ordered branch chain")
    tests: list[str] = []
    branch = chains[0]
    while True:
        tests.append(ast.unparse(branch.test))
        if len(branch.orelse) == 1 and isinstance(branch.orelse[0], ast.If):
            branch = branch.orelse[0]
            continue
        break
    required_tokens = (
        ("registry_violation_count", "assignment_followed", "protocol_ok"),
        ("contaminated",),
        ("treatment_fired", "expected_block_count"),
        ("p_values.p_on", "ONE_SIDED_ALPHA"),
        ("p_values.p_off", "ONE_SIDED_ALPHA"),
    )
    if len(tests) != len(required_tokens):
        _fail("validated verdict branch count changed")
    for test, tokens in zip(tests, required_tokens, strict=True):
        if not all(token in test for token in tokens) or "A_MIN" in test:
            _fail("validated verdict branch order or threshold changed")


def assert_contract_constants_are_source_literals(
    contract_source_bytes: bytes,
) -> None:
    """Require named assignments and all contract enum values to be direct literals."""

    tree = _parse_source(contract_source_bytes, "contract")
    assignments = _module_assignments(tree)
    expected = {
        "B4_ANALYSIS_CONTRACT_SCHEMA_VERSION": contract.B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        "EXPECTED_BLOCK_COUNT": contract.EXPECTED_BLOCK_COUNT,
        "A_MIN": contract.A_MIN,
        "ONE_SIDED_ALPHA": contract.ONE_SIDED_ALPHA,
        "TWO_SIDED_ALPHA": contract.TWO_SIDED_ALPHA,
        "TEST_UNIT": contract.TEST_UNIT,
    }
    for name, imported_value in expected.items():
        if name not in assignments:
            _fail(f"contract source assignment is absent: {name}")
        if _direct_literal_value(assignments[name]) != imported_value:
            _fail(f"contract source literal differs from imported value: {name}")
    for class_name in (
        "B4AnalysisInvalidReason",
        "B4RegistryViolationReason",
        "B4Arm",
        "B4BlockStatus",
        "B4Verdict",
    ):
        source_values = _enum_literals(tree, class_name)
        imported_type = getattr(contract, class_name)
        if source_values != tuple(member.value for member in imported_type):
            _fail(f"contract enum source differs from imported values: {class_name}")
    _assert_contract_function_shapes(tree)


def _function(tree: ast.Module, name: str, label: str) -> ast.FunctionDef:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        _fail(f"{label} function is absent or duplicated: {name}")
    return matches[0]


def _call_lines(function: ast.FunctionDef, name: str) -> tuple[int, ...]:
    return tuple(
        node.lineno
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == name
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == name
        )
    )


def _assert_source_closure_shapes(
    *,
    ledgers_source_bytes: bytes,
    path_source_bytes: bytes,
) -> None:
    ledger_tree = _parse_source(ledgers_source_bytes, "ledgers")
    generate = _function(ledger_tree, "generate_analysis_manifest", "ledgers")
    first_slice = [
        node
        for node in ast.walk(generate)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "eligible"
        and isinstance(node.slice, ast.Slice)
        and node.slice.lower is None
        and isinstance(node.slice.upper, ast.Name)
        and node.slice.upper.id == "EXPECTED_BLOCK_COUNT"
        and node.slice.step is None
    ]
    if len(first_slice) != 1:
        _fail("ledger selection is not the unique first-n source slice")
    violation_lines = _call_lines(generate, "derive_registry_violation_count")
    eligible_lines = tuple(
        node.lineno
        for node in ast.walk(generate)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == "eligible"
    )
    if (
        len(violation_lines) != 1
        or len(eligible_lines) != 1
        or violation_lines[0] >= eligible_lines[0]
    ):
        _fail("registry violation derivation no longer precedes eligibility filtering")

    path_tree = _parse_source(path_source_bytes, "analysis path")
    evaluate = _function(path_tree, "evaluate_b4_artifacts", "analysis path")
    derive_lines = _call_lines(evaluate, "derive_registry_violation_count")
    adapt_lines = _call_lines(evaluate, "adapt_raw_blocks")
    evaluate_lines = _call_lines(evaluate, "evaluate_analysis")
    if (
        len(derive_lines) != 1
        or len(adapt_lines) != 1
        or len(evaluate_lines) != 1
        or not derive_lines[0] < adapt_lines[0] < evaluate_lines[0]
    ):
        _fail("analysis path violation, adaptation, and verdict order changed")
    assignments = _module_assignments(path_tree)
    closure_node = assignments.get("_SOURCE_CLOSURE_PATHS")
    if closure_node is None or _direct_literal_value(closure_node) != _CLOSURE_PATHS:
        _fail("analysis source closure member tuple changed")


def _behavior_attempt(
    index: int,
    *,
    arm_digest_received: bool = False,
) -> ledgers.B4ScheduledAttemptInput:
    digest = hashlib.sha256(f"behavior-{index}".encode("ascii")).hexdigest()
    return ledgers.B4ScheduledAttemptInput(
        schema_version=ledgers.B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
        attempt_id=f"behavior-attempt-{index:03d}",
        registry_ordinal=index,
        block_id=f"behavior-block-{index:03d}",
        driver="behavior-driver",
        reason=ledgers.B4ScheduledAttemptReason.SCHEDULED,
        whiteboard_result=ledgers.B4WhiteboardResult.REJECTED,
        digest_red_classes=(ledgers.B4DigestRedClass.VERIFY_RED,),
        workload="behavior-workload",
        calibrated_workload_member=True,
        initial_proposal_sha256=digest,
        bootstrap_member=True,
        reference_tps=1000 + index,
        reference_snapshot_hash=hashlib.sha256(
            f"snapshot-{index}".encode("ascii")
        ).hexdigest(),
        reference_receipt_hash=hashlib.sha256(
            f"receipt-{index}".encode("ascii")
        ).hexdigest(),
        reference_is_unique=True,
        arm_digest_received=arm_digest_received,
    )


def _behavior_registry(
    attempts: tuple[ledgers.B4ScheduledAttemptInput, ...],
) -> tuple[
    ledgers.B4ScheduleReceipt,
    ledgers.B4ScheduledAttemptRegistry,
]:
    receipt = ledgers.B4ScheduleReceipt(
        schema_version=ledgers.B4_SCHEDULE_RECEIPT_SCHEMA_VERSION,
        issuer_sha256=hashlib.sha256(b"behavior-schedule-issuer").hexdigest(),
        scheduled_inputs_sha256=ledgers.scheduled_attempts_sha256(attempts),
        scheduled_attempt_count=len(attempts),
    )
    registry = ledgers.seal_scheduled_attempt_registry(
        scheduled_inputs=attempts,
        schedule_receipt=receipt,
    )
    return receipt, registry


def _behavior_seed(
    registry: ledgers.B4ScheduledAttemptRegistry,
) -> ledgers.B4RandomizationSeedRecord:
    return ledgers.B4RandomizationSeedRecord(
        schema_version=ledgers.B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
        seed_hex=hashlib.sha256(b"behavior-seed").hexdigest(),
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        issuer_sha256=hashlib.sha256(b"behavior-seed-issuer").hexdigest(),
        source_receipt_sha256=hashlib.sha256(b"behavior-seed-receipt").hexdigest(),
    )


def _assert_selection_behavior() -> None:
    attempts = tuple(
        _behavior_attempt(index)
        for index in range(contract.EXPECTED_BLOCK_COUNT + 1)
    )
    receipt, registry = _behavior_registry(attempts)
    seed = _behavior_seed(registry)
    manifest = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    if not isinstance(manifest, ledgers.B4AnalysisManifest):
        _fail("first-n behavior probe did not produce a manifest")
    expected = tuple(
        attempt.attempt_id for attempt in attempts[: contract.EXPECTED_BLOCK_COUNT]
    )
    if tuple(row.attempt_id for row in manifest.rows) != expected:
        _fail("manifest behavior does not select the first n eligible rows")


def _assert_violation_behavior() -> None:
    attempts = (_behavior_attempt(0, arm_digest_received=True),)
    receipt, registry = _behavior_registry(attempts)
    contaminated = attempts[0]
    registry = ledgers.append_registry_violation(
        registry,
        schedule_receipt=receipt,
        attempt_id=contaminated.attempt_id,
        block_id=contaminated.block_id,
        reason=contract.B4RegistryViolationReason.ARM_DIGEST_CONTAMINATED_PRECURSOR,
        evidence_sha256=hashlib.sha256(b"behavior-violation").hexdigest(),
    )
    violation_count = analysis_path.derive_registry_violation_count(
        registry=registry,
        schedule_receipt=receipt,
    )
    if violation_count != 1:
        _fail("full-registry violation count ignored an ineligible row")


def _assert_rank_and_threshold_behavior() -> None:
    source_hash = hashlib.sha256(b"rank-behavior").hexdigest()

    def arm(
        status: contract.B4BlockStatus,
        throughput: Fraction | None,
    ) -> contract.B4ArmObservation:
        return contract.B4ArmObservation(
            schema_version=contract.B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
            precursor_hash=source_hash,
            status=status,
            throughput=throughput,
            treatment_fired=True,
            contaminated=False,
            protocol_ok=True,
        )

    blocks = tuple(
        contract.B4BlockObservation(
            schema_version=contract.B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
            block_id=f"rank-behavior-{index:03d}",
            reference_tps=Fraction(1),
            reference_snapshot_hash=source_hash,
            reference_receipt_hash=source_hash,
            assignment_followed=True,
            on=arm(
                contract.B4BlockStatus.CERTIFIED,
                Fraction(2) if index < 6 else Fraction(1),
            ),
            off=arm(contract.B4BlockStatus.CERTIFIED, Fraction(1)),
        )
        for index in range(contract.EXPECTED_BLOCK_COUNT)
    )
    binding = contract.B4ContractBinding(
        schema_version=contract.B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        manifest_sha256=source_hash,
        registry_sha256=source_hash,
        blocks=tuple(
            contract.B4ContractBlockBinding(
                schema_version=contract.B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
                block_id=block.block_id,
                reference_tps=block.reference_tps,
                reference_snapshot_hash=block.reference_snapshot_hash,
                reference_receipt_hash=block.reference_receipt_hash,
                assignment_schedule=(contract.B4Arm.ON, contract.B4Arm.OFF),
            )
            for block in blocks
        ),
        expected_block_count=contract.EXPECTED_BLOCK_COUNT,
    )
    result = contract.evaluate_analysis(
        floor=Fraction(0),
        contract_binding=binding,
        registry_violation_count=0,
        blocks=blocks,
    )
    if (
        result.analysis_invalid is not None
        or result.verdict is not contract.B4Verdict.ESTABLISHED
        or result.a_hat is None
        or result.a_hat.value >= contract.A_MIN
    ):
        _fail("A_min became a verdict threshold or score behavior changed")

    probe = contract.B4BlockObservation(
        schema_version=contract.B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        block_id="rank-probe",
        reference_tps=Fraction(1),
        reference_snapshot_hash=source_hash,
        reference_receipt_hash=source_hash,
        assignment_followed=True,
        on=arm(contract.B4BlockStatus.CERTIFIED, Fraction(1)),
        off=arm(contract.B4BlockStatus.CERTIFIED, Fraction(1)),
    )
    rejected = arm(contract.B4BlockStatus.REJECTED, None)
    aborted = arm(contract.B4BlockStatus.ABORTED, None)
    missing = arm(contract.B4BlockStatus.MISSING, None)
    rank_cases = (
        (replace(probe, on=rejected, off=aborted), Fraction(1, 2)),
        (replace(probe, on=missing, off=rejected), Fraction(0)),
        (replace(probe, on=rejected, off=missing), Fraction(1)),
        (
            replace(
                probe,
                on=arm(contract.B4BlockStatus.CERTIFIED, Fraction(11, 10)),
                off=arm(contract.B4BlockStatus.CERTIFIED, Fraction(1)),
            ),
            Fraction(1, 2),
        ),
    )
    if any(
        contract.block_score(block, floor=Fraction(1, 10)) != expected
        for block, expected in rank_cases
    ):
        _fail("status rank, tie, or inclusive floor behavior changed")


def _assert_imported_values(
    parsed: ParsedPreregisteredAnalysisContract,
) -> None:
    comparisons = (
        (
            tuple(member.value for member in contract.B4AnalysisInvalidReason),
            parsed.analysis_invalid_reasons,
            "analysis_invalid enum",
        ),
        (
            tuple(member.value for member in contract.B4RegistryViolationReason),
            parsed.registry_violation_reasons,
            "registry violation enum",
        ),
        (
            tuple(member.value for member in contract.B4BlockStatus),
            parsed.block_statuses,
            "block status enum",
        ),
        (contract.A_MIN, parsed.a_min, "A_min"),
        (contract.EXPECTED_BLOCK_COUNT, parsed.expected_block_count, "block count"),
        (contract.TEST_UNIT, parsed.test_unit, "test unit"),
        (contract.ONE_SIDED_ALPHA, parsed.one_sided_alpha, "one-sided alpha"),
        (contract.TWO_SIDED_ALPHA, parsed.two_sided_alpha, "two-sided alpha"),
    )
    for imported, documented, label in comparisons:
        if imported != documented:
            _fail(f"imported implementation differs from document: {label}")
    if tuple(member.value for member in B4ExecutionDisposition if member is not B4ExecutionDisposition.EXECUTED) != parsed.missing_dispositions:
        _fail("adapter missing-disposition mapping differs from document")
    if tuple(member.value for member in contract.B4Verdict) != (
        "established",
        "not_established",
        "indeterminate",
        "protocol_violation",
    ):
        _fail("implementation verdict display vocabulary changed")
    p_zero = contract.exact_sign_pvalues(on_wins=0, non_ties=0)
    if (p_zero.p_on, p_zero.p_off) != parsed.sign_m_zero_p_values:
        _fail("m-zero sign-test behavior differs from document")
    theta_zero = contract.clopper_pearson_theta_95(on_wins=0, non_ties=0)
    if (
        (theta_zero.lower, theta_zero.upper) != parsed.theta_m_zero_interval
        or theta_zero.theta_estimable != parsed.theta_m_zero_estimable
    ):
        _fail("m-zero theta behavior differs from document")


def assert_preregistration_matches_implementation(
    *,
    document_bytes: bytes,
    contract_source_bytes: bytes,
    ledgers_source_bytes: bytes,
    path_source_bytes: bytes,
) -> ParsedPreregisteredAnalysisContract:
    """Check document literals, source closure shapes, and live behaviors."""

    parsed = extract_preregistered_analysis_contract(document_bytes)
    assert_contract_constants_are_source_literals(contract_source_bytes)
    _assert_source_closure_shapes(
        ledgers_source_bytes=ledgers_source_bytes,
        path_source_bytes=path_source_bytes,
    )
    _assert_imported_values(parsed)
    _assert_rank_and_threshold_behavior()
    _assert_selection_behavior()
    _assert_violation_behavior()
    return parsed


def _verified_repository_contract_and_receipt(
    *,
    repository_root: Path,
) -> tuple[
    ParsedPreregisteredAnalysisContract,
    analysis_path.B4AnalysisSourceClosureReceipt,
]:
    """Run the consumer, then bind its canonical success result to a receipt."""

    if not isinstance(repository_root, Path):
        _fail("repository_root must be a Path")
    document_path = (
        repository_root
        / "docs/phase3-b4-reflux-ablation-preregistration.md"
    )
    try:
        document_bytes = document_path.read_bytes()
        member_bytes = {
            path: (repository_root / path).read_bytes()
            for path in _CLOSURE_PATHS
        }
    except OSError as error:
        raise B4PreregistrationContractError(
            "document or source closure member is unreadable"
        ) from error
    parsed = assert_preregistration_matches_implementation(
        document_bytes=document_bytes,
        contract_source_bytes=member_bytes[_CLOSURE_PATHS[0]],
        ledgers_source_bytes=member_bytes[_CLOSURE_PATHS[2]],
        path_source_bytes=member_bytes[_CLOSURE_PATHS[3]],
    )
    try:
        consumer_result_bytes = _canonical_consumer_result_bytes(parsed)
        receipt = analysis_path._generate_analysis_source_closure_receipt(
            repository_root=repository_root,
            preregistration_document_bytes=document_bytes,
            consumer_result_canonical_bytes=consumer_result_bytes,
        )
    except analysis_path.B4AnalysisSourceClosureError as error:
        raise B4PreregistrationContractError(
            "analysis source closure receipt generation failed"
        ) from error
    if (
        tuple(member.path for member in receipt.members) != _CLOSURE_PATHS
        or receipt.preregistration_section_sha256 != parsed.section_sha256
        or receipt.consumer_result_canonical_bytes != consumer_result_bytes
        or receipt.consumer_result_sha256
        != hashlib.sha256(consumer_result_bytes).hexdigest()
    ):
        _fail("analysis source closure receipt differs from the consumer closure")
    return parsed, receipt


def verify_repository_preregistration_contract(
    *,
    repository_root: Path,
) -> ParsedPreregisteredAnalysisContract:
    """Read every fixed member and require consumer-bound receipt generation."""

    parsed, _receipt = _verified_repository_contract_and_receipt(
        repository_root=repository_root
    )
    return parsed


def generate_verified_analysis_source_closure_receipt(
    *,
    repository_root: Path,
) -> analysis_path.B4AnalysisSourceClosureReceipt:
    """Return a closure receipt only after all consumer checks succeed."""

    _parsed, receipt = _verified_repository_contract_and_receipt(
        repository_root=repository_root
    )
    return receipt


__all__ = [
    "B4_PREREGISTRATION_CONSUMER_SCHEMA_VERSION",
    "B4PreregistrationContractError",
    "PREREGISTRATION_SECTION_5_1_1_SEMANTIC_SHA256",
    "PREREGISTRATION_SECTION_5_1_1_SHA256",
    "ParsedPreregisteredAnalysisContract",
    "assert_contract_constants_are_source_literals",
    "assert_preregistration_matches_implementation",
    "extract_preregistered_analysis_contract",
    "generate_verified_analysis_source_closure_receipt",
    "verify_repository_preregistration_contract",
]
