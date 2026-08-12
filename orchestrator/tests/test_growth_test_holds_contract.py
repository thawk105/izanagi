"""Non-tautological contract tests for repository-growth test holds."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import orchestrator.tests.conftest as CONF
from orchestrator.tests.growth_test_holds import (
    GROWTH_TEST_HOLDS,
    RUN_GROWTH_HELD_TESTS_ENV,
    RUN_GROWTH_HELD_TESTS_TOKEN,
    GrowthTestHold,
    _validate_hold_rows,
    growth_test_hold_inventory,
    growth_test_hold_key_digest,
)
from tools import run_tests as RT


_EXPECTED_HOLD_COUNT = 30
_EXPECTED_KEY_SHA256 = "8e4917269631347e1a78c2ac82875efc6ac509bba1181037ee7fab26208f6205"
_EXPECTED_ROW_CONTRACT_SHA256 = "442229f582a373223c332c10f02936df51465ea5ca8b558830b8779166392509"
_HELD_SERIAL_NODE = (
    "test_s8b_repo_scan_invariant.py::"
    "test_real_repository_scan_matches_known_hits_and_has_positive_control"
)
_META_NODE = (
    "test_growth_test_holds_contract.py::test_contract_module_is_not_held"
)


class _Item:
    def __init__(self, node_id: str):
        filename, function = node_id.split("::", 1)
        self.path = Path("/synthetic") / filename
        self.name = function
        self.originalname = function
        self.user_properties: list[tuple[str, object]] = []
        self._markers = []

    def add_marker(self, marker, append: bool = True) -> None:
        mark = getattr(marker, "mark", marker)
        if append:
            self._markers.append(mark)
        else:
            self._markers.insert(0, mark)

    def iter_markers(self, name: str | None = None):
        return (
            marker for marker in self._markers
            if name is None or marker.name == name
        )


class _Terminal:
    def __init__(self):
        self.lines: list[str] = []

    def write_line(self, line: str) -> None:
        self.lines.append(line)


def _config(*, complete: bool = False, terminal=None):
    root = Path(CONF.__file__).resolve().parent
    pluginmanager = SimpleNamespace(
        get_plugin=lambda name: terminal if name == "terminalreporter" else None,
    )
    return SimpleNamespace(
        args=[str(root if complete else root / "test_growth_test_holds_contract.py")],
        invocation_params=SimpleNamespace(args=()),
        pluginmanager=pluginmanager,
        option=SimpleNamespace(numprocesses=None),
    )


def _run_collection_hook(config, items) -> None:
    wrapper = CONF.pytest_collection_modifyitems(config, items)
    next(wrapper)
    with pytest.raises(StopIteration):
        next(wrapper)


def _literal_hold(**changes) -> GrowthTestHold:
    hold = GrowthTestHold(
        hold_axis="commits",
        ruling="2026-08-12 rulings 第 3 束",
        reason="synthetic valid reason",
        correctness_gate=True,
        release_condition="explicit-user-command-only",
        measured_seconds=None,
    )
    return replace(hold, **changes)


def _row_contract_digest() -> str:
    payload = json.dumps(
        [
            [key, hold.hold_axis, hold.ruling, hold.correctness_gate]
            for key, hold in sorted(GROWTH_TEST_HOLDS.items())
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_inventory_count_and_key_digest_are_independently_pinned():
    assert len(GROWTH_TEST_HOLDS) == _EXPECTED_HOLD_COUNT
    assert growth_test_hold_key_digest(GROWTH_TEST_HOLDS) == _EXPECTED_KEY_SHA256
    assert _row_contract_digest() == _EXPECTED_ROW_CONTRACT_SHA256


def test_registry_rows_preserve_current_wave_contract():
    assert {hold.ruling for hold in GROWTH_TEST_HOLDS.values()} == {
        "2026-08-12 rulings 第 3 束",
    }
    assert all(hold.correctness_gate is True for hold in GROWTH_TEST_HOLDS.values())
    assert all(hold.measured_seconds is None for hold in GROWTH_TEST_HOLDS.values())
    assert all(
        hold.release_condition == "explicit-user-command-only"
        for hold in GROWTH_TEST_HOLDS.values()
    )
    assert not any(
        key.startswith("test_s8b_ratified_verify.py::")
        or key.startswith("test_silo_ladder_rung1_evidence.py::")
        or key == (
            "test_s8b_oracle_driver.py::"
            "test_nonnull_floor_without_active_generation_is_refused"
        )
        for key in GROWTH_TEST_HOLDS
    )


@pytest.mark.parametrize(
    ("key", "hold"),
    [
        ("test_file.py::test_name", _literal_hold(correctness_gate="false")),
        ("test_file.py::test_name", _literal_hold(release_condition="automatic")),
        ("test_file.py:test_name_typo", _literal_hold()),
        ("test_file.py::test_name", _literal_hold(reason=" ")),
        ("test_file.py::test_name", _literal_hold(ruling="\t")),
        ("test_file.py::test_name", _literal_hold(hold_axis="repository_size")),
        ("test_file.py::test_name", _literal_hold(measured_seconds=float("inf"))),
        ("test_file.py::test_name", _literal_hold(measured_seconds=-0.1)),
        ("test_file.py::test_name", _literal_hold(measured_seconds=False)),
        ("test_file.py::test_name", _literal_hold(collateral_note=" \t")),
        ("test_file.py::test_name", _literal_hold(collateral_note=0)),
    ],
)
def test_schema_negative_controls_are_rejected(key, hold):
    with pytest.raises(ValueError):
        _validate_hold_rows(((key, hold),))


def test_empty_and_duplicate_registries_are_rejected():
    with pytest.raises(ValueError):
        _validate_hold_rows(())
    row = ("test_file.py::test_name", _literal_hold())
    with pytest.raises(ValueError):
        _validate_hold_rows((row, row))


def test_collection_hook_attaches_skip_metadata_and_prints_early_summary(monkeypatch):
    monkeypatch.delenv(RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    terminal = _Terminal()
    config = _config(terminal=terminal)
    item = _Item(_HELD_SERIAL_NODE)

    _run_collection_hook(config, [item])

    skip_marks = list(item.iter_markers(name="skip"))
    assert len(skip_marks) == 1
    reason = skip_marks[0].kwargs["reason"]
    assert reason.startswith("IZANAGI_GROWTH_HOLD_V1 ")
    payload = json.loads(reason.split(" ", 1)[1])
    assert payload["node_id"] == _HELD_SERIAL_NODE
    assert payload["hold_axis"] == "tracked_files"
    assert payload["correctness_gate"] is True
    assert payload["release_condition"] == "explicit-user-command-only"
    assert [mark.args for mark in item.iter_markers(name="xdist_group")] == [
        ("real-repo",),
    ]
    assert dict(item.user_properties) == {
        "growth_hold_node_id": _HELD_SERIAL_NODE,
        "growth_hold_axis": "tracked_files",
        "growth_hold_correctness_gate": True,
        "growth_hold_release_condition": "explicit-user-command-only",
    }

    session = SimpleNamespace(config=config)
    CONF.pytest_sessionfinish(session, 0)
    assert terminal.lines[0].startswith("IZANAGI_GROWTH_HOLD_SUMMARY_V1 ")
    assert terminal.lines[1] == reason


def test_collection_hook_opt_in_keeps_real_repo_serialization_without_skip(monkeypatch):
    monkeypatch.setenv(RUN_GROWTH_HELD_TESTS_ENV, RUN_GROWTH_HELD_TESTS_TOKEN)
    item = _Item(_HELD_SERIAL_NODE)

    _run_collection_hook(_config(), [item])

    assert list(item.iter_markers(name="skip")) == []
    assert [mark.args for mark in item.iter_markers(name="xdist_group")] == [
        ("real-repo",),
    ]


def test_collection_hook_rejects_opt_in_typo(monkeypatch):
    monkeypatch.setenv(RUN_GROWTH_HELD_TESTS_ENV, "explicit-user-commnad")
    wrapper = CONF.pytest_collection_modifyitems(_config(), [_Item(_HELD_SERIAL_NODE)])
    with pytest.raises(pytest.UsageError):
        next(wrapper)


def test_complete_collection_rejects_valid_shape_function_typo(monkeypatch):
    typo = (
        "test_s8b_repo_scan_invariant.py::"
        "test_real_repository_scan_matches_known_hits_and_has_positive_control_typo"
    )
    monkeypatch.delenv(RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    monkeypatch.setattr(CONF, "GROWTH_TEST_HOLDS", {typo: _literal_hold()})
    wrapper = CONF.pytest_collection_modifyitems(
        _config(complete=True), [_Item(_HELD_SERIAL_NODE)],
    )
    with pytest.raises(pytest.UsageError, match="missing from complete collection"):
        next(wrapper)


def test_contract_module_is_not_held():
    assert _META_NODE not in GROWTH_TEST_HOLDS
    assert not any(
        key.startswith("test_growth_test_holds_contract.py::")
        for key in GROWTH_TEST_HOLDS
    )


def test_inventory_output_is_sorted_exact_and_marks_correctness_gates():
    first = growth_test_hold_inventory()
    second = growth_test_hold_inventory()
    assert first == second
    keys = sorted(GROWTH_TEST_HOLDS)
    assert first["count"] == _EXPECTED_HOLD_COUNT
    assert first["key_sha256"] == _EXPECTED_KEY_SHA256
    assert first["correctness_gate_keys"] == keys
    assert [row["node_id"] for row in first["holds"]] == keys
    assert all(row["correctness_gate"] is True for row in first["holds"])
    rows = {row["node_id"]: row for row in first["holds"]}
    assert all("collateral_note" in row for row in rows.values())
    assert {
        key: row["collateral_note"]
        for key, row in rows.items()
        if row["collateral_note"] is not None
    } == {
        "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight": (
            "Holding this node also removes fixed-size checks for the maximum "
            "package, MAX_CANDIDATES/MAX_QUERY_COUNT/MAX_SIGNAL_TOKENS, "
            "independent inspect/pickaxe evidence, and the 45/60-second "
            "preflight boundaries."
        ),
        "test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies": (
            "Holding this node also removes fixed-size checks for corpus count 48, "
            "disjoint success/failure sets, and the complete JSON-pair partition."
        ),
    }


def test_opt_in_changes_only_suite_identity_not_acceptance_shape(monkeypatch):
    assert RT._RUN_GROWTH_HELD_TESTS_ENV == RUN_GROWTH_HELD_TESTS_ENV
    assert RT._RUN_GROWTH_HELD_TESTS_TOKEN == RUN_GROWTH_HELD_TESTS_TOKEN
    regular = RT._suite_identity([], "", run_growth_held_tests=False)
    opted_in = RT._suite_identity([], "", run_growth_held_tests=True)
    assert regular == ("full", "pytest-orchestrator-full")
    assert opted_in == ("full", "pytest-orchestrator-full-growth-held-opt-in")
    targeted_regular = RT._suite_identity(["test_file.py"], "", run_growth_held_tests=False)
    targeted_opted_in = RT._suite_identity(
        ["test_file.py"], "", run_growth_held_tests=True,
    )
    assert targeted_regular[0] == targeted_opted_in[0] == "targeted"
    assert targeted_regular[1] != targeted_opted_in[1]

    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv(RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    before = (
        RT._is_full_suite([], ""),
        RT._has_no_execution_flag([]),
        RT._has_dispatch_exempt_flag([]),
        RT._is_acceptance_run([]),
    )
    monkeypatch.setenv(RUN_GROWTH_HELD_TESTS_ENV, RUN_GROWTH_HELD_TESTS_TOKEN)
    after = (
        RT._is_full_suite([], ""),
        RT._has_no_execution_flag([]),
        RT._has_dispatch_exempt_flag([]),
        RT._is_acceptance_run([]),
    )
    assert after == before
