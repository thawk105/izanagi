"""Cicada read-only GC publication model; runnable without pytest."""
from __future__ import annotations

import sys
import traceback
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from vhash_forwarding_model import ro_gc_publish as m  # noqa: E402

_RESULTS = {}


def _result(arm, config=m.Config(), cap=20_000):
    key = arm, config, cap
    if key not in _RESULTS:
        _RESULTS[key] = m.explore(arm, config=config, max_states=cap)
    return _RESULTS[key]


def test_configurations_and_completed_safety():
    expected = {
        "w2-k1-r1": ((299, 4594, 13478), (True, True, True)),
        "w2-k1-r2": ((345, 5171, 14055), (True, True, True)),
        "w2-k2-r1": ((345, 5171, 14055), (True, True, True)),
        "w2-k2-r2": ((529, 7479, 16363), (True, True, True)),
        "w3-k1-r1": ((5980, 20000, 20000), (True, False, False)),
    }
    assert tuple(c.name for c in m.CONFIGS) == tuple(expected)
    other_expected = {
        "w2-k1-r1": ((16630, 20000, 5971), (True, False, True)),
        "w2-k1-r2": ((18815, 20000, 6708), (True, False, True)),
        "w2-k2-r1": ((19033, 20000, 6708), (True, False, True)),
        "w2-k2-r2": ((20000, 20000, 9656), (False, False, True)),
        "w3-k1-r1": ((20000, 20000, 20000), (False, False, False)),
    }
    for config in m.CONFIGS:
        rows = [_result(arm, config) for arm in ("stock", "safe-flag", "safe-mainte")]
        states, complete = expected[config.name]
        assert tuple(r["states"] for r in rows) == states
        assert tuple(r["complete"] for r in rows) == complete
        for row in rows:
            assert row["config"] == config.name
            assert row["serializability"] == m.SERIALIZABILITY
            assert row["progress_meaning"] == m.PROGRESS
            if row["complete"]:
                assert row["gc_violations"] == 0
        if all(complete):
            assert rows[0]["publications"] == rows[0]["cuts"] == 0
            assert rows[1]["cuts"] > 0 and rows[2]["cuts"] > 0
        other = [_result(arm, config) for arm in
                 ("neg-early-flag", "bad-raise-slot", "bad-clear-slot")]
        states, complete = other_expected[config.name]
        assert tuple(r["states"] for r in other) == states
        assert tuple(r["complete"] for r in other) == complete
        if other[0]["complete"]:
            assert other[0]["gc_violations"] == 0
        for row in other[1:]:
            if row["complete"]:
                assert row["gc_violations"] > 0


def test_safe_cut_is_after_three_versions_and_next_slot_store():
    for arm in ("safe-flag", "safe-mainte"):
        row = _result(arm)
        assert row["complete"] and row["cuts"] > 0
        assert row["boundary_loads"] > 0 and row["no_cuts"] > 0
        steps = row["cut_witness"]
        assert steps[-1] == "U.cut_A10=39"
        assert steps.index("U.commit_A=30") < steps.index("U.commit_A=40")
        assert steps.index("U.commit_A=40") < steps.index("R.store_rts_slot=39")
        before = m.replay(arm, steps[:-1])
        after, event = next((state, event) for state, event in m.transitions(before, arm)
                            if event.label() == steps[-1])
        assert before.procedure == 2 and before.r_slot == 39
        assert m.gc_violation(before, after, event) is None
        assert after.reclaimed and not before.reclaimed


def test_stock_has_no_publication_or_cut():
    row = _result("stock")
    assert row["complete"] and row["publications"] == 0 and row["cuts"] == 0
    assert row["gc_violations"] == 0 and not row["progress"]


