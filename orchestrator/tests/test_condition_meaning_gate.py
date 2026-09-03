# -*- coding: utf-8 -*-
"""Independent supply and compiler-evaluated meaning tests for T-2018."""
from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import struct
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from orchestrator.campaign import b10_backoff_shape_sweep as B10
from orchestrator.campaign import condition_meaning_gate as G
from orchestrator.campaign.evolve_block import extract_materialized_evolve_block
from orchestrator.tests.condition_gate_test_support import (
    install_condition_gate_build_fixture,
)


_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).parent / "fixtures" / "condition_meaning_gate"
_SUPPLIED = _FIXTURES / "supplied"
_F707 = _FIXTURES / "f707-missing-supply"
_IGNORED = _FIXTURES / "effectuation-ignored"
_PATCH = _ROOT / "patches" / "silo-backoff-fixed.patch"
_COMPILE_TIME_BRANCH_MACROS = (
    "IZANAGI_BREAK_PERMUTATION",
    "IZANAGI_BREAK_PERMUTATION_SWAP",
    "IZANAGI_BREAK_LOCK_COVERAGE",
    "IZANAGI_BREAK_EARLY_UNLOCK",
    "IZANAGI_BREAK_WRITE_INTENT_ERASE",
    "IZANAGI_BREAK_WRITE_INTENT_FORGE",
    "IZANAGI_BREAK_WRITE_INTENT_OPSWAP",
    "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
)


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


def _public_arm_record(
    *,
    arm: str,
    terminal_status: str,
    reason_code: str,
    request: G.DefineRequest,
    request_digest: str,
    evidence: dict[str, object],
) -> G.ConditionArmRecord:
    payload = {
        "arm": arm,
        "terminal_status": terminal_status,
        "reason_code": reason_code,
        "driver_id": request.driver_id,
        "macro": request.macro,
        "request_digest": request_digest,
        "evidence": evidence,
    }
    digest = G._canonical_digest(payload)
    return G.ConditionArmRecord(
        record_id=f"condition-gate/{arm}/{digest}",
        record_digest=digest,
        arm=arm,
        terminal_status=terminal_status,
        reason_code=reason_code,
        driver_id=request.driver_id,
        macro=request.macro,
        request_digest=request_digest,
        evidence=evidence,
    )


def _assert_current_cmake_evidence(
    evidence: dict[str, object],
    labels: tuple[str, str],
) -> None:
    cmake_path = evidence["cmake_path"]
    assert type(cmake_path) is str
    cmake_file = Path(cmake_path)
    current_sha256 = hashlib.sha256(cmake_file.read_bytes()).hexdigest()
    current_identity = G._file_identity(os.stat(cmake_file, follow_symlinks=False))
    for label in labels:
        configure_argv = evidence[f"{label}_configure_argv"]
        identities = evidence[f"{label}_cmake_identities"]
        assert type(configure_argv) is tuple
        assert configure_argv and configure_argv[0] == cmake_path
        assert type(identities) is tuple
        assert tuple(row.phase for row in identities) == (
            "before-configure", "after-configure",
        )
        assert all(row.sha256 == current_sha256 for row in identities)
        assert all(row.identity == current_identity for row in identities)


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


def _compile_time_request(
    macro: str,
    *,
    requested: int | str = 1,
    default: int | str | None = 0,
) -> G.DefineRequest:
    return G.make_define_request(
        driver_id="test-compile-time-branch-selection",
        macro=macro,
        requested_value=requested,
        default_value=default,
    )


def _compile_time_source_root(
    tmp_path: Path,
    macro: str,
    *,
    prefix: str = "",
    duplicate: bool = False,
    nested: bool = False,
    close: bool = True,
    directive: str | None = None,
    owner_text: str | None = None,
) -> Path:
    root = tmp_path / "ccbench"
    owner = root / "cc" / "silo" / "transaction.cc"
    owner.parent.mkdir(parents=True)
    if owner_text is None:
        branch = (
            (directive or f"#if {macro}") + "\n"
            "int izanagi_compile_time_selected = 1;\n"
            + ("#endif\n" if close else "")
        )
        if nested:
            branch = "#if 1\n" + branch + "#endif\n"
        owner_text = prefix + branch + (branch if duplicate else "")
    owner.write_text(owner_text, encoding="utf-8")
    return install_condition_gate_build_fixture(root)


