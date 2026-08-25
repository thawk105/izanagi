"""Acceptance loadgroup duration ordering and its semantic isolation gates."""
from __future__ import annotations

import ast
import json
import math
import os
import site
import subprocess
import sys
import textwrap
from collections import Counter, OrderedDict
from pathlib import Path
from types import SimpleNamespace

import pytest
from xdist.scheduler.loadgroup import LoadGroupScheduling

from orchestrator.tests import conftest as CONF


pytest_plugins = ("pytester",)

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/run_tests.py"
LEDGER = ROOT / "orchestrator/tests/acceptance_duration_ledger.json"
_COVERAGE_PROBE_ENV = "IZANAGI_ACCEPTANCE_LEDGER_COVERAGE_PROBE"


def _independent_ledger_nodeid(item) -> str:
    """Build the expected key without calling the production consumer."""
    nodeid = str(item.nodeid)
    if nodeid.rfind("@") > nodeid.rfind("]"):
        nodeid = nodeid[:nodeid.rfind("@")]
    relative_path = Path(item.path).resolve(strict=False).relative_to(ROOT).as_posix()
    _original_path, separator, suffix = nodeid.partition("::")
    return relative_path if not separator else f"{relative_path}::{suffix}"


def pytest_collection_finish(session) -> None:
    """Emit real-item consumer and independent keys for the F16 probe only."""
    output = os.environ.get(_COVERAGE_PROBE_ENV)
    if output is None or hasattr(session.config, "workerinput"):
        return
    rows = [
        {
            "consumer": CONF._acceptance_ledger_nodeid(item),
            "expected": _independent_ledger_nodeid(item),
        }
        for item in session.items
    ]
    Path(output).write_text(
        json.dumps({"collection_count": len(session.items), "rows": rows}),
        encoding="utf-8",
    )


class _Item:
    def __init__(
        self,
        nodeid: str,
        *,
        markers=(),
        keywords=None,
        user_properties=(),
    ) -> None:
        self.nodeid = nodeid
        self.path = ROOT / nodeid.split("::", 1)[0]
        self._markers = list(markers)
        self.keywords = dict(keywords or {})
        self.user_properties = list(user_properties)

    def add_marker(self, marker, append=True) -> None:
        if isinstance(marker, str):
            marker = getattr(pytest.mark, marker)
        mark = getattr(marker, "mark", None)
        if mark is None:
            raise ValueError("is not a string or pytest.mark.* Marker")
        self.keywords[mark.name] = marker
        if append:
            self._markers.append(mark)
        else:
            self._markers.insert(0, mark)

    def iter_markers(self, name=None):
        return (
            mark for mark in self._markers
            if name is None or mark.name == name
        )


def _item(nodeid: str, **kwargs) -> _Item:
    return _Item(nodeid, **kwargs)


def _durations(items, values) -> dict[str, float]:
    return {
        CONF._acceptance_ledger_nodeid(item): float(value)
        for item, value in zip(items, values)
    }


def _ledger_bytes(durations: dict[str, object], **extra) -> bytes:
    document = {
        "schema_version": 1,
        "unit": "seconds",
        "nodeid_count": len(durations),
        "duration_seconds_by_nodeid": durations,
        **extra,
    }
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


_RECURSIVE_JSON = b"[" * 2_000 + b"0" + b"]" * 2_000
_HUGE_INTEGER_JSON = (
    b'{"schema_version":1,"unit":"seconds","nodeid_count":1,'
    b'"duration_seconds_by_nodeid":{"node":'
    + b"1" * 5_000
    + b"}}"
)


_LIVE_CONFTEST = r"""
import json
from pathlib import Path

import pytest
from orchestrator.tests import conftest as production

_HERE = Path(__file__).resolve().parent
production._ACCEPTANCE_DURATION_LEDGER_REPO_ROOT = _HERE
production._ACCEPTANCE_DURATION_LEDGER_PATH = _HERE / "acceptance_duration_ledger.json"

pytest_collection_modifyitems = production.pytest_collection_modifyitems
pytest_configure_node = production.pytest_configure_node
pytest_unconfigure = production.pytest_unconfigure


class _Recorder:
    def __init__(self, config):
        self.config = config
        self.outcomes = {}

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        if (
            not hasattr(session.config, "workerinput")
            and not session.config.getoption("collectonly", False)
        ):
            return
        entries = []
        for item in session.items:
            entries.append({
                "nodeid": item.nodeid,
                "markers": [
                    {"name": mark.name, "args": list(mark.args), "kwargs": mark.kwargs}
                    for mark in item.iter_markers()
                ],
                "keywords": sorted(str(key) for key in item.keywords),
                "user_properties": list(item.user_properties),
            })
        (_HERE / "collection.json").write_text(json.dumps({
            "dist": session.config.option.dist,
            "loadgroup": session.config.getoption("loadgroup", None),
            "entries": entries,
        }, sort_keys=True), encoding="utf-8")

    def pytest_runtest_logreport(self, report):
        if hasattr(self.config, "workerinput"):
            return
        if report.skipped:
            outcome = "xfail" if hasattr(report, "wasxfail") else "skipped"
        elif report.failed:
            outcome = "failed"
        elif report.when == "call":
            outcome = "passed"
        else:
            return
        reason = None
        if report.skipped and isinstance(report.longrepr, tuple):
            reason = str(report.longrepr[2])
        self.outcomes[report.nodeid] = {
            "outcome": outcome,
            "skip_reason": reason,
            "user_properties": list(report.user_properties),
        }

    def pytest_sessionfinish(self, session):
        if hasattr(session.config, "workerinput"):
            return
        (_HERE / "outcomes.json").write_text(
            json.dumps(self.outcomes, sort_keys=True), encoding="utf-8"
        )


class _AfterSnapshotLedgerSwap:
    @pytest.hookimpl(trylast=True)
    def pytest_configure_node(self, node):
        replacement = _HERE / "after_snapshot_ledger.json"
        if replacement.exists():
            (_HERE / "acceptance_duration_ledger.json").write_bytes(
                replacement.read_bytes()
            )


def pytest_configure(config):
    production.pytest_configure(config)
    if (_HERE / "replace_guard.trigger").exists():
        original_replace = production._replace_acceptance_items

        def tracked_replace(items, reordered):
            (_HERE / "replace_guard.called").write_text("called", encoding="ascii")
            return original_replace(items, reordered)

        production._replace_acceptance_items = tracked_replace
    config.pluginmanager.register(_Recorder(config), "acceptance-order-recorder")
    config.pluginmanager.register(
        _AfterSnapshotLedgerSwap(), "acceptance-after-snapshot-ledger-swap"
    )
"""


_THREE_PASS_TESTS = """
def test_fast():
    pass

def test_slow():
    pass

def test_unknown():
    pass
"""


def _install_live_suite(pytester, source: str = _THREE_PASS_TESTS) -> None:
    pytester.makeconftest(_LIVE_CONFTEST)
    pytester.makepyfile(test_sample=source)


