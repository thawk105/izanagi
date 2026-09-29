"""Cicada read-only GC publication model; runnable without pytest."""
from __future__ import annotations

import sys
import traceback
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from vhash_forwarding_model import ro_gc_publish as m  # noqa: E402

_RESULTS = {}


def _result(arm):
    if arm not in _RESULTS:
        _RESULTS[arm] = m.explore(arm, max_states=20_000)
    assert _RESULTS[arm]["complete"], (arm, _RESULTS[arm]["states"])
    return _RESULTS[arm]


def test_safe_flag_only_and_full_mainte():
    for arm in ("stock", "safe-flag", "safe-mainte", "neg-early-flag"):
        result = _result(arm)
        assert result["gc_violations"] == 0, (arm, result["gc_witness"])
        assert result["cycles"] == 0, (arm, result["cycle_witness"])
    assert not _result("stock")["progress"]
    assert _result("safe-flag")["progress"]
    assert _result("safe-mainte")["progress"]


def test_begin_interleavings_preserve_floor():
    for arm in ("stock", "safe-flag", "safe-mainte"):
        assert _result(arm)["complete"]
        assert _result(arm)["gc_witness"] is None
    s = m.State(phase="begin_load")
    after, _ = next((n, e) for n, e in m.transitions(s, "safe-flag")
                    if e.operation == "load_MinWts")
    assert after.phase == "begin_r" and after.r_rts == 19
    assert after.r_slot == s.r_slot


def test_long_ro_can_publish_without_boundary_advance():
    s = m.State(phase="hold", r_rts=19, r_slot=19, min_rts=19,
                leader=7, scan_r=19, held=("A10",))
    after, _ = next((n, e) for n, e in m.transitions(s, "safe-flag")
                    if e.operation == "store_MinRts")
    assert after.publications == 1 and not after.progress
    assert _result("safe-flag")["progress"]
    assert _result("safe-mainte")["progress"]


RAISE_WITNESS = [
    "R.raise_rts_slot=39", "L.load_flag0=1", "U.mainte_start",
    "U.load_execute=0", "U.timer_elapsed", "U.load_flag=0",
    "U.store_flag=1", "L.load_flag1=1", "L.load_wts0=50",
    "L.load_rts0=39", "L.load_wts1=40", "L.load_rts1=39",
    "L.store_MinWts=40", "L.store_MinRts=39", "L.reset_flag0=0",
    "L.store_execute0=1", "L.reset_flag1=0", "L.store_execute1=1",
    "U.mainte_done", "U.mainte_start", "U.load_execute=1",
    "U.load_MinRts=39", "U.cut_A10=39",
]
CLEAR_WITNESS = [
    "R.clear_refs", "R.store_rts_slot=1000000", "R.store_flag=1",
    "R.store_wts_slot=50", "R.load_MinWts=20", "L.load_flag0=1",
    "U.mainte_start", "U.load_execute=0", "U.timer_elapsed",
    "U.load_flag=0", "U.store_flag=1", "L.load_flag1=1",
    "L.load_wts0=50", "L.load_rts0=1000000",
    "L.load_wts1=40", "L.load_rts1=39", "L.store_MinWts=40",
    "L.store_MinRts=39", "L.reset_flag0=0", "L.store_execute0=1",
    "L.reset_flag1=0", "L.store_execute1=1", "U.mainte_done",
    "U.mainte_start", "U.load_execute=1", "U.load_MinRts=39",
    "U.cut_A10=39",
]


def _check_bad(arm, expected, reason):
    result = _result(arm)
    assert result["gc_violations"] > 0
    assert result["gc_witness"]["steps"] == expected
    assert result["gc_witness"]["reason"]["reason"] == reason
    before = m.replay(arm, expected[:-1])
    after, event = next((n, e) for n, e in m.transitions(before, arm)
                        if e.label() == expected[-1])
    assert m.gc_violation(before, after, event) == result["gc_witness"]["reason"]
    assert after.reclaimed and not before.reclaimed
    assert result["cycles"] == 0


def test_bad_raise_slot_reclaims_held_version():
    _check_bad("bad-raise-slot", RAISE_WITNESS, "held_pointer")


def test_bad_clear_slot_reclaims_future_read():
    _check_bad("bad-clear-slot", CLEAR_WITNESS, "future_read")


def test_early_flag_alone_is_not_assumed_unsafe():
    result = _result("neg-early-flag")
    assert result["gc_violations"] == 0
    assert result["cycles"] == 0
    assert result["progress"]


def test_oracle_is_independent_of_gc_boundary():
    s = m.State(phase="read", r_rts=19, min_rts=39)
    assert m.needed_versions(s) == {"A10"}
    assert m.needed_versions(replace(s, min_rts=1)) == {"A10"}
    held = replace(s, phase="hold", held=("A10",))
    assert m.needed_versions(held) == {"A10"}
    assert m.needed_versions(replace(held, r_slot=m.INF)) == {"A10"}


def test_j1_adapter_detects_cycle():
    def version(name, key, wts, owner):
        return SimpleNamespace(id=name, key=key, wts=wts,
                               owner=owner, status="COMMITTED")
    versions = (version("A10", "A", 10, "initial"),
                version("B11", "B", 11, "initial"),
                version("WA", "A", 30, "W"),
                version("TB", "B", 20, "T"))
    txns = (SimpleNamespace(id="T", phase="done", failed=False,
                            read_log=(("A", "A10"),)),
             SimpleNamespace(id="W", phase="done", failed=False,
                             read_log=(("B", "B11"),)))
    cycle = m.j1_adapter(m.State(), history=(versions, txns))
    assert cycle and {e["kind"] for e in cycle["edges"]} == {"rw"}
    assert m.j1_adapter(m.State(), history=(versions[:2], txns)) is None


def test_state_cap_is_incomplete():
    result = m.explore("safe-mainte", max_states=1)
    assert result["states"] == 1 and not result["complete"]


def _run():
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception:
                failures += 1
                print(f"FAIL {name}", flush=True)
                traceback.print_exc()
            else:
                print(f"PASS {name}", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(_run())
