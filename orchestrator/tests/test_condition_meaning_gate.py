# -*- coding: utf-8 -*-
"""Independent supply and compiler-evaluated meaning tests for T-2018."""
from __future__ import annotations

import hashlib
import os
import shutil
import struct
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from orchestrator.campaign import b10_backoff_shape_sweep as B10
from orchestrator.campaign import condition_meaning_gate as G
from orchestrator.campaign.evolve_block import extract_materialized_evolve_block


_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).parent / "fixtures" / "condition_meaning_gate"
_SUPPLIED = _FIXTURES / "supplied"
_F707 = _FIXTURES / "f707-missing-supply"
_IGNORED = _FIXTURES / "effectuation-ignored"
_PATCH = _ROOT / "patches" / "silo-backoff-fixed.patch"


def _any_cxx() -> str:
    for candidate in ("g++-13", "g++-12", "g++"):
        if shutil.which(candidate):
            return candidate
    pytest.skip("no supported C++ compiler is installed")


def _any_cmake() -> str:
    candidate = shutil.which("cmake")
    if candidate is None:
        pytest.skip("cmake is not installed")
    return candidate


def _bits(value: int | float) -> str:
    return struct.pack(">d", float(value)).hex()


def _case(value: int, expected: int | float | None = None) -> G.MeaningCase:
    bits = _bits(value if expected is None else expected)
    return G.MeaningCase(value, (bits, bits))


def _stock_branch_case() -> G.MeaningCase:
    return G.MeaningCase(-1, None, G.STOCK_ADAPTIVE_BRANCH)


def _request(
    value: int,
    *,
    default: int | None = -1,
    stock: bool = False,
) -> G.DefineRequest:
    return G.make_define_request(
        driver_id="test-condition-meaning-gate",
        macro="BACKOFF_FIXED",
        requested_value=value,
        default_value=default,
        stock_comparison=stock,
    )


def _declaration(*cases: G.MeaningCase) -> G.MeaningWitnessDeclaration:
    return G.MeaningWitnessDeclaration("BACKOFF_FIXED", tuple(cases))


def _copied_fixture(tmp_path: Path) -> Path:
    destination = tmp_path / "ccbench"
    shutil.copytree(_SUPPLIED, destination)
    return destination


def _replace_source(root: Path, old: str, new: str) -> None:
    source = root / G.SOURCE_REL
    text = source.read_text(encoding="utf-8")
    assert text.count(old) == 1
    source.write_text(text.replace(old, new), encoding="utf-8")


def _fixture_hole(root: Path) -> str:
    source = (root / G.SOURCE_REL).read_text(encoding="utf-8")
    return extract_materialized_evolve_block(source, G.MARKER_ID).hole


def _patch_target_source() -> str:
    """Independently reconstruct target-side hunk bytes for backoff.hh."""
    lines = _PATCH.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next(
        index for index, line in enumerate(lines)
        if line.startswith("diff --git a/include/backoff.hh b/include/backoff.hh")
    )
    target: list[str] = []
    in_hunk = False
    for line in lines[start + 1:]:
        if line.startswith("diff --git "):
            break
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk or line.startswith(("---", "+++")):
            continue
        if line.startswith(("+", " ")):
            target.append(line[1:])
    return "".join(target)


def test_backoff_fixed_five_matches_pointwise():
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    evidence = G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=_any_cxx())

    assert evidence.proof_kind == G.MEANING_PROOF_KIND
    assert "standalone-tu" in evidence.proof_kind
    assert "finite-pointwise-witness" in evidence.proof_kind
    assert "actual-target-tu" not in evidence.proof_kind
    assert "dynamic-reachability" not in evidence.proof_kind
    assert "exact-build-input" not in evidence.proof_kind
    assert evidence.driver_integration == "none"
    assert [(row.start, row.observed_bits) for row in evidence.observations] == [
        (1, _bits(5)), (2, _bits(5)),
    ]
    assert evidence.source_sha256 == hashlib.sha256(captured.source_bytes).hexdigest()
    assert evidence.compiler_path == evidence.compiler_argv[0]
    assert evidence.run_argv and evidence.compiler_version
    assert evidence.input_files == captured.input_files
    assert [entry.phase for entry in evidence.compiler_identities] == [
        "before-version", "after-version", "after-compile",
    ]
    assert len({
        (entry.identity, entry.sha256) for entry in evidence.compiler_identities
    }) == 1


