# -*- coding: utf-8 -*-
"""Independent supply and compiler-evaluated meaning tests for T-2018."""
from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import struct
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from orchestrator.campaign import b10_backoff_shape_sweep as B10
from orchestrator.campaign import condition_meaning_gate as G
from orchestrator.campaign import screening_driver
from orchestrator.campaign.evolve_block import extract_materialized_evolve_block
from orchestrator.tests.condition_gate_test_support import (
    SORT_VARIANT_SOURCE,
    install_condition_gate_build_fixture,
)


_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).parent / "fixtures" / "condition_meaning_gate"
_SUPPLIED = _FIXTURES / "supplied"
_F707 = _FIXTURES / "f707-missing-supply"
_IGNORED = _FIXTURES / "effectuation-ignored"
_PATCH = _ROOT / "patches" / "silo-backoff-fixed.patch"
_COMPILE_TIME_BRANCH_MACROS = (
    "BACKOFF_NOINLINE",
    "IZANAGI_BREAK_PERMUTATION",
    "IZANAGI_BREAK_PERMUTATION_SWAP",
    "IZANAGI_BREAK_LOCK_COVERAGE",
    "IZANAGI_BREAK_EARLY_UNLOCK",
    "IZANAGI_BREAK_MOCC_LOCK_COVERAGE",
    "IZANAGI_BREAK_MOCC_PERMUTATION",
    "IZANAGI_BREAK_MOCC_EARLY_UNLOCK",
    "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
    "IZANAGI_BREAK_WRITE_INTENT_ERASE",
    "IZANAGI_BREAK_WRITE_INTENT_FORGE",
    "IZANAGI_BREAK_WRITE_INTENT_OPSWAP",
    "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
    "IZANAGI_BREAK_NOREAD_VALIDATION",
    "IZANAGI_BREAK_HIGHKEY_VALIDATION",
    "MOCC_TEMP_PREDICATE",
    "SORT_VARIANT",
    "IZANAGI_SILO_LADDER_RUNG1_REPORT",
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


def _append_inert_header_lines(
    root: Path,
    requested_lines: tuple[str, ...],
    control_lines: tuple[str, ...] | None = None,
) -> None:
    if control_lines is None:
        control_lines = requested_lines
    for header, lines in (
        (root / "include" / "backoff.hh", requested_lines),
        (root / "stock" / "include" / "backoff.hh", control_lines),
    ):
        content = header.read_text(encoding="utf-8")
        header.write_text(content + "".join(lines), encoding="utf-8")


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
    source_rel, _start_directive = G.CONDITIONAL_BRANCH_WITNESSES[macro]
    owner_rel = G.DEFINE_SPECS[macro].owner_tus[0]
    if source_rel != owner_rel:
        assert macro == "BACKOFF_NOINLINE"
        assert not prefix and not duplicate and not nested and close
        assert directive is None and owner_text is None
        shutil.copytree(_SUPPLIED, root)
        return root
    spec = G.DEFINE_SPECS[macro]
    owner = root / spec.owner_tus[0]
    owner.parent.mkdir(parents=True)
    if owner_text is None:
        branch = (
            (directive or _start_directive) + "\n"
            "int izanagi_compile_time_selected = 1;\n"
            + ("#endif\n" if close else "")
        )
        if nested:
            branch = "#if 1\n" + branch + "#endif\n"
        owner_text = prefix + branch + (branch if duplicate else "")
    if macro == "IZANAGI_SILO_LADDER_RUNG1_REPORT":
        owner_text = "int izanagi_owner_present = 1;\n" + owner_text
    owner.write_text(owner_text, encoding="utf-8")
    install_condition_gate_build_fixture(root, define_spec=spec)
    if macro == "IZANAGI_SILO_LADDER_RUNG1_REPORT":
        with (root / "CMakeLists.txt").open("a", encoding="utf-8") as stream:
            stream.write("target_sources(ycsb_silo.exe PRIVATE cc/silo/ycsb_silo.cc)\n")
    return root


def _patch_added_branch_declaration(macro: str) -> tuple[str, str]:
    """Derive the unique owner/directive pair from real patch additions."""
    patch = _ROOT / G.DEFINE_SPECS[macro].patch_rel
    if macro == "IZANAGI_SILO_LADDER_RUNG1_REPORT":
        expected_directive = (
            "#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT"
        )
    elif macro == "MOCC_TEMP_PREDICATE":
        expected_directive = "#if MOCC_TEMP_PREDICATE // file-scope helper"
    else:
        expected_directive = f"#if {macro}"
    current_target: str | None = None
    matches: list[tuple[str, str]] = []
    for line in patch.read_text(encoding="utf-8").splitlines():
        if line.startswith("+++ b/"):
            current_target = line.removeprefix("+++ b/")
        elif line.startswith("+") and not line.startswith("+++") \
                and line[1:] == expected_directive:
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


def test_backoff_fixed_raw_3000_is_observed_as_static_1000():
    captured = G.capture_backoff_fixed_inputs(_SUPPLIED)
    evidence = G.assert_backoff_fixed_meaning(
        captured, [_case(3000, 1000)], cxx=_any_cxx(),
    )
    assert [(row.start, row.expected_bits, row.observed_bits) for row in evidence.observations] == [
        (1, _bits(1000), _bits(1000)),
        (2, _bits(1000), _bits(1000)),
    ]


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


@pytest.mark.parametrize(
    ("macro", "requested", "default"),
    (
        pytest.param("BACKOFF_FIXED", -1, None, id="BACKOFF_FIXED=-1"),
        pytest.param("BACKOFF_NOINLINE", 0, 0, id="BACKOFF_NOINLINE=0"),
    ),
)
def test_inert_root_location_only_difference_is_green(
    tmp_path: Path,
    macro: str,
    requested: int,
    default: int | None,
):
    root = _copied_fixture(tmp_path).resolve()
    _append_inert_header_lines(
        root,
        ('    static constexpr const char *condition_gate_file = __FILE__;\n',),
    )
    request = G.make_define_request(
        driver_id="test-condition-meaning-gate",
        macro=macro,
        requested_value=requested,
        default_value=default,
    )
    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(root, stock_root=root / "stock"),
        request=request,
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "green", "stock-inert-preprocess-root-location-only",
    )
    assert evidence["comparison"] == "stock-inert-root-location-only"
    assert evidence["requested_digest"] != evidence["control_digest"]
    assert type(evidence["root_diff_line_count"]) is int
    assert evidence["root_diff_line_count"] >= 1
    assert type(evidence["root_diff_replacement_count"]) is int
    assert evidence["root_diff_replacement_count"] >= 1
    assert evidence["root_diff_source_roots"] == (
        os.fspath(root), os.fspath(root / "stock"),
    )
    assert evidence["root_diff_has_residual"] is False
    G._validate_arm_record_integrity(record)


