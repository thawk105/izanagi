"""Executable contract for the evidence-backed flaky-node quarantine."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from orchestrator.tests import conftest as CONF
from orchestrator.tests import flaky_test_holds as REG
from tools import mutation_harness as MH


_HELD_NODE = (
    "orchestrator/tests/test_mutation_harness.py::"
    "test_sigterm_handler_stops_child_and_restores_active_mutation"
)
_HELD_FILE = _HELD_NODE.split("::", 1)[0]
_SIBLING_NODE = (
    "orchestrator/tests/test_mutation_harness.py::"
    "test_cumulative_replacement_uses_the_result_of_the_previous_anchor"
)
_FOCUS_NODE = (
    "orchestrator/tests/test_campaign_claim.py::"
    "test_read_proc_starttime_uses_field_22_with_spaced_comm"
)


def _valid_hold() -> REG.FlakyTestHold:
    return REG.FLAKY_TEST_HOLDS[_HELD_NODE]


def test_initial_registry_is_one_exact_node_with_reintroduction_anchor() -> None:
    assert set(REG.FLAKY_TEST_HOLDS) == {_HELD_NODE}
    hold = _valid_hold()
    assert hold.known_failure_node_ids == frozenset({_HELD_NODE})
    assert hold.same_tree is True
    assert hold.green_collection_condition == "single-file"
    assert hold.green_run_count == 1
    assert hold.red_collection_condition == REG.ACCEPTANCE_COLLECTION
    assert hold.failure_signature
    assert hold.cause
    assert hold.evidence_id == "F57"
    assert hold.reintroduction_task_id == "{{T:flaky-sigterm-sync-point}}"


def test_real_pytest_subprocess_skips_registered_node_and_runs_same_file_sibling() -> None:
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "-vv",
            "-rs",
            _HELD_FILE,
        ],
        cwd=_REPO,
        env=environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout
    assert f"{_HELD_NODE} SKIPPED" in result.stdout
    assert f"{_SIBLING_NODE} PASSED" in result.stdout
    assert re.search(r"\b[0-9]+ passed\b", result.stdout)
    assert re.search(r"\b1 skipped\b", result.stdout)


def test_xdist_subprocess_focus_collection_does_not_run_stale_check() -> None:
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "-n",
            "2",
            "--dist",
            "load",
            "-vv",
            "-rs",
            _FOCUS_NODE,
        ],
        cwd=_REPO,
        env=environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout
    assert "missing from complete collection" not in result.stdout
    assert re.search(r"\b1 passed\b", result.stdout)


def test_xdist_subprocess_complete_collection_runs_stale_check() -> None:
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "-n",
            "2",
            "--dist",
            "load",
            "--collect-only",
            str(Path(CONF.__file__).resolve().parent),
        ],
        cwd=_REPO,
        env=environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout
    assert "flaky-test hold keys missing from complete collection" not in result.stdout


def test_mutation_harness_rejects_an_isolated_expected_failure_node() -> None:
    mutation = MH.Mutation(
        id="held-node",
        category="negative",
        replacements=(),
        expected_nodes=(_HELD_NODE,),
        expected_status="KILLED",
        hang_risk=False,
    )
    with pytest.raises(MH.HarnessError, match="policy mismatch"):
        MH._validate_registrations(
            _REPO,
            SimpleNamespace(mutations=(mutation,)),
            {},
        )


def test_mutation_harness_does_not_import_holds_from_another_checkout(
    tmp_path: Path,
) -> None:
    assert MH._flaky_hold_node_ids_for_policy(tmp_path) == frozenset()


@pytest.mark.parametrize(
    ("condition", "changes"),
    [
        ("green and red evidence", {"green_observation": ""}),
        ("failure signature", {"failure_signature": ""}),
        ("cause", {"cause": ""}),
        ("canonical evidence", {"evidence_id": "F999999"}),
        ("reintroduction task", {"reintroduction_task_id": ""}),
        ("reintroduction task format", {"reintroduction_task_id": "{{T:Flaky}}"}),
        ("same tree", {"same_tree": False}),
        (
            "known failure node IDs",
            {"known_failure_node_ids": frozenset({"other.py::test_other"})},
        ),
    ],
)
def test_each_acceptance_condition_has_a_rejected_negative_control(
    condition: str,
    changes: dict[str, object],
) -> None:
    del condition
    invalid = replace(_valid_hold(), **changes)
    with pytest.raises(ValueError):
        REG.validate_flaky_test_hold_rows(((_HELD_NODE, invalid),))


def test_acceptance_collection_evidence_is_required() -> None:
    invalid = replace(
        _valid_hold(),
        green_collection_condition="single-file",
        red_collection_condition="single-file",
    )
    with pytest.raises(ValueError):
        REG.validate_flaky_test_hold_rows(((_HELD_NODE, invalid),))


def test_evidence_section_must_name_registered_test_function() -> None:
    unrecorded_node = (
        "orchestrator/tests/test_mutation_harness.py::"
        "test_unrecorded_flaky_node"
    )
    invalid = replace(
        _valid_hold(),
        known_failure_node_ids=frozenset({unrecorded_node}),
    )
    with pytest.raises(ValueError, match="does not mention test function"):
        REG.validate_flaky_test_hold_rows(((unrecorded_node, invalid),))


def test_evidence_section_must_contain_failure_signature() -> None:
    invalid = replace(_valid_hold(), failure_signature="unrelated failure signature")
    with pytest.raises(ValueError, match="failure_signature"):
        REG.validate_flaky_test_hold_rows(((_HELD_NODE, invalid),))


def test_complete_collection_rejects_a_stale_registered_node() -> None:
    with pytest.raises(pytest.UsageError, match="missing from complete collection"):
        CONF._check_flaky_hold_collection_complete(SimpleNamespace(), ())


def test_flaky_summary_is_separate_and_uses_registry_digest() -> None:
    lines: list[str] = []

    class Terminal:
        def write_line(self, line: str) -> None:
            lines.append(line)

    config = SimpleNamespace(
        pluginmanager=SimpleNamespace(
            get_plugin=lambda name: Terminal() if name == "terminalreporter" else None
        ),
        _izanagi_collected_flaky_hold_ids={_HELD_NODE},
        _izanagi_skipped_flaky_hold_ids={_HELD_NODE},
    )
    CONF.pytest_sessionfinish(SimpleNamespace(config=config), 0)
    summary_lines = [
        line for line in lines if line.startswith("IZANAGI_FLAKY_HOLD_SUMMARY_V1 ")
    ]
    assert len(summary_lines) == 1
    payload = json.loads(summary_lines[0].split(" ", 1)[1])
    assert payload == {
        "registered_node_count": 1,
        "matched_node_count": 1,
        "skipped_node_count": 1,
        "registry_sha256": REG.FLAKY_TEST_HOLDS_SHA256,
    }
    assert not any(
        line.startswith("IZANAGI_GROWTH_HOLD_SUMMARY_V1 ") for line in lines
    )


def _run() -> int:
    """Run fixture and parametrized nodes without a plain-runner false green."""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
