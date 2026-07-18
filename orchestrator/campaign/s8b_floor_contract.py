# -*- coding: utf-8 -*-
"""S8b floor protocol / cell / schedule の共有 validation leaf。

stdlib のみに依存し、campaign 内の他 module は import しない。発行側と検証側が同じ
protocol 正規化、``verify_floor_artifact`` 用射影、freeze 由来セル集合、決定的 schedule を
循環 import なしで利用するための単一源である。

``validate_protocol`` の ``contract_sha256_lookup`` は env registry の単一源を leaf 内へ複製
しないための注入点であり、runtime bypass ではない。呼び手は検証対象 ``env_tag`` に対応する
凍結済み contract hash を返し、未登録 tag は ``FloorContractError`` で拒否しなければならない。
"""
from __future__ import annotations

import hashlib
import json
import math
import posixpath
import random
from collections.abc import Callable, Mapping
from typing import Optional


# 版名は一括 v2 改版し交差受理を拒否する。freeze schema は v1 freeze を読むため据置。
PROTOCOL_SCHEMA = "s8b-floor-protocol/v2"
FREEZE_SCHEMA = "8b-holdout-freeze/v1"
SCHEDULE_ALGORITHM = "round-permutation/v2"
RESULT_SCHEMA = "s8b-floor-result/v2"
MANIFEST_SCHEMA = "s8b-floor-manifest/v2"
JOURNAL_SCHEMA = "s8b-floor-journal/v2"
FORMULA_ID = "s8b-floor-stats/v2"

_PROTOCOL_KEYS = frozenset({
    "schema", "formula", "env_tag", "ccbench_pin", "freeze", "stock_configuration",
    "n_sessions", "reps", "master_seed", "schedule_algorithm", "extime_s",
    "wired_min_rel_floor", "retry_slots_per_cell",
    "session_cv_max", "cell_cv_max", "scale_adequacy_rel_tolerance",
    "allowed_excluded_reasons", "contract_sha256",
})
_FREEZE_RECORD_KEYS = frozenset({"path", "sha256"})

# 承認済み標本設計の凍結値。共有 validator が別実験への変質を開始前に拒否する。
_APPROVED_N_SESSIONS = 8
_APPROVED_REPS = 5
_APPROVED_RETRY_SLOTS = 2
_APPROVED_SESSION_CV_MAX = "0.10"
_APPROVED_CELL_CV_MAX = "0.15"
_APPROVED_SCALE_ADEQUACY = "0.10"
_APPROVED_REASONS = (
    "competing_process",
    "launch_failure",
    "nonfinite_or_partial_output",
    "performance_anomaly",
)

_FLOOR_ARTIFACT_PROTOCOL_KEYS = (
    "formula",
    "n_sessions",
    "reps",
    "stock_configuration",
    "wired_min_rel_floor",
    "session_cv_max",
    "cell_cv_max",
)

# calibrator.runner の production command が記録する perf event 集合。runner 側が
# drift した場合、issuer の raw→portable 射影が fail-closed で止める。
_RUN_CMD_PERF_EVENTS = (
    "LLC-load-misses", "LLC-loads", "instructions", "cycles",
)


class FloorContractError(RuntimeError):
    """floor 共有契約を検証できない場合の fail-closed 拒否。"""


def _pos_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FloorContractError(f"protocol.{field} が正整数でない")
    return value


def _non_neg_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FloorContractError(f"protocol.{field} が非負整数でない")
    return value


