# -*- coding: utf-8 -*-
"""偵察 sweep 専用 screening driver の計測なし単体テスト。"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import env_contract, ident, screening_driver, wal  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from campaign.layout import campaign_layout                     # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_DONE,  # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT,
                            CampaignConfig, Genome)
from campaign.pipeline import EvalResult, PerfConfig             # noqa: E402
from campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)


WORKLOAD = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}
_BUILD_CONTEXT = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
_AUTHORIZATION = env_contract.lookup("linux-baremetal")


def _source_evidence(genome: Genome, *, root: str = "/fixture/ccbench"):
    return SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=os.path.realpath(root),
        ccbench_commit="deadbeef",
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token="stock",
        source_bytes_sha256="3" * 64,
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )


def _log_completed_attempt(layout, variant: str, genome: Genome) -> None:
    evidence = _source_evidence(genome)
    generator = attest_generator_output(
        _BUILD_CONTEXT, evidence, generator_input_sha256="1" * 64,
    )
    admission = derive_build_admission(
        _BUILD_CONTEXT, evidence, generator_receipt=generator,
    )
    attempt_id = f"fixture-{variant}"
    common = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": admission.receipt_sha256,
    }
    wal.log(layout, variant, STAGE_BUILD_START, "test", {
        **common,
        "genome": genome.canonical(),
        "src_token": evidence.src_token,
        "build_admission": admission.as_wal_receipt(),
    })
    wal.log(layout, variant, STAGE_BUILD_DONE, "test", common)
    wal.log(layout, variant, STAGE_COMMIT, "test", common)


def _cfg():
    return ident.bind_admission_policy(CampaignConfig(
        spec_slug="screen-driver", search_tag="sweep", spec_content="fixture",
        ccbench_commit="deadbeef", search_config={"workload": "balanced"},
        trial="fixture"), _BUILD_CONTEXT.policy)


def _write_floor(root, *, floor=0.03, workload=WORKLOAD):
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "between_run_noise_fixture.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"workload": workload, "between_run": {"cv": floor}}, f)
    return path


def test_prepare_screening_bakes_identity_and_uses_new_same_campaign_baseline(tmp_path):
    calibration = str(tmp_path / "calibration")
    output = str(tmp_path / "output")
    _write_floor(calibration, floor=0.03000001)
    seen = {}

    def measure(cfg, layout):
        seen["cfg"] = cfg
        seen["layout"] = layout
        assert cfg.search_config["screening"] == {
            "baseline_ref": "baseline-v1", "floor": "0.03000001", "k": "1.5",
            "high_abort_factor": "2.0"}
        wal.log(layout, "baseline-v1", STAGE_BENCH_DONE, "test", {
            "median_tps": 10000.0,
            "leading_indicators": {"abort_rate": 0.04},
        }, ts=1234.0)
        wal.log(layout, "baseline-v1", STAGE_COMMIT, "test", {
            "fitness_tps": 10000.0,
        }, ts=1235.0)

    prepared = screening_driver.prepare_screening_campaign(
        _cfg(), WORKLOAD, "baseline-v1", measure,
        authorization_contract=_AUTHORIZATION,
        env_tag=_AUTHORIZATION.env_tag,
        clocks_per_us=_AUTHORIZATION.clocks_per_us,
        numactl=_AUTHORIZATION.numactl,
        calibration_dir=calibration, output_root=output,
        build_context=_BUILD_CONTEXT)
    assert prepared.cfg is seen["cfg"] and prepared.layout is seen["layout"]
    assert prepared.screening.baseline_tps == 10000.0
    assert prepared.screening.baseline_abort_rate == 0.04
    assert prepared.screening.baseline_measured_at == 1234.0
    assert prepared.screening.floor == 0.03000001
    ident.verify_screening_preimage(
        prepared.screening, wal.read_lock(prepared.layout))


def test_prepare_screening_fails_closed_when_floor_json_missing(tmp_path):
    called = False

    def measure(_cfg, _layout):
        nonlocal called
        called = True

    with pytest.raises(ValueError, match="floor JSON"):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            authorization_contract=_AUTHORIZATION,
            env_tag=_AUTHORIZATION.env_tag,
            clocks_per_us=_AUTHORIZATION.clocks_per_us,
            numactl=_AUTHORIZATION.numactl,
            calibration_dir=str(tmp_path / "missing"), output_root=str(tmp_path / "out"),
            build_context=_BUILD_CONTEXT)
    assert called is False


def test_prepare_screening_rejects_authorization_before_layout_or_wal(tmp_path):
    output = tmp_path / "output"
    calibration = tmp_path / "calibration"
    _write_floor(str(calibration))
    called = False

    def measure(_cfg, _layout):
        nonlocal called
        called = True

    with pytest.raises(TypeError, match="authorization_contract"):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            authorization_contract=None,
            env_tag=_AUTHORIZATION.env_tag,
            clocks_per_us=_AUTHORIZATION.clocks_per_us,
            numactl=_AUTHORIZATION.numactl,
            calibration_dir=str(calibration), output_root=str(output),
            build_context=_BUILD_CONTEXT,
        )
    assert called is False
    assert not output.exists()


@pytest.mark.parametrize("missing", ["median", "abort_rate", "commit"])
def test_prepare_screening_requires_complete_baseline_evidence(tmp_path, missing):
    calibration = str(tmp_path / f"cal-{missing}")
    _write_floor(calibration)

    def measure(_cfg, layout):
        payload = {"median_tps": 100.0,
                   "leading_indicators": {"abort_rate": 0.1}}
        if missing == "median":
            payload.pop("median_tps")
        if missing == "abort_rate":
            payload["leading_indicators"].pop("abort_rate")
        wal.log(layout, "baseline-v1", STAGE_BENCH_DONE, "test", payload, ts=10.0)
        if missing != "commit":
            wal.log(layout, "baseline-v1", STAGE_COMMIT, "test", {}, ts=11.0)

    with pytest.raises(ValueError):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            authorization_contract=_AUTHORIZATION,
            env_tag=_AUTHORIZATION.env_tag,
            clocks_per_us=_AUTHORIZATION.clocks_per_us,
            numactl=_AUTHORIZATION.numactl,
            calibration_dir=calibration, output_root=str(tmp_path / f"out-{missing}"),
            build_context=_BUILD_CONTEXT)


def test_prepare_repairs_tail_before_baseline_callback(tmp_path):
    calibration = str(tmp_path / "calibration")
    output = str(tmp_path / "output")
    _write_floor(calibration)
    policy = ident.screening_policy_search_config("baseline-v1", 0.03, 1.5, 2.0)
    cfg = CampaignConfig(
        **{**_cfg().__dict__, "search_config": {**_cfg().search_config, **policy}})
    layout = campaign_layout(str(ident.campaign_id(cfg)), output).ensure()
    wal.write_lock(layout, ident.canonical_preimage(cfg))
    _log_completed_attempt(layout, "prior", Genome("silo", {"BACK_OFF": 0}))
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    surfaced = []

    def measure(_cfg, callback_layout):
        assert callback_layout.wal_file == layout.wal_file
        records, truncated = wal.read_records_checked(callback_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"] * 3
        wal.log(callback_layout, "baseline-v1", STAGE_BENCH_DONE, "test", {
            "median_tps": 100.0,
            "leading_indicators": {"abort_rate": 0.1},
        }, ts=10.0)
        wal.log(callback_layout, "baseline-v1", STAGE_COMMIT, "test", {}, ts=11.0)

    screening_driver.prepare_screening_campaign(
        _cfg(), WORKLOAD, "baseline-v1", measure,
        authorization_contract=_AUTHORIZATION,
        env_tag=_AUTHORIZATION.env_tag,
        clocks_per_us=_AUTHORIZATION.clocks_per_us,
        numactl=_AUTHORIZATION.numactl,
        calibration_dir=calibration, output_root=output, log=surfaced.append,
        build_context=_BUILD_CONTEXT)
    assert len(surfaced) == 1 and '"status": "repaired"' in surfaced[0]
    assert '"removed_bytes": 8' in surfaced[0]


def test_evaluate_candidate_repairs_tail_before_replay_and_evaluate(
        tmp_path, monkeypatch):
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    wal.write_lock(layout, ident.canonical_preimage(cfg))
    prior_genome = Genome("silo", {"BACK_OFF": 0})
    _log_completed_attempt(layout, "prior", prior_genome)
    with open(layout.wal_file, "ab") as stream:
        stream.write("途中".encode("utf-8")[:4])
    genome = Genome("silo", {"BACK_OFF": 1})
    calls = []

    def evaluate(candidate, candidate_layout, *args, **kwargs):
        records, truncated = wal.read_records_checked(candidate_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"] * 3
        calls.append(candidate)
        return EvalResult(
            genome=candidate, variant="candidate", certified=True, aborted=False)

    monkeypatch.setattr(screening_driver, "evaluate", evaluate)
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome),
    )
    result = screening_driver.evaluate_candidate(
        cfg, layout, genome, PerfConfig(records=1, threads=1),
        _AUTHORIZATION.env_tag, _AUTHORIZATION.clocks_per_us,
        numactl=_AUTHORIZATION.numactl,
        authorization_contract=_AUTHORIZATION,
        build_context=_BUILD_CONTEXT,
        screening=None, src_token="stock", log=lambda message: None)
    assert result is not None and result.certified and calls == [genome]


@pytest.mark.parametrize("failure_kind", ["append", "framing"])
def test_evaluate_candidate_does_not_append_abort_after_wal_io_error(
        tmp_path, monkeypatch, failure_kind):
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    ident.ensure_resumable_wal(
        cfg, layout, admission_policy=_BUILD_CONTEXT.policy,
    )
    genome = Genome("silo", {"BACK_OFF": 1})
    failure = (wal.WalAppendError(
        layout.wal_file, 10, 3, "write", OSError("disk"))
        if failure_kind == "append" else wal.WalFramingError("unframed"))

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(screening_driver, "evaluate", fail)
    monkeypatch.setattr(
        screening_driver.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: _source_evidence(genome),
    )
    with pytest.raises(type(failure)) as caught:
        screening_driver.evaluate_candidate(
            cfg, layout, genome, PerfConfig(records=1, threads=1),
            _AUTHORIZATION.env_tag, _AUTHORIZATION.clocks_per_us,
            numactl=_AUTHORIZATION.numactl,
            authorization_contract=_AUTHORIZATION,
            build_context=_BUILD_CONTEXT,
            screening=None, src_token="stock", log=lambda message: None)
    assert caught.value is failure
    assert wal.read_records(layout) == []
