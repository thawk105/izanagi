# -*- coding: utf-8 -*-
"""U3 caller/CLI authority and bounded materializer inventory gates."""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import os
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH))

from campaign import pipeline
from campaign import p3_s4_loop as L
from campaign import p3_s4_loop_trigger_gating as TRIGGER
from campaign import s6_sort_sweep as S6
from campaign import wal
from campaign import env_contract
from campaign.auditor_gate import AuditorVerdict

from campaign.build_admission import (
    BuildProvenance,
    GeneratorId,
    add_coder_build_authority_argument,
    build_run_context,
    derive_build_admission,
)
from campaign.materializer_admission import (
    NON_ADMISSIBLE,
    NON_ADMISSIBLE_MATERIALIZERS,
    non_admissible_materializer,
)
from campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, STOCK, SourceEvidence
from campaign.layout import CampaignLayout
from campaign.model import Genome


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

_EXPECTED_REPO_STOCK_PIN = "d706650"


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


def _pipeline_admission(source, context, *, capability_resolver=None):
    genome = Genome("silo", {"BACK_OFF": 1})
    source = replace(
        source,
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
    )
    root = tempfile.mkdtemp(prefix="izanagi_p3_admission_positive_")
    layout = CampaignLayout(root=root).ensure()
    seen = []

    def stop_at_build(_genome, _commit, trace, **kwargs):
        assert trace is True
        seen.append(kwargs["admission"].provenance)
        raise RuntimeError("stop after public pipeline admission")

    try:
        with mock.patch.object(
                pipeline.source_digest, "resolve_evidence",
                lambda *_args, **_kwargs: source), mock.patch.object(
                    pipeline.buildcache, "build", stop_at_build):
            result = pipeline.evaluate(
                genome, layout, "test-env", source.ccbench_commit,
                pipeline.PerfConfig(records=1, threads=1), 1800,
                do_bench=False, log=lambda *_args: None,
                build_context=context,
                capability_resolver=capability_resolver,
                src_token=source.src_token,
            )
        records = wal.read_records(layout)
        return result, seen, records
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _public_s6_machine_admission():
    root = tempfile.mkdtemp(prefix="izanagi_p3_s6_public_")
    ccbench = os.path.join(root, "external", "ccbench")
    os.makedirs(ccbench)
    layout = CampaignLayout(root=os.path.join(root, "campaign")).ensure()
    machine_name = S6.CANDIDATES[0][0]
    seen = []
    passed = SimpleNamespace(passed=True)

    def evidence_for(genome, commit, source_root):
        assert commit == _EXPECTED_REPO_STOCK_PIN == S6.PIN
        return SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.abspath(source_root),
            ccbench_commit=_EXPECTED_REPO_STOCK_PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="6" * 64,
            source_bytes_sha256="7" * 64,
            tracked_clean=False,
            tracked_diff_sha256="8" * 64,
            tracked_paths=("cc/silo/transaction.cc",),
        )

    def resolve(genome, commit, ccbench_dir="", **_kwargs):
        return evidence_for(genome, commit, ccbench_dir).src_token

    def resolve_evidence(genome, commit, *, ccbench_dir="", **_kwargs):
        return evidence_for(genome, commit, ccbench_dir)

    def stop_at_build(_genome, _commit, trace, **kwargs):
        assert trace is True
        seen.append(kwargs["admission"].provenance)
        raise RuntimeError("stop after public S6 admission")

    def run_through_pipeline(cfg, genomes, perf, env_tag, clocks_per_us, **kwargs):
        result = pipeline.evaluate(
            genomes[0], layout, env_tag, cfg.ccbench_commit, perf,
            clocks_per_us, do_bench=False, log=lambda *_args: None,
            ccbench_dir=kwargs["ccbench_dir"],
            cache_root=kwargs["cache_root"],
            build_context=kwargs["build_context"],
            capability_resolver=kwargs["capability_resolver"],
        )
        return SimpleNamespace(results=[result])

    try:
        from campaign import patchharness
        with contextlib.ExitStack() as stack:
            for target, name, value in (
                    (S6, "_assert_single_tenant", lambda: None),
                    (S6, "_repo_root", lambda: root),
                    (S6, "campaign_layout", lambda _campaign_id: layout),
                    (patchharness, "assert_pinned_clean", lambda *_args: None),
                    (patchharness, "applied",
                     lambda *_args, **_kwargs: contextlib.nullcontext()),
                    (L, "quarantine", lambda *_args, **_kwargs: (passed, "", "", "")),
                    (S6.source_digest, "resolve", resolve),
                    (pipeline.source_digest, "resolve_evidence", resolve_evidence),
                    (pipeline.buildcache, "build", stop_at_build),
                    (S6, "run_campaign", run_through_pipeline)):
                stack.enter_context(mock.patch.object(target, name, value))
            S6.run_sweep(
                "balanced", names=[machine_name], isolate=False,
                log=lambda *_args: None,
            )
        return seen
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_stock_machine_and_opted_in_coder_paths_remain_accepted():
    stock_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    stock_result, stock_seen, _ = _pipeline_admission(
        _source(stock=True, ccbench_commit=_EXPECTED_REPO_STOCK_PIN),
        stock_context,
    )
    assert stock_result.aborted and stock_seen == [BuildProvenance.STOCK_BASELINE]

    assert _public_s6_machine_admission() == [BuildProvenance.MACHINE_GENERATED]

    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    authority = parser.parse_args(["--allow-coder-derived-build"]).coder_build_authority
    coder_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=authority,
    )
    coder_result, coder_seen, _ = _pipeline_admission(
        _source(stock=False), coder_context,
    )
    assert coder_result.aborted and coder_seen == [BuildProvenance.CODER_AUTHORED]
    assert "nonce" not in repr(coder_context.policy.as_preimage()).lower()


