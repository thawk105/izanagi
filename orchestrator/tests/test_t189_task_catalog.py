from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.t189_task_catalog import (
    TaskCatalogError,
    build_task_catalog,
    task_catalog_bytes,
    validate_task_catalog,
)


GOOD_COMMIT = "a" * 40
MISSING_COMMIT = "b" * 40


def _reverse_key_order(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _reverse_key_order(item)
            for key, item in reversed(list(value.items()))
        }
    if isinstance(value, list):
        return [_reverse_key_order(item) for item in value]
    return value


def _json_bytes(value: object, *, reverse_keys: bool = False) -> bytes:
    if reverse_keys:
        value = _reverse_key_order(value)
    return json.dumps(
        value, ensure_ascii=False, sort_keys=False, separators=(",", ":"),
    ).encode("utf-8")


def _classification(*, reverse_keys: bool = False) -> bytes:
    artifact = {
        "artifact_kind": "t189-task-type-classification",
        "classifications": [{
            "evidence": {
                "kind": "worklog-entry",
                "line": 7,
                "path": "docs/archive/worklog-fixture.md",
                "relative_to": "repository-root",
            },
            "rationale": "fixture の新規機構",
            "rule_id": "TT-NEW-01",
            "task_type": "new-mechanism",
            "task_type_status": "classified",
            "tie_break_applied": False,
            "wave_id": "wave-a",
        }],
        "criteria_document": "docs/phase3-t189-task-catalog-classification.md",
        "criteria_version": "t189-task-type/v1",
        "schema_version": 1,
    }
    return _json_bytes(artifact, reverse_keys=reverse_keys)


def _receipt(
    *,
    schema_version: object,
    stage: str,
    prompt_sha256: str,
    base_commit: str = GOOD_COMMIT,
) -> bytes:
    # The extra fields prove that this tool checks only the receipt fields it
    # reads; it does not fork the receipt's closed-schema authority.
    return _json_bytes({
        "schema_version": schema_version,
        "stage": stage,
        "prompt_sha256": prompt_sha256,
        "base_commit": base_commit,
        "future_receipt_field": {"wall_clock_s": 1.25},
    })


def _write_receipt(
    jobs_root: Path,
    wave_id: str,
    job_id: str,
    *,
    schema_version: object,
    stage: str,
    prompt_sha256: str,
    base_commit: str = GOOD_COMMIT,
) -> Path:
    path = jobs_root / wave_id / job_id / "receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_receipt(
        schema_version=schema_version,
        stage=stage,
        prompt_sha256=prompt_sha256,
        base_commit=base_commit,
    ))
    return path


