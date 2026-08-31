from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from decimal import Decimal
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest import mock

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

import pytest

from orchestrator.campaign import p3_b4_analysis_ledgers as ledgers
from orchestrator.campaign import p3_b4_closed_critic as closed_critic
from orchestrator.campaign import p3_b4_material_report as R
from orchestrator.campaign import p3_b4_raw_record_producer as producer
from orchestrator.campaign import p3_s4_loop as loop
from orchestrator.campaign.p3_b4_analysis_contract import EXPECTED_BLOCK_COUNT
import test_p3_b4_raw_record_producer as producer_test_support
from test_p3_b4_raw_record_producer import (
    _PublicationEvidence,
    _assert_replicas_match_real_except_identity,
    _build_full_publication_evidence,
    _publication,
    _publish_full_publication,
)


pytestmark = pytest.mark.xdist_group("p3-b4-material-report")


@dataclass(frozen=True)
class _ImmutablePublication:
    publication_evidence: _PublicationEvidence

    @property
    def publication(self):
        return self.publication_evidence.publication


_INPUT_CACHE: dict[str, R.B4MaterialReportInputs] = {}
_DOCUMENT_CACHE: dict[str, R.B4MaterialReportDocument] = {}


@pytest.fixture(scope="module")
def immutable_publication(tmp_path_factory) -> _ImmutablePublication:
    """Create one immutable publication with exactly one real on/off invoke pair."""

    root = tmp_path_factory.mktemp("b4-material-report-publication")
    invoke_ids: list[str] = []
    original_invoke = closed_critic.B4ClosedCriticController.invoke
    original_admission_factory = producer_test_support._committed_admission_fixture
    original_clone = producer_test_support._clone_evidence_with_writers

    def counted_invoke(controller, *, invocation_id):
        invoke_ids.append(invocation_id)
        return original_invoke(controller, invocation_id=invocation_id)

    def canonical_role_admission(*args, **kwargs):
        return replace(
            original_admission_factory(*args, **kwargs),
            role_file=closed_critic.ROLE_FILE.resolve(),
        )

    def clone_abort_evidence(*args, **kwargs):
        assert kwargs["terminal"] == "abort"
        cloned = original_clone(
            *args,
            **{**kwargs, "terminal": "absent"},
        )
        for layout in (cloned.on_layout, cloned.off_layout):
            state = loop.load_loop_state(layout)
            assert state is not None
            state.iteration += 1
            state.whiteboard.append(loop.WhiteboardEntry(
                iteration=state.iteration,
                direction="increase",
                magnitude="small",
                result="rejected",
                delta_pct=None,
            ))
            loop.save_loop_state(layout, state)
        return cloned

    with (
        mock.patch.object(os, "fsync", return_value=None),
        mock.patch.object(
            producer_test_support,
            "_committed_admission_fixture",
            side_effect=canonical_role_admission,
        ),
        mock.patch.object(
            producer_test_support,
            "_clone_evidence_with_writers",
            side_effect=clone_abort_evidence,
        ),
        mock.patch.object(
            closed_critic.B4ClosedCriticController,
            "invoke",
            counted_invoke,
        ),
    ):
        publication_evidence = _build_full_publication_evidence(
            root / "evidence",
            terminal="abort",
        )
        _assert_replicas_match_real_except_identity(
            publication_evidence.evidence
        )
        publication, _ = _publish_full_publication(
            publication=publication_evidence.publication,
            evidence=publication_evidence.evidence,
        )
    assert publication is publication_evidence.publication
    assert invoke_ids == ["producer-on-1", "producer-off-1"]
    return _ImmutablePublication(
        publication_evidence=publication_evidence,
    )


def _fresh_publication_from_shared_evidence(
    tmp_path: Path,
    immutable: _ImmutablePublication,
):
    seed = bytes.fromhex(immutable.publication.seed_receipt.seed_hex)
    with (
        mock.patch.object(os, "fsync", return_value=None),
        mock.patch.object(
            sys.modules[_publication.__module__].issuer.secrets,
            "token_bytes",
            return_value=seed,
        ),
    ):
        publication = _publication(tmp_path / "fresh")
        publication, assembly = _publish_full_publication(
            publication=publication,
            evidence=immutable.publication_evidence.evidence,
        )
    assert isinstance(assembly, producer.B4RawAnalysisAssembly)
    return publication


