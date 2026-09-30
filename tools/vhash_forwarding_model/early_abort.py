"""Finite Cicada version-chain model for the early-abort predicate.

Each edge is one read, install, decision, validation, forward, GC cut, or
reuse. A successful forward assumes W*: its two visibility checks and rts
publication prevent an older writer from subsequently committing.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from time import monotonic


PENDING, COMMITTED, DELETED, ABORTED = "pending", "committed", "deleted", "aborted"
FINAL = (COMMITTED, DELETED)


def stamp(clock: int, thread: int) -> int:
    return clock * 256 + thread


@dataclass(frozen=True)
class Version:
    id: str                 # physical pointer; reuse retains this id
    key: str
    wts: int
    owner: str
    status: str
    rts: int = 0
    reclaimed: bool = False
    reused: bool = False


@dataclass(frozen=True)
class Read:
    key: str
    version: str
    wts: int
    later: str = ""


@dataclass(frozen=True)
class Tx:
    id: str
    ts: int
    start_floor: int
    floor: int
    kind: str               # reader, writer, or readonly
    phase: str = "start"
    reads: tuple[Read, ...] = ()
    writes: tuple[str, ...] = ()
    forwarded: bool = False
    doomed: bool = False


@dataclass(frozen=True)
class State:
    versions: tuple[Version, ...]
    chains: tuple[tuple[str, tuple[str, ...]], ...]
    txs: tuple[Tx, ...]


@dataclass(frozen=True)
class Edge:
    label: str
    wstar: bool = False


def initial(writers: int = 1, *, readonly: bool = False) -> State:
    assert writers in (1, 2)
    starts = [stamp(50, 2), stamp(30, 3)]
    if writers == 2:
        starts.append(stamp(40, 4))
    floor = min(starts) - 1  # MinWts - 1 at transaction start
    txs = [Tx("R", starts[0], floor, floor, "readonly" if readonly else "reader")]
    txs.append(Tx("W1", starts[1], floor, floor, "writer"))
    if writers == 2:
        txs.append(Tx("W2", starts[2], floor, floor, "writer"))
    return State((Version("a0", "A", stamp(10, 0), "initial:a0", COMMITTED),
                  Version("b0", "B", stamp(10, 1), "initial:b0", COMMITTED)),
                 (("A", ("a0",)), ("B", ("b0",))), tuple(txs))


def _v(s: State, vid: str) -> Version:
    return next(v for v in s.versions if v.id == vid)


def _chain(s: State, key: str) -> tuple[str, ...]:
    return dict(s.chains)[key]


def _set_tx(s: State, tx: Tx) -> State:
    return replace(s, txs=tuple(tx if t.id == tx.id else t for t in s.txs))


def _set_version(s: State, version: Version) -> State:
    return replace(s, versions=tuple(version if v.id == version.id else v for v in s.versions))


def _set_chain(s: State, key: str, chain: tuple[str, ...]) -> State:
    return replace(s, chains=tuple((k, chain if k == key else ids) for k, ids in s.chains))


def check_timestamps(s: State) -> None:
    """The low thread bits give distinct owners distinct timestamps."""
    owners: dict[int, str] = {}
    threads = {"initial:a0": 0, "initial:b0": 1, "R": 2,
               "W1": 3, "W2": 4, "X": 4, "reuse": 5}
    for t in s.txs:
        for ts in (t.ts,):
            old = owners.setdefault(ts, t.id)
            if old != t.id:
                raise ValueError(f"timestamp collision at {ts}: {old}, {t.id}")
            assert ts % 256 == threads[t.id]
    for v in s.versions:
        if v.reclaimed:
            continue
        assert v.wts % 256 == threads[v.owner]
        old = owners.setdefault(v.wts, v.owner)
        if old != v.owner:
            raise ValueError(f"timestamp collision at {v.wts}: {old}, {v.owner}")
    for key, ids in s.chains:
        assert all(_v(s, vid).key == key and not _v(s, vid).reclaimed for vid in ids)
        assert all(_v(s, a).wts > _v(s, b).wts for a, b in zip(ids, ids[1:]))


def _read_candidate(s: State, tx: Tx, key: str) -> tuple[str, str] | None:
    """read_internal: skip >ts while saving later, wait on pending, skip aborts."""
    later = ""
    for vid in _chain(s, key):
        version = _v(s, vid)
        if version.wts > tx.ts:
            later = vid
            continue
        if version.status == PENDING:
            return None
        if version.status in FINAL:
            return (vid, later) if version.status == COMMITTED else None
    return None


def detect_d(s: State, txid: str = "R", *, mutation: str = "normal") -> bool:
    """D scans latest to the saved pointer; an unreachable pointer is unknown."""
    if mutation not in ("normal", "pending", "self"):
        raise ValueError(mutation)
    tx = next(t for t in s.txs if t.id == txid)
    if tx.kind == "readonly" or not tx.reads:
        return False
    for read in tx.reads:
        seen: list[Version] = []
        for vid in _chain(s, read.key):
            version = _v(s, vid)
            seen.append(version)
            if vid == read.version:
                allowed = FINAL + ((PENDING,) if mutation == "pending" else ())
                end = len(seen) if mutation == "self" else len(seen) - 1
                if any(v.status in allowed and
                       (read.wts <= v.wts if mutation == "self" else read.wts < v.wts)
                       and v.wts < tx.ts for v in seen[:end]):
                    return True
                break
        # Falling off the chain is deliberately not a witness.
    return False


def validation_reads(s: State, txid: str = "R") -> bool | None:
    """Independent translation of transaction.cc:543-568; None means wait.

    Unlike D, this starts at saved later_ver_ when present, skips wts >= ts,
    waits for pending resolution, and compares the first final pointer.
    """
    tx = next(t for t in s.txs if t.id == txid)
    for read in tx.reads:
        chain = _chain(s, read.key)
        if read.later:
            if read.later not in chain:
                return False
            chain = chain[chain.index(read.later):]
        selected = None
        for vid in chain:
            version = _v(s, vid)
            if version.wts >= tx.ts:
                continue
            if version.status == PENDING:
                return None
            if version.status in FINAL:
                selected = vid
                break
        if selected != read.version:
            return False
    return True


def _insert(s: State, version: Version) -> State:
    chain = list(_chain(s, version.key))
    at = next((i for i, vid in enumerate(chain) if _v(s, vid).wts < version.wts), len(chain))
    chain.insert(at, version.id)
    return _set_chain(replace(s, versions=s.versions + (version,)), version.key, tuple(chain))


def _writer_may_commit(s: State, tx: Tx) -> bool:
    # W*: the writer's validation of its predecessor's read timestamp.
    chain = _chain(s, "A")
    pos = chain.index(tx.writes[0])
    for vid in chain[pos + 1:]:
        v = _v(s, vid)
        if v.status in FINAL:
            return v.rts <= tx.ts
        if v.status == PENDING:
            return False
    return False


def transitions(s: State, *, writer_outcomes: tuple[str, ...] | None = None) -> list[tuple[State, Edge]]:
    out: list[tuple[State, Edge]] = []
    for tx in s.txs:
        if tx.phase == "done":
            continue
        if tx.kind in ("reader", "readonly"):
            if tx.phase == "start":
                selected = _read_candidate(s, tx, "A")
                if selected:
                    vid, later = selected
                    v = _v(s, vid)
                    read = Read("A", vid, v.wts, later)
                    out.append((_set_tx(s, replace(tx, phase="read", reads=(read,))),
                                Edge(f"R.read_A={vid}")))
            elif tx.phase == "read":
                if not tx.forwarded:
                    target = stamp(70, 2)
                    candidate = _set_tx(s, replace(tx, ts=target, reads=tuple(
                        replace(r, later="") for r in tx.reads)))
                    if validation_reads(candidate, tx.id) is True:
                        ns = candidate
                        for read in tx.reads:
                            v = _v(ns, read.version)
                            ns = _set_version(ns, replace(v, rts=max(v.rts, target)))
                        forward_tx = replace(next(t for t in ns.txs if t.id == tx.id),
                                             floor=max(tx.floor, target - 1), forwarded=True)
                        out.append((_set_tx(ns, forward_tx), Edge("R.forward_70_publish_69", True)))
                if tx.kind == "readonly":
                    out.append((_set_tx(s, replace(tx, phase="validate")), Edge("R.begin_validation")))
                else:
                    v = Version("rb", "B", tx.ts, tx.id, PENDING)
                    ns = _insert(s, v)
                    out.append((_set_tx(ns, replace(tx, phase="validate", writes=("rb",))),
                                Edge("R.install_B=pending")))
            elif tx.phase == "validate":
                result = validation_reads(s, tx.id)
                if result is not None:
                    status = COMMITTED if result else ABORTED
                    ns = s
                    for vid in tx.writes:
                        ns = _set_version(ns, replace(_v(ns, vid), status=status))
                    out.append((_set_tx(ns, replace(tx, phase="done", floor=10**9)),
                                Edge(f"R.validation_read={'pass' if result else 'fail'}")))
        elif tx.phase == "start":
            vid = tx.id.lower()
            v = Version(vid, "A", tx.ts, tx.id, PENDING)
            ns = _insert(s, v)
            out.append((_set_tx(ns, replace(tx, phase="pending", writes=(vid,))),
                        Edge(f"{tx.id}.install_A=pending")))
        elif tx.phase == "pending":
            outcomes = writer_outcomes or (COMMITTED, DELETED, ABORTED)
            for status in outcomes:
                if status in FINAL and not _writer_may_commit(s, tx):
                    continue
                ns = _set_version(s, replace(_v(s, tx.writes[0]), status=status))
                out.append((_set_tx(ns, replace(tx, phase="done", floor=10**9)),
                            Edge(f"{tx.id}.{status}")))

    floor = min((t.floor for t in s.txs if t.phase != "done"), default=10**9)
    for key, chain in s.chains:
        for i, vid in enumerate(chain[:-1]):
            v = _v(s, vid)
            if v.status not in FINAL or v.wts >= floor:
                continue
            detached = chain[i + 1:]
            ns = _set_chain(s, key, chain[:i + 1])
            for old in detached:
                ns = _set_version(ns, replace(_v(ns, old), reclaimed=True))
            out.append((ns, Edge(f"GC.cut_{key}_after={vid}")))
    # A detached physical slot is reused once with a fresh timestamp.
    for v in s.versions:
        if v.reclaimed and not v.reused:
            new = replace(v, key="A", wts=stamp(80, 5), owner="reuse", status=COMMITTED,
                          rts=0, reclaimed=False, reused=True)
            if any(x.wts == new.wts and not x.reclaimed for x in s.versions):
                continue
            ns = _set_version(s, new)
            chain = _chain(ns, "A")
            ns = _set_chain(ns, "A", (v.id,) + chain)
            out.append((ns, Edge(f"GC.reuse_{v.id}_as_A80")))
    return out


def replay(labels: tuple[str, ...], *, writers: int = 1, readonly: bool = False,
           writer_outcomes: tuple[str, ...] | None = None) -> State:
    state = initial(writers, readonly=readonly)
    for label in labels:
        matches = [n for n, edge in transitions(state, writer_outcomes=writer_outcomes)
                   if edge.label == label]
        if len(matches) != 1:
            raise ValueError(f"unavailable or ambiguous step {label}")
        state = matches[0]
        check_timestamps(state)
    return state


def explore(*, writers: int = 1, mutation: str = "normal", max_states: int = 100_000,
            writer_outcomes: tuple[str, ...] | None = None) -> dict:
    """BFS checks every reachable state after D, returning shortest violation."""
    start = monotonic()
    root = initial(writers)
    queue = deque([root])
    paths = {root: ()}
    edges = wstar_edges = d_states = cuts = reuses = 0
    while queue:
        state = queue.popleft()
        path = paths[state]
        reader = state.txs[0]
        if reader.doomed and reader.phase != "done":
            d_states += 1
        for next_state, edge in transitions(state, writer_outcomes=writer_outcomes):
            edges += 1
            if edge.wstar:
                wstar_edges += 1
            cuts += edge.label.startswith("GC.cut")
            reuses += edge.label.startswith("GC.reuse")
            if reader.doomed and edge.label == "R.validation_read=pass":
                return dict(sound=False, complete=False, states=len(paths), transitions=edges,
                            wstar_transitions=wstar_edges, d_states=d_states, cuts=cuts,
                            reuses=reuses, seconds=monotonic() - start,
                            counterexample=path + (edge.label,))
            next_reader = next_state.txs[0]
            if next_reader.phase != "done" and detect_d(next_state, mutation=mutation):
                next_state = _set_tx(next_state, replace(next_reader, doomed=True))
            check_timestamps(next_state)
            if next_state not in paths:
                paths[next_state] = path + (edge.label,)
                if len(paths) >= max_states:
                    return dict(sound=True, complete=False, states=len(paths), transitions=edges,
                                wstar_transitions=wstar_edges, d_states=d_states, cuts=cuts,
                                reuses=reuses, seconds=monotonic() - start, counterexample=None)
                queue.append(next_state)
    return dict(sound=True, complete=True, states=len(paths), transitions=edges,
                wstar_transitions=wstar_edges, d_states=d_states, cuts=cuts,
                reuses=reuses, seconds=monotonic() - start, counterexample=None)