def test_backoff_fixed_nonnegative_endpoints_match_pointwise():
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    cases = [_case(0), _case(5), _case(999)]
    evidence = G.assert_backoff_fixed_meaning(captured, cases, cxx=_any_cxx())
    assert len(evidence.observations) == 6
    assert all(row.expected_bits == row.observed_bits for row in evidence.observations)


def test_f707_missing_mapping_rejected_before_compiler(monkeypatch: pytest.MonkeyPatch):
    assert _fixture_hole(_F707) == _fixture_hole(_SUPPLIED)
    captured = G.capture_backoff_fixed_inputs(_F707)
    supplied_names = G.source_digest.parse_supplied_macros(
        captured.options_text, captured.protocol_cmake_text,
    )
    assert supplied_names == {"BACKOFF_NOINLINE"}
    supplied_options = (_SUPPLIED / G.OPTIONS_REL).read_text(encoding="utf-8")
    assert captured.options_text == supplied_options.replace(
        "    BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}\n", "",
    )

    def forbidden(*args, **kwargs):
        pytest.fail("compiler seam was reached before supply rejection")

    monkeypatch.setattr(G, "_resolve_compiler", forbidden)
    monkeypatch.setattr(G, "_run_process", forbidden)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_supply(captured, [5])
    assert raised.value.reason_code == "macro-not-supplied"
    assert raised.value.define_value == 5


def test_meaning_arm_does_not_depend_on_supply_green():
    captured = G.capture_backoff_fixed_inputs(_F707)
    with pytest.raises(G.ConditionMeaningGateError) as supply_rejection:
        G.assert_backoff_fixed_supply(captured, [5])
    assert supply_rejection.value.reason_code == "macro-not-supplied"

    meaning = G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=_any_cxx())
    assert [row.observed_bits for row in meaning.observations] == [_bits(5), _bits(5)]


def test_wrong_cache_rhs_rejects_supply_value_mismatch(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    options = root / G.OPTIONS_REL
    text = options.read_text(encoding="utf-8")
    options.write_text(
        text.replace(
            "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}",
            "BACKOFF_FIXED=${CCBENCH_BACKOFF_NOINLINE}",
        ),
        encoding="utf-8",
    )
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_supply(captured, [5])
    assert raised.value.reason_code == "supply-value-mismatch"
    assert raised.value.expected == "5"
    assert raised.value.observed == "0"


def test_wrong_cache_rhs_is_rejected_even_when_effective_value_matches(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    options = root / G.OPTIONS_REL
    text = options.read_text(encoding="utf-8")
    text = text.replace(
        "set(CCBENCH_BACKOFF_NOINLINE 0 CACHE STRING",
        "set(CCBENCH_BACKOFF_NOINLINE 5 CACHE STRING",
    )
    text = text.replace(
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}",
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_NOINLINE}",
    )
    options.write_text(text, encoding="utf-8")
    captured = G.capture_backoff_fixed_inputs(root)

    resolution = G.source_digest.resolve_effective_defines_from_cmake_sources(
        G.SOURCE_REL,
        G.Genome(G.PROTOCOL, {G.MACRO: 5}),
        options_text=captured.options_text,
        protocol_cmake_text=captured.protocol_cmake_text,
    )
    assert resolution.cache_name(G.MACRO) == "BACKOFF_NOINLINE"
    assert resolution.effective_value(G.MACRO) == "5"

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_supply(captured, [5])
    assert raised.value.reason_code == "supply-value-mismatch"
    assert raised.value.expected == raised.value.observed == "5"


