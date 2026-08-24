#!/usr/bin/env python3
"""Fail-closed input normalizer for the T-1618 replay harness."""
from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


sys.dont_write_bytecode = True


SCHEMA = "t1618-input-manifest/v2"
K1_ID = "reference-full-measurement-14467"
K2_ID = "canonical-acceptance-15103-k2"
LEDGER_ID = "ledger-usable-14457"
EXPECTED_LEDGER_SHA256 = (
    "2570d39b97d7281d621cb6b7e31b1a721c34a4d98342998037b3fa25a5f168ab"
)
EXPECTED_COUNTS = {K1_ID: 14467, K2_ID: 15103, LEDGER_ID: 14457}
K1_ROOT = Path(
    "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-shard-dispatch"
)
K2_ROOT = Path(
    "/work/1/SFC/tanab/.izanagi-acceptance-shards/"
    "b08e632755ed9bbb698f400b5cdcc49c"
)
XDIST_ROOT = Path("/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist")
HERE = Path(__file__).resolve().parent
OWNED_OUTPUT = (HERE / "input-manifest.json").resolve()
EXPECTED_ORDER_DIGESTS = {
    "reference-k1-production-reorder-control": "06411b221ccbe529c4953dcfac9f81ec6299f2eef9496989834a50cc76179b2d",
    "canonical-k2-shard-0": "09bc024e97e450e7e5695166acc28605074bcb3f460a8b49529cf5a8085a2920",
    "canonical-k2-shard-1": "c84daa016b5ee31ecf51616a1605e84a9fe52f9cbf71042609f04e265b79df1d",
}
EXPECTED_K2_COMMAND = [
    "/usr/bin/python3",
    "-m",
    "pytest",
    "--ignore=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1621-suite-order-dependence/orchestrator/tests/test_dev_wave_cleanup.py",
    "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1621-suite-order-dependence/orchestrator/tests",
    "--collect-only",
    "-q",
    "-p",
    "no:cacheprovider",
]


class InputError(ValueError):
    """The source artifacts do not meet the closed input contract."""


def _repo_root() -> Path:
    root = Path(__file__).resolve().parents[3]
    if not (root / "pytest.ini").is_file():
        raise InputError("repository root cannot be resolved from harness path")
    return root


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise InputError(f"cannot hash required input: {path}: {exc}") from exc
    return digest.hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("ascii")


