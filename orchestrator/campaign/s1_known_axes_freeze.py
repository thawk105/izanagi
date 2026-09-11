# -*- coding: utf-8 -*-
"""S-1 既知軸基準点と系側構成を機械抽出して凍結・照合する。

使い方:
  python3 orchestrator/campaign/s1_known_axes_freeze.py generate
  python3 orchestrator/campaign/s1_known_axes_freeze.py verify
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent

from . import axis_trigger_gating as trigger_axis  # noqa: E402
from . import backoff_sweep, genome, s6_sort_sweep, s8a_trigger_sweep  # noqa: E402
from . import sort_comparator_authority  # noqa: E402
from . import trigger_gate_binding  # noqa: E402
from . import freeze_verification_hold as _freeze_hold  # noqa: E402
from .model import Genome  # noqa: E402
from .pipeline import variant_id  # noqa: E402


ROOT = _ORCHESTRATOR.parent
SCRIPT_REL = "orchestrator/campaign/s1_known_axes_freeze.py"
FREEZE_REL = "output/s1-freeze/known_axes_freeze.json"
FREEZE_PATH = ROOT / FREEZE_REL

WORKLOADS = ("balanced", "write-heavy", "read-heavy")
EXPECTED_P2 = {
    "balanced": ("5185ee5e6094", 2752621.0),
    "write-heavy": ("5185ee5e6094", 1872376.0),
    "read-heavy": ("b971a1d9f80a", 8487844.0),
}
EXPECTED_BACKOFF = {"balanced": 5, "write-heavy": 10, "read-heavy": 2}
EXPECTED_SORT = {"balanced": "sp_dd", "write-heavy": "sk_ad"}
EXPECTED_GATES = {"balanced": "g_rl", "write-heavy": "g_rt", "read-heavy": "g_rl"}

SORT_MAIN = {
    "balanced": "p3-s6-sort-sweep-balanced-sweep-dd25aa8c",
    "write-heavy": "p3-s6-sort-sweep-write-heavy-sweep-0484feef",
}
SORT_BALANCED_REMEASURE = "p3-s6-sort-sweep-balanced-sweep-1b39095e"
TRIGGER_REMEASURE = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb",
    "read-heavy": "p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7",
}
TRIGGER_MAIN = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-c2d838b8",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8",
    "read-heavy": "p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c",
}

RECON_REL = "output/insights/2026-07-11_s8a-trigger-gating-recon.md"
PHASE_MAIN_REL = "docs/phase3-main-experiment.md"
SORT_INSIGHT_REL = "output/insights/2026-07-10_s6-sort-sweep-preliminary.md"
OPTIONS_REL = "external/ccbench/cmake/Options.cmake"
SILO_CMAKE_REL = "external/ccbench/cc/silo/CMakeLists.txt"

TOP_LEVEL_KEYS = {
    "what", "frozen_at_head", "ccbench_pin", "generator", "python_version",
    "selection_rules", "entries", "s1b_pairing", "reference_values_note",
}
ENTRY_KEYS = {
    "system_gate", "ident_all", "p2_2_flag_opt", "backoff_fixed_best",
    "sort_best", "stock_common",
}


class FreezeError(RuntimeError):
    """凍結生成・照合を fail-closed で止めるエラー。"""


def _require_sort_name_comparator_binding(
        name: object, comparator: object, *, workload: str) -> None:
    try:
        sort_comparator_authority.require_sort_name_comparator_binding(
            name, comparator)
    except sort_comparator_authority.SortComparatorAuthorityError as e:
        raise FreezeError(
            f"entries.{workload}.sort_best.name/comparator が権威集合と不一致") from e


def _require_canonical_trigger_predicate(
        predicate: object, *, workload: str, configuration: str) -> None:
    if not trigger_gate_binding.is_canonical_predicate(predicate):
        raise FreezeError(
            f"entries.{workload}.{configuration}.gate_predicate が正準集合外")


def _trigger_reasons_for_mask(mask: int) -> Tuple[str, ...]:
    return tuple(
        reason
        for bit, reason in enumerate(trigger_axis.GATEABLE_REASONS)
        if mask & (1 << bit)
    )


def _build_trigger_name_mask_index() -> Dict[str, int]:
    index: Dict[str, int] = {}
    for mask in range(32):
        name = s8a_trigger_sweep.subset_name(_trigger_reasons_for_mask(mask))
        if type(name) is not str:
            raise FreezeError(
                "trigger subset name が非文字列: "
                f"type={type(name).__name__}")
        if name in index:
            raise FreezeError(
                f"trigger subset name が mask 間で重複: {name!r}")
        index[name] = mask

    alias = s8a_trigger_sweep.IDENT_NAME
    all_mask = (1 << len(trigger_axis.GATEABLE_REASONS)) - 1
    if all_mask != 31:
        raise FreezeError(f"trigger 要因数から得た全 mask が 31 でない: {all_mask}")
    if type(alias) is not str:
        raise FreezeError(
            "trigger ident_all alias が非文字列: "
            f"type={type(alias).__name__}")
    if alias in index:
        raise FreezeError(
            f"trigger ident_all alias が既存名と衝突: {alias!r}")
    index[alias] = all_mask
    return index


_TRIGGER_NAME_MASK_BINDING_CACHE: Optional[
    Tuple[Dict[str, int], Tuple[Tuple[str, ...], ...]]
] = None


def _trigger_name_mask_binding_index(
) -> Tuple[Dict[str, int], Tuple[Tuple[str, ...], ...]]:
    global _TRIGGER_NAME_MASK_BINDING_CACHE
    cached = _TRIGGER_NAME_MASK_BINDING_CACHE
    if cached is None:
        index = _build_trigger_name_mask_index()
        expected_names_by_mask = tuple(
            tuple(
                name
                for name, indexed_mask in index.items()
                if indexed_mask == mask
            )
            for mask in range(32)
        )
        cached = (index, expected_names_by_mask)
        _TRIGGER_NAME_MASK_BINDING_CACHE = cached
    return cached


def _require_trigger_name_mask_binding(
        name: object, predicate: object, *,
        workload: str, configuration: str) -> None:
    _require_canonical_trigger_predicate(
        predicate, workload=workload, configuration=configuration)
    predicate_mask = trigger_gate_binding.mask_for_canonical_predicate(predicate)
    name_mask_index, expected_names_by_mask = _trigger_name_mask_binding_index()
    expected_names = expected_names_by_mask[predicate_mask]

    def reject() -> None:
        raise FreezeError(
            f"entries.{workload}.{configuration}.name と gate_predicate の mask が不一致: "
            f"name={name!r} predicate_mask={predicate_mask} "
            f"expected_names={expected_names!r}")

    if type(name) is not str:
        raise FreezeError(
            f"entries.{workload}.{configuration}.name と gate_predicate の mask が不一致: "
            f"name_type={type(name).__name__}")
    if name not in name_mask_index:
        reject()
    if name_mask_index[name] != predicate_mask:
        reject()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_git(args: Sequence[str], cwd: Path = ROOT) -> str:
    try:
        p = subprocess.run(["git", *args], cwd=cwd, check=True, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as e:
        detail = getattr(e, "stderr", "") or str(e)
        raise FreezeError(f"git {' '.join(args)} に失敗: {detail.strip()}") from e
    return p.stdout.strip()


def _source(path_rel: str, key: str, *, lines: Optional[List[str]] = None) -> Dict:
    path = ROOT / path_rel
    if not path.is_file():
        raise FreezeError(f"source が存在しない: {path_rel}")
    out = {"path": path_rel, "sha256": _sha256(path), "key": key}
    if lines is not None:
        out["lines"] = lines
    return out


def _module_source(module, key: str) -> Dict:
    path = Path(module.__file__).resolve()
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError as e:
        raise FreezeError(f"repo 外 module は source にできない: {path}") from e
    return _source(rel, key)


def _load_json(path: Path) -> Dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise FreezeError(f"JSON を読めない: {path}: {e}") from e
    if not isinstance(value, dict):
        raise FreezeError(f"JSON top-level が object ではない: {path}")
    return value


def _wal_records(path: Path) -> List[Dict]:
    records: List[Dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise FreezeError(f"WAL を読めない: {path}: {e}") from e
    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            raise FreezeError(f"WAL JSON 不正: {path}:{lineno}: {e}") from e
        if not isinstance(record, dict):
            raise FreezeError(f"WAL record が object ではない: {path}:{lineno}")
        records.append(record)
    return records


def _exclude_screening_campaigns(paths: Sequence[Path]) -> List[Path]:
    """bench-first screening campaign (D58) を S-1 材料から除外する。

    screening campaign は偵察専用で、S-1 の基準点材料に流用しない (D58 firewall)。
    判別子は campaign.lock の search_config に焼き込まれた screening キー
    (pipeline の機械結合が evaluate 前に保証する)。lock が読めない campaign は
    素性不明なので fails-closed で止める。
    """
    kept: List[Path] = []
    for path in paths:
        lock_path = path.parent.parent / "campaign.lock"
        if not lock_path.is_file():
            raise FreezeError(f"campaign.lock がない: {lock_path}")
        lock = _load_json(lock_path)
        search_config = lock.get("search_config")
        if not isinstance(search_config, dict):
            raise FreezeError(f"campaign.lock に search_config がない: {lock_path}")
        if "screening" in search_config:
            continue
        kept.append(path)
    return kept


def _commit_rows(paths: Sequence[Path]) -> Tuple[List[Dict], Dict[str, str]]:
    rows: List[Dict] = []
    genomes: Dict[str, str] = {}
    seen_commit: set[Tuple[str, str]] = set()
    for path in paths:
        for record in _wal_records(path):
            variant = record.get("variant")
            if not isinstance(variant, str):
                raise FreezeError(f"variant 欠落: {path}")
            if record.get("stage") == "build_start":
                canonical = (record.get("payload") or {}).get("genome")
                if canonical is not None:
                    if not isinstance(canonical, str):
                        raise FreezeError(f"genome が文字列でない: {path} variant={variant}")
                    old = genomes.setdefault(variant, canonical)
                    if old != canonical:
                        raise FreezeError(f"同一 variant の genome が不一致: {variant}")
            if record.get("stage") != "commit":
                continue
            key = (path.as_posix(), variant)
            if key in seen_commit:
                raise FreezeError(f"同一 WAL に COMMIT が重複: {path} variant={variant}")
            seen_commit.add(key)
            fitness = (record.get("payload") or {}).get("fitness_tps")
            if not isinstance(fitness, (int, float)) or isinstance(fitness, bool):
                raise FreezeError(f"COMMIT fitness_tps が数値でない: {path} variant={variant}")
            rows.append({"variant": variant, "fitness_tps": float(fitness), "path": path})
    if not rows:
        raise FreezeError("COMMIT 済み variant が 1 件もない")
    return rows, genomes


def _unique_argmax(rows: Sequence[Dict], label: str, key: str = "fitness_tps") -> Dict:
    best_value = max(row[key] for row in rows)
    best = [row for row in rows if row[key] == best_value]
    if len(best) != 1:
        raise FreezeError(f"{label}: argmax が一意でない ({len(best)} 件, {key}={best_value})")
    return best[0]


def _parse_canonical(canonical: str) -> Genome:
    try:
        protocol, body = canonical.split("|", 1)
        flags = {}
        for item in body.split(","):
            name, raw = item.split("=", 1)
            flags[name] = int(raw)
    except (ValueError, TypeError) as e:
        raise FreezeError(f"canonical genome を解釈できない: {canonical!r}") from e
    return Genome(protocol, flags)


def _reverse_p2_variant(variant: str) -> Genome:
    matches = [g for g in genome.SILO_SPACE.enumerate() if variant_id(g) == variant]
    if len(matches) != 1:
        raise FreezeError(f"SILO_SPACE から variant_id を一意に逆引きできない: {variant}")
    return matches[0]


def _p2_label(flags: Mapping[str, int]) -> str:
    lock = flags.get("NO_WAIT_LOCKING_IN_VALIDATION")
    tictoc = flags.get("NO_WAIT_OF_TICTOC")
    if (lock, tictoc) == (1, 0):
        middle = "L"
    elif (lock, tictoc) == (0, 1):
        middle = "T"
    else:
        raise FreezeError(f"P2-2 no-wait flags が既知ラベルに対応しない: {dict(flags)}")
    return f"B{flags['BACK_OFF']}-{middle}-W{flags['WAL']}"


def _p2_entry(workload: str) -> Tuple[Dict, str]:
    paths = _exclude_screening_campaigns(sorted(ROOT.glob(
        f"output/campaigns/p2-2-silo-{workload}-enumerate-*/runs/wal.jsonl")))
    if not paths:
        raise FreezeError(f"P2-2 WAL がない: workload={workload}")
    rows, wal_genomes = _commit_rows(paths)
    best = _unique_argmax(rows, f"P2-2 {workload}")
    expected_variant, expected_fitness = EXPECTED_P2[workload]
    if (best["variant"], best["fitness_tps"]) != (expected_variant, expected_fitness):
        raise FreezeError(
            f"P2-2 {workload}: argmax が期待値と不一致: "
            f"actual={(best['variant'], best['fitness_tps'])} "
            f"expected={(expected_variant, expected_fitness)}")

    canonical = wal_genomes.get(best["variant"])
    if canonical is not None:
        selected = _parse_canonical(canonical)
        method = "WAL の build_start.payload.genome を採用"
    else:
        selected = _reverse_p2_variant(best["variant"])
        method = "WAL に genome が無いため SILO_SPACE 列挙と variant_id 再計算で逆引き"
    if variant_id(selected) != best["variant"]:
        raise FreezeError(f"P2-2 {workload}: genome と variant_id が一致しない")
    sources = [_source(p.relative_to(ROOT).as_posix(), "stage=commit/build_start")
               for p in paths]
    sources.append(_module_source(genome, "SILO_SPACE fallback definition"))
    return ({
        "variant": best["variant"],
        "label": _p2_label(selected.flags),
        "flags": dict(selected.flags),
        "reference_fitness_tps": best["fitness_tps"],
        "sources": sources,
    }, method)


def _backoff_entry(workload: str) -> Dict:
    paths = _exclude_screening_campaigns(sorted(ROOT.glob(
        f"output/campaigns/backoff-sweep-silo-{workload}-sweep-*/runs/wal.jsonl")))
    if not paths:
        raise FreezeError(f"BACKOFF_FIXED WAL がない: workload={workload}")
    rows, wal_genomes = _commit_rows(paths)
    candidates: List[Dict] = []
    references: Dict[str, Dict] = {}
    for row in rows:
        canonical = wal_genomes.get(row["variant"])
        if canonical is None:
            raise FreezeError(f"backoff WAL に genome がない: {row['variant']}")
        flags = _parse_canonical(canonical).flags
        row = {**row, "flags": dict(flags), "backoff_us": flags.get("BACKOFF_FIXED")}
        if flags.get("BACK_OFF") == 1 and row["backoff_us"] in backoff_sweep.SWEEP_US:
            candidates.append(row)
        elif flags.get("BACK_OFF") == 0 and row["backoff_us"] == -1:
            if "no_backoff" in references:
                raise FreezeError(f"BACKOFF_FIXED {workload}: no_backoff 点が重複")
            references["no_backoff"] = row
        elif flags.get("BACK_OFF") == 1 and row["backoff_us"] == -1:
            if "stock_adaptive" in references:
                raise FreezeError(f"BACKOFF_FIXED {workload}: stock_adaptive 点が重複")
            references["stock_adaptive"] = row
    if {row["backoff_us"] for row in candidates} != set(backoff_sweep.SWEEP_US):
        raise FreezeError(f"BACKOFF_FIXED {workload}: 静的 grid が SWEEP_US と一致しない")
    if set(references) != {"no_backoff", "stock_adaptive"}:
        raise FreezeError(f"BACKOFF_FIXED {workload}: 参考 2 点が揃っていない")
    best = _unique_argmax(candidates, f"BACKOFF_FIXED {workload}")
    if best["backoff_us"] != EXPECTED_BACKOFF[workload]:
        raise FreezeError(
            f"BACKOFF_FIXED {workload}: argmax={best['backoff_us']}us "
            f"!= expected={EXPECTED_BACKOFF[workload]}us")
    expected_flags = {**backoff_sweep._BASE, "BACK_OFF": 1,
                      "BACKOFF_FIXED": best["backoff_us"]}
    if best["flags"] != expected_flags:
        raise FreezeError(f"BACKOFF_FIXED {workload}: WAL flags と driver 定数が不一致")
    sources = [_source(p.relative_to(ROOT).as_posix(), "stage=commit/build_start")
               for p in paths]
    sources.append(_module_source(backoff_sweep, "_BASE and SWEEP_US"))
    return {
        "backoff_us": best["backoff_us"],
        "flags": expected_flags,
        "reference_fitness_tps": best["fitness_tps"],
        "reference_points": {
            name: {"flags": ref["flags"],
                   "reference_fitness_tps": ref["fitness_tps"]}
            for name, ref in sorted(references.items())
        },
        "sources": sources,
    }


def _campaign_file(campaign: str, relative: str) -> Path:
    path = ROOT / "output/campaigns" / campaign / relative
    if not path.is_file():
        raise FreezeError(f"campaign artifact がない: {path.relative_to(ROOT)}")
    return path


def _named_commit_rows(wal_path: Path, provenance_path: Path) -> Tuple[List[Dict], Dict]:
    prov = _load_json(provenance_path)
    entries = prov.get("entries")
    if not isinstance(entries, dict):
        raise FreezeError(f"provenance entries が object でない: {provenance_path}")
    commits, _ = _commit_rows([wal_path])
    by_variant: Dict[str, str] = {}
    for name, entry in entries.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("variant_id"), str):
            continue
        variant = entry["variant_id"]
        if variant in by_variant:
            raise FreezeError(f"provenance variant_id が重複: {provenance_path} {variant}")
        by_variant[variant] = name
    rows = []
    for commit in commits:
        name = by_variant.get(commit["variant"])
        if name is None:
            raise FreezeError(
                f"COMMIT variant が provenance にない: {provenance_path} {commit['variant']}")
        rows.append({**commit, "name": name,
                     "category": entries[name].get("category")})
    return rows, prov


def _find_sort_remeasure(workload: str) -> Tuple[Path, Path]:
    found: List[Tuple[Path, Path]] = []
    for prov_path in sorted(ROOT.glob(
            f"output/campaigns/p3-s6-sort-sweep-{workload}-sweep-*/"
            "reports/s6_sort_sweep_provenance.json")):
        prov = _load_json(prov_path)
        if str(prov.get("trial", "")).startswith("p3-s6-sort-sweep-remeasure"):
            wal_path = prov_path.parent.parent / "runs/wal.jsonl"
            if wal_path.is_file() and _exclude_screening_campaigns([wal_path]):
                found.append((wal_path, prov_path))
    if len(found) != 1:
        raise FreezeError(f"sort remeasure が一意でない: workload={workload} count={len(found)}")
    return found[0]


def _remeasure_reference(wal_path: Path, prov_path: Path) -> Dict:
    rows, _ = _named_commit_rows(wal_path, prov_path)
    full_order = [row for row in rows if row["category"] == "full-order"]
    if not full_order:
        raise FreezeError(f"sort remeasure に full-order COMMIT がない: {prov_path}")
    best = _unique_argmax(full_order, f"sort remeasure full-order {prov_path}")
    return {"argmax_name": best["name"],
            "reference_fitness_tps": best["fitness_tps"]}


def _sort_entry(workload: str) -> Dict:
    if workload == "read-heavy":
        write_campaign = SORT_MAIN["write-heavy"]
        prov_path = _campaign_file(
            write_campaign, "reports/s6_sort_sweep_provenance.json")
        prov = _load_json(prov_path)
        try:
            comparator = prov["entries"]["sk_ad"]["implementation"]
        except (KeyError, TypeError) as e:
            raise FreezeError("write-heavy 本走 provenance に entries.sk_ad.implementation がない") from e
        if not isinstance(comparator, str):
            raise FreezeError("entries.sk_ad.implementation が文字列でない")
        _require_sort_name_comparator_binding(
            "sk_ad", comparator, workload=workload)
        flags = dict(s6_sort_sweep._genome(1).flags)
        return {
            "name": "sk_ad", "flags": flags, "comparator": comparator,
            "note": "read-heavy は sweep 未実施。D52 §2.1 の事前固定 sk_ad を採用し、comparator は write-heavy 本走 provenance から流用。",
            "sources": [
                _source(PHASE_MAIN_REL, "D52 2026-07-12追記: read-heavy sk_ad事前固定"),
                _source(prov_path.relative_to(ROOT).as_posix(), "entries.sk_ad.implementation"),
                _module_source(s6_sort_sweep, "_genome(1) and candidate space"),
                _module_source(s6_sort_sweep.S, "_BASE used by _genome(1)"),
            ],
        }

    campaign = SORT_MAIN[workload]
    wal_path = _campaign_file(campaign, "runs/wal.jsonl")
    prov_path = _campaign_file(campaign, "reports/s6_sort_sweep_provenance.json")
    rows, prov = _named_commit_rows(wal_path, prov_path)
    # s6_sort_sweep のレポート契約どおり、性能地形の比較候補は valid な
    # full-order 点。degenerate と stock は別掲対照で argmax 母集団に入れない。
    full_order = [row for row in rows if row["category"] == "full-order"]
    if not full_order:
        raise FreezeError(f"sort main {workload}: full-order COMMIT がない")
    best = _unique_argmax(full_order, f"sort main full-order {workload}")
    if best["name"] != EXPECTED_SORT[workload]:
        raise FreezeError(
            f"sort {workload}: argmax={best['name']} != expected={EXPECTED_SORT[workload]}")
    try:
        comparator = prov["entries"][best["name"]]["implementation"]
    except (KeyError, TypeError) as e:
        raise FreezeError(f"sort provenance implementation がない: {best['name']}") from e
    if not isinstance(comparator, str):
        raise FreezeError(f"sort comparator が文字列でない: {best['name']}")
    _require_sort_name_comparator_binding(
        best["name"], comparator, workload=workload)

    re_wal, re_prov = _find_sort_remeasure(workload)
    if workload == "balanced":
        expected = ROOT / "output/campaigns" / SORT_BALANCED_REMEASURE
        if re_wal.parent.parent != expected:
            raise FreezeError(f"balanced remeasure campaign が期待値と不一致: {re_wal}")
        note = ("本走 argmax 規則により sp_dd を固定。balanced の sp_dd は remeasure campaign "
                "p3-s6-sort-sweep-balanced-sweep-1b39095e で floor 超を再現せず、D46 裁定は差なし。")
    else:
        note = "本走 argmax 規則で固定。remeasure は参考値としてのみ併記し、再選定には使わない。"
    return {
        "name": best["name"],
        "flags": dict(s6_sort_sweep._genome(1).flags),
        "comparator": comparator,
        "note": note,
        "remeasure_reference": _remeasure_reference(re_wal, re_prov),
        "sources": [
            _source(wal_path.relative_to(ROOT).as_posix(), "stage=commit argmax"),
            _source(prov_path.relative_to(ROOT).as_posix(),
                    f"entries.{best['name']}.implementation"),
            _source(re_wal.relative_to(ROOT).as_posix(), "remeasure stage=commit reference"),
            _source(re_prov.relative_to(ROOT).as_posix(), "remeasure name mapping"),
            _source(SORT_INSIGHT_REL, "D46 main/remeasure interpretation"),
            _module_source(s6_sort_sweep, "_genome(1) and candidate space"),
            _module_source(s6_sort_sweep.S, "_BASE used by _genome(1)"),
        ],
    }


def _fixed_gates_from_recon() -> Dict[str, str]:
    text = (ROOT / RECON_REL).read_text(encoding="utf-8")
    pattern = re.compile(
        r"^\|\s*(balanced|write-heavy|read-heavy)\s*\|\s*([a-z0-9_+]+)\s*\|",
        re.MULTILINE)
    found = {workload: gate for workload, gate in pattern.findall(text)}
    if set(found) != set(WORKLOADS):
        raise FreezeError(f"D50 best gate 表を一意に抽出できない: {found}")
    if found != EXPECTED_GATES:
        raise FreezeError(f"D50 best gate 表が期待値と不一致: {found}")
    return found


def _trigger_entries(workload: str, gate_name: str) -> Tuple[Dict, Dict]:
    re_campaign = TRIGGER_REMEASURE[workload]
    main_campaign = TRIGGER_MAIN[workload]
    re_path = _campaign_file(
        re_campaign, "reports/s8a_trigger_sweep_provenance.json")
    main_path = _campaign_file(
        main_campaign, "reports/s8a_trigger_sweep_provenance.json")
    re_prov, main_prov = _load_json(re_path), _load_json(main_path)
    flags = dict(s8a_trigger_sweep._genome(1).flags)
    expected_flags = dict(trigger_axis._BASE)
    if flags != expected_flags:
        raise FreezeError("s8a_trigger_sweep._genome(1) と axis_trigger_gating._BASE が不一致")

    def implementation(prov: Dict, name: str, label: str) -> str:
        try:
            value = prov["entries"][name]["implementation"]
        except (KeyError, TypeError) as e:
            raise FreezeError(f"{label} provenance に entries.{name}.implementation がない") from e
        if not isinstance(value, str):
            raise FreezeError(f"{label} entries.{name}.implementation が文字列でない")
        return value

    gate_predicate = implementation(re_prov, gate_name, "remeasure")
    _require_trigger_name_mask_binding(
        gate_name, gate_predicate,
        workload=workload, configuration="system_gate")
    if gate_predicate != implementation(main_prov, gate_name, "main"):
        raise FreezeError(f"trigger gate predicate が main/remeasure で不一致: {workload} {gate_name}")
    ident_predicate = implementation(re_prov, "ident_all", "remeasure")
    _require_trigger_name_mask_binding(
        "ident_all", ident_predicate,
        workload=workload, configuration="ident_all")
    if ident_predicate != implementation(main_prov, "ident_all", "main"):
        raise FreezeError(f"ident_all predicate が main/remeasure で不一致: {workload}")
    common_module_sources = [
        _module_source(trigger_axis, "_BASE"),
        _module_source(s8a_trigger_sweep, "_genome(1)"),
    ]
    gate = {
        "name": gate_name,
        "flags": copy.deepcopy(flags),
        "gate_predicate": gate_predicate,
        "sources": [
            _source(RECON_REL, f"floor超地形 best gate table: {workload}"),
            _source(re_path.relative_to(ROOT).as_posix(),
                    f"entries.{gate_name}.implementation"),
            _source(main_path.relative_to(ROOT).as_posix(),
                    f"entries.{gate_name}.implementation equality assertion"),
            *common_module_sources,
        ],
    }
    ident = {
        "name": "ident_all",
        "flags": copy.deepcopy(flags),
        "gate_predicate": ident_predicate,
        "sources": [
            _source(re_path.relative_to(ROOT).as_posix(),
                    "entries.ident_all.implementation"),
            _source(main_path.relative_to(ROOT).as_posix(),
                    "entries.ident_all.implementation equality assertion"),
            *common_module_sources,
        ],
    }
    return gate, ident


def _unique_cmake_line(text: str, pattern: str, label: str) -> Tuple[int, str]:
    regex = re.compile(pattern)
    found = [(i, line) for i, line in enumerate(text.splitlines(), 1) if regex.search(line)]
    if len(found) != 1:
        raise FreezeError(f"{label} の CMake 行が一意でない: {len(found)} 件")
    return found[0]


def _stock_common() -> Dict:
    options_text = (ROOT / OPTIONS_REL).read_text(encoding="utf-8")
    silo_text = (ROOT / SILO_CMAKE_REL).read_text(encoding="utf-8")
    defaults: Dict[str, int] = {}
    option_lines: List[str] = []
    for flag in ("BACK_OFF", "NO_WAIT_LOCKING_IN_VALIDATION", "NO_WAIT_OF_TICTOC", "WAL"):
        line_no, line = _unique_cmake_line(
            options_text,
            rf"^\s*set\(CCBENCH_{re.escape(flag)}\s+(-?\d+)\s+CACHE\s+STRING\b",
            f"CCBENCH_{flag} default")
        match = re.search(rf"set\(CCBENCH_{re.escape(flag)}\s+(-?\d+)", line)
        assert match is not None
        defaults[flag] = int(match.group(1))
        option_lines.append(f"{line_no}: {line}")

    universal_no, universal_line = _unique_cmake_line(
        options_text, r"^\s*BACK_OFF=\$\{CCBENCH_BACK_OFF\}\s*$", "BACK_OFF universal mapping")
    option_lines.append(f"{universal_no}: {universal_line}")
    silo_lines: List[str] = []
    for flag in ("NO_WAIT_LOCKING_IN_VALIDATION", "NO_WAIT_OF_TICTOC", "WAL"):
        line_no, line = _unique_cmake_line(
            silo_text,
            rf"^\s*{re.escape(flag)}=\$\{{CCBENCH_{re.escape(flag)}\}}\s*$",
            f"silo {flag} mapping")
        silo_lines.append(f"{line_no}: {line}")
    return {
        "flags": defaults,
        "sources": [
            _source(OPTIONS_REL, "four CACHE defaults and BACK_OFF universal mapping",
                    lines=option_lines),
            _source(SILO_CMAKE_REL, "silo target mappings for three protocol flags",
                    lines=silo_lines),
        ],
    }


def assert_s1b_pairing(doc: Mapping) -> None:
    entries = doc.get("entries")
    pairings = doc.get("s1b_pairing")
    if not isinstance(entries, dict) or not isinstance(pairings, list):
        raise FreezeError("s1b_pairing 検査に必要な entries/list がない")
    by_workload: Dict[str, Mapping] = {}
    for pair in pairings:
        if not isinstance(pair, dict) or not isinstance(pair.get("workload"), str):
            raise FreezeError("s1b_pairing entry が不正")
        workload = pair["workload"]
        if workload in by_workload:
            raise FreezeError(f"s1b_pairing workload 重複: {workload}")
        by_workload[workload] = pair
    if set(by_workload) != set(WORKLOADS):
        raise FreezeError(f"s1b_pairing workload 集合が不一致: {sorted(by_workload)}")
    for workload in WORKLOADS:
        entry = entries.get(workload)
        if not isinstance(entry, dict):
            raise FreezeError(f"entries.{workload} がない")
        gate, ident, pair = entry.get("system_gate"), entry.get("ident_all"), by_workload[workload]
        if not isinstance(gate, dict) or not isinstance(ident, dict):
            raise FreezeError(f"entries.{workload} の gate/ident_all が不正")
        identical = gate.get("flags") == ident.get("flags")
        if not identical:
            raise FreezeError(f"s1b_pairing flags 不一致: {workload}")
        try:
            gate_mask = trigger_gate_binding.mask_for_canonical_predicate(
                gate.get("gate_predicate"))
            ident_mask = trigger_gate_binding.mask_for_canonical_predicate(
                ident.get("gate_predicate"))
        except trigger_gate_binding.TriggerGateBindingError as e:
            raise FreezeError(
                f"s1b_pairing predicate が正準集合外: {workload}") from e
        if gate_mask == ident_mask:
            raise FreezeError(f"s1b_pairing predicate 差分がない: {workload}")
        expected = {"workload": workload, "gate_on": gate.get("name"),
                    "gate_off": ident.get("name"), "flags_identical": True}
        if pair != expected or not pair.get("flags_identical"):
            raise FreezeError(f"s1b_pairing 台帳が entry と不一致: {workload}")


def build_document(*, frozen_at_head: Optional[str] = None,
                   ccbench_pin: Optional[str] = None,
                   python_version: Optional[str] = None,
                   generator_sha: Optional[str] = None) -> Dict:
    p2_entries: Dict[str, Dict] = {}
    p2_methods: set[str] = set()
    for workload in WORKLOADS:
        p2_entries[workload], method = _p2_entry(workload)
        p2_methods.add(method)
    gates = _fixed_gates_from_recon()
    stock = _stock_common()
    entries: Dict[str, Dict] = {}
    for workload in WORKLOADS:
        gate, ident = _trigger_entries(workload, gates[workload])
        entries[workload] = {
            "system_gate": gate,
            "ident_all": ident,
            "p2_2_flag_opt": p2_entries[workload],
            "backoff_fixed_best": _backoff_entry(workload),
            "sort_best": _sort_entry(workload),
            "stock_common": copy.deepcopy(stock),
        }
    doc = {
        "what": "S-1 既知軸基準点 + 系側構成の凍結 (D52 §2.1 の実体化)",
        "frozen_at_head": frozen_at_head or _run_git(["rev-parse", "HEAD"]),
        "ccbench_pin": ccbench_pin or _run_git(["rev-parse", "HEAD"], ROOT / "external/ccbench"),
        "generator": {
            "path": SCRIPT_REL,
            "sha256": generator_sha or _sha256(ROOT / SCRIPT_REL),
        },
        "python_version": python_version or sys.version,
        "selection_rules": {
            "p2_2": (
                "workload 別 p2-2-silo-<wl>-enumerate-*/runs/wal.jsonl の COMMIT 済み全 variant から "
                "fitness_tps の一意な argmax を選ぶ。同値最大は停止。flags 取得方法: "
                + " / ".join(sorted(p2_methods))
                + "。期待 variant/fitness と不一致なら停止。"),
            "backoff_fixed": (
                "workload 別 backoff-sweep WAL のうち backoff_sweep.SWEEP_US に含まれる静的 "
                "BACKOFF_FIXED grid 点だけから fitness_tps の一意な argmax を選ぶ。同値最大は停止。"
                "BACKOFF_FIXED=-1 の無 backoff 点と stock 適応点は選定外で reference_points に併記し、"
                "flags は backoff_sweep._BASE + BACK_OFF=1 + 選定値から構成する。期待 us と不一致なら停止。"),
            "sort": (
                "balanced/write-heavy は指定した本走 campaign の COMMIT と provenance name/category 対応から、"
                "s6_sort_sweep レポート契約の valid full-order 点を候補に fitness_tps の一意な argmax を選ぶ。"
                "degenerate 点と stock は候補外。implementation を同 provenance から逐語取得する。"
                "remeasure は reference のみで再選定しない。read-heavy は sweep 未実施のため D52 §2.1 の "
                "sk_ad を事前固定し、comparator は write-heavy 本走 provenance entries.sk_ad.implementation "
                "を逐語流用する。flags は s6_sort_sweep._genome(1) 由来。"),
            "system_gate": (
                "機械 argmax は行わず、D50 recon の workload 別 best gate 表を機械読取して "
                "balanced=g_rl/write-heavy=g_rt/read-heavy=g_rl に事前固定する。述語は workload 別 remeasure "
                "provenance から逐語取得し、本走 provenance の同名 implementation と完全一致を要求する。"
                "ident_all も同じ provenance から取得し、flags は axis_trigger_gating._BASE 由来で gate_on/off "
                "完全一致を要求する。"),
            "stock_common": (
                "external/ccbench/cmake/Options.cmake の一意な CCBENCH_* CACHE 既定を読み、BACK_OFF の "
                "universal mapping と cc/silo/CMakeLists.txt の silo mapping を照合して出荷既定を確定する。"
                "4 フラグの既定または配線が一意でなければ停止する。"),
        },
        "entries": entries,
        "s1b_pairing": [
            {"workload": workload, "gate_on": entries[workload]["system_gate"]["name"],
             "gate_off": "ident_all", "flags_identical": True}
            for workload in WORKLOADS
        ],
        "reference_values_note": (
            "reference_fitness_tps は過去実測の参考値。S-1 判定には同一 campaign 系列の再計測のみを使う "
            "(既存実測は参考併記 — D52 §2.1)"),
    }
    assert_s1b_pairing(doc)
    return doc


def _iter_sources(value) -> Iterable[Mapping]:
    if isinstance(value, dict):
        sources = value.get("sources")
        if sources is not None:
            if not isinstance(sources, list):
                raise FreezeError("sources が list ではない")
            for source in sources:
                if not isinstance(source, dict):
                    raise FreezeError("source entry が object ではない")
                yield source
        for key, child in value.items():
            if key != "sources":
                yield from _iter_sources(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_sources(child)


def _validate_schema(doc: Mapping) -> None:
    if set(doc) != TOP_LEVEL_KEYS:
        raise FreezeError(f"freeze top-level keys が schema と不一致: {sorted(set(doc) ^ TOP_LEVEL_KEYS)}")
    rules = doc.get("selection_rules")
    if not isinstance(rules, dict) or set(rules) != {
            "p2_2", "backoff_fixed", "sort", "system_gate", "stock_common"}:
        raise FreezeError("selection_rules keys が schema と不一致")
    entries = doc.get("entries")
    if not isinstance(entries, dict) or set(entries) != set(WORKLOADS):
        raise FreezeError("entries workload keys が schema と不一致")
    for workload, entry in entries.items():
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise FreezeError(f"entries.{workload} keys が schema と不一致")
        for configuration in ("system_gate", "ident_all"):
            record = entry.get(configuration)
            if not isinstance(record, Mapping):
                raise FreezeError(
                    f"entries.{workload}.{configuration} が object ではない")
            _require_trigger_name_mask_binding(
                record.get("name"),
                record.get("gate_predicate"),
                workload=workload,
                configuration=configuration,
            )
        sort_record = entry.get("sort_best")
        if not isinstance(sort_record, Mapping):
            raise FreezeError(
                f"entries.{workload}.sort_best が object ではない")
        _require_sort_name_comparator_binding(
            sort_record.get("name"),
            sort_record.get("comparator"),
            workload=workload,
        )
    generator_doc = doc.get("generator")
    if not isinstance(generator_doc, dict) or set(generator_doc) != {"path", "sha256"}:
        raise FreezeError("generator schema が不一致")


_HISTORICAL_CODE_PATHS = frozenset({
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/s8a_trigger_sweep.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/backoff_sweep.py",
    "orchestrator/campaign/s6_sort_sweep.py",
    "orchestrator/campaign/p3_s4_loop_sort.py",
})


def verify_document(doc: Mapping, *,
                    source_resolver: Optional[Callable[[str], Path]] = None,
                    historical: bool = False) -> Tuple[Mapping[str, object], ...]:
    """Verify current semantics by default, or view the identified old record."""
    raw = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return _verify_document(
        doc, source_resolver=source_resolver, historical=historical, raw=raw)


def _verify_document(doc: Mapping, *, historical: bool, raw: bytes,
                     source_resolver: Optional[Callable[[str], Path]] = None
                    ) -> Tuple[Mapping[str, object], ...]:
    held_checks: List[Mapping[str, object]] = []
    # Reuse the existing root only to identify this historical document; this
    # does not execute or release the held T-080 artifact check.
    from .t080_freeze_migration import KNOWN_AXES_RAW_SHA256

    known_historical = hashlib.sha256(raw).hexdigest() == KNOWN_AXES_RAW_SHA256
    if not (known_historical and historical):
        _validate_schema(doc)
    generator_doc = doc["generator"]
    if generator_doc["path"] != SCRIPT_REL:
        raise FreezeError(f"generator.path 不一致: {generator_doc['path']}")
    if not known_historical:
        actual_generator = _sha256(ROOT / SCRIPT_REL)
        if generator_doc["sha256"] != actual_generator:
            raise FreezeError(
                f"generator sha256 不一致: recorded={generator_doc['sha256']} actual={actual_generator}")

    resolver = source_resolver or (lambda rel: ROOT / rel)
    source_count = 0
    for source in _iter_sources(doc):
        path_rel, expected = source.get("path"), source.get("sha256")
        if not isinstance(path_rel, str) or not isinstance(expected, str):
            raise FreezeError("source path/sha256 が文字列でない")
        if known_historical and historical and path_rel in _HISTORICAL_CODE_PATHS:
            continue
        path = resolver(path_rel)
        if not path.is_file():
            raise FreezeError(f"source が存在しない: {path_rel} -> {path}")
        actual = _sha256(path)
        if actual != expected and not (known_historical and path_rel in _HISTORICAL_CODE_PATHS):
            raise FreezeError(
                f"source sha256 不一致: {path_rel} recorded={expected} actual={actual}")
        source_count += 1
    if source_count == 0:
        raise FreezeError("sources が 1 件もない")

    if not (known_historical and historical):
        assert_s1b_pairing(doc)
        frozen_head = doc.get("frozen_at_head")
        if not isinstance(frozen_head, str) or not re.fullmatch(r"[0-9a-f]{40}", frozen_head):
            raise FreezeError("frozen_at_head が 40 桁 git SHA でない")
        if not known_historical:
            try:
                _run_git(["cat-file", "-e", f"{frozen_head}^{{commit}}"])
                _run_git(["merge-base", "--is-ancestor", frozen_head, "HEAD"])
            except FreezeError as e:
                raise FreezeError(f"frozen_at_head が現行 HEAD の commit ancestor でない: {frozen_head}") from e

    if _freeze_hold.HELD:
        held_checks.append(_freeze_hold.held_marker(
            "s1-known-axes.ccbench-submodule-head-pin",
        ))
    else:
        actual_pin = _run_git(["rev-parse", "HEAD"], ROOT / "external/ccbench")
        if doc.get("ccbench_pin") != actual_pin:
            raise FreezeError(
                f"ccbench_pin 不一致: recorded={doc.get('ccbench_pin')} actual={actual_pin}"
            )

    if known_historical and historical:
        return tuple(held_checks)

    expected_doc = build_document(
        frozen_at_head=frozen_head,
        ccbench_pin=doc["ccbench_pin"],
        python_version=doc.get("python_version"),
        generator_sha=generator_doc["sha256"],
    )
    if known_historical:
        expected_doc = copy.deepcopy(expected_doc)
        for recorded, current in zip(_iter_sources(doc), _iter_sources(expected_doc)):
            if (recorded["path"] in _HISTORICAL_CODE_PATHS
                    and current.get("path") == recorded["path"]):
                current["sha256"] = recorded["sha256"]
    if doc != expected_doc:
        raise FreezeError("freeze JSON の内容が現行 generator による機械再構成と不一致")
    return tuple(held_checks)


def generate(output_path: Path = FREEZE_PATH) -> Dict:
    if output_path.exists():
        raise FreezeError(
            f"freeze が既に存在する: {output_path} — "
            "再凍結する場合は人間が明示的に削除してから再実行すること")
    doc = build_document()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("x", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except FileExistsError as e:
        raise FreezeError(f"freeze が既に存在する: {output_path}") from e
    return doc


def verify(path: Path = FREEZE_PATH, *,
           source_resolver: Optional[Callable[[str], Path]] = None,
           historical: bool = False) -> Dict:
    if not path.is_file():
        raise FreezeError(f"freeze が存在しない: {path}")
    try:
        raw = path.read_bytes()
        doc = json.loads(raw)
    except (OSError, ValueError) as e:
        raise FreezeError(f"JSON を読めない: {path}: {e}") from e
    if not isinstance(doc, dict):
        raise FreezeError(f"JSON top-level が object ではない: {path}")
    held_checks = _verify_document(
        doc, source_resolver=source_resolver, historical=historical, raw=raw)
    return _freeze_hold.result_with_markers(doc, held_checks)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if len(args) != 1 or args[0] not in {"generate", "verify"}:
        print(f"usage: python3 {SCRIPT_REL} generate|verify", file=sys.stderr)
        return 2
    try:
        if args[0] == "generate":
            generate()
            print(f"generated: {FREEZE_REL}")
        else:
            result = verify(historical=True)
            if result.held_checks:
                print(json.dumps({
                    "status": "held", "path": FREEZE_REL,
                    "held_checks": result.held_checks,
                }, ensure_ascii=False, sort_keys=True))
            else:
                print(f"verified: {FREEZE_REL}")
    except FreezeError as e:
        print(f"fails-closed: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
