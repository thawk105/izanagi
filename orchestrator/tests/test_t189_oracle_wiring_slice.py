# -*- coding: utf-8 -*-
"""Closed-schema, join, provenance, and CLI checks for the T-189 wiring slice.

Mutation anchors:
OR-M1 is owned by the production-loader pin node in test_codex_reasoning_ab.py.
OR-M2 is owned by the production command-dispatch node in that same file.
OR-M3 is owned by the object projection nodes in both suites.
OR-M4 is owned by test_or_m4_receipt_ordinal_is_needed_for_unique_join.
OR-M5 is owned by test_or_m5_physical_prompt_byte_change_has_one_sha_reason.
OR-M6 diagnostic and dual-layer correctness anchors live in the core suite.
OR-M7 has no valid-from-acceptance production branch; its exact status is a
positive downstream invariant in the checked-slice CLI nodes.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

from tools.dev_waves.schema import strict_loads, DEFAULT_MAX_JSON_BYTES
from tools import t189_oracle_wiring_slice as TOOL
from tools import t189_task_catalog as CATALOG


_ROOT = Path(__file__).resolve().parents[2]
_SLICE = _ROOT / "output/t189-routing-preregistration/task-oracle-wiring-slice-v1.json"
_CATALOG = _ROOT / "output/t189-routing-preregistration/task-catalog-v1.json"
_CLASSIFICATION = (
    _ROOT
    / "output/t189-routing-preregistration/task-type-classification-v1.json"
)
_JOBS_ROOT = Path("/work/1/SFC/tanab/dev-wave-jobs")
_PINNED_SLICE_SHA256 = (
    "96a39ee259f985525df0a1206665dd331eb23b24e365b84e4558bfe115e75767"
)


def _slice_value() -> dict[str, Any]:
    return json.loads(_SLICE.read_bytes())


def _pinned_jobs_paths() -> tuple[str, ...]:
    paths: set[str] = set()
    for task in _slice_value()["tasks"].values():
        catalog_join = task["provenance"]["catalog_join"]
        for name in ("prompt", "receipt"):
            descriptor = catalog_join[name]
            if descriptor["relative_to"] == "jobs-root":
                paths.add(descriptor["jobs_relative_path"])
        for descriptor in task["provenance"]["evidence"]:
            if descriptor["relative_to"] == "jobs-root":
                paths.add(descriptor["path"])
    return tuple(sorted(paths))


def _missing_pinned_jobs_files(jobs_root: Path) -> tuple[str, ...]:
    missing = []
    for relative in _pinned_jobs_paths():
        try:
            os.stat(jobs_root / relative)
        except FileNotFoundError:
            missing.append(relative)
    return tuple(missing)


def _require_pinned_jobs_files(jobs_root: Path) -> None:
    missing = _missing_pinned_jobs_files(jobs_root)
    if missing:
        detail = ", ".join(missing)
        pytest.skip(
            "pinned external jobs inputs are unavailable; missing relative "
            f"paths: {detail}; with the complete input set, all assertions "
            "in this test would run"
        )


def _all_keys(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_keys(item)


def test_checked_in_slice_has_fixed_raw_pin_and_exact_canonical_bytes() -> None:
    raw = _SLICE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _PINNED_SLICE_SHA256
    value = TOOL.load_wiring_slice(_SLICE)
    assert raw == TOOL.canonical_bytes(value) + b"\n"
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert TOOL.SLICE_SHA256 == _PINNED_SLICE_SHA256


def test_portable_verifier_joins_checked_in_catalog_and_classification() -> None:
    result = TOOL.verify_wiring_slice(
        slice_path=_SLICE,
        catalog_path=_CATALOG,
        classification_path=_CLASSIFICATION,
        repo_root=_ROOT,
    )
    assert result["integrity_status"] == "verified"
    assert result["physical_jobs_audit"] == "not-requested"
    assert result["checked_task_count"] == 2
    assert result["task_acceptance_status"] == "unbound"
    assert result["fix_gate_eligible"] is False
    assert result["routing_evidence_eligible"] is False
    assert result["routing_evidence_status"] == "inconclusive"
    assert not {"accepted", "success", "passed"}.intersection(_all_keys(result))


def test_optional_jobs_root_audits_pinned_prompt_and_receipt_bytes() -> None:
    _require_pinned_jobs_files(_JOBS_ROOT)
    result = TOOL.verify_wiring_slice(
        slice_path=_SLICE,
        catalog_path=_CATALOG,
        classification_path=_CLASSIFICATION,
        repo_root=_ROOT,
        jobs_root=_JOBS_ROOT,
    )
    assert result["integrity_status"] == "verified"
    assert result["physical_jobs_audit"] == "verified"


def test_pinned_jobs_requirements_are_exact() -> None:
    assert _pinned_jobs_paths() == (
        "T-1222-population-closure/"
        "T-1222-population-closure-plan-"
        "c7d8a2085d4bacb773d2a1a240801409d1c754541d424fffe87fbf21e1305ff3/"
        "receipt.json",
        "T-1222-population-closure/stage2-plan-prompt.md",
        "dev-wave-t1393-finish-trial-indeterminate/"
        "dev-wave-t1393-finish-trial-indeterminate-plan-"
        "8501201db4c59d0a3d53591b3b0c373cccccf2c67159a53b4e9a2c35b2b62a3c/"
        "receipt.json",
        "dev-wave-t1393-finish-trial-indeterminate/stage2-prompt.md",
    )


def _write_pinned_jobs_stubs(jobs_root: Path, paths: tuple[str, ...]) -> None:
    for relative in paths:
        target = jobs_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"stub\n")


def test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing(
    tmp_path: Path,
) -> None:
    jobs_root = tmp_path / "jobs"
    jobs_root.mkdir()
    paths = _pinned_jobs_paths()
    _write_pinned_jobs_stubs(jobs_root, paths[1:])

    with pytest.raises(pytest.skip.Exception) as caught:
        _require_pinned_jobs_files(jobs_root)
    assert paths[0] in str(caught.value)
    assert "complete input set, all assertions in this test would run" in str(
        caught.value
    )


def test_pinned_jobs_guard_does_not_skip_for_complete_input_set(
    tmp_path: Path,
) -> None:
    jobs_root = tmp_path / "jobs"
    _write_pinned_jobs_stubs(jobs_root, _pinned_jobs_paths())

    _require_pinned_jobs_files(jobs_root)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ("unknown-top", "wiring_slice: field set mismatch"),
        ("unknown-task", "task row is closed"),
        ("missing-profile", "wiring_slice: field set mismatch"),
        ("projection", "known_finding_ids: oracle finding projection mismatch"),
        ("status", "task_acceptance_status: must be unbound"),
        ("allowlist", "supported_commands: allowlist mismatch"),
    ),
)
def test_closed_slice_schema_rejects_single_field_mutations(
    mutation: str, reason: str,
) -> None:
    value = _slice_value()
    first = value["tasks"]["T-1222-population-closure:plan:0"]
    if mutation == "unknown-top":
        value["unknown"] = True
    elif mutation == "unknown-task":
        first["unknown"] = True
    elif mutation == "missing-profile":
        del value["slice_schema_version"]
    elif mutation == "projection":
        first["known_finding_ids"] = ["wrong-finding"]
    elif mutation == "status":
        first["task_acceptance_status"] = "bound"
    else:
        value["supported_commands"].append("build-snapshot")
    with pytest.raises(TOOL.WiringSliceError) as caught:
        TOOL.validate_wiring_slice(value)
    if mutation == "unknown-task":
        assert str(caught.value).endswith("field set mismatch")
    else:
        assert reason in str(caught.value)


def test_semantically_consistent_finding_change_is_stopped_by_pin() -> None:
    value = _slice_value()
    finding = value["tasks"]["T-1222-population-closure:plan:0"][
        "oracle_findings"
    ][0]
    finding["detection_condition"] += " Extra text is forbidden by the pin."
    with pytest.raises(TOOL.WiringSliceError) as caught:
        TOOL.validate_wiring_slice(value)
    assert str(caught.value) == "wiring_slice: semantic SHA-256 pin mismatch"


@pytest.mark.parametrize("framing", ("pretty", "missing-lf", "extra-lf"))
def test_slice_loader_rejects_noncanonical_raw_framing(
    framing: str, tmp_path: Path,
) -> None:
    value = _slice_value()
    if framing == "pretty":
        raw = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    elif framing == "missing-lf":
        raw = _SLICE.read_bytes()[:-1]
    else:
        raw = _SLICE.read_bytes() + b"\n"
    path = tmp_path / "slice.json"
    path.write_bytes(raw)
    with pytest.raises(TOOL.WiringSliceError, match="exactly one LF"):
        TOOL.load_wiring_slice(path)


def test_slice_loader_rejects_symlink_transport(tmp_path: Path) -> None:
    path = tmp_path / "slice.json"
    path.symlink_to(_SLICE)
    with pytest.raises(TOOL.WiringSliceError) as caught:
        TOOL.load_wiring_slice(path)
    assert str(caught.value) == (
        "wiring_slice: must be a non-symlink regular file"
    )


def test_direct_loader_rejects_duplicate_key(tmp_path: Path) -> None:
    path = tmp_path / "slice.json"
    path.write_bytes(b'{"schema_version":3,"schema_version":3}\n')
    with pytest.raises(TOOL.WiringSliceError, match="not strict JSON"):
        TOOL.load_wiring_slice(path, require_pin=False)


def test_direct_loader_rejects_nan(tmp_path: Path) -> None:
    path = tmp_path / "slice.json"
    path.write_bytes(b'{"value":NaN}\n')
    with pytest.raises(TOOL.WiringSliceError, match="not strict JSON"):
        TOOL.load_wiring_slice(path, require_pin=False)


def test_direct_loader_rejects_infinity(tmp_path: Path) -> None:
    path = tmp_path / "slice.json"
    path.write_bytes(b'{"value":Infinity}\n')
    with pytest.raises(TOOL.WiringSliceError, match="not strict JSON"):
        TOOL.load_wiring_slice(path, require_pin=False)


def test_direct_loader_rejects_nested_float(tmp_path: Path) -> None:
    path = tmp_path / "slice.json"
    path.write_bytes(b'{"nested":{"value":1.5}}\n')
    with pytest.raises(TOOL.WiringSliceError, match="float is forbidden"):
        TOOL.load_wiring_slice(path, require_pin=False)


def test_direct_loader_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "slice.json"
    path.write_bytes(b'{"value":"\xff"}\n')
    with pytest.raises(TOOL.WiringSliceError, match="not strict JSON"):
        TOOL.load_wiring_slice(path, require_pin=False)


def test_or_m4_receipt_ordinal_is_needed_for_unique_join() -> None:
    catalog = CATALOG.validate_task_catalog(
        strict_loads(
            _CATALOG.read_bytes(),
            label="catalog-fixture",
            max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    )
    task = next(iter(TOOL.load_wiring_slice(_SLICE)["tasks"].values()))
    target = next(
        row
        for row in catalog["candidates"]
        if row["wave_id"] == task["provenance"]["catalog_join"]["wave_id"]
        and row["dev_wave_stage"] == "plan"
        and row["receipt_ordinal"] == 0
    )
    synthetic = copy.deepcopy(catalog)
    second_ordinal = copy.deepcopy(target)
    second_ordinal["receipt_ordinal"] = 1
    synthetic["candidates"].append(second_ordinal)
    assert TOOL._catalog_row_for_task(synthetic, task) == target


def test_classification_join_rejects_task_type_drift_at_join_layer() -> None:
    value = TOOL.load_wiring_slice(_SLICE)
    task = next(iter(value["tasks"].values()))
    catalog = CATALOG.validate_task_catalog(
        strict_loads(
            _CATALOG.read_bytes(),
            label="catalog-fixture",
            max_bytes=DEFAULT_MAX_JSON_BYTES,
        )
    )
    row = TOOL._catalog_row_for_task(catalog, task)
    classifications = CATALOG._load_classifications(_CLASSIFICATION)
    mutated = copy.deepcopy(classifications)
    mutated[row["wave_id"]]["task_type"] = "docs"
    with pytest.raises(TOOL.WiringSliceError) as caught:
        TOOL._classification_for_task(row, task, mutated)
    assert str(caught.value).endswith("task type mismatch")


def _synthetic_jobs_task(root: Path) -> dict[str, Any]:
    prompt = root / "wave/prompt.md"
    receipt = root / "wave/job/receipt.json"
    prompt.parent.mkdir(parents=True)
    receipt.parent.mkdir(parents=True)
    prompt.write_bytes(b"line one\nline two\n")
    receipt.write_bytes(b'{"schema_version":3}\n')
    task = copy.deepcopy(next(iter(TOOL.load_wiring_slice(_SLICE)["tasks"].values())))
    join = task["provenance"]["catalog_join"]
    join["prompt"] = {
        "jobs_relative_path": "wave/prompt.md",
        "relative_to": "jobs-root",
        "sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
    }
    join["receipt"] = {
        "jobs_relative_path": "wave/job/receipt.json",
        "relative_to": "jobs-root",
        "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
    }
    evidence = task["provenance"]["evidence"][0]
    evidence.update(
        {
            "path": "wave/prompt.md",
            "sha256": join["prompt"]["sha256"],
            "line_start": 1,
            "line_end": 2,
        }
    )
    return task


def test_or_m5_physical_prompt_byte_change_has_one_sha_reason(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    task = _synthetic_jobs_task(jobs)
    rooted = TOOL._root(jobs, label="jobs-root")
    TOOL._audit_jobs_task(task, rooted)
    (jobs / "wave/prompt.md").write_bytes(b"line one\nline Xwo\n")
    with pytest.raises(TOOL.WiringSliceError) as caught:
        TOOL._audit_jobs_task(task, rooted)
    assert str(caught.value).endswith("prompt: SHA-256 mismatch")


@pytest.mark.parametrize("mutation", ("symlink", "directory", "invalid-utf8", "line-range"))
def test_repo_evidence_path_and_text_checks_fail_closed(
    mutation: str, tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "evidence.md"
    evidence = {
        "path": "evidence.md",
        "sha256": "",
        "line_start": 1,
        "line_end": 1,
    }
    if mutation == "symlink":
        source = repo / "source.md"
        source.write_bytes(b"one\n")
        target.symlink_to(source)
        evidence["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        match = "symlink path is forbidden"
    elif mutation == "directory":
        target.mkdir()
        evidence["sha256"] = hashlib.sha256(b"").hexdigest()
        match = "must be a regular file"
    elif mutation == "invalid-utf8":
        target.write_bytes(b"\xff\n")
        evidence["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        match = "not strict UTF-8"
    else:
        target.write_bytes(b"one\n")
        evidence["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        evidence["line_end"] = 2
        match = "line range exceeds file"
    with pytest.raises(TOOL.WiringSliceError, match=match):
        TOOL._audit_file_evidence(
            TOOL._root(repo, label="repository-root"),
            evidence,
            label="repository-evidence",
        )


def test_root_rejects_lexical_ancestor_symlink(tmp_path: Path) -> None:
    physical = tmp_path / "physical"
    root = physical / "repo"
    root.mkdir(parents=True)
    alias = tmp_path / "alias"
    alias.symlink_to(physical, target_is_directory=True)
    with pytest.raises(TOOL.WiringSliceError, match="root ancestor"):
        TOOL._root(alias / "repo", label="repository-root")


def test_rooted_reader_rejects_symlink_directory_component(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    physical = root / "physical"
    physical.mkdir(parents=True)
    (physical / "evidence.md").write_bytes(b"one\n")
    (root / "alias").symlink_to(physical, target_is_directory=True)
    with pytest.raises(TOOL.WiringSliceError, match="symlink path is forbidden"):
        TOOL._rooted_regular_bytes(
            TOOL._root(root, label="repository-root"),
            "alias/evidence.md",
            label="repository-evidence",
        )


def test_rooted_reader_rejects_final_path_swap_at_read_seam(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "evidence.md"
    replacement = root / "replacement.md"
    target.write_bytes(b"pinned\n")
    replacement.write_bytes(b"swapped\n")

    def swap_final_path() -> None:
        os.replace(replacement, target)

    with pytest.raises(TOOL.WiringSliceError, match="path changed while reading"):
        TOOL._rooted_regular_bytes(
            TOOL._root(root, label="repository-root"),
            "evidence.md",
            label="repository-evidence",
            before_read=swap_final_path,
        )


def test_rooted_reader_rejects_intermediate_directory_swap_at_read_seam(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (nested / "evidence.md").write_bytes(b"pinned\n")
    displaced = root / "displaced"

    def swap_intermediate_directory() -> None:
        nested.rename(displaced)
        nested.mkdir()
        (nested / "evidence.md").write_bytes(b"swapped\n")

    with pytest.raises(TOOL.WiringSliceError, match="path changed while reading"):
        TOOL._rooted_regular_bytes(
            TOOL._root(root, label="repository-root"),
            "nested/evidence.md",
            label="repository-evidence",
            before_read=swap_intermediate_directory,
        )


def test_verifier_never_reloads_classification_by_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_reload(_path: Path) -> dict[str, dict[str, object]]:
        raise AssertionError("classification pathname loader must not run")

    monkeypatch.setattr(CATALOG, "_load_classifications", forbidden_reload)
    result = TOOL.verify_wiring_slice(
        slice_path=_SLICE,
        catalog_path=_CATALOG,
        classification_path=_CLASSIFICATION,
        repo_root=_ROOT,
    )
    assert result["integrity_status"] == "verified"


def test_verifier_cli_failure_separates_integrity_from_task_acceptance(
    tmp_path: Path, capfd: pytest.CaptureFixture[str],
) -> None:
    rc = TOOL.main(
        [
            "verify",
            "--slice", os.fspath(tmp_path / "missing.json"),
            "--catalog", os.fspath(_CATALOG),
            "--classification", os.fspath(_CLASSIFICATION),
            "--repo-root", os.fspath(_ROOT),
        ]
    )
    result = json.loads(capfd.readouterr().out)
    assert rc == 2
    assert result["integrity_status"] == "rejected"
    assert result["task_acceptance_status"] == "unbound"
    assert result["routing_evidence_status"] == "inconclusive"
    assert not {"accepted", "success", "passed"}.intersection(_all_keys(result))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
