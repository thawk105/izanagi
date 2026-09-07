# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import re
import copy
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import replace
from types import SimpleNamespace
from fractions import Fraction
from pathlib import Path

import pytest

from orchestrator.campaign import b10_backoff_shape_sweep as B
from orchestrator.campaign.durable_root import DurableRootError
from orchestrator.campaign.layout import (
    CampaignLayout,
    write_capability_for_directory,
)


ROOT = Path(__file__).resolve().parents[2]


def _job_script_output_root(
    *, repo_root: Path, git_common_dir: Path, nonce: str,
) -> Path:
    job = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    assignments = [
        line for line in job.read_text(encoding="utf-8").splitlines()
        if line.startswith("OUTPUT_ROOT=")
    ]
    assert len(assignments) == 1
    completed = subprocess.run(
        [
            "bash", "-c",
            "set -Eeuo pipefail\n"
            "GIT_COMMON_DIR=$1\n"
            "GIT_COMMON_REPO=$2\n"
            "REPO_ROOT=$3\n"
            "IZANAGI_B10_NONCE=$4\n"
            f"{assignments[0]}\n"
            "printf '%s\\n' \"$OUTPUT_ROOT\"\n",
            "b10-output-root",
            os.fspath(git_common_dir),
            os.fspath(git_common_dir.parent),
            os.fspath(repo_root),
            nonce,
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return Path(completed.stdout.rstrip("\n"))


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


def _physical_residual_provenance() -> dict[str, object]:
    return {
        "probe_schema_version": "izanagi-b10-backoff-shape-probe/v1",
        "probe_result_sha256": (
            "6e7d8ed7d27be091ce94de4b85ac61a50e99d97167e75c4328e8a54982224bc3"
        ),
        "probe_source_commit": "8df4fa25da01311e887336b6f454f6d33ec28a2c",
        "placeholder_preregistration_commit": (
            "1549bd92794d72e05aeafe5903568f7d9023614d"
        ),
        "probe_request_id": "953543.nqsv",
        "probe_nonce": "6f8cea40fcf2193f4e4157e9c89adde1",
        "submission_receipt_sha256": (
            "782b25fc0aecf78d0aa9dfa36ef2d036c777eb171b3ebe654405b7364dc7eb54"
        ),
        "probe_host": "bnode142",
        "probe_measured_at_utc": "2026-08-27T16:26:55.628726Z",
        "probe_clocks_per_us": 2100,
        "probe_calls_per_cell": 100000,
        "probe_cells_total": 18,
        "extraction_rule": "select-probe-rows-whose-shape-is-in-the-registered-grid",
    }


def _spec_dict() -> dict[str, object]:
    patch_sha = _sha(_patch_bytes())
    return {
        "schema_version": "izanagi-b10-backoff-shape-preregistration/v5",
        "artifacts": {
            "patch_sha256": patch_sha,
            "formula_sha256": B.FORMULA_SHA256,
        },
        "registration_rules": {
            "shape_eligibility_criterion": (
                "symbolic-mean-deviation-has-no-unsuppressed-mu-coefficient-"
                "on-mixer-high-bit-frequency"
            ),
            "shape_eligibility_evidence": "formula-only-not-observed-deviation",
            "shape_exclusion_granularity": "whole-shape-only",
            "means_us_and_cell_partition": "unchanged",
            "physical_residual_cell_policy": (
                "evaluate-all-registered-cells-without-exemption"
            ),
            "throughput_decision_procedure": "unchanged-and-independent-of-a2",
            "a2_material_role": (
                "motivation-and-prior-evidence-not-parameter-selection"
            ),
            "shape_rule_formulation_timing": (
                "after-physical-residual-probe-before-shape-grid-throughput"
            ),
        },
        "grid": {
            "means_us": list(B.MEANS_US),
            "shapes": [
                {"name": "constant", "code": 0, "support": "mu"},
                {
                    "name": "symmetric-modulo", "code": 1,
                    "support": "closed-half-width-mu/2-through-3mu/2",
                },
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
                for shape in ("symmetric-modulo",)
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
                "holm-adjust-all-three-families",
                "different-iff-testable-and-holm-p-less-than-or-equal-alpha",
                "otherwise-not-detected",
                "report-all-cell-effects-confidence-intervals-and-equivalence-relations",
            ],
        },
        "physical_residual": {
            "measurement": "realized-backoff-loop-cycles",
            "maximum_absolute_deviation_pct_exclusive": 1.0,
            "provenance": _physical_residual_provenance(),
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


def _prior_block_record(
    tmp_path: Path, *, point: str = "none",
) -> tuple[B.Preregistration, dict[str, object]]:
    spec = _spec()
    binding = _binding()
    prereg = B.Preregistration(binding, B.PREREG_REL, spec)
    receipt = tmp_path / "submit-receipt.json"
    receipt_bytes = b"fixture submission receipt\n"
    receipt.write_bytes(receipt_bytes)
    block_id = "block-1"
    schedule_index = B.block_run_order(block_id).index(point)
    shape, mean_us, encoded = B._name_metadata(point)
    request_id = "request-1"
    nonce = "d" * 32
    row = {
        "schema_version": "b10-backoff-shape-block/v2",
        "official_certification": False,
        "execution_host": "compute-fixture",
        "workload": "write-heavy",
        "block_id": block_id,
        "schedule_index": schedule_index,
        "point": point,
        "shape": shape,
        "mean_us": mean_us,
        "encoded": encoded,
        "genome": dict(B.named_genomes())[point].canonical(),
        "variant_id": hashlib.sha256(point.encode("utf-8")).hexdigest()[:12],
        "source_commit": binding.analysis_commit,
        "trial": f"{request_id}-{nonce[:12]}",
        "submission_receipt": str(receipt),
        "submission_receipt_sha256": _sha(receipt_bytes),
        "request_id": request_id,
        "submission_nonce": nonce,
        "job_script_sha256": "6" * 64,
        "preregistration_binding": binding.as_dict(),
        "spec_sha256": spec.spec_sha256,
        "analysis_commit": binding.analysis_commit,
        "analysis_code_sha256": binding.analysis_code_sha256,
    }
    return prereg, row


def _legacy_v4_preregistration_binding_literal() -> dict[str, str]:
    return {
        "prereg_commit": "77b33e37d2d63b1f83d10652792c3c93eba9fe8f",
        "prereg_blob_sha": "ea910de32df83c1bb320cbe62344dc5fb3b94684",
        "spec_sha256": "9c59411476018d510c8fc5d57f203920ccd3b216e6c5f341ce6b97e45041a7c2",
        "patch_sha256": "36cd974c56c6f103d894a53048ac734d9859def266c05898d3794d2c48470832",
        "formula_sha256": "5b3d8deefed35d05597891592d7af442c96b2fa094cdebc8376b2e9bc9cd7662",
    }


def _legacy_adapter_records(
    tmp_path: Path,
) -> tuple[B.Preregistration, list[dict[str, object]]]:
    prereg, template = _prior_block_record(tmp_path)
    template.pop("execution_host")
    template["source_commit"] = B.LEGACY_WRITE_HEAVY_ANALYSIS_COMMIT
    template["preregistration_binding"] = {
        **_legacy_v4_preregistration_binding_literal(),
        "analysis_commit": B.LEGACY_WRITE_HEAVY_ANALYSIS_COMMIT,
        "analysis_code_sha256": B.LEGACY_WRITE_HEAVY_ANALYSIS_SHA256,
        "binding_sha256": B.LEGACY_WRITE_HEAVY_BINDING_SHA256,
    }
    template["spec_sha256"] = _legacy_v4_preregistration_binding_literal()[
        "spec_sha256"
    ]
    template["analysis_commit"] = B.LEGACY_WRITE_HEAVY_ANALYSIS_COMMIT
    template["analysis_code_sha256"] = B.LEGACY_WRITE_HEAVY_ANALYSIS_SHA256
    template["correctness_certified"] = True
    template["median_tps"] = 10.0
    records = []
    for block_id, order in prereg.spec.block_orders:
        for schedule_index, point in enumerate(order):
            shape, mean_us, encoded = B._name_metadata(point)
            content = {
                **template,
                "block_id": block_id,
                "schedule_index": schedule_index,
                "point": point,
                "shape": shape,
                "mean_us": mean_us,
                "encoded": encoded,
                "genome": dict(B.named_genomes())[point].canonical(),
                "variant_id": hashlib.sha256(point.encode("utf-8")).hexdigest()[:12],
            }
            records.append({**content, "record_sha256": B._sha256_json(content)})
    return prereg, records


def _legacy_balanced_adapter_records(
    tmp_path: Path,
) -> tuple[B.Preregistration, list[dict[str, object]]]:
    prereg, template = _prior_block_record(tmp_path)
    template["execution_host"] = "bnode015"
    template["workload"] = "balanced"
    template["source_commit"] = B.LEGACY_BALANCED_ANALYSIS_COMMIT
    template["preregistration_binding"] = {
        **_legacy_v4_preregistration_binding_literal(),
        "analysis_code_sha256": B.LEGACY_BALANCED_ANALYSIS_SHA256,
        "binding_sha256": B.LEGACY_BALANCED_BINDING_SHA256,
    }
    template["spec_sha256"] = _legacy_v4_preregistration_binding_literal()[
        "spec_sha256"
    ]
    template["analysis_commit"] = B.LEGACY_BALANCED_ANALYSIS_COMMIT
    template["analysis_code_sha256"] = B.LEGACY_BALANCED_ANALYSIS_SHA256
    template["correctness_certified"] = True
    template["build_attempt_id"] = "attempt-balanced"
    template["performance_binary_sha256"] = "7" * 64
    template["missing"] = False
    template["median_tps"] = 10.0
    records = []
    for block_id, order in prereg.spec.block_orders:
        for schedule_index, point in enumerate(order):
            shape, mean_us, encoded = B._name_metadata(point)
            content = {
                **template,
                "block_id": block_id,
                "schedule_index": schedule_index,
                "point": point,
                "shape": shape,
                "mean_us": mean_us,
                "encoded": encoded,
                "genome": dict(B.named_genomes())[point].canonical(),
                "variant_id": hashlib.sha256(point.encode("utf-8")).hexdigest()[:12],
            }
            records.append({**content, "record_sha256": B._sha256_json(content)})
    return prereg, records


def _rehash_record(record: dict[str, object]) -> None:
    content = dict(record)
    content.pop("record_sha256", None)
    record["record_sha256"] = B._sha256_json(content)


def _trial_predicate_fixture(
    tmp_path: Path,
) -> tuple[
    B.Preregistration,
    B.SubmissionIdentity,
    dict[str, object],
    dict[str, B.CertificationAttempt],
]:
    prereg, row = _prior_block_record(tmp_path, point="constant-mu2")
    block_id, schedule_index, point = B._trial_cell(prereg.spec)
    variant = "1" * 12
    perf_sha = "2" * 64
    attempt = B.CertificationAttempt("attempt-trial", perf_sha)
    row.update({
        "workload": "read-heavy",
        "block_id": block_id,
        "schedule_index": schedule_index,
        "point": point,
        "shape": "constant",
        "mean_us": 2,
        "encoded": B.encode("constant", 2),
        "genome": dict(B.named_genomes())[point].canonical(),
        "variant_id": variant,
        "correctness_certified": True,
        "build_attempt_id": attempt.attempt_id,
        "performance_binary_sha256": perf_sha,
        "missing": False,
    })
    _rehash_record(row)
    submission = B.SubmissionIdentity(
        receipt_path=str(row["submission_receipt"]),
        receipt_sha256=str(row["submission_receipt_sha256"]),
        request_id=str(row["request_id"]),
        nonce=str(row["submission_nonce"]),
        source_commit=str(row["source_commit"]),
        prereg_commit=prereg.binding.prereg_commit,
        job_script_sha256=str(row["job_script_sha256"]),
        phase=B.TRIAL_CELL_PHASE,
        workload="read-heavy",
    )
    return prereg, submission, row, {variant: attempt}


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
        "schema_version": "izanagi-b10-backoff-shape-probe/v2",
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
    assert dict(prereg.spec.registration_rules)["shape_eligibility_evidence"] \
        == "formula-only-not-observed-deviation"
    assert len(prereg.spec.physical_residual_values) == 12
    assert prereg.equivalence_margin_pct == 3.0


def test_m09_shape_code_three_is_rejected_instead_of_falling_back():
    _expect = lambda: B.decode(3002)
    with pytest.raises(ValueError, match="grid 外"):
        _expect()


def test_m10_underexposed_cell_is_indeterminate_not_success_or_failure():
    key = ("read-heavy", "block-1", "symmetric-modulo", 2)
    result = B.judge(_complete_records(underexposed=key), _spec())
    family = next(
        item for item in result["families"]
        if item["workload"] == "read-heavy"
        and item["shape"] == "symmetric-modulo"
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
        if (row["workload"], row["shape"]) == target and changed < 6:
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


def test_m14_dormant_cpp_code2_mixer_must_match_registered_symmetric_mixer():
    mutated_line = B.EXPECTED_HOLE_LINE.replace(
        "0x9e3779b97f4a7c15ULL) >> 63) *",
        "0xd1b54a32d192ed03ULL) >> 63) *",
        1,
    )
    assert mutated_line != B.EXPECTED_HOLE_LINE
    # Code 2 is absent from the v5 grid, Holm families, and throughput report.
    # This checks only compatibility of the byte-pinned formula's dormant code-2
    # branch with the registered symmetric branch's mixer.
    _expect_code("mixer", lambda: B.validate_formula_contract(mutated_line))


def test_dormant_cpp_code2_pair_average_is_exact_for_alternate_odd_mixer(
    tmp_path: Path,
):
    """An alternate odd mixer keeps every constructed pair's average at mu."""
    mutated_line = B.EXPECTED_HOLE_LINE.replace(
        "0x9e3779b97f4a7c15ULL) >> 63) *",
        "0xd1b54a32d192ed03ULL) >> 63) *",
        1,
    )
    binary = _compile_expression(tmp_path, mutated_line, "alternate_odd_mixer")
    inverse = pow(B.MIXER, -1, 1 << 64)
    # Dormant code 2 is byte-pinned C++ compatibility, not a registered v5 shape.
    encoded = 2025
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


def test_same_job_correctness_and_performance_binary_sha_still_match(tmp_path: Path):
    binary = tmp_path / "perf.bin"
    binary.write_bytes(b"one verify-perf job binary")
    built_sha = B.buildcache.full_sha256(binary)
    certified = B.CertificationAttempt("attempt-1", built_sha)
    assert B.verify_performance_binary(str(binary), built_sha, certified) == built_sha


def test_b10_cache_roots_are_disjoint_by_workload_and_stable_across_submissions(
    tmp_path: Path,
):
    roots = {
        workload: B._b10_workload_cache_root(tmp_path, workload)
        for workload in B.WORKLOADS
    }
    assert len(set(roots.values())) == 3
    assert all(Path(root).parent.name == "b10-workloads" for root in roots.values())

    # A retry has a new submission nonce, but the production cache address has
    # no nonce input and resolves to the same workload-owned directory.
    retry_nonces = ("0" * 32, "f" * 32)
    retry_roots = {
        _nonce: B._b10_workload_cache_root(tmp_path, "balanced")
        for _nonce in retry_nonces
    }
    assert len(set(retry_roots.values())) == 1
    assert retry_roots[retry_nonces[0]] == roots["balanced"]

    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    run_formal = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_formal"
    )
    production_calls = [
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_b10_workload_cache_root"
    ]
    assert len(production_calls) == 2
    assert {
        ast.unparse(call.args[1]) for call in production_calls
    } == {"cache_workload", "workload"}
    assert "submission.nonce" not in "\n".join(
        ast.unparse(node) for node in ast.walk(run_formal)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id in {"cache_root", "build_kwargs"}
            for target in node.targets
        )
    )

    _expect_code(
        "phase", lambda: B._b10_workload_cache_root(tmp_path, "unregistered"),
    )


def test_build_admission_identity_keeps_the_source_root_in_its_preimage():
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    binding = _binding()
    first = B.source_digest.SourceEvidence(
        schema_version=B.source_digest.SOURCE_EVIDENCE_SCHEMA,
        source_root="/tmp/b10-source-a",
        ccbench_commit=B.PIN,
        genome_sha256="e" * 64,
        src_token="f" * 64,
        source_bytes_sha256="1" * 64,
        tracked_clean=False,
        tracked_diff_sha256="2" * 64,
        tracked_paths=tuple(sorted(B.EXPECTED_PATCH_PATHS)),
    )
    second = replace(first, source_root="/tmp/b10-source-b")
    first_receipt = B.attest_generator_output(
        context, first, generator_input_sha256=binding.binding_sha256,
    )
    second_receipt = B.attest_generator_output(
        context, second, generator_input_sha256=binding.binding_sha256,
    )
    first_admission = B.derive_build_admission(
        context, first, generator_receipt=first_receipt,
    )
    second_admission = B.derive_build_admission(
        context, second, generator_receipt=second_receipt,
    )
    assert first.as_receipt()["source_root"] != second.as_receipt()["source_root"]
    assert first_admission.as_cache_identity()["source"]["source_root"] \
        == "/tmp/b10-source-a"
    assert second_admission.as_cache_identity()["source"]["source_root"] \
        == "/tmp/b10-source-b"
    assert first_admission.receipt_sha256 != second_admission.receipt_sha256


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


def test_analysis_commit_drift_is_resumable_but_analysis_code_drift_is_not(
    tmp_path: Path, monkeypatch,
):
    layout = CampaignLayout(str(tmp_path / "campaign"))
    Path(layout.runs_dir).mkdir(parents=True)
    Path(layout.lock_file).write_text("bound", encoding="utf-8")
    Path(layout.wal_file).write_text("record\n", encoding="utf-8")
    stored = _binding()
    resumed = replace(stored, analysis_commit="c" * 40)

    assert stored.analysis_commit == "f" * 40
    assert resumed.analysis_commit == "c" * 40
    for binding in (stored, resumed):
        assert "analysis_commit" not in binding.core()
        assert "analysis_commit" not in binding.as_dict()
    assert stored.core() == resumed.core()
    assert stored.as_dict() == resumed.as_dict()
    assert stored.binding_sha256 == resumed.binding_sha256

    monkeypatch.setattr(B.wal, "read_lock", lambda _layout: "bound")
    monkeypatch.setattr(
        B, "_decode_lock_search_config",
        lambda _raw: {"preregistration_binding": stored.as_dict()},
    )
    record = SimpleNamespace(
        stage=B.STAGE_BUILD_START,
        payload={
            B.B10_BUILD_START_BINDING_KEY: stored.as_dict(),
            "build_admission": {"input_sha256": stored.binding_sha256},
        },
    )
    monkeypatch.setattr(B.wal, "read_records_checked", lambda _layout: ([record], False))
    B.assert_resumable_binding(layout, resumed)

    code_drift = replace(resumed, analysis_code_sha256="d" * 64)
    assert stored.core() != code_drift.core()
    assert stored.as_dict() != code_drift.as_dict()
    assert stored.binding_sha256 != code_drift.binding_sha256
    _expect_code(
        "resume-binding",
        lambda: B.assert_resumable_binding(layout, code_drift),
    )


def test_p06_canonical_v5_machine_spec_hashes_and_runtime_residual_are_accepted():
    spec = B.parse_preregistration(
        (ROOT / B.PREREG_REL).read_bytes(),
    )
    assert spec.patch_sha256 == hashlib.sha256(
        (ROOT / "patches/silo-backoff-fixed.patch").read_bytes(),
    ).hexdigest()
    assert spec.formula_sha256 == hashlib.sha256(
        B.EXPECTED_HOLE_LINE.encode("utf-8"),
    ).hexdigest()
    assert spec.means_us == B.MEANS_US
    assert tuple(name for name, _code, _support in spec.shapes) == (
        "constant", "symmetric-modulo",
    )
    assert len(spec.block_orders) == 3
    assert len(spec.workloads) == 3
    assert spec.performance_reps == spec.correctness_reps == 5
    assert spec.holm_families == (
        ("write-heavy", "symmetric-modulo"),
        ("balanced", "symmetric-modulo"),
        ("read-heavy", "symmetric-modulo"),
    )
    assert spec.pairs_per_family == 18
    assert spec.missing_family_action == "indeterminate"
    assert spec.reference_width_terminology == "external-floor-derived-reference-width"
    assert spec.reference_width_power_guarantee is False
    assert spec.reference_widths == (
        ("write-heavy", 0.67, 1.9, "linux-baremetal"),
        ("balanced", 1.07, 3.0, "linux-baremetal"),
        ("read-heavy", 0.22, 0.62, "pegasus"),
    )
    rules = dict(spec.registration_rules)
    assert rules == {
        "shape_eligibility_criterion": (
            "symbolic-mean-deviation-has-no-unsuppressed-mu-coefficient-"
            "on-mixer-high-bit-frequency"
        ),
        "shape_eligibility_evidence": "formula-only-not-observed-deviation",
        "shape_exclusion_granularity": "whole-shape-only",
        "means_us_and_cell_partition": "unchanged",
        "physical_residual_cell_policy": (
            "evaluate-all-registered-cells-without-exemption"
        ),
        "throughput_decision_procedure": "unchanged-and-independent-of-a2",
        "a2_material_role": (
            "motivation-and-prior-evidence-not-parameter-selection"
        ),
        "shape_rule_formulation_timing": (
            "after-physical-residual-probe-before-shape-grid-throughput"
        ),
    }
    assert len(spec.physical_residual_values) == 12
    assert spec.maximum_absolute_deviation_pct_exclusive == 1.0
    assert B.validate_runtime_physical_residual(spec, 2100) \
        == pytest.approx(0.5616942857142844)


def test_v5_spec_including_binary_shape_is_rejected():
    B.parse_preregistration(_prereg_doc())
    mutated = copy.deepcopy(_spec_dict())
    mutated["grid"]["shapes"].append({
        "name": "binary", "code": 2,
        "support": "two-point-mu/2-or-3mu/2",
    })
    _expect_code("prereg-spec", lambda: B.parse_preregistration(_prereg_doc(mutated)))


@pytest.mark.parametrize("limit", (0.5, 2.0))
def test_physical_residual_limit_other_than_exact_one_is_rejected(limit: float):
    B.parse_preregistration(_prereg_doc())
    mutated = copy.deepcopy(_spec_dict())
    mutated["physical_residual"]["maximum_absolute_deviation_pct_exclusive"] = limit
    _expect_code("prereg-spec", lambda: B.parse_preregistration(_prereg_doc(mutated)))


@pytest.mark.parametrize(
    ("field", "mutated_value"),
    (
        ("probe_schema_version", "izanagi-b10-backoff-shape-probe/v2"),
        ("probe_result_sha256", "0" * 64),
        ("probe_source_commit", "0" * 40),
        ("placeholder_preregistration_commit", "1" * 40),
        ("probe_request_id", "953544.nqsv"),
        ("probe_nonce", "0" * 32),
        ("submission_receipt_sha256", "f" * 64),
        ("probe_host", "bnode143"),
        ("probe_measured_at_utc", "2026-08-27T16:26:56.628726Z"),
        ("probe_clocks_per_us", 2101),
        ("probe_calls_per_cell", 100001),
        ("probe_cells_total", 19),
        ("extraction_rule", "select-all-probe-rows"),
    ),
)
def test_physical_residual_provenance_values_are_checked_exactly(
    field: str, mutated_value: object,
):
    B.parse_preregistration(_prereg_doc())
    mutated = copy.deepcopy(_spec_dict())
    mutated["physical_residual"]["provenance"][field] = mutated_value
    _expect_code(
        "prereg-spec", lambda: B.parse_preregistration(_prereg_doc(mutated)),
    )


def test_registration_rules_values_are_checked_exactly():
    B.parse_preregistration(_prereg_doc())

    observed_deviation = copy.deepcopy(_spec_dict())
    observed_deviation["registration_rules"]["shape_eligibility_evidence"] = (
        "observed-deviation-below-limit"
    )
    _expect_code(
        "prereg-spec",
        lambda: B.parse_preregistration(_prereg_doc(observed_deviation)),
    )

    cell_exclusion = copy.deepcopy(_spec_dict())
    cell_exclusion["registration_rules"]["physical_residual_cell_policy"] = (
        "exclude-cells-by-observed-deviation"
    )
    _expect_code(
        "prereg-spec",
        lambda: B.parse_preregistration(_prereg_doc(cell_exclusion)),
    )

    extra_cell = copy.deepcopy(_spec_dict())
    extra_cell["physical_residual"]["values"].append({
        "shape": "constant",
        "mean_us": 2,
        "realized_mean_cycles": 4200.0,
        "commanded_mean_cycles": 4200,
        "deviation_pct": 0.0,
    })
    _expect_code(
        "prereg-spec",
        lambda: B.parse_preregistration(_prereg_doc(extra_cell)),
    )


def test_schema_v4_document_is_rejected_after_v5_positive_control():
    B.parse_preregistration(_prereg_doc())
    mutated = copy.deepcopy(_spec_dict())
    mutated["schema_version"] = "izanagi-b10-backoff-shape-preregistration/v4"
    _expect_code("prereg-spec", lambda: B.parse_preregistration(_prereg_doc(mutated)))


def test_physical_residual_deviation_exactly_at_the_limit_is_rejected():
    B.parse_preregistration(_prereg_doc())
    mutated = copy.deepcopy(_spec_dict())
    row = mutated["physical_residual"]["values"][0]
    row["commanded_mean_cycles"] = 4200
    row["realized_mean_cycles"] = 4242
    row["deviation_pct"] = 1.0
    spec = B.parse_preregistration(_prereg_doc(mutated))
    _expect_code(
        "physical-residual",
        lambda: B.validate_runtime_physical_residual(spec, 2100),
    )


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


def test_verify_perf_phase_is_additive_to_the_legacy_phase_set():
    assert B.FORMAL_PHASES == (
        *B.RUN_PHASES, "verify-perf", "trial-cell", "report",
    )


@pytest.mark.parametrize("workload", tuple(B.WORKLOADS))
def test_trial_cell_requires_and_accepts_each_registered_workload(workload):
    B._validate_phase_workload(B.TRIAL_CELL_PHASE, workload)
    _expect_code(
        "phase", lambda: B._validate_phase_workload(B.TRIAL_CELL_PHASE, None),
    )


def test_trial_cell_is_derived_as_first_registered_shape_cell():
    spec = _spec()
    assert B._trial_cell(spec) == ("block-1", 3, "constant-mu2")


def test_trial_run_uses_one_genome_and_summary_contract_is_one_vs_fifteen():
    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    run_formal = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_formal"
    )
    assignments = {
        target.id: node.value
        for node in ast.walk(run_formal)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        and target.id in {"selected_genomes", "expected_variants"}
    }
    selected = assignments["selected_genomes"]
    assert isinstance(selected, ast.IfExp)
    assert isinstance(selected.body, ast.Tuple) and len(selected.body.elts) == 1
    assert isinstance(selected.orelse, ast.Call)
    assert isinstance(selected.orelse.func, ast.Name)
    assert selected.orelse.func.id == "genomes"
    expected = assignments["expected_variants"]
    assert isinstance(expected, ast.IfExp)
    assert isinstance(expected.body, ast.Constant) and expected.body.value == 1
    assert isinstance(expected.orelse, ast.Name)
    assert expected.orelse.id == "POINTS_PER_BLOCK"
    run_call = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_campaign"
    )
    assert isinstance(run_call.args[1], ast.Name)
    assert run_call.args[1].id == "selected_genomes"
    config_call = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "config_for"
    )
    keywords = {keyword.arg: keyword.value for keyword in config_call.keywords}
    assert ast.unparse(keywords["search_tag"]) \
        == "TRIAL_SEARCH_TAG if phase == TRIAL_CELL_PHASE else 'formal'"
    assert ast.unparse(keywords["submission_nonce"]) \
        == "submission.nonce if phase == TRIAL_CELL_PHASE else None"
    writer_assignment = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_write_block_record_create_only"
    )
    assert [ast.unparse(target) for target in writer_assignment.targets] \
        == ["written_record_sha256"]
    predicate_call = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_trial_execution_succeeded"
    )
    predicate_keywords = {
        keyword.arg: keyword.value for keyword in predicate_call.keywords
    }
    assert ast.unparse(predicate_keywords["written_record_sha256"]) \
        == "written_record_sha256"
    prior_read = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "prior"
            for target in node.targets
        )
    )
    reject_call = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_reject_trial_prior_records"
    )
    validator_calls = sorted(
        (
            node for node in ast.walk(run_formal)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_validate_prior_block_records"
        ),
        key=lambda node: node.lineno,
    )
    assert len(validator_calls) == 2
    assert prior_read.lineno < reject_call.lineno < validator_calls[0].lineno