def _inputs(immutable: _ImmutablePublication) -> R.B4MaterialReportInputs:
    publication_root = immutable.publication.publication_root
    if publication_root not in _INPUT_CACHE:
        _INPUT_CACHE[publication_root] = R._load_and_evaluate(
            Path(publication_root)
        )
    return _INPUT_CACHE[publication_root]


def _document(immutable: _ImmutablePublication) -> R.B4MaterialReportDocument:
    publication_root = immutable.publication.publication_root
    if publication_root not in _DOCUMENT_CACHE:
        _DOCUMENT_CACHE[publication_root] = R.build_material_report_document(
            publication_root
        )
    return _DOCUMENT_CACHE[publication_root]


def test_normal_path_assembles_binds_evaluates_and_builds_document(
    immutable_publication: _ImmutablePublication,
) -> None:
    inputs = _inputs(immutable_publication)
    assert isinstance(inputs.assembly, producer.B4RawAnalysisAssembly)
    assert len(inputs.assembly.source_artifact_bytes) == 2 * EXPECTED_BLOCK_COUNT
    assert inputs.contract_binding is not None
    assert inputs.analysis_result is not None

    document = _document(immutable_publication)
    assert document.json_value["assembly"]["status"] == "assembled"
    assert document.json_value["analysis"]["status"] == "evaluated"


def test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf(
    tmp_path: Path,
    immutable_publication: _ImmutablePublication,
) -> None:
    publication = _fresh_publication_from_shared_evidence(
        tmp_path,
        immutable_publication,
    )
    missing = publication.planned_result_artifacts[-1]
    Path(missing.artifact_path).unlink()
    output = tmp_path / "report-output"

    written = R.write_material_report(
        publication.publication_root,
        output_root=output,
    )
    report = json.loads(Path(written.report_json_path).read_bytes())

    assert report["block_count"] == EXPECTED_BLOCK_COUNT
    assert report["arm_row_count"] == 2 * EXPECTED_BLOCK_COUNT
    assert report["assembly"]["status"] == "rejected"
    assert report["assembly"]["analysis_status"] == "not_evaluated"
    assert report["analysis"] == {
        "floor_argument": None,
        "reason": "assembly_rejected",
        "result": None,
        "status": "not_evaluated",
    }
    assert report["assembly"]["reason"]["issues"][0]["code"] == "incomplete_set"
    missing_rows = [
        row for row in report["rows"]
        if row["attempt_id"] == missing.attempt_id
    ]
    assert len(missing_rows) == 2
    assert {row["planned_attempt_artifact"]["availability"] for row in missing_rows} == {"absent"}
    assert sum(
        row["planned_attempt_artifact"]["availability"] == "present"
        for row in report["rows"]
    ) == 2 * (EXPECTED_BLOCK_COUNT - 1)
    assert all(row["source_object"]["availability"] == "absent" for row in report["rows"])
    assert (
        "past_producer_rejections_are_not_fully_reconstructible_from_publication_root"
        in report["provenance"]["report_non_guarantees"]
    )
    assert report["campaign_disjointness"]["status"] == "partial"
    assert report["campaign_disjointness"]["unresolved"]
    markdown = Path(written.report_md_path).read_text(encoding="utf-8")
    assert "assembly rejection reason" in markdown
    assert "incomplete_set" in markdown
    assert report["provenance"]["publication_root"] in markdown
    assert report["provenance"]["artifacts"]["registry"]["sha256"] in markdown
    assert _independent_markdown_cell(
        report["provenance"]["reproduction_argv"]
    ) in markdown
    assert Path(written.report_commit_path).is_file()


