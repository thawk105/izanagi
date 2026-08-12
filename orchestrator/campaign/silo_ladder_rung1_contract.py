"""Silo ladder rung 1 の patch/ledger 静的契約。

この module は入力された文字列だけを検査する。subprocess、filesystem 読み書き、
compiler 呼び出しは行わない。
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


RUNG_MACRO = "IZANAGI_SILO_LADDER_RUNG1"
REPORT_MACRO = "IZANAGI_SILO_LADDER_RUNG1_REPORT"
IDENTITY_SYMBOL = "izanagi_silo_ladder_rung1_identity"
PATCH_PATH = "patches/silo_ladder_rung1.patch"
SOURCE_FILES = (
    "cc/silo/transaction.cc",
    "cc/silo/ycsb_silo.cc",
)

NON_THREAD_LOCAL = "non_thread_local"
GUARD_LIFETIME = "guard_lifetime"
SINGLE_CAS_NO_BYPASS = "single_cas_no_bypass"
MACRO_DISCIPLINE = "macro_discipline"
STOCK_VERBATIM = "stock_verbatim"
IDENTITY_SYMBOL_REASON = "identity_symbol"
DECLARED_FILES_ONLY = "declared_files_only"
LEDGER_CONSISTENCY = "ledger_consistency"


@dataclass(frozen=True)
class ContractFailure:
    """一つの静的契約に帰属する fail-closed 理由。"""

    reason_code: str
    detail: str


@dataclass(frozen=True)
class _Hunk:
    new_lines: tuple[str, ...]
    added_lines: tuple[str, ...]


@dataclass(frozen=True)
class _PatchFile:
    old_path: str
    new_path: str
    hunks: tuple[_Hunk, ...]


def _parse_patch(patch_text: str) -> tuple[_PatchFile, ...]:
    files: list[_PatchFile] = []
    current_old: str | None = None
    current_new: str | None = None
    hunks: list[_Hunk] = []
    new_lines: list[str] | None = None
    added_lines: list[str] | None = None

    def finish_hunk() -> None:
        nonlocal new_lines, added_lines
        if new_lines is not None and added_lines is not None:
            hunks.append(_Hunk(tuple(new_lines), tuple(added_lines)))
        new_lines = None
        added_lines = None

    def finish_file() -> None:
        nonlocal current_old, current_new, hunks
        finish_hunk()
        if current_old is not None and current_new is not None:
            files.append(_PatchFile(current_old, current_new, tuple(hunks)))
        current_old = None
        current_new = None
        hunks = []

    for line in patch_text.splitlines():
        match = re.fullmatch(r"diff --git a/(.+) b/(.+)", line)
        if match:
            finish_file()
            current_old, current_new = match.groups()
            continue
        if line.startswith("@@ "):
            finish_hunk()
            new_lines = []
            added_lines = []
            continue
        if new_lines is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            value = line[1:]
            new_lines.append(value)
            added_lines.append(value)
        elif line.startswith(" "):
            new_lines.append(line[1:])
        elif line.startswith("-") or line == r"\ No newline at end of file":
            continue
        else:
            # A malformed hunk is made observably invalid for all structural checks.
            new_lines.append("\0INVALID-HUNK-LINE\0")
    finish_file()
    return tuple(files)


def _file(patch: Sequence[_PatchFile], path: str) -> _PatchFile | None:
    matches = [item for item in patch if item.new_path == path]
    return matches[0] if len(matches) == 1 else None


def _all_added(item: _PatchFile | None) -> list[str]:
    if item is None:
        return []
    return [line for hunk in item.hunks for line in hunk.added_lines]


def _blocks(
    item: _PatchFile | None, condition: str
) -> list[tuple[list[str], list[str] | None]]:
    """Exact ``#if condition`` blocks を、top-level #else で二分して返す。"""
    found: list[tuple[list[str], list[str] | None]] = []
    if item is None:
        return found
    opener = f"#if {condition}"
    for hunk in item.hunks:
        lines = list(hunk.new_lines)
        for start, line in enumerate(lines):
            if line.strip() != opener:
                continue
            depth = 1
            else_at: int | None = None
            for index in range(start + 1, len(lines)):
                directive = lines[index].strip()
                if re.match(r"#if(?:def|ndef)?\b", directive):
                    depth += 1
                elif directive == "#endif":
                    depth -= 1
                    if depth == 0:
                        if else_at is None:
                            found.append((lines[start + 1:index], None))
                        else:
                            found.append(
                                (
                                    lines[start + 1:else_at],
                                    lines[else_at + 1:index],
                                )
                            )
                        break
                elif directive == "#else" and depth == 1:
                    else_at = index
    return found


