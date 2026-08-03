# -*- coding: utf-8 -*-
"""U3 caller/CLI authority and bounded materializer inventory gates."""
from __future__ import annotations

import argparse
import ast
from dataclasses import replace
from pathlib import Path

from campaign.build_admission import (
    BuildProvenance,
    GeneratorId,
    add_coder_build_authority_argument,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from campaign.materializer_admission import (
    NON_ADMISSIBLE,
    NON_ADMISSIBLE_MATERIALIZERS,
    non_admissible_materializer,
)
from campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, STOCK, SourceEvidence


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "orchestrator" / "campaign"

CODER_DRIVERS = (
    "p3_kickoff.py",
    "p3_s4_red.py",
    "p3_s4_loop.py",
    "p3_s4_loop_sort.py",
    "p3_s4_loop_trigger_gating.py",
)

MACHINE_CALLERS = {
    "backoff_overthrottle.py": "BACKOFF_OVERTHROTTLE",
    "backoff_profile.py": "BACKOFF_PROFILE",
    "backoff_repro.py": "BACKOFF_REPRO",
    "backoff_sweep.py": "BACKOFF_SWEEP",
    "s1_verify_extime_calibration.py": "S1_EXTIME_CALIBRATION",
}

MANUAL_BUILD_FILES = {
    "s2_verify_calibration.py",
    "s3_lock_coverage.py",
    "s5_permutation_coverage.py",
    "s8a_trigger_coverage.py",
    "silo_ladder_rung1.py",
    "t152_write_intent_coverage.py",
}

ADMITTED_MANUAL_BUILD_FILES = {"s8a_trigger_coverage.py"}

EXPECTED_NON_ADMISSIBLE = {
    "orchestrator.campaign.s2_verify_calibration._broken_build_and_verify",
    "orchestrator.campaign.s3_lock_coverage._build_broken",
    "orchestrator.campaign.s5_permutation_coverage._build_broken",
    "orchestrator.campaign.t152_write_intent_coverage._build",
    "orchestrator.campaign.silo_ladder_rung1._build_variant",
    "orchestrator.campaign.silo_ladder_rung1._correctness_command",
}


def _source(*, stock: bool, ccbench_commit: str = "historical-test-pin") -> SourceEvidence:
    return SourceEvidence(
        schema_version="source-evidence/v1",
        source_root="/tmp/izanagi-u3-source",
        ccbench_commit=ccbench_commit,
        genome_sha256="1" * 64,
        src_token=STOCK if stock else "2" * 64,
        source_bytes_sha256="3" * 64,
        tracked_clean=stock,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256 if stock else "4" * 64,
        tracked_paths=() if stock else ("cc/silo/include/transaction.hh",),
    )


def test_all_five_drivers_issue_opaque_authority():
    for name in CODER_DRIVERS:
        tree = ast.parse((CAMPAIGN / name).read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert any(call.func.id == "add_coder_build_authority_argument" for call in calls), name
        assert not any(
            call.func.id == "BuildAdmission" for call in calls
        ), name
        run_calls = [call for call in calls if call.func.id == "run_campaign"]
        assert run_calls, name
        assert all(
            any(keyword.arg == "build_context" for keyword in call.keywords)
            and not any(keyword.arg == "admission" for keyword in call.keywords)
            for call in run_calls
        ), name


def test_stock_machine_and_opted_in_coder_paths_remain_accepted():
    stock_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    repo_pin = stock_context.policy.as_preimage()["repo_stock_pin"]
    assert derive_build_admission(
        stock_context, _source(stock=True, ccbench_commit=repo_pin),
    ).provenance is BuildProvenance.STOCK_BASELINE

    machine_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    machine_source = _source(stock=False)
    generator_receipt = attest_generator_output(
        machine_context, machine_source, generator_input_sha256="5" * 64,
    )
    assert derive_build_admission(
        machine_context, machine_source, generator_receipt=generator_receipt,
    ).provenance is BuildProvenance.MACHINE_GENERATED

    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    authority = parser.parse_args(["--allow-coder-derived-build"]).coder_build_authority
    coder_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=authority,
    )
    admission = derive_build_admission(coder_context, _source(stock=False))
    assert admission.provenance is BuildProvenance.CODER_AUTHORED
    assert "nonce" not in repr(coder_context.policy.as_preimage()).lower()


def test_dirty_noop_stock_token_enters_coder_admission_namespace():
    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=parser.parse_args(
            ["--allow-coder-derived-build"]
        ).coder_build_authority,
    )
    dirty_noop = replace(_source(stock=False), src_token=STOCK)
    assert derive_build_admission(
        context, dirty_noop,
    ).provenance is BuildProvenance.CODER_AUTHORED


def test_machine_callers_use_closed_generator_receipts():
    for filename, enum_name in MACHINE_CALLERS.items():
        source = (CAMPAIGN / filename).read_text(encoding="utf-8")
        assert "attest_generator_output(" in source, filename
        assert f"GeneratorId.{enum_name}" in source, filename
        assert "BuildProvenance" not in source, filename
    coverage = (CAMPAIGN / "s8a_trigger_coverage.py").read_text(encoding="utf-8")
    assert "GeneratorId.S8A_TRIGGER_SWEEP" in coverage
    assert "attest_generator_output(" in coverage
    assert "require_build_admission(" in coverage
    frequency = (CAMPAIGN / "s8a_trigger_freq.py").read_text(encoding="utf-8")
    assert "admission_receipts=result[\"build_admissions\"]" in frequency


def test_python_ccbench_manual_materializers_are_explicitly_non_admissible():
    actual_manual_files = {
        path.name for path in CAMPAIGN.glob("*.py")
        if "--build" in path.read_text(encoding="utf-8")
        and path.name != "buildcache.py"
    }
    assert actual_manual_files == MANUAL_BUILD_FILES
    for filename in ADMITTED_MANUAL_BUILD_FILES:
        assert "require_build_admission(" in (CAMPAIGN / filename).read_text(
            encoding="utf-8"
        )
    assert set(NON_ADMISSIBLE_MATERIALIZERS) == EXPECTED_NON_ADMISSIBLE
    for materializer in EXPECTED_NON_ADMISSIBLE:
        classification = non_admissible_materializer(materializer)
        assert classification["admission_status"] == NON_ADMISSIBLE
        assert classification["materializer"] == materializer
        assert classification["reason"]


def test_registry_declares_intentionally_unclosed_surfaces():
    doc = __import__(
        "campaign.materializer_admission", fromlist=["__doc__"]
    ).__doc__ or ""
    assert "tools/pegasus/*.sh" in doc
    assert "arbitrary binary path" in doc
