# -*- coding: utf-8 -*-
"""8b oracle の実行 gate、binding 実体化、block 単位 driver。"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent
sys.path.insert(0, str(_ORCHESTRATOR))

from campaign import pipeline, s8b_budget, s8b_run_marker, wal  # noqa: E402
from campaign.layout import campaign_layout, repo_output_root  # noqa: E402
from campaign.s1_direct_comparison import PreparedCell, prepare_cell  # noqa: E402
from campaign import s1_known_axes_freeze, s8b_holdout_freeze  # noqa: E402
from campaign.s8b_oracle_manifest import (  # noqa: E402
    config_for_block,
    verify_manifest,
)


SESSION_STAGE = "s8b-oracle-session"
DEFAULT_FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"
DEFAULT_BUDGET_PATH = ROOT / "output/s8b-budget/time_ledger.json"
NUMACTL = ["numactl", "--interleave=all"]
_BINDING_KEYS = {
    "genome_canonical", "src_token", "variant_id", "entry_sha256",
    "binding_sha256",
}


class OracleDriverError(RuntimeError):
    """8b oracle の入力・identity・実行契約を検証できない場合の拒否。"""


class _UnknownAbortReason(OracleDriverError):
    """pipeline の abort reason を凍結済み outcome へ射影できない。"""

    def __init__(self, reason: str):
        super().__init__(f"未知の pipeline abort reason: {reason}")
        self.reason = reason


@dataclass
class GateDecision:
    allowed: bool
    refusals: list[str]


def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OracleDriverError(f"canonical JSON に変換できない: {exc}") from exc


def _canonical_sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _load_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OracleDriverError(f"JSON を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OracleDriverError(f"JSON top-level が object でない: {path}")
    return value


def _reject_json_constant(token: str):
    """strict parse: NaN / Infinity 等の非数値定数を拒否する。"""
    raise OracleDriverError(f"freeze JSON に非数値定数が含まれる: {token}")


@dataclass(frozen=True)
class VerifiedFreeze:
    """hash 検証済み freeze bytes の strict parse 結果と、その byte sha256。

    verify から use までを単一 object で束ね、consumer 間 (gate・driver・
    manifest verify・budget limits・perf 三軸) の再読込を除去する (A3-6)。
    """
    document: dict
    sha256: str


def load_verified_freeze(path, expected_hash: Optional[str] = None) -> VerifiedFreeze:
    """freeze bytes を一度だけ読み、hash 検証 + strict parse した単一 object を返す。

    全 consumer はこの戻り値の ``document`` / ``sha256`` だけを使い、freeze を
    再読込しない。よって gate 検証後・使用前に freeze byte を差し替えても差替え後
    の値は一切観測されない (verify-use 間 TOCTOU の遮断、A3-6)。``expected_hash``
    を与えた場合は byte sha256 との一致を要求し、不一致は拒否する (fail-closed)。
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise OracleDriverError(f"freeze bytes を読めない: {path}: {exc}") from exc
    sha256 = hashlib.sha256(raw).hexdigest()
    if expected_hash is not None and sha256 != expected_hash:
        raise OracleDriverError(
            f"freeze byte sha256 が expected_hash と不一致: {path}"
        )
    try:
        document = json.loads(raw.decode("utf-8"),
                              parse_constant=_reject_json_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OracleDriverError(
            f"freeze JSON を strict parse できない: {path}: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise OracleDriverError(f"freeze JSON top-level が object でない: {path}")
    return VerifiedFreeze(document=document, sha256=sha256)


def _resolve_recorded_path(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def gate_check(*, freeze_path=None, manifest_path=None, root,
               verified: Optional[VerifiedFreeze] = None) -> GateDecision:
    """実走前の独立 gate を順番に全件検査し、全拒否理由を返す。

    ``verified`` (``load_verified_freeze`` の戻り値) を与えた場合は freeze を
    再読込せず、その単一 object の document/sha256 だけを使う (A3-6: verify-use
    間差替えの遮断)。与えない場合は自身で ``load_verified_freeze`` を一度呼ぶ。
    """
    root = Path(root)
    refusals: list[str] = []
    freeze: Optional[dict] = None
    freeze_sha: Optional[str] = None

    if verified is not None:
        freeze = verified.document
        freeze_sha = verified.sha256
    else:
        try:
            loaded = load_verified_freeze(Path(freeze_path))
        except Exception as exc:
            refusals.append(f"holdout-freeze-verify: {type(exc).__name__}: {exc}")
        else:
            freeze = loaded.document
            freeze_sha = loaded.sha256

    if freeze is not None:
        if freeze.get("floor") is None and freeze.get("budget") is None:
            try:
                # v1 verifier は floor/budget がともに null の freeze だけを対象にする。
                # v2 実走経路はこの枝に入らない (下の freeze-v2 refusal へ倒れる) ため、
                # ここでの path 再読込は A3-6 の単一 object 対象外。
                s8b_holdout_freeze.verify(Path(freeze_path), root=root)
            except Exception as exc:
                refusals.append(
                    f"holdout-freeze-verify: {type(exc).__name__}: {exc}"
                )
        else:
            # floor/budget 充填済み freeze は、承認証跡も含む strict v2
            # verifier が導入されるまで内容を部分解釈しない。
            refusals.append(
                "freeze-v2-verifier-not-implemented: "
                "floor/budget 充填済み freeze の strict verifier が未実装"
            )

    try:
        known_record = freeze.get("known_axes_freeze") if isinstance(freeze, Mapping) else None
        if not isinstance(known_record, Mapping):
            raise OracleDriverError("known_axes_freeze source record がない")
        known_path_text = known_record.get("path")
        if not isinstance(known_path_text, str) or not known_path_text:
            raise OracleDriverError("known_axes_freeze.path が空でない文字列でない")
        known_path = _resolve_recorded_path(known_path_text, root=root)
        s1_known_axes_freeze.verify(
            known_path, source_resolver=lambda relative: root / relative,
        )
    except Exception as exc:
        refusals.append(f"known-axes-freeze-verify: {type(exc).__name__}: {exc}")

    if not isinstance(freeze, Mapping) or freeze.get("floor") is None:
        refusals.append("floor-null: freeze.floor が null")
    if not isinstance(freeze, Mapping) or freeze.get("budget") is None:
        refusals.append("budget-null: freeze.budget が null")

    if manifest_path is not None:
        manifest_path = Path(manifest_path)
        try:
            # A3-6: 検証済み単一 object を渡し、manifest verify 内での freeze 再読込を除く。
            if freeze is not None and freeze_sha is not None:
                verify_manifest(
                    manifest_path, root=root,
                    freeze_document=freeze, freeze_sha256=freeze_sha,
                )
            else:
                verify_manifest(manifest_path, root=root)
        except Exception as exc:
            refusals.append(f"manifest-verify: {type(exc).__name__}: {exc}")
        try:
            manifest = _load_json_object(manifest_path)
            record = manifest.get("freeze")
            if not isinstance(record, Mapping) or not isinstance(record.get("sha256"), str):
                raise OracleDriverError("manifest.freeze.sha256 がない")
            if freeze_sha is None:
                raise OracleDriverError("freeze が読めず byte sha256 を照合できない")
            if record["sha256"] != freeze_sha:
                raise OracleDriverError("manifest と指定 freeze の byte sha256 が不一致")
        except Exception as exc:
            refusals.append(f"manifest-freeze-hash: {type(exc).__name__}: {exc}")

    return GateDecision(allowed=not refusals, refusals=refusals)


def _binding_entry(freeze: Mapping, holdout_id: str, configuration_id: str) -> Mapping:
    try:
        holdout = freeze["holdouts"][holdout_id]
        binding = holdout["variant_binding"]
        entry = binding["entries"][configuration_id]
    except (KeyError, TypeError) as exc:
        raise OracleDriverError(
            f"freeze binding がない: holdout={holdout_id} configuration={configuration_id}"
        ) from exc
    if not isinstance(entry, Mapping):
        raise OracleDriverError("freeze binding entry が object でない")
    return entry


def _binding_from_prepared(entry: Mapping, prepared: PreparedCell) -> dict:
    if not isinstance(prepared, PreparedCell):
        raise OracleDriverError("prepare_fn の戻り値が PreparedCell でない")
    identity = {
        "genome_canonical": prepared.genome.canonical(),
        "src_token": prepared.src_token,
        "variant_id": pipeline.variant_id(prepared.genome, prepared.src_token),
        "entry_sha256": _canonical_sha256(entry),
    }
    identity["binding_sha256"] = _canonical_sha256(identity)
    return identity


@contextlib.contextmanager
def _prepared_binding(
        *, freeze: Mapping, holdout_id: str, configuration_id: str,
        ccbench_pin: str, prepare_fn):
    entry = _binding_entry(freeze, holdout_id, configuration_id)
    cell = {"configuration": configuration_id, "variant": entry}
    resource = prepare_fn(cell, ccbench_pin)
    manager = (resource if hasattr(resource, "__enter__") and hasattr(resource, "__exit__")
               else contextlib.nullcontext(resource))
    with manager as prepared:
        yield _binding_from_prepared(entry, prepared), prepared


def prepare_binding(
        *, freeze, holdout_id, configuration_id, ccbench_pin,
        prepare_fn=prepare_cell) -> dict:
    """freeze entry を S-1 materializer で実体化し、完全 binding identity を返す。"""
    with _prepared_binding(
            freeze=freeze, holdout_id=holdout_id,
            configuration_id=configuration_id, ccbench_pin=ccbench_pin,
            prepare_fn=prepare_fn) as (identity, _prepared):
        return identity


def _expected_binding(manifest: Mapping, holdout_id: str,
                      configuration_id: str) -> dict:
    raw = manifest.get("binding_identity")
    candidate = None
    if isinstance(raw, Mapping):
        for key in (f"{holdout_id}:{configuration_id}",
                    f"{holdout_id}/{configuration_id}"):
            if isinstance(raw.get(key), Mapping):
                candidate = raw[key]
                break
        if candidate is None:
            for value in raw.values():
                if (isinstance(value, Mapping)
                        and value.get("holdout_id") == holdout_id
                        and value.get("configuration_id") == configuration_id):
                    candidate = value
                    break
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        for value in raw:
            if (isinstance(value, Mapping)
                    and value.get("holdout_id") == holdout_id
                    and value.get("configuration_id") == configuration_id):
                candidate = value
                break
    if not isinstance(candidate, Mapping):
        raise OracleDriverError(
            f"manifest binding_identity がない: {holdout_id}/{configuration_id}"
        )
    projected = {
        key: value for key, value in candidate.items()
        if key not in {"holdout_id", "configuration_id"}
    }
    if set(projected) != _BINDING_KEYS:
        raise OracleDriverError(
            f"manifest binding_identity schema が不一致: {sorted(set(projected) ^ _BINDING_KEYS)}"
        )
    _canonical_bytes(projected)
    return projected


def _append_session(layout, env_tag: str, event: str, payload: Mapping) -> None:
    wal.log(
        layout, "oracle-session", SESSION_STAGE, env_tag,
        {"event": event, **dict(payload)},
    )


def _session_events(layout) -> list[dict]:
    return [dict(record.payload) for record in wal.read_records(layout)
            if record.stage == SESSION_STAGE]


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _is_transient_prepare_failure(exc: BaseException) -> bool:
    current: Optional[BaseException] = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (OSError, subprocess.SubprocessError)):
            return True
        current = current.__cause__ or current.__context__
    return False


def _perf_for_holdout(freeze: Mapping, holdout_id: str,
                      run_contract: Mapping) -> pipeline.PerfConfig:
    try:
        holdout = freeze["holdouts"][holdout_id]
        records = holdout["records"]
        threads = holdout["threads"]
        workload = holdout["ycsb"]
        extime = run_contract["extime"]
        reps = run_contract["reps"]
    except (KeyError, TypeError) as exc:
        raise OracleDriverError(f"holdout/perf 構成が不完全: {holdout_id}") from exc
    if (isinstance(records, bool) or not isinstance(records, int) or records <= 0
            or isinstance(threads, bool) or not isinstance(threads, int) or threads <= 0
            or not isinstance(workload, Mapping)):
        raise OracleDriverError(f"holdout perf schema が不正: {holdout_id}")
    return pipeline.PerfConfig(
        records=records, threads=threads, workload=dict(workload),
        extime=extime, reps=reps,
    )


def _trial_measurements(records: Sequence[object]) -> tuple[dict, float]:
    abort_payload: dict = {}
    bench_wall_s = 0.0
    for record in records:
        payload = getattr(record, "payload", None)
        if not isinstance(payload, Mapping):
            continue
        if getattr(record, "stage", None) == "abort":
            abort_payload = dict(payload)
        if getattr(record, "stage", None) in {"bench_done", "abort"}:
            value = payload.get("bench_wall_s")
            if (not isinstance(value, bool) and isinstance(value, (int, float))
                    and math.isfinite(float(value)) and float(value) >= 0):
                bench_wall_s = max(bench_wall_s, float(value))
    return abort_payload, bench_wall_s


def _outcome_for(result, abort_payload: Mapping) -> str:
    if getattr(result, "certified", False) and not getattr(result, "aborted", True):
        return "committed"
    reason = str(abort_payload.get("reason") or getattr(result, "abort_reason", "") or "abort")
    verdict = str(getattr(result, "verdict", "") or "")
    if abort_payload.get("verify") is not None or (verdict and verdict != "serializable"):
        return "correctness-red"
    if reason in {"build-error", "identity-error"}:
        return "build-failed"
    if reason == "trace-timeout":
        return "timeout"
    if reason in {
            "trace-run-nonzero-exit", "trace-empty", "trace-no-abort-counts",
            "trace-parse-error", "verify-competing-tenant"}:
        return "verify-inconclusive"
    if reason in {
            "bench-competing-tenant", "bench-no-throughput", "bench-cv-undefined"}:
        return "bench-failed"
    raise _UnknownAbortReason(reason)


def _ensure_campaign(layout, *, manifest_sha256: str, block_id: str,
                     campaign_id: str, freeze_sha256: str, marker_root) -> None:
    """実走前に claim を確立する。既に着手済みなら択 (a) で resume を全拒否する。

    R6: WAL byte の存在 / 実走済みマーカーの存在 / campaign.lock の存在の三重判定で、
    どれか一つでも存在すれば当該 freeze/campaign は着手済みとみなし resume を拒否する
    (§9 項 8 択 (a) = 途中 crash は実験全体を判定不能へ)。順序は「マーカー生成 →
    (呼び出し元が) campaign-start」。マーカーは `--output-root` 非依存の場所に置くため、
    出力先の付け替えで拒否を迂回できない。
    """
    layout.ensure()
    preimage = _canonical_bytes({
        "manifest_sha256": manifest_sha256,
        "block_id": block_id,
        "campaign_id": campaign_id,
    }).decode("utf-8")

    # (1) truncated/汚染 WAL を含む「byte が存在する WAL」の resume を閉じる。
    #     read_records() が末尾切れの 1 行を捨てて [] を返す経路でも byte 存在で拒否。
    if wal.wal_bytes_present(layout):
        raise OracleDriverError(
            "既存 WAL byte を持つ oracle campaign の resume は拒否 (択 a・truncated 含む)"
        )
    # (2) 実走済みマーカー (--output-root 非依存・freeze byte hash 束縛) の存在で全拒否。
    if s8b_run_marker.marker_exists(marker_root, freeze_sha256):
        raise OracleDriverError(
            "実走済みマーカーが存在する freeze の再走は全拒否 (択 a)"
        )
    # (3) 原子的 one-shot lock。既存 lock = 並行起動 or 着手済み → resume 拒否。
    #     ここから campaign-start までが排他区間。
    if not wal.acquire_lock_atomic(layout, preimage):
        raise OracleDriverError(
            "campaign.lock が既に存在するため resume/並行起動を拒否 (択 a)"
        )
    # (4) マーカー生成 (campaign-start より前)。原子的 exclusive-create が競合を捕捉する。
    try:
        s8b_run_marker.create_run_marker(marker_root, freeze_sha256, {
            "campaign_id": campaign_id,
            "block_id": block_id,
            "manifest_sha256": manifest_sha256,
        })
    except s8b_run_marker.RunMarkerError as exc:
        raise OracleDriverError(
            f"実走済みマーカーの原子的生成に失敗 (再走の可能性): {exc}"
        ) from exc


def run_block(
        *, manifest_path, block_id, freeze_path, root, output_root, budget_path,
        marker_root=None, evaluate_fn=None, prepare_fn=None) -> dict:
    """一つの immutable block を直列実行し、terminal status を耐久化して返す。

    gate 拒否時は一切書き込まず ``status="refused"`` を返す。

    戻り値 JSON 契約 (CLI が ``_exit_code`` で終了コードへ射影する):

    - ``status`` — 次のいずれか (かっこ内は CLI rc):
      ``completed`` (0): 全予定行が一意 terminal outcome + 対応 budget terminal
      record を耐久化し、held reservation を実測へ精算した (強い completed 定義)。
      ``protocol_violation`` (3): 1 行以上が binding-refused / prepare 恒久失敗 /
      未実行で強い completed 定義を満たさない。``unresolved_rows`` に未達
      schedule_index を載せ、reservation は精算せず held のまま残す (fail-closed)。
      ``budget_exhausted_before_attempt`` (2): 一括予約が確保できず一行も走らない。
      ``error`` (1): 実行中の内部逸脱 (未分類 abort reason / reservation 枠超過)。
      reservation を非解放のまま残し ``error`` に理由を載せる。
      ``refused`` (2): 実走前 gate が拒否し ``refusals`` に全拒否理由を載せる。
    - ``completed_trials`` — 一意 terminal outcome + budget entry を得た行数。
    - ``unresolved_rows`` — protocol_violation 時のみ。未達 schedule_index の列。
    - ``error`` — error 時のみ。逸脱理由の文字列。
    - ``events`` — WAL に耐久化した session event の逐次列 (terminal event を含む)。
    - ``allowed`` / ``refusals`` / ``campaign_id`` / ``manifest_sha256`` /
      ``freeze_sha256`` / ``schedule_sha256`` — gate 判定と block identity。

    rc 優先順位は ``_exit_code`` を正本とする:
    internal-error(1) > protocol_violation(3) > budget-refused(2) > completed(0)。
    """
    freeze_path = Path(freeze_path)
    # A3-6: freeze bytes を一度だけ読み hash 検証 + strict parse した単一 object を、
    # gate・manifest verify・budget limits・perf 三軸の全 consumer で共有する。
    # verify から use までの間に freeze byte を差し替えても差替え後の値は使われない。
    try:
        verified = load_verified_freeze(freeze_path)
    except OracleDriverError as exc:
        decision = GateDecision(
            allowed=False,
            refusals=[f"holdout-freeze-verify: {type(exc).__name__}: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}

    decision = gate_check(
        freeze_path=freeze_path, manifest_path=manifest_path, root=root,
        verified=verified,
    )
    if not decision.allowed:
        return {"status": "refused", **asdict(decision)}

    root = Path(root)
    output_root = Path(output_root)
    budget_path = Path(budget_path)
    # マーカーは --output-root 非依存 (freeze 正本側)。既定は freeze ファイルと同じ
    # ディレクトリ = production では output/s8b-freeze/ 配下。
    marker_root = Path(marker_root) if marker_root is not None else freeze_path.parent
    manifest = verify_manifest(
        Path(manifest_path), root=root,
        freeze_document=verified.document, freeze_sha256=verified.sha256,
    )
    freeze = verified.document
    block = config_for_block(manifest, block_id)
    limits = s8b_budget.load_oracle_limits(freeze)
    manifest_sha = _canonical_sha256(manifest)
    freeze_sha = verified.sha256
    schedule_sha = manifest["schedule_sha256"]
    campaign_id = block["campaign_id"]
    run_contract = block["run_contract"]
    env_tag = run_contract["env_tag"]
    evaluate_fn = evaluate_fn or pipeline.evaluate
    prepare_fn = prepare_fn or prepare_cell
    layout = campaign_layout(campaign_id, output_root=str(output_root))

    _ensure_campaign(
        layout, manifest_sha256=manifest_sha, block_id=block_id,
        campaign_id=campaign_id, freeze_sha256=freeze_sha, marker_root=marker_root,
    )
    _append_session(layout, env_tag, "campaign-start", {
        "manifest_sha256": manifest_sha,
        "block_id": block_id,
        "campaign_id": campaign_id,
    })
    ledger_identity = {
        "manifest_sha256": manifest_sha,
        "freeze_sha256": freeze_sha,
        "schedule_sha256": schedule_sha,
    }
    s8b_budget.create_ledger(budget_path, limits=limits, **ledger_identity)

    schedule = block["schedule"]
    per_row_bench_s = float(
        run_contract["extime"] * run_contract["reps"]
        * run_contract["bench_max_rounds"]
    )
    reserved_bench_s = per_row_bench_s * len(schedule)
    by_holdout_reserved: dict[str, float] = {}
    for row in schedule:
        by_holdout_reserved[row["holdout_id"]] = (
            by_holdout_reserved.get(row["holdout_id"], 0.0) + per_row_bench_s
        )
    reserved_iso = _iso_now()

    # 事前一括 reservation。確保できなければ一行も走らせず terminal を耐久化する
    # (§5.2 の予算不足 = 未実施 arm を対称に判定不能へ倒す契約)。
    try:
        s8b_budget.reserve(
            budget_path, reserved_bench_s=reserved_bench_s,
            by_holdout_reserved=by_holdout_reserved, reserved_iso=reserved_iso,
            **ledger_identity,
        )
    except s8b_budget.BudgetError as exc:
        s8b_budget.mark_exhausted(
            budget_path, requested_bench_s=reserved_bench_s,
            by_holdout_requested=by_holdout_reserved, reserved_iso=reserved_iso,
            **ledger_identity,
        )
        _append_session(layout, env_tag, "budget-exhausted-before-attempt", {
            "reason": str(exc),
            "reserved_bench_s": reserved_bench_s,
        })
        return {
            "status": "budget_exhausted_before_attempt",
            "allowed": True,
            "refusals": [],
            "campaign_id": campaign_id,
            "manifest_sha256": manifest_sha,
            "freeze_sha256": freeze_sha,
            "schedule_sha256": schedule_sha,
            "completed_trials": 0,
            "events": _session_events(layout),
        }

    completed = 0
    # 強い completed 定義の未達行 (binding-refused / prepare 恒久失敗 / 未実行) を集める。
    # 1 件でも残れば terminal は protocol_violation に倒す (fail-closed)。
    unresolved_rows: list[int] = []
    error_stopped = False
    error_message: Optional[str] = None
    for position, row in enumerate(schedule):
        schedule_index = row["schedule_index"]
        holdout_id = row["holdout_id"]
        configuration_id = row["configuration_id"]
        row_done = False
        for attempt in (1, 2):
            started_iso = _iso_now()
            attempt_started = time.monotonic()
            _append_session(layout, env_tag, "trial-start", {
                "schedule_index": schedule_index,
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "attempt": attempt,
            })
            evaluate_started = False
            try:
                with _prepared_binding(
                        freeze=freeze, holdout_id=holdout_id,
                        configuration_id=configuration_id,
                        ccbench_pin=run_contract["ccbench_pin"],
                        prepare_fn=prepare_fn) as (actual_binding, prepared):
                    expected_binding = _expected_binding(
                        manifest, holdout_id, configuration_id,
                    )
                    if _canonical_bytes(actual_binding) != _canonical_bytes(expected_binding):
                        _append_session(layout, env_tag, "binding-refused", {
                            "schedule_index": schedule_index,
                            "reason": "manifest binding_identity と再実体化 identity が不一致",
                        })
                        unresolved_rows.append(schedule_index)
                        row_done = True
                        break

                    prepared_for_eval = PreparedCell(
                        genome=prepared.genome,
                        src_token=prepared.src_token,
                        ccbench_dir=prepared.ccbench_dir,
                        cache_root=str(output_root / "s8b-build-cache"),
                    )
                    perf = _perf_for_holdout(freeze, holdout_id, run_contract)
                    before = len(wal.read_records(layout))
                    evaluate_started = True
                    try:
                        result = evaluate_fn(
                            prepared_for_eval.genome, layout, env_tag,
                            run_contract["ccbench_pin"], perf,
                            run_contract["clocks"],
                            numactl=NUMACTL,
                            correctness=None,
                            extra_correctness=[(
                                pipeline.S2_TAG, pipeline.s2_correctness_workload(),
                            )],
                            do_bench=True,
                            do_settle=True,
                            src_token=prepared_for_eval.src_token,
                            log=lambda _message: None,
                            ccbench_dir=prepared_for_eval.ccbench_dir,
                            cache_root=prepared_for_eval.cache_root,
                            screening=None,
                            bench_max_rounds=run_contract["bench_max_rounds"],
                        )
                    except Exception as exc:
                        result = pipeline.EvalResult(
                            genome=prepared_for_eval.genome,
                            variant=pipeline.variant_id(
                                prepared_for_eval.genome, prepared_for_eval.src_token),
                            certified=False, aborted=True,
                            notes=[f"evaluate exception: {type(exc).__name__}: {exc}"],
                        )
                    new_records = wal.read_records(layout)[before:]
                    abort_payload, bench_s = _trial_measurements(new_records)
                    try:
                        outcome = _outcome_for(result, abort_payload)
                    except _UnknownAbortReason as exc:
                        _append_session(layout, env_tag, "deviation", {
                            "message": str(exc),
                            "kind": "unknown-abort-reason",
                            "schedule_index": schedule_index,
                            "abort_reason": exc.reason,
                        })
                        error_stopped = True
                        error_message = str(exc)
                        row_done = True
                        break
            except Exception as exc:
                if evaluate_started:
                    _append_session(layout, env_tag, "deviation", {
                        "message": f"evaluate 後の materializer cleanup 失敗: {type(exc).__name__}: {exc}",
                    })
                    raise
                if attempt == 1 and _is_transient_prepare_failure(exc):
                    _append_session(layout, env_tag, "retry", {
                        "schedule_index": schedule_index,
                        "attempt": 2,
                        "reason": f"prepare {type(exc).__name__}: {exc}",
                    })
                    continue
                _append_session(layout, env_tag, "binding-refused", {
                    "schedule_index": schedule_index,
                    "reason": f"prepare {type(exc).__name__}: {exc}",
                })
                unresolved_rows.append(schedule_index)
                row_done = True
                break

            if error_stopped or row_done:
                break
            finished_iso = _iso_now()
            wall_s = float(max(0.0, time.monotonic() - attempt_started))
            _append_session(layout, env_tag, "trial-result", {
                "schedule_index": schedule_index,
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "attempt": attempt,
                "outcome": outcome,
                "excluded_reason": None,
                "screen_outcome": "not_enabled",
            })
            completed += 1
            budget_entry = {
                "campaign_id": campaign_id,
                "block_id": block_id,
                "schedule_index": schedule_index,
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "attempt": attempt,
                "outcome": outcome,
                "bench_s": bench_s,
                "wall_s": wall_s,
                "started_iso": started_iso,
                "finished_iso": finished_iso,
            }
            # reservation 済み枠内の実測計上。枠超過は protocol violation として fail-closed。
            try:
                s8b_budget.append_entry(
                    budget_path, entry=budget_entry, **ledger_identity,
                )
            except s8b_budget.BudgetError as exc:
                _append_session(layout, env_tag, "deviation", {
                    "message": f"実測 bench が予約枠を超過し台帳に拒否された: {exc}",
                    "kind": "reservation-envelope-exceeded",
                    "schedule_index": schedule_index,
                    "bench_s": bench_s,
                    "reserved_bench_s": reserved_bench_s,
                })
                error_stopped = True
                error_message = str(exc)
                row_done = True
                break
            row_done = True
            break
        if error_stopped:
            break
        if not row_done:
            raise OracleDriverError(f"schedule_index={schedule_index} が終端に到達しない")

    if error_stopped:
        # 内部逸脱 (未分類 abort / reservation 枠超過)。精算せず予約枠を非解放の
        # まま残す (fail-closed)。terminal status は internal-error。
        status = "error"
    elif completed == len(schedule) and not unresolved_rows:
        # 強い completed 定義: 全予定行が一意 terminal outcome + budget entry を
        # 耐久化した。held reservation を実測へ確定し未使用枠を解放する。
        s8b_budget.settle(
            budget_path, settled_iso=_iso_now(), **ledger_identity,
        )
        status = "completed"
    else:
        # 1 行以上が binding-refused / prepare 恒久失敗で terminal outcome を
        # 得ていない。強い completed 定義を満たさず protocol_violation に倒す。
        # 精算せず予約枠を held のまま残す (fail-closed)。
        _append_session(layout, env_tag, "protocol-violation", {
            "unresolved_rows": unresolved_rows,
            "completed_trials": completed,
            "scheduled_rows": len(schedule),
        })
        status = "protocol_violation"

    return {
        "status": status,
        "allowed": True,
        "refusals": [],
        "campaign_id": campaign_id,
        "manifest_sha256": manifest_sha,
        "freeze_sha256": freeze_sha,
        "schedule_sha256": schedule_sha,
        "completed_trials": completed,
        **({"error": error_message} if error_message is not None else {}),
        **({"unresolved_rows": unresolved_rows}
           if status == "protocol_violation" else {}),
        "events": _session_events(layout),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8b oracle 実行 gate / block driver")
    subparsers = parser.add_subparsers(dest="command", required=True)
    gate = subparsers.add_parser("gate-check")
    gate.add_argument("--freeze", type=Path, required=True)
    gate.add_argument("--manifest", type=Path)
    gate.add_argument("--root", type=Path, default=ROOT)

    run = subparsers.add_parser("run-block")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--block-id", required=True)
    run.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE_PATH)
    run.add_argument("--root", type=Path, default=ROOT)
    run.add_argument("--output-root", type=Path, default=Path(repo_output_root()))
    # 実走済みマーカーの置き場は CLI から上書きできない (freeze ファイルと同じ
    # ディレクトリ = production では output/s8b-freeze/ 配下に固定)。R6: --output-root を
    # 変えても同じ場所を指すため resume 拒否を出力先付け替えで迂回できない。--budget と
    # 同じ判断 (別 path 指定 = fail-open) で CLI 面から撤去。run_block の引数はテスト専用
    # --budget override は廃止。台帳 path は canonical 固定 (別 path 指定による
    # 総枠複製 = fail-open を塞ぐ。T 層項 6)。
    return parser


# terminal status → CLI 終了コードの固定表。rc 優先順位:
# internal-error(1) > protocol_violation(3) > budget-refused(2) > completed(0)。
# gate-refused も rc 2。ここに無い status は fail-closed で internal-error(1)。
_EXIT_CODE_BY_STATUS = {
    "completed": 0,
    "error": 1,  # 内部逸脱 = internal-error
    "protocol_violation": 3,
    "budget_exhausted_before_attempt": 2,  # budget-refused
    "refused": 2,  # gate-refused
}


def _exit_code(status: object) -> int:
    """run_block / gate の terminal status を CLI 終了コードへ射影する。

    rc 優先順位 = internal-error(1) > protocol_violation(3) > budget-refused(2)
    > completed(0)。gate-refused も rc 2。未知・欠測 status は fail-closed で
    internal-error(1) に倒す。
    """
    return _EXIT_CODE_BY_STATUS.get(status, 1)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "gate-check":
            decision = gate_check(
                freeze_path=args.freeze, manifest_path=args.manifest, root=args.root,
            )
            print(json.dumps(asdict(decision), ensure_ascii=False, sort_keys=True))
            return 0 if decision.allowed else _exit_code("refused")
        result = run_block(
            manifest_path=args.manifest, block_id=args.block_id,
            freeze_path=args.freeze, root=args.root,
            output_root=args.output_root, budget_path=DEFAULT_BUDGET_PATH,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return _exit_code(result.get("status"))
    except Exception as exc:
        print(json.dumps({
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