def _cas_block(
    transaction: _PatchFile | None,
) -> tuple[list[str], list[str]] | None:
    matches = [
        (on, off)
        for on, off in _blocks(transaction, RUNG_MACRO)
        if off is not None and "compareExchange" in "\n".join(off)
    ]
    if len(matches) != 1:
        return None
    on, off = matches[0]
    assert off is not None
    return on, off


def _failure(reason_code: str, details: list[str]) -> ContractFailure | None:
    if not details:
        return None
    return ContractFailure(reason_code, "; ".join(details))


def _check_non_thread_local(transaction: _PatchFile | None) -> ContractFailure | None:
    lines = _all_added(transaction)
    declaration_indexes = [
        index
        for index, line in enumerate(lines)
        if re.search(
            r"\b(?:static\s+|thread_local\s+|inline\s+)*"
            r"std::mutex\s+gate_mutex\b",
            line,
        )
    ]
    details: list[str] = []
    if len(declaration_indexes) != 1:
        details.append("gate_mutex declaration count is not one")
        return _failure(NON_THREAD_LOCAL, details)

    index = declaration_indexes[0]
    if lines[index].strip() != "std::mutex gate_mutex;":
        details.append("gate_mutex is not the exact non-static non-thread-local declaration")
    namespace_open = [
        pos
        for pos, line in enumerate(lines[:index])
        if line.strip() == "namespace izanagi_silo_ladder_rung1 {"
    ]
    if len(namespace_open) != 1:
        details.append("expected namespace opening is missing or duplicated")
    else:
        depth = 1
        for line in lines[namespace_open[0] + 1:index]:
            depth += line.count("{") - line.count("}")
        if depth != 1:
            details.append("gate_mutex is not at namespace scope")
    return _failure(NON_THREAD_LOCAL, details)


def _brace_depths(lines: Sequence[str]) -> list[int]:
    depth = 0
    result: list[int] = []
    for line in lines:
        result.append(depth)
        code = line.split("//", 1)[0]
        depth += code.count("{") - code.count("}")
    return result


