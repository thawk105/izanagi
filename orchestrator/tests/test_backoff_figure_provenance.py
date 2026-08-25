# -*- coding: utf-8 -*-
"""backoff figure provenance v2 の bytes と baseline 意味束縛を検査する。

matplotlib/numpy/campaign admission に依存せず、合成 WAL/dat/generator/output だけで
positive control と負の対照を走らせる。
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shlex
import statistics
import sys
import tempfile
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path


SCHEMA = "izanagi-backoff-figure-provenance/v2"
BASELINE_BY_GENOME = {
    ("0", "-1"): ("no-backoff", "no backoff"),
    ("1", "-1"): ("stock-adaptive", "stock adaptive"),
}
RUN_CONDITION_KEYS = (
    "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us",
    "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw",
)
INTEGER_CONDITIONS = {
    "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us", "ycsb_rratio",
    "CCBENCH_TRACE",
}
T_975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
    14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
    20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048,
}
REAL_PROVENANCE = Path(
    "docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json")


class ProvenanceValidationError(ValueError):
    """provenance v2 と現在 bytes/意味の不一致。"""


def _reject(message: str) -> None:
    raise ProvenanceValidationError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(repo_root: Path, value: object, *, repo_relative: bool = False) -> Path:
    if not isinstance(value, str) or not value:
        _reject(f"path must be a non-empty string: {value!r}")
    path = Path(value)
    if repo_relative and path.is_absolute():
        _reject(f"path must be repo-relative: {value}")
    resolved = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    if repo_relative:
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError:
            _reject(f"path leaves repo root: {value}")
    return resolved


def _read_wal(path: Path) -> list[dict]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _reject(f"cannot parse WAL {path}: {exc}")


def _parse_genome(value: str) -> dict[str, str]:
    body = value.split("|", 1)[1] if "|" in value else value
    result = {}
    for item in body.split(","):
        if "=" in item:
            key, raw = item.split("=", 1)
            result[key] = raw
    return result


def _condition_scalar(key: str, value: str) -> object:
    if key == "ycsb_rmw":
        normalized = str(value).strip().lower()
        if normalized in ("false", "0"):
            return False
        if normalized in ("true", "1"):
            return True
        _reject(f"ycsb_rmw is not boolean: {value!r}")
    if key in INTEGER_CONDITIONS:
        return int(value)
    if key == "ycsb_zipf_skew":
        return float(value)
    return value


def _unique(values: Sequence[object]) -> object:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    unique.sort(key=lambda value: (type(value).__name__, repr(value)))
    return unique[0] if len(unique) == 1 else unique


def _numactl_arguments(run_cmd: str) -> list[str] | None:
    try:
        tokens = shlex.split(run_cmd)
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if Path(token).name != "numactl":
            continue
        arguments = []
        take_value = False
        for candidate in tokens[index + 1:]:
            if take_value:
                arguments.append(candidate)
                take_value = False
                continue
            if not candidate.startswith("-"):
                break
            arguments.append(candidate)
            if candidate in {
                "-i", "--interleave", "-m", "--membind", "-N", "--cpunodebind",
                "-C", "--physcpubind", "-p", "--preferred", "-w",
                "--weighted-interleave",
            }:
                take_value = True
        return arguments
    return None


def _conditions_from_wal(records: Sequence[Mapping], campaign_dir: Path) -> dict:
    observed = {key: [] for key in RUN_CONDITION_KEYS}
    observed["numactl_args"] = []
    run_commands = []
    env_values = []
    trace_values = []
    build_done_count = 0
    trace_observation_count = 0
    for record in records:
        env_tag = record.get("env_tag")
        if env_tag:
            env_values.append(str(env_tag))
        payload = record.get("payload", {})
        run_cmd = payload.get("run_cmd")
        if run_cmd:
            run_commands.append(run_cmd)
            numactl_args = _numactl_arguments(run_cmd)
            if numactl_args is not None:
                observed["numactl_args"].append(numactl_args)
            for key in RUN_CONDITION_KEYS:
                match = re.search(rf"(?:^|\s)-{re.escape(key)}=([^\s]+)", run_cmd)
                if match:
                    observed[key].append(_condition_scalar(key, match.group(1)))
        if record.get("stage") == "build_done":
            build_done_count += 1
            found = []
            for value in payload.values():
                if isinstance(value, str):
                    found.extend(re.findall(r"(?:^|\s)-DCCBENCH_TRACE=([^\s]+)", value))
            if found:
                trace_observation_count += 1
                trace_values.extend(_condition_scalar("CCBENCH_TRACE", value)
                                    for value in found)

    conditions = {}
    unresolved = []
    incomplete = []
    for key in RUN_CONDITION_KEYS + ("numactl_args",):
        values = observed[key]
        if values:
            conditions[key] = _unique(values)
            if len(values) < len(run_commands):
                incomplete.append(key)
        else:
            unresolved.append(key)
    if env_values:
        conditions["env"] = _unique(env_values)
    else:
        unresolved.append("env")
    if trace_values:
        conditions["CCBENCH_TRACE"] = _unique(trace_values)
        if trace_observation_count < build_done_count:
            incomplete.append("CCBENCH_TRACE")
    else:
        unresolved.append("CCBENCH_TRACE")
    try:
        commit = json.loads((campaign_dir / "campaign.lock").read_text(
            encoding="utf-8")).get("ccbench_commit")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        commit = None
    if commit is None:
        unresolved.append("ccbench_commit")
    else:
        conditions["ccbench_commit"] = commit
    conditions["unresolved_fields"] = sorted(unresolved)
    conditions["incomplete_fields"] = sorted(incomplete)
    return conditions


def _reject_incomplete_conditions(conditions: object) -> None:
    if not isinstance(conditions, Mapping):
        _reject("conditions must be an object")
    for marker in ("unresolved_fields", "incomplete_fields"):
        value = conditions.get(marker)
        if not isinstance(value, list):
            _reject(f"conditions.{marker} must be a list")
        if value:
            _reject(f"conditions.{marker} must be empty: {value}")
    for key, value in conditions.items():
        if key in ("unresolved_fields", "incomplete_fields"):
            continue
        if key == "numactl_args":
            if (not isinstance(value, list)
                    or any(not isinstance(argument, str) for argument in value)):
                _reject("conditions.numactl_args must be one argument list")
        elif isinstance(value, list):
            _reject(f"condition has multiple values inside one workload: {key}")


def _conditions_without_markers(conditions: Mapping) -> dict:
    return {key: value for key, value in conditions.items()
            if key not in ("unresolved_fields", "incomplete_fields")}


def _ci95_half_tps(reps: Sequence[object]) -> float | None:
    values = [float(value) for value in reps]
    if len(values) < 2:
        return None
    factor = T_975.get(len(values) - 1, 1.96)
    return float(factor * statistics.stdev(values) / math.sqrt(len(values)))


def _baseline_candidates(records: Sequence[Mapping]) -> dict[str, dict]:
    genomes = {}
    pending = {}
    committed = {}
    for record in records:
        variant = record.get("variant")
        stage = record.get("stage")
        payload = record.get("payload", {})
        if stage == "build_start" and isinstance(payload.get("genome"), str):
            genomes[variant] = _parse_genome(payload["genome"])
        elif stage == "bench_done":
            pending[variant] = record
        elif stage == "commit" and variant in pending:
            committed[variant] = pending.pop(variant)

    candidates = {}
    for variant, record in committed.items():
        genome = genomes.get(variant, {})
        pair = (str(genome.get("BACK_OFF")), str(genome.get("BACKOFF_FIXED")))
        baseline = BASELINE_BY_GENOME.get(pair)
        if baseline is None:
            continue
        reps = record.get("payload", {}).get("tps", [])
        if not reps:
            continue
        baseline_id, _label = baseline
        candidates[baseline_id] = {
            "value_tps": float(statistics.fmean(float(value) for value in reps)),
            "ci95_half_tps": _ci95_half_tps(reps),
            "genome": dict(sorted(genome.items())),
        }
    return candidates


def _facts_from_wal(records: Sequence[Mapping]) -> dict:
    genomes = {}
    pending = {}
    committed = {}
    for record in records:
        variant = record.get("variant")
        stage = record.get("stage")
        payload = record.get("payload", {})
        if stage == "build_start" and isinstance(payload.get("genome"), str):
            genomes[variant] = _parse_genome(payload["genome"])
        elif stage == "bench_done":
            pending[variant] = record
        elif stage == "commit" and variant in pending:
            committed[variant] = pending.pop(variant)

    points = []
    none_reps = None
    for variant, record in committed.items():
        genome = genomes.get(variant, {})
        back_off = genome.get("BACK_OFF", "0")
        fixed = genome.get("BACKOFF_FIXED", "-1")
        reps = record.get("payload", {}).get("tps", [])
        if back_off == "1" and fixed not in ("-1", None):
            if not isinstance(reps, list) or not reps:
                _reject(f"static backoff {fixed} has empty tps repetitions")
            values = [float(value) for value in reps]
            if any(not math.isfinite(value) for value in values):
                _reject(f"static backoff {fixed} has non-finite tps")
            points.append((int(fixed), values))
        elif back_off == "0":
            none_reps = reps
    if not points:
        _reject("WAL has no committed static-backoff point")
    points.sort(key=lambda item: item[0])
    means = [float(statistics.fmean(reps)) / 1e6 for _, reps in points]
    peak = max(range(len(points)), key=lambda index: means[index])
    none_m = None
    if none_reps:
        none_m = float(statistics.fmean(float(value) for value in none_reps)) / 1e6
    return {
        "best_M": means[peak],
        "best_bf": points[peak][0],
        "none_M": none_m,
        "n_reps": len(points[0][1]),
    }


def _workload_from_dat(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        _reject(f"cannot parse dat {path}: {exc}")
    for line in lines:
        if line.startswith("# workload:"):
            value = line.split(":", 1)[1].strip()
            return value.split("(", 1)[0].strip() if value else "?"
    _reject(f"dat has no workload metadata: {path}")


def _same_number(observed: object, expected: object) -> bool:
    if expected is None:
        return observed is None
    return (isinstance(observed, (int, float)) and not isinstance(observed, bool)
            and math.isfinite(float(observed))
            and math.isclose(float(observed), float(expected), rel_tol=0.0, abs_tol=1e-9))


def validate_figure_provenance(
    provenance: Mapping, repo_root: Path, expected_baselines: Sequence[str]
) -> None:
    """v2 provenance を現在 bytes と期待する描画 baseline 集合に対して検査する。"""
    repo_root = Path(repo_root)
    if provenance.get("schema") != SCHEMA:
        _reject(f"unsupported schema: {provenance.get('schema')}")

    generator = provenance.get("generator_source")
    if not isinstance(generator, Mapping):
        _reject("generator_source is missing")
    generator_path = _resolve(repo_root, generator.get("path"), repo_relative=True)
    if generator.get("sha256") != _sha256(generator_path):
        _reject("generator SHA256 mismatch")

    outputs = provenance.get("outputs")
    if not isinstance(outputs, list) or len(outputs) != 2:
        _reject("outputs must contain PNG and PDF")
    suffixes = [Path(row.get("path", "")).suffix if isinstance(row, Mapping) else ""
                for row in outputs]
    if suffixes != [".png", ".pdf"]:
        _reject(f"output order must be PNG, PDF: {suffixes}")
    for row in outputs:
        output_path = _resolve(repo_root, row.get("path"), repo_relative=True)
        if row.get("sha256") != _sha256(output_path):
            _reject(f"output SHA256 mismatch: {row.get('path')}")

    expected_baselines = tuple(expected_baselines)
    if len(set(expected_baselines)) != len(expected_baselines):
        _reject(f"duplicate expected baseline: {expected_baselines}")
    if any(value not in {item[0] for item in BASELINE_BY_GENOME.values()}
           for value in expected_baselines):
        _reject(f"unknown expected baseline: {expected_baselines}")

    inputs = provenance.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        _reject("inputs must be a non-empty list")
    expected_facts = {}
    for row in inputs:
        if not isinstance(row, Mapping):
            _reject("input entry must be an object")
        campaign_dir = _resolve(repo_root, row.get("dir"), repo_relative=True)
        wal_path = _resolve(repo_root, row.get("wal"), repo_relative=True)
        dat_path = _resolve(repo_root, row.get("dat"), repo_relative=True)
        lock_path = _resolve(repo_root, row.get("lock"), repo_relative=True)
        if lock_path != (campaign_dir / "campaign.lock").resolve():
            _reject("input lock must be the campaign.lock under input dir")
        if row.get("wal_sha256") != _sha256(wal_path):
            _reject(f"WAL SHA256 mismatch: {row.get('wal')}")
        if row.get("dat_sha256") != _sha256(dat_path):
            _reject(f"dat SHA256 mismatch: {row.get('dat')}")
        if row.get("lock_sha256") != _sha256(lock_path):
            _reject(f"campaign.lock SHA256 mismatch: {row.get('lock')}")
        records = _read_wal(wal_path)
        expected_conditions = _conditions_from_wal(records, campaign_dir)
        conditions = row.get("conditions")
        _reject_incomplete_conditions(conditions)
        if (_conditions_without_markers(conditions)
                != _conditions_without_markers(expected_conditions)):
            _reject(f"conditions mismatch: {conditions} != {expected_conditions}")

        candidates = _baseline_candidates(records)
        baselines = row.get("baselines")
        if not isinstance(baselines, list):
            _reject("baselines must be a list")
        observed_ids = []
        for baseline in baselines:
            if not isinstance(baseline, Mapping) or set(baseline) != {
                "label", "value_tps", "ci95_half_tps", "genome",
            }:
                _reject(
                    "each baseline must have exactly "
                    "label/value_tps/ci95_half_tps/genome")
            genome = baseline["genome"]
            if not isinstance(genome, Mapping):
                _reject("baseline genome must be an object")
            pair = (str(genome.get("BACK_OFF")), str(genome.get("BACKOFF_FIXED")))
            identity = BASELINE_BY_GENOME.get(pair)
            if identity is None:
                _reject(f"unrecognized baseline genome: {pair}")
            baseline_id, expected_label = identity
            if baseline["label"] != expected_label:
                _reject(
                    f"baseline label/genome mismatch: {baseline['label']!r} != "
                    f"{expected_label!r} for {pair}")
            candidate = candidates.get(baseline_id)
            if candidate is None:
                _reject(f"baseline is absent from committed WAL data: {baseline_id}")
            if dict(genome) != candidate["genome"]:
                _reject(f"baseline genome differs from WAL: {baseline_id}")
            value = baseline["value_tps"]
            if (not isinstance(value, (int, float)) or not math.isfinite(value)
                    or not math.isclose(float(value), candidate["value_tps"],
                                        rel_tol=0.0, abs_tol=1e-9)):
                _reject(f"baseline value differs from WAL mean: {baseline_id}")
            half = baseline["ci95_half_tps"]
            expected_half = candidate["ci95_half_tps"]
            if expected_half is None:
                if half is not None:
                    _reject(f"baseline CI must be null when incalculable: {baseline_id}")
            elif (not isinstance(half, (int, float)) or isinstance(half, bool)
                  or not math.isfinite(float(half))
                  or not math.isclose(float(half), expected_half,
                                      rel_tol=0.0, abs_tol=1e-6)):
                _reject(f"baseline CI differs from WAL: {baseline_id}")
            observed_ids.append(baseline_id)
        if tuple(observed_ids) != expected_baselines:
            _reject(
                f"recorded baselines differ from rendered selection: "
                f"{tuple(observed_ids)} != {expected_baselines}")

        workload = _workload_from_dat(dat_path)
        if workload in expected_facts:
            _reject(f"duplicate facts workload: {workload}")
        expected_facts[workload] = _facts_from_wal(records)

    facts = provenance.get("facts")
    if not isinstance(facts, Mapping):
        _reject("facts must be an object")
    if set(facts) != set(expected_facts):
        _reject(f"facts workloads differ: {set(facts)} != {set(expected_facts)}")
    for workload, expected in expected_facts.items():
        observed = facts[workload]
        if not isinstance(observed, Mapping):
            _reject(f"facts.{workload} must be an object")
        for key in ("best_M", "none_M"):
            if not _same_number(observed.get(key), expected[key]):
                _reject(f"facts.{workload}.{key} differs from WAL")
        for key in ("best_bf", "n_reps"):
            value = observed.get(key)
            if (not isinstance(value, int) or isinstance(value, bool)
                    or value != expected[key]):
                _reject(f"facts.{workload}.{key} differs from WAL")


def _digest_row(path: str, root: Path) -> dict:
    return {"path": path, "sha256": _sha256(root / path)}


def _baseline_row(baseline_id: str) -> dict:
    if baseline_id == "no-backoff":
        return {
            "label": "no backoff", "value_tps": 110.0,
            "ci95_half_tps": 127.06,
            "genome": {"BACKOFF_FIXED": "-1", "BACK_OFF": "0", "WAL": "0"},
        }
    return {
        "label": "stock adaptive", "value_tps": 85.0,
        "ci95_half_tps": 63.53,
        "genome": {"BACKOFF_FIXED": "-1", "BACK_OFF": "1", "WAL": "0"},
    }


@contextmanager
def _synthetic_fixture(selected=("no-backoff", "stock-adaptive")):
    with tempfile.TemporaryDirectory(prefix="backoff-prov-") as temp:
        root = Path(temp)
        campaign = root / "output" / "campaigns" / "fixture"
        reports = campaign / "reports"
        runs = campaign / "runs"
        generator = root / "tools" / "plotting" / "plot_backoff.py"
        output_dir = root / "docs" / "paper-story" / "figures"
        reports.mkdir(parents=True)
        runs.mkdir(parents=True)
        generator.parent.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        run_cmd = (
            "numactl --interleave=all perf stat -e cycles -- /tmp/ycsb_silo.exe "
            "-thread_num=48 -ycsb_tuple_num=1000000 -extime=3 "
            "-clocks_per_us=1800 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0"
        )
        variants = (
            ("none", "silo|BACKOFF_FIXED=-1,BACK_OFF=0,WAL=0", [100.0, 120.0]),
            ("adapt", "silo|BACKOFF_FIXED=-1,BACK_OFF=1,WAL=0", [80.0, 90.0]),
            ("static", "silo|BACKOFF_FIXED=10,BACK_OFF=1,WAL=0", [130.0, 140.0]),
        )
        records = []
        for variant, genome, reps in variants:
            records.extend([
                {"variant": variant, "stage": "build_start", "env_tag": "linux-baremetal",
                 "payload": {"genome": genome}},
                {"variant": variant, "stage": "build_done", "env_tag": "linux-baremetal",
                 "payload": {"perf_configure_cmd": "cmake -DCCBENCH_TRACE=0"}},
                {"variant": variant, "stage": "bench_done", "env_tag": "linux-baremetal",
                 "payload": {"tps": reps, "run_cmd": run_cmd}},
                {"variant": variant, "stage": "commit", "env_tag": "linux-baremetal",
                 "payload": {"fitness_tps": reps[0]}},
            ])
        wal_path = runs / "wal.jsonl"
        wal_path.write_text("".join(json.dumps(record) + "\n" for record in records),
                            encoding="utf-8")
        dat_path = reports / "fixture.dat"
        dat_path.write_bytes(
            b"# workload: write-heavy (ycsb_rmw=0)\n10 135 1.0 1.2\n")
        lock_path = campaign / "campaign.lock"
        lock_path.write_text(
            json.dumps({"ccbench_commit": "6656e93"}), encoding="utf-8")
        generator.write_bytes(b"# fixture plot_backoff generator\n")
        png_path = output_dir / "figure.png"
        pdf_path = output_dir / "figure.pdf"
        png_path.write_bytes(b"fixture-png")
        pdf_path.write_bytes(b"fixture-pdf")

        conditions = {
            "thread_num": 48, "ycsb_tuple_num": 1000000, "extime": 3,
            "clocks_per_us": 1800, "ycsb_zipf_skew": 0.9, "ycsb_rratio": 5,
            "ycsb_rmw": False, "numactl_args": ["--interleave=all"],
            "env": "linux-baremetal",
            "CCBENCH_TRACE": 0, "ccbench_commit": "6656e93",
            "unresolved_fields": [], "incomplete_fields": [],
        }
        wal_rel = str(wal_path.relative_to(root))
        dat_rel = str(dat_path.relative_to(root))
        provenance = {
            "schema": SCHEMA,
            "generated_utc": "fixture",
            "generator": "plot_backoff.py",
            "generator_source": _digest_row(str(generator.relative_to(root)), root),
            "outputs": [
                _digest_row(str(png_path.relative_to(root)), root),
                _digest_row(str(pdf_path.relative_to(root)), root),
            ],
            "inputs": [{
                "campaign": "fixture", "dir": str(campaign.relative_to(root)),
                "wal": wal_rel, "wal_sha256": _sha256(wal_path),
                "dat": dat_rel, "dat_sha256": _sha256(dat_path),
                "lock": str(lock_path.relative_to(root)),
                "lock_sha256": _sha256(lock_path),
                "threads": [48], "env": "linux-baremetal",
                "baselines": [_baseline_row(value) for value in selected],
                "conditions": conditions,
            }],
            "facts": {
                "write-heavy": {
                    "best_M": 0.000135,
                    "best_bf": 10,
                    "none_M": 0.00011,
                    "n_reps": 2,
                },
            },
        }
        yield root, provenance


def _expect_rejected(
    provenance: Mapping,
    root: Path,
    expected_baselines: Sequence[str],
    reason: str | None = None,
) -> None:
    try:
        validate_figure_provenance(provenance, root, expected_baselines)
    except ProvenanceValidationError as exc:
        if reason is not None and reason not in str(exc):
            raise AssertionError(f"wrong rejection reason: {exc}") from exc
        return
    raise AssertionError("invalid provenance was accepted")


def test_p1_accepts_complete_v2_provenance():
    with _synthetic_fixture() as (root, provenance):
        validate_figure_provenance(
            provenance, root, ("no-backoff", "stock-adaptive"))


def test_p2_accepts_no_backoff_only():
    with _synthetic_fixture(("no-backoff",)) as (root, provenance):
        validate_figure_provenance(provenance, root, ("no-backoff",))


def test_p3_boolean_spellings_preserve_meaning_and_numactl_arguments():
    with tempfile.TemporaryDirectory(prefix="backoff-condition-") as temp:
        campaign = Path(temp)
        (campaign / "campaign.lock").write_text(
            json.dumps({"ccbench_commit": "6656e93"}), encoding="utf-8")

        def conditions(rmw: str, numa: str) -> dict:
            command = (
                f"numactl {numa} /tmp/ycsb_silo.exe -thread_num=48 "
                "-ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=1800 "
                f"-ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw={rmw}")
            records = [{
                "stage": "build_done", "env_tag": "linux-baremetal",
                "payload": {
                    "run_cmd": command,
                    "configure": "cmake -DCCBENCH_TRACE=0",
                },
            }]
            return _conditions_from_wal(records, campaign)

        false_word = conditions("false", "--interleave=all")
        false_digit = conditions("0", "--interleave=all")
        true_word = conditions("true", "--interleave=all")
        true_digit = conditions("1", "--interleave=all")
        localalloc = conditions("false", "--localalloc")
        if false_word != false_digit or false_word["ycsb_rmw"] is not False:
            raise AssertionError("false and 0 were not normalized to the same false value")
        if true_word != true_digit or true_word["ycsb_rmw"] is not True:
            raise AssertionError("true and 1 were not normalized to the same true value")
        if false_word["numactl_args"] != ["--interleave=all"]:
            raise AssertionError(false_word["numactl_args"])
        if localalloc["numactl_args"] != ["--localalloc"]:
            raise AssertionError(localalloc["numactl_args"])
        if false_word["numactl_args"] == localalloc["numactl_args"]:
            raise AssertionError("distinct numactl policies collapsed")


def test_real_fig2b_provenance_is_admitted_with_no_backoff_only():
    repo_root = Path(__file__).resolve().parents[2]
    provenance_path = repo_root / REAL_PROVENANCE
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    validate_figure_provenance(provenance, repo_root, ("no-backoff",))


def test_n1_rejects_input_byte_change():
    with _synthetic_fixture() as (root, provenance):
        path = root / provenance["inputs"][0]["dat"]
        original = path.read_bytes()
        # 意味値は変えず、hash predicate だけを狙う comment byte drift。
        path.write_bytes(original + b"# digest drift only\n")
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "dat SHA256 mismatch")


def test_n2_rejects_recorded_input_digest_change():
    with _synthetic_fixture() as (root, provenance):
        digest = provenance["inputs"][0]["wal_sha256"]
        provenance["inputs"][0]["wal_sha256"] = (
            ("0" if digest[0] != "0" else "1") + digest[1:])
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "WAL SHA256 mismatch")


def test_n3_rejects_generator_byte_change():
    with _synthetic_fixture() as (root, provenance):
        (root / provenance["generator_source"]["path"]).write_bytes(b"changed")
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "generator SHA256 mismatch")


def test_n4_rejects_output_png_byte_change():
    with _synthetic_fixture() as (root, provenance):
        (root / provenance["outputs"][0]["path"]).write_bytes(b"changed")
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "output SHA256 mismatch")


def test_n5_rejects_label_that_disagrees_with_genome():
    with _synthetic_fixture(("no-backoff",)) as (root, provenance):
        provenance["inputs"][0]["baselines"][0]["label"] = "stock adaptive"
        _expect_rejected(
            provenance, root, ("no-backoff",), "baseline label/genome mismatch")


def test_n6_rejects_valid_but_not_rendered_baseline():
    with _synthetic_fixture(("no-backoff",)) as (root, provenance):
        provenance["inputs"][0]["baselines"].append(_baseline_row("stock-adaptive"))
        _expect_rejected(
            provenance, root, ("no-backoff",),
            "recorded baselines differ from rendered selection")


def test_n7_rejects_non_v2_schema():
    with _synthetic_fixture() as (root, provenance):
        provenance["schema"] = "izanagi-backoff-figure-provenance/v1"
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n8_rejects_baseline_with_extra_field():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["baselines"][0]["series"] = "hidden"
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n9_rejects_condition_drift():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["conditions"]["thread_num"] = 47
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n10_rejects_output_order_drift():
    with _synthetic_fixture() as (root, provenance):
        provenance["outputs"].reverse()
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n11_rejects_absolute_generator_path():
    with _synthetic_fixture() as (root, provenance):
        provenance["generator_source"]["path"] = str(
            root / provenance["generator_source"]["path"])
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n12_rejects_baseline_value_drift():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["baselines"][0]["value_tps"] += 1.0
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n13_rejects_baseline_genome_drift():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["baselines"][0]["genome"]["WAL"] = "1"
        _expect_rejected(provenance, root, ("no-backoff", "stock-adaptive"))


def test_n14_rejects_facts_best_M_drift():
    with _synthetic_fixture() as (root, provenance):
        provenance["facts"]["write-heavy"]["best_M"] = 999.0
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"), "best_M differs")


def test_n15_rejects_baseline_ci_half_width_drift():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["baselines"][0]["ci95_half_tps"] += 1.0
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "baseline CI differs")


def test_n16_rejects_campaign_lock_byte_change():
    with _synthetic_fixture() as (root, provenance):
        lock_path = root / provenance["inputs"][0]["lock"]
        lock_path.write_text(
            json.dumps({"ccbench_commit": "6656e93"}, indent=2) + "\n",
            encoding="utf-8")
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "campaign.lock SHA256 mismatch")


def test_n17_rejects_absolute_output_path():
    with _synthetic_fixture() as (root, provenance):
        provenance["outputs"][0]["path"] = str(
            root / provenance["outputs"][0]["path"])
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "path must be repo-relative")


def test_n18_rejects_input_path_that_leaves_repo():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["wal"] = "../../outside/wal.jsonl"
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "path leaves repo root")


def test_n19_rejects_nonempty_unresolved_fields():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["conditions"]["unresolved_fields"] = ["numactl_args"]
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "unresolved_fields must be empty")


def test_n20_rejects_multiple_condition_values_inside_workload():
    with _synthetic_fixture() as (root, provenance):
        provenance["inputs"][0]["conditions"]["thread_num"] = [47, 48]
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "multiple values inside one workload")


def test_n21_rejects_empty_static_tps_before_facts_can_be_recorded():
    with _synthetic_fixture() as (root, provenance):
        wal_path = root / provenance["inputs"][0]["wal"]
        records = [json.loads(line) for line in wal_path.read_text(
            encoding="utf-8").splitlines()]
        for record in records:
            if record["variant"] == "static" and record["stage"] == "bench_done":
                record["payload"]["tps"] = []
        wal_path.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        provenance["inputs"][0]["wal_sha256"] = _sha256(wal_path)
        _expect_rejected(
            provenance, root, ("no-backoff", "stock-adaptive"),
            "empty tps repetitions")


def _run() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