def test_bare_supply_is_value_mismatch_not_missing(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    options = root / G.OPTIONS_REL
    text = options.read_text(encoding="utf-8")
    options.write_text(
        text.replace(
            "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}",
            "BACKOFF_FIXED",
        ),
        encoding="utf-8",
    )
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_supply(captured, [5])
    assert raised.value.reason_code == "supply-value-mismatch"
    assert raised.value.expected == "5"
    assert raised.value.observed == "1"


def test_f718_1000_decodes_to_zero():
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    supply = G.assert_backoff_fixed_supply(captured, [1000])
    assert supply.driver_integration == "none"
    assert supply.observations[0].effective_value == "1000"
    assert supply.input_files == captured.input_files

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(captured, [_case(1000)], cxx=_any_cxx())
    error = raised.value
    assert error.reason_code == "decoded-meaning-mismatch"
    assert error.define_value == 1000
    assert error.context_index == 0
    assert error.expected == _bits(1000)
    assert error.observed == _bits(0)


def test_generic_f707_is_supply_red_and_meaning_green():
    captured = G.capture_define_inputs(_F707)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=_declaration(_case(5)), cxx=_any_cxx(),
    )

    assert (supply.terminal_status, supply.reason_code) == ("red", "macro-not-supplied")
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )


def test_generic_f718_is_supply_green_and_meaning_red():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(1000)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=_declaration(_case(1000)), cxx=_any_cxx(),
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "decoded-meaning-mismatch",
    )


def test_cmake_cxx_flags_route_uses_real_owner_compile_command():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = G.make_define_request(
        driver_id="test-condition-meaning-gate",
        macro="IZANAGI_BREAK_PERMUTATION",
        requested_value=1,
        default_value=None,
    )
    record = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    assert any(
        argument == "-DIZANAGI_BREAK_PERMUTATION=1"
        for argument in evidence["requested_replay_argv"]
    )


def test_supply_effectuation_does_not_pin_volatile_fixture_hash(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    owner = root / "cc" / "silo" / "transaction.cc"
    owner.write_text(
        owner.read_text(encoding="utf-8") + "\n// unrelated worktree drift\n",
        encoding="utf-8",
    )
    captured = G.capture_define_inputs(root)
    record = G.evaluate_define_supply_effectuation(
        captured, request=_request(5), cxx=_any_cxx(), cmake=_any_cmake(),
    )

    assert (record.terminal_status, record.reason_code) == (
        "green", "requested-default-preprocess-different",
    )


def test_ignored_define_has_identical_preprocessed_bytes_and_is_red():
    captured = G.capture_define_inputs(_IGNORED)
    request = _request(5)
    record = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=_declaration(_case(5)), cxx=_any_cxx(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "red", "preprocess-bytes-identical",
    )
    assert evidence["requested_digest"] == evidence["control_digest"]
    assert evidence["requested_byte_length"] == evidence["control_byte_length"]
    assert any(
        argument == "-DBACKOFF_FIXED=5"
        for argument in evidence["requested_replay_argv"]
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )


def test_backoff_fixed_minus_one_stock_preprocess_identity_is_green():
    captured = G.capture_define_inputs(_SUPPLIED, stock_root=_SUPPLIED / "stock")
    record = G.evaluate_define_supply_effectuation(
        captured, request=_request(-1, default=None),
        cxx=_any_cxx(), cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "green", "stock-inert-preprocess-identical",
    )
    assert evidence["requested_digest"] == evidence["control_digest"]


def test_requested_default_inert_reaches_tu_and_matches_stock():
    captured = G.capture_define_inputs(_SUPPLIED, stock_root=_SUPPLIED / "stock")
    request = G.make_define_request(
        driver_id="test-condition-meaning-gate",
        macro="BACKOFF_NOINLINE",
        requested_value=0,
        default_value=0,
    )
    record = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "green", "stock-inert-preprocess-identical",
    )
    assert evidence["comparison"] == "stock-inert-identity"
    assert evidence["requested_digest"] == evidence["control_digest"]
    assert any(
        argument == "-DBACKOFF_NOINLINE=0"
        for argument in evidence["requested_replay_argv"]
    )


