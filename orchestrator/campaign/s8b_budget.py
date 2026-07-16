# -*- coding: utf-8 -*-
"""S-1 と独立した 8b oracle の bench/wall budget 台帳。

台帳 identity は manifest / freeze byte / schedule の三つの hash に束縛され、open 時に
完全一致を要求する (別 worktree・別 host の同名 path を別台帳へ分離しない fail-open を塞ぐ)。

予算は行単位 preflight ではなく **事前一括 reservation** で確保する。attempt 開始前に全予定行の
最大 bench 枠を予約し (`reserve`)、terminal 後に実測へ精算する (`settle`)。予約は crash では
解放しない (`charged_bench_s == reserved_bench_s` を耐久化する)。確保できない場合は一行も走らせず
`mark_exhausted` で terminal を耐久化する。`reserved_bench_s` (予約枠) / `charged_bench_s`
(gate 計上額) / `actual_bench_s` (実測) を分離して記録する。
"""
from __future__ import annotations

import contextlib
import copy
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Dict, Mapping


SCHEMA_VERSION = "8b-budget-ledger/v2"
_TOP_LEVEL_KEYS = {
    "schema_version", "manifest_sha256", "freeze_sha256", "schedule_sha256",
    "limits", "reservation", "spent", "entries",
}
_LIMIT_KEYS = {"total_bench_s", "per_holdout_bench_s", "oracle_shared"}
_SPENT_KEYS = {"bench_s", "wall_s", "by_holdout"}
_RESERVATION_KEYS = {
    "status", "reserved_bench_s", "charged_bench_s", "actual_bench_s",
    "by_holdout_reserved", "by_holdout_charged", "reserved_iso", "settled_iso",
}
_RESERVATION_STATUSES = {"held", "settled", "exhausted"}
_ENTRY_KEYS = {
    "campaign_id", "block_id", "schedule_index", "holdout_id",
    "configuration_id", "attempt", "outcome", "bench_s", "wall_s",
    "started_iso", "finished_iso",
}
_TOLERANCE = 1e-6


class BudgetError(RuntimeError):
    """8b budget を検証・確保できない場合の fail-closed 拒否。"""


def _finite_nonnegative(value, *, field: str) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value)) or float(value) < 0):
        raise BudgetError(f"{field} が有限の非負数でない")
    return float(value)


