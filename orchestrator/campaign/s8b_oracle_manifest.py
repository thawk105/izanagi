# -*- coding: utf-8 -*-
"""8b oracle の決定論的 schedule と immutable manifest。

``schedule_index`` は ``rows`` を平坦化した通し番号 (cell ordinal) である。
``build_schedule`` の現在の生成順序では、反復内の row 添字は
``schedule_index % C`` (``C`` は holdout×configuration の cell 数) になる。
これは構築時の性質であり、``validate_schedule`` が独立に再検証する
manifest-schema 上の不変条件ではない。``s8b_oracle_n_pilot`` の observation
``seq`` はこの値をそのまま渡したもの (rename のみ) で、反復内の
``position`` は表示専用の派生値であり、admission ticket 消費の鍵は
``schedule_index`` 自身である。``s1_direct_comparison`` の attempt 添字は
別モジュールの別 namespace に属し、同一 ``schedule_index`` 内の retry 回数を
数える独立カウンタである。これらの field 名は契約で固定されており、改名できない。
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import random
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Dict, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import s8b_oracle_artifacts as _artifacts
from . import s8b_experiment_numbers as _experiment_numbers


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

MANIFEST_CANDIDATE_DIR = "output/s8b-oracle-manifest-candidates"

SCHEMA_VERSION = _artifacts.OFFICIAL_MANIFEST_SCHEMA
# freeze の stock 構成名。freeze document 自体に「どれが stock か」の明示 field は
# ないためハードコードし、schedule の cell product 検証時に構成集合に実在すること
# (一致検査) を _holdout_configuration_ids で強制する。
STOCK_CONFIGURATION = "stock_common"
_ROW_KEYS = {
    "block_id", "replicate_index", "schedule_index",
    "holdout_id", "configuration_id",
}
_MANIFEST_KEYS = {
    "schema_version", "manifest_id", "spec_sha256", "freeze", "known_axes_freeze",
    "run_contract", "binding_identity", "schedule", "schedule_sha256",
    "campaign_ids", "campaign_config_preimages",
    "holdout_references", "allowed_excluded_reasons", "generator_versions",
}
_RUN_CONTRACT_KEYS = {
    "ccbench_pin", "env_tag", "clocks", "reps", "extime", "verify",
    "screening", "bench_max_rounds", "contract_sha256",
}
_GENERATOR_SOURCES = MappingProxyType({
    "materializer": "orchestrator/campaign/s1_direct_comparison.py",
    "report": "orchestrator/campaign/s8b_oracle_report.py",
    "judge": "orchestrator/campaign/s8b_oracle_judge.py",
    "outcome_stage_contract": (
        "orchestrator/campaign/s8b_outcome_stage_contract.py"
    ),
    "artifacts": "orchestrator/campaign/s8b_oracle_artifacts.py",
})
_GENERATOR_KEYS = frozenset(_GENERATOR_SOURCES)
_BINDING_KEYS = {
    "holdout_id", "configuration_id", "entry_sha256", "genome_canonical",
    "src_token", "variant_id", "binding_sha256",
}


class ManifestError(RuntimeError):
    """schedule / manifest を検証できない場合の fail-closed 拒否。"""


class ManifestCliError(ManifestError):
    """approved-manifest CLI の構造化拒否。"""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        super().__init__(f"[{reason}] {detail}" if detail else reason)


def _verified_manifest_api():
    seal = object()

    @dataclass(frozen=True, init=False)
    class VerifiedManifest:
        """verify_manifest の構造検査通過 token。provenance 証明ではない。

        freeze の権威性は caller の責務であり、公式 CLI は active ratified 束縛で
        担う。in-process の ``object.__new__`` 等による偽造は信頼境界外。
        """

        document: _artifacts.OfficialManifest
        sha256: str

        def __init__(self, document, sha256, *, _seal=None):
            if _seal is not seal:
                raise ManifestError(
                    "VerifiedManifest は verify_manifest の検証結果からのみ構築できる"
                )
            if type(document) is not _artifacts.OfficialManifest:
                raise ManifestError(
                    "VerifiedManifest.document は OfficialManifest exact type でなければならない"
                )
            if (not isinstance(sha256, str) or len(sha256) != 64
                    or any(character not in "0123456789abcdef"
                           for character in sha256)):
                raise ManifestError(
                    "VerifiedManifest.sha256 は lowercase 64 hex でなければならない"
                )
            object.__setattr__(self, "document", document)
            object.__setattr__(self, "sha256", sha256)

    def seal_verifier(function):
        def verified(
                path, *, root, freeze_document, freeze_sha256, approved_spec):
            return function(
                path, root=root, freeze_document=freeze_document,
                freeze_sha256=freeze_sha256, approved_spec=approved_spec,
                _seal=seal,
            )

        verified.__name__ = function.__name__
        verified.__qualname__ = function.__qualname__
        verified.__doc__ = function.__doc__
        verified.__annotations__ = {
            key: (VerifiedManifest if key == "return" else value)
            for key, value in function.__annotations__.items()
            if key != "_seal"
        }
        return verified

    return VerifiedManifest, seal_verifier


VerifiedManifest, _seal_verified_manifest = _verified_manifest_api()
del _verified_manifest_api


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


def _mutable_json_tree(value):
    """deep-frozen ratified JSON view を既存 validator 用 container へ射影する。"""
    if isinstance(value, Mapping):
        return {
            key: _mutable_json_tree(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_mutable_json_tree(item) for item in value]
    return value


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
    """完全ブロック replicate を time block へ割り当てて決定論的に並べる。

    各 row の ``schedule_index`` は ``rows`` の平坦化された通し番号
    (cell ordinal) である。現在の実装が replicate-major, cell-minor の順に
    生成するため、反復内 row 添字は ``schedule_index % C`` (``C`` は
    holdout×configuration の cell 数) となり、``schedule_index // C`` は
    ``replicate_index`` となる。ただしこれは ``build_schedule`` の生成順序に
    よる構築時の性質であり、``validate_schedule`` が独立に検証する
    manifest-schema 上の不変条件ではない。

    ``s8b_oracle_n_pilot`` の observation ``seq`` は ``schedule_index`` をそのまま
    渡した値 (rename のみ) で、反復内 ``position`` は表示専用の派生値である。
    admission ticket 消費の鍵は ``schedule_index`` 自身である。なお
    ``s1_direct_comparison`` の attempt 添字は別モジュールの別 namespace にある、
    同一 ``schedule_index`` 内の retry 回数を数える独立カウンタである。field 名は
    契約で固定されており、改名できない。
    """
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


def validate_schedule(schedule: Mapping) -> None:
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
    if not isinstance(generator_versions, Mapping):
        raise ManifestError("generator_versions が mapping でない")
    actual_keys = set(generator_versions)
    missing = sorted(_GENERATOR_KEYS - actual_keys)
    extra = sorted(
        actual_keys - _GENERATOR_KEYS,
        key=lambda value: (type(value).__name__, repr(value)),
    )
    if missing or extra:
        raise ManifestError(
            f"generator_versions key 集合が不一致: "
            f"missing={missing!r} extra={extra!r}"
        )
    root = root.resolve()
    validated = {}
    for key in sorted(_GENERATOR_KEYS):
        record = _source_record(
            generator_versions[key], field=f"generator_versions.{key}",
        )
        canonical_path = _GENERATOR_SOURCES[key]
        if record["path"] != canonical_path:
            raise ManifestError(
                f"generator_versions.{key}.path が canonical path と不一致: "
                f"{record['path']!r} != {canonical_path!r}"
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


def _build_manifest_from_snapshot(
    *, freeze: Mapping, freeze_record: Mapping, freeze_source_path: Path,
    spec_sha256, schedule, run_contract, binding_identity, campaign_ids,
    allowed_excluded_reasons, generator_versions, campaign_config_preimages=None,
    root: Path,
) -> _artifacts.OfficialManifest:
    """一度捕捉した freeze snapshot から manifest を組み立てる private core。"""
    known_axes_record = _source_record(
        freeze.get("known_axes_freeze"), field="known_axes_freeze",
    )
    _find_recorded_source(known_axes_record, freeze_path=freeze_source_path)

    validate_schedule(schedule)
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
        "spec_sha256": _sha256_text(spec_sha256, field="spec_sha256"),
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
        "holdout_references": holdout_references,
        "allowed_excluded_reasons": reasons,
        "generator_versions": _validate_generators(generator_versions, root=root),
    }
    document["manifest_id"] = _manifest_id(document)
    return _artifacts.OfficialManifest(document)


def _build_manifest(
    *, freeze_path, spec_sha256, schedule, run_contract, binding_identity, campaign_ids,
    allowed_excluded_reasons, generator_versions, campaign_config_preimages=None,
) -> _artifacts.OfficialManifest:
    """参照 hash と実走契約だけを持つ 8b oracle manifest を組み立てる。"""
    freeze_path = Path(freeze_path)
    freeze = _load_json_object(freeze_path)
    freeze_record = _path_record(freeze_path)
    return _build_manifest_from_snapshot(
        freeze=freeze,
        freeze_record=freeze_record,
        freeze_source_path=freeze_path,
        spec_sha256=spec_sha256,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=binding_identity,
        campaign_ids=campaign_ids,
        allowed_excluded_reasons=allowed_excluded_reasons,
        generator_versions=generator_versions,
        campaign_config_preimages=campaign_config_preimages,
        root=ROOT,
    )


def _build_manifest_from_ratified(
    ratified, *, spec_sha256, schedule, run_contract, binding_identity, campaign_ids,
    allowed_excluded_reasons, generator_versions, root=ROOT,
) -> _artifacts.OfficialManifest:
    """loader が返した active snapshot を再読込せず manifest へ射影する。"""
    from . import s8b_ratified_freeze

    if type(ratified) is not s8b_ratified_freeze.RatifiedFreeze:
        raise ManifestError("ratified freeze exact type が必要")
    root = Path(root)
    freeze_rel = (
        "output/s8b-freeze/"
        f"holdout_freeze.v2.g{ratified.generation_number}.json"
    )
    freeze_record = {"path": freeze_rel, "sha256": ratified.sha256}
    return _build_manifest_from_snapshot(
        freeze=_mutable_json_tree(ratified.document),
        freeze_record=freeze_record,
        freeze_source_path=root / freeze_rel,
        spec_sha256=spec_sha256,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=binding_identity,
        campaign_ids=campaign_ids,
        allowed_excluded_reasons=allowed_excluded_reasons,
        generator_versions=generator_versions,
        root=root,
    )


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


def _write_manifest(path, manifest) -> None:
    """manifest を create-only の同一 filesystem atomic link で封印する。"""
    if type(manifest) is not _artifacts.OfficialManifest:
        raise _artifacts.OracleArtifactTypeError(
            "write_manifest は OfficialManifest exact type のみ受理する")
    _atomic_create_json(Path(path), manifest)


def _candidate_output_parts(raw_output: str) -> tuple[str, ...]:
    if not isinstance(raw_output, str) or not raw_output or "\x00" in raw_output:
        raise ManifestCliError("invalid-output-path")
    path = PurePosixPath(raw_output)
    parts = path.parts
    prefix = PurePosixPath(MANIFEST_CANDIDATE_DIR).parts
    if (path.is_absolute() or path.as_posix() != raw_output
            or len(parts) <= len(prefix) or parts[:len(prefix)] != prefix
            or any(part in {"", ".", ".."} for part in parts)):
        raise ManifestCliError("invalid-output-path")
    return parts


def _write_approved_manifest(
    raw_output: str, document: Mapping, *, root=ROOT,
) -> None:
    """CLI candidate を dirfd traversal + nofollow + exclusive-create で書く。"""
    if type(document) is not _artifacts.OfficialManifest:
        raise ManifestCliError("invalid-manifest-type")
    parts = _candidate_output_parts(raw_output)
    try:
        raw = (json.dumps(
            document, ensure_ascii=False, indent=2, allow_nan=False,
        ) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ManifestCliError("invalid-manifest-json", str(exc)) from exc

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    cloexec = getattr(os, "O_CLOEXEC", None)
    if nofollow is None or directory is None or cloexec is None:
        raise ManifestCliError("safe-open-unavailable")

    opened_dirs: list[int] = []
    leaf_fd = None
    leaf_identity = None
    current_fd = None
    completed = False
    try:
        root_path = Path(root).resolve(strict=True)
        current_fd = os.open(
            root_path, os.O_RDONLY | directory | cloexec | nofollow,
        )
        opened_dirs.append(current_fd)
        candidate_prefix_size = len(PurePosixPath(MANIFEST_CANDIDATE_DIR).parts)
        for index, part in enumerate(parts[:-1]):
            try:
                next_fd = os.open(
                    part, os.O_RDONLY | directory | cloexec | nofollow,
                    dir_fd=current_fd,
                )
            except FileNotFoundError:
                # CLI が作成してよい directory は fixed candidate root だけ。
                # その配下の caller 指定 subdirectory は既存かつ nofollow の場合のみ辿る。
                if index >= candidate_prefix_size:
                    raise
                os.mkdir(part, mode=0o755, dir_fd=current_fd)
                next_fd = os.open(
                    part, os.O_RDONLY | directory | cloexec | nofollow,
                    dir_fd=current_fd,
                )
            opened_dirs.append(next_fd)
            current_fd = next_fd

        try:
            leaf_fd = os.open(
                parts[-1],
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow | cloexec,
                0o644,
                dir_fd=current_fd,
            )
        except FileExistsError as exc:
            raise ManifestCliError("output-exists") from exc
        info = os.fstat(leaf_fd)
        if not stat.S_ISREG(info.st_mode):
            raise ManifestCliError("invalid-output-leaf")
        leaf_identity = (info.st_dev, info.st_ino)
        view = memoryview(raw)
        while view:
            written = os.write(leaf_fd, view)
            if written <= 0:
                raise OSError("manifest write が進行しない")
            view = view[written:]
        os.fsync(leaf_fd)
        os.fsync(current_fd)
        completed = True
    except ManifestCliError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise ManifestCliError("invalid-output-path", str(exc)) from exc
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        if leaf_identity is not None and current_fd is not None and not completed:
            # 書込み失敗時だけ同一 inode の partial leaf を回収する。成功時は残す。
            try:
                info = os.stat(
                    parts[-1], dir_fd=current_fd, follow_symlinks=False,
                )
                if ((info.st_dev, info.st_ino) == leaf_identity
                        and stat.S_ISREG(info.st_mode)):
                    os.unlink(parts[-1], dir_fd=current_fd)
            except OSError:
                pass
        for directory_fd in reversed(opened_dirs):
            os.close(directory_fd)


@_seal_verified_manifest
def verify_manifest(
    path, *, root, freeze_document, freeze_sha256, approved_spec, _seal,
) -> VerifiedManifest:
    """manifest の参照 hash、schedule、block/campaign 束縛を再照合する。

    ``freeze_document`` / ``freeze_sha256`` は必須 (C2-7)。freeze を disk から
    再読込せず、hash 検証済みの単一 object だけを使う。通常 caller は
    ``load_verified_freeze`` の戻り値を渡し、公式 report CLI は publish 済み
    ratified 経路の ``load_ratified_freeze`` → ``reverify_published_freeze`` が
    historical contract で再検証した同一 document/sha256 を渡す。verify から use
    までの freeze byte 差替え (TOCTOU) を
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
    freeze = _mutable_json_tree(freeze_document)

    known_record = _source_record(
        document.get("known_axes_freeze"), field="known_axes_freeze",
    )
    known_path = _resolve_source(known_record["path"], root=root)
    if _file_sha256(known_path) != known_record["sha256"]:
        raise ManifestError("known_axes byte sha256 が manifest と不一致")
    if freeze.get("known_axes_freeze") != known_record:
        raise ManifestError("freeze と manifest の known_axes 参照が不一致")

    validate_schedule(document.get("schedule"))
    if document.get("schedule_sha256") != schedule_sha256(document["schedule"]):
        raise ManifestError("schedule_sha256 が再計算値と不一致")
    actual_cells = _schedule_cells(document["schedule"])
    schedule_holdouts = {holdout_id for holdout_id, _ in actual_cells}
    frozen_holdouts = freeze.get("holdouts")
    if (not isinstance(frozen_holdouts, Mapping)
            or schedule_holdouts != set(frozen_holdouts)):
        raise ManifestError("schedule holdout 集合が freeze.holdouts と完全一致しない")
    expected_cells = {
        (holdout_id, configuration_id)
        for holdout_id in frozen_holdouts
        for configuration_id in _holdout_configuration_ids(freeze, holdout_id)
    }
    if actual_cells != expected_cells:
        raise ManifestError(
            "schedule cell 集合が freeze の holdout-configuration product と"
            "完全一致しない"
        )
    blocks = [block["block_id"] for block in document["schedule"]["blocks"]]
    campaigns = document.get("campaign_ids")
    if not isinstance(campaigns, dict) or set(campaigns) != set(blocks):
        raise ManifestError("campaign_ids が block と一対一でない")
    if (any(not isinstance(value, str) or not value for value in campaigns.values())
            or len(set(campaigns.values())) != len(campaigns)):
        raise ManifestError("campaign ID が空または重複")

    expected_holdout_ids = sorted(frozen_holdouts)
    _validate_execution_snapshot(freeze, holdout_ids=expected_holdout_ids)
    run_contract = _validate_run_contract(document.get("run_contract"))
    binding_identity = _validate_binding_identity(
        document.get("binding_identity"), schedule=document["schedule"],
    )
    generator_versions = _validate_generators(
        document.get("generator_versions"), root=root,
    )
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

    from . import s8b_oracle_spec

    try:
        approved = s8b_oracle_spec.validate_approved_spec_snapshot(
            approved_spec, root=root,
        )
    except s8b_oracle_spec.ReviewedSpecError as exc:
        raise ManifestError(f"approved spec が不正: {exc}") from exc
    spec = _mutable_json_tree(approved.document)
    parameters = spec["schedule_parameters"]
    expected_schedule = build_schedule(
        n=parameters["n"],
        master_seed=parameters["master_seed"],
        block_sizes=parameters["block_sizes"],
        holdout_ids=parameters["holdout_ids"],
        configuration_ids=parameters["configuration_ids"],
    )
    if document["schedule"] != expected_schedule:
        raise ManifestError("schedule が approved spec の再生成値と不一致")
    if campaigns != spec["campaign_ids"]:
        raise ManifestError("campaign_ids が approved spec と不一致")
    if run_contract != spec["run_contract"]:
        raise ManifestError("run_contract が approved spec と不一致")
    if binding_identity != spec["binding_identity"]:
        raise ManifestError("binding_identity が approved spec と不一致")
    if reasons != spec["allowed_excluded_reasons"]:
        raise ManifestError("allowed_excluded_reasons が approved spec と不一致")
    if generator_versions != spec["generator_versions"]:
        # 両側の canonical path/実 byte hash 検査後の defense-in-depth。
        raise ManifestError("generator_versions が approved spec と不一致")
    recorded_spec_sha256 = _sha256_text(
        document.get("spec_sha256"), field="spec_sha256",
    )
    if recorded_spec_sha256 != approved.sha256:
        raise ManifestError("spec_sha256 が approved spec と不一致")

    without_id = dict(document)
    recorded_id = without_id.pop("manifest_id", None)
    if recorded_id != _manifest_id(without_id):
        raise ManifestError("manifest_id が内容と一致しない")
    official = _artifacts.OfficialManifest(document)
    return VerifiedManifest(
        document=official, sha256=_canonical_sha256(official), _seal=_seal,
    )