def _run_live(
    pytester,
    ledger: bytes | None,
    *options: str,
    after_snapshot_ledger: bytes | None = None,
    track_replace_guard: bool = False,
):
    ledger_path = pytester.path / "acceptance_duration_ledger.json"
    if ledger is None:
        ledger_path.unlink(missing_ok=True)
    else:
        ledger_path.write_bytes(ledger)
    after_snapshot_path = pytester.path / "after_snapshot_ledger.json"
    if after_snapshot_ledger is None:
        after_snapshot_path.unlink(missing_ok=True)
    else:
        after_snapshot_path.write_bytes(after_snapshot_ledger)
    guard_trigger = pytester.path / "replace_guard.trigger"
    if track_replace_guard:
        guard_trigger.write_text("enabled", encoding="ascii")
    else:
        guard_trigger.unlink(missing_ok=True)
    for output in ("collection.json", "outcomes.json", "replace_guard.called"):
        (pytester.path / output).unlink(missing_ok=True)
    with pytest.MonkeyPatch.context() as environment:
        user_site = Path(site.getusersitepackages())
        pythonpath_entries = []
        if user_site.exists():
            pythonpath_entries.append(str(user_site))
        pythonpath_entries.append(str(ROOT))
        current = os.environ.get("PYTHONPATH")
        if current:
            pythonpath_entries.append(current)
        environment.setenv("PYTHONPATH", os.pathsep.join(pythonpath_entries))
        result = pytester.runpytest_subprocess(
            "-n", "1", "--dist", "loadgroup", "-q", *options,
        )
    collection_path = pytester.path / "collection.json"
    collection = (
        json.loads(collection_path.read_text(encoding="utf-8"))
        if collection_path.exists() else None
    )
    outcome_path = pytester.path / "outcomes.json"
    outcomes = (
        json.loads(outcome_path.read_text(encoding="utf-8"))
        if outcome_path.exists() else None
    )
    return result, collection, outcomes


def _ordered_names(collection) -> list[str]:
    return [
        entry["nodeid"].split("::", 1)[1].split("@", 1)[0]
        for entry in collection["entries"]
    ]


# G1: live hook-chain identity and fail-soft cases.  The valid cases must move
# an item, so a permanently disconnected or no-op production hook cannot pass.
@pytest.mark.parametrize(
    ("case", "ledger_factory", "expected"),
    (
        (
            "valid",
            lambda: _ledger_bytes({
                "test_sample.py::test_fast": 1,
                "test_sample.py::test_slow": 10,
                "test_sample.py::test_unknown": 2,
            }),
            ["test_slow", "test_unknown", "test_fast"],
        ),
        ("missing", lambda: None, ["test_fast", "test_slow", "test_unknown"]),
        ("broken-json", lambda: b"{", ["test_fast", "test_slow", "test_unknown"]),
        (
            "oversize",
            lambda: b" " * (CONF._ACCEPTANCE_DURATION_LEDGER_MAX_BYTES + 1),
            ["test_fast", "test_slow", "test_unknown"],
        ),
        (
            "unknown-mixed",
            lambda: _ledger_bytes({
                "test_sample.py::test_fast": 1,
                "test_sample.py::test_slow": 10,
            }),
            ["test_slow", "test_fast", "test_unknown"],
        ),
        (
            "extra-key",
            lambda: _ledger_bytes({
                "test_sample.py::test_fast": 1,
                "test_sample.py::test_slow": 10,
                "test_sample.py::test_unknown": 2,
            }, future_metadata={"ignored": True}),
            ["test_slow", "test_unknown", "test_fast"],
        ),
    ),
)
def test_g1_live_hook_chain_preserves_collection_identity(
    pytester, case, ledger_factory, expected,
):
    _install_live_suite(pytester)
    result, collection, _outcomes = _run_live(pytester, ledger_factory())
    result.assert_outcomes(passed=3)
    assert collection is not None, case
    actual = _ordered_names(collection)
    assert Counter(actual) == Counter(
        ("test_fast", "test_slow", "test_unknown")
    )
    assert actual == expected
    if case in {"valid", "extra-key", "unknown-mixed"}:
        assert actual != ["test_fast", "test_slow", "test_unknown"]


def test_g1_loader_filters_only_invalid_entries(tmp_path: Path):
    path = tmp_path / "ledger.json"
    path.write_bytes(_ledger_bytes({
        "good-int": 2,
        "good-zero": -0.0,
        "bool": True,
        "negative": -1,
        "nan": math.nan,
        "infinity": math.inf,
        "overflow": 10 ** 400,
        "string": "1.0",
    }))
    assert CONF._load_acceptance_duration_ledger(path) == {
        "good-int": 2.0,
        "good-zero": -0.0,
    }


@pytest.mark.parametrize(
    "payload",
    (
        b"\xff",
        b"[]",
        _RECURSIVE_JSON,
        _HUGE_INTEGER_JSON,
        b'{"schema_version":true,"unit":"seconds","nodeid_count":0,"duration_seconds_by_nodeid":{}}',
        b'{"schema_version":2,"unit":"seconds","nodeid_count":0,"duration_seconds_by_nodeid":{}}',
        b'{"schema_version":1,"unit":"milliseconds","nodeid_count":0,"duration_seconds_by_nodeid":{}}',
        b'{"schema_version":1,"unit":"seconds","nodeid_count":0,"duration_seconds_by_nodeid":[]}',
    ),
)
def test_g1_loader_schema_unicode_and_top_level_fail_soft(tmp_path: Path, payload):
    path = tmp_path / "ledger.json"
    path.write_bytes(payload)
    assert CONF._load_acceptance_duration_ledger(path) == {}


def test_g1_loader_catches_only_file_io_oserror(monkeypatch, tmp_path: Path):
    missing = tmp_path / "missing.json"
    assert CONF._load_acceptance_duration_ledger(missing) == {}
    valid = tmp_path / "valid.json"
    valid.write_bytes(_ledger_bytes({"node": 1}))

    def programming_error(_document):
        raise OSError("validator bug")

    monkeypatch.setattr(
        CONF, "_validate_acceptance_duration_ledger_document", programming_error,
    )
    with pytest.raises(OSError, match="validator bug"):
        CONF._load_acceptance_duration_ledger(valid)


@pytest.mark.parametrize("exception", (KeyboardInterrupt(), SystemExit(), MemoryError()))
def test_g1_loader_does_not_hide_process_or_memory_exceptions(exception):
    class _ExplodingPath:
        def open(self, _mode):
            raise exception

    with pytest.raises(type(exception)):
        CONF._load_acceptance_duration_ledger(_ExplodingPath())


def test_g1_repo_external_item_is_unknown_without_changing_collection():
    fast = _item("orchestrator/tests/test_fast.py::test_fast")
    external = _item("external.py::test_external")
    external.path = Path("/tmp/izanagi-acceptance-external.py")
    slow = _item("orchestrator/tests/test_slow.py::test_slow")
    items = [fast, external, slow]
    before = Counter(map(id, items))
    ledger = {
        "orchestrator/tests/test_fast.py::test_fast": 1.0,
        "orchestrator/tests/test_slow.py::test_slow": 10.0,
    }

    assert CONF._acceptance_ledger_nodeid(external) is None
    assert CONF._reorder_acceptance_items_by_duration(items, ledger)
    assert items == [slow, fast, external]
    assert Counter(map(id, items)) == before