def test_report_phase_is_the_only_report_writer_caller():
    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    run_formal = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_formal"
    )
    writer_calls = [
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_write_reports"
    ]
    assert len(writer_calls) == 1
    report_branch = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.If) and ast.unparse(node.test) == "phase == 'report'"
    )
    assert writer_calls[0] in tuple(ast.walk(report_branch))


def test_new_v2_block_writer_records_the_reservation_binding_host():
    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    run_formal = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_formal"
    )
    host_assignments = [
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "execution_host"
            for target in node.targets
        )
    ]
    assert len(host_assignments) == 1
    assert ast.unparse(host_assignments[0].value) \
        == "reservation.read_binding(os.environ).host"
    row_assignment = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "row" for target in node.targets)
        and isinstance(node.value, ast.Dict)
        and any(
            isinstance(key, ast.Constant) and key.value == "schema_version"
            for key in node.value.keys
        )
    )
    row_values = {
        key.value: value
        for key, value in zip(row_assignment.value.keys, row_assignment.value.values)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert ast.unparse(row_values["execution_host"]) == "execution_host"
    assert isinstance(row_values["schema_version"], ast.Constant)
    assert row_values["schema_version"].value == "b10-backoff-shape-block/v2"


def test_verify_perf_reuses_one_checkout_and_stops_before_perf_on_abort():
    source = Path(B.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    run_formal = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_formal"
    )

    calls = [node for node in ast.walk(run_formal) if isinstance(node, ast.Call)]
    named_calls = [
        node for node in calls
        if isinstance(node.func, ast.Name)
    ]
    assert sum(node.func.id == "run_campaign" for node in named_calls) == 1
    assert sum(node.func.id == "checkout" for node in named_calls) == 1
    assert sum(node.func.id == "_certification_attempts" for node in named_calls) == 1
    assert sum(node.func.id == "_perf_binary" for node in named_calls) == 1

    run_call = next(node for node in named_calls if node.func.id == "run_campaign")
    run_keywords = {keyword.arg: keyword.value for keyword in run_call.keywords}
    assert isinstance(run_keywords["do_bench"], ast.Constant)
    assert run_keywords["do_bench"].value is False

    verify_branch = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.If)
        and ast.unparse(node.test)
        == "phase in {'verify', 'verify-perf', 'trial-cell'}"
    )
    abort_guard = verify_branch.body[-1]
    assert isinstance(abort_guard, ast.If)
    assert ast.unparse(abort_guard.test) == (
        "phase == 'verify' or summary.aborted != 0"
    )
    assert len(abort_guard.body) == 1
    assert isinstance(abort_guard.body[0], ast.Return)

    checkout_scope = next(
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.With)
        and any(
            isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Name)
            and item.context_expr.func.id == "checkout"
            for item in node.items
        )
    )
    checkout_calls = {
        node.func.id for node in ast.walk(checkout_scope)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {"run_campaign", "_certification_attempts", "_perf_binary"} \
        <= checkout_calls


def test_formal_build_requires_exact_path_policy_and_job_exports_it(monkeypatch):
    job = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    job_source = job.read_text(encoding="utf-8")
    expected_export = (
        f'export {B.buildcache.B10_BINARY_PATH_POLICY_ENV}='
        f'"{B.buildcache.B10_BINARY_PATH_POLICY}"'
    )
    assert job_source.splitlines().count(expected_export) == 1
    assert job_source.count("-DBUILD_SHARED_LIBS=OFF") == 2

    monkeypatch.delenv(B.buildcache.B10_BINARY_PATH_POLICY_ENV, raising=False)
    _expect_code(
        "binary-path-policy",
        lambda: B.run_formal(
            phase="build", workload=None, prereg_commit="a" * 40,
            submission_receipt="/not/read/without/policy.json",
        ),
    )
    monkeypatch.setenv(
        B.buildcache.B10_BINARY_PATH_POLICY_ENV,
        B.buildcache.B10_BINARY_PATH_POLICY,
    )
    B._require_binary_path_policy()
    monkeypatch.setenv(B.buildcache.B10_BINARY_PATH_POLICY_ENV, "unknown/v1")
    _expect_code("binary-path-policy", B._require_binary_path_policy)


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
    assert B._validate_probe_result(result)["schema_version"] \
        == "izanagi-b10-backoff-shape-probe/v2"
    legacy = copy.deepcopy(result)
    legacy["schema_version"] = "izanagi-b10-backoff-shape-probe/v1"
    _expect_code("probe-schema", lambda: B._validate_probe_result(legacy))
    path = tmp_path / "probe-result.json"
    B._write_probe_result_create_only(path, result)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert B._validate_probe_result(loaded)["calls_per_cell"] == 100_000
    assert len(loaded["cells"]) == 12
    assert len(loaded["shape_differences_from_constant"]) == 6
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


def test_prior_block_record_with_canonical_point_metadata_is_accepted(
    tmp_path: Path,
):
    prereg, row = _prior_block_record(tmp_path, point="symmetric-modulo-mu2")
    indexed = B._validate_prior_block_records(
        [row], workload="write-heavy", prereg=prereg,
    )
    assert indexed == {("block-1", "symmetric-modulo-mu2"): row}


def test_current_v2_block_record_requires_nonempty_execution_host(tmp_path: Path):
    prereg, row = _prior_block_record(tmp_path)
    for invalid in (None, "", 1):
        candidate = copy.deepcopy(row)
        if invalid is None:
            del candidate["execution_host"]
        else:
            candidate["execution_host"] = invalid
        _expect_code(
            "resume-binding",
            lambda candidate=candidate: B._validate_prior_block_records(
                [candidate], workload="write-heavy", prereg=prereg,
            ),
        )


def test_current_v2_block_record_requires_well_formed_variant_id(tmp_path: Path):
    prereg, row = _prior_block_record(tmp_path)
    for invalid in (None, "", 1, "not-a-hash", "A" * 12, "0" * 13):
        candidate = copy.deepcopy(row)
        if invalid is None:
            del candidate["variant_id"]
        else:
            candidate["variant_id"] = invalid
        _expect_code(
            "resume-binding",
            lambda candidate=candidate: B._validate_prior_block_records(
                [candidate], workload="write-heavy", prereg=prereg,
            ),
        )


def test_trial_exact_cell_gate_accepts_only_derived_logical_key(tmp_path: Path):
    prereg, _submission, row, _attempts = _trial_predicate_fixture(tmp_path)
    indexed = {(str(row["block_id"]), str(row["point"])): row}
    B._require_exact_trial_cell(indexed, prereg=prereg)
    _expect_code(
        "trial-cell", lambda: B._require_exact_trial_cell({}, prereg=prereg),
    )
    _expect_code(
        "trial-cell",
        lambda: B._require_exact_trial_cell(
            {**indexed, ("block-1", "adaptive"): row}, prereg=prereg,
        ),
    )


def test_trial_rejects_preexisting_self_hashed_record_even_with_matching_wal(
    tmp_path: Path,
):
    prereg, submission, row, attempts = _trial_predicate_fixture(tmp_path)
    indexed = B._validate_prior_block_records(
        [row], workload="read-heavy", prereg=prereg,
    )
    assert indexed == {(str(row["block_id"]), str(row["point"])): row}
    assert B._trial_execution_succeeded(
        [row], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256=str(row["record_sha256"]),
    )
    _expect_code(
        "trial-cell",
        lambda: B._reject_trial_prior_records(B.TRIAL_CELL_PHASE, [row]),
    )
    B._reject_trial_prior_records("perf", [row])


def test_trial_success_predicate_matches_same_submission_certification(
    tmp_path: Path,
):
    prereg, submission, row, attempts = _trial_predicate_fixture(tmp_path)
    assert B._trial_execution_succeeded(
        [row], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256=str(row["record_sha256"]),
    )
    assert not B._trial_execution_succeeded(
        [], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256=str(row["record_sha256"]),
    )
    assert not B._trial_execution_succeeded(
        [row, row], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256=str(row["record_sha256"]),
    )


def test_trial_success_predicate_requires_this_invocations_written_record_digest(
    tmp_path: Path,
):
    prereg, submission, row, attempts = _trial_predicate_fixture(tmp_path)
    assert not B._trial_execution_succeeded(
        [row], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256="f" * 64,
    )
    assert B._trial_execution_succeeded(
        [row], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256=str(row["record_sha256"]),
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "host-missing", "perf-sha-missing", "perf-sha-malformed",
        "perf-sha-mismatch", "attempt-id-mismatch", "missing",
        "uncertified", "certified-attempt-missing", "request-id-mismatch",
        "nonce-mismatch", "receipt-sha-mismatch",
    ),
)
def test_trial_success_predicate_rejects_each_incomplete_binding(
    tmp_path: Path, mutation: str,
):
    prereg, submission, row, attempts = _trial_predicate_fixture(tmp_path)
    if mutation == "host-missing":
        del row["execution_host"]
    elif mutation == "perf-sha-missing":
        row["performance_binary_sha256"] = None
    elif mutation == "perf-sha-malformed":
        row["performance_binary_sha256"] = "not-a-sha"
    elif mutation == "perf-sha-mismatch":
        row["performance_binary_sha256"] = "3" * 64
    elif mutation == "attempt-id-mismatch":
        row["build_attempt_id"] = "other-attempt"
    elif mutation == "missing":
        row["missing"] = True
    elif mutation == "uncertified":
        row["correctness_certified"] = False
    elif mutation == "certified-attempt-missing":
        attempts = {}
    elif mutation == "request-id-mismatch":
        row["request_id"] = "old-request"
        row["trial"] = f"old-request-{str(row['submission_nonce'])[:12]}"
    elif mutation == "nonce-mismatch":
        row["submission_nonce"] = "e" * 32
        row["trial"] = f"{row['request_id']}-{'e' * 12}"
    else:
        old_receipt = tmp_path / "old-submit-receipt.json"
        old_receipt.write_bytes(b"old fixture submission receipt\n")
        row["submission_receipt"] = str(old_receipt)
        row["submission_receipt_sha256"] = _sha(old_receipt.read_bytes())
    _rehash_record(row)
    assert not B._trial_execution_succeeded(
        [row], prereg=prereg, attempts=attempts, submission=submission,
        written_record_sha256=str(row["record_sha256"]),
    )