def test_bad_raise_slot_counterexample_and_extra_flag():
    row = _result("bad-raise-slot", cap=30_000)
    assert row["complete"] and row["states"] == 28742
    assert row["gc_violations"] == 10
    assert row["bad_raise_requires_extra_flag"]
    witness = row["gc_witness"]
    assert witness["steps"] == ["R.store_wts_slot=50","R.load_MinWts=20","R.store_rts_slot=19","R.read_A=A10","R.early_store_flag=1","U.store_wts_slot=30","U.store_rts_slot=29","U.commit_A=30","U.store_wts_slot=40","U.store_rts_slot=39","U.commit_A=40","U.mainte_start","U.load_execute=0","U.timer_elapsed","U.load_flag=0","U.store_flag=1","U.mainte_done","U.mainte_start","U.load_execute=0","U.timer_elapsed","L.load_flag0=1","L.load_flag1=1","L.load_wts0=50","L.load_rts0=19","L.load_wts1=40","L.load_rts1=39","L.store_MinWts=40","R.raise_rts_slot=39","L.store_MinRts=19","L.reset_flag0=0","R.early_store_flag=1","L.store_execute0=1","L.reset_flag1=0","U.load_flag=0","U.store_flag=1","U.mainte_done","U.mainte_start","L.store_execute1=1","U.load_execute=1","L.load_flag0=1","L.load_flag1=1","L.load_wts0=50","L.load_rts0=39","L.load_wts1=40","L.load_rts1=39","L.store_MinWts=40","L.store_MinRts=39","U.load_MinRts=39","U.cut_A10=39"]
    assert witness["reason"] == {"version": "A10", "reason": "held_pointer", "reader_rts": 19}
    steps = witness["steps"]
    assert steps[:5] == ["R.store_wts_slot=50", "R.load_MinWts=20",
                         "R.store_rts_slot=19", "R.read_A=A10", "R.early_store_flag=1"]
    assert steps.count("R.early_store_flag=1") == 2
    assert steps.index("R.raise_rts_slot=39") < steps.index("L.store_MinRts=39")
    assert steps[-1] == "U.cut_A10=39"
    before = m.replay("bad-raise-slot", steps[:-1])
    after, event = next((state, event) for state, event in m.transitions(before, "bad-raise-slot")
                        if event.label() == steps[-1])
    assert m.gc_violation(before, after, event) == witness["reason"]


def test_bad_clear_slot_counterexample():
    row = _result("bad-clear-slot")
    assert row["complete"] and row["states"] == 5971
    assert row["gc_violations"] == 12
    witness = row["gc_witness"]
    assert witness["steps"] == ["R.store_wts_slot=50","R.load_MinWts=20","R.store_rts_slot=19","R.read_A=A10","R.clear_refs","R.store_rts_slot=1000000","R.store_flag=1","R.store_wts_slot=60","R.load_MinWts=20","U.store_wts_slot=30","U.store_rts_slot=29","U.commit_A=30","U.store_wts_slot=40","U.store_rts_slot=39","U.commit_A=40","U.mainte_start","U.load_execute=0","U.timer_elapsed","U.load_flag=0","U.store_flag=1","U.mainte_done","U.mainte_start","L.load_flag0=1","L.load_flag1=1","L.load_wts0=60","L.load_rts0=1000000","R.store_rts_slot=19","L.load_wts1=40","L.load_rts1=39","L.store_MinWts=40","L.store_MinRts=39","L.reset_flag0=0","L.store_execute0=1","L.reset_flag1=0","L.store_execute1=1","U.load_execute=1","U.load_MinRts=39","U.cut_A10=39"]
    assert witness["reason"] == {"version": "A10", "reason": "future_read", "reader_rts": 19}
    steps = witness["steps"]
    assert steps[:7] == ["R.store_wts_slot=50", "R.load_MinWts=20",
                         "R.store_rts_slot=19", "R.read_A=A10", "R.clear_refs",
                         f"R.store_rts_slot={m.INF}", "R.store_flag=1"]
    assert steps[-1] == "U.cut_A10=39"
    before = m.replay("bad-clear-slot", steps[:-1])
    after, event = next((state, event) for state, event in m.transitions(before, "bad-clear-slot")
                        if event.label() == steps[-1])
    assert m.gc_violation(before, after, event) == witness["reason"]


def test_early_flag_is_safe_and_progress_is_descriptive():
    row = _result("neg-early-flag")
    assert row["complete"] and row["gc_violations"] == 0
    assert isinstance(row["progress"], bool)
    assert "MinRts value changed" in row["progress_meaning"]
    assert "not publication count" in row["progress_meaning"]


def test_equal_publication_is_not_progress():
    state = m.State(phase="hold", r_rts=19, r_slot=19, min_rts=19,
                    leader=7, scan_r=19, held=("A10",))
    after, _ = next((n, e) for n, e in m.transitions(state, "safe-flag")
                    if e.operation == "store_MinRts")
    assert after.publications == 1 and not after.progress


def test_oracle_ignores_gc_boundary():
    state = m.State(phase="read", r_rts=19, min_rts=39)
    assert m.needed_versions(state) == {"A10"}
    assert m.needed_versions(replace(state, min_rts=1)) == {"A10"}
    held = replace(state, phase="hold", held=("A10",))
    assert m.needed_versions(held) == m.needed_versions(replace(held, r_slot=m.INF)) == {"A10"}


def test_state_cap_is_incomplete():
    row = m.explore("safe-mainte", max_states=1)
    assert row["states"] == 1 and not row["complete"]


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