@pytest.mark.parametrize("damage", ["missing", "malformed"])
def test_partial_campaign_discovery_fails_closed_for_output_campaigns_path(
    tmp_path: Path,
    immutable_publication: _ImmutablePublication,
    damage: str,
) -> None:
    publication = _fresh_publication_from_shared_evidence(
        tmp_path,
        immutable_publication,
    )
    damaged = publication.planned_result_artifacts[-1]
    if damage == "missing":
        Path(damaged.artifact_path).unlink()
    else:
        Path(damaged.artifact_path).write_bytes(b"{")
    campaign = Path(
        immutable_publication.publication_evidence.evidence[-1].on_layout.root
    )
    output = campaign / "material-report-output"
    with pytest.raises(
        R.B4MaterialReportError,
        match="output_campaign_disjointness_unproven",
    ):
        R.write_material_report(
            publication.publication_root,
            output_root=output,
        )
    assert not (output / R.REPORT_JSON_NAME).exists()
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_complete_projection_preserves_402_sources_fields_and_transcribed_binding(
    immutable_publication: _ImmutablePublication,
) -> None:
    document = _document(immutable_publication)
    report = document.json_value
    publication = immutable_publication.publication
    attempts = {item.attempt_id: item for item in publication.registry.scheduled_attempts}

    assert report["block_count"] == EXPECTED_BLOCK_COUNT
    assert report["arm_row_count"] == 2 * EXPECTED_BLOCK_COUNT
    assert len(report["rows"]) == 2 * EXPECTED_BLOCK_COUNT
    identities = [(row["attempt_id"], row["arm"]) for row in report["rows"]]
    assert identities == [
        (manifest_row.attempt_id, arm)
        for manifest_row in publication.manifest.rows
        for arm in ("on", "off")
    ]
    source_hashes = []
    for row in report["rows"]:
        source_bytes = row["source_artifact_utf8"].encode("utf-8")
        source_hashes.append(hashlib.sha256(source_bytes).hexdigest())
        assert row["source_artifact_sha256"] == source_hashes[-1]
        assert row["source_object"] == json.loads(source_bytes, parse_float=Decimal)
        assert row["campaign_id"] == row["source_object"]["identity"]["campaign_id"]
        assert str(closed_critic.ROLE_FILE.resolve()) in {
            item["path"]
            for item in row["source_object"]["evidence"]["transitive_evidence"]
        }
        campaign_root = Path(
            row["source_object"]["evidence"]["campaign_lock"]["path"]
        ).resolve().parent
        wal_path = Path(row["wal"]["path"]).resolve()
        assert wal_path.parents[1] == campaign_root
        assert wal_path.parent != campaign_root
        assert str(campaign_root) in report["campaign_disjointness"]["campaign_roots"]
        assert row["stop_reason"]["terminal_reason"] == row["source_object"]["raw"]["terminal_reason"]
        assert row["stop_reason"]["terminal_reason"] == "diff-quarantine"
        assert row["evidence_issues"] == row["source_object"]["evidence_issues"]
        attempt = attempts[row["attempt_id"]]
        assert row["precursor_digest_red_classes"] == [
            item.value for item in attempt.digest_red_classes
        ]
        assert row["anomaly_class"] == {"availability": "absent", "value": None}
        initial = row["initial_snapshot_hash"]
        assert initial["value"] == attempt.initial_proposal_sha256
        assert initial["binding"] == "transcribed"
        assert initial["source"] == "registry.initial_proposal_sha256"
        assert "転記に留まる" in initial["non_guarantee"]
    assert len(set(source_hashes)) == 2 * EXPECTED_BLOCK_COUNT
    assert report["campaign_disjointness"]["status"] == "complete"
    assert report["campaign_disjointness"]["unresolved"] == []
    assert document.json_bytes == R._canonical_json_bytes(report)


def _independent_markdown_cell(value: object) -> str:
    if type(value) is dict and value.get("availability") == "absent":
        return "不在"
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    else:
        text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", " ")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def test_markdown_provenance_argv_and_required_columns_match_json_rows(
    immutable_publication: _ImmutablePublication,
) -> None:
    document = _document(immutable_publication)
    report = document.json_value
    markdown = document.markdown_bytes.decode("utf-8")
    assert _independent_markdown_cell(
        report["provenance"]["publication_root"]
    ) in markdown
    assert _independent_markdown_cell(
        report["provenance"]["reproduction_argv"]
    ) in markdown
    for artifact in report["provenance"]["artifacts"].values():
        if artifact.get("sha256") is not None:
            assert artifact["sha256"] in markdown

    lines = markdown.splitlines()
    header = "| row | block | arm | campaign | initial snapshot | model/prompt/projection | WAL path/hash | artifact | stop reason | budget | verdict | anomaly class | performance value | precursor red classes | evidence issues |"
    first_row = lines.index(header) + 2
    columns = (
        "row_ordinal", "block_id", "arm", "campaign_id",
        "initial_snapshot_hash", "model_prompt_projection_hash", "wal",
        "planned_attempt_artifact", "stop_reason", "budget_consumption",
        "verdict", "anomaly_class", "performance_value_present",
        "precursor_digest_red_classes", "evidence_issues",
    )
    for offset, row in enumerate(report["rows"]):
        values = []
        for column in columns:
            value = row[column]
            if column == "planned_attempt_artifact":
                value = value["availability"]
            values.append(_independent_markdown_cell(value))
        assert lines[first_row + offset] == "| " + " | ".join(values) + " |"


