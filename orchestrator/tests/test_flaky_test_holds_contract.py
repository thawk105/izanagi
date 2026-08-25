"""Executable contract for the evidence-backed flaky-node quarantine."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
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
_SIBLING_NODE = (
    "orchestrator/tests/test_mutation_harness.py::"
    "test_cumulative_replacement_uses_the_result_of_the_previous_anchor"
)
_FOCUS_NODE = (
    "orchestrator/tests/test_campaign_claim.py::"
    "test_read_proc_starttime_uses_field_22_with_spaced_comm"
)
_STALE_NODE = "orchestrator/tests/test_t1551_stale.py::test_missing_hold"
_SECOND_STALE_NODE = (
    "orchestrator/tests/test_t1551_stale.py::test_second_missing_hold"
)
_STALE_NODES = (_STALE_NODE, _SECOND_STALE_NODE)
_INJECTION_MARKER_PREFIX = "IZANAGI_FLAKY_REGISTRY_INJECTION_V1 "
_LAZY_LOAD_MARKER_PREFIX = "IZANAGI_FLAKY_REGISTRY_LAZY_LOAD_V1 "
_EMPTY_REGISTRY_SHA256 = (
    "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
)


def _synthetic_valid_hold() -> REG.FlakyTestHold:
    """Return the removed F57 row as a test-only complete hold."""
    return REG.FlakyTestHold(
        known_failure_node_ids=frozenset({_HELD_NODE}),
        same_tree=True,
        green_observation=(
            "同一 tree の同 file 単独実走は 80 passed で再現しなかった"
        ),
        green_collection_condition="single-file",
        green_run_count=1,
        red_observation=(
            "同一 tree の受入全走で gw28 が 1 failed / 11866 passed / 92 skipped"
        ),
        red_collection_condition=REG.ACCEPTANCE_COLLECTION,
        failure_signature=(
            "SIGTERM 送信前に子が rc=1 で終了して 128 + SIGTERM を観測できなかった"
        ),
        cause="隣接 wave の子による資源競合で、子が SIGTERM 到達前に終了する",
        evidence_id="F57",
        reintroduction_task_id="{{T:flaky-sigterm-sync-point}}",
    )


def _stale_sentinels(*node_ids: str) -> dict[str, object]:
    return {node_id: object() for node_id in node_ids}


def _hold_constructor_fields(hold: REG.FlakyTestHold) -> dict[str, object]:
    return {
        "known_failure_node_ids": sorted(hold.known_failure_node_ids),
        "same_tree": hold.same_tree,
        "green_observation": hold.green_observation,
        "green_collection_condition": hold.green_collection_condition,
        "green_run_count": hold.green_run_count,
        "red_observation": hold.red_observation,
        "red_collection_condition": hold.red_collection_condition,
        "failure_signature": hold.failure_signature,
        "cause": hold.cause,
        "evidence_id": hold.evidence_id,
        "reintroduction_task_id": hold.reintroduction_task_id,
    }


def _write_registry_injection_plugin(
    tmp_path: Path,
    *,
    plugin_name: str,
    matched_holds: Mapping[str, REG.FlakyTestHold],
    stale_sentinels: Mapping[str, object],
) -> str:
    """Write one test-only plugin with distinct matched and stale value paths."""
    if not matched_holds and not stale_sentinels:
        raise AssertionError("registry injection must be nonempty")
    if set(matched_holds) & set(stale_sentinels):
        raise AssertionError("matched and stale injection node IDs must be disjoint")
    if any(not isinstance(hold, REG.FlakyTestHold) for hold in matched_holds.values()):
        raise AssertionError("matched injection requires complete FlakyTestHold values")
    if any(isinstance(value, REG.FlakyTestHold) for value in stale_sentinels.values()):
        raise AssertionError("stale injection requires sentinel values")

    matched_rows = {
        node_id: _hold_constructor_fields(hold)
        for node_id, hold in matched_holds.items()
    }
    stale_node_ids = tuple(stale_sentinels)
    injected_sha256 = REG.flaky_test_hold_registry_sha256(matched_holds)
    production_conftest = Path(CONF.__file__).resolve()
    plugin_source = f'''\
import json
from pathlib import Path
import sys

import pytest

from orchestrator.tests.flaky_test_holds import FlakyTestHold

_PRODUCTION_CONFTEST = Path({str(production_conftest)!r})
_MATCHED_HOLD_ROWS = {matched_rows!r}
_STALE_NODE_IDS = {stale_node_ids!r}
_REGISTRY_SHA256 = {injected_sha256!r}
_MARKER_PREFIX = {_INJECTION_MARKER_PREFIX!r}


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    targets = {{}}
    for _name, plugin in config.pluginmanager.list_name_plugin():
        plugin_file = getattr(plugin, "__file__", None)
        if plugin_file is None:
            continue
        try:
            candidate = Path(plugin_file).resolve()
        except (OSError, TypeError, ValueError):
            continue
        if candidate == _PRODUCTION_CONFTEST:
            targets[id(plugin)] = plugin
    if len(targets) != 1:
        raise pytest.UsageError(
            "IZANAGI_FLAKY_REGISTRY_INJECTION_TARGET_ERROR "
            f"target_count={{len(targets)}}"
        )

    target = next(iter(targets.values()))
    original = target.FLAKY_TEST_HOLDS
    if original:
        raise pytest.UsageError("IZANAGI_FLAKY_REGISTRY_INJECTION_EXPECTED_EMPTY")
    patched = dict(original)
    for node_id, fields in _MATCHED_HOLD_ROWS.items():
        patched[node_id] = FlakyTestHold(
            known_failure_node_ids=frozenset(fields["known_failure_node_ids"]),
            same_tree=fields["same_tree"],
            green_observation=fields["green_observation"],
            green_collection_condition=fields["green_collection_condition"],
            green_run_count=fields["green_run_count"],
            red_observation=fields["red_observation"],
            red_collection_condition=fields["red_collection_condition"],
            failure_signature=fields["failure_signature"],
            cause=fields["cause"],
            evidence_id=fields["evidence_id"],
            reintroduction_task_id=fields["reintroduction_task_id"],
        )
    stale_sentinel = object()
    for node_id in _STALE_NODE_IDS:
        patched[node_id] = stale_sentinel
    target.FLAKY_TEST_HOLDS = patched
    target.FLAKY_TEST_HOLD_NODE_IDS = frozenset(patched)
    target.FLAKY_TEST_HOLDS_SHA256 = _REGISTRY_SHA256
    payload = {{
        "matched_node_ids": sorted(_MATCHED_HOLD_ROWS),
        "stale_node_ids": list(_STALE_NODE_IDS),
        "target_count": len(targets),
    }}
    print(
        _MARKER_PREFIX + json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )
'''
    (tmp_path / f"{plugin_name}.py").write_text(plugin_source, encoding="utf-8")
    return plugin_name


def _subprocess_environment(tmp_path: Path) -> dict[str, str]:
    environment = os.environ.copy()
    for name in (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_DEBUG",
        "PYTEST_XDIST_WORKER",
        "PYTEST_XDIST_WORKER_COUNT",
        "PYTEST_XDIST_TESTRUNUID",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    ):
        environment.pop(name, None)
    environment["NO_COLOR"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        value
        for value in (str(tmp_path), environment.get("PYTHONPATH"))
        if value
    )
    return environment


def _assert_injection_marker(
    output: str,
    *,
    matched_node_ids: list[str],
    stale_node_ids: list[str],
    expected_line_count: int | None = 1,
) -> None:
    marker_lines = [
        line for line in output.splitlines()
        if line.startswith(_INJECTION_MARKER_PREFIX)
    ]
    assert marker_lines, output
    if expected_line_count is not None:
        assert len(marker_lines) == expected_line_count, output
    expected_payload = {
        "matched_node_ids": matched_node_ids,
        "stale_node_ids": stale_node_ids,
        "target_count": 1,
    }
    for marker_line in marker_lines:
        payload = json.loads(marker_line[len(_INJECTION_MARKER_PREFIX):])
        assert payload == expected_payload


def _expected_flaky_summary_line(
    registry: Mapping[str, REG.FlakyTestHold],
    *,
    matched_node_count: int,
    skipped_node_count: int,
) -> str:
    return "IZANAGI_FLAKY_HOLD_SUMMARY_V1 " + json.dumps(
        {
            "registered_node_count": len(registry),
            "matched_node_count": matched_node_count,
            "skipped_node_count": skipped_node_count,
            "registry_sha256": REG.flaky_test_hold_registry_sha256(registry),
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )


def test_initial_registry_is_empty_without_weakening_nonempty_validation() -> None:
    assert REG._FLAKY_TEST_HOLD_ROWS == ()
    assert dict(REG.FLAKY_TEST_HOLDS) == {}
    assert REG.FLAKY_TEST_HOLD_NODE_IDS == frozenset()
    assert REG.FLAKY_TEST_HOLD_NODE_IDS == frozenset(REG.FLAKY_TEST_HOLDS)
    assert REG.FLAKY_TEST_HOLDS_SHA256 == _EMPTY_REGISTRY_SHA256
    assert REG.FLAKY_TEST_HOLDS_SHA256 == (
        REG.flaky_test_hold_registry_sha256(REG.FLAKY_TEST_HOLDS)
    )
    assert REG.flaky_test_hold_registry_sha256({}) == _EMPTY_REGISTRY_SHA256

    validated_empty = REG.validate_flaky_test_hold_rows(())
    assert dict(validated_empty) == {}
    with pytest.raises(TypeError):
        validated_empty[_HELD_NODE] = _synthetic_valid_hold()  # type: ignore[index]

    synthetic = _synthetic_valid_hold()
    validated_nonempty = REG.validate_flaky_test_hold_rows(((_HELD_NODE, synthetic),))
    assert dict(validated_nonempty) == {_HELD_NODE: synthetic}


def test_production_export_wiring_derives_nonempty_registry_from_rows(
    tmp_path: Path,
) -> None:
    source = Path(REG.__file__).read_text(encoding="utf-8")
    rows_assignment = "_FLAKY_TEST_HOLD_ROWS = ()"
    assert source.count(rows_assignment) == 1
    synthetic_rows = (
        "_FLAKY_TEST_HOLD_ROWS = (("
        f"{_HELD_NODE!r}, {_synthetic_valid_hold()!r}"
        "),)"
    )

    module_path = tmp_path / "orchestrator" / "tests" / "flaky_test_holds.py"
    module_path.parent.mkdir(parents=True)
    module_path.write_text(
        source.replace(rows_assignment, synthetic_rows),
        encoding="utf-8",
    )
    ledger = tmp_path / "docs" / "failures.md"
    ledger.parent.mkdir()
    ledger.write_bytes((_REPO / "docs" / "failures.md").read_bytes())

    module_name = f"_izanagi_synthetic_flaky_registry_{tmp_path.name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)

    assert tuple(module._FLAKY_TEST_HOLD_ROWS)
    derived = module.validate_flaky_test_hold_rows(module._FLAKY_TEST_HOLD_ROWS)
    assert dict(module.FLAKY_TEST_HOLDS) == dict(derived)
    assert module.FLAKY_TEST_HOLD_NODE_IDS == frozenset(module.FLAKY_TEST_HOLDS)
    assert module.FLAKY_TEST_HOLDS_SHA256 == (
        module.flaky_test_hold_registry_sha256(module.FLAKY_TEST_HOLDS)
    )


def test_production_export_wiring_rejects_invalid_rows_during_import(
    tmp_path: Path,
) -> None:
    source = Path(REG.__file__).read_text(encoding="utf-8")
    rows_assignment = "_FLAKY_TEST_HOLD_ROWS = ()"
    assert source.count(rows_assignment) == 1
    invalid = replace(_synthetic_valid_hold(), red_observation="")
    invalid_rows = (
        "_FLAKY_TEST_HOLD_ROWS = (("
        f"{_HELD_NODE!r}, {invalid!r}"
        "),)"
    )

    module_path = tmp_path / "orchestrator" / "tests" / "flaky_test_holds.py"
    module_path.parent.mkdir(parents=True)
    module_path.write_text(
        source.replace(rows_assignment, invalid_rows),
        encoding="utf-8",
    )
    ledger = tmp_path / "docs" / "failures.md"
    ledger.parent.mkdir()
    ledger.write_bytes((_REPO / "docs" / "failures.md").read_bytes())

    module_name = f"_izanagi_invalid_flaky_registry_{tmp_path.name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        with pytest.raises(ValueError):
            spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)


def test_registry_module_lazy_loader_drives_collection_skip_and_summary(
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "registry-root"
    registry_source = Path(REG.__file__).read_text(encoding="utf-8")
    rows_assignment = "_FLAKY_TEST_HOLD_ROWS = ()"
    assert registry_source.count(rows_assignment) == 1
    synthetic_rows = (
        "_FLAKY_TEST_HOLD_ROWS = (("
        f"{_HELD_NODE!r}, {_synthetic_valid_hold()!r}"
        "),)"
    )
    registry_path = (
        registry_root / "orchestrator" / "tests" / "flaky_test_holds.py"
    )
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        registry_source.replace(rows_assignment, synthetic_rows),
        encoding="utf-8",
    )
    ledger = registry_root / "docs" / "failures.md"
    ledger.parent.mkdir()
    ledger.write_bytes((_REPO / "docs" / "failures.md").read_bytes())

    sibling_node = (
        "orchestrator/tests/test_mutation_harness.py::"
        "test_registry_loader_sibling"
    )
    suite_root = tmp_path / "suite-root"
    test_module = suite_root / "orchestrator" / "tests" / "test_mutation_harness.py"
    test_module.parent.mkdir(parents=True)
    test_module.write_text(
        "def test_sigterm_handler_stops_child_and_restores_active_mutation():\n"
        "    raise AssertionError('held node executed')\n\n"
        "def test_registry_loader_sibling():\n"
        "    pass\n",
        encoding="utf-8",
    )

    bootstrap_path = tmp_path / "lazy_registry_bootstrap.py"
    bootstrap_path.write_text(
        f'''\
import builtins
import importlib.util
import json
from pathlib import Path
import sys

import pytest

_REPO = Path({str(_REPO)!r})
_CONFTEST_PATH = Path({str(Path(CONF.__file__).resolve())!r})
_REGISTRY_PATH = Path({str(registry_path)!r})
_ORIGINAL_IMPORT = builtins.__import__


def _block_initial_flaky_registry(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name == "orchestrator.tests.flaky_test_holds":
        raise ModuleNotFoundError(
            "test-only deferred flaky registry import",
            name="orchestrator",
        )
    return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


sys.path.insert(0, str(_REPO))
conftest_name = "_izanagi_production_conftest_lazy_bridge"
conftest_spec = importlib.util.spec_from_file_location(
    conftest_name,
    _CONFTEST_PATH,
)
if conftest_spec is None or conftest_spec.loader is None:
    raise RuntimeError("production conftest spec unavailable")
production_conftest = importlib.util.module_from_spec(conftest_spec)
sys.modules[conftest_name] = production_conftest
builtins.__import__ = _block_initial_flaky_registry
try:
    conftest_spec.loader.exec_module(production_conftest)
finally:
    builtins.__import__ = _ORIGINAL_IMPORT

lazy_before_collection = production_conftest.FLAKY_TEST_HOLDS is None
if not lazy_before_collection:
    raise RuntimeError("production conftest did not retain the lazy registry state")

registry_name = "orchestrator.tests.flaky_test_holds"
registry_spec = importlib.util.spec_from_file_location(
    registry_name,
    _REGISTRY_PATH,
)
if registry_spec is None or registry_spec.loader is None:
    raise RuntimeError("synthetic registry spec unavailable")
synthetic_registry = importlib.util.module_from_spec(registry_spec)
sys.modules[registry_name] = synthetic_registry
tests_package = sys.modules.get("orchestrator.tests")
if tests_package is None:
    raise RuntimeError("orchestrator.tests package unavailable")
setattr(tests_package, "flaky_test_holds", synthetic_registry)
registry_spec.loader.exec_module(synthetic_registry)

exit_code = pytest.main(
    ["--color=no", "-vv", "-rs", {_HELD_NODE!r}, {sibling_node!r}],
    plugins=[production_conftest],
)
loaded_registry = production_conftest.FLAKY_TEST_HOLDS
payload = {{
    "lazy_before_collection": lazy_before_collection,
    "loaded_registry_count": (
        None if loaded_registry is None else len(loaded_registry)
    ),
    "registry_identity_preserved": (
        loaded_registry is synthetic_registry.FLAKY_TEST_HOLDS
    ),
    "registry_sha256": production_conftest.FLAKY_TEST_HOLDS_SHA256,
}}
print(
    {_LAZY_LOAD_MARKER_PREFIX!r}
    + json.dumps(payload, sort_keys=True, separators=(",", ":")),
    flush=True,
)
raise SystemExit(int(exit_code))
''',
        encoding="utf-8",
    )

    environment = _subprocess_environment(tmp_path)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [sys.executable, str(bootstrap_path)],
        cwd=suite_root,
        env=environment,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )

    assert result.returncode == 0, result.stdout
    assert f"{_HELD_NODE} SKIPPED" in result.stdout
    assert f"{sibling_node} PASSED" in result.stdout
    assert re.search(r"\b1 passed\b", result.stdout)
    assert re.search(r"\b1 skipped\b", result.stdout)
    expected_registry = {_HELD_NODE: _synthetic_valid_hold()}
    expected_summary = _expected_flaky_summary_line(
        expected_registry,
        matched_node_count=1,
        skipped_node_count=1,
    )
    assert result.stdout.splitlines().count(expected_summary) == 1, result.stdout
    marker_lines = [
        line for line in result.stdout.splitlines()
        if line.startswith(_LAZY_LOAD_MARKER_PREFIX)
    ]
    assert len(marker_lines) == 1, result.stdout
    marker_payload = json.loads(
        marker_lines[0][len(_LAZY_LOAD_MARKER_PREFIX):]
    )
    assert marker_payload == {
        "lazy_before_collection": True,
        "loaded_registry_count": 1,
        "registry_identity_preserved": True,
        "registry_sha256": REG.flaky_test_hold_registry_sha256(
            expected_registry
        ),
    }


def test_real_pytest_subprocess_skips_registered_node_and_runs_same_file_sibling(
    tmp_path: Path,
) -> None:
    plugin_name = _write_registry_injection_plugin(
        tmp_path,
        plugin_name="t1548_matched_registry_injector",
        matched_holds={_HELD_NODE: _synthetic_valid_hold()},
        stale_sentinels={},
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "-vv",
            "-rs",
            "-p",
            plugin_name,
            _HELD_NODE,
            _SIBLING_NODE,
        ],
        cwd=_REPO,
        env=_subprocess_environment(tmp_path),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout
    assert f"{_HELD_NODE} SKIPPED" in result.stdout
    assert f"{_SIBLING_NODE} PASSED" in result.stdout
    assert re.search(r"\b1 passed\b", result.stdout)
    assert re.search(r"\b1 skipped\b", result.stdout)
    assert "IZANAGI_FLAKY_HOLD_V1" in result.stdout
    expected_summary = _expected_flaky_summary_line(
        {_HELD_NODE: _synthetic_valid_hold()},
        matched_node_count=1,
        skipped_node_count=1,
    )
    assert result.stdout.splitlines().count(expected_summary) == 1, result.stdout
    _assert_injection_marker(
        result.stdout,
        matched_node_ids=[_HELD_NODE],
        stale_node_ids=[],
    )


def test_xdist_subprocess_focus_collection_does_not_run_stale_check(
    tmp_path: Path,
) -> None:
    plugin_name = _write_registry_injection_plugin(
        tmp_path,
        plugin_name="t1548_narrowed_stale_registry_injector",
        matched_holds={},
        stale_sentinels=_stale_sentinels(*_STALE_NODES),
    )
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
            "-p",
            plugin_name,
            _FOCUS_NODE,
        ],
        cwd=_REPO,
        env=_subprocess_environment(tmp_path),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout
    assert "missing from complete collection" not in result.stdout
    assert re.search(r"\b1 passed\b", result.stdout)
    _assert_injection_marker(
        result.stdout,
        matched_node_ids=[],
        stale_node_ids=list(_STALE_NODES),
        expected_line_count=None,
    )


def test_requested_xdist_collect_only_effective_serial_rejects_stale_registry(
    tmp_path: Path,
) -> None:
    plugin_name = _write_registry_injection_plugin(
        tmp_path,
        plugin_name="t1548_complete_stale_registry_injector",
        matched_holds={},
        stale_sentinels=_stale_sentinels(*_STALE_NODES),
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "-p",
            plugin_name,
            "-n",
            "2",
            "--dist",
            "load",
            "--collect-only",
            str(Path(CONF.__file__).resolve().parent),
        ],
        cwd=_REPO,
        env=_subprocess_environment(tmp_path),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    assert result.returncode == int(pytest.ExitCode.USAGE_ERROR), result.stdout
    _assert_injection_marker(
        result.stdout,
        matched_node_ids=[],
        stale_node_ids=list(_STALE_NODES),
    )
    expected_missing = (
        "flaky-test hold keys missing from complete collection: "
        f"{sorted(_STALE_NODES)!r}"
    )
    assert expected_missing in result.stdout
    scheduler_marker = (
        'IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"serial"}'
    )
    assert result.stdout.splitlines().count(scheduler_marker) == 1, result.stdout


def test_mutation_harness_rejects_an_isolated_expected_failure_node(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "orchestrator" / "tests" / "flaky_test_holds.py"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        f"FLAKY_TEST_HOLD_NODE_IDS = {frozenset({_HELD_NODE})!r}\n",
        encoding="utf-8",
    )
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
            tmp_path,
            SimpleNamespace(mutations=(mutation,)),
            {},
        )


def test_mutation_harness_does_not_import_holds_from_another_checkout(
    tmp_path: Path,
) -> None:
    assert MH._flaky_hold_node_ids_for_policy(tmp_path) == frozenset()
    live = MH._flaky_hold_node_ids_for_policy(_REPO)
    assert isinstance(live, frozenset)
    assert live == frozenset()


@pytest.mark.parametrize(
    ("condition", "changes"),
    [
        ("green and red evidence", {"green_observation": ""}),
        ("red observation", {"red_observation": ""}),
        ("green collection condition", {"green_collection_condition": ""}),
        (
            "red collection condition",
            {
                "green_collection_condition": REG.ACCEPTANCE_COLLECTION,
                "red_collection_condition": "",
            },
        ),
        ("green run count zero", {"green_run_count": 0}),
        ("green run count negative", {"green_run_count": -1}),
        ("green run count bool", {"green_run_count": True}),
        ("green run count non-int", {"green_run_count": 1.0}),
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
        (
            "known failure node IDs type",
            {"known_failure_node_ids": {_HELD_NODE}},
        ),
    ],
)
def test_each_acceptance_condition_has_a_rejected_negative_control(
    condition: str,
    changes: dict[str, object],
) -> None:
    del condition
    invalid = replace(_synthetic_valid_hold(), **changes)
    with pytest.raises(ValueError):
        REG.validate_flaky_test_hold_rows(((_HELD_NODE, invalid),))


@pytest.mark.parametrize("condition", ["node ID format", "hold type"])
def test_registry_row_key_and_hold_type_are_rejected(condition: str) -> None:
    if condition == "node ID format":
        invalid_node = (
            "orchestrator/tests/test_mutation_harness.txt::"
            "test_sigterm_handler_stops_child_and_restores_active_mutation"
        )
        invalid_hold = replace(
            _synthetic_valid_hold(),
            known_failure_node_ids=frozenset({invalid_node}),
        )
        rows = ((invalid_node, invalid_hold),)
    else:
        rows = ((_HELD_NODE, object()),)
    with pytest.raises(ValueError):
        REG.validate_flaky_test_hold_rows(rows)  # type: ignore[arg-type]


def test_acceptance_collection_evidence_is_required() -> None:
    invalid = replace(
        _synthetic_valid_hold(),
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
        _synthetic_valid_hold(),
        known_failure_node_ids=frozenset({unrecorded_node}),
    )
    with pytest.raises(ValueError, match="does not mention test function"):
        REG.validate_flaky_test_hold_rows(((unrecorded_node, invalid),))


def test_evidence_section_must_contain_failure_signature() -> None:
    invalid = replace(
        _synthetic_valid_hold(),
        failure_signature="unrelated failure signature",
    )
    with pytest.raises(ValueError, match="failure_signature"):
        REG.validate_flaky_test_hold_rows(((_HELD_NODE, invalid),))


def test_complete_collection_rejects_a_stale_registered_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale_sentinel = object()
    monkeypatch.setattr(CONF, "FLAKY_TEST_HOLDS", {_STALE_NODE: stale_sentinel})
    monkeypatch.setattr(CONF, "FLAKY_TEST_HOLD_NODE_IDS", frozenset({_STALE_NODE}))
    with pytest.raises(pytest.UsageError, match="missing from complete collection"):
        CONF._check_flaky_hold_collection_complete(SimpleNamespace(), ())


def test_shard_controller_does_not_recheck_its_selected_xdist_subset() -> None:
    config = SimpleNamespace(
        args=[str(Path(CONF.__file__).resolve().parent)],
        invocation_params=SimpleNamespace(args=()),
        pluginmanager=SimpleNamespace(
            get_plugin=lambda name: SimpleNamespace(
                sched=SimpleNamespace(numnodes=1),
            ) if name == "dsession" else None,
        ),
        _izanagi_flaky_hold_collection_workers={"gw0"},
    )
    assert CONF._xdist_flaky_collection_is_complete(config) is True

    config._izanagi_acceptance_shard_spec = object()
    assert CONF._xdist_flaky_collection_is_complete(config) is False

    config.workerinput = {}
    assert CONF._is_complete_flaky_hold_collection(config) is True


def test_xdist_collection_hook_rejects_stale_registry_only_after_all_workers_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """これは受理集合の正しさゲートではなく diagnostic sensitivity pin である。

    stale の拒否は実 xdist の各 worker も同じ検査を行うため、controller 側の
    再検査は冗長である。ただし hook 本体の ``_note_flaky_hold`` 集約は冗長ではない。
    これは ``IZANAGI_FLAKY_HOLD_SUMMARY_V1`` を生成する唯一の controller 入力であり、
    集約が消えると受理集合は同じまま summary 行が失われる。この test は pluggy の
    実配送を証明しない。
    """
    patched_holds = {
        _HELD_NODE: _synthetic_valid_hold(),
        _STALE_NODE: object(),
    }
    monkeypatch.setattr(CONF, "FLAKY_TEST_HOLDS", patched_holds)
    monkeypatch.setattr(
        CONF, "FLAKY_TEST_HOLD_NODE_IDS", frozenset(patched_holds),
    )
    config = SimpleNamespace(
        args=[str(Path(CONF.__file__).resolve().parent)],
        invocation_params=SimpleNamespace(args=()),
        pluginmanager=SimpleNamespace(
            get_plugin=lambda name: SimpleNamespace(
                sched=SimpleNamespace(numnodes=2),
            ) if name == "dsession" else None,
        ),
    )
    first = SimpleNamespace(
        config=config,
        gateway=SimpleNamespace(id="gw0"),
    )
    second = SimpleNamespace(
        config=config,
        gateway=SimpleNamespace(id="gw1"),
    )

    CONF.pytest_xdist_node_collection_finished(first, [_HELD_NODE])
    with pytest.raises(pytest.UsageError) as error:
        CONF.pytest_xdist_node_collection_finished(second, [])

    message = str(error.value)
    assert message.endswith(repr([_STALE_NODE]))
    assert _HELD_NODE not in message


def test_flaky_summary_is_separate_and_uses_registry_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines: list[str] = []

    class Terminal:
        def write_line(self, line: str) -> None:
            lines.append(line)

    config = SimpleNamespace(
        invocation_params=SimpleNamespace(args=()),
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
        "registered_node_count": 0,
        "matched_node_count": 0,
        "skipped_node_count": 0,
        "registry_sha256": REG.FLAKY_TEST_HOLDS_SHA256,
    }
    assert payload["registry_sha256"] == _EMPTY_REGISTRY_SHA256
    assert not any(
        line.startswith("IZANAGI_GROWTH_HOLD_SUMMARY_V1 ") for line in lines
    )

    synthetic_holds = {_HELD_NODE: _synthetic_valid_hold()}
    synthetic_sha256 = REG.flaky_test_hold_registry_sha256(synthetic_holds)
    monkeypatch.setattr(CONF, "FLAKY_TEST_HOLDS", synthetic_holds)
    monkeypatch.setattr(CONF, "FLAKY_TEST_HOLD_NODE_IDS", frozenset(synthetic_holds))
    monkeypatch.setattr(CONF, "FLAKY_TEST_HOLDS_SHA256", synthetic_sha256)
    lines.clear()

    CONF.pytest_sessionfinish(SimpleNamespace(config=config), 0)
    expected_nonempty_line = (
        "IZANAGI_FLAKY_HOLD_SUMMARY_V1 "
        + json.dumps(
            {
                "registered_node_count": 1,
                "matched_node_count": 1,
                "skipped_node_count": 1,
                "registry_sha256": synthetic_sha256,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )
    assert lines == [expected_nonempty_line]


def _run() -> int:
    """Run fixture and parametrized nodes without a plain-runner false green."""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