def test_inert_semantic_difference_on_root_line_is_red(tmp_path: Path):
    root = _copied_fixture(tmp_path).resolve()
    requested_header = root / "include" / "backoff.hh"
    control_header = root / "stock" / "include" / "backoff.hh"
    requested_text = requested_header.read_text(encoding="utf-8")
    control_text = control_header.read_text(encoding="utf-8")
    old = "    double now_backoff = Backoff_.load(std::memory_order_acquire);\n"
    requested_new = (
        "    double now_backoff = Backoff_.load(std::memory_order_acquire); "
        "static constexpr const char *condition_gate_file = __FILE__;\n"
    )
    control_new = (
        "    double now_backoff = Backoff_.load(std::memory_order_acquire) + 1; "
        "static constexpr const char *condition_gate_file = __FILE__;\n"
    )
    assert requested_text.count(old) == 1
    assert control_text.count(old) == 1
    requested_header.write_text(
        requested_text.replace(old, requested_new), encoding="utf-8",
    )
    control_header.write_text(
        control_text.replace(old, control_new), encoding="utf-8",
    )

    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(root, stock_root=root / "stock"),
        request=_request(-1, default=None, stock=True),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "red", "stock-inert-mismatch",
    )
    assert evidence["root_diff_replacement_count"] >= 1
    assert evidence["root_diff_has_residual"] is True


def test_inert_root_shaped_literal_outside_closure_is_red(tmp_path: Path):
    root = _copied_fixture(tmp_path).resolve()
    control_root = root / "stock"
    _append_inert_header_lines(
        root,
        (
            f'    static constexpr const char *condition_gate_literal = "{root}'
            '/not-a-dependency.hh";\n',
            '    static constexpr const char *condition_gate_file = __FILE__;\n',
        ),
        (
            f'    static constexpr const char *condition_gate_literal = "{control_root}'
            '/not-a-dependency.hh";\n',
            '    static constexpr const char *condition_gate_file = __FILE__;\n',
        ),
    )

    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(root, stock_root=control_root),
        request=_request(-1, default=None, stock=True),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "red", "stock-inert-mismatch",
    )
    assert evidence["requested_root_dependent_builtin_paths"]
    assert evidence["control_root_dependent_builtin_paths"]
    assert evidence["root_diff_replacement_count"] >= 1
    assert evidence["root_diff_has_residual"] is True


def test_inert_root_prefixed_by_path_byte_is_red(tmp_path: Path):
    root = _copied_fixture(tmp_path).resolve()
    control_root = root / "stock"
    _append_inert_header_lines(
        root,
        (
            f'    static constexpr const char *condition_gate_literal = "xyz{root}'
            '/include/backoff.hh";\n',
            '    static constexpr const char *condition_gate_file = __FILE__;\n',
        ),
        (
            f'    static constexpr const char *condition_gate_literal = "xyz{control_root}'
            '/include/backoff.hh";\n',
            '    static constexpr const char *condition_gate_file = __FILE__;\n',
        ),
    )

    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(root, stock_root=control_root),
        request=_request(-1, default=None, stock=True),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "red", "stock-inert-mismatch",
    )
    assert evidence["requested_root_dependent_builtin_paths"]
    assert evidence["control_root_dependent_builtin_paths"]
    assert evidence["root_diff_replacement_count"] >= 1
    assert evidence["root_diff_has_residual"] is True