def test_markdown_escape_orders_backslash_pipe_and_normalizes_cr_lf() -> None:
    value = "left\\|right\r\nnext\rlast\nend"
    assert R._display(value) == _independent_markdown_cell(value)
    assert "\r" not in R._display(value)
    assert "\n" not in R._display(value)


def test_artifact_availability_is_frozen_once_per_planned_leaf(
    monkeypatch: pytest.MonkeyPatch,
    immutable_publication: _ImmutablePublication,
) -> None:
    original = R._observe_artifact_availability
    observations: list[str] = []

    def observe(path: str) -> str:
        observations.append(path)
        return original(path)

    monkeypatch.setattr(R, "_observe_artifact_availability", observe)
    inputs = R._load_and_evaluate(
        Path(immutable_publication.publication.publication_root)
    )
    rows = R._project_rows(inputs)
    R._assert_complete_projection(inputs, rows)
    assert observations == [
        item.artifact_path
        for item in immutable_publication.publication.planned_result_artifacts
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        "terminal-reason",
        "campaign-id",
        "drop-one-arm",
        "duplicate-one-arm",
        "rewrite-source-utf8",
        "anomaly-class-alias",
        "absent-to-zero",
        "remove-transcribed-binding",
    ],
)
def test_m03_m04_m05_m06_m07_m14_m17_m18_public_builder_rejects_projection_mutations(
    monkeypatch: pytest.MonkeyPatch,
    immutable_publication: _ImmutablePublication,
    mutation: str,
) -> None:
    original = R._project_rows

    def mutate(inputs):
        rows = copy.deepcopy(list(original(inputs)))
        if mutation == "terminal-reason":
            rows[0]["stop_reason"]["terminal_reason"] = None
        elif mutation == "campaign-id":
            rows[0]["campaign_id"] = "mutated-campaign"
        elif mutation == "drop-one-arm":
            rows.pop()
        elif mutation == "duplicate-one-arm":
            rows[-1] = copy.deepcopy(rows[0])
        elif mutation == "rewrite-source-utf8":
            rows[0]["source_artifact_utf8"] += " "
        elif mutation == "anomaly-class-alias":
            rows[0]["anomaly_class"] = {
                "availability": "present",
                "value": rows[0]["precursor_digest_red_classes"],
            }
        elif mutation == "absent-to-zero":
            rows[0]["budget_consumption"] = {"availability": "present", "value": 0}
        else:
            assert mutation == "remove-transcribed-binding"
            rows[0]["initial_snapshot_hash"].pop("binding")
        return tuple(rows)

    monkeypatch.setattr(R, "_project_rows", mutate)
    inputs = _inputs(immutable_publication)
    monkeypatch.setattr(R, "_load_and_evaluate", lambda _root: inputs)
    with pytest.raises(R.B4MaterialReportError, match="projection_"):
        R.build_material_report_document(
            immutable_publication.publication.publication_root
        )


@pytest.mark.parametrize("artifact", ["registry", "manifest", "issuer_receipt"])
def test_input_artifact_projection_rejects_one_byte_rewrite_through_public_builder(
    monkeypatch: pytest.MonkeyPatch,
    immutable_publication: _ImmutablePublication,
    artifact: str,
) -> None:
    original = R._build_report_value

    def mutate(inputs, rows, reproduction_argv):
        report = original(inputs, rows, reproduction_argv)
        report["provenance"]["artifacts"][artifact]["utf8"] += " "
        return report

    monkeypatch.setattr(R, "_build_report_value", mutate)
    inputs = _inputs(immutable_publication)
    monkeypatch.setattr(R, "_load_and_evaluate", lambda _root: inputs)
    with pytest.raises(R.B4MaterialReportError, match=artifact):
        R.build_material_report_document(
            immutable_publication.publication.publication_root
        )


