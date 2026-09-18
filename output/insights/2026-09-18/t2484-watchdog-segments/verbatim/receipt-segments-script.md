# t2484_receipt_segments.py — dispatch receipt の区間別集計 script (逐語)

- 作成: Codex `role=author` (job `t2484-author-1`、wave dev-wave-t2484-watchdog-segments、2026-09-18)。repo へは commit しない (docs/ai-provenance.md の実装面規約)。実体は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-watchdog-segments/t2484_receipt_segments.py` と author branch `impl-author-dev-wave-t2484-watchdog-segments` (起動器の終端 commit 0d294fbf5)。
- sha256 `96c0c3a9396532091c57be98f808ef02400069f326ad9af2c7ed6845bb653c7b`、20,610 bytes、414 行。親が login node で `--selftest` を実走し `SELFTEST_PASS`。
- percentile は sorted list の nearest-rank (index = ceil(p/100 * n) - 1)。`post_end_s` は file mtime による近似で、`cp` 複製 (mtime が揃う) では負値になる。

```python
#!/usr/bin/env python3
"""Read-only dispatch receipt segment report (Python 3.10, standard library).

Percentiles use nearest rank: sorted_values[ceil(p / 100 * n) - 1].
Only records with parse_error are excluded from summaries. Missing optional
measurements remain null; each distribution reports its own denominator n.
queue_wait_ge ratios have denominator n_wait (observed plus derived waits),
including derived_ratio, which counts only derived lower bounds in its numerator.
Congestion n counts all accepted records in the bucket; n_wait counts known waits.
File mtimes are proxies, not dispatcher clocks; negative post_end_s is retained.
Trace span uses earliest/latest time_ns across all matching stderr files.
Inputs are never executed or modified. Overlapping roots are deduplicated by
resolved receipt path. Required receipt fields: schema_version, request
(job_name, walltime, nodes, task), outcome (kind, rc), nonempty state_history
(state, finite nonnegative elapsed_s in chronological order). request_id may be
absent before submission. Optional malformed data also sets parse_error.
"""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


KEYS = """submission_dir receipt_path schema_version request_id job_name walltime
walltime_s nodes task args_head outcome_kind outcome_rc outcome_reason
terminal_reason poll_count states last_state t_first_qstat_s t_run_first_s t_end_s
t_last_s queue_wait_s queue_wait_observed queue_wait_derived_s run_s qdel_attempted
qdel_cleanup_elapsed_s qdel_job_may_remain qdel_gate_reason preflight_gen_s
dispatch_sh_mtime receipt_mtime wall_files_s post_end_s job_trace_events
job_trace_span_s parse_error""".split()
SEGMENTS = ("t_first_qstat_s", "queue_wait_s", "queue_wait_derived_s", "run_s",
            "post_end_s", "qdel_cleanup_elapsed_s", "job_trace_span_s")
JST = timezone(timedelta(hours=9))
TRACE = "IZANAGI_DISPATCH_JOB_TRACE "


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"expected number, got {value!r}")
    if not math.isfinite(value):
        raise ValueError("nonfinite number")
    return value


def optional_number(value):
    return None if value is None else number(value)


def optional_bool(value):
    if value is not None and not isinstance(value, bool):
        raise ValueError(f"expected boolean, got {value!r}")
    return value


def string(value):
    if not isinstance(value, str):
        raise ValueError(f"expected string, got {value!r}")
    return value


def optional_string(value):
    return None if value is None else string(value)


def congestion(preflight):
    if preflight is None:
        return None
    capture = preflight.get("qstat_Q")
    if capture is None:
        return None
    header = None
    for line in string(capture.get("stdout", "")).splitlines():
        fields = line.split()
        if fields and fields[0] == "QueueName":
            header = fields
        elif fields and fields[0] == "gen_S":
            if header is None:
                raise ValueError("gen_S without QueueName header")
            return {key.lower(): int(fields[header.index(key)])
                    for key in ("TOT", "QUE", "PRR", "RUN")}
    return None


