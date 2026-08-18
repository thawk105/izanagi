"""8c budget consumer の runtime contract tests。"""
from __future__ import annotations

import ast
import threading
from pathlib import Path

import pytest

from orchestrator.campaign import s8c_budget as B


def _cells(seconds: float = 4.0) -> tuple[B.ReservationCell, ...]:
    return tuple(
        B.ReservationCell(
            cell_id=f"{holdout.lower()}-{arm}",
            holdout=holdout,
            arm=arm,
            reserved_bench_s=seconds,
        )
        for holdout, arm in B._EXPECTED_CELL_ROWS
    )


def _limits(
    *, total: float = 24.0, per_arm: float = 8.0, per_holdout: float = 12.0
) -> B.BudgetLimits:
    return B.BudgetLimits(
        total_bench_s=total,
        per_arm_bench_s={
            "on": per_arm,
            "off": per_arm,
            "swapped": per_arm,
        },
        per_holdout_bench_s={"H1": per_holdout, "H2": per_holdout},
    )


def _reserve(path: Path, *, limits: B.BudgetLimits) -> B.Ledger:
    return B.reserve_all_cells(
        path,
        manifest_sha256="a" * 64,
        freeze_sha256="b" * 64,
        schedule_sha256="c" * 64,
        ratified_generation_sha256="d" * 64,
        cells=_cells(),
        limits=limits,
    )


@pytest.mark.parametrize(
    "limits",
    [
        pytest.param(_limits(total=10.0, per_arm=100.0, per_holdout=100.0), id="total"),
        pytest.param(_limits(total=100.0, per_arm=5.0, per_holdout=100.0), id="arm"),
        pytest.param(_limits(total=100.0, per_arm=100.0, per_holdout=5.0), id="holdout"),
    ],
)
def test_each_budget_layer_has_a_numeric_insufficient_witness(
    tmp_path: Path, limits: B.BudgetLimits
) -> None:
    ledger = _reserve(tmp_path / "ledger.json", limits=limits)
    assert ledger.reservation.state == "insufficient"
    assert ledger.reservation.total_reserved_bench_s == 24.0
    assert B.symmetric_indeterminate(ledger) == ledger.cell_ids


def test_all_three_layers_within_limit_are_held(tmp_path: Path) -> None:
    ledger = _reserve(tmp_path / "ledger.json", limits=_limits())
    assert ledger.reservation.state == "held"
    assert B.symmetric_indeterminate(ledger) == frozenset()
    assert ledger.manifest_sha256 == "a" * 64
    assert ledger.reservation.cells[0].reserved_bench_s == 4.0
    assert ledger.settlement.cells == ()


def test_budget_limits_require_arm_and_holdout_coverage() -> None:
    with pytest.raises(B.BudgetError, match="coverage"):
        B.BudgetLimits(
            total_bench_s=1.0,
            per_arm_bench_s={"on": 1.0, "off": 1.0},
            per_holdout_bench_s={"H1": 1.0, "H2": 1.0},
        )
    with pytest.raises(B.BudgetError, match="coverage"):
        B.BudgetLimits(
            total_bench_s=1.0,
            per_arm_bench_s={"on": 1.0, "off": 1.0, "swapped": 1.0},
            per_holdout_bench_s={"H1": 1.0},
        )


def test_reservation_is_immutable_and_exact_reserve_is_idempotent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ledger.json"
    limits = _limits()
    ledger = _reserve(path, limits=limits)
    with pytest.raises((AttributeError, TypeError)):
        ledger.reservation.cells.append(ledger.reservation.cells[0])  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        limits.per_arm_bench_s["on"] = 9.0  # type: ignore[index]
    with pytest.raises((AttributeError, TypeError)):
        ledger.cell_ids.add("late-cell")  # type: ignore[attr-defined]
    assert _reserve(path, limits=limits) == ledger

    changed = _cells()
    changed = changed[:-1] + (
        B.ReservationCell("h2-swapped-new", "H2", "swapped", 4.0),
    )
    with pytest.raises(B.BudgetError, match="reservation"):
        B.reserve_all_cells(
            path,
            manifest_sha256="a" * 64,
            freeze_sha256="b" * 64,
            schedule_sha256="c" * 64,
            ratified_generation_sha256="d" * 64,
            cells=changed,
            limits=limits,
        )


