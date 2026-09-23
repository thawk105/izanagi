"""Full-structure compatibility guard for the originless bounded trial path."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from orchestrator.campaign import p3_autonomous_workload_trial as A
from orchestrator.tests import test_p3_autonomous_workload_trial as p3_test


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _pin_fixture_commit_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the rebuilt fixture repository's commit identities deterministic."""
    original_git_env = A.trial_registry._git_env

    def deterministic_git_env() -> dict[str, str]:
        env = original_git_env()
        env.update({
            "GIT_AUTHOR_DATE": "2026-08-12T00:00:00+0000",
            "GIT_COMMITTER_DATE": "2026-08-12T00:00:00+0000",
        })
        return env

    monkeypatch.setattr(A.trial_registry, "_git_env", deterministic_git_env)


def _bundle(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    explicit_none: bool,
) -> dict[str, object]:
    root.mkdir(parents=True)
    fixture = p3_test.t325_registered_trial.__wrapped__(root, monkeypatch)
    manifest = A.trial_registry.load_trial_manifest(fixture.manifest_path)
    report_paths: list[Path] = []
    for trial in manifest.trials:
        workload = A.trial_registry.HOLDOUT_BINDINGS[trial.holdout]["workload"]
        run_root = fixture.repo / "output" / "originless" / trial.trial_id
        arguments = dict(
            trial_id=trial.trial_id,
            workloads=[workload],
            generations=2,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            drive=p3_test._fake_drive,
            preview=p3_test._fake_preview,
            trial_manifest=fixture.manifest_path,
            effective_preregistration=fixture.capability,
        )
        if explicit_none:
            arguments.update({
                "origin_binding_request": None,
                "origin_producer_inputs": None,
            })
        report = A.run_trial(**arguments)
        assert report["status"] == "complete"
        report_paths.append(run_root / "report.json")
    summary = A.trial_registry.assert_trial_registry_acceptance(
        effective_preregistration=fixture.capability,
        manifest_path=fixture.manifest_path,
        report_paths=report_paths,
        repository_root=fixture.repo,
        registry_path=fixture.registry_path,
        lifecycle_path=fixture.repo / A.trial_registry.DEFAULT_LIFECYCLE_PATH,
    )
    bundle = {
        "reports": [json.loads(path.read_bytes()) for path in report_paths],
        "journals": [
            [
                json.loads(line)
                for line in path.with_name(
                    "attempts.jsonl"
                ).read_bytes().splitlines()
            ]
            for path in report_paths
        ],
        "lifecycle": [
            json.loads(line)
            for line in (
                fixture.repo / A.trial_registry.DEFAULT_LIFECYCLE_PATH
            ).read_bytes().splitlines()
        ],
        "acceptance": json.loads((fixture.repo / summary.receipt_path).read_bytes()),
    }
    activation_digest = fixture.capability.report_digest_sha256
    assert bundle["acceptance"]["activation_report_digest_sha256"] == (
        activation_digest
    )
    assert all(
        report["launch_admission"]["activation_report_digest_sha256"]
        == activation_digest
        for report in bundle["reports"]
    )
    assert all(
        event["launch_admission"]["activation_report_digest_sha256"]
        == activation_digest
        for journal in bundle["journals"]
        for event in journal
        if event["event"] == "run-start"
    )
    assert all(
        row["activation_report_digest_sha256"] == activation_digest
        for row in bundle["lifecycle"]
        if "activation_report_digest_sha256" in row
    )
    return bundle


def _origin_enabled_bundle(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    """Build the matching origin-enabled G=2 report and journal."""

    root.mkdir(parents=True)
    fixture = p3_test.t325_registered_trial.__wrapped__(root, monkeypatch)
    request, producer = p3_test._origin_public_inputs(root, monkeypatch, fixture)
    run_root = fixture.repo / "output" / "origin-enabled" / fixture.trial_id
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        **p3_test._origin_trial_arguments(fixture, run_root),
    )
    assert type(outcome) is A.OriginCompletedTrialReport
    report = json.loads((run_root / "report.json").read_bytes())
    assert "origin_binding" in report["launch_admission"]
    assert "origin_terminal_projection" in report
    return {
        "reports": [report],
        "journals": [
            [
                json.loads(line)
                for line in (run_root / "attempts.jsonl").read_bytes().splitlines()
            ]
        ],
    }


def _fixed_width_bundle_root(tmp_path: Path, label: str) -> Path:
    prefix = tmp_path / label
    padding = 240 - len(str(prefix)) - 1
    assert padding > 0
    result = prefix / ("x" * padding)
    assert len(str(result)) == 240
    return result


# Each role/journal timestamp is sampled from wall clock at append time.
_VOLATILE_ROLE_TS = ("reports", "*", "cells", "*", "generations", "*", "roles", "*", "ts")
# Raw role paths are absolute descendants of the per-invocation temporary repository.
_VOLATILE_ROLE_PATH = (
    "reports", "*", "cells", "*", "generations", "*", "roles", "*",
    "raw_response_path",
)
# Trial start is sampled from wall clock immediately after run-root creation.
_VOLATILE_REPORT_STARTED = ("reports", "*", "started_at")
# Trial finish is sampled from wall clock after the bounded drive completes.
_VOLATILE_REPORT_FINISHED = ("reports", "*", "finished_at")
# The journal reference is an absolute path beneath the temporary repository.
_VOLATILE_REPORT_JOURNAL_PATH = ("reports", "*", "attempt_journal")
# The journal digest covers wall-clock timestamps and temporary absolute paths.
_VOLATILE_REPORT_JOURNAL_SHA = ("reports", "*", "attempt_journal_sha256")
# Campaign roots are absolute trial-local paths; admission_decision.campaign_path is not excluded.
_VOLATILE_REPORT_CAMPAIGN_ROOT = ("reports", "*", "cells", "*", "campaign_root")
# T-1311 proposal artifacts are absolute descendants of each run root.
_VOLATILE_REPORT_PROPOSAL_PATH = (
    "reports", "*", "cells", "*", "generations", "*", "proposal", "path",
)
# Every journal append independently records its wall-clock timestamp.
_VOLATILE_JOURNAL_TS = ("journals", "*", "*", "ts")
# Role journal rows retain the absolute raw-response artifact path.
_VOLATILE_JOURNAL_ROLE_PATH = ("journals", "*", "*", "raw_response_path")
# The run-finish row retains the absolute terminal report path.
_VOLATILE_JOURNAL_REPORT_PATH = ("journals", "*", "*", "report")
# Lifecycle start records the absolute run root to bind later terminal artifacts.
_VOLATILE_LIFECYCLE_RUN_ROOT = ("lifecycle", "*", "run_root")
# Terminal report digest covers report wall clock and temporary absolute paths.
_VOLATILE_LIFECYCLE_REPORT_SHA = ("lifecycle", "*", "report_sha256")
# Terminal journal digest covers journal wall clock and temporary absolute paths.
_VOLATILE_LIFECYCLE_JOURNAL_SHA = ("lifecycle", "*", "attempt_journal_sha256")
# Acceptance lifecycle digest transitively covers volatile lifecycle leaves above.
_VOLATILE_ACCEPTANCE_LIFECYCLE_SHA = ("acceptance", "lifecycle_prefix_sha256")
_VOLATILE_ACCEPTANCE_LIFECYCLE_BYTES = ("acceptance", "lifecycle_prefix_bytes")
# Acceptance report digests transitively cover volatile report leaves above.
_VOLATILE_ACCEPTANCE_REPORT_SHA = ("acceptance", "trials", "*", "report_sha256")
# Acceptance journal digests transitively cover volatile journal leaves above.
_VOLATILE_ACCEPTANCE_JOURNAL_SHA = ("acceptance", "trials", "*", "attempt_journal_sha256")
# The attempt prefix contains exact start/classification/terminal evidence,
# including wall-clock timestamps, process identity, and report/journal-derived
# digests.  Its receipt binding must remain exact, but its digest and byte count
# are therefore transitively volatile across equivalent harness rebuilds.
_VOLATILE_ACCEPTANCE_ATTEMPT_PREFIX_SHA = (
    "acceptance", "attempt_registry_prefix_sha256",
)
_VOLATILE_ACCEPTANCE_ATTEMPT_PREFIX_BYTES = (
    "acceptance", "attempt_registry_prefix_bytes",
)
# Attempt output digests cover the journal's wall clock and temporary paths.
_VOLATILE_REPORT_RAW_OUTPUT_SHA = ("reports", "*", "raw_output_sha256")
_VOLATILE_LIFECYCLE_CLASSIFICATION_SHA = (
    "lifecycle", "*", "classification_receipt_sha256",
)
_VOLATILE_LIFECYCLE_RAW_OUTPUT_SHA = (
    "lifecycle", "*", "raw_output_sha256",
)
_VOLATILE_LIFECYCLE_PROCESS_IDENTITY = (
    "lifecycle", "*", "process_identity", "*",
)
# T1353's P/C registry identities are commit IDs derived from fixture-repository
# contents; the same binding is copied into each consumer record.
# The observation and schedule digests below are also derived from the changed
# fixture content, rather than from the pre-wave compatibility contract.
_VOLATILE_REPORT_OBSERVATION_SHA = ("reports", "*", "observation_sha256")
_VOLATILE_REPORT_PREREG_CONTENT_COMMIT = (
    "reports", "*", "prereg_content_commit",
)
_VOLATILE_REPORT_PREREG_EFFECTIVE_COMMIT = (
    "reports", "*", "prereg_effective_commit",
)
_VOLATILE_REPORT_ADMISSION_PREREG_CONTENT_COMMIT = (
    "reports", "*", "launch_admission", "prereg_content_commit",
)
_VOLATILE_REPORT_ADMISSION_PREREG_EFFECTIVE_COMMIT = (
    "reports", "*", "launch_admission", "prereg_effective_commit",
)
_VOLATILE_REPORT_BINDING_PREREG_CONTENT_COMMIT = (
    "reports", "*", "launch_admission", "binding", "prereg_content_commit",
)
_VOLATILE_REPORT_BINDING_PREREG_EFFECTIVE_COMMIT = (
    "reports", "*", "launch_admission", "binding", "prereg_effective_commit",
)
_VOLATILE_JOURNAL_PREREG_CONTENT_COMMIT = (
    "journals", "*", "*", "prereg_content_commit",
)
_VOLATILE_JOURNAL_PREREG_EFFECTIVE_COMMIT = (
    "journals", "*", "*", "prereg_effective_commit",
)
_VOLATILE_JOURNAL_ADMISSION_PREREG_CONTENT_COMMIT = (
    "journals", "*", "*", "launch_admission", "prereg_content_commit",
)
_VOLATILE_JOURNAL_ADMISSION_PREREG_EFFECTIVE_COMMIT = (
    "journals", "*", "*", "launch_admission", "prereg_effective_commit",
)
_VOLATILE_JOURNAL_BINDING_PREREG_CONTENT_COMMIT = (
    "journals", "*", "*", "launch_admission", "binding",
    "prereg_content_commit",
)
_VOLATILE_JOURNAL_BINDING_PREREG_EFFECTIVE_COMMIT = (
    "journals", "*", "*", "launch_admission", "binding",
    "prereg_effective_commit",
)
_VOLATILE_LIFECYCLE_TERMINAL_PREREG_COMMIT = (
    "lifecycle", "*", "terminal", "prereg_commit",
)
_VOLATILE_LIFECYCLE_PREREG_CONTENT_COMMIT = (
    "lifecycle", "*", "prereg_content_commit",
)
_VOLATILE_LIFECYCLE_PREREG_EFFECTIVE_COMMIT = (
    "lifecycle", "*", "prereg_effective_commit",
)
_VOLATILE_LIFECYCLE_SCHEDULE_ROW_SHA = (
    "lifecycle", "*", "schedule_row_sha256",
)

_VOLATILE_LEAF_PATHS = frozenset({
    _VOLATILE_ROLE_TS,
    _VOLATILE_ROLE_PATH,
    _VOLATILE_REPORT_STARTED,
    _VOLATILE_REPORT_FINISHED,
    _VOLATILE_REPORT_JOURNAL_PATH,
    _VOLATILE_REPORT_JOURNAL_SHA,
    _VOLATILE_REPORT_CAMPAIGN_ROOT,
    _VOLATILE_REPORT_PROPOSAL_PATH,
    _VOLATILE_JOURNAL_TS,
    _VOLATILE_JOURNAL_ROLE_PATH,
    _VOLATILE_JOURNAL_REPORT_PATH,
    _VOLATILE_LIFECYCLE_RUN_ROOT,
    _VOLATILE_LIFECYCLE_REPORT_SHA,
    _VOLATILE_LIFECYCLE_JOURNAL_SHA,
    _VOLATILE_ACCEPTANCE_LIFECYCLE_SHA,
    _VOLATILE_ACCEPTANCE_LIFECYCLE_BYTES,
    _VOLATILE_ACCEPTANCE_REPORT_SHA,
    _VOLATILE_ACCEPTANCE_JOURNAL_SHA,
    _VOLATILE_ACCEPTANCE_ATTEMPT_PREFIX_SHA,
    _VOLATILE_ACCEPTANCE_ATTEMPT_PREFIX_BYTES,
    _VOLATILE_REPORT_RAW_OUTPUT_SHA,
    _VOLATILE_LIFECYCLE_CLASSIFICATION_SHA,
    _VOLATILE_LIFECYCLE_RAW_OUTPUT_SHA,
    _VOLATILE_LIFECYCLE_PROCESS_IDENTITY,
    _VOLATILE_REPORT_OBSERVATION_SHA,
    _VOLATILE_REPORT_PREREG_CONTENT_COMMIT,
    _VOLATILE_REPORT_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_REPORT_ADMISSION_PREREG_CONTENT_COMMIT,
    _VOLATILE_REPORT_ADMISSION_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_REPORT_BINDING_PREREG_CONTENT_COMMIT,
    _VOLATILE_REPORT_BINDING_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_JOURNAL_PREREG_CONTENT_COMMIT,
    _VOLATILE_JOURNAL_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_JOURNAL_ADMISSION_PREREG_CONTENT_COMMIT,
    _VOLATILE_JOURNAL_ADMISSION_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_JOURNAL_BINDING_PREREG_CONTENT_COMMIT,
    _VOLATILE_JOURNAL_BINDING_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_LIFECYCLE_TERMINAL_PREREG_COMMIT,
    _VOLATILE_LIFECYCLE_PREREG_CONTENT_COMMIT,
    _VOLATILE_LIFECYCLE_PREREG_EFFECTIVE_COMMIT,
    _VOLATILE_LIFECYCLE_SCHEDULE_ROW_SHA,
})