def _patch_added_branch_declaration(macro: str) -> tuple[str, str]:
    """Derive the owner and exact start directive from real patch additions."""
    patch = _ROOT / G.DEFINE_SPECS[macro].patch_rel
    current_target: str | None = None
    matches: list[tuple[str, str]] = []
    for line in patch.read_text(encoding="utf-8").splitlines():
        if line.startswith("+++ b/"):
            current_target = line.removeprefix("+++ b/")
        elif line.startswith("+") and not line.startswith("+++") \
                and line[1:] == f"#if {macro}":
            assert current_target is not None
            matches.append((current_target, line[1:]))
    assert len(matches) == 1
    return matches[0]


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


def test_supply_green_binds_real_cmake_identity_and_gate_configure_argv():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    G._validate_arm_record_integrity(supply)
    _assert_current_cmake_evidence(
        dict(supply.evidence), ("requested", "control"),
    )


def test_real_cmake_wrapper_replacement_during_configure_is_rejected(
    tmp_path: Path,
):
    real_cmake = Path(_any_cmake()).resolve(strict=True)
    wrapper = tmp_path / "cmake-wrapper"
    stable = tmp_path / "cmake-wrapper.stable"
    stable.write_text(
        "#!/bin/sh\n"
        f"exec {shlex.quote(os.fspath(real_cmake))} \"$@\"\n",
        encoding="utf-8",
    )
    stable.chmod(0o755)
    original = (
        "#!/bin/sh\n"
        "cp \"$0.stable\" \"$0.next\"\n"
        "chmod 755 \"$0.next\"\n"
        "mv \"$0.next\" \"$0\"\n"
        f"exec {shlex.quote(os.fspath(real_cmake))} \"$@\"\n"
    )
    wrapper.write_text(original, encoding="utf-8")
    wrapper.chmod(0o755)

    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(_SUPPLIED),
        request=_request(5),
        cxx=_any_cxx(),
        cmake=os.fspath(wrapper),
    )

    assert wrapper.read_text(encoding="utf-8") == stable.read_text(encoding="utf-8")
    assert (record.terminal_status, record.reason_code) == (
        "red", "cmake-identity-drift",
    )


