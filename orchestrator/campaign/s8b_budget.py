# -*- coding: utf-8 -*-
"""S-1 と独立した 8b oracle の bench/wall budget 台帳。"""
from __future__ import annotations

import copy
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Dict, Mapping


SCHEMA_VERSION = "8b-budget-ledger/v1"
_TOP_LEVEL_KEYS = {"schema_version", "manifest_sha256", "limits", "spent", "entries"}
_LIMIT_KEYS = {"total_bench_s", "per_holdout_bench_s", "oracle_shared"}
_SPENT_KEYS = {"bench_s", "wall_s", "by_holdout"}
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


def create_ledger(path, *, manifest_sha256, limits) -> None:
    """空 ledger を create-only で作る。null/空 limit は拒否する。"""
    manifest_sha256 = _nonempty_string(manifest_sha256, field="manifest_sha256")
    if not limits:
        raise BudgetError("limits が null/空")
    document = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "limits": _validate_limits(limits),
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


def read_ledger(path, *, manifest_sha256) -> dict:
    """schema、manifest 束縛、entries からの再集計を完全照合する。"""
    manifest_sha256 = _nonempty_string(manifest_sha256, field="manifest_sha256")
    document = _load_json_object(Path(path))
    if set(document) != _TOP_LEVEL_KEYS:
        raise BudgetError("budget ledger top-level schema が不一致")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise BudgetError("budget ledger schema_version が不一致")
    if document.get("manifest_sha256") != manifest_sha256:
        raise BudgetError("budget ledger manifest_sha256 が不一致")
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
    return document


def assert_available(ledger, *, holdout_id, required_bench_s) -> None:
    """総枠と holdout 枠を検査する。

    不足時、呼び出し側は当該 cell だけを飛ばさず、残り schedule 全体を停止すること。
    """
    if not isinstance(ledger, Mapping):
        raise BudgetError("ledger が object でない")
    holdout_id = _nonempty_string(holdout_id, field="holdout_id")
    required = _finite_nonnegative(required_bench_s, field="required_bench_s")
    limits = _validate_limits(ledger.get("limits"))
    spent = ledger.get("spent")
    if not isinstance(spent, Mapping) or set(spent) != _SPENT_KEYS:
        raise BudgetError("ledger.spent schema が不一致")
    if holdout_id not in limits["per_holdout_bench_s"]:
        raise BudgetError(f"holdout budget が存在しない: {holdout_id}")
    total_spent = _finite_nonnegative(spent.get("bench_s"), field="spent.bench_s")
    by_holdout = spent.get("by_holdout")
    if not isinstance(by_holdout, Mapping):
        raise BudgetError("spent.by_holdout が object でない")
    holdout_spent = _finite_nonnegative(
        by_holdout.get(holdout_id, 0.0), field=f"spent.by_holdout.{holdout_id}",
    )
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


def append_entry(path, *, manifest_sha256, entry) -> dict:
    """exclusive lock 下で一件を検証・debit し、ledger を atomic replace する。"""
    path = Path(path)
    manifest_sha256 = _nonempty_string(manifest_sha256, field="manifest_sha256")
    validated_entry = _validate_entry(entry)
    lock_path = path.with_name(path.name + ".lock")
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise BudgetError(f"budget ledger lock が既に存在する: {lock_path}") from exc
    except OSError as exc:
        raise BudgetError(f"budget ledger lock を作れない: {lock_path}: {exc}") from exc
    try:
        os.close(lock_fd)
        document = read_ledger(path, manifest_sha256=manifest_sha256)
        assert_available(
            document,
            holdout_id=validated_entry["holdout_id"],
            required_bench_s=validated_entry["bench_s"],
        )
        updated = copy.deepcopy(document)
        updated["entries"].append(validated_entry)
        updated["spent"] = _reaggregate(updated["entries"])
        _atomic_replace_json(path, updated)
        return read_ledger(path, manifest_sha256=manifest_sha256)
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise BudgetError(f"budget ledger lock を削除できない: {lock_path}: {exc}") from exc