def test_inert_root_difference_without_code_owned_file_builtin_is_red(
    tmp_path: Path,
):
    root = _copied_fixture(tmp_path).resolve()
    control_root = root / "stock"
    _append_inert_header_lines(
        root,
        (
            f'    static constexpr const char *condition_gate_literal = "{root}'
            '/include/backoff.hh";\n',
        ),
        (
            f'    static constexpr const char *condition_gate_literal = "{control_root}'
            '/include/backoff.hh";\n',
        ),
    )

    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(root, stock_root=control_root),
        request=_request(-1, default=None, stock=True),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )

    evidence = dict(record.evidence)
    assert (record.terminal_status, record.reason_code) == (
        "red", "stock-inert-mismatch",
    )
    assert evidence["requested_root_dependent_builtin_paths"] == ()
    assert evidence["control_root_dependent_builtin_paths"] == ()
    assert evidence["root_diff_replacement_count"] >= 1
    assert evidence["root_diff_has_residual"] is False


def test_inert_root_location_evidence_binds_configure_source_roots(
    tmp_path: Path,
):
    root = _copied_fixture(tmp_path).resolve()
    _append_inert_header_lines(
        root,
        ('    static constexpr const char *condition_gate_file = __FILE__;\n',),
    )
    request = _request(-1, default=None, stock=True)
    record = G.evaluate_define_supply_effectuation(
        G.capture_define_inputs(root, stock_root=root / "stock"),
        request=request,
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )
    assert record.terminal_status == "green"

    evidence = dict(record.evidence)
    evidence["root_diff_source_roots"] = (
        "/forged/requested-source", "/forged/control-source",
    )
    forged = _public_arm_record(
        arm="supply-effectuation",
        terminal_status="green",
        reason_code=record.reason_code,
        request=request,
        request_digest=record.request_digest,
        evidence=evidence,
    )
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._validate_arm_record_integrity(forged, require_issuer=False)
    assert raised.value.reason_code == "admission-contract-invalid"


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
                fixture / patch_declaration[0]
            ).read_text(encoding="utf-8").splitlines()
            if line == patch_declaration[1]
        ]
        assert fixture_directives == [patch_declaration[1]]
        assert (patch_declaration[0], fixture_directives[0]) \
            == patch_declaration
        assert G.CONDITIONAL_BRANCH_WITNESSES[macro] == patch_declaration


@pytest.mark.parametrize("body_changed", [False, True])
def test_sort_real_structure_establishes_only_branch_selection(tmp_path, body_changed):
    source = SORT_VARIANT_SOURCE
    if body_changed:
        source = source.replace("sort(write_set_.begin(), write_set_.end());", "(void)0;")
    root = _compile_time_source_root(tmp_path, "SORT_VARIANT", owner_text=source)
    request = _compile_time_request("SORT_VARIANT")
    captured = G.capture_define_inputs(root)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == meaning.terminal_status == "green"
    admission = G.require_condition_gate_family([supply], [meaning], use_class="certified-selection")
    assert admission.admitted
    assert admission.unestablished_meaning_macros == ()


def test_sort_undef_rejects_family_with_supply_still_green(tmp_path):
    source = SORT_VARIANT_SOURCE.replace("#if SORT_VARIANT\n", "#undef SORT_VARIANT\n#if SORT_VARIANT\n")
    root = _compile_time_source_root(tmp_path, "SORT_VARIANT", owner_text=source)
    request = _compile_time_request("SORT_VARIANT")
    captured = G.capture_define_inputs(root)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == "green"
    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "compile-time-branch-selection-not-discriminating",
    )
    assert not G.require_condition_gate_family(
        [supply], [meaning], use_class="certified-selection",
    ).admitted


@pytest.mark.parametrize("body_changed", [False, True])
def test_report_companion_argv_establishes_report_only(tmp_path, body_changed):
    macro = "IZANAGI_SILO_LADDER_RUNG1_REPORT"
    root = _compile_time_source_root(tmp_path, macro)
    owner = root / "cc/silo/ycsb_silo.cc"
    assert "#define" not in owner.read_text()
    if body_changed:
        owner.write_text(owner.read_text().replace("selected = 1", "selected = 42"))
    captured = G.capture_define_inputs(root)
    request = _compile_time_request(macro)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == meaning.terminal_status == "green"
    for label, selected in (("requested", 1), ("default", 0)):
        observation = meaning.evidence[label]
        assert "-DIZANAGI_SILO_LADDER_RUNG1=1" in observation.preprocess_argv
        assert (observation.selected_count, observation.completed_count) == (selected, 1)
    other_request = _request(5)
    other_supply = G.evaluate_define_supply_effectuation(
        captured, request=other_request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    other_meaning = G.evaluate_define_runtime_meaning(
        captured, request=other_request, declaration=None, cxx=_any_cxx(),
    )
    assert other_supply.terminal_status == "green"
    admission = G.require_condition_gate_family(
        [supply, other_supply], [meaning, other_meaning], use_class="certified-selection",
    )
    assert admission.admitted
    assert admission.unestablished_meaning_macros == ("BACKOFF_FIXED",)


def test_report_missing_compile_argv_companion_rejects_meaning(tmp_path):
    """meaning arm 単体の companion 検査。

    同じ入力は supply も拒否するので family 拒否の meaning 単独帰属には使わない。
    """
    macro = "IZANAGI_SILO_LADDER_RUNG1_REPORT"
    root = _compile_time_source_root(tmp_path, macro)
    with (root / "CMakeLists.txt").open("a") as stream:
        stream.write('string(REPLACE "-DIZANAGI_SILO_LADDER_RUNG1=1" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")\n')
    request = _compile_time_request(macro)
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root), request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "companion-define-mismatch",
    )


