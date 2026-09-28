"""Independent final-history and logical-GC judgments."""
from __future__ import annotations


def _committed(state):
    return {t.id: t for t in state.txns
            if t.phase in ("release", "done") and not t.failed}


def _rw_successors(versions, key, read_version):
    return (v for v in versions if v.key == key and v.wts > read_version.wts)


def _needed_future(before, t, v):
    remaining = t.ops[t.pc:]
    if not any(op == "R" and key == v.key for op, key in remaining):
        return False
    successors = [x for x in before.versions if x.key == v.key and x.status == "COMMITTED"
                  and x.wts > v.wts and x.wts <= t.cand_ts]
    return v.status == "COMMITTED" and not successors


def j1(state):
    committed = _committed(state)
    versions = [v for v in state.versions if v.status == "COMMITTED"
                and (v.owner == "initial" or v.owner in committed)]
    by_id = {v.id: v for v in versions}
    edges = {}
    def edge(a, b, kind, key, version):
        if a != b and a in committed and b in committed:
            edges.setdefault(a, []).append({"from": a, "to": b, "kind": kind,
                                               "key": key, "version": version})
    for key in {v.key for v in versions}:
        ordered = sorted((v for v in versions if v.key == key), key=lambda v: v.wts)
        for a, b in zip(ordered, ordered[1:]):
            edge(a.owner, b.owner, "ww", key, a.id)
    for t in committed.values():
        for key, vid in t.read_log:
            v = by_id.get(vid)
            if v is None:
                continue
            edge(v.owner, t.id, "wr", key, vid)
            for later in _rw_successors(versions, key, v):
                edge(t.id, later.owner, "rw", key, vid)
    def visit(node, path, seen):
        for e in edges.get(node, ()):
            if e["to"] in path:
                at = path.index(e["to"])
                return {"cycle": path[at:] + [e["to"]], "edges": seen[at:] + [e]}
            if e["to"] not in explored:
                result = visit(e["to"], path + [e["to"]], seen + [e])
                if result:
                    return result
        explored.add(node)
        return None
    explored = set()
    for node in committed:
        if node not in explored:
            result = visit(node, [node], [])
            if result:
                return result
    return None


def j2(state):
    committed = _committed(state)
    versions = [v for v in state.versions if v.status == "COMMITTED"]
    for t in committed.values():
        for key, vid in t.read_log:
            expected = max((v for v in versions if v.key == key and v.wts <= t.cand_ts
                            and v.owner != t.id), key=lambda v: v.wts, default=None)
            if expected and expected.id != vid:
                return {"txn": t.id, "key": key, "actual": vid, "expected": expected.id}
    return None


def j3(before, after, step):
    if step.operation == "touch_reclaimed":
        return {"version": step.version, "txn": step.thread, "reason": "use_after_free"}
    if step.operation != "reclaim":
        return None
    v = next(x for x in before.versions if x.id == step.version)
    for t in before.txns:
        if t.phase == "done":
            continue
        if v.id in t.refs:
            return {"version": v.id, "txn": t.id, "reason": "reference", "gc_step": step.operation}
        if v.id in (vid for _, vid in t.read_log):
            return {"version": v.id, "txn": t.id, "reason": "read_log", "gc_step": step.operation}
        if _needed_future(before, t, v):
            return {"version": v.id, "txn": t.id, "reason": "future_read",
                    "cand_ts": t.cand_ts, "gc_step": step.operation}
    return None


def judge(before, after, step, *, all_transitions=False):
    decision = all_transitions or step.operation.startswith("decide_")
    gc = all_transitions or step.operation in ("reclaim", "touch_reclaimed")
    return {"J1": j1(after) if decision else None,
            "J2": j2(after) if decision else None,
            "J3": j3(before, after, step) if gc else None}
