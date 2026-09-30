"""Required gate witness routing for campaign evaluation."""
from __future__ import annotations

from dataclasses import replace

import pytest

from orchestrator.campaign import loop, pipeline
from orchestrator.campaign import source_digest
from orchestrator.campaign.model import CampaignConfig, Genome
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
                genome, layout, support._AUTH_CONTRACT.env_tag, "deadbeef",
                PerfConfig(records=1, threads=1), support._AUTH_CONTRACT.clocks_per_us,
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
        pipeline._execute_verification_repetition(
            "silo.exe", str(TRACE), {}, 1800, timeout_s=1.0,
            numactl=None, build_attempt_id="fixed-attempt",
            trace_binary_sha256="b" * 64,
            include_qualification_evidence=False,
            collected_trace_result=trace, verifier_runner=spy,
            require_gate_witness=True, **binding,
        )
    assert observed == [True, True]


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
