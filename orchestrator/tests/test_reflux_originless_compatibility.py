"""Full-structure compatibility guard for the originless bounded trial path."""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from orchestrator.campaign import p3_autonomous_workload_trial as A
from orchestrator.tests import test_p3_autonomous_workload_trial as p3_test


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
            generations=1,
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
    return {
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
# Acceptance report digests transitively cover volatile report leaves above.
_VOLATILE_ACCEPTANCE_REPORT_SHA = ("acceptance", "trials", "*", "report_sha256")
# Acceptance journal digests transitively cover volatile journal leaves above.
_VOLATILE_ACCEPTANCE_JOURNAL_SHA = ("acceptance", "trials", "*", "attempt_journal_sha256")

_VOLATILE_LEAF_PATHS = frozenset({
    _VOLATILE_ROLE_TS,
    _VOLATILE_ROLE_PATH,
    _VOLATILE_REPORT_STARTED,
    _VOLATILE_REPORT_FINISHED,
    _VOLATILE_REPORT_JOURNAL_PATH,
    _VOLATILE_REPORT_JOURNAL_SHA,
    _VOLATILE_REPORT_CAMPAIGN_ROOT,
    _VOLATILE_JOURNAL_TS,
    _VOLATILE_JOURNAL_ROLE_PATH,
    _VOLATILE_JOURNAL_REPORT_PATH,
    _VOLATILE_LIFECYCLE_RUN_ROOT,
    _VOLATILE_LIFECYCLE_REPORT_SHA,
    _VOLATILE_LIFECYCLE_JOURNAL_SHA,
    _VOLATILE_ACCEPTANCE_LIFECYCLE_SHA,
    _VOLATILE_ACCEPTANCE_REPORT_SHA,
    _VOLATILE_ACCEPTANCE_JOURNAL_SHA,
})


def _volatile(path: tuple[object, ...]) -> bool:
    return any(
        len(pattern) == len(path)
        and all(expected == "*" or expected == actual for expected, actual in zip(pattern, path))
        for pattern in _VOLATILE_LEAF_PATHS
    )


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


def test_originless_harness_rebuild_is_deterministic_control(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Control: rebuilding the harness must not change default-path bytes."""
    _pin_fixture_commit_dates(monkeypatch)
    bundle_root = tmp_path / "originless-control"
    first = _bundle(bundle_root, monkeypatch, explicit_none=False)
    shutil.rmtree(bundle_root)
    second = _bundle(bundle_root, monkeypatch, explicit_none=False)
    _assert_same_structure(first, second)


def test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_fixture_commit_dates(monkeypatch)
    bundle_root = tmp_path / "originless"
    omitted = _bundle(bundle_root, monkeypatch, explicit_none=False)
    shutil.rmtree(bundle_root)
    explicit_none = _bundle(bundle_root, monkeypatch, explicit_none=True)
    _assert_same_structure(omitted, explicit_none)
    originless_key_mutant = copy.deepcopy(omitted)
    originless_key_mutant["reports"][0]["origin_runtime"] = None
    with pytest.raises(AssertionError):
        _assert_same_structure(omitted, originless_key_mutant)

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
            assert "origin_terminal_projection" not in row
        for trial in bundle["acceptance"]["trials"]:
            assert "origin_terminal_projection" not in trial