def test_settle_accepts_one_known_cell_only_once_and_never_over_reserves(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ledger.json"
    _reserve(path, limits=_limits())
    settled = B.settle(path, cell_id="h1-on", actual_bench_s=3.5)
    assert settled.settlement.cells == (
        B.SettlementCell("h1-on", 3.5),
    )
    with pytest.raises(B.BudgetError, match="二重精算"):
        B.settle(path, cell_id="h1-on", actual_bench_s=3.5)
    with pytest.raises(B.BudgetError, match="未知"):
        B.settle(path, cell_id="unknown", actual_bench_s=0.0)
    with pytest.raises(B.BudgetError, match="予約枠"):
        B.settle(path, cell_id="h1-off", actual_bench_s=4.1)


def test_settle_serializes_read_modify_write_with_o_excl_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "ledger.json"
    _reserve(path, limits=_limits())
    entered = threading.Event()
    release = threading.Event()
    original = B._read_ledger

    def blocked(ledger_path: Path):
        entered.set()
        assert release.wait(5.0)
        return original(ledger_path)

    monkeypatch.setattr(B, "_read_ledger", blocked)
    outcomes: list[object] = []

    def first() -> None:
        try:
            outcomes.append(B.settle(path, cell_id="h1-on", actual_bench_s=1.0))
        except BaseException as exc:  # pragma: no cover - diagnostic path
            outcomes.append(exc)

    thread = threading.Thread(target=first)
    thread.start()
    assert entered.wait(5.0)
    with pytest.raises(B.BudgetError, match="lock"):
        B.settle(path, cell_id="h1-off", actual_bench_s=1.0)
    release.set()
    thread.join(5.0)
    assert len(outcomes) == 1
    assert isinstance(outcomes[0], B.Ledger)


def test_stale_lock_is_fail_closed_and_partial_insufficient_run_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ledger.json"
    path.with_name(path.name + ".lock").touch()
    with pytest.raises(B.BudgetError, match="lock"):
        _reserve(path, limits=_limits())

    ledger = _reserve(tmp_path / "insufficient.json", limits=_limits(total=10.0))
    with pytest.raises(B.BudgetError, match="一部"):
        B.symmetric_indeterminate(ledger, launched_cell_ids=("h1-on",))


def test_registered_build_gate_requires_authoritative_drive_before_reserve() -> None:
    """M6 の注入 drive は budget consumer より前に fail-closed で拒否する。"""
    supervisor_path = Path(B.__file__).with_name("p3_autonomous_workload_trial.py")
    tree = ast.parse(supervisor_path.read_text(encoding="utf-8"))
    run_trial = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_trial"
    )
    calls = [
        node
        for node in ast.walk(run_trial)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    ]
    authority_calls = [
        node
        for node in calls
        if node.func.id == "_accounting_authority"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "drive"
    ]
    reserve_calls = [node for node in calls if node.func.id == "reserve_all_cells"]
    assert authority_calls and reserve_calls
    assert min(node.lineno for node in authority_calls) < min(
        node.lineno for node in reserve_calls
    )
    gates = [
        node
        for node in ast.walk(run_trial)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.BoolOp)
        and isinstance(node.test.op, ast.And)
        and any(
            isinstance(value, ast.Compare)
            and any(
                isinstance(part, ast.Name)
                and part.id == "accounting_authority"
                for part in ast.walk(value)
            )
            and any(
                isinstance(part, ast.Name)
                and part.id == "_AUTHORITATIVE_ACCOUNTING"
                for part in ast.walk(value)
            )
            for value in node.test.values
        )
    ]
    assert gates
    gate = gates[0]
    assert any(isinstance(node, ast.Raise) for node in ast.walk(gate))


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
