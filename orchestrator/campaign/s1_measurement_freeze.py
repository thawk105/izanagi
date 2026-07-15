# -*- coding: utf-8 -*-
"""S-1 計測構成・比較対・schedule・実装 hash を凍結・照合する。

使い方:
  python3 orchestrator/campaign/s1_measurement_freeze.py generate
  python3 orchestrator/campaign/s1_measurement_freeze.py verify
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Sequence

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import pin  # noqa: E402
from campaign import s1_known_axes_freeze as known_axes  # noqa: E402


ROOT = _ORCHESTRATOR.parent
SCRIPT_REL = "orchestrator/campaign/s1_measurement_freeze.py"
STATS_REL = "orchestrator/campaign/s1_stats.py"
KNOWN_AXES_REL = "output/s1-freeze/known_axes_freeze.json"
FREEZE_REL = "output/s1-freeze/measurement_freeze.json"

SCRIPT_PATH = ROOT / SCRIPT_REL
STATS_PATH = ROOT / STATS_REL
KNOWN_AXES_PATH = ROOT / KNOWN_AXES_REL
FREEZE_PATH = ROOT / FREEZE_REL

WORKLOADS = ("balanced", "write-heavy", "read-heavy")
CONFIGURATIONS = (
    "system_gate", "ident_all", "p2_2_flag_opt", "backoff_fixed_best",
    "sort_best", "stock_common",
)
S1A_CONTROLS = ("p2_2_flag_opt", "backoff_fixed_best", "sort_best")
CAMPAIGN_ROUNDS = {"floor": 8, "test_block_1": 4, "test_block_2": 4}

# seed 自体に意味を持たせず、commit された定数で実行順を凍結する。
MASTER_SEED = 20260715
OPERATING_POINT = {"RECORDS": 1_000_000, "THREADS": 48, "EXTIME": 3, "REPS": 5}
# D50 系の確立した workload 座標。p2_2 / s8a_trigger_sweep / backoff_sweep と同じ
# balanced=rr50, write-heavy=rr5, read-heavy=rr95 を比較点の自由度ごと凍結する。
WORKLOAD_FLAGS = {
    "balanced": {"ycsb_rratio": "50"},
    "write-heavy": {"ycsb_rratio": "5"},
    "read-heavy": {"ycsb_rratio": "95"},
}

TOP_LEVEL_KEYS = {
    "what", "frozen_at_head", "ccbench_pin", "generator", "python_version",
    "cells", "comparisons", "s1b_pairing", "operating_point", "workload_flags",
    "master_seed", "schedule", "schedule_hash", "implementation_hashes",
}
IMPLEMENTATION_KEYS = {
    "s1_stats", "s1_measurement_freeze", "known_axes_freeze",
}
CELL_KEYS = {"workload", "configuration", "variant", "source_pointer"}
COMPARISON_KEYS = {
    "comparison_id", "family", "workload", "left_cell", "right_cell",
    "alternative", "note",
}


class FreezeError(RuntimeError):
    """凍結生成・照合を fail-closed で止めるエラー。"""


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise FreezeError(f"hash 対象が存在しない: {path}")
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError as e:
        raise FreezeError(f"hash 対象を読めない: {path}: {e}") from e
    return h.hexdigest()


def _load_json(path: Path) -> Dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise FreezeError(f"JSON を読めない: {path}: {e}") from e
    if not isinstance(value, dict):
        raise FreezeError(f"JSON top-level が object ではない: {path}")
    return value


def _run_git(args: Sequence[str]) -> str:
    try:
        p = subprocess.run(
            ["git", *args], cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as e:
        detail = getattr(e, "stderr", "") or str(e)
        raise FreezeError(f"git {' '.join(args)} に失敗: {detail.strip()}") from e
    return p.stdout.strip()


def _source(path: Path, recorded_path: str, key: str) -> Dict:
    return {"path": recorded_path, "sha256": _sha256(path), "key": key}


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                         sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def derive_seed(master_seed: int, campaign: str, round_number: int) -> int:
    """S6 と同型の domain-separated SHA-256 から周回 seed を導出する。"""
    if isinstance(master_seed, bool) or not isinstance(master_seed, int):
        raise FreezeError("master_seed が整数でない")
    if campaign not in CAMPAIGN_ROUNDS:
        raise FreezeError(f"未知の campaign: {campaign}")
    if (isinstance(round_number, bool) or not isinstance(round_number, int)
            or not 1 <= round_number <= CAMPAIGN_ROUNDS[campaign]):
        raise FreezeError(f"周回番号が範囲外: {campaign} {round_number}")
    digest = hashlib.sha256(
        f"izanagi-s1-schedule:{master_seed}:{campaign}:{round_number}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _cell_id(workload: str, configuration: str) -> str:
    return f"{workload}:{configuration}"


def build_schedule(master_seed: int = MASTER_SEED) -> Dict[str, list[list[str]]]:
    """各周回に18セルを1回ずつ含む固定 seed schedule を作る。"""
    cell_ids = [_cell_id(workload, configuration)
                for workload in WORKLOADS for configuration in CONFIGURATIONS]
    schedule: Dict[str, list[list[str]]] = {}
    for campaign, rounds in CAMPAIGN_ROUNDS.items():
        campaign_schedule = []
        for round_number in range(1, rounds + 1):
            order = list(cell_ids)
            random.Random(derive_seed(master_seed, campaign, round_number)).shuffle(order)
            campaign_schedule.append(order)
        schedule[campaign] = campaign_schedule
    return schedule


def _verify_known_axes(path: Path,
                       source_resolver: Optional[Callable[[str], Path]]) -> Dict:
    doc = _load_json(path)
    try:
        known_axes.verify_document(doc, source_resolver=source_resolver)
    except known_axes.FreezeError as e:
        raise FreezeError(f"known_axes_freeze 照合失敗: {e}") from e
    return doc


def _build_cells(known_doc: Mapping) -> Dict[str, Dict]:
    entries = known_doc.get("entries")
    if not isinstance(entries, dict) or set(entries) != set(WORKLOADS):
        raise FreezeError("known_axes_freeze.entries workload keys が不一致")
    cells: Dict[str, Dict] = {}
    for workload in WORKLOADS:
        workload_entries = entries.get(workload)
        if not isinstance(workload_entries, dict) or set(workload_entries) != set(CONFIGURATIONS):
            raise FreezeError(f"known_axes_freeze.entries.{workload} keys が不一致")
        for configuration in CONFIGURATIONS:
            variant = workload_entries.get(configuration)
            if not isinstance(variant, dict):
                raise FreezeError(
                    f"known_axes_freeze.entries.{workload}.{configuration} が object でない")
            cell_id = _cell_id(workload, configuration)
            cells[cell_id] = {
                "workload": workload,
                "configuration": configuration,
                # 值の再選定を避け、材料 freeze の entry をそのまま射影する。
                "variant": copy.deepcopy(variant),
                "source_pointer": {
                    "path": KNOWN_AXES_REL,
                    "key": f"entries.{workload}.{configuration}",
                },
            }
    return cells


def _build_comparisons() -> list[Dict]:
    note = "stock_common は併記用の文脈セルであり、検定比較対には含めない。"
    comparisons = []
    for workload in WORKLOADS:
        for control in S1A_CONTROLS:
            comparisons.append({
                "comparison_id": f"S-1a:{workload}:{control}",
                "family": "S-1a",
                "workload": workload,
                "left_cell": _cell_id(workload, "system_gate"),
                "right_cell": _cell_id(workload, control),
                "alternative": "greater",
                "note": note,
            })
    for workload in WORKLOADS:
        comparisons.append({
            "comparison_id": f"S-1b:{workload}:gate_on_vs_gate_off",
            "family": "S-1b",
            "workload": workload,
            "left_cell": _cell_id(workload, "system_gate"),
            "right_cell": _cell_id(workload, "ident_all"),
            "alternative": "greater",
            "note": note,
        })
    return comparisons


def assert_s1b_pairing(doc: Mapping) -> None:
    """gate on/off は flags が同一で、述語だけが異なることを再検査する。"""
    cells, pairings = doc.get("cells"), doc.get("s1b_pairing")
    if not isinstance(cells, dict) or not isinstance(pairings, list):
        raise FreezeError("s1b_pairing 検査に必要な cells/list がない")
    entries: Dict[str, Dict] = {workload: {} for workload in WORKLOADS}
    for workload in WORKLOADS:
        for configuration in ("system_gate", "ident_all"):
            cell = cells.get(_cell_id(workload, configuration))
            if not isinstance(cell, dict) or not isinstance(cell.get("variant"), dict):
                raise FreezeError(f"s1b_pairing cell が不正: {workload} {configuration}")
            entries[workload][configuration] = cell["variant"]
    projected = {"entries": entries, "s1b_pairing": pairings}
    try:
        known_axes.assert_s1b_pairing(projected)
    except known_axes.FreezeError as e:
        raise FreezeError(f"s1b_pairing 検査失敗: {e}") from e


def build_document(
        *, frozen_at_head: Optional[str] = None,
        ccbench_pin: Optional[str] = None,
        python_version: Optional[str] = None,
        master_seed: int = MASTER_SEED,
        known_axes_path: Path = KNOWN_AXES_PATH,
        stats_path: Path = STATS_PATH,
        generator_path: Path = SCRIPT_PATH,
        known_source_resolver: Optional[Callable[[str], Path]] = None) -> Dict:
    known_doc = _verify_known_axes(known_axes_path, known_source_resolver)
    cells = _build_cells(known_doc)
    schedule = build_schedule(master_seed)
    implementation_hashes = {
        "s1_stats": _source(stats_path, STATS_REL, "S-1 層別統計実装"),
        "s1_measurement_freeze": _source(
            generator_path, SCRIPT_REL, "S-1 計測 freeze generator"),
        "known_axes_freeze": _source(
            known_axes_path, KNOWN_AXES_REL, "S-1 既知軸基準点 freeze"),
    }
    doc = {
        "what": "S-1 計測 freeze v2 (18セル・比較対・schedule・実装 hash)",
        "frozen_at_head": frozen_at_head or _run_git(["rev-parse", "HEAD"]),
        "ccbench_pin": ccbench_pin or pin.CURRENT_PIN,
        "generator": {
            "path": SCRIPT_REL,
            "sha256": implementation_hashes["s1_measurement_freeze"]["sha256"],
        },
        "python_version": python_version or sys.version,
        "cells": cells,
        "comparisons": _build_comparisons(),
        "s1b_pairing": copy.deepcopy(known_doc.get("s1b_pairing")),
        "operating_point": copy.deepcopy(OPERATING_POINT),
        "workload_flags": copy.deepcopy(WORKLOAD_FLAGS),
        "master_seed": master_seed,
        "schedule": schedule,
        "schedule_hash": _canonical_sha256(schedule),
        "implementation_hashes": implementation_hashes,
    }
    assert_s1b_pairing(doc)
    return doc


def _validate_schema(doc: Mapping) -> None:
    if set(doc) != TOP_LEVEL_KEYS:
        raise FreezeError(
            f"freeze top-level keys が schema と不一致: {sorted(set(doc) ^ TOP_LEVEL_KEYS)}")
    generator = doc.get("generator")
    if not isinstance(generator, dict) or set(generator) != {"path", "sha256"}:
        raise FreezeError("generator schema が不一致")
    hashes = doc.get("implementation_hashes")
    if not isinstance(hashes, dict) or set(hashes) != IMPLEMENTATION_KEYS:
        raise FreezeError("implementation_hashes keys が schema と不一致")
    for name, source in hashes.items():
        if not isinstance(source, dict) or set(source) != {"path", "sha256", "key"}:
            raise FreezeError(f"implementation_hashes.{name} schema が不一致")
        if not all(isinstance(source.get(key), str) for key in ("path", "sha256", "key")):
            raise FreezeError(f"implementation_hashes.{name} に非文字列がある")
    expected_paths = {
        "s1_stats": STATS_REL,
        "s1_measurement_freeze": SCRIPT_REL,
        "known_axes_freeze": KNOWN_AXES_REL,
    }
    for name, path in expected_paths.items():
        if hashes[name]["path"] != path:
            raise FreezeError(f"implementation_hashes.{name}.path 不一致")
    if (generator.get("path") != SCRIPT_REL
            or generator.get("sha256") !=
            hashes["s1_measurement_freeze"].get("sha256")):
        raise FreezeError("generator と implementation_hashes の自己 hash が不一致")

    cells = doc.get("cells")
    expected_cells = {_cell_id(workload, configuration)
                      for workload in WORKLOADS for configuration in CONFIGURATIONS}
    if not isinstance(cells, dict) or set(cells) != expected_cells:
        raise FreezeError("cells が18セル構成表と不一致")
    for cell_id, cell in cells.items():
        if not isinstance(cell, dict) or set(cell) != CELL_KEYS:
            raise FreezeError(f"cells.{cell_id} schema が不一致")
        if cell_id != _cell_id(cell.get("workload"), cell.get("configuration")):
            raise FreezeError(f"cells.{cell_id} ID と workload/configuration が不一致")
        if not isinstance(cell.get("variant"), dict):
            raise FreezeError(f"cells.{cell_id}.variant が object ではない")
        pointer = cell.get("source_pointer")
        if (not isinstance(pointer, dict) or set(pointer) != {"path", "key"}
                or pointer.get("path") != KNOWN_AXES_REL
                or pointer.get("key") !=
                f"entries.{cell['workload']}.{cell['configuration']}"):
            raise FreezeError(f"cells.{cell_id}.source_pointer が不正")

    comparisons = doc.get("comparisons")
    if not isinstance(comparisons, list) or len(comparisons) != 12:
        raise FreezeError("comparisons が12対ではない")
    ids = set()
    family_counts = {"S-1a": 0, "S-1b": 0}
    for comparison in comparisons:
        if not isinstance(comparison, dict) or set(comparison) != COMPARISON_KEYS:
            raise FreezeError("comparison schema が不一致")
        if not all(isinstance(comparison.get(key), str) for key in COMPARISON_KEYS):
            raise FreezeError("comparison に非文字列がある")
        if comparison.get("comparison_id") in ids:
            raise FreezeError("comparison_id が重複")
        ids.add(comparison.get("comparison_id"))
        family = comparison.get("family")
        if family not in family_counts:
            raise FreezeError(f"未知の比較 family: {family}")
        family_counts[family] += 1
        if comparison.get("workload") not in WORKLOADS:
            raise FreezeError("comparison workload が不正")
        if (comparison.get("left_cell") not in expected_cells
                or comparison.get("right_cell") not in expected_cells):
            raise FreezeError("comparison が未知の cell を参照")
        if comparison.get("alternative") != "greater":
            raise FreezeError("comparison alternative が greater ではない")
        if "stock_common" not in comparison.get("note", ""):
            raise FreezeError("comparison note に stock_common の除外理由がない")
    if family_counts != {"S-1a": 9, "S-1b": 3}:
        raise FreezeError(f"comparison family 件数が不一致: {family_counts}")

    if doc.get("operating_point") != OPERATING_POINT:
        raise FreezeError("operating_point が事前登録値と不一致")
    if doc.get("workload_flags") != WORKLOAD_FLAGS:
        raise FreezeError("workload_flags が事前固定値と不一致")
    master_seed = doc.get("master_seed")
    if isinstance(master_seed, bool) or not isinstance(master_seed, int):
        raise FreezeError("master_seed が整数でない")
    if master_seed != MASTER_SEED:
        raise FreezeError(
            f"master_seed が凍結定数と不一致: recorded={master_seed} "
            f"actual={MASTER_SEED}")
    schedule = doc.get("schedule")
    if not isinstance(schedule, dict) or set(schedule) != set(CAMPAIGN_ROUNDS):
        raise FreezeError("schedule campaign keys が不一致")
    for campaign, rounds in CAMPAIGN_ROUNDS.items():
        campaign_schedule = schedule.get(campaign)
        if not isinstance(campaign_schedule, list) or len(campaign_schedule) != rounds:
            raise FreezeError(f"schedule.{campaign} の周回数が不一致")
        for order in campaign_schedule:
            if (not isinstance(order, list) or len(order) != 18
                    or not all(isinstance(cell_id, str) for cell_id in order)
                    or set(order) != expected_cells):
                raise FreezeError(f"schedule.{campaign} の周回が18セル均衡でない")
            if len(set(order)) != len(order):
                raise FreezeError(f"schedule.{campaign} の周回に重複セルがある")
    if not isinstance(doc.get("schedule_hash"), str):
        raise FreezeError("schedule_hash が文字列でない")


def verify_document(
        doc: Mapping, *,
        source_resolver: Optional[Callable[[str], Path]] = None,
        known_source_resolver: Optional[Callable[[str], Path]] = None) -> None:
    _validate_schema(doc)
    resolver = source_resolver or (lambda rel: ROOT / rel)

    generator = doc["generator"]
    actual_generator = _sha256(resolver(SCRIPT_REL))
    if generator["sha256"] != actual_generator:
        raise FreezeError(
            f"generator sha256 不一致: recorded={generator['sha256']} actual={actual_generator}")

    for name, source in doc["implementation_hashes"].items():
        actual = _sha256(resolver(source["path"]))
        if source["sha256"] != actual:
            raise FreezeError(
                f"implementation_hashes.{name} sha256 不一致: "
                f"recorded={source['sha256']} actual={actual}")

    known_path = resolver(KNOWN_AXES_REL)
    known_doc = _verify_known_axes(known_path, known_source_resolver)
    assert_s1b_pairing(doc)

    actual_schedule_hash = _canonical_sha256(doc["schedule"])
    if doc["schedule_hash"] != actual_schedule_hash:
        raise FreezeError(
            f"schedule_hash 不一致: recorded={doc['schedule_hash']} "
            f"actual={actual_schedule_hash}")

    frozen_head = doc.get("frozen_at_head")
    if not isinstance(frozen_head, str) or not re.fullmatch(r"[0-9a-f]{40}", frozen_head):
        raise FreezeError("frozen_at_head が40桁 git SHA でない")
    try:
        _run_git(["cat-file", "-e", f"{frozen_head}^{{commit}}"])
        _run_git(["merge-base", "--is-ancestor", frozen_head, "HEAD"])
    except FreezeError as e:
        raise FreezeError(
            f"frozen_at_head が現行 HEAD の commit ancestor でない: {frozen_head}") from e
    if doc.get("ccbench_pin") != pin.CURRENT_PIN:
        raise FreezeError(
            f"ccbench_pin 不一致: recorded={doc.get('ccbench_pin')} actual={pin.CURRENT_PIN}")

    expected = build_document(
        frozen_at_head=frozen_head,
        ccbench_pin=doc["ccbench_pin"],
        python_version=doc.get("python_version"),
        master_seed=MASTER_SEED,
        known_axes_path=known_path,
        stats_path=resolver(STATS_REL),
        generator_path=resolver(SCRIPT_REL),
        known_source_resolver=known_source_resolver,
    )
    # material の検査済み document と同じセル射影かも明示的に照合する。
    if expected["cells"] != _build_cells(known_doc):
        raise FreezeError("known_axes_freeze からの cells 射影が不一致")
    if doc != expected:
        raise FreezeError("freeze JSON の内容が現行 generator による機械再構成と不一致")


def generate(
        output_path: Path = FREEZE_PATH, *,
        known_axes_path: Path = KNOWN_AXES_PATH,
        stats_path: Path = STATS_PATH,
        generator_path: Path = SCRIPT_PATH,
        known_source_resolver: Optional[Callable[[str], Path]] = None) -> Dict:
    if output_path.exists():
        raise FreezeError(
            f"freeze が既に存在する: {output_path} — "
            "再凍結する場合は人間が明示的に削除してから再実行すること")
    doc = build_document(
        known_axes_path=known_axes_path,
        stats_path=stats_path,
        generator_path=generator_path,
        known_source_resolver=known_source_resolver,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("x", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except FileExistsError as e:
        raise FreezeError(f"freeze が既に存在する: {output_path}") from e
    return doc


def verify(
        path: Path = FREEZE_PATH, *,
        source_resolver: Optional[Callable[[str], Path]] = None,
        known_source_resolver: Optional[Callable[[str], Path]] = None) -> Dict:
    if not path.is_file():
        raise FreezeError(f"freeze が存在しない: {path}")
    doc = _load_json(path)
    verify_document(
        doc,
        source_resolver=source_resolver,
        known_source_resolver=known_source_resolver,
    )
    return doc


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
            verify()
            print(f"verified: {FREEZE_REL}")
    except FreezeError as e:
        print(f"fails-closed: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