def _json_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read JSON object: {path}: {exc}") from exc
    if type(value) is not dict:
        raise InputError(f"JSON top level is not an object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    payload = _canonical_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _node_file(base_nodeid: str) -> str:
    filename, separator, _suffix = base_nodeid.partition("::")
    if (
        not separator
        or not filename.endswith(".py")
        or Path(filename).is_absolute()
        or ".." in Path(filename).parts
    ):
        raise InputError(f"noncanonical nodeid: {base_nodeid!r}")
    return filename


def _scheduler_nodeid(base_nodeid: str, group: str | None) -> str:
    _node_file(base_nodeid)
    if group is None:
        return base_nodeid
    if type(group) is not str or not group:
        raise InputError(f"invalid group for {base_nodeid!r}")
    return f"{base_nodeid}@{group}"


def _tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _junit_join(
    path: Path,
    scheduler_nodeids: Sequence[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    expected = set(scheduler_nodeids)
    module_to_file: dict[str, str] = {}
    for nodeid in scheduler_nodeids:
        filename = _node_file(nodeid)
        module = filename[:-3].replace("/", ".")
        previous = module_to_file.setdefault(module, filename)
        if previous != filename:
            raise InputError(f"ambiguous JUnit module identity: {module!r}")
    modules = sorted(module_to_file, key=len, reverse=True)
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise InputError(f"cannot parse JUnit: {path}: {exc}") from exc
    result: dict[str, dict[str, Any]] = {}
    outcomes: Counter[str] = Counter()
    known_children = {
        "error", "failure", "properties", "skipped", "system-err", "system-out",
    }
    testcases = [element for element in root.iter() if _tag_name(element) == "testcase"]
    for testcase in testcases:
        attributes = testcase.attrib
        classname = attributes.get("classname")
        name = attributes.get("name")
        raw_time = attributes.get("time")
        if type(classname) is not str or type(name) is not str or raw_time is None:
            raise InputError(f"unknown JUnit testcase schema in {path}")
        matching_modules = [
            module for module in modules
            if classname == module or classname.startswith(module + ".")
        ]
        if not matching_modules:
            raise InputError(f"JUnit classname does not join the population: {classname!r}")
        module = matching_modules[0]
        class_suffix = classname[len(module):].lstrip(".")
        suffix = "::".join(class_suffix.split(".") + [name]) if class_suffix else name
        nodeid = f"{module_to_file[module]}::{suffix}"
        if nodeid not in expected:
            raise InputError(f"JUnit testcase does not join the population: {nodeid!r}")
        if nodeid in result:
            raise InputError(f"duplicate JUnit testcase: {nodeid!r}")
        try:
            duration = float(raw_time)
        except (TypeError, ValueError) as exc:
            raise InputError(f"invalid JUnit duration: {nodeid!r}") from exc
        if not math.isfinite(duration) or duration < 0:
            raise InputError(f"nonfinite or negative JUnit duration: {nodeid!r}")
        child_names = [_tag_name(child) for child in testcase]
        unknown = set(child_names) - known_children
        if unknown:
            raise InputError(f"unknown JUnit testcase children: {sorted(unknown)!r}")
        terminal = [name for name in child_names if name in {"error", "failure", "skipped"}]
        if len(terminal) > 1:
            raise InputError(f"multiple JUnit outcomes: {nodeid!r}")
        outcome = terminal[0] if terminal else "passed"
        outcomes[outcome] += 1
        result[nodeid] = {"duration_s": duration, "outcome": outcome}
    if len(testcases) != len(scheduler_nodeids) or set(result) != set(scheduler_nodeids):
        missing = set(scheduler_nodeids) - set(result)
        raise InputError(
            f"JUnit join mismatch: testcases={len(testcases)} expected={len(scheduler_nodeids)} "
            f"joined={len(result)} missing={len(missing)}"
        )
    return result, dict(sorted(outcomes.items()))


class _FakeItem:
    def __init__(self, repo: Path, base_nodeid: str, scheduler_nodeid: str) -> None:
        self.nodeid = scheduler_nodeid
        self.path = repo / _node_file(base_nodeid)


def _production_reorder(
    repo: Path,
    ordered_base_nodeids: Sequence[str],
    group_by_base: Mapping[str, str | None],
    ledger: Mapping[str, float],
) -> list[str]:
    sys.path.insert(0, str(repo))
    try:
        from orchestrator.tests import conftest as acceptance_conftest
    finally:
        try:
            sys.path.remove(str(repo))
        except ValueError:
            pass
    items = [
        _FakeItem(repo, base, _scheduler_nodeid(base, group_by_base[base]))
        for base in ordered_base_nodeids
    ]
    changed = acceptance_conftest._reorder_acceptance_items_by_duration(items, ledger)
    if not changed:
        raise InputError("production duration reorder declined a nonempty population")
    result = [str(item.nodeid) for item in items]
    expected = [_scheduler_nodeid(base, group_by_base[base]) for base in ordered_base_nodeids]
    if Counter(result) != Counter(expected) or len(result) != len(set(result)):
        raise InputError("production duration reorder changed the collection multiset")
    return result


def _split_scope(nodeid: str) -> str:
    return nodeid.split("@")[-1] if nodeid.rfind("@") > nodeid.rfind("]") else nodeid


def _unit_stats(collection: Sequence[str]) -> dict[str, Any]:
    sizes = Counter(_split_scope(nodeid) for nodeid in collection)
    multi = sorted(
        ({"scope": scope, "items": count} for scope, count in sizes.items() if count > 1),
        key=lambda entry: (-entry["items"], entry["scope"]),
    )
    return {
        "work_unit_count": len(sizes),
        "single_item_units": sum(count == 1 for count in sizes.values()),
        "multi_item_units": multi,
        "max_items_per_unit": max(sizes.values()),
    }


def _failed_pair_prefix_sum(strings: Sequence[str]) -> int:
    root: dict[str, Any] = {"count": 0, "children": {}}
    total = 0
    for value in strings:
        node = root
        for character in value:
            children = node["children"]
            child = children.get(character)
            if child is None:
                child = {"count": 0, "children": {}}
                children[character] = child
            total += child["count"]
            child["count"] += 1
            node = child
    return total


def _prefix_invariant(primary: Sequence[str], alternate: Sequence[str]) -> dict[str, Any]:
    if Counter(primary) != Counter(alternate):
        raise InputError("prefix invariant inputs do not have the same value multiset")
    first = _failed_pair_prefix_sum(primary)
    second = _failed_pair_prefix_sum(alternate)
    reverse = _failed_pair_prefix_sum(list(reversed(primary)))
    if first != second or first != reverse:
        raise InputError("mathematical prefix invariant was violated")
    return {
        "status": "recorded-mathematical-invariant",
        "adoption_gate": False,
        "failed_pair_common_prefix_codepoint_sum": first,
        "alternate_order_sum": second,
        "reverse_order_sum": reverse,
    }


def _ledger(repo: Path) -> tuple[dict[str, float], dict[str, Any]]:
    path = repo / "orchestrator/tests/acceptance_duration_ledger.json"
    if _sha256(path) != EXPECTED_LEDGER_SHA256:
        raise InputError("duration ledger SHA-256 differs from the adjudicated input")
    raw = _read_json_object(path)
    if set(raw) != {"schema_version", "unit", "nodeid_count", "duration_seconds_by_nodeid"}:
        raise InputError("unknown duration ledger schema")
    if raw["schema_version"] != 1 or raw["unit"] != "seconds":
        raise InputError("unknown duration ledger version or unit")
    values = raw["duration_seconds_by_nodeid"]
    if type(values) is not dict or raw["nodeid_count"] != EXPECTED_COUNTS[LEDGER_ID]:
        raise InputError("duration ledger count mismatch")
    ledger: dict[str, float] = {}
    for nodeid, duration in values.items():
        if type(nodeid) is not str or type(duration) not in {int, float}:
            raise InputError("invalid duration ledger entry")
        value = float(duration)
        if not math.isfinite(value) or value < 0:
            raise InputError("invalid duration ledger duration")
        ledger[nodeid] = value
    if len(ledger) != EXPECTED_COUNTS[LEDGER_ID]:
        raise InputError("duration ledger key count mismatch")
    return ledger, {
        "population_id": LEDGER_ID,
        "path": str(path),
        "sha256": EXPECTED_LEDGER_SHA256,
        "nodeid_count": len(ledger),
    }


def _item_records(
    ordered_base: Sequence[str],
    group_by_base: Mapping[str, str | None],
    junit: Mapping[str, Mapping[str, Any]],
    ledger: Mapping[str, float],
) -> list[list[Any]]:
    records = []
    for base in ordered_base:
        scheduler = _scheduler_nodeid(base, group_by_base[base])
        evidence = junit[scheduler]
        record = [
            scheduler,
            evidence["duration_s"],
            group_by_base[base],
            evidence["outcome"],
            ledger.get(base),
        ]
        records.append(record)
    return records


def _order_indices(items: Sequence[Sequence[Any]], order: Sequence[str]) -> list[int]:
    index_by_nodeid = {entry[0]: index for index, entry in enumerate(items)}
    if len(index_by_nodeid) != len(items):
        raise InputError("compact item table contains duplicate scheduler nodeids")
    try:
        result = [index_by_nodeid[nodeid] for nodeid in order]
    except KeyError as exc:
        raise InputError(f"controller order is outside compact item table: {exc}") from exc
    if len(result) != len(set(result)):
        raise InputError("controller order contains duplicate compact indices")
    return result


def _require_expected_order(controller_id: str, before: Sequence[str], after: Sequence[str]) -> str:
    if list(before) == list(after):
        raise InputError(f"production reorder was a no-op for {controller_id}")
    digest = _json_digest(after)
    if digest != EXPECTED_ORDER_DIGESTS[controller_id]:
        raise InputError(
            f"independently preregistered order digest mismatch for {controller_id}: {digest}"
        )
    return digest


def _k1_population(repo: Path, ledger: Mapping[str, float]) -> dict[str, Any]:
    groupmap_path = K1_ROOT / "groupmap.json"
    junit_path = K1_ROOT / "measure1-junit.xml"
    measure_script = K1_ROOT / "measure1.sh"
    measure_log = K1_ROOT / "measure1.log"
    groupmap = _read_json_object(groupmap_path)
    if len(groupmap) != EXPECTED_COUNTS[K1_ID]:
        raise InputError("K=1 groupmap count mismatch")
    ordered_base = list(groupmap)
    if len(ordered_base) != len(set(ordered_base)):
        raise InputError("K=1 groupmap has duplicate nodeids")
    group_by_base: dict[str, str | None] = {}
    for base, group in groupmap.items():
        _node_file(base)
        if group is not None and (type(group) is not str or not group):
            raise InputError("K=1 groupmap has an invalid group")
        group_by_base[base] = group
    scheduler_order = [_scheduler_nodeid(base, group_by_base[base]) for base in ordered_base]
    joined, outcomes = _junit_join(junit_path, scheduler_order)
    missing_ledger = [base for base in ordered_base if base not in ledger]
    missing_outcomes = Counter(joined[_scheduler_nodeid(base, group_by_base[base])]["outcome"] for base in missing_ledger)
    if (
        len(missing_ledger) != 10
        or set(missing_outcomes) - {"failure", "error"}
        or sum(missing_outcomes.values()) != 10
        or any("test_sort_swo_oracle" not in base for base in missing_ledger)
    ):
        raise InputError("K=1 ledger difference is not the adjudicated ten failures/errors")
    post_order = _production_reorder(repo, ordered_base, group_by_base, ledger)
    unit_stats = _unit_stats(scheduler_order)
    multi_sizes = sorted((entry["items"] for entry in unit_stats["multi_item_units"]), reverse=True)
    if unit_stats["work_unit_count"] != 14373 or multi_sizes != [70, 22, 5]:
        raise InputError(f"K=1 loadgroup unit gate failed: {unit_stats!r}")
    post_digest = _require_expected_order(
        "reference-k1-production-reorder-control", scheduler_order, post_order
    )
    prefix = _prefix_invariant(scheduler_order, post_order)
    records = _item_records(ordered_base, group_by_base, joined, ledger)
    sources = {
        "groupmap": {"path": str(groupmap_path), "sha256": _sha256(groupmap_path)},
        "junit": {"path": str(junit_path), "sha256": _sha256(junit_path)},
        "measure_script": {"path": str(measure_script), "sha256": _sha256(measure_script)},
        "measure_log": {"path": str(measure_log), "sha256": _sha256(measure_log)},
    }
    return {
        "id": K1_ID,
        "kind": "reference-population-conditional-replay",
        "shard_count": 1,
        "worker_count_per_controller": 48,
        "n": len(records),
        "ledger_joined": len(records) - len(missing_ledger),
        "ledger_missing": len(missing_ledger),
        "junit_outcomes": outcomes,
        "item_fields": [
            "scheduler_nodeid", "duration_s", "group", "outcome", "ledger_duration_s"
        ],
        "items": records,
        "unit_stats": unit_stats,
        "prefix_order_invariance": prefix,
        "sources": sources,
        "controllers": [
            {
                "id": "reference-k1-groupmap-order-conditional",
                "order": "groupmap-order-conditional-control",
                "order_indices": None,
                "ordered_collection_sha256": _json_digest(scheduler_order),
                "selected_n": len(scheduler_order),
                "expected_worker_occupancy": None,
                "expected_group_to_workers": None,
                "provenance_closed": False,
                "provenance_limitation": "groupmap insertion order is not bound to the historical K=1 collection; historical K=1 values must not be connected",
            },
            {
                "id": "reference-k1-production-reorder-control",
                "order": "production-reorder-of-groupmap-conditional-control",
                "order_indices": _order_indices(records, post_order),
                "ordered_collection_sha256": post_digest,
                "selected_n": len(post_order),
                "expected_worker_occupancy": None,
                "expected_group_to_workers": None,
                "provenance_closed": False,
                "provenance_limitation": "counterfactual production reorder of the historical population",
            },
        ],
    }


def _records_digest(records: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {"file": entry["file"], "group": entry["group"], "nodeid": entry["nodeid"]}
        for entry in records
    ]
    return _json_digest(payload)


def _login_collection(path: Path) -> tuple[list[str], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot read login collection log: {exc}") from exc
    commands = [line for line in lines if line.startswith("command=")]
    if len(commands) != 1:
        raise InputError("login collection log must contain exactly one command record")
    try:
        command = json.loads(commands[0][len("command="):])
    except json.JSONDecodeError as exc:
        raise InputError("login collection command is not a JSON list") from exc
    if command != EXPECTED_K2_COMMAND:
        raise InputError(f"login collection command differs from exact preregistration: {command!r}")
    stdout_positions = [index for index, line in enumerate(lines) if line == "stdout:"]
    stderr_positions = [index for index, line in enumerate(lines) if line == "stderr:"]
    if len(stdout_positions) != 1 or len(stderr_positions) != 1:
        raise InputError("login collection log must contain one stdout and one stderr section")
    stdout_at, stderr_at = stdout_positions[0], stderr_positions[0]
    if not (lines.index(commands[0]) < stdout_at < stderr_at):
        raise InputError("login collection section order is invalid")
    def looks_like_nodeid(line: str) -> bool:
        return line.startswith("orchestrator/tests/") and "::" in line
    outside = lines[: stdout_at + 1] + lines[stderr_at:]
    if any(looks_like_nodeid(line) for line in outside):
        raise InputError("nodeid-like line appeared outside the stdout section")
    nodeids = [line for line in lines[stdout_at + 1:stderr_at] if looks_like_nodeid(line)]
    if len(nodeids) != EXPECTED_COUNTS[K2_ID] or len(nodeids) != len(set(nodeids)):
        raise InputError("login ordered collection count or uniqueness mismatch")
    return nodeids, command


def _validate_report(report: Mapping[str, Any], shard_index: int) -> None:
    fields = {
        "schema_version", "shard_count", "shard_index", "pytest_rc",
        "observed_universe", "selected", "finished", "effective_scheduler",
        "terminal_counts", "failures", "group_to_workers", "worker_occupancy",
        "junit_path", "worker_collection_digests",
    }
    if set(report) != fields or report["schema_version"] != "izanagi-acceptance-shard-report/v1":
        raise InputError(f"unknown K=2 report schema for shard {shard_index}")
    if report["shard_count"] != 2 or report["shard_index"] != shard_index:
        raise InputError(f"K=2 report index mismatch for shard {shard_index}")
    if report["pytest_rc"] != 0 or report["effective_scheduler"] != "loadgroup":
        raise InputError(f"K=2 report is not a successful loadgroup run for shard {shard_index}")


def _k2_population(repo: Path, ledger: Mapping[str, float]) -> dict[str, Any]:
    login_path = K2_ROOT / "login-collection.log"
    login_order, login_command = _login_collection(login_path)
    reports = [_read_json_object(K2_ROOT / f"shard-{index}/report.json") for index in range(2)]
    for index, report in enumerate(reports):
        _validate_report(report, index)
    if reports[0]["observed_universe"] != reports[1]["observed_universe"]:
        raise InputError("K=2 observed universes differ by shard")
    universe = reports[0]["observed_universe"]
    if type(universe) is not list or len(universe) != EXPECTED_COUNTS[K2_ID]:
        raise InputError("K=2 observed universe count mismatch")
    group_by_base: dict[str, str | None] = {}
    for entry in universe:
        if type(entry) is not dict or set(entry) != {"file", "group", "nodeid"}:
            raise InputError("unknown K=2 observed universe item schema")
        base = entry["nodeid"]
        if type(base) is not str or entry["file"] != _node_file(base):
            raise InputError("invalid K=2 observed universe item")
        group = entry["group"]
        if group is not None and (type(group) is not str or not group):
            raise InputError("invalid K=2 observed universe group")
        if base in group_by_base:
            raise InputError("duplicate K=2 observed universe nodeid")
        group_by_base[base] = group
    if Counter(login_order) != Counter(group_by_base.keys()):
        raise InputError("login ordered collection does not join the observed universe")
    digest = _records_digest(universe)
    all_digests: list[str] = []
    selected_sets: list[set[str]] = []
    for index, report in enumerate(reports):
        digests = report["worker_collection_digests"]
        if type(digests) is not list or len(digests) != 48 or set(digests) != {digest}:
            raise InputError(f"worker collection digest gate failed for shard {index}")
        all_digests.extend(digests)
        selected = report["selected"]
        expected_n = 7552 if index == 0 else 7551
        if type(selected) is not list or len(selected) != expected_n or len(selected) != len(set(selected)):
            raise InputError(f"K=2 selected count or uniqueness mismatch for shard {index}")
        if not set(selected) <= set(group_by_base):
            raise InputError(f"K=2 selected is outside universe for shard {index}")
        selected_sets.append(set(selected))
    if selected_sets[0] & selected_sets[1] or selected_sets[0] | selected_sets[1] != set(group_by_base):
        raise InputError("K=2 selected sets do not partition the observed universe")

    joined_by_scheduler: dict[str, dict[str, Any]] = {}
    outcomes: Counter[str] = Counter()
    controllers = []
    for index, report in enumerate(reports):
        selected_set = selected_sets[index]
        ordered_base = [base for base in login_order if base in selected_set]
        scheduler_before = [_scheduler_nodeid(base, group_by_base[base]) for base in ordered_base]
        junit_path = K2_ROOT / f"shard-{index}/junit.xml"
        joined, shard_outcomes = _junit_join(junit_path, scheduler_before)
        if set(joined_by_scheduler) & set(joined):
            raise InputError("K=2 JUnit join overlaps across shards")
        joined_by_scheduler.update(joined)
        outcomes.update(shard_outcomes)
        reordered = _production_reorder(repo, ordered_base, group_by_base, ledger)
        controller_id = f"canonical-k2-shard-{index}"
        reordered_digest = _require_expected_order(controller_id, scheduler_before, reordered)
        prefix = _prefix_invariant(scheduler_before, reordered)
        occupancy = report["worker_occupancy"]
        if type(occupancy) is not dict or len(occupancy) != 48:
            raise InputError(f"K=2 worker occupancy count mismatch for shard {index}")
        if sum(entry.get("items", -1) for entry in occupancy.values() if type(entry) is dict) != len(reordered):
            raise InputError(f"K=2 worker occupancy item join failed for shard {index}")
        controllers.append({
            "id": controller_id,
            "shard_index": index,
            "order": "post-d746",
            "order_indices": None,
            "ordered_collection_sha256": reordered_digest,
            "selected_n": len(reordered),
            "unit_stats": _unit_stats(reordered),
            "prefix_order_invariance": prefix,
            "expected_worker_occupancy": occupancy,
            "expected_group_to_workers": report["group_to_workers"],
            "worker_collection_digest": digest,
            "worker_collection_digest_count": len(report["worker_collection_digests"]),
            "provenance_closed": False,
            "provenance_limitation": "historical K=2 HEAD, ledger bytes, conftest bytes, and ordered worker collection digest were not recorded together",
            "provenance_basis": {
                "ordered_login_collection_sha256": _json_digest(login_order),
                "login_universe_counter_match": True,
                "canonical_sorted_records_digest_matches_all_workers": True,
                "production_reorder_source_sha256": _sha256(repo / "orchestrator/tests/conftest.py"),
                "digest_semantics": "canonical sorted records only; it does not close ordered collection provenance",
            },
            "sources": {
                "report": {
                    "path": str(K2_ROOT / f"shard-{index}/report.json"),
                    "sha256": _sha256(K2_ROOT / f"shard-{index}/report.json"),
                },
                "junit": {"path": str(junit_path), "sha256": _sha256(junit_path)},
            },
        })
    if len(joined_by_scheduler) != EXPECTED_COUNTS[K2_ID]:
        raise InputError("K=2 combined JUnit join count mismatch")
    records = _item_records(login_order, group_by_base, joined_by_scheduler, ledger)
    for controller in controllers:
        index = controller["shard_index"]
        selected_set = selected_sets[index]
        ordered_base = [base for base in login_order if base in selected_set]
        reordered = _production_reorder(repo, ordered_base, group_by_base, ledger)
        controller["order_indices"] = _order_indices(records, reordered)
    return {
        "id": K2_ID,
        "kind": "canonical-acceptance-observed-k2-replay",
        "shard_count": 2,
        "worker_count_per_controller": 48,
        "n": len(records),
        "ledger_joined": sum(record[4] is not None for record in records),
        "ledger_missing": sum(record[4] is None for record in records),
        "junit_outcomes": dict(sorted(outcomes.items())),
        "item_fields": [
            "scheduler_nodeid", "duration_s", "group", "outcome", "ledger_duration_s"
        ],
        "items": records,
        "sources": {
            "login_collection": {"path": str(login_path), "sha256": _sha256(login_path)},
            "login_command": login_command,
            "worker_collection_digest_definition": {
                "producer": "tools/acceptance_shards.py:_digest(_records_payload(records))",
                "canonical_json": "ensure_ascii=true,separators=(',',':'),sort_keys=true,trailing_lf=true",
                "sha256": digest,
                "matching_worker_payloads": len(all_digests),
            },
        },
        "controllers": controllers,
    }


def _collection_invariance(repo: Path) -> dict[str, Any]:
    path = repo / "pytest.ini"
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with path.open("r", encoding="utf-8") as stream:
            parser.read_file(stream)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise InputError(f"cannot parse pytest.ini: {exc}") from exc
    testpaths = parser.get("pytest", "testpaths", fallback="").split()
    norecursedirs = parser.get("pytest", "norecursedirs", fallback="").split()
    if testpaths != ["orchestrator/tests"] or "output" not in norecursedirs:
        raise InputError("pytest.ini no longer statically excludes the harness from acceptance")
    return {
        "status": "passed-static",
        "pytest_ini_path": str(path),
        "pytest_ini_sha256": _sha256(path),
        "testpaths": testpaths,
        "norecursedirs_contains_output": True,
        "acceptance_collection_delta_from_harness": 0,
        "basis": "testpaths is orchestrator/tests and norecursedirs contains output",
    }


def build_manifest() -> dict[str, Any]:
    repo = _repo_root()
    ledger, ledger_evidence = _ledger(repo)
    k1 = _k1_population(repo, ledger)
    k2 = _k2_population(repo, ledger)
    xdist_sources = {
        name: {
            "path": str(XDIST_ROOT / relative),
            "sha256": _sha256(XDIST_ROOT / relative),
        }
        for name, relative in {
            "xdist": Path("__init__.py"),
            "loadscope": Path("scheduler/loadscope.py"),
            "loadgroup": Path("scheduler/loadgroup.py"),
            "dsession": Path("dsession.py"),
        }.items()
    }
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise InputError(f"cannot resolve repository HEAD: {exc}") from exc
    return {
        "schema_version": SCHEMA,
        "snapshot_format": "compact-deduplicated-json",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "producer": str(Path(__file__).resolve()),
        "repo_root": str(repo),
        "repo_head": head,
        "population_ids": [K1_ID, K2_ID],
        "ledger": ledger_evidence,
        "collection_invariance": _collection_invariance(repo),
        "xdist": {
            "version": "3.8.0",
            "source_root": str(XDIST_ROOT),
            "sources": xdist_sources,
        },
        "populations": [k1, k2],
    }


def summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    populations = []
    for population in manifest["populations"]:
        populations.append({
            "id": population["id"],
            "n": population["n"],
            "ledger_joined": population["ledger_joined"],
            "ledger_missing": population["ledger_missing"],
            "controllers": [
                {
                    "id": controller["id"],
                    "selected_n": controller["selected_n"],
                    "ordered_collection_sha256": controller["ordered_collection_sha256"],
                }
                for controller in population["controllers"]
            ],
        })
    return {
        "schema_version": manifest["schema_version"],
        "ledger": manifest["ledger"],
        "collection_invariance": manifest["collection_invariance"],
        "populations": populations,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = build_manifest()
        if args.output is not None:
            output = args.output.resolve()
            if output != OWNED_OUTPUT:
                raise InputError(f"--output must be exactly the owned snapshot path: {OWNED_OUTPUT}")
            _write_json(output, manifest)
        print(json.dumps(summary(manifest), ensure_ascii=True, sort_keys=True))
    except InputError as exc:
        print(f"input normalization failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
