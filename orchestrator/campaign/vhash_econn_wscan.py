"""md_39 write-scan probe launcher. All output paths must be outside the repo.

Example (on a login node, dispatch only):
  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:10:00 --overall-grace 3900 -- python3 -m orchestrator.campaign.vhash_econn_wscan build --job repro --variant pre --third-party-cache /absolute/cache --out /absolute/builds
  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:10:00 --overall-grace 3900 -- python3 -m orchestrator.campaign.vhash_econn_wscan run --job repro --binaries /absolute/builds --shard 0 --shards 4 --output /absolute/raw
  python3 -m orchestrator.campaign.vhash_econn_wscan aggregate --raw /absolute/raw/repro-shard-0-of-4.json /absolute/raw/repro-shard-1-of-4.json /absolute/raw/repro-shard-2-of-4.json /absolute/raw/repro-shard-3-of-4.json --output /absolute/aggregate.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time

from orchestrator.campaign import patchharness, pin
from orchestrator.campaign import vhash_forwarding_prototype as base

ROOT = base.ROOT
VGT = ("patches/cicada-forwarding-variant.patch", "patches/cicada-forwarding-gc.patch",
       "patches/cicada-forwarding-target.patch")
PROBE = "patches/cicada-forwarding-wscan-probe.patch"
CAP = "patches/cicada-forwarding-wscan-cap.patch"
BROKEN = "patches/cicada-forwarding-wscan-cap-broken.patch"
PATCHES = {("count", "pre"): VGT, ("count", "fix"): (*VGT, CAP),
           ("repro", "pre"): (*VGT, PROBE),
           ("repro", "fix"): (*VGT, PROBE, CAP),
           ("repro", "broken"): (*VGT, PROBE, CAP, BROKEN)}
WSCAN_FIELDS = frozenset(("thid", "eligible", "delayed", "insertion_reached", "rounds_sum",
    "rounds_max", "rounds_ge2", "detached", "post_scan_detached", "probe_aborts",
    "k1_redirects", "k1_read_collisions", "k2_flag_raises", "reach_both", "detached_reach_both"))
CAP_FIELDS = frozenset(("thid", "publishes", "cap_limited", "cap_delta_clock_sum", "cap_no_raise"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_compute():
    if re.fullmatch(r"pegasus0[0-9]", socket.gethostname()):
        raise RuntimeError("build/run must run on a compute node")


def require_external(path):
    path = Path(path).resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("output and binary directories must be outside the repository")
    return path


def plan_runs(job, extra=False):
    if job not in ("repro", "count"):
        raise ValueError(job)
    specs = []
    if job == "repro":
        if extra:
            for rep in range(3):
                for variant in (("pre", "fix", "broken") if rep == 0 else
                                ("fix", "broken", "pre") if rep == 1 else ("broken", "pre", "fix")):
                    specs.append(dict(job=job, group="K12", variant=variant, arm="E-max", delay_us=10000,
                                      k1=True, k2=True, rep=rep, skew=.9))
        else:
            for rep in range(3):
                if rep < 2:
                    for variant in (("pre", "fix") if rep == 0 else ("fix", "pre")):
                        for delay in (0, 1000):
                            specs.append(dict(job=job, group="N", variant=variant, arm="E-max", delay_us=delay,
                                              k1=False, k2=False, rep=rep, skew=.9))
                # Rotate the K1/K12 treatment order, so shard assignment mixes treatments.
                for variant in (("pre", "fix", "broken") if rep == 0 else
                                ("fix", "broken", "pre") if rep == 1 else ("broken", "pre", "fix")):
                    specs.append(dict(job=job, group="K12", variant=variant, arm="E-max", delay_us=1000,
                                      k1=True, k2=True, rep=rep, skew=.9))
                specs.append(dict(job=job, group="K1", variant="pre", arm="E-max", delay_us=1000,
                                  k1=True, k2=False, rep=rep, skew=.9))
    else:
        for rep in range(3):
            for skew in ((.9, 0) if rep % 2 == 0 else (0, .9)):
                arms = (("E-hb", "pre"), ("E-max", "pre"), ("E-max", "fix"))
                for arm, variant in arms[rep % 3:] + arms[:rep % 3]:
                    specs.append(dict(job=job, group="count", variant=variant, arm=arm,
                                      delay_us=0, k1=False, k2=False, rep=rep, skew=skew))
    for i, spec in enumerate(specs):
        spec["order"] = i
        spec["id"] = f"{job}{'-extra' if extra else ''}-{i:02d}"
    return specs


def argv_for(binary, spec):
    base_spec = dict(gc_job=True, workload="wait_after_reads", wait_us=10000,
                     skew=spec["skew"], extime=3, gc_inter_us=10,
                     arm="stock", build_kind="gc-e-count")
    args = base._argv(Path(binary), base_spec) + base.target_arm_flags(spec["arm"])
    if spec["job"] == "repro":
        args += [f"--cicada_wscan_delay_us={spec['delay_us']}",
                 f"--cicada_wscan_k1={'true' if spec['k1'] else 'false'}",
                 f"--cicada_wscan_k2={'true' if spec['k2'] else 'false'}"]
    return args


def _line(stdout, name, fields, top):
    prefix = name + " "
    lines = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise ValueError(f"{name}: expected one line, got {len(lines)}")
    value = json.loads(lines[0], object_pairs_hook=_unique)
    if type(value) is not dict or value.keys() != top or value["schema"] != name or type(value["threads"]) is not list:
        raise ValueError(f"{name}: invalid top fields")
    ids = []
    for row in value["threads"]:
        if type(row) is not dict or row.keys() != fields or any(type(v) is not int or v < 0 for v in row.values()):
            raise ValueError(f"{name}: invalid thread fields")
        ids.append(row["thid"])
    if not ids or len(ids) != len(set(ids)):
        raise ValueError(f"{name}: missing/duplicate threads")
    for key in top - {"schema", "threads"}:
        if type(value[key]) not in (int, bool) or (type(value[key]) is int and value[key] < 0):
            raise ValueError(f"{name}: invalid {key}")
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_lines(stdout, job, variant, arm, spec=None):
    fwd, gc, longtx = base.parse_target_lines(stdout, arm, True)
    wscan = (_line(stdout, "CICADA_WSCAN_V1", WSCAN_FIELDS,
              frozenset(("schema", "delay_us", "k1", "k2", "k1_key", "gc_detach_matches", "threads")))
             if job == "repro" else None)
    if wscan is not None:
        for key in ("k1", "k2"):
            if type(wscan[key]) is not bool:
                raise ValueError(f"CICADA_WSCAN_V1: invalid {key}")
        for key in ("delay_us", "k1_key", "gc_detach_matches"):
            if type(wscan[key]) is not int or wscan[key] < 0:
                raise ValueError(f"CICADA_WSCAN_V1: invalid {key}")
        if spec is not None and any(wscan[key] != spec[key] for key in ("delay_us", "k1", "k2")):
            raise ValueError("CICADA_WSCAN_V1: argv settings mismatch")
    cap = (_line(stdout, "CICADA_WSCAN_CAP_V1", CAP_FIELDS, frozenset(("schema", "threads")))
           if variant in ("fix", "broken") else None)
    return dict(gc=gc, fwd=fwd, longtx=longtx, wscan=wscan, cap=cap)


def build(job, variant, out, cache):
    require_compute()
    out, cache = require_external(out), Path(cache).resolve(strict=True)
    patches = PATCHES[(job, variant)]
    started = time.monotonic()
    policy = base.compute._load_policy(ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    toolchain = base.compute._resolve_toolchain(policy)
    with tempfile.TemporaryDirectory(prefix="vhash-wscan-") as tmp:
        scratch = Path(tmp)
        deps = base.compute._prepare_dependencies(ROOT, policy, cache, scratch, toolchain)
        with patchharness.checkout(pin.CURRENT_PIN) as checkout:
            source = Path(checkout)
            for name in VGT:
                patchharness.apply_patch(str(ROOT / name), str(source))
            dep, dep_gate, dep_seconds = base._build_variant(source, scratch / "dependency", "gc-dependency", deps, toolchain)
            inert = None
            if patches != VGT:
                entries = {name: base._inert_entry(base._compile_entry(scratch / "dependency", name))[0]
                           for name in ("transaction.cc", "ycsb_cicada.cc")}
                before = {name: base._preprocess(entry) for name, entry in entries.items()}
            for name in patches[len(VGT):]:
                patchharness.apply_patch(str(ROOT / name), str(source))
            if patches != VGT:
                after = {name: base._preprocess(entry) for name, entry in entries.items()}
                inert = dict(before=before, after=after, matched=before == after)
                if not inert["matched"]:
                    raise RuntimeError("wscan inert preprocessing mismatch")
            binary, gates, seconds = base._build_variant(source, scratch / "count", "gc-e-count", deps, toolchain)
            dest = out / f"{job}-{variant}"
            dest.mkdir(parents=True, exist_ok=False)
            shutil.copy2(binary, dest / "ycsb_cicada.exe")
            receipt = dict(schema="vhash-econn-wscan-build/v1", job=job, variant=variant,
                pin=pin.CURRENT_PIN, head=base.checked(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.decode().strip(),
                patches=list(patches), patch_sha256={name: sha(ROOT / name) for name in patches},
                kind="gc-e-count", genome=base.GC_GENOME, binary_sha256=sha(dest / "ycsb_cicada.exe"),
                gate_receipts=gates, dependency_gate_receipts=dep_gate,
                dependency_binary_sha256=sha(dep), dependency_seconds=dep_seconds,
                inert_receipt=inert if inert is not None else {"status": "not_applicable_no_new_patch"},
                hostname=socket.gethostname(), seconds=time.monotonic()-started, build_seconds=seconds)
            (dest / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    return receipt


def _binary(binaries, job, variant):
    folder = Path(binaries) / f"{job}-{variant}"
    receipt = json.loads((folder / "receipt.json").read_text())
    binary = folder / "ycsb_cicada.exe"
    if (receipt["job"], receipt["variant"], receipt["pin"], receipt["kind"], receipt["patches"]) != (
            job, variant, pin.CURRENT_PIN, "gc-e-count", list(PATCHES[(job, variant)])):
        raise ValueError("build receipt mismatch")
    if receipt["genome"] != base.GC_GENOME:
        raise ValueError("build receipt genome mismatch")
    if set(receipt["patch_sha256"]) != set(receipt["patches"]):
        raise ValueError("build receipt patch sha256 keys mismatch")
    if sha(binary) != receipt["binary_sha256"]:
        raise ValueError("binary sha256 mismatch")
    return binary, receipt


def _compare_provenance(receipts):
    reference = receipts[0]
    for receipt in receipts:
        if any(receipt[key] != reference[key] for key in ("pin", "kind", "genome", "head")):
            raise ValueError("build receipt provenance mismatch")
        shared = receipt["patch_sha256"].keys() & reference["patch_sha256"].keys()
        if any(receipt["patch_sha256"][key] != reference["patch_sha256"][key] for key in shared):
            raise ValueError("shared patch sha256 mismatch")
        for name in ("gate_receipts", "dependency_gate_receipts"):
            gates = receipt[name]
            expected = len(base.MACROS[receipt["kind"] if name == "gate_receipts" else "gc-dependency"])
            if type(gates) is not list or len(gates) != expected or any(
                    g["admission"]["admitted"] is not True for g in gates):
                raise ValueError(f"{name}: nonadmitted gate")


def run(job, binaries, shard, shards, output, extra=False):
    require_compute()
    binaries, output = require_external(binaries), require_external(output)
    if shards < 1 or not 0 <= shard < shards:
        raise ValueError("invalid shard")
    if extra and job != "repro":
        raise ValueError("extra matrix is repro only")
    specs = plan_runs(job, extra)
    if not extra and any(not {s["variant"] for s in specs[i::shards]} >= {"pre", "fix"}
           for i in range(shards)):
        raise ValueError("every shard must mix pre and fix treatments")
    selected = specs[shard::shards]
    if not selected:
        raise ValueError("empty shard")
    verified = {variant: _binary(binaries, job, variant) for variant in {s["variant"] for s in specs}}
    _compare_provenance([receipt for _, receipt in verified.values()])
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{job}{'-extra' if extra else ''}-shard-{shard}-of-{shards}.json"
    raw = dict(schema="vhash-econn-wscan-raw/v1", job=job, shard=shard, shards=shards,
               extra=extra, planned_ids=[s["id"] for s in selected], hostname=socket.gethostname(), runs=[])
    def save():
        path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    save()
    for spec in selected:
        binary, receipt = verified[spec["variant"]]
        argv = argv_for(binary, spec)
        start = time.monotonic()
        try:
            proc = subprocess.run(argv, capture_output=True, timeout=180)
            rc, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
            error = None
        except subprocess.TimeoutExpired as exc:
            rc, stdout, stderr, error = 124, exc.stdout or b"", exc.stderr or b"", "timeout"
        except OSError as exc:
            rc, stdout, stderr, error = 127, b"", str(exc).encode(), type(exc).__name__
        record = dict(spec=spec, pin=receipt["pin"], head=receipt["head"],
            patch_sha256=receipt["patch_sha256"], patches=receipt["patches"],
            kind=receipt["kind"], genome=receipt["genome"], binary_sha256=receipt["binary_sha256"],
            argv=argv, hostname=socket.gethostname(), order=spec["order"], rc=rc,
            signal=-rc if rc < 0 else None, error=error, seconds=time.monotonic()-start,
            stdout={"sha256": hashlib.sha256(stdout).hexdigest(), "tail": stdout[-65536:].decode("utf-8", "replace")},
            stderr={"sha256": hashlib.sha256(stderr).hexdigest(), "tail": stderr[-65536:].decode("utf-8", "replace")},
            counters=None, parse_error=None)
        try:
            record["counters"] = parse_lines(stdout.decode("utf-8", "replace"), job, spec["variant"], spec["arm"], spec)
        except (ValueError, TypeError, KeyError) as exc:
            record["parse_error"] = f"{type(exc).__name__}: {exc}"
        raw["runs"].append(record)
        save()
    return path


def _sum(counter, key):
    return sum(row[key] for row in counter["threads"])


def _max(counter, key):
    return max(row[key] for row in counter["threads"])


def repro_verdict(group, variant, records, same_job_triggered):
    if not records or any(r["rc"] != 0 or r["parse_error"] or not r["counters"] or not r["counters"]["wscan"] or
                          (r["spec"]["delay_us"] > 0 and
                           (_sum(r["counters"]["wscan"], "eligible") == 0 or
                            _sum(r["counters"]["wscan"], "delayed") == 0)) for r in records):
        return "invalid"
    counter = {key: sum(_sum(r["counters"]["wscan"], key) for r in records)
               for key in WSCAN_FIELDS if key != "thid" and key != "rounds_max"}
    fired = any(_sum(r["counters"]["wscan"], "detached_reach_both") > 0 for r in records)
    reached = any(_sum(r["counters"]["wscan"], "reach_both") > 0 for r in records)
    if group == "K12" and variant in ("pre", "broken"):
        return "fired" if reached and fired else "reached_not_fired" if reached else "positive_unestablished"
    if group == "K12" and variant == "fix":
        clean_reached = any(_sum(r["counters"]["wscan"], "reach_both") > 0 and
                            _sum(r["counters"]["wscan"], "detached") +
                            _sum(r["counters"]["wscan"], "post_scan_detached") == 0 for r in records)
        return "repair_success" if clean_reached and same_job_triggered else "indeterminate"
    if max(_max(r["counters"]["wscan"], "rounds_max") for r in records) >= 2:
        return "P1_refuted"
    if counter["detached"] + counter["post_scan_detached"] > 0:
        return "unexpected_detach"
    return "Z_reached_barrier" if group == "K1" and counter["insertion_reached"] > 0 else "no_Z_reached" if group == "K1" else "P1_consistent"


def extra_round_required(records):
    return not any(r.get("counters") and r["counters"].get("wscan") and
                   _sum(r["counters"]["wscan"], "reach_both") > 0
                   for r in records if r["spec"]["group"] == "K12" and
                   r["spec"]["variant"] in ("pre", "broken"))


def aggregate(raws):
    if not raws:
        raise ValueError("no raw shards")
    job, shards, extra = raws[0]["job"], raws[0]["shards"], raws[0].get("extra", False)
    if any(r["job"] != job or r["shards"] != shards or r.get("extra", False) != extra for r in raws):
        raise ValueError("mixed raw jobs")
    provenance = [record for raw in raws for record in raw["runs"]]
    provenance_fields = ("pin", "head", "kind", "genome", "patch_sha256")
    if provenance and all(all(key in record for key in provenance_fields) for record in provenance):
        reference = provenance[0]
        for record in provenance:
            if any(record[key] != reference[key] for key in ("pin", "head", "kind", "genome")):
                raise ValueError("raw provenance mismatch")
            shared = record["patch_sha256"].keys() & reference["patch_sha256"].keys()
            if any(record["patch_sha256"][key] != reference["patch_sha256"][key] for key in shared):
                raise ValueError("raw shared patch sha256 mismatch")
    by_id = {}
    duplicate = []
    for raw in raws:
        for record in raw["runs"]:
            key = record["spec"]["id"]
            if key in by_id:
                duplicate.append(key)
            by_id[key] = dict(record, shard=raw.get("shard", 0))
    expected = plan_runs(job, extra)
    missing = [s["id"] for s in expected if s["id"] not in by_id]
    invalid = [key for key, r in by_id.items() if
               key not in {s["id"] for s in expected} or
               r["spec"] != next((s for s in expected if s["id"] == key), None) or
               not all(field in r for field in provenance_fields) or
               r.get("patches") != list(PATCHES.get((job, r["spec"].get("variant")), ())) or
               set(r.get("patch_sha256", {})) != set(r.get("patches", ())) or
               r["rc"] != 0 or r["parse_error"] or not r["counters"] or
               not r["counters"].get("gc") or not r["counters"].get("longtx") or
               (job == "repro" and not r["counters"].get("wscan")) or
               (r["spec"]["variant"] in ("fix", "broken") and not r["counters"].get("cap"))]
    output = dict(schema="vhash-econn-wscan-aggregate/v1", job=job, extra=extra,
                  missing=missing, duplicate=duplicate, invalid=invalid, complete=not (missing or duplicate or invalid), arms={})
    if job == "repro":
        output["extra_round_required"] = extra_round_required(list(by_id.values())) if not extra else False
        for group in ("N", "K1", "K12"):
            variants = ("pre", "fix") if group == "N" else ("pre",) if group == "K1" else ("pre", "fix", "broken")
            for variant in variants:
                rows = [by_id[s["id"]] for s in expected if s["group"] == group and s["variant"] == variant and s["id"] in by_id]
                planned = sum(s["group"] == group and s["variant"] == variant for s in expected)
                triggered = False
                if group == "K12" and variant == "fix":
                    triggered = any(
                        any(_sum(r["counters"]["wscan"], "reach_both") > 0 and
                            _sum(r["counters"]["wscan"], "detached") +
                            _sum(r["counters"]["wscan"], "post_scan_detached") == 0
                            for r in rows if r.get("counters") and r["counters"].get("wscan") and
                            r.get("shard") == shard) and
                        any(_sum(r["counters"]["wscan"], "detached_reach_both") > 0
                            for r in by_id.values() if r["spec"]["group"] == "K12" and
                            r["spec"]["variant"] in ("pre", "broken") and
                            r.get("shard") == shard and r.get("counters") and r["counters"].get("wscan"))
                        for shard in range(shards))
                verdict = repro_verdict(group, variant, rows, triggered) if len(rows) == planned else "invalid"
                output["arms"][f"{group}:{variant}"] = dict(planned=planned, observed=len(rows), verdict=verdict,
                    p1_run_ids=[r["spec"]["id"] for r in rows if r.get("counters") and r["counters"].get("wscan") and
                                _max(r["counters"]["wscan"], "rounds_max") >= 2] if verdict == "P1_refuted" else [],
                    totals={key: (max((_max(r["counters"]["wscan"], key) for r in rows if r.get("counters") and r["counters"].get("wscan")), default=0)
                                  if key == "rounds_max" else sum(_sum(r["counters"]["wscan"], key) for r in rows if r.get("counters") and r["counters"].get("wscan")))
                            for key in WSCAN_FIELDS if key != "thid"})
    else:
        for skew in (.9, 0):
            summaries = {}
            for arm, variant in (("E-hb", "pre"), ("E-max", "pre"), ("E-max", "fix")):
                specs = [s for s in expected if s["skew"] == skew and s["arm"] == arm and s["variant"] == variant]
                rows = [by_id[s["id"]] for s in specs if s["id"] in by_id]
                key = f"{skew:g}:{arm}:{variant}"
                valid = len(rows) == len(specs) and all(
                    r["rc"] == 0 and not r["parse_error"] and r["counters"] and
                    r["counters"].get("gc") and r["counters"].get("longtx") and
                    (variant != "fix" or r["counters"].get("cap")) for r in rows)
                metrics = None
                if valid:
                    uniform = [r["counters"]["gc"]["uniform"] for r in rows]
                    count = sum(u["count"] for u in uniform)
                    metrics = dict(lag_rts_mean_us=sum(u["lag_rts_sum_us"] for u in uniform) / count if count else None,
                                   lag_rts_max_us=max(u["lag_rts_max_us"] for u in uniform),
                                   live_mean=sum(u["live_sum"] for u in uniform) / count if count else None)
                output["arms"][key] = dict(planned=len(specs), observed=len(rows), diagnostic_instrumented_build=metrics,
                                            cap_totals={field: sum(_sum(r["counters"]["cap"], field) for r in rows)
                                                for field in CAP_FIELDS if field != "thid"} if valid and variant == "fix" else None)
                summaries[(arm, variant)] = metrics
            hb, pre, fix = (summaries[("E-hb", "pre")], summaries[("E-max", "pre")], summaries[("E-max", "fix")])
            comparison = {}
            for field in ("lag_rts_mean_us", "lag_rts_max_us", "live_mean"):
                comparison[field] = dict(fix_pre_ratio=fix[field] / pre[field] if fix and pre and pre[field] else None,
                    gain_retained_fraction=(hb[field]-fix[field]) / (hb[field]-pre[field])
                    if hb and pre and fix and all(x[field] is not None for x in (hb, pre, fix)) and hb[field] != pre[field] else None)
            output.setdefault("diagnostic_instrumented_build_comparisons", {})[f"{skew:g}"] = comparison
    output["preregistered_success"] = (output["complete"] and
        (job == "count" or all(output["arms"][f"K12:{variant}"]["verdict"] == wanted
            for variant, wanted in (("pre", "fired"), ("broken", "fired"),
                                    ("fix", "repair_success")))))
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build")
    b.add_argument("--job", required=True, choices=("repro", "count"))
    b.add_argument("--variant", required=True, choices=("pre", "fix", "broken"))
    b.add_argument("--third-party-cache", required=True, type=Path)
    b.add_argument("--out", required=True, type=Path)
    r = commands.add_parser("run")
    r.add_argument("--job", required=True, choices=("repro", "count"))
    r.add_argument("--binaries", required=True, type=Path)
    r.add_argument("--shard", required=True, type=int)
    r.add_argument("--shards", required=True, type=int)
    r.add_argument("--output", required=True, type=Path)
    r.add_argument("--extra", action="store_true")
    a = commands.add_parser("aggregate")
    a.add_argument("--raw", nargs="+", required=True, type=Path)
    a.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "build":
        build(args.job, args.variant, args.out, args.third_party_cache)
    elif args.command == "run":
        run(args.job, args.binaries, args.shard, args.shards, args.output, args.extra)
    else:
        result = aggregate([json.loads(path.read_text()) for path in args.raw])
        path = require_external(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        return 0 if result["preregistered_success"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