def test_inert_missing_tu_supply_is_red_while_branch_meaning_is_green():
    captured = G.capture_define_inputs(_F707, stock_root=_SUPPLIED / "stock")
    request = _request(-1, default=-1)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=_declaration(_stock_branch_case()), cxx=_any_cxx(),
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "red", "macro-not-supplied",
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )
    assert meaning.evidence["observed_branch"] == G.STOCK_ADAPTIVE_BRANCH


def test_inert_supply_and_independent_branch_meaning_admit_certified_selection():
    captured = G.capture_define_inputs(_SUPPLIED, stock_root=_SUPPLIED / "stock")
    request = _request(-1, default=-1)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=_declaration(_stock_branch_case()), cxx=_any_cxx(),
    )
    admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="certified-selection",
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "green", "stock-inert-preprocess-identical",
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )
    assert meaning.evidence["proof_kind"] == G.BRANCH_MEANING_PROOF_KIND
    assert meaning.evidence["observed_branch"] == G.STOCK_ADAPTIVE_BRANCH
    assert supply.record_id != meaning.record_id
    assert supply.record_digest != meaning.record_digest
    assert admission.admitted is True


def test_inert_supply_green_but_nonstock_selected_branch_is_meaning_red(
    tmp_path: Path,
):
    root = _copied_fixture(tmp_path)
    _replace_source(root, "#if BACKOFF_FIXED >= 0", "#if BACKOFF_FIXED >= -1")
    _replace_source(
        root,
        B10.EXPECTED_HOLE_LINE,
        "    double now_backoff = Backoff_.load(std::memory_order_acquire);",
    )
    captured = G.capture_define_inputs(root, stock_root=root / "stock")
    request = _request(-1, default=-1)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=_declaration(_stock_branch_case()), cxx=_any_cxx(),
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "green", "stock-inert-preprocess-identical",
    )
    assert supply.evidence["requested_digest"] == supply.evidence["control_digest"]
    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "selected-branch-mismatch",
    )
    assert meaning.evidence["expected"] == G.STOCK_ADAPTIVE_BRANCH
    assert meaning.evidence["observed"] == G.SYNTHESIZED_BACKOFF_BRANCH


def test_cli_accepts_inert_selected_branch_meaning_case():
    cases = G._cli_meaning_cases([
        f"-1:branch:{G.STOCK_ADAPTIVE_BRANCH}",
    ])
    assert cases == (_stock_branch_case(),)


def test_backoff_fixed_minus_one_requires_stock_preprocess_identity(tmp_path: Path):
    root = tmp_path / "supplied"
    shutil.copytree(_SUPPLIED, root)
    stock_header = root / "stock" / "include" / "backoff.hh"
    stock_header.write_text(
        "    double now_backoff = Backoff_.load(std::memory_order_acquire) + 1;\n",
        encoding="utf-8",
    )
    captured = G.capture_define_inputs(root, stock_root=root / "stock")
    record = G.evaluate_define_supply_effectuation(
        captured, request=_request(-1, default=None, stock=True),
        cxx=_any_cxx(), cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "red", "stock-inert-mismatch",
    )
    assert evidence["requested_digest"] != evidence["control_digest"]


def test_arm_records_have_distinct_ids_digests_statuses_and_reasons():
    request = _request(5)
    request_digest = G._request_digest(request, ())
    supply = G._arm_record(
        arm="supply-effectuation", terminal_status="green",
        reason_code="requested-default-preprocess-different", request=request,
        request_digest=request_digest, evidence={"requested_digest": "a" * 64},
    )
    meaning = G._arm_record(
        arm="runtime-meaning", terminal_status="red",
        reason_code="decoded-meaning-mismatch", request=request,
        request_digest=request_digest, evidence={"observed": "b" * 16},
    )

    assert supply.record_id != meaning.record_id
    assert supply.record_digest != meaning.record_digest
    assert supply.terminal_status != meaning.terminal_status
    assert supply.reason_code != meaning.reason_code
    admission = G.require_condition_gate_family([supply], [meaning], use_class="raw")
    serialized = admission.canonical_json()
    assert admission.record_ids == (supply.record_id, meaning.record_id)
    assert admission.admitted is False
    assert "terminal_status" not in serialized
    assert "reason_code" not in serialized
    assert "evidence" not in serialized


