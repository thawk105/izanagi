#!/usr/bin/env python3
"""使い捨て campaign transport smoke。sanctioned CLI ではない。"""
from __future__ import annotations
import argparse, dataclasses, datetime as dt, hashlib, json, os, sys, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(ROOT / "orchestrator"))
from calibrator.runner import competing_bench_pids  # noqa: E402
from campaign import p3_autonomous_workload_trial as trial, p3_s4_loop_trigger_gating as trigger  # noqa: E402
from campaign import patchharness, pipeline, site_policy  # noqa: E402
from campaign.build_admission import GeneratorId, add_coder_build_authority_argument, build_run_context  # noqa: E402
def _append(path: Path, event: str, **fields: object) -> None:
    row = {"event": event, "ts": dt.datetime.now(dt.timezone.utc).isoformat(), **fields}
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | (getattr(os, "O_NOFOLLOW", 0))
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush(); os.fsync(handle.fileno())
def _fixture(role: str, payload: dict[str, object]):
    response = trial.FixtureRoleProvider(role).invoke(invocation_id=f"wave-a-smoke-{role}", payload=payload)
    return trial.PARSERS[role](response.raw_response)
def _run_leg(leg: str, verify_config: str, progress_dir: Path, token: str,
             workload: str, flags: dict[str, str], context) -> dict[str, object]:
    progress = progress_dir / "driver-progress.jsonl"
    common = {"leg": leg, "verify_config": verify_config, "outcome": "pending", "ran": False,
              "error_type": None, "message": None, "traceback": None, "abort_record": None}
    _append(progress, "leg-start", **common)
    try:
        descriptor, binding = trial._descriptor_for(flags)
        cfg = trial._campaign_for(workload=workload, workload_flags=flags, descriptor=descriptor,
            descriptor_record=binding, trial_id=f"wave-a-smoke-leg-{leg.lower()}-{token}",
            generations=1, build_context=context)
        search_config = dict(cfg.search_config)
        if verify_config == pipeline.VERIFY_LEGACY_PLUS_S2:
            search_config[pipeline.SEARCH_CONFIG_VERIFY_KEY] = verify_config
        else:
            search_config.pop(pipeline.SEARCH_CONFIG_VERIFY_KEY, None)
        cfg = dataclasses.replace(cfg, search_config=search_config)
        planner = _fixture("planner", {}); coder = _fixture("coder", {"generation": 1})
        with patchharness.checkout(trigger.PIN, base_dir=str(ROOT / "external" / "ccbench")) as sub:
            preview = trial._preview(coder, sub=sub)
            auditor = _fixture("auditor", {"diff_digest": preview["diff_digest"]})
            _append(progress, "fixtures-parsed", leg=leg, workload=workload)
            competitors = competing_bench_pids()
            if competitors: raise RuntimeError(f"competing bench process: {competitors!r}")
            _append(progress, "single-tenancy-ok", leg=leg)
            _append(progress, "drive-iteration-start", leg=leg)
            drive_log = progress_dir / f"drive-iteration-leg{leg}.log.jsonl"
            out = trigger.drive_iteration(cfg, trial._perf_for(flags), planner, coder,
                auditor, None, sub, True,
                log=lambda line: _append(drive_log, "drive-log", line=str(line)),
                cache_root=str(Path(os.environ["TMPDIR"]) / f"campaign-build-cache-leg{leg}"),
                proposal_path=str(Path(__file__).resolve()), build_context=context)
        records = out.get("records") if isinstance(out.get("records"), dict) else {}
        complete = out.get("ran") is True and all(s in records for s in ("build_done", "verify_done", "bench_done"))
        abort_record = records.get("abort") if isinstance(records.get("abort"), dict) else None
        done = {**common, "outcome": out.get("outcome"), "ran": out.get("ran"),
                "transport_complete": complete, "campaign_id": out.get("campaign_id"),
                "layout_root": out.get("layout_root"), "abort_record": abort_record,
                "message": abort_record.get("reason") if abort_record else None}
    except BaseException as exc:
        done = {**common, "outcome": "exception", "transport_complete": False,
                "error_type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    _append(progress, "leg-done", **done)
    return done
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress-dir", required=True)
    parser.add_argument("--disposable-smoke-i-understand-this-is-not-sanctioned", action="store_true")
    add_coder_build_authority_argument(parser)
    args = parser.parse_args(argv)
    if not args.disposable_smoke_i_understand_this_is_not_sanctioned:
        parser.error("使い捨て smoke の明示 opt-in が必要")
    if trigger._current_site() != site_policy.PEGASUS_COMPUTE:
        parser.error("PEGASUS_COMPUTE 以外では実行しない")
    progress_dir = Path(args.progress_dir)
    if not progress_dir.is_absolute() or not str(progress_dir).startswith("/work/"):
        parser.error("--progress-dir は /work 配下の絶対 path が必要")
    progress_dir.mkdir(parents=True, exist_ok=True)
    progress_dir = progress_dir.resolve(strict=True)
    if not str(progress_dir).startswith("/work/"):
        parser.error("--progress-dir の解決先は /work 配下が必要")
    progress = progress_dir / "driver-progress.jsonl"
    _append(progress, "driver-start", pid=os.getpid())
    _append(progress, "site-admitted", site=site_policy.PEGASUS_COMPUTE)
    try:
        if args.coder_build_authority is None:
            raise RuntimeError("--allow-coder-derived-build の parser 発行 token が必要")
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP, coder_authority=args.coder_build_authority)
        workload, flags = next(iter(trial.WORKLOADS.items()))
        token = hashlib.sha256(f"{os.environ.get('PBS_JOBID', '')}:{progress_dir}".encode()).hexdigest()[:12]
        _run_leg("A", pipeline.VERIFY_LEGACY_PLUS_S2, progress_dir, token, workload, flags, context)
        leg_b = _run_leg("B", pipeline.LEGACY_TAG, progress_dir, token, workload, flags, context)
        rc = 0 if leg_b.get("transport_complete") is True else 1
    except BaseException as exc:
        _append(progress, "exception", error_type=type(exc).__name__, message=str(exc),
                traceback=traceback.format_exc())
        rc = 1
    _append(progress, "driver-exit", rc=rc)
    return rc
if __name__ == "__main__": raise SystemExit(main())
