"""Small fixed histories and reachability predicates for S1--S10."""
from __future__ import annotations

from dataclasses import replace
from .model import State, Txn, Version, enabled_steps, visible, _hot

NAMES = tuple(f"S{i}" for i in range(1, 11))
GC_NAMES = tuple(f"G{i}" for i in range(1, 7))


def _v(key, ts, rts=None):
    return Version(f"{key}{ts}", key, ts, ts if rts is None else rts)


def _t(name, ts, *ops):
    return Txn(name, ts, tuple(ops))


def scenario(name):
    if name == "G1":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("WAIT", "")),
                       _t("W", 50, ("W", "B"))))
        predicate = lambda b, a, x: x.operation == "read_floor" and any(
            t.id == "T" and t.gc_floor > t.start and t.pc == 1 and t.phase == "ops"
            for t in a.txns)
    elif name == "G2":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("WAIT", "")),
                       _t("U", 35, ("R", "A"), ("WAIT", ""))))
        predicate = lambda b, a, x: x.operation == "read_floor" and any(
            t.id == "T" and t.gc_floor > t.start and t.pc == 1 for t in a.txns) and any(
            t.id == "U" and t.gc_floor == t.start and t.pc == 1 for t in a.txns)
    elif name == "G3":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "A"), ("WAIT", ""), ("R", "B")),
                       _t("W", 50, ("W", "A"))))
        predicate = lambda b, a, x: x.operation == "read_floor" and any(
            t.id == "T" and t.phase in ("p_rts", "p_check", "p_commit")
            and t.cand_ts == t.start for t in a.txns)
    elif name == "G4":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60), _v("B", 80)),
                      (_t("T", 45, ("R", "A"), ("WAIT", ""), ("R", "B")),))
        predicate = lambda b, a, x: x.operation == "read_floor" and any(
            t.id == "T" and t.cand_ts > t.start and t.pc == 1 for t in a.txns)
    elif name == "G5":
        state = State((_v("A", 10), _v("B", 11), _v("B", 25)),
                      (_t("T", 15, ("R", "A"), ("WAIT", ""), ("W", "B")),
                       _t("W", 20, ("R", "B"), ("W", "A"))))
        predicate = lambda b, a, x: x.operation == "install" and x.version == "W:A" and any(
            t.id == "T" and t.phase in ("p_rts", "p_check", "p_commit") for t in a.txns)
    elif name == "G6":
        state = State((_v("A", 20), _v("B", 40), _v("B", 60), _v("B", 80)),
                      (_t("T", 45, ("R", "A"), ("WAIT", ""), ("R", "B")),
                       _t("W", 70, ("W", "A"))))
        predicate = lambda b, a, x: x.operation == "pressure_fallback" and any(
            t.id == "T" and t.published_max > t.start for t in a.txns) and any(
            v.id == "B40" and v.reclaimed for v in a.versions)
    elif name == "S1":
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
        def predicate(b, a, x):
            t = next(t for t in b.txns if t.id == "T")
            return (x.thread == "T" and x.operation in ("forward_check", "forward_commit")
                    and bool(t.forward_hot) and
                    not _hot(b, next(v for v in b.versions if v.id == t.forward_hot)))
    elif name == "S3":
        state = State((_v("A", 10), _v("A", 20), _v("A", 55),
                       _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "B"), ("R", "A")),), 1)
        predicate = lambda b, a, x: x.thread == "GC" and x.operation in ("read_floor", "reclaim") and any(
            t.phase == "f_publish" and t.cand_ts > t.start and t.start == 45
            and (old := visible(b, "A", t.start)) is not None
            and old.status == "COMMITTED" and not old.reclaimed for t in b.txns)
    elif name == "S4":
        state = State((_v("A", 10), _v("B", 40), _v("B", 60)),
                      (_t("T", 45, ("R", "B")),
                       _t("W", 43, ("W", "B"))), 2)
        predicate = lambda b, a, x: x.operation.startswith("decide_") and x.thread == "W" and any(
            t.id == "T" and t.phase == "ops" and t.pc == 0 and
            (pending := visible(b, "B", t.cand_ts)) is not None and
            pending.id == "W:B" and pending.status == "PENDING"
            for t in b.txns)
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
        predicate = lambda b, a, x: (x.thread == "W" and x.operation == "write_rts_check"
                                     and any(v.id == "P:A" and v.status == "PENDING"
                                             for v in b.versions))
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


def danger_witness(name):
    """Unsafe outcomes, distinct from the interruption-window witnesses."""
    if name in ("G1", "G2"):
        return lambda b, a, x: False
    if name == "G3":
        return lambda b, a, x: x.operation == "reclaim" and x.version == "B40" and any(
            t.id == "T" and t.cand_ts == 45 and t.pc == 1 and t.phase in
            ("p_rts", "p_check", "p_commit") for t in b.txns)
    if name == "G4":
        return lambda b, a, x: x.operation == "reclaim" and x.version == "B60" and any(
            t.id == "T" and t.cand_ts == 61 and t.pc == 1 for t in b.txns)
    if name == "G5":
        from .judge import j1
        return lambda b, a, x: x.operation == "decide_committed" and bool(j1(a))
    if name == "G6":
        from .judge import j3
        return lambda b, a, x: x.operation == "pressure_fallback" and bool(j3(b, a, x))
    if name == "S3":
        return lambda b, a, x: (x.operation == "reclaim" and x.version == "A20"
                                and any(t.phase == "f_publish" and t.start == 45
                                        and (old := visible(b, "A", t.start)) is not None
                                        and old.id == x.version for t in b.txns))
    if name == "S8":
        def danger(b, a, x, trace):
            if x.thread != "W" or x.operation != "decide_committed":
                return False
            if not any(v.id == "P:A" and v.status == "ABORTED" for v in b.versions):
                return False
            steps = trace()
            check = next((i for i, step in enumerate(steps) if step.thread == "W"
                          and step.operation == "write_rts_check" and step.version == "P:A"), None)
            abort = next((i for i, step in enumerate(steps) if step.thread == "P"
                          and step.operation == "decide_aborted"), None)
            return check is not None and abort is not None and check < abort
        return danger
    raise KeyError(name)


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