def test_trial_report_is_create_only_and_contains_bound_outcome(tmp_path: Path):
    prereg, submission, row, attempts = _trial_predicate_fixture(tmp_path)
    attempt = attempts[str(row["variant_id"])]
    path = B._write_trial_report_create_only(
        tmp_path / "trial-campaign",
        campaign_id="trial-campaign-id",
        phase=B.TRIAL_CELL_PHASE,
        workload="read-heavy",
        submission=submission,
        record=row,
        certified_attempt=attempt,
        succeeded=True,
        preregistration_binding=prereg.binding.as_dict(),
    )
    assert path == (
        tmp_path / "trial-campaign" / "reports" / "trial"
        / f"{submission.nonce}.json"
    )
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report == {
        "schema_version": "b10-backoff-shape-trial-report/v1",
        "campaign_id": "trial-campaign-id",
        "phase": B.TRIAL_CELL_PHASE,
        "workload": "read-heavy",
        "submission_identity": {
            "request_id": submission.request_id,
            "nonce": submission.nonce,
            "receipt_path": submission.receipt_path,
            "receipt_sha256": submission.receipt_sha256,
            "source_commit": submission.source_commit,
        },
        "record_sha256": row["record_sha256"],
        "execution_host": "compute-fixture",
        "certified_attempt": {
            "build_attempt_id": attempt.attempt_id,
            "performance_binary_sha256": attempt.perf_bin_sha256,
        },
        "measurement_succeeded": True,
        "success_predicate": True,
        "preregistration_binding": prereg.binding.as_dict(),
    }
    with pytest.raises(FileExistsError):
        B._write_trial_report_create_only(
            tmp_path / "trial-campaign",
            campaign_id="trial-campaign-id",
            phase=B.TRIAL_CELL_PHASE,
            workload="read-heavy",
            submission=submission,
            record=row,
            certified_attempt=attempt,
            succeeded=True,
            preregistration_binding=prereg.binding.as_dict(),
        )


