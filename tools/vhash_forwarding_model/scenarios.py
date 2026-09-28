"""Small fixed histories and reachability predicates for S1--S8."""
from __future__ import annotations

from dataclasses import replace
from .model import State, Txn, Version

NAMES = tuple(f"S{i}" for i in range(1, 9))


def _v(key, ts, rts=None):
    return Version(f"{key}{ts}", key, ts, ts if rts is None else rts)


def _t(name, ts, *ops):
    return Txn(name, ts, tuple(ops))


def scenario(name):
    if name == "S1":
        state = State((_v("A", 10), _v("B", 11)),
                      (_t("T", 70, ("R", "A"), ("W", "B")),
                       _t("W", 50, ("R", "B"), ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "write_rts_check" and x.thread == "W"
    elif name == "S2":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("R", "B")),
                       _t("W", 70, ("W", "B"))), 1)
        predicate = lambda b, a, x: x.operation == "forward_check"
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
        predicate = lambda b, a, x: x.operation == "validate_read"
    elif name == "S6":
        state = State((_v("A", 10), _v("B", 11), _v("B", 25)),
                      (_t("T", 15, ("R", "A"), ("R", "B")),
                       _t("W", 20, ("W", "A"))), 1)
        predicate = lambda b, a, x: x.operation == "forward_check"
    elif name == "S7":
        state = State((_v("A", 20), _v("A", 65), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("R", "B")),), 1)
        predicate = lambda b, a, x: x.operation == "publish_floor"
    elif name == "S8":
        t = replace(_t("T", 70, ("R", "A"), ("W", "B")),
                    pc=2, phase="w_check", fixed=True, pending=("T:B",),
                    read_log=(("A", "A10"),), refs=("A10",))
        w = replace(_t("W", 50, ("R", "B"), ("W", "A")),
                    pc=2, phase="install", fixed=True,
                    read_log=(("B", "B11"),), refs=("B11",))
        p = replace(_t("P", 40, ("W", "A")), pc=1, phase="install", fixed=True)
        state = State((_v("A", 10, 70), _v("B", 11),
                       Version("T:B", "B", 70, 70, "PENDING", "T")),
                      (t, w, p), 1)
        predicate = lambda b, a, x: x.operation == "write_rts_check" and x.thread == "W"
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
    after = replace(before, versions=(replace(versions[0], reclaimed=True), versions[1]),
                    last_gc="A20")
    return before, after
