"""Required gate witness routing for campaign evaluation."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from orchestrator.campaign import loop, pipeline
from orchestrator.campaign import buildcache
from orchestrator.campaign import source_digest
from orchestrator.campaign.model import CampaignConfig, Genome
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.pipeline import EvalResult, PerfConfig


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_m1_flag_forces_required_evaluate(tmp_path):
    from orchestrator.tests import test_campaign as support
    from orchestrator.tests.test_verifier_capability_gate_witness import _root
    from orchestrator.verifier.model import capture_compiled_protocol_source_snapshot

    support._refresh_certified_writer_authority()
    genome = Genome("silo", {"SILO_ORDER_VARIANT": 1})
    root = _root(tmp_path / "source", emitter=True)
    observed = []
    for explicit in ({}, {"require_gate_witness": False}):
        layout = support._tmp_layout()
        support._write_certified_lock(layout, support._bound(support._cfg()))
        with support._mock_pipeline() as _calls:
            mock_build = pipeline.buildcache.build

            def build_with_requirement(*args, require_gate_witness=False, **kwargs):
                assert require_gate_witness is True
                return mock_build(*args, **kwargs)

            pipeline.buildcache.build = build_with_requirement
            def resolve(candidate, commit, *, require_gate_witness=False, **_kwargs):
                return replace(
                    support._source_evidence(candidate, commit, source_root=str(root)),
                    proof_source_snapshot=capture_compiled_protocol_source_snapshot(
                        candidate.protocol, root,
                        require_gate_witness=require_gate_witness),
                    verification_variant=source_digest.verification_variant_id(candidate),
                )

            pipeline.source_digest.resolve_evidence = resolve
            downstream = pipeline.verify_trace_dir_with_capability

            def spy(trace_dir, **kwargs):
                observed.append(kwargs.get("require_gate_witness"))
                return downstream(trace_dir, **kwargs)

            pipeline.verify_trace_dir_with_capability = spy
            pipeline.evaluate(
                genome, layout, support._AUTH_CONTRACT.env_tag, CURRENT_PIN,
                PerfConfig(records=1, threads=1), support._AUTH_CONTRACT.clocks_per_us,
                numactl=list(support._AUTH_CONTRACT.numactl),
                do_bench=False, log=lambda *_args: None,
                authorization_contract=support._AUTHORIZATION,
                build_context=support._BUILD_CONTEXT,
                **explicit,
            )
    assert observed == [True, True]


def test_required_repetition_reaches_capability(tmp_path):
    from orchestrator.tests.test_verifier_capability_gate_witness import _binding, _root, TRACE

    binding = _binding(_root(tmp_path / "source", emitter=True), gate=True)
    observed = []
    real_verifier = pipeline.verify_trace_dir_with_capability

    def spy(trace_dir, **kwargs):
        observed.append(kwargs.get("require_gate_witness"))
        return real_verifier(trace_dir, **kwargs)

    trace = pipeline._TraceRunResult(2, 0, 0, 2, 0)
    for _ in range(2):
        outcome = pipeline._execute_verification_repetition(
            "silo.exe", str(TRACE), {}, 1800, timeout_s=1.0,
            numactl=None, build_attempt_id="fixed-attempt",
            trace_binary_sha256="b" * 64,
            include_qualification_evidence=False,
            collected_trace_result=trace, verifier_runner=spy,
            require_gate_witness=True, **binding,
        )
        from orchestrator.verifier.report import result_to_dict
        assert outcome.verify_payload["gate_witness"] == (
            result_to_dict(outcome.verify_result)["gate_witness"])
    assert observed == [True, True]


def test_m13_build_exit_rechecks_required_snapshot_for_fresh_and_hit(
        monkeypatch, tmp_path):
    import os
    from types import SimpleNamespace
    from orchestrator.campaign.build_admission import derive_build_admission
    from orchestrator.tests import test_campaign as support
    from orchestrator.tests.test_verifier_capability_gate_witness import _root
    from orchestrator.verifier.model import capture_compiled_protocol_source_snapshot

    genome = Genome("silo", {})
    sub, head, _git = support._fake_ccbench_repo()
    root = _root(Path(sub), emitter=True)
    legacy_evidence = support._source_evidence(genome, head, source_root=sub)
    evidence = replace(
        legacy_evidence,
        proof_source_snapshot=capture_compiled_protocol_source_snapshot(
            "silo", root, require_gate_witness=True),
    )
    admission = derive_build_admission(support._BUILD_CONTEXT, evidence)
    observed = []

    def resolve(candidate, commit, *, require_gate_witness=False, **kwargs):
        observed.append(require_gate_witness)
        return evidence if require_gate_witness else legacy_evidence

    def fake_run(cmd, what):
        if what == "build":
            staging = cmd[cmd.index("--build") + 1]
            binary = os.path.join(staging, "cc", "silo", "ycsb_silo.exe")
            os.makedirs(os.path.dirname(binary), exist_ok=True)
            with open(binary, "w") as stream:
                stream.write("fake-binary")

    monkeypatch.setattr(buildcache, "source_digest", SimpleNamespace(
        STOCK="stock", resolve_evidence=resolve,
        assert_worktree_within_allowlist=lambda *a, **k: None,
        assert_trace_diff_matches_head=lambda *a, **k: None,
    ))
    monkeypatch.setattr(buildcache, "_run", fake_run)
    results = [
        buildcache.build(
            genome, head, trace=True, cache_root=str(tmp_path / "cache"),
            ccbench_dir=sub, src_token="stock",
            build_context=support._BUILD_CONTEXT, admission=admission,
            source_evidence=evidence,
            require_gate_witness=True,
        )
        for _ in range(2)
    ]
    assert [result.cached for result in results] == [False, True]
    legacy = buildcache.build(
        genome, head, trace=True, cache_root=str(tmp_path / "cache"),
        ccbench_dir=sub, src_token="stock",
        build_context=support._BUILD_CONTEXT, admission=admission,
        source_evidence=legacy_evidence,
    )
    assert legacy.cached
    assert observed == [True, True, False]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_m2_explicit_requirement_passes_run_campaign(monkeypatch, tmp_path):
    from orchestrator.tests import test_campaign as support

    support._refresh_certified_writer_authority()
    genome = Genome("silo", {"SILO_ORDER_VARIANT": 0})
    observed = []
    observed_source = []

    def evaluate(candidate, *_args, **kwargs):
        observed.append(kwargs.get("require_gate_witness"))
        return EvalResult(
            genome=candidate,
            variant=pipeline.variant_id(candidate, kwargs["src_token"]),
            certified=True, aborted=False)

    monkeypatch.setattr(loop, "evaluate", evaluate)
    source_stub = support._sd_mock("stock")
    original_resolve = source_stub.resolve_evidence

    def resolve(*args, require_gate_witness=False, **kwargs):
        observed_source.append(require_gate_witness)
        return original_resolve(*args, **kwargs)

    source_stub.resolve_evidence = resolve
    monkeypatch.setattr(loop, "source_digest", source_stub)
    loop.run_campaign(
        CampaignConfig(spec_slug="gate-witness-explicit", search_tag="test",
                       spec_content="gate witness forwarding", ccbench_commit="deadbeef"),
        [genome], PerfConfig(records=1, threads=1),
        support._AUTH_CONTRACT.env_tag, support._AUTH_CONTRACT.clocks_per_us,
        numactl=list(support._AUTH_CONTRACT.numactl), do_bench=False,
        output_root=str(tmp_path / "campaign"), log=lambda *_args: None,
        authorization_contract=support._AUTHORIZATION,
        build_context=support._BUILD_CONTEXT, declared_use_class="official",
        require_gate_witness=True,
    )
    assert observed == [True]
    assert observed_source == [True]


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