# campaign identity は main の identity contract の進行で変わる値であり、
# 本 wave の originless 不変性とは独立である。
_MAIN_DERIVED_CAMPAIGN_ID_LEAF_PATHS = frozenset({
    ("reports", "*", "launch_admission", "binding", "campaign_id"),
    ("reports", "*", "cells", "*", "campaign_id"),
    ("journals", "*", "*", "launch_admission", "binding", "campaign_id"),
    ("acceptance", "trials", "*", "campaign_id"),
})
# Manifest identity は上の campaign identity を含むため main の進行で変わる値であり、
# 本 wave の originless 不変性とは独立である。
_MAIN_DERIVED_MANIFEST_SHA_LEAF_PATHS = frozenset({
    ("reports", "*", "manifest_sha256"),
    ("reports", "*", "launch_admission", "binding", "manifest_sha256"),
    ("journals", "*", "*", "manifest_sha256"),
    ("journals", "*", "*", "launch_admission", "binding", "manifest_sha256"),
    ("lifecycle", "*", "manifest_sha256"),
    ("acceptance", "manifest_sha256"),
})
# Fixture repository HEAD は manifest / registry commit から決まり main の進行で変わる値であり、
# 本 wave の originless 不変性とは独立である。
_MAIN_DERIVED_MEASUREMENT_HEAD_LEAF_PATHS = frozenset({
    ("reports", "*", "measurement_head"),
    ("reports", "*", "launch_admission", "binding", "measurement_head"),
    ("journals", "*", "*", "measurement_head"),
    ("journals", "*", "*", "launch_admission", "binding", "measurement_head"),
    ("lifecycle", "*", "measurement_head"),
    ("acceptance", "trials", "*", "measurement_head"),
})
# Registry identity と admission digest は上の main-derived 値から導出されて main の進行で
# 変わる値であり、本 wave の originless 不変性とは独立である。
_MAIN_DERIVED_TRANSITIVE_LEAF_PATHS = frozenset({
    ("acceptance", "registry_blob_sha256"),
    ("acceptance", "registry_introduction_commit"),
    ("lifecycle", "*", "launch_admission_sha256"),
})
_MAIN_DERIVED_LEAF_PATHS = frozenset().union(
    _MAIN_DERIVED_CAMPAIGN_ID_LEAF_PATHS,
    _MAIN_DERIVED_MANIFEST_SHA_LEAF_PATHS,
    _MAIN_DERIVED_MEASUREMENT_HEAD_LEAF_PATHS,
    _MAIN_DERIVED_TRANSITIVE_LEAF_PATHS,
)
_MAIN_DERIVED_PLACEHOLDER = "<main-derived>"

