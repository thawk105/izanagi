# -*- coding: utf-8 -*-
"""Tests for the P3 B-4 authoritative floor artifact issuer."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
from fractions import Fraction
from pathlib import Path

import pytest

from orchestrator.campaign import floor_pair_driver
from orchestrator.campaign import p3_b4_analysis_contract
from orchestrator.campaign import p3_b4_floor_artifact_issuer as issuer
from orchestrator.tests import test_floor_pair_driver as driver_tests


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_bytes(root: Path, relpath: str, raw: bytes) -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _synthetic_source(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    candidate_1: float = 130.0,
    reference_1: float = 100.0,
    candidate_2: float = 104.0,
    reference_2: float = 100.0,
    receipt_has_protocol: bool = False,
) -> tuple[Path, dict[str, object]]:
    """Write a closed-schema producer spec and an internally derived summary."""

    hashes = driver_tests._write_inputs(root)
    spec = driver_tests._valid_document(hashes)
    spec["environment"]["env_tag"] = "synthetic-env"
    spec["cells"][0]["perf_config"]["threads"] = 4
    if receipt_has_protocol:
        for artifact in spec["artifacts"]:
            receipt_path = artifact["build_receipt"]["path"]
            receipt = json.loads((root / receipt_path).read_text(encoding="utf-8"))
            receipt["protocol"] = "silo"
            artifact["build_receipt"]["sha256"] = _write_bytes(
                root, receipt_path, _canonical(receipt)
            )
    spec["outputs"]["summary_relpath"] = "out/summary.json"
    spec_sha = _write_bytes(root, "refs/spec.json", _canonical(spec))
    driver_tests._install_git(monkeypatch, root)
    if receipt_has_protocol:
        # The portable receipt contract does not yet carry the protocol field.
        # Preserve every real receipt check while isolating only that known
        # unresolved outer-key delta for identity-positive issuer tests.
        validate_portable_record = (
            floor_pair_driver.s8b_binary_admission.validate_portable_binary_record
        )

        def validate_with_fixture_protocol(record, **kwargs):
            record_without_protocol = dict(record)
            assert record_without_protocol.pop("protocol") == "silo"
            return validate_portable_record(record_without_protocol, **kwargs)

        monkeypatch.setattr(
            floor_pair_driver.s8b_binary_admission,
            "validate_portable_binary_record",
            validate_with_fixture_protocol,
        )
    monkeypatch.setattr(
        floor_pair_driver.calibration_verify,
        "load_verified_calibration",
        lambda **_kwargs: driver_tests._verified_calibration(
            env_tag="synthetic-env",
            threads=4,
        ),
    )

    # The floor is always derived from named synthetic medians.  No measured or
    # plausible production floor is embedded as a fixture default.
    gain = floor_pair_driver.compute_gain_difference(
        candidate_1_tps=candidate_1,
        reference_1_tps=reference_1,
        candidate_2_tps=candidate_2,
        reference_2_tps=reference_2,
    )
    window_raw = b"synthetic window artifact\n"
    window_sha = _write_bytes(root, "out/window.jsonl", window_raw)
    summary = {
        "schema": floor_pair_driver.SUMMARY_SCHEMA,
        "format": floor_pair_driver.SUMMARY_FORMAT_ID,
        "spec_relpath": "refs/spec.json",
        "spec_sha256": spec_sha,
        "loaded_head": "b" * 40,
        "plan_sha256": hashlib.sha256(b"synthetic plan").hexdigest(),
        "generated_at": "2030-01-01T00:30:00Z",
        "status": "generated",
        "upper": gain.difference,
        "candidate_floor": gain.difference,
        "statistics": {
            "reference_measurements_per_pair_sample": (
                floor_pair_driver.REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE
            ),
            "difference_formula": floor_pair_driver.DIFFERENCE_FORMULA,
        },
        "window_artifacts": [
            {
                "window_id": "window-a",
                "campaign_id": "campaign-a",
                "artifact_relpath": "out/window.jsonl",
                "artifact_sha256": window_sha,
            }
        ],
        "campaigns": [
            {
                "window_id": "window-a",
                "campaign_id": "campaign-a",
                "planned_sample_count": 1,
                "dropped_sample_count": 0,
                "dropped_fraction": {"numerator": 0, "denominator": 1},
                "threshold": "1/20",
                "admissible": True,
                "strata": [
                    {
                        "window_id": "window-a",
                        "pair_id": "pair-a",
                        "planned_sample_count": 1,
                        "dropped_sample_count": 0,
                        "retained_sample_count": 1,
                    }
                ],
            }
        ],
        "dropped_sample_count": 0,
        "dropped_record_count": 0,
        "dropped": [],
        "derivation": [
            {
                "samples": [
                    {
                        "window_id": "window-a",
                        "pair_id": "pair-a",
                        "sample_index": 0,
                        "session_medians": {
                            "candidate_1": {
                                "candidate": candidate_1,
                                "reference": reference_1,
                            },
                            "candidate_2": {
                                "candidate": candidate_2,
                                "reference": reference_2,
                            },
                        },
                        "gain_1": gain.gain_1,
                        "gain_2": gain.gain_2,
                        "difference": gain.difference,
                    }
                ],
                "strata": [
                    {
                        "window_id": "window-a",
                        "pair_id": "pair-a",
                        "values": [gain.difference],
                        "upper_function": floor_pair_driver.STRATUM_UPPER_ID,
                        "upper": gain.difference,
                    }
                ],
            }
        ],
        "proof_limitations": {
            "section": "synthetic fixture limitations",
            "items": ["not a measurement", "not producer-issued evidence"],
        },
    }
    summary_path = root / "out/summary.json"
    summary_path.write_bytes(_canonical(summary))
    return Path("out/summary.json"), summary


def _rewrite_summary(root: Path, summary: dict[str, object]) -> None:
    (root / "out/summary.json").write_bytes(_canonical(summary))


def _preregistration(value: str) -> bytes:
    return (
        "# Synthetic preregistration fixture\n\n"
        "## 5. 実走前に数値で埋める欄\n\n"
        "|欄|値|\n"
        "|---|---|\n"
        f"|{issuer.PREREGISTRATION_FLOOR_LABEL}|{value}|\n"
    ).encode("utf-8")


def test_m04_summary_schema_pin_is_one_exact_string() -> None:
    assert type(issuer.ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION) is str
    assert (
        issuer.ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION
        == "floor-pair-summary/v3"
    )


def test_real_finalize_floor_summary_is_accepted_before_missing_protocol_blocks_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use the actual producer finalizer; only measurement execution is synthetic."""

    spec, plan = driver_tests._run_production(
        tmp_path,
        monkeypatch,
        driver_tests._pair_measurement_values(
            candidate_1=(120.0, 120.0),
            reference_1=(100.0, 100.0),
            candidate_2=(110.0, 110.0),
            reference_2=(110.0, 110.0),
        ),
    )
    produced = floor_pair_driver.finalize_floor(
        spec, plan, now_fn=lambda: driver_tests.NOW
    )
    assert produced.status == "generated"

    accepted = issuer.load_floor_pair_summary(
        repo_root=tmp_path,
        summary_path=Path(produced.summary_relpath),
    )
    assert accepted.summary_sha256 == produced.summary_sha256
    assert accepted.candidate_floor == produced.candidate_floor
    assert accepted.missing_identity_elements == ("protocol",)
    with pytest.raises(issuer.B4FloorIdentityError) as caught:
        issuer.issue_authoritative_floor(
            repo_root=tmp_path,
            summary_path=Path(produced.summary_relpath),
        )
    assert caught.value.missing_elements == ("protocol",)