@pytest.mark.parametrize(("execution_complete", "expected_rc"), ((True, 0), (False, 1)))
def test_trial_main_return_code_is_exact_success_predicate(
    monkeypatch: pytest.MonkeyPatch, execution_complete: bool, expected_rc: int,
):
    monkeypatch.setattr(
        B, "run_formal",
        lambda **_kwargs: (Path("trial-report.json"), None, execution_complete),
    )
    assert B.main([
        "--phase", B.TRIAL_CELL_PHASE,
        "--workload", "balanced",
        "--prereg-commit", "a" * 40,
        "--submission-receipt", "/fixture/submit-receipt.json",
    ]) == expected_rc


def test_e3de15eb_legacy_adapter_enforces_injected_exact_digest_set(
    tmp_path: Path,
):
    prereg, records = _legacy_adapter_records(tmp_path)
    expected_digests = frozenset(row["record_sha256"] for row in records)
    frozen_digests = sorted(B.LEGACY_WRITE_HEAVY_RECORD_SHA256S)
    assert B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID \
        == "b10-backoff-shape-silo-write-heavy-formal-e3de15eb"
    assert len(frozen_digests) == len(set(frozen_digests)) == 45
    assert "ceeb007ffca91a254bc261e2ff2e8b2f3255edd07d5e5409b47a2d8900496349" \
        in frozen_digests
    expected_binding = {
        **_legacy_v4_preregistration_binding_literal(),
        "analysis_commit": B.LEGACY_WRITE_HEAVY_ANALYSIS_COMMIT,
        "analysis_code_sha256": B.LEGACY_WRITE_HEAVY_ANALYSIS_SHA256,
        "binding_sha256": B.LEGACY_WRITE_HEAVY_BINDING_SHA256,
    }
    assert B._legacy_write_heavy_binding(prereg) == expected_binding
    assert records[0]["preregistration_binding"] == expected_binding
    assert prereg.binding.patch_sha256 != expected_binding["patch_sha256"]
    assert prereg.spec.spec_sha256 != records[0]["spec_sha256"]
    B._require_legacy_record_digests(frozen_digests)
    assert len(records) == len(expected_digests) == 45
    indexed = B._validate_legacy_write_heavy_records(
        records,
        campaign_id=B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID,
        prereg=prereg,
        expected_record_digests=expected_digests,
    )
    assert len(indexed) == 45

    mutated = copy.deepcopy(records)
    changed = mutated[0]
    changed["correctness_certified"] = False
    content = dict(changed)
    content.pop("record_sha256")
    changed["record_sha256"] = B._sha256_json(content)
    assert changed["record_sha256"] not in expected_digests
    _expect_code(
        "legacy-record",
        lambda: B._validate_legacy_write_heavy_records(
            mutated,
            campaign_id=B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID,
            prereg=prereg,
            expected_record_digests=expected_digests,
        ),
    )


def test_e3de15eb_legacy_adapter_rejects_current_v5_patch_binding(
    tmp_path: Path,
):
    prereg, records = _legacy_adapter_records(tmp_path)
    changed = records[0]
    old_digest = changed["record_sha256"]
    mixed_binding = dict(changed["preregistration_binding"])
    mixed_binding["patch_sha256"] = prereg.binding.patch_sha256
    assert mixed_binding["patch_sha256"] \
        != _legacy_v4_preregistration_binding_literal()["patch_sha256"]
    changed["preregistration_binding"] = mixed_binding
    _rehash_record(changed)
    expected_digests = {row["record_sha256"] for row in records}
    assert changed["record_sha256"] != old_digest
    _expect_code(
        "legacy-record",
        lambda: B._validate_legacy_write_heavy_records(
            records,
            campaign_id=B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID,
            prereg=prereg,
            expected_record_digests=expected_digests,
        ),
    )


