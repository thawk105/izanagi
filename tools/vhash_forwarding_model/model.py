"""Finite, sequentially consistent model of memo §4 assumptions.

Rule / counterexample:
| v0 counterexample | v1 rule |
| S8: PENDING predecessor hides an older committed version's rts | R9': inspect through PENDING versions to the first COMMITTED version |

One step observes one key's version sequence, writes one version field, or
changes local transaction state with at most one shared write. A status
decision atomically changes all versions of one transaction.
GC rereads the protection floor before reclaiming. Floors only increase because
all transactions are registered initially; using an older floor is conservative.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from time import perf_counter


@dataclass(frozen=True)
class Version:
    id: str
    key: str
    wts: int
    rts: int
    status: str = "COMMITTED"
    owner: str = "initial"
    reclaimed: bool = False


@dataclass(frozen=True)
class Txn:
    id: str
    start: int
    ops: tuple[tuple[str, str], ...]
    cand_ts: int = 0
    gc_floor: int = 0
    pc: int = 0
    phase: str = "ops"
    index: int = 0
    target: int = 0
    read_log: tuple[tuple[str, str], ...] = ()
    refs: tuple[str, ...] = ()
    confirmed: tuple[tuple[str, int], ...] = ()
    fixed: bool = False
    failed: bool = False
    pending: tuple[str, ...] = ()
    observed_end: tuple[tuple[str, int], ...] = ()
    observed_rts: tuple[tuple[str, int], ...] = ()

    def __post_init__(self):
        if not self.cand_ts:
            object.__setattr__(self, "cand_ts", self.start)
        if not self.gc_floor:
            object.__setattr__(self, "gc_floor", self.start)


@dataclass(frozen=True)
class State:
    versions: tuple[Version, ...]
    txns: tuple[Txn, ...]
    k: int = 1
    gc_seen: int | None = None

    def __post_init__(self):
        initial = [v.wts for v in self.versions if v.owner == "initial"]
        starts = [t.start for t in self.txns]
        assert len(initial + starts) == len(set(initial + starts))
        assert all(len(t.ops) <= 3 for t in self.txns)
        assert self.k in (1, 2)


@dataclass(frozen=True)
class Step:
    thread: str
    operation: str
    version: str = ""
    fault: str = ""


class TimestampCollisionError(RuntimeError):
    """Two distinct timestamp owners occupy the same time in a reachable state."""


def check_timestamp_uniqueness(s: State) -> None:
    """Check initial versions and each txn's candidate, target, and installed versions.

    A txn may repeat its own timestamp across these fields. Initial versions
    each own a distinct timestamp, even though their owner field is shared.
    """
    owners: dict[int, str] = {}

    def claim(ts: int, owner: str) -> None:
        previous = owners.setdefault(ts, owner)
        if previous != owner:
            raise TimestampCollisionError(f"timestamp {ts}: {previous} and {owner}")

    for v in s.versions:
        if v.owner == "initial":
            claim(v.wts, f"initial:{v.id}")
        else:
            claim(v.wts, v.owner)
    for t in s.txns:
        claim(t.cand_ts, t.id)
        if t.target:
            claim(t.target, t.id)


def _put_txn(s: State, t: Txn) -> State:
    return replace(s, txns=tuple(t if x.id == t.id else x for x in s.txns))


def _put_version(s: State, v: Version) -> State:
    return replace(s, versions=tuple(v if x.id == v.id else x for x in s.versions))


def _version(s: State, vid: str) -> Version:
    return next(v for v in s.versions if v.id == vid)


def _ordered(s: State, key: str) -> list[Version]:
    return sorted((v for v in s.versions if v.key == key and v.status != "ABORTED"),
                  key=lambda v: v.wts, reverse=True)


def visible(s: State, key: str, ts: int, faults: frozenset[str] = frozenset()) -> Version | None:
    candidates = [v for v in _ordered(s, key) if v.wts <= ts]
    if "U5" in faults:
        candidates = [v for v in candidates if v.status != "PENDING"]
    return candidates[0] if candidates else None


def _validation_visible(s: State, key: str, ts: int, owner: str) -> Version | None:
    candidates = [v for v in _ordered(s, key) if v.wts <= ts
                  and not (v.status == "PENDING" and v.owner == owner)]
    return candidates[0] if candidates else None


def _end(s: State, v: Version) -> int:
    return min((x.wts for x in _ordered(s, v.key) if x.wts > v.wts), default=10**9)


def _hot(s: State, v: Version) -> bool:
    return v.id in [x.id for x in _ordered(s, v.key)[:s.k]]


def _writes(t: Txn) -> tuple[str, ...]:
    return tuple(dict.fromkeys(k for op, k in t.ops if op == "W"))


def _next_free(s: State, minimum: int) -> int:
    used = ({v.wts for v in s.versions} | {t.start for t in s.txns}
            | {t.cand_ts for t in s.txns} | {t.target for t in s.txns if t.target})
    while minimum in used:
        minimum += 1
    return minimum


def _forward_target(s: State, t: Txn, key: str) -> int:
    h = [v for v in _ordered(s, key)[:s.k] if v.status == "COMMITTED" and v.wts > t.cand_ts]
    if not h:
        return 0
    chosen = min(h, key=lambda v: v.wts)
    target = _next_free(s, chosen.wts + 1)
    v = visible(s, key, target)
    return target if v and v.id == chosen.id else 0


def _read(s: State, t: Txn, key: str, *, cold: bool = False,
          faults: frozenset[str] = frozenset()) -> tuple[State, Step] | None:
    v = visible(s, key, t.cand_ts, faults)
    if v is None or v.status != "COMMITTED":
        return None
    if v.reclaimed:
        return s, Step(t.id, "touch_reclaimed", v.id)
    nt = replace(t, pc=t.pc + 1, phase="drop_refs" if "U3b" in faults else "ops",
                 read_log=t.read_log + ((key, v.id),),
                 refs=t.refs + (v.id,))
    ordinary = visible(s, key, t.cand_ts)
    changed_u5 = "U5" in faults and ordinary is not None and ordinary.id != v.id
    return _put_txn(s, nt), Step(t.id, "cold_read" if cold else "read", v.id,
                                "U5" if changed_u5 else "")


def _abort_or_next(t: Txn, success: bool) -> Txn:
    return replace(t, failed=t.failed or not success, index=t.index + 1)


def txn_step(s: State, t: Txn, protocol: str, faults: frozenset[str], o1: bool = False) -> tuple[State, Step] | None:
    if t.phase == "done":
        return None
    if t.phase == "ops":
        if t.pc == len(t.ops):
            return _put_txn(s, replace(t, phase="fixed")), Step(t.id, "begin_commit")
        op, key = t.ops[t.pc]
        if op == "W" or key in _writes(t) and any(o == "W" and k == key for o, k in t.ops[:t.pc]):
            return _put_txn(s, replace(t, pc=t.pc + 1)), Step(t.id, "buffer_write" if op == "W" else "local_read")
        v = visible(s, key, t.cand_ts, faults)
        if v is None or v.status == "PENDING":
            return None
        if v.reclaimed:
            return s, Step(t.id, "touch_reclaimed", v.id)
        if _hot(s, v):
            return _read(s, t, key, faults=faults)
        target = _forward_target(s, t, key) if not t.pending and not t.fixed else 0
        if target:
            ends = tuple((vid, _end(s, _version(s, vid))) for _, vid in t.read_log)
            nt = replace(t, phase="f_rts", target=target, index=0, observed_end=ends)
            if "U3a" in faults:
                nt = replace(nt, gc_floor=target)
            ordinary = visible(s, key, t.cand_ts)
            changed_u5 = "U5" in faults and ordinary is not None and ordinary.id != v.id
            return _put_txn(s, nt), Step(t.id, "forward_candidate", v.id,
                                        "U3a" if "U3a" in faults else "U5" if changed_u5 else "")
        return _read(s, t, key, cold=True, faults=faults)
    if t.phase == "drop_refs":
        return _put_txn(s, replace(t, phase="ops", refs=())), Step(t.id, "early_release_refs", fault="U3b")
    if t.phase in ("f_rts", "f_check"):
        ids = tuple(vid for _, vid in t.read_log)
        # U1f swaps the two passes.
        checking = (t.phase == "f_check") != ("U1f" in faults)
        if t.index == len(ids):
            next_phase = "f_check" if t.phase == "f_rts" else "f_commit"
            return _put_txn(s, replace(t, phase=next_phase, index=0)), Step(t.id, "forward_pass")
        vid = ids[t.index]
        v = _version(s, vid)
        if v.reclaimed:
            return s, Step(t.id, "touch_reclaimed", vid)
        if checking:
            if "U6" in faults:
                ok = v.wts <= t.target < dict(t.observed_end).get(vid, 10**9)
                fault = "U6"
            else:
                ok = visible(s, v.key, t.target).id == vid if visible(s, v.key, t.target) else False
                fault = "U1f" if "U1f" in faults else ""
            nt = _abort_or_next(t, ok)
            return _put_txn(s, nt), Step(t.id, "forward_check", vid, fault)
        nv = replace(v, rts=max(v.rts, t.target))
        return _put_txn(_put_version(s, nv), replace(t, index=t.index + 1)), Step(t.id, "forward_rts", vid,
                                                                                   "U1f" if "U1f" in faults else "")
    if t.phase == "f_commit":
        if t.failed:
            nt = replace(t, phase="fallback", target=0, failed=False)
            return _put_txn(s, nt), Step(t.id, "forward_fallback")
        nt = replace(t, cand_ts=t.target, phase="f_publish",
                     confirmed=t.confirmed + tuple((vid, t.target) for _, vid in t.read_log))
        return _put_txn(s, nt), Step(t.id, "forward_commit")
    if t.phase == "f_publish":
        return _put_txn(s, replace(t, gc_floor=t.cand_ts, phase="ops")), Step(t.id, "publish_floor")
    if t.phase == "fallback":
        return _read(s, t, t.ops[t.pc][1], cold=True, faults=faults)
    if t.phase == "fixed":
        return _put_txn(s, replace(t, fixed=True, phase="install")), Step(t.id, "fix_timestamp")
    if t.phase == "install":
        keys = _writes(t)
        if t.index == len(keys):
            return _put_txn(s, replace(t, phase="v_rts", index=0)), Step(t.id, "installed")
        key = keys[t.index]
        vid = f"{t.id}:{key}"
        v = Version(vid, key, t.cand_ts, t.cand_ts, "PENDING", t.id)
        ns = replace(s, versions=s.versions + (v,))
        nt = replace(t, index=t.index + 1, pending=t.pending + (vid,))
        return _put_txn(ns, nt), Step(t.id, "install", vid)
    if t.phase in ("v_rts", "v_check"):
        ids = tuple(vid for _, vid in t.read_log)
        checking = (t.phase == "v_check") != ("U1v" in faults)
        if o1:
            ids = tuple(vid for vid in ids if (vid, t.cand_ts) not in t.confirmed)
        if t.index == len(ids):
            return _put_txn(s, replace(t, phase="v_check" if t.phase == "v_rts" else "w_check", index=0)), Step(t.id, "validation_pass")
        vid = ids[t.index]
        v = _version(s, vid)
        if v.reclaimed:
            return s, Step(t.id, "touch_reclaimed", vid)
        if checking:
            if "U2" in faults and dict(t.observed_rts).get(vid, -1) >= t.cand_ts:
                ok, fault = True, "U2"
            else:
                vis = _validation_visible(s, v.key, t.cand_ts, t.id)
                ok, fault = bool(vis and vis.id == vid and not v.reclaimed), "U1v" if "U1v" in faults else ""
            return _put_txn(s, _abort_or_next(t, ok)), Step(t.id, "validate_read", vid, fault)
        ns = _put_version(s, replace(v, rts=max(v.rts, t.cand_ts)))
        nt = replace(t, index=t.index + 1, observed_rts=t.observed_rts + ((vid, v.rts),))
        return _put_txn(ns, nt), Step(t.id, "validation_rts", vid,
                                                                     "U1v" if "U1v" in faults else "")
    if t.phase == "w_check":
        keys = _writes(t)
        if t.index == len(keys):
            return _put_txn(s, replace(t, phase="decision")), Step(t.id, "writes_checked")
        key = keys[t.index]
        older = [v for v in _ordered(s, key) if v.wts < t.cand_ts]
        checked = []
        for v in older:
            checked.append(v)
            if protocol == "v0" or v.status == "COMMITTED":
                break
        ok = all(v.rts <= t.cand_ts for v in checked)
        nt = _abort_or_next(t, ok)
        return _put_txn(s, nt), Step(t.id, "write_rts_check", checked[-1].id if checked else "",
                                           "")
    if t.phase == "decision":
        status = "ABORTED" if t.failed else "COMMITTED"
        ns = replace(s, versions=tuple(replace(v, status=status) if v.id in t.pending else v for v in s.versions))
        return _put_txn(ns, replace(t, phase="release")), Step(t.id, "decide_" + status.lower())
    if t.phase == "release":
        return _put_txn(s, replace(t, phase="done", refs=())), Step(t.id, "release_refs", fault="U3b" if "U3b" in faults else "")
    raise AssertionError(t.phase)


def gc_steps(s: State, faults: frozenset[str]) -> list[tuple[State, Step]]:
    active = [t for t in s.txns if t.phase != "done"]
    b = min((t.gc_floor for t in active), default=max((v.wts for v in s.versions), default=0) + 1)
    if s.gc_seen != b:
        return [(replace(s, gc_seen=b), Step("GC", "read_floor"))]
    out = []
    refs = {vid for t in s.txns for vid in t.refs}
    for v in s.versions:
        if v.reclaimed or v.status == "PENDING" or v.id in refs:
            continue
        successors = [x for x in s.versions if x.key == v.key and x.status == "COMMITTED"
                      and x.wts > v.wts and x.wts <= b]
        legal = v.status == "ABORTED" or bool(successors)
        if "U4" in faults:
            legal = v.wts < b
        if legal:
            ns = _put_version(s, replace(v, reclaimed=True))
            out.append((ns, Step("GC", "reclaim", v.id, "U4" if "U4" in faults else "")))
    return out


def enabled_steps(s: State, protocol: str = "v1", faults: frozenset[str] = frozenset(), o1: bool = False):
    assert protocol in ("v0", "v1")
    assert len(faults) <= 1
    for t in s.txns:
        result = txn_step(s, t, protocol, faults, o1)
        if result is not None:
            yield result
    yield from gc_steps(s, faults)


def changed_step_in_trace(trace: list[Step], fault: str) -> bool:
    return any(step.fault == fault for step in trace)


def replay(initial: State, trace: list[Step], protocol="v1", fault="", o1=False) -> State:
    s = initial
    for step in trace:
        matches = [(n, x) for n, x in enabled_steps(s, protocol, frozenset((fault,)) if fault else frozenset(), o1)
                   if x == step]
        assert len(matches) == 1, step
        s = matches[0][0]
    return s


def explore(initial: State, protocol="v1", fault="", witness=None, max_states=None,
            o1=False, max_seconds=None, all_transitions=False):
    """Explore every enabled edge, including edges to states already visited.

    J1 and J2 depend only on committed transactions and committed versions, so
    only decide_* edges can change them. J3 concerns reclaim and attempted
    access to a reclaimed version, so only those edges need its judgment.
    all_transitions is a reference mode for checking this restriction.
    """
    from .judge import judge
    faults = frozenset((fault,)) if fault else frozenset()
    began = perf_counter()
    queue = deque([initial])
    parent = {initial: None}
    check_timestamp_uniqueness(initial)
    verdicts = {"J1": None, "J2": None, "J3": None}
    violation_kinds = {"J1": set(), "J2": set(), "J3": set()}
    counterexample = None
    witness_trace = None
    terminals = deadlocks = 0
    timed_out = False
    def trace(s):
        steps = []
        while parent[s] is not None:
            s, step = parent[s]
            steps.append(step)
        return list(reversed(steps))
    while queue:
        if max_seconds is not None and perf_counter() - began >= max_seconds:
            timed_out = True
            break
        s = queue.popleft()
        steps = list(enabled_steps(s, protocol, faults, o1))
        if not steps:
            terminals += 1
            if any(t.phase != "done" for t in s.txns):
                deadlocks += 1
        for ns, step in steps:
            check_timestamp_uniqueness(ns)
            relevant = (all_transitions or step.operation.startswith("decide_")
                        or step.operation in ("reclaim", "touch_reclaimed"))
            if not relevant and not witness:
                found = {}
            elif relevant:
                found = judge(s, ns, step, all_transitions=all_transitions)
            else:
                found = {}
            candidate_trace = None
            for name, reason in found.items():
                if reason:
                    violation_kinds[name].add(reason.get("reason", "violation"))
                if reason and verdicts[name] is None:
                    verdicts[name] = reason
                    candidate_trace = candidate_trace or trace(s) + [step]
                    if name in ("J1", "J3") and counterexample is None:
                        counterexample = {"judge": name, "reason": reason, "steps": candidate_trace}
            if witness and witness(s, ns, step) and witness_trace is None:
                witness_trace = trace(s) + [step]
            if ns in parent:
                continue
            parent[ns] = (s, step)
            queue.append(ns)
            if max_states and len(parent) >= max_states:
                queue.clear()
                break
    return {"statistics": {"visited": len(parent), "terminal": terminals, "deadlock": deadlocks,
                           "seconds": perf_counter() - began,
                           "complete": not timed_out and (not bool(max_states) or len(parent) < max_states)},
            "verdicts": verdicts, "counterexample": counterexample,
            "violation_kinds": {k: sorted(v) for k, v in violation_kinds.items()},
            "witness": {"reached": witness_trace is not None, "steps": witness_trace or []}}


def aborted_after_fault(initial: State, fault: str, o1: bool = False) -> list[Step] | None:
    """Find a fault step followed by that transaction's failed commit validation."""
    queue = deque([(initial, "", False, [])])
    seen = {(initial, "", False)}
    while queue:
        state, actor, failed_validation, trace = queue.popleft()
        for next_state, step in enabled_steps(state, "v1", frozenset((fault,)), o1):
            changed = step.fault == fault
            if changed and fault == "U5":
                txn = next(t for t in state.txns if t.id == step.thread)
                key = txn.ops[txn.pc][1]
                ordinary = visible(state, key, txn.cand_ts)
                changed = ordinary is not None and ordinary.id != step.version
            next_actor = actor or (step.thread if changed else "")
            next_failed = failed_validation or bool(
                next_actor and step.thread == next_actor and step.operation == "validate_read"
                and next(t for t in next_state.txns if t.id == next_actor).failed)
            next_trace = trace + [step]
            if (next_actor and next_failed and step.thread == next_actor
                    and step.operation == "decide_aborted"):
                return next_trace
            key = (next_state, next_actor, next_failed)
            if key not in seen:
                seen.add(key)
                queue.append((next_state, next_actor, next_failed, next_trace))
    return None