def test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one(
    tmp_path: Path,
):
    root = _compile_time_source_root(tmp_path, "BACKOFF_NOINLINE")
    request = _compile_time_request(
        "BACKOFF_NOINLINE", requested=0, default=0,
    )
    declaration = G.declare_define_runtime_meaning(request)

    assert type(declaration) is G.ConditionalBranchMeaningDeclaration
    assert declaration.source_rel == "include/backoff.hh"
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
    requested = meaning.evidence["requested"]
    default = meaning.evidence["default"]
    assert (requested.define_value, requested.selected_count,
            requested.completed_count) == ("0", 0, 1)
    assert (default.define_value, default.selected_count,
            default.completed_count) == ("1", 1, 1)
    for observation in (requested, default):
        assert sum(
            argument.endswith(request.owner_tu)
            for argument in observation.preprocess_argv
        ) == 1
    G._validate_arm_record_integrity(meaning)
    requested_argv = tuple(
        argument.replace("-DBACKOFF_NOINLINE=0", "-DBACKOFF_NOINLINE=<VALUE>")
        for argument in requested.preprocess_argv
    )
    default_argv = tuple(
        argument.replace("-DBACKOFF_NOINLINE=1", "-DBACKOFF_NOINLINE=<VALUE>")
        for argument in default.preprocess_argv
    )
    assert requested_argv == default_argv


def test_backoff_noinline_requested_one_supply_and_meaning_are_green(
    tmp_path: Path,
):
    root = _compile_time_source_root(tmp_path, "BACKOFF_NOINLINE")
    captured = G.capture_define_inputs(root)
    request = _compile_time_request(
        "BACKOFF_NOINLINE", requested=1, default=0,
    )
    cxx = _any_cxx()
    cmake = _any_cmake()

    with G._configured_define_compile_commands(
        captured, request=request, cxx=cxx, cmake=cmake,
    ) as configured_commands:
        assert configured_commands.requested is not None
        assert configured_commands.control is not None
        assert configured_commands.requested.build_root != (
            configured_commands.control.build_root
        )
        supply = G.evaluate_define_supply_effectuation(
            captured, request=request, cxx=cxx, cmake=cmake,
            configured_commands=configured_commands,
        )
        meaning = G.evaluate_define_runtime_meaning(
            captured,
            request=request,
            declaration=G.declare_define_runtime_meaning(request),
            cxx=cxx,
            cmake=cmake,
            configured_commands=configured_commands,
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
    assert meaning.evidence["requested"].define_value == "1"
    assert meaning.evidence["default"].define_value == "0"
    assert admission.admitted is True


def test_header_shadow_preserves_directory_symlinks_and_git_link(
    tmp_path: Path,
):
    root = _compile_time_source_root(tmp_path / "source", "BACKOFF_NOINLINE")
    (root / ".git").mkdir()
    (root / "linked-target").mkdir()
    (root / "linked-target" / ".git").mkdir()
    (root / "linked-directory").symlink_to(
        root / "linked-target", target_is_directory=True,
    )
    shadow = tmp_path / "shadow"
    owner = G._write_shadow_owner_source(
        root,
        "include/backoff.hh",
        "#if BACKOFF_NOINLINE\n#endif\n",
        shadow,
        owner_tu="cc/silo/transaction.cc",
    )

    assert owner == shadow / "cc" / "silo" / "transaction.cc"
    assert owner.is_symlink()
    assert (shadow / "include").is_dir()
    assert not (shadow / "include").is_symlink()
    assert not (shadow / "include" / "backoff.hh").is_symlink()
    assert (shadow / "linked-directory").is_symlink()
    assert (shadow / ".git").is_symlink()
    assert (shadow / "linked-target" / ".git").is_symlink()


@pytest.mark.parametrize("failure", [OSError("walk"), RuntimeError("walk")])
def test_header_shadow_traversal_failure_is_structured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
):
    root = _compile_time_source_root(tmp_path / "source", "BACKOFF_NOINLINE")

    def fail_walk(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(G.os, "walk", fail_walk)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._write_shadow_owner_source(
            root,
            "include/backoff.hh",
            "#if BACKOFF_NOINLINE\n#endif\n",
            tmp_path / "shadow",
            owner_tu="cc/silo/transaction.cc",
        )
    assert raised.value.reason_code == (
        "compile-time-branch-instrumentation-failed"
    )


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


@pytest.mark.parametrize("macro", [
    "IZANAGI_BREAK_NOREAD_VALIDATION",
    "IZANAGI_BREAK_HIGHKEY_VALIDATION",
])
def test_compile_time_branch_selection_accepts_else_with_nested_analysis(
    tmp_path: Path,
    macro: str,
):
    # ADD_ANALYSIS 未定義の正例。実 patch の前処理構造を模した toy TU であり、
    # 実 patch 適用後の TU の実測ではない。
    if macro == "IZANAGI_BREAK_NOREAD_VALIDATION":
        owner_text = f"""void validation_fixture() {{
  if (true) {{
#if {macro}
    int izanagi_selected_body = 1;
#else
#if ADD_ANALYSIS
    int izanagi_default_analysis = 1;
#endif
    int izanagi_default_body = 1;
#endif
  }}
}}
"""
    else:
        owner_text = f"""void validation_fixture() {{
  if (true) {{
#if {macro}
    int izanagi_selected_body = 1;
    if (izanagi_selected_body < 1000) {{
#if ADD_ANALYSIS
      int izanagi_selected_analysis = 1;
#endif
      int izanagi_selected_lowkey_body = 1;
    }}
#else
#if ADD_ANALYSIS
    int izanagi_default_analysis = 1;
#endif
    int izanagi_default_body = 1;
#endif
  }}
}}
"""
    root = _compile_time_source_root(tmp_path, macro, owner_text=owner_text)
    captured = G.capture_define_inputs(root)
    request = _compile_time_request(macro)
    declaration = G.declare_define_runtime_meaning(request)

    assert type(declaration) is G.ConditionalBranchMeaningDeclaration
    assert declaration.source_rel == "cc/silo/transaction.cc"
    assert declaration.start_directive == f"#if {macro}"
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    meaning = G.evaluate_define_runtime_meaning(
        captured, request=request, declaration=declaration,
        cxx=_any_cxx(), cmake=_any_cmake(),
    )
    admission = G.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )

    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-compile-time-branch-selection-observed",
    )
    for label, expected in (
        ("requested", ("1", 1, 1)), ("default", ("0", 0, 1)),
    ):
        observation = meaning.evidence[label]
        assert (
            observation.define_value,
            observation.selected_count,
            observation.completed_count,
        ) == expected
    assert admission.admitted is True
    assert admission.unestablished_meaning_macros == ()


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
    request = _compile_time_request("IZANAGI_BREAK_TRIGGER_MISATTR")
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
@pytest.mark.parametrize("macro", [
    "IZANAGI_BREAK_PERMUTATION", "SORT_VARIANT", "IZANAGI_SILO_LADDER_RUNG1_REPORT",
])
def test_compile_time_factory_rejects_nonpaired_values(
    macro: str,
    requested: int,
    default: int | None,
):
    request = _compile_time_request(
        macro,
        requested=requested,
        default=default,
    )
    assert G.declare_define_runtime_meaning(request) is None


