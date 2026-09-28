"""Small fixed histories and reachability predicates for S1--S10."""
from __future__ import annotations

from dataclasses import replace
from .model import State, Txn, Version, enabled_steps

NAMES = tuple(f"S{i}" for i in range(1, 11))


def _v(key, ts, rts=None):
    return Version(f"{key}{ts}", key, ts, ts if rts is None else rts)


def _t(name, ts, *ops):
    return Txn(name, ts, tuple(ops))


def scenario(name):
    if name == "S1":
        state = State((_v("A", 10), _v("B", 11)),
                      (_t("T", 70, ("R", "A"), ("W", "B")),
                       _t("W", 50, ("R", "B"), ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "install" and x.version == "W:A" and any(
            t.id == "T" and t.phase in ("v_check", "w_check", "decision", "release", "done")
            and ("A", "A10") in t.read_log for t in b.txns)
    elif name == "S2":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("R", "B")),
                       _t("W", 70, ("W", "B"))), 1)
        predicate = lambda b, a, x: x.thread == "T" and x.operation in ("read", "cold_read") and any(
            t.id == "T" and t.cand_ts > t.start for t in b.txns) and any(
            v.id == "W:B" for v in b.versions)
    elif name == "S3":
        state = State((_v("A", 10), _v("A", 20), _v("A", 55),
                       _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "B"), ("R", "A")),), 1)
        predicate = lambda b, a, x: x.operation == "reclaim" and any(
            t.phase == "f_publish" for t in b.txns)
    elif name == "S4":
        state = State((_v("A", 10), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "B")),
                       _t("W", 43, ("W", "B"))), 2)
        predicate = lambda b, a, x: x.operation.startswith("decide_") and x.thread == "W" and any(
            v.status == "PENDING" and v.key == "B" and v.wts <= 45 for v in b.versions)
    elif name == "S5":
        state = State((_v("A", 100), _v("B", 101)),
                      (_t("T", 130, ("R", "A"), ("W", "B")),
                       _t("W", 120, ("R", "B"), ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "install" and x.version == "W:A" and any(
            t.id == "T" and t.phase == "v_rts" and t.index == 1 and ("A", "A100") in t.read_log
            for t in b.txns)
    elif name == "S6":
        state = State((_v("A", 10), _v("B", 11), _v("B", 25)),
                      (_t("T", 15, ("R", "A"), ("R", "B")),
                       _t("W", 20, ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "install" and x.version == "W:A" and any(
            t.id == "T" and t.phase in ("f_rts", "f_check") and t.target > 0 for t in b.txns)
    elif name == "S7":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("R", "B")),
                       _t("W", 65, ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "read_floor" and any(
            t.gc_floor > t.start and ("A", "A20") in t.read_log and
            any(v.id == "W:A" and v.wts > t.cand_ts for v in a.versions) and
            not any(v.key == "A" and v.status == "COMMITTED" and 20 < v.wts <= t.cand_ts
                    for v in a.versions) for t in a.txns)
    elif name == "S8":
        state = State((_v("A", 10), _v("B", 11)),
                      (_t("T", 70, ("R", "A"), ("W", "B")),
                       _t("W", 50, ("R", "B"), ("W", "A")),
                       _t("P", 40, ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "write_rts_check" and x.thread == "W"
    elif name == "S9":
        state = State((_v("A", 10), _v("B", 11)),
                      (_t("T", 60, ("R", "A"), ("W", "B")),
                       _t("W", 50, ("R", "B"), ("W", "A")),
                       _t("U", 80, ("R", "A"), ("W", "A"))), 1)
        predicate = lambda b, a, x: x.thread == "T" and x.operation == "validate_read" and x.fault == "U2" and any(
            t.id == "U" and t.phase in ("release", "done") and t.failed for t in b.txns)
    elif name == "S10":
        state = State((_v("A", 10), _v("B", 11), _v("B", 25)),
                      (_t("T", 15, ("R", "A"), ("R", "B"), ("W", "B")),
                       _t("W", 20, ("R", "B"), ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "install" and x.version == "W:A" and any(
            t.id == "T" and t.phase in ("f_rts", "f_check") and t.target > 0
            and ("A", "A10") in t.read_log
            and 10 < next(v.wts for v in a.versions if v.id == "W:A") < t.target
            for t in b.txns)
    else:
        raise KeyError(name)
    return state, predicate


def handmade_j1(cycle=True):
    versions = (_v("A", 10), _v("B", 11),
                Version("T:A", "A", 30, 30, owner="T"),
                Version("W:B", "B", 20, 20, owner="W"))
    t = replace(_t("T", 30), phase="done", read_log=(("B", "B11"),))
    w = replace(_t("W", 20), phase="done",
                read_log=(("A", "A10"),) if cycle else ())
    return State(versions, (t, w))


def handmade_j3(unsafe=True):
    versions = (_v("A", 20), _v("A", 65))
    t = _t("T", 61, ("R", "A")) if unsafe else _t("T", 70, ("R", "A"))
    before = State(versions, (t,), gc_seen=61)
    after = replace(before, versions=(replace(versions[0], reclaimed=True), versions[1]))
    return before, after


def handmade_future_forward():
    versions = (_v("A", 30), _v("A", 65), _v("B", 40), _v("B", 60))
    before = State(versions, (_t("T", 20, ("R", "B"), ("R", "A")),), gc_seen=20)
    after = replace(before, versions=(replace(versions[0], reclaimed=True),) + versions[1:])
    return before, after


def s8_prefix():
    state, _ = scenario("S8")
    trace = []
    for thread in ("T", "W", "P", "P", "P", "W", "W", "W", "T", "T", "T",
                   "T", "T", "T", "T", "T", "T", "T"):
        choices = [(n, step) for n, step in enabled_steps(state, "v0") if step.thread == thread]
        assert len(choices) == 1
        state, step = choices[0]
        trace.append(step)
    assert next(t for t in state.txns if t.id == "T").phase == "w_check"
    return trace, state