del _seal_verified_manifest


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


def build_approved_manifest(raw_output: str, *, root=ROOT) -> _artifacts.OfficialManifest:
    """active ratified freeze と pinned reviewed spec だけから candidate を作る。"""
    from . import s8b_oracle_spec
    from . import s8b_ratified_freeze

    root = Path(root)
    try:
        ratified = s8b_ratified_freeze.load_ratified_freeze(root)
        s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)
    except s8b_ratified_freeze.RatifiedFreezeError as exc:
        reason = (
            "no-active-ratified-freeze"
            if exc.reason == "no-active" else exc.reason
        )
        raise ManifestCliError(reason, str(exc)) from exc

    try:
        approved = s8b_oracle_spec.load_approved_spec(root)
    except s8b_oracle_spec.ReviewedSpecError as exc:
        raise ManifestCliError(exc.reason, str(exc)) from exc

    spec = approved.document
    parameters = spec["schedule_parameters"]
    freeze_holdouts = ratified.document.get("holdouts")
    if not isinstance(freeze_holdouts, Mapping):
        raise ManifestCliError("invalid-ratified-freeze", "holdouts が object でない")
    holdout_ids = parameters["holdout_ids"]
    configuration_ids = parameters["configuration_ids"]
    if list(holdout_ids) != sorted(freeze_holdouts):
        raise ManifestCliError(
            "approved-spec-cell-product-mismatch",
            "spec holdout_ids が active freeze の全 holdout と一致しない",
        )
    if list(configuration_ids) != sorted(configuration_ids):
        raise ManifestCliError(
            "approved-spec-cell-product-mismatch",
            "spec configuration_ids が sort 済みでない",
        )
    for holdout_id in holdout_ids:
        if set(configuration_ids) != _holdout_configuration_ids(
                ratified.document, holdout_id):
            raise ManifestCliError(
                "approved-spec-cell-product-mismatch",
                f"{holdout_id} の構成集合が spec と一致しない",
            )

    try:
        result = _build_manifest_from_ratified(
            ratified,
            spec_sha256=approved.sha256,
            schedule=_mutable_json_tree(approved.schedule),
            run_contract=spec["run_contract"],
            binding_identity=spec["binding_identity"],
            campaign_ids=spec["campaign_ids"],
            allowed_excluded_reasons=spec["allowed_excluded_reasons"],
            generator_versions=spec["generator_versions"],
            root=root,
        )
    except ManifestCliError:
        raise
    except ManifestError as exc:
        raise ManifestCliError("approved-manifest-invalid", str(exc)) from exc
    _write_approved_manifest(raw_output, result, root=root)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="approved 8b oracle manifest candidate を構築する",
        allow_abbrev=False,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    approved = subparsers.add_parser("build-approved", allow_abbrev=False)
    approved.add_argument("--output", required=True)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build-approved":
            build_approved_manifest(args.output, root=ROOT)
    except ManifestCliError as exc:
        print(f"refused: {exc.reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover - direct CLI execution
    raise SystemExit(main())
