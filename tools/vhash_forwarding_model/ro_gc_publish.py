"""Bounded SC model of Cicada read-only commit, flag publication and version GC.

This models point reads, no delete, group_commit=0 and two workers. Each
transition contains at most one shared load or store. Local phase changes are
steps too; timestamps are fixed representatives of their ordering classes.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

from .judge import j1

ARMS = ("stock", "safe-flag", "safe-mainte", "neg-early-flag",
        "bad-raise-slot", "bad-clear-slot")
INF = 10**6


@dataclass(frozen=True)
class State:
    # R's first procedure is at release; its second is the long read-only tx.
    phase: str = "release"
    r_count: int = 0
    r_wts: int = 20
    r_rts: int = 9
    r_slot: int = 9
    u_wts: int = 40
    u_slot: int = 39
    min_wts: int = 20
    min_rts: int = 9
    flags: tuple[int, int] = (0, 0)
    execute: tuple[int, int] = (0, 0)
    # Leader phases: flag0, flag1, w0, r0, w1, r1, storew, storer,
    # reset0, exec0, reset1, exec1.
    leader: int = 0
    scan_w: int = INF
    scan_r: int = INF
    # Update worker may call maintenance twice; each invocation is finite.
    u_calls: int = 0
    u_phase: str = "start"
    u_boundary: int = 0
    r_maint: str = "idle"
    r_boundary: int = 0
    held: tuple[str, ...] = ()
    reads: tuple[tuple[str, str], ...] = ()
    reclaimed: bool = False
    raised: bool = False
    early: bool = False
    publications: int = 0
    progress: bool = False


@dataclass(frozen=True)
class Event:
    actor: str
    operation: str
    value: int | str | None = None

    def label(self) -> str:
        return f"{self.actor}.{self.operation}" + (f"={self.value}" if self.value is not None else "")


def _put_pair(pair: tuple[int, int], index: int, value: int) -> tuple[int, int]:
    return (value, pair[1]) if index == 0 else (pair[0], value)


def _selected(s: State, key: str, ts: int) -> str:
    if key == "A":
        return "A30" if ts >= 30 else "A10"
    return "B11"


def needed_versions(s: State) -> set[str]:
    """Oracle from the immutable version history and live reader, not GC floor.

    The chain is A30 -> A10 and B11. A held pointer remains needed even
    after its read operation; a pending read selects by the tx's own rts.
    """
    needed = set(s.held)
    if s.phase in ("begin_r", "read"):
        needed.add(_selected(s, "A", s.r_rts))
    return needed


def gc_violation(before: State, after: State, event: Event) -> dict | None:
    if event.operation != "cut_A10" or not after.reclaimed:
        return None
    if "A10" in needed_versions(before):
        return {"version": "A10", "reason": "held_pointer" if "A10" in before.held
                else "future_read", "reader_rts": before.r_rts}
    return None


def j1_adapter(s: State, *, history=None):
    """Present committed Cicada point history in the existing J1 input shape."""
    if history is not None:
        versions, txns = history
        return j1(SimpleNamespace(versions=versions, txns=txns))
    versions = [SimpleNamespace(id="A10", key="A", wts=10, status="COMMITTED",
                                owner="initial"),
                SimpleNamespace(id="A30", key="A", wts=30, status="COMMITTED", owner="U"),
                SimpleNamespace(id="B11", key="B", wts=11, status="COMMITTED",
                                owner="initial")]
    txns = [SimpleNamespace(id="U", phase="done", failed=False, read_log=())]
    if s.phase == "done":
        txns.append(SimpleNamespace(id="R", phase="done", failed=False,
                                    read_log=s.reads))
    return j1(SimpleNamespace(versions=versions, txns=txns))


def _maintenance(s: State, who: str):
    """One shared operation per step in mainte(): execute, boundary, cut, reset, timer, flag."""
    is_r = who == "R"
    phase = s.r_maint if is_r else s.u_phase
    if not is_r and s.u_calls >= 2 and phase == "start":
        return
    if phase == "idle":
        return
    def change(new_phase: str, **kw):
        kw["r_maint" if is_r else "u_phase"] = new_phase
        return replace(s, **kw)
    idx = 0 if is_r else 1
    if phase == "start":
        if is_r:
            return
        yield change("exec_check"), Event(who, "mainte_start")
    elif phase == "exec_check":
        nxt = "boundary" if s.execute[idx] else "timer_check"
        yield change(nxt), Event(who, "load_execute", s.execute[idx])
    elif phase == "boundary":
        yield change("cut", **({"r_boundary": s.min_rts} if is_r else
                               {"u_boundary": s.min_rts})), Event(who, "load_MinRts", s.min_rts)
    elif phase == "cut":
        floor = s.r_boundary if is_r else s.u_boundary
        if floor > 30 and not s.reclaimed:
            yield change("exec_reset", reclaimed=True), Event(who, "cut_A10", floor)
        else:
            yield change("exec_reset"), Event(who, "gc_no_cut", floor)
    elif phase == "exec_reset":
        yield change("timer_check", execute=_put_pair(s.execute, idx, 0)), Event(who, "store_execute", 0)
    elif phase == "timer_check":
        yield change("flag_check"), Event(who, "timer_elapsed")
    elif phase == "flag_check":
        yield change("flag_store" if not s.flags[idx] else "finish"), Event(who, "load_flag", s.flags[idx])
    elif phase == "flag_store":
        yield change("finish", flags=_put_pair(s.flags, idx, 1)), Event(who, "store_flag", 1)
    elif phase == "finish":
        if is_r:
            yield change("idle", phase="begin_w" if s.r_count == 1 else "done"), Event(who, "mainte_done")
        else:
            yield change("start", u_calls=s.u_calls + 1), Event(who, "mainte_done")


def transitions(s: State, arm: str):
    """Enumerate all enabled local, shared-load and shared-store steps."""
    p = s.phase
    if p == "release":
        yield replace(s, held=(), phase="clear_slot" if arm == "bad-clear-slot" else
                      "ro_commit"), Event("R", "clear_refs")
    elif p == "clear_slot":
        yield replace(s, r_slot=INF, phase="ro_commit"), Event("R", "store_rts_slot", INF)
    elif p == "ro_commit":
        if arm in ("safe-flag", "bad-raise-slot", "bad-clear-slot", "neg-early-flag"):
            yield replace(s, flags=_put_pair(s.flags, 0, 1), r_count=1,
                          phase="begin_w"), Event("R", "store_flag", 1)
        elif arm == "safe-mainte":
            yield replace(s, r_count=1, phase="maint_wait", r_maint="exec_check"), Event("R", "mainte_start")
        else:
            yield replace(s, r_count=1, phase="begin_w"), Event("R", "ro_commit")
    elif p == "begin_w":
        yield replace(s, r_wts=50, phase="begin_load"), Event("R", "store_wts_slot", 50)
    elif p == "begin_load":
        yield replace(s, r_rts=s.min_wts - 1, phase="begin_r"), Event("R", "load_MinWts", s.min_wts)
    elif p == "begin_r":
        yield replace(s, r_slot=s.r_rts, phase="read"), Event("R", "store_rts_slot", s.r_rts)
    elif p == "read":
        version = _selected(s, "A", s.r_rts)
        yield replace(s, held=(version,), reads=(("A", version),), phase="hold"), Event("R", "read_A", version)
    elif p == "hold":
        if arm == "bad-raise-slot" and not s.raised and s.min_wts > s.r_rts + 1:
            yield replace(s, r_slot=s.min_wts - 1, raised=True), Event("R", "raise_rts_slot", s.min_wts - 1)
        if arm == "neg-early-flag" and not s.early:
            yield replace(s, flags=_put_pair(s.flags, 0, 1), early=True), Event("R", "early_store_flag", 1)
        yield replace(s, held=(), phase="done"), Event("R", "clear_refs")
    # Leader follows util.cc and cannot restart mid-scan.
    l = s.leader
    if l < 2:
        flag = s.flags[l]
        yield replace(s, leader=l + 1 if flag else 0), Event("L", f"load_flag{l}", flag)
    elif l in (2, 4):
        i = (l - 2) // 2
        v = s.r_wts if i == 0 else s.u_wts
        yield replace(s, scan_w=min(s.scan_w, v), leader=l + 1), Event("L", f"load_wts{i}", v)
    elif l in (3, 5):
        i = (l - 3) // 2
        v = s.r_slot if i == 0 else s.u_slot
        yield replace(s, scan_r=min(s.scan_r, v), leader=l + 1), Event("L", f"load_rts{i}", v)
    elif l == 6:
        yield replace(s, min_wts=s.scan_w, leader=7), Event("L", "store_MinWts", s.scan_w)
    elif l == 7:
        progress = s.progress or (s.phase in ("begin_load", "begin_r", "read", "hold")
                                  and s.scan_r != s.min_rts)
        yield replace(s, min_rts=s.scan_r, leader=8, progress=progress,
                      publications=s.publications + 1), Event("L", "store_MinRts", s.scan_r)
    elif l in (8, 10):
        i = (l - 8) // 2
        yield replace(s, flags=_put_pair(s.flags, i, 0), leader=l + 1), Event("L", f"reset_flag{i}", 0)
    else:
        i = (l - 9) // 2
        yield replace(s, execute=_put_pair(s.execute, i, 1), leader=0 if l == 11 else l + 1,
                      scan_w=INF if l == 11 else s.scan_w,
                      scan_r=INF if l == 11 else s.scan_r), Event("L", f"store_execute{i}", 1)
    yield from _maintenance(s, "U")
    if s.r_maint != "idle":
        yield from _maintenance(s, "R")


def initial_state(arm: str) -> State:
    if arm == "bad-raise-slot":
        # A bounded prefix: the long reader already holds A10 at rts 19;
        # a later publication advanced MinWts to 40. The bad intervention
        # now raises its slot while its snapshot and pointer remain old.
        return State(phase="hold", r_count=1, r_wts=50, r_rts=19, r_slot=19,
                     min_wts=40, held=("A10",), reads=(("A", "A10"),),
                     flags=(1, 0))
    return State()


def explore(arm: str, *, max_states: int = 200_000) -> dict:
    if arm not in ARMS:
        raise ValueError(arm)
    initial = initial_state(arm)
    queue = deque([initial])
    paths = {initial: ()}
    gc_witness = None
    cycle_witness = None
    progress_witness = None
    violations = 0
    cycles = 0
    complete = True
    while queue:
        state = queue.popleft()
        path = paths[state]
        for after, event in transitions(state, arm):
            label = event.label()
            violation = gc_violation(state, after, event)
            if violation:
                violations += 1
                if gc_witness is None:
                    gc_witness = {"steps": list(path + (label,)), "reason": violation}
            if after.progress and progress_witness is None:
                progress_witness = list(path + (label,))
            cycle = j1_adapter(after) if after.phase == "done" else None
            if cycle:
                cycles += 1
                if cycle_witness is None:
                    cycle_witness = {"steps": list(path + (label,)), "reason": cycle}
            if after not in paths:
                if len(paths) >= max_states:
                    complete = False
                    queue.clear()
                    break
                paths[after] = path + (label,)
                queue.append(after)
    return {"arm": arm, "states": len(paths), "complete": complete,
            "gc_violations": violations, "gc_witness": gc_witness,
            "cycles": cycles, "cycle_witness": cycle_witness,
            "progress": progress_witness is not None,
            "progress_witness": progress_witness}


def replay(arm: str, labels: list[str]) -> State:
    state = initial_state(arm)
    for label in labels:
        matches = [next_state for next_state, event in transitions(state, arm)
                   if event.label() == label]
        if len(matches) != 1:
            raise ValueError((label, len(matches)))
        state = matches[0]
    return state


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-states", type=int, default=200_000)
    parser.add_argument("--arm", choices=ARMS, action="append")
    args = parser.parse_args(argv)
    if args.max_states < 1:
        parser.error("--max-states must be positive")
    results = {arm: explore(arm, max_states=args.max_states) for arm in (args.arm or ARMS)}
    args.out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if all(row["complete"] for row in results.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
