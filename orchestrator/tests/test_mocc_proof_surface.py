# -*- coding: utf-8 -*-
"""MOCC lock/permutation proof-surface contract and verifier controls."""
from __future__ import annotations

import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest import mock

from orchestrator.campaign import condition_meaning_gate
from orchestrator.verifier import result_to_dict, verify_trace_dir
from orchestrator.verifier.model import (
    assess_compiled_protocol_source_snapshot,
    capture_compiled_protocol_source_snapshot,
)


_ROOT = Path(__file__).resolve().parents[2]
_CCBENCH = _ROOT / "external" / "ccbench"
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_E9 = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
_PIN = "511c9538"
_MISSING_OID = "0" * 40
_INSTRUMENTATION = _ROOT / "patches" / "instr-mocc-lock-coverage.patch"
_LOCKSKIP = _ROOT / "patches" / "broken-mocc-lockskip-validation.patch"
_PERMUTATION = _ROOT / "patches" / "broken-mocc-permutation-erase.patch"
_EARLY_UNLOCK = _ROOT / "patches" / "broken-mocc-early-unlock.patch"
_MATERIALIZED_PATHS = (
    "cc/mocc/CMakeLists.txt",
    "cc/mocc/transaction.cc",
    "cc/mocc/util.cc",
    "cc/mocc/lock.cc",
)
_CHECK_KEYS = (
    "stock_single_certified_and_silent",
    "stock_single_non_insert_writes_positive",
    "stock_high_xp_silent",
    "stock_high_non_insert_writes_positive",
    "lockskip_single_cycles_zero_x_positive",
    "lockskip_single_both_entry_and_retention_reasons",
    "lockskip_high_x_positive",
    "perm_single_only_size_changed",
    "early_unlock_single_retention_reasons_without_entry",
    "trace0_nm_izanagi_zero",
    "trace0_strings_izanagi_trace_zero",
    "trace0_text_identical",
    "all_patch_touch_sets_are_transaction_only",
    "toolchain_matches_policy",
)
_PATCH_PATHS = {
    "patches/instr-mocc-lock-coverage.patch",
    "patches/broken-mocc-lockskip-validation.patch",
    "patches/broken-mocc-permutation-erase.patch",
    "patches/broken-mocc-early-unlock.patch",
}


def _materialize(oid: str, root: Path) -> Path:
    """Materialize only the MOCC compiled-source closure from one git object."""
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for relative in _MATERIALIZED_PATHS:
        rendered = subprocess.run(
            ["git", "-C", str(_CCBENCH), "show", f"{oid}:{relative}"],
            check=True,
            capture_output=True,
        ).stdout
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(rendered)
    return root


def _check_patch(root: Path, patch: Path) -> None:
    subprocess.run(
        ["git", "-C", str(root), "apply", "--check", str(patch)],
        check=True,
        capture_output=True,
    )


def _apply_patch(root: Path, patch: Path) -> None:
    _check_patch(root, patch)
    subprocess.run(
        ["git", "-C", str(root), "apply", str(patch)],
        check=True,
        capture_output=True,
    )


@contextmanager
def _source_root(*patches: Path, oid: str = _E9):
    with tempfile.TemporaryDirectory(prefix="mocc-proof-surface-") as raw:
        root = _materialize(oid, Path(raw) / "ccbench")
        for patch in patches:
            _apply_patch(root, patch)
        yield root


def _source(root: Path) -> str:
    return (root / "cc" / "mocc" / "transaction.cc").read_text(
        encoding="utf-8",
    )


def _assessment(root: Path) -> dict[str, str | None]:
    snapshot = capture_compiled_protocol_source_snapshot("mocc", root)
    return assess_compiled_protocol_source_snapshot(snapshot).as_record()


def _strip_includes(source: str) -> str:
    # Keep each newline: #line values are defined against the original physical
    # layout, and deleting the whole line would make this witness self-disturbing.
    return re.sub(r"(?m)^[ \t]*#[ \t]*include\b.*$", "", source)


