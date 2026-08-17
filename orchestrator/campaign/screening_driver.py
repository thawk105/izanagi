# -*- coding: utf-8 -*-
"""偵察 sweep 専用の bench-first screening 組み立てと候補評価。

autonomous `loop.py` へ screening を配線せず、opt-in driver だけがこの層を使う。
"""
from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, replace
from typing import Callable, Dict, Optional, Sequence

from ..calibrator import perf_preflight as _perf_preflight
from . import buildcache, execution_guard, ident, source_digest, wal
from .build_admission import BuildRunContext
from .env_contract import AuthorizedContract
from .layout import CampaignLayout, campaign_layout, repo_output_root
from .model import (STAGE_ABORT, STAGE_BENCH_DONE, STAGE_COMMIT,
                    CampaignConfig, Genome)
from .pipeline import (AdmissionCapabilityResolver, EvalResult, PerfConfig, S2_TAG,
                       SEARCH_CONFIG_VERIFY_KEY,
                       ScreeningConfig, VERIFY_LEGACY_PLUS_S2, evaluate,
                       s2_correctness_workload, variant_id)


@dataclass(frozen=True)
class PreparedScreening:
    cfg: CampaignConfig
    layout: CampaignLayout
    screening: ScreeningConfig


def _default_calibration_dir() -> str:
    return os.path.join(repo_output_root(), "env", "linux-baremetal", "calibration")