def test_undeclared_meaning_is_not_green_and_p_strict_blocks_promotion():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=_any_cxx(),
    )
    supply = G._arm_record(
        arm="supply-effectuation", terminal_status="green",
        reason_code="requested-default-preprocess-different", request=request,
        request_digest=meaning.request_digest, evidence={},
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "unestablished", "meaning-witness-undeclared",
    )
    assert G.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    ).admitted is True
    assert G.require_condition_gate_family(
        [supply], [meaning], use_class="paper",
    ).admitted is False


def test_duplicate_correct_marker_blocks_are_rejected(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    source = root / G.SOURCE_REL
    text = source.read_text(encoding="utf-8")
    source.write_text(text + text, encoding="utf-8")
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=_any_cxx())
    assert raised.value.reason_code == "materialized-decoder-invalid"


def test_formula_in_comment_with_changed_expression_is_rejected(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    formula = B10.EXPECTED_HOLE_LINE
    replacement = (
        f"    // {formula.strip()}\n"
        "    double now_backoff = static_cast<double>(BACKOFF_FIXED + 1);"
    )
    _replace_source(root, formula, replacement)
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=_any_cxx())
    assert raised.value.reason_code == "decoded-meaning-mismatch"


def test_uniform_shift_decoder_is_rejected(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    _replace_source(
        root,
        B10.EXPECTED_HOLE_LINE,
        "    double now_backoff = static_cast<double>(BACKOFF_FIXED + 1);",
    )
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(
            captured, [_case(0), _case(5), _case(999)], cxx=_any_cxx(),
        )
    assert raised.value.reason_code == "decoded-meaning-mismatch"
    assert raised.value.define_value == 0


def test_result_identifier_must_be_exact_double(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    _replace_source(
        root,
        B10.EXPECTED_HOLE_LINE,
        "    std::uint64_t now_backoff = 0x4014000000000000ULL;",
    )
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=_any_cxx())
    assert raised.value.reason_code == "compiler-failed"


def test_duplicate_rows_fail_closed():
    cases = (_case(5),)
    valid = _bits(5).encode("ascii")
    output = b"0 0 " + valid + b"\n0 0 " + valid + b"\n0 1 " + valid + b"\n"
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._parse_observed_rows(output, cases)
    assert raised.value.reason_code == "compiler-output-invalid"


def test_missing_rows_fail_closed():
    valid = _bits(5).encode("ascii")
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._parse_observed_rows(b"0 0 " + valid + b"\n", (_case(5),))
    assert raised.value.reason_code == "compiler-output-invalid"


def test_unknown_rows_fail_closed():
    valid = _bits(5).encode("ascii")
    output = b"0 0 " + valid + b"\n1 0 " + valid + b"\n"
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._parse_observed_rows(output, (_case(5),))
    assert raised.value.reason_code == "compiler-output-invalid"


def test_nonfinite_decoder_output_fails_closed(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    _replace_source(
        root,
        B10.EXPECTED_HOLE_LINE,
        "    double now_backoff = __builtin_inf();",
    )
    captured = G.capture_backoff_fixed_inputs(root)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=_any_cxx())
    assert raised.value.reason_code == "decoded-output-nonfinite"
    assert raised.value.define_value == 5
    for bits in ("7ff0000000000000", "7ff8000000000001"):
        output = f"0 0 {bits}\n0 1 {_bits(5)}\n".encode("ascii")
        with pytest.raises(G.ConditionMeaningGateError) as parsed:
            G._parse_observed_rows(output, (_case(5),))
        assert parsed.value.reason_code == "decoded-output-nonfinite"


def test_compiler_failure_fails_closed(tmp_path: Path):
    compiler = tmp_path / "failing-cxx"
    compiler.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo fixture-cxx; exit 0; fi\n"
        "echo compile-failed >&2\n"
        "exit 9\n",
        encoding="utf-8",
    )
    compiler.chmod(0o755)
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(captured, [_case(5)], cxx=os.fspath(compiler))
    assert raised.value.reason_code == "compiler-failed"


