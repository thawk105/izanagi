# -*- coding: utf-8 -*-
"""Tests for the P3 B-4 authoritative floor artifact issuer."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from orchestrator.campaign import floor_pair_driver
from orchestrator.campaign import p3_b4_analysis_contract
from orchestrator.campaign import p3_b4_floor_artifact_issuer as issuer
from orchestrator.campaign.model import Genome
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


def _mocc_genome_canonicals() -> dict[str, str]:
    return {
        "candidate": Genome(
            protocol="mocc", flags={"FIXTURE": 1}
        ).canonical(),
        "reference": Genome(
            protocol="mocc", flags={"FIXTURE": 2}
        ).canonical(),
    }


def _synthetic_source(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    candidate_1: float = 130.0,
    reference_1: float = 100.0,
    candidate_2: float = 104.0,
    reference_2: float = 100.0,
    genome_canonicals: dict[str, str] | None = None,
) -> tuple[Path, dict[str, object]]:
    """Write a closed-schema producer spec and an internally derived summary."""

    hashes = driver_tests._write_inputs(
        root, genome_canonicals=genome_canonicals
    )
    spec = driver_tests._valid_document(hashes)
    spec["environment"]["env_tag"] = "synthetic-env"
    spec["cells"][0]["perf_config"]["threads"] = 4
    spec["outputs"]["summary_relpath"] = "out/summary.json"
    spec_sha = _write_bytes(root, "refs/spec.json", _canonical(spec))
    driver_tests._install_git(monkeypatch, root)
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
        "loaded_head": driver_tests.HEAD,
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


def test_real_finalize_floor_summary_is_issued_with_receipt_protocol(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use the actual producer finalizer; only measurement execution is synthetic."""

    write_inputs = driver_tests._write_inputs
    genome_canonicals = _mocc_genome_canonicals()
    monkeypatch.setattr(
        driver_tests,
        "_write_inputs",
        lambda root: write_inputs(
            root, genome_canonicals=genome_canonicals
        ),
    )
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
    assert accepted.missing_identity_elements == ()
    assert accepted.identity is not None
    assert accepted.identity.protocol == "mocc"

    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path,
        summary_path=Path(produced.summary_relpath),
    )
    assert "__protocol-mocc" in Path(result.artifact_path).name
    authority = json.loads(
        (tmp_path / result.artifact_path).read_text(encoding="utf-8")
    )
    assert authority["artifact_identity"]["protocol"] == "mocc"


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


@pytest.mark.parametrize(
    "genome_canonicals",
    (
        None,
        {
            "candidate": "mocc|B=1,A=2",
            "reference": "mocc|B=1,A=2",
        },
        {
            "candidate": Genome(
                protocol="mocc", flags={"FIXTURE": 1}
            ).canonical(),
            "reference": "mocc|B=1,A=2",
        },
    ),
    ids=("json-fixture", "unsorted-flags", "partial-noncanonical"),
)
def test_identity_is_not_a_caller_surface_and_noncanonical_genomes_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    genome_canonicals: dict[str, str] | None,
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
        tmp_path,
        monkeypatch,
        genome_canonicals=genome_canonicals,
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


def test_mixed_receipt_protocols_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path,
        monkeypatch,
        genome_canonicals={
            "candidate": Genome(
                protocol="mocc", flags={"FIXTURE": 1}
            ).canonical(),
            "reference": Genome(
                protocol="silo", flags={"FIXTURE": 1}
            ).canonical(),
        },
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


def test_authority_value_rejects_nonempty_missing_protocol_with_valid_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path,
        monkeypatch,
        genome_canonicals=_mocc_genome_canonicals(),
    )
    accepted = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=summary_path
    )
    assert accepted.identity is not None
    broken = replace(
        accepted, missing_identity_elements=("protocol",)
    )
    with pytest.raises(issuer.B4FloorIdentityError) as caught:
        issuer._authority_value(broken)
    assert caught.value.missing_elements == ("protocol",)


def test_authority_issue_is_create_only_exact_and_loadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, summary = _synthetic_source(
        tmp_path,
        monkeypatch,
        genome_canonicals=_mocc_genome_canonicals(),
    )
    accepted_summary = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=summary_path
    )
    parsed_spec = floor_pair_driver.load_frozen_spec(
        Path(summary["spec_relpath"]),
        summary["spec_sha256"],
        repo_root=tmp_path,
    )
    assert summary["loaded_head"] == parsed_spec.loaded_head
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
    assert issuer.FREEZE_TIMING_NOT_PROVEN in raw.decode()

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
        tmp_path,
        monkeypatch,
        genome_canonicals=_mocc_genome_canonicals(),
    )
    result = issuer.issue_authoritative_floor(
        repo_root=tmp_path, summary_path=summary_path
    )
    authority = json.loads(
        (tmp_path / result.artifact_path).read_text(encoding="utf-8")
    )

    assert authority["non_guarantees"][:3] == [
        "binary64 の中間丸めにより、記録された float D が同じ入力の exact D より小さいことがある。",
        "凍結が測定の結果を見る前に行われたことを証明しない。",
        "source summary の参照先を実在照合していない",
    ]