def test_m08_floor_absence_runs_existing_evaluator_as_protocol_violation(
    immutable_publication: _ImmutablePublication,
) -> None:
    report = _document(immutable_publication).json_value
    assert "floor" not in inspect.signature(R.build_material_report_document).parameters
    assert "floor" not in inspect.signature(R.write_material_report).parameters
    assert report["floor"] == {
        "availability": "absent",
        "reason": "preregistration_section_5_unfilled",
        "source": None,
        "value": None,
    }
    assert report["report_scope"] == {
        "kind": "evidence-only",
        "preregistration_section_5": "not_in_effect",
        "floor_availability": "absent",
        "expected_analysis_verdict": "protocol_violation",
        "expected_analysis_reason": "floor_domain_error",
        "section_7_1_four_classifications_operationalized": False,
    }
    assert report["analysis"]["status"] == "evaluated"
    assert report["analysis"]["floor_argument"] is None
    assert report["analysis"]["result"]["verdict"] == "protocol_violation"
    assert report["analysis"]["result"]["analysis_invalid"]["reasons"] == [
        "floor_domain_error"
    ]


@pytest.mark.parametrize(
    "verdict",
    ["established", "not_established", "indeterminate", "protocol_violation"],
)
def test_m09_renderer_only_future_compatibility_preserves_four_verdict_wire_values(
    verdict: str,
) -> None:
    """Renderer-only future compatibility; this is not sanctioned-path reachability."""

    report = {
        "schema_version": R.SCHEMA_VERSION,
        "assembly": {"status": "assembled"},
        "analysis": {"status": "evaluated", "result": {"verdict": verdict}},
        "campaign_disjointness": {"status": "complete"},
        "provenance": {
            "publication_root": "/example/publication",
            "reproduction_argv": ["python3", R.GENERATOR_IDENTITY],
            "artifacts": {
                "registry": {},
                "manifest": {},
                "issuer_receipt": {},
                "raw_analysis": {},
            },
        },
        "rows": [],
    }
    rendered = R._render_markdown(report, "0" * 64).decode("utf-8")
    assert f"analysis verdict: `{verdict}`" in rendered
    if verdict == "indeterminate":
        assert "還流に価値なし" not in rendered


def _first_campaign_root(immutable: _ImmutablePublication) -> Path:
    first = _document(immutable).json_value["rows"][0]
    return Path(
        first["source_object"]["evidence"]["campaign_lock"]["path"]
    ).resolve().parent


@pytest.mark.parametrize("direction", ["equal", "below", "above"])
def test_m10_m11_m12_output_campaign_intersection_three_directions_write_nothing(
    immutable_publication: _ImmutablePublication,
    monkeypatch: pytest.MonkeyPatch,
    direction: str,
) -> None:
    campaign = _first_campaign_root(immutable_publication)
    inputs = _inputs(immutable_publication)
    output = {
        "equal": campaign,
        "below": campaign / "material-report-output",
        "above": campaign.parent,
    }[direction]
    monkeypatch.setattr(
        R,
        "_load_and_evaluate",
        lambda _root: inputs,
    )
    with pytest.raises(R.B4MaterialReportError, match="output_campaign_intersection"):
        R.write_material_report(
            immutable_publication.publication.publication_root,
            output_root=output,
        )
    assert not (output / R.REPORT_JSON_NAME).exists()
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_m13_lexical_dotdot_alias_reaches_resolved_campaign_comparison(
    immutable_publication: _ImmutablePublication,
) -> None:
    campaign = _first_campaign_root(immutable_publication)
    output = campaign / "runs" / ".."
    with pytest.raises(R.B4MaterialReportError, match="output_campaign_intersection"):
        R.write_material_report(
            immutable_publication.publication.publication_root,
            output_root=output,
        )
    assert not (campaign / R.REPORT_JSON_NAME).exists()
    assert not (campaign / R.REPORT_MARKDOWN_NAME).exists()
    assert not (campaign / R.REPORT_COMMIT_NAME).exists()


def test_output_symlink_component_is_rejected_before_any_report_write(
    tmp_path: Path,
    immutable_publication: _ImmutablePublication,
) -> None:
    campaign = _first_campaign_root(immutable_publication)
    link = tmp_path / "campaign-link"
    link.symlink_to(campaign, target_is_directory=True)
    output = link / "material-report-output"
    with pytest.raises(R.B4MaterialReportError, match="output_symlink_component"):
        R.write_material_report(
            immutable_publication.publication.publication_root,
            output_root=output,
        )
    assert not (campaign / "material-report-output" / R.REPORT_JSON_NAME).exists()
    assert not (campaign / "material-report-output" / R.REPORT_MARKDOWN_NAME).exists()
    assert not (campaign / "material-report-output" / R.REPORT_COMMIT_NAME).exists()