@pytest.mark.parametrize(
    "exception",
    (ValueError("path"), OSError("path"), RuntimeError("path"), TypeError("path")),
)
def test_g1_ledger_nodeid_path_failures_are_unknown(exception):
    class _ExplodingPath:
        def __fspath__(self):
            raise exception

    item = _item("orchestrator/tests/test_path.py::test_path")
    item.path = _ExplodingPath()
    assert CONF._acceptance_ledger_nodeid(item) is None


# G2: unequal costs intentionally oppose lexical order; equal costs retain the
# original index even when ledger insertion order is reversed.
def test_g2_cost_order_tie_break_and_payload_order_are_deterministic():
    original = [
        _item("orchestrator/tests/test_a.py::test_fast"),
        _item("orchestrator/tests/test_z.py::test_slow"),
        _item("orchestrator/tests/test_y.py::test_tie_first"),
        _item("orchestrator/tests/test_b.py::test_tie_second"),
    ]
    values = _durations(original, (1, 20, 5, 5))
    reversed_payload = dict(reversed(tuple(values.items())))
    observed = []
    for payload in (values, reversed_payload, values, reversed_payload):
        items = list(original)
        assert CONF._reorder_acceptance_items_by_duration(items, payload)
        observed.append([item.nodeid for item in items])
    assert observed[0] == observed[1] == observed[2] == observed[3]
    assert observed[0] == [
        original[1].nodeid,
        original[2].nodeid,
        original[3].nodeid,
        original[0].nodeid,
    ]
    assert observed[0] != sorted(item.nodeid for item in original)


def test_g2_overflowed_unit_sum_is_unknown_not_infinite_priority():
    known = _item("orchestrator/tests/test_known.py::test_known")
    first = _item("orchestrator/tests/test_group.py::test_first@overflow")
    second = _item("orchestrator/tests/test_group.py::test_second@overflow")
    items = [known, first, second]
    ledger = _durations(items, (5, 1e308, 1e308))
    assert CONF._reorder_acceptance_items_by_duration(items, ledger)
    assert items == [known, first, second]


# G3: differential oracle is the installed xdist scheduler itself.
@pytest.mark.parametrize(
    "nodeid",
    (
        "orchestrator/tests/test_plain.py::test_plain",
        "orchestrator/tests/test_group.py::test_case@group",
        "orchestrator/tests/test_group.py::test_case@first@second",
        "orchestrator/tests/test_group.py::test_case[param@value]@group",
        "orchestrator/tests/test_group.py::test_case[param@one@two]",
        "orchestrator/tests/test_check_acceptance_reds.py::test_collection_preserves_literal_nodeid_suffixes[orchestrator/tests/test_example.py::test_target@literal]",
        "orchestrator/tests/test_coder_effect_gate.py::test_malformed_tokens_and_strings_fail_closed_without_byte_reflection[int value = 0; @ SENTINEL_UNEXPECTED_TOKEN]",
        "",
        "@",
        "試験::場合[値@例]",
        "試験::場合@直列",
    ),
)
def test_g3_splitter_exactly_matches_loadgroup_scheduler(nodeid: str):
    expected = LoadGroupScheduling._split_scope(None, nodeid)
    assert CONF._acceptance_loadgroup_scope(nodeid) == expected


def _semantic_snapshot(items):
    return {
        id(item): {
            "markers": tuple(
                (mark.name, tuple(mark.args), dict(mark.kwargs))
                for mark in item.iter_markers()
            ),
            "keywords": dict(item.keywords),
            "user_properties": tuple(item.user_properties),
        }
        for item in items
    }


# G4: selection and acceptance-bearing item state is compared in full, while
# the runner is independently pinned away from the ledger by AST.
def test_g4_reorder_preserves_deselection_markers_keywords_properties_and_identity():
    marks = (
        SimpleNamespace(name="skip", args=(), kwargs={"reason": "kept reason"}),
        SimpleNamespace(name="xfail", args=("predicate",), kwargs={"strict": True}),
        SimpleNamespace(name="custom", args=(1, "two"), kwargs={"flag": False}),
    )
    selected = [
        _item(
            "orchestrator/tests/test_a.py::test_a",
            markers=marks,
            keywords={"test_a": True, "custom": marks[-1]},
            user_properties=(("receipt", "a"),),
        ),
        _item(
            "orchestrator/tests/test_b.py::test_b",
            markers=tuple(reversed(marks)),
            keywords={"test_b": True, "xfail": marks[1]},
            user_properties=(("receipt", "b"), ("count", 2)),
        ),
    ]
    deselected = [_item("orchestrator/tests/test_c.py::test_deselected")]
    before_selected = _semantic_snapshot(selected)
    before_deselected = tuple(deselected)
    before_identity = Counter(map(id, selected))
    assert CONF._reorder_acceptance_items_by_duration(
        selected, _durations(selected, (1, 10)),
    )
    assert _semantic_snapshot(selected) == before_selected
    assert Counter(map(id, selected)) == before_identity
    assert tuple(deselected) == before_deselected


def test_g4_runner_ast_has_no_ledger_import_or_reference():
    """Record the isolation intent; this AST check is not a security barrier."""
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"), filename=str(RUNNER))
    observed = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            observed.append(node.id)
        elif isinstance(node, ast.Attribute):
            observed.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            observed.append(node.value)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            observed.extend(alias.name for alias in node.names)
    forbidden = [
        value for value in observed
        if "acceptance_duration_ledger" in value
        or "acceptance_schedule_order" in value
    ]
    assert forbidden == []


_OUTCOME_TESTS = """
import pytest

@pytest.fixture(scope="module")
def order_independent_module_state(request):
    seen = set()

    def finalize():
        assert seen == {"pass", "fail", "xfail"}

    request.addfinalizer(finalize)
    return seen

@pytest.mark.parametrize("value", [1], ids=["one"])
def test_pass(value, record_property, order_independent_module_state):
    order_independent_module_state.add("pass")
    record_property("receipt", "pass")
    assert value == 1

def test_fail(record_property, order_independent_module_state):
    order_independent_module_state.add("fail")
    record_property("receipt", "fail")
    assert False, "stable failure"

@pytest.mark.skip(reason="stable skip reason")
def test_skip():
    pass

@pytest.mark.xfail(reason="stable xfail reason", strict=True)
def test_xfail(record_property, order_independent_module_state):
    order_independent_module_state.add("xfail")
    record_property("receipt", "xfail")
    assert False
"""