def test_configure_compile_commands_rejects_real_cmake_replacement_before_return(
    tmp_path: Path,
):
    real_cmake = Path(_any_cmake()).resolve(strict=True)
    wrapper = tmp_path / "cmake-wrapper"
    stable = tmp_path / "cmake-wrapper.stable"
    stable.write_text(
        "#!/bin/sh\n"
        f"exec {shlex.quote(os.fspath(real_cmake))} \"$@\"\n",
        encoding="utf-8",
    )
    stable.chmod(0o755)
    wrapper.write_text(
        "#!/bin/sh\n"
        "cp \"$0.stable\" \"$0.next\"\n"
        "chmod 755 \"$0.next\"\n"
        "mv \"$0.next\" \"$0\"\n"
        f"exec {shlex.quote(os.fspath(real_cmake))} \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    _spec, requested, _default, companions = G._validate_define_request(request)
    resolved_wrapper = G._resolve_executable(
        os.fspath(wrapper), "configure-failed",
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._configure_compile_commands(
            captured=captured,
            request=request,
            source_root=Path(captured.source_root),
            build_root=tmp_path / "build",
            value=requested,
            companions=companions,
            compiler=G._resolve_compiler(_any_cxx()),
            cmake=resolved_wrapper,
        )

    assert wrapper.read_text(encoding="utf-8") == stable.read_text(encoding="utf-8")
    assert raised.value.reason_code == "cmake-identity-drift"
    assert raised.value.detail == "CMake path identity/content changed by after-configure"


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


def test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches(
    tmp_path: Path,
):
    assert tuple(G.CONDITIONAL_BRANCH_WITNESSES) == _COMPILE_TIME_BRANCH_MACROS
    for macro in _COMPILE_TIME_BRANCH_MACROS:
        patch_declaration = _patch_added_branch_declaration(macro)
        fixture = _compile_time_source_root(tmp_path / macro, macro)
        fixture_directives = [
            line for line in (
                fixture / "cc" / "silo" / "transaction.cc"
            ).read_text(encoding="utf-8").splitlines()
            if line.startswith("#if ")
        ]
        assert fixture_directives == [f"#if {macro}"]
        assert ("cc/silo/transaction.cc", fixture_directives[0]) \
            == patch_declaration
        assert G.CONDITIONAL_BRANCH_WITNESSES[macro] == patch_declaration


def test_compile_time_meaning_green_binds_real_cmake_identity_and_gate_argv(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_PERMUTATION"
    root = _compile_time_source_root(tmp_path, macro)
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )
    G._validate_arm_record_integrity(meaning)
    _assert_current_cmake_evidence(
        dict(meaning.evidence), ("requested", "default"),
    )


def test_real_compile_time_green_admits_certified_selection(tmp_path: Path):
    macro = "IZANAGI_BREAK_PERMUTATION"
    root = _copied_fixture(tmp_path)
    captured = G.capture_define_inputs(root)
    request = _compile_time_request(macro)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured,
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )
    admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="certified-selection",
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )
    G._validate_arm_record_integrity(supply)
    G._validate_arm_record_integrity(meaning)
    _assert_current_cmake_evidence(
        dict(supply.evidence), ("requested", "control"),
    )
    _assert_current_cmake_evidence(
        dict(meaning.evidence), ("requested", "default"),
    )
    assert admission.admitted is True


@pytest.mark.parametrize("macro", _COMPILE_TIME_BRANCH_MACROS)
def test_compile_time_branch_selection_accepts_each_registry_macro(
    tmp_path: Path,
    macro: str,
):
    root = _compile_time_source_root(tmp_path, macro)
    request = _compile_time_request(macro)
    declaration = G.declare_define_runtime_meaning(request)

    assert type(declaration) is G.ConditionalBranchMeaningDeclaration
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=declaration,
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )
    assert meaning.evidence["proof_kind"] == G.COMPILE_TIME_BRANCH_SELECTION_PROOF_KIND
    assert "compile-time" in meaning.evidence["proof_kind"]
    assert "runtime" not in meaning.evidence["proof_kind"]
    assert meaning.evidence["requested"].selected_count == 1
    assert meaning.evidence["requested"].completed_count == 1
    assert meaning.evidence["default"].selected_count == 0
    assert meaning.evidence["default"].completed_count == 1
    requested_argv = tuple(
        argument.replace(f"-D{macro}=1", f"-D{macro}=<VALUE>")
        for argument in meaning.evidence["requested"].preprocess_argv
    )
    default_argv = tuple(
        argument.replace(f"-D{macro}=0", f"-D{macro}=<VALUE>")
        for argument in meaning.evidence["default"].preprocess_argv
    )
    assert requested_argv == default_argv