def test_e3de15eb_legacy_adapter_rejects_other_campaign_id():
    _expect_code(
        "legacy-record",
        lambda: B._validate_legacy_write_heavy_records(
            [], campaign_id="b10-backoff-shape-silo-write-heavy-formal-other",
            prereg=B.Preregistration(_binding(), B.PREREG_REL, _spec()),
        ),
    )


def test_143a3f74_balanced_adapter_accepts_only_pinned_series(tmp_path: Path):
    prereg, records = _legacy_balanced_adapter_records(tmp_path)
    expected_digests = frozenset(row["record_sha256"] for row in records)
    frozen = sorted(B.LEGACY_BALANCED_RECORD_SHA256S)
    assert B.LEGACY_BALANCED_CAMPAIGN_ID \
        == "b10-backoff-shape-silo-balanced-formal-143a3f74"
    assert B.LEGACY_BALANCED_ANALYSIS_COMMIT \
        == "c7ed565892cd4aba52d7fa47a7d1da17b117c005"
    assert B.LEGACY_BALANCED_ANALYSIS_SHA256 \
        == "f6246360c784813a581d7e104f116c07838106022fb9245f5de50b338e9ea0ec"
    assert B.LEGACY_BALANCED_BINDING_SHA256 \
        == "588aaa9cd5eb844eeef48251777bb1d682d3b4993bae0e1b9bac94d893d7ae8f"
    assert len(frozen) == len(set(frozen)) == 45
    meta_digest = hashlib.sha256(
        ("\n".join(frozen) + "\n").encode("ascii"),
    ).hexdigest()
    assert meta_digest \
        == "8e5f0b48ba9e635e3d0e4e6c9c312c7436008dbe1a34f91a5763300920c37bad"
    binding = B._legacy_balanced_binding(prereg)
    assert binding == {
        **_legacy_v4_preregistration_binding_literal(),
        "analysis_code_sha256": B.LEGACY_BALANCED_ANALYSIS_SHA256,
        "binding_sha256": B.LEGACY_BALANCED_BINDING_SHA256,
    }
    assert "analysis_commit" not in binding
    indexed = B._validate_legacy_balanced_records(
        records,
        campaign_id=B.LEGACY_BALANCED_CAMPAIGN_ID,
        prereg=prereg,
        expected_record_digests=expected_digests,
    )
    assert len(indexed) == 45
    assert {row["execution_host"] for row in indexed.values()} == {"bnode015"}


def test_balanced_legacy_validator_default_is_the_frozen_balanced_set():
    defaults = B._validate_legacy_balanced_records.__kwdefaults__
    assert defaults is not None
    assert defaults["expected_record_digests"] \
        is B.LEGACY_BALANCED_RECORD_SHA256S

    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    collector = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_collect_report_inputs"
    )
    balanced_call = next(
        node for node in ast.walk(collector)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_validate_legacy_balanced_records"
    )
    assert "expected_record_digests" not in {
        keyword.arg for keyword in balanced_call.keywords
    }


def test_balanced_legacy_content_change_is_outside_frozen_digest_set(
    tmp_path: Path,
):
    prereg, records = _legacy_balanced_adapter_records(tmp_path)
    expected = frozenset(row["record_sha256"] for row in records)
    records[0]["correctness_certified"] = False
    _rehash_record(records[0])
    _expect_code(
        "legacy-record",
        lambda: B._validate_legacy_balanced_records(
            records,
            campaign_id=B.LEGACY_BALANCED_CAMPAIGN_ID,
            prereg=prereg,
            expected_record_digests=expected,
        ),
    )


def test_balanced_legacy_rejects_other_campaign_id(tmp_path: Path):
    prereg, records = _legacy_balanced_adapter_records(tmp_path)
    _expect_code(
        "legacy-record",
        lambda: B._validate_legacy_balanced_records(
            records,
            campaign_id="b10-backoff-shape-silo-balanced-formal-other",
            prereg=prereg,
            expected_record_digests={row["record_sha256"] for row in records},
        ),
    )


@pytest.mark.parametrize(
    "mutation",
    ("execution-host-missing", "workload-wrong", "binding-analysis-sha-wrong"),
)
def test_balanced_legacy_semantic_gate_rejects_even_with_mutated_digest_injected(
    tmp_path: Path, mutation: str,
):
    prereg, records = _legacy_balanced_adapter_records(tmp_path)
    expected = {row["record_sha256"] for row in records}
    changed = records[0]
    old_digest = changed["record_sha256"]
    if mutation == "execution-host-missing":
        del changed["execution_host"]
    elif mutation == "workload-wrong":
        changed["workload"] = "read-heavy"
    else:
        changed["preregistration_binding"] = prereg.binding.as_dict()
    _rehash_record(changed)
    expected.remove(old_digest)
    expected.add(changed["record_sha256"])
    _expect_code(
        "legacy-record",
        lambda: B._validate_legacy_balanced_records(
            records,
            campaign_id=B.LEGACY_BALANCED_CAMPAIGN_ID,
            prereg=prereg,
            expected_record_digests=expected,
        ),
    )


def test_balanced_legacy_46th_record_belongs_to_exact_cell_gate(tmp_path: Path):
    prereg, records = _legacy_balanced_adapter_records(tmp_path)
    # This mutation is owned by the record-count/cell gate, not digest equality.
    extra = copy.deepcopy(records[0])
    _expect_code(
        "report-completeness",
        lambda: B._validate_legacy_balanced_records(
            [*records, extra],
            campaign_id=B.LEGACY_BALANCED_CAMPAIGN_ID,
            prereg=prereg,
            expected_record_digests={row["record_sha256"] for row in records},
        ),
    )


@pytest.mark.parametrize("mutation", ("missing", "additional", "replacement"))
def test_legacy_digest_helper_rejects_nonexact_sets_directly(mutation: str):
    expected = sorted(B.LEGACY_BALANCED_RECORD_SHA256S)
    if mutation == "missing":
        observed = expected[:-1]
    elif mutation == "additional":
        observed = [*expected, "0" * 64]
    else:
        observed = [*expected[:-1], "0" * 64]
    _expect_code(
        "legacy-record",
        lambda: B._require_legacy_record_digests(
            observed, B.LEGACY_BALANCED_RECORD_SHA256S,
        ),
    )


def test_report_lock_binding_reads_the_real_campaign_lock_codec(tmp_path: Path):
    layout = CampaignLayout(str(tmp_path / "campaign"))
    Path(layout.root).mkdir(parents=True)
    binding = _binding().as_dict()
    identity = {
        "spec_content": "fixture",
        "ccbench_commit": B.PIN,
        "search_tag": "formal",
        "search_config": {"preregistration_binding": binding},
        "trial": "fixture",
    }
    Path(layout.lock_file).write_text(
        B.campaign_lock.canonical_json(identity), encoding="utf-8",
    )
    B._assert_report_lock_binding(layout, binding)
    _expect_code(
        "resume-binding",
        lambda: B._assert_report_lock_binding(
            layout, {**binding, "binding_sha256": "0" * 64},
        ),
    )


def test_report_admission_requires_exactly_135_registered_block_cells():
    prereg = B.Preregistration(_binding(), B.PREREG_REL, _spec())
    records = [
        {"workload": workload, "block_id": block_id, "point": point}
        for workload in prereg.spec.workload_map
        for block_id, order in prereg.spec.block_orders
        for point in order
    ]
    assert len(records) == 135
    B._require_exact_report_cells(records, prereg)
    _expect_code(
        "report-completeness",
        lambda: B._require_exact_report_cells(records[:-1], prereg),
    )
    _expect_code(
        "report-completeness",
        lambda: B._require_exact_report_cells([*records, records[0]], prereg),
    )


def test_report_admission_rejects_same_size_unique_nonregistered_grid():
    prereg = B.Preregistration(_binding(), B.PREREG_REL, _spec())
    records = [
        {"workload": workload, "block_id": block_id, "point": point}
        for workload in prereg.spec.workload_map
        for block_id, order in prereg.spec.block_orders
        for point in order
    ]
    records[-1] = {
        "workload": "read-heavy",
        "block_id": "block-3",
        "point": "unregistered-point",
    }
    observed = [
        (row["workload"], row["block_id"], row["point"])
        for row in records
    ]
    assert len(observed) == len(set(observed)) == 135
    _expect_code(
        "report-completeness",
        lambda: B._require_exact_report_cells(records, prereg),
    )


