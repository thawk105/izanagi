# -*- coding: utf-8 -*-
"""8b oracle の決定論的 schedule と immutable manifest。"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Sequence

from campaign import s8b_oracle_artifacts as _artifacts
from campaign import s8b_experiment_numbers as _experiment_numbers


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

SCHEMA_VERSION = _artifacts.OFFICIAL_MANIFEST_SCHEMA
# freeze の stock 構成名。freeze document 自体に「どれが stock か」の明示 field は
# ないためハードコードし、per-pair floor 検証時に freeze の構成集合に実在すること
# (一致検査) を _holdout_configuration_ids で強制する (C3-3/C3-1)。
STOCK_CONFIGURATION = "stock_common"
_ROW_KEYS = {
    "block_id", "replicate_index", "schedule_index",
    "holdout_id", "configuration_id",
}
_MANIFEST_KEYS = {
    "schema_version", "manifest_id", "freeze", "known_axes_freeze",
    "run_contract", "binding_identity", "schedule", "schedule_sha256",
    "campaign_ids", "campaign_config_preimages", "floor_budget_snapshot_sha256",
    "holdout_references", "allowed_excluded_reasons", "generator_versions",
}
_RUN_CONTRACT_KEYS = {
    "ccbench_pin", "env_tag", "clocks", "reps", "extime", "verify",
    "screening", "bench_max_rounds", "contract_sha256",
}
_GENERATOR_KEYS = {"materializer", "report", "judge"}
_BINDING_KEYS = {
    "holdout_id", "configuration_id", "entry_sha256", "genome_canonical",
    "src_token", "variant_id", "binding_sha256",
}


class ManifestError(RuntimeError):
    """schedule / manifest を検証できない場合の fail-closed 拒否。"""


@dataclass(frozen=True)
class VerifiedManifest:
    """verify_manifest の検証済み戻り値 (C2-9)。

    ``document`` は全検査を通過した manifest 文書、``sha256`` はその文書の
    canonical SHA-256 (= 全 consumer の identity。run_block の
    ``_canonical_sha256(manifest)`` と同値)。gate と run_block はこの単一 object を
    共有し manifest を再読込・再検証しない。

    設計判断: raw file bytes は保持しない。manifest の identity は canonical SHA-256
    に一本化されており (budget 台帳・campaign marker が使うのはこの値)、file byte
    hash を別 field で持つと未使用の第二 identity を生む。frozen なのは field 束縛の
    再代入防止であって document dict の深い不変化 (C1-7) は後続 wave の責務。
    """
    document: _artifacts.OfficialManifest
    sha256: str


def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"canonical JSON に変換できない: {exc}") from exc


def _canonical_sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def manifest_sha256(document: Mapping) -> str:
    """自己 hash field を除く manifest 文書の canonical SHA-256。"""
    if not isinstance(document, Mapping):
        raise ManifestError("manifest が object でない")
    value = copy.deepcopy(dict(document))
    value.pop("manifest_sha256", None)
    return _canonical_sha256(value)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ManifestError(f"sha256 対象を読めない: {path}: {exc}") from exc
    return digest.hexdigest()


def _load_json_object(path: Path) -> Dict:
    try:
        return _artifacts.strict_load_json_object(path)
    except _artifacts.OracleArtifactTypeError as exc:
        raise ManifestError(str(exc)) from exc


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _identifier(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{field} が空でない文字列でない")
    return value


def _identifiers(values: Sequence[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ManifestError(f"{field} が文字列 sequence でない")
    out = tuple(_identifier(value, field=field) for value in values)
    if not out or len(set(out)) != len(out):
        raise ManifestError(f"{field} が空または重複を含む")
    return out


def derive_seed(master_seed: str, block_id: str, replicate_index: int) -> int:
    """SHA-256 による domain separation から shuffle seed を導く。"""
    _identifier(master_seed, field="master_seed")
    _identifier(block_id, field="block_id")
    if not _is_int(replicate_index) or replicate_index < 0:
        raise ManifestError("replicate_index が非負整数でない")
    payload = f"{master_seed}/{block_id}/{replicate_index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def build_schedule(
    *, n: int, master_seed: str, block_sizes: Mapping[str, int],
    holdout_ids: Sequence[str], configuration_ids: Sequence[str],
) -> dict:
    """完全ブロック replicate を time block へ割り当てて決定論的に並べる。"""
    if not _is_int(n) or n <= 0:
        raise ManifestError("n が正整数でない")
    _identifier(master_seed, field="master_seed")
    if not isinstance(block_sizes, Mapping) or not block_sizes:
        raise ManifestError("block_sizes が空でない mapping でない")

    blocks = []
    for raw_block_id, size in block_sizes.items():
        block_id = _identifier(raw_block_id, field="block_id")
        if not _is_int(size) or size <= 0:
            raise ManifestError(f"block_sizes.{block_id} が正整数でない")
        blocks.append({"block_id": block_id, "size": size})
    if sum(block["size"] for block in blocks) != n:
        raise ManifestError("sum(block_sizes) が n と一致しない")

    holdouts = _identifiers(holdout_ids, field="holdout_ids")
    configurations = _identifiers(configuration_ids, field="configuration_ids")
    cells = [(holdout_id, configuration_id)
             for holdout_id in holdouts for configuration_id in configurations]

    rows = []
    replicate_index = 0
    for block in blocks:
        block_id = block["block_id"]
        for _ in range(block["size"]):
            shuffled = list(cells)
            random.Random(
                derive_seed(master_seed, block_id, replicate_index)
            ).shuffle(shuffled)
            for holdout_id, configuration_id in shuffled:
                rows.append({
                    "block_id": block_id,
                    "replicate_index": replicate_index,
                    "schedule_index": len(rows),
                    "holdout_id": holdout_id,
                    "configuration_id": configuration_id,
                })
            replicate_index += 1

    return {
        "n": n,
        "master_seed": master_seed,
        "blocks": blocks,
        "rows": rows,
    }


def schedule_sha256(schedule) -> str:
    """schedule 全体の canonical JSON SHA-256。"""
    return _canonical_sha256(schedule)


def _validate_schedule(schedule: Mapping) -> None:
    if not isinstance(schedule, Mapping) or set(schedule) != {
        "n", "master_seed", "blocks", "rows",
    }:
        raise ManifestError("schedule schema が不一致")
    n = schedule.get("n")
    if not _is_int(n) or n <= 0:
        raise ManifestError("schedule.n が正整数でない")
    _identifier(schedule.get("master_seed"), field="schedule.master_seed")

    blocks = schedule.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise ManifestError("schedule.blocks が空でない list でない")
    block_sizes: Dict[str, int] = {}
    for block in blocks:
        if not isinstance(block, dict) or set(block) != {"block_id", "size"}:
            raise ManifestError("schedule block schema が不一致")
        block_id = _identifier(block.get("block_id"), field="schedule block_id")
        size = block.get("size")
        if block_id in block_sizes:
            raise ManifestError(f"schedule block_id が重複: {block_id}")
        if not _is_int(size) or size <= 0:
            raise ManifestError(f"schedule block size が正整数でない: {block_id}")
        block_sizes[block_id] = size
    # 単一 block 契約 (A3-3): 1 manifest に block は正確に 1 件で、その block が
    # 予定全行を含む。複数 block は共有台帳の総枠 gate を fail-open させるため拒否する。
    if len(block_sizes) != 1:
        raise ManifestError("schedule.blocks が正確に 1 件でない (単一 block 契約)")
    if sum(block_sizes.values()) != n:
        raise ManifestError("schedule n と block size 合計が不一致")

    rows = schedule.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ManifestError("schedule.rows が空でない list でない")
    by_replicate: Dict[int, list] = {}
    for expected_index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != _ROW_KEYS:
            raise ManifestError("schedule row schema が不一致")
        if row.get("schedule_index") != expected_index:
            raise ManifestError("schedule_index が連続していない")
        replicate = row.get("replicate_index")
        if not _is_int(replicate) or not 0 <= replicate < n:
            raise ManifestError("replicate_index が範囲外")
        if row.get("block_id") not in block_sizes:
            raise ManifestError("schedule row が未知 block を参照")
        _identifier(row.get("holdout_id"), field="holdout_id")
        _identifier(row.get("configuration_id"), field="configuration_id")
        by_replicate.setdefault(replicate, []).append(row)
    if set(by_replicate) != set(range(n)):
        raise ManifestError("replicate_index が 0..n-1 を網羅しない")

    all_cells = {
        (row["holdout_id"], row["configuration_id"])
        for row in rows
    }
    if not all_cells:
        raise ManifestError("schedule cell が空")
    block_replicates: Dict[str, set[int]] = {block_id: set() for block_id in block_sizes}
    for replicate, replicate_rows in by_replicate.items():
        cells = [(row["holdout_id"], row["configuration_id"])
                 for row in replicate_rows]
        block_ids = {row["block_id"] for row in replicate_rows}
        if len(block_ids) != 1 or len(cells) != len(all_cells) or set(cells) != all_cells:
            raise ManifestError(f"replicate {replicate} が完全ブロックでない")
        if len(set(cells)) != len(cells):
            raise ManifestError(f"replicate {replicate} に cell 重複がある")
        block_replicates[next(iter(block_ids))].add(replicate)
    for block_id, expected_size in block_sizes.items():
        if len(block_replicates[block_id]) != expected_size:
            raise ManifestError(f"block {block_id} の replicate 数が size と不一致")


def _source_record(value, *, field: str) -> dict:
    if not isinstance(value, Mapping) or set(value) != {"path", "sha256"}:
        raise ManifestError(f"{field} source record schema が不一致")
    path = _identifier(value.get("path"), field=f"{field}.path")
    sha256 = value.get("sha256")
    if (not isinstance(sha256, str) or len(sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in sha256)):
        raise ManifestError(f"{field}.sha256 が SHA-256 でない")
    return {"path": path, "sha256": sha256}


def _path_record(path: Path) -> dict:
    resolved = path.resolve()
    try:
        display = resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        display = str(resolved)
    return {"path": display, "sha256": _file_sha256(resolved)}


def _resolve_source(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def _find_recorded_source(record: Mapping, *, freeze_path: Path) -> Path:
    path_text = str(record["path"])
    source = Path(path_text)
    if source.is_absolute():
        candidates = [source]
    else:
        candidates = [parent / source for parent in freeze_path.resolve().parents]
        candidates.append(ROOT / source)
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            if _file_sha256(resolved) != record["sha256"]:
                raise ManifestError(f"参照 source sha256 不一致: {record['path']}")
            return resolved
    raise ManifestError(f"参照 source が存在しない: {record['path']}")


def _validate_run_contract(run_contract: Mapping) -> dict:
    if not isinstance(run_contract, Mapping) or not _RUN_CONTRACT_KEYS <= set(run_contract):
        raise ManifestError("run_contract の必須 field が不足")
    if run_contract.get("verify") != "legacy+s2":
        raise ManifestError("run_contract.verify が legacy+s2 でない")
    if run_contract.get("screening") != "off":
        raise ManifestError("run_contract.screening が off でない")
    for field in ("ccbench_pin", "env_tag"):
        _identifier(run_contract.get(field), field=f"run_contract.{field}")
    # C3-9/C3-10: env 契約 fingerprint。driver が env_contract.lookup(env_tag) の
    # contract_sha256 との完全一致を検査する (ここでは形式のみ 64hex 検査)。
    _sha256_text(run_contract.get("contract_sha256"),
                 field="run_contract.contract_sha256")
    for field in ("clocks", "reps", "extime", "bench_max_rounds"):
        value = run_contract.get(field)
        if not _is_int(value) or value <= 0:
            raise ManifestError(f"run_contract.{field} が正整数でない")
    # M5: oracle adapter は必ず bench_max_rounds=1 を明示する (generic
    # pipeline.evaluate の default=3 とは別)。正整数一般でなく 1 完全一致で pin する。
    if run_contract.get("bench_max_rounds") != 1:
        raise ManifestError("run_contract.bench_max_rounds が 1 でない")
    if run_contract.get("reps") != _experiment_numbers.APPROVED_REPS:
        raise ManifestError(
            "run_contract.reps が承認凍結値でない: "
            f"{_experiment_numbers.APPROVED_REPS}"
        )
    if run_contract.get("extime") != _experiment_numbers.APPROVED_EXTIME_S:
        raise ManifestError(
            "run_contract.extime が承認凍結値でない: "
            f"{_experiment_numbers.APPROVED_EXTIME_S}"
        )
    return copy.deepcopy(dict(run_contract))


def _validate_generators(generator_versions: Mapping, *, root: Path) -> dict:
    if not isinstance(generator_versions, Mapping) or set(generator_versions) != _GENERATOR_KEYS:
        raise ManifestError("generator_versions schema が不一致")
    root = root.resolve()
    validated = {}
    for key in sorted(_GENERATOR_KEYS):
        record = _source_record(
            generator_versions[key], field=f"generator_versions.{key}",
        )
        resolved = _resolve_source(record["path"], root=root).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ManifestError(
                f"generator_versions.{key}.path が root 外: {record['path']}"
            ) from exc
        if not resolved.is_file():
            raise ManifestError(
                f"generator_versions.{key}.path が実ファイルでない: {record['path']}"
            )
        if _file_sha256(resolved) != record["sha256"]:
            raise ManifestError(f"generator_versions.{key}.sha256 が実 byte hash と不一致")
        validated[key] = record
    return validated


def _sha256_text(value, *, field: str) -> str:
    value = _identifier(value, field=field)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ManifestError(f"{field} が SHA-256 でない")
    return value


def _schedule_cells(schedule: Mapping) -> set[tuple[str, str]]:
    return {
        (row["holdout_id"], row["configuration_id"])
        for row in schedule["rows"]
    }


def _validate_binding_identity(binding_identity, *, schedule: Mapping) -> list[dict]:
    if (not isinstance(binding_identity, Sequence)
            or isinstance(binding_identity, (str, bytes, bytearray))):
        raise ManifestError("binding_identity が list でない")
    expected_cells = _schedule_cells(schedule)
    if len(binding_identity) != len(expected_cells):
        raise ManifestError(
            f"binding_identity 件数が schedule cell 数と不一致: "
            f"{len(binding_identity)} != {len(expected_cells)}"
        )
    validated: list[dict] = []
    cells: set[tuple[str, str]] = set()
    for raw in binding_identity:
        if not isinstance(raw, Mapping) or set(raw) != _BINDING_KEYS:
            raise ManifestError("binding_identity entry schema が不一致")
        entry = dict(raw)
        holdout_id = _identifier(entry.get("holdout_id"), field="binding.holdout_id")
        configuration_id = _identifier(
            entry.get("configuration_id"), field="binding.configuration_id",
        )
        cell = (holdout_id, configuration_id)
        if cell in cells:
            raise ManifestError(f"binding_identity cell が重複: {cell!r}")
        cells.add(cell)
        entry_sha = _sha256_text(entry.get("entry_sha256"), field="binding.entry_sha256")
        genome = entry.get("genome_canonical")
        if not ((isinstance(genome, str) and genome)
                or isinstance(genome, Mapping)):
            raise ManifestError("binding.genome_canonical が非空文字列/object でない")
        src_token = _identifier(entry.get("src_token"), field="binding.src_token")
        variant_id = _identifier(entry.get("variant_id"), field="binding.variant_id")
        binding_sha = _sha256_text(
            entry.get("binding_sha256"), field="binding.binding_sha256",
        )
        projected = {
            "genome_canonical": copy.deepcopy(genome),
            "src_token": src_token,
            "variant_id": variant_id,
            "entry_sha256": entry_sha,
        }
        if binding_sha != _canonical_sha256(projected):
            raise ManifestError("binding.binding_sha256 が identity 再計算値と不一致")
        validated.append({
            "holdout_id": holdout_id,
            "configuration_id": configuration_id,
            **projected,
            "binding_sha256": binding_sha,
        })
    if cells != expected_cells:
        raise ManifestError("binding_identity cell 集合が schedule と完全一致しない")
    return validated


def _finite_positive_or_none(value) -> bool:
    """有限正 float (>0) または None のとき True。bool・非有限・0 以下は False。"""
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value)) and float(value) > 0


def _holdout_configuration_ids(freeze: Mapping, holdout_id: str) -> set:
    """freeze の当該 holdout の構成集合 (variant_binding.entries の key 集合)。

    stock 構成名 (STOCK_CONFIGURATION) が実在することを併せて検査する
    (ハードコード名と freeze 記録値の一致検査。C3-1/C3-3)。
    """
    holdouts = freeze.get("holdouts")
    if not isinstance(holdouts, Mapping):
        raise ManifestError("freeze.holdouts が object でない")
    entry = holdouts.get(holdout_id)
    if not isinstance(entry, Mapping):
        raise ManifestError(f"freeze.holdouts.{holdout_id} が object でない")
    binding = entry.get("variant_binding")
    if not isinstance(binding, Mapping):
        raise ManifestError(
            f"freeze.holdouts.{holdout_id}.variant_binding が object でない"
        )
    entries = binding.get("entries")
    if not isinstance(entries, Mapping) or not entries:
        raise ManifestError(
            f"freeze.holdouts.{holdout_id}.variant_binding.entries が"
            " 空でない object でない"
        )
    config_ids = set(entries)
    if STOCK_CONFIGURATION not in config_ids:
        raise ManifestError(
            f"freeze.holdouts.{holdout_id} の構成集合に stock 構成"
            f" {STOCK_CONFIGURATION} がない"
        )
    return config_ids


def _validate_holdout_floor(freeze: Mapping, holdout_id: str, value) -> None:
    """1 holdout の per-pair floor table を exact 検査する (C3-3)。

    形 = exact 3 keys {pairs, scale_ref, scalar_alt}。scalar (v1 数値) 形・stock key
    混入・pair 欠落/余分・自己矛盾する相関は全て拒否する。
    """
    if not isinstance(value, Mapping) or set(value) != {
            "pairs", "scale_ref", "scalar_alt"}:
        raise ManifestError(
            f"freeze.floor.by_holdout.{holdout_id} が"
            " exact {pairs, scale_ref, scalar_alt} でない"
        )
    pairs = value["pairs"]
    scale_ref = value["scale_ref"]
    scalar_alt = value["scalar_alt"]

    expected_pairs = _holdout_configuration_ids(freeze, holdout_id) - {
        STOCK_CONFIGURATION}
    if not isinstance(pairs, Mapping) or set(pairs) != expected_pairs:
        raise ManifestError(
            f"freeze.floor.by_holdout.{holdout_id}.pairs の key 集合が"
            " 構成集合−stock と一致しない"
        )
    for configuration_id, pair_value in pairs.items():
        if not _finite_positive_or_none(pair_value):
            raise ManifestError(
                f"freeze.floor.by_holdout.{holdout_id}.pairs.{configuration_id}"
                " が有限正 float or null でない"
            )
    if not _finite_positive_or_none(scale_ref):
        raise ManifestError(
            f"freeze.floor.by_holdout.{holdout_id}.scale_ref が"
            " 有限正 float or null でない"
        )
    if not _finite_positive_or_none(scalar_alt):
        raise ManifestError(
            f"freeze.floor.by_holdout.{holdout_id}.scalar_alt が"
            " 有限正 float or null でない"
        )

    pair_values = list(pairs.values())
    all_pairs_present = bool(pair_values) and all(
        v is not None for v in pair_values)
    # 相関 1: scale_ref が null (stock 未確定) ⇒ 全 pair と scalar_alt も null。
    if scale_ref is None and (
            any(v is not None for v in pair_values) or scalar_alt is not None):
        raise ManifestError(
            f"freeze.floor.by_holdout.{holdout_id}: scale_ref が null なのに"
            " pair/scalar_alt が非 null"
        )
    # 相関 2: scalar_alt は全 pair 非 null なら max(pairs)、いずれか null なら null。
    if all_pairs_present:
        if scalar_alt != max(pair_values):
            raise ManifestError(
                f"freeze.floor.by_holdout.{holdout_id}.scalar_alt が"
                " max(pairs) と不一致"
            )
    elif scalar_alt is not None:
        raise ManifestError(
            f"freeze.floor.by_holdout.{holdout_id}.scalar_alt が"
            " pair に null を含むのに非 null"
        )


def _validate_execution_snapshot(freeze: Mapping, *, holdout_ids: Sequence[str]) -> None:
    floor = freeze.get("floor")
    budget = freeze.get("budget")
    if floor is None:
        raise ManifestError("freeze.floor が null")
    if budget is None:
        raise ManifestError("freeze.budget が null")
    if not isinstance(floor, Mapping) or set(floor) != {"by_holdout"}:
        raise ManifestError("freeze.floor が exact {by_holdout} でない")
    if not isinstance(budget, Mapping) or not budget:
        raise ManifestError("freeze.budget が空でない object でない")
    by_holdout = floor.get("by_holdout")
    if not isinstance(by_holdout, Mapping) or set(by_holdout) != set(holdout_ids):
        raise ManifestError("freeze.floor.by_holdout が schedule holdout と一致しない")
    for holdout_id, value in by_holdout.items():
        _validate_holdout_floor(freeze, holdout_id, value)
    total = budget.get("total_bench_s")
    per_holdout = budget.get("per_holdout_bench_s")
    if (isinstance(total, bool) or not isinstance(total, (int, float))
            or not math.isfinite(float(total)) or float(total) < 0):
        raise ManifestError("freeze.budget.total_bench_s が有限の非負数でない")
    if not isinstance(per_holdout, Mapping) or set(per_holdout) != set(holdout_ids):
        raise ManifestError("freeze.budget.per_holdout_bench_s が schedule holdout と一致しない")
    for holdout_id, value in per_holdout.items():
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(float(value)) or float(value) < 0):
            raise ManifestError(
                f"freeze.budget.per_holdout_bench_s.{holdout_id} が有限の非負数でない"
            )
    if budget.get("oracle_shared") is not True:
        raise ManifestError("freeze.budget.oracle_shared が true でない")


def _campaign_config_preimages(*, schedule: Mapping, run_contract: Mapping,
                               campaign_ids: Mapping[str, str]) -> dict:
    records = {}
    for block in schedule["blocks"]:
        block_id = block["block_id"]
        preimage_value = {
            "block_id": block_id,
            "campaign_id": campaign_ids[block_id],
            "run_contract": run_contract,
            "schedule": [row for row in schedule["rows"] if row["block_id"] == block_id],
        }
        canonical_json = _canonical_bytes(preimage_value).decode("utf-8")
        records[block_id] = {
            "canonical_json": canonical_json,
            "sha256": hashlib.sha256(canonical_json.encode("utf-8")).hexdigest(),
        }
    return records


def _validate_campaign_config_preimages(value: Mapping, *, schedule: Mapping,
                                        run_contract: Mapping,
                                        campaign_ids: Mapping[str, str]) -> dict:
    expected = _campaign_config_preimages(
        schedule=schedule, run_contract=run_contract, campaign_ids=campaign_ids,
    )
    if value != expected:
        raise ManifestError("campaign config preimage/hash が manifest 実行契約と不一致")
    return copy.deepcopy(expected)


def _manifest_id(document_without_id: Mapping) -> str:
    return "s8b-oracle-" + _canonical_sha256(document_without_id)[:16]


def build_manifest(
    *, freeze_path, schedule, run_contract, binding_identity, campaign_ids,
    allowed_excluded_reasons, generator_versions, campaign_config_preimages=None,
) -> _artifacts.OfficialManifest:
    """参照 hash と実走契約だけを持つ 8b oracle manifest を組み立てる。"""
    freeze_path = Path(freeze_path)
    freeze = _load_json_object(freeze_path)
    freeze_record = _path_record(freeze_path)

    known_axes_record = _source_record(
        freeze.get("known_axes_freeze"), field="known_axes_freeze",
    )
    _find_recorded_source(known_axes_record, freeze_path=freeze_path)

    _validate_schedule(schedule)
    schedule_copy = copy.deepcopy(dict(schedule))
    blocks = [block["block_id"] for block in schedule_copy["blocks"]]
    if not isinstance(campaign_ids, Mapping) or set(campaign_ids) != set(blocks):
        raise ManifestError("campaign_ids が schedule block と一対一でない")
    campaign_copy = {
        block_id: _identifier(campaign_ids[block_id], field=f"campaign_ids.{block_id}")
        for block_id in blocks
    }
    if len(set(campaign_copy.values())) != len(campaign_copy):
        raise ManifestError("campaign ID が重複")

    if (not isinstance(allowed_excluded_reasons, Sequence)
            or isinstance(allowed_excluded_reasons, (str, bytes))):
        raise ManifestError("allowed_excluded_reasons が sequence でない")
    reasons = [
        _identifier(reason, field="allowed_excluded_reasons")
        for reason in allowed_excluded_reasons
    ]
    if len(set(reasons)) != len(reasons):
        raise ManifestError("allowed_excluded_reasons が重複")

    holdout_ids = sorted({row["holdout_id"] for row in schedule_copy["rows"]})
    frozen_holdouts = freeze.get("holdouts")
    if not isinstance(frozen_holdouts, Mapping) or not set(holdout_ids) <= set(frozen_holdouts):
        raise ManifestError("schedule が freeze にない holdout_id を参照")
    holdout_references = [{
        "holdout_id": holdout_id,
        "freeze_pointer": "/holdouts/" + holdout_id.replace("~", "~0").replace("/", "~1"),
    } for holdout_id in holdout_ids]
    _validate_execution_snapshot(freeze, holdout_ids=holdout_ids)
    run_contract_copy = _validate_run_contract(run_contract)
    derived_preimages = _campaign_config_preimages(
        schedule=schedule_copy, run_contract=run_contract_copy,
        campaign_ids=campaign_copy,
    )
    if campaign_config_preimages is not None:
        _validate_campaign_config_preimages(
            campaign_config_preimages, schedule=schedule_copy,
            run_contract=run_contract_copy, campaign_ids=campaign_copy,
        )

    document = {
        "schema_version": SCHEMA_VERSION,
        "freeze": freeze_record,
        "known_axes_freeze": known_axes_record,
        "run_contract": run_contract_copy,
        "binding_identity": _validate_binding_identity(
            binding_identity, schedule=schedule_copy,
        ),
        "schedule": schedule_copy,
        "schedule_sha256": schedule_sha256(schedule_copy),
        "campaign_ids": campaign_copy,
        "campaign_config_preimages": derived_preimages,
        "floor_budget_snapshot_sha256": _canonical_sha256({
            "floor": freeze.get("floor"), "budget": freeze.get("budget"),
        }),
        "holdout_references": holdout_references,
        "allowed_excluded_reasons": reasons,
        "generator_versions": _validate_generators(generator_versions, root=ROOT),
    }
    document["manifest_id"] = _manifest_id(document)
    return _artifacts.OfficialManifest(document)


def _atomic_create_json(path: Path, document: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ManifestError(f"manifest は既に存在する: {path}")
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(tmp_name, path)
        except FileExistsError as exc:
            raise ManifestError(f"manifest は既に存在する: {path}") from exc
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


def write_manifest(path, manifest) -> None:
    """manifest を create-only の同一 filesystem atomic link で封印する。"""
    if type(manifest) is not _artifacts.OfficialManifest:
        raise _artifacts.OracleArtifactTypeError(
            "write_manifest は OfficialManifest exact type のみ受理する")
    _atomic_create_json(Path(path), manifest)


def verify_manifest(path, *, root, freeze_document, freeze_sha256) -> VerifiedManifest:
    """manifest の参照 hash、schedule、block/campaign 束縛を再照合する。

    ``freeze_document`` / ``freeze_sha256`` は必須 (C2-7)。freeze を disk から
    再読込せず、hash 検証済みの単一 object (呼び出し元の ``load_verified_freeze``
    の戻り値) だけを使う。verify から use までの freeze byte 差替え (TOCTOU) を
    consumer 間で断つための A3-6 経路。かつて存在した「freeze を manifest 記載 path
    から再読込する fallback」は撤去した (差替え窓を残すため)。

    戻り値は ``VerifiedManifest`` (document + canonical SHA-256)。gate と run_block は
    この単一 object を共有し、再読込・再検証しない (C2-9)。
    """
    path = Path(path)
    root = Path(root)
    if freeze_document is None or freeze_sha256 is None:
        raise ManifestError(
            "verify_manifest には freeze_document と freeze_sha256 が必須"
        )
    document = _load_json_object(path)
    if set(document) != _MANIFEST_KEYS:
        raise ManifestError("manifest top-level schema が不一致")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError("manifest schema_version が不一致")

    freeze_record = _source_record(document.get("freeze"), field="freeze")
    # A3-6: 検証済み単一 object を使い freeze を再読込しない。manifest 記載の byte
    # hash と一致することだけを確認する (差替え検出は呼び出し元の単一 read)。
    if not isinstance(freeze_document, Mapping):
        raise ManifestError("freeze_document が object でない")
    if freeze_sha256 != freeze_record["sha256"]:
        raise ManifestError("freeze byte sha256 が manifest と不一致")
    freeze = freeze_document

    known_record = _source_record(
        document.get("known_axes_freeze"), field="known_axes_freeze",
    )
    known_path = _resolve_source(known_record["path"], root=root)
    if _file_sha256(known_path) != known_record["sha256"]:
        raise ManifestError("known_axes byte sha256 が manifest と不一致")
    if freeze.get("known_axes_freeze") != known_record:
        raise ManifestError("freeze と manifest の known_axes 参照が不一致")

    _validate_schedule(document.get("schedule"))
    if document.get("schedule_sha256") != schedule_sha256(document["schedule"]):
        raise ManifestError("schedule_sha256 が再計算値と不一致")
    blocks = [block["block_id"] for block in document["schedule"]["blocks"]]
    campaigns = document.get("campaign_ids")
    if not isinstance(campaigns, dict) or set(campaigns) != set(blocks):
        raise ManifestError("campaign_ids が block と一対一でない")
    if (any(not isinstance(value, str) or not value for value in campaigns.values())
            or len(set(campaigns.values())) != len(campaigns)):
        raise ManifestError("campaign ID が空または重複")

    if document.get("floor_budget_snapshot_sha256") != _canonical_sha256({
            "floor": freeze.get("floor"), "budget": freeze.get("budget"),
    }):
        raise ManifestError("floor/budget snapshot hash が不一致")
    expected_holdout_ids = sorted({
        row["holdout_id"] for row in document["schedule"]["rows"]
    })
    _validate_execution_snapshot(freeze, holdout_ids=expected_holdout_ids)
    run_contract = _validate_run_contract(document.get("run_contract"))
    _validate_binding_identity(
        document.get("binding_identity"), schedule=document["schedule"],
    )
    _validate_generators(document.get("generator_versions"), root=root)
    _validate_campaign_config_preimages(
        document.get("campaign_config_preimages"), schedule=document["schedule"],
        run_contract=run_contract, campaign_ids=campaigns,
    )

    expected_references = [{
        "holdout_id": holdout_id,
        "freeze_pointer": "/holdouts/" + holdout_id.replace("~", "~0").replace("/", "~1"),
    } for holdout_id in expected_holdout_ids]
    if document.get("holdout_references") != expected_references:
        raise ManifestError("holdout freeze pointer が schedule と不一致")
    reasons = document.get("allowed_excluded_reasons")
    if (not isinstance(reasons, list)
            or any(not isinstance(reason, str) or not reason for reason in reasons)
            or len(set(reasons)) != len(reasons)):
        raise ManifestError("allowed_excluded_reasons が不正")

    without_id = dict(document)
    recorded_id = without_id.pop("manifest_id", None)
    if recorded_id != _manifest_id(without_id):
        raise ManifestError("manifest_id が内容と一致しない")
    official = _artifacts.OfficialManifest(document)
    return VerifiedManifest(document=official, sha256=_canonical_sha256(official))


def config_for_block(manifest, block_id) -> dict:
    """driver 向けに一つの block の campaign、契約、schedule 行だけを射影する。"""
    if not isinstance(manifest, Mapping):
        raise ManifestError("manifest が object でない")
    block_id = _identifier(block_id, field="block_id")
    schedule = manifest.get("schedule")
    campaigns = manifest.get("campaign_ids")
    if not isinstance(schedule, Mapping) or not isinstance(campaigns, Mapping):
        raise ManifestError("manifest の schedule/campaign_ids が不正")
    if block_id not in campaigns:
        raise ManifestError(f"未知 block_id: {block_id}")
    rows = [copy.deepcopy(row) for row in schedule.get("rows", [])
            if isinstance(row, Mapping) and row.get("block_id") == block_id]
    if not rows:
        raise ManifestError(f"block schedule が空: {block_id}")
    return {
        "block_id": block_id,
        "campaign_id": campaigns[block_id],
        "campaign_config_preimage": copy.deepcopy(
            manifest.get("campaign_config_preimages", {}).get(block_id)
        ),
        "run_contract": copy.deepcopy(manifest.get("run_contract")),
        "schedule": rows,
    }
