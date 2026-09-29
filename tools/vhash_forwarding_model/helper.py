"""One helper thread's local snapshot and atomic descriptor transitions."""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class HelperState:
    phase: str = "idle"
    txn: str = ""
    gen: int = 0
    target: int = 0
    reads: tuple[tuple[str, str], ...] = ()
    index: int = 0
    failed: bool = False
    refs: tuple[str, ...] = ()


def waiting(t):
    return (t.phase == "ops" and t.pc < len(t.ops) and t.ops[t.pc] == ("WAIT", "")
            and not t.fixed and not t.pending and not t.expired)


def helper_steps(s, faults, resume="accept"):
    from .model import Step, _put_txn, _put_version, _version, visible
    from .gc_connection import pressure_targets

    h = s.helper
    if resume == "expire":
        for candidate in s.txns:
            if waiting(candidate):
                yield _put_txn(s, replace(candidate, expired=True, gen=candidate.gen + 1,
                                          held_refs=candidate.refs if "UH3X" in faults else candidate.held_refs,
                                          refs=() if "UH3X" in faults else candidate.refs)), Step(
                                              "H", "h_expire", candidate.id,
                                              "UH3X" if "UH3X" in faults and candidate.refs else "")
    if h.phase == "idle":
        for t in s.txns:
            if not waiting(t):
                continue
            for target in pressure_targets(s, t):
                if target in t.tried_targets:
                    continue
                nh = HelperState("rts", t.id, t.gen, target, t.read_log,
                                 refs=() if "UH6" in faults else tuple(dict.fromkeys(
                                     vid for _, vid in t.read_log)))
                ns = _put_txn(s, replace(t, tried_targets=t.tried_targets + (target,)))
                ns = replace(ns, helper=nh)
                if "UH2" in faults and target > t.gc_floor:
                    ns = _put_txn(ns, replace(next(x for x in ns.txns if x.id == t.id),
                                              gc_floor=target))
                yield ns, Step("H", "h_snapshot", f"{t.id}:{target}",
                               "UH2" if "UH2" in faults and target > t.gc_floor else
                               "UH6" if "UH6" in faults and t.read_log else "")
        return
    t = next(x for x in s.txns if x.id == h.txn)
    if h.phase in ("rts", "check"):
        if h.index == len(h.reads):
            phase = "check" if h.phase == "rts" else "commit"
            yield replace(s, helper=replace(h, phase=phase, index=0)), Step("H", "h_pass")
            return
        vid = h.reads[h.index][1]
        v = _version(s, vid)
        if v.reclaimed:
            yield s, Step("H", "touch_reclaimed", vid)
            return
        if h.phase == "rts":
            ns = _put_version(s, replace(v, rts=max(v.rts, h.target)))
            yield replace(ns, helper=replace(h, index=h.index + 1)), Step("H", "h_rts", vid)
        else:
            selected = visible(s, v.key, h.target)
            if selected and selected.reclaimed:
                yield s, Step("H", "touch_reclaimed", selected.id)
                return
            ok = bool(selected and selected.id == vid and not selected.reclaimed and not v.reclaimed)
            yield replace(s, helper=replace(h, index=h.index + 1, failed=h.failed or not ok)), Step(
                "H", "h_check", vid)
        return
    if h.phase == "commit":
        cas = ("UH1" in faults or (waiting(t) and ("UH1g" in faults or t.gen == h.gen)))
        if h.failed or not cas:
            yield replace(s, helper=HelperState()), Step("H", "h_commit_fail", t.id)
            return
        nt = replace(t, cand_ts=h.target, gen=t.gen + 1, helper_base=t.cand_ts,
                     confirmed=t.confirmed + tuple((vid, h.target) for _, vid in h.reads))
        ns = _put_txn(s, nt)
        changed = "UH1" in faults and not (waiting(t) and t.gen == h.gen)
        yield replace(ns, helper=replace(h, phase="publish", gen=nt.gen)), Step(
            "H", "h_commit", t.id, "UH1" if changed else "")
        return
    if h.phase == "publish":
        sound_cas = waiting(t) and t.gen == h.gen
        cas = ("UH1" in faults or "UH1p" in faults or
               (waiting(t) and ("UH1g" in faults or t.gen == h.gen)))
        if cas:
            published = h.target if "UH1p" in faults or "UH1" in faults else t.cand_ts
            nt = replace(t, gc_floor=max(t.gc_floor, published),
                         held_refs=t.refs if "UH3F" in faults else t.held_refs,
                         refs=() if "UH3F" in faults else t.refs)
            ns = _put_txn(s, nt)
            fault = (next((f for f in ("UH1", "UH1p") if f in faults), "")
                     if not sound_cas or published != t.cand_ts else
                     "UH3F" if "UH3F" in faults and t.refs else "")
            yield replace(ns, helper=HelperState()), Step("H", "h_publish", t.id, fault)
        else:
            yield replace(s, helper=HelperState()), Step("H", "h_publish_fail", t.id)
