"""Independent fixtures for the reusable concurrency model checker."""
from __future__ import annotations

import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from cc_model_checker import (  # noqa: E402
    SCHEMA, INITIAL_WRITER, CommittedVersion, Counterexample, CounterexampleStep,
    CycleEdge, Judgment, ModelInputError, ModelInvariantError, Read, explore,
    find_cycle, from_json_bytes, iter_l3, to_json_bytes, validate_counterexample,
)


def _version(id, key, writer=INITIAL_WRITER):
    return CommittedVersion(id, key, writer)


def _expect_raises(exc_type, call):
    try:
        call()
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


def test_search_all_edges_and_shortest():
    graph = {
        "root": (("short", "branch_short"), ("long1", "branch_long")),
        "long1": (("long2", "long_2"),),
        "long2": (("target", "long_3"),),
        "short": (("target", "short_2"),),
        "target": (("target", "return_seen"), ("end", "to_end")),
        "end": (),
    }
    result = explore("root", lambda state: graph[state], (
        Judgment("branch", lambda b, a, e: True,
                 lambda b, a, e: "short" if e == "branch_short" else None),
        Judgment("target", lambda b, a, e: True,
                 lambda b, a, e: "reached" if a == "target" else None),
        Judgment("seen", lambda b, a, e: True,
                 lambda b, a, e: "seen" if e == "return_seen" else None),
    ), witness=lambda b, a, e, trace: e == "to_end" and len(trace()) == 3)
    assert result.statistics.complete and result.statistics.stop_reason == "exhausted"
    assert result.statistics.visited == 6 and result.statistics.transitions_checked == 7
    assert result.statistics.terminal == 1
    assert result.first_violation.judgment_id == "branch"
    assert result.first_by_judgment["target"].steps == ("branch_short", "short_2")
    assert result.first_by_judgment["seen"].steps[-1] == "return_seen"
    assert result.witness_steps == ("branch_short", "short_2", "to_end")


def test_search_limits_and_invariant_error():
    graph = {0: ((1, "forward"),), 1: ((0, "back"), (2, "next")), 2: ()}
    walk = lambda state: graph[state]
    result = explore(0, walk, (), max_states=2)
    assert result.statistics.stop_reason == "max_states" and not result.statistics.complete
    with patch("cc_model_checker.search.monotonic", side_effect=(0.0, 1.0, 1.0)):
        result = explore(0, walk, (), max_seconds=0.5)
    assert result.statistics.stop_reason == "max_seconds" and not result.statistics.complete
    assert explore(0, lambda _: (), ()).statistics.complete
    for invalid_seconds in (float("nan"), float("inf"), float("-inf")):
        _expect_raises(ValueError, lambda: explore(0, walk, (), max_seconds=invalid_seconds))
    assert explore(0, lambda _: (), (), max_seconds=1.0).statistics.complete

    exc = _expect_raises(ModelInvariantError, lambda: explore(
        0, walk, (), state_invariant=lambda state: (_ for _ in ()).throw(ValueError("bad"))
        if state == 1 else None))
    assert exc.invariant_id == "state" and exc.partial_steps == ("forward",)
    assert isinstance(exc.__cause__, ValueError)
    exc = _expect_raises(ModelInvariantError, lambda: explore(
        0, walk, (), transition_invariant=lambda b, a, e:
        (_ for _ in ()).throw(ValueError("back")) if e == "back" else None))
    assert exc.invariant_id == "transition" and exc.partial_steps == ("forward", "back")
    assert isinstance(exc.__cause__, ValueError)


def test_cycle_ww_only_required():
    versions = {"A": (_version("A0", "A"), _version("A1", "A", "T"),
                      _version("A2", "A", "U")),
                "B": (_version("B0", "B"), _version("B1", "B", "T"))}
    cycle = find_cycle(frozenset(("T", "U")), versions, {"U": (Read("B", "B0"),)})
    assert cycle is not None and {edge.kind for edge in cycle.edges} == {"ww", "rw"}
    assert any(edge.kind == "ww" and (edge.from_version, edge.to_version) == ("A1", "A2")
               for edge in cycle.edges)


def test_cycle_wr_only_required():
    versions = {"A": (_version("A0", "A"), _version("A1", "A", "U")),
                "B": (_version("B0", "B"), _version("B1", "B", "U"))}
    cycle = find_cycle(frozenset(("T", "U")), versions,
                       {"T": (Read("A", "A1"), Read("B", "B0"))})
    assert cycle is not None and {edge.kind for edge in cycle.edges} == {"wr", "rw"}
    assert any(edge.kind == "wr" and edge.from_version == edge.to_version == "A1"
               for edge in cycle.edges)


def test_cycle_write_skew_rw_only_required():
    versions = {"A": (_version("A0", "A"), _version("A1", "A", "U")),
                "B": (_version("B0", "B"), _version("B1", "B", "T"))}
    cycle = find_cycle(frozenset(("T", "U")), versions,
                       {"T": (Read("A", "A0"),), "U": (Read("B", "B0"),)})
    assert cycle is not None and {edge.kind for edge in cycle.edges} == {"rw"}
    assert find_cycle(frozenset(("T", "U")), versions, {}) is None


def test_cycle_all_later_versions():
    versions = {"A": (_version("A0", "A"), _version("A00", "A"),
                      _version("A1", "A", "U")),
                "B": (_version("B0", "B"), _version("B1", "B", "T"))}
    cycle = find_cycle(frozenset(("T", "U")), versions,
                       {"T": (Read("A", "A0"),), "U": (Read("B", "B0"),)})
    assert cycle is not None
    assert any(edge.kind == "rw" and (edge.from_version, edge.to_version) == ("A0", "A1")
               for edge in cycle.edges)
    assert find_cycle(frozenset(("T", "U")), versions,
                      {"T": (Read("B", "B1"),)}) is None