def test_shared_owner_commands_keep_arm_verdicts_independent_without_reconfigure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    macro = "IZANAGI_BREAK_PERMUTATION"
    root = _compile_time_source_root(
        tmp_path,
        macro,
        owner_text=(
            "int common_owner_bytes = 1;\n"
            f"#if {macro}\n"
            "#endif\n"
        ),
    )
    captured = G.capture_define_inputs(root)
    request = _compile_time_request(macro)
    cxx = _any_cxx()
    cmake = _any_cmake()
    configure_calls: list[Path] = []
    real_configure = G._configure_compile_commands

    def recording_configure(**kwargs):
        configure_calls.append(kwargs["build_root"])
        return real_configure(**kwargs)

    monkeypatch.setattr(G, "_configure_compile_commands", recording_configure)
    with G._configured_define_compile_commands(
        captured, request=request, cxx=cxx, cmake=cmake,
    ) as configured_commands:
        supply = G.evaluate_define_supply_effectuation(
            captured, request=request, cxx=cxx, cmake=cmake,
            configured_commands=configured_commands,
        )
        assert len(configure_calls) == 2
        meaning = G.evaluate_define_runtime_meaning(
            captured,
            request=request,
            declaration=G.declare_define_runtime_meaning(request),
            cxx=cxx,
            cmake=cmake,
            configured_commands=configured_commands,
        )
        assert len(configure_calls) == 2

    assert (supply.terminal_status, supply.reason_code) == (
        "red", "preprocess-bytes-identical",
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )
    assert supply.record_id != meaning.record_id
    assert supply.record_digest != meaning.record_digest


def test_compile_time_branch_selection_rejects_non_discriminating_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    macro = "IZANAGI_BREAK_PERMUTATION"
    source_rel, _start_directive = G.CONDITIONAL_BRANCH_WITNESSES[macro]
    mutated_directive = "#if 1"
    monkeypatch.setitem(
        G._CONDITIONAL_BRANCH_WITNESSES,
        macro,
        (source_rel, mutated_directive),
    )
    root = _compile_time_source_root(
        tmp_path,
        macro,
        directive=mutated_directive,
    )
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-selection-not-discriminating",
    )
    assert meaning.evidence["observed"] == "requested=(1, 1),default=(1, 1)"


def test_compile_time_branch_selection_accepts_active_nested_context(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_LOCK_COVERAGE"
    root = _compile_time_source_root(tmp_path, macro, nested=True)
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )


def test_compile_time_branch_selection_accepts_block_comment_prefix(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_LOCK_COVERAGE"
    root = _compile_time_source_root(
        tmp_path, macro, prefix="/*\n#if 0\n*/\n",
    )
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )


def test_compile_time_branch_selection_rejects_duplicate_start_directive(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_WRITE_INTENT_ERASE"
    root = _compile_time_source_root(tmp_path, macro, duplicate=True)
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-start-not-unique",
    )


def test_compile_time_branch_selection_rejects_owner_prefix_undef(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_WRITE_INTENT_FORGE"
    root = _compile_time_source_root(tmp_path, macro, prefix=f"#undef {macro}\n")
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-selection-not-discriminating",
    )
    assert meaning.evidence["observed"] == "requested=(0, 1),default=(0, 1)"


def test_compile_time_branch_selection_rejects_line_spliced_comment_endif(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_WRITE_INTENT_OPSWAP"
    root = _compile_time_source_root(
        tmp_path,
        macro,
        owner_text=(
            "#if 0\n"
            "// this endif is part of the comment after splicing \\\n"
            "#endif\n"
            f"#if {macro}\n"
            "int guarded = 1;\n"
            "#endif\n"
            "#endif\n"
        ),
    )
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-selection-not-discriminating",
    )
    assert meaning.evidence["observed"] == "requested=(0, 0),default=(0, 0)"


@pytest.mark.parametrize("container", ["block-comment", "raw-string"])
def test_compile_time_branch_selection_rejects_declared_line_in_non_directive_text(
    tmp_path: Path,
    container: str,
):
    macro = "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP"
    owner_text = (
        f"/*\n#if {macro}\n#endif\n*/\n"
        if container == "block-comment"
        else f'const char *text = R"probe(\n#if {macro}\n)probe";\n'
    )
    root = _compile_time_source_root(
        tmp_path / container, macro, owner_text=owner_text,
    )
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-selection-not-discriminating",
    )
    assert meaning.evidence["observed"] == "requested=(0, 0),default=(0, 0)"


def test_compile_time_branch_selection_rejects_unobserved_completion_marker(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_PERMUTATION"
    root = _compile_time_source_root(
        tmp_path,
        macro,
        prefix=(
            f"#undef {G._COMPILE_TIME_COMPLETED_MARKER}\n"
            f"#define {G._COMPILE_TIME_COMPLETED_MARKER}()\n"
        ),
    )
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-selection-mismatch",
    )
    assert meaning.evidence["observed"] == "requested=(1, 0),default=(0, 0)"