def extract(path):
    """Always return exactly KEYS, including for unreadable/malformed receipts."""
    path = Path(path)
    record = dict.fromkeys(KEYS)
    record.update(submission_dir=str(path.parent), receipt_path=str(path),
                  args_head=[], states=[], poll_count=0, job_trace_events=0)
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        record["schema_version"] = string(data["schema_version"])
        if record["schema_version"] not in ("pegasus-dispatch-receipt/v1",
                                             "pegasus-dispatch-receipt/v2"):
            raise ValueError("unsupported schema_version")
        request = data["request"]
        record["request_id"] = optional_string(data.get("request_id"))
        for key in ("job_name", "walltime", "task"):
            record[key] = string(request[key])
        walltime = re.fullmatch(r"(\d+):([0-5]\d):([0-5]\d)", record["walltime"])
        if walltime is None:
            raise ValueError("walltime must be HH:MM:SS")
        h, m, s = map(int, walltime.groups())
        record["walltime_s"] = h * 3600 + m * 60 + s
        record["nodes"] = number(request["nodes"])
        args = request.get("args", [])
        if not isinstance(args, list):
            raise ValueError("request.args must be a list")
        record["args_head"] = [os.path.basename(string(arg)) for arg in args[:3]]
        outcome = data["outcome"]
        record["outcome_kind"] = string(outcome["kind"])
        record["outcome_rc"] = number(outcome["rc"])
        record["outcome_reason"] = optional_string(outcome.get("reason"))
        record["terminal_reason"] = optional_string(data.get("terminal_reason"))
        record["queue_wait_s"] = optional_number(data.get("queue_wait_s"))
        record["queue_wait_observed"] = optional_bool(data.get("queue_wait_observed"))
        qdel = data.get("qdel") or {}
        record["qdel_attempted"] = optional_bool(qdel.get("attempted"))
        record["qdel_cleanup_elapsed_s"] = optional_number(qdel.get("cleanup_elapsed_s"))
        record["qdel_job_may_remain"] = optional_bool(qdel.get("job_may_remain"))
        record["qdel_gate_reason"] = optional_string((qdel.get("gate") or {}).get("reason"))
        record["preflight_gen_s"] = congestion(data.get("preflight"))
        history = data["state_history"]
        if not isinstance(history, list):
            raise ValueError("state_history must be a list")
        record["poll_count"] = len(history)
        if not history:
            raise ValueError("state_history is empty: segment boundaries unavailable")
        previous = 0
        for entry in history:
            elapsed = number(entry["elapsed_s"])
            if elapsed < previous:
                raise ValueError("state_history elapsed_s negative or nonmonotonic")
            previous = elapsed
            state = string(entry["state"])
            if not record["states"] or record["states"][-1] != state:
                record["states"].append(state)
            if state == "RUN" and record["t_run_first_s"] is None:
                record["t_run_first_s"] = elapsed
            if state == "END" and record["t_end_s"] is None:
                record["t_end_s"] = elapsed
        record["last_state"] = history[-1]["state"]
        record["t_first_qstat_s"] = history[0]["elapsed_s"]
        record["t_last_s"] = history[-1]["elapsed_s"]
        if record["queue_wait_s"] is None:
            record["queue_wait_derived_s"] = record["t_last_s"] - record["t_first_qstat_s"]
        if record["t_run_first_s"] is not None and record["t_end_s"] is not None:
            record["run_s"] = record["t_end_s"] - record["t_run_first_s"]
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError,
            OverflowError, RecursionError) as exc:
        errors.append(f"receipt: {type(exc).__name__}: {exc}")

    # Independent metadata extraction preserves useful diagnostics even on errors.
    mtimes = {}
    for key, file in (("receipt_mtime", path),
                      ("dispatch_sh_mtime", path.parent / "dispatch.sh")):
        try:
            timestamp = file.stat().st_mtime
            mtimes[key] = timestamp
            record[key] = datetime.fromtimestamp(timestamp, JST).isoformat()
        except FileNotFoundError:
            pass
        except (OSError, ValueError, OverflowError) as exc:
            errors.append(f"{key}: {exc}")
    if len(mtimes) == 2:
        record["wall_files_s"] = mtimes["receipt_mtime"] - mtimes["dispatch_sh_mtime"]
        if record["t_end_s"] is not None:
            record["post_end_s"] = record["wall_files_s"] - record["t_end_s"]
    times = []
    try:
        for stderr in sorted(path.parent.glob("izdw-*.e*")):
            with stderr.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    if not line.startswith(TRACE):
                        continue
                    record["job_trace_events"] += 1
                    try:
                        event = json.loads(line[len(TRACE):])
                        timestamp = event["time_ns"]
                        if isinstance(timestamp, bool) or not isinstance(timestamp, int):
                            raise ValueError("time_ns must be integer")
                        times.append(timestamp)
                    except (ValueError, KeyError, TypeError) as exc:
                        errors.append(f"{stderr.name} trace: {exc}")
        if len(times) >= 2:
            record["job_trace_span_s"] = (max(times) - min(times)) / 1e9
    except OSError as exc:
        errors.append(f"stderr: {exc}")
    record["parse_error"] = "; ".join(errors) or None
    return record


