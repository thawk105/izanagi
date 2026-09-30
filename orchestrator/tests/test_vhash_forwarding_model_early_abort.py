"""Cicada early-abort finite model; also runnable without pytest."""
from __future__ import annotations

import sys
import time
import traceback
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from vhash_forwarding_model import early_abort as m  # noqa: E402


_RESULTS = {}


def _result(writers=1, mutation="normal", cap=100_000):
    key = writers, mutation, cap
    if key not in _RESULTS:
        _RESULTS[key] = m.explore(writers=writers, mutation=mutation, max_states=cap)
    return _RESULTS[key]


def test_two_tx_exhaustive_sound():
    row = _result()
    assert row["complete"] and row["sound"] and row["d_states"] > 0, row
    assert row["cuts"] > 0 and row["reuses"] > 0, row
    assert row["wstar_transitions"] > 0, row


def test_three_tx_budgeted_sound():
    row = _result(2, cap=30_000)
    assert row["complete"] and row["sound"] and row["d_states"] > 0, row
    assert row["states"] <= 30_000 and row["transitions"] >= row["states"] - 1
    assert row["wstar_transitions"] > 0, row


def test_three_tx_fixed_abort_then_committed_witness():
    state = m.replay(("R.read_A=a0", "W1.install_A=pending", "W1.aborted",
                      "W2.install_A=pending", "W2.committed", "R.install_B=pending"),
                     writers=2)
    assert m.detect_d(state)
    assert m.validation_reads(state) is False
    finished = next(n for n, edge in m.transitions(state)
                    if edge.label == "R.validation_read=fail")
    assert finished.txs[0].phase == "done"


def test_deleted_version_is_a_witness():
    state = m.replay(("R.read_A=a0", "W1.install_A=pending", "W1.deleted"))
    assert m.detect_d(state)
    assert m.validation_reads(state) is False


def test_pending_abort_counterexample():
    pending = m.replay(("R.read_A=a0", "W1.install_A=pending"))
    assert m.detect_d(pending, mutation="pending")
    assert not m.detect_d(pending)
    resolved = m.replay(("R.read_A=a0", "W1.install_A=pending", "W1.aborted",
                         "R.install_B=pending"))
    assert m.validation_reads(resolved) is True
    row = _result(mutation="pending")
    assert not row["sound"] and row["counterexample"], row
    steps = row["counterexample"]
    assert "W1.install_A=pending" in steps and "W1.aborted" in steps
    assert steps.index("W1.install_A=pending") < steps.index("W1.aborted")
    assert "R.install_B=pending" in steps
    assert steps[-1] == "R.validation_read=pass"


def test_read_version_is_not_witness():
    read = m.replay(("R.read_A=a0",))
    assert not m.detect_d(read)
    assert m.detect_d(read, mutation="self")
    row = _result(mutation="self")
    assert not row["sound"] and row["counterexample"], row
    assert row["counterexample"][-1] == "R.validation_read=pass"


def test_saved_later_version_and_independent_validation():
    # A writer newer than R's original ts is skipped and saved at read time.
    state = m.initial()
    writer = state.txs[1]
    writer = replace(writer, ts=m.stamp(60, 3))
    state = replace(state, txs=(state.txs[0], writer))
    state = next(n for n, edge in m.transitions(state)
                 if edge.label == "W1.install_A=pending")
    state = next(n for n, edge in m.transitions(state)
                 if edge.label == "R.read_A=a0")
    assert state.txs[0].reads[0].later == "w1"
    assert m.validation_reads(state) is True  # pending 60 is above R.ts 50
    assert not m.detect_d(state)
    # Validation must neither call nor share the implementation of D.
    original = m.detect_d
    try:
        m.detect_d = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("D called"))
        assert m.validation_reads(state) is True
    finally:
        m.detect_d = original


def test_saved_later_explains_promotion_exclusion():
    # This manually promoted state is outside the modeled genome. A newer
    # committed witness can sit above saved later_ver_ and be skipped there.
    state = m.initial()
    writer = replace(state.txs[1], ts=m.stamp(60, 3))
    state = replace(state, txs=(state.txs[0], writer))
    state = next(n for n, e in m.transitions(state) if e.label == "W1.install_A=pending")
    state = next(n for n, e in m.transitions(state) if e.label == "R.read_A=a0")
    state = next(n for n, e in m.transitions(state) if e.label == "W1.aborted")
    witness = m.Version("x", "A", m.stamp(65, 4), "X", m.COMMITTED)
    state = replace(state, versions=state.versions + (witness,),
                    chains=(("A", ("x", "w1", "a0")), state.chains[1]),
                    txs=(replace(state.txs[0], ts=m.stamp(70, 2)), state.txs[1]))
    m.check_timestamps(state)
    assert m.detect_d(state)
    assert m.validation_reads(state) is True
    assert m.validation_reads(replace(state, txs=(replace(
        state.txs[0], reads=(replace(state.txs[0].reads[0], later=""),)), state.txs[1]))) is False


def test_readonly_is_never_predicted():
    state = m.replay(("R.read_A=a0", "W1.install_A=pending", "W1.committed"),
                     readonly=True)
    assert not m.detect_d(state)
    assert not m.detect_d(state, mutation="pending")


def test_forward_floor_and_gc_reuse():
    state = m.replay(("R.read_A=a0", "R.forward_70_publish_69"))
    reader = state.txs[0]
    assert reader.start_floor < reader.floor == m.stamp(70, 2) - 1
    assert reader.reads[0].later == ""
    assert m.validation_reads(state) is True
    # W* blocks a writer whose earlier timestamp would invalidate the read.
    pending = next(n for n, edge in m.transitions(state)
                   if edge.label == "W1.install_A=pending")
    assert "W1.committed" not in [e.label for _, e in m.transitions(pending)]
    assert "W1.aborted" in [e.label for _, e in m.transitions(pending)]


def test_gc_cuts_and_reuses_physical_pointer():
    state = m.replay(("R.read_A=a0", "W1.install_A=pending", "W1.committed",
                      "R.install_B=pending", "R.validation_read=fail",
                      "GC.cut_A_after=w1", "GC.reuse_a0_as_A80"))
    reused = next(v for v in state.versions if v.id == "a0")
    assert reused.reused and not reused.reclaimed
    assert reused.wts == m.stamp(80, 5) and m._chain(state, "A")[0] == "a0"
    m.check_timestamps(state)


def test_timestamp_uniqueness_rejects_other_owner():
    state = m.initial()
    bad = replace(state.txs[1], ts=state.txs[0].ts)
    state = replace(state, txs=(state.txs[0], bad))
    try:
        m.check_timestamps(state)
    except ValueError:
        pass
    else:
        raise AssertionError("same wts accepted for distinct owners")


def _run():
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        start = time.monotonic()
        try:
            fn()
        except Exception:
            failed += 1
            print(f"FAIL {name} {time.monotonic() - start:.3f}s", flush=True)
            traceback.print_exc()
        else:
            print(f"PASS {name} {time.monotonic() - start:.3f}s", flush=True)
    for key, row in sorted(_RESULTS.items()):
        print(f"EXPLORE {key}: {row}", flush=True)
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(_run())
