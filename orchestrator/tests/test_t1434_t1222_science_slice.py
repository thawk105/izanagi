from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from tools import t1434_t1222_science_slice as science


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = (
    REPO_ROOT
    / "output/t189-routing-preregistration/"
    "task-oracle-science-slice-t1222-v1.json"
)
JOBS_ROOT = Path("/work/1/SFC/tanab/dev-wave-jobs")


def _artifact_value() -> dict[str, Any]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _write_canonical(path: Path, value: object) -> Path:
    path.write_bytes(science.canonical_bytes(value) + b"\n")
    return path


def _jobs_descriptors(value: dict[str, Any]) -> list[dict[str, str]]:
    descriptors: list[dict[str, str]] = []
    for review in value["content_review"]["reviews"]:
        descriptors.extend(review[name] for name in ("prompt", "output", "receipt"))
    for target in value["evidence"]["targets"]:
        descriptors.extend(target[name] for name in ("prompt", "output", "receipt"))
    descriptors.append(value["evidence"]["acceptance_receipt"])
    descriptors.extend((
        value["oracle_ledger"]["freeze"],
        value["oracle_ledger"]["source_bundle"],
    ))
    for reader in value["reader_reviews"]:
        descriptors.extend(reader[name] for name in ("prompt", "output", "receipt"))
    return descriptors


def _pinned_jobs_paths() -> tuple[str, ...]:
    return tuple(sorted({
        descriptor["jobs_relative_path"]
        for descriptor in _jobs_descriptors(_artifact_value())
    }))


def _reader_output_path(reader_id: str) -> str:
    reader = next(
        row for row in _artifact_value()["reader_reviews"]
        if row["reader_id"] == reader_id
    )
    return reader["output"]["jobs_relative_path"]