# Frozen from the originless output of pre-wave commit 7b6f91a8.  Volatile
# leaves retain their separate structural marker; the closed main-derived set
# is normalized below without removing any key or container structure.
_PRE_WAVE_ORIGINLESS_BASELINE = json.loads(r"""{"$":[[{"dict_keys":["reports","journals","lifecycle","acceptance"]},1]],"acceptance":[[{"dict_keys":["activation_report_digest_sha256","certifying","lifecycle_path","lifecycle_prefix_bytes","lifecycle_prefix_sha256","manifest_path","manifest_sha256","non_certifying_reason_codes","prereg_commit","registry_blob_sha256","registry_introduction_commit","registry_path","schema_version","trials"]},1]],"acceptance/activation_report_digest_sha256":[["3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170",1]],"acceptance/certifying":[[false,1]],"acceptance/lifecycle_path":[["output/s8c-trial-registry/lifecycle.jsonl",1]],"acceptance/lifecycle_prefix_bytes":[[6318,1]],"acceptance/lifecycle_prefix_sha256":[[{"volatile":true},1]],"acceptance/manifest_path":[["manifests/trial.json",1]],"acceptance/manifest_sha256":[["b3a39cac230ec9afb17650206626d965e1417f47e5bd22c99e7858df0b9e0b00",1]],"acceptance/non_certifying_reason_codes":[[{"list_length":2},1]],"acceptance/non_certifying_reason_codes/*":[["c02-arm-binding-unproven",1],["t468-approval-authority-absent",1]],"acceptance/prereg_commit":[["bcb3912d3380451505a2cd5de3138e310dd659b6",1]],"acceptance/registry_blob_sha256":[["2c2325f0d043897069b83b883cb58b2f767c5f34d72d4231fca234e9d85a5d12",1]],"acceptance/registry_introduction_commit":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",1]],"acceptance/registry_path":[["output/s8c-trial-registry/registry.jsonl",1]],"acceptance/schema_version":[["p3-8c-trial-acceptance-receipt/v1",1]],"acceptance/trials":[[{"list_length":6},1]],"acceptance/trials/*":[[{"dict_keys":["arm","attempt_journal_path","attempt_journal_sha256","campaign_id","holdout","measurement_head","report_path","report_sha256","status","trial_id"]},6]],"acceptance/trials/*/arm":[["off",1],["on",1],["swapped",1],["off",1],["on",1],["swapped",1]],"acceptance/trials/*/attempt_journal_path":[["output/originless/t325-h1-off/attempts.jsonl",1],["output/originless/t325-h1-on/attempts.jsonl",1],["output/originless/t325-h1-swapped/attempts.jsonl",1],["output/originless/t325-h2-off/attempts.jsonl",1],["output/originless/t325-h2-on/attempts.jsonl",1],["output/originless/t325-h2-swapped/attempts.jsonl",1]],"acceptance/trials/*/attempt_journal_sha256":[[{"volatile":true},6]],"acceptance/trials/*/campaign_id":[["p3-t178-rr80-workload-conditioned-autonomous-d02c9cd6",1],["p3-t178-rr80-workload-conditioned-autonomous-013e1866",1],["p3-t178-rr80-workload-conditioned-autonomous-30314735",1],["p3-t178-rr20-workload-conditioned-autonomous-025f0c2e",1],["p3-t178-rr20-workload-conditioned-autonomous-64868657",1],["p3-t178-rr20-workload-conditioned-autonomous-ad4063f2",1]],"acceptance/trials/*/holdout":[["H1",3],["H2",3]],"acceptance/trials/*/measurement_head":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",6]],"acceptance/trials/*/report_path":[["output/originless/t325-h1-off/report.json",1],["output/originless/t325-h1-on/report.json",1],["output/originless/t325-h1-swapped/report.json",1],["output/originless/t325-h2-off/report.json",1],["output/originless/t325-h2-on/report.json",1],["output/originless/t325-h2-swapped/report.json",1]],"acceptance/trials/*/report_sha256":[[{"volatile":true},6]],"acceptance/trials/*/status":[["complete",6]],"acceptance/trials/*/trial_id":[["t325-h1-off",1],["t325-h1-on",1],["t325-h1-swapped",1],["t325-h2-off",1],["t325-h2-on",1],["t325-h2-swapped",1]],"journals":[[{"list_length":6},1]],"journals/*":[[{"list_length":6},6]],"journals/*/*":[[{"dict_keys":["do_build","event","generation_budget_per_workload","launch_admission","manifest_sha256","max_wall_s","measurement_head","performance_early_stop","prereg_commit","provider","schema_version","scientific_claim","seq","trial_id","ts","workloads"]},1],[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},4],[{"dict_keys":["event","report","seq","status","ts"]},1],[{"dict_keys":["do_build","event","generation_budget_per_workload","launch_admission","manifest_sha256","max_wall_s","measurement_head","performance_early_stop","prereg_commit","provider","schema_version","scientific_claim","seq","trial_id","ts","workloads"]},1],[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},4],[{"dict_keys":["event","report","seq","status","ts"]},1],[{"dict_keys":["do_build","event","generation_budget_per_workload","launch_admission","manifest_sha256","max_wall_s","measurement_head","performance_early_stop","prereg_commit","provider","schema_version","scientific_claim","seq","trial_id","ts","workloads"]},1],[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},4],[{"dict_keys":["event","report","seq","status","ts"]},1],[{"dict_keys":["do_build","event","generation_budget_per_workload","launch_admission","manifest_sha256","max_wall_s","measurement_head","performance_early_stop","prereg_commit","provider","schema_version","scientific_claim","seq","trial_id","ts","workloads"]},1],[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},4],[{"dict_keys":["event","report","seq","status","ts"]},1],[{"dict_keys":["do_build","event","generation_budget_per_workload","launch_admission","manifest_sha256","max_wall_s","measurement_head","performance_early_stop","prereg_commit","provider","schema_version","scientific_claim","seq","trial_id","ts","workloads"]},1],[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},4],[{"dict_keys":["event","report","seq","status","ts"]},1],[{"dict_keys":["do_build","event","generation_budget_per_workload","launch_admission","manifest_sha256","max_wall_s","measurement_head","performance_early_stop","prereg_commit","provider","schema_version","scientific_claim","seq","trial_id","ts","workloads"]},1],[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},4],[{"dict_keys":["event","report","seq","status","ts"]},1]],"journals/*/*/attempt":[[1,24]],"journals/*/*/declassifications":[[{"list_length":0},2],[{"list_length":1},1],[{"list_length":0},3],[{"list_length":1},1],[{"list_length":0},3],[{"list_length":1},1],[{"list_length":0},3],[{"list_length":1},1],[{"list_length":0},3],[{"list_length":1},1],[{"list_length":0},3],[{"list_length":1},1],[{"list_length":0},1]],"journals/*/*/declassifications/*":[[{"dict_keys":["disclosures","policy_id","policy_sha256"]},6]],"journals/*/*/declassifications/*/disclosures":[[{"list_length":2},6]],"journals/*/*/declassifications/*/disclosures/*":[[{"dict_keys":["json_pointer","transform","value_sha256"]},12]],"journals/*/*/declassifications/*/disclosures/*/json_pointer":[["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1]],"journals/*/*/declassifications/*/disclosures/*/transform":[["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1]],"journals/*/*/declassifications/*/disclosures/*/value_sha256":[["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1]],"journals/*/*/declassifications/*/policy_id":[["t244-auditor-diff-declassification/v1",6]],"journals/*/*/declassifications/*/policy_sha256":[["48ceaddf62ba66577e20e5df958ef7d2f16ac925bf11141e5fd64e8deafdbebc",6]],"journals/*/*/descriptor_sha256":[["06849bef4774cc276de969931b3b95493a8558ccf05e4b3ebe1573d99dcd75d3",12],["0c43da926fb27666351215d103d7db060c6c57f242940a9ab1bd8651cf4a9e86",12]],"journals/*/*/do_build":[[false,6]],"journals/*/*/event":[["run-start",1],["role-attempt",4],["run-finish",1],["run-start",1],["role-attempt",4],["run-finish",1],["run-start",1],["role-attempt",4],["run-finish",1],["run-start",1],["role-attempt",4],["run-finish",1],["run-start",1],["role-attempt",4],["run-finish",1],["run-start",1],["role-attempt",4],["run-finish",1]],"journals/*/*/generation":[[1,24]],"journals/*/*/generation_budget_per_workload":[[1,6]],"journals/*/*/input_payload_sha256":[["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",1],["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",1],["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",1],["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",1],["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",1],["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",1],["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",1],["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",1],["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",1],["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",1],["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",1],["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",1],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",1],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",1],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",1],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",1],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",1],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",1],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",1],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",1],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",1],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",1],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",1],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",1]],"journals/*/*/invocation_id":[["rr80.g1.planner",1],["rr80.g1.coder",1],["rr80.g1.auditor",1],["rr80.g1.critic",1],["rr80.g1.planner",1],["rr80.g1.coder",1],["rr80.g1.auditor",1],["rr80.g1.critic",1],["rr80.g1.planner",1],["rr80.g1.coder",1],["rr80.g1.auditor",1],["rr80.g1.critic",1],["rr20.g1.planner",1],["rr20.g1.coder",1],["rr20.g1.auditor",1],["rr20.g1.critic",1],["rr20.g1.planner",1],["rr20.g1.coder",1],["rr20.g1.auditor",1],["rr20.g1.critic",1],["rr20.g1.planner",1],["rr20.g1.coder",1],["rr20.g1.auditor",1],["rr20.g1.critic",1]],"journals/*/*/launch_admission":[[{"dict_keys":["activation_report_digest_sha256","binding","certifying","mode","reason_code","trial_id","workloads"]},6]],"journals/*/*/launch_admission/activation_report_digest_sha256":[["3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170",6]],"journals/*/*/launch_admission/binding":[[{"dict_keys":["arm","campaign_id","holdout","manifest_sha256","measurement_head","prereg_commit","trial_id","workload","ycsb_rratio"]},6]],"journals/*/*/launch_admission/binding/arm":[["on",1],["off",1],["swapped",1],["on",1],["off",1],["swapped",1]],"journals/*/*/launch_admission/binding/campaign_id":[["p3-t178-rr80-workload-conditioned-autonomous-013e1866",1],["p3-t178-rr80-workload-conditioned-autonomous-d02c9cd6",1],["p3-t178-rr80-workload-conditioned-autonomous-30314735",1],["p3-t178-rr20-workload-conditioned-autonomous-64868657",1],["p3-t178-rr20-workload-conditioned-autonomous-025f0c2e",1],["p3-t178-rr20-workload-conditioned-autonomous-ad4063f2",1]],"journals/*/*/launch_admission/binding/holdout":[["H1",3],["H2",3]],"journals/*/*/launch_admission/binding/manifest_sha256":[["b3a39cac230ec9afb17650206626d965e1417f47e5bd22c99e7858df0b9e0b00",6]],"journals/*/*/launch_admission/binding/measurement_head":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",6]],"journals/*/*/launch_admission/binding/prereg_commit":[["bcb3912d3380451505a2cd5de3138e310dd659b6",6]],"journals/*/*/launch_admission/binding/trial_id":[["t325-h1-on",1],["t325-h1-off",1],["t325-h1-swapped",1],["t325-h2-on",1],["t325-h2-off",1],["t325-h2-swapped",1]],"journals/*/*/launch_admission/binding/workload":[["rr80",3],["rr20",3]],"journals/*/*/launch_admission/binding/ycsb_rratio":[["80",3],["20",3]],"journals/*/*/launch_admission/certifying":[[false,6]],"journals/*/*/launch_admission/mode":[["registered-effective",6]],"journals/*/*/launch_admission/reason_code":[["registered-effective-non-certifying",6]],"journals/*/*/launch_admission/trial_id":[["t325-h1-on",1],["t325-h1-off",1],["t325-h1-swapped",1],["t325-h2-on",1],["t325-h2-off",1],["t325-h2-swapped",1]],"journals/*/*/launch_admission/workloads":[[{"list_length":1},6]],"journals/*/*/launch_admission/workloads/*":[["rr80",3],["rr20",3]],"journals/*/*/manifest_sha256":[["b3a39cac230ec9afb17650206626d965e1417f47e5bd22c99e7858df0b9e0b00",6]],"journals/*/*/max_wall_s":[[3600,6]],"journals/*/*/measurement_head":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",6]],"journals/*/*/parsed":[[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},1],[{"dict_keys":["axis","confidence","justification_present"]},1],[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},1],[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},1],[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},1],[{"dict_keys":["axis","confidence","justification_present"]},1],[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},1],[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},1],[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},1],[{"dict_keys":["axis","confidence","justification_present"]},1],[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},1],[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},1],[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},1],[{"dict_keys":["axis","confidence","justification_present"]},1],[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},1],[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},1],[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},1],[{"dict_keys":["axis","confidence","justification_present"]},1],[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},1],[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},1],[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},1],[{"dict_keys":["axis","confidence","justification_present"]},1],[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},1],[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},1]],"journals/*/*/parsed/attribution":[["fixture has no measured indicators",6]],"journals/*/*/parsed/avoid":[["do not infer performance from dry-run output",6]],"journals/*/*/parsed/axis":[["silo-backoff-trigger-gating",12]],"journals/*/*/parsed/confidence":[["low",6]],"journals/*/*/parsed/diff_digest":[["5d020005a56c56ad05f1be54fed1924e4ea5ca90858c5b12d9e7f7fbdb09fb8c",6]],"journals/*/*/parsed/direction":[["explore_both",6]],"journals/*/*/parsed/justification":[["fixture: descriptor-conditioned wiring proposal",6]],"journals/*/*/parsed/justification_present":[[true,6]],"journals/*/*/parsed/magnitude":[["small",6]],"journals/*/*/parsed/nit_count":[[0,6]],"journals/*/*/parsed/proposed_test_count":[[0,6]],"journals/*/*/parsed/recommend":[["continue the fixed generation schedule",6]],"journals/*/*/parsed/reverse_recommended":[[false,6]],"journals/*/*/parsed/uncertainty":[["fixture output; no scientific inference",1],["all performance metrics are absent",1],["fixture output; no scientific inference",1],["all performance metrics are absent",1],["fixture output; no scientific inference",1],["all performance metrics are absent",1],["fixture output; no scientific inference",1],["all performance metrics are absent",1],["fixture output; no scientific inference",1],["all performance metrics are absent",1],["fixture output; no scientific inference",1],["all performance metrics are absent",1]],"journals/*/*/parsed/uncertainty_present":[[true,6]],"journals/*/*/parsed/verdict":[["pass",6]],"journals/*/*/parsed/violation_codes":[[{"list_length":0},6]],"journals/*/*/performance_early_stop":[[false,6]],"journals/*/*/prereg_commit":[["bcb3912d3380451505a2cd5de3138e310dd659b6",6]],"journals/*/*/provenance":[[{"dict_keys":["child_id","declared_tools","effective_prompt_sha256","fresh_context","model","observed_tool_events","payload_sha256","role_file_sha256","role_name"]},24]],"journals/*/*/provenance/child_id":[["fixture-rr80.g1.planner",1],["fixture-rr80.g1.coder",1],["fixture-rr80.g1.auditor",1],["fixture-rr80.g1.critic",1],["fixture-rr80.g1.planner",1],["fixture-rr80.g1.coder",1],["fixture-rr80.g1.auditor",1],["fixture-rr80.g1.critic",1],["fixture-rr80.g1.planner",1],["fixture-rr80.g1.coder",1],["fixture-rr80.g1.auditor",1],["fixture-rr80.g1.critic",1],["fixture-rr20.g1.planner",1],["fixture-rr20.g1.coder",1],["fixture-rr20.g1.auditor",1],["fixture-rr20.g1.critic",1],["fixture-rr20.g1.planner",1],["fixture-rr20.g1.coder",1],["fixture-rr20.g1.auditor",1],["fixture-rr20.g1.critic",1],["fixture-rr20.g1.planner",1],["fixture-rr20.g1.coder",1],["fixture-rr20.g1.auditor",1],["fixture-rr20.g1.critic",1]],"journals/*/*/provenance/declared_tools":[[{"list_length":0},24]],"journals/*/*/provenance/effective_prompt_sha256":[["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",1],["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",1],["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",1],["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",1],["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",1],["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",1],["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",1],["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",1],["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",1],["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",1],["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",1],["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",1],["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",1],["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",1],["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",1],["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",1],["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",1],["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",1],["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",1],["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",1],["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",1],["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",1],["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",1],["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",1]],"journals/*/*/provenance/fresh_context":[[true,24]],"journals/*/*/provenance/model":[["fixture",24]],"journals/*/*/provenance/observed_tool_events":[[{"list_length":0},24]],"journals/*/*/provenance/payload_sha256":[["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",1],["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",1],["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",1],["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",1],["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",1],["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",1],["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",1],["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",1],["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",1],["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",1],["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",1],["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",1],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",1],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",1],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",1],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",1],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",1],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",1],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",1],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",1],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",1],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",1],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",1],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",1]],"journals/*/*/provenance/role_file_sha256":[["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",1],["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",1],["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",1],["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",1],["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",1],["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",1],["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",1],["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",1],["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",1],["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",1],["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",1],["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",1],["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",1],["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",1],["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",1],["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",1],["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",1],["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",1],["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",1],["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",1],["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",1],["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",1],["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",1],["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",1]],"journals/*/*/provenance/role_name":[["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1]],"journals/*/*/provider":[["fixture",6]],"journals/*/*/raw_response_path":[[{"volatile":true},24]],"journals/*/*/raw_response_sha256":[["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",1],["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",1],["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",1],["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",1],["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",1],["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",1],["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",1],["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",1],["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",1],["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",1],["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",1],["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",1],["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",1],["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",1],["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",1],["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",1],["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",1],["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",1],["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",1],["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",1],["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",1],["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",1],["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",1],["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",1]],"journals/*/*/report":[[{"volatile":true},6]],"journals/*/*/retry":[[false,24]],"journals/*/*/role":[["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1],["planner",1],["coder",1],["auditor",1],["critic",1]],"journals/*/*/schema_version":[["p3-autonomous-workload-trial/v3",6]],"journals/*/*/scientific_claim":[[false,6]],"journals/*/*/seq":[[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[1,1],[2,1],[3,1],[4,1],[5,1],[6,1]],"journals/*/*/status":[["valid",4],["complete",1],["valid",4],["complete",1],["valid",4],["complete",1],["valid",4],["complete",1],["valid",4],["complete",1],["valid",4],["complete",1]],"journals/*/*/trial_id":[["t325-h1-on",1],["t325-h1-off",1],["t325-h1-swapped",1],["t325-h2-on",1],["t325-h2-off",1],["t325-h2-swapped",1]],"journals/*/*/ts":[[{"volatile":true},36]],"journals/*/*/workload":[["rr80",12],["rr20",12]],"journals/*/*/workloads":[[{"list_length":1},6]],"journals/*/*/workloads/*":[["rr80",3],["rr20",3]],"lifecycle":[[{"list_length":12},1]],"lifecycle/*":[[{"dict_keys":["activation_report_digest_sha256","event","launch_admission_sha256","manifest_sha256","measurement_head","mode","run_root","schema_version","trial_id"]},1],[{"dict_keys":["attempt_journal_sha256","event","report_sha256","schema_version","terminal_status","trial_id"]},1],[{"dict_keys":["activation_report_digest_sha256","event","launch_admission_sha256","manifest_sha256","measurement_head","mode","run_root","schema_version","trial_id"]},1],[{"dict_keys":["attempt_journal_sha256","event","report_sha256","schema_version","terminal_status","trial_id"]},1],[{"dict_keys":["activation_report_digest_sha256","event","launch_admission_sha256","manifest_sha256","measurement_head","mode","run_root","schema_version","trial_id"]},1],[{"dict_keys":["attempt_journal_sha256","event","report_sha256","schema_version","terminal_status","trial_id"]},1],[{"dict_keys":["activation_report_digest_sha256","event","launch_admission_sha256","manifest_sha256","measurement_head","mode","run_root","schema_version","trial_id"]},1],[{"dict_keys":["attempt_journal_sha256","event","report_sha256","schema_version","terminal_status","trial_id"]},1],[{"dict_keys":["activation_report_digest_sha256","event","launch_admission_sha256","manifest_sha256","measurement_head","mode","run_root","schema_version","trial_id"]},1],[{"dict_keys":["attempt_journal_sha256","event","report_sha256","schema_version","terminal_status","trial_id"]},1],[{"dict_keys":["activation_report_digest_sha256","event","launch_admission_sha256","manifest_sha256","measurement_head","mode","run_root","schema_version","trial_id"]},1],[{"dict_keys":["attempt_journal_sha256","event","report_sha256","schema_version","terminal_status","trial_id"]},1]],"lifecycle/*/activation_report_digest_sha256":[["3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170",6]],"lifecycle/*/attempt_journal_sha256":[[{"volatile":true},6]],"lifecycle/*/event":[["start",1],["terminal",1],["start",1],["terminal",1],["start",1],["terminal",1],["start",1],["terminal",1],["start",1],["terminal",1],["start",1],["terminal",1]],"lifecycle/*/launch_admission_sha256":[["ada51a71704097a2636837533681d4adf32283b2a3ae6f0a2d97c821577da944",1],["47e5797d057a0d7c07780ffeb8279c047e1401bf7913e23c4442cf429a71317e",1],["6834dc76e994ec886bef32d0917abadf710d1f390a8c71f5a05f013ef7c7637c",1],["761c0456aade865de9383a447c7e968798d5ad3814eba818c5fa92f33c7de867",1],["612b8fbef28bb223948639f0e3341922342dba86eeef7126055a7cadfe2ddaa2",1],["c255fcac60188e2b302823aa0760e772864f378de685364a26824236da6a2543",1]],"lifecycle/*/manifest_sha256":[["b3a39cac230ec9afb17650206626d965e1417f47e5bd22c99e7858df0b9e0b00",6]],"lifecycle/*/measurement_head":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",6]],"lifecycle/*/mode":[["registered-effective",6]],"lifecycle/*/report_sha256":[[{"volatile":true},6]],"lifecycle/*/run_root":[[{"volatile":true},6]],"lifecycle/*/schema_version":[["p3-8c-trial-lifecycle/v1",12]],"lifecycle/*/terminal_status":[["complete",6]],"lifecycle/*/trial_id":[["t325-h1-on",2],["t325-h1-off",2],["t325-h1-swapped",2],["t325-h2-on",2],["t325-h2-off",2],["t325-h2-swapped",2]],"reports":[[{"list_length":6},1]],"reports/*":[[{"dict_keys":["attempt_journal","attempt_journal_sha256","cells","claim_scope","do_build","finished_at","generation_budget_per_workload","launch_admission","manifest_sha256","measurement_head","prereg_commit","provider","schema_version","started_at","status","stop_policy","trial_id","workloads_requested"]},6]],"reports/*/attempt_journal":[[{"volatile":true},6]],"reports/*/attempt_journal_sha256":[[{"volatile":true},6]],"reports/*/cells":[[{"list_length":1},6]],"reports/*/cells/*":[[{"dict_keys":["admission_decision","campaign_id","campaign_root","descriptor","descriptor_binding","generations","stop_reason","workload","workload_flags"]},6]],"reports/*/cells/*/admission_decision":[[{"dict_keys":["admission_status"]},6]],"reports/*/cells/*/admission_decision/admission_status":[["not-applicable",6]],"reports/*/cells/*/campaign_id":[["p3-t178-rr80-workload-conditioned-autonomous-013e1866",1],["p3-t178-rr80-workload-conditioned-autonomous-d02c9cd6",1],["p3-t178-rr80-workload-conditioned-autonomous-30314735",1],["p3-t178-rr20-workload-conditioned-autonomous-64868657",1],["p3-t178-rr20-workload-conditioned-autonomous-025f0c2e",1],["p3-t178-rr20-workload-conditioned-autonomous-ad4063f2",1]],"reports/*/cells/*/campaign_root":[[{"volatile":true},6]],"reports/*/cells/*/descriptor":[[{"dict_keys":["contention","correctness","objective","read_write","scale","schema_version","source"]},6]],"reports/*/cells/*/descriptor/contention":[[{"dict_keys":["label","skew"]},6]],"reports/*/cells/*/descriptor/contention/label":[["high",6]],"reports/*/cells/*/descriptor/contention/skew":[[0.9,6]],"reports/*/cells/*/descriptor/correctness":[["serializable_legacy_and_s2",6]],"reports/*/cells/*/descriptor/objective":[["maximize_throughput_tps",6]],"reports/*/cells/*/descriptor/read_write":[[{"dict_keys":["read_ratio_percent","rmw"]},6]],"reports/*/cells/*/descriptor/read_write/read_ratio_percent":[[80,3],[20,3]],"reports/*/cells/*/descriptor/read_write/rmw":[[0,6]],"reports/*/cells/*/descriptor/scale":[[{"dict_keys":["records","threads"]},6]],"reports/*/cells/*/descriptor/scale/records":[[100000,6]],"reports/*/cells/*/descriptor/scale/threads":[[4,6]],"reports/*/cells/*/descriptor/schema_version":[["8b-v1",6]],"reports/*/cells/*/descriptor/source":[["campaign_search_config_projection",6]],"reports/*/cells/*/descriptor_binding":[[{"dict_keys":["input_sha256","output_sha256","projection_version","schema_sha256"]},6]],"reports/*/cells/*/descriptor_binding/input_sha256":[["f4df0a972780cdc7330a261c9c7745c86f45a5b370fcd6d06d713a5a80e22eab",3],["a29b1eec6c7b1f55bef9a4dbd936ae081986ac6535a00b4d45c8d526207b8843",3]],"reports/*/cells/*/descriptor_binding/output_sha256":[["06849bef4774cc276de969931b3b95493a8558ccf05e4b3ebe1573d99dcd75d3",3],["0c43da926fb27666351215d103d7db060c6c57f242940a9ab1bd8651cf4a9e86",3]],"reports/*/cells/*/descriptor_binding/projection_version":[["8b-descriptor-projection/v1",6]],"reports/*/cells/*/descriptor_binding/schema_sha256":[["5a9e2696b8fba18f8f7cf01183673a1bd6f5781cc9cb1fe8641f9d667fe11549",6]],"reports/*/cells/*/generations":[[{"list_length":1},6]],"reports/*/cells/*/generations/*":[[{"dict_keys":["generation","harness","outcome","preview","roles"]},6]],"reports/*/cells/*/generations/*/generation":[[1,6]],"reports/*/cells/*/generations/*/harness":[[{"dict_keys":["critic_digest_generated","iteration","outcome","ran","stop_reason","trigger_gate_binding_commitment","variant"]},6]],"reports/*/cells/*/generations/*/harness/critic_digest_generated":[[false,6]],"reports/*/cells/*/generations/*/harness/iteration":[[1,6]],"reports/*/cells/*/generations/*/harness/outcome":[["dry-pass",6]],"reports/*/cells/*/generations/*/harness/ran":[[true,6]],"reports/*/cells/*/generations/*/harness/stop_reason":[["continue",6]],"reports/*/cells/*/generations/*/harness/trigger_gate_binding_commitment":[["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",6]],"reports/*/cells/*/generations/*/harness/variant":[[null,6]],"reports/*/cells/*/generations/*/outcome":[["dry-pass",6]],"reports/*/cells/*/generations/*/preview":[[{"dict_keys":["diff_digest","forbidden_identifiers","passed","reason","subtype"]},6]],"reports/*/cells/*/generations/*/preview/diff_digest":[["5d020005a56c56ad05f1be54fed1924e4ea5ca90858c5b12d9e7f7fbdb09fb8c",6]],"reports/*/cells/*/generations/*/preview/forbidden_identifiers":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/preview/passed":[[true,6]],"reports/*/cells/*/generations/*/preview/reason":[["",6]],"reports/*/cells/*/generations/*/preview/subtype":[[null,6]],"reports/*/cells/*/generations/*/roles":[[{"dict_keys":["auditor","coder","critic","planner"]},6]],"reports/*/cells/*/generations/*/roles/auditor":[[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},6]],"reports/*/cells/*/generations/*/roles/auditor/attempt":[[1,6]],"reports/*/cells/*/generations/*/roles/auditor/declassifications":[[{"list_length":1},6]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*":[[{"dict_keys":["disclosures","policy_id","policy_sha256"]},6]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/disclosures":[[{"list_length":2},6]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/disclosures/*":[[{"dict_keys":["json_pointer","transform","value_sha256"]},12]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/disclosures/*/json_pointer":[["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1],["/working_diff",1],["/diff_digest",1]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/disclosures/*/transform":[["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1],["identity",1],["sha256-hex-of-/working_diff",1]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/disclosures/*/value_sha256":[["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1],["752a40c45422221f05718d06389e15a4f757db13c41cccd4030f452935c21861",1],["e7cbd8e04105245b03bd1f065d907dfd6a851ffe8506e01b3045a98865e60fa8",1]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/policy_id":[["t244-auditor-diff-declassification/v1",6]],"reports/*/cells/*/generations/*/roles/auditor/declassifications/*/policy_sha256":[["48ceaddf62ba66577e20e5df958ef7d2f16ac925bf11141e5fd64e8deafdbebc",6]],"reports/*/cells/*/generations/*/roles/auditor/descriptor_sha256":[["06849bef4774cc276de969931b3b95493a8558ccf05e4b3ebe1573d99dcd75d3",3],["0c43da926fb27666351215d103d7db060c6c57f242940a9ab1bd8651cf4a9e86",3]],"reports/*/cells/*/generations/*/roles/auditor/event":[["role-attempt",6]],"reports/*/cells/*/generations/*/roles/auditor/generation":[[1,6]],"reports/*/cells/*/generations/*/roles/auditor/input_payload_sha256":[["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",3],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",3]],"reports/*/cells/*/generations/*/roles/auditor/invocation_id":[["rr80.g1.auditor",3],["rr20.g1.auditor",3]],"reports/*/cells/*/generations/*/roles/auditor/parsed":[[{"dict_keys":["diff_digest","nit_count","proposed_test_count","uncertainty_present","verdict","violation_codes"]},6]],"reports/*/cells/*/generations/*/roles/auditor/parsed/diff_digest":[["5d020005a56c56ad05f1be54fed1924e4ea5ca90858c5b12d9e7f7fbdb09fb8c",6]],"reports/*/cells/*/generations/*/roles/auditor/parsed/nit_count":[[0,6]],"reports/*/cells/*/generations/*/roles/auditor/parsed/proposed_test_count":[[0,6]],"reports/*/cells/*/generations/*/roles/auditor/parsed/uncertainty_present":[[true,6]],"reports/*/cells/*/generations/*/roles/auditor/parsed/verdict":[["pass",6]],"reports/*/cells/*/generations/*/roles/auditor/parsed/violation_codes":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/auditor/provenance":[[{"dict_keys":["child_id","declared_tools","effective_prompt_sha256","fresh_context","model","observed_tool_events","payload_sha256","role_file_sha256","role_name"]},6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/child_id":[["fixture-rr80.g1.auditor",3],["fixture-rr20.g1.auditor",3]],"reports/*/cells/*/generations/*/roles/auditor/provenance/declared_tools":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/effective_prompt_sha256":[["b9bbc39512b9dd98eca920650e8754265abbcb00295263102ba62dadf23f2da8",6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/fresh_context":[[true,6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/model":[["fixture",6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/observed_tool_events":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/payload_sha256":[["08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",3],["2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",3]],"reports/*/cells/*/generations/*/roles/auditor/provenance/role_file_sha256":[["e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e",6]],"reports/*/cells/*/generations/*/roles/auditor/provenance/role_name":[["auditor",6]],"reports/*/cells/*/generations/*/roles/auditor/raw_response_path":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/auditor/raw_response_sha256":[["ab543c845ffcb014f8e0aa1fa311963065f45bf897d98986f3abf383615e8475",6]],"reports/*/cells/*/generations/*/roles/auditor/retry":[[false,6]],"reports/*/cells/*/generations/*/roles/auditor/role":[["auditor",6]],"reports/*/cells/*/generations/*/roles/auditor/seq":[[4,6]],"reports/*/cells/*/generations/*/roles/auditor/status":[["valid",6]],"reports/*/cells/*/generations/*/roles/auditor/ts":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/auditor/workload":[["rr80",3],["rr20",3]],"reports/*/cells/*/generations/*/roles/coder":[[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},6]],"reports/*/cells/*/generations/*/roles/coder/attempt":[[1,6]],"reports/*/cells/*/generations/*/roles/coder/declassifications":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/coder/descriptor_sha256":[["06849bef4774cc276de969931b3b95493a8558ccf05e4b3ebe1573d99dcd75d3",3],["0c43da926fb27666351215d103d7db060c6c57f242940a9ab1bd8651cf4a9e86",3]],"reports/*/cells/*/generations/*/roles/coder/event":[["role-attempt",6]],"reports/*/cells/*/generations/*/roles/coder/generation":[[1,6]],"reports/*/cells/*/generations/*/roles/coder/input_payload_sha256":[["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",3],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",3]],"reports/*/cells/*/generations/*/roles/coder/invocation_id":[["rr80.g1.coder",3],["rr20.g1.coder",3]],"reports/*/cells/*/generations/*/roles/coder/parsed":[[{"dict_keys":["axis","confidence","justification_present"]},6]],"reports/*/cells/*/generations/*/roles/coder/parsed/axis":[["silo-backoff-trigger-gating",6]],"reports/*/cells/*/generations/*/roles/coder/parsed/confidence":[["low",6]],"reports/*/cells/*/generations/*/roles/coder/parsed/justification_present":[[true,6]],"reports/*/cells/*/generations/*/roles/coder/provenance":[[{"dict_keys":["child_id","declared_tools","effective_prompt_sha256","fresh_context","model","observed_tool_events","payload_sha256","role_file_sha256","role_name"]},6]],"reports/*/cells/*/generations/*/roles/coder/provenance/child_id":[["fixture-rr80.g1.coder",3],["fixture-rr20.g1.coder",3]],"reports/*/cells/*/generations/*/roles/coder/provenance/declared_tools":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/coder/provenance/effective_prompt_sha256":[["87e82cb7989e3835934ea24054a7aa38addea4170e62386fd4705ff4c70b8f74",6]],"reports/*/cells/*/generations/*/roles/coder/provenance/fresh_context":[[true,6]],"reports/*/cells/*/generations/*/roles/coder/provenance/model":[["fixture",6]],"reports/*/cells/*/generations/*/roles/coder/provenance/observed_tool_events":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/coder/provenance/payload_sha256":[["5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",3],["ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",3]],"reports/*/cells/*/generations/*/roles/coder/provenance/role_file_sha256":[["a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0",6]],"reports/*/cells/*/generations/*/roles/coder/provenance/role_name":[["coder",6]],"reports/*/cells/*/generations/*/roles/coder/raw_response_path":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/coder/raw_response_sha256":[["04cc962ce8a5a089e675f742c257d70432485974d72fa25ab7e5cf14d15479ae",6]],"reports/*/cells/*/generations/*/roles/coder/retry":[[false,6]],"reports/*/cells/*/generations/*/roles/coder/role":[["coder",6]],"reports/*/cells/*/generations/*/roles/coder/seq":[[3,6]],"reports/*/cells/*/generations/*/roles/coder/status":[["valid",6]],"reports/*/cells/*/generations/*/roles/coder/ts":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/coder/workload":[["rr80",3],["rr20",3]],"reports/*/cells/*/generations/*/roles/critic":[[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},6]],"reports/*/cells/*/generations/*/roles/critic/attempt":[[1,6]],"reports/*/cells/*/generations/*/roles/critic/declassifications":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/critic/descriptor_sha256":[["06849bef4774cc276de969931b3b95493a8558ccf05e4b3ebe1573d99dcd75d3",3],["0c43da926fb27666351215d103d7db060c6c57f242940a9ab1bd8651cf4a9e86",3]],"reports/*/cells/*/generations/*/roles/critic/event":[["role-attempt",6]],"reports/*/cells/*/generations/*/roles/critic/generation":[[1,6]],"reports/*/cells/*/generations/*/roles/critic/input_payload_sha256":[["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",3],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",3]],"reports/*/cells/*/generations/*/roles/critic/invocation_id":[["rr80.g1.critic",3],["rr20.g1.critic",3]],"reports/*/cells/*/generations/*/roles/critic/parsed":[[{"dict_keys":["attribution","avoid","recommend","reverse_recommended","uncertainty"]},6]],"reports/*/cells/*/generations/*/roles/critic/parsed/attribution":[["fixture has no measured indicators",6]],"reports/*/cells/*/generations/*/roles/critic/parsed/avoid":[["do not infer performance from dry-run output",6]],"reports/*/cells/*/generations/*/roles/critic/parsed/recommend":[["continue the fixed generation schedule",6]],"reports/*/cells/*/generations/*/roles/critic/parsed/reverse_recommended":[[false,6]],"reports/*/cells/*/generations/*/roles/critic/parsed/uncertainty":[["all performance metrics are absent",6]],"reports/*/cells/*/generations/*/roles/critic/provenance":[[{"dict_keys":["child_id","declared_tools","effective_prompt_sha256","fresh_context","model","observed_tool_events","payload_sha256","role_file_sha256","role_name"]},6]],"reports/*/cells/*/generations/*/roles/critic/provenance/child_id":[["fixture-rr80.g1.critic",3],["fixture-rr20.g1.critic",3]],"reports/*/cells/*/generations/*/roles/critic/provenance/declared_tools":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/critic/provenance/effective_prompt_sha256":[["8bf9e75bcef797d589f8b402c25f43dea658d405359bda71abba60c5127e735e",6]],"reports/*/cells/*/generations/*/roles/critic/provenance/fresh_context":[[true,6]],"reports/*/cells/*/generations/*/roles/critic/provenance/model":[["fixture",6]],"reports/*/cells/*/generations/*/roles/critic/provenance/observed_tool_events":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/critic/provenance/payload_sha256":[["150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",3],["b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",3]],"reports/*/cells/*/generations/*/roles/critic/provenance/role_file_sha256":[["cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",6]],"reports/*/cells/*/generations/*/roles/critic/provenance/role_name":[["critic",6]],"reports/*/cells/*/generations/*/roles/critic/raw_response_path":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/critic/raw_response_sha256":[["5cfab197df7ccf0503a276257751c6057e6d2cd7a58e280948b85b7a43cf2fe3",6]],"reports/*/cells/*/generations/*/roles/critic/retry":[[false,6]],"reports/*/cells/*/generations/*/roles/critic/role":[["critic",6]],"reports/*/cells/*/generations/*/roles/critic/seq":[[5,6]],"reports/*/cells/*/generations/*/roles/critic/status":[["valid",6]],"reports/*/cells/*/generations/*/roles/critic/ts":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/critic/workload":[["rr80",3],["rr20",3]],"reports/*/cells/*/generations/*/roles/planner":[[{"dict_keys":["attempt","declassifications","descriptor_sha256","event","generation","input_payload_sha256","invocation_id","parsed","provenance","raw_response_path","raw_response_sha256","retry","role","seq","status","ts","workload"]},6]],"reports/*/cells/*/generations/*/roles/planner/attempt":[[1,6]],"reports/*/cells/*/generations/*/roles/planner/declassifications":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/planner/descriptor_sha256":[["06849bef4774cc276de969931b3b95493a8558ccf05e4b3ebe1573d99dcd75d3",3],["0c43da926fb27666351215d103d7db060c6c57f242940a9ab1bd8651cf4a9e86",3]],"reports/*/cells/*/generations/*/roles/planner/event":[["role-attempt",6]],"reports/*/cells/*/generations/*/roles/planner/generation":[[1,6]],"reports/*/cells/*/generations/*/roles/planner/input_payload_sha256":[["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",3],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",3]],"reports/*/cells/*/generations/*/roles/planner/invocation_id":[["rr80.g1.planner",3],["rr20.g1.planner",3]],"reports/*/cells/*/generations/*/roles/planner/parsed":[[{"dict_keys":["axis","direction","justification","magnitude","uncertainty"]},6]],"reports/*/cells/*/generations/*/roles/planner/parsed/axis":[["silo-backoff-trigger-gating",6]],"reports/*/cells/*/generations/*/roles/planner/parsed/direction":[["explore_both",6]],"reports/*/cells/*/generations/*/roles/planner/parsed/justification":[["fixture: descriptor-conditioned wiring proposal",6]],"reports/*/cells/*/generations/*/roles/planner/parsed/magnitude":[["small",6]],"reports/*/cells/*/generations/*/roles/planner/parsed/uncertainty":[["fixture output; no scientific inference",6]],"reports/*/cells/*/generations/*/roles/planner/provenance":[[{"dict_keys":["child_id","declared_tools","effective_prompt_sha256","fresh_context","model","observed_tool_events","payload_sha256","role_file_sha256","role_name"]},6]],"reports/*/cells/*/generations/*/roles/planner/provenance/child_id":[["fixture-rr80.g1.planner",3],["fixture-rr20.g1.planner",3]],"reports/*/cells/*/generations/*/roles/planner/provenance/declared_tools":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/planner/provenance/effective_prompt_sha256":[["f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",6]],"reports/*/cells/*/generations/*/roles/planner/provenance/fresh_context":[[true,6]],"reports/*/cells/*/generations/*/roles/planner/provenance/model":[["fixture",6]],"reports/*/cells/*/generations/*/roles/planner/provenance/observed_tool_events":[[{"list_length":0},6]],"reports/*/cells/*/generations/*/roles/planner/provenance/payload_sha256":[["e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",3],["95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",3]],"reports/*/cells/*/generations/*/roles/planner/provenance/role_file_sha256":[["0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e",6]],"reports/*/cells/*/generations/*/roles/planner/provenance/role_name":[["planner",6]],"reports/*/cells/*/generations/*/roles/planner/raw_response_path":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/planner/raw_response_sha256":[["a7573907c2b76a2cec2cde107f15b971d8f015d00e1167b41a079bb4d8966d39",6]],"reports/*/cells/*/generations/*/roles/planner/retry":[[false,6]],"reports/*/cells/*/generations/*/roles/planner/role":[["planner",6]],"reports/*/cells/*/generations/*/roles/planner/seq":[[2,6]],"reports/*/cells/*/generations/*/roles/planner/status":[["valid",6]],"reports/*/cells/*/generations/*/roles/planner/ts":[[{"volatile":true},6]],"reports/*/cells/*/generations/*/roles/planner/workload":[["rr80",3],["rr20",3]],"reports/*/cells/*/stop_reason":[["fixed-generation-budget",6]],"reports/*/cells/*/workload":[["rr80",3],["rr20",3]],"reports/*/cells/*/workload_flags":[[{"dict_keys":["ycsb_rmw","ycsb_rratio","ycsb_zipf_skew"]},6]],"reports/*/cells/*/workload_flags/ycsb_rmw":[["0",6]],"reports/*/cells/*/workload_flags/ycsb_rratio":[["80",3],["20",3]],"reports/*/cells/*/workload_flags/ycsb_zipf_skew":[["0.9",6]],"reports/*/claim_scope":[[{"dict_keys":["formal_followup","known_workload_warning","label","scientific_claim"]},6]],"reports/*/claim_scope/formal_followup":[["H1 rr80 / H2 rr20 x on/off/swapped",6]],"reports/*/claim_scope/known_workload_warning":[["YCSB A/B are known rr50/rr95 points; YCSB C is an exploratory read-only negative-control candidate.",6]],"reports/*/claim_scope/label":[["exploratory wiring pilot",6]],"reports/*/claim_scope/scientific_claim":[[false,6]],"reports/*/do_build":[[false,6]],"reports/*/finished_at":[[{"volatile":true},6]],"reports/*/generation_budget_per_workload":[[1,6]],"reports/*/launch_admission":[[{"dict_keys":["activation_report_digest_sha256","binding","certifying","mode","reason_code","trial_id","workloads"]},6]],"reports/*/launch_admission/activation_report_digest_sha256":[["3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170",6]],"reports/*/launch_admission/binding":[[{"dict_keys":["arm","campaign_id","holdout","manifest_sha256","measurement_head","prereg_commit","trial_id","workload","ycsb_rratio"]},6]],"reports/*/launch_admission/binding/arm":[["on",1],["off",1],["swapped",1],["on",1],["off",1],["swapped",1]],"reports/*/launch_admission/binding/campaign_id":[["p3-t178-rr80-workload-conditioned-autonomous-013e1866",1],["p3-t178-rr80-workload-conditioned-autonomous-d02c9cd6",1],["p3-t178-rr80-workload-conditioned-autonomous-30314735",1],["p3-t178-rr20-workload-conditioned-autonomous-64868657",1],["p3-t178-rr20-workload-conditioned-autonomous-025f0c2e",1],["p3-t178-rr20-workload-conditioned-autonomous-ad4063f2",1]],"reports/*/launch_admission/binding/holdout":[["H1",3],["H2",3]],"reports/*/launch_admission/binding/manifest_sha256":[["b3a39cac230ec9afb17650206626d965e1417f47e5bd22c99e7858df0b9e0b00",6]],"reports/*/launch_admission/binding/measurement_head":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",6]],"reports/*/launch_admission/binding/prereg_commit":[["bcb3912d3380451505a2cd5de3138e310dd659b6",6]],"reports/*/launch_admission/binding/trial_id":[["t325-h1-on",1],["t325-h1-off",1],["t325-h1-swapped",1],["t325-h2-on",1],["t325-h2-off",1],["t325-h2-swapped",1]],"reports/*/launch_admission/binding/workload":[["rr80",3],["rr20",3]],"reports/*/launch_admission/binding/ycsb_rratio":[["80",3],["20",3]],"reports/*/launch_admission/certifying":[[false,6]],"reports/*/launch_admission/mode":[["registered-effective",6]],"reports/*/launch_admission/reason_code":[["registered-effective-non-certifying",6]],"reports/*/launch_admission/trial_id":[["t325-h1-on",1],["t325-h1-off",1],["t325-h1-swapped",1],["t325-h2-on",1],["t325-h2-off",1],["t325-h2-swapped",1]],"reports/*/launch_admission/workloads":[[{"list_length":1},6]],"reports/*/launch_admission/workloads/*":[["rr80",3],["rr20",3]],"reports/*/manifest_sha256":[["b3a39cac230ec9afb17650206626d965e1417f47e5bd22c99e7858df0b9e0b00",6]],"reports/*/measurement_head":[["ec4efa2a8030fd853f67059f136d41f0d34aebd9",6]],"reports/*/prereg_commit":[["bcb3912d3380451505a2cd5de3138e310dd659b6",6]],"reports/*/provider":[["fixture",6]],"reports/*/schema_version":[["p3-autonomous-workload-trial-report/v2",6]],"reports/*/started_at":[[{"volatile":true},6]],"reports/*/status":[["complete",6]],"reports/*/stop_policy":[[{"dict_keys":["fixed_generations","max_wall_s","performance_early_stop"]},6]],"reports/*/stop_policy/fixed_generations":[[true,6]],"reports/*/stop_policy/max_wall_s":[[3600,6]],"reports/*/stop_policy/performance_early_stop":[[false,6]],"reports/*/trial_id":[["t325-h1-on",1],["t325-h1-off",1],["t325-h1-swapped",1],["t325-h2-on",1],["t325-h2-off",1],["t325-h2-swapped",1]],"reports/*/workloads_requested":[[{"list_length":1},6]],"reports/*/workloads_requested/*":[["rr80",3],["rr20",3]]}""")

