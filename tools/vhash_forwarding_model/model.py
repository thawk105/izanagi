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
from dataclasses import dataclass, field, replace
from inspect import signature
from time import monotonic
from .helper import HelperState, helper_steps


@dataclass(frozen=True, slots=True)
class Version:
    id: str
    key: str
    wts: int
    rts: int
    status: str = "COMMITTED"
    owner: str = "initial"
    reclaimed: bool = False


@dataclass(frozen=True, slots=True)
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
    forward_hot: str = ""
    pressure_request: bool = False
    attempt_base: int = 0
    tried_targets: tuple[int, ...] = ()
    pressure_base_confirmed: int = 0
    pressure_base_floor: int = 0
    gen: int = 0
    expired: bool = False
    helper_base: int = 0
    resume_used: bool = False
    held_refs: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.cand_ts:
            object.__setattr__(self, "cand_ts", self.start)
        if not self.gc_floor:
            object.__setattr__(self, "gc_floor", self.start)


@dataclass(frozen=True, slots=True)
class State:
    versions: tuple[Version, ...]
    txns: tuple[Txn, ...]
    k: int = 1
    gc_seen: int | None = None
    helper: HelperState = HelperState()
    _cached_hash: int = field(init=False, compare=False, repr=False)

    def __post_init__(self):
        initial = [v.wts for v in self.versions if v.owner == "initial"]
        starts = [t.start for t in self.txns]
        assert len(initial + starts) == len(set(initial + starts))
        assert all(len(t.ops) <= 4 and sum(op != "WAIT" for op, _ in t.ops) <= 3
                   for t in self.txns)
        assert self.k in (1, 2)
        object.__setattr__(self, "_cached_hash", hash((self.versions, self.txns, self.k, self.gc_seen, self.helper)))

    def __hash__(self):
        return self._cached_hash


@dataclass(frozen=True, slots=True)
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


def floor_lowering_transition(before: State, after: State) -> bool:
    """Whether one explored edge lowers any transaction's published GC floor."""
    return any(new.gc_floor < old.gc_floor for old, new in zip(before.txns, after.txns))


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
            | {t.cand_ts for t in s.txns} | {t.target for t in s.txns if t.target}
            | ({s.helper.target} if s.helper.target else set()))
    while minimum in used:
        minimum += 1
    return minimum


def _forward_target(s: State, t: Txn, key: str) -> tuple[int, str, str]:
    h = [v for v in _ordered(s, key)[:s.k] if v.status == "COMMITTED" and v.wts > t.cand_ts]
    if not h:
        return 0, "", ""
    chosen = min(h, key=lambda v: v.wts)
    if chosen.reclaimed:
        return 0, chosen.id, ""
    target = _next_free(s, chosen.wts + 1)
    v = visible(s, key, target)
    if v and v.reclaimed:
        return 0, v.id, ""
    return (target if v and v.id == chosen.id else 0), "", chosen.id


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
    if ordinary and ordinary.reclaimed:
        return s, Step(t.id, "touch_reclaimed", ordinary.id)
    changed_u5 = "U5" in faults and ordinary is not None and ordinary.id != v.id
    return _put_txn(s, nt), Step(t.id, "cold_read" if cold else "read", v.id,
                                "U5" if changed_u5 else "")


def _abort_or_next(t: Txn, success: bool) -> Txn:
    return replace(t, failed=t.failed or not success, index=t.index + 1)


