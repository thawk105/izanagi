# -*- coding: utf-8 -*-
"""8b selector 実験の holdout 未既知性を検索し、実走前に凍結する。

使い方:
  python3 orchestrator/campaign/s8b_holdout_freeze.py search
  python3 orchestrator/campaign/s8b_holdout_freeze.py generate --confirmed-by NAME --confirmed-at DATE
  python3 orchestrator/campaign/s8b_holdout_freeze.py generate-v2-candidate --floor-result PATH --budget PATH
  python3 orchestrator/campaign/s8b_holdout_freeze.py verify
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"


_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

from . import t080_freeze_migration  # noqa: E402
from . import freeze_verification_hold as _freeze_hold  # noqa: E402

SCRIPT_REL = "orchestrator/campaign/s8b_holdout_freeze.py"
FREEZE_REL = "output/s8b-freeze/holdout_freeze.json"
FREEZE_PATH = ROOT / FREEZE_REL
DESIGN_REL = "docs/phase3-8b-descriptor-design.md"
KNOWN_AXES_REL = "output/s1-freeze/known_axes_freeze.json"
EXCLUDED_PATHS = ("output/s8b-freeze/",)

V2_SCHEMA_VERSION = "8b-holdout-freeze/v2"
FLOOR_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"
V2_CANDIDATE_REL = "output/s8b-freeze-candidates/holdout_freeze.v2.g1.json"
BUDGET_APPROVAL_REL = "output/s8b-freeze-budget-approvals/g1.json"
BUDGET_APPROVAL_SCOPE = "s8b-holdout-freeze/v2:g1-budget"
BUDGET_APPROVAL_SHA256: Optional[str] = "05d4d778826d7f0d93bdfbbd9e8c3ea09711b6c268bfba9086927bdc92f6549d"
_FLOOR_SELECTION_RULE_VERSION = "earliest-eligible-official-run-id/v1"
V2_ADDED_KEYS = frozenset({
    "generation_number", "supersedes_sha256", "env_tag",
    "floor_protocol", "floor_source", "measurement_closure",
})
BUDGET_KEYS = frozenset({
    "total_bench_s", "per_holdout_bench_s", "oracle_shared",
})
BUDGET_APPROVAL_KEYS = frozenset({"approved_at", "approver", "budget", "scope"})
V2_REFREEZE_NOTE_PREFIX = "floor/budget refreeze v2 g1; budget approval"

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


def _strict_json_pairs(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise FreezeError(f"JSON に duplicate key: {key!r}")
        value[key] = child
    return value


def _reject_json_constant(value: str):
    raise FreezeError(f"JSON に非有限定数: {value}")


def _assert_finite_json(value, *, label: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise FreezeError(f"{label} に非有限数")
    if isinstance(value, Mapping):
        for child in value.values():
            _assert_finite_json(child, label=label)
    elif isinstance(value, list):
        for child in value:
            _assert_finite_json(child, label=label)


def _strict_load_object_bytes(raw: bytes, label: str) -> Dict:
    """UTF-8・duplicate key・非有限数を拒否して top-level object を読む。"""
    try:
        text = raw.decode("utf-8", "strict")
        value = json.loads(
            text,
            object_pairs_hook=_strict_json_pairs,
            parse_constant=_reject_json_constant,
        )
    except FreezeError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FreezeError(f"{label} を strict JSON として読めない: {exc}") from exc
    if not isinstance(value, dict):
        raise FreezeError(f"{label} の top-level が object でない")
    _assert_finite_json(value, label=label)
    return value


def _strict_load_jsonl_objects(raw: bytes, label: str) -> list[Dict]:
    """Strictly parse a non-empty JSONL stream of top-level objects."""

    if not raw or not raw.endswith(b"\n"):
        raise FreezeError(f"{label} が non-empty newline-terminated JSONL でない")
    records = []
    for index, line in enumerate(raw.splitlines()):
        if not line:
            raise FreezeError(f"{label}[{index}] が空行")
        records.append(_strict_load_object_bytes(line, f"{label}[{index}]"))
    return records


def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FreezeError(f"canonical JSON に変換できない: {exc}") from exc


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_relative_path(raw, *, label: str) -> str:
    try:
        path = os.fspath(raw)
    except TypeError as exc:
        raise FreezeError(f"{label} が path でない") from exc
    if not isinstance(path, str) or not path:
        raise FreezeError(f"{label} が空でない raw POSIX relative path でない")
    components = path.split("/")
    if (path.startswith("/") or path.endswith("/") or "//" in path or "\\" in path
            or "." in components or ".." in components
            or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in path)):
        raise FreezeError(f"{label} の raw POSIX relative path が非正規: {path!r}")
    return path


def _capture_regular_nofollow(path: Path, *, label: str) -> bytes:
    """symlink/FIFO を辿らず、open 前後で同一の regular file を一度捕捉する。"""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise FreezeError("O_NOFOLLOW が利用できないため安全に capture できない")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0)
    try:
        before = path.lstat()
        fd = os.open(path, flags)
        try:
            after = os.fstat(fd)
            if (not stat.S_ISREG(before.st_mode) or not stat.S_ISREG(after.st_mode)
                    or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)):
                raise FreezeError(f"{label} が同一 regular file でない: {path}")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(fd)
    except FreezeError:
        raise
    except OSError as exc:
        raise FreezeError(f"{label} を nofollow で読めない: {path}: {exc}") from exc


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


def _run_git_bytes(args: Sequence[str], cwd: Path) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=cwd, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raw = getattr(exc, "stderr", b"") or str(exc).encode("utf-8", "replace")
        detail = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
        raise FreezeError(f"git {' '.join(args)} に失敗: {detail.strip()}") from exc
    return completed.stdout


def _blob_at_head(head: str, path: str, root: Path, *, label: str) -> bytes:
    """captured HEAD の path が blob の場合だけ raw bytes を返す。"""
    spec = f"{head}:{path}"
    try:
        kind = _run_git(["cat-file", "-t", spec], root)
        if kind != "blob":
            raise FreezeError(f"{label} が captured HEAD の blob でない: {path}")
        return _run_git_bytes(["cat-file", "blob", spec], root)
    except FreezeError as exc:
        if "captured HEAD の blob" in str(exc):
            raise
        raise FreezeError(f"{label} が captured HEAD の blob として存在しない: {path}") from exc


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


def _derive_required_literal(expressions: Mapping[str, str]) -> Optional[str]:
    """対応する expression 群から、全 match に必要な key 側 literal を導出する。"""
    if not expressions:
        return None

    keys = []
    unsupported = frozenset("\\^$*+?{}[]()")
    for expression in expressions.values():
        if not isinstance(expression, str) or not expression.startswith("(?:") \
                or not expression.endswith(")"):
            return None
        alternatives = expression[3:-1].split("|")
        if not alternatives:
            return None
        for alternative in alternatives:
            if alternative.startswith('"'):
                marker = alternative.find('":')
                if marker <= 1:
                    return None
                key = alternative[1:marker]
                value = alternative[marker + 2:]
                if value.startswith(" "):
                    value = value[1:]
                if len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
                    return None
                value = value[1:-1]
            else:
                if alternative.count("=") != 1:
                    return None
                key, value = alternative.split("=", 1)
            if not key or not value or any(char in unsupported or char in '.|"' for char in key):
                return None
            # 値は regex であり literal 導出には使わない。現行値の dot だけを許し、
            # escape、文字クラス、group、量指定子、lookaround などは slow fallback に倒す。
            if any(char in unsupported or char in '|"' for char in value):
                return None
            keys.append(key)

    if not keys:
        return None
    first = keys[0]
    candidates = {
        first[start:end]
        for start in range(len(first))
        for end in range(start + 1, len(first) + 1)
    }
    common = [candidate for candidate in candidates if all(candidate in key for key in keys[1:])]
    if not common:
        return None
    return min(common, key=lambda candidate: (-len(candidate), candidate))


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


@dataclass(frozen=True)
class _ScanMemo:
    """同一 ``texts`` object の内容が不変な間だけ、
    exact ``str`` expression ごとの hit 集合を再利用する。
    """

    texts: Mapping[str, str]
    hits_by_expression: Dict[str, frozenset[str]] = field(default_factory=dict)
    _mutable_texts_snapshot: Optional[Dict[str, str]] = field(
        init=False, repr=False, compare=False,
    )

    def __post_init__(self) -> None:
        snapshot = (
            None
            if isinstance(self.texts, MappingProxyType)
            else dict(self.texts.items())
        )
        object.__setattr__(self, "_mutable_texts_snapshot", snapshot)


def _scan_one(
    texts: Mapping[str, str], candidate_id: str, expressions: Mapping[str, str],
    *, memo: Optional[_ScanMemo] = None,
) -> Dict:
    """各 expression の軸別 count と、全軸に一致する sorted path を返す。

    memo は同じ texts object に限り、内容が不変な間だけ exact ``str``
    expression の hit 集合を再利用する。
    """
    expression_snapshot = dict(expressions.items())
    compiled = {
        axis: re.compile(expression)
        for axis, expression in expression_snapshot.items()
    }
    required_literal = (
        _derive_required_literal(expression_snapshot)
        if all(type(expression) is str for expression in expression_snapshot.values())
        else None
    )
    axis_literals = (
        {
            axis: _derive_required_literal({axis: expression})
            for axis, expression in expression_snapshot.items()
        }
        if required_literal is not None
        else {axis: None for axis in expression_snapshot}
    )
    memo_hits = None
    if memo is not None and memo.texts is texts:
        if (memo._mutable_texts_snapshot is not None
                and dict(texts.items()) != memo._mutable_texts_snapshot):
            raise FreezeError("_ScanMemo の texts 内容が再利用前に変化した")
        memo_hits = memo.hits_by_expression
    matched_paths = {}
    for axis, expression in expression_snapshot.items():
        hits = (
            memo_hits.get(expression)
            if memo_hits is not None and type(expression) is str
            else None
        )
        if hits is None:
            found = set()
            for rel, text in texts.items():
                if required_literal is not None and required_literal not in text:
                    continue
                axis_literal = axis_literals[axis]
                if axis_literal is not None and axis_literal not in text:
                    continue
                if compiled[axis].search(text):
                    found.add(rel)
            hits = frozenset(found)
            if memo_hits is not None and type(expression) is str:
                memo_hits[expression] = hits
        matched_paths[axis] = hits
    per_axis_counts = {
        axis: len(hits) for axis, hits in matched_paths.items()
    }
    hit_sets = iter(matched_paths.values())
    first_hit_set = next(hit_sets, None)
    conjunction_hits = (
        sorted(first_hit_set.intersection(*hit_sets))
        if first_hit_set is not None
        else sorted(texts)
    )
    hash_input = {
        "candidate_id": candidate_id,
        "expressions": expression_snapshot,
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

    列挙・open・read・decode は全対象 file について維持し、prefilter と call-local
    memo は regex search の係数だけを減らす。
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

    texts = MappingProxyType(texts)
    memo = _ScanMemo(texts)
    holdout_results = {}
    for name, holdout in HOLDOUTS.items():
        ycsb = holdout["ycsb"]
        expressions = _expressions(ycsb[RRATIO_KEY], ycsb[SKEW_KEY], ycsb[RMW_KEY])
        holdout_results[name] = _scan_one(
            texts, holdout["candidate_id"], expressions, memo=memo,
        )

    positive_expressions = _expressions(
        _POSITIVE_RATIO, _FIXED_SKEW, _FIXED_RMW,
    )
    positive = _scan_one(
        texts, "rr50-positive-control", positive_expressions, memo=memo,
    )
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
V2_TOP_LEVEL_KEYS = frozenset(TOP_LEVEL_KEYS) | V2_ADDED_KEYS

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
    """世代別承認を検証しない v1 経路では世代 schema document を拒否する。"""
    if not isinstance(doc, Mapping):
        return
    present = sorted(GENERATION_SCHEMA_FIELDS & set(doc))
    if present:
        raise FreezeError(
            "世代 document は v1 verify_document 経路では発効しない: 世代 schema field "
            f"{present} を検出したが、この v1 経路は世代別承認を検証しない "
            "(fail-closed)"
        )


def _verify_source(doc: Mapping, field: str, root: Path, rel: str) -> None:
    """source を現行 worktree path の bytes hash で照合する。

    v1 単一 filename freeze は常に唯一の発効中 (active) 世代であり、その source は
    worktree の現物と完全一致しなければならない (ドリフト検知)。record と不一致なら
    拒否 (fail-closed)。frozen_at_head 時点の git blob への救済照合は、世代別不変
    filename + supersedes 連鎖 + 承認束縛を伴う v2 の「旧世代」再検証専用であり、v2 側の
    authority は ``s8b_ratified_freeze.load_ratified_freeze`` が持つ。この v1 経路は
    世代別承認を検証しないので世代 schema document を発効させない。唯一の active 世代へ
    blob 救済を適用すると、設計本文・known_axes・
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
) -> Tuple[Mapping[str, object], ...]:
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
    held_checks = []
    if _freeze_hold.HELD:
        for field in ("design_source", "known_axes_freeze", "generator"):
            held_checks.append(_freeze_hold.held_marker(
                f"s8b-holdout.{field}-implementation-bytes",
            ))
        held_checks.append(_freeze_hold.held_marker(
            "s8b-holdout.frozen-head-current-head",
        ))
    else:
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
    return tuple(held_checks)


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
    held_checks = verify_document(doc, root=root, files=files, current_head=current_head)
    return _freeze_hold.result_with_markers(doc, held_checks)