def _missing_pinned_jobs_files(
    jobs_root: Path,
    relative_paths: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    missing = []
    requirements = (
        _pinned_jobs_paths()
        if relative_paths is None
        else relative_paths
    )
    for relative in requirements:
        try:
            os.stat(jobs_root / relative)
        except FileNotFoundError:
            missing.append(relative)
    return tuple(missing)


def _require_pinned_jobs_files(
    jobs_root: Path,
    relative_paths: tuple[str, ...] | None = None,
) -> None:
    missing = _missing_pinned_jobs_files(jobs_root, relative_paths)
    if missing:
        detail = ", ".join(missing)
        pytest.skip(
            "pinned external jobs inputs are unavailable; missing relative "
            f"paths: {detail}; with the complete input set, all assertions "
            "in this test would run"
        )


def _copy_physical_jobs_fixture(tmp_path: Path) -> Path:
    jobs = tmp_path / "jobs"
    for descriptor in _jobs_descriptors(_artifact_value()):
        relative = descriptor["jobs_relative_path"]
        destination = jobs / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(JOBS_ROOT / relative, destination)
    return jobs


def test_checked_in_artifact_portable_is_not_evaluated(capsys: pytest.CaptureFixture[str]) -> None:
    rc = science.main([
        "verify-portable", os.fspath(ARTIFACT),
        "--repo-root", os.fspath(REPO_ROOT),
    ])
    assert rc == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["artifact_verification_status"] == "valid"
    assert receipt["integrity_status"] == "valid"
    assert receipt["retrospective_task_output_acceptance_status"] == "not-evaluated"
    assert receipt["verification_mode"] == "portable"
    assert receipt["organizational_independence"] == "not-established"
    assert receipt["section8_complete"] is False
    assert "artifact_raw_sha256" not in receipt
    assert "dependency_bytes" not in receipt
    assert "validator_bytes_sha256" not in receipt


def test_physical_real_jobs_root_is_valid_negative_observation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _require_pinned_jobs_files(JOBS_ROOT)
    rc = science.main([
        "verify-physical", os.fspath(ARTIFACT),
        "--repo-root", os.fspath(REPO_ROOT),
        "--jobs-root", os.fspath(JOBS_ROOT),
    ])
    assert rc == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["artifact_verification_status"] == "valid"
    assert receipt["integrity_status"] == "valid"
    assert receipt["coverage"] == {
        "agreed_detected": 2,
        "canonical_rational": "1/3",
        "oracle_finding_total": 6,
    }
    assert receipt["reader_agreement_status"] == "agreed-all-cells"
    assert receipt["retrospective_task_output_acceptance_status"] == "not-accepted"
    assert receipt["organizational_independence"] == "not-established"
    assert receipt["section8_complete"] is False
    assert receipt["artifact_raw_sha256"] == hashlib.sha256(
        ARTIFACT.read_bytes(),
    ).hexdigest()
    assert receipt["validator_bytes_sha256"] == hashlib.sha256(
        Path(science.__file__).read_bytes(),
    ).hexdigest()

    dependencies = receipt["dependency_bytes"]
    assert dependencies == sorted(
        dependencies,
        key=lambda item: (item["relative_to"], item["path"], item["sha256"]),
    )
    value = _artifact_value()
    expected_paths = {
        ("repository-root", value["evidence"]["catalog"]["path"]),
        (
            "repository-root",
            value["evidence"]["fixed_state"]["worklog_path"],
        ),
    }
    expected_paths.update(
        ("jobs-root", descriptor["jobs_relative_path"])
        for descriptor in _jobs_descriptors(value)
    )
    assert len(dependencies) == len(expected_paths)
    assert {
        (item["relative_to"], item["path"]) for item in dependencies
    } == expected_paths
    roots = {"repository-root": REPO_ROOT, "jobs-root": JOBS_ROOT}
    for item in dependencies:
        assert set(item) == {"path", "relative_to", "sha256"}
        raw = (roots[item["relative_to"]] / item["path"]).read_bytes()
        assert item["sha256"] == hashlib.sha256(raw).hexdigest()


def test_ss_m1_exact_ledger_rejects_deleted_finding(tmp_path: Path) -> None:
    value = _artifact_value()
    del value["oracle_ledger"]["findings"][0]  # type: ignore[index]
    mutated = _write_canonical(tmp_path / "artifact.json", value)
    with pytest.raises(science.ScienceSliceError, match="exact six-finding ledger"):
        science.verify_portable(artifact_path=mutated, repo_root=REPO_ROOT)


def test_ss_m1_exact_ledger_rejects_must_fix_false(tmp_path: Path) -> None:
    value = _artifact_value()
    value["oracle_ledger"]["findings"][0]["must_fix"] = False  # type: ignore[index]
    mutated = _write_canonical(tmp_path / "artifact.json", value)
    with pytest.raises(science.ScienceSliceError, match="exact six-finding ledger"):
        science.verify_portable(artifact_path=mutated, repo_root=REPO_ROOT)


def test_exact_ledger_rejects_detection_condition_tamper(tmp_path: Path) -> None:
    value = _artifact_value()
    finding = value["oracle_ledger"]["findings"][0]  # type: ignore[index]
    finding["detection_condition"] += " weakened"  # type: ignore[index,operator]
    mutated = _write_canonical(tmp_path / "artifact.json", value)
    with pytest.raises(science.ScienceSliceError, match="exact six-finding ledger"):
        science.verify_portable(artifact_path=mutated, repo_root=REPO_ROOT)


def test_ss_m2_reader_consensus_single_reader_miss_cannot_accept() -> None:
    cells = {
        (finding_id, stage): "detected"
        for finding_id in science.FINDING_IDS
        for stage in science.STAGES
    }
    matrices = {"reader-A": dict(cells), "reader-B": dict(cells)}
    matrices["reader-B"][(science.FINDING_IDS[0], "plan")] = "not-detected"
    result = science._evaluate_reader_matrices(
        matrices, primary_child_green=True,
    )
    assert result["reader_agreement_status"] == "disagreed-cells"
    assert result["coverage"] == {
        "agreed_detected": 5,
        "canonical_rational": "5/6",
        "oracle_finding_total": 6,
    }
    assert result["retrospective_task_output_acceptance_status"] == "not-accepted"


def test_ss_m3_non_child_green_receipt_cannot_accept() -> None:
    cells = {
        (finding_id, stage): "detected"
        for finding_id in science.FINDING_IDS
        for stage in science.STAGES
    }
    result = science._evaluate_reader_matrices(
        {"reader-A": dict(cells), "reader-B": dict(cells)},
        primary_child_green=False,
    )
    assert result["coverage"]["agreed_detected"] == 6
    assert result["reader_agreement_status"] == "agreed-all-cells"
    assert result["retrospective_task_output_acceptance_status"] == "not-accepted"


def test_all_findings_both_stages_both_readers_and_child_green_is_accepted() -> None:
    cells = {
        (finding_id, stage): "detected"
        for finding_id in science.FINDING_IDS
        for stage in science.STAGES
    }
    result = science._evaluate_reader_matrices(
        {"reader-A": dict(cells), "reader-B": dict(cells)},
        primary_child_green=True,
    )
    assert result["coverage"]["agreed_detected"] == 6
    assert result["reader_agreement_status"] == "agreed-all-cells"
    assert result["semantic_miss_finding_ids"] == []
    assert result["retrospective_task_output_acceptance_status"] == "accepted"


def test_ss_m4_stored_coverage_tampering_is_rejected(tmp_path: Path) -> None:
    _require_pinned_jobs_files(JOBS_ROOT)
    value = _artifact_value()
    coverage = value["results"]["coverage"]  # type: ignore[index]
    coverage["agreed_detected"] = 3
    coverage["canonical_rational"] = "1/2"
    mutated = _write_canonical(tmp_path / "artifact.json", value)
    with pytest.raises(science.ScienceSliceError, match="coverage: physical recomputation mismatch"):
        science.verify_physical(
            artifact_path=mutated, repo_root=REPO_ROOT, jobs_root=JOBS_ROOT,
        )


def test_ss_m5_portable_receipt_never_exposes_physical_semantics() -> None:
    receipt = science.verify_portable(
        artifact_path=ARTIFACT, repo_root=REPO_ROOT,
    )
    assert receipt["retrospective_task_output_acceptance_status"] == "not-evaluated"
    assert "coverage" not in receipt
    assert "reader_agreement_status" not in receipt


def test_ss_m6_changed_target_output_bytes_are_rejected_by_direct_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_pinned_jobs_files(JOBS_ROOT)
    value = _artifact_value()
    jobs = _copy_physical_jobs_fixture(tmp_path)
    target_path = value["evidence"]["targets"][0]["output"]["jobs_relative_path"]
    target = jobs / target_path
    target.write_bytes(target.read_bytes() + b"\nSS-M6 changed target output bytes\n")

    # Frozen receipts record the original absolute root. Keep that path
    # projection fixed so only the copied target's bytes can reject this run.
    absolute_under = science._absolute_under
    monkeypatch.setattr(
        science, "_absolute_under",
        lambda _root, relative: absolute_under(JOBS_ROOT, relative),
    )
    with pytest.raises(science.ScienceSliceError):
        science.verify_physical(
            artifact_path=ARTIFACT, repo_root=REPO_ROOT, jobs_root=jobs,
        )


def test_artifact_rejects_noncanonical_json(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(_artifact_value(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(science.ScienceSliceError, match="sorted compact UTF-8"):
        science.load_artifact(path)


def test_artifact_rejects_duplicate_key(tmp_path: Path) -> None:
    raw = ARTIFACT.read_bytes().replace(
        b'{"artifact_kind":',
        b'{"artifact_kind":"duplicate","artifact_kind":',
        1,
    )
    path = tmp_path / "artifact.json"
    path.write_bytes(raw)
    with pytest.raises(science.ScienceSliceError, match="duplicate key"):
        science.load_artifact(path)


def test_artifact_rejects_float(tmp_path: Path) -> None:
    raw = ARTIFACT.read_bytes().replace(
        b'"schema_version":"t1434-t1222-task-output-science-slice/v1"',
        b'"schema_version":1.0',
        1,
    )
    path = tmp_path / "artifact.json"
    path.write_bytes(raw)
    with pytest.raises(science.ScienceSliceError, match="float is forbidden"):
        science.load_artifact(path)


def test_artifact_scope_rejects_canonical_false_changed_to_integer_zero(
    tmp_path: Path,
) -> None:
    value = _artifact_value()
    value["scope"]["section8_complete"] = 0
    mutated = _write_canonical(tmp_path / "artifact.json", value)
    with pytest.raises(science.ScienceSliceError, match="scope must match"):
        science.load_artifact(mutated)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra", "bad-verdict"])
def test_reader_table_rejects_missing_duplicate_extra_and_bad_verdict(mutation: str) -> None:
    relative = _reader_output_path("reader-A")
    _require_pinned_jobs_files(JOBS_ROOT, (relative,))
    raw = (JOBS_ROOT / relative).read_bytes()
    text = raw.decode("utf-8")
    row = next(
        line for line in text.splitlines()
        if line.startswith("| T1222-O1-FRESH-CHILD-IMPORT-ISOLATION | plan |")
    )
    if mutation == "missing":
        text = text.replace(row + "\n", "", 1)
    elif mutation == "duplicate":
        text = text.replace(row + "\n", row + "\n" + row + "\n", 1)
    elif mutation == "extra":
        text = text.replace(row, row.replace("T1222-O1", "T1222-EXTRA"), 1)
    else:
        text = text.replace("| plan | detected |", "| plan | maybe |", 1)
    with pytest.raises(science.ScienceSliceError):
        science.parse_reader_markdown(
            text.encode("utf-8"), expected_reader_id="reader-A", label="reader-A",
        )


def test_reader_markdown_rejects_duplicate_blindness_attestation() -> None:
    relative = _reader_output_path("reader-A")
    _require_pinned_jobs_files(JOBS_ROOT, (relative,))
    raw = (JOBS_ROOT / relative).read_bytes()
    contradictory = raw + (
        b"\n## Blindness attestation\n"
        b"reader_id=reader-A\n"
        b"peer_verdict_disclosed=true\n"
        b"arm_counts_disclosed=false\n"
    )
    with pytest.raises(science.ScienceSliceError, match="exactly one"):
        science.parse_reader_markdown(
            contradictory, expected_reader_id="reader-A", label="reader-A",
        )


@pytest.mark.parametrize(
    "duplicate_header",
    [
        "## Blindness attestation   ",
        "## Blindness attestation #",
        "## Blindness attestation ####   ",
    ],
)
def test_reader_markdown_rejects_markdown_equivalent_duplicate_attestation(
    duplicate_header: str,
) -> None:
    relative = _reader_output_path("reader-A")
    _require_pinned_jobs_files(JOBS_ROOT, (relative,))
    raw = (JOBS_ROOT / relative).read_bytes()
    contradictory = raw + (
        f"\n{duplicate_header}\n"
        "reader_id=reader-A\n"
        "peer_verdict_disclosed=true\n"
        "arm_counts_disclosed=false\n"
    ).encode("utf-8")
    with pytest.raises(science.ScienceSliceError, match="exactly one"):
        science.parse_reader_markdown(
            contradictory, expected_reader_id="reader-A", label="reader-A",
        )


def test_pinned_jobs_requirements_are_exact() -> None:
    assert _pinned_jobs_paths() == (
        "T-1222-population-closure/"
        "T-1222-population-closure-author-"
        "6e91e61393fd97a4ea7ea5ef8783eb93cdc131692dc10259c99d97c42c444863/"
        "receipt.json",
        "T-1222-population-closure/"
        "T-1222-population-closure-plan-"
        "c7d8a2085d4bacb773d2a1a240801409d1c754541d424fffe87fbf21e1305ff3/"
        "receipt.json",
        "T-1222-population-closure/acceptance-receipt-2.json",
        "T-1222-population-closure/stage2-plan-prompt.md",
        "T-1222-population-closure/stage2-plan.md",
        "T-1222-population-closure/stage5-author-prompt.md",
        "T-1222-population-closure/stage5-author.md",
        "dev-wave-t1434-science-slice/codex-artifacts/"
        "dev-wave-t1434-science-slice/t1434-science-readerA/receipt.json",
        "dev-wave-t1434-science-slice/codex-artifacts/"
        "dev-wave-t1434-science-slice/t1434-science-readerB/receipt.json",
        "dev-wave-t1434-science-slice/codex-artifacts/"
        "dev-wave-t1434-science-slice/t1434-science-stage3-lensA/receipt.json",
        "dev-wave-t1434-science-slice/codex-artifacts/"
        "dev-wave-t1434-science-slice/t1434-science-stage3-lensB/receipt.json",
        "dev-wave-t1434-science-slice/oracle-ledger-freeze-v1.json",
        "dev-wave-t1434-science-slice/projections/oracle-source-bundle.md",
        "dev-wave-t1434-science-slice/readerA-prompt.md",
        "dev-wave-t1434-science-slice/readerA.md",
        "dev-wave-t1434-science-slice/readerB-prompt.md",
        "dev-wave-t1434-science-slice/readerB.md",
        "dev-wave-t1434-science-slice/stage3-lensA-prompt.md",
        "dev-wave-t1434-science-slice/stage3-lensA.md",
        "dev-wave-t1434-science-slice/stage3-lensB-prompt.md",
        "dev-wave-t1434-science-slice/stage3-lensB.md",
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


def test_reader_output_guard_does_not_require_unrelated_pinned_files(
    tmp_path: Path,
) -> None:
    jobs_root = tmp_path / "jobs"
    relative = _reader_output_path("reader-A")
    _write_pinned_jobs_stubs(jobs_root, (relative,))

    _require_pinned_jobs_files(jobs_root, (relative,))


def test_git_environment_overrides_are_isolated_and_linked_worktree_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (REPO_ROOT / ".git").is_file()
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_COUNT",
    ):
        monkeypatch.setenv(name, "/outside/untrusted-git-state")
    receipt = science.verify_portable(
        artifact_path=ARTIFACT, repo_root=REPO_ROOT,
    )
    assert receipt["artifact_verification_status"] == "valid"


def test_git_repository_root_must_be_the_exact_top_level() -> None:
    with pytest.raises(science.ScienceSliceError, match="not the git top-level"):
        science._verify_git_toplevel(REPO_ROOT / "tools")


def test_physical_rejects_symlink_component(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    (jobs / "dev-wave-t1434-science-slice").symlink_to(
        JOBS_ROOT / "dev-wave-t1434-science-slice", target_is_directory=True,
    )
    with pytest.raises(science.ScienceSliceError, match="symlink path component"):
        science.verify_physical(
            artifact_path=ARTIFACT, repo_root=REPO_ROOT, jobs_root=jobs,
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