def test_authority_filename_contains_all_five_derived_components(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path, _summary = _synthetic_source(
        tmp_path,
        monkeypatch,
        genome_canonicals=_mocc_genome_canonicals(),
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
        tmp_path,
        monkeypatch,
        genome_canonicals=_mocc_genome_canonicals(),
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
        tmp_path,
        monkeypatch,
        genome_canonicals=_mocc_genome_canonicals(),
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



def _aggregate_coverage_case(root: Path, *, ordinal: int = 0):
    """Parse a two-window spec and derive synthetic summary arithmetic.

    This fixture exercises coverage and composition only: it does not pretend
    that constructing a FloorPairSpec constitutes frozen-spec admission.
    No validator or dependency is replaced.
    """
    hashes = driver_tests._write_inputs(root, genome_canonicals=_mocc_genome_canonicals())
    document = driver_tests._valid_document(hashes)
    document["environment"]["env_tag"] = "synthetic-env"
    document["cells"][0]["perf_config"]["threads"] = 4
    cell = document["cells"][0]
    workload = cell["perf_config"]["workload"]
    workload[sorted(workload)[0]] = f"synthetic-workload-{ordinal}"
    cell["cell_id"] = "cell-a"
    second_cell = copy.deepcopy(cell)
    second_cell["cell_id"] = "cell-b"
    document["cells"] = [cell, second_cell]
    pair = document["pairs"][0]
    pair["pair_id"], pair["cell_id"] = "pair-a", "cell-a"
    second_pair = copy.deepcopy(pair)
    second_pair["pair_id"], second_pair["cell_id"] = "pair-b", "cell-b"
    document["pairs"] = [pair, second_pair]
    from datetime import datetime, timezone
    windows = tuple(floor_pair_driver.WindowConfig(
        window_id=f"window-{wid}", campaign_id=f"campaign-{ordinal}-{wid}",
        not_before=datetime(2030, 1, day, tzinfo=timezone.utc),
        not_after=datetime(2030, 1, day, 1, tzinfo=timezone.utc),
        sample_count=20, pair_ids=("pair-a", "pair-b"),
        artifact_relpath=f"out/{ordinal}/window-{wid}.jsonl",
    ) for day, wid in ((1, "a"), (2, "b")))
    document["statistics"]["closed_strata"] = [
        {"window_id": w.window_id, "pair_id": pair_id}
        for w in windows for pair_id in w.pair_ids
    ]
    document["outputs"]["summary_relpath"] = f"out/{ordinal}/summary.json"
    spec = floor_pair_driver.FloorPairSpec(
        schema=document["schema"],
        provenance=floor_pair_driver._parse_provenance(document["provenance"]),
        environment=floor_pair_driver._parse_environment(document["environment"]),
        artifacts=floor_pair_driver._parse_artifacts(document["artifacts"]),
        cells=floor_pair_driver._parse_cells(document["cells"]),
        pairs=floor_pair_driver._parse_pairs(document["pairs"]), windows=windows,
        randomization=floor_pair_driver._parse_randomization(document["randomization"]),
        statistics=floor_pair_driver._parse_statistics(document["statistics"]),
        failure_policy=floor_pair_driver._parse_failure_policy(document["failure_policy"]),
        outputs=floor_pair_driver._parse_outputs(document["outputs"]),
        repo_root=root, spec_relpath=f"refs/spec-{ordinal}.json",
        spec_sha256=hashlib.sha256(_canonical(document)).hexdigest(),
        loaded_head=driver_tests.HEAD,
    )
    floor_pair_driver._validate_cross_references(
        artifacts=spec.artifacts, cells=spec.cells, pairs=spec.pairs,
        windows=spec.windows, statistics=spec.statistics,
    )
    candidate = (100.0, 120.0, 130.0)[ordinal % 3]
    gain = floor_pair_driver.compute_gain_difference(
        candidate_1_tps=candidate, reference_1_tps=100.0,
        candidate_2_tps=100.0, reference_2_tps=100.0,
    )
    samples, strata, campaigns, dropped = [], [], [], []
    for window in windows:
        campaign_strata = []
        for pair_id in window.pair_ids:
            missing = pair_id == "pair-a"
            for index in range(20):
                if missing and index == 0:
                    for side in ("candidate_1", "candidate_2"):
                        dropped.append({
                            "window_id": window.window_id, "pair_id": pair_id,
                            "sample_index": index, "side_id": side,
                            "status": "dropped", "error": "synthetic missing sample",
                            "dropped_by_session_id": None,
                        })
                    continue
                samples.append({
                    "window_id": window.window_id, "pair_id": pair_id,
                    "sample_index": index,
                    "session_medians": {
                        "candidate_1": {"candidate": candidate, "reference": 100.0},
                        "candidate_2": {"candidate": 100.0, "reference": 100.0},
                    },
                    "gain_1": gain.gain_1, "gain_2": gain.gain_2,
                    "difference": gain.difference,
                })
            strata.append({
                "window_id": window.window_id, "pair_id": pair_id,
                "values": [gain.difference] * (19 if missing else 20),
                "upper_function": "sample_max/v1", "upper": gain.difference,
            })
            campaign_strata.append({
                "window_id": window.window_id, "pair_id": pair_id,
                "planned_sample_count": 20, "dropped_sample_count": int(missing),
                "retained_sample_count": 19 if missing else 20,
            })
        campaigns.append({
            "window_id": window.window_id, "campaign_id": window.campaign_id,
            "planned_sample_count": 40, "dropped_sample_count": 1,
            "dropped_fraction": {"numerator": 1, "denominator": 40},
            "threshold": "1/20", "admissible": True, "strata": campaign_strata,
        })
    summary = {
        "schema": "floor-pair-summary/v3", "format": floor_pair_driver.SUMMARY_FORMAT_ID,
        "spec_relpath": spec.spec_relpath, "spec_sha256": spec.spec_sha256,
        "loaded_head": spec.loaded_head,
        "plan_sha256": hashlib.sha256(f"synthetic plan {ordinal}".encode()).hexdigest(),
        "generated_at": "2030-01-02T01:00:00Z", "status": "generated",
        "upper": gain.difference, "candidate_floor": gain.difference,
        "statistics": {
            "reference_measurements_per_pair_sample": spec.statistics.reference_measurements_per_pair_sample,
            "difference_formula": spec.statistics.difference_formula,
        },
        "window_artifacts": [{
            "window_id": w.window_id, "campaign_id": w.campaign_id,
            "artifact_relpath": w.artifact_relpath,
            "artifact_sha256": hashlib.sha256(f"synthetic {ordinal} {w.window_id}".encode()).hexdigest(),
        } for w in windows],
        "campaigns": campaigns, "dropped_sample_count": 2, "dropped_record_count": 4,
        "dropped": dropped, "derivation": [{"samples": samples, "strata": strata}],
        "proof_limitations": {
            "section": f"synthetic source {ordinal} limitations",
            "items": ["not a measurement", "not a measurement", f"source {ordinal}"],
        },
    }
    _value, candidate_floor, campaign_ids, limitations = issuer._validate_summary_document(summary)
    identity, missing, workloads = issuer._derive_identity(root, spec, campaign_ids)
    assert identity is not None and not missing
    accepted = issuer.B4ValidatedFloorPairSummary(
        summary_path=spec.outputs.summary_relpath,
        summary_sha256=hashlib.sha256(_canonical(summary)).hexdigest(),
        candidate_floor=candidate_floor, floor_exact=issuer._exact_floor(candidate_floor),
        source_float_hex=candidate_floor.hex(), spec_relpath=spec.spec_relpath,
        spec_sha256=spec.spec_sha256, loaded_head=spec.loaded_head,
        plan_sha256=summary["plan_sha256"], campaign_ids=campaign_ids,
        workload_values=workloads, proof_limitations=limitations, identity=identity,
        missing_identity_elements=missing,
    )
    return spec, accepted, summary


def test_aggregate_coverage_projects_windows_and_counts_drop_records(tmp_path: Path) -> None:
    spec, accepted, summary = _aggregate_coverage_case(tmp_path)
    assert len(spec.windows) == 2
    assert len(spec.cells) == 2
    assert summary["dropped_sample_count"] == 2
    assert summary["dropped_record_count"] == 4
    assert len(summary["derivation"][0]["samples"]) == 78
    issuer._validate_aggregate_summary_coverage(spec, accepted, summary)


@pytest.mark.parametrize("mode", ("missing", "extra", "duplicate", "campaign", "path"))
def test_aggregate_window_binding_reaches_spec_comparison(tmp_path: Path, mode: str) -> None:
    spec, accepted, summary = _aggregate_coverage_case(tmp_path)
    rows = summary["window_artifacts"]
    if mode == "missing":
        rows.pop()
    elif mode in ("extra", "duplicate"):
        row = copy.deepcopy(rows[0])
        if mode == "extra":
            row["window_id"] = "window-extra"
        rows.append(row)
    else:
        rows[0]["campaign_id" if mode == "campaign" else "artifact_relpath"] = (
            "campaign-other" if mode == "campaign" else "out/other.jsonl"
        )
    issuer._validate_summary_document(summary)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._validate_aggregate_summary_coverage(spec, accepted, summary)
    assert caught.value.code == "aggregate_window_binding_error"


@pytest.mark.parametrize("mode", ("derivation", "campaign", "cell"))
def test_aggregate_partial_closure_reaches_strata_or_cells(tmp_path: Path, mode: str) -> None:
    spec, accepted, summary = _aggregate_coverage_case(tmp_path)
    if mode == "derivation":
        for field in ("samples", "strata"):
            summary["derivation"][0][field] = [
                row for row in summary["derivation"][0][field] if row["pair_id"] != "pair-b"
            ]
    elif mode == "campaign":
        summary["campaigns"][0]["strata"][0]["window_id"] = "window-b"
    else:
        spec = replace(spec, cells=(*spec.cells, replace(spec.cells[0], cell_id="cell-unused")))
    issuer._validate_summary_document(summary)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._validate_aggregate_summary_coverage(spec, accepted, summary)
    assert caught.value.code == ("aggregate_cell_coverage_error" if mode == "cell" else "aggregate_strata_error")


@pytest.mark.parametrize("mode", ("missing", "extra", "overlap", "sample-count", "record-count", "campaign-count", "stratum-count", "threshold", "fraction", "admissible"))
def test_aggregate_sample_accounting_reaches_named_gate(tmp_path: Path, mode: str) -> None:
    spec, accepted, summary = _aggregate_coverage_case(tmp_path)
    derivation = summary["derivation"][0]
    if mode == "missing":
        derivation["samples"].pop(0)
        derivation["strata"][0]["values"].pop(0)
    elif mode == "extra":
        derivation["samples"][0]["sample_index"] = 20
    elif mode == "overlap":
        summary["dropped"][0]["sample_index"] = 1
    elif mode == "sample-count":
        summary["dropped_sample_count"] += 1
    elif mode == "record-count":
        summary["dropped_record_count"] += 1
    elif mode == "campaign-count":
        summary["campaigns"][0]["planned_sample_count"] += 1
    elif mode == "stratum-count":
        summary["campaigns"][0]["strata"][0]["retained_sample_count"] += 1
    elif mode == "threshold":
        summary["campaigns"][0]["threshold"] = "1/10"
    elif mode == "fraction":
        summary["campaigns"][0]["dropped_fraction"]["numerator"] = 0
    else:
        summary["campaigns"][0]["admissible"] = False
    issuer._validate_summary_document(summary)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._validate_aggregate_summary_coverage(spec, accepted, summary)
    assert caught.value.code == (
        "aggregate_sample_partition_error" if mode in ("missing", "extra", "overlap") else
        "aggregate_drop_policy_error" if mode in ("threshold", "fraction", "admissible") else
        "aggregate_sample_count_error"
    )


def test_aggregate_statistics_reaches_spec_comparison(tmp_path: Path) -> None:
    spec, accepted, summary = _aggregate_coverage_case(tmp_path)
    summary["statistics"]["difference_formula"] = "synthetic-other-formula/v1"
    issuer._validate_summary_document(summary)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._validate_aggregate_summary_coverage(spec, accepted, summary)
    assert caught.value.code == "aggregate_statistics_error"


def test_aggregate_composition_exact_max_sources_and_order(tmp_path: Path) -> None:
    from itertools import permutations
    cases = [_aggregate_coverage_case(tmp_path / str(i), ordinal=i) for i in range(3)]
    for spec, accepted, document in cases:
        issuer._validate_aggregate_summary_coverage(spec, accepted, document)
    sources = [(accepted, document, issuer._authority_value(accepted)) for _, accepted, document in cases]
    pins = [(spec.spec_relpath, spec.spec_sha256) for spec, _, _ in cases]
    values = [issuer._compose_aggregate_authority(order, list(reversed(pins))) for order in permutations(sources)]
    assert all(_canonical(value) == _canonical(values[0]) for value in values)
    value = values[0]
    # Independently calculated binary64 result of 130 / 100 - 1.
    assert value["floor_exact"] == [1351079888211149, 4503599627370496]
    assert value["source_float_hex"] == "0x1.3333333333334p-2"
    assert value["schema"] == "p3-b4-authoritative-floor/v2"
    assert value["source_summary"]["spec_relpath"] == "refs/spec-2.json"
    assert len(value["aggregation"]["sources"]) == 3
    assert len(value["identity_derivation"]["workloads"]) == 3
    assert len(value["identity_derivation"]["campaign_ids"]) == 6
    for index, source in enumerate(value["aggregation"]["sources"]):
        accepted, document, _ = sources[index]
        assert source["artifact_path"] == accepted.summary_path
        assert source["artifact_sha256"] == hashlib.sha256(_canonical(document)).hexdigest()
        assert source["spec_relpath"] == accepted.spec_relpath
        assert source["spec_sha256"] == accepted.spec_sha256
        assert source["floor_exact"] == [accepted.floor_exact.numerator, accepted.floor_exact.denominator]
        assert source["source_float_hex"] == accepted.source_float_hex
        assert source["proof_limitations"] == document["proof_limitations"]
    assert value["non_guarantees"][3:12] == [item for _, _, doc in cases for item in doc["proof_limitations"]["items"]]
    identity = issuer._parse_identity(value["artifact_identity"])
    expected_name = (
        f"b4-floor-aggregate__env-{identity.env_tag}__protocol-{identity.protocol}"
        f"__threads-{identity.threads}__workload-{identity.workload_identifier}"
        f"__campaign-{identity.campaign_identifier}.json"
    )
    assert issuer._aggregate_artifact_filename(identity) == expected_name


@pytest.mark.parametrize("field", ("env_tag", "protocol", "threads"))
def test_aggregate_composition_identity_mismatch_gate(tmp_path: Path, field: str) -> None:
    _, accepted, document = _aggregate_coverage_case(tmp_path)
    altered = replace(accepted, identity=replace(accepted.identity, **{field: 8 if field == "threads" else "other"}))
    sources = [(s, document, issuer._authority_value(s)) for s in (accepted, altered)]
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._compose_aggregate_authority(sources, [(accepted.spec_relpath, accepted.spec_sha256)])
    assert caught.value.code == "aggregate_identity_error"


@pytest.mark.parametrize("mode", ("unknown", "v1-as-v2"))
def test_aggregate_schema_rejects_unknown_and_missing_aggregation(tmp_path: Path, mode: str) -> None:
    _, accepted, _ = _aggregate_coverage_case(tmp_path)
    value = issuer._authority_value(accepted)
    value["schema"] = "p3-b4-authoritative-floor/v999" if mode == "unknown" else "p3-b4-authoritative-floor/v2"
    digest = _write_bytes(tmp_path, "out/authority.json", _canonical(value))
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.load_authoritative_floor(repo_root=tmp_path, artifact_path="out/authority.json", expected_sha256=digest)
    assert caught.value.code == ("artifact_schema_error" if mode == "unknown" else "schema_error")
    if mode == "v1-as-v2":
        assert "authority.aggregation" in caught.value.detail


@pytest.mark.parametrize("pins,code", (
    ([], "aggregate_expected_specs_error"),
    ([("refs/spec.json", "0" * 64)] * 2, "aggregate_expected_specs_error"),
    ([("../spec.json", "0" * 64)], "path_error"),
    ([("refs/spec.json", "A" * 64)], "schema_error"),
    ([("refs/spec.json",)], "aggregate_expected_specs_error"),
))
def test_aggregate_expected_pin_shape_gate(tmp_path: Path, pins, code: str) -> None:
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.issue_aggregate_authoritative_floor(
            repo_root=tmp_path, summary_paths=[], expected_specs=pins, output_dir=Path("."),
        )
    assert caught.value.code == code


@pytest.mark.parametrize("options", (
    ["--aggregate-summary", "out/s.json"],
    ["--aggregate-summary", "out/s.json", "--expected-spec", "refs/spec.json", "0" * 64],
    ["--aggregate-summary", "out/s.json", "--aggregate-output-dir", "out"],
    ["--summary", "out/s.json", "--aggregate-summary", "out/t.json"],
    ["--summary", "out/s.json", "--expected-spec", "refs/spec.json", "0" * 64],
    ["--summary", "out/s.json", "--aggregate-output-dir", "out"],
))
def test_aggregate_cli_rejects_incomplete_or_mixed_modes(tmp_path: Path, capsys, options) -> None:
    with pytest.raises(SystemExit) as caught:
        issuer.main(["--repo-root", str(tmp_path), *options])
    assert caught.value.code == 2
    error = capsys.readouterr().err
    if "--summary" in options and "--aggregate-summary" in options:
        assert "not allowed with argument --summary" in error
    elif "--summary" in options:
        assert "aggregate-only arguments cannot accompany --summary" in error
    else:
        assert "aggregate mode requires --expected-spec and --aggregate-output-dir" in error


@pytest.mark.parametrize("option", ("--s", "--su", "--sum", "--summ", "--summa", "--summar", "--summary"))
def test_aggregate_cli_preserves_legacy_summary_abbreviations(tmp_path: Path, capsys, option: str) -> None:
    # Missing file is a semantic path rejection, proving parsing selected v1.
    assert issuer.main(["--repo-root", str(tmp_path), option, "missing.json"]) == 2
    error = json.loads(capsys.readouterr().err)
    assert error["error"] == "path_error"
    assert "floor-pair summary" in error["detail"]



def test_aggregate_excess_drops_reaches_policy_after_consistent_counts(tmp_path: Path) -> None:
    spec, accepted, summary = _aggregate_coverage_case(tmp_path)
    derived = summary["derivation"][0]
    # Three missing samples out of forty, with all accounting updated.
    derived["samples"] = [r for r in derived["samples"] if not (
        r["window_id"] == "window-a" and r["pair_id"] == "pair-a"
        and r["sample_index"] in (1, 2)
    )]
    derived["strata"][0]["values"] = derived["strata"][0]["values"][2:]
    for index in (1, 2):
        row = copy.deepcopy(summary["dropped"][0])
        row["sample_index"] = index
        summary["dropped"].append(row)
    summary["dropped_sample_count"] = 4
    summary["dropped_record_count"] = 6
    campaign = summary["campaigns"][0]
    campaign["dropped_sample_count"] = 3
    campaign["dropped_fraction"] = {"numerator": 3, "denominator": 40}
    campaign["strata"][0]["dropped_sample_count"] = 3
    campaign["strata"][0]["retained_sample_count"] = 17
    # Keep generated/admissible so threshold arithmetic itself must reject.
    issuer._validate_summary_document(summary)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._validate_aggregate_summary_coverage(spec, accepted, summary)
    assert caught.value.code == "aggregate_drop_policy_error"


def test_aggregate_filename_publication_uses_create_only_primitive(tmp_path: Path) -> None:
    _, accepted, document = _aggregate_coverage_case(tmp_path)
    value = issuer._compose_aggregate_authority(
        [(accepted, document, issuer._authority_value(accepted))],
        [(accepted.spec_relpath, accepted.spec_sha256)],
    )
    path = tmp_path / issuer._aggregate_artifact_filename(issuer._parse_identity(value["artifact_identity"]))
    raw = _canonical(value)
    issuer._publish_create_only(path, raw)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer._publish_create_only(path, b"replacement forbidden\n")
    assert caught.value.code == "artifact_exists"
    assert path.read_bytes() == raw
    assert not list(tmp_path.glob(".b4-floor-stage-*"))



def test_aggregate_api_requires_independent_expectation_and_output() -> None:
    parameters = inspect.signature(issuer.issue_aggregate_authoritative_floor).parameters
    assert set(parameters) == {"repo_root", "summary_paths", "expected_specs", "output_dir"}
    assert all(p.default is inspect.Parameter.empty for p in parameters.values())
    assert issuer.B4_FLOOR_ARTIFACT_SCHEMA_VERSION == "p3-b4-authoritative-floor/v1"


def test_aggregate_cli_preserves_last_legacy_summary_value(tmp_path: Path, capsys) -> None:
    assert issuer.main([
        "--repo-root", str(tmp_path), "--summary", "first-missing.json",
        "--summary", "last-missing.json",
    ]) == 2
    error = json.loads(capsys.readouterr().err)
    assert error["error"] == "path_error"
    assert "last-missing.json" in error["detail"]


def _aggregate_public_sources(root: Path, monkeypatch: pytest.MonkeyPatch):
    """Real frozen-spec admission and aggregation; only Git/calibration are seams."""
    _, template = _synthetic_source(
        root, monkeypatch, genome_canonicals=_mocc_genome_canonicals()
    )
    base_spec = json.loads((root / template["spec_relpath"]).read_bytes())
    calibrations = {}
    pins, paths, summaries = [], [], []
    for ordinal, rratio in enumerate(("5", "50", "95")):
        spec = copy.deepcopy(base_spec)
        cell = spec["cells"][0]
        cell["perf_config"]["workload"]["ycsb_rratio"] = rratio
        second_cell = copy.deepcopy(cell)
        second_cell["cell_id"] = "cell-b"
        spec["cells"].append(second_cell)
        second_pair = copy.deepcopy(spec["pairs"][0])
        second_pair.update(pair_id="pair-b", cell_id="cell-b")
        spec["pairs"].append(second_pair)
        # Distinct calibration references select the allowed dependency seam.
        calibration_path = f"refs/calibration-{ordinal}.json"
        calibration_sha = _write_bytes(root, calibration_path, b"{}\n")
        spec["provenance"]["calibration"].update(
            path=calibration_path, sha256=calibration_sha
        )
        calibrations[calibration_path] = driver_tests._verified_calibration(
            env_tag="synthetic-env", threads=4,
            workload=dict(cell["perf_config"]["workload"]),
        )
        window_template = copy.deepcopy(spec["windows"][0])
        spec["windows"] = []
        for day, wid in ((1, "a"), (2, "b")):
            window = copy.deepcopy(window_template)
            window.update(
                window_id=f"window-{wid}", campaign_id=f"campaign-{ordinal}-{wid}",
                not_before=f"2030-01-0{day}T00:00:00Z",
                not_after=f"2030-01-0{day}T01:00:00Z", sample_count=20,
                pair_ids=["pair-a", "pair-b"],
                # Shared between specs, as permitted by the aggregate contract.
                artifact_relpath=f"out/window-{wid}.jsonl",
            )
            spec["windows"].append(window)
        spec["statistics"]["closed_strata"] = [
            {"window_id": w["window_id"], "pair_id": pair}
            for w in spec["windows"] for pair in w["pair_ids"]
        ]
        summary_path = Path(f"out/summary-{ordinal}.json")
        spec["outputs"]["summary_relpath"] = summary_path.as_posix()
        spec_path = f"refs/spec-{ordinal}.json"
        spec_sha = _write_bytes(root, spec_path, _canonical(spec))
        pins.append((spec_path, spec_sha))
        summary = copy.deepcopy(template)
        candidate = (110.0, 130.0, 120.0)[ordinal]
        gain = floor_pair_driver.compute_gain_difference(
            candidate_1_tps=candidate, reference_1_tps=100.0,
            candidate_2_tps=100.0, reference_2_tps=100.0,
        )
        summary.update(
            spec_relpath=spec_path, spec_sha256=spec_sha,
            candidate_floor=gain.difference, upper=gain.difference,
            window_artifacts=[], campaigns=[], dropped=[],
            dropped_sample_count=2, dropped_record_count=4,
            derivation=[{"samples": [], "strata": []}],
            proof_limitations={
                "section": f"synthetic source {ordinal} limitations",
                "items": ["not a measurement", f"source {ordinal}"],
            },
        )
        for window in spec["windows"]:
            wid = window["window_id"]
            artifact_sha = _write_bytes(
                root, window["artifact_relpath"], b"synthetic window artifact\n"
            )
            summary["window_artifacts"].append({
                "window_id": wid, "campaign_id": window["campaign_id"],
                "artifact_relpath": window["artifact_relpath"],
                "artifact_sha256": artifact_sha,
            })
            campaign = {
                "window_id": wid, "campaign_id": window["campaign_id"],
                "planned_sample_count": 40, "dropped_sample_count": 1,
                "dropped_fraction": {"numerator": 1, "denominator": 40},
                "threshold": "1/20", "admissible": True, "strata": [],
            }
            for pair in window["pair_ids"]:
                missing = int(pair == "pair-a")
                for index in range(20):
                    if missing and index == 0:
                        for side in ("candidate_1", "candidate_2"):
                            summary["dropped"].append({
                                "window_id": wid, "pair_id": pair,
                                "sample_index": index, "side_id": side,
                                "status": "dropped", "error": "synthetic missing sample",
                                "dropped_by_session_id": None,
                            })
                        continue
                    summary["derivation"][0]["samples"].append({
                        "window_id": wid, "pair_id": pair, "sample_index": index,
                        "session_medians": {
                            "candidate_1": {"candidate": candidate, "reference": 100.0},
                            "candidate_2": {"candidate": 100.0, "reference": 100.0},
                        },
                        "gain_1": gain.gain_1, "gain_2": gain.gain_2,
                        "difference": gain.difference,
                    })
                summary["derivation"][0]["strata"].append({
                    "window_id": wid, "pair_id": pair,
                    "values": [gain.difference] * (20 - missing),
                    "upper_function": floor_pair_driver.STRATUM_UPPER_ID,
                    "upper": gain.difference,
                })
                campaign["strata"].append({
                    "window_id": wid, "pair_id": pair, "planned_sample_count": 20,
                    "dropped_sample_count": missing, "retained_sample_count": 20 - missing,
                })
            summary["campaigns"].append(campaign)
        _write_bytes(root, summary_path.as_posix(), _canonical(summary))
        paths.append(summary_path)
        summaries.append(summary)
    monkeypatch.setattr(
        floor_pair_driver.calibration_verify, "load_verified_calibration",
        lambda **kwargs: calibrations[str(kwargs["calibration_path"])],
    )
    return pins, paths, summaries, calibrations


def test_aggregate_public_issue_load_and_preregistration_pin(tmp_path, monkeypatch):
    pins, paths, summaries, _ = _aggregate_public_sources(tmp_path, monkeypatch)
    expected_values = [Fraction(s["candidate_floor"]) for s in summaries]
    assert len(set(expected_values)) == 3
    result = issuer.issue_aggregate_authoritative_floor(
        repo_root=tmp_path, summary_paths=paths, expected_specs=pins, output_dir=Path("out")
    )
    loaded = issuer.load_authoritative_floor(
        repo_root=tmp_path, artifact_path=result.artifact_path,
        expected_sha256=result.artifact_sha256,
    )
    prereg_path = Path("docs/prereg.md")
    _write_bytes(tmp_path, prereg_path.as_posix(), _preregistration(
        f"artifact_path={result.artifact_path}; sha256={result.artifact_sha256}"
    ))
    resolved = issuer.resolve_preregistered_authoritative_floor(
        repo_root=tmp_path, preregistration_path=prereg_path
    )
    assert resolved == loaded
    assert loaded.floor == max(expected_values)
    assert loaded.schema_version == "p3-b4-authoritative-floor/v2"
    assert loaded.artifact_path == result.artifact_path
    raw = (tmp_path / result.artifact_path).read_bytes()
    assert loaded.artifact_sha256 == result.artifact_sha256 == hashlib.sha256(raw).hexdigest()
    value = json.loads(raw)
    assert value["floor_exact"] == [loaded.floor.numerator, loaded.floor.denominator]
    assert value["aggregation"]["expected_specs"] == [list(pin) for pin in pins]
    assert len(value["aggregation"]["sources"]) == 3
    assert len(value["identity_derivation"]["workloads"]) == 3
    for source, path, pin, summary in zip(value["aggregation"]["sources"], paths, pins, summaries):
        assert source["artifact_path"] == path.as_posix()
        assert source["artifact_sha256"] == hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()
        assert (source["spec_relpath"], source["spec_sha256"]) == pin
        assert pin[1] == hashlib.sha256((tmp_path / pin[0]).read_bytes()).hexdigest()
        exact = Fraction(summary["candidate_floor"])
        assert source["floor_exact"] == [exact.numerator, exact.denominator]
        assert source["proof_limitations"] == summary["proof_limitations"]
        spec = json.loads((tmp_path / pin[0]).read_bytes())
        assert len(spec["windows"]) == 2
        assert len(spec["cells"]) == 2
        assert len(spec["statistics"]["closed_strata"]) == 4
        assert len(summary["derivation"][0]["samples"]) == 78
        assert summary["dropped_sample_count"] == 2
        assert summary["dropped_record_count"] == 4
    assert list(loaded.non_guarantees) == [
        *issuer.NON_GUARANTEES,
        *(item for s in summaries for item in s["proof_limitations"]["items"]),
        *issuer.AGGREGATE_NON_GUARANTEES,
    ]
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.issue_aggregate_authoritative_floor(
            repo_root=tmp_path, summary_paths=paths, expected_specs=pins, output_dir=Path("out")
        )
    assert caught.value.code == "artifact_exists"
    assert (tmp_path / result.artifact_path).read_bytes() == raw


def test_aggregate_public_missing_summary_keeps_expected_specs(tmp_path, monkeypatch):
    pins, paths, _, _ = _aggregate_public_sources(tmp_path, monkeypatch)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.issue_aggregate_authoritative_floor(
            repo_root=tmp_path, summary_paths=paths[:-1], expected_specs=pins,
            output_dir=Path("out"),
        )
    assert caught.value.code == "aggregate_spec_closure_error"
    assert not list((tmp_path / "out").glob("b4-floor-aggregate__*.json"))


@pytest.mark.parametrize("mutation", ("nonmaximum-floor", "nonmaximum-limitation"))
def test_aggregate_public_rejects_rehashed_artifact(tmp_path, monkeypatch, mutation):
    pins, paths, summaries, _ = _aggregate_public_sources(tmp_path, monkeypatch)
    result = issuer.issue_aggregate_authoritative_floor(
        repo_root=tmp_path, summary_paths=paths, expected_specs=pins, output_dir=Path("out")
    )
    value = json.loads((tmp_path / result.artifact_path).read_bytes())
    nonmaximum = value["aggregation"]["sources"][0]
    assert Fraction(*nonmaximum["floor_exact"]) < Fraction(*value["floor_exact"])
    if mutation == "nonmaximum-floor":
        value["floor_exact"] = nonmaximum["floor_exact"][:]
        value["source_float_hex"] = summaries[0]["candidate_floor"].hex()
        assert Fraction(float.fromhex(value["source_float_hex"])) == Fraction(*value["floor_exact"])
    else:
        nonmaximum["proof_limitations"]["items"].pop()
    digest = _write_bytes(tmp_path, result.artifact_path, _canonical(value))
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.load_authoritative_floor(
            repo_root=tmp_path, artifact_path=result.artifact_path, expected_sha256=digest
        )
    assert caught.value.code == "aggregate_reconstruction_error"


def test_aggregate_public_rejects_individually_valid_identity_mismatch(tmp_path, monkeypatch):
    pins, paths, summaries, calibrations = _aggregate_public_sources(tmp_path, monkeypatch)
    spec = json.loads((tmp_path / pins[0][0]).read_bytes())
    spec["environment"]["env_tag"] = "synthetic-other-env"
    calibration_path = spec["provenance"]["calibration"]["path"]
    calibrations[calibration_path] = driver_tests._verified_calibration(
        env_tag="synthetic-other-env", threads=4,
        workload=dict(spec["cells"][0]["perf_config"]["workload"]),
    )
    digest = _write_bytes(tmp_path, pins[0][0], _canonical(spec))
    pins[0] = (pins[0][0], digest)
    summaries[0]["spec_sha256"] = digest
    _write_bytes(tmp_path, paths[0].as_posix(), _canonical(summaries[0]))
    single = issuer.issue_authoritative_floor(repo_root=tmp_path, summary_path=paths[0])
    accepted = issuer.load_authoritative_floor(
        repo_root=tmp_path, artifact_path=single.artifact_path,
        expected_sha256=single.artifact_sha256,
    )
    assert accepted.identity.env_tag == "synthetic-other-env"
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.issue_aggregate_authoritative_floor(
            repo_root=tmp_path, summary_paths=paths, expected_specs=pins, output_dir=Path("out")
        )
    assert caught.value.code == "aggregate_identity_error"
    assert not list((tmp_path / "out").glob("b4-floor-aggregate__*.json"))


@pytest.mark.parametrize("window_count", (1, 3), ids=("one-window", "three-windows"))
def test_aggregate_public_rejects_non_two_window_spec(tmp_path, monkeypatch, window_count):
    pins, paths, summaries, _ = _aggregate_public_sources(tmp_path, monkeypatch)
    spec = json.loads((tmp_path / pins[0][0]).read_bytes())
    summary = summaries[0]
    if window_count == 1:
        spec["windows"] = spec["windows"][:1]
    else:
        third = copy.deepcopy(spec["windows"][0])
        third.update(
            window_id="window-c", campaign_id="campaign-0-c",
            not_before="2030-01-03T00:00:00Z",
            not_after="2030-01-03T01:00:00Z",
            artifact_relpath="out/window-c.jsonl",
        )
        spec["windows"].append(third)
        _write_bytes(tmp_path, third["artifact_relpath"], b"synthetic window artifact\n")
    spec["statistics"]["closed_strata"] = [
        {"window_id": window["window_id"], "pair_id": pair}
        for window in spec["windows"] for pair in window["pair_ids"]
    ]

    # Reuse complete per-window records, including both cells and dropped sides.
    # Calibration identity/workload is unchanged, so the helper's seam still fits.
    collections = [
        summary["window_artifacts"], summary["campaigns"], summary["dropped"],
        summary["derivation"][0]["samples"], summary["derivation"][0]["strata"],
    ]
    for rows in collections:
        if window_count == 1:
            rows[:] = [row for row in rows if row["window_id"] == "window-a"]
        else:
            for original in list(rows):
                if original["window_id"] != "window-a":
                    continue
                row = copy.deepcopy(original)
                row["window_id"] = "window-c"
                if "campaign_id" in row:
                    row["campaign_id"] = "campaign-0-c"
                if "artifact_relpath" in row:
                    row["artifact_relpath"] = "out/window-c.jsonl"
                if "strata" in row:
                    for stratum in row["strata"]:
                        stratum["window_id"] = "window-c"
                rows.append(row)
    summary["dropped_sample_count"] = window_count
    summary["dropped_record_count"] = 2 * window_count
    digest = _write_bytes(tmp_path, pins[0][0], _canonical(spec))
    pins[0] = (pins[0][0], digest)
    summary["spec_sha256"] = digest
    _write_bytes(tmp_path, paths[0].as_posix(), _canonical(summary))

    # Prove admission and closure independently of the aggregate count guard.
    loaded_spec = floor_pair_driver.load_frozen_spec(
        Path(pins[0][0]), digest, repo_root=tmp_path,
    )
    assert len(loaded_spec.windows) == window_count
    loaded_summary = issuer.load_floor_pair_summary(
        repo_root=tmp_path, summary_path=paths[0],
    )
    issuer._validate_aggregate_summary_coverage(loaded_spec, loaded_summary, summary)
    with pytest.raises(issuer.B4FloorArtifactError) as caught:
        issuer.issue_aggregate_authoritative_floor(
            repo_root=tmp_path, summary_paths=paths, expected_specs=pins,
            output_dir=Path("out"),
        )
    assert caught.value.code == "aggregate_window_count_error"
    assert not list((tmp_path / "out").glob("b4-floor-aggregate__*.json"))


def _run() -> int:
    """pytest fixtures/parametrize を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
