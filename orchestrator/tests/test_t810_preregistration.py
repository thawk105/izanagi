# -*- coding: utf-8 -*-
"""T-810 canonical preregistration と dormant seal の負例。"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
REPO_ROOT = ORCHESTRATOR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign.t810_preregistration import (  # noqa: E402
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    ENVIRONMENT_CONTRACT_SHA256,
    PREREG_PATH,
    ApprovalReceipt,
    T810NotAuthorizedError,
    T810PreregistrationError,
    VerifiedT810Preregistration,
    _canonical_bytes,
    _verify_approval_digest,
    load_t810_preregistration,
    request_t810_launch,
)


# 第 1 段の人間 receipt を模した固定 fixture。artifact から実行時に導出しない。
FIXTURE_ARTIFACT_SHA256 = "3052af20993481730a826ce08ee26289948f29836d43afb2d7c743cfdd12e404"
FIXTURE_RECEIPT = ApprovalReceipt(
    artifact_sha256=FIXTURE_ARTIFACT_SHA256,
    approval_id="fixture-stage1-review-t810-v1",
    schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
)


def _load():
    return load_t810_preregistration(
        PREREG_PATH, approval_receipt=FIXTURE_RECEIPT
    )


def _canonical_payload(payload: dict) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ": "),
            indent=2,
        )
        + "\n"
    ).encode()


def _receipt_for(raw: bytes) -> ApprovalReceipt:
    return ApprovalReceipt(
        artifact_sha256=hashlib.sha256(raw).hexdigest(),
        approval_id="negative-fixture",
        schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
    )


def test_fixture_receipt_pins_raw_artifact_bytes_and_environment_digest():
    raw = PREREG_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_ARTIFACT_SHA256
    prereg = _load()
    digest = prereg.projection["measurement"]["environment"]["contract_sha256"]
    assert digest == ENVIRONMENT_CONTRACT_SHA256
    assert digest == "1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c"
    assert len(digest) == 64


def test_loader_requires_external_receipt_and_rejects_self_authenticating_digest():
    with pytest.raises(TypeError):
        load_t810_preregistration(PREREG_PATH)  # type: ignore[call-arg]
    wrong = ApprovalReceipt(
        artifact_sha256="0" * 64,
        approval_id="wrong-authority",
        schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
    )
    with pytest.raises(T810PreregistrationError, match="approval receipt"):
        load_t810_preregistration(PREREG_PATH, approval_receipt=wrong)


def test_digest_verifier_hashes_raw_not_reserialized_bytes():
    canonical = PREREG_PATH.read_bytes()
    noncanonical = canonical.replace(b"{\n", b"{ \n", 1)
    receipt = ApprovalReceipt(
        artifact_sha256=hashlib.sha256(canonical).hexdigest(),
        approval_id="raw-vs-canonical",
        schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
    )
    with pytest.raises(T810PreregistrationError, match="digest"):
        _verify_approval_digest(raw=noncanonical, canonical=canonical, receipt=receipt)


def test_loader_rejects_one_byte_tamper_even_when_json_remains_canonical(tmp_path: Path):
    raw = PREREG_PATH.read_bytes().replace(b'"node_count": 13', b'"node_count": 12', 1)
    path = tmp_path / "tampered.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError, match="digest"):
        load_t810_preregistration(path, approval_receipt=FIXTURE_RECEIPT)


@pytest.mark.parametrize(
    "transform",
    [
        lambda raw: b"\xef\xbb\xbf" + raw,
        lambda raw: raw.replace(b"\n", b"\r\n"),
        lambda raw: raw + b"\n",
        lambda raw: raw.replace(b"{\n", b"{ \n", 1),
    ],
)
def test_loader_rejects_noncanonical_transport_bytes(tmp_path: Path, transform):
    raw = transform(PREREG_PATH.read_bytes())
    path = tmp_path / "transport.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))


def test_loader_rejects_nested_duplicate_key(tmp_path: Path):
    raw = PREREG_PATH.read_bytes().replace(
        b'"node_count": 13,', b'"node_count": 13,\n      "node_count": 12,', 1
    )
    path = tmp_path / "duplicate.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError, match="duplicate JSON key"):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))


@pytest.mark.parametrize("token", [b"0.5", b"NaN", b"Infinity", b"-0"])
def test_loader_rejects_float_nonfinite_and_negative_zero(tmp_path: Path, token: bytes):
    raw = PREREG_PATH.read_bytes().replace(b"400000", token, 1)
    path = tmp_path / "number.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))


def test_hidden_candidate_and_unknown_nested_field_are_rejected(tmp_path: Path):
    payload = json.loads(PREREG_PATH.read_text())
    payload["design"]["hidden_candidate"] = {"node_count": 12, "round_count": 12}
    raw = _canonical_payload(payload)
    path = tmp_path / "candidate.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))


def test_recursive_design_schema_rejects_nested_alternative_before_conformance(
    tmp_path: Path,
):
    payload = json.loads(PREREG_PATH.read_text())
    payload["design"]["assurance"]["alternatives"] = [{"N": 12, "R": 12}]
    raw = _canonical_payload(payload)
    path = tmp_path / "nested-alternative.json"
    path.write_bytes(raw)
    with pytest.raises(
        T810PreregistrationError,
        match=r"/design/assurance has an unknown or missing field",
    ):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))


def test_verified_preregistration_cannot_be_constructed_outside_loader():
    with pytest.raises(T810PreregistrationError, match="only be constructed by the loader"):
        VerifiedT810Preregistration(
            sha256="0" * 64,
            approval_id="bypass",
            projection={"protocol": {"run_authorized": False}},
        )


def test_selected_design_has_no_runtime_candidate_table_and_state_df_are_derived():
    prereg = _load()
    design = prereg.projection["design"]
    assert design["selected"] == {
        "node_count": 13,
        "round_count": 10,
        "total_measurements": 130,
        "unique_minimum": True,
    }
    assert set(design["effective_states"]) == {"valid", "terminal_reduced"}
    assert design["effective_states"]["valid"] == {
        "effective_node_count": 13,
        "nu1": 12,
        "nu2": 108,
    }
    assert design["effective_states"]["terminal_reduced"] == {
        "effective_node_count": 12,
        "nu1": 11,
        "nu2": 99,
    }
    assert prereg.effective_node_count("valid") == 13
    assert prereg.effective_node_count("terminal_reduced") == 12


def test_preregistration_contains_adjudicated_upper_closure():
    root = _load().projection
    assert root["authorization"] == {
        "missing_components": ("a", "b", "c", "d2", "f", "g"),
        "stage1_satisfied": False,
    }
    assert root["limitations"]["execution_mediation_incomplete"] is True
    assert root["limitations"]["approval_receipt_trust_root_absent"] is True
    assert root["limitations"]["unfrozen_procedures"] == (
        "build_argv",
        "qsub_argv",
        "raw_throughput_to_log_matrix",
        "secondary_quantities",
        "downstream_decision_consumer",
    )
    assert root["assignment"]["submission_order"]["receipt_fields"] == (
        "seed",
        "permutation",
    )
    assert set(root["downstream_decisions"]["mapping"]) == {
        "pre_release_invalid",
        "post_release_pre_measurement_invalid",
        "incomplete_after_start",
        "material_node_difference_refuted",
        "material_node_difference_supported",
        "underdetermined",
        "underdetermined_model_violation",
    }
    assert root["lineage"]["attempt_schema"] == (
        "protocol_digest",
        "attempt_id",
        "submission_nonce",
        "group_manifest_sha256",
        "release_token_sha256",
        "slot_id",
    )
    reproduction = root["design"]["assurance_reproduction"]
    assert reproduction["draw_order"] == ("MS_A", "MS_E")
    assert reproduction["wins"] == {"dropout": 323211, "selected": 338491}
    assert reproduction["update_values_on_mismatch"] is False
    assert reproduction["failure_code"] == "reference_not_reproduced"
    assert set(root["artifacts"]["presence_matrix"]) == {
        "pre_release_invalid",
        "post_release_pre_measurement_invalid",
        "incomplete_after_start",
        "terminal_reduced",
        "valid",
    }
    assert root["artifacts"]["presence_matrix"]["pre_release_invalid"] == {
        "estimate": "forbidden",
        "measurements": "forbidden",
        "node_receipts": "reached-slots-exact",
        "release_event": "forbidden",
    }
    assert root["artifacts"]["presence_matrix"]["terminal_reduced"]["estimate"] == "required"
    assert root["artifacts"]["presence_matrix"]["valid"]["measurements"] == "all-13-times-10"


def test_benchmark_argv_and_submission_permutation_procedure_are_exact():
    root = _load().projection
    assert root["measurement"]["canonical_benchmark_argv"] == (
        "-thread_num=48",
        "-ycsb_tuple_num=1000000",
        "-extime=3",
        "-clocks_per_us=2100",
        "-ycsb_rratio=50",
        "-ycsb_zipf_skew=0.9",
        "-ycsb_rmw=0",
    )
    submission = root["assignment"]["submission_order"]
    assert submission == {
        "canonical_encoding": "utf8-json-array-no-whitespace",
        "canonical_permutation": (
            '["slot-02","slot-00","slot-07","slot-11","slot-05",'
            '"slot-09","slot-04","slot-03","slot-12","slot-10",'
            '"slot-01","slot-06","slot-08"]'
        ),
        "expected_permutation": (
            "slot-02",
            "slot-00",
            "slot-07",
            "slot-11",
            "slot-05",
            "slot-09",
            "slot-04",
            "slot-03",
            "slot-12",
            "slot-10",
            "slot-01",
            "slot-06",
            "slot-08",
        ),
        "freeze_before_submission": True,
        "permutation_generation": "Generator(PCG64(seed)).permutation(slot_domain)",
        "prng": "PCG64",
        "receipt_fields": ("seed", "permutation"),
        "seed": 810,
        "seed_source": "approved-attempt-manifest",
        "slot_domain": tuple(f"slot-{index:02d}" for index in range(13)),
        "version": "NumPy-2.2.6",
    }


def test_loader_rejects_golden_schema_drift_and_replays_live_conformance(tmp_path: Path):
    payload = json.loads(PREREG_PATH.read_text())
    del payload["golden_vectors"][0]["expected"]["tau_U"]
    raw = _canonical_payload(payload)
    path = tmp_path / "missing-golden-field.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError, match="unknown or missing field"):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))

    payload = json.loads(PREREG_PATH.read_text())
    payload["golden_vectors"][0]["expected"]["conclusion_code"] = "underdetermined"
    raw = _canonical_payload(payload)
    path = tmp_path / "semantic-golden-drift.json"
    path.write_bytes(raw)
    with pytest.raises(T810PreregistrationError, match="does not conform"):
        load_t810_preregistration(path, approval_receipt=_receipt_for(raw))


def test_projection_is_deeply_immutable_including_every_nested_sequence():
    projection = _load().projection

    def visit(value):
        if isinstance(value, MappingProxyType):
            with pytest.raises(TypeError):
                value["mutation"] = True
            for child in value.values():
                visit(child)
        elif isinstance(value, tuple):
            with pytest.raises(TypeError):
                value[0] = None
            for child in value:
                visit(child)
        else:
            assert not isinstance(value, (dict, list))

    visit(projection)


def test_dormant_seal_has_no_successful_launch_path():
    prereg = _load()
    assert prereg.run_authorized is False
    with pytest.raises(T810NotAuthorizedError):
        request_t810_launch(prereg)


def test_policy_registry_contains_t810_in_sorted_closed_list():
    registry = json.loads(
        (REPO_ROOT / "tools/pegasus/policies/registry_v1.json").read_text()
    )
    paths = registry["policy_paths"]
    assert paths == sorted(paths)
    assert paths.count("tools/pegasus/policies/t810_prereg_v1.json") == 1


def test_canonical_round_trip_is_exact():
    raw = PREREG_PATH.read_bytes()
    parsed = json.loads(raw)
    assert _canonical_bytes(parsed) == raw
