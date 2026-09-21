# gate_wait_probe.py の逐語 (sha256 796d1b65d6aecd160258b9a0dd55ac49aeb0a71d3c59d6562225d3a899951914、52216 bytes)

Codex author (段 5) と fix1〜fix4 が子 worktree `author-lease-gate-wait-probe` の `tools/gate_wait_probe.py` に書いた版 (子 branch の終端 commit fdafb4c2)。repo には land しない。実行形は README §10。

```python
#!/usr/bin/env python3
"""Read-only gate log analysis; no repository imports or command execution.

Times are JST. Percentiles use nearest rank; censored and unresolved records
never enter observed-wait distributions. Script conditions describe the surviving
script, not necessarily its historical contents. Raw lines remain in JSON.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import statistics
import stat as stat_module
import sys

JST = timezone(timedelta(hours=9))
STAMP = re.compile(r"^(\d\d:\d\d:\d\d) (.*)$")
GATE = re.compile(r"^\d\d:\d\d:\d\d (?:gate: load=|attempt=\d+ leaders=)", re.M)
WAIT = {"observed-wait", "censored"}
REASONS = ("open", "leaders-only", "load-only", "both", "pigz", "unknown")


def read(path, warnings):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        warnings.append(f"{path}: {exc}")
        return ""


def iso(value):
    return value.isoformat() if value is not None else None


def dt(value):
    # Python 3.8 accepts +09:00 but not the GNU date %z form +0900.
    value = re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", value)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def until_datetime(value):
    parsed = dt(value)
    if parsed.utcoffset() != timedelta(hours=9):
        raise argparse.ArgumentTypeError("--until requires an ISO datetime with JST offset +09:00")
    return parsed.astimezone(JST)


def bounded_starts(starts, until):
    return [{"started_file": s["file"], "start": iso(s["start"]),
             "finish": iso(s["finish"]) if s["finish"] is not None
             and (until is None or s["finish"] <= until) else None,
             "finish_after_until": until is not None and s["finish"] is not None
             and s["finish"] > until}
            for s in starts if until is None or s["start"] <= until]


def number(pattern, text):
    match = re.search(pattern, text)
    return float(match[1]) if match else None


def conditions(script, directory):
    code = "\n".join(x for x in script.splitlines() if not x.lstrip().startswith("#"))
    patterns = {
        "maxl": [r"\bmaxl\s*=\s*(\d+)", r'\$leaders["\s]*-le\s+(\d+)', r"leaders\s*<=\s*(\d+)"],
        "maxload": [r"\bmaxload\s*=\s*([\d.]+)", r"\bx\s*<=?\s*([\d.]+)", r"l1\s*<=?\s*([\d.]+)"],
        "maxpigz": [r"\bmaxpigz\s*=\s*(\d+)", r"pigz\s*<=\s*(\d+)"],
        "streak_required": [r'\$streak["\s]*-ge\s+(\d+)', r'\$stable["\s]*-lt\s+(\d+)'],
    }
    result = {}
    for key, pats in patterns.items():
        values = [number(p, code) for p in pats]
        value = next((v for v in values if v is not None), None)
        result[key] = {"value": value, "source": "script" if value is not None else "unknown"}
    grep = "\n".join(x for x in code.splitlines() if "ps -eo args" in x and "grep" in x)
    mode = ("argv-anchored" if "^(python3|" in grep or "^python3( -u)?" in grep
            else "substring" if "[d]ev_wave_wait.py" in grep else "unknown")
    scope = "unknown"
    if "then recount" in code and code.count("if ! gate_open") >= 2:
        scope = "leaders+load"
    elif "recount" in code and ("count_leaders" in code or "recount=$(ps" in code):
        scope = "leaders-only"
    for key, value in (("leaders_grep", mode), ("recount_scope", scope)):
        result[key] = {"value": value, "source": "script" if value != "unknown" else "unknown"}
    result["recount_conf"] = {"value": scope == "leaders+load" and "gate.conf" in code,
                               "source": "script" if code else "unknown"}
    result["gate_conf_present"] = {"value": (directory / "gate.conf").is_file(), "source": "filesystem"}
    return result


def log_conditions(body, base):
    result = {k: dict(v) for k, v in base.items()}
    for key, pat in (("maxl", r"(?:leaders<=|maxl=)(\d+)"),
                     ("maxload", r"(?:l1<=|maxload=)([\d.]+)"),
                     ("maxpigz", r"pigz<=(\d+)")):
        value = number(pat, body)
        if value is not None:
            result[key] = {"value": value, "source": "log"}
        elif "(cond " in body and key == "maxpigz":
            result[key] = {"value": None, "source": "log", "meaning": "no pigz condition"}
    return result


def parse_lines(text, base):
    events = []
    pending = False
    active_conditions = base
    for index, raw in enumerate(text.splitlines(), 1):
        match = STAMP.match(raw)
        body = match[2] if match else raw
        event = {"line": index, "raw": raw, "clock": match[1] if match else None,
                 "kind": "other", "time": None}
        if re.match(r"(?:attempt=\d+ leaders=|gate: load=)", body):
            chain = body.startswith("gate:")
            vals = {k: float(v) for k, v in re.findall(r"\b(leaders|load1|load5|pigz|workers|streak|ok_load|ok)=(\d+(?:\.\d+)?)", body)}
            if chain:
                loads = re.search(r"load=([\d.]+)/([\d.]+)/([\d.]+)", body)
                if loads:
                    vals.update(zip(("load1", "load5", "load15"), map(float, loads.groups())))
            if all(k in vals for k in ("leaders", "load1", "load5")):
                event.update(vals)
                event["kind"] = "recount" if chain and pending else "tick"
                event["conditions"] = log_conditions(body, base)
                active_conditions = event["conditions"]
                pending = False
        elif "gate open twice" in body and "recount" in body:
            event["kind"] = "recount-intent"
            pending = True
        elif re.search(r"recount\b[^:]*:? leaders=\d+", body):
            event.update(kind="recount", leaders=number(r"leaders=(\d+)", body), conditions=active_conditions)
            pending = False
        elif "gate closed at recount" in body or "recount closed" in body:
            event["kind"] = "rejection"
            pending = False
        elif re.match(r"(?:GO attempt=\d+|attempt \d+: (?:main=|tip=))", body):
            event["kind"] = "go"
            tag = re.search(r"\btag=(\S+)", body)
            event["tag"] = tag[1] if tag else None
        elif body.startswith("merged: tip="):
            event["kind"] = "merge"
        elif re.match(r"attempt(?:=\d+| \d+:) rc=", body):
            event.update(kind="rc", rc=number(r"rc=(\d+)", body))
            pending = False
        elif re.match(r"(?:child-green with receipt\b|Automatic merge\b|Auto-merging\b|"
                      r"CONFLICT\b|check_ai_provenance:|reds:|reds not all\b|"
                      r"spool dry-run\b|no child log\b|postcheck race\b|merge conflict\b|"
                      r"merge message preflight\b|terminal-merge\b|sampler\b|"
                      r"attempt=\d+ reds:|\S+\.txt: 実装面に)", body):
            event["kind"] = "info"
        attempt = re.search(r"attempt[= ](\d+)", body)
        event["attempt"] = int(attempt[1]) if attempt else None
        events.append(event)
    return events


def dated_files(directory, warnings):
    records = []
    for path in sorted(directory.glob("acceptance-*.started.txt")):
        try:
            start = dt(read(path, warnings).strip())
            start = start.replace(tzinfo=JST) if start.tzinfo is None else start.astimezone(JST)
        except ValueError:
            warnings.append(f"invalid ISO datetime: {path}")
            continue
        finish_path = path.with_name(path.name.replace(".started.txt", ".finished.txt"))
        finish = None
        if finish_path.is_file():
            try:
                finish = dt(read(finish_path, warnings).strip())
                finish = finish.replace(tzinfo=JST) if finish.tzinfo is None else finish.astimezone(JST)
            except ValueError:
                warnings.append(f"invalid ISO datetime: {finish_path}")
        records.append({"file": str(path), "start": start, "finish": finish})
    return records


def date_events(events, mtime, starts):
    timed = [e for e in events if e["clock"]]
    backwards = sum(b["clock"] < a["clock"] for a, b in zip(timed, timed[1:]))
    day = mtime.date()
    previous = None
    for event in reversed(timed):
        if previous is not None and event["clock"] > previous:
            day -= timedelta(days=1)
        event["time"] = iso(datetime.combine(day, datetime.strptime(event["clock"], "%H:%M:%S").time(), JST))
        previous = event["clock"]
    anchors = []
    for event in timed:
        if event["kind"] != "go":
            continue
        candidates = []
        for record in starts:
            if event.get("tag") and Path(record["file"]).name != f"acceptance-{event['tag']}.started.txt":
                continue
            # A start follows GO, possibly across midnight. Compare clock distance
            # before looking at mtime, so a conflicting dated anchor is not hidden.
            clock = datetime.strptime(event["clock"], "%H:%M:%S").time()
            go = datetime.combine(record["start"].date(), clock, JST)
            if go > record["start"]:
                go -= timedelta(days=1)
            delta = (record["start"] - go).total_seconds()
            if 0 <= delta <= 600:
                candidates.append((delta, record["file"], go, record))
        if candidates:
            _, _, go, record = min(candidates)
            anchors.append((go - dt(event["time"])).days)
            event["started_file"] = record["file"]
            event["started"] = iso(record["start"])
            event["finished"] = iso(record["finish"])
    issues = []
    if backwards >= 2:
        issues.append("multiple clock reversals")
    if anchors and (len(set(anchors)) != 1 or anchors[0] != 0):
        issues.append("started anchor contradicts mtime date")
    return ("unresolved" if issues else "anchored" if anchors else "mtime-estimated"), issues


def reason(tick):
    cond = tick["conditions"]
    ml, load, pigz = (cond[k]["value"] for k in ("maxl", "maxload", "maxpigz"))
    if ml is None or load is None:
        return "unknown"
    if pigz is not None and tick.get("pigz") is None:
        return "unknown"
    if pigz is not None and tick["pigz"] > pigz:
        return "pigz"
    a, b = tick["leaders"] > ml, tick["load1"] > load
    return "both" if a and b else "leaders-only" if a else "load-only" if b else "open"


def model_candidate(ticks, recounts, maxl=None, maxload=None):
    """Same two-tick model for baseline and alternatives; None uses log/script.

    Conditions can change within a run. Unknown baseline limits cannot produce
    a comparable baseline; never silently substitute the common 1/60 variant.
    """
    streak = 0
    for i, tick in enumerate(ticks):
        ml = maxl if maxl is not None else tick["conditions"]["maxl"]["value"]
        load = maxload if maxload is not None else tick["conditions"]["maxload"]["value"]
        if ml is None or load is None:
            return None
        streak = streak + 1 if tick["leaders"] <= ml and tick["load1"] <= load else 0
        if streak < 2:
            continue
        stop = ticks[i + 1]["line"] if i + 1 < len(ticks) else math.inf
        rec = next((r for r in recounts if tick["line"] < r["line"] < stop), None)
        value = rec["leaders"] if rec else tick["leaders"]
        recount_limit = maxl if maxl is not None else (rec or tick)["conditions"]["maxl"]["value"]
        if recount_limit is None:
            return None
        if value <= recount_limit:
            return {"time": tick["time"], "recount_leaders": value,
                    "recount_source": "log" if rec else "previous-tick (推定)"}
    return None


def segments(run):
    result = []
    current = []
    last_tick = None
    retry = None

    def add(kind, start, end, events, attempt=None):
        ticks = [e for e in events if e["kind"] == "tick"]
        recounts = [e for e in events if e["kind"] == "recount"]
        rejects = sum(e["kind"] == "rejection" for e in events)
        for i, e in enumerate(events):
            if e["kind"] != "recount":
                continue
            limit = e["conditions"]["maxl"]["value"]
            # Explicit rejection and numeric rejection are one event, not two.
            next_kind = next((x["kind"] for x in events[i + 1:] if x["kind"] not in {"other", "info"}), None)
            if limit is not None and e["leaders"] > limit and next_kind != "rejection":
                rejects += 1
        seconds = (dt(end) - dt(start)).total_seconds()
        record = {"wave": run["wave"], "file": run["file"], "run_id": run["run_id"],
                  "segment_id": len(result) + 1, "kind": kind, "start": start, "end": end,
                  "seconds": seconds, "attempt": attempt, "date_status": run["date_status"],
                  "eligible": run["date_status"] != "unresolved", "tick_count": len(ticks),
                  "ticks": ticks, "recounts": recounts, "recount_rejections": rejects,
                  "conditions": [e["conditions"] for e in ticks],
                  "closed_reasons": dict(Counter(reason(t) for t in ticks)),
                  "pre_go_tick": ticks[-1] if ticks and kind == "observed-wait" else None,
                  "pre_go_recount": recounts[-1] if recounts and kind == "observed-wait" else None,
                  "hour_jst": dt(start).hour, "long_wait": kind in WAIT and seconds >= 1800,
                  "starvation_candidate": kind in WAIT and seconds >= 1800 and rejects >= 2,
                  "concurrent_wait_max": None, "concurrent_wait_pre_go": None,
                  "concurrent_run_max": None, "concurrent_run_pre_go": None,
                  "leaders_minus_runs_pre_go": None,
                  "concurrent_wait_go": None, "concurrent_go": None, "sensitivity": {}}
        if kind == "observed-wait":
            baseline = model_candidate(ticks, recounts)
            record["sensitivity_baseline"] = baseline
            record["actual_go_minus_baseline_seconds"] = (
                (dt(end) - dt(baseline["time"])).total_seconds() if baseline else None)
            record["sensitivity"]["実条件 = 模型基準"] = (
                dict(baseline, delta_seconds=0.0) if baseline else None)
            for ml in (1, 2, 3):
                for load in (60, 80):
                    found = model_candidate(ticks, recounts, ml, load)
                    if found:
                        found["delta_seconds"] = ((dt(found["time"]) - dt(baseline["time"])).total_seconds()
                                                  if baseline else None)
                    record["sensitivity"][f"maxl={ml},maxload={load}"] = found
        result.append(record)

    def close(go=None, cutoff=None):
        nonlocal current, last_tick
        if current:
            end = go["time"] if go else cutoff or next(e["time"] for e in reversed(current) if e["time"])
            add("observed-wait" if go else "censored", current[0]["time"], end, current,
                go["attempt"] if go else current[0]["attempt"])
            if cutoff and not go:
                result[-1]["end_source"] = "until"
        current, last_tick = [], None

    for event in run["events"]:
        kind = event["kind"]
        if kind == "tick":
            if last_tick and (dt(event["time"]) - dt(last_tick["time"])).total_seconds() > 600:
                close()
            if retry:
                add("retry-prep", retry["time"], event["time"], [], event["attempt"])
                retry = None
            current.append(event)
            last_tick = event
        elif kind == "go":
            close(event)
            if event.get("started"):
                add("submit-prep", event["time"], event["started"], [], event["attempt"])
                if event.get("finished") and dt(event["finished"]) >= dt(event["started"]):
                    add("run", event["started"], event["finished"], [], event["attempt"])
                elif event.get("finish_after_until"):
                    add("run", event["started"], run["until"], [], event["attempt"])
                    result[-1].update(end_source="until", censored=True)
        elif kind == "rc":
            close()
            retry = event
        elif current:
            current.append(event)
    close(cutoff=run.get("truncated_at"))
    return result


def discover(args, warnings):
    directories = {}
    for root_string in args.jobs_root + args.claude_jobs_root:
        root = Path(root_string)
        if not root.is_dir():
            warnings.append(f"root missing or not directory: {root}")
            continue
        if root_string in args.jobs_root:
            for directory in sorted(root.iterdir()):
                if directory.is_dir():
                    directories[directory.resolve()] = directory.name
        if root_string in args.claude_jobs_root:
            for tmp in sorted(root.glob("*/tmp")):
                if tmp.is_dir():
                    directories[tmp.resolve()] = f"JOBS/{tmp.parent.name}/tmp"
                    for sub in sorted(tmp.iterdir()):
                        if sub.is_dir():
                            directories[sub.resolve()] = f"JOBS/{tmp.parent.name}/tmp/{sub.name}"
    runs = []
    start_directories = []
    for directory_index, (directory, wave) in enumerate(sorted(directories.items()), 1):
        if directory_index % 100 == 0:
            print(f"scan directories={directory_index} gate_logs={len(runs)}", file=sys.stderr, flush=True)
        if wave in args.exclude_wave:
            continue
        starts = dated_files(directory, warnings)
        directory_record = {"wave": wave, "directory": str(directory),
                            "dated_runs": bounded_starts(starts, args.until),
                            "has_gate_log": False}
        start_directories.append(directory_record)
        evidence = None
        for path in sorted(directory.glob("*.log")):
            try:
                stat = path.stat()
            except OSError as exc:
                warnings.append(f"{path}: {exc}")
                continue
            if not stat_module.S_ISREG(stat.st_mode) or stat.st_size >= 2_000_000:
                continue
            mtime = datetime.fromtimestamp(stat.st_mtime, JST)
            text = read(path, warnings)
            if not GATE.search(text):
                continue
            if evidence is None:
                land_files = sorted({p for pattern in ("land*.log", "land*.stdout", "land-*.json")
                                     for p in directory.glob(pattern) if p.is_file()})
                matches = [str(p) for p in land_files if re.search(r"\blanded\b", read(p, warnings))]
                evidence = {"green_receipt": "yes" if (directory / "acceptance-receipt-green.json").is_file() else "no",
                            "land_log": "yes" if matches else "no" if land_files else "no-file",
                            "land_files": list(map(str, land_files)), "land_matches": matches}
            style = "loop" if re.search(r"^\d\d:\d\d:\d\d attempt=\d+ leaders=", text, re.M) else "chain"
            script_path = directory / ("gate-acceptance-loop.sh" if style == "loop" else "run-acceptance-gated.sh")
            script = read(script_path, warnings) if script_path.is_file() else ""
            base = conditions(script, directory)
            events = parse_lines(text, base)
            status, issues = date_events(events, mtime, starts)
            truncated = args.until is not None and any(
                e["time"] and dt(e["time"]) > args.until for e in events)
            if args.until is not None:
                # Untimed continuations follow the preceding timestamp for filtering.
                retained = []
                keep = True
                for event in events:
                    if event["time"]:
                        keep = dt(event["time"]) <= args.until
                    if not keep:
                        continue
                    if event.get("started") and dt(event["started"]) > args.until:
                        for key in ("started", "started_file", "finished"):
                            event.pop(key, None)
                    if event.get("finished") and dt(event["finished"]) > args.until:
                        event["finished"] = None
                        event["finish_after_until"] = True
                    retained.append(event)
                events = retained
                if not any(GATE.match(e["raw"]) for e in events):
                    continue
            directory_record["has_gate_log"] = True
            selection_key = (max(e["time"] for e in events if GATE.match(e["raw"]))
                             if args.until is not None else iso(mtime))
            run = {"wave": wave, "file": str(path), "run_id": str(path), "style": style,
                   "selection_key": selection_key, "until": iso(args.until),
                   "truncated_at": iso(args.until) if truncated else None,
                   "mtime": iso(mtime), "date_status": status, "date_issues": issues,
                   "conditions_script": base, "script": str(script_path) if script else None,
                   "gate_conf": read(directory / "gate.conf", warnings) if (directory / "gate.conf").is_file() else None,
                   "events": events, "other_count": sum(e["kind"] == "other" for e in events),
                   "info_count": sum(e["kind"] == "info" for e in events),
                   "land_evidence": evidence,
                   "dated_runs": directory_record["dated_runs"],
                   "running_comparison": "available" if any(e.get("finished") for e in events) else "unavailable"}
            run["conditions"] = list({json.dumps(e["conditions"], sort_keys=True): e["conditions"]
                                      for e in events if e["kind"] == "tick"}.values())
            runs.append(run)
    return runs, start_directories


def distribution(values):
    values = sorted(values)
    return {"n": len(values), "median": statistics.median(values) if values else None,
            "p90": values[math.ceil(len(values) * .9) - 1] if values else None,
            "max": max(values) if values else None,
            "min": min(values) if values else None, "sum": sum(values)}


def running_intervals(runs, start_directories, since, until):
    """Collect every since dated start, regardless of gate log presence.

    Missing ends use the corresponding GO's next rc, never a later attempt's rc.
    With neither end source, censor at the directory's last log observation/mtime.
    The current wall clock is deliberately not used, keeping output deterministic.
    """
    directories = defaultdict(list)
    for run in runs:
        directories[str(Path(run["file"]).parent)].append(run)
    result = []
    for directory in start_directories:
        directory_runs = directories[directory["directory"]]
        starts = {s["started_file"]: s for s in directory["dated_runs"]
                  if dt(s["start"]).date() >= since}
        cutoff = max([r["mtime"] for r in directory_runs] +
                     [e["time"] for r in directory_runs if r["date_status"] != "unresolved"
                      for e in r["events"] if e["time"]], default=None)
        for path, start in sorted(starts.items()):
            finish = start["finish"]
            source = "finished.txt"
            rc_candidates = []
            if start["finish_after_until"]:
                finish, source = iso(until), "until"
            elif finish is None or finish < start["start"]:
                for run in directory_runs:
                    if run["date_status"] == "unresolved":
                        continue
                    for i, event in enumerate(run["events"]):
                        if event["kind"] != "go" or event.get("started_file") != path:
                            continue
                        for after in run["events"][i + 1:]:
                            if after["kind"] == "go":
                                break
                            if after["kind"] == "rc":
                                if after["attempt"] == event["attempt"] and after["time"] >= start["start"]:
                                    rc_candidates.append(after["time"])
                                break
                finish = min(rc_candidates) if rc_candidates else max(cutoff or start["start"], start["start"])
                source = "rc (推定)" if rc_candidates else "censored (推定)"
                if until is not None and not rc_candidates:
                    finish, source = iso(until), "until"
            result.append({"wave": directory["wave"], "kind": "run",
                           "has_gate_log": directory["has_gate_log"],
                           "started_file": path, "start": start["start"], "end": finish,
                           "end_source": source, "censored": source in {"censored (推定)", "until"}})
    return result


def concurrency(records, run_intervals):
    waits = [r for r in records if r["eligible"] and r["kind"] in WAIT]
    pool = [r for r in waits if r["in_since"]]
    goes = [r for r in pool if r["kind"] == "observed-wait"]
    for record in waits:
        def count(time):
            return len({r["wave"] for r in pool if r["wave"] != record["wave"] and r["start"] <= time <= r["end"]})
        record["concurrent_wait_max"] = max((count(t["time"]) for t in record["ticks"]), default=0)
        for tick in record["ticks"]:
            tick["concurrent_run_waves"] = sorted({r["wave"] for r in run_intervals
                if r["wave"] != record["wave"] and r["start"] <= tick["time"] < r["end"]})
            tick["concurrent_runs"] = len(tick["concurrent_run_waves"])
        record["concurrent_run_max"] = max((t["concurrent_runs"] for t in record["ticks"]), default=0)
        if record["kind"] == "observed-wait":
            record["concurrent_run_pre_go"] = record["ticks"][-1]["concurrent_runs"]
            record["leaders_minus_runs_pre_go"] = record["ticks"][-1]["leaders"] - record["concurrent_run_pre_go"]
            record["concurrent_wait_pre_go"] = count(record["ticks"][-1]["time"])
            record["concurrent_wait_go"] = count(record["end"])
            record["concurrent_go"] = len({r["wave"] for r in goes if r["wave"] != record["wave"] and
                                            abs((dt(r["end"]) - dt(record["end"])).total_seconds()) <= 120})


def self_check(runs, records):
    checks = []
    for wave, expected in (
        ("dev-wave-t2610-fig10", [("censored", 3021, 2, True, 1), ("observed-wait", 853, 0, False, 1)]),
        ("dev-wave-t2814-cleanup-command", [("observed-wait", 745, 0, False, 1), ("observed-wait", 122, 0, False, 2)]),
        ("dev-wave-paper-story-20260921", [("observed-wait", 149, 0, False, 1)]),
        ("dev-wave-t2243-collection-diag", [("observed-wait", 171, 0, False, 1), ("observed-wait", 151, 0, False, 2)]),
    ):
        filename = "gate-loop-final.log" if wave in {"dev-wave-t2610-fig10", "dev-wave-t2814-cleanup-command"} else "acceptance-final.chain.log"
        selected = [r for r in runs if r["wave"] == wave and Path(r["file"]).name == filename]
        if not selected:
            checks.append({"wave": wave, "status": "skipped", "actual": [], "expected": expected})
            continue
        for run in selected:
            actual = [(r["kind"], r["seconds"], r["recount_rejections"], r["starvation_candidate"], r["attempt"])
                      for r in records if r["run_id"] == run["run_id"] and r["kind"] in WAIT]
            checks.append({"wave": wave, "file": run["file"], "status": "passed" if actual == expected and run["date_status"] != "unresolved" else "FAILED",
                           "actual": actual, "expected": expected})
    return checks


def summarize(runs, records, recent):
    groups = {"recent": [r for r in records if r["wave"] in recent],
              "since": [r for r in records if r["in_since"]],
              "since-2026-09-19": [r for r in records if r["in_since"] and r["start"][:10] >= "2026-09-19"]}
    summaries = {}
    for name, group in groups.items():
        for variant in ("all", "maxl<=1", "other-known", "unknown"):
            subset = []
            for r in group:
                limits = [c["maxl"]["value"] for c in r["conditions"]]
                category = "unknown" if not limits or any(x is None for x in limits) else "maxl<=1" if all(x <= 1 for x in limits) else "other-known"
                if variant == "all" or category == variant:
                    subset.append(r)
            waits = [r for r in subset if r["kind"] in WAIT]
            observed = [r for r in waits if r["eligible"] and r["kind"] == "observed-wait"]
            summaries[f"{name}/{variant}"] = dict(distribution([r["seconds"] for r in observed]),
                censored=sum(r["eligible"] and r["kind"] == "censored" for r in waits),
                missing=sum(not r["eligible"] for r in waits),
                rejections=sum(r["recount_rejections"] for r in waits if r["eligible"]))
    return summaries


def markdown(data):
    lines = []
    def section(title):
        lines.extend([f"## {title}", ""])
    def table(headers, rows):
        def cell(x):
            if isinstance(x, (dict, list)):
                x = json.dumps(x, ensure_ascii=False, sort_keys=True)
            return str(x if x is not None else "unknown").replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        lines.extend("| " + " | ".join(map(cell, row)) + " |" for row in rows)
        lines.append("")
    runs, records, recent = data["runs"], data["segments"], data["recent_waves"]
    grep_by_run = {r["run_id"]: r["conditions_script"]["leaders_grep"]["value"] for r in runs}
    waits = [r for r in records if r["kind"] in WAIT and r["eligible"]]
    obs = [r for r in waits if r["kind"] == "observed-wait"]
    def subset(records, group):
        return [r for r in records if (r["wave"] in recent if group == "recent" else r["in_since"])
                and (group != "since-2026-09-19" or r["start"][:10] >= "2026-09-19")]

    def value_counts(values):
        counts = Counter(values)
        return "; ".join(f"{value if value is not None else '欠測'}: {counts[value]}"
                         for value in sorted(counts, key=lambda v: (v is None, v if v is not None else 0))) or "-"
    section("母集合と観測区間")
    selection = "until 以前の最後の門番行の時刻" if data["population"]["until"] else "最終 mtime"
    lines.extend([f"母集合は残存門番 log の{selection}順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。", "",
                  "since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。", ""])
    table(["項目", "値"], data["population"].items())
    section("wave 表 (直近 20)")
    rows = []
    for wave in recent:
        wr = [r for r in runs if r["wave"] == wave]
        ws = [r for r in waits if r["wave"] == wave]
        go = [r for r in ws if r["kind"] == "observed-wait"]
        slug_type = "rulings" if "rulings" in wave else "paper" if "paper" in wave else "診断" if any(x in wave for x in ("diag", "probe", "wall-decomp")) else "実装"
        evidence = [r["land_evidence"] for r in wr]
        green = "yes" if any(e["green_receipt"] == "yes" for e in evidence) else "no"
        land = "yes" if any(e["land_log"] == "yes" for e in evidence) else "no" if any(e["land_log"] == "no" for e in evidence) else "no-file"
        rows.append([wave, slug_type, green, land, len(wr), len(go), max(0, len(go)-1),
                     sum(r["seconds"] for r in go), sum(r["kind"] == "censored" for r in ws),
                     sum(r["date_status"] == "unresolved" for r in wr), sum(r["recount_rejections"] for r in ws)])
    table(["wave", "種別 (slug、確認可能な範囲)", "green-receipt", "land-log", "起動回", "GO", "再投入", "観測待ち和 秒", "打切り", "欠測 file", "拒否"], rows)
    lines.extend(["出所: file 実在 / grep。同 dir の acceptance-receipt-green.json の実在と land*.log / land*.stdout / land-*.json の単語 landed を確認。landed の断定ではない。", ""])
    section("区間分布")
    lines.extend(["秒。p90 は nearest rank。打切り・日付未解決を observed-wait 分布に混ぜない。", ""])
    table(["母集合/条件", "n", "中央値", "p90", "最大", "打切り", "欠測区間", "拒否"],
          [[k] + [v[x] for x in ("n", "median", "p90", "max", "censored", "missing", "rejections")] for k, v in data["summary"].items()])
    table(["母集合", "wave 観測待ち和の分布 (秒)"], [[group, distribution([sum(r["seconds"] for r in obs if r["wave"] == w) for w in sorted({r["wave"] for r in obs if (r["in_since"] if group == "since" else r["wave"] in recent)})])] for group in ("recent", "since")])
    table(["区間種類", "分布 (秒)"], [[kind, distribution([r["seconds"] for r in records if r["eligible"] and r["kind"] == kind])] for kind in ("retry-prep", "submit-prep", "run")])
    section("閉門理由内訳")
    for group in ("recent", "since"):
        counts = Counter()
        seconds = Counter()
        for r in waits:
            if not (r["in_since"] if group == "since" else r["wave"] in recent):
                continue
            counts.update(r["closed_reasons"])
            for i, tick in enumerate(r["ticks"]):
                end = r["ticks"][i+1]["time"] if i+1 < len(r["ticks"]) else r["end"]
                seconds[reason(tick)] += (dt(end)-dt(tick["time"])).total_seconds()
        table([group, "tick 数", "分 (推定、直前 tick 配分、因果寄与ではない)"], [[k, counts[k], round(seconds[k]/60, 3)] for k in REASONS])
    rows = []
    for group in ("recent", "since"):
        counts, seconds = Counter(), Counter()
        for r in subset(waits, group):
            for i, tick in enumerate(r["ticks"]):
                if reason(tick) not in {"leaders-only", "both"}:
                    continue
                bucket = min(tick["concurrent_runs"], 2)
                end = r["ticks"][i+1]["time"] if i+1 < len(r["ticks"]) else r["end"]
                counts[bucket] += 1
                seconds[bucket] += (dt(end) - dt(tick["time"])).total_seconds()
        rows.extend([group, str(k) if k < 2 else "≥2", counts[k], round(seconds[k]/60, 3)] for k in range(3))
    table(["母集合", "leaders-only + both の走行数", "tick 数", "分 (推定、直前 tick 配分)"], rows)
    lines.extend(["走行数 ≥2 は実在する走行中の受入との競合。≤1 は記録 leaders と走行数の不一致 (偽 leader・log の無い走行・started/finished の欠落のいずれか、断定しない)。走行終点の rc / 打切り補完は推定であり、競合の照合もその限界を持つ。", ""])
    cross_rows, difference_rows = [], []
    for group in ("recent", "since"):
        counts, seconds, differences = Counter(), Counter(), Counter()
        for r in subset(waits, group):
            mode = grep_by_run[r["run_id"]]
            for i, tick in enumerate(r["ticks"]):
                if reason(tick) not in {"leaders-only", "both"}:
                    continue
                bucket = min(tick["concurrent_runs"], 2)
                key = (mode, bucket)
                end = r["ticks"][i+1]["time"] if i+1 < len(r["ticks"]) else r["end"]
                counts[key] += 1
                seconds[key] += (dt(end) - dt(tick["time"])).total_seconds()
                difference = tick["leaders"] - tick["concurrent_runs"]
                differences[mode, bucket, max(0, min(difference, 3))] += 1
        for mode in ("substring", "argv-anchored", "unknown"):
            for bucket, label in enumerate(("0", "1", "≥2")):
                key = (mode, bucket)
                cross_rows.append([group, mode, label, counts[key], round(seconds[key]/60, 3)])
                difference_rows.append([group, mode, label,
                                        *[differences[mode, bucket, d] for d in range(4)]])
    lines.extend(["leaders 起因閉門 (leaders-only + both): 判定方式 × 走行数。0 件の組合せも表示。", ""])
    table(["母集合", "leaders_grep", "走行数", "tick 数", "分 (推定、直前 tick 配分)"], cross_rows)
    lines.extend(["同じ leaders 起因閉門 tick の記録 leaders − 走行数の内訳。", ""])
    table(["母集合", "leaders_grep", "走行数", "差 ≤0 tick", "差 1 tick", "差 2 tick", "差 ≥3 tick"], difference_rows)
    lines.extend(["substring は他 process の argv に `dev_wave_wait.py` と ` acceptance` の両方を含むだけで数える (包み shell・codex 子の prompt 文字列を含みうる)。argv-anchored は interpreter で始まる行だけを数える。差は原因の候補であって断定ではない。", ""])
    section("GO 時点値")
    rows = []
    for group in ("recent", "since"):
        selected = subset(obs, group)
        stats = distribution([r["pre_go_tick"]["load1"] for r in selected])
        rows.append([group, len(selected), value_counts(r["pre_go_tick"]["leaders"] for r in selected),
                     value_counts((r["pre_go_recount"] or {}).get("leaders") for r in selected),
                     *[stats[k] for k in ("median", "p90", "max")]])
    table(["母集合", "GO 数", "GO 直前 leaders 値:件数", "recount leaders 値:件数",
           "GO 直前 load1 中央値", "p90", "最大"], rows)
    table(["wave", "file", "segment", "GO", "leaders", "load1", "load5", "recount leaders", "recount load1"], [[r["wave"], Path(r["file"]).name, r["segment_id"], r["end"], *[r["pre_go_tick"].get(k) for k in ("leaders", "load1", "load5")], *[(r["pre_go_recount"] or {}).get(k, "-") for k in ("leaders", "load1")]] for r in obs])
    section("同時待ち・同時 GO")
    lines.extend(["全 since 対象の観測区間で他 wave を重複排除。leaders は走行側観測であり同時待ち数を補正しない。log の無い待ち手は欠測。", ""])
    counts = Counter(r["has_gate_log"] for r in data["running_intervals"])
    lines.extend([f"走行区間の数: 門番 log のある dir {counts[True]} / 無い dir {counts[False]}", ""])
    lines.extend(["走行数は全走査対象 dir の since 日付以降に始まった started→finished を照合し、started ≤ tick < end の他 wave 数。finished 欠落時は対応 GO 後の rc、それも無ければ until、until 無指定なら同 dir の最終観測時刻 / log mtime (門番 log も無ければ started) で打切り (推定)。until より後の finished は until で打切り。GO の無い censored の GO 直前値は欠測。leaders_minus_runs_pre_go は記録 leaders − 走行数で、偽 leader 疑いの上限であり断定ではない。", ""])
    table(["母集合", "GO 直前同時待ち 値:件数", "区間最大同時待ち 値:件数 (打切り含む)",
           "同時 GO ±120秒 値:件数", "走行数 (GO 直前) 値:件数"],
          [[group, value_counts(r["concurrent_wait_pre_go"] for r in subset(obs, group)),
            value_counts(r["concurrent_wait_max"] for r in subset(waits, group)),
            value_counts(r["concurrent_go"] for r in subset(obs, group)),
            value_counts(r["concurrent_run_pre_go"] for r in subset(obs, group))] for group in ("recent", "since")])
    table(["wave", "file", "segment", "最大 他 wave", "GO 直前 tick", "GO 時点", "GO ±120秒", "走行 (GO 直前)", "leaders − 走行"], [[r["wave"], Path(r["file"]).name, r["segment_id"], *[r[k] for k in ("concurrent_wait_max", "concurrent_wait_pre_go", "concurrent_wait_go", "concurrent_go", "concurrent_run_pre_go", "leaders_minus_runs_pre_go")]] for r in waits])
    section("飢餓候補と長時間待ち")
    lines.extend(["長時間待ち ≥1800秒、飢餓候補 = 長時間待ちかつ同一区間の拒否 ≥2。事例探索条件であり一般定義ではない。", ""])
    table(["母集合", "wave", "file", "segment", "kind", "秒", "拒否", "飢餓候補",
           "同時待ち最大", "走行最大", "leaders_grep", "閉門 leaders 起因 tick / 全 tick"],
          [[group, r["wave"], Path(r["file"]).name, r["segment_id"], r["kind"], r["seconds"],
            r["recount_rejections"], r["starvation_candidate"], r["concurrent_wait_max"],
            r["concurrent_run_max"], grep_by_run[r["run_id"]],
            f"{r['closed_reasons'].get('leaders-only', 0) + r['closed_reasons'].get('both', 0)} / {r['tick_count']}"]
           for group in ("recent", "since", "since-2026-09-19") for r in subset(waits, group) if r["long_wait"]])
    rows = []
    for group in ("recent", "since", "since-2026-09-19"):
        long = [r for r in subset(waits, group) if r["long_wait"]]
        starvation = [r for r in long if r["starvation_candidate"]]
        rows.append([group, len(long), len(starvation), sum(r["kind"] == "censored" for r in starvation),
                     sum(r["kind"] == "censored" for r in long)])
    table(["母集合", "長時間待ち n", "飢餓候補 n", "うち censored n (飢餓候補)", "censored n (長時間待ち)"], rows)
    section("時間帯")
    rows = []
    for group in ("recent", "since"):
        for hour in range(24):
            stats = distribution([r["seconds"] for r in subset(obs, group) if r["hour_jst"] == hour])
            if stats["n"]:
                rows.append([group, hour, stats, sum(r["kind"] == "censored" and r["hour_jst"] == hour
                                                    for r in subset(waits, group))])
    table(["母集合", "開始 JST 時", "observed 分布 秒", "打切り"], rows)
    lines.extend(["n=0 の時間帯は省略。n は observed-wait 数。打切りのみの時間帯も省略し、打切り総数は区間分布に保持。", ""])
    section("条件変種")
    lines.extend(["script は現存版からの読取りであり過去版の証明ではない。grep 差だけでは偽陽性と断定しない。", ""])
    def condition_cell(run, key):
        values = []
        for cond in run["conditions"]:
            item = cond[key]
            value = item["value"]
            text = f"{value if value is not None else item.get('meaning', 'unknown')} ({item['source']})"
            if text not in values:
                values.append(text)
        return "; ".join(values)
    table(["wave", "file", "maxl (出所)", "maxload (出所)", "maxpigz (出所)", "leaders_grep", "recount_scope", "streak", "gate.conf", "照合可否"],
          [[r["wave"], Path(r["file"]).name, *[condition_cell(r, k) for k in ("maxl", "maxload", "maxpigz", "leaders_grep", "recount_scope", "streak_required", "gate_conf_present")], r["running_comparison"]] for r in runs])
    section("sensitivity (仮定付き参考模型、効果見積りではない)")
    lines.extend(["連続2 tickと直後の記録 recount (無ければ直前 tick の leaders (推定))。b0 は各 tick の実条件 (log/script の maxl・maxload) を同じ模型へ適用した候補 tick。差は代替候補 tick − b0 秒、負なら早く開いたであろう。", "",
                  "実 GO − b0 は jitter + recount の実費等を含む模型と実の差として別掲。pigz、他 wave の応答、jitter・位相・FIFO の効果は模型に含めない。基準不明・成立機会なしは差の分布から除外。", ""])
    sensitivity_rows = []
    keys = ["実条件 = 模型基準"] + [f"maxl={ml},maxload={load}" for ml in (1, 2, 3) for load in (60, 80)]
    for group in ("recent", "since"):
        selected = subset(obs, group)
        for key in keys + ["実 GO − b0"]:
            values = [(r["actual_go_minus_baseline_seconds"] if key == "実 GO − b0" else
                       (r["sensitivity"].get(key) or {}).get("delta_seconds")) for r in selected]
            stats = distribution([v for v in values if v is not None])
            sensitivity_rows.append([group, key, *[stats[k] for k in ("n", "min", "median", "p90", "max", "sum")], sum(v is None for v in values)])
    table(["母集合", "条件", "n", "min", "中央値", "p90", "最大", "合計 (秒)", "基準不明・成立機会なし"], sensitivity_rows)
    lines.extend(["感度分析の寄与上位: 差 (代替 − b0) が負の区間を差の小さい順。同差は wave・file・segment 順。maxl=2,maxload=60 は各母集合で最大15行、maxl=1,maxload=80 は最大10行。", ""])
    rows = []
    for group in ("recent", "since"):
        for key, limit in (("maxl=2,maxload=60", 15), ("maxl=1,maxload=80", 10)):
            candidates = []
            for r in subset(obs, group):
                delta = (r["sensitivity"].get(key) or {}).get("delta_seconds")
                if delta is not None and delta < 0:
                    candidates.append((delta, r["wave"], r["file"], r["segment_id"], r))
            for delta, _, _, _, r in sorted(candidates, key=lambda item: item[:4])[:limit]:
                rows.append([group, key, r["wave"], Path(r["file"]).name, r["segment_id"],
                             r["seconds"], delta, r["pre_go_tick"]["leaders"],
                             r["concurrent_run_pre_go"], grep_by_run[r["run_id"]]])
    table(["母集合", "条件", "wave", "file", "segment", "observed 秒", "差 (代替 − b0) 秒",
           "GO 直前 leaders", "GO 直前走行数", "leaders_grep"], rows)
    section("欠測・打切り・未知行")
    lines.extend(["24時間以上の無記録空白は時刻文字列のみから識別できない。複数逆行または錨と mtime の日付矛盾は未解決。未知行は JSON に逐語を保持。", ""])
    table(["分類", "行数"], [[kind, sum(r[kind + "_count"] for r in runs)] for kind in ("info", "other")])
    table(["file", "date_status", "理由", "info 数", "other 数", "打切り数", "GO に started 無し"], [[r["file"], r["date_status"] + (" (推定)" if r["date_status"] == "mtime-estimated" else ""), r["date_issues"], r["info_count"], r["other_count"], sum(s["kind"] == "censored" and s["run_id"] == r["run_id"] for s in records), sum(e["kind"] == "go" and not e.get("started") for e in r["events"])] for r in runs])
    table(["警告"], [[w] for w in data["warnings"]])
    section("self-check")
    lines.extend(["実 log の照合。tuple = (kind, 秒, 再カウント拒否, 飢餓候補, attempt)。", ""])
    table(["wave", "結果", "実測", "期待"], [[c["wave"], c["status"], c["actual"], c["expected"]] for c in data["self_check"]])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-root", action="append", default=[])
    parser.add_argument("--claude-jobs-root", action="append", default=[])
    parser.add_argument("--since", required=True, type=lambda s: datetime.strptime(s, "%Y-%m-%d").date())
    parser.add_argument("--recent-n", type=int, default=20)
    parser.add_argument("--until", type=until_datetime)
    parser.add_argument("--exclude-wave", action="append", default=[])
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--self-check", action="store_true", default=True)
    args = parser.parse_args()
    if args.recent_n < 1 or not (args.jobs_root or args.claude_jobs_root):
        parser.error("positive --recent-n and at least one input root required")
    warnings = []
    all_runs, start_directories = discover(args, warnings)
    all_records = [s for r in all_runs for s in segments(r)]
    checks = self_check(all_runs, all_records)
    since_runs = [r for r in all_runs if dt(r["mtime"]).date() >= args.since]
    latest = {}
    for r in since_runs:
        latest[r["wave"]] = max(latest.get(r["wave"], ""), r["selection_key"])
    recent = sorted(latest, key=lambda w: (latest[w], w), reverse=True)[:args.recent_n]
    since_ids = {r["run_id"] for r in since_runs}
    runs = [r for r in all_runs if r["run_id"] in since_ids or r["wave"] in recent]
    ids = {r["run_id"] for r in runs}
    records = [s for s in all_records if s["run_id"] in ids]
    for record in records:
        record["in_since"] = record["run_id"] in since_ids
    run_intervals = running_intervals(all_runs, start_directories, args.since, args.until)
    concurrency(records, run_intervals)
    for run in runs:
        goes = [e for e in run["events"] if e["kind"] == "go"]
        started_files = {e.get("started_file") for e in goes}
        comparable = [r for r in run_intervals if r["started_file"] in started_files]
        run["running_comparison"] = (
            "available" if comparable and None not in started_files
            and all(r["end_source"] == "finished.txt" for r in comparable)
            else "partial (started 欠測 / 終点推定)" if comparable else "unavailable")
    recent_waits = [r for r in records if r["wave"] in recent and r["eligible"] and r["kind"] in WAIT]
    population = {"since (log mtime 下限)": str(args.since), "until": iso(args.until),
                  "exclude_wave": sorted(set(args.exclude_wave)),
                  "門番 file 数": len(runs), "wave 数": len(latest),
                  "直近 wave 数": len(recent), "選択キー期間 JST": [min((latest[w] for w in recent), default=None), max((latest[w] for w in recent), default=None)],
                  "直近の観測区間 JST": [min((r["start"] for r in recent_waits), default=None), max((r["end"] for r in recent_waits), default=None)],
                  "日付未解決 file 数": sum(r["date_status"] == "unresolved" for r in runs),
                  "mtime 日付復元 file 数 (推定)": sum(r["date_status"] == "mtime-estimated" for r in runs),
                  "observed-wait 数": sum(r["eligible"] and r["kind"] == "observed-wait" for r in records),
                  "censored 数": sum(r["eligible"] and r["kind"] == "censored" for r in records)}
    data = {"schema": "gate-wait-probe/v1", "population": population, "recent_waves": recent,
            "runs": runs, "segments": records, "summary": summarize(runs, records, recent),
            "warnings": sorted(set(warnings)), "self_check": checks}
    data["running_intervals"] = run_intervals
    data["field_descriptions"] = {
        "concurrent_run_max": "区間の各 tick に走行中の他 wave 数の最大 (wave 単位重複排除)",
        "concurrent_run_pre_go": "GO 直前 tick に走行中の他 wave 数。censored / 日付未解決は null",
        "leaders_minus_runs_pre_go": "GO 直前 tick の記録 leaders − 走行数。偽 leader 疑いの上限であり断定ではない",
        "running_intervals": "全走査対象 dir の since 日付以降の started→finished。finished 欠落時は対応 GO 後の rc、無ければ until、until 無指定なら同 dir の最終観測時刻 / log mtime (門番 log も無ければ started) で打切り (推定)。until より後の finished は until で打切り。started ≤ t < end",
        "has_gate_log": "until 適用後に門番行を持つ log が同 dir にあるか。MD の数は dir 数ではなく走行区間数"}
    for path in (args.out_json, args.out_md):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(data), encoding="utf-8")
    for warning in data["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"gate logs={len(runs)} waves={len(latest)} segments={len(records)}")
    for check in checks:
        print(f"self-check {check['wave']}: {check['status']} {check['actual']}")
    print(f"JSON: {args.out_json}\nMD: {args.out_md}")
    return 3 if any(c["status"] == "FAILED" for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
```
