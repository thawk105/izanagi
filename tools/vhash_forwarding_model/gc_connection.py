"""Pure calculations for pressure candidates and logical GC effects."""
from __future__ import annotations


def pressure_targets(state, txn):
    from .model import _next_free
    return tuple(sorted({_next_free(state, v.wts + 1) for v in state.versions
                         if v.status == "COMMITTED" and v.wts > txn.cand_ts}))


def reclaimable_versions(state):
    active = [t for t in state.txns if t.phase != "done" and not t.expired]
    boundary = min((t.gc_floor for t in active),
                   default=max((v.wts for v in state.versions), default=0) + 1)
    refs = {vid for t in state.txns for vid in t.refs} | set(state.helper.refs)
    return tuple(v.id for v in state.versions
                 if not v.reclaimed and v.status != "PENDING" and v.id not in refs
                 and (v.status == "ABORTED" or any(
                     x.key == v.key and x.status == "COMMITTED"
                     and v.wts < x.wts <= boundary for x in state.versions)))


def effect_snapshot(state):
    active = [t for t in state.txns if t.phase != "done" and not t.expired]
    boundary = min((t.gc_floor for t in active),
                   default=max((v.wts for v in state.versions), default=0) + 1)
    reclaimed = sum(v.reclaimed for v in state.versions)
    reclaimable = len(reclaimable_versions(state))
    return {"B": boundary, "reclaimed": reclaimed, "reclaimable": reclaimable,
            "freed": reclaimed + reclaimable}