def _preprocess_trace_zero(source: str) -> bytes:
    cxx = shutil.which("g++")
    if cxx is None:
        raise AssertionError("g++ is required for the fail-closed TRACE=0 witness")
    command = [
        cxx,
        "-E",
        "-nostdinc",
        "-Werror=undef",
        "-DTRACE=0",
        "-DRWLOCK",
        "-DADD_ANALYSIS=0",
        "-DBACK_OFF=0",
        "-DKEY_SORT=0",
        "-DTEMPERATURE_RESET_OPT=1",
        "-DMASSTREE_USE=1",
        "-DLinux",
        "-DKEY_SIZE=8",
        "-DVAL_SIZE=4",
        "-x",
        "c++",
        "-",
    ]
    return subprocess.run(
        command,
        input=_strip_includes(source).encode("utf-8"),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


_CPP_MARKER = re.compile(
    rb'^#\s+([0-9]+)\s+"[^"\r\n]+"(?:\s+[0-9]+)*\s*$'
)
_DIRECTIVE_OPEN = re.compile(r"#\s*(?:if|ifdef|ifndef)\b")
_DIRECTIVE_CLOSE = re.compile(r"#\s*endif\b")


def _logical_nonempty_rows(
    preprocessed: bytes,
) -> tuple[tuple[int, bytes], ...]:
    logical: int | None = None
    rows: list[tuple[int, bytes]] = []
    for raw in preprocessed.splitlines():
        marker = _CPP_MARKER.fullmatch(raw)
        if marker is not None:
            logical = int(marker.group(1))
            continue
        if logical is None:
            if raw.strip():
                raise AssertionError("body appeared before a line marker")
            continue
        if raw.strip():
            rows.append((logical, raw))
        logical += 1
    return tuple(rows)


def _strip_comments(source: str) -> str:
    without_blocks = re.sub(
        r"/\*.*?\*/",
        lambda match: "\n" * match.group(0).count("\n"),
        source,
        flags=re.DOTALL,
    )
    return re.sub(r"//[^\r\n]*", "", without_blocks)


def _directive_end(lines: list[str], start: int) -> int:
    depth = 0
    for index in range(start, len(lines)):
        line = lines[index].strip()
        if _DIRECTIVE_OPEN.match(line):
            depth += 1
        elif _DIRECTIVE_CLOSE.match(line):
            depth -= 1
            if depth == 0:
                return index
    raise AssertionError(f"unterminated conditional directive at line {start + 1}")


def _directive_block(source: str, directive: str) -> str:
    lines = source.splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if line.strip() == directive
    ]
    assert len(starts) == 1, (directive, len(starts))
    start = starts[0]
    return "\n".join(lines[start:_directive_end(lines, start) + 1])


def _trace_blocks(source: str) -> tuple[str, ...]:
    lines = source.splitlines()
    return tuple(
        "\n".join(lines[start:_directive_end(lines, start) + 1])
        for start, line in enumerate(lines)
        if line.strip() == "#if TRACE"
    )


def _trace_block_containing(source: str, needle: str) -> str:
    matches = [block for block in _trace_blocks(source) if needle in block]
    assert len(matches) == 1, (needle, len(matches))
    return matches[0]


def _following_nonempty_lines(source: str, block: str) -> list[str]:
    block_at = source.index(block)
    tail = source[block_at + len(block):]
    return [line.strip() for line in tail.splitlines() if line.strip()]


def _following_text(source: str, block: str) -> str:
    block_at = source.index(block)
    return source[block_at + len(block):]


def _normalized_whitespace(source: str) -> str:
    return re.sub(r"\s+", " ", source).strip()


def _assert_lock_violation_block(
    block: str, condition: str, emitter: str,
) -> None:
    normalized = _normalized_whitespace(block)
    expected_statement = _normalized_whitespace(
        f"{condition}\n{emitter}"
    )
    assert expected_statement in normalized