def txn_step(s: State, t: Txn, protocol: str, faults: frozenset[str], o1: bool = False,
             pressure: str = "off", revert_after_confirm: bool = False) -> tuple[State, Step] | None:
    if t.phase == "done":
        return None
    if t.phase == "ops":
        if t.pc == len(t.ops):
            return _put_txn(s, replace(t, phase="fixed")), Step(t.id, "begin_commit")
        op, key = t.ops[t.pc]
        if op == "WAIT":
            if pressure == "helper":
                base = t.cand_ts
                if "UH4" in faults and t.helper_base:
                    base = t.helper_base
                nt = replace(t, pc=t.pc + 1, phase="resume", gen=t.gen + 1,
                             cand_ts=base, resume_used=False)
                if base != t.cand_ts:
                    nt = replace(nt, confirmed=tuple((vid, ts) for vid, ts in t.confirmed if ts <= base))
                return _put_txn(s, nt), Step(t.id, "end_wait", fault="UH4" if "UH4" in faults and base != t.cand_ts else "")
            return _put_txn(s, replace(t, pc=t.pc + 1, pressure_request=False,
                                       tried_targets=())), Step(t.id, "end_wait")
        if op == "W" or key in _writes(t) and any(o == "W" and k == key for o, k in t.ops[:t.pc]):
            return _put_txn(s, replace(t, pc=t.pc + 1)), Step(t.id, "buffer_write" if op == "W" else "local_read")
        v = visible(s, key, t.cand_ts, faults)
        if v is None or v.status == "PENDING":
            return None
        if v.reclaimed:
            return s, Step(t.id, "touch_reclaimed", v.id)
        if _hot(s, v):
            return _read(s, t, key, faults=faults)
        target, touched, hot = _forward_target(s, t, key) if not t.pending and not t.fixed else (0, "", "")
        if touched:
            return s, Step(t.id, "touch_reclaimed", touched)
        if target:
            ends = tuple((vid, _end(s, _version(s, vid))) for _, vid in t.read_log)
            nt = replace(t, phase="f_rts", target=target, index=0, observed_end=ends,
                         forward_hot=hot)
            if "U3a" in faults:
                nt = replace(nt, gc_floor=target)
            ordinary = visible(s, key, t.cand_ts)
            if ordinary and ordinary.reclaimed:
                return s, Step(t.id, "touch_reclaimed", ordinary.id)
            changed_u5 = "U5" in faults and ordinary is not None and ordinary.id != v.id
            return _put_txn(s, nt), Step(t.id, "forward_candidate", v.id,
                                        "U3a" if "U3a" in faults else "U5" if changed_u5 else "")
        return _read(s, t, key, cold=True, faults=faults)
    if t.phase == "drop_refs":
        return _put_txn(s, replace(t, phase="ops", refs=())), Step(t.id, "early_release_refs", fault="U3b")
    if t.phase == "resume":
        if not t.resume_used:
            for vid in dict.fromkeys(t.refs + t.held_refs):
                if _version(s, vid).reclaimed:
                    return s, Step(t.id, "touch_reclaimed", vid)
            return _put_txn(s, replace(t, resume_used=True)), Step(t.id, "use_values")
        if t.expired:
            if "UH5" in faults:
                return _put_txn(s, replace(t, phase="ops")), Step(t.id, "check_expired", fault="UH5")
            return _put_txn(s, replace(t, phase="resume_abort")), Step(t.id, "check_expired")
        return _put_txn(s, replace(t, phase="ops")), Step(t.id, "check_expired")
    if t.phase == "resume_abort":
        return _put_txn(s, replace(t, phase="release", failed=True)), Step(t.id, "decide_aborted")
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
                selected = visible(s, v.key, t.target)
                if selected and selected.reclaimed:
                    return s, Step(t.id, "touch_reclaimed", selected.id)
                ok = bool(selected and selected.id == vid)
                fault = "U1f" if "U1f" in faults else ""
            nt = _abort_or_next(t, ok)
            return _put_txn(s, nt), Step(t.id, "forward_check", vid, fault)
        nv = replace(v, rts=max(v.rts, t.target))
        return _put_txn(_put_version(s, nv), replace(t, index=t.index + 1)), Step(t.id, "forward_rts", vid,
                                                                                   "U1f" if "U1f" in faults else "")
    if t.phase == "f_commit":
        if t.failed:
            nt = replace(t, phase="fallback", target=0, failed=False, forward_hot="")
            return _put_txn(s, nt), Step(t.id, "forward_fallback")
        nt = replace(t, cand_ts=t.target, phase="f_publish", forward_hot="",
                     confirmed=t.confirmed + tuple((vid, t.target) for _, vid in t.read_log))
        return _put_txn(s, nt), Step(t.id, "forward_commit")
    if t.phase == "f_publish":
        return _put_txn(s, replace(t, gc_floor=max(t.gc_floor, t.cand_ts), phase="ops")), Step(t.id, "publish_floor")
    if t.phase == "fallback":
        return _read(s, t, t.ops[t.pc][1], cold=True, faults=faults)
    if t.phase in ("p_rts", "p_check"):
        ids = tuple(vid for _, vid in t.read_log)
        if t.index == len(ids):
            phase = "p_check" if t.phase == "p_rts" else "p_commit"
            return _put_txn(s, replace(t, phase=phase, index=0)), Step(t.id, "pressure_pass")
        vid = ids[t.index]
        v = _version(s, vid)
        if v.reclaimed:
            return s, Step(t.id, "touch_reclaimed", vid)
        if t.phase == "p_rts":
            ns = _put_version(s, replace(v, rts=max(v.rts, t.target)))
            return _put_txn(ns, replace(t, index=t.index + 1)), Step(t.id, "pressure_rts", vid)
        selected = visible(s, v.key, t.target)
        if selected and selected.reclaimed:
            return s, Step(t.id, "touch_reclaimed", selected.id)
        ok = "UG3" in faults or bool(selected and selected.id == vid)
        return _put_txn(s, _abort_or_next(t, ok)), Step(t.id, "pressure_check", vid,
                                                        "UG3" if "UG3" in faults else "")
    if t.phase == "p_commit":
        if t.failed:
            base = t.start if "UF1" in faults and t.gc_floor > t.start else t.attempt_base
            nt = replace(t, cand_ts=base, phase="ops", target=0, failed=False,
                         pressure_request=False)
            return _put_txn(s, nt), Step(t.id, "pressure_fallback",
                                         fault="UF1" if base == t.start and base != t.attempt_base else "")
        floor = 10**9 if "UG2" in faults else t.gc_floor
        nt = replace(t, cand_ts=t.target, phase="p_publish", gc_floor=floor,
                     refs=() if "UG2r" in faults else t.refs,
                     confirmed=t.confirmed + tuple((vid, t.target) for _, vid in t.read_log))
        fault = "UG2" if "UG2" in faults else "UG2r" if "UG2r" in faults else ""
        return _put_txn(s, nt), Step(t.id, "pressure_commit", fault=fault)
    if t.phase == "p_publish":
        nt = replace(t, gc_floor=max(t.gc_floor, t.cand_ts) if "UG2" not in faults else t.gc_floor, phase="ops",
                     target=0, pressure_request=False)
        return _put_txn(s, nt), Step(t.id, "pressure_publish")
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
                if vis and vis.reclaimed:
                    return s, Step(t.id, "touch_reclaimed", vis.id)
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
            if v.reclaimed:
                return s, Step(t.id, "touch_reclaimed", v.id)
            checked.append(v)
            if protocol == "v0" or v.status == "COMMITTED":
                break
        ok = all(v.rts <= t.cand_ts for v in checked)
        nt = _abort_or_next(t, ok)
        return _put_txn(s, nt), Step(t.id, "write_rts_check", checked[-1].id if checked else "",
                                           "")
    if t.phase == "decision":
        status = "ABORTED" if t.failed else "COMMITTED"
        if t.expired:
            status = "ABORTED"
        ns = replace(s, versions=tuple(replace(v, status=status) if v.id in t.pending else v for v in s.versions))
        return _put_txn(ns, replace(t, phase="release")), Step(t.id, "decide_" + status.lower())
    if t.phase == "release":
        return _put_txn(s, replace(t, phase="done", refs=())), Step(t.id, "release_refs", fault="U3b" if "U3b" in faults else "")
    raise AssertionError(t.phase)