def _read_regular_nofollow(path: Path) -> bytes:
    """symlink を辿らず、open 前後で同じ regular file だけを capture する。"""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        before = path.lstat()
        fd = os.open(path, flags)
        try:
            after = os.fstat(fd)
            if (not stat.S_ISREG(before.st_mode) or not stat.S_ISREG(after.st_mode)
                    or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)):
                raise FreezeError(f"canonical freeze が同一 regular file でない: {path}")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(fd)
    except FreezeError:
        raise
    except OSError as exc:
        raise FreezeError(f"canonical freeze を nofollow で読めない: {path}: {exc}") from exc


def _t080_migration_module():
    """package import と直接 CLI 実行の双方で同じ T-080 module を返す。"""
    return t080_freeze_migration


def verify_cli_with_t080_receipt(path: Path = FREEZE_PATH, *, root: Path = ROOT) -> Dict:
    """CLI verify だけに T-080 移行 receipt の例外を適用する。

    adapter 成功後に canonical 2 artifact を再読して差替え窓を最小化する。ただし
    filesystem を lock しないため、最終再読後から return までの残余 TOCTOU 窓は消せない。
    """
    root = Path(root).absolute()
    path = Path(path)
    candidate = path if path.is_absolute() else root / path
    canonical = root / FREEZE_REL
    migration = _t080_migration_module()

    captured = None
    path_refusal = None
    if candidate != canonical:
        path_refusal = f"T-080 例外対象 path が canonical active path でない: {path}"
    else:
        try:
            captured = _read_regular_nofollow(candidate)
        except FreezeError as exc:
            path_refusal = str(exc)

    try:
        resolution = migration.verify_receipt(root=root)
    except migration.MigrationError as exc:
        detail = f" {exc.detail}" if exc.detail else ""
        raise FreezeError(f"T-080 receipt 検証失敗: [{exc.reason}]{detail}") from exc

    if resolution.state == "never-issued":
        return verify(path, root=root)
    if path_refusal is not None or captured is None:
        raise FreezeError(path_refusal or "T-080 例外対象 bytes を capture できない")
    if resolution.state != "active-valid" or resolution.refusals or resolution.receipt is None:
        refusals = "; ".join(resolution.refusals) or "refusal detail なし"
        raise FreezeError(f"T-080 receipt が有効でない: {resolution.state}: {refusals}")

    try:
        expected_sha256 = resolution.receipt["artifacts"]["holdout"]["raw_sha256"]
    except (KeyError, TypeError) as exc:
        raise FreezeError("T-080 receipt の holdout 固定値が不正") from exc
    captured_sha256 = hashlib.sha256(captured).hexdigest()
    if captured_sha256 != expected_sha256:
        raise FreezeError("T-080 receipt と capture bytes の sha256 が不一致")

    reread = _read_regular_nofollow(candidate)
    if reread != captured:
        raise FreezeError("T-080 receipt 検証前後で freeze bytes が変化")

    try:
        document = json.loads(captured.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FreezeError(f"T-080 holdout capture を JSON として読めない: {exc}") from exc
    known_record = document.get("known_axes_freeze") if isinstance(document, Mapping) else None
    if (not isinstance(known_record, Mapping)
            or known_record.get("path") != migration.KNOWN_AXES_REL
            or known_record.get("sha256") != migration.KNOWN_AXES_RAW_SHA256):
        raise FreezeError("T-080 adapter の known_axes 発火条件が一致しない")

    known_raw = _read_regular_nofollow(root / migration.KNOWN_AXES_REL)
    try:
        adapted = migration.static_gate_adapter(
            resolution=resolution,
            known_raw=known_raw,
            holdout_raw=captured,
            root=root,
        )
    except migration.MigrationError as exc:
        detail = f" {exc.detail}" if exc.detail else ""
        raise FreezeError(f"T-080 adapter 検証失敗: [{exc.reason}]{detail}") from exc
    if adapted.refusals:
        raise FreezeError(f"T-080 adapter refusal: {'; '.join(adapted.refusals)}")
    if adapted.t080_freeze_migration_observation is None:
        raise FreezeError("T-080 adapter observation が空")

    final_holdout = _read_regular_nofollow(candidate)
    if final_holdout != captured:
        raise FreezeError("T-080 adapter 検証中に freeze bytes が変化")
    final_known = _read_regular_nofollow(root / migration.KNOWN_AXES_REL)
    if final_known != known_raw:
        raise FreezeError("T-080 adapter 検証中に known_axes bytes が変化")
    return _freeze_hold.result_with_markers(document, adapted.held_checks)


def _validate_budget(budget: Mapping, *, holdout_ids: Sequence[str], label: str) -> Dict:
    if not isinstance(budget, Mapping) or frozenset(budget) != BUDGET_KEYS:
        raise FreezeError(f"{label} の key 集合が不一致")
    if budget.get("oracle_shared") is not True:
        raise FreezeError(f"{label}.oracle_shared が true でない")
    total = budget.get("total_bench_s")
    if (isinstance(total, bool) or not isinstance(total, (int, float))
            or (isinstance(total, float) and (
                not math.isfinite(total)
                or (total == 0.0 and math.copysign(1.0, total) < 0)
            ))
            or total < 0):
        raise FreezeError(f"{label}.total_bench_s が有限非負数でない")
    per_holdout = budget.get("per_holdout_bench_s")
    if (not isinstance(per_holdout, Mapping)
            or set(per_holdout) != set(holdout_ids)):
        raise FreezeError(f"{label}.per_holdout_bench_s の holdout 集合が不一致")
    for holdout_id, value in per_holdout.items():
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or (isinstance(value, float) and (
                    not math.isfinite(value)
                    or (value == 0.0 and math.copysign(1.0, value) < 0)
                ))
                or value < 0):
            raise FreezeError(
                f"{label}.per_holdout_bench_s.{holdout_id} が有限非負数でない"
            )
    return copy.deepcopy(dict(budget))