@pytest.mark.parametrize(
    ("requested", "default", "declared"),
    [
        (0, 0, True),
        (1, 0, True),
        (0, 1, False),
        (1, 1, False),
        (0, None, False),
    ],
)
def test_backoff_noinline_factory_accepts_only_default_zero_binary_requests(
    requested: int,
    default: int | None,
    declared: bool,
):
    request = _compile_time_request(
        "BACKOFF_NOINLINE", requested=requested, default=default,
    )
    declaration = G.declare_define_runtime_meaning(request)

    assert (type(declaration) is G.ConditionalBranchMeaningDeclaration) \
        is declared


def test_legacy_meaning_declaration_and_cli_stay_backoff_fixed_only(
    tmp_path: Path,
):
    assert G.MeaningWitnessDeclaration("BACKOFF_FIXED", ()) \
        == G.MeaningWitnessDeclaration("BACKOFF_FIXED", ())
    with pytest.raises(ValueError, match="no runtime witness support"):
        G.MeaningWitnessDeclaration("IZANAGI_BREAK_PERMUTATION", ())
    with pytest.raises(ValueError, match="no runtime witness support"):
        G.MeaningWitnessDeclaration("BACKOFF_NOINLINE", ())

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


def test_backoff_noinline_green_schema_rejects_nonbinary_and_same_value(
    tmp_path: Path,
):
    root = _compile_time_source_root(tmp_path, "BACKOFF_NOINLINE")
    request = _compile_time_request(
        "BACKOFF_NOINLINE", requested=0, default=0,
    )
    meaning = G.evaluate_define_runtime_meaning(
        G.capture_define_inputs(root),
        request=request,
        declaration=G.declare_define_runtime_meaning(request),
        cxx=_any_cxx(),
        cmake=_any_cmake(),
    )
    assert meaning.terminal_status == "green"

    nonbinary = dict(meaning.evidence)
    nonbinary["requested"] = replace(
        nonbinary["requested"], define_value="2",
    )
    same_value = dict(meaning.evidence)
    same_value["default"] = same_value["requested"]
    for evidence in (nonbinary, same_value):
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