def gc_steps(s: State, faults: frozenset[str]) -> list[tuple[State, Step]]:
    active = [t for t in s.txns if t.phase != "done" and not t.expired]
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


def enabled_steps(s: State, protocol: str = "v1", faults: frozenset[str] = frozenset(),
                  o1: bool = False, pressure: str = "off", revert_after_confirm: bool = False,
                  resume: str = "accept"):
    assert protocol in ("v0", "v1")
    assert len(faults) <= 1
    for t in s.txns:
        result = txn_step(s, t, protocol, faults, o1, pressure, revert_after_confirm)
        if result is not None:
            yield result
        if pressure == "helper" and t.phase == "resume" and not t.resume_used:
            if t.expired and "UH5" not in faults:
                yield _put_txn(s, replace(t, phase="resume_abort")), Step(t.id, "check_expired")
            elif t.expired:
                yield _put_txn(s, replace(t, phase="ops")), Step(t.id, "check_expired", fault="UH5")
            else:
                yield _put_txn(s, replace(t, phase="ops")), Step(t.id, "check_expired")
        if pressure == "helper" and revert_after_confirm and t.phase == "ops" and t.pc < len(t.ops) and t.ops[t.pc][0] == "WAIT" and t.helper_base and t.gc_floor < t.cand_ts:
            # The alternate end_wait edge cancels an unpublished H4.
            nt = replace(t, pc=t.pc + 1, phase="resume", gen=t.gen + 1,
                         cand_ts=t.helper_base, resume_used=False,
                         confirmed=tuple((vid, ts) for vid, ts in t.confirmed if ts <= t.helper_base))
            yield _put_txn(s, nt), Step(t.id, "end_wait_revert")
        if pressure == "self" and t.phase == "ops" and t.pc < len(t.ops) and t.ops[t.pc] == ("WAIT", ""):
            if not t.pressure_request:
                yield _put_txn(s, replace(t, pressure_request=True)), Step("GC", "request_pressure", t.id)
            if t.pressure_request and not t.fixed and not t.pending:
                from .gc_connection import pressure_targets
                for target in pressure_targets(s, t):
                    if target in t.tried_targets:
                        continue
                    nt = replace(t, phase="p_rts", target=target, index=0, failed=False,
                                 attempt_base=t.cand_ts, pressure_base_confirmed=len(t.confirmed),
                                 pressure_base_floor=t.gc_floor,
                                 tried_targets=t.tried_targets + (target,))
                    if "UG1" in faults:
                        nt = replace(nt, gc_floor=max(t.gc_floor, target))
                    yield _put_txn(s, nt), Step(t.id, "pressure_start", str(target),
                                                 "UG1" if "UG1" in faults else "")
        if revert_after_confirm and t.phase == "p_publish":
            nt = replace(t, cand_ts=t.attempt_base, target=0, phase="ops",
                         confirmed=t.confirmed[:t.pressure_base_confirmed],
                         pressure_request=False)
            yield _put_txn(s, nt), Step(t.id, "pressure_revert")
    if pressure == "helper":
        assert all(sum(op == "WAIT" for op, _ in t.ops) <= 1 for t in s.txns)
        yield from helper_steps(s, faults, resume)
    yield from gc_steps(s, faults)