def _non_empty_str(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FloorContractError(f"protocol.{field} が空でない文字列でない")
    return value


def _pinned(value, expected, *, field: str):
    """承認凍結値との完全一致を要求する。"""
    if value != expected or type(value) is not type(expected):
        raise FloorContractError(
            f"protocol.{field} が承認凍結値と不一致 (受領 {value!r} != 承認 {expected!r})"
        )
    return value


def validate_protocol(
        document: Mapping, *, contract_sha256_lookup: Callable[[str], str]) -> dict:
    """protocol を full validate し、canonical hash 入力となる正規化 dict を返す。

    未知 key・欠落・型不正・版不一致・承認 pin 不一致・env contract hash 不一致をすべて
    fail-closed で拒否する。戻り値は exact 18-key で、JSON canonicalization 前の唯一の
    正規化表現である。
    """
    if not isinstance(document, Mapping):
        raise FloorContractError("protocol が object でない")
    keys = set(document)
    if keys != set(_PROTOCOL_KEYS):
        missing = sorted(set(_PROTOCOL_KEYS) - keys)
        unknown = sorted(keys - set(_PROTOCOL_KEYS))
        raise FloorContractError(
            f"protocol の key 集合が不一致 (欠落={missing} 未知={unknown})"
        )

    if document["schema"] != PROTOCOL_SCHEMA:
        raise FloorContractError(
            f"protocol.schema が {PROTOCOL_SCHEMA} でない (v1 の交差受理を拒否)"
        )
    if document["schedule_algorithm"] != SCHEDULE_ALGORITHM:
        raise FloorContractError(
            f"protocol.schedule_algorithm が {SCHEDULE_ALGORITHM} でない"
        )

    formula = _non_empty_str(document["formula"], field="formula")
    if formula != FORMULA_ID:
        raise FloorContractError(
            f"protocol.formula ({formula}) が s8b_floor_stats.FORMULA_ID "
            f"({FORMULA_ID}) と不一致"
        )

    env_tag = _non_empty_str(document["env_tag"], field="env_tag")
    contract_sha256 = _non_empty_str(document["contract_sha256"], field="contract_sha256")
    try:
        expected_contract_sha256 = contract_sha256_lookup(env_tag)
    except FloorContractError:
        raise
    except Exception as exc:
        raise FloorContractError(
            f"protocol.env_tag の env contract を照合できない: {exc}"
        ) from exc
    if contract_sha256 != expected_contract_sha256:
        raise FloorContractError(
            f"protocol.contract_sha256 が env_contract.lookup({env_tag!r}).contract_sha256 と不一致"
        )
    ccbench_pin = _non_empty_str(document["ccbench_pin"], field="ccbench_pin")
    stock_configuration = _non_empty_str(
        document["stock_configuration"], field="stock_configuration",
    )
    master_seed = _non_empty_str(document["master_seed"], field="master_seed")

    freeze_record = document["freeze"]
    if not isinstance(freeze_record, Mapping) or set(freeze_record) != set(_FREEZE_RECORD_KEYS):
        raise FloorContractError("protocol.freeze schema が {path, sha256} でない")
    freeze_path = _non_empty_str(freeze_record["path"], field="freeze.path")
    freeze_sha = freeze_record["sha256"]
    if (not isinstance(freeze_sha, str) or len(freeze_sha) != 64
            or any(ch not in "0123456789abcdef" for ch in freeze_sha)):
        raise FloorContractError("protocol.freeze.sha256 が SHA-256 でない")

    n_sessions = _pinned(
        document["n_sessions"], _APPROVED_N_SESSIONS, field="n_sessions",
    )
    reps = _pinned(document["reps"], _APPROVED_REPS, field="reps")
    retry_slots_per_cell = _pinned(
        document["retry_slots_per_cell"], _APPROVED_RETRY_SLOTS,
        field="retry_slots_per_cell",
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
        raise FloorContractError("protocol.wired_min_rel_floor が (0,1] の有限数でない")
    wired_min_rel_floor = float(wired_min_rel_floor)

    reasons_raw = document["allowed_excluded_reasons"]
    if reasons_raw != list(_APPROVED_REASONS):
        raise FloorContractError(
            "protocol.allowed_excluded_reasons が承認凍結 4 行 (固定順) と不一致: "
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


def canonical_protocol_sha256(normalized_protocol: Mapping) -> str:
    """full-validated 正規化戻り値の canonical JSON SHA-256 を返す。"""
    try:
        raw = json.dumps(
            normalized_protocol,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FloorContractError(f"canonical JSON に変換できない: {exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def project_protocol_for_floor_artifact(protocol: Mapping) -> dict:
    """full-validated protocol を ``verify_floor_artifact`` 用 7 scalar へ射影する。"""
    return {key: protocol[key] for key in _FLOOR_ARTIFACT_PROTOCOL_KEYS}


def build_portable_run_cmd(
        *, binary, workload, records, threads, extime_s, clocks_per_us,
        numactl) -> tuple[str, ...]:
    """検証・artifact 記録用の portable benchmark argv を決定論的に構築する。

    ``binary`` は out-root 相対の portable store path とし、runtime absolute path は
    受理しない。workload flag は key の辞書順で固定するため、入力 Mapping の挿入順に
    依存しない。戻り値は表示・照合専用であり、再実行 API ではない。
    """
    if (not isinstance(binary, str) or not binary or binary.startswith("/")
            or "\\" in binary or "\x00" in binary
            or posixpath.normpath(binary) != binary
            or binary in {".", ".."}
            or any(part in {"", ".", ".."} for part in binary.split("/"))):
        raise FloorContractError("run_cmd.binary が canonical portable relative path でない")
    for field, value in {
            "records": records, "threads": threads, "extime_s": extime_s,
            "clocks_per_us": clocks_per_us,
    }.items():
        if type(value) is not int or value <= 0:
            raise FloorContractError(f"run_cmd.{field} が正整数でない")
    if not isinstance(workload, Mapping) or not workload:
        raise FloorContractError("run_cmd.workload が空でない Mapping でない")
    for key, value in workload.items():
        if (not isinstance(key, str) or not key or not isinstance(value, str)
                or not value or "\x00" in key or "\x00" in value):
            raise FloorContractError("run_cmd.workload が空でない str→str でない")
    if not isinstance(numactl, tuple):
        raise FloorContractError("run_cmd.numactl が tuple でない")
    if not all(isinstance(token, str) and token and "\x00" not in token
               for token in numactl):
        raise FloorContractError("run_cmd.numactl に空または非 str token がある")

    argv = [
        *numactl,
        "perf", "stat", "-e", ",".join(_RUN_CMD_PERF_EVENTS), "--", binary,
        f"-thread_num={threads}",
        f"-ycsb_tuple_num={records}",
        f"-extime={extime_s}",
        f"-clocks_per_us={clocks_per_us}",
    ]
    argv.extend(f"-{key}={workload[key]}" for key in sorted(workload))
    return tuple(argv)


def _holdout_workload(holdout: Mapping, *, holdout_id: str) -> dict:
    records = holdout.get("records")
    threads = holdout.get("threads")
    workload = holdout.get("ycsb")
    if (isinstance(records, bool) or not isinstance(records, int) or records <= 0
            or isinstance(threads, bool) or not isinstance(threads, int) or threads <= 0):
        raise FloorContractError(f"holdout {holdout_id} の records/threads が正整数でない")
    if not isinstance(workload, Mapping) or not workload:
        raise FloorContractError(f"holdout {holdout_id} の ycsb が空でない object でない")
    for key, value in workload.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise FloorContractError(f"holdout {holdout_id} の ycsb が str→str でない")
    return {"records": records, "threads": threads, "workload": dict(workload)}


def enumerate_cells(freeze: Mapping, *, stock_configuration: str) -> list[dict]:
    """freeze から holdout × configuration セルを決定論的に列挙する。"""
    holdouts_obj = freeze.get("holdouts")
    if not isinstance(holdouts_obj, Mapping) or not holdouts_obj:
        raise FloorContractError("freeze.holdouts が空でない object でない")
    holdout_ids = sorted(holdouts_obj)

    configurations: Optional[list[str]] = None
    per_holdout: dict[str, dict] = {}
    for holdout_id in holdout_ids:
        holdout = holdouts_obj[holdout_id]
        if not isinstance(holdout, Mapping):
            raise FloorContractError(f"holdout {holdout_id} が object でない")
        binding = holdout.get("variant_binding")
        entries = binding.get("entries") if isinstance(binding, Mapping) else None
        if not isinstance(entries, Mapping) or not entries:
            raise FloorContractError(
                f"holdout {holdout_id} の variant_binding.entries が空でない object でない"
            )
        entry_ids = sorted(entries)
        if configurations is None:
            configurations = entry_ids
        elif entry_ids != configurations:
            raise FloorContractError(
                f"holdout {holdout_id} の構成集合が他 holdout と不一致"
            )
        if stock_configuration not in entries:
            raise FloorContractError(
                f"holdout {holdout_id} の entries に stock_configuration "
                f"({stock_configuration}) がない"
            )
        per_holdout[holdout_id] = _holdout_workload(holdout, holdout_id=holdout_id)

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


def expected_cells_from_cells(cells) -> dict[str, list]:
    """検証済み cell 列から ``expected_cells`` の exact mapping を作る。"""
    expected_cells: dict[str, list] = {}
    for cell in cells:
        expected_cells.setdefault(cell["holdout_id"], []).append(cell["configuration_id"])
    for holdout_id in expected_cells:
        expected_cells[holdout_id] = sorted(expected_cells[holdout_id])
    return expected_cells


def derive_expected_cells(freeze: Mapping, *, stock_configuration: str) -> dict[str, list]:
    """ratified freeze の holdout/variant binding から expected cells を独立導出する。"""
    cells = enumerate_cells(freeze, stock_configuration=stock_configuration)
    return expected_cells_from_cells(cells)


def _round_seed(master_seed: str, round_no: int) -> int:
    """round 種: sha256(f"{master_seed}/{r}") の先頭 8 byte、big-endian。"""
    payload = f"{master_seed}/{round_no}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def build_schedule(*, cells: list[dict], master_seed: str, n_sessions: int) -> list[dict]:
    """round ごとに全 cell_id を seed 置換した決定的 session 列を返す。"""
    if not isinstance(n_sessions, int) or isinstance(n_sessions, bool) or n_sessions <= 0:
        raise FloorContractError("build_schedule: n_sessions が正整数でない")
    cell_ids = sorted(cell["cell_id"] for cell in cells)
    if len(set(cell_ids)) != len(cell_ids):
        raise FloorContractError("build_schedule: cell_id が重複している")
    if not cell_ids:
        raise FloorContractError("build_schedule: cells が空")
    rows: list[dict] = []
    for round_no in range(1, n_sessions + 1):
        permuted = list(cell_ids)
        random.Random(_round_seed(master_seed, round_no)).shuffle(permuted)
        for cell_id in permuted:
            rows.append({"seq": len(rows), "round": round_no, "cell_id": cell_id})
    return rows


_RESUME_STATES = frozenset({
    "L", "M-prestart", "M-running", "M-finalize-pending",
})


def classify_journal_resume_state(
        records, *, manifest_exists: bool, result_published: bool,
        markdown_published: bool) -> str:
    """L/M resume の構造 substate を fail-closed に分類する共有 pure helper。

    ``L`` は manifest 無し・journal が launch-start 1 件だけ、``M-prestart`` は
    sealed manifest 有り・campaign-start 無し、``M-running`` は一意 campaign-start
    有り・terminal 無し、``M-finalize-pending`` は一意 completed terminal が最終 record
    だが result/md publish が片方以上未完、である。cert bytes/path/time、event ごとの exact
    schema、manifest/result bytes は issuer/verifier の各境界で別途厳密検証する。

    aborted / artifact-invalid / terminal 重複 / completed 後の record / publish 完了済みは
    再開可能状態に分類しない。L の自己整合 bundle 全体をゼロから捏造する攻撃は、この
    journal 内 hash だけでは閉じない（凍結済み保証境界）。
    """
    if not isinstance(records, list) or not all(isinstance(r, Mapping) for r in records):
        raise FloorContractError("resume journal が object record の list でない")
    for name, value in {
            "manifest_exists": manifest_exists,
            "result_published": result_published,
            "markdown_published": markdown_published,
    }.items():
        if type(value) is not bool:
            raise FloorContractError(f"resume state {name} が bool でない")

    terminals = [r for r in records if r.get("event") == "terminal"]
    if len(terminals) > 1:
        raise FloorContractError("resume journal の terminal が重複している")
    if terminals:
        terminal = terminals[0]
        if records[-1] is not terminal:
            raise FloorContractError("resume journal の terminal が最終 record でない")
        if terminal.get("status") != "completed":
            raise FloorContractError("aborted/artifact-invalid terminal は再開できない")
        if not manifest_exists:
            raise FloorContractError("completed terminal に sealed manifest がない")
        if result_published and markdown_published:
            raise FloorContractError("publish 完了済み campaign は再開できない")
        return "M-finalize-pending"

    campaign_starts = [r for r in records if r.get("event") == "campaign-start"]
    if len(campaign_starts) > 1:
        raise FloorContractError("resume journal の campaign-start が重複している")
    if not manifest_exists:
        if (len(records) == 1 and records[0].get("event") == "launch-start"
                and not result_published and not markdown_published):
            return "L"
        raise FloorContractError("manifest 無し journal は厳密な L 状態でない")
    if result_published or markdown_published:
        raise FloorContractError("completed terminal 前に result/md が publish されている")
    if not campaign_starts:
        if any(r.get("event") != "launch-start" for r in records):
            raise FloorContractError("M-prestart に launch-start 以外の record がある")
        if sum(r.get("event") == "launch-start" for r in records) > 1:
            raise FloorContractError("M-prestart の launch-start が重複している")
        return "M-prestart"
    return "M-running"