def _assert_instr_x_p_structure(source: str) -> None:
    source = _strip_comments(source)
    write_blocks = [
        block for block in _trace_blocks(source)
        if '"lock-lost-before-write"' in block
    ]
    assert len(write_blocks) == 2

    update_start = source.index("case OpType::UPDATE:")
    update_end = source.index("case OpType::INSERT:", update_start)
    update_case = source[update_start:update_end]
    update_block = _trace_block_containing(
        update_case, '"lock-lost-before-write"',
    )
    write_condition = (
        "if ((*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED)"
    )
    write_emitter = (
        "izanagi_trace::emit_lock_violation( "
        "thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_), "
        '"lock-lost-before-write");'
    )
    _assert_lock_violation_block(
        update_block, write_condition, write_emitter,
    )
    assert _following_text(update_case, update_block).startswith(
        "\n#line 1169\n"
    )
    update_following = _following_nonempty_lines(update_case, update_block)
    assert update_following[0] == "#line 1169"
    assert update_following[1].startswith("memcpy(")

    delete_start = source.index("case OpType::DELETE:", update_end)
    delete_end = source.index("default:", delete_start)
    delete_case = source[delete_start:delete_end]
    delete_block = _trace_block_containing(
        delete_case, '"lock-lost-before-write"',
    )
    _assert_lock_violation_block(
        delete_block, write_condition, write_emitter,
    )
    assert _following_text(delete_case, delete_block).startswith(
        "\n#line 1187\n"
    )
    delete_following = _following_nonempty_lines(delete_case, delete_block)
    assert delete_following[0] == "#line 1187"
    assert delete_following[1].rsplit(".", 1)[-1].startswith(
        "remove_value_if_present("
    )

    publish_block = _trace_block_containing(
        source, '"lock-lost-before-publish"',
    )
    publish_condition = (
        "if ((*itr).op_ != OpType::INSERT && "
        "(*itr).rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED)"
    )
    publish_emitter = (
        "izanagi_trace::emit_lock_violation( "
        "thid_, izanagi_txid, izanagi_trace::key_to_hex((*itr).key_), "
        '"lock-lost-before-publish");'
    )
    _assert_lock_violation_block(
        publish_block, publish_condition, publish_emitter,
    )
    assert _following_text(source, publish_block).startswith(
        "\n#line 1195\n"
    )
    publish_following = _following_nonempty_lines(source, publish_block)
    assert publish_following[0] == "#line 1195"
    assert publish_following[1].startswith("__atomic_store_n(")

    pre_sort_block = _trace_block_containing(
        source, "const std::size_t izanagi_pre_sort_size",
    )
    assert (
        "const std::size_t izanagi_pre_sort_size = write_set_.size();"
        in _normalized_whitespace(pre_sort_block)
    )
    assert _following_text(source, pre_sort_block).startswith(
        "\n#line 990\n"
    )
    pre_sort_following = _following_nonempty_lines(source, pre_sort_block)
    assert pre_sort_following[0] == "#line 990"
    assert pre_sort_following[1] == "sort(write_set_.begin(), write_set_.end());"
    sort_at = source.index(pre_sort_following[1])
    post_sort_block = _trace_block_containing(
        source,
        r'''izanagi_trace::stream(thid_) << "P " << izanagi_perm_reason << '\n';''',
    )
    between_sort_and_post = source[
        sort_at + len(pre_sort_following[1]):source.index(post_sort_block)
    ]
    assert not between_sort_and_post.strip()
    normalized_post = _normalized_whitespace(post_sort_block)
    assert (
        "bool izanagi_perm_ok = "
        "(write_set_.size() == izanagi_pre_sort_size);"
        in normalized_post
    )
    assert (
        "if (izanagi_post_sort_rcdptrs != izanagi_pre_sort_rcdptrs) {"
        in normalized_post
    )
    permutation_emitter = _normalized_whitespace(
        r'''if (!izanagi_perm_ok) {
          izanagi_trace::stream(thid_) << "P " << izanagi_perm_reason << '\n';
        }'''
    )
    assert permutation_emitter in normalized_post
    assert '"size-changed"' in post_sort_block
    assert '"rcdptr-set-changed"' in post_sort_block


def _assert_instr_source_contract(source: str) -> None:
    source = _strip_comments(source)
    entry_block = _trace_block_containing(source, '"not-locked-at-entry"')
    normalized = _normalized_whitespace(entry_block)
    predicate = (
        "if (lock_element.key_ == we.rcdptr_ && lock_element.mode_ && "
        "lock_element.lock_ == &we.rcdptr_->rwlock_)"
    )
    assert predicate in normalized
    assert "if (we.op_ == OpType::INSERT) continue;" in normalized
    assert "bool izanagi_cll_has_writer = false;" in normalized
    entry_condition = (
        "if (!izanagi_cll_has_writer || "
        "we.rcdptr_->rwlock_.ldAcqCounter() != W_LOCKED) {"
    )
    entry_emitter = (
        "izanagi_trace::emit_lock_violation( "
        "thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_), "
        '"not-locked-at-entry");'
    )
    _assert_lock_violation_block(
        entry_block, entry_condition, entry_emitter,
    )
    assert _following_text(source, entry_block).startswith("\n#line 1158\n")
    assert _following_nonempty_lines(source, entry_block)[0] == "#line 1158"


def test_instr_patch_applies_to_e9e477ca_and_rejects_511c9538():
    with _source_root(_INSTRUMENTATION):
        pass
    with tempfile.TemporaryDirectory(prefix="mocc-proof-pin-") as raw:
        pin_root = _materialize(_PIN, Path(raw) / "ccbench")
        try:
            _check_patch(pin_root, _INSTRUMENTATION)
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("instrumentation patch unexpectedly applies to 511c9538")