def changed_step_in_trace(trace: list[Step], fault: str) -> bool:
    return any(step.fault == fault for step in trace)


def fault_changes_forward_check(initial: State, trace: list[Step], fault: str,
                                o1: bool = False) -> bool:
    """Compare each faulty forwarding step with the sound check in that state."""
    assert fault in ("U1f", "U6")
    state = initial
    for step in trace:
        if step.fault == fault and step.operation in ("forward_check", "forward_rts"):
            t = next(t for t in state.txns if t.id == step.thread)
            v = _version(state, step.version)
            selected = visible(state, v.key, t.target)
            sound_ok = bool(selected and selected.id == v.id and not selected.reclaimed)
            if step.operation == "forward_rts":
                faulty_ok = True  # U1f has already checked and now skips the check.
            else:
                next_state, _ = txn_step(state, t, "v1", frozenset((fault,)), o1)
                faulty_ok = not next(x for x in next_state.txns if x.id == t.id).failed
            if faulty_ok != sound_ok:
                return True
        state = next(n for n, x in enabled_steps(
            state, "v1", frozenset((fault,)), o1) if x == step)
    return False


def replay(initial: State, trace: list[Step], protocol="v1", fault="", o1=False,
           pressure="off", revert_after_confirm=False, resume="accept") -> State:
    s = initial
    for step in trace:
        matches = [(n, x) for n, x in enabled_steps(s, protocol, frozenset((fault,)) if fault else frozenset(), o1,
                                                pressure, revert_after_confirm, resume)
                   if x == step]
        assert len(matches) == 1, step
        s = matches[0][0]
    return s


