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

from campaign import pipeline, s8b_budget, wal  # noqa: E402
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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise OracleDriverError(f"sha256 対象を読めない: {path}: {exc}") from exc
    return digest.hexdigest()


def _load_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OracleDriverError(f"JSON を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OracleDriverError(f"JSON top-level が object でない: {path}")
    return value


def _resolve_recorded_path(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def gate_check(*, freeze_path, manifest_path=None, root) -> GateDecision:
    """実走前の独立 gate を順番に全件検査し、全拒否理由を返す。"""
    freeze_path = Path(freeze_path)
    root = Path(root)
    refusals: list[str] = []
    freeze: Optional[dict] = None

    try:
        freeze = _load_json_object(freeze_path)
    except Exception as exc:
        refusals.append(f"holdout-freeze-verify: {type(exc).__name__}: {exc}")
    else:
        if freeze.get("floor") is None and freeze.get("budget") is None:
            try:
                # v1 verifier は floor/budget がともに null の freeze だけを対象にする。
                s8b_holdout_freeze.verify(freeze_path, root=root)
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
            verify_manifest(manifest_path, root=root)
        except Exception as exc:
            refusals.append(f"manifest-verify: {type(exc).__name__}: {exc}")
        try:
            manifest = _load_json_object(manifest_path)
            record = manifest.get("freeze")
            if not isinstance(record, Mapping) or not isinstance(record.get("sha256"), str):
                raise OracleDriverError("manifest.freeze.sha256 がない")
            if record["sha256"] != _file_sha256(freeze_path):
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
                     campaign_id: str) -> None:
    layout.ensure()
    preimage = _canonical_bytes({
        "manifest_sha256": manifest_sha256,
        "block_id": block_id,
        "campaign_id": campaign_id,
    }).decode("utf-8")
    stored = wal.read_lock(layout)
    if stored is None:
        wal.write_lock(layout, preimage)
        stored = wal.read_lock(layout)
    if stored != preimage:
        raise OracleDriverError("campaign.lock と oracle block identity が不一致")
    if wal.read_records(layout):
        raise OracleDriverError("既存 WAL を持つ oracle campaign の resume は拒否")


def run_block(
        *, manifest_path, block_id, freeze_path, root, output_root, budget_path,
        evaluate_fn=None, prepare_fn=None) -> dict:
    """一つの immutable block を直列実行する。gate 拒否時は一切書き込まない。"""
    decision = gate_check(
        freeze_path=freeze_path, manifest_path=manifest_path, root=root,
    )
    if not decision.allowed:
        return {"status": "refused", **asdict(decision)}

    root = Path(root)
    output_root = Path(output_root)
    budget_path = Path(budget_path)
    manifest = verify_manifest(Path(manifest_path), root=root)
    freeze = _load_json_object(Path(freeze_path))
    block = config_for_block(manifest, block_id)
    limits = s8b_budget.load_oracle_limits(freeze)
    manifest_sha = _canonical_sha256(manifest)
    campaign_id = block["campaign_id"]
    run_contract = block["run_contract"]
    env_tag = run_contract["env_tag"]
    evaluate_fn = evaluate_fn or pipeline.evaluate
    prepare_fn = prepare_fn or prepare_cell
    layout = campaign_layout(campaign_id, output_root=str(output_root))

    _ensure_campaign(
        layout, manifest_sha256=manifest_sha, block_id=block_id,
        campaign_id=campaign_id,
    )
    _append_session(layout, env_tag, "campaign-start", {
        "manifest_sha256": manifest_sha,
        "block_id": block_id,
        "campaign_id": campaign_id,
    })
    s8b_budget.create_ledger(
        budget_path, manifest_sha256=manifest_sha, limits=limits,
    )

    completed = 0
    budget_stopped = False
    error_stopped = False
    error_message: Optional[str] = None
    schedule = block["schedule"]
    required_bench_s = float(
        run_contract["extime"] * run_contract["reps"]
        * run_contract["bench_max_rounds"]
    )
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
                        row_done = True
                        break

                    ledger = s8b_budget.read_ledger(
                        budget_path, manifest_sha256=manifest_sha,
                    )
                    try:
                        s8b_budget.assert_available(
                            ledger, holdout_id=holdout_id,
                            required_bench_s=required_bench_s,
                        )
                    except s8b_budget.BudgetError as exc:
                        _append_session(layout, env_tag, "budget-refused", {
                            "schedule_index": schedule_index, "reason": str(exc),
                        })
                        for remaining in schedule[position + 1:]:
                            _append_session(layout, env_tag, "trial-skipped", {
                                "schedule_index": remaining["schedule_index"],
                                "reason": "先行 schedule 行の budget-refused により block 停止",
                            })
                        budget_stopped = True
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
                row_done = True
                break

            if budget_stopped or error_stopped or row_done:
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
            try:
                s8b_budget.append_entry(
                    budget_path, manifest_sha256=manifest_sha,
                    entry=budget_entry,
                )
            except s8b_budget.BudgetError as exc:
                _append_session(layout, env_tag, "deviation", {
                    "message": f"実測 bench debit が予算台帳に拒否された: {exc}",
                    "kind": "budget-debit-refused",
                    "schedule_index": schedule_index,
                    "bench_s": bench_s,
                    "reserved_bench_s": required_bench_s,
                })
                _append_session(layout, env_tag, "budget-refused", {
                    "schedule_index": schedule_index, "reason": str(exc),
                })
                for remaining in schedule[position + 1:]:
                    _append_session(layout, env_tag, "trial-skipped", {
                        "schedule_index": remaining["schedule_index"],
                        "reason": "先行 schedule 行の budget-refused により block 停止",
                    })
                budget_stopped = True
                row_done = True
                break
            row_done = True
            break
        if budget_stopped or error_stopped:
            break
        if not row_done:
            raise OracleDriverError(f"schedule_index={schedule_index} が終端に到達しない")

    return {
        "status": ("error" if error_stopped else
                   "budget-refused" if budget_stopped else "completed"),
        "allowed": True,
        "refusals": [],
        "campaign_id": campaign_id,
        "manifest_sha256": manifest_sha,
        "completed_trials": completed,
        **({"error": error_message} if error_message is not None else {}),
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
    run.add_argument("--budget", type=Path, default=DEFAULT_BUDGET_PATH)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "gate-check":
            decision = gate_check(
                freeze_path=args.freeze, manifest_path=args.manifest, root=args.root,
            )
            print(json.dumps(asdict(decision), ensure_ascii=False, sort_keys=True))
            return 0 if decision.allowed else 2
        result = run_block(
            manifest_path=args.manifest, block_id=args.block_id,
            freeze_path=args.freeze, root=args.root,
            output_root=args.output_root, budget_path=args.budget,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result.get("status") == "completed" else 2
    except Exception as exc:
        print(json.dumps({
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