def _calls(text: str, function: str) -> list[str]:
    """function 呼出しを括弧対応で抽出し、空白を正規化する。"""
    found: list[str] = []
    needle = f"{function}("
    cursor = 0
    while True:
        start = text.find(needle, cursor)
        if start < 0:
            break
        depth = 0
        end: int | None = None
        for index in range(start + len(function), len(text)):
            char = text[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            found.append("\0UNTERMINATED-CALL\0")
            break
        found.append(re.sub(r"\s+", " ", text[start:end]))
        cursor = end
    return found


def _check_guard_lifetime(transaction: _PatchFile | None) -> ContractFailure | None:
    block = _cas_block(transaction)
    if block is None:
        return ContractFailure(GUARD_LIFETIME, "unique gated CAS block is missing")
    on, _ = block
    guard_indexes = [
        index
        for index, line in enumerate(on)
        if "std::lock_guard<std::mutex> guard(" in line
    ]
    cas_indexes = [
        index for index, line in enumerate(on) if "compareExchange" in line
    ]
    details: list[str] = []
    if len(guard_indexes) != 1 or not cas_indexes:
        details.append("guard and primary CAS must be present")
        return _failure(GUARD_LIFETIME, details)
    guard_at = guard_indexes[0]
    cas_at = cas_indexes[0]
    depths = _brace_depths(on)
    guard_statement = " ".join(on[guard_at:guard_at + 2])
    guard_statement = re.sub(r"\s+", " ", guard_statement).strip()
    if guard_statement != (
        "std::lock_guard<std::mutex> guard( "
        "izanagi_silo_ladder_rung1::gate_mutex);"
    ):
        details.append("guard declaration does not bind the rung namespace mutex")
    if guard_at >= cas_at:
        details.append("guard declaration does not precede CAS")
    elif depths[guard_at] <= 0:
        details.append("guard is not in a lexical block")
    elif depths[cas_at] < depths[guard_at]:
        details.append("guard scope closes before CAS")
    elif min(depths[guard_at:cas_at + 1]) < depths[guard_at]:
        details.append("guard lifetime does not continuously contain CAS")
    return _failure(GUARD_LIFETIME, details)


def _check_single_cas_no_bypass(
    transaction: _PatchFile | None,
) -> ContractFailure | None:
    block = _cas_block(transaction)
    if block is None:
        return ContractFailure(
            SINGLE_CAS_NO_BYPASS, "unique gated CAS block is missing"
        )
    on, _ = block
    text = "\n".join(on)
    details: list[str] = []
    on_calls = _calls(text, "compareExchange")
    off_calls = _calls("\n".join(block[1]), "compareExchange")
    if len(on_calls) != 1:
        details.append("ON branch compareExchange count is not one")
    elif len(off_calls) != 1 or on_calls[0] != off_calls[0]:
        details.append("ON branch CAS lvalue or arguments differ from stock")
    store_patterns = (
        r"\bstoreRelease\s*\(",
        r"\bstoreRelaxed\s*\(",
        r"\batomicStore\w*\s*\(",
        r"\.store\s*\(",
    )
    if any(re.search(pattern, text) for pattern in store_patterns):
        details.append("ON branch contains an alternate store")
    return _failure(SINGLE_CAS_NO_BYPASS, details)


def _check_macro_discipline(patch: Sequence[_PatchFile]) -> ContractFailure | None:
    transaction = _file(patch, SOURCE_FILES[0])
    ycsb = _file(patch, SOURCE_FILES[1])
    added = _all_added(transaction) + _all_added(ycsb)
    text = "\n".join(added)
    macros = set(re.findall(r"\b(?:IZANAGI|CCBENCH)_[A-Z0-9_]+\b", text))
    details: list[str] = []
    if macros != {RUNG_MACRO, REPORT_MACRO}:
        details.append(f"bare macro set mismatch: {sorted(macros)!r}")
    if "CCBENCH_" in text:
        details.append("CCBENCH_ prefix is forbidden")
    if "IZANAGI_T139_PROBE" in text:
        details.append("disposable probe token remains")

    cas_blocks = [
        block for block in _blocks(transaction, RUNG_MACRO)
        if block[1] is not None and "compareExchange" in "\n".join(block[1] or [])
    ]
    if len(cas_blocks) != 1:
        details.append("RUNG1 default-OFF #if/#else/#endif CAS block is not unique")

    report_condition = f"{RUNG_MACRO} && {REPORT_MACRO}"
    report_blocks = _blocks(ycsb, report_condition)
    if len(report_blocks) != 1 or report_blocks[0][1] is not None:
        details.append("reporter is not under the exact RUNG1 && REPORT gate")
    else:
        report_text = "\n".join(report_blocks[0][0])
        required_report_fragments = (
            "worker < TotalThreadNum",
            "silo_ladder_rung1.worker_commit[",
            "CCBenchResults[worker].local_commit_counts_",
            "silo_ladder_rung1.worker_batch_commit[",
            "CCBenchResults[worker].local_batch_commit_counts_",
            "std::cout.flush();",
        )
        missing = [
            fragment
            for fragment in required_report_fragments
            if fragment not in report_text
        ]
        if missing:
            details.append(f"reporter footer is incomplete: {missing!r}")

    directive_lines = [
        line.strip() for line in added
        if line.lstrip().startswith(("#if", "#ifdef", "#ifndef"))
    ]
    expected_directives = [
        f"#if {RUNG_MACRO}",
        f"#if {RUNG_MACRO}",
        f"#if {report_condition}",
    ]
    if sorted(directive_lines) != sorted(expected_directives):
        details.append("preprocessor gate directives are not the closed expected set")
    return _failure(MACRO_DISCIPLINE, details)


def _stock_cas_lines(stock_transaction: str) -> list[str] | None:
    function_at = stock_transaction.find("void TxExecutor::lockWriteSet()")
    if function_at < 0:
        return None
    function_end = stock_transaction.find("\n}\n", function_at)
    if function_end < 0:
        return None
    lines = stock_transaction[function_at:function_end].splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if "if (compareExchange(" in line
    ]
    if len(starts) != 1:
        return None
    start = starts[0]
    for end in range(start, len(lines)):
        if ")) {" in lines[end]:
            return lines[start:end + 1]
    return None