def test_m15_real_issuer_exception_is_wrapped_with_reason_and_writes_nothing(
    tmp_path: Path,
) -> None:
    output = tmp_path / "issuer-output"
    with pytest.raises(R.B4MaterialReportError, match="publication_rejected") as exc_info:
        R.write_material_report(
            tmp_path / "missing-publication",
            output_root=output,
        )
    assert "publication_root_invalid" in str(exc_info.value)
    assert exc_info.value.__cause__.__class__.__name__ == "B4PrerunIssuerError"
    assert not (output / R.REPORT_JSON_NAME).exists()
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_publication_symlink_alias_remains_rejected_by_existing_loader(
    tmp_path: Path,
    immutable_publication: _ImmutablePublication,
) -> None:
    alias = tmp_path / "publication-alias"
    alias.symlink_to(
        immutable_publication.publication.publication_root,
        target_is_directory=True,
    )
    with pytest.raises(R.B4MaterialReportError, match="publication_root_invalid"):
        R.build_material_report_document(alias)


def test_m15_real_ledger_exception_type_is_wrapped_and_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    immutable_publication: _ImmutablePublication,
) -> None:
    output = tmp_path / "ledger-output"

    def reject_binding(**_kwargs):
        raise ledgers.B4LedgerError("named-ledger-rejection")

    monkeypatch.setattr(R, "build_contract_binding", reject_binding)
    with pytest.raises(R.B4MaterialReportError, match="named-ledger-rejection") as exc_info:
        R.write_material_report(
            immutable_publication.publication.publication_root,
            output_root=output,
        )
    assert isinstance(exc_info.value.__cause__, ledgers.B4LedgerError)
    assert not (output / R.REPORT_JSON_NAME).exists()
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_m16a_existing_pair_is_rejected_before_publication_reload(tmp_path: Path) -> None:
    output = tmp_path / "existing-output"
    output.mkdir()
    (output / R.REPORT_JSON_NAME).write_bytes(b"existing-json")
    (output / R.REPORT_MARKDOWN_NAME).write_bytes(b"existing-md")
    with pytest.raises(R.B4MaterialReportError, match="output_exists"):
        R.write_material_report(
            tmp_path / "publication-that-must-not-be-loaded",
            output_root=output,
        )
    assert (output / R.REPORT_JSON_NAME).read_bytes() == b"existing-json"
    assert (output / R.REPORT_MARKDOWN_NAME).read_bytes() == b"existing-md"


def test_m16b_prepublication_race_check_rejects_new_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    immutable_publication: _ImmutablePublication,
) -> None:
    output = tmp_path / "prepublish-race"
    inputs = _inputs(immutable_publication)
    original = R._assert_output_absent
    observations = 0

    def introduce_race(root: Path) -> None:
        nonlocal observations
        observations += 1
        if observations == 2:
            root.mkdir(parents=True, exist_ok=True)
            (root / R.REPORT_JSON_NAME).write_bytes(b"race-winner")
        original(root)

    monkeypatch.setattr(R, "_assert_output_absent", introduce_race)
    monkeypatch.setattr(
        R,
        "_load_and_evaluate",
        lambda _root: inputs,
    )
    with pytest.raises(R.B4MaterialReportError, match="output_exists"):
        R.write_material_report(
            immutable_publication.publication.publication_root,
            output_root=output,
        )
    assert observations == 2
    assert (output / R.REPORT_JSON_NAME).read_bytes() == b"race-winner"
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_m16c_create_only_link_rejects_collision_without_other_guards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "hard-link-collision"
    output.mkdir()
    target = output / R.REPORT_JSON_NAME
    target.write_bytes(b"existing")
    monkeypatch.setattr(R, "_assert_output_absent", lambda _root: None)
    with pytest.raises(R.B4MaterialReportError, match="output_exists"):
        R._publish_pair_no_overwrite(output, b"new-json", b"new-markdown")
    assert target.read_bytes() == b"existing"
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_commit_marker_is_last_and_binds_both_durable_files(
    tmp_path: Path,
) -> None:
    output = tmp_path / "committed-pair"
    json_bytes = b"json-bytes"
    markdown_bytes = b"markdown-bytes"
    R._publish_pair_no_overwrite(output, json_bytes, markdown_bytes)
    marker = json.loads((output / R.REPORT_COMMIT_NAME).read_bytes())
    assert marker == {
        "schema_version": "p3-b4-material-report-commit/v1",
        "report_json_sha256": hashlib.sha256(json_bytes).hexdigest(),
        "report_markdown_sha256": hashlib.sha256(markdown_bytes).hexdigest(),
    }
    assert (output / R.REPORT_JSON_NAME).read_bytes() == json_bytes
    assert (output / R.REPORT_MARKDOWN_NAME).read_bytes() == markdown_bytes