def _process_phase(argv: list[str]) -> str:
    if argv[1:] == ["--version"]:
        return "version"
    if "-o" in argv:
        return "compile"
    assert len(argv) == 1
    return "run"


def _valid_process_result(argv: list[str], phase: str) -> subprocess.CompletedProcess[bytes]:
    stdout = b"fixture-cxx 1\n" if phase == "version" else b""
    if phase == "compile":
        binary_path = Path(argv[argv.index("-o") + 1])
        binary_path.write_bytes(b"fixture-decoder")
        binary_path.chmod(0o755)
    elif phase == "run":
        binary_path = Path(argv[0])
        assert binary_path.read_bytes() == b"fixture-decoder"
        assert os.access(binary_path, os.X_OK)
        stdout = f"0 0 {_bits(5)}\n0 1 {_bits(5)}\n".encode("ascii")
    return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr=b"")


def _assert_process_phase_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    target_phase: str,
    target_result: subprocess.CompletedProcess[bytes] | None,
    expected_reason: str,
) -> None:
    compiler = tmp_path / "fixture-cxx"
    compiler.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    compiler.chmod(0o755)
    process_phases: list[str] = []
    observed_timeouts: list[float] = []

    def run(argv, **kwargs):
        assert kwargs["capture_output"] is True
        assert kwargs["check"] is False
        observed_timeouts.append(kwargs["timeout"])
        phase = _process_phase(argv)
        process_phases.append(phase)
        valid = _valid_process_result(argv, phase)
        if phase != target_phase:
            return valid
        if target_result is None:
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        stdout = valid.stdout if phase == "run" else target_result.stdout
        return subprocess.CompletedProcess(
            argv, target_result.returncode,
            stdout=stdout, stderr=target_result.stderr,
        )

    monkeypatch.setattr(G.subprocess, "run", run)
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(
            captured, [_case(5)], cxx=os.fspath(compiler),
        )
    assert raised.value.reason_code == expected_reason
    expected_phases = ["version", "compile"]
    if target_phase == "run":
        expected_phases.append("run")
    assert process_phases == expected_phases
    assert observed_timeouts == [G.PROCESS_TIMEOUT_SECONDS] * len(expected_phases)


def test_compile_timeout_is_120_seconds_and_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_process_phase_failure(
        tmp_path, monkeypatch, target_phase="compile", target_result=None,
        expected_reason="compiler-timeout",
    )


def test_run_timeout_is_120_seconds_and_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_process_phase_failure(
        tmp_path, monkeypatch, target_phase="run", target_result=None,
        expected_reason="decoder-run-timeout",
    )


def test_compile_return_code_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_process_phase_failure(
        tmp_path, monkeypatch, target_phase="compile",
        target_result=subprocess.CompletedProcess(
            ["x"], 4, stdout=b"", stderr=b"",
        ),
        expected_reason="compiler-failed",
    )


def test_run_return_code_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_process_phase_failure(
        tmp_path, monkeypatch, target_phase="run",
        target_result=subprocess.CompletedProcess(
            ["x"], 4, stdout=b"", stderr=b"",
        ),
        expected_reason="decoder-run-failed",
    )


def test_compile_stderr_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_process_phase_failure(
        tmp_path, monkeypatch, target_phase="compile",
        target_result=subprocess.CompletedProcess(
            ["x"], 0, stdout=b"", stderr=b"warning",
        ),
        expected_reason="compiler-failed",
    )


