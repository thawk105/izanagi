# -*- coding: utf-8 -*-
"""T-342 evidence-derived build admission controls."""
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import source_digest  # noqa: E402
from orchestrator.campaign.axis_trigger_gating import (  # noqa: E402
    FROZEN_TEMPLATE_BLOCK_BYTES,
    FROZEN_TEMPLATE_EPILOGUE_BYTES,
    FROZEN_TEMPLATE_HOLE_BYTES,
    MARKER_ID as TRIGGER_MARKER_ID,
    PREDICATE_HOLE_INDENT as TRIGGER_PREDICATE_HOLE_INDENT,
    SOURCE_REL as TRIGGER_SOURCE_REL,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    ADMISSION_SCHEMA,
    REVIEW_RECEIPT_SCHEMA,
    BuildAdmission,
    BuildAdmissionError,
    BuildProvenance,
    GeneratorId,
    ReviewId,
    add_coder_build_authority_argument,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    require_build_admission,
    validate_build_admission_receipt,
    verify_review_receipt,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.reflux_ir import TriggerGateIR, emit_predicate  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    SOURCE_EVIDENCE_SCHEMA,
    STOCK,
    SourceEvidence,
)


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


def _context(*, authority=None):
    return build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=authority,
    )


def test_policy_shape_literal_matches_current_schema():
    from orchestrator.campaign import build_admission as B

    current = B.resolve_current_build_admission_policy()
    preimage = current.as_preimage()
    assert B._HISTORICAL_POLICY_KEYS == frozenset(preimage)
    assert B._HISTORICAL_POLICY_SCHEMA == preimage["schema"]
    historical = B.decode_historical_build_admission_policy(preimage)
    assert type(historical) is B.HistoricalBuildAdmissionPolicy
    assert not isinstance(historical, B.BuildAdmissionPolicy)
    assert historical.sha256 == current.sha256
    # Recorded order is identity, not something the decoder may repair.
    preimage["generator_registry"].reverse()
    historical = B.decode_historical_build_admission_policy(preimage)
    assert historical.as_preimage() == preimage
    assert historical.sha256 == _outer_sha(preimage)
    preimage["generator_registry"].append("later-mutation")
    assert historical.as_preimage() != preimage


def test_historical_policy_cannot_enter_current_consumers(tmp_path):
    from orchestrator.campaign import build_admission as B, wal
    from orchestrator.campaign.layout import CampaignLayout

    context = _context()
    source = _source()
    admission = derive_build_admission(context, source)
    policy = B.decode_historical_build_admission_policy(context.policy.as_preimage())
    with pytest.raises(TypeError, match="exact value"):
        wal._validate_attempt_topology([], admission_policy=policy, campaign_lock={})
    with pytest.raises(TypeError, match="exact value"):
        wal._recover_interrupted_attempts(
            CampaignLayout(root=str(tmp_path)), admission_policy=policy,
        )
    with pytest.raises(BuildAdmissionError, match="exact value"):
        require_build_admission(admission, expected_policy=policy, expected_source=source)
    with pytest.raises(BuildAdmissionError, match="exact value"):
        validate_build_admission_receipt(admission.as_wal_receipt(), expected_policy=policy)


