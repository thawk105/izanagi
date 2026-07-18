# -*- coding: utf-8 -*-
"""8b selector 実験の holdout 未既知性を検索し、実走前に凍結する。

使い方:
  python3 orchestrator/campaign/s8b_holdout_freeze.py search
  python3 orchestrator/campaign/s8b_holdout_freeze.py generate --confirmed-by NAME --confirmed-at DATE
  python3 orchestrator/campaign/s8b_holdout_freeze.py verify
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

SCRIPT_REL = "orchestrator/campaign/s8b_holdout_freeze.py"
FREEZE_REL = "output/s8b-freeze/holdout_freeze.json"
FREEZE_PATH = ROOT / FREEZE_REL
DESIGN_REL = "docs/phase3-8b-descriptor-design.md"
KNOWN_AXES_REL = "output/s1-freeze/known_axes_freeze.json"
EXCLUDED_PATHS = ("output/s8b-freeze/",)

RRATIO_KEY = "ycsb_" + "rratio"
SKEW_KEY = "ycsb_" + "zipf_skew"
RMW_KEY = "ycsb_" + "rmw"

RRATIO_TEMPLATE = (
    '(?:ycsb_rratio=<v>|"ycsb_rratio": "<v>"|"ycsb_rratio":"<v>")'
)
SKEW_TEMPLATE = (
    '(?:ycsb_zipf_skew=<v>|"ycsb_zipf_skew": "<v>"|"ycsb_zipf_skew":"<v>")'
)
RMW_TEMPLATE = '(?:ycsb_rmw=<v>|"ycsb_rmw": "<v>"|"ycsb_rmw":"<v>")'
AXIS_TEMPLATES = {
    "rratio": RRATIO_TEMPLATE,
    "skew": SKEW_TEMPLATE,
    "rmw": RMW_TEMPLATE,
}

_HOLDOUT_HIGH = "8" + "0"
_HOLDOUT_LOW = "2" + "0"
_POSITIVE_RATIO = "5" + "0"
_FIXED_SKEW = "0" + ".9"
_FIXED_RMW = "0"


def _holdout(candidate_id: str, ratio: str) -> Dict:
    return {
        "candidate_id": candidate_id,
        "ycsb": {
            SKEW_KEY: _FIXED_SKEW,
            RRATIO_KEY: ratio,
            RMW_KEY: _FIXED_RMW,
        },
        "records": 1_000_000,
        "threads": 48,
    }


HOLDOUTS = {
    "rr80": _holdout("H1", _HOLDOUT_HIGH),
    "rr20": _holdout("H2", _HOLDOUT_LOW),
}
DERANGEMENT = {"rr80": "rr20", "rr20": "rr80"}
VARIANT_NAMES = (
    "p2_2_flag_opt",
    "backoff_fixed_best",
    "sort_best",
    "system_gate",
    "ident_all",
    "stock_common",
)
BINDING_RULE = "nearest-read-ratio-v1"
KNOWN_READ_RATIOS = {"read-heavy": 95, "balanced": 50, "write-heavy": 5}
STRIP_KEYS = frozenset({
    "reference_fitness_tps", "reference_points", "remeasure_reference",
})

MATCH_CONVENTION = (
    "file-level conjunction: 同一ファイルが rratio/skew/rmw の三軸正規表現すべてに"
    "一致した場合だけ 1 hit と数える"
)
FILE_ENUMERATION = (
    "repo root の git ls-files -z -s (通常ファイル mode 100644/100755 のみ。gitlink/symlink は"
    "テキストでないため除外) と git ls-files -z --others --exclude-standard の和集合に、"
    "git -C external/ccbench ls-files -z -s の各通常ファイル path へ external/ccbench/ を"
    "前置した集合を加える"
)
SCOPE_NOTE = (
    "この確認はリポジトリに記録された既知性に関するものであり、既存 WAL が欠落している"
    "可能性は解消しない。"
)
BINDING_RULE_NOTE = (
    "nearest-read-ratio-v1 は設計書未規定の実装裁定。生成には人間確認 "
    "(--confirmed-by) が必須。"
)
REFREEZE_NOTE = (
    "floor/budget は対象別 floor 再実測後に再凍結 + 承認で充填する (設計 §5.2)"
)
WHAT = "8b selector 実験の holdout freeze (設計 §3.1/§3.2/§5.1)"
SCHEMA_VERSION = "8b-holdout-freeze/v1"


class FreezeError(RuntimeError):
    """凍結生成・照合を fail-closed で止めるエラー。"""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError as exc:
        raise FreezeError(f"sha256 対象を読めない: {path}: {exc}") from exc
    return h.hexdigest()


def _canonical_sha256(value: Mapping) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> Dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FreezeError(f"JSON を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FreezeError(f"JSON top-level が object ではない: {path}")
    return value


def _run_git(args: Sequence[str], cwd: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=cwd, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise FreezeError(
            f"git {' '.join(args)} に失敗: {str(detail).strip()}"
        ) from exc
    return completed.stdout.strip()


def _run_git_z(args: Sequence[str], cwd: Path) -> Tuple[str, ...]:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=cwd, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raw = getattr(exc, "stderr", b"") or str(exc).encode("utf-8", "replace")
        detail = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
        raise FreezeError(f"git {' '.join(args)} に失敗: {detail.strip()}") from exc
    try:
        return tuple(
            part.decode("utf-8") for part in completed.stdout.split(b"\0") if part
        )
    except UnicodeDecodeError as exc:
        raise FreezeError(f"git {' '.join(args)} の path が UTF-8 でない") from exc


def _tracked_regular_files(cwd: Path) -> set:
    """git ls-files -s から通常ファイル (mode 100644/100755) だけを取る。

    gitlink (160000、入れ子 submodule) と symlink (120000) はテキストとして検索できず、
    worktree に実体が無いこともあるため列挙から除外する (FILE_ENUMERATION に明記)。"""
    paths = set()
    for entry in _run_git_z(["ls-files", "-z", "-s"], cwd):
        meta, sep, rel = entry.partition("\t")
        if not sep or not rel:
            raise FreezeError(f"git ls-files -s の出力を解釈できない: {entry!r}")
        mode = meta.split(" ", 1)[0]
        if mode in ("100644", "100755"):
            paths.add(rel)
        elif mode not in ("160000", "120000"):
            raise FreezeError(f"未知の git file mode: {mode} ({rel})")
    return paths


def enumerate_repository_files(root: Path = ROOT) -> Tuple[str, ...]:
    """worktree と ccbench submodule の検索対象を git の列挙から確定する。"""
    root = Path(root)
    paths = _tracked_regular_files(root)
    for rel in _run_git_z(["ls-files", "-z", "--others", "--exclude-standard"], root):
        # untracked 側は mode 情報が無い。symlink は tracked 側 (120000 除外) と対称に、
        # 非ファイル (入れ子 git repo を含むディレクトリは ls-files --others がディレクトリ
        # 自体を列挙する) は検索不能なので除外する。
        path = root / rel
        if path.is_file() and not path.is_symlink():
            paths.add(rel)

    submodule = root / "external/ccbench"
    for rel in _tracked_regular_files(submodule):
        paths.add("external/ccbench/" + rel)
    return tuple(sorted(paths))


def _normalise_files(root: Path, files: Iterable[os.PathLike | str]) -> Tuple[str, ...]:
    root_abs = Path(os.path.abspath(root))
    normalised = set()
    for raw in files:
        path = Path(raw)
        candidate = path if path.is_absolute() else root_abs / path
        candidate = Path(os.path.abspath(candidate))
        try:
            rel = candidate.relative_to(root_abs).as_posix()
        except ValueError as exc:
            raise FreezeError(f"検索対象が repo root 外: {candidate}") from exc
        if rel == "." or rel.startswith("../"):
            raise FreezeError(f"検索対象 path が不正: {raw}")
        normalised.add(rel)
    return tuple(sorted(normalised))


def _is_excluded(rel: str) -> bool:
    return any(rel.startswith(prefix) for prefix in EXCLUDED_PATHS)


def _expressions(rratio: str, skew: str, rmw: str) -> Dict[str, str]:
    values = {"rratio": rratio, "skew": skew, "rmw": rmw}
    return {
        axis: template.replace("<v>", values[axis])
        for axis, template in AXIS_TEMPLATES.items()
    }


def concrete_axis_encodings(axis: str, value: str) -> Tuple[str, str, str]:
    """番人テスト用に、ある軸の三つの canonical 符号化を実行時生成する。"""
    keys = {"rratio": RRATIO_KEY, "skew": SKEW_KEY, "rmw": RMW_KEY}
    if axis not in keys:
        raise FreezeError(f"未知の検索軸: {axis}")
    key = keys[axis]
    return (
        key + "=" + value,
        '"' + key + '": "' + value + '"',
        '"' + key + '":"' + value + '"',
    )


def _read_search_text(path: Path) -> Optional[str]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise FreezeError(f"検索対象を読めない: {path}: {exc}") from exc
    if b"\0" in payload[:8192]:
        return None
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _scan_one(
    texts: Mapping[str, str], candidate_id: str, expressions: Mapping[str, str],
) -> Dict:
    compiled = {axis: re.compile(expression) for axis, expression in expressions.items()}
    per_axis_paths = {axis: [] for axis in expressions}
    conjunction_hits = []
    for rel, text in texts.items():
        matched = {axis: bool(pattern.search(text)) for axis, pattern in compiled.items()}
        for axis, is_match in matched.items():
            if is_match:
                per_axis_paths[axis].append(rel)
        if all(matched.values()):
            conjunction_hits.append(rel)
    per_axis_counts = {axis: len(paths) for axis, paths in per_axis_paths.items()}
    conjunction_hits.sort()
    hash_input = {
        "candidate_id": candidate_id,
        "expressions": dict(expressions),
        "per_axis_counts": per_axis_counts,
        "conjunction_hits": conjunction_hits,
    }
    return {
        **hash_input,
        "result_sha256": _canonical_sha256(hash_input),
    }


def search_repository(
    root: Path = ROOT, files: Optional[Iterable[os.PathLike | str]] = None,
    exempt_exact: Optional[Mapping[str, str]] = None,
) -> Dict:
    """三軸 conjunction を検索する。files 指定時は git 列挙を注入値で置換する。

    ``exempt_exact`` は launch_validate の (ix)-9 用 API であり、検証済み
    active-chain artifact だけを repo 相対の exact path + bytes の SHA-256 で
    scan から免除する。指定時は ``output/s8b-freeze/`` の prefix 除外を無効化し、
    path が未指定または hash 不一致の file は通常どおり scan する。列挙結果からは
    免除しない。既定の ``None`` では v1 互換のため従来の prefix 除外を維持する。
    """
    root = Path(root)
    enumerated = enumerate_repository_files(root) if files is None else tuple(files)
    enumerated_rel_paths = _normalise_files(root, enumerated)
    rel_paths = (
        tuple(rel for rel in enumerated_rel_paths if not _is_excluded(rel))
        if exempt_exact is None
        else enumerated_rel_paths
    )

    texts: Dict[str, str] = {}
    skipped = 0
    for rel in rel_paths:
        path = root / rel
        if not path.is_file():
            raise FreezeError(f"git が列挙した検索対象が file ではない: {rel}")
        if exempt_exact is not None and rel in exempt_exact:
            try:
                payload = path.read_bytes()
            except OSError as exc:
                raise FreezeError(f"検索対象を読めない: {path}: {exc}") from exc
            if hashlib.sha256(payload).hexdigest() == exempt_exact[rel]:
                continue
            if b"\0" in payload[:8192]:
                text = None
            else:
                try:
                    text = payload.decode("utf-8")
                except UnicodeDecodeError:
                    text = None
        else:
            text = _read_search_text(path)
        if text is None:
            skipped += 1
        else:
            texts[rel] = text

    top_level_dirs = sorted({rel.split("/", 1)[0] for rel in rel_paths if "/" in rel})
    scope = {
        "file_enumeration": FILE_ENUMERATION,
        "top_level_dirs": top_level_dirs,
        "file_count": len(rel_paths),
        "skipped_binary_count": skipped,
        "excluded_paths": list(EXCLUDED_PATHS) if exempt_exact is None else [],
    }

    holdout_results = {}
    for name, holdout in HOLDOUTS.items():
        ycsb = holdout["ycsb"]
        expressions = _expressions(ycsb[RRATIO_KEY], ycsb[SKEW_KEY], ycsb[RMW_KEY])
        holdout_results[name] = _scan_one(
            texts, holdout["candidate_id"], expressions,
        )

    positive_expressions = _expressions(
        _POSITIVE_RATIO, _FIXED_SKEW, _FIXED_RMW,
    )
    positive = _scan_one(texts, "rr50-positive-control", positive_expressions)
    positive_control = {
        "expressions": positive["expressions"],
        "per_axis_counts": positive["per_axis_counts"],
        "hit_count": len(positive["conjunction_hits"]),
        "hit_paths": positive["conjunction_hits"][:10],
    }
    return {
        "match_convention": MATCH_CONVENTION,
        "search": scope,
        "holdouts": holdout_results,
        "positive_control": positive_control,
    }


def recompute_snapshot_zero_hit_sha256(
    candidate_id: str, expressions: Mapping, per_axis_counts: Mapping,
) -> str:
    """記録済みフィールドから zero_hit_output_sha256 を再計算する (v2 未知性層1 の共用)。

    conjunction_hits を空 (未既知性 = 0 hit) に固定した snapshot_input の canonical sha256。
    v1 verify_document の層1 と v2 verifier (s8b_ratified_freeze) が同一ロジックを通る
    (挙動不変。式は verify_document の snapshot_input と byte 一致する)。"""
    snapshot_input = {
        "candidate_id": candidate_id,
        "expressions": dict(expressions),
        "per_axis_counts": dict(per_axis_counts),
        "conjunction_hits": [],
    }
    return _canonical_sha256(snapshot_input)


def holdout_conjunction_hits(texts: Mapping[str, str]) -> Dict[str, list]:
    """与えた texts (path→内容) に各 holdout の三軸 conjunction を適用し hit path list を返す。

    v2 未知性層2 の「closure bytes から期待 hit を導出」用 (verifier が同一 bytes から
    導出し、予告 bool を信じない)。HOLDOUTS の expressions を _scan_one に通すだけで、
    search_repository と同じ MATCH_CONVENTION を共有する。"""
    out: Dict[str, list] = {}
    for name, holdout in HOLDOUTS.items():
        ycsb = holdout["ycsb"]
        expressions = _expressions(ycsb[RRATIO_KEY], ycsb[SKEW_KEY], ycsb[RMW_KEY])
        result = _scan_one(texts, holdout["candidate_id"], expressions)
        out[name] = list(result["conjunction_hits"])
    return out


def _assert_search_pass(report: Mapping) -> None:
    errors = []
    holdouts = report.get("holdouts")
    if not isinstance(holdouts, Mapping):
        raise FreezeError("search report に holdouts がない")
    for name in HOLDOUTS:
        result = holdouts.get(name)
        if not isinstance(result, Mapping):
            errors.append(f"{name}: 検索結果がない")
            continue
        hits = result.get("conjunction_hits")
        if not isinstance(hits, list):
            errors.append(f"{name}: conjunction_hits が list でない")
        elif hits:
            errors.append(f"{name}: holdout hit {len(hits)} 件: {hits}")
    positive = report.get("positive_control")
    hit_count = positive.get("hit_count") if isinstance(positive, Mapping) else None
    if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:
        errors.append("rr50 陽性対照が 0 件: 検索式の偽保証を排除できない")
    if errors:
        raise FreezeError("; ".join(errors))


def select_anchor(
    read_ratio_percent: int,
    known_ratios: Mapping[str, int] = KNOWN_READ_RATIOS,
) -> Tuple[str, Dict[str, int]]:
    """read ratio の最近傍 workload を選び、同距離なら人間裁定へ倒す。"""
    if not isinstance(read_ratio_percent, int) or isinstance(read_ratio_percent, bool):
        raise FreezeError("read_ratio_percent が整数でない")
    if not known_ratios:
        raise FreezeError("既知 workload の read ratio が空")
    distances = {
        workload: abs(read_ratio_percent - ratio)
        for workload, ratio in known_ratios.items()
    }
    minimum = min(distances.values())
    nearest = [workload for workload, distance in distances.items() if distance == minimum]
    if len(nearest) != 1:
        raise FreezeError(
            f"{BINDING_RULE}: 最近傍が tie: read_ratio={read_ratio_percent}, "
            f"workloads={sorted(nearest)}"
        )
    return nearest[0], distances


def _strip_measurements(value, removed: set[str]):
    if isinstance(value, dict):
        cleaned = {}
        for key, child in value.items():
            if key in STRIP_KEYS:
                removed.add(key)
            else:
                cleaned[key] = _strip_measurements(child, removed)
        return cleaned
    if isinstance(value, list):
        return [_strip_measurements(child, removed) for child in value]
    return copy.deepcopy(value)


def build_variant_binding(
    read_ratio_percent: int, known_axes: Mapping,
) -> Dict:
    anchor, distances = select_anchor(read_ratio_percent)
    all_entries = known_axes.get("entries")
    if not isinstance(all_entries, Mapping):
        raise FreezeError("known_axes freeze に entries object がない")
    anchor_entries = all_entries.get(anchor)
    if not isinstance(anchor_entries, Mapping):
        raise FreezeError(f"known_axes freeze に anchor workload がない: {anchor}")
    missing = [name for name in VARIANT_NAMES if not isinstance(anchor_entries.get(name), Mapping)]
    if missing:
        raise FreezeError(f"known_axes freeze の 6 構成が不足: {anchor}: {missing}")

    removed: set[str] = set()
    entries = {
        name: _strip_measurements(anchor_entries[name], removed)
        for name in VARIANT_NAMES
    }
    return {
        "rule": BINDING_RULE,
        "anchor_workload": anchor,
        "distances": distances,
        "entries": entries,
        "stripped_keys": sorted(removed),
    }


def _source_record(root: Path, rel: str) -> Dict[str, str]:
    path = root / rel
    if not path.is_file():
        raise FreezeError(f"凍結 source が存在しない: {rel}")
    return {"path": rel, "sha256": _sha256(path)}


def build_document(
    *,
    confirmed_by: str,
    confirmed_at: str,
    root: Path = ROOT,
    files: Optional[Iterable[os.PathLike | str]] = None,
    frozen_at_head: Optional[str] = None,
) -> Dict:
    """検索合格後に holdout freeze 文書をメモリ上で構成する。"""
    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
        raise FreezeError("--confirmed-by は空でない人間確認者名が必須")
    if not isinstance(confirmed_at, str) or not confirmed_at.strip():
        raise FreezeError("--confirmed-at は空でない確認日時が必須")
    root = Path(root)
    report = search_repository(root, files)
    _assert_search_pass(report)

    known_axes = _load_json(root / KNOWN_AXES_REL)
    holdouts = {}
    for name, frozen in HOLDOUTS.items():
        result = report["holdouts"][name]
        unknownness = {
            "search_scope": copy.deepcopy(report["search"]),
            "expressions": copy.deepcopy(result["expressions"]),
            "per_axis_counts": copy.deepcopy(result["per_axis_counts"]),
            "conjunction_hits": copy.deepcopy(result["conjunction_hits"]),
            "zero_hit_output_sha256": result["result_sha256"],
            "positive_control": copy.deepcopy(report["positive_control"]),
            "confirmed_by": confirmed_by,
        }
        holdouts[name] = {
            **copy.deepcopy(frozen),
            "unknownness_check": unknownness,
            "variant_binding": build_variant_binding(
                int(frozen["ycsb"][RRATIO_KEY]), known_axes,
            ),
        }

    head = frozen_at_head or _run_git(["rev-parse", "HEAD"], root)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise FreezeError(f"frozen_at_head が 40 桁 git SHA でない: {head!r}")
    return {
        "what": WHAT,
        "schema_version": SCHEMA_VERSION,
        "frozen_at_head": head,
        "design_source": _source_record(root, DESIGN_REL),
        "known_axes_freeze": _source_record(root, KNOWN_AXES_REL),
        "generator": _source_record(root, SCRIPT_REL),
        "match_convention": MATCH_CONVENTION,
        "search": copy.deepcopy(report["search"]),
        "holdouts": holdouts,
        "positive_control": copy.deepcopy(report["positive_control"]),
        "derangement": copy.deepcopy(DERANGEMENT),
        "confirmed_by": confirmed_by,
        "confirmed_at": confirmed_at,
        "floor": None,
        "budget": None,
        "refreeze_note": REFREEZE_NOTE,
        "scope_note": SCOPE_NOTE,
        "binding_rule_note": BINDING_RULE_NOTE,
    }


def generate(
    *,
    confirmed_by: str,
    confirmed_at: str,
    output_path: Path = FREEZE_PATH,
    root: Path = ROOT,
    files: Optional[Iterable[os.PathLike | str]] = None,
    frozen_at_head: Optional[str] = None,
) -> Dict:
    """holdout freeze を新規作成する。既存出力は上書きしない。"""
    output_path = Path(output_path)
    if output_path.exists():
        raise FreezeError(
            f"freeze が既に存在する: {output_path} — 再凍結は明示削除 + 再承認が必要"
        )
    doc = build_document(
        confirmed_by=confirmed_by,
        confirmed_at=confirmed_at,
        root=root,
        files=files,
        frozen_at_head=frozen_at_head,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("x", encoding="utf-8") as stream:
            json.dump(doc, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError as exc:
        raise FreezeError(f"freeze が既に存在する: {output_path}") from exc
    return doc


TOP_LEVEL_KEYS = {
    "what", "schema_version", "frozen_at_head", "design_source",
    "known_axes_freeze", "generator", "match_convention", "search", "holdouts",
    "positive_control", "derangement", "confirmed_by", "confirmed_at", "floor",
    "budget", "refreeze_note", "scope_note", "binding_rule_note",
}

# freeze v2 世代 schema の header/approval field (supersedes 連鎖・承認記録)。
# 承認済み世代の機械判定は s8b_ratified_freeze.load_ratified_freeze の責務であり、v1
# verify_document 経路 (LegacyFreeze 相当) はこれらの field を持つ document を一律
# invalid に倒す。これは **defense-in-depth であって信頼境界ではない** — 実境界は
# consumer が RatifiedFreeze のみ受理することであり (C1-9)、この union は v1 経路へ
# v2 document が誤って流れ込んだ場合の第二の遮断にすぎない。承認束縛検証を伴わない
# 世代を v1 経路で通せば未承認の floor/budget 差し替え世代が fail-open するため
# (F14 型: 宣言のみの遮断)、認識即拒否とする。旧 (approved_by 系) と新 (v2 header の
# 新規 field) の union を張り、いずれも v1 の 18 top-level key と重ならない。
GENERATION_SCHEMA_FIELDS = frozenset({
    # v1 骨格段階からの旧 header/self-approval field。
    "supersedes_sha256", "change_reason",
    "approved_by", "approved_at", "approval_scope",
    # F6/F7 確定後の v2 header 新規 field と外部 approval record の field 名。
    "generation_number", "env_tag",
    "floor_protocol", "floor_source", "measurement_closure",
    "approver", "scope",
})


def _reject_unratified_generation(doc: Mapping) -> None:
    """世代 schema field を持つ新世代 document を承認束縛未裁定として拒否する。"""
    if not isinstance(doc, Mapping):
        return
    present = sorted(GENERATION_SCHEMA_FIELDS & set(doc))
    if present:
        raise FreezeError(
            "未承認世代 document は発効しない: 世代 schema field "
            f"{present} を検出したが、承認束縛方式が §8 で未裁定 (fail-closed)"
        )


def _verify_source(doc: Mapping, field: str, root: Path, rel: str) -> None:
    """source を現行 worktree path の bytes hash で照合する。

    v1 単一 filename freeze は常に唯一の発効中 (active) 世代であり、その source は
    worktree の現物と完全一致しなければならない (ドリフト検知)。record と不一致なら
    拒否 (fail-closed)。frozen_at_head 時点の git blob への救済照合は、世代別不変
    filename + supersedes 連鎖 + 承認束縛を伴う v2 の「旧世代」再検証専用であり、その
    束縛方式は §8 で未裁定 (未承認世代は _reject_unratified_generation が拒否) のため
    発効しない。唯一の active 世代へ blob 救済を適用すると、設計本文・known_axes・
    generator を worktree で改変しても (recorded が frozen_at_head の blob と一致する
    限り) verify が通り、active 世代のドリフト検知が骨抜きになる (fail-open) ため、
    ここでは worktree 完全一致のみを正とする。"""
    record = doc.get(field)
    if not isinstance(record, Mapping) or set(record) != {"path", "sha256"}:
        raise FreezeError(f"{field} schema が不正")
    if record.get("path") != rel:
        raise FreezeError(f"{field}.path 不一致: {record.get('path')!r}")
    actual = _sha256(root / rel)
    if record.get("sha256") != actual:
        raise FreezeError(
            f"{field} sha256 不一致: recorded={record.get('sha256')} actual={actual}"
        )


def _verify_head(recorded: object, root: Path, current_head: Optional[str]) -> None:
    if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{40}", recorded):
        raise FreezeError("frozen_at_head が 40 桁 git SHA でない")
    if current_head is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", current_head) or recorded != current_head:
            raise FreezeError(
                f"frozen_at_head 不一致: recorded={recorded} current={current_head}"
            )
        return
    try:
        _run_git(["cat-file", "-e", recorded + "^{commit}"], root)
        _run_git(["merge-base", "--is-ancestor", recorded, "HEAD"], root)
    except FreezeError as exc:
        raise FreezeError(
            f"frozen_at_head が現行 HEAD の commit ancestor でない: {recorded}"
        ) from exc


def verify_document(
    doc: Mapping,
    *,
    root: Path = ROOT,
    files: Optional[Iterable[os.PathLike | str]] = None,
    current_head: Optional[str] = None,
) -> None:
    """source hash、未知性検索、binding の三境界を現物から再照合する。

    未知性の検査は二層に分ける: (1) スナップショット整合 = 記録済みフィールドから
    zero_hit_output_sha256 を再計算して一致・記録済み conjunction_hits が空、
    (2) 現時点有効性 = 検索の再実行で conjunction 0 件 + 陽性対照 > 0。
    per_axis_counts / positive_control の件数は生成時点のスナップショットであり、
    無関係なファイル追加 (単一軸だけ一致する新規 campaign.lock 等) で経時変動する
    ため、再実行値との完全一致は要求しない。holdout を実走した後は再実行で
    conjunction hit が生じて (2) が失敗する — 未既知性は計測開始前にのみ成立する
    性質であり、これは意図した fails-closed である。"""
    _reject_unratified_generation(doc)
    if set(doc) != TOP_LEVEL_KEYS:
        raise FreezeError(
            f"freeze top-level keys が schema と不一致: {sorted(set(doc) ^ TOP_LEVEL_KEYS)}"
        )
    root = Path(root)
    if doc.get("what") != WHAT or doc.get("schema_version") != SCHEMA_VERSION:
        raise FreezeError("what/schema_version 不一致")
    head = doc.get("frozen_at_head")
    _verify_source(doc, "design_source", root, DESIGN_REL)
    _verify_source(doc, "known_axes_freeze", root, KNOWN_AXES_REL)
    _verify_source(doc, "generator", root, SCRIPT_REL)
    _verify_head(head, root, current_head)

    report = search_repository(root, files)
    _assert_search_pass(report)
    if doc.get("match_convention") != MATCH_CONVENTION:
        raise FreezeError("match_convention 不一致")
    if doc.get("derangement") != DERANGEMENT:
        raise FreezeError("derangement 不一致")
    if doc.get("scope_note") != SCOPE_NOTE or doc.get("binding_rule_note") != BINDING_RULE_NOTE:
        raise FreezeError("scope/binding rule note 不一致")
    if doc.get("refreeze_note") != REFREEZE_NOTE or doc.get("floor") is not None or doc.get("budget") is not None:
        raise FreezeError("floor/budget/refreeze_note 不一致")

    stored_search = doc.get("search")
    if not isinstance(stored_search, Mapping):
        raise FreezeError("search scope が object でない")
    if stored_search.get("file_enumeration") != FILE_ENUMERATION:
        raise FreezeError("search.file_enumeration 不一致")
    if stored_search.get("excluded_paths") != list(EXCLUDED_PATHS):
        raise FreezeError("search.excluded_paths 不一致")
    if not isinstance(stored_search.get("top_level_dirs"), list):
        raise FreezeError("search.top_level_dirs が list でない")
    for count_key in ("file_count", "skipped_binary_count"):
        count = stored_search.get(count_key)
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise FreezeError(f"search.{count_key} が非負整数でない")

    confirmed_by = doc.get("confirmed_by")
    confirmed_at = doc.get("confirmed_at")
    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
        raise FreezeError("confirmed_by が空")
    if not isinstance(confirmed_at, str) or not confirmed_at.strip():
        raise FreezeError("confirmed_at が空")
    holdouts_doc = doc.get("holdouts")
    if not isinstance(holdouts_doc, Mapping) or set(holdouts_doc) != set(HOLDOUTS):
        raise FreezeError("holdouts schema が不一致")

    known_axes = _load_json(root / KNOWN_AXES_REL)
    for name, frozen in HOLDOUTS.items():
        entry = holdouts_doc.get(name)
        if not isinstance(entry, Mapping):
            raise FreezeError(f"holdouts.{name} が object でない")
        expected_entry_keys = {
            "candidate_id", "ycsb", "records", "threads",
            "unknownness_check", "variant_binding",
        }
        if set(entry) != expected_entry_keys:
            raise FreezeError(f"holdouts.{name} schema が不一致")
        for field in ("candidate_id", "ycsb", "records", "threads"):
            if entry.get(field) != frozen[field]:
                raise FreezeError(f"holdouts.{name}.{field} 不一致")
        unknownness = entry.get("unknownness_check")
        if not isinstance(unknownness, Mapping):
            raise FreezeError(f"holdouts.{name}.unknownness_check がない")
        expected_unknownness_keys = {
            "search_scope", "expressions", "per_axis_counts", "conjunction_hits",
            "zero_hit_output_sha256", "positive_control", "confirmed_by",
        }
        if set(unknownness) != expected_unknownness_keys:
            raise FreezeError(f"holdouts.{name}.unknownness_check schema が不一致")
        current = report["holdouts"][name]
        # 決定論的に定数から導かれる欄は再実行値と一致しなければならない。
        if unknownness.get("expressions") != current["expressions"]:
            raise FreezeError(f"holdouts.{name}.unknownness_check.expressions 不一致")
        if unknownness.get("confirmed_by") != confirmed_by:
            raise FreezeError(f"holdouts.{name}.unknownness_check.confirmed_by 不一致")
        # 層1: スナップショット整合 — 記録済みフィールドから hash を再計算する。
        recorded_hits = unknownness.get("conjunction_hits")
        if recorded_hits != []:
            raise FreezeError(f"holdouts.{name}.unknownness_check.conjunction_hits が空でない")
        per_axis = unknownness.get("per_axis_counts")
        if (not isinstance(per_axis, Mapping) or set(per_axis) != set(AXIS_TEMPLATES)
                or any(not isinstance(v, int) or isinstance(v, bool) or v < 0
                       for v in per_axis.values())):
            raise FreezeError(f"holdouts.{name}.unknownness_check.per_axis_counts が不正")
        expected_zero_hit = recompute_snapshot_zero_hit_sha256(
            frozen["candidate_id"], unknownness["expressions"], per_axis,
        )
        if unknownness.get("zero_hit_output_sha256") != expected_zero_hit:
            raise FreezeError(
                f"holdouts.{name}.unknownness_check.zero_hit_output_sha256 が"
                "記録済みフィールドから再計算した値と一致しない"
            )
        # 層2: 現時点有効性 — 再実行の conjunction 0 件は _assert_search_pass が既に強制。
        if current["conjunction_hits"]:
            raise FreezeError(f"holdouts.{name}: 再実行検索で hit が生じた (既知化)")
        recorded_positive = unknownness.get("positive_control")
        if (not isinstance(recorded_positive, Mapping)
                or recorded_positive.get("expressions") != report["positive_control"]["expressions"]):
            raise FreezeError(f"holdouts.{name}.unknownness_check.positive_control.expressions 不一致")
        recorded_positive_hits = recorded_positive.get("hit_count")
        if (not isinstance(recorded_positive_hits, int) or isinstance(recorded_positive_hits, bool)
                or recorded_positive_hits <= 0):
            raise FreezeError(f"holdouts.{name}.unknownness_check.positive_control.hit_count が 0 以下")
        if unknownness.get("search_scope") != stored_search:
            raise FreezeError(f"holdouts.{name}.unknownness_check.search_scope 不一致")

        expected_binding = build_variant_binding(
            int(frozen["ycsb"][RRATIO_KEY]), known_axes,
        )
        if entry.get("variant_binding") != expected_binding:
            raise FreezeError(f"holdouts.{name}.variant_binding 不一致")

    positive_doc = doc.get("positive_control")
    if not isinstance(positive_doc, Mapping):
        raise FreezeError("positive_control が object でない")
    if positive_doc.get("expressions") != report["positive_control"]["expressions"]:
        raise FreezeError("positive_control.expressions 不一致")
    positive_hits = positive_doc.get("hit_count")
    if (not isinstance(positive_hits, int) or isinstance(positive_hits, bool)
            or positive_hits <= 0):
        raise FreezeError("positive_control.hit_count が 0 以下")


def verify(
    path: Path = FREEZE_PATH,
    *,
    root: Path = ROOT,
    files: Optional[Iterable[os.PathLike | str]] = None,
    current_head: Optional[str] = None,
) -> Dict:
    path = Path(path)
    if not path.is_file():
        raise FreezeError(f"freeze が存在しない: {path}")
    doc = _load_json(path)
    verify_document(doc, root=root, files=files, current_head=current_head)
    return doc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8b holdout freeze の検索・生成・照合")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("search", help="書き込みなしで未知性検索を実行する")

    generate_parser = subparsers.add_parser("generate", help="検索合格後に freeze を生成する")
    generate_parser.add_argument("--confirmed-by", required=True)
    generate_parser.add_argument("--confirmed-at", required=True)
    generate_parser.add_argument("--output", type=Path, default=FREEZE_PATH)

    verify_parser = subparsers.add_parser("verify", help="freeze を現物から再照合する")
    verify_parser.add_argument("path", nargs="?", type=Path, default=FREEZE_PATH)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "search":
            report = search_repository()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            _assert_search_pass(report)
        elif args.command == "generate":
            generate(
                confirmed_by=args.confirmed_by,
                confirmed_at=args.confirmed_at,
                output_path=args.output,
            )
            print(f"generated: {args.output}")
        else:
            verify(args.path)
            print(f"verified: {args.path}")
    except FreezeError as exc:
        print(f"fails-closed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
