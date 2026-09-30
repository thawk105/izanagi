"""Bounded SC model of Cicada read-only publication and version GC.

Progress means a publication that changes MinRts while a long read-only
procedure is active; the number of publications is a separate observation.
The model covers point reads, no deletes and group_commit=0. bad-clear-slot
is a positive counterexample obtained by adding an infinity slot store to the
safe-flag arm. Shared loads and stores are distinct steps.

The bad-raise-slot witness also needs early flag stores to trigger publication.
That prefix is outside stock's read-only transition path; this arm does not
establish a stock-reachable slot-raise-only counterexample.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path

ARMS = ("stock", "safe-flag", "safe-mainte", "neg-early-flag",
        "bad-raise-slot", "bad-clear-slot")
INF = 10**6
SERIALIZABILITY = "not modeled (checked by the trace verifier on the C++ build)"
PROGRESS = "MinRts value changed during an active long read-only procedure; not publication count"


@dataclass(frozen=True)
class Config:
    workers: int = 2
    keys: int = 1
    reads: int = 1

    def __post_init__(self):
        if self.workers not in (2, 3) or self.keys not in (1, 2) or self.reads not in (1, 2):
            raise ValueError(self)

    @property
    def name(self):
        return f"w{self.workers}-k{self.keys}-r{self.reads}"


CONFIGS = (Config(2, 1, 1), Config(2, 1, 2), Config(2, 2, 1),
           Config(2, 2, 2), Config(3, 1, 1))


@dataclass(frozen=True)
class State:
    phase: str = "begin_w"
    procedure: int = 0
    read_index: int = 0
    r_wts: int = 20
    r_rts: int = 9
    r_slot: int = 9
    u_wts: int = 20
    u_slot: int = 19
    min_wts: int = 20
    min_rts: int = 9
    flags: tuple[int, ...] = (0, 0)
    execute: tuple[int, ...] = (0, 0)
    leader: int = 0
    scan_w: int = INF
    scan_r: int = INF
    u_write: int = 0
    u_calls: int = 0
    u_phase: str = "write_wts"
    r_maint: str = "idle"
    u_boundary: int = 0
    r_boundary: int = 0
    held: tuple[str, ...] = ()
    reclaimed: bool = False
    raised: bool = False
    early: bool = False
    publications: int = 0
    progress: bool = False
    x_phase: str = "write_wts"
    x_wts: int = 20
    x_slot: int = 19
    x_write: bool = False
    x_calls: int = 0
    x_boundary: int = 0


@dataclass(frozen=True)
class Event:
    actor: str
    operation: str
    value: int | str | None = None

    def label(self):
        return f"{self.actor}.{self.operation}" + (f"={self.value}" if self.value is not None else "")


def _put(pair, index, value):
    return pair[:index] + (value,) + pair[index + 1:]


def initial_state(config: Config = Config()):
    n = config.workers
    return State(flags=(0,) * n, execute=(0,) * n)


def _versions(s, key):
    if key == "B":
        return ((11, "B11"),) + ((50, "B50"),) * s.x_write
    return ((10, "A10"),) + ((30, "A30"),) * (s.u_write >= 1) + ((40, "A40"),) * (s.u_write >= 2)


def _selected(s, key, ts):
    return max((row for row in _versions(s, key) if row[0] <= ts), default=_versions(s, key)[0])[1]


def needed_versions(s, config=Config()):
    """Independent oracle: choose versions from the live reader's own rts.

    This never uses the GC boundary, cached scan result, or GC cut condition.
    """
    needed = set(s.held)
    if s.phase == "read":
        for key in ("A", "B")[:config.keys]:
            needed.add(_selected(s, key, s.r_rts))
    return needed


def gc_violation(before, after, event, config=Config()):
    if event.operation != "cut_A10" or before.reclaimed:
        return None
    if "A10" in needed_versions(before, config):
        return {"version": "A10", "reason": "held_pointer" if "A10" in before.held else "future_read",
                "reader_rts": before.r_rts}
    return None


def _maintenance(s, who):
    is_r = who == "R"
    is_x = who == "X"
    phase = s.r_maint if is_r else s.x_phase if is_x else s.u_phase
    calls = s.x_calls if is_x else s.u_calls
    if not is_r and (calls >= 3 or phase.startswith("write")):
        return
    if phase == "idle":
        return
    field = "r_maint" if is_r else "x_phase" if is_x else "u_phase"
    bound = "r_boundary" if is_r else "x_boundary" if is_x else "u_boundary"
    idx = 0 if is_r else 2 if is_x else 1

    def change(next_phase, **kw):
        return replace(s, **{field: next_phase, **kw})

    if phase == "start":
        yield change("exec_check"), Event(who, "mainte_start")
    elif phase == "exec_check":
        yield change("boundary" if s.execute[idx] else "timer_check"), Event(who, "load_execute", s.execute[idx])
    elif phase == "boundary":
        yield change("cut", **{bound: s.min_rts}), Event(who, "load_MinRts", s.min_rts)
    elif phase == "cut":
        floor = getattr(s, bound)
        if s.u_write >= 2 and floor > 30 and not s.reclaimed:
            yield change("exec_reset", reclaimed=True), Event(who, "cut_A10", floor)
        else:
            yield change("exec_reset"), Event(who, "gc_no_cut", floor)
    elif phase == "exec_reset":
        yield change("timer_check", execute=_put(s.execute, idx, 0)), Event(who, "store_execute", 0)
    elif phase == "timer_check":
        yield change("flag_check"), Event(who, "timer_elapsed")
    elif phase == "flag_check":
        yield change("flag_store" if not s.flags[idx] else "finish"), Event(who, "load_flag", s.flags[idx])
    elif phase == "flag_store":
        yield change("finish", flags=_put(s.flags, idx, 1)), Event(who, "store_flag", 1)
    elif phase == "finish":
        if is_r:
            yield change("idle", phase="begin_w" if s.procedure == 1 else "done"), Event(who, "mainte_done")
        elif is_x:
            yield change("start", x_calls=s.x_calls + 1), Event(who, "mainte_done")
        else:
            yield change("start", u_calls=s.u_calls + 1), Event(who, "mainte_done")


def transitions(s, arm, config=Config()):
    """Each yielded transition performs at most one shared memory operation."""
    p = s.phase
    if p == "begin_w":
        yield replace(s, r_wts=50 if s.procedure == 0 else 60, phase="begin_load"), Event("R", "store_wts_slot", 50 if s.procedure == 0 else 60)
    elif p == "begin_load":
        yield replace(s, r_rts=s.min_wts - 1, phase="begin_r"), Event("R", "load_MinWts", s.min_wts)
    elif p == "begin_r":
        yield replace(s, r_slot=s.r_rts, phase="read", read_index=0, held=()), Event("R", "store_rts_slot", s.r_rts)
    elif p == "read":
        for key in ("A", "B")[:config.keys]:
            version = _selected(s, key, s.r_rts)
            last = s.read_index + 1 == config.reads
            yield replace(s, held=s.held + (version,), read_index=s.read_index + 1,
                          phase="hold" if last else "read"), Event("R", f"read_{key}", version)
    elif p == "hold":
        if arm == "bad-raise-slot" and not s.early and s.procedure == 0:
            yield replace(s, flags=_put(s.flags, 0, 1), early=True), Event("R", "early_store_flag", 1)
        if arm == "bad-raise-slot" and not s.raised and s.procedure == 0 and s.min_wts > s.r_rts + 1:
            yield replace(s, r_slot=s.min_wts - 1, raised=True), Event("R", "raise_rts_slot", s.min_wts - 1)
        if arm == "bad-raise-slot" and s.raised and s.flags[0] == 0:
            yield replace(s, flags=_put(s.flags, 0, 1), early=True), Event("R", "early_store_flag", 1)
        if arm == "neg-early-flag" and not s.early and s.procedure == 0:
            yield replace(s, flags=_put(s.flags, 0, 1), early=True), Event("R", "early_store_flag", 1)
        yield replace(s, held=(), phase="clear_slot" if arm == "bad-clear-slot" and s.procedure == 0 else "ro_commit"), Event("R", "clear_refs")
    elif p == "clear_slot":
        yield replace(s, r_slot=INF, phase="ro_commit"), Event("R", "store_rts_slot", INF)
    elif p == "ro_commit":
        count = s.procedure + 1
        if arm == "safe-mainte":
            yield replace(s, procedure=count, phase="maint_wait", r_maint="exec_check"), Event("R", "mainte_start")
        elif arm != "stock":
            yield replace(s, procedure=count, flags=_put(s.flags, 0, 1),
                          phase="begin_w" if count == 1 else "done"), Event("R", "store_flag", 1)
        else:
            yield replace(s, procedure=count, phase="begin_w" if count == 1 else "done"), Event("R", "ro_commit")

    # Update worker creates three versions of A, including the initial A10.
    if s.u_phase == "write_wts":
        v = 30 if s.u_write == 0 else 40
        yield replace(s, u_wts=v, u_phase="write_slot"), Event("U", "store_wts_slot", v)
    elif s.u_phase == "write_slot":
        yield replace(s, u_slot=s.u_wts - 1, u_phase="write_version"), Event("U", "store_rts_slot", s.u_wts - 1)
    elif s.u_phase == "write_version":
        count = s.u_write + 1
        yield replace(s, u_write=count, u_phase="write_wts" if count < 2 else "start"), Event("U", "commit_A", s.u_wts)
    else:
        yield from _maintenance(s, "U")

    if config.workers == 3:
        if s.x_phase == "write_wts":
            yield replace(s, x_wts=50, x_phase="write_slot"), Event("X", "store_wts_slot", 50)
        elif s.x_phase == "write_slot":
            yield replace(s, x_slot=49, x_phase="write_version"), Event("X", "store_rts_slot", 49)
        elif s.x_phase == "write_version":
            yield replace(s, x_write=True, x_phase="start"), Event("X", "commit_B", 50)
        else:
            yield from _maintenance(s, "X")
    if s.r_maint != "idle":
        yield from _maintenance(s, "R")

    # The leader scans each flag, then each worker's Wts and Rts slots.
    n = config.workers
    l = s.leader
    if l < n:
        flag = s.flags[l]
        yield replace(s, leader=l + 1 if flag else 0), Event("L", f"load_flag{l}", flag)
    elif l < n + 2 * n:
        i = (l - n) // 2
        w = (s.r_wts, s.u_wts, s.x_wts)[i]
        r = (s.r_slot, s.u_slot, s.x_slot)[i]
        if (l - n) % 2 == 0:
            yield replace(s, scan_w=min(s.scan_w, w), leader=l + 1), Event("L", f"load_wts{i}", w)
        else:
            yield replace(s, scan_r=min(s.scan_r, r), leader=l + 1), Event("L", f"load_rts{i}", r)
    elif l == 3 * n:
        yield replace(s, min_wts=s.scan_w, leader=l + 1), Event("L", "store_MinWts", s.scan_w)
    elif l == 3 * n + 1:
        active = s.phase in ("read", "hold")
        yield replace(s, min_rts=s.scan_r, leader=l + 1,
                      progress=s.progress or (active and s.scan_r != s.min_rts),
                      publications=s.publications + 1), Event("L", "store_MinRts", s.scan_r)
    else:
        i = (l - (3 * n + 2)) // 2
        if (l - (3 * n + 2)) % 2 == 0:
            yield replace(s, flags=_put(s.flags, i, 0), leader=l + 1), Event("L", f"reset_flag{i}", 0)
        else:
            last = i == n - 1
            yield replace(s, execute=_put(s.execute, i, 1), leader=0 if last else l + 1,
                          scan_w=INF if last else s.scan_w, scan_r=INF if last else s.scan_r), Event("L", f"store_execute{i}", 1)


def explore(arm, *, config=Config(), max_states=200_000):
    if arm not in ARMS:
        raise ValueError(arm)
    initial = initial_state(config)
    queue = deque([initial])
    paths = {initial: ()}
    violations = cuts = no_cuts = loads = publications = 0
    witness = progress_witness = cut_witness = None
    complete = True
    while queue:
        state = queue.popleft()
        path = paths[state]
        for after, event in transitions(state, arm, config):
            label = event.label()
            if event.operation == "load_MinRts":
                loads += 1
            if event.operation == "cut_A10":
                cuts += 1
                if cut_witness is None:
                    cut_witness = list(path + (label,))
            if event.operation == "gc_no_cut":
                no_cuts += 1
            if event.operation == "store_MinRts":
                publications += 1
            violation = gc_violation(state, after, event, config)
            if violation:
                violations += 1
                if witness is None:
                    witness = {"steps": list(path + (label,)), "reason": violation}
            if after.progress and progress_witness is None:
                progress_witness = list(path + (label,))
            if after not in paths:
                if len(paths) >= max_states:
                    complete = False
                    queue.clear()
                    break
                paths[after] = path + (label,)
                queue.append(after)
    return {"arm": arm, "config": config.name, "workers": config.workers,
            "keys": config.keys, "reads": config.reads, "states": len(paths),
            "complete": complete, "gc_violations": violations, "gc_witness": witness,
            "boundary_loads": loads, "cuts": cuts, "no_cuts": no_cuts,
            "cut_witness": cut_witness, "publications": publications,
            "progress": progress_witness is not None, "progress_witness": progress_witness,
            "progress_meaning": PROGRESS, "serializability": SERIALIZABILITY,
            "bad_raise_requires_extra_flag": arm == "bad-raise-slot"}


def replay(arm, labels, config=Config()):
    state = initial_state(config)
    for label in labels:
        matches = [next_state for next_state, event in transitions(state, arm, config) if event.label() == label]
        if len(matches) != 1:
            raise ValueError((label, len(matches)))
        state = matches[0]
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-states", type=int, default=200_000)
    parser.add_argument("--arm", choices=ARMS, action="append")
    args = parser.parse_args(argv)
    if args.max_states < 1:
        parser.error("--max-states must be positive")
    results = {config.name: {arm: explore(arm, config=config, max_states=args.max_states)
                             for arm in (args.arm or ARMS)} for config in CONFIGS}
    args.out.write_text(json.dumps({"configurations": results, "serializability": SERIALIZABILITY,
                                     "progress_meaning": PROGRESS}, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return 0 if all(row["complete"] for group in results.values() for row in group.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
