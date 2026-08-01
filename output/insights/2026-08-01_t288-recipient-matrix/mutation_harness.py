#!/usr/bin/env python3
"""T-288 recipient-matrix mutation harness (N01--N15)."""

import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


REPO = Path(
    "/home/SFC/tanab/github/izanagi/.claude/worktrees/"
    "dev-wave-t288-recipient-matrix"
)
TARGET_REL = Path("orchestrator/campaign/p3_autonomous_workload_trial.py")
TARGET = REPO / TARGET_REL
LEDGER = Path("/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/mutation-ledger.json")
LOCK = Path("/home/SFC/tanab/.claude/jobs/64ffb231/tmp/t288/mutation-harness.lock")
TEST_COMMAND = [
    "python3",
    "tools/run_tests.py",
    "orchestrator/tests/test_p3_autonomous_workload_trial.py",
    "orchestrator/tests/test_p3_s4_loop.py",
    "-q",
    "-rf",
]
TIMEOUT_SECONDS = 1800
ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
FAILED_RE = re.compile(r"^\s*(?:(?:\||│|┃|>)\s*)*FAILED\s+(.+?)\s*$")


def _node(name):
    return "orchestrator/tests/test_p3_autonomous_workload_trial.py::" + name


MUTATIONS = [
    {
        "id": "N01",
        "anchor": "abort_rate * 100.0",
        "new": "abort_rate * 1.0",
        "expected_hint": "abort_rate_pct だけが変わる",
        "expected_nodes": {_node("test_role_metric_payloads_convert_only_percent_fields")},
    },
    {
        "id": "N02",
        "anchor": "llc_miss_rate * 100.0",
        "new": "llc_miss_rate * 1.0",
        "expected_hint": "cache_miss_rate_pct だけが変わる",
        "expected_nodes": {_node("test_role_metric_payloads_convert_only_percent_fields")},
    },
    {
        "id": "N03",
        "anchor": "if isinstance(value, bool) or not isinstance(value, (int, float)):",
        "new": "if not isinstance(value, (int, float)):",
        "expected_hint": "bool だけが通る",
        "expected_nodes": {_node("test_metric_projection_rejects_only_invalid_numbers")},
    },
    {
        "id": "N04",
        "anchor": "return metric if math.isfinite(metric) else None",
        "new": "return metric",
        "expected_hint": "非有限だけが通る",
        "expected_nodes": {_node("test_metric_projection_rejects_only_invalid_numbers")},
    },
    {
        "id": "N05",
        "anchor": '"abort_rate": _finite_metric_or_none(leading.get("abort_rate")),',
        "new": '"abort_rate_pct": _finite_metric_or_none(leading.get("abort_rate")),',
        "expected_hint": "内部 key だけが変わる",
        "expected_nodes": {_node("test_metric_projection_uses_ratio_keys_and_units")},
    },
    {
        "id": "N06",
        "anchor": '"abort_rate": _finite_metric_or_none(leading.get("abort_rate")),',
        "new": '"abort_rate": _finite_metric_or_none(leading.get("llc_miss_rate")),',
        "expected_hint": "abort の source だけが変わる",
        "expected_nodes": {_node("test_metric_projection_uses_ratio_keys_and_units")},
    },
    {
        "id": "N07",
        "anchor": '"current_perf": dict(perf_payload),',
        "new": '"current_perf": dict(current_metrics),',
        "expected_hint": "planner の key 集合だけが変わる",
        "expected_nodes": {_node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")},
    },
    {
        "id": "N08",
        "anchor": '"baseline": dict(perf_payload),',
        "new": '"baseline": dict(current_metrics),',
        "expected_hint": "coder の key 集合だけが変わる",
        "expected_nodes": {_node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")},
    },
    {
        "id": "N09",
        "anchor": '"metrics": dict(current_metrics),',
        "new": '"metrics": dict(perf_payload),',
        "expected_hint": "critic の key 集合だけが変わる",
        "expected_nodes": {_node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")},
    },
    {
        "id": "N10",
        "anchor": 'SCHEMA_VERSION = "p3-autonomous-workload-trial/v2"',
        "new": 'SCHEMA_VERSION = "p3-autonomous-workload-trial/v1"',
        "expected_hint": "schema literal だけが変わる",
        "expected_nodes": {_node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")},
    },
    {
        "id": "N11",
        "anchor": 'contention_level=descriptor["contention"]["label"],',
        "new": 'contention_level="wrong",',
        "expected_hint": "leading の label だけが変わる",
        "expected_nodes": {
            _node("test_generation_one_finite_metrics_preserve_recipient_units_and_report_schema")
        },
    },
    {
        "id": "N12",
        "anchor": '"abort_rate": None,',
        "new": '"abort_rate": 0.0,',
        "expected_hint": "未観測世代の値だけが変わる",
        "expected_nodes": {_node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")},
    },
    {
        "id": "N13",
        "anchor": '"llc_miss_rate": llc_miss_rate,',
        "new": '"llc_miss_rate": llc_miss_rate * 100.0,',
        "expected_hint": "percent 名でない field だけが変わる",
        "expected_nodes": {_node("test_role_metric_payloads_convert_only_percent_fields")},
    },
    {
        "id": "N14",
        "anchor": "else _finite_metric_or_none(abort_rate * 100.0)",
        "new": "else abort_rate * 100.0",
        "expected_hint": "sys.float_info.max 経路だけが変わる",
        "expected_nodes": {_node("test_role_metric_payloads_reject_percent_overflow")},
    },
    {
        "id": "N15",
        "anchor": "current_metrics = _metric_projection(outcome)",
        "new": 'generation_record["metrics"] = dict(current_metrics)',
        "expected_hint": "report の key 集合だけが変わる",
        "expected_nodes": {_node("test_fixture_trial_runs_ycsb_abc_and_binds_descriptor")},
        "insert_after": True,
    },
]


class HarnessAbort(RuntimeError):
    pass


def _write_text(path, content):
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _write_ledger(state):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    temporary = LEDGER.with_name(LEDGER.name + ".{}.tmp".format(os.getpid()))
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(str(temporary), str(LEDGER))


def _normalize_node(node):
    node = node.strip().replace("\\", "/")
    repo_prefix = str(REPO).replace("\\", "/") + "/"
    if node.startswith(repo_prefix):
        node = node[len(repo_prefix):]
    while node.startswith("./"):
        node = node[2:]
    return node


def _failed_nodes(output):
    nodes = []
    for raw_line in output.splitlines():
        line = ANSI_RE.sub("", raw_line)
        match = FAILED_RE.match(line)
        if match is None:
            continue
        remainder = match.group(1)
        node = remainder.split(" - ", 1)[0] if " - " in remainder else remainder
        node = _normalize_node(node)
        if node and node not in nodes:
            nodes.append(node)
    return nodes


def _stop_process_group(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def _run_tests():
    started = time.monotonic()
    process = subprocess.Popen(
        TEST_COMMAND,
        cwd=str(REPO),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        start_new_session=True,
    )
    try:
        try:
            output, _ = process.communicate(timeout=TIMEOUT_SECONDS)
            return {
                "rc": process.returncode,
                "timed_out": False,
                "output": output or "",
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            output, _ = process.communicate()
            if not output:
                partial = exc.output or ""
                output = (
                    partial.decode("utf-8", errors="replace")
                    if isinstance(partial, bytes)
                    else partial
                )
            return {
                "rc": None,
                "timed_out": True,
                "output": output or "",
                "duration_seconds": round(time.monotonic() - started, 3),
            }
    except BaseException:
        _stop_process_group(process)
        raise


def _mutated_source(spec, original):
    anchor = spec["anchor"]
    count = original.count(anchor)
    if count != 1:
        return None, count
    if not spec.get("insert_after"):
        mutated = original.replace(anchor, spec["new"], 1)
    else:
        position = original.index(anchor)
        line_start = original.rfind("\n", 0, position) + 1
        indent = original[line_start:position]
        if indent.strip():
            raise HarnessAbort(
                "{}: N15 anchor の前が純粋なインデントでない".format(spec["id"])
            )
        replacement = anchor + "\n" + indent + spec["new"]
        mutated = original.replace(anchor, replacement, 1)
    if mutated == original:
        raise HarnessAbort("{}: 注入後も内容が変化していない".format(spec["id"]))
    return mutated, count


def _base_record(spec):
    return {
        "mutation_id": spec["id"],
        "file": TARGET_REL.as_posix(),
        "anchor": spec["anchor"],
        "new": spec["new"],
        "expected_hint": spec["expected_hint"],
        "expected_nodes": sorted(spec["expected_nodes"]),
    }


def _restore(original):
    _write_text(TARGET, original)
    if TARGET.read_text(encoding="utf-8") != original:
        raise HarnessAbort("復元後 read_text() が元ソースと一致しない")


def _summarize_record(record):
    rc = "timeout" if record.get("timed_out") else record.get("rc")
    return "{id} {judgment} rc={rc} failed={count} {seconds:.3f}s".format(
        id=record["mutation_id"],
        judgment=record["judgment"],
        rc=rc,
        count=len(record.get("failed_nodes", [])),
        seconds=record.get("duration_seconds", 0.0),
    )


def _run_mutation(spec, original):
    record = _base_record(spec)
    mutated, count = _mutated_source(spec, original)
    record["anchor_count"] = count
    if mutated is None:
        record.update({
            "rc": None,
            "timed_out": False,
            "failed_nodes": [],
            "matched_expected_nodes": [],
            "judgment": "ANCHOR_ERROR",
            "duration_seconds": 0.0,
        })
        return record, False

    restored = False
    started = time.monotonic()
    try:
        if TARGET.read_text(encoding="utf-8") != original:
            raise HarnessAbort("{}: 注入前 source drift".format(spec["id"]))
        _write_text(TARGET, mutated)
        if TARGET.read_text(encoding="utf-8") != mutated:
            raise HarnessAbort("{}: 注入内容の再読が不一致".format(spec["id"]))
        result = _run_tests()
        failed = _failed_nodes(result["output"])
        expected = {_normalize_node(node) for node in spec["expected_nodes"]}
        matched = sorted(expected.intersection(failed))
        if result["timed_out"]:
            judgment = "INCONCLUSIVE"
        elif result["rc"] == 0:
            judgment = "SURVIVED"
        elif not failed:
            judgment = "PARSE_ERROR"
        elif matched:
            judgment = "KILL"
        else:
            judgment = "INCONCLUSIVE"
        record.update({
            "rc": result["rc"],
            "timed_out": result["timed_out"],
            "failed_nodes": failed,
            "matched_expected_nodes": matched,
            "judgment": judgment,
            "duration_seconds": result["duration_seconds"],
        })
    finally:
        try:
            _restore(original)
            restored = True
        finally:
            record["restored"] = restored
            record.setdefault(
                "duration_seconds", round(time.monotonic() - started, 3)
            )
    stop = record["judgment"] == "PARSE_ERROR"
    return record, stop


def _counts(records):
    return {
        "KILL": sum(item.get("judgment") == "KILL" for item in records),
        "SURVIVED": sum(item.get("judgment") == "SURVIVED" for item in records),
        "OTHER": sum(
            item.get("judgment") not in {"KILL", "SURVIVED"} for item in records
        ),
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        choices=[spec["id"] for spec in MUTATIONS],
        help="実行する変異 ID の部分集合",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lock_stream = LOCK.open("a+")
    try:
        try:
            fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("ABORT: mutation harness は既に走行中です", file=sys.stderr)
            return 3

        original = TARGET.read_text(encoding="utf-8")
        selected_ids = set(args.only) if args.only else None
        selected = [
            spec for spec in MUTATIONS
            if selected_ids is None or spec["id"] in selected_ids
        ]
        state = {
            "schema_version": "t288-mutation-ledger/v1",
            "worktree_root": str(REPO),
            "test_command": TEST_COMMAND,
            "timeout_seconds": TIMEOUT_SECONDS,
            "selected_mutations": [spec["id"] for spec in selected],
            "baseline": None,
            "mutations": [],
            "summary": {"KILL": 0, "SURVIVED": 0, "OTHER": 0},
            "aborted": False,
            "abort_reason": None,
        }
        _write_ledger(state)

        try:
            baseline_result = _run_tests()
            baseline_nodes = _failed_nodes(baseline_result["output"])
            state["baseline"] = {
                "rc": baseline_result["rc"],
                "timed_out": baseline_result["timed_out"],
                "failed_nodes": baseline_nodes,
                "duration_seconds": baseline_result["duration_seconds"],
                "judgment": (
                    "PASS"
                    if baseline_result["rc"] == 0 and not baseline_result["timed_out"]
                    else "FAIL"
                ),
            }
            _write_ledger(state)
            if baseline_result["timed_out"] or baseline_result["rc"] != 0:
                raise HarnessAbort("baseline が rc=0 でないため変異を開始しない")

            for spec in selected:
                record, stop = _run_mutation(spec, original)
                state["mutations"].append(record)
                state["summary"] = _counts(state["mutations"])
                _write_ledger(state)
                print(_summarize_record(record), flush=True)
                if not record.get("restored", True):
                    raise HarnessAbort("復元失敗のため即時停止")
                if stop:
                    raise HarnessAbort(
                        "rc!=0 かつ FAILED node 抽出 0 件のため fail-closed 停止"
                    )
        except BaseException as exc:
            state["aborted"] = True
            state["abort_reason"] = "{}: {}".format(type(exc).__name__, exc)
            state["summary"] = _counts(state["mutations"])
            _write_ledger(state)
            raise
        finally:
            if TARGET.read_text(encoding="utf-8") != original:
                _restore(original)

        counts = state["summary"]
        print(
            "TOTAL KILL={KILL} SURVIVED={SURVIVED} OTHER={OTHER}".format(**counts),
            flush=True,
        )
        return 0
    except (HarnessAbort, OSError) as exc:
        print("ABORT: {}".format(exc), file=sys.stderr, flush=True)
        return 2
    finally:
        lock_stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