def test_m01_exact_conversion_preserves_candidate_binary64_and_accepts_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(tmp_path, monkeypatch)
    accepted = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=summary_path
    )
    parsed_spec = floor_pair_driver.load_frozen_spec(
        Path(summary["spec_relpath"]),
        summary["spec_sha256"],
        repo_root=tmp_path,
    )
    assert type(parsed_spec) is floor_pair_driver.FloorPairSpec
    assert parsed_spec.environment.env_tag == "synthetic-env"
    original_candidate = summary["candidate_floor"]
    assert type(original_candidate) is float
    expected = Fraction(*original_candidate.as_integer_ratio())
    assert (
        p3_b4_analysis_contract.as_b4_exact_fraction(accepted.floor_exact)
        == expected
    )
    assert (
        p3_b4_analysis_contract.as_b4_exact_fraction(accepted.candidate_floor)
        is None
    )
    assert accepted.source_float_hex == original_candidate.hex()

    zero_root = tmp_path / "zero"
    zero_summary_path, _zero_summary = _synthetic_source(
        zero_root,
        monkeypatch,
        candidate_1=100.0,
        reference_1=100.0,
        candidate_2=100.0,
        reference_2=100.0,
    )
    zero = issuer.load_floor_pair_summary(
        repo_root=zero_root, summary_path=zero_summary_path
    )
    assert zero.floor_exact == Fraction(0, 1)
    assert zero.source_float_hex == 0.0.hex()


