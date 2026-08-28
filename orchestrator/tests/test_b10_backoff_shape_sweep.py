# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import io
import json
import os
import copy
import shutil
import subprocess
import tarfile
from types import SimpleNamespace
from fractions import Fraction
from pathlib import Path

import pytest

from orchestrator.campaign import b10_backoff_shape_sweep as B
from orchestrator.campaign.layout import CampaignLayout


ROOT = Path(__file__).resolve().parents[2]


def _patch_bytes() -> bytes:
    return (ROOT / B.PATCH_REL).read_bytes()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fixture_source() -> bytes:
    return (
        b"#include <cstdint>\n"
        b"class Backoff {\n"
        b" public:\n"
        b"  static void backoff() {\n"
        b"    uint64_t start = 0;\n"
        b"    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude\n"
        b"#if BACKOFF_FIXED >= 0\n"
        + B.EXPECTED_HOLE_LINE.encode("utf-8") + b"\n"
        b"#else\n"
        b"    double now_backoff = Backoff_.load(std::memory_order_acquire);\n"
        b"#endif\n"
        b"    // EVOLVE-BLOCK-END silo-backoff-magnitude\n"
        b"    while (rdtscp() - start <= now_backoff) { pause(); }\n"
        b"  }\n"
        b"};\n"
    )


def _fixture_tree(tmp_path: Path, source: bytes | None = None) -> tuple[Path, bytes, bytes]:
    source_bytes = _fixture_source() if source is None else source
    options = b"set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING fixture)\n"
    (tmp_path / "include").mkdir()
    (tmp_path / "cmake").mkdir()
    (tmp_path / B.SOURCE_REL).write_bytes(source_bytes)
    (tmp_path / B.OPTIONS_REL).write_bytes(options)
    return tmp_path, source_bytes, options


def _passing_applied_tree(tmp_path: Path, **overrides):
    tree, source, options = _fixture_tree(tmp_path, overrides.pop("source", None))
    patch = _patch_bytes()
    defaults = {
        "patch_bytes": patch,
        "patch_sha256": _sha(patch),
        "expected_options_sha256": _sha(options),
        "expected_frame_sha256": B._frame_sha256(source),
        "digest_compute": lambda *_args: "same",
        "digest_baseline": lambda *_args: "same",
        "token_resolver": lambda *_args: "stock",
        "applied_paths": tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    }
    defaults.update(overrides)
    return B.validate_applied_tree(tree, **defaults)


def _expect_code(code: str, fn) -> None:
    with pytest.raises(B.PreflightError) as caught:
        fn()
    assert caught.value.code == code


def _complete_records(*, underexposed=None, unstable=None, uncertified=None):
    rows = []
    for workload in B.WORKLOADS:
        for block_id in B.BLOCK_IDS:
            for mean_us in B.MEANS_US:
                for shape, _code in B.SHAPES:
                    key = (workload, block_id, shape, mean_us)
                    abort_count = 9 if key == underexposed else 100
                    row = {
                        "workload": workload,
                        "block_id": block_id,
                        "shape": shape,
                        "mean_us": mean_us,
                        "median_tps": 100.0 if shape == "constant" else 101.0,
                        "abort_count": abort_count,
                        "backoff_call_count": abort_count,
                        "correctness_certified": key != uncertified,
                        "official_certification": False,
                        "unstable": key == unstable,
                        "missing": False,
                    }
                    rows.append(row)
    return rows


def _physical_residual_values(
    *, clocks_per_us: int = 2100, deviation_pct: float = 0.5,
) -> list[dict[str, object]]:
    rows = []
    for mean_us in B.MEANS_US:
        for shape, _code in B.SHAPES:
            commanded = mean_us * clocks_per_us
            realized = commanded * (1.0 + deviation_pct / 100.0)
            rows.append({
                "shape": shape,
                "mean_us": mean_us,
                "realized_mean_cycles": realized,
                "commanded_mean_cycles": commanded,
                "deviation_pct": 100.0 * (realized - commanded) / commanded,
            })
    return rows


def _spec_dict() -> dict[str, object]:
    patch_sha = _sha(_patch_bytes())
    return {
        "schema_version": "izanagi-b10-backoff-shape-preregistration/v3",
        "artifacts": {
            "patch_sha256": patch_sha,
            "formula_sha256": B.FORMULA_SHA256,
        },
        "grid": {
            "means_us": list(B.MEANS_US),
            "shapes": [
                {"name": "constant", "code": 0, "support": "mu"},
                {
                    "name": "symmetric-modulo", "code": 1,
                    "support": "closed-half-width-mu/2-through-3mu/2",
                },
                {"name": "binary", "code": 2, "support": "two-point-mu/2-or-3mu/2"},
            ],
            "encoding": "BACKOFF_FIXED=shape_code*1000+mu",
            "references": [
                {"name": "none", "back_off": 0, "backoff_fixed": -1},
                {"name": "adaptive", "back_off": 1, "backoff_fixed": -1},
                {"name": "zero-loop", "back_off": 1, "backoff_fixed": 0},
            ],
        },
        "blocks": {
            "count": 3,
            "ids": list(B.BLOCK_IDS),
            "run_order": {
                block: list(B.block_run_order(block)) for block in B.BLOCK_IDS
            },
        },
        "workloads": [
            {"name": name, **flags} for name, flags in B.WORKLOADS.items()
        ],
        "execution": {
            "threads": 48,
            "extime_s": 3,
            "performance_reps": 5,
            "correctness_reps": 5,
            "correctness_mode": "legacy+performance",
            "screening": False,
        },
        "analysis": {
            "alpha": 0.05,
            "holm_families": [
                {"workload": workload, "shape": shape}
                for workload in B.WORKLOADS
                for shape in ("symmetric-modulo", "binary")
            ],
            "permutation": {
                "method": "exact-sign-flip",
                "sided": "two-sided",
                "statistic": "absolute-sum-paired-relative-effect",
                "enumeration": "all-2^18",
                "pairs_per_family": 18,
            },
            "confidence_interval": {
                "method": "student-t-paired-block-mean",
                "confidence_level": 0.95,
                "degrees_of_freedom": 2,
                "critical_value": 4.302652729911275,
            },
            "missingness": {
                "conditions": [
                    "missing", "performance-error", "correctness-not-certified",
                    "unstable", "underexposed",
                ],
                "pair_action": "invalidate-entire-family",
                "family_action": "indeterminate",
                "indeterminate_pvalue": 1.0,
            },
            "exposure": {
                "metric": "sum-performance-rep-abort-counts",
                "minimum_calls_per_cell": 10,
                "below_minimum_action": "indeterminate",
            },
            "equivalence_margin_pct": 3.0,
            "decision_procedure": [
                "construct-all-18-within-block-paired-relative-effects",
                "mark-family-indeterminate-on-any-unusable-pair",
                "enumerate-two-sided-sign-flip-pvalue-for-each-testable-family",
                "set-indeterminate-family-pvalue-to-1",
                "holm-adjust-all-six-families",
                "different-iff-testable-and-holm-p-less-than-or-equal-alpha",
                "otherwise-not-detected",
                "report-all-cell-effects-confidence-intervals-and-equivalence-relations",
            ],
        },
        "physical_residual": {
            "measurement": "realized-backoff-loop-cycles",
            "maximum_absolute_deviation_pct_exclusive": 1.0,
            "values": _physical_residual_values(),
        },
        "external_floor_reference_widths": {
            "terminology": "external-floor-derived-reference-width",
            "power_guarantee": False,
            "values": [
                {
                    "workload": "write-heavy", "between_run_cv_pct": 0.67,
                    "reference_width_pct": 1.9, "source_environment": "linux-baremetal",
                },
                {
                    "workload": "balanced", "between_run_cv_pct": 1.07,
                    "reference_width_pct": 3.0, "source_environment": "linux-baremetal",
                },
                {
                    "workload": "read-heavy", "between_run_cv_pct": 0.22,
                    "reference_width_pct": 0.62, "source_environment": "pegasus",
                },
            ],
        },
    }


