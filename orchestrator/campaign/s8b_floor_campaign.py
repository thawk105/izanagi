# -*- coding: utf-8 -*-
"""8b floor campaign driver — holdout freeze から floor 案を実測する env-neutral driver。

役割 (凍結案パッケージ wave 2 = output/insights/2026-07-16_s8b-floor-protocol-package.md と
同期): holdout freeze v1 の 2 holdout × 6 構成 = 12 セルを floor protocol (明示入力・未凍結数値の
デフォルト内蔵禁止) が定める schedule どおり直列・単一テナントで計測し、``s8b_floor_stats``
(formula v1) で floor 案を算出して artifact (result.json/md) に書く。**freeze への floor 書込み・
phase 文書の編集はしない** (§8 手続き: 発効はユーザー承認事項)。本 driver は「案」を出すだけで、
何も発効させない。

系譜: 計測は calibration driver (``between_run_floor.py``) と同型で ``measure_point`` を直接
呼ぶ (``pipeline.evaluate`` は使わない — floor は correctness gate を通す本走ではなく noise
の実測)。build 経路だけ oracle と揃える (共有 ``s8b_materialization.prepared_binding`` +
``buildcache.build(trace=False)``) ので、floor を測るバイナリと oracle 本走のバイナリが同一
identity になる。

**式は本 driver の外 (``s8b_floor_stats``, formula v1) が正本。** driver は計測して SessionRecord
を作り、cell_stats / holdout_floors / verify_floor_artifact を呼ぶだけで、floor の式を自前で持たない
(規律5: 単一目的の分離)。session 有効性契約も ``s8b_floor_stats.session_median`` の逐語定義に従う。

絶対規律の適用:
- 規律1 (観測者効果): 計測は trace-disabled build (``trace=False``)。buildcache の nm ガードが
  trace シンボル混入を fails-closed に検査する
- 規律4 (単一テナント直列): session ごとの臨界区間 (probe → measure → post-probe → journal) で
  自前の strict probe (pgrep) を計測の前後に叩く。**rc=1 のみ「競合なし」**、rc=0 の競合列挙は
  当該 session を無効 (``competing_process``, retry 可) にし、実行不能・rc>1・parse 不能は
  **CampaignAbort** で倒す (共有 ``competing_bench_pids`` も B-1 以降 fail-closed だが、floor は
  kind 付き CampaignAbort・生出力 journal・competing_process retry を要するため自前 strict probe を維持する)
- 規律6 (信頼境界): freeze は素性の知れない外部内容。bytes-hash pin で束縛し、以後この単一
  parse 結果だけを使う (再読込禁止)

fail-closed の原則: 縮退・欠測・不正入力・競合はすべて null / 拒否 / 判定不能へ倒す。fallback や
黙認は書かない。protocol config の数値はコードに既定値を持たず入力必須にする。CLI に env・経路・
数値の上書き面は作らない (``--marker-root`` 撤去の教訓、worklog 2026-07-16 (12))。

**なぜ ``s8b_holdout_freeze.verify_document`` を呼ばないか:** v1 freeze は design/generator の
worktree drift (design 1829af→bce6ef, generator 1910ff→2356fd) で現在 **意味検証に不合格**で
あり、意味再検証は freeze v2 machinery (strict v2 verifier) の責務。本 driver は freeze を
**bytes-hash pin** で束縛し (protocol.freeze.sha256 との byte 一致)、構造だけを最小検査して
floor 実測に使う。意味検証を通せない v1 でも floor を測れるのは、floor が「対象点の noise の
物理量」であって freeze の意味論に依存しないため。

official mode は承認束縛方式が §8 未裁定のため現時点で常に拒否する (fail-closed 既定)。pilot の
artifact には ``eligible_for_refreeze: false`` を焼き込む。
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Mapping, Optional

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from calibrator.runner import (  # noqa: E402
    _self_and_descendant_pids,
    measure_point,
)
from campaign import buildcache, s8b_floor_stats  # noqa: E402
from campaign.layout import env_scope_dir, repo_output_root  # noqa: E402
from campaign.p2_2 import CLK, ENV_TAG  # noqa: E402
from campaign.s1_direct_comparison import prepare_cell  # noqa: E402
from campaign.s8b_materialization import (  # noqa: E402
    MaterializationError,
    prepared_binding,
)
from campaign.s8b_oracle_driver import (  # noqa: E402
    NUMACTL,
    VerifiedFreeze,
    load_verified_freeze,
)

PROTOCOL_SCHEMA = "s8b-floor-protocol/v1"
FREEZE_SCHEMA = "8b-holdout-freeze/v1"
SCHEDULE_ALGORITHM = "balanced-permutation/v1"
RESULT_SCHEMA = "s8b-floor-result/v1"
MANIFEST_SCHEMA = "s8b-floor-manifest/v1"

# protocol JSON の必須 key (strict: これ以外の key・欠落・型不正・duplicate key はすべて拒否)。
_PROTOCOL_KEYS = frozenset({
    "schema", "formula", "env_tag", "ccbench_pin", "freeze", "stock_configuration",
    "n_sessions", "reps", "blocks", "replicates_per_block", "min_block_gap_s",
    "master_seed", "schedule_algorithm", "extime_s", "wired_min_rel_floor",
    "retry_slots_per_cell", "allowed_excluded_reasons",
})
_FREEZE_RECORD_KEYS = frozenset({"path", "sha256"})

# 無効 session の閉じた excluded_reason コード (パッケージ 裁定 F2 の閉じた表)。driver が観測から
# 分類するコードはこの集合に限る。protocol.allowed_excluded_reasons が使用コードを含まなければ
# CampaignAbort (未登録の縮退, fail-closed)。correctness 系コードは floor に存在しない (F2)。
_REASON_COMPETING = "competing_process"          # preflight/post probe の競合
_REASON_LAUNCH = "launch_failure"                # プロセス起動失敗 (全 rep 実行不能)
_REASON_PARTIAL = "nonfinite_or_partial_output"  # bench の非有限/部分 rep 出力


class FloorCampaignError(RuntimeError):
    """floor campaign の入力・identity・実行契約を検証できない場合の fail-closed 拒否。"""


class CampaignAbort(FloorCampaignError):
    """臨界区間 (probe 実行不能・rc>1・parse 不能等) の破れで campaign を安全側に中断する (規律4)。"""


# --------------------------------------------------------------------------- #
# canonical JSON / hash                                                        #
# --------------------------------------------------------------------------- #

def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FloorCampaignError(f"canonical JSON に変換できない: {exc}") from exc


def _canonical_sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _full_sha256(path: Path) -> str:
    """バイナリ内容の **full** sha256 (provenance snapshot; truncate しない)。

    hash 計算本体は ``buildcache.full_sha256`` に一元化し (二重実装 drift の解消, D-8)、
    ここは薄い adapter として ``OSError``/``BinaryDigestError`` を ``FloorCampaignError`` に
    変換するだけ (CLI JSON の構造化失敗契約を保つ)。"""
    try:
        return buildcache.full_sha256(path)
    except (OSError, buildcache.BinaryDigestError) as exc:
        raise FloorCampaignError(f"バイナリ sha256 を計算できない: {path}: {exc}") from exc


# --------------------------------------------------------------------------- #
# protocol (strict 明示入力・デフォルト内蔵禁止)                                #
# --------------------------------------------------------------------------- #

def _reject_json_constant(token: str):
    raise FloorCampaignError(f"protocol JSON に非数値定数が含まれる: {token}")


def _no_duplicate_pairs(pairs):
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise FloorCampaignError(f"protocol JSON に duplicate key: {key}")
        result[key] = value
    return result


def load_protocol(path) -> dict:
    """protocol JSON を strict parse する (duplicate key・非数値定数を拒否)。"""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FloorCampaignError(f"protocol を読めない: {path}: {exc}") from exc
    try:
        document = json.loads(
            text, object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise FloorCampaignError(f"protocol を strict parse できない: {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise FloorCampaignError(f"protocol top-level が object でない: {path}")
    return document


def _pos_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FloorCampaignError(f"protocol.{field} が正整数でない")
    return value


def _non_neg_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FloorCampaignError(f"protocol.{field} が非負整数でない")
    return value


def _non_neg_number(value, *, field: str) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value)) or float(value) < 0):
        raise FloorCampaignError(f"protocol.{field} が有限の非負数でない")
    return float(value)


def _non_empty_str(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FloorCampaignError(f"protocol.{field} が空でない文字列でない")
    return value


def validate_protocol(document: Mapping) -> dict:
    """protocol の必須 key・型・整合を strict に検査し、正規化 dict を返す (fail-closed)。

    未知 key・欠落・型不正はすべて拒否する。数値の既定値はコードに持たない (入力必須)。
    ``formula`` の ``s8b_floor_stats.FORMULA_ID`` 一致検査もここで行う (式の版束縛)。
    """
    if not isinstance(document, Mapping):
        raise FloorCampaignError("protocol が object でない")
    keys = set(document)
    if keys != set(_PROTOCOL_KEYS):
        missing = sorted(set(_PROTOCOL_KEYS) - keys)
        unknown = sorted(keys - set(_PROTOCOL_KEYS))
        raise FloorCampaignError(
            f"protocol の key 集合が不一致 (欠落={missing} 未知={unknown})"
        )

    if document["schema"] != PROTOCOL_SCHEMA:
        raise FloorCampaignError(f"protocol.schema が {PROTOCOL_SCHEMA} でない")
    if document["schedule_algorithm"] != SCHEDULE_ALGORITHM:
        raise FloorCampaignError(
            f"protocol.schedule_algorithm が {SCHEDULE_ALGORITHM} でない"
        )

    formula = _non_empty_str(document["formula"], field="formula")
    if formula != s8b_floor_stats.FORMULA_ID:
        raise FloorCampaignError(
            f"protocol.formula ({formula}) が s8b_floor_stats.FORMULA_ID "
            f"({s8b_floor_stats.FORMULA_ID}) と不一致"
        )

    env_tag = _non_empty_str(document["env_tag"], field="env_tag")
    ccbench_pin = _non_empty_str(document["ccbench_pin"], field="ccbench_pin")
    stock_configuration = _non_empty_str(
        document["stock_configuration"], field="stock_configuration",
    )
    master_seed = _non_empty_str(document["master_seed"], field="master_seed")

    freeze_record = document["freeze"]
    if not isinstance(freeze_record, Mapping) or set(freeze_record) != set(_FREEZE_RECORD_KEYS):
        raise FloorCampaignError("protocol.freeze schema が {path, sha256} でない")
    freeze_path = _non_empty_str(freeze_record["path"], field="freeze.path")
    freeze_sha = freeze_record["sha256"]
    if (not isinstance(freeze_sha, str) or len(freeze_sha) != 64
            or any(ch not in "0123456789abcdef" for ch in freeze_sha)):
        raise FloorCampaignError("protocol.freeze.sha256 が SHA-256 でない")

    n_sessions = _pos_int(document["n_sessions"], field="n_sessions")
    reps = _pos_int(document["reps"], field="reps")
    blocks = _pos_int(document["blocks"], field="blocks")
    replicates_per_block = _pos_int(
        document["replicates_per_block"], field="replicates_per_block",
    )
    if blocks * replicates_per_block != n_sessions:
        raise FloorCampaignError(
            f"blocks × replicates_per_block ({blocks}×{replicates_per_block}) が "
            f"n_sessions ({n_sessions}) と不一致"
        )
    if blocks != 2:
        # formula v1 (s8b_floor_stats.holdout_floors) は d_{c,b} を b=1,2 に固定して直接
        # 添字参照する 2-block 専用式。blocks!=2 は式の前提を満たさないのでここで拒否する
        # (fail-closed。レビュー所見 F1-blocks-not-pinned-to-2)。
        raise FloorCampaignError(
            f"protocol.blocks ({blocks}) が formula v1 の前提 (2-block 固定) と不一致 "
            "(blocks は 2 でなければならない)"
        )
    extime_s = _pos_int(document["extime_s"], field="extime_s")
    retry_slots_per_cell = _non_neg_int(
        document["retry_slots_per_cell"], field="retry_slots_per_cell",
    )
    min_block_gap_s = _non_neg_number(
        document["min_block_gap_s"], field="min_block_gap_s",
    )
    wired_min_rel_floor = document["wired_min_rel_floor"]
    if (isinstance(wired_min_rel_floor, bool)
            or not isinstance(wired_min_rel_floor, (int, float))
            or not math.isfinite(float(wired_min_rel_floor))
            or not (0.0 < float(wired_min_rel_floor) <= 1.0)):
        raise FloorCampaignError("protocol.wired_min_rel_floor が (0,1] の有限数でない")
    wired_min_rel_floor = float(wired_min_rel_floor)

    reasons_raw = document["allowed_excluded_reasons"]
    if not isinstance(reasons_raw, list) or not reasons_raw:
        raise FloorCampaignError("protocol.allowed_excluded_reasons が空でない list でない")
    reasons = [
        _non_empty_str(reason, field="allowed_excluded_reasons[]")
        for reason in reasons_raw
    ]
    if len(set(reasons)) != len(reasons):
        raise FloorCampaignError("protocol.allowed_excluded_reasons に重複がある")

    return {
        "schema": PROTOCOL_SCHEMA,
        "formula": formula,
        "env_tag": env_tag,
        "ccbench_pin": ccbench_pin,
        "freeze": {"path": freeze_path, "sha256": freeze_sha},
        "stock_configuration": stock_configuration,
        "n_sessions": n_sessions,
        "reps": reps,
        "blocks": blocks,
        "replicates_per_block": replicates_per_block,
        "min_block_gap_s": min_block_gap_s,
        "master_seed": master_seed,
        "schedule_algorithm": SCHEDULE_ALGORITHM,
        "extime_s": extime_s,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": retry_slots_per_cell,
        "allowed_excluded_reasons": reasons,
    }


# --------------------------------------------------------------------------- #
# freeze 構造検査 + セル列挙 (POINTS 手書き禁止・freeze から取る)               #
# --------------------------------------------------------------------------- #

def _holdout_workload(holdout: Mapping, *, holdout_id: str) -> dict:
    records = holdout.get("records")
    threads = holdout.get("threads")
    workload = holdout.get("ycsb")
    if (isinstance(records, bool) or not isinstance(records, int) or records <= 0
            or isinstance(threads, bool) or not isinstance(threads, int) or threads <= 0):
        raise FloorCampaignError(f"holdout {holdout_id} の records/threads が正整数でない")
    if not isinstance(workload, Mapping) or not workload:
        raise FloorCampaignError(f"holdout {holdout_id} の ycsb が空でない object でない")
    for key, value in workload.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise FloorCampaignError(f"holdout {holdout_id} の ycsb が str→str でない")
    return {"records": records, "threads": threads, "workload": dict(workload)}


def enumerate_cells(freeze: Mapping, *, stock_configuration: str) -> list[dict]:
    """freeze から 12 セル (holdout × configuration) を決定論的に列挙する (純粋関数)。

    構成集合は全 holdout で一致し、stock_configuration を含むことを検査する。
    records/threads/workload は freeze の holdout から取る (POINTS 手書き・rr 値コピー禁止)。
    """
    holdouts_obj = freeze.get("holdouts")
    if not isinstance(holdouts_obj, Mapping) or not holdouts_obj:
        raise FloorCampaignError("freeze.holdouts が空でない object でない")
    holdout_ids = sorted(holdouts_obj)

    configurations: Optional[list[str]] = None
    per_holdout: dict[str, dict] = {}
    for holdout_id in holdout_ids:
        holdout = holdouts_obj[holdout_id]
        if not isinstance(holdout, Mapping):
            raise FloorCampaignError(f"holdout {holdout_id} が object でない")
        binding = holdout.get("variant_binding")
        entries = binding.get("entries") if isinstance(binding, Mapping) else None
        if not isinstance(entries, Mapping) or not entries:
            raise FloorCampaignError(
                f"holdout {holdout_id} の variant_binding.entries が空でない object でない"
            )
        entry_ids = sorted(entries)
        if configurations is None:
            configurations = entry_ids
        elif entry_ids != configurations:
            raise FloorCampaignError(
                f"holdout {holdout_id} の構成集合が他 holdout と不一致"
            )
        if stock_configuration not in entries:
            raise FloorCampaignError(
                f"holdout {holdout_id} の entries に stock_configuration "
                f"({stock_configuration}) がない"
            )
        per_holdout[holdout_id] = {
            **_holdout_workload(holdout, holdout_id=holdout_id),
        }

    assert configurations is not None
    cells: list[dict] = []
    for holdout_id in holdout_ids:
        info = per_holdout[holdout_id]
        for configuration_id in configurations:
            cells.append({
                "cell_id": f"{holdout_id}::{configuration_id}",
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "records": info["records"],
                "threads": info["threads"],
                "workload": info["workload"],
            })
    return cells


# --------------------------------------------------------------------------- #
# schedule (seed 均衡置換, 純粋関数)                                            #
# --------------------------------------------------------------------------- #

def _permutation_seed(master_seed: str, block: int, replicate: int) -> int:
    payload = f"{master_seed}/{block}/{replicate}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def build_schedule(*, cells: list[dict], master_seed: str, blocks: int,
                   replicates_per_block: int) -> list[dict]:
    """block × replicate ごとに 12 セルを seed 決定の置換で並べた session 列を作る (純粋関数)。

    seed = int.from_bytes(sha256(f"{master_seed}/{b}/{r}").digest()[:8], "big") による
    ``random.Random`` の shuffle。session 列 {seq, block, replicate, cell_id} を返す。
    """
    cell_ids = [cell["cell_id"] for cell in cells]
    rows: list[dict] = []
    for block in range(1, blocks + 1):
        for replicate in range(replicates_per_block):
            permuted = list(cell_ids)
            random.Random(_permutation_seed(master_seed, block, replicate)).shuffle(permuted)
            for cell_id in permuted:
                rows.append({
                    "seq": len(rows),
                    "block": block,
                    "replicate": replicate,
                    "cell_id": cell_id,
                })
    return rows


# --------------------------------------------------------------------------- #
# journal (append-only jsonl + fsync)                                          #
# --------------------------------------------------------------------------- #

def _journal_append(journal_path: Path, record: Mapping) -> None:
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with open(journal_path, "a", encoding="utf-8") as stream:
        stream.write(line + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _read_journal(journal_path: Path) -> list[dict]:
    if not journal_path.exists():
        return []
    records: list[dict] = []
    with open(journal_path, "r", encoding="utf-8") as stream:
        for lineno, raw in enumerate(stream, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                # 末尾切れ (crash) の 1 行。fail-closed: truncated journal の自動続行は
                # 危険なので拒否する (都合のよい session 再現を許さない, 所見 G10)。
                raise FloorCampaignError(
                    f"journal 行 {lineno} が壊れている (truncated crash の疑い): {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise FloorCampaignError(f"journal 行 {lineno} が object でない")
            records.append(value)
    return records


# --------------------------------------------------------------------------- #
# strict single-tenant probe (規律4, 自前 pgrep)                               #
# --------------------------------------------------------------------------- #

def _default_probe_fn() -> tuple[int, str]:
    """pgrep -af 'ycsb_.*\\.exe' を 1 回叩き (rc, stdout) を返す (OSError は投げる)。"""
    result = subprocess.run(
        ["pgrep", "-af", r"ycsb_.*\.exe"], capture_output=True, text=True,
    )
    return result.returncode, result.stdout


def strict_probe(probe_fn: Callable[[], tuple[int, str]]) -> dict:
    """計測前後の臨界区間 probe。競合検知は lag-free の確定信号 (規律4)。

    rc==1 → マッチ無し = 競合なし。rc==0 → 自プロセス子孫を除外して残れば競合 (``competing``
    に生行を載せて返す — 呼び手が当該 session を ``competing_process`` で無効にする)。それ以外の
    rc (rc>1)・OSError・**pid parse 不能** → CampaignAbort (fail-closed。パッケージ 裁定 F2 の
    「実行不能・rc>1・parse 不能は campaign abort」)。共有 ``competing_bench_pids`` も B-1 以降
    fail-closed だが、floor は kind 付き CampaignAbort・生出力 journal・competing_process retry を
    要するため自前で叩く。probe の生出力は戻り値に含め、呼び手が journal に残す。
    """
    try:
        rc, stdout = probe_fn()
    except OSError as exc:
        raise CampaignAbort(f"strict probe が OSError: {exc}") from exc
    if rc == 1:
        return {"rc": rc, "stdout": stdout, "competing": []}
    if rc != 0:
        raise CampaignAbort(f"strict probe の rc が想定外: {rc} (stdout={stdout[:200]!r})")

    excluded = _self_and_descendant_pids(os.getpid())
    competing: list[str] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        pid_field = line.split(None, 1)[0]
        try:
            pid = int(pid_field)
        except ValueError as exc:
            raise CampaignAbort(
                f"strict probe の pgrep 行から pid を parse できない: {line!r}"
            ) from exc
        if pid not in excluded:
            competing.append(line)
    return {"rc": rc, "stdout": stdout, "competing": competing}


# --------------------------------------------------------------------------- #
# boot / host provenance                                                       #
# --------------------------------------------------------------------------- #

def _boot_id() -> Optional[str]:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip() or None
    except (OSError, UnicodeError):
        return None


def _wall_marker(monotonic_fn: Callable[[], float], now_fn: Callable[[], dt.datetime]) -> dict:
    return {
        "boot_id": _boot_id(),
        "hostname": socket.gethostname(),
        "utc": now_fn().isoformat(),
        "monotonic": float(monotonic_fn()),
    }


# --------------------------------------------------------------------------- #
# ScalePoint → session 射影 (s8b_floor_stats の有効性契約に従う)                #
# --------------------------------------------------------------------------- #

_EXEC_FAIL_RE = re.compile(r"(\d+)/\d+ reps failed to execute")


def _count_exec_failures(notes) -> int:
    """ScalePoint.notes から実行失敗した rep 数を数える (measure_point の集約 note を読む)。"""
    for note in notes or []:
        if not isinstance(note, str):
            continue
        match = _EXEC_FAIL_RE.search(note)
        if match:
            return int(match.group(1))
    return 0


def _project_scalepoint(scale_point, *, reps: int) -> dict:
    """ScalePoint を SessionRecord の計測フィールドへ射影する (throughputs / exec_failures)。

    有効性判定そのものは ``s8b_floor_stats.session_median`` が正本 (呼び手が SessionRecord を
    組んで問い合わせる)。ここは生計測の抽出だけを行う。
    """
    throughputs = [float(t) for t in (getattr(scale_point, "throughputs", None) or [])]
    exec_failures = _count_exec_failures(getattr(scale_point, "notes", None))
    return {"throughputs": throughputs, "exec_failures": exec_failures}


# --------------------------------------------------------------------------- #
# build 12 cells (oracle と同一経路, trace-disabled)                           #
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def _prepared_binding(
        *, freeze: Mapping, holdout_id: str, configuration_id: str,
        ccbench_pin: str, prepare_fn):
    """共有 materializer の floor 境界 wrapper。identity 合成の MaterializationError だけを
    FloorCampaignError へ因果付き変換し (CLI main が JSON で捕捉する)、consumer body の
    他例外・cleanup 例外はそのまま透過させる。"""
    try:
        with prepared_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id, ccbench_pin=ccbench_pin,
                prepare_fn=prepare_fn) as (identity, prepared):
            yield identity, prepared
    except MaterializationError as exc:
        raise FloorCampaignError(str(exc)) from exc


def build_cells(freeze: Mapping, cells: list[dict], *, ccbench_pin: str,
                out_root: Path, prepare_fn) -> dict[str, dict]:
    """全 12 セルを実行開始前に実体化・ビルドし、binary path と full sha256 を返す。

    oracle と同一経路 (共有 ``s8b_materialization.prepared_binding`` の contextmanager 内で
    ``buildcache.build(trace=False, cache_root=<out_root>/s8b-build-cache,
    ccbench_dir=prepared.ccbench_dir, src_token=prepared.src_token)``) を使うので、floor を
    測るバイナリと oracle 本走のバイナリが同一 identity になる。途中 rebuild はしない。

    ``binary_sha256`` は ``buildcache.build`` が計算済みの ``result.bin_sha256`` を単一ソース
    として記録する (record 時の再読・再ハッシュをやめる, A-4)。これは build 時点の byte を
    写した provenance snapshot であって、以後の実行 byte の同一性を保証するものではない。"""
    cache_root = str(out_root / "s8b-build-cache")
    built: dict[str, dict] = {}
    for cell in cells:
        holdout_id = cell["holdout_id"]
        configuration_id = cell["configuration_id"]
        with _prepared_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id, ccbench_pin=ccbench_pin,
                prepare_fn=prepare_fn) as (identity, prepared):
            result = buildcache.build(
                prepared.genome, ccbench_commit=ccbench_pin, trace=False,
                cache_root=cache_root, ccbench_dir=prepared.ccbench_dir,
                src_token=prepared.src_token,
            )
            binary_path = Path(result.binary)
            built[cell["cell_id"]] = {
                "cell_id": cell["cell_id"],
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "binary": str(binary_path),
                "binary_sha256": result.bin_sha256,
                "bin_hash_short": result.bin_hash,
                "binding": dict(identity),
                "configure_cmd": result.configure_cmd,
                "build_cmd": result.build_cmd,
                "cached": result.cached,
            }
    return built


# --------------------------------------------------------------------------- #
# manifest (create-only)                                                        #
# --------------------------------------------------------------------------- #

def assemble_manifest(*, protocol: Mapping, protocol_sha256: str,
                      freeze_sha256: str, cells: list[dict],
                      built: Mapping, schedule: list[dict]) -> dict:
    """参照 hash と build identity・schedule を持つ floor manifest を組み立てる (純粋)。"""
    return {
        "schema_version": MANIFEST_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "freeze": dict(protocol["freeze"]),
        "freeze_sha256": freeze_sha256,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"],
        "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "extime_s": protocol["extime_s"],
        "blocks": protocol["blocks"],
        "replicates_per_block": protocol["replicates_per_block"],
        "cells": [dict(cell) for cell in cells],
        "binaries": {cid: dict(rec) for cid, rec in built.items()},
        "schedule": [dict(row) for row in schedule],
    }


def _write_create_only_json(path: Path, document: Mapping) -> bytes:
    """create-only で JSON を書き、書いた byte 列を返す (redo/上書きは fail-closed)。"""
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with open(path, "x", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise FloorCampaignError(f"既に存在するため上書きしない: {path}") from exc
    return payload.encode("utf-8")


# --------------------------------------------------------------------------- #
# session 実行エンジン (fresh/resume 共通)                                      #
# --------------------------------------------------------------------------- #

class _Runner:
    """schedule を直列・単一テナントで消化する実行エンジン (fresh/resume 共通)。

    臨界区間は session ごとに ``session-start → probe → measure → post-probe → session (end)``
    を journal へ即時記録する。crash した session は start だけが残り、resume では **terminal
    (再実行しない)** 扱いにする (パッケージ 裁定 F2: 完了/crash いずれも forward-only で再走禁止)。
    """

    def __init__(self, *, protocol, cells, cell_by_id, binaries, schedule,
                 journal_path, measure_fn, probe_fn, sleep_fn, monotonic_fn, now_fn):
        self.protocol = protocol
        self.cells = cells
        self.cell_by_id = cell_by_id
        self.binaries = binaries
        self.schedule = schedule
        self.journal_path = journal_path
        self.measure_fn = measure_fn
        self.probe_fn = probe_fn
        self.sleep_fn = sleep_fn
        self.monotonic_fn = monotonic_fn
        self.now_fn = now_fn
        self.reps = protocol["reps"]
        self.retry_slots = protocol["retry_slots_per_cell"]
        self.min_gap = protocol["min_block_gap_s"]
        self.allowed_reasons = set(protocol["allowed_excluded_reasons"])
        self.records = _read_journal(journal_path)  # fresh なら []

    def _emit(self, record: dict) -> None:
        _journal_append(self.journal_path, record)
        self.records.append(record)

    def _check_reason(self, reason: str) -> str:
        if reason not in self.allowed_reasons:
            raise CampaignAbort(
                f"excluded_reason ({reason!r}) が allowed_excluded_reasons に無い "
                "(閉じた表と protocol の不一致, fail-closed)"
            )
        return reason

    def _session_record(self, *, seq, block, replicate, cell_id, kind, retry,
                        throughputs, exec_failures, excluded_reason,
                        probe_before, probe_after, run_cmd, notes) -> dict:
        cell = self.cell_by_id[cell_id]
        # SessionRecord (s8b_floor_stats) と同じ計測フィールドで有効性を確定する。
        rec = s8b_floor_stats.SessionRecord(
            cell_id=cell_id, holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], block=block, seq=seq,
            throughputs=tuple(throughputs), reps_expected=self.reps,
            exec_failures=exec_failures,
            excluded_reason=(self._check_reason(excluded_reason)
                             if excluded_reason is not None else None),
            retry=retry,
        )
        median = s8b_floor_stats.session_median(rec)
        valid = median is not None
        reason = rec.excluded_reason
        if not valid and reason is None:
            # 計測が終わり excluded 事由 (競合/起動) は無いのに無効 = 非有限/部分 rep 出力。
            reason = self._check_reason(_REASON_PARTIAL)
        return {
            "event": "session",
            "kind": kind,
            "seq": seq,
            "block": block,
            "replicate": replicate,
            "cell_id": cell_id,
            "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": cell["workload"],
            # --- SessionRecord と同じ key (verify_floor_artifact が再構成する) ---
            "throughputs": list(throughputs),
            "reps_expected": self.reps,
            "exec_failures": exec_failures,
            "excluded_reason": reason,
            "retry": retry,
            # --- driver の付帯情報 (verify は無視する) ---
            "session_median": median,
            "valid": valid,
            "run_cmd": run_cmd,
            "notes": list(notes or []),
            "probe_before": probe_before,
            "probe_after": probe_after,
        }

    def _run_session(self, *, seq: int, block: int, replicate: Optional[int],
                     cell_id: str, kind: str) -> dict:
        retry = kind == "retry"
        self._emit({
            "event": "session-start", "seq": seq, "kind": kind, "cell_id": cell_id,
            "block": block, "replicate": replicate,
            "started_iso": self.now_fn().isoformat(),
        })
        cell = self.cell_by_id[cell_id]
        binary = self.binaries[cell_id]["binary"]

        probe_before = strict_probe(self.probe_fn)  # rc>1/OSError/parse 不能 → CampaignAbort
        if probe_before["competing"]:
            record = self._session_record(
                seq=seq, block=block, replicate=replicate, cell_id=cell_id, kind=kind,
                retry=retry, throughputs=[], exec_failures=0,
                excluded_reason=_REASON_COMPETING, probe_before=probe_before,
                probe_after=None, run_cmd=None, notes=["preflight probe 競合で計測をスキップ"],
            )
            self._emit(record)
            return record

        run_cmd = None
        notes: list = []
        try:
            scale_point = self.measure_fn(
                binary, cell["records"], cell["threads"], cell["workload"],
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            # 全 rep が実行不能 = 起動失敗系。session 無効 (retry 可)。
            record = self._session_record(
                seq=seq, block=block, replicate=replicate, cell_id=cell_id, kind=kind,
                retry=retry, throughputs=[], exec_failures=self.reps,
                excluded_reason=_REASON_LAUNCH, probe_before=probe_before,
                probe_after=None, run_cmd=None,
                notes=[f"measure 失敗: {type(exc).__name__}: {str(exc)[:200]}"],
            )
            self._emit(record)
            return record

        run_cmd = getattr(scale_point, "run_cmd", None)
        notes = list(getattr(scale_point, "notes", []) or [])
        probe_after = strict_probe(self.probe_fn)
        projection = _project_scalepoint(scale_point, reps=self.reps)
        excluded_reason = _REASON_COMPETING if probe_after["competing"] else None
        record = self._session_record(
            seq=seq, block=block, replicate=replicate, cell_id=cell_id, kind=kind,
            retry=retry, throughputs=projection["throughputs"],
            exec_failures=projection["exec_failures"], excluded_reason=excluded_reason,
            probe_before=probe_before, probe_after=probe_after, run_cmd=run_cmd,
            notes=notes,
        )
        self._emit(record)
        return record

    # --- journal 由来の状態再構成 (fresh/resume 共通) --------------------- #

    def _started_seqs(self) -> set[int]:
        """start 済み (完了 or crash) の seq。resume はこれを skip する (再走禁止)。"""
        return {r["seq"] for r in self.records if r.get("event") == "session-start"}

    def _completed_blocks(self) -> set[int]:
        return {r["block"] for r in self.records if r.get("event") == "block-complete"}

    def _retries_used(self, cell_id: str) -> int:
        return sum(1 for r in self.records
                   if r.get("event") == "session" and r.get("retry") is True
                   and r.get("cell_id") == cell_id)

    def _block_deficit(self, block: int) -> dict[str, int]:
        """block 内で planned が無効だった数から、同 block の有効 retry で埋めた数を引く。"""
        invalid_planned: dict[str, int] = {}
        valid_retry: dict[str, int] = {}
        for r in self.records:
            if r.get("event") != "session" or r.get("block") != block:
                continue
            cell_id = r.get("cell_id")
            if not r.get("retry") and not r.get("valid"):
                invalid_planned[cell_id] = invalid_planned.get(cell_id, 0) + 1
            elif r.get("retry") and r.get("valid"):
                valid_retry[cell_id] = valid_retry.get(cell_id, 0) + 1
        deficit: dict[str, int] = {}
        for cell_id, count in invalid_planned.items():
            remaining = count - valid_retry.get(cell_id, 0)
            if remaining > 0:
                deficit[cell_id] = remaining
        return deficit

    def _next_retry_seq(self) -> int:
        seqs = [r["seq"] for r in self.records
                if r.get("event") in {"session", "session-start"}]
        base = len(self.schedule) - 1
        return max(seqs + [base]) + 1

    # --- block 実行 ------------------------------------------------------- #

    def _wait_gap(self, prev_end_monotonic: Optional[float]) -> None:
        if prev_end_monotonic is None or self.min_gap <= 0:
            return
        deadline = prev_end_monotonic + self.min_gap
        while self.monotonic_fn() < deadline:
            self.sleep_fn(min(1.0, deadline - self.monotonic_fn()))

    def _retry_block(self, block: int) -> None:
        """block 末尾に無効 session を retry_slots_per_cell まで補填する。

        retry_slots_per_cell はセルごとの **campaign 通算** 予算であり、block ごとに復活しない
        (``_retries_used`` は全 block 通算でカウントする)。block ごとの予算と誤読しないこと。
        block の時間窓内 (block 末尾) で消化し first-authorized-valid のみ採用、全 attempt 課金
        (journal に残る)。slot 超過はセル未確定のまま続行 (対称に完走し選択的打ち切りをしない)。
        """
        deficit = self._block_deficit(block)
        for cell_id in sorted(deficit):
            remaining = deficit[cell_id]
            while remaining > 0 and self._retries_used(cell_id) < self.retry_slots:
                record = self._run_session(
                    seq=self._next_retry_seq(), block=block, replicate=None,
                    cell_id=cell_id, kind="retry",
                )
                if record["valid"]:
                    remaining -= 1

    def run(self) -> None:
        if not any(r.get("event") == "campaign-start" for r in self.records):
            self._emit({
                "event": "campaign-start",
                **_wall_marker(self.monotonic_fn, self.now_fn),
            })

        started = self._started_seqs()
        completed_blocks = self._completed_blocks()
        rows_by_block: dict[int, list[dict]] = {}
        for row in self.schedule:
            rows_by_block.setdefault(row["block"], []).append(row)

        prev_end_monotonic: Optional[float] = None
        for block in sorted(rows_by_block):
            if block in completed_blocks:
                continue
            self._wait_gap(prev_end_monotonic)
            self._emit({
                "event": "block-start", "block": block,
                **_wall_marker(self.monotonic_fn, self.now_fn),
            })
            for row in rows_by_block[block]:
                if row["seq"] in started:
                    continue  # 完了 or crash 済み = 再走しない (forward-only)
                self._run_session(
                    seq=row["seq"], block=block, replicate=row["replicate"],
                    cell_id=row["cell_id"], kind="planned",
                )
            self._retry_block(block)
            self._emit({
                "event": "block-complete", "block": block,
                **_wall_marker(self.monotonic_fn, self.now_fn),
            })
            prev_end_monotonic = self.monotonic_fn()


# --------------------------------------------------------------------------- #
# terminal: floor 算出 (s8b_floor_stats) + artifact (create-only)              #
# --------------------------------------------------------------------------- #

def _session_records(records: list[dict]) -> list[dict]:
    return [r for r in records if r.get("event") == "session"]


def _cellstats_to_dict(cs) -> dict:
    return {
        "n_valid": cs.n_valid,
        "medians": list(cs.medians),
        "m": cs.m,
        "s": cs.s,
        "block_medians": cs.block_medians,
        "valid": cs.valid,
        "cv": cs.cv,
        "notes": list(cs.notes),
    }


def _floors_to_dict(hf) -> dict:
    return {
        "pairs": dict(hf.pairs),
        "scalar_alt": hf.scalar_alt,
        "scale_ref": hf.scale_ref,
        "diagnostics": hf.diagnostics,
    }


def assemble_result(*, protocol, mode, protocol_sha256, freeze_sha256,
                    manifest_sha256, cells, binaries, records) -> dict:
    """journal の生 session から floor artifact (result) を組み立てる。

    cell_stats / holdout_floors は ``s8b_floor_stats`` (formula v1) が正本。artifact の
    ``config`` / ``sessions`` / ``cells`` / ``floors`` は ``verify_floor_artifact`` が生
    session から再計算して自己申告値と厳密比較する形に合わせる。pilot の artifact には
    ``eligible_for_refreeze: false`` を焼き込む (再凍結資格は official のみ)。
    """
    n_sessions = protocol["n_sessions"]
    blocks = protocol["blocks"]
    replicates_per_block = protocol["replicates_per_block"]
    stock_configuration = protocol["stock_configuration"]
    wired_min_rel_floor = protocol["wired_min_rel_floor"]

    session_records = _session_records(records)
    records_by_cell: dict[str, list] = {}
    for cell in cells:
        records_by_cell[cell["cell_id"]] = []
    for raw in session_records:
        cell_id = raw["cell_id"]
        records_by_cell.setdefault(cell_id, []).append(
            s8b_floor_stats.SessionRecord(
                cell_id=cell_id, holdout_id=raw["holdout_id"],
                configuration_id=raw["configuration_id"], block=int(raw["block"]),
                seq=int(raw["seq"]), throughputs=tuple(raw["throughputs"]),
                reps_expected=int(raw["reps_expected"]),
                exec_failures=int(raw["exec_failures"]),
                excluded_reason=raw["excluded_reason"], retry=bool(raw["retry"]),
            )
        )

    # セル別統計 (s8b_floor_stats.cell_stats)。
    cell_stats_map: dict[str, object] = {}
    cells_out: dict[str, dict] = {}
    for cell in cells:
        cell_id = cell["cell_id"]
        cs = s8b_floor_stats.cell_stats(
            records_by_cell[cell_id], n_sessions=n_sessions, blocks=blocks,
            replicates_per_block=replicates_per_block,
        )
        cell_stats_map[cell_id] = cs
        cells_out[cell_id] = _cellstats_to_dict(cs)

    # holdout 別 floor (s8b_floor_stats.holdout_floors)。
    holdouts = sorted({cell["holdout_id"] for cell in cells})
    configurations = sorted({cell["configuration_id"] for cell in cells})
    floors_out: dict[str, dict] = {}
    for holdout_id in holdouts:
        holdout_cells = {
            cell["cell_id"]: cell_stats_map[cell["cell_id"]]
            for cell in cells if cell["holdout_id"] == holdout_id
        }
        stock_cell_id = f"{holdout_id}::{stock_configuration}"
        hf = s8b_floor_stats.holdout_floors(
            holdout_cells, stock_id=stock_cell_id,
            wired_min_rel_floor=wired_min_rel_floor,
        )
        floors_out[holdout_id] = _floors_to_dict(hf)

    excluded = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "retry": r.get("retry"),
            "excluded_reason": r.get("excluded_reason"), "block": r.get("block"),
        }
        for r in session_records if not r.get("valid")
    ]
    wall_ledger = [
        r for r in records
        if r.get("event") in {"campaign-start", "block-start", "block-complete"}
    ]

    return {
        "schema": RESULT_SCHEMA,
        "formula": protocol["formula"],
        "mode": mode,
        "eligible_for_refreeze": (mode == "official"),
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "manifest_sha256": manifest_sha256,
        "stock_configuration": stock_configuration,
        "wired_min_rel_floor": wired_min_rel_floor,
        "reps": protocol["reps"],
        "n_sessions": n_sessions,
        "holdouts": holdouts,
        "configurations": configurations,
        "binaries": {cid: dict(rec) for cid, rec in binaries.items()},
        # --- verify_floor_artifact が読む正本フィールド ---
        "config": {
            "n_sessions": n_sessions,
            "blocks": blocks,
            "replicates_per_block": replicates_per_block,
            "stock_configuration_id": stock_configuration,
            "wired_min_rel_floor": wired_min_rel_floor,
        },
        "sessions": session_records,
        "cells": cells_out,
        "floors": floors_out,
        # --- 付帯 ---
        "wall_ledger": wall_ledger,
        "excluded": excluded,
    }


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.4g}"
    return str(value)


def _render_result_md(result: Mapping) -> str:
    """人間向けサマリ (セル表 + floor 案 + 除外一覧)。"""
    lines: list[str] = []
    lines.append(f"# 8b floor campaign result — {result['env_tag']} / mode={result['mode']}")
    lines.append("")
    lines.append("> floor **案** (何も発効させていない)。freeze への floor 書込みは親が行う。")
    lines.append(f"> eligible_for_refreeze: {result['eligible_for_refreeze']}")
    lines.append("")
    lines.append(f"- formula: `{result['formula']}`")
    lines.append(f"- ccbench_pin: `{result['ccbench_pin']}`")
    lines.append(f"- protocol_sha256: `{result['protocol_sha256']}`")
    lines.append(f"- freeze_sha256: `{result['freeze_sha256']}`")
    lines.append(f"- manifest_sha256: `{result['manifest_sha256']}`")
    lines.append(f"- stock_configuration: `{result['stock_configuration']}`")
    lines.append(f"- wired_min_rel_floor: {result['wired_min_rel_floor']}")
    lines.append("")

    lines.append("## セル統計 (session-median の散らばり)")
    lines.append("")
    cells = result.get("cells") or {}
    lines.append("| cell | valid | n_valid | m (median) | s (stdev) | cv |")
    lines.append("|---|:---:|---:|---:|---:|---:|")
    for cell_id in sorted(cells):
        c = cells[cell_id]
        lines.append(
            f"| `{cell_id}` | {c.get('valid')} | {c.get('n_valid')} | "
            f"{_fmt(c.get('m'))} | {_fmt(c.get('s'))} | {_fmt(c.get('cv'))} |"
        )
    lines.append("")

    lines.append("## floor 案 (holdout 別)")
    lines.append("")
    floors = result.get("floors") or {}
    for holdout_id in sorted(floors):
        hf = floors[holdout_id]
        lines.append(f"### {holdout_id}")
        lines.append("")
        lines.append(f"- scalar_alt (全 pair の max): {_fmt(hf.get('scalar_alt'))}")
        lines.append(f"- scale_ref (m_stock): {_fmt(hf.get('scale_ref'))}")
        lines.append("")
        pairs = hf.get("pairs") or {}
        lines.append("| pair (cell) | floor_pair |")
        lines.append("|---|---:|")
        for cell_id in sorted(pairs):
            lines.append(f"| `{cell_id}` | {_fmt(pairs[cell_id])} |")
        lines.append("")

    lines.append("## 除外 session")
    lines.append("")
    excluded = result.get("excluded") or []
    if not excluded:
        lines.append("(なし)")
    else:
        lines.append("| seq | cell | retry | reason |")
        lines.append("|---:|---|:---:|---|")
        for item in excluded:
            lines.append(
                f"| {item['seq']} | `{item['cell_id']}` | {item.get('retry')} | "
                f"{item.get('excluded_reason')} |"
            )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# run_campaign (注入点)                                                         #
# --------------------------------------------------------------------------- #

def run_campaign(protocol, freeze_doc, *, out_root, mode, resume_dir=None,
                 measure_fn=None, probe_fn=None, sleep_fn=time.sleep,
                 monotonic_fn=time.monotonic, prepare_fn=None, now_fn=None) -> dict:
    """floor campaign を直列・単一テナントで実行し、floor 案 artifact を書いて返す。

    注入点 (テスト容易性、``between_run_floor`` の measure_fn 注入と同思想):
    ``measure_fn(binary, records, threads, workload) -> ScalePoint`` /
    ``probe_fn() -> (rc, stdout)`` / ``sleep_fn`` / ``monotonic_fn`` / ``prepare_fn`` /
    ``now_fn() -> datetime``。CLI main はこれらを実物で束ねるだけにする。``mode`` (pilot/
    official) と ``resume_dir`` は運用パラメタ。

    ``protocol`` は ``validate_protocol`` 済み dict でも生 dict でもよい (内部で再検証)、
    ``freeze_doc`` は ``load_verified_freeze`` の戻り値 (``VerifiedFreeze``: document/sha256)。
    freeze は protocol.freeze.sha256 と byte 一致を要求する (fail-closed)。

    ``protocol.retry_slots_per_cell`` はセルごとの **campaign 通算** 予算 (block ごとに復活
    しない) で、各 block 末尾 (``_Runner._retry_block``) で消化される。block ごとの予算と
    誤読しないこと。
    """
    if not isinstance(freeze_doc, VerifiedFreeze):
        raise FloorCampaignError("freeze_doc が load_verified_freeze の戻り値でない")
    now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    prepare_fn = prepare_fn or prepare_cell
    probe_fn = probe_fn or _default_probe_fn

    protocol = validate_protocol(protocol)

    # env 束縛: ENV_TAG != protocol.env_tag → 拒否 (計測環境の取り違え防止)。
    if ENV_TAG != protocol["env_tag"]:
        raise FloorCampaignError(
            f"env_tag 不一致: protocol={protocol['env_tag']} != p2_2.ENV_TAG={ENV_TAG}"
        )

    freeze = freeze_doc.document
    freeze_sha256 = freeze_doc.sha256
    if freeze_sha256 != protocol["freeze"]["sha256"]:
        raise FloorCampaignError(
            "freeze byte sha256 が protocol.freeze.sha256 と不一致 (bytes-hash pin 破れ)"
        )
    # 構造だけを最小検査する (verify_document は呼ばない — docstring 参照)。
    if freeze.get("schema_version") != FREEZE_SCHEMA:
        raise FloorCampaignError(f"freeze.schema_version が {FREEZE_SCHEMA} でない")

    cells = enumerate_cells(freeze, stock_configuration=protocol["stock_configuration"])
    cell_by_id = {cell["cell_id"]: cell for cell in cells}
    schedule = build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        blocks=protocol["blocks"], replicates_per_block=protocol["replicates_per_block"],
    )
    protocol_sha256 = _canonical_sha256(protocol)

    if measure_fn is None:
        extime_s = protocol["extime_s"]
        reps = protocol["reps"]

        def measure_fn(binary, records, threads, workload):  # noqa: ANN001
            return measure_point(
                binary, records, threads, CLK, extime=extime_s, reps=reps,
                workload=workload, numactl=NUMACTL,
            )

    out_root = Path(out_root)

    if resume_dir is None:
        # fresh: run_dir を作り、全 12 セルをビルドし manifest を封印する。
        run_dir = _fresh_run_dir(out_root, protocol, mode, protocol_sha256, now_fn)
        journal_path = run_dir / "journal.jsonl"
        manifest_path = run_dir / "manifest.json"
        built = build_cells(
            freeze, cells, ccbench_pin=protocol["ccbench_pin"],
            out_root=out_root, prepare_fn=prepare_fn,
        )
        manifest = assemble_manifest(
            protocol=protocol, protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256, cells=cells, built=built, schedule=schedule,
        )
        manifest_bytes = _write_create_only_json(manifest_path, manifest)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    else:
        # resume: 既存 manifest/journal を読み、protocol/freeze/manifest/binary hash を照合し
        # forward-only 続行する。完了 or crash 済み seq は skip、再実行は拒否。
        run_dir = Path(resume_dir)
        journal_path = run_dir / "journal.jsonl"
        manifest_path = run_dir / "manifest.json"
        _manifest, manifest_sha256, built = _load_resume_manifest(
            manifest_path, protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        )
        # manifest は binary_sha256 を記録するだけでなく、disk 上バイナリと再照合してはじめて
        # 「binary hash に限り forward-only」(凍結案パッケージ 裁定 F2) を実装で満たす
        # (所見 F3-resume-binary-hash-not-enforced)。
        _verify_resume_binaries(built)

    runner = _Runner(
        protocol=protocol, cells=cells, cell_by_id=cell_by_id, binaries=built,
        schedule=schedule, journal_path=journal_path, measure_fn=measure_fn,
        probe_fn=probe_fn, sleep_fn=sleep_fn, monotonic_fn=monotonic_fn, now_fn=now_fn,
    )
    if resume_dir is not None:
        _verify_resume_journal(runner.records)

    try:
        runner.run()
    except CampaignAbort as exc:
        _journal_append(journal_path, {
            "event": "terminal", "status": "aborted", "reason": str(exc),
        })
        raise

    result = assemble_result(
        protocol=protocol, mode=mode, protocol_sha256=protocol_sha256,
        freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
        cells=cells, binaries=built, records=runner.records,
    )

    # 自己検査: verify_floor_artifact(result) == [] を満たさなければ artifact を書かない。
    problems = s8b_floor_stats.verify_floor_artifact(result)
    if problems:
        _journal_append(journal_path, {
            "event": "terminal", "status": "artifact-invalid", "problems": list(problems),
        })
        raise FloorCampaignError(f"verify_floor_artifact が非空: {problems}")

    _write_create_only_json(run_dir / "result.json", result)
    (run_dir / "result.md").write_text(_render_result_md(result), encoding="utf-8")
    _journal_append(journal_path, {"event": "terminal", "status": "completed"})
    return {"status": "completed", "run_dir": str(run_dir), "result": result}


def _fresh_run_dir(out_root: Path, protocol: Mapping, mode: str,
                   protocol_sha256: str, now_fn) -> Path:
    ts = now_fn().strftime("%Y%m%dT%H%M%SZ")
    base = Path(env_scope_dir(protocol["env_tag"], output_root=str(out_root)))
    run_dir = base / "calibration" / f"s8b-floor-{mode}" / f"{ts}-{protocol_sha256[:8]}"
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise FloorCampaignError(f"run_dir が既に存在する: {run_dir}") from exc
    return run_dir


def _load_resume_manifest(manifest_path: Path, *, protocol_sha256: str,
                          freeze_sha256: str) -> tuple[dict, str, dict]:
    try:
        raw = manifest_path.read_bytes()
    except OSError as exc:
        raise FloorCampaignError(f"resume: manifest を読めない: {manifest_path}: {exc}") from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FloorCampaignError(f"resume: manifest を parse できない: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise FloorCampaignError("resume: manifest が object でない")
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    if manifest.get("protocol_sha256") != protocol_sha256:
        raise FloorCampaignError("resume: protocol sha256 が manifest と不一致")
    if manifest.get("freeze_sha256") != freeze_sha256:
        raise FloorCampaignError("resume: freeze sha256 が manifest と不一致")
    binaries = manifest.get("binaries")
    if not isinstance(binaries, Mapping):
        raise FloorCampaignError("resume: manifest.binaries が不正")
    return dict(manifest), manifest_sha256, {cid: dict(rec) for cid, rec in binaries.items()}


def _verify_resume_binaries(built: Mapping) -> None:
    """resume: manifest 記録の binary_sha256 と disk 上バイナリの実 hash を全セル再照合する。

    凍結案パッケージ (裁定 F2、``output/insights/2026-07-16_s8b-floor-protocol-package.md:166``)
    は「resume は同一 protocol/freeze/manifest/binary hash に限り forward-only」と謳うが、
    ``_load_resume_manifest`` の hash 照合は protocol_sha256/freeze_sha256 止まりで、記録済み
    binary_sha256 を消費していなかった (記録するだけで検証しない破れ、所見
    F3-resume-binary-hash-not-enforced)。バイナリの不在・差し替えは resume 前提そのものが
    崩れているため、個々 session の launch_failure (retry 可) には倒さず、campaign 続行不可の
    FloorCampaignError で拒否する (fail-closed)。
    """
    for cell_id in sorted(built):
        rec = built[cell_id]
        binary = rec.get("binary")
        recorded = rec.get("binary_sha256")
        if not isinstance(binary, str) or not binary:
            raise FloorCampaignError(
                f"resume: セル {cell_id} の manifest.binaries に binary path が無い"
            )
        if not isinstance(recorded, str) or not recorded:
            raise FloorCampaignError(
                f"resume: セル {cell_id} の manifest.binaries に binary_sha256 が無い"
            )
        actual = _full_sha256(Path(binary))  # バイナリ不在/読めない場合はここで FloorCampaignError
        if actual != recorded:
            raise FloorCampaignError(
                f"resume: セル {cell_id} のバイナリ sha256 が manifest と不一致 "
                f"(記録={recorded} 実測={actual}, path={binary})"
            )


def _verify_resume_journal(records: list[dict]) -> None:
    """resume: campaign-start が存在し、既 completed の campaign を再実行しないことを検査する。"""
    if not any(r.get("event") == "campaign-start" for r in records):
        raise FloorCampaignError("resume: journal に campaign-start がない")
    if any(r.get("event") == "terminal" and r.get("status") == "completed"
           for r in records):
        raise FloorCampaignError("resume: 既に completed 済みの campaign は再実行しない")


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="8b floor campaign driver (floor 案の実測。何も発効させない)",
    )
    parser.add_argument("--mode", choices=["pilot", "official"], required=True)
    parser.add_argument("--protocol", type=Path, required=True,
                        help="floor protocol JSON (s8b-floor-protocol/v1)")
    parser.add_argument("--resume", type=Path, default=None,
                        help="既存 run_dir を forward-only で続行する")
    # env・経路・数値の上書き面は作らない (--marker-root 撤去の教訓、worklog 2026-07-16 (12))。
    return parser


def _resolve_freeze_path(freeze_path_text: str) -> Path:
    path = Path(freeze_path_text)
    return path if path.is_absolute() else ROOT / path


def main(argv=None) -> int:
    args = _parser().parse_args(argv)

    # official は §8 未裁定 (承認束縛方式が未確定) につき現時点で常に拒否する = fail-closed 既定。
    if args.mode == "official":
        print(json.dumps({
            "status": "refused",
            "reason": "official mode は承認束縛方式が §8 未裁定のため現時点で拒否する "
                      "(pilot のみ実行可)",
        }, ensure_ascii=False))
        return 2

    try:
        raw_protocol = load_protocol(args.protocol)
        protocol = validate_protocol(raw_protocol)
        freeze_path = _resolve_freeze_path(protocol["freeze"]["path"])
        verified = load_verified_freeze(freeze_path, expected_hash=protocol["freeze"]["sha256"])
        out_root = Path(repo_output_root())
        outcome = run_campaign(
            protocol, verified, out_root=out_root, mode=args.mode,
            resume_dir=args.resume,
        )
    except FloorCampaignError as exc:
        print(json.dumps({
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False))
        return 1
    print(json.dumps({
        "status": outcome["status"], "run_dir": outcome["run_dir"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