def _volatile(path: tuple[object, ...]) -> bool:
    return any(
        len(pattern) == len(path)
        and all(expected == "*" or expected == actual for expected, actual in zip(pattern, path))
        for pattern in _VOLATILE_LEAF_PATHS
    )


def _normalize_main_derived_leaves(
    structure: dict[str, list[list[object]]],
) -> dict[str, list[list[object]]]:
    """Keep each main-derived leaf path and cardinality while masking its value."""
    normalized = copy.deepcopy(structure)
    for pattern in _MAIN_DERIVED_LEAF_PATHS:
        path = "/".join(pattern)
        assert path in normalized, path
        runs = normalized[path]
        assert runs, path
        count = 0
        for run in runs:
            assert len(run) == 2 and type(run[1]) is int and run[1] > 0, path
            count += run[1]
        normalized[path] = [[_MAIN_DERIVED_PLACEHOLDER, count]]
    return normalized


_PRE_WAVE_ORIGINLESS_BASELINE = _normalize_main_derived_leaves(
    _PRE_WAVE_ORIGINLESS_BASELINE
)


def _extend_t1353_originless_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Freeze the required registry/receipt fields introduced by T1353.

    The observed prefix byte count changes across executions (11364, 11352,
    and 11358), and the neighboring `acceptance/lifecycle_prefix_sha256`
    leaf is already volatile, so this leaf remains volatile.
    """

    def set_keys(path: str, keys: list[str]) -> None:
        for run in baseline[path]:
            assert type(run[0]) is dict
            run[0]["dict_keys"] = list(keys)

    def set_value(path: str, value: object, count: int) -> None:
        baseline[path] = [[value, count]]

    set_keys("reports/*", [
        "attempt_journal", "attempt_journal_sha256", "cells", "claim_scope",
        "do_build", "finished_at", "generation_budget_per_workload",
        "launch_admission", "manifest_sha256", "measurement_head",
        "observation_sha256", "prereg_commit", "prereg_content_commit",
        "prereg_effective_commit", "primary_value", "provider",
        "raw_output_sha256", "schema_version", "slot_id", "started_at",
        "status", "stop_policy", "trial_id", "workloads_requested",
    ])
    set_keys("reports/*/launch_admission", [
        "activation_report_digest_sha256", "binding", "certifying", "mode",
        "prereg_content_commit", "prereg_effective_commit", "reason_code",
        "trial_id", "workloads",
    ])
    set_keys("reports/*/launch_admission/binding", [
        "arm", "campaign_id", "holdout", "manifest_sha256",
        "measurement_head", "prereg_commit", "prereg_content_commit",
        "prereg_effective_commit", "trial_id", "workload", "ycsb_rratio",
    ])
    baseline["reports/*/observation_sha256"] = [
        [{"volatile": True}, 6],
    ]
    set_value(
        "reports/*/prereg_content_commit",
        {"volatile": True},
        6,
    )
    set_value(
        "reports/*/prereg_effective_commit",
        {"volatile": True},
        6,
    )
    set_value("reports/*/primary_value", 0.0, 6)
    set_value("reports/*/raw_output_sha256", {"volatile": True}, 6)
    baseline["reports/*/slot_id"] = [
        ["t325-h1-on-r0-a0", 1], ["t325-h1-off-r0-a0", 1],
        ["t325-h1-swapped-r0-a0", 1], ["t325-h2-on-r0-a0", 1],
        ["t325-h2-off-r0-a0", 1], ["t325-h2-swapped-r0-a0", 1],
    ]
    for path in (
        "reports/*/launch_admission/prereg_content_commit",
        "reports/*/launch_admission/prereg_effective_commit",
        "reports/*/launch_admission/binding/prereg_content_commit",
        "reports/*/launch_admission/binding/prereg_effective_commit",
    ):
        set_value(path, {"volatile": True}, 6)

    journal_runs = baseline["journals/*/*"]
    run_start_keys = [
        "do_build", "event", "generation_budget_per_workload",
        "launch_admission", "manifest_sha256", "max_wall_s",
        "measurement_head", "performance_early_stop", "prereg_commit",
        "prereg_content_commit", "prereg_effective_commit", "provider",
        "schema_version", "scientific_claim", "seq", "slot_id", "trial_id",
        "ts", "workloads",
    ]
    for index in range(0, len(journal_runs), 3):
        journal_runs[index][0]["dict_keys"] = list(run_start_keys)
    set_keys("journals/*/*/launch_admission", [
        "activation_report_digest_sha256", "binding", "certifying", "mode",
        "prereg_content_commit", "prereg_effective_commit", "reason_code",
        "trial_id", "workloads",
    ])
    set_keys("journals/*/*/launch_admission/binding", [
        "arm", "campaign_id", "holdout", "manifest_sha256",
        "measurement_head", "prereg_commit", "prereg_content_commit",
        "prereg_effective_commit", "trial_id", "workload", "ycsb_rratio",
    ])
    set_value(
        "journals/*/*/prereg_content_commit",
        {"volatile": True},
        6,
    )
    set_value(
        "journals/*/*/prereg_effective_commit",
        {"volatile": True},
        6,
    )
    baseline["journals/*/*/slot_id"] = [
        ["t325-h1-on-r0-a0", 1], ["t325-h1-off-r0-a0", 1],
        ["t325-h1-swapped-r0-a0", 1], ["t325-h2-on-r0-a0", 1],
        ["t325-h2-off-r0-a0", 1], ["t325-h2-swapped-r0-a0", 1],
    ]
    for path in (
        "journals/*/*/launch_admission/prereg_content_commit",
        "journals/*/*/launch_admission/prereg_effective_commit",
        "journals/*/*/launch_admission/binding/prereg_content_commit",
        "journals/*/*/launch_admission/binding/prereg_effective_commit",
    ):
        set_value(path, {"volatile": True}, 6)

    lifecycle_runs = baseline["lifecycle/*"]
    lifecycle_start_keys = [
        "activation_report_digest_sha256", "event", "launch_admission_sha256",
        "manifest_sha256", "measurement_head", "mode", "prereg_commit",
        "prereg_content_commit", "prereg_effective_commit", "process_identity",
        "run_root", "schedule_row_sha256", "schema_version", "slot_id",
        "trial_id",
    ]
    lifecycle_terminal_keys = [
        "attempt_journal_sha256", "classification_receipt_sha256", "event",
        "prereg_commit", "prereg_content_commit", "prereg_effective_commit",
        "raw_output_sha256", "report_sha256", "schema_version", "slot_id",
        "terminal_status", "trial_id",
    ]
    for index, run in enumerate(lifecycle_runs):
        run[0]["dict_keys"] = list(
            lifecycle_start_keys if index % 2 == 0 else lifecycle_terminal_keys
        )
    baseline["lifecycle/*/start/prereg_commit"] = [
        ["bcb3912d3380451505a2cd5de3138e310dd659b6", 6],
    ]
    baseline["lifecycle/*/terminal/prereg_commit"] = [
        [{"volatile": True}, 6],
    ]
    set_value(
        "lifecycle/*/prereg_content_commit",
        {"volatile": True},
        12,
    )
    set_value(
        "lifecycle/*/prereg_effective_commit",
        {"volatile": True},
        12,
    )
    set_value("lifecycle/*/schema_version", "p3-8c-trial-lifecycle/v2", 12)
    set_value(
        "lifecycle/*/process_identity",
        {"dict_keys": ["execution_uuid", "pid", "starttime"]},
        6,
    )
    for field in ("execution_uuid", "pid", "starttime"):
        set_value(f"lifecycle/*/process_identity/{field}", {"volatile": True}, 6)
    set_value(
        "lifecycle/*/classification_receipt_sha256",
        {"volatile": True},
        6,
    )
    set_value("lifecycle/*/raw_output_sha256", {"volatile": True}, 6)
    baseline["lifecycle/*/schedule_row_sha256"] = [[{"volatile": True}, 6]]
    baseline["lifecycle/*/slot_id"] = [
        ["t325-h1-on-r0-a0", 2], ["t325-h1-off-r0-a0", 2],
        ["t325-h1-swapped-r0-a0", 2], ["t325-h2-on-r0-a0", 2],
        ["t325-h2-off-r0-a0", 2], ["t325-h2-swapped-r0-a0", 2],
    ]
    baseline["acceptance/lifecycle_prefix_bytes"] = [[{"volatile": True}, 1]]


_extend_t1353_originless_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _extend_t2145_role_source_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Follow the reviewed T-2145 auditor source pin in live originless output."""
    old = "e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e"
    new = "a0912ebbc95e2f3641cfb1cbf0d609cfbe2deb7ba52d1c3057517b1bc69fab35"
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    replaced = 0
    for row in journal_rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    report_rows = baseline[
        "reports/*/cells/*/generations/*/roles/auditor/"
        "provenance/role_file_sha256"
    ]
    assert report_rows == [[old, 6]]
    report_rows[0][0] = new