def _write_prompt(jobs_root: Path, wave_id: str, name: str, body: str) -> str:
    path = jobs_root / wave_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = body.encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _materialize_fixture(
    root: Path, *, reverse_creation: bool = False, reverse_classification: bool = False,
) -> tuple[Path, Path, Path]:
    jobs_root = root / "jobs"
    repo_root = root / "repo"
    jobs_root.mkdir(parents=True)
    repo_root.mkdir()
    classification = root / "classification.json"
    classification.write_bytes(_classification(reverse_keys=reverse_classification))

    prompts = {
        ("wave-a", "plan.md"): "Plan a fixture mechanism.",
        ("wave-a", "author.md"): (
            "Author T-189 model-routing work with gpt-5.6-sol and "
            "routing_evidence_status."
        ),
        ("wave-b", "plan.md"): "Only one dev-wave stage exists.",
        ("wave-c", "plan.md"): "Recoverable plan prompt.",
        ("wave-c", "wrong-author.md"): "This does not match the author digest.",
        ("wave-d", "plan.md"): "Unclassified plan.",
        ("wave-d", "author.md"): "Unclassified author.",
        ("wave-e", "plan.md"): "Unresolvable base plan.",
        ("wave-e", "author.md"): "Unresolvable base author.",
    }
    digests: dict[tuple[str, str], str] = {}
    prompt_items = list(prompts.items())
    if reverse_creation:
        prompt_items.reverse()
    for (wave_id, name), body in prompt_items:
        digests[(wave_id, name)] = _write_prompt(jobs_root, wave_id, name, body)

    rows = [
        ("wave-a", "job-plan-z", 3, "plan", digests[("wave-a", "plan.md")], GOOD_COMMIT),
        ("wave-a", "job-plan-a", 3, "plan", digests[("wave-a", "plan.md")], GOOD_COMMIT),
        ("wave-a", "job-author", 4, "author", digests[("wave-a", "author.md")], GOOD_COMMIT),
        ("wave-a", "job-old", 2, "plan", digests[("wave-a", "plan.md")], GOOD_COMMIT),
        ("wave-a", "job-review", 3, "review", digests[("wave-a", "plan.md")], GOOD_COMMIT),
        ("wave-b", "job-plan", 3, "plan", digests[("wave-b", "plan.md")], GOOD_COMMIT),
        ("wave-c", "job-plan", 3, "plan", digests[("wave-c", "plan.md")], GOOD_COMMIT),
        ("wave-c", "job-author", 3, "author", "c" * 64, GOOD_COMMIT),
        ("wave-d", "job-plan", 3, "plan", digests[("wave-d", "plan.md")], GOOD_COMMIT),
        ("wave-d", "job-author", 3, "author", digests[("wave-d", "author.md")], GOOD_COMMIT),
        ("wave-e", "job-plan", 3, "plan", digests[("wave-e", "plan.md")], MISSING_COMMIT),
        ("wave-e", "job-author", 3, "author", digests[("wave-e", "author.md")], MISSING_COMMIT),
    ]
    if reverse_creation:
        rows.reverse()
    for wave_id, job_id, schema, stage, prompt_sha, base in rows:
        _write_receipt(
            jobs_root, wave_id, job_id,
            schema_version=schema,
            stage=stage,
            prompt_sha256=prompt_sha,
            base_commit=base,
        )

    acceptance_rows = [
        ("acceptance-receipt-2.json", "child-green"),
        ("acceptance-receipt-1.json", "child-red"),
    ]
    if reverse_creation:
        acceptance_rows.reverse()
    for name, verdict in acceptance_rows:
        (jobs_root / "wave-a" / name).write_bytes(_json_bytes({
            "schema_version": "fixture/v1", "verdict": verdict,
        }))
    (jobs_root / "wave-a" / "acceptance-receipt-2.json.acceptance-red-check.json").write_bytes(
        _json_bytes({"verdict": "must-not-be-primary"})
    )
    return jobs_root, repo_root, classification


def _build(paths: tuple[Path, Path, Path]) -> dict[str, object]:
    jobs_root, repo_root, classification = paths
    return build_task_catalog(
        jobs_root,
        repo_root,
        classification,
        commit_resolver=lambda _repo, commit: commit == GOOD_COMMIT,
    )


def _candidate(
    artifact: dict[str, object], wave_id: str, stage: str, ordinal: int = 0,
) -> dict[str, object]:
    return next(
        row for row in artifact["candidates"]
        if row["wave_id"] == wave_id
        and row["dev_wave_stage"] == stage
        and row["receipt_ordinal"] == ordinal
    )


def test_positive_fixture_builds_physical_receipt_catalog(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))

    assert artifact["schema_version"] == "t189-task-catalog/v1"
    assert artifact["counts"] == {
        "paired_stage_wave_count": 4,
        "prompt_recoverable_wave_count": 3,
        "candidate_receipt_count": 5,
        "excluded_receipt_count": 7,
        "candidate_receipts_by_task_type": {
            "new-mechanism": 3,
            "bug-fix": 0,
            "check-or-test": 0,
            "docs": 0,
            "unclassified": 2,
        },
    }
    plan = _candidate(artifact, "wave-a", "plan")
    assert plan["receipt_schema_version"] == 3
    assert plan["base_commit"] == GOOD_COMMIT
    assert plan["base_commit_resolvable"] is True
    assert plan["task_type"] == "new-mechanism"
    assert plan["rule_id"] == "TT-NEW-01"
    assert plan["evidence"] == {
        "kind": "worklog-entry",
        "path": "docs/archive/worklog-fixture.md",
        "relative_to": "repository-root",
        "line": 7,
    }

    acceptance = plan["primary_acceptance_receipt"]
    assert acceptance["present"] is True
    assert [row["jobs_relative_path"] for row in acceptance["records"]] == [
        "wave-a/acceptance-receipt-1.json",
        "wave-a/acceptance-receipt-2.json",
    ]
    assert [row["verdict"] for row in acceptance["records"]] == [
        "child-red", "child-green",
    ]


