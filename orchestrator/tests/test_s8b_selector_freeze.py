from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign.s8b_descriptor import descriptor_for_holdout
from orchestrator.campaign.s8b_selector_freeze import (
    SelectorFreezeError,
    binding_entry_for_choice,
    build_prediction_freeze,
    build_prediction_jobs,
    record_agent_attempt,
    selector_basis_sha256,
    verify_prediction_freeze,
    write_prediction_freeze,
)
from orchestrator.campaign.s8b_selector_input import (
    CHOICE_TO_BINDING,
    STATIC_DEFAULT_CHOICE_ID,
    build_selector_payload,
)


ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"
ARMS = {"on", "off", "swapped"}


def _freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _raw(choice_id: str, rationale: str = "descriptor と機構の適合を比較した") -> str:
    return json.dumps(
        {
            "schema_version": "8b-selector-output/v1",
            "choice_id": choice_id,
            "rationale": rationale,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _rows(
    freeze: dict, *, role_sha256: str | None = None, root: Path | None = None,
) -> list[dict]:
    choices = tuple(CHOICE_TO_BINDING)
    role_sha256 = role_sha256 or hashlib.sha256(b"role").hexdigest()
    rows = []
    agent_index = 0
    for job in build_prediction_jobs(freeze):
        if job["arm"] == "off":
            rows.append({
                **job,
                "status": "valid",
                "rationale": None,
                "raw_response_path": None,
                "raw_sha256": None,
                "parser_error_code": None,
                "agent_provenance": None,
            })
            continue
        raw = _raw(choices[agent_index])
        attempt = record_agent_attempt(job=job, raw_output=raw)
        raw_response_path = f"selector-runs/cell-{agent_index}.json"
        if root is not None:
            destination = root / raw_response_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(raw, encoding="utf-8")
        rows.append({
            **job,
            **attempt,
            "parser_error_code": attempt.get("parser_error_code"),
            "raw_response_path": raw_response_path,
            "agent_provenance": {
                "child_id": f"child-{agent_index}",
                "role_file_sha256": role_sha256,
                "model": "fixture-model",
                "started_at": f"2026-07-16T00:00:0{agent_index}Z",
                "finished_at": f"2026-07-16T00:01:0{agent_index}Z",
                "fresh_context": True,
                "declared_tools": [],
                "observed_tool_events": [],
            },
        })
        agent_index += 1
    return rows


def _sources(root: Path | None = None) -> dict:
    names = ("holdout_freeze", "builder", "role", "input_schema", "output_schema")
    if root is not None:
        originals = {
            "holdout_freeze": FREEZE_PATH,
            "builder": ROOT / "orchestrator/campaign/s8b_selector_input.py",
            "role": ROOT / ".claude/agents/selector-8b.md",
            "input_schema": ROOT / "orchestrator/campaign/s8b_selector_catalog.json",
            "output_schema": ROOT / "orchestrator/campaign/s8b_selector_output_schema.json",
        }
        records = {}
        for name in names:
            destination = root / "source" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(originals[name].read_bytes())
            records[name] = {
                "path": f"source/{name}",
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            }
        return records
    return {
        name: {"path": f"source/{name}", "sha256": hashlib.sha256(name.encode()).hexdigest()}
        for name in names
    }


def _policy() -> dict:
    return {
        "attempts_per_agent_cell": 1,
        "retry": False,
        "reuse_equal_payload_output": False,
        "fresh_context": True,
        "declared_tools": [],
    }


def _document(
    freeze: dict, rows: list[dict] | None = None, *, root: Path | None = None,
) -> dict:
    sources = _sources(root)
    return build_prediction_freeze(
        freeze=freeze,
        rows=(_rows(freeze, role_sha256=sources["role"]["sha256"], root=root)
              if rows is None else rows),
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head="a" * 40,
        sources=sources,
        execution_policy=_policy(),
    )


def _rehash(document: dict) -> None:
    body = {key: value for key, value in document.items() if key != "body_sha256"}
    rendered = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    document["body_sha256"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def test_build_prediction_jobs_has_six_complete_cells_and_static_off() -> None:
    freeze = _freeze()
    jobs = build_prediction_jobs(freeze)

    assert len(jobs) == 6
    cells = {(job["target_holdout"], job["arm"]) for job in jobs}
    assert cells == {(target, arm) for target in freeze["holdouts"] for arm in ARMS}
    off = [job for job in jobs if job["arm"] == "off"]
    assert len(off) == 2
    assert all(job["decision_method"] == "static_default" for job in off)
    assert all(job["choice_id"] == STATIC_DEFAULT_CHOICE_ID for job in off)
    assert all(job["descriptor_source_holdout"] is None for job in off)
    assert all(job["input_payload_sha256"] is None for job in off)


def test_swapped_uses_deranged_descriptor_without_payload_identity_fields() -> None:
    freeze = _freeze()
    jobs = build_prediction_jobs(freeze)

    for job in jobs:
        if job["arm"] == "off":
            continue
        expected_source = (
            job["target_holdout"]
            if job["arm"] == "on"
            else freeze["derangement"][job["target_holdout"]]
        )
        assert job["descriptor_source_holdout"] == expected_source
        payload = build_selector_payload(
            descriptor_for_holdout(freeze["holdouts"][expected_source])
        )
        assert "arm" not in payload
        assert "target_holdout" not in payload
        rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert all(target not in rendered for target in freeze["holdouts"])


def test_record_agent_attempt_valid_and_invalid_never_falls_back() -> None:
    job = next(job for job in build_prediction_jobs(_freeze()) if job["arm"] == "on")
    valid = record_agent_attempt(job=job, raw_output=_raw("c02"))
    invalid = record_agent_attempt(job=job, raw_output="not json")

    assert valid["status"] == "valid"
    assert valid["choice_id"] == "c02"
    assert valid["rationale"]
    assert invalid["status"] == "invalid"
    assert invalid["choice_id"] is None
    assert invalid["parser_error_code"]
    assert invalid["raw_sha256"]
    assert STATIC_DEFAULT_CHOICE_ID not in invalid.values()


def test_binding_resolution_is_target_local_and_unknown_choice_fails() -> None:
    freeze = _freeze()
    for target in freeze["holdouts"]:
        entry = binding_entry_for_choice(freeze, target, "c01")
        key = CHOICE_TO_BINDING["c01"]
        assert entry == freeze["holdouts"][target]["variant_binding"]["entries"][key]
        assert entry is not freeze["holdouts"][target]["variant_binding"]["entries"][key]
    with pytest.raises(SelectorFreezeError, match="unknown selector choice_id"):
        binding_entry_for_choice(freeze, next(iter(freeze["holdouts"])), "c99")


def test_build_prediction_freeze_requires_complete_unique_cells() -> None:
    freeze = _freeze()
    rows = _rows(freeze)
    document = _document(freeze, rows)
    assert len(document["rows"]) == 6

    with pytest.raises(SelectorFreezeError, match="ちょうど6行"):
        _document(freeze, rows[:-1])
    duplicate = copy.deepcopy(rows)
    duplicate[-1] = copy.deepcopy(duplicate[0])
    with pytest.raises(SelectorFreezeError, match="重複"):
        _document(freeze, duplicate)


def test_build_prediction_freeze_rejects_tagged_union_violations() -> None:
    freeze = _freeze()
    off_provenance = _rows(freeze)
    off = next(row for row in off_provenance if row["arm"] == "off")
    off["agent_provenance"] = {"child_id": "forbidden"}
    with pytest.raises(SelectorFreezeError, match="off row に agent provenance"):
        _document(freeze, off_provenance)

    agent_static = _rows(freeze)
    agent = next(row for row in agent_static if row["arm"] == "on")
    agent["decision_method"] = "static_default"
    with pytest.raises(SelectorFreezeError, match="固定 job と不一致"):
        _document(freeze, agent_static)


def test_swapped_expectations_are_derived_only_from_deranged_on_rows() -> None:
    freeze = _freeze()
    document = _document(freeze)
    on_choices = {
        row["target_holdout"]: row["choice_id"]
        for row in document["rows"] if row["arm"] == "on"
    }
    expectations = {
        item["target_holdout"]: item for item in document["swapped_follow_expectations"]
    }
    for target, source in freeze["derangement"].items():
        assert expectations[target]["source_on_holdout"] == source
        assert expectations[target]["expected_choice_id"] == on_choices[source]


def test_verify_detects_body_row_derangement_and_basis_tampering(tmp_path: Path) -> None:
    freeze = _freeze()
    document = _document(freeze, root=tmp_path)
    verify_prediction_freeze(document, freeze=freeze, root=tmp_path)

    body_tampered = copy.deepcopy(document)
    body_tampered["generated_at"] = "changed"
    with pytest.raises(SelectorFreezeError, match="body_sha256"):
        verify_prediction_freeze(body_tampered, freeze=freeze, root=tmp_path)

    row_tampered = copy.deepcopy(document)
    valid_agent = next(
        row for row in row_tampered["rows"]
        if row["arm"] == "on" and row["status"] == "valid"
    )
    valid_agent["choice_id"] = "c06"
    _rehash(row_tampered)
    with pytest.raises(SelectorFreezeError, match="binding_key"):
        verify_prediction_freeze(row_tampered, freeze=freeze, root=tmp_path)

    derangement_tampered = copy.deepcopy(document)
    first = next(iter(derangement_tampered["derangement"]))
    derangement_tampered["derangement"][first] = first
    _rehash(derangement_tampered)
    with pytest.raises(SelectorFreezeError, match="derangement"):
        verify_prediction_freeze(derangement_tampered, freeze=freeze, root=tmp_path)

    changed_freeze = copy.deepcopy(freeze)
    target = next(iter(changed_freeze["holdouts"]))
    key = next(iter(CHOICE_TO_BINDING.values()))
    changed_freeze["holdouts"][target]["variant_binding"]["entries"][key]["test_change"] = True
    with pytest.raises(SelectorFreezeError, match="selector_basis_sha256"):
        verify_prediction_freeze(document, freeze=changed_freeze, root=tmp_path)


def test_verify_binds_role_raw_and_exact_agent_provenance_to_files(tmp_path: Path) -> None:
    freeze = _freeze()

    role_root = tmp_path / "role-case"
    role_document = _document(freeze, root=role_root)
    role_path = role_root / role_document["sources"]["role"]["path"]
    role_path.write_bytes(role_path.read_bytes() + b"x")
    with pytest.raises(SelectorFreezeError, match="sources.role.sha256"):
        verify_prediction_freeze(role_document, freeze=freeze, root=role_root)

    raw_root = tmp_path / "raw-case"
    raw_document = _document(freeze, root=raw_root)
    raw_row = next(row for row in raw_document["rows"] if row["arm"] == "on")
    raw_path = raw_root / raw_row["raw_response_path"]
    raw_path.write_bytes(raw_path.read_bytes() + b"x")
    with pytest.raises(SelectorFreezeError, match="raw_response.sha256"):
        verify_prediction_freeze(raw_document, freeze=freeze, root=raw_root)

    provenance_root = tmp_path / "provenance-case"
    provenance_document = _document(freeze, root=provenance_root)
    provenance_row = next(
        row for row in provenance_document["rows"] if row["arm"] == "on"
    )
    provenance_row["agent_provenance"].pop("model")
    _rehash(provenance_document)
    with pytest.raises(SelectorFreezeError, match="agent_provenance schema"):
        verify_prediction_freeze(
            provenance_document, freeze=freeze, root=provenance_root,
        )


def test_selector_basis_ignores_floor_budget_but_binds_variant_entries() -> None:
    freeze = _freeze()
    baseline = selector_basis_sha256(freeze)

    floor_budget_changed = copy.deepcopy(freeze)
    floor_budget_changed["floor"] = {"future": 1}
    floor_budget_changed["budget"] = {"future": 2}
    assert selector_basis_sha256(floor_budget_changed) == baseline

    binding_changed = copy.deepcopy(freeze)
    target = next(iter(binding_changed["holdouts"]))
    key = next(iter(CHOICE_TO_BINDING.values()))
    binding_changed["holdouts"][target]["variant_binding"]["entries"][key]["future"] = 1
    assert selector_basis_sha256(binding_changed) != baseline


def test_write_prediction_freeze_is_atomic_exclusive_create(tmp_path: Path) -> None:
    document = _document(_freeze())
    destination = tmp_path / "nested" / "prediction.json"
    write_prediction_freeze(destination, document)
    assert json.loads(destination.read_text(encoding="utf-8")) == document

    with pytest.raises(SelectorFreezeError, match="既に存在"):
        write_prediction_freeze(destination, document)
    assert json.loads(destination.read_text(encoding="utf-8")) == document