def test_mocc_x_p_proof_surfaces_are_present_only_after_instr_patch():
    expected_absent = {
        "protocol": "mocc",
        "X": "evidence-absent",
        "P": "evidence-absent",
        "I": "evidence-absent",
    }
    expected_patched = {
        "protocol": "mocc",
        "X": "evidence-present",
        "P": "evidence-present",
        "I": "evidence-absent",
    }
    with _source_root() as unpatched:
        assert _assessment(unpatched) == expected_absent
    with _source_root(_INSTRUMENTATION) as patched:
        assert _assessment(patched) == expected_patched
        _assert_instr_x_p_structure(_source(patched))


def test_instr_patch_names_cll_lock_pointer_predicate():
    with _source_root(_INSTRUMENTATION) as root:
        _assert_instr_source_contract(_source(root))


def test_instr_patch_keeps_trace0_preprocess_identical():
    with _source_root() as unpatched:
        before = _preprocess_trace_zero(_source(unpatched))
    with _source_root(_INSTRUMENTATION) as patched:
        after = _preprocess_trace_zero(_source(patched))
    before_rows = _logical_nonempty_rows(before)
    after_rows = _logical_nonempty_rows(after)
    if after_rows != before_rows:
        for index in range(max(len(before_rows), len(after_rows))):
            before_row = before_rows[index] if index < len(before_rows) else None
            after_row = after_rows[index] if index < len(after_rows) else None
            if before_row != after_row:
                raise AssertionError(
                    "TRACE=0 logical preprocessor rows differ: "
                    f"index={index} before={before_row!r} after={after_row!r}"
                )
        raise AssertionError("TRACE=0 logical preprocessor row lengths differ")


def test_broken_mocc_lockskip_patch_guards_validation_lock():
    with _source_root(_INSTRUMENTATION, _LOCKSKIP) as root:
        source = _strip_comments(_source(root))
    block = _directive_block(
        source, "#if IZANAGI_BREAK_MOCC_LOCK_COVERAGE",
    )
    lines = [line.strip() for line in block.splitlines()]
    alternate = lines.index("#else")
    assert [line for line in lines[1:alternate] if line] == []
    assert [line for line in lines[alternate + 1:-1] if line] == [
        "lock((*itr).rcdptr_, true);",
    ]
    block_at = source.index(block)
    preceding = [
        line.strip() for line in source[:block_at].splitlines()
        if line.strip()
    ]
    assert preceding[-1] == "if (itr->op_ == OpType::INSERT) continue;"
    following = _following_nonempty_lines(source, block)
    assert following[:2] == [
        "#line 994",
        "if (this->status_ == TransactionStatus::aborted ||",
    ]


def test_broken_mocc_permutation_patch_pops_between_sort_and_trace_check():
    with _source_root(_INSTRUMENTATION, _PERMUTATION) as root:
        source = _strip_comments(_source(root))
    directive = "#if IZANAGI_BREAK_MOCC_PERMUTATION"
    block = _directive_block(source, directive)
    inner = [line.strip() for line in block.splitlines()[1:-1] if line.strip()]
    assert inner == ["if (!write_set_.empty()) write_set_.pop_back();"]
    sort_at = source.index("sort(write_set_.begin(), write_set_.end());")
    sort_end = sort_at + len("sort(write_set_.begin(), write_set_.end());")
    block_at = source.index(block)
    assert not source[sort_end:block_at].strip()
    following = _following_nonempty_lines(source, block)
    assert following[:2] == ["#line 991", "#if TRACE"]
    assert _following_text(source, block).startswith("\n#line 991\n#if TRACE\n")
    post_sort_block = _trace_block_containing(source, "izanagi_perm_ok")
    assert source.index(post_sort_block) == source.index("#if TRACE", block_at)


