"""8c の累積ベンチ時間 consumer。

この module は 6 cell 分の予約を一度に ledger へ固定し、terminal 後に
cell ごとの実測値だけを精算する。ledger の identity と read-modify-write
は process 間でも同じ lock で保護する。
"""
from __future__ import annotations

import contextlib
import dataclasses
import json
import math
import os
import re
import tempfile
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Literal

__all__ = ("reserve_all_cells", "settle", "symmetric_indeterminate")


class BudgetError(RuntimeError):
    """予算 ledger の入力または状態が不正である。"""


_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_ARMS = frozenset(("on", "off", "swapped"))
_HOLDOUTS = frozenset(("H1", "H2"))
_EXPECTED_CELL_ROWS = (
    ("H1", "on"),
    ("H1", "off"),
    ("H1", "swapped"),
    ("H2", "on"),
    ("H2", "off"),
    ("H2", "swapped"),
)
_TOLERANCE = 1e-9
_LEDGER_SCHEMA = "s8c-budget-ledger/v1"


def _finite_nonnegative(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BudgetError(f"{field} は有限の非負数でない")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise BudgetError(f"{field} は有限の非負数でない")
    return number


def _nonempty_string(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise BudgetError(f"{field} は空でない str でない")
    return value


def _hash(value: object, *, field: str) -> str:
    value = _nonempty_string(value, field=field)
    if _HASH_RE.fullmatch(value) is None:
        raise BudgetError(f"{field} は lowercase sha256 でない")
    return value


def _immutable_limit_map(
    value: Mapping[str, float], *, field: str, expected_keys: frozenset[str]
) -> Mapping[str, float]:
    if not isinstance(value, Mapping):
        raise BudgetError(f"{field} は mapping でない")
    copied: dict[str, float] = {}
    for key, raw in value.items():
        if type(key) is not str or not key:
            raise BudgetError(f"{field} の key が不正")
        copied[key] = _finite_nonnegative(raw, field=f"{field}.{key}")
    if frozenset(copied) != expected_keys:
        raise BudgetError(
            f"{field} の coverage が不一致: "
            f"expected={sorted(expected_keys)!r} actual={sorted(copied)!r}"
        )
    return MappingProxyType(copied)


@dataclasses.dataclass(frozen=True, slots=True)
class BudgetLimits:
    total_bench_s: float
    per_arm_bench_s: Mapping[str, float]
    per_holdout_bench_s: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "total_bench_s",
            _finite_nonnegative(self.total_bench_s, field="total_bench_s"),
        )
        object.__setattr__(
            self,
            "per_arm_bench_s",
            _immutable_limit_map(
                self.per_arm_bench_s,
                field="per_arm_bench_s",
                expected_keys=_ARMS,
            ),
        )
        object.__setattr__(
            self,
            "per_holdout_bench_s",
            _immutable_limit_map(
                self.per_holdout_bench_s,
                field="per_holdout_bench_s",
                expected_keys=_HOLDOUTS,
            ),
        )
        for arm in sorted(_ARMS):
            if self.per_arm_bench_s[arm] <= 0.0:
                raise BudgetError(f"per_arm_bench_s.{arm} が正でない")
        for holdout in sorted(_HOLDOUTS):
            if self.per_holdout_bench_s[holdout] <= 0.0:
                raise BudgetError(f"per_holdout_bench_s.{holdout} が正でない")
        if min(self.per_arm_bench_s.values()) != max(self.per_arm_bench_s.values()):
            raise BudgetError("per_arm_bench_s が arm 間で対称でない")
        if (
            sum(self.per_holdout_bench_s[holdout] for holdout in sorted(_HOLDOUTS))
            != self.total_bench_s
        ):
            raise BudgetError("per_holdout_bench_s の和が総上限と一致しない")


@dataclasses.dataclass(frozen=True, slots=True)
class ReservationCell:
    cell_id: str
    holdout: str
    arm: str
    reserved_bench_s: float

    def __post_init__(self) -> None:
        _nonempty_string(self.cell_id, field="cell_id")
        if type(self.holdout) is not str or self.holdout not in _HOLDOUTS:
            raise BudgetError(f"holdout が未知: {self.holdout!r}")
        if type(self.arm) is not str or self.arm not in _ARMS:
            raise BudgetError(f"arm が未知: {self.arm!r}")
        _finite_nonnegative(self.reserved_bench_s, field="reserved_bench_s")


@dataclasses.dataclass(frozen=True, slots=True)
class Reservation:
    cells: tuple[ReservationCell, ...]
    budget_bench_s: float
    total_reserved_bench_s: float
    state: Literal["held", "insufficient"]


@dataclasses.dataclass(frozen=True, slots=True)
class SettlementCell:
    cell_id: str
    actual_bench_s: float


@dataclasses.dataclass(frozen=True, slots=True)
class Settlement:
    cells: tuple[SettlementCell, ...]
    total_actual_bench_s: float


@dataclasses.dataclass(frozen=True, slots=True)
class Ledger:
    manifest_sha256: str
    freeze_sha256: str
    schedule_sha256: str
    ratified_generation_sha256: str
    reservation: Reservation
    settlement: Settlement
    cell_ids: frozenset[str]


def _validate_cell_matrix(cells: Sequence[ReservationCell]) -> tuple[ReservationCell, ...]:
    if isinstance(cells, (str, bytes)):
        raise BudgetError("cells は sequence でない")
    try:
        frozen = tuple(cells)
    except TypeError as exc:
        raise BudgetError("cells は sequence でない") from exc
    if len(frozen) != len(_EXPECTED_CELL_ROWS):
        raise BudgetError("cells は H1/H2 x on/off/swapped の 6 件でない")
    if any(type(cell) is not ReservationCell for cell in frozen):
        raise BudgetError("cells に ReservationCell 以外がある")
    if len({cell.cell_id for cell in frozen}) != len(frozen):
        raise BudgetError("cell_id が重複")
    observed = frozenset((cell.holdout, cell.arm) for cell in frozen)
    expected = frozenset(_EXPECTED_CELL_ROWS)
    if observed != expected:
        raise BudgetError("cells の holdout/arm coverage が不一致")
    return frozen


def _sum_by(
    cells: Sequence[ReservationCell], *, key: str
) -> dict[str, float]:
    values = {name: 0.0 for name in (_ARMS if key == "arm" else _HOLDOUTS)}
    for cell in cells:
        values[getattr(cell, key)] += cell.reserved_bench_s
    return values


def _sum_actual_by(
    reservation: Reservation, cells: Sequence[SettlementCell], *, key: str
) -> dict[str, float]:
    metadata = {cell.cell_id: cell for cell in reservation.cells}
    values = {name: 0.0 for name in (_ARMS if key == "arm" else _HOLDOUTS)}
    for cell in cells:
        values[getattr(metadata[cell.cell_id], key)] += cell.actual_bench_s
    return values


def _document(ledger: Ledger, *, limits: BudgetLimits) -> dict[str, object]:
    return {
        "schema_version": _LEDGER_SCHEMA,
        "manifest_sha256": ledger.manifest_sha256,
        "freeze_sha256": ledger.freeze_sha256,
        "schedule_sha256": ledger.schedule_sha256,
        "ratified_generation_sha256": ledger.ratified_generation_sha256,
        "reservation": {
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "holdout": cell.holdout,
                    "arm": cell.arm,
                    "reserved_bench_s": cell.reserved_bench_s,
                }
                for cell in ledger.reservation.cells
            ],
            "budget_bench_s": ledger.reservation.budget_bench_s,
            "total_reserved_bench_s": ledger.reservation.total_reserved_bench_s,
            "state": ledger.reservation.state,
            "limits": {
                "total_bench_s": limits.total_bench_s,
                "per_arm_bench_s": dict(limits.per_arm_bench_s),
                "per_holdout_bench_s": dict(limits.per_holdout_bench_s),
            },
        },
        "settlement": {
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "actual_bench_s": cell.actual_bench_s,
                }
                for cell in ledger.settlement.cells
            ],
            "total_actual_bench_s": ledger.settlement.total_actual_bench_s,
        },
        "cell_ids": sorted(ledger.cell_ids),
    }