# G5: for this deliberately order-independent suite, two genuinely different
# valid ledgers produce different order but the same outcomes and metadata.
# The module-scoped fixture and its finalizer use a set, never execution order.
def test_g5_two_ledgers_preserve_outcomes_skip_markers_and_properties(pytester):
    _install_live_suite(pytester, _OUTCOME_TESTS)
    nodeids = (
        "test_sample.py::test_pass[one]",
        "test_sample.py::test_fail",
        "test_sample.py::test_skip",
        "test_sample.py::test_xfail",
    )
    first = _ledger_bytes(dict(zip(nodeids, (40, 30, 20, 10))))
    second = _ledger_bytes(dict(zip(nodeids, (10, 20, 30, 40))))

    result_a, collection_a, outcomes_a = _run_live(pytester, first)
    result_a.assert_outcomes(passed=1, failed=1, skipped=1, xfailed=1)
    result_b, collection_b, outcomes_b = _run_live(pytester, second)
    result_b.assert_outcomes(passed=1, failed=1, skipped=1, xfailed=1)

    assert _ordered_names(collection_a) != _ordered_names(collection_b)
    metadata_a = {
        entry["nodeid"]: {
            "markers": entry["markers"],
            "keywords": entry["keywords"],
            "user_properties": entry["user_properties"],
        }
        for entry in collection_a["entries"]
    }
    metadata_b = {
        entry["nodeid"]: {
            "markers": entry["markers"],
            "keywords": entry["keywords"],
            "user_properties": entry["user_properties"],
        }
        for entry in collection_b["entries"]
    }
    assert metadata_a == metadata_b
    assert outcomes_a == outcomes_b
    assert any(
        entry["outcome"] == "skipped"
        and entry["skip_reason"] == "Skipped: stable skip reason"
        for entry in outcomes_a.values()
    )
    assert {entry["outcome"] for entry in outcomes_a.values()} == {
        "passed", "failed", "skipped", "xfail",
    }


def test_g5_real_ledger_covers_at_least_90_percent_of_real_collection(
    tmp_path: Path,
):
    """Join real consumer keys to producer output without self-derived expectations."""
    probe_path = tmp_path / "acceptance-ledger-coverage.json"
    environment = {**os.environ, _COVERAGE_PROBE_ENV: str(probe_path)}
    user_site = Path(site.getusersitepackages())
    if user_site.exists():
        current = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            str(user_site) if not current
            else str(user_site) + os.pathsep + current
        )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "orchestrator.tests.test_acceptance_schedule_order",
            "--collect-only",
            "-q",
            "orchestrator/tests",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-4000:]
    assert probe_path.exists(), "real collection coverage probe did not run"

    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    rows = probe["rows"]
    assert probe["collection_count"] == len(rows)
    assert rows
    expected_keys = [row["expected"] for row in rows]
    consumer_keys = [row["consumer"] for row in rows]
    assert len(set(expected_keys)) == len(expected_keys)

    ledger_document = json.loads(LEDGER.read_text(encoding="utf-8"))
    ledger_keys = set(ledger_document["duration_seconds_by_nodeid"])
    covered = sum(key in ledger_keys for key in consumer_keys)
    coverage = covered / len(rows)
    print(
        "acceptance duration ledger coverage: "
        f"{covered}/{len(rows)} = {coverage:.6%}"
    )
    assert coverage >= 0.90, (
        f"acceptance duration ledger coverage too low: {coverage:.6%}"
    )
    assert consumer_keys == expected_keys, (
        "acceptance duration ledger consumer key round-trip mismatch"
    )


# G6: reuse the independent literal and live collection audit, then compare the
# complete real-repo projection across a production reorder.
def test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order():
    from orchestrator.tests import test_real_repo_serialization as real_gate

    report = real_gate._collect_xdist_group_report(real_gate.HERE, cwd=real_gate.ROOT)
    real_gate._assert_xdist_group_contract(
        report, real_gate._XDIST_GROUP_NAMES_GOLDEN,
    )
    real_gate._assert_real_repo_collection_order(report)
    assert set(CONF.REAL_REPO_SERIAL_NODES) == set(
        real_gate._REAL_REPO_SERIAL_NODES_GOLDEN
    )

    items = []
    canonical_by_identity = {}
    for entry in report:
        nodeid = entry["nodeid"]
        if entry["marks"]:
            nodeid = f"{nodeid}@{entry['marks'][0]['args'][0]}"
        item = _item(nodeid)
        items.append(item)
        canonical_by_identity[id(item)] = entry["canonical_node"]
    before = [
        canonical_by_identity[id(item)] for item in items
        if CONF._acceptance_loadgroup_scope(item.nodeid) == "real-repo"
    ]
    assert len(before) >= 4
    ledger = _durations(items, (1 for _item_value in items))
    assert CONF._reorder_acceptance_items_by_duration(items, ledger)
    positions = [
        index for index, item in enumerate(items)
        if CONF._acceptance_loadgroup_scope(item.nodeid) == "real-repo"
    ]
    after = [canonical_by_identity[id(items[index])] for index in positions]
    assert after == before
    assert positions == list(range(positions[0], positions[0] + len(positions)))


class _OptionConfig:
    def __init__(self, **overrides):
        defaults = {
            "dist": "no",
            "maxfail": 0,
            "stepwise": False,
            "stepwise_skip": False,
            "stepwise_reset": False,
            "failedfirst": False,
            "newfirst": False,
            "lf": False,
            "collectonly": False,
            "setuponly": False,
            "setupplan": False,
            "showfixtures": False,
            "show_fixtures_per_test": False,
            "cacheshow": None,
            "loadscopereorder": True,
            "trace": False,
        }
        defaults.update(overrides)
        self.option = SimpleNamespace(**defaults)

    def getvalue(self, name):
        if name != "loadgroup":
            raise ValueError(name)
        return True


def test_g7_reordering_enablement_fails_closed_but_has_positive_control():
    assert CONF._acceptance_reordering_enabled(_OptionConfig()) is True
    assert CONF._acceptance_reordering_enabled(SimpleNamespace()) is False
    assert CONF._acceptance_reordering_enabled(
        SimpleNamespace(getvalue=lambda _name: True)
    ) is False

    for exception in (
        AttributeError("getvalue"),
        ValueError("getvalue"),
        TypeError("getvalue"),
    ):
        def broken_getvalue(_name, failure=exception):
            raise failure

        config = SimpleNamespace(
            option=_OptionConfig().option,
            getvalue=broken_getvalue,
        )
        assert CONF._acceptance_reordering_enabled(config) is False


# G7: every parsed semantic axis has a negative signature.  The live positive
# below additionally proves worker-side dist="no" does not disable the hook.
@pytest.mark.parametrize(
    "option",
    (
        {"maxfail": 1},
        {"stepwise": True},
        {"stepwise_skip": True},
        {"stepwise_reset": True},
        {"failedfirst": True},
        {"newfirst": True},
        {"lf": True},
        {"collectonly": True},
        {"setuponly": True},
        {"setupplan": True},
        {"showfixtures": True},
        {"show_fixtures_per_test": True},
        {"cacheshow": [None]},
        {"loadscopereorder": False},
        {"trace": True},
    ),
)
def test_g7_early_order_and_nonexecution_options_disable_reorder(option):
    assert CONF._acceptance_reordering_enabled(_OptionConfig(**option)) is False