def test_green_supply_rejects_cmake_identity_drift_within_arm():
    captured = G.capture_define_inputs(_SUPPLIED)
    request = _request(5)
    supply = G.evaluate_define_supply_effectuation(
        captured, request=request, cxx=_any_cxx(), cmake=_any_cmake(),
    )
    assert supply.terminal_status == "green"

    evidence = dict(supply.evidence)
    requested_identities = evidence["requested_cmake_identities"]
    control_identities = evidence["control_cmake_identities"]
    assert type(requested_identities) is tuple
    assert type(control_identities) is tuple
    before, after = control_identities
    assert (requested_identities[0].identity, requested_identities[0].sha256) \
        == (before.identity, before.sha256)
    drift_sha256 = (
        ("0" if after.sha256[0] != "0" else "1") + after.sha256[1:]
    )
    evidence["control_cmake_identities"] = (
        before,
        replace(
            after,
            identity=replace(after.identity, inode=after.identity.inode + 1),
            sha256=drift_sha256,
        ),
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
    assert "CMake identity drift" in raised.value.detail


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


def test_run_process_real_failures_report_exact_argv_and_stderr():
    failed_argv = [
        sys.executable,
        "-c",
        "import sys; sys.stderr.write('t2449-real-stderr\\n'); sys.exit(23)",
        "t2449-real-argv-element",
    ]
    with pytest.raises(G.ConditionMeaningGateError) as failed:
        G._run_process(
            failed_argv,
            timeout_reason="t2449-timeout",
            failure_reason="t2449-failure",
        )
    assert failed.value.reason_code == "t2449-failure"
    assert "rc=23" in failed.value.detail
    assert "t2449-real-stderr" in failed.value.detail
    assert "t2449-real-argv-element" in failed.value.detail
    assert f"argv={shlex.join(failed_argv)}" in failed.value.detail

    stderr_argv = [
        sys.executable,
        "-c",
        "import sys; sys.stderr.write('t2449-success-stderr\\n')",
        "t2449-stderr-argv-element",
    ]
    with pytest.raises(G.ConditionMeaningGateError) as stderr_failure:
        G._run_process(
            stderr_argv,
            timeout_reason="t2449-timeout",
            failure_reason="t2449-failure",
        )
    assert stderr_failure.value.reason_code == "t2449-failure"
    assert "successful process wrote stderr=" in stderr_failure.value.detail
    assert "t2449-success-stderr" in stderr_failure.value.detail
    assert "t2449-stderr-argv-element" in stderr_failure.value.detail
    assert f"argv={shlex.join(stderr_argv)}" in stderr_failure.value.detail


def test_run_process_timeout_and_execution_failures_report_exact_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    missing_argv = [
        os.fspath(tmp_path / "t2449-missing-command"),
        "--t2449-execution-element",
    ]
    with pytest.raises(G.ConditionMeaningGateError) as missing:
        G._run_process(
            missing_argv,
            timeout_reason="t2449-timeout",
            failure_reason="t2449-failure",
        )
    assert missing.value.reason_code == "t2449-failure"
    assert "process could not be executed" in missing.value.detail
    assert f"argv={shlex.join(missing_argv)}" in missing.value.detail

    timeout_argv = ["t2449-timeout-command", "--t2449-timeout-element"]

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(G.subprocess, "run", timeout)
    with pytest.raises(G.ConditionMeaningGateError) as timed_out:
        G._run_process(
            timeout_argv,
            timeout_reason="t2449-timeout",
            failure_reason="t2449-failure",
        )
    assert timed_out.value.reason_code == "t2449-timeout"
    assert "process exceeded 120 seconds" in timed_out.value.detail
    assert f"argv={shlex.join(timeout_argv)}" in timed_out.value.detail


def test_run_process_argv_detail_is_bounded_and_marks_truncation():
    long_element = "t2449-long-" + ("x" * 1000) + "-tail-must-be-truncated"
    argv = [
        sys.executable,
        "-c",
        "import sys; sys.stderr.write('t2449-bounded-stderr\\n'); sys.exit(31)",
        long_element,
    ]
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._run_process(
            argv,
            timeout_reason="t2449-timeout",
            failure_reason="t2449-failure",
        )
    assert "rc=31" in raised.value.detail
    assert "t2449-bounded-stderr" in raised.value.detail
    argv_detail = raised.value.detail.rsplit("; argv=", 1)[1]
    assert len(argv_detail.encode("utf-8")) <= G._PROCESS_ARGV_DETAIL_LIMIT_BYTES
    assert (
        f"limit={G._PROCESS_ARGV_DETAIL_LIMIT_BYTES} bytes" in argv_detail
    )
    assert "original=" in argv_detail
    assert "sha256=" in argv_detail
    assert "argv truncated" in argv_detail
    assert "tail-must-be-truncated" not in argv_detail


def test_run_process_argv_detail_failure_preserves_original_rejection(
    monkeypatch: pytest.MonkeyPatch,
):
    assert G._bounded_process_argv_detail([object()]) == (
        G._PROCESS_ARGV_DETAIL_UNAVAILABLE
    )

    def fail_render(_argv):
        raise RuntimeError("t2449 argv rendering failure")

    monkeypatch.setattr(G.shlex, "join", fail_render)
    assert G._bounded_process_argv_detail(["t2449-command"]) == (
        G._PROCESS_ARGV_DETAIL_UNAVAILABLE
    )

    def fail_execution(_argv, **_kwargs):
        raise OSError("t2449 original execution failure")

    monkeypatch.setattr(G.subprocess, "run", fail_execution)
    with pytest.raises(G.ConditionMeaningGateError) as raised:
        G._run_process(
            ["t2449-command"],
            timeout_reason="t2449-timeout",
            failure_reason="t2449-original-reason",
        )
    assert raised.value.reason_code == "t2449-original-reason"
    assert raised.value.detail == (
        "process could not be executed; "
        f"argv={G._PROCESS_ARGV_DETAIL_UNAVAILABLE}"
    )


def test_run_process_truncated_argv_detail_binds_full_command_and_short_is_unchanged():
    common = "t2449-common-" + ("x" * 1000)
    argv_a = ["t2449-command", common + "a"]
    argv_b = ["t2449-command", common + "b"]
    rendered_a = shlex.join(argv_a).encode("utf-8")
    rendered_b = shlex.join(argv_b).encode("utf-8")
    assert rendered_a[:G._PROCESS_ARGV_DETAIL_LIMIT_BYTES] == (
        rendered_b[:G._PROCESS_ARGV_DETAIL_LIMIT_BYTES]
    )
    assert len(rendered_a) == len(rendered_b)

    detail_a = G._bounded_process_argv_detail(argv_a)
    detail_b = G._bounded_process_argv_detail(argv_b)
    assert detail_a != detail_b
    assert f"sha256={hashlib.sha256(rendered_a).hexdigest()}" in detail_a
    assert f"sha256={hashlib.sha256(rendered_b).hexdigest()}" in detail_b

    short_argv = ["t2449-command", "short value"]
    assert G._bounded_process_argv_detail(short_argv) == shlex.join(short_argv)


def test_run_process_success_returns_completed_process_unchanged(
    monkeypatch: pytest.MonkeyPatch,
):
    def forbidden_argv_render(_argv):
        raise AssertionError("successful process must not render failure argv detail")

    monkeypatch.setattr(G, "_bounded_process_argv_detail", forbidden_argv_render)
    argv = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.write('t2449-success-stdout')",
    ]
    completed = G._run_process(
        argv,
        timeout_reason="t2449-timeout",
        failure_reason="t2449-failure",
    )
    assert completed.args == argv
    assert completed.returncode == 0
    assert completed.stdout == b"t2449-success-stdout"
    assert completed.stderr == b""


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
        "MOCC_TEMP_PREDICATE",
        "BACKOFF_FIXED", "BACKOFF_INCR_MILLI", "BACKOFF_MAX_US",
        "BACKOFF_COUNT_WINDOW", "BACKOFF_COUNT_CAP_US", "BACKOFF_STEP_ADAPT",
        "BACKOFF_STEP_MIN_MILLI", "BACKOFF_STEP_MAX_MILLI",
        "BACKOFF_DYN_CEILING", "BACKOFF_TRACE", "BACKOFF_TRACE_TERMINAL_US",
        "BACKOFF_STEP_POLICY", "BACKOFF_STEP_POLICY_SEED",
        "BACKOFF_NOINLINE", "BACKOFF_REQUESTED_US", "BACKOFF_TRIGGER_GATING",
        "BACKOFF_UPDATE_US", "SORT_VARIANT", "SS2PL_LOCK_IMPL",
        "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
        "IZANAGI_BREAK_PERMUTATION", "IZANAGI_BREAK_PERMUTATION_SWAP",
        "IZANAGI_BREAK_LOCK_COVERAGE", "IZANAGI_BREAK_EARLY_UNLOCK",
        "IZANAGI_BREAK_NOREAD_VALIDATION", "IZANAGI_BREAK_HIGHKEY_VALIDATION",
        "IZANAGI_BREAK_WRITE_INTENT_ERASE", "IZANAGI_BREAK_WRITE_INTENT_FORGE",
        "IZANAGI_BREAK_WRITE_INTENT_OPSWAP", "IZANAGI_BREAK_WRITE_INTENT_PTRSWAP",
        "IZANAGI_BREAK_MOCC_LOCK_COVERAGE", "IZANAGI_BREAK_MOCC_PERMUTATION",
        "IZANAGI_BREAK_MOCC_EARLY_UNLOCK",
        "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
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
        "MOCC_TEMP_PREDICATE",
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
    dynamic_specs = {
        macro: (
            spec.patch_rel,
            spec.owner_tus,
            spec.target,
            spec.inert_values,
        )
        for macro, spec in G.DEFINE_SPECS.items()
        if spec.patch_rel == "patches/cicada-adaptive-dynamic.patch"
    }
    assert dynamic_specs == {
        "BACKOFF_COUNT_WINDOW": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            ("0",),
        ),
        "BACKOFF_COUNT_CAP_US": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            (),
        ),
        "BACKOFF_STEP_ADAPT": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            ("0",),
        ),
        "BACKOFF_STEP_MIN_MILLI": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            (),
        ),
        "BACKOFF_STEP_MAX_MILLI": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            (),
        ),
        "BACKOFF_DYN_CEILING": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            ("0",),
        ),
        "BACKOFF_TRACE": (
            "patches/cicada-adaptive-dynamic.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            ("0",),
        ),
    }
    assert {
        macro: screening_driver._CONDITION_DEFAULTS[macro]
        for macro in dynamic_specs
    } == {
        "BACKOFF_COUNT_WINDOW": 0,
        "BACKOFF_COUNT_CAP_US": 0,
        "BACKOFF_STEP_ADAPT": 0,
        "BACKOFF_STEP_MIN_MILLI": 100000,
        "BACKOFF_STEP_MAX_MILLI": 100000,
        "BACKOFF_DYN_CEILING": 0,
        "BACKOFF_TRACE": 0,
    }
    assert G.DEFINE_SPECS[
        "IZANAGI_SILO_LADDER_RUNG1_REPORT"
    ].companion_defines == (("IZANAGI_SILO_LADDER_RUNG1", "1"),)
    assert sum(
        spec.route == G.ROUTE_CMAKE_CACHE for spec in G.DEFINE_SPECS.values()
    ) == 23
    assert sum(
        spec.route == G.ROUTE_CMAKE_CXX_FLAGS for spec in G.DEFINE_SPECS.values()
    ) == 17
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


