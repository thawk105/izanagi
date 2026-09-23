"""T-2851 transfer execution.

事前登録 v1 §2.3 / TPC-C 版 §2.3 の転記。生成・選択に使ってはならない (v1 §3.1)。
block 番号の始点は登録文に明記なし、実装の選択として 1..32 とする。

JSON minimum examples (field names and types):
freeze: {"workload":"ycsb", "sha256":"hex", "jobs":[{"cohort":1,"protocol":"silo","cell":"wh-base","identities":["R0"]}], "comparisons":[], "m_by_family":{"ycsb":0}, "binaries":{"R0":{"perf_path":"/x","perf_sha256":"hex","trace_path":"/y","trace_sha256":"hex"}}}
run-job: {"workload":"ycsb","cohort":1,"protocol":"silo","cell":"wh-base","hostname":"node","start_utc":"ISO","end_utc":"ISO","blocks":[{"block":1,"order":["R0"],"runs":{"R0":{"tps":1.0,"rc":0}}}],"completed_blocks":32,"isolation_ok":true,"separate_allocation":true,"next_action":"none"}
verify: {"workload":"ycsb","protocol":"silo","cell":"wh-base","identity":"R1","hostname":"node","status":"未確定","reason":"trace-empty","anomalies":0}
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import uuid
from typing import Mapping, Sequence

from orchestrator.calibrator import runner as calibrator
from orchestrator.campaign import pipeline
from orchestrator.verifier.core import verify_trace_dir
from orchestrator.verifier.report import result_to_dict


@dataclass(frozen=True)
class Cell:
    workload: str
    stage: str | None
    name: str
    anchor: str
    factor: str | None
    held_out: bool
    flags: dict[str, str]


def _cell(workload, stage, name, anchor, factor, flags):
    return Cell(workload, stage, name, anchor, factor, factor is not None,
                {key: str(value) for key, value in flags.items()})


def cells(workload: str, stage: str | None = None) -> tuple[Cell, ...]:
    out = []
    if workload == "ycsb" and stage is None:
        for anchor, ratio in (("wh", 5), ("bal", 50), ("rh", 95)):
            base = dict(ycsb_rratio=ratio, ycsb_zipf_skew="0.9", thread_num=48,
                        ycsb_max_ope=10, ycsb_rmw=0, ycsb_tuple_num=1000000, extime=3)
            def add(suffix, factor, **changed):
                out.append(_cell(workload, None, anchor + "-" + suffix,
                                 anchor + "-base", factor, base | changed))
            add("base", None)
            if anchor == "wh":
                add("rr25", "read_ratio", ycsb_rratio=25)
            if anchor == "rh":
                add("rr75", "read_ratio", ycsb_rratio=75)
            for suffix, factor, key, value in (
                ("skew070", "skew", "ycsb_zipf_skew", "0.7"),
                ("skew099", "skew", "ycsb_zipf_skew", "0.99"),
                ("thr12", "threads", "thread_num", 12),
                ("thr24", "threads", "thread_num", 24),
                ("ope05", "operations", "ycsb_max_ope", 5),
                ("ope20", "operations", "ycsb_max_ope", 20),
                ("rmw1", "overlap", "ycsb_rmw", 1),
            ):
                add(suffix, factor, **{key: value})
    elif workload == "tpcc" and stage in {"s1", "s2"}:
        for anchor, warehouses in (("H", 1), ("L", 48)):
            prefix = stage + "-" + anchor
            base = dict(tpcc_num_wh=warehouses, thread_num=48, tpcc_perc_payment=43,
                        tpcc_perc_order_status=0 if stage == "s1" else 4,
                        tpcc_perc_delivery=0 if stage == "s1" else 4,
                        tpcc_perc_stock_level=0 if stage == "s1" else 4,
                        tpcc_interactive_ms=0, extime=3)
            def add(suffix, factor, **changed):
                out.append(_cell(workload, stage, prefix + "-" + suffix,
                                 prefix + "-base", factor, base | changed))
            add("base", None)
            if anchor == "H":
                add("wh04", "warehouses", tpcc_num_wh=4)
            else:
                add("wh16", "warehouses", tpcc_num_wh=16)
            add("thr12", "threads", thread_num=12)
            add("thr24", "threads", thread_num=24)
            if stage == "s1":
                add("pay20", "mix", tpcc_perc_payment=20)
                add("pay70", "mix", tpcc_perc_payment=70)
            else:
                for n in (1, 10):
                    add(f"scan{n:02}", "mix", tpcc_perc_order_status=n,
                        tpcc_perc_delivery=n, tpcc_perc_stock_level=n)
    else:
        raise ValueError("workload/stage must be ycsb/None or tpcc/s1|s2")
    return tuple(out)


def known_separate(protocol: str, cell: str) -> bool:
    return protocol == "silo" and cell == "bal-rmw1"


def order_identities(identities: Sequence[str], *, workload: str,
                     stage: str | None, cohort: int, protocol: str,
                     cell: str, block: int) -> tuple[str, ...]:
    if block not in range(1, 33) or cohort not in (1, 2):
        raise ValueError("cohort/block outside plan")
    prefix = "t2851-order-v1" if workload == "ycsb" and stage is None else "t2851-tpcc-order-v1"
    if workload == "tpcc" and stage not in {"s1", "s2"}:
        raise ValueError("invalid stage")
    key = "|".join(map(str, (prefix, *((stage,) if stage else ()), cohort, protocol, cell, block)))
    ordered = sorted(set(identities))
    for i in range(len(ordered) - 1, 0, -1):
        j = int.from_bytes(hashlib.sha256(f"{key}|{i}".encode()).digest(), "big") % (i + 1)
        ordered[i], ordered[j] = ordered[j], ordered[i]
    return tuple(ordered)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _reference_for(refs, protocol, anchor):
    p = refs[protocol]
    return p.get(anchor, p) if protocol == "silo" and isinstance(p, dict) else p


def freeze_candidates(record: Mapping[str, object]) -> dict:
    workload, stage = record["workload"], record.get("stage")
    table = cells(workload, stage)
    anchors = {c.name for c in table if not c.held_out}
    groups = record["search_groups"]
    series = record["series"]
    binaries = record["binaries"]
    refs = record["references"]
    if not isinstance(record.get("selection_rule"), str) or not record["selection_rule"].strip():
        raise ValueError("selection_rule missing")
    group_keys = set()
    expected = set()
    for group in groups:
        key = (group["task"], group["method"])
        if key in group_keys or not set(group["learning_cells"]) <= anchors:
            raise ValueError("duplicate group or unregistered learning cell")
        group_keys.add(key)
        searches = group["independent_searches"]
        if len(searches) != len(set(searches)) or not searches:
            raise ValueError("invalid independent searches")
        expected.update((*key, s) for s in searches)
    seen = set()
    for item in series:
        key = (item["task"], item["method"], item["independent_search"])
        if key in seen or key not in expected or item["anchor"] not in anchors:
            raise ValueError("duplicate, unexpected series or anchor")
        if item["protocol"] not in ("silo", "mocc"):
            raise ValueError("unsupported protocol")
        chosen = item.get("selected_identity")
        failed = item.get("selection_failure")
        if bool(chosen) == bool(failed):
            raise ValueError("selected_identity and selection_failure must be exclusive")
        if chosen and chosen not in binaries:
            raise ValueError("selected identity missing binary")
        seen.add(key)
    if seen != expected:
        raise ValueError("missing series")
    for identity, pair in binaries.items():
        if not identity or any(not pair.get(k) for k in
                               ("perf_path", "perf_sha256", "trace_path", "trace_sha256")):
            raise ValueError("incomplete binary pair")
    jobs, comparisons = [], []
    m = 0
    for protocol in sorted(refs):
        if protocol not in ("silo", "mocc"):
            raise ValueError("unsupported protocol")
        for cell in table:
            ref = _reference_for(refs, protocol, cell.anchor)
            mode = ref.get("mode", "a" if workload == "ycsb" and protocol == "silo" else None)
            if mode not in ("a", "b", "c"):
                raise ValueError("reference mode missing")
            if mode == "c":
                continue
            r0 = ref["R0"]
            strong = [ref[k] for k in ("R1", "R2") if k in ref] if workload == "ycsb" and protocol == "silo" else ([ref["reference_identity"]] if mode == "a" else [])
            selected = [s["selected_identity"] for s in series
                        if s["protocol"] == protocol and s["anchor"] == cell.anchor and s.get("selected_identity")]
            identities = sorted(set([r0, *strong, *selected, *ref.get("candidate_identities", [])]))
            if any(identity not in binaries for identity in identities):
                raise ValueError("reference identity missing binary")
            for cohort in (1, 2):
                jobs.append(dict(stage=stage, cohort=cohort, protocol=protocol,
                                 cell=cell.name, identities=identities, R0=r0))
            for s in series:
                candidate = s.get("selected_identity")
                if s["protocol"] != protocol or s["anchor"] != cell.anchor or not candidate:
                    continue
                for reference in [r0, *strong]:
                    primary = reference in strong and mode == "a" and not known_separate(protocol, cell.name)
                    same = candidate == reference
                    comparisons.append(dict(stage=stage, protocol=protocol, cell=cell.name,
                                            candidate=candidate, reference=reference,
                                            series=[s["task"], s["method"], s["independent_search"]],
                                            family="primary" if primary else "descriptive",
                                            same_identity=same, known_separate=known_separate(protocol, cell.name)))
                    if primary and not same:
                        m += 1
    normalized = dict(workload=workload, stage=stage, series=series,
                      search_groups=groups, selection_rule=record["selection_rule"],
                      references=refs, binaries=binaries)
    return dict(**normalized, sha256=_sha(normalized), jobs=jobs,
                comparisons=comparisons, m_by_family={stage or "ycsb": m})


def activation_allowed(cell: Cell, freeze: Mapping, activation: Mapping | None) -> bool:
    return (not cell.held_out or bool(activation and activation.get("decision_id")
            and activation.get("freeze_sha256") == freeze.get("sha256")
            and (cell.workload != "tpcc" or
                 (activation.get("stage") == cell.stage and activation.get("certification_path")))))


def _require_activation(cell, freeze, activation):
    if not activation_allowed(cell, freeze, activation):
        raise ValueError("held-out cell activation missing or mismatched")


def cohort2_admission(*, cohort1_last_end_utc: str, cohort2_first_start_utc: str,
                      prior_hostname: str, current_hostname: str,
                      same_host_rejections: int) -> dict:
    t1 = datetime.fromisoformat(cohort1_last_end_utc.replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(cohort2_first_start_utc.replace("Z", "+00:00"))
    time_ok = t2 - t1 >= timedelta(hours=24)
    same = prior_hostname == current_hostname
    return dict(time_ok=time_ok, measure=time_ok and (not same or same_host_rejections >= 2),
                separate_allocation=not same,
                next_action="wait-24h" if not time_ok else
                ("resubmit-same-host" if same and same_host_rejections < 2 else "none"))


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _find_cell(freeze, name):
    return next(c for c in cells(freeze["workload"], freeze.get("stage")) if c.name == name)


def _flags(cell):
    return [f"-{k}={v}" for k, v in cell.flags.items()]


def _binary(freeze, identity, kind):
    pair = freeze["binaries"][identity]
    path = pair[kind + "_path"]
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != pair[kind + "_sha256"]:
        raise ValueError("binary sha256 mismatch")
    return path


_TX_RE = re.compile(r"^\s*Transaction type:\s*(\S+)\s*$")
_COUNT_RE = re.compile(r"^\s*(commits|aborts):\s*([0-9]+)\s*$")


def parse_tpcc_counts(stdout: str) -> dict | None:
    out, current = {}, None
    for line in stdout.splitlines():
        tx = _TX_RE.fullmatch(line)
        if tx:
            current = tx.group(1)
            if current in out:
                return None
            out[current] = {}
        else:
            count = _COUNT_RE.fullmatch(line)
            if count and current:
                if count.group(1) in out[current]:
                    return None
                out[current][count.group(1)] = int(count.group(2))
    return out if out and all(set(x) == {"commits", "aborts"} for x in out.values()) else None


def _probe(workload, probe=calibrator.composite_competing_probe,
           subprocess_runner=subprocess.run):
    try:
        result = probe(nonce=uuid.uuid4().hex[:12])
        if result.get("status") != "passed":
            return False
        if workload == "tpcc":
            p = subprocess_runner(["pgrep", "-af", r"tpcc_.*\.exe"],
                                 capture_output=True, text=True, timeout=10)
            return p.returncode == 1 and not p.stdout.strip()
        return True
    except Exception:
        return False


def run_job(spec: Mapping, *, subprocess_runner=subprocess.run,
            probe=calibrator.composite_competing_probe) -> dict:
    freeze = spec["freeze"]
    cell = _find_cell(freeze, spec["cell"])
    _require_activation(cell, freeze, spec.get("activation"))
    protocol, cohort = spec["protocol"], spec["cohort"]
    job = next(j for j in freeze["jobs"] if j["protocol"] == protocol and
               j["cell"] == cell.name and j["cohort"] == cohort)
    host, start = socket.gethostname(), _utc()
    result = dict(workload=cell.workload, stage=cell.stage, cohort=cohort,
                  protocol=protocol, cell=cell.name, hostname=host,
                  start_utc=start, end_utc=None, freeze_sha256=freeze["sha256"],
                  blocks=[], completed_blocks=0, isolation_ok=False,
                  separate_allocation=True, next_action="none")
    history = [h for h in spec.get("attempt_history", [])
               if h.get("stage") == cell.stage and h.get("cohort") == cohort and
               h.get("protocol") == protocol and h.get("cell") == cell.name]
    if any(h.get("completed_blocks") == 32 and h.get("isolation_ok")
           for h in history):
        raise ValueError("completed job already present in attempt history")
    if any(h.get("next_action") == "retry-exhausted" for h in history) or sum(
        h.get("next_action") in ("resubmit-isolation", "resubmit-job-failure")
        for h in history) >= 2:
        raise ValueError("job retry limit exceeded")
    retried = any(h.get("next_action") in ("resubmit-isolation", "resubmit-job-failure")
                  for h in history)
    def retry_action(reason):
        return "retry-exhausted" if retried else "resubmit-" + reason
    if cohort == 2:
        prior = spec["cohort1_record"]
        if (prior.get("stage"), prior.get("cohort"), prior.get("protocol"),
                prior.get("cell")) != (cell.stage, 1, protocol, cell.name):
            raise ValueError("cohort1_record job key mismatch")
        rejects = sum(h.get("next_action") == "resubmit-same-host" for h in history)
        gate = cohort2_admission(cohort1_last_end_utc=spec["cohort1_last_end_utc"],
                                 cohort2_first_start_utc=start,
                                 prior_hostname=prior["hostname"],
                                 current_hostname=host, same_host_rejections=rejects)
        result.update(separate_allocation=gate["separate_allocation"],
                      next_action=gate["next_action"])
        if not gate["measure"]:
            result["end_utc"] = _utc()
            return result
    if not _probe(cell.workload, probe, subprocess_runner):
        result.update(next_action=retry_action("isolation"), end_utc=_utc())
        return result
    result["isolation_ok"] = True
    perf_binaries = {identity: _binary(freeze, identity, "perf")
                     for identity in job["identities"]}
    def once(identity):
        captured = {}
        def capture(*args, **kwargs):
            p = subprocess_runner(*args, **kwargs)
            captured["stdout"] = p.stdout
            return p
        rcs = []
        try:
            metrics, _, wall = calibrator.run_once(
                perf_binaries[identity], _flags(cell), use_perf=False,
                rep_returncodes=rcs, subprocess_runner=capture)
            tps = float(metrics["throughput[tps]"])
            if rcs != [0] or not math.isfinite(tps) or tps <= 0:
                raise ValueError("unusable throughput or returncode")
            return dict(tps=tps, rc=0, walltime=wall,
                        transaction_counts=(parse_tpcc_counts(captured.get("stdout", ""))
                                            if cell.workload == "tpcc" else None))
        except Exception as exc:
            return dict(tps=None, rc=rcs[0] if rcs else None,
                        reason=type(exc).__name__ + ": " + str(exc).splitlines()[0])
    result["warmup"] = once(job["R0"])
    if result["warmup"]["tps"] is None:
        result.update(next_action=retry_action("job-failure"), end_utc=_utc())
        return result
    try:
        for block in range(1, 33):
            order = order_identities(job["identities"], workload=cell.workload,
                                     stage=cell.stage, cohort=cohort,
                                     protocol=protocol, cell=cell.name, block=block)
            result["blocks"].append(dict(block=block, order=list(order),
                                         runs={identity: once(identity) for identity in order}))
            result["completed_blocks"] = block
    except Exception as exc:
        result.update(next_action=retry_action("job-failure"), error=str(exc).splitlines()[0])
    result["isolation_ok"] = _probe(cell.workload, probe, subprocess_runner)
    if not result["isolation_ok"]:
        result["next_action"] = retry_action("isolation")
    result["end_utc"] = _utc()
    return result


def verification_status(*, completed: bool, serializable: bool | None,
                        anomalies: int | None, witness_ok: bool,
                        certified: bool) -> str:
    if anomalies is not None and anomalies >= 1 or serializable is False:
        return "失格"
    return "certified" if completed and serializable is True and anomalies == 0 and witness_ok and certified else "未確定"


def verify_candidate(spec: Mapping, *, trace_runner=pipeline._run_trace,
                     verifier=verify_trace_dir) -> dict:
    freeze = spec["freeze"]
    cell = _find_cell(freeze, spec["cell"])
    _require_activation(cell, freeze, spec.get("activation"))
    identity, protocol = spec["identity"], spec["protocol"]
    job = next(j for j in freeze["jobs"] if j["protocol"] == protocol and
               j["cell"] == cell.name and j["cohort"] == 1)
    if identity == job["R0"] or identity not in job["identities"]:
        raise ValueError("verify identity must be a non-R0 measured candidate")
    host = socket.gethostname()
    previous = spec.get("previous_record")
    result = dict(workload=cell.workload, stage=cell.stage, protocol=protocol,
                  cell=cell.name, identity=identity, hostname=host,
                  freeze_sha256=freeze["sha256"], status="未確定", reason="",
                  anomalies=None, start_utc=_utc(), end_utc=None)
    prior_attempts = [h for h in spec.get("attempt_history", [])
                      if (h.get("stage"), h.get("protocol"), h.get("cell"),
                          h.get("identity")) == (cell.stage, protocol, cell.name, identity)]
    if len(prior_attempts) >= 2:
        result["reason"] = "reverification-limit"
        result["end_utc"] = _utc()
        return result
    if prior_attempts and previous is None:
        previous = prior_attempts[-1]
    if previous:
        if previous.get("status") != "未確定" or previous.get("hostname") == host:
            result["reason"] = "reverification-not-admitted"
            result["end_utc"] = _utc()
            return result
    if cell.workload == "tpcc":
        result["reason"] = "認定経路なし"
        result["end_utc"] = _utc()
        return result
    try:
        binary = _binary(freeze, identity, "trace")
        with tempfile.TemporaryDirectory(prefix="t2851_trace_") as trace_dir:
            tr = trace_runner(binary, trace_dir, cell.flags, spec.get("clocks_per_us", 2400),
                              timeout_s=spec.get("timeout_s", 120),
                              numactl=spec.get("numactl"))
            # pipeline.py:572-613: same rc, nonempty trace, abort and two commit
            # witnesses, zero batch commits before verifier admission.
            witness_ok = (tr.returncode == 0 and tr.trace_c_lines > 0 and
                          tr.abort_counts is not None and
                          tr.commit_count_witness is not None and
                          tr.batch_commit_count_witness == 0)
            if not witness_ok:
                result["reason"] = "trace-witness-failed"
            else:
                vr = verifier(trace_dir, expected_commits=tr.commit_count_witness,
                              protocol=protocol)
                anomalies = max(len(vr.anomalies), vr.total_cycles)
                result.update(status=verification_status(
                    completed=True, serializable=vr.serializable,
                    anomalies=anomalies, witness_ok=witness_ok,
                    certified=vr.certified), anomalies=anomalies,
                    verifier=result_to_dict(vr), reason=vr.verdict)
    except Exception as exc:
        result["reason"] = type(exc).__name__ + ": " + str(exc).splitlines()[0]
    result["end_utc"] = _utc()
    return result


def _create_json(path, value):
    with open(path, "x", encoding="utf-8") as f:
        f.write(_canonical(value) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("freeze", "run-job", "verify"):
        q = sub.add_parser(name)
        q.add_argument("input")
        q.add_argument("output")
        if name != "freeze":
            q.add_argument("--activation")
            q.add_argument("--cohort1-record")
            q.add_argument("--attempt-history")
    args = p.parse_args(argv)
    try:
        spec = json.loads(Path(args.input).read_text())
        if args.command != "freeze":
            if args.activation:
                spec["activation"] = json.loads(Path(args.activation).read_text())
            if args.cohort1_record:
                spec["cohort1_record"] = json.loads(Path(args.cohort1_record).read_text())
            if args.attempt_history:
                spec["attempt_history"] = json.loads(Path(args.attempt_history).read_text())
        value = (freeze_candidates(spec) if args.command == "freeze" else
                 run_job(spec) if args.command == "run-job" else verify_candidate(spec))
        _create_json(args.output, value)
        return 0
    except (ValueError, KeyError, OSError) as exc:
        p.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