@pytest.mark.parametrize(
    "option",
    ("-x", "--ff", "--collect-only", "--no-loadscope-reorder", "--trace"),
)
def test_g7_live_negative_categories_keep_original_order(pytester, option):
    _install_live_suite(pytester)
    ledger = _ledger_bytes({
        "test_sample.py::test_fast": 1,
        "test_sample.py::test_slow": 10,
        "test_sample.py::test_unknown": 2,
    })
    _result, collection, _outcomes = _run_live(pytester, ledger, option)
    assert collection is not None
    assert _ordered_names(collection) == [
        "test_fast", "test_slow", "test_unknown",
    ]


def test_g7_live_worker_dist_no_still_reorders_with_loadgroup(pytester):
    _install_live_suite(pytester)
    ledger = _ledger_bytes({
        "test_sample.py::test_fast": 1,
        "test_sample.py::test_slow": 10,
        "test_sample.py::test_unknown": 2,
    })
    result, collection, _outcomes = _run_live(pytester, ledger)
    result.assert_outcomes(passed=3)
    assert collection["dist"] == "no"
    assert collection["loadgroup"] is True
    assert _ordered_names(collection)[0] == "test_slow"


def test_g7_live_hook_uses_loadgroup_splitter(pytester):
    source = """
import pytest

def test_solo():
    pass

@pytest.mark.xdist_group("paired")
def test_group_first():
    pass

@pytest.mark.xdist_group("paired")
def test_group_second():
    pass
"""
    _install_live_suite(pytester, source)
    ledger = _ledger_bytes({
        "test_sample.py::test_solo": 10,
        "test_sample.py::test_group_first": 6,
        "test_sample.py::test_group_second": 6,
    })
    result, collection, _outcomes = _run_live(pytester, ledger)
    result.assert_outcomes(passed=3)
    assert _ordered_names(collection) == [
        "test_group_first", "test_group_second", "test_solo",
    ]


def test_g7_live_worker_uses_controller_snapshot_not_mutated_file(pytester):
    _install_live_suite(pytester)
    controller_ledger = _ledger_bytes({
        "test_sample.py::test_fast": 1,
        "test_sample.py::test_slow": 10,
        "test_sample.py::test_unknown": 2,
    })
    replacement_ledger = _ledger_bytes({
        "test_sample.py::test_fast": 20,
        "test_sample.py::test_slow": 1,
        "test_sample.py::test_unknown": 2,
    })
    result, collection, _outcomes = _run_live(
        pytester,
        controller_ledger,
        after_snapshot_ledger=replacement_ledger,
    )
    result.assert_outcomes(passed=3)
    assert (pytester.path / "acceptance_duration_ledger.json").read_bytes() == (
        replacement_ledger
    )
    assert _ordered_names(collection) == [
        "test_slow", "test_unknown", "test_fast",
    ]


def test_g7_live_hook_calls_identity_guard(pytester):
    _install_live_suite(pytester)
    ledger = _ledger_bytes({
        "test_sample.py::test_fast": 1,
        "test_sample.py::test_slow": 10,
        "test_sample.py::test_unknown": 2,
    })
    result, collection, _outcomes = _run_live(
        pytester, ledger, track_replace_guard=True,
    )
    result.assert_outcomes(passed=3)
    assert _ordered_names(collection)[0] == "test_slow"
    assert (pytester.path / "replace_guard.called").read_text(
        encoding="ascii"
    ) == "called"