def _atomic_create(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise BudgetError(f"budget ledger は既に存在する: {path}")
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise BudgetError(f"budget ledger は既に存在する: {path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _atomic_replace(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise BudgetError(f"budget ledger が symlink: {path}")
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def _ledger_lock(path: Path):
    """台帳の read-modify-write 全区間を O_EXCL lock で直列化する。"""
    lock_path = path.with_name(path.name + ".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise BudgetError(f"budget ledger lock が既に存在する: {lock_path}") from exc
    except OSError as exc:
        raise BudgetError(f"budget ledger lock を作れない: {lock_path}: {exc}") from exc
    try:
        os.close(lock_fd)
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise BudgetError(f"budget ledger lock を削除できない: {lock_path}") from exc


def _read_raw(path: Path) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BudgetError(f"budget ledger を読めない: {path}") from exc
    if not isinstance(value, dict):
        raise BudgetError("budget ledger top-level が object でない")
    return value


def _limits_from_raw(value: object) -> BudgetLimits:
    if not isinstance(value, Mapping):
        raise BudgetError("reservation.limits が object でない")
    return BudgetLimits(
        total_bench_s=value.get("total_bench_s"),
        per_arm_bench_s=value.get("per_arm_bench_s"),
        per_holdout_bench_s=value.get("per_holdout_bench_s"),
    )


def _ledger_from_raw(value: Mapping[str, object]) -> tuple[Ledger, BudgetLimits]:
    expected = {
        "schema_version",
        "manifest_sha256",
        "freeze_sha256",
        "schedule_sha256",
        "ratified_generation_sha256",
        "reservation",
        "settlement",
        "cell_ids",
    }
    if set(value) != expected:
        raise BudgetError("budget ledger schema が不一致")
    if value["schema_version"] != _LEDGER_SCHEMA:
        raise BudgetError("budget ledger schema_version が不一致")
    reservation_raw = value["reservation"]
    settlement_raw = value["settlement"]
    if not isinstance(reservation_raw, Mapping) or not isinstance(settlement_raw, Mapping):
        raise BudgetError("reservation/settlement が object でない")
    if set(reservation_raw) != {
        "cells", "budget_bench_s", "total_reserved_bench_s", "state", "limits"
    }:
        raise BudgetError("reservation schema が不一致")
    if set(settlement_raw) != {"cells", "total_actual_bench_s"}:
        raise BudgetError("settlement schema が不一致")
    raw_cells = reservation_raw["cells"]
    raw_settlements = settlement_raw["cells"]
    if not isinstance(raw_cells, list) or not isinstance(raw_settlements, list):
        raise BudgetError("reservation.cells/settlement.cells が list でない")
    cells: list[ReservationCell] = []
    for raw_cell in raw_cells:
        if not isinstance(raw_cell, Mapping) or set(raw_cell) != {
            "cell_id", "holdout", "arm", "reserved_bench_s"
        }:
            raise BudgetError("reservation cell schema が不一致")
        cells.append(
            ReservationCell(
                cell_id=raw_cell["cell_id"],
                holdout=raw_cell["holdout"],
                arm=raw_cell["arm"],
                reserved_bench_s=raw_cell["reserved_bench_s"],
            )
        )
    frozen_cells = _validate_cell_matrix(cells)
    cell_ids = value["cell_ids"]
    if (
        not isinstance(cell_ids, list)
        or any(type(item) is not str for item in cell_ids)
        or frozenset(cell_ids) != frozenset(cell.cell_id for cell in frozen_cells)
    ):
        raise BudgetError("ledger.cell_ids が reservation と不一致")
    state = reservation_raw["state"]
    if type(state) is not str or state not in {"held", "insufficient"}:
        raise BudgetError("reservation.state が不正")
    reservation = Reservation(
        cells=frozen_cells,
        budget_bench_s=_finite_nonnegative(
            reservation_raw["budget_bench_s"], field="reservation.budget_bench_s"
        ),
        total_reserved_bench_s=_finite_nonnegative(
            reservation_raw["total_reserved_bench_s"],
            field="reservation.total_reserved_bench_s",
        ),
        state=state,
    )
    settlements: list[SettlementCell] = []
    known_ids = frozenset(cell.cell_id for cell in frozen_cells)
    for raw_cell in raw_settlements:
        if not isinstance(raw_cell, Mapping) or set(raw_cell) != {
            "cell_id", "actual_bench_s"
        }:
            raise BudgetError("settlement cell schema が不一致")
        cell_id = _nonempty_string(raw_cell["cell_id"], field="settlement.cell_id")
        if cell_id not in known_ids:
            raise BudgetError("未知 cell を精算")
        if any(item.cell_id == cell_id for item in settlements):
            raise BudgetError("同一 cell を二重精算")
        settlements.append(
            SettlementCell(
                cell_id=cell_id,
                actual_bench_s=_finite_nonnegative(
                    raw_cell["actual_bench_s"], field="settlement.actual_bench_s"
                ),
            )
        )
    settlement = Settlement(
        cells=tuple(settlements),
        total_actual_bench_s=_finite_nonnegative(
            settlement_raw["total_actual_bench_s"],
            field="settlement.total_actual_bench_s",
        ),
    )
    if not math.isclose(
        settlement.total_actual_bench_s,
        sum(item.actual_bench_s for item in settlements),
        rel_tol=0.0,
        abs_tol=_TOLERANCE,
    ):
        raise BudgetError("settlement.total_actual_bench_s が再集計と不一致")
    if not math.isclose(
        reservation.total_reserved_bench_s,
        sum(item.reserved_bench_s for item in frozen_cells),
        rel_tol=0.0,
        abs_tol=_TOLERANCE,
    ):
        raise BudgetError("reservation.total_reserved_bench_s が再集計と不一致")
    for settled in settlements:
        reserved = next(
            cell.reserved_bench_s
            for cell in frozen_cells
            if cell.cell_id == settled.cell_id
        )
        if settled.actual_bench_s > reserved + _TOLERANCE:
            raise BudgetError("settlement が cell 予約枠を超過")
    ledger = Ledger(
        manifest_sha256=_hash(value["manifest_sha256"], field="manifest_sha256"),
        freeze_sha256=_hash(value["freeze_sha256"], field="freeze_sha256"),
        schedule_sha256=_hash(value["schedule_sha256"], field="schedule_sha256"),
        ratified_generation_sha256=_hash(
            value["ratified_generation_sha256"],
            field="ratified_generation_sha256",
        ),
        reservation=reservation,
        settlement=settlement,
        cell_ids=frozenset(cell_ids),
    )
    limits = _limits_from_raw(reservation_raw["limits"])
    if not math.isclose(
        reservation.budget_bench_s,
        limits.total_bench_s,
        rel_tol=0.0,
        abs_tol=_TOLERANCE,
    ):
        raise BudgetError("reservation.budget_bench_s が limits と不一致")
    expected_total, sufficient = _check_limit_state(frozen_cells, limits)
    if not math.isclose(
        reservation.total_reserved_bench_s,
        expected_total,
        rel_tol=0.0,
        abs_tol=_TOLERANCE,
    ) or reservation.state != ("held" if sufficient else "insufficient"):
        raise BudgetError("reservation の limit state が不一致")
    if settlement.total_actual_bench_s > limits.total_bench_s + _TOLERANCE:
        raise BudgetError("settlement の総実測が総上限を超過")
    for arm, value in _sum_actual_by(
        reservation, settlements, key="arm"
    ).items():
        if value > limits.per_arm_bench_s[arm] + _TOLERANCE:
            raise BudgetError("settlement の arm 実測が上限を超過")
    for holdout, value in _sum_actual_by(
        reservation, settlements, key="holdout"
    ).items():
        if value > limits.per_holdout_bench_s[holdout] + _TOLERANCE:
            raise BudgetError("settlement の holdout 実測が上限を超過")
    return ledger, limits


def _read_ledger(path: Path) -> tuple[Ledger, BudgetLimits]:
    return _ledger_from_raw(_read_raw(path))


def _same_identity(
    ledger: Ledger,
    *,
    manifest_sha256: str,
    freeze_sha256: str,
    schedule_sha256: str,
    ratified_generation_sha256: str,
) -> bool:
    return (
        ledger.manifest_sha256 == manifest_sha256
        and ledger.freeze_sha256 == freeze_sha256
        and ledger.schedule_sha256 == schedule_sha256
        and ledger.ratified_generation_sha256 == ratified_generation_sha256
    )


def _check_limit_state(cells: Sequence[ReservationCell], limits: BudgetLimits) -> tuple[float, bool]:
    total_reserved_bench_s = sum(cell.reserved_bench_s for cell in cells)
    all_cells_reserved = all(cell.reserved_bench_s > 0.0 for cell in cells)
    by_arm = _sum_by(cells, key="arm")
    by_holdout = _sum_by(cells, key="holdout")
    total_ok = total_reserved_bench_s <= limits.total_bench_s + _TOLERANCE
    arm_ok = all(
        value <= limits.per_arm_bench_s[arm] + _TOLERANCE
        for arm, value in by_arm.items()
    )
    holdout_ok = all(
        value <= limits.per_holdout_bench_s[holdout] + _TOLERANCE
        for holdout, value in by_holdout.items()
    )
    return (
        total_reserved_bench_s,
        all_cells_reserved and total_ok and arm_ok and holdout_ok,
    )


def reserve_all_cells(
    ledger_path: Path,
    *,
    manifest_sha256: str,
    freeze_sha256: str,
    schedule_sha256: str,
    ratified_generation_sha256: str,
    cells: Sequence[ReservationCell],
    limits: BudgetLimits,
) -> Ledger:
    """全 cell を予約し、総上限・arm 上限・holdout 上限を同時に判定する。"""
    path = Path(ledger_path)
    if path.is_symlink():
        raise BudgetError(f"budget ledger が symlink: {path}")
    manifest_sha256 = _hash(manifest_sha256, field="manifest_sha256")
    freeze_sha256 = _hash(freeze_sha256, field="freeze_sha256")
    schedule_sha256 = _hash(schedule_sha256, field="schedule_sha256")
    ratified_generation_sha256 = _hash(
        ratified_generation_sha256, field="ratified_generation_sha256"
    )
    if type(limits) is not BudgetLimits:
        raise BudgetError("limits は BudgetLimits 必須")
    frozen_cells = _validate_cell_matrix(cells)
    total_reserved_bench_s, sufficient = _check_limit_state(frozen_cells, limits)
    state: Literal["held", "insufficient"] = "held" if sufficient else "insufficient"
    candidate = Ledger(
        manifest_sha256=manifest_sha256,
        freeze_sha256=freeze_sha256,
        schedule_sha256=schedule_sha256,
        ratified_generation_sha256=ratified_generation_sha256,
        reservation=Reservation(
            cells=frozen_cells,
            budget_bench_s=limits.total_bench_s,
            total_reserved_bench_s=total_reserved_bench_s,
            state=state,
        ),
        settlement=Settlement(cells=tuple(), total_actual_bench_s=0.0),
        cell_ids=frozenset(cell.cell_id for cell in frozen_cells),
    )
    with _ledger_lock(path):
        if path.exists() or path.is_symlink():
            existing, existing_limits = _read_ledger(path)
            if not _same_identity(
                existing,
                manifest_sha256=manifest_sha256,
                freeze_sha256=freeze_sha256,
                schedule_sha256=schedule_sha256,
                ratified_generation_sha256=ratified_generation_sha256,
            ):
                raise BudgetError("既存 ledger の 4 hash identity が不一致")
            if existing.reservation.cells != frozen_cells:
                raise BudgetError("既存 ledger の cell reservation が不一致")
            if existing.reservation.budget_bench_s != limits.total_bench_s:
                raise BudgetError("既存 ledger の総予算が不一致")
            if existing_limits != limits:
                raise BudgetError("既存 ledger の 3 層予算が不一致")
            return existing
        _atomic_create(path, _document(candidate, limits=limits))
        created, _ = _read_ledger(path)
        return created


def settle(
    ledger_path: Path, *, cell_id: str, actual_bench_s: float
) -> Ledger:
    """既知かつ未精算の cell を実測値へ精算する。"""
    path = Path(ledger_path)
    if path.is_symlink():
        raise BudgetError(f"budget ledger が symlink: {path}")
    cell_id = _nonempty_string(cell_id, field="cell_id")
    actual_bench_s = _finite_nonnegative(actual_bench_s, field="actual_bench_s")
    with _ledger_lock(path):
        ledger, limits = _read_ledger(path)
        if ledger.reservation.state != "held":
            raise BudgetError("insufficient ledger は精算できない")
        if cell_id not in ledger.cell_ids:
            raise BudgetError(f"未知 cell を精算: {cell_id}")
        if any(item.cell_id == cell_id for item in ledger.settlement.cells):
            raise BudgetError(f"cell を二重精算: {cell_id}")
        reserved = next(
            cell.reserved_bench_s
            for cell in ledger.reservation.cells
            if cell.cell_id == cell_id
        )
        if actual_bench_s <= reserved + _TOLERANCE:
            pass
        else:
            raise BudgetError("actual_bench_s が cell 予約枠を超過")
        settlement_cells = ledger.settlement.cells + (
            SettlementCell(cell_id=cell_id, actual_bench_s=actual_bench_s),
        )
        total_actual_bench_s = sum(cell.actual_bench_s for cell in settlement_cells)
        if total_actual_bench_s <= ledger.reservation.total_reserved_bench_s + _TOLERANCE:
            pass
        else:
            raise BudgetError("settlement の総実測が総予約枠を超過")
        for arm, value in _sum_actual_by(
            ledger.reservation, settlement_cells, key="arm"
        ).items():
            if value > limits.per_arm_bench_s[arm] + _TOLERANCE:
                raise BudgetError("settlement の arm 実測が上限を超過")
        for holdout, value in _sum_actual_by(
            ledger.reservation, settlement_cells, key="holdout"
        ).items():
            if value > limits.per_holdout_bench_s[holdout] + _TOLERANCE:
                raise BudgetError("settlement の holdout 実測が上限を超過")
        updated = dataclasses.replace(
            ledger,
            settlement=Settlement(
                cells=settlement_cells,
                total_actual_bench_s=total_actual_bench_s,
            ),
        )
        _atomic_replace(path, _document(updated, limits=limits))
        settled, _ = _read_ledger(path)
        return settled


def symmetric_indeterminate(
    ledger: Ledger, *, launched_cell_ids: Collection[str] = ()
) -> frozenset[str]:
    """不足時に未走 cell を対称に判定不能へ投影する。"""
    if type(ledger) is not Ledger:
        raise BudgetError("ledger は Ledger 必須")
    launched = frozenset(launched_cell_ids)
    if not launched <= ledger.cell_ids:
        raise BudgetError("launched_cell_ids に未知 cell がある")
    if ledger.reservation.state != "insufficient":
        return frozenset()
    if launched:
        raise BudgetError("insufficient ledger で一部 cell だけ走った")
    return frozenset(ledger.cell_ids)