def test_run_stderr_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_process_phase_failure(
        tmp_path, monkeypatch, target_phase="run",
        target_result=subprocess.CompletedProcess(
            ["x"], 0, stdout=b"", stderr=b"warning",
        ),
        expected_reason="decoder-run-failed",
    )


def test_patch_target_decoder_and_fixture_holes_are_independently_anchored():
    patch_block = extract_materialized_evolve_block(_patch_target_source(), G.MARKER_ID)
    supplied_block = extract_materialized_evolve_block(
        (_SUPPLIED / G.SOURCE_REL).read_text(encoding="utf-8"), G.MARKER_ID,
    )
    f707_block = extract_materialized_evolve_block(
        (_F707 / G.SOURCE_REL).read_text(encoding="utf-8"), G.MARKER_ID,
    )
    assert supplied_block.conditional == patch_block.conditional
    assert f707_block.conditional == patch_block.conditional
    assert supplied_block.hole == f707_block.hole
    assert supplied_block.hole == B10.EXPECTED_HOLE_LINE + "\n"


def test_v1_domain_and_claim_boundaries_are_exact():
    assert G.SUPPORTED_MACROS == {
        "BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACKOFF_REQUESTED_US",
        "BACKOFF_TRIGGER_GATING", "SORT_VARIANT", "SS2PL_LOCK_IMPL",
        "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
        "IZANAGI_BREAK_PERMUTATION", "IZANAGI_BREAK_PERMUTATION_SWAP",
        "IZANAGI_BREAK_LOCK_COVERAGE", "IZANAGI_BREAK_EARLY_UNLOCK",
        "IZANAGI_BREAK_NOREAD_VALIDATION", "IZANAGI_BREAK_HIGHKEY_VALIDATION",
        "IZANAGI_BREAK_WRITE_INTENT_ERASE", "IZANAGI_BREAK_WRITE_INTENT_FORGE",
        "IZANAGI_BREAK_WRITE_INTENT_OPSWAP", "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
        "IZANAGI_BREAK_TRIGGER_MISATTR", "IZANAGI_SILO_LADDER_RUNG1",
        "IZANAGI_SILO_LADDER_RUNG1_REPORT",
    }
    assert G.RELATED_DEFINE_DECODE_MACROS == {
        "BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACKOFF_REQUESTED_US",
        "BACKOFF_TRIGGER_GATING", "SORT_VARIANT", "SS2PL_LOCK_IMPL",
        "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
    }
    assert G.RELATED_DEFINE_DECODE_MACROS <= G.SUPPORTED_MACROS
    assert G.DEFINE_SPECS["SS2PL_LOCK_KIND"].companion_defines == (
        ("SS2PL_LOCK_IMPL", "1"),
    )
    assert G.DEFINE_SPECS["BACKOFF_FIXED"].inert_values == ("-1",)
    assert G.DEFINE_SPECS[
        "IZANAGI_SILO_LADDER_RUNG1_REPORT"
    ].companion_defines == (("IZANAGI_SILO_LADDER_RUNG1", "1"),)
    assert sum(
        spec.route == G.ROUTE_CMAKE_CACHE for spec in G.DEFINE_SPECS.values()
    ) == 9
    assert sum(
        spec.route == G.ROUTE_CMAKE_CXX_FLAGS for spec in G.DEFINE_SPECS.values()
    ) == 13
    assert G.CONTEXT_STARTS == (1, 2)
    assert G.DRIVER_INTEGRATION == "none"
    for invalid in (True, -1, 1.0, "1"):
        with pytest.raises(ValueError):
            G.MeaningCase(invalid, (_bits(1), _bits(1)))
    assert _stock_branch_case().expected_selected_branch == G.STOCK_ADAPTIVE_BRANCH
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    for invalid in (True, -1, 1.0, "1"):
        with pytest.raises(G.ConditionMeaningGateError) as raised:
            G.assert_backoff_fixed_supply(captured, [invalid])
        assert raised.value.reason_code == "supply-contract-invalid"
    with pytest.raises(ValueError):
        G.MeaningCase(1, ("7ff0000000000000", "7ff0000000000000"))