_extend_t2145_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _extend_t2249_role_source_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Follow the reviewed T-2249 planner source pin in live originless output."""
    old = "0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e"
    new = "3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374"
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    replaced = 0
    for row in journal_rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    report_rows = baseline[
        "reports/*/cells/*/generations/*/roles/planner/"
        "provenance/role_file_sha256"
    ]
    assert report_rows == [[old, 6]]
    report_rows[0][0] = new


_extend_t2249_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _extend_t2528_role_source_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Follow the reviewed T-2528 planner and trigger-gating source pins."""
    old = "3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374"
    new = "1d6b1603dbbb7c776202cd20a300e60e01b9119b55068ddfcce3e83714f646da"
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    replaced = 0
    for row in journal_rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    report_rows = baseline[
        "reports/*/cells/*/generations/*/roles/planner/"
        "provenance/role_file_sha256"
    ]
    assert report_rows == [[old, 6]]
    report_rows[0][0] = new

    old = "a03045c86027ec09e01d0727557eaa653c8f04d0929c007a4f129902742a2db0"
    new = "00405a9639b150372cf0881699090090cf688d4a61fa22651e0aee27e8d5279a"
    replaced = 0
    for row in journal_rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    report_rows = baseline[
        "reports/*/cells/*/generations/*/roles/coder/"
        "provenance/role_file_sha256"
    ]
    assert report_rows == [[old, 6]]
    report_rows[0][0] = new