@pytest.mark.parametrize("mutation, message", [
    ("stock", "stock class を repo pin/clean/source evidence が支持しない"),
    ("generator", "generator receipt の generator_id が未登録"),
    ("authority", "coder-authored class は CLI authority kind が必要"),
])
@pytest.mark.parametrize("entry", ["current", "historical"])
def test_receipt_rejects_invalid_current_comparison(mutation, message, entry):
    from orchestrator.campaign import build_admission as B, wal
    from orchestrator.campaign.model import WalRecord

    source = _source() if mutation == "stock" else _source(token=_SHA_C, clean=False)
    context = _context(authority=_parser_authority()) if mutation == "authority" else _context()
    kwargs = {}
    if mutation == "generator":
        kwargs["generator_receipt"] = attest_generator_output(
            context, source, generator_input_sha256=_SHA_A,
        )
    body = derive_build_admission(context, source, **kwargs).as_wal_receipt()
    if mutation == "stock":
        body["source"]["ccbench_commit"] = "d706650"
    elif mutation == "generator":
        generator = body["generator_receipt"]
        generator["generator_id"] = "unregistered-generator"
        generator["receipt_sha256"] = _outer_sha({
            k: v for k, v in generator.items() if k != "receipt_sha256"
        })
        body["generator_id"] = generator["generator_id"]
    else:
        body["authority_kind"] = "other-authority"
    body["receipt_sha256"] = _outer_sha({
        k: v for k, v in body.items() if k != "receipt_sha256"
    })
    assert body["policy_sha256"] == B.resolve_current_build_admission_policy().sha256
    policy = context.policy
    validate = validate_build_admission_receipt
    topology = wal._validate_attempt_topology
    if entry == "historical":
        recorded = policy.as_preimage()
        if mutation == "generator":
            recorded["generator_registry"].append(body["generator_id"])
        elif mutation == "authority":
            recorded["coder_authority"] = body["authority_kind"]
        policy = B.decode_historical_build_admission_policy(recorded)
        body["policy_sha256"] = policy.sha256
        body["receipt_sha256"] = _outer_sha({
            k: v for k, v in body.items() if k != "receipt_sha256"
        })
        validate = B.validate_historical_build_admission_receipt
        topology = wal._validate_historical_attempt_topology
    with pytest.raises(BuildAdmissionError, match=message):
        validate(body, expected_policy=policy)
    # Propagation is consistent as well: rejection must reach the class comparison.
    records = [WalRecord(
        ts=1.0, stage="build_start", variant="variant", env_tag="test",
        payload={
            "build_attempt_id": "attempt",
            "build_admission": body,
            "build_admission_receipt_sha256": body["receipt_sha256"],
        },
    )]
    with pytest.raises(wal.AttemptTopologyError, match=message):
        topology(records, admission_policy=policy, campaign_lock={})


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


def _canonical_trigger_hole(mask: int) -> bytes:
    return (
        TRIGGER_PREDICATE_HOLE_INDENT + emit_predicate(TriggerGateIR(mask))
    ).encode("utf-8")


def _trigger_block_with_hole(hole: bytes) -> bytes:
    assert FROZEN_TEMPLATE_BLOCK_BYTES.count(FROZEN_TEMPLATE_HOLE_BYTES) == 1
    return FROZEN_TEMPLATE_BLOCK_BYTES.replace(FROZEN_TEMPLATE_HOLE_BYTES, hole)


def _trigger_source_bytes(
    block: bytes,
    *,
    epilogue: bytes = FROZEN_TEMPLATE_EPILOGUE_BYTES,
    after: bytes = b"int izanagi_after_block = 0;\n",
) -> bytes:
    marker_explanation = (
        b"// explanation mentions " + TRIGGER_MARKER_ID.encode("ascii") + b" only\n"
    )
    return marker_explanation + block + epilogue + after


def _write_trigger_source(tmp_path: Path, raw: bytes) -> tuple[SourceEvidence, Path]:
    root = tmp_path / "ccbench"
    target = root / TRIGGER_SOURCE_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return _source(root=str(root)), target


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


@pytest.mark.parametrize("mask", range(32), ids=lambda mask: f"mask-{mask}")
def test_trigger_axis_semantic_admission_accepts_exact_emitter_bytes_without_binding(
    tmp_path: Path, mask: int,
):
    block = _trigger_block_with_hole(_canonical_trigger_hole(mask))
    source, _ = _write_trigger_source(tmp_path, _trigger_source_bytes(block))
    admission = derive_build_admission(_context(), source)
    assert admission.provenance is BuildProvenance.STOCK_BASELINE


def test_trigger_axis_semantic_admission_accepts_pristine_frozen_block(tmp_path: Path):
    source, _ = _write_trigger_source(
        tmp_path, _trigger_source_bytes(FROZEN_TEMPLATE_BLOCK_BYTES)
    )
    assert derive_build_admission(_context(), source).provenance is (
        BuildProvenance.STOCK_BASELINE
    )