def test_report_collector_calls_each_series_specific_legacy_validator_once():
    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    collector = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_collect_report_inputs"
    )
    calls = [
        node.func.id for node in ast.walk(collector)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert calls.count("_validate_legacy_write_heavy_records") == 1
    assert calls.count("_validate_legacy_balanced_records") == 1
    assert {
        name for name in calls if name.startswith("_validate_legacy_")
    } == {
        "_validate_legacy_write_heavy_records",
        "_validate_legacy_balanced_records",
    }


def test_report_collector_reads_only_three_formal_series_and_discloses_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    prereg = B.Preregistration(_binding(), B.PREREG_REL, _spec())
    calibration = B.CalibrationSelection(
        path="calibration.json", sha256="e" * 64,
        schema_version="calibration/v2", records=100,
        threads=48, env_tag="pegasus", clocks_per_us=2100,
        saturated=True, lower_bound_selected=False, cache_floor_warning=False,
    )
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    contract = B.env_contract.GENERATIONS["pegasus"][-1].contract
    formal_cfg = B.config_for(
        "read-heavy", prereg, calibration, context, contract,
    )
    formal_read_id = str(B.ident.campaign_id(formal_cfg))
    trial_read_id = str(B.ident.campaign_id(B.config_for(
        "read-heavy", prereg, calibration, context, contract,
        search_tag=B.TRIAL_SEARCH_TAG, submission_nonce="0" * 32,
    )))

    def indexed(workload: str):
        return {
            (block_id, point): {
                "workload": workload, "block_id": block_id, "point": point,
            }
            for block_id, order in prereg.spec.block_orders
            for point in order
        }

    monkeypatch.setattr(B, "_read_block_records", lambda _root: [])
    monkeypatch.setattr(
        B, "_validate_legacy_write_heavy_records",
        lambda *_args, **_kwargs: indexed("write-heavy"),
    )
    monkeypatch.setattr(
        B, "_validate_legacy_balanced_records",
        lambda *_args, **_kwargs: indexed("balanced"),
    )
    monkeypatch.setattr(
        B, "_validate_prior_block_records",
        lambda *_args, workload, **_kwargs: indexed(workload),
    )
    monkeypatch.setattr(B, "_assert_report_lock_binding", lambda *_args: None)
    monkeypatch.setattr(
        B, "_verification_source_disclosure",
        lambda _layout, *, workload, campaign_id, indexed: (
            {
                "workload": workload, "campaign_id": campaign_id,
                "raw_verify_done_records": 0,
            },
            {},
        ),
    )
    requested = []

    def layout_for_campaign(campaign_id: str) -> CampaignLayout:
        requested.append(campaign_id)
        return CampaignLayout(str(tmp_path / campaign_id))

    _records, performance, _verification = B._collect_report_inputs(
        str(tmp_path), prereg=prereg, calibration=calibration,
        context=context, contract=contract,
        layout_for_campaign=layout_for_campaign,
    )
    assert requested == [
        B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID,
        B.LEGACY_BALANCED_CAMPAIGN_ID,
        formal_read_id,
    ]
    assert trial_read_id not in requested
    measured = {
        source["workload"]: source["measured_with"]
        for source in performance["source_campaigns"]
    }
    assert measured["write-heavy"] == {
        "analysis_commit": B.LEGACY_WRITE_HEAVY_ANALYSIS_COMMIT,
        "analysis_code_sha256": B.LEGACY_WRITE_HEAVY_ANALYSIS_SHA256,
        "binding_sha256": B.LEGACY_WRITE_HEAVY_BINDING_SHA256,
    }
    assert measured["balanced"] == {
        "analysis_commit": B.LEGACY_BALANCED_ANALYSIS_COMMIT,
        "analysis_code_sha256": B.LEGACY_BALANCED_ANALYSIS_SHA256,
        "binding_sha256": B.LEGACY_BALANCED_BINDING_SHA256,
    }
    assert measured["read-heavy"] == {
        "analysis_commit": prereg.binding.analysis_commit,
        "analysis_code_sha256": prereg.binding.analysis_code_sha256,
        "binding_sha256": prereg.binding.binding_sha256,
    }


def test_report_discloses_manual_termination_guarantee_and_wal_limitations(
    tmp_path: Path,
):
    prereg = B.Preregistration(_binding(), B.PREREG_REL, _spec())
    tree = ast.parse(Path(B.__file__).read_text(encoding="utf-8"))
    collector = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_collect_report_inputs"
    )
    producer_calls = [
        node for node in ast.walk(collector)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_performance_cell_completeness"
    ]
    assert len(producer_calls) == 1
    calibration = B.CalibrationSelection(
        path="calibration.json", sha256="e" * 64,
        schema_version="calibration/v2", records=100,
        threads=48, env_tag="pegasus", clocks_per_us=2100,
        saturated=True, lower_bound_selected=False, cache_floor_warning=False,
    )
    submission = B.SubmissionIdentity(
        receipt_path="submit-receipt.json", receipt_sha256="d" * 64,
        request_id="report-request", nonce="c" * 32,
        source_commit="b" * 40, prereg_commit="a" * 40,
        job_script_sha256="9" * 64, phase="report", workload=None,
    )
    performance = B._performance_cell_completeness(
        [
            {"workload": workload, "campaign_id": f"campaign-{workload}", "observed_cells": 45}
            for workload in prereg.spec.workload_map
        ],
        observed_cells=135,
        prereg=prereg,
    )
    verification = {
        "expected_slots": 270,
        "completed_logical_slots": 197,
        "incomplete_slots": 73,
        "logical_key": ["workload", "variant", "verify_tag", "repetition"],
        "counting_rule": "count verify_done by (workload, variant, verify_tag)",
        "known_limitation": (
            "duplicate WAL frames and distinct repetitions cannot be distinguished"
        ),
        "observed_verify_done_records": 198,
        "source_campaigns": [{
            "workload": "write-heavy",
            "campaign_id": B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID,
            "raw_verify_done_records": 91,
            "completed_logical_slots": 90,
            "verify_done_records_by_tag": {"legacy": 15, "performance": 75},
            "unknown_verify_tags": {"extra": 1},
            "unknown_verify_tag_values": [{"tag": "extra", "count": 1}],
            "unmapped_variants": {},
            "wal_truncated_tail": True,
            "wal_read_error": None,
            "registered_tag_overruns": [{"variant": "none"}],
        }],
        "observed_registered_counts": [],
        "registered_tag_overruns": [{"workload": "write-heavy", "variant": "none"}],
        "missing_slots": [],
    }
    report_root = tmp_path / "reports/final"
    json_path, markdown_path = B._write_reports(
        report_root,
        prereg=prereg,
        calibration=calibration,
        records=_complete_records(),
        applied_evidence={},
        submission=submission,
        performance_cell_completeness=performance,
        verification_slot_completeness=verification,
    )
    document = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert document["schema_version"] == "b10-backoff-shape-provenance/v2"
    assert document["performance_cell_completeness"][
        "proves_all_workload_jobs_terminated"
    ] is False
    assert "does not prove that all three workload jobs terminated" in markdown
    assert "submission sequencing after all three workload jobs terminate" in markdown
    assert "duplicate WAL frames and distinct repetitions cannot be distinguished" in markdown
    assert "completed_logical_slots=90" in markdown
    assert "truncated_tail=True" in markdown
    with pytest.raises(FileExistsError):
        B._write_reports(
            report_root,
            prereg=prereg,
            calibration=calibration,
            records=_complete_records(),
            applied_evidence={},
            submission=submission,
            performance_cell_completeness=performance,
            verification_slot_completeness=verification,
        )


def test_verification_completeness_counts_records_and_discloses_wal_anomalies(
    tmp_path: Path,
):
    indexed = {("block-1", "none"): {"variant_id": "variant-none"}}

    def read_source(name: str, tags: list[object]):
        layout = CampaignLayout(str(tmp_path / name))
        Path(layout.runs_dir).mkdir(parents=True)
        frames = [
            json.dumps({
                "variant": "variant-none",
                "stage": B.STAGE_VERIFY_DONE,
                "env_tag": "pegasus",
                "ts": index,
                "payload": {
                    "build_attempt_id": "attempt",
                    "workload": {"tag": tag},
                },
            }, separators=(",", ":"))
            for index, tag in enumerate(tags)
        ]
        Path(layout.wal_file).write_text(
            "\n".join(frames) + "\n{\"unterminated\"", encoding="utf-8",
        )
        return B._verification_source_disclosure(
            layout,
            workload="write-heavy",
            campaign_id=B.LEGACY_WRITE_HEAVY_CAMPAIGN_ID,
            indexed=indexed,
        )

    tags: list[object] = ["performance"] * 6 + ["legacy", "unregistered", []]
    source, counts = read_source("forward", tags)
    reverse_source, reverse_counts = read_source("reverse", list(reversed(tags)))
    assert counts == reverse_counts == {("none", "performance"): 6, ("none", "legacy"): 1}
    assert source["raw_verify_done_records"] == reverse_source["raw_verify_done_records"] == 9
    assert source["wal_truncated_tail"] is True
    assert source["unknown_verify_tags"] == {"unregistered": 1, "[]": 1}
    assert source["unknown_verify_tag_values"] == [
        {"tag": "unregistered", "count": 1},
        {"tag": [], "count": 1},
    ]
    assert source["registered_tag_overruns"] == [{
        "variant": "none", "verify_tag": "performance", "observed": 6, "registered": 5,
    }]

    prereg = B.Preregistration(_binding(), B.PREREG_REL, _spec())
    completeness = B._verification_completeness(
        [source], {"write-heavy": counts}, prereg,
    )
    assert completeness["expected_slots"] == 270
    assert completeness["completed_logical_slots"] == 6
    assert completeness["incomplete_slots"] == 264
    assert completeness["source_campaigns"][0]["raw_verify_done_records"] == 9
    assert completeness["source_campaigns"][0]["completed_logical_slots"] == 6
    assert completeness["registered_tag_overruns"] == [{
        "workload": "write-heavy", "variant": "none",
        "verify_tag": "performance", "observed": 6, "registered": 5,
    }]
    assert "cannot be distinguished" in completeness["known_limitation"]

    calibration = B.CalibrationSelection(
        path="calibration.json", sha256="e" * 64,
        schema_version="calibration/v2", records=100,
        threads=48, env_tag="pegasus", clocks_per_us=2100,
        saturated=True, lower_bound_selected=False, cache_floor_warning=False,
    )
    submission = B.SubmissionIdentity(
        receipt_path="submit-receipt.json", receipt_sha256="d" * 64,
        request_id="report-request", nonce="c" * 32,
        source_commit="b" * 40, prereg_commit="a" * 40,
        job_script_sha256="9" * 64, phase="report", workload=None,
    )
    performance = B._performance_cell_completeness(
        [{
            "workload": workload,
            "campaign_id": f"campaign-{workload}",
            "observed_cells": 45,
        } for workload in prereg.spec.workload_map],
        observed_cells=135,
        prereg=prereg,
    )
    json_path, markdown_path = B._write_reports(
        tmp_path / "reports/final",
        prereg=prereg,
        calibration=calibration,
        records=_complete_records(),
        applied_evidence={},
        submission=submission,
        performance_cell_completeness=performance,
        verification_slot_completeness=completeness,
    )
    report = json.loads(json_path.read_text(encoding="utf-8"))
    report_source = report["verification_slot_completeness"]["source_campaigns"][0]
    assert report_source["unknown_verify_tags"] == {"unregistered": 1, "[]": 1}
    assert report_source["unknown_verify_tag_values"] == [
        {"tag": "unregistered", "count": 1},
        {"tag": [], "count": 1},
    ]
    assert report_source["raw_verify_done_records"] == 9
    assert report_source["completed_logical_slots"] == 6
    assert markdown_path.is_file()


def test_prior_block_record_allows_commit_drift_but_rejects_code_drift(
    tmp_path: Path,
):
    stored_prereg, row = _prior_block_record(tmp_path)
    stored_commit = stored_prereg.binding.analysis_commit
    current_binding = replace(
        stored_prereg.binding,
        analysis_commit="c" * 40,
    )
    current_prereg = B.Preregistration(
        current_binding, stored_prereg.path, stored_prereg.spec,
    )

    assert row["analysis_commit"] == stored_commit
    assert row["source_commit"] == stored_commit
    assert row["preregistration_binding"] == current_binding.as_dict()
    assert row["analysis_code_sha256"] == current_binding.analysis_code_sha256
    indexed = B._validate_prior_block_records(
        [row], workload="write-heavy", prereg=current_prereg,
    )
    assert indexed == {("block-1", "none"): row}
    assert indexed[("block-1", "none")]["analysis_commit"] == stored_commit
    assert indexed[("block-1", "none")]["source_commit"] == stored_commit

    code_drift_binding = replace(
        current_binding,
        analysis_code_sha256="d" * 64,
    )
    code_drift_prereg = B.Preregistration(
        code_drift_binding, stored_prereg.path, stored_prereg.spec,
    )
    code_drift_row = copy.deepcopy(row)
    code_drift_row["preregistration_binding"] = code_drift_binding.as_dict()
    assert code_drift_row["preregistration_binding"] == code_drift_binding.as_dict()
    assert code_drift_row["analysis_code_sha256"] \
        != code_drift_binding.analysis_code_sha256
    _expect_code(
        "resume-binding",
        lambda: B._validate_prior_block_records(
            [code_drift_row], workload="write-heavy", prereg=code_drift_prereg,
        ),
    )


def test_prior_block_record_metadata_must_match_point(tmp_path: Path):
    prereg, row = _prior_block_record(tmp_path)
    malicious = copy.deepcopy(row)
    malicious.update({
        "shape": "binary",
        "mean_us": 2,
        "encoded": 2002,
        "genome": B.Genome(
            "silo", {**B._BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 2002},
        ).canonical(),
    })
    _expect_code(
        "resume-binding",
        lambda: B._validate_prior_block_records(
            [malicious], workload="write-heavy", prereg=prereg,
        ),
    )


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