def test_m02_difference_self_inconsistency_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(tmp_path, monkeypatch)
    broken = copy.deepcopy(summary)
    broken["derivation"][0]["samples"][0]["difference"] += 0.125
    _rewrite_summary(tmp_path, broken)
    with pytest.raises(issuer.B4FloorArtifactError, match="difference"):
        issuer.load_floor_pair_summary(
            repo_root=tmp_path, summary_path=summary_path
        )


def test_gain_stratum_and_final_uppers_are_each_rederived(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(tmp_path, monkeypatch)
    mutations = (
        ("gain", lambda value: value["derivation"][0]["samples"][0].__setitem__("gain_1", 0.5)),
        ("values", lambda value: value["derivation"][0]["strata"][0].__setitem__("values", [0.125])),
        ("stratum", lambda value: value["derivation"][0]["strata"][0].__setitem__("upper", 0.125)),
        ("final", lambda value: value.__setitem__("upper", 0.125)),
        ("candidate", lambda value: value.__setitem__("candidate_floor", 0.125)),
    )
    for _mutation_id, mutate in mutations:
        broken = copy.deepcopy(summary)
        mutate(broken)
        _rewrite_summary(tmp_path, broken)
        with pytest.raises(issuer.B4FloorArtifactError):
            issuer.load_floor_pair_summary(
                repo_root=tmp_path, summary_path=summary_path
            )
        _rewrite_summary(tmp_path, summary)

    negative_root = tmp_path / "negative-zero"
    negative_summary_path, zero_summary = _synthetic_source(
        negative_root,
        monkeypatch,
        candidate_1=100.0,
        reference_1=100.0,
        candidate_2=100.0,
        reference_2=100.0,
    )
    for field in (
        "candidate_floor",
        "upper",
        "stratum_upper",
        "difference",
        "gain_1",
        "gain_2",
        "values",
    ):
        broken = copy.deepcopy(zero_summary)
        sample = broken["derivation"][0]["samples"][0]
        stratum = broken["derivation"][0]["strata"][0]
        if field in {"candidate_floor", "upper"}:
            broken[field] = -0.0
        elif field == "stratum_upper":
            stratum["upper"] = -0.0
        elif field == "values":
            stratum["values"] = [-0.0]
        else:
            sample[field] = -0.0
        _rewrite_summary(negative_root, broken)
        with pytest.raises(issuer.B4FloorArtifactError, match="negative zero"):
            issuer.load_floor_pair_summary(
                repo_root=negative_root,
                summary_path=negative_summary_path,
            )
        _rewrite_summary(negative_root, zero_summary)


def test_m03_bool_upper_is_rejected_even_when_it_equals_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(
        tmp_path,
        monkeypatch,
        candidate_1=100.0,
        reference_1=100.0,
        candidate_2=100.0,
        reference_2=100.0,
    )
    summary["upper"] = False
    _rewrite_summary(tmp_path, summary)
    with pytest.raises(issuer.B4FloorArtifactError, match="exact finite float"):
        issuer.load_floor_pair_summary(
            repo_root=tmp_path, summary_path=summary_path
        )


def test_m11_exact_floor_domain_rejects_one_without_clamp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path,
        monkeypatch,
        candidate_1=200.0,
        reference_1=100.0,
        candidate_2=100.0,
        reference_2=100.0,
    )
    with pytest.raises(issuer.B4FloorArtifactError, match="0 <= floor < 1"):
        issuer.load_floor_pair_summary(
            repo_root=tmp_path, summary_path=summary_path
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("schema", "floor-pair-summary/v2", "pinned"),
        ("status", "not_generated_missing_samples", "generated"),
    ),
)
def test_summary_schema_and_generated_status_are_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    summary_path, summary = _synthetic_source(tmp_path, monkeypatch)
    summary[field] = value
    _rewrite_summary(tmp_path, summary)
    with pytest.raises(issuer.B4FloorArtifactError, match=message):
        issuer.load_floor_pair_summary(
            repo_root=tmp_path, summary_path=summary_path
        )