@pytest.mark.parametrize(
    "after",
    [
        pytest.param(
            b"\n#if ADD_ANALYSIS\nint izanagi_after_block = 0;\n#endif\n",
            id="analysis-code",
        ),
        pytest.param(FROZEN_TEMPLATE_EPILOGUE_BYTES, id="duplicated-epilogue"),
    ],
)
def test_trigger_axis_semantic_admission_does_not_freeze_bytes_after_epilogue(
    tmp_path: Path, after: bytes,
):
    source, _ = _write_trigger_source(
        tmp_path,
        _trigger_source_bytes(
            FROZEN_TEMPLATE_BLOCK_BYTES,
            after=after,
        ),
    )
    assert derive_build_admission(_context(), source).provenance is (
        BuildProvenance.STOCK_BASELINE
    )


@pytest.mark.parametrize(
    "epilogue",
    [
        pytest.param(b"", id="deleted"),
        pytest.param(
            FROZEN_TEMPLATE_EPILOGUE_BYTES.replace(
                b"if (izanagi_gate_pass)", b"if (!izanagi_gate_pass)"
            ),
            id="modified",
        ),
        pytest.param(
            b"\n" + FROZEN_TEMPLATE_EPILOGUE_BYTES,
            id="gap-before",
        ),
    ],
)
def test_trigger_axis_semantic_admission_rejects_noncanonical_epilogue(
    tmp_path: Path, epilogue: bytes,
):
    source, _ = _write_trigger_source(
        tmp_path,
        _trigger_source_bytes(FROZEN_TEMPLATE_BLOCK_BYTES, epilogue=epilogue),
    )
    with pytest.raises(BuildAdmissionError, match="trigger axis predicate"):
        derive_build_admission(_context(), source)


_BEGIN_LINE = b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
_END_LINE = b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
_N11_EXTRA_IF = b"#if 1\n  izanagi_gate_pass = false;\n#endif\n"
_N14_NESTED = (
    b"  // EVOLVE-BLOCK-BEGIN other-trigger-axis\n"
    b"#if 1\n#else\n#endif\n"
    b"  // EVOLVE-BLOCK-END other-trigger-axis\n"
)
_LOWERCASE_SECOND_BLOCK = FROZEN_TEMPLATE_BLOCK_BYTES.replace(
    b"EVOLVE-BLOCK-BEGIN", b"evolve-block-begin"
).replace(b"EVOLVE-BLOCK-END", b"evolve-block-end")


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    _BEGIN_LINE, b"\t// EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
                )
            ),
            id="N01-marker-prefix",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    b"EVOLVE-BLOCK-", b"evolve-block-"
                )
            ),
            id="N02-marker-case",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    b"silo-backoff-trigger-gating",
                    b"silo-backoff-trigger-gating-shadow",
                )
            ),
            id="N04-marker-id-variant",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    _BEGIN_LINE, _BEGIN_LINE[:-1] + b"\r\n"
                )
            ),
            id="N05-mixed-newline",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(_BEGIN_LINE, b"").replace(
                    _END_LINE, b""
                )
            ),
            id="N08-markers-deleted",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    b"#if BACKOFF_TRIGGER_GATING\n", b"#if 0\n"
                )
            ),
            id="N09-disabled-if",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    b"#if BACKOFF_TRIGGER_GATING\n", b"#ifdef OTHER_MACRO\n"
                )
            ),
            id="N10-other-ifdef",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    b"#endif\n" + _END_LINE, b"#endif\n" + _N11_EXTRA_IF + _END_LINE
                )
            ),
            id="N11-extra-if-block",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES + _LOWERCASE_SECOND_BLOCK
            ),
            id="N13-second-case-varied-block",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES.replace(
                    b"#if BACKOFF_TRIGGER_GATING\n",
                    _N14_NESTED + b"#if BACKOFF_TRIGGER_GATING\n",
                )
            ),
            id="N14-nested-block",
        ),
        pytest.param(
            _trigger_source_bytes(
                FROZEN_TEMPLATE_BLOCK_BYTES + FROZEN_TEMPLATE_BLOCK_BYTES
            ),
            id="N15-duplicate-block",
        ),
        pytest.param(
            _trigger_source_bytes(_END_LINE + _BEGIN_LINE),
            id="N16-reversed-directives",
        ),
    ],
)
def test_trigger_axis_semantic_admission_rejects_frame_mutations(
    tmp_path: Path, raw: bytes,
):
    source, _ = _write_trigger_source(tmp_path, raw)
    with pytest.raises(BuildAdmissionError, match="trigger axis predicate"):
        derive_build_admission(_context(), source)