def _check_stock_verbatim(
    transaction: _PatchFile | None, stock_sources: Mapping[str, str]
) -> ContractFailure | None:
    stock = stock_sources.get(SOURCE_FILES[0])
    if not isinstance(stock, str):
        return ContractFailure(STOCK_VERBATIM, "pinned transaction source is missing")
    stock_lines = _stock_cas_lines(stock)
    block = _cas_block(transaction)
    if stock_lines is None or block is None:
        return ContractFailure(STOCK_VERBATIM, "stock or patch CAS branch is ambiguous")
    _, off = block
    if off != stock_lines:
        return ContractFailure(
            STOCK_VERBATIM, "#else branch is not byte-for-byte pinned stock"
        )
    return None


def _check_identity_symbol(transaction: _PatchFile | None) -> ContractFailure | None:
    lines = _all_added(transaction)
    text = "\n".join(lines)
    details: list[str] = []
    if text.count(IDENTITY_SYMBOL) != 1:
        details.append("identity symbol definition count is not one")
    stripped = [line.strip() for line in lines]
    declaration = (
        'extern "C" {',
        '__attribute__((used, visibility("default")))',
        f"volatile unsigned char {IDENTITY_SYMBOL} = 1;",
        "}",
    )
    declaration_count = sum(
        tuple(stripped[index:index + len(declaration)]) == declaration
        for index in range(len(stripped) - len(declaration) + 1)
    )
    if declaration_count != 1:
        details.append("identity declaration does not match the visibility contract")
    guarded_blocks = _blocks(transaction, RUNG_MACRO)
    definitions_in_guard = sum(
        IDENTITY_SYMBOL in "\n".join(on)
        for on, _ in guarded_blocks
    )
    if definitions_in_guard != 1:
        details.append("identity definition is not uniquely RUNG1-gated")
    return _failure(IDENTITY_SYMBOL_REASON, details)


def _check_declared_files_only(
    patch: Sequence[_PatchFile],
) -> ContractFailure | None:
    declared = [(item.old_path, item.new_path) for item in patch]
    expected = [(path, path) for path in SOURCE_FILES]
    if declared != expected:
        return ContractFailure(
            DECLARED_FILES_ONLY,
            f"declared files mismatch: actual={declared!r} expected={expected!r}",
        )
    return None


_TOP_KEYS = frozenset({"schema_version", "scope", "entries"})
_ENTRY_KEYS = frozenset({
    "id",
    "path",
    "patch_sha256",
    "base_repo",
    "base_commit",
    "classification",
    "evaluation_role",
    "ability_probe",
    "research_goal_eligible",
    "recovery_measurement_eligibility",
    "pipeline_eligible",
    "composition",
    "default_enabled",
    "stock_source_policy",
    "macro",
    "report_macro",
    "symbols",
    "driver",
    "pbs_job",
    "source_files",
    "evidence",
    "projection_policy",
})
_SYMBOL_KEYS = frozenset({"name", "kind", "defined_count"})
_PROJECTION_KEYS = frozenset({
    "planner_coder_eligible",
    "excluded_paths",
    "excluded_tokens",
})