def test_cycle_input_validation():
    duplicate = {"A": (_version("same", "A"),), "B": (_version("same", "B"),)}
    _expect_raises(ModelInputError, lambda: find_cycle(frozenset(), duplicate, {}))
    base = {"A": (_version("A0", "A"),)}
    _expect_raises(ModelInputError, lambda: find_cycle(frozenset(("T",)), base,
                                                  {"U": (Read("A", "A0"),)}))
    _expect_raises(ModelInputError, lambda: find_cycle(frozenset(("T",)), base,
                                                  {"T": (Read("B", "A0"),)}))
    _expect_raises(ModelInputError, lambda: find_cycle(frozenset(("T",)), base,
                                                  {"T": (Read("A", "missing"),)}))
    _expect_raises(ModelInputError, lambda: find_cycle(frozenset(("T",)),
                                                  {"A": (_version("A1", "A", "U"),)}, {}))
    versions = {"A": (_version("A0", "A"), _version("A1", "A", "T"),
                      _version("A2", "A", "U"), _version("A3", "A", "T"))}
    _expect_raises(ModelInputError, lambda: find_cycle(frozenset(("T", "U")), versions, {}))
    assert find_cycle(frozenset(("T", "U")),
                      {"A": versions["A"][:3]}, {}) is None


def test_l3_counts_order_ids():
    for count, expected in ((2, 1600), (3, 32000)):
        rows = list(iter_l3(count))
        assert len(rows) == expected
        assert len({row.id for row in rows}) == expected
        assert rows[0].id.startswith(f"l3-v1-n{count}-i11-t0RA")
        assert rows[-1].id.startswith(f"l3-v1-n{count}-i22-t0WBWB")
        assert [row.id for row in iter_l3(count)] == [row.id for row in rows]
        assert any(len(ops) == 2 for row in rows for ops in row.txn_ops)
    _expect_raises(ValueError, lambda: list(iter_l3(1)))


def _record():
    return Counterexample(SCHEMA, "sha256:" + "a" * 64, "scenario.1", "J1",
                          (CounterexampleStep(1, "T", "read", "A", "A0", None),),
                          ("T", "U"),
                          (CycleEdge("T", "U", "rw", "A", "A0", "A1"),
                           CycleEdge("U", "T", "rw", "B", "B0", "B1")), ("R1",))


def test_counterexample_schema():
    record = _record()
    encoded = to_json_bytes(record)
    assert from_json_bytes(encoded) == record
    assert validate_counterexample(asdict(record)) == record
    raw = asdict(record)
    raw["unknown"] = "x"
    _expect_raises(ValueError, lambda: validate_counterexample(raw))
    raw = asdict(record)
    raw["steps"][0]["observed_value"] = "free text"
    _expect_raises(ValueError, lambda: validate_counterexample(raw))
    raw = asdict(record)
    raw["steps"][0]["number"] = True
    _expect_raises(ValueError, lambda: validate_counterexample(raw))
    raw = asdict(record)
    del raw["steps"][0]["name"]
    _expect_raises(ValueError, lambda: validate_counterexample(raw))
    raw = asdict(record)
    raw["cycle_edges"][0]["target"] = "T"
    _expect_raises(ValueError, lambda: validate_counterexample(raw))
    raw = encoded.decode("ascii").replace('"scenario_id":"scenario.1"',
                                           '"scenario_id":"scenario.1","scenario_id":"again"')
    _expect_raises(ValueError, lambda: from_json_bytes(raw.encode("ascii")))
    _expect_raises(ValueError, lambda: from_json_bytes(encoded.replace(b"null", b"NaN", 1)))
    vocabulary = {"judgment_id": frozenset(("J1",)),
                  "name": frozenset(("read",)), "rule_id": frozenset(("R1",))}
    assert validate_counterexample(record, vocabulary=vocabulary) == record
    assert from_json_bytes(encoded, vocabulary=vocabulary) == record
    _expect_raises(ValueError, lambda: validate_counterexample(record, vocabulary={"other": frozenset()}))
    for field, allowed in (("judgment_id", "J2"), ("name", "write"), ("rule_id", "R2")):
        _expect_raises(ValueError, lambda: validate_counterexample(
            record, vocabulary={field: frozenset((allowed,))}))
    _expect_raises(ValueError, lambda: from_json_bytes(
        encoded, vocabulary={"name": frozenset(("write",))}))
    raw = asdict(record)
    raw["steps"] = [dict(asdict(record.steps[0]), number=number)
                    for number in range(1, 1026)]
    _expect_raises(ValueError, lambda: validate_counterexample(raw))
    for field in ("cycle_txns", "cycle_edges", "rule_ids"):
        raw = asdict(record)
        raw[field] = raw[field] * 65
        _expect_raises(ValueError, lambda raw=raw: validate_counterexample(raw))


if __name__ == "__main__":
    failures = 0
    for name in sorted(name for name, value in globals().items()
                       if name.startswith("test_") and callable(value)):
        try:
            globals()[name]()
        except Exception:
            failures += 1
            print(f"FAIL {name}", flush=True)
            traceback.print_exc()
        else:
            print(f"PASS {name}", flush=True)
    sys.exit(1 if failures else 0)