def test_compile_time_factory_keeps_unregistered_macro_unestablished(tmp_path: Path):
    request = _compile_time_request("IZANAGI_BREAK_NOREAD_VALIDATION")
    assert G.declare_define_runtime_meaning(request) is None

    root = tmp_path / "ccbench"
    root.mkdir()
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "unestablished", "meaning-witness-undeclared",
    )


@pytest.mark.parametrize(
    ("requested", "default"),
    [(1, None), (1, 1), (0, 0), (0, 1)],
)
def test_compile_time_factory_rejects_nonpaired_values(
    requested: int,
    default: int | None,
):
    request = _compile_time_request(
        "IZANAGI_BREAK_PERMUTATION",
        requested=requested,
        default=default,
    )
    assert G.declare_define_runtime_meaning(request) is None


def test_legacy_meaning_declaration_and_cli_stay_backoff_fixed_only(
    tmp_path: Path,
):
    assert G.MeaningWitnessDeclaration("BACKOFF_FIXED", ()) \
        == G.MeaningWitnessDeclaration("BACKOFF_FIXED", ())
    with pytest.raises(ValueError, match="no runtime witness support"):
        G.MeaningWitnessDeclaration("IZANAGI_BREAK_PERMUTATION", ())

    root = tmp_path / "ccbench"
    root.mkdir()
    with pytest.raises(SystemExit) as raised:
        G.condition_gate_cli([
            "--source-root", os.fspath(root),
            "--driver-id", "test-cli-legacy-boundary",
            "--macro", "IZANAGI_BREAK_PERMUTATION",
            "--requested-value", "1",
            "--default-value", "0",
            "--meaning-case", f"1:{_bits(1)}:{_bits(1)}",
            "--cxx", _any_cxx(),
        ])
    assert raised.value.code == 2


def test_compile_time_green_schema_rejects_missing_or_mutated_observations(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_PERMUTATION_SWAP"
    root = _compile_time_source_root(tmp_path, macro)
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )
    assert meaning.terminal_status == "green"

    mutations: list[dict[str, object]] = []
    missing = dict(meaning.evidence)
    del missing["default"]
    mutations.append(missing)
    same_observation = dict(meaning.evidence)
    same_observation["default"] = replace(
        same_observation["default"], selected_count=1,
    )
    mutations.append(same_observation)
    drifted_argv = dict(meaning.evidence)
    drifted_argv["default"] = replace(
        drifted_argv["default"],
        preprocess_argv=(*drifted_argv["default"].preprocess_argv, "-DOTHER=1"),
    )
    mutations.append(drifted_argv)
    wrong_kind = dict(meaning.evidence)
    wrong_kind["proof_kind"] = "runtime-conditional-branch-witness"
    mutations.append(wrong_kind)

    for evidence in mutations:
        forged = _public_arm_record(
            arm="runtime-meaning",
            terminal_status="green",
            reason_code="declared-compile-time-branch-selection-observed",
            request=request,
            request_digest=meaning.request_digest,
            evidence=evidence,
        )
        with pytest.raises(G.ConditionMeaningGateError) as raised:
            G._validate_arm_record_integrity(forged, require_issuer=False)
        assert raised.value.reason_code == "admission-contract-invalid"