def test_broken_mocc_early_unlock_patch_unlocks_after_entry_and_relocks_before_publish():
    with _source_root(_INSTRUMENTATION, _EARLY_UNLOCK) as root:
        source = _strip_comments(_source(root))
    directive = "#if IZANAGI_BREAK_MOCC_EARLY_UNLOCK"
    constexpr_block = _directive_block(source, directive)
    constexpr_lines = [
        line.strip() for line in constexpr_block.splitlines() if line.strip()
    ]
    assert constexpr_lines == [
        directive,
        "static constexpr bool izanagi_break_mocc_early_unlock = true;",
        "#else",
        "static constexpr bool izanagi_break_mocc_early_unlock = false;",
        "#endif",
    ]
    constexpr_at = source.index(constexpr_block)
    assert source[:constexpr_at].rstrip().endswith("#line 17")
    assert _following_text(source, constexpr_block).startswith("\n#line 17\n")
    assert _following_nonempty_lines(source, constexpr_block)[0] == "#line 17"
    constexpr_use = "if constexpr (izanagi_break_mocc_early_unlock) {"
    assert source.count(constexpr_use) == 2

    entry_block = _trace_block_containing(source, '"not-locked-at-entry"')
    after_entry = source[source.index(entry_block) + len(entry_block):]
    assert after_entry.startswith("\n#line 1158\n")
    first_entry_line = after_entry.index("#line 1158")
    second_entry_line = after_entry.index(
        "#line 1158", first_entry_line + len("#line 1158"),
    )
    site_one = after_entry[
        first_entry_line + len("#line 1158"):second_entry_line
    ]
    assert [line.strip() for line in site_one.splitlines() if line.strip()] == [
        constexpr_use,
        "for (auto& we : write_set_) {",
        "if (we.op_ != OpType::INSERT) we.rcdptr_->rwlock_.w_unlock();",
        "}",
        "}",
    ]

    publish_block = _trace_block_containing(
        source, '"lock-lost-before-publish"',
    )
    after_publish = source[source.index(publish_block) + len(publish_block):]
    assert after_publish.startswith("\n#line 1195\n")
    first_publish_line = after_publish.index("#line 1195")
    second_publish_line = after_publish.index(
        "#line 1195", first_publish_line + len("#line 1195"),
    )
    site_two = after_publish[
        first_publish_line + len("#line 1195"):second_publish_line
    ]
    assert [line.strip() for line in site_two.splitlines() if line.strip()] == [
        constexpr_use,
        "if ((*itr).op_ != OpType::INSERT) (*itr).rcdptr_->rwlock_.w_lock();",
        "}",
    ]
    after_site_two = after_publish[
        second_publish_line + len("#line 1195"):
    ]
    assert next(
        line.strip() for line in after_site_two.splitlines() if line.strip()
    ).startswith("__atomic_store_n(")


def test_broken_mocc_patches_have_unique_production_condition_witnesses():
    cases = (
        ("IZANAGI_BREAK_MOCC_LOCK_COVERAGE", _LOCKSKIP),
        ("IZANAGI_BREAK_MOCC_PERMUTATION", _PERMUTATION),
        ("IZANAGI_BREAK_MOCC_EARLY_UNLOCK", _EARLY_UNLOCK),
    )
    for macro, patch in cases:
        owner, directive = condition_meaning_gate.CONDITIONAL_BRANCH_WITNESSES[
            macro
        ]
        assert owner == "cc/mocc/transaction.cc"
        declaration = condition_meaning_gate.ConditionalBranchMeaningDeclaration(
            macro=macro,
            source_rel=owner,
            start_directive=directive,
        )
        with _source_root(_INSTRUMENTATION, patch) as root:
            source = (root / owner).read_text(encoding="utf-8")
        instrumented = condition_meaning_gate._instrument_declared_owner_source(
            source, declaration,
        )
        assert instrumented != source
        duplicated = source + "\n" + directive + "\n"
        try:
            condition_meaning_gate._instrument_declared_owner_source(
                duplicated, declaration,
            )
        except condition_meaning_gate.ConditionMeaningGateError as exc:
            assert exc.reason_code == "compile-time-branch-start-not-unique"
        else:
            raise AssertionError(f"duplicate condition witness was accepted: {macro}")


def _verified_fixture(name: str, ccbench_root: Path):
    return verify_trace_dir(
        str(_FIXTURES / name),
        protocol="mocc",
        ccbench_root=ccbench_root,
    )


def test_mocc_x_fixture_routes_to_lock_coverage_indeterminate():
    with _source_root(_INSTRUMENTATION) as root:
        result = _verified_fixture("m3_mocc_lock_coverage", root)
    assert result.integrity.lock_coverage_violations == 1
    assert result.integrity.permutation_violations == 0
    assert result.total_cycles == 0
    assert result.verdict == "indeterminate"
    assert not result.certified


