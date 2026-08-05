# -*- coding: utf-8 -*-
"""D12 層3材料レポートの決定論的な完全射影を検査する。"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from campaign import (  # noqa: E402
    layer3_report,
    model,
    s8c_acceptance_receipt,
    trigger_gate_binding,
    wal,
)
from campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from campaign.pin import CURRENT_PIN  # noqa: E402
from campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)


ROOT = _HERE.parent.parent
REAL_CAMPAIGN = ROOT / "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
YCSB = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}
ABORTED_FIXTURE_VARIANT = "2225adf39fa3"
REJECTED_FIXTURE_VARIANT = "d85dc0fc5a6e"


def _admission_bound_records(tmp_path: Path, records: list[dict]) -> tuple[list[dict], dict]:
    """Turn semantic Layer3 fixtures into independently generated post-policy WAL."""
    copied = json.loads(json.dumps(records))
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    labels = list(dict.fromkeys(record["variant"] for record in copied))
    by_label = {label: [record for record in copied if record["variant"] == label]
                for label in labels}
    bindings = {}
    for ordinal, label in enumerate(labels):
        group = by_label[label]
        stages = {record["stage"] for record in group}
        needs_start = bool(stages & {
            "build_start", "build_done", "verify_done", "bench_done", "commit",
        })
        if not needs_start:
            continue
        protocol = f"fixture-{hashlib.sha256(label.encode()).hexdigest()[:8]}"
        canonical = f"{protocol}|"
        variant = hashlib.sha256(canonical.encode()).hexdigest()[:12]
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str(tmp_path.resolve()),
            ccbench_commit=CURRENT_PIN,
            genome_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            src_token="stock",
            source_bytes_sha256="a" * 64,
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        bindings[label] = {
            "attempt": f"fixture-attempt-{ordinal}",
            "canonical": canonical,
            "variant": variant,
            "receipt": receipt,
        }

    rendered = []
    started = set()
    for record in copied:
        label = record["variant"]
        binding = bindings.get(label)
        if binding is None:
            rendered.append(record)
            continue
        if label not in started and record["stage"] != "build_start":
            rendered.append({
                "ts": record["ts"],
                "stage": "build_start",
                "variant": binding["variant"],
                "env_tag": record["env_tag"],
                "payload": {
                    "genome": binding["canonical"],
                    "src_token": "stock",
                    "build_attempt_id": binding["attempt"],
                    "build_admission": binding["receipt"],
                    "build_admission_receipt_sha256": binding["receipt"]["receipt_sha256"],
                },
            })
            started.add(label)
        record["variant"] = binding["variant"]
        if record["stage"] == "build_start":
            record["payload"].update({
                "genome": binding["canonical"],
                "src_token": "stock",
                "build_attempt_id": binding["attempt"],
                "build_admission": binding["receipt"],
                "build_admission_receipt_sha256": binding["receipt"]["receipt_sha256"],
            })
            started.add(label)
        elif record["stage"] in {"build_done", "commit", "abort"}:
            record["payload"]["build_attempt_id"] = binding["attempt"]
            record["payload"]["build_admission_receipt_sha256"] = (
                binding["receipt"]["receipt_sha256"]
            )
        rendered.append(record)
    return rendered, dict(context.policy.as_preimage())


def _campaign(tmp_path: Path, records, whiteboard=None, *, loop_state=True,
              ycsb=None) -> tuple[Path, Path]:
    output_root = tmp_path / "repo" / "output"
    root = output_root / "campaigns" / "campaign"
    (root / "runs").mkdir(parents=True)
    records, admission_policy = _admission_bound_records(tmp_path, records)
    search_config = {
        "records": 100000,
        "threads": 4,
        "build_admission": admission_policy,
    }
    if ycsb is not None:
        search_config["ycsb"] = ycsb
    (root / "campaign.lock").write_text(json.dumps({
        "ccbench_commit": CURRENT_PIN, "search_config": search_config,
        "search_tag": "test", "spec_content": "test", "trial": "trial",
    }), encoding="utf-8")
    if loop_state:
        (root / "loop_state.json").write_text(
            json.dumps({"whiteboard": whiteboard if whiteboard is not None else []}),
            encoding="utf-8")
    (root / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return root, output_root


def _verified_non_certifying_receipt(
    campaign: Path,
    output_root: Path,
) -> s8c_acceptance_receipt.VerifiedAcceptanceReceipt:
    repo = output_root.parent
    init = subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=False,
        capture_output=True, text=True,
    )
    assert init.returncode == 0, init.stderr
    for key, value in (
        ("user.email", "fixture@example.invalid"),
        ("user.name", "Fixture"),
    ):
        assert subprocess.run(
            ["git", "-C", str(repo), "config", key, value], check=False,
        ).returncode == 0

    def write(relative: str, data: bytes) -> str:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    manifest_path = "input/manifest.json"
    manifest_sha = write(manifest_path, b'{"fixture":"manifest"}\n')
    registry_path = "output/s8c-trial-registry/registry.jsonl"
    registry_sha = write(registry_path, b'{"fixture":"registry"}\n')
    lifecycle_path = "output/s8c-trial-registry/lifecycle.jsonl"
    lifecycle_sha = write(lifecycle_path, b'{"fixture":"lifecycle"}\n')
    trial_rows = []
    for index in range(6):
        trial_id = "trial" if index == 0 else f"trial-{index}"
        report_path = f"acceptance-refs/{trial_id}/report.json"
        journal_path = f"acceptance-refs/{trial_id}/attempts.jsonl"
        trial_rows.append({
            "trial_id": trial_id,
            "arm": ("on", "off", "swapped")[index % 3],
            "holdout": "H1" if index < 3 else "H2",
            "campaign_id": campaign.name if index == 0 else f"other-{index}",
            "status": "complete",
            "measurement_head": "1" * 40,
            "report_path": report_path,
            "report_sha256": write(report_path, f"report-{index}\n".encode()),
            "attempt_journal_path": journal_path,
            "attempt_journal_sha256": write(
                journal_path, f"journal-{index}\n".encode()
            ),
        })
    assert subprocess.run(
        ["git", "-C", str(repo), "add", "-A"], check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "references"],
        check=False,
    ).returncode == 0
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
    ).strip()
    value = {
        "schema_version": s8c_acceptance_receipt.SCHEMA_VERSION,
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha,
        "prereg_commit": head,
        "activation_report_digest_sha256": "2" * 64,
        "registry_path": registry_path,
        "registry_blob_sha256": registry_sha,
        "registry_introduction_commit": head,
        "lifecycle_path": lifecycle_path,
        "lifecycle_prefix_bytes": len((repo / lifecycle_path).read_bytes()),
        "lifecycle_prefix_sha256": lifecycle_sha,
        "certifying": False,
        "non_certifying_reason_codes": sorted(
            s8c_acceptance_receipt.MANDATORY_NON_CERTIFYING_REASONS
        ),
        "trials": sorted(trial_rows, key=lambda item: item["trial_id"]),
    }
    receipt_path = repo.joinpath(
        *s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR.parts,
        f"{manifest_sha}.json",
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode() + b"\n"
    )
    assert subprocess.run(
        ["git", "-C", str(repo), "add", "-A"], check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "receipt"],
        check=False,
    ).returncode == 0
    return s8c_acceptance_receipt.verify_acceptance_receipt(
        receipt_path, repository_root=repo,
    )


def test_trigger_build_start_commitment_survives_report_projection_without_raw_mask():
    commitment = "c" * 64
    records = [{
        "variant": "trigger-v",
        "stage": "build_start",
        "env_tag": "test",
        "ts": 1.0,
        "payload": {
            "genome": "silo|BACK_OFF=1",
            "src_token": "stock",
            "trigger_gate_binding_commitment": commitment,
        },
    }]
    rows = layer3_report._variant_rows(records)
    assert rows[0]["events"][0]["payload"][
        "trigger_gate_binding_commitment"
    ] == commitment
    rendered = json.dumps(rows, sort_keys=True)
    assert '"mask"' not in rendered
    assert '"trigger_gate_binding"' not in rendered


def test_trigger_campaign_report_keeps_commitment_and_excludes_raw_binding(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [
            _record("build_start", genome="fixture|", src_token="stock"),
            _record("abort", reason="fixture-abort"),
        ],
    )
    lock_path = campaign / "campaign.lock"
    lock = json.loads(lock_path.read_text())
    lock["search_config"].update({
        "axis": wal.TRIGGER_AXIS,
        "reflux": "on",
        wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY: trigger_gate_binding.SCHEMA_VERSION,
    })
    canonical_lock = json.dumps(
        lock, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    lock_path.write_bytes(canonical_lock)
    canonical_campaign = campaign.with_name(
        f"campaign-{lock['search_tag']}-{hashlib.sha256(canonical_lock).hexdigest()[:8]}"
    )
    campaign.rename(canonical_campaign)
    campaign = canonical_campaign

    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    start = next(record for record in records if record["stage"] == "build_start")
    source = start["payload"]["build_admission"]["source"]
    binding = trigger_gate_binding.TriggerGateBinding(
        mask=4,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(4),
        nonce="4" * 64,
        source=trigger_gate_binding.SourceBinding(
            src_token=source["src_token"],
            source_bytes_sha256=source["source_bytes_sha256"],
        ),
    )
    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY] = \
        trigger_gate_binding.commitment(binding)
    raw = {
        "variant": start["variant"],
        "stage": trigger_gate_binding.WAL_RECORD_STAGE,
        "env_tag": start["env_tag"],
        "ts": start["ts"] - 0.5,
        "payload": {
            "build_attempt_id": start["payload"]["build_attempt_id"],
            wal.TRIGGER_BINDING_PAYLOAD_KEY: trigger_gate_binding.to_record(binding),
        },
    }
    records.insert(records.index(start), raw)
    wal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    reports = campaign / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "p3_s8a_trigger_loop_provenance.json").write_text(json.dumps({
        "entries": {
            "1": {
                "variant": start["variant"],
                "build_attempt_id": start["payload"]["build_attempt_id"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY:
                    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
            },
        },
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    rendered = json.dumps(report, sort_keys=True)
    assert start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY] in rendered
    assert '"trigger_gate_binding"' not in rendered
    assert '"mask"' not in rendered


def _record(stage, variant="v1", **payload):
    return {"ts": 1.0, "stage": stage, "variant": variant, "env_tag": "test-env", "payload": payload}


def _bench(variant="v1", **extra):
    return _record("bench_done", variant, tps=[1.0], median_tps=1.0, cv=0.0,
                   rounds=1, leading_indicators={}, **extra)


def test_real_legacy_s8a_campaign_is_rejected(tmp_path):
    out = tmp_path / "report.json"
    with pytest.raises(layer3_report.Layer3ReportError, match="legacy-unclassified"):
        layer3_report.render(REAL_CAMPAIGN, out, generated_from_head="fixed-head")
    assert not out.exists()


def test_campaign_without_loop_state_has_empty_absent_whiteboard(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], loop_state=False)
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["whiteboard"] == []
    assert report["whiteboard_provenance"] == "absent"
    assert not any(ref.startswith("wb:") for ref in report["source_refs"])
    assert report["schema_version"] == "layer3-material-report/v3"
    assert report["acceptance_receipt"] is None
    assert report["certifying_input"] is False
    decision = report["admission_decision"]
    assert decision["classification"] == "admitted-new-schema"
    assert decision["admission_status"] == "admitted"
    assert decision["overlay"]["record_key"] is None


def test_legacy_v2_report_schema_remains_readable(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v2"
    del legacy["admission_decision"]
    del legacy["acceptance_receipt"]
    del legacy["certifying_input"]
    layer3_report._validate_schema(legacy)


def test_existing_v3_missing_new_admission_fields_remains_readable(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    assert report["acceptance_receipt"] is None
    del report["acceptance_receipt"]
    del report["certifying_input"]
    layer3_report._validate_schema(report)


def test_generic_generators_have_no_certifying_input_parameter(
    tmp_path: Path,
) -> None:
    import inspect

    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign,
        generated_from_head="fixed",
        output_root=output_root,
    )
    assert report["certifying_input"] is False
    assert "certifying_input" not in inspect.signature(
        layer3_report.build_report
    ).parameters
    assert "certifying_input" not in inspect.signature(
        layer3_report.render
    ).parameters
    with pytest.raises(TypeError, match="certifying_input"):
        layer3_report.build_report(
            campaign,
            generated_from_head="fixed",
            output_root=output_root,
            certifying_input=True,
        )
    with pytest.raises(TypeError, match="certifying_input"):
        layer3_report.render(
            campaign,
            tmp_path / "forbidden-certifying-report.json",
            generated_from_head="fixed",
            output_root=output_root,
            certifying_input=True,
        )


def test_reader_rejects_certifying_input_without_acceptance_receipt(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["certifying_input"] = True
    assert report["acceptance_receipt"] is None
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying_input=true と acceptance_receipt 非 null は同値必須$",
    ):
        layer3_report._validate_schema(report)


def test_reader_rejects_acceptance_receipt_without_certifying_input(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["acceptance_receipt"] = {"path": "receipt.json", "sha256": "a" * 64}
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying_input=true と acceptance_receipt 非 null は同値必須$",
    ):
        layer3_report._validate_schema(report)


def test_m14_non_certifying_receipt_is_rejected_downstream(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _verified_non_certifying_receipt(campaign, output_root)
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying=true でない",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=verified,
            generated_from_head="fixed",
            output_root=output_root,
        )


def test_accepted_report_api_has_no_return_code_or_stdout_parameter() -> None:
    import inspect

    parameters = inspect.signature(layer3_report.build_accepted_report).parameters
    assert "acceptance_receipt" in parameters
    assert not ({"rc", "return_code", "stdout"} & set(parameters))


def test_accepted_report_rejects_unsealed_receipt_capability(tmp_path: Path) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _verified_non_certifying_receipt(campaign, output_root)
    forged = dataclasses.replace(verified, _seal=object())
    with pytest.raises(
        layer3_report.Layer3ReportError, match="receipt-capability",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=forged,
            output_root=output_root,
        )


def test_bench_rep_returncodes_passes_real_view_and_schema(tmp_path):
    """M-P10: bench event の新 key が _view_row を経ても実 schema 検証を通る。"""
    campaign, output_root = _campaign(
        tmp_path, [_bench(rep_returncodes=[0, 0, 0, 0, 0])],
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["runs"][0]["rep_returncodes"] == [0, 0, 0, 0, 0]


@pytest.mark.parametrize("state", ["not-json", json.dumps({"whiteboard": {}})])
def test_existing_invalid_loop_state_fails_closed(tmp_path, state):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "loop_state.json").write_text(state, encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_existing_empty_loop_state_keeps_loop_state_provenance(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], whiteboard=[])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["whiteboard"] == []
    assert report["whiteboard_provenance"] == "loop_state"
    assert not any(ref.startswith("wb:") for ref in report["source_refs"])


@pytest.mark.parametrize("provenance", [None, "unknown"])
def test_schema_rejects_missing_or_invalid_whiteboard_provenance(provenance, tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    if provenance is None:
        del report["whiteboard_provenance"]
    else:
        report["whiteboard_provenance"] = provenance
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_relative_and_absolute_campaign_paths_are_byte_identical(tmp_path, monkeypatch):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    monkeypatch.chdir(output_root.parent)
    relative = campaign.relative_to(output_root.parent)
    layer3_report.render(relative, first, generated_from_head="f" * 40, output_root=output_root)
    layer3_report.render(campaign, second, generated_from_head="f" * 40, output_root=output_root)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text())["meta"]["campaign_path"] == relative.as_posix()


def test_unknown_stage_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("unknown-stage")])
    with pytest.raises(layer3_report.Layer3ReportError, match="unknown WAL stage") as exc_info:
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalLineError)


def test_shared_known_session_stage_is_outside_layer3_semantic_subset(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record(model.STAGE_S1_SESSION, event="session-start")],
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="未知の WAL stage"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )


def test_nested_duplicate_wal_key_fails_closed_for_one_reason(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "runs/wal.jsonl").write_bytes(
        b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
        b'"ts":1,"payload":{"genome":"g","src_token":"s",'
        b'"details":{"fitness_tps":1,"fitness_tps":2}}}\n',
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="WAL record が不正") as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalDuplicateKeyError)
    assert "duplicate key" in str(exc_info.value)


@pytest.mark.parametrize(
    ("raw_line", "expected_cause"),
    [
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env","ts":1}\n',
            "missing=['payload']", id="missing-key",
        ),
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
            b'"ts":1,"payload":{},"extra":true}\n',
            "unknown=['extra']", id="unknown-key",
        ),
        pytest.param(
            b'{"variant":"v1","stage":1,"env_tag":"test-env",'
            b'"ts":1,"payload":{}}\n',
            "WAL stage must be a string", id="wrong-type",
        ),
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
            b'"ts":1,"payload":["bad"]}\n',
            "WAL payload must be a JSON object", id="non-object-payload",
        ),
    ],
)
def test_wal_wrapper_preserves_specific_parser_diagnosis(
        tmp_path, raw_line, expected_cause):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "runs/wal.jsonl").write_bytes(raw_line)

    with pytest.raises(layer3_report.Layer3ReportError) as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)

    assert expected_cause in str(exc_info.value)


def test_wal_blank_between_records_uses_shared_strict_contract(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", variant="v1", genome="g", src_token="s"),
        _record("build_start", variant="v2", genome="h", src_token="t"),
    ])
    wal_path = campaign / "runs/wal.jsonl"
    lines = wal_path.read_text(encoding="utf-8").splitlines(keepends=True)
    wal_path.write_text(lines[0] + "\n" + lines[1], encoding="utf-8")

    with pytest.raises(
            layer3_report.Layer3ReportError, match="WAL line must not be empty",
    ) as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalLineError)


@pytest.mark.parametrize("tail_kind", ["complete-json", "multibyte-partial"])
def test_unframed_wal_tail_is_translated_with_framing_cause(tmp_path, tail_kind):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    wal_path = campaign / "runs/wal.jsonl"
    if tail_kind == "complete-json":
        wal_path.write_bytes(wal_path.read_bytes()[:-1])
    else:
        with wal_path.open("ab") as stream:
            stream.write(b'{"variant":"broken-\xe3\x81')

    with pytest.raises(layer3_report.Layer3ReportError, match="WAL framing") as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )

    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalFramingError)


def test_direct_script_starts_with_clean_pythonpath(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(Path(layer3_report.__file__).resolve()), "--help"],
        cwd=tmp_path, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "campaign_dir" in completed.stdout


def test_body_event_omission_is_detected(tmp_path, monkeypatch):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", genome="g", src_token="s"), _bench(),
    ])
    original = layer3_report._variant_rows

    def drop_one(records):
        rows = original(records)
        rows[0]["events"].pop()
        return rows

    monkeypatch.setattr(layer3_report, "_variant_rows", drop_one)
    with pytest.raises(layer3_report.Layer3ReportError, match="report 本体"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)


def test_duplicate_wal_and_whiteboard_fail_closed(tmp_path):
    duplicate = _bench()
    campaign, output_root = _campaign(tmp_path, [duplicate, duplicate])
    with pytest.raises(layer3_report.Layer3ReportError, match="完全重複"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    whiteboard = {"iteration": 1, "direction": "up", "magnitude": "small", "result": "ok", "delta_pct": None}
    campaign, output_root = _campaign(tmp_path / "whiteboard", [_record("build_start", genome="g", src_token="s")], [whiteboard, whiteboard])
    with pytest.raises(layer3_report.Layer3ReportError, match="完全重複"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)


def test_floor_kinds_match_independently_and_classification_records_skips(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    within = {"cv": 0.01, "median": 12.0}
    between = {"max_delta_pct": 2.0}
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4, "saturation": {"records": 100000}, "workload": YCSB,
        "noise_floor": within,
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "between_run": between,
    }), encoding="utf-8")
    (calibration / "frequency.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "frequency_hz": 10,
    }), encoding="utf-8")
    (calibration / "wrong-workload.json").write_text(json.dumps({
        "records": 100000, "threads": 4,
        "workload": {**YCSB, "ycsb_rratio": "95"},
        "noise_floor": {"cv": 0.02},
    }), encoding="utf-8")
    report = layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert report["noise_floor"]["within_run"]["value"] == within
    assert report["noise_floor"]["between_run"]["value"] == between
    for kind in ("within_run", "between_run"):
        assert report["noise_floor"][kind]["provenance"] == "env-record"
        assert report["noise_floor"][kind]["source"]["path"].startswith(
            "env/test-env/calibration/")
        assert report["noise_floor"][kind]["search"] is None

    _, search_details = layer3_report._calibration_floors(
        calibration, 100000, 4, YCSB)
    for kind in ("within_run", "between_run"):
        assert search_details[kind]["skipped_no_floor_block"] == ["frequency.json"]


def test_duplicate_matching_floor_of_same_kind_fails_closed(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    for name, cv in (("first.json", 0.01), ("second.json", 0.02)):
        (calibration / name).write_text(json.dumps({
            "records": 100000, "threads": 4, "workload": YCSB,
            "noise_floor": {"cv": cv},
        }), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="within_run.*複数"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_floor_candidate_without_workload_fails_closed(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    (calibration / "broken.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="workload dict"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_campaign_without_ycsb_has_honest_null_for_both_floor_kinds(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    (calibration / "within.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "between_run": {"max_delta_pct": 2.0},
    }), encoding="utf-8")
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    for kind in ("within_run", "between_run"):
        floor = report["noise_floor"][kind]
        assert floor["value"] is None
        assert floor["provenance"] == "no-matching-env-record"
        assert floor["source"] is None
        assert floor["search"]["campaign_has_no_ycsb"] is True


def test_schema_rejects_inconsistent_floor_result_correlation(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    report["noise_floor"]["within_run"]["search"] = None
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_abort_event_renders_abort_view_and_commit_absent_reject(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", "aborted", genome="g", src_token="s"),
        _record("abort", "aborted", reason="build-error"),
    ])
    out = tmp_path / "report.json"
    report = layer3_report.render(
        campaign, out, generated_from_head="fixed", output_root=output_root)
    assert out.is_file()
    assert report["aborts"] == [{
        "variant": ABORTED_FIXTURE_VARIANT,
        "reason": "build-error",
        "source_ref": report["aborts"][0]["source_ref"],
    }]
    assert report["aborts"][0]["source_ref"] in report["source_refs"]
    assert report["rejects"][0]["variant"] == ABORTED_FIXTURE_VARIANT
    assert report["rejects"][0]["reason"] == "commit-event-absent"


def test_existing_output_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    out = tmp_path / "exists.json"
    out.write_text("already here", encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="既に存在"):
        layer3_report.render(campaign, out, generated_from_head="fixed", output_root=output_root)


def test_variant_without_commit_is_reject_with_primary_reference(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", "rejected", genome="g", src_token="s"), _bench("rejected"),
    ])
    report = layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert report["rejects"][0]["variant"] == REJECTED_FIXTURE_VARIANT
    assert report["rejects"][0]["reason"] == "commit-event-absent"
    assert report["rejects"][0]["source_ref"] in report["source_refs"]


@pytest.mark.parametrize("section", ["variants", "runs", "verifications", "rejects", "aborts", "whiteboard"])
def test_schema_rejects_empty_material_items(section, tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report[section] = [{}]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_git_head_is_real_repository_head():
    head = layer3_report._git_head(ROOT)
    assert len(head) == 40
    assert all(char in "0123456789abcdef" for char in head)


def test_campaign_outside_repo_fails_closed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(layer3_report.Layer3ReportError, match="repo 外"):
        layer3_report.build_report(outside, generated_from_head="fixed")