def explore(initial: State, protocol="v1", fault="", witness=None, max_states=None,
            o1=False, max_seconds=None, all_transitions=False, danger=None,
            pressure="off", revert_after_confirm=False, state_invariant=None,
            transition_invariant=None, collect_effects=True, resume="accept"):
    """Explore every enabled edge, including edges to states already visited.

    J1 and J2 depend only on committed transactions and committed versions, so
    only decide_* edges can change them. J3 concerns reclaim and attempted
    access to a reclaimed version, so only those edges need its judgment.
    all_transitions is a reference mode for checking this restriction.
    """
    from .judge import judge
    faults = frozenset((fault,)) if fault else frozenset()
    assert resume in ("accept", "expire")
    began = monotonic()
    witness_uses_trace = witness is not None and len(signature(witness).parameters) == 4
    danger_uses_trace = danger is not None and len(signature(danger).parameters) == 4
    queue = deque([initial])
    parent = {initial: None}
    check_timestamp_uniqueness(initial)
    if state_invariant is not None:
        state_invariant(initial)
    verdicts = {"J1": None, "J2": None, "J3": None}
    violation_kinds = {"J1": set(), "J2": set(), "J3": set()}
    counterexample = None
    witness_trace = None
    danger_trace = None
    effects = None
    if collect_effects and any(("WAIT", "") in t.ops for t in initial.txns):
        effects = {"waiting_states": 0, "max_B": None, "max_freed": None,
                   "simultaneous": None, "attributable": None,
                   "g2": {"T_only": None, "both": None}}
    terminals = deadlocks = floor_lowering_transitions = 0
    timed_out = False
    fault_step_seen = False
    floor_above_cand_states = 0
    def trace(s):
        steps = []
        while parent[s] is not None:
            s, step = parent[s]
            steps.append(step)
        return list(reversed(steps))
    while queue:
        if max_seconds is not None and monotonic() - began >= max_seconds:
            timed_out = True
            break
        s = queue.popleft()
        floor_above_cand_states += any(t.gc_floor > t.cand_ts and not t.expired for t in s.txns)
        if effects is not None:
            from .gc_connection import effect_snapshot
            t = next((t for t in s.txns if t.id == "T"), None)
            waiting = t is not None and t.phase == "ops" and t.pc < len(t.ops) and t.ops[t.pc] == ("WAIT", "")
            if waiting:
                effects["waiting_states"] += 1
                snap = effect_snapshot(s)
                for key, value in (("max_B", snap["B"]), ("max_freed", snap["freed"])):
                    if effects[key] is None or value > effects[key]["value"]:
                        effects[key] = {"value": value, "snapshot": snap, "steps": trace(s)}
                if any(x.id == "U" for x in s.txns):
                    u = next(t for t in s.txns if t.id == "U")
                    both_wait = u.phase == "ops" and u.pc < len(u.ops) and u.ops[u.pc] == ("WAIT", "")
                    label = "T_only" if both_wait and t.gc_floor > t.start and u.gc_floor == u.start else (
                        "both" if both_wait and t.gc_floor > t.start and u.gc_floor > u.start else "")
                    if label and (effects["g2"][label] is None or snap["B"] > effects["g2"][label]["snapshot"]["B"]):
                        effects["g2"][label] = {"snapshot": snap, "steps": trace(s)}
        steps = list(enabled_steps(s, protocol, faults, o1, pressure, revert_after_confirm, resume))
        if not steps:
            terminals += 1
            if any(t.phase != "done" for t in s.txns):
                deadlocks += 1
        for ns, step in steps:
            fault_step_seen |= bool(fault and step.fault == fault)
            floor_lowering_transitions += floor_lowering_transition(s, ns)
            if transition_invariant is not None:
                transition_invariant(s, ns, step)
            if ns not in parent:
                check_timestamp_uniqueness(ns)
                if state_invariant is not None:
                    state_invariant(ns)
            lowered = any(a.cand_ts < b.cand_ts for a, b in zip(ns.txns, s.txns))
            relevant = (all_transitions or step.operation.startswith("decide_")
                        or step.operation in ("reclaim", "touch_reclaimed") or lowered)
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
            if witness and witness_trace is None:
                reached = (witness(s, ns, step, lambda: trace(s) + [step])
                           if witness_uses_trace else witness(s, ns, step))
                if reached:
                    witness_trace = trace(s) + [step]
            if danger and danger_trace is None:
                reached = (danger(s, ns, step, lambda: trace(s) + [step])
                           if danger_uses_trace else danger(s, ns, step))
                if reached:
                    danger_trace = trace(s) + [step]
            if effects is not None and step.operation == "pressure_publish" and step.thread == "T":
                t = next(t for t in ns.txns if t.id == "T")
                if t.phase == "ops" and t.pc < len(t.ops) and t.ops[t.pc] == ("WAIT", ""):
                    control = _put_txn(ns, replace(t, gc_floor=t.pressure_base_floor))
                    old, new = effect_snapshot(control), effect_snapshot(ns)
                    delta_B, delta_freed = new["B"] - old["B"], new["freed"] - old["freed"]
                    best = effects["attributable"]
                    if best is None or (delta_B, delta_freed) > (best["delta_B"], best["delta_freed"]):
                        effects["attributable"] = {"delta_B": delta_B, "delta_freed": delta_freed,
                                                   "before": old, "after": new, "steps": trace(s) + [step]}
            if effects is not None and pressure == "helper" and step.thread == "H" and step.operation in ("h_publish", "h_expire") and step.version == "T":
                old_t = next(t for t in s.txns if t.id == "T")
                new_t = next(t for t in ns.txns if t.id == "T")
                if step.operation == "h_publish":
                    control = _put_txn(ns, replace(new_t, gc_floor=old_t.gc_floor))
                else:
                    control = _put_txn(ns, replace(new_t, expired=False))
                old, new = effect_snapshot(control), effect_snapshot(ns)
                row = {"delta_B": new["B"] - old["B"], "delta_freed": new["freed"] - old["freed"],
                       "delta_reclaimed": new["reclaimed"] - old["reclaimed"],
                       "delta_reclaimable": new["reclaimable"] - old["reclaimable"],
                       "before": old, "after": new, "steps": trace(s) + [step]}
                best = effects["attributable"]
                if best is None or (row["delta_B"], row["delta_freed"]) > (best["delta_B"], best["delta_freed"]):
                    effects["attributable"] = row
            if ns in parent:
                continue
            parent[ns] = (s, step)
            queue.append(ns)
            if max_states and len(parent) >= max_states:
                queue.clear()
                break
    if effects is not None and effects["max_B"] is not None and effects["max_freed"] is not None:
        mb, mf = effects["max_B"]["value"], effects["max_freed"]["value"]
        for state in parent:
            t = next((x for x in state.txns if x.id == "T" and x.phase == "ops" and x.pc < len(x.ops)
                      and x.ops[x.pc] == ("WAIT", "")), None)
            if t is not None:
                snap = effect_snapshot(state)
                if snap["B"] == mb and snap["freed"] == mf:
                    effects["simultaneous"] = {"snapshot": snap, "steps": trace(state)}
                    break
    return {"statistics": {"visited": len(parent), "terminal": terminals, "deadlock": deadlocks,
                           "floor_lowering_transitions": floor_lowering_transitions,
                           "seconds": monotonic() - began,
                           "complete": not timed_out and (not bool(max_states) or len(parent) < max_states)},
            "verdicts": verdicts, "counterexample": counterexample,
            "violation_kinds": {k: sorted(v) for k, v in violation_kinds.items()},
            "witness": {"reached": witness_trace is not None, "steps": witness_trace or []},
            "danger": {"reached": danger_trace is not None, "steps": danger_trace or []},
            "effects": effects, "fault_step_seen": fault_step_seen,
            "floor_above_cand_states": floor_above_cand_states}


def aborted_after_fault(initial: State, fault: str, o1: bool = False,
                        pressure: str = "off", revert_after_confirm=False, resume="accept") -> list[Step] | None:
    """Find a fault step followed by that transaction's failed commit validation."""
    queue = deque([(initial, "", False, [])])
    seen = {(initial, "", False)}
    while queue:
        state, actor, failed_validation, trace = queue.popleft()
        for next_state, step in enabled_steps(state, "v1", frozenset((fault,)), o1, pressure, revert_after_confirm, resume):
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
