# -*- coding: utf-8 -*-
"""8b floor campaign driver — holdout freeze から floor 案を実測する env-neutral driver (v2)。

役割: holdout freeze v1 の 2 holdout × 6 構成 = 12 セルを floor protocol (明示入力・未凍結数値の
デフォルト内蔵禁止) が定める schedule どおり直列・単一テナントで計測し、``s8b_floor_stats``
(formula v2) で floor 案を算出して artifact (result.json/md) に書く。**freeze への floor 書込み・
phase 文書の編集はしない** (§8 手続き: 発効はユーザー承認事項)。本 driver は「案」を出すだけで、
何も発効させない。

**この floor は単一 campaign 内で観測された session dispersion に基づく記述的下限であり、
時間ドリフト・cold-boot・温度など別 run 間の変動は含まれない** (formula v2、§9 承認状態
2026-07-18)。式は本 driver の外 (``s8b_floor_stats``, formula v2) が正本。driver は計測して
SessionRecord を作り、cell_stats / holdout_floors / verify_floor_artifact を呼ぶだけで、floor の
式を自前で持たない。session 有効性・異常判定 (session 内 CV / セル間 CV) はすべて stats 側の
``assess_session`` / ``cell_cv_exceeds`` が正本で、driver は生値の抽出だけを行う (α-8/δ-6)。

系譜: 計測は calibration driver (``between_run_floor.py``) と同型で ``measure_point`` を直接呼ぶ
(``pipeline.evaluate`` は使わない — floor は correctness gate を通す本走ではなく noise の実測。
floor 経路に settle は使わない = ``measure_point(settle_first=False)`` 既定)。build 経路だけ oracle
と揃える (共有 ``s8b_materialization.prepared_binding`` + ``buildcache.build(trace=False)``) ので、
floor を測るバイナリと oracle 本走のバイナリが同一 identity になる。

env 契約 (F4): 計測環境の固有値 (clocks_per_us / numactl) は ``env_contract.lookup(env_tag)`` から
取る。driver は env 固有 literal を持たない (γ-16 の AST 検査が機械固定)。attestation が入る登録段
までの暫定 machine-pin として、契約の env_tag が実行機の ``p2_2.ENV_TAG`` と一致することを要求する。

絶対規律の適用:
- 規律1 (観測者効果): 計測は trace-disabled build (``trace=False``)。
- 規律4 (単一テナント直列): session ごとの臨界区間 (probe → measure → post-probe → journal) で
  自前の strict probe (pgrep) を計測の前後に叩く。**rc=1 のみ「競合なし」**、rc=0 の競合列挙は
  当該 session を無効 (``competing_process``, retry 可) にし、実行不能・rc>1・parse 不能は
  **CampaignAbort** で倒す。**post-probe は measure が例外を投げた経路でも finally 相当で必ず
  実行する** (β-7)。
- 規律6 (信頼境界): freeze は素性の知れない外部内容。bytes-hash pin で束縛し、以後この単一
  parse 結果だけを使う (再読込禁止)。

fail-closed の原則: 縮退・欠測・不正入力・競合はすべて null / 拒否 / 判定不能へ倒す。protocol
config の数値はコードに既定値を持たず入力必須にする (F14 対策)。CLI に env・経路・数値の上書き面は
作らない。

official mode は承認束縛方式が §8 未裁定のため **core (run_campaign) で無条件拒否する** (δ-3)。
pilot の artifact には ``eligible_for_refreeze: false`` を焼き込む。
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
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from calibrator.runner import (  # noqa: E402
    CompetingBenchProbeError,
    classify_competing_probe,
    measure_point,
)
from campaign import buildcache, s8b_floor_stats  # noqa: E402
from campaign import s8b_approved  # noqa: E402  (承認定数の単一源 C4-3/C4-4)
from campaign import env_contract as _env_contract  # noqa: E402
from campaign import execution_guard  # noqa: E402  (共有 machine-pin + receipt)
from campaign import s8b_holdout_freeze as _holdout_freeze  # noqa: E402  (launch certificate の clean scan)
from campaign import s8b_freeze_io as _freeze_io  # noqa: E402
from campaign.layout import env_scope_dir, repo_output_root  # noqa: E402
from campaign.p2_2 import ENV_TAG  # noqa: E402  (machine-pin 用のみ。CLK/NUMA は contract 経由)
from campaign.s1_direct_comparison import prepare_cell  # noqa: E402
from campaign.s8b_materialization import (  # noqa: E402
    MaterializationError,
    prepared_binding,
)

# 版名は一括 v2 改版し交差受理を拒否する (β-2/δ-2)。freeze schema は v1 freeze を読むため据置。
PROTOCOL_SCHEMA = "s8b-floor-protocol/v2"
FREEZE_SCHEMA = "8b-holdout-freeze/v1"
SCHEDULE_ALGORITHM = "round-permutation/v2"
RESULT_SCHEMA = "s8b-floor-result/v2"
MANIFEST_SCHEMA = "s8b-floor-manifest/v2"
JOURNAL_SCHEMA = "s8b-floor-journal/v2"
LAUNCH_CERT_SCHEMA = "s8b-floor-launch-certificate/v1"

# protocol JSON の必須 key (strict: これ以外の key・欠落・型不正・duplicate key はすべて拒否)。
# v2: blocks / replicates_per_block / min_block_gap_s を削除、session_cv_max / cell_cv_max /
# scale_adequacy_rel_tolerance を追加 (β-1)。
_PROTOCOL_KEYS = frozenset({
    "schema", "formula", "env_tag", "ccbench_pin", "freeze", "stock_configuration",
    "n_sessions", "reps", "master_seed", "schedule_algorithm", "extime_s",
    "wired_min_rel_floor", "retry_slots_per_cell",
    "session_cv_max", "cell_cv_max", "scale_adequacy_rel_tolerance",
    "allowed_excluded_reasons",
    # §5-v (F4 実装解釈、親追認事項): 17→18 key。env 契約の同一性 fingerprint を
    # protocol へ焼き込み cross-field pin する (契約 env と protocol env の乖離を開始前に拒否)。
    "contract_sha256",
})
_FREEZE_RECORD_KEYS = frozenset({"path", "sha256"})

# 承認済み標本設計の凍結数値 (§9 承認状態 2026-07-18)。validate_protocol が完全一致で pin する
# (別実験への変質を開始前に拒否, β-1)。値の単一源は campaign.s8b_approved (C4-3): ここには
# literal を残さず束縛のみ (builder と validate_protocol が同一定義を参照する)。
_APPROVED_N_SESSIONS = s8b_approved.APPROVED_N_SESSIONS
_APPROVED_REPS = s8b_approved.APPROVED_REPS
_APPROVED_RETRY_SLOTS = s8b_approved.APPROVED_RETRY_SLOTS
_APPROVED_SESSION_CV_MAX = s8b_approved.APPROVED_SESSION_CV_MAX
_APPROVED_CELL_CV_MAX = s8b_approved.APPROVED_CELL_CV_MAX
_APPROVED_SCALE_ADEQUACY = s8b_approved.APPROVED_SCALE_ADEQUACY
# 閉じた除外理由表の固定順 (stats が正本)。protocol は完全一致 (固定順) を要求する。
_APPROVED_REASONS = list(s8b_approved.APPROVED_REASONS)

# driver が観測から分類する excluded_reason コード (stats の閉じた表と一致)。
_REASON_COMPETING = "competing_process"          # preflight/post probe の競合
_REASON_LAUNCH = "launch_failure"                # プロセス起動失敗 (全 rep 実行不能)


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
    """バイナリ内容の full sha256 (provenance snapshot; truncate しない)。"""
    try:
        return buildcache.full_sha256(path)
    except buildcache.BinaryDigestError as exc:
        raise FloorCampaignError(str(exc)) from exc


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


def _non_empty_str(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FloorCampaignError(f"protocol.{field} が空でない文字列でない")
    return value


def _pinned(value, expected, *, field: str):
    """承認凍結値との完全一致を要求する (別実験への変質を開始前に拒否, β-1)。"""
    if value != expected or type(value) is not type(expected):
        raise FloorCampaignError(
            f"protocol.{field} が承認凍結値と不一致 (受領 {value!r} != 承認 {expected!r})"
        )
    return value


def validate_protocol(document: Mapping) -> dict:
    """protocol の必須 key・型・整合を strict に検査し、正規化 dict を返す (fail-closed)。

    未知 key・欠落・型不正はすべて拒否する。数値の既定値はコードに持たない (入力必須)。
    ``formula`` は ``s8b_floor_stats.FORMULA_ID`` (v2) と一致検査する (式の版束縛)。承認済み標本
    設計の凍結数値 (n_sessions=8 / reps=5 / retry_slots=2 / 閾値 3 種 / 除外理由 4 行固定順) は
    完全一致で pin する (β-1)。承認凍結値の単一源は ``campaign.s8b_approved`` (C4-3)。

    ``contract_sha256`` は §5-v の親追認事項 (F4 の実装解釈、schema version bump ではなく凍結前の
    17→18 key 追加)。``env_contract.lookup(env_tag).contract_sha256`` と完全一致で cross-field pin
    し、未登録 env_tag は fail-closed で拒否する (契約 env と protocol env の乖離を開始前に止める)。
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
        raise FloorCampaignError(
            f"protocol.schema が {PROTOCOL_SCHEMA} でない (v1 の交差受理を拒否)"
        )
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
    # §5-v: contract_sha256 を env 契約から cross-field pin する (親追認事項)。env_tag が
    # env 契約に未登録なら fail-closed (曖昧な fallback なし)。
    contract_sha256 = _non_empty_str(document["contract_sha256"], field="contract_sha256")
    try:
        _contract = _env_contract.lookup(env_tag)
    except _env_contract.EnvContractError as exc:
        raise FloorCampaignError(f"protocol.env_tag が env 契約に未登録: {exc}") from exc
    if contract_sha256 != _contract.contract_sha256:
        raise FloorCampaignError(
            f"protocol.contract_sha256 が env_contract.lookup({env_tag!r}).contract_sha256 と不一致"
        )
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

    # 承認凍結値の完全一致 pin (β-1)。n_sessions/reps/retry_slots は型と値、閾値 3 種は decimal
    # 文字列として完全一致。
    n_sessions = _pinned(document["n_sessions"], _APPROVED_N_SESSIONS, field="n_sessions")
    reps = _pinned(document["reps"], _APPROVED_REPS, field="reps")
    retry_slots_per_cell = _pinned(
        document["retry_slots_per_cell"], _APPROVED_RETRY_SLOTS, field="retry_slots_per_cell",
    )
    session_cv_max = _pinned(
        document["session_cv_max"], _APPROVED_SESSION_CV_MAX, field="session_cv_max",
    )
    cell_cv_max = _pinned(
        document["cell_cv_max"], _APPROVED_CELL_CV_MAX, field="cell_cv_max",
    )
    scale_adequacy_rel_tolerance = _pinned(
        document["scale_adequacy_rel_tolerance"], _APPROVED_SCALE_ADEQUACY,
        field="scale_adequacy_rel_tolerance",
    )

    extime_s = _pos_int(document["extime_s"], field="extime_s")

    wired_min_rel_floor = document["wired_min_rel_floor"]
    if (isinstance(wired_min_rel_floor, bool)
            or not isinstance(wired_min_rel_floor, (int, float))
            or not math.isfinite(float(wired_min_rel_floor))
            or not (0.0 < float(wired_min_rel_floor) <= 1.0)):
        raise FloorCampaignError("protocol.wired_min_rel_floor が (0,1] の有限数でない")
    wired_min_rel_floor = float(wired_min_rel_floor)

    reasons_raw = document["allowed_excluded_reasons"]
    if reasons_raw != _APPROVED_REASONS:
        # 完全一致 (固定順) を要求する。欠落・余分・並べ替えを開始前に拒否 (β-1)。
        raise FloorCampaignError(
            f"protocol.allowed_excluded_reasons が承認凍結 4 行 (固定順) と不一致: "
            f"受領 {reasons_raw!r}"
        )

    return {
        "schema": PROTOCOL_SCHEMA,
        "formula": formula,
        "env_tag": env_tag,
        "ccbench_pin": ccbench_pin,
        "freeze": {"path": freeze_path, "sha256": freeze_sha},
        "stock_configuration": stock_configuration,
        "n_sessions": n_sessions,
        "reps": reps,
        "master_seed": master_seed,
        "schedule_algorithm": SCHEDULE_ALGORITHM,
        "extime_s": extime_s,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": retry_slots_per_cell,
        "session_cv_max": session_cv_max,
        "cell_cv_max": cell_cv_max,
        "scale_adequacy_rel_tolerance": scale_adequacy_rel_tolerance,
        "allowed_excluded_reasons": list(_APPROVED_REASONS),
        "contract_sha256": contract_sha256,
    }