def test_p02_all_12_registered_encodings_are_bijective():
    encoded = {B.encode(shape, mean_us) for shape, _code in B.SHAPES for mean_us in B.MEANS_US}
    assert len(encoded) == 12
    assert {B.decode(value) for value in encoded} == {
        (shape, mean_us) for shape, _code in B.SHAPES for mean_us in B.MEANS_US
    }
    with pytest.raises(ValueError, match="grid 外"):
        B.encode("binary", 2)
    with pytest.raises(ValueError, match="grid 外"):
        B.decode(2002)


def test_p03_legacy_zero_through_999_is_numerically_identical():
    for value in range(1000):
        assert B.exact_model(value, 0) == Fraction(value)
        assert B.exact_model(value, (1 << 64) - 1) == Fraction(value)


def test_legacy_encoded_shape_ranges_keep_their_closed_forms():
    starts = (0, 1, 17, B._MASK64)
    for encoded in range(1000, 2000):
        mean_us = encoded % 1000
        for start in starts:
            mixed = (start * 0x9E3779B97F4A7C15) & B._MASK64
            high = mixed >> 63
            low = mixed & ((1 << 63) - 1)
            residue = low % (2 * mean_us + 1)
            offset = 2 * mean_us - residue if high else residue
            assert B.exact_model(encoded, start) == Fraction(mean_us + offset, 2)
    for encoded in range(2000, 3000):
        mean_us = encoded % 1000
        for start in starts:
            high = ((start * 0x9E3779B97F4A7C15) & B._MASK64) >> 63
            assert B.exact_model(encoded, start) == Fraction(
                mean_us + high * 2 * mean_us, 2,
            )


def test_high_static_raw_values_and_exact_model_domain_are_literal_pins():
    for encoded, expected in ((3000, 1000), (3001, 1001), (3999, 1999)):
        assert B.exact_model(encoded, 0) == Fraction(expected)
        assert B.exact_model(encoded, B._MASK64) == Fraction(expected)
    assert B.exact_model(11999, 0) == Fraction(9999)
    for invalid in (-1, True, 12000):
        with pytest.raises(ValueError, match=r"\[0, 11999\]"):
            B.exact_model(invalid, 0)


def test_p04_three_reference_points_and_full_grid_are_accepted():
    refs = dict(B.reference_genomes())
    assert set(refs) == {"none", "adaptive", "zero-loop"}
    assert refs["none"].flags["BACK_OFF"] == 0
    assert refs["none"].flags["BACKOFF_FIXED"] == -1
    assert refs["adaptive"].flags["BACK_OFF"] == 1
    assert refs["adaptive"].flags["BACKOFF_FIXED"] == -1
    assert refs["zero-loop"].flags["BACK_OFF"] == 1
    assert refs["zero-loop"].flags["BACKOFF_FIXED"] == 0
    assert B.POINTS_PER_BLOCK == 15
    assert len(B.genomes()) == 15


def test_exact_finite_models_distinguish_registered_shapes_and_dormant_code2():
    width = 16
    assert B.MIXER % 2 == 1
    inverse = pow(B.MIXER, -1, 1 << 64)
    for mean_us in B.MEANS_US:
        encoded_values = (
            B.encode("constant", mean_us),
            B.encode("symmetric-modulo", mean_us),
            2000 + mean_us,
        )
        # constant/symmetric are registered v5 shapes. Code 2 is retained only
        # as a byte-pinned dormant C++ compatibility branch.
        for low in range(1 << width):
            starts = (
                (low * inverse) & B._MASK64,
                (((1 << 63) | low) * inverse) & B._MASK64,
            )
            for encoded in encoded_values:
                values = [B.exact_model(encoded, start) for start in starts]
                assert sum(values, Fraction()) == Fraction(2 * mean_us)


def test_dormant_code2_binary_arms_and_registered_symmetric_bounds_for_odd_means():
    for mean_us in (5, 25):
        dormant_code2 = 2000 + mean_us
        # MIXER is odd, so start=0 has high bit 0.  Search one finite witness for high bit 1.
        high_start = next(
            start for start in range(1, 1000)
            if (((start * B.MIXER) & B._MASK64) >> 63) == 1
        )
        assert B.exact_model(dormant_code2, 0) == Fraction(mean_us, 2)
        assert B.exact_model(dormant_code2, high_start) == Fraction(3 * mean_us, 2)
        symmetric = B.encode("symmetric-modulo", mean_us)
        for start in (0, high_start, (1 << 64) - 1):
            value = B.exact_model(symmetric, start)
            assert Fraction(mean_us, 2) <= value <= Fraction(3 * mean_us, 2)


def test_block_orders_are_distinct_complete_identity_bearing_permutations():
    orders = [B.block_run_order(block) for block in B.BLOCK_IDS]
    expected = {name for name, _genome in B.named_genomes()}
    assert len(set(orders)) == 3
    assert all(
        len(order) == B.POINTS_PER_BLOCK == 15 and set(order) == expected
        for order in orders
    )


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
    assert "15 genomes" in cfg.spec_content


def test_trial_config_is_separate_from_formal_and_nonce_specific():
    spec = _spec()
    prereg = B.Preregistration(_binding(), B.PREREG_REL, spec)
    calibration = B.CalibrationSelection(
        path="artifact.json", sha256="e" * 64, schema_version="calibration/v2",
        records=765432, threads=48, env_tag="pegasus", clocks_per_us=2100,
        saturated=False, lower_bound_selected=True, cache_floor_warning=False,
    )
    context = B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP)
    contract = B.env_contract.GENERATIONS["pegasus"][-1].contract
    formal = B.config_for(
        "read-heavy", prereg, calibration, context, contract,
        search_tag="formal",
    )
    first = B.config_for(
        "read-heavy", prereg, calibration, context, contract,
        search_tag=B.TRIAL_SEARCH_TAG, submission_nonce="0" * 32,
    )
    second = B.config_for(
        "read-heavy", prereg, calibration, context, contract,
        search_tag=B.TRIAL_SEARCH_TAG, submission_nonce="1" * 32,
    )
    assert formal.spec_slug == "b10-backoff-shape-silo-read-heavy"
    assert formal.search_config["scale"] == "silo-b10-backoff-shape"
    assert formal.search_tag == "formal"
    assert formal.trial == f"{B.TRIAL}-{spec.spec_sha256[:16]}"
    assert first.search_tag == second.search_tag == "trial"
    assert first.trial \
        == f"{B.TRIAL}-{spec.spec_sha256[:16]}-{'0' * 32}"
    assert "0" * 32 in first.trial
    assert formal.search_config == first.search_config == second.search_config
    assert len({
        str(B.ident.campaign_id(formal)),
        str(B.ident.campaign_id(first)),
        str(B.ident.campaign_id(second)),
    }) == 3
    assert first.trial != second.trial
    for workload in B.WORKLOADS:
        cfg = B.config_for(
            workload, prereg, calibration, context, contract,
            search_tag=B.TRIAL_SEARCH_TAG, submission_nonce="2" * 32,
        )
        assert cfg.search_tag == "trial"
    with pytest.raises(ValueError, match="validated submission nonce"):
        B.config_for(
            "read-heavy", prereg, calibration, context, contract,
            search_tag=B.TRIAL_SEARCH_TAG,
        )


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
        ("balanced", "block-1", "symmetric-modulo", 2),
        ("balanced", "block-2", "symmetric-modulo", 5),
    )
    for selector in ("unstable", "uncertified"):
        kwargs = {selector: keys[0]}
        result = B.judge(_complete_records(**kwargs), _spec())
        family = next(
            row for row in result["families"]
            if row["workload"] == "balanced"
            and row["shape"] == "symmetric-modulo"
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
        if row["workload"] == "balanced"
        and row["shape"] == "symmetric-modulo"
    )
    assert family["outcome"] == "indeterminate"


def test_cell_effects_cover_all_36_factorial_cells_with_ci():
    effects = B.cell_effects(_complete_records(), _spec())
    assert len(effects) == 36
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
    assert B.FORMULA_SHA256 == "1205b1ffb4fa6740873f1aa1ecf50bfc484239fb74aa28464dcb2e3a19fbe8df"
    assert B.SPACE_VERSION == "b10-backoff-shape/v3"
    assert B.TRIAL == "b10-backoff-shape-v3"


def test_actual_cpp_expression_compiles_with_werror_and_matches_fraction_model(tmp_path: Path):
    binary = _compile_expression(tmp_path, _patch_hole_line(_patch_bytes()))
    starts = (0, 1, 2, 17, (1 << 63) - 1, 1 << 63, (1 << 64) - 1)
    for shape, _code in B.SHAPES:
        for mean_us in B.MEANS_US:
            encoded = B.encode(shape, mean_us)
            for start in starts:
                assert _cpp_value(binary, encoded, start) == B.exact_model(encoded, start)

    # Independent semantic oracle: odd MIXER is a permutation. Construct y,
    # invert it to start, and pair equal low63 values with opposite high bits.
    # symmetric-modulo is registered; code 2 is absent from the v5 grid, Holm
    # families, and throughput report, and remains only for byte-pinned formula
    # compatibility.
    assert B.MIXER & 1
    inverse = pow(B.MIXER, -1, 1 << 64)
    for shape in ("symmetric-modulo", "dormant-code2"):
        for mean_us in B.MEANS_US:
            encoded = (
                B.encode("symmetric-modulo", mean_us)
                if shape == "symmetric-modulo" else 2000 + mean_us
            )
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

    # Independent literals prevent a matching Python/C++ decoder bug from
    # blessing the new static escape range.
    for encoded, expected in ((3000, 1000), (3001, 1001), (3999, 1999)):
        assert _cpp_value(binary, encoded, 0) == Fraction(expected)
        assert _cpp_value(binary, encoded, B._MASK64) == Fraction(expected)
        assert _cpp_value(binary, encoded, 17) == B.exact_model(encoded, 17)


def test_t1905_m1_job_exports_official_root_and_missing_env_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
):
    job = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    lines = job.read_text(encoding="utf-8").splitlines()
    assert lines.count(
        'export IZANAGI_OFFICIAL_OUTPUT_ROOT="$OUTPUT_ROOT"'
    ) == 1
    assert lines.count("unset IZANAGI_OFFICIAL_OUTPUT_ROOT") == 1

    monkeypatch.delenv("IZANAGI_OFFICIAL_OUTPUT_ROOT", raising=False)
    with pytest.raises(ValueError, match="official output_root は明示必須"):
        B._prepare_official_output(B.ENV_TAG)


def test_t1905_m2_job_root_passes_real_external_and_claim_capability_gates(
    monkeypatch: pytest.MonkeyPatch,
):
    with tempfile.TemporaryDirectory(
        prefix="izanagi-b10-m2-", dir="/var/tmp",
    ) as raw_root:
        repo = Path(raw_root) / "repo"
        git_common_dir = repo / ".git"
        git_common_dir.mkdir(parents=True)
        output_root = _job_script_output_root(
            repo_root=repo,
            git_common_dir=git_common_dir,
            nonce="0" * 32,
        )
        monkeypatch.setenv(
            "IZANAGI_OFFICIAL_OUTPUT_ROOT", os.fspath(output_root),
        )

        resolved_output, policy = B._prepare_official_output(B.ENV_TAG)
        resolved_root = Path(resolved_output)
        claim_root = resolved_root / "env" / B.ENV_TAG / "claims"
        capability = write_capability_for_directory(claim_root, policy=policy)

        assert resolved_root == output_root.resolve()
        assert resolved_root != repo and repo not in resolved_root.parents
        assert policy.approved_roots == (resolved_root,)
        assert capability.root == claim_root.resolve()