def test_mocc_p_fixture_routes_to_permutation_indeterminate():
    with _source_root(_INSTRUMENTATION) as root:
        result = _verified_fixture("m4_mocc_permutation", root)
    assert result.integrity.lock_coverage_violations == 0
    assert result.integrity.permutation_violations == 1
    details = result_to_dict(result)["integrity"]["permutation_violation_details"]
    assert details["counts"] == {
        "size-changed": 1,
        "rcdptr-set-changed": 0,
        "unknown": 0,
    }
    assert result.total_cycles == 0
    assert result.verdict == "indeterminate"
    assert not result.certified


def test_mocc_clean_fixture_is_certified_with_patched_snapshot():
    with tempfile.TemporaryDirectory(prefix="mocc-proof-clean-") as raw:
        parent = Path(raw)
        unpatched = _materialize(_E9, parent / "unpatched")
        patched = _materialize(_E9, parent / "patched")
        _apply_patch(patched, _INSTRUMENTATION)
        positive = _verified_fixture("g7_mocc_minimal_2thread", patched)
        negative = _verified_fixture("g7_mocc_minimal_2thread", unpatched)
    assert positive.integrity.lock_coverage_violations == 0
    assert positive.integrity.permutation_violations == 0
    assert positive.total_cycles == 0
    assert positive.verdict == "serializable"
    assert positive.certified
    assert negative.verdict == "indeterminate"
    assert not negative.certified


def test_e9e477ca_materialization_fails_closed_when_object_is_missing():
    with tempfile.TemporaryDirectory(prefix="mocc-proof-missing-") as raw:
        try:
            _materialize(_MISSING_OID, Path(raw) / "ccbench")
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("missing git object was not rejected")


def test_driver_check_keys_are_exact():
    from orchestrator.campaign import s3_mocc_lock_coverage

    assert type(s3_mocc_lock_coverage.CHECK_KEYS) is tuple
    assert s3_mocc_lock_coverage.CHECK_KEYS == _CHECK_KEYS


def test_driver_trace0_build_directory_names_are_equal_length():
    from orchestrator.campaign import s3_mocc_lock_coverage

    source = Path(s3_mocc_lock_coverage.__file__).read_text(encoding="utf-8")
    base_name = "trace0-base"
    instrumented_name = "trace0-inst"
    assert len(base_name) == len(instrumented_name)
    assert source.count(f'scratch / "{base_name}"') == 1
    assert source.count(f'scratch / "{instrumented_name}"') == 1
    assert "__FILE__ path drift in .text" in source
    assert "base-trace0" not in source
    assert "patched-trace0" not in source


def test_driver_verify_passes_mocc_protocol_and_given_root():
    from orchestrator.campaign import s3_mocc_lock_coverage

    calls: list[tuple[list[str], dict[str, object]]] = []

    def recording_run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        payload = {
            "results": [{
                "verdict": "serializable",
                "certified": True,
                "total_cycles": 0,
                "integrity": {
                    "lock_coverage_violations": 0,
                    "permutation_violations": 0,
                },
                "stats": {"txns": 1, "reads": 0, "writes": 1},
            }],
        }
        return subprocess.CompletedProcess(
            argv, 0, stdout=json.dumps(payload), stderr="",
        )

    with tempfile.TemporaryDirectory(prefix="mocc-driver-root-") as raw:
        given_root = str(Path(raw) / "given-ccbench")
        with mock.patch.object(
            s3_mocc_lock_coverage.subprocess,
            "run",
            side_effect=recording_run,
        ):
            s3_mocc_lock_coverage._verify("/trace/input", given_root)
    assert len(calls) == 1
    argv, _kwargs = calls[0]
    protocol_at = argv.index("--protocol")
    root_at = argv.index("--ccbench-root")
    assert argv[protocol_at + 1] == "mocc"
    assert argv[root_at + 1] == given_root
    assert str(_CCBENCH) not in argv