def test_second_link_failure_rolls_back_pair_and_leaves_no_commit_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "pair-rollback"
    original_link = os.link
    calls = 0

    def fail_second_link(source, target, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected markdown link failure")
        return original_link(source, target, **kwargs)

    monkeypatch.setattr(os, "link", fail_second_link)
    with pytest.raises(R.B4MaterialReportError, match="output_io_error"):
        R._publish_pair_no_overwrite(output, b"json", b"markdown")
    assert calls == 2
    assert not (output / R.REPORT_JSON_NAME).exists()
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_commit_marker_link_failure_rolls_back_both_staged_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "marker-rollback"
    original_link = os.link
    calls = 0

    def fail_commit_link(source, target, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected commit marker link failure")
        return original_link(source, target, **kwargs)

    monkeypatch.setattr(os, "link", fail_commit_link)
    with pytest.raises(R.B4MaterialReportError, match="output_io_error"):
        R._publish_pair_no_overwrite(output, b"json", b"markdown")
    assert calls == 3
    assert not (output / R.REPORT_JSON_NAME).exists()
    assert not (output / R.REPORT_MARKDOWN_NAME).exists()
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_rollback_failure_is_reported_instead_of_suppressed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "rollback-failure"
    original_link = os.link
    original_unlink = Path.unlink
    calls = 0

    def fail_second_link(source, target, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected markdown link failure")
        return original_link(source, target, **kwargs)

    def fail_json_rollback(path: Path, *args, **kwargs):
        if path == output / R.REPORT_JSON_NAME:
            raise OSError("injected rollback failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "link", fail_second_link)
    monkeypatch.setattr(Path, "unlink", fail_json_rollback)
    with pytest.raises(R.B4MaterialReportError, match="output_rollback_error"):
        R._publish_pair_no_overwrite(output, b"json", b"markdown")
    assert (output / R.REPORT_JSON_NAME).read_bytes() == b"json"
    assert not (output / R.REPORT_COMMIT_NAME).exists()


def test_cli_clean_subprocess_runs_twice_and_refuses_overwrite(
    tmp_path: Path,
    immutable_publication: _ImmutablePublication,
) -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    output = tmp_path / "cli-output"
    argv = [
        sys.executable,
        "-B",
        str(Path(R.__file__).resolve()),
        immutable_publication.publication.publication_root,
        "--output-root",
        str(output),
    ]

    first = subprocess.run(
        argv,
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    json_path = output / R.REPORT_JSON_NAME
    markdown_path = output / R.REPORT_MARKDOWN_NAME
    original_json = json_path.read_bytes()
    original_markdown = markdown_path.read_bytes()
    marker_path = output / R.REPORT_COMMIT_NAME
    marker = json.loads(marker_path.read_bytes())
    digest = hashlib.sha256(original_json).hexdigest()
    assert f"report JSON SHA-256: `{digest}`" in original_markdown.decode("utf-8")
    assert marker["report_json_sha256"] == digest
    assert marker["report_markdown_sha256"] == hashlib.sha256(original_markdown).hexdigest()

    second = subprocess.run(
        argv,
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert second.returncode != 0
    assert "output_exists" in second.stderr
    assert json_path.read_bytes() == original_json
    assert markdown_path.read_bytes() == original_markdown
    assert json.loads(marker_path.read_bytes()) == marker


def test_outputs_contain_no_combining_diacritic_codepoints(
    immutable_publication: _ImmutablePublication,
) -> None:
    document = _document(immutable_publication)
    for text in (
        document.json_bytes.decode("utf-8"),
        document.markdown_bytes.decode("utf-8"),
    ):
        assert not any("\u0300" <= character <= "\u036f" for character in text)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