@pytest.mark.parametrize(
    "block",
    [
        pytest.param(
            FROZEN_TEMPLATE_BLOCK_BYTES.replace(b"\n", b"\r\n"), id="crlf"
        ),
        pytest.param(
            FROZEN_TEMPLATE_BLOCK_BYTES.replace(b"\n", b"\r"), id="cr-only"
        ),
        pytest.param(
            _trigger_block_with_hole(b"\t" + _canonical_trigger_hole(0)[2:]),
            id="tab-indent",
        ),
        pytest.param(
            _trigger_block_with_hole(b" " + _canonical_trigger_hole(0)),
            id="outer-leading-space",
        ),
        pytest.param(
            _trigger_block_with_hole(_canonical_trigger_hole(0) + b" "),
            id="outer-trailing-space",
        ),
        pytest.param(_trigger_block_with_hole(b""), id="empty-hole"),
        pytest.param(
            _trigger_block_with_hole(
                _canonical_trigger_hole(0) + b"\n" + _canonical_trigger_hole(31)
            ),
            id="multiple-hole-lines",
        ),
        pytest.param(
            _trigger_block_with_hole(b"  izanagi_gate_pass = (true);"),
            id="non-emitter-spelling",
        ),
    ],
)
def test_trigger_axis_semantic_admission_rejects_noncanonical_block(
    tmp_path: Path, block: bytes,
):
    source, _ = _write_trigger_source(tmp_path, _trigger_source_bytes(block))
    with pytest.raises(BuildAdmissionError, match="trigger axis predicate"):
        derive_build_admission(_context(), source)


@pytest.mark.parametrize("case", ["missing-root", "missing-source", "marker-absent"])
def test_trigger_axis_semantic_admission_is_noop_without_axis(tmp_path: Path, case: str):
    if case == "missing-root":
        source = _source(root=str(tmp_path / "absent"))
    else:
        root = tmp_path / "ccbench"
        root.mkdir()
        source = _source(root=str(root))
        if case == "marker-absent":
            target = root / TRIGGER_SOURCE_REL
            target.parent.mkdir(parents=True)
            target.write_bytes(b"int stock_source = 0;\n")
    assert derive_build_admission(_context(), source).provenance is (
        BuildProvenance.STOCK_BASELINE
    )


def test_trigger_axis_semantic_admission_rejects_non_enoent_read_failure(tmp_path: Path):
    root = tmp_path / "ccbench"
    target = root / TRIGGER_SOURCE_REL
    target.mkdir(parents=True)
    with pytest.raises(BuildAdmissionError, match="trigger axis predicate"):
        derive_build_admission(_context(), _source(root=str(root)))


def test_trigger_axis_semantic_admission_reads_source_bytes_once(
    tmp_path: Path, monkeypatch,
):
    source, target = _write_trigger_source(
        tmp_path, _trigger_source_bytes(FROZEN_TEMPLATE_BLOCK_BYTES)
    )
    real_open = builtins.open
    reads = []

    def counting_open(path, *args, **kwargs):
        if os.fspath(path) == os.fspath(target):
            reads.append((args, kwargs))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)
    derive_build_admission(_context(), source)
    assert len(reads) == 1