def test_driver_resolve_toolchain_accepts_bound_versions_and_fails_closed():
    from orchestrator.campaign import s3_mocc_lock_coverage

    version_body = " synthetic-version-body"
    matching_digest = hashlib.sha256(version_body.encode("utf-8")).hexdigest()
    policy = {
        "expected_compiler_version_body_sha256": {
            "gcc": matching_digest,
            "g++": matching_digest,
        },
    }

    with tempfile.TemporaryDirectory(prefix="mocc-toolchain-") as raw:
        compiler_paths = {
            "gcc": Path(raw) / "gcc",
            "g++": Path(raw) / "g++",
        }
        for path in compiler_paths.values():
            path.touch()

        def fake_which(role):
            return str(compiler_paths[role])

        def version_run(argv, **_kwargs):
            role = Path(argv[0]).name
            return subprocess.CompletedProcess(
                argv, 0, stdout=f"{role}{version_body}\n", stderr="",
            )

        with mock.patch.object(
            s3_mocc_lock_coverage.shutil, "which", side_effect=fake_which,
        ), mock.patch.object(
            s3_mocc_lock_coverage, "_run_checked", side_effect=version_run,
        ):
            resolved = s3_mocc_lock_coverage._resolve_toolchain(policy)
        assert resolved == {
            "version_body_sha256": {
                "gcc": matching_digest,
                "g++": matching_digest,
            },
            "cc_path": str(compiler_paths["gcc"].resolve()),
            "cxx_path": str(compiler_paths["g++"].resolve()),
        }

        def mismatched_gxx_run(argv, **_kwargs):
            role = Path(argv[0]).name
            body = version_body if role == "gcc" else " mismatched-version-body"
            return subprocess.CompletedProcess(
                argv, 0, stdout=f"{role}{body}\n", stderr="",
            )

        with mock.patch.object(
            s3_mocc_lock_coverage.shutil, "which", side_effect=fake_which,
        ), mock.patch.object(
            s3_mocc_lock_coverage,
            "_run_checked",
            side_effect=mismatched_gxx_run,
        ):
            try:
                s3_mocc_lock_coverage._resolve_toolchain(policy)
            except RuntimeError as exc:
                assert str(exc).startswith("g++ version body mismatch:")
            else:
                raise AssertionError("mismatched g++ version body was accepted")

    with mock.patch.object(
        s3_mocc_lock_coverage.shutil, "which", return_value=None,
    ), mock.patch.object(
        s3_mocc_lock_coverage,
        "_run_checked",
        side_effect=AssertionError("version command must not run"),
    ) as run_checked:
        try:
            s3_mocc_lock_coverage._resolve_toolchain(policy)
        except RuntimeError as exc:
            assert str(exc) == "compiler is unavailable: gcc"
        else:
            raise AssertionError("missing compiler was accepted")
    assert not run_checked.called