def test_g7_controller_reads_ledger_only_for_enabled_loadgroup(
    monkeypatch, tmp_path: Path,
):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_bytes(_ledger_bytes({"loaded": 3.0}))
    calls = []
    original_open = Path.open

    def tracked_open(path, *args, **kwargs):
        if path == ledger_path:
            calls.append(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(CONF, "_ACCEPTANCE_DURATION_LEDGER_PATH", ledger_path)
    monkeypatch.setattr(Path, "open", tracked_open)
    disabled = (
        _OptionConfig(dist="no"),
        _OptionConfig(dist="load"),
        _OptionConfig(dist="loadgroup", maxfail=1),
        _OptionConfig(dist="loadgroup", loadscopereorder=False),
        _OptionConfig(dist="loadgroup", trace=True),
    )
    for config in disabled:
        CONF._configure_acceptance_duration_ledger(config)
        assert getattr(
            config, CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR
        ) == {}
    assert calls == []

    enabled = _OptionConfig(dist="loadgroup")

    def forbidden_getvalue(_name):
        raise AssertionError("controller consulted worker-only loadgroup state")

    enabled.getvalue = forbidden_getvalue
    CONF._configure_acceptance_duration_ledger(enabled)
    assert getattr(
        enabled, CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR
    ) == {"loaded": 3.0}
    assert calls == [ledger_path]


def test_g2a_configure_node_only_sends_snapshot_controller_actually_read():
    for snapshot in (None, []):
        config = _OptionConfig(dist="loadgroup")
        setattr(config, CONF._RECEIPT_MEMO_SESSION_ID_ATTR, "controller-session")
        setattr(
            config,
            CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR,
            snapshot,
        )
        node = SimpleNamespace(config=config, workerinput={"testrunuid": "run"})
        CONF.pytest_configure_node(node)
        assert node.workerinput == {
            "testrunuid": "run",
            CONF._RECEIPT_MEMO_SESSION_ID_ATTR: "controller-session",
        }

    config = _OptionConfig(dist="loadgroup")
    setattr(config, CONF._RECEIPT_MEMO_SESSION_ID_ATTR, "controller-session")
    node = SimpleNamespace(config=config, workerinput={"testrunuid": "run"})
    CONF.pytest_configure_node(node)
    assert node.workerinput == {
        "testrunuid": "run",
        CONF._RECEIPT_MEMO_SESSION_ID_ATTR: "controller-session",
    }

    setattr(
        config,
        CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR,
        {"node": 2.0},
    )
    node = SimpleNamespace(config=config, workerinput={"testrunuid": "run"})
    CONF.pytest_configure_node(node)
    assert node.workerinput == {
        "testrunuid": "run",
        CONF._RECEIPT_MEMO_SESSION_ID_ATTR: "controller-session",
        CONF._ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY: {
            "schema_version": 1,
            "duration_seconds_by_nodeid": {"node": 2.0},
        },
    }


# These direct helper checks are supplementary; the live gates above are the
# authority for splitter, snapshot-only worker input, and identity-guard wiring.
def test_g2b_workerinput_absence_is_empty_but_type_damage_is_rejected():
    key = CONF._ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY
    missing = SimpleNamespace(workerinput={})
    CONF._configure_acceptance_duration_ledger(missing)
    assert getattr(missing, CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR) == {}
    with pytest.raises(pytest.UsageError, match="payload 型が不正"):
        CONF._configure_acceptance_duration_ledger(
            SimpleNamespace(workerinput={key: []})
        )


def test_g2c_enabled_worker_rejects_missing_snapshot_but_disabled_accepts_it():
    enabled = _OptionConfig()
    enabled.workerinput = {}
    with pytest.raises(pytest.UsageError, match="snapshot が無い"):
        CONF._configure_acceptance_duration_ledger(enabled)

    disabled = _OptionConfig(maxfail=1)
    disabled.workerinput = {}
    CONF._configure_acceptance_duration_ledger(disabled)
    assert getattr(disabled, CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR) == {}


def test_g7_worker_consumes_snapshot_without_reading_file(monkeypatch):
    def forbidden_read(*_args, **_kwargs):
        raise AssertionError("worker reread the ledger")

    monkeypatch.setattr(CONF, "_load_acceptance_duration_ledger", forbidden_read)
    key = CONF._ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY
    config = SimpleNamespace(workerinput={key: {
        "schema_version": 1,
        "duration_seconds_by_nodeid": {"node": 2.0},
    }})
    CONF._configure_acceptance_duration_ledger(config)
    assert getattr(config, CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR) == {
        "node": 2.0,
    }


# G8: the unknown unit lands immediately after the known unit tied at the 96th
# cost.  Infinity would put it first and zero would put it last.
def test_g8_unknown_cost_is_known_96th_and_zero_known_is_full_noop(monkeypatch):
    known = [
        _item(f"orchestrator/tests/test_{index:03d}.py::test_case")
        for index in range(100)
    ]
    unknown = _item("orchestrator/tests/test_unknown.py::test_case")
    items = [*known, unknown]
    ledger = _durations(known, range(200, 100, -1))
    assert CONF._reorder_acceptance_items_by_duration(items, ledger)
    assert items.index(unknown) == 96
    assert items[95] is known[95]

    class _TrackingList(list):
        replacements = 0

        def __setitem__(self, key, value):
            if isinstance(key, slice):
                self.replacements += 1
            return super().__setitem__(key, value)

    no_known = _TrackingList([unknown, known[0]])
    before = tuple(no_known)

    def forbidden_key_calculation(_item_value):
        raise AssertionError("empty ledger calculated an item key")

    monkeypatch.setattr(
        CONF, "_acceptance_ledger_nodeid", forbidden_key_calculation,
    )
    assert not CONF._reorder_acceptance_items_by_duration(no_known, {})
    assert tuple(no_known) == before
    assert no_known.replacements == 0


# G9: dynamic optimized-mode rejection and AST both pin the explicit check.
def test_g9_identity_guard_survives_python_optimized_mode():
    code = textwrap.dedent(
        """
        from orchestrator.tests import conftest as target
        first, second = object(), object()
        try:
            target._replace_acceptance_items([first, second], [first])
        except target.pytest.UsageError as exc:
            print(str(exc))
        else:
            raise SystemExit(17)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-O", "-B", "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert completed.returncode == 0, completed.stderr
    assert "item identity multiset" in completed.stdout

    source = ast.parse(Path(CONF.__file__).read_text(encoding="utf-8"))
    function = next(
        node for node in source.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_replace_acceptance_items"
    )
    assert not any(isinstance(node, ast.Assert) for node in ast.walk(function))

    class _SabotagedList(list):
        def __setitem__(self, key, value):
            if isinstance(key, slice):
                value = value[:-1]
            return super().__setitem__(key, value)

    first, second = object(), object()
    with pytest.raises(pytest.UsageError, match="reorder 後"):
        CONF._replace_acceptance_items(
            _SabotagedList([first, second]), [second, first],
        )


# G10/G11: T-1563 compares only the complete collection order and the global
# work-unit dequeue order.  Worker assignment, prefetch timing, and completion
# order are deliberately absent from these observations because they are
# mediators of worker count, not invariants.
_NPROC_ARMS = (16, 32, 48)
_NPROC_INITIAL_INDEX_ORDER = tuple(range(20, 40)) + tuple(range(20))
_NPROC_EXPECTED_NODEIDS = tuple(
    "orchestrator/tests/test_t1563_nproc_order.py::"
    f"test_case_{index:02d}@unit-{index:02d}"
    for index in range(40)
)
_NPROC_EXPECTED_SCOPES = tuple(
    f"unit-{index:02d}" for index in range(40)
)
_NPROC_DURATION_LEDGER = {
    "orchestrator/tests/test_t1563_nproc_order.py::"
    f"test_case_{index:02d}": float(40 - index)
    for index in range(39)
}
# Give units 10 and 11 the same cost.  Their canonical order is therefore the
# stable original-index tie-break, which both positive controls can perturb.
_NPROC_DURATION_LEDGER[
    "orchestrator/tests/test_t1563_nproc_order.py::test_case_11"
] = 30.0
# Unit 39 is deliberately unknown.  The production 96-unit window ties it with
# the lowest known unit (38), after which their stable input order puts 38 first.
# A numprocesses * 2 window mutation instead moves it after unit 31 at n=16.


def _nproc_initial_items() -> tuple[_Item, ...]:
    items = []
    for index in _NPROC_INITIAL_INDEX_ORDER:
        item = _item(
            "orchestrator/tests/test_t1563_nproc_order.py::"
            f"test_case_{index:02d}@unit-{index:02d}"
        )
        # The production wrapper's pre-yield hold handling consumes the pytest
        # item name.  These synthetic nodeids intentionally match no hold.
        item.name = f"test_case_{index:02d}"
        items.append(item)
    return tuple(items)


def _run_collection_wrapper_arm(
    numprocesses: int,
    initial_items: tuple[_Item, ...],
    duration_ledger: dict[str, float],
):
    items = list(initial_items)
    before_nodeids = tuple(item.nodeid for item in items)
    before_identities = Counter(id(item) for item in items)
    config = _OptionConfig(
        numprocesses=numprocesses,
        dist="loadgroup",
        loadscopereorder=True,
    )
    setattr(
        config,
        CONF._ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR,
        duration_ledger,
    )

    wrapper = CONF.pytest_collection_modifyitems(config, items)
    assert next(wrapper) is None
    with pytest.raises(StopIteration):
        next(wrapper)

    return {
        "before_nodeids": before_nodeids,
        "after_nodeids": tuple(item.nodeid for item in items),
        "after_items": tuple(items),
        "before_identities": before_identities,
        "after_identities": Counter(id(item) for item in items),
        "ledger_identity": id(duration_ledger),
        "loadgroup": config.getvalue("loadgroup"),
    }


def _assert_collection_wrapper_arm_contract(observation) -> None:
    before = observation["before_nodeids"]
    after = observation["after_nodeids"]
    assert len(before) >= 4
    assert all(before)
    assert len(set(before)) == len(before)
    assert observation["after_identities"] == observation["before_identities"]
    assert after == _NPROC_EXPECTED_NODEIDS
    assert after != before


def _assert_arm_tuples_equal(observations, key: str, label: str) -> None:
    canonical = observations[_NPROC_ARMS[0]][key]
    for numprocesses in _NPROC_ARMS[1:]:
        assert observations[numprocesses][key] == canonical, (
            f"{label} changed at numprocesses={numprocesses}"
        )


def test_g10_collection_wrapper_order_is_worker_count_independent():
    initial_items = _nproc_initial_items()
    duration_ledger = dict(_NPROC_DURATION_LEDGER)
    observations = {
        numprocesses: _run_collection_wrapper_arm(
            numprocesses, initial_items, duration_ledger,
        )
        for numprocesses in _NPROC_ARMS
    }

    for observation in observations.values():
        _assert_collection_wrapper_arm_contract(observation)
    assert all(
        observation["before_identities"]
        == observations[_NPROC_ARMS[0]]["before_identities"]
        for observation in observations.values()
    )
    assert {
        observation["ledger_identity"] for observation in observations.values()
    } == {id(duration_ledger)}
    assert {
        observation["loadgroup"] for observation in observations.values()
    } == {True}
    _assert_arm_tuples_equal(
        observations, "after_nodeids", "complete collection nodeid tuple",
    )


def test_g10_collection_wrapper_worker_dependent_tie_break_control_fails(
    monkeypatch,
):
    initial_items = _nproc_initial_items()
    duration_ledger = dict(_NPROC_DURATION_LEDGER)
    production_reorder = CONF._reorder_acceptance_items_by_duration
    active_numprocesses = {"value": None}

    # The wrapper has no callable-injection parameter: it directly resolves
    # this module helper post-yield.  Patch that production-resolved callable,
    # while keeping the item objects and ledger identical across all arms.
    def worker_dependent_tie_break(items, durations):
        changed = production_reorder(items, durations)
        if active_numprocesses["value"] == 32:
            first = next(
                index for index, item in enumerate(items)
                if item.nodeid.endswith("test_case_10@unit-10")
            )
            second = next(
                index for index, item in enumerate(items)
                if item.nodeid.endswith("test_case_11@unit-11")
            )
            items[first], items[second] = items[second], items[first]
        return changed

    monkeypatch.setattr(
        CONF,
        "_reorder_acceptance_items_by_duration",
        worker_dependent_tie_break,
    )
    observations = {}
    for numprocesses in _NPROC_ARMS:
        active_numprocesses["value"] = numprocesses
        observations[numprocesses] = _run_collection_wrapper_arm(
            numprocesses, initial_items, duration_ledger,
        )

    assert all(
        observation["before_identities"]
        == observations[_NPROC_ARMS[0]]["before_identities"]
        for observation in observations.values()
    )
    assert {
        observation["ledger_identity"] for observation in observations.values()
    } == {id(duration_ledger)}
    assert {
        observation["loadgroup"] for observation in observations.values()
    } == {True}
    with pytest.raises(
        AssertionError, match="complete collection nodeid tuple changed",
    ):
        _assert_arm_tuples_equal(
            observations, "after_nodeids", "complete collection nodeid tuple",
        )


class _SchedulerConfig:
    def __init__(self, numprocesses: int) -> None:
        self.option = SimpleNamespace(loadscopereorder=True)
        self._tx = tuple("popen" for _index in range(numprocesses))

    def getvalue(self, name: str):
        if name != "tx":
            raise ValueError(name)
        return self._tx


class _FakeSchedulerNode:
    def __init__(self, index: int) -> None:
        self.gateway = SimpleNamespace(id=f"gw{index}")
        self.shutting_down = False

    def send_runtest_some(self, _indexes) -> None:
        # Assignment is intentionally not recorded: it is outside the claim.
        pass

    def shutdown(self) -> None:
        self.shutting_down = True


class _TracingWorkQueue(OrderedDict):
    def __init__(self) -> None:
        super().__init__()
        self.dequeue_trace = []

    def popitem(self, last=True):
        scope, work_unit = super().popitem(last=last)
        self.dequeue_trace.append(scope)
        return scope, work_unit


def _nproc_scheduler_fixture():
    """Build non-degenerate loadgroup units and a real priority inversion."""
    synthetic_path = "orchestrator/tests/test_t1563_scheduler_order.py"

    def synthetic_items(scope: str, count: int) -> tuple[_Item, ...]:
        items = []
        for index in range(count):
            item = _item(
                f"{synthetic_path}::test_{scope}_{index:02d}@{scope}"
            )
            item.name = f"test_{scope}_{index:02d}"
            items.append(item)
        return tuple(items)

    medium = synthetic_items("medium", 17)
    large = synthetic_items("large", 33)
    pair_a = synthetic_items("pair-a", 2)
    pair_b = synthetic_items("pair-b", 2)
    singleton_a = synthetic_items("singleton-a", 1)
    singleton_b = synthetic_items("singleton-b", 1)

    serial_nodes = set(CONF.REAL_REPO_SERIAL_NODES)
    priority_nodes = tuple(
        node for node in CONF.REAL_REPO_EXECUTION_PRIORITY
        if node in serial_nodes
    )
    assert len(priority_nodes) >= 2
    real_marker = SimpleNamespace(
        name="xdist_group", args=("real-repo",), kwargs={},
    )
    real_priority = []
    for node in priority_nodes[:2]:
        item = _item(
            f"orchestrator/tests/{node}@real-repo",
            markers=(real_marker,),
        )
        item.name = node.split("::", 1)[1]
        real_priority.append(item)
    real_priority = tuple(real_priority)
    real_initial = tuple(reversed(real_priority))

    # The wrapper sees large first, but the duration ledger intentionally puts
    # medium first.  That insertion order makes min(unit_size, numprocesses)
    # distinguish the 16-worker arm from the 32/48-worker arms.
    initial_items = (
        *large,
        *singleton_b,
        *pair_b,
        *real_initial,
        *singleton_a,
        *medium,
        *pair_a,
    )
    duration_ledger = {}
    for items, duration in (
        (medium, 10.0),
        (large, 4.0),
        (pair_a, 50.5),
        (pair_b, 50.0),
        (real_priority, 40.0),
        (singleton_a, 30.0),
        (singleton_b, 30.0),
    ):
        for item in items:
            key = CONF._acceptance_ledger_nodeid(item)
            assert key is not None
            duration_ledger[key] = duration

    pre_finish_items = (
        *medium,
        *large,
        *pair_a,
        *pair_b,
        *real_initial,
        *singleton_b,
        *singleton_a,
    )
    final_items = (
        *medium,
        *large,
        *pair_a,
        *pair_b,
        *real_priority,
        *singleton_b,
        *singleton_a,
    )
    return {
        "initial_items": tuple(initial_items),
        "duration_ledger": duration_ledger,
        "pre_finish_nodeids": tuple(item.nodeid for item in pre_finish_items),
        "final_nodeids": tuple(item.nodeid for item in final_items),
        "dequeue_scopes": (
            "large",
            "medium",
            "pair-a",
            "pair-b",
            "real-repo",
            "singleton-b",
            "singleton-a",
        ),
    }


def _assert_nproc_scheduler_fixture_contract(fixture) -> None:
    scope_counts = Counter(
        CONF._acceptance_loadgroup_scope(nodeid)
        for nodeid in fixture["final_nodeids"]
    )
    assert scope_counts["singleton-a"] == 1
    assert scope_counts["singleton-b"] == 1
    assert scope_counts["pair-a"] == scope_counts["pair-b"] == 2
    assert scope_counts["medium"] == 17
    assert scope_counts["large"] == 33
    assert fixture["pre_finish_nodeids"] != fixture["final_nodeids"]


def _run_scheduler_arm(
    numprocesses: int,
    initial_items: tuple[_Item, ...],
    duration_ledger: dict[str, float],
    queue_factory,
):
    wrapper_observation = _run_collection_wrapper_arm(
        numprocesses, initial_items, duration_ledger,
    )
    final_items = list(wrapper_observation["after_items"])
    finish_config = _OptionConfig(
        numprocesses=numprocesses,
        dist="loadgroup",
        loadscopereorder=True,
    )
    # The production hook always prioritizes first.  workerinput suppresses
    # unrelated controller-only receipt prewarming after that ordering step.
    finish_config.workerinput = {}
    CONF.pytest_collection_finish(SimpleNamespace(
        items=final_items,
        config=finish_config,
    ))
    collection = tuple(item.nodeid for item in final_items)
    config = _SchedulerConfig(numprocesses)
    scheduler = LoadGroupScheduling(config)
    queue = queue_factory(numprocesses)
    scheduler.workqueue = queue
    nodes = tuple(_FakeSchedulerNode(index) for index in range(numprocesses))
    for node in nodes:
        scheduler.add_node(node)
        scheduler.add_node_collection(node, collection)

    scheduler.schedule()
    # schedule() already exercises the scheduler's own _reschedule() pass; an
    # extra pass must not discover any work that escaped the global trace.
    for node in tuple(scheduler.nodes):
        scheduler._reschedule(node)
    assert not scheduler.workqueue
    return {
        "pre_finish_collection": wrapper_observation["after_nodeids"],
        "collection": collection,
        "dequeue_trace": tuple(queue.dequeue_trace),
        "before_identities": wrapper_observation["before_identities"],
        "ledger_identity": wrapper_observation["ledger_identity"],
        "loadgroup": wrapper_observation["loadgroup"],
        "loadscopereorder": config.option.loadscopereorder,
    }


def test_g11_loadgroup_global_dequeue_order_is_worker_count_independent():
    initial_items = _nproc_initial_items()
    duration_ledger = dict(_NPROC_DURATION_LEDGER)
    observations = {
        numprocesses: _run_scheduler_arm(
            numprocesses,
            initial_items,
            duration_ledger,
            lambda _numprocesses: _TracingWorkQueue(),
        )
        for numprocesses in _NPROC_ARMS
    }

    for observation in observations.values():
        assert observation["collection"] == _NPROC_EXPECTED_NODEIDS
        assert observation["dequeue_trace"] == _NPROC_EXPECTED_SCOPES
    assert all(
        observation["before_identities"]
        == observations[_NPROC_ARMS[0]]["before_identities"]
        for observation in observations.values()
    )
    assert {
        observation["ledger_identity"] for observation in observations.values()
    } == {id(duration_ledger)}
    assert {
        observation["loadgroup"] for observation in observations.values()
    } == {True}
    assert {
        observation["loadscopereorder"] for observation in observations.values()
    } == {True}
    _assert_arm_tuples_equal(
        observations, "dequeue_trace", "global dequeue trace",
    )


def test_g11_final_collection_and_mixed_scope_order_are_worker_count_independent():
    fixture = _nproc_scheduler_fixture()
    _assert_nproc_scheduler_fixture_contract(fixture)
    initial_items = fixture["initial_items"]
    duration_ledger = fixture["duration_ledger"]
    observations = {
        numprocesses: _run_scheduler_arm(
            numprocesses,
            initial_items,
            duration_ledger,
            lambda _numprocesses: _TracingWorkQueue(),
        )
        for numprocesses in _NPROC_ARMS
    }

    for observation in observations.values():
        assert observation["pre_finish_collection"] == (
            fixture["pre_finish_nodeids"]
        )
        assert observation["collection"] == fixture["final_nodeids"]
        assert observation["dequeue_trace"] == fixture["dequeue_scopes"]
    assert all(
        observation["before_identities"]
        == observations[_NPROC_ARMS[0]]["before_identities"]
        for observation in observations.values()
    )
    assert {
        observation["ledger_identity"] for observation in observations.values()
    } == {id(duration_ledger)}
    assert {
        observation["loadgroup"] for observation in observations.values()
    } == {True}
    assert {
        observation["loadscopereorder"] for observation in observations.values()
    } == {True}
    _assert_arm_tuples_equal(
        observations, "collection", "scheduler input collection",
    )
    _assert_arm_tuples_equal(
        observations, "dequeue_trace", "global dequeue trace",
    )


def test_g11_loadgroup_worker_dependent_tie_break_control_fails(monkeypatch):
    fixture = _nproc_scheduler_fixture()
    _assert_nproc_scheduler_fixture_contract(fixture)
    initial_items = fixture["initial_items"]
    duration_ledger = fixture["duration_ledger"]
    schedule_globals = LoadGroupScheduling.schedule.__globals__
    installed_sorted = schedule_globals.get("sorted", sorted)
    active_numprocesses = {"value": None}
    injected_arms = []

    # Patch the installed schedule() callable's exact global ordering lookup,
    # not the observation queue.  The injected comparator models a regression
    # that caps unit size by worker count.
    def worker_dependent_unit_order(iterable, *, key=None, reverse=False):
        entries = tuple(iterable)
        numprocesses = active_numprocesses["value"]
        assert key is not None
        assert numprocesses in _NPROC_ARMS
        injected_arms.append(numprocesses)
        return installed_sorted(
            entries,
            key=lambda item: -min(len(item[1]), numprocesses),
            reverse=reverse,
        )

    monkeypatch.setitem(
        schedule_globals,
        "sorted",
        worker_dependent_unit_order,
    )
    observations = {}
    for numprocesses in _NPROC_ARMS:
        active_numprocesses["value"] = numprocesses
        observations[numprocesses] = _run_scheduler_arm(
            numprocesses,
            initial_items,
            duration_ledger,
            lambda _numprocesses: _TracingWorkQueue(),
        )

    assert injected_arms == list(_NPROC_ARMS)
    assert all(
        observation["before_identities"]
        == observations[_NPROC_ARMS[0]]["before_identities"]
        for observation in observations.values()
    )
    assert {
        observation["ledger_identity"] for observation in observations.values()
    } == {id(duration_ledger)}
    assert {
        observation["loadgroup"] for observation in observations.values()
    } == {True}
    assert {
        observation["loadscopereorder"] for observation in observations.values()
    } == {True}
    _assert_arm_tuples_equal(
        observations, "collection", "scheduler input collection",
    )
    assert observations[16]["dequeue_trace"][:2] == ("medium", "large")
    assert observations[32]["dequeue_trace"][:2] == ("large", "medium")
    with pytest.raises(AssertionError, match="global dequeue trace changed"):
        _assert_arm_tuples_equal(
            observations, "dequeue_trace", "global dequeue trace",
        )


def _run() -> int:
    """Keep this test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