def _prereg_doc(spec: dict[str, object] | None = None) -> bytes:
    machine = _spec_dict() if spec is None else spec
    return (
        "# fixture\n\n"
        f"{B._SPEC_BEGIN}\n"
        "```json\n"
        + json.dumps(machine, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n```\n"
        f"{B._SPEC_END}\n"
    ).encode("utf-8")


def _spec() -> B.PreregistrationSpec:
    return B.parse_preregistration(_prereg_doc())


def _binding() -> B.PreregistrationBinding:
    spec = _spec()
    return B.PreregistrationBinding(
        "a" * 40, "b" * 40, spec.spec_sha256, _sha(_patch_bytes()),
        B.FORMULA_SHA256, "f" * 40, "e" * 64,
    )


def _probe_result() -> dict[str, object]:
    clocks_per_us = 2100
    calls = B.PROBE_CALLS_PER_CELL
    cells = []
    for mean_us in B.MEANS_US:
        for shape, _code in B.SHAPES:
            commanded = mean_us * clocks_per_us
            shape_extra = {
                "constant": 20.0,
                "symmetric-modulo": 24.0,
                "binary": 22.0,
            }[shape]
            realized = commanded + shape_extra
            cells.append({
                "shape": shape,
                "mean_us": mean_us,
                "encoded": B.encode(shape, mean_us),
                "calls": calls,
                "realized_mean_cycles": realized,
                "realized_median_cycles": float(commanded + 20),
                "realized_p50_cycles": float(commanded + 20),
                "realized_p99_cycles": commanded + 80,
                "realized_min_cycles": commanded + 1,
                "commanded_mean_cycles": commanded,
                "deviation_cycles": shape_extra,
                "absolute_deviation_cycles": shape_extra,
                "deviation_pct": 100.0 * shape_extra / commanded,
            })
    return {
        "schema_version": B.PROBE_SCHEMA,
        "source_commit": "a" * 40,
        "patch_sha256": _sha(_patch_bytes()),
        "formula_sha256": B.FORMULA_SHA256,
        "clocks_per_us": clocks_per_us,
        "host": {"hostname": "compute-1", "fqdn": "compute-1", "machine": "x86_64"},
        "measured_at_utc": "2026-08-26T00:00:00Z",
        "calls_per_cell": calls,
        "compile": {
            "build_system": "cmake",
            "cmake_path": "/usr/bin/cmake",
            "cmake_version": "cmake version fixture",
            "build_type": "Release",
            "cxx_standard": 20,
            "cxx_extensions": False,
            "compiler_path": "/usr/bin/g++",
            "compiler_version": "g++ fixture",
            "required_flags": [
                "-O3", "-DNDEBUG", "-Wall", "-Wextra", "-Werror", "-std=c++20",
            ],
            "compile_options_path": "cmake/CompileOptions.cmake",
            "compile_options_sha256": "b" * 64,
            "compile_commands_sha256": "c" * 64,
        },
        "cells": cells,
        "shape_differences_from_constant": B._shape_differences(cells),
        "submission": {
            "request_id": "request-1",
            "nonce": "d" * 32,
            "receipt_path": "/durable/submit-receipt.json",
            "receipt_sha256": "e" * 64,
        },
    }


def _mock_prereg_git(monkeypatch, root: Path, *, status="", blob=None, ancestor_rc=0):
    prereg = _prereg_doc()
    committed_blob = prereg if blob is None else blob
    patch = _patch_bytes()

    def fake_git(_root, *args, binary=False):
        assert Path(_root) == root.resolve()
        if args[:3] == ("rev-parse", "--verify", "HEAD^{commit}"):
            return "f" * 40 + "\n"
        if args[:2] == ("status", "--porcelain"):
            return status
        if args[:2] == ("show", "a" * 40 + ":docs/b10-backoff-shape-preregistration.md"):
            return committed_blob
        if args[:2] == ("rev-parse", "a" * 40 + ":docs/b10-backoff-shape-preregistration.md"):
            return "b" * 40 + "\n"
        if args[:2] == ("show", "a" * 40 + ":patches/silo-backoff-fixed.patch"):
            return patch
        if args[:2] == (
            "show", "f" * 40 + ":orchestrator/campaign/b10_backoff_shape_sweep.py",
        ):
            return (root / B.ANALYSIS_REL).read_bytes()
        raise AssertionError(args)

    monkeypatch.setattr(B, "_git", fake_git)
    monkeypatch.setattr(
        B.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=ancestor_rc),
    )


def _write_prereg_files(root: Path, raw: bytes | None = None) -> None:
    prereg = _prereg_doc() if raw is None else raw
    for relative, content in (
        (B.PREREG_REL, prereg),
        (B.PATCH_REL, _patch_bytes()),
        (B.ANALYSIS_REL, Path(B.__file__).read_bytes()),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _compiler() -> str:
    compiler = next(
        (path for name in ("g++-13", "g++-12", "g++") if (path := shutil.which(name))),
        None,
    )
    assert compiler is not None, "B10 semantic oracle requires a C++ compiler"
    return compiler


def _compile_expression(tmp_path: Path, line: str, stem: str = "b10_expr") -> Path:
    source = tmp_path / f"{stem}.cc"
    binary = tmp_path / stem
    source.write_text(
        "#include <cstdint>\n"
        "#include <cstdlib>\n"
        "#include <iomanip>\n"
        "#include <iostream>\n"
        "using std::uint64_t;\n"
        "int main(int argc, char** argv) {\n"
        "  if (argc != 3) return 2;\n"
        "  const uint64_t BACKOFF_FIXED = std::strtoull(argv[1], nullptr, 10);\n"
        "  const uint64_t start = std::strtoull(argv[2], nullptr, 10);\n"
        f"{line}\n"
        "  std::cout << std::setprecision(17) << now_backoff << '\\n';\n"
        "  return 0;\n"
        "}\n",
        encoding="utf-8",
    )
    compiled = subprocess.run(
        [_compiler(), "-std=c++20", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        capture_output=True, text=True,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    return binary


def _cpp_value(binary: Path, encoded: int, start: int) -> Fraction:
    completed = subprocess.run(
        [str(binary), str(encoded), str(start)], capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return Fraction(completed.stdout.strip())


def _patch_hole_line(patch: bytes) -> str:
    rows = [
        row[1:].decode("utf-8") for row in patch.splitlines()
        if row.startswith(b"+    double now_backoff =")
    ]
    assert len(rows) == 1
    return rows[0]


def test_m01_patch_path_widening_is_rejected_for_one_reason():
    mutated = _patch_bytes().replace(
        b"diff --git a/include/backoff.hh b/include/backoff.hh",
        b"diff --git a/cc/silo/transaction.cc b/cc/silo/transaction.cc",
    )
    _expect_code("patch-paths", lambda: B.validate_patch_bytes(mutated, _sha(mutated)))


def test_m02_patch_sha_bypass_witness_is_rejected_for_one_reason():
    patch = _patch_bytes()
    _expect_code("patch-sha", lambda: B.validate_patch_bytes(patch, "0" * 64))


def test_m03_duplicate_marker_is_rejected_for_one_reason(tmp_path: Path):
    source = _fixture_source().replace(
        b"    // EVOLVE-BLOCK-END silo-backoff-magnitude\n",
        b"    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude\n"
        b"    // EVOLVE-BLOCK-END silo-backoff-magnitude\n",
    )
    _expect_code("markers", lambda: _passing_applied_tree(tmp_path, source=source))


def test_m04_hole_substring_match_is_rejected_for_one_reason(tmp_path: Path):
    appended = B.EXPECTED_HOLE_LINE.encode("utf-8") + b" /* appended */"
    source = _fixture_source().replace(
        B.EXPECTED_HOLE_LINE.encode("utf-8"),
        appended,
    )
    _expect_code(
        "hole",
        lambda: _passing_applied_tree(
            tmp_path, source=source,
            expected_frame_sha256=B._frame_sha256(source, expected_line=appended),
        ),
    )


def test_m05_wait_loop_mutation_is_rejected_for_one_reason(tmp_path: Path):
    original = _fixture_source()
    mutated = original.replace(b"pause();", b"pause(); pause();")
    _expect_code(
        "frame",
        lambda: _passing_applied_tree(
            tmp_path, source=mutated,
            expected_frame_sha256=B._frame_sha256(original),
        ),
    )


def test_m06_nonstock_inert_token_is_rejected_for_one_reason(tmp_path: Path):
    _expect_code(
        "inert-token",
        lambda: _passing_applied_tree(
            tmp_path, token_resolver=lambda *_args: "1" * 64,
        ),
    )


def test_m07_unapplied_patch_is_not_a_success(tmp_path: Path):
    source = b"class Backoff { static void backoff() {} };\n"
    _fixture_tree(tmp_path, source)
    patch = _patch_bytes()
    _expect_code(
        "patch-unapplied",
        lambda: B.validate_applied_tree(
            tmp_path,
            patch_bytes=patch,
            patch_sha256=_sha(patch),
            expected_options_sha256=_sha((tmp_path / B.OPTIONS_REL).read_bytes()),
            expected_frame_sha256="0" * 64,
            digest_compute=lambda *_args: "same",
            digest_baseline=lambda *_args: "same",
            token_resolver=lambda *_args: "stock",
            applied_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
        ),
    )


def test_m08_legacy_wal_without_binding_is_rejected_for_one_reason(
    tmp_path: Path, monkeypatch,
):
    layout = CampaignLayout(str(tmp_path / "campaign"))
    Path(layout.root).mkdir()
    Path(layout.runs_dir).mkdir()
    Path(layout.lock_file).write_text("legacy", encoding="utf-8")
    Path(layout.wal_file).write_text("\n", encoding="utf-8")
    binding = _binding()
    monkeypatch.setattr(B.wal, "read_lock", lambda _layout: "legacy")
    monkeypatch.setattr(B, "_decode_lock_search_config", lambda _raw: {})
    _expect_code("resume-binding", lambda: B.assert_resumable_binding(layout, binding))


def test_preregistration_dirty_tree_is_rejected_before_blob_admission(
    tmp_path: Path, monkeypatch,
):
    _write_prereg_files(tmp_path)
    _mock_prereg_git(monkeypatch, tmp_path, status=" M tracked.py\n")
    _expect_code(
        "dirty",
        lambda: B.load_preregistration(tmp_path, "a" * 40),
    )


def test_preregistration_nonancestor_commit_is_rejected(
    tmp_path: Path, monkeypatch,
):
    _write_prereg_files(tmp_path)
    _mock_prereg_git(monkeypatch, tmp_path, ancestor_rc=1)
    _expect_code(
        "prereg-ancestor",
        lambda: B.load_preregistration(tmp_path, "a" * 40),
    )


def test_preregistration_blob_mismatch_is_rejected(
    tmp_path: Path, monkeypatch,
):
    _write_prereg_files(tmp_path)
    _mock_prereg_git(monkeypatch, tmp_path, blob=b"different\n")
    _expect_code(
        "prereg-blob",
        lambda: B.load_preregistration(tmp_path, "a" * 40),
    )


def test_preregistration_matching_commit_blob_patch_and_formula_are_accepted(
    tmp_path: Path, monkeypatch,
):
    _write_prereg_files(tmp_path)
    _mock_prereg_git(monkeypatch, tmp_path)
    prereg = B.load_preregistration(tmp_path, "a" * 40)
    assert prereg.binding.prereg_commit == "a" * 40
    assert prereg.binding.prereg_blob_sha == "b" * 40
    assert prereg.binding.spec_sha256 == prereg.spec.spec_sha256
    assert prereg.binding.patch_sha256 == _sha(_patch_bytes())
    assert prereg.binding.formula_sha256 == B.FORMULA_SHA256
    assert prereg.minimum_abort_calls == 10
    assert prereg.maximum_absolute_deviation_pct_exclusive == 1.0
    assert len(prereg.spec.physical_residual_values) == 18
    assert prereg.equivalence_margin_pct == 3.0


def test_m09_shape_code_three_is_rejected_instead_of_falling_back():
    _expect = lambda: B.decode(3002)
    with pytest.raises(ValueError, match="grid 外"):
        _expect()


def test_m10_underexposed_cell_is_indeterminate_not_success_or_failure():
    key = ("read-heavy", "block-1", "binary", 2)
    result = B.judge(_complete_records(underexposed=key), _spec())
    family = next(
        item for item in result["families"]
        if item["workload"] == "read-heavy" and item["shape"] == "binary"
    )
    assert family["outcome"] == "indeterminate"
    assert family["pairs"] == 17
    assert family["raw_p"] == 1.0


def test_m11_raw_p_cannot_bypass_holm_family_correction():
    spec = _spec()
    rows = _complete_records()
    target = ("write-heavy", "symmetric-modulo")
    changed = 0
    for row in rows:
        if row["shape"] != "constant":
            row["median_tps"] = 100.0
        if (row["workload"], row["shape"]) == target and changed < 7:
            row["median_tps"] = 120.0
            changed += 1
    result = B.judge(rows, spec)
    family = next(
        item for item in result["families"]
        if (item["workload"], item["shape"]) == target
    )
    assert family["raw_p"] < spec.alpha
    assert family["holm_p"] > spec.alpha
    assert family["outcome"] == "not-detected"


def test_m12_sign_flip_test_is_two_sided_not_fixed_one_sided():
    assert B.sign_flip_permutation_pvalue([1.0] * 5) == Fraction(2, 32)


def test_m13_actual_patch_half_width_mutation_reaches_only_cpp_bounds_oracle(
    tmp_path: Path,
):
    mutated_patch = _patch_bytes().replace(
        b"% 1000ULL) + 1ULL)", b"% 1000ULL) + 2ULL)", 1,
    )
    assert mutated_patch != _patch_bytes()
    binary = _compile_expression(tmp_path, _patch_hole_line(mutated_patch), "m13")
    mean_us = 2
    encoded = B.encode("symmetric-modulo", mean_us)
    inverse = pow(B.MIXER, -1, 1 << 64)
    violating_low = 2 * mean_us + 1
    start = (((1 << 63) | violating_low) * inverse) & B._MASK64
    value = _cpp_value(binary, encoded, start)
    assert value < Fraction(mean_us, 2)


def test_m14_different_random_mixers_are_rejected_for_one_reason():
    mutated_line = B.EXPECTED_HOLE_LINE.replace(
        "0x9e3779b97f4a7c15ULL) >> 63) *",
        "0xd1b54a32d192ed03ULL) >> 63) *",
        1,
    )
    assert mutated_line != B.EXPECTED_HOLE_LINE
    # Any odd mixer preserves the high-bit-separated pair, so the numeric pair-sum
    # oracle cannot kill this mutation. M14 targets the formula-structure gate that
    # enforces one shared mixer across both random shapes.
    _expect_code("mixer", lambda: B.validate_formula_contract(mutated_line))


def test_cpp_pair_average_is_exact_mean_for_an_alternate_odd_mixer(tmp_path: Path):
    """An alternate odd mixer keeps every constructed pair's average at mu."""
    mutated_line = B.EXPECTED_HOLE_LINE.replace(
        "0x9e3779b97f4a7c15ULL) >> 63) *",
        "0xd1b54a32d192ed03ULL) >> 63) *",
        1,
    )
    binary = _compile_expression(tmp_path, mutated_line, "alternate_odd_mixer")
    inverse = pow(B.MIXER, -1, 1 << 64)
    encoded = B.encode("binary", 25)
    for low in range(1000):
        starts = (
            (low * inverse) & B._MASK64,
            (((1 << 63) | low) * inverse) & B._MASK64,
        )
        values = [_cpp_value(binary, encoded, start) for start in starts]
        assert sum(values, Fraction()) == Fraction(50)


def test_m15_uncertified_performance_binary_sha_is_rejected_before_measurement(
    tmp_path: Path,
):
    binary = tmp_path / "perf.bin"
    binary.write_bytes(b"certified bytes")
    built_sha = B.buildcache.full_sha256(binary)
    certified = B.CertificationAttempt("attempt-1", "0" * 64)
    _expect_code(
        "perf-binary-binding",
        lambda: B.verify_performance_binary(str(binary), built_sha, certified),
    )


def test_m16_omitting_one_registered_analysis_field_is_rejected():
    mutated = copy.deepcopy(_spec_dict())
    del mutated["analysis"]["confidence_interval"]
    _expect_code("prereg-spec", lambda: B.parse_preregistration(_prereg_doc(mutated)))


def test_m17_and_p05_matching_bound_wal_is_resumable(tmp_path: Path, monkeypatch):
    layout = CampaignLayout(str(tmp_path / "campaign"))
    Path(layout.runs_dir).mkdir(parents=True)
    Path(layout.lock_file).write_text("bound", encoding="utf-8")
    Path(layout.wal_file).write_text("record\n", encoding="utf-8")
    binding = _binding()
    monkeypatch.setattr(B.wal, "read_lock", lambda _layout: "bound")
    monkeypatch.setattr(
        B, "_decode_lock_search_config",
        lambda _raw: {"preregistration_binding": binding.as_dict()},
    )
    record = SimpleNamespace(
        stage=B.STAGE_BUILD_START,
        payload={
            B.B10_BUILD_START_BINDING_KEY: binding.as_dict(),
            "build_admission": {"input_sha256": binding.binding_sha256},
        },
    )
    monkeypatch.setattr(B.wal, "read_records_checked", lambda _layout: ([record], False))
    B.assert_resumable_binding(layout, binding)


def test_p06_full_machine_spec_and_runtime_residual_are_accepted():
    spec = _spec()
    assert spec.means_us == B.MEANS_US
    assert len(spec.shapes) == 3
    assert len(spec.block_orders) == 3
    assert len(spec.workloads) == 3
    assert spec.performance_reps == spec.correctness_reps == 5
    assert len(spec.holm_families) == 6
    assert spec.pairs_per_family == 18
    assert spec.missing_family_action == "indeterminate"
    assert spec.reference_width_power_guarantee is False
    assert dict((row[0], row[1]) for row in spec.reference_widths)["read-heavy"] == 0.22
    assert len(spec.physical_residual_values) == 18
    assert B.validate_runtime_physical_residual(spec, 2100) == pytest.approx(0.5)


def test_physical_residual_table_is_required_and_placeholders_are_rejected():
    mutated = copy.deepcopy(_spec_dict())
    del mutated["physical_residual"]["values"]
    _expect_code("prereg-spec", lambda: B.parse_preregistration(_prereg_doc(mutated)))
    placeholder = copy.deepcopy(_spec_dict())
    placeholder["physical_residual"]["values"][0]["realized_mean_cycles"] = (
        "FILL_FROM_PROBE_RESULT"
    )
    _expect_code(
        "prereg-spec", lambda: B.parse_preregistration(_prereg_doc(placeholder)),
    )


def test_m18_disabling_realized_deviation_upper_bound_is_red_for_one_reason():
    mutated = copy.deepcopy(_spec_dict())
    row = mutated["physical_residual"]["values"][0]
    commanded = row["commanded_mean_cycles"]
    row["realized_mean_cycles"] = commanded * 1.02
    row["deviation_pct"] = 100.0 * (
        row["realized_mean_cycles"] - commanded
    ) / commanded
    spec = B.parse_preregistration(_prereg_doc(mutated))
    _expect_code(
        "physical-residual",
        lambda: B.validate_runtime_physical_residual(spec, 2100),
    )


def test_canonical_preregistration_path_cannot_be_overridden_from_cli():
    with pytest.raises(SystemExit) as caught:
        B.main([
            "--phase", "build",
            "--prereg-commit", "a" * 40,
            "--submission-receipt", "/tmp/not-used",
            "--preregistration", "docs/another.md",
        ])
    assert caught.value.code == 2


def test_run_phase_closed_set_is_build_verify_perf_probe():
    assert set(B.RUN_PHASES) == {"build", "verify", "perf", "probe"}


def test_probe_phase_fails_closed_at_login_site_before_any_work(monkeypatch):
    called = []

    def reject_site(_label):
        raise B.PreflightError("site", "login node")

    monkeypatch.setattr(B.pipeline, "_require_measurement_site", reject_site)
    monkeypatch.setattr(
        B.p2_2, "resolve_site_runtime",
        lambda: called.append("resolved"),
    )
    _expect_code(
        "site",
        lambda: B.run_probe(
            prereg_commit="a" * 40,
            submission_receipt="/not/read/on/login.json",
        ),
    )
    assert called == []


def test_probe_phase_does_not_start_performance_campaign(tmp_path: Path, monkeypatch):
    probe_path = tmp_path / "probe-result.json"
    monkeypatch.setattr(B, "run_probe", lambda **_kwargs: probe_path)
    monkeypatch.setattr(
        B, "run_campaign",
        lambda *_args, **_kwargs: pytest.fail("probe started performance campaign"),
    )
    assert B.run_formal(
        phase="probe", workload=None, prereg_commit="a" * 40,
        submission_receipt="/fixture/submit-receipt.json",
    ) == (probe_path, None, True)


def test_probe_harness_copies_reviewed_chkclkspan_and_wait_loop_verbatim():
    source = B._render_probe_harness(B.EXPECTED_HOLE_LINE)
    assert source.count(B.EXPECTED_HOLE_LINE) == 1
    assert source.count(B.EXPECTED_CHK_CLK_SPAN) == 1
    assert source.count(B.EXPECTED_WAIT_LOOP) == 1


def test_probe_output_schema_and_create_only(tmp_path: Path):
    result = _probe_result()
    assert B._validate_probe_result(result)["schema_version"] == B.PROBE_SCHEMA
    path = tmp_path / "probe-result.json"
    B._write_probe_result_create_only(path, result)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert B._validate_probe_result(loaded)["calls_per_cell"] == 100_000
    assert len(loaded["cells"]) == 18
    assert len(loaded["shape_differences_from_constant"]) == 12
    with pytest.raises(FileExistsError):
        B._write_probe_result_create_only(path, result)


def test_block_records_are_hash_verified_and_create_only(tmp_path: Path):
    path = tmp_path / B._block_record_filename("block-1", 0, "none")
    row = {
        "block_id": "block-1", "schedule_index": 0, "point": "none",
    }
    digest = B._write_block_record_create_only(path, row)
    loaded = B._load_block_record(path)
    assert loaded["record_sha256"] == digest
    with pytest.raises(FileExistsError):
        B._write_block_record_create_only(path, row)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["record"]["point"] = "adaptive"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    _expect_code("measurement-record", lambda: B._load_block_record(path))


def test_p01_registered_patch_hole_frame_and_inert_binding_are_accepted(tmp_path: Path):
    evidence = _passing_applied_tree(tmp_path)
    assert evidence["patch_sha256"] == _sha(_patch_bytes())
    assert len(evidence["inert_references"]) == 2
    assert {row["src_token"] for row in evidence["inert_references"]} == {"stock"}


def test_actual_patch_is_applied_in_isolation_and_inert_gate_does_not_skip(tmp_path: Path):
    compiler = next(
        (path for name in ("g++-13", "g++-12", "g++") if (path := shutil.which(name))),
        None,
    )
    assert compiler is not None, "source-digest inert witness requires a C++ compiler"
    patch_program = shutil.which("patch")
    assert patch_program is not None, "actual isolated patch witness requires patch(1)"
    archived = subprocess.run(
        ["git", "-C", str(ROOT / "external/ccbench"), "archive", B.PIN],
        capture_output=True,
    )
    assert archived.returncode == 0, archived.stderr.decode(errors="replace")
    stock = tmp_path / "stock"
    applied = tmp_path / "applied"
    stock.mkdir()
    applied.mkdir()
    for destination in (stock, applied):
        with tarfile.open(fileobj=io.BytesIO(archived.stdout), mode="r:") as archive:
            members = archive.getmembers()
            assert all(
                not member.name.startswith("/")
                and ".." not in Path(member.name).parts
                and not member.issym()
                and not member.islnk()
                for member in members
            )
            archive.extractall(destination, members=members)
    patched = subprocess.run(
        [patch_program, "-s", "-d", str(applied), "-p1", "-i", str(ROOT / B.PATCH_REL)],
        capture_output=True, text=True,
    )
    assert patched.returncode == 0, patched.stdout + patched.stderr
    hole_line, compile_options_sha256 = B._extract_applied_probe_contract(applied)
    assert hole_line == B.EXPECTED_HOLE_LINE
    assert compile_options_sha256 == _sha(
        (applied / "cmake/CompileOptions.cmake").read_bytes(),
    )
    cache = {}

    def compute_at(genome, directory, cxx):
        key = (genome.canonical(), str(directory), cxx)
        if key not in cache:
            cache[key] = B.source_digest.compute(genome, str(directory), cxx)
        return cache[key]

    def baseline(genome, _commit, _directory, cxx):
        return compute_at(genome, stock, cxx)

    def token(genome, commit, directory, cxx):
        return "stock" if compute_at(genome, directory, cxx) == baseline(
            genome, commit, directory, cxx,
        ) else "candidate"

    patch = _patch_bytes()
    evidence = B.validate_applied_tree(
        applied,
        patch_bytes=patch,
        patch_sha256=_sha(patch),
        cxx=compiler,
        digest_compute=compute_at,
        digest_baseline=baseline,
        token_resolver=token,
        applied_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    )
    assert len(evidence["inert_references"]) == 2


def test_p02_all_18_encodings_are_bijective():
    encoded = {B.encode(shape, mean_us) for shape, _code in B.SHAPES for mean_us in B.MEANS_US}
    assert len(encoded) == 18
    assert {B.decode(value) for value in encoded} == {
        (shape, mean_us) for shape, _code in B.SHAPES for mean_us in B.MEANS_US
    }


def test_p03_legacy_zero_through_999_is_numerically_identical():
    for value in range(1000):
        assert B.exact_model(value, 0) == Fraction(value)
        assert B.exact_model(value, (1 << 64) - 1) == Fraction(value)


def test_p04_three_reference_points_and_full_grid_are_accepted():
    refs = dict(B.reference_genomes())
    assert set(refs) == {"none", "adaptive", "zero-loop"}
    assert refs["none"].flags["BACK_OFF"] == 0
    assert refs["none"].flags["BACKOFF_FIXED"] == -1
    assert refs["adaptive"].flags["BACK_OFF"] == 1
    assert refs["adaptive"].flags["BACKOFF_FIXED"] == -1
    assert refs["zero-loop"].flags["BACK_OFF"] == 1
    assert refs["zero-loop"].flags["BACKOFF_FIXED"] == 0
    assert len(B.genomes()) == 21


def test_exact_finite_models_have_mean_exactly_mu_for_all_shapes():
    width = 16
    mask = (1 << width) - 1
    lower_mask = (1 << (width - 1)) - 1
    multiplier = B.MIXER & mask
    assert multiplier % 2 == 1
    for mean_us in B.MEANS_US:
        constant = []
        symmetric = []
        binary = []
        for start in range(1 << width):
            mixed = (start * multiplier) & mask
            high = mixed >> (width - 1)
            low = mixed & lower_mask
            residue = low % (2 * mean_us + 1)
            offset = 2 * mean_us - residue if high else residue
            constant.append(Fraction(mean_us))
            symmetric.append(Fraction(mean_us + offset, 2))
            binary.append(Fraction(mean_us + high * 2 * mean_us, 2))
        for values in (constant, symmetric, binary):
            assert sum(values, Fraction()) / len(values) == Fraction(mean_us)


def test_exact_model_binary_arms_and_symmetric_bounds_for_odd_means():
    for mean_us in (5, 25):
        binary = B.encode("binary", mean_us)
        # MIXER is odd, so start=0 has high bit 0.  Search one finite witness for high bit 1.
        high_start = next(
            start for start in range(1, 1000)
            if (((start * B.MIXER) & B._MASK64) >> 63) == 1
        )
        assert B.exact_model(binary, 0) == Fraction(mean_us, 2)
        assert B.exact_model(binary, high_start) == Fraction(3 * mean_us, 2)
        symmetric = B.encode("symmetric-modulo", mean_us)
        for start in (0, high_start, (1 << 64) - 1):
            value = B.exact_model(symmetric, start)
            assert Fraction(mean_us, 2) <= value <= Fraction(3 * mean_us, 2)


def test_block_orders_are_distinct_complete_identity_bearing_permutations():
    orders = [B.block_run_order(block) for block in B.BLOCK_IDS]
    expected = {name for name, _genome in B.named_genomes()}
    assert len(set(orders)) == 3
    assert all(len(order) == 21 and set(order) == expected for order in orders)


def test_config_uses_calibration_records_and_binds_preregistration():
    spec = _spec()
    binding = _binding()
    prereg = B.Preregistration(binding, B.PREREG_REL, spec)
    calibration = B.CalibrationSelection(
        path="artifact.json", sha256="e" * 64, schema_version="calibration/v2",
        records=765432, threads=48, env_tag="pegasus", clocks_per_us=2100,
        saturated=False, lower_bound_selected=True, cache_floor_warning=False,
    )
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    assert context.generator_id.value == "backoff-sweep"
    assert "backoff-sweep" in context.policy.as_preimage()["generator_registry"]
    contract = B.env_contract.GENERATIONS["pegasus"][-1].contract
    cfg = B.config_for("balanced", prereg, calibration, context, contract)
    perf = B.perf_for("balanced", calibration, spec)
    assert cfg.search_config["records"] == 765432
    assert perf.records == 765432
    assert B.pipeline.performance_correctness_workload(perf).reps == 5
    assert cfg.search_config["preregistration_binding"] == binding.as_dict()
    assert cfg.search_config[B.SEARCH_CONFIG_VERIFY_KEY] == B.VERIFY_LEGACY_PLUS_PERFORMANCE
    assert "screening" not in cfg.search_config


@pytest.mark.parametrize(
    ("quality", "saturation"),
    (
        ("rejected", {"records": 10, "saturated": True,
                      "lower_bound_selected": False, "cache_floor_warning": False}),
        ("accepted", None),
        ("accepted", {"records": 10, "saturated": False,
                      "lower_bound_selected": False, "cache_floor_warning": False}),
        ("accepted", {"records": 10, "saturated": True,
                      "lower_bound_selected": False, "cache_floor_warning": True}),
    ),
)
def test_rejected_missing_null_or_cache_warning_calibration_fails_before_run(
    monkeypatch, quality, saturation,
):
    contract = B.env_contract.GENERATIONS["pegasus"][-1].contract
    parsed = SimpleNamespace(
        saturation=saturation,
        quality=SimpleNamespace(status=quality),
        threads=48,
        env_tag="pegasus",
        clocks_per_us=2100,
    )
    loaded = SimpleNamespace(
        parsed=parsed,
        verified=SimpleNamespace(schema_version="calibration/v2"),
    )
    monkeypatch.setattr(B.p2_2, "_load_calibration_once", lambda _contract: loaded)
    _expect_code("calibration", lambda: B.load_calibration(contract, _spec()))


def test_each_generator_receipt_commits_the_exact_preregistration_bundle():
    binding = _binding()
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    evidence = B.source_digest.SourceEvidence(
        schema_version=B.source_digest.SOURCE_EVIDENCE_SCHEMA,
        source_root="/tmp/b10-source-fixture",
        ccbench_commit=B.PIN,
        genome_sha256="e" * 64,
        src_token="f" * 64,
        source_bytes_sha256="1" * 64,
        tracked_clean=False,
        tracked_diff_sha256="2" * 64,
        tracked_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    )
    receipt = B._formula_generator_resolver(context, binding)(evidence).as_receipt()
    assert receipt["generator_input_sha256"] == binding.binding_sha256
    assert receipt["source"] == evidence.as_receipt()


def test_each_build_start_carries_all_four_explicit_binding_values(monkeypatch):
    binding = _binding()
    captured = []

    def fake_log(layout, variant, stage, env_tag, payload, *args, **kwargs):
        captured.append((stage, payload))

    monkeypatch.setattr(B.wal, "log", fake_log)
    with B.bind_build_start_wal(binding):
        B.wal.log(None, "variant", B.STAGE_BUILD_START, "pegasus", {
            "build_attempt_id": "attempt",
        })
        B.wal.log(None, "variant", "verify_done", "pegasus", {"other": True})
    assert captured[0][1][B.B10_BUILD_START_BINDING_KEY] == binding.as_dict()
    assert captured[1][1] == {"other": True}
    assert B.wal.log is fake_log


def test_missing_uncertified_and_unstable_pairs_are_indeterminate():
    keys = (
        ("balanced", "block-1", "binary", 2),
        ("balanced", "block-2", "binary", 5),
    )
    for selector in ("unstable", "uncertified"):
        kwargs = {selector: keys[0]}
        result = B.judge(_complete_records(**kwargs), _spec())
        family = next(
            row for row in result["families"]
            if row["workload"] == "balanced" and row["shape"] == "binary"
        )
        assert family["outcome"] == "indeterminate"
    rows = _complete_records()
    rows = [
        row for row in rows
        if (row["workload"], row["block_id"], row["shape"], row["mean_us"]) != keys[1]
    ]
    result = B.judge(rows, _spec())
    family = next(
        row for row in result["families"]
        if row["workload"] == "balanced" and row["shape"] == "binary"
    )
    assert family["outcome"] == "indeterminate"


def test_cell_effects_cover_all_54_factorial_cells_with_ci():
    effects = B.cell_effects(_complete_records(), _spec())
    assert len(effects) == 54
    assert all(row["status"] == "estimable" for row in effects)
    assert all(row["ci95_low"] is not None and row["ci95_high"] is not None for row in effects)
    assert {row["equivalence_relation"] for row in effects} <= {
        "inside-equivalence-range", "outside-equivalence-range",
        "overlaps-equivalence-boundary",
    }


def test_nominal_wait_uses_abort_calls_times_target_mean():
    assert B._nominal_wait(123, 25) == 3075
    assert B._nominal_wait(123, 0) == 0
    assert B._nominal_wait(123, None) is None


def test_actual_patch_has_only_one_authorized_hole_line_and_exact_formula_sha():
    patch = _patch_bytes()
    assert B.validate_patch_bytes(patch, _sha(patch)) == _sha(patch)
    assert patch.count(b"+" + B.EXPECTED_HOLE_LINE.encode("utf-8")) == 1
    assert hashlib.sha256(B.EXPECTED_HOLE_LINE.encode("utf-8")).hexdigest() == B.FORMULA_SHA256


def test_actual_cpp_expression_compiles_with_werror_and_matches_fraction_model(tmp_path: Path):
    binary = _compile_expression(tmp_path, _patch_hole_line(_patch_bytes()))
    starts = (0, 1, 2, 17, (1 << 63) - 1, 1 << 63, (1 << 64) - 1)
    for shape, _code in B.SHAPES:
        for mean_us in B.MEANS_US:
            encoded = B.encode(shape, mean_us)
            for start in starts:
                assert _cpp_value(binary, encoded, start) == B.exact_model(encoded, start)

    # Independent semantic oracle: odd MIXER is a permutation.  Construct y
    # directly, invert it to start, and pair equal low63 values with opposite
    # high bits.  This checks the 2*mu sum without mirroring the C++ branches.
    assert B.MIXER & 1
    inverse = pow(B.MIXER, -1, 1 << 64)
    for shape in ("symmetric-modulo", "binary"):
        for mean_us in B.MEANS_US:
            encoded = B.encode(shape, mean_us)
            for residue in range(2 * mean_us + 1):
                low = residue
                starts_for_pair = (
                    (low * inverse) & B._MASK64,
                    (((1 << 63) | low) * inverse) & B._MASK64,
                )
                values = [_cpp_value(binary, encoded, start) for start in starts_for_pair]
                assert sum(values, Fraction()) == Fraction(2 * mean_us)
                assert all(
                    Fraction(mean_us, 2) <= value <= Fraction(3 * mean_us, 2)
                    for value in values
                )

    # The actual C++ expression, not the Python model, preserves all legacy
    # constants 0..999 at both uint64 endpoints.
    for encoded in range(1000):
        assert _cpp_value(binary, encoded, 0) == Fraction(encoded)
        assert _cpp_value(binary, encoded, B._MASK64) == Fraction(encoded)


def test_pegasus_submit_and_job_scripts_are_syntax_valid_and_use_pbs_contract():
    submit = ROOT / "tools/pegasus/submit_b10_backoff_shape.sh"
    job = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    for path in (submit, job):
        completed = subprocess.run(
            ["bash", "-n", str(path)], capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
    submit_text = submit.read_text(encoding="utf-8")
    job_text = job.read_text(encoding="utf-8")
    assert "qsub -o" in submit_text and "-v \"$export_spec\"" in submit_text
    assert "dispatch_compute.py" not in submit_text + job_text
    assert "#PBS -q gen_S" in job_text
    assert "submit-receipt.json" in submit_text + job_text
    assert "izanagi-job-evidence/b10-backoff-shape/submissions" in submit_text + job_text
    assert 'unset PYTHONPATH PYTHONHOME PYTHONSTARTUP' in submit_text
    assert 'unset PYTHONPATH PYTHONHOME PYTHONSTARTUP' in job_text
    assert "Elapse Time Limit" in job_text
    assert "SCHEDULER_ELAPSE_LIMIT_S" in job_text
    assert "REQUESTED_S=21600" not in job_text
    assert "write_failure" in job_text
    assert "on_signal" in job_text
    assert "IZANAGI_RESERVATION_JOB_ID" in job_text
    assert '--phase "$IZANAGI_B10_PHASE"' in job_text
    job_lines = job_text.splitlines()
    driver_definition_lines = [
        index for index, line in enumerate(job_lines) if line == "driver_argv=("
    ]
    assert len(driver_definition_lines) == 1
    driver_definition_line = driver_definition_lines[0]
    assert job_lines[driver_definition_line:driver_definition_line + 13] == [
        "driver_argv=(",
        '  "$PY" -B -m orchestrator.campaign.b10_backoff_shape_sweep',
        '  --phase "$IZANAGI_B10_PHASE"',
        '  --prereg-commit "$IZANAGI_B10_PREREG_COMMIT"',
        '  --submission-receipt "$SUBMIT_RECEIPT"',
        ")",
        'if [[ -n "${IZANAGI_B10_WORKLOAD:-}" ]]; then',
        '  driver_argv+=(--workload "$IZANAGI_B10_WORKLOAD")',
        "fi",
        'CURRENT_STAGE="driver-$IZANAGI_B10_PHASE"',
        "driver_rc=0",
        '(cd "$REPO_ROOT" && "${driver_argv[@]}") \\',
        '  >"$ATTEMPT_DIR/driver.stdout" 2>"$ATTEMPT_DIR/driver.stderr" || driver_rc=$?',
    ]
    assert [line for line in job_lines if "driver_argv" in line] == [
        "driver_argv=(",
        '  driver_argv+=(--workload "$IZANAGI_B10_WORKLOAD")',
        '(cd "$REPO_ROOT" && "${driver_argv[@]}") \\',
    ]
    assert [
        line for line in job_lines
        if "orchestrator.campaign.b10_backoff_shape_sweep" in line
    ] == ['  "$PY" -B -m orchestrator.campaign.b10_backoff_shape_sweep']
    assert [line for line in job_lines if '"$PY" -I -B - ' in line] == [
        '    "$PY" -I -B - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" \\',
        '  "$PY" -I -B - "$SUBMIT_RECEIPT" "$IZANAGI_B10_NONCE" "$PBS_JOBID" \\',
        '  "$PY" -I -B - "$ATTEMPT_DIR/qstat-f.stdout" "$qstat_rc" \\',
        '  readarray -t DEPENDENCY_VALUES < <("$PY" -I -B - "$REPO_ROOT/tools/pegasus/policy.json" <<\'PY\'',
        '"$PY" -I -B - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$driver_rc" \\',
    ]
    assert '"$PY" -B -m orchestrator.campaign.b10_backoff_shape_sweep' in job_text
    assert '"$PY" -I -B -m orchestrator.campaign.b10_backoff_shape_sweep' not in job_text
    assert "build|verify|perf|probe" in submit_text + job_text
    assert '[[ "$IZANAGI_B10_PHASE" != probe ]]' in job_text


def test_sanctioned_dry_run_stages_outside_worktree_and_preserves_clean_surface(
    tmp_path: Path,
):
    repo = tmp_path / "repo"
    tools = repo / "tools/pegasus"
    tools.mkdir(parents=True)
    submit_source = ROOT / "tools/pegasus/submit_b10_backoff_shape.sh"
    job_source = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    submit = tools / submit_source.name
    job = tools / job_source.name
    shutil.copy2(submit_source, submit)
    shutil.copy2(job_source, job)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/bash\n"
        "case \"$*\" in\n"
        "  *\"rev-parse --verify HEAD^{commit}\"*) printf '%s\\n' \"$FAKE_HEAD\" ;;\n"
        "  *\"rev-parse --path-format=absolute --git-common-dir\"*) printf '%s\\n' \"$FAKE_COMMON\" ;;\n"
        "  *\"merge-base --is-ancestor\"*) exit 0 ;;\n"
        "  *\"cat-file -e\"*) exit 0 ;;\n"
        "  *\"cat-file blob\"*) /bin/cat \"$FAKE_JOB\" ;;\n"
        "  *\"status --porcelain --untracked-files=all\"*) exit 0 ;;\n"
        "  *) printf 'unexpected fake git argv: %s\\n' \"$*\" >&2; exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    common = tmp_path / "common/.git"
    common.mkdir(parents=True)
    durable = tmp_path / "durable"
    before = {path.relative_to(repo) for path in repo.rglob("*")}
    env = {
        **os.environ,
        "PATH": os.fspath(fake_bin) + os.pathsep + os.environ["PATH"],
        "FAKE_HEAD": "a" * 40,
        "FAKE_COMMON": os.fspath(common),
        "FAKE_JOB": os.fspath(job),
    }
    completed = subprocess.run(
        [
            str(submit), "--dry-run", "--durable-root", str(durable),
            "--prereg-commit", "a" * 40, "--phase", "probe",
        ],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    after = {path.relative_to(repo) for path in repo.rglob("*")}
    assert after == before
    receipts = list(durable.glob("*/submit-receipt.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert receipt["dry_run"] is True
    assert receipt["phase"] == "probe"
    assert receipt["workload"] is None


def test_plain_runner_executes_this_file_instead_of_false_green():
    source = Path(__file__).read_text(encoding="utf-8")
    assert "pytest.main" in source.split("__main__", 1)[1]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