_extend_t2528_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _extend_t304_role_name_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Apply only the reviewed source/schema leaves surviving projection.

    T1311 restores all four roles' payload hashes; T244 consumes validation
    receipts and restores the report schema. Keep those frozen expectations.
    """
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    for role, old, new in (
        (
            "planner",
            "1d6b1603dbbb7c776202cd20a300e60e01b9119b55068ddfcce3e83714f646da",
            "c47cf0ff81bb88d1ad65d5b0b92ac35feb40f49e4d2a8eef9007b48c286bf5f9",
        ),
        (
            "coder",
            "00405a9639b150372cf0881699090090cf688d4a61fa22651e0aee27e8d5279a",
            "2b46df2e4a5cbafcd3780b4cca54b3d81f3a73d9999cc6c859f1107aa398835a",
        ),
    ):
        replaced = 0
        for row in journal_rows:
            if row[0] == old:
                row[0] = new
                replaced += 1
        assert replaced == 6
        report_rows = baseline[
            f"reports/*/cells/*/generations/*/roles/{role}/"
            "provenance/role_file_sha256"
        ]
        assert report_rows == [[old, 6]]
        report_rows[0][0] = new
    schema_rows = baseline["journals/*/*/schema_version"]
    assert schema_rows == [["p3-autonomous-workload-trial/v3", 6]]
    schema_rows[0][0] = "p3-autonomous-workload-trial/v4"


_extend_t304_role_name_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _extend_t2703_role_source_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Follow the reviewed T-2703/T-2717/T-2705 role source pins."""
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    for role, old, new in (
        (
            "planner",
            "c47cf0ff81bb88d1ad65d5b0b92ac35feb40f49e4d2a8eef9007b48c286bf5f9",
            # T-2849: fixed pin for the reviewed K0 observation-input revision.
            "a2e01d52bb4d6399c40a5e1ae280ec9e7c64201e79a4a365f00734d006d3eb55",
        ),
        (
            "critic",
            "cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",
            "fea81c65909aa9026b8fda1bf9b4768b38185dfd9327cff86a8bcef844504c1b",
        ),
        (
            "coder",
            "2b46df2e4a5cbafcd3780b4cca54b3d81f3a73d9999cc6c859f1107aa398835a",
            "2cc08b30573aef3337740d3e44848d94651d48528d4e1f095b420ceea4807388",
        ),
    ):
        replaced = 0
        for row in journal_rows:
            if row[0] == old:
                row[0] = new
                replaced += 1
        assert replaced == 6
        report_rows = baseline[
            f"reports/*/cells/*/generations/*/roles/{role}/"
            "provenance/role_file_sha256"
        ]
        assert report_rows == [[old, 6]]
        report_rows[0][0] = new


_extend_t2703_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _extend_t2773_role_source_baseline(baseline):
    old = "a0912ebbc95e2f3641cfb1cbf0d609cfbe2deb7ba52d1c3057517b1bc69fab35"
    new = "dc63a3118393503f7eed4952478f0aa34690b344ee1ca98915e455e210165f34"
    rows = baseline["journals/*/*/provenance/role_file_sha256"]
    replaced = 0
    for row in rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    rows = baseline[
        "reports/*/cells/*/generations/*/roles/auditor/"
        "provenance/role_file_sha256"
    ]
    assert rows == [[old, 6]]
    rows[0][0] = new


_extend_t2773_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)


def _assert_same_structure(left: object, right: object, path=()) -> None:
    if type(left) is dict or type(right) is dict:
        assert type(left) is type(right) is dict, path
        assert list(left) == list(right), path
        for key in left:
            _assert_same_structure(left[key], right[key], (*path, key))
        return
    if type(left) is list or type(right) is list:
        assert type(left) is type(right) is list, path
        assert len(left) == len(right), path
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=True)):
            _assert_same_structure(left_item, right_item, (*path, index))
        return
    if not _volatile(path):
        assert left == right, path


def _generation_two_views(
    bundle: dict[str, object],
) -> dict[str, tuple[dict[str, object], list[dict[str, object]]]]:
    reports = bundle["reports"]
    journals = bundle["journals"]
    assert type(reports) is list
    assert type(journals) is list
    journal_by_trial = {}
    for journal in journals:
        assert type(journal) is list
        run_start = next(event for event in journal if event["event"] == "run-start")
        trial_id = run_start["trial_id"]
        assert trial_id not in journal_by_trial
        journal_by_trial[trial_id] = journal

    views = {}
    for report in reports:
        assert type(report) is dict
        trial_id = report["trial_id"]
        assert trial_id not in views
        cells = report["cells"]
        assert type(cells) is list and len(cells) == 1
        generations = cells[0]["generations"]
        assert [item["generation"] for item in generations] == [1, 2]
        generation_two = generations[1]
        journal_events = [
            event
            for event in journal_by_trial.pop(trial_id)
            if event.get("generation") == 2
        ]
        assert [
            (event["event"], event.get("role")) for event in journal_events
        ] == [
            ("role-attempt", "planner"),
            ("role-attempt", "coder"),
            ("role-attempt", "auditor"),
            ("role-attempt", "critic"),
            ("generation-accounting", None),
        ]
        views[trial_id] = (generation_two, journal_events)
    assert not journal_by_trial
    return views


