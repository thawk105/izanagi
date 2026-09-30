"""Capability D5 source binding and legacy byte compatibility."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign.build_admission import GeneratorId, build_run_context, derive_build_admission
from orchestrator.campaign.pipeline import _TraceRunResult, _execute_verification_repetition
from orchestrator.campaign.model import Genome
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.source_digest import (
    EMPTY_TRACKED_DIFF_SHA256, SOURCE_EVIDENCE_SCHEMA, SourceEvidence,
    deserialize_compiled_protocol_source_snapshot,
    serialize_compiled_protocol_source_snapshot,
)
from orchestrator.verifier import CAMPAIGN_WAL_SINK, verify_trace_dir_with_capability
from orchestrator.verifier.core import verify_trace_dir
from orchestrator.verifier.core import result_to_dict_v3
from orchestrator.verifier.commit_receipt import _domain_digest
from orchestrator.verifier.model import capture_compiled_protocol_source_snapshot
from orchestrator.verifier.report import result_to_dict

TRACE = Path(__file__).parent / "fixtures/g1_serial"


def _root(path: Path, *, emitter: bool) -> Path:
    (path / "include").mkdir(parents=True, exist_ok=True)
    (path / "cc/silo").mkdir(parents=True, exist_ok=True)
    (path / "cc/silo/CMakeLists.txt").write_text(
        "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n")
    (path / "include/ycsb.hh").write_text(
        "#if TRACE\n" + ("izanagi_trace::emit_steps(0);\n" if emitter else "") + "#endif\n")
    (path / "cc/silo/transaction.cc").write_text(
        "#if TRACE\nizanagi_trace::emit_lock_violation(0,0,{},{});\n"
        "izanagi_trace::stream(0) << \"P \";\n"
        "izanagi_trace::emit_write_intent_violation(0,0,{},{});\n"
        + ("izanagi_trace::emit_stored(0);\nizanagi_trace::set_gate_txid(0);\n"
           if emitter else "") + "#endif\n")
    (path / "cc/silo/ycsb_silo.cc").write_text('#include "../../include/ycsb.hh"\n')
    return path


def _binding(root: Path, *, gate: bool):
    genome = Genome("silo", {})
    variant = "gate-capability-fixture"
    snapshot = capture_compiled_protocol_source_snapshot(
        "silo", root, require_gate_witness=gate)
    source = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA, source_root=str(root),
        ccbench_commit=CURRENT_PIN, genome_sha256=hashlib.sha256(
            genome.canonical().encode()).hexdigest(), src_token="stock",
        source_bytes_sha256=hashlib.sha256(b"fixture").hexdigest(),
        tracked_clean=True, tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(), proof_source_snapshot=snapshot,
        verification_variant=variant,
    )
    admission = derive_build_admission(
        build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP), source)
    return dict(genome=genome, source_evidence=source, build_admission=admission,
                receipt_sink_kind=CAMPAIGN_WAL_SINK,
                receipt_lock_identity_sha256="a" * 64,
                receipt_variant=variant, receipt_operation_identity="op",
                receipt_workload_tag="legacy")


def test_m5_unrequested_snapshot_legacy_bytes(tmp_path):
    root = _root(tmp_path / "source", emitter=True)
    snap = capture_compiled_protocol_source_snapshot("silo", root)
    body = serialize_compiled_protocol_source_snapshot(snap)
    expected_source = (
        '#if TRACE\nizanagi_trace::emit_lock_violation(0,0,{},{});\n'
        'izanagi_trace::stream(0) << "P ";\n'
        'izanagi_trace::emit_write_intent_violation(0,0,{},{});\n'
        'izanagi_trace::emit_stored(0);\nizanagi_trace::set_gate_txid(0);\n#endif\n'
    )
    expected_bytes = (
        b'{"ccbench_root":' + json.dumps(str(root)).encode() +
        b',"normalized_sources":' + json.dumps([expected_source], separators=(",", ":")).encode() +
        b',"protocol":"silo","schema":"compiled-protocol-source-snapshot/v1"}'
    )
    assert json.dumps(body, sort_keys=True, separators=(",", ":")).encode() == expected_bytes
    assert "gate_d5_sources" not in body
    assert deserialize_compiled_protocol_source_snapshot(body) == snap
    for changed in ({key: value for key, value in body.items() if key != "protocol"},
                    {**body, "unknown": 1}, {**body, "gate_d5_sources": None},
                    {**body, "gate_d5_sources": ["", "", "", 1]}):
        with pytest.raises(ValueError):
            deserialize_compiled_protocol_source_snapshot(changed)


def test_m3_required_capability_rejects_absent_gate_file(tmp_path):
    root = _root(tmp_path / "source", emitter=True)
    binding = _binding(root, gate=True)
    baseline, _ = verify_trace_dir_with_capability(str(TRACE), **binding)
    required, _ = verify_trace_dir_with_capability(
        str(TRACE), require_gate_witness=True, **binding)
    assert baseline.certified
    assert not required.certified
    assert required.integrity.gate_witness_required is True
    assert required.integrity.gate_unreachable == 1
    assert required.integrity.gate_d5 == "pass"


def test_m4_required_d5_uses_snapshot_not_disk(tmp_path):
    root = _root(tmp_path / "source", emitter=False)
    snapshot = capture_compiled_protocol_source_snapshot(
        "silo", root, require_gate_witness=True)
    wire = serialize_compiled_protocol_source_snapshot(snapshot)
    assert "gate_d5_sources" in wire
    assert deserialize_compiled_protocol_source_snapshot(wire) == snapshot
    _root_existing = root / "include/ycsb.hh"
    _root_existing.write_text("#if TRACE\nizanagi_trace::emit_steps(0);\n#endif\n")
    (root / "cc/silo/transaction.cc").write_text(
        "#if TRACE\nizanagi_trace::emit_stored(0);\n"
        "izanagi_trace::set_gate_txid(0);\n#endif\n")
    result = verify_trace_dir(str(TRACE), protocol="silo", ccbench_root=root,
                              require_gate_witness=True,
                              _proof_source_snapshot=snapshot)
    assert result.integrity.gate_d5 == "fail"
    assert verify_trace_dir(str(TRACE), protocol="silo", ccbench_root=root,
                            require_gate_witness=True).integrity.gate_d5 == "pass"
    # The reverse direction also must use the captured evidence.
    snapshot = capture_compiled_protocol_source_snapshot(
        "silo", root, require_gate_witness=True)
    (root / "include/ycsb.hh").unlink()
    reverse = verify_trace_dir(str(TRACE), protocol="silo", ccbench_root=root,
                               require_gate_witness=True,
                               _proof_source_snapshot=snapshot)
    assert reverse.integrity.gate_d5 == "pass"
    assert verify_trace_dir(str(TRACE), protocol="silo", ccbench_root=root,
                            require_gate_witness=True).integrity.gate_d5 == "unavailable"
    other_root = _root(tmp_path / "other-source", emitter=True)
    missing_bundle = capture_compiled_protocol_source_snapshot("silo", other_root)
    unavailable = verify_trace_dir(
        str(TRACE), require_gate_witness=True,
        _proof_source_snapshot=missing_bundle)
    assert unavailable.integrity.gate_d5 == "unavailable"
    assert not unavailable.certified


def test_capability_rejects_nonbool_requirement(tmp_path):
    binding = _binding(_root(tmp_path / "source", emitter=True), gate=False)
    with pytest.raises(TypeError, match="require_gate_witness"):
        verify_trace_dir_with_capability(
            str(TRACE), require_gate_witness=1, **binding)


def test_unrequested_capability_projection_matches_legacy(tmp_path):
    root = _root(tmp_path / "source", emitter=True)
    binding = _binding(root, gate=False)
    result, capability = verify_trace_dir_with_capability(str(TRACE), **binding)
    direct = verify_trace_dir(str(TRACE),
        _proof_source_snapshot=binding["source_evidence"].proof_source_snapshot)
    assert json.dumps(result_to_dict(result), sort_keys=True).encode() == (
        json.dumps(result_to_dict(direct), sort_keys=True).encode())
    assert capability._receipt_evidence()[0:2] == (result.verdict, result.certified)
    receipt_projection = result_to_dict_v3(direct)
    receipt_projection.pop("trace_dir", None)
    receipt_projection["integrity"].pop("framing_violation_details", None)
    receipt_projection["integrity"].pop("permutation_violation_details", None)
    assert capability._receipt_evidence() == (
        direct.verdict, direct.certified,
        _domain_digest(b"izanagi-verifier-result-v1", receipt_projection),
    )
    assert result.integrity.gate_witness_required is False
    assert result.integrity.gate_d5 == "not-required"


def test_unrequested_verify_payload_keeps_legacy_bytes(tmp_path):
    root = _root(tmp_path / "source", emitter=True)
    binding = _binding(root, gate=False)
    trace = _TraceRunResult(2, 0, 3, 2, 0)
    outcome = _execute_verification_repetition(
        "silo.exe", str(TRACE), {}, 1800, timeout_s=1.0, numactl=None,
        build_attempt_id="fixed-attempt", trace_binary_sha256="b" * 64,
        include_qualification_evidence=False,
        collected_trace_result=trace, **binding,
    )
    assert outcome.abort is None
    expected = {
        "build_attempt_id": "fixed-attempt", "verdict": "serializable",
        "certified": True, "commits": 2, "aborts": 3,
        "commit_witness": {"commit_counts": 2, "batch_commit_counts": 0},
        "anomalies": 0, "workload": {"tag": "legacy"},
        "proof_surfaces": {
            "protocol": "silo", "X": "evidence-present",
            "P": "evidence-present", "I": "evidence-present",
        },
    }
    assert json.dumps(outcome.verify_payload, sort_keys=True, separators=(",", ":")).encode() == (
        json.dumps(expected, sort_keys=True, separators=(",", ":")).encode())


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