def test_driver_compute_checks_is_input_derived_per_key():
    from orchestrator.campaign import s3_mocc_lock_coverage

    runs = {
        "stock_single": {
            "certified": True,
            "verdict": "serializable",
            "total_cycles": 0,
            "lock_coverage_violations": 0,
            "permutation_violations": 0,
            "txns": 1,
            "non_insert_writes": 1,
            "x_reasons": {},
            "p_reasons": {},
            "_other_integrity_clean": True,
        },
        "stock_high": {
            "lock_coverage_violations": 0,
            "permutation_violations": 0,
            "txns": 1,
            "non_insert_writes": 1,
            "_other_integrity_clean": True,
        },
        "lockskip_single": {
            "total_cycles": 0,
            "lock_coverage_violations": 3,
            "txns": 1,
            "verdict": "indeterminate",
            "x_reasons": {
                "not-locked-at-entry": 1,
                "lock-lost-before-write": 1,
                "lock-lost-before-publish": 1,
            },
        },
        "lockskip_high": {"lock_coverage_violations": 1},
        "perm_erase_single": {
            "total_cycles": 0,
            "lock_coverage_violations": 0,
            "permutation_violations": 1,
            "p_reasons": {"size-changed": 1},
            "txns": 1,
            "verdict": "indeterminate",
        },
        "early_unlock_single": {
            "total_cycles": 0,
            "lock_coverage_violations": 2,
            "txns": 1,
            "verdict": "indeterminate",
            "x_reasons": {
                "not-locked-at-entry": 0,
                "lock-lost-before-write": 1,
                "lock-lost-before-publish": 1,
            },
        },
    }
    trace0 = {
        "nm_izanagi_count": 0,
        "strings_izanagi_trace_count": 0,
        "strings_izanagi_macro_count": 0,
        "text_identical": True,
    }
    patch_relatives = (
        s3_mocc_lock_coverage.INSTRUMENTATION_PATCH,
        s3_mocc_lock_coverage.LOCKSKIP_PATCH,
        s3_mocc_lock_coverage.PERMUTATION_PATCH,
        s3_mocc_lock_coverage.EARLY_UNLOCK_PATCH,
    )
    touch_sets = {
        relative: [s3_mocc_lock_coverage.SOURCE_REL]
        for relative in patch_relatives
    }
    digest = "1" * 64
    toolchain = {
        "version_body_sha256": {"gcc": digest, "g++": digest},
    }
    policy = {
        "expected_compiler_version_body_sha256": {
            "gcc": digest,
            "g++": digest,
        },
    }

    def compute(bundle):
        return s3_mocc_lock_coverage.compute_checks(
            bundle["runs"], bundle["trace0"], bundle["touch_sets"],
            bundle["patch_relatives"], bundle["toolchain"], bundle["policy"],
        )

    baseline = {
        "runs": runs,
        "trace0": trace0,
        "touch_sets": touch_sets,
        "patch_relatives": patch_relatives,
        "toolchain": toolchain,
        "policy": policy,
    }
    positive = compute(copy.deepcopy(baseline))
    assert tuple(positive) == _CHECK_KEYS
    assert all(value is True for value in positive.values())

    mutations = (
        ("stock_single_certified_and_silent", lambda data: data["runs"][
            "stock_single"
        ].__setitem__("certified", False)),
        ("stock_single_non_insert_writes_positive", lambda data: data[
            "runs"
        ]["stock_single"].__setitem__("non_insert_writes", 0)),
        ("stock_high_xp_silent", lambda data: data["runs"][
            "stock_high"
        ].__setitem__("_other_integrity_clean", False)),
        ("stock_high_non_insert_writes_positive", lambda data: data[
            "runs"
        ]["stock_high"].__setitem__("non_insert_writes", 0)),
        ("lockskip_single_cycles_zero_x_positive", lambda data: data[
            "runs"
        ]["lockskip_single"].__setitem__("total_cycles", 1)),
        ("lockskip_single_both_entry_and_retention_reasons", lambda data: data[
            "runs"
        ]["lockskip_single"]["x_reasons"].__setitem__(
            "lock-lost-before-write", 0,
        )),
        ("lockskip_high_x_positive", lambda data: data["runs"][
            "lockskip_high"
        ].__setitem__("lock_coverage_violations", 0)),
        ("perm_single_only_size_changed", lambda data: data["runs"][
            "perm_erase_single"
        ].__setitem__("p_reasons", {"rcdptr-set-changed": 1})),
        ("early_unlock_single_retention_reasons_without_entry", lambda data: data[
            "runs"
        ]["early_unlock_single"]["x_reasons"].__setitem__(
            "not-locked-at-entry", 1,
        )),
        ("trace0_nm_izanagi_zero", lambda data: data["trace0"].__setitem__(
            "nm_izanagi_count", 1,
        )),
        ("trace0_strings_izanagi_trace_zero", lambda data: data[
            "trace0"
        ].__setitem__("strings_izanagi_macro_count", 1)),
        ("trace0_text_identical", lambda data: data["trace0"].__setitem__(
            "text_identical", False,
        )),
        ("all_patch_touch_sets_are_transaction_only", lambda data: data[
            "touch_sets"
        ].pop(data["patch_relatives"][0])),
        ("toolchain_matches_policy", lambda data: data["toolchain"][
            "version_body_sha256"
        ].__setitem__("g++", "2" * 64)),
    )
    assert tuple(key for key, _mutate in mutations) == _CHECK_KEYS
    for expected_false, mutate in mutations:
        changed = copy.deepcopy(baseline)
        mutate(changed)
        checks = compute(changed)
        assert tuple(checks) == _CHECK_KEYS
        assert {
            key for key, value in checks.items() if value is False
        } == {expected_false}


def test_compute_positive_control_json_is_all_pass_and_bound():
    from orchestrator.campaign import s3_mocc_lock_coverage

    result_path = (
        _ROOT
        / "output"
        / "env"
        / "pegasus"
        / "calibration"
        / "s3_mocc_lock_coverage.json"
    )
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "s3-mocc-lock-coverage/v1"
    assert payload["ccbench_commit"] == _E9
    assert type(payload["patches"]) is dict
    recorded_paths: set[str] = set()
    for descriptor in payload["patches"].values():
        assert type(descriptor) is dict
        relative = descriptor["path"]
        assert type(relative) is str and not Path(relative).is_absolute()
        recorded_paths.add(relative)
        assert descriptor["sha256"] == hashlib.sha256(
            (_ROOT / relative).read_bytes(),
        ).hexdigest()
    assert recorded_paths == _PATCH_PATHS
    assert tuple(s3_mocc_lock_coverage.CHECK_KEYS) == _CHECK_KEYS
    assert set(payload["checks"]) == set(_CHECK_KEYS)
    assert all(value is True for value in payload["checks"].values())
    assert payload["all_pass"] is True


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001 - fail-closed plain harness
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