def _assert_generation_two_matches(
    reference: dict[str, object],
    candidate: dict[str, object],
) -> None:
    reference_views = _generation_two_views(reference)
    candidate_views = _generation_two_views(candidate)
    assert candidate_views
    assert set(candidate_views) <= set(reference_views)
    for trial_id, (candidate_report, candidate_journal) in candidate_views.items():
        reference_report, reference_journal = reference_views[trial_id]
        _assert_same_structure(
            reference_report,
            candidate_report,
            ("reports", 0, "cells", 0, "generations", 1),
        )
        assert len(reference_journal) == len(candidate_journal)
        for index, (reference_event, candidate_event) in enumerate(
            zip(reference_journal, candidate_journal, strict=True)
        ):
            _assert_same_structure(
                reference_event,
                candidate_event,
                ("journals", 0, index),
            )


def _baseline_structure(value: object) -> dict[str, list[list[object]]]:
    observed: dict[str, list[object]] = {}

    def add(path: tuple[object, ...], item: object) -> None:
        key = "/".join(str(component) for component in path) or "$"
        observed.setdefault(key, []).append(item)

    def walk(item: object, path: tuple[object, ...] = ()) -> None:
        if type(item) is dict:
            add(path, {"dict_keys": list(item)})
            for key, child in item.items():
                child_path = (*path, key)
                # T1353's lifecycle ``prereg_commit`` is the stable manifest
                # anchor on start rows but the content commit on terminal rows.
                if (
                    path == ("lifecycle", "*")
                    and key == "prereg_commit"
                    and item.get("event") in {"start", "terminal"}
                ):
                    child_path = (*path, item["event"], key)
                walk(child, child_path)
            return
        if type(item) is list:
            add(path, {"list_length": len(item)})
            for child in item:
                walk(child, (*path, "*"))
            return
        add(path, {"volatile": True} if _volatile(path) else item)

    walk(value)
    compacted: dict[str, list[list[object]]] = {}
    for path, values in sorted(observed.items()):
        runs: list[list[object]] = []
        for item in values:
            if runs and runs[-1][0] == item:
                runs[-1][1] += 1
            else:
                runs.append([item, 1])
        compacted[path] = runs
    return _normalize_main_derived_leaves(compacted)


_T244_REPORT_ADDITIONS = {
    "honest_accounting",
    "honest_accounting_authority",
    "generation_driver",
    "gating_spec_sha256",
}
_T244_DRIVER = {
    "wrapper": "s8c-generation/v1",
    "delegate": "caller-injected-unsupported",
}
_T244_ACCOUNTING_AUTHORITY = "excluded-caller-injected-unsupported"
_T244_GATING_SPEC_SHA256 = hashlib.sha256(
    A.GATING_SPEC.encode("utf-8")
).hexdigest()
_T244_ADJUDICATED_PLANNER_EFFECTIVE_PROMPT_DELTA = {
    "pre_wave": "f7f461a798b5a1745a26fdc51860853c4c95327f2234ec050ec3f9b46271542d",
    "current": "55c52d5ea8afdd9c9a26f9ef2f8696e3740423b4461096ce2bc6a49003389b53",
}


def _project_planner_effective_prompt_delta(event: dict[str, object]) -> None:
    if event["role"] != "planner":
        return
    provenance = event["provenance"]
    assert isinstance(provenance, dict)
    # 段 4 裁定 §1 / 第 2 巡の親裁定で ROLE_CONTRACTS["planner"] へ critic_feedback の記述を追加したため。
    assert provenance["effective_prompt_sha256"] == (
        _T244_ADJUDICATED_PLANNER_EFFECTIVE_PROMPT_DELTA["current"]
    )
    provenance["effective_prompt_sha256"] = (
        _T244_ADJUDICATED_PLANNER_EFFECTIVE_PROMPT_DELTA["pre_wave"]
    )


def _consume_role_validation_evidence(event: dict[str, object]) -> None:
    role = event["role"]
    generation = event["generation"]
    spec_key = (
        "planner-generation-1"
        if role == "planner" and generation == 1
        else "planner-generation-next"
        if role == "planner"
        else role
    )
    assert event.pop("payload_exact_keys") == A.ROLE_PAYLOAD_KEY_SPEC[spec_key]
    assert event.pop("payload_allowlist_sha256") == A.ROLE_PAYLOAD_ALLOWLIST_SHA256
    ordinal = event.pop("role_query_ordinal")
    assert type(ordinal) is int and ordinal >= 1
    if role in {"planner", "coder"}:
        receipt = event.pop("payload_validation_receipt")
        assert set(receipt) == {
            "schema_version", "role", "payload_sha256",
            "payload_allowlist_sha256", "safe_projection",
            "safe_projection_sha256", "seal_sha256",
        }
        assert receipt["role"] == role
        assert receipt["payload_sha256"] == event["input_payload_sha256"]
        assert receipt["payload_allowlist_sha256"] == A.ROLE_PAYLOAD_ALLOWLIST_SHA256
    else:
        assert "payload_validation_receipt" not in event


def _project_t1185_generation_binding_to_generation_one(
    bundle: dict[str, object],
) -> dict[str, object]:
    """Consume the intended formal G=2 delta before the older golden view."""

    projected = copy.deepcopy(bundle)
    for report in projected["reports"]:
        assert report["generation_budget_per_workload"] == 2
        report["generation_budget_per_workload"] = 1
        assert report["honest_accounting"]["role_query_count"] == 8
        report["honest_accounting"]["role_query_count"] = 4
        for cell in report["cells"]:
            generations = cell["generations"]
            assert [item["generation"] for item in generations] == [1, 2]
            first, second = generations
            assert list(first) == list(second)
            assert list(first["roles"]) == list(second["roles"])
            for role in first["roles"]:
                assert list(first["roles"][role]) == list(second["roles"][role])
            cell["generations"] = [first]

    for journal in projected["journals"]:
        generation_one_roles = {
            event["role"]: event
            for event in journal
            if event["event"] == "role-attempt" and event["generation"] == 1
        }
        generation_one_accounting = next(
            event for event in journal
            if event["event"] == "generation-accounting"
            and event["generation"] == 1
        )
        kept = []
        removed = 0
        for event in journal:
            if event["event"] == "run-start":
                assert event["generation_budget_per_workload"] == 2
                event["generation_budget_per_workload"] = 1
            elif event["event"] == "role-attempt" and event["generation"] == 2:
                assert list(event) == list(generation_one_roles[event["role"]])
                removed += 1
                continue
            elif (
                event["event"] == "generation-accounting"
                and event["generation"] == 2
            ):
                assert list(event) == list(generation_one_accounting)
                removed += 1
                continue
            elif event["event"] == "run-finish":
                assert event["seq"] == 12
                event["seq"] = 7
                assert event["honest_accounting"]["role_query_count"] == 8
                event["honest_accounting"]["role_query_count"] = 4
            kept.append(event)
        assert removed == 5
        journal[:] = kept
    return projected


_PRE_T1311_ROLE_PAYLOAD_SHA256 = {
    "rr80": {
        "planner": "e13194c65ec91bfbc5e85961b69f4c26a12330992f63d1a54ffbbe59a5521c30",
        "coder": "5582fb991ca35d43f28b0820a992ebf992eb40d5309e5866999aac9c2341a2c5",
        "auditor": "08469300d23c5d6985d6a0ff5fe2f48e4c41e1b2fb55f7a1408516df25265ceb",
        "critic": "150985d205911afcbd0604e4600dea5e2a50ebacf89f671e135d0ae33c984a90",
    },
    "rr20": {
        "planner": "95b45f9add1a4319d7a47ea70744a6cfc78587131aa5c43c0d196b06f5edc17a",
        "coder": "ad21042abc28eababb14788755185510d6a50f26d6ed67b4f92eeea377a2b30b",
        "auditor": "2ade3914c5d2f4bc03991e29346f32ee973863a339e34cf2fe9d994dcff8487e",
        "critic": "b77e3c1d6b70096714a2fa9f5523248ab2c30ba6751ad9593ee680a704585395",
    },
}


def _pre_t1311_descriptor(
    workload: str,
) -> tuple[dict[str, object], dict[str, str]]:
    flags = A.WORKLOADS[workload]["ycsb"]
    projected_input = {
        "records": 100_000,
        "threads": 4,
        "ycsb": dict(flags),
    }
    descriptor = {
        "schema_version": "8b-v1",
        "source": "campaign_search_config_projection",
        "contention": {"label": "high", "skew": 0.9},
        "read_write": {
            "read_ratio_percent": int(flags["ycsb_rratio"]),
            "rmw": int(flags["ycsb_rmw"]),
        },
        "scale": {"records": 100_000, "threads": 4},
        "correctness": "serializable_legacy_and_s2",
        "objective": "maximize_throughput_tps",
    }
    def canonical(value: object) -> bytes:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    binding = {
        "input_sha256": hashlib.sha256(canonical(projected_input)).hexdigest(),
        "output_sha256": hashlib.sha256(canonical(descriptor)).hexdigest(),
        "projection_version": "8b-descriptor-projection/v1",
        "schema_sha256": (
            "5a9e2696b8fba18f8f7cf01183673a1bd6f5781cc9cb1fe8641f9d667fe11549"
        ),
    }
    return descriptor, binding


_PRE_T822_ACTIVATION_REPORT_DIGEST_SHA256 = (
    "3176f3a92cd88bf551acb18651143835901286e2ab86f73be8d9098d8cfae170"
)


def _project_t1749_receipt_v4_to_v1(
    bundle: dict[str, object],
) -> dict[str, object]:
    """Validate and consume receipt-v4 additions before the frozen view."""

    projected = copy.deepcopy(bundle)
    acceptance = projected["acceptance"]
    reports = projected["reports"]
    journals = projected["journals"]
    assert type(acceptance) is dict
    assert type(reports) is list
    assert type(journals) is list
    assert acceptance["schema_version"] == "p3-8c-trial-acceptance-receipt/v5"
    assert acceptance["certifying"] is False
    assert acceptance["non_certifying_reason_codes"] == [
        "no-build",
        "t468-approval-authority-absent",
    ]
    aggregate = acceptance.pop("cross_binding_receipt_sha256")
    assert type(aggregate) is str and len(aggregate) == 64
    prereg_content_commit = acceptance.pop("prereg_content_commit")
    prereg_effective_commit = acceptance.pop("prereg_effective_commit")
    assert (
        type(prereg_content_commit) is str
        and len(prereg_content_commit) == 40
    )
    assert (
        type(prereg_effective_commit) is str
        and len(prereg_effective_commit) == 40
    )
    attempt_path = acceptance.pop("attempt_registry_path")
    attempt_prefix_bytes = acceptance.pop("attempt_registry_prefix_bytes")
    attempt_prefix_sha256 = acceptance.pop("attempt_registry_prefix_sha256")
    attempt_projection = acceptance.pop("attempt_slot_projection")
    assert attempt_path == "output/s8c-preregistration/attempt-registry.jsonl"
    assert type(attempt_prefix_bytes) is int and attempt_prefix_bytes > 0
    assert type(attempt_prefix_sha256) is str and len(attempt_prefix_sha256) == 64
    assert type(attempt_projection) is dict
    current_activation_digest = acceptance[
        "activation_report_digest_sha256"
    ]
    assert (
        type(current_activation_digest) is str
        and len(current_activation_digest) == 64
        and current_activation_digest
        != _PRE_T822_ACTIVATION_REPORT_DIGEST_SHA256
    )

    reports_by_id = {}
    for report in reports:
        assert type(report) is dict
        trial_id = report["trial_id"]
        assert type(trial_id) is str and trial_id not in reports_by_id
        reports_by_id[trial_id] = report
    starts_by_id = {}
    for journal in journals:
        assert type(journal) is list
        starts = [event for event in journal if event.get("event") == "run-start"]
        assert len(starts) == 1
        start = starts[0]
        trial_id = start["trial_id"]
        assert type(trial_id) is str and trial_id not in starts_by_id
        starts_by_id[trial_id] = start
    assert set(reports_by_id) == set(starts_by_id)
    for report in reports:
        assert report["launch_admission"][
            "activation_report_digest_sha256"
        ] == current_activation_digest
        report["launch_admission"]["activation_report_digest_sha256"] = (
            _PRE_T822_ACTIVATION_REPORT_DIGEST_SHA256
        )
    for start in starts_by_id.values():
        assert start["launch_admission"][
            "activation_report_digest_sha256"
        ] == current_activation_digest
        start["launch_admission"]["activation_report_digest_sha256"] = (
            _PRE_T822_ACTIVATION_REPORT_DIGEST_SHA256
        )
    for row in projected["lifecycle"]:
        if "activation_report_digest_sha256" not in row:
            continue
        assert row["activation_report_digest_sha256"] == current_activation_digest
        row["activation_report_digest_sha256"] = (
            _PRE_T822_ACTIVATION_REPORT_DIGEST_SHA256
        )

    receipt_trials = acceptance["trials"]
    assert type(receipt_trials) is list
    assert {trial["trial_id"] for trial in receipt_trials} == set(reports_by_id)
    leaf_rows = []
    for trial in receipt_trials:
        assert type(trial) is dict
        trial_id = trial["trial_id"]
        arm_execution = trial.pop("arm_execution")
        leaf = trial.pop("cross_binding_receipt_sha256")
        assert type(leaf) is str and len(leaf) == 64
        leaf_rows.append({"trial_id": trial_id, "receipt_sha256": leaf})
        assert set(arm_execution) == {
            "input_schema_version",
            "content_digest_sha256",
            "arm_binding_digest_sha256",
        }
        assert arm_execution == reports_by_id[trial_id]["arm_execution"]
        assert arm_execution == starts_by_id[trial_id]["arm_execution"]
        assert arm_execution.pop("input_schema_version") == "8b-v1"
        assert set(arm_execution) == {
            "content_digest_sha256",
            "arm_binding_digest_sha256",
        }
    assert hashlib.sha256(
        _canonical({
            "schema_version": "p3-8c-cross-binding-receipt/v2",
            "trials": sorted(leaf_rows, key=lambda row: row["trial_id"]),
        })
    ).hexdigest() == aggregate

    acceptance["schema_version"] = "p3-8c-trial-acceptance-receipt/v1"
    acceptance["activation_report_digest_sha256"] = (
        _PRE_T822_ACTIVATION_REPORT_DIGEST_SHA256
    )
    acceptance["non_certifying_reason_codes"] = [
        "c02-arm-binding-unproven",
        "t468-approval-authority-absent",
    ]
    return projected