def _exact_keys(value: Any, expected: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _strict_equal(actual: Any, expected: Any) -> bool:
    return type(actual) is type(expected) and actual == expected


def _check_ledger_consistency(
    patch_text: str, patch: Sequence[_PatchFile], ledger_text: str | None
) -> ContractFailure | None:
    details: list[str] = []
    if ledger_text is None:
        return ContractFailure(LEDGER_CONSISTENCY, "ledger input is missing")
    try:
        ledger = json.loads(ledger_text)
    except (json.JSONDecodeError, TypeError) as exc:
        return ContractFailure(LEDGER_CONSISTENCY, f"ledger JSON is invalid: {exc}")

    if not _exact_keys(ledger, _TOP_KEYS):
        details.append("top-level schema is not closed")
        return _failure(LEDGER_CONSISTENCY, details)
    if ledger["schema_version"] != "izanagi-patch-ledger/v1":
        details.append("schema_version mismatch")
    if ledger["scope"] != "registered-entries-only":
        details.append("scope mismatch")
    entries = ledger["entries"]
    if not isinstance(entries, list) or not entries:
        details.append("entries must be a non-empty array")
        return _failure(LEDGER_CONSISTENCY, details)
    if len(entries) != 1:
        details.append("initial ledger must contain exactly one entry")
    if not all(_exact_keys(item, _ENTRY_KEYS) for item in entries):
        details.append("entry schema is not closed")
        return _failure(LEDGER_CONSISTENCY, details)
    entry = entries[0]
    for candidate in entries:
        candidate_symbols = candidate["symbols"]
        if (
            not isinstance(candidate_symbols, list)
            or len(candidate_symbols) != 1
            or not _exact_keys(candidate_symbols[0], _SYMBOL_KEYS)
        ):
            details.append("symbols schema is not closed")
            return _failure(LEDGER_CONSISTENCY, details)
        if not _exact_keys(candidate["projection_policy"], _PROJECTION_KEYS):
            details.append("projection_policy schema is not closed")
            return _failure(LEDGER_CONSISTENCY, details)
    symbols = entry["symbols"]
    projection = entry["projection_policy"]

    expected_scalars = {
        "id": "silo_ladder_rung1",
        "path": PATCH_PATH,
        "patch_sha256": hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
        "base_repo": "external/ccbench",
        "base_commit": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
        "classification": "d18-type4",
        "evaluation_role": "ability_probe",
        "ability_probe": True,
        "research_goal_eligible": False,
        "recovery_measurement_eligibility": False,
        "pipeline_eligible": False,
        "composition": "dedicated-driver-only",
        "default_enabled": False,
        "stock_source_policy": "patch-not-applied",
        "macro": RUNG_MACRO,
        "report_macro": REPORT_MACRO,
        "driver": "orchestrator/campaign/silo_ladder_rung1.py",
        "pbs_job": "tools/pegasus/silo_ladder_rung1.sh",
        "evidence": (
            "output/env/pegasus/silo_ladder_rung1/"
            "silo_ladder_rung1.json"
        ),
    }
    for key, expected in expected_scalars.items():
        if not _strict_equal(entry[key], expected):
            details.append(f"{key} mismatch")

    declared_paths = [item.new_path for item in patch]
    if entry["source_files"] != declared_paths or declared_paths != list(SOURCE_FILES):
        details.append("source_files do not match patch declarations")

    symbol = symbols[0]
    expected_symbol = {
        "name": IDENTITY_SYMBOL,
        "kind": "activation-identity",
        "defined_count": 1,
    }
    if symbol != expected_symbol:
        details.append("identity symbol ledger binding mismatch")
    patch_added_text = "\n".join(
        line
        for patch_file in patch
        for line in _all_added(patch_file)
    )
    patch_macros = set(
        re.findall(r"\b(?:IZANAGI|CCBENCH)_[A-Z0-9_]+\b", patch_added_text)
    )
    if not isinstance(entry["macro"], str) or entry["macro"] not in patch_macros:
        details.append("macro is not present in patch additions")
    if (
        not isinstance(entry["report_macro"], str)
        or entry["report_macro"] not in patch_macros
    ):
        details.append("report_macro is not present in patch additions")
    if (
        not isinstance(symbol["name"], str)
        or type(symbol["defined_count"]) is not int
        or patch_added_text.count(symbol["name"]) != symbol["defined_count"]
    ):
        details.append("symbol defined_count does not match patch additions")

    required_excluded_paths = {
        "patches/ledger.json",
        PATCH_PATH,
        expected_scalars["driver"],
        expected_scalars["pbs_job"],
        "tools/pegasus/submit_silo_ladder_rung1.sh",
        "output/env/pegasus/silo_ladder_rung1",
    }
    excluded_paths = projection["excluded_paths"]
    if (
        not isinstance(excluded_paths, list)
        or not all(isinstance(item, str) for item in excluded_paths)
        or len(excluded_paths) != len(set(excluded_paths))
        or set(excluded_paths) != required_excluded_paths
    ):
        details.append("projection excluded_paths mismatch")
    required_tokens = {
        "silo_ladder_rung1",
        RUNG_MACRO,
        REPORT_MACRO,
        IDENTITY_SYMBOL,
    }
    excluded_tokens = projection["excluded_tokens"]
    if (
        not isinstance(excluded_tokens, list)
        or not all(isinstance(item, str) for item in excluded_tokens)
        or len(excluded_tokens) != len(set(excluded_tokens))
        or set(excluded_tokens) != required_tokens
    ):
        details.append("projection excluded_tokens mismatch")
    if projection["planner_coder_eligible"] is not False:
        details.append("planner_coder_eligible must be false")

    ids = [item.get("id") for item in entries if isinstance(item, dict)]
    macros = [item.get("macro") for item in entries if isinstance(item, dict)]
    symbol_names = [
        item.get("name")
        for ledger_entry in entries
        if isinstance(ledger_entry, dict)
        for item in ledger_entry.get("symbols", [])
        if isinstance(item, dict)
    ]
    if not all(isinstance(item, str) for item in ids):
        details.append("entry ids are not strings")
    elif len(ids) != len(set(ids)):
        details.append("entry ids are not unique")
    if not all(isinstance(item, str) for item in macros):
        details.append("entry macros are not strings")
    elif len(macros) != len(set(macros)):
        details.append("entry macros are not unique")
    if not all(isinstance(item, str) for item in symbol_names):
        details.append("symbol names are not strings")
    elif len(symbol_names) != len(set(symbol_names)):
        details.append("symbol names are not unique")
    return _failure(LEDGER_CONSISTENCY, details)


def validate(
    patch_text: str,
    stock_sources: Mapping[str, str],
    ledger_text: str | None = None,
) -> tuple[ContractFailure, ...]:
    """全静的契約を独立評価し、赤理由だけを固定順で返す。"""
    patch_failures = validate_patch(patch_text, stock_sources)
    ledger_failure = validate_ledger(patch_text, ledger_text)
    return patch_failures + (() if ledger_failure is None else (ledger_failure,))


def validate_patch(
    patch_text: str,
    stock_sources: Mapping[str, str],
) -> tuple[ContractFailure, ...]:
    """patch 単体の七契約を独立評価する。"""
    patch = _parse_patch(patch_text)
    transaction = _file(patch, SOURCE_FILES[0])
    failures = (
        _check_non_thread_local(transaction),
        _check_guard_lifetime(transaction),
        _check_single_cas_no_bypass(transaction),
        _check_macro_discipline(patch),
        _check_stock_verbatim(transaction, stock_sources),
        _check_identity_symbol(transaction),
        _check_declared_files_only(patch),
    )
    return tuple(failure for failure in failures if failure is not None)


def validate_ledger(
    patch_text: str,
    ledger_text: str | None,
) -> ContractFailure | None:
    """ledger closed schema と patch 現物束縛を検査する。"""
    patch = _parse_patch(patch_text)
    return _check_ledger_consistency(patch_text, patch, ledger_text)