def test_captured_input_hash_drift_fails_closed():
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    assert [entry.relative_path for entry in captured.input_files] == [
        G.SOURCE_REL, G.OPTIONS_REL, G.PROTOCOL_CMAKE_REL,
    ]
    expected_hashes = {
        G.SOURCE_REL: captured.source_sha256,
        G.OPTIONS_REL: captured.options_sha256,
        G.PROTOCOL_CMAKE_REL: captured.protocol_cmake_sha256,
    }
    for entry in captured.input_files:
        assert entry.before == entry.after == entry.path_after
        assert entry.sha256 == expected_hashes[entry.relative_path]
    tampered = replace(captured, source_sha256="0" * 64)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_supply(tampered, [5])
    assert raised.value.reason_code == "input-capture-failed"


def test_parent_component_symlink_outside_root_is_rejected(tmp_path: Path):
    root = _copied_fixture(tmp_path)
    outside = tmp_path / "outside"
    shutil.copytree(root / "include", outside)
    (root / "include").rename(root / "include-original")
    (root / "include").symlink_to(outside, target_is_directory=True)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.capture_backoff_fixed_inputs(root)
    assert raised.value.reason_code == "input-capture-failed"


def _assert_compiler_phase_drift_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift_phase: str,
) -> None:
    compiler = tmp_path / "fixture-cxx"
    compiler.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    compiler.chmod(0o755)
    baseline = G.RegularFileIdentity(1, 2, 3, 4, 5)
    drifted = replace(baseline, inode=baseline.inode + 1)
    captured_phases: list[str] = []
    process_phases: list[str] = []

    def capture_identity(path: Path, phase: str) -> G.CompilerFileEvidence:
        assert path == compiler
        captured_phases.append(phase)
        identity = drifted if phase == drift_phase else baseline
        return G.CompilerFileEvidence(phase, identity, "a" * 64)

    def run(argv, **kwargs):
        assert kwargs == {
            "capture_output": True,
            "timeout": G.PROCESS_TIMEOUT_SECONDS,
            "check": False,
        }
        phase = _process_phase(argv)
        process_phases.append(phase)
        return _valid_process_result(argv, phase)

    monkeypatch.setattr(G, "_capture_compiler_identity", capture_identity)
    monkeypatch.setattr(G.subprocess, "run", run)
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.assert_backoff_fixed_meaning(
            captured, [_case(5)], cxx=os.fspath(compiler),
        )
    assert raised.value.reason_code == "compiler-identity-drift"
    assert drift_phase in raised.value.detail

    original_require = G._require_same_compiler

    def require_other_phases(
        baseline_evidence: G.CompilerFileEvidence,
        observed: G.CompilerFileEvidence,
    ) -> None:
        if observed.phase != drift_phase:
            original_require(baseline_evidence, observed)

    captured_phases.clear()
    process_phases.clear()
    monkeypatch.setattr(G, "_require_same_compiler", require_other_phases)
    evidence = G.assert_backoff_fixed_meaning(
        captured, [_case(5)], cxx=os.fspath(compiler),
    )
    assert captured_phases == ["before-version", "after-version", "after-compile"]
    assert process_phases == ["version", "compile", "run"]
    assert [entry.identity for entry in evidence.compiler_identities] == [
        baseline,
        drifted if drift_phase == "after-version" else baseline,
        drifted if drift_phase == "after-compile" else baseline,
    ]
    assert [(row.start, row.observed_bits) for row in evidence.observations] == [
        (1, "4014000000000000"), (2, "4014000000000000"),
    ]


def test_compiler_identity_drift_after_version_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_compiler_phase_drift_is_rejected(tmp_path, monkeypatch, "after-version")


def test_compiler_identity_drift_after_compile_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _assert_compiler_phase_drift_is_rejected(tmp_path, monkeypatch, "after-compile")


def _run() -> int:
    """Keep this test file in the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