def load_between_run_floor(workload: Dict[str, str], calibration_dir: str = "") -> float:
    """workload が完全一致する between-run JSON を一意に選び、CVをfloorとして返す。"""
    root = calibration_dir or _default_calibration_dir()
    matches = []
    for path in sorted(glob.glob(os.path.join(root, "between_run_noise_*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"floor JSONを読めない: {path}: {exc}") from exc
        stored_workload = doc.get("workload")
        if isinstance(stored_workload, dict) and {
                str(k): str(v) for k, v in stored_workload.items()} == {
                str(k): str(v) for k, v in workload.items()}:
            matches.append((path, doc))
    if len(matches) != 1:
        raise ValueError(
            "workload対応のbetween-run floor JSONは一意に必要: "
            f"workload={workload!r}, matches={[p for p, _ in matches]!r}")
    path, doc = matches[0]
    floor = (doc.get("between_run") or {}).get("cv")
    if not isinstance(floor, (int, float)) or not 0 < floor < 1:
        raise ValueError(f"between_run.cv が欠落または範囲外: {path}: {floor!r}")
    return float(floor)


def _surface_repair(result: wal.WalTailRepairResult, log) -> None:
    if result.status == "repaired":
        log("[screening] WAL tail repair: " + json.dumps({
            "status": result.status,
            "original_size": result.original_size,
            "final_size": result.final_size,
            "removed_bytes": result.removed_bytes,
            "removed_sha256": result.removed_sha256,
            "preview": result.preview,
            "receipt_path": result.receipt_path,
        }, ensure_ascii=False, sort_keys=True))


def prepare_screening_campaign(
        base_cfg: CampaignConfig, workload: Dict[str, str], baseline_ref: str,
        measure_baseline: Callable[[CampaignConfig, CampaignLayout], None], *,
        authorization_contract: AuthorizedContract,
        env_tag: str, clocks_per_us: int, numactl: Sequence[str],
        calibration_dir: str = "", output_root: str = "", k: float = 1.5,
        high_abort_factor: float = 2.0,
        reanchor_threshold_s: float = 1800.0, log=print,
        build_context: BuildRunContext) -> PreparedScreening:
    """identity焼き込み→同一campaign baseline実測→runtime config生成を一括実行する。"""
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if not baseline_ref:
        raise ValueError("baseline_ref が欠落")
    if "screening" in base_cfg.search_config:
        raise ValueError("base campaign config に既存 screening key がある")
    if k < 1.5:
        raise ValueError("k は 1.5 以上でなければならない")
    if high_abort_factor < 1.0:
        raise ValueError("high_abort_factor は 1.0 以上でなければならない")
    if reanchor_threshold_s <= 0:
        raise ValueError("reanchor_threshold_s は正でなければならない")
    floor = load_between_run_floor(workload, calibration_dir)
    policy = ident.screening_policy_search_config(
        baseline_ref, floor, k, high_abort_factor)
    cfg = replace(base_cfg, search_config={**base_cfg.search_config, **policy})
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    authorized_contract = execution_guard.require_certified_writer_authorization(
        authorization_contract,
        env_tag=env_tag,
        clocks_per_us=clocks_per_us,
        numactl=numactl,
    )
    cfg = ident.bind_environment_contract(cfg, authorized_contract)
    layout = campaign_layout(str(ident.campaign_id(cfg)), output_root).ensure()
    _surface_repair(ident.ensure_resumable_wal(
        cfg, layout, admission_policy=build_context.policy,
    ), log)

    before = sum(1 for rec in wal.read_records(layout)
                 if rec.variant == baseline_ref and rec.stage == STAGE_BENCH_DONE)
    measure_baseline(cfg, layout)
    records = [rec for rec in wal.read_records(layout) if rec.variant == baseline_ref]
    benches = [rec for rec in records if rec.stage == STAGE_BENCH_DONE]
    commits = [rec for rec in records if rec.stage == STAGE_COMMIT]
    if len(benches) <= before:
        raise ValueError("baseline を同一campaign内で新規実測できなかった")
    if not commits or commits[-1].ts <= benches[-1].ts:
        raise ValueError("baseline の最新実測がCOMMITされていない")
    bench = benches[-1]
    median = bench.payload.get("median_tps")
    abort_rate = (bench.payload.get("leading_indicators") or {}).get("abort_rate")
    measured_at = bench.ts
    if not isinstance(median, (int, float)) or median <= 0:
        raise ValueError("baseline median_tps が欠落または非正")
    if not isinstance(abort_rate, (int, float)) or abort_rate < 0:
        raise ValueError("baseline abort_rate が欠落または負")
    if not isinstance(measured_at, (int, float)) or measured_at <= 0:
        raise ValueError("baseline 測定時刻が欠落または非正")
    screening = ScreeningConfig(
        baseline_tps=float(median), baseline_ref=baseline_ref,
        baseline_measured_at=float(measured_at), floor=floor, k=k,
        baseline_abort_rate=float(abort_rate), high_abort_factor=high_abort_factor,
        reanchor_threshold_s=reanchor_threshold_s)
    ident.verify_screening_preimage(screening, wal.read_lock(layout))
    return PreparedScreening(cfg=cfg, layout=layout, screening=screening)


def evaluate_candidate(
        cfg: CampaignConfig, layout: CampaignLayout, genome: Genome,
        perf: PerfConfig, env_tag: str, clocks_per_us: int, *,
        authorization_contract: AuthorizedContract,
        build_context: BuildRunContext,
        screening: Optional[ScreeningConfig],
        capability_resolver: Optional[AdmissionCapabilityResolver] = None,
        numactl: Optional[Sequence[str]] = None, src_token: Optional[str] = None,
        do_settle: bool = False, force: bool = False, log=print,
        ccbench_dir: str = "", cache_root: str = "") -> Optional[EvalResult]:
    """sweep候補を1点評価する。forceはbaseline再アンカー専用。"""
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    authorized_contract = execution_guard.require_certified_writer_authorization(
        authorization_contract,
        env_tag=env_tag,
        clocks_per_us=clocks_per_us,
        numactl=numactl,
    )
    cfg = ident.bind_admission_policy(cfg, build_context.policy)
    cfg = ident.bind_environment_contract(cfg, authorized_contract)
    _surface_repair(ident.ensure_resumable_wal(
        cfg, layout, admission_policy=build_context.policy,
    ), log)
    _, resolved_cxx = buildcache.compilers_for_current_site()
    evidence = source_digest.resolve_evidence(
        genome,
        cfg.ccbench_commit,
        ccbench_dir=ccbench_dir,
        cxx=resolved_cxx,
    )
    if src_token is not None and src_token != evidence.src_token:
        raise ValueError("src_token が current SourceEvidence と不一致")
    src_tok = evidence.src_token
    vid = variant_id(genome, src_tok)
    state = wal.replay(layout, admission_policy=build_context.policy).get(vid)
    # transient な環境故障 abort (identity/probe-error) は permanent skip にせず再評価する
    # (loop.py と同じ retryable 契約, D25/B-3)。
    if (not force and state is not None and state.terminal
            and not state.retryable_abort):
        return None
    perf_preflight_receipt = _perf_preflight.probe_perf_availability()
    use_perf = _perf_preflight.use_perf_from_receipt(perf_preflight_receipt)
    perf_evaluate_kwargs = {}
    if not use_perf:
        perf_evaluate_kwargs = {
            "use_perf": False,
            "perf_preflight_receipt": perf_preflight_receipt,
        }
    extra_correctness = None
    if cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2:
        extra_correctness = [(S2_TAG, s2_correctness_workload())]
    try:
        return evaluate(
            genome, layout, env_tag, cfg.ccbench_commit, perf, clocks_per_us,
            numactl=numactl, do_settle=do_settle, src_token=src_tok,
            extra_correctness=extra_correctness, screening=screening, log=log,
            ccbench_dir=ccbench_dir, cache_root=cache_root,
            authorization_contract=authorization_contract,
            build_context=build_context,
            capability_resolver=capability_resolver,
            source_evidence=evidence,
            **perf_evaluate_kwargs)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:  # candidate固有失敗をWALへ隔離。loop.pyと同じ境界。
        if isinstance(exc, (wal.WalAppendError, wal.WalFramingError)):
            raise
        payload = {"reason": f"eval-exception: {type(exc).__name__}: {exc}"}
        replayed = wal.replay(layout, admission_policy=build_context.policy).get(vid)
        if replayed is not None:
            active = [
                attempt for attempt in replayed.attempts.values()
                if not attempt.committed and not attempt.aborted
            ]
            if len(active) == 1:
                payload["build_attempt_id"] = active[0].attempt_id
                if active[0].receipt_sha256 is not None:
                    payload["build_admission_receipt_sha256"] = active[0].receipt_sha256
        wal.log(layout, vid, STAGE_ABORT, env_tag, payload)
        return EvalResult(genome=genome, variant=vid, certified=False, aborted=True,
                          notes=[f"評価中の例外 → reject ({exc})"])