def test_summary_spec_hash_and_closed_top_level_are_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(tmp_path, monkeypatch)
    spec_path = tmp_path / "refs/spec.json"
    original_spec_raw = spec_path.read_bytes()
    spec_path.write_bytes(b"{}\n")
    with pytest.raises(issuer.B4FloorArtifactError, match="spec_hash_mismatch"):
        issuer.load_floor_pair_summary(
            repo_root=tmp_path, summary_path=summary_path
        )

    spec_path.write_bytes(original_spec_raw)
    summary["unexpected"] = "closed schema"
    _rewrite_summary(tmp_path, summary)
    with pytest.raises(issuer.B4FloorArtifactError, match="unknown"):
        issuer.load_floor_pair_summary(
            repo_root=tmp_path, summary_path=summary_path
        )
    summary.pop("unexpected")
    spec_path = tmp_path / summary["spec_relpath"]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["fixture_kind"] = "producer-must-reject-this-unknown-key"
    spec_raw = _canonical(spec)
    spec_path.write_bytes(spec_raw)
    summary["spec_sha256"] = hashlib.sha256(spec_raw).hexdigest()
    _rewrite_summary(tmp_path, summary)

    with pytest.raises(
        issuer.B4FloorArtifactError,
        match="floor_pair_driver.load_frozen_spec",
    ) as caught:
        issuer.load_floor_pair_summary(
            repo_root=tmp_path,
            summary_path=summary_path,
        )
    assert caught.value.code == "spec_rejected_by_producer"
    assert isinstance(caught.value.__cause__, floor_pair_driver.FloorPairSpecError)


def test_identity_is_not_a_caller_surface_and_missing_protocol_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert set(inspect.signature(issuer.issue_authoritative_floor).parameters) == {
        "repo_root",
        "summary_path",
    }
    loader_signature = inspect.signature(issuer.load_authoritative_floor)
    assert loader_signature.parameters["expected_sha256"].default is (
        inspect.Parameter.empty
    )
    summary_path, _summary = _synthetic_source(
        tmp_path, monkeypatch, receipt_has_protocol=False
    )
    accepted = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=summary_path
    )
    assert accepted.identity is None
    assert accepted.missing_identity_elements == ("protocol",)
    with pytest.raises(issuer.B4FloorIdentityError) as caught:
        issuer.issue_authoritative_floor(
            repo_root=tmp_path, summary_path=summary_path
        )
    assert caught.value.missing_elements == ("protocol",)


def test_authority_issue_is_create_only_exact_and_loadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(
        tmp_path, monkeypatch, receipt_has_protocol=True
    )
    accepted_summary = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=summary_path
    )
    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path, summary_path=summary_path
    )
    raw = (tmp_path / result.artifact_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == result.artifact_sha256
    assert not list((tmp_path / "out").glob(".b4-floor-stage-*"))
    with pytest.raises(TypeError, match="expected_sha256"):
        issuer.load_authoritative_floor(
            repo_root=tmp_path,
            artifact_path=result.artifact_path,
        )

    loaded = issuer.load_authoritative_floor(
        repo_root=tmp_path,
        artifact_path=result.artifact_path,
        expected_sha256=result.artifact_sha256,
    )
    assert loaded.floor == Fraction(
        *accepted_summary.candidate_floor.as_integer_ratio()
    )
    assert loaded.source_float_hex == accepted_summary.candidate_floor.hex()
    assert loaded.identity == accepted_summary.identity
    assert loaded.non_guarantees == (
        *issuer.NON_GUARANTEES,
        *summary["proof_limitations"]["items"],
    )
    assert issuer.SOURCE_SUMMARY_REFERENCES_NOT_VERIFIED in raw.decode()
    authority = json.loads(raw)
    assert authority["non_guarantees"][len(issuer.NON_GUARANTEES) :] == (
        summary["proof_limitations"]["items"]
    )
    assert issuer.BINARY64_INTERMEDIATE_ROUNDING_LIMITATION in raw.decode()
    assert issuer.D1699_VERSION_LIMITATION in raw.decode()

    before = raw
    with pytest.raises(issuer.B4FloorArtifactError, match="artifact_exists"):
        issuer.issue_authoritative_floor(
            repo_root=tmp_path, summary_path=summary_path
        )
    assert (tmp_path / result.artifact_path).read_bytes() == before


def test_authority_non_guarantees_pin_required_verbatim_limitations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path, monkeypatch, receipt_has_protocol=True
    )
    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path, summary_path=summary_path
    )
    authority = json.loads(
        (tmp_path / result.artifact_path).read_text(encoding="utf-8")
    )

    assert authority["non_guarantees"][:3] == [
        "binary64 の中間丸めにより、記録された float D が同じ入力の exact D より小さいことがある。",
        "その版が D1699 適合をまだ満たしていない。",
        "source summary の参照先を実在照合していない",
    ]