def _nonempty_string(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise BudgetError(f"{field} が空でない文字列でない")
    return value


def _by_holdout_map(value, *, field: str) -> Dict[str, float]:
    if not isinstance(value, Mapping):
        raise BudgetError(f"{field} が object でない")
    projected: Dict[str, float] = {}
    for key, amount in value.items():
        holdout_id = _nonempty_string(key, field=f"{field} key")
        projected[holdout_id] = _finite_nonnegative(
            amount, field=f"{field}.{holdout_id}",
        )
    return projected


def _validate_limits(limits: Mapping) -> dict:
    if not isinstance(limits, Mapping) or set(limits) != _LIMIT_KEYS:
        raise BudgetError("limits schema が不一致")
    total = _finite_nonnegative(limits.get("total_bench_s"), field="total_bench_s")
    per_holdout = limits.get("per_holdout_bench_s")
    if not isinstance(per_holdout, Mapping) or not per_holdout:
        raise BudgetError("per_holdout_bench_s が空でない object でない")
    projected: Dict[str, float] = {}
    for holdout_id, value in per_holdout.items():
        holdout_id = _nonempty_string(holdout_id, field="holdout_id")
        projected[holdout_id] = _finite_nonnegative(
            value, field=f"per_holdout_bench_s.{holdout_id}",
        )
    if limits.get("oracle_shared") is not True:
        raise BudgetError("limits.oracle_shared が true でない")
    return {
        "total_bench_s": total,
        "per_holdout_bench_s": projected,
        "oracle_shared": True,
    }


def load_oracle_limits(freeze: Mapping) -> dict:
    """freeze の数値 budget を arm 非依存 oracle limit へ射影する。"""
    if not isinstance(freeze, Mapping):
        raise BudgetError("freeze が object でない")
    budget = freeze.get("budget")
    if budget is None:
        raise BudgetError("freeze budget が null のため oracle 台帳を作れない")
    if not isinstance(budget, Mapping) or not budget:
        raise BudgetError("freeze budget が空でない object でない")

    total_keys = [key for key in ("total_bench_s", "B_total_seconds") if key in budget]
    holdout_keys = [
        key for key in ("per_holdout_bench_s", "holdout_bench_s") if key in budget
    ]
    if len(total_keys) != 1 or len(holdout_keys) != 1:
        raise BudgetError("freeze budget の総枠/holdout 枠が一意に射影できない")
    if "oracle_shared" in budget and budget.get("oracle_shared") is not True:
        raise BudgetError("freeze budget.oracle_shared が true でない")
    return _validate_limits({
        "total_bench_s": budget[total_keys[0]],
        "per_holdout_bench_s": budget[holdout_keys[0]],
        "oracle_shared": True,
    })


def _load_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BudgetError(f"budget ledger を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BudgetError("budget ledger top-level が object でない")
    return value


def _atomic_create_json(path: Path, document: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise BudgetError(f"budget ledger は既に存在する: {path}")
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(tmp_name, path)
        except FileExistsError as exc:
            raise BudgetError(f"budget ledger は既に存在する: {path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def _atomic_replace_json(path: Path, document: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def _ledger_lock(path: Path):
    """台帳変更を直列化する O_EXCL lock。reservation/精算/追記を相互排他にする。"""
    lock_path = path.with_name(path.name + ".lock")
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
            raise BudgetError(
                f"budget ledger lock を削除できない: {lock_path}: {exc}"
            ) from exc


def create_ledger(path, *, manifest_sha256, freeze_sha256, schedule_sha256,
                  limits) -> None:
    """空 ledger を create-only で作る。null/空 limit は拒否する。

    台帳 identity は manifest / freeze byte / schedule の三 hash に束縛する。
    """
    manifest_sha256 = _nonempty_string(manifest_sha256, field="manifest_sha256")
    freeze_sha256 = _nonempty_string(freeze_sha256, field="freeze_sha256")
    schedule_sha256 = _nonempty_string(schedule_sha256, field="schedule_sha256")
    if not limits:
        raise BudgetError("limits が null/空")
    document = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "freeze_sha256": freeze_sha256,
        "schedule_sha256": schedule_sha256,
        "limits": _validate_limits(limits),
        "reservation": None,
        "spent": {"bench_s": 0.0, "wall_s": 0.0, "by_holdout": {}},
        "entries": [],
    }
    _atomic_create_json(Path(path), document)


def _validate_entry(entry: Mapping) -> dict:
    if not isinstance(entry, Mapping) or set(entry) != _ENTRY_KEYS:
        raise BudgetError("budget entry schema が不一致")
    out = dict(entry)
    for field in (
        "campaign_id", "block_id", "holdout_id", "configuration_id",
        "outcome", "started_iso", "finished_iso",
    ):
        out[field] = _nonempty_string(out.get(field), field=f"entry.{field}")
    for field in ("schedule_index", "attempt"):
        value = out.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise BudgetError(f"entry.{field} が非負整数でない")
    out["bench_s"] = _finite_nonnegative(out.get("bench_s"), field="entry.bench_s")
    out["wall_s"] = _finite_nonnegative(out.get("wall_s"), field="entry.wall_s")
    return out


def _reaggregate(entries: list[Mapping]) -> dict:
    bench_s = 0.0
    wall_s = 0.0
    by_holdout: Dict[str, float] = {}
    identities = set()
    for raw_entry in entries:
        entry = _validate_entry(raw_entry)
        identity = (
            entry["campaign_id"], entry["block_id"], entry["schedule_index"],
            entry["attempt"],
        )
        if identity in identities:
            raise BudgetError("budget entry identity が重複")
        identities.add(identity)
        bench_s += entry["bench_s"]
        wall_s += entry["wall_s"]
        by_holdout[entry["holdout_id"]] = (
            by_holdout.get(entry["holdout_id"], 0.0) + entry["bench_s"]
        )
    return {"bench_s": bench_s, "wall_s": wall_s, "by_holdout": by_holdout}


def _close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=_TOLERANCE)


def _validate_reservation(reservation, *, aggregated: Mapping, entries: list,
                          limits: Mapping) -> None:
    """reservation の schema・status 別不変・実測束縛・枠上限を検査する。"""
    if reservation is None:
        # 予約前 (create 直後)。この状態では entry は一件もあってはならない。
        if entries:
            raise BudgetError("reservation なしに entry が存在する")
        return
    if not isinstance(reservation, Mapping) or set(reservation) != _RESERVATION_KEYS:
        raise BudgetError("reservation schema が不一致")
    status = reservation.get("status")
    if status not in _RESERVATION_STATUSES:
        raise BudgetError("reservation.status が不正")
    reserved = _finite_nonnegative(
        reservation.get("reserved_bench_s"), field="reservation.reserved_bench_s",
    )
    charged = _finite_nonnegative(
        reservation.get("charged_bench_s"), field="reservation.charged_bench_s",
    )
    actual = _finite_nonnegative(
        reservation.get("actual_bench_s"), field="reservation.actual_bench_s",
    )
    by_reserved = _by_holdout_map(
        reservation.get("by_holdout_reserved"), field="reservation.by_holdout_reserved",
    )
    by_charged = _by_holdout_map(
        reservation.get("by_holdout_charged"), field="reservation.by_holdout_charged",
    )
    _nonempty_string(reservation.get("reserved_iso"), field="reservation.reserved_iso")
    settled_iso = reservation.get("settled_iso")

    # by_holdout 合計整合性: by_holdout_reserved の合計は総 reserved_bench_s と
    # 一致しなければならない (held/settled/exhausted いずれの status でも
    # by_holdout_reserved は reserve/mark_exhausted 時に固定され以後不変)。
    # holdout 網羅性 (schedule の全 holdout を含むか) は呼び手情報が要るため
    # ここでは検査しない (reserve の docstring 参照)。
    if not _close(sum(by_reserved.values()), reserved):
        raise BudgetError(
            "reservation.by_holdout_reserved の合計が reserved_bench_s と不一致"
        )

    # 実測束縛: actual_bench_s は entries の再集計と一致する。
    if not _close(actual, aggregated["bench_s"]):
        raise BudgetError("reservation.actual_bench_s が entries 再集計と不一致")

    if status == "exhausted":
        if entries:
            raise BudgetError("exhausted reservation に entry が存在する")
        if not _close(charged, 0.0) or not _close(actual, 0.0):
            raise BudgetError("exhausted は charged/actual が 0 でない")
        if by_charged:
            raise BudgetError("exhausted は by_holdout_charged が空でない")
        if settled_iso is not None:
            raise BudgetError("exhausted に settled_iso がある")
    elif status == "held":
        if not _close(charged, reserved):
            raise BudgetError("held reservation は charged==reserved でない (非解放)")
        if actual > reserved + _TOLERANCE:
            raise BudgetError("held reservation の実測が予約枠を超過")
        if settled_iso is not None:
            raise BudgetError("held に settled_iso がある")
    else:  # settled
        if not _close(charged, actual):
            raise BudgetError("settled reservation は charged==actual でない")
        _nonempty_string(settled_iso, field="reservation.settled_iso")

    # gate 計上額 charged は枠を超えない (crash 非解放時も held の全枠が枠内)。
    if charged > _finite_nonnegative(
            limits["total_bench_s"], field="limits.total_bench_s") + _TOLERANCE:
        raise BudgetError("reservation charged が総 bench 枠を超過")
    for holdout_id, value in by_charged.items():
        if holdout_id not in limits["per_holdout_bench_s"]:
            raise BudgetError(f"reservation が未知 holdout を計上: {holdout_id}")
        if value > limits["per_holdout_bench_s"][holdout_id] + _TOLERANCE:
            raise BudgetError(f"reservation charged が holdout 枠を超過: {holdout_id}")


def read_ledger(path, *, manifest_sha256, freeze_sha256, schedule_sha256) -> dict:
    """schema、三 hash 束縛、reservation、entries 再集計を完全照合する。"""
    manifest_sha256 = _nonempty_string(manifest_sha256, field="manifest_sha256")
    freeze_sha256 = _nonempty_string(freeze_sha256, field="freeze_sha256")
    schedule_sha256 = _nonempty_string(schedule_sha256, field="schedule_sha256")
    document = _load_json_object(Path(path))
    if set(document) != _TOP_LEVEL_KEYS:
        raise BudgetError("budget ledger top-level schema が不一致")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise BudgetError("budget ledger schema_version が不一致")
    if document.get("manifest_sha256") != manifest_sha256:
        raise BudgetError("budget ledger manifest_sha256 が不一致")
    if document.get("freeze_sha256") != freeze_sha256:
        raise BudgetError("budget ledger freeze_sha256 が不一致")
    if document.get("schedule_sha256") != schedule_sha256:
        raise BudgetError("budget ledger schedule_sha256 が不一致")
    limits = _validate_limits(document.get("limits"))
    spent = document.get("spent")
    entries = document.get("entries")
    if not isinstance(spent, Mapping) or set(spent) != _SPENT_KEYS:
        raise BudgetError("budget ledger spent schema が不一致")
    if not isinstance(entries, list):
        raise BudgetError("budget ledger entries が list でない")
    aggregated = _reaggregate(entries)
    recorded_bench = _finite_nonnegative(spent.get("bench_s"), field="spent.bench_s")
    recorded_wall = _finite_nonnegative(spent.get("wall_s"), field="spent.wall_s")
    recorded_by_holdout = spent.get("by_holdout")
    if not isinstance(recorded_by_holdout, Mapping):
        raise BudgetError("spent.by_holdout が object でない")
    normalised_by_holdout = {
        _nonempty_string(key, field="spent.by_holdout key"):
        _finite_nonnegative(value, field=f"spent.by_holdout.{key}")
        for key, value in recorded_by_holdout.items()
    }
    if (not _close(recorded_bench, aggregated["bench_s"])
            or not _close(recorded_wall, aggregated["wall_s"])
            or set(normalised_by_holdout) != set(aggregated["by_holdout"])
            or any(not _close(normalised_by_holdout[key], aggregated["by_holdout"][key])
                   for key in normalised_by_holdout)):
        raise BudgetError("budget ledger spent と entries 再集計が不一致")
    if recorded_bench > limits["total_bench_s"] + _TOLERANCE:
        raise BudgetError("budget ledger が総 bench 枠を超過")
    for holdout_id, value in normalised_by_holdout.items():
        if holdout_id not in limits["per_holdout_bench_s"]:
            raise BudgetError(f"budget ledger が未知 holdout を含む: {holdout_id}")
        if value > limits["per_holdout_bench_s"][holdout_id] + _TOLERANCE:
            raise BudgetError(f"budget ledger が holdout 枠を超過: {holdout_id}")
    _validate_reservation(
        document.get("reservation"), aggregated=aggregated, entries=entries,
        limits=limits,
    )
    return document


def assert_available(ledger, *, holdout_id, required_bench_s) -> None:
    """総枠と holdout 枠の残量を検査する (計上済み reservation を差し引く)。

    不足時、呼び出し側は当該 cell だけを飛ばさず、残り schedule 全体を停止すること。
    """
    if not isinstance(ledger, Mapping):
        raise BudgetError("ledger が object でない")
    holdout_id = _nonempty_string(holdout_id, field="holdout_id")
    required = _finite_nonnegative(required_bench_s, field="required_bench_s")
    limits = _validate_limits(ledger.get("limits"))
    if holdout_id not in limits["per_holdout_bench_s"]:
        raise BudgetError(f"holdout budget が存在しない: {holdout_id}")

    reservation = ledger.get("reservation")
    if isinstance(reservation, Mapping) and reservation:
        total_spent = _finite_nonnegative(
            reservation.get("charged_bench_s"), field="reservation.charged_bench_s",
        )
        by_holdout = _by_holdout_map(
            reservation.get("by_holdout_charged", {}),
            field="reservation.by_holdout_charged",
        )
    else:
        spent = ledger.get("spent")
        if not isinstance(spent, Mapping) or set(spent) != _SPENT_KEYS:
            raise BudgetError("ledger.spent schema が不一致")
        total_spent = _finite_nonnegative(spent.get("bench_s"), field="spent.bench_s")
        raw_by_holdout = spent.get("by_holdout")
        if not isinstance(raw_by_holdout, Mapping):
            raise BudgetError("spent.by_holdout が object でない")
        by_holdout = _by_holdout_map(raw_by_holdout, field="spent.by_holdout")

    holdout_spent = by_holdout.get(holdout_id, 0.0)
    total_remaining = limits["total_bench_s"] - total_spent
    holdout_remaining = limits["per_holdout_bench_s"][holdout_id] - holdout_spent
    if total_remaining + _TOLERANCE < required:
        raise BudgetError(
            f"総 bench 枠不足: remaining={total_remaining:.6f} required={required:.6f}"
        )
    if holdout_remaining + _TOLERANCE < required:
        raise BudgetError(
            f"holdout bench 枠不足: holdout={holdout_id} "
            f"remaining={holdout_remaining:.6f} required={required:.6f}"
        )


def reserve(path, *, manifest_sha256, freeze_sha256, schedule_sha256,
            reserved_bench_s, by_holdout_reserved, reserved_iso) -> dict:
    """attempt 開始前に全予定行の bench 枠を一括予約する。

    確保できなければ BudgetError を投げ、台帳を変更しない (呼び出し側は `mark_exhausted`
    で terminal を耐久化し一行も走らせない)。確保できれば `charged==reserved` を耐久化し、
    crash では解放しない。既に reservation があれば再予約を拒否する。

    `by_holdout_reserved` の合計が `reserved_bench_s` と一致することを検査する
    (不一致は BudgetError で拒否)。schedule に含まれる全 holdout を
    `by_holdout_reserved` が網羅していること (holdout 網羅性) は、この関数が
    schedule を持たず検査できないため、呼び手が保証する。
    """
    path = Path(path)
    reserved = _finite_nonnegative(reserved_bench_s, field="reserved_bench_s")
    by_reserved = _by_holdout_map(
        by_holdout_reserved, field="by_holdout_reserved",
    )
    if not _close(sum(by_reserved.values()), reserved):
        raise BudgetError(
            "by_holdout_reserved の合計が reserved_bench_s と不一致"
        )
    reserved_iso = _nonempty_string(reserved_iso, field="reserved_iso")
    with _ledger_lock(path):
        document = read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )
        if document.get("reservation") is not None:
            raise BudgetError("既に reservation が存在するため再予約を拒否")
        limits = document["limits"]
        if reserved > limits["total_bench_s"] + _TOLERANCE:
            raise BudgetError(
                f"総 bench 枠を一括予約できない: "
                f"total={limits['total_bench_s']:.6f} required={reserved:.6f}"
            )
        for holdout_id, value in by_reserved.items():
            if holdout_id not in limits["per_holdout_bench_s"]:
                raise BudgetError(f"予約対象に未知 holdout: {holdout_id}")
            if value > limits["per_holdout_bench_s"][holdout_id] + _TOLERANCE:
                raise BudgetError(
                    f"holdout bench 枠を一括予約できない: holdout={holdout_id} "
                    f"limit={limits['per_holdout_bench_s'][holdout_id]:.6f} "
                    f"required={value:.6f}"
                )
        updated = copy.deepcopy(document)
        updated["reservation"] = {
            "status": "held",
            "reserved_bench_s": reserved,
            "charged_bench_s": reserved,
            "actual_bench_s": 0.0,
            "by_holdout_reserved": by_reserved,
            "by_holdout_charged": dict(by_reserved),
            "reserved_iso": reserved_iso,
            "settled_iso": None,
        }
        _atomic_replace_json(path, updated)
        return read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )


def mark_exhausted(path, *, manifest_sha256, freeze_sha256, schedule_sha256,
                   requested_bench_s, by_holdout_requested, reserved_iso) -> dict:
    """一括予約が確保できなかったことを terminal として耐久化する。

    一行も走らせないため entry は空でなければならない。以降 `held` へは遷移しない。
    """
    path = Path(path)
    requested = _finite_nonnegative(requested_bench_s, field="requested_bench_s")
    by_requested = _by_holdout_map(
        by_holdout_requested, field="by_holdout_requested",
    )
    reserved_iso = _nonempty_string(reserved_iso, field="reserved_iso")
    with _ledger_lock(path):
        document = read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )
        if document.get("reservation") is not None:
            raise BudgetError("既に reservation が存在するため exhausted 化を拒否")
        if document.get("entries"):
            raise BudgetError("entry が存在する状態で exhausted 化を拒否")
        updated = copy.deepcopy(document)
        updated["reservation"] = {
            "status": "exhausted",
            "reserved_bench_s": requested,
            "charged_bench_s": 0.0,
            "actual_bench_s": 0.0,
            "by_holdout_reserved": by_requested,
            "by_holdout_charged": {},
            "reserved_iso": reserved_iso,
            "settled_iso": None,
        }
        _atomic_replace_json(path, updated)
        return read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )


def append_entry(path, *, manifest_sha256, freeze_sha256, schedule_sha256,
                 entry) -> dict:
    """held reservation 下で一件を検証・実測計上し、ledger を atomic replace する。

    実測は予約枠 (総枠・holdout 枠) を超えられない (超過は protocol violation として拒否)。
    """
    path = Path(path)
    validated_entry = _validate_entry(entry)
    with _ledger_lock(path):
        document = read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )
        reservation = document.get("reservation")
        if not isinstance(reservation, Mapping) or reservation.get("status") != "held":
            raise BudgetError("held reservation なしに entry を追記できない")
        updated = copy.deepcopy(document)
        updated["entries"].append(validated_entry)
        aggregated = _reaggregate(updated["entries"])
        if aggregated["bench_s"] > reservation["reserved_bench_s"] + _TOLERANCE:
            raise BudgetError("実測 bench 累計が予約枠を超過")
        for holdout_id, value in aggregated["by_holdout"].items():
            cap = reservation["by_holdout_reserved"].get(holdout_id)
            if cap is None or value > cap + _TOLERANCE:
                raise BudgetError(
                    f"holdout 実測 bench が予約枠を超過: {holdout_id}"
                )
        updated["spent"] = aggregated
        updated["reservation"] = {
            **reservation, "actual_bench_s": aggregated["bench_s"],
        }
        _atomic_replace_json(path, updated)
        return read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )


def settle(path, *, manifest_sha256, freeze_sha256, schedule_sha256,
           settled_iso) -> dict:
    """terminal 後に held reservation を実測へ精算する (charged=actual、未使用枠を解放)。"""
    path = Path(path)
    settled_iso = _nonempty_string(settled_iso, field="settled_iso")
    with _ledger_lock(path):
        document = read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )
        reservation = document.get("reservation")
        if not isinstance(reservation, Mapping) or reservation.get("status") != "held":
            raise BudgetError("held reservation がないため精算できない")
        actual = _finite_nonnegative(
            document["spent"]["bench_s"], field="spent.bench_s",
        )
        by_actual = _by_holdout_map(
            document["spent"]["by_holdout"], field="spent.by_holdout",
        )
        updated = copy.deepcopy(document)
        updated["reservation"] = {
            **reservation,
            "status": "settled",
            "charged_bench_s": actual,
            "actual_bench_s": actual,
            "by_holdout_charged": by_actual,
            "settled_iso": settled_iso,
        }
        _atomic_replace_json(path, updated)
        return read_ledger(
            path, manifest_sha256=manifest_sha256,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
        )