def test_t1905_m3_job_root_is_identical_across_phase_job_nonces(tmp_path: Path):
    repo = tmp_path / "repo"
    git_common_dir = repo / ".git"
    git_common_dir.mkdir(parents=True)
    roots = {
        _job_script_output_root(
            repo_root=repo,
            git_common_dir=git_common_dir,
            nonce=nonce,
        )
        for nonce in ("0" * 32, "f" * 32)
    }
    assert len(roots) == 1


def test_formal_campaign_layout_and_writer_share_resolved_root_and_policy():
    source = Path(B.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    run_formal = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_formal"
    )
    prepare_calls = [
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_prepare_official_output"
    ]
    layout_calls = [
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "campaign_layout"
    ]
    writer_calls = [
        node for node in ast.walk(run_formal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_campaign"
    ]

    assert len(prepare_calls) == 1
    assert len(layout_calls) == 2
    assert all(
        len(call.args) == 2
        and isinstance(call.args[1], ast.Name)
        and call.args[1].id == "resolved_output"
        for call in layout_calls
    )
    assert len(writer_calls) == 1
    writer_keywords = {keyword.arg: keyword.value for keyword in writer_calls[0].keywords}
    assert isinstance(writer_keywords["output_root"], ast.Name)
    assert writer_keywords["output_root"].id == "resolved_output"
    assert isinstance(writer_keywords["durable_root_policy"], ast.Name)
    assert writer_keywords["durable_root_policy"].id == "durable_policy"


def test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    with tempfile.TemporaryDirectory(
        prefix="izanagi-b10-forbidden-", dir="/tmp",
    ) as raw_root:
        forbidden_root = Path(raw_root).resolve()
        monkeypatch.setenv(
            "IZANAGI_OFFICIAL_OUTPUT_ROOT", os.fspath(forbidden_root),
        )

        resolved_output, policy = B._prepare_official_output(B.ENV_TAG)
        claim_root = Path(resolved_output) / "env" / B.ENV_TAG / "claims"

        assert Path(resolved_output) == forbidden_root
        with pytest.raises(
            DurableRootError, match="^candidate が forbidden root 配下$",
        ):
            write_capability_for_directory(claim_root, policy=policy)


def test_t1905_a5_non_forbidden_external_official_root_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
):
    with tempfile.TemporaryDirectory(
        prefix="izanagi-b10-durable-", dir="/var/tmp",
    ) as raw_root:
        external_root = Path(raw_root).resolve()
        monkeypatch.setenv(
            "IZANAGI_OFFICIAL_OUTPUT_ROOT", os.fspath(external_root),
        )

        resolved_output, policy = B._prepare_official_output(B.ENV_TAG)
        claim_root = Path(resolved_output) / "env" / B.ENV_TAG / "claims"
        capability = write_capability_for_directory(claim_root, policy=policy)

        assert Path(resolved_output) == external_root
        assert external_root.is_relative_to(Path("/var/tmp"))
        assert capability.root == claim_root.resolve()


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
        '  "$PY" -I -B - "$REPO_ROOT/tools/pegasus/policy.json" <<\'PY\'',
        '    "$PY" -I -B - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" \\',
        '  "$PY" -I -B - "$SUBMIT_RECEIPT" "$IZANAGI_B10_NONCE" "$PBS_JOBID" \\',
        '  "$PY" -I -B - "$ATTEMPT_DIR/qstat-f.stdout" "$qstat_rc" \\',
        '  readarray -t DEPENDENCY_VALUES < <("$PY" -I -B - "$REPO_ROOT/tools/pegasus/policy.json" <<\'PY\'',
        '"$PY" -I -B - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$driver_rc" \\',
    ]
    assert '"$PY" -B -m orchestrator.campaign.b10_backoff_shape_sweep' in job_text
    assert '"$PY" -I -B -m orchestrator.campaign.b10_backoff_shape_sweep' not in job_text
    assert "build|verify|perf|probe|verify-perf|trial-cell|report" \
        in submit_text + job_text
    assert '[[ "$IZANAGI_B10_PHASE" != probe && "$IZANAGI_B10_PHASE" != report ]]' in job_text


def test_pegasus_job_signal_handler_records_failure_and_exits_with_signal_status(
    tmp_path: Path,
):
    job = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    handlers = re.findall(
        r"(?ms)^on_signal\(\) \{\n.*?^\}\n",
        job.read_text(encoding="utf-8"),
    )
    assert len(handlers) == 1

    failure_args = tmp_path / "failure-args"
    completed = subprocess.run(
        [
            "bash", "-c",
            "set -Eeuo pipefail\n"
            "FAILURE_ARGS=$1\n"
            "write_failure() {\n"
            "  printf '%s\\n' \"$1\" \"$2\" \"$3\" >>\"$FAILURE_ARGS\"\n"
            "}\n"
            f"{handlers[0]}"
            "on_signal TERM 15\n",
            "b10-on-signal-test",
            os.fspath(failure_args),
        ],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 143, completed.stdout + completed.stderr
    assert failure_args.read_text(encoding="utf-8").splitlines() == [
        "143", "signal", "received TERM",
    ]


def test_verify_perf_launcher_contract_and_walltime_are_consistent(tmp_path: Path):
    submit_text = (
        ROOT / "tools/pegasus/submit_b10_backoff_shape.sh"
    ).read_text(encoding="utf-8")
    job_text = (
        ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    ).read_text(encoding="utf-8")
    driver_text = Path(B.__file__).read_text(encoding="utf-8")

    policy = json.loads((ROOT / B.B10_POLICY_REL).read_text(encoding="utf-8"))
    walltime_s = policy["b10_backoff_shape_walltime_s"]
    assert walltime_s == 24 * 60 * 60

    directive = re.findall(
        r"(?m)^#PBS -l elapstim_req=([0-9]+):([0-9]+):([0-9]+)$", job_text,
    )
    assert directive == [("24", "00", "00")]
    hours, minutes, seconds = map(int, directive[0])
    assert hours * 3600 + minutes * 60 + seconds == walltime_s

    def evaluated_request_walltime(source: str) -> int:
        expressions = re.findall(
            r'"elapstim_req_s":\s*([^}\n]+)\}', source,
        )
        assert len(expressions) == 1
        return eval(  # noqa: S307 - evaluates one captured in-repository expression
            expressions[0], {"__builtins__": {}, "int": int},
            {"walltime_s": str(walltime_s)},
        )

    assert evaluated_request_walltime(job_text) == walltime_s
    assert evaluated_request_walltime(submit_text) == walltime_s
    assert B._b10_pbs_request(ROOT)["elapstim_req_s"] == walltime_s

    scheduler_condition = re.findall(
        r'(?m)^(\[\[ "\$SCHEDULER_ELAPSE_LIMIT_S" -eq "\$B10_WALLTIME_S" \]\]) \\$',
        job_text,
    )
    assert len(scheduler_condition) == 1
    compared = subprocess.run(
        [
            "bash", "-c",
            "SCHEDULER_ELAPSE_LIMIT_S=$1; B10_WALLTIME_S=$2; "
            + scheduler_condition[0],
            "b10-walltime-value-test", str(walltime_s), str(walltime_s),
        ],
        capture_output=True, text=True,
    )
    assert compared.returncode == 0, compared.stdout + compared.stderr

    scheduler_gate = re.findall(
        r'(?m)^(\[\[ "\$SCHEDULER_ELAPSE_LIMIT_S" -eq "\$B10_WALLTIME_S" \]\] \\\n'
        r'  \|\| \{ write_failure 2 allocation '
        r'"actual scheduler Elapse limit differs from receipt"; exit 2; \})$',
        job_text,
    )
    assert len(scheduler_gate) == 1
    failure_args = tmp_path / "walltime-failure-args"
    rejected = subprocess.run(
        [
            "bash", "-c",
            "set -Eeuo pipefail\n"
            "failure_args=$1\n"
            "write_failure() { printf '%s\\n' \"$1\" \"$2\" \"$3\" >\"$failure_args\"; }\n"
            "SCHEDULER_ELAPSE_LIMIT_S=$2\n"
            "B10_WALLTIME_S=$3\n"
            + scheduler_gate[0],
            "b10-walltime-rejection-test", os.fspath(failure_args),
            str(walltime_s + 1), str(walltime_s),
        ],
        capture_output=True,
        text=True,
    )
    assert rejected.returncode == 2, rejected.stdout + rejected.stderr
    assert failure_args.read_text(encoding="utf-8").splitlines() == [
        "2", "allocation", "actual scheduler Elapse limit differs from receipt",
    ]

    for text in (submit_text, job_text):
        assert "build|verify|perf|probe|verify-perf|trial-cell|report" in text
    for duplicated_walltime in ("43200", "86400"):
        assert duplicated_walltime not in job_text + submit_text + driver_text
    assert "21600" not in submit_text + job_text + driver_text
    assert "06:00:00" not in job_text


def test_sanctioned_dry_run_stages_outside_worktree_and_preserves_clean_surface(
    tmp_path: Path,
):
    repo = tmp_path / "repo"
    tools = repo / "tools/pegasus"
    tools.mkdir(parents=True)
    submit_source = ROOT / "tools/pegasus/submit_b10_backoff_shape.sh"
    job_source = ROOT / "tools/pegasus/b10_backoff_shape_campaign.sh"
    policy_source = ROOT / B.B10_POLICY_REL
    submit = tools / submit_source.name
    job = tools / job_source.name
    policy = tools / policy_source.name
    shutil.copy2(submit_source, submit)
    shutil.copy2(job_source, job)
    shutil.copy2(policy_source, policy)
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
    phase_workloads = [
        ("probe", None),
        ("report", None),
        *((B.TRIAL_CELL_PHASE, workload) for workload in B.WORKLOADS),
    ]
    for phase, workload in phase_workloads:
        argv = [
            str(submit), "--dry-run", "--durable-root", str(durable),
            "--prereg-commit", "a" * 40, "--phase", phase,
        ]
        if workload is not None:
            argv.extend(("--workload", workload))
        completed = subprocess.run(
            argv,
            cwd=repo, env=env, capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
    missing_workload = subprocess.run(
        [
            str(submit), "--dry-run", "--durable-root", str(durable),
            "--prereg-commit", "a" * 40, "--phase", B.TRIAL_CELL_PHASE,
        ],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert missing_workload.returncode == 2
    after = {path.relative_to(repo) for path in repo.rglob("*")}
    assert after == before
    receipts = list(durable.glob("*/submit-receipt.json"))
    assert len(receipts) == 5
    receipt_docs = [json.loads(path.read_text(encoding="utf-8")) for path in receipts]
    assert {
        (receipt["phase"], receipt["workload"]) for receipt in receipt_docs
    } == set(phase_workloads)
    for receipt in receipt_docs:
        assert receipt["dry_run"] is True
        assert receipt["request"]["elapstim_req_s"] \
            == json.loads(policy.read_text(encoding="utf-8"))["b10_backoff_shape_walltime_s"]


def test_plain_runner_executes_this_file_instead_of_false_green():
    source = Path(__file__).read_text(encoding="utf-8")
    assert "pytest.main" in source.split("__main__", 1)[1]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