def test_compile_time_green_rejects_different_requested_default_cmake_identity(
    tmp_path: Path,
):
    macro = "IZANAGI_BREAK_PERMUTATION_SWAP"
    root = _compile_time_source_root(tmp_path, macro)
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )
    assert meaning.terminal_status == "green"

    evidence = dict(meaning.evidence)
    default_identities = evidence["default_cmake_identities"]
    assert type(default_identities) is tuple
    evidence["default_cmake_identities"] = tuple(
        replace(
            row,
            identity=replace(row.identity, inode=row.identity.inode + 1),
            sha256="0" * 64,
        )
        for row in default_identities
    )
    forged = _public_arm_record(
        arm="runtime-meaning",
        terminal_status="green",
        reason_code=meaning.reason_code,
        request=request,
        request_digest=meaning.request_digest,
        evidence=evidence,
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._validate_arm_record_integrity(forged, require_issuer=False)
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "different CMake identities" in raised.value.detail


def test_nonconfiguring_meaning_proofs_reject_unexpected_cmake_evidence():
    captured = G.capture_define_inputs(_SUPPLIED)
    pointwise_request = _request(5)
    branch_request = _request(-1, default=-1)
    pointwise = G.evaluate_define_runtime_meaning(
        captured,
        request=pointwise_request,
        declaration=_declaration(_case(5)),
        cxx=_any_cxx(),
    )
    branch = G.evaluate_define_runtime_meaning(
        captured,
        request=branch_request,
        declaration=_declaration(_stock_branch_case()),
        cxx=_any_cxx(),
    )
    assert {
        pointwise.evidence["proof_kind"], branch.evidence["proof_kind"],
    } == {G.MEANING_PROOF_KIND, G.BRANCH_MEANING_PROOF_KIND}
    cmake_path = os.fspath(Path(_any_cmake()).resolve(strict=True))

    for record, request in (
        (pointwise, pointwise_request), (branch, branch_request),
    ):
        assert record.terminal_status == "green"
        evidence = dict(record.evidence)
        evidence["cmake_path"] = cmake_path
        forged = _public_arm_record(
            arm="runtime-meaning",
            terminal_status="green",
            reason_code=record.reason_code,
            request=request,
            request_digest=record.request_digest,
            evidence=evidence,
        )
        with pytest.raises(G.ConditionMeaningGateError) as raised:
            G._validate_arm_record_integrity(forged, require_issuer=False)
        assert raised.value.reason_code == "admission-contract-invalid"
        assert "unexpected=['cmake_path']" in raised.value.detail


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
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=_declaration(_case(5, expected=6)), cxx=_any_cxx(),
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


def test_unestablished_meaning_is_carried_into_promoted_admission():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = G.make_define_request(
        driver_id="test-condition-meaning-gate",
        macro="IZANAGI_BREAK_PERMUTATION",
        requested_value=1,
        default_value=None,
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=_any_cxx(),
    )
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )

    assert (meaning.terminal_status, meaning.reason_code) == (
        "unestablished", "meaning-witness-undeclared",
    )
    raw_admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    paper_admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="paper",
    )
    assert raw_admission.admitted is True
    assert paper_admission.admitted is True
    assert paper_admission.unestablished_meaning_macros == (
        "IZANAGI_BREAK_PERMUTATION",
    )
    assert '"unestablished_meaning_macros":["IZANAGI_BREAK_PERMUTATION"]' in (
        paper_admission.canonical_json()
    )


def test_promotion_rejects_red_runtime_meaning():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=_declaration(_case(5, expected=6)), cxx=_any_cxx(),
    )

    admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="certified-selection",
    )
    assert supply.terminal_status == "green"
    assert meaning.terminal_status == "red"
    assert admission.admitted is False
    assert admission.unestablished_meaning_macros == ()


def test_promotion_rejects_non_green_supply_effectuation():
    captured = G.capture_define_inputs(_F707)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=_declaration(_case(5)), cxx=_any_cxx(),
    )

    admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="paper",
    )
    assert supply.terminal_status == "red"
    assert meaning.terminal_status == "green"
    assert admission.admitted is False
    assert admission.unestablished_meaning_macros == ()


def test_established_meaning_uses_examined_empty_carryover_not_unset():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=_declaration(_case(5)), cxx=_any_cxx(),
    )

    admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="oracle",
    )
    assert admission.admitted is True
    assert admission.unestablished_meaning_macros == ()
    assert admission.unestablished_meaning_macros is not None