def test_authority_filename_contains_all_five_derived_components(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path, monkeypatch, receipt_has_protocol=True
    )
    accepted = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=summary_path
    )
    assert accepted.identity is not None
    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path, summary_path=summary_path
    )
    name = Path(result.artifact_path).name
    identity = accepted.identity
    assert f"__env-{identity.env_tag}" in name
    assert f"__protocol-{identity.protocol}" in name
    assert f"__threads-{identity.threads}" in name
    assert f"__workload-{identity.workload_identifier}" in name
    assert f"__campaign-{identity.campaign_identifier}" in name


def test_resolver_exact_sentinel_is_the_only_absence(tmp_path: Path) -> None:
    prereg_path = Path("docs/prereg.md")
    _write_bytes(
        tmp_path,
        prereg_path.as_posix(),
        _preregistration(issuer.PREREGISTRATION_ABSENT_SENTINEL),
    )
    assert (
        issuer.resolve_preregistered_authoritative_floor(
            repo_root=tmp_path, preregistration_path=prereg_path
        )
        is None
    )
    for malformed in (" 未記入", "未記入 ", "TBD", "artifact_path=x"):
        _write_bytes(tmp_path, prereg_path.as_posix(), _preregistration(malformed))
        with pytest.raises(issuer.B4FloorArtifactError) as caught:
            issuer.resolve_preregistered_authoritative_floor(
                repo_root=tmp_path, preregistration_path=prereg_path
            )
        assert caught.value.code == "preregistration_floor_grammar_error"


def test_resolver_returns_exact_fraction_from_valid_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path, monkeypatch, receipt_has_protocol=True
    )
    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path, summary_path=summary_path
    )
    prereg_path = Path("docs/prereg.md")
    _write_bytes(
        tmp_path,
        prereg_path.as_posix(),
        _preregistration(
            f"artifact_path={result.artifact_path}; sha256={result.artifact_sha256}"
        ),
    )
    resolved = issuer.resolve_preregistered_authoritative_floor(
        repo_root=tmp_path, preregistration_path=prereg_path
    )
    assert resolved is not None
    assert type(resolved.floor) is Fraction
    assert resolved.artifact_path == result.artifact_path
    assert resolved.artifact_sha256 == result.artifact_sha256


@pytest.mark.parametrize("mode", ("missing", "hash", "schema"))
def test_m05_m06_resolver_fails_closed_without_absence_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path, monkeypatch, receipt_has_protocol=True
    )
    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path, summary_path=summary_path
    )
    artifact_path = result.artifact_path
    artifact_sha = result.artifact_sha256
    if mode == "missing":
        artifact_path = "out/missing-authority.json"
    elif mode == "hash":
        artifact_sha = "0" * 64
    else:
        value = json.loads((tmp_path / artifact_path).read_text(encoding="utf-8"))
        value["schema"] = "p3-b4-authoritative-floor/v2"
        raw = _canonical(value)
        (tmp_path / artifact_path).write_bytes(raw)
        artifact_sha = hashlib.sha256(raw).hexdigest()
    prereg_path = Path("docs/prereg.md")
    _write_bytes(
        tmp_path,
        prereg_path.as_posix(),
        _preregistration(
            f"artifact_path={artifact_path}; sha256={artifact_sha}"
        ),
    )
    with pytest.raises(issuer.B4FloorArtifactError):
        issuer.resolve_preregistered_authoritative_floor(
            repo_root=tmp_path, preregistration_path=prereg_path
        )


def test_resolver_rejects_duplicate_floor_rows(tmp_path: Path) -> None:
    row = (
        f"|{issuer.PREREGISTRATION_FLOOR_LABEL}|"
        f"{issuer.PREREGISTRATION_ABSENT_SENTINEL}|\n"
    )
    raw = ("# Fixture\n\n" + row + row).encode("utf-8")
    prereg_path = Path("docs/prereg.md")
    _write_bytes(tmp_path, prereg_path.as_posix(), raw)
    with pytest.raises(issuer.B4FloorArtifactError, match="exact 1"):
        issuer.resolve_preregistered_authoritative_floor(
            repo_root=tmp_path, preregistration_path=prereg_path
        )