# --------------------------------------------------------------------------- #
# protocol builder + writer (承認定数から機械組立て、C4-4/C4-7)                 #
#                                                                              #
# 凍結手順 (ユーザー): (1) master_seed / env_tag を確定 → (2) build_protocol_document #
# で組立て (承認 pin は s8b_approved 単一源から焼く) → (3) write_protocol_document で   #
# 明示出力先へ書き出し → (4) ユーザーが commit する (AI-Agent: none)。実凍結 (実 repo の #
# output/s8b-freeze/ への書込み) は AI が行わずユーザー手順で行う。                     #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class BuiltProtocol:
    """組立て済み protocol (validate_protocol 通過済み) と canonical bytes/sha256。"""

    document: dict
    canonical_bytes: bytes
    sha256: str


def _ccbench_gitlink(root: Path) -> str:
    """``external/ccbench`` の HEAD gitlink (40 hex commit) を実測する (fail-closed)。"""
    try:
        completed = subprocess.run(
            ["git", "ls-tree", "HEAD", "external/ccbench"],
            cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        out = completed.stdout.decode("utf-8", "strict")
    except (OSError, subprocess.CalledProcessError, UnicodeError) as exc:
        raise FloorCampaignError(f"ccbench gitlink を実測できない: {exc}") from exc
    # 期待形式: "160000 commit <40hex>\texternal/ccbench"
    fields = out.split()
    if len(fields) < 3 or fields[0] != "160000" or fields[1] != "commit":
        raise FloorCampaignError(f"external/ccbench が gitlink (submodule) でない: {out!r}")
    sha = fields[2]
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise FloorCampaignError(f"ccbench gitlink が 40 桁 hex でない: {sha!r}")
    return sha


def build_protocol_document(master_seed, env_tag, *, stock_configuration,
                            extime_s, wired_min_rel_floor, root=ROOT) -> BuiltProtocol:
    """承認定数を単一源から機械組立てし ``validate_protocol`` を通した protocol を返す (C4-7)。

    引数 ``master_seed`` / ``env_tag`` / ``stock_configuration`` / ``extime_s`` /
    ``wired_min_rel_floor`` は validate_protocol が pin しない自由値であり、**凍結時に
    ユーザーが確定する欄**である。既定値を持たない (値の発明・追認を禁止する — 欠落は
    TypeError で落ちる)。

    承認 pin 値 (n_sessions=8 等・閾値・除外理由)・v1 freeze {path, sha256}・ccbench full
    commit sha は ``campaign.s8b_approved`` を単一源として焼く。**現在値の追認を許さない**
    (C4-4): 実 v1 bytes が ``APPROVED_FREEZE_SHA256`` と、実 gitlink が ``CCBENCH_FULL_SHA``
    と一致することを組立て前に検証する。``contract_sha256`` は ``env_tag`` から導出する
    (validate_protocol が cross-field 照合する、§5-v)。canonical bytes + sha256 も返す。

    凍結手順: master_seed / env_tag を確定 → 本 builder → write_protocol_document で明示
    出力先へ → ユーザーが commit (AI-Agent: none)。
    """
    root = Path(root)
    if not isinstance(master_seed, str) or not master_seed:
        raise FloorCampaignError("build_protocol_document: master_seed が空でない str でない")
    if not isinstance(env_tag, str) or not env_tag:
        raise FloorCampaignError("build_protocol_document: env_tag が空でない str でない")

    # 実 v1 bytes を承認定数と照合してから焼く (現在値の追認を拒否、C4-4)。
    v1_path = root / s8b_approved.APPROVED_FREEZE_PATH
    try:
        actual_v1 = hashlib.sha256(v1_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FloorCampaignError(f"v1 freeze を読めない: {v1_path}: {exc}") from exc
    if actual_v1 != s8b_approved.APPROVED_FREEZE_SHA256:
        raise FloorCampaignError(
            "v1 freeze bytes が承認定数と不一致 (現在値の追認を拒否): "
            f"実 {actual_v1} != 承認 {s8b_approved.APPROVED_FREEZE_SHA256}"
        )

    # 実 gitlink を承認定数と照合してから焼く (現在値の追認を拒否、C4-4)。
    actual_link = _ccbench_gitlink(root)
    if actual_link != s8b_approved.CCBENCH_FULL_SHA:
        raise FloorCampaignError(
            "ccbench gitlink が承認定数と不一致 (現在値の追認を拒否): "
            f"実 {actual_link} != 承認 {s8b_approved.CCBENCH_FULL_SHA}"
        )

    # contract_sha256 は env_tag から導出 (validate_protocol が cross-field 検査する)。
    try:
        contract = _env_contract.lookup(env_tag)
    except _env_contract.EnvContractError as exc:
        raise FloorCampaignError(f"env_tag が env 契約に未登録: {exc}") from exc

    document = {
        "schema": PROTOCOL_SCHEMA,
        "formula": s8b_floor_stats.FORMULA_ID,
        "env_tag": env_tag,
        "ccbench_pin": s8b_approved.CCBENCH_FULL_SHA,
        "freeze": {
            "path": s8b_approved.APPROVED_FREEZE_PATH,
            "sha256": s8b_approved.APPROVED_FREEZE_SHA256,
        },
        "stock_configuration": stock_configuration,
        "n_sessions": s8b_approved.APPROVED_N_SESSIONS,
        "reps": s8b_approved.APPROVED_REPS,
        "master_seed": master_seed,
        "schedule_algorithm": SCHEDULE_ALGORITHM,
        "extime_s": extime_s,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": s8b_approved.APPROVED_RETRY_SLOTS,
        "session_cv_max": s8b_approved.APPROVED_SESSION_CV_MAX,
        "cell_cv_max": s8b_approved.APPROVED_CELL_CV_MAX,
        "scale_adequacy_rel_tolerance": s8b_approved.APPROVED_SCALE_ADEQUACY,
        "allowed_excluded_reasons": list(s8b_approved.APPROVED_REASONS),
        "contract_sha256": contract.contract_sha256,
    }
    # validate_protocol を単一の受理ゲートに通す (builder 自身では判定を持たない)。
    normalized = validate_protocol(document)
    canonical = _canonical_bytes(normalized)
    return BuiltProtocol(
        document=normalized,
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


def _guarded_freeze_dirs(root: Path) -> tuple:
    """writer が書込みを拒否する実凍結領域の解決済み path (存在しなくても解決)。"""
    dirs = []
    for rel in ("output/s8b-freeze", "output/env"):
        dirs.append((root / rel).resolve())
    return tuple(dirs)


def write_protocol_document(path, built: "BuiltProtocol", *, root=ROOT) -> Path:
    """``built`` を create-only で書き出す。**default path なし (明示出力先必須)**。

    出力先が実 repo の凍結領域 (``output/s8b-freeze/`` ・ ``output/env/``) 配下なら拒否する
    (テスト誤爆の第二防壁 — 実凍結はユーザー手順で行い、AI-Agent: none で commit する)。
    既存 path も拒否する (create-only)。ファイル bytes は canonical bytes と一致し、その
    sha256 は ``built.sha256`` (= protocol_sha256 の pre-image) に等しい。
    """
    if not isinstance(built, BuiltProtocol):
        raise FloorCampaignError("write_protocol_document: BuiltProtocol でない")
    destination = Path(path)
    resolved_parent = destination.parent.resolve()
    for guarded in _guarded_freeze_dirs(Path(root)):
        if resolved_parent == guarded or guarded in resolved_parent.parents:
            raise FloorCampaignError(
                "実 repo の凍結領域配下への書込みは拒否 (実凍結はユーザー手順): "
                f"{destination} ⊂ {guarded}"
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(destination.parent),
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as stream:
            tmp = Path(stream.name)
            stream.write(built.canonical_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(tmp, destination)
        except FileExistsError as exc:
            raise FloorCampaignError(
                f"protocol document が既に存在する (create-only): {destination}"
            ) from exc
        dir_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as exc:
        if isinstance(exc, FileExistsError):  # pragma: no cover - 上で翻訳済み
            raise FloorCampaignError(
                f"protocol document が既に存在する (create-only): {destination}"
            ) from exc
        raise FloorCampaignError(f"protocol document を書けない: {destination}: {exc}") from exc
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return destination


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
# schedule v2 (round 単位 seed 置換, 純粋関数)                                  #
# --------------------------------------------------------------------------- #

def _round_seed(master_seed: str, round_no: int) -> int:
    """round 種: seed = int.from_bytes(sha256(f"{master_seed}/{r}").digest()[:8], big)。"""
    payload = f"{master_seed}/{round_no}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def build_schedule(*, cells: list[dict], master_seed: str, n_sessions: int) -> list[dict]:
    """round r=1..n_sessions ごとに 12 セル (cell_id sort・一意) を seed 置換した session 列。

    契約 (β-3): 各 round は正規化済み (sort 済み・重複なし) の全 cell_id の完全置換で、
    各セルは round ごとにちょうど 1 回現れる。seq は 0..(n_sessions×|cells|-1) の通し番号。
    エントリは {seq, round, cell_id} のみ (96 スロット一括置換ではなく round 構造を保つ)。入力
    順に依存しないよう cell_id を sort し一意検査する。
    """
    if not isinstance(n_sessions, int) or isinstance(n_sessions, bool) or n_sessions <= 0:
        raise FloorCampaignError("build_schedule: n_sessions が正整数でない")
    cell_ids = sorted(cell["cell_id"] for cell in cells)
    if len(set(cell_ids)) != len(cell_ids):
        raise FloorCampaignError("build_schedule: cell_id が重複している")
    if not cell_ids:
        raise FloorCampaignError("build_schedule: cells が空")
    rows: list[dict] = []
    for round_no in range(1, n_sessions + 1):
        permuted = list(cell_ids)
        random.Random(_round_seed(master_seed, round_no)).shuffle(permuted)
        for cell_id in permuted:
            rows.append({"seq": len(rows), "round": round_no, "cell_id": cell_id})
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
                # 危険なので拒否する (都合のよい session 再現を許さない)。
                raise FloorCampaignError(
                    f"journal 行 {lineno} が壊れている (truncated crash の疑い): {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise FloorCampaignError(f"journal 行 {lineno} が object でない")
            records.append(value)
    return records


# --------------------------------------------------------------------------- #
# strict single-tenant probe (規律4, runner の共有分類器を消費)                 #
# --------------------------------------------------------------------------- #

_PROBE_ARGV = ["pgrep", "-af", r"ycsb_.*\.exe"]


def _default_probe_fn() -> tuple[int, str, str]:
    """pgrep -af 'ycsb_.*\\.exe' を 1 回叩き (rc, stdout, stderr) を返す (OSError は投げる)。"""
    result = subprocess.run(_PROBE_ARGV, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def strict_probe(probe_fn: Callable[[], tuple[int, str, str]]) -> dict:
    """計測前後の臨界区間 probe。競合検知は lag-free の確定信号 (規律4)。

    分類は runner の共有 `classify_competing_probe` に委譲する (C4-5: 二重実装排除)。
    rc==1+空 → 競合なし / rc==0+PID 行 → 自 PID (`os.getpid()`) を除いて残れば競合 /
    rc==1+付随出力・rc==0+空・rc>1・負値・**rc==1+stderr 非空 (BusyBox 罠)** →
    `CompetingBenchProbeError` を CampaignAbort へ翻訳 (fail-closed)。probe_fn は
    (rc, stdout, stderr) を返す注入シーム (テスト用) で、stderr も分類器へ実値で渡す
    — runner の `competing_bench_pids` と全く同じ strict 契約を通す (C4-5 統一の要:
    floor だけが BusyBox ガードを死なせない)。除外は自 PID のみ (B-2 裁定済み —
    自分の子孫も競合として検出する。worklog 2026-07-18 (6) /
    docs/phase3-8b-descriptor-design.md §9)。生出力は戻り値に含め、呼び手が journal に残す。
    """
    try:
        rc, stdout, stderr = probe_fn()
    except OSError as exc:
        raise CampaignAbort(f"strict probe が OSError: {exc}") from exc
    try:
        competing = classify_competing_probe(rc, stdout, stderr, _PROBE_ARGV)
    except CompetingBenchProbeError as exc:
        raise CampaignAbort(
            f"strict probe が競合の有無を確定できない (fail-closed): {exc}") from exc
    return {"rc": rc, "stdout": stdout, "stderr": stderr, "competing": competing}


# --------------------------------------------------------------------------- #
# host / process provenance (G12 capture; γ-5/γ-12: 絶対 monotonic を持たない)  #
# --------------------------------------------------------------------------- #

def _boot_id() -> Optional[str]:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip() or None
    except (OSError, UnicodeError):
        return None


def _cpuset() -> Optional[str]:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("Cpus_allowed_list:"):
                return line.split(":", 1)[1].strip() or None
    except (OSError, UnicodeError):
        return None
    return None


def _proc_starttime() -> Optional[int]:
    """/proc/self/stat の starttime (field 22)。process identity の一部 (γ-5)。"""
    try:
        data = Path("/proc/self/stat").read_text(encoding="utf-8")
        after = data.rsplit(")", 1)[1].split()  # comm を括弧ごと除いた残り (field 3..)
        return int(after[19])
    except (OSError, UnicodeError, IndexError, ValueError):
        return None


def _host_provenance(now_fn: Callable[[], dt.datetime]) -> dict:
    """G12 capture: hostname / boot_id / job_id / cpuset / UTC。絶対 monotonic は持たない。"""
    return {
        "hostname": socket.gethostname(),
        "boot_id": _boot_id(),
        "job_id": os.environ.get("PBS_JOBID") or os.environ.get("SLURM_JOB_ID") or None,
        "cpuset": _cpuset(),
        "utc": now_fn().isoformat(),
    }


def _process_identity() -> dict:
    """process 同一性 (γ-5): pid + starttime + execution_uuid。resume 越しの識別用。"""
    return {
        "pid": os.getpid(),
        "starttime": _proc_starttime(),
        "execution_uuid": uuid.uuid4().hex,
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


def _project_scalepoint(scale_point) -> dict:
    """ScalePoint を SessionRecord の計測フィールドへ射影する (throughputs / exec_failures)。"""
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
    FloorCampaignError へ因果付き変換する。"""
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
    """全 12 セルを実行開始前に実体化・ビルドし、binary path と full sha256 を返す。"""
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
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
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
# launch certificate (C2-2) — official 開始時の clean-scan 証明                 #
#                                                                             #
# 【状態: 未結線 scaffolding】以下 3 関数は building block として実装・単体検証済み   #
# だが run_campaign には**まだ結線していない** (下記 official mode の無条件拒否に    #
# より本 wave では発行経路が存在しない)。official floor を有効化する floor 実走 wave  #
# で「clean_scan_digest → build_launch_certificate → issue_launch_certificate    #
# → campaign-start record への cert sha256 束縛 → v2 closure の lineage 照合」を     #
# 結線することが C2-2 mitigation を発火させる**阻止的前提条件**。それまで verifier      #
# 側 (s8b_ratified_freeze.launch_validate) は certificate lineage を照合しない —      #
# certificate 以前に消した痕跡は不可視の open residual (§5-viii)。                   #
# --------------------------------------------------------------------------- #

def clean_scan_digest(root: Path) -> str:
    """発行時点の clean scan を証明する: holdout hit 0 件 + 列挙 digest を返す (fail-closed)。

    search_repository を実行し、いずれの holdout にも conjunction hit が無いこと (未申告
    先行測定が既に存在しないこと) を確認し、列挙集合の digest を返す。hit があれば
    FloorCampaignError (clean でない = certificate を発行できない)。"""
    report = _holdout_freeze.search_repository(Path(root))
    for name, result in report["holdouts"].items():
        hits = result.get("conjunction_hits")
        if hits:
            raise FloorCampaignError(
                f"launch certificate: holdout {name} に既存 hit {hits} (clean scan でない)"
            )
    files = _holdout_freeze.enumerate_repository_files(Path(root))
    return hashlib.sha256("\n".join(files).encode("utf-8")).hexdigest()


def build_launch_certificate(*, v1_freeze_sha256: str, clean_digest: str,
                             protocol_sha256: str, started_utc: str,
                             campaign_run_id: str) -> dict:
    """official floor 開始時の launch certificate を組み立てる (純粋、C2-2)。

    {v1_freeze_sha256, clean_scan_digest, protocol_sha256, started_utc, campaign_run_id}
    を束ねる。certificate 自身の bytes sha256 を campaign-start record が束縛し、v2 closure は
    この certificate 起点の lineage から導出する (certificate 以前に削除された痕跡は原理的に
    検出不能 — §5-viii の限界)。"""
    return {
        "schema": LAUNCH_CERT_SCHEMA,
        "v1_freeze_sha256": v1_freeze_sha256,
        "clean_scan_digest": clean_digest,
        "protocol_sha256": protocol_sha256,
        "started_utc": started_utc,
        "campaign_run_id": campaign_run_id,
    }


def issue_launch_certificate(cert_path: Path, certificate: Mapping) -> str:
    """certificate を create-only で発行し、その bytes sha256 (journal 束縛値) を返す。"""
    cert_bytes = _write_create_only_json(Path(cert_path), certificate)
    return hashlib.sha256(cert_bytes).hexdigest()


# --------------------------------------------------------------------------- #
# content-addressed binary store (C3-7) — 計測 bytes を hash 名で永続化         #
# --------------------------------------------------------------------------- #

def store_binaries(built: dict, store_root: Path, *, out_root: Path) -> None:
    """計測に使う binary bytes を store_root/<sha256> へ create-only 複製する (C3-7)。

    既に同 hash の store が在れば内容 hash を照合するだけ (冪等)。各 built rec に out_root
    相対の store_path を書き込む。oracle 側の消費 (run marker 前の存在+hash 検査) は W4。"""
    store_root = Path(store_root)
    store_root.mkdir(parents=True, exist_ok=True)
    out_root = Path(out_root)
    for cell_id in sorted(built):
        rec = built[cell_id]
        sha = rec["binary_sha256"]
        src = Path(rec["binary"])
        dest = store_root / sha
        if dest.exists():
            actual = _full_sha256(dest)
            if actual != sha:
                raise FloorCampaignError(
                    f"binary store 破損: {dest} の sha256={actual} != {sha}"
                )
        else:
            data = src.read_bytes()
            if hashlib.sha256(data).hexdigest() != sha:
                raise FloorCampaignError(
                    f"store 対象 binary の sha256 が build 記録と不一致: {src}"
                )
            tmp = store_root / f".{sha}.tmp.{os.getpid()}"
            with open(tmp, "xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(tmp, dest)
            except FileExistsError:
                pass  # 並走で先に作られた (content-addressed なので同一 bytes)
            finally:
                tmp.unlink(missing_ok=True)
            actual = _full_sha256(dest)
            if actual != sha:
                raise FloorCampaignError(f"store 書込後 hash 不一致: {dest} sha256={actual}")
        try:
            rec["store_path"] = str(dest.relative_to(out_root))
        except ValueError:
            rec["store_path"] = str(dest)


def _verify_resume_store(built: Mapping, out_root: Path) -> None:
    """resume: 記録済み store_path が存在し、その bytes sha256 が binary_sha256 と一致する。"""
    out_root = Path(out_root)
    for cell_id in sorted(built):
        rec = built[cell_id]
        store_path = rec.get("store_path")
        sha = rec.get("binary_sha256")
        if not isinstance(store_path, str) or not store_path:
            # v2 の store_binaries は常に store_path を書くため、欠落は改竄か
            # store 前 manifest の混入 — 正当な消費者のない緩和を置かない (fail-closed)。
            raise FloorCampaignError(f"resume: store_path 欠落: {cell_id}")
        candidate = Path(store_path)
        if not candidate.is_absolute():
            candidate = out_root / store_path
        if not candidate.is_file():
            raise FloorCampaignError(f"resume: store 欠落: {store_path}")
        actual = _full_sha256(candidate)
        if actual != sha:
            raise FloorCampaignError(
                f"resume: store bytes sha256 が binary_sha256 と不一致 (store={actual} rec={sha})"
            )


# --------------------------------------------------------------------------- #
# session 実行エンジン (fresh/resume 共通)                                      #
# --------------------------------------------------------------------------- #

class _Runner:
    """schedule を直列・単一テナントで消化する実行エンジン (fresh/resume 共通)。

    臨界区間は session ごとに ``session-start (=authorization) → probe → measure → post-probe →
    session (end)`` を journal へ即時記録する。crash した session は start だけが残り、resume では
    **terminal (再実行しない)** 扱いにする (forward-only)。retry の枠消費は authorization
    (session-start) の fsync 時点で確定し、(cell_id, retry_ordinal) は resume を跨いで再発行しない
    (β-5)。retry は失敗が起きた round の末尾で schedule 順に消化する (β-4)。
    """

    def __init__(self, *, protocol, cells, cell_by_id, binaries, schedule,
                 journal_path, measure_fn, probe_fn, sleep_fn, monotonic_fn, now_fn,
                 protocol_sha256, freeze_sha256, manifest_sha256,
                 execution_receipt=None):
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
        self.protocol_sha256 = protocol_sha256
        self.freeze_sha256 = freeze_sha256
        self.manifest_sha256 = manifest_sha256
        # C3-10: 共有 execution guard の receipt (campaign-start journal に記録)。
        self.execution_receipt = execution_receipt
        self.reps = protocol["reps"]
        self.session_cv_max = protocol["session_cv_max"]
        self.retry_slots = protocol["retry_slots_per_cell"]
        self.allowed_reasons = set(protocol["allowed_excluded_reasons"])
        self.records = _read_journal(journal_path)  # fresh なら []

    # --- journal I/O ----------------------------------------------------- #

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

    # --- attempt registry / retry 予算 (fsync 時点で消費) ----------------- #

    def _authorized_retry_ordinals(self, cell_id: str) -> set:
        """当該セルで authorization (session-start) 済みの retry_ordinal 集合。crash した
        authorization も含む (枠消費は session-start の fsync 時点, β-5)。"""
        return {r.get("retry_ordinal") for r in self.records
                if r.get("event") == "session-start" and r.get("kind") == "retry"
                and r.get("cell_id") == cell_id and r.get("retry_ordinal") is not None}

    def _authorized_retries(self, cell_id: str) -> int:
        return len(self._authorized_retry_ordinals(cell_id))

    def _next_retry_ordinal(self, cell_id: str) -> int:
        used = self._authorized_retry_ordinals(cell_id)
        return (max(used) + 1) if used else 1

    def _started_seqs(self) -> set:
        return {r["seq"] for r in self.records if r.get("event") == "session-start"}

    def _next_retry_seq(self) -> int:
        seqs = [r["seq"] for r in self.records
                if r.get("event") in {"session", "session-start"} and "seq" in r]
        base = len(self.schedule) - 1
        return max(seqs + [base]) + 1

    def _completed_rounds(self) -> set:
        return {r["round"] for r in self.records if r.get("event") == "round-complete"}

    # --- round / cell の状態問い合わせ (journal から再構成) --------------- #

    def _round_rows(self, round_no: int) -> list[dict]:
        return [row for row in self.schedule if row["round"] == round_no]

    def _planned_seq(self, round_no: int, cell_id: str) -> Optional[int]:
        for row in self.schedule:
            if row["round"] == round_no and row["cell_id"] == cell_id:
                return row["seq"]
        return None

    def _planned_attempt_id(self, round_no: int, cell_id: str) -> Optional[str]:
        seq = self._planned_seq(round_no, cell_id)
        return None if seq is None else _attempt_id(cell_id, "planned", seq, None)

    def _round_failed_cells(self, round_no: int) -> list[str]:
        """round 内で planned session が完了して無効だったセルを schedule 順に。

        crash (start だけで完了記録なし) は forward-only の terminal であり retry を発火しない
        (完了 invalid のみが retry の trigger)。各セルは round ごと 1 回なので重複しない。
        """
        order = [row["cell_id"] for row in self._round_rows(round_no)]
        failed: list[str] = []
        for cell_id in order:
            planned = [r for r in self.records
                       if r.get("event") == "session" and r.get("kind") == "planned"
                       and r.get("round") == round_no and r.get("cell_id") == cell_id]
            if planned and not planned[0].get("valid"):
                failed.append(cell_id)
        return failed

    def _cell_round_has_valid(self, cell_id: str, round_no: int) -> bool:
        return any(r.get("event") == "session" and r.get("cell_id") == cell_id
                   and r.get("round") == round_no and r.get("valid")
                   for r in self.records)

    # --- 1 session 実行 (precedence 固定, β-7) ---------------------------- #

    def _run_session(self, *, seq: int, round_no: int, cell_id: str, kind: str,
                     retry_ordinal: Optional[int], trigger: Optional[str]) -> dict:
        attempt_id = _attempt_id(cell_id, kind, seq, retry_ordinal)
        # authorization record: retry 枠はこの fsync 時点で消費される (crash しても再発行しない)。
        self._emit({
            "event": "session-start", "seq": seq, "kind": kind, "cell_id": cell_id,
            "round": round_no, "retry_ordinal": retry_ordinal, "attempt_id": attempt_id,
            "trigger": trigger, "started_iso": self.now_fn().isoformat(),
        })
        start_mono = self.monotonic_fn()
        cell = self.cell_by_id[cell_id]
        binary = self.binaries[cell_id]["binary"]

        # binary receipt (C3-6): 実測直前に binary bytes を再 hash し build 記録と照合する。
        # 記録 (build 時 hash) と実測直前 hash が食い違えば差し替えの疑いで CampaignAbort。
        recorded_bin_sha = self.binaries[cell_id]["binary_sha256"]
        measured_bin_sha = _full_sha256(Path(binary))
        if measured_bin_sha != recorded_bin_sha:
            raise CampaignAbort(
                f"binary receipt 不一致: cell={cell_id} 記録={recorded_bin_sha} "
                f"実測直前={measured_bin_sha} (計測 bytes 差し替えの疑い)"
            )

        # pre-probe: rc>1/OSError/parse 不能 → CampaignAbort。競合列挙 → competing_process。
        probe_before = strict_probe(self.probe_fn)
        if probe_before["competing"]:
            return self._finish_session(
                seq=seq, round_no=round_no, cell_id=cell_id, kind=kind,
                retry_ordinal=retry_ordinal, attempt_id=attempt_id, trigger=trigger,
                throughputs=[], exec_failures=0, excluded_reason=_REASON_COMPETING,
                session_cv=None, duration_s=self._elapsed(start_mono),
                probe_before=probe_before, probe_after=None, run_cmd=None,
                notes=["preflight probe 競合で計測をスキップ"],
                binary_sha256_at_measure=measured_bin_sha,
            )

        # measure を試みる。例外 (全 rep 起動不能) でも post-probe は finally 相当で必ず実行する。
        measure_error: Optional[BaseException] = None
        scale_point = None
        try:
            scale_point = self.measure_fn(
                binary, cell["records"], cell["threads"], cell["workload"],
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            measure_error = exc

        probe_after = strict_probe(self.probe_fn)  # 検査不能 → CampaignAbort (finally 相当)

        if scale_point is not None:
            projection = _project_scalepoint(scale_point)
            throughputs = projection["throughputs"]
            exec_failures = projection["exec_failures"]
            run_cmd = getattr(scale_point, "run_cmd", None)
            notes = list(getattr(scale_point, "notes", []) or [])
        else:
            throughputs = []
            exec_failures = self.reps
            run_cmd = None
            notes = [f"measure 失敗: {type(measure_error).__name__}: "
                     f"{str(measure_error)[:200]}"]

        # 生値から表示 CV / 必然理由を導出 (stats の単一純関数, α-8)。理由の precedence 決定に使う。
        session_cv: Optional[float] = None
        derived_reason: Optional[str] = None
        if scale_point is not None:
            try:
                assessment = s8b_floor_stats.assess_session(
                    throughputs, reps=self.reps, session_cv_max=self.session_cv_max,
                )
            except s8b_floor_stats.FloorStatsError as exc:
                raise CampaignAbort(f"assess_session 内部不変条件破れ: {exc}") from exc
            session_cv = assessment.cv
            derived_reason = assessment.required_reason

        # precedence (β-7): post-probe 競合 → competing / 全 rep 起動不能 → launch /
        # 部分・非有限 → partial / 完全値 CV 超過 → performance / その他 valid。
        if probe_after["competing"]:
            excluded_reason: Optional[str] = _REASON_COMPETING
        elif measure_error is not None:
            excluded_reason = _REASON_LAUNCH
        elif exec_failures >= self.reps:
            excluded_reason = _REASON_LAUNCH  # 全 rep 起動不能 (β-7)
        elif exec_failures > 0 and derived_reason is None:
            # 完全有限ベクトル + 起動失敗 note の矛盾状態。session は stats 側で必ず
            # 無効になる (exec_failures != 0) ため、閉表の理由なしで invalid になる
            # 行を作らない (レビュー所見)。
            excluded_reason = _REASON_LAUNCH
        else:
            excluded_reason = derived_reason  # None / partial / performance

        return self._finish_session(
            seq=seq, round_no=round_no, cell_id=cell_id, kind=kind,
            retry_ordinal=retry_ordinal, attempt_id=attempt_id, trigger=trigger,
            throughputs=throughputs, exec_failures=exec_failures,
            excluded_reason=excluded_reason, session_cv=session_cv,
            duration_s=self._elapsed(start_mono), probe_before=probe_before,
            probe_after=probe_after, run_cmd=run_cmd, notes=notes,
            binary_sha256_at_measure=measured_bin_sha,
        )

    def _elapsed(self, start_mono: float) -> float:
        """同一 process 内の monotonic 差 (γ-12: 絶対 monotonic は永続化しない)。"""
        return float(self.monotonic_fn() - start_mono)

    def _finish_session(self, *, seq, round_no, cell_id, kind, retry_ordinal, attempt_id,
                        trigger, throughputs, exec_failures, excluded_reason, session_cv,
                        duration_s, probe_before, probe_after, run_cmd, notes,
                        binary_sha256_at_measure=None) -> dict:
        cell = self.cell_by_id[cell_id]
        reason = self._check_reason(excluded_reason) if excluded_reason is not None else None
        rec = s8b_floor_stats.SessionRecord(
            cell_id=cell_id, holdout_id=cell["holdout_id"],
            configuration_id=cell["configuration_id"], seq=seq,
            throughputs=tuple(throughputs), reps_expected=self.reps,
            exec_failures=exec_failures, excluded_reason=reason, retry=(kind == "retry"),
        )
        median = s8b_floor_stats.session_median(
            rec, reps=self.reps, session_cv_max=self.session_cv_max,
        )
        valid = median is not None
        record = {
            "event": "session", "kind": kind, "seq": seq, "round": round_no,
            "retry_ordinal": retry_ordinal, "attempt_id": attempt_id, "trigger": trigger,
            "cell_id": cell_id, "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"], "threads": cell["threads"],
            "workload": cell["workload"],
            # --- SessionRecord と同じ key (verify_floor_artifact が再構成する) ---
            "throughputs": list(throughputs), "reps_expected": self.reps,
            "exec_failures": exec_failures, "excluded_reason": reason,
            "retry": (kind == "retry"),
            # --- driver の付帯情報 (verify は無視する) ---
            "session_median": median, "valid": valid, "session_cv": session_cv,
            "duration_s": duration_s, "run_cmd": run_cmd, "notes": list(notes or []),
            "probe_before": probe_before, "probe_after": probe_after,
            # binary receipt (C3-6): 実測直前に再計算した binary bytes の full sha256。
            "binary_sha256_at_measure": binary_sha256_at_measure,
        }
        self._emit(record)
        return record

    # --- retry (round 末尾で失敗セルを schedule 順に消化, β-4) ------------ #

    def _retry_round(self, round_no: int) -> None:
        for cell_id in self._round_failed_cells(round_no):
            trigger = self._planned_attempt_id(round_no, cell_id)
            # campaign 通算予算まで、first-authorized-valid で 1 本有効になるまで消化する。
            while (self._authorized_retries(cell_id) < self.retry_slots
                   and not self._cell_round_has_valid(cell_id, round_no)):
                self._run_session(
                    seq=self._next_retry_seq(), round_no=round_no, cell_id=cell_id,
                    kind="retry", retry_ordinal=self._next_retry_ordinal(cell_id),
                    trigger=trigger,
                )

    # --- campaign 実行 --------------------------------------------------- #

    def run(self) -> None:
        fresh = not any(r.get("event") == "campaign-start" for r in self.records)
        if fresh:
            self._emit({
                "event": "campaign-start", "schema": JOURNAL_SCHEMA,
                "protocol_sha256": self.protocol_sha256,
                "freeze_sha256": self.freeze_sha256,
                "manifest_sha256": self.manifest_sha256,
                **_host_provenance(self.now_fn), **_process_identity(),
                # C3-10: 共有 execution guard の receipt (env_tag + contract_sha256 +
                # 実行機 attestation)。report/verifier が env 契約と照合する。
                **({"execution_receipt": self.execution_receipt}
                   if self.execution_receipt is not None else {}),
            })
        else:
            # resume: 新 process の identity を記録する (γ-5)。result には含めない (決定性維持)。
            self._emit({
                "event": "resume-start", **_host_provenance(self.now_fn),
                **_process_identity(),
            })

        started = self._started_seqs()
        completed_rounds = self._completed_rounds()
        started_rounds = {r["round"] for r in self.records
                          if r.get("event") == "round-start"}
        for round_no in sorted({row["round"] for row in self.schedule}):
            if round_no in completed_rounds:
                continue
            if round_no not in started_rounds:
                # resume で round 途中から再入するとき round-start を二重記録しない
                # (レビュー所見: wall_ledger の round 記録が倍加していた)。
                self._emit({"event": "round-start", "round": round_no,
                            "utc": self.now_fn().isoformat()})
            for row in self._round_rows(round_no):
                if row["seq"] in started:
                    continue  # 完了 or crash 済み = 再走しない (forward-only)
                self._run_session(
                    seq=row["seq"], round_no=round_no, cell_id=row["cell_id"],
                    kind="planned", retry_ordinal=None, trigger=None,
                )
            self._retry_round(round_no)
            self._emit({"event": "round-complete", "round": round_no,
                        "utc": self.now_fn().isoformat()})


def _attempt_id(cell_id: str, kind: str, seq: int, retry_ordinal: Optional[int]) -> str:
    if kind == "retry":
        return f"{cell_id}::retry{retry_ordinal}"
    return f"{cell_id}::seq{seq}"


# --------------------------------------------------------------------------- #
# terminal: floor 算出 (s8b_floor_stats) + artifact                            #
# --------------------------------------------------------------------------- #

def _session_records(records: list[dict]) -> list[dict]:
    return [r for r in records if r.get("event") == "session"]


def _journal_expected_binaries(records: list[dict]) -> dict:
    """journal の session receipt から cell_id → binary_sha256_at_measure を集約する (C3-6)。

    verify_floor_artifact の expected_binaries に渡す独立 receipt。同一 cell の複数 session が
    異なる measured hash を持てば差し替えの疑いで fail-closed (実際は _run_session が build 記録と
    食い違いを CampaignAbort するため、完走 campaign では単一値に収束する)。"""
    out: dict = {}
    for rec in _session_records(records):
        cell_id = rec.get("cell_id")
        sha = rec.get("binary_sha256_at_measure")
        if not isinstance(cell_id, str) or not isinstance(sha, str) or len(sha) != 64:
            continue
        prev = out.get(cell_id)
        if prev is not None and prev != sha:
            raise FloorCampaignError(
                f"journal receipt: cell {cell_id} の binary_sha256_at_measure が "
                f"session 間で不一致 ({prev} != {sha})"
            )
        out[cell_id] = sha
    return out


def _cellstats_to_dict(cs) -> dict:
    return {
        "holdout_id": cs.holdout_id,
        "configuration_id": cs.configuration_id,
        "n_valid": cs.n_valid,
        "medians": list(cs.medians),
        "m": cs.m,
        "s": cs.s,
        "valid": cs.valid,
        "cv": cs.cv,
        "notes": list(cs.notes),
    }


def _floors_to_dict(hf) -> dict:
    return {
        "pairs": dict(hf.pairs),           # キーは configuration_id (δ-10)
        "scalar_alt": hf.scalar_alt,
        "scale_ref": hf.scale_ref,
        "diagnostics": hf.diagnostics,     # キーは cell_id
    }


def _expected_protocol(protocol: Mapping, cells: list[dict]) -> dict:
    """verify_floor_artifact に渡す外部 expected_protocol (凍結値) を protocol + cells から組む。"""
    expected_cells: dict[str, list] = {}
    for cell in cells:
        expected_cells.setdefault(cell["holdout_id"], []).append(cell["configuration_id"])
    for holdout_id in expected_cells:
        expected_cells[holdout_id] = sorted(expected_cells[holdout_id])
    return {
        "formula": protocol["formula"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "stock_configuration": protocol["stock_configuration"],
        "wired_min_rel_floor": protocol["wired_min_rel_floor"],
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
        "expected_cells": expected_cells,
    }


def assemble_result(*, protocol, mode, protocol_sha256, freeze_sha256,
                    manifest_sha256, cells, binaries, records) -> dict:
    """journal の生 session から floor artifact (result) を組み立てる (formula v2)。

    cell_stats / holdout_floors は ``s8b_floor_stats`` (formula v2) が正本。artifact の
    ``config`` / ``sessions`` / ``cells`` / ``floors`` は ``verify_floor_artifact`` が生 session
    から再計算して自己申告値 + 外部 expected_protocol と厳密比較する形に合わせる。durations /
    wall_ledger は journal から読むだけの純粋関数なので resume を跨いで決定的 (β-11 の冪等
    finalization が hash 照合に依存する)。
    """
    n_sessions = protocol["n_sessions"]
    reps = protocol["reps"]
    session_cv_max = protocol["session_cv_max"]
    cell_cv_max = protocol["cell_cv_max"]
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
                configuration_id=raw["configuration_id"], seq=int(raw["seq"]),
                throughputs=tuple(raw["throughputs"]),
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
            records_by_cell[cell_id], n_sessions=n_sessions, reps=reps,
            session_cv_max=session_cv_max,
        )
        cell_stats_map[cell_id] = cs
        cells_out[cell_id] = _cellstats_to_dict(cs)

    # holdout 別 floor (s8b_floor_stats.holdout_floors)。pairs キーは configuration_id (δ-10)。
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
            wired_min_rel_floor=wired_min_rel_floor, cell_cv_max=cell_cv_max,
        )
        floors_out[holdout_id] = _floors_to_dict(hf)

    excluded = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "kind": r.get("kind"),
            "retry": r.get("retry"), "round": r.get("round"),
            "excluded_reason": r.get("excluded_reason"),
            "session_cv": r.get("session_cv"),
        }
        for r in session_records if not r.get("valid")
    ]
    # 全 attempt 台帳 (α-14: CV / median / valid / 除外理由を併記, machine_anomaly と分離)。
    attempts = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "kind": r.get("kind"),
            "round": r.get("round"), "retry_ordinal": r.get("retry_ordinal"),
            "valid": r.get("valid"), "excluded_reason": r.get("excluded_reason"),
            "session_cv": r.get("session_cv"), "session_median": r.get("session_median"),
            "duration_s": r.get("duration_s"),
        }
        for r in session_records
    ]
    wall_ledger = [
        dict(r) for r in records
        if r.get("event") in {"campaign-start", "round-start", "round-complete"}
    ]

    return {
        "schema": RESULT_SCHEMA,
        "formula": protocol["formula"],
        "mode": mode,
        # official は F6 裁定まで run_campaign core が無条件拒否するため、結果を
        # 生成できる campaign では恒に False。条件式で書くと「official なら True に
        # なり得る」という誤読を招くので定数で明示する (レビュー所見)。
        "eligible_for_refreeze": False,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "manifest_sha256": manifest_sha256,
        "stock_configuration": stock_configuration,
        "wired_min_rel_floor": wired_min_rel_floor,
        "reps": protocol["reps"],
        "n_sessions": n_sessions,
        "scale_adequacy_rel_tolerance": protocol["scale_adequacy_rel_tolerance"],
        "holdouts": holdouts,
        "configurations": configurations,
        "binaries": {cid: dict(rec) for cid, rec in binaries.items()},
        # --- verify_floor_artifact が読む正本フィールド (config は 7 scalar のみ, α-3) ---
        "config": {
            "formula": protocol["formula"],
            "n_sessions": n_sessions,
            "reps": reps,
            "stock_configuration": stock_configuration,
            "wired_min_rel_floor": wired_min_rel_floor,
            "session_cv_max": session_cv_max,
            "cell_cv_max": cell_cv_max,
        },
        "sessions": session_records,
        "cells": cells_out,
        "floors": floors_out,
        # --- 付帯 ---
        "wall_ledger": wall_ledger,
        "excluded": excluded,
        "attempts": attempts,
    }


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.4g}"
    return str(value)


def _render_result_md(result: Mapping) -> str:
    """人間向けサマリ。**result JSON からのみ描画する** (β-9: JSON が唯一のソース)。

    セル表 + floor 案 (pair=configuration_id) + 除外理由別件数 + machine_anomaly セル一覧 +
    全 attempt の CV/median/valid (α-14) を併記する。
    """
    lines: list[str] = []
    lines.append(f"# 8b floor campaign result — {result['env_tag']} / mode={result['mode']}")
    lines.append("")
    lines.append("> floor **案** (何も発効させていない)。freeze への floor 書込みは親が行う。")
    lines.append("> 単一 campaign 内 session dispersion に基づく記述的下限 "
                 "(別 run 間の変動は含まない)。")
    lines.append(f"> eligible_for_refreeze: {result['eligible_for_refreeze']}")
    lines.append("")
    lines.append(f"- formula: `{result['formula']}`")
    lines.append(f"- ccbench_pin: `{result['ccbench_pin']}`")
    lines.append(f"- protocol_sha256: `{result['protocol_sha256']}`")
    lines.append(f"- freeze_sha256: `{result['freeze_sha256']}`")
    lines.append(f"- manifest_sha256: `{result['manifest_sha256']}`")
    lines.append(f"- stock_configuration: `{result['stock_configuration']}`")
    lines.append(f"- wired_min_rel_floor: {result['wired_min_rel_floor']}")
    lines.append(f"- scale_adequacy_rel_tolerance: {result.get('scale_adequacy_rel_tolerance')}")
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

    lines.append("## floor 案 (holdout 別, pair = configuration_id)")
    lines.append("")
    floors = result.get("floors") or {}
    for holdout_id in sorted(floors):
        hf = floors[holdout_id]
        lines.append(f"### {holdout_id}")
        lines.append("")
        lines.append(f"- scalar_alt (全 pair の max): {_fmt(hf.get('scalar_alt'))}")
        lines.append(f"- scale_ref (m_stock): {_fmt(hf.get('scale_ref'))}")
        diag = hf.get("diagnostics") or {}
        anomaly_cells = diag.get("machine_anomaly_cells") or []
        lines.append(f"- machine_anomaly セル: "
                     f"{', '.join(f'`{c}`' for c in anomaly_cells) if anomaly_cells else '(なし)'}")
        lines.append("")
        pairs = hf.get("pairs") or {}
        lines.append("| pair (configuration_id) | floor_pair |")
        lines.append("|---|---:|")
        for cfg in sorted(pairs):
            lines.append(f"| `{cfg}` | {_fmt(pairs[cfg])} |")
        lines.append("")

    lines.append("## 除外 session (理由別件数)")
    lines.append("")
    excluded = result.get("excluded") or []
    reason_counts: dict[str, int] = {}
    for item in excluded:
        reason = item.get("excluded_reason") or "(none)"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    if not reason_counts:
        lines.append("(なし)")
    else:
        lines.append("| reason | count |")
        lines.append("|---|---:|")
        for reason in sorted(reason_counts):
            lines.append(f"| {reason} | {reason_counts[reason]} |")
    lines.append("")

    lines.append("## 全 attempt 台帳 (CV / median / valid)")
    lines.append("")
    attempts = result.get("attempts") or []
    lines.append("| seq | cell | kind | round | valid | reason | cv | median | dur(s) |")
    lines.append("|---:|---|---|---:|:---:|---|---:|---:|---:|")
    for a in sorted(attempts, key=lambda x: x.get("seq", 0)):
        lines.append(
            f"| {a.get('seq')} | `{a.get('cell_id')}` | {a.get('kind')} | "
            f"{a.get('round')} | {a.get('valid')} | {a.get('excluded_reason')} | "
            f"{_fmt(a.get('session_cv'))} | {_fmt(a.get('session_median'))} | "
            f"{_fmt(a.get('duration_s'))} |"
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 冪等 finalization (β-11): result.json/md/terminal の状態機械                  #
# --------------------------------------------------------------------------- #

def _result_bytes(result: Mapping) -> bytes:
    return (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _md_bytes(md_text: str) -> bytes:
    text = md_text if md_text.endswith("\n") else md_text + "\n"
    return text.encode("utf-8")


def _finalize(run_dir: Path, result: Mapping, md_text: str, journal_path: Path) -> None:
    """既存物は hash 検証 + 欠落分のみ create-only 補完、上書きなし (β-11)。

    result / md は journal の純粋関数なので resume を跨いで決定的。既存 result.json/md が
    再計算 byte と一致すれば skip、不一致なら fail-closed で拒否 (改竄/非決定の検出)。
    """
    result_json = run_dir / "result.json"
    result_md = run_dir / "result.md"
    payload = _result_bytes(result)
    if result_json.exists():
        if result_json.read_bytes() != payload:
            raise FloorCampaignError(
                "finalize: 既存 result.json が再計算と不一致 (改竄/非決定の疑い)"
            )
    else:
        _create_only_bytes(result_json, payload)

    md_payload = _md_bytes(md_text)
    if result_md.exists():
        if result_md.read_bytes() != md_payload:
            raise FloorCampaignError("finalize: 既存 result.md が再計算と不一致")
    else:
        _create_only_bytes(result_md, md_payload)

    if not any(r.get("event") == "terminal" and r.get("status") == "completed"
               for r in _read_journal(journal_path)):
        _journal_append(journal_path, {"event": "terminal", "status": "completed"})


def _create_only_bytes(path: Path, payload: bytes) -> None:
    try:
        with open(path, "xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise FloorCampaignError(f"既に存在するため上書きしない: {path}") from exc


# --------------------------------------------------------------------------- #
# run_campaign (注入点)                                                         #
# --------------------------------------------------------------------------- #

def run_campaign(protocol, freeze_doc, *, out_root, mode, resume_dir=None,
                 measure_fn=None, probe_fn=None, sleep_fn=time.sleep,
                 monotonic_fn=time.monotonic, prepare_fn=None, now_fn=None) -> dict:
    """floor campaign を直列・単一テナントで実行し、floor 案 artifact を書いて返す。

    注入点 (テスト容易性): ``measure_fn(binary, records, threads, workload) -> ScalePoint`` /
    ``probe_fn() -> (rc, stdout, stderr)`` / ``sleep_fn`` / ``monotonic_fn`` / ``prepare_fn`` /
    ``now_fn() -> datetime``。CLI main はこれらを実物で束ねるだけにする。

    official mode は §8 未裁定のため **core で無条件拒否する** (δ-3): build・measure・書き込みを
    一切行わない。env 契約 (F4): clocks_per_us / numactl は ``env_contract.lookup(env_tag)`` から
    取る。machine-pin として契約の env_tag が実行機の ``p2_2.ENV_TAG`` と一致することを要求する。
    """
    # official 拒否は最優先 (build/measure/write の前, δ-3)。
    # 【C2-2 前提条件】official を有効化する際は、この直後に launch certificate 発行
    # (clean_scan_digest → build_launch_certificate → issue_launch_certificate) と
    # campaign-start record への cert sha256 束縛を結線し、verifier 側 (launch_validate)
    # で closure が certificate 起点 lineage から導出されることを照合するまで有効化しない。
    # 未結線のまま official を開けると C2-2 の未申告先行測定 fail-open が復活する。
    if mode == "official":
        raise FloorCampaignError(
            "official mode は §8 (承認束縛方式) 未裁定のため core で無条件拒否する "
            "(F6 まで pilot のみ実行可)"
        )

    if not isinstance(freeze_doc, _freeze_io.VerifiedFreeze):
        raise FloorCampaignError("freeze_doc が load_verified_freeze の戻り値でない")
    now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    prepare_fn = prepare_fn or prepare_cell
    probe_fn = probe_fn or _default_probe_fn

    protocol = validate_protocol(protocol)

    # env 契約 lookup (F4): 未登録 env_tag は fail-closed。EnvContractError は境界で
    # FloorCampaignError へ翻訳する (s8b_freeze_io adapter と同型)。
    try:
        contract = _env_contract.lookup(protocol["env_tag"])
    except _env_contract.EnvContractError as exc:
        raise FloorCampaignError(f"env 契約 lookup 失敗: {exc}") from exc
    # machine-pin + receipt (C3-10): 暫定 machine-pin と実行機 attestation の capture を
    # oracle driver と共有する execution_guard へ集約する (拒否意味論は同値 — guard が
    # p2_2.ENV_TAG との一致を検査)。EnvContractError は上で握って FloorCampaignError に
    # 翻訳済みなので、ここでは machine-pin の ExecutionGuardError だけを翻訳する。
    try:
        execution_guard.assert_machine_pin(contract, machine_env_tag=ENV_TAG)
    except execution_guard.ExecutionGuardError as exc:
        raise FloorCampaignError(str(exc)) from exc
    execution_receipt = execution_guard.build_receipt(contract, now_fn=now_fn)
    # isolation policy: allow_resume=False の env では別 process からの resume を拒否 (γ-5)。
    if resume_dir is not None and not contract.isolation_policy.allow_resume:
        raise FloorCampaignError(
            f"env {contract.env_tag} は allow_resume=False (別 process resume を拒否)"
        )

    freeze = freeze_doc.document
    freeze_sha256 = freeze_doc.sha256
    if freeze_sha256 != protocol["freeze"]["sha256"]:
        raise FloorCampaignError(
            "freeze byte sha256 が protocol.freeze.sha256 と不一致 (bytes-hash pin 破れ)"
        )
    if freeze.get("schema_version") != FREEZE_SCHEMA:
        raise FloorCampaignError(f"freeze.schema_version が {FREEZE_SCHEMA} でない")

    cells = enumerate_cells(freeze, stock_configuration=protocol["stock_configuration"])
    cell_by_id = {cell["cell_id"]: cell for cell in cells}
    schedule = build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    protocol_sha256 = _canonical_sha256(protocol)

    if measure_fn is None:
        extime_s = protocol["extime_s"]
        reps = protocol["reps"]
        clocks_per_us = contract.clocks_per_us
        numactl = list(contract.numactl)

        def measure_fn(binary, records, threads, workload):  # noqa: ANN001
            return measure_point(
                binary, records, threads, clocks_per_us, extime=extime_s, reps=reps,
                workload=workload, numactl=numactl,
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
        # content-addressed store (C3-7): 計測 bytes を env scope 永続領域へ複製し store_path を記録。
        store_root = Path(env_scope_dir(protocol["env_tag"], output_root=str(out_root))) / "binaries"
        store_binaries(built, store_root, out_root=out_root)
        manifest = assemble_manifest(
            protocol=protocol, protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256, cells=cells, built=built, schedule=schedule,
        )
        manifest_bytes = _write_create_only_json(manifest_path, manifest)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    else:
        # resume: 既存 manifest/journal を読み、protocol/freeze/manifest/binary/schedule を照合し
        # forward-only 続行する。完了 or crash 済み seq は skip、再実行は拒否。
        run_dir = Path(resume_dir)
        journal_path = run_dir / "journal.jsonl"
        manifest_path = run_dir / "manifest.json"
        manifest, manifest_sha256, built = _load_resume_manifest(
            manifest_path, protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        )
        # manifest.schedule を権威とし、再導出列との一致を検査する (β-6, 改竄検出)。
        manifest_schedule = manifest.get("schedule")
        if not isinstance(manifest_schedule, list):
            raise FloorCampaignError("resume: manifest.schedule が list でない")
        if [dict(row) for row in manifest_schedule] != schedule:
            raise FloorCampaignError(
                "resume: manifest.schedule が再導出列と不一致 (改竄の疑い, fail-closed)"
            )
        # 記録済み binary_sha256 と disk 上バイナリの実 hash を全セル再照合する。
        _verify_resume_binaries(built)
        # content-addressed store の存在 + hash 一致も再照合する (C3-7)。
        _verify_resume_store(built, out_root)

    runner = _Runner(
        protocol=protocol, cells=cells, cell_by_id=cell_by_id, binaries=built,
        schedule=schedule, journal_path=journal_path, measure_fn=measure_fn,
        probe_fn=probe_fn, sleep_fn=sleep_fn, monotonic_fn=monotonic_fn, now_fn=now_fn,
        protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        manifest_sha256=manifest_sha256, execution_receipt=execution_receipt,
    )
    if resume_dir is not None:
        _verify_resume_journal(
            runner.records, schedule=schedule, protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
        )

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

    # 自己検査: verify_floor_artifact(result, expected_protocol) == [] を満たさなければ書かない。
    # C3-6/W3 申し送り: journal receipt (session ごとの実測直前 binary_sha256_at_measure) を
    # expected_binaries として渡し、binaries section の突合を恒真検査でなく実発火にする。
    # measured_bin_sha は build 記録 sha と食い違えば _run_session が CampaignAbort するため、
    # 完走した campaign では全 session が一致し、artifact.binaries と完全一致する。
    expected = _expected_protocol(protocol, cells)
    expected_binaries = _journal_expected_binaries(runner.records)
    problems = s8b_floor_stats.verify_floor_artifact(
        result, expected, expected_binaries=expected_binaries,
    )
    if problems:
        _journal_append(journal_path, {
            "event": "terminal", "status": "artifact-invalid", "problems": list(problems),
        })
        raise FloorCampaignError(f"verify_floor_artifact が非空: {problems}")

    _finalize(run_dir, result, _render_result_md(result), journal_path)
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
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise FloorCampaignError(
            f"resume: manifest.schema_version が {MANIFEST_SCHEMA} でない (v1 交差受理を拒否)"
        )
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
    """resume: manifest 記録の binary_sha256 と disk 上バイナリの実 hash を全セル再照合する。"""
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
        actual = _full_sha256(Path(binary))
        if actual != recorded:
            raise FloorCampaignError(
                f"resume: セル {cell_id} のバイナリ sha256 が manifest と不一致 "
                f"(記録={recorded} 実測={actual}, path={binary})"
            )


def _verify_resume_journal(records: list[dict], *, schedule: list[dict],
                           protocol_sha256: str, freeze_sha256: str,
                           manifest_sha256: str) -> None:
    """resume: journal を状態機械で全件検証する (β-6)。

    campaign-start の schema 版 + protocol/freeze/manifest hash 一致、completed の再実行拒否、
    session-start の seq 一意 (duplicate start 拒否) + attempt_id 一意 + planned seq の schedule
    cell/round 一致 + retry (cell_id, retry_ordinal) 一意、session 完了→start 対応を検査する。
    """
    starts = [r for r in records if r.get("event") == "campaign-start"]
    if not starts:
        raise FloorCampaignError("resume: journal に campaign-start がない")
    cs = starts[0]
    if len(starts) != 1:
        raise FloorCampaignError("resume: campaign-start が複数ある")
    if cs.get("schema") != JOURNAL_SCHEMA:
        raise FloorCampaignError(
            f"resume: campaign-start.schema が {JOURNAL_SCHEMA} でない (旧版 journal を拒否)"
        )
    if cs.get("protocol_sha256") != protocol_sha256:
        raise FloorCampaignError("resume: campaign-start.protocol_sha256 が不一致")
    if cs.get("freeze_sha256") != freeze_sha256:
        raise FloorCampaignError("resume: campaign-start.freeze_sha256 が不一致")
    if cs.get("manifest_sha256") != manifest_sha256:
        raise FloorCampaignError("resume: campaign-start.manifest_sha256 が不一致")
    if any(r.get("event") == "terminal" and r.get("status") == "completed"
           for r in records):
        raise FloorCampaignError("resume: 既に completed 済みの campaign は再実行しない")

    sched_by_seq = {row["seq"]: row for row in schedule}
    seen_seq: set = set()
    seen_attempt: set = set()
    seen_retry: set = set()
    for r in records:
        if r.get("event") != "session-start":
            continue
        seq = r.get("seq")
        if seq in seen_seq:
            raise FloorCampaignError(f"resume: session-start の seq が重複 (duplicate start): {seq}")
        seen_seq.add(seq)
        aid = r.get("attempt_id")
        if aid in seen_attempt:
            raise FloorCampaignError(f"resume: attempt_id が重複: {aid!r}")
        seen_attempt.add(aid)
        kind = r.get("kind")
        if kind == "planned":
            row = sched_by_seq.get(seq)
            if row is None:
                raise FloorCampaignError(f"resume: planned seq {seq} が schedule に無い")
            if r.get("cell_id") != row["cell_id"] or r.get("round") != row["round"]:
                raise FloorCampaignError(
                    f"resume: seq {seq} の cell/round が schedule と不一致 "
                    f"(journal={r.get('cell_id')}/{r.get('round')} "
                    f"!= schedule={row['cell_id']}/{row['round']})"
                )
        elif kind == "retry":
            key = (r.get("cell_id"), r.get("retry_ordinal"))
            if key in seen_retry:
                raise FloorCampaignError(
                    f"resume: (cell_id, retry_ordinal) が重複 (枠再発行): {key}"
                )
            seen_retry.add(key)
        else:
            raise FloorCampaignError(f"resume: session-start の kind が未知: {kind!r}")

    for r in records:
        if r.get("event") == "session" and r.get("seq") not in seen_seq:
            raise FloorCampaignError(
                f"resume: session 完了 (seq {r.get('seq')}) に対応する start が無い"
            )


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="8b floor campaign driver (floor 案の実測。何も発効させない)",
    )
    parser.add_argument("--mode", choices=["pilot", "official"], required=True)
    parser.add_argument("--protocol", type=Path, required=True,
                        help="floor protocol JSON (s8b-floor-protocol/v2)")
    parser.add_argument("--resume", type=Path, default=None,
                        help="既存 run_dir を forward-only で続行する")
    return parser


def _resolve_freeze_path(freeze_path_text: str) -> Path:
    path = Path(freeze_path_text)
    return path if path.is_absolute() else ROOT / path


def _load_verified_freeze(path, expected_hash=None):
    """freeze loader (中立 leaf ``s8b_freeze_io``) の floor 境界 adapter。"""
    try:
        return _freeze_io.load_verified_freeze(path, expected_hash)
    except _freeze_io.FreezeIOError as exc:
        raise FloorCampaignError(str(exc)) from exc


def main(argv=None) -> int:
    args = _parser().parse_args(argv)

    # official は §8 未裁定につき CLI でも拒否する (core も二重に拒否する, δ-3)。
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
        verified = _load_verified_freeze(freeze_path, expected_hash=protocol["freeze"]["sha256"])
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