def _project_t1311_arm_authority_to_pre_wave(
    bundle: dict[str, object],
) -> dict[str, object]:
    """Validate and consume the current arm-authority epoch additions."""

    projected = copy.deepcopy(bundle)

    def project_role(event: dict[str, object]) -> None:
        workload = event["workload"]
        role = event["role"]
        assert workload in _PRE_T1311_ROLE_PAYLOAD_SHA256
        assert role in _PRE_T1311_ROLE_PAYLOAD_SHA256[workload]
        arm_digest = event.pop("arm_binding_digest_sha256")
        assert type(arm_digest) is str and len(arm_digest) == 64
        old_payload_sha256 = _PRE_T1311_ROLE_PAYLOAD_SHA256[workload][role]
        event["descriptor_sha256"] = _pre_t1311_descriptor(workload)[1][
            "output_sha256"
        ]
        event["input_payload_sha256"] = old_payload_sha256
        event["invocation_id"] = f"{workload}.g1.{role}"
        provenance = event["provenance"]
        assert type(provenance) is dict
        provenance["child_id"] = f"fixture-{workload}.g1.{role}"
        provenance["payload_sha256"] = old_payload_sha256
        receipt = event.get("payload_validation_receipt")
        if receipt is not None:
            assert type(receipt) is dict
            receipt["payload_sha256"] = old_payload_sha256

    for report in projected["reports"]:
        arm_execution = report.pop("arm_execution")
        assert arm_execution.pop("input_schema_version") == "8b-v1"
        assert set(arm_execution) == {
            "content_digest_sha256", "arm_binding_digest_sha256",
        }
        for cell in report["cells"]:
            perf_config_scale = cell.pop("perf_config_scale")
            assert perf_config_scale == cell["descriptor"]["scale"]
            descriptor, descriptor_binding = _pre_t1311_descriptor(
                cell["workload"]
            )
            descriptor = json.loads(json.dumps(descriptor, sort_keys=True))
            descriptor_binding = json.loads(json.dumps(
                descriptor_binding, sort_keys=True,
            ))
            current_binding = cell["descriptor_binding"]
            assert set(current_binding) == {
                "input_sha256", "output_sha256", "projection_version",
                "schema_sha256", "content_digest_sha256",
                "arm_binding_digest_sha256",
            }
            assert current_binding["content_digest_sha256"] == (
                arm_execution["content_digest_sha256"]
            )
            assert current_binding["arm_binding_digest_sha256"] == (
                arm_execution["arm_binding_digest_sha256"]
            )
            cell["descriptor"] = descriptor
            cell["descriptor_binding"] = descriptor_binding
            for generation in cell["generations"]:
                proposal = generation.pop("proposal")
                assert set(proposal) == {"path", "sha256", "digest"}
                assert proposal["digest"] == arm_execution[
                    "arm_binding_digest_sha256"
                ]
                for event in generation["roles"].values():
                    project_role(event)

    for journal in projected["journals"]:
        for event in journal:
            if event["event"] == "run-start":
                arm_execution = event.pop("arm_execution")
                assert arm_execution.pop("input_schema_version") == "8b-v1"
                assert set(arm_execution) == {
                    "content_digest_sha256", "arm_binding_digest_sha256",
                }
            elif event["event"] == "role-attempt":
                project_role(event)
    return projected


def _project_t244_additions_to_pre_wave(bundle: dict[str, object]) -> dict[str, object]:
    """Consume each adjudicated addition explicitly, then expose the old view."""

    projected = _project_t1185_generation_binding_to_generation_one(bundle)
    projected = _project_t1749_receipt_v4_to_v1(projected)
    projected = _project_t1311_arm_authority_to_pre_wave(projected)
    for report in projected["reports"]:
        assert report["schema_version"] == A.REPORT_SCHEMA_VERSION
        report["schema_version"] = "p3-autonomous-workload-trial-report/v2"
        assert _T244_REPORT_ADDITIONS <= set(report)
        assert report.pop("honest_accounting") == {
            "role_query_count": 4,
            "bench_wall_seconds": 0.0,
        }
        assert report.pop("honest_accounting_authority") == _T244_ACCOUNTING_AUTHORITY
        assert report.pop("generation_driver") == _T244_DRIVER
        assert report.pop("gating_spec_sha256") == _T244_GATING_SPEC_SHA256
        for cell in report["cells"]:
            for generation in cell["generations"]:
                assert generation.pop("bench_wall_seconds") == 0.0
                assert generation.pop("generation_driver") == _T244_DRIVER
                assert generation.pop("gating_spec_sha256") == _T244_GATING_SPEC_SHA256
                for event in generation["roles"].values():
                    _project_planner_effective_prompt_delta(event)
                    _consume_role_validation_evidence(event)

    for journal in projected["journals"]:
        legacy_events = []
        for event in journal:
            event_name = event["event"]
            if event_name == "run-start":
                assert event.pop("generation_driver") == _T244_DRIVER
                assert event.pop("gating_spec_sha256") == _T244_GATING_SPEC_SHA256
                assert event.pop("honest_accounting_authority") == _T244_ACCOUNTING_AUTHORITY
            elif event_name == "role-attempt":
                _project_planner_effective_prompt_delta(event)
                _consume_role_validation_evidence(event)
            elif event_name == "generation-accounting":
                assert event["state"] == "generation-complete"
                assert event["provider_invoke_count"] == 4
                assert event["auditor_pre_audit_skipped"] is False
                assert event["bench_wall_seconds"] == 0.0
                assert event["generation_driver"] == _T244_DRIVER
                assert event["gating_spec_sha256"] == _T244_GATING_SPEC_SHA256
                assert event["accounting_authority"] == _T244_ACCOUNTING_AUTHORITY
                continue
            elif event_name == "run-finish":
                assert event["seq"] == 7
                event["seq"] = 6
                assert event.pop("generation_driver") == _T244_DRIVER
                assert event.pop("gating_spec_sha256") == _T244_GATING_SPEC_SHA256
                assert event.pop("honest_accounting") == {
                    "role_query_count": 4,
                    "bench_wall_seconds": 0.0,
                }
                assert event.pop("honest_accounting_authority") == _T244_ACCOUNTING_AUTHORITY
            legacy_events.append(event)
        journal[:] = legacy_events
    return projected


def test_originless_harness_rebuild_is_deterministic_control(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Control: rebuilding the harness must not change default-path bytes."""
    _pin_fixture_commit_dates(monkeypatch)
    bundle_root = _fixed_width_bundle_root(tmp_path, "originless-control")
    first = _bundle(bundle_root, monkeypatch, explicit_none=False)
    shutil.rmtree(bundle_root)
    second = _bundle(bundle_root, monkeypatch, explicit_none=False)
    _assert_same_structure(first, second)


def test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_fixture_commit_dates(monkeypatch)
    bundle_root = _fixed_width_bundle_root(tmp_path, "originless")
    omitted = _bundle(bundle_root, monkeypatch, explicit_none=False)
    shutil.rmtree(bundle_root)
    explicit_none = _bundle(bundle_root, monkeypatch, explicit_none=True)
    origin_enabled = _origin_enabled_bundle(
        _fixed_width_bundle_root(tmp_path, "origin-enabled"), monkeypatch
    )
    _assert_generation_two_matches(omitted, explicit_none)
    _assert_generation_two_matches(omitted, origin_enabled)
    generation_two_mutant = copy.deepcopy(origin_enabled)
    generation_two_mutant["reports"][0]["cells"][0]["generations"][1]["roles"][
        "planner"
    ]["parsed"]["magnitude"] = "generation-two-mutant"
    generation_two_planner = next(
        event
        for event in generation_two_mutant["journals"][0]
        if event.get("generation") == 2 and event.get("role") == "planner"
    )
    generation_two_planner["parsed"]["magnitude"] = "generation-two-mutant"
    with pytest.raises(AssertionError):
        _assert_generation_two_matches(omitted, generation_two_mutant)
    receipt_binding_mutant = copy.deepcopy(omitted)
    receipt_binding_mutant["acceptance"]["trials"][0]["arm_execution"][
        "content_digest_sha256"
    ] = "f" * 64
    with pytest.raises(AssertionError):
        _project_t1749_receipt_v4_to_v1(receipt_binding_mutant)
    run_start_mutant = copy.deepcopy(omitted)
    start = next(
        event for event in run_start_mutant["journals"][0]
        if event["event"] == "run-start"
    )
    start["arm_execution"]["content_digest_sha256"] = "e" * 64
    with pytest.raises(AssertionError):
        _project_t1749_receipt_v4_to_v1(run_start_mutant)
    input_schema_mutant = copy.deepcopy(omitted)
    receipt_trial = input_schema_mutant["acceptance"]["trials"][0]
    trial_id = receipt_trial["trial_id"]
    report = next(
        item for item in input_schema_mutant["reports"]
        if item["trial_id"] == trial_id
    )
    run_start = next(
        event
        for journal in input_schema_mutant["journals"]
        for event in journal
        if event.get("event") == "run-start" and event["trial_id"] == trial_id
    )
    for arm_execution in (
        receipt_trial["arm_execution"],
        report["arm_execution"],
        run_start["arm_execution"],
    ):
        arm_execution["input_schema_version"] = "8b-mutant"
    with pytest.raises(AssertionError):
        _project_t244_additions_to_pre_wave(input_schema_mutant)
    report_schema_mutant = copy.deepcopy(omitted)
    report_schema_mutant["reports"][0]["arm_execution"][
        "input_schema_version"
    ] = "8b-mutant"
    with pytest.raises(AssertionError):
        _project_t1311_arm_authority_to_pre_wave(report_schema_mutant)
    run_start_schema_mutant = copy.deepcopy(omitted)
    run_start = next(
        event for event in run_start_schema_mutant["journals"][0]
        if event["event"] == "run-start"
    )
    run_start["arm_execution"]["input_schema_version"] = "8b-mutant"
    with pytest.raises(AssertionError):
        _project_t1311_arm_authority_to_pre_wave(run_start_schema_mutant)
    assert _baseline_structure(
        _project_t244_additions_to_pre_wave(omitted)
    ) == _PRE_WAVE_ORIGINLESS_BASELINE
    assert _baseline_structure(
        _project_t244_additions_to_pre_wave(explicit_none)
    ) == _PRE_WAVE_ORIGINLESS_BASELINE
    _assert_same_structure(omitted, explicit_none)
    originless_key_mutant = copy.deepcopy(omitted)
    originless_key_mutant["reports"][0]["origin_runtime"] = None
    with pytest.raises(AssertionError):
        assert _baseline_structure(
            _project_t244_additions_to_pre_wave(originless_key_mutant)
        ) == _PRE_WAVE_ORIGINLESS_BASELINE
    with pytest.raises(AssertionError):
        _assert_same_structure(omitted, originless_key_mutant)
    unknown_key_mutant = copy.deepcopy(omitted)
    unknown_key_mutant["reports"][0]["stable_unknown_top_level_key"] = "stable-value"
    with pytest.raises(AssertionError):
        assert _baseline_structure(
            _project_t244_additions_to_pre_wave(unknown_key_mutant)
        ) == _PRE_WAVE_ORIGINLESS_BASELINE
    for bundle in (omitted, explicit_none):
        for report in bundle["reports"]:
            assert "origin_runtime" not in report
            assert "origin_terminal_projection" not in report
            assert "origin_binding" not in report["launch_admission"]
            for cell in report["cells"]:
                assert "campaign_path" in cell["admission_decision"] or (
                    cell["admission_decision"] == {"admission_status": "not-applicable"}
                )
        for row in bundle["lifecycle"]:
            assert "origin_run_plan_sha256" not in row
            assert "origin_terminal_projection" not in row
        for trial in bundle["acceptance"]["trials"]:
            assert "origin_terminal_projection" not in trial
