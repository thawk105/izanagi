# -*- coding: utf-8 -*-
"""T-342 evidence-derived build admission controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR))

from campaign import build_admission, source_digest  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    ADMISSION_SCHEMA,
    ADMISSION_SCHEMA_V2,
    REVIEW_RECEIPT_SCHEMA,
    BuildAdmission,
    BuildAdmissionError,
    BuildProvenance,
    GeneratorId,
    ReviewId,
    TriggerGateReceipt,
    add_coder_build_authority_argument,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    issue_trigger_gate_receipt,
    require_build_admission,
    require_trigger_gate_receipt,
    validate_build_admission_receipt,
    verify_review_receipt,
)
from campaign.model import Genome  # noqa: E402
from campaign.pin import CURRENT_PIN  # noqa: E402
from campaign.source_digest import (  # noqa: E402
    SOURCE_EVIDENCE_SCHEMA,
    SOURCE_EVIDENCE_SCHEMA_V2,
    STOCK,
    SourceEvidence,
)
from campaign.trigger_gate_language import TRIGGER_GATE_LANGUAGE  # noqa: E402


_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64


def _source(
    *,
    commit: str = CURRENT_PIN,
    token: str = STOCK,
    clean: bool = True,
    root: str = "/evidence/ccbench",
) -> SourceEvidence:
    return SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=root,
        ccbench_commit=commit,
        genome_sha256=_SHA_A,
        src_token=token,
        source_bytes_sha256=_SHA_B,
        tracked_clean=clean,
        tracked_diff_sha256=(
            source_digest.EMPTY_TRACKED_DIFF_SHA256 if clean else _SHA_C
        ),
        tracked_paths=() if clean else ("include/backoff.hh",),
    )


def _write_trigger_source(root: Path, implementation: bytes) -> None:
    path = root / source_digest.TRIGGER_GATE_SOURCE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
        b"#if BACKOFF_TRIGGER_GATING\n"
        + implementation
        + b"\n#else\n  Backoff::backoff(FLAGS_clocks_per_us);\n#endif\n"
        b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
    )


def _trigger_source(root: Path, implementation: bytes) -> SourceEvidence:
    return SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA_V2,
        source_root=str(root.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=_SHA_A,
        src_token=_SHA_C,
        source_bytes_sha256=_SHA_B,
        tracked_clean=False,
        tracked_diff_sha256=_SHA_C,
        tracked_paths=(source_digest.TRIGGER_GATE_SOURCE_REL,),
        trigger_gate_language=TRIGGER_GATE_LANGUAGE,
        trigger_gate_implementation_sha256=hashlib.sha256(implementation).hexdigest(),
    )


def _issue_trigger(monkeypatch, source: SourceEvidence) -> TriggerGateReceipt:
    monkeypatch.setattr(
        build_admission.source_digest, "resolve_evidence",
        lambda *args, **kwargs: source,
    )
    return issue_trigger_gate_receipt(
        source, genome=Genome("silo", {"BACKOFF_TRIGGER_GATING": 1}),
    )


def _context(*, authority=None):
    return build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=authority,
    )


def _outer_sha(body: dict[str, object]) -> str:
    rendered = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _review_body(source: SourceEvidence, *, review_id=ReviewId.S1_KNOWN_AXES):
    body = {
        "schema": REVIEW_RECEIPT_SCHEMA,
        "review_id": review_id.value,
        "source": source.as_receipt(),
        "input_sha256": _SHA_A,
    }
    body["receipt_sha256"] = _outer_sha(body)
    return body


def _parser_authority():
    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    return parser.parse_args(["--allow-coder-derived-build"]).coder_build_authority


def test_direct_constructor_is_not_an_admission_path():
    with pytest.raises(BuildAdmissionError, match="derive_build_admission"):
        BuildAdmission(BuildProvenance.STOCK_BASELINE, {})


def test_clean_repo_pinned_stock_is_derived_without_authority():
    source = _source()
    context = _context()
    admission = derive_build_admission(context, source)
    assert admission.provenance is BuildProvenance.STOCK_BASELINE
    assert require_build_admission(
        admission, expected_policy=context.policy, expected_source=source
    ) is admission


def test_dirty_noop_does_not_derive_stock():
    with pytest.raises(BuildAdmissionError, match="どれも支持しない"):
        derive_build_admission(_context(), _source(clean=False))


def test_stock_requires_repo_declared_pin():
    with pytest.raises(BuildAdmissionError, match="どれも支持しない"):
        derive_build_admission(_context(), _source(commit="0123456"))


def test_registered_generator_receipt_derives_machine():
    source = _source(token=_SHA_C, clean=False)
    context = _context()
    generator = attest_generator_output(
        context, source, generator_input_sha256=_SHA_A
    )
    admission = derive_build_admission(context, source, generator_receipt=generator)
    body = admission.as_wal_receipt()
    assert admission.provenance is BuildProvenance.MACHINE_GENERATED
    assert body["generator_receipt"] == generator.as_receipt()
    assert body["generator_id"] == GeneratorId.BACKOFF_SWEEP.value
    assert body["input_sha256"] == _SHA_A


def test_generator_receipt_from_another_run_is_rejected():
    source = _source(token=_SHA_C, clean=False)
    first = _context()
    generator = attest_generator_output(first, source, generator_input_sha256=_SHA_A)
    with pytest.raises(BuildAdmissionError, match="別 run context"):
        derive_build_admission(_context(), source, generator_receipt=generator)


def test_review_receipt_is_exactly_source_bound():
    source = _source(token=_SHA_C, clean=False)
    review = verify_review_receipt(
        ReviewId.S1_KNOWN_AXES, source, receipt=_review_body(source)
    )
    admission = derive_build_admission(_context(), source, review_receipt=review)
    assert admission.provenance is BuildProvenance.HUMAN_REVIEWED
    other = _source(token=_SHA_C, clean=False, root="/other/ccbench")
    with pytest.raises(BuildAdmissionError, match="対象 source evidence"):
        verify_review_receipt(
            ReviewId.S1_KNOWN_AXES, other, receipt=_review_body(source)
        )


def test_generator_and_review_receipts_are_ambiguous():
    source = _source(token=_SHA_C, clean=False)
    context = _context()
    generator = attest_generator_output(context, source, generator_input_sha256=_SHA_A)
    review = verify_review_receipt(
        ReviewId.S1_KNOWN_AXES, source, receipt=_review_body(source)
    )
    with pytest.raises(BuildAdmissionError, match="同時提示は曖昧"):
        derive_build_admission(
            context, source, generator_receipt=generator, review_receipt=review
        )


def test_coder_requires_parser_issued_run_token():
    source = _source(token=_SHA_C, clean=False)
    with pytest.raises(BuildAdmissionError, match="exact type"):
        build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=True)

    @dataclass(frozen=True)
    class FakeAuthority:
        _nonce: str

    with pytest.raises(BuildAdmissionError, match="exact type"):
        build_run_context(
            generator_id=GeneratorId.BACKOFF_SWEEP,
            coder_authority=FakeAuthority("0" * 64),
        )
    authority = _parser_authority()
    context = _context(authority=authority)
    admission = derive_build_admission(context, source)
    assert admission.provenance is BuildProvenance.CODER_AUTHORED
    with pytest.raises(BuildAdmissionError, match="別 run context で既に使用済み"):
        _context(authority=authority)


def test_cli_nonce_is_not_serialized():
    authority = _parser_authority()
    context = _context(authority=authority)
    admission = derive_build_admission(context, _source(token=_SHA_C, clean=False))
    rendered = json.dumps(admission.as_wal_receipt(), sort_keys=True)
    assert authority._nonce not in rendered
    assert "context_nonce" not in rendered
    assert admission.as_wal_receipt()["authority_kind"] == "cli-opt-in"


def test_persistent_receipt_has_exact_full_canonical_body():
    source = _source(token=_SHA_C, clean=False)
    context = _context()
    generator = attest_generator_output(context, source, generator_input_sha256=_SHA_A)
    admission = derive_build_admission(context, source, generator_receipt=generator)
    body = admission.as_cache_identity()
    assert set(body) == {
        "schema", "class", "policy_sha256", "source", "generator_id", "review_id",
        "input_sha256", "generator_receipt", "review_receipt", "authority_kind",
        "receipt_sha256",
    }
    assert body["schema"] == ADMISSION_SCHEMA
    assert body["source"] == source.as_receipt()
    assert isinstance(body["generator_receipt"], dict)
    assert validate_build_admission_receipt(
        body, expected_policy=context.policy, expected_source=source
    ) == body


def test_persistent_receipt_rejects_unknown_key_and_outer_sha_mutation():
    source = _source()
    context = _context()
    body = dict(derive_build_admission(context, source).as_wal_receipt())
    body["unknown"] = None
    with pytest.raises(BuildAdmissionError, match="key 集合"):
        validate_build_admission_receipt(body, expected_policy=context.policy)
    body.pop("unknown")
    body["class"] = BuildProvenance.CODER_AUTHORED.value
    with pytest.raises(BuildAdmissionError, match="outer SHA"):
        validate_build_admission_receipt(body, expected_policy=context.policy)


def test_receipt_validation_binds_source_root():
    source = _source()
    context = _context()
    admission = derive_build_admission(context, source)
    with pytest.raises(BuildAdmissionError, match="source evidence/root"):
        require_build_admission(
            admission,
            expected_policy=context.policy,
            expected_source=_source(root="/different/ccbench"),
        )


def test_resolve_evidence_captures_one_status_snapshot_and_tracked_diff(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(tuple(args))
        if args[-2:] == ["status", "--porcelain"]:
            return SimpleNamespace(
                returncode=0,
                stdout=" M include/backoff.hh\n?? build/generated.o\n",
                stderr="",
            )
        if "diff" in args:
            return SimpleNamespace(returncode=0, stdout=b"tracked binary diff", stderr=b"")
        raise AssertionError(args)

    monkeypatch.setattr(source_digest.subprocess, "run", fake_run)
    monkeypatch.setattr(source_digest, "assert_includes_match_head", lambda *a, **k: None)
    monkeypatch.setattr(source_digest, "assert_conditional_macros_covered", lambda *a, **k: None)
    monkeypatch.setattr(source_digest, "compute", lambda *a, **k: _SHA_B)
    monkeypatch.setattr(source_digest, "baseline", lambda *a, **k: _SHA_A)
    genome = Genome("silo", {"BACKOFF": 1})
    evidence = source_digest.resolve_evidence(
        genome, CURRENT_PIN, ccbench_dir="/tmp/../tmp/ccbench"
    )
    assert evidence.source_root == os.path.realpath("/tmp/../tmp/ccbench")
    assert evidence.tracked_clean is False
    assert evidence.tracked_paths == ("include/backoff.hh",)
    assert evidence.tracked_diff_sha256 == hashlib.sha256(b"tracked binary diff").hexdigest()
    assert evidence.src_token == _SHA_B
    assert sum(call[-2:] == ("status", "--porcelain") for call in calls) == 1


def test_source_evidence_receipt_is_exact_and_rejects_forged_clean_bit():
    source = _source(clean=False)
    assert SourceEvidence.from_receipt(source.as_receipt()) == source
    forged = source.as_receipt()
    forged["tracked_clean"] = True
    with pytest.raises(ValueError, match="tracked_clean"):
        SourceEvidence.from_receipt(forged)


@pytest.mark.parametrize("flag", [0, 1])
def test_resolve_trigger_evidence_records_actual_hole_for_marker_or_flag(
        tmp_path, monkeypatch, flag):
    implementation = b"  izanagi_gate_pass = true;"
    _write_trigger_source(tmp_path, implementation)
    monkeypatch.setattr(
        source_digest,
        "_tracked_status_paths",
        lambda *_args, **_kwargs: (source_digest.TRIGGER_GATE_SOURCE_REL,),
    )
    monkeypatch.setattr(
        source_digest, "_tracked_diff_sha256", lambda *_args, **_kwargs: _SHA_C,
    )
    monkeypatch.setattr(source_digest, "assert_includes_match_head", lambda *a, **k: None)
    monkeypatch.setattr(
        source_digest, "assert_conditional_macros_covered", lambda *a, **k: None,
    )
    monkeypatch.setattr(source_digest, "compute", lambda *a, **k: _SHA_B)
    monkeypatch.setattr(source_digest, "baseline", lambda *a, **k: _SHA_A)
    genome = Genome("silo", {"BACKOFF_TRIGGER_GATING": flag})
    evidence = source_digest.resolve_evidence(
        genome, CURRENT_PIN, ccbench_dir=str(tmp_path),
    )
    assert evidence.schema_version == SOURCE_EVIDENCE_SCHEMA_V2
    assert evidence.trigger_gate_language == TRIGGER_GATE_LANGUAGE
    assert evidence.trigger_gate_implementation_sha256 == hashlib.sha256(
        implementation
    ).hexdigest()
    assert set(evidence.as_receipt()) == SourceEvidence._KEYS_V2


def test_resolve_trigger_flag_without_actual_marker_fails_before_digest(
        tmp_path, monkeypatch):
    monkeypatch.setattr(
        source_digest,
        "compute",
        lambda *a, **k: pytest.fail("digest reached without required trigger marker"),
    )
    with pytest.raises(source_digest.TriggerGateSourceError):
        source_digest.resolve_evidence(
            Genome("silo", {"BACKOFF_TRIGGER_GATING": 1}),
            CURRENT_PIN,
            ccbench_dir=str(tmp_path),
        )


def test_trigger_source_rejects_substituted_if_expression(tmp_path):
    path = tmp_path / source_digest.TRIGGER_GATE_SOURCE_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(
        b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
        b"#if BACKOFF_TRIGGER_GATING && 0\n"
        b"  izanagi_gate_pass = true;\n"
        b"#else\n"
        b"  Backoff::backoff(FLAGS_clocks_per_us);\n"
        b"#endif\n"
        b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
    )
    with pytest.raises(source_digest.TriggerGateSourceError):
        source_digest.inspect_trigger_gate_source(str(tmp_path), required=True)


def test_trigger_receipt_has_no_persistent_issued_field_and_binds_v2_source(
        tmp_path, monkeypatch):
    implementation = b"  izanagi_gate_pass = true;"
    _write_trigger_source(tmp_path, implementation)
    source = _trigger_source(tmp_path, implementation)
    receipt = _issue_trigger(monkeypatch, source)
    body = receipt.as_receipt()
    assert set(body) == {
        "schema", "trigger_gate_language", "implementation_sha256", "source",
        "receipt_sha256",
    }
    assert "issued" not in json.dumps(body, sort_keys=True)
    context = _context(authority=_parser_authority())
    admission = derive_build_admission(
        context, source, trigger_gate_receipt=receipt,
    )
    assert admission.as_wal_receipt()["schema"] == ADMISSION_SCHEMA_V2
    assert admission.as_wal_receipt()["trigger_gate_receipt"] == body


def test_trigger_v2_requires_sealed_exact_receipt_and_v1_refuses_one(
        tmp_path, monkeypatch):
    implementation = b"  izanagi_gate_pass = true;"
    _write_trigger_source(tmp_path, implementation)
    source = _trigger_source(tmp_path, implementation)
    receipt = _issue_trigger(monkeypatch, source)
    with pytest.raises(BuildAdmissionError, match="exact value"):
        derive_build_admission(
            _context(authority=_parser_authority()), source,
            trigger_gate_receipt=object(),
        )
    forged = object.__new__(TriggerGateReceipt)
    object.__setattr__(forged, "_body_json", receipt._body_json)
    object.__setattr__(forged, "_runtime_seal", object())
    with pytest.raises(BuildAdmissionError, match="runtime seal"):
        require_trigger_gate_receipt(forged, expected_source=source)
    with pytest.raises(BuildAdmissionError, match="v1"):
        derive_build_admission(_context(), _source(), trigger_gate_receipt=receipt)


def test_m10_issue_trigger_receipt_rejects_invalid_actual_source(tmp_path, monkeypatch):
    implementation = b"  izanagi_gate_pass = true;\rSECRET_CANARY"
    _write_trigger_source(tmp_path, implementation)
    source = _trigger_source(tmp_path, implementation)
    with pytest.raises(BuildAdmissionError) as caught:
        _issue_trigger(monkeypatch, source)
    assert "SECRET_CANARY" not in repr(caught.value)


def test_m11_trigger_receipt_requires_exact_type_not_subclass(tmp_path, monkeypatch):
    implementation = b"  izanagi_gate_pass = true;"
    _write_trigger_source(tmp_path, implementation)
    source = _trigger_source(tmp_path, implementation)
    receipt = _issue_trigger(monkeypatch, source)

    class ForgedTriggerGateReceipt(TriggerGateReceipt):
        pass

    forged = object.__new__(ForgedTriggerGateReceipt)
    object.__setattr__(forged, "_body_json", receipt._body_json)
    object.__setattr__(forged, "_runtime_seal", receipt._runtime_seal)
    with pytest.raises(BuildAdmissionError, match="exact value"):
        require_trigger_gate_receipt(forged, expected_source=source)


@pytest.mark.parametrize(
    ("changed_path", "changed_source_sha"),
    [
        ("cmake/Options.cmake", _SHA_B),
        (source_digest.TRIGGER_GATE_SOURCE_REL, "d" * 64),
    ],
)
def test_trigger_receipt_refuses_fresh_options_or_backoff_evidence_change(
        tmp_path, monkeypatch, changed_path, changed_source_sha):
    implementation = b"  izanagi_gate_pass = true;"
    _write_trigger_source(tmp_path, implementation)
    source = _trigger_source(tmp_path, implementation)
    changed = replace(
        source,
        source_bytes_sha256=changed_source_sha,
        tracked_paths=(changed_path,),
    )
    monkeypatch.setattr(
        build_admission.source_digest, "resolve_evidence",
        lambda *args, **kwargs: changed,
    )
    with pytest.raises(BuildAdmissionError, match="current SourceEvidence"):
        issue_trigger_gate_receipt(
            source, genome=Genome("silo", {"BACKOFF_TRIGGER_GATING": 1}),
        )


@pytest.mark.parametrize(
    "implementation",
    [
        b"  izanagi_gate_pass = true;\rSECRET_CANARY",
        b"  izanagi_gate_pass = true;\x00SECRET_CANARY",
        b"  izanagi_gate_pass = true;\xffSECRET_CANARY",
    ],
)
def test_actual_source_binary_reject_does_not_leak_canary(tmp_path, implementation):
    _write_trigger_source(tmp_path, implementation)
    with pytest.raises(source_digest.TriggerGateSourceError) as caught:
        source_digest.inspect_trigger_gate_source(str(tmp_path), required=True)
    rendered = repr(caught.value)
    assert "SECRET_CANARY" not in rendered
    assert caught.value.__cause__ is None


def _run() -> int:
    """pytest fixtures を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