def _budget_approval_authority() -> str:
    approval_sha256 = BUDGET_APPROVAL_SHA256
    if approval_sha256 is None:
        raise FreezeError("budget-approval-not-ratified")
    if (not isinstance(approval_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", approval_sha256)):
        raise FreezeError("budget-approval-pin-invalid")
    return approval_sha256


def _load_budget_approval(
    root: Path, *, holdout_ids: Sequence[str], approval_sha256: str,
) -> Tuple[Dict, str]:
    raw = _capture_regular_nofollow(
        root / BUDGET_APPROVAL_REL, label="budget approval",
    )
    actual_sha256 = _sha256_bytes(raw)
    if actual_sha256 != approval_sha256:
        raise FreezeError("budget-approval-sha256-mismatch")
    approval = _strict_load_object_bytes(raw, "budget approval")
    if frozenset(approval) != BUDGET_APPROVAL_KEYS:
        raise FreezeError("budget approval の key 集合が不一致")
    if _canonical_bytes(approval) != raw:
        raise FreezeError("budget approval raw bytes が canonical JSON でない")
    if approval.get("scope") != BUDGET_APPROVAL_SCOPE:
        raise FreezeError("budget approval.scope が固定値と不一致")
    approver = approval.get("approver")
    if not isinstance(approver, str) or not approver.strip():
        raise FreezeError("budget approval.approver が空")
    approved_at = approval.get("approved_at")
    if not isinstance(approved_at, str):
        raise FreezeError("budget approval.approved_at が UTC timestamp でない")
    try:
        parsed = dt.datetime.strptime(approved_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise FreezeError("budget approval.approved_at が UTC timestamp でない") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != approved_at:
        raise FreezeError("budget approval.approved_at が canonical UTC timestamp でない")
    approval["budget"] = _validate_budget(
        approval.get("budget"), holdout_ids=holdout_ids,
        label="budget approval.budget",
    )
    return approval, actual_sha256


def _load_repo_object(root: Path, raw_path, *, label: str) -> Tuple[str, bytes, Dict]:
    rel = _canonical_relative_path(raw_path, label=label)
    raw = _capture_regular_nofollow(root / rel, label=label)
    return rel, raw, _strict_load_object_bytes(raw, label)


def _project_floor_for_freeze(
    result: Mapping, *, expected_holdouts: Optional[Sequence[str]] = None,
) -> Dict:
    """floor result の diagnostics を除いた凍結投影を構築する。"""
    floors = result.get("floors")
    if not isinstance(floors, Mapping):
        raise FreezeError("floor result.floors が object でない")
    holdout_ids = tuple(floors) if expected_holdouts is None else tuple(expected_holdouts)
    if expected_holdouts is not None and set(floors) != set(holdout_ids):
        raise FreezeError("floor result.floors の holdout 集合が不一致")
    projected = {}
    for holdout_id in holdout_ids:
        value = floors.get(holdout_id)
        if (not isinstance(value, Mapping)
                or set(value) != {"pairs", "scale_ref", "scalar_alt", "diagnostics"}):
            raise FreezeError(f"floor result.floors.{holdout_id} の schema が不一致")
        projected[holdout_id] = {
            "pairs": copy.deepcopy(value["pairs"]),
            "scale_ref": copy.deepcopy(value["scale_ref"]),
            "scalar_alt": copy.deepcopy(value["scalar_alt"]),
        }
    return {"by_holdout": projected}


def _validate_floor_inputs(
    *, root: Path, head: str, floor_result_path, v1: Mapping,
) -> Tuple[str, bytes, Dict, bytes, Dict, Dict, Dict]:
    # v1 API の import・実行境界を v2 専用依存の import-time validation や
    # process-wide callback 登録から分離する。
    from . import env_contract
    from . import s8b_floor_contract
    from . import s8b_floor_stats
    from . import s8b_binary_admission
    from ..calibrator import perf_preflight as _perf_preflight
    from .s8b_holdout_admission import FloorHoldoutEvidenceError
    from .build_admission import resolve_current_build_admission_policy
    from .s8b_launch_cert import LaunchCertError, parse_official_run_path

    protocol_raw = _capture_regular_nofollow(
        root / FLOOR_PROTOCOL_REL, label="floor protocol",
    )
    head_protocol_raw = _blob_at_head(
        head, FLOOR_PROTOCOL_REL, root, label="floor protocol",
    )
    if protocol_raw != head_protocol_raw:
        raise FreezeError(
            "floor protocol が captured HEAD と worktree で不一致"
        )
    protocol_document = _strict_load_object_bytes(protocol_raw, "floor protocol")
    try:
        protocol = s8b_floor_contract.validate_protocol(
            protocol_document,
            contract_sha256_lookup=lambda env_tag: env_contract.lookup(
                env_tag,
            ).contract_sha256,
        )
        protocol_sha256 = s8b_floor_contract.canonical_protocol_sha256(protocol)
    except (s8b_floor_contract.FloorContractError, env_contract.EnvContractError) as exc:
        raise FreezeError(f"floor protocol が不正: {exc}") from exc
    protocol_raw_sha256 = _sha256_bytes(protocol_raw)
    if protocol_sha256 != protocol_raw_sha256:
        raise FreezeError("floor protocol raw bytes が canonical protocol と一致しない")
    if protocol.get("freeze") != {
        "path": FREEZE_REL,
        "sha256": t080_freeze_migration.HOLDOUT_RAW_SHA256,
    }:
        raise FreezeError("floor protocol.freeze が固定 v1 freeze と不一致")

    result_rel, result_raw, result = _load_repo_object(
        root, floor_result_path, label="floor result",
    )
    try:
        path_info = parse_official_run_path(result_rel, expected_basename="result.json")
    except LaunchCertError as exc:
        raise FreezeError(f"floor result path が official result でない: {exc}") from exc
    result_perf_preflight = result.get("perf_preflight")
    result_schema = result.get("schema")
    result_key_schema = (
        s8b_floor_contract.RESULT_SCHEMA_V5
        if result_schema == s8b_floor_contract.RESULT_SCHEMA_V5
        else s8b_floor_contract.LEGACY_RESULT_SCHEMA
    )
    try:
        expected_use_perf = _perf_preflight.use_perf_from_receipt(
            result_perf_preflight
        )
        expected_result_keys = s8b_floor_contract.result_keys_for_mode(
            "official", schema=result_key_schema,
            perf_preflight=result_perf_preflight,
        )
    except (_perf_preflight.PerfPreflightError,
            s8b_floor_contract.FloorContractError) as exc:
        raise FreezeError(f"floor result の perf evidence が不正: {exc}") from exc
    if frozenset(result) != expected_result_keys:
        raise FreezeError("floor result の key 集合が不一致")
    if (
        result_schema != s8b_floor_contract.LEGACY_RESULT_SCHEMA
        and result_schema != s8b_floor_contract.RESULT_SCHEMA_V5
    ):
        raise FreezeError(
            f"floor result.schema が {s8b_floor_contract.RESULT_SCHEMA} でない"
        )
    if result.get("mode") != "official":
        raise FreezeError("floor result.mode が official でない")
    if not expected_use_perf:
        try:
            normalized_observation = s8b_floor_stats.validate_floor_perf_evidence(
                result, result.get("perf_observation"), claim="throughput",
            )
        except _perf_preflight.PerfPreflightError as exc:
            raise FreezeError(f"floor result perf_observation が不正: {exc}") from exc
        if normalized_observation["preflight"] != result_perf_preflight:
            raise FreezeError(
                "floor result perf_observation.preflight が perf_preflight と不一致"
            )
    if result.get("freeze_sha256") != t080_freeze_migration.HOLDOUT_RAW_SHA256:
        raise FreezeError("floor result.freeze_sha256 が固定 v1 hash と不一致")
    if result.get("protocol_sha256") != protocol_sha256:
        raise FreezeError("floor result.protocol_sha256 が固定 protocol hash と不一致")
    if (result.get("env_tag") != protocol["env_tag"]
            or path_info["env_tag"] != protocol["env_tag"]):
        raise FreezeError("floor result/protocol/path の env_tag が不一致")
    if path_info["proto8"] != protocol_sha256[:8]:
        raise FreezeError("floor result path の proto8 が protocol hash と不一致")
    header_fields = (
        "formula", "ccbench_pin", "stock_configuration", "wired_min_rel_floor",
        "reps", "n_sessions", "scale_adequacy_rel_tolerance",
    )
    for field in header_fields:
        if (result.get(field) != protocol.get(field)
                or type(result.get(field)) is not type(protocol.get(field))):
            raise FreezeError(f"floor result.{field} が protocol と不一致")

    try:
        cells = s8b_floor_contract.enumerate_cells(
            v1, stock_configuration=protocol["stock_configuration"],
        )
        schedule = s8b_floor_contract.build_schedule(
            cells=cells, master_seed=protocol["master_seed"],
            n_sessions=protocol["n_sessions"],
        )
        expected_cells = s8b_floor_contract.expected_cells_from_cells(cells)
    except s8b_floor_contract.FloorContractError as exc:
        raise FreezeError(
            f"v1 holdout binding から full cells/schedule を導出できない: {exc}"
        ) from exc
    expected_holdouts = sorted(expected_cells)
    expected_configurations = sorted({
        configuration
        for configurations in expected_cells.values()
        for configuration in configurations
    })
    if result.get("holdouts") != expected_holdouts:
        raise FreezeError("floor result.holdouts が v1 holdout 集合と不一致")
    if result.get("configurations") != expected_configurations:
        raise FreezeError("floor result.configurations が v1 configuration 集合と不一致")
    binaries = result.get("binaries")
    if not isinstance(binaries, Mapping):
        raise FreezeError("floor result.binaries が object でない")
    current_admission_policy = resolve_current_build_admission_policy()
    for holdout_id, configurations in expected_cells.items():
        for configuration_id in configurations:
            cell_id = f"{holdout_id}::{configuration_id}"
            rec = binaries.get(cell_id)
            if not isinstance(rec, Mapping):
                raise FreezeError(
                    f"floor result.binaries に admission 付き cell が無い: {cell_id}"
                )
            try:
                entry = v1["holdouts"][holdout_id]["variant_binding"]["entries"][
                    configuration_id
                ]
                entry_sha256 = _sha256_bytes(_canonical_bytes(entry))
                binding_sha256 = rec["binding"]["binding_sha256"]
                s8b_binary_admission.validate_portable_binary_record(
                    rec, expected_policy=current_admission_policy,
                    expected_ccbench_pin=protocol["ccbench_pin"],
                    expected_contract_sha256=protocol["contract_sha256"],
                    expected_cell_id=cell_id,
                    expected_holdout_id=holdout_id,
                    expected_configuration_id=configuration_id,
                    expected_entry_sha256=entry_sha256,
                    expected_binding_sha256=binding_sha256,
                )
            except (KeyError, TypeError, s8b_binary_admission.BinaryAdmissionError) as exc:
                raise FreezeError(
                    f"floor result.binaries admission 束縛が不正: {cell_id}: {exc}"
                ) from exc
    expected_protocol = s8b_floor_contract.project_protocol_for_floor_artifact(protocol)
    expected_protocol["expected_cells"] = expected_cells
    run_dir = result_rel.rsplit("/", 1)[0]
    manifest_rel = f"{run_dir}/manifest.json"
    try:
        manifest_raw = _capture_regular_nofollow(
            root / manifest_rel, label="floor result sibling manifest",
        )
    except FreezeError as exc:
        raise FreezeError(
            f"floor-admission-unverifiable: sibling-manifest-unavailable: {exc}"
        ) from exc
    manifest_sha256 = _sha256_bytes(manifest_raw)
    if result.get("manifest_sha256") != manifest_sha256:
        raise FreezeError(
            "floor-admission-mismatch: result.manifest_sha256 が sibling manifest bytes と不一致"
        )
    manifest_document = _strict_load_object_bytes(
        manifest_raw, "floor result sibling manifest",
    )
    try:
        manifest_run_cmd, manifest_indicators = (
            s8b_floor_contract.manifest_perf_validation_context(manifest_document)
        )
        s8b_floor_contract.validate_manifest_v3(
            manifest_document, protocol=protocol,
            protocol_sha256=protocol_sha256,
            freeze_sha256=t080_freeze_migration.HOLDOUT_RAW_SHA256,
            expected_cells=cells, expected_schedule=schedule, mode="official",
            run_cmd=manifest_run_cmd, leading_indicators=manifest_indicators,
        )
    except s8b_floor_contract.FloorContractError as exc:
        raise FreezeError(
            f"floor-admission-mismatch: sibling-manifest-invalid: {exc}"
        ) from exc
    if result["binaries"] != manifest_document["binaries"]:
        raise FreezeError(
            "floor-admission-mismatch: result.binaries が sibling manifest と不一致"
        )
    if (result.get("perf_preflight") != manifest_document.get("perf_preflight")
            or result.get("perf_observation")
            != manifest_document.get("perf_observation")):
        raise FreezeError(
            "floor-admission-mismatch: result/manifest の perf evidence が不一致"
        )
    journal_rel = f"{run_dir}/journal.jsonl"
    try:
        journal_raw = _capture_regular_nofollow(
            root / journal_rel, label="floor result sibling journal",
        )
        journal_records = _strict_load_jsonl_objects(
            journal_raw, "floor result sibling journal",
        )
    except FreezeError as exc:
        raise FreezeError(
            f"floor-admission-unverifiable: sibling-journal-unavailable: {exc}"
        ) from exc
    journal_sessions = [
        record for record in journal_records if record.get("event") == "session"
    ]
    result_sessions = result["sessions"]
    if type(result_sessions) is not list or journal_sessions != result_sessions:
        raise FreezeError(
            "floor-admission-mismatch: journal sessions と result.sessions が不一致"
        )
    attempt_lifecycle = [
        record for record in journal_records
        if record.get("event") in {"session-start", "session"}
    ]
    expected_binaries: dict[str, str] = {}
    for record in journal_sessions:
        try:
            cell_id = record["cell_id"]
            measured_sha256 = record["binary_sha256_at_measure"]
        except KeyError as exc:
            raise FreezeError(
                "floor-admission-mismatch: journal binary receipt が欠落"
            ) from exc
        if (
            type(cell_id) is not str or not cell_id
            or type(measured_sha256) is not str
            or len(measured_sha256) != 64
            or any(character not in "0123456789abcdef" for character in measured_sha256)
        ):
            raise FreezeError(
                "floor-admission-mismatch: journal binary receipt が不正"
            )
        previous = expected_binaries.setdefault(cell_id, measured_sha256)
        if previous != measured_sha256:
            raise FreezeError(
                "floor-admission-mismatch: journal binary receipt が cell 内で不一致"
            )
    try:
        problems = s8b_floor_stats.verify_floor_artifact_with_live_admission(
            result, expected_protocol, expected_binaries=expected_binaries,
            repo_root=root, protocol=protocol,
            verified_freeze_document=v1,
            freeze_sha256=t080_freeze_migration.HOLDOUT_RAW_SHA256,
            manifest_sha256=manifest_sha256,
            campaign_run_id=path_info["run_id"],
            run_relpath=run_dir.removeprefix("output/"), mode="official",
            cells=cells, schedule=schedule, sessions=attempt_lifecycle,
            expected_use_perf=expected_use_perf,
        )
    except FloorHoldoutEvidenceError as exc:
        prefix = (
            "floor-admission-unverifiable"
            if exc.category == "unverifiable"
            else "floor-admission-mismatch"
        )
        raise FreezeError(f"{prefix}: {exc.reason}") from exc
    if problems:
        if any("holdout_admission" in problem for problem in problems):
            raise FreezeError(f"floor-admission-mismatch: {problems[0]}")
        raise FreezeError(f"floor result の統計検証に失敗: {'; '.join(problems)}")
    if result.get("eligible_for_refreeze") is not True:
        raise FreezeError("floor result.eligible_for_refreeze が true でない")

    floor = _project_floor_for_freeze(
        result, expected_holdouts=expected_holdouts,
    )
    return (
        result_rel, result_raw, result, protocol_raw, protocol,
        floor, path_info,
    )


def _validate_selected_floor_launch_certificate(
    *, namespace_fd: int, result_rel: str, protocol: Mapping, path_info: Mapping,
) -> None:
    """selected result の certificate と official path の起動秒を束縛する。"""
    from . import s8b_floor_contract
    from .s8b_launch_cert import LaunchCertError, validate_launch_certificate

    run_name = result_rel.rsplit("/", 2)[-2]
    run_fd = None
    try:
        run_fd = _open_nofollow_child_directory(
            namespace_fd, run_name, label="floor result selected run",
        )
        cert_raw = _capture_regular_nofollow_at(
            run_fd, "launch_certificate.json",
            label="floor result launch certificate",
        )
        if cert_raw is None:
            raise FreezeError("floor result launch certificate が存在しない")
        cert = _strict_load_object_bytes(cert_raw, "floor result launch certificate")
        validate_launch_certificate(
            cert,
            expected_v1_freeze_sha256=t080_freeze_migration.HOLDOUT_RAW_SHA256,
            expected_protocol_sha256=(
                s8b_floor_contract.canonical_protocol_sha256(protocol)
            ),
            expected_run_id=path_info["run_id"],
        )
    except (FreezeError, LaunchCertError, KeyError, TypeError) as exc:
        raise FreezeError(f"floor-launch-certificate-invalid: {exc}") from exc
    finally:
        if run_fd is not None:
            os.close(run_fd)


def _open_nofollow_directory_chain(
    root: Path, rel: str, *, label: str,
) -> int:
    """root から rel までを dirfd で辿り、束縛済み leaf directory fd を返す。"""
    rel = _canonical_relative_path(rel, label=label)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise FreezeError(
            "O_NOFOLLOW/O_DIRECTORY が利用できないため安全に directory を開けない"
        )
    flags = os.O_RDONLY | nofollow | directory
    current_fd = None
    try:
        root_before = root.lstat()
        current_fd = os.open(root, flags)
        root_after = os.fstat(current_fd)
        if (
            not stat.S_ISDIR(root_before.st_mode)
            or not stat.S_ISDIR(root_after.st_mode)
            or (root_before.st_dev, root_before.st_ino)
            != (root_after.st_dev, root_after.st_ino)
        ):
            raise FreezeError(f"{label} repo root が同一 non-symlink directory でない")
        for component in rel.split("/"):
            next_fd = os.open(component, flags, dir_fd=current_fd)
            next_stat = os.fstat(next_fd)
            if not stat.S_ISDIR(next_stat.st_mode):
                os.close(next_fd)
                raise FreezeError(
                    f"{label} component が non-symlink directory でない: {component}"
                )
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except FreezeError:
        if current_fd is not None:
            os.close(current_fd)
        raise
    except OSError as exc:
        if current_fd is not None:
            os.close(current_fd)
        raise FreezeError(
            f"{label} non-symlink directory chain を開けない: {exc}"
        ) from exc


def _open_nofollow_child_directory(
    parent_fd: int, component: str, *, label: str,
) -> int:
    """束縛済み parent fd から同一 inode の child directory を開く。"""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise FreezeError(
            "O_NOFOLLOW/O_DIRECTORY が利用できないため安全に directory を開けない"
        )
    flags = os.O_RDONLY | nofollow | directory
    child_fd = None
    try:
        before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
        child_fd = os.open(component, flags, dir_fd=parent_fd)
        after = os.fstat(child_fd)
        if (
            not stat.S_ISDIR(before.st_mode)
            or not stat.S_ISDIR(after.st_mode)
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        ):
            raise FreezeError(
                f"{label} が同一 non-symlink directory でない: {component}"
            )
        return child_fd
    except FreezeError:
        if child_fd is not None:
            os.close(child_fd)
        raise
    except OSError as exc:
        if child_fd is not None:
            os.close(child_fd)
        raise FreezeError(
            f"{label} が non-symlink directory でない: {component}: {exc}"
        ) from exc


def _capture_regular_nofollow_at(
    parent_fd: int, leaf: str, *, label: str, missing_ok: bool = False,
) -> Optional[bytes]:
    """束縛済み directory fd から同一 regular leaf を nofollow で捕捉する。"""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise FreezeError("O_NOFOLLOW が利用できないため安全に capture できない")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0)
    fd = None
    try:
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        fd = os.open(leaf, flags, dir_fd=parent_fd)
        after = os.fstat(fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or not stat.S_ISREG(after.st_mode)
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        ):
            raise FreezeError(f"{label} が同一 non-symlink regular file でない")
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise FreezeError(f"{label} が存在しない")
    except FreezeError:
        raise
    except OSError as exc:
        raise FreezeError(
            f"{label} が同じ dirfd 上の non-symlink regular file でない: {exc}"
        ) from exc
    finally:
        if fd is not None:
            os.close(fd)


def _official_earlier_floor_results(
    *, root: Path, selected_rel: str, selected_path_info: Mapping,
    protocol: Mapping, v1: Mapping, namespace_fd: int, namespace_rel: str,
) -> Tuple[Tuple[str, Dict, bool], ...]:
    """束縛済み namespace fd から earlier result と適格性を捕捉する。"""
    from .s8b_launch_cert import LaunchCertError, parse_official_run_path

    try:
        entries = tuple(os.listdir(namespace_fd))
    except OSError as exc:
        raise FreezeError(f"floor selection namespace を列挙できない: {exc}") from exc

    earlier = []
    for entry_name in entries:
        candidate_rel = f"{namespace_rel}/{entry_name}/result.json"
        try:
            path_info = parse_official_run_path(
                candidate_rel, expected_basename="result.json",
            )
        except LaunchCertError:
            continue
        if (path_info["env_tag"] != selected_path_info["env_tag"]
                or path_info["proto8"] != selected_path_info["proto8"]
                or path_info["ts"] >= selected_path_info["ts"]):
            continue
        run_fd = _open_nofollow_child_directory(
            namespace_fd, entry_name, label="floor selection earlier run",
        )
        try:
            result_before = _capture_regular_nofollow_at(
                run_fd, "result.json", label="floor selection earlier result",
                missing_ok=True,
            )
            if result_before is None:
                continue
            try:
                derived = _derive_floor_selection_eligibility(
                    root=root, run_fd=run_fd, result_rel=candidate_rel,
                    result_before=result_before, path_info=path_info,
                    protocol=protocol, v1=v1,
                )
            except FreezeError as exc:
                raise FreezeError(
                    "floor-selection-eligibility-underivable: "
                    f"{candidate_rel}: {exc}"
                ) from exc
            earlier.append((candidate_rel, path_info, derived))
        finally:
            os.close(run_fd)
    return tuple(sorted(earlier, key=lambda item: item[1]["run_id"]))


def _derive_floor_selection_eligibility(
    *, root: Path, run_fd: int, result_rel: str, result_before: bytes,
    path_info: Mapping, protocol: Mapping, v1: Mapping,
) -> bool:
    """earlier run の適格性を共有 admission 台帳だけから再導出する。"""
    from . import s8b_floor_contract
    from .s8b_holdout_admission import (
        FloorHoldoutEvidenceError,
        FloorHoldoutEvidenceInspection,
        inspect_floor_holdout_admission_evidence,
    )

    run_dir = result_rel.rsplit("/", 1)[0]
    manifest_before = _capture_regular_nofollow_at(
        run_fd, "manifest.json", label="floor selection earlier manifest",
    )
    journal_before = _capture_regular_nofollow_at(
        run_fd, "journal.jsonl", label="floor selection earlier journal",
    )
    if manifest_before is None or journal_before is None:
        raise FreezeError("earlier manifest/journal が存在しない")
    journal_records = _strict_load_jsonl_objects(
        journal_before, "floor selection earlier journal",
    )
    attempt_lifecycle = [
        record for record in journal_records
        if record.get("event") in {"session-start", "session"}
    ]
    try:
        cells = s8b_floor_contract.enumerate_cells(
            v1, stock_configuration=protocol["stock_configuration"],
        )
        schedule = s8b_floor_contract.build_schedule(
            cells=cells, master_seed=protocol["master_seed"],
            n_sessions=protocol["n_sessions"],
        )
        inspection = inspect_floor_holdout_admission_evidence(
            repo_root=root, protocol=protocol,
            verified_freeze_document=v1,
            freeze_sha256=t080_freeze_migration.HOLDOUT_RAW_SHA256,
            manifest_sha256=_sha256_bytes(manifest_before),
            campaign_run_id=path_info["run_id"],
            run_relpath=run_dir.removeprefix("output/"), mode="official",
            cells=cells, schedule=schedule, sessions=attempt_lifecycle,
        )
    except (KeyError, TypeError, ValueError, s8b_floor_contract.FloorContractError,
            FloorHoldoutEvidenceError) as exc:
        raise FreezeError(str(exc)) from exc
    if not isinstance(inspection, FloorHoldoutEvidenceInspection):
        raise FreezeError("admission inspector の戻り値が契約外")
    for leaf, before, label in (
        ("result.json", result_before, "result"),
        ("manifest.json", manifest_before, "manifest"),
        ("journal.jsonl", journal_before, "journal"),
    ):
        after = _capture_regular_nofollow_at(
            run_fd, leaf, label=f"floor selection earlier {label} recapture",
        )
        if after != before:
            raise FreezeError(f"earlier {label} が適格性導出中に変化")
    return inspection.derived_eligible_for_refreeze


def _assert_floor_selection_identity(
    *, root: Path, selected_rel: str, selected_path_info: Mapping,
    protocol: Mapping, v1: Mapping, validate_selected_certificate: bool = False,
) -> None:
    """selected が earliest derived-eligible official run であることを要求する。"""
    namespace_rel = (
        f"output/env/{selected_path_info['env_tag']}/calibration/"
        "s8b-floor-official"
    )
    if not selected_rel.startswith(f"{namespace_rel}/"):
        raise FreezeError("floor selection selected path が namespace と不一致")
    namespace_fd = _open_nofollow_directory_chain(
        root, namespace_rel, label="floor selection namespace",
    )
    try:
        if validate_selected_certificate:
            _validate_selected_floor_launch_certificate(
                namespace_fd=namespace_fd, result_rel=selected_rel,
                protocol=protocol, path_info=selected_path_info,
            )
        eligible = [(selected_path_info["run_id"], selected_rel)]
        for earlier_rel, earlier_info, derived in _official_earlier_floor_results(
                root=root, selected_rel=selected_rel,
                selected_path_info=selected_path_info, protocol=protocol, v1=v1,
                namespace_fd=namespace_fd, namespace_rel=namespace_rel):
            if derived:
                eligible.append((earlier_info["run_id"], earlier_rel))
    finally:
        os.close(namespace_fd)
    required_run_id, _required_rel = min(eligible, key=lambda item: item[0])
    selected_run_id = selected_path_info["run_id"]
    if required_run_id != selected_run_id:
        raise FreezeError(
            f"floor-selection-rule-mismatch: {_FLOOR_SELECTION_RULE_VERSION}: "
            f"selected_run_id={selected_run_id} required_run_id={required_run_id}"
        )


def _measurement_closure(
    *, root: Path, head: str, floor_result_rel: str,
) -> list[Dict[str, str]]:
    report = search_repository(root)
    hits = set()
    for holdout_id in HOLDOUTS:
        result = report.get("holdouts", {}).get(holdout_id)
        paths = result.get("conjunction_hits") if isinstance(result, Mapping) else None
        if not isinstance(paths, list):
            raise FreezeError(f"closure scan の {holdout_id}.conjunction_hits が list でない")
        hits.update(paths)
    run_dir = floor_result_rel.rsplit("/", 1)[0]
    dedicated = {
        FLOOR_PROTOCOL_REL,
        V2_CANDIDATE_REL,
        floor_result_rel,
        f"{run_dir}/manifest.json",
        f"{run_dir}/journal.jsonl",
        f"{run_dir}/launch_certificate.json",
    }
    closure = []
    for raw_path in sorted(hits - dedicated):
        rel = _canonical_relative_path(raw_path, label="measurement_closure path")
        head_raw = _blob_at_head(head, rel, root, label="measurement_closure path")
        worktree_raw = _capture_regular_nofollow(
            root / rel, label=f"measurement_closure:{rel}",
        )
        if worktree_raw != head_raw:
            raise FreezeError(
                f"measurement_closure path が captured HEAD と worktree で不一致: {rel}"
            )
        closure.append({"canonical_path": rel, "sha256": _sha256_bytes(head_raw)})
    return closure


def _v1_source_record_at_head(
    v1: Mapping, field: str, *, head: str, root: Path, fixed_path: Optional[str] = None,
) -> Dict[str, str]:
    record = v1.get(field)
    if not isinstance(record, Mapping) or set(record) != {"path", "sha256"}:
        raise FreezeError(f"v1 {field} schema が不正")
    rel = _canonical_relative_path(record.get("path"), label=f"v1 {field}.path")
    if fixed_path is not None and rel != fixed_path:
        raise FreezeError(f"v1 {field}.path が固定 path と不一致")
    raw = _blob_at_head(head, rel, root, label=f"v1 {field}")
    return {"path": rel, "sha256": _sha256_bytes(raw)}


def build_v2_g1_candidate(
    *, floor_result_path, budget_path, root: Path = ROOT,
) -> Dict:
    """固定 v1・official floor・承認 budget から未発効 g1 candidate を構築する。"""
    approval_pin = _budget_approval_authority()
    root = Path(root).absolute()
    head = _run_git(["rev-parse", "HEAD"], root)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise FreezeError("captured HEAD が 40 桁 git SHA でない")

    v1_raw = _capture_regular_nofollow(root / FREEZE_REL, label="canonical v1 freeze")
    v1_sha256 = _sha256_bytes(v1_raw)
    if v1_sha256 != t080_freeze_migration.HOLDOUT_RAW_SHA256:
        raise FreezeError("canonical v1 freeze が T-080 固定 hash と不一致")
    v1 = _strict_load_object_bytes(v1_raw, "canonical v1 freeze")
    if set(v1) != TOP_LEVEL_KEYS:
        raise FreezeError("canonical v1 freeze の top-level schema が不一致")
    holdouts = v1.get("holdouts")
    if not isinstance(holdouts, Mapping) or set(holdouts) != set(HOLDOUTS):
        raise FreezeError("canonical v1 freeze の holdout 集合が不一致")

    approval, approval_sha256 = _load_budget_approval(
        root, holdout_ids=sorted(holdouts), approval_sha256=approval_pin,
    )
    _budget_rel, _budget_raw, budget_document = _load_repo_object(
        root, budget_path, label="budget",
    )
    budget = _validate_budget(
        budget_document, holdout_ids=sorted(holdouts), label="budget",
    )
    if _canonical_bytes(approval["budget"]) != _canonical_bytes(budget):
        raise FreezeError("budget-approval-budget-canonical-mismatch")

    (
        result_rel, result_raw, _result, protocol_raw, protocol, floor,
        path_info,
    ) = _validate_floor_inputs(
        root=root, head=head, floor_result_path=floor_result_path, v1=v1,
    )
    _assert_floor_selection_identity(
        root=root, selected_rel=result_rel, selected_path_info=path_info,
        protocol=protocol, v1=v1, validate_selected_certificate=True,
    )
    known_axes = _v1_source_record_at_head(
        v1, "known_axes_freeze", head=head, root=root,
    )
    if known_axes != v1["known_axes_freeze"]:
        raise FreezeError("v1 known_axes_freeze が captured HEAD blob と不一致")
    generator = _v1_source_record_at_head(
        v1, "generator", head=head, root=root, fixed_path=SCRIPT_REL,
    )
    design_source = _v1_source_record_at_head(
        v1, "design_source", head=head, root=root,
    )
    closure = _measurement_closure(
        root=root, head=head, floor_result_rel=result_rel,
    )

    document = copy.deepcopy(v1)
    document.update({
        "schema_version": V2_SCHEMA_VERSION,
        "frozen_at_head": head,
        "design_source": design_source,
        "generator": generator,
        "floor": floor,
        "budget": budget,
        "refreeze_note": (
            f"{V2_REFREEZE_NOTE_PREFIX}: {BUDGET_APPROVAL_REL} "
            f"sha256={approval_sha256}"
        ),
        "generation_number": 1,
        "supersedes_sha256": v1_sha256,
        "env_tag": protocol["env_tag"],
        "floor_protocol": {
            "path": FLOOR_PROTOCOL_REL,
            "sha256": _sha256_bytes(protocol_raw),
        },
        "floor_source": {
            "path": result_rel,
            "sha256": _sha256_bytes(result_raw),
        },
        "measurement_closure": closure,
    })
    if frozenset(document) != V2_TOP_LEVEL_KEYS:
        raise FreezeError("v2 g1 candidate の top-level schema が不一致")
    return document


def _validate_v2_candidate_output(root: Path, output) -> str:
    rel = _canonical_relative_path(output, label="v2 candidate output")
    if rel != V2_CANDIDATE_REL:
        raise FreezeError("v2 candidate output が固定 candidate path と不一致")
    try:
        root_stat = Path(root).lstat()
    except OSError as exc:
        raise FreezeError(f"repo root を検査できない: {root}: {exc}") from exc
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
        raise FreezeError("repo root が既存 non-symlink directory でない")
    return rel


def _write_v2_candidate_create_only(root: Path, output, raw: bytes) -> None:
    """root dirfd から no-follow で辿り、固定 leaf を create-only で書く。"""
    root = Path(root).absolute()
    rel = _validate_v2_candidate_output(root, output)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise FreezeError("O_NOFOLLOW/O_DIRECTORY が利用できないため安全に生成できない")
    directory_flags = os.O_RDONLY | directory | nofollow
    descriptors = []
    created = False
    parent_fd = None
    leaf = rel.split("/")[-1]
    try:
        root_before = root.lstat()
        root_fd = os.open(root, directory_flags)
        descriptors.append(root_fd)
        root_after = os.fstat(root_fd)
        if ((root_before.st_dev, root_before.st_ino)
                != (root_after.st_dev, root_after.st_ino)
                or not stat.S_ISDIR(root_after.st_mode)):
            raise FreezeError("repo root が検査時と同一 directory でない")
        parent_fd = root_fd
        for component in rel.split("/")[:-1]:
            try:
                next_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(component, 0o700, dir_fd=parent_fd)
                except FileExistsError:
                    # 同時作成された entry も下の nofollow open で再検証する。
                    pass
                next_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            descriptors.append(next_fd)
            parent_fd = next_fd
        flags = (
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | nofollow
        )
        leaf_fd = os.open(leaf, flags, 0o600, dir_fd=parent_fd)
        created = True
        try:
            if not stat.S_ISREG(os.fstat(leaf_fd).st_mode):
                raise FreezeError("v2 candidate leaf が regular file でない")
            offset = 0
            while offset < len(raw):
                written = os.write(leaf_fd, raw[offset:])
                if written <= 0:
                    raise FreezeError("v2 candidate write が進行しない")
                offset += written
            os.fsync(leaf_fd)
        finally:
            os.close(leaf_fd)
    except FreezeError:
        if created and parent_fd is not None:
            try:
                os.unlink(leaf, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    except OSError as exc:
        if created and parent_fd is not None:
            try:
                os.unlink(leaf, dir_fd=parent_fd)
            except OSError:
                pass
        raise FreezeError(f"v2 candidate を安全に新規作成できない: {rel}: {exc}") from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def generate_v2_g1_candidate(
    *, floor_result_path, budget_path, output_path=V2_CANDIDATE_REL,
    root: Path = ROOT,
) -> Dict:
    """全入力を検証・canonical 化した後、g1 candidate を最後に一度だけ作る。"""
    _validate_v2_candidate_output(root, output_path)
    document = build_v2_g1_candidate(
        floor_result_path=floor_result_path,
        budget_path=budget_path,
        root=root,
    )
    _write_v2_candidate_create_only(root, output_path, _canonical_bytes(document))
    return document


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8b holdout freeze の検索・生成・照合")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("search", help="書き込みなしで未知性検索を実行する")

    generate_parser = subparsers.add_parser("generate", help="検索合格後に freeze を生成する")
    generate_parser.add_argument("--confirmed-by", required=True)
    generate_parser.add_argument("--confirmed-at", required=True)
    generate_parser.add_argument("--output", type=Path, default=FREEZE_PATH)

    v2_parser = subparsers.add_parser(
        "generate-v2-candidate", help="承認済み budget と official floor から g1 candidate を生成する",
    )
    v2_parser.add_argument("--floor-result", required=True)
    v2_parser.add_argument("--budget", required=True)
    v2_parser.add_argument("--output", default=V2_CANDIDATE_REL)

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
        elif args.command == "verify":
            result = verify_cli_with_t080_receipt(args.path)
            if result.held_checks:
                print(json.dumps({
                    "status": "held", "path": str(args.path),
                    "held_checks": result.held_checks,
                }, ensure_ascii=False, sort_keys=True))
            else:
                print(f"verified: {args.path}")
        else:
            generate_v2_g1_candidate(
                floor_result_path=args.floor_result,
                budget_path=args.budget,
                output_path=args.output,
            )
            print(f"generated-v2-candidate: {args.output}")
    except FreezeError as exc:
        print(f"fails-closed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