def test_mut1_unknown_evidence_is_never_rewritten_as_a_value(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    row = _candidate(artifact, "wave-a", "author")

    assert row["oracle_finding_count"] == {
        "evidence_status": "not-established",
        "blocked_on": "§8 oracle ledger (未実装)",
    }
    assert row["t189_stage_boundary"] == {
        "evidence_status": "not-established",
        "blocked_on": "§5.3 stage2/stage5 replayer 契約 (未登録)",
    }
    assert row["replay_artifact_sufficiency"] == {
        "evidence_status": "not-established",
        "blocked_on": "§5.3 replayer 契約 (未登録)",
    }
    for field in (
        "oracle_finding_count", "t189_stage_boundary",
        "replay_artifact_sufficiency",
    ):
        assert row[field] not in (0, False, "none-required")

    mutated = copy.deepcopy(artifact)
    mutated["candidates"][0]["oracle_finding_count"] = 0
    with pytest.raises(TaskCatalogError, match="oracle_finding_count"):
        validate_task_catalog(mutated)


def test_mut2_every_same_stage_receipt_has_count_and_ordinal(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    plans = [
        row for row in artifact["candidates"]
        if row["wave_id"] == "wave-a" and row["dev_wave_stage"] == "plan"
    ]

    assert len(plans) == 2
    assert [row["wave_stage_receipt_count"] for row in plans] == [2, 2]
    assert [row["receipt_ordinal"] for row in plans] == [0, 1]
    assert [row["receipt"]["jobs_relative_path"] for row in plans] == [
        "wave-a/job-plan-a/receipt.json",
        "wave-a/job-plan-z/receipt.json",
    ]


def test_catalog_rejects_missing_physical_receipt_row(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    removed = next(
        row for row in artifact["candidates"]
        if row["wave_id"] == "wave-a"
        and row["dev_wave_stage"] == "plan"
        and row["receipt_ordinal"] == 1
    )
    artifact["candidates"].remove(removed)
    artifact["counts"]["candidate_receipt_count"] -= 1
    artifact["counts"]["candidate_receipts_by_task_type"]["new-mechanism"] -= 1

    with pytest.raises(
        TaskCatalogError,
        match="wave_stage_receipt_count.*candidate and excluded row count mismatch",
    ):
        validate_task_catalog(artifact)


@pytest.mark.parametrize("candidate_ordinal", [0, 1])
def test_catalog_accepts_reasoned_exclusion_consuming_an_ordinal(
    tmp_path: Path, candidate_ordinal: int,
) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    excluded_ordinal = 1 - candidate_ordinal
    removed = _candidate(artifact, "wave-a", "plan", ordinal=excluded_ordinal)
    artifact["candidates"].remove(removed)
    artifact["excluded"].append({
        "wave_id": removed["wave_id"],
        "receipt": removed["receipt"],
        "receipt_schema_version": removed["receipt_schema_version"],
        "dev_wave_stage": removed["dev_wave_stage"],
        "reason_codes": ["prompt-body-unrecoverable"],
    })
    artifact["counts"]["candidate_receipt_count"] -= 1
    artifact["counts"]["excluded_receipt_count"] += 1
    artifact["counts"]["candidate_receipts_by_task_type"]["new-mechanism"] -= 1

    validated = validate_task_catalog(artifact)

    plan = _candidate(validated, "wave-a", "plan", ordinal=candidate_ordinal)
    assert plan["wave_stage_receipt_count"] == 2
    assert any(
        row["receipt"]["jobs_relative_path"]
        == removed["receipt"]["jobs_relative_path"]
        and row["reason_codes"] == ["prompt-body-unrecoverable"]
        for row in validated["excluded"]
    )


def test_catalog_rejects_duplicate_receipt_ordinal(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    row = _candidate(artifact, "wave-a", "plan", ordinal=1)
    row["receipt_ordinal"] = 0

    with pytest.raises(TaskCatalogError, match="receipt_ordinal.*unique within wave-stage"):
        validate_task_catalog(artifact)


def test_catalog_rejects_inconsistent_wave_stage_receipt_count(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    row = _candidate(artifact, "wave-a", "plan", ordinal=1)
    row["wave_stage_receipt_count"] = 3

    with pytest.raises(TaskCatalogError, match="wave_stage_receipt_count.*agree"):
        validate_task_catalog(artifact)


def test_catalog_rejects_receipt_ordinal_outside_declared_count(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    row = _candidate(artifact, "wave-a", "plan", ordinal=1)
    row["receipt_ordinal"] = 2

    with pytest.raises(TaskCatalogError, match="receipt_ordinal.*outside stage receipt count"):
        validate_task_catalog(artifact)


def test_mut3_v4_is_a_candidate_and_other_schema_is_excluded(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    assert _candidate(artifact, "wave-a", "author")["receipt_schema_version"] == 4

    old = next(
        row for row in artifact["excluded"]
        if row["receipt"]["jobs_relative_path"] == "wave-a/job-old/receipt.json"
    )
    assert old["receipt_schema_version"] == 2
    assert old["reason_codes"] == ["unsupported-receipt-schema"]


def test_mut4_prompt_sha_mismatch_never_supplies_a_candidate(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))

    assert not any(row["wave_id"] == "wave-c" for row in artifact["candidates"])
    excluded = [row for row in artifact["excluded"] if row["wave_id"] == "wave-c"]
    assert len(excluded) == 2
    assert all("prompt-body-unrecoverable" in row["reason_codes"] for row in excluded)


def test_mut5_model_slug_contamination_is_recorded_not_auto_excluded(
    tmp_path: Path,
) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    author = _candidate(artifact, "wave-a", "author")

    assert author["model_slug_contamination"] == {
        "scanned_surfaces": [{
            "surface": "prompt-body",
            "jobs_relative_path": "wave-a/author.md",
            "relative_to": "jobs-root",
            "detected": True,
            "matches": ["gpt-5.6-sol"],
        }],
        "unscanned_surfaces": [
            {
                "surface": "snapshot",
                "evidence_status": "not-established",
                "blocked_on": "§5.3 replayer 契約 (未登録)",
            },
            {
                "surface": "artifact",
                "evidence_status": "not-established",
                "blocked_on": "§5.3 replayer 契約 (未登録)",
            },
        ],
    }
    assert author["t189_design_work_markers"] == [
        "T-189", "model-routing", "routing_evidence_status",
    ]


@pytest.mark.parametrize("surface_index", [0, 1], ids=["snapshot", "artifact"])
def test_unscanned_slug_surfaces_cannot_claim_established_evidence(
    tmp_path: Path, surface_index: int,
) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    contamination = artifact["candidates"][0]["model_slug_contamination"]
    contamination["unscanned_surfaces"][surface_index]["evidence_status"] = "established"

    with pytest.raises(TaskCatalogError, match="evidence_status.*not-established"):
        validate_task_catalog(artifact)


def test_missing_classification_is_explicitly_unclassified(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    row = _candidate(artifact, "wave-d", "plan")

    assert row["task_type"] is None
    assert row["task_type_status"] == "unclassified"
    assert row["task_type_reason"] == "not-classified-in-this-generation"
    assert row["rule_id"] is None
    assert row["evidence"] is None


def test_all_noncandidate_receipts_remain_with_reason_codes(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    by_path = {
        row["receipt"]["jobs_relative_path"]: row
        for row in artifact["excluded"]
    }

    assert by_path["wave-a/job-review/receipt.json"]["reason_codes"] == [
        "unsupported-dev-wave-stage",
    ]
    assert "missing-paired-stage" in by_path[
        "wave-b/job-plan/receipt.json"
    ]["reason_codes"]
    assert all(
        "base-commit-unresolvable" in by_path[path]["reason_codes"]
        for path in (
            "wave-e/job-plan/receipt.json",
            "wave-e/job-author/receipt.json",
        )
    )


def test_directory_creation_and_classification_key_order_do_not_change_bytes(
    tmp_path: Path,
) -> None:
    left = _build(_materialize_fixture(tmp_path / "left"))
    right = _build(_materialize_fixture(
        tmp_path / "right",
        reverse_creation=True,
        reverse_classification=True,
    ))

    left_bytes = task_catalog_bytes(left)
    right_bytes = task_catalog_bytes(right)
    assert left_bytes == right_bytes
    assert left_bytes.endswith(b"\n")
    assert not left_bytes.endswith(b"\n\n")
    assert b"\n" not in left_bytes[:-1]


def test_injected_commit_resolver_never_invokes_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _materialize_fixture(tmp_path)

    def forbidden_run(*_args, **_kwargs):
        raise AssertionError("git must not run in fixture tests")

    monkeypatch.setattr("tools.t189_task_catalog.subprocess.run", forbidden_run)
    artifact = _build(paths)
    assert artifact["counts"]["candidate_receipt_count"] == 5


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("paired_stage_wave_count", 0),
        ("paired_stage_wave_count", 999),
        ("prompt_recoverable_wave_count", 0),
        ("prompt_recoverable_wave_count", 999),
    ],
)
def test_funnel_counts_must_match_the_catalog_rows(
    tmp_path: Path, field: str, bad_value: int,
) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    artifact["counts"][field] = bad_value

    with pytest.raises(TaskCatalogError, match=rf"{field}.*count mismatch"):
        validate_task_catalog(artifact)


@pytest.mark.parametrize("bad_number", [1.5, float("nan")])
def test_float_and_nan_catalog_values_are_rejected(
    tmp_path: Path, bad_number: float,
) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    artifact["counts"]["paired_stage_wave_count"] = bad_number
    with pytest.raises(TaskCatalogError, match="float"):
        validate_task_catalog(artifact)


def test_duplicate_json_key_is_rejected(tmp_path: Path) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification.write_bytes(
        b'{"artifact_kind":"t189-task-type-classification",'
        b'"artifact_kind":"duplicate"}'
    )
    with pytest.raises(TaskCatalogError, match="strict JSON"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


def test_nan_json_input_is_rejected(tmp_path: Path) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification.write_bytes(_classification().replace(
        b'"schema_version":1',
        b'"schema_version":NaN',
    ))
    with pytest.raises(TaskCatalogError, match="strict JSON"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


def test_decimal_json_input_field_is_rejected(tmp_path: Path) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification.write_bytes(_classification().replace(
        b'"schema_version":1',
        b'"schema_version":1.5',
    ))
    with pytest.raises(TaskCatalogError, match="Decimal"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


def test_unknown_fields_are_rejected_in_input_and_catalog(tmp_path: Path) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification_value = json.loads(_classification())
    classification_value["unknown"] = "forbidden"
    classification.write_bytes(_json_bytes(classification_value))
    with pytest.raises(TaskCatalogError, match="field set"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )

    artifact = _build(_materialize_fixture(tmp_path / "catalog"))
    artifact["candidates"][0]["unknown"] = "forbidden"
    with pytest.raises(TaskCatalogError, match="field set"):
        validate_task_catalog(artifact)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("classifier", "fixture manager"),
        ("independent_classifiers", 0),
        ("signatures", None),
    ],
)
def test_forbidden_classifier_metadata_fields_are_rejected(
    tmp_path: Path, field: str, value: object,
) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification_value = json.loads(_classification())
    classification_value[field] = value
    classification.write_bytes(_json_bytes(classification_value))

    with pytest.raises(TaskCatalogError, match="classification-artifact: field set mismatch"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


def test_rule_id_must_map_to_task_type(tmp_path: Path) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification_value = json.loads(_classification())
    classification_value["classifications"][0]["task_type"] = "docs"
    classification.write_bytes(_json_bytes(classification_value))

    with pytest.raises(TaskCatalogError, match="rule_id.*does not map to task_type"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("criteria_document", "docs/not-the-criteria.md"),
        ("criteria_version", "t189-task-type/v2"),
    ],
)
def test_classification_criteria_identity_is_fixed(
    tmp_path: Path, field: str, bad_value: str,
) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    classification_value = json.loads(_classification())
    classification_value[field] = bad_value
    classification.write_bytes(_json_bytes(classification_value))

    with pytest.raises(TaskCatalogError, match=rf"{field}.*criteria mismatch"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


def test_task_type_must_be_consistent_within_a_wave(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    author = _candidate(artifact, "wave-a", "author")
    author["task_type"] = "docs"
    author["rule_id"] = "TT-DOCS-01"

    with pytest.raises(TaskCatalogError, match="task_type.*consistent within a wave"):
        validate_task_catalog(artifact)


def test_catalog_path_records_fix_their_relative_base(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))
    assert artifact["candidates"][0]["receipt"]["relative_to"] == "jobs-root"
    artifact["candidates"][0]["receipt"]["relative_to"] = "repository-root"

    with pytest.raises(TaskCatalogError, match="relative_to.*jobs-root"):
        validate_task_catalog(artifact)


def test_receipt_duplicate_key_is_rejected_even_without_closed_schema(
    tmp_path: Path,
) -> None:
    jobs_root, repo_root, classification = _materialize_fixture(tmp_path)
    receipt = jobs_root / "wave-a" / "job-author" / "receipt.json"
    receipt.write_bytes(
        b'{"schema_version":4,"schema_version":3,"stage":"author"}'
    )
    with pytest.raises(TaskCatalogError, match="strict JSON"):
        build_task_catalog(
            jobs_root, repo_root, classification,
            commit_resolver=lambda _repo, _commit: True,
        )


def test_schema_keys_never_claim_final_task_admission(tmp_path: Path) -> None:
    artifact = _build(_materialize_fixture(tmp_path))

    def keys(value: object):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    assert not {"included", "eligible", "selected"}.intersection(keys(artifact))