def distribution(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return dict(n=0, min=None, p50=None, p90=None, max=None)
    return dict(n=len(values), min=round(values[0], 1),
                p50=round(values[math.ceil(0.5 * len(values)) - 1], 1),
                p90=round(values[math.ceil(0.9 * len(values)) - 1], 1),
                max=round(values[-1], 1))


def waited(record):
    if record["queue_wait_observed"] is True and record["queue_wait_s"] is not None:
        return record["queue_wait_s"]
    return record["queue_wait_derived_s"]


def bucket(record):
    preflight = record["preflight_gen_s"]
    if preflight is None:
        return "unknown"
    que = preflight["que"]
    return "0-9" if que < 10 else "10-49" if que < 50 else "50-99" if que < 100 else "100+"


def summarize(records):
    valid = [r for r in records if r["parse_error"] is None]
    counts = Counter((r["outcome_kind"], r["outcome_reason"]) for r in valid)
    summary = dict(n_receipts=len(records), n_parse_error=len(records) - len(valid),
                   by_outcome=[dict(kind=k, reason=r, n=n) for (k, r), n in
                               sorted(counts.items(), key=lambda item: (item[0][0], item[0][1] or ""))])
    summary["distributions"] = {
        key: distribution(r[key] for r in valid
                          if key != "queue_wait_s" or r["queue_wait_observed"] is True)
        for key in SEGMENTS}
    waits = [waited(r) for r in valid if waited(r) is not None]
    derived = [r["queue_wait_derived_s"] for r in valid if r["queue_wait_derived_s"] is not None]
    summary["n_wait"] = len(waits)
    summary["queue_wait_ge"] = []
    for seconds in (300, 600, 900, 1200, 3000):
        n = sum(w >= seconds for w in waits)
        nd = sum(w >= seconds for w in derived)
        summary["queue_wait_ge"].append(dict(seconds=seconds, n=n,
            ratio=n / len(waits) if waits else None, derived_n=nd,
            derived_ratio=nd / len(waits) if waits else None))
    summary["by_congestion"] = []
    for label in ("0-9", "10-49", "50-99", "100+", "unknown"):
        group = [r for r in valid if bucket(r) == label]
        values = [waited(r) for r in group if waited(r) is not None]
        dist = distribution(values)
        summary["by_congestion"].append(dict(bucket=label, n=len(group), n_wait=len(values),
            p50=dist["p50"], p90=dist["p90"], max=dist["max"],
            queue_wait_ge_900=sum(w >= 900 for w in values)))
    summary["firings"] = [dict(submission_dir=Path(r["submission_dir"]).name,
        request_id=r["request_id"], reason=r["outcome_reason"], last_state=r["last_state"],
        t_last_s=r["t_last_s"], cleanup_elapsed_s=r["qdel_cleanup_elapsed_s"],
        preflight_que=None if r["preflight_gen_s"] is None else r["preflight_gen_s"]["que"])
        for r in valid if "timeout" in (r["outcome_reason"] or "") or r["qdel_attempted"] is True]
    return summary


def markdown(summary):
    def cell(value):
        return ("null" if value is None else str(value)).replace("|", "\\|").replace("\n", " ").replace("\r", " ")

    lines = [f"n_receipts={summary['n_receipts']}; n_parse_error={summary['n_parse_error']}; n_wait={summary['n_wait']}",
             "Ratios use n_wait; derived waits are lower bounds. Times in seconds."]

    def table(headers, rows):
        lines.append("")
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        lines.extend("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)

    table(["kind", "reason", "n"], ([r[k] for k in ("kind", "reason", "n")] for r in summary["by_outcome"]))
    table(["segment", "n", "min", "p50", "p90", "max"],
          ([key] + [d[k] for k in ("n", "min", "p50", "p90", "max")] for key, d in summary["distributions"].items()))
    for key, headers in (("queue_wait_ge", ["seconds", "n", "ratio", "derived_n", "derived_ratio"]),
                         ("by_congestion", ["bucket", "n", "n_wait", "p50", "p90", "max", "queue_wait_ge_900"]),
                         ("firings", ["submission_dir", "request_id", "reason", "last_state", "t_last_s", "cleanup_elapsed_s", "preflight_que"])):
        table(headers, ([r[h] for h in headers] for r in summary[key]))
    return "\n".join(lines)


def collect(roots):
    paths = set()
    for root in roots:
        # iterdir exposes unreadable roots as errors instead of silently ignoring them.
        for child in root.iterdir():
            if child.is_dir():
                path = child / "receipt.json"
                if path.exists() or path.is_symlink():
                    paths.add(path.resolve())
    return [extract(path) for path in sorted(paths)]


def selftest():
    root = Path(tempfile.mkdtemp(prefix="t2484-segments-"))
    try:
        for name, history in (("a", [(10, "QUE"), (20, "QUE"), (310, "RUN"), (350, "END")]),
                              ("b", [(10, "QUE"), (910, "QUE")]), ("c", [])):
            directory = root / name
            directory.mkdir()
            data = dict(schema_version="pegasus-dispatch-receipt/v2", request_id=name,
                request=dict(job_name=name, walltime="01:02:03", nodes=1, task="tests", args=["/x/a", "-q", "/y/b", "ignored"]),
                outcome=dict(kind="child", rc=0),
                state_history=[dict(elapsed_s=t, state=s) for t, s in history],
                preflight=dict(qstat_Q=dict(stdout="QueueName RUN QUE TOT PRR\ngen_S 3 12 20 5\n")))
            if name == "a":
                data.update(queue_wait_s=300, queue_wait_observed=True, terminal_reason="scheduler-end-state")
            elif name == "b":
                data.update(outcome=dict(kind="infra", rc=16, reason="queue-wait-timeout"),
                            qdel=dict(attempted=True, cleanup_elapsed_s=12, job_may_remain=True,
                                      gate=dict(reason="fresh-cancellable-snapshot")))
            path = directory / "receipt.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            script = directory / "dispatch.sh"
            script.write_text("synthetic, never executed\n", encoding="utf-8")
            os.utime(script, (1000000000, 1000000000))
            os.utime(path, (1000000400, 1000000400))
            if name == "a":
                (directory / "izdw-a.e1").write_text(TRACE + '{"time_ns":1000000000}\n' +
                    TRACE + '{"time_ns":3500000000}\n', encoding="utf-8")
        a, b, c = records = collect([root])

        def check(actual, expected):
            if actual != expected:
                raise AssertionError(f"expected {expected!r}, got {actual!r}")

        for record in records:
            check(set(record), set(KEYS))
        check(a["parse_error"], None)
        check(b["parse_error"], None)
        check(bool(c["parse_error"]), True)
        check([a[k] for k in ("walltime_s", "poll_count", "states", "t_first_qstat_s",
            "t_run_first_s", "t_end_s", "queue_wait_s", "run_s", "wall_files_s", "post_end_s",
            "job_trace_events", "job_trace_span_s")],
            [3723, 4, ["QUE", "RUN", "END"], 10, 310, 350, 300, 40, 400, 50, 2, 2.5])
        check(a["preflight_gen_s"], dict(tot=20, que=12, prr=5, run=3))
        check(a["args_head"], ["a", "-q", "b"])
        check(a["dispatch_sh_mtime"], "2001-09-09T10:46:40+09:00")
        check([b[k] for k in ("outcome_kind", "outcome_rc", "queue_wait_s", "queue_wait_derived_s",
            "qdel_attempted", "qdel_cleanup_elapsed_s", "qdel_job_may_remain", "run_s",
            "post_end_s", "job_trace_events", "job_trace_span_s")],
            ["infra", 16, None, 900, True, 12, True, None, None, 0, None])
        summary = summarize(records)
        check([summary[k] for k in ("n_receipts", "n_parse_error", "n_wait")], [3, 1, 2])
        for key, value, n in (("t_first_qstat_s", 10.0, 2), ("queue_wait_s", 300.0, 1),
            ("queue_wait_derived_s", 900.0, 1), ("run_s", 40.0, 1), ("post_end_s", 50.0, 1),
            ("qdel_cleanup_elapsed_s", 12.0, 1), ("job_trace_span_s", 2.5, 1)):
            check(summary["distributions"][key], dict(n=n, min=value, p50=value, p90=value, max=value))
        check(summary["queue_wait_ge"], [dict(seconds=s, n=n, ratio=r, derived_n=d, derived_ratio=dr)
            for s, n, r, d, dr in ((300, 2, 1.0, 1, 0.5), (600, 1, 0.5, 1, 0.5),
                                  (900, 1, 0.5, 1, 0.5), (1200, 0, 0.0, 0, 0.0), (3000, 0, 0.0, 0, 0.0))])
        check(summary["by_congestion"][1], dict(bucket="10-49", n=2, n_wait=2, p50=300.0, p90=900.0, max=900.0, queue_wait_ge_900=1))
        check(summary["by_outcome"], [dict(kind="child", reason=None, n=1), dict(kind="infra", reason="queue-wait-timeout", n=1)])
        check(summary["firings"], [dict(submission_dir="b", request_id="b", reason="queue-wait-timeout", last_state="QUE", t_last_s=910, cleanup_elapsed_s=12, preflight_que=12)])
        check(distribution([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), dict(n=10, min=1, p50=5, p90=9, max=10))
        print("SELFTEST_PASS")
        return 0
    except Exception as exc:
        print(f"SELFTEST_FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, action="append", default=[])
    parser.add_argument("--glob-worktrees", type=Path, action="append", default=[])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--table", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    options = parser.parse_args()
    if options.selftest:
        if options.root or options.glob_worktrees or options.out or options.table:
            parser.error("--selftest must be used alone")
        return selftest()
    if not options.root and not options.glob_worktrees:
        parser.error("at least one --root or --glob-worktrees is required")
    if options.out is None and not options.table:
        parser.error("--out or --table is required")
    for path in options.root + options.glob_worktrees:
        if not path.is_absolute() or not path.is_dir():
            parser.error(f"input must be an existing absolute directory: {path}")
    if options.out is not None:
        if not options.out.is_absolute() or not options.out.parent.is_dir():
            parser.error("--out must be absolute with an existing parent directory")
        if options.out.exists() or options.out.is_symlink():
            parser.error(f"refusing to overwrite: {options.out}")
    try:
        roots = set(options.root)
        for parent in options.glob_worktrees:
            for child in parent.iterdir():
                path = child / "output" / "pegasus-dispatch"
                if path.is_dir():
                    roots.add(path)
        records = collect(roots)
        summary = summarize(records)
        if options.out is not None:
            payload = json.dumps(dict(records=records, summary=summary), ensure_ascii=False,
                                 indent=2, allow_nan=False) + "\n"
            with options.out.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        if options.table:
            print(markdown(summary))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