def test_authorityless_trigger_coder_is_rejected_before_build_spy():
    root = tempfile.mkdtemp(prefix="izanagi_p3_trigger_negative_")
    layout = CampaignLayout(root=os.path.join(root, "campaign")).ensure()
    sub = os.path.join(root, "ccbench")
    os.makedirs(sub)
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    contract = env_contract.lookup(TRIGGER.ENV_TAG)
    seen = []

    def dirty_evidence(genome, commit, *, ccbench_dir="", **_kwargs):
        assert commit == _EXPECTED_REPO_STOCK_PIN == TRIGGER.PIN
        return SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.abspath(ccbench_dir),
            ccbench_commit=_EXPECTED_REPO_STOCK_PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="2" * 64,
            source_bytes_sha256="3" * 64,
            tracked_clean=False,
            tracked_diff_sha256="4" * 64,
            tracked_paths=("cc/silo/transaction.cc",),
        )

    def build_spy(*_args, **_kwargs):
        seen.append(_kwargs)
        raise AssertionError("authorityless trigger source reached build")

    def run_through_pipeline(cfg, genomes, perf, env_tag, clocks_per_us, **kwargs):
        result = pipeline.evaluate(
            genomes[0], layout, env_tag, cfg.ccbench_commit, perf,
            clocks_per_us, do_bench=False, log=lambda *_args: None,
            ccbench_dir=kwargs["ccbench_dir"],
            cache_root=kwargs["cache_root"],
            build_context=kwargs["build_context"],
        )
        return SimpleNamespace(results=[result], skipped=0)

    planner = L.PlannerProposal(
        axis=TRIGGER.MARKER_ID, direction="explore_both", magnitude="small",
    )
    coder = TRIGGER.CoderProposalTriggerGating(
        axis=TRIGGER.MARKER_ID,
        implementation="izanagi_gate_pass = true;",
    )
    auditor = AuditorVerdict(verdict="pass", diff_digest="fixture")
    try:
        from campaign import patchharness
        with contextlib.ExitStack() as stack:
            for target, name, value in (
                    (TRIGGER, "_current_site", lambda: TRIGGER.site_policy.OTHER),
                    (TRIGGER, "_lookup", lambda _env_tag: contract),
                    (TRIGGER, "exploration_campaign_layout", lambda _cid: layout),
                    (TRIGGER, "_assert_resume_allowed", lambda *_args: None),
                    (TRIGGER, "_quarantine_and_audit", lambda *_args, **_kwargs: None),
                    (patchharness, "applied",
                     lambda *_args, **_kwargs: contextlib.nullcontext()),
                    (pipeline.source_digest, "resolve_evidence", dirty_evidence),
                    (pipeline.buildcache, "build", build_spy),
                    (TRIGGER, "run_campaign", run_through_pipeline)):
                stack.enter_context(mock.patch.object(target, name, value))
            outcome = TRIGGER.run_one_iteration(
                TRIGGER.default_cfg(), TRIGGER.default_perf(), planner, coder,
                auditor, L.LoopState(start_wall=0.0), sub, do_build=True,
                layout=layout, log=lambda *_args: None, build_context=context,
            )
        records = wal.read_records(layout)
        assert outcome["outcome"] == "aborted"
        assert seen == []
        assert [record.stage for record in records] == ["build_start", "abort"]
        assert records[-1].payload["reason"] == "admission-error"
        assert records[-1].payload["error"].startswith("BuildAdmissionError:")
    finally:
        shutil.rmtree(root, ignore_errors=True)


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


def _run():
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # noqa: BLE001 - plain-runner result aggregation
            failures += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