def test_counterfactual_specs_are_exact() -> None:
    counterfactual_specs = {
        macro: (
            spec.route,
            spec.patch_rel,
            spec.owner_tus,
            spec.target,
            spec.companion_defines,
            spec.inert_values,
        )
        for macro, spec in G.DEFINE_SPECS.items()
        if spec.patch_rel == "patches/cicada-adaptive-counterfactual.patch"
    }
    assert counterfactual_specs == {
        "BACKOFF_STEP_POLICY": (
            G.ROUTE_CMAKE_CACHE,
            "patches/cicada-adaptive-counterfactual.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            (),
            ("0",),
        ),
        "BACKOFF_STEP_POLICY_SEED": (
            G.ROUTE_CMAKE_CACHE,
            "patches/cicada-adaptive-counterfactual.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            (),
            (),
        ),
        "BACKOFF_TRACE_TERMINAL_US": (
            G.ROUTE_CMAKE_CACHE,
            "patches/cicada-adaptive-counterfactual.patch",
            ("cc/silo/transaction.cc",),
            "ycsb_silo.exe",
            (),
            ("0",),
        ),
    }


def test_define_inventory_includes_counterfactual_defaults() -> None:
    patch_text = (
        _ROOT / "patches" / "cicada-adaptive-counterfactual.patch"
    ).read_text(encoding="utf-8")
    assert (
        '+set(CCBENCH_BACKOFF_STEP_POLICY 0 CACHE STRING '
        '"backoff step policy (0=stock, 1=invert, 2=randomized)")'
    ) in patch_text
    assert (
        '+set(CCBENCH_BACKOFF_STEP_POLICY_SEED 11400714819323198485 '
        'CACHE STRING "deterministic backoff step policy seed")'
    ) in patch_text
    assert (
        '+set(CCBENCH_BACKOFF_TRACE_TERMINAL_US 0 CACHE STRING '
        '"count-closed terminal trace deadline in us (0=off)")'
    ) in patch_text
    assert screening_driver._CONDITION_DEFAULTS["BACKOFF_STEP_POLICY"] == 0
    assert screening_driver._CONDITION_DEFAULTS[
        "BACKOFF_STEP_POLICY_SEED"
    ] == 11400714819323198485
    assert screening_driver._CONDITION_DEFAULTS[
        "BACKOFF_TRACE_TERMINAL_US"
    ] == 0
    assert all(
        G.DEFINE_SPECS[macro].route == G.ROUTE_CMAKE_CACHE
        for macro in (
            "BACKOFF_STEP_POLICY", "BACKOFF_STEP_POLICY_SEED",
            "BACKOFF_TRACE_TERMINAL_US",
        )
    )

    stock_requests = {
        request.macro: request
        for request in screening_driver._condition_requests_for_genome(
            G.Genome("silo", {
                "BACKOFF_STEP_POLICY": 0,
                "BACKOFF_STEP_POLICY_SEED": 11400714819323198485,
            })
        )
    }
    nonstock_requests = {
        request.macro: request
        for request in screening_driver._condition_requests_for_genome(
            G.Genome("silo", {
                "BACKOFF_STEP_POLICY": 1,
                "BACKOFF_STEP_POLICY_SEED": 11400714819323198485,
            })
        )
    }
    assert set(stock_requests) == {
        "BACKOFF_STEP_POLICY", "BACKOFF_STEP_POLICY_SEED",
    }
    assert stock_requests["BACKOFF_STEP_POLICY"].default_value == 0
    assert stock_requests["BACKOFF_STEP_POLICY"].stock_comparison is True
    assert nonstock_requests["BACKOFF_STEP_POLICY"].default_value == 0
    assert nonstock_requests["BACKOFF_STEP_POLICY"].stock_comparison is False
    assert stock_requests[
        "BACKOFF_STEP_POLICY_SEED"
    ].default_value == 11400714819323198485
    assert stock_requests["BACKOFF_STEP_POLICY_SEED"].stock_comparison is True


def test_module_claim_names_the_exact_38_define_supply_domain() -> None:
    assert "supply domain contains the 40 patch-derived defines" in G.__doc__
    assert "registered macros plus five mocc controls additionally have a bounded" in G.__doc__
    assert "compile-time witness (18 total)" in G.__doc__


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