def test_runtime_admission_rechecks_trigger_axis_while_receipt_replay_does_not(
    tmp_path: Path,
):
    source, target = _write_trigger_source(
        tmp_path,
        _trigger_source_bytes(
            _trigger_block_with_hole(_canonical_trigger_hole(31))
        ),
    )
    context = _context()
    admission = derive_build_admission(context, source)
    body = admission.as_wal_receipt()
    expected_keys = {
        "schema", "class", "policy_sha256", "source", "generator_id", "review_id",
        "input_sha256", "generator_receipt", "review_receipt", "authority_kind",
        "receipt_sha256",
    }
    target.write_bytes(
        _trigger_source_bytes(
            _trigger_block_with_hole(_canonical_trigger_hole(31) + b" ")
        )
    )
    with pytest.raises(BuildAdmissionError, match="trigger axis predicate"):
        require_build_admission(
            admission, expected_policy=context.policy, expected_source=source
        )
    assert validate_build_admission_receipt(
        body, expected_policy=context.policy, expected_source=source
    ) == body
    assert set(body) == expected_keys


def test_trigger_axis_semantic_validator_precedes_class_selection(tmp_path: Path):
    """診断順序だけを pin し、gate 単独変異の kill 証拠には数えない。"""

    source, _ = _write_trigger_source(
        tmp_path,
        _trigger_source_bytes(
            _trigger_block_with_hole(_canonical_trigger_hole(0) + b" ")
        ),
    )
    source = _source(root=source.source_root, token=_SHA_C, clean=False)
    with pytest.raises(BuildAdmissionError, match="trigger axis predicate"):
        derive_build_admission(_context(), source)


def test_frozen_trigger_block_matches_template_patch_bytes():
    patch_path = ORCHESTRATOR.parent / "patches" / "silo-backoff-trigger-gating-variant.patch"
    patch_lines = patch_path.read_bytes().splitlines(keepends=True)
    start = patch_lines.index(b"+" + _BEGIN_LINE)
    stop = patch_lines.index(b"+" + _END_LINE, start)
    reconstructed = b"".join(
        line[1:] for line in patch_lines[start:stop + 1] if line[:1] in (b"+", b" ")
    )
    assert reconstructed == FROZEN_TEMPLATE_BLOCK_BYTES


def test_frozen_trigger_epilogue_matches_template_patch_bytes():
    patch_path = ORCHESTRATOR.parent / "patches" / "silo-backoff-trigger-gating-variant.patch"
    patch_lines = patch_path.read_bytes().splitlines(keepends=True)
    end = patch_lines.index(b"+" + _END_LINE)
    epilogue_lines = patch_lines[end + 1:end + 6]
    assert len(epilogue_lines) == 5
    assert all(line.startswith(b"+") for line in epilogue_lines)
    assert b"".join(line[1:] for line in epilogue_lines) == (
        FROZEN_TEMPLATE_EPILOGUE_BYTES
    )


def test_trigger_axis_import_and_gateway_call_constraints():
    axis_path = ORCHESTRATOR / "campaign" / "axis_trigger_gating.py"
    axis_tree = ast.parse(axis_path.read_text(encoding="utf-8"))
    forbidden_import_reads = {
        "open", "read_bytes", "read_text", "read", "parse_template_file"
    }
    assert not {
        call.func.id if isinstance(call.func, ast.Name) else call.func.attr
        for call in ast.walk(axis_tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, (ast.Name, ast.Attribute))
        and (
            (isinstance(call.func, ast.Name) and call.func.id in forbidden_import_reads)
            or (
                isinstance(call.func, ast.Attribute)
                and call.func.attr in forbidden_import_reads
            )
        )
    }

    admission_path = ORCHESTRATOR / "campaign" / "build_admission.py"
    admission_tree = ast.parse(admission_path.read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in admission_tree.body if isinstance(node, ast.FunctionDef)
    }

    def semantic_calls(function_name: str) -> int:
        return sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_require_materialized_trigger_axis_predicate"
            for node in ast.walk(functions[function_name])
        )

    assert semantic_calls("derive_build_admission") == 1
    assert semantic_calls("require_build_admission") == 1
    assert semantic_calls("validate_build_admission_receipt") == 0


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


def _run() -> int:
    """pytest fixtures を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