def test_empty_green_record_built_from_public_fields_is_rejected():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    request_digest = G._request_digest(request, ())
    forged_supply = _public_arm_record(
        arm="supply-effectuation",
        terminal_status="green",
        reason_code="requested-default-preprocess-different",
        request=request,
        request_digest=request_digest,
        evidence={},
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=_any_cxx(),
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.require_condition_gate_family(
            [forged_supply], [meaning], use_class="raw-measurement",
        )
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "evidence" in raised.value.detail


def test_empty_green_meaning_record_is_rejected():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    forged_meaning = _public_arm_record(
        arm="runtime-meaning",
        terminal_status="green",
        reason_code="declared-meaning-observed",
        request=request,
        request_digest=supply.request_digest,
        evidence={},
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.require_condition_gate_family(
            [supply], [forged_meaning], use_class="raw-measurement",
        )
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "evidence" in raised.value.detail


def test_green_supply_schema_rejects_missing_wrong_type_and_empty_fields():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=_any_cxx(),
    )
    mutations: list[dict[str, object]] = []
    missing = dict(supply.evidence)
    del missing["compiler_path"]
    mutations.append(missing)
    wrong_type = dict(supply.evidence)
    wrong_type["requested_replay_argv"] = list(
        wrong_type["requested_replay_argv"],
    )
    mutations.append(wrong_type)
    empty = dict(supply.evidence)
    empty["compiler_version"] = ""
    mutations.append(empty)

    for evidence in mutations:
        forged_supply = _public_arm_record(
            arm="supply-effectuation",
            terminal_status="green",
            reason_code="requested-default-preprocess-different",
            request=request,
            request_digest=supply.request_digest,
            evidence=evidence,
        )
        with pytest.raises(G.ConditionMeaningGateError) as raised:
            G.require_condition_gate_family(
                [forged_supply], [meaning], use_class="raw-measurement",
            )
        assert raised.value.reason_code == "admission-contract-invalid"
        assert "production evaluator" not in raised.value.detail


def test_green_supply_rejects_missing_cmake_evidence():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == "green"

    evidence = dict(supply.evidence)
    del evidence["cmake_path"]
    forged = _public_arm_record(
        arm="supply-effectuation",
        terminal_status="green",
        reason_code=supply.reason_code,
        request=request,
        request_digest=supply.request_digest,
        evidence=evidence,
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._validate_arm_record_integrity(forged, require_issuer=False)
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "missing=['cmake_path']" in raised.value.detail


def test_green_supply_rejects_configure_argv_for_different_cmake_path():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == "green"

    evidence = dict(supply.evidence)
    requested_argv = evidence["requested_configure_argv"]
    assert type(requested_argv) is tuple
    evidence["requested_configure_argv"] = (
        f"{evidence['cmake_path']}.different", *requested_argv[1:],
    )
    forged = _public_arm_record(
        arm="supply-effectuation",
        terminal_status="green",
        reason_code=supply.reason_code,
        request=request,
        request_digest=supply.request_digest,
        evidence=evidence,
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._validate_arm_record_integrity(forged, require_issuer=False)
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "not bound to cmake_path" in raised.value.detail


def test_green_supply_rejects_different_arm_cmake_identity():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == "green"

    evidence = dict(supply.evidence)
    control_identities = evidence["control_cmake_identities"]
    assert type(control_identities) is tuple
    evidence["control_cmake_identities"] = tuple(
        replace(
            row,
            identity=replace(row.identity, inode=row.identity.inode + 1),
            sha256="0" * 64,
        )
        for row in control_identities
    )
    forged = _public_arm_record(
        arm="supply-effectuation",
        terminal_status="green",
        reason_code=supply.reason_code,
        request=request,
        request_digest=supply.request_digest,
        evidence=evidence,
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._validate_arm_record_integrity(forged, require_issuer=False)
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "different CMake identities" in raised.value.detail


def test_unknown_terminal_status_is_rejected_before_raw_admission():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    forged_meaning = _public_arm_record(
        arm="runtime-meaning",
        terminal_status="unknown",
        reason_code="meaning-witness-undeclared",
        request=request,
        request_digest=supply.request_digest,
        evidence={"witness_declared": False},
    )

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.require_condition_gate_family(
            [supply], [forged_meaning], use_class="raw-measurement",
        )
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "terminal status" in raised.value.detail


def test_complete_public_clone_lacks_production_evaluator_issuance():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=_any_cxx(),
    )
    cloned_supply = G.ConditionArmRecord(
        record_id=supply.record_id,
        record_digest=supply.record_digest,
        arm=supply.arm,
        terminal_status=supply.terminal_status,
        reason_code=supply.reason_code,
        driver_id=supply.driver_id,
        macro=supply.macro,
        request_digest=supply.request_digest,
        evidence=supply.evidence,
    )
    assert cloned_supply.record_digest == supply.record_digest
    assert "_issuer_capability" not in supply.canonical_json()

    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G.require_condition_gate_family(
            [cloned_supply], [meaning], use_class="raw-measurement",
        )
    assert raised.value.reason_code == "admission-contract-invalid"
    assert "production evaluator" in raised.value.detail


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
    supply_domain = {
        "BACKOFF_FIXED", "BACKOFF_INCR_MILLI", "BACKOFF_MAX_US",
        "BACKOFF_NOINLINE", "BACKOFF_REQUESTED_US", "BACKOFF_TRIGGER_GATING",
        "BACKOFF_UPDATE_US", "SORT_VARIANT", "SS2PL_LOCK_IMPL",
        "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
        "IZANAGI_BREAK_PERMUTATION", "IZANAGI_BREAK_PERMUTATION_SWAP",
        "IZANAGI_BREAK_LOCK_COVERAGE", "IZANAGI_BREAK_EARLY_UNLOCK",
        "IZANAGI_BREAK_NOREAD_VALIDATION", "IZANAGI_BREAK_HIGHKEY_VALIDATION",
        "IZANAGI_BREAK_WRITE_INTENT_ERASE", "IZANAGI_BREAK_WRITE_INTENT_FORGE",
        "IZANAGI_BREAK_WRITE_INTENT_OPSWAP", "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
        "IZANAGI_BREAK_TRIGGER_MISATTR", "IZANAGI_SILO_LADDER_RUNG1",
        "IZANAGI_SILO_LADDER_RUNG1_REPORT",
    }
    assert G.SUPPLY_DOMAIN_MACROS == supply_domain
    assert G.MEANING_SUPPORTED_MACROS == {
        "BACKOFF_FIXED", *_COMPILE_TIME_BRANCH_MACROS,
    }
    assert G.MEANING_SUPPORTED_MACROS < G.SUPPLY_DOMAIN_MACROS
    assert not hasattr(G, "SUPPORTED_MACROS")
    assert G.RELATED_DEFINE_DECODE_MACROS == {
        "BACKOFF_FIXED", "BACKOFF_NOINLINE", "BACKOFF_REQUESTED_US",
        "BACKOFF_TRIGGER_GATING", "SORT_VARIANT", "SS2PL_LOCK_IMPL",
        "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
    }
    assert G.RELATED_DEFINE_DECODE_MACROS <= G.SUPPLY_DOMAIN_MACROS
    for macro in G.SUPPLY_DOMAIN_MACROS - {"BACKOFF_FIXED"}:
        with pytest.raises(ValueError, match="no runtime witness support"):
            G.MeaningWitnessDeclaration(macro, ())
    assert G.DEFINE_SPECS["SS2PL_LOCK_KIND"].companion_defines == (
        ("SS2PL_LOCK_IMPL", "1"),
    )
    assert G.DEFINE_SPECS["BACKOFF_FIXED"].inert_values == ("-1",)
    assert G.DEFINE_SPECS[
        "IZANAGI_SILO_LADDER_RUNG1_REPORT"
    ].companion_defines == (("IZANAGI_SILO_LADDER_RUNG1", "1"),)
    assert sum(
        spec.route == G.ROUTE_CMAKE_CACHE for spec in G.DEFINE_SPECS.values()
    ) == 12
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
